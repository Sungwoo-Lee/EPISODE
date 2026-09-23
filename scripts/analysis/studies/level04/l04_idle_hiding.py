"""FIGURE 4 — What each agent does in an empty scene, across the whole of training, in both worlds.

WHAT IS PLOTTED. The empty test scene: one bush three squares away, full stomach, no animal, no
food. Hiding here cannot be a response to anything, so it is the clearest view of an agent's habit.
Each point is one saved checkpoint (30 episodes); the shaded band marks the last 20, which the rest
of the page averages. Because there is no animal, the bush's permeability cannot matter, so the
first world's sweep -- run before the bush was fixed -- is valid here and here only.

WHAT TO READ FROM IT. In the first world (left) both agents rarely sit in the empty bush. In the
world where cover heals (right) the ordinary agent swings between rarely and almost always from one
checkpoint to the next, while the neuromodulated agent stays low. This is the one place the two
agents part company -- and Figure 3 shows that in the training world, with food and animals present,
they do not.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
import _common as C, house

house.apply()
fig, ax = plt.subplots(1, 2, figsize=(10.0, 5.0), sharey=True)
for p, (O, title) in enumerate(((C.W1, "first world"), (C.W2, "second world"))):
    for run, lab, col in C.ARMS:
        st, v = C.W.read_series(O, run, "avoid_none_inj00")
        ax[p].plot(st / 1e6, v, color=col, lw=1.6, marker="o", ms=3, label=lab)
        m = C.windowed(O, run, "avoid_none_inj00")[1]
        ax[p].plot([st[-C.WIN] / 1e6, st[-1] / 1e6], [m, m], color=col, lw=3.2, alpha=0.9, zorder=4)
    ax[p].axvspan(st[-C.WIN] / 1e6, st[-1] / 1e6, color=house.INK_2, alpha=0.07, lw=0)
    ax[p].set_title(title, fontsize=10.5, color=house.INK, loc="left", pad=8)
    ax[p].set_xlabel("training progress (millions of steps)")
    ax[p].set_xlim(-0.3, 10.6)
ax[0].set_ylim(-3, 103)
ax[0].set_ylabel("steps on the bush, empty scene (%)")
C.legend_below(ax[0], ncol=2, offset=-0.20)
fig.suptitle("Thick bar = mean of the last 20 checkpoints (shaded). Thin line = every checkpoint.",
             fontsize=10, color=house.INK_2, x=0.005, ha="left", y=0.995, va="top")
C.record_samples("l04_idle_hiding", [
    dict(what="checkpoints per line", used=50, total=50, note="every saved checkpoint, both worlds"),
    dict(what="episodes per checkpoint", used=30, total=30, note="fixed seeds"),
    dict(what="test scenes", used=1, total=12,
         note="the empty scene only — the one where the first world's permeable bush cannot matter"),
    dict(what="training runs", used=4, total=4, note="ordinary and neuromodulated in each world, one seed each")])
fig.tight_layout(w_pad=1.8, rect=(0, 0, 1, 0.965))
# Guards AFTER layout: run before it, they inspect a layout that is never saved.
C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)
house.save(fig, os.path.join(C.FIG, "l04_idle_hiding"), column_px=C.COLUMN_PX)
