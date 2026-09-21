#!/usr/bin/env python3
"""olf_contextual_fraction.py - how much of the modulator's output actually varies with context?

THE QUESTION THIS ANSWERS, AND WHY IT COMES LAST. Three behaviour measures find no effect of the
modulator: the injury dose-response, the timing of the response, and the criterion shift. A null
across three measures invites the obvious objection - that the measures are too blunt. This figure
answers it from the other side, by looking at what the modulator EMITS rather than at what the
agent does.

THE QUANTITY. A FiLM modulator multiplies a layer's activations by a gain and adds an offset, both
produced per step from what the agent senses. Its gain therefore varies in two ways at once: across
UNITS (unit 7 is scaled differently from unit 40, always) and across TIME within a unit (unit 7 is
scaled differently now than a moment ago, because the agent senses something different). Only the
second is modulation in any interesting sense; the first is a fixed reparameterisation that a plain
weight matrix could have absorbed at training time. The variance splits exactly:

    Var over units and time = Var_units( mean over time )  +  mean over units( Var over time )

and rho is the second term over the total - the CONTEXTUAL FRACTION. rho near 1 means the gain is
mostly a live response to what is being sensed. rho near 0 means the modulator has collapsed into a
constant rescaling wearing the shape of a modulator.

WHAT IT SHOWS. rho sits between 0.08 and 0.15 in every one of the four grids, so roughly 85-92% of
the gain's spread is a fixed per-unit rescaling. There is very little context-dependence in the
signal for the behaviour measures to have found. Widening the observation from 27 to 47 numbers did
not change this - if anything the extended-olfaction MC grid is the least contextual of the four.

INPUT   results/analysis/nmn_representation/mod_distribution/distributions.csv        (range 0)
        results/analysis/nmn_representation/mod_distribution_olf/distributions.csv    (range 1)
OUTPUT  $NMN_FIG_ROOT/n04_contextual_fraction.{svg,pdf,png} + .data.txt
"""
from __future__ import annotations
import csv, os, sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts", "analysis", "style"))
os.chdir(ROOT)

import matplotlib.pyplot as plt                                          # noqa: E402
import house                                                             # noqa: E402

FIG = os.environ.get("NMN_FIG_ROOT", "docs/experiments/active/nmn_input_site_grid/figures_olf")
SRC = {"nmnsite":    ("range 0 · MC",  "results/analysis/nmn_representation/mod_distribution/distributions.csv"),
       "nmngaenorm": ("range 0 · GAE", "results/analysis/nmn_representation/mod_distribution/distributions.csv"),
       "olfmc":      ("range 1 · MC",  "results/analysis/nmn_representation/mod_distribution_olf/distributions.csv"),
       "olfgae":     ("range 1 · GAE", "results/analysis/nmn_representation/mod_distribution_olf/distributions.csv")}
ORDER = ["range 0 · MC", "range 0 · GAE", "range 1 · MC", "range 1 · GAE"]
PALETTE = None          # set in main(), after house is imported


def collect():
    out = {}
    for grid, (label, path) in SRC.items():
        if not os.path.exists(path):
            sys.exit(f"{label}: no distributions.csv at {path} - run scripts/analysis/nmn/"
                     f"run_mod_distribution.py --grids {grid}")
        vals = [float(r["gamma_rho"]) for r in csv.DictReader(open(path))
                if r.get("grid") == grid and r.get("gamma_rho") not in (None, "", "nan")]
        if not vals:
            sys.exit(f"{label}: no gamma_rho rows for grid {grid!r} in {path}")
        out[label] = np.array(vals, float)
    return out


def main():
    global PALETTE
    PALETTE = [house.BLUE, "#7fb0e4", house.RED, "#d98b73"]
    house.apply(series=PALETTE)
    col = dict(zip(ORDER, PALETTE))
    D = collect()

    fig, ax = plt.subplots(figsize=(7.8, 4.6))
    for i, label in enumerate(ORDER):
        v = D[label]
        # every run-site as a point, jittered only along the category axis so none hides another
        rng = np.random.default_rng(0)
        ax.scatter(v, np.full(len(v), i) + rng.uniform(-.17, .17, len(v)),
                   s=26, color=col[label], alpha=.75, edgecolor="none", zorder=3)
        m = float(np.median(v))
        ax.plot([m, m], [i - .26, i + .26], color=house.INK, lw=2.0, zorder=5)
        # BESIDE the bar, not under it. Printed below, the bar's lower end ran through the digits
        # and the reader saw "0.1|40". The caption says where the number is; keep the two in step.
        ax.annotate(f"median {m:.3f}", xy=(m + .012, i - .30), ha="left", va="center",
                    fontsize=house.FS_LABEL, color=house.INK, zorder=6)
    ax.set_yticks(range(len(ORDER))); ax.set_yticklabels(ORDER)
    ax.invert_yaxis()
    ax.set_xlim(0, 0.45)
    ax.set_xlabel("contextual fraction of the gain (0 = a fixed rescaling, 1 = all context)")
    ax.set_title("How much of the modulator's gain varies with context")
    ax.grid(axis="y", visible=False); ax.grid(axis="x", visible=True)
    fig.subplots_adjust(left=0.22, bottom=0.20, top=0.88)
    house.save(fig, f"{FIG}/n04_contextual_fraction", column_px=688)

    n = sum(len(v) for v in D.values())
    with open(f"{FIG}/n04_contextual_fraction.data.txt", "w") as fh:
        fh.write(f"{n} run-and-site measurements, all {n} of {n} drawn (100%): the 15 modulated "
                 f"cells of each of 4 grids, each contributing one value per FiLM site it switches "
                 f"on. Each value is computed from a 128-episode greedy replay of that agent, not "
                 f"from the 1,000,000-episode behaviour store \u2014 the modulator's own output is not "
                 f"recorded in that store.\n")

    print(f"\n{'grid':16}{'n':>5}{'median':>9}{'min':>9}{'max':>9}")
    for label in ORDER:
        v = D[label]
        print(f"{label:16}{len(v):>5}{np.median(v):>9.3f}{v.min():>9.3f}{v.max():>9.3f}")


if __name__ == "__main__":
    main()
