"""FIGURE G1 — In controlled scenes, time in the bush against the starting injury, 0 to 90.

WHAT IS PLOTTED. Three fixed scenes (nothing, a predator, a wandering rabbit), each started at
injury 0, 10, ... 90, replayed at every saved checkpoint for 30 seeded episodes. Value = mean over the
newest 20 checkpoints. Levels 02-04: one scene version, band = +-1 SD across those checkpoints.
Levels 05/06: four survivable temperature versions; line = median of the four, band = their range.
Level 06 appears twice: without and with its injury-driven sensory noise. Predator-scene points where
the agent dies before step 100 on average are drawn hollow: there, time in the bush is a share of a
shortened life.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "basicq2_waves"))
import numpy as np, matplotlib.pyplot as plt
import _common as C, _inj as I, house

house.apply()
fig, ax = plt.subplots(len(I.SCENES), len(I.SCENE_COLS), figsize=(10.0, 6.8), sharex=True, sharey=True)
x = np.array(I.INJ); samples = []
for j, (lv, vers, title) in enumerate(I.SCENE_COLS):
    for i, (scene, sname) in enumerate(I.SCENES):
        a = ax[i, j]
        for arm, alab, col in C.ARMS:
            lab = f"{lv}_{arm}"
            m, lo, hi = I.dose_curve(vers, lab, scene)
            if np.all(np.isnan(m)):
                continue
            a.fill_between(x, lo, hi, color=col, alpha=0.18, lw=0)
            a.plot(x, m, "-", color=col, lw=1.8, label=alab if (i == ax.shape[0] - 1 and j == 0) else None)
            surv, _, _ = I.dose_curve(vers, lab, scene, "survival_steps")
            full = surv >= 100
            a.plot(x[full], m[full], "o", color=col, ms=3.6)
            a.plot(x[~full], m[~full], "o", mfc="white", mec=col, ms=4.2, mew=1.2)
        a.set_ylim(0, 100); a.set_yticks([0, 50, 100])
        if j == 0:
            a.set_ylabel(f"{sname}\n% in bush")
        if i == 0:
            a.set_title(title, loc="left", fontsize=10, color=house.INK)
        if i == len(I.SCENES) - 1:
            a.set_xlabel("starting injury"); a.set_xticks([0, 90])
    for arm, alab, _ in C.ARMS:
        n = sum(I.window_mean(v, f"{lv}_{arm}", s, i)[2] for v in vers for s, _ in I.SCENES for i in I.INJ)
        samples.append(dict(what=f"{title.replace(chr(10), ' ')} {alab}: checkpoint x condition cells",
                            used=n, total=len(vers) * len(I.SCENES) * len(I.INJ) * I.LAST,
                            note=f"newest {I.LAST} checkpoints x 30 episodes; {len(vers)} scene version(s)"))
fig.tight_layout(h_pad=0.8, w_pad=0.5)
C.legend_below(ax[-1, 0], ncol=2, offset=-0.5)
fig.tight_layout(h_pad=0.8, w_pad=0.5)
C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)
C.record_kind("g1_scene_dose", "scene")
C.record_samples("g1_scene_dose", samples)
house.save(fig, os.path.join(C.FIG, "g1_scene_dose"), column_px=C.COLUMN_PX)
