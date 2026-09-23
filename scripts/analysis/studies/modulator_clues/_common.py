"""Shared data access for the integrated exploratory page on where the modulator matters.

WHAT THIS PAGE IS FOR. Not a verdict. The ordinary agent and the fully neuromodulated agent are
compared across three worlds (blind, Wave 1, Wave 2) and curriculum levels 02-06, using the same
analyses the project published for the Sensor Ladder and "What makes this agent hide?", to gather
clues about WHEN, HOW and WHY the modulated agent behaves the same, better or worse -- and so which
direction to explore next. Plan: docs/experiments/active/basic_levels_q2_default/
INTEGRATED_ANALYSIS_PLAN.md (Revision 2).

THREE RULES THIS MODULE ENFORCES, one per error made on this data on 2026-09-23:
  1. No final-checkpoint-only number where a spread exists: coarse store measures come with the
     spread across late checkpoints (`late()`), probe measures with the 20-checkpoint window.
  2. Every figure is tagged CAUSAL, OBSERVATIONAL or CONTROLLED-SCENE (`KIND`), and the page builder
     refuses an untagged one. "Causal" is reserved for episodes whose starting injury was assigned
     at random.
  3. Every spread is labelled for what it is: across checkpoints of ONE run, never between runs.
"""
import glob, json, os, sys
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts", "analysis", "style"))
import house                                          # noqa: E402
from figguards import (assert_min_text_px, assert_no_text_overlap,   # noqa: E402,F401
                       assert_ticks_dont_collide, legend_below, COLUMN_PX)

A = os.path.join(ROOT, "results/analysis")
INT = os.path.join(A, "basicq2_integrated")
FIG = os.path.join(ROOT, "docs/experiments/active/modulator_clues/figures")
ARMS = [("control", "ordinary agent", house.BLUE), ("modulated", "neuromodulated agent", house.ORANGE)]
GAP = house.INK                                   # the modulated-minus-ordinary difference

#: Columns of every world x level figure. The blind world has no curriculum levels, so it is ONE
#: detached column, never drawn as if it were a level.
COLUMNS = [("blind", None), ("w1", 2), ("w1", 3), ("w1", 4), ("w1", 5), ("w1", 6),
           ("w2", 4), ("w2", 5), ("w2", 6)]
WORLD_NAME = {"blind": "blind", "w1": "Wave 1", "w2": "Wave 2"}
#: Cells that exist but are not comparable at full length -- both agents are read at matched steps.
MATCHED = {("w1", 2): "58 %", ("w1", 3): "88 %"}
#: Cells with no data, and why. The page builder prints these rather than leaving blanks.
EMPTY = {("w2", 2): "still training", ("w2", 3): "still training"}

KIND = {"causal": "causal — starting injury assigned at random",
        "observational": "observational — the agent's own history, not assigned",
        "scene": "controlled test scene"}


def col_label(world, level):
    if world == "blind":
        return "blind"
    s = f"{WORLD_NAME[world]}\nlevel {level:02d}"
    return s + (f"\n(at {MATCHED[(world, level)]})" if (world, level) in MATCHED else "")


# ---------------------------------------------------------------------------- data sources
def ladder(world, level, arm):
    """Sensor-ladder aggregate (1M final-checkpoint store) for one cell, or None."""
    if world == "blind":
        p = os.path.join(A, "nmn_olf_gae_grid/ladderstyle",
                         f"{'t1none' if arm == 'control' else 't16quad_ALL'}.json")
    else:
        p = os.path.join(INT, "ladderstyle", f"{world}_lvl{level:02d}_{arm}.json")
    return json.load(open(p)) if os.path.exists(p) else None


def context_final(world, level, arm):
    """context_dependence JSON on the 1M final store (injury state), or None."""
    if world == "blind":
        p = os.path.join(A, "basicq2_w1/context_prev", f"prev_{arm}.json")
    elif world == "w1":
        p = os.path.join(A, "basicq2_w1/context", f"lvl{level:02d}_{arm}.json")
    else:
        p = os.path.join(A, "basicq2_w1/context_w2", f"lvl{level:02d}_{arm}.json")
    return json.load(open(p)) if os.path.exists(p) else None


def late(world, level, arm):
    """context_dependence JSONs at every late checkpoint of one cell, oldest first."""
    if world == "blind":
        return []
    grid = "basicq2" if world == "w1" else "bq2cover"
    fs = sorted(glob.glob(os.path.join(INT, "context_late", f"{grid}_lvl{level:02d}_{arm}_*.json")),
                key=lambda f: int(f.rsplit("_", 1)[1].split(".")[0]))
    return [json.load(open(f)) for f in fs]


def causal_metric(d, key):
    return d["randomised_early"]["metrics"][key]


def entry_change(d):
    return d["entry"]["b0"]["first_25|action|near"]["delta_b0"]


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
    """Tag a figure causal / observational / scene. The builder refuses an untagged figure."""
    assert kind in KIND, kind
    os.makedirs(FIG, exist_ok=True)
    open(os.path.join(FIG, f"{stem}.kind.txt"), "w").write(kind + "\n")


# ---------------------------------------------------------------- per-episode drives (Figures A5, E3)
TARGET = {"blind": 100.0, "w1": 100.0, "w2": 100.0}


def npz(world, lvl, arm):
    if world == "blind":
        p = os.path.join(A, "nmn_olf_gae_grid/ladderstyle",
                         f"{'t1none' if arm == 'control' else 't16quad_ALL'}_episodes.npz")
    else:
        p = os.path.join(INT, "ladderstyle", f"{world}_lvl{lvl:02d}_{arm}_episodes.npz")
    return np.load(p) if os.path.exists(p) else None


def spans(z, world):
    be, se = z["bush_early"].astype(float), z["steps_early"].astype(float)
    rate = lambda m: 100 * be[m].sum() / se[m].sum() if se[m].sum() > 5000 else np.nan
    inj = z["inj0"]; dev = z["nut0"] - TARGET[world]            # negative = below target
    inj_span = rate(inj >= 75) - rate(inj < 25)
    hunger = rate((dev <= -75) & (dev >= -100)) - rate((dev > -25) & (dev <= 0))
    over = rate((dev > 25) & (dev <= 100)) - rate((dev > -25) & (dev <= 0)) if world == "w2" else np.nan
    return inj_span, hunger, over


