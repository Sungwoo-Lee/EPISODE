"""FIGURE D1 — In a controlled scene, how differently do the two agents answer a rising threat?

WHAT IS PLOTTED. Five fixed test scenes at curriculum level 04, ordered from nothing to a hunting
predator. For each scene: the share of steps the agent spends on the hiding bush, averaged over the
last 20 saved checkpoints of one training run (left: the neuromodulated agent MINUS the ordinary
one; right: both agents' raw values). Only Wave 2 is shown: Wave 1's test scenes were replayed before
the bush was made to block animals, so its animal scenes are not comparable.

WHAT CLUE IT OFFERS. The extra hiding a predator causes over the empty scene is almost identical in
the two agents, so the modulator does not change the SIZE of the threat response here. The gap is
instead a constant shift in the calm scenes -- which points at a difference in default or idle
behaviour rather than in threat processing.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "basicq2_waves"))
import numpy as np, matplotlib.pyplot as plt
import _common as C, house, window_profile as W

house.apply()
O = os.path.join(C.ROOT, "results/eval/avoidance/metrics_history_rppo_basicq2_wave2_blocking_bush")
SC = [("avoid_none_inj00", "nothing"), ("avoid_rabbitwander_inj00", "rabbit,\nwandering"),
      ("avoid_rabbitwander_predsmell_inj00", "rabbit wandering\n+ predator smell"),
      ("avoid_rabbit_inj00", "rabbit,\nchasing"), ("avoid_pred_inj00", "predator")]
vals = {}
for arm, _, _ in C.ARMS:
    for c, _ in SC:
        _, v = W.read_series(O, f"lvl04_{arm}", c)
        vals[(arm, c)] = v[-20:]
y = np.arange(len(SC))[::-1]
fig, ax = plt.subplots(1, 2, figsize=(10.0, 4.8), sharey=True, gridspec_kw={"width_ratios": [1, 1.25]})
gap = np.array([vals[("modulated", c)].mean() - vals[("control", c)].mean() for c, _ in SC])
# spread of the gap across the 20 checkpoints, pairing the two runs' checkpoints by position
spread = np.array([np.std(vals[("modulated", c)] - vals[("control", c)], ddof=1) for c, _ in SC])
ax[0].barh(y, gap, color=C.GAP, height=0.56)
ax[0].errorbar(gap, y, xerr=spread, fmt="none", ecolor=house.TEXT_LIGHT, elinewidth=1.4, capsize=3.5)
ax[0].axvline(0, color=house.INK, lw=1)
ax[0].set_xlim(-50, 12)
ax[0].set_xlabel("neuromodulated − ordinary (pp)")
ax[0].set_title("the gap", fontsize=10.5, color=house.INK, loc="left", pad=8)
for arm, lab, col in C.ARMS:
    ax[1].plot([vals[(arm, c)].mean() for c, _ in SC], y, "o", ms=8.5, color=col, label=lab)
ax[1].set_xlim(0, 100); ax[1].set_xlabel("steps on the hiding bush (%)")
ax[1].set_title("both agents", fontsize=10.5, color=house.INK, loc="left", pad=8)
ax[0].set_yticks(y); ax[0].set_yticklabels([t.replace(chr(10), " ") for _, t in SC], fontsize=10)
for a_ in ax: a_.grid(axis="y", visible=False)
C.legend_below(ax[1], ncol=2, offset=-0.2)
fig.suptitle("Wave 2, level 04 test scenes. Values: mean of the last 20 checkpoints; whiskers: SD of the gap across them (one run).",
             fontsize=10, color=house.INK_2, x=0.005, ha="left", y=0.995, va="top")
fig.tight_layout(w_pad=1.6, rect=(0, 0, 1, 0.95))
C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)
C.record_kind("d1_threat_ladder", "scene")
C.record_samples("d1_threat_ladder", [
    dict(what="checkpoints per value", used=20, total=50, note="the newest 20 of each run's 50"),
    dict(what="episodes per checkpoint", used=30, total=30, note="fixed seeds shared by both agents"),
    dict(what="worlds with comparable animal scenes", used=1, total=3,
         note="Wave 2 only: Wave 1's scenes predate the bush fix and the blind world has no test scenes"),
    dict(what="training runs", used=2, total=2, note="one seed each")])
house.save(fig, os.path.join(C.FIG, "d1_threat_ladder"), column_px=C.COLUMN_PX)
for (c, t), g, s in zip(SC, gap, spread): print(f"  {t.replace(chr(10),' '):32} gap {g:+6.1f}  sd {s:5.1f}")
