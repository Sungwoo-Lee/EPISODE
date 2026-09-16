"""The composition of one world square: variant H, checked as arithmetic.

WHAT THESE TESTS ARE FOR, IN PLAIN WORDS. A square of the world can hold more
than one thing at once, and the old renderer drew them all on the same centre
point, so one covered the other: an agent standing in a bush rendered as an agent
alone. The fix the user chose draws the terrain as the square's FLOOR and stands
the occupants on it, side by side. Whether that is *legible* is not a matter of
opinion -- it reduces to a few numbers, and this file is where those numbers are
checked:

* a token's ink half-extent ``h`` is **15.00 / 10.35 / 10.12 px** for one, two,
  and three-or-four occupants in a 50 px square;
* the smallest identifying mark on each form (the predator's amber eye slit, the
  rabbit's ear gap) must clear about 3 rendered pixels, which is what makes the
  square's minimum size **49 px** for two occupants and **50 px** for a four-way;
* the agent's chevron must clear 6 px.

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
@pytest.mark.parametrize("n,expected", [(1, 15.00), (2, 10.35), (3, 10.12), (4, 10.12)])
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
    assert lone.h == shared.h == pytest.approx(15.0)
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


def test_the_agent_drops_its_halo_when_the_square_is_shared():
    """The halo is wider than a whole bush glyph, so in a shared square it is
    ink landing on the neighbour -- the mechanism behind 'agent in a bush
    renders as agent alone'."""
    solo = C.token("agent", 25, 25, C.slot_h(1, CELL), action="UP", shared=False)
    shared = C.token("agent", 25, 25, C.slot_h(2, CELL), action="UP", shared=True)
    assert len(solo) == len(shared) + 2, "solo keeps a halo and a shadow; shared keeps neither"

    def radius(shapes):
        return max(s.patch.get_extents().width / 2 for s in shapes)

    assert radius(solo) > C.slot_h(1, CELL), "the solo halo reaches past h"
    assert radius(shared) <= C.slot_h(2, CELL) + 0.51, "no shared ink may pass h"


def test_a_token_is_one_compound_form_including_its_keyline():
    """The keyline travels WITH its token, as part of the same compound form.

    Drawn as its own artist it would be ink sitting on the perimeter of its own
    bounding box -- which is exactly how the audit recognises an outline -- and a
    ring-shaped part that classifies as an outline silently leaves the count of
    what is in the square.
    """
    shapes = C.token("predator", 25, 25, 10.35)
    rings = [s for s in shapes if s.fc == "none"]
    assert len(rings) == 1 and rings[0].lw > 0
    assert shapes[0] is rings[0], "the keyline is drawn first, beneath its own token"


def test_the_keyline_is_inset_so_its_outer_edge_lies_at_h():
    h = 10.35
    ring = C.token("food", 25, 25, h)[0]
    r = ring.patch.get_extents().width / 2
    assert r + ring.lw / 2 == pytest.approx(h, abs=1e-6)
