#!/usr/bin/env python3
"""launch_collection.py -- finished-runs-only, idempotent launcher for a trajectory-collection spec.

Why this exists
---------------
`run_collection.py` collects every run a spec lists, and `checkpoints: [final]` takes whatever
checkpoint exists at that moment. A spec that lists runs still training therefore cannot be
launched as a whole. This wrapper reads the FULL spec (the study's run manifest), keeps only the
runs whose training log ends in "Training complete. Results saved to <run dir>", and launches them
as a BATCH: a derived spec with its own `name` (so its own scratch dir and completion markers) and
its own live-free nodes. Re-running it launches only runs not already claimed by an earlier batch,
so it is safe to call repeatedly (e.g. from `--watch`) while the remaining runs finish.

Nothing here changes what is collected: every scientific key of the derived spec is copied
verbatim from the full spec; only `name`, `nodes` and `runs` differ.

Node rules
----------
* A node is a candidate only if it is in `--nodes`, is not used by a still-running batch of this
  spec, and passes a live check over SSH: GPU 0 (the collector always lands on GPU 0 -- see
  scripts/eval/traj_collect/README.md) has < 1000 MiB used and no `collect_trajectories` process
  runs there.
* A batch takes EVERY finished, unclaimed run and every free node; the driver LPT-partitions the
  runs across those nodes (one run = one 200-block cell), so a node may collect several runs in
  sequence. A node counts as busy until its batch's `done_<node>` marker exists.

Recovery
--------
A batch that failed part-way is resumed by re-running its driver on the same derived spec (the
collector skips completed blocks): `run_collection.py <out_root>/_scratch/_batch_specs/<batch>.yaml`.

Usage
-----
    /home/vncuser/miniconda3/envs/grid_world_pain/bin/python \
      scripts/analysis/studies/level05_body_interactions/launch_collection.py \
      configs/trajectory_collection/level05_body_interactions.yaml \
      --logs-glob 'logs/20260927_053*.log' --nodes 106 107 108 [--dry-run] [--watch 600]

    `--logs PATH [PATH ...]` replaces `--logs-glob` (exactly one of the two) when the logs must be
    named one by one, e.g. the May replication (configs/trajectory_collection/continual_mayrep_probes.yaml).
"""
from __future__ import annotations

import argparse
import glob
import json
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[4]   # scripts/analysis/studies/<study> -> root
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

PY = "/home/vncuser/miniconda3/envs/grid_world_pain/bin/python"
DRIVER = PROJECT_ROOT / "scripts" / "eval" / "traj_collect" / "run_collection.py"
SSH_OPTS = ["-p", "1800", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5"]
DONE_RE = re.compile(r"Training complete\. Results saved to (\S+)")


def log_files(logs_glob: str | None = None, logs: list | None = None) -> list[Path]:
    """The training logs to read: EXACTLY one of a repo-relative glob or an explicit list.

    `--logs` names files one by one (the May replication, tooling plan File Changes §12): each
    must exist and be non-empty, otherwise ValueError, because a typo'd or empty log would
    silently make its run look "not finished" and the launcher would skip it forever.
    """
    if (logs_glob is None) == (logs is None):
        raise ValueError("give exactly one of --logs-glob or --logs")
    if logs_glob is not None:
        return [Path(f) for f in glob.glob(str(PROJECT_ROOT / logs_glob))]
    out = []
    for f in logs:
        p = Path(f) if Path(f).is_absolute() else PROJECT_ROOT / f
        if not p.is_file():
            raise ValueError(f"--logs: {f} does not exist")
        if p.stat().st_size == 0:
            raise ValueError(f"--logs: {f} is empty (0 bytes); it names no run")
        out.append(p)
    return out


def finished_runs(files: list[Path]) -> set[str]:
    """Run-dir basenames whose training log reports completion."""
    done = set()
    for f in files:
        with open(f, "rb") as fh:
            fh.seek(0, 2)
            fh.seek(max(0, fh.tell() - 4096))
            tail = fh.read().decode("utf-8", "replace")
        for m in DONE_RE.finditer(tail):
            done.add(Path(m.group(1)).name)
    return done


def node_is_free(node: str) -> tuple[bool, str]:
    cmd = ("nvidia-smi --query-gpu=index,memory.used --format=csv,noheader,nounits; "
           "echo ---; pgrep -af collect_trajectories | grep -v pgrep || true")
    try:
        r = subprocess.run(["ssh", *SSH_OPTS, f"vncuser@192.168.0.{node}", cmd],
                           capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        return False, "ssh timeout"
    if r.returncode != 0:
        return False, f"ssh rc={r.returncode}"
    gpu, _, procs = r.stdout.partition("---")
    for line in gpu.strip().splitlines():
        idx, used = [x.strip() for x in line.split(",")]
        if idx == "0" and int(used) >= 1000:
            return False, f"GPU0 {used} MiB used"
    if procs.strip():
        return False, "collect_trajectories already running"
    return True, "free"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec", type=Path)
    lg = ap.add_mutually_exclusive_group(required=True)
    lg.add_argument("--logs-glob",
                    help="training logs (repo-relative glob) whose tails name finished runs")
    lg.add_argument("--logs", nargs="+", metavar="PATH",
                    help="training logs named one by one (each must exist and be non-empty)")
    ap.add_argument("--nodes", nargs="+", required=True, help="nodes this launcher may use")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--watch", type=int, default=0,
                    help="re-check every N seconds until every spec run is claimed (0 = once)")
    a = ap.parse_args(argv)
    a.log_files = log_files(a.logs_glob, a.logs)     # --logs checked once, before any launch

    while True:
        pending = launch_once(a)
        if a.watch <= 0 or pending == 0 or a.dry_run:
            return 0
        time.sleep(a.watch)


def launch_once(a) -> int:
    """One pass. Returns the number of spec runs not yet claimed by any batch."""
    import importlib.util
    mod_spec = importlib.util.spec_from_file_location("run_collection", DRIVER)
    rc = importlib.util.module_from_spec(mod_spec)
    mod_spec.loader.exec_module(rc)
    spec = rc.load_spec(a.spec)                     # validates the full spec
    raw = yaml.safe_load(a.spec.read_text())
    out_root = PROJECT_ROOT / spec["out_root"]
    state_dir = out_root / "_scratch" / "_batch_specs"
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / f"{spec['name']}_batches.json"
    batches = json.loads(state_path.read_text()) if state_path.exists() else []

    claimed = {Path(r["path"]).name for b in batches for r in b["runs"]}
    busy = set()
    for b in batches:
        mark = out_root / "_scratch" / b["name"] / "_run_markers"
        busy |= {n for n in b["nodes"] if not (mark / f"done_{n}").exists()}

    fin = finished_runs(a.log_files if a.logs is not None else log_files(a.logs_glob))
    all_runs = raw["runs"]
    todo = [r for r in all_runs if Path(r["path"]).name in fin
            and Path(r["path"]).name not in claimed]
    unclaimed = [r for r in all_runs if Path(r["path"]).name not in claimed]
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{stamp}] spec runs={len(all_runs)} finished={len(fin & {Path(r['path']).name for r in all_runs})} "
          f"claimed={len(claimed)} to-launch={len(todo)} busy-nodes={sorted(busy)}", flush=True)
    if not todo:
        return len(unclaimed)

    free = []
    for n in [str(x) for x in a.nodes]:
        if n in busy:
            continue
        ok, why = node_is_free(n)
        print(f"  node {n}: {why}", flush=True)
        if ok:
            free.append(n)
    if not free:
        print("  no free node; waiting", flush=True)
        return len(unclaimed)

    take = todo
    nodes = free[:len(take)]
    k = len(batches) + 1
    bname = f"{spec['name']}_b{k:02d}"
    bspec = dict(raw)
    bspec.update(name=bname, nodes=[int(n) for n in nodes], runs=take)
    bpath = state_dir / f"{bname}.yaml"
    print(f"  batch {bname}: {len(take)} run(s) on nodes {nodes}", flush=True)
    for r in take:
        print(f"    {r.get('label', '')}  {r['path']}", flush=True)
    if a.dry_run:
        return len(unclaimed)

    bpath.write_text(f"# Derived from {a.spec} by launch_collection.py at {stamp}.\n"
                     + yaml.safe_dump(bspec, sort_keys=False))
    log = state_dir / f"{bname}.driver.log"
    with open(log, "w") as fh:
        p = subprocess.Popen([PY, str(DRIVER), str(bpath)], cwd=PROJECT_ROOT, stdout=fh,
                             stderr=subprocess.STDOUT, start_new_session=True)
    batches.append({"name": bname, "nodes": nodes, "runs": take, "launched_at": stamp,
                    "driver_pid": p.pid, "driver_log": str(log.relative_to(PROJECT_ROOT))})
    state_path.write_text(json.dumps(batches, indent=1))
    print(f"  driver pid {p.pid}, log {log}", flush=True)
    # The driver launches its nodes serially through run_command.py, which is not parallel-safe:
    # give it time to finish launching before any later batch could start its own launches.
    time.sleep(20 * len(nodes))
    return len(unclaimed) - len(take)


if __name__ == "__main__":
    sys.exit(main())
