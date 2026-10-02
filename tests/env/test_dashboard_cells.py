"""The composition of one world square, checked as arithmetic.

WHAT THESE TESTS ARE FOR, IN PLAIN WORDS. A square of the world can hold more
than one thing at once, and the old renderer drew them all on the same centre
point, so one covered the other: an agent standing in a bush rendered as an agent
alone. The approved design draws a lone occupant as a centred glyph -- a rock is a
rock, an apple is an apple -- and this module's job is to keep that picture while
making the crowded case honest. The rule is:

    one occupant is centred at its own size; two or more stand side by side.

So this file checks two different things, and the split matters. For a LONE
occupant it checks that the drawing is the approved mock's own: the sizes here
are read off the sketch's drawing code, not chosen. For a SHARED square it checks
that the departure is safe -- disjoint slots, nothing overlapping, and every token
still above the size at which the user's artwork stops being identifiable after
video compression.

WHAT CHANGED ON 2026-09-17 (plan Revision 27). Terrain used to be drawn as
"variant H": a full-bleed FLOOR filling the square with movers standing on it.
The user's approved design does not draw that, so the beds, `BED_MARGIN`,
`bed_plate_fraction` and the tests that pinned them are gone. Terrain is now an
occupant like any other -- it takes a slot when the square is shared -- which is
why the co-occupancy tests below include a rock and a bush among the things that
must stay visible.

THE OTHER HALF OF THE CHANGE IS THAT THE SQUARE SIZE IS NO LONGER FIXED. The
arena is a fixed 480 px box holding `local_view_size` squares, so the square is
96 px at a 5-wide window and 48 px at a 10-wide one. Every floor below is
therefore checked at BOTH ends of that range rather than at one decided size.
"""

import math
import os
import sys

import pytest

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import matplotlib  # noqa: E402
matplotlib.use("Agg")

from src.environment.dashboard import cells as C  # noqa: E402
from src.environment.dashboard import layout as L  # noqa: E402

#: The square at the approved design's own window (5 wide), and at the widest
#: window this renderer will draw (11 wide). Every floor is checked at both.
WIDE = L.arena_cell_px(5)        # 96.0
TIGHT = L.arena_cell_px(11)      # 43.63...
TEN = L.arena_cell_px(10)        # 48.0

MOVERS = ("agent", "predator", "hiding_predator", "food", "neutral")


# --------------------------------------------------------------------------
# a lone occupant: the approved mock's own picture
# --------------------------------------------------------------------------
@pytest.mark.parametrize("name,frac", [
    ("agent", 0.396),            # ds.agent_marker: halo at 1.32 x 0.30 x s
    ("food", 0.34),              # ds.token: the white disc is 0.34 x s
    ("predator", 0.34),
    ("hiding_predator", 0.34),
    ("neutral", 0.34),
    ("rock", 0.27),              # ds.g_rock / g_bush / g_tree / g_campfire span
    ("bush", 0.27),              # 0.26..0.285 x s; terrain takes the middle
    ("tree", 0.27),
    ("campfire", 0.27),
])
def test_a_lone_occupant_is_drawn_at_the_sketchs_own_size(name, frac):
    """These fractions are READ OFF the approved sketch, not chosen here.

    `renderer_layout_redesign/dashboard_style.py` draws a mover's token disc at
    `0.34 * s` and the agent's outer halo at `1.32 * 0.30 * s`; the terrain glyphs
    span 0.261 (bush) to 0.285 (campfire). If one of these moves, the frame stops
    being the frame the user approved, so it fails here.
    """
    assert C.SOLO_FRAC[name] == frac
    assert C.solo_h(name, WIDE) == pytest.approx(frac * WIDE)


def test_a_lone_occupant_keeps_the_artworks_own_proportions():
    """A rock is half again as wide as it is tall, and must be drawn that way.

    MEASURED from the masters' alpha bounding boxes: rock 1.52, bush 1.27, tree
    0.72, campfire 1.00, the movers 0.976. Fitting a master into a SQUARE box --
    which is what the renderer did while terrain was a full-bleed floor and the
    question did not arise -- draws a squashed rock and a stretched tree.
    """
    assert C.master_aspect("rock") == pytest.approx(1.52, abs=0.02)
    assert C.master_aspect("tree") == pytest.approx(0.72, abs=0.02)

    hw, hh = C.fit_box("rock", C.solo_h("rock", WIDE))
    assert hw / hh == pytest.approx(C.master_aspect("rock"), rel=1e-6)
    assert hw == pytest.approx(C.solo_h("rock", WIDE)), "the wider axis touches the box"

    hw, hh = C.fit_box("tree", C.solo_h("tree", WIDE))
    assert hh == pytest.approx(C.solo_h("tree", WIDE)), "the taller axis touches the box"
    assert hw < hh


def test_one_occupant_is_centred_and_is_the_only_thing_drawn():
    for name in ("rock", "campfire", "food", "agent"):
        drawn = C.compose([name], 48, 48, WIDE)
        assert len(drawn) == 1
        (nm, shapes), = drawn
        assert nm == name
        (r,) = shapes
        assert (r.cx, r.cy) == (48, 48)
        assert r.hw == pytest.approx(C.fit_box(name, C.solo_h(name, WIDE))[0])


# --------------------------------------------------------------------------
# a shared square: the only place the drawing departs from the mock
# --------------------------------------------------------------------------
@pytest.mark.parametrize("n", [2, 3, 4])
@pytest.mark.parametrize("cell", [WIDE, TEN, TIGHT])
def test_shared_slots_are_disjoint_and_inside_their_square(n, cell):
    """Two occupants may not overlap, and neither may leave the square.

    This is the property the whole module exists for: 'agent in a bush' renders as
    an agent AND a bush. Checked as geometry rather than by eye, at both ends of
    the window range.
    """
    names = list(C.CELL_PRIORITY[:n - 1]) + ["bush"]
    sl = C.slots(names, cell / 2, cell / 2, cell)
    assert len(sl) == n
    boxes = []
    for s in sl:
        hw, hh = C.fit_box(s.name, s.h)
        boxes.append((s.cx - hw, s.cy - hh, s.cx + hw, s.cy + hh))
        assert s.cx - hw >= 0 and s.cx + hw <= cell, f"{s.name} leaves its square"
        assert s.cy - hh >= 0 and s.cy + hh <= cell, f"{s.name} leaves its square"
    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            overlap_x = min(a[2], b[2]) - max(a[0], b[0])
            overlap_y = min(a[3], b[3]) - max(a[1], b[1])
            assert overlap_x <= 0 or overlap_y <= 0, (
                f"two tokens of a {n}-way square overlap by "
                f"{overlap_x:.2f} x {overlap_y:.2f} px at a {cell:.1f}px square")


def test_two_occupants_keep_a_real_gap_at_every_window_size():
    """Adjacent slot centres are cell/2 apart, and the tokens do not reach them.

    MEASURED rather than derived from `SHARED_FRAC` alone, because the tokens keep
    their own aspect ratios: the agent's master is square so its half-width is the
    full `0.235 * cell`, while a mover's is 0.976 as wide as it is tall, so its
    half-width is 0.2294 * cell. The gap between an agent and a predator is
    therefore 0.0356 * cell -- 3.42 px at a 5-wide window, 1.71 px at a 10-wide
    one, 1.55 px at the widest window the renderer allows. Recorded as numbers
    because "they do not touch" is exactly the kind of claim that stops being true
    silently.
    """
    for cell, expect in ((WIDE, 3.42), (TEN, 1.71), (TIGHT, 1.55)):
        a, b = C.slots(["agent", "predator"], cell / 2, cell / 2, cell)
        gap = abs(b.cx - a.cx) - (C.fit_box(a.name, a.h)[0] + C.fit_box(b.name, b.h)[0])
        assert gap == pytest.approx(expect, abs=0.05), f"{cell:.1f}px square: {gap:.2f}px"
        assert gap > 0


def test_terrain_is_an_occupant_now_and_takes_a_slot():
    """The reversal of variant H, asserted rather than described.

    A bush and an agent in one square are TWO drawn things side by side, not a
    carpet with something standing on it. The old rule returned a bed plus one
    token and drew the agent at full size; this one returns two tokens.
    """
    drawn = C.compose(["bush", "agent"], 48, 48, WIDE)
    assert [n for n, _ in drawn] == ["agent", "bush"], "agent first, by CELL_PRIORITY"
    assert len({s[0].cx for _n, s in drawn}) == 2, "they must not share a centre"
    for _n, (r,) in drawn:
        assert r.hw <= C.shared_h(WIDE) + 1e-9


def test_three_occupants_read_as_two_over_one_and_four_fill_the_quadrants():
    three = C.slots(["agent", "predator", "food"], 48, 48, WIDE)
    rows = sorted({round(s.cy, 3) for s in three})
    assert len(rows) == 2
    assert len([s for s in three if round(s.cy, 3) == rows[1]]) == 1
    assert [s for s in three if round(s.cy, 3) == rows[1]][0].cx == pytest.approx(48.0)

    four = C.slots(["agent", "predator", "food", "neutral"], 48, 48, WIDE)
    assert len({(round(s.cx, 3), round(s.cy, 3)) for s in four}) == 4


def test_the_ceiling_is_four_and_the_agent_is_never_the_one_dropped():
    """Five things in one square: the agent is drawn, the terrain is not.

    `CELL_PRIORITY` puts the agent first and terrain last, so the square keeps
    answering the question a viewer is actually asking.
    """
    five = ["rock", "neutral", "food", "predator", "agent"]
    drawn = C.compose(five, 48, 48, WIDE)
    assert len(drawn) == C.MAX_SLOTS == 4
    names = [n for n, _ in drawn]
    assert names[0] == "agent"
    assert "rock" not in names, "terrain is last by priority, so it is what drops"


# --------------------------------------------------------------------------
# the legibility floors, recomputed
# --------------------------------------------------------------------------
def test_the_window_floor_in_layout_is_derived_from_the_artworks_own_floor():
    """`layout.ARENA_CELL_MIN_PX` is restated, not independently chosen.

    Layout may not import a drawing module, so the number that decides how wide a
    window may be lives in two places. This is what keeps them honest: it is
    re-derived from `cells` here, and it is the DIAMETER floor that binds
    (42.55 px), not the chevron (41.18) and not any body-colour area.
    """
    derived = C.min_cell_legible()
    assert derived == pytest.approx(C.RASTER_MIN_DIAMETER_PX / (2 * C.SHARED_FRAC))
    assert derived == pytest.approx(42.55, abs=0.05)
    assert L.ARENA_CELL_MIN_PX >= derived, (
        f"layout admits a {L.ARENA_CELL_MIN_PX}px square while cells.py says the "
        f"artwork stops being legible below {derived:.2f}px")
    assert L.ARENA_CELL_MIN_PX - derived < 1.0, "the restatement has drifted upward"
    assert int(L.ARENA_PX // L.ARENA_CELL_MIN_PX) == 11


@pytest.mark.parametrize("cell", [WIDE, TEN, TIGHT])
def test_every_composition_is_legible_at_every_window_size(cell):
    """The four-way square with terrain in it -- the tightest case that ships."""
    for names in (["campfire"], ["agent", "rock"],
                  ["agent", "predator", "bush"],
                  ["agent", "predator", "food", "campfire"]):
        C.check_legible(len(names), names, cell)
        C.compose(names, cell / 2, cell / 2, cell)


def test_a_window_one_wider_than_the_widest_is_refused_by_the_cell_rule():
    """12 squares across puts the square at 40 px, and the artwork says no.

    The failure is deliberately at COMPOSE time as well as at pack time: nothing
    should be able to reach the painter with a square the artwork cannot carry.
    """
    too_small = L.arena_cell_px(12)
    assert too_small == 40.0
    with pytest.raises(C.CellLegibilityError):
        C.compose(["agent", "predator"], 20, 20, too_small)


@pytest.mark.parametrize("cell", [WIDE, TEN, TIGHT])
def test_the_artwork_clears_its_two_measured_floors_at_every_window_size(cell):
    for n in (1, 2, 3, 4):
        for name in C.CELL_PRIORITY:
            h = C.slot_h(n, cell, name)
            assert 2 * h >= C.RASTER_MIN_DIAMETER_PX - 1e-9, (name, n, cell)
            assert C.raster_body_area_px2(name, h) >= C.RASTER_MIN_BODY_AREA_PX2 - 1e-9


def test_the_chevron_floor_is_on_the_chevron():
    """0.62 x h >= 6 px -- the drawn chevron length, not ``h`` itself."""
    assert C.CHEVRON_FRACTION * C.slot_h(2, WIDE) == pytest.approx(13.99, abs=0.01)
    assert C.CHEVRON_FRACTION * C.slot_h(4, TIGHT) == pytest.approx(6.36, abs=0.01)
    assert C.min_cell_for_chevron(2) == pytest.approx(41.18, abs=0.02)


def test_the_marks_the_50px_square_could_not_carry_are_carried_at_96():
    """A measured consequence of the fixed arena, recorded rather than implied.

    The plan substituted two raster floors for the per-mark 3 px floor (§R26.1)
    because at the then-decided 50 px square three of the four marks measured
    2.16-2.45 px and the renderer would have drawn no frame at all. At the
    approved design's 96 px square the same marks measure 4.15-8.00 px and clear
    the original floor outright; at a 10-wide window (48 px) they do not. The
    substitution is therefore still doing work -- it is what lets the window widen
    -- and this test states both halves so neither is mistaken for the other.
    """
    at = lambda cell: {n: C.RASTER_MARK[n] * C.solo_h(n, cell) for n in C.RASTER_MARK}  # noqa: E731
    wide, tight = at(WIDE), at(TEN)
    assert min(wide.values()) == pytest.approx(4.15, abs=0.05)
    assert min(wide.values()) > C.MARK_FLOOR_PX, (
        "at the approved square the artwork clears the mark floor it once missed")
    assert min(tight.values()) == pytest.approx(2.07, abs=0.05)
    assert min(tight.values()) < C.MARK_FLOOR_PX, (
        "at a 10-wide window it does not, which is why the raster pair is the gate")


def test_the_marks_are_re_measured_from_the_artwork_not_taken_on_trust():
    """Replacing an asset with weaker artwork must fail HERE, not in a video.

    This is what makes a frozen raster measurement a stronger guard than a typed
    vector fraction: the constant cannot notice that the file under it changed,
    and this does.
    """
    for name, frozen in C.RASTER_MARK.items():
        measured = C.measure_raster_mark(name)
        assert measured == pytest.approx(frozen, abs=0.005), (
            f"{name}'s {C.KEY_MARK[name]} measures {measured:.3f} x h in "
            f"assets/dashboard_icons/{name}.png against the frozen {frozen:.3f}. If "
            f"the artwork was deliberately replaced, re-measure and move RASTER_MARK "
            f"with the new numbers recorded; never relax this tolerance.")


def test_the_terrain_glyphs_are_gated_too_now():
    """Terrain answers to the same body-colour floor as everything else.

    Under variant H a bed was "the floor" and had NO legibility gate at all, so
    nothing measured whether a rock stayed a rock. The numbers are recorded
    because the campfire is the tightest of the four -- its log brown is a small
    share of a glyph that is mostly flame.
    """
    for name in ("rock", "bush", "tree", "campfire"):
        assert name in C.RASTER_BODY_COLOUR
    ref = 10.0
    need = {n: ref * (C.RASTER_MIN_BODY_AREA_PX2
                      / C.raster_body_area_px2(n, ref)) ** 0.5 / C.SHARED_FRAC
            for n in ("rock", "bush", "tree", "campfire")}
    assert need["campfire"] == pytest.approx(35.85, abs=0.5)
    assert max(need.values()) < L.ARENA_CELL_MIN_PX, (
        f"a terrain glyph would become the binding floor: {need}")


# --------------------------------------------------------------------------
# the tables the matrix depends on
# --------------------------------------------------------------------------
def test_every_entity_the_matrix_can_place_has_artwork_and_a_readers_name():
    placeable = {"agent", "predator", "neutral", "food", "hiding_predator",
                 "rock", "bush", "tree", "campfire"}
    assert placeable == set(C.CELL_PRIORITY)
    assert placeable == set(C.SOLO_FRAC)
    assert placeable == set(C.DISPLAY_NAME)
    assert set(C.TERRAIN_NAMES) == {"rock", "bush", "tree", "campfire"}
    assert C.display("neutral") == "rabbit"
    with pytest.raises(KeyError):
        C.display("magnetoceptor")


def test_draw_order_is_explicit_and_never_alphabetical():
    assert C.by_priority(["neutral", "agent"]) == ["agent", "neutral"]
    assert C.by_priority(["food", "predator"]) == ["predator", "food"]
    assert C.by_priority(["neutral", "food"]) == ["food", "neutral"], (
        "alphabetical order would put 'food' first here too -- so the case that "
        "proves the point is the pair above, where alphabetical disagrees"
    )
    assert C.by_priority(["bush", "agent"]) == ["agent", "bush"]
    with pytest.raises(KeyError):
        C.by_priority(["magnetoceptor"])


def test_two_terrains_in_one_square_raise():
    with pytest.raises(ValueError, match="two terrains"):
        C.compose(["bush", "rock"], 48, 48, WIDE)


def test_every_arena_overlay_is_below_the_tokens():
    assert C.GROUND_Z < C.TOKEN_Z
    assert C.OUTLINE_Z < C.TOKEN_Z
    assert C.FOOTPRINT_Z < C.TOKEN_Z


def test_a_token_is_exactly_one_artist():
    """One occupant is one drawn thing, including the agent's action chevron.

    The audit's co-occupancy rule forbids two of a square's occupant artists from
    sharing a pixel -- that is how it catches one token painted over another -- so
    an agent whose chevron were its own patch artist, lying by construction on top
    of its own disc, would report EVERY agent in EVERY frame as an occupant drawn
    over an occupant.
    """
    import numpy as np

    for name in C.CELL_PRIORITY:
        drawn = C.token(name, 25, 25, 20.0, action="RIGHT")
        assert len(drawn) == 1, f"{name} draws {len(drawn)} things"
        assert isinstance(drawn[0], C.Raster)
    turned = {a: C.icon_array("agent", 40, 40, a) for a in ("UP", "RIGHT", None)}
    assert not np.array_equal(turned["UP"], turned["RIGHT"]), (
        "the agent's image must change with its action, or the chevron is not in it")
    assert not np.array_equal(turned["UP"], turned[None])


def test_only_the_agent_carries_an_action_mark():
    with pytest.raises(ValueError, match="no action mark"):
        C.icon_array("food", 20, 20, "UP")


def test_an_icon_is_resampled_once_to_an_integer_pixel_size():
    """Matplotlib's on-the-fly resampling is mushy at 20 px, so the image handed
    to the canvas is already exactly the size it will occupy."""
    h = C.shared_h(WIDE)
    (r,) = C.token("rock", 48, 48, h)
    assert (r.px_w, r.px_h) == (round(2 * r.hw), round(2 * r.hh))
    assert r.px_w > r.px_h, "a rock is wider than it is tall, in pixels too"
    arr = C.icon_array(r.name, r.px_w, r.px_h, r.action)
    assert arr.shape == (r.px_h, r.px_w, 4)
    assert arr.max() <= 1.0, "RGBA is handed over in 0..1, as Matplotlib wants it"
    assert C.icon_array(r.name, r.px_w, r.px_h, r.action) is arr, "resampling must be cached"


def test_a_missing_master_raises_rather_than_falling_back_to_a_vector_imitation():
    with pytest.raises(KeyError):
        C.token("magnetoceptor", 0, 0, 10.0)


def test_the_slot_arithmetic_is_recomputed_not_quoted():
    """`SHARED_FRAC` is 0.25 x 0.94 -- a quarter of the square, less a 6 % margin."""
    assert C.SHARED_FRAC == pytest.approx(0.25 * 0.94)
    assert C.shared_h(WIDE) == pytest.approx(22.56)
    assert math.isclose(C.slot_h(2, WIDE), C.shared_h(WIDE))
    assert math.isclose(C.slot_h(1, WIDE, "food"), C.solo_h("food", WIDE))
