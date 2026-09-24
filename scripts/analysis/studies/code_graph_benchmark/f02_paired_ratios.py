#!/usr/bin/env python3
"""FIGURE 2 - each tool against plain Claude Code, task by task, on four cost measures.

QUESTION IT ANSWERS. Taking the six tasks as six matched comparisons, did Graft or Graphify
change how long an attempt took, how many tokens it read, or how many tool calls and turns it
needed? The pre-registered bar for "beneficial" at equal correctness was 25% less time or tokens,
i.e. a ratio at or below 0.75; the figure draws that bar.

HOW IT IS COMPUTED. For each task, the median of the tool group's three attempts divided by the
median of the plain group's three attempts; the point is the geometric mean of the six task
ratios (so 2x on one task and 0.5x on another average to 1). The whisker is a 95% bootstrap
interval: resample the three attempts inside every task-and-group cell with replacement, recompute
the point, 4000 times, take the 2.5th and 97.5th percentiles. All in _common.paired_ratios.

KNOWN WEAKNESS. Three attempts per cell is few, so the intervals are wide; the figure can rule out
a large effect, not a moderate one. Wall-clock also carries a machine-load confound (figure 1).
"""
import os

import matplotlib.pyplot as plt
import numpy as np

import _common as K
from _common import house

METRICS = [("wall_s", "time per attempt"), ("total_in", "input tokens read"),
           ("tool_calls", "tool calls"), ("turns", "turns")]


def main():
    house.apply()
    runs = K.load_runs()
    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    ax.axvspan(0.5, 0.75, color=house.BG_SOFT, zorder=0)
    ax.axvline(1.0, color=house.INK_2, lw=1.2, zorder=1)
    ax.axvline(0.75, color=house.RULE, lw=1.0, ls="--", zorder=1)
    ax.text(0.745, len(METRICS) - 0.35, "pre-registered bar:\n25% cheaper", ha="right", va="top",
            color=house.INK_2, fontsize=house.FS_LABEL)
    yt, yl = [], []
    for i, (key, name) in enumerate(METRICS):
        y0 = len(METRICS) - 1 - i
        yt.append(y0)
        yl.append(name)
        for arm, dy in (("G", 0.13), ("F", -0.13)):
            p, lo, hi, _ = K.paired_ratios(runs, key, arm)
            ax.plot([lo, hi], [y0 + dy] * 2, color=K.ARM_COLOUR[arm], lw=2.2, zorder=3)
            ax.scatter([p], [y0 + dy], s=42, color=K.ARM_COLOUR[arm], zorder=4,
                       label=K.ARM_NAME[arm] if i == 0 else None, edgecolors="none")
    ax.set_xscale("log")
    ticks = [0.5, 0.75, 1.0, 1.5, 2.0]
    ax.set_xticks(ticks)
    ax.set_xticklabels(["0.5x", "0.75x", "1x", "1.5x", "2x"])
    ax.minorticks_off()
    ax.set_xlim(0.5, 2.0)
    ax.set_yticks(yt)
    ax.set_yticklabels(yl)
    ax.set_ylim(-0.6, len(METRICS) - 0.3)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x")
    ax.set_xlabel("tool group / plain Claude Code (ratio, log scale; left of 1x = cheaper)")
    house.legend_below(ax, ncol=2)
    fig.subplots_adjust(left=0.22, bottom=0.24, top=0.97, right=0.97)
    house.save(fig, os.path.join(K.OUT, "f02_paired_ratios"))

    ex = K.excluded()
    K.data_statement("f02_paired_ratios", [
        {"what": "Attempts used", "used": len(runs), "total": len(runs) + len(ex),
         "note": "every graded attempt; each ratio pairs a tool group's 18 attempts with the plain "
                 "group's 18 on the same six tasks"},
        {"what": "Tasks paired", "used": len(K.TASKS), "total": len(K.TASKS),
         "note": "all six tasks that passed the validity and leak checks"},
    ])


if __name__ == "__main__":
    main()
