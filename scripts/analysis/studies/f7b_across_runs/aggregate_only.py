#!/usr/bin/env python3
"""aggregate_only.py - run only the aggregation + plotting stage of a dwell sweep whose node workers
have already finished, with a small worker pool.

Why: run_sweep.py has no aggregate-only mode, and fifteen concurrent run_sweep.py aggregations (each
with a pool of up to 32 processes) drove this container's load average past 350 on 2026-10-04. This
calls run_sweep.py's own functions unchanged (load_spec, build_groups, aggregate, plot), one spec at
a time, so the CSVs are byte-for-byte what run_sweep.py would have written.

    $P scripts/analysis/studies/f7b_across_runs/aggregate_only.py SPEC [SPEC ...] --workers 6
"""
import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts" / "eval" / "dwell_sweep"))
import run_sweep as RS  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("specs", nargs="+")
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    for sp in a.specs:
        t = time.time()
        spec = RS.load_spec(sp)
        out = RS.REPO_ROOT / spec["output_dir"]
        scratch = out / "_scratch"
        nodes = spec["nodes"]
        missing = [n for n in nodes if not (scratch / "_run_markers" / f"done_{n}").exists()]
        if missing:
            raise SystemExit(f"{sp}: node worker(s) {missing} have no done marker -- run run_sweep.py instead")
        _, cond_groups = RS.build_groups(spec, out, None)
        n = RS.aggregate(cond_groups, scratch, n_workers=a.workers)
        RS.plot(spec, out)
        print(f"{spec['name']}: wrote {n} CSV(s) in {time.time() - t:.0f}s", flush=True)


if __name__ == "__main__":
    main()
