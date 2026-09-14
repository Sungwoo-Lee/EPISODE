#!/usr/bin/env python3
"""run_hiding_drivers.py - the hiding-drivers GLM, asked of every cell of a neuromodulator grid.

`scripts/analysis/hiding_drivers.py` is genuinely run-agnostic: it derives the entity/resource slot
layout from the run's own saved config and takes `--run`, `--store-root`, `--out`. What it does NOT
have is a driver. The fourteen per-arm outputs under `results/analysis/lad/<arm>/` that the ladder's
figures 6 and 7 read were produced by a loop nobody wrote down, so the invocation had to be
reconstructed from scratch every time somebody needed another cohort. This is that loop.

THE CACHE IS THE TRAP, and it is why this file exists rather than a shell one-liner.
`hiding_drivers.main()` skips the aggregation stage entirely when the cache file already exists:

    if a.stage in ("aggregate", "all") and not os.path.exists(cache):

so a second run against a stale cache silently re-fits the GLM on the PREVIOUS population and
verifies nothing at all about the scan. A driver that loops without thinking about this turns one
stale file into a whole grid of numbers that look fresh. This one refuses to start on a cell whose
cache already exists unless `--reuse-cache` says so out loud.

USAGE
    python scripts/analysis/studies/nmn_site_grid/run_hiding_drivers.py --grid olfmc
    python scripts/analysis/studies/nmn_site_grid/run_hiding_drivers.py --grid olfgae --dry-run
    python .../run_hiding_drivers.py --grid nmnsite --cells t1none t3rnn_I --reuse-cache
"""
from __future__ import annotations
import argparse, os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))   # scripts/<a>/<b>/<c>.py
os.chdir(ROOT)
sys.path.insert(0, HERE)
from make_manifest import GRIDS, build                                # noqa: E402

PY = sys.executable
DRIVER = "scripts/analysis/hiding_drivers.py"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--grid", choices=sorted(GRIDS), required=True)
    ap.add_argument("--cells", nargs="*", default=None, help="subset; default every cell the "
                                                             "manifest resolves to a store")
    ap.add_argument("--out", default=None, help="default results/analysis/<grid>/glm")
    ap.add_argument("--reuse-cache", action="store_true",
                    help="permit a cell whose aggregate.npz already exists. Without this the run "
                         "stops, because hiding_drivers skips the scan when a cache is present and "
                         "would re-fit the old population while looking fresh.")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    man = build(a.grid)
    cells = a.cells or sorted(man)
    unknown = [c for c in cells if c not in man]
    if unknown:
        sys.exit(f"not in the {a.grid} manifest (no collected store?): {unknown}")
    out_root = a.out or f"results/analysis/{a.grid}/glm"

    stale = [c for c in cells if os.path.exists(f"{out_root}/{c}/aggregate.npz")]
    if stale and not a.reuse_cache:
        sys.exit(f"{len(stale)} cell(s) already hold an aggregate.npz: {stale[:5]}"
                 f"{'...' if len(stale) > 5 else ''}\n"
                 f"hiding_drivers would skip the scan and re-fit that cached population. Delete "
                 f"them, point --out elsewhere, or pass --reuse-cache if that is what you mean.")

    print(f"grid={a.grid}  cells={len(cells)}  store roots={GRIDS[a.grid]}  out={out_root}")
    failed = []
    for i, c in enumerate(cells, 1):
        out = f"{out_root}/{c}"
        cmd = [PY, DRIVER, "--run", man[c]["run"], "--store-root", *GRIDS[a.grid],
               "--out", out, "--cache", f"{out}/aggregate.npz"]
        print(f"\n[{i}/{len(cells)}] {c}\n  {' '.join(cmd)}", flush=True)
        if a.dry_run:
            continue
        os.makedirs(out, exist_ok=True)
        t0 = time.time()
        r = subprocess.run(cmd)
        if r.returncode:
            failed.append(c)
            print(f"  FAILED (exit {r.returncode}) after {time.time()-t0:.0f}s", flush=True)
        else:
            print(f"  ok ({time.time()-t0:.0f}s)", flush=True)

    if failed:
        print(f"\n{len(failed)} cell(s) failed: {failed}")
        return 1
    print(f"\n{len(cells)} cell(s) written under {out_root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
