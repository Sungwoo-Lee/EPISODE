"""Stage 6a of the temperature system — the field, the gauge, and old recordings.

What this file checks, in plain terms. Videos of a thermal episode now show two
new things: the world's temperature painted under the grid, and the agent's own
body temperature as a gauge beside the other vitals. Three properties have to
hold or the pictures mislead rather than inform.

  1. The colour scale is FIXED for the whole episode. If it were recomputed per
     frame, a world that is steadily cooling would render as a world of constant
     appearance — the colours would track the shrinking range instead of the
     falling temperature, hiding the one thing the picture exists to show.
  2. A `.rec` file recorded before the thermal system existed must keep
     rendering EXACTLY as it does today. `RECORDING_FORMAT_VERSION` was
     deliberately not bumped, so the reader branches on whether the two thermal
     fields are present.
  3. A thermal-OFF config must render exactly the frame it rendered before this
     stage — no empty thermoception pod, no shifted panel.

These are properties a rendered frame either has or does not. A test that only
checked "render_jax_state did not raise" would pass on a colour scale that
inverts, a gauge that clips, and a panel that has silently lost its Visual pod —
all three of which happened while this stage was being written and none of which
were visible in the source.
"""
import os

os.environ.setdefault("JAX_PLATFORMS", "cpu")

import copy
import sys

import numpy as np
import pytest
import yaml

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
sys.path.insert(0, _ROOT)

import jax
import jax.numpy as jnp

from src.utils.config import Config
from src.environment.config_loader import load_env_params
from src.environment.core import jax_reset, jax_step
from src.environment.sensor import get_observation, build_sensory_viz
from src.environment.renderer import (
    render_jax_state, thermal_color_limits, _thermal_rgba,
)
from src.utils.eval_recording import _snapshot_state

THERMAL_CONFIG = os.path.join(
    _ROOT, "configs", "environment", "experiment", "archive", "thermal", "campfire_world.yaml")
DEFAULT_CONFIG = os.path.join(_ROOT, "configs", "environment", "default.yaml")

REST = 4

# The figure is a fixed 14x10 inches at dpi 100, so the arena's pixel box is
# stable across runs. Cropped generously INSIDE the arena so a one-pixel shift
# in the surrounding layout cannot make the crop test pass or fail spuriously.
_ARENA_CROP = (np.s_[250:760], np.s_[460:975])


# ── helpers ───────────────────────────────────────────────────────────────────

def _still_thermal_world():
    """A thermal world in which NOTHING moves except the agent's temperature.

    Animals are removed and the agent rests, so any pixel difference between two
    frames of the same episode is attributable to the thermal layer rather than
    to an entity having walked.
    """
    d = copy.deepcopy(yaml.safe_load(open(THERMAL_CONFIG)))
    d["environment"]["entities"] = []
    d["environment"]["obstacles"] = [
        o for o in d["environment"]["obstacles"] if o.get("name") == "campfire"]
    d["environment"]["resources"] = [
        r for r in d["environment"]["resources"] if r.get("type") == "food"]
    d["environment"]["random_start_pos"] = False
    d["environment"]["start_pos"] = [1, 1]
    d["body"]["metabolic_cost"] = 0.0
    d["body"]["with_injury"] = False
    return d


def _params(d):
    return load_env_params(Config(d))


def _frame(state, params, step, thermal_clim=None, debug=False):
    obs = get_observation(state, params, apply_noise=False)
    viz = build_sensory_viz(np.asarray(obs), state, params)
    return render_jax_state(state, params, episode=1, step=step, action=REST,
                            sensory_data=viz, icon_config=None,
                            thermal_clim=thermal_clim, debug_thermal_cells=debug)


class _Snapshot:
    """The object `scripts/eval/render_recordings.py` builds from a `.rec` file:
    a bare namespace carrying exactly the keys the snapshot dict holds."""

    def __init__(self, mapping):
        for k, v in mapping.items():
            setattr(self, k, v)


# ── 1. the colour scale is fixed for the whole episode ────────────────────────

def test_a_cooling_world_does_not_rescale_its_colours():
    """Early and late frames of a cooling episode paint the arena identically.

    The agent's body temperature falls from the setpoint towards the world's,
    which is what "cooling" means here; the WORLD's temperature is constant, so
    the arena must not change a single pixel. A colour scale that rescaled to,
    say, the body-relative range would repaint the whole arena every frame and
    this crop comparison would fail.
    """
    params = _params(_still_thermal_world())
    state = jax_reset(params, jax.random.PRNGKey(3))
    clim = thermal_color_limits(state.thermal_field, params)
    assert clim is not None

    early = _frame(state, params, 0, thermal_clim=clim)
    early_temp = float(state.body_temp)

    for t in range(15):
        state, _, done, _ = jax_step(state, REST, params)
        assert not bool(done), "the episode ended before the body had cooled"
    late = _frame(state, params, 15, thermal_clim=clim)
    late_temp = float(state.body_temp)

    assert late_temp < early_temp - 5.0, (
        f"body temperature only moved {early_temp:+.2f} -> {late_temp:+.2f}; this "
        f"test cannot distinguish a fixed scale from a rescaling one unless the "
        f"world is actually cooling the agent")

    np.testing.assert_array_equal(
        early[_ARENA_CROP], late[_ARENA_CROP],
        err_msg="the arena repainted itself between frames of one episode — the "
                "field underlay's colour limits are not fixed for the episode")
    assert not np.array_equal(early, late), (
        "the two frames are identical everywhere, including the body-temperature "
        "gauge — the gauge is not tracking the body at all")


def test_a_cells_colour_depends_only_on_its_temperature_and_the_limits():
    """The mapping is a pure function of (temperature, limits).

    This is the property that makes the scale comparable ACROSS frames: the same
    temperature must produce the same colour regardless of what else the frame
    contains. Per-frame rescaling is exactly the violation of it.
    """
    clim = (-60.0, 60.0)
    assert _thermal_rgba(0.0, clim) == _thermal_rgba(0.0, clim)
    assert _thermal_rgba(-25.0, clim) != _thermal_rgba(+25.0, clim)
    # Diverging, and the right way round: cold is blue (more blue than red),
    # hot is red. An inverted colormap is invisible in the source.
    cold = _thermal_rgba(-55.0, clim)
    hot = _thermal_rgba(+55.0, clim)
    assert cold[2] > cold[0], f"cold did not render blue: rgba={cold}"
    assert hot[0] > hot[2], f"hot did not render red: rgba={hot}"
    # Widening the limits must change the colour of a fixed temperature — which
    # is precisely why the limits have to be pinned rather than re-derived.
    assert _thermal_rgba(25.0, clim) != _thermal_rgba(25.0, (-300.0, 300.0))


def test_limits_are_symmetric_about_the_setpoint():
    """A diverging scale needs its neutral midpoint on the meaningful zero.

    That zero is `temperature_setpoint` — the value the body is defending — not
    the midpoint of whatever range the field happens to span.
    """
    params = _params(_still_thermal_world())
    state = jax_reset(params, jax.random.PRNGKey(3))
    vmin, vmax = thermal_color_limits(state.thermal_field, params)
    setpoint = float(params.temperature_setpoint)
    np.testing.assert_allclose((vmin + vmax) / 2.0, setpoint, atol=1e-5)
    field = np.asarray(state.thermal_field)
    assert vmin <= field.min() and field.max() <= vmax, (
        "the fixed limits do not cover the field, so some cells saturate")


def test_render_honours_an_explicitly_pinned_clim():
    """`thermal_clim` must actually be used, not accepted and ignored.

    The offline recording renderer pins the limits once per episode and relies
    on this; a signature that swallowed the argument would look correct in the
    source and pin nothing.
    """
    params = _params(_still_thermal_world())
    state = jax_reset(params, jax.random.PRNGKey(3))
    auto = _frame(state, params, 0, thermal_clim=None)
    pinned = _frame(state, params, 0,
                    thermal_clim=thermal_color_limits(state.thermal_field, params))
    other = _frame(state, params, 0, thermal_clim=(-500.0, 500.0))
    np.testing.assert_array_equal(
        auto, pinned,
        err_msg="passing the limits the renderer would have derived changed the frame")
    assert not np.array_equal(auto[_ARENA_CROP], other[_ARENA_CROP]), \
        "a different thermal_clim produced the same arena — the argument is ignored"


# ── 2. recordings written before the thermal system ───────────────────────────

def test_snapshot_carries_the_two_thermal_fields():
    """Offline video rendering reads the snapshot and nothing else."""
    params = _params(_still_thermal_world())
    state = jax_reset(params, jax.random.PRNGKey(0))
    snap = _snapshot_state(state)
    assert "thermal_field" in snap and "body_temp" in snap
    assert np.asarray(snap["thermal_field"]).shape == (int(params.height), int(params.width))


def test_a_recording_without_thermal_fields_still_renders():
    """The present-or-absent branch, exercised on a snapshot with the keys REMOVED.

    This is what every `.rec` file written before the thermal system looks like.
    `RECORDING_FORMAT_VERSION` was deliberately not bumped (the stamp nothing
    reads would not have removed a line of this branch), so the reader's only
    protection is that the renderer treats both fields as optional.
    """
    params = _params(copy.deepcopy(yaml.safe_load(open(DEFAULT_CONFIG))))
    state = jax_reset(params, jax.random.PRNGKey(0))
    obs = get_observation(state, params, apply_noise=False)
    viz = build_sensory_viz(np.asarray(obs), state, params)

    old_snap = {k: v for k, v in _snapshot_state(state).items()
                if k not in ("thermal_field", "body_temp")}
    assert "thermal_field" not in old_snap and "body_temp" not in old_snap

    from_old = render_jax_state(_Snapshot(old_snap), params, episode=1, step=0,
                                action=REST, sensory_data=viz, icon_config=None)
    from_live = render_jax_state(state, params, episode=1, step=0, action=REST,
                                 sensory_data=viz, icon_config=None)
    np.testing.assert_array_equal(
        from_old, from_live,
        err_msg="a pre-thermal recording renders differently from the live state "
                "it was taken from")


def test_thermal_off_frame_has_no_thermoception_pod():
    """An absent sensor is drawn as an OFFLINE pod, so an unconditional entry in
    `known_sensors` would put an empty THERMOCEPTION panel on every non-thermal
    frame — and push the Visual pod off the bottom of the panel. Rendering is the
    only way to see that; it is not visible in the list literal."""
    params = _params(copy.deepcopy(yaml.safe_load(open(DEFAULT_CONFIG))))
    state = jax_reset(params, jax.random.PRNGKey(0))
    obs = get_observation(state, params, apply_noise=False)
    viz = build_sensory_viz(np.asarray(obs), state, params)
    assert not any(v["name"] == "Thermoception" for v in viz), \
        "a thermal-off config emitted a thermoception viz entry"
    assert thermal_color_limits(getattr(state, "thermal_field", None), params) is None
    frame = render_jax_state(state, params, episode=1, step=0, action=REST,
                             sensory_data=viz, icon_config=None)
    assert frame.shape[2] == 3 and frame.any()


def test_thermal_on_frame_draws_a_thermoception_pod():
    """The pod is drawn only if the panel loop walks the name.

    Compared against the same frame with the Thermoception entry removed from
    the viz list: if the two right panels are identical, the entry reached the
    renderer and the renderer ignored it — which is what happened before
    `known_sensors` gained the name.
    """
    params = _params(_still_thermal_world())
    state = jax_reset(params, jax.random.PRNGKey(3))
    obs = get_observation(state, params, apply_noise=False)
    viz = build_sensory_viz(np.asarray(obs), state, params)
    assert any(v["name"] == "Thermoception" for v in viz)

    clim = thermal_color_limits(state.thermal_field, params)
    with_pod = render_jax_state(state, params, episode=1, step=0, action=REST,
                                sensory_data=viz, icon_config=None,
                                thermal_clim=clim)
    without = render_jax_state(
        state, params, episode=1, step=0, action=REST,
        sensory_data=[v for v in viz if v["name"] != "Thermoception"],
        icon_config=None, thermal_clim=clim)
    right = np.s_[:, 1050:1300]
    assert not np.array_equal(with_pod[right], without[right]), \
        "the thermoception reading reached the renderer and was not drawn"


# ── 3. the gauge ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("body_temp", [-14.9, -5.0, 0.0, 5.0, 14.9])
def test_the_gauge_renders_across_the_whole_survivable_band(body_temp):
    """Including both ends. A gauge that clips or draws a negative-width bar at
    the cold end is a defect the source does not show."""
    params = _params(_still_thermal_world())
    state = jax_reset(params, jax.random.PRNGKey(3))
    state = state.replace(body_temp=jnp.float32(body_temp))
    frame = _frame(state, params, 0)
    assert frame.shape == (1000, 1400, 3)
    assert frame.any()


def test_the_gauge_bar_length_tracks_the_body_temperature():
    """The BAR must move, not just the number printed beside it.

    Asserted on the fill patch's geometry rather than on pixels, because a gauge
    whose bar is frozen still repaints its numeric readout — so a whole-panel
    pixel comparison passes on a completely inert bar. (Confirmed: pinning the
    fill fraction to a constant left every pixel-level assertion green.)
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from src.environment.renderer import draw_temperature_gauge

    params = _params(_still_thermal_world())
    t_min, t_max = float(params.min_temperature), float(params.max_temperature)
    clim = (t_min * 4, t_max * 4)

    def _fill_width(body_temp):
        fig = plt.figure(figsize=(4, 4))
        ax = fig.add_subplot(111)
        draw_temperature_gauge(ax, 0.05, 0.5, 0.9, 0.04, body_temp, params, clim,
                               transform=ax.transAxes)
        # patch 0 is the trough, patch 1 the fill (both FancyBboxPatch).
        boxes = [p for p in ax.patches
                 if isinstance(p, matplotlib.patches.FancyBboxPatch)]
        assert len(boxes) >= 2, "the gauge did not draw a trough and a fill"
        w = boxes[1].get_width()
        plt.close(fig)
        return float(w)

    widths = [_fill_width(t) for t in (t_min, -7.5, 0.0, 7.5, t_max)]
    assert all(a < b for a, b in zip(widths, widths[1:])), (
        f"the gauge fill is not monotone in body temperature: {widths}")
    # The middle sample must sit where the linear map puts it, so a bar that
    # merely wobbles cannot pass.
    np.testing.assert_allclose(widths[2], 0.9 * (0.0 - t_min) / (t_max - t_min),
                               rtol=1e-6)
    np.testing.assert_allclose(widths[4], 0.9, rtol=1e-6)


def test_the_gauge_moves_with_the_body_in_a_rendered_frame():
    """And the change reaches an actual frame."""
    params = _params(_still_thermal_world())
    state = jax_reset(params, jax.random.PRNGKey(3))
    clim = thermal_color_limits(state.thermal_field, params)
    cold = _frame(state.replace(body_temp=jnp.float32(-12.0)), params, 0, clim)
    warm = _frame(state.replace(body_temp=jnp.float32(+12.0)), params, 0, clim)
    left = np.s_[:, 150:400]
    assert not np.array_equal(cold[left], warm[left]), \
        "the vitals panel is identical at -12 and +12 degrees — the gauge is inert"


def test_debug_read_cells_are_off_by_default():
    """The thermoceptor outline is a debugging aid, not part of the frame."""
    params = _params(_still_thermal_world())
    state = jax_reset(params, jax.random.PRNGKey(3))
    clim = thermal_color_limits(state.thermal_field, params)
    plain = _frame(state, params, 0, clim, debug=False)
    default = _frame(state, params, 0, clim)
    outlined = _frame(state, params, 0, clim, debug=True)
    np.testing.assert_array_equal(plain, default)
    assert not np.array_equal(plain[_ARENA_CROP], outlined[_ARENA_CROP]), \
        "debug_thermal_cells=True drew nothing"
