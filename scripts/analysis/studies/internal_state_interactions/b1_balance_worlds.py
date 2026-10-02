"""FIGURE B1 — Is each world balanced? The pre-registered balance measures, one row per world, on the
map without a warm bush (the primary verdict; Revision 2a).

Panel 1 (time): share of rollout steps in cover, on a warm cell, eating, elsewhere; lines at 10 % and 70 %.
Panel 2 (each need drives its own behaviour): eating ratio (hungry vs fed), hiding ratio (injured vs
barely injured), per-decision warming ratio (b'), log scale; line at 2.
Panel 3 (outcomes): survival share of the ideal policy, and the share of starts dying after step 20.
Panel 4 (combinations): combination gain minus today's, with the pre-registered bar (criterion 6).
Rows: every world of the balance sweep except the grid (the next figure) and checks.
"""
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
import _common as C

house = C.house; house.apply()
SW = os.path.join(C.OUT, "balance")
rule = json.load(open(os.path.join(SW, "balance_rule.json")))
meta = rule["_meta_warm0"]
LABEL = {
    "baseline__level-05__today": "today's level 05",
    "coupling__hungry-healing-floor-0__on": "healing slower when hungry",
    "coupling__healing-costs-0.5-food-per-point__on": "healing uses up food (0.5)",
    "coupling__warmth-costs-food-at-rate-2__on": "cold or hot uses up food (2)",
    "coupling__all-four-picked-rules__on": "all four rules (running experiment)",
    "food__gross-per-bite__10": "food per bite 10", "food__gross-per-bite__8": "food per bite 8",
    "food__gross-per-bite__5": "food per bite 5", "food__gross-per-bite__4": "food per bite 4",
    "food__gross-per-bite__3": "food per bite 3",
    "search__trip-to-food-x-bites-per-item__t6_b12": "food search: trip 6, 12 bites",
    "search__trip-to-food-x-bites-per-item__t8_b12": "food search: trip 8, 12 bites",
    "search__trip-to-food-x-bites-per-item__t4_b6": "food search: trip 4, 6 bites",
    "search__trip-to-food-x-bites-per-item__t6_b6": "food search: trip 6, 6 bites",
    "search__trip-to-food-x-bites-per-item__t8_b6": "food search: trip 8, 6 bites",
    "injury__bush-healing-multiplier__10": "bush heals 10x (not 25x)",
    "temperature__cooling-rate-scale__0.5": "body cools twice as fast",
    "hazard_diagnostic__hit-probability-outside-cover-(times-measured)__0.5": "check: predator hits halved",
    "hazard_diagnostic__hit-probability-outside-cover-(times-measured)__2.0": "check: predator hits doubled",
}
rows = [k for k in LABEL if k in rule]
fig, ax = plt.subplots(1, 4, figsize=(10.0, 7.6), sharey=True, gridspec_kw=dict(width_ratios=[1.1, 1.0, 1.0, 0.9]))
y = np.arange(len(rows))[::-1]
MK = {"cover": ("o", house.BLUE), "warm": ("s", house.ORANGE), "eat": ("D", house.GREEN), "elsewhere": ("^", "#8a8f99")}
for r, k in enumerate(rows):
    v = rule[k]["warm0"]
    for a, (mk, col) in MK.items():
        ax[0].plot([100 * v["time_share"][a]], [y[r]], mk, color=col, ms=5, label=a if r == 0 else None)
    dr = v["drive_ratio"]
    for lab, val, mk, col in (("eating", dr["eat"], "D", house.GREEN), ("hiding", dr["hide"], "o", house.BLUE),
                              ("warming (per decision)", v["warming_per_decision"], "s", house.ORANGE)):
        if val:
            ax[1].plot([min(val, 1000)], [y[r]], mk, color=col, mfc="white" if lab.startswith("warming") else col,
                       ms=5, label=lab if r == 0 else None)
    ax[2].plot([100 * v["survival"]], [y[r]], "o", color=house.INK, ms=5, label="survives 500 steps" if r == 0 else None)
    ax[2].plot([100 * v["late_death_share"]], [y[r]], "x", color=house.INK, ms=6, label="dies after step 20" if r == 0 else None)
    ax[3].plot([100 * v["comb_gain_minus_today"]], [y[r]], "o", color=house.INK, ms=5)
for x in (10, 70):
    ax[0].axvline(x, color=house.INK, lw=0.8, ls=":")
ax[1].axvline(2, color=house.INK, lw=0.8, ls=":"); ax[1].set_xscale("log"); ax[1].set_xlim(0.8, 1500)
ax[3].axvline(0, color=house.INK, lw=0.8); ax[3].axvline(100 * meta["comb_needed"], color=house.INK, lw=0.8, ls=":")
ax[0].set_xlim(0, 60); ax[2].set_xlim(0, 100); ax[3].set_xlim(-8, 11)
ax[0].set_xlabel("share of\nsteps (%)"); ax[1].set_xlabel("need present ÷\nneed absent (×)")
ax[2].set_xlabel("share of\nstarts (%)"); ax[3].set_xlabel("combination gain\nvs today (points)")
ax[0].set_yticks(y); ax[0].set_yticklabels([LABEL[k] for k in rows], fontsize=9.5)
for a in ax:
    a.grid(axis="y", visible=False)
ax[0].set_ylim(-0.8, len(rows) - 0.3)
fig.tight_layout(w_pad=0.6, rect=(0, 0.1, 1, 1))
h, l = [], []
for a in ax[:3]:
    hh, ll = a.get_legend_handles_labels(); h += hh; l += ll
fig.legend(h, l, loc="lower center", ncol=5, frameon=False, bbox_to_anchor=(0.5, 0.0), fontsize=9.5)
C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)
C.record_kind("b1_balance_worlds", "planner")
C.record_samples("b1_balance_worlds", [
    dict(what="worlds shown (one setting changed from today, plus two checks)", used=len(rows), total=len(rows),
         note="the food × predator grid is the next figure; map without a warm bush only (primary verdict)"),
    dict(what="rollout starts per world", used=2000, total=2000, note="training-style random starts, 500 steps each")])
house.save(fig, os.path.join(C.FIG, "b1_balance_worlds"), column_px=C.COLUMN_PX)
