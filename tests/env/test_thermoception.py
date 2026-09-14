"""Stage 3 of the temperature system — the thermoceptor (+5 observation dims).

What this file checks, in plain terms: the agent can now feel how warm the cell
it stands on is, and how warm its four neighbours are, relative to its own body
("that cell is 30 degrees warmer than me"). That is five new numbers in the
observation vector, and they are inserted in the MIDDLE of it — after pain,
before smell — which is what makes this stage delicate.

Four things are easy to get wrong here, and each has its own test:

1. **A wrong stencil.** Reading the wrong five cells — transposed, rotated, or
   off by one — produces numbers that look completely reasonable. So the field
   used in `test_reads_the_five_cells_it_claims` has a DISTINCT value in every
   cell; a uniform or symmetric test field cannot tell a correct stencil from a
   transposed one. This is the exact failure that cost this project the most
   time on the visual sensor.

2. **Out-of-bounds cells reading zero.** Olfaction and vision zero their
   out-of-bounds cells. For a RELATIVE thermal reading, zero means "that cell is
   exactly my own temperature" — the most misleading value available, because it
   makes the map edge look like a warm refuge to an agent standing in the cold.
   Thermoception clamps the coordinate instead. Note what
   `test_oob_reads_the_clamped_neighbour` asserts: the out-of-bounds reading
   equals the clamped in-grid cell EXACTLY. Merely asserting "no reading equals
   minus my body temperature" would be far too weak — an implementation that
   copies the olfaction idiom (mask applied AFTER `field - body_temp`) reads 0.0
   out of bounds, which already differs from `-body_temp` whenever the body is
   not at zero, so the most likely wrong implementation would pass.

3. **A silently shifted renderer.** `build_sensory_viz` walks the observation
   with a slice pointer. Before this stage it had no terminal `else`, so an
   unrecognised modality never advanced the pointer and every LATER panel —
   smell, collision, proprioception, vision, location — drew another modality's
   numbers. Nothing raised; the videos were simply wrong.
   `test_sensory_viz_panels_are_not_shifted` compares each panel against a slice
   offset computed independently from the breakdown, never against
   `build_sensory_viz`'s own pointer, which would re-derive the bug.

4. **The perceptual-noise path.** Adding a modality without a matching
   `thermoception:` block raises a bare `KeyError` inside a jit trace, and the
   loader's default clip of +/-100 would quietly compress a sensor that routinely
   reads past +100 down to a flat saturated value — invisible, because every
   other test in the thermal suite runs with noise off. Both are checked here.
"""
import os

# Backend pinning MUST precede any jax import (mirrors test_thermal_field.py).
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
from src.environment.core import jax_reset
from src.environment import sensor as sensor_mod
from src.environment.sensor import (
    build_sensory_viz,
    get_observation,
    get_observation_breakdown,
    get_visual_offsets,
    sense_thermoception,
)

THERMAL_CONFIG = os.path.join(
    _ROOT, "configs", "environment", "experiment", "archive", "thermal", "campfire_world.yaml")
DEFAULT_CONFIG = os.path.join(_ROOT, "configs", "environment", "default.yaml")

BODY_TEMP = 7.5   # deliberately non-zero: it separates "reads zero" from
                  # "reads minus my body temperature" in the OOB test.


# ── helpers ───────────────────────────────────────────────────────────────────

def _params(path, mutate=None):
    d = copy.deepcopy(yaml.safe_load(open(path)))
    if mutate is not None:
        mutate(d)
    return load_env_params(Config(d))


def _distinct_field(h, w):
    """A field with a DIFFERENT value in every cell, and no zeros.

    `10*r + c + 1` distinguishes (r, c) from (c, r) for every r != c, so a
    transposed stencil cannot pass, and never equals 0, so a zero-filled
    out-of-bounds cell cannot masquerade as a real reading.
    """
    r = np.arange(h)[:, None]
    c = np.arange(w)[None, :]
    return jnp.asarray(10.0 * r + c + 1.0, dtype=jnp.float32)


def _state_with_field(params, agent_rc, body_temp=BODY_TEMP, field=None):
    """A real reset state with the field, agent cell and body temperature pinned."""
    state = jax_reset(params, jax.random.PRNGKey(0))
    if field is None:
        field = _distinct_field(params.height, params.width)
    return state.replace(
        thermal_field=field,
        agent_pos=jnp.array(agent_rc, dtype=state.agent_pos.dtype),
        body_temp=jnp.float32(body_temp),
    )


def _slice_of(breakdown, name):
    """Start/stop of one modality, computed from the breakdown ONLY.

    Deliberately independent of `build_sensory_viz`'s own pointer walk — the
    thing under test in `test_sensory_viz_panels_are_not_shifted` is precisely
    whether that pointer stays in step.
    """
    ptr = 0
    for k, dim in breakdown.items():
        if k == name:
            return ptr, ptr + int(dim)
        ptr += int(dim)
    raise KeyError(f"{name!r} not in breakdown {list(breakdown)}")


# ── 1. the stencil ────────────────────────────────────────────────────────────

def test_reads_the_five_cells_it_claims():
    """Centre, up, right, down, left — in that order, each minus body_temp."""
    params = _params(THERMAL_CONFIG)
    assert params.thermal_enabled and params.thermal_relative
    assert params.thermal_grid_range == 1

    field = _distinct_field(params.height, params.width)
    agent = (4, 6)                     # interior: every neighbour is in bounds
    state = _state_with_field(params, agent, field=field)

    offsets = np.asarray(get_visual_offsets(params.thermal_grid_range))
    assert offsets.tolist() == [[0, 0], [-1, 0], [0, 1], [1, 0], [0, -1]], (
        "the project's diamond order changed; the expectations below encode it")

    f = np.asarray(field)
    expected = np.array([f[agent[0] + dr, agent[1] + dc] - BODY_TEMP
                         for dr, dc in offsets], dtype=np.float32)

    got = np.asarray(sense_thermoception(state, params))
    assert got.shape == (5,)
    np.testing.assert_array_equal(got, expected)

    # The five values must all differ — proof the test field can actually
    # discriminate a wrong stencil rather than merely agreeing with one.
    assert len(set(expected.tolist())) == 5

    # And the same five numbers must appear at the breakdown's declared offset
    # of the assembled observation, not merely inside `sense_thermoception`.
    obs = np.asarray(get_observation(state, params, apply_noise=False))
    lo, hi = _slice_of(get_observation_breakdown(params), "Thermoception")
    np.testing.assert_array_equal(obs[lo:hi], expected)


def test_absolute_mode_drops_the_body_term():
    """`thermal.relative: false` reports the field itself, at the same width."""
    params = _params(THERMAL_CONFIG, lambda d: d["thermal"].update(relative=False))
    assert not params.thermal_relative
    field = _distinct_field(params.height, params.width)
    state = _state_with_field(params, (4, 6), field=field)

    got = np.asarray(sense_thermoception(state, params))
    f = np.asarray(field)
    expected = np.array([f[4 + dr, 6 + dc] for dr, dc in
                         np.asarray(get_visual_offsets(1))], dtype=np.float32)
    np.testing.assert_array_equal(got, expected)
    # Same dimension count, different meaning — which is exactly why
    # `thermal_relative` is in the curriculum modality fingerprint.
    assert get_observation_breakdown(params)["Thermoception"] == 5


# ── 2. out of bounds ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("corner,oob_idx,inb_idx", [
    # (agent cell, indices whose offset leaves the grid, indices that do not)
    ((0, 0), (1, 4), (2, 3)),          # up and left fall off; right and down do not
    ((9, 9), (2, 3), (1, 4)),          # right and down fall off
])
def test_oob_reads_the_clamped_neighbour(corner, oob_idx, inb_idx):
    """An out-of-bounds cell reads the nearest REAL cell, exactly — not zero.

    The assertion is an identity (`== centre`), not the absence of one wrong
    answer. Clamping the whole coordinate pair when only one axis is out of
    range, or wrapping instead of clamping, both produce some OTHER in-grid
    cell's value and would sail past a weaker check.
    """
    params = _params(THERMAL_CONFIG)
    field = _distinct_field(params.height, params.width)
    state = _state_with_field(params, corner, field=field)

    got = np.asarray(sense_thermoception(state, params))
    f = np.asarray(field)
    centre = f[corner] - BODY_TEMP

    assert got[0] == centre
    for i in oob_idx:
        # Clamping only the offending axis leaves the other one alone, and at a
        # corner both offsets of the diamond collapse onto the centre cell.
        assert got[i] == centre, (
            f"cell {i} left the grid and read {got[i]}, not the clamped "
            f"neighbour {centre}")
        assert got[i] != 0.0, "an out-of-bounds cell read zero (the olfaction idiom)"

    # The in-bounds neighbours are untouched by the clamp.
    offsets = np.asarray(get_visual_offsets(1))
    for i in inb_idx:
        dr, dc = offsets[i]
        assert got[i] == f[corner[0] + dr, corner[1] + dc] - BODY_TEMP
        assert got[i] != centre        # so the clamp is not clamping everything


def test_oob_is_not_the_zero_fill_convention():
    """Stated separately because the two failure modes are easy to conflate.

    Out of bounds, olfaction/vision would give 0.0. Here the reading is the
    clamped neighbour, which in a non-zero field is a non-zero number and
    differs from BOTH 0.0 and -body_temp.
    """
    params = _params(THERMAL_CONFIG)
    state = _state_with_field(params, (0, 0))
    got = np.asarray(sense_thermoception(state, params))
    up = got[1]
    assert up != 0.0
    assert up != -BODY_TEMP
    assert up == np.float32(1.0 - BODY_TEMP)   # field[0,0] == 1.0


# ── 3. the assembled observation ──────────────────────────────────────────────

@pytest.mark.parametrize("path,thermal_on,expected_thermo", [
    (DEFAULT_CONFIG, False, None),
    (THERMAL_CONFIG, True, 5),
])
def test_breakdown_matches_assembly(path, thermal_on, expected_thermo):
    params = _params(path)
    assert params.thermal_enabled is thermal_on
    state = jax_reset(params, jax.random.PRNGKey(0))
    obs = get_observation(state, params, apply_noise=False)
    breakdown = get_observation_breakdown(params)
    assert sum(breakdown.values()) == int(obs.shape[0])
    assert breakdown.get("Thermoception") == expected_thermo


def test_thermoception_costs_exactly_five_dims_and_sits_before_olfaction():
    """The width delta and the insertion point, both pinned.

    The two configs are identical apart from `thermal.enabled` and the campfire
    obstacle — and `thermal.body_temp_observable`, which is switched OFF on BOTH
    sides — so the difference in observation width is the thermoceptor's alone.
    """
    # `body_temp_observable` is switched OFF on both sides so the width delta
    # below is the thermoceptor's alone. The body-temperature channel's own +1
    # is pinned in tests/env/test_body_temperature_observation.py.
    off = _params(THERMAL_CONFIG, lambda d: d["thermal"].update(enabled=False))
    on = _params(THERMAL_CONFIG,
                 lambda d: d["thermal"].update(body_temp_observable=False))
    b_off = get_observation_breakdown(off)
    b_on = get_observation_breakdown(on)
    assert sum(b_on.values()) - sum(b_off.values()) == 5
    assert "Thermoception" not in b_off
    keys = list(b_on)
    assert keys.index("Thermoception") == keys.index("Extero Nociception") + 1
    assert keys.index("Thermoception") < keys.index("Olfaction")
    # Every OTHER modality keeps its width; only the new one is added.
    assert {k: v for k, v in b_on.items() if k != "Thermoception"} == b_off


# ── 4. the renderer (finding F7 / hazard H15) ─────────────────────────────────

def _pod_to_breakdown_name(pod_name):
    return {"Olfactory": "Olfaction",
            "LOC": "Location",
            "Intero Nociception": "Interoceptive Nociception"}.get(pod_name, pod_name)


@pytest.mark.parametrize("path", [DEFAULT_CONFIG, THERMAL_CONFIG])
def test_sensory_viz_panels_are_not_shifted(path):
    """Every panel must carry ITS OWN slice of the observation.

    A slice shift of 5 is invisible to any assertion on totals or on the set of
    panels present — both stay correct while every panel after thermoception
    draws its neighbour's numbers. So each panel is compared value-by-value
    against an offset computed from the breakdown alone.
    """
    params = _params(path)
    state = _state_with_field(params, (4, 6)) if params.thermal_enabled \
        else jax_reset(params, jax.random.PRNGKey(0))
    obs = np.asarray(get_observation(state, params, apply_noise=False))
    breakdown = get_observation_breakdown(params)

    viz = build_sensory_viz(obs, state, params)
    seen = []
    for pod in viz:
        name = _pod_to_breakdown_name(pod["name"])
        seen.append(name)
        lo, hi = _slice_of(breakdown, name)
        if "vector" in pod:
            np.testing.assert_array_equal(
                np.asarray(pod["vector"]), obs[lo:hi],
                err_msg=f"panel {pod['name']!r} is drawing the wrong slice")
        elif "intensity" in pod:
            assert hi - lo == 1
            assert np.float32(pod["intensity"]) == obs[lo]
        elif "value" in pod:
            # Body Temperature: one raw-degrees number, deliberately not keyed
            # `intensity` because it is not a [0,1] fraction.
            assert hi - lo == 1
            assert np.float32(pod["value"]) == obs[lo]
        elif "value_text" in pod:
            assert pod["value_text"] == f"({obs[lo]:.2f}, {obs[lo+1]:.2f})"
        else:
            raise AssertionError(f"unrecognised pod shape for {pod['name']!r}")

    # Nothing dropped: a missing branch would silently omit a panel AND shift
    # every later one, so the panel set is checked too.
    assert seen == list(breakdown)


def test_sensory_viz_raises_on_an_unknown_modality(monkeypatch):
    """The terminal `else` — the tripwire for the NEXT modality.

    Without it an unrecognised name advances no pointer and every later panel is
    silently misaligned. With it, the same mistake is a loud failure at the first
    frame rendered.
    """
    params = _params(DEFAULT_CONFIG)
    state = jax_reset(params, jax.random.PRNGKey(0))
    obs = np.asarray(get_observation(state, params, apply_noise=False))

    real = sensor_mod.get_observation_breakdown

    def _with_ghost(p):
        bd = dict(real(p))
        out = {}
        for k, v in bd.items():
            if k == "Collision":
                out["Ghost Sense"] = 5    # inserted BEFORE collision, as thermal is
            out[k] = v
        return out

    monkeypatch.setattr(sensor_mod, "get_observation_breakdown", _with_ghost)
    with pytest.raises(ValueError, match="no branch for sensor 'Ghost Sense'"):
        build_sensory_viz(obs, state, params)


# ── 5. the perceptual-noise path (finding F2 / hazard H18) ────────────────────

def test_noise_enabled_thermal_run_loads_and_runs():
    """Both halves of F2 in one test: the whitelist entry and the config block.

    `_YAML_KEY_TO_SENSOR_NAME` is a strict whitelist, so the `thermoception:`
    block alone raises at load; `apply_perceptual_noise` looks every breakdown
    key up in that same map, so the dict entry alone raises a bare KeyError
    inside a jit trace. Only both together work, and this exercises both.
    """
    params = _params(THERMAL_CONFIG,
                     lambda d: d["perceptual_noise"].update(enabled=True))
    assert params.perceptual_noise_enabled
    assert "Thermoception" in params.noise_modality_order
    state = _state_with_field(params, (4, 6))
    obs = get_observation(state, params, apply_noise=True)     # must not raise
    assert int(obs.shape[0]) == sum(get_observation_breakdown(params).values())


def test_noise_clip_does_not_compress_the_fire():
    """The clip bounds must not bind on a real fire reading.

    `apply_perceptual_noise` clips EVERY modality whenever perceptual noise is
    enabled — including modalities in mode "none" — so the loader's +/-100
    default would train the agent on a sensor saturated at 100 while every
    (noise-off) test saw the true value. The declared bounds are checked against
    a field hotter than that default.
    """
    params = _params(THERMAL_CONFIG,
                     lambda d: d["perceptual_noise"].update(enabled=True))
    hot = jnp.full((params.height, params.width), 250.0, dtype=jnp.float32)
    state = _state_with_field(params, (4, 6), field=hot)

    obs = np.asarray(get_observation(state, params, apply_noise=True))
    lo, hi = _slice_of(get_observation_breakdown(params), "Thermoception")
    thermo = obs[lo:hi]
    assert np.all(thermo > 100.0), (
        f"thermoception was clipped to {thermo.max()}; the declared clip_max is "
        f"too tight for the field this environment builds")
    np.testing.assert_allclose(thermo, 250.0 - BODY_TEMP, rtol=0, atol=1e-4)


def test_stats_csv_has_a_column_per_thermoceptive_cell():
    """`_sensor_stat_columns` raises on any modality it does not know."""
    from src.utils.evaluation_core import _sensor_stat_columns
    params = _params(THERMAL_CONFIG)
    names = _sensor_stat_columns("Thermoception", 5, params, "obs_")
    assert names == ["obs_thermo_r0c0", "obs_thermo_r-1c0", "obs_thermo_r0c1",
                     "obs_thermo_r1c0", "obs_thermo_r0c-1"]
