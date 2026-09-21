"""The sensor band's DECLARED width must be the width the painter really needs.

WHAT THIS FILE IS FOR, IN PLAIN WORDS. Two different pieces of code decide how
wide a sense panel has to be, and until 2026-09-18 they disagreed. The layout
registry (`panels.py`) tells the packer "vision needs N pixels"; the packer then
either hands out that much room or REFUSES to lay the frame out at all. The
painter (`painters.py`) is what actually draws the little diamond maps, and it
has its own floor: a map square below 10 px is unreadable, so it raises rather
than draw one. If the registry asks for MORE than the painter needs, the packer
refuses a frame the painter would have drawn perfectly well -- which is what
happened to vision at range 3. If it asks for LESS, the packer hands out a box
the painter then refuses -- the same failure from the other side, and that is
what olfaction was one `2 * PAD` away from.

So the property asserted here is an EQUALITY, not an inequality: what the
registry declares is exactly what the painter needs, at every range either sense
is drawn at.

THE EQUALITY NOW HAS TWO REGIMES, AND BOTH ARE TESTED. Since channel names became
config data, how many map SLOTS a panel is sized for depends on where the names
came from:

  * CONFIGURED -- the recording carries names, so the panel is a FIXED size:
    five slots for smell, six for vision, whatever the run's channel count. A
    one-channel run draws one map and leaves the rest blank.
  * LEGACY -- the recording predates channel names, so it has no merge group and
    draws one map per channel. Its panel is sized to `max(slots, drawn)`, which
    is WIDER than the fixed size at eight channels.

They are different functions of the channel count, so an equality proved on one
says nothing about the other.

WHY THE SECOND TEST EXISTS. The first test computes the painter's requirement
from the painter's own map plan and its own gap constant -- but it is still
arithmetic, and arithmetic that mirrors the code it checks can be wrong in the
same direction as the code. The second test therefore RUNS the painter: it draws
a real sense panel at exactly the declared width (must not raise) and at one
pixel less (must raise). That is the claim stated in the only terms that cannot
be re-derived wrongly -- the painter's own verdict on its own geometry.

WHY NOTHING HERE NAMES A CONFIG FILE ANY MORE. This gate has now gone dark TWICE
because a config it pointed at moved: `4b6f7196`'s own history, and again at
`47b1b8c3`, which deleted both `WIDE_SENSE_CONFIGS` entries and left the two
cases that exercised a wide sense panel silently SKIPPING while reporting green.
A gate that skips when its subject disappears is indistinguishable from a gate
that passes. Every case below is therefore built IN MEMORY from literals, there
is no `pytest.skip` anywhere in this file, and absence of a subject is impossible
rather than merely discouraged.
"""
import os
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

os.environ.setdefault("JAX_PLATFORMS", "cpu")

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from src.environment.dashboard import painters as PN  # noqa: E402
from src.environment.dashboard import palette as PAL  # noqa: E402
from src.environment.dashboard import panels as P  # noqa: E402
from src.environment.dashboard.labels import (  # noqa: E402
    ChannelDisplay,
    PANEL_MAP_SLOTS,
    map_plan,
    panel_map_slots,
)
from src.environment.dashboard.layout import LayoutOverflowError, pack  # noqa: E402

#: `(panel key, conventional channel count, colour stops)` per sense, exactly as
#: `episode.py` passes them to the painter.
SENSES = {
    "Olfaction": ("olfactory", 5, PAL.OLF_STOPS),
    "Visual": ("visual", 8, PAL.VIS_STOPS),
}

#: The painter's own floor, written as the literal it is at `painters.py`'s
#: `if cs < 10: raise`. Deliberately NOT read from `panels.MAP_CELL_MIN_PX` --
#: that constant is half of what this file is checking, and a test that takes its
#: expected value from the thing under test asserts nothing. A test below pins
#: the two together, so a change to either is still caught.
PAINTER_CELL_FLOOR_PX = 10

RANGES = (1, 2, 3)
REGIMES = ("configured", "legacy")
CASES = [(s, r, g) for s in SENSES for r in RANGES for g in REGIMES]
IDS = [f"{s.lower()}_r{r}_{g}" for s, r, g in CASES]


# ---------------------------------------------------------------------------
# displays, built from literals
# ---------------------------------------------------------------------------
def _names(n):
    return [{"name": f"Ch{i}", "qualifier": ""} for i in range(n)]


TERRAIN = {"name": "Terrain", "channels": [0, 1, 2]}


def _display(sense, n, *, regime="configured", groups=None):
    """One sense's display. `configured` carries names; `legacy` carries none."""
    if regime == "legacy":
        return ChannelDisplay.from_meta(sense, n, None, key_present=False)
    if groups is None:
        groups = [TERRAIN] if (sense == "Visual" and n >= 3) else []
    return ChannelDisplay.from_meta(
        sense, n, {"names": _names(n), "groups": groups}, key_present=True)


def _payload(vis_n, olf_n=5, *, vis_groups=None):
    """The raw `run_meta` payload a CONFIGURED recording would carry."""
    if vis_groups is None:
        vis_groups = [TERRAIN] if vis_n >= 3 else []
    return {
        "Olfaction": {"names": _names(olf_n), "groups": []},
        "Visual": {"names": _names(vis_n), "groups": vis_groups},
    }


def _ctx(sense, r, *, visual_vector_size=8, olfactory_channels=5,
         channel_display=None):
    """A context with ONE sense drawn as maps, for the registry to size."""
    key = SENSES[sense][0]
    return P.LayoutContext(
        world_w=10, world_h=10, local_view_size=5, breakdown={},
        thermal=False, intero_noc_enabled=False,
        olfactory_range=r if key == "olfactory" else 0,
        visual_range=r if key == "visual" else 0,
        visual_vector_size=visual_vector_size,
        olfactory_channels=olfactory_channels,
        channel_display=channel_display,
    )


def _full_ctx(*, vis_channels, vis_range, olf_channels=5, olf_range=1,
              channel_display=None):
    """A context complete enough to PACK -- both senses present in the band."""
    return P.LayoutContext(
        world_w=10, world_h=10, local_view_size=5,
        breakdown={"Satiation": 1,
                   "Olfaction": P._diamond_cells(olf_range) * olf_channels,
                   "Visual": P._diamond_cells(vis_range) * vis_channels,
                   "Collision": 5, "Proprioception": 4},
        thermal=False, intero_noc_enabled=False,
        olfactory_range=olf_range, visual_range=vis_range,
        visual_vector_size=vis_channels, olfactory_channels=olf_channels,
        channel_display=channel_display,
    )


def _declared_w(sense, r, *, regime="configured", n_channels=None):
    """What the registry tells the packer this sense's panel needs."""
    n = SENSES[sense][1] if n_channels is None else n_channels
    key = SENSES[sense][0]
    payload = None if regime == "legacy" else _payload(
        n if key == "visual" else 8, n if key == "olfactory" else 5)
    ctx = _ctx(sense, r,
               visual_vector_size=n if key == "visual" else 8,
               olfactory_channels=n if key == "olfactory" else 5,
               channel_display=payload)
    fn = P._olf_min_size if key == "olfactory" else P._visual_min_size
    return fn(ctx).w


def _painter_map_count(sense, display):
    """How many maps the painter DRAWS -- asked of the painter, not assumed."""
    return len(map_plan(sense, display))


def _painter_needs_w(sense, r, display):
    """The panel width the painter requires, built from the painter's own terms.

    `episode.py` gives the painter `panel.w - 2 * PAD`, and the painter divides
    it into `panel_map_slots` slots of `2r+1` squares with `MAP_GAP` between
    them, refusing any square under 10 px. Invert that. NOTE it is the SLOT
    count, not the map count -- that is what makes blank space appear instead of
    one stretched map.
    """
    n = panel_map_slots(sense, display)
    cells = 2 * r + 1
    return (n * cells * PAINTER_CELL_FLOOR_PX
            + PN.MAP_GAP * (n - 1)
            + 2 * PN.PAD)


# ---------------------------------------------------------------------------
# running the painter for real
# ---------------------------------------------------------------------------
class _Setter:
    """Stands in for the text fitter's return value: `.set(s)` yields a width."""

    def set(self, s):
        return 10.0


class _StubDash:
    """The handful of services `build_channel_maps` asks of its renderer.

    Text measurement is stubbed to a constant because none of it participates in
    the geometry under test -- the map squares are sized from the panel width,
    the slot count and the gap alone. Everything that DOES participate is the
    painter's own code, running unmodified.
    """

    def __init__(self):
        self.updates = []
        self.sense_max = {}

    def fit(self, ax, x, y, role, max_w, numeric=True, **kw):
        return _Setter()

    def width(self, s, role):
        return 10.0

    def viz_name(self, name):
        return name


def _paint(sense, r, panel_w, panel_h=400, display=None):
    """Draw one sense panel at `panel_w`, the way `episode.py` would.

    Raises `LayoutOverflowError` exactly when the painter judges the panel too
    narrow. `panel_h` is generous on purpose so WIDTH is what binds.
    """
    from src.environment.sensor import get_visual_offsets

    if display is None:
        display = _display(sense, SENSES[sense][1])
    stops = SENSES[sense][2]
    offsets = [tuple(o) for o in get_visual_offsets(r)]
    fig = plt.figure(figsize=(16, 4), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1600)
    ax.set_ylim(panel_h, 0)
    ax.set_axis_off()
    # The painters draw in PIXELS, and read the card's pixel size back off the
    # Axes -- `episode.py` tags every card Axes with `_px_w`/`_px_h` before any
    # painter touches it. A bare Axes has no such attribute, so the colour ramp
    # in the sense's title strip raises `AttributeError` before the geometry
    # under test is ever reached. Tagged here for the same reason and with the
    # same meaning; neither number enters the map-square arithmetic.
    ax._px_w, ax._px_h = 1600, panel_h
    try:
        PN.build_channel_maps(_StubDash(), ax, 0, panel_w - 2 * PN.PAD, panel_h,
                              sense, sense, display, stops, offsets, r)
    finally:
        plt.close(fig)


# ---------------------------------------------------------------------------
# the property, in BOTH sizing regimes
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("sense,r,regime", CASES, ids=IDS)
def test_the_declared_minimum_is_exactly_what_the_painter_needs(sense, r, regime):
    n = SENSES[sense][1]
    display = _display(sense, n, regime=regime)
    declared = _declared_w(sense, r, regime=regime)
    needed = _painter_needs_w(sense, r, display)
    assert declared == needed, (
        f"{sense} at range {r} ({regime}): the registry declares {declared}px but "
        f"the painter needs {needed}px "
        f"({panel_map_slots(sense, display)} slots of {2 * r + 1} squares, "
        f"{PN.MAP_GAP}px gaps, {2 * PN.PAD}px card padding). "
        f"A declaration above the requirement makes the packer refuse a frame "
        f"the painter would draw; one below it hands the painter a panel it "
        f"refuses."
    )


@pytest.mark.parametrize("sense,r,regime", CASES, ids=IDS)
def test_the_painter_draws_at_the_declared_minimum_and_refuses_one_pixel_less(
        sense, r, regime):
    """The painter's own verdict, not arithmetic about it."""
    display = _display(sense, SENSES[sense][1], regime=regime)
    declared = _declared_w(sense, r, regime=regime)
    _paint(sense, r, declared, display=display)  # must not raise
    with pytest.raises(LayoutOverflowError):
        _paint(sense, r, declared - 1, display=display)


def test_vision_declares_six_maps_because_terrain_is_one_map():
    """Eight channels, six maps: grass/sand/plain are one categorical map."""
    assert _painter_map_count("Visual", _display("Visual", 8)) == 6
    assert _painter_map_count("Olfaction", _display("Olfaction", 5)) == 5


def test_an_off_standard_vision_width_gets_the_SAME_panel_not_one_map_per_channel():
    """REWRITTEN, because the old claim became false.

    This case used to assert "4 channels => 4 maps", which was the pre-change
    rule: the panel followed the live channel count. It no longer does, and that
    is the whole point of the change -- so the case is rewritten rather than
    updated, in both regimes:

      * CONFIGURED: 4 channels draw 4 maps into a panel still sized for SIX
        slots. The two spare slots are blank BY DESIGN.
      * LEGACY: 4 channels draw 4 maps and are sized `max(6, 4)` = 6 as well.

    A four-channel run and an eight-channel run therefore get identical panels,
    which is the comparability the fixed size exists to provide.
    """
    configured4 = _display("Visual", 4, groups=[])
    assert _painter_map_count("Visual", configured4) == 4
    assert panel_map_slots("Visual", configured4) == PANEL_MAP_SLOTS["Visual"] == 6

    legacy4 = _display("Visual", 4, regime="legacy")
    assert _painter_map_count("Visual", legacy4) == 4
    assert panel_map_slots("Visual", legacy4) == 6

    assert (_declared_w("Visual", 1, n_channels=4)
            == _declared_w("Visual", 1, n_channels=8))


def test_a_legacy_eight_channel_panel_is_WIDER_than_a_configured_one():
    """The deliberate asymmetry, asserted so it cannot be "simplified" away: a
    legacy recording carries no merge group, so it draws 8 maps and is sized for
    8. Using the fixed six here would overflow every recording on disk."""
    assert panel_map_slots("Visual", _display("Visual", 8, regime="legacy")) == 8
    assert panel_map_slots("Visual", _display("Visual", 8)) == 6
    assert _declared_w("Visual", 2, regime="legacy") > _declared_w("Visual", 2)


def test_the_gap_between_two_maps_is_one_constant_not_two():
    """Registry and painter must read the SAME number, not two equal numbers.

    Equality alone would not say that: two separately written `6`s are equal
    today and drift apart the first time one of them is tuned (they were `6` and
    `8` until this fix). So the structure is asserted too -- the painter takes
    the registry's constant by import rather than declaring its own.
    """
    assert PN.MAP_GAP == P.MAP_GAP_PX
    src = Path(PN.__file__).read_text()
    assert "MAP_GAP_PX as MAP_GAP" in src, (
        "painters.py declares its own map gap again; it must import the "
        "registry's `MAP_GAP_PX`, or the two can disagree about how wide a "
        "sense panel has to be"
    )


def test_the_painters_cell_floor_matches_the_registrys():
    """The 10 px this file expects is the 10 px both sides actually use."""
    assert P.MAP_CELL_MIN_PX == PAINTER_CELL_FLOOR_PX
    src = Path(PN.__file__).read_text()
    assert "if cs < 10:" in src, (
        "the painter's map-square floor moved; this file's expected value and "
        "`panels.MAP_CELL_MIN_PX` both have to move with it"
    )


# ---------------------------------------------------------------------------
# the product: a world that reads BOTH senses wide, built in memory
# ---------------------------------------------------------------------------
#: What the band actually grants one of two sense panels, measured from the
#: packer's own geometry rather than copied: the band is
#: `CANVAS_W - OUTER - cx` wide, its two children split that with one `GAP`
#: between them. Asserted below so the three cases' arithmetic is anchored to
#: something real.
EXPECTED_GRANT_PX = 520


def test_the_band_grants_each_of_two_senses_the_width_these_cases_assume():
    lay = pack(_full_ctx(vis_channels=8, vis_range=2,
                         channel_display=_payload(8)))
    assert lay.panels["visual"].w == EXPECTED_GRANT_PX, (
        f"the band grant moved to {lay.panels['visual'].w}px; the three "
        f"wide-sense cases below are written against {EXPECTED_GRANT_PX}px")


def test_a_configured_world_reading_both_senses_wide_packs_and_paints():
    """CONFIGURED, vision at range 3. Six slots need 482 px of the 520 granted.

    Range 3 is the condition the band-width fix exists for and the widest sense
    panel the packer is ever asked to place. No maintained world reads sight that
    far, so the condition is held HERE, in memory, where no commit can delete it.
    """
    ctx = _full_ctx(vis_channels=8, vis_range=3, channel_display=_payload(8))
    display = _display("Visual", 8)
    assert panel_map_slots("Visual", display) == 6
    assert _painter_needs_w("Visual", 3, display) == 482

    lay = pack(ctx)
    box = lay.panels["visual"]
    assert box.w >= 482
    _paint("Visual", 3, box.w, panel_h=box.h, display=display)

    olf = _display("Olfaction", 5)
    obox = lay.panels["olfactory"]
    assert obox.w >= _painter_needs_w("Olfaction", 1, olf)
    _paint("Olfaction", 1, obox.w, panel_h=obox.h, display=olf)


def test_an_eight_channel_LEGACY_world_at_range_three_is_refused_and_says_why():
    """The mirror, and the reason the refusal is stated as NEED versus GRANT.

    A legacy recording draws one map per channel, so eight channels at range 3
    need 634 px against the 520 px the band grants. It genuinely does not fit.
    The refusal must name the reason and the remedy -- re-record it, which
    regenerates it with names and the terrain merge and brings it back inside
    the panel -- rather than surfacing as a bare packer error.
    """
    display = _display("Visual", 8, regime="legacy")
    assert panel_map_slots("Visual", display) == 8
    assert _painter_needs_w("Visual", 3, display) == 634
    assert 634 > EXPECTED_GRANT_PX

    ctx = _full_ctx(vis_channels=8, vis_range=3, channel_display=None)
    with pytest.raises(LayoutOverflowError):
        pack(ctx)

    with pytest.raises(LayoutOverflowError) as exc:
        P.pack_or_explain(ctx)
    msg = str(exc.value).lower()
    assert "re-record" in msg, f"the refusal must name the remedy. Got: {msg}"
    assert "634" in str(exc.value) and "520" in str(exc.value), (
        f"the refusal must name what it needed and what it was granted. "
        f"Got: {exc.value}")


def test_a_ONE_channel_legacy_world_at_range_three_still_renders():
    """THE CASE THAT STOPS THE REFUSAL BEING KEYED ON RANGE.

    A one-channel legacy recording at range 3 is sized `max(6, 1)` = 6 maps, so
    it needs 482 px and fits comfortably. Since the default moved to
    single-channel vision this is an ordinary thing to have, and a `range >= 3`
    rule would refuse a recording that renders perfectly well.
    """
    display = _display("Visual", 1, regime="legacy")
    assert panel_map_slots("Visual", display) == 6
    assert _painter_needs_w("Visual", 3, display) == 482

    ctx = _full_ctx(vis_channels=1, vis_range=3, channel_display=None)
    lay = P.pack_or_explain(ctx)          # must NOT raise
    box = lay.panels["visual"]
    _paint("Visual", 3, box.w, panel_h=box.h, display=display)
