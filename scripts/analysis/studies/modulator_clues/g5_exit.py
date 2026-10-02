"""FIGURE G5 — When does the agent leave cover? Bush-exit rate against the felt injury.

WHAT IS PLOTTED. Every step the agent spent in the bush with no animal within reach, in the no-animal
and wandering-rabbit scenes started at injury 0, 30, 60 and 90, pooled: the share of those steps after
which it was out of the bush, by the felt injury it had at the time (ten-point bins; bins with under
200 steps not drawn). An agent whose leaving waits on healing shows a rate that falls steeply as felt
injury rises. Newest 20 checkpoints; levels 05/06 pooled over the scene versions in the column. The
training-world twin of this measure is the bottom row of Figures G8-G9.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "basicq2_waves"))
import numpy as np, matplotlib.pyplot as plt
import _common as C, _inj as I, house

house.apply()
EDGES = np.arange(0, 101, 10); MIN = 200; xm = EDGES[:-1] + 5
fig, ax = plt.subplots(1, len(I.SCENE_COLS), figsize=(10.0, 3.9), sharey=True)
samples = []
for j, (lv, vers, title) in enumerate(I.SCENE_COLS):
    a = ax[j]
    for arm, alab, col in C.ARMS:
        ex, st = [], []
        for v in vers:
            z = I.steps_npz(v, f"{lv}_{arm}")
            if z is None:
                continue
            for sc in ("avoid_none", "avoid_rabbitwander"):
                for s0 in I.STARTS:
                    ex.append(z[f"{sc}_inj{s0:02d}__exits"]); st.append(z[f"{sc}_inj{s0:02d}__stays"])
        if not ex:
            continue
        ex, st = np.concatenate(ex), np.concatenate(st)
        ne = np.histogram(ex, EDGES)[0]; ns = np.histogram(st, EDGES)[0]; tot = ne + ns
        r = np.where(tot >= MIN, 100 * ne / np.maximum(tot, 1), np.nan)
        a.plot(xm, r, "-o", color=col, ms=3.5, lw=1.7, label=alab if j == 0 else None)
        samples.append(dict(what=f"{title.replace(chr(10), ' ')} {alab}: in-bush steps, no animal near",
                            used=int(tot[tot >= MIN].sum()), total=int(tot.sum()),
                            note=f"felt-injury bins with at least {MIN} steps drawn"))
    a.set_title(title, loc="left", fontsize=10, color=house.INK)
    a.set_xticks([0, 50, 100]); a.set_xlim(0, 100)
ax[0].set_ylabel("left the bush (%)")
fig.supxlabel("felt injury at the time (0-100)", y=0.14, fontsize=11)
fig.tight_layout(w_pad=0.5, rect=(0, 0.12, 1, 1))
C.legend_below(ax[0], ncol=2, offset=-0.42)
C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)
C.record_kind("g5_exit", "scene")
C.record_samples("g5_exit", samples)
house.save(fig, os.path.join(C.FIG, "g5_exit"), column_px=C.COLUMN_PX)
