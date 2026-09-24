#!/usr/bin/env python3
"""FIGURE 1 - wall-clock time of every attempt, by task and group.

QUESTION IT ANSWERS. Did either code-graph tool make Claude Code finish the same task faster?
The pooled median says Graft was 36% faster; this figure shows why that number should not be
trusted: the differences are task-specific and point both ways (Graft much faster on T3, much
slower on T2), and within a task the three attempts of one group often spread wider than the gap
between groups.

HOW IT IS COMPUTED. One dot per graded attempt (6 tasks x 3 groups x 3 attempts = 54), placed at
the attempt's wall-clock time in minutes: from launching the sandboxed Claude Code session to its
final message, which includes the agent running tests. A short vertical bar marks the median of
each group's three attempts on that task. Grading time is not included.

KNOWN WEAKNESS. Runs shared the machine with 4-7 others at different times, and the Graft runs of
T1, T6 and T7 ran last, so wall-clock carries a machine-load confound that tokens do not.
"""
import os
import statistics

import matplotlib.pyplot as plt

import _common as K
from _common import house


def main():
    house.apply()
    runs = K.load_runs()
    fig, ax = plt.subplots(figsize=(8.2, 5.6))
    offsets = {"A": 0.24, "G": 0.0, "F": -0.24}
    yt, yl = [], []
    for i, t in enumerate(K.TASKS):
        y0 = len(K.TASKS) - 1 - i
        yt.append(y0)
        yl.append(f"{t}  {K.TASK_NAME[t]}")
        for a in K.ARMS:
            xs = [v / 60 for v in K.cell(runs, t, a, "wall_s")]
            y = y0 + offsets[a]
            ax.scatter(xs, [y] * 3, s=26, color=K.ARM_COLOUR[a], alpha=0.85, zorder=3,
                       label=K.ARM_NAME[a] if i == 0 else None, edgecolors="none")
            m = statistics.median(xs)
            ax.plot([m, m], [y - 0.09, y + 0.09], color=K.ARM_COLOUR[a], lw=2.4, zorder=4)
    ax.set_yticks(yt)
    ax.set_yticklabels(yl)
    ax.set_ylim(-0.6, len(K.TASKS) - 0.4)
    ax.set_xlim(0, 16)
    ax.set_xticks([0, 4, 8, 12, 16])
    ax.grid(axis="x")
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("wall-clock time of one attempt (minutes)")
    house.legend_below(ax, ncol=3)
    fig.subplots_adjust(left=0.36, bottom=0.2, top=0.97, right=0.97)
    house.save(fig, os.path.join(K.OUT, "f01_time_per_task"))

    ex = K.excluded()
    n_smoke = sum("smoke" in e["reason"] for e in ex)
    K.data_statement("f01_time_per_task", [
        {"what": "Attempts plotted", "used": len(runs), "total": len(runs) + len(ex),
         "note": f"every graded attempt; the {len(ex)} left out are {n_smoke} pipeline smoke tests and "
                 f"{len(ex) - n_smoke} attempts made with two task descriptions that were later corrected"},
    ])


if __name__ == "__main__":
    main()
