#!/usr/bin/env python3
"""readout.py - stage-1 readout of the level-05 modulator screens (capacity grid, input sets).

Each screen trains one seed (42) per modulator setting at level 05 and tests it like the fast-heal
replication (docs/experiments/active/hypervigilance/NMN_CAPACITY_GRID_L05.md, NMN_INPUT_L05.md). This
draws, per scene set (neutral, own), every setting's three effects - injury 70 minus 0 with no animal,
the same with the wandering rabbit, hunting predator minus no animal (unhurt) - beside the six existing
level-05 agents (ordinary and current modulated, seeds 42-44), and writes a table with the two candidate
stage-2 rules as reference columns only (the user decides stage 2 by judgement).

All numbers: mean over the 0.2 M checkpoint grid from 2 to 10 M training steps with the lag-1-corrected
95 % interval (fast_heal_replication/figures.py effect()); runs still training use the checkpoints so far
(the "ckpts" column says how many of the planned 41).

    $P scripts/analysis/studies/nmn_screens/readout.py --study cap|inp --fig-dir <dir>
"""
from __future__ import annotations

import argparse
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "fast_heal_replication"))
import figures as RF  # noqa: E402  (effect, MEASURES, HL, H)

HL, H = RF.HL, RF.H
AV = "results/eval/avoidance"
STUDY = {
    "cap": ("metrics_history_rppo_nmncap", [f"h{h}g{g}" for h in (32, 64, 128) for g in (8, 16, 32)],
            lambda c: f"size {c[1:c.index('g')]}, grouping {c[c.index('g') + 1:]}"),
    "inp": ("metrics_history_rppo_nmninp", ["N", "I", "IT", "X"],
            lambda c: {"N": "reads felt injury only", "I": "reads fullness + felt injury",
                       "IT": "reads all body signals", "X": "reads outside world only"}[c]),
}
SETS = ("neutral", "own")
# candidate stage-2 rules (reference only; NMN_CAPACITY_GRID_L05.md section 5.1 and its plan-review option A)
STRICT = dict(injw=12.2, inj=14.7, lo_injw=9.2, lo_inj=11.7)
OPT_A = dict(injw=9.2, inj=10.65, own_injw=8.8, own_inj=9.1)


def ref_leaf(scene_set, agent, seed):
    return f"{RF.REP}/l05_{scene_set}/l05_{agent}_s{seed}"


def rows(study):
    folder, cells, name = STUDY[study]
    out = []
    for a in ("ordinary", "modulated"):
        for s in RF.SEEDS:
            out.append(("reference", f"{a} agent (size 16, grouping 1, reads all), seed {s}" if a == "modulated"
                        else f"ordinary agent, seed {s}", {st: ref_leaf(st, a, s) for st in SETS}))
    for c in cells:
        out.append(("cell", f"{name(c)}, seed 42", {st: f"{AV}/{folder}/l05_{st}/l05_{c}_s42" for st in SETS}))
    return out


def measures(leaf):
    return {m: RF.effect(leaf, *ab) for m, ab, _ in RF.MEASURES}


def table(study):
    recs = []
    for kind, lab, leaves in rows(study):
        r = {"kind": kind, "row": lab}
        for st in SETS:
            E = measures(leaves[st]) if os.path.isdir(os.path.join(HL.C.ROOT, leaves[st])) else {}
            for m, *_ in RF.MEASURES:
                e = E.get(m)
                r[f"{st}_{m}"], r[f"{st}_{m}_lo"], r[f"{st}_{m}_hi"] = (e[0], e[1], e[2]) if e else (None,) * 3
                r[f"{st}_ckpts"] = e[3] if e else 0
        recs.append(r)
    T = pd.DataFrame(recs)
    c = T.kind == "cell"
    T.loc[c, "rule_strict"] = ((T.neutral_injw >= STRICT["injw"]) & (T.neutral_inj >= STRICT["inj"])
                               & (T.neutral_injw_lo > STRICT["lo_injw"]) & (T.neutral_inj_lo > STRICT["lo_inj"]))[c]
    T.loc[c, "rule_option_A"] = ((T.neutral_injw >= OPT_A["injw"]) & (T.neutral_inj >= OPT_A["inj"])
                                 & (T.own_injw >= OPT_A["own_injw"]) & (T.own_inj >= OPT_A["own_inj"]))[c]
    return T


def figure(T, scene_set):
    import matplotlib.pyplot as plt
    import numpy as np
    R = T.iloc[::-1].reset_index(drop=True)
    fig, axs = plt.subplots(1, 3, figsize=(12.0, 0.42 * len(R) + 1.9), sharey=True)
    y = np.arange(len(R))
    data_rows = []
    for ax, (m, _, xl) in zip(axs, RF.MEASURES):
        vals = [v for k in (("inj", "injw") if m != "pred" else ("pred",))
                for col in (f"{scene_set}_{k}_lo", f"{scene_set}_{k}_hi") for v in R[col].dropna()]
        x0, x1 = min(-2, min(vals) - 2), max(vals) * 1.25 + 4
        for yi, r in R.iterrows():
            mu, lo, hi = r[f"{scene_set}_{m}"], r[f"{scene_set}_{m}_lo"], r[f"{scene_set}_{m}_hi"]
            if pd.isna(mu):
                continue
            ref = r.kind == "reference"
            agent = "ordinary" if r.row.startswith("ordinary") else "modulated"
            c = HL.AGENT_COL[agent] if ref else H.BLUE
            ax.plot([lo, hi], [yi, yi], color=c, lw=2.0, alpha=0.6 if ref else 1, solid_capstyle="round")
            ax.plot(mu, yi, HL.AGENT_MK[agent] if ref else "D", color=c, ms=6.5, mew=1.4, zorder=3,
                    mfc=(H.PAPER if agent == "ordinary" else c) if ref else c, alpha=0.6 if ref else 1)
            ax.text(hi + 0.02 * (x1 - x0), yi, f"{mu:+.0f}".replace("-", "−"), va="center",
                    fontsize=H.FS_LABEL - 1, color=H.INK_2)
        n_ref = int((R.kind == "reference").sum())
        ax.axhline(len(R) - n_ref - 0.5, color=H.INK_2, lw=0.9)
        ax.set_xlim(x0, x1)
        ax.axvline(0, color=H.RULE, lw=1.1, zorder=0)
        ax.set_xlabel(xl, fontsize=H.FS_LABEL)
        ax.grid(axis="y", visible=False)
    axs[0].set_yticks(y)
    axs[0].set_yticklabels(R.row, fontsize=H.FS_LABEL - 1)
    for t, k in zip(axs[0].get_yticklabels(), R.kind):
        t.set_color(H.INK_2 if k == "reference" else H.INK)
    axs[0].set_ylim(-0.6, len(R) - 0.4)
    fig.subplots_adjust(left=0.33, right=0.98, top=0.97, bottom=0.17 * 14 / len(R), wspace=0.12)
    for _, r in R.iterrows():
        data_rows.append({"what": f"{r.row}: checkpoints used", "used": int(r[f"{scene_set}_ckpts"]),
                          "total": HL.GRID_N, "note": "0.2 M grid 2-10 M training steps; 30 episodes per checkpoint, "
                          "scene and injury" + ("" if r[f"{scene_set}_ckpts"] >= HL.GRID_N else
                                                "; run still training or not yet tested to 10 M")})
    return fig, data_rows


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--study", required=True, choices=list(STUDY))
    ap.add_argument("--fig-dir", required=True)
    a = ap.parse_args(argv)
    H.apply()
    T = table(a.study)
    os.makedirs(a.fig_dir, exist_ok=True)
    T.to_csv(os.path.join(a.fig_dir, f"screen_{a.study}_table.csv"), index=False, float_format="%.2f")
    for st in SETS:
        fig, data_rows = figure(T, st)
        stem = f"screen_{a.study}__{st}"
        HL.FG.record_samples(os.path.abspath(a.fig_dir), stem, data_rows)
        HL.FG.save(fig, os.path.abspath(a.fig_dir), stem)
    show = ["row", "neutral_inj", "neutral_injw", "neutral_pred", "own_inj", "own_injw", "neutral_ckpts",
            "rule_strict", "rule_option_A"]
    print(T[show].to_string(index=False, float_format=lambda v: f"{v:+.1f}"))


if __name__ == "__main__":
    main()
