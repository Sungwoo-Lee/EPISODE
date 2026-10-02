"""FIGURE C2 — How much would it be worth to know the danger level? (context-exploration study, Part 2.)

The ideal planner is solved twice for each danger context (0, 1 or 2 hunting predators): once knowing
the context, once for the average context; both are then followed in that context. Hit rates come from
each trained agent's own recordings (ordinary: filled circle; modulator: open square).

Left: value of knowing = survival share (policy for the context) minus survival share (average policy),
in percentage points; large marker = mean over 3 rollout seeds x 10,000 starts, bar = 95 % interval,
small dots = the three seeds. Dotted line: pre-registered 2-point bar.
Right: share of start states where the context's best choice beats the average policy's choice by more
than the tie margin 0.5. Dotted line: pre-registered 10 % bar.
"""
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
import _common as C

house = C.house; house.apply()
SRC = os.path.join(C.ROOT, "results/analysis/context_exploration/part2_value_of_knowing.json")
d = json.load(open(SRC))
CTX = ["pred0", "pred1", "pred2"]
AG = {"ordinary": ("o", house.INK, "hit rates from the ordinary agent"),
      "modulator": ("s", "white", "hit rates from the modulator agent")}
fig, ax = plt.subplots(1, 2, figsize=(10.0, 4.0))
x = np.arange(len(CTX), dtype=float)
for j, (ag, (mk, fc, lab)) in enumerate(AG.items()):
    off = -0.12 if j == 0 else 0.12
    for i, c in enumerate(CTX):
        v = d["per_agent"][ag]["contexts"][c]
        lo, hi = v["value_ci95"]
        ax[0].plot([x[i] + off] * 2, [lo, hi], color=house.INK, lw=1.6, solid_capstyle="butt")
        ax[0].plot([x[i] + off + 0.07] * 3, v["value_points_per_seed"], ".", color="#8a8f99", ms=4)
        ax[0].plot([x[i] + off], [v["value_points"]], mk, mfc=fc, mec=house.INK, mew=1.3, ms=7,
                   label=lab if i == 0 else None)
        ax[1].plot([x[i] + off], [100 * v["choice_difference"]["0.5"]["category"]], mk, mfc=fc, mec=house.INK,
                   mew=1.3, ms=7)
ax[0].axhline(0, color="#8a8f99", lw=0.8)
ax[0].axhline(2, color=house.INK, lw=0.9, ls=":")
ax[0].text(-0.45, 2.25, "worth-knowing bar (2 points)", fontsize=9.5, color=house.INK, va="bottom")
ax[1].axhline(10, color=house.INK, lw=0.9, ls=":")
ax[1].text(-0.45, 10.4, "worth-knowing bar (10 %)", fontsize=9.5, color=house.INK, va="bottom")
for a in ax:
    a.set_xticks(x); a.set_xticklabels(["no predators", "1 predator", "2 predators"])
    a.set_xlim(-0.55, 2.55); a.set_xlabel("danger context (hunting predators)")
ax[0].set_ylim(-1, 7); ax[1].set_ylim(0, 25)
ax[0].set_ylabel("value of knowing\n(survival, points)"); ax[1].set_ylabel("start states choosing\ndifferently (%)")
fig.tight_layout(w_pad=1.5, rect=(0, 0.09, 1, 1))
h_, l_ = ax[0].get_legend_handles_labels()
fig.legend(h_, l_, loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, 0.0), fontsize=9.5)
C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)

C.record_kind("c2_value_of_knowing", "planner")
rows = []
for ag in AG:
    cx = d["per_agent"][ag]["contexts"]
    rows.append(dict(what=f"{ag} agent: recorded episodes behind the hit rates (0 / 1 / 2 predators)",
                     used=sum(cx[c]["episodes"] for c in CTX), total=sum(cx[c]["episodes"] for c in CTX),
                     note="per context " + " / ".join(f"{cx[c]['episodes']:,}" for c in CTX)
                          + "; the ambusher-split contexts are in the study plan, not drawn"))
    rows.append(dict(what=f"{ag} agent: start states compared per context", used=cx["pred0"]["choice_difference"]["start_states"],
                     total=cx["pred0"]["choice_difference"]["start_states"], note="every start state of the planner, tie margin 0.5"))
rows.append(dict(what="rollouts per policy and context", used=len(d["seeds"]) * d["starts_per_seed"],
                 total=len(d["seeds"]) * d["starts_per_seed"], note=f"{len(d['seeds'])} seeds x {d['starts_per_seed']:,} starts, 500 steps, map without a warm bush"))
C.record_samples("c2_value_of_knowing", rows)
house.save(fig, os.path.join(C.FIG, "c2_value_of_knowing"), column_px=C.COLUMN_PX)
