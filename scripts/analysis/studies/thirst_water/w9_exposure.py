"""FIGURE 9 — The price the simulation leaves out: water steps are steps outside cover.

The pond is not cover (predators walk in freely, decision 9), so every step walking to water or
standing in it is a step a predator can hit. This multiplies the simulated water steps per episode by
the hit rate MEASURED outside cover on real level-05 training recordings (mean damage per step while
moving or standing, not resting: world_measurements.json, the ordinary agent t1none), giving the
expected injury those steps carry. Left: vs drain at grid 10. Right: vs grid size at drain 0.625.
"""
import os, sys, json; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
import _common as C
from _sw import SW, META

house = C.house; house.apply()
wm = json.load(open(os.path.join(C.ROOT, "results/analysis/internal_state_interactions/world_measurements.json")))
run = "20260922-182534_rppo_bq2cover_lvl05_t1none_s42"
h = wm["hazard"][run]["open_not_resting"]; rows_h = wm["hazard"][run]["rows"]
D, G, E = META["drains"], META["grids"], META["E"]


def inj(v):
    steps = (v["share"]["walking to water"] + v["share"]["drinking"]) * v["mean_life"]
    return steps * h, steps


fig, ax = plt.subplots(1, 2, figsize=(10.2, 3.9))
for key, ls, mk, lab in (("drain_grid", "-", "o", "knows the pond"), ("drain_grid_search", "--", "s", "must find it")):
    ax[0].plot(D, [inj(SW[key][f"{d}|10"])[0] for d in D], color=house.BLUE, ls=ls, marker=mk, ms=4.5, lw=1.8, label=lab)
    ax[1].plot(G, [inj(SW[key][f"0.625|{g}"])[0] for g in G], color=house.BLUE, ls=ls, marker=mk, ms=4.5, lw=1.8, label=lab)
for a in ax:
    a.axhline(100, color=house.INK, lw=0.9, ls=":"); a.set_ylim(0, 130); a.set_ylabel("expected injury per episode\nfrom water steps (points)")
    a.legend(loc="upper left", fontsize=10)
ax[0].text(0.98, 104, "lethal injury (100)", ha="left", fontsize=10, color=house.INK_2)
ax[0].set_xlim(0.2, 1.7); ax[0].set_xticks([0.4, 0.8, 1.2, 1.6]); ax[1].set_xlim(7.3, 20.7)
ax[0].set_xlabel("drain per step away from water"); ax[0].axvline(0.625, color="#d4d6dc", lw=6, zorder=0)
ax[1].set_xlabel("grid size (cells per side)"); ax[1].set_xticks(G); ax[1].axvline(10, color="#d4d6dc", lw=6, zorder=0)
fig.tight_layout(w_pad=2.0)
C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)
C.record_kind("w9_exposure", "simulation")
C.record_samples("w9_exposure", [
    dict(what="simulated episodes", used=E * (len(D) + len(G) - 1) * 2, total=E * (len(D) + len(G) - 1) * 2,
         note="drain sweep at grid 10 and grid sweep at drain 0.625, knows / must find"),
    dict(what="recorded level-05 steps (all; the rate uses those outside cover, not resting)", used=int(rows_h), total=int(rows_h),
         note=f"ordinary agent, final checkpoint, steps outside cover not resting: {h:.3f} damage per step")])
house.save(fig, os.path.join(C.FIG, "w9_exposure"), column_px=C.COLUMN_PX)
print("design point", inj(SW["drain_grid"]["0.625|10"]), inj(SW["drain_grid_search"]["0.625|10"]))
