#!/usr/bin/env python3
"""house.py - the figure style, as code rather than as prose.

WHAT THIS IS. The matplotlib half of the project's house style. The page half - type, colour,
numbering, boxes, tabs, glossaries - is `docs/develop/active/meta/house_style_sheet.html`, which
also documents every value below. If the two ever disagree, this file is what actually draws, so
fix the document.

WHERE THE VALUES COME FROM. Two sources, kept apart on purpose:
  * the PALETTE is the one the Thermoregulation design page settled on (2026-09-08): a faintly
    green-grey ground, blue-black ink, and four hues - blue, orange, green, red;
  * the CHART CONVENTIONS were read out of the stylesheets behind
    transformer-circuits.pub/2026/workspace (2026-09-09) - spines deleted, no tick marks, faint
    horizontal rules, a label < axis title hierarchy, legend below and unboxed.

WHY IT IS A MODULE. A style written down in a document is a style that each figure script
re-implements slightly differently. `apply()` is the only place any of these numbers exist, so
changing the house style is one edit rather than fifteen.

TWO RULES THE MODULE CANNOT ENFORCE BY ITSELF, both stated on the style sheet:

  1. SIZES. Figures here render 1500-2300px wide and display in a 730px column. What transfers
     from the source is the RATIO (labels < axis titles < figure title); `check_floor()` proves
     the smallest label still clears the guide's 9px floor.
  2. COLOUR MEANING. The four series hues are the same values the page uses for its chrome accent
     and its warning / decision / danger boxes. A page whose figure spends a hue on a data category
     must not also spend it on chrome (format register F11 amendment). Pass `series=` to give a
     figure its own meaning, and the page swaps its chrome token - never the other way round.
"""
from __future__ import annotations

import logging
import os

import matplotlib
matplotlib.use("Agg")

# IBM Plex Mono is named first in the mono stack to match the page, but is not installed for
# matplotlib, so the fallback renders. Silencing the lookup keeps every figure script from printing a
# warning per save.
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
import matplotlib.pyplot as plt
from cycler import cycler

_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))

# --- the palette, from the Thermoregulation design page ------------------------------------
# Neutrals carry a slight green bias rather than being pure greys; the page's tokens are named in
# the right-hand comments so the two halves of the house style can be checked against each other.
INK        = "#16181d"   # --ink    : axis titles, legend text
INK_2      = "#4e545e"   # --ink-2  : secondary text
TEXT_LIGHT = "#6e747e"   # --ink-3  : tick labels (Thermoregulation #767c86, darkened for 4.5:1)
TICK       = INK_2
TICK_LINE  = "#dcdedb"   # --line   : the rules that replace the axes
RULE       = "#c9cdc9"   # --rule
BG_SOFT    = "#f1f2f0"   # --surface
PAPER      = "#fbfbfa"   # --ground : figures sit on the page ground, not on a white card

BLUE       = "#2a78d6"   # --series-1 (same value as --accent)
ORANGE     = "#eb6834"   # --series-2 (same value as --warn)
GREEN      = "#0f7a55"   # --series-3 (same value as --ok)
RED        = "#b02b2b"   # --series-4 (same value as --danger)
# Blue and orange first: that pair stays distinguishable under the common colour-vision
# deficiencies. Green and red are a poor pair for a red-green deficient reader, so a figure that
# needs a third and fourth series should also vary line style or marker, not hue alone.
SERIES     = [BLUE, ORANGE, GREEN, RED]

# Pretendard, vendored at assets/fonts/pretendard/ under the SIL Open Font License 1.1 and
# registered with matplotlib below. It is the house body face, so figure text matches the page's
# running text; the DejaVu fallback matplotlib reaches for otherwise is heavy and wide at these sizes.
FONT_SANS = ["Pretendard", "system-ui", "DejaVu Sans", "sans-serif"]
# A real monospaced stack, for anything that must line up by column. NOT Pretendard, which is
# proportional -- putting it first here would silently make "mono" mean nothing.
FONT_MONO = ["IBM Plex Mono", "DejaVu Sans Mono", "SF Mono", "Menlo", "monospace"]


def _register_vendored_fonts() -> bool:
    """Make the vendored Pretendard visible to matplotlib. Returns whether it resolved."""
    import glob
    import matplotlib.font_manager as fm
    for path in glob.glob(os.path.join(_ROOT, "assets", "fonts", "pretendard", "*.otf")):
        try:
            fm.fontManager.addfont(path)
        except Exception:
            pass
    return any("preten" in f.name.lower() for f in fm.fontManager.ttflist)


# Source sizes are 11 / 13 / 15 px and they are used as-is. An earlier version scaled them up by
# 1.55 on the theory that a figure rendered wide and shown narrow needs bigger type. That was wrong
# twice over: it is the CANVAS that should shrink, not the type that should grow, and the arithmetic
# already worked -- 11pt at 150dpi is 22.9px, which is 14.7px in a 730px column for a 1140px-wide
# figure. Scaling it produced a specimen whose labels ran off all four edges. `check_floor()` is
# what enforces legibility now; the sizes just stay honest to the source.
SCALE = 1.0
FS_LABEL = 11 * SCALE      # tick labels
FS_BODY  = 13 * SCALE      # axis titles
FS_TITLE = 15 * SCALE      # a figure title, when one is drawn into the image at all


def apply(series: list[str] | None = None) -> None:
    """Install the house style. Call once, at the top of a figure script."""
    _register_vendored_fonts()
    plt.rcParams.update({
        "figure.facecolor": PAPER, "savefig.facecolor": PAPER, "axes.facecolor": PAPER,
        "font.family": "sans-serif", "font.sans-serif": FONT_SANS,
        "font.size": FS_BODY,
        "axes.labelsize": FS_BODY, "axes.labelcolor": INK, "axes.labelweight": "semibold",   # CSS 600
        "axes.titlesize": FS_TITLE, "axes.titlecolor": INK, "axes.titleweight": "semibold",   # CSS 600
        "axes.titlelocation": "left", "axes.titlepad": 14,
        "xtick.labelsize": FS_LABEL, "ytick.labelsize": FS_LABEL,
        "xtick.color": TEXT_LIGHT, "ytick.color": TEXT_LIGHT,
        # no tick marks: the source draws rules, not ticks
        "xtick.major.size": 0, "ytick.major.size": 0,
        "xtick.minor.size": 0, "ytick.minor.size": 0,
        # the spine is deleted, not lightened
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.spines.left": False, "axes.spines.bottom": False,
        "axes.grid": True, "axes.grid.axis": "y", "axes.axisbelow": True,
        "grid.color": TICK_LINE, "grid.linewidth": 0.9, "grid.linestyle": "-",
        # Sparse rules. The source labels four or five values, not every step: the rules are there
        # to read a value off, and one every few pixels stops being a reference and starts being a
        # texture behind the data.
        "axes.autolimit_mode": "round_numbers",
        "legend.frameon": False, "legend.fontsize": FS_LABEL,
        "legend.handlelength": 1.1, "legend.handleheight": 0.35, "legend.columnspacing": 1.8,
        "lines.linewidth": 2.0, "lines.solid_capstyle": "round",
        "axes.prop_cycle": cycler(color=series or SERIES),
        "svg.fonttype": "none",     # keep text as text in the SVG, so it stays selectable
        "pdf.fonttype": 42,         # embed TrueType in the PDF rather than Type 3
    })


def legend_below(ax, ncol: int = 2, **kw):
    """The house legend: below the axes, centred, unboxed, in the mono face.

    Never inside the plot. The source puts it in a flex row under the chart with a 16px gap, and a
    legend that floats over data is the single most common way a figure loses a series.
    """
    leg = ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=ncol,
                    frameon=False, **kw)
    # The source sets legends in its mono face. We keep Pretendard instead: mixing a proportional
    # body face with a monospaced legend reads as an accident when the two are not from the same
    # family, and this project has one chosen face. The swatch and the smaller size already
    # separate the legend from the prose, which is the job the mono was doing.
    for t in leg.get_texts():
        t.set_color(INK)
        t.set_fontsize(FS_LABEL)
    return leg


def check_floor(fig, column_px: int = 730, floor_px: float = 9.0) -> float:
    """Assert the smallest text still clears the artifact guide's legibility floor.

    A figure is rendered wide and displayed narrow, so the size that matters is the rendered one:
    `pt * dpi/72 * column/width`. This is the check that lets the house style keep the SOURCE's
    ratios without inheriting its absolute sizes, which would be illegible here.
    """
    w_px = fig.get_size_inches()[0] * fig.dpi
    px = FS_LABEL * (fig.dpi / 72.0) * (column_px / w_px)
    if px < floor_px:
        raise SystemExit(
            f"house style: smallest label renders at {px:.1f}px in a {column_px}px column "
            f"(floor {floor_px}px). The figure is {w_px:.0f}px wide - narrow the canvas or raise "
            f"SCALE; do not lower the floor.")
    return px


def save(fig, stem: str, formats=("svg", "pdf", "png"), column_px: int = 730):
    """Write the figure once per format, vector first, and verify two things before returning.

    Vector is the default because a figure that exists only as a raster cannot go into a
    manuscript, and redrawing it later from a screenshot is how a paper figure stops matching the
    numbers behind it.
    """
    import os
    import numpy as np
    px = check_floor(fig, column_px)
    os.makedirs(os.path.dirname(stem) or ".", exist_ok=True)
    out = []
    for f in formats:
        p = f"{stem}.{f}"
        kw = {"metadata": {"Date": None}} if f == "svg" else {}
        # pad_inches explicitly: a rotated axis label's true ink reaches past the extent
        # matplotlib reports for it, so the default pad can end up entirely consumed and the label
        # sits flush against the crop edge.
        fig.savefig(p, bbox_inches="tight", pad_inches=0.14, facecolor=PAPER, **kw)
        out.append(p)
    # ink in the margin means a label was sheared off, which reads as a deliberate abbreviation
    png = f"{stem}.png"
    if os.path.exists(png):
        from PIL import Image
        a = np.asarray(Image.open(png).convert("RGB")).astype(int)
        # Threshold at 90 so an antialiased halo does not read as ink; 90 needs a pixel clearly
        # darker than paper. This guard is verified against a real case rather than a synthetic
        # one: the sensor-grid figure g03, before its label was shortened, reports 81 ink pixels on
        # its right edge and passes after. (A synthetic control that draws text off-canvas does NOT
        # work here -- `bbox_inches="tight"` simply expands to include it, so nothing is clipped.)
        ink = (np.abs(a - np.array([255, 255, 255])).sum(2) > 90)
        for side, strip in (("left", ink[:, :3]), ("right", ink[:, -3:]),
                            ("top", ink[:3, :]), ("bottom", ink[-3:, :])):
            if strip.sum():
                raise SystemExit(f"{stem}: ink in the {side} margin - something is clipped")
    plt.close(fig)
    print(f"  wrote {'  '.join(out)}   (smallest label {px:.1f}px at a {column_px}px column)")
    return out
