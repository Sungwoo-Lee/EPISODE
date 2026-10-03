#!/usr/bin/env python3
"""f4_multivariate.py - Figure 4: the factors fitted together, per run (models M1-M5 of the hiding page).

Plan: BASIC_BEHAVIOUR_ANALYSIS_PIPELINE.md (Revision 2), Figure scripts, F4. Reads
<cell>/<target>/multivariate.csv and prefit.json (fit.py --kind multivariate); seconds.

One panel per model, in the legacy order M1, M2, M3, M5, M4. Rows: the model's terms; x: change in
the behaviour's share in percentage points per +1 SD of the term, holding the model's other terms
fixed. One marker per run (colour = world, shape = agent). Models skipped in a run are listed in the
data statement.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _fig as FG                                                       # noqa: E402
import registry as REG                                                  # noqa: E402

STEM = "f4_multivariate"
MODELS = ["M1", "M2", "M3", "M4", "M5"]          # numeric order on the page (the CSVs keep the legacy order)
SHORT = {"M1": "M1  features drawn before the agent acts, all episodes",
         "M2": "M2  + predator traits, episodes with one predator",
         "M3": "M3  + rabbit smell, episodes with one predator and one rabbit",
         "M4": "M4  + what happened during the episode, all episodes",
         "M5": "M5  episodes with two predators: keener vs less keen"}
WHY = {"M1": "all episodes", "M2": "episodes with exactly one predator",
       "M3": "episodes with exactly one predator and exactly one rabbit", "M4": "all episodes",
       "M5": "episodes with exactly two predators"}


def main(argv=None):
    import pandas as pd
    a = FG.args([("--target", dict(required=True, choices=sorted(REG.TARGETS)))], argv)
    H = FG.H
    H.apply()
    import matplotlib.pyplot as plt
    D = FG.load_outputs(a.population, a.out_root)
    frames, rows = [], []
    for c in D["cells"]:
        if not c["inv"]["targets"][a.target]["available"]:
            continue
        p = os.path.join(c["dir"], a.target, "multivariate.csv")
        if not os.path.exists(p):
            raise SystemExit(f"{c['label']}: no {p} -- run fit.py --kind multivariate --target {a.target}")
        m = pd.read_csv(p)
        m["label"] = c["label"]
        m["mid"] = m.model.str.split(" ").str[0]
        frames.append(m)
        rec = json.load(open(os.path.join(c["dir"], a.target, "prefit.json"))).get("multivariate", {})
        n = c["inv"]["n_episodes"]
        for mid in MODELS:
            r = rec.get(mid)
            if r is None:
                continue
            if "skipped" in r:
                rows.append({"what": f"{mid}, {FG.run_label(c)}", "used": 0, "total": n,
                             "note": f"skipped: {r['skipped']}"})
            else:
                ex = "; ".join(f"{FG.flabel(e['name'])} ({e['reason']})" for e in r.get("excluded", []))
                rows.append({"what": f"{mid}, {FG.run_label(c)}", "used": r["n"], "total": n,
                             "note": WHY[mid] + (f"; dropped inside the model: {ex}" if ex else "")})
    M = pd.concat(frames)
    M = M[M.term != "const"]
    present = [m for m in MODELS if (M.mid == m).any()]
    cmap = {c["label"]: c for c in D["cells"]}
    sizes = [M[M.mid == m].term.nunique() for m in present]
    fig, axs = plt.subplots(len(present), 1, figsize=(12.0, 0.3 * sum(sizes) + 1.3 * len(present) + 1.0),
                            gridspec_kw={"height_ratios": sizes}, squeeze=False)
    for ax, mid in zip(axs[:, 0], present):
        sub = M[M.mid == mid]
        terms = list(dict.fromkeys(sub.term))
        for i, t in enumerate(terms):
            st = sub[sub.term == t]
            k = len(st)
            for j, r in enumerate(st.itertuples()):
                c = cmap[r.label]
                dy = (j - (k - 1) / 2) * (0.5 / max(k, 1))
                ax.plot(r.dpp_per_sd, i + dy, ls="", marker=D["marker"][c["agent"]], ms=5.5,
                        color=D["colour"][c["world"]], alpha=0.9)
        ax.axvline(0, color=H.RULE, lw=1)
        ax.set_yticks(range(len(terms)))
        ax.set_yticklabels([FG.flabel(t) for t in terms], fontsize=H.FS_LABEL)
        ax.set_ylim(len(terms) - 0.3, -0.7)
        ax.grid(axis="x", color=H.TICK_LINE)
        ax.grid(axis="y", visible=False)
        ax.set_title(SHORT[mid] + "  (own horizontal scale)", fontsize=H.FS_BODY)
        ax.set_xlabel("change in share of steps (percentage points per +1 standard deviation, other terms held fixed)")
    fig.legend(handles=FG.legend_handles(D), loc="lower center", ncol=FG.legend_ncol(D),
               frameon=False, fontsize=H.FS_LABEL, bbox_to_anchor=(0.5, -0.005))
    fig.tight_layout(rect=(0, 0.025, 1, 1), h_pad=1.6)
    stem = f"{STEM}__{a.target}"
    FG.record_samples(a.fig_dir, stem, rows)
    FG.save(fig, a.fig_dir, stem)


if __name__ == "__main__":
    main()
