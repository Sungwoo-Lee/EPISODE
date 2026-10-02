"""Text that is measured into its box -- and raises rather than lying.

PLAIN-LANGUAGE SUMMARY. The defect this whole redesign exists to remove is a
label printed on top of another one. Half of that problem is layout (panels get
boxes that cannot overlap); the other half is this module: a piece of text must
fit the width it was given, and when it cannot, *something has to give*. What
gives is decided here, by what kind of text it is.

THE SPLIT, AND WHY IT IS THE WAY ROUND IT IS (plan section D1.3).

* **A number never shrinks past the floor and never ellipsises.** A body
  temperature rendered as ``-14...`` or as 7 px of unreadable grey is worse than
  no frame at all, because a viewer reads it and believes it. So the numeric
  kinds raise :class:`TextFitError`, and the episode fails loudly before the
  video exists.
* **Free text (the header line only) may ellipsise at the floor**, and every
  ellipsis is written to the render log, so a truncation is a recorded event
  rather than a silent one.

THE FLOORS are 14 px for playback text and 12 px for captions (Revision 8).
They are *rendered* pixel sizes, measured with Matplotlib's own text metrics at
the figure's dpi -- not point sizes hopefully converted.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

LOG = logging.getLogger("dashboard.text")

#: Rendered-pixel floors (Revision 8). Below these a reader cannot be expected to
#: read the frame, so shrinking further is not an option the renderer has.
PLAYBACK_FLOOR_PX = 14.0
CAPTION_FLOOR_PX = 12.0

#: Text kinds that carry a value a reader relies on. They raise at the floor.
#: Free text is everything else, and only the header is free text today.
NUMERIC_KINDS = frozenset({
    "vital_row", "temp_row", "hidden_state", "intensity", "thermal_diamond",
    "text_row", "cell_num", "value", "hero", "badge", "chip", "chip_on",
    "coll_letter", "map_label", "caption", "caption_medium", "col_head",
    "card_title", "card_sub", "row_label", "not_observed", "step", "step_aux",
})

ELLIPSIS = "…"


class TextFitError(ValueError):
    """A text that must stay readable does not fit the box it was given.

    Raised **before the frame is produced**. The message names the string, the
    width it needed and the width it had, because "text did not fit" without
    those three numbers is not actionable.
    """


@dataclass(frozen=True)
class FitResult:
    text: str
    width_px: float
    size_px: float
    ellipsised: bool


def measure(artist, renderer) -> float:
    """Rendered width of a text artist, in pixels."""
    return float(artist.get_window_extent(renderer).width)


def fit_text(artist, text: str, max_w: float, renderer, *,
             numeric: bool = True, floor_px: float = CAPTION_FLOOR_PX,
             where: str = "") -> FitResult:
    """Set ``text`` on ``artist`` so it fits ``max_w``, or raise / ellipsise.

    The artist is shrunk one point at a time down to ``floor_px``. At the floor,
    a numeric kind raises and free text is ellipsised and logged.
    """
    artist.set_text(text)
    size_px = float(artist.get_fontsize()) * artist.figure.dpi / 72.0
    w = measure(artist, renderer)
    if w <= max_w + 0.5:
        return FitResult(text, w, size_px, False)

    start_px = size_px
    while size_px > floor_px + 1e-9:
        size_px = max(floor_px, size_px - 1.0)
        artist.set_fontsize(size_px * 72.0 / artist.figure.dpi)
        w = measure(artist, renderer)
        if w <= max_w + 0.5:
            return FitResult(text, w, size_px, False)

    if numeric:
        artist.set_fontsize(start_px * 72.0 / artist.figure.dpi)
        artist.set_text(text)
        raise TextFitError(
            f"{where or 'text'} {text!r} needs {measure(artist, renderer):.0f}px at the "
            f"{floor_px:.0f}px legibility floor but its slot is {max_w:.0f}px. This is a "
            f"numeric element, so it is not shrunk further and not ellipsised: a number a "
            f"viewer cannot read, or reads wrongly, is worse than a missing frame."
        )

    kept = text
    while len(kept) > 1:
        kept = kept[:-1]
        artist.set_text(kept.rstrip() + ELLIPSIS)
        w = measure(artist, renderer)
        if w <= max_w + 0.5:
            LOG.info("ellipsised %s: %r -> %r (slot %.0fpx)", where, text,
                     artist.get_text(), max_w)
            return FitResult(artist.get_text(), w, size_px, True)
    raise TextFitError(
        f"{where or 'text'} {text!r} cannot be ellipsised into {max_w:.0f}px"
    )
