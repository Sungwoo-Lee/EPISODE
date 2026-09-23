"""FIGURE A4 — Hypervigilance: does a badly injured agent avoid the harmless rabbit more? (Sensor Ladder 10-12)

THE PROJECT'S DEFINITION. Hypervigilance is injury-state-dependent avoidance of a HARMLESS animal: a
badly injured agent avoids the rabbit more than a lightly injured one. The predator is not the
reference -- it appears only in the right-hand panel, as ordinary threat avoidance, for context.

TWO READINGS OF "AVOID", each as the most-injured quarter minus the least-injured one:
  * hiding  -- the proximity effect: share of steps in a bush with the nearest rabbit 1-2 squares
               away minus with it 6 or more away. A positive shift = the injured agent hides from a
               nearby rabbit more;
  * distance -- share of steps on which the nearest rabbit is within 2 squares, with no predator within
               2 squares. A NEGATIVE shift = the injured agent lets the rabbit come close less often.
TWO READINGS OF "INJURED": the starting injury the environment assigned at random (filled markers,
causal; hiding over the whole episode, distance over the first 25 steps) and the injury the agent
carries at that moment (hollow markers, observational -- a hurt agent was usually just attacked).

WHAT CLUE IT OFFERS. Where, if anywhere, either agent shows the injury-dependent rabbit avoidance the
project calls hypervigilance, and whether the modulator adds to it.
"""
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "ladder"))
import numpy as np, matplotlib.pyplot as plt
import _common as C, house
from _ladder import proximity_effect

house.apply()
COLS = [c for c in C.COLUMNS if c[0] == "blind" or c[1] >= 4]


def key(world, lvl, arm):
    return f"blind_{arm}" if world == "blind" else f"{world}_lvl{lvl:02d}_{arm}"


def hiding_shift(d, grid):
    g = d["grids"]; f = lambda b: proximity_effect(g[f"{grid}_bush"], g[f"{grid}_tot"], b)
    return f((3,)) - f((0,))


def distance_shift(world, lvl, arm, which):
    p = os.path.join(C.INT, "rabbit_avoidance", key(world, lvl, arm) + ".json")
    return json.load(open(p))[which]["near_share_shift"] if os.path.exists(p) else np.nan


V = {}
for j, (world, lvl) in enumerate(COLS):
    for arm, _, _ in C.ARMS:
        d = C.ladder(world, lvl, arm)
        V[(j, arm)] = dict(hide_s=hiding_shift(d, "rd"), hide_c=hiding_shift(d, "rdc"),
                           dist_s=distance_shift(world, lvl, arm, "start"),
                           dist_c=distance_shift(world, lvl, arm, "current"),
                           pred_s=hiding_shift(d, "pd"))
PANELS = [("hide", "hiding near the rabbit\n(+ = injured hides more)"),
          ("dist", "rabbit within 2 squares\n(− = injured keeps it away)"),
          ("pred", "context: hiding near a predator\n(ordinary threat avoidance)")]
fig, ax = plt.subplots(1, 3, figsize=(10.0, 5.6), sharey=True)
y = np.arange(len(COLS))[::-1]
for p, (kind, title) in enumerate(PANELS):
    for j in range(len(COLS)):
        for k, (arm, lab, col) in enumerate(C.ARMS):
            yy = y[j] + (0.5 - k) * 0.3
            if kind == "pred":
                ax[p].plot([V[(j, arm)]["pred_s"]], [yy], "o", ms=7, color=col, alpha=0.55)
                continue
            ax[p].plot([V[(j, arm)][f"{kind}_s"]], [yy], "o", ms=7.5, color=col,
                       label=f"{lab}, assigned injury (causal)" if (p == 0 and j == 0) else None)
            ax[p].plot([V[(j, arm)][f"{kind}_c"]], [yy], "o", ms=7.5, mfc="none", mec=col, mew=1.8,
                       label=f"{lab}, current injury (observational)" if (p == 0 and j == 0) else None)
    ax[p].axvline(0, color=house.INK, lw=1); ax[p].grid(axis="y", visible=False)
    ax[p].set_ylim(-0.8, len(COLS) - 0.2)
    ax[p].set_title(title, fontsize=10, color=house.INK if kind != "pred" else house.TEXT_LIGHT, loc="left", pad=8)
    ax[p].set_xlabel("most − least injured (pp)", fontsize=10)
ax[0].set_yticks(y); ax[0].set_yticklabels([C.col_label(*c).replace(chr(10), " ") for c in COLS], fontsize=10)
h, l = ax[0].get_legend_handles_labels()
leg = fig.legend(h, l, loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, 0.0))
for t in leg.get_texts(): t.set_fontsize(house.FS_LABEL)
fig.tight_layout(w_pad=1.2, rect=(0, 0.13, 1, 1))
C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)
C.record_kind("a4_hypervigilance", "causal")
C.record_samples("a4_hypervigilance", [
    dict(what="world × level cells", used=len(COLS), total=len(COLS),
         note="blind plus levels 04-06 of both waves; Wave 1 levels 02/03 unmatched, level 02 has no random injury"),
    dict(what="episodes per agent per cell", used=1000000, total=1000000,
         note="final-checkpoint store; only episodes containing a rabbit count"),
    dict(what="injury quarters compared", used=2, total=4, note="the most- and least-injured quarters")])
house.save(fig, os.path.join(C.FIG, "a4_hypervigilance"), column_px=C.COLUMN_PX)
for (j, arm), v in sorted(V.items()):
    print(f"  {C.col_label(*COLS[j]).replace(chr(10),' '):18} {arm:9} " + " ".join(f"{k}={v[k]:+.2f}" for k in v))
