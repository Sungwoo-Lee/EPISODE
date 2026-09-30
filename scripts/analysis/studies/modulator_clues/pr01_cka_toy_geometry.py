"""FIGURE pr01 - primer: what CKA compares, on three moments and two units.

WHAT IS PLOTTED. Five layers that hold the same three moments (m1, m2, m3), one column each:
network A, and four versions of network B (A rotated 90 degrees; rotated and 5x larger; each unit
rescaled on its own, x3 and x0.5; and a layout that merges m1 and m2). Top row: where each moment
sits in that layer's two-unit activity space. Bottom row: the layer's "who looks like whom" table,
K = X X^T after centring, one row and one column per moment, with its entries printed. Each column
title carries the linear CKA between A and that layer, computed here from the points drawn.

WHAT IT READS. Nothing: the points are fixed toy values chosen to make the geometry visible.

    python scripts/analysis/studies/modulator_clues/pr01_cka_toy_geometry.py [--out <folder>]
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np                                                         # noqa: E402
import matplotlib.pyplot as plt                                            # noqa: E402
import _an_common as C                                                     # noqa: E402
from _an_common import house                                               # noqa: E402

STEM = "pr01_cka_toy_geometry"


def gram(X):
    Xc = X - X.mean(axis=0)
    return Xc @ Xc.T


def cka(X, Y):
    K, L = gram(X), gram(Y)
    return float((K * L).sum() / np.sqrt((K * K).sum() * (L * L).sum()))


def layouts():
    A = np.array([[2.0, 1.0], [-2.0, 1.0], [0.0, -2.0]])
    R = np.array([[0.0, -1.0], [1.0, 0.0]])                  # 90 degrees
    return [("A (reference)", A),
            ("B1: A rotated 90°", A @ R.T),
            ("B2: rotated, 5× larger", 5 * (A @ R.T)),
            ("B3: unit 1 ×3, unit 2 ×0.5", A * np.array([3.0, 0.5])),
            ("B4: m1 and m2 merged", np.array([[1.0, 1.0], [1.0, 1.0], [-2.0, -2.0]]))]


def main():
    ap = argparse.ArgumentParser(description="primer figure pr01")
    ap.add_argument("--out", default=C.FIG_DIR)
    out = ap.parse_args().out
    house.apply()
    L = layouts()
    A = L[0][1]
    fig, axs = plt.subplots(2, len(L), figsize=(10.4, 5.4), gridspec_kw={"height_ratios": [1.0, 1.0]})
    # shade = size of the entry, in neutral ink (blue and orange mean ordinary / modulated agent
    # on this page, register F11); the sign is carried by the printed number
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("mag", [house.PAPER, house.BG_SOFT, house.RULE, house.INK_2])
    names = ["m1", "m2", "m3"]
    for j, (title, X) in enumerate(L):
        ax = axs[0, j]
        lim = max(3.0, np.abs(X).max() * 1.75)
        ax.axhline(0, color=house.TICK_LINE, lw=1.0, zorder=0)
        ax.axvline(0, color=house.TICK_LINE, lw=1.0, zorder=0)
        ax.scatter(X[:, 0], X[:, 1], s=46, color=house.INK, zorder=3)
        seen = {}
        for i, (x, y) in enumerate(X):
            k = (round(x, 3), round(y, 3))
            off = seen.get(k, 0)
            seen[k] = off + 1
            ax.annotate(names[i], (x, y), xytext=(6, 5 - 13 * off), textcoords="offset points",
                        fontsize=house.FS_LABEL, color=house.INK_2)
        ax.set_xlim(-lim, lim)
        ax.set_ylim(-lim, lim)
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])
        ax.grid(False)
        c = cka(A, X)
        ax.set_title(C.wrap(title, 17) + f"\nCKA with A = {c:.2f}", fontsize=house.FS_LABEL,
                     color=house.INK, loc="left")
        ax.set_xlabel("unit 1", fontsize=house.FS_LABEL)
        if j == 0:
            ax.set_ylabel("unit 2", fontsize=house.FS_LABEL)
        K = gram(X)
        ax = axs[1, j]
        span = np.abs(K).max()
        ax.imshow(np.abs(K), cmap=cmap, vmin=0, vmax=span)
        for a in range(3):
            for b in range(3):
                v = K[a, b]
                ax.text(b, a, f"{v:g}", ha="center", va="center", fontsize=house.FS_LABEL,
                        color=house.PAPER if abs(v) > 0.7 * span else house.INK)
        ax.set_xticks(range(3))
        ax.set_xticklabels(names, fontsize=house.FS_LABEL)
        ax.set_yticks(range(3))
        ax.set_yticklabels(names if j == 0 else [""] * 3, fontsize=house.FS_LABEL)
        ax.grid(False)
        ax.set_xlabel(f"Frobenius length = {np.sqrt((K * K).sum()):.4g}", fontsize=house.FS_LABEL)
    axs[1, 0].set_ylabel("moment", fontsize=house.FS_LABEL)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    C.illustration_footer(fig, y=0.03)
    C.finish(fig, STEM, out)
    C.write_illustration(STEM, out, f"fixed toy values in {STEM}.py", [
        {"what": "moments per layer", "used": 3, "total": 3,
         "note": "chosen by hand so the geometry is visible"},
        {"what": "layers drawn", "used": 5, "total": 5,
         "note": "network A and four versions of network B"}])


if __name__ == "__main__":
    main()
