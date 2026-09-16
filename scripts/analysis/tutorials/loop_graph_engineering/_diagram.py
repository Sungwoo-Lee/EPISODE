#!/usr/bin/env python3
"""_diagram.py - shared drawing helpers for the loop / graph engineering tutorial figures.

WHAT THIS IS. The figures on the tutorial page are explanatory diagrams, not charts: boxes, arrows
and labels that encode no measurement. The artifact guide (section 2.7) still wants them drawn by
Python scripts rather than in the page, so they can be re-run, restyled and dropped into slides.
Each `lgNN_*.py` script draws one figure; this module holds the pieces they share so a box looks
the same in all six.

COLOUR MEANING, fixed here once for every figure (format register F11):
  * blue   (house.BLUE)   - an agent doing work: a model call, a pass of an agent's loop
  * orange (house.ORANGE) - a check: a verifier, a reviewer, a rule that can send work back
  * green  (house.GREEN)  - state kept on disk between passes: memory, a plan file, the diary
  * grey                  - everything else: people, tasks, structure
Red is never used, so the page's hazard box keeps its own meaning.

The tints are mixed from the house series colours and the house paper colour, so the palette still
lives only in `scripts/analysis/style/house.py`.
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))   # scripts/<a>/<b>/<c>/ -> repo
sys.path.insert(0, os.path.join(ROOT, "scripts", "analysis", "style"))
os.chdir(ROOT)

import matplotlib.pyplot as plt                                   # noqa: E402
from matplotlib.colors import to_rgb                              # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch    # noqa: E402

import house                                                      # noqa: E402

OUT = os.environ.get("LG_FIG_ROOT", "docs/project/tutorials/loop_and_graph_engineering/figures")


def tint(hex_colour: str, amount: float = 0.13) -> tuple:
    """`amount` of the colour laid over the house paper - a fill light enough to hold ink text."""
    c, p = to_rgb(hex_colour), to_rgb(house.PAPER)
    return tuple(amount * ci + (1 - amount) * pi for ci, pi in zip(c, p))


# role -> (fill, border)
ROLE = {
    "agent": (tint(house.BLUE), house.BLUE),
    "check": (tint(house.ORANGE), house.ORANGE),
    "state": (tint(house.GREEN), house.GREEN),
    "plain": (house.BG_SOFT, house.RULE),
    "person": (house.PAPER, house.INK_2),
}


def canvas(w_in: float, h_in: float):
    """A figure whose data units are inches, with the axes filling it and no axis drawn."""
    house.apply()
    fig = plt.figure(figsize=(w_in, h_in))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w_in)
    ax.set_ylim(0, h_in)
    ax.axis("off")
    return fig, ax


DRAWN = []   # (title, role) of every titled box, in drawing order - so a Data line can count, not type


def box(ax, cx, cy, w, h, title, sub=None, role="plain", title_size=None, lw=1.3, ls="-", r=0.08):
    fc, ec = ROLE[role]
    if title:
        DRAWN.append((title, role))
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                                boxstyle=f"round,pad=0,rounding_size={r}",
                                fc=fc, ec=ec, lw=lw, ls=ls, zorder=2))
    ts = title_size or house.FS_BODY
    if sub:
        n = sub.count("\n") + 1
        ax.text(cx, cy + 0.10 * n + 0.01, title, ha="center", va="center", fontsize=ts,
                fontweight="semibold", color=house.INK, zorder=3)
        ax.text(cx, cy - 0.06 - 0.055 * n, sub, ha="center", va="center", fontsize=house.FS_LABEL,
                color=house.INK_2, zorder=3, linespacing=1.25)
    else:
        ax.text(cx, cy, title, ha="center", va="center", fontsize=ts,
                fontweight="semibold", color=house.INK, zorder=3)


def frame(ax, x0, y0, x1, y1, title, sub=None, fc=None, ec=None, lw=1.2):
    """A labelled region whose title sits inside its top-left corner (used for nesting)."""
    ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, y1 - y0, boxstyle="round,pad=0,rounding_size=0.1",
                                fc=fc or house.PAPER, ec=ec or house.RULE, lw=lw, zorder=1))
    ax.text(x0 + 0.18, y1 - 0.27, title, ha="left", va="center", fontsize=house.FS_BODY,
            fontweight="semibold", color=house.INK, zorder=3)
    if sub:
        ax.text(x0 + 0.18, y1 - 0.53, sub, ha="left", va="center", fontsize=house.FS_LABEL,
                color=house.INK_2, zorder=3)


def arrow(ax, p, q, colour=None, rad=0.0, lw=1.4, ls="-", both=False, conn=None, z=4, shrink=0):
    """`shrink` is in points - used to stop an arrow at the rim of a round node."""
    style = "<|-|>" if both else "-|>"
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=13, lw=lw, ls=ls,
                                 color=colour or house.INK_2, shrinkA=shrink, shrinkB=shrink,
                                 connectionstyle=conn or f"arc3,rad={rad}", zorder=z))


def line(ax, p, q, colour=None, lw=1.2):
    ax.plot([p[0], q[0]], [p[1], q[1]], color=colour or house.RULE, lw=lw, zorder=1,
            solid_capstyle="round")


def label(ax, x, y, text, ha="center", va="center", colour=None, size=None, weight="normal", **kw):
    ax.text(x, y, text, ha=ha, va=va, fontsize=size or house.FS_LABEL, color=colour or house.INK_2,
            fontweight=weight, zorder=5, linespacing=1.25, **kw)


def save(fig, stem: str, data_statement: str):
    """Write SVG/PDF/PNG through the house checks, then the data-used line the page shows (11b).

    `check_text=False` is the documented opt-out from `house.save`'s text-inside-axes guard (added
    2026-09-16, register F18 amendment), and it applies to this whole family for one reason: these
    are DIAGRAMS. `canvas()` makes an axes that fills the entire figure with `axis("off")`, so the
    axes rectangle IS the canvas and there is no axis title underneath for a label to print
    through - which is the defect the guard exists to catch. A label sitting a couple of points
    past the rim of a borderless diagram is a drawing choice, not an escape. (It fires in practice:
    `lg02_prompting_vs_loop`'s "passes" label overhangs by 7 rendered pixels, about 2 px at display
    width.) Real plots must NOT use this opt-out.
    """
    house.save(fig, f"{OUT}/{stem}", check_text=False)
    with open(f"{OUT}/{stem}.data.txt", "w") as fh:
        fh.write(data_statement.strip() + "\n")
