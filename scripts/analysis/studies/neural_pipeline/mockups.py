#!/usr/bin/env python3
"""mockups.py - the encoding-model (GLM) figure types of the Neural Recording Pipeline plan, drawn from SIMULATED
numbers (no agent data), so the reader can judge each figure type before the pipeline exists. Chosen with the user
on 2026-10-15 (unit map = "version 13": modulator hidden state on top, its FiLM outputs below). Real figures will be
drawn by the pipeline from recorded activity; these stay as the page's illustrations until then.

    $P scripts/analysis/studies/neural_pipeline/mockups.py
"""
import os
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
ROOT = "/media/nas01/projects/Interoceptive-AI/grid_world_pain"
sys.path.insert(0, os.path.join(ROOT, "scripts", "analysis", "style"))
import house as H
H.apply()
OUT = os.path.join(ROOT, "docs", "experiments", "active", "neural_analysis", "figures")
rng = np.random.default_rng(7)
LAYERS = [("encoder stage 1", 128), ("encoder hub", 128), ("recurrent (GRU)", 128), ("actor", 128), ("critic", 128), ("modulator", 16)]
REGS = ["injury", "observed\ninjury", "satiation", "rabbit\npresent", "predator\npresent", "nearest-animal\ndistance",
        "injury ×\nrabbit", "on bush", "action", "time in\nepisode"]
# how strongly each layer carries each regressor in the made-up world (mean unique R2)
PROF = np.array([
    [.02, .20, .10, .06, .06, .12, .00, .05, .01, .00],
    [.04, .12, .08, .08, .08, .10, .01, .06, .02, .01],
    [.10, .04, .06, .07, .10, .05, .05, .06, .03, .04],
    [.05, .02, .04, .05, .07, .04, .03, .04, .15, .01],
    [.06, .02, .08, .03, .09, .03, .02, .04, .01, .06],
    [.12, .06, .05, .03, .04, .02, .06, .02, .01, .02]])
SEQ = LinearSegmentedColormap.from_list("seq", [H.PAPER, "#b9d3f0", H.BLUE, "#123f78"])
DIV = LinearSegmentedColormap.from_list("div", [H.BLUE, "#c9daf0", H.PAPER, "#f6c9b3", H.ORANGE])


def unit_r2():
    rows, edges, names = [], [0], []
    for (nm, n), p in zip(LAYERS, PROF):
        m = rng.gamma(0.6, p / 0.6, size=(n, len(REGS)))
        m *= (rng.random((n, 1)) > 0.15)   # some units silent
        order = np.lexsort((-m.max(1), m.argmax(1)))
        rows.append(m[order]); edges.append(edges[-1] + n); names.append(nm)
    return np.clip(np.vstack(rows), 0, 0.6), edges, names


STAMP = dict(ha="right", va="top", fontsize=H.FS_LABEL - 1, color=H.TEXT_LIGHT, weight="semibold")


def stamp(fig, y=0.995):
    fig.text(0.99, y, "MOCK-UP · made-up numbers", **STAMP)


def tag(ax):
    ax.text(0.99, 0.99, "MOCK-UP · made-up numbers", transform=ax.transAxes, ha="right", va="top",
            fontsize=H.FS_LABEL - 1, color=H.ORANGE, weight="semibold")


def f1_encoding_map():
    M, edges, names = unit_r2()
    fig, ax = plt.subplots(figsize=(8.4, 7.2))
    im = ax.imshow(M, aspect="auto", cmap=SEQ, vmin=0, vmax=0.4, interpolation="nearest")
    ax.grid(False)
    ax.set_xticks(range(len(REGS)), REGS, fontsize=H.FS_LABEL)
    ax.xaxis.tick_top()
    mids = [(a + b) / 2 for a, b in zip(edges[:-1], edges[1:])]
    ax.set_yticks(mids, [f"{n}\n({b - a} units)" for n, a, b in zip(names, edges[:-1], edges[1:])], fontsize=H.FS_LABEL)
    for e in edges[1:-1]:
        ax.axhline(e - 0.5, color=H.INK, lw=1.2)
    cb = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    cb.set_label("unique explained variance (ΔR²)", fontsize=H.FS_LABEL); cb.outline.set_visible(False)
    stamp(fig)
    fig.subplots_adjust(left=0.17, right=0.93, top=0.86, bottom=0.03)
    return fig


def f2_share():
    fig, ax = plt.subplots(figsize=(8.4, 4.4))
    show = [0, 1, 3, 4, 6, 2]
    labs = ["injury", "observed injury", "rabbit present", "predator present", "injury × rabbit", "satiation"]
    cols = [H.RED, "#e9a3a3", H.GREEN, H.INK_2, H.ORANGE, H.BLUE]
    w = 0.13
    for k, (j, lb, c) in enumerate(zip(show, labs, cols)):
        share = np.clip(PROF[:, j] * 380 + rng.normal(0, 3, len(LAYERS)), 1, 95)
        ax.bar(np.arange(len(LAYERS)) + (k - 2.5) * w, share, w * 0.92, color=c, label=lb)
    ax.set_xticks(range(len(LAYERS)), [n for n, _ in LAYERS])
    ax.set_ylabel("units significantly tuned (%)")
    ax.set_ylim(0, 100)
    ax.legend(ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.12))
    stamp(fig)
    fig.subplots_adjust(left=0.1, right=0.98, top=0.9, bottom=0.3)
    return fig


def f3_kernels():
    t = np.arange(-5, 21)
    n = 128
    peak = rng.uniform(-2, 18, n); width = rng.uniform(1.5, 5, n); amp = rng.normal(0, 1, n) * (rng.random(n) > 0.35)
    K = amp[:, None] * np.exp(-0.5 * ((t[None] - peak[:, None]) / width[:, None]) ** 2)
    K = K[np.argsort(np.where(np.abs(amp) > 0, peak, 99))]
    fig, (a0, a1) = plt.subplots(2, 1, figsize=(8.4, 6.6), sharex=True, gridspec_kw={"height_ratios": [1, 3.2]})
    a0.plot(t, np.abs(K).mean(0), color=H.INK, lw=2)
    a0.fill_between(t, np.abs(K).mean(0) - 0.03, np.abs(K).mean(0) + 0.03, color=H.INK, alpha=0.12, lw=0)
    a0.axvline(0, color=H.INK, lw=1.2); a0.set_ylabel("mean |kernel|", fontsize=H.FS_LABEL)
    stamp(fig)
    im = a1.imshow(K, aspect="auto", cmap=DIV, norm=TwoSlopeNorm(0, -1.2, 1.2), extent=[t[0] - .5, t[-1] + .5, n, 0])
    a1.grid(False); a1.axvline(0, color=H.INK, lw=1.2)
    a1.set_xlabel("time from the rabbit entering the field of view (steps)"); a1.set_ylabel("recurrent units (sorted by peak latency)")
    fig.subplots_adjust(top=0.92)
    cb = fig.colorbar(im, ax=[a0, a1], fraction=0.03, pad=0.02); cb.set_label("kernel coefficient (a.u.)", fontsize=H.FS_LABEL)
    cb.outline.set_visible(False)
    return fig


def f4_tuning():
    inj = np.arange(0, 100, 10)
    fig, axs = plt.subplots(1, 4, figsize=(8.4, 3.4), sharex=True)
    specs = [("recurrent unit 17", .2, .006), ("recurrent unit 64", .5, -.001), ("recurrent unit 103", .1, .0),
             ("recurrent layer, mean", .3, .003)]
    for ax, (nm, b, k) in zip(axs, specs):
        base = b + 0.004 * inj
        for lab, col, mk, add in (("no animal", H.INK_2, "o", 0), ("rabbit present", H.GREEN, "s", 1)):
            y = base + add * (0.05 + k * inj) + rng.normal(0, 0.012, len(inj))
            ax.plot(inj, y, color=col, marker=mk, ms=4, lw=1.6, mfc=H.PAPER if mk == "o" else col, label=lab)
            ax.fill_between(inj, y - 0.03, y + 0.03, color=col, alpha=0.12, lw=0)
        ax.set_title(nm, fontsize=H.FS_LABEL + 1, loc="left")
        ax.set_xticks([0, 30, 60, 90]); ax.set_xlabel("injury level")
    axs[0].set_ylabel("activity (a.u.)")
    stamp(fig)
    axs[0].legend(loc="upper center", bbox_to_anchor=(2.3, -0.3), ncol=2)
    fig.subplots_adjust(left=0.08, right=0.99, top=0.78, bottom=0.33, wspace=0.35)
    return fig


def f5_models():
    models = ["time only", "+ sensory\ninputs", "+ injury", "+ animal\nidentity", "+ injury ×\nanimal"]
    fig, ax = plt.subplots(figsize=(8.4, 4.0))
    ends = []
    for li, (nm, _) in enumerate(LAYERS[:-1]):
        base = np.cumsum([0.05, 0.25 - 0.04 * li, 0.03 + 0.02 * li, 0.04, 0.005 + 0.01 * (li == 2)])
        col = [H.INK, H.INK_2, H.INK, H.TEXT_LIGHT, H.INK_2][li]
        ax.plot(range(len(models)), base, marker=["o", "s", "D", "^", "v"][li], ms=5, lw=1.8, label=nm, color=col,
                ls=["-", "--", "-.", ":", (0, (5, 1.5, 1, 1.5, 1, 1.5))][li])
        ends.append([base[-1], nm, col])
    ends.sort(key=lambda e: -e[0])   # end labels, pushed apart so none overlaps the next
    for i in range(1, len(ends)):
        ends[i][0] = min(ends[i][0], ends[i - 1][0] - 0.03)
    for yv, nm, col in ends:
        ax.text(len(models) - 1 + 0.18, yv, nm, va="center", ha="left", fontsize=H.FS_LABEL, color=col, clip_on=False)
    ax.set_xlim(-0.3, len(models) - 1 + 0.1)
    ax.set_xticks(range(len(models)), models)
    ax.set_ylabel("cross-validated R² (mean over units)")
    stamp(fig)
    fig.subplots_adjust(left=0.1, right=0.86, top=0.9, bottom=0.2)
    return fig


def f6_network():
    fig, ax = plt.subplots(figsize=(8.4, 5.2))
    ax.grid(False); ax.set_xticks([]); ax.set_yticks([])
    for li, (nm, n) in enumerate(LAYERS):
        cols = 8 if n > 16 else 4
        rows = n // cols
        x = li * 1.0 + (np.arange(n) % cols) * 0.09
        y = (np.arange(n) // cols) / max(rows, 1) * 0.9 + (0.45 - 0.45 * rows / 16 if n <= 16 else 0)
        wv = rng.normal(0, 0.25, n) + (rng.random(n) < [0.02, .04, .15, .06, .05, .3][li]) * rng.choice([-1, 1], n) * 0.9
        sc = ax.scatter(x, y, c=np.clip(wv, -1, 1), cmap=DIV, norm=TwoSlopeNorm(0, -1, 1), s=16, edgecolors="none")
        ax.text(li * 1.0 + 0.32, -0.08, nm, ha="center", va="top", fontsize=H.FS_LABEL)
    ax.set_xlim(-0.15, 5.9); ax.set_ylim(-0.2, 1.0)
    cb = fig.colorbar(sc, ax=ax, fraction=0.03, pad=0.01); cb.set_label("injury × rabbit coefficient (z)", fontsize=H.FS_LABEL)
    cb.outline.set_visible(False)
    stamp(fig)
    return fig


def f7_worlds():
    worlds = [f"w{k}" for k in range(1, 17)]
    fig, ax = plt.subplots(figsize=(8.4, 4.0))
    for ai, (ag, col, mk) in enumerate((("ordinary", H.INK, "o"), ("modulated", H.TEXT_LIGHT, "s"))):
        mu = rng.uniform(4, 14, 16) + ai * rng.uniform(0, 8, 16)
        for s in range(3):
            ax.scatter(np.arange(16) + (ai - 0.5) * 0.3 + rng.normal(0, 0.03, 16), mu + rng.normal(0, 2, 16),
                       s=14, color=col, alpha=0.45, marker=mk, lw=0)
        ax.scatter(np.arange(16) + (ai - 0.5) * 0.3, mu, s=48, color=col, marker=mk, label=f"{ag} agent (mean of 3 seeds)",
                   edgecolors=H.PAPER, lw=0.8, zorder=3)
    ax.set_xticks(range(16), worlds)
    ax.set_ylabel("recurrent units tuned to\ninjury × rabbit (%)")
    ax.set_ylim(0, 30)
    ax.legend(ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.12))
    stamp(fig)
    fig.subplots_adjust(left=0.12, right=0.98, top=0.9, bottom=0.25)
    return fig




def _layout():
    """Dot positions: each layer a block of 8 columns (modulator 4), units in reading order."""
    xs, ys, lid = [], [], []
    for li, (nm, n) in enumerate(LAYERS):
        cols = 8 if n > 16 else 4
        rows = int(np.ceil(n / cols))
        xs.append(li * 1.0 + (np.arange(n) % cols) * 0.09 + (0.18 if cols == 4 else 0))
        ys.append(1 - (np.arange(n) // cols) / 15.0 * 0.9 - (0.38 if n <= 16 else 0))
        lid.append(np.full(n, li))
    return np.concatenate(xs), np.concatenate(ys), np.concatenate(lid)


def f8_map_per_regressor():
    M, edges, names = unit_r2()
    x, y, _ = _layout()
    show = [0, 1, 2, 3, 4, 6]
    fig, axs = plt.subplots(3, 2, figsize=(8.4, 9.0))
    for ax, j in zip(axs.flat, show):
        ax.grid(False); ax.set_xticks([]); ax.set_yticks([])
        sc = ax.scatter(x, y, c=M[:, j], cmap=SEQ, vmin=0, vmax=0.3, s=5, edgecolors="none")
        ax.set_title(REGS[j].replace("\n", " "), fontsize=H.FS_BODY, loc="left", pad=4)
        for li, (nm, n) in enumerate(LAYERS):
            ax.text(li + 0.32, 0.0, nm.replace(" ", "\n") if li < 2 else nm, ha="center", va="top", fontsize=H.FS_LABEL - 2)
        ax.set_xlim(-0.1, 5.8); ax.set_ylim(-0.22, 1.05)
    stamp(fig)
    cb = fig.colorbar(sc, ax=axs, fraction=0.025, pad=0.02, location="right")
    cb.set_label("unique explained variance (ΔR²)", fontsize=H.FS_LABEL); cb.outline.set_visible(False)
    fig.subplots_adjust(left=0.02, right=0.86, top=0.95, bottom=0.02, hspace=0.25, wspace=0.05)
    return fig


def f9_map_best():
    M, edges, names = unit_r2()
    x, y, _ = _layout()
    best = M.argmax(1); size = 4 + 120 * M.max(1)
    pal = {0: H.RED, 1: "#e9a3a3", 2: H.BLUE, 3: H.GREEN, 4: H.INK_2, 5: "#8fb8a6", 6: H.ORANGE, 7: "#7b5ea7",
           8: "#b8860b", 9: "#c9cdc9"}
    fig, ax = plt.subplots(figsize=(8.4, 5.6))
    ax.grid(False); ax.set_xticks([]); ax.set_yticks([])
    weak = M.max(1) < 0.03
    ax.scatter(x[weak], y[weak], s=6, facecolors="none", edgecolors=H.RULE, lw=0.6)
    ax.scatter(x[~weak], y[~weak], c=[pal[b] for b in best[~weak]], s=size[~weak], edgecolors="none")
    for li, (nm, n) in enumerate(LAYERS):
        ax.text(li + 0.32, -0.05, nm, ha="center", va="top", fontsize=H.FS_LABEL)
    ax.set_xlim(-0.1, 5.8); ax.set_ylim(-0.18, 1.05)
    from matplotlib.lines import Line2D
    hs = [Line2D([], [], marker="o", ls="none", color=pal[j], label=REGS[j].replace("\n", " ")) for j in range(len(REGS))]
    hs.append(Line2D([], [], marker="o", ls="none", mfc="none", mec=H.RULE, label="ΔR² < 0.03 for every regressor"))
    ax.legend(handles=hs, ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.1), fontsize=H.FS_LABEL - 1)
    stamp(fig)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.93, bottom=0.27)
    return fig




PAL = {0: H.RED, 1: "#e9a3a3", 2: H.BLUE, 3: H.GREEN, 4: H.INK_2, 5: "#8fb8a6", 6: H.ORANGE, 7: "#7b5ea7",
       8: "#b8860b", 9: "#c9cdc9"}


def _mixed_M():
    M, edges, names = unit_r2()
    # make about a third of units mixed: give them a second strong record
    k = rng.random(M.shape[0]) < 0.35
    j2 = rng.integers(0, M.shape[1], M.shape[0])
    M[k, j2[k]] += M[k].max(1) * rng.uniform(0.5, 1.0, k.sum())
    return M


def _legend(fig, extra=()):
    from matplotlib.lines import Line2D
    hs = [Line2D([], [], marker="o", ls="none", color=PAL[j], label=REGS[j].replace("\n", " ")) for j in range(len(REGS))]
    hs += list(extra)
    fig.legend(handles=hs, ncol=4, loc="lower center", fontsize=H.FS_LABEL - 1, bbox_to_anchor=(0.5, 0.0))


def _frame(ax, ylo=-0.18):
    ax.grid(False); ax.set_xticks([]); ax.set_yticks([])
    for li, (nm, n) in enumerate(LAYERS):
        ax.text(li + 0.32, -0.05, nm, ha="center", va="top", fontsize=H.FS_LABEL)
    ax.set_xlim(-0.1, 5.8); ax.set_ylim(ylo, 1.05); ax.set_aspect("equal")


P_ = 0.09


def _layout2():
    xs, ys = [], []
    for li, (nm, n) in enumerate(LAYERS):
        cols = 8 if n > 16 else 4
        xs.append(li * 1.0 + (np.arange(n) % cols) * P_ + (2 * P_ if cols == 4 else 0))
        ys.append(-(np.arange(n) // cols) * P_ - (6 * P_ if n <= 16 else 0))
    return np.concatenate(xs), np.concatenate(ys), None


def _frame2(ax):
    ax.grid(False); ax.set_xticks([]); ax.set_yticks([])
    for li, (nm, n) in enumerate(LAYERS):
        ax.text(li + 3.5 * P_, -16 * P_, nm, ha="center", va="top", fontsize=H.FS_LABEL)
    ax.set_xlim(-0.08, 5.75); ax.set_ylim(-17.6 * P_, 0.6 * P_); ax.set_aspect("equal")


def f10_pies():
    """Each unit a small pie: slices = share of its explained variance per record (records under 15 % of the
    unit's total pooled grey); pie size = total explained variance."""
    from matplotlib.patches import Wedge, Circle
    M = _mixed_M(); x, y, _ = _layout2()
    fig, ax = plt.subplots(figsize=(8.4, 4.6))
    for xi, yi, m in zip(x, y, M):
        tot = m.sum()
        r = 0.016 + 0.026 * np.sqrt(min(tot, 0.6) / 0.6)
        if m.max() < 0.03:
            ax.add_patch(Circle((xi, yi), 0.01, fc="none", ec=H.RULE, lw=0.5)); continue
        sh = m / tot; big = sh >= 0.15
        parts = [(j, sh[j]) for j in np.argsort(-sh) if big[j]] + [(9, sh[~big].sum())]
        a = 90.0
        for j, s in parts:
            if s <= 0: continue
            ax.add_patch(Wedge((xi, yi), r, a - 360 * s, a, fc=PAL[j] if j != 9 or big[9] else "#e3e5e2", ec="none"))
            a -= 360 * s
    _frame2(ax)
    stamp(fig)
    from matplotlib.lines import Line2D
    _legend(fig, [Line2D([], [], marker="o", ls="none", color="#e3e5e2", label="small rest (< 15 % each)")])
    fig.subplots_adjust(left=0.01, right=0.99, top=0.95, bottom=0.27)
    return fig


def f11_dot_ring():
    """Fill = best record, ring = second record when it explains at least half as much; dots without a ring are
    selective. Size = total explained variance."""
    M = _mixed_M(); x, y, _ = _layout2()
    o = np.argsort(-M, 1); b1, b2 = o[:, 0], o[:, 1]
    v1 = M[np.arange(len(M)), b1]; v2 = M[np.arange(len(M)), b2]
    mixed = v2 >= 0.5 * v1
    weak = v1 < 0.03
    fig, ax = plt.subplots(figsize=(8.4, 4.6))
    s = 5 + 22 * np.clip(M.sum(1), 0, 0.6) / 0.6
    ax.scatter(x[weak], y[weak], s=4, facecolors="none", edgecolors=H.RULE, lw=0.5)
    sel = ~weak & ~mixed
    ax.scatter(x[sel], y[sel], s=s[sel], c=[PAL[j] for j in b1[sel]], edgecolors="none")
    mx = ~weak & mixed
    ax.scatter(x[mx], y[mx], s=34, c="none", edgecolors=[PAL[j] for j in b2[mx]], lw=1.6)
    ax.scatter(x[mx], y[mx], s=11, c=[PAL[j] for j in b1[mx]], edgecolors="none")
    _frame2(ax)
    stamp(fig)
    from matplotlib.lines import Line2D
    _legend(fig, [Line2D([], [], marker="o", ls="none", mfc="none", mec=H.INK_2, mew=2, ms=9, label="ring: second record (mixed unit)"),
                  Line2D([], [], marker="o", ls="none", mfc="none", mec=H.RULE, label="ΔR² < 0.03 for every regressor")])
    fig.subplots_adjust(left=0.01, right=0.99, top=0.95, bottom=0.27)
    return fig


def f12_cotuning():
    """Per layer: how many units are tuned to both of two records (diagonal = tuned to that record at all)."""
    M = _mixed_M()
    T = M >= 0.05
    _, edges, _ = unit_r2()
    show = [0, 1, 2, 3, 4, 6]
    lab = [REGS[j].replace("\n", " ") for j in show]
    fig, axs = plt.subplots(1, 3, figsize=(8.4, 3.6))
    for ax, li in zip(axs, (1, 2, 5)):
        a, b = edges[li], edges[li + 1]
        t = T[a:b][:, show].astype(float)
        C = (t.T @ t) / (b - a) * 100
        im = ax.imshow(C, cmap=SEQ, vmin=0, vmax=60)
        ax.grid(False)
        ax.set_xticks(range(len(show)), lab, rotation=55, ha="right", fontsize=H.FS_LABEL - 1)
        ax.set_yticks(range(len(show)), lab if li == 1 else [], fontsize=H.FS_LABEL - 1)
        ax.set_title(LAYERS[li][0], fontsize=H.FS_BODY, loc="left")
        for i in range(len(show)):
            for j in range(len(show)):
                ax.text(j, i, f"{C[i, j]:.0f}", ha="center", va="center", fontsize=H.FS_LABEL - 3,
                        color=H.PAPER if C[i, j] > 35 else H.INK_2)
    cax = fig.add_axes([0.92, 0.36, 0.015, 0.52])
    cb = fig.colorbar(im, cax=cax); cb.set_label("% of the layer's units", fontsize=H.FS_LABEL)
    cb.outline.set_visible(False)
    stamp(fig)
    fig.subplots_adjust(left=0.16, right=0.89, top=0.86, bottom=0.36, wspace=0.08)
    return fig




# ---- modulator split into its memory (top) and its outputs (below), user 2026-10-15 ------------------------------
SITES = ["encoder stage 1", "encoder hub", "recurrent (GRU)", "actor + critic"]
NOUT = 16   # outputs drawn per site in the mock-up (real: 128 gains + 128 offsets per site)


def _M_split(mixed=False):
    M = _mixed_M() if mixed else unit_r2()[0]
    out = np.clip(rng.gamma(0.6, PROF[5] / 0.6, size=(len(SITES) * NOUT, len(REGS))) * (rng.random((len(SITES) * NOUT, 1)) > 0.2), 0, 0.6)
    if mixed:
        k = rng.random(len(out)) < 0.35
        j2 = rng.integers(0, len(REGS), len(out))
        out[k, j2[k]] += out[k].max(1) * rng.uniform(0.5, 1.0, k.sum())
    return np.vstack([M, out])


def _layout3():
    """Like _layout2, but the modulator column holds its 16 memory units on top and, below, its outputs:
    one 8 x 2 block per site it modulates."""
    x, y, _ = _layout2()
    n_main = sum(n for _, n in LAYERS)
    xm = 5.0 + (np.arange(16) % 8) * P_
    ym = -(np.arange(16) // 8) * P_
    x[n_main - 16:], y[n_main - 16:] = xm, ym
    xo, yo = [], []
    for si in range(len(SITES)):
        k = np.arange(NOUT)
        xo.append(5.0 + (k % 8) * P_)
        yo.append(-(4.6 + si * 3.0 + k // 8) * P_)
    return np.concatenate([x, *xo]), np.concatenate([y, *yo])


def _frame3(ax):
    _frame2(ax)
    ax.set_xlim(-0.08, 6.55)
    ax.text(5.0 + 3.5 * P_, 0.9 * P_, "hidden state", ha="center", va="bottom", fontsize=H.FS_LABEL - 2, color=H.INK_2)
    ax.plot([4.97, 5.0 + 7.4 * P_], [-2.1 * P_] * 2, color=H.RULE, lw=0.8)
    ax.text(5.0 + 3.5 * P_, -2.35 * P_, "FiLM outputs (γ, β) to", ha="center", va="top", fontsize=H.FS_LABEL - 3, color=H.INK_2)
    for si, nm in enumerate(SITES):
        ax.text(5.0 + 7.9 * P_, -(4.6 + si * 3.0 + 0.5) * P_, nm, ha="left", va="center", fontsize=H.FS_LABEL - 3, color=H.INK_2)
    for t in ax.texts:
        if t.get_text() == "modulator":
            t.set_x(5.0 + 3.5 * P_)
    ax.set_ylim(-17.6 * P_, 2.2 * P_)


def _dots_best(ax, M, x, y):
    best = M.argmax(1); weak = M.max(1) < 0.03
    s = 5 + 30 * np.clip(M.max(1), 0, 0.4) / 0.4
    ax.scatter(x[weak], y[weak], s=4, facecolors="none", edgecolors=H.RULE, lw=0.5)
    ax.scatter(x[~weak], y[~weak], c=[PAL[b] for b in best[~weak]], s=s[~weak], edgecolors="none")


def f13_best_split():
    M = _M_split(); x, y = _layout3()
    fig, ax = plt.subplots(figsize=(8.4, 3.9))
    _dots_best(ax, M, x, y)
    _frame3(ax)
    from matplotlib.lines import Line2D
    stamp(fig)
    _legend(fig, [Line2D([], [], marker="o", ls="none", mfc="none", mec=H.RULE, label="ΔR² < 0.03 for every regressor")])
    fig.subplots_adjust(left=0.01, right=0.99, top=0.97, bottom=0.25)
    return fig


def f14_ring_split():
    M = _M_split(mixed=True); x, y = _layout3()
    o = np.argsort(-M, 1); b1, b2 = o[:, 0], o[:, 1]
    v1 = M[np.arange(len(M)), b1]; v2 = M[np.arange(len(M)), b2]
    mixed = v2 >= 0.5 * v1; weak = v1 < 0.03
    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    s = 5 + 22 * np.clip(M.sum(1), 0, 0.6) / 0.6
    ax.scatter(x[weak], y[weak], s=4, facecolors="none", edgecolors=H.RULE, lw=0.5)
    sel = ~weak & ~mixed
    ax.scatter(x[sel], y[sel], s=s[sel], c=[PAL[j] for j in b1[sel]], edgecolors="none")
    mx = ~weak & mixed
    ax.scatter(x[mx], y[mx], s=34, c="none", edgecolors=[PAL[j] for j in b2[mx]], lw=1.6)
    ax.scatter(x[mx], y[mx], s=11, c=[PAL[j] for j in b1[mx]], edgecolors="none")
    _frame3(ax)
    from matplotlib.lines import Line2D
    stamp(fig)
    _legend(fig, [Line2D([], [], marker="o", ls="none", mfc="none", mec=H.INK_2, mew=1.6, ms=7, label="ring: second record (mixed unit)"),
                  Line2D([], [], marker="o", ls="none", mfc="none", mec=H.RULE, label="ΔR² < 0.03 for every regressor")])
    fig.subplots_adjust(left=0.01, right=0.99, top=0.95, bottom=0.27)
    return fig


def f15_pies_split():
    from matplotlib.patches import Wedge, Circle
    M = _M_split(mixed=True); x, y = _layout3()
    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    for xi, yi, m in zip(x, y, M):
        tot = m.sum()
        r = 0.016 + 0.026 * np.sqrt(min(tot, 0.6) / 0.6)
        if m.max() < 0.03:
            ax.add_patch(Circle((xi, yi), 0.01, fc="none", ec=H.RULE, lw=0.5)); continue
        sh = m / tot; big = sh >= 0.15
        parts = [(j, sh[j]) for j in np.argsort(-sh) if big[j]] + [(None, sh[~big].sum())]
        a = 90.0
        for j, sv in parts:
            if sv <= 0: continue
            ax.add_patch(Wedge((xi, yi), r, a - 360 * sv, a, fc=PAL[j] if j is not None else "#e3e5e2", ec="none"))
            a -= 360 * sv
    _frame3(ax)
    from matplotlib.lines import Line2D
    stamp(fig)
    _legend(fig, [Line2D([], [], marker="o", ls="none", color="#e3e5e2", label="small rest (< 15 % each)")])
    fig.subplots_adjust(left=0.01, right=0.99, top=0.95, bottom=0.27)
    return fig




def f16_weight_split():
    """Network map of the injury x rabbit weight, same layout as the encoding map (version 13)."""
    n = sum(n for _, n in LAYERS) + len(SITES) * NOUT
    x, y = _layout3()
    lay = np.concatenate([np.full(nn, li) for li, (_, nn) in enumerate(LAYERS)] + [np.full(len(SITES) * NOUT, 5)])
    strong = np.array([0.02, .04, .15, .06, .05, .3])[lay]
    wv = rng.normal(0, 0.25, n) + (rng.random(n) < strong) * rng.choice([-1, 1], n) * 0.9
    fig, ax = plt.subplots(figsize=(8.4, 4.1))
    sc = ax.scatter(x, y, c=np.clip(wv, -1, 1), cmap=DIV, norm=TwoSlopeNorm(0, -1, 1), s=16, edgecolors="none")
    _frame3(ax)
    cax = fig.add_axes([0.2, 0.15, 0.6, 0.03])
    cb = fig.colorbar(sc, cax=cax, orientation="horizontal"); cb.set_label("injury × rabbit coefficient (z)", fontsize=H.FS_LABEL)
    cb.outline.set_visible(False)
    stamp(fig)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.95, bottom=0.27)
    return fig


def f17_appendix_split():
    """Appendix: one map per task record (unique explained variance), same layout as version 13."""
    M = _M_split(); x, y = _layout3()
    fig, axs = plt.subplots(5, 2, figsize=(8.4, 8.6))
    for j, ax in enumerate(axs.flat):
        sc = ax.scatter(x, y, c=M[:, j], cmap=SEQ, vmin=0, vmax=0.3, s=6, edgecolors=H.RULE, linewidths=0.3)
        _frame3(ax)
        short = {"encoder stage 1": "enc 1", "encoder hub": "hub", "recurrent (GRU)": "GRU", "modulator": "mod."}
        for t in list(ax.texts):   # small panels: short layer names only (Figure 1 labels the modulator parts)
            if t.get_position()[0] > 4.9 and t.get_text() != "modulator":
                t.remove()
            else:
                t.set_text(short.get(t.get_text(), t.get_text())); t.set_fontsize(H.FS_LABEL - 1)
        ax.set_title(REGS[j].replace("\n", " "), fontsize=H.FS_BODY, loc="left", pad=2)
    cax = fig.add_axes([0.2, 0.04, 0.6, 0.012])
    cb = fig.colorbar(sc, cax=cax, orientation="horizontal"); cb.set_label("unique explained variance (ΔR²)", fontsize=H.FS_LABEL)
    cb.outline.set_visible(False)
    stamp(fig, 0.998)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.96, bottom=0.11, hspace=0.3, wspace=0.04)
    return fig




def f18_design_matrix():
    """The design matrix of one simulated episode, time running left to right as in the event strip above it
    (transposed from the SPM convention so both panels share one time axis). Continuous and state regressors are
    lanes; each event is a block of FIR lagged copies, one row per lag. Redesigned by visual-design-reviewer
    (2026-10-15; mock-up tmp/20261015_design_matrix_redesign/)."""
    from matplotlib.colors import to_rgb
    from matplotlib.patches import Rectangle, FancyBboxPatch
    rng = np.random.default_rng(7)
    # --- the page's regressor palette (PAL in mockups.py), by meaning ------------------------------------------------
    PURPLE = "#7b5ea7"                       # PAL[7] on bush
    C = {"injury": H.RED, "observed injury": "#e9a3a3", "satiation": H.BLUE, "nearest-animal distance": "#8fb8a6",
         "rabbit present": H.GREEN, "predator present": H.INK_2, "on bush": PURPLE, "injury × rabbit": H.ORANGE,
         # events inherit the hue of the state they belong to (extension of PAL, same meanings)
         "rabbit enters view": H.GREEN, "predator enters view": H.INK_2, "bush entry": PURPLE, "bush exit": PURPLE,
         "injury onset": H.RED, "eating": H.BLUE}
    ZERO = np.array(to_rgb(H.BG_SOFT))       # a 0 cell: the matrix ground, visibly distinct from the page
    FS_S, FS_M = 9, H.FS_LABEL               # 9 pt = 11.4 px in a 730 px column (floor 9 px); 11 pt = 13.9 px


    def mix(a, b, w):
        return (1 - w) * np.array(to_rgb(a)) + w * np.array(to_rgb(b))


    def ramp_rgb(v, hue):
        """0 -> matrix ground, 0.6 -> the PAL hue, 1 -> the hue darkened 35 % toward ink (one hue family per lane)."""
        v = np.clip(v, 0, 1)[..., None]
        lo, mid, hi = ZERO, np.array(to_rgb(hue)), mix(hue, H.INK, 0.35)
        a = np.where(v < 0.6, lo + (mid - lo) * (v / 0.6), mid + (hi - mid) * ((v - 0.6) / 0.4))
        return a


    def tracked(s):
        """Uppercase eyebrow with tracking (matplotlib has no letter-spacing: insert hair spaces)."""
        return " ".join(s.upper())


    # --- the same made-up episode as f18 ------------------------------------------------------------------------------
    T = 100
    t = np.arange(T)
    EV = {"rabbit enters view": [18], "predator enters view": [], "bush entry": [34], "bush exit": [61],
          "injury onset": [70], "eating": [82, 83, 84]}
    LAGS = {"rabbit enters view": range(-5, 21), "predator enters view": range(-5, 21), "bush entry": range(-10, 11),
            "bush exit": range(-5, 11), "injury onset": range(0, 21), "eating": range(0, 6)}
    injury = np.where(t < 70, 0.3, 0.75) + rng.normal(0, 0.01, T)
    observed = np.convolve(np.r_[np.full(3, injury[0]), injury], np.ones(4) / 4, "valid")[:T]
    satiation = np.clip(0.6 - 0.004 * t + 0.25 * (t >= 84), 0, 1)
    dist = np.clip(np.abs(np.sin(t / 14)) * 6 + 1, 1, 7) / 7
    rabbit = ((t >= 18) & (t < 66)).astype(float)
    bush = ((t >= 34) & (t < 61)).astype(float)
    SINGLE = [("Continuous", [("injury", injury), ("observed injury", observed), ("satiation", satiation),
                              ("nearest-animal distance", (dist - dist.min()) / np.ptp(dist))]),
              ("States · boxcar", [("rabbit present", rabbit), ("predator present", np.zeros(T)), ("on bush", bush)]),
              ("Interaction", [("injury × rabbit", injury * rabbit)])]


    def fir(e):
        X = np.zeros((len(LAGS[e]), T))
        for i, L in enumerate(LAGS[e]):
            for te in EV[e]:
                if 0 <= te + L < T:
                    X[i, te + L] = 1
        return X


    # --- geometry, in inches (the axes is 1 data unit = 1 inch vertically, so heights are honest) -------------------
    LANE, LGAP, ROW, HEAD, GGAP, EGAP = 0.165, 0.045, 0.034, 0.24, 0.16, 0.10
    STRIP = 1.05
    W_IN = 8.0
    L_IN, R_IN = 2.05, 0.62                  # label column, lag-tick column
    y = STRIP + 0.12                         # cursor, downward
    items = []                               # (kind, payload, y0, h)
    for gname, regs in SINGLE:
        items.append(("head", gname, y, HEAD)); y += HEAD
        for nm, v in regs:
            items.append(("lane", (nm, v), y, LANE)); y += LANE + LGAP
        y += GGAP - LGAP
    items.append(("head", "Events · FIR, one row per lag", y, HEAD)); y += HEAD
    for e in EV:
        n = len(LAGS[e])
        h = n * ROW if EV[e] else 0.12      # an event that never occurs collapses to a stub (labelled)
        items.append(("event", e, y, h)); y += h + EGAP
    Y_END = y - EGAP
    H_IN = Y_END + 0.55
    fig = plt.figure(figsize=(W_IN, H_IN))
    ax = fig.add_axes([L_IN / W_IN, 0.42 / H_IN, (W_IN - L_IN - R_IN) / W_IN, (H_IN - 0.42 - 0.12) / H_IN])
    ax.set_xlim(-0.5, T - 0.5); ax.set_ylim(Y_END + 0.04, -0.12)
    ax.grid(False); ax.set_yticks([])
    ax.set_xticks([0, 20, 40, 60, 80, 99]); ax.tick_params(axis="x", pad=3)
    ax.set_xlabel("time in episode (steps)", labelpad=6)
    XL = -0.5 - 1.2                           # label anchor (data x), just left of the matrix
    tr_lbl = dict(ha="right", va="center", clip_on=False)

    # --- 1. the episode strip: what happened, on the same time axis -------------------------------------------------
    yb = STRIP - 0.30                         # baseline of the strip (event dots sit on it)
    yr0, yr1 = yb + 0.06, yb + 0.30           # phase ribbon under the baseline
    ax.add_patch(Rectangle((23.5, yr0), 10, yr1 - yr0, color=mix(PURPLE, H.PAPER, 0.90), lw=0))
    ax.add_patch(Rectangle((33.5, yr0), 27, yr1 - yr0, color=mix(PURPLE, H.PAPER, 0.75), lw=0))
    ax.text(23.0, (yr0 + yr1) / 2, "approach \u2192", ha="right", va="center", fontsize=FS_S, color=H.INK_2)
    ax.text(47, (yr0 + yr1) / 2, "in the bush: hiding, resting", ha="center", va="center", fontsize=FS_S - 1,
            color=H.INK)
    ax.plot([-0.5, T - 0.5], [yb, yb], color=H.RULE, lw=0.9, solid_capstyle="butt")
    TIER = {1: yb - 0.50, 2: yb - 0.26}       # two label tiers so neighbouring events never collide
    marks = [("rabbit enters view", 18, 1), ("bush entry", 34, 2), ("bush exit", 61, 1), ("injury onset", 70, 2),
             ("eating", 83, 1)]
    for nm, te, tier in marks:
        ytop = TIER[tier]
        ax.plot([te, te], [ytop + 0.03, yb], color=C[nm], lw=1.4, solid_capstyle="butt")
        ax.text(te, ytop, nm, ha="center", va="bottom", fontsize=FS_S, color=H.INK, weight="semibold")
    for e, times in EV.items():
        for te in times:
            ax.plot(te, yb, "o", ms=4.6, mec=H.PAPER, mew=0.9, color=C[e], zorder=3)
    ax.text(XL, yb - 0.10, "Episode", ha="right", va="center", clip_on=False, fontsize=FS_M, color=H.INK,
            weight="semibold")
    ax.text(XL, yb + 0.12, "one run, 100 steps", ha="right", va="center", clip_on=False, fontsize=FS_S,
            color=H.TEXT_LIGHT)
    ax.add_patch(Rectangle((33.5, yr1), 27, 10, color=mix(PURPLE, H.PAPER, 0.93), lw=0, zorder=0.2))   # in-bush, visible in the gaps

    # --- 2. event guide lines through the whole matrix (drawn first, lanes cover them) ---------------------------------
    for e in ("rabbit enters view", "bush entry", "bush exit", "injury onset"):
        for te in EV[e]:
            ax.plot([te, te], [yr1, Y_END], color=C[e], lw=0.7, alpha=0.55, ls=(0, (2, 2)), zorder=0.5)

    # --- 3. lanes and event blocks -----------------------------------------------------------------------------------
    for kind, p, y0, h in items:
        if kind == "head":
            ax.text(XL + 0.0, y0 + h * 0.62, tracked(p) if "·" not in p else
                    "  ·  ".join(tracked(s.strip()) if i == 0 else s.strip() for i, s in enumerate(p.split("·"))),
                    ha="right", va="center", clip_on=False, fontsize=FS_S, color=H.TEXT_LIGHT, weight="semibold")
            ax.plot([-0.5, T - 0.5], [y0 + h * 0.62] * 2, color=H.TICK_LINE, lw=0.7, zorder=0.4)
        elif kind == "lane":
            nm, v = p
            ax.imshow(ramp_rgb(v[None, :], C[nm]), extent=(-0.5, T - 0.5, y0 + h, y0), aspect="auto",
                      interpolation="nearest", zorder=1)
            ax.add_patch(Rectangle((-3.6, y0 + 0.02), 1.6, h - 0.04, color=C[nm], lw=0, clip_on=False))   # key chip
            ax.text(XL - 2.6, y0 + h / 2, nm, **tr_lbl, fontsize=FS_M, color=H.INK)
            if nm == "predator present":
                ax.text(50, y0 + h / 2, "no predator in this episode (all zeros)", ha="center", va="center",
                        fontsize=FS_S, color=H.TEXT_LIGHT, zorder=2)
        else:
            e, lags = p, list(LAGS[p])
            ax.add_patch(Rectangle((-3.6, y0 + 0.02), 1.6, h - 0.04, color=C[e], lw=0, clip_on=False))
            if not EV[e]:
                ax.add_patch(Rectangle((-0.5, y0), T, h, color=ZERO, lw=0, zorder=1))
                ax.text(XL - 2.6, y0 + h / 2, e, **tr_lbl, fontsize=FS_M, color=H.INK)
                ax.text(50, y0 + h / 2, f"{len(lags)} lag rows, all zeros here — shown collapsed", ha="center",
                        va="center", fontsize=FS_S, color=H.TEXT_LIGHT, zorder=2)
                continue
            X = fir(e)
            ax.imshow(ramp_rgb(X * 0.85, C[e]), extent=(-0.5, T - 0.5, y0 + h, y0), aspect="auto",
                      interpolation="nearest", zorder=1)
            rng_s = f"lags {lags[0]:+d} to {lags[-1]:+d}".replace("+0 ", "0 ").replace("-", "\u2212")
            if h >= 0.32:
                ax.text(XL - 2.6, y0 + h / 2 - 0.08, e, **tr_lbl, fontsize=FS_M, color=H.INK)
                ax.text(XL - 2.6, y0 + h / 2 + 0.10, rng_s, **tr_lbl, fontsize=FS_S, color=H.TEXT_LIGHT)
            else:
                r_t = ax.text(XL - 2.6, y0 + h / 2, rng_s, **tr_lbl, fontsize=FS_S, color=H.TEXT_LIGHT)
                fig.canvas.draw()
                bb = r_t.get_window_extent().transformed(ax.transData.inverted())
                ax.text(bb.x0 - 1.2, y0 + h / 2, e, **tr_lbl, fontsize=FS_M, color=H.INK)
            yy = y0 + (lags.index(0) + 0.5) * ROW   # lag-0 row: where the band crosses it is the event step
            ax.plot(T - 0.5 + 0.9, yy, marker="<", ms=4.5, color=H.INK, mew=0, clip_on=False)
            ax.text(T - 0.5 + 1.9, yy, "0", ha="left", va="center", fontsize=FS_S, clip_on=False, color=H.INK,
                    weight="semibold")
            if e == "bush entry":   # name the two halves of the band
                ax.text(26.5, y0 + 9.5 * ROW, "before entry: approach", ha="right", va="center", fontsize=FS_S,
                        color=H.INK_2, path_effects=H.halo(H.BG_SOFT))
                ax.text(45.0, y0 + 17.5 * ROW, "after entry: in the bush", ha="left", va="center", fontsize=FS_S,
                        color=H.INK_2, path_effects=H.halo(H.BG_SOFT))
    ax.text(T - 0.5 + 1.5, items[[k for k, *_ in items].index("event") - 1][2] + HEAD * 0.62, "lag", ha="left",
            va="center", fontsize=FS_S, color=H.TEXT_LIGHT, weight="semibold", clip_on=False)

    stamp(fig, 0.997)
    return fig


FIGS = [("np_design_matrix", f18_design_matrix), ("np_unitmap", f13_best_split), ("np_tuned_share", f2_share), ("np_kernels", f3_kernels),
        ("np_tuning", f4_tuning), ("np_models", f5_models), ("np_interaction_map", f16_weight_split),
        ("np_worlds", f7_worlds), ("np_unitmap_per_regressor", f17_appendix_split)]


def main():
    import json
    for stem, f in FIGS:
        fig = f()
        H.save(fig, f"{OUT}/{stem}", formats=("svg", "png"), check_text=False)   # text outside axes on purpose: dot-map labels
        plt.close(fig)
        rows = [{"what": "simulated units and episodes", "used": 0, "total": 0, "pct": 0.0,
                 "note": "illustration only: made-up numbers from a random generator; no agent data is used"}]
        json.dump(rows, open(f"{OUT}/{stem}.samples.json", "w"), indent=1)
        print("saved", stem)


if __name__ == "__main__":
    main()
