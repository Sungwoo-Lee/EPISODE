"""Shared paths and helpers for the thirst/water design page (docs/develop/active/thirst/).

Every figure script records how much data it used (<stem>.data.txt) and what kind of evidence it is
(<stem>.kind.txt); build_page.py embeds both and refuses to build without them (guide 11b).
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts", "analysis", "style"))
sys.path.insert(0, os.path.join(ROOT, "scripts", "analysis", "studies", "internal_state_interactions"))
import house                                                          # noqa: E402
from figguards import (assert_min_text_px, assert_no_text_overlap,   # noqa: E402,F401
                       assert_ticks_dont_collide, legend_below, COLUMN_PX)

OUT = os.path.join(ROOT, "results/analysis/thirst_water")
FIG = os.path.join(ROOT, "docs/develop/active/thirst/figures")

KIND = {"calculation": "calculation — exact arithmetic from the planned rules, no simulation",
        "simulation": "simulation — planned rules with a scripted agent, no trained agent, no predators",
        "mockup": "mock-up — the episode dashboard drawing a real level-05 frame with a hand-built pond and hydration"}

# One colour per activity / cause, shared by every figure.
ACT_COLOURS = {"walking to water": house.BLUE, "drinking": "#7fb2e5",
               "walking to food": house.GREEN, "eating": "#9fd19a",
               "walking to a fire": house.ORANGE, "at the fire ring": "#f5c28a"}
CAUSE_ORDER = ["survived 500", "thirst", "over-drinking", "starvation", "over-eating", "cold", "heat"]
CAUSE_COLOURS = {"survived 500": "#b8bcc4", "thirst": house.BLUE, "over-drinking": "#7fb2e5",
                 "starvation": house.GREEN, "over-eating": "#9fd19a", "cold": "#5b6bbf", "heat": house.ORANGE}


def record_samples(stem, rows):
    os.makedirs(FIG, exist_ok=True)
    with open(os.path.join(FIG, f"{stem}.data.txt"), "w") as fh:
        for r in rows:
            pct = 100.0 * r["used"] / r["total"] if r["total"] else 0.0
            u = f"{r['used']:,}" if isinstance(r["used"], int) else r["used"]
            t = f"{r['total']:,}" if isinstance(r["total"], int) else r["total"]
            fh.write(f"{r['what']}|{u}|{t}|{pct:.1f}|{r['note']}\n")
    print(f"  wrote {stem}.data.txt ({len(rows)} rows)")


def record_kind(stem, kind):
    assert kind in KIND, kind
    os.makedirs(FIG, exist_ok=True)
    open(os.path.join(FIG, f"{stem}.kind.txt"), "w").write(kind + "\n")
