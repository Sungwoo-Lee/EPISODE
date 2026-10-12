"""FIGURE A5 -- Which predators kill: sight and pounce reach, in level-05 episodes with exactly one predator.

Left: share of episodes surviving 500 steps; right: share ending in an injury death; by the predator's sight
(detection_range, 1-7 cells) and pounce reach (attack_range, 2 or 3 cells). 6,674,860 episodes from 20
level-05-world agents. A pounce only fires during a chase, which ends once the agent is beyond 1.5 x sight
(core.py _hunt_step), so at sight 1 the pounce reach makes no difference. x: predator sight (cells);
y: share of episodes (%).
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
import _common as C

house = C.house; house.apply()
A = json.load(open(os.path.join(C.FIG, "data", "one_predator_l05_by_sight_pounce.json")))
cell = {}
for r in A["rows"]:
    c = cell.setdefault((r["sight"], r["pounce"]), dict(n=0, surv=0, inj=0))
    c["n"] += r["episodes"]; c["surv"] += r["endings"].get("1", 0); c["inj"] += r["endings"].get("4", 0)
fig, ax = plt.subplots(1, 2, figsize=(9.2, 4.2), sharex=True)
xs = list(range(1, 8))
for p in (2, 3):
    st = C.POUNCE_STYLE[p]
    for j, key in enumerate(("surv", "inj")):
        ax[j].plot(xs, [100.0 * cell[(x, p)][key] / cell[(x, p)]["n"] for x in xs], ls=st["ls"],
                   color=st["color"], lw=1.8, label=f"pounce reach {p}")
ax[0].set_ylabel("episodes surviving 500 steps (%)"); ax[1].set_ylabel("episodes ending in injury death (%)")
for a in ax:
    a.set_xlabel("predator sight (detection range, cells)"); a.set_xticks(xs); a.set_ylim(0, 100)
fig.tight_layout(rect=(0, 0.1, 1, 1), w_pad=2.0)
fig.legend(*ax[0].get_legend_handles_labels(), loc="lower center", ncol=2, frameon=False, fontsize=9.5, handlelength=2.6,
           bbox_to_anchor=(0.5, 0.0))
C.finish(fig, "a5_sight_pounce", "recordings", [
    dict(what=f"sight {x}, pounce {p}", used=cell[(x, p)]["n"], total=A["episodes"],
         note="level-05-world episodes with exactly one visible predator of this kind") for x in xs for p in (2, 3)])
