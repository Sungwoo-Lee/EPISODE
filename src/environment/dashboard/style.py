"""Type roles, the vendored font, and the two drawing primitives every painter uses.

PLAIN-LANGUAGE SUMMARY. A dashboard that mixes six font sizes chosen ad hoc reads
as six dashboards. This module is the single list of text *roles* -- "card
title", "value", "caption" -- each with one weight, one size and one colour, so a
painter picks a role rather than a number. It also carries the two shapes drawn
everywhere (a rounded rectangle and a text artist) and the loader for the
vendored font.

WHERE THE VALUES COME FROM. The adopted design spec, as encoded in the approved
sketch ``renderer_layout_redesign/dashboard_style.py``. Copied, not re-chosen.

THE ONE UNIT RULE THAT MATTERS. Every painter works in **pixels with y growing
downward** -- each card's Axes is set up with ``xlim 0..w`` and ``ylim h..0`` --
because that is how the sketch is drawn and because a box handed out by the
packer is in pixels. Matplotlib wants font sizes in points, so ``PT = 72/DPI``
converts, once, here.
"""

from __future__ import annotations

import glob
import os

import matplotlib.font_manager as fm
from matplotlib.patches import FancyBboxPatch

from .palette import INK, INK2, INK3, IRIS, WHITE

DPI = 100
PT = 72 / DPI          # one pixel, in points, at this dpi

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
FONT_DIR = os.path.join(_ROOT, "assets", "fonts", "dashboard_sans_tab")
FONT = "Dashboard Sans Tab"

#: role -> (weight, rendered px, colour). The 14 px / 12 px legibility floors of
#: Revision 8 are met by construction: no playback role is below 14 and no
#: caption role below 12.
TYPE: dict[str, tuple[str, float, str]] = {
    "frame_title": ("semibold", 22, INK),
    "step": ("semibold", 26, INK),
    "step_aux": ("regular", 15, INK3),
    "card_title": ("semibold", 15, INK),
    "card_sub": ("regular", 13, INK3),
    "meta": ("regular", 14, INK2),
    "row_label": ("medium", 14, INK),
    "map_label": ("medium", 13, INK2),
    "value": ("semibold", 18, INK),
    "hero": ("semibold", 30, INK),
    "caption": ("regular", 12, INK3),
    "caption_medium": ("medium", 12, INK3),
    "col_head": ("medium", 12, INK3),
    "not_observed": ("regular", 13, INK3),
    "chip": ("medium", 13, INK2),
    "chip_on": ("semibold", 13, WHITE),
    "badge": ("semibold", 14, IRIS),
    "cell_num": ("semibold", 14, INK),
    "coll_letter": ("semibold", 12, INK3),
}

TITLE_BASE = 30        # a card title's baseline, from the card's top edge
CARD_RADIUS = 12

_REGISTERED = False


def register_fonts() -> str:
    """Register the vendored faces with Matplotlib, and return the family name.

    Raises if the faces are missing rather than silently falling back to
    DejaVu -- a frame drawn in the wrong font is a frame whose measured text
    widths mean nothing.
    """
    global _REGISTERED
    if _REGISTERED:
        return FONT
    paths = sorted(glob.glob(os.path.join(FONT_DIR, "DashboardSansTab-*.otf")))
    if len(paths) != 3:
        raise FileNotFoundError(
            f"expected 3 '{FONT}' faces in {FONT_DIR}, found {len(paths)}. They are "
            f"vendored assets; the dashboard does not fall back to another font, "
            f"because every measured text width in this package assumes this one."
        )
    for p in paths:
        fm.fontManager.addfont(p)
    if FONT not in {f.name for f in fm.fontManager.ttflist}:
        raise RuntimeError(f"font family {FONT!r} did not register")
    _REGISTERED = True
    return FONT


def text(ax, x, y, s, role, ha="left", va="baseline", color=None, **kw):
    """A text artist in one of the named roles."""
    weight, px, colour = TYPE[role]
    return ax.text(x, y, s, fontsize=px * PT, fontfamily=FONT, fontweight=weight,
                   color=color or colour, ha=ha, va=va, **kw)


def rrect(ax, x, y, w, h, r, fc, ec="none", lw_px=0.0, z=1.0, alpha=None, **kw):
    """A rounded rectangle in pixel coordinates."""
    return ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}",
        fc=fc, ec=ec, lw=lw_px * PT, zorder=z, alpha=alpha, **kw))


def signed(v, d=0) -> str:
    """A signed number with a real minus sign, and no '-0'."""
    s = f"{v:+.{d}f}"
    if float(s) == 0:
        s = f"{0:.{d}f}"
    return s.replace("-", "−")
