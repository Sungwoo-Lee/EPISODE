"""FIGURE 3 - The level 05 / 06 result: threat-conditional hiding in all four thermal worlds.

WHAT IS PLOTTED. For each of the four thermal arms and each of the two hardest curriculum levels,
the conditional hiding contrast of the plain and the neuromodulated agent: the share of steps on
the hiding bush with a predator present, minus the share with an empty world. Every estimate is
the mean over the last twenty saved checkpoints, with a 95% interval on the effective sample size.
Zero means the agent hides just as much whether or not anything is hunting it.

THE TWO READINGS. First, every bar is far above zero: in every world both agents hide substantially
more when a predator is there. Threat-conditional hiding is not in doubt. Second, the plain and the
neuromodulated agent are not separated by it -- the pairs overlap nearly everywhere, the gaps run in
both directions between arms, and with ten arm-by-level cells tested about one nominal hit is
expected by chance.

WHY FOUR WORLDS. Making these levels survivable at all requires changing their temperature, and no
setting is the world the agents trained in. Running four settings measures how much that choice
moves the answer instead of assuming it does not: the contrast is roughly twice as large in the
neutral world as in the one where the fire sits beside the bush.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
import _common as C, window_profile as W, house
house.apply()
WIN = 20

rows = []
for arm, arm_lab in C.ARMS:
    d = C.arm_dir(arm)
    for lvl in C.LEVELS:
        cell = {}
        for kind in ("control", "modulated"):
            s = C.contrast(d, f"{lvl}_{kind}")
            if s is None:
                cell = None; break
            pr = W.window_profile(s); r = pr[pr.window == WIN]
            if r.empty: cell = None; break
            cell[kind] = r.iloc[0]
        if cell: rows.append((arm_lab, lvl, cell))

fig, ax = plt.subplots(figsize=(10.0, 5.6))
x = np.arange(len(rows)); w = 0.36
for k, (kind, lab) in enumerate((("control", "plain agent"), ("modulated", "neuromodulated agent"))):
    m = [r[2][kind]["mean"] for r in rows]
    lo = [r[2][kind]["mean"] - r[2][kind]["lo"] for r in rows]
    hi = [r[2][kind]["hi"] - r[2][kind]["mean"] for r in rows]
    ax.bar(x + (k - 0.5) * w, m, width=w, color=C.ARMC[kind], label=lab, edgecolor="none")
    ax.errorbar(x + (k - 0.5) * w, m, yerr=[lo, hi], fmt="none",
                ecolor=house.INK, elinewidth=1.3, capsize=3.4)
ax.axhline(0, color=house.INK, lw=1)
ax.set_xticks(x)
# The arm name went on ONE line in the first build, so "fire beside the bush" and "fire away from
# the bush" ran into their neighbours and rendered as one smear (register F18, second amendment).
# Names are wrapped to short lines and the level goes underneath; the collision is then ASSERTED
# rather than eyeballed, because neither house guard looks at tick labels.
SHORT = {"neutral": "neutral", "cool": "cool",
         "fire beside the bush": "fire beside\nthe bush",
         "fire away from the bush": "fire away\nfrom the bush"}
ax.set_xticklabels([f"{SHORT[r[0].splitlines()[0]]}\n{C.LEVEL_NAME[r[1]]}" for r in rows],
                   fontsize=10)
ax.set_ylabel("conditional hiding contrast (pp)")
ax.set_ylim(0, 62)
ax.set_xlabel("thermal arm, and curriculum level")
ax.set_title("Threat-conditional hiding, last 20 checkpoints, 95% intervals\n"
             "Every bar is far above zero: both agents hide more when hunted. The two agents "
             "overlap in\nalmost every world, and the gaps change sign between worlds.",
             fontsize=10, color=house.INK_2, loc="left", pad=8)
C.legend_below(ax, ncol=2, offset=-0.34)   # 2-line tick labels + x-label sit above it
C.record_samples("t03_arms_result", [
    dict(what="arm \u00d7 level cells", used=len(rows), total=8,
         note="4 thermal arms \u00d7 2 curriculum levels; each needs both a plain and a neuromodulated "
              "run present"),
    dict(what="checkpoints per estimate", used=WIN, total=50,
         note="the newest 20 of 50, the plateau region identified in Figure 1; earlier checkpoints "
              "are excluded because they average in a less-trained policy"),
    dict(what="episodes per checkpoint", used=60, total=60,
         note="30 with a predator and 30 with an empty world"),
    dict(what="training seeds per cell", used=1, total=1,
         note="a single seed per arm, so intervals describe these runs \u2014 not the method")])
fig.subplots_adjust(bottom=0.30)
fig.tight_layout()
C.assert_ticks_dont_collide(ax)
C.assert_no_text_overlap(fig)
C.assert_min_text_px(fig)
house.save(fig, os.path.join(C.FIG, "t03_arms_result"), column_px=C.COLUMN_PX)
for r in rows:
    print(f"{r[0].splitlines()[0]:24} {r[1]}  control {r[2]['control']['mean']:5.1f}  "
          f"modulated {r[2]['modulated']['mean']:5.1f}")
