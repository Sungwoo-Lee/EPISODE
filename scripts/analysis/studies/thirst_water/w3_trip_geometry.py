"""FIGURE 3 — Where the pond can be, and how far the agent walks to reach it, by grid size and mode.

For each grid size (8-20 cells square) and each placement mode (list: the four quadrant blocks just
inside the 1-cell margin; random: any 2x2 block inside the margin; center: the one middle block),
every combination of start cell (not on the pond) and allowed pond position is enumerated, with each
position equally likely, and the Manhattan distance to the nearest pond cell is computed (moves are the
four compass steps and nothing on the level-05 map blocks the agent, so that distance is the walk).
Left: median walk and the 10-90 % range. Right: how many places the pond can be (information the
agent must resolve each episode; centre = 1, i.e. the location never changes).
"""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
import _common as C
import watersim as S

house = C.house; house.apply()
GRIDS = list(range(8, 21))
MODES = [("list", house.INK, "o", "list (4 candidates)"), ("random", "#6e747e", "s", "random"),
         ("center", "#a7acb5", "^", "center")]   # neutral: blue/green/orange mean water/food/fire on this page
stats = {}; n_pairs = 0
for m, *_ in MODES:
    for G in GRIDS:
        opts = S.pond_topleft_options(G, S.Water(placement=m))
        rr, cc = np.meshgrid(np.arange(G), np.arange(G), indexing="ij")
        ds = []
        for (r0, c0) in opts:
            dr = np.maximum(0, np.maximum(r0 - rr, rr - (r0 + 1))); dc = np.maximum(0, np.maximum(c0 - cc, cc - (c0 + 1)))
            dd = dr + dc; ds.append(dd[dd > 0])
        ds = np.concatenate(ds); n_pairs += ds.size
        stats[(m, G)] = (np.median(ds), np.percentile(ds, 10), np.percentile(ds, 90), len(opts))
fig, ax = plt.subplots(1, 2, figsize=(10.2, 4.0))
for m, col, mk, lab in MODES:
    med = [stats[(m, G)][0] for G in GRIDS]; lo = [stats[(m, G)][1] for G in GRIDS]; hi = [stats[(m, G)][2] for G in GRIDS]
    ax[0].plot(GRIDS, med, color=col, marker=mk, ms=4.5, lw=1.8, label=lab)
    if m == "list":                          # shade only the planned mode; one band stays attributable
        ax[0].fill_between(GRIDS, lo, hi, color=col, alpha=0.10, lw=0, label="list: 10-90 % range")
    ax[1].plot(GRIDS, [stats[(m, G)][3] for G in GRIDS], color=col, marker=mk, ms=4.5, lw=1.8, label=lab)
for a in ax:
    a.axvline(10, color="#d4d6dc", lw=6, zorder=0); a.set_xlabel("grid size (cells per side)"); a.set_xticks(GRIDS[::2])
ax[0].set_ylim(0, 30); ax[0].set_xlim(7.5, 20.5); ax[1].set_xlim(7.5, 20.5); ax[1].set_ylim(0.7, 450)
ax[0].set_ylabel("walk to the pond (steps)"); ax[0].legend(loc="upper left", fontsize=10.5)
ax[1].set_yscale("log"); ax[1].set_ylabel("places the pond can be")
ax[1].set_yticks([1, 4, 10, 30, 100, 300]); ax[1].set_yticklabels(["1", "4", "10", "30", "100", "300"])
fig.tight_layout(w_pad=2.2)
C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)
C.record_kind("w3_trip_geometry", "calculation")
C.record_samples("w3_trip_geometry", [
    dict(what="(start cell, pond position) pairs enumerated", used=int(n_pairs), total=int(n_pairs),
         note="every pair, 13 grid sizes x 3 modes; starts on the pond excluded (walk 0)")])
house.save(fig, os.path.join(C.FIG, "w3_trip_geometry"), column_px=C.COLUMN_PX)
print({k: v for k, v in stats.items() if k[1] in (10, 20)})
