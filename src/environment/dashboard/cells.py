"""One square of the world: the floor it stands on, and who is standing on it.

PLAIN-LANGUAGE SUMMARY. A square of the world can hold more than one thing at
once -- the agent standing in a bush, a predator and a rabbit in the same square,
food lying on a rock. The old renderer drew every occupant on the *same centre
point*, so two drawings landed on top of each other and whichever name sorted
later in the alphabet won: an agent standing in a bush rendered as an agent
alone. This module is the fix the user chose (**variant H**, decided question
Q18), and its rule is one sentence:

    **Terrain is the floor, not a picture in the middle of the square.**

A bush, rock, tree or campfire is drawn as ground cover filling the square --
inset by :data:`BED_MARGIN` on every side, so a ring of the square's own
temperature colour always shows -- and the occupants stand *on* it. Because the
floor costs the occupants no room, a lone agent on a bush is drawn at exactly the
size it would be on an empty square. A second and a third occupant stand side by
side in a band across the middle of the square. From three occupants up the
square degenerates to equal tiles with no focal point: that is a **property** of
the design, recorded rather than hidden (plan section R17.5 item 2).

WHY NOTHING HERE IS A PNG. Every form below is a vector primitive (plan Revision
19, finding 58). The legibility of a shared square is decided by an arithmetic
floor -- the predator's amber eye slit and the rabbit's ear gap must clear about
3 rendered pixels -- and ``tests/env/test_dashboard_cells.py`` recomputes that
number as ``MIN_MARK x h`` and compares it against the measured 49 px / 50 px
square floors. A raster icon cannot supply ``MIN_MARK x h``, so a raster icon
cannot be checked.

TWO CONSTRAINTS THAT LOOK LIKE STYLE AND ARE NOT.

1. **Each bed is exactly one artist**, and its ink covers at least 40 % of the
   square (plan section R20.8). The pixel audit separates "floor" from
   "occupant" by *measured area*, never by a painter's say-so, so a bed split
   into six little artists would have its flames and logs counted as an occupant
   and would fail a correct frame. One artist, measured whole.
2. **Depth is pinned, not incidental** (sections R20.1, R20.2): bed **below**
   token, the agent's square outline **below** token, a sense's footprint
   outline **below** token. Drawn above, a 1.5 px footprint edge crossing a
   20 px occupant deletes ~7 % of it and the audit's survival floor fires on a
   picture that is actually correct. Below, the occupant is the subject and the
   annotation passes behind it -- which is also the better picture.

VOCABULARY, fixed here so painter, test and audit use one set of words:
**ground** = the square's own fill (its temperature colour, or the neutral track
when the world has no temperature); **bed** = the terrain ground cover;
**token** = one occupant's drawing; **slot** = the box a token is drawn for;
**h** = a token's ink half-extent in pixels, the one number that decides
legibility.

Forms are ported from the round-2 design mock
``tmp/20260916_design_cell_cooccupancy_r2/cooccupancy_r2.py``, with the bed forms
rebuilt full-bleed per the constraint above.
"""

from __future__ import annotations

from dataclasses import dataclass

from matplotlib.patches import Circle, Ellipse, FancyBboxPatch, Polygon, Rectangle

from . import palette as P

# --------------------------------------------------------------------------
# The rule's constants
# --------------------------------------------------------------------------

#: Draw order, explicit and never alphabetical. The observed overdraw bug is
#: exactly what a ``sorted()`` over entity names buys. Slots are filled left to
#: right, then top to bottom, in this order.
CELL_PRIORITY: tuple[str, ...] = (
    "agent", "predator", "hiding_predator", "food", "neutral",
)

#: Terrain is the floor. At most one per square, ever (environment rule R1:
#: reset places every non-agent entity on a distinct square).
TERRAIN_NAMES: frozenset[str] = frozenset({"rock", "bush", "tree", "campfire"})

#: Share of the square left showing the ground on every side, so a square's
#: temperature is never completely painted over by its terrain.
BED_MARGIN = 0.14

#: A lone occupant's ink half-extent, as a share of the square.
SOLO_H = 0.30

#: The band a shared square lays its occupants out in, as a share of the square,
#: and the side margin left round that band.
BAND_TWO = 0.60
BAND_MANY = 0.88
SLOT_MARGIN = 0.05
SLOT_FILL = 0.92        # a token fills this much of the slot it was given

#: Each token's one identifying mark, and that mark's SHORT dimension as a share
#: of ``h``. These are constants rather than opinions because they are what makes
#: a minimum square size computable in a test instead of argued about.
MIN_MARK: dict[str, float] = {
    "food": 0.34, "predator": 0.30, "neutral": 0.30, "hiding_predator": 0.32,
    "agent": 0.55,
}
KEY_MARK: dict[str, str] = {
    "food": "green leaf", "predator": "amber eye slit", "neutral": "ear gap",
    "hiding_predator": "amber spike tip", "agent": "white chevron",
}

#: A colour mark must clear this in its short dimension to survive video
#: compression (the round-2 design round's measured heuristic).
MARK_FLOOR_PX = 3.0

#: The chevron inside the agent token, as a share of ``h``, and its own floor.
#: The floor is on the CHEVRON, not on ``h`` (Revision 19, finding 60).
CHEVRON_FRACTION = 0.62
CHEVRON_FLOOR_PX = 6.0

#: Depth, pinned. Strictly increasing, and every arena overlay is below tokens.
GROUND_Z = 1.0
BED_Z = 2.0
OUTLINE_Z = 3.0         # the agent's square outline
FOOTPRINT_Z = 3.5       # a sense's diamond footprint
TOKEN_Z = 5.0

ARROW_VEC = {"UP": (0, -1), "RIGHT": (1, 0), "DOWN": (0, 1), "LEFT": (-1, 0)}
ARROW_TEXT = {"UP": "↑", "RIGHT": "→", "DOWN": "↓", "LEFT": "←"}


class CellLegibilityError(ValueError):
    """A square is too small to draw its occupants legibly.

    Raised instead of drawing a chevron or an identifying mark below its floor.
    """


@dataclass(frozen=True)
class Shape:
    """One filled path of a compound form, with its own colours.

    A bed or a token is a LIST of these, which the painter hands to a single
    Matplotlib artist -- see the module docstring, constraint 1.
    """

    patch: object
    fc: object
    ec: object = "none"
    lw: float = 0.0        # in pixels; converted to points by the painter


@dataclass(frozen=True)
class Slot:
    """Where one occupant is drawn, and how big it is."""

    name: str
    cx: float
    cy: float
    h: float


# --------------------------------------------------------------------------
# Slot geometry -- the arithmetic the plan pins
# --------------------------------------------------------------------------
def by_priority(names) -> list[str]:
    """Occupants in :data:`CELL_PRIORITY` order; an unknown name raises."""
    out = list(names)
    for n in out:
        if n not in CELL_PRIORITY:
            raise KeyError(
                f"entity {n!r} is not in CELL_PRIORITY {CELL_PRIORITY}. Draw order must "
                f"be explicit: an entity that falls back to alphabetical order is the "
                f"overdraw bug this module exists to remove."
            )
    return sorted(out, key=CELL_PRIORITY.index)


def slot_h(n: int, cell: float) -> float:
    """The ink half-extent for ``n`` occupants sharing a square of ``cell`` px.

    At the decided 50 px square this is **15.00 / 10.35 / 10.12 px** for one,
    two, and three-or-four occupants (plan section R18.3).
    """
    if n <= 0:
        raise ValueError("a square with no occupants has no slot")
    if n == 1:
        return SOLO_H * cell
    cols = 2
    rows = 1 if n == 2 else 2
    band = BAND_TWO if n == 2 else BAND_MANY
    w = (cell - 2 * SLOT_MARGIN * cell) / cols
    return min(w, band * cell / rows) / 2 * SLOT_FILL


def slots(names, cx: float, cy: float, cell: float) -> list[Slot]:
    """Lay the non-terrain occupants of one square out in their slots.

    One centred token for one occupant; a row of two; **two rows** from three up,
    with the last row centred so three reads as 2-over-1 rather than as a gap. A
    single row of three was tried in the design round and rejected by
    measurement: it collapses ``h`` to 0.135 x cell and pushes the four-way
    minimum square to 75 px -- an artefact of the layout, not of the idea.
    """
    order = by_priority(names)
    n = len(order)
    if n == 0:
        return []
    h = slot_h(n, cell)
    if n == 1:
        return [Slot(order[0], cx, cy, h)]

    cols = 2
    rows = 1 if n == 2 else 2
    band = (BAND_TWO if n == 2 else BAND_MANY) * cell
    w = (cell - 2 * SLOT_MARGIN * cell) / cols
    bh = band / rows
    top = cy - band / 2
    out: list[Slot] = []
    for r in range(rows):
        chunk = order[r * cols:(r + 1) * cols]
        for c, nm in enumerate(chunk):
            out.append(Slot(nm, cx - len(chunk) * w / 2 + (c + 0.5) * w,
                            top + (r + 0.5) * bh, h))
    return out


def min_cell_for(n: int, name: str) -> float:
    """The smallest square at which ``name``'s identifying mark still survives.

    Recomputed from the mark fraction rather than quoted: the mark's short
    dimension is ``MIN_MARK[name] x h``, ``h`` follows :func:`slot_h`, and the
    mark must clear :data:`MARK_FLOOR_PX`. At the decided constants this returns
    **49 px** for the binding two-occupant cases and **50 px** for the four-way,
    which are the two floors the plan records.
    """
    frac = MIN_MARK[name] * slot_h(n, 1.0)
    return MARK_FLOOR_PX / frac


def min_cell_for_chevron(n: int) -> float:
    """The smallest square at which the agent's chevron is still legible."""
    return CHEVRON_FLOOR_PX / (CHEVRON_FRACTION * slot_h(n, 1.0))


def check_legible(n: int, names, cell: float) -> None:
    """Raise when a square cannot show what it is being asked to show."""
    h = slot_h(n, cell)
    for nm in names:
        if nm == "agent" and CHEVRON_FRACTION * h < CHEVRON_FLOOR_PX - 1e-9:
            raise CellLegibilityError(
                f"the agent's chevron would be {CHEVRON_FRACTION * h:.2f}px in a "
                f"{cell:.0f}px square shared by {n}; the floor is {CHEVRON_FLOOR_PX}px "
                f"({min_cell_for_chevron(n):.1f}px square needed)"
            )
        if nm in MIN_MARK and MIN_MARK[nm] * h < MARK_FLOOR_PX - 1e-9:
            raise CellLegibilityError(
                f"the {nm}'s {KEY_MARK[nm]} would be {MIN_MARK[nm] * h:.2f}px in a "
                f"{cell:.0f}px square shared by {n}; the floor is {MARK_FLOOR_PX}px "
                f"({min_cell_for(n, nm):.1f}px square needed)"
            )


# --------------------------------------------------------------------------
# Token forms (companions)
#
# Each is drawn FOR a small box rather than scaled down into one, and keeps
# exactly one identifying mark at the fraction of `h` recorded in MIN_MARK.
# --------------------------------------------------------------------------
def _keyline(cx, cy, h) -> Shape:
    """The white keyline that separates a token from the bed it stands on.

    Radius is exactly ``h``: the stroke is **inset** so its OUTER edge lies at
    ``h`` (plan section R17.3 item 7, as corrected in Revision 19). A keyline
    centred on ``h`` puts half its width outside, and the keylines of two
    adjacent slots then kiss -- white on white, invisible to the eye, and the
    whole of this design's residual measured "glyph overlap".
    """
    lw = max(0.8, h / 8)
    return Shape(Circle((cx, cy), h - lw / 2), "none", P.WHITE, lw)


def cf_food(cx, cy, h, action=None) -> list[Shape]:
    return [
        _keyline(cx, cy, h),
        Shape(Rectangle((cx - 0.06 * h, cy - 0.92 * h), 0.12 * h, 0.44 * h), P.FOOD_STEM),
        Shape(Circle((cx, cy + 0.12 * h), 0.80 * h), P.FOOD),
        Shape(Ellipse((cx + 0.46 * h, cy - 0.62 * h), 0.86 * h, 0.34 * h, angle=-30),
              P.FOOD_LEAF),
    ]


def cf_predator(cx, cy, h, action=None) -> list[Shape]:
    pts = [(-0.98, -0.92), (-0.44, -0.24), (0.44, -0.24), (0.98, -0.92),
           (0.90, 0.16), (0.34, 0.96), (-0.34, 0.96), (-0.90, 0.16)]
    out = [_keyline(cx, cy, h),
           Shape(Polygon([(cx + a * h, cy + b * h) for a, b in pts], closed=True), P.PRED)]
    for sx in (-1, 1):
        out.append(Shape(Polygon([(cx + sx * 0.60 * h, cy + 0.02 * h),
                                  (cx + sx * 0.16 * h, cy + 0.16 * h),
                                  (cx + sx * 0.50 * h, cy + 0.34 * h)], closed=True),
                         P.HIDE_EYE))
    return out


def cf_neutral(cx, cy, h, action=None) -> list[Shape]:
    """The rabbit. Its identifying mark is the EAR GAP -- two tall, separated
    ears in warm grey -- because the pink ear lining is only ~0.2 h and cannot
    survive a shared square. The lining is painted only where there is room."""
    out = [_keyline(cx, cy, h)]
    for sx in (-1, 1):
        out.append(Shape(Ellipse((cx + sx * 0.40 * h, cy - 0.46 * h), 0.44 * h,
                                 1.22 * h, angle=sx * 8), P.NEUT))
        if h >= 9:
            out.append(Shape(Ellipse((cx + sx * 0.40 * h, cy - 0.50 * h), 0.22 * h,
                                     0.82 * h, angle=sx * 8), P.NEUT_INNER))
    out.append(Shape(Circle((cx, cy + 0.40 * h), 0.66 * h), P.NEUT))
    if h >= 9:
        for sx in (-1, 1):
            out.append(Shape(Circle((cx + sx * 0.26 * h, cy + 0.30 * h), 0.11 * h),
                             P.EYE_DARK))
    return out


def cf_hiding_predator(cx, cy, h, action=None) -> list[Shape]:
    """A thorn cluster, not a lurking animal: the entity never moves and has no
    odour, so the form reads as a static hazard. It keeps the predator's threat
    pair (charcoal body, amber accent) so the two read as siblings."""
    out = [_keyline(cx, cy, h),
           Shape(Ellipse((cx, cy + 0.66 * h), 1.90 * h, 0.52 * h), P.HIDE_BODY)]
    for xo, ht, w in ((-0.58, 0.50, 0.30), (0.0, 0.98, 0.34), (0.58, 0.58, 0.30)):
        ytip, ybase = cy - ht * h, cy + 0.66 * h
        out.append(Shape(Polygon([(cx + xo * h, ytip), (cx + (xo - w) * h, ybase),
                                  (cx + (xo + w) * h, ybase)], closed=True), P.HIDE_BODY))
        t = 0.52
        ycut, wcut = ytip + t * (ybase - ytip), w * t
        out.append(Shape(Polygon([(cx + xo * h, ytip), (cx + (xo - wcut) * h, ycut),
                                  (cx + (xo + wcut) * h, ycut)], closed=True), P.HIDE_EYE))
    return out


def cf_agent(cx, cy, h, action=None, *, shared: bool = True) -> list[Shape]:
    """The agent.

    **The halo is dropped whenever the square is shared** (plan R17.3 item 8). At
    full size the marker carries a 16 % iris halo at 1.32 r; in a shared square
    that halo is ink spilling past ``h`` onto the neighbour, and it was the
    entirety of this variant's measured overlap before it was removed. Concretely
    the halo reaches 0.396 x cell from the centre while a whole bush glyph
    reached only 0.261 x cell -- the halo was wider than the drawing it was
    supposed to sit beside, which is the mechanism behind "agent in a bush
    renders as agent alone".

    The white ring stays at every size, and so does the chevron pointing in the
    last action's direction (a dot for Rest and Eat). Which square the agent is
    in is said by the square's own iris outline, not by the token's size.
    """
    out: list[Shape] = []
    if not shared:
        out.append(Shape(Circle((cx, cy), h * 1.32), (*_rgb(P.IRIS), 0.16)))
        out.append(Shape(Circle((cx, cy + h * 0.07), h * 1.04), (0, 0, 0, 0.12)))
    out.append(Shape(Circle((cx, cy), h), P.IRIS, P.WHITE, max(0.9, h / 8)))
    a = h * CHEVRON_FRACTION
    if action in ARROW_VEC:
        dx, dy = ARROW_VEC[action]
        nx, ny = -dy, dx
        out.append(Shape(Polygon([
            (cx + dx * a, cy + dy * a),
            (cx - dx * a * 0.3 + nx * a * 0.62, cy - dy * a * 0.3 + ny * a * 0.62),
            (cx, cy),
            (cx - dx * a * 0.3 - nx * a * 0.62, cy - dy * a * 0.3 - ny * a * 0.62),
        ], closed=True), P.WHITE))
    else:
        out.append(Shape(Circle((cx, cy), h * 0.30), P.WHITE))
    return out


COMPANION = {
    "food": cf_food, "predator": cf_predator, "neutral": cf_neutral,
    "hiding_predator": cf_hiding_predator, "agent": cf_agent,
}


def token(name: str, cx: float, cy: float, h: float, action=None,
          shared: bool = True) -> list[Shape]:
    """One occupant's drawing, as a list of filled paths for ONE artist."""
    fn = COMPANION[name]
    if name == "agent":
        return fn(cx, cy, h, action, shared=shared)
    return fn(cx, cy, h, action)


# --------------------------------------------------------------------------
# Bed forms
#
# ONE ARTIST EACH, AND FULL-BLEED. The plan's own words are "drawn full-bleed,
# inset by BED_MARGIN on every side" (R17.3 item 2), and the audit classifies a
# bed by measuring that its ink covers >= 40 % of the square (R19.1 step 2). A
# full-bleed inset square is 0.72^2 = 51.8 % of the square, which clears that
# line by construction; the design mock's partial silhouettes (a rock sitting on
# the lower two thirds) cover only ~28-36 % and would be counted as OCCUPANTS by
# the audit -- a false failure on a correct painter. So each bed here is a base
# plate at the inset, with that terrain's own texture drawn on top of it.
# --------------------------------------------------------------------------
def _rgb(c):
    from matplotlib.colors import to_rgb
    return to_rgb(c)


def _plate(cx, cy, s, colour, alpha=None) -> Shape:
    m = BED_MARGIN * s
    side = s - 2 * m
    fc = colour if alpha is None else (*_rgb(colour), alpha)
    return Shape(FancyBboxPatch((cx - side / 2, cy - side / 2), side, side,
                                boxstyle=f"round,pad=0,rounding_size={0.10 * s}"), fc)


def bed_bush(cx, cy, s) -> list[Shape]:
    m = BED_MARGIN * s
    x0, x1 = cx - s / 2 + m, cx + s / 2 - m
    w = x1 - x0
    out = [_plate(cx, cy, s, P.BUSH)]
    for i in range(4):
        fx = x0 + (i + 0.5) * w / 4
        out.append(Shape(Circle((fx, cy - 0.16 * s), w / 7.0 * 1.30),
                         P.BUSH_HI if i % 2 else P.BUSH))
    out.append(Shape(Circle((cx - w * 0.16, cy + 0.02 * s), w / 7.0), P.BUSH_HI))
    out.append(Shape(Circle((cx + w * 0.22, cy + 0.18 * s), w / 8.0), P.BUSH_HI))
    return out


def bed_rock(cx, cy, s) -> list[Shape]:
    m = BED_MARGIN * s
    x0, x1 = cx - s / 2 + m, cx + s / 2 - m
    top, bot = cy - s / 2 + m, cy + s / 2 - m
    w = x1 - x0
    out = [_plate(cx, cy, s, P.ROCK)]
    out.append(Shape(Polygon([(x0 + 0.10 * w, bot), (x0 + 0.22 * w, top + 0.34 * w),
                              (x0 + 0.52 * w, top + 0.10 * w), (x1 - 0.10 * w, top + 0.40 * w),
                              (x1 - 0.06 * w, bot)], closed=True), P.ROCK_HI))
    out.append(Shape(Polygon([(x0 + 0.22 * w, top + 0.34 * w), (x0 + 0.52 * w, top + 0.10 * w),
                              (x0 + 0.60 * w, top + 0.44 * w), (x0 + 0.26 * w, top + 0.58 * w)],
                             closed=True), P.ROCK))
    return out


def bed_tree(cx, cy, s) -> list[Shape]:
    m = BED_MARGIN * s
    x0, x1 = cx - s / 2 + m, cx + s / 2 - m
    top, bot = cy - s / 2 + m, cy + s / 2 - m
    w = x1 - x0
    out = [_plate(cx, cy, s, P.TREE)]
    out.append(Shape(Rectangle((cx - 0.055 * s, cy + 0.06 * s), 0.11 * s, bot - cy - 0.06 * s),
                     P.TRUNK))
    out.append(Shape(Circle((cx - w * 0.18, top + 0.30 * w), 0.16 * w), P.TREE_HI))
    out.append(Shape(Circle((cx + w * 0.20, top + 0.22 * w), 0.12 * w), P.TREE_HI))
    return out


def bed_campfire(cx, cy, s) -> list[Shape]:
    m = BED_MARGIN * s
    x0, x1 = cx - s / 2 + m, cx + s / 2 - m
    bot = cy + s / 2 - m
    w = x1 - x0
    out = [_plate(cx, cy, s, P.GLOW, alpha=0.42)]
    for xo, col in ((-0.06, P.LOG_BACK), (0.06, P.LOG_FRONT)):
        e = Ellipse((cx + xo * s, bot - s * 0.08), w * 0.92, s * 0.12, angle=xo * 260)
        out.append(Shape(e, col))
    out.append(Shape(Ellipse((cx, bot - s * 0.24), s * 0.32, s * 0.44), P.FIRE_OUT))
    out.append(Shape(Ellipse((cx, bot - s * 0.22), s * 0.18, s * 0.28), P.FIRE_MID))
    out.append(Shape(Ellipse((cx, bot - s * 0.20), s * 0.09, s * 0.16), P.FIRE_CORE))
    return out


BED = {"bush": bed_bush, "rock": bed_rock, "tree": bed_tree, "campfire": bed_campfire}


def bed(name: str, cx: float, cy: float, cell: float) -> list[Shape]:
    """The terrain floor of one square, as a list of paths for ONE artist."""
    return BED[name](cx, cy, cell)


# --------------------------------------------------------------------------
# The composition of one square
# --------------------------------------------------------------------------
def compose(occupants, cx: float, cy: float, cell: float, action=None):
    """Turn "who is in this square" into what to draw, before anything is drawn.

    Returns ``(bed_name_or_None, [(name, [Shape, ...]), ...])``. Slots are
    computed first and the drawing follows them: the painter never draws
    concentrically and then relies on z-order to sort it out, which is the
    defect this module replaces.
    """
    names = list(occupants)
    terrain = [n for n in names if n in TERRAIN_NAMES]
    if len(terrain) > 1:
        raise ValueError(
            f"square at ({cx:.0f},{cy:.0f}) has two terrains {terrain}; the environment "
            f"places at most one per square (reset resolves overlaps), so the bed layer "
            f"never has to compose two"
        )
    rest = [n for n in names if n not in TERRAIN_NAMES]
    n = len(rest)
    if n:
        check_legible(n, rest, cell)
    # THE HALO IS DROPPED WHENEVER THE SQUARE HAS ANYTHING ELSE IN IT -- another
    # occupant OR a bed. The plan (R17.3 item 8) says "n >= 2", which is right
    # for occupant-on-occupant and WRONG for the archetype the variant was
    # chosen for. Measured: a lone agent's halo reaches 0.396 x cell from the
    # centre while the bed spans 0.72 x cell, i.e. 0.36 x cell from the centre --
    # so the halo is wider than the entire floor beneath it and "agent in a bush"
    # renders as an agent alone, which is the defect, not the fix. On a genuinely
    # empty square the halo covers only bare ground and is kept, because there it
    # costs nothing and makes the agent easy to find.
    shared = n >= 2 or bool(terrain)
    out = []
    for sl in slots(rest, cx, cy, cell):
        out.append((sl.name, token(sl.name, sl.cx, sl.cy, sl.h, action=action,
                                   shared=shared)))
    return (terrain[0] if terrain else None), out


def bed_plate_fraction(cell: float = 50.0) -> float:
    """The share of a square a bed's base plate covers, ignoring its texture.

    Every bed is built on the same full-bleed plate, so this number does not
    depend on which terrain it is. The audit's floor-versus-occupant split is a
    >= 40 % area test, so this is what decides whether a bed is classified as
    the floor, and it is a LOWER bound: the texture drawn on top of the plate
    can only add ink, never remove it.
    """
    side = cell - 2 * BED_MARGIN * cell
    return float(side * side) / float(cell * cell)
