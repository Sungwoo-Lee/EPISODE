"""FIGURE A4 — Does a wound make the agent treat a HARMLESS animal as a threat? (Sensor Ladder 10-12)

THE QUESTION. Hiding more from a predator when wounded is ordinary caution. The signature the
project is looking for -- hypervigilance -- is a change in what counts as a threat: a wound that
raises the agent's response to a harmless rabbit by MORE than it raises its response to a predator.
If both rise equally, the agent has only become more defensive overall.

HOW IT IS COMPUTED. Within each quarter of the STARTING injury -- assigned at random before the agent
acts, so the contrast is causal -- the proximity effect is the share of steps on a bush with the
nearest animal 1-2 squares away minus with it 6 or more away. The wound's shift is the most-wounded
quarter minus the least. The "criterion shift" is the rabbit shift minus the predator shift:
positive means the wound made the harmless animal count for more, relative to the real threat.

WHAT CLUE IT OFFERS. Where, if anywhere, the modulator makes a harmless cue more alarming when
wounded -- which is the behaviour a state-dependent gain on threat evidence ought to produce.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "ladder"))
import numpy as np, matplotlib.pyplot as plt
import _common as C, house
from _ladder import proximity_effect

house.apply()
COLS = [c for c in C.COLUMNS if c[0] == "blind" or c[1] >= 4]


def shifts(d):
    g = d["grids"]
    f = lambda k, b: proximity_effect(g[f"{k}_bush"], g[f"{k}_tot"], b)
    rab = f("rd", (3,)) - f("rd", (0,)); pre = f("pd", (3,)) - f("pd", (0,))
    return rab, pre, rab - pre


fig, ax = plt.subplots(1, 2, figsize=(10.0, 5.4), sharey=True, gridspec_kw={"width_ratios": [1.25, 1]})
y = np.arange(len(COLS))[::-1]
vals, pend = {}, []
for i, (world, lvl) in enumerate(COLS):
    d = {arm: C.ladder(world, lvl, arm) for arm, _, _ in C.ARMS}
    if None in d.values():
        pend.append(i); continue
    for arm in d: vals[(i, arm)] = shifts(d[arm])
for i in range(len(COLS)):
    if i in pend:
        ax[0].annotate("pending", xy=(0, y[i]), ha="center", va="center", fontsize=10, color=house.TEXT_LIGHT)
        continue
    for k, (arm, lab, col) in enumerate(C.ARMS):
        r, p, c = vals[(i, arm)]
        ax[0].plot([r], [y[i] + (0.5 - k) * 0.28], "o", ms=7.5, color=col, label=lab if i == 0 else None)
        ax[0].plot([p], [y[i] + (0.5 - k) * 0.28], "s", ms=7, mfc="none", mec=col, mew=1.8)
    gap = vals[(i, "modulated")][2] - vals[(i, "control")][2]
    ax[1].barh(y[i], gap, color=C.GAP, height=0.55)
ax[0].plot([], [], "o", color=house.INK_2, label="harmless rabbit (filled)")
ax[0].plot([], [], "s", mfc="none", mec=house.INK_2, mew=1.8, label="predator (hollow)")
for a in ax:
    a.axvline(0, color=house.INK, lw=1); a.grid(axis="y", visible=False)
    a.set_ylim(-0.8, len(COLS) - 0.2)
ax[0].set_yticks(y); ax[0].set_yticklabels([C.col_label(*c).replace(chr(10), " ") for c in COLS], fontsize=10)
ax[0].set_xlabel("wound's shift in proximity effect (pp)")
ax[0].set_title("how much a wound raises hiding near each animal", fontsize=10.5, color=house.INK, loc="left", pad=8)
ax[1].set_xlabel("criterion shift: neuromodulated − ordinary (pp)")
ax[1].set_title("the modulator's effect on it", fontsize=10.5, color=house.INK, loc="left", pad=8)
C.legend_below(ax[0], ncol=2, offset=-0.17)
fig.tight_layout(w_pad=1.6)
C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)
C.record_kind("a4_hypervigilance", "causal")
C.record_samples("a4_hypervigilance", [
    dict(what="world × level cells", used=len(COLS) - len(pend), total=len(COLS),
         note="blind plus levels 04-06; level 02 never randomises the starting wound, and Wave 1 level 03 is unmatched"),
    dict(what="injury quarters compared", used=2, total=4, note="the most and least wounded starting quarters"),
    dict(what="distance bins", used=6, total=8, note="1-2 squares (near) against 6 or more (far); 3-5 are left out as ambiguous"),
    dict(what="checkpoints", used=1, total=5, note="final only — this filtered measure needs the 1M sample")])
house.save(fig, os.path.join(C.FIG, "a4_hypervigilance"), column_px=C.COLUMN_PX)
for (i, arm), v in sorted(vals.items()):
    print(f"  {C.col_label(*COLS[i]).replace(chr(10),' '):20} {arm:9} rabbit {v[0]:+6.2f} predator {v[1]:+6.2f} criterion {v[2]:+6.2f}")
