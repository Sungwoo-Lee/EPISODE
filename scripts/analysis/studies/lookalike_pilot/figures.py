#!/usr/bin/env python3
"""figures.py - figures of the 'Lookalike Animals Pilot Results' page.

Four agents trained in the lookalike-animals world (design: docs/experiments/active/hypervigilance/
LOOKALIKE_ANIMALS_CLOSE_POUNCE.md) and the twelve level-05 agents of the fast-heal replication, each
tested in the injury-grid scenes (no temperature; starting injury 0..90) twice: with the training
world's bush healing, and with healing switched off in the test scene only (behavior_probes/no_healing/).

  curves  --group G   bush dwell against starting injury: no animal vs wandering rabbit, healing on | off
  extra   --group G   the rabbit's extra bush dwell (rabbit minus no animal) at each starting injury
  train   --group G   the injury-10 contrast at every tested checkpoint across training
Groups: lookalike (4 runs), replication (6 level-05 replication runs), fixedstart (6 level-05 fixed-start
runs); --group all draws the three in one process. The extra and train figures share one y-range across the
three groups, so the groups can be compared by eye.

    $P scripts/analysis/studies/lookalike_pilot/figures.py --fig-dir <dir> --figure curves|extra|train --group G
"""
from __future__ import annotations

import argparse
import functools
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "f7b_across_runs"))
import highlight as HL  # noqa: E402  (series, grid_row, K, C, H, FG, LO_M, HI_M, SPACING_M)

H, K, C, FG = HL.H, HL.K, HL.C, HL.FG
AV = "results/eval/avoidance"
INJ = [f"{i:02d}" for i in range(0, 100, 10)]
X = [int(i) for i in INJ]
NONE_COL, RABBIT_COL = "#8a8f98", H.ORANGE
# healing on/off get their own colours and markers: grey circles and orange squares already mean
# "no animal" and "rabbit" in the curves figures
HEAL_COL = {"on": H.GREEN, "off": H.BLUE}
HEAL_MK = {"on": "^", "off": "D"}
HEAL_NAME = {"on": "healing on (as in training)", "off": "healing off (test only)"}
SEEDS = {"lookalike": (42, 43), "replication": (42, 43, 44), "fixedstart": (42, 43, 44)}
PREFIX = {"replication": "l05", "fixedstart": "l05fix"}   # run-label prefix in the healrep result folders
GROUP_NAME = {"lookalike": "lookalike-animals agents", "replication": "level-05 replication agents",
              "fixedstart": "level-05 fixed-start agents"}


def leaf(group, heal, agent, seed):
    if group == "lookalike":
        base = "metrics_history_rppo_lookalike" + ("_noheal" if heal == "off" else "")
        return f"{AV}/{base}/grid/lookalike_{agent}_s{seed}"
    g = PREFIX[group]
    if heal == "on":
        return f"{AV}/metrics_history_rppo_healrep/{g}_grid/{g}_{agent}_s{seed}"
    return f"{AV}/metrics_history_rppo_healrep_noheal/grid/{g}_{agent}_s{seed}"


def runs(group):
    return [(a, s) for a in ("ordinary", "modulated") for s in SEEDS[group]]


@functools.lru_cache(maxsize=None)
def _series(lf, scene, inj):
    return HL.series(lf, scene, inj)


def ser(lf, scene, inj, on_grid=True):
    v = _series(lf, scene, inj)
    if v is None:
        raise SystemExit(f"missing test result: {lf} {scene} injury {inj}")
    return K.on_grid(v, HL.LO_M, HL.HI_M, HL.SPACING_M) if on_grid else v


def prof(v):
    p = C.P.W.window_profile(np.asarray(v, float), windows=[len(v)]).iloc[0]
    return p["mean"], p["lo"], p["hi"]


def band(ax, x, m, lo, hi, col, mk="o", label=None, filled=True):
    ax.fill_between(x, lo, hi, color=col, alpha=0.14, lw=0)
    for e in (lo, hi):
        ax.plot(x, e, color=col, lw=0.7, ls=(0, (3, 2)))
    ax.plot(x, m, color=col, lw=2.0, marker=mk, ms=4.5, mfc=col if filled else H.PAPER, mew=1.3, zorder=3, label=label)


def grid_layout(group):
    import matplotlib.pyplot as plt
    rr = runs(group)
    ns = len(SEEDS[group])
    return rr, ns, plt


def fig_curves(group):
    rr, ns, plt = grid_layout(group)
    fig, axs = plt.subplots(len(rr), 2, figsize=(8.4, 2.35 * len(rr) + 1.0), sharex=True, sharey=True)
    rows = []
    for r_, (a, s) in enumerate(rr):
        for c_, heal in enumerate(("on", "off")):
            ax, lf = axs[r_, c_], leaf(group, heal, a, s)
            for sc, col, mk, filled, name in (("none", NONE_COL, "o", False, "no animal"),
                                              ("rabbitwander", RABBIT_COL, "s", True, "wandering rabbit")):
                st = [prof(ser(lf, sc, i)) for i in INJ]
                band(ax, X, *zip(*st), col, mk, filled=filled)
                v = ser(lf, sc, "10")
                rows.append(HL.grid_row(f"{a} s{s}, {HEAL_NAME[heal]}, {name}: checkpoints per starting injury", v, lf))
            if r_ == 0:
                ax.set_title(HEAL_NAME[heal], loc="left", fontsize=H.FS_BODY)
            if c_ == 0:
                ax.set_ylabel(f"{a}, seed {s}\nbush dwell (%)", fontsize=H.FS_LABEL)
            if r_ == len(rr) - 1:
                ax.set_xlabel("starting injury", fontsize=H.FS_LABEL)
    axs[0, 0].set_ylim(0, 100); axs[0, 0].set_xticks([0, 30, 60, 90]); axs[0, 0].set_xlim(-4, 94)
    from matplotlib.lines import Line2D
    hs = [Line2D([], [], color=NONE_COL, marker="o", mfc=H.PAPER, mew=1.3, lw=2, label="no animal"),
          Line2D([], [], color=RABBIT_COL, marker="s", mfc=RABBIT_COL, lw=2, label="wandering rabbit"),
          Line2D([], [], color=H.INK_2, lw=0.7, ls=(0, (3, 2)), label="dashed edges: 95 % interval")]
    fig.legend(handles=hs, loc="lower center", ncol=3, frameon=False, fontsize=H.FS_LABEL, bbox_to_anchor=(0.5, -0.005))
    fig.subplots_adjust(left=0.13, right=0.99, top=0.96, bottom=0.6 / (2.35 * len(rr) + 1.0), hspace=0.28, wspace=0.08)
    return fig, rows


def extra_series(lf, inj, on_grid=True):
    return ser(lf, "rabbitwander", inj, on_grid) - ser(lf, "none", inj, on_grid)


def panels(group):
    rr, ns, plt = grid_layout(group)
    nr = 2
    # same width for 2- and 3-column groups, so text prints at one size at the page's column width
    fig, axs = plt.subplots(nr, ns, figsize=(2.9 * 3 + 0.9, 2.7 * nr + 1.1), sharex=True, sharey=True, squeeze=False)
    return rr, ns, fig, axs


def all_runs():
    return [(g, a, s) for g in SEEDS for a, s in runs(g)]


def padded(lo, hi, step):
    return np.floor(lo / step) * step, np.ceil(hi / step) * step


@functools.lru_cache(maxsize=None)
def extra_ylim():
    """One y-range for the extra figures of all three groups: the outermost interval edge drawn."""
    v = [x for g, a, s in all_runs() for h in ("on", "off") for i in INJ
         for x in prof(extra_series(leaf(g, h, a, s), i).dropna())[1:]]
    return padded(min(v), max(v), 10)


@functools.lru_cache(maxsize=None)
def train_ylim():
    """One y-range for the train figures of all three groups: the outermost single checkpoint drawn."""
    v = [train_series(leaf(g, h, a, s)) for g, a, s in all_runs() for h in ("on", "off")]
    return padded(min(x.min() for x in v), max(x.max() for x in v), 20)


def train_series(lf):
    return (extra_series(lf, "10", False) - extra_series(lf, "00", False)).dropna()


def fig_extra(group):
    rr, ns, fig, axs = panels(group)
    rows = []
    for k, (a, s) in enumerate(rr):
        ax = axs[k // ns, k % ns]
        for heal, filled in (("on", False), ("off", True)):
            lf = leaf(group, heal, a, s)
            st = [prof(extra_series(lf, i).dropna()) for i in INJ]
            band(ax, X, *zip(*st), HEAL_COL[heal], HEAL_MK[heal], filled=filled)
            ax.axhline(st[0][0], color=HEAL_COL[heal], lw=0.9, ls=":", zorder=1)
            rows.append(HL.grid_row(f"{a} s{s}, {HEAL_NAME[heal]}: checkpoints per starting injury",
                                    extra_series(lf, "10").dropna(), lf))
        ax.axhline(0, color=H.RULE, lw=0.8, zorder=0)
        ax.set_title(f"{a}, seed {s}", loc="left", fontsize=H.FS_LABEL + 1)
        if k % ns == 0:
            ax.set_ylabel("rabbit minus no animal\n(points of bush dwell)", fontsize=H.FS_LABEL)
        if k // ns == 1:
            ax.set_xlabel("starting injury", fontsize=H.FS_LABEL)
    axs[0, 0].set_xticks([0, 30, 60, 90]); axs[0, 0].set_xlim(-4, 94); axs[0, 0].set_ylim(*extra_ylim())
    from matplotlib.lines import Line2D
    hs = [Line2D([], [], color=HEAL_COL["on"], marker=HEAL_MK["on"], mfc=H.PAPER, mew=1.3, lw=2, label=HEAL_NAME["on"]),
          Line2D([], [], color=HEAL_COL["off"], marker=HEAL_MK["off"], lw=2, label=HEAL_NAME["off"]),
          Line2D([], [], color=H.INK_2, lw=0.9, ls=":", label="dotted: the value when unhurt (injury 0)")]
    fig.legend(handles=hs, loc="lower center", ncol=2, frameon=False, fontsize=H.FS_LABEL, bbox_to_anchor=(0.5, -0.01))
    fig.subplots_adjust(left=0.1, right=0.99, top=0.93, bottom=0.15, hspace=0.32, wspace=0.08)
    return fig, rows


def fig_train(group):
    rr, ns, fig, axs = panels(group)
    rows = []
    for k, (a, s) in enumerate(rr):
        ax = axs[k // ns, k % ns]
        for heal in ("on", "off"):
            lf = leaf(group, heal, a, s)
            d = train_series(lf)
            x = d.index.to_numpy() / 1e6
            ax.plot(x, d.to_numpy(), color=HEAL_COL[heal], lw=0.6, alpha=0.45)
            ax.plot(x, d.rolling(5, center=True, min_periods=3).mean().to_numpy(), color=HEAL_COL[heal], lw=2.0)
            rows.append({"what": f"{a} s{s}, {HEAL_NAME[heal]}: tested checkpoints, whole training", "used": len(d),
                         "total": len(ser(lf, "none", "00", False)),
                         "note": f"checkpoints with all four tests (no animal and rabbit, injury 0 and 10); {HL.episodes(lf)} episodes each"})
        ax.axhline(0, color=H.RULE, lw=0.8, zorder=0)
        ax.axvspan(0, 2, color=H.RULE, alpha=0.25, lw=0)
        ax.set_title(f"{a}, seed {s}", loc="left", fontsize=H.FS_LABEL + 1)
        if k % ns == 0:
            ax.set_ylabel("injury-10 contrast\n(points of bush dwell)", fontsize=H.FS_LABEL)
        if k // ns == 1:
            ax.set_xlabel("training (million steps)", fontsize=H.FS_LABEL)
    axs[0, 0].set_xlim(-0.4, 10.2); axs[0, 0].set_xticks([0, 2, 4, 6, 8, 10]); axs[0, 0].set_ylim(*train_ylim())
    from matplotlib.lines import Line2D
    hs = [Line2D([], [], color=HEAL_COL[h], lw=2, label=HEAL_NAME[h]) for h in ("on", "off")]
    hs.append(Line2D([], [], color=H.INK_2, lw=0.6, alpha=0.6, label="thin: single checkpoints; thick: 5-checkpoint average"))
    fig.legend(handles=hs, loc="lower center", ncol=2, frameon=False, fontsize=H.FS_LABEL, bbox_to_anchor=(0.5, -0.01))
    fig.subplots_adjust(left=0.1, right=0.99, top=0.93, bottom=0.15, hspace=0.32, wspace=0.08)
    return fig, rows


def collapse(rows, what):
    """One data-statement row per figure: every series in it has the same coverage, so 16-24 identical
    rows say nothing more than their sum. Refuses if the series do not share one note."""
    notes = {r["note"] for r in rows}
    if len(notes) != 1:
        return rows
    return [{"what": what, "used": sum(r["used"] for r in rows), "total": sum(r["total"] for r in rows),
             "note": notes.pop()}]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--fig-dir", required=True)
    ap.add_argument("--figure", required=True, choices=["curves", "extra", "train"])
    ap.add_argument("--group", required=True, choices=list(SEEDS) + ["all"])
    a = ap.parse_args(argv)
    H.apply()
    d = os.path.abspath(a.fig_dir)
    what = {"curves": "every agent x healing x animal series, per starting injury",
            "extra": "every agent x healing series, per starting injury",
            "train": "every agent x healing series, whole training"}[a.figure]
    for g in (list(SEEDS) if a.group == "all" else [a.group]):
        fig, rows = {"curves": fig_curves, "extra": fig_extra, "train": fig_train}[a.figure](g)
        stem = f"lk_{a.figure}__{g}"
        FG.record_samples(d, stem, collapse(rows, f"{len(rows)} series ({what})"))
        FG.save(fig, d, stem)


if __name__ == "__main__":
    main()
