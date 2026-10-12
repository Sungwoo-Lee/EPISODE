"""FIGURE A4 -- How much does each extra predator cost?

Share of episodes that survive the 500-step cap, by the number of visible predators drawn for the episode
(0, 1 or 2), one line per level (both Wave-2 agents of a level pooled), each labelled at its end. Level 02
always has exactly one predator, so it has a single point; it is given in the caption and data table, not
drawn. Levels are told apart by grey shade and direct labels -- no marker shapes, which are reserved for the
planner's hide / eat / other on this page. x: number of visible predators in the episode; y: share of those
episodes surviving 500 steps (%).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
import _common as C, _deaths as Dd

house = C.house; house.apply()
B = Dd.counts(); L = Dd.by_level(); levels = sorted(L)
SHADE = {"03": "#b3b9c1", "04": "#7f8792", "05": house.INK, "06": "#3c434d"}
LW = {"03": 1.8, "04": 1.8, "05": 2.4, "06": 1.8}
fig, ax = plt.subplots(figsize=(8.0, 4.4))
rows, ends = [], []
for l in levels:
    agg = {}
    for s in L[l]:
        for k, n in B[s].items():
            k = int(k); nv, r = k // 10000, k % 100
            a = agg.setdefault(nv, [0, 0]); a[1] += n; a[0] += n * (r == 1)
    xs = sorted(agg); ys = [100.0 * agg[x][0] / agg[x][1] for x in xs]
    for x in xs:
        rows.append(dict(what=f"{Dd.LEVEL_LABEL[l]}, {x} visible predator(s)", used=agg[x][1] if len(xs) > 1 else 0,
                         total=sum(v[1] for v in agg.values()),
                         note=("episodes with this predator count, both agents pooled" if len(xs) > 1 else
                               f"single point, not drawn; {ys[0]:.0f} % survive, given in the caption")))
    if len(xs) < 2:
        continue
    ax.plot(xs, ys, color=SHADE[l], lw=LW[l], solid_capstyle="round")
    ends.append([ys[-1], ys[-1], l])
# direct labels at the line ends, pushed apart by at least 6 points, with a short leader line
ends.sort()
ends[0][1] = max(ends[0][1], 3.5)                 # keep the lowest label inside the panel
for i in range(1, len(ends)):
    ends[i][1] = max(ends[i][1], ends[i - 1][1] + 6.0)
for y0, yl, l in ends:
    ax.plot([2.0, 2.06], [y0, yl], color=SHADE[l], lw=0.8)
    ax.text(2.08, yl, "level 07 (old 06)" if l == "06" else Dd.LEVEL_LABEL[l], va="center", fontsize=9.5, color=house.INK)
ax.set_xticks([0, 1, 2]); ax.set_xlim(-0.1, 2.75); ax.set_ylim(0, 100)
ax.set_xlabel("visible predators in the episode"); ax.set_ylabel("episodes surviving 500 steps (%)")
fig.tight_layout()
C.finish(fig, "a4_survival_by_predator_count", "recordings", rows)
