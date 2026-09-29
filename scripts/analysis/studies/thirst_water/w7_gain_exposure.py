"""FIGURE 7 — The water consumption value: gain per step on the pond (simulation, grid 10, no predators).

Left: steps the agent stands on the pond per visit -- its exposure at a fixed place predators can
reach -- as gain varies, at drain 0.625 (planned) and 1.0. Right: share of episodes lasting 500 steps.
The scripted agent drinks until hydration reaches 160.
"""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matplotlib.pyplot as plt
import _common as C
from _sw import SW, META

house = C.house; house.apply()
A, E = META["gains"], META["E"]
fig, ax = plt.subplots(1, 2, figsize=(10.2, 3.9))
for d, ls, mk in ((0.625, "-", "o"), (1.0, "--", "s")):
    v = [SW["drain_gain"][f"{d}|{a}"] for a in A]
    ax[0].plot(A, [x["steps_per_visit"] for x in v], color=house.BLUE, ls=ls, marker=mk, ms=4.5, lw=1.8, label=f"drain {d:g}")
    ax[1].plot(A, [100 * x["survive"] for x in v], color=house.INK, ls=ls, marker=mk, ms=4.5, lw=1.8, label=f"drain {d:g}")
for a in ax:
    a.axvline(5.625, color="#d4d6dc", lw=6, zorder=0); a.set_xlabel("gain per step standing on the pond"); a.legend(fontsize=10)
ax[0].set_ylim(0, 70); ax[0].set_ylabel("steps on the pond per visit")
ax[1].set_ylim(30, 100); ax[1].set_ylabel("lasts 500 steps (% of episodes)")
fig.tight_layout(w_pad=2.0)
C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)
C.record_kind("w7_gain_exposure", "simulation")
n = E * len(A) * 2
C.record_samples("w7_gain_exposure", [
    dict(what="episodes", used=n, total=n, note=f"{len(A)} gains x 2 drains x {E:,}, grid 10, list placement, agent knows the pond")])
house.save(fig, os.path.join(C.FIG, "w7_gain_exposure"), column_px=C.COLUMN_PX)
