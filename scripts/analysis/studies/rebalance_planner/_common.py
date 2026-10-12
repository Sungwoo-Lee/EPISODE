"""Shared paths and helpers for the rebalance-planner figures (same conventions as the
internal-state-interactions study's _common.py: house style, data accounting, figure kind)."""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts", "analysis", "style"))
import house                                                          # noqa: E402
from figguards import (assert_min_text_px, assert_no_text_overlap,   # noqa: E402,F401
                       assert_ticks_dont_collide, COLUMN_PX)

FIG = os.path.join(ROOT, "docs/experiments/active/rebalance_planner/figures")
KIND = {"planner": "ideal planner — the best choices under the body rules, not a trained agent",
        "recordings": "recordings — trained agents' own episodes",
        "check": "check — simulator against the real environment"}
DECISION_COLOURS = {"hide": house.BLUE, "forage": house.GREEN, "other": "#b8bcc4"}
DECISION_LABEL = {"hide": "hide in a bush", "forage": "go out to eat", "other": "other (warm up / stay in the open)"}
ORDER = ["level05", "w1", "w2", "w3", "w4", "w5", "w6", "w7", "w8"]


def world_label(tag, r):
    if tag == "level05":
        return "level 05 (reference)"
    k = tag[1]
    return f"world {k}  {' '.join(r['signs'])}"


def results():
    return json.load(open(os.path.join(FIG, "results.json")))


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
    open(os.path.join(FIG, f"{stem}.kind.txt"), "w").write(kind + "\n")

# One meaning per colour across the WHOLE page (F11): decisions blue / green / grey; warming orange only;
# death sources below. Death categories that are zero everywhere are dropped from a figure, not coloured.
DEATH_COLOURS = {"survived": "#d9dcd8", "predator": house.RED, "trap": "#c96f8f", "rock": "#e9bccb",
                 "starvation": "#6b4fa3", "over-eating": "#3f6e6e", "cold": "#24324a", "injury": "#6e2323"}
DEATH_LABEL = {"survived": "survived 500 steps", "predator": "predator", "trap": "trap (hidden predator)",
               "rock": "rock", "starvation": "starvation", "over-eating": "over-eating", "cold": "cold",
               "injury": "injury (any source)"}
TIME_COLOURS = {"bush": house.BLUE, "travel": "#e6e1d3", "eat": house.GREEN, "warm": house.ORANGE, "open": "#b8bcc4"}
# predator pounce reach: line style + shade, no markers (marker shapes are reserved for hide / eat / other)
POUNCE_STYLE = {2: dict(color="#7f8792", ls="--"), 3: dict(color=house.INK, ls="-")}


def finish(fig, stem, kind, samples):
    """Guards, data accounting, kind tag, save (house.save refuses sub-9px text and edge ink)."""
    import matplotlib.pyplot as plt
    assert_no_text_overlap(fig); assert_min_text_px(fig)
    record_kind(stem, kind); record_samples(stem, samples)
    house.save(fig, os.path.join(FIG, stem), column_px=COLUMN_PX)
    plt.close(fig)
