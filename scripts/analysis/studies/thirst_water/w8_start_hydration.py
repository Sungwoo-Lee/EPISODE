"""FIGURE 8 — What the full 0-200 starting range costs (simulation, planned settings, grid 10).

Left: mean survival steps by starting hydration (bins of 10). Right: share of episodes dead of thirst
by step k, compared with 0.625*k/200 -- the share whose starting water would run out by step k if the
agent never reached the pond (the plan's Revision-1 figure, which called this 'whatever the agent does').
"""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
import _common as C
from _sw import SW

house = C.house; house.apply()
W0 = np.array(SW["start"]["W0"]); life = np.array(SW["start"]["life"]); cz = np.array(SW["start"]["cause"])
n = len(W0)
edges = np.arange(0, 201, 10); mid = edges[:-1] + 5
m = [life[(W0 >= lo) & (W0 < lo + 10)].mean() for lo in edges[:-1]]
fig, ax = plt.subplots(1, 2, figsize=(10.2, 3.9))
ax[0].bar(mid, m, width=8.5, color=house.BLUE)
ax[0].axvline(100, color=house.INK, lw=0.9, ls=":"); ax[0].text(103, 540, "setpoint", fontsize=10, color=house.INK_2, va="top")
ax[0].set_ylim(0, 560); ax[0].set_xlim(0, 200)
ax[0].set_xlabel("starting hydration"); ax[0].set_ylabel("mean survival (steps)")
k = np.arange(0, 121)
dead = [100 * np.mean((cz == 1) & (life <= kk)) for kk in k]
ax[1].plot(k, dead, color=house.BLUE, lw=2.0, label="simulated: dead of thirst by step k")
ax[1].plot(k, 100 * 0.625 * k / 200, color=house.INK, lw=1.2, ls="--", label="if it never drank: 0.625 k / 200")
ax[1].set_ylim(0, 40); ax[1].set_xlim(0, 120)
ax[1].set_xlabel("step k"); ax[1].set_ylabel("episodes dead of thirst (%)"); ax[1].legend(loc="upper left", fontsize=10)
fig.tight_layout(w_pad=2.0)
C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)
C.record_kind("w8_start_hydration", "simulation")
C.record_samples("w8_start_hydration", [
    dict(what="episodes", used=n, total=n, note="planned settings, grid 10, list placement, agent knows the pond; start hydration uniform 0-200")])
house.save(fig, os.path.join(C.FIG, "w8_start_hydration"), column_px=C.COLUMN_PX)
print("dead of thirst by 16/50:", dead[16], dead[50], "overall thirst", 100*np.mean(cz==1))
