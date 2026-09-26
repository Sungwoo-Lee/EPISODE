"""FIGURE S5 — Does the ranking survive the choices the analysis had to make?

For every world, the combination gain MINUS today's, in points, under four variants of the analysis:
tie margin 0, 0.5 (the rule's) and 2 return units at discount 0.95, and discount 0.99 (margin 0.5).
The grey band is +/- twice the noise floor (today re-solved on a finer grid). Also shown as two extra
rows: today's world with the predator hazard switched off and doubled (checks, not settings).
"""
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
import _common as C, sweep as SW

house = C.house; house.apply()
R = C.sweep_results()
rule = json.load(open(os.path.join(C.OUT, "reading_rule.json")))
base = R["baseline__level 05__today"]
noise = rule["_meta"]["noise_floor"]
rows = [w for w in SW.worlds() if w[0] in R and w[1] != "baseline" and not w[0].startswith("check__finer")]
# shapes and fills only, all in ink: blue and grey already mean choices on this page (F11)
VARIANTS = [("margin 0", lambda r: r["gain_by_margin"]["0.0"], "o", house.INK, "full"),
            ("margin 0.5 (rule)", lambda r: r["gain_by_margin"]["0.5"], "o", house.INK, "none"),
            ("margin 2", lambda r: r["gain_by_margin"]["2.0"], "s", house.INK, "none"),
            ("discount 0.99", lambda r: r["summary_gamma099"]["combination_gain"], "^", house.INK, "full")]
fig, ax = plt.subplots(figsize=(10.0, 8.0))
y = np.arange(len(rows))[::-1]; labels = []
for r, (name, group, label, value, *_x) in enumerate(rows):
    res = R[name]
    labels.append(f"{group}: {label} = {value:g}")
    for k, (vl, f, mk, col, fill) in enumerate(VARIANTS):
        d = 100 * (f(res) - f(base))
        ax.plot([d], [y[r] + (1.5 - k) * 0.17], mk, color=col, mfc=col if fill == "full" else "white", mec=col, ms=5.5,
                label=vl if r == 0 else None)
ax.axvspan(-200 * noise, 200 * noise, color="#d4d6dc", lw=0)
ax.axvline(0, color=house.INK, lw=0.9); ax.axvline(5, color=house.INK, lw=0.9, ls=":")
ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=9.5); ax.grid(axis="y", visible=False)
ax.set_xlabel("combination gain minus today's (points)")
ax.set_ylim(-0.8, len(rows) - 0.3)
fig.tight_layout(rect=(0, 0.06, 1, 1))
h, l = ax.get_legend_handles_labels()
fig.legend(h, l, loc="lower center", ncol=4, frameon=False, bbox_to_anchor=(0.55, 0.0), fontsize=9.5)
C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)
C.record_kind("s5_robustness", "planner")
C.record_samples("s5_robustness", [
    dict(what="worlds and checks shown", used=len(rows), total=len(rows), note="each solved twice (discount 0.95 and 0.99) on both maps"),
    dict(what="analysis variants per world", used=4, total=4, note="tie margins 0 / 0.5 / 2; discount 0.99")])
house.save(fig, os.path.join(C.FIG, "s5_robustness"), column_px=C.COLUMN_PX)
