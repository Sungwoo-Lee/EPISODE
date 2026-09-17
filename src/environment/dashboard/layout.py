"""The column packer: panel demands in, concrete disjoint boxes out.

PLAIN-LANGUAGE SUMMARY. Every panel of the episode dashboard says how much room
it needs. This module turns those demands into actual rectangles on a fixed
1440 x 896 canvas, and if they cannot all fit it **raises**
:class:`LayoutOverflowError` naming what did not fit and by how much. It never
shrinks a panel below its stated minimum to make room, and it never lets two
rectangles share a pixel. That is the whole point of the redesign: overlapping
dashboard text stops being something a human notices in a video and becomes an
exception thrown before a single frame is drawn.

NO MATPLOTLIB. This module imports no drawing library, and a test asserts it.
Layout runs once per episode, before any figure exists.

LAYOUT NEVER READS EPISODE DATA (plan section D7.7 item 1). :func:`pack` and every
panel's ``min_size`` accept only a :class:`~.panels.LayoutContext`, which is built
from environment params. Two episodes of one run therefore always pack to
identical boxes -- a property a test pins by inspecting the signatures.

THE GEOMETRY, AND WHERE THE NUMBERS COME FROM. ``OUTER``, ``GAP``, ``PAD`` and
``HEAD`` are read out of the design sketch's surviving style module,
``renderer_layout_redesign/dashboard_style.py``, which still carries them as its
own ``OUTER, GAP, PAD, HEAD = 24, 16, 16, 64``. ``LEFT_W = 320`` is the World
map's column and ``MIN_RIGHT_W = 440`` is the thermoception diamond's own stated
demand (see ``panels.THERMO_MIN_W``). Three columns sit under a header: a
fixed-width left column, the arena card in the middle, and whatever width is left
over on the right.

    right_w = 1440 - 24 - (24 + 320 + 16 + card_w + 16) = 1040 - card_w

THE ARENA IS A FIXED BOX OF FIXED SIZE, AND THE WINDOW IS A ZOOM INSIDE IT
(user decision 2026-09-17; plan Revision 27, which supersedes Revision 18's
whole-world arena). The arena's drawing area is **always** :data:`ARENA_PX`
square. What ``visualization.local_view_size`` decides is how many world squares
are drawn inside that fixed area -- i.e. how far the view is zoomed out:

    cell = ARENA_PX / view_cells      96 px at 5x5, 68.57 at 7x7, 48 at 10x10

So every world and every window packs to the same frame:

    arena card 544 x 544   right column 496 px   sensor band 256 px

That invariance is the point. The arrangement this replaces sized the card from
the WORLD (``view * 50 + 64``), so the left column, the right column and the band
all reflowed when the world's size changed, and the layout stopped fitting at
11x11 -- a 20x20 world silently changed the dashboard's shape instead of simply
showing more world at a smaller square. Nothing reflows now: a 5x5 world and a
50x50 world produce identical panel boxes, and only the grid's own square size
moves.

``ARENA_PX = 480`` is not chosen here. It is the approved design sketch's own
arena -- a 5x5 window at a 96 px square (plan section R18.1, the "Figure 3 as
approved" column) -- so this reproduces the approved frame exactly rather than
approximating it.

WHAT THE PACKER STILL REFUSES. The arena can no longer overflow, so the fallback
ladder exists only for genuinely impossible panel sets (a right column whose pods
do not fit the 544 px the arena leaves it). The one arena-side refusal left is a
window so wide that the square falls below :data:`ARENA_CELL_MIN_PX`, the size at
which the movers' artwork stops being legible when a square is shared.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator, Mapping, Sequence

# --------------------------------------------------------------------------
# Canvas and column constants, read from the approved design sketch.
# Multiples of 16 so imageio never resamples the frame (plan Q3).
# --------------------------------------------------------------------------
CANVAS_W: int = 1440
CANVAS_H: int = 896

OUTER: int = 24          # outer gutter
GAP: int = 16            # gap between cards
PAD: int = 16            # padding inside a card
HEAD: int = 64           # header band height; cards start at y = HEAD

LEFT_W: int = 320        # left column width (fixed)
MIN_RIGHT_W: int = 440   # the thermoception diamond plus its shared scale
MIN_BAND_H: int = 200    # a sensor band below this is unreadable

#: The arena's drawing area, in pixels, square -- FIXED, whatever the world size
#: and whatever the window. 480 = the approved sketch's 5 x 96 px arena.
ARENA_PX: int = 480

#: The smallest square this renderer will draw, and therefore the widest window.
#:
#: It is NOT a taste decision and it is not chosen here: it is
#: ``cells.RASTER_MIN_DIAMETER_PX / (2 * cells.SHARED_FRAC)`` rounded up -- the
#: square at which two occupants sharing one square are drawn exactly at the
#: diameter below which the artwork's silhouette stops surviving the video path's
#: chroma subsampling. It is restated here rather than imported because this
#: module must not import a drawing library, and
#: ``tests/env/test_dashboard_cells.py`` re-derives it from ``cells`` and fails if
#: the two ever disagree.
#:
#: At ARENA_PX = 480 it puts the widest usable window at **11 x 11** (43.6 px a
#: square); a 12-wide window would draw 40 px squares and is refused.
ARENA_CELL_MIN_PX: float = 43.0

# Arena card chrome. The card is square by construction:
#   w = ARENA_PX + 2 * 32      h = 48 + ARENA_PX + 16
ARENA_TITLE_H: int = 48
ARENA_BOTTOM_PAD: int = 16
ARENA_SIDE_PAD: int = 32

#: The arena card's outer size, constant: 480 + 64 = 544 on both axes.
ARENA_CARD_W: int = ARENA_PX + 2 * ARENA_SIDE_PAD
ARENA_CARD_H: int = ARENA_TITLE_H + ARENA_PX + ARENA_BOTTOM_PAD

#: Card title strip height, used as the default top chrome of a single-panel card.
CARD_TITLE_H: int = 46

#: The action pill in the arena card's title strip (plan Q4).
BADGE_W: int = 120
BADGE_H: int = 28


def arena_cell_px(view_cells: int) -> float:
    """Pixels per world square for a ``view_cells``-wide window.

    The arena is a fixed box, so this is a division rather than a table: the
    window zooms, the panel does not move. A non-integer result (68.571 px at a
    7-wide window) is deliberate and harmless -- every square is drawn inset by
    1 px on each side, so neighbouring squares never share an edge and no seam
    can appear between two rounded fills.
    """
    if view_cells < 1:
        raise LayoutOverflowError(f"a window of {view_cells} squares cannot be drawn")
    return ARENA_PX / float(view_cells)


class LayoutOverflowError(ValueError):
    """The panels' stated minimums do not fit the canvas.

    Raised **before any frame is drawn**. On the training path this fails only
    the render child process -- the recordings stay on disk and the error lands
    in the render log.
    """


@dataclass(frozen=True)
class Size:
    """A minimum demand in pixels. ``w == 0`` means "whatever the column gives"."""

    w: int
    h: int


@dataclass(frozen=True)
class Box:
    """An integer-pixel rectangle. Origin is the canvas top-left."""

    x: int
    y: int
    w: int
    h: int

    @property
    def right(self) -> int:
        return self.x + self.w

    @property
    def bottom(self) -> int:
        return self.y + self.h

    def intersects(self, other: "Box") -> bool:
        """True when the two boxes share at least one pixel.

        Touching edges do not count as sharing: a box ending at x=100 and one
        starting at x=100 are adjacent, not overlapping.
        """
        return (
            self.x < other.right
            and other.x < self.right
            and self.y < other.bottom
            and other.y < self.bottom
        )

    def contains(self, other: "Box") -> bool:
        """True when ``other`` lies wholly inside this box (equality allowed)."""
        return (
            other.x >= self.x
            and other.y >= self.y
            and other.right <= self.right
            and other.bottom <= self.bottom
        )


@dataclass(frozen=True)
class CardDemand:
    """What one card asks the packer for.

    A *card* is a placed unit -- it gets a box from a column. Its *children* are
    the panels drawn inside it, which get boxes carved out of the card's inner
    area. A single-panel card (the minimap, a sensor pod) has exactly one child
    filling its inner area; the merged vitals card stacks several.
    """

    key: str
    region: str               # 'header' | 'left' | 'centre' | 'right' | 'band'
    order: int
    min_h: int
    min_w: int = 0
    chrome_top: int = CARD_TITLE_H
    chrome_bottom: int = PAD
    chrome_side: int = PAD
    grow: bool = False
    max_h: int | None = None
    row: str | None = None    # cards sharing a row key sit side by side
    flow: str = "single"      # 'single' | 'stack' | 'row' | 'arena'
    children: tuple[str, ...] = ()
    child_h: int = 0
    child_min_w: tuple[int, ...] = ()   # per-child minimum width, for 'row' flow


@dataclass(frozen=True)
class Layout:
    """The packer's output.

    ``cards`` are the placed units and are pairwise disjoint. ``panels`` are the
    leaf boxes actually painted into; each lies inside its card, and leaves
    sharing a card are pairwise disjoint. Splitting the two is what lets the
    arena expose its drawing area (always ``ARENA_PX`` square) separately from
    the card that frames it.

    ``view_cells`` is how many world squares the grid draws across, and
    ``cell_px`` is ``ARENA_PX / view_cells``.
    """

    cards: Mapping[str, Box]
    panels: Mapping[str, Box]
    parent: Mapping[str, str]
    view_cells: int
    cell_px: float
    band: bool
    step: str
    compact: bool
    regions: Mapping[str, Box] = field(default_factory=dict)

    @property
    def arena_grid(self) -> Box:
        """The arena's drawing area: ``ARENA_PX`` square, always."""
        return self.panels["arena"]


# --------------------------------------------------------------------------
# Packing
# --------------------------------------------------------------------------
def window_cells(ctx) -> int:
    """How many world squares the grid view draws across.

    THE CONFIG DECIDES WHAT IS DRAWN, and the floor is the one thing it may not
    undercut: the view must at least cover what the agent can sense, so a sense
    reaching ``r`` squares forces a ``2r + 1`` window however small
    ``local_view_size`` is set. A world no larger than that window is drawn
    whole -- the whole world is the SPECIAL CASE of a window wider than the
    world, not the first choice.
    """
    window = max(int(ctx.local_view_size), 2 * int(ctx.max_sense_range) + 1)
    return max(1, min(window, int(max(ctx.world_w, ctx.world_h))))


def pack(ctx, cards: Sequence[CardDemand] | None = None) -> Layout:
    """Place every present panel, or raise :class:`LayoutOverflowError`.

    ``cards`` is normally derived from the registry; passing it explicitly is how
    a test packs a demand set that no real config produces.

    The ladder is two steps long now, and that is a consequence of the arena
    becoming a fixed box (Revision 27): the arena cannot overflow, so the only
    thing left to try is the ``compact`` vitals rows, and the only thing that can
    still fail is a right column whose own pods do not fit.
    """
    last: LayoutOverflowError | None = None
    for view, band, compact, step in _candidates(ctx):
        try:
            return _pack_once(ctx, view, band, compact, step, cards)
        except LayoutOverflowError as exc:
            last = exc
    assert last is not None, "the candidate ladder must yield at least one attempt"
    raise last


def _candidates(ctx) -> Iterator[tuple[int, bool, bool, str]]:
    """Yield ``(view_cells, band, compact, step_name)``.

    The view is decided by the CONFIG (:func:`window_cells`) and never by whether
    the packer finds it convenient, so there is exactly one view here and the
    remaining candidate is the compact fallback for the left column's text rows.
    """
    view = window_cells(ctx)
    natural_band = bool(ctx.band_senses)
    whole = view >= int(max(ctx.world_w, ctx.world_h))
    yield view, natural_band, False, ("whole_world" if whole else "local_window")
    yield view, natural_band, True, "compact"


def _pack_once(
    ctx,
    view: int,
    band: bool,
    compact: bool,
    step: str,
    cards: Sequence[CardDemand] | None,
) -> Layout:
    if cards is None:
        # Deferred so that panels.py may import this module's constants without
        # a cycle. panels.py is the only registry; layout.py stays generic.
        from . import panels as _panels

        cards = _panels.present_cards(ctx, band=band, compact=compact)

    cell_px = arena_cell_px(view)
    if cell_px < ARENA_CELL_MIN_PX:
        raise LayoutOverflowError(
            f"a {view}x{view} window draws {cell_px:.1f}px squares in the arena's "
            f"fixed {ARENA_PX}px box, below the {ARENA_CELL_MIN_PX:.0f}px at which two "
            f"occupants sharing one square stop being separable in the finished video. "
            f"Lower visualization.local_view_size (the widest window this renderer "
            f"draws is {int(ARENA_PX // ARENA_CELL_MIN_PX)}x"
            f"{int(ARENA_PX // ARENA_CELL_MIN_PX)}); the arena card is a fixed size and "
            f"is never grown to accommodate a wider window."
        )

    top = HEAD
    bottom = CANVAS_H - GAP
    lx = OUTER
    cx = lx + LEFT_W + GAP

    card_w, card_h = ARENA_CARD_W, ARENA_CARD_H

    rx = cx + card_w + GAP
    rw = CANVAS_W - OUTER - rx
    if rw < MIN_RIGHT_W:
        raise LayoutOverflowError(
            f"right column is {rw}px wide; needs {MIN_RIGHT_W}px "
            f"(the arena card is {card_w}px)"
        )

    card_boxes: dict[str, Box] = {}
    regions: dict[str, Box] = {}

    by_key = {c.key: c for c in cards}
    arena = by_key.get("arena")
    if arena is None:
        raise LayoutOverflowError("the registry produced no arena card")
    card_boxes["arena"] = Box(cx, top, card_w, card_h)
    regions["centre"] = Box(cx, top, card_w, card_h)

    # Header sits above every column, in the band the columns start below.
    #
    # ITS BOX IS THE WHOLE BAND, not the band inset by the gutter, and the
    # difference is not cosmetic: the header's Axes CLIPS the patches drawn into
    # it. Inset to `HEAD - 2 * GAP` = 32 px tall, the 4 px step-progress bar the
    # approved design draws at y = 48 fell outside its own Axes and was clipped
    # away on every frame ever rendered -- the title and step number survived
    # only because Matplotlib does not clip Text by default. The painter places
    # its own content against the gutter, so the box is the band.
    header = by_key.get("header")
    if header is not None:
        card_boxes["header"] = Box(0, 0, CANVAS_W, HEAD)
        regions["header"] = card_boxes["header"]

    band_cards = [c for c in cards if c.region == "band"]
    if band_cards:
        # Refused BEFORE any box is handed out, not after. The band is ONE card
        # whose children share its width; two cards here would both be given the
        # SAME box, i.e. a total overlap. Rejecting the second up front is what
        # makes "no two cards share a box" true by construction, which is why
        # _validate needs no exemption for coincident boxes.
        if len(band_cards) > 1:
            raise LayoutOverflowError(
                "more than one band card; the band is a single card whose children "
                "share its width"
            )
        band_y = top + card_h + GAP
        band_h = bottom - band_y
        need = max(c.min_h for c in band_cards)
        if band_h < max(MIN_BAND_H, need):
            raise LayoutOverflowError(
                f"sensor band needs {max(MIN_BAND_H, need)}px, has {band_h}px"
            )
        band_w = CANVAS_W - OUTER - cx
        band_box = Box(cx, band_y, band_w, band_h)
        regions["band"] = band_box
        card_boxes[band_cards[0].key] = band_box

    # The right column is measured against the arena's bottom edge whenever a
    # band is present. With a fixed arena this is a CONSTANT 544 px rather than
    # something the world's size moves, which is what removed the coupling that
    # made a smaller world starve the right column (Revision 27).
    right_bottom = (top + card_h) if band_cards else bottom
    regions["left"] = Box(lx, top, LEFT_W, bottom - top)
    regions["right"] = Box(rx, top, rw, right_bottom - top)

    for region, box in (("left", regions["left"]), ("right", regions["right"])):
        members = sorted(
            (c for c in cards if c.region == region), key=lambda c: c.order
        )
        card_boxes.update(_pack_region(region, box, members))

    panels, parent = _carve_panels(cards, card_boxes, ctx)

    layout = Layout(
        cards=card_boxes,
        panels=panels,
        parent=parent,
        view_cells=view,
        cell_px=cell_px,
        band=bool(band_cards),
        step=step,
        compact=compact,
        regions=regions,
    )
    _validate(layout, cards)
    return layout


def _pack_region(
    region: str, box: Box, members: Sequence[CardDemand]
) -> dict[str, Box]:
    """Stack ``members`` down a column, giving leftover height to growers."""
    if not members:
        return {}

    rows: list[list[CardDemand]] = []
    for card in members:
        if rows and card.row is not None and rows[-1][0].row == card.row:
            rows[-1].append(card)
        else:
            rows.append([card])

    avail = box.h
    need = sum(max(c.min_h for c in r) for r in rows) + GAP * (len(rows) - 1)
    if need > avail:
        detail = ", ".join(f"{c.key}={c.min_h}" for r in rows for c in r)
        raise LayoutOverflowError(
            f"{region} column needs {need}px, has {avail}px: {detail}"
        )

    widest = max((c.min_w for c in members), default=0)
    if widest > box.w:
        offender = max(members, key=lambda c: c.min_w)
        raise LayoutOverflowError(
            f"{region} column is {box.w}px wide; {offender.key} needs {offender.min_w}px"
        )

    grower_rows = {id(r) for r in rows if any(c.grow for c in r)}
    spare = avail - need
    share = spare // len(grower_rows) if grower_rows else 0

    out: dict[str, Box] = {}
    y = box.y
    for r in rows:
        h = max(c.min_h for c in r)
        if id(r) in grower_rows:
            h += share
        caps = [c.max_h for c in r if c.max_h is not None]
        if caps:
            h = min(h, min(caps))
        each_w = (box.w - GAP * (len(r) - 1)) // len(r)
        for i, c in enumerate(r):
            out[c.key] = Box(box.x + i * (each_w + GAP), y, each_w, h)
        y += h + GAP
    return out


def _carve_panels(
    cards: Sequence[CardDemand],
    card_boxes: Mapping[str, Box],
    ctx,
) -> tuple[dict[str, Box], dict[str, str]]:
    """Carve each card's inner area into its children's leaf boxes."""
    panels: dict[str, Box] = {}
    parent: dict[str, str] = {}

    for card in cards:
        box = card_boxes[card.key]
        inner = Box(
            box.x + card.chrome_side,
            box.y + card.chrome_top,
            max(0, box.w - 2 * card.chrome_side),
            max(0, box.h - card.chrome_top - card.chrome_bottom),
        )
        if not card.children:
            continue

        if card.flow == "single":
            panels[card.children[0]] = inner
            parent[card.children[0]] = card.key

        elif card.flow == "stack":
            y = inner.y
            for key in card.children:
                panels[key] = Box(inner.x, y, inner.w, card.child_h)
                parent[key] = card.key
                y += card.child_h
            if y > inner.bottom:
                raise LayoutOverflowError(
                    f"card {card.key} stacks {len(card.children)} rows of "
                    f"{card.child_h}px into {inner.h}px of inner height"
                )

        elif card.flow == "row":
            n = len(card.children)
            each = (inner.w - GAP * (n - 1)) // n
            if each <= 0:
                raise LayoutOverflowError(
                    f"card {card.key} cannot fit {n} children in {inner.w}px"
                )
            for i, key in enumerate(card.children):
                floor = card.child_min_w[i] if i < len(card.child_min_w) else 0
                if each < floor:
                    raise LayoutOverflowError(
                        f"{key} needs {floor}px of width in the {card.key}; "
                        f"{n} children share {inner.w}px, giving it {each}px"
                    )
                panels[key] = Box(inner.x + i * (each + GAP), inner.y, each, inner.h)
                parent[key] = card.key

        elif card.flow == "arena":
            # children[0] is the grid; the optional children[1] is the action
            # pill, which lives in the card's title strip rather than its inner
            # area -- the one leaf whose geometry is the card's chrome.
            panels[card.children[0]] = inner
            parent[card.children[0]] = card.key
            for key in card.children[1:]:
                panels[key] = place_action_badge(box, BADGE_W, BADGE_H)
                parent[key] = card.key

        else:  # pragma: no cover - guarded by the registry
            raise ValueError(f"card {card.key}: unknown flow {card.flow!r}")

    return panels, parent


def place_action_badge(arena_card: Box, badge_w: int, badge_h: int) -> Box:
    """The action pill's box, in the arena card's title strip (plan Q4)."""
    return Box(
        arena_card.right - PAD - badge_w,
        arena_card.y + (ARENA_TITLE_H - badge_h) // 2,
        badge_w,
        badge_h,
    )


def _validate(layout: Layout, cards: Sequence[CardDemand]) -> None:
    """The structural guarantee: nothing overlaps, nothing escapes, nothing is lost.

    This runs on every successful pack. It is deliberately a separate pass over
    the finished boxes rather than an invariant trusted from the packing code --
    a packer bug that produced overlapping boxes should be caught by geometry,
    not by the author's confidence.
    """
    canvas = Box(0, 0, CANVAS_W, CANVAS_H)

    keys = sorted(layout.cards)
    for key in keys:
        box = layout.cards[key]
        if box.w <= 0 or box.h <= 0:
            raise LayoutOverflowError(f"card {key} has a non-positive size: {box}")
        if not canvas.contains(box):
            raise LayoutOverflowError(f"card {key} leaves the canvas: {box}")

    # NO EXEMPTION FOR COINCIDENT BOXES. Two cards with equal boxes share every
    # pixel of both -- the most complete overlap there is -- so equality is caught
    # by the ordinary intersects() test rather than skipped before it.
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            if layout.cards[a].intersects(layout.cards[b]):
                raise LayoutOverflowError(
                    f"cards {a} and {b} intersect: {layout.cards[a]} vs {layout.cards[b]}"
                )

    declared: set[str] = set()
    for card in cards:
        declared.update(card.children)
    missing = declared - set(layout.panels)
    if missing:
        raise LayoutOverflowError(
            f"declared panels were never placed: {sorted(missing)}"
        )

    for key, box in layout.panels.items():
        card_box = layout.cards[layout.parent[key]]
        if not card_box.contains(box):
            raise LayoutOverflowError(
                f"panel {key} escapes its card {layout.parent[key]}: {box} not in {card_box}"
            )

    by_card: dict[str, list[str]] = {}
    for key in layout.panels:
        by_card.setdefault(layout.parent[key], []).append(key)
    for card_key, members in by_card.items():
        members = sorted(members)
        for i, a in enumerate(members):
            for b in members[i + 1:]:
                if layout.panels[a].intersects(layout.panels[b]):
                    raise LayoutOverflowError(
                        f"panels {a} and {b} intersect inside card {card_key}: "
                        f"{layout.panels[a]} vs {layout.panels[b]}"
                    )
