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
HYD = ["<50", "50-100", "100-150", "150+"]                             # registry.HYD_EDGES


def main(argv=None):
    a = FG.args([("--target", dict(required=True, choices=sorted(REG.TARGETS)))], argv)
    H = FG.H
    H.apply()
    import matplotlib.pyplot as plt
    D = FG.load_outputs(a.population, a.out_root, need_episodes=True)
    cells = [c for c in D["cells"] if (c["inv"]["targets"].get(a.target) or {}).get("available")]
    water = FG.has_water(cells)             # D8: hydration panels only for populations with water
    onset = a.target == "pond"              # the pond is binned at bout onset (Revision 1, finding 3)
    hheat = {}
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
        if water and "hyd_nut_trials" in x.files:
            ht = x["hyd_nut_onset_trials"] if onset else x["hyd_nut_trials"]
            hy = x["hyd_nut_onset__pond"] if onset else x[f"hyd_nut__{a.target}"]
            hh = hheat.setdefault(g, [np.zeros(16), np.zeros(16)])
            hh[0] += hy; hh[1] += ht
            rows.append({"what": f"chosen steps by hydration, {FG.run_label(c)}", "used": int(ht.sum()),
                         "total": int(e["n_steps"].sum()),
                         "note": ("bout onset: only steps where the agent was off the pond one step earlier"
                                  if onset else "every chosen step, binned by hydration one step earlier")})
        rows.append({"what": f"chosen steps, {FG.run_label(c)}", "used": int(tr.sum()),
                     "total": int(e["n_rows"].sum()),
                     "note": "every chosen step, binned by the state one step earlier; the starting row is not a chosen step"})
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
                     "total": int(keep.size), "note": ("episodes with exactly one rabbit and no predator, so only the smell can signal danger"
                              + ("; not drawn: the behaviour cannot occur without a predator" if a.target == "near_predator" else ""))})
    ng = len(groups)
    nrow_h = int(np.ceil(ng / 3))
    worlds = D["worlds"]
    nrow_w = nrow_h if water else 0         # one row of hydration maps per row of injury maps
    fact = FG.factorial(worlds)             # map size x smell reach: a smell panel for EVERY world
    nsm = int(np.ceil(len(worlds) / 3)) if fact else 1
    height = 3.6 * (nrow_h + nrow_w) + 7.6 + 4.1 * (nsm - 1)
    fig = plt.figure(figsize=(12.0, height))
    # heat maps in columns 0-2, a dedicated narrow column for the colour bar (it must not sit over a
    # panel title: register F18 amendment); then one smell panel per world; then the nearby-animals panel
    gs = fig.add_gridspec(nrow_h + nrow_w + nsm + 1, 4, width_ratios=[1, 1, 1, 0.06],
                          height_ratios=[1] * (nrow_h + nrow_w) + [1.15] * nsm + [1.15],
                          hspace=1.15 if fact else 0.95, wspace=0.55 if fact else 0.42)
    vals = {g: 100 * h[0] / np.maximum(h[1], 1) for g, h in heat.items()}
    lo = min(v[heat[g][1] > 0].min() for g, v in vals.items())
    hi = max(v[heat[g][1] > 0].max() for g, v in vals.items())
    # neutral ramp: colour means smell world elsewhere on the page, so the heat maps carry no hue;
    # anchored at the data's own range (shared by every map) so differences are visible
    cm = H.sequential(stops=[H.PAPER, "#dfe1e3", "#a9aeb5", "#6e747e", H.INK])
    for k, g in enumerate(groups):
        ax = fig.add_subplot(gs[k // 3, k % 3])
        V = vals[g].reshape(4, 4)
        im = ax.imshow(V, cmap=cm, vmin=lo, vmax=hi, origin="upper", aspect="auto")
        for i in range(4):
            for j in range(4):
                n = heat[g][1].reshape(4, 4)[i, j]
                ax.text(j, i, f"{V[i, j]:.0f}" if n > 0 else "-", ha="center", va="center",
                        fontsize=H.FS_LABEL, color=H.INK, path_effects=H.halo())
        ax.set_xticks(range(4)); ax.set_xticklabels(NUT, fontsize=H.FS_LABEL)
        ax.set_yticks(range(4)); ax.set_yticklabels(INJ, fontsize=H.FS_LABEL)
        ax.grid(False)
        seeds = sorted(heat[g][2])
        ax.set_title(f"{FG.WORLD_SHORT.get(g[0], g[0])}, {FG.AGENT_SHORT.get(g[1], g[1])}\n"
                     f"seed{'s' if len(seeds) > 1 else ''} {', '.join(map(str, seeds))}", fontsize=H.FS_LABEL)
        ax.set_xlabel("nutrition one step earlier")
        ax.set_ylabel("injury one step earlier")
    cax = fig.add_subplot(gs[0:nrow_h, 3])
    cb = fig.colorbar(im, cax=cax)
    cb.set_label("share of chosen steps (%)", fontsize=H.FS_LABEL)
    cb.outline.set_visible(False)
    if water:
        hydration_maps(fig, gs, groups, hheat, nrow_h, nrow_w, cm, onset, H)
    # one smell panel per world, the runs of both agents in it, shape = agent
    ys = [y for xs, yv in ladder.values() for y in yv]
    pad = 0.08 * (max(ys) - min(ys) + 1e-9)
    # a behaviour that cannot occur on this subset (near a predator, in predator-free episodes) gives
    # all-zero lines; say so instead of drawing them on a meaningless 1e-11 scale
    undefined = max(abs(y) for y in ys) < 1e-9
    if undefined:
        ax = fig.add_subplot(gs[nrow_h + nrow_w, 0:3])
        ax.axis("off")
        ax.text(0.5, 0.5, "By the rabbit's smell: not defined for this behaviour. These episodes contain "
                "no predator,\nso the share of steps near a predator is zero by construction.",
                ha="center", va="center", transform=ax.transAxes, fontsize=H.FS_BODY, color=H.INK_2)
    for k, w in enumerate([] if undefined else (worlds if fact else worlds[:3])):
        ax = fig.add_subplot(gs[nrow_h + nrow_w + k // 3, k % 3])
        for c in [c for c in cells if c["world"] == w]:
            xs, yv = ladder[c["label"]]
            ax.plot(xs, yv, color=D["colour"][w], marker=D["marker"][c["agent"]], ms=5.5, lw=1.3, alpha=0.9)
        ax.set_ylim(min(ys) - pad, max(ys) + pad)
        ax.set_xlim(min(min(v[0]) for v in ladder.values()) - 0.25, max(max(v[0]) for v in ladder.values()) + 0.25)
        ax.axvline(0, color=H.RULE, lw=1)
        ax.set_title(f"{FG.WORLD_SHORT.get(w, w)}: by the rabbit's smell", fontsize=H.FS_LABEL)
        ax.set_xlabel("rabbit smell (nats, sextile means)")
        if k % 3 == 0:
            ax.set_ylabel("share of chosen steps (%)")
    ax = fig.add_subplot(gs[nrow_h + nrow_w + nsm, 0:3])
    for j, c in enumerate(cells):
        off = (j - (len(cells) - 1) / 2) * (0.7 / max(len(cells), 1))
        for k in range(4):
            ax.plot(k + off, near[c["label"]][k], ls="", marker=D["marker"][c["agent"]], ms=6,
                    color=D["colour"][c["world"]], alpha=0.9)
    ax.set_xticks(range(4)); ax.set_xticklabels(NEAR, fontsize=H.FS_LABEL)
    ax.set_xlim(-0.6, 3.6)
    ax.set_ylim(bottom=0)
    ax.set_ylabel("share of chosen steps (%)")
    ax.set_title("By nearby animals (within 2 squares, one step earlier); one marker per run", fontsize=H.FS_BODY)
    if fact:                                # absolute margins on a tall canvas (no blank band)
        fig.legend(handles=FG.legend_handles(D), loc="lower center", ncol=FG.legend_ncol(D),
                   frameon=False, fontsize=H.FS_LABEL, bbox_to_anchor=(0.5, 0.1 / height))
        fig.subplots_adjust(left=0.08, right=0.94, top=1 - 0.5 / height, bottom=1.55 / height)
    else:
        fig.legend(handles=FG.legend_handles(D), loc="lower center", ncol=FG.legend_ncol(D),
                   frameon=False, fontsize=H.FS_LABEL, bbox_to_anchor=(0.5, -0.005))
        fig.subplots_adjust(left=0.08, right=0.94, top=0.95, bottom=0.08)
    stem = f"{STEM}__{a.target}"
    FG.record_samples(a.fig_dir, stem, rows)
    FG.save(fig, a.fig_dir, stem)


def hydration_maps(fig, gs, groups, hheat, r0, nrow, cm, onset, H):
    """D8: share of chosen steps by hydration band x nutrition band, both one step earlier, per world
    x agent; for the pond, the bout-onset rate (steps off the pond one step earlier only)."""
    have = [hheat[g] for g in groups if g in hheat]
    vals = {g: 100 * h[0] / np.maximum(h[1], 1) for g, h in hheat.items()}
    lo = min(v[hheat[g][1] > 0].min() for g, v in vals.items()) if have else 0
    hi = max(v[hheat[g][1] > 0].max() for g, v in vals.items()) if have else 1
    im = None
    for k, g in enumerate(groups):
        ax = fig.add_subplot(gs[r0 + k // 3, k % 3])
        ax.grid(False)
        title = f"{FG.WORLD_SHORT.get(g[0], g[0])}, {FG.AGENT_SHORT.get(g[1], g[1])}"
        if g not in hheat:
            ax.axis("off")
            ax.set_title(title + "\nno water in this world", fontsize=H.FS_LABEL)
            continue
        V = vals[g].reshape(4, 4)
        n = hheat[g][1].reshape(4, 4)
        im = ax.imshow(V, cmap=cm, vmin=lo, vmax=hi, origin="upper", aspect="auto")
        for i in range(4):
            for j in range(4):
                ax.text(j, i, f"{V[i, j]:.0f}" if n[i, j] > 0 else "-", ha="center", va="center",
                        fontsize=H.FS_LABEL, color=H.INK, path_effects=H.halo())
        ax.set_xticks(range(4)); ax.set_xticklabels(NUT, fontsize=H.FS_LABEL)
        ax.set_yticks(range(4)); ax.set_yticklabels(HYD, fontsize=H.FS_LABEL)
        ax.set_title(title + ("\narrivals on the pond" if onset else "\nby hydration"), fontsize=H.FS_LABEL)
        ax.set_xlabel("nutrition one step earlier")
        if k % 3 == 0:
            ax.set_ylabel("hydration one step earlier")
    if im is not None:
        cax = fig.add_subplot(gs[r0:r0 + nrow, 3])
        cb = fig.colorbar(im, cax=cax)
        cb.set_label("share of steps arriving on the pond (%)" if onset else "share of chosen steps (%)",
                     fontsize=H.FS_LABEL)
        cb.outline.set_visible(False)


if __name__ == "__main__":
    main()
