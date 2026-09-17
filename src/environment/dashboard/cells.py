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

THE MOVERS ARE THE USER'S OWN ARTWORK (2026-09-17). Each of the five occupant
tokens is the PNG the user personally chose from the icon contact sheets --
``assets/dashboard_icons/*.png``, the rose apple with its green leaf, the
charcoal thorn cluster, the grey rabbit with the pink inner ear -- drawn as one
pre-resized image per slot. **The terrain beds stay vector**, because the terrain
PNGs are centred glyphs from before variant H and cannot serve as the full-bleed
floors this module draws.

This reverses the claim that stood here until today, and the reversal is the
point rather than an exception: "a raster icon cannot supply ``MIN_MARK x h``,
so a raster icon cannot be checked" is false. A mark is measured ONCE from the
asset and frozen, exactly as the vector fractions were frozen -- see
:data:`RASTER_MARK` and :func:`measure_raster_mark` -- and the test re-measures
it FROM THE PNG, so replacing an asset with weaker artwork fails the suite. That
is a stronger guard than a typed constant, because a typed constant cannot
notice that the file under it changed.

WHAT THE MEASUREMENT THEN SAID, WHICH IS NOT WHAT THE VECTOR FORMS SAID. The
chosen artwork draws its identifying marks **2.2-2.4x thinner** than the vector
imitations of it did, so at a 50 px square three of the four raster marks do NOT
clear the 3 px floor those imitations were built to clear (measured at solo size:
food leaf 4.16 px, but hiding-predator spike tip 2.45, rabbit inner ear 2.30,
predator eye slit 2.16). The floor is therefore NOT silently lowered and NOT
silently kept: rasters are judged by :data:`RASTER_MIN_DIAMETER_PX` and
:data:`RASTER_MIN_MARK_AREA_PX2` -- the pair validated by the design round's own
4:2:0 + JPEG compression test -- and :data:`MARK_FLOOR_PX` stays exactly where it
was, still enforced, for the vector forms it was swept on. The substitution is
recorded in the plan and in the Implementation Report, never here alone.

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
#:
#: 0.30 -> 0.34 on 2026-09-17. The adopted spec says the white token is
#: "0.34 x cell" and always did; the renderer had been drawing every mover at
#: 0.30, a shrink nobody decided and which the plan deferred to this checkpoint.
#: It costs the arena nothing -- the tokens sit in slots that were already wider
#: than this -- and lifts every identifying mark by 13 %.
SOLO_H = 0.34

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
#:
#: UNCHANGED, DELIBERATELY. It is swept on, and still enforced for, the VECTOR
#: forms below. The raster movers are judged by the pair beneath it instead --
#: see the module docstring, and :func:`check_legible`, which applies whichever
#: rule matches how the token is actually drawn rather than applying both to
#: everything.
MARK_FLOOR_PX = 3.0

#: The raster substitution, and the two numbers that replace the mark floor for
#: an artwork token.
#:
#: WHY A SUBSTITUTION EXISTS AT ALL. The per-mark 3 px floor is unachievable at
#: SHARED size for ANY 50 px square and always was: at ``slot_h(2, 50) = 10.35``
#: even the vector rabbit's 0.30 x h ear gap is 3.1 px and the four-way is 3.0,
#: i.e. the vector forms passed only because they drew their marks 2.2-2.4x
#: thicker than the art they were imitating. Against the real artwork the floor
#: rejects three of four movers at SOLO size, so keeping it would mean rendering
#: no frame at all rather than rendering a legible one. The mark is still
#: MEASURED (:func:`raster_mark_area_px2`, :data:`RASTER_MARK`) and still
#: reported; what changed is that it is no longer the gate.
#:
#: WHAT REPLACES IT, AND ON WHAT EVIDENCE. The design round composited all five
#: masters at these exact token sizes on a real ground square and pushed them
#: through 4:2:0 chroma subsampling plus JPEG q42 -- the video path's own
#: degradation. All five stayed identifiable at solo size and separable at shared
#: size, where identity moves from the fine mark to SILHOUETTE and BODY COLOUR.
#: These two numbers are what that evidence actually supports: a token big enough
#: to carry a silhouette, and enough surviving body colour to tell one from
#: another. They are not a loosened version of the mark floor; they measure a
#: different thing, which is why the mark floor is left standing rather than
#: edited down to fit.
RASTER_MIN_DIAMETER_PX = 20.0
RASTER_MIN_BODY_AREA_PX2 = 40.0

#: The white token disc's radius in every mover master, as a fraction of the
#: 1000 px canvas -- measured, and identical across all four non-agent masters
#: (alpha bbox 0.153..0.847). It is the number that converts a mark measured on
#: the master into a fraction of ``h``.
TOKEN_DISC_FRAC = 0.347

#: Each mover's identifying mark and the palette colour it is painted in, so the
#: mark can be found in the asset rather than described in prose.
RASTER_MARK_COLOUR: dict[str, str] = {
    "food": P.FOOD_LEAF,
    "predator": P.HIDE_EYE,
    "neutral": P.NEUT_INNER,
    "hiding_predator": P.HIDE_EYE,
}

#: Each mover's BODY colour -- the large flat field that carries its silhouette.
#: This, not the mark, is what :func:`check_legible` gates on at shared size:
#: the compression test found identity moving to silhouette and body colour once
#: the fine mark stops surviving, so the body is the thing that has to be there.
RASTER_BODY_COLOUR: dict[str, str] = {
    "food": P.FOOD,
    "predator": P.PRED,
    "neutral": P.NEUT,
    "hiding_predator": P.HIDE_BODY,
    "agent": P.IRIS,
}

#: The frozen measurement: each mark's SHORT DIMENSION on its own master, as a
#: fraction of ``h``. Frozen so the arithmetic is readable without opening a PNG,
#: and RE-MEASURED from the PNG by ``test_dashboard_cells.py`` so swapping in
#: weaker artwork fails rather than silently shipping.
#:
#: At the decided 50 px square these are 4.16 / 2.45 / 2.30 / 2.16 rendered px
#: solo. Recorded here because the numbers, not an adjective, are what a later
#: reader needs to re-open this decision.
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
class Raster:
    """One occupant drawn as the user's own artwork, in its own image artist.

    ``px`` is the INTEGER edge length the master is resampled to, once, at build
    time. Matplotlib's own on-the-fly resampling is mushy at 20 px, so the image
    handed to the canvas is already exactly the size it will occupy and is drawn
    with ``interpolation="none"``.
    """

    name: str
    cx: float
    cy: float
    h: float
    px: int
    action: str | None = None

    @property
    def extent(self):
        """``(left, right, bottom, top)`` in the arena's y-DOWN pixel space."""
        return (self.cx - self.h, self.cx + self.h,
                self.cy + self.h, self.cy - self.h)


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

    Cropping to the ALPHA BOUNDING BOX is what makes every token the same size
    as every other: the masters pad their glyphs differently (the agent's halo
    reaches 0.104..0.896 of its canvas, a mover's token disc 0.153..0.847), so
    mapping the canvas would draw the agent smaller than the rabbit standing
    beside it. The bbox is mapped to the slot's ``2h`` box instead, which also
    keeps every token's ink inside ``h`` -- the property the slot geometry and
    the pixel audit both assume.
    """
    import numpy as np
    from PIL import Image

    path = os.path.join(ICON_DIR, f"{name}.png")
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"no artwork for {name!r} at {path}. The movers are drawn from the "
            f"user's chosen icon set; this package does not fall back to a "
            f"vector imitation of it, because a frame drawn in the wrong forms "
            f"is the defect this restoration removed."
        )
    im = np.asarray(Image.open(path).convert("RGBA"))
    ys, xs = np.nonzero(im[..., 3] > 8)
    return im[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


@functools.lru_cache(maxsize=None)
def icon_array(name: str, px: int, action: str | None = None):
    """The artwork for ``name``, resampled ONCE to ``px`` x ``px``.

    Lanczos, because this is a downsample of about 50:1 and the marks that carry
    identity are two pixels wide at the far end of it.

    THE AGENT'S CHEVRON IS COMPOSITED IN HERE, NOT DRAWN OVER THE TOP, and the
    reason is the audit rather than tidiness. The co-occupancy rule forbids two
    of a square's occupant artists from sharing a single pixel -- that is how it
    catches one token painted over another -- so a chevron in its own patch
    artist, lying by construction on top of the agent's own disc, would report
    every agent in every frame as an occupant drawn over an occupant. One token
    is one artist; the chevron therefore goes into the token's own pixels.

    It is supersampled 4x and box-filtered down, so the diagonal edges are as
    smooth as the vector one was at the sizes this actually draws at (17 px and
    10 px half-extents).
    """
    import numpy as np
    from PIL import Image, ImageDraw

    if px < 1:
        raise ValueError(f"{name}: an icon cannot be drawn at {px}px")
    if action is not None and name != "agent":
        raise ValueError(
            f"{name!r} has no action mark; only the agent carries one "
            f"(asked for {action!r})"
        )
    ss = 4
    src = Image.fromarray(_master(name)).resize((int(px) * ss, int(px) * ss),
                                                Image.LANCZOS)
    if name == "agent":
        big = int(px) * ss
        c = big / 2.0
        a = (big / 2.0) * CHEVRON_FRACTION
        layer = Image.new("RGBA", (big, big), (0, 0, 0, 0))
        pen = ImageDraw.Draw(layer)
        if action in ARROW_VEC:
            dx, dy = ARROW_VEC[action]
            nx, ny = -dy, dx
            pen.polygon([
                (c + dx * a, c + dy * a),
                (c - dx * a * 0.3 + nx * a * 0.62, c - dy * a * 0.3 + ny * a * 0.62),
                (c, c),
                (c - dx * a * 0.3 - nx * a * 0.62, c - dy * a * 0.3 - ny * a * 0.62),
            ], fill=(255, 255, 255, 255))
        else:
            r = (big / 2.0) * 0.30
            pen.ellipse([c - r, c - r, c + r, c + r], fill=(255, 255, 255, 255))
        src = Image.alpha_composite(src, layer)
    return np.asarray(src.resize((int(px), int(px)), Image.BOX),
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
    change while the process lives. A property of a PNG on disk belongs in a
    cache keyed by that PNG, not in the per-frame hot path.
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
    token's drawn size depends on the frame.
    """
    return _colour_share(name, colour) * (2.0 * h) ** 2


def raster_body_area_px2(name: str, h: float) -> float:
    """How much of a token's OWN colour survives at half-extent ``h``, in px^2.

    THE UNION OF A TOKEN'S OWN PARTS, which is this project's existing rule and
    not a convenience adopted here. A mark drawn in two paints reads as partly
    missing if only one of them is counted: ``palette.MINIMAP_MARK_COLOURS``
    already defines the hiding predator's mark as its charcoal body PLUS the
    amber accent that tells it from an ordinary predator, and the pixel audit
    counts a token's own eye towards its own body for the same reason (plan
    sections R19.1 step 5 and R22.1).

    IT IS LOAD-BEARING FOR EXACTLY ONE MOVER, and the numbers are recorded so
    nobody has to wonder whether the rule was chosen to fit them. At shared size
    (``h`` = 10.35) the hiding predator's charcoal alone measures **39.41 px²**
    against the 40 px² floor -- it is a cluster of thin spikes, so its body is
    mostly edge -- and with its own amber tips counted, as the audit counts them,
    **45.80 px²**. Every other mover clears the floor on body colour alone.
    """
    colours = {RASTER_BODY_COLOUR[name]}
    if name in RASTER_MARK_COLOUR:
        colours.add(RASTER_MARK_COLOUR[name])
    return sum(_colour_area_px2(name, c, h) for c in sorted(colours))


def raster_mark_area_px2(name: str, h: float) -> float:
    """The identifying mark's painted AREA at half-extent ``h``, in px^2.

    Reported rather than gated on -- see :func:`check_legible`. At a shared 50 px
    square these are single-digit numbers for every mover, which is the measured
    fact behind the substitution the module docstring records.
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
    """Raise when a square cannot show what it is being asked to show.

    The movers are ARTWORK, so they are judged by the pair the compression test
    validated -- the token's diameter, and how much of its identifying mark's
    colour survives -- rather than by :data:`MARK_FLOOR_PX`, which measures a
    property of the vector imitations and is applied to them in
    :func:`min_cell_for`. The reasoning, and the measured numbers that forced the
    split, are in the module docstring; this function must not be read as the
    place the decision was made.

    The agent's chevron is still vector, so it still answers to its own floor.
    """
    h = slot_h(n, cell)
    for nm in names:
        if nm == "agent" and CHEVRON_FRACTION * h < CHEVRON_FLOOR_PX - 1e-9:
            raise CellLegibilityError(
                f"the agent's chevron would be {CHEVRON_FRACTION * h:.2f}px in a "
                f"{cell:.0f}px square shared by {n}; the floor is {CHEVRON_FLOOR_PX}px "
                f"({min_cell_for_chevron(n):.1f}px square needed)"
            )
        if 2.0 * h < RASTER_MIN_DIAMETER_PX - 1e-9:
            raise CellLegibilityError(
                f"the {nm} token would be {2 * h:.2f}px across in a {cell:.0f}px "
                f"square shared by {n}; the floor is {RASTER_MIN_DIAMETER_PX}px, "
                f"below which the artwork's silhouette stops being separable under "
                f"the video path's chroma subsampling"
            )
        if nm in RASTER_BODY_COLOUR:
            area = raster_body_area_px2(nm, h)
            if area < RASTER_MIN_BODY_AREA_PX2 - 1e-9:
                raise CellLegibilityError(
                    f"the {nm} would keep {area:.1f}px² of its own body colour in a "
                    f"{cell:.0f}px square shared by {n}; the floor is "
                    f"{RASTER_MIN_BODY_AREA_PX2}px², below which the silhouette that "
                    f"carries its identity at this size stops being separable"
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


#: The vector mover forms, which as of 2026-09-17 are the artwork's PROVENANCE
#: rather than the drawing path: the PNGs in ``assets/dashboard_icons/`` were
#: generated from these functions and then chosen, by eye, from contact sheets.
#: :func:`token` draws the PNGs. The table is kept -- and kept correct -- because
#: it is still what says WHICH movers exist: ``DISPLAY_NAME`` is asserted against
#: it at import, ``check_legible`` and the icon sheet read it, and a mover added
#: to the renderer with no form here would be an entity nothing can draw.
COMPANION = {
    "food": cf_food, "predator": cf_predator, "neutral": cf_neutral,
    "hiding_predator": cf_hiding_predator, "agent": cf_agent,
}


def token(name: str, cx: float, cy: float, h: float, action=None,
          shared: bool = True) -> list:
    """One occupant's drawing: its artwork, as ONE image, in its slot.

    ``shared`` is accepted and ignored on the artwork path, and that is a real
    simplification rather than an oversight: the vector agent needed its halo
    dropped on a shared square because the halo reached 1.32 x h, WIDER than the
    bed beneath it. ``agent.png`` carries its halo INSIDE its own alpha bbox,
    which is mapped to exactly ``2h``, so no part of the artwork can reach a
    neighbour and there is nothing to drop. The parameter stays because the
    vector forms below keep their signature -- they are the artwork's provenance
    now, not the drawing path.
    """
    if name not in COMPANION:
        raise KeyError(f"no form for {name!r}; known movers are {sorted(COMPANION)}")
    return [Raster(name, cx, cy, h, max(1, int(round(2 * h))),
                   action if name == "agent" else None)]


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
# What a READER calls each of these
#
# WHY A SECOND SET OF NAMES EXISTS. The keys above are the code's tokens, and
# one of them is not the English for the thing it draws: ``neutral`` is a
# rabbit. Every hand-written surface says "rabbit" -- the figure that labels the
# forms, the caption that describes a shared square, this module's own docstring
# -- while anything that *serialises* the token says "neutral", and a reader has
# no way to learn they are one animal. A reader reads "neutral" as an English
# adjective, not as an identifier, so the mismatch survives prose review.
#
# THE RULE THIS TABLE MAKES POSSIBLE. Any exporter that emits one of these names
# into something a reader will see routes it through :func:`display`, so the
# page's vocabulary and the painter's vocabulary cannot drift apart.
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

# Asserted at import, not trusted: a form added to COMPANION or BED without a
# reader's name for it would otherwise reach a page as a bare token, which is the
# exact defect this table was added to remove.
if set(DISPLAY_NAME) != set(COMPANION) | set(BED):
    _known = set(COMPANION) | set(BED)
    raise RuntimeError(
        f"DISPLAY_NAME does not cover the forms this module draws: missing "
        f"{sorted(_known - set(DISPLAY_NAME))}, unknown {sorted(set(DISPLAY_NAME) - _known)}"
    )


def display(name: str) -> str:
    """The name a reader sees for one occupant or terrain token.

    Raises rather than falling back to the token: a silently passed-through
    ``neutral`` on a page is the failure this function exists to make loud.
    """
    if name not in DISPLAY_NAME:
        raise KeyError(
            f"no reader's name for {name!r}; known tokens are {sorted(DISPLAY_NAME)}"
        )
    return DISPLAY_NAME[name]


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
