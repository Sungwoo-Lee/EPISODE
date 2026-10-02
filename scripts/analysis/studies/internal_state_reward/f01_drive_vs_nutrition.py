"""FIGURE 1 — the shape of the problem, before and after.

QUESTION. The homeostatic drive is one number: how far the body is from where it wants to be.
Reward is how much that number shrank this step. So the drive's SHAPE against fullness is the
whole task, and on 2026-09-22 that shape changed from a ramp into a valley.

WHY IT MATTERS. Under the old shape the best thing an agent could do with food was eat all of it:
the drive fell monotonically all the way to the ceiling, which was also the target. Under the new
shape there is a single best fullness in the middle, and both directions away from it are punished
symmetrically. That is what makes this an internal-state REGULATION problem rather than a
maximisation one.

HOW IT IS COMPUTED. Both curves come from the live `calculate_drive`, called with injury fixed at
zero and thermal off, so the only live axis is fullness. The OLD curve is produced by resolving the
same world with `max_nutrition`/`max_satiation` overridden back to 100 and the setpoint left at 100
— i.e. the world as it shipped before the change — rather than by re-deriving a formula. Fullness
is swept across the whole reachable range of each world at 1-unit steps.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
import _common as C
import house

STEM = "f01_drive_vs_nutrition"

new = C.params_for("10x10")
old = C.params_for("10x10", max_nutrition=100, max_satiation=100, satiation_setpoint=100,
                   start_nutrition_high=100)   # the guard added 2026-09-22 rejects a start range
                                               # wider than the ceiling, so the old world must be
                                               # restored consistently, not one key at a time.

n_new = np.arange(0, new.max_nutrition + 1, 1.0)
n_old = np.arange(0, old.max_nutrition + 1, 1.0)
d_new = C.drive(C.satiation_of(n_new, new), 0.0, new)
d_old = C.drive(C.satiation_of(n_old, old), 0.0, old)

# THE TWO CURVES COINCIDE BELOW 100, and that is the point of the figure rather than a
# drawing problem. In both worlds satiation equals nutrition and the target is 100, so the
# left arm is the SAME line; what changed is that the old world simply STOPPED at 100 --
# its ceiling was its target -- while the new one carries on to 200 with a second death at
# the far end. Drawn as a thick pale underlay so the shared arm is visible rather than
# hidden under the blue, which would leave the legend promising a line the plot never shows.
house.apply()
fig, ax = plt.subplots(figsize=(7.6, 4.6))
ax.plot(n_old, d_old, lw=7.0, color=house.ORANGE, alpha=0.30, solid_capstyle="butt",
        label="before — the world ended at 100")
ax.plot(n_new, d_new, lw=2.6, color=house.BLUE, label="after — 0 to 200, target at 100")
ax.axvline(new.setpoint, color=house.INK_2, lw=1.0, ls=(0, (4, 3)))
ax.plot([new.setpoint], [0.0], marker="o", ms=6.5, color=house.BLUE, zorder=5)
ax.annotate("target: drive 0", xy=(new.setpoint, 0), xytext=(new.setpoint + 9, 11),
            fontsize=house.FS_LABEL, color=house.INK)
# NO on-figure note about the shared left arm. Two placements were tried -- beside the
# right arm (sat on the blue line, register F33 amendment) and inside the V (crossed the
# left arm, three lines being wider than the wedge). The point is interpretation, so it
# lives in the caption, where the guide puts interpretation anyway.
for x, lab, dx in ((0, "starves", 6), (new.max_nutrition, "overeats", -44)):
    ax.plot([x], [100], marker="X", ms=8, color=house.RED, zorder=5)
    ax.annotate(lab, xy=(x, 100), xytext=(x + dx, 90),
                fontsize=house.FS_LABEL, color=house.RED)
ax.set_xlabel("the agent's fullness (nutrition), in nutrition points")
ax.set_ylabel("homeostatic drive, in satiation units")
ax.set_xlim(-5, 205); ax.set_ylim(-5, 114)
house.legend_below(ax, ncol=2)

C.record_samples(STEM, [
    dict(what="fullness values swept, new world", used=len(n_new), total=len(n_new),
         note="every whole nutrition point in the reachable range 0-200; analytic sweep through "
              "the live calculate_drive, not sampled from episodes"),
    dict(what="fullness values swept, pre-change world", used=len(n_old), total=len(n_old),
         note="the same sweep over the old reachable range 0-100, resolved by overriding the "
              "three body keys back to their pre-2026-09-22 values")])
house.save(fig, os.path.join(C.FIG_ROOT, STEM))
print(f"  drive at target = {C.drive(C.satiation_of(100, new), 0.0, new)[0]:.3f}")
print(f"  drive at 50 / 150 = {C.drive(C.satiation_of([50,150], new), 0.0, new)}")
