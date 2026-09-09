#!/usr/bin/env python3
"""house.py - the figure style, as code rather than as prose.

WHAT THIS IS. A matplotlib translation of the design system behind
transformer-circuits.pub/2026/workspace, read out of that page's own stylesheets rather than from
looking at it. The values are quoted in `docs/develop/active/meta/transformer_circuits_style.html`,
which is the human-readable half of this file; if the two ever disagree, this one is what actually
draws, so fix the document.

WHY IT IS A MODULE. A style written down in a document is a style that each figure script
re-implements slightly differently. The point of putting it here is that `apply()` is the only
place any of these numbers exist, so changing the house style is one edit rather than fifteen.

THE CONVENTIONS, and what each one is for:
  * no axis spines at all - the source deletes them (`.axis path.domain {display:none}`) rather
    than lightening them, so the reader takes values off faint horizontal rules instead of off a
    frame around the data;
  * no tick marks, only those rules, in #ddd;
  * a hierarchy INSIDE the figure: tick labels light and small, axis titles darker and heavier, so
    a reader finds out what is plotted before how much;
  * legends below the axes, never floating in the plot, in the mono face;
  * two data colours, Paul Tol's blue and orange, chosen because they stay distinguishable under
    the common colour-vision deficiencies. Everything else is grey.

TWO PLACES THE SOURCE STYLE CANNOT BE COPIED LITERALLY, both recorded in the document:

  1. SIZES. Their pages display a figure at roughly its natural width, so an 11px tick label is
     11px on screen. This project renders 1500-2300px wide and displays in a 730px column, so a
     literal 11pt label lands near 5px - under the 9px floor the artifact guide enforces. What
     transfers is the RATIO (labels < axis titles < figure title), not the absolute values, so the
     sizes below are scaled and `check_floor()` exists to prove the result clears 9px.
  2. COLOUR MEANING. Their blue and orange mean "series 1" and "series 2". Several pages in this
     project already spend purple/blue/green on what a modulator reads. Passing `series=` an
     explicit list is therefore supported: the house palette is a default, not a mandate, and a
     page whose colours already mean something keeps its own.
"""
from __future__ import annotations

import logging
import os

import matplotlib
matplotlib.use("Agg")

# The three Anthropic faces are proprietary and will not resolve anywhere but that site, which is
# expected and documented -- the fallbacks are what render. Keeping them first in the stack records
# the intent; silencing the lookup keeps every figure script from printing three warnings per save.
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
import matplotlib.pyplot as plt
from cycler import cycler

_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))

# --- the palette, verbatim from the source stylesheets -----------------------------------------
# Each grey is written there as `var(--gray-N, #hex)` and no --gray-N is defined in any of the
# three sheets, so these fallbacks are what actually render on that site.
INK        = "#333333"   # --text
TICK       = "#555555"   # --tick
TEXT_LIGHT = "#888888"   # --text-light : captions, tick labels
TEXT_FAINT = "#bbbbbb"   # --text-faint
TICK_LINE  = "#dddddd"   # --tick-line  : the rules that replace the axes
RULE       = "#eeeeee"   # --rule
BG_SOFT    = "#fafafa"   # --bg-soft
PAPER      = "#ffffff"

TOL_BLUE   = "#0077bb"   # --tol-blue   / --series-blue
TOL_ORANGE = "#ee7733"   # --tol-orange / --series-orange
# The rest of Paul Tol's vibrant qualitative set, so a third and fourth series have a defined next
# colour instead of a free choice. Only the first two appear in the source; the others are the
# published scheme those two come from.
TOL_EXTRA  = ["#009988", "#cc3311", "#ee3377", "#0077bb"]
SERIES     = [TOL_BLUE, TOL_ORANGE] + TOL_EXTRA

# Pretendard, vendored at assets/fonts/pretendard/ under the SIL Open Font License 1.1 and
# registered with matplotlib below. It is the project's chosen face: the source's own three
# typefaces are proprietary and resolve nowhere else, and the DejaVu fallback that matplotlib
# reaches for otherwise is heavy and wide at these sizes.
FONT_SANS = ["Pretendard", "Anthropic Sans", "system-ui", "DejaVu Sans", "sans-serif"]
# A real monospaced stack, for anything that must line up by column. NOT Pretendard, which is
# proportional -- putting it first here would silently make "mono" mean nothing.
FONT_MONO = ["Anthropic Mono", "DejaVu Sans Mono", "SF Mono", "Menlo", "monospace"]


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
