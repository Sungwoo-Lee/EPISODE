"""Body temperature as an interoceptive observation channel.

What this file checks, in plain terms: the agent can now be TOLD how warm its
own body is. Until this change it could only feel how much warmer or colder the
world was than itself (that is what the thermoceptor reports — a difference),
so its own temperature was latent: recoverable in principle by integrating over
every step of the episode, never handed over. One config key,
`thermal.body_temp_observable`, decides which of those two worlds a run lives
in, and this file pins every property that key is supposed to have.

Five things are easy to get wrong, and each has its own test:

1. **Reading the key outside its guard.** It is conditional-mandatory under
   `thermal.enabled`, exactly like the rest of the `thermal:` block. Reading it
   unconditionally would raise on the 72 stand-alone byte-parity fixture configs
   (they are loaded from a RAW `Config`, which does not resolve `extends:`), and
   the parity gate would go red before it compared a single byte.
   `test_key_is_not_read_when_thermal_is_off` is what makes that safe BY
   CONSTRUCTION rather than only by measurement.

2. **A fallback default.** `config.get('thermal.body_temp_observable', False)`
   would convert 68 deliberately-unmigrated configs from "loudly unmigrated" to
   "silently loading with a value nobody chose". The key must have no default.

3. **A normalised value.** The channel carries RAW DEGREES — `state.body_temp`
   itself — so that `Thermoception[centre] + BodyTemperature` equals the thermal
   field at the agent's own cell under the shipped `thermal.relative: true`. A
   division by `max_temperature`, a clip, or a rescale all fail
   `test_channel_present_and_is_raw_body_temp`.

4. **A reorder.** `get_observation` and `get_observation_breakdown` are the same
   layout stated twice. Body Temperature and Interoceptive Nociception are both
   ONE number wide and sit next to each other, so swapping them leaves every
   total and every width identical while every name-keyed consumer downstream
   (the stats CSV, the renderer, the modulator's input slice) silently labels
   the right columns with the wrong names. `test_order_assert_catches_a_reorder`
   swaps exactly that pair, which is why a width-and-count check would not do.

5. **A half-landed modality.** A new observation block needs its
   `_YAML_KEY_TO_SENSOR_NAME` entry, its `perceptual_noise.modalities` block,
   its stats-CSV branch and its renderer branch, all in the same change. Three
   of the four raise if missing; the fourth raises inside a jit trace naming
   neither the config nor the fix.
"""
import os

# Backend pinning MUST precede any jax import (mirrors test_thermoception.py).
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
)
from src.utils.evaluation_core import build_stat_headers

THERMAL_CONFIG = os.path.join(
    _ROOT, "configs", "environment", "experiment", "thermal", "campfire_world.yaml")
HIDDEN_CONFIG = os.path.join(
    _ROOT, "configs", "environment", "experiment", "thermal",
    "campfire_world_body_temp_hidden.yaml")
DEFAULT_CONFIG = os.path.join(_ROOT, "configs", "environment", "default.yaml")

KEY = "thermal.body_temp_observable"
NAME = "Body Temperature"


# ── helpers ───────────────────────────────────────────────────────────────────

def _dict(path):
    return copy.deepcopy(yaml.safe_load(open(path)))


def _params(path, mutate=None):
    d = _dict(path)
    if mutate is not None:
        mutate(d)
    return load_env_params(Config(d))


def _offset_of(breakdown, name):
    """Start index of one modality, computed from the breakdown ONLY."""
    ptr = 0
    for k, dim in breakdown.items():
        if k == name:
            return ptr
        ptr += int(dim)
    raise KeyError(f"{name!r} not in breakdown {list(breakdown)}")


# ══════════════════════════════════════════════════════════════════════════════
# 1. The config contract
# ══════════════════════════════════════════════════════════════════════════════

def test_key_is_mandatory_when_thermal_is_on():
    """Thermal ON and the key absent must RAISE, naming the key."""
    d = _dict(THERMAL_CONFIG)
    del d["thermal"]["body_temp_observable"]
    with pytest.raises(ValueError, match=r"thermal\.body_temp_observable"):
        load_env_params(Config(d))


def test_key_is_not_read_when_thermal_is_off():
    """Thermal OFF and the key absent must LOAD, with the inert False sentinel.

    This is what proves the 72 byte-parity fixture configs are safe BY
    CONSTRUCTION and not merely by measurement: every one of them ships
    `thermal.enabled: false`, and none of them declares this key.
    """
    d = _dict(DEFAULT_CONFIG)
    assert d["thermal"]["enabled"] is False, "default.yaml is meant to be thermal-off"
    del d["thermal"]["body_temp_observable"]
    params = load_env_params(Config(d))
    assert params.thermal_body_temp_observable is False
    # ...and the modality really is absent from the observation.
    assert NAME not in get_observation_breakdown(params)


def test_no_fallback_default():
    """The loader's message must NAME the key.

    Guards against a `config.get(KEY, False)` creeping in later: a fallback
    default is the single change that would make deferring the 68 unmigrated
    configs unsafe, because `test_backward_compat_configs.py` only knows to SKIP
    a stale config when the loader says "... is required but missing".
    """
    d = _dict(THERMAL_CONFIG)
    del d["thermal"]["body_temp_observable"]
    with pytest.raises(ValueError) as excinfo:
        load_env_params(Config(d))
    msg = str(excinfo.value)
    assert KEY in msg
    assert "required but missing" in msg


def test_both_shipped_thermal_configs_declare_the_key():
    """Both arms of the ablation carry the key INLINE.

    Cheap, and it is what stops either config falling silently into the "stale
    config" SKIP branch of test_backward_compat_configs.py, where a missing key
    is skipped rather than failed.
    """
    shown = _dict(THERMAL_CONFIG)
    hidden = _dict(HIDDEN_CONFIG)
    assert shown["thermal"]["body_temp_observable"] is True
    assert hidden["thermal"]["body_temp_observable"] is False
    assert "extends" not in shown and "extends" not in hidden


# ══════════════════════════════════════════════════════════════════════════════
# 2. The channel itself
# ══════════════════════════════════════════════════════════════════════════════

def test_channel_present_and_is_raw_body_temp():
    """One dim, and it is `state.body_temp` verbatim — not normalised, not clipped."""
    params = _params(THERMAL_CONFIG)
    assert params.thermal_body_temp_observable is True
    breakdown = get_observation_breakdown(params)
    assert breakdown.get(NAME) == 1

    state = jax_reset(params, jax.random.PRNGKey(0)).replace(
        body_temp=jnp.float32(-7.25))
    obs = np.asarray(get_observation(state, params, apply_noise=False))
    idx = _offset_of(breakdown, NAME)
    assert obs[idx] == np.float32(-7.25), (
        f"observation[{idx}] is {obs[idx]!r}, not the raw body temperature. A "
        f"normalised, clipped or rescaled channel fails here by design.")


def test_flag_false_removes_exactly_that_one_column():
    """Switching the flag off removes that column and changes NOTHING else.

    Self-consistency rather than a historical comparison: no pre-change
    thermal-ON observation fixture exists. ONE state is reset (the flag is read
    nowhere in core.py, so a single state is valid under both params) and the
    two observations are taken from it.
    """
    p_true = _params(THERMAL_CONFIG)
    p_false = _params(THERMAL_CONFIG,
                      lambda d: d["thermal"].update(body_temp_observable=False))
    state = jax_reset(p_false, jax.random.PRNGKey(3))

    obs_true = np.asarray(get_observation(state, p_true, apply_noise=False))
    obs_false = np.asarray(get_observation(state, p_false, apply_noise=False))
    assert obs_true.shape[0] == obs_false.shape[0] + 1

    idx = _offset_of(get_observation_breakdown(p_true), NAME)
    np.testing.assert_array_equal(
        np.delete(obs_true, idx), obs_false,
        err_msg="the flag removed more (or less) than its own column")


def test_position_is_after_satiation_before_intero_noci():
    """Satiation, then Body Temperature, then Interoceptive Nociception.

    The directly-delivered body LEVELS stay contiguous and the PERCEPT follows
    them, mirroring EVAAA's `resourceLevels` block — and making
    ["Satiation", "Body Temperature", "Interoceptive Nociception"] a contiguous
    slice for future modulator work.
    """
    keys = list(get_observation_breakdown(_params(THERMAL_CONFIG)))
    i = keys.index("Satiation")
    assert keys[i + 1] == NAME
    assert keys[i + 2] == "Interoceptive Nociception"


@pytest.mark.parametrize("thermal_on", [True, False])
@pytest.mark.parametrize("observable", [True, False])
def test_breakdown_and_observation_agree(thermal_on, observable):
    """All four combinations of (thermal on/off) x (observable true/false)."""
    params = _params(
        THERMAL_CONFIG,
        lambda d: d["thermal"].update(enabled=thermal_on,
                                      body_temp_observable=observable))
    state = jax_reset(params, jax.random.PRNGKey(0))
    obs = get_observation(state, params, apply_noise=False)
    breakdown = get_observation_breakdown(params)
    assert sum(breakdown.values()) == int(obs.shape[0])
    assert (NAME in breakdown) == (thermal_on and observable)


# ══════════════════════════════════════════════════════════════════════════════
# 3. The ordering contract
# ══════════════════════════════════════════════════════════════════════════════

def test_order_assert_catches_a_reorder(monkeypatch):
    """Swap two EQUAL-WIDTH neighbours and `get_observation` must raise.

    This is the test that proves the order check is not vacuous. Body
    Temperature and Interoceptive Nociception are both width 1, so the swapped
    layout has the identical total, the identical set of names and the identical
    per-modality widths — every count-and-width check passes. Only comparing
    NAMES catches it.
    """
    params = _params(THERMAL_CONFIG)
    state = jax_reset(params, jax.random.PRNGKey(0))
    real = sensor_mod.get_observation_breakdown

    def swapped(p):
        b = dict(real(p))
        keys = list(b)
        i, j = keys.index(NAME), keys.index("Interoceptive Nociception")
        keys[i], keys[j] = keys[j], keys[i]
        return {k: b[k] for k in keys}

    # The swap is invisible to totals and widths — stated here so the test
    # documents the hazard it exists for.
    assert sum(swapped(params).values()) == sum(real(params).values())
    assert set(swapped(params)) == set(real(params))

    monkeypatch.setattr(sensor_mod, "get_observation_breakdown", swapped)
    # `get_observation` is jitted: a cached trace from an earlier test would skip
    # the (trace-time) check entirely and make this test vacuous.
    sensor_mod.get_observation.clear_cache()
    try:
        with pytest.raises(AssertionError) as excinfo:
            sensor_mod.get_observation(state, params, apply_noise=False)
    finally:
        monkeypatch.undo()
        sensor_mod.get_observation.clear_cache()

    msg = str(excinfo.value)
    print("\nRAISED:", msg)
    assert NAME in msg and "Interoceptive Nociception" in msg
    assert "diverged" in msg


# ══════════════════════════════════════════════════════════════════════════════
# 4. The downstream consumers
# ══════════════════════════════════════════════════════════════════════════════

def test_modulator_slice_resolves_under_the_new_layout():
    """The three interoceptive names resolve to CONTIGUOUS indices, and a name
    that is absent raises rather than re-indexing silently."""
    from src.models.recurrent_ppo_network import _resolve_modulator_input_indices

    params = _params(THERMAL_CONFIG)
    breakdown = get_observation_breakdown(params)
    obs_dim = sum(breakdown.values())
    idx = _resolve_modulator_input_indices(
        ["Satiation", NAME, "Interoceptive Nociception"], breakdown, obs_dim)
    assert len(idx) == 3
    assert list(idx) == list(range(idx[0], idx[0] + 3)), "not contiguous"

    p_false = _params(THERMAL_CONFIG,
                      lambda d: d["thermal"].update(body_temp_observable=False))
    b_false = get_observation_breakdown(p_false)
    with pytest.raises(ValueError, match="unknown sensor"):
        _resolve_modulator_input_indices(
            ["Satiation", NAME, "Interoceptive Nociception"],
            b_false, sum(b_false.values()))


def test_noise_map_and_config_block_are_paired():
    """The YAML block and the loader's name map must land together."""
    params = _params(THERMAL_CONFIG)
    assert NAME in params.noise_modality_order

    # The half that only shows with noise ON: without the YAML block,
    # `apply_perceptual_noise` raises a bare KeyError inside a jit trace naming
    # neither the config nor the fix. Every other thermal test runs noise OFF,
    # so nothing else in the suite walks this path. The channel's σ is 0.0 and
    # its clips are ±100, so the value must come through untouched.
    p_noisy = _params(THERMAL_CONFIG,
                      lambda d: d["perceptual_noise"].update(enabled=True))
    state = jax_reset(p_noisy, jax.random.PRNGKey(0)).replace(
        body_temp=jnp.float32(-9.0))
    obs = np.asarray(get_observation(state, p_noisy, apply_noise=True))
    idx = _offset_of(get_observation_breakdown(p_noisy), NAME)
    assert obs[idx] == np.float32(-9.0)

    def _bad_key(d):
        d["perceptual_noise"]["modalities"]["body_temperature_typo"] = {
            "mode": "none", "sigma": 0.0}
    with pytest.raises(ValueError, match="unknown perceptual-noise modality key"):
        _params(THERMAL_CONFIG, _bad_key)


def test_stats_csv_and_viz_have_branches():
    """Neither terminal `raise` fires, and the CSV names the column."""
    params = _params(THERMAL_CONFIG)
    breakdown = get_observation_breakdown(params)
    headers = build_stat_headers(params, breakdown, record_true_obs=False)
    assert "obs_intero_body_temp" in headers

    state = jax_reset(params, jax.random.PRNGKey(0)).replace(
        body_temp=jnp.float32(4.5))
    obs = np.asarray(get_observation(state, params, apply_noise=False))
    viz = build_sensory_viz(obs, state, params)
    pods = {pod["name"]: pod for pod in viz}
    assert NAME in pods
    assert pods[NAME]["value"] == np.float32(4.5)
    # Keyed `value`, NOT `intensity`: it is raw degrees, not a [0,1] fraction,
    # and draw_intensity_pod would clamp it with `min(1.0, v)`.
    assert "intensity" not in pods[NAME]
