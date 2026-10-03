#!/usr/bin/env python3
"""f1_behaviours_survival.py - Figure 1: how much of its time each run spends on each behaviour,
how long it survives, and how its episodes end.

Plan: BASIC_BEHAVIOUR_ANALYSIS_PIPELINE.md (Revision 2), Figure scripts, F1.
Reads caches only (sweep.py's episodes.npz + inventory.json); seconds.

    $P scripts/analysis/basic_behaviour/f1_behaviours_survival.py --population <json> \
        --out-root <abs results/analysis/basic_behaviour/<pop>> --fig-dir <page dir>/figures

Panels: one per behaviour available in any run (share of chosen steps, %, per run, grouped by world x
agent, one marker per seed); mean survival in steps per run (episode `length`, the project's
evaluation metric); share of episodes ending in each way, per run.
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _fig as FG                                                       # noqa: E402
import registry as REG                                                  # noqa: E402

STEM = "f1_behaviours_survival"
TERM_SHORT = {1: "step limit\nreached", 2: "starved", 3: "over-ate", 4: "injury at\nmaximum",
              5: "temperature\nout of range", 6: "died of\nthirst", 7: "over-drank"}
TARGET_KEY = {"bush_dwell": "bush_steps", "eating": "y_eat", "near_rabbit": "y_near_rab",
              "near_predator": "y_near_pred", "warm_cell": "y_warm", "pond": "y_pond"}


def target_info(c, t) -> dict:
    """The inventory's entry for target t; a target the world does not have (the pond, in a world
    without water, or an inventory written before the pond target existed) is unavailable."""
    return c["inv"]["targets"].get(t) or {"available": False, "reason": "this world has no water"}


def main(argv=None):
    a = FG.args(argv=argv)
    H = FG.H
    H.apply()
    import matplotlib.pyplot as plt
    D = FG.load_outputs(a.population, a.out_root, need_episodes=True)
    cells = D["cells"]
    if not cells:
        raise SystemExit("no swept cells")
    targets = [t for t in REG.TARGETS if any(target_info(c, t)["available"] for c in cells)]
    TERM = FG.term_names(cells)             # codes 6 and 7 only for populations with water (D9)
    pos, ticks, labels = FG.group_positions(D)
    rows = []
    stats = {}
    for c in cells:
        e = c["ep"]
        L = e["n_steps"]
        s = {"n": int(L.size), "survival": float(e["length"].mean()), "steps": float(L.sum()),
             "rows": float(e["n_rows"].sum())}
        for t in targets:
            if target_info(c, t)["available"]:
                s[t] = 100.0 * float(e[f"y__{t}"].sum() / L.sum())
        term = e["term"]
        s["term"] = {k: 100.0 * float((term == k).mean()) for k in TERM}
        other = 100.0 * float((~np.isin(term, list(TERM))).mean())
        if other > 0:
            raise SystemExit(f"{c['label']}: {other:.3f}% of episodes have an unknown termination code")
        stats[c["label"]] = s
        rows.append({"what": f"episodes, {FG.run_label(c)}", "used": s["n"], "total": s["n"],
                     "note": "every evaluation episode in the store"})
        for t in [t for t in REG.TARGETS if t in c["inv"]["targets"] or t in targets]:
            if not target_info(c, t)["available"]:
                rows.append({"what": f"{FG.TARGET_NOUN[t]}, {FG.run_label(c)}", "used": 0, "total": s["n"],
                             "note": f"not available: {target_info(c, t)['reason']}"})
    rows.append({"what": "chosen steps (t >= 1), all runs", "used": int(sum(s["steps"] for s in stats.values())),
                 "total": int(sum(s["rows"] for s in stats.values())),
                 "note": "the reset row t = 0 is the random spawn, not a step the agent chose"})
    for c in D["unswept"]:
        rows.append({"what": f"not swept yet: {FG.run_label(c)}", "used": 0, "total": 0,
                     "note": "completed in the manifest; sweep.py has not been run on it"})
    for c in D["not_completed"]:
        rows.append({"what": f"not completed: {c['label']}", "used": 0, "total": 0,
                     "note": f"manifest status '{c['status']}'"})

    # behaviour panels + survival take one slot each; the termination panel takes two
    ncol = 4
    k = len(targets) + 1                  # first slot of the termination panel
    if k % ncol == ncol - 1:              # no room for two slots on this row
        k += 1
    nrow = int(np.ceil((k + 2) / ncol))
    fig = plt.figure(figsize=(12.0, 5.0 * nrow))
    gs = fig.add_gridspec(nrow, ncol)
    axs = [fig.add_subplot(gs[i // ncol, i % ncol]) for i in range(len(targets) + 1)]
    axs.append(fig.add_subplot(gs[k // ncol, k % ncol:k % ncol + 2]))

    def top(ax, vmax):
        ax.set_ylim(0, vmax * 1.18 if vmax > 0 else 1)

    def dots(ax, key):
        for c in cells:
            v = stats[c["label"]].get(key)
            if v is None:
                continue
            ax.plot(pos[c["label"]], v, ls="", marker=D["marker"][c["agent"]], ms=7,
                    color=D["colour"][c["world"]], alpha=0.9)
        ax.set_xticks(ticks)
        ax.set_xticklabels(labels, fontsize=H.FS_LABEL, rotation=90)
        ax.set_xlim(min(ticks) - 0.6, max(ticks) + 0.6)

    for i, t in enumerate(targets):
        ax = axs[i]
        dots(ax, t)
        ax.set_title(FG.TARGET_TITLE[t], fontsize=H.FS_BODY)
        ax.set_ylabel("share of chosen steps (%)")
        top(ax, max(stats[c["label"]].get(t, 0) for c in cells))
    ax = axs[len(targets)]
    dots(ax, "survival")
    ax.set_title("Survival", fontsize=H.FS_BODY)
    ax.set_ylabel("mean episode length (steps)")
    top(ax, max(stats[c["label"]]["survival"] for c in cells))
    ax = axs[len(targets) + 1]
    for k, (code, name) in enumerate(TERM.items()):
        for j, c in enumerate(cells):
            off = (j - (len(cells) - 1) / 2) * (0.7 / max(len(cells), 1))
            ax.plot(k + off, stats[c["label"]]["term"][code], ls="", marker=D["marker"][c["agent"]],
                    ms=6, color=D["colour"][c["world"]], alpha=0.9)
    ax.set_xticks(range(len(TERM)))
    ax.set_xticklabels([TERM_SHORT[c] for c in TERM], fontsize=H.FS_LABEL)
    ax.set_title("How episodes end", fontsize=H.FS_BODY)
    ax.set_ylabel("share of episodes (%)")
    top(ax, max(max(stats[c["label"]]["term"].values()) for c in cells))
    fig.legend(handles=FG.legend_handles(D), loc="lower center", ncol=len(D["worlds"]) + len(D["agents"]),
               frameon=False, bbox_to_anchor=(0.5, -0.02), fontsize=H.FS_LABEL)
    fig.tight_layout(rect=(0, 0.06, 1, 1), h_pad=2.2, w_pad=1.6)
    FG.record_samples(a.fig_dir, STEM, rows)
    FG.save(fig, a.fig_dir, STEM)


if __name__ == "__main__":
    main()
