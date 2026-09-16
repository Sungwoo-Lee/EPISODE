#!/usr/bin/env python3
"""FIGURE 1 - three answers to "what makes a toothache unpleasant?", drawn as where the content points.

QUESTION IT ANSWERS. The three theories in this corpus all say unpleasantness is a matter of an
experience's content. They differ on two things: whether that content DESCRIBES/EVALUATES or
COMMANDS, and whether it is about the world (the body, the tooth) or about the experience itself.
A reader who holds that two-by-two in mind can follow every argument on the page; prose alone
makes it easy to lose.

WHAT IS IN IT. One panel per theory, the same toothache in each. A rounded box is the experience;
the square box is what a content is about. Arrows are contents. Grey = a plain sensory report of the
bodily state, which carries no valence on its own. Orange = evaluative content. Blue = imperative
content. Klein's panel has no grey arrow: he holds that pain's content is exhausted by the command,
which forbids an action rather than describing the tooth. In Carruthers's account of pain, what is
evaluated as bad is the felt bodily state (2018, p. 665). Reflexive imperativism's blue arrow loops
back onto the experience itself.

HOW IT IS COMPUTED. Nothing is computed: this is a schematic that encodes no data. The content
formulas are taken from the reviewed papers (Klein 2007; Carruthers 2018; Barlassina & Hayward
2019, Barlassina 2020) and summarised in ../imperativism_lit_review.md.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts", "analysis", "style"))

import matplotlib.pyplot as plt                              # noqa: E402
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch  # noqa: E402
import house                                                  # noqa: E402

OUT = os.path.join(HERE, "figures")
STEM = "fig01_three_contents"

GREY = house.TEXT_LIGHT
EVAL = house.SERIES[1]      # orange: evaluative content
IMP = house.SERIES[0]       # blue: imperative content

PANELS = [
    # name, citation, gloss, colour, content label, object label, sensory arrow?, reflexive?
    ("Imperativism", "Klein 2007",
     "unpleasant because it forbids\nan action involving the body",
     IMP, "\u201cDon\u2019t bite with it!\u201d", "biting with\nthat tooth", False, False),
    ("Evaluativism", "Carruthers 2018, 2023",
     "unpleasant because it represents\nthe felt bodily state as bad",
     EVAL, "\u201cthis is bad\u201d", "the throbbing\ntooth-state", True, False),
    ("Reflexive imperativism", "Barlassina & Hayward 2019",
     "unpleasant because it commands\nless of this very experience",
     IMP, "\u201cLess of me!\u201d", "the throbbing\ntooth-state", True, True),
]


def panel(ax, name, who, gloss, colour, content, obj, sensory, reflexive):
    ax.set_xlim(0, 10)
    ax.set_ylim(0.6, 10.6)
    ax.axis("off")
    ax.text(0.2, 10.2, name, fontsize=house.FS_TITLE, fontweight="semibold", color=house.INK,
            va="top")
    ax.text(0.2, 9.25, who, fontsize=house.FS_LABEL, color=GREY, va="top")
    # the experience (rounded) and what its content is about (square)
    ax.add_patch(FancyBboxPatch((0.6, 3.6), 3.6, 2.2, boxstyle="round,pad=0.12,rounding_size=0.9",
                                fc=house.PAPER, ec=house.INK, lw=1.4))
    ax.text(2.4, 4.7, "toothache\nexperience", ha="center", va="center", fontsize=house.FS_LABEL,
            color=house.INK)
    ax.add_patch(FancyBboxPatch((6.5, 3.8), 2.9, 1.8, boxstyle="square,pad=0.1",
                                fc=house.PAPER, ec=GREY, lw=1.2))
    ax.text(7.95, 4.7, obj, ha="center", va="center", fontsize=house.FS_LABEL, color=house.INK)
    if sensory:
        # plain sensory content: a report of the bodily state, which carries no valence by itself
        ax.add_patch(FancyArrowPatch((4.35, 4.25), (6.4, 4.25), arrowstyle="-|>",
                                     mutation_scale=12, color=GREY, lw=1.3))
        ax.text(5.35, 3.35, "reports it", ha="center", va="top", fontsize=house.FS_LABEL,
                color=GREY)
    if reflexive:
        ax.add_patch(FancyArrowPatch((3.5, 5.95), (1.3, 5.95), connectionstyle="arc3,rad=0.9",
                                     arrowstyle="-|>", mutation_scale=14, color=colour, lw=2.2))
        ax.text(2.4, 7.9, content, ha="center", va="center", fontsize=house.FS_BODY,
                fontweight="semibold", color=colour)
    else:
        y = 5.2 if sensory else 4.7
        ax.add_patch(FancyArrowPatch((4.35, y), (6.4, y), arrowstyle="-|>", mutation_scale=14,
                                     color=colour, lw=2.2))
        # keep the label clear of both box outlines, whatever height the arrow sits at (register F33)
        ax.text(5.35, max(y + 1.05, 6.35), content, ha="center", va="center", fontsize=house.FS_BODY,
                fontweight="semibold", color=colour)
    ax.text(0.2, 1.9, gloss, fontsize=house.FS_LABEL, color=house.INK, va="top", linespacing=1.4)


def main():
    house.apply()
    fig, axes = plt.subplots(1, 3, figsize=(11.6, 4.6))
    for ax, p in zip(axes, PANELS):
        panel(ax, *p)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.98, bottom=0.03, wspace=0.08)
    house.save(fig, os.path.join(OUT, STEM))
    with open(os.path.join(OUT, f"{STEM}.data.txt"), "w") as fh:
        fh.write("Schematic, not measured: 3 theory panels drawn from the content formulas in the 5 "
                 "reviewed papers; no data points exist, so none are omitted (0 of 0, n/a).\n")


if __name__ == "__main__":
    main()
