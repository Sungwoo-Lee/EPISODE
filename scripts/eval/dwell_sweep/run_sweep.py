#!/usr/bin/env python
"""Dwell-history / behavior-metrics sweep driver — the self-serve entry point for the
promoted-from-tmp/ dwell-history pipeline (see README.md for the full picture).

What this reproduces: this session built (and proved, across ~7 sweeps) a working but
gitignored pipeline in tmp/ that, for a set of training runs, rolls out each saved
checkpoint against a battery of fixed "behavior probe" scenarios (e.g. "a predator is
present" vs "no animal"), computes 11 behavior measures per rollout (time spent hiding in
the bush, how close the agent lets a predator get, etc.), and plots how those measures
evolve over training. This script is that pipeline, cleaned up, unified across the two
supported algorithms (rPPO and Dreamer), and committed so it can be re-run any time a
training run advances instead of hand-assembled per sweep.

End-to-end, given a YAML spec (see README.md "Spec schema"), this script:
  1. resolves each run's directory + enumerates its saved checkpoints,
  2. skips checkpoints already present in that run's output CSV (incremental),
  3. LPT-partitions the remaining (run, condition) work across the nodes (spec or --nodes),
  4. writes a provenance snapshot incl. a COPY of the worker files, and launches that copy on
     each node via run_command.py. On the node, each worklist line plays its episodes into
     node-local staging; finish_cells.py then writes ONE archive per checkpoint x scene cell
     (`_scratch/<label>/<cond>/<step>.zip`) and the cell's CSV row into a small rows table
     (plan docs/develop/active/refactors/SWEEP_EPISODE_BUNDLES_AND_ON_NODE_MEASURES.md),
  5. polls the nodes with liveness checks (done / dead / stalled / never started),
  6. collates: merges the nodes' rows tables into `<out>/<run_label>/<condition>.csv` after a
     coverage check (every launched cell has exactly one row with the full episode count; a
     (run, scene) group with any hole is NOT merged and is listed; non-zero exit),
  7. renders the requested measures via plot_summary.py.

Every launch (not --dry-run) first writes a provenance snapshot, the test-side counterpart of the
`models/config.yaml` + `provenance.json` a training run saves:
  <output_dir>/_provenance/<YYYYMMDD_HHMMSS>/      (the folder name is the launch id)
      spec.yaml                  the sweep spec exactly as given
      provenance.json            git commit / branch / uncommitted changes under configs/ src/ scripts/,
                                 start time, host, command line, nodes, npar, episodes, which
                                 checkpoint steps of which runs this launch evaluates, the exact
                                 list of cells, and the sha256 of the worker files
      scenes/<cond>.yaml         each scene file as written
      scenes/<cond>.resolved.yaml  the same scene after its `extends:` chain (load_env_config, the
                                 loader eval_rollout.py uses), so a later edit to a parent world
                                 cannot silently change what an existing result meant
      worker/                    sweep_worker.sh, finish_cells.py, cell_measures.py as launched; the
                                 nodes run THESE copies, so no later edit can reach a running sweep
A scene that does not resolve stops the sweep before anything is launched. Why: on 2026-10-06 a
cross-run comparison mixed two test-scene sets and the settings had to be re-derived from today's
files (docs/llm_wiki/entries/behavior_measures/20261006_0758_test_scene_confound_level05_modulator_gap.md).

Usage:
  /home/vncuser/miniconda3/envs/grid_world_pain/bin/python \\
      scripts/eval/dwell_sweep/run_sweep.py configs/eval_sweeps/basic04_variants_rppo.yaml
  ... --dry-run   # build the worklist + LPT partition, print launch commands, don't launch
  ... --max-checkpoints 3   # cap each (run, condition) to its newest N pending checkpoints
  ... --nodes 105,110       # override spec.nodes
  ... --status              # per-node liveness + per-launch collation state, then exit
  ... --collate-only [--launch ID]   # re-collate a finished launch from its rows tables
  ... --collate-only --from-bundles  # recovery: score every pending cell from its archive/folder
"""
import argparse
import csv
import glob as globmod
import hashlib
import json
import multiprocessing as mp
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
import traceback
from collections import defaultdict
from pathlib import Path

import yaml

_HERE = Path(__file__).resolve()
REPO_ROOT = _HERE.parents[3]  # scripts/eval/dwell_sweep/run_sweep.py -> repo root (3 up)
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "behavior_measures"))
sys.path.insert(0, str(_HERE.parent))
from avoidance_stats_heatmap import KEYS  # noqa: E402,F401 (re-exported: experiment_eval_checkpoint.py imports KEYS from here)
from cell_measures import HEAD, measure_cell, measure_cell_n  # noqa: E402 (the ONE row-arithmetic site)
import src.utils.episode_bundle as EB  # noqa: E402
import plot_summary  # noqa: E402

PY = "/home/vncuser/miniconda3/envs/grid_world_pain/bin/python"
RUN_COMMAND = REPO_ROOT / "run_command.py"
WORKER = _HERE.parent / "sweep_worker.sh"
#: copied into _provenance/<launch_id>/worker/ at every launch; the nodes run the copies (C2).
WORKER_FILES = ("sweep_worker.sh", "finish_cells.py", "cell_measures.py")
FORMAT = "bundles-1"   # written to <scratch>/_format on the first new-code launch into a root

# Liveness thresholds (operational, not experiment settings; plan F4.7). Seconds.
HEARTBEAT_STALE_S = 600    # alive_<node> content unchanged this long -> stalled
PROGRESS_STALE_S = 1200    # lines-done counter unchanged this long -> stalled
START_GRACE_S = 300        # no started_<node> this long after launch -> never started
COLLATE_BEAT_S = 60        # collation heartbeat period
COLLATE_STALE_S = 300      # .alive older than this with no .done/.failed -> DEAD
ONE_NODE_WARN_LINES = 50   # warn when one node gets more lines than this

CLEAN_PROBE_DIR = REPO_ROOT / "configs/environment/experiment/archive/behavior_probes/core/avoidance"
NOISE_PROBE_DIR = REPO_ROOT / "configs/environment/experiment/archive/behavior_probes/explore/avoidance_stat_noise"

# Tuned NPAR defaults (see README.md "Tuning notes"): rPPO's single-env eval is light
# enough for ~1 process/core; batched Dreamer's vmap parallelises across cores on its
# own even with thread caps, so it needs a much lower process count.
DEFAULT_NPAR = {"rppo": 18, "dreamer": 5}
X_AXIS_DEFAULT = {"rppo": "steps", "dreamer": "episodes"}
ROWS_KEY = ("run_label", "cond", "step")


def mandatory(d, key, ctx=""):
    if key not in d or d[key] is None:
        suffix = f" ({ctx})" if ctx else ""
        raise ValueError(f"eval-sweep spec missing mandatory key '{key}'{suffix}")
    return d[key]


def load_spec(path):
    with open(path) as f:
        spec = yaml.safe_load(f)
    for k in ("name", "algo", "runs", "conditions", "nodes"):
        mandatory(spec, k)
    if spec["algo"] not in ("rppo", "dreamer"):
        raise ValueError(f"spec.algo must be 'rppo' or 'dreamer', got {spec['algo']!r}")
    return spec


def resolve_run_dir(path_or_glob, algo):
    has_glob = any(c in path_or_glob for c in "*?[")
    if has_glob:
        matches = sorted(globmod.glob(str(REPO_ROOT / path_or_glob)))
        if len(matches) != 1:
            raise ValueError(
                f"runs[].path glob '{path_or_glob}' resolved to {len(matches)} directories "
                f"(need exactly 1): {matches}"
            )
        run_dir = Path(matches[0])
    else:
        p = Path(path_or_glob)
        run_dir = p if p.is_absolute() else REPO_ROOT / p
    expected_root = "JAX_RecurrentPPO" if algo == "rppo" else "JAX_DreamerSRL"
    if expected_root not in str(run_dir):
        print(f"  WARNING: run dir '{run_dir}' does not contain '{expected_root}' "
              f"(spec.algo={algo!r}) -- double check this run is the right algorithm.")
    return run_dir


def list_checkpoints(algo, run_dir):
    sub = "models" if algo == "rppo" else "checkpoints"
    d = run_dir / sub
    if not d.is_dir():
        return []
    return sorted(int(p.name) for p in d.iterdir() if p.name.isdigit())


def checkpoint_path(algo, run_dir, step):
    sub = "models" if algo == "rppo" else "checkpoints"
    return run_dir / sub / str(step)


def default_agent_config(run_dir):
    cand = run_dir / "models" / "agent_config.yaml"
    if not cand.exists():
        raise ValueError(
            f"Dreamer run {run_dir} has no models/agent_config.yaml and its spec entry "
            "gives no explicit 'agent_config' override -- one of the two is required."
        )
    return cand


def probe_dir(probe):
    # Named presets, or any repo-relative path to a directory of probe configs
    # (e.g. a bush-refuge-matched battery). Backward compatible: "clean"/"noise"
    # keep their meaning; anything else is treated as a repo-relative dir path.
    if probe == "clean":
        return CLEAN_PROBE_DIR
    if probe == "noise":
        return NOISE_PROBE_DIR
    cand = REPO_ROOT / probe
    if cand.is_dir():
        return cand
    raise ValueError(
        f"spec.probe must be 'clean', 'noise', or a repo-relative probe-dir "
        f"path; got {probe!r} (resolved {cand}, not a directory)")


def resolve_conditions(spec):
    pdir = probe_dir(spec.get("probe", "clean"))
    conds = mandatory(spec, "conditions")
    if conds == "all":
        return sorted(p.stem for p in pdir.glob("avoid_*.yaml"))
    return list(conds)


def read_existing_max_step(csv_path):
    if not csv_path.exists():
        return 0
    maxstep = 0
    with open(csv_path) as f:
        for row in csv.DictReader(f):
            try:
                maxstep = max(maxstep, int(row["step"]))
            except (KeyError, ValueError, TypeError):
                pass
    return maxstep


def build_groups(spec, output_dir, max_checkpoints):
    """Build the two group views this driver needs, at DIFFERENT granularities:

    - `checkpoint_groups`: ONE entry per (run, checkpoint) that has at least one
      PENDING condition -- `{"run_label", "run_dir", "step", "agent_config",
      "conds": [{"cond","cfg_path","out_csv","out"}, ...]}` (each entry's `conds`
      list holds ONLY the conditions still pending for THAT checkpoint -- a
      checkpoint may be ahead on some conditions and behind on others under the
      incremental filter). This is the LPT-partition/worklist unit: a whole
      checkpoint (and every one of its pending conditions) is always routed to
      ONE node, so a single `eval_rollout.py --config-list` process can build the
      model + restore that checkpoint ONCE and loop over every pending condition
      -- the entire point of this grouping (see module docstring).
    - `cond_groups`: ONE entry per (run, cond) that has >=1 pending checkpoint --
      `{"run_label", "cond", "out_csv"}` -- used only by `aggregate()`, which
      still refreshes CSVs per (run, cond) exactly as before this change.
    """
    algo = spec["algo"]
    pdir = probe_dir(spec.get("probe", "clean"))
    conditions = resolve_conditions(spec)
    checkpoint_groups = []
    cond_groups = []
    for run in spec["runs"]:
        label = mandatory(run, "label", "runs[]")
        path = mandatory(run, "path", "runs[]")
        run_dir = resolve_run_dir(path, algo)
        all_ckpts = list_checkpoints(algo, run_dir)
        agent_config = run.get("agent_config")
        if agent_config:
            agent_config = REPO_ROOT / agent_config if not Path(agent_config).is_absolute() else Path(agent_config)
        elif algo == "dreamer":
            agent_config = default_agent_config(run_dir)

        # Per-condition pending-checkpoint sets, same incremental + max_checkpoints
        # semantics as before (each condition capped to its OWN newest-N pending).
        pending_by_cond = {}
        cfg_by_cond = {}
        for cond in conditions:
            cfg_path = pdir / f"{cond}.yaml"
            if not cfg_path.exists():
                raise ValueError(f"condition config not found: {cfg_path}")
            out_csv = output_dir / label / f"{cond}.csv"
            maxdone = read_existing_max_step(out_csv)
            newck = [c for c in all_ckpts if c > maxdone]
            if max_checkpoints:
                newck = newck[-max_checkpoints:]
            cfg_by_cond[cond] = (cfg_path, out_csv)
            if newck:
                pending_by_cond[cond] = set(newck)
                cond_groups.append({"run_label": label, "cond": cond, "out_csv": out_csv})

        # Union of pending steps across all conditions for this run -> one
        # checkpoint_groups entry per step, carrying only the conditions pending
        # for THAT step.
        all_pending_steps = sorted(set().union(*pending_by_cond.values())) if pending_by_cond else []
        for step in all_pending_steps:
            conds_here = [c for c in conditions if step in pending_by_cond.get(c, ())]
            if not conds_here:
                continue
            checkpoint_groups.append({
                "run_label": label, "run_dir": run_dir, "step": step,
                "agent_config": agent_config,
                "conds": [
                    {"cond": c, "cfg_path": cfg_by_cond[c][0], "out_csv": cfg_by_cond[c][1]}
                    for c in conds_here
                ],
            })
    return checkpoint_groups, cond_groups


def lpt_partition(checkpoint_groups, nodes):
    """Longest-Processing-Time-first: sort (run,checkpoint) cells by pending-condition
    count descending, assign each WHOLE cell (checkpoint + all its pending conditions)
    to whichever node currently has the smallest running total. A cell is never split
    across nodes -- that's what lets ONE eval_rollout.py process build the model +
    restore that checkpoint once and loop over every pending condition."""
    loads = {n: 0 for n in nodes}
    buckets = {n: [] for n in nodes}
    for g in sorted(checkpoint_groups, key=lambda g: -len(g["conds"])):
        n = min(nodes, key=lambda n: loads[n])
        buckets[n].append(g)
        loads[n] += len(g["conds"])
    return buckets, loads


def write_worklist(node, checkpoint_groups, scratch_root, algo):
    """One line per (run, checkpoint) cell: `CHECKPOINT|AGENT_OR_-|EPISODE_OR_-|
    CFG1,OUT1;CFG2,OUT2;...` -- `sweep_worker.sh` expands the last field into a
    `--config-list` file and calls `eval_rollout.py` ONCE per line, evaluating every
    listed condition against that one checkpoint build+restore."""
    lines = []
    for g in checkpoint_groups:
        ck = checkpoint_path(algo, g["run_dir"], g["step"])
        agent = str(g["agent_config"]) if g["agent_config"] else "-"
        cfg_out = ";".join(
            f'{c["cfg_path"]},{scratch_root / g["run_label"] / c["cond"] / str(g["step"])}'
            for c in g["conds"]
        )
        lines.append(f'{ck}|{agent}|-|{cfg_out}')
    wl_dir = scratch_root / "_worklists"
    wl_dir.mkdir(parents=True, exist_ok=True)
    wl_path = wl_dir / f"worklist_{node}.txt"
    wl_path.write_text("\n".join(lines) + ("\n" if lines else ""))
    return wl_path, len(lines)


def worker_command(worker_sh, wl_path, node, npar, episodes, launch_id):
    """The node command: the COPIED worker, with the repo root as its mandatory 6th argument
    (plan-review N1: the copy cannot find the repo by path depth)."""
    return (f"PYTHONUNBUFFERED=1 bash {worker_sh} {wl_path} {node} {npar} {episodes} "
            f"{launch_id} {REPO_ROOT}")


def launch_node(node, worker_sh, wl_path, npar, episodes, launch_id, dry_run):
    cmd = worker_command(worker_sh, wl_path, node, npar, episodes, launch_id)
    full = [PY, str(RUN_COMMAND), str(node), cmd, "--no-tail"]
    print(f"  launch: {' '.join(full)}")
    if dry_run:
        return
    subprocess.run(full, check=True)


# ------------------------------------------------------------------------------ liveness ----
def _read(p):
    try:
        return Path(p).read_text()
    except OSError:
        return None


def _tail(p, n=5):
    t = _read(p)
    return "" if t is None else "\n".join(t.rstrip().splitlines()[-n:])


def poll_done(scratch_root, nodes, interval=15, clock=time.time, sleep=time.sleep):
    """Wait until every node is done or unhealthy. Returns {node: status}, status one of
    'done', 'dead' (exit_ without done_), 'stalled' (heartbeat content unchanged for
    HEARTBEAT_STALE_S, or its lines-done counter unchanged for PROGRESS_STALE_S),
    'never_started' (no started_ within START_GRACE_S). Ages are measured on THIS host's clock
    from when a change was last SEEN, so node/NAS clock skew does not matter. An unhealthy node
    gets a FAILED_<node> marker and its prog_/fail_/exit_ tails printed; healthy nodes are still
    waited for. Before 2026-10 a dead worker made this loop forever (plan A3)."""
    mark = Path(scratch_root) / "_run_markers"
    nodes = [str(n) for n in nodes]
    pending = set(nodes)
    status = {}
    t0 = clock()
    seen_alive = {n: (None, t0) for n in nodes}
    seen_lines = {n: (None, t0) for n in nodes}
    while pending:
        now = clock()
        for n in sorted(pending):
            why = None
            if (mark / f"done_{n}").exists():
                status[n] = "done"
                print(f"  node {n} done ({now - t0:.0f}s elapsed)")
            elif (mark / f"exit_{n}").exists():
                status[n], why = "dead", f"worker exited without done_ ({_tail(mark / f'exit_{n}', 1)})"
            elif not (mark / f"started_{n}").exists():
                if now - t0 > START_GRACE_S:
                    status[n], why = "never_started", f"no started_{n} after {START_GRACE_S}s"
            else:
                alive = _read(mark / f"alive_{n}")
                if alive != seen_alive[n][0]:
                    seen_alive[n] = (alive, now)
                elif now - seen_alive[n][1] > HEARTBEAT_STALE_S:
                    status[n], why = "stalled", f"heartbeat unchanged for {now - seen_alive[n][1]:.0f}s"
                fields = (alive or "").split()
                lines = fields[1] if len(fields) > 1 else None
                if n not in status:
                    if lines != seen_lines[n][0]:
                        seen_lines[n] = (lines, now)
                    elif now - seen_lines[n][1] > PROGRESS_STALE_S:
                        status[n], why = "stalled", f"no worklist line finished for {now - seen_lines[n][1]:.0f}s"
            if n in status:
                pending.discard(n)
            if why:
                print(f"  NODE {n} {status[n].upper()}: {why}")
                for f in (f"prog_{n}", f"fail_{n}", f"exit_{n}"):
                    t = _tail(mark / f)
                    if t:
                        print(f"    {f}: {t}")
                (mark / f"FAILED_{n}").write_text(f"{status[n]} {why} {time.ctime()}\n")
        if pending:
            sleep(interval)
    bad = [n for n in nodes if status[n] != "done"]
    print(f"  {len(nodes) - len(bad)}/{len(nodes)} node(s) done in {clock() - t0:.0f}s"
          + (f"; UNHEALTHY: {', '.join(f'{n}={status[n]}' for n in bad)}" if bad else ""))
    return status


def report_fails(scratch_root, nodes):
    """Print count + first lines of every fail_<node>; returns the total count."""
    mark = Path(scratch_root) / "_run_markers"
    total = 0
    for n in nodes:
        t = _read(mark / f"fail_{n}")
        if t:
            lines = t.strip().splitlines()
            total += len(lines)
            print(f"  fail_{n}: {len(lines)} failed worklist line(s); first: {lines[0][:300]}")
    return total


# ------------------------------------------------------------------------- measuring cells ----
def _measure_cell(step_dir):
    """(step:int, row:list) for ONE cell -- a legacy folder or a `<step>.zip` archive -- or None if
    it holds no recordings. Kept with this name and contract for
    scripts/eval/experiment_eval_checkpoint.py; the arithmetic lives in cell_measures.cell_row."""
    return measure_cell(step_dir)


def _measure_cell_n(cell):
    return measure_cell_n(cell)


def measure_groups(groups, scratch_root, n_workers=None):
    """Score every cell present (archive or legacy folder, via EB.step_names + EB.cell_path) of
    each (run, cond) group. Returns, per group, {step: (row, n_episodes)}. No CSV is read."""
    if n_workers is None:
        n_workers = min(os.cpu_count() or 8, 32)
    cells = []
    for gi, g in enumerate(groups):
        cond_dir = Path(scratch_root) / g["run_label"] / g["cond"]
        if not cond_dir.is_dir():
            continue
        for s in EB.step_names(cond_dir):
            cells.append((gi, str(EB.cell_path(cond_dir, s))))
    if n_workers <= 1 or len(cells) <= 1:
        results = [_measure_cell_n(c) for _, c in cells]
    else:
        with mp.Pool(processes=n_workers) as pool:
            results = pool.map(_measure_cell_n, [c for _, c in cells])   # order preserved
    out = [dict() for _ in groups]
    for (gi, _), res in zip(cells, results):
        if res is not None:
            step, row, n = res
            out[gi][step] = (row, n)
    return out


def _write_csv(out_csv, by_step):
    """Unchanged CSV write of the former aggregate(): header, rows sorted by step."""
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    rows = [by_step[s] for s in sorted(by_step)]
    with open(out_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(HEAD)
        for v in rows:
            w.writerow(v)


def _seed(out_csv):
    by_step = {}
    if out_csv.exists():
        for r in csv.DictReader(open(out_csv)):
            by_step[int(r["step"])] = [r.get(h, "") for h in HEAD]
    return by_step


def aggregate_from_bundles(groups, scratch_root, n_workers=None, seed_from_csv=True):
    """Recovery path (and the former aggregate()): score every cell on disk of each group from its
    archive or folder and MERGE into the group's CSV (never drops prior rows). seed_from_csv=False
    writes only what was measured (used by the gates, so a test cannot pass by echoing the CSV)."""
    measured = measure_groups(groups, scratch_root, n_workers)
    n_written = 0
    for g, m in zip(groups, measured):
        by_step = _seed(g["out_csv"]) if seed_from_csv else {}
        for step, (row, _n) in m.items():
            by_step[step] = row
        if not by_step:
            continue
        _write_csv(g["out_csv"], by_step)
        n_written += 1
    return n_written


# ---------------------------------------------------------------------------- collation ----
def read_rows(scratch_root, launch_id, nodes):
    """All rows of one launch: rows_<node>.csv, or the node's line pieces if the worker died
    before concatenating them."""
    base = Path(scratch_root) / "_rows" / launch_id
    rows = []
    for n in nodes:
        f = base / f"rows_{n}.csv"
        files = [f] if f.exists() else sorted((base / str(n)).glob("*.csv"))
        for p in files:
            with open(p, newline="") as fh:
                rows.extend(csv.DictReader(fh))
    return rows


def collate(cond_groups, scratch_root, launch_id, nodes, worklist_cells, episodes):
    """Merge one launch's rows tables into the per-scene CSVs, after a coverage check: every
    worklist cell (run_label, cond, step) has exactly one row and n_episodes == episodes.
    A (run, cond) group with ANY missing, duplicate or short cell is not merged at all (review
    M6: a partial merge would let the max-step incremental rule skip the holes forever).
    Returns (n_written, problems) with problems {(label, cond): [message, ...]}."""
    by_key = defaultdict(list)
    for r in read_rows(scratch_root, launch_id, nodes):
        by_key[(r["run_label"], r["cond"], int(r["step"]))].append(r)
    problems = defaultdict(list)
    for key in sorted(set(map(tuple, worklist_cells))):
        label, cond, step = key[0], key[1], int(key[2])
        rs = by_key.get((label, cond, step), [])
        if not rs:
            problems[(label, cond)].append(f"step {step}: no row")
        elif len(rs) > 1:
            problems[(label, cond)].append(f"step {step}: {len(rs)} rows")
        elif int(rs[0]["n_episodes"]) != int(episodes):
            problems[(label, cond)].append(f"step {step}: {rs[0]['n_episodes']} episodes, expected {episodes}")
    wanted = defaultdict(list)
    for label, cond, step in map(tuple, worklist_cells):
        wanted[(label, cond)].append(int(step))
    n_written = 0
    for g in cond_groups:
        k = (g["run_label"], g["cond"])
        if k in problems or k not in wanted:
            continue
        by_step = _seed(g["out_csv"])
        for step in wanted[k]:
            r = by_key[(k[0], k[1], step)][0]
            by_step[step] = [r[h] for h in HEAD]
        _write_csv(g["out_csv"], by_step)
        n_written += 1
    for k, msgs in sorted(problems.items()):
        print(f"  NOT MERGED {k[0]}/{k[1]}: {len(msgs)} problem cell(s); first: {msgs[0]}")
    return n_written, dict(problems)


def _cmark(scratch_root, cid, kind):
    return Path(scratch_root) / "_run_markers" / f"collate_{cid}.{kind}"


def with_collate_markers(scratch_root, cid, fn, beat_s=COLLATE_BEAT_S):
    """Run fn() between collate_<cid>.started and .done / .failed, touching .alive every beat_s
    from a daemon thread (review M5): a collation killed on ANY host is visible to --status as
    DEAD once .alive is older than COLLATE_STALE_S."""
    mk = lambda k: _cmark(scratch_root, cid, k)  # noqa: E731
    mk("started").parent.mkdir(parents=True, exist_ok=True)
    for k in ("done", "failed"):
        mk(k).unlink(missing_ok=True)
    mk("started").write_text(json.dumps({"host": socket.gethostname(), "pid": os.getpid(),
                                         "time": time.time()}) + "\n")
    stop = threading.Event()

    def beat():
        while not stop.is_set():
            mk("alive").write_text(f"{time.time()}\n")
            stop.wait(beat_s)
    th = threading.Thread(target=beat, daemon=True)
    th.start()
    try:
        res = fn()
    except BaseException:
        stop.set()
        mk("failed").write_text(traceback.format_exc())
        raise
    stop.set()
    mk("done").write_text(f"{time.time()}\n")
    return res


def collation_state(scratch_root, cid, now=None):
    """'running' | 'DEAD' | 'done' | 'failed' | 'never collated'."""
    now = time.time() if now is None else now
    if _cmark(scratch_root, cid, "done").exists():
        return "done"
    if _cmark(scratch_root, cid, "failed").exists():
        return "failed"
    if not _cmark(scratch_root, cid, "started").exists():
        return "never collated"
    a = _cmark(scratch_root, cid, "alive")
    age = now - (a.stat().st_mtime if a.exists() else _cmark(scratch_root, cid, "started").stat().st_mtime)
    return "DEAD" if age > COLLATE_STALE_S else "running"


def launches(output_dir):
    """[(launch_id, provenance dict)] of bundle-format launches, oldest first."""
    out = []
    for p in sorted((Path(output_dir) / "_provenance").glob("*/provenance.json")):
        try:
            prov = json.loads(p.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if prov.get("launch_format") == FORMAT:
            out.append((p.parent.name, prov))
    return out


def status(output_dir, now=None):
    """Print per-node liveness and per-launch collation state; returns the printed lines."""
    now = time.time() if now is None else now
    scratch = Path(output_dir) / "_scratch"
    mark = scratch / "_run_markers"
    lines = []
    nodes = sorted({p.name.split("_", 1)[1] for p in mark.glob("*_*")
                    if "." not in p.name and p.name.split("_", 1)[0] in ("npar", "started", "done", "exit", "alive")})
    for n in nodes:
        def age(f):
            p = mark / f
            return f"{now - p.stat().st_mtime:.0f}s ago" if p.exists() else "-"
        nl = len((_read(mark / f"lines_{n}") or "").split())
        nf = len((_read(mark / f"fail_{n}") or "").strip().splitlines())
        ex = (_read(mark / f"exit_{n}") or "").split("\n")[0] or "-"
        lines.append(f"node {n}: started {age(f'started_{n}')}, alive {age(f'alive_{n}')}, lines done {nl}, "
                     f"done {'yes' if (mark / f'done_{n}').exists() else 'no'}, exit {ex}, fails {nf}"
                     + (", FAILED" if (mark / f"FAILED_{n}").exists() else ""))
    for cid, prov in launches(output_dir):
        st = collation_state(scratch, cid, now)
        if st == "never collated" and all((mark / f"done_{n}").exists() for n in prov.get("nodes", [])):
            st = "workers done, never collated"
        lines.append(f"launch {cid}: nodes {prov.get('nodes')} -> {st}")
    for p in sorted(mark.glob("collate_*.started")):
        cid = p.name[len("collate_"):-len(".started")]
        if not (Path(output_dir) / "_provenance" / cid).is_dir():
            lines.append(f"collation {cid}: {collation_state(scratch, cid, now)}")
    for ln in lines:
        print(ln)
    return lines


def plot(spec, output_dir):
    algo = spec["algo"]
    x_axis = spec.get("x_axis") or X_AXIS_DEFAULT[algo]
    if x_axis == "steps":
        os.environ["XDIV"] = "1e6"
        os.environ["XLABEL"] = "training  (million steps)"
        os.environ.setdefault("XBOUNDARY", "10")
    elif x_axis == "episodes":
        os.environ["XDIV"] = "1e3"
        os.environ["XLABEL"] = "training  (thousand episodes)"
        os.environ["XBOUNDARY"] = ""
    else:
        raise ValueError(f"spec.x_axis must be 'steps' or 'episodes', got {x_axis!r}")
    # plot_summary reads these env vars at import time; re-apply them onto its module
    # globals since we imported it before the spec (and its x_axis) was known.
    plot_summary.XDIV = float(os.environ["XDIV"])
    plot_summary.XLABEL = os.environ["XLABEL"]
    plot_summary.XBND = os.environ["XBOUNDARY"]

    measures = spec.get("plot_measures", ["bush_hiding", "spatial_spread", "survival_steps"])
    figs = []
    for run in spec["runs"]:
        label = run["label"]
        level_dir = output_dir / label
        if not level_dir.is_dir():
            continue
        for m in measures:
            o = plot_summary.fig_for(str(level_dir), label, m)
            if o:
                figs.append(o)
    return figs


def _git(*a):
    r = subprocess.run(["git", *a], cwd=REPO_ROOT, capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(a)} failed: {r.stderr.strip()}")
    return r.stdout.strip()


def _sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def worklist_cells(checkpoint_groups):
    return sorted([g["run_label"], c["cond"], int(g["step"])] for g in checkpoint_groups for c in g["conds"])


def write_provenance(spec_path, spec, output_dir, checkpoint_groups, nodes, npar, episodes):
    """Snapshot the spec, the code version, every scene's resolved settings and the worker files
    for THIS launch. The folder name is the launch id; the nodes run worker/ from here."""
    import datetime
    from src.environment.config_loader import load_env_config
    from src.utils.config import dump_config_yaml

    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    snap = output_dir / "_provenance" / stamp
    (snap / "scenes").mkdir(parents=True, exist_ok=False)
    shutil.copy2(spec_path, snap / "spec.yaml")
    pdir = probe_dir(spec.get("probe", "clean"))
    conds = sorted({c["cond"] for g in checkpoint_groups for c in g["conds"]})
    for cond in conds:
        src = pdir / f"{cond}.yaml"
        shutil.copy2(src, snap / "scenes" / f"{cond}.yaml")
        with open(snap / "scenes" / f"{cond}.resolved.yaml", "w") as fh:
            dump_config_yaml(load_env_config(str(src)).to_dict(), fh)
    (snap / "worker").mkdir()
    for f in WORKER_FILES:
        shutil.copy2(_HERE.parent / f, snap / "worker" / f)
    steps = defaultdict(list)
    for g in checkpoint_groups:
        steps[g["run_label"]].append(int(g["step"]))
    runs = [{"label": r["label"], "path": r["path"], "steps_evaluated": sorted(steps.get(r["label"], []))}
            for r in spec["runs"]]
    dirty = _git("status", "--porcelain", "--", "configs", "src", "scripts")
    prov = {"started": datetime.datetime.now().isoformat(timespec="seconds"), "host": socket.gethostname(),
            "argv": sys.argv, "git_sha": _git("rev-parse", "HEAD"), "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
            "uncommitted_changes": dirty.splitlines(), "spec": str(spec_path), "probe_dir": str(pdir.relative_to(REPO_ROOT)),
            "conditions": conds, "nodes": nodes, "npar": npar, "episodes": episodes, "runs": runs,
            "launch_format": FORMAT, "repo_root": str(REPO_ROOT),
            "worker_sha256": {f: _sha256(snap / "worker" / f) for f in WORKER_FILES},
            "cells": worklist_cells(checkpoint_groups)}
    with open(snap / "provenance.json", "w") as fh:
        json.dump(prov, fh, indent=1)
    return snap


def check_lock(scratch_root):
    """Refuse to launch into a root that bundle_scratch.py is migrating (F4.12)."""
    lock = Path(scratch_root) / "_bundle.lock"
    if lock.exists():
        import bundle_scratch
        if not bundle_scratch.lock_is_stale(lock):
            raise SystemExit(f"{lock} is held by a migration ({_read(lock).strip()}); not launching")
        print(f"  WARNING: stale migration lock {lock} ({_read(lock).strip()}); "
              f"remove it with `bundle_scratch.py unlock`. Not launching.")
        raise SystemExit(f"stale lock {lock}")


def node_warning(nodes, n_lines):
    if len(nodes) == 1 and n_lines > ONE_NODE_WARN_LINES:
        print(f"  WARNING: {n_lines} worklist lines on ONE node ({nodes[0]}). List more usable nodes with "
              f"--nodes. Usable = no training process running (pgrep -f train.py), no other sweep's live "
              f"markers on it, no diary claim for today -- not merely 'GPU free' (this job is CPU-bound, "
              f"~18 processes per node).")


def _collate_only(args, spec, output_dir, scratch_root, agg_workers):
    if args.from_bundles:
        _, cond_groups = build_groups(spec, output_dir, None)
        cid = "frombundles_" + time.strftime("%Y%m%d_%H%M%S")
        n = with_collate_markers(scratch_root, cid,
                                 lambda: aggregate_from_bundles(cond_groups, scratch_root, agg_workers))
        print(f"  wrote/updated {n} CSV(s) from archives/folders on disk")
        return 0
    known = dict(launches(output_dir))
    if not known:
        raise SystemExit(f"no bundle-format launch under {output_dir}/_provenance; use --from-bundles")
    cid = args.launch or sorted(known)[-1]
    if cid not in known:
        raise SystemExit(f"launch {cid!r} not found among {sorted(known)}")
    prov = known[cid]
    nodes = [str(n) for n in prov["nodes"]]
    missing = [n for n in nodes if not (scratch_root / "_run_markers" / f"done_{n}").exists()]
    if missing:
        raise SystemExit(f"launch {cid}: node(s) {missing} have no done_ marker; "
                         f"use --from-bundles to score what is on disk")
    return _collate_launch(output_dir, scratch_root, cid, nodes, prov["cells"], prov["episodes"])


def _collate_launch(output_dir, scratch_root, cid, nodes, cells, episodes):
    groups = [{"run_label": lab, "cond": cond, "out_csv": output_dir / lab / f"{cond}.csv"}
              for lab, cond in sorted({(c[0], c[1]) for c in cells})]
    t = time.time()
    n, problems = with_collate_markers(
        scratch_root, cid, lambda: collate(groups, scratch_root, cid, nodes, cells, episodes))
    print(f"  wrote/updated {n} CSV(s) in {time.time() - t:.1f}s; {len(problems)} group(s) not merged")
    return 3 if problems else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec", help="Path to a sweep spec YAML (see README.md).")
    ap.add_argument("--dry-run", action="store_true",
                    help="Build the worklist + LPT partition, print launch commands, don't launch.")
    ap.add_argument("--max-checkpoints", type=int, default=None,
                    help="Cap each (run,condition) to its newest N pending checkpoints "
                         "(overrides spec.max_checkpoints; useful for a quick smoke test).")
    ap.add_argument("--agg-workers", type=int, default=None,
                    help="Process count for --from-bundles scoring (overrides spec.agg_workers; "
                         "default auto = min(os.cpu_count(), 32) on the driver host).")
    ap.add_argument("--nodes", default=None, help="Comma-separated node ids; overrides spec.nodes.")
    ap.add_argument("--status", action="store_true", help="Print node liveness + collation state; exit.")
    ap.add_argument("--collate-only", action="store_true",
                    help="Collate a finished launch (newest, or --launch ID) from its rows tables.")
    ap.add_argument("--launch", default=None, help="With --collate-only: the launch id to collate.")
    ap.add_argument("--from-bundles", action="store_true",
                    help="With --collate-only: score every pending cell on disk (recovery path).")
    args = ap.parse_args()

    spec = load_spec(args.spec)
    algo = spec["algo"]
    output_dir = REPO_ROOT / (spec.get("output_dir") or f"results/eval/avoidance/{spec['name']}")
    scratch_root = output_dir / "_scratch"
    npar = spec.get("npar") or DEFAULT_NPAR[algo]
    episodes = spec.get("episodes", 30)
    nodes = [str(n) for n in (args.nodes.split(",") if args.nodes else spec["nodes"])]
    max_checkpoints = args.max_checkpoints if args.max_checkpoints is not None else spec.get("max_checkpoints")
    agg_workers = args.agg_workers if args.agg_workers is not None else spec.get("agg_workers")

    if args.status:
        status(output_dir)
        return
    print(f"=== dwell sweep: {spec['name']} ({algo}) ===")
    print(f"output: {output_dir}")
    if args.collate_only:
        rc = _collate_only(args, spec, output_dir, scratch_root, agg_workers)
        print("Plotting...")
        print(f"  wrote {len(plot(spec, output_dir))} figure(s)")
        if rc:
            raise SystemExit(rc)
        return

    check_lock(scratch_root)
    checkpoint_groups, cond_groups = build_groups(spec, output_dir, max_checkpoints)
    total_ck = sum(len(g["conds"]) for g in checkpoint_groups)
    print(f"{len(checkpoint_groups)} (run,checkpoint) cell(s) with pending work "
          f"({total_ck} checkpoint-eval(s) = checkpoints x pending conditions total)")
    if total_ck == 0:
        print("Nothing to do -- every (run,condition) CSV is already up to date with the newest checkpoint.")
        return

    buckets, loads = lpt_partition(checkpoint_groups, nodes)
    for n in nodes:
        print(f"  node {n}: {len(buckets[n])} checkpoint cell(s), {loads[n]} checkpoint-eval(s)")
    node_warning(nodes, len(checkpoint_groups))

    wl_paths = {}
    for n in nodes:
        if not buckets[n]:
            continue
        wl_path, nlines = write_worklist(n, buckets[n], scratch_root, algo)
        wl_paths[n] = wl_path
        print(f"  wrote {wl_path} ({nlines} lines)")

    if args.dry_run:
        stamp = time.strftime("%Y%m%d_%H%M%S")
        wk = output_dir / "_provenance" / stamp / "worker" / "sweep_worker.sh"
        print(f"\n[DRY RUN] launch commands (not executed; launch id would be {stamp}):")
        for n, wl in wl_paths.items():
            print(f"  {PY} {RUN_COMMAND} {n} \"{worker_command(wk, wl, n, npar, episodes, stamp)}\" --no-tail")
        print("\n[DRY RUN] complete -- nothing launched.")
        return

    snap = write_provenance(Path(args.spec), spec, output_dir, checkpoint_groups, list(wl_paths), npar, episodes)
    launch_id = snap.name
    worker_sh = snap / "worker" / "sweep_worker.sh"
    print(f"provenance: {snap}  (launch id {launch_id})")
    (scratch_root / "_format").write_text(FORMAT + "\n")

    t0 = time.time()
    # Clear stale per-node markers from a PRIOR launch before launching -- without this,
    # poll_done() could see an old done_/exit_ immediately. Race-free: clear -> launch -> poll.
    mark_dir = scratch_root / "_run_markers"
    for n in wl_paths:
        for m in ("done", "exit", "alive", "started", "FAILED", "fail", "lines"):
            (mark_dir / f"{m}_{n}").unlink(missing_ok=True)
    print("\nLaunching...")
    for n, wl in wl_paths.items():
        launch_node(n, worker_sh, wl, npar, episodes, launch_id, dry_run=False)
    print("Waiting for nodes to finish...")
    st = poll_done(scratch_root, list(wl_paths.keys()))
    rc = 2 if any(v != "done" for v in st.values()) else 0
    if report_fails(scratch_root, list(wl_paths)):
        rc = rc or 4

    print("Collating...")
    rc_c = _collate_launch(output_dir, scratch_root, launch_id, list(wl_paths),
                           worklist_cells(checkpoint_groups), episodes)
    rc = rc or rc_c

    print("Plotting...")
    figs = plot(spec, output_dir)
    print(f"  wrote {len(figs)} figure(s)")

    elapsed = time.time() - t0
    print(f"\n=== done in {elapsed:.0f}s ===")
    for run in spec["runs"]:
        label = run["label"]
        d = output_dir / label
        n_csv_files = len(list(d.glob("*.csv"))) if d.is_dir() else 0
        n_figs = len(list(d.glob("FIG_*.png"))) if d.is_dir() else 0
        print(f"  {label}: {n_csv_files} CSV(s), {n_figs} figure(s)")
    if rc:
        raise SystemExit(rc)


if __name__ == "__main__":
    main()
