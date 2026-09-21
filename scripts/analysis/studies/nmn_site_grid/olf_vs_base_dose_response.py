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
this directly (its figure 14), and the companion script `olf_window_and_variable.py` shows it again
on these very runs: read over a whole episode, the result below reverses.

WHAT IT SHOWS. The sign of the response is set by the SENSORY setting, not by the modulator: every
run at range 0 hides LESS when handed a worse injury, every run at range 1 hides MORE, and at both
settings the unmodulated control sits inside the spread of the modulated cells.

STYLE. `house.apply()` is called with an explicit four-colour series, which is a stated departure
from the default palette and the reason is the figure's own structure: its four categories are two
PAIRS - one hue per olfactory range, the lighter member of each pair being the GAE_NORM twin - and
the pairing is what the figure is about. Four unrelated series hues would hide the finding. The
override goes through house.apply's own `series` argument rather than around it.

INPUT   results/analysis/{nmn_site_grid,nmn_gaenorm_grid,nmn_olf_mc_grid,nmn_olf_gae_grid}/ladderstyle
OUTPUT  $NMN_FIG_ROOT/n01_injury_dose_response_by_range.{svg,pdf,png} + .data.txt
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

FIG = os.environ.get("NMN_FIG_ROOT", "docs/experiments/active/nmn_input_site_grid/figures_olf")
GRIDS = [("range 0 · MC",  "results/analysis/nmn_site_grid/ladderstyle"),
         ("range 0 · GAE", "results/analysis/nmn_gaenorm_grid/ladderstyle"),
         ("range 1 · MC",  "results/analysis/nmn_olf_mc_grid/ladderstyle"),
         ("range 1 · GAE", "results/analysis/nmn_olf_gae_grid/ladderstyle")]
SITES  = ["t2enc", "t3rnn", "t4act", "t5crt", "t16quad"]
CELLS  = [f"{s}_{sl}" for s in SITES for sl in ("I", "X", "ALL")]
# one hue per olfactory range, lighter member = the GAE_NORM twin; see STYLE above
PALETTE = [house.BLUE, "#7fb0e4", house.RED, "#d98b73"]
COL = dict(zip([g for g, _ in GRIDS], PALETTE))


def load(root, name):
    p = f"{root}/{name}.json"
    return json.load(open(p)) if os.path.exists(p) else None


def curve(d):
    g = d["grids"]
    return L.rate(g["dw_early"], g["dwt_early"])


def controls(root):
    return sorted(os.path.splitext(os.path.basename(q))[0]
                  for q in glob.glob(f"{root}/baseline_s*.json"))


def collect():
    out, missing, used, avail = {}, {}, 0, 0
    for name, root in GRIDS:
        cells = {c: d for c in CELLS if (d := load(root, c))}
        t1 = load(root, "t1none")
        if t1 is None:
            sys.exit(f"{name}: no t1none aggregate under {root}")
        ctrl = {c: d for c in controls(root) if (d := load(root, c))}
        out[name] = dict(cells=cells, t1none=t1, ctrl=ctrl)
        missing[name] = [c for c in CELLS if c not in cells]
        used += sum(d["n_episodes"] for d in cells.values()) + t1["n_episodes"] \
              + sum(d["n_episodes"] for d in ctrl.values())
        avail += (len(CELLS) + 1 + len(ctrl)) * 1_000_000
    return out, missing, used, avail


def main():
    house.apply(series=PALETTE)
    D, missing, used, avail = collect()
    x = np.arange(4)
    fig, ax = plt.subplots(1, 2, figsize=(11.2, 5.2),
                           gridspec_kw={"width_ratios": [1, 1.2], "wspace": .30})

    # ---- A: the four dose-response curves -------------------------------------------------
    for name, _root in GRIDS:
        g = D[name]
        for d in g["cells"].values():
            ax[0].plot(x, curve(d), color=COL[name], lw=0.9, alpha=.34, zorder=2)
        ax[0].plot(x, curve(g["t1none"]), color=COL[name], lw=2.6, marker="o", ms=5,
                   zorder=4, label=name)
    ax[0].set_xticks(x); ax[0].set_xticklabels(L.INJ_NAMES)
    ax[0].set_xlabel("initial injury level (0-100, four equal quarters)")
    ax[0].set_ylabel("bush hiding, first 25 steps (% of those steps)")
    ax[0].set_title("A.  Injury response, by setting")
    house.legend_below(ax[0], ncol=2)

    # ---- B: the slope per cell ------------------------------------------------------------
    ypos, labels, seen = [], [], 0
    for name, _root in GRIDS:
        g = D[name]
        mod = [c for c in CELLS if c in g["cells"]]
        for i, c in enumerate(mod):
            v = float(curve(g["cells"][c])[3] - curve(g["cells"][c])[0])
            ax[1].barh(seen + i, v, color=COL[name], height=.78, edgecolor="none", zorder=3)
        ctl = float(curve(g["t1none"])[3] - curve(g["t1none"])[0])
        ax[1].plot([ctl, ctl], [seen - .6, seen + len(mod) - .4],
                   color=house.INK, lw=1.8, zorder=5)
        if len(g["ctrl"]) > 1:
            cs = [float(curve(d)[3] - curve(d)[0]) for d in g["ctrl"].values()]
            ax[1].add_patch(plt.Rectangle((min(cs), seen - .6), max(cs) - min(cs), len(mod) + .2,
                                          facecolor=house.INK, alpha=.09, lw=0, zorder=1))
        ypos.append(seen + (len(mod) - 1) / 2); labels.append(name)
        seen += len(mod) + 2.2
    ax[1].axvline(0, color=house.INK, lw=1.1, zorder=4)
    ax[1].set_yticks(ypos); ax[1].set_yticklabels(labels)
    ax[1].invert_yaxis()
    ax[1].grid(axis="y", visible=False); ax[1].grid(axis="x", visible=True)
    ax[1].set_xlabel("hiding, highest injury quarter minus lowest\n"
                     "(percentage points; left of zero = hides less)")
    ax[1].set_title("B.  Every cell, every grid")
    fig.subplots_adjust(bottom=0.30, top=0.90)
    house.save(fig, f"{FIG}/n01_injury_dose_response_by_range", column_px=688)

    absent = sorted(c for v in missing.values() for c in v)
    with open(f"{FIG}/n01_injury_dose_response_by_range.data.txt", "w") as fh:
        fh.write(f"{used:,} of {avail:,} episodes ({100*used/avail:.1f}%) across 4 grids: "
                 f"15 modulated cells, 1 in-grid unmodulated control and, for the two range-0 "
                 f"grids only, 5 further unmodulated reference seeds each. Every episode is read "
                 f"once, over its first 25 steps."
                 + (f" Absent: {', '.join(absent)}.\n" if absent else "\n"))

    print(f"\n{'grid':16}{'t1none':>9}{'cells lo':>10}{'cells hi':>10}{'inside?':>10}{'ctrl':>7}")
    for name, _root in GRIDS:
        g = D[name]
        sl = [float(curve(d)[3] - curve(d)[0]) for d in g["cells"].values()]
        ctl = float(curve(g["t1none"])[3] - curve(g["t1none"])[0])
        print(f"{name:16}{ctl:>+9.2f}{min(sl):>+10.2f}{max(sl):>+10.2f}"
              f"{('yes' if min(sl) <= ctl <= max(sl) else 'NO'):>10}{len(g['ctrl']):>7}")


if __name__ == "__main__":
    main()
