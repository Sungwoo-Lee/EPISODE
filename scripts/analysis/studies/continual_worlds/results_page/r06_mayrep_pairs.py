"""FIGURE r06 — May replication, the registered readings: return advantage and forgetting difference per seed
pair against the pre-registered noise band, and May's own return advantage for scale.

Source: results/analysis/continual_worlds/mayrep_readout.json, `mayrep.H_ret` and `mayrep.H_forget` (k = 3, 5):
per-pair modulated-minus-ordinary differences (seeds 42, 43, 44), their mean, the between-seed SE (`se_raw`)
and the SE actually used (`se`, floored at the pre-registered floor `se_floor`); the rule counts a reading as
beyond noise when |mean| > 2 x se. May's numbers are `mayrep.may_comparison.may` (D = May's return advantage
in steps; norm_adv / may_sized_line = the same as a share of stage-1 survival) and the replication's stage-1
ordinary level `may_comparison.reference_200k.S1_ord_mean`.
"""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import _common as C

house = C.house; house.apply()
STEM = "r06_mayrep_pairs"
M = C.load(C.MAYREP)["mayrep"]
MAY = M["may_comparison"]["may"]
S1 = M["may_comparison"]["reference_200k"]["S1_ord_mean"]
READ = [("H_ret", "3", "better return, first return"), ("H_ret", "5", "better return, second return"),
        ("H_forget", "3", "less forgetting, first return"), ("H_forget", "5", "less forgetting, second return")]
SEEDM = {0: "o", 1: "s", 2: "^"}

fig = plt.figure(figsize=(9.9, 5.6))
axA = fig.add_axes([0.25, 0.25, 0.36, 0.62])
axB = fig.add_axes([0.66, 0.25, 0.32, 0.62])
ys = np.arange(len(READ))[::-1]
for y, (key, k, lab) in zip(ys, READ):
    r = M[key][k]
    assert r["n_pairs"] == 3 and r["verdict"] == "inside noise", (key, k)
    band = 2 * r["se"]
    axA.plot([-band, band], [y, y], color=C.BAND, lw=9, solid_capstyle="butt", zorder=1)
    axA.plot([-2 * r["se_raw"], 2 * r["se_raw"]], [y - 0.28] * 2, color=C.GREY, lw=1.4, zorder=2)
    for i, d in enumerate(r["pair_diffs"]):
        axA.plot([d], [y + 0.12], SEEDM[i], ms=5.2, mfc=house.PAPER, mec=house.INK, mew=1.1, zorder=3)
    axA.plot([r["mean_diff"]], [y], "D", ms=7, color=house.INK, zorder=4)
axA.axvline(0, color=C.GREY, lw=0.9)
axA.set_yticks(ys); axA.set_yticklabels([l for *_, l in READ], fontsize=C.SMALLEST_PT)
axA.set_ylim(-0.7, len(READ) - 0.4); axA.set_xlim(-12, 12); axA.set_xticks([-10, -5, 0, 5, 10])
axA.grid(axis="x", visible=True); axA.grid(axis="y", visible=False)
axA.set_xlabel("modulated minus ordinary, steps", fontsize=C.SMALLEST_PT + 1)
axA.set_title("(a) the replication, per seed pair", fontsize=C.SMALLEST_PT + 1.5, loc="left", pad=8)
C.assert_ticks_dont_collide(axA, "x")

yb = np.array([1, 0])
for y, k in zip(yb, ("3", "5")):
    axB.barh(y + 0.17, MAY["D"][k], height=0.3, color=C.GREY)
    axB.barh(y - 0.17, M["H_ret"][k]["mean_diff"], height=0.3, color=house.INK)
    axB.plot([MAY["may_sized_line"][k] * S1] * 2, [y - 0.4, y + 0.4], color=house.INK, lw=1.3, ls=(0, (3, 2)))
axB.set_yticks(yb); axB.set_yticklabels(["first\nreturn", "second\nreturn"], fontsize=C.SMALLEST_PT)
axB.set_xlim(0, 150); axB.set_xticks([0, 50, 100, 150]); axB.set_ylim(-0.6, 1.6)
axB.grid(axis="x", visible=True); axB.grid(axis="y", visible=False)
axB.set_xlabel("return advantage, steps", fontsize=C.SMALLEST_PT + 1)
axB.set_title("(b) for scale: May vs the replication", fontsize=C.SMALLEST_PT + 1.5, loc="left", pad=8)
C.assert_ticks_dont_collide(axB, "x")
h = [Line2D([], [], marker="D", ms=7, color=house.INK, ls="none", label="mean of the 3 pairs"),
     Line2D([], [], marker="o", ms=5.2, mfc=house.PAPER, mec=house.INK, ls="none", label="seed 42"),
     Line2D([], [], marker="s", ms=5.2, mfc=house.PAPER, mec=house.INK, ls="none", label="seed 43"),
     Line2D([], [], marker="^", ms=5.2, mfc=house.PAPER, mec=house.INK, ls="none", label="seed 44"),
     Patch(color=C.BAND, label="registered noise band (± 2 × floored SE)"),
     Line2D([], [], color=C.GREY, lw=1.4, label="± 2 × raw SE between seeds"),
     Patch(color=C.GREY, label="(b) May, one run per agent"), Patch(color=house.INK, label="(b) replication mean"),
     Line2D([], [], color=house.INK, lw=1.3, ls=(0, (3, 2)), label="(b) 'May-sized' line")]
fig.legend(handles=h, loc="lower center", ncol=3, frameon=False, fontsize=C.SMALLEST_PT + 0.5,
           bbox_to_anchor=(0.5, 0.0), handlelength=1.6, columnspacing=1.2)

r3, r5, g3, g5 = (M[a][b] for a, b, _ in READ)
C.record_numbers(STEM, {
    "d3": C.fmt(r3["mean_diff"], sign=True), "d5": C.fmt(r5["mean_diff"], sign=True),
    "d_band": C.fmt(2 * r3["se"]), "g3": C.fmt(g3["mean_diff"], sign=True), "g_band": C.fmt(2 * g3["se"]),
    "d5_raw_band": C.fmt(2 * r5["se_raw"], 2), "d5_mean2": C.fmt(r5["mean_diff"], 2),
    "d5_pos": str(r5["n_pairs_pos"]), "d3_pos": str(r3["n_pairs_pos"]),
    "may_d3": C.fmt(MAY["D"]["3"], 0), "may_d5": C.fmt(MAY["D"]["5"], 0),
    "may_sized_3": C.fmt(MAY["may_sized_line"]["3"] * S1, 0), "may_sized_5": C.fmt(MAY["may_sized_line"]["5"] * S1, 0),
    "verdict": M["overall"]["verdict"],
    "floor_ret": C.fmt(r3["se_floor"]), "floor_forget": C.fmt(g3["se_floor"]),
    "share_of_may_max": C.fmt(100 * max(M["may_comparison"]["reference_200k"]["per_return"][k]["share_of_may"] for k in ("3", "5")), 1)})
C.record_kind(STEM, "training")
C.record_samples(STEM, [
    dict(what="seed pairs", used=3, total=3, note="seeds 42, 43, 44; same-seed ordinary and modulated runs paired"),
    dict(what="readings drawn", used=len(READ), total=len(READ),
         note="the four registered readings; each uses the last 200,000 episodes of a stage")])
C.save(fig, STEM)
