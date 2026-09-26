"""FIGURE S3 — For each world: how much knowing a second body variable improves the best choice,
how the choices are shared out, and whether the ideal policy survives (ideal planner, no agent).

Left: combination gain (accuracy of the best two-variable rule minus the best one-variable rule, in
points, over training start states, ties excluded): both maps pooled 0.59/0.41 (black, the ruled
value), and each map alone (blue: no bush on a fire ring; grey: a bush on a fire ring). Solid line: today's
level 05 with B1; dotted: +5 points (rule 1); the grey band is today +/- twice the noise floor.
Middle: need balance -- share of start states in which each choice is best.
Right: survival share of the ideal policy over 500 steps (2,000 starts per map).
A black diamond in the right margin marks worlds that pass the pre-registered reading rule (STUDY_PLAN.md, Revisions 1 and 1b).
Writes results/analysis/internal_state_interactions/reading_rule.json.
"""
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
import _common as C, sweep as SW

house = C.house; house.apply()
R = C.sweep_results()
base = R["baseline__level 05__today"]
finer = R["check__finer grid__81x41x91"]
noise = abs(finer["summary"]["combination_gain"] - base["summary"]["combination_gain"])
b_gain, b_surv = base["summary"]["combination_gain"], base["survival_share"]
settings = [w for w in SW.worlds(R["baseline__level 05__today"]["trip"]["F"]) if w[1] not in ("check",) and w[0] in R]


def rule(res):
    s = res["summary"]; bal = s["balance"]
    r1 = s["combination_gain"] >= b_gain + 0.05 and (s["combination_gain"] - b_gain) > 2 * noise
    r2 = max(bal.values()) <= 0.80 and any(v >= 0.10 for k, v in bal.items() if k != "rest in cover")
    r3 = res["survival_share"] >= b_surv - 0.05
    r4 = res["summary_gamma099"]["combination_gain"] > base["summary_gamma099"]["combination_gain"]   # same direction at 0.99
    tie_flag = s["tie_share"] > 0.40
    return r1, r2, r3, r4, tie_flag


fig, ax = plt.subplots(1, 3, figsize=(10.0, 8.2), gridspec_kw=dict(width_ratios=[1, 1.2, 0.6]), sharey=True)
y = np.arange(len(settings))[::-1]; out = {}; labels = []
for r, (name, group, label, value, *_rest) in enumerate(settings):
    res = R[name]; s = res["summary"]
    labels.append("today" if group == "baseline" else f"{group}: {label} = {value:g}")
    r1, r2, r3, r4, tie_flag = rule(res); ok = r1 and r2 and r3 and not tie_flag and group != "baseline"
    out[name] = dict(group=group, label=label, value=value, combination_gain=s["combination_gain"],
                     balance=s["balance"], tie_share=s["tie_share"], survival_share=res["survival_share"],
                     rule_1_gain=bool(r1), rule_2_balance=bool(r2), rule_3_survival=bool(r3),
                     rule_4_same_direction_at_099=bool(r4), tie_flag=bool(tie_flag), passes=bool(ok),
                     gain_by_margin=res["gain_by_margin"], gain_099=res["summary_gamma099"]["combination_gain"])
    ax[0].plot([100 * s["combination_gain"]], [y[r]], "o", color=house.INK, ms=6.5,
               label="both maps (59 : 41)" if r == 0 else None)
    ax[0].plot([100 * s["per_map"][0]["combination_gain"]], [y[r] + 0.22], "v", color=house.BLUE, ms=5,
               label="no bush on a fire ring (59 %)" if r == 0 else None)
    ax[0].plot([100 * s["per_map"][1]["combination_gain"]], [y[r] - 0.22], "^", mfc="white", mec="#8a8f99", ms=5,
               label="a bush on a fire ring (41 %)" if r == 0 else None)
    if ok:
        # in the right margin, outside the survival axis, so it cannot read as a survival value
        ax[2].plot([1.12], [y[r]], marker="D", color=house.INK, ms=5, transform=ax[2].get_yaxis_transform(), clip_on=False)
    left = 0.0
    for cat in C.CHOICE_ORDER:
        v = 100 * s["balance"][cat]
        ax[1].barh(y[r], v, left=left, color=C.CHOICE_COLOURS[cat], height=0.7, label=cat if r == 0 else None,
                   edgecolor="white", linewidth=0.4)
        left += v
    ax[2].plot([100 * res["survival_share"]], [y[r]], "o", color=house.INK, ms=5)
ax[0].axvspan(100 * (b_gain - 2 * noise), 100 * (b_gain + 2 * noise), color="#d4d6dc", lw=0)
ax[0].axvline(100 * b_gain, color=house.INK, lw=0.9); ax[0].axvline(100 * b_gain + 5, color=house.INK, lw=0.9, ls=":")
ax[0].set_yticks(y); ax[0].set_yticklabels(labels, fontsize=9.5)
ax[0].set_xlabel("combination gain (points)"); ax[1].set_xlabel("best choice (% of start states)")
ax[2].set_xlabel("survival (%)"); ax[1].set_xlim(0, 100)
for a in ax:
    a.grid(axis="y", visible=False)
ax[0].set_ylim(-0.8, len(settings) - 0.3)
fig.tight_layout(w_pad=0.8, rect=(0, 0.09, 1, 1))
h, l = ax[1].get_legend_handles_labels(); h0, l0 = ax[0].get_legend_handles_labels()
fig.legend(h0 + h, l0 + l, loc="lower center", ncol=4, frameon=False, bbox_to_anchor=(0.5, 0.0), fontsize=9.5)
C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)
C.record_kind("s3_worlds", "planner")
C.record_samples("s3_worlds", [
    dict(what="worlds solved (each on two maps)", used=len(settings), total=len([w for w in SW.worlds(R["baseline__level 05__today"]["trip"]["F"]) if w[1] != "check"]),
         note="one setting changed at a time from today's level 05 with B1"),
    dict(what="start states per map (food x injury x temperature at open ground)", used=41106, total=41106,
         note="grid 51 x 26 x 31 over food 0-200, injury 0-100, temperature -10..+5"),
    dict(what="start states excluded as ties (today's world)", used=int(round(41106 * base["summary"]["tie_share"])), total=41106,
         note="best and second-best choice within 0.5 return units")])
house.save(fig, os.path.join(C.FIG, "s3_worlds"), column_px=C.COLUMN_PX)
out["_meta"] = dict(baseline_gain=b_gain, noise_floor=noise, baseline_survival=b_surv,
                    baseline_gain_099=base["summary_gamma099"]["combination_gain"])
json.dump(out, open(os.path.join(C.OUT, "reading_rule.json"), "w"), indent=1)
print(f"baseline gain {100*b_gain:.1f}  noise floor {100*noise:.1f}  survival {100*b_surv:.1f}")
for k, v in out.items():
    if k != "_meta":
        print(f"  {'PASS' if v['passes'] else '    '} {k:58} gain {100*v['combination_gain']:5.1f}  max-cat {100*max(v['balance'].values()):4.0f}  surv {100*v['survival_share']:5.1f}  r1{int(v['rule_1_gain'])} r2{int(v['rule_2_balance'])} r3{int(v['rule_3_survival'])} r4{int(v['rule_4_same_direction_at_099'])} tie{int(v['tie_flag'])}")
