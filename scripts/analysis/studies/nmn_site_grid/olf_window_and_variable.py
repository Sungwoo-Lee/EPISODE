#!/usr/bin/env python3
"""olf_window_and_variable.py - is the injury sign-flip real, or an artefact of how it is measured?

The companion figure (`olf_vs_base_dose_response.py`) reports that the sign of the injury response
is set by the sensory range: every run at olfactory range 0 hides LESS when handed a worse injury,
every run at range 1 hides MORE. That claim is worth attacking, because the sensor-ladder study
already showed this exact measurement is fragile - its figure 14 changed the answer twice by
changing nothing about the data, only about how it was read.

So the same three readings are taken here, of all four grids:

  A  ASSIGNED injury, first 25 steps   the honest measurement - the dose is still largely intact
  B  ASSIGNED injury, whole episode    same cause, diluted window; the injury heals by ~step 28,
                                       so most of the average is an uninjured agent
  C  CARRIED injury, whole episode     a different variable, and a CONSEQUENCE of behaviour: an
                                       agent carries a large injury precisely because it was out
                                       in the open near a predator, which is also where it hides

Panel B is what the hiding-drivers GLM's whole-episode model sees, and it is why that model's
injury coefficients came out an order of magnitude below its nutrition ones. Panel C is the trap
the ladder names explicitly: it looks like a much stronger result and is not a causal one.

A finding that survives A and changes in B and C is behaving exactly as the ladder says it should.
A finding that only exists in A is not thereby wrong - A is the honest window - but the reader is
owed all three.

INPUT   results/analysis/{nmn_site_grid,nmn_gaenorm_grid,nmn_olf_mc_grid,nmn_olf_gae_grid}/ladderstyle
OUTPUT  $NMN_FIG_ROOT/n02_window_and_variable.png
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
GRIDS = [
    ("range 0 · MC",  "results/analysis/nmn_site_grid/ladderstyle"),
    ("range 0 · GAE", "results/analysis/nmn_gaenorm_grid/ladderstyle"),
    ("range 1 · MC",  "results/analysis/nmn_olf_mc_grid/ladderstyle"),
    ("range 1 · GAE", "results/analysis/nmn_olf_gae_grid/ladderstyle"),
]
SITES  = ["t2enc", "t3rnn", "t4act", "t5crt", "t16quad"]
CELLS  = [f"{s}_{sl}" for s in SITES for sl in ("I", "X", "ALL")]
PANELS = [("early",    "A.  ASSIGNED injury, first 25 steps\nthe honest window"),
          ("inj",      "B.  ASSIGNED injury, whole episode\nsame cause, diluted window"),
          ("carried",  "C.  CARRIED injury, whole episode\ndifferent variable - a consequence")]
COL = {"range 0 · MC": "#2f6f9f", "range 0 · GAE": "#7fb3d5",
       "range 1 · MC": "#a8442a", "range 1 · GAE": "#d98b73"}
CTRL_C, PAPER, ANNO = "#1b1b1d", "#f8f7f5", "#3d3c3a"
plt.rcParams.update({"font.size": 15, "axes.titlesize": 16, "axes.labelsize": 15,
                     "xtick.labelsize": 13, "ytick.labelsize": 13, "legend.fontsize": 12,
                     "figure.facecolor": PAPER, "savefig.facecolor": PAPER,
                     "axes.facecolor": "#ffffff", "axes.axisbelow": True})


def slope(d, key):
    """Highest injury quarter minus lowest, in percentage points of bush hiding."""
    g = d["grids"]
    c = L.rate(g[f"dw_{key}"], g[f"dwt_{key}"])
    return float(c[3] - c[0])


def main():
    data, samples = {}, []
    for name, root in GRIDS:
        cells = {}
        for c in CELLS + ["t1none"]:
            p = f"{root}/{c}.json"
            if os.path.exists(p):
                cells[c] = json.load(open(p))
        if "t1none" not in cells:
            sys.exit(f"{name}: no t1none aggregate under {root}")
        ctrl = {os.path.basename(q)[:-5]: json.load(open(q))
                for q in sorted(glob.glob(f"{root}/baseline_s*.json"))}
        data[name] = (cells, ctrl)
        n_mod = len([c for c in cells if c != "t1none"])
        samples.append(dict(
            what=f"episodes, {name}",
            used=int(sum(d["n_episodes"] for d in cells.values())
                     + sum(d["n_episodes"] for d in ctrl.values())),
            total=int((len(CELLS) + 1 + len(ctrl)) * 1_000_000),
            note=f"{n_mod} modulated cells + t1none + {len(ctrl)} unmodulated reference run(s); "
                 f"every episode is read three times, once per panel"))

    fig, ax = plt.subplots(1, 3, figsize=(21.0, 7.6), sharey=True,
                           gridspec_kw={"wspace": .10})
    for j, (key, title) in enumerate(PANELS):
        ypos, labels, seen = [], [], 0
        for name, _root in GRIDS:
            cells, ctrl = data[name]
            mod = [c for c in CELLS if c in cells]
            for i, c in enumerate(mod):
                ax[j].barh(seen + i, slope(cells[c], key), color=COL[name], height=.80,
                           edgecolor="none", zorder=3)
            ctl = slope(cells["t1none"], key)
            ax[j].plot([ctl, ctl], [seen - .6, seen + len(mod) - .4],
                       color=CTRL_C, lw=2.2, zorder=5)
            if len(ctrl) > 1:
                cs = [slope(d, key) for d in ctrl.values()]
                ax[j].add_patch(plt.Rectangle((min(cs), seen - .6), max(cs) - min(cs),
                                              len(mod) + .2, facecolor=CTRL_C, alpha=.10,
                                              lw=0, zorder=1))
            ypos.append(seen + (len(mod) - 1) / 2); labels.append(name)
            seen += len(mod) + 2.2
        # Zero must be VISIBLY inside every panel. Panels B and C have values entirely on one
        # side of it, so on autoscaled limits the zero line landed exactly on the panel edge and
        # the "left of zero / right of zero" instruction had nothing to point at. The three
        # panels keep their own scales - their magnitudes differ by 30x and forcing one scale
        # would flatten A and B into nothing - but each is padded to show zero.
        vals = [b.get_width() for b in ax[j].patches if hasattr(b, "get_width")]
        if vals:
            lo, hi = min(min(vals), 0.0), max(max(vals), 0.0)
            pad = max((hi - lo) * 0.08, 0.05)
            ax[j].set_xlim(lo - pad, hi + pad)
        ax[j].axvline(0, color=ANNO, lw=1.4, zorder=4)
        ax[j].set_title(title, loc="left", pad=10)
        ax[j].grid(axis="y", visible=False)
        if j == 0:
            ax[j].set_yticks(ypos); ax[j].set_yticklabels(labels); ax[j].invert_yaxis()

    ax[1].set_xlabel("a DIFFERENCE, in percentage points: bush hiding in the highest "
                     "injury quarter MINUS the lowest\n"
                     "left of zero = hides LESS when injured      right of zero = hides MORE")
    os.makedirs(FIG, exist_ok=True)
    out = f"{FIG}/n02_window_and_variable.png"
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor=PAPER)
    plt.close(fig)
    L.record_samples("n02_window_and_variable", samples)
    print(f"wrote {out}\n")

    print("%-16s%12s%12s%12s   %s" % ("grid", "A early", "B whole", "C carried", "sign of A / B / C"))
    for name, _root in GRIDS:
        cells, _ = data[name]
        row = []
        for key, _t in PANELS:
            vals = [slope(cells[c], key) for c in CELLS if c in cells]
            row.append((float(np.mean(vals)), min(vals), max(vals)))
        sign = " / ".join("+" if r[1] > 0 else ("-" if r[2] < 0 else "mixed") for r in row)
        print("%-16s%+12.2f%+12.2f%+12.2f   %s" % (name, row[0][0], row[1][0], row[2][0], sign))


if __name__ == "__main__":
    main()
