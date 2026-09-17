"""One square of the world: who is standing on it, and how they are drawn.

PLAIN-LANGUAGE SUMMARY. A square of the world can hold more than one thing at
once -- the agent standing in a bush, a predator and a rabbit in the same square,
food lying on a rock. The old renderer drew every occupant on the *same centre
point*, so two drawings landed on top of each other and whichever name sorted
later in the alphabet won: an agent standing in a bush rendered as an agent
alone. This module is where that is fixed, and since 2026-09-17 it is fixed the
way the approved design draws it (plan Revision 27):

    **One occupant is a centred glyph. Two or more stand side by side.**

A square holding ONE thing -- a rock, a campfire, an apple, the agent -- is drawn
exactly as the approved mock draws it: the entity's own artwork, centred, at that
entity's own size. That is the overwhelmingly common case and it is pixel-for-
pixel the design the user chose. Only when a square holds two or more does the
composition depart from the mock, and then it departs in the one direction that
cannot lose information: the occupants are laid out in disjoint slots -- two side
by side, three or four in quadrants -- so every one of them is visible. At the
arena's 96 px square (a 5-wide window) a slot is 45 px across, which is larger
than the whole square was in some earlier drafts.

WHAT THIS REPLACES, AND WHY. Between 2026-09-16 and today terrain was drawn as
"variant H": a full-bleed FLOOR filling the square, with the movers standing on
top of it. That solved the same overdraw problem and the user has since said it
is not what they want -- the approved mock draws a rock as a rock, centred, not
as a carpet. Variant H is therefore withdrawn together with its bed forms, its
``BED_MARGIN``, and the audit's floor-versus-occupant area split. Terrain is now
an occupant like any other: it takes a slot when the square is shared, and it is
counted by the pixel audit as a thing that must be visible.

THE ARTWORK IS THE USER'S OWN. All NINE entities are the PNGs the user chose by
hand from the icon contact sheets -- ``assets/dashboard_icons/*.png``: the rose
apple with its green leaf, the charcoal thorn cluster, the grey rabbit with the
pink inner ear, and the four terrain glyphs (rock, bush, tree, campfire) that
variant H had stopped reading. Nothing in a world square is drawn in code any
more.

ASPECT RATIO IS PRESERVED, AND THAT IS NOT A DETAIL. The four terrain masters are
not square -- measured on their own alpha bounding boxes, rock is 1.52 wide for 1
tall, the tree 0.72 -- so mapping a master into a square box would draw a
squashed rock and a stretched tree. Each token is fitted INSIDE its slot's box at
its own aspect instead.

VOCABULARY, fixed here so painter, test and audit use one set of words:
**ground** = the square's own fill (its temperature colour, or the neutral track
when the world has no temperature); **token** = one occupant's drawing; **slot** =
the box a token is drawn for; **h** = a token's ink half-extent in pixels, the one
number that decides legibility.
"""

from __future__ import annotations

import functools
import os
from dataclasses import dataclass

from matplotlib.patches import Circle, Ellipse, FancyBboxPatch, Polygon, Rectangle

from . import palette as P

#: The user's chosen artwork. One 1000 px RGBA master per entity.
ICON_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "assets", "dashboard_icons"))

# --------------------------------------------------------------------------
# The rule's constants
# --------------------------------------------------------------------------

#: Terrain. At most one per square, ever (environment rule R1: reset places every
#: non-agent entity on a distinct square).
TERRAIN_NAMES: frozenset[str] = frozenset({"rock", "bush", "tree", "campfire"})

#: Draw order, explicit and never alphabetical. The observed overdraw bug is
#: exactly what a ``sorted()`` over entity names buys. Slots are filled left to
#: right, then top to bottom, in this order.
#:
#: TERRAIN COMES LAST, and that is the ordering decision the ceiling rests on: a
#: square can show four things, so when a fifth would be needed the one dropped
#: is the one that moves least and matters least to a viewer watching an animal
#: being chased. The agent is first and is never the one dropped.
CELL_PRIORITY: tuple[str, ...] = (
    "agent", "predator", "hiding_predator", "food", "neutral",
    "rock", "bush", "tree", "campfire",
)

#: How many occupants one square can show. Four slots, four occupants.
MAX_SLOTS = 4

#: A LONE occupant's ink half-extent, as a share of the square. These are the
#: approved sketch's own glyph sizes, measured off its drawing code
#: (``renderer_layout_redesign/dashboard_style.py``) rather than re-chosen:
#:
#:   * a mover's white token disc is ``0.34 * s``          (``ds.token``)
#:   * the agent's outer halo is ``1.32 * 0.30 * s`` = 0.396  (``ds.agent_marker``)
#:   * a terrain glyph spans ``0.26..0.285 * s`` depending on which one it is
#:     (bush 0.261, rock 0.270, campfire 0.285), so terrain takes the middle of
#:     that range and each glyph keeps its own aspect inside it.
#:
#: The agent is bigger than a mover because its halo is ink that reaches past the
#: disc, and the mock draws it that way.
SOLO_FRAC: dict[str, float] = {
    "agent": 0.396,
    "food": 0.34, "predator": 0.34, "hiding_predator": 0.34, "neutral": 0.34,
    "rock": 0.27, "bush": 0.27, "tree": 0.27, "campfire": 0.27,
}

#: A SHARED square's slot: every occupant gets a quarter of the square (two
#: occupants take the left and right halves, three or four take quadrants), and
#: the token fills that quarter with a small margin so two neighbours cannot
#: touch. ``0.235`` is ``0.25 * 0.94``: the slot's own half-width, minus 6 %.
#:
#: MEASURED CONSEQUENCE, since this is the number that decides how wide a window
#: can be: adjacent slot centres are ``cell / 2`` apart and a token is
#: ``0.47 * cell`` wide, so two neighbours are separated by ``0.03 * cell``
#: whatever the square size -- 2.9 px at a 5-wide window, 1.4 px at a 10-wide
#: one. The floor this hits first is :data:`RASTER_MIN_DIAMETER_PX`.
SHARED_FRAC = 0.235

#: Each token's one identifying mark, and that mark's SHORT dimension as a share
#: of ``h``, for the VECTOR forms at the bottom of this module. Kept because it
#: is what :func:`min_cell_for` computes from, and because the vector forms are
#: the artwork's provenance.
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
#:
#: UNCHANGED, DELIBERATELY. It is swept on, and still enforced for, the VECTOR
#: forms below. The raster movers are judged by the pair beneath it instead --
#: see :func:`check_legible`, which applies whichever rule matches how the token
#: is actually drawn rather than applying both to everything.
MARK_FLOOR_PX = 3.0

#: The raster substitution, and the two numbers that replace the mark floor for
#: an artwork token. See the 2026-09-17 Implementation Report (§R26.1): the
#: per-mark 3 px floor is unachievable at SHARED size for any square this
#: renderer draws and the chosen artwork misses it even SOLO, so the gate is the
#: pair the design round's own 4:2:0 + JPEG q42 compression test validated -- a
#: token big enough to carry a silhouette, and enough surviving body colour to
#: tell one from another.
#:
#: THESE TWO ARE NOW WHAT LIMITS THE WINDOW. With a fixed 480 px arena the square
#: shrinks as the window widens, so the diameter floor is what says how far out
#: the view may zoom: ``2 * SHARED_FRAC * cell >= 20`` puts the smallest square
#: at 42.6 px and the widest window at 11 x 11. ``layout.ARENA_CELL_MIN_PX``
#: restates that and a test re-derives it from here.
RASTER_MIN_DIAMETER_PX = 20.0
RASTER_MIN_BODY_AREA_PX2 = 40.0

#: The white token disc's radius in every MOVER master, as a fraction of the
#: 1000 px canvas -- measured, and identical across all four non-agent masters
#: (alpha bbox 0.153..0.847). It converts a mark measured on the master into a
#: fraction of ``h``.
TOKEN_DISC_FRAC = 0.347

#: Each mover's identifying mark and the palette colour it is painted in, so the
#: mark can be found in the asset rather than described in prose.
RASTER_MARK_COLOUR: dict[str, str] = {
    "food": P.FOOD_LEAF,
    "predator": P.HIDE_EYE,
    "neutral": P.NEUT_INNER,
    "hiding_predator": P.HIDE_EYE,
}

#: Each entity's BODY colour -- the large flat field that carries its silhouette.
#: This, not the mark, is what :func:`check_legible` gates on at shared size.
#:
#: THE FOUR TERRAIN GLYPHS ARE IN THIS TABLE SINCE 2026-09-17, and that is a
#: strengthening rather than bookkeeping: under variant H a bed was "the floor"
#: and had no legibility gate at all, so nothing measured whether a rock stayed a
#: rock. Terrain is an occupant now, so it answers to the same floor as everyone
#: else.
RASTER_BODY_COLOUR: dict[str, str] = {
    "food": P.FOOD,
    "predator": P.PRED,
    "neutral": P.NEUT,
    "hiding_predator": P.HIDE_BODY,
    "agent": P.IRIS,
    "rock": P.ROCK,
    "bush": P.BUSH,
    "tree": P.TREE,
    "campfire": P.LOG_BACK,
}

#: The frozen measurement: each mover's mark's SHORT DIMENSION on its own master,
#: as a fraction of ``h``. Frozen so the arithmetic is readable without opening a
#: PNG, and RE-MEASURED from the PNG by ``test_dashboard_cells.py`` so swapping in
#: weaker artwork fails rather than silently shipping.
RASTER_MARK: dict[str, float] = {
    "food": 0.245,
    "hiding_predator": 0.144,
    "neutral": 0.135,
    "predator": 0.127,
}

#: The chevron inside the agent token, as a share of ``h``, and its own floor.
#: The floor is on the CHEVRON, not on ``h`` (Revision 19, finding 60).
CHEVRON_FRACTION = 0.62
CHEVRON_FLOOR_PX = 6.0

#: Depth, pinned. Strictly increasing, and every arena overlay is below tokens.
GROUND_Z = 1.0
OUTLINE_Z = 3.0         # an overlay on a square (no longer drawn by the arena)
FOOTPRINT_Z = 3.5       # a sense's diamond footprint
TOKEN_Z = 5.0

ARROW_VEC = {"UP": (0, -1), "RIGHT": (1, 0), "DOWN": (0, 1), "LEFT": (-1, 0)}
ARROW_TEXT = {"UP": "↑", "RIGHT": "→", "DOWN": "↓", "LEFT": "←"}


class CellLegibilityError(ValueError):
    """A square is too small to draw its occupants legibly.

    Raised instead of drawing a token below its measured floor.
    """


@dataclass(frozen=True)
class Shape:
    """One filled path of a compound form, with its own colours.

    The VECTOR forms at the bottom of this module are lists of these. They are no
    longer the drawing path -- the artwork is -- but they are kept because they
    are the artwork's provenance and because the icon contact sheet draws them.
    """

    patch: object
    fc: object
    ec: object = "none"
    lw: float = 0.0        # in pixels; converted to points by the painter


@dataclass(frozen=True)
class Raster:
    """One occupant drawn as the user's own artwork, in its own image artist.

    ``hw`` / ``hh`` are the token's half-width and half-height in pixels: the
    master's own aspect ratio, fitted inside the slot's ``2h`` box. ``px_w`` /
    ``px_h`` are the INTEGER pixel size the master is resampled to, once, at build
    time -- Matplotlib's on-the-fly resampling is mushy at 20 px, so the image
    handed to the canvas is already exactly the size it will occupy and is drawn
    with ``interpolation="none"``.
    """

    name: str
    cx: float
    cy: float
    hw: float
    hh: float
    px_w: int
    px_h: int
    action: str | None = None

    @property
    def extent(self):
        """``(left, right, bottom, top)`` in the arena's y-DOWN pixel space."""
        return (self.cx - self.hw, self.cx + self.hw,
                self.cy + self.hh, self.cy - self.hh)


@dataclass(frozen=True)
class Slot:
    """Where one occupant is drawn, and how big it is."""

    name: str
    cx: float
    cy: float
    h: float


# --------------------------------------------------------------------------
# The artwork: loading it, and measuring it
# --------------------------------------------------------------------------
@functools.lru_cache(maxsize=None)
def _master(name: str):
    """One icon master as an RGBA float array, cropped to its own ink.

    Cropping to the ALPHA BOUNDING BOX is what makes every token the size it was
    asked for: the masters pad their glyphs differently (the agent's halo reaches
    0.104..0.896 of its canvas, a mover's token disc 0.153..0.847, the rock only
    0.245..0.769 across and 0.320..0.664 down), so mapping the canvas would draw
    the agent smaller than the rabbit beside it and leave the rock floating in
    empty pixels.
    """
    import numpy as np
    from PIL import Image

    path = os.path.join(ICON_DIR, f"{name}.png")
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"no artwork for {name!r} at {path}. Every entity in a world square is "
            f"drawn from the user's chosen icon set; this package does not fall back "
            f"to a vector imitation of it, because a frame drawn in the wrong forms "
            f"is the defect this restoration removed."
        )
    im = np.asarray(Image.open(path).convert("RGBA"))
    ys, xs = np.nonzero(im[..., 3] > 8)
    return im[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


@functools.lru_cache(maxsize=None)
def master_aspect(name: str) -> float:
    """The master's own width / height, measured on its alpha bounding box.

    Measured, not declared: the terrain glyphs are visibly non-square (rock 1.52,
    bush 1.27, tree 0.72, campfire 1.00) and drawing them into a square box is
    the difference between a rock and a squashed rock.
    """
    m = _master(name)
    return float(m.shape[1]) / float(m.shape[0])


def fit_box(name: str, h: float) -> tuple[float, float]:
    """``(half_width, half_height)`` for ``name`` drawn inside a ``2h`` box.

    The token keeps its own proportions and touches the box on its longer axis,
    so ``h`` is always the token's larger half-extent.
    """
    ar = master_aspect(name)
    return (h, h / ar) if ar >= 1.0 else (h * ar, h)


@functools.lru_cache(maxsize=None)
def icon_array(name: str, px_w: int, px_h: int, action: str | None = None):
    """The artwork for ``name``, resampled ONCE to ``px_w`` x ``px_h``.

    Lanczos, because this is a downsample of roughly 15:1 to 50:1 and the marks
    that carry identity are two pixels wide at the far end of it.

    THE AGENT'S CHEVRON IS COMPOSITED IN HERE, NOT DRAWN OVER THE TOP, and the
    reason is the audit rather than tidiness. The co-occupancy rule forbids two of
    a square's occupant artists from sharing a single pixel -- that is how it
    catches one token painted over another -- so a chevron in its own patch
    artist, lying by construction on top of the agent's own disc, would report
    every agent in every frame as an occupant drawn over an occupant. One token is
    one artist; the chevron therefore goes into the token's own pixels.

    It is supersampled 4x and box-filtered down, so the diagonal edges stay smooth
    at the sizes this actually draws at.
    """
    import numpy as np
    from PIL import Image, ImageDraw

    if px_w < 1 or px_h < 1:
        raise ValueError(f"{name}: an icon cannot be drawn at {px_w}x{px_h}px")
    if action is not None and name != "agent":
        raise ValueError(
            f"{name!r} has no action mark; only the agent carries one "
            f"(asked for {action!r})"
        )
    ss = 4
    src = Image.fromarray(_master(name)).resize((int(px_w) * ss, int(px_h) * ss),
                                                Image.LANCZOS)
    if name == "agent":
        bw, bh = int(px_w) * ss, int(px_h) * ss
        cxx, cyy = bw / 2.0, bh / 2.0
        a = (min(bw, bh) / 2.0) * CHEVRON_FRACTION
        layer = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
        pen = ImageDraw.Draw(layer)
        if action in ARROW_VEC:
            dx, dy = ARROW_VEC[action]
            nx, ny = -dy, dx
            pen.polygon([
                (cxx + dx * a, cyy + dy * a),
                (cxx - dx * a * 0.3 + nx * a * 0.62, cyy - dy * a * 0.3 + ny * a * 0.62),
                (cxx, cyy),
                (cxx - dx * a * 0.3 - nx * a * 0.62, cyy - dy * a * 0.3 - ny * a * 0.62),
            ], fill=(255, 255, 255, 255))
        else:
            r = (min(bw, bh) / 2.0) * 0.30
            pen.ellipse([cxx - r, cyy - r, cxx + r, cyy + r], fill=(255, 255, 255, 255))
        src = Image.alpha_composite(src, layer)
    return np.asarray(src.resize((int(px_w), int(px_h)), Image.BOX),
                      dtype=float) / 255.0


def measure_raster_mark(name: str) -> float:
    """This icon's identifying mark, as a fraction of ``h``, FROM THE PNG.

    The mark is found by colour -- the palette hex it is painted in -- and taken
    as the largest connected run of it; its SHORT dimension is the number that
    matters, because that is the dimension chroma subsampling eats first. The
    result is divided by the token disc's own radius on the master, so it is
    directly comparable with the vector :data:`MIN_MARK` fractions.

    This is the function the test runs against :data:`RASTER_MARK`, so that
    swapping in weaker artwork fails rather than shipping.
    """
    import numpy as np
    from matplotlib.colors import to_rgb
    from scipy import ndimage

    if name not in RASTER_MARK_COLOUR:
        raise KeyError(
            f"{name!r} has no identifying mark registered; known movers with one "
            f"are {sorted(RASTER_MARK_COLOUR)} (the agent's mark is the vector "
            f"chevron, which is drawn rather than read from artwork)"
        )
    im = _master(name).astype(int)
    want = np.asarray([round(v * 255) for v in to_rgb(RASTER_MARK_COLOUR[name])])
    hit = (np.abs(im[..., :3] - want).max(2) <= 24) & (im[..., 3] > 200)
    lab, n = ndimage.label(hit, structure=np.ones((3, 3), dtype=int))
    if n == 0:
        raise ValueError(
            f"{name}: no pixel of its mark colour {RASTER_MARK_COLOUR[name]} is "
            f"in the artwork, so the icon carries no identifying mark at all"
        )
    sizes = ndimage.sum(hit, lab, range(1, n + 1))
    comp = lab == int(np.argmax(sizes)) + 1
    ys, xs = np.nonzero(comp)
    short = min(xs.max() - xs.min() + 1, ys.max() - ys.min() + 1)
    # The master is cropped to the token's own alpha bbox, whose half-width IS
    # the token disc's radius, so the mark's share of that half-width is its
    # share of `h`.
    return float(short) / (im.shape[1] / 2.0)


@functools.lru_cache(maxsize=None)
def _colour_share(name: str, colour: str) -> float:
    """Share of this master's pixels painted in ``colour``. Measured ONCE.

    THE CACHE IS LOAD-BEARING, not tidiness. This scans a ~700 x 700 RGBA master
    with numpy, and :func:`check_legible` asks for it on every occupied square of
    every frame. Uncached it measured **2.08 s of every 3.62 s** of a five-frame
    render -- 57 % of the renderer's time spent re-measuring an asset that cannot
    change while the process lives.
    """
    import numpy as np
    from matplotlib.colors import to_rgb

    im = _master(name).astype(int)
    want = np.asarray([round(v * 255) for v in to_rgb(colour)])
    hit = (np.abs(im[..., :3] - want).max(2) <= 24) & (im[..., 3] > 200)
    return float(hit.sum()) / float(im.shape[0] * im.shape[1])


def _colour_area_px2(name: str, colour: str, h: float) -> float:
    """How much of ``colour`` this artwork carries at half-extent ``h``, in px^2.

    The share is a property of the artwork; only the multiplication by the
    token's drawn size depends on the frame. The drawn area is the token's own
    fitted box, so a non-square glyph is not credited with area it never covers.
    """
    hw, hh = fit_box(name, h)
    return _colour_share(name, colour) * (2.0 * hw) * (2.0 * hh)


def raster_body_area_px2(name: str, h: float) -> float:
    """How much of a token's OWN colour survives at half-extent ``h``, in px^2.

    THE UNION OF A TOKEN'S OWN PARTS, which is this project's existing rule and
    not a convenience adopted here. A mark drawn in two paints reads as partly
    missing if only one of them is counted: ``palette.MINIMAP_MARK_COLOURS``
    already defines the hiding predator's mark as its charcoal body PLUS the
    amber accent that tells it from an ordinary predator, and the pixel audit
    counts a token's own eye towards its own body for the same reason (plan
    sections R19.1 step 5 and R22.1).
    """
    colours = {RASTER_BODY_COLOUR[name]}
    if name in RASTER_MARK_COLOUR:
        colours.add(RASTER_MARK_COLOUR[name])
    return sum(_colour_area_px2(name, c, h) for c in sorted(colours))


def raster_mark_area_px2(name: str, h: float) -> float:
    """The identifying mark's painted AREA at half-extent ``h``, in px^2.

    Reported rather than gated on -- see :func:`check_legible`.
    """
    return _colour_area_px2(name, RASTER_MARK_COLOUR[name], h)


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


def solo_h(name: str, cell: float) -> float:
    """The ink half-extent of a LONE occupant -- the approved mock's own size."""
    if name not in SOLO_FRAC:
        raise KeyError(f"no solo size for {name!r}; known entities are {sorted(SOLO_FRAC)}")
    return SOLO_FRAC[name] * cell


def shared_h(cell: float) -> float:
    """The ink half-extent of one occupant of a SHARED square."""
    return SHARED_FRAC * cell


def slot_h(n: int, cell: float, name: str = "food") -> float:
    """The ink half-extent for ``n`` occupants sharing a square of ``cell`` px.

    ``name`` is consulted only for ``n == 1``, where the size is the entity's own
    (a terrain glyph is drawn smaller than a mover's token disc, exactly as the
    mock draws it).
    """
    if n <= 0:
        raise ValueError("a square with no occupants has no slot")
    return solo_h(name, cell) if n == 1 else shared_h(cell)


def slots(names, cx: float, cy: float, cell: float) -> list[Slot]:
    """Lay the occupants of one square out in their slots.

    One centred token for one occupant; the left and right halves for two;
    quadrants for three or four, with the third centred on the bottom row so
    three reads as 2-over-1 rather than as a gap.
    """
    order = by_priority(names)[:MAX_SLOTS]
    n = len(order)
    if n == 0:
        return []
    if n == 1:
        return [Slot(order[0], cx, cy, solo_h(order[0], cell))]

    h = shared_h(cell)
    q = cell / 4.0
    if n == 2:
        centres = [(cx - q, cy), (cx + q, cy)]
    elif n == 3:
        centres = [(cx - q, cy - q), (cx + q, cy - q), (cx, cy + q)]
    else:
        centres = [(cx - q, cy - q), (cx + q, cy - q),
                   (cx - q, cy + q), (cx + q, cy + q)]
    return [Slot(nm, x, y, h) for nm, (x, y) in zip(order, centres)]


def min_cell_for(n: int, name: str) -> float:
    """The smallest square at which ``name``'s VECTOR mark still survives.

    Recomputed from the mark fraction rather than quoted. It describes the vector
    forms at the bottom of this module, which are the artwork's provenance and
    not the drawing path -- the shipped gate is :func:`check_legible`.
    """
    frac = MIN_MARK[name] * (SOLO_FRAC[name] if n == 1 else SHARED_FRAC)
    return MARK_FLOOR_PX / frac


def min_cell_for_chevron(n: int) -> float:
    """The smallest square at which the agent's chevron is still legible."""
    frac = SOLO_FRAC["agent"] if n == 1 else SHARED_FRAC
    return CHEVRON_FLOOR_PX / (CHEVRON_FRACTION * frac)


def min_cell_legible() -> float:
    """The smallest square at which a SHARED square can be drawn at all.

    The binding floor across every gate in :func:`check_legible`, computed rather
    than quoted, because it is what decides how wide a window the renderer will
    accept. ``layout.ARENA_CELL_MIN_PX`` restates it and a test pins the two
    together.
    """
    need = [RASTER_MIN_DIAMETER_PX / (2.0 * SHARED_FRAC),
            min_cell_for_chevron(2)]
    for name in RASTER_BODY_COLOUR:
        # area scales with h^2, so the cell that puts it exactly on the floor is
        # found from one measurement at a reference size.
        ref = 10.0
        area = raster_body_area_px2(name, ref)
        need.append(ref * (RASTER_MIN_BODY_AREA_PX2 / area) ** 0.5 / SHARED_FRAC)
    return max(need)


def check_legible(n: int, names, cell: float) -> None:
    """Raise when a square cannot show what it is being asked to show.

    Every entity is ARTWORK, so all of them are judged by the pair the
    compression test validated -- the token's size, and how much of its own body
    colour survives -- rather than by :data:`MARK_FLOOR_PX`, which measures a
    property of the vector imitations and is applied to them in
    :func:`min_cell_for`.

    The diameter is measured on the token's LONGER axis, which is the size the
    slot actually asked for; a terrain glyph is legitimately thinner than that on
    its other axis (a rock is 1.5 times as wide as it is tall) and gating on its
    short side would reject artwork that is drawn exactly as designed. What
    protects the short side is the body-colour area below, which is measured on
    the token's real drawn box.

    The agent's chevron is still vector, so it still answers to its own floor.
    """
    for nm in names:
        h = slot_h(n, cell, nm)
        if nm == "agent" and CHEVRON_FRACTION * h < CHEVRON_FLOOR_PX - 1e-9:
            raise CellLegibilityError(
                f"the agent's chevron would be {CHEVRON_FRACTION * h:.2f}px in a "
                f"{cell:.0f}px square shared by {n}; the floor is {CHEVRON_FLOOR_PX}px "
                f"({min_cell_for_chevron(n):.1f}px square needed)"
            )
        if 2.0 * h < RASTER_MIN_DIAMETER_PX - 1e-9:
            raise CellLegibilityError(
                f"the {nm} token would be {2 * h:.2f}px across in a {cell:.1f}px "
                f"square shared by {n}; the floor is {RASTER_MIN_DIAMETER_PX}px, "
                f"below which the artwork's silhouette stops being separable under "
                f"the video path's chroma subsampling. The arena is a fixed box, so "
                f"this is a window that has been zoomed too far out: lower "
                f"visualization.local_view_size."
            )
        if nm in RASTER_BODY_COLOUR:
            area = raster_body_area_px2(nm, h)
            if area < RASTER_MIN_BODY_AREA_PX2 - 1e-9:
                raise CellLegibilityError(
                    f"the {nm} would keep {area:.1f}px² of its own body colour in a "
                    f"{cell:.1f}px square shared by {n}; the floor is "
                    f"{RASTER_MIN_BODY_AREA_PX2}px², below which the silhouette that "
                    f"carries its identity at this size stops being separable"
                )


def token(name: str, cx: float, cy: float, h: float, action=None,
          shared: bool = True) -> list:
    """One occupant's drawing: its artwork, as ONE image, fitted to its slot.

    ``shared`` is accepted and ignored: the vector agent needed its halo dropped
    on a shared square because the halo reached 1.32 x h, wider than anything
    beneath it. ``agent.png`` carries its halo INSIDE its own alpha bbox, which is
    mapped to exactly the slot's box, so no part of the artwork can reach a
    neighbour and there is nothing to drop.
    """
    if name not in SOLO_FRAC:
        raise KeyError(f"no artwork for {name!r}; known entities are {sorted(SOLO_FRAC)}")
    hw, hh = fit_box(name, h)
    return [Raster(name, cx, cy, hw, hh,
                   max(1, int(round(2 * hw))), max(1, int(round(2 * hh))),
                   action if name == "agent" else None)]


# --------------------------------------------------------------------------
# The composition of one square
# --------------------------------------------------------------------------
def compose(occupants, cx: float, cy: float, cell: float, action=None):
    """Turn "who is in this square" into what to draw, before anything is drawn.

    Returns ``[(name, [Raster]), ...]``. Slots are computed first and the drawing
    follows them: the painter never draws concentrically and then relies on
    z-order to sort it out, which is the defect this module replaces.

    A square with ONE occupant returns that occupant centred at its own size,
    which is the approved mock's own picture; only two or more depart from it.
    """
    names = list(occupants)
    terrain = [n for n in names if n in TERRAIN_NAMES]
    if len(terrain) > 1:
        raise ValueError(
            f"square at ({cx:.0f},{cy:.0f}) has two terrains {terrain}; the environment "
            f"places at most one per square (reset resolves overlaps), so a square never "
            f"has to compose two"
        )
    order = by_priority(names)[:MAX_SLOTS]
    if order:
        check_legible(len(order), order, cell)
    return [(sl.name, token(sl.name, sl.cx, sl.cy, sl.h, action=action,
                            shared=len(order) > 1))
            for sl in slots(names, cx, cy, cell)]


# --------------------------------------------------------------------------
# What a READER calls each of these
# --------------------------------------------------------------------------
DISPLAY_NAME: dict[str, str] = {
    "agent": "agent",
    "predator": "predator",
    "hiding_predator": "hiding predator",
    "food": "food",
    "neutral": "rabbit",
    "rock": "rock",
    "bush": "bush",
    "tree": "tree",
    "campfire": "campfire",
}

# Asserted at import, not trusted: an entity the renderer can draw but cannot
# NAME would reach a page as a bare token, which is the defect this table was
# added to remove.
if set(DISPLAY_NAME) != set(SOLO_FRAC):
    raise RuntimeError(
        f"DISPLAY_NAME does not cover the entities this module draws: missing "
        f"{sorted(set(SOLO_FRAC) - set(DISPLAY_NAME))}, "
        f"unknown {sorted(set(DISPLAY_NAME) - set(SOLO_FRAC))}"
    )
if set(CELL_PRIORITY) != set(SOLO_FRAC):
    raise RuntimeError(
        f"CELL_PRIORITY and SOLO_FRAC disagree about which entities exist: "
        f"{sorted(set(CELL_PRIORITY) ^ set(SOLO_FRAC))}"
    )


def display(name: str) -> str:
    """The name a reader sees for one occupant.

    Raises rather than falling back to the token: a silently passed-through
    ``neutral`` on a page is the failure this function exists to make loud.
    """
    if name not in DISPLAY_NAME:
        raise KeyError(
            f"no reader's name for {name!r}; known tokens are {sorted(DISPLAY_NAME)}"
        )
    return DISPLAY_NAME[name]


# --------------------------------------------------------------------------
# The VECTOR forms
#
# As of 2026-09-17 these are the artwork's PROVENANCE rather than the drawing
# path: the PNGs in `assets/dashboard_icons/` were generated from these functions
# and then chosen, by eye, from contact sheets. `token()` draws the PNGs. They are
# kept because the icon contact sheet draws them and because `MIN_MARK` (which
# `min_cell_for` computes from) describes them.
# --------------------------------------------------------------------------
def _rgb(c):
    from matplotlib.colors import to_rgb
    return to_rgb(c)


def _keyline(cx, cy, h) -> Shape:
    """The white keyline that separates a token from what it stands on."""
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
    """The rabbit."""
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
    """A thorn cluster, not a lurking animal."""
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
    """The agent: iris disc, white ring, halo, and one mark per last action."""
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
