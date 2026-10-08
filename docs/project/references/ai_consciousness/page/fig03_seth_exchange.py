#!/usr/bin/env python3
"""FIGURE 3 - the fifty replies to Seth: what they argued, and how Seth answered.

LEFT: the ten themes the replies fall into (field_data/clusters.csv), one bar each, split by the
reply's verdict on Seth's thesis - blue supports, greys extend or qualify, orange rejects.
RIGHT: the same fifty replies counted by verdict (rows) against how Seth's response treated them
(columns): conceded, partly conceded, held his ground against, or agreed with.
"""
import numpy as np
import matplotlib.pyplot as plt
import _aifig as _ai
from _aifig import house

STEM = "fig03_seth_exchange"
TREAT = [("concede", "concedes"), ("partly", "concedes\nin part"), ("holds", "holds firm\nagainst"),
         ("holds-in-agreement", "agrees\nwith it")]


def main():
    house.apply()
    C = _ai.read("commentaries.csv")
    CL = _ai.read("clusters.csv")
    vkeys = [v for v, _, _ in _ai.VERDICTS]
    if {r["verdict"] for r in C} - set(vkeys) or {r["response_treatment"] for r in C} - {t for t, _ in TREAT}:
        raise SystemExit(f"{STEM}: unexpected verdict or treatment codes")
    # stacked, not side by side: side by side the canvas was so wide that every label fell under the
    # 9 px floor at desktop column width (format gate 2026-10-07)
    fig, (a, b) = plt.subplots(2, 1, figsize=(10.0, 10.4), gridspec_kw={"height_ratios": [1.55, 1]})
    ys = list(range(len(CL)))[::-1]
    for y, cl in zip(ys, CL):
        left = 0
        members = [r for r in C if r["theme_cluster"] == cl["cluster_id"]]
        for v, lab, col in _ai.VERDICTS:
            n = sum(1 for r in members if r["verdict"] == v)
            if n:
                a.barh(y, n, left=left, height=0.62, color=col, label=lab if y == ys[0] or True else None)
            left += n
        a.text(left + 0.15, y, str(len(members)), va="center", fontsize=house.FS_LABEL, color=house.INK)
    a.set_yticks(ys)
    a.set_yticklabels([cl["label"] for cl in CL], fontsize=house.FS_LABEL)
    a.set_xlabel("number of replies")
    a.grid(axis="y", visible=False)
    a.set_title("What the replies argued, by theme", loc="left", fontsize=house.FS_BODY,
                fontweight="semibold", color=house.INK, pad=8)
    M = np.zeros((len(vkeys), len(TREAT)), int)
    for r in C:
        M[vkeys.index(r["verdict"]), [t for t, _ in TREAT].index(r["response_treatment"])] += 1
    b.imshow(M, cmap=house.sequential(stops=[house.PAPER, "#dfe2de", "#a9afa9", "#4e545e"]), aspect="auto")
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            dark = M[i, j] > 0.8 * M.max()          # only the darkest cells take light text
            b.text(j, i, str(M[i, j]) if M[i, j] else "·", ha="center", va="center",
                   fontsize=house.FS_BODY, color=house.PAPER if dark else house.INK)
    b.set_xticks(range(len(TREAT)))
    b.set_xticklabels([l for _, l in TREAT], fontsize=house.FS_LABEL)
    b.set_yticks(range(len(vkeys)))
    b.set_yticklabels([l for _, l, _ in _ai.VERDICTS], fontsize=house.FS_LABEL)
    b.set_xlabel("how Seth's response treated the reply")
    b.grid(False)
    b.set_title("How Seth answered", loc="left", fontsize=house.FS_BODY, fontweight="semibold",
                color=house.INK, pad=8)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for _, _, c in _ai.VERDICTS]
    a.legend(handles, [l for _, l, _ in _ai.VERDICTS], loc="upper center", ncol=4, frameon=False,
             fontsize=house.FS_LABEL, bbox_to_anchor=(0.32, -0.13))
    fig.subplots_adjust(left=0.42, right=0.97, top=0.95, bottom=0.12, hspace=0.62)
    house.save(fig, f"{_ai.FIGS}/{STEM}")
    _ai.note(STEM, (f"All {len(C)} replies are counted once in each panel (field_data/commentaries.csv). The "
                    "verdict is the reviewer's reading of each reply; the treatment is the reviewer's reading of "
                    "Seth's response. The themes are the curator's grouping."))


if __name__ == "__main__":
    main()
