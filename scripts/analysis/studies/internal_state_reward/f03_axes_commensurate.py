"""FIGURE 3 — do hunger, injury and cold weigh the same?

QUESTION. The drive adds three unlike things: fullness points, injury points and degrees. For
that sum to mean anything, a deviation that is equally serious on each axis has to contribute
equally. This figure checks that directly rather than trusting the intent.

WHY IT MATTERS. It is the test the 2026-09-22 change could most easily have broken. Moving the
fullness target to the middle halved how far fullness can stray from it, while the code's scale
factor still referred to the ceiling — which would have made one degree of cold count double.

HOW IT IS COMPUTED. For each fraction f from 0 to 1, one axis at a time is pushed f of the way
from its setpoint to the value at which the agent dies, with the other two held exactly at their
setpoints, and the live `calculate_drive` is called on the thermal world. Fullness is shown twice,
once in each direction, because it is the only axis with two lethal ends. If the axes are
commensurate all four traces lie on top of each other, so they are drawn in four different dash
patterns — a single visible line here is the RESULT, not a drawing fault.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
import _common as C
import house

STEM = "f03_axes_commensurate"
p = C.params_for("thermal")
assert p.thermal_enabled, "figure 3 needs the thermal world: it is the only one with three axes"
f = np.linspace(0, 1, 201)
sp, T0 = float(p.setpoint), float(p.temperature_setpoint)

# ONE INK, FOUR DASH PATTERNS. Spending four hues here would re-use colours that figures 1,
# 2, 4 and 5 have already given other meanings (register F11). The claim this figure makes is
# that the four traces COINCIDE, and a dash pattern carries identity for that on its own -- in
# fact better, because four colours on one line invite a reader to suspect a rendering fault.
INK = house.INK
traces = [
    ("fullness, falling  (toward starving)",  C.drive(sp - f * sp, 0.0, p, T0),                   (0, ())),
    ("fullness, rising  (toward overeating)", C.drive(sp + f * (p.max_satiation - sp), 0.0, p, T0), (0, (7, 4))),
    ("injury",                                C.drive(sp, f * p.max_injury, p, T0),                (0, (2, 3))),
    ("body temperature",                      C.drive(sp, 0.0, p, T0 + f * p.max_temperature),     (0, (9, 3, 2, 3))),
]

house.apply()
fig, ax = plt.subplots(figsize=(7.6, 4.6))
for lab, y, ls in traces:
    ax.plot(f, y, lw=2.2, ls=ls, color=INK, label=lab)
ax.plot([1.0], [100.0], marker="o", ms=7, color=INK, zorder=6)
# THE FIGURE MUST STATE ITS OWN RESULT. A reader who skips the caption sees one solid line
# under a legend promising three dashed ones, and the natural reading is "three curves are
# missing" -- the inverse of register F53. The endpoint value alone does not fix that, because
# it is a fact about the end of the line rather than about the overlap.
ax.annotate("FOUR traces are drawn here, one per axis.\nThey coincide exactly, so they read as"
            " one line —\nand all four reach 100.000, the penalty for dying.",
            xy=(1.0, 100), xytext=(0.04, 78), fontsize=house.FS_LABEL, color=house.INK_2)
ax.set_xlabel("how far the body has strayed from its target,\nas a fraction of the distance to death on that axis")
ax.set_ylabel("homeostatic drive, in satiation units")
ax.set_xlim(-0.02, 1.05); ax.set_ylim(-3, 112)
house.legend_below(ax, ncol=2, handlelength=3.4)

ends = {lab: float(y[-1]) for lab, y, _ in traces}
C.record_samples(STEM, [
    dict(what="deviation fractions evaluated per axis", used=len(f), total=len(f),
         note="0 to 1 in 201 steps, on the campfire world (basic/05) because it is the only "
              "maintained world whose drive has a third axis"),
    dict(what="axes compared", used=4, total=4,
         note="fullness in both directions, injury, body temperature - every axis the drive has")])
house.save(fig, os.path.join(C.FIG_ROOT, STEM))
for k, v in ends.items():
    print(f"  drive at full-scale deviation, {k:40} {v:7.3f}")
print(f"  death_penalty for comparison: {p.death_penalty}")
