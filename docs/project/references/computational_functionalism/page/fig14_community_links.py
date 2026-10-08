#!/usr/bin/env python3
"""FIGURE 14 - who engages whom: documented engagements between the research communities.

QUESTION IT ANSWERS. Do the communities arguing about machine minds actually read each other, or do
they argue past each other from separate literatures?

WHAT IS IN IT. A grid. Rows are the community of the engaging work, columns the community of the
work engaged (edges.csv joined to works.csv). A cell counts documented engagements - building on,
critiquing, replying to, reinterpreting, using as evidence, naming as an opponent, excluding, or
flagging as open - as the reviewers recorded them. Darker cells hold more; grey, not a hue, because
hue on this page means community in the other figures and stance in figure 12.

WHAT IT IS NOT. A citation census. 26 of the 110 edges record an engagement whose citation names a
different document - a sibling paper by the same author or theory group - and named-only works can
only receive, never send, so their rows are empty by construction.
"""
import numpy as np
import matplotlib.pyplot as plt
import _cffig as _cf
from _cffig import house

STEM = "fig14_community_links"
SHORT = {"philosophy-of-mind": "Philosophy\nof mind", "philosophy-of-computation": "Philosophy of\ncomputation",
         "consciousness-science": "Consciousness\nscience", "biology-and-neuroscience": "Biology &\nneuroscience",
         "AI-and-ML": "AI &\nmachine learning", "ethics-and-policy": "Ethics &\npolicy",
         "unknown": "Not\nrecorded"}


def main():
    house.apply()
    W = _cf.works()
    edges = _cf.read("edges.csv")
    lanes = [c[0] for c in _cf.COMMUNITIES if any(w["community"] == c[0] for w in W.values())]
    idx = {c: i for i, c in enumerate(lanes)}
    M = np.zeros((len(lanes), len(lanes)), int)
    for e in edges:
        M[idx[W[e["from_key"]]["community"]], idx[W[e["to_key"]]["community"]]] += 1
    fig, ax = plt.subplots(figsize=(8.8, 6.2))
    ax.imshow(np.log1p(M), aspect="auto", vmin=0, vmax=np.log1p(M.max()),
              cmap=house.sequential(stops=[house.PAPER, "#dfe2de", "#b3b8b2", "#6e747e", "#2b2f36"]))
    for i in range(len(lanes)):
        for j in range(len(lanes)):
            v = M[i, j]
            dark = np.log1p(v) > 0.55 * np.log1p(M.max())
            ax.text(j, i, str(v) if v else "·", ha="center", va="center", fontsize=house.FS_BODY,
                    color=house.PAPER if dark else (house.INK if v else house.TEXT_LIGHT),
                    fontweight="semibold" if v else "normal")
    ax.set_xticks(range(len(lanes)))
    ax.set_xticklabels([SHORT[c] for c in lanes], fontsize=house.FS_LABEL)
    ax.set_yticks(range(len(lanes)))
    ax.set_yticklabels([SHORT[c].replace("\n", " ") for c in lanes], fontsize=house.FS_LABEL)
    ax.xaxis.tick_top()
    ax.set_xlabel("community of the work being engaged (built on, critiqued, replied to)")
    ax.xaxis.set_label_position("top")
    ax.set_ylabel("community of the engaging work")
    ax.grid(False)
    ax.set_xticks(np.arange(-.5, len(lanes)), minor=True)
    ax.set_yticks(np.arange(-.5, len(lanes)), minor=True)
    ax.grid(which="minor", color=house.PAPER, linewidth=2)
    ax.tick_params(which="minor", length=0)
    fig.subplots_adjust(left=0.22, right=0.99, top=0.80, bottom=0.03)
    house.save(fig, f"{_cf.FIGS}/{STEM}")
    total = int(M.sum())
    diag = int(np.trace(M))
    cross = total - diag
    _cf.data_statement(STEM, (
        f"All {total} of {len(edges)} documented engagements in edges.csv are counted (100%). {diag} "
        f"({100 * diag / total:.0f}%) stay inside one community and {cross} ({100 * cross / total:.0f}%) cross "
        "between communities. An engagement is recorded only where a reviewer found one in the text, so a zero "
        "means 'none recorded among the 36 reviewed works', never 'none exists'. The biology and neuroscience row "
        "and column are one work's, and named-only works cannot engage anything, so they send nothing."))


if __name__ == "__main__":
    main()
