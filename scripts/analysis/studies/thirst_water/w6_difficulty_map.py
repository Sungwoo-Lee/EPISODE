"""FIGURE 6 — The difficulty map: drain rate x grid size (simulation, scripted agent, no predators).

Each cell: share of episodes lasting 500 steps, list placement, gain 5.625. Left: the agent knows
where the pond is. Right: it must find it first. The planned design point (drain 0.625, grid 10) is
outlined.
"""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import _common as C
from _sw import SW, META

house = C.house; house.apply()
D, G, E = META["drains"], META["grids"], META["E"]
fig, ax = plt.subplots(1, 2, figsize=(10.4, 4.8))
for a, key, title in ((ax[0], "drain_grid", "knows the pond"), (ax[1], "drain_grid_search", "must find it")):
    M = np.array([[100 * SW[key][f"{d}|{g}"]["survive"] for g in G] for d in D])
    im = a.imshow(M, cmap="Blues", vmin=0, vmax=100, origin="lower", aspect="auto")
    for i in range(len(D)):
        for j in range(len(G)):
            a.text(j, i, f"{M[i, j]:.0f}", ha="center", va="center", fontsize=10.5,
                   color="white" if M[i, j] > 60 else house.INK)
    a.add_patch(Rectangle((G.index(10) - 0.5, D.index(0.625) - 0.5), 1, 1, fill=False, ec=house.ORANGE, lw=2.4))
    a.set_xticks(range(len(G))); a.set_xticklabels(G); a.set_yticks(range(len(D))); a.set_yticklabels([f"{d:g}" for d in D])
    a.set_xlabel("grid size (cells per side)"); a.set_ylabel("drain per step"); a.grid(False)
    a.set_title(title, fontsize=12)
fig.tight_layout(w_pad=2.0)
C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)
C.record_kind("w6_difficulty_map", "simulation")
n = E * len(D) * len(G)
C.record_samples("w6_difficulty_map", [
    dict(what="episodes, agent knows the pond", used=n, total=n, note=f"{len(D)} drains x {len(G)} grids x {E:,}, list placement"),
    dict(what="episodes, agent must find it", used=n, total=n, note="same settings and seeds, search on")])
house.save(fig, os.path.join(C.FIG, "w6_difficulty_map"), column_px=C.COLUMN_PX)
