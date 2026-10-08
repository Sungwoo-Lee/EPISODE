#!/usr/bin/env python3
"""FIGURE 1 - four claims about what a mind can be made of, from weakest to strongest.

QUESTION IT ANSWERS. People often say "the mind is like software, so it could run on any hardware".
That sentence hides several different claims of different strength. Which are they, and how do
they differ?

WHAT IS IN IT. Four steps, rising from left to right. Each step is one claim, in plain words, with
an everyday example and the work in this collection that states it most clearly. Each step claims
more than the step before it: if a higher claim is true, the lower ones are true too, but not the
other way round. The claims are taken from the synthesis's vocabulary section, which takes them
from the reviewed works.

HOW IT IS DRAWN. Nothing is computed. The four work keys are checked against works.csv when the
figure is drawn, so a renamed work breaks the build instead of mislabelling a step. Ink greys only:
hue on this page means research community, and this figure shows no communities.
"""
import textwrap
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import _cffig as _cf
from _cffig import house

STEM = "fig01_three_claims"

STEPS = [   # name, claim in plain words, everyday example, key of the work that states it most clearly
    ("Multiple realizability",
     "The same mental state can be built from different physical parts.",
     "Your pain and my pain can use slightly different neurons and still both be pain.",
     "fodor1974"),
    ("Substrate flexibility",
     "A mind could be built from some other material, but not necessarily from every material.",
     "Perhaps some non-living materials would work and others would not.",
     "seth2025"),
    ("Substrate independence",
     "A mind can be built from any of a broad class of materials.",
     "Neurons or silicon chips: the material makes little difference.",
     "bostrom2003"),
    ("Organizational invariance",
     "Copy how the parts act on each other, and you copy the mind, whatever the parts are made of.",
     "A silicon copy wired exactly like your brain would have your mind.",
     "chalmers1994cfc"),
]


def main():
    house.apply()
    W = _cf.works()
    missing = [k for *_, k in STEPS if k not in W]
    if missing:
        raise SystemExit(f"{STEM}: key not in works.csv: {missing}")
    fig, ax = plt.subplots(figsize=(11.6, 6.6))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    ax.set_position([0.01, 0.02, 0.98, 0.96])
    # one unit of height in points, so text is stacked by its real line height instead of by guesswork
    unit_pt = fig.get_size_inches()[1] * 0.96 * 72 / 100
    line = lambda fs, sp: fs * sp / unit_pt

    w, h, gap, rise = 22.5, 58.0, 2.0, 8.0
    fills = ["#f1f2f0", "#e6e8e5", "#d9dcd8", "#cbcfca"]   # darker = stronger claim, greys only
    for i, (name, claim, example, key) in enumerate(STEPS):
        x0 = 1.5 + i * (w + gap)
        y0 = 9.0 + i * rise
        ax.add_patch(FancyBboxPatch((x0, y0), w, h, boxstyle="round,pad=0.4,rounding_size=1.2",
                                    linewidth=1.0, edgecolor=house.RULE, facecolor=fills[i], zorder=2))
        y = y0 + h - 2.0
        blocks = [(f"Step {i + 1}", 99, house.FS_LABEL, house.TEXT_LIGHT, "normal", "normal", 1.2),
                  (name, 16, house.FS_BODY, house.INK, "semibold", "normal", 1.15),
                  (claim, 25, house.FS_LABEL, house.INK, "normal", "normal", 1.3),
                  ("Example: " + example, 26, house.FS_LABEL, house.INK_2, "normal", "italic", 1.3)]
        for text, width, fs, col, wt, st, sp in blocks:
            lines = textwrap.wrap(text, width)
            ax.text(x0 + 1.4, y, "\n".join(lines), ha="left", va="top", fontsize=fs, color=col,
                    fontweight=wt, style=st, linespacing=sp, zorder=3)
            y -= len(lines) * line(fs, sp) + 2.4
        if y < y0 + 8.0:
            raise SystemExit(f"{STEM}: step {i + 1} text runs into its source line; make the cards taller")
        ax.text(x0 + 1.4, y0 + 1.6, f"clearest statement:\n{W[key]['short_label']}", ha="left", va="bottom",
                fontsize=house.FS_LABEL, color=house.TEXT_LIGHT, zorder=3, linespacing=1.2)
    ax.add_patch(FancyArrowPatch((2.0, 3.0), (97.0, 3.0), arrowstyle="-|>", mutation_scale=14,
                                 color=house.INK_2, lw=1.4))
    ax.text(49.5, 4.2, "each step claims more than the step before it", ha="center", va="bottom",
            fontsize=house.FS_LABEL, color=house.INK_2)
    ax.text(1.5, 97.5, "From weakest to strongest: what can a mind be made of?", ha="left", va="top",
            fontsize=house.FS_TITLE, fontweight="semibold", color=house.INK)
    house.save(fig, f"{_cf.FIGS}/{STEM}")
    _cf.data_statement(STEM, (
        f"A schematic: nothing is computed and no data file is summarised. It shows {len(STEPS)} of the "
        f"{len(STEPS)} claims about substrate that the synthesis's vocabulary section sets out, each named "
        "with the reviewed work that states it most clearly; the four keys are checked against works.csv when "
        "the figure is drawn. The example sentences are illustrations written for this page, not quotations."))


if __name__ == "__main__":
    main()
