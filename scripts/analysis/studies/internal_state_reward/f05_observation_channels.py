"""FIGURE 5 — what the agent actually receives, which is not what the drive uses.

QUESTION. The drive is computed in raw body units, but the agent never sees those. It sees each
body channel divided by that channel's ceiling, so everything arrives on a 0-to-1 scale. What does
the fullness channel look like after the ceiling doubled?

WHY IT MATTERS. Two things change at once and only one of them is obvious. The obvious one: the
same fullness now reports HALF the value it used to, so a checkpoint trained before the change
loads without complaint and reads a different problem. The subtle one: the value the agent should
aim for moved from the top of the channel to its middle. "Push this number up" was a winning policy
before and is a losing one now, and nothing in the observation says so — the agent has to learn it.

HOW IT IS COMPUTED. Every curve is the live `sensor.py` expression `state.satiation / max_satiation`
evaluated on the resolved `EnvParams`, once for the shipped world and once for the same world with
the three body keys overridden back to their pre-2026-09-22 values. Fullness is swept over each
world's own reachable range. The injury channel is drawn for contrast: it is unchanged, and its
target has always been at the bottom of its range rather than the top.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
import _common as C
import house

STEM = "f05_observation_channels"
new = C.params_for("10x10")
old = C.params_for("10x10", max_nutrition=100, max_satiation=100, satiation_setpoint=100,
                   start_nutrition_high=100)

n_new = np.arange(0, new.max_nutrition + 1, 1.0)
n_old = np.arange(0, old.max_nutrition + 1, 1.0)
ch_new = C.satiation_of(n_new, new) / new.max_satiation
ch_old = C.satiation_of(n_old, old) / old.max_satiation

house.apply()
fig, ax = plt.subplots(figsize=(7.6, 4.6))
ax.plot(n_old, ch_old, lw=7.0, color=house.ORANGE, alpha=0.30, solid_capstyle="butt",
        label="before — full scale reached at fullness 100")
ax.plot(n_new, ch_new, lw=2.6, color=house.BLUE,
        label="after — full scale reached at fullness 200")
ax.axhline(new.setpoint / new.max_satiation, color=house.INK_2, lw=1.0, ls=(0, (4, 3)))
ax.plot([new.setpoint], [new.setpoint / new.max_satiation], marker="o", ms=6.5,
        color=house.BLUE, zorder=5)
ax.annotate("the value to aim for is now 0.5,\nnot 1.0", xy=(100, 0.5), xytext=(108, 0.30),
            fontsize=house.FS_LABEL, color=house.INK)
ax.set_xlabel("the agent's fullness (nutrition), in nutrition points")
ax.set_ylabel("the fullness channel as the agent receives it,\n0 to 1")
ax.set_xlim(-5, 205); ax.set_ylim(-0.03, 1.08)
house.legend_below(ax, ncol=1)

C.record_samples(STEM, [
    dict(what="fullness values evaluated, shipped world", used=len(n_new), total=len(n_new),
         note="every whole nutrition point over the reachable range 0-200, through the live "
              "sensor expression rather than a re-derivation of it"),
    dict(what="fullness values evaluated, pre-change world", used=len(n_old), total=len(n_old),
         note="the same sweep over the old range 0-100, resolved by overriding the body keys")])
house.save(fig, os.path.join(C.FIG_ROOT, STEM))
print(f"  channel at fullness 100: before {ch_old[100]:.3f}   after {ch_new[100]:.3f}")
