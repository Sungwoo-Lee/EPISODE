#!/usr/bin/env python
"""On-node finisher of the behaviour-test sweep: archive, then score, the cells of ONE worklist
line (one checkpoint, k scenes), right after eval_rollout.py wrote them to node-local staging.
Plan: docs/develop/active/refactors/SWEEP_EPISODE_BUNDLES_AND_ON_NODE_MEASURES.md (F3).

    finish_cells.py --repo-root R --pairs STAGE1=CELL1 [STAGE2=CELL2 ...] \\
        --rows-piece <_rows/<launch_id>/<node>/<line>.csv> --episodes N --log <finish_<node>.log>

STAGE is the node-local folder eval_rollout.py wrote (``/tmp/...``); CELL is the cell's place on
the shared disk, ``<scratch>/<run_label>/<cond>/<step>``. Per pair, in this order:

  1. pack STAGE into a local archive (episode_bundle.pack: ZIP_STORED, verified byte for byte);
  2. publish it to ``CELL.zip``: ONE sequential file copy to the NAS into a ``.partial-*`` name,
     fsync, drop this host's cache, re-read and compare sha256, then rename into place. The NAS
     sees one file per cell instead of ~64 small files and 5 directories;
  3. score: the CSV row from STAGE's recordings (cell_measures). STAGE is byte-identical to the
     published archive (checked in 1 and 2), so this equals scoring the archive, without
     re-reading it over the NAS. The archive exists before scoring starts (review M3): a scoring
     error leaves the archive and costs only the row.

Rows of the line go to ``--rows-piece`` (tmp + rename). Columns: run_label, cond, step, step_M,
<11 measures>, n_episodes, numpy_version, bundle. Exit status 1 if any cell failed or held a
number of episodes other than --episodes; the worker then keeps that line's staging for recovery.

``--repo-root`` is mandatory and has no default (plan-review N1): the driver launches a COPY of
this file from ``<output_dir>/_provenance/<launch_id>/worker/``, from where the repo cannot be
derived by path depth.
"""
import argparse
import csv
import hashlib
import os
import shutil
import socket
import sys
import time
import traceback
from pathlib import Path

ROWS_HEAD_PREFIX = ["run_label", "cond"]
ROWS_HEAD_SUFFIX = ["n_episodes", "numpy_version", "bundle"]


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def publish(local_zip, target, EB, log):
    """Copy `local_zip` to `target` atomically and verified. An existing target (a re-test of a
    cell whose group was not merged last time) is replaced; a differing one is logged."""
    target = Path(target)
    partial = target.with_name(f"{target.name}.partial-{socket.gethostname()}-{os.getpid()}")
    want = _sha256(local_zip)
    try:
        with open(local_zip, "rb") as src, open(partial, "wb") as dst:
            shutil.copyfileobj(src, dst, 1 << 20)
            dst.flush()
            os.fsync(dst.fileno())
        EB._drop_cache(partial)
        got = _sha256(partial)
        if got != want:
            raise EB.BundleMismatch(f"{partial}: sha256 after copy {got} != local {want}")
        if target.exists():
            old = _sha256(target)
            if old != want:
                log(f"REPLACED differing archive {target} (old sha256 {old[:12]}, new {want[:12]})")
        os.replace(partial, target)
    except BaseException:
        if partial.exists():
            partial.unlink()
        raise
    return want


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo-root", required=True, help="repository root (mandatory, no default)")
    ap.add_argument("--pairs", nargs="+", required=True, help="STAGE=CELL, one per scene")
    ap.add_argument("--rows-piece", required=True)
    ap.add_argument("--episodes", type=int, required=True)
    ap.add_argument("--log", required=True)
    a = ap.parse_args(argv)

    repo = Path(a.repo_root).resolve()
    if not (repo / "src" / "utils" / "episode_bundle.py").is_file():
        raise SystemExit(f"finish_cells.py: --repo-root {repo} does not hold src/utils/episode_bundle.py")
    here = Path(__file__).resolve().parent
    for p in (str(repo / "scripts" / "behavior_measures"), str(repo), str(here)):
        if p not in sys.path:
            sys.path.insert(0, p)
    import numpy as np
    import src.utils.episode_bundle as EB
    from cell_measures import measure_cell_n

    host = socket.gethostname()
    logf = open(a.log, "a")

    def log(msg):
        logf.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {host} pid={os.getpid()} {msg}\n")
        logf.flush()

    rows, failed = [], 0
    for pair in a.pairs:
        stage, _, cell = pair.partition("=")
        if not stage or not cell:
            raise SystemExit(f"finish_cells.py: bad --pairs entry {pair!r} (want STAGE=CELL)")
        stage, cell = Path(stage), Path(cell)
        step, cond, label = int(cell.name), cell.parent.name, cell.parent.parent.name
        scratch = cell.parent.parent.parent
        target = cell.with_name(cell.name + EB.BUNDLE_SUFFIX)
        local_zip = stage.with_name(stage.name + EB.BUNDLE_SUFFIX)
        try:
            t0 = time.time()
            if local_zip.exists():
                local_zip.unlink()
            man = EB.pack(stage, local_zip)
            t1 = time.time()
            target.parent.mkdir(parents=True, exist_ok=True)
            publish(local_zip, target, EB, log)
            t2 = time.time()
            res = measure_cell_n(stage, step)
            t3 = time.time()
            if res is None:
                raise RuntimeError(f"no recordings in {stage}")
            _step, row, n = res
            rows.append([label, cond] + row + [n, np.__version__, target.relative_to(scratch).as_posix()])
            ok = n == a.episodes
            failed += 0 if ok else 1
            log(f"{'OK' if ok else 'SHORT'} {label}/{cond}/{step} n={n} files={len(man)} "
                f"pack={t1 - t0:.2f}s publish={t2 - t1:.2f}s score={t3 - t2:.2f}s")
        except Exception:
            failed += 1
            log(f"FAIL {label}/{cond}/{step} stage={stage}\n{traceback.format_exc()}")

    piece = Path(a.rows_piece)
    piece.parent.mkdir(parents=True, exist_ok=True)
    tmp = piece.with_name(piece.name + f".tmp-{host}-{os.getpid()}")
    from cell_measures import HEAD
    with open(tmp, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(ROWS_HEAD_PREFIX + HEAD + ROWS_HEAD_SUFFIX)
        w.writerows(rows)
    os.replace(tmp, piece)
    logf.close()
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
