#!/usr/bin/env python3
"""f3_univariate.py - Figure 3: each factor on its own, per run (one quasi-binomial fit per factor).

Plan: BASIC_BEHAVIOUR_ANALYSIS_PIPELINE.md (Revision 2), Figure scripts, F3. Reads
<cell>/<target>/univariate.csv (fit.py --kind univariate); seconds.

Rows: factors ranked by the median, across runs, of |change in percentage points per +1 SD|;
exogenous factors (drawn before the agent acts) on the left, consequences (produced during the
episode, association only) on the right. x: change in the behaviour's share, in percentage points,
per +1 standard deviation of the factor. One marker per run (colour = world, shape = agent).
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _fig as FG                                                       # noqa: E402
import registry as REG                                                  # noqa: E402

STEM = "f3_univariate"


def main(argv=None):
    import pandas as pd
    a = FG.args([("--target", dict(required=True, choices=sorted(REG.TARGETS)))], argv)
    H = FG.H
    H.apply()
    import matplotlib.pyplot as plt
    D = FG.load_outputs(a.population, a.out_root)
    frames, rows = [], []
    for c in D["cells"]:
        p = os.path.join(c["dir"], a.target, "univariate.csv")
        if not c["inv"]["targets"][a.target]["available"]:
            rows.append({"what": FG.run_label(c), "used": 0, "total": c["inv"]["n_episodes"],
                         "note": f"not available: {c['inv']['targets'][a.target]['reason']}"})
            continue
        if not os.path.exists(p):
            raise SystemExit(f"{c['label']}: no {p} -- run fit.py --kind univariate --target {a.target}")
        u = pd.read_csv(p)
        u["label"] = c["label"]
        frames.append(u)
        n = c["inv"]["n_episodes"]
        for sub, test, why in (
                ("factors defined on every episode", lambda t: t == "start_injury",
                 "all episodes"),
                ("predator traits and smell", lambda t: t.startswith("pred_"),
                 "episodes with exactly one predator: a single predator's traits are defined only there"),
                ("rabbit smell", lambda t: t.startswith("rab_"),
                 "episodes with exactly one rabbit: a single rabbit's smell is defined only there")):
            hit = u[u.term.map(test)]
            if len(hit):
                rows.append({"what": f"{sub}, {FG.run_label(c)}", "used": int(hit.n.max()), "total": n,
                             "note": why})
    U = pd.concat(frames)
    cmap = {c["label"]: c for c in D["cells"]}
    blocks = [("exogenous", "Drawn before the agent acts\n(own horizontal scale)"),
              ("consequence", "Produced during the episode\n(own horizontal scale)")]
    order = {}
    for b, _ in blocks:
        s = U[U.block == b].groupby("term").dpp_per_sd.apply(lambda x: np.median(np.abs(x)))
        order[b] = list(s.sort_values(ascending=True).index)
    nmax = max(len(v) for v in order.values())
    fig, axs = plt.subplots(1, 2, figsize=(12.0, 0.36 * nmax + 2.4))
    for ax, (b, title) in zip(axs, blocks):
        terms = order[b]
        for i, t in enumerate(terms):
            sub = U[(U.block == b) & (U.term == t)]
            k = len(sub)
            for j, r in enumerate(sub.itertuples()):
                c = cmap[r.label]
                dy = (j - (k - 1) / 2) * (0.5 / max(k, 1))
                ax.plot(r.dpp_per_sd, i + dy, ls="", marker=D["marker"][c["agent"]], ms=5.5,
                        color=D["colour"][c["world"]], alpha=0.9)
        ax.axvline(0, color=H.RULE, lw=1)
        ax.set_yticks(range(len(terms)))
        ax.set_yticklabels([FG.flabel(t) for t in terms], fontsize=H.FS_LABEL)
        ax.set_ylim(-0.7, len(terms) - 0.3)
        ax.grid(axis="x", color=H.TICK_LINE)
        ax.grid(axis="y", visible=False)
        ax.set_title(title, fontsize=H.FS_BODY)
        ax.set_xlabel("change in share of steps (percentage\npoints per +1 standard deviation)")
    fig.legend(handles=FG.legend_handles(D), loc="lower center", ncol=len(D["worlds"]) + len(D["agents"]),
               frameon=False, fontsize=H.FS_LABEL, bbox_to_anchor=(0.5, -0.01))
    fig.tight_layout(rect=(0, 0.05, 1, 1), w_pad=2.0)
    stem = f"{STEM}__{a.target}"
    FG.record_samples(a.fig_dir, stem, rows)
    FG.save(fig, a.fig_dir, stem)


if __name__ == "__main__":
    main()
