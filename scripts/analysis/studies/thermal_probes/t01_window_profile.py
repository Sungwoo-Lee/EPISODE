"""FIGURE 1 - Why the last checkpoint is not the answer, at every window size at once.

THE QUESTION. Does the neuromodulated agent hide more selectively than the plain one? The measure
is the CONDITIONAL HIDING CONTRAST: the share of steps spent on the hiding bush when a predator is
in the world, MINUS the share when the world is empty. A large positive value means the agent
hides because of the threat rather than out of habit.

WHY A SWEEP RATHER THAN A NUMBER. Read at the final saved checkpoint, that contrast says the plain
agent is at -7.6 and the neuromodulated one at +52.8 -- a sixty-point gap, and a tidy story. Read
over the last twenty checkpoints the same two agents sit at 41.7 and 41.0. The endpoint is one draw
from a distribution whose checkpoint-to-checkpoint spread is four to ten times the sampling error of
the thirty episodes inside it, so it carries a story that is not there. Choosing some other single
window would only move the arbitrariness, so this figure refuses to choose: it plots the estimate at
every trailing window from one checkpoint to all fifty.

WHAT THE SHAPE MEANS. Widening the window is not simply more data. Variance falls roughly as one
over the square root of the window, but the window reaches further back into training, so bias grows
as a less-trained policy is averaged in. A real difference holds its sign and size across scales; an
endpoint artefact is large at the left edge and collapses; an effect that is still training drifts
steadily and never settles. The flat middle is the only region that is both converged and precise,
and it is what the page quotes.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
import _common as C
import window_profile as W
import house

house.apply()

dc = C.contrast(C.LVL04, "lvl04_control")
dm = C.contrast(C.LVL04, "lvl04_modulated")
pc, pm = W.window_profile(dc), W.window_profile(dm)
dif = W.difference_profile(dc, dm)

fig, ax = plt.subplots(1, 2, figsize=(10.0, 5.0))

# The window-2 interval spans about +-400 pp (a t interval on one degree of freedom). Drawn to
# scale it flattens every real feature into a horizontal line, so both panels are clipped to the
# range the data actually occupies and the off-scale intervals are named instead.
LEFT_YLIM, RIGHT_YLIM = (-22, 78), (-72, 38)

for prof, lab, col in ((pc, "plain agent", C.ARMC["control"]),
                       (pm, "neuromodulated agent", C.ARMC["modulated"])):
    m = prof["window"] >= 3
    ax[0].fill_between(prof["window"][m], prof["lo"][m], prof["hi"][m], color=col, alpha=0.18, lw=0)
    ax[0].plot(prof["window"], prof["mean"], color=col, lw=2.4, marker="o", ms=4.4, label=lab)
    ax[0].plot([1], [prof["mean"].iloc[0]], marker="o", ms=11, mfc="none", mec=col, mew=2.2)
ax[0].axhline(0, color=house.RULE, lw=1)
ax[0].set_ylim(*LEFT_YLIM)
ax[0].annotate("windows of 2 are omitted:\ntheir interval spans about \u00b1400",
               xy=(2.0, -16), fontsize=10, color=house.TEXT_LIGHT, ha="left", va="center")
ax[0].set_ylabel("conditional hiding contrast (pp)")
ax[0].set_title("Each agent, at every window size\n"
                "Ringed marker = the final-checkpoint reading. Bands are 95% intervals.",
                fontsize=10, color=house.INK_2, loc="left", pad=8)
house.legend_below(ax[0], ncol=2)

d = dif[dif["window"] >= 3]
ax[1].fill_between(d["window"], d["lo"], d["hi"], color=house.INK_2, alpha=0.16, lw=0)
ax[1].plot(dif["window"], dif["diff"], color=house.INK, lw=2.4, marker="o", ms=4.4)
# The reference line is chrome, not a category: RED is already the "endpoint artefact"
# label in this same panel.
ax[1].axhline(0, color=house.TEXT_LIGHT, lw=1.3, ls=(0, (4, 3)))
ax[1].plot([1], [dif["diff"].iloc[0]], marker="o", ms=11, mfc="none", mec=house.INK, mew=2.2)
ax[1].set_ylim(*RIGHT_YLIM)
for x, y, t, col, ha in ((1.25, -57, "endpoint\nartefact\n-60 pp", house.RED, "left"),
                         (4.6, 24, "plateau: no difference\n(p = 0.93 to 0.92)", house.GREEN, "left"),
                         (56.0, -41, "window has reached\ninto training\n-19 pp, p = 0.004",
                          house.INK_2, "right")):   # not ORANGE: that is the neuromodulated agent elsewhere
    ax[1].annotate(t, xy=(x, y), fontsize=10, color=col, ha=ha, va="center")
ax[1].set_ylabel("plain MINUS neuromodulated (pp)")
ax[1].set_title("The difference a claim would rest on\n"
                "Dashed grey line = no difference. Both ends deviate, for opposite reasons.",
                fontsize=10, color=house.INK_2, loc="left", pad=8)

for a in ax:
    a.set_xscale("log")
    a.set_xlim(0.88, 72)
    a.set_xticks([1, 2, 5, 10, 20, 50])
    a.set_xticklabels(["1", "2", "5", "10", "20", "50"])
    a.set_xlabel("trailing window (newest checkpoints averaged)")

C.record_samples("t01_window_profile", [
    dict(what="checkpoints per agent", used=len(dc), total=50,
         note="every saved checkpoint of both level-04 runs; the sweep wrote 50 of 50 with no "
              "failed cells"),
    dict(what="episodes behind each checkpoint", used=60, total=60,
         note="30 episodes with a predator and 30 with an empty world, per checkpoint, per agent"),
    dict(what="training runs", used=2, total=2,
         note="one plain and one neuromodulated run, both seed 42 \u2014 a single seed per arm, so the "
              "intervals describe these two runs and not the method")])

fig.tight_layout(w_pad=2.4)
C.assert_no_text_overlap(fig)
C.assert_min_text_px(fig)
house.save(fig, os.path.join(C.FIG, "t01_window_profile"), column_px=C.COLUMN_PX)
print("final %.1f | w10 %.1f p=%.3f | w20 %.1f p=%.3f | w50 %.1f p=%.3f" % (
    dif["diff"].iloc[0],
    dif[dif.window == 10]["diff"].iloc[0], dif[dif.window == 10]["p"].iloc[0],
    dif[dif.window == 20]["diff"].iloc[0], dif[dif.window == 20]["p"].iloc[0],
    dif[dif.window == 50]["diff"].iloc[0], dif[dif.window == 50]["p"].iloc[0]))
