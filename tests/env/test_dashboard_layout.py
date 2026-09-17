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
deleted. This plan has already been bitten by exactly that: an earlier phase's
audit suite passed all 18 of its tests when the ink measurement was mutated to
flag every pixel on the canvas.

SYNTHETIC VERSUS REAL CONTEXTS. Some geometry the plan pins cannot be reached by
any config this project maintains. Every maintained world reads both senses at
range 0, so none of them produces the **diamond-map** band that the pinned
564 / 476 / 236 geometry is measured on, and that case exists only as a synthetic
``LayoutContext``. Tests that use one say so in their name and docstring, so a
later reader does not go hunting for the config that produces it.

WHAT CHANGED ON 2026-09-17, because these tests asserted the opposite until then.
The band used to exist only for a sense reading past the agent's own square, so
every maintained world had NO band and its two sense panels were pushed into the
right-hand column. That left a 564 x 269 px hole under the arena in the shipped
frame and is not what the approved design shows. The band now exists whenever a
sense is observed **at any range**; what the range decides is what is drawn in it
(diamond maps at range >= 1, named channel rows at range 0).
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
    # A thin training-only override of the config above (checkpoint frequency and
    # retention). It is listed because "every maintained config packs" must mean
    # every one of the nine, not the eight anybody would think to type: an
    # override that reaches the layout would do so through `extends:`, which is
    # resolved here exactly as the trainer resolves it.
    "configs/environment/experiment/basic/03-random_init_10x10_ckpt1k.yaml",
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

    The default is the geometry the plan pins for Phase 1: a 10x10 world with a
    thermoception card *and* a sensor band. No maintained config has both -- the
    thermal worlds have the card and no band, and a band needs a sense at range
    1 or more, which no maintained config has.
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
    on what the cards are. The case it was written for (the band) cannot arise: a
    single card never pairs with itself, and a second band card is now refused in
    ``_pack_once`` before any box is handed out.

    Asserted against ``_validate`` on a hand-built Layout rather than on a packed
    one, precisely because no context can reach this state -- a test that only
    packs real configs could never see the hole.
    """
    shared = Box(100, 100, 200, 200)
    lay = L.Layout(
        cards={"a": shared, "b": shared},
        panels={},
        parent={},
        view_cells=10,
        cell_px=L.ARENA_CELL_PX,
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
        L._pack_once(ctx, 10, True, False, "test", cards + [twin])


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
        L._pack_once(ctx, 10, True, False, "test", fat)
    assert "right" in str(exc.value)


def test_a_5x5_world_with_thermal_and_a_band_raises_naming_the_right_column():
    """SYNTHETIC context -- no maintained config reaches this.

    The coupling: when a sensor band is present the right column is measured
    against the arena's bottom edge, so a SMALLER world gives the right column
    LESS height. A 5x5 world leaves it 314 px against the 516 px a thermal right
    column needs (proprioception 104 + the extero/collision row 150 +
    thermoception 230 + two 16 px gaps).
    """
    with pytest.raises(LayoutOverflowError) as exc:
        pack(_synthetic(5, local_view=5))
    assert "right" in str(exc.value).lower()


def test_a_world_too_large_to_draw_whole_still_checks_the_right_column():
    """The fallback must not land on a window that starves the right column."""
    with pytest.raises(LayoutOverflowError) as exc:
        pack(_synthetic(14, local_view=5))
    assert "right" in str(exc.value).lower()


# --------------------------------------------------------------------------
# The arena is a FIXED box, not a grow panel
# --------------------------------------------------------------------------
@pytest.mark.parametrize("name,make", ALL_CONTEXTS, ids=[n for n, _ in ALL_CONTEXTS])
def test_the_arena_draws_exactly_fifty_pixels_per_world_square(name, make):
    """The arena never absorbs leftover height and never grows to fill a column."""
    lay = pack(make())
    grid = lay.arena_grid
    expected = lay.view_cells * L.ARENA_CELL_PX
    assert grid.w == expected, f"{name}: arena width {grid.w} != {expected}"
    assert grid.h == expected, f"{name}: arena height {grid.h} != {expected}"
    assert lay.cell_px == 50


@pytest.mark.parametrize("name,make", ALL_CONTEXTS, ids=[n for n, _ in ALL_CONTEXTS])
def test_the_arena_is_square_and_shows_the_whole_world(name, make):
    ctx = make()
    lay = pack(ctx)
    card = lay.cards["arena"]
    assert card.w == card.h, f"{name}: arena card is not square: {card}"
    if ctx.world_w <= 10:
        assert lay.view_cells == ctx.world_w, (
            f"{name}: a world that fits whole at 50px must be drawn whole"
        )
        assert lay.step == "whole_world"


def test_leftover_height_never_reaches_the_arena():
    """Two worlds of the same size but different panel loads get the same arena."""
    a = pack(_synthetic(10))
    b = pack(_synthetic(10, location=True))
    assert a.arena_grid.w == b.arena_grid.w == 500
    assert a.cards["arena"] == b.cards["arena"]


# --------------------------------------------------------------------------
# The geometry the plan pins, to the pixel
# --------------------------------------------------------------------------
def test_a_10x10_world_gives_the_pinned_geometry():
    """SYNTHETIC context (thermal card + sensor band): 564 / 476 / 236.

    No maintained config produces this -- every maintained world has both sense
    ranges at 0, so none has a band. Asserted on a synthetic LayoutContext with
    thermal on and one sense at range 1.
    """
    lay = pack(_synthetic(10))
    card = lay.cards["arena"]
    assert (card.w, card.h) == (564, 564)
    assert lay.regions["right"].w == 476
    assert lay.regions["right"].w >= L.MIN_RIGHT_W
    assert lay.regions["band"].h == 236
    assert lay.regions["band"].h >= L.MIN_BAND_H
    assert lay.regions["band"].y == 644
    assert lay.regions["band"].w == 1056
    # With a band, the right column is measured against the arena's bottom edge.
    assert lay.regions["right"].h == 564


def test_the_10x10_right_column_clears_what_a_thermal_column_needs():
    lay = pack(_synthetic(10))
    need = P.PROP_H + P.EXTERO_NOC_H + P.THERMO_H + 2 * L.GAP
    assert need == 516
    assert lay.regions["right"].h - need == 48


@pytest.mark.parametrize("path", FIVE_BY_FIVE)
def test_a_5x5_maintained_world_gives_a_314_card_and_a_726_right_column(path):
    lay = pack(_ctx(path))
    card = lay.cards["arena"]
    assert (card.w, card.h) == (314, 314)
    assert lay.arena_grid.w == 250
    assert lay.regions["right"].w == 726
    # These worlds read both senses, so they have a band, and the right column is
    # therefore measured against the arena's bottom edge rather than the canvas.
    assert lay.band is True
    assert lay.regions["right"].h == 314
    assert lay.regions["band"].y == 394 and lay.regions["band"].h == 486
    # It still fits, because a 5x5 world has no temperature system: the column
    # carries proprioception plus the extero/collision row, not five pods.
    assert P.PROP_H + P.EXTERO_NOC_H + L.GAP == 270 <= 314


def test_a_smaller_world_gives_the_right_column_less_height_when_a_band_exists():
    """The coupling stated as a property, not as one worked example."""
    ten = pack(_synthetic(10))
    assert ten.band is True
    assert ten.regions["right"].h == ten.cards["arena"].h
    # The 5x5 version of the same context cannot pack at all, which is the point.
    with pytest.raises(LayoutOverflowError):
        pack(_synthetic(5))


@pytest.mark.parametrize("world", [5, 8, 10, 12, 14])
def test_one_check_covers_every_route_to_an_arena_height(world):
    """Whatever chooses the arena height, the right column is checked against it.

    The three routes are the world's own size, the whole-world rule, and the
    fallback's shrink step. Either the pack succeeds and the right column really
    does hold its panels, or it raises.
    """
    ctx = _synthetic(world, local_view=5)
    try:
        lay = pack(ctx)
    except LayoutOverflowError:
        return
    right = lay.regions["right"]
    used = [
        (k, b) for k, b in lay.cards.items()
        if b.x >= right.x and b.x + b.w <= right.x + right.w and k != "header"
    ]
    for key, box in used:
        assert box.y + box.h <= right.y + right.h + L.GAP, (
            f"world {world}: right-column card {key} {box} runs past its region {right}"
        )


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
def test_every_maintained_config_has_a_sensor_band(path):
    """The band is not a feature of long-range senses; it is where senses live.

    Both halves are asserted, because the distinction is the whole change: every
    maintained world DOES have a band (it observes smell and sight), and none of
    them has a GRID sense (both ranges are 0), so each draws named channel rows
    rather than diamond maps. That second half is also why the pinned
    564/476/236 geometry still has to be measured on a synthetic context.
    """
    ctx = _ctx(path)
    assert ctx.band_senses == ("olfactory", "visual")
    assert ctx.has_grid_sense is False
    lay = pack(ctx)
    assert lay.band is True
    assert lay.parent["olfactory"] == "band" and lay.parent["visual"] == "band"


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
    scripts legitimately mention the name in a comment or an error message
    ("Needs _recording_flag (plan section D4.1, Phase 1)"). A prose mention is
    not a use, and a text grep cannot tell the two apart.
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

    WHY THIS TEST EXISTS (plan section D1.1, added after the CP1 verification).
    The campfire thermal world and the sensory-noise world have a temperature
    system AND both senses, so they are what any change to the sense panels is
    felt by first.

    WHAT IT USED TO PIN, AND WHY THAT IS GONE. Until 2026-09-17 both senses were
    pods in the RIGHT COLUMN, which therefore carried five pods needing 800 px of
    its 816 -- a 16 px margin, the tightest in the project, and the reason the two
    range-0 pod heights were the most dangerous numbers in the layout. Moving both
    senses into the band removes that budget rather than loosening it: the right
    column now carries three pods, and the pressure moves to the band, which is
    pinned below.
    """
    ctx = _ctx(M4)
    # `band=True` is what `pack()` selects for this world (see `_candidates`);
    # the default is False, which is the arrangement this world no longer uses.
    right = [c for c in P.present_cards(ctx, band=True) if c.region == "right"]
    assert {c.key for c in right} == {
        "proprioception", "extero_nociception", "collision", "thermoception"}, (
        "the campfire world's right column after the senses moved to the band")

    need = P.PROP_H + P.EXTERO_NOC_H + P.THERMO_H + 2 * L.GAP
    lay = pack(ctx)
    avail = lay.regions["right"].h
    assert need == 516
    assert avail == 564, "with a band, the right column stops at the arena's bottom"
    assert avail - need == 48, (
        f"the recorded margin is 48px; this run has {avail - need}px")

    # The thermoception card is the column's only grower, so the slack lands
    # there and the column bottom-aligns with the arena at y = 628.
    assert lay.cards["thermoception"].h == P.THERMO_H + 48 == 278
    assert lay.cards["thermoception"].bottom == lay.cards["arena"].bottom == 628

    # The band, which is where the pressure moved to.
    band = lay.regions["band"]
    assert (band.x, band.y, band.w, band.h) == (360, 644, 1056, 236)
    olf, vis = lay.panels["olfactory"], lay.panels["visual"]
    assert (olf.x, olf.y, olf.w, olf.h) == (360, 644, 520, 236)
    assert (vis.x, vis.y, vis.w, vis.h) == (896, 644, 520, 236)
    assert max(P.OLF_ROWS_H, P.VISUAL_ROWS_H) == 232 <= band.h, (
        "the taller channel-row panel must fit the band a 10x10 world leaves")


def test_the_channel_row_heights_agree_with_the_painter_that_draws_them():
    """Layout's two height constants are arithmetic ON the painter's pitches.

    They are declared in `panels.py` because layout may not import a drawing
    module, which makes them exactly the kind of number that drifts from the
    thing it describes. So the arithmetic is redone here from the painter's own
    constants: a 64 px title strip, the taller column's rows at that sense's
    pitch, and a 16 px footer for the caption naming the scale.
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
