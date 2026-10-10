#!/usr/bin/env python3
"""aggregate_only.py - run only the collation + plotting stage of a dwell sweep whose node workers
have already finished, with a small worker pool.

Why: fifteen concurrent run_sweep.py aggregations (each with a pool of up to 32 processes) drove
this container's load average past 350 on 2026-10-04. Since the on-node pipeline (plan
docs/develop/active/refactors/SWEEP_EPISODE_BUNDLES_AND_ON_NODE_MEASURES.md) the nodes score their
own cells, so the default here only merges the newest launch's rows tables (seconds, no pool).
`--from-bundles` is the recovery path: score every pending cell from its archive (or legacy
folder) on this host with `--workers` processes, as the old aggregation did. Both call
run_sweep.py's own functions, so the CSVs are byte-for-byte what run_sweep.py writes.

    $P scripts/analysis/studies/f7b_across_runs/aggregate_only.py SPEC [SPEC ...] [--launch ID]
    $P scripts/analysis/studies/f7b_across_runs/aggregate_only.py SPEC --from-bundles --workers 6
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
    ap.add_argument("--workers", type=int, default=6, help="process count for --from-bundles")
    ap.add_argument("--launch", default=None, help="launch id to collate (default: newest)")
    ap.add_argument("--from-bundles", action="store_true",
                    help="score every pending cell on disk instead of reading rows tables")
    a = ap.parse_args()
    rc = 0
    for sp in a.specs:
        t = time.time()
        spec = RS.load_spec(sp)
        out = RS.REPO_ROOT / spec["output_dir"]
        scratch = out / "_scratch"
        if a.from_bundles:
            nodes = [str(n) for n in spec["nodes"]]
            missing = [n for n in nodes if not (scratch / "_run_markers" / f"done_{n}").exists()]
            if missing:
                raise SystemExit(f"{sp}: node worker(s) {missing} have no done marker -- run run_sweep.py instead")
            _, cond_groups = RS.build_groups(spec, out, None)
            cid = "frombundles_" + time.strftime("%Y%m%d_%H%M%S")
            n = RS.with_collate_markers(
                scratch, cid, lambda: RS.aggregate_from_bundles(cond_groups, scratch, n_workers=a.workers))
            this_rc = 0
        else:
            known = dict(RS.launches(out))
            if not known:
                raise SystemExit(f"{sp}: no bundle-format launch under {out}/_provenance; use --from-bundles")
            cid = a.launch or sorted(known)[-1]
            prov = known[cid]
            nodes = [str(n) for n in prov["nodes"]]
            missing = [n for n in nodes if not (scratch / "_run_markers" / f"done_{n}").exists()]
            if missing:
                raise SystemExit(f"{sp}: launch {cid}: node worker(s) {missing} have no done marker -- "
                                 f"run run_sweep.py --status, or use --from-bundles")
            this_rc = RS._collate_launch(out, scratch, cid, nodes, prov["cells"], prov["episodes"])
            n = "see above"
        RS.plot(spec, out)
        print(f"{spec['name']}: wrote {n} CSV(s) in {time.time() - t:.0f}s", flush=True)
        rc = rc or this_rc
    if rc:
        raise SystemExit(rc)


if __name__ == "__main__":
    main()
