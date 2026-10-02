"""Per-block counts behind measure 1 (true injury), so Figure 1 can carry intervals.

WHY THIS EXISTS. state_contrasts.py sums every store into one set of cell counts, so it leaves no
way to say how much a per-world value would move on a different million evaluation episodes. Each
store is written in 200 blocks of 5,000 whole episodes; episodes are independent, so resampling
BLOCKS (not steps, which are strongly correlated within an episode) gives an honest interval for
evaluation-episode noise. It says nothing about seed-to-seed noise (one seed per world).

Counts are taken exactly as state_contrasts.py takes them: DECISION rows only
(_common.read_decision_rows), nutrition band hungry = [0, 60), fed = [100, inf) (half-open), true
injury low = [0, 20], high = [60, 100] (inclusive), bush = agent_in_bush at row t. The band and range
edges are read from the analysis manifest, never restated here. The block sums are checked against
state_contrasts.json cell by cell; any mismatch stops the script.

Output: results/analysis/level05_body_interactions/page/shard_cells.json
   {label: {"store":..., "cells": {"fed|low": [[n, k], ... one per block], ...}}}
Usage:  $PY scripts/analysis/studies/level05_body_interactions/page/shard_cells.py [--workers 12]
"""
import argparse, json, os, sys
from functools import partial
from pathlib import Path

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))               # the study's own _common (store reading)
import _common as SC                                     # noqa: E402  (study helpers, not the page's)

MANIFEST = SC.ROOT / "docs/experiments/active/level05_body_interactions/analysis_manifest.yaml"
BANDS, RANGES = ("hungry", "fed"), ("low", "high")


def _in(x, lo, hi, inclusive_hi):
    return (x >= lo) & ((x <= hi) if inclusive_hi else (x < hi))


def _block(shard, bands, ranges):
    r = SC.read_decision_rows(Path(shard), ["nutrition", "injury_level", "agent_in_bush"], None, None)
    nut, inj = r["nutrition"].astype(np.float64), r["injury_level"].astype(np.float64)
    bush = r["agent_in_bush"].astype(bool)
    out = {}
    for b in BANDS:
        bm = _in(nut, bands[b][0], bands[b][1], False)
        for g in RANGES:
            m = bm & _in(inj, ranges[g][0], ranges[g][1], True)
            out[f"{b}|{g}"] = [int(m.sum()), int((m & bush).sum())]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=12)
    a = ap.parse_args()
    man = SC.load_manifest(MANIFEST)
    sc = json.load(open(SC.ROOT / "results/analysis/level05_body_interactions/state_contrasts.json"))
    out_p = SC.ROOT / "results/analysis/level05_body_interactions/page/shard_cells.json"
    res = json.load(open(out_p)) if out_p.exists() else {}
    for label, run in sorted(sc["runs"].items()):
        store = SC.ROOT / run["final"]["store"]
        if label in res and res[label]["store"] == run["final"]["store"]:
            continue
        fs = [str(s) for s in SC.shard_files(store)]
        parts = SC.parallel_map(partial(_block, bands=man["nutrition_bands"], ranges=man["injury_ranges"]),
                                fs, a.workers)
        cells = {k: [p[k] for p in parts] for k in parts[0]}
        for k, v in cells.items():                       # must equal the pre-registered analysis
            n, kk = np.sum(v, axis=0)
            ref = run["final"]["true"]["cells"][k]
            if n != ref["n"] or abs(kk / n - ref["B"]) > 1e-12:
                raise SystemExit(f"{label} {k}: block sums n={n} B={kk/n} differ from "
                                 f"state_contrasts.json n={ref['n']} B={ref['B']}")
        res[label] = {"store": run["final"]["store"], "blocks": len(fs), "cells": cells}
        SC.write_json(out_p, res)
        print(f"  {label}: {len(fs)} blocks, sums match state_contrasts.json", flush=True)
    print(f"wrote {out_p.relative_to(SC.ROOT)} ({len(res)} runs)")


if __name__ == "__main__":
    main()
