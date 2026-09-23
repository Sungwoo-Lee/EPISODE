"""FIGURE 2 - The level-04 series the endpoint was read from.

WHY IT IS HERE. Figure 1 shows that averaging changes the answer. This one shows WHY, by drawing
the raw series the endpoint was taken from. Each point is one saved checkpoint: the share of an
episode's steps the agent spent sitting on the hiding bush, averaged over thirty episodes. The
right-hand marker is the final checkpoint -- the number an earlier analysis reported.

WHAT TO LOOK FOR. In the empty world the plain agent's final checkpoint sits at 86%, which was read
as "this agent is simply parked in a bush". Its ten preceding checkpoints average 24% and range from
4% to 86%: the endpoint is the MAXIMUM of its own neighbourhood, not a typical value. The shaded
band marks the last twenty checkpoints, the window the page quotes.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
import _common as C, window_profile as W, house
house.apply()

fig, ax = plt.subplots(1, 2, figsize=(12.0, 5.0), sharey=True)
for j, (cond, cname) in enumerate([(C.NONE, "empty world (no animal)"),
                                   (C.PRED, "a hunting predator is present")]):
    for run, lab in [("lvl04_control", "plain agent"), ("lvl04_modulated", "neuromodulated agent")]:
        st, v = W.read_series(C.LVL04, run, cond)
        col = C.ARMC["control" if "t1none" in run or "control" in run else "modulated"]
        ax[j].plot(st / 1e6, v, color=col, lw=1.7, marker="o", ms=3.2, alpha=0.95, label=lab)
        ax[j].plot([st[-1] / 1e6], [v[-1]], marker="o", ms=11, mfc="none", mec=col, mew=2.2)
    ax[j].axvspan(st[-20] / 1e6, st[-1] / 1e6, color=house.INK_2, alpha=0.07, lw=0)
    ax[j].set_title(cname, fontsize=10, color=house.INK, loc="left", pad=8)
    ax[j].set_xlabel("training progress (millions of environment steps)")
ax[0].set_ylabel("steps spent on the hiding bush (%)")
ax[0].annotate("shaded = the last 20 checkpoints,\nthe window quoted on this page",
               xy=(4.2, 92), fontsize=8.5, color=house.TEXT_LIGHT, ha="left", va="top")
ax[0].annotate("final checkpoint: 86%\nprevious ten average 24%",
               xy=(9.9, 78), fontsize=8.5, color=house.RED, ha="right", va="top")
house.legend_below(ax[0], ncol=2)
C.record_samples("t02_checkpoint_trace", [
    dict(what="checkpoints drawn", used=100, total=100,
         note="50 per agent x 2 agents, both probe conditions; the sweep wrote every one"),
    dict(what="episodes per point", used=30, total=30,
         note="30 evaluation episodes at fixed seeds behind each plotted marker"),
    dict(what="training runs", used=2, total=2, note="one seed per arm -- descriptive only")])
fig.tight_layout(w_pad=2.2)
house.save(fig, os.path.join(C.FIG, "t02_checkpoint_trace"))
print("done t02")
