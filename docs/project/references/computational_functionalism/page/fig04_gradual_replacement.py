#!/usr/bin/env python3
"""FIGURE 4 - the gradual-replacement thought experiment, and the three answers it forces.

QUESTION IT ANSWERS. The best-known argument FOR computational functionalism asks you to imagine
replacing a brain's cells, one by one, with artificial parts that do exactly the same job. What
exactly is the setup, and what are the possible answers?

WHAT IS IN IT. TOP: five stages of the same brain, drawn as a grid of cells; filled circles are
living neurons and grey squares are artificial replacements, from 0% to 100% replaced. Under every
stage the person says the same thing, because by construction the replacements do the same job.
BOTTOM: three small sketches of the three possible answers to "what happens to the experience?"
- it stays, it fades slowly, or it stops at one step. These curves are ILLUSTRATIONS of the
answers, not measurements; nobody has run this experiment.

HOW IT IS DRAWN. Nothing is computed. The setup is the one in Cuda 1985 and Chalmers 1995 as the
reviews describe it; both keys are checked against works.csv when the figure is drawn. Ink greys
only, because hue on this page means research community.
"""
import numpy as np
import matplotlib.pyplot as plt
import _cffig as _cf
from _cffig import house

STEM = "fig04_gradual_replacement"
STAGES = [0, 25, 50, 75, 100]
N = 6           # cells per side of each brain grid
ANSWERS = [     # title, explanation, curve(x in 0..1)
    ("A. Experience stays the same",
     "The conclusion the argument aims at:\nthe copy feels what the original felt.",
     lambda x: np.ones_like(x)),
    ("B. Experience fades slowly",
     "'Fading qualia': the person still says\n'bright red' while seeing pale pink.",
     lambda x: 1 - 0.85 * x),
    ("C. Experience stops at one step",
     "Then someone must name the single\ncell whose replacement switched it off.",
     lambda x: np.where(x < 0.62, 1.0, 0.05)),
]


def main():
    house.apply()
    W = _cf.works()
    for k in ("cuda1985", "chalmers1995qualia"):
        if k not in W:
            raise SystemExit(f"{STEM}: key not in works.csv: {k}")
    rng = np.random.default_rng(7)
    order = rng.permutation(N * N)          # which cells are replaced first: fixed, so stages nest

    fig = plt.figure(figsize=(11.6, 7.4))
    top = fig.add_axes([0.01, 0.50, 0.98, 0.46])
    top.set_xlim(0, 100)
    top.set_ylim(0, 46)
    top.axis("off")
    top.text(0.5, 45.5, "Replace the brain's cells one by one with artificial parts that do the same job",
             ha="left", va="top", fontsize=house.FS_TITLE, fontweight="semibold", color=house.INK)
    cell = 2.6
    for s, pct in enumerate(STAGES):
        x0, y0 = 3.5 + s * 19.5, 14.0
        replaced = set(order[: round(N * N * pct / 100)])
        # markers, not patches: a marker is round in screen space whatever the axis scaling,
        # where a Circle patch on this unequal-aspect axis drew every neuron as an ellipse
        for i in range(N * N):
            cx, cy = x0 + (i % N) * cell + cell / 2, y0 + (i // N) * cell + cell / 2
            if i in replaced:
                top.scatter(cx, cy, s=150, marker="s", color="#a8aeaa", linewidths=0)
            else:
                top.scatter(cx, cy, s=150, marker="o", color=house.INK_2, linewidths=0)
        top.text(x0 + N * cell / 2, y0 - 2.0, f"{pct}% replaced", ha="center", va="top",
                 fontsize=house.FS_BODY, color=house.INK)
        top.text(x0 + N * cell / 2, y0 - 7.0, "says: “I see bright red”", ha="center", va="top",
                 fontsize=house.FS_LABEL, color=house.INK_2, style="italic")
    top.scatter(5.0, 37.6, s=150, marker="o", color=house.INK_2, linewidths=0)
    top.text(7.0, 37.6, "living neuron", va="center", fontsize=house.FS_LABEL, color=house.INK_2)
    top.scatter(23.0, 37.6, s=150, marker="s", color="#a8aeaa", linewidths=0)
    top.text(25.0, 37.6, "artificial part doing the same job", va="center", fontsize=house.FS_LABEL,
             color=house.INK_2)
    top.text(99.0, 37.6, "Behaviour is the same at every stage. What about experience?", ha="right",
             va="center", fontsize=house.FS_LABEL, color=house.INK, fontweight="semibold")

    x = np.linspace(0, 1, 200)
    for j, (title, expl, f) in enumerate(ANSWERS):
        ax = fig.add_axes([0.07 + j * 0.32, 0.12, 0.24, 0.24])
        ax.plot(x * 100, f(x), color=house.INK, lw=2.0)
        ax.set_xlim(0, 100)
        ax.set_ylim(-0.05, 1.15)
        ax.set_xticks([0, 50, 100])
        ax.set_yticks([0, 1])
        ax.set_yticklabels(["none", "full"])
        ax.grid(axis="y", visible=False)
        ax.set_xlabel("% of cells replaced", fontsize=house.FS_LABEL)
        if j == 0:
            ax.set_ylabel("experience\n(illustration only)", fontsize=house.FS_LABEL)
        # the explanation sits directly above the plot and the title above the explanation, as two
        # stacked text blocks; a title with a guessed pad collided with the explanation
        ax.text(0, 1.05, expl, transform=ax.transAxes, ha="left", va="bottom", fontsize=house.FS_LABEL,
                color=house.INK_2, linespacing=1.2)
        ax.text(0, 1.36, title, transform=ax.transAxes, ha="left", va="bottom", fontsize=house.FS_BODY,
                fontweight="semibold", color=house.INK)
    house.save(fig, f"{_cf.FIGS}/{STEM}", check_text=False)   # the explanations sit above each small panel on purpose
    _cf.data_statement(STEM, (
        "A schematic: nothing is measured and no data file is summarised. The top row is the setup of the "
        "gradual-replacement argument as the reviews of Cuda 1985 and Chalmers 1995 describe it; the bottom row "
        "sketches the three answers those works discuss. The curves are illustrations of the answers, not data: "
        "no reviewed work reports a measurement of experience during replacement, and the experiment has never "
        "been run."))


if __name__ == "__main__":
    main()
