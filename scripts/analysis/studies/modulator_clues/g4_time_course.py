"""FIGURE G4 — Within an episode: how long injured hiding lasts, and what the agent feels meanwhile.

WHAT IS PLOTTED. The no-animal scene, started at injury 0, 30, 60 or 90 (light to dark). Top two rows:
share of episodes in the bush at each step, ordinary agent then neuromodulated agent. Bottom row: the
felt injury the agent receives (the interoceptive signal, 0-100) after a start at 90 — it builds over
the first few steps, then falls as the agent heals, which is fast while resting in cover. Newest 20
checkpoints; in this scene nothing is random, so each checkpoint contributes one distinct episode.
Levels 05/06: mean over the scene versions in the column.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "basicq2_waves"))
import numpy as np, matplotlib.pyplot as plt
from matplotlib.colors import to_rgb
import _common as C, _inj as I, house

house.apply()
T = 61; t = np.arange(T)
fig, ax = plt.subplots(3, len(I.SCENE_COLS), figsize=(10.0, 6.6), sharex=True, sharey="row")
samples = []


def shade(col, k):
    c = np.array(to_rgb(col)); return tuple(1 - (1 - c) * (0.35 + 0.65 * k / 3))


for j, (lv, vers, title) in enumerate(I.SCENE_COLS):
    for r, (arm, alab, col) in enumerate(C.ARMS):
        a = ax[r, j]
        for k, s0 in enumerate(I.STARTS):
            y, n = I.steps_mean(vers, f"{lv}_{arm}", f"avoid_none_inj{s0:02d}__bush")
            if y is not None:
                a.plot(t, 100 * y[:T], color=shade(col, k), lw=1.6,
                       label=f"start {s0}" if (j == 0 and r == 0) else None)
        y, n = I.steps_mean(vers, f"{lv}_{arm}", "avoid_none_inj90__felt")
        if y is not None:
            ax[2, j].plot(t, y[:T], color=col, lw=1.6, label=alab if j == 0 else None)
        samples.append(dict(what=f"{title.replace(chr(10), ' ')} {alab}", used=n, total=len(vers),
                            note="scene versions summarised (newest 20 checkpoints each)"))
    ax[0, j].set_title(title, loc="left", fontsize=10, color=house.INK)
    ax[2, j].set_xticks([0, 30, 60])
    for r in range(3):
        ax[r, j].set_ylim(0, 100); ax[r, j].set_yticks([0, 50, 100])
ax[0, 0].set_ylabel("ordinary\n% in bush"); ax[1, 0].set_ylabel("neuromodulated\n% in bush")
ax[2, 0].set_ylabel("felt injury\n(start 90)")
fig.supxlabel("step of the episode", y=0.12, fontsize=11)
fig.tight_layout(h_pad=0.8, w_pad=0.5, rect=(0, 0.1, 1, 1))
h0, l0 = ax[0, 0].get_legend_handles_labels(); h2, l2 = ax[2, 0].get_legend_handles_labels()
leg = fig.legend(h0 + h2, l0 + l2, loc="lower center", ncol=6, frameon=False, bbox_to_anchor=(0.5, 0.0))
C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)
C.record_kind("g4_time_course", "scene")
C.record_samples("g4_time_course", samples)
house.save(fig, os.path.join(C.FIG, "g4_time_course"), column_px=C.COLUMN_PX)
