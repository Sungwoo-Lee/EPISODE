#!/usr/bin/env python3
"""figures.py - figures of the 'Predator, Food and Hazard Settings Screen' page.

The level-05 half-factorial screen (design: docs/experiments/active/hypervigilance/LOOKALIKE_HALF_FACTORIAL_L05.md):
eight training worlds x {ordinary, modulated}, seed 42, plus world 1's seed-43 pair as the seed-to-seed
reference; every agent tested in world 1's frozen injury-grid scenes with bush healing on and off. Numbers come
from data.py (one series per run, resumed sessions merged); every summary is the mean of the newest 20 tested
checkpoints with a 95 % interval, as in the pre-registered readout.

  curves --world N   bush dwell against starting injury: no animal vs wandering rabbit, healing on | off
  extra  --world N   the rabbit's extra bush dwell (rabbit minus no animal) at each starting injury
  train  --world N   the injury contrast (readout c) at every tested checkpoint, injury 70 | injury 10
  animals            healing off: bush dwell per run with no animal / wandering rabbit / chasing rabbit /
                     predator, unhurt and at injury 70 (a heat map, one row per run)
  group              the pre-registered group test: each setting group's effect against the bar
  seeds              the injury contrast of every world and agent, seed 42 beside each tested replication seed
  seedtrain          the injury contrast across training, healing off, injury 70, the seeds overlaid
  food               each run's injury contrast with the food item (x) against the food-free scenes (y)
--world all draws the eight worlds in one process (the CSVs are read once).

    $P scripts/analysis/studies/half_factorial_l05/figures.py --fig-dir <dir> --figure curves|extra|train --world N|all
    $P scripts/analysis/studies/half_factorial_l05/figures.py --fig-dir <dir> --figure animals|group|seeds|seedtrain|food
"""
from __future__ import annotations

import argparse
import functools
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import data as D  # noqa: E402
sys.path.insert(0, os.path.join(D.ROOT, "scripts", "analysis", "basic_behaviour"))
import _fig as FG  # noqa: E402

H = FG.H
X = [int(i) for i in D.INJ]
NONE_COL, RABBIT_COL = "#8a8f98", H.ORANGE
HEAL_COL = {"on": H.GREEN, "off": H.BLUE}
HEAL_MK = {"on": "^", "off": "D"}
HEAL_NAME = {"on": "healing on (as in training)", "off": "healing off (test only)"}
HEALS = ("off", "on")
# Figure 1's pass / no-pass marks: ink and light grey, so no hue there collides with the healing colours of
# Figures 3-4 or the blue ramp of Figure 5 (format review 2026-10-13, register F11)
STATUS_YES, STATUS_NO = H.INK, "#9aa0a8"   # healing off is the headline (user, 2026-10-13)


def runs(world):
    if world == D.REF:
        return [(a, s) for a in D.AGENTS for s in D.ref_seeds(a)]
    return [(a, s) for a in D.AGENTS for s in ((42, 43) if world == 1 else (42,))]


def world_title(w):
    if w == D.REF:
        return "plain level 05 (reference, no lookalike change)"
    return "world 1 (the lookalike world)" if w == 1 else f"world {w} (changed: {', '.join(D.NEW[w])})"


def ref_worlds():
    """The plain level-05 reference, once any of its runs is tested, then the design's eight worlds."""
    return ([D.REF] if any(D.ref_seeds(a) for a in D.AGENTS) else []) + list(D.WORLDS)


def summ(v):
    p = D.newest(v.dropna())
    return p["mean"], p["lo"], p["hi"]


def used_row(what, v, w, a, s, heal):
    v = v.dropna()
    return {"what": what, "used": min(D.NEWEST, len(v)), "total": len(v),
            "note": f"newest {D.NEWEST} tested checkpoints of each run (steps {v.index[-D.NEWEST] / 1e6:.1f}-"
                    f"{v.index[-1] / 1e6:.1f} M for this one); {D.n_episodes(w, a, heal, 'grid', s)} episodes each"}


def band(ax, x, m, lo, hi, col, mk="o", filled=True):
    ax.fill_between(x, lo, hi, color=col, alpha=0.14, lw=0)
    for e in (lo, hi):
        ax.plot(x, e, color=col, lw=0.7, ls=(0, (3, 2)))
    ax.plot(x, m, color=col, lw=2.0, marker=mk, ms=4.5, mfc=col if filled else H.PAPER, mew=1.3, zorder=3)


def g(w, a, heal, sc, inj, s):
    return D.dwell(w, a, heal, "grid", sc, inj, s)


def extra(w, a, heal, inj, s):
    return (g(w, a, heal, "rabbitwander", inj, s) - g(w, a, heal, "none", inj, s)).dropna()


def fig_curves(w):
    import matplotlib.pyplot as plt
    rr = [(a, s) for a in D.AGENTS for s in seed_runs(w, a)]   # every tested seed (user, 2026-10-14)
    fig, axs = plt.subplots(len(rr), 2, figsize=(8.4, 2.35 * len(rr) + 1.0), sharex=True, sharey=True, squeeze=False)
    rows = []
    for r_, (a, s) in enumerate(rr):
        for c_, heal in enumerate(HEALS):
            ax = axs[r_, c_]
            for sc, col, mk, filled, name in (("none", NONE_COL, "o", False, "no animal"),
                                              ("rabbitwander", RABBIT_COL, "s", True, "wandering rabbit")):
                st = [summ(g(w, a, heal, sc, i, s)) for i in D.INJ]
                band(ax, X, *zip(*st), col, mk, filled=filled)
                rows.append(used_row("", g(w, a, heal, sc, "70", s), w, a, s, heal))
                if D.has_nofood(w, a, s):   # food-free scenes (user, 2026-10-14): dotted, no band
                    nf = [summ(D.dwell(w, a, heal, "grid_nofood", sc, i, s))[0] for i in D.INJ]
                    ax.plot(X, nf, color=col, lw=1.5, ls=(0, (1.2, 1.4)), marker=mk, ms=3.2, mfc=H.PAPER, mew=1.0, zorder=4)
                    rows.append(used_row("", D.dwell(w, a, heal, "grid_nofood", sc, "70", s), w, a, s, heal))
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
    if any(D.has_nofood(w, a, s) for a, s in rr):
        hs.append(Line2D([], [], color=H.INK_2, lw=1.5, ls=(0, (1.2, 1.4)), marker="o", ms=3.2, mfc=H.PAPER,
                         label="dotted: food-free scenes"))
    fig.legend(handles=hs, loc="lower center", ncol=4 if len(hs) == 4 else 3, frameon=False, fontsize=H.FS_LABEL, bbox_to_anchor=(0.5, -0.005))
    fig.subplots_adjust(left=0.13, right=0.99, top=0.95 if len(rr) == 2 else 0.96,
                        bottom=0.6 / (2.35 * len(rr) + 1.0) + 0.04, hspace=0.28, wspace=0.08)
    return fig, rows


def panels(n):
    import matplotlib.pyplot as plt
    ncol = 2
    nrow = (n + 1) // ncol
    fig, axs = plt.subplots(nrow, ncol, figsize=(8.4, 2.8 * nrow + 1.1), sharex=True, sharey=True, squeeze=False)
    return fig, axs, ncol


def fig_extra(w):
    rr = runs(w)
    fig, axs, nc = panels(len(rr))
    rows = []
    for k, (a, s) in enumerate(rr):
        ax = axs[k // nc, k % nc]
        for heal in HEALS:
            st = [summ(extra(w, a, heal, i, s)) for i in D.INJ]
            band(ax, X, *zip(*st), HEAL_COL[heal], HEAL_MK[heal], filled=heal == "off")
            ax.axhline(st[0][0], color=HEAL_COL[heal], lw=0.9, ls=":", zorder=1)
            rows.append(used_row("", extra(w, a, heal, "70", s), w, a, s, heal))
        ax.axhline(0, color=H.RULE, lw=0.8, zorder=0)
        ax.set_title(f"{a}, seed {s}", loc="left", fontsize=H.FS_LABEL + 1)
        if k % nc == 0:
            ax.set_ylabel("rabbit minus no animal\n(points of bush dwell)", fontsize=H.FS_LABEL)
        if k // nc == axs.shape[0] - 1:
            ax.set_xlabel("starting injury", fontsize=H.FS_LABEL)
    axs[0, 0].set_xticks([0, 30, 60, 90]); axs[0, 0].set_xlim(-4, 94); axs[0, 0].set_ylim(*extra_ylim())
    lo, hi = extra_ylim()
    axs[0, 0].set_yticks(np.arange(np.ceil(lo / 20) * 20, hi + 1, 20))   # same ticks in every world's figure (format review 2026-10-15)
    from matplotlib.lines import Line2D
    hs = [Line2D([], [], color=HEAL_COL["off"], marker=HEAL_MK["off"], lw=2, label=HEAL_NAME["off"]),
          Line2D([], [], color=HEAL_COL["on"], marker=HEAL_MK["on"], mfc=H.PAPER, mew=1.3, lw=2, label=HEAL_NAME["on"]),
          Line2D([], [], color=H.INK_2, lw=0.9, ls=":", label="dotted: the value when unhurt (injury 0)")]
    fig.legend(handles=hs, loc="lower center", ncol=2, frameon=False, fontsize=H.FS_LABEL, bbox_to_anchor=(0.5, -0.01))
    fig.subplots_adjust(left=0.12, right=0.99, top=0.93 if axs.shape[0] == 1 else 0.95,
                        bottom=0.24 if axs.shape[0] == 1 else 0.14, hspace=0.32, wspace=0.08)
    return fig, rows


def padded(lo, hi, step):
    return np.floor(lo / step) * step, np.ceil(hi / step) * step


def all_runs():
    return [(w, a, s) for w in ref_worlds() for a, s in runs(w)]


@functools.lru_cache(maxsize=None)
def extra_ylim():
    """One y-range for every world's extra figure: the outermost interval edge drawn."""
    v = [x for w, a, s in all_runs() for h in HEALS for i in D.INJ for x in summ(extra(w, a, h, i, s))[1:]]
    return padded(min(v), max(v), 10)


@functools.lru_cache(maxsize=None)
def train_ylim():
    """One y-range for every world's training figure: the outermost single checkpoint drawn."""
    v = [D.contrast(w, a, h, "interaction", i, s) for w, a, s in all_runs() for h in HEALS for i in ("70", "10")]
    return padded(min(x.min() for x in v), max(x.max() for x in v), 20)


def fig_train(w):
    import matplotlib.pyplot as plt
    rr = runs(w)
    fig, axs = plt.subplots(len(rr), 2, figsize=(8.4, 2.35 * len(rr) + 1.0), sharex=True, sharey=True, squeeze=False)
    rows = []
    for r_, (a, s) in enumerate(rr):
        for c_, inj in enumerate(("70", "10")):
            ax = axs[r_, c_]
            for heal in HEALS:
                d = D.contrast(w, a, heal, "interaction", inj, s)
                x = d.index.to_numpy() / 1e6
                ax.plot(x, d.to_numpy(), color=HEAL_COL[heal], lw=0.6, alpha=0.45)
                ax.plot(x, d.rolling(5, center=True, min_periods=3).mean().to_numpy(), color=HEAL_COL[heal], lw=2.0)
                if inj == "70":
                    rows.append({"what": "", "used": len(d), "total": len(g(w, a, heal, "none", "00", s)),
                                 "note": "every tested checkpoint with all four tests (no animal and rabbit, unhurt and "
                                         f"injured); {D.n_episodes(w, a, heal, 'grid', s)} episodes each"})
            lo = d.index[-D.NEWEST] / 1e6
            ax.axvspan(lo - 0.1, 10.1, color=H.RULE, alpha=0.25, lw=0, zorder=0)
            ax.axhline(0, color=H.RULE, lw=0.8, zorder=0)
            if r_ == 0:
                ax.set_title(f"injury {int(inj)}" + (" (headline)" if inj == "70" else ""), loc="left", fontsize=H.FS_BODY)
            if c_ == 0:
                ax.set_ylabel(f"{a}, seed {s}\ncontrast (points)", fontsize=H.FS_LABEL)
            if r_ == len(rr) - 1:
                ax.set_xlabel("training (million steps)", fontsize=H.FS_LABEL)
    axs[0, 0].set_xlim(-0.2, 10.3); axs[0, 0].set_xticks([0, 2, 4, 6, 8, 10]); axs[0, 0].set_ylim(*train_ylim())
    lo, hi = train_ylim()
    axs[0, 0].set_yticks(np.arange(lo, hi + 1, 50))   # same ticks in every world's figure, whatever its height
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    hs = [Line2D([], [], color=HEAL_COL[h], lw=2, label=HEAL_NAME[h]) for h in HEALS]
    hs.append(Line2D([], [], color=H.INK_2, lw=0.6, alpha=0.6, label="thin: single checkpoints; thick: 5-checkpoint average"))
    hs.append(Patch(color=H.RULE, alpha=0.5, label=f"shaded: the newest {D.NEWEST} checkpoints (the summary window)"))
    fig.legend(handles=hs, loc="lower center", ncol=2, frameon=False, fontsize=H.FS_LABEL, bbox_to_anchor=(0.5, -0.005))
    fig.subplots_adjust(left=0.13, right=0.99, top=0.95 if len(rr) == 2 else 0.96,
                        bottom=0.85 / (2.35 * len(rr) + 1.0) + 0.05, hspace=0.28, wspace=0.08)
    return fig, rows


ANIMALS = (("grid", "none", "no animal"), ("grid", "rabbitwander", "wandering rabbit"),
           ("gridchase", "rabbit", "chasing rabbit"), ("grid", "pred", "predator"))


ANIMAL_INJ = [f"{i}" for i in range(10, 100, 10)]


def fig_animals(injury="70"):
    """One heat map per injury level (user, 2026-10-15: the page lets the reader pick 10-90, as Figure 2's tabs do);
    each compares that injury with unhurt. Lower injuries keep hiding off the 100 % ceiling (Visualization session)."""
    import matplotlib.pyplot as plt
    rr = [(w, a, s) for w, a, s in all_runs()]
    cols = [(st, sc, name, inj) for inj in ("00", injury) for st, sc, name in ANIMALS]
    M = np.full((len(rr), len(cols)), np.nan)
    rows = []
    for i, (w, a, s) in enumerate(rr):
        for j, (st, sc, name, inj) in enumerate(cols):
            v = D.dwell(w, a, "off", st, sc, inj, s).dropna()
            M[i, j] = summ(v)[0]
            if j == 0:
                rows.append(used_row("", v, w, a, s, "off"))
    fig, ax = plt.subplots(figsize=(8.4, 0.36 * len(rr) + 2.2))
    im = ax.imshow(M, cmap=H.sequential(), vmin=0, vmax=100, aspect="auto")
    ax.grid(False)
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            ax.text(j, i, f"{M[i, j]:.0f}", ha="center", va="center", fontsize=H.FS_LABEL - 1,
                    color=H.PAPER if M[i, j] > 60 else H.INK)
    ax.set_xticks(range(len(cols)), [f"{name}, " + ("unhurt" if inj == "00" else f"injury {int(inj)}") for _, _, name, inj in cols],
                  rotation=35, ha="right", fontsize=H.FS_LABEL)
    ax.set_yticks(range(len(rr)), [("level 05" if w == D.REF else f"w{w}") + f" {a}" + (f" s{s}" if w in (1, D.REF) else "")
                                   for w, a, s in rr], fontsize=H.FS_LABEL)
    ax.axvline(len(ANIMALS) - 0.5, color=H.PAPER, lw=3)
    for i in range(1, len(rr)):
        if rr[i][0] != rr[i - 1][0]:   # a white rule between worlds
            ax.axhline(i - 0.5, color=H.PAPER, lw=2)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(length=0)
    cb = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    cb.set_label("bush dwell (%)", fontsize=H.FS_LABEL)
    cb.outline.set_visible(False)
    fig.subplots_adjust(left=0.2, right=0.95, top=0.98, bottom=0.2)
    return fig, rows


def fig_group():
    import matplotlib.pyplot as plt
    cases = (("off", "70", "healing off\ninjury 70 (headline)"), ("off", "10", "healing off\ninjury 10"),
             ("on", "70", "healing on\ninjury 70"))
    fig, axs = plt.subplots(1, len(cases), figsize=(8.4, 5.0), sharey=True)
    rows = []
    for ax, (heal, inj, title) in zip(axs, cases):
        rt = D.run_table(heal, inj)
        ge = D.group_effects(rt)
        y = np.arange(len(ge))[::-1]
        bar = ge["bar"].iloc[0]
        ax.axvspan(-bar, bar, color=H.RULE, alpha=0.2, lw=0, zorder=0)
        ax.axvline(0, color=H.INK_2, lw=0.8, zorder=1)
        for yy, (_, r) in zip(y, ge.iterrows()):
            passed = r["clears_bar"] and r["same_sign_6_8_10"]
            col = STATUS_YES if passed else STATUS_NO
            for a, mk in (("ordinary", "o"), ("modulated", "s")):
                ax.plot(r[f"effect_{a}"], yy, marker=mk, ms=4.5, mfc=H.PAPER, mec=col, mew=1.1, ls="none", zorder=2)
            ax.plot(r["effect"], yy, marker="D", ms=7.5, color=col, ls="none", zorder=3)
        ax.set_yticks(y, [f"{t}: {D.GROUPS[t]}" if t in D.GROUPS else f"pair {t}" for t in ge["term"]],
                      fontsize=H.FS_LABEL)
        ax.set_title(title, loc="left", fontsize=H.FS_LABEL + 1)
        ax.set_xlabel("effect (points of bush dwell)", fontsize=H.FS_LABEL)
        s = rt[rt.seed == 42]
        rows.append({"what": "", "used": int(s.n_ckpt.clip(upper=D.NEWEST).sum()), "total": int(s.n_ckpt.sum()),
                     "note": f"16 screen runs (8 worlds x 2 agents), newest {D.NEWEST} tested checkpoints each; "
                             "world 1's seed-43 pair is not part of the test"})
    lim = max(abs(x) for ax in axs for x in ax.get_xlim())
    lim = 10 * np.ceil(lim / 10)
    for ax in axs:
        ax.set_xlim(-lim, lim)
        ax.set_xticks([-lim / 2, 0, lim / 2] if lim >= 20 else [-lim, 0, lim])
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    hs = [Line2D([], [], marker="D", color=STATUS_YES, ls="none", ms=7, label="both agents averaged: clears the bar, same sign at 6, 8, 10 M"),
          Line2D([], [], marker="D", color=STATUS_NO, ls="none", ms=7, label="both agents averaged: does not"),
          Line2D([], [], marker="o", mfc=H.PAPER, mec=H.INK_2, ls="none", label="ordinary agent"),
          Line2D([], [], marker="s", mfc=H.PAPER, mec=H.INK_2, ls="none", label="modulated agent"),
          Patch(color=H.RULE, alpha=0.6, label="shaded: inside the bar (no effect claimed)")]
    fig.legend(handles=hs, loc="lower center", ncol=2, frameon=False, fontsize=H.FS_LABEL, bbox_to_anchor=(0.5, -0.01))
    fig.subplots_adjust(left=0.25, right=0.98, top=0.88, bottom=0.33, wspace=0.14)
    return fig, rows


# replication seeds: hues outside the healing (blue / green) and animal (grey / orange) colours used above
SEED_COL = {42: H.INK, 43: "#7b5ea7", 44: "#b8860b"}
SEED_MK = {42: "o", 43: "P", 44: "X"}   # shapes used nowhere else on the page (format review, F11)


def seed_runs(w, a):
    if w == D.REF:
        return tuple(D.ref_seeds(a))
    return (42, 43) if w == 1 else (42, *D.tested_seeds(w, a))


def fig_seeds():
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(2, 2, figsize=(8.4, 8.2), sharex=True, sharey=True)
    rows = []
    ys = np.arange(len(D.WORLDS))[::-1]
    for r_, heal in enumerate(HEALS):
        for c_, a in enumerate(D.AGENTS):
            ax = axs[r_, c_]
            ax.axvline(0, color=H.INK_2, lw=0.8, zorder=1)
            for y, w in zip(ys, D.WORLDS):
                ss = seed_runs(w, a)
                for k, s in enumerate(ss):
                    v = D.contrast(w, a, heal, "interaction", "70", s)
                    m, lo, hi = summ(v)
                    yy = y + (k - (len(ss) - 1) / 2) * 0.22
                    ax.plot([lo, hi], [yy, yy], color=SEED_COL[s], lw=1.3, zorder=2)
                    ax.plot(m, yy, marker=SEED_MK[s], ms=5.5, color=SEED_COL[s], mfc=SEED_COL[s],
                            mew=1.3, ls="none", zorder=3)
                    rows.append(used_row("", v, w, a, s, heal))
            ax.set_yticks(ys, ["w1 (base)"] + [f"w{w} {'+'.join(D.NEW[w])}" for w in D.WORLDS[1:]], fontsize=H.FS_LABEL)
            ax.axhline(ys[0] - 0.5, color=H.RULE, lw=0.8)
            if r_ == 0:
                ax.set_title(f"{a} agent", loc="left", fontsize=H.FS_BODY)
            if c_ == 0:
                ax.set_ylabel(HEAL_NAME[heal], fontsize=H.FS_LABEL)
            if r_ == 1:
                ax.set_xlabel("injury contrast at injury 70 (points)", fontsize=H.FS_LABEL)
    lim = max(abs(x) for ax in axs.flat for x in ax.get_xlim())
    lim = 10 * np.ceil(lim / 10)
    axs[0, 0].set_xlim(-lim, lim)
    axs[0, 0].set_xticks([-lim / 2, 0, lim / 2])   # no end ticks: the two columns' end labels would touch
    from matplotlib.lines import Line2D
    hs = [Line2D([], [], color=SEED_COL[s], marker=SEED_MK[s], mfc=SEED_COL[s], mew=1.3, lw=1.3,
                 label=f"seed {s}") for s in (42, 43, 44)]
    hs.append(Line2D([], [], color=H.INK_2, lw=1.3, label="line: 95 % interval"))
    fig.legend(handles=hs, loc="lower center", ncol=4, frameon=False, fontsize=H.FS_LABEL, bbox_to_anchor=(0.5, -0.005))
    fig.subplots_adjust(left=0.17, right=0.98, top=0.96, bottom=0.11, hspace=0.12, wspace=0.08)
    return fig, rows


def fig_seedtrain():
    import matplotlib.pyplot as plt
    ws = D.WORLDS
    fig, axs = plt.subplots(len(ws), 2, figsize=(8.4, 1.55 * len(ws) + 1.2), sharex=True, sharey=True, squeeze=False)
    rows, ext = [], []
    for r_, w in enumerate(ws):
        for c_, a in enumerate(D.AGENTS):
            ax = axs[r_, c_]
            ax.axhline(0, color=H.RULE, lw=0.8, zorder=0)
            for s in seed_runs(w, a):
                d = D.contrast(w, a, "off", "interaction", "70", s)
                x = d.index.to_numpy() / 1e6
                sm = d.rolling(5, center=True, min_periods=3).mean().to_numpy()
                ext += [np.nanmin(sm), np.nanmax(sm)]
                ax.plot(x, sm, color=SEED_COL[s], lw=1.7,
                        ls="-" if s == 42 else (0, (4, 1.5)) if s == 43 else (0, (1.5, 1.2)))
                rows.append({"what": "", "used": len(d), "total": len(g(w, a, "off", "none", "00", s)),
                             "note": "every tested checkpoint with all four tests (no animal and rabbit, unhurt and "
                                     f"injury 70); {D.n_episodes(w, a, 'off', 'grid', s)} episodes each"})
            if r_ == 0:
                ax.set_title(f"{a} agent", loc="left", fontsize=H.FS_BODY)
            if c_ == 0:
                ax.set_ylabel("w1 (base)" if w == 1 else f"w{w} {'+'.join(D.NEW[w])}", fontsize=H.FS_LABEL)
            if r_ == len(ws) - 1:
                ax.set_xlabel("training (million steps)", fontsize=H.FS_LABEL)
    lo, hi = padded(min(ext), max(ext), 20)   # its own range: smoothed lines only, every seed drawn
    axs[0, 0].set_xlim(-0.2, 10.3); axs[0, 0].set_xticks([0, 2, 4, 6, 8, 10]); axs[0, 0].set_ylim(lo, hi)
    axs[0, 0].set_yticks(np.arange(lo, hi + 1, 40 if hi - lo > 80 else 20))
    from matplotlib.lines import Line2D
    hs = [Line2D([], [], color=SEED_COL[s], lw=1.7, ls="-" if s == 42 else (0, (4, 1.5)) if s == 43 else (0, (1.5, 1.2)),
                 label=f"seed {s}") for s in (42, 43, 44)]
    fig.legend(handles=hs, loc="lower center", ncol=3, frameon=False, fontsize=H.FS_LABEL, bbox_to_anchor=(0.5, -0.003))
    fig.subplots_adjust(left=0.11, right=0.99, top=0.97, bottom=0.62 / (1.55 * len(ws) + 1.2) + 0.02, hspace=0.18, wspace=0.06)
    return fig, rows


def planned_runs_row():
    """Run-level coverage against the planned set (format review F83): the 16 screen runs, world 1's seed-43
    pair and the 28 repeat runs; every repeat run not yet tested is named as missing, with its state."""
    st = [D.seed_status(w, a, s)[0] for w in D.WORLDS[1:] for a in D.AGENTS for s in D.EXTRA_SEEDS]
    shown = 18 + st.count("tested")
    n = {k: st.count(k) for k in ("testing", "training", "queued")}
    left = ", ".join(f"{v} {k if k != 'testing' else 'being tested'}" for k, v in n.items() if v)
    return {"what": "runs drawn, of all planned", "used": shown, "total": 18 + len(st),
            "note": (f"{len(st) - st.count('tested')} repeat run{'s' if len(st) - st.count('tested') != 1 else ''} not yet tested ({left}); shown once finished and tested")
            if left else "every planned run is drawn"}


def world_runs_row(w):
    """Figure 2's run-level coverage for one world: drawn (agent, seed) runs of all planned (format review F83)."""
    plan = [(a, s) for a in D.AGENTS for s in (D.REF_SEEDS if w == D.REF else (42, 43) if w == 1 else (42, *D.EXTRA_SEEDS))]
    drawn = sum(1 for a, s in plan if s in seed_runs(w, a))
    st = [D.seed_status(w, a, s)[0] for a, s in plan if s != 42 and w > 1 and s not in seed_runs(w, a)]
    left = ", ".join(f"{st.count(k)} {k if k != 'testing' else 'being tested'}" for k in ("testing", "training", "queued")
                     if st.count(k))
    return {"what": "runs drawn, of all planned", "used": drawn, "total": len(plan),
            "note": (f"{len(st)} repeat run{'s' if len(st) != 1 else ''} not yet tested ({left}); shown once finished and tested") if st
            else "every planned run of this world is drawn"}


FOOD_MK = {"ordinary": "o", "modulated": "s"}


def food_runs():
    """Every run whose food-free test is complete: (world, agent, seed)."""
    out = []
    for w in D.WORLDS:
        for a in D.AGENTS:
            for s in ((42, 43) if w == 1 else (42, *D.tested_seeds(w, a))):
                if D.has_nofood(w, a, s):
                    out.append((w, a, s))
    return out


def fig_food():
    import matplotlib.pyplot as plt
    rr = food_runs()
    fig, axs = plt.subplots(1, 2, figsize=(8.4, 4.9), sharex=True, sharey=True)
    rows, ext = [], []
    for ax, heal in zip(axs, HEALS):
        for w, a, s in rr:
            v1 = D.contrast(w, a, heal, "interaction", "70", s, "grid")
            v0 = D.contrast(w, a, heal, "interaction", "70", s, "grid_nofood")
            m1, lo1, hi1 = summ(v1)
            m0, lo0, hi0 = summ(v0)
            ext += [lo1, hi1, lo0, hi0]
            ax.plot([lo1, hi1], [m0, m0], color=SEED_COL[s], lw=0.8, alpha=0.6, zorder=2)
            ax.plot([m1, m1], [lo0, hi0], color=SEED_COL[s], lw=0.8, alpha=0.6, zorder=2)
            ax.plot(m1, m0, marker=FOOD_MK[a], ms=5.5, color=SEED_COL[s], mfc=SEED_COL[s] if a == "ordinary" else H.PAPER,
                    mew=1.3, ls="none", zorder=3)
            if abs(m0 - m1) > 15:   # label only runs the food moved by more than 15 points
                ax.annotate(f"w{w}", (m1, m0), xytext=(4, 3), textcoords="offset points", fontsize=H.FS_LABEL - 1,
                            color=H.INK_2)
            rows.append(used_row("", v0, w, a, s, heal))
        ax.set_title(HEAL_NAME[heal], loc="left", fontsize=H.FS_BODY)
        ax.set_xlabel("with the food item (points)", fontsize=H.FS_LABEL)
    lim = 20 * np.ceil(max(abs(x) for x in ext) / 20)
    for ax in axs:
        ax.plot([-lim, lim], [-lim, lim], color=H.INK_2, lw=0.8, ls=(0, (4, 2)), zorder=1)
        ax.axhline(0, color=H.RULE, lw=0.8, zorder=0); ax.axvline(0, color=H.RULE, lw=0.8, zorder=0)
    axs[0].set_xlim(-lim, lim); axs[0].set_ylim(-lim, lim); axs[0].set_aspect("equal")
    axs[0].set_ylabel("food-free scenes (points)", fontsize=H.FS_LABEL)
    from matplotlib.lines import Line2D
    hs = [Line2D([], [], marker="o", color=H.INK_2, ls="none", label="ordinary agent"),
          Line2D([], [], marker="s", color=H.INK_2, mfc=H.PAPER, mew=1.3, ls="none", label="modulated agent")]
    hs += [Line2D([], [], marker="o", color=SEED_COL[s], ls="none", label=f"seed {s}") for s in (42, 43, 44)]
    hs.append(Line2D([], [], color=H.INK_2, lw=0.8, ls=(0, (4, 2)), label="dashed: same value in both"))
    fig.legend(handles=hs, loc="lower center", ncol=3, frameon=False, fontsize=H.FS_LABEL, bbox_to_anchor=(0.5, -0.01))
    fig.subplots_adjust(left=0.1, right=0.98, top=0.93, bottom=0.27, wspace=0.08)
    return fig, rows


def collapse(rows, what):
    """One data-statement row per figure when every series shares one coverage note (the per-run step range
    is dropped from the note, since it differs only by when testing started)."""
    notes = {re.sub(r" \(steps [^)]*\)", "", r["note"]) for r in rows}
    if len(notes) != 1:
        return [{**r, "what": what} for r in rows]
    return [{"what": what, "used": sum(r["used"] for r in rows), "total": sum(r["total"] for r in rows),
             "note": notes.pop()}]


WHAT = {"curves": "series (agent \u00d7 seed \u00d7 healing \u00d7 animal \u00d7 with or without food), counted at injury 70",
        "extra": "series (agent x healing), counted at injury 70",
        "train": "series (agent x healing), whole training",
        "animals": "runs, healing off, 8 scenes each",
        "group": "group tests (one per panel)",
        "seeds": "series (run \u00d7 healing), counted at injury 70",
        "seedtrain": "series (run), healing off, injury 70, whole training",
        "food": "series (run \u00d7 healing), food-free scenes, counted at injury 70"}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--fig-dir", required=True)
    ap.add_argument("--figure", required=True, choices=list(WHAT))
    ap.add_argument("--world", default="all")
    a = ap.parse_args(argv)
    H.apply()
    d = os.path.abspath(a.fig_dir)
    if a.figure == "animals":
        jobs = [(f"hf_animals__i{i}", functools.partial(fig_animals, i)) for i in ANIMAL_INJ]
    elif a.figure in ("group", "seeds", "seedtrain", "food"):
        jobs = [(f"hf_{a.figure}", {"group": fig_group, "seeds": fig_seeds,
                                    "seedtrain": fig_seedtrain, "food": fig_food}[a.figure])]
    else:
        ws = ref_worlds() if a.world == "all" else [int(a.world)]
        f = {"curves": fig_curves, "extra": fig_extra, "train": fig_train}[a.figure]
        jobs = [(f"hf_{a.figure}__w{w}", functools.partial(f, w)) for w in ws]
    for stem, f in jobs:
        fig, rows = f()
        rows = collapse(rows, f"{len(rows)} {WHAT[a.figure]}")
        if a.figure in ("seeds", "seedtrain"):
            rows.append(planned_runs_row())
        if a.figure == "food":
            n = len(food_runs())
            rows.append({"what": "runs drawn, of all tested with food", "used": n, "total": 18 + sum(
                D.seed_status(w, ag, s)[0] == "tested" for w in D.WORLDS[1:] for ag in D.AGENTS for s in D.EXTRA_SEEDS),
                "note": "a run is drawn once its food-free test holds its final checkpoint, healing on and off"})
        if a.figure == "curves":
            rows.append(world_runs_row(int(stem.rsplit("w", 1)[1])))
        FG.record_samples(d, stem, rows)
        FG.save(fig, d, stem)
        print("saved", stem, flush=True)


if __name__ == "__main__":
    main()
