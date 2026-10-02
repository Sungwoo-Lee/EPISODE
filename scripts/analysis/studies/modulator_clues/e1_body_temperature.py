"""FIGURE E1 — At the thermal levels, does behaviour depend on how cold the agent is?

WHY THIS FIGURE. Levels 05 and 06 add a third homeostatic need: the world is cold, the body cools
away from a fire, and the agent dies below -15 degrees. A neuromodulator that reads the body's state
should, if anything, make behaviour track body temperature -- that was the point of adding it.

WHAT IS PLOTTED. From one million replayed episodes per agent in its own training world: steps are
grouped by the agent's body temperature at that moment, and for each group we report the share spent
in a bush with no predator nearby (left of each pair of panels: calm hiding) and how much more with a
predator within two squares (right: the threat response). Both agents in each panel.

WHY IT IS OBSERVATIONAL ONLY. Every episode starts at the body's target temperature, so body
temperature is never assigned at random the way starting injury is. A cold agent is one that has
spent time away from a fire -- which is itself a behaviour. So these curves show what goes TOGETHER
with being cold, not what being cold causes. Bins with too few steps are left out.
"""
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
import _common as C, house

house.apply()
CELLS = [("w1", 5), ("w1", 6), ("w2", 5), ("w2", 6)]
BINS = ["below -10", "-10 to -5", "-5 to 0", "0 and above"]
XL = ["<−10", "−10", "−5", "≥0"]   # bins: below −10 / −10 to −5 / −5 to 0 / 0 and above
fig, ax = plt.subplots(2, 4, figsize=(10.0, 6.0), sharey="row")
pend = []
for j, (world, lvl) in enumerate(CELLS):
    for arm, lab, col in C.ARMS:
        p = os.path.join(C.INT, "context_bodytemp", f"{world}_lvl{lvl:02d}_{arm}.json")
        if not os.path.exists(p):
            pend.append(j); continue
        rows = {r["state"]: r for r in json.load(open(p))["observed"]["rows"]}
        calm = [rows[b]["hide_calm"] if b in rows and rows[b]["n_calm"] > 20000 else np.nan for b in BINS]
        eff = [rows[b]["proximity_effect"] if b in rows and rows[b]["n_threat"] > 20000 else np.nan for b in BINS]
        ax[0, j].plot(range(4), calm, color=col, lw=2.2, marker="o", ms=5, label=lab)
        ax[1, j].plot(range(4), eff, color=col, lw=2.2, marker="o", ms=5)
    ax[0, j].set_title(C.col_label(world, lvl).replace(chr(10), ", "), fontsize=10.5, color=house.INK, loc="left", pad=8)
    for i in range(2):
        ax[i, j].set_xticks(range(4)); ax[i, j].set_xticklabels(XL if i == 1 else [""] * 4, fontsize=9.6)
        if j in pend:
            ax[i, j].annotate("pending", xy=(1.5, 0.5), xycoords=("data", "axes fraction"), ha="center",
                              fontsize=10, color=house.TEXT_LIGHT)
ax[0, 0].set_ylim(0, 60); ax[1, 0].set_ylim(0, 60)
ax[0, 0].set_ylabel("calm hiding (%)"); ax[1, 0].set_ylabel("threat response (pp)")
fig.supxlabel("body temperature at that step, bin lower edge (degrees from the target; death below −15)", fontsize=11, y=0.07)
# figure-level legend in its own band: anchored to one small panel it landed under the shared
# x-label and was drawn over by it.
_h = [plt.Line2D([], [], color=c, lw=2.2, marker="o", ms=5, label=l) for _, l, c in C.ARMS]
_leg = fig.legend(handles=_h, loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, 0.0))
for _t in _leg.get_texts(): _t.set_fontsize(house.FS_LABEL)
fig.tight_layout(h_pad=1.4, w_pad=0.8, rect=(0, 0.11, 1, 1))
C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)
C.record_kind("e1_body_temperature", "observational")
C.record_samples("e1_body_temperature", [
    dict(what="thermal cells", used=4 - len(set(pend)), total=4, note="levels 05 and 06 of both waves; the other levels have no body temperature"),
    dict(what="episodes per agent per cell", used=1000000, total=1000000, note="final-checkpoint store"),
    dict(what="minimum steps for a plotted bin", used=20000, total=20000, note="bins with fewer steps are left blank rather than drawn noisy"),
    dict(what="temperature bins", used=4, total=4, note="below −10, −10 to −5, −5 to 0, 0 and above")])
house.save(fig, os.path.join(C.FIG, "e1_body_temperature"), column_px=C.COLUMN_PX)
print("pending:", sorted(set(pend)))
