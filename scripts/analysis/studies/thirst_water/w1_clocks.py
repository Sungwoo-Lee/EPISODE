"""FIGURE 1 — The body clocks at the planned settings: how long each need lets the agent go.

Left: hydration over time from the setpoint (100 of 200) -- away from water it drains 0.625 per step
and reaches 0 at step 160; standing on the pond it rises a net 5 per step and reaches the 200 ceiling
at step 20. Right: steps from the comfortable middle to death, per need, against the 500-step cap.
Exact arithmetic from the planned rule (THIRST_WATER_PLAN.md, target-first water clock); the cold
clock is the measured 86-99-step band quoted from CONFIG_CRITICAL_SETTINGS.md (2026-09-19).
"""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
import _common as C
import watersim as S

house = C.house; house.apply()
Wt = S.Water()
k = np.arange(0, 201)
away = np.clip(Wt.setpoint - Wt.drain * k, 0, Wt.max)
on = np.clip(Wt.setpoint + (Wt.gain - Wt.drain) * k, 0, Wt.max)
t_thirst = int(round(Wt.setpoint / Wt.drain)); t_over = int(round((Wt.max - Wt.setpoint) / (Wt.gain - Wt.drain)))

fig, ax = plt.subplots(1, 2, figsize=(10.2, 4.0), gridspec_kw=dict(width_ratios=[1.15, 1]))
a = ax[0]
a.plot(k[:t_thirst + 1], away[:t_thirst + 1], color=house.BLUE, lw=2.2, label="away from water (-0.625 per step)")
a.plot(k[:t_over + 1], on[:t_over + 1], color=house.ORANGE, lw=2.2, label="standing on the pond (+5 net per step)")
a.axhline(Wt.setpoint, color="#8a8f99", lw=0.9, ls=":")
a.scatter([t_thirst, t_over], [0, Wt.max], color=house.INK, zorder=5, s=22)
a.annotate(f"dies of thirst\nat step {t_thirst}", (t_thirst, 0), xytext=(118, 34), fontsize=10.5, color=house.INK)
a.annotate(f"over-drinks\nat step {t_over}", (t_over, Wt.max), xytext=(32, 172), fontsize=10.5, color=house.INK)
a.text(186, 104, "setpoint", fontsize=10, color=house.INK_2, ha="right")
a.set_xlim(0, 200); a.set_ylim(0, 215)
a.set_xlabel("steps since leaving the setpoint"); a.set_ylabel("hydration (0-200)")
a.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=1, fontsize=10.5)

b = ax[1]
rows = [("hunger", 100, 100, house.GREEN), ("cold", 86, 99, "#5b6bbf"), ("thirst", t_thirst, t_thirst, house.BLUE)]
for i, (lab, lo, hi, col) in enumerate(rows):
    b.barh(i, hi, color=col, height=0.55)
    if hi > lo:
        b.barh(i, hi - lo, left=lo, color="white", alpha=0.45, height=0.55, hatch="///", edgecolor=col, lw=0)
    b.text(hi + 8, i, f"{lo}" if lo == hi else f"{lo}-{hi}", va="center", fontsize=11, color=house.INK)
b.axvline(500, color=house.INK, lw=1.0, ls="--"); b.text(492, 2.45, "episode cap", ha="right", fontsize=10, color=house.INK_2)
b.set_yticks(range(3)); b.set_yticklabels([r[0] for r in rows]); b.set_ylim(-0.6, 2.8)
b.set_xlim(0, 520); b.grid(axis="x"); b.grid(axis="y", visible=False)
b.set_xlabel("steps from the comfortable middle to death")
fig.tight_layout(w_pad=2.0)
C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)
C.record_kind("w1_clocks", "calculation")
C.record_samples("w1_clocks", [
    dict(what="hydration steps computed", used=len(k), total=len(k), note="every step 0-200 of the planned rule, exact"),
    dict(what="cold clock (quoted)", used=600, total=600, note="real level-05 resets at shipped values, CONFIG_CRITICAL_SETTINGS 2026-09-19")])
house.save(fig, os.path.join(C.FIG, "w1_clocks"), column_px=C.COLUMN_PX)
