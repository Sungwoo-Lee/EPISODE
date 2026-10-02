"""FIGURE pr02 - primer: how predictivity and CKA score five toy relationships.

WHAT IS PLOTTED. Network A holds two quantities, hunger h and danger d, as its two units. Five
versions of network B hold: the same [h, d]; a mixture [h+d, h-d]; each unit rescaled on its own
[3h, 0.5d]; one extra quantity [h, d, p] that A does not have; and a bent version [h, d^2]. For each,
four bars: R^2 of predicting B from A, R^2 of predicting A from B, their minimum (the predictivity
score, which is what the page's verdicts use), and linear CKA.

WHAT IT COMPUTES. 2,000 toy moments with h, d, p drawn uniformly on [0, 1] (seed 0). R^2 is an
ordinary least-squares fit with an intercept, pooled over target units (variance-weighted), on the
same rows it was fitted on: with 2 or 3 predictors and 2,000 rows, overfitting is negligible, so the
study's held-out split and ridge penalty are left out to keep the example plain.

    python scripts/analysis/studies/modulator_clues/pr02_toy_scores.py [--out <folder>]
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np                                                         # noqa: E402
import matplotlib.pyplot as plt                                            # noqa: E402
import _an_common as C                                                     # noqa: E402
from _an_common import house                                               # noqa: E402

STEM = "pr02_toy_scores"
N = 2000


def r2(X, Y):
    Xc = np.c_[X - X.mean(axis=0), np.ones(len(X))]
    W = np.linalg.lstsq(Xc, Y, rcond=None)[0]
    R = Y - Xc @ W
    return float(1.0 - (R ** 2).sum() / ((Y - Y.mean(axis=0)) ** 2).sum())


def cka(X, Y):
    X = X - X.mean(axis=0)
    Y = Y - Y.mean(axis=0)
    return float(np.linalg.norm(Y.T @ X) ** 2 / (np.linalg.norm(X.T @ X) * np.linalg.norm(Y.T @ Y)))


def main():
    ap = argparse.ArgumentParser(description="primer figure pr02")
    ap.add_argument("--out", default=C.FIG_DIR)
    out = ap.parse_args().out
    house.apply()
    rng = np.random.default_rng(0)
    h, d, p = rng.uniform(0, 1, N), rng.uniform(0, 1, N), rng.uniform(0, 1, N)
    A = np.c_[h, d]
    cases = [("same  [h, d]", np.c_[h, d]),
             ("mixed  [h+d, h−d]", np.c_[h + d, h - d]),
             ("each unit rescaled  [3h, 0.5d]", np.c_[3 * h, 0.5 * d]),
             ("B knows more  [h, d, p]", np.c_[h, d, p]),
             ("one quantity bent  [h, d²]", np.c_[h, d ** 2])]
    bars = [("R² predicting B from A", house.RULE, None),
            ("R² predicting A from B", house.TEXT_LIGHT, None),
            ("predictivity = the smaller (decides)", house.INK, None),
            ("linear CKA (reported beside it)", house.PAPER, "///")]
    vals = np.array([[r2(A, B), r2(B, A), min(r2(A, B), r2(B, A)), cka(A, B)] for _, B in cases])
    fig, ax = plt.subplots(figsize=(10.4, 8.4))
    y = np.arange(len(cases))[::-1]
    hgt = 0.21
    for k, (lab, col, hatch) in enumerate(bars):
        yy = y + (1.5 - k) * hgt
        ax.barh(yy, vals[:, k], height=hgt * 0.92, color=col, edgecolor=house.INK_2, lw=0.8,
                hatch=hatch, label=lab)
        for yi, v in zip(yy, vals[:, k]):
            ax.text(v + 0.01, yi, f"{v:.2f}", va="center", fontsize=house.FS_LABEL, color=house.INK)
    ax.set_yticks(y)
    ax.set_yticklabels([c for c, _ in cases], fontsize=house.FS_LABEL)
    ax.set_xlim(0, 1.12)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_xlabel("score (1 = the two layers match fully)")
    ax.grid(axis="y", visible=False)
    house.legend_below(ax, ncol=2)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    C.illustration_footer(fig, y=0.025)
    C.finish(fig, STEM, out)
    C.write_illustration(STEM, out, f"random toy moments generated in {STEM}.py (seed 0)", [
        {"what": "toy moments per relationship", "used": N, "total": N,
         "note": "h, d and p drawn uniformly on [0, 1]; all rows used for fit and score"},
        {"what": "relationships scored", "used": len(cases), "total": len(cases),
         "note": "network A against five versions of network B"}])


if __name__ == "__main__":
    main()
