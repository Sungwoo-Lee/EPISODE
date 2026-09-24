"""FIGURE G7 — What the felt-injury manipulation does to the agent's memory.

WHAT IS PLOTTED. The sustained manipulation of Figure G6, no-animal scene. The agent's decisions pass
through a recurrent memory (a GRU), and the modulator has a memory of its own. A shadow copy of the
network is fed the true inputs along the same path, so its memory is the one the agent would have had.
Top: how far the manipulated memory sits from that natural memory, as a fraction of the natural
memory's size, averaged over the episode (solid: the agent's main memory; dotted, modulated agent
only: the modulator's memory). Bottom: the share of memory units outside the range they ever take
naturally in these episodes — how far the manipulation pushes the memory off its usual ground.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "basicq2_waves"))
import numpy as np, matplotlib.pyplot as plt
import _common as C, _inj as I, house

house.apply()
x = np.array(I.LADDER) * 100
ROWS = [(("d_task_mean", "d_mod_mean"), "memory moved\n(fraction of size)"),
        (("out_of_range_task", "out_of_range_mod"), "units outside\nnatural range (%)")]
fig, ax = plt.subplots(len(ROWS), len(I.MANIP_COLS), figsize=(10.0, 5.0), sharex=True, sharey="row")
samples = []
for j, (lv, vers, title) in enumerate(I.MANIP_COLS):
    for i, ((mt, mm), yl) in enumerate(ROWS):
        a = ax[i, j]; sc = 100 if i == 1 else 1
        for arm, alab, col in C.ARMS:
            y, n = I.manip_curve(vers, f"{lv}_{arm}", "avoid_none_inj00", "ladder_sustained", mt)
            if y is None:
                continue
            a.plot(x, sc * y, "-", color=col, lw=1.7, label=f"{alab}, main memory" if (i == 0 and j == 0) else None)
            if arm == "modulated":
                ym, _ = I.manip_curve(vers, f"{lv}_{arm}", "avoid_none_inj00", "ladder_sustained", mm)
                a.plot(x, sc * ym, ":", color=col, lw=1.9,
                       label="neuromodulated agent, modulator memory" if (i == 0 and j == 0) else None)
            if i == 0:
                samples.append(dict(what=f"{title.replace(chr(10), ' ')} {alab}", used=n, total=len(vers),
                                    note="scene versions finished (x 20 checkpoints x 30 episodes x 10 values)"))
        if j == 0:
            a.set_ylabel(yl)
        if i == 0:
            a.set_title(title, loc="left", fontsize=10, color=house.INK)
        if i == len(ROWS) - 1:
            a.set_xticks([0, 50, 90])
for a in ax[1]:
    a.set_ylim(0, 60)
for a in ax[0]:
    a.set_ylim(0, 2.6)
fig.supxlabel("felt injury given", y=0.12, fontsize=11)
fig.tight_layout(h_pad=0.8, w_pad=0.5, rect=(0, 0.11, 1, 1))
h, l = ax[0, 0].get_legend_handles_labels()
fig.legend(h, l, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 0.0), fontsize=10)
C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)
C.record_kind("g7_memory", "manipulation")
C.record_samples("g7_memory", samples)
house.save(fig, os.path.join(C.FIG, "g7_memory"), column_px=C.COLUMN_PX)
