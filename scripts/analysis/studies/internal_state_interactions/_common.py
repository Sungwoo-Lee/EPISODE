"""Shared paths and helpers for the 'interactions between internal states' page figures."""
import glob, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts", "analysis", "style"))
import house                                                          # noqa: E402
from figguards import (assert_min_text_px, assert_no_text_overlap,   # noqa: E402,F401
                       assert_ticks_dont_collide, legend_below, COLUMN_PX)

OUT = os.path.join(ROOT, "results/analysis/internal_state_interactions")
SWEEP = os.path.join(OUT, "sweep_food4")   # food trip 4 (measured, predators excluded); "sweep" used 2
FIG = os.path.join(ROOT, "docs/experiments/active/internal_state_interactions/figures")

KIND = {"simulation": "simulation — body rules only, no trained agent",
        "planner": "ideal planner — the best choices under the body rules, not a trained agent",
        "validation": "check — simulator against the real environment"}

# one colour per choice category (planner.CATEGORIES), shared by every figure
CHOICE_COLOURS = {"rest in cover": house.BLUE, "warm up": house.ORANGE, "eat": house.GREEN,
                  "stay in the open": "#b8bcc4"}
CHOICE_ORDER = ["rest in cover", "warm up", "eat", "stay in the open"]


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


def sweep_results():
    """All sweep JSONs, keyed by world name."""
    return {json.load(open(p))["name"]: json.load(open(p)) for p in sorted(glob.glob(os.path.join(SWEEP, "*.json")))}
