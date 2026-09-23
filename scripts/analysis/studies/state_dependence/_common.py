"""Shared data access for the state-dependence ladder figures.

WHICH PANEL. `context_dependence.py` reports every measure twice. The OBSERVED panel uses whatever
injury the agent happened to be carrying; the CAUSAL panel (`randomised_early`) uses only episodes
whose STARTING injury was assigned at random, so it cannot have been produced by the agent's own
behaviour. Everything here reads the CAUSAL panel, because the observed one is confounded by
reverse causation: an agent at high injury mid-episode was just bitten in a predator encounter, and
the encounter is what put it in the bush. That confound is not a subtlety -- read on the observed
panel the headline measure is flat at ~21 points across six wildly different agents, and the flatness
is a property of the environment rather than of any policy.
"""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts", "analysis", "style"))
import house                                     # noqa: E402
from figguards import (assert_min_text_px,       # noqa: E402,F401
                       assert_no_text_overlap, assert_ticks_dont_collide,
                       legend_below, COLUMN_PX)

A = os.path.join(ROOT, "results/analysis/basicq2_w1")
FIG = os.path.join(ROOT, "docs/experiments/active/state_dependence/figures")
ARMC = {"control": house.BLUE, "modulated": house.ORANGE}
NEAR = "first_25|action|near"

#: The three rungs, in the order the world changed. Each is (label, directory, cell-name pattern).
RUNGS = [("blind\n(no vision at all)",        f"{A}/context_prev",      "prev_{arm}"),
         ("sighted\n(vision switched on)",    f"{A}/context",           "lvl04_{arm}"),
         ("cover heals\n(bush is the only\nplace healing works)", f"{A}/context_w2", "lvl04_{arm}")]


def cell(directory, pattern, arm):
    p = os.path.join(directory, pattern.format(arm=arm) + ".json")
    return json.load(open(p)) if os.path.exists(p) else None


def causal(d):
    """(state span, proximity-effect trend) from the causal panel, in percentage points."""
    m = d["randomised_early"]["metrics"]
    return m["state_span"], m["proximity_effect_trend_per_bin"]


def delta_b0(d, key=NEAR):
    """Change in bush-ENTRY rate from the lowest to the highest injury bin, predator near."""
    e = d["entry"]["b0"][key]
    return e["delta_b0"], e["delta_b0_ci95"]


def seed_scale():
    """Run-to-run spread of each measure, from five seeds of one unmodulated agent.

    This is the denominator every arm comparison needs. The within-run confidence intervals the
    tool prints are +-0.05 to +-0.07 pp, which makes EVERY difference "significant" including ones
    that flip sign between worlds -- they describe sampling inside one run, not how much two runs
    of the same configuration disagree.
    """
    import glob
    import numpy as np
    out = {}
    for est in ("gaenorm", "mc"):
        rows = []
        for f in sorted(glob.glob(f"{A}/context_seedscale/seed_{est}_s*.json")):
            d = json.load(open(f))
            f1, f2 = causal(d)
            rows.append((f1, f2, delta_b0(d)[0]))
        a = np.asarray(rows, float)
        a = a[~np.isnan(a).any(1)]
        out[est] = dict(n=len(a), f1=a[:, 0].std(ddof=1), f2=a[:, 1].std(ddof=1),
                        b0=a[:, 2].std(ddof=1))
    return out


def record_samples(stem, rows):
    os.makedirs(FIG, exist_ok=True)
    with open(os.path.join(FIG, f"{stem}.data.txt"), "w") as fh:
        for r in rows:
            pct = 100.0 * r["used"] / r["total"] if r["total"] else 0.0
            u = f"{r['used']:,}" if isinstance(r["used"], int) else r["used"]
            t = f"{r['total']:,}" if isinstance(r["total"], int) else r["total"]
            fh.write(f"{r['what']}|{u}|{t}|{pct:.1f}|{r['note']}\n")
    print(f"  wrote {stem}.data.txt ({len(rows)} rows)")
