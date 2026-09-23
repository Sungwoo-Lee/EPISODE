"""Shared data access for the thermal-probe figures.

Every figure here reads the checkpoint-history CSVs the dwell sweep wrote -- one row per saved
checkpoint, one file per (run, probe condition) -- and never the final checkpoint alone. The
reason is measured rather than stylistic: checkpoint-to-checkpoint policy variation (sd 10-27
percentage points) is four to ten times the 30-episode sampling error (SE 2.3-2.6 pp), so an
endpoint reading is one draw from a wide distribution. Reading the endpoint once produced a
60-point level-04 "result" that was 0.8 points once ten checkpoints were averaged.
"""
import os
import sys

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts", "analysis", "studies", "basicq2_waves"))
sys.path.insert(0, os.path.join(ROOT, "scripts", "analysis", "style"))

import window_profile as W          # noqa: E402
import house                        # noqa: E402

EVAL = os.path.join(ROOT, "results/eval/avoidance")
LVL04 = os.path.join(EVAL, "metrics_history_rppo_basicq2_wave2_blocking_bush")
FIG = os.path.join(ROOT, "docs/experiments/active/behavior_measures/figures")

#: The four thermal arms, ordered as the design states them: the two worlds made comfortable by
#: warming the whole world, then the two that keep the trained cold and add a fire.
ARMS = [("neutral_clean",      "neutral\n(whole world at the set point)"),
        ("cool_clean",         "cool\n(body settles 5 below)"),
        ("fire_by_bush_clean", "fire beside the bush\n(hiding is warm)"),
        ("fire_away_clean",    "fire away from the bush\n(hiding is cold)")]
LEVELS = ["lvl05", "lvl06"]
ARMC = {"control": house.BLUE, "modulated": house.ORANGE}

PRED, NONE = "avoid_pred_inj00", "avoid_none_inj00"


def arm_dir(arm):
    return os.path.join(EVAL, f"metrics_history_rppo_thermalprobe_{arm}")


def contrast(out_dir, run):
    """Per-checkpoint conditional-hiding contrast: hiding(predator) - hiding(no animal), in pp.

    Positive means the agent hides MORE when a predator is in the world -- threat-conditional
    hiding. The two conditions are separate episode sets, so their sampling noise is independent
    and adds; pairing them by checkpoint does NOT cancel policy drift (measured: sd of the
    difference 20.5 against a mean level sd of 19.2), which is why the level series are reported
    beside the contrast rather than replaced by it.
    """
    _, p = W.read_series(out_dir, run, PRED)
    _, n = W.read_series(out_dir, run, NONE)
    if p is None or n is None:
        return None
    return p - n


def record_samples(stem, rows):
    """Emit `<stem>.data.txt`: used / available / percent per subset, with a reason.

    Written BY THE SCRIPT, never typed into the page by hand -- artifact guide section 11b.
    """
    os.makedirs(FIG, exist_ok=True)
    with open(os.path.join(FIG, f"{stem}.data.txt"), "w") as fh:
        for r in rows:
            pct = 100.0 * r["used"] / r["total"] if r["total"] else 0.0
            fh.write(f"{r['what']}|{r['used']}|{r['total']}|{pct:.1f}|{r['note']}\n")
    print(f"  wrote {stem}.data.txt ({len(rows)} rows)")


#: The page's real text column: 70ch of Pretendard at 16.5px measures 688px, not the 730px
#: `house.check_floor` assumes by default. Every figure here passes this explicitly.
COLUMN_PX = 688

#: Display names for run keys. The first build put "L05 cont" and "L06 modu" on an axis -- tokens
#: that appear nowhere in the page's prose, which calls them "plain agent" and "neuromodulated
#: agent" at level 05 and 06 (format register F57).
KIND_NAME = {"control": "plain", "modulated": "neuromodulated"}
LEVEL_NAME = {"lvl05": "level 05", "lvl06": "level 06"}
COND_NAME = {"avoid_pred_inj00": "predator", "avoid_none_inj00": "empty world"}


def assert_min_text_px(fig, column_px=COLUMN_PX, floor_px=9.0):
    """Assert the figure's SMALLEST DRAWN TEXT clears the legibility floor at the real column.

    `house.check_floor` computes one number from the house constant FS_LABEL at a default column of
    730px. That is not the same question: an annotation set at 8.5pt is not FS_LABEL, and this page's
    column is 688px. On the first build of this page that gap let annotations ship at 6.8px and tick
    labels at 6.1px under a build line that read "smallest label 9.3px" -- the check ran, printed a
    passing number, and measured something no reader ever sees. So this walks every visible Text
    artist and takes the true minimum. Proposed for the format register as F63.
    """
    import matplotlib.text
    w_px = fig.get_size_inches()[0] * fig.dpi
    smallest, who = None, None
    for t in fig.findobj(matplotlib.text.Text):
        if not t.get_visible() or not (t.get_text() or "").strip():
            continue
        pt = t.get_fontsize()
        if smallest is None or pt < smallest:
            smallest, who = pt, (t.get_text() or "")[:40].replace("\n", " ")
    px = smallest * (fig.dpi / 72.0) * (column_px / w_px)
    if px < floor_px:
        raise SystemExit(
            f"smallest DRAWN text renders at {px:.1f}px in a {column_px}px column "
            f"(floor {floor_px}px): {smallest:g}pt on {who!r}. Raise the size or narrow the canvas; "
            f"do not lower the floor.")
    return px


def assert_ticks_dont_collide(ax, axis="x"):
    """Assert an axis's tick labels do not overprint one another.

    `house.assert_labels_fit` guards the axis label and title; `assert_text_inside_axes` guards
    hand-placed text. Neither looks at tick labels, so long categorical names silently run into each
    other -- which is what happened to the arm names on the results figure. Proposed as a second
    amendment to register F18.
    """
    fig = ax.get_figure()
    fig.canvas.draw()
    labs = ax.get_xticklabels() if axis == "x" else ax.get_yticklabels()
    boxes = [(l, l.get_window_extent()) for l in labs if (l.get_text() or "").strip()]
    for i in range(len(boxes) - 1):
        (la, a), (lb, b) = boxes[i], boxes[i + 1]
        if a.x1 > b.x0 + 0.5 if axis == "x" else a.y1 > b.y0 + 0.5:
            raise SystemExit(
                f"{axis}-tick labels overlap: {la.get_text()!r} runs into {lb.get_text()!r}. "
                f"Wrap or rotate them.")
