"""FIGURE r07 — May replication, frozen-agent retention test: each stage-end checkpoint played, without training,
in the hunting world; how much the two harmless stages cost; and the modulated-minus-ordinary difference in
that loss per seed pair.

Source: results/analysis/continual_worlds/retention_mayrep_readout.json (MAY_DOUBLE_RETURN_REPLICATION.md 5.6):
per run, `policies.greedy.A` = hunting-world survival of the five stage-end checkpoints (2,000 episodes each),
`cap_active` = share of those episodes at the 500-step cap; `verdicts.{greedy,sampled}.H_zeroshot.ZA_2 / ZA_4`
= per-pair (Z_mod - Z_ord) where Z_j = A_j - A_{j-1} is the loss over harmless stage j, the mean, the
between-seed SE and the registered result (|mean| > 2 x SE). Greedy is the registered policy; sampled is
the robustness run.

Two post-hoc scales are drawn and labelled as such (plan-reviewer finding A2 on the May verdict):
  * a three-seed 95 % interval, mean +/- t(0.975, 2 d.f.) x SE, which is wider than the registered 2 x SE;
  * the 'May-sized' advantage = (1 - May's forgetting ratio) x the ordinary agent's mean loss, with May's
    ratios from mayrep_readout.json (`may_comparison.may.forget_ratio`, k = 3 for harmless stage 1 and
    k = 5 for harmless stage 2, the returns that follow them).
"""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from scipy import stats
import _common as C

house = C.house; house.apply()
STEM = "r07_retention"
R = C.load(C.RETENTION)
MAY = C.load(C.MAYREP)["mayrep"]["may_comparison"]["may"]
assert R["registered_policy"] == "greedy"
LS = {42: "-", 43: (0, (5, 2)), 44: (0, (1.5, 1.5))}

fig = plt.figure(figsize=(9.9, 5.8))
axA = fig.add_axes([0.08, 0.27, 0.40, 0.62])
axB = fig.add_axes([0.66, 0.27, 0.32, 0.62])
caps_after_harmless = []
for r in R["runs"]:
    g = r["policies"]["greedy"]
    assert len(g["A"]) == 5
    axA.plot(range(1, 6), g["A"], color=C.AGENT_COL[r["agent"]], ls=LS[r["seed"]], lw=1.4, marker=C.SEED_MARKER[r["seed"]], ms=6.8)
    caps_after_harmless += [g["cap_active"][1], g["cap_active"][3]]
axA.axhline(500, color=C.GREY, lw=2.2, zorder=1)
axA.set_xticks(range(1, 6))
axA.set_xticklabels(["end 1\nhunting", "end 2\nharmless", "end 3\nhunting", "end 4\nharmless", "end 5\nhunting"],
                    fontsize=C.SMALLEST_PT)
axA.set_ylim(250, 510); axA.set_yticks([250, 300, 350, 400, 450, 500])
axA.set_ylabel("hunting-world survival (steps per episode)", fontsize=C.SMALLEST_PT + 1)
axA.set_xlabel("frozen checkpoint (end of stage)", fontsize=C.SMALLEST_PT + 1)
axA.set_title("(a) frozen checkpoints in the hunting world", fontsize=C.SMALLEST_PT + 1.5, loc="left", pad=8)

tq = stats.t.ppf(0.975, 2)
out = {}
ys = {"ZA_2": 1, "ZA_4": 0}
for key, y in ys.items():
    gv, sv = R["verdicts"]["greedy"]["H_zeroshot"][key], R["verdicts"]["sampled"]["H_zeroshot"][key]
    assert gv["n_pairs"] == 3 and gv["verdict"] == "inside noise"
    k_may = {"ZA_2": "3", "ZA_4": "5"}[key]
    may_adv = (1 - MAY["forget_ratio"][k_may]) * abs(gv["mean_ord"])
    axB.plot([gv["mean_diff"] - tq * gv["se"], gv["mean_diff"] + tq * gv["se"]], [y - 0.25] * 2, color=C.GREY, lw=1.4)
    axB.plot([gv["mean_diff"] - 2 * gv["se"], gv["mean_diff"] + 2 * gv["se"]], [y] * 2, color=C.BAND, lw=9,
             solid_capstyle="butt", zorder=1)
    for i, (p, mk) in enumerate(zip(gv["pairs"], [C.SEED_MARKER[q["seed"]] for q in gv["pairs"]])):
        axB.plot([p["ZA"]], [y + 0.36 - 0.1 * i], mk, ms=8, mec=house.INK, mew=1.1,
                 mfc=house.INK if p["beyond_eval_noise"] else house.PAPER, zorder=3)
    axB.plot([gv["mean_diff"]], [y], "D", ms=7, color=house.INK, zorder=4)
    axB.plot([sv["mean_diff"]], [y - 0.1], "D", ms=6, mfc=house.PAPER, mec=house.INK, mew=1.2, zorder=4)
    axB.plot([may_adv] * 2, [y - 0.38, y + 0.38], color=C.GREY, lw=1.4, ls="-.")
    out[key] = dict(g=gv, s=sv, may=may_adv, t_hi=gv["mean_diff"] + tq * gv["se"])
axB.axvline(0, color=C.GREY, lw=0.9)
axB.set_yticks([1, 0]); axB.set_yticklabels(["harmless\nstage 1", "harmless\nstage 2"], fontsize=C.SMALLEST_PT)
axB.set_ylim(-0.6, 1.6); axB.set_xlim(-60, 120); axB.set_xticks([-50, 0, 50, 100])
axB.grid(axis="x", visible=True); axB.grid(axis="y", visible=False)
axB.set_xlabel("steps less lost by the modulated agent", fontsize=C.SMALLEST_PT + 1)
axB.set_title("(b) modulated minus ordinary loss", fontsize=C.SMALLEST_PT + 1.5, loc="left", pad=8)
C.assert_ticks_dont_collide(axB, "x")
h = [Line2D([], [], color=C.ORD, lw=2, label="ordinary"), Line2D([], [], color=C.MOD, lw=2, label="modulated"),
     Line2D([], [], color=house.INK, ls=LS[42], lw=1.4, marker=C.SEED_MARKER[42], ms=8.4, mfc=house.PAPER, label="seed 42 (a line, b marker)"),
     Line2D([], [], color=house.INK, ls=LS[43], lw=1.4, marker=C.SEED_MARKER[43], ms=8.4, mfc=house.PAPER, label="seed 43 (a line, b marker)"),
     Line2D([], [], color=house.INK, ls=LS[44], lw=1.4, marker=C.SEED_MARKER[44], ms=8.4, mfc=house.PAPER, label="seed 44 (a line, b marker)"),
     Line2D([], [], color=C.GREY, lw=2.2, label="500-step cap"),
     Line2D([], [], marker="D", ms=7, color=house.INK, ls="none", label="mean, most-likely action"),
     Line2D([], [], marker="D", ms=6, mfc=house.PAPER, mec=house.INK, ls="none", label="mean, sampled actions"),
     Patch(color=C.BAND, label="registered band, ± 2 × SE"),
     Line2D([], [], color=C.GREY, lw=1.4, label="3-seed 95 % interval (post hoc)"),
     Line2D([], [], color=C.GREY, lw=1.4, ls="-.", label="May-sized advantage"),
     Line2D([], [], marker=C.SEED_MARKER[42], ms=8.4, color=house.INK, ls="none", label="filled: pair beyond test noise")]
fig.legend(handles=h, loc="lower center", ncol=4, frameon=False, fontsize=C.SMALLEST_PT + 0.2,
           bbox_to_anchor=(0.5, 0.0), handlelength=1.8, columnspacing=1.0)

z2, z4 = out["ZA_2"], out["ZA_4"]
C.record_numbers(STEM, {
    "cap_after_min": C.fmt(100 * min(caps_after_harmless), 0), "cap_after_max": C.fmt(100 * max(caps_after_harmless), 0),
    "z2_ord": C.fmt(z2["g"]["mean_ord"]), "z2_mod": C.fmt(z2["g"]["mean_mod"]),
    "z4_ord": C.fmt(z4["g"]["mean_ord"]), "z4_mod": C.fmt(z4["g"]["mean_mod"]),
    "loss_approx": C.fmt(round(-np.mean([z2["g"]["mean_ord"], z2["g"]["mean_mod"],
                                          z4["g"]["mean_ord"], z4["g"]["mean_mod"]]), -1), 0),
    "za2": C.fmt(z2["g"]["mean_diff"], sign=True), "za2_abs": C.fmt(abs(z2["g"]["mean_diff"])), "za4_abs": C.fmt(abs(z4["g"]["mean_diff"])),
    "za4": C.fmt(z4["g"]["mean_diff"], sign=True), "za4_se": C.fmt(z4["g"]["se"]),
    "za2_t_hi": C.fmt(z2["t_hi"], 0, sign=True), "za4_t_hi": C.fmt(z4["t_hi"], 0, sign=True),
    "may2": C.fmt(z2["may"], 0), "may4": C.fmt(z4["may"], 0), "t_q": C.fmt(tq),
    "za4_pairs": ", ".join(C.fmt(p["ZA"], 1, sign=True) for p in z4["g"]["pairs"]),
    "za2_samp": C.fmt(z2["s"]["mean_diff"], sign=True), "za4_samp": C.fmt(z4["s"]["mean_diff"], sign=True)})
C.record_kind(STEM, "evaluation")
C.record_samples(STEM, [
    dict(what="frozen checkpoints", used=5 * len(R["runs"]), total=5 * len(R["runs"]), note="5 stage ends per run, 6 runs; 2,000 hunting-world test episodes each"),
    dict(what="seed pairs in panel b", used=3, total=3, note="same-seed ordinary and modulated runs")])
C.save(fig, STEM)
