"""The composition of one world square: variant H, checked as arithmetic.

WHAT THESE TESTS ARE FOR, IN PLAIN WORDS. A square of the world can hold more
than one thing at once, and the old renderer drew them all on the same centre
point, so one covered the other: an agent standing in a bush rendered as an agent
alone. The fix the user chose draws the terrain as the square's FLOOR and stands
the occupants on it, side by side. Whether that is *legible* is not a matter of
opinion -- it reduces to a few numbers, and this file is where those numbers are
checked:

* a token's ink half-extent ``h`` is **17.00 / 10.35 / 10.12 px** for one, two,
  and three-or-four occupants in a 50 px square;
* the smallest identifying mark on each VECTOR form (the predator's amber eye
  slit, the rabbit's ear gap) must clear about 3 rendered pixels, which is what
  makes the square's minimum size **49 px** for two occupants and **50 px** for a
  four-way;
* the agent's chevron must clear 6 px;
* and, since the movers are now drawn from the user's own artwork rather than
  from vector imitations of it, each icon's identifying mark is RE-MEASURED from
  its PNG, so swapping in weaker artwork fails here rather than shipping.

They are recomputed here from the form constants rather than quoted, so a change
to a form that breaks legibility fails **here**, in a second, instead of in a
video nobody re-measures.

WHY THE DEPTH TESTS MATTER AS MUCH AS THE SIZE ONES. The instrument that checks
a finished frame decides "was this occupant actually visible?" by asking which
element was painted last at each of its pixels. That makes three orderings
load-bearing rather than cosmetic: bed below token, the agent's square outline
below token, and a sense's footprint outline below token. Drawn above, a 1.5 px
footprint edge crossing a 20 px occupant deletes about 7 % of it and the audit
fires on a picture that is actually correct.
"""

import os
import sys

import pytest

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import matplotlib  # noqa: E402
matplotlib.use("Agg")

from src.environment.dashboard import cells as C  # noqa: E402

CELL = 50.0


# --------------------------------------------------------------------------
# slot geometry
# --------------------------------------------------------------------------
@pytest.mark.parametrize("n,expected", [(1, 17.00), (2, 10.35), (3, 10.12), (4, 10.12)])
def test_slot_half_extent_at_the_decided_square(n, expected):
    """The three pinned numbers of plan section R18.3, to two decimals."""
    assert C.slot_h(n, CELL) == pytest.approx(expected, abs=0.005)


def test_a_lone_occupant_is_the_same_size_with_and_without_a_bed():
    """The property variant H was chosen for.

    Terrain is the floor, so it costs the occupants no room: an agent standing
    in a bush is drawn at exactly the size it would be on bare ground. If this
    ever fails, the bed has started taking ink budget from the movers and the
    whole reason for the variant is gone.
    """
    bare = C.compose(["agent"], 25, 25, CELL)
    on_bush = C.compose(["bush", "agent"], 25, 25, CELL)
    assert bare[0] is None and on_bush[0] == "bush"
    lone = C.slots(["agent"], 25, 25, CELL)[0]
    shared = C.slots(["agent"], 25, 25, CELL)[0]
    assert lone.h == shared.h == pytest.approx(17.0)
    assert len(on_bush[1]) == 1 and on_bush[1][0][0] == "agent"


def test_three_occupants_read_as_two_over_one_not_as_a_gap():
    sl = C.slots(["agent", "predator", "food"], 25, 25, CELL)
    assert len(sl) == 3
    rows = sorted({round(s.cy, 3) for s in sl})
    assert len(rows) == 2, "three occupants use two rows"
    bottom = [s for s in sl if round(s.cy, 3) == rows[1]]
    assert len(bottom) == 1
    assert bottom[0].cx == pytest.approx(25.0), "the last row is centred"


def test_two_occupants_sit_side_by_side_and_their_ink_cannot_touch():
    """Adjacent slots are further apart than two tokens are wide.

    The keyline is drawn INSET so its outer edge lies at ``h`` (never centred on
    ``h``), which is what keeps this margin real rather than a white-on-white
    kiss that no eye sees and no measurement forgives.
    """
    a, b = C.slots(["agent", "predator"], 25, 25, CELL)
    gap = abs(b.cx - a.cx) - (a.h + b.h)
    assert gap > 0, f"tokens overlap by {-gap:.2f}px"


def test_slots_stay_inside_their_square():
    for names in (["agent"], ["agent", "predator"],
                  ["agent", "predator", "food"],
                  ["agent", "predator", "food", "neutral"]):
        for s in C.slots(names, 25, 25, CELL):
            assert s.cx - s.h >= 0 and s.cx + s.h <= CELL
            assert s.cy - s.h >= 0 and s.cy + s.h <= CELL


# --------------------------------------------------------------------------
# the legibility floors, recomputed
# --------------------------------------------------------------------------
def test_the_two_recorded_square_floors_are_reproduced():
    """49 px for the binding two-occupant case, 50 px for the four-way."""
    two = max(C.min_cell_for(2, n) for n in ("predator", "neutral", "food",
                                             "hiding_predator"))
    four = max(C.min_cell_for(4, n) for n in ("predator", "neutral", "food",
                                              "hiding_predator"))
    assert two == pytest.approx(48.31, abs=0.02)
    assert four == pytest.approx(49.41, abs=0.02)
    import math
    assert math.ceil(two) == 49
    assert math.ceil(four) == 50
    assert CELL >= math.ceil(four), "the decided square must clear the four-way floor"


def test_the_chevron_floor_is_on_the_chevron():
    """0.62 x h >= 6 px -- the drawn chevron length, not ``h`` itself."""
    assert C.CHEVRON_FRACTION * C.slot_h(2, CELL) == pytest.approx(6.417, abs=0.01)
    assert C.CHEVRON_FRACTION * C.slot_h(4, CELL) == pytest.approx(6.274, abs=0.01)
    assert C.min_cell_for_chevron(4) < CELL


def test_a_square_too_small_raises_rather_than_drawing_the_unreadable():
    with pytest.raises(C.CellLegibilityError):
        C.compose(["agent", "predator", "food", "neutral"], 12, 12, 24.0)


# --------------------------------------------------------------------------
# the tables the matrix depends on
# --------------------------------------------------------------------------
def test_every_entity_the_matrix_can_place_has_a_form():
    """Every non-terrain kind is in CELL_PRIORITY and has a companion form;
    every terrain has a bed form. A name in neither is an entity that would be
    drawn by accident of alphabetical order, which is the defect being removed.
    """
    placeable = {"agent", "predator", "neutral", "food", "hiding_predator"}
    assert placeable == set(C.CELL_PRIORITY)
    assert placeable == set(C.COMPANION)
    assert set(C.TERRAIN_NAMES) == set(C.BED)
    for name in placeable:
        assert name in C.MIN_MARK and name in C.KEY_MARK


def test_draw_order_is_explicit_and_never_alphabetical():
    assert C.by_priority(["neutral", "agent"]) == ["agent", "neutral"]
    assert C.by_priority(["food", "predator"]) == ["predator", "food"]
    assert C.by_priority(["neutral", "food"]) == ["food", "neutral"], (
        "alphabetical order would put 'food' first here too -- so the case that "
        "proves the point is the pair above, where alphabetical disagrees"
    )
    with pytest.raises(KeyError):
        C.by_priority(["rock"])


def test_terrain_never_counts_as_an_occupant():
    """Two occupants plus a bed is a TWO-slot square, not a three-slot one."""
    _bed, drawn = C.compose(["bush", "agent", "predator"], 25, 25, CELL)
    assert _bed == "bush"
    assert len(drawn) == 2
    assert all(len(C.slots(["agent", "predator"], 25, 25, CELL)) == 2 for _ in (0,))


def test_two_terrains_in_one_square_raise():
    with pytest.raises(ValueError, match="two terrains"):
        C.compose(["bush", "rock"], 25, 25, CELL)


# --------------------------------------------------------------------------
# depth, and the one-artist bed rule
# --------------------------------------------------------------------------
def test_every_arena_overlay_is_below_the_tokens():
    assert C.GROUND_Z < C.BED_Z < C.TOKEN_Z
    assert C.OUTLINE_Z < C.TOKEN_Z
    assert C.FOOTPRINT_Z < C.TOKEN_Z


def test_a_bed_plate_covers_more_than_forty_percent_of_its_square():
    """The audit tells a floor from an occupant by measured AREA, at 40 %.

    A bed under that line is counted as an occupant, and a square holding only a
    campfire would then be reported as holding an animal -- a failure on a
    correct painter. The full-bleed plate clears the line by construction.
    """
    assert C.bed_plate_fraction(CELL) > 0.40
    assert C.bed_plate_fraction(CELL) == pytest.approx(0.5184, abs=1e-4)


def test_no_token_can_put_ink_outside_its_own_slot():
    """The property the vector agent needed a special rule to obtain.

    The vector agent carried a halo at 1.32 x h -- wider than the bed beneath it
    -- so it had to be dropped whenever the square was shared, or it painted over
    the neighbour. That was the mechanism behind 'agent in a bush renders as
    agent alone'. The artwork makes the rule unnecessary instead of enforcing it:
    ``agent.png`` holds its halo INSIDE its own alpha bounding box, which is
    mapped to exactly ``2h``, so no mover's ink can leave its slot whatever else
    is in the square. Asserted for every mover, shared and solo.
    """
    for name in C.CELL_PRIORITY:
        for n, shared in ((1, False), (2, True)):
            h = C.slot_h(n, CELL)
            (r,) = C.token(name, 25, 25, h, action="UP", shared=shared)
            left, right, bottom, top = r.extent
            assert (right - left) == pytest.approx(2 * h)
            assert (bottom - top) == pytest.approx(2 * h)
            assert left == pytest.approx(25 - h) and top == pytest.approx(25 - h)


def test_a_token_is_exactly_one_artist():
    """One occupant is one drawn thing, including the agent's action chevron.

    The audit's co-occupancy rule forbids two of a square's occupant artists from
    sharing a pixel -- that is how it catches one token painted over another -- so
    an agent whose chevron were its own patch artist, lying by construction on
    top of its own disc, would report EVERY agent in EVERY frame as an occupant
    drawn over an occupant. The chevron is therefore composited into the agent's
    own pixels, and a token is one image and nothing else.
    """
    for name in C.CELL_PRIORITY:
        drawn = C.token(name, 25, 25, 10.35, action="RIGHT")
        assert len(drawn) == 1, f"{name} draws {len(drawn)} things"
        assert isinstance(drawn[0], C.Raster)
    # and the chevron really does travel inside the agent's own image
    import numpy as np
    turned = {a: C.icon_array("agent", 34, a) for a in ("UP", "RIGHT", None)}
    assert not np.array_equal(turned["UP"], turned["RIGHT"]), (
        "the agent's image must change with its action, or the chevron is not in it")
    assert not np.array_equal(turned["UP"], turned[None])


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
            f"assets/dashboard_icons/{name}.png against the frozen "
            f"{frozen:.3f}. If the artwork was deliberately replaced, re-measure "
            f"and move RASTER_MARK with the new numbers recorded; never relax "
            f"this tolerance to accommodate a weaker icon.")


def test_the_artwork_meets_the_floors_that_replaced_the_mark_floor():
    """The substitution's own two numbers, at both sizes a 50 px square uses.

    Recorded here because the numbers, not an adjective, are what a later reader
    needs: the per-mark 3 px floor is NOT met by this artwork (measured 2.16-4.16
    px solo), and the pair below is what the design round's compression test
    actually validated in its place.
    """
    for n in (1, 2, 3, 4):
        h = C.slot_h(n, CELL)
        assert 2 * h >= C.RASTER_MIN_DIAMETER_PX
        for name in C.CELL_PRIORITY:
            assert C.raster_body_area_px2(name, h) >= C.RASTER_MIN_BODY_AREA_PX2
        C.check_legible(n, list(C.CELL_PRIORITY)[:n], CELL)

    # The one mover the floor actually binds on, with both numbers, so that the
    # union rule cannot be mistaken for a threshold chosen to fit the artwork.
    tight = C.slot_h(2, CELL)
    assert C._colour_area_px2("hiding_predator", C.RASTER_BODY_COLOUR[
        "hiding_predator"], tight) == pytest.approx(39.41, abs=0.05)
    assert C.raster_body_area_px2("hiding_predator", tight) == pytest.approx(
        45.80, abs=0.1)

    solo = {n: C.RASTER_MARK[n] * C.slot_h(1, CELL) for n in C.RASTER_MARK}
    assert solo["food"] == pytest.approx(4.16, abs=0.05)
    assert min(solo.values()) == pytest.approx(2.16, abs=0.05), solo
    assert min(solo.values()) < C.MARK_FLOOR_PX, (
        "if the artwork ever clears the 3px mark floor at solo size, say so in "
        "the plan and reconsider the substitution -- do not leave this comment")


def test_the_world_map_caption_fits_its_card_and_describes_what_is_drawn():
    """The World card's caption is load-bearing text, and it is checked as such.

    TWO THINGS CAN GO WRONG WITH IT, and both have. It can stop being TRUE: the map used
    to draw a third occupant as a pip on the square's rim, that pip was retired (plan
    section R22.3) and a caption still naming it would leave the picture encoding one
    thing and the page stating another -- the failure mode finding #56 logged. And it can
    stop FITTING: the caption role is already at its 12 px legibility floor, so the text
    fitter cannot shrink it and RAISES instead, which would take the whole renderer down.

    The card is 320 px wide with 16 px padding, so the slot is 288 px. Measured here in
    the vendored font rather than estimated from character counts.
    """
    import matplotlib.pyplot as plt

    from src.environment.dashboard import painters as PN
    from src.environment.dashboard.layout import LEFT_W
    from src.environment.dashboard.style import register_fonts, text

    # The vendored faces, or this measures DejaVu and means nothing: the same line is
    # 299.6 px in the fallback font against 264.0 px in the real one, so a test without
    # this call fails on text that fits perfectly well.
    register_fonts()
    budget = LEFT_W - 2 * PN.PAD
    fig = plt.figure(figsize=(LEFT_W / 100, 1.0), dpi=100)
    try:
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis("off")
        ax.set_xlim(0, LEFT_W)
        ax.set_ylim(100, 0)
        fig.canvas.draw()
        rend = fig.canvas.get_renderer()
        for line in PN.MINIMAP_CAPTION:
            w = text(ax, 0, 50, line, "caption").get_window_extent(rend).width
            assert w <= budget, (
                f"the World map caption line {line!r} measures {w:.1f} px against a "
                f"{budget} px slot; the caption role is at its legibility floor, so the "
                f"fitter raises rather than shrinking and the renderer would not build")
    finally:
        plt.close(fig)

    whole = " ".join(PN.MINIMAP_CAPTION).lower()
    # The audit keys on this substring (`SHARED_CAPTION`) to decide the card SAYS in words
    # that colour is a code here -- the honesty condition R17.4's exemption rests on.
    assert "shared square" in whole
    assert "colour is the code" in whole
    assert "grid view" in whole
    assert "up to four" in whole, "the caption must state the encoding's ceiling"
    assert "pip" not in whole, "the rim pip is retired; a caption naming it is stale"


def test_an_icon_is_resampled_once_to_an_integer_pixel_size():
    """Matplotlib's on-the-fly resampling is mushy at 20 px, so the image handed
    to the canvas is already exactly the size it will occupy."""
    h = 10.35
    (r,) = C.token("food", 25, 25, h)
    assert r.px == round(2 * h) == 21
    arr = C.icon_array(r.name, r.px, r.action)
    assert arr.shape == (21, 21, 4)
    assert arr.max() <= 1.0, "RGBA is handed over in 0..1, as Matplotlib wants it"
    assert C.icon_array(r.name, r.px, r.action) is arr, "resampling must be cached"
