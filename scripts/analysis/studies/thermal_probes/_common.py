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
