"""Stage 5 of the temperature system — defending body temperature costs nutrition.

**Plain-language summary.** The body already fights the cold: every step it undoes
a slice of its own deviation from the setpoint (the `k_loss` term of the
body-temperature recurrence). Until now that fight was free. This stage makes it
cost food, by draining nutrition in proportion to the work — and ships the whole
thing switched off (`thermal.metabolic_coupling: false`).

Because it ships off, **the no-op proof is the important test in this file**, not
the feature test. A coupling that silently drew nutrition while claiming to be
disabled would change the outcome of every future run without changing a single
line of any config, and nothing in the existing suite would notice: the Stage 0
parity fixtures are all thermal-OFF configs by construction
(`test_thermal_parity.py` asserts exactly that), so they are structurally blind to
a leak in code that only exists on a thermal-ON world.

So `test_off_by_default_is_a_provable_noop` compares a 300-step thermal-ON
rollout — every numeric state field, the reward, `done`, every numeric `info`
entry — against a fixture captured from a git worktree of the **Stage 4 tip**,
i.e. from source that predates the coupling. It is a comparison with ground truth
that could not have been contaminated by the change, which is the same reason the
Stage 0 fixtures exist. Fixture generator:
`scripts/fixtures/generate_metabolic_coupling_fixture.py`.

The rest of the file stops the no-op proof from being satisfied by an
implementation that does nothing at all: the drain must fire when switched on,
must match the closed form `rate * |k_loss * (T - setpoint)|` per step, must cost
nothing while the body sits at its setpoint, and must not be able to sneak
nutrition below zero or past the starvation check.
"""
import os

# Backend pinning MUST precede any jax import — the fixture was generated on CPU
# and this file holds it to `array_equal` with no tolerance. Same form as the
# other thermal tests and the fixture generators.
os.environ.setdefault("JAX_PLATFORMS", "cpu")

import copy
import dataclasses
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

THERMAL_CONFIG = os.path.join(
    _ROOT, "configs", "environment", "experiment", "archive", "thermal", "campfire_world.yaml")
DEFAULT_CONFIG = os.path.join(_ROOT, "configs", "environment", "default.yaml")
FIXTURE = os.path.join(
    _ROOT, "tests", "env", "fixtures", "metabolic_coupling",
    "thermal_on_coupling_off.npz")

# These three MUST match scripts/fixtures/generate_metabolic_coupling_fixture.py
# (CONFIG_REL / ACTIONS / SEED). The fixture is a recording of exactly this
# rollout; a drift in any of them turns the no-op proof into a comparison
# between two different experiments.
ACTIONS = [0, 1, 2, 3, 4, 5, 1, 1, 2, 2] * 30
SEED = 0

REST = 4


def _numeric_leaves(state, tag):
    """Mirror of the generator's `numeric_leaves` — every numeric EnvState field."""
    out = {}
    for f in dataclasses.fields(state):
        value = getattr(state, f.name)
        try:
            arr = np.asarray(value)
        except Exception:
            continue
        if arr.dtype.kind in "biufc":
            out[f"{tag}.{f.name}"] = arr
    return out


def _load(path_or_dict):
    if isinstance(path_or_dict, dict):
        return load_env_params(Config(path_or_dict))
    with open(path_or_dict) as fh:
        d = yaml.safe_load(fh)
        # Archived raw input: not migrated for the water gate (project policy); supplied in memory, `false` = the pre-water world (THIRST_WATER_PLAN).
        d.setdefault("water", {"enabled": False})
        return load_env_params(Config(d))


# ══════════════════════════════════════════════════════════════════════════════
# 1. The no-op proof — the reason this stage is safe to ship enabled-by-nobody
# ══════════════════════════════════════════════════════════════════════════════

def test_off_by_default_is_a_provable_noop():
    """A 300-step thermal-ON rollout, bit-identical to the pre-Stage-5 fixture.

    Thermal ON is the point. The coupling code lives inside the thermal-on world,
    so a thermal-off comparison — which is all the Stage 0 fixtures can offer —
    cannot see a leak in it.

    Held to `np.array_equal` across every numeric state leaf, the reward, `done`
    and every numeric `info` entry. If this goes red, the drain is firing while
    disabled (or something else in `update_body` moved); do NOT add a tolerance
    and do NOT regenerate the fixture from the working tree — the fixture's whole
    value is that it predates this stage.
    """
    fixture = np.load(FIXTURE)
    params = _load(THERMAL_CONFIG)
    assert params.thermal_enabled, (
        "the no-op proof is worthless on a thermal-off config — the coupling "
        "code path only exists when thermal is on")
    assert params.with_nutrition, (
        "the no-op proof is worthless with nutrition off — nutrition is the "
        "quantity the coupling moves")
    assert not params.thermal_metabolic_coupling, (
        "campfire_world.yaml must ship with thermal.metabolic_coupling: false")

    state = jax_reset(params, jax.random.PRNGKey(SEED))
    series = {}

    def push(d):
        for k, v in d.items():
            series.setdefault(k, []).append(v)

    push(_numeric_leaves(state, "state"))
    for action in ACTIONS:
        state, reward, done, info = jax_step(state, action, params)
        push(_numeric_leaves(state, "state"))
        rec = {"reward": np.asarray(reward), "done": np.asarray(done)}
        for k, v in sorted(info.items()):
            try:
                arr = np.asarray(v)
            except Exception:
                continue
            if arr.dtype.kind in "biufc":
                rec[f"info.{k}"] = arr
        push(rec)

    got = {k: np.stack(v) for k, v in series.items()}
    expected_keys = set(fixture.files) - {"_provenance_sha"}
    assert set(got) == expected_keys, (
        f"captured fields differ from the fixture's: "
        f"only-now={sorted(set(got) - expected_keys)}, "
        f"only-fixture={sorted(expected_keys - set(got))}")

    sha = str(fixture["_provenance_sha"])
    for key in sorted(expected_keys):
        have, want = got[key], fixture[key]
        assert np.array_equal(have, want), (
            f"'{key}' is not bit-identical to the pre-Stage-5 fixture (captured at "
            f"{sha}). max |diff| = "
            f"{float(np.abs(have.astype(np.float64) - want.astype(np.float64)).max()):.6e}. "
            f"With thermal.metabolic_coupling false this rollout must be exactly "
            f"the Stage 4 rollout.")

    # The recording must not be vacuously constant, or "bit-identical" is cheap.
    assert got["state.body_temp"].min() < -5.0, (
        "the fixture rollout barely moves the body temperature — it cannot "
        "detect a drain proportional to the deviation from setpoint")
    assert np.ptp(got["state.nutrition"]) > 1.0, (
        "the fixture rollout barely moves nutrition — it cannot detect a "
        "nutrition drain")


def test_shipped_configs_have_the_coupling_off():
    """Both configs carrying a full thermal block default to coupling OFF.

    Cheap, and it is the thing that makes every *other* run in the project safe:
    the no-op proof above only covers the config it runs.
    """
    for path in (DEFAULT_CONFIG, THERMAL_CONFIG):
        params = _load(path)
        assert params.thermal_metabolic_coupling is False, (
            f"{os.path.relpath(path, _ROOT)} ships with metabolic coupling ON")


def test_thermal_off_carries_the_inert_sentinel():
    """Thermal off forces coupling off, whatever the YAML says.

    `metabolic_coupling` is conditional-mandatory under `thermal.enabled`, so on a
    thermal-off config the key is not read at all. This asserts what it is *set*
    to instead — False, the value that makes the drain untraceable — rather than
    leaving the thermal-off path to inherit whatever a stray key happened to say.
    """
    d = yaml.safe_load(open(DEFAULT_CONFIG))
    assert d["thermal"]["enabled"] is False
    # A stray true here must not switch anything on: thermal is the outer gate.
    d["thermal"]["metabolic_coupling"] = True
    params = _load(d)
    assert params.thermal_metabolic_coupling is False
    assert float(params.thermal_metabolic_coupling_rate) == 0.0


# ══════════════════════════════════════════════════════════════════════════════
# 2. The coupling is real when switched on
# ══════════════════════════════════════════════════════════════════════════════

def _uniform_field_config(coupling, rate=2.0, max_steps=500):
    """A thermal-on world whose field is a known constant, with nutrition live.

    Every choice here is load-bearing for the closed-form assertions below:

    * both heat-source mechanisms off and a degenerate `default_temp` — blurring a
      constant returns the constant, so the field is known without reading it back
      out of the environment. The rollout helper then overwrites `thermal_field`
      directly anyway, so a single params object serves several temperatures.
    * entities and non-food resources stripped — the agent must not take damage
      (injury is a second nutrition-independent way to die) and must not be chased
      off the cell whose temperature the closed form assumes.
    * nutrition left ON with its real `metabolic_cost` — unlike the Stage 4 reward
      tests, nutrition is the quantity under test here, so it cannot be switched
      off. The closed form carries `metabolic_cost` explicitly instead.
    """
    d = copy.deepcopy(yaml.safe_load(open(THERMAL_CONFIG)))
    # Archived raw input: not migrated for the water gate (project policy); supplied in memory, `false` = the pre-water world (THIRST_WATER_PLAN).
    d.setdefault("water", {"enabled": False})
    d["thermal"]["use_object_sources"] = False
    d["thermal"]["use_random_spots"] = False
    d["thermal"]["default_temp"] = [0.0, 0.0]
    d["thermal"]["metabolic_coupling"] = bool(coupling)
    d["thermal"]["metabolic_coupling_rate"] = float(rate)
    d["environment"]["entities"] = []
    d["environment"]["obstacles"] = [
        o for o in d["environment"]["obstacles"] if o.get("name") == "campfire"]
    d["environment"]["resources"] = [
        r for r in d["environment"]["resources"] if r.get("type") == "food"]
    d["environment"]["max_steps"] = int(max_steps)
    d["body"]["with_injury"] = False
    return d


def _rest_rollout(params, n_steps, field_value, seed=0):
    """Rest in place in a uniform field, recording the pre-step body temperature.

    The field is written straight into the state — the same `_replace` trick
    `test_thermal_body.py::test_body_reads_the_post_move_cell` and the Stage 4
    reward tests use — so the world's temperature is set by this call rather than
    by wherever placement happened to put a fire.

    `body_temp_pre[t]` is the temperature the drain on step t is charged against;
    recording it (rather than the post-step value) is what lets the closed form
    below be an equality instead of an approximation.
    """
    H, W = int(params.height), int(params.width)
    field = jnp.full((H, W), float(field_value), dtype=jnp.float32)
    state = jax_reset(params, jax.random.PRNGKey(seed))
    state = state.replace(thermal_field=field)

    rec = {"body_temp_pre": [], "nutrition": [float(state.nutrition)],
           "ate_food": [], "done": [], "reason": []}
    for _ in range(n_steps):
        rec["body_temp_pre"].append(float(state.body_temp))
        state, _reward, done, info = jax_step(state, REST, params)
        rec["nutrition"].append(float(state.nutrition))
        rec["ate_food"].append(bool(info["ate_food"]))
        rec["done"].append(bool(done))
        rec["reason"].append(int(info["termination_reason"]))
    return {k: np.asarray(v) for k, v in rec.items()}


def test_on_costs_nutrition_in_the_cold():
    """Nutrition falls strictly faster in the cold, by exactly the closed form.

    Two rollouts of the same length in the same world at two field temperatures:
    one at the setpoint, one at -25. The setpoint rollout is the control — the
    body never leaves the setpoint there, so there is no defence to pay for and
    nutrition must fall at exactly `metabolic_cost`. Anything the cold rollout
    loses beyond that is the coupling, and it is checked against
    `rate * |k_loss * (T_t - setpoint)|` step by step, using the *recorded* body
    temperatures. That closed form fails if the drain is charged on the raw
    deviation instead of the `k_loss` work, on the post-step temperature instead
    of the pre-step one, or at the wrong rate.
    """
    n = 60
    params = _load(_uniform_field_config(coupling=True, rate=2.0))
    assert params.thermal_metabolic_coupling is True
    warm = _rest_rollout(params, n, field_value=float(params.temperature_setpoint))
    # -15 rather than a deeper cold on purpose: the body's fixed point is
    # k_exchange*T_field/(k_exchange + k_loss) = -12, comfortably inside the
    # survivable band, so the agent does not freeze part-way through and leave
    # the two rollouts different lengths.
    cold = _rest_rollout(params, n, field_value=-15.0)

    # De-confounders, checked rather than assumed.
    assert not warm["ate_food"].any() and not cold["ate_food"].any(), (
        "the agent ate during a rollout — the closed form below omits the refill")
    assert not warm["done"].any() and not cold["done"].any(), (
        "a rollout ended early; the comparison needs both to run the full length")
    assert np.allclose(warm["body_temp_pre"], float(params.temperature_setpoint)), (
        "the control rollout left the setpoint — it is no longer a zero-defence "
        "control")

    cost = float(params.metabolic_cost)
    # Control: no defence, so nutrition falls at exactly metabolic_cost.
    assert np.allclose(np.diff(warm["nutrition"]), -cost, atol=1e-4)

    # Cold: strictly faster, on every step after the body has actually left the
    # setpoint (step 0 starts exactly on it, so its drain is genuinely zero).
    warm_drop = -np.diff(warm["nutrition"])
    cold_drop = -np.diff(cold["nutrition"])
    assert np.all(cold_drop[1:] > warm_drop[1:] + 1e-6), (
        "nutrition does not fall faster in the cold — the coupling is not firing")

    # And the magnitude, per step, from the recorded temperatures.
    expected_drain = (float(params.thermal_metabolic_coupling_rate)
                      * np.abs(float(params.thermal_k_loss)
                               * (cold["body_temp_pre"] - float(params.temperature_setpoint))))
    np.testing.assert_allclose(cold_drop, cost + expected_drain, atol=1e-4)


def test_defending_against_heat_costs_the_same_as_against_cold():
    """The bill is on |work|, so a hot world charges like an equally cold one.

    The `k_loss` term of the recurrence is signed — it pushes the body down when
    it is too warm and up when it is too cold — and the energy cost of doing so is
    not. Without the absolute value this test fails by *paying* the agent to
    overheat, which is the sign error most likely to survive a code read.
    """
    n = 40
    params = _load(_uniform_field_config(coupling=True, rate=2.0))
    setpoint = float(params.temperature_setpoint)
    cold = _rest_rollout(params, n, field_value=setpoint - 15.0)
    hot = _rest_rollout(params, n, field_value=setpoint + 15.0)
    np.testing.assert_allclose(cold["body_temp_pre"] - setpoint,
                               -(hot["body_temp_pre"] - setpoint), atol=1e-4)
    np.testing.assert_allclose(cold["nutrition"], hot["nutrition"], atol=1e-4)


def test_at_the_setpoint_the_coupling_is_free():
    """Coupling on but body at setpoint: identical to coupling off.

    Separates "the drain exists" from "the drain is proportional to the work". An
    implementation that charged a flat per-step fee whenever the flag is on would
    pass `test_on_costs_nutrition_in_the_cold` and fail here.
    """
    n = 40
    setpoint = float(_load(_uniform_field_config(coupling=False)).temperature_setpoint)
    off = _rest_rollout(_load(_uniform_field_config(coupling=False)), n, setpoint)
    on = _rest_rollout(_load(_uniform_field_config(coupling=True, rate=5.0)), n, setpoint)
    np.testing.assert_array_equal(on["nutrition"], off["nutrition"])


def test_drain_cannot_go_negative_or_bypass_starvation():
    """An absurd rate floors nutrition at exactly 0.0 and dies of starvation.

    The drain is applied before the single `jnp.clip(..., 0.0, max_nutrition)`, and
    the termination test reads the clipped value, so an over-large drain must land
    on 0.0 and trip termination reason 2 — not go negative, not produce a NaN, and
    not step past the starvation check into an episode that continues with
    impossible nutrition.
    """
    params = _load(_uniform_field_config(coupling=True, rate=1e6))
    rec = _rest_rollout(params, 40, field_value=-15.0)
    assert np.isfinite(rec["nutrition"]).all(), "nutrition went non-finite"
    assert (rec["nutrition"] >= 0.0).all(), (
        f"nutrition went negative: min={rec['nutrition'].min()}")
    assert rec["nutrition"].min() == 0.0, (
        "a 1e6 coupling rate did not empty nutrition — the drain is being "
        "clamped or ignored somewhere upstream of the clip")
    first_zero = int(np.argmax(rec["nutrition"][1:] <= 0.0))
    assert rec["done"][first_zero], "nutrition hit zero without ending the episode"
    assert rec["reason"][first_zero] == 2, (
        f"nutrition hit zero but the termination reason is "
        f"{rec['reason'][first_zero]}, not 2 (starvation) — the drain has routed "
        f"around the starvation path")


# ══════════════════════════════════════════════════════════════════════════════
# 3. Config contract
# ══════════════════════════════════════════════════════════════════════════════

def test_rate_is_mandatory_once_the_coupling_is_on():
    """No fallback default: switching the coupling on without a rate must raise.

    The project rule is that a critical key has no default. The rate is exactly
    that — a silent 0.0 would give a coupling that is switched on and does
    nothing, which is the failure mode hardest to notice in a training log.
    """
    d = _uniform_field_config(coupling=True)
    del d["thermal"]["metabolic_coupling_rate"]
    with pytest.raises(ValueError, match="thermal.metabolic_coupling_rate"):
        _load(d)


def test_metabolic_coupling_itself_is_mandatory_when_thermal_is_on():
    d = _uniform_field_config(coupling=True)
    del d["thermal"]["metabolic_coupling"]
    with pytest.raises(ValueError, match="thermal.metabolic_coupling"):
        _load(d)


def test_negative_rate_is_rejected():
    """A negative rate would pay the agent for standing in the cold."""
    d = _uniform_field_config(coupling=True, rate=-0.5)
    with pytest.raises(ValueError, match="thermal.metabolic_coupling_rate"):
        _load(d)


def test_rate_is_not_read_while_the_coupling_is_off():
    """Conditional-mandatory one level deeper: off means the key need not exist.

    Keeps the migration cheap — a thermal-on config that never intends to switch
    the coupling on is not forced to carry a number nothing reads.
    """
    d = _uniform_field_config(coupling=False)
    del d["thermal"]["metabolic_coupling_rate"]
    params = _load(d)
    assert params.thermal_metabolic_coupling is False
    assert float(params.thermal_metabolic_coupling_rate) == 0.0
