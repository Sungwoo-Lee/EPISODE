"""FIGURE r04 — The modulated checkpoint's zero-shot head start, and how much of the first-entry advantage it
explains; with the sampled-action re-check of the key cells.

Sources (read):
  results/analysis/continual_worlds/forgetting_p3_{t1none,t16quad}.json   the branch-point row ('start'):
      the two frozen checkpoints played greedily in all seven worlds before any alternating training
      (identical in P1 and P2; checked in r03).
  results/analysis/continual_worlds/sampled_check_p3.json   the same checkpoints re-played with SAMPLED
      actions (2,000 episodes each, same seeds) for four cells, with unpaired and paired 95 % CIs.
  tmp/20260930_cw_zeroshot_relative.json   per first visit (exploratory, post-data, CONTINUAL_WORLDS.md 10.11):
      diff_Z_greedy (greedy matrix cell of the checkpoint the agent arrives with), diff_Z_samp (first logged
      training row after the switch, ~4,000 episodes, sampled), diff_S20 (the registered first-20k window)
      and diff_gain20 (first-20k mean minus the agent's own start level).
The registered first-20k differences are asserted equal to the verdict file's.
"""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import _common as C

house = C.house; house.apply()
STEM = "r04_head_start"
Z = C.load(C.ZEROSHOT)
V = C.load(C.VERDICT)
SC = C.load(C.SAMPLED)

# ---- (a) branch-point checkpoints, greedy, all worlds ----------------------------------------------
start = {}
for a in ("ordinary", "modulated"):
    F = C.forgetting("P3", a)
    start[a] = {c["world"]: (c["mean"], c["ci95_lo"], c["ci95_hi"]) for c in F["cells"] if c["row"] == "start"}
worlds = sorted(start["ordinary"], key=lambda w: start["modulated"][w][0] - start["ordinary"][w][0], reverse=True)
worlds = [w for w in worlds if w != "forage"] + ["forage"]

fig = plt.figure(figsize=(9.9, 8.6))
axA = fig.add_axes([0.14, 0.60, 0.31, 0.33])
axB = fig.add_axes([0.66, 0.60, 0.33, 0.33])
axC = fig.add_axes([0.26, 0.14, 0.60, 0.27])
ya = np.arange(len(worlds))[::-1]
for y, w in zip(ya, worlds):
    for a, off in (("ordinary", 0.13), ("modulated", -0.13)):
        m, lo, hi = start[a][w]
        axA.plot([lo, hi], [y + off] * 2, color=C.AGENT_COL[a], lw=1.6, alpha=0.55)
        axA.plot([m], [y + off], "o", ms=6, color=C.AGENT_COL[a])
axA.set_yticks(ya); axA.set_yticklabels([C.WORLD[w] + (" (trained)" if w == "forage" else "") for w in worlds],
                                         fontsize=C.SMALLEST_PT)
axA.set_xlim(0, 500); axA.set_xticks([0, 100, 200, 300, 400, 500])
axA.grid(axis="x", visible=True); axA.grid(axis="y", visible=False)
axA.set_xlabel("survival, steps per episode", fontsize=C.SMALLEST_PT + 1)
axA.set_title("(a) branch-point checkpoints, before any training", fontsize=C.SMALLEST_PT + 1.5, loc="left", pad=8)
C.assert_ticks_dont_collide(axA, "x")
diffs0 = {w: start["modulated"][w][0] - start["ordinary"][w][0] for w in worlds}
assert all(d > 0 for d in diffs0.values()), diffs0

# ---- (b) first visits: head start vs first 20k vs gain ---------------------------------------------
fv = []
for s in ("P1", "P2", "P3"):
    vs = {v["stage"]: v for v in V["switches"][s]}
    for z in Z[s]:
        if z["visit"] != 1:
            continue
        assert abs(z["diff_S20"] - (-vs[z["stage"]]["dip_common_diff_steps"])) < 1e-6, (s, z["switch"])
        a, b = z["switch"].split(" -> ")
        fv.append((f"{s}  {C.WORLD[a]} → {C.WORLD[b]}", z))
yb = np.arange(len(fv))[::-1]
MEAS = [("diff_Z_greedy", "head start: checkpoint it arrives with, most-likely action", "s", house.PAPER),
        ("diff_Z_samp", "start level: first ~4,000 training episodes", "o", house.PAPER),
        ("diff_S20", "first 20,000 episodes (the registered window)", "o", house.INK),
        ("diff_gain20", "gain over its own start (first 20k minus start level)", "D", C.GREY)]
OFF = [0.27, 0.09, -0.09, -0.27]
for y, (lab, z) in zip(yb, fv):
    for (k, _, mk, fc), o in zip(MEAS, OFF):
        axB.plot([z[k]], [y + o], mk, ms=5.6, mec=house.INK, mfc=fc, mew=1.2)
axB.axvline(0, color=C.GREY, lw=0.9)
for yy in yb[:-1]:
    axB.axhline(yy - 0.5, color=house.RULE, lw=0.6)
axB.set_yticks(yb); axB.set_yticklabels([l for l, _ in fv], fontsize=C.SMALLEST_PT)
axB.set_xlim(-15, 45); axB.set_xticks([-10, 0, 10, 20, 30, 40])
axB.set_ylim(-0.6, len(fv) - 0.4)
axB.grid(axis="x", visible=True); axB.grid(axis="y", visible=False)
axB.set_xlabel("modulated minus ordinary, steps", fontsize=C.SMALLEST_PT + 1)
axB.set_title("(b) the six first visits", fontsize=C.SMALLEST_PT + 1.5, loc="left", pad=8)
C.assert_ticks_dont_collide(axB, "x")

# ---- (c) sampled vs greedy re-check -----------------------------------------------------------------
CELLNAME = {("start", "winter"): "branch point, played in Winter",
            ("start", "forage"): "branch point, played in Forage",
            ("end_02_winter", "forage"): "after the first Winter stage, in Forage",
            ("end_02_winter", "winter"): "after the first Winter stage, in Winter"}
cells = SC["cells"]
yc = np.arange(len(cells))[::-1]
for y, c in zip(yc, cells):
    for mode, o, mk in (("greedy", 0.14, "s"), ("sampled", -0.14, "o")):
        g = c[f"gap_modulated_minus_ordinary_{mode}"]["unpaired"]
        axC.plot([g["ci95_lo"], g["ci95_hi"]], [y + o] * 2, color=house.INK, lw=1.4)
        axC.plot([g["diff"]], [y + o], mk, ms=6, mec=house.INK, mfc=house.PAPER if mode == "greedy" else house.INK, mew=1.3)
axC.axvline(0, color=C.GREY, lw=0.9)
axC.set_yticks(yc); axC.set_yticklabels([CELLNAME[(c["row"], c["world"])] for c in cells], fontsize=C.SMALLEST_PT)
axC.set_xlim(-20, 130); axC.set_xticks([0, 25, 50, 75, 100, 125])
axC.set_ylim(-0.6, len(cells) - 0.4)
axC.grid(axis="x", visible=True); axC.grid(axis="y", visible=False)
axC.set_xlabel("modulated minus ordinary, steps (bar = 95 % interval)", fontsize=C.SMALLEST_PT + 1)
axC.set_title("(c) re-check with sampled actions: P3 checkpoints", fontsize=C.SMALLEST_PT + 1.5, loc="left", pad=8)
C.assert_ticks_dont_collide(axC, "x")

h = [Line2D([], [], marker="o", ms=6, color=C.ORD, ls="none", label="(a) ordinary"),
     Line2D([], [], marker="o", ms=6, color=C.MOD, ls="none", label="(a) modulated"),
     Line2D([], [], marker="s", ms=5.6, mec=house.INK, mfc=house.PAPER, ls="none", label="(b, c) most-likely action"),
     Line2D([], [], marker="o", ms=5.6, mec=house.INK, mfc=house.PAPER, ls="none", label="(b) start level, sampled"),
     Line2D([], [], marker="o", ms=5.6, mec=house.INK, mfc=house.INK, ls="none", label="(b) first 20k  ·  (c) sampled"),
     Line2D([], [], marker="D", ms=5.6, mec=house.INK, mfc=C.GREY, ls="none", label="(b) gain over own start")]
fig.legend(handles=h, loc="lower center", ncol=3, frameon=False, fontsize=C.SMALLEST_PT + 0.5,
           bbox_to_anchor=(0.5, 0.0), handlelength=1.2, columnspacing=1.2)

# ---- numbers --------------------------------------------------------------------------------------
unseen = [d for w, d in diffs0.items() if w != "forage"]
zmap = {l: z for l, z in fv}
def first(seq, sw):
    return next(z for s in (seq,) for z in Z[s] if z["switch"] == sw)
w1, d1, f1 = first("P3", "forage -> winter"), first("P1", "forage -> danger_scout_a"), first("P2", "forage -> fog_scout_b")
gains = [z["diff_gain20"] for _, z in fv]
cw = {(c["row"], c["world"]): c for c in cells}
g_fw = cw[("end_02_winter", "forage")]["gap_modulated_minus_ordinary_sampled"]["unpaired"]
g_ww = cw[("end_02_winter", "winter")]["gap_modulated_minus_ordinary_sampled"]
g_zw = cw[("start", "winter")]["gap_modulated_minus_ordinary_sampled"]["unpaired"]
C.record_numbers(STEM, {
    "zs_min": C.fmt(min(unseen)), "zs_max": C.fmt(max(unseen)),
    "zs_winter_ord": C.fmt(start["ordinary"]["winter"][0]), "zs_winter_mod": C.fmt(start["modulated"]["winter"][0]),
    "hs_winter": C.fmt(w1["diff_Z_greedy"]), "s20_winter": C.fmt(w1["diff_S20"]),
    "hs_danger": C.fmt(d1["diff_Z_greedy"]), "s20_danger": C.fmt(d1["diff_S20"]),
    "hs_fog": C.fmt(f1["diff_Z_greedy"]), "s20_fog": C.fmt(f1["diff_S20"]),
    "gain_better": str(sum(g > 0 for g in gains)), "gain_worse": str(sum(g < 0 for g in gains)), "gain_n": str(len(gains)),
    "gain_fog": C.fmt(f1["diff_gain20"], sign=True),
    "samp_forage_gap": C.fmt(g_fw["diff"], sign=True), "samp_forage_lo": C.fmt(g_fw["ci95_lo"], sign=True),
    "samp_forage_hi": C.fmt(g_fw["ci95_hi"], sign=True),
    "samp_zs_winter": C.fmt(g_zw["diff"], sign=True), "samp_zs_winter_lo": C.fmt(g_zw["ci95_lo"], sign=True),
    "samp_zs_winter_hi": C.fmt(g_zw["ci95_hi"], sign=True),
    "samp_winter_after": C.fmt(g_ww["unpaired"]["diff"], sign=True),
    "samp_winter_after_plo": C.fmt(g_ww["paired_by_seed"]["ci95_lo"], sign=True),
    "samp_winter_after_phi": C.fmt(g_ww["paired_by_seed"]["ci95_hi"], sign=True)})
C.record_kind(STEM, "mixed")
C.record_samples(STEM, [
    dict(what="(a) worlds played by the branch-point checkpoints", used=len(worlds), total=len(worlds),
         note="2,000 test episodes per cell, most-likely action; the same row in all three sequences"),
    dict(what="(b) first visits", used=len(fv), total=12,
         note="first visits only; the six returns are in Figure 2. Exploratory measures chosen after the data"),
    dict(what="(c) cells re-checked with sampled actions", used=len(cells), total=35,
         note="the cells the headline claims rest on, in the P3 ordinary and modulated matrices; the rest stay greedy only")])
C.save(fig, STEM)
