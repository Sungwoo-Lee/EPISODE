#!/usr/bin/env python3
"""FIGURE 3 - who engages whom: documented engagements between communities.

QUESTION IT ANSWERS. Do the communities that study pain's non-sensory side read each other?

WHAT IS IN IT. A grid: rows are the community of the citing work, columns the community of the work
it engages (edges.csv, joined to works.csv). Each cell counts documented engagements - a paper
building on, critiquing, replying to, reinterpreting or using another as evidence, as recorded by the
reviewers. Darker grey cells hold more links (grey, not a hue: blue and orange mean command vs evaluation on this page). The diagonal is a community engaging itself.

WHAT IT IS NOT. A citation census. Links exist only where a reviewer recorded one, named-only works
cannot cite anything, and the corpus is a selection. A zero means "none recorded in this corpus".
"""
import collections
import numpy as np
import matplotlib.pyplot as plt
import _impfig as _imp
from _impfig import house

STEM = "fig11_community_links"


def main():
    house.apply()
    W = _imp.works()
    edges = _imp.read("edges.csv")
    lanes = [c[0] for c in _imp.COMMUNITIES]
    idx = {c: i for i, c in enumerate(lanes)}
    M = np.zeros((len(lanes), len(lanes)), int)
    for e in edges:
        M[idx[W[e["from_key"]]["community"]], idx[W[e["to_key"]]["community"]]] += 1
    fig, ax = plt.subplots(figsize=(8.6, 6.4))
    ax.imshow(np.log1p(M), cmap=house.sequential(stops=[house.PAPER, "#dfe2de", "#b3b8b2", "#6e747e", "#2b2f36"]), vmin=0, vmax=np.log1p(M.max()), aspect="auto")
    for i in range(len(lanes)):
        for j in range(len(lanes)):
            v = M[i, j]
            dark = np.log1p(v) > 0.55 * np.log1p(M.max())
            ax.text(j, i, str(v) if v else "·", ha="center", va="center", fontsize=house.FS_BODY,
                    color=house.PAPER if dark else (house.INK if v else house.TEXT_LIGHT),
                    fontweight="semibold" if v else "normal")
    short = {"philosophy": "Philosophy", "clinical-psychology": "Clinical\npsychology",
             "neurology-neurosurgery": "Neurology &\nneurosurgery", "human-neuroscience": "Human\nneuroscience",
             "animal-circuits": "Animal\ncircuits", "computational": "Computa-\ntional", "unknown": "Not\nrecorded"}
    ax.set_xticks(range(len(lanes)))
    ax.set_xticklabels([short[c] for c in lanes], fontsize=house.FS_LABEL)
    ax.set_yticks(range(len(lanes)))
    ax.set_yticklabels([short[c].replace("\n", " ").replace("- ", "") for c in lanes], fontsize=house.FS_LABEL)
    ax.xaxis.tick_top()
    ax.set_xlabel("community of the work being engaged (cited, critiqued, replied to)")
    ax.xaxis.set_label_position("top")
    ax.set_ylabel("community of the citing work")
    ax.grid(False)
    ax.set_xticks(np.arange(-.5, len(lanes)), minor=True)
    ax.set_yticks(np.arange(-.5, len(lanes)), minor=True)
    ax.grid(which="minor", color=house.PAPER, linewidth=2)
    ax.tick_params(which="minor", length=0)
    fig.subplots_adjust(left=0.2, right=0.99, top=0.82, bottom=0.02)
    house.save(fig, f"{_imp.FIGS}/{STEM}")
    total = int(M.sum())
    diag = int(np.trace(M))
    into_phil = int(M[:, idx["philosophy"]].sum() - M[idx["philosophy"], idx["philosophy"]])
    _imp.data_statement(STEM, (
        f"All {total} of {len(edges)} documented engagements in edges.csv are counted (100%); {diag} "
        f"({100 * diag / total:.0f}%) stay inside one community and {into_phil} are recorded from outside philosophy "
        "into philosophy. Engagements exist only where a reviewer recorded one (full-tier reviews recorded about 1.8 times as many per paper as short summaries, and philosophy is almost all full-tier); named-only works cannot cite, "
        "so their rows are empty by construction."))


if __name__ == "__main__":
    main()
