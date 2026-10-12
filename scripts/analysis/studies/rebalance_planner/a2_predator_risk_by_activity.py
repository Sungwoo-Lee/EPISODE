"""FIGURE A2 -- When do predators and traps kill: right after eating, on the way to food, or roaming?

Fatal hits per 1,000 steps spent in each activity outside a bush, per level (both Wave-2 agents of a level
pooled). Left: hits by a visible predator; right: by a trap (hidden predator). The activity is a working
definition: "just ate" = ate in the last 20 steps; "heading to food" = this step moved closer to the nearest
food item; "roaming" = anything else outside a bush. Steps in a bush carry no deaths in any store.
x: fatal hits per 1,000 steps in that activity (same scale in both panels); y: level; bar shade: activity
(light = just ate, mid = heading to food, full = roaming).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
import _common as C, _deaths as Dd

house = C.house; house.apply()
D = Dd.deaths(); L = Dd.by_level(); levels = sorted(L)
ACTS = ["out_ate20", "out_toward", "out_other"]
rate, steps, bush_deaths = {}, {}, 0
for l in levels:
    for src, keys in (("predator", ("visible", "both")), ("trap", ("hidden",))):
        for a in ACTS:
            n = sum(D[s]["fatal"][k][a] for s in L[l] for k in keys)
            st = sum(D[s]["steps"][a] for s in L[l])
            rate[(l, src, a)] = 1000.0 * n / st
            steps[(l, a)] = st
    bush_deaths += sum(D[s]["fatal"][k]["bush"] for s in L[l] for k in ("visible", "hidden", "both"))
y = np.arange(len(levels))[::-1].astype(float)
xmax = 1.08 * max(rate.values())
# activity is shown by SHADE of the source colour (light = just ate, mid = heading to food, full = roaming):
# marker shapes are reserved for the planner's hide / eat / other on this page
ALPHA = {"out_ate20": 0.30, "out_toward": 0.62, "out_other": 1.0}
H = 0.26
fig, ax = plt.subplots(1, 2, figsize=(9.2, 4.6), sharey=True)
for j, src in enumerate(("predator", "trap")):
    for k, a in enumerate(ACTS):
        ax[j].barh(y + (1 - k) * H, [rate[(l, src, a)] for l in levels], height=H * 0.92,
                   color=C.DEATH_COLOURS[src], alpha=ALPHA[a], edgecolor=house.INK_2, lw=0.4)
    ax[j].set_xlim(0, xmax); ax[j].grid(axis="y", visible=False)
    ax[j].set_title("killed by a visible predator" if src == "predator" else "killed by a trap (hidden predator)",
                    loc="left", fontsize=10.5)
    ax[j].set_xlabel("fatal hits per 1,000 steps in the activity")
ax[0].set_yticks(y); ax[0].set_yticklabels([Dd.LEVEL_LABEL[l] for l in levels])
fig.tight_layout(rect=(0, 0.14, 1, 1), w_pad=1.5)
from matplotlib.patches import Patch
fig.legend(handles=[Patch(facecolor="#6e747e", alpha=ALPHA[a], edgecolor=house.INK_2, lw=0.4, label=Dd.ACT_LABEL[a])
                    for a in ACTS], loc="lower center", ncol=2, frameon=False, fontsize=9.5, bbox_to_anchor=(0.5, 0.0))
assert bush_deaths == 0, bush_deaths
rows = []
for l in levels:
    eps = sum(D[s]["episodes"] for s in L[l])
    tot = sum(D[s]["length_sum"] for s in L[l])
    out = sum(steps[(l, a)] for a in ACTS)
    rows.append(dict(what=f"{Dd.LEVEL_LABEL[l]}: steps outside a bush ({len(L[l])} agent(s), {eps:,} episodes)",
                     used=int(out), total=int(tot),
                     note="the rest are steps in a bush, where no store has a single predator or trap death"))
C.finish(fig, "a2_predator_risk_by_activity", "recordings", rows)
