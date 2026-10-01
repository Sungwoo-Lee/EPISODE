#!/usr/bin/env python3
"""f5_settings.py - Figure 5: which settings move each behaviour (exploratory screening across runs).

Plan: BASIC_BEHAVIOUR_ANALYSIS_PIPELINE.md (Revision 2), A7, B5, Figure scripts, F5. Reads
<out-root>/screen/<target>/{per_run,cells,contrasts,variance}.csv (screen.py); seconds.

(a) primary ranking: each contrast between settings divided by the seed-to-seed SD (standardised
    effect), with its run-level 95 % interval, sorted; behaviour level and the start-injury and
    start-nutrition slopes only - never the smell slopes (Revision 2, N5);
(b) secondary: method-of-moments variance components per quantity, truncated at 0 (flagged), each
    with the share its raw sum of squares would take under pure seed noise as a reference mark;
(c) per world x agent cell: the per-run values and the cell mean +/- seed-to-seed SD for the level,
    start injury, start nutrition, smell (per nat) and smell x start injury. The two smell panels
    carry no test and no interval: exploratory screening, not the smell study's pre-registered verdict.
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _fig as FG                                                       # noqa: E402
import registry as REG                                                  # noqa: E402

STEM = "f5_settings"
QLAB = {"level": "behaviour level (logit of share)",
        "start_injury": "start injury slope (logit per 10 points)",
        "start_nutrition": "start nutrition slope (logit per 10 points)",
        "smell": "rabbit smell slope (logit per nat)",
        "smell_x_injury": "smell x start injury (logit per nat per 10 points)"}
SMELL = {"smell", "smell_x_injury"}
SCREEN_NOTE = "exploratory screening - not the smell study's pre-registered verdict"


def main(argv=None):
    import pandas as pd
    a = FG.args([("--target", dict(required=True, choices=sorted(REG.TARGETS)))], argv)
    H = FG.H
    H.apply()
    import matplotlib.pyplot as plt
    D = FG.load_outputs(a.population, a.out_root)
    sd = os.path.join(a.out_root, "screen", a.target)
    for f in ("per_run.csv", "cells.csv", "contrasts.csv", "variance.csv"):
        if not os.path.exists(os.path.join(sd, f)):
            raise SystemExit(f"no {sd}/{f} -- run screen.py --target {a.target}")
    PR = pd.read_csv(os.path.join(sd, "per_run.csv"))
    CE = pd.read_csv(os.path.join(sd, "cells.csv"))
    CO = pd.read_csv(os.path.join(sd, "contrasts.csv"))
    VA = pd.read_csv(os.path.join(sd, "variance.csv"))
    if CO.quantity.isin(SMELL).any() or VA.get("quantity", pd.Series(dtype=str)).isin(SMELL).any():
        raise SystemExit("smell quantities found in contrasts / variance outputs (Revision 2, N5)")
    cmap = {c["label"]: c for c in D["cells"]}
    qs = [q for q in QLAB if (PR.quantity == q).any()]
    hA, hB, hC = max(len(CO), 1) * 0.36 + 1.2, max(len(VA), 1) * 0.3 + 1.2, 6.0
    fig = plt.figure(figsize=(12.0, hA + hB + hC + 0.8))
    top, bot = fig.subfigures(2, 1, height_ratios=[hA + hB, hC])
    gs = top.add_gridspec(2, 1, height_ratios=[hA, hB])
    gsc = bot.add_gridspec(1, len(qs))

    def plain(text):
        pairs = list(FG.WORLD_SHORT.items()) + list(FG.AGENT_SHORT.items())
        for code, lab in sorted(pairs, key=lambda kv: -len(kv[0])):     # hv1chm before hv1ch
            text = text.replace(code, lab)
        return text.replace(" | ", ", within ")
    # (a) standardised effects
    ax = top.add_subplot(gs[0])
    C = CO.assign(lab=CO.quantity.map(lambda q: q.replace("_", " ")) + ": " + CO.contrast.map(plain))
    C = C.reindex(C.standardised.abs().sort_values().index)
    for i, r in enumerate(C.itertuples()):
        ax.plot([r.std_ci_lo, r.std_ci_hi], [i, i], color=H.INK_2, lw=1.4)
        ax.plot(r.standardised, i, "o", color=H.INK, ms=5)
    ax.axvline(0, color=H.RULE, lw=1)
    ax.set_yticks(range(len(C)))
    ax.set_yticklabels(C.lab, fontsize=H.FS_LABEL)
    ax.grid(axis="y", visible=False); ax.grid(axis="x", color=H.TICK_LINE)
    ax.set_xlabel("contrast divided by the seed-to-seed SD (standardised effect), with run-level 95% interval")
    ax.set_title("(a) Setting contrasts, ranked", fontsize=H.FS_BODY)
    # (b) variance components
    ax = top.add_subplot(gs[1])
    V = VA.dropna(subset=["share_mom"]) if "share_mom" in VA else VA.iloc[0:0]
    labs = []
    for i, r in enumerate(V.itertuples()):
        ax.barh(i, r.share_mom, color=H.INK_2 if not r.truncated else H.RULE, height=0.6)
        ax.plot([r.pure_noise_reference] * 2, [i - 0.38, i + 0.38], color=H.ORANGE, lw=2)
        if r.truncated:
            ax.text(0.005, i, "0 (truncated)", va="center", fontsize=H.FS_LABEL, color=H.INK)
        labs.append(f"{r.quantity.replace('_', ' ')}: {r.component}")
    ax.set_yticks(range(len(labs))); ax.set_yticklabels(labs, fontsize=H.FS_LABEL)
    ax.set_xlim(0, 1)
    ax.grid(axis="y", visible=False); ax.grid(axis="x", color=H.TICK_LINE)
    ax.set_xlabel("share of run-to-run variation (orange tick: share expected from seed noise alone)")
    ax.set_title("(b) Variance components (secondary description)", fontsize=H.FS_BODY)
    # (c) per cell
    pos, ticks, tlabels = FG.group_positions(D)
    for k, q in enumerate(qs):
        ax = bot.add_subplot(gsc[0, k])
        sub = PR[PR.quantity == q]
        for r in sub.itertuples():
            c = cmap[r.label]
            ax.plot(pos[r.label], r.coef, ls="", marker=D["marker"][c["agent"]], ms=5.5,
                    color=D["colour"][c["world"]], alpha=0.9)
        for r in CE[CE.quantity == q].itertuples():
            grp = [c["label"] for c in D["cells"] if c["world"] == r.world and c["agent"] == r.agent]
            x0 = np.mean([pos[g] for g in grp])
            ax.errorbar(x0 + 0.42, r.mean, yerr=r.seed_sd_pooled, fmt="_", color=H.INK, ms=10, lw=1.2)
        ax.set_xticks(ticks)
        ax.set_xticklabels(tlabels, rotation=90, fontsize=H.FS_LABEL)
        ax.axhline(0, color=H.RULE, lw=1)
        ax.set_title(QLAB[q].split(" (")[0].replace(" slope", "").replace(" x ", " x\n")
                     + ("\n(screening,\nno test)" if q in SMELL else ""), fontsize=H.FS_LABEL)
        ax.set_ylabel(QLAB[q][QLAB[q].find("(") + 1:-1] if "(" in QLAB[q] else "")
    bot.suptitle("(c) Per run, and per setting as mean +/- seed-to-seed SD", x=0.02, ha="left",
                 fontsize=H.FS_BODY, fontweight="semibold")
    bot.legend(handles=FG.legend_handles(D), loc="lower center", ncol=len(D["worlds"]) + len(D["agents"]),
               frameon=False, fontsize=H.FS_LABEL, bbox_to_anchor=(0.5, 0.0))
    top.subplots_adjust(left=0.36, right=0.97, top=0.97, bottom=0.05, hspace=0.18)
    bot.subplots_adjust(left=0.07, right=0.98, top=0.82, bottom=0.42, wspace=0.75)
    rows = []
    for r in PR[PR.quantity == "start_injury"].itertuples():
        rows.append({"what": f"within-run model episodes, {FG.run_label(cmap[r.label])}", "used": int(r.n),
                     "total": int(cmap[r.label]["inv"]["n_episodes"]),
                     "note": "exactly one rabbit, any number of predators"})
    import json as _json
    pf = _json.load(open(os.path.join(sd, "prefit.json")))
    noisy = [q for q, v in pf["median_episode_se_vs_seed_sd"].items() if not v["se_below_half_sd"]]
    rows.append({"what": "quantities whose within-run noise is small beside seed-to-seed variation",
                 "used": len(pf["median_episode_se_vs_seed_sd"]) - len(noisy),
                 "total": len(pf["median_episode_se_vs_seed_sd"]),
                 "note": ("median per-run episode-level SE below half the seed-to-seed SD; not so for: "
                          + ", ".join(noisy) + " - for these, part of the spread between seeds is "
                          "estimation noise inside each run") if noisy else
                 "median per-run episode-level SE below half the seed-to-seed SD for every quantity"})
    rows.append({"what": "runs in the cross-run analysis", "used": PR.label.nunique(),
                 "total": PR.label.nunique() + len(D["not_completed"]),
                 "note": "each training run is one replicate"})
    stem = f"{STEM}__{a.target}"
    FG.record_samples(a.fig_dir, stem, rows)
    FG.save(fig, a.fig_dir, stem)


if __name__ == "__main__":
    main()
