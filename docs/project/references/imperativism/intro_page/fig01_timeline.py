#!/usr/bin/env python3
"""FIGURE 1 - the field at a glance: every work in the corpus on one timeline, by community and era.

QUESTION IT ANSWERS. When did each research community start working on pain's non-sensory side, how
dense was each era, and how much of the corpus was actually read?

WHAT IS IN IT. One horizontal lane per community (works.csv `community`), years on the x-axis
(works.csv `year`, the first public year). Filled marks were reviewed from the PDF, open marks are
named-only. Grey bands are the five eras (eras.csv). No work is labelled here: a label that floats away
from its mark reads as belonging to the wrong lane. Figure 2 names every work.
"""
import collections
import numpy as np
import matplotlib.pyplot as plt
import _impfig as _imp
from _impfig import house

STEM = "fig01_timeline"


def main():
    house.apply()
    works = list(_imp.works().values())
    eras = _imp.read("eras.csv")
    lanes = [c[0] for c in _imp.COMMUNITIES]
    ypos = {c: len(lanes) - 1 - i for i, c in enumerate(lanes)}

    fig, ax = plt.subplots(figsize=(11.6, 5.6))
    shade = ["#eef0ed", "#f7f8f6"]
    for i, er in enumerate(eras):
        x0, x1 = int(er["start_year"]) - 0.5, int(er["end_year"]) + 0.5
        ax.axvspan(x0, x1, color=shade[i % 2], zorder=0, lw=0)
        ax.text((x0 + x1) / 2, len(lanes) - 0.25, f"Era {i + 1}\n{er['start_year']}–{er['end_year']}",
                ha="center", va="bottom", fontsize=house.FS_LABEL, color=house.INK_2, linespacing=1.2)
    # stack works that share a lane and a year so marks never sit on top of each other
    slot = collections.Counter()
    for w in sorted(works, key=lambda r: (int(r["year"]), r["key"])):
        c = w["community"]
        k = (c, int(w["year"]))
        off = slot[k]
        slot[k] += 1
        y = ypos[c] + (off - 0.0) * 0.16 - 0.24
        read = w["status"] != "named-only"
        ax.scatter(int(w["year"]), y, s=46 if w["status"] == "reviewed-full" else 34,
                   marker=_imp.MARKER[c], facecolor=_imp.COLOUR[c] if read else house.PAPER,
                   edgecolor=_imp.COLOUR[c], linewidth=1.3, zorder=3)
    ax.set_xlim(1959, 2028)
    ax.set_ylim(-0.7, len(lanes) + 0.55)
    ax.set_yticks([ypos[c] for c in lanes])
    per = collections.Counter(w["community"] for w in works)
    ax.set_yticklabels([f"{_imp.LABEL[c]} ({per[c]})" for c in lanes])
    ax.set_xticks(range(1960, 2030, 10))
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=True, color=house.TICK_LINE, lw=0.8)
    ax.set_xlabel("year the work first appeared (online year where it differs from print)")
    fig.subplots_adjust(left=0.17, right=0.99, top=0.97, bottom=0.12)
    house.save(fig, f"{_imp.FIGS}/{STEM}")
    n = len(works)
    read = sum(w["status"] != "named-only" for w in works)
    _imp.data_statement(STEM, (
        f"All {n} of {n} works in the corpus are drawn (100%): {read} reviewed from the PDF (filled marks) and "
        f"{n - read} named-only (open marks). The number after each community is its count of works. "
        "Nothing is filtered; the corpus itself is a selection (one survey's references plus history anchors), "
        "so lane sizes describe this corpus, not the size of each community's literature."))

if __name__ == "__main__":
    main()
