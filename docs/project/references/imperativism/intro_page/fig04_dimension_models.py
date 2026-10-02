#!/usr/bin/env python3
"""FIGURE 4 - how pain was divided: every model of pain's components in the corpus, in order.

QUESTION IT ANSWERS. How many parts has pain been said to have, and what were they called, from the
gate-control paper to the 2020s?

WHAT IS IN IT. One row per model (dimension_models.csv), oldest at the top. The left column names the
work, its year and the model. Each box to the right is one component the model names, in the order the
model lists them; the number of boxes is the number of components. Box outlines take the colour of the
work's community. A dashed outline marks a named-only work, whose model is known only from citing papers.
"""
import textwrap
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import _impfig as _imp
from _impfig import house

STEM = "fig04_dimension_models"


def main():
    house.apply()
    W = _imp.works()
    rows = sorted(_imp.read("dimension_models.csv"), key=lambda r: (int(r["year"]), r["key"]))
    n = len(rows)
    fig, ax = plt.subplots(figsize=(11.4, 0.56 * n + 0.4))
    ax.set_xlim(0, 100)
    ax.set_ylim(-1.0, n - 0.35)
    ax.axis("off")
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    # the component boxes start just right of the widest left-column text, measured, never guessed
    widest = 0.0
    for r in rows:
        for txt, weight in ((W[r["key"]]["short_label"], "semibold"), (textwrap.fill(r["model_label"], 46), "normal")):
            t = ax.text(0.2, 0, txt, fontsize=house.FS_LABEL, fontweight=weight)
            widest = max(widest, t.get_window_extent(renderer=rend).transformed(ax.transData.inverted()).x1)
            t.remove()
    x0 = widest + 1.5
    for i, r in enumerate(rows):
        y = n - 1 - i
        w = W[r["key"]]
        c = w["community"]
        named = w["status"] == "named-only"
        ax.text(0.2, y + 0.24, w["short_label"], ha="left", va="center", fontsize=house.FS_LABEL,
                fontweight="semibold", color=house.INK)
        ax.text(0.2, y + 0.06, textwrap.fill(r["model_label"], 46), ha="left", va="top", fontsize=house.FS_LABEL,
                color=house.INK_2, linespacing=1.05)
        x = x0
        for comp in [s.strip() for s in r["components"].split(";") if s.strip()]:
            t = ax.text(x + 0.9, y, comp, ha="left", va="center", fontsize=house.FS_LABEL, color=house.INK)
            bb = t.get_window_extent(renderer=rend).transformed(ax.transData.inverted())
            wdt = bb.width + 1.8
            ax.add_patch(FancyBboxPatch((x, y - 0.3), wdt, 0.6, boxstyle="round,pad=0,rounding_size=0.18",
                                        fc=house.PAPER, ec=_imp.COLOUR[c], lw=1.3,
                                        ls=(0, (3, 2)) if named else "-", mutation_aspect=0.12))
            x += wdt + 1.2
        if x > 100:
            raise SystemExit(f"{r['key']}: components overflow the row")
        if i < n - 1:
            ax.plot([0, 100], [y - 0.5, y - 0.5], color=house.TICK_LINE, lw=0.7)
    fig.subplots_adjust(left=0.005, right=0.995, top=0.995, bottom=0.005)
    house.save(fig, f"{_imp.FIGS}/{STEM}")
    named = sum(W[r["key"]]["status"] == "named-only" for r in rows)
    works_n = len(W)
    _imp.data_statement(STEM, (
        f"{n} of {works_n} works ({100 * n / works_n:.0f}%) propose or test a component model and are drawn; "
        f"the other {works_n - n} do not state one. {named} of the {n} are named-only (dashed boxes), their "
        "components taken from how reviewed papers describe them."))


if __name__ == "__main__":
    main()
