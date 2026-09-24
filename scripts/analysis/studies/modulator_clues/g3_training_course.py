"""FIGURE G3 — When during training does hiding start to follow injury, and how steadily?

WHAT IS PLOTTED. The slope of time-in-bush on starting injury (points per 10 injury, the G2 measure)
in the no-animal and wandering-rabbit scenes, at every one of the 50 saved checkpoints, against
training steps. Levels 05/06: median over the four temperature versions at each checkpoint. The
wobble of a line is how much that agent's injury dependence changes from one checkpoint to the next —
the steadiness the page reads as a clue.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "basicq2_waves"))
import numpy as np, matplotlib.pyplot as plt
import _common as C, _inj as I, house

house.apply()
SC = [("avoid_none", "no animal"), ("avoid_rabbitwander", "wandering rabbit")]
fig, ax = plt.subplots(len(SC), len(I.SCENE_COLS), figsize=(10.0, 5.4), sharex=True, sharey="row")
samples = []
for j, (lv, vers, title) in enumerate(I.SCENE_COLS):
    for i, (scene, sname) in enumerate(SC):
        a = ax[i, j]
        for arm, alab, col in C.ARMS:
            ser = [I.slope_series(v, f"{lv}_{arm}", scene) for v in vers]
            ser = [s for s in ser if s[0] is not None]
            if not ser:
                continue
            n = min(len(s[0]) for s in ser)
            steps = ser[0][0][:n] / 1e6
            y = np.median(np.array([s[1][:n] for s in ser]), 0)
            a.plot(steps, y, "-", color=col, lw=1.5, label=alab if (i == ax.shape[0] - 1 and j == 0) else None)
            if i == 0:
                samples.append(dict(what=f"{title.replace(chr(10), ' ')} {alab}", used=n, total=50,
                                    note=f"checkpoints with all ten injury levels; {len(ser)} scene version(s)"))
        a.axhline(0, color=house.INK, lw=0.8)
        if j == 0:
            a.set_ylabel(f"{sname}\nslope (pts / 10 injury)")
        if i == 0:
            a.set_title(title, loc="left", fontsize=10, color=house.INK)
        if i == len(SC) - 1:
            a.set_xlabel("training steps (M)"); a.set_xticks([0, 5, 10])
fig.tight_layout(h_pad=0.8, w_pad=0.5)
C.legend_below(ax[-1, 0], ncol=2, offset=-0.55)
fig.tight_layout(h_pad=0.8, w_pad=0.5)
C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)
C.record_kind("g3_training_course", "scene")
C.record_samples("g3_training_course", samples)
house.save(fig, os.path.join(C.FIG, "g3_training_course"), column_px=C.COLUMN_PX)
