"""FIGURE G10 — Replayed training episodes: how much the choice to Rest depends on felt injury.

WHAT IS PLOTTED. 2,000 recorded training-world episodes per agent (final checkpoint) are fed back
through the network twice: exactly as recorded, and with only the felt-injury input changed. The
agent does not act, so the history is identical and every difference is caused by the input.
Top: felt injury raised by 0.3 (the injury scale's 30 points). Bottom: felt injury erased (x 0).
Vertical: change in the probability the agent gives to Rest, in points, averaged over the decisions in
each bin of the felt injury it actually had (horizontal). Solid: the change flows through memory
(sustained); dashed: one step only.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "basicq2_waves"))
import numpy as np, pandas as pd, matplotlib.pyplot as plt
import _common as C, _inj as I, house

house.apply()
REST = 4
ROWS = [("shift", "felt_injury add 0.3", "felt +0.3:\nΔ Rest (pts)"),
        ("erase", "felt_injury scale 0", "felt erased:\nΔ Rest (pts)")]
fig, ax = plt.subplots(len(ROWS), len(I.LEVELS), figsize=(10.0, 5.8), sharex=True, sharey="row")
samples = []
for j, lv in enumerate(I.LEVELS):
    for i, (m, lab, yl) in enumerate(ROWS):
        a = ax[i, j]
        for arm, alab, col in C.ARMS:
            for mem, ls in (("sustained", "-"), ("one_step", "--")):
                p = os.path.join(I.ID, "replay", f"{lv}_{arm}", f"{m}_{mem}", "summary.csv")
                if not os.path.exists(p):
                    continue
                d = pd.read_csv(p); d = d[(d.label == lab) & (d.steps >= I.MIN_DEN)]
                xm = 100 * (d.natural_bin_lo + d.natural_bin_hi) / 2
                a.plot(xm, 100 * (d[f"p_act_{REST}"] - d[f"p_nat_{REST}"]), ls, color=col, marker="o", ms=3,
                       lw=1.6 if ls == "-" else 1.2,
                       label=f"{alab}, {'sustained' if ls == '-' else 'one step'}" if (i == ax.shape[0] - 1 and j == 2) else None)
                if i == 0 and mem == "sustained":
                    samples.append(dict(what=f"level {lv[-2:]} {alab}", used=int(d.steps.sum()),
                                        total=int(pd.read_csv(p).query("label == @lab").steps.sum()),
                                        note=f"decisions in felt-injury bins with at least {I.MIN_DEN:,}; 2,000 episodes"))
        a.axhline(0, color=house.INK, lw=0.8)
        if j == 0:
            a.set_ylabel(yl)
        if i == 0:
            a.set_title(f"level {lv[-2:]}", loc="left", fontsize=10, color=house.INK)
        if i == len(ROWS) - 1:
            a.set_xticks([0, 40, 80]); a.set_xlim(0, 85)
fig.supxlabel("felt injury it had (0-100)", y=0.13, fontsize=11)
fig.tight_layout(h_pad=0.8, w_pad=0.5, rect=(0, 0.1, 1, 1))
C.legend_below(ax[-1, 2], ncol=2, offset=-0.42)
C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)
C.record_kind("g10_replay", "manipulation")
C.record_samples("g10_replay", samples)
house.save(fig, os.path.join(C.FIG, "g10_replay"), column_px=C.COLUMN_PX)
