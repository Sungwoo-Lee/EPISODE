"""FIGURE 3 — In the world they trained in, the two agents hide the same amount at every injury level.

WHAT IS PLOTTED. Unlike Figures 1 and 2, which use small fixed test scenes, this reads the agents'
own training world: one million replayed episodes per agent, restricted to episodes whose starting
injury was handed out at random (so the wound cannot be a consequence of the agent's own behaviour)
and to their first 25 steps. Steps are split by that starting injury into three levels and by
whether a predator is within two cells. The y-value is the share of those steps spent on a bush.

WHAT TO READ FROM IT. The two colours lie on top of each other in both panels -- in the world they
were trained for, the ordinary and neuromodulated agents behave alike. The two line styles do not:
moving from the first version of the world (dashed) to the second (solid) -- where resting in cover
heals wounds 25 times faster, and eating past the target becomes harmful and eventually lethal -- roughly triples calm hiding at low injury, while hiding under threat rises
far less, because it was already high.

WHAT IT CANNOT SAY. These stores exist only for the final saved checkpoint, which is precisely the
reading Figure 1 shows can mislead. The training-world side of this comparison has not been windowed.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
import _common as C, house

house.apply()
fig, ax = plt.subplots(1, 2, figsize=(10.0, 5.2), sharey=True)
for p, (key, title) in enumerate((("hide_calm", "no predator within two cells"),
                                  ("hide_threat", "predator within two cells"))):
    for run, lab, col in C.ARMS:
        arm = run.split("_")[1]
        for wave, ls, mk in (("W1", (0, (4, 2.5)), "s"), ("W2", "-", "o")):
            rows = C.causal_rows(wave, arm)
            ax[p].plot(range(len(rows)), [r[key] for r in rows], color=col, ls=ls, lw=2.2,
                       marker=mk, ms=6, alpha=0.9)
    ax[p].set_xticks(range(3)); ax[p].set_xticklabels(["low\n(0–25)", "middle\n(25–50)", "high\n(50+)"], fontsize=10)
    ax[p].set_xlabel("starting injury, assigned at random")
    ax[p].set_title(title, fontsize=10.5, color=house.INK, loc="left", pad=8)
ax[0].set_ylim(0, 100)
ax[0].set_ylabel("steps spent on a bush (%)")
from matplotlib.lines import Line2D
h = [Line2D([], [], color=house.BLUE, lw=2.4, label="ordinary agent"),
     Line2D([], [], color=house.ORANGE, lw=2.4, label="neuromodulated agent"),
     Line2D([], [], color=house.INK_2, lw=2.2, ls=(0, (4, 2.5)), marker="s", label="first world"),
     Line2D([], [], color=house.INK_2, lw=2.2, marker="o", label="second world")]
# fig.legend, not ax.legend: anchored to one axes and pushed sideways, the legend made
# tight_layout reserve room for it and pulled the two panels apart.
leg = fig.legend(handles=h, loc="lower center", bbox_to_anchor=(0.5, 0.0), ncol=4, frameon=False, handlelength=2.6)
for t in leg.get_texts(): t.set_fontsize(house.FS_LABEL)
fig.suptitle("Training world, final checkpoint. Blue and orange overlap; dashed and solid do not.",
             fontsize=10, color=house.INK_2, x=0.005, ha="left", y=0.995, va="top")
C.record_samples("l03_injury_by_wave", [
    dict(what="episodes replayed per agent per world", used=1000000, total=1000000,
         note="full trajectory store, paired seeds across the two worlds"),
    dict(what="step-rows kept", used=20, total=104,
         note="approximate millions: first 25 steps of randomly-injured episodes only, so the wound "
              "precedes the behaviour"),
    dict(what="checkpoints", used=1, total=50,
         note="the final one only — the stores were collected once; see the limit in the caption"),
    dict(what="training runs", used=4, total=4, note="ordinary and neuromodulated in each world, one seed each")])
fig.tight_layout(w_pad=1.8, rect=(0, 0.12, 1, 0.965))
# Guards AFTER layout: run before it, they inspect a layout that is never saved.
C.assert_ticks_dont_collide(ax[0]); C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)
house.save(fig, os.path.join(C.FIG, "l03_injury_by_wave"), column_px=C.COLUMN_PX)
