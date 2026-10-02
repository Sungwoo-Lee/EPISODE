"""FIGURE 1 — Every number the 2026-09-22 analysis reported, beside what it becomes when measured properly.

WHY IT IS HERE. The earlier analysis read each scene's hiding off the final saved checkpoint. This
figure puts that reading (hollow ring) next to the mean of the last 20 checkpoints (filled dot) for
every test scene and both agents, so the correction is visible scene by scene rather than asserted.
A line joins the two readings of the same scene: the longer the line, the more the endpoint misled.

WHAT TO READ FROM IT. For the ordinary agent the rings sit far to the right of the dots in the calm
scenes -- the final checkpoint happened to be one of its most bush-bound, which is what produced
"this agent is parked in a bush". For the neuromodulated agent ring and dot mostly sit close together.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
import _common as C, house

house.apply()
SCENES = [("avoid_none_inj00", "nothing"),
          ("avoid_none_inj70", "nothing, agent injured"),
          ("avoid_rabbit_olfzero_inj00", "rabbit chasing, smell off"),
          ("avoid_rabbitwander_inj00", "rabbit wandering"),
          ("avoid_rabbitwander_predsmell_inj00", "rabbit wandering + predator smell"),
          ("avoid_rabbit_inj00", "rabbit chasing"),
          ("avoid_pred_inj00", "predator"),
          ("avoid_pred_inj70", "predator, agent injured")]
fig, ax = plt.subplots(1, 2, figsize=(10.0, 5.6), sharey=True)
y = np.arange(len(SCENES))[::-1]
for p, (run, lab, col) in enumerate(C.ARMS):
    for yi, (cond, _) in zip(y, SCENES):
        f, m, lo, hi, _n = C.windowed(C.W2, run, cond)
        ax[p].plot([lo, hi], [yi, yi], color=col, lw=5, alpha=0.22, solid_capstyle="butt", zorder=1)
        ax[p].plot([f, m], [yi, yi], color=house.INK_2, lw=1.2, zorder=2)
        ax[p].plot([m], [yi], "o", ms=8, color=col, zorder=3)
        ax[p].plot([f], [yi], "o", ms=9, mfc="none", mec=house.INK, mew=1.8, zorder=4)
    ax[p].set_xlim(0, 100)
    ax[p].set_title(lab, fontsize=10.5, color=col, loc="left", pad=8)
    ax[p].set_xlabel("steps on the hiding bush (%)")
    ax[p].grid(axis="y", visible=False)
ax[0].set_yticks(y); ax[0].set_yticklabels([s for _, s in SCENES], fontsize=10)
ax[0].plot([], [], "o", ms=9, mfc="none", mec=house.INK, mew=1.8, label="final checkpoint (as reported)")
ax[0].plot([], [], "o", ms=8, color=house.INK_2, label="mean of the last 20 (this page)")
C.legend_below(ax[0], ncol=2, offset=-0.16)
fig.suptitle("The same eight scenes read two ways. Shaded bar = 95% interval across the last 20 checkpoints.",
             fontsize=10, color=house.INK_2, x=0.005, ha="left", y=0.995, va="top")
C.record_samples("l02_endpoint_vs_window", [
    dict(what="test scenes", used=len(SCENES), total=12,
         note="every scene the earlier analysis quoted, plus the injured and smell-silenced variants; "
              "the four remaining are injured copies of the rabbit scenes"),
    dict(what="checkpoints behind each filled dot", used=C.WIN, total=50,
         note="the newest 20; the hollow ring is the single newest"),
    dict(what="episodes per checkpoint", used=30, total=30, note="fixed seeds shared by both agents"),
    dict(what="training runs", used=2, total=2, note="one seed each")])
fig.tight_layout(w_pad=1.6, rect=(0, 0, 1, 0.965))
# Guards AFTER layout: run before it, they inspect a layout that is never saved.
C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)
house.save(fig, os.path.join(C.FIG, "l02_endpoint_vs_window"), column_px=C.COLUMN_PX)
