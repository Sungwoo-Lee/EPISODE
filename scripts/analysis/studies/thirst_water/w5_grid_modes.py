"""FIGURE 5 — Grid size and placement mode (simulation, scripted agent, no predators, drain 0.625).

Left: share of episodes that last 500 steps, per placement mode, for an agent that knows the pond
(solid) and one that must find it (dashed). Right: share of the agent's steps spent walking to water.
"""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matplotlib.pyplot as plt
import _common as C
from _sw import SW, META

house = C.house; house.apply()
G = META["grids"]; E = META["E"]
MODES = [("list", house.INK, "o"), ("random", "#6e747e", "s"), ("center", "#a7acb5", "^")]   # neutral: blue/green/orange mean water/food/fire
fig, ax = plt.subplots(1, 2, figsize=(10.2, 4.1))
for m, col, mk in MODES:
    k = [SW["grid_mode"][f"{g}|{m}"] for g in G]; s = [SW["grid_mode_search"][f"{g}|{m}"] for g in G]
    ax[0].plot(G, [100 * v["survive"] for v in k], color=col, marker=mk, ms=4.5, lw=1.8, label=f"{m}, knows the pond")
    ax[0].plot(G, [100 * v["survive"] for v in s], color=col, marker=mk, ms=4.5, lw=1.4, ls="--", label=f"{m}, must find it")
    ax[1].plot(G, [100 * v["share"]["walking to water"] for v in k], color=col, marker=mk, ms=4.5, lw=1.8)
    ax[1].plot(G, [100 * v["share"]["walking to water"] for v in s], color=col, marker=mk, ms=4.5, lw=1.4, ls="--")
ax[0].plot(G, [100 * SW["no_water"][str(g)]["survive"] for g in G], color=house.BLUE, lw=1.4, ls=":", label="no water (reference)")
for a in ax:
    a.axvline(10, color="#d4d6dc", lw=6, zorder=0); a.set_xlabel("grid size (cells per side)"); a.set_xticks(G)
ax[0].set_ylim(40, 100); ax[0].set_ylabel("lasts 500 steps (% of episodes)")
ax[1].set_ylim(0, 25); ax[1].set_ylabel("steps walking to water (%)")
fig.tight_layout(rect=(0, 0.16, 1, 1), w_pad=2.0)
h, l = ax[0].get_legend_handles_labels()
fig.legend(h, l, loc="lower center", ncol=3, fontsize=10.5, bbox_to_anchor=(0.5, 0.0), handlelength=3.5)
C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)
C.record_kind("w5_grid_modes", "simulation")
n = E * len(G) * len(MODES)
C.record_samples("w5_grid_modes", [
    dict(what="episodes, agent knows the pond", used=n, total=n, note=f"{len(G)} grids x 3 modes x {E:,}; food 1-4 and fires 1-3 at every size"),
    dict(what="episodes, agent must find it", used=n, total=n, note="same settings and seeds, search on")])
house.save(fig, os.path.join(C.FIG, "w5_grid_modes"), column_px=C.COLUMN_PX)
