#!/usr/bin/env python
"""Per-episode table of one Figure 5 re-collection scene set, read from the sweep's cell archives.

Why: the sweep's per-scene CSVs keep only the mean over each checkpoint's 100 episodes; the result
of each single episode lives only in the cell archives ``_scratch/<label>/<scene>/<step>.zip``.
The layout-sampling error bar and the episode-bootstrap standard errors need per-episode values,
so this table must exist, checked, before any archive is deleted (plan-review finding C1 in
docs/experiments/active/hypervigilance/LOOKALIKE_HALF_FACTORIAL_L05.md, "Figure 5 re-collection").

    extract_episodes.py <sweep spec .yaml> [--workers N] [--data-root R]

Reads the spec's ``output_dir`` (one set, e.g.
results/eval/avoidance/metrics_history_rppo_lookalike_hf_random_layout/healoff_food_sampled) and
writes ONE table, ``<output_dir>/_episodes/episodes.parquet``, one row per episode:

    scene_set, run, run_label, cond, animal, injury, step, step_M, episode_index, seed,
    <the 11 per-episode measures of cell_measures>, archive, archive_bytes, archive_sha256

``run`` is the run label without its ``_resumed<k>`` suffix (the session folders of one run share
it). The measures come from the same function the sweep uses (``avoidance_stats_heatmap.
episode_measures``, called through ``cell_measures``); nothing is re-implemented here.

Checks, per cell (any failure is an error; errors abort that run label, are listed, exit 1):
  * the archive holds exactly the spec's ``episodes`` recordings (100);
  * episode i has ``episode_index`` i and the seed ``eval_seeds[i]`` of the scene file (the same
    100 seeds, in the same order, in every cell);
  * ``cell_measures.cell_row`` over the archive's episodes equals the cell's CSV row, all 13
    columns (string-equal, or within 1e-4 if the formatting differs).
Only cells with a CSV row are extracted (an archive without a CSV row was not merged and cannot be
checked). Gaps -- an archive without a CSV row, or a CSV row with neither archive nor table rows --
are listed and give exit status 2 (the good cells are still written).

Incremental: a cell (run_label, cond, step) already in the table is skipped, so re-running after
more runs are tested reads only the new archives, and cells whose archives were pruned stay. The
table is rewritten atomically (tmp + rename) after every 10 run labels and at the end.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import math
import os
import re
import sys
import time
from multiprocessing import Pool
from pathlib import Path

os.environ.setdefault("JAX_PLATFORMS", "cpu")
REPO_ROOT = Path(__file__).resolve().parents[4]  # scripts/analysis/studies/half_factorial_l05/ -> repo

TABLE_REL = Path("_episodes") / "episodes.parquet"
RESUMED_RE = re.compile(r"_resumed\d*$")
FLOAT_TOL = 1e-4
FLUSH_EVERY = 10


def _setup_path():
    """Code imports always come from THIS repository (not from --data-root)."""
    for p in (str(REPO_ROOT), str(REPO_ROOT / "scripts" / "behavior_measures"),
              str(REPO_ROOT / "scripts" / "eval" / "dwell_sweep")):
        if p not in sys.path:
            sys.path.insert(0, p)


def mandatory(d, key, ctx="spec"):
    if key not in d or d[key] is None:
        raise ValueError(f"{ctx}: missing mandatory key '{key}'")
    return d[key]


def run_of(label):
    return RESUMED_RE.sub("", label)


def load_spec(spec_path, repo_root):
    """(spec, output_dir, probe_dir, conds, episodes) -- every key mandatory."""
    import yaml
    spec = yaml.safe_load(open(spec_path))
    if mandatory(spec, "algo") != "rppo":
        raise ValueError(f"spec algo must be rppo, got {spec['algo']!r}")
    out = repo_root / mandatory(spec, "output_dir")
    probe = repo_root / mandatory(spec, "probe")
    if not probe.is_dir():
        raise ValueError(f"spec probe {probe} is not a directory")
    conds = mandatory(spec, "conditions")
    conds = sorted(p.stem for p in probe.glob("avoid_*.yaml")) if conds == "all" else list(conds)
    episodes = int(mandatory(spec, "episodes"))
    for r in mandatory(spec, "runs"):
        mandatory(r, "label", "spec runs[]"); mandatory(r, "path", "spec runs[]")
    return spec, out, probe, conds, episodes


def expected_seeds(probe, conds, episodes):
    """{cond: tuple of the first `episodes` eval seeds} from each scene file, via the loader
    eval_rollout.py uses (load_env_config + load_behavior_measure_cfg)."""
    from src.environment.config_loader import load_env_config, load_behavior_measure_cfg
    out = {}
    for c in conds:
        bm = load_behavior_measure_cfg(load_env_config(str(probe / f"{c}.yaml")))
        if bm is None:
            raise ValueError(f"{probe / c}.yaml has no behavior_measures block")
        if len(bm.eval_seeds) < episodes:
            raise ValueError(f"{c}: {len(bm.eval_seeds)} eval seeds < spec episodes {episodes}")
        out[c] = tuple(int(s) for s in bm.eval_seeds[:episodes])
    return out


def read_csv_rows(csv_path):
    """{step: [13 strings in cell_measures.HEAD order]} of one per-scene CSV, or {} if absent."""
    from cell_measures import HEAD
    if not csv_path.exists():
        return {}
    with open(csv_path, newline="") as fh:
        return {int(r["step"]): [r.get(h, "") for h in HEAD] for r in csv.DictReader(fh)}


def rows_equal(a, b):
    """True if two cell rows agree: equal strings, or both numbers within FLOAT_TOL, or both empty."""
    if len(a) != len(b):
        return False
    for x, y in zip(a, b):
        x, y = str(x), str(y)
        if x == y:
            continue
        if x == "" or y == "":
            return False
        try:
            if abs(float(x) - float(y)) > FLOAT_TOL:
                return False
        except ValueError:
            return False
    return True


def sha256_file(path):
    h = hashlib.sha256()
    n = 0
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
            n += len(b)
    return n, h.hexdigest()


def _extract_cell(job):
    """Worker: per-episode rows of one cell + its checks. Returns (key, columns dict, errors)."""
    (label, cond, step, zip_path, csv_row, seeds, episodes) = job
    _setup_path()
    import src.utils.episode_bundle as EB
    from avoidance_stats_heatmap import episode_measures, KEYS
    from cell_measures import cell_row, EPISODE_PATTERN
    key = (label, cond, step)
    errs = []
    try:
        nbytes, sha = sha256_file(zip_path)
        names = EB.members(zip_path, EPISODE_PATTERN)
        eps = [EB.load_recording(zip_path, n) for n in names]
    except Exception as e:  # unreadable archive is an error, not a gap
        return key, None, [f"{zip_path}: cannot read ({type(e).__name__}: {e})"]
    if len(eps) != episodes:
        errs.append(f"{zip_path}: {len(eps)} episodes, expected {episodes}")
    idx = [int(ep["episode_index"]) for ep in eps]
    sd = [int(ep["seed"]) for ep in eps]
    if idx != list(range(len(eps))):
        errs.append(f"{zip_path}: episode_index not 0..{len(eps) - 1} in archive order")
    if tuple(sd) != tuple(seeds[:len(sd)]) or len(sd) != len(seeds):
        bad = next((i for i, (a, b) in enumerate(zip(sd, seeds)) if a != b), min(len(sd), len(seeds)))
        errs.append(f"{zip_path}: episode seeds differ from the scene's eval_seeds (first at index {bad})")
    row = cell_row(step, eps)
    if row is None or not rows_equal(row, csv_row):
        errs.append(f"{zip_path}: cell mean {row} != CSV row {csv_row}")
    if errs:
        return key, None, errs
    per = [episode_measures(ep) for ep in eps]
    cols = {"episode_index": idx, "seed": sd}
    for k in KEYS:
        cols[k] = [float(p[k]) for p in per]
    cols["archive_bytes"] = nbytes
    cols["archive_sha256"] = sha
    return key, cols, []


def load_table(path):
    import pyarrow.parquet as pq
    if not path.exists():
        return None
    return pq.read_table(path)


def done_keys(table):
    if table is None:
        return set()
    t = table.select(["run_label", "cond", "step"]).to_pydict()
    return set(zip(t["run_label"], t["cond"], (int(s) for s in t["step"])))


def build_table(scene_set, label, cond, step, cols, archive_rel):
    import pyarrow as pa
    from avoidance_stats_heatmap import KEYS, split_cfg
    n = len(cols["seed"])
    animal, inj = split_cfg(cond)
    data = {
        "scene_set": pa.array([scene_set] * n),
        "run": pa.array([run_of(label)] * n),
        "run_label": pa.array([label] * n),
        "cond": pa.array([cond] * n),
        "animal": pa.array([animal] * n),
        "injury": pa.array([int(inj)] * n, pa.int16()),
        "step": pa.array([step] * n, pa.int64()),
        "step_M": pa.array([round(step / 1e6, 4)] * n, pa.float64()),
        "episode_index": pa.array(cols["episode_index"], pa.int32()),
        "seed": pa.array(cols["seed"], pa.int64()),
    }
    for k in KEYS:
        data[k] = pa.array(cols[k], pa.float64())
    data["archive"] = pa.array([archive_rel] * n)
    data["archive_bytes"] = pa.array([cols["archive_bytes"]] * n, pa.int64())
    data["archive_sha256"] = pa.array([cols["archive_sha256"]] * n)
    return pa.table(data)


def write_table(path, tables):
    """Concatenate `tables` (old table first), sort, write atomically."""
    import pyarrow as pa
    import pyarrow.parquet as pq
    tables = [t for t in tables if t is not None and t.num_rows]
    if not tables:
        return 0
    # plain string columns in memory (sortable); parquet dictionary-encodes them on disk
    t = pa.concat_tables(tables, promote_options="permissive").combine_chunks()
    t = t.sort_by([("run_label", "ascending"), ("cond", "ascending"), ("step", "ascending"),
                   ("episode_index", "ascending")])
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".tmp-{os.getpid()}")
    pq.write_table(t, tmp, compression="zstd")
    os.replace(tmp, path)
    return t.num_rows


def plan_cells(spec, out, conds, have):
    """(jobs_by_label, gaps). jobs: (label, cond, step, zip, csv_row); gaps: messages."""
    import src.utils.episode_bundle as EB
    scratch = out / "_scratch"
    jobs, gaps = {}, []
    for r in spec["runs"]:
        label = r["label"]
        for cond in conds:
            csv_rows = read_csv_rows(out / label / f"{cond}.csv")
            cond_dir = scratch / label / cond
            on_disk = set(int(s) for s in EB.step_names(cond_dir)) if cond_dir.is_dir() else set()
            for s in sorted(on_disk - set(csv_rows)):
                gaps.append(f"{label}/{cond}/{s}: archive without a CSV row (not merged), skipped")
            for s, row in sorted(csv_rows.items()):
                if (label, cond, s) in have:
                    continue
                z = cond_dir / f"{s}{EB.BUNDLE_SUFFIX}"
                if not z.is_file():
                    gaps.append(f"{label}/{cond}/{s}: CSV row but no archive and no table rows")
                    continue
                jobs.setdefault(label, []).append((label, cond, s, z, row))
    return jobs, gaps


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec", help="the set's sweep spec (configs/eval_sweeps/lookalike_hf_random_layout/...)")
    ap.add_argument("--workers", type=int, default=min(os.cpu_count() or 4, 16))
    ap.add_argument("--data-root", default=str(REPO_ROOT),
                    help="root the spec's paths are relative to (default: this repository; tests "
                         "point it at a synthetic copy). Code is always imported from this repository.")
    a = ap.parse_args(argv)
    repo = Path(a.data_root).resolve()
    _setup_path()
    spec, out, probe, conds, episodes = load_spec(a.spec, repo)
    scene_set = out.name
    seeds = expected_seeds(probe, conds, episodes)
    table_path = out / TABLE_REL
    old = load_table(table_path)
    have = done_keys(old)
    jobs, gaps = plan_cells(spec, out, conds, have)
    n_jobs = sum(len(v) for v in jobs.values())
    print(f"[extract] {scene_set}: {len(spec['runs'])} labels x {len(conds)} scenes; "
          f"{len(have)} cells already in the table, {n_jobs} to extract, {len(gaps)} gap(s)")
    errors, new_tables, n_new_cells, labels_since_flush = [], [], 0, 0
    t0 = time.time()
    with Pool(max(1, a.workers)) as pool:
        for li, (label, js) in enumerate(sorted(jobs.items())):
            work = [(lab, c, s, str(z), row, seeds[c], episodes) for (lab, c, s, z, row) in js]
            res = pool.map(_extract_cell, work, chunksize=4)
            lab_errs = [e for _, _, es in res for e in es]
            if lab_errs:
                errors.extend(lab_errs)
                print(f"  [{li + 1}/{len(jobs)}] {label}: {len(lab_errs)} ERROR(S), label not written; "
                      f"first: {lab_errs[0]}")
                continue
            for (lab, c, s, z, _row), (_k, cols, _e) in zip(js, res):
                rel = Path(z).relative_to(repo).as_posix()
                new_tables.append(build_table(scene_set, lab, c, s, cols, rel))
            n_new_cells += len(js)
            labels_since_flush += 1
            print(f"  [{li + 1}/{len(jobs)}] {label}: {len(js)} cells ok ({time.time() - t0:.0f}s)")
            if labels_since_flush >= FLUSH_EVERY:
                old = load_table(table_path)
                write_table(table_path, [old] + new_tables)
                new_tables, labels_since_flush = [], 0
    if new_tables:
        old = load_table(table_path)
        write_table(table_path, [old] + new_tables)
    final = load_table(table_path)
    print(f"[extract] wrote {n_new_cells} new cells; table {table_path} holds "
          f"{0 if final is None else final.num_rows} episode rows "
          f"({0 if final is None else len(done_keys(final))} cells)")
    for g in gaps:
        print(f"  GAP {g}")
    for e in errors:
        print(f"  ERROR {e}")
    if errors:
        return 1
    return 2 if gaps else 0


if __name__ == "__main__":
    sys.exit(main())
