#!/usr/bin/env python3
"""olf_vs_base_dose_response.py - does a neuromodulator change what an injury does to behaviour?

THE QUESTION. At the start of every episode the environment hands the agent an injury drawn
uniformly from 0 to 100 that it did nothing to earn, and the agent has no sensor for it - only a
delayed, smoothed trace on an interoceptive channel. Behaviour that tracks that assigned number is
therefore CAUSED by it. So: does adding a modulator change how much of the agent's hiding depends
on that internal state?

Four grids answer it at once. The same sixteen-cell site x input-slice grid was trained twice at
each of two sensory settings:

    range 0   omnidirectional smell, no direction   MC and GAE_NORM   (2026-09-07)
    range 1   a five-cell directional smell field   MC and GAE_NORM   (2026-09-09)

WHY THE FIRST 25 STEPS AND NOT THE WHOLE EPISODE. The injury heals by about step 28, so a
whole-episode average is mostly measuring an uninjured agent. The sensor-ladder study established
this directly (its figure 14): the same contrast measured over a whole episode collapses, and in
several arms reverses sign. The hiding-drivers GLM's whole-episode model shows exactly that
dilution here - injury coefficients an order of magnitude below the nutrition ones. This figure
uses the window the ladder settled on.

WHAT IT SHOWS. The sign of the response is set by the SENSORY setting, not by the modulator: every
run at range 0 hides LESS when handed a worse injury, every run at range 1 hides MORE, and at both
settings the unmodulated control sits inside the spread of the modulated cells.

INPUT   results/analysis/{nmn_site_grid,nmn_gaenorm_grid,nmn_olf_mc_grid,nmn_olf_gae_grid}/ladderstyle
        plus the ladder's own aggregates, for the two rungs these grids sit on
OUTPUT  $NMN_FIG_ROOT/n01_injury_dose_response_by_range.png
"""
from __future__ import annotations
import json, os, sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))     # scripts/<a>/<b>/<c>.py
sys.path.insert(0, os.path.join(ROOT, "scripts", "analysis", "ladder"))
os.chdir(ROOT)
import _ladder as L                                                     # noqa: E402

FIG = os.environ.get("NMN_FIG_ROOT", "docs/experiments/active/nmn_input_site_grid/figures")

# grid key -> (plain-English name, aggregate root, the ladder rung it sits on)
GRIDS = [
    ("range 0 · MC",  "results/analysis/nmn_site_grid/ladderstyle",     "A_baseline"),
    ("range 0 · GAE", "results/analysis/nmn_gaenorm_grid/ladderstyle",  "A_baseline"),
    ("range 1 · MC",  "results/analysis/nmn_olf_mc_grid/ladderstyle",   "B_olf_only"),
    ("range 1 · GAE", "results/analysis/nmn_olf_gae_grid/ladderstyle",  "B_olf_only"),
]
SITES  = ["t2enc", "t3rnn", "t4act", "t5crt", "t16quad"]
SLICES = ["I", "X", "ALL"]
CELLS  = [f"{s}_{sl}" for s in SITES for sl in SLICES]

# One hue per SENSORY SETTING, because that is the split the figure is about. The return mode is
# the lighter/darker pair within a hue, not a separate colour: it is the second-order question.
COL = {"range 0 · MC": "#2f6f9f", "range 0 · GAE": "#7fb3d5",
       "range 1 · MC": "#a8442a", "range 1 · GAE": "#d98b73"}
CTRL_C, PAPER, ANNO = "#1b1b1d", "#f8f7f5", "#3d3c3a"
plt.rcParams.update({"font.size": 16, "axes.titlesize": 18, "axes.labelsize": 16,
                     "xtick.labelsize": 14, "ytick.labelsize": 14, "legend.fontsize": 13,
                     "figure.facecolor": PAPER, "savefig.facecolor": PAPER,
                     "axes.facecolor": "#ffffff", "axes.axisbelow": True})


def load(root, name):
    p = f"{root}/{name}.json"
    return json.load(open(p)) if os.path.exists(p) else None


def curve(d):
    """Bush hiding (%) in each quarter of the ASSIGNED starting injury, first 25 steps."""
    g = d["grids"]
    return L.rate(g["dw_early"], g["dwt_early"])


def controls(root):
    """However many unmodulated reference runs this cohort has - five, or one, or none."""
    import glob
    return sorted(os.path.splitext(os.path.basename(q))[0]
                  for q in glob.glob(f"{root}/baseline_s*.json"))


def collect():
    out, missing, samples = {}, {}, []
    for name, root, rung in GRIDS:
        cells = {c: load(root, c) for c in CELLS}
        absent = [c for c, d in cells.items() if d is None]
        t1 = load(root, "t1none")
        ctrl = {c: load(root, c) for c in controls(root)}
        if t1 is None:
            sys.exit(f"{name}: no t1none aggregate under {root}")
        out[name] = dict(cells={c: d for c, d in cells.items() if d}, t1none=t1,
                         ctrl={k: v for k, v in ctrl.items() if v}, rung=rung, root=root)
        missing[name] = absent
        n = sum(d["n_episodes"] for d in out[name]["cells"].values()) \
            + t1["n_episodes"] + sum(d["n_episodes"] for d in out[name]["ctrl"].values())
        samples.append(dict(
            what=f"episodes, {name}", used=int(n),
            total=int((len(CELLS) + 1 + len(ctrl)) * 1_000_000),
            note=(f"{len(out[name]['cells'])} modulated cells + t1none + "
                  f"{len(out[name]['ctrl'])} unmodulated reference run(s)"
                  + (f"; ABSENT and still training: {', '.join(absent)}" if absent else ""))))
    return out, missing, samples


def main():
    D, missing, samples = collect()
    x = np.arange(4)
    # wspace is explicit: panel B's row labels are long, and at the default they printed over
    # panel A's plotting area.
    fig, ax = plt.subplots(1, 2, figsize=(20.5, 8.8),
                           gridspec_kw={"width_ratios": [1, 1.25], "wspace": .26})

    # ---- A: the four dose-response curves ------------------------------------------------
    for name, _root, _rung in GRIDS:
        g = D[name]
        for c, d in g["cells"].items():
            ax[0].plot(x, curve(d), color=COL[name], lw=1.0, alpha=.38, zorder=2)
        ax[0].plot(x, curve(g["t1none"]), color=COL[name], lw=3.2, marker="o", ms=7,
                   zorder=4, label=name)
    # NO axhline(0) here. It was added to steady the y-formatter and instead forced the axis to
    # include zero, which squashed two families that live at 20-27% and 32-40% into the upper
    # half of the panel. The y-axis is cropped to the data, and the caption says so.
    ax[0].set_xticks(x); ax[0].set_xticklabels(L.INJ_NAMES)
    ax[0].set_xlabel("initial injury level  (0-100, in four equal quarters)")
    ax[0].set_ylabel("bush hiding over the episode's first 25 steps\n(% of those steps in a bush)")
    ax[0].set_title("A.  What an injury does, at two sensory settings", loc="left", pad=10)
    ax[0].legend(loc="upper left", framealpha=.92,
                 title="thick line + markers = that grid's unmodulated t1none;\n"
                       "thin lines = its fifteen modulated cells", title_fontsize=12)

    # ---- B: the slope per cell, grid by grid ----------------------------------------------
    ypos, labels, seen = [], [], 0
    for gi, (name, _root, _rung) in enumerate(GRIDS):
        g = D[name]
        sl = {c: float(curve(d)[3] - curve(d)[0]) for c, d in g["cells"].items()}
        ctl = float(curve(g["t1none"])[3] - curve(g["t1none"])[0])
        base = seen
        for j, c in enumerate([c for c in CELLS if c in sl]):
            ax[1].barh(base + j, sl[c], color=COL[name], height=.78, edgecolor="none", zorder=3)
        n = len([c for c in CELLS if c in sl])
        # the unmodulated control as a line across that grid's block, not as a bar: it is the
        # thing the bars are compared TO, and a bar would read as one more cell
        ax[1].plot([ctl, ctl], [base - .6, base + n - .4], color=CTRL_C, lw=2.4, zorder=5)
        # Label on whichever side of zero this grid's bars do NOT occupy, so it never prints
        # over a bar. Every cell in a grid shares the sign of its control here, so the opposite
        # side is empty by construction.
        side = -1 if ctl > 0 else +1
        ax[1].annotate(f"t1none {ctl:+.2f}", xy=(side * 5.7, base + (n - 1) / 2), fontsize=12.5,
                       color=CTRL_C, ha="left" if side < 0 else "right", va="center", zorder=6)
        if len(g["ctrl"]) > 1:
            cs = [float(curve(d)[3] - curve(d)[0]) for d in g["ctrl"].values()]
            ax[1].add_patch(plt.Rectangle((min(cs), base - .6), max(cs) - min(cs), n + .2,
                                          facecolor=CTRL_C, alpha=.10, lw=0, zorder=1))
        ypos.append(base + (n - 1) / 2); labels.append(name)
        seen = base + n + 2.2

    ax[1].axvline(0, color=ANNO, lw=1.4, zorder=4)
    ax[1].set_yticks(ypos); ax[1].set_yticklabels(labels)
    ax[1].set_title("B.  Every cell, every grid  (shaded = the span of five control seeds, "
                    "where the cohort has five)", loc="left", pad=10, fontsize=15)
    ax[1].grid(axis="y", visible=False)
    ax[1].invert_yaxis()

    # Folded into the x-axis label rather than annotated under it: the label is already two
    # lines, and a separate annotation at a hand-picked offset printed straight through it.
    ax[1].set_xlabel("a DIFFERENCE, in percentage points:\n"
                     "bush hiding in the highest initial-injury quarter MINUS the lowest\n"
                     "left of zero = hides LESS when injured      right of zero = hides MORE")
    absent = {k: v for k, v in missing.items() if v}
    if absent:
        # Inside panel B, bottom-left: the bottom block's bars are all positive, so left of zero
        # is empty there. Below the axes it printed through a three-line x-label.
        ax[1].annotate("still training, so absent above:\n"
                       + "\n".join(f"{k}: {', '.join(v)}" for k, v in absent.items()),
                       xy=(.015, .02), xycoords="axes fraction", ha="left", va="bottom",
                       fontsize=12, color="#a8442a", zorder=7)

    os.makedirs(FIG, exist_ok=True)
    out = f"{FIG}/n01_injury_dose_response_by_range.png"
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor=PAPER)
    plt.close(fig)
    L.record_samples("n01_injury_dose_response_by_range", samples)
    print(f"wrote {out}")

    print(f"\n{'grid':16}{'t1none':>9}{'cells lo':>10}{'cells hi':>10}{'control inside?':>17}"
          f"{'ctrl seeds':>12}")
    for name, _root, _rung in GRIDS:
        g = D[name]
        sl = [float(curve(d)[3] - curve(d)[0]) for d in g["cells"].values()]
        ctl = float(curve(g["t1none"])[3] - curve(g["t1none"])[0])
        print(f"{name:16}{ctl:>+9.2f}{min(sl):>+10.2f}{max(sl):>+10.2f}"
              f"{('yes' if min(sl) <= ctl <= max(sl) else 'NO'):>17}{len(g['ctrl']):>12}")


if __name__ == "__main__":
    main()
