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

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts", "analysis", "ladder"))
sys.path.insert(0, os.path.join(ROOT, "scripts", "analysis", "style"))
os.chdir(ROOT)

import matplotlib.pyplot as plt                                          # noqa: E402
import house                                                             # noqa: E402
import _ladder as L                                                      # noqa: E402

FIG = os.environ.get("NMN_FIG_ROOT", "docs/experiments/active/nmn_input_site_grid/figures")
GRIDS = [
    ("range 0 · MC",  "results/analysis/nmn_site_grid/ladderstyle"),
    ("range 0 · GAE", "results/analysis/nmn_gaenorm_grid/ladderstyle"),
    ("range 1 · MC",  "results/analysis/nmn_olf_mc_grid/ladderstyle"),
    ("range 1 · GAE", "results/analysis/nmn_olf_gae_grid/ladderstyle"),
]
SITES  = ["t2enc", "t3rnn", "t4act", "t5crt", "t16quad"]
CELLS  = [f"{s}_{sl}" for s in SITES for sl in ("I", "X", "ALL")]
PANELS = [("early",   "A.  Assigned injury, first 25 steps"),
          ("inj",     "B.  Assigned injury, whole episode"),
          ("carried", "C.  Carried injury, whole episode")]
# One hue per olfactory range, the lighter member of each pair being the GAE_NORM twin. This is a
# stated departure from the house series palette, for the same reason as the companion figure: the
# four categories are two PAIRS and the pairing is what the figure is about. It goes through
# house.apply's own `series` argument rather than around it.
PALETTE = [None, None, None, None]        # filled in main(), after house is imported
COL = {}


def slope(d, key):
    """Highest injury quarter minus lowest, in percentage points of bush hiding."""
    g = d["grids"]
    c = L.rate(g[f"dw_{key}"], g[f"dwt_{key}"])
    return float(c[3] - c[0])


def main():
    PALETTE[:] = [house.BLUE, "#7fb0e4", house.RED, "#d98b73"]
    COL.update(dict(zip([g for g, _ in GRIDS], PALETTE)))
    house.apply(series=PALETTE)
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

    fig, ax = plt.subplots(3, 1, figsize=(7.8, 11.4), sharey=True,
                           gridspec_kw={"hspace": .55})
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
                       color=house.INK, lw=2.2, zorder=5)
            if len(ctrl) > 1:
                cs = [slope(d, key) for d in ctrl.values()]
                ax[j].add_patch(plt.Rectangle((min(cs), seen - .6), max(cs) - min(cs),
                                              len(mod) + .2, facecolor=house.INK, alpha=.09,
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
        ax[j].axvline(0, color=house.INK, lw=1.1, zorder=4)
        ax[j].set_title(title)
        ax[j].grid(axis="y", visible=False)
        ax[j].set_yticks(ypos); ax[j].set_yticklabels(labels)
        ax[j].invert_yaxis()
        ax[j].grid(axis="x", visible=True)

    ax[2].set_xlabel("hiding, highest injury quarter minus lowest\n"
                     "(percentage points; left of zero = hides less)")
    house.save(fig, f"{FIG}/n02_window_and_variable")
    used = sum(s["used"] for s in samples); avail = sum(s["total"] for s in samples)
    with open(f"{FIG}/n02_window_and_variable.data.txt", "w") as fh:
        fh.write(f"{used:,} of {avail:,} episodes ({100*used/avail:.1f}%) across 4 grids. "
                 f"Every episode is read three times, once per panel: over its first 25 steps, "
                 f"over the whole episode, and again binned by the injury carried rather than "
                 f"the injury assigned.\n")
    print()

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
