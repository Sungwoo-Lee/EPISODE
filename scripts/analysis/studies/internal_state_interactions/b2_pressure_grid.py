"""FIGURE B2 — Does combination dependence peak at a middle food pressure? Food energy per bite (gross,
horizontal) against predator hit odds (x0.5, today, x2; one line each), map without a warm bush.

Left: combination gain minus today's (points), with the pre-registered bar (criterion 6).
Middle: share of steps eating. Right: survival share of the ideal policy.
"""
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
import _common as C

house = C.house; house.apply()
SW = os.path.join(C.OUT, "balance")
rule = json.load(open(os.path.join(SW, "balance_rule.json"))); meta = rule["_meta_warm0"]
FOOD = [3, 4, 5, 6, 8, 10]
def key(g, h):
    if h == 1.0:
        return "baseline__level-05__today" if g == 6 else f"food__gross-per-bite__{g}"
    if g == 6:
        return f"hazard_diagnostic__hit-probability-outside-cover-(times-measured)__{h}"
    return f"grid__gross-food-x-hazard__g{g}_h{h}"
fig, ax = plt.subplots(1, 3, figsize=(10.0, 3.8))
styles = {0.5: ("o", ":", "predator hits halved"), 1.0: ("s", "-", "predator hits as measured"), 2.0: ("^", "--", "predator hits doubled")}
n_used = 0
for h, (mk, ls, lab) in styles.items():
    ks = [key(g, h) for g in FOOD]; vs = [rule[k]["warm0"] for k in ks]; n_used += len(vs)
    ax[0].plot(FOOD, [100 * v["comb_gain_minus_today"] for v in vs], marker=mk, ls=ls, color=house.INK, ms=5, label=lab)
    ax[1].plot(FOOD, [100 * v["time_share"]["eat"] for v in vs], marker=mk, ls=ls, color=house.INK, ms=5)
    ax[2].plot(FOOD, [100 * v["survival"] for v in vs], marker=mk, ls=ls, color=house.INK, ms=5)
ax[0].axhline(0, color="#8a8f99", lw=0.8); ax[0].axhline(100 * meta["comb_needed"], color=house.INK, lw=0.8, ls=":")
ax[0].set_ylabel("combination gain\nvs today (points)"); ax[1].set_ylabel("steps eating (%)"); ax[2].set_ylabel("survives 500 steps (%)")
for a in ax:
    a.set_xlabel("food energy per bite (gross)"); a.set_xticks(FOOD); a.axvline(6, color="#d4d6dc", lw=6, zorder=0)
fig.tight_layout(w_pad=1.0, rect=(0, 0.12, 1, 0.97))
h_, l_ = ax[0].get_legend_handles_labels()
fig.legend(h_, l_, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 0.0), fontsize=9.5, handlelength=3.5)
C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)
C.record_kind("b2_pressure_grid", "planner")
C.record_samples("b2_pressure_grid", [
    dict(what="worlds: food energy per bite x predator hit odds", used=n_used, total=18,
         note="6 food values x 3 hazard levels; today's is food 6 at measured odds (grey band)"),
    dict(what="rollout starts per world", used=2000, total=2000, note="map without a warm bush")])
house.save(fig, os.path.join(C.FIG, "b2_pressure_grid"), column_px=C.COLUMN_PX)
