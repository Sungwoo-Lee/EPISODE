"""Stage 6b of the temperature system — the load-time structure check.

What this file checks, in plain terms. The temperature task only exists inside a
narrow band of settings: the fire has to be hot enough to hurt when you stand on
it, the ring one cell out has to be somewhere you can survive forever, and three
cells out the cold has to actually kill you on a clock. Miss the band and the
run still looks healthy while the agent quietly learns a different task. This
stage makes a config outside the band fail at LOAD, loudly, instead of training
for a week and being discovered afterwards.

The file has two halves and both matter equally:

  * the POSITIVE cases — configs that must be REFUSED, each asserted on the text
    of the message, not merely on "something raised". A ValueError thrown by an
    unrelated line would otherwise pass every one of them.
  * the NEGATIVE cases — configs that must still LOAD. These are what stop the
    check from breaking the four earlier stages. Stages 1 through 5 each ship
    thermal-ON test configs that deliberately lack the pain-plus-comfort
    structure, and a check that rejected them would surface as four stages
    becoming unrunnable rather than as a failure here.
"""
import os

# Backend pinning MUST precede any jax import (see the sibling thermal tests).
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
from src.environment.config_loader import (
    load_env_params, _thermal_single_fire_field, _thermal_equilibrium,
    _thermal_radial_equilibria,
)
from src.environment.core import jax_reset

THERMAL_CONFIG = os.path.join(
    _ROOT, "configs", "environment", "experiment", "archive", "thermal", "campfire_world.yaml")
DEFAULT_CONFIG = os.path.join(_ROOT, "configs", "environment", "default.yaml")


# ── config helpers ────────────────────────────────────────────────────────────

def _campfire_dict():
    d = copy.deepcopy(yaml.safe_load(open(THERMAL_CONFIG)))
    # Archived raw input: not migrated for the water gate (project policy); supplied in memory, `false` = the pre-water world (THIRST_WATER_PLAN).
    d.setdefault("water", {"enabled": False})
    return d


def _default_dict():
    return copy.deepcopy(yaml.safe_load(open(DEFAULT_CONFIG)))


def _fire_entry(d):
    for o in d["environment"]["obstacles"]:
        if o.get("name") == "campfire":
            return o
    raise AssertionError("campfire entry missing from the thermal example config")


def _params(d):
    return load_env_params(Config(d))


def _with_thermal(**kw):
    d = _campfire_dict()
    d["thermal"].update(kw)
    return d


def _with_fire(**kw):
    d = _campfire_dict()
    _fire_entry(d).update(kw)
    return d


def _no_confounders(d):
    """Strip everything that can end an episode for a non-thermal reason."""
    d["environment"]["entities"] = []
    d["environment"]["obstacles"] = [
        o for o in d["environment"]["obstacles"] if o.get("name") == "campfire"]
    d["environment"]["resources"] = [
        r for r in d["environment"]["resources"] if r.get("type") == "food"]
    return d


# ── 1. configs that must be REFUSED, each asserting on the message ────────────
#
# `match` is a regex searched against the message. Every entry names a key the
# reader can go and edit; a case that only asserted `pytest.raises(ValueError)`
# would pass on a ValueError raised anywhere else in a 2000-line loader.

_MUST_RAISE = [
    ("sigma_zero",
     lambda: _with_thermal(sigma=0.0),
     r"thermal\.sigma must be > 0"),
    ("min_above_max_temperature",
     lambda: _with_thermal(min_temperature=15.0, max_temperature=-15.0),
     r"(?s)thermal\.min_temperature .* must be < thermal\.max_temperature"),
    ("fire_too_weak",
     lambda: _with_fire(temperature_ratio=[3, 4]),
     r"(?s)structure check FAILED.*temperature_ratio = 3.*the fire does not hurt"),
    ("fire_too_strong",
     lambda: _with_fire(temperature_ratio=[25, 30]),
     r"(?s)structure check FAILED.*there is no comfort ring"),
    ("blurred_flat",
     lambda: _with_thermal(sigma=1.5),
     r"(?s)structure check FAILED.*thermal\.sigma = 1\.5"),
    ("edge_margin_empties_the_spawn_rectangle",
     lambda: _with_fire(edge_margin=5),
     r"edge_margin=5 leaves an EMPTY spawn area"),
    ("both_temperature_styles",
     lambda: _with_fire(temperature=40.0),
     r"'temperature' and 'temperature_ratio' are mutually exclusive"),
    ("negative_min_fire_separation",
     lambda: _with_thermal(min_fire_separation=-1),
     r"thermal\.min_fire_separation must be >= 0"),
    ("negative_food_min_fire_distance",
     lambda: _with_thermal(food_min_fire_distance=-1),
     r"thermal\.food_min_fire_distance must be >= 0"),
    ("negative_bush_min_fire_distance",
     lambda: _with_thermal(bush_min_fire_distance=-1),
     r"thermal\.bush_min_fire_distance must be 0 \(off\) or >= 2"),
    ("bush_min_fire_distance_one",
     lambda: _with_thermal(bush_min_fire_distance=1),
     r"thermal\.bush_min_fire_distance must be 0 \(off\) or >= 2"),
    ("merged_fires_cannot_be_certified",
     lambda: _with_thermal(min_fire_separation=0),      # count_high: 3 in the base config
     r"thermal\.min_fire_separation is 0 while 3 heat-source slots"),
]


@pytest.mark.parametrize("name,build,pattern",
                         _MUST_RAISE, ids=[c[0] for c in _MUST_RAISE])
def test_invalid_thermal_config_raises_with_a_useful_message(name, build, pattern):
    with pytest.raises(ValueError, match=pattern):
        _params(build())


def test_the_merged_fire_message_names_both_keys():
    """`min_fire_separation: 0` plus more than one fire must name BOTH keys.

    The reader has two ways out of this one — raise the separation, or drop the
    fire count to 1 — and a message naming only the separation hides the second.
    """
    with pytest.raises(ValueError) as exc:
        _params(_with_thermal(min_fire_separation=0))
    msg = str(exc.value)
    assert "thermal.min_fire_separation" in msg
    assert "count_high" in msg


def test_failure_message_reports_all_three_distances():
    """The message must carry the numbers, not just the verdict.

    Retuning a thermal config means moving `default_temp` or the ratio until the
    three equilibria straddle the thresholds correctly. A message that says only
    "structure check failed" sends the reader back to this source file.
    """
    with pytest.raises(ValueError) as exc:
        _params(_with_fire(temperature_ratio=[3, 4]))
    msg = str(exc.value)
    for token in ("d0 = ", "d1 = ", "d3 = ", "thermal.default_temp",
                  "temperature_ratio", "thermal.sigma"):
        assert token in msg, f"failure message does not mention {token!r}:\n{msg}"


# ── 2. configs that must still LOAD — the earlier stages' regression guard ────

def _stage1_degenerate(n_fires, temperature, baseline):
    """Stage 1's oracle configs (tests/env/test_thermal_field.py)."""
    d = _campfire_dict()
    d["thermal"]["default_temp"] = [baseline, baseline]
    d["thermal"]["use_random_spots"] = False
    fire = _fire_entry(d)
    fire.pop("temperature_ratio", None)
    fire.pop("count_low", None)
    fire.pop("count_high", None)
    fire["count"] = n_fires
    fire["temperature"] = temperature
    return d


def _stage_uniform(cell_temp):
    """The shape Stages 2, 4 and 5 all use: no object sources, flat field."""
    d = _no_confounders(_campfire_dict())
    d["thermal"]["use_object_sources"] = False
    d["thermal"]["use_random_spots"] = False
    d["thermal"]["default_temp"] = [float(cell_temp), float(cell_temp)]
    d["body"]["metabolic_cost"] = 0.0
    return d


_MUST_LOAD = [
    ("shipped_campfire_world", _campfire_dict),
    ("thermal_off_default", _default_dict),
    # Stage 1 — the oracle configs. These are thermal-ON, object-sources-ON and
    # DO declare a heat source, so the plan's stated precondition would have run
    # the check on them; two of the three then fail it and cannot be retuned
    # into the band without destroying what they test. See the note in
    # `_check_thermal_structure` for why the ratio/absolute split is the
    # exemption that was chosen.
    ("stage1_abs300_over_minus25",
     lambda: _stage1_degenerate(1, 300.0, -25.0)),
    ("stage1_abs100_over_zero_baseline",
     lambda: _stage1_degenerate(2, 100.0, 0.0)),
    ("stage1_abs100_over_minus25",
     lambda: _stage1_degenerate(2, 100.0, -25.0)),
    ("stage1_three_fires", lambda: (lambda d: (
        _fire_entry(d).pop("count_low", None),
        _fire_entry(d).pop("count_high", None),
        _fire_entry(d).update(count=3), d)[-1])(_campfire_dict())),
    ("stage1_food_min_fire_distance", lambda: _with_thermal(food_min_fire_distance=4)),
    ("bush_min_fire_distance_3", lambda: _with_thermal(bush_min_fire_distance=3)),
    ("stage1_thermal_on_constraints_zero", lambda: (lambda d: (
        d["thermal"].update(enabled=True, min_fire_separation=0,
                            food_min_fire_distance=0), d)[-1])(_default_dict())),
    # Stage 2 — the uniform-field body configs.
    ("stage2_uniform_minus25", lambda: _stage_uniform(-25.0)),
    ("stage2_uniform_plus30", lambda: _stage_uniform(30.0)),
    # Stage 3 — the thermoceptor configs.
    ("stage3_noise_on", lambda: (lambda d: (
        d["perceptual_noise"].update(enabled=True), d)[-1])(_campfire_dict())),
    ("stage3_absolute_readings", lambda: _with_thermal(relative=False)),
    ("stage3_thermal_off_variant", lambda: _with_thermal(enabled=False)),
    # Stage 4 — the reward-gate config (temperature is the only live axis).
    ("stage4_thermal_only", lambda: (lambda d: (
        d["body"].update(with_nutrition=False, with_injury=False),
        d)[-1])(_stage_uniform(-10.0))),
    # Stage 5 — the metabolic-coupling fixture.
    ("stage5_coupling_on", lambda: (lambda d: (
        d["thermal"].update(metabolic_coupling=True, metabolic_coupling_rate=2.0),
        d)[-1])(_stage_uniform(0.0))),
    # Mode A — random spots, no object sources: there is no fire to check.
    ("mode_a_random_spots", lambda: _with_thermal(
        use_random_spots=True, use_object_sources=False)),
    # A thermal-on world whose entities all sit at temperature 0.0.
    ("all_entities_at_zero_temperature", lambda: (lambda d: (
        _fire_entry(d).pop("temperature_ratio", None),
        _fire_entry(d).update(temperature=0.0), d)[-1])(_campfire_dict())),
]


@pytest.mark.parametrize("name,build", _MUST_LOAD, ids=[c[0] for c in _MUST_LOAD])
def test_earlier_stage_configs_still_load(name, build):
    """A structure check that rejects any of these is over-broad.

    Asserted HERE rather than discovered later, because the failure mode is four
    earlier stages silently becoming unrunnable.
    """
    params = load_env_params(Config(build()))
    assert params is not None


def test_skip_is_logged_rather_than_silent(caplog):
    """Every skip says which precondition failed, so a config is never quietly
    uncertified. The reader must be able to tell "checked and passed" from
    "never checked" by reading the log."""
    import logging
    with caplog.at_level(logging.INFO, logger="src.environment.config_loader"):
        _params(_with_thermal(use_random_spots=True, use_object_sources=False))
    assert any("structure check SKIPPED" in r.message and "use_object_sources" in r.message
               for r in caplog.records), \
        "mode A loaded without logging why the structure check did not run"

    caplog.clear()
    with caplog.at_level(logging.INFO, logger="src.environment.config_loader"):
        _params(_stage1_degenerate(1, 300.0, -25.0))
    assert any("structure check SKIPPED" in r.message and "ABSOLUTE" in r.message
               for r in caplog.records), \
        "an absolute-temperature config loaded without logging that it is not certified"


# ── 3. the two computational corrections ──────────────────────────────────────

def test_general_equilibrium_used():
    """A config that is legal under the general fixed point and illegal under the
    setpoint-zero special case must LOAD.

    The recurrence's fixed point is

        T* = (k_ex*T_field + k_loss*setpoint + k_metabolic) / (k_ex + k_loss)

    The design sandbox quotes `k_ex*T_field / (k_ex + k_loss)`, which is only
    correct when `temperature_setpoint` and `k_metabolic` are both zero. Both are
    config keys with non-zero-capable values.

    The config below has `temperature_setpoint: 5.0`, which shifts every
    equilibrium by `0.2 * 5.0 = +1.0`. The fire's own cell settles at +15.97 —
    above the +15 death threshold, so the fire hurts and the structure holds —
    while the special case puts it at +14.97, inside the survivable band, and
    would reject the config for having a fire with no bite. The numbers are
    asserted explicitly so the test fails loudly if either formula moves.
    """
    d = _no_confounders(_campfire_dict())
    d["thermal"]["default_temp"] = [-30.0, -30.0]
    d["thermal"]["temperature_setpoint"] = 5.0
    _fire_entry(d)["temperature_ratio"] = [5.0, 5.0]
    _fire_entry(d).pop("count_low", None)
    _fire_entry(d).pop("count_high", None)
    _fire_entry(d)["count"] = 1

    params = _params(d)          # must not raise
    assert float(params.temperature_setpoint) == 5.0

    k_ex, k_loss = float(params.thermal_k_exchange), float(params.thermal_k_loss)
    k_met = float(params.thermal_k_metabolic)
    general = _thermal_radial_equilibria(
        5.0 * 30.0, -30.0, float(params.thermal_sigma),
        int(params.thermal_kernel_radius), int(params.height), int(params.width),
        k_ex, k_loss, k_met, 5.0)
    setpoint_zero = _thermal_radial_equilibria(
        5.0 * 30.0, -30.0, float(params.thermal_sigma),
        int(params.thermal_kernel_radius), int(params.height), int(params.width),
        k_ex, k_loss, k_met, 0.0)

    t_hi = float(params.max_temperature)
    assert general[0] > t_hi, (
        f"the general formula must find the fire lethal; got {general[0]:+.2f} "
        f"against a threshold of {t_hi}")
    assert setpoint_zero[0] <= t_hi, (
        f"this config no longer distinguishes the two formulas: the setpoint-zero "
        f"form also finds the fire lethal at {setpoint_zero[0]:+.2f}")
    np.testing.assert_allclose(general[0] - setpoint_zero[0],
                               k_loss * 5.0 / (k_ex + k_loss), rtol=1e-5)


def test_the_equilibrium_is_the_recurrence_fixed_point():
    """`_thermal_equilibrium` must be the value `update_body`'s recurrence stops at.

    Checked by iterating the recurrence itself rather than by re-deriving the
    algebra: an equilibrium formula verified against its own rearrangement would
    prove nothing about the environment.
    """
    k_ex, k_loss, k_met, setpoint, ambient = 0.04, 0.01, 0.3, 5.0, -20.0
    t = 0.0
    for _ in range(5000):
        t = t + k_ex * (ambient - t) + k_met - k_loss * (t - setpoint)
    np.testing.assert_allclose(
        t, _thermal_equilibrium(ambient, k_ex, k_loss, k_met, setpoint),
        rtol=1e-6,
        err_msg="the closed form is not where the recurrence actually settles")


def test_check_uses_the_reset_blur():
    """The field the check evaluates must be the field `jax_reset` builds.

    A numpy re-implementation of the blur would validate a world the environment
    never constructs — the exact circular verification this whole plan exists to
    avoid — and would drift silently the first time the kernel is touched.

    The config is DEGENERATE on purpose, and it has to be for the test to be
    well-posed: the check evaluates the CORNERS of the sampled ranges while
    `jax_reset` draws ONE sample, so on a normal config the two are comparing
    different worlds and equality is not even meaningful. With single-valued
    ranges (`default_temp: [-25, -25]`, `temperature_ratio: [12, 12]`), a single
    fire, and a spawn area of exactly one cell — the grid centre, where the check
    puts its fire — the corner, the midpoint and the drawn sample are all the
    same field.
    """
    d = _no_confounders(_campfire_dict())
    d["thermal"]["default_temp"] = [-25.0, -25.0]
    d["thermal"]["use_random_spots"] = False
    d["environment"]["resources"] = []          # nothing else may stamp or move
    fire = _fire_entry(d)
    fire.pop("count_low", None)
    fire.pop("count_high", None)
    fire["count"] = 1
    fire["temperature_ratio"] = [12.0, 12.0]
    fire.pop("edge_margin", None)
    fire["area"] = [[6, 6], [6, 6]]              # 1-based -> grid cell (5, 5)

    params = _params(d)
    H, W = int(params.height), int(params.width)
    assert (H // 2, W // 2) == (5, 5), "this test pins the fire to the grid centre"

    state = jax_reset(params, jax.random.PRNGKey(0))
    fires = np.flatnonzero(np.asarray(params.obs_temp_ratio_low) != 0.0)
    assert len(fires) == 1
    pos = np.asarray(state.obs_pos)[fires[0]]
    assert tuple(int(x) for x in pos) == (5, 5), (
        f"the fire spawned at {tuple(int(x) for x in pos)}, not the grid centre — "
        f"the two fields are then not comparable")

    checked = _thermal_single_fire_field(
        12.0 * 25.0, -25.0, float(params.thermal_sigma),
        int(params.thermal_kernel_radius), H, W)

    np.testing.assert_allclose(
        np.asarray(state.thermal_field), checked, rtol=1e-5, atol=1e-4,
        err_msg="the load-time check is not evaluating the field jax_reset builds")


def test_heat_source_is_counted_per_slot_not_per_entry():
    """Two separate single-count fire entries are TWO fires, not one.

    The obvious wrong reading of "a heat source" is "an entry with
    `count_high > 1`", which lets two separate single-count entries through as
    "only one fire" when they can in fact spawn adjacent and merge. The shared
    definition in `core.heat_source_mask` counts SLOTS, after `count_high`
    expansion, and this is the case that tells the two readings apart.
    """
    d = _campfire_dict()
    fire = _fire_entry(d)
    fire.pop("count_low", None)
    fire.pop("count_high", None)
    fire["count"] = 1
    second = copy.deepcopy(fire)
    second["name"] = "campfire2"
    d["environment"]["obstacles"].append(second)
    d["thermal"]["min_fire_separation"] = 0

    with pytest.raises(ValueError, match=r"min_fire_separation is 0 while 2 heat-source slots"):
        _params(d)
