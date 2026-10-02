"""Shared helpers for the level-05 body-interactions store analyses.

Run-agnostic: every run, label, band, range and threshold comes from the analysis manifest YAML
(e.g. docs/experiments/active/level05_body_interactions/analysis_manifest.yaml) and the collection
spec it names. Nothing here knows the 32 runs of this study.

Row convention (docs/environment/TRAJECTORY_STORE_SCHEMA.md §1): a step store has T+1 rows per
episode; row t carries the state at t (position, injury, nutrition, `agent_in_bush`, `obs_true`),
while `ate_food` belongs to the step that ARRIVED at t. The analyses therefore use DECISION rows:
rows t = 0..T-1, i.e. every state the policy acted from. Body state and bush occupancy are read at
t; "ate" means `ate_food` on row t+1 (the action taken from state t ate).
"""
from __future__ import annotations

import copy
import json
import os
import re
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[4]      # scripts/analysis/studies/<study>/ -> repo root
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MANDATORY = ("collection_spec", "out_dir", "factors", "agents", "difference", "reference_label",
             "checkpoint", "late_window_checkpoints", "nutrition_bands", "injury_ranges",
             "min_steps_per_cell", "felt_injury_quantiles", "felt_injury_slot", "temperature_slot",
             "gain_bins", "gain_nutrition_range", "gain_injury_range",
             "gain_temperature_percentiles", "min_steps_per_gain_bin",
             "survival_readout_fraction", "collapse_fraction", "lenth_alpha", "wandb_ids")
LABEL_RE = re.compile(r"^w([01]+)_([A-Za-z0-9]+)$")
# Tooling tests only: accept stores whose collection is still running. Set by a script's
# --max-shards test mode, whose outputs are stamped PARTIAL.
ALLOW_INCOMPLETE = False


def abs_path(p) -> Path:
    p = Path(p)
    return p if p.is_absolute() else ROOT / p


def load_manifest(path) -> dict:
    man = yaml.safe_load(Path(path).read_text())
    missing = [k for k in MANDATORY if k not in man or man[k] is None]
    if missing:
        raise ValueError(f"{path}: analysis manifest lacks mandatory key(s) {missing}")
    spec = yaml.safe_load(abs_path(man["collection_spec"]).read_text())
    for k in ("nutrition_bands", "injury_ranges"):         # numeric, or fail here
        man[k] = {n: [float(v[0]), float(v[1])] for n, v in man[k].items()}
    man["_spec"] = spec
    runs = []
    for r in spec["runs"]:
        label = r.get("label")
        m = LABEL_RE.match(label or "")
        if not m:
            raise ValueError(f"run label {label!r} is not of the form w<bits>_<agent>")
        code, agent = m.groups()
        if len(code) != len(man["factors"]):
            raise ValueError(f"{label}: world code has {len(code)} digits, manifest has "
                             f"{len(man['factors'])} factors")
        if agent not in man["agents"]:
            raise ValueError(f"{label}: agent {agent!r} not in manifest agents {man['agents']}")
        runs.append({"label": label, "world": "w" + code, "code": code, "agent": agent,
                     "path": r["path"], "run_name": Path(r["path"]).name})
    man["_runs"] = runs
    return man


def out_dir(man) -> Path:
    d = abs_path(man["out_dir"])
    d.mkdir(parents=True, exist_ok=True)
    return d


# ------------------------------------------------------------------------------------ stores --
def run_stores(man, run) -> list[tuple[int, Path]]:
    """All COMPLETE stores of a run under the spec's out_root, as (ckpt_step, dir), newest first.
    A store is complete when its manifest's n_episodes shards are all present."""
    from src.utils.trajectory_store import completed_blocks, read_manifest
    root = abs_path(man["_spec"]["out_root"]) / run["run_name"]
    out = []
    for mf in root.glob("*/*/_manifest.json"):
        d = mf.parent
        m = read_manifest(d)
        n_blocks = -(-int(m["n_episodes"]) // int(m["shard_episodes"]))
        if len(completed_blocks(d)) == n_blocks or (ALLOW_INCOMPLETE and completed_blocks(d)):
            out.append((int(m["ckpt_step"]), d))
    return sorted(out, reverse=True)


def final_step(run) -> int:
    steps = [int(p.name) for p in (abs_path(run["path"]) / "models").iterdir() if p.name.isdigit()]
    return max(steps)


def select_stores(man, run, pooled: bool) -> list[tuple[int, Path]]:
    """The store(s) a measure reads. pooled=False: the final checkpoint's store only (error if the
    final checkpoint has none). pooled=True: the newest `late_window_checkpoints` checkpoints, all
    of which must have a complete store; returns [] if any is missing."""
    stores = dict(run_stores(man, run))
    ckpts = sorted((int(p.name) for p in (abs_path(run["path"]) / "models").iterdir()
                    if p.name.isdigit()), reverse=True)
    if not pooled:
        return [(ckpts[0], stores[ckpts[0]])] if ckpts[0] in stores else []
    want = ckpts[:int(man["late_window_checkpoints"])]
    if not all(c in stores for c in want):
        return []
    return [(c, stores[c]) for c in want]


def shard_files(store_dir: Path, max_shards: int | None = None, prefix: str = "steps") -> list[Path]:
    """Shards of COMPLETED blocks only (a block is complete iff both its shards exist)."""
    from src.utils.trajectory_store import completed_blocks, shard_names
    fs = [store_dir / shard_names(b)[0 if prefix == "episodes" else 1] for b in sorted(completed_blocks(store_dir))]
    return fs[:max_shards] if max_shards else fs


# ------------------------------------------------------------------------ observation layout --
_LAYOUT_CACHE: dict = {}


def store_layout(store_dir: Path) -> dict:
    """Slot offsets of obs_true and the fire-obstacle mask, from the run's OWN saved config built
    exactly as the collector builds it (saved-config compat on a deep copy, then load_env_params).
    The manifest's `observation_breakdown` is key-sorted JSON and so loses the order; the order
    comes from src.environment.sensor.get_observation_breakdown."""
    key = str(store_dir)
    if key in _LAYOUT_CACHE:
        return _LAYOUT_CACHE[key]
    from src.environment.config_loader import load_env_params
    from src.environment.saved_config_compat import apply_saved_config_compat
    from src.environment.sensor import get_observation_breakdown
    from src.utils.config import Config
    from src.utils.trajectory_store import read_manifest
    m = read_manifest(store_dir)
    cfg_path = Path(m["run_path"]) / "models" / "config.yaml"
    cfg = copy.deepcopy(yaml.safe_load(cfg_path.read_text()))
    apply_saved_config_compat(cfg, source=str(cfg_path))
    P = load_env_params(Config(cfg))
    bd = get_observation_breakdown(P)
    if dict(sorted(bd.items())) != dict(sorted(m["observation_breakdown"].items())):
        raise ValueError(f"{store_dir}: observation breakdown rebuilt from the saved config "
                         f"{bd} differs from the store manifest {m['observation_breakdown']}")
    off, slots = 0, {}
    for name, dim in bd.items():
        slots[name] = (off, int(dim))
        off += int(dim)
    D = int(m["dims"]["D"])
    if off != D:
        raise ValueError(f"{store_dir}: breakdown width {off} != store D {D}")
    fire = np.asarray(P.obs_temp_ratio_high) > 0
    lay = {"slots": slots, "D": D, "fire_slots": fire, "max_nutrition": float(P.max_nutrition),
           "obs_precision": m["obs_precision"], "ckpt_step": int(m["ckpt_step"]),
           "n_episodes": int(m["n_episodes"])}
    _LAYOUT_CACHE[key] = lay
    return lay


def slot_index(lay: dict, name: str) -> int:
    if name not in lay["slots"]:
        raise ValueError(f"observation slot {name!r} absent; present: {list(lay['slots'])}")
    off, dim = lay["slots"][name]
    if dim != 1:
        raise ValueError(f"observation slot {name!r} has width {dim}, expected 1")
    return off


# ------------------------------------------------------------------------- per-shard reading --
def read_decision_rows(shard: Path, columns: list[str], obs_slots: list[int] | None,
                       D: int | None, next_cols: tuple[str, ...] = ()) -> dict:
    """Load one step shard and return numpy arrays restricted to DECISION rows (t = 0..T-1).

    `columns` are read at row t; `next_cols` are read at row t+1 (returned as '<name>_next').
    `obs_slots` (indices into obs_true) are returned as 'obs_<i>'."""
    import pyarrow.parquet as pq
    need = sorted(set(["episode_seed", "t"] + list(columns) + list(next_cols)
                      + (["obs_true"] if obs_slots else [])))
    tbl = pq.read_table(shard, columns=need)
    seed = tbl.column("episode_seed").to_numpy()
    t = tbl.column("t").to_numpy().astype(np.int64)
    n = seed.size
    # rows must be grouped by episode with t increasing by 1; check rather than assume
    same_next = np.zeros(n, bool)
    same_next[:-1] = seed[1:] == seed[:-1]
    if np.any(same_next[:-1] & (t[1:] != t[:-1] + 1)):
        raise ValueError(f"{shard}: step rows are not in (episode, t) order")
    dec = same_next                                   # a row with a successor in its episode
    out = {"episode_seed": seed[dec], "t": t[dec]}
    import pyarrow as pa
    from src.utils.trajectory_store import _list_column_to_2d

    def col(c):
        if pa.types.is_list(tbl.schema.field(c).type):       # fixed-width list -> (n, width)
            width = len(tbl.column(c)[0].as_py()) if n else 0
            return _list_column_to_2d(tbl, c, width)
        return tbl.column(c).to_numpy(zero_copy_only=False)
    for c in columns:
        out[c] = col(c)[dec]
    nxt = np.flatnonzero(dec) + 1
    for c in next_cols:
        out[c + "_next"] = col(c)[nxt]
    if obs_slots:
        ot = _list_column_to_2d(tbl, "obs_true", D)
        for i in obs_slots:
            out[f"obs_{i}"] = ot[dec, i].astype(np.float64)
    return out


def parallel_map(fn, items, workers: int):
    if workers <= 1:
        return [fn(x) for x in items]
    # spawn, not fork: the parent has imported JAX (store_layout), and forking a multithreaded
    # JAX process can deadlock. Workers only read parquet with numpy/pyarrow.
    import multiprocessing as mp
    with ProcessPoolExecutor(max_workers=workers, mp_context=mp.get_context("spawn")) as ex:
        return list(ex.map(fn, items))


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=1, default=_json_default))
    os.replace(tmp, path)


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, Path):
        return str(o)
    raise TypeError(type(o))
