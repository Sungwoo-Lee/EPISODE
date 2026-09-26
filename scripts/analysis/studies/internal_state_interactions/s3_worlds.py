"""FIGURE S3 — For each world: how often the best choice needs more than one body variable, and
how the choices are shared out (ideal planner, no trained agent).

Left: interaction share (share of training start states whose best choice cannot be predicted from
any single body variable), for the map without a warm bush (filled) and with one (hollow); the
vertical line is today's level 05, the dotted line is today + 5 points (the reading rule).
Right: need balance, the share of start states in which each choice is best (map without a warm
bush). A black diamond marks worlds that pass the reading rule fixed in the study plan (both maps).
Writes results/analysis/internal_state_interactions/reading_rule.json.
"""
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
import _common as C, sweep as SW

house = C.house; house.apply()
R = C.sweep_results()
rows = [w for w in SW.worlds() if (w[0], False) in R and (w[0], True) in R]
base = {warm: R[("baseline__level 05__today", warm)]["summary"] for warm in (False, True)}


def passes(summ, warm):
    b = summ["balance"]
    return (summ["interaction_share"] >= base[warm]["interaction_share"] + 0.05
            and max(b.values()) <= 0.80
            and any(v >= 0.10 for k, v in b.items() if not k.startswith("rest in cover")))


fig, ax = plt.subplots(1, 2, figsize=(10.0, 8.0), gridspec_kw=dict(width_ratios=[1, 1.25]), sharey=True)
y = np.arange(len(rows))[::-1]; rule = {}; labels = []
for r, (name, group, label, value, _, _) in enumerate(rows):
    labels.append("today" if group == "baseline" else f"{group}: {label} = {value:g}")
    s0, s1 = R[(name, False)]["summary"], R[(name, True)]["summary"]
    ax[0].plot([100 * s0["interaction_share"]], [y[r]], "o", color=house.INK, ms=6)
    ax[0].plot([100 * s1["interaction_share"]], [y[r]], "o", mfc="white", mec=house.INK, ms=6, mew=1.3)
    ok = passes(s0, False) and passes(s1, True)
    rule[name] = dict(group=group, label=label, value=value, passes=bool(ok),
                      interaction_share=[s0["interaction_share"], s1["interaction_share"]],
                      balance=[s0["balance"], s1["balance"]])
    if ok:
        ax[0].plot([1.0], [y[r]], marker="D", color=house.INK, ms=5, transform=ax[0].get_yaxis_transform(), clip_on=False)
    left = 0.0
    for cat in C.CHOICE_ORDER:
        v = 100 * s0["balance"].get(cat, 0.0)
        ax[1].barh(y[r], v, left=left, color=C.CHOICE_COLOURS[cat], height=0.7,
                   label=cat if r == 0 else None, edgecolor="white", linewidth=0.4)
        left += v
b0 = 100 * base[False]["interaction_share"]
ax[0].axvline(b0, color=house.INK, lw=0.9); ax[0].axvline(b0 + 5, color=house.INK, lw=0.9, ls=":")
ax[0].set_yticks(y); ax[0].set_yticklabels(labels, fontsize=9.5)
ax[0].set_xlabel("interaction share (% of start states)"); ax[0].grid(axis="y", visible=False)
ax[1].set_xlabel("best choice (% of start states, no warm bush)"); ax[1].set_xlim(0, 100); ax[1].grid(axis="y", visible=False)
ax[0].set_ylim(-0.8, len(rows) - 0.3)
fig.tight_layout(w_pad=1.0, rect=(0, 0.07, 1, 1))
h, l = ax[1].get_legend_handles_labels()
fig.legend(h, l, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.62, 0.0), fontsize=9.5)
C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)
C.record_kind("s3_worlds", "planner")
n_states = base[False]["n_states"]
C.record_samples("s3_worlds", [
    dict(what="worlds solved (each on two maps)", used=len(rows), total=len(SW.worlds()), note="sweep outputs present"),
    dict(what="start states per world and map", used=n_states, total=n_states,
         note="grid: food 0-200 by 4, injury 0-100 by 4, temperature -10..+5 by 0.5, at open ground")])
house.save(fig, os.path.join(C.FIG, "s3_worlds"), column_px=C.COLUMN_PX)
json.dump(rule, open(os.path.join(C.OUT, "reading_rule.json"), "w"), indent=1)
for k, v in rule.items():
    print(f"  {'PASS' if v['passes'] else '    '} {k:60} share {100*v['interaction_share'][0]:5.1f} / {100*v['interaction_share'][1]:5.1f}")
