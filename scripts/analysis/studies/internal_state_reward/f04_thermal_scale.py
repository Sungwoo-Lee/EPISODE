"""FIGURE 4 — the bug the change would have introduced, if the scale had not been fixed.

QUESTION. Temperature is measured in degrees and fullness in satiation points, so the drive has
to convert one into the other. What should one degree of cold be worth?

WHY IT MATTERS. The conversion used to be written as `max_satiation / max_temperature`. That was
right only by coincidence: while the fullness target sat AT the ceiling, "the ceiling" and "the
furthest fullness can stray from its target" were the same number. Moving the target to the middle
separated them, and the untouched formula would have doubled the weight of temperature on the two
thermal worlds — a change nobody asked for, arriving silently inside a change about nutrition.

HOW IT IS COMPUTED. Both factors are computed from the resolved `EnvParams` of the campfire world:
the shipped one calls the live `satiation_deviation_range`, the counterfactual substitutes
`max_satiation` in its place. The bars show what one degree of deviation from the temperature
setpoint costs, in satiation units, under each. The right-hand pair shows the consequence at a
realistic deviation — the campfire world's baseline sits about 30 degrees below the body setpoint.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
import _common as C
import house
from src.environment.core import satiation_deviation_range

STEM = "f04_thermal_scale"
p = C.params_for("thermal")
range_S = float(satiation_deviation_range(p))
shipped = range_S / float(p.max_temperature)
ceiling = float(p.max_satiation) / float(p.max_temperature)
DEV = 10.0

house.apply()
fig, ax = plt.subplots(figsize=(7.2, 4.4))
x = np.arange(2)
w = 0.34
b1 = ax.bar(x - w/2, [shipped, shipped * DEV], w, color=house.BLUE,
            label=f"shipped — scaled by the deviation range ({range_S:.0f})")
# Neutral + hatched, not --danger: red means DEATH on this page (figure 1), and this
# bar is a counterfactual, not a hazard (register F11).
b2 = ax.bar(x + w/2, [ceiling, ceiling * DEV], w, color="#d8dad6",
            edgecolor=house.INK_2, hatch="///", linewidth=0.8,
            label=f"if the ceiling ({p.max_satiation:.0f}) had been kept")
for bars in (b1, b2):
    for r in bars:
        ax.annotate(f"{r.get_height():.2f}", xy=(r.get_x() + r.get_width()/2, r.get_height()),
                    xytext=(0, 3), textcoords="offset points", ha="center",
                    fontsize=house.FS_LABEL, color=house.INK)
ax.set_xticks(x)
ax.set_xticklabels(["one degree from\nthe temperature target",
                    f"{DEV:.0f} degrees from\nthe temperature target"])
ax.set_ylabel("cost in homeostatic drive,\nin satiation units")
ax.set_ylim(0, max(ceiling * DEV, shipped * DEV) * 1.22)
house.legend_below(ax, ncol=1)

C.record_samples(STEM, [
    dict(what="conversion factors compared", used=2, total=2,
         note="the shipped one read from the live satiation_deviation_range, and the "
              "counterfactual that substitutes max_satiation for it"),
    dict(what="worlds this applies to", used=2, total=7,
         note="only basic/05 and basic/06 switch the temperature system on; the other five "
              "maintained levels have a two-axis drive and are untouched by this factor")])
house.save(fig, os.path.join(C.FIG_ROOT, STEM))
print(f"  range_S={range_S}  shipped={shipped:.4f}  ceiling-version={ceiling:.4f}  "
      f"ratio={ceiling/shipped:.2f}x")
