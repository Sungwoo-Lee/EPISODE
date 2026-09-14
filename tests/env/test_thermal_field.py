"""Stage 1 of the temperature system — the [H, W] thermal field.

What this file checks, in plain terms: the environment now builds a map of how
warm every cell is, once, when an episode starts. These tests check that the map
is built the way the design says (fill the world with cold, add each fire's heat
on top of what is already there, then blur once), and that turning the new
placement rules OFF leaves the world exactly where it was before this work.

The blur is checked against an INDEPENDENT oracle — the pure-numpy calibration
sandbox the design's numbers were computed from, vendored into
`tests/env/thermal_sandbox_oracle.py`. Re-deriving the expected field with the
same JAX helper would only prove the function equals itself.
"""
import os

# Backend pinning MUST precede any jax import: the no-op test compares against
# fixtures generated on CPU, and a GPU run differs in the last bits.
os.environ.setdefault("JAX_PLATFORMS", "cpu")

import copy
import sys

import numpy as np
import pytest
import yaml

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)          # for the vendored oracle module

import jax
import jax.numpy as jnp

from src.utils.config import Config
from src.environment.config_loader import load_env_params
from src.environment.core import jax_reset, _build_thermal_field, _gaussian_smooth_normalised
from thermal_sandbox_oracle import gaussian_smooth

THERMAL_CONFIG = os.path.join(
    _ROOT, "configs", "environment", "experiment", "archive", "thermal", "campfire_world.yaml")
DEFAULT_CONFIG = os.path.join(_ROOT, "configs", "environment", "default.yaml")
THERMAL_PARITY_FIXTURES = os.path.join(_ROOT, "tests", "env", "fixtures", "thermal_parity")


# ── config helpers ────────────────────────────────────────────────────────────

def _campfire_dict():
    return copy.deepcopy(yaml.safe_load(open(THERMAL_CONFIG)))


def _campfire_entry(d):
    for o in d["environment"]["obstacles"]:
        if o.get("name") == "campfire":
            return o
    raise AssertionError("campfire entry missing from the thermal example config")


def _degenerate_absolute_config(n_fires=1, temperature=300.0, baseline=-25.0):
    """A thermal config whose raw field is fully determined by the placed positions.

    Two deliberate departures from the shipped example, both so the oracle can
    reconstruct the RAW stamps from state alone:
      - `default_temp` is a degenerate range, so the world baseline is a constant
        rather than a per-episode draw;
      - the campfire declares an ABSOLUTE `temperature` instead of a
        `temperature_ratio`, so its stamp is not a per-episode draw either.
    """
    d = _campfire_dict()
    d["thermal"]["default_temp"] = [baseline, baseline]
    d["thermal"]["use_random_spots"] = False
    fire = _campfire_entry(d)
    fire.pop("temperature_ratio", None)
    fire.pop("count_low", None)
    fire.pop("count_high", None)
    fire["count"] = n_fires
    fire["temperature"] = temperature
    return d


def _params(d):
    return load_env_params(Config(d))


def _fire_slots(params):
    """Slot mask of heat sources — a slot with a non-zero declared temperature."""
    return (np.asarray(params.obs_temperature) != 0.0) \
        | (np.asarray(params.obs_temp_ratio_low) != 0.0) \
        | (np.asarray(params.obs_temp_ratio_high) != 0.0)


# ── the oracle test ───────────────────────────────────────────────────────────

def test_field_matches_numpy_sandbox():
    """Build the field through `jax_reset`; blur the same raw stamps in numpy.

    The raw stamps are reconstructed from the reset state (`obs_pos`,
    `obs_active`) plus the config's absolute temperatures — which is only
    possible because `_degenerate_absolute_config` removes both per-episode
    draws. What is actually under test is the blur: the weight renormalisation
    at the edges, the kernel radius, and the fact that the blur happens exactly
    once, at the end.
    """
    params = _params(_degenerate_absolute_config(n_fires=1, temperature=300.0))
    state = jax_reset(params, jax.random.PRNGKey(0))

    H, W = params.height, params.width
    raw = np.full((H, W), -25.0, dtype=np.float64)
    temp = np.asarray(params.obs_temperature)
    pos = np.asarray(state.obs_pos)
    active = np.asarray(state.obs_active)
    for i in range(pos.shape[0]):
        r, c = int(pos[i, 0]), int(pos[i, 1])
        if active[i] and 0 <= r < H and 0 <= c < W:
            raw[r, c] += float(temp[i])

    expected = gaussian_smooth(raw, float(params.thermal_sigma))
    np.testing.assert_allclose(
        np.asarray(state.thermal_field), expected, rtol=1e-5,
        err_msg="jax_reset's thermal field disagrees with the numpy sandbox oracle")

    # Sanity: the fire actually did something, so a silently-empty field cannot
    # pass this test by matching an all-baseline oracle.
    assert np.asarray(state.thermal_field).max() > -20.0


def test_stamps_are_additive():
    """Two campfires on ONE cell sum; they do not overwrite each other.

    This case CANNOT be set up through `jax_reset`: `resolve_overlaps_global`
    exists precisely to stop two entities sharing a cell, so the co-location
    never survives placement. `_build_thermal_field` is therefore called
    directly with a hand-constructed `obs_pos`. Do not "fix" this into a
    reset-based test — it would quietly stop testing addition.

    The regression it guards against is EVAAA's `areaTemp[x, z] = temperature`
    (ThermoGridSpawner.cs:218), where the last source spawned silently wins.
    """
    # A zero baseline, so the comparison is not a difference of two numbers near
    # -25: at float32 that cancellation destroys the relative precision of the
    # small tail values and the test would fail for arithmetic reasons.
    params = _params(_degenerate_absolute_config(
        n_fires=2, temperature=100.0, baseline=0.0))
    fires = _fire_slots(params)
    assert fires.sum() == 2, "expected exactly two campfire slots"

    n_obs = params.obs_temperature.shape[0]
    n_res = params.res_temperature.shape[0]
    idx = np.flatnonzero(fires)

    def field_for(active_slots):
        """active_slots: {slot index -> (row, col)}"""
        obs_pos = np.zeros((n_obs, 2), dtype=np.int32)
        obs_active = np.zeros(n_obs, dtype=bool)
        for slot, p in active_slots.items():
            obs_pos[slot] = p
            obs_active[slot] = True
        return np.asarray(_build_thermal_field(
            params, jax.random.PRNGKey(0),
            jnp.array(obs_pos), jnp.array(obs_active),
            jnp.zeros((n_res, 2), dtype=jnp.int32), jnp.zeros(n_res, dtype=jnp.bool_)))

    single = field_for({idx[0]: (4, 4)})
    both_on_one_cell = field_for({idx[0]: (4, 4), idx[1]: (4, 4)})

    np.testing.assert_allclose(
        both_on_one_cell, 2.0 * single, rtol=1e-5, atol=1e-5,
        err_msg="two co-located stamps did not add — an assignment (last writer "
                "wins) would give exactly the single-stamp field")
    assert both_on_one_cell.max() > 1.9 * single.max()


def test_field_is_order_independent():
    """Swapping the two campfires' slot indices leaves the field unchanged.

    This is the direct regression test for a return to assignment semantics:
    with `=` the result depends on which slot is stamped last, with `+=` it
    cannot.
    """
    params = _params(_degenerate_absolute_config(n_fires=2, temperature=100.0))
    idx = np.flatnonzero(_fire_slots(params))
    n_obs = params.obs_temperature.shape[0]
    n_res = params.res_temperature.shape[0]

    def field_for(pa, pb):
        obs_pos = np.zeros((n_obs, 2), dtype=np.int32)
        obs_active = np.zeros(n_obs, dtype=bool)
        obs_pos[idx[0]], obs_active[idx[0]] = pa, True
        obs_pos[idx[1]], obs_active[idx[1]] = pb, True
        return np.asarray(_build_thermal_field(
            params, jax.random.PRNGKey(0),
            jnp.array(obs_pos), jnp.array(obs_active),
            jnp.zeros((n_res, 2), dtype=jnp.int32), jnp.zeros(n_res, dtype=jnp.bool_)))

    np.testing.assert_array_equal(field_for((2, 3), (7, 8)), field_for((7, 8), (2, 3)))


@pytest.mark.parametrize("shape", [(10, 10), (7, 13), (13, 7)])
def test_edge_renormalisation_matches_oracle(shape):
    """A corner stamp on a NON-SQUARE grid, where a transposed kernel would show.

    Edge cells must be normalised by the in-bounds weight sum (EVAAA's
    `sum / weightSum`), not by the full kernel mass. A naive convolution treats
    the out-of-bounds neighbours as zeros and reports a corner as far colder
    than it is. On a square grid a row/column transposition in the kernel is
    invisible; on 7x13 and 13x7 it is not.
    """
    H, W = shape
    raw = np.full((H, W), -25.0, dtype=np.float64)
    raw[0, 0] += 300.0
    raw[H - 1, W - 1] += 120.0
    sigma = 0.7
    radius = int(np.ceil(3 * sigma))

    got = np.asarray(_gaussian_smooth_normalised(jnp.array(raw, dtype=jnp.float32),
                                                 sigma, radius))
    np.testing.assert_allclose(got, gaussian_smooth(raw, sigma), rtol=1e-5)


# ── placement constraints (D2 / D3) ───────────────────────────────────────────

_N_RESETS = 500


def test_fires_respect_min_separation():
    """Over 500 resets, no two fires sit closer than `min_fire_separation`.

    Sampled over many resets on purpose: a constraint that holds on seed 0 and
    fails on seed 7 is exactly the failure mode here.

    The count is pinned to a fixed 3 so every single reset exercises the
    feasibility claim behind the default (three fires 3+ apart fit the 6x6
    interior that `edge_margin: 2` leaves on a 10x10 grid). A sampler that
    quietly gave up would otherwise look like a rare unlucky draw.

    The in-area assertion is not decoration. `resolve_overlaps_global` has a
    SILENT fallback: when no cell satisfies its validity mask, the entity is
    parked at cell (0, 0) — outside its own spawn area, with nothing raised.
    Tightening the mask makes that more reachable, so the only thing turning a
    silent (0, 0) park into a visible failure is this check.
    """
    d = _campfire_dict()
    fire = _campfire_entry(d)
    fire.pop("count_low", None)
    fire.pop("count_high", None)
    fire["count"] = 3
    params = _params(d)
    sep = params.thermal_min_fire_separation
    assert sep == 3, f"expected the shipped default min_fire_separation=3, got {sep}"

    fires = _fire_slots(params)
    assert fires.sum() == 3
    areas = np.asarray(params.obs_spawn_area)[fires]      # [3, 4] min_r,min_c,max_r,max_c

    keys = jax.random.split(jax.random.PRNGKey(20260908), _N_RESETS)
    states = jax.vmap(lambda k: jax_reset(params, k))(keys)
    pos = np.asarray(states.obs_pos)[:, fires, :]         # [N, 3, 2]
    active = np.asarray(states.obs_active)[:, fires]      # [N, 3]

    assert active.all(), "a fixed count: 3 entry must activate all three slots"

    # (a) every pair at least `sep` Manhattan cells apart
    d01 = np.abs(pos[:, 0] - pos[:, 1]).sum(-1)
    d02 = np.abs(pos[:, 0] - pos[:, 2]).sum(-1)
    d12 = np.abs(pos[:, 1] - pos[:, 2]).sum(-1)
    worst = min(d01.min(), d02.min(), d12.min())
    assert worst >= sep, (
        f"closest fire pair over {_N_RESETS} resets was {worst} Manhattan cells "
        f"apart; min_fire_separation is {sep}")

    # (b) no fire parked outside its own spawn area (the silent (0,0) fallback)
    for f in range(3):
        min_r, min_c, max_r, max_c = (int(x) for x in areas[f])
        r, c = pos[:, f, 0], pos[:, f, 1]
        outside = ~((r >= min_r) & (r < max_r) & (c >= min_c) & (c < max_c))
        assert not outside.any(), (
            f"fire {f} landed outside its own spawn area "
            f"[{min_r},{min_c})-[{max_r},{max_c}) on {int(outside.sum())} of "
            f"{_N_RESETS} resets — this is the silent cell-(0,0) placement "
            f"fallback in resolve_overlaps_global, not an unlucky draw")


def test_food_min_fire_distance_is_enforced_when_enabled():
    """The D3 second pass actually moves food away from fires when switched on.

    Food is placed BEFORE any fire exists (the scan order is
    [res, pred, obs, neutral]), so this cannot be a term in the first pass — it
    needs a second pass, and this test is what says the second pass ran.
    """
    d = _campfire_dict()
    d["thermal"]["food_min_fire_distance"] = 4
    fire = _campfire_entry(d)
    fire.pop("count_low", None)
    fire.pop("count_high", None)
    fire["count"] = 1
    params = _params(d)
    assert params.thermal_food_min_fire_distance == 4

    fires = _fire_slots(params)
    food = np.asarray(params.res_type) == 0

    keys = jax.random.split(jax.random.PRNGKey(7), 100)
    states = jax.vmap(lambda k: jax_reset(params, k))(keys)
    fpos = np.asarray(states.obs_pos)[:, fires, :]       # [N, 1, 2]
    rpos = np.asarray(states.res_pos)[:, food, :]        # [N, n_food, 2]
    ract = np.asarray(states.res_active)[:, food]

    dist = np.abs(rpos[:, :, None, :] - fpos[:, None, :, :]).sum(-1)   # [N, n_food, 1]
    violating = (dist < 4).any(-1) & ract
    assert not violating.any(), (
        f"{int(violating.sum())} active food items landed within 4 Manhattan "
        f"cells of a fire despite food_min_fire_distance: 4")


def test_placement_constraints_are_noops_when_disabled():
    """With both constraints at 0 the world is byte-identical to the Stage 0 record.

    This is the H10 guard. `resolve_overlaps_global` draws exactly ONE
    permutation and then walks it deterministically; any implementation that
    draws a key when it has nothing to reject would move every downstream PRNG
    stream, and the whole project's reward history with it.

    The reference is the Stage 0 THERMAL-parity fixture, not the older
    `tests/env/fixtures/parity/` set: that older set does not capture the full
    position triple, and it is the gate this test is meant to be independent of.

    Two configurations are checked, because they fail differently:
      (a) thermal OFF — the state every existing config is in;
      (b) thermal ON with both constraints at 0 — proves the no-op is a property
          of the constraint values, not merely of the master switch.
    """
    fixture_path = os.path.join(THERMAL_PARITY_FIXTURES, "configs__environment__default.npz")
    assert os.path.exists(fixture_path), (
        "Stage 0 fixture missing — regenerate with "
        "scripts/fixtures/generate_thermal_parity_fixtures.py")
    fx = np.load(fixture_path)

    base = copy.deepcopy(yaml.safe_load(open(DEFAULT_CONFIG)))

    thermal_on = copy.deepcopy(base)
    thermal_on["thermal"]["enabled"] = True
    thermal_on["thermal"]["min_fire_separation"] = 0
    thermal_on["thermal"]["food_min_fire_distance"] = 0

    for label, d in (("thermal off", base), ("thermal on, constraints 0", thermal_on)):
        params = _params(d)
        assert params.thermal_min_fire_separation == 0
        assert params.thermal_food_min_fire_distance == 0
        state = jax_reset(params, jax.random.PRNGKey(0))
        # index 0 of each stacked fixture array is the reset state
        for field in ("key", "res_pos", "animal_pos", "obs_pos"):
            np.testing.assert_array_equal(
                np.asarray(getattr(state, field)), fx[field][0],
                err_msg=f"[{label}] {field} moved relative to the Stage 0 fixture — "
                        f"a placement change has shifted the PRNG stream")
