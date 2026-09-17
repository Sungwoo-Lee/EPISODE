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
own ``OUTER, GAP, PAD, HEAD = 24, 16, 16, 64``. The rest -- the 1440 x 896
canvas, ``LEFT_W`` and ``MIN_RIGHT_W`` -- came from that sketch's companion
drawing script, which was DELETED on 2026-09-17 when this redesign's page moved
to showing the real renderer's output rather than a mock of it. Their
justification today is the plan itself: the canvas size is user decision Q3,
``LEFT_W = 320`` is the World map's column kept by user decision Q21, and
``MIN_RIGHT_W = 440`` is the thermoception diamond's own stated demand (see
``panels.THERMO_MIN_W``, which is where that number is reasoned about). The
packing arithmetic they produce is re-derived and pinned in the plan's
Revision 18 (section R18.1), and ``test_dashboard_layout.py`` fails with the
worked numbers if one moves. None of them is re-chosen here. Three columns sit
under a header: a fixed-width left column, the arena card in the middle, and
whatever width is left over on the right.

    right_w = 1440 - 24 - (24 + 320 + 16 + card_w + 16) = 1040 - card_w

THE ARENA IS A FIXED BOX, NOT A GROW PANEL. The arena draws the whole world at
exactly ``ARENA_CELL_PX`` pixels per world square. It never absorbs leftover
height and never grows to fill its column. Leftover height goes only to the
minimap and to the thermoception card. Worked numbers, both pinned by tests:

    10x10 world -> arena card 564 x 564, right column 476 px, band 236 px
     5x5  world -> arena card 314 x 314, right column 726 px, band 486 px

ONE COUPLING THAT IS EASY TO MISS. When a sensor band is present, the right
column is measured against the *arena's bottom edge*, so a **smaller** world
gives the right column **less** height, not more. A 5x5 world with a band leaves
the right column 314 px against the 516 px a thermal right column needs. No
maintained config reaches that today, but the packer must check it, and it
checks it in exactly one place: :func:`_validate_region` runs against whatever
arena height was selected, whichever of the three routes chose it (the world's
own size, the whole-world rule, or the fallback's shrink step).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator, Mapping, Sequence

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

#: Pixels per world square in the arena. Decided at Revision 18 (was 48 at
#: Revision 17, 32 before that). 50 px is the *smallest* square that clears
#: every measured legibility floor for two animals sharing one square (49 px)
#: and for a four-way square (50 px) -- it is a floor that is met exactly, not
#: a comfortable margin. Drawing size and minimum are deliberately the same
#: number: there is one arena floor, not two.
ARENA_CELL_PX: int = 50
ARENA_CELL_MIN_PX: int = 50

# Arena card chrome. The card is square by construction:
#   w = view * 50 + 2 * 32      h = 48 + view * 50 + 16
ARENA_TITLE_H: int = 48
ARENA_BOTTOM_PAD: int = 16
ARENA_SIDE_PAD: int = 32

#: Card title strip height, used as the default top chrome of a single-panel card.
CARD_TITLE_H: int = 46

#: The action pill in the arena card's title strip (plan Q4). Its size is not
#: pinned anywhere in the plan -- the design sketch draws the pill but never
#: states a box -- so these are developer-chosen and are refined in Phase 2 when
#: the text can actually be measured. Nothing else depends on them: the badge
#: sits in chrome the arena already reserves.
BADGE_W: int = 120
BADGE_H: int = 28

#: On this canvas the largest whole-world square is 53 px: at 54 px the sensor
#: band falls to 196 px and the right column to 436 px, both under their minima.
#: Recorded so nobody has to re-derive it; 50 px sits 3 px below the ceiling.
ARENA_CELL_CEILING_PX: int = 53


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
    arena expose its drawing area (exactly ``view x view`` squares of 50 px)
    separately from the card that frames it.
    """

    cards: Mapping[str, Box]
    panels: Mapping[str, Box]
    parent: Mapping[str, str]
    view_cells: int
    cell_px: int
    band: bool
    step: str
    compact: bool
    regions: Mapping[str, Box] = field(default_factory=dict)

    @property
    def arena_grid(self) -> Box:
        """The arena's drawing area: exactly ``view_cells * cell_px`` square."""
        return self.panels["arena"]


# --------------------------------------------------------------------------
# Packing
# --------------------------------------------------------------------------
def pack(ctx, cards: Sequence[CardDemand] | None = None) -> Layout:
    """Place every present panel, or raise :class:`LayoutOverflowError`.

    ``cards`` is normally derived from the registry; passing it explicitly is how
    a test packs a demand set that no real config produces.

    The fallback ladder is tried in the order the plan fixes (section D7.7 item
    3), and the step that succeeded is recorded on the returned
    :class:`Layout` so a concatenated video can assert it never changed:

      0. the whole world at 50 px  -- the only step a maintained config reaches
      1. a local window, ``max(local_view_size, 2 * max_range + 1)``
      2. the side-column layout
      3. the sensor-band layout
      4. shrink the window by 2 toward ``local_view_size``
      5. ``compact`` minimum sizes
      6. raise

    Every candidate is validated by the same code, so the right column is
    checked against whatever arena height that candidate chose. That single
    check covers all three routes to an arena height.
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
    """Yield ``(view_cells, band, compact, step_name)`` in the plan's order."""
    world = int(ctx.world_w)
    natural_band = bool(ctx.band_senses)
    window = max(int(ctx.local_view_size), 2 * int(ctx.max_sense_range) + 1)

    yield world, natural_band, False, "whole_world"
    if window != world:
        yield window, natural_band, False, "local_window"

    # Steps 2 and 3 of the plan's ladder -- "side column" then "sensor band" --
    # are not a free choice here. The approved design sketch settles the
    # selection: a grid-kind sense (smell or vision at range >= 1) goes in the
    # band, and everything else goes in the side column. So the two steps are
    # determined by the config rather than tried in turn, and there is nothing
    # to move into a band when no grid-kind sense exists. This is also what
    # makes the 5x5-with-a-band case raise rather than quietly falling back to a
    # side column that happens to fit.

    # Step 4: shrink the window by 2 per step, never below local_view_size.
    # This is the step that can *shorten* the arena and so take height away from
    # a right column measured against the arena's bottom edge -- which is why it
    # is validated like every other candidate rather than trusted.
    view = min(window, world) - 2
    while view >= int(ctx.local_view_size) and view >= 1:
        yield view, natural_band, False, f"shrink_{view}"
        view -= 2

    yield world, natural_band, True, "compact"


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

    top = HEAD
    bottom = CANVAS_H - GAP
    lx = OUTER
    cx = lx + LEFT_W + GAP

    grid_px = view * ARENA_CELL_PX
    card_w = grid_px + 2 * ARENA_SIDE_PAD
    card_h = ARENA_TITLE_H + grid_px + ARENA_BOTTOM_PAD

    rx = cx + card_w + GAP
    rw = CANVAS_W - OUTER - rx
    if rw < MIN_RIGHT_W:
        raise LayoutOverflowError(
            f"right column is {rw}px wide; needs {MIN_RIGHT_W}px "
            f"(arena view {view}x{view} at {ARENA_CELL_PX}px makes a {card_w}px card)"
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
                f"sensor band needs {max(MIN_BAND_H, need)}px, has {band_h}px "
                f"(arena view {view}x{view} pushes the band down to y={band_y})"
            )
        band_w = CANVAS_W - OUTER - cx
        band_box = Box(cx, band_y, band_w, band_h)
        regions["band"] = band_box
        card_boxes[band_cards[0].key] = band_box

    # The right column is measured against the arena's bottom edge whenever a
    # band is present. This is the coupling that makes a SMALLER world give the
    # right column LESS height.
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
        cell_px=ARENA_CELL_PX,
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
    # by the ordinary intersects() test rather than skipped before it. The
    # exemption this replaces was keyed on the boxes' COORDINATES matching, which
    # let through any two cards that happened to coincide, whatever they were; the
    # case it was written for (the band) cannot arise, because one card never pairs
    # with itself and a second band card is refused in _pack_once before a box is
    # assigned.
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
