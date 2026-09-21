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
is drawn at. Three counts have to agree for that to hold, and each was wrong:

  * HOW MANY MAPS. Vision has eight channels but draws only SIX maps, because
    the three terrain channels (grass / sand / plain) are one categorical map --
    a square is one of the three, never two. The registry counted channels.
  * THE GAP between two maps. The painter leaves 6 px; the registry allowed 8.
  * THE CARD'S PADDING. `episode.py` hands the painter the panel's width minus
    `2 * PAD`, so the registry's number has to be the painter's requirement PLUS
    that padding. It did not include it.

WHY THE SECOND TEST EXISTS. The first test computes the painter's requirement
from the painter's own map plan and its own gap constant -- but it is still
arithmetic, and arithmetic that mirrors the code it checks can be wrong in the
same direction as the code. The second test therefore RUNS the painter: it draws
a real sense panel at exactly the declared width (must not raise) and at one
pixel less (must raise). That is the claim stated in the only terms that cannot
be re-derived wrongly -- the painter's own verdict on its own geometry.
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
from src.environment.dashboard.labels import channel_labels  # noqa: E402
from src.environment.dashboard.layout import LayoutOverflowError, pack  # noqa: E402

#: `(panel key, channel count, colour stops)` per sense, exactly as `episode.py`
#: passes them to the painter.
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
CASES = [(s, r) for s in SENSES for r in RANGES]
IDS = [f"{s.lower()}_r{r}" for s, r in CASES]


def _ctx(sense, r, *, visual_vector_size=8, olfactory_channels=5):
    """A context with ONE sense drawn as maps, for the registry to size."""
    key = SENSES[sense][0]
    return P.LayoutContext(
        world_w=10, world_h=10, local_view_size=5, breakdown={},
        thermal=False, intero_noc_enabled=False,
        olfactory_range=r if key == "olfactory" else 0,
        visual_range=r if key == "visual" else 0,
        visual_vector_size=visual_vector_size,
        olfactory_channels=olfactory_channels,
    )


def _declared_w(sense, r, **kw):
    """What the registry tells the packer this sense's panel needs."""
    ctx = _ctx(sense, r, **kw)
    fn = P._olf_min_size if SENSES[sense][0] == "olfactory" else P._visual_min_size
    return fn(ctx).w


def _painter_map_count(sense, n_channels):
    """How many maps the painter DRAWS -- asked of the painter, not assumed."""
    return len(PN.map_plan(sense, channel_labels(sense, n_channels)))


def _painter_needs_w(sense, r, n_channels=None):
    """The panel width the painter requires, built from the painter's own terms.

    `episode.py` gives the painter `panel.w - 2 * PAD`, and the painter fits
    `n` maps of `2r+1` squares into it with `MAP_GAP` between them, refusing any
    square under 10 px. Invert that.
    """
    n_channels = SENSES[sense][1] if n_channels is None else n_channels
    n = _painter_map_count(sense, n_channels)
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
    the map count and the gap alone. Everything that DOES participate is the
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


def _paint(sense, r, panel_w, panel_h=400, n_channels=None):
    """Draw one sense panel at `panel_w`, the way `episode.py` would.

    Raises `LayoutOverflowError` exactly when the painter judges the panel too
    narrow. `panel_h` is generous on purpose so WIDTH is what binds. `n_channels`
    defaults to the standard width for that sense; a caller working from a real
    config passes that config's own channel count, because the map plan -- and so
    the width the painter demands -- is built from it.
    """
    from src.environment.sensor import get_visual_offsets

    codes = channel_labels(sense, SENSES[sense][1] if n_channels is None
                           else n_channels)
    stops = SENSES[sense][2]
    offsets = [tuple(o) for o in get_visual_offsets(r)]
    fig = plt.figure(figsize=(16, 4), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1600)
    ax.set_ylim(panel_h, 0)
    ax.set_axis_off()
    # The painters draw in PIXELS, and read the card's pixel size back off the
    # Axes -- `episode.py` tags every card Axes with `_px_w`/`_px_h` before any
    # painter touches it (`episode.py:304`). A bare Axes has no such attribute,
    # so the colour ramp in the sense's title strip raises `AttributeError`
    # before the geometry under test is ever reached. Tagged here for the same
    # reason and with the same meaning; neither number enters the map-square
    # arithmetic this file is about.
    ax._px_w, ax._px_h = 1600, panel_h
    try:
        PN.build_channel_maps(_StubDash(), ax, 0, panel_w - 2 * PN.PAD, panel_h,
                              sense, sense, codes, stops, offsets, r)
    finally:
        plt.close(fig)


# ---------------------------------------------------------------------------
# the property
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("sense,r", CASES, ids=IDS)
def test_the_declared_minimum_is_exactly_what_the_painter_needs(sense, r):
    declared = _declared_w(sense, r)
    needed = _painter_needs_w(sense, r)
    assert declared == needed, (
        f"{sense} at range {r}: the registry declares {declared}px but the "
        f"painter needs {needed}px "
        f"({_painter_map_count(sense, SENSES[sense][1])} maps of {2 * r + 1} "
        f"squares, {PN.MAP_GAP}px gaps, {2 * PN.PAD}px card padding). "
        f"A declaration above the requirement makes the packer refuse a frame "
        f"the painter would draw; one below it hands the painter a panel it "
        f"refuses."
    )


@pytest.mark.parametrize("sense,r", CASES, ids=IDS)
def test_the_painter_draws_at_the_declared_minimum_and_refuses_one_pixel_less(sense, r):
    """The painter's own verdict, not arithmetic about it."""
    declared = _declared_w(sense, r)
    _paint(sense, r, declared)  # must not raise
    with pytest.raises(LayoutOverflowError):
        _paint(sense, r, declared - 1)


def test_vision_declares_six_maps_because_terrain_is_one_map():
    """Eight channels, six maps: grass/sand/plain are one categorical map."""
    assert _painter_map_count("Visual", 8) == 6
    assert _painter_map_count("Olfaction", 5) == 5


def test_an_off_standard_vision_width_is_declared_one_map_per_channel():
    """The composite is keyed to the standard eight channels in standard order.

    Any other width gets one map per channel -- the painter's rule -- so the
    declaration must follow it rather than hardcode six.
    """
    assert _painter_map_count("Visual", 4) == 4
    assert _declared_w("Visual", 1, visual_vector_size=4) == _painter_needs_w(
        "Visual", 1, n_channels=4)


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
# the product: the two configs this fix exists for
# ---------------------------------------------------------------------------
#: `(config, expected olfactory radius, expected visual radius)`. The radii are
#: spelled out rather than read off the config, and the test fails if they do not
#: match, because the ID of each case names the condition it is supposed to
#: exercise. THIS IS THE LESSON OF 2026-09-21: both cases used to name a config
#: that a later commit deleted, and the body skipped on a missing file -- so this
#: regression sat with ZERO live coverage while its two cases reported green.
#: A condition that silently stops being tested is worse than one that was never
#: tested, because the green tick is read as proof. Neither a missing file nor a
#: config that has drifted off the condition may read as a pass here.
WIDE_SENSE_CONFIGS = [
    # Level 05, the campfire thermal world. It needs no override any more: the
    # project default moved to olfaction 1 / vision 2 on 2026-09-19, which is
    # exactly the condition the deleted `..._olf1_vis2.yaml` used to create.
    ("configs/environment/experiment/basic/05-campfire_thermal_10x10.yaml", 1, 2),
    # Vision at radius 3 -- the condition this whole fix exists for, and the
    # widest sense panel the packer is ever asked to place. No maintained world
    # reads sight that far, so the condition is held by a test fixture of our own
    # rather than by a rung of the ladder, which is free to move again.
    ("tests/env/fixtures/dashboard_band_vis3.yaml", 1, 3),
]


@pytest.mark.parametrize("cfg,olf_r,vis_r", WIDE_SENSE_CONFIGS,
                         ids=["olf1_vis2", "olf1_vis3"])
def test_a_world_that_reads_both_senses_wide_packs_and_paints(cfg, olf_r, vis_r):
    """Vision at range 3 is drawable; before this fix the packer refused it."""
    path = _ROOT / cfg
    assert path.exists(), (
        f"{cfg} is not on disk. This case is the only live coverage of the "
        f"band-width fix at olfaction {olf_r} / vision {vis_r}; if the config "
        f"moved, repoint the case at a world that reads both senses that far "
        f"(or a fixture under tests/env/fixtures/). Do not delete the case, and "
        f"do not skip on a missing file -- that is how this coverage was lost."
    )
    from src.environment.config_loader import load_env_config, load_env_params

    ctx = P.LayoutContext.from_params(load_env_params(load_env_config(str(path))))
    assert (ctx.olfactory_range, ctx.visual_range) == (olf_r, vis_r), (
        f"{cfg} now reads olfaction {ctx.olfactory_range} / vision "
        f"{ctx.visual_range}, not the {olf_r} / {vis_r} this case is named for. "
        f"It would still pass, but it would no longer test the condition."
    )
    lay = pack(ctx)
    for sense, (key, _n, _stops) in SENSES.items():
        box = lay.panels[key]
        # The channel counts come from the CONFIG, not from `SENSES`: the map
        # plan the painter builds -- and therefore the width it demands -- is
        # built from however many channels this world's sensor actually returns.
        if key == "olfactory":
            r, n = ctx.olfactory_range, ctx.olfactory_channels
        else:
            r, n = ctx.visual_range, ctx.visual_vector_size
        assert box.w >= _painter_needs_w(sense, r, n_channels=n), (
            f"{cfg}: {key} got {box.w}px, painter needs "
            f"{_painter_needs_w(sense, r, n_channels=n)}px at range {r} "
            f"with {n} channels"
        )
        _paint(sense, r, box.w, panel_h=box.h, n_channels=n)
