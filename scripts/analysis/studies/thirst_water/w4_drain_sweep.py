"""FIGURE 4 — How the drain rate changes survival at grid 10 (simulation, scripted agent, no predators).

Left: share of episodes that last the full 500 steps, for an agent that knows where the pond is and
one that must find it first. Middle: how the episodes that die, die (knows the pond). Right: pond
visits per episode and steps on the pond per visit (knows the pond).
"""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
import _common as C
from _sw import SW, META

house = C.house; house.apply()
D = META["drains"]; E = META["E"]
known = [SW["drain_grid"][f"{d}|10"] for d in D]
search = [SW["drain_grid_search"][f"{d}|10"] for d in D]
fig, ax = plt.subplots(1, 3, figsize=(10.2, 4.1))
a = ax[0]
a.plot(D, [100 * k["survive"] for k in known], color=house.INK, marker="o", ms=4.5, lw=1.8, label="knows the pond")
a.plot(D, [100 * k["survive"] for k in search], color=house.INK, marker="s", ms=4.5, lw=1.8, ls="--", label="must find it")
base = 100 * SW["no_water"]["10"]["survive"]
a.axhline(base, color="#8a8f99", lw=1.2, ls=":", label="no water (reference)")
a.set_ylim(80, 100); a.set_ylabel("lasts 500 steps (% of episodes)")
a.legend(loc="lower left", fontsize=10.5)
b = ax[1]; bottom = np.zeros(len(D)); x = np.arange(len(D))
for cz in C.CAUSE_ORDER[1:]:
    v = np.array([100 * k["causes"][cz] for k in known])
    if v.max() < 0.05:
        continue
    b.bar(x, v, bottom=bottom, color=C.CAUSE_COLOURS[cz], width=0.7, label=cz); bottom += v
b.set_xticks(x); b.set_xticklabels([f"{d:g}" for d in D], rotation=90); b.set_ylabel("episodes that die (%)")
b.set_ylim(0, 10); b.legend(loc="upper left", fontsize=10.5)
c = ax[2]
c.plot(D, [k["drinks"] for k in known], color=house.BLUE, marker="o", ms=4.5, lw=1.8, label="drinking visits per episode")
c.plot(D, [k["steps_per_drink"] / 5 for k in known], color="#6e747e", marker="s", ms=4.5, lw=1.8, label="steps per drinking visit / 5")
c.set_ylim(0, 8); c.set_ylabel("count"); c.legend(loc="upper left", fontsize=10.5)
for a_ in ax:
    a_.set_xlabel("drain per step away from water")
for a_ in (ax[0], ax[2]):
    a_.axvline(0.625, color="#d4d6dc", lw=6, zorder=0); a_.set_xlim(0.2, 1.7); a_.set_xticks([0.4, 0.8, 1.2, 1.6])
b.axvspan(2.6, 3.4, color="#d4d6dc", zorder=0, lw=0)
fig.tight_layout(w_pad=1.6)
C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)
C.record_kind("w4_drain_sweep", "simulation")
C.record_samples("w4_drain_sweep", [
    dict(what="episodes per drain value, agent knows the pond", used=E * len(D), total=E * len(D), note=f"{len(D)} drain values x {E:,} episodes, grid 10, list placement"),
    dict(what="episodes per drain value, agent must find it", used=E * len(D), total=E * len(D), note="same settings and seeds, search on")])
house.save(fig, os.path.join(C.FIG, "w4_drain_sweep"), column_px=C.COLUMN_PX)
