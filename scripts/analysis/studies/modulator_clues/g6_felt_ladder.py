"""FIGURE G6 — Observation manipulation: an unhurt agent made to FEEL injured.

WHAT IS PLOTTED. Each scene is started uninjured. The only change is the felt-injury input the network
receives, held at 0, 0.1, ... 0.9 (drawn on the injury scale, 0-90) from the first step; the world,
the true injury and everything else the agent senses are untouched. Solid lines: the manipulated input
also flows through the agent's memory (sustained). Dashed: at each step the agent acts from the memory
it would have had without manipulation, so only that step's input is changed (one step). Value = time
in the bush, mean over 30 seeded episodes and the newest 20 checkpoints; levels 05/06, median over the
scene versions in the column. Compare with Figure G1, where the injury was real.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "basicq2_waves"))
import numpy as np, matplotlib.pyplot as plt
import _common as C, _inj as I, house

house.apply()
x = np.array(I.LADDER) * 100
fig, ax = plt.subplots(len(I.SCENES), len(I.MANIP_COLS), figsize=(10.0, 6.8), sharex=True, sharey=True)
samples = []
for j, (lv, vers, title) in enumerate(I.MANIP_COLS):
    for i, (scene, sname) in enumerate(I.SCENES):
        a = ax[i, j]
        for arm, alab, col in C.ARMS:
            for job, ls in (("ladder_sustained", "-"), ("ladder_one_step", "--")):
                y, n = I.manip_curve(vers, f"{lv}_{arm}", f"{scene}_inj00", job, "bush_hiding")
                if y is None:
                    continue
                a.plot(x, 100 * y, ls, color=col, lw=1.7 if ls == "-" else 1.3,
                       label=(f"{alab}, {'sustained' if ls == '-' else 'one step'}") if (i == ax.shape[0] - 1 and j == 0) else None)
                if i == 0:
                    samples.append(dict(what=f"{title.replace(chr(10), ' ')} {alab} {job.split('_', 1)[1]}",
                                        used=n * len(I.SCENES), total=len(vers) * len(I.SCENES),
                                        note="scene versions finished (x 20 checkpoints x 30 episodes x 10 values)"))
        a.set_ylim(0, 100); a.set_yticks([0, 50, 100])
        if j == 0:
            a.set_ylabel(f"{sname}\n% in bush")
        if i == 0:
            a.set_title(title, loc="left", fontsize=10, color=house.INK)
        if i == len(I.SCENES) - 1:
            a.set_xlabel("felt injury given"); a.set_xticks([0, 50, 90])
fig.tight_layout(h_pad=0.8, w_pad=0.5)
C.legend_below(ax[-1, 0], ncol=2, offset=-0.55)
fig.tight_layout(h_pad=0.8, w_pad=0.5)
C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)
C.record_kind("g6_felt_ladder", "manipulation")
C.record_samples("g6_felt_ladder", samples)
house.save(fig, os.path.join(C.FIG, "g6_felt_ladder"), column_px=C.COLUMN_PX)
