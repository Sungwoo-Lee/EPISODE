#!/usr/bin/env python3
"""injury_dose_response.py - does waking up wounded make this agent hide more, or less?

THE LADDER'S QUESTION, ASKED OF THIS STUDY. At the start of every episode the environment hands the
agent a wound drawn uniformly from 0 to 100 that it did nothing to earn, so behaviour that tracks
that number was CAUSED by it. The sensory study binned bush hiding over each episode's first 25
steps by that dealt wound and found thirteen of its fourteen agents hiding MORE when handed a bigger
one, by +2.6 to +6.7 percentage points. One arm went the other way: `A_baseline`, the agent with
neither directional smell nor useful sight, at -2.34.

WHY THAT MATTERS HERE, AND IT IS NOT A COINCIDENCE. Every run in the neuromodulator study was trained in the
same ENVIRONMENT as `A_baseline` - same world, same sensors, same nociceptor. How far each goes
beyond that differs, and the distinction matters: the five Monte-Carlo reference runs are that agent
exactly (4 differing leaf keys of 251, all of them the run name and logging labels); the GAE
references add the return estimator; the two in-grid controls add a critic learning rate no code
reads; the thirty cells add that plus the modulator. So this study sits on the ladder rung whose
EARLY-WINDOW wound response is negative - a 25-step statement, since twelve of the thirteen rising
arms also go negative over a whole episode. And the replication it supplies is four fresh seeds, not
ten: the ladder ran at seed 42 and so does `baseline_s42`, which is a repeat rather than a replicate.

The 25-step window is the ladder's, not a choice made here: the wound heals, so a whole-episode
average dilutes the dealt dose with whatever the agent's own later behaviour produced. Both windows
are printed so the dilution is visible rather than asserted.

INPUT   results/analysis/{ladder,nmn_site_grid/ladderstyle,nmn_gaenorm_grid/ladderstyle}/<name>.json
OUTPUT  docs/experiments/active/nmn_input_site_grid/figures/g09_injury_dose_response.png
"""
from __future__ import annotations
import json, os, sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts", "analysis", "ladder"))
os.chdir(ROOT)
import _ladder as L                                                     # noqa: E402

MC  = "results/analysis/nmn_site_grid/ladderstyle"
GAE = "results/analysis/nmn_gaenorm_grid/ladderstyle"
FIG = os.environ.get("NMN_FIG_ROOT", "docs/experiments/active/nmn_input_site_grid/figures")
SITES  = ["t2enc", "t3rnn", "t4act", "t5crt", "t16quad"]
SLICES = ["I", "X", "ALL"]
CTRL   = [f"baseline_s{s}" for s in (42, 43, 44, 45, 46)]
CELLS  = [f"{s}_{sl}" for s in SITES for sl in SLICES]
SLICE_NAME = {"I": "body only", "X": "world only", "ALL": "everything"}
C = {"I": "#8a4b8f", "X": "#2f6f9f", "ALL": "#2d6a4f", "ctrl": "#6f6d69", "none": "#1b1b1d"}
PAPER = "#f8f7f5"; ANNO = "#3d3c3a"
LAD = "#9a968f"          # the ladder's other arms: neutral, they are context not data
plt.rcParams.update({"font.size": 17, "axes.titlesize": 19, "axes.labelsize": 17,
                     "xtick.labelsize": 16, "ytick.labelsize": 16, "legend.fontsize": 14,
                     "figure.facecolor": PAPER, "savefig.facecolor": PAPER,
                     "axes.facecolor": "#ffffff", "axes.axisbelow": True})


def curve(d, window="early"):
    g = d["grids"]
    return L.rate(g[f"dw_{window}"], g[f"dwt_{window}"])


def load(root, name):
    return json.load(open(f"{root}/{name}.json"))


def main():
    lad = L.load_all()
    grids = {"MC": {n: load(MC, n) for n in CELLS + ["t1none"] + CTRL},
             "GAE": {n: load(GAE, n) for n in CELLS + ["t1none"] + CTRL}}
    x = np.arange(4)

    fig, ax = plt.subplots(2, 1, figsize=(11.8, 15.2),
                           gridspec_kw={"height_ratios": [1.15, 1], "hspace": .40})

    # ---- LEFT: the curves themselves, this study against the ladder it sits in ----
    for a in L.ARM_ORDER:
        if a == "A_baseline":
            continue
        ax[0].plot(x, curve(lad[a]), color=LAD, lw=1.2, alpha=.55)
    ax[0].plot(x, curve(lad["A_baseline"]), color=ANNO, lw=2.6, ls=(0, (5, 2)),
               label="ladder A_baseline (this study's environment)", zorder=6)
    for n in CELLS:
        ax[0].plot(x, curve(grids["MC"][n]), color=C[n.split("_")[1]], lw=1.0, alpha=.5)
    B = np.array([curve(grids["MC"][n]) for n in CTRL])
    ax[0].fill_between(x, B.min(0), B.max(0), color=C["ctrl"], alpha=.28, lw=0,
                       label="this study, five controls (range)")
    ax[0].plot(x, curve(grids["MC"]["t1none"]), color=C["none"], lw=2.6,
               label="t1none (in-grid control)", zorder=5)
    ax[0].plot([], [], color=LAD, lw=1.6, label="the ladder's 13 better-sensed arms")
    ax[0].set_xticks(x); ax[0].set_xticklabels(L.INJ_NAMES)
    ax[0].set_xlabel("wound the environment dealt at the start,\non the 0-100 scale, in quarters")
    ax[0].set_ylabel("bush hiding over the episode's first 25 steps\n(% of those steps spent in a bush)")
    ax[0].set_title("A bigger wound makes the ladder's agents hide MORE, and these hide LESS",
                    loc="left", fontsize=17)
    ax[0].grid(alpha=.25, lw=.5)
    b, t = ax[0].get_ylim(); ax[0].set_ylim(b - (t - b) * .30, t)
    ax[0].legend(loc="lower left", framealpha=.95, fontsize=13, ncol=2)

    # ---- RIGHT: one number per run - heaviest quarter minus lightest ----
    slope = lambda d: curve(d)[3] - curve(d)[0]
    rows = [
("the ladder's 13\nbetter-sensed arms",
         [(slope(lad[a]), LAD, "o") for a in L.ARM_ORDER if a != "A_baseline"]),
("ladder A_baseline\nthis study's environment",
         [(slope(lad["A_baseline"]), ANNO, "D")]),
("this study, 12\nunmodulated runs",
         [(slope(grids[g][n]), C["ctrl"], "o") for g in grids for n in CTRL]
         + [(slope(grids[g]["t1none"]), C["none"], "*") for g in grids]),
("this study, 30\nmodulated cells",
         [(slope(grids[g][n]), C[n.split("_")[1]], "o") for g in grids for n in CELLS]),
    ]
    n_mod = len(CELLS) * len(grids)
    n_unmod = (1 + len(CTRL)) * len(grids)
    assert rows[2][0].startswith(f"this study, {n_unmod}\n") and rows[3][0].startswith(f"this study, {n_mod}\n"), \
        f"row labels claim counts the data does not have: {n_unmod} unmodulated, {n_mod} modulated"
    assert len(rows[2][1]) == n_unmod and len(rows[3][1]) == n_mod
    for yi, (lab, pts) in enumerate(rows):
        for v, col, mk in pts:
            ax[1].scatter(v, yi + np.random.RandomState(int(abs(v) * 1e4) % 9973).uniform(-.16, .16),
                          s=150 if mk in "D*" else 78, color=col, marker=mk,
                          edgecolor="white", lw=.9, zorder=4)
    ax[1].axvline(0, color=ANNO, lw=1.4, zorder=2)
    ax[1].set_yticks(range(len(rows))); ax[1].set_yticklabels([r[0] for r in rows])
    ax[1].set_ylim(len(rows) - .5, -.75)
    ax[1].set_xlabel("wound sensitivity, in percentage points\n"
                     "hiding in the heaviest wound quarter MINUS the lightest")
    ax[1].set_title("Over this window, every run in this study falls on the same side of zero",
                    loc="left", fontsize=17)
    ax[1].grid(axis="x", alpha=.25, lw=.5)
    ax[1].annotate("hides LESS when wounded", xy=(-3.6, -0.40), ha="center", fontsize=15,
                   color=ANNO, fontweight="bold")
    ax[1].annotate("hides MORE when wounded", xy=(4.8, -0.40), ha="center", fontsize=15,
                   color=ANNO, fontweight="bold")
    ax[1].set_xlim(-7.2, 8.2)

    os.makedirs(FIG, exist_ok=True)
    p = f"{FIG}/g09_injury_dose_response.png"
    fig.savefig(p, dpi=150, bbox_inches="tight", facecolor=PAPER)
    plt.close(fig)
    from PIL import Image
    a = np.asarray(Image.open(p).convert("RGB")).astype(int)
    ink = (np.abs(a - np.array([248, 247, 245])).sum(2) > 40)
    for side, strip in (("left", ink[:, :3]), ("right", ink[:, -3:]),
                        ("top", ink[:3, :]), ("bottom", ink[-3:, :])):
        if strip.sum():
            raise SystemExit(f"g09: ink in the {side} margin - something is clipped")
    print(f"  wrote {p}")

    v13 = [slope(lad[a]) for a in L.ARM_ORDER if a != "A_baseline"]
    print(f"  ladder, 13 better-sensed arms : {min(v13):+.2f} .. {max(v13):+.2f}   "
          f"({sum(1 for q in v13 if q > 0)}/13 positive)")
    print(f"  ladder A_baseline             : {slope(lad['A_baseline']):+.2f}")
    for g in grids:
        c = [slope(grids[g][n]) for n in CTRL]; m = [slope(grids[g][n]) for n in CELLS]
        print(f"  this study {g:4} controls       : {np.mean(c):+.2f} +- {np.std(c, ddof=1):.2f}"
              f"   t1none {slope(grids[g]['t1none']):+.2f}   16 cells {min(m):+.2f} .. {max(m):+.2f}")
    used = sum(float(np.asarray(grids[g][n]["grids"]["dwt_early"], float).sum())
               for g in grids for n in CELLS + ["t1none"] + CTRL)
    tot = 0
    for g, root in (("MC", MC), ("GAE", GAE)):
        for n in CELLS + ["t1none"] + CTRL:
            tot += int(np.load(f"{root}/{n}_episodes.npz")["n_steps"].sum())
    print(f"  this study, 25-step window: {used:,.0f} of {tot:,.0f} step rows ({100*used/tot:.1f}%)")
    allv = [slope(grids[g][n]) for g in grids for n in CELLS + ["t1none"] + CTRL]
    print(f"  every one of the study's {len(allv)} runs is negative: "
          f"{all(q < 0 for q in allv)}   (max {max(allv):+.2f})")
    for g in grids:
        c25 = np.mean([slope(grids[g][n]) for n in CTRL])
        cw = np.mean([curve(grids[g][n], "inj")[3] - curve(grids[g][n], "inj")[0] for n in CTRL])
        print(f"  window check {g:4}: 25 steps {c25:+.2f}   whole episode {cw:+.2f}")


if __name__ == "__main__":
    main()
