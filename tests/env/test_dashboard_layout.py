"""CP1: the dashboard registry and the layout packer.

WHAT THESE TESTS ARE FOR, IN PLAIN WORDS. The episode-video redesign rests on one
claim: that two dashboard panels printing on top of each other becomes
*structurally impossible* rather than something a human notices in a finished
video. This file is where that claim is checked. Panels declare the room they
need, a packer places them, and if they cannot all fit the packer raises instead
of quietly shrinking one or letting two boxes share pixels.

THE CHECKPOINT'S OWN FAILURE CONDITIONS. CP1 fails if boxes intersect, if a
declared panel is never placed, or if an impossible budget fails to raise. Each
of those is a test below, and each is written to do its **own** geometry check
rather than trusting the packer's internal assertion -- a suite that merely calls
``pack()`` and believes it would still pass a packer whose overlap check had been
deleted.

WHAT CHANGED ON 2026-09-17, because these tests asserted something quite
different until then (plan Revision 27). The arena used to be sized from the
WORLD -- ``world_w * 50 + 64`` -- so a 5x5 world packed to a 314 px card and a
10x10 world to a 564 px one, and every other panel on the frame reflowed with it:
the right column, the sensor band and the minimap's grow budget all moved when
the world's size changed, and the layout stopped fitting at 11x11 altogether.

The arena is now a **fixed 480 px box**, and ``visualization.local_view_size``
decides how many world squares are drawn inside it. So the whole frame is a
constant -- a 544 px arena card, a 496 px right column, a 256 px band -- for every
world and every window, and the square size is what moves (96 px at a 5-wide
window, 48 px at a 10-wide one). Most of the geometry pinned below is therefore
pinned ONCE rather than per world, and two properties this file used to assert
are gone on purpose:

  * "a smaller world gives the right column less height" -- there is no coupling
    left to state; the arena's height no longer depends on the world at all.
  * "a world too large to draw whole falls down a ladder" -- a world larger than
    the window is the ORDINARY case now (the grid view draws a window of it), not
    a fallback.

Both are replaced below by the property that superseded them: the packed boxes
are identical for worlds and windows of every size.
"""

import os
import subprocess
import sys

import pytest

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from src.environment.dashboard import layout as L  # noqa: E402
from src.environment.dashboard import panels as P  # noqa: E402
from src.environment.dashboard.layout import Box, LayoutOverflowError, pack  # noqa: E402
from src.environment.dashboard.panels import LayoutContext  # noqa: E402

MAINTAINED = [
    "configs/environment/default.yaml",
    "configs/environment/experiment/basic/00-static_predator_5x5.yaml",
    "configs/environment/experiment/basic/01-slow_predator_5x5.yaml",
    "configs/environment/experiment/basic/02-predator_and_rabbit_10x10.yaml",
    "configs/environment/experiment/basic/03-random_init_10x10.yaml",
    "configs/environment/experiment/basic/04-jump_attack_10x10.yaml",
    "configs/environment/experiment/basic/05-campfire_thermal_10x10.yaml",
    "configs/environment/experiment/basic/06-sensory_noise_10x10.yaml",
]

#: The campfire temperature world -- matrix cell M4. Its observation lacks
#: Nutrition and Injury, which is what CP1's "M4 yields observed Nutrition or
#: Injury rows" failure condition is about.
M4 = "configs/environment/experiment/basic/05-campfire_thermal_10x10.yaml"

FIVE_BY_FIVE = [
    "configs/environment/experiment/basic/00-static_predator_5x5.yaml",
    "configs/environment/experiment/basic/01-slow_predator_5x5.yaml",
]


def _params(path):
    """Resolve a config the way the trainer does -- never a raw YAML read.

    A raw ``yaml.safe_load`` does not resolve ``extends:``, so a config that
    inherits a mandatory key reports a false "required but missing".
    """
    from src.environment.config_loader import load_env_config, load_env_params

    return load_env_params(load_env_config(os.path.join(_ROOT, path)))


def _ctx(path):
    return LayoutContext.from_params(_params(path))


def _synthetic(
    world=10,
    *,
    thermal=True,
    olf_range=1,
    vis_range=0,
    visual_present=False,
    location=False,
    local_view=5,
    intero=True,
    action=True,
):
    """A LayoutContext for a world no maintained config produces.

    The default is a 10x10 world with a thermoception card, a sensor band holding
    diamond maps, and NO visual panel at all. No maintained config is shaped like
    that: the maintained thermal world reads BOTH senses past its own square
    (since 2026-09-19), so its band carries two sets of diamond maps, and a band
    holding smell alone exists only here.
    """
    bd = {"Satiation": 1}
    if thermal:
        bd["Body Temperature"] = 1
    if intero:
        bd["Interoceptive Nociception"] = 1
    bd["Extero Nociception"] = 1
    if thermal:
        bd["Thermoception"] = 5
    bd["Olfaction"] = 5 * P._diamond_cells(olf_range)
    bd["Collision"] = 5
    bd["Proprioception"] = 6
    if visual_present:
        bd["Visual"] = 8 * P._diamond_cells(vis_range)
    if location:
        bd["Location"] = 2
    return LayoutContext(
        world_w=world,
        world_h=world,
        local_view_size=local_view,
        breakdown=bd,
        thermal=thermal,
        intero_noc_enabled=intero,
        olfactory_range=olf_range,
        visual_range=vis_range,
        thermal_range=1 if thermal else 0,
        collision_range=1,
        visual_vector_size=8,
        olfactory_channels=5,
        real_available={},
        action_recorded=action,
    )


# --------------------------------------------------------------------------
# CP1 failure condition 1: boxes must not intersect
# --------------------------------------------------------------------------
def _overlapping_pairs(boxes):
    """Independent geometry check. Deliberately does not call Box.intersects.

    It also does not inherit the implementation's exemptions. An earlier version
    skipped any two boxes that were EQUAL, mirroring an exemption the packer then
    had -- but a helper that agrees with the packer by construction cannot catch a
    mistake in the packer's rule, and equal boxes are the most complete overlap
    there is rather than a special case. Two identical boxes are reported here.
    """
    keys = sorted(boxes)
    bad = []
    for i, a in enumerate(keys):
        ax, ay, aw, ah = boxes[a].x, boxes[a].y, boxes[a].w, boxes[a].h
        for b in keys[i + 1:]:
            bx, by, bw, bh = boxes[b].x, boxes[b].y, boxes[b].w, boxes[b].h
            x_ov = min(ax + aw, bx + bw) - max(ax, bx)
            y_ov = min(ay + ah, by + bh) - max(ay, by)
            if x_ov > 0 and y_ov > 0:
                bad.append((a, b, x_ov, y_ov))
    return bad


ALL_CONTEXTS = [
    ("default", lambda: _ctx("configs/environment/default.yaml")),
    ("m4_campfire", lambda: _ctx(M4)),
    ("5x5_static", lambda: _ctx(FIVE_BY_FIVE[0])),
    ("synthetic_band_10", lambda: _synthetic(10)),
    ("synthetic_band_both_senses", lambda: _synthetic(10, vis_range=1, visual_present=True)),
    ("synthetic_no_thermal", lambda: _synthetic(10, thermal=False)),
    ("synthetic_location", lambda: _synthetic(10, location=True)),
    ("synthetic_no_action", lambda: _synthetic(10, action=False)),
    ("synthetic_wide_world", lambda: _synthetic(20)),
    ("synthetic_wide_window", lambda: _synthetic(20, local_view=10)),
]


@pytest.mark.parametrize("name,make", ALL_CONTEXTS, ids=[n for n, _ in ALL_CONTEXTS])
def test_no_two_cards_share_a_pixel(name, make):
    """CP1: boxes must never intersect.

    This is the test that must go red if the packer is mutated to allow an
    overlap, so it recomputes the pairwise overlap itself instead of asking the
    packer whether it is happy.
    """
    lay = pack(make())
    bad = _overlapping_pairs(lay.cards)
    assert not bad, f"{name}: overlapping cards {bad}"


def test_the_overlap_helper_itself_flags_two_identical_boxes():
    """The helper must not inherit the implementation's exemptions.

    This is the check on the checker. If ``_overlapping_pairs`` skipped equal
    boxes -- as it and the packer both once did -- then every test above would
    still pass against a packer that placed two cards on top of each other, and
    the suite's central claim would be worthless for the worst case it can face.
    """
    same = Box(0, 0, 10, 10)
    assert _overlapping_pairs({"a": same, "b": same}), (
        "two boxes sharing every pixel must be reported as overlapping"
    )


def test_two_cards_with_the_same_box_are_rejected_rather_than_exempted():
    """The packer refuses coincident cards; it does not exempt them.

    ``_validate`` used to skip its overlap check for any two cards whose boxes
    were EQUAL -- an exemption keyed on coordinates happening to match rather than
    on what the cards are. Asserted against ``_validate`` on a hand-built Layout
    rather than on a packed one, precisely because no context can reach this state
    -- a test that only packs real configs could never see the hole.
    """
    shared = Box(100, 100, 200, 200)
    lay = L.Layout(
        cards={"a": shared, "b": shared},
        panels={},
        parent={},
        view_cells=5,
        cell_px=L.arena_cell_px(5),
        band=False,
        step="test",
        compact=False,
    )
    with pytest.raises(LayoutOverflowError, match="intersect"):
        L._validate(lay, [])


def test_a_second_band_card_is_refused_before_a_box_is_assigned():
    """Two band cards would both be given the band's box, i.e. a total overlap.

    The refusal is what lets the overlap check run with no exemption at all, so it
    has to happen before the boxes are handed out, not after.
    """
    ctx = _synthetic(10)
    cards = list(P.present_cards(ctx, band=True, compact=False))
    band = [c for c in cards if c.region == "band"]
    assert len(band) == 1, "the synthetic band context should declare exactly one band card"
    twin = L.CardDemand(**{**band[0].__dict__, "key": band[0].key + "_twin"})
    with pytest.raises(LayoutOverflowError, match="more than one band card"):
        L._pack_once(ctx, 5, True, False, "test", cards + [twin])


@pytest.mark.parametrize("name,make", ALL_CONTEXTS, ids=[n for n, _ in ALL_CONTEXTS])
def test_panels_inside_their_card_and_disjoint_within_it(name, make):
    """Leaves stay inside the card that frames them, and never overlap a sibling."""
    lay = pack(make())
    by_card = {}
    for key, box in lay.panels.items():
        card = lay.cards[lay.parent[key]]
        assert (
            box.x >= card.x
            and box.y >= card.y
            and box.x + box.w <= card.x + card.w
            and box.y + box.h <= card.y + card.h
        ), f"{name}: panel {key} {box} escapes card {lay.parent[key]} {card}"
        by_card.setdefault(lay.parent[key], {})[key] = box
    for card_key, members in by_card.items():
        bad = _overlapping_pairs(members)
        assert not bad, f"{name}: overlapping panels inside {card_key}: {bad}"


@pytest.mark.parametrize("name,make", ALL_CONTEXTS, ids=[n for n, _ in ALL_CONTEXTS])
def test_every_box_is_inside_the_canvas(name, make):
    lay = pack(make())
    for key, box in list(lay.cards.items()) + list(lay.panels.items()):
        assert box.x >= 0 and box.y >= 0, f"{name}: {key} starts off-canvas: {box}"
        assert box.x + box.w <= L.CANVAS_W, f"{name}: {key} runs past the right edge: {box}"
        assert box.y + box.h <= L.CANVAS_H, f"{name}: {key} runs past the bottom: {box}"
        assert box.w > 0 and box.h > 0, f"{name}: {key} has an empty box: {box}"


# --------------------------------------------------------------------------
# CP1 failure condition 2: every declared panel is placed
# --------------------------------------------------------------------------
@pytest.mark.parametrize("name,make", ALL_CONTEXTS, ids=[n for n, _ in ALL_CONTEXTS])
def test_every_present_panel_gets_a_box(name, make):
    ctx = make()
    lay = pack(ctx)
    declared = {p.key for p in P.present_panels(ctx)}
    missing = declared - set(lay.panels)
    assert not missing, f"{name}: declared but never placed: {sorted(missing)}"


@pytest.mark.parametrize("name,make", ALL_CONTEXTS, ids=[n for n, _ in ALL_CONTEXTS])
def test_no_absent_panel_is_placed(name, make):
    ctx = make()
    lay = pack(ctx)
    declared = {p.key for p in P.present_panels(ctx)}
    extra = set(lay.panels) - declared
    assert not extra, f"{name}: placed a panel that is not present: {sorted(extra)}"


# --------------------------------------------------------------------------
# CP1 failure condition 3: overflow raises
# --------------------------------------------------------------------------
def test_an_impossible_budget_raises_rather_than_shrinking():
    """A demand that cannot fit must raise, not silently squeeze a panel."""
    ctx = _synthetic(10)
    cards = list(P.present_cards(ctx, band=True, compact=False))
    fat = [
        L.CardDemand(
            key=c.key, region=c.region, order=c.order,
            min_h=c.min_h * 4 if c.region == "right" else c.min_h,
            min_w=c.min_w, chrome_top=c.chrome_top, chrome_bottom=c.chrome_bottom,
            chrome_side=c.chrome_side, grow=c.grow, max_h=c.max_h, row=c.row,
            flow=c.flow, children=c.children, child_h=c.child_h,
            child_min_w=c.child_min_w,
        )
        for c in cards
    ]
    with pytest.raises(LayoutOverflowError) as exc:
        L._pack_once(ctx, 5, True, False, "test", fat)
    assert "right" in str(exc.value)


def test_a_window_too_wide_to_draw_legibly_is_refused_naming_the_config_key():
    """The one arena-side refusal left, and the reason it is the LAST resort.

    The arena is a fixed 480 px box, so a wider window buys more world at a
    smaller square -- and below `ARENA_CELL_MIN_PX` two occupants sharing a square
    stop being separable in the finished video. The packer refuses rather than
    drawing it, and the message names `local_view_size`, because the fix is the
    config's and never "grow the card".
    """
    with pytest.raises(LayoutOverflowError) as exc:
        pack(_synthetic(30, local_view=14))
    msg = str(exc.value)
    assert "local_view_size" in msg and "fixed size" in msg


def test_the_widest_usable_window_is_eleven_and_it_is_derived_not_declared():
    """11 x 11 packs, 12 x 12 does not, and the boundary is arithmetic.

    `480 / 43 = 11.2`, so eleven squares across is the widest window whose square
    still clears the artwork's own legibility floor. It is asserted here as a
    BOUNDARY rather than a constant so that moving either number moves this test.
    """
    widest = int(L.ARENA_PX // L.ARENA_CELL_MIN_PX)
    assert widest == 11
    lay = pack(_synthetic(30, local_view=widest))
    assert lay.view_cells == widest
    assert lay.cell_px >= L.ARENA_CELL_MIN_PX
    with pytest.raises(LayoutOverflowError):
        pack(_synthetic(30, local_view=widest + 1))


# --------------------------------------------------------------------------
# The arena is a FIXED BOX and the window is a zoom inside it
# --------------------------------------------------------------------------
@pytest.mark.parametrize("name,make", ALL_CONTEXTS, ids=[n for n, _ in ALL_CONTEXTS])
def test_the_arena_is_always_the_same_size(name, make):
    """The claim Revision 27 rests on: the panel does not move, the zoom does."""
    lay = pack(make())
    card = lay.cards["arena"]
    assert (card.w, card.h) == (544, 544), f"{name}: arena card {card}"
    grid = lay.arena_grid
    assert (grid.w, grid.h) == (L.ARENA_PX, L.ARENA_PX), f"{name}: arena grid {grid}"
    assert lay.cell_px == pytest.approx(L.ARENA_PX / lay.view_cells)


@pytest.mark.parametrize("world", [5, 10, 20, 50])
@pytest.mark.parametrize("view", [5, 7, 10])
def test_every_world_and_every_window_packs_to_identical_boxes(world, view):
    """The property that replaced "a smaller world gives less height".

    A 5x5 world and a 50x50 world, a 5-wide window and a 10-wide one: the same
    frame, to the pixel. Only `view_cells` and `cell_px` differ, which is the
    whole of what the window is allowed to change.
    """
    base = pack(_synthetic(10, local_view=5))
    lay = pack(_synthetic(world, local_view=view))
    assert lay.cards == base.cards
    assert lay.panels == base.panels
    assert lay.regions == base.regions
    assert lay.view_cells == min(view, world)
    assert lay.cell_px == pytest.approx(L.ARENA_PX / min(view, world))


def test_the_window_is_the_config_s_and_the_sense_range_is_its_floor():
    """`local_view_size` decides, except that the view must cover what is sensed.

    A sense reaching two squares forces a 5-wide window even if the config asks
    for 3, because a grid view that cannot show what the agent just smelled is
    lying about the episode by omission.
    """
    assert L.window_cells(_synthetic(10, local_view=7)) == 7
    assert L.window_cells(_synthetic(10, local_view=3, olf_range=2)) == 5
    assert L.window_cells(_synthetic(10, local_view=9, olf_range=2)) == 9
    # ...and a world smaller than the window is drawn whole, which is the SPECIAL
    # case rather than the first choice.
    assert L.window_cells(_synthetic(4, local_view=7)) == 4


@pytest.mark.parametrize("path", MAINTAINED)
def test_every_maintained_world_draws_a_five_square_window(path):
    """Every maintained config sets `local_view_size: 5` and senses at range <= 1.

    So every one of them draws a 5 x 5 window at a 96 px square -- the approved
    design's own frame -- and the two 5x5 worlds reach that window by being
    smaller than it rather than by a different rule.
    """
    ctx = _ctx(path)
    lay = pack(ctx)
    assert lay.view_cells == 5
    assert lay.cell_px == 96.0
    assert lay.step == ("whole_world" if ctx.world_w <= 5 else "local_window")


def test_leftover_height_never_reaches_the_arena():
    """Two worlds of the same size but different panel loads get the same arena."""
    a = pack(_synthetic(10))
    b = pack(_synthetic(10, location=True))
    assert a.arena_grid.w == b.arena_grid.w == L.ARENA_PX
    assert a.cards["arena"] == b.cards["arena"]


# --------------------------------------------------------------------------
# The geometry the plan pins, to the pixel -- now once, not per world
# --------------------------------------------------------------------------
def test_the_pinned_geometry_is_544_496_256():
    """Revision 27's worked numbers, which no world and no window may move."""
    lay = pack(_synthetic(10))
    card = lay.cards["arena"]
    assert (card.x, card.y, card.w, card.h) == (360, 64, 544, 544)
    assert lay.regions["right"].w == 496
    assert lay.regions["right"].w >= L.MIN_RIGHT_W
    assert lay.regions["band"].h == 256
    assert lay.regions["band"].h >= L.MIN_BAND_H
    assert lay.regions["band"].y == 624
    assert lay.regions["band"].w == 1056
    # With a band, the right column is measured against the arena's bottom edge --
    # which is now a constant rather than something the world's size moves.
    assert lay.regions["right"].h == 544


def test_the_right_column_clears_what_a_thermal_column_needs():
    lay = pack(_synthetic(10))
    need = P.PROP_H + P.EXTERO_NOC_H + P.THERMO_H + 2 * L.GAP
    assert need == 516
    assert lay.regions["right"].h - need == 28


@pytest.mark.parametrize("path", FIVE_BY_FIVE)
def test_a_5x5_maintained_world_gets_the_same_frame_as_every_other(path):
    """The case that used to be special, and is not any more.

    These worlds packed to a 314 px arena card and a 726 px right column while a
    10x10 world packed to 564 / 476. Both now pack to 544 / 496: the world is
    smaller than the window, so it is drawn whole, at the same square size as
    everything else.
    """
    lay = pack(_ctx(path))
    assert (lay.cards["arena"].w, lay.cards["arena"].h) == (544, 544)
    assert lay.arena_grid.w == L.ARENA_PX
    assert lay.view_cells == 5 and lay.cell_px == 96.0
    assert lay.step == "whole_world"
    assert lay.regions["right"].w == 496
    assert lay.band is True
    assert lay.regions["right"].h == 544
    assert lay.regions["band"].y == 624 and lay.regions["band"].h == 256
    # It fits, because a 5x5 world has no temperature system: the column carries
    # proprioception plus the extero/collision row, not five pods.
    assert P.PROP_H + P.EXTERO_NOC_H + L.GAP == 270 <= 544


# --------------------------------------------------------------------------
# Registry behaviour
# --------------------------------------------------------------------------
def test_m4_has_no_observed_nutrition_or_injury_rows():
    """CP1: the campfire world must not caption a hidden body state as observed.

    M4's observation genuinely lacks Nutrition and Injury. The rows still appear
    (user decision Q10 = show) but as hidden-state rows reading "not observed",
    which is the defect this replaces: the live renderer prints the true value
    and captions it OBS.
    """
    ctx = _ctx(M4)
    assert "Nutrition" not in ctx.breakdown
    assert "Injury" not in ctx.breakdown
    keys = {p.key for p in P.present_panels(ctx)}
    assert "nutrition" not in keys and "injury" not in keys
    assert "nutrition_hidden" in keys and "injury_hidden" in keys
    lay = pack(ctx)
    assert "nutrition_hidden" in lay.panels and "injury_hidden" in lay.panels


def test_m4_body_temperature_is_observed_but_a_world_without_it_is_hidden():
    ctx = _ctx(M4)
    body = {p.key: p for p in P.present_panels(ctx)}["body_temp"]
    assert body.kind_for(ctx) == "temp_row"

    no_obs = _synthetic(10)
    no_obs = LayoutContext(
        **{**no_obs.__dict__, "breakdown": {k: v for k, v in no_obs.breakdown.items()
                                            if k != "Body Temperature"}}
    )
    body2 = {p.key: p for p in P.present_panels(no_obs)}["body_temp"]
    assert body2.kind_for(no_obs) == "hidden_state"
    pack(no_obs)  # the hidden path must still lay out


def test_an_unregistered_breakdown_name_raises():
    ctx = _synthetic(10)
    broken = LayoutContext(
        **{**ctx.__dict__, "breakdown": {**ctx.breakdown, "Magnetoception": 3}}
    )
    with pytest.raises(ValueError, match="Magnetoception"):
        P.check_completeness(broken)
    with pytest.raises(ValueError, match="Magnetoception"):
        pack(broken)


@pytest.mark.parametrize("path", MAINTAINED)
def test_every_maintained_config_packs_and_is_complete(path):
    ctx = _ctx(path)
    P.check_completeness(ctx)
    lay = pack(ctx)
    assert not _overlapping_pairs(lay.cards)


@pytest.mark.parametrize("path", MAINTAINED)
def test_every_maintained_config_has_a_sensor_band_of_diamond_maps(path):
    """The band is where senses live, and every maintained world now fills it with maps.

    Both halves are asserted, because the distinction is the whole design: every
    maintained world DOES have a band (it observes smell and sight), and since
    2026-09-19 every one of them reads BOTH senses past the agent's own square,
    so each sense is drawn as a row of per-channel diamond maps rather than as a
    named channel row. Olfaction samples a radius-1 diamond everywhere; sight
    samples radius 1 in the two 5x5 worlds and radius 2 in the 10x10 ones. The
    range-0 case that drew named rows -- one omnidirectional whiff, one glance at
    the square underfoot -- is gone from the maintained ladder, so a band of rows
    is now the synthetic case rather than the ordinary one.

    WHAT IS ASSERTED IS THE DRAWN FORM, not merely the `has_grid_sense` flag,
    because the flag is only the switch and the form is the product. Each sense
    panel's kind must be `channel_maps` (the value the switch selects, against
    `spectrum` for smell and `cross_bars` for sight at range 0); its declared
    minimum must be a real diamond span rather than the zero width a named-row
    panel declares; and the box the packer actually hands it must hold that
    minimum at THIS world's own range, which differs between the 5x5 and 10x10
    groups. A packer that flipped the switch and went on placing row-shaped
    boxes would still fail here.
    """
    ctx = _ctx(path)
    assert ctx.band_senses == ("olfactory", "visual")
    assert ctx.grid_senses == ("olfactory", "visual")
    assert ctx.olfactory_range >= 1 and ctx.visual_range >= 1

    specs = {p.key: p for p in P.present_panels(ctx)}
    lay = pack(ctx)
    assert lay.band is True
    assert lay.parent["olfactory"] == "band" and lay.parent["visual"] == "band"

    for key in ("olfactory", "visual"):
        assert specs[key].kind_for(ctx) == "channel_maps", (
            f"{path}: {key} reads range {ctx.range_of(key)} but is drawn as "
            f"{specs[key].kind_for(ctx)!r}; a sense that samples past its own "
            f"square must be drawn as diamond maps"
        )
        want = specs[key].min_size(ctx)
        assert want.w > 0, (
            f"{path}: {key} declared a zero-width minimum, which is the "
            f"named-row declaration; diamond maps must declare the span they "
            f"need or the packer has nothing to honour"
        )
        box = lay.panels[key]
        assert box.w >= want.w and box.h >= want.h, (
            f"{path}: {key} at range {ctx.range_of(key)} declared a "
            f"{want.w}x{want.h}px diamond-map minimum but was placed in a "
            f"{box.w}x{box.h}px box"
        )


def test_toggling_a_modality_frees_exactly_its_height():
    """Switching a vital row off returns its 76 px to the column's grow panel."""
    on = _synthetic(10, location=True)
    off = _synthetic(10, location=True, intero=False)

    lay_on, lay_off = pack(on), pack(off)
    assert lay_on.cards["vitals"].h - lay_off.cards["vitals"].h == P.VITAL_ROW_H
    assert lay_off.cards["minimap"].h - lay_on.cards["minimap"].h == P.VITAL_ROW_H
    assert "intero_nociception" in lay_on.panels
    assert "intero_nociception" not in lay_off.panels


def test_the_minimap_never_grows_past_its_cap():
    for _, make in ALL_CONTEXTS:
        lay = pack(make())
        assert lay.cards["minimap"].h <= P.MINIMAP_MAX_H


def test_the_action_badge_sits_in_the_arena_title_strip_and_clears_the_grid():
    lay = pack(_synthetic(10, action=True))
    badge, grid, card = lay.panels["action_badge"], lay.arena_grid, lay.cards["arena"]
    assert badge.y + badge.h <= card.y + L.ARENA_TITLE_H
    assert not badge.intersects(grid)
    assert "action_badge" not in pack(_synthetic(10, action=False)).panels


# --------------------------------------------------------------------------
# Layout never reads episode data; the package stays drawing-free
# --------------------------------------------------------------------------
def test_real_available_is_identical_for_two_contexts_of_one_run():
    """Every episode of a run shares params, so the REAL slot cannot move."""
    params = _params("configs/environment/experiment/basic/06-sensory_noise_10x10.yaml")
    a = LayoutContext.from_params(params)
    b = LayoutContext.from_params(params)
    assert a.real_available == b.real_available
    assert pack(a).cards == pack(b).cards
    assert any(a.real_available.values()), "this config has noise on; expect some REAL"


def test_real_available_is_all_false_when_noise_is_off():
    params = _params("configs/environment/default.yaml")
    avail = P.real_available(params)
    assert avail and not any(avail.values())


def test_min_size_signatures_take_only_a_layout_context():
    """Layout may not read episode data. Pinned by inspecting the signatures."""
    import inspect

    for panel in P.PANELS:
        sig = inspect.signature(panel.min_size)
        assert len(sig.parameters) == 1, f"{panel.key}.min_size takes {sig}"
    assert list(inspect.signature(P.present_cards).parameters) == [
        "ctx", "band", "compact",
    ]


def test_the_window_is_decided_from_params_and_never_from_episode_data():
    """The window follows the AGENT per frame, but its SIZE is fixed per episode.

    That split is what keeps a concatenated video honest: `window_cells` takes a
    LayoutContext (built from params) and nothing else, so two episodes of one run
    cannot draw different-sized windows, while `EpisodeRenderer.view_origin` --
    which does read the agent's position -- only ever moves the window, never
    resizes it.
    """
    import inspect

    assert list(inspect.signature(L.window_cells).parameters) == ["ctx"]
    a = _synthetic(10, local_view=7)
    assert pack(a).view_cells == pack(a).view_cells == 7


def test_the_package_imports_without_matplotlib():
    """Phase 1 has no painters; importing it must not pull in a drawing stack."""
    code = (
        "import sys; import src.environment.dashboard as d; "
        "print('matplotlib' in sys.modules)"
    )
    out = subprocess.run(
        [sys.executable, "-c", code], cwd=_ROOT, capture_output=True, text=True
    )
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == "False", "importing the dashboard package loaded matplotlib"


def test_recording_flag_is_confined_to_the_dashboard_package():
    """`_recording_flag` is absence-shaped compat for recordings, never for configs.

    The contract is that nothing outside this package *imports or calls* it --
    treating a missing attribute as "absent" is right for an archived recording
    and wrong for a live config, where a missing key must raise.

    This reads the AST rather than grepping the text, because several Phase 0
    scripts legitimately mention the name in a comment or an error message. A
    prose mention is not a use, and a text grep cannot tell the two apart.
    """
    import ast

    hits = []
    for sub in ("src", "scripts"):
        for dirpath, _dirs, files in os.walk(os.path.join(_ROOT, sub)):
            if "dashboard" in dirpath or "__pycache__" in dirpath:
                continue
            for fn in files:
                if not fn.endswith(".py"):
                    continue
                path = os.path.join(dirpath, fn)
                with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                    src = fh.read()
                if "_recording_flag" not in src:
                    continue
                try:
                    tree = ast.parse(src)
                except SyntaxError:  # pragma: no cover - not our file to fix
                    continue
                rel = os.path.relpath(path, _ROOT)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Name) and node.id == "_recording_flag":
                        hits.append(f"{rel}: reference")
                    elif isinstance(node, ast.Attribute) and node.attr == "_recording_flag":
                        hits.append(f"{rel}: attribute access")
                    elif isinstance(node, ast.ImportFrom) and any(
                        a.name == "_recording_flag" for a in node.names
                    ):
                        hits.append(f"{rel}: import")
                    elif isinstance(node, ast.FunctionDef) and node.name == "_recording_flag":
                        hits.append(f"{rel}: a second definition")
    assert not hits, f"_recording_flag used outside the dashboard package: {hits}"


def test_a_recording_missing_a_flag_reads_as_absent_not_as_false():
    class Old:
        pass

    assert P._recording_flag(Old(), "thermal_enabled") is P.ABSENT
    assert not P._recording_flag(Old(), "thermal_enabled")
    assert P.real_available(Old()) == {}


def test_the_campfire_worlds_columns_are_pinned():
    """The tightest real budget in the project, named so a failure explains itself.

    The campfire thermal world and the sensory-noise world have a temperature
    system AND both senses, so they are what any change to the sense panels is
    felt by first. The margin is 28 px rather than the 48 px this test recorded
    before Revision 27, and the reason is worth stating: the arena card grew from
    the 564 px a 10x10 world used to produce to a constant 544 px, so the right
    column -- measured against the arena's bottom edge -- lost 20 px. It gained
    the property that it can never move again.
    """
    ctx = _ctx(M4)
    # `band=True` is what `pack()` selects for this world (see `_candidates`).
    right = [c for c in P.present_cards(ctx, band=True) if c.region == "right"]
    assert {c.key for c in right} == {
        "proprioception", "extero_nociception", "collision", "thermoception"}, (
        "the campfire world's right column after the senses moved to the band")

    need = P.PROP_H + P.EXTERO_NOC_H + P.THERMO_H + 2 * L.GAP
    lay = pack(ctx)
    avail = lay.regions["right"].h
    assert need == 516
    assert avail == 544, "with a band, the right column stops at the arena's bottom"
    assert avail - need == 28, (
        f"the recorded margin is 28px; this run has {avail - need}px")

    # The thermoception card is the column's only grower, so the slack lands
    # there and the column bottom-aligns with the arena at y = 608.
    assert lay.cards["thermoception"].h == P.THERMO_H + 28 == 258
    assert lay.cards["thermoception"].bottom == lay.cards["arena"].bottom == 608

    # The band, which is where the pressure moved to.
    band = lay.regions["band"]
    assert (band.x, band.y, band.w, band.h) == (360, 624, 1056, 256)
    olf, vis = lay.panels["olfactory"], lay.panels["visual"]
    assert (olf.x, olf.y, olf.w, olf.h) == (360, 624, 520, 256)
    assert (vis.x, vis.y, vis.w, vis.h) == (896, 624, 520, 256)
    assert max(P.OLF_ROWS_H, P.VISUAL_ROWS_H) == 232 <= band.h, (
        "the taller channel-row panel must fit the band")


def test_the_channel_row_heights_agree_with_the_painter_that_draws_them():
    """Layout's two height constants are arithmetic ON the painter's pitches.

    They are declared in `panels.py` because layout may not import a drawing
    module, which makes them exactly the kind of number that drifts from the
    thing it describes. So the arithmetic is redone here from the painter's own
    constants: a 64 px title strip, the taller column's rows at that sense's
    pitch, and a 16 px footer.
    """
    from src.environment.dashboard import painters as PN

    for sense, key, n_channels, pinned in (
        ("Olfaction", "olfactory", 5, P.OLF_ROWS_H),
        ("Visual", "visual", 8, P.VISUAL_ROWS_H),
    ):
        per_col = (n_channels + 1) // 2
        assert 64 + per_col * PN.CHANNEL_ROW_PITCH[sense] + 16 == pinned, (
            f"{key}: {per_col} rows at {PN.CHANNEL_ROW_PITCH[sense]}px no longer "
            f"makes the pinned {pinned}px")
