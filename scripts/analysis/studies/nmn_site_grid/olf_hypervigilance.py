#!/usr/bin/env python3
"""olf_hypervigilance.py - does an injury make the agent treat a HARMLESS cue as a threat?

THE CLAIM BEING TESTED, AND WHY IT IS NARROW. That an injured animal hides more is ordinary
caution, and Figure n01 already shows it. Hypervigilance is a stronger and more specific claim:
that being injured shifts the agent's CRITERION, so an ambiguous and harmless cue starts driving
the same defence a real threat does. A rabbit cannot hurt the agent - it is a false alarm by
construction - so the test is whether an injury raises the rabbit response BY MORE than it raises
the predator response. If both rise equally the agent has simply become more cautious, which is
not the claim.

    rabbit shift    = P(in bush | rabbit 1-2 cells) - P(in bush | rabbit 6+ cells)
                      measured in the HIGHEST starting-injury quarter, minus the same contrast
                      measured in the LOWEST
    predator shift  = the same thing for a predator - the control
    hypervigilance  = rabbit shift MINUS predator shift, a difference of two differences

The starting injury is drawn uniformly at random before the agent acts and the agent has no sensor
for it, so splitting on it is causal. Distance is NOT randomised - the agent chose where to walk -
so the near-versus-far contrast is descriptive; it is the injury split across it that carries the
causal reading.

Asked of all four grids: the site x input-slice grid trained under MC and GAE_NORM at each of two
olfactory ranges. The question for this study is whether a modulator - and especially one reading
the INTEROCEPTIVE slice, which is the one that can see the injury signal at all - produces a shift
the unmodulated control does not.

INPUT   results/analysis/{nmn_site_grid,nmn_gaenorm_grid,nmn_olf_mc_grid,nmn_olf_gae_grid}/ladderstyle
OUTPUT  $NMN_FIG_ROOT/n03_hypervigilance.png
"""
from __future__ import annotations
import glob, json, os, sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts", "analysis", "ladder"))
os.chdir(ROOT)
import _ladder as L                                                     # noqa: E402

FIG = os.environ.get("NMN_FIG_ROOT", "docs/experiments/active/nmn_input_site_grid/figures")
GRIDS = [("range 0 · MC",  "results/analysis/nmn_site_grid/ladderstyle"),
         ("range 0 · GAE", "results/analysis/nmn_gaenorm_grid/ladderstyle"),
         ("range 1 · MC",  "results/analysis/nmn_olf_mc_grid/ladderstyle"),
         ("range 1 · GAE", "results/analysis/nmn_olf_gae_grid/ladderstyle")]
SITES  = ["t2enc", "t3rnn", "t4act", "t5crt", "t16quad"]
SLICES = ["I", "X", "ALL"]
CELLS  = [f"{s}_{sl}" for s in SITES for sl in SLICES]
LOW, HIGH = (0,), (3,)                      # lightest and heaviest starting-injury quarters
# Colour by INPUT SLICE here, not by grid: the question is whether the modulator's input matters,
# and the interoceptive slice is the one that can see the injury signal at all.
C = {"I": "#8a4b8f", "X": "#2f6f9f", "ALL": "#2d6a4f"}
SLICE_NAME = {"I": "body only (interoceptive)", "X": "world only", "ALL": "everything"}
CTRL_C, PAPER, ANNO = "#1b1b1d", "#f8f7f5", "#3d3c3a"
plt.rcParams.update({"font.size": 15, "axes.titlesize": 16.5, "axes.labelsize": 15,
                     "xtick.labelsize": 13, "ytick.labelsize": 13, "legend.fontsize": 12.5,
                     "figure.facecolor": PAPER, "savefig.facecolor": PAPER,
                     "axes.facecolor": "#ffffff", "axes.axisbelow": True})


def shifts(d):
    """(rabbit shift, predator shift, hypervigilance) in percentage points, for one run."""
    g = d["grids"]
    rab = (L.proximity_effect(g["rd_bush"], g["rd_tot"], HIGH)
           - L.proximity_effect(g["rd_bush"], g["rd_tot"], LOW))
    pre = (L.proximity_effect(g["pd_bush"], g["pd_tot"], HIGH)
           - L.proximity_effect(g["pd_bush"], g["pd_tot"], LOW))
    return float(rab), float(pre), float(rab - pre)


def main():
    data, samples = {}, []
    for name, root in GRIDS:
        cells = {c: json.load(open(f"{root}/{c}.json"))
                 for c in CELLS + ["t1none"] if os.path.exists(f"{root}/{c}.json")}
        ctrl = {os.path.basename(q)[:-5]: json.load(open(q))
                for q in sorted(glob.glob(f"{root}/baseline_s*.json"))}
        if "t1none" not in cells:
            sys.exit(f"{name}: no t1none aggregate under {root}")
        data[name] = (cells, ctrl)
        samples.append(dict(
            what=f"episodes, {name}",
            used=int(sum(d["n_episodes"] for d in cells.values())
                     + sum(d["n_episodes"] for d in ctrl.values())),
            total=int((len(CELLS) + 1 + len(ctrl)) * 1_000_000),
            note="only the steps with an animal 1-2 or 6+ cells away enter the contrast; the "
                 "3-5 bins are excluded by construction, and each contrast is taken inside one "
                 "starting-injury quarter"))

    fig, ax = plt.subplots(1, 2, figsize=(19.0, 8.2), gridspec_kw={"width_ratios": [1.15, 1],
                                                                   "wspace": .22})
    # ---- A: the two shifts against each other -------------------------------------------
    for name, _r in GRIDS:
        cells, _ = data[name]
        for c in [c for c in CELLS if c in cells]:
            r, p, _ = shifts(cells[c])
            ax[0].scatter(p, r, s=95, color=C[c.split("_")[1]], edgecolor="white", lw=.9, zorder=4)
        r, p, _ = shifts(cells["t1none"])
        ax[0].scatter(p, r, s=260, color=CTRL_C, marker="*", zorder=6)
    lim = np.array(ax[0].get_xlim() + ax[0].get_ylim())
    lo, hi = float(lim.min()), float(lim.max())
    ax[0].plot([lo, hi], [lo, hi], color=ANNO, lw=1.2, ls=(0, (5, 3)), zorder=2)
    ax[0].annotate("equal shift: injury made both\nresponses rise the same amount,\nwhich is "
                   "caution, not hypervigilance", xy=(hi, lo), ha="right", va="bottom",
                   fontsize=12.5, color=ANNO)
    ax[0].axhline(0, color=ANNO, lw=.9, zorder=1); ax[0].axvline(0, color=ANNO, lw=.9, zorder=1)
    ax[0].set_xlabel("shift in the PREDATOR response  (percentage points)\n"
                     "heaviest starting-injury quarter MINUS lightest")
    ax[0].set_ylabel("shift in the RABBIT response  (percentage points)\n"
                     "heaviest starting-injury quarter MINUS lightest")
    # Say that this panel POOLS the grids. Colour here encodes the modulator's input slice, not
    # the grid, so without this a reader cannot tell which of the four a point came from - and
    # the two ranges occupy visibly different parts of the plane. Panel B separates them.
    ax[0].set_title("A.  Above the dashed line = the harmless cue moved more\n"
                    "all four grids pooled; colour is the modulator's input, not the grid",
                    loc="left", pad=10, fontsize=15)
    hnd = [plt.Line2D([], [], ls="", marker="o", ms=10, color=C[s],
                      label=f"modulator reads {SLICE_NAME[s]}") for s in SLICES] + \
          [plt.Line2D([], [], ls="", marker="*", ms=15, color=CTRL_C,
                      label="t1none (unmodulated), one per grid")]
    ax[0].legend(handles=hnd, loc="upper left", framealpha=.93)

    # ---- B: hypervigilance per cell, grid by grid -----------------------------------------
    ypos, labels, seen = [], [], 0
    for name, _r in GRIDS:
        cells, ctrl = data[name]
        mod = [c for c in CELLS if c in cells]
        for i, c in enumerate(mod):
            ax[1].barh(seen + i, shifts(cells[c])[2], color=C[c.split("_")[1]], height=.80,
                       edgecolor="none", zorder=3)
        ctl = shifts(cells["t1none"])[2]
        ax[1].plot([ctl, ctl], [seen - .6, seen + len(mod) - .4], color=CTRL_C, lw=2.2, zorder=5)
        if len(ctrl) > 1:
            cs = [shifts(d)[2] for d in ctrl.values()]
            ax[1].add_patch(plt.Rectangle((min(cs), seen - .6), max(cs) - min(cs), len(mod) + .2,
                                          facecolor=CTRL_C, alpha=.10, lw=0, zorder=1))
        ypos.append(seen + (len(mod) - 1) / 2); labels.append(name)
        seen += len(mod) + 2.2
    ax[1].axvline(0, color=ANNO, lw=1.4, zorder=4)
    ax[1].set_yticks(ypos); ax[1].set_yticklabels(labels); ax[1].invert_yaxis()
    ax[1].grid(axis="y", visible=False)
    ax[1].set_xlabel("HYPERVIGILANCE: a difference of two differences, in percentage points\n"
                     "(rabbit shift) MINUS (predator shift)\n"
                     "right of zero = injury moved the harmless cue more than the real threat")
    ax[1].set_title("B.  Every cell  (black line = that grid's unmodulated run;\n"
                    "shading = the span of five control seeds, where the cohort has five)",
                    loc="left", pad=10, fontsize=14.5)

    os.makedirs(FIG, exist_ok=True)
    out = f"{FIG}/n03_hypervigilance.png"
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor=PAPER)
    plt.close(fig)
    L.record_samples("n03_hypervigilance", samples)
    print(f"wrote {out}\n")

    print("%-16s%11s%11s%11s%11s%11s" % ("grid", "t1none HV", "cells lo", "cells hi",
                                          "inside?", "n>0 of 15"))
    for name, _r in GRIDS:
        cells, _ = data[name]
        hv = [shifts(cells[c])[2] for c in CELLS if c in cells]
        ctl = shifts(cells["t1none"])[2]
        inside = "yes" if min(hv) <= ctl <= max(hv) else "NO"
        print("%-16s%+11.2f%+11.2f%+11.2f%11s%11d" %
              (name, ctl, min(hv), max(hv), inside, sum(1 for v in hv if v > 0)))


if __name__ == "__main__":
    main()
