"""FIGURE A3 -- Were agents hungry when the fatal hit came?

Level 05 (four agents: the two Wave-2 agents and the two level-05-body agents of the smell study). Distribution
of food energy (satiation, 0-200; setpoint 100) on the step before a fatal predator or trap hit outside a bush
(red), against the same distribution over all steps outside a bush (grey). x: food energy before the step, in
5-unit bins; y: share of the steps in each group (%), so the two curves are comparable in shape.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
import _common as C, _deaths as Dd

house = C.house; house.apply()
D = Dd.deaths()
fat = np.sum([np.array(D[s]["fatal"]["pred_sat_hist"], float) for s in Dd.L05_STORES], 0)
allo = np.sum([np.array(D[s]["sat_all_out"], float) for s in Dd.L05_STORES], 0)
edges = np.arange(0, 205, 5); mid = (edges[:-1] + edges[1:]) / 2
med = lambda h: float(edges[1:][np.searchsorted(np.cumsum(h) / h.sum(), 0.5)])
fig, ax = plt.subplots(figsize=(8.0, 4.0))
ax.plot(mid, 100 * allo / allo.sum(), color="#8a919c", lw=1.6, label=f"all steps outside a bush (median {med(allo):.0f})")
ax.plot(mid, 100 * fat / fat.sum(), color=C.DEATH_COLOURS["predator"], lw=1.8,
        label=f"step before a fatal predator or trap hit (median {med(fat):.0f})")
ax.set_ylim(0, None)
ax.axvline(100, color=house.INK, lw=0.8, ls=":")
ax.text(102, ax.get_ylim()[1] * 0.92, "setpoint 100", fontsize=9.5, color=house.INK)
ax.set_xlim(0, 200); ax.set_xlabel("food energy before the step (0-200)"); ax.set_ylabel("share of steps (%)")
fig.tight_layout(rect=(0, 0.12, 1, 1))
fig.legend(loc="lower center", ncol=1, frameon=False, fontsize=9.5, bbox_to_anchor=(0.5, 0.0))
eps = sum(D[s]["episodes"] for s in Dd.L05_STORES)
inj = sum(D[s]["fatal"]["injury_deaths"] for s in Dd.L05_STORES)
C.finish(fig, "a3_hunger_at_fatal_hit", "recordings", [
    dict(what=f"fatal predator or trap hits outside a bush, level 05 (4 agents, {eps:,} episodes)", used=int(fat.sum()),
         total=int(inj), note="of all injury deaths: the rest are rock or unattributed hits, or hits taken in a bush (none)"),
    dict(what="steps outside a bush, level 05 (same agents)", used=int(allo.sum()), total=int(allo.sum()),
         note="every step after t = 0 spent outside a bush")])
