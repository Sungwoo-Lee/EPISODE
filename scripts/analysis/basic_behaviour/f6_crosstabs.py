#!/usr/bin/env python3
"""f6_crosstabs.py - Figure 6: the behaviour by the agent's state one step earlier, by the rabbit's
smell, and by which animals are close.

Plan: BASIC_BEHAVIOUR_ANALYSIS_PIPELINE.md (Revision 2), B6, Figure scripts, F6. Reads xtab.npz and
episodes.npz; seconds.

(a) per world x agent cell (seeds pooled, trial-weighted): share of chosen steps in each injury band x
    nutrition band, both read at row t-1 - the state the agent was in when it chose the step;
(b) the behaviour by rabbit-smell sextile: episodes with exactly one rabbit and no predator, cut into sextiles of
    the rabbit's smell on the evidence scale (log-likelihood ratio, nats); one line per run;
(c) share of chosen steps with a rabbit near / far x a predator near / far at row t-1, per run.
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _fig as FG                                                       # noqa: E402
import registry as REG                                                  # noqa: E402

STEM = "f6_crosstabs"
INJ = ["0", "0-25", "25-50", "50+"]
NUT = ["<25", "25-50", "50-75", "75+"]
NEAR = ["both far", "predator near", "rabbit near", "both near"]      # index rabbit*2 + predator


def main(argv=None):
    a = FG.args([("--target", dict(required=True, choices=sorted(REG.TARGETS)))], argv)
    H = FG.H
    H.apply()
    import matplotlib.pyplot as plt
    D = FG.load_outputs(a.population, a.out_root, need_episodes=True)
    cells = [c for c in D["cells"] if c["inv"]["targets"][a.target]["available"]]
    groups = [(w, ag) for w in D["worlds"] for ag in D["agents"]
              if any(c["world"] == w and c["agent"] == ag for c in cells)]
    rows, heat, near, ladder = [], {}, {}, {}
    for c in cells:
        x = np.load(os.path.join(c["dir"], "xtab.npz"))
        e = c["ep"]
        tr = x["inj_nut_trials"]
        if tr.sum() != e["n_steps"].sum():
            raise SystemExit(f"{c['label']}: cross-table trials {tr.sum()} != chosen steps {e['n_steps'].sum()}")
        g = (c["world"], c["agent"])
        h = heat.setdefault(g, [np.zeros(16), np.zeros(16), []])
        h[0] += x[f"inj_nut__{a.target}"]; h[1] += tr; h[2].append(c["seed"])
        near[c["label"]] = 100 * x[f"near__{a.target}"] / np.maximum(x["near_trials"], 1)
        rows.append({"what": f"chosen steps, {FG.run_label(c)}", "used": int(tr.sum()),
                     "total": int(e["n_rows"].sum()),
                     "note": "every step t >= 1, binned by the row before it; the reset row is not a step"})
        rab = next(t["tag"] for t in c["inv"]["slots"]["entities"] if t["cls"] != "predator")
        prd = [t["tag"] for t in c["inv"]["slots"]["entities"] if t["cls"] == "predator"]
        keep = (e[f"cnt__{rab}"] == 1)
        for p in prd:
            keep &= e[f"cnt__{p}"] == 0
        llr = e["rab_smell_llr"][keep]
        y = e[f"y__{a.target}"][keep]
        L = e["n_steps"][keep]
        q = np.quantile(llr, np.linspace(0, 1, 7))
        b = np.clip(np.searchsorted(q, llr, side="right") - 1, 0, 5)
        ladder[c["label"]] = ([float(llr[b == k].mean()) for k in range(6)],
                              [100 * float(y[b == k].sum() / max(L[b == k].sum(), 1)) for k in range(6)])
        rows.append({"what": f"episodes in the smell sextiles, {FG.run_label(c)}", "used": int(keep.sum()),
                     "total": int(keep.size), "note": "exactly one rabbit and no predator"})
    ng = len(groups)
    fig = plt.figure(figsize=(12.0, 3.3 * int(np.ceil(ng / 3)) + 4.4))
    gs = fig.add_gridspec(int(np.ceil(ng / 3)) + 1, 3, height_ratios=[1] * int(np.ceil(ng / 3)) + [1.25])
    vals = {g: 100 * h[0] / np.maximum(h[1], 1) for g, h in heat.items()}
    vmax = max(v.max() for v in vals.values())
    cm = H.sequential()
    for k, g in enumerate(groups):
        ax = fig.add_subplot(gs[k // 3, k % 3])
        V = vals[g].reshape(4, 4)
        im = ax.imshow(V, cmap=cm, vmin=0, vmax=vmax, origin="upper", aspect="auto")
        for i in range(4):
            for j in range(4):
                n = heat[g][1].reshape(4, 4)[i, j]
                ax.text(j, i, f"{V[i, j]:.0f}" if n > 0 else "-", ha="center", va="center",
                        fontsize=H.FS_LABEL, color=H.INK, path_effects=H.halo())
        ax.set_xticks(range(4)); ax.set_xticklabels(NUT, fontsize=H.FS_LABEL)
        ax.set_yticks(range(4)); ax.set_yticklabels(INJ, fontsize=H.FS_LABEL)
        ax.grid(False)
        seeds = sorted(heat[g][2])
        ax.set_title(f"{FG.wlabel(g[0])}, {FG.alabel(g[1])}\nseeds {', '.join(map(str, seeds))}",
                     fontsize=H.FS_LABEL)
        ax.set_xlabel("nutrition at t-1")
        ax.set_ylabel("injury at t-1")
    cax = fig.add_axes([0.92, 0.55, 0.012, 0.3])
    cb = fig.colorbar(im, cax=cax)
    cb.set_label("share of chosen steps (%)", fontsize=H.FS_LABEL)
    cb.outline.set_visible(False)
    r0 = int(np.ceil(ng / 3))
    ax = fig.add_subplot(gs[r0, 0:2])
    for c in cells:
        xs, ys = ladder[c["label"]]
        ax.plot(xs, ys, color=D["colour"][c["world"]], marker=D["marker"][c["agent"]], ms=5, lw=1.4,
                alpha=0.85)
    ax.set_xlabel("rabbit smell, log-likelihood ratio predator vs rabbit (nats; sextile means)")
    ax.set_ylabel("share of chosen steps (%)")
    ax.set_title("By the rabbit's smell (one rabbit, no predator)", fontsize=H.FS_BODY)
    ax.axvline(0, color=H.RULE, lw=1)
    ax = fig.add_subplot(gs[r0, 2])
    for j, c in enumerate(cells):
        off = (j - (len(cells) - 1) / 2) * (0.7 / max(len(cells), 1))
        for k in range(4):
            ax.plot(k + off, near[c["label"]][k], ls="", marker=D["marker"][c["agent"]], ms=5,
                    color=D["colour"][c["world"]], alpha=0.9)
    ax.set_xticks(range(4)); ax.set_xticklabels([n.replace(" ", "\n") for n in NEAR], fontsize=H.FS_LABEL)
    ax.set_ylabel("share of chosen steps (%)")
    ax.set_title("By animals within 2 squares at t-1", fontsize=H.FS_BODY)
    fig.legend(handles=FG.legend_handles(D), loc="lower center", ncol=len(D["worlds"]) + len(D["agents"]),
               frameon=False, fontsize=H.FS_LABEL, bbox_to_anchor=(0.5, -0.01))
    fig.subplots_adjust(left=0.07, right=0.9, top=0.94, bottom=0.12, hspace=0.75, wspace=0.35)
    stem = f"{STEM}__{a.target}"
    FG.record_samples(a.fig_dir, stem, rows)
    FG.save(fig, a.fig_dir, stem)


if __name__ == "__main__":
    main()
