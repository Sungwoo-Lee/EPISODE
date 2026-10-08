#!/usr/bin/env python3
"""FIGURE 9 - one verdict, four routes, no shared premise.

QUESTION IT ANSWERS. Four reviewed works conclude that a detailed computer simulation of a brain
would not be conscious. Is that a consensus?

WHAT IS IN IT. A schematic. Each card on the left is one work's reason, in its own words where the
review quotes them, drawn in that work's community colour from figure 2's key. Each arrow runs to
the single verdict on the right. The cards do not connect to each other, because the reasons share
no premise: two of the four authors are defending computational functionalism while they say it.
The dashed link is the one kinship anyone claims - an endnote in the integrated-information paper
naming Searle and Leibniz's mill - and it is asserted rather than argued, so it is drawn differently
from the arrows that carry a reason.

HOW IT IS DRAWN. Nothing is computed. The four routes and their quotations are taken from §5.7 of
the field-history synthesis; each key is checked against works.csv so a renamed work breaks the
build rather than silently mislabelling a card.
"""
import textwrap
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import _cffig as _cf
from _cffig import house

STEM = "fig09_four_routes"

ROUTES = [   # key, the route in one line, the review's locus
    ("tononi2015", "A simulation is virtual; consciousness is real intrinsic cause-effect power. "
                   "“A computer simulation of a giant star will not bend space–time around the machine.”",
     "D §1, p. 15"),
    ("searle1980", "Intentionality is a biological phenomenon. “No one would suppose that we could produce "
                   "milk and sugar by running a computer simulation of… lactation and photosynthesis.”",
     "B §1, p. 424"),
    ("klein_maudlin", "A virtual machine is not a process that actually has an architecture — a conclusion "
                      "reached while DEFENDING computationalism, and called “suspiciously close to… Searle”.",
     "F §2, PDF p. 16"),
    ("seth2025", "Simulating a mechanism is neither implementing nor realising it. “Nothing gets wet in a "
                 "weather forecasting computer.”",
     "C §5 §3.7"),
]
VERDICT = "A detailed computer simulation\nof a brain would not be conscious"


def main():
    house.apply()
    W = _cf.works()
    missing = [k for k, _, _ in ROUTES if k not in W]
    if missing:
        raise SystemExit(f"{STEM}: route key not in works.csv: {missing}")
    fig, ax = plt.subplots(figsize=(11.6, 5.8))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    ax.set_position([0.01, 0.02, 0.98, 0.9])

    ax.text(0, 99, "Four reviewed works, four reasons, one verdict — and no premise in common",
            ha="left", va="top", fontsize=house.FS_TITLE, fontweight="semibold", color=house.INK)

    top, gap, h = 88.0, 3.0, 18.5
    centres = []
    for i, (key, line, locus) in enumerate(ROUTES):
        w = W[key]
        col = _cf.COLOUR[w["community"]]
        y1 = top - i * (h + gap)
        y0 = y1 - h
        ax.add_patch(FancyBboxPatch((1.5, y0), 50, h, boxstyle="round,pad=0.6,rounding_size=1.4",
                                    linewidth=1.4, edgecolor=col, facecolor=house.BG_SOFT, zorder=2))
        ax.text(3.6, y1 - 3.4, w["short_label"], ha="left", va="center", fontsize=house.FS_BODY,
                fontweight="semibold", color=col, zorder=3)
        ax.text(50.0, y1 - 3.4, f"{_cf.LABEL[w['community']]}  ·  {locus}", ha="right", va="center",
                fontsize=house.FS_LABEL, color=house.TEXT_LIGHT, zorder=3)
        ax.text(3.6, y1 - 7.0, "\n".join(textwrap.wrap(line, 72)), ha="left", va="top",
                fontsize=house.FS_LABEL, color=house.INK, linespacing=1.35, zorder=3)
        centres.append((y0 + h / 2, col))

    vy = (centres[0][0] + centres[-1][0]) / 2
    ax.add_patch(FancyBboxPatch((64, vy - 9), 34, 18, boxstyle="round,pad=0.6,rounding_size=1.4",
                                linewidth=1.6, edgecolor=house.INK, facecolor=house.PAPER, zorder=2))
    ax.text(81, vy + 3.2, "the shared verdict", ha="center", va="center", fontsize=house.FS_LABEL,
            color=house.TEXT_LIGHT, zorder=3)
    ax.text(81, vy - 2.6, VERDICT, ha="center", va="center", fontsize=house.FS_BODY, color=house.INK,
            linespacing=1.35, zorder=3)
    for y, col in centres:
        ax.add_patch(FancyArrowPatch((52.6, y), (63.4, vy), arrowstyle="-|>", mutation_scale=11,
                                     color=col, lw=1.4, shrinkA=0, shrinkB=2,
                                     connectionstyle="arc3,rad=0.10", zorder=1, alpha=0.9))
    # the one claimed kinship, drawn as a claim rather than as a reason
    ax.add_patch(FancyArrowPatch((53.4, centres[0][0] - 3), (53.4, centres[1][0] + 3), arrowstyle="-|>",
                                 mutation_scale=9, color=house.TEXT_LIGHT, lw=1.0, ls=(0, (4, 3)),
                                 connectionstyle="arc3,rad=-0.9", zorder=1))
    ax.text(58.5, (centres[0][0] + centres[1][0]) / 2, "kinship claimed in an\nendnote, not argued",
            ha="left", va="center", fontsize=house.FS_LABEL, color=house.TEXT_LIGHT, linespacing=1.25)
    ax.text(1.5, 0.8,
            "The cards are deliberately not joined to one another: merging them would draw a consensus that "
            "does not exist.", ha="left", va="bottom", fontsize=house.FS_LABEL, color=house.INK_2)
    house.save(fig, f"{_cf.FIGS}/{STEM}")
    _cf.data_statement(STEM, (
        f"A schematic: nothing is computed and no file is summarised. It draws {len(ROUTES)} of the "
        f"{len(ROUTES)} routes recorded in §5.7 of the field-history synthesis, each quoted from the review "
        "of that work, with the four keys checked against works.csv at build time. The community colours are "
        "figure 2's. The corpus holds no fifth work concluding this, and none of the four cites another of them "
        "for the conclusion."))


if __name__ == "__main__":
    main()
