"""FIGURE 2 — How much each agent hides, from an empty scene up to a hunting predator.

WHAT IS PLOTTED. The share of an episode's steps the agent spends on the hiding bush in five fixed
test scenes, ordered by how threatening they are. Each point is the mean over the last 20 saved
checkpoints of one training run, with a 95% interval describing how much that run's behaviour moves
between those checkpoints. The bush blocks animals, as it did in training.

WHAT TO READ FROM IT. Both lines climb in the same order: neither agent treats a wandering rabbit as
a threat, both hide more from a chasing one, and both hide most from a predator. The ordinary agent's
line sits higher throughout, including in the empty scene, where nothing is there to hide from.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
import _common as C, house

house.apply()
fig, ax = plt.subplots(figsize=(10.0, 5.4))
x = np.arange(len(C.THREATS))
for k, (run, lab, col) in enumerate(C.ARMS):
    rows = [C.windowed(C.W2, run, c) for c, _ in C.THREATS]
    m = np.array([r[1] for r in rows]); lo = np.array([r[2] for r in rows]); hi = np.array([r[3] for r in rows])
    xs = x + (k - 0.5) * 0.12
    ax.fill_between(xs, lo, hi, color=col, alpha=0.14, lw=0)
    ax.plot(xs, m, color=col, lw=2.4, marker="o", ms=6, label=lab)
    ax.errorbar(xs, m, yerr=[m - lo, hi - m], fmt="none", ecolor=col, elinewidth=1.3, capsize=3.2)
ax.set_xticks(x); ax.set_xticklabels([t for _, t in C.THREATS], fontsize=10)
ax.set_ylim(0, 100)
ax.set_ylabel("steps spent on the hiding bush (%)")
ax.set_xlabel("what is in the test scene, least to most threatening")
fig.suptitle("Both agents hide more as the threat grows; the ordinary agent hides more throughout.",
             fontsize=10, color=house.INK_2, x=0.005, ha="left", y=0.995, va="top")
C.legend_below(ax, ncol=2, offset=-0.24)
C.record_samples("l01_threat_ladder", [
    dict(what="checkpoints per point", used=C.WIN, total=50,
         note="the newest 20 of 50; older ones average in a less-trained agent"),
    dict(what="episodes per checkpoint", used=30, total=30,
         note="fixed seeds, so both agents meet identical scenes"),
    dict(what="test scenes shown", used=5, total=12,
         note="the uninjured scenes ordered by threat; the injured and smell-silenced variants are "
              "in Figure 1"),
    dict(what="training runs", used=2, total=2,
         note="one ordinary and one neuromodulated run, one seed each")])
fig.tight_layout(rect=(0, 0, 1, 0.965))
# Guards AFTER layout: run before it, they inspect a layout that is never saved.
C.assert_ticks_dont_collide(ax); C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)
house.save(fig, os.path.join(C.FIG, "l01_threat_ladder"), column_px=C.COLUMN_PX)
