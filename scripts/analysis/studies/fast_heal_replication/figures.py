#!/usr/bin/env python3
"""figures.py - figures of the fast-bush-healing replication results page.

The replication (docs/experiments/active/hypervigilance/FAST_HEAL_REPLICATION.md) trained the ordinary and
the modulated agent with fast bush healing at levels 04, 05 and 06, seeds 42-44, on 2026-10-05. This page
repeats the cross-run page's "most effective conditions" analysis (Figures B1-B12) on those 18 runs, from
the experiment tests only (configs/eval_sweeps/healrep/): level 04 in the core scenes, levels 05 and 06 in
thermal-neutral scenes (air 0 C, no campfire, start body temperature 0), all at every saved checkpoint.

  summary            one row per level x seed pair (+ the 22-Sep originals of levels 04 and 05 as
                     reference rows): injury effect with no animal, with the wandering rabbit, predator
                     response; ordinary and modulated side by side, 95 % intervals
  (level 05 also has a fixed-start-temperature arm, "l05fix": same world but every episode starts at the
  temperature setpoint, trained 2026-10-06; its own scenes are the fixed-start copies in
  behavior_probes/fixed_start/)
  dose  --level L    bush dwell against starting injury 0..90, rows = seeds, columns = four scenes
  train --level L --seed S   the B5 view: ten injury lines across training, four scenes x two agents

All numbers are means over the checkpoints from 2 to 10 M training steps on a 0.2 M grid
(checkpoint_stats.on_grid), with the lag-1-corrected interval of the Basic Behaviour estimator.

    $P scripts/analysis/studies/fast_heal_replication/figures.py --fig-dir <dir> --figure summary|dose|train ...
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "f7b_across_runs"))
import highlight as HL  # noqa: E402  (series, grid_leaf, INJ_GRID, fig_injtrain, fig_injdose_seeds, K, C, H)

H, K, C = HL.H, HL.K, HL.C
AV = "results/eval/avoidance"
REP = f"{AV}/metrics_history_rppo_healrep"
LEVELS = ("l04", "l05", "l05fix", "l06")
SEEDS = (42, 43, 44)
# the scene set each level is read in for the summary: level 04 has no temperature system (core scenes);
# levels 05 and 06 are read in the thermal-neutral scenes (the cross-run page's 2026-10-06 correction)
MAIN_SET = {"l04": "core", "l05": "neutral", "l05fix": "neutral", "l06": "neutral"}
SET_NAME = {"core": "core scenes", "neutral": "neutral scenes", "own": "own scenes"}
GRID = {"l04": ("grid", "gridchase"), "l05": ("grid", "gridchase"), "l05fix": ("grid", "gridchase"),
        "l06": ("grid", "grid")}
LEVEL_NAME = {"l04": "level 04", "l05": "level 05 (temperature)", "l05fix": "level 05, fixed start temperature",
              "l06": "level 06 (temperature + thirst)"}

for _lv in LEVELS:
    for _s in SEEDS:
        base, chase = GRID[_lv]
        HL.INJ_GRID[f"rep_{_lv}_s{_s}"] = (
            f"replication {LEVEL_NAME[_lv]}, seed {_s}",
            {a: f"{REP}/{_lv}_{base}/{_lv}_{a}_s{_s}" for a in ("ordinary", "modulated")},
            {a: f"{REP}/{_lv}_{chase}/{_lv}_{a}_s{_s}" for a in ("ordinary", "modulated")})

REFERENCE = {  # the 22-Sep originals (one seed) in the matching scene sets
    "l04": {a: f"{AV}/metrics_history_rppo_basicq2_wave2_blocking_bush/lvl04_{x}" for a, x in
            (("ordinary", "control"), ("modulated", "modulated"))},
    "l05": {a: f"{AV}/metrics_history_rppo_thermalprobe_neutral_clean/lvl05_{x}" for a, x in
            (("ordinary", "control"), ("modulated", "modulated"))},
}


def leaf(level, scene_set, agent, seed):
    return f"{REP}/{level}_{scene_set}/{level}_{agent}_s{seed}"


def effect(leaf_, a, b):
    """(mean, lo, hi, n) of a per-checkpoint difference a - b, each (scene, injury), on the 2-10 M grid."""
    va, vb = HL.series(leaf_, *a), HL.series(leaf_, *b)
    if va is None or vb is None:
        return None
    v = K.on_grid((va - vb).dropna(), HL.LO_M, HL.HI_M, HL.SPACING_M)
    p = C.P.W.window_profile(v.to_numpy(), windows=[len(v)]).iloc[0]
    return float(p["mean"]), float(p["lo"]), float(p["hi"]), len(v)


MEASURES = (("inj", (("none", "70"), ("none", "00")), "injury effect, no animal:\ninjured (70) minus unhurt (0),\nbush dwell (pp)"),
            ("injw", (("rabbitwander", "70"), ("rabbitwander", "00")), "injury effect, wandering rabbit:\ninjured (70) minus unhurt (0),\nbush dwell (pp)"),
            ("pred", (("pred", "00"), ("none", "00")), "animal effect: hunting predator\nminus no animal, unhurt,\nbush dwell (pp)"))


def summary_rows():
    """[(label, {agent: {measure: (mean, lo, hi, n)}}, is_reference)] in display order."""
    out = []
    for lv in LEVELS:
        if lv in REFERENCE:
            out.append((f"22 Sep original, {LEVEL_NAME[lv]}, seed 42",
                        {a: {m: effect(REFERENCE[lv][a], *ab) for m, ab, _ in MEASURES} for a in ("ordinary", "modulated")},
                        True))
        for s in SEEDS:
            out.append((f"replication, {LEVEL_NAME[lv]}, seed {s}",
                        {a: {m: effect(leaf(lv, MAIN_SET[lv], a, s), *ab) for m, ab, _ in MEASURES}
                         for a in ("ordinary", "modulated")}, False))
    return out


def fig_summary():
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    R = summary_rows()[::-1]
    fig, axs = plt.subplots(1, 3, figsize=(12.0, 0.62 * len(R) + 1.9), sharey=True)
    y = np.arange(len(R))
    off = {"ordinary": 0.17, "modulated": -0.17}
    rows = []
    for ax, (m, _, xl) in zip(axs, MEASURES):
        vals = [e[m] for _, E, _ in R for e in E.values() if e[m] is not None]
        if m in ("inj", "injw"):     # the two injury panels share one scale (register F10)
            vals = [e[k] for _, E, _ in R for e in E.values() for k in ("inj", "injw") if e[k] is not None]
        x0, x1 = min(-2, min(v[1] for v in vals) - 2), max(v[2] for v in vals) * 1.25 + 4
        gap = 0.02 * (x1 - x0)
        for yi, (lab, E, ref) in zip(y, R):
            for agent in ("ordinary", "modulated"):
                e = E[agent][m]
                if e is None:
                    continue
                c, yy = HL.AGENT_COL[agent], yi + off[agent]
                ax.plot([e[1], e[2]], [yy, yy], color=c, lw=2.2, solid_capstyle="round", alpha=0.55 if ref else 1)
                ax.plot(e[0], yy, HL.AGENT_MK[agent], color=c, mfc=c if agent == "modulated" else H.PAPER, ms=7.5,
                        mew=1.6, zorder=3, alpha=0.55 if ref else 1)
                ax.text(e[2] + gap, yy, f"{e[0]:+.0f}".replace("-", "−"), va="center",
                        fontsize=H.FS_LABEL - 1, color=H.INK_2)
            if yi > 0:
                ax.axhline(yi - 0.5, color=H.RULE, lw=0.7, zorder=0)
        ax.set_xlim(x0, x1)
        ax.axvline(0, color=H.RULE, lw=1.1, zorder=0)
        ax.set_xlabel(xl, fontsize=H.FS_LABEL)
        ax.grid(axis="y", visible=False)
    axs[0].set_yticks(y)
    axs[0].set_yticklabels([lab.replace(", fixed start temperature,", ",\nfixed start temperature,") for lab, _, _ in R],
                           fontsize=H.FS_LABEL - 1)
    for t, (_, _, ref) in zip(axs[0].get_yticklabels(), R):
        if ref:
            t.set_color(H.INK_2)
    axs[0].set_ylim(-0.6, len(R) - 0.4)
    hs = [Line2D([], [], color=HL.AGENT_COL[a], marker=HL.AGENT_MK[a], mfc=HL.AGENT_COL[a] if a == "modulated" else H.PAPER,
                 mew=1.6, lw=2.2, label=f"{a} agent ({'upper' if a == 'ordinary' else 'lower'} mark)") for a in HL.AGENT_COL]
    fig.legend(handles=hs, loc="upper center", ncol=2, frameon=False, fontsize=H.FS_LABEL, bbox_to_anchor=(0.62, 1.0))
    fig.subplots_adjust(left=0.30, right=0.98, top=0.94, bottom=0.17 * 12 / len(R), wspace=0.12)
    for lab, E, ref in R:
        for a in E:
            n = E[a]["inj"][3] if E[a]["inj"] else 0
            why = "0.2 M grid from 2 to 10 M training steps; 30 episodes per checkpoint, scene and injury"
            if n < HL.GRID_N:
                why = f"the last {HL.GRID_N - n} grid checkpoints were not tested (testing stopped before 10 M); " + why
            rows.append({"what": f"{lab}, {a}: checkpoints used", "used": n, "total": HL.GRID_N, "note": why})
    return fig, rows


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--fig-dir", required=True)
    ap.add_argument("--figure", required=True, choices=["summary", "dose", "train"])
    ap.add_argument("--level", choices=LEVELS)
    ap.add_argument("--seed", type=int, choices=SEEDS)
    a = ap.parse_args(argv)
    H.apply()
    if a.figure == "summary":
        fig, rows = fig_summary()
        stem = "rep_summary"
    elif a.figure == "dose":
        fig, rows = HL.fig_injdose_seeds([f"rep_{a.level}_s{s}" for s in SEEDS])
        stem = f"rep_dose__{a.level}"
    else:
        fig, rows = HL.fig_injtrain(f"rep_{a.level}_s{a.seed}")
        stem = f"rep_train__{a.level}_s{a.seed}"
    HL.FG.record_samples(os.path.abspath(a.fig_dir), stem, rows)
    HL.FG.save(fig, os.path.abspath(a.fig_dir), stem)


if __name__ == "__main__":
    main()
