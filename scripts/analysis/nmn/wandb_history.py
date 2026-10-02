"""Read a training run's own local WandB log: survival, food bites and gradient norms.

Plain-language purpose: two analyses of "What Both Agents Compute" need numbers the network
activations do not hold. The wake-up measure (B2) needs survival over training, averaged
within each interval between saved checkpoints, to find where survival levels off; the
seed-yardstick analysis (A3) and gate G5 need each run's survival and food bites at the end
of a stage. All of them come from the run's local WandB binary (never the web API).

Three rules keep it honest:
- **The folder is found by the run's tag.** `resolve_by_tag` reads every local
  `wandb/run-*/files/wandb-metadata.json`, and exactly one folder must have been launched with
  `--tag <tag>`; zero or several raise. Never a timestamp glob.
- **Rows are weighted as the pre-registered rules say.** Each logged `Episode/*` row is a
  rolling-window mean. The registered weighting (`parameters.common.survival.row_weight`) is
  `delta_episode_number`: a row counts for the episodes it adds, the increase in
  `Episode/Number` since the previous row. That is exactly `pilot_readout.Series`, the code
  that computes the May replication's own verdict. `window_n` (weight by `Episode/_window_n`)
  exists only as a printed diagnostic. Rows whose `Episode/_window_n` is below the caller's
  `min_window_n` are skipped. Every one of these values is passed in by the caller from the
  rules' `parameters:`; this module holds no default.
- **Loss rows are joined to episodes, never converted by arithmetic.** A May-replication loss
  row carries its own `Episode/Number`; a level-05 loss row does not, and is matched to the
  episode row with the same `timesteps` value. Unmatched rows are counted, not interpolated.

Plan: docs/develop/active/neuromodulation/ALGORITHMIC_NULL_ANALYSIS_TOOLING.md, File Changes §7.
"""
from __future__ import annotations

import glob
import json
import math
import os
from pathlib import Path

import numpy as np

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

NUM, WN, STAGE, TS = "Episode/Number", "Episode/_window_n", "stage/index", "timesteps"
WEIGHTINGS = ("delta_episode_number", "window_n")
# pilot_readout.analyse_sequence's own stage-row selection (l.667): stage k's rows are those with
# stage/index == k and lo < Episode/Number <= hi + 4000, because a stage's last logged row may sit
# up to one logging step past the schedule boundary. Mirrored here, not re-chosen; Checkpoint 4.6
# (tests/analysis/test_nmn_stage_level.py) checks the result equals pilot_readout's on real runs.
BOUNDARY_SLACK_EPISODES = 4000

_TAG_INDEX: dict[str, dict[str, list[str]]] = {}


# ------------------------------------------------------------------------------ resolution --
def _tag_index(wandb_root: str) -> dict[str, list[str]]:
    """tag -> [folders launched with --tag tag]; built once per process (the NAS scan of
    ~1,000 metadata files takes a minute or two)."""
    if wandb_root not in _TAG_INDEX:
        idx: dict[str, list[str]] = {}
        for mf in glob.glob(os.path.join(wandb_root, "run-*", "files", "wandb-metadata.json")):
            try:
                args = json.load(open(mf)).get("args", [])
            except (ValueError, OSError):
                continue
            if "--tag" in args and args.index("--tag") + 1 < len(args):
                idx.setdefault(args[args.index("--tag") + 1], []).append(
                    os.path.dirname(os.path.dirname(mf)))
        _TAG_INDEX[wandb_root] = idx
    return _TAG_INDEX[wandb_root]


def resolve_by_tag(tag: str, wandb_root: str | None = None) -> Path:
    """The one local WandB folder launched with `--tag <tag>`. Zero or several raise."""
    root = wandb_root or os.path.join(_ROOT, "wandb")
    hits = sorted(_tag_index(root).get(tag, []))
    if len(hits) != 1:
        raise ValueError(f"--tag {tag}: expected exactly one local WandB folder under {root}, "
                         f"found {len(hits)}: {hits}")
    return Path(hits[0])


def run_tag(run_dir) -> str:
    """The run's saved top-level `tag:` (never a manifest label)."""
    import yaml
    cfg = yaml.safe_load((Path(run_dir) / "models" / "config.yaml").read_text())
    if not cfg.get("tag"):
        raise ValueError(f"{run_dir}: saved models/config.yaml has no top-level tag")
    return cfg["tag"]


# --------------------------------------------------------------------------------- reading --
def scan(wandb_dir, allow_truncated: bool) -> dict:
    """All history rows of the binary, parsed to floats where possible, plus whether the run
    wrote an exit record (it finished) and its exit code.

    A run still being written can end in a half-written record. With `allow_truncated` the
    scan stops there and says so in `truncated` (the error text), but only when the unreadable
    record is in the file's last block (the datastore's own in-progress test); an unreadable
    record earlier in the file is corruption and raises either way. The CALLER decides whether
    the rows it needs are complete (e.g. a later stage has logged rows).

    Returns {"rows": [dict], "exit_code": int | None, "file": str, "truncated": str | None}."""
    from wandb.proto import wandb_internal_pb2 as pb
    from wandb.sdk.internal import datastore

    files = glob.glob(os.path.join(str(wandb_dir), "run-*.wandb"))
    if len(files) != 1:
        raise ValueError(f"{wandb_dir}: expected one run-*.wandb, found {files}")
    ds = datastore.DataStore()
    ds.open_for_scan(files[0])
    rows, exit_code, truncated = [], None, None
    while True:
        try:
            data = ds.scan_data()
            if data is None:
                break
            rec = pb.Record()
            rec.ParseFromString(data)
        except Exception as e:  # a run still being written can end mid-record
            if allow_truncated and ds.in_last_block():
                truncated = f"{type(e).__name__}: {e}"
                break
            raise RuntimeError(f"{files[0]}: unreadable record ({type(e).__name__}: {e})"
                               f"{'' if ds.in_last_block() else ' before the last block'}") from e
        rtype = rec.WhichOneof("record_type")
        if rtype == "exit":
            exit_code = int(rec.exit.exit_code)
            continue
        if rtype != "history":
            continue
        r = {}
        for it in rec.history.item:
            k = it.key or "/".join(it.nested_key)
            try:
                v = json.loads(it.value_json)
            except ValueError:
                continue
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                r[k] = float(v)
        rows.append(r)
    return {"rows": rows, "exit_code": exit_code, "file": files[0], "truncated": truncated}


def episode_rows(scanned: dict, stage_index: int | None) -> list[dict]:
    """Episode rows (those with `Episode/Steps`), in `Episode/Number` order; restricted to
    `stage/index == stage_index` when a stage is given (continual runs)."""
    rows = [r for r in scanned["rows"] if "Episode/Steps" in r]
    for r in rows:
        if NUM not in r or WN not in r:
            raise ValueError(f"{scanned['file']}: episode row without {NUM} / {WN}: {r}")
    if stage_index is not None:
        miss = [r for r in rows if STAGE not in r]
        if miss:
            raise ValueError(f"{scanned['file']}: {len(miss)} episode rows carry no {STAGE}; "
                             f"a stage cannot be selected")
        rows = [r for r in rows if int(r[STAGE]) == stage_index]
    rows.sort(key=lambda r: r[NUM])
    return rows


def start_counter(rows: list[dict]) -> float:
    """The episode counter before the first row: first Number - first _window_n (0 for a run
    trained from scratch; pilot_readout's `start_counter`)."""
    if not rows:
        raise ValueError("no episode rows")
    return rows[0][NUM] - rows[0][WN]


def weighted(rows: list[dict], start: float, weighting: str, min_window_n: float) -> list:
    """[(episode, weight, row)] for the rows that count.

    `delta_episode_number` reproduces `pilot_readout.Series` exactly: the weight is the
    increase in `Episode/Number` since the previous row (skipped rows included, so a skipped
    row's episodes are not handed to its successor), and a row is dropped if its
    `_window_n` < `min_window_n` or its weight is not positive. `window_n` weights by
    `Episode/_window_n` under the same skip (diagnostic only)."""
    if weighting not in WEIGHTINGS:
        raise ValueError(f"weighting {weighting!r}: must be one of {WEIGHTINGS} "
                         f"(parameters.common.survival.row_weight)")
    out, prev = [], start
    for r in rows:
        e = r[NUM]
        w = e - prev if weighting == "delta_episode_number" else r[WN]
        prev = e
        if r[WN] < min_window_n or w <= 0:
            continue
        out.append((e, w, r))
    return out


def interval_means(rows: list[dict], key: str, edges, weighting: str,
                   min_window_n: float) -> tuple[np.ndarray, dict]:
    """Weighted mean of `key` within each checkpoint interval (edges[i-1], edges[i]].

    `edges` is the run's checkpoint grid with its lower end first (0 for step 0 of a run
    trained from scratch; the rules' B2 `x_grid`). Row weights run from the rows' own start
    counter, as in `pilot_readout.Series`. An interval with no counted row is NaN and is
    listed in the info, never filled."""
    edges = np.asarray(edges, dtype=float)
    if edges.ndim != 1 or np.any(np.diff(edges) <= 0):
        raise ValueError("edges must be strictly increasing")
    kept = weighted(rows, start_counter(rows), weighting, min_window_n)
    e = np.array([k[0] for k in kept])
    w = np.array([k[1] for k in kept])
    v = np.array([k[2].get(key, np.nan) for k in kept])
    means = np.full(len(edges) - 1, np.nan)
    counts = np.zeros(len(edges) - 1, dtype=int)
    for i in range(len(edges) - 1):
        m = (e > edges[i]) & (e <= edges[i + 1]) & ~np.isnan(v)
        counts[i] = int(m.sum())
        if counts[i] and w[m].sum() > 0:
            means[i] = float((v[m] * w[m]).sum() / w[m].sum())
    info = {"rows_total": len(rows), "rows_counted": len(kept),
            "rows_skipped": len(rows) - len(kept), "rows_per_interval": counts.tolist(),
            "empty_intervals": [int(i) for i in np.flatnonzero(counts == 0)],
            "rows_beyond_last_edge": int((e > edges[-1]).sum()),
            "weighting": weighting, "min_window_n": min_window_n}
    return means, info


def stage_rows(scanned: dict, stage_index: int, bounds) -> list[dict]:
    """Stage k's episode rows exactly as pilot_readout.analyse_sequence selects them:
    stage/index == k AND lo < Episode/Number <= hi + BOUNDARY_SLACK_EPISODES, where
    bounds = (lo, hi) is the stage's schedule boundary pair (lo = the previous stage's hi, or
    the run's start counter for stage 0). Sorted by Episode/Number."""
    lo, hi = (float(b) for b in bounds)
    if not hi > lo:
        raise ValueError(f"stage bounds {bounds}: hi must exceed lo")
    return [r for r in episode_rows(scanned, stage_index)
            if lo < r[NUM] <= hi + BOUNDARY_SLACK_EPISODES]


def stage_level(scanned: dict, stage_index: int, bounds, key: str, window: float,
                min_window_n: float, weighting: str) -> tuple[float | None, dict]:
    """S_k-style level: the weighted mean of `key` over the last `window` episodes of stage
    `stage_index` (rows in (last - window, last], `last` the last counted row), the May
    design's §5.1 quantity and `pilot_readout.last_level`.

    `bounds` = (lo, hi), the stage's schedule boundaries (pilot_readout's `lo`, `hi`). Rows are
    selected by `stage_rows` and weighted from `lo` (the series starts at lo, as
    `pilot_readout.Series(srows, lo)`). The stage must be complete: a later stage has logged
    rows, or the run wrote a zero exit code. Otherwise, or with fewer than `window` episodes,
    the value is None and `info["reason"]` says why."""
    lo, hi = (float(b) for b in bounds)
    rows = stage_rows(scanned, stage_index, bounds)
    info = {"rows": len(rows), "weighting": weighting, "window": window,
            "min_window_n": min_window_n, "bounds": [lo, hi]}
    later = any(STAGE in r and int(r[STAGE]) > stage_index for r in scanned["rows"])
    finished = scanned["exit_code"] == 0
    info["complete"] = bool(later or finished)
    if not rows:
        info["reason"] = f"no episode rows for stage/index {stage_index} in ({lo:,.0f}, {hi:,.0f}]"
        return None, info
    if not info["complete"]:
        info["reason"] = "stage not complete (no later stage logged, no clean exit)"
        return None, info
    kept = weighted(rows, lo, weighting, min_window_n)
    e = np.array([k[0] for k in kept])
    w = np.array([k[1] for k in kept])
    last = float(e[-1]) if len(e) else lo
    info["last_episode"] = last
    info["reached_boundary"] = last >= hi - BOUNDARY_SLACK_EPISODES    # pilot_readout's `done`
    if last - lo < window:
        info["reason"] = f"stage holds {last - lo:,.0f} < window {window:,.0f} episodes"
        return None, info
    v = np.array([k[2].get(key, np.nan) for k in kept])
    m = (e > last - window) & (e <= last) & ~np.isnan(v)
    info["rows_used"] = int(m.sum())
    if not m.any() or w[m].sum() <= 0:
        info["reason"] = f"no {key} rows in the window"
        return None, info
    return float((v[m] * w[m]).sum() / w[m].sum()), info


def read_keys(scanned: dict, keys: list[str]) -> tuple[dict, dict]:
    """{key: (episode array, value array)} for history rows carrying `key`, each placed at an
    episode count by the join described in the module docstring. Returns (series, info) with
    the number of unmatched rows per key."""
    ep_by_ts: dict[float, float] = {}
    for r in scanned["rows"]:
        if "Episode/Steps" in r and NUM in r and TS in r:
            ep_by_ts.setdefault(r[TS], r[NUM])
    out, info = {}, {}
    for k in keys:
        eps, vals, unmatched = [], [], 0
        for r in scanned["rows"]:
            if k not in r:
                continue
            if NUM in r:
                ep = r[NUM]
            elif TS in r and r[TS] in ep_by_ts:
                ep = ep_by_ts[r[TS]]
            else:
                unmatched += 1
                continue
            if not math.isfinite(r[k]):
                continue
            eps.append(ep)
            vals.append(r[k])
        order = np.argsort(eps, kind="stable")
        out[k] = (np.asarray(eps)[order], np.asarray(vals)[order])
        info[k] = {"rows": len(eps), "unmatched": unmatched}
    return out, info
