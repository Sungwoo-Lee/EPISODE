"""FIGURE C3 — Can a bigger, harder-to-smell world make food search a real task without killing the
agent? (context-exploration study, Part 3, Revision 2a: the ideal planner with the warmth trip taken
from memory, hazard x1.)

Left: mean food search time on 1,000 real resets (steps, log scale) against the food-smell range, one
line per grid size (marker shape) and food setup (line style); other entities at today's density.
Dotted line: the 20-step floor (the agent's planning horizon at discount 0.95).
Right: survival share of the ideal planner against mean food search time (log scale), one point per
world; filled = other entities at today's density, open = at today's count; black = passes balance
criteria 1, 2, 4 and 5 at hazard x1, grey = fails. Dotted lines: 20-step floor and 80 % of today's
survival.
"""
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import _common as C

house = C.house; house.apply()
SRC = os.path.join(C.ROOT, "results/analysis/context_exploration/part3_balance_worlds_rev2.json")
d = json.load(open(SRC))
W = d["worlds"]; FLOOR = d["search_floor_steps"]
TODAY = d["today_survival"]["memory"]["1.0"]; BAR4 = 0.8 * TODAY
RANGES = [20, 8, 5, 3]
GRID_MK = {10: "o", 15: "s", 20: "^"}
FOOD_LS = {"count": ("-", "same food count as today"), "density": ("--", "same food density"),
           "mid": ("-.", "middle food setting"), "fewrich": ((0, (5, 1.5, 1, 1.5, 1, 1.5)), "1-2 rich items")}
FAIL = "#9aa0a8"

fig, ax = plt.subplots(1, 2, figsize=(10.0, 4.6))
xr = np.arange(len(RANGES), dtype=float)
lines = {}
for n, w in W.items():
    if w["others"] == "od":
        lines.setdefault((w["grid"], w["food"]), {})[w["range"]] = w["search"]["food"]["mean"]
for (g, f), byr in sorted(lines.items()):
    ax[0].plot(xr, [byr[r] for r in RANGES], ls=FOOD_LS[f][0], marker=GRID_MK[g], color=house.INK, lw=1.3,
               ms=5.5, mfc=house.INK, mec=house.INK)
ax[0].axhline(FLOOR, color=house.INK, lw=0.9, ls=":")
ax[0].set_yscale("log"); ax[0].set_ylim(3, 400)
ax[0].set_yticks([5, 10, 20, 50, 100, 200]); ax[0].set_yticklabels(["5", "10", "20", "50", "100", "200"])
ax[0].set_xticks(xr); ax[0].set_xticklabels([str(r) for r in RANGES]); ax[0].set_xlim(-0.3, 3.3)
ax[0].set_xlabel("food smell range (cells)"); ax[0].set_ylabel("mean food search (steps)")

n_pass = 0
for n, w in W.items():
    h = w["by_trip"]["memory"]["per_hazard"]["1.0"]; ok = h["pass_1245"]; n_pass += ok
    col = house.INK if ok else FAIL
    ax[1].plot([w["search"]["food"]["mean"]], [100 * h["survival_share"]], GRID_MK[w["grid"]], ms=6,
               mec=col, mfc=col if w["others"] == "od" else "white", mew=1.2, zorder=3 if ok else 2)
tw = W[d["today"]]
ax[1].annotate("today", (tw["search"]["food"]["mean"], 100 * TODAY), xytext=(3.2, 68), fontsize=9.5,
               color=house.INK, arrowprops=dict(arrowstyle="-", color=house.INK, lw=0.8))
ax[1].axvline(FLOOR, color=house.INK, lw=0.9, ls=":")
ax[1].axhline(100 * BAR4, color=house.INK, lw=0.9, ls=":")
ax[1].text(330, 100 * BAR4 + 1.5, "80 % of today", fontsize=9.5, ha="right", va="bottom", color=house.INK)
ax[1].set_xscale("log"); ax[1].set_xlim(3, 400)
ax[1].set_xticks([5, 10, 20, 50, 100, 200]); ax[1].set_xticklabels(["5", "10", "20", "50", "100", "200"])
ax[1].set_ylim(-3, 90)
ax[1].set_xlabel("mean food search (steps)"); ax[1].set_ylabel("survives 500 steps (%)")
ax[1].grid(axis="x", visible=True)
fig.tight_layout(w_pad=1.5, rect=(0, 0.2, 1, 1))
k = dict(color=house.INK, mec=house.INK, lw=0)
rowA = [Line2D([], [], marker=GRID_MK[g], mfc=house.INK, ms=6, label=f"{g} x {g} grid", **k) for g in GRID_MK]
rowA += [Line2D([], [], marker="o", mfc=house.INK, ms=6, label="others at today's density", **k),
         Line2D([], [], marker="o", mfc="white", ms=6, label="others at today's count", **k)]
rowB = [Line2D([], [], color=house.INK, ls=FOOD_LS[f][0], lw=1.3, label=FOOD_LS[f][1]) for f in FOOD_LS]
rowC = [Line2D([], [], marker="o", mfc=house.INK, ms=6, label="passes balance criteria 1, 2, 4, 5 (right)", **k),
        Line2D([], [], marker="o", color=FAIL, mec=FAIL, mfc=FAIL, lw=0, ms=6, label="fails them (right)"),
        Line2D([], [], color=house.INK, lw=0.9, ls=":", label="20-step search floor (both)")]
for hs, yb, hl in ((rowA, 0.115, 1.1), (rowB, 0.057, 3.2), (rowC, 0.0, 2.2)):
    fig.legend(handles=hs, loc="lower center", ncol=len(hs), frameon=False, bbox_to_anchor=(0.5, yb),
               fontsize=9.5, handlelength=hl, columnspacing=1.4)
C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)

C.record_kind("c3_search_vs_survival", "planner")
od = [w for w in W.values() if w["others"] == "od"]
capped = [w for w in W.values() if w["search"]["food"]["capped_share"] > 0]
C.record_samples("c3_search_vs_survival", [
    dict(what="worlds on the left (others at today's density)", used=len(od), total=len(W),
         note="the 'others at today's count' worlds share the same food positions, so their search times are identical"),
    dict(what="worlds on the right", used=len(W), total=len(W),
         note=f"{n_pass} pass balance criteria 1, 2, 4, 5 at hazard x1; memory warmth trip"),
    dict(what="real resets per world for the food search time", used=min(w["search"]["food"]["n"] for w in W.values()),
         total=max(w["search"]["food"]["n"] for w in W.values()),
         note=f"search capped at 2,000 steps in {len(capped)} worlds (at most {100 * max(w['search']['food']['capped_share'] for w in W.values()):.1f} % of resets)")])
house.save(fig, os.path.join(C.FIG, "c3_search_vs_survival"), column_px=C.COLUMN_PX)
