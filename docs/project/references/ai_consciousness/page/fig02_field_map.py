#!/usr/bin/env python3
"""FIGURE 2 - the field on two questions at once: does the right computation suffice, and could AI be conscious?

A grid. Columns: each work's stance on computational functionalism (the view that running the right
computation is enough for consciousness). Rows: its stance on whether AI could be conscious. Each cell
shows how many works in the collection take that pair of stances, and names the core papers in it.
Cell shading follows the count, in greys. The two codes come from field_data/works.csv; for many of the
50 commentaries they are the curator's reading, not the reviewer's, and the page says so. NOT A VOTE:
the collection was built around one debate, so the counts describe this collection only.
"""
import textwrap
import numpy as np
import matplotlib.pyplot as plt
import _aifig as _ai
from _aifig import house

STEM = "fig02_field_map"
COLS = [("supports", "supports it"), ("restricts", "narrows it"), ("rejects", "rejects it"),
        ("neutral", "takes no side")]
ROWS = [("likely", "likely, or already\npartly conscious"), ("possible", "possible"),
        ("unlikely-now", "unlikely for\ncurrent systems"), ("very-unlikely", "very unlikely\nfor computers"),
        ("question-reframed", "the question\nshould be reframed"), ("no-verdict", "gives no verdict")]


def main():
    house.apply()
    W = _ai.read("works.csv")
    bad = {r["stance_cf"] for r in W} - {c for c, _ in COLS} | {r["stance_ai"] for r in W} - {r for r, _ in ROWS}
    if bad:
        raise SystemExit(f"{STEM}: unexpected stance codes {bad}")
    M = np.zeros((len(ROWS), len(COLS)), int)
    names = {}
    for r in W:
        i = [k for k, _ in ROWS].index(r["stance_ai"])
        j = [k for k, _ in COLS].index(r["stance_cf"])
        M[i, j] += 1
        if r["batch"] in ("A", "B"):
            names.setdefault((i, j), []).append(r["short_label"])
    fig, ax = plt.subplots(figsize=(11.6, 7.6))
    ax.imshow(np.sqrt(M), cmap=house.sequential(stops=[house.PAPER, "#e3e6e2", "#c4c9c3", "#8e959b"]),
              vmin=0, vmax=np.sqrt(M.max()), aspect="auto")
    for i in range(len(ROWS)):
        for j in range(len(COLS)):
            v = M[i, j]
            ax.text(j, i - 0.18, str(v) if v else "·", ha="center", va="center", fontsize=house.FS_TITLE,
                    fontweight="semibold" if v else "normal", color=house.INK if v else house.TEXT_LIGHT)
            if (i, j) in names:
                ax.text(j, i + 0.2, "\n".join(textwrap.wrap(", ".join(names[(i, j)]), 30)), ha="center",
                        va="center", fontsize=house.FS_LABEL - 0.5, color=house.INK_2, linespacing=1.1)
    ax.set_xticks(range(len(COLS)))
    ax.set_xticklabels([l for _, l in COLS], fontsize=house.FS_LABEL)
    ax.set_yticks(range(len(ROWS)))
    ax.set_yticklabels([l for _, l in ROWS], fontsize=house.FS_LABEL)
    ax.xaxis.tick_top()
    ax.xaxis.set_label_position("top")
    ax.set_xlabel("stance on computational functionalism (the right computation is enough)")
    ax.set_ylabel("stance on whether AI could be conscious")
    ax.grid(False)
    ax.set_xticks(np.arange(-.5, len(COLS)), minor=True)
    ax.set_yticks(np.arange(-.5, len(ROWS)), minor=True)
    ax.grid(which="minor", color=house.PAPER, linewidth=3)
    ax.tick_params(which="minor", length=0)
    fig.subplots_adjust(left=0.2, right=0.99, top=0.86, bottom=0.02)
    house.save(fig, f"{_ai.FIGS}/{STEM}")
    own = sum(1 for r in W if r["stance_basis"].startswith("review"))
    _ai.note(STEM, (f"All {len(W)} works in the collection are counted, one per cell (field_data/works.csv). "
                    f"For {own} of them both codes come from the reviewer's own record; the rest are the "
                    "curator's reading of the review, a reading aid rather than a measurement. Names in a cell "
                    "are the core papers; the 50 commentaries are counted but not named. Not a vote: the "
                    "collection was built around one debate."))


if __name__ == "__main__":
    main()
