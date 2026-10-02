"""FIGURE D2 — At the thermal levels, does the modulator change calm hiding or threat response?

WHAT IS PLOTTED. The level-05 and level-06 agents (Wave 2) replayed in four versions of a test scene
made survivable in different ways: the whole world warmed to the body's target ("neutral"), warmed
most of the way ("cool"), the trained cold with a fire beside the bush, and the trained cold with the
fire away from it. Every comfortable version is a world the agent never trained in, so the four are a
sensitivity check on each other. Two quantities, each as neuromodulated MINUS ordinary, averaged over
the last 20 checkpoints: calm hiding (share of steps on the bush in an empty scene) and the threat
response (predator scene minus empty scene).

WHAT CLUE IT OFFERS. Whether a gap, if any, holds its sign across all four temperature fixes -- a gap
that flips between fixes is more likely a product of the fix than of the agent.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "basicq2_waves"))
import numpy as np, matplotlib.pyplot as plt
import _common as C, house, window_profile as W

house.apply()
EV = os.path.join(C.ROOT, "results/eval/avoidance")
ARMSX = [("neutral", "neutral"), ("cool", "cool"), ("fire_by_bush", "fire beside bush"),
         ("fire_away", "fire away from bush")]
rows = []   # (label, level, calm gap, calm sd, threat gap, threat sd)
for key, name in ARMSX:
    O = os.path.join(EV, f"metrics_history_rppo_thermalprobe_{key}_clean")
    for lvl in ("lvl05", "lvl06"):
        v = {}
        for arm in ("control", "modulated"):
            _, n = W.read_series(O, f"{lvl}_{arm}", "avoid_none_inj00")
            _, p = W.read_series(O, f"{lvl}_{arm}", "avoid_pred_inj00")
            v[arm] = (n[-20:], p[-20:] - n[-20:])
        cg = v["modulated"][0] - v["control"][0]; tg = v["modulated"][1] - v["control"][1]
        rows.append((f"{name}, level {lvl[-2:]}", cg.mean(), cg.std(ddof=1), tg.mean(), tg.std(ddof=1)))
y = np.arange(len(rows))[::-1]
fig, ax = plt.subplots(1, 2, figsize=(10.0, 5.2), sharey=True)
for p, (i, title) in enumerate(((1, "calm hiding (empty scene)"), (3, "threat response (predator − empty)"))):
    g = np.array([r[i] for r in rows]); s = np.array([r[i + 1] for r in rows])
    ax[p].barh(y, g, color=C.GAP, height=0.56)
    ax[p].errorbar(g, y, xerr=s, fmt="none", ecolor=house.TEXT_LIGHT, elinewidth=1.4, capsize=3.2)
    ax[p].axvline(0, color=house.INK, lw=1)
    ax[p].set_xlim(-45, 45)
    ax[p].set_title(title, fontsize=10.5, color=house.INK, loc="left", pad=8)
    ax[p].set_xlabel("neuromodulated − ordinary (pp)")
    ax[p].grid(axis="y", visible=False)
ax[0].set_yticks(y); ax[0].set_yticklabels([r[0] for r in rows], fontsize=10)
fig.suptitle("Wave 2, thermal levels, four survivable versions of the test scene. Bars: 20-checkpoint mean gap; whiskers: its SD (one run).",
             fontsize=10, color=house.INK_2, x=0.005, ha="left", y=0.995, va="top")
fig.tight_layout(w_pad=1.6, rect=(0, 0, 1, 0.95))
C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)
C.record_kind("d2_thermal_scenes", "scene")
C.record_samples("d2_thermal_scenes", [
    dict(what="temperature fixes × levels", used=len(rows), total=8, note="4 fixes × levels 05 and 06"),
    dict(what="checkpoints per value", used=20, total=50, note="the newest 20"),
    dict(what="episodes per checkpoint", used=30, total=30, note="fixed seeds shared by both agents"),
    dict(what="worlds", used=1, total=3,
         note="Wave 2 only: Wave 1 trained on a different hunger scale, so the scenes misstate its fullness; "
              "the blind world has no thermal levels")])
house.save(fig, os.path.join(C.FIG, "d2_thermal_scenes"), column_px=C.COLUMN_PX)
for r in rows: print(f"  {r[0]:34} calm {r[1]:+6.1f}±{r[2]:4.1f}   threat {r[3]:+6.1f}±{r[4]:4.1f}")
