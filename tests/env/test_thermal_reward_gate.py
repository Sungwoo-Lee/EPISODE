"""Stage 4 of the temperature system — body temperature as the third drive axis.

Two claims, and they pull in opposite directions on purpose.

**1. The gate.** With `thermal.enabled: false` the reward and the drive must be
*bit-identical* to what they were before any thermal code existed. This is checked
against the Stage 0 `.npz` fixtures — captured before `calculate_drive` was touched
— so it is a comparison with pre-change ground truth, not a re-derivation through
the edited function. The thermal-off branch of `calculate_drive` is the pre-thermal
three lines verbatim under a static `if params.thermal_enabled:`, so this test
should be provable by reading the source; it exists because "should be" is not the
same as "is".

**2. The axis is actually wired in.** A gate test alone is satisfied perfectly by an
implementation that computes the thermal axis and then never adds it to the norm —
or that takes the thermal-off branch in both cases. `test_thermal_axis_moves_the_drive`
and `test_reward_tracks_the_thermal_axis_alone` are what refuse that.

**Why this file does not measure the reward on a walking agent.** The obvious test —
"walk away from the fire, assert the reward goes negative" — is circular here.
`metabolic_cost: 1.0` drains nutrition on *every* step, so satiation falls and the
homeostatic reward is already negative on any outward walk, thermal axis or not. The
test would be just as green against an implementation that does nothing. So the
configs below switch **`with_nutrition: false` and `with_injury: false`** and start
satiation exactly at its setpoint, which puts the first two axes at a constant zero
and leaves temperature as the only live term in the drive. Every rollout re-asserts
that the two axes really did stay flat, so the de-confounding is checked rather than
assumed.

The magnitude oracle is numpy, built from the design's own formula and from the
*recorded* body-temperature trajectory. It therefore fails if the thermal axis is
missing, mis-scaled (the design's literal 1/max_temperature normalisation instead of
the F1 rescale into satiation units), squared, or counted twice.
"""
import os

# Backend pinning MUST precede any jax import — same form as the other thermal
# tests and the fixture generator. Fixtures were generated on CPU.
os.environ.setdefault("JAX_PLATFORMS", "cpu")

import copy
import glob
import re
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
from src.environment.core import jax_reset, jax_step, calculate_drive

FIXTURE_DIR = os.path.join(_ROOT, "tests", "env", "fixtures", "thermal_parity")
ACTIONS = [0, 1, 2, 3, 4] * 20   # 100 steps — must match the Stage 0 generator
SEED = 0

THERMAL_CONFIG = os.path.join(
    _ROOT, "configs", "environment", "experiment", "archive", "thermal", "campfire_world.yaml")

REST = 4


# ══════════════════════════════════════════════════════════════════════════════
# 1. The gate — thermal off is bit-identical to the pre-thermal reference
# ══════════════════════════════════════════════════════════════════════════════

def _config_slug(config_path):
    """Matches scripts/fixtures/generate_thermal_parity_fixtures.py:config_slug."""
    rel = os.path.relpath(config_path, _ROOT)
    slug = re.sub(r'[/\\]', '__', rel)
    slug = re.sub(r'\.yaml$', '', slug)
    return re.sub(r'[^A-Za-z0-9_.-]', '_', slug)


def _collect_configs():
    """Matches scripts/fixtures/generate_thermal_parity_fixtures.py:collect_configs, archive
    exclusion included.

    `configs/environment/experiment/archive/**` is EXCLUDED. Per the settings-tree
    maintenance policy (CONFIG_CRITICAL_SETTINGS.md, 2026-09-15), the project maintains
    only `configs/environment/default.yaml` and `experiment/basic/`; archived worlds are
    explicitly NOT kept loadable and are regenerated fresh when needed. This is the FOURTH
    verbatim copy of this collector (the others are in
    `scripts/fixtures/generate_thermal_parity_fixtures.py`,
    `tests/env/test_thermal_parity.py` and `tests/env/test_backward_compat_configs.py`);
    keep all four in step.
    """
    configs = []
    configs += sorted(
        p for p in glob.glob(os.path.join(_ROOT, "configs", "environment", "experiment", "**", "*.yaml"), recursive=True)
        if os.sep + "archive" + os.sep not in p
    )
    configs += sorted(glob.glob(os.path.join(_ROOT, "configs", "continual", "**", "*.yaml"), recursive=True))
    configs += sorted(glob.glob(os.path.join(_ROOT, "configs", "verification", "**", "*.yaml"), recursive=True))
    env_default = os.path.join(_ROOT, "configs", "environment", "default.yaml")
    if env_default not in configs:
        configs.append(env_default)
    return configs


_fixture_cases = [
    (p, _config_slug(p)) for p in _collect_configs()
    if os.path.exists(os.path.join(FIXTURE_DIR, _config_slug(p) + ".npz"))
]


@pytest.mark.parametrize("config_path,slug", _fixture_cases,
                         ids=[c[1] for c in _fixture_cases])
def test_drive_bit_identical_when_thermal_off(config_path, slug):
    """Reward and drive over 100 steps, exactly equal to the Stage 0 fixture.

    Narrower than `test_thermal_parity.py` (that one adjudicates observations and
    placement too) and deliberately so: this is the *reward* gate for Stage 4, and
    it holds reward and both drives to `array_equal` with no tolerance of any
    kind. There is nothing here that a legitimate implementation can move — the
    ulp exemption `test_thermal_parity.py` documents is anchored on the sampled
    property arrays, and reward is not downstream of a divergence that small on
    these fixtures (which is itself asserted there, exactly).

    If this goes red: diff the drive expression. Do NOT add a tolerance — the
    whole value of the Stage 0 fixtures is that they predate the edit.
    """
    with open(config_path) as f:
        params = load_env_params(Config(yaml.safe_load(f)))
    assert not params.thermal_enabled, (
        f"{slug}: fixture config has thermal ON. The Stage 0 fixtures are the "
        f"PRE-thermal reference; a thermal-on config cannot be compared with them."
    )

    fixture = np.load(os.path.join(FIXTURE_DIR, slug + ".npz"))

    state = jax_reset(params, jax.random.PRNGKey(SEED))
    drives = [np.array(calculate_drive(state.satiation, state.injury_level, params))]
    rewards = []
    for action in ACTIONS:
        state, reward, _done, _info = jax_step(state, action, params)
        rewards.append(np.array(reward))
        drives.append(np.array(calculate_drive(state.satiation, state.injury_level, params)))

    got = {
        "reward": np.stack(rewards),
        "drive_before": np.stack(drives[:-1]),
        "drive_after": np.stack(drives[1:]),
    }
    for field, have in got.items():
        assert np.array_equal(have, fixture[field]), (
            f"{slug}: '{field}' is not bit-identical to the pre-thermal Stage 0 "
            f"fixture. max |diff| = "
            f"{float(np.abs(have.astype(np.float64) - fixture[field].astype(np.float64)).max()):.3e}. "
            f"The thermal-off branch of calculate_drive must be the pre-thermal "
            f"expression — diff it, do not widen this."
        )


def test_thermal_off_ignores_body_temp_entirely():
    """On a thermal-off config the drive does not depend on `body_temp` at all.

    The companion to the fixture test above, and the cheap one: it says the
    thermal-off branch is not merely *equal* to the old answer on the fixture
    trajectories but *independent of the third argument*, which is what "the old
    expression, untouched" actually means.
    """
    with open(os.path.join(_ROOT, "configs", "environment", "default.yaml")) as f:
        params = load_env_params(Config(yaml.safe_load(f)))
    assert not params.thermal_enabled

    sat, inj = jnp.asarray(42.0), jnp.asarray(7.0)
    base = float(calculate_drive(sat, inj, params))
    assert float(calculate_drive(sat, inj, params, jnp.asarray(0.0))) == base
    assert float(calculate_drive(sat, inj, params, jnp.asarray(-30.0))) == base
    assert float(calculate_drive(sat, inj, params, jnp.asarray(99.0))) == base
    # And the two-axis closed form, so this is not just self-consistency.
    assert base == pytest.approx(
        float(np.hypot(42.0 - float(params.setpoint), 7.0)), abs=1e-5)


# ══════════════════════════════════════════════════════════════════════════════
# 2. The axis is live — thermal on
# ══════════════════════════════════════════════════════════════════════════════

def _thermal_only_config(cell_temp, max_steps=500):
    """A thermal-on config in which temperature is the ONLY live drive axis.

    Every de-confounding choice here is load-bearing:

    * `with_nutrition: false` and `metabolic_cost: 0` — otherwise satiation falls
      on every single step and the reward is negative regardless of what the
      thermal axis does. This is the circularity the module docstring names.
    * `with_injury: false`, no animals, no damaging obstacles, no hiding predator
      — injury is the second axis and also, with `with_injury` off, an instant
      death on any damage at all.
    * `start_nutrition == max_nutrition` and `satiation_setpoint == max_satiation`
      (both already true in the base config) put satiation exactly ON its setpoint,
      so the first axis contributes exactly 0.0 rather than a large constant. The
      drive is then exactly the thermal axis, and `test_reward_tracks_the_thermal_axis_alone`
      can compare against a closed form with no cancellation error.
    * Both heat-source mechanisms off and a degenerate `default_temp` — the raw
      field is the constant `cell_temp` and blurring a constant returns it, so the
      field is known without reading it back out of the environment.

    The rollouts below re-assert the flatness of the first two axes rather than
    trusting this docstring.
    """
    d = copy.deepcopy(yaml.safe_load(open(THERMAL_CONFIG)))
    d["thermal"]["use_object_sources"] = False
    d["thermal"]["use_random_spots"] = False
    d["thermal"]["default_temp"] = [float(cell_temp), float(cell_temp)]
    d["environment"]["entities"] = []
    d["environment"]["obstacles"] = [
        o for o in d["environment"]["obstacles"] if o.get("name") == "campfire"]
    d["environment"]["resources"] = [
        r for r in d["environment"]["resources"] if r.get("type") == "food"]
    d["environment"]["max_steps"] = int(max_steps)
    d["body"]["with_nutrition"] = False
    d["body"]["with_injury"] = False
    d["body"]["metabolic_cost"] = 0.0
    return d


def _params(d):
    return load_env_params(Config(d))


def _rest_rollout(params, n_steps, field_value, seed=0, start_state=None):
    """Rest in place in a uniform field of `field_value`, recording what matters.

    The field is written directly into the state (the same `_replace` trick
    `test_thermal_body.py::test_body_reads_the_post_move_cell` uses) so that a
    *second* phase can run in a different field without rebuilding params — which
    is how the "walk back to the fire" half of the plan's test is expressed here
    without depending on where placement happened to put the fire.
    """
    H, W = int(params.height), int(params.width)
    field = jnp.full((H, W), float(field_value), dtype=jnp.float32)
    state = (jax_reset(params, jax.random.PRNGKey(seed)) if start_state is None
             else start_state)
    state = state._replace(thermal_field=field)

    rec = {"body_temp": [float(state.body_temp)], "reward": [], "drive_thermal": [],
           "satiation": [float(state.satiation)], "injury": [float(state.injury_level)]}
    for _ in range(n_steps):
        state, reward, done, info = jax_step(state, REST, params)
        rec["body_temp"].append(float(state.body_temp))
        rec["satiation"].append(float(state.satiation))
        rec["injury"].append(float(state.injury_level))
        rec["reward"].append(float(reward))
        rec["drive_thermal"].append(float(info["drive_thermal"]))
        assert not bool(info["ate_food"]), "the rest action must not eat; reward would gain a food term"
        assert not bool(done), "the episode ended early; this rollout must stay well inside the band"
    return {k: np.array(v) for k, v in rec.items()}, state


def _assert_other_axes_flat(rec, params):
    """The de-confounding, checked rather than assumed."""
    assert np.allclose(rec["satiation"], rec["satiation"][0], atol=0.0), (
        "satiation moved during the rollout — the hunger axis is live and this "
        "test can no longer attribute the reward to temperature")
    assert np.allclose(rec["injury"], rec["injury"][0], atol=0.0), (
        "injury moved during the rollout — the injury axis is live")
    assert rec["satiation"][0] == pytest.approx(float(params.setpoint), abs=1e-5), (
        f"satiation starts at {rec['satiation'][0]} but the setpoint is "
        f"{float(params.setpoint)}; the hunger axis is a non-zero constant and the "
        f"closed form below no longer isolates temperature")
    assert rec["injury"][0] == pytest.approx(0.0, abs=1e-5)


def test_thermal_axis_moves_the_drive():
    """`calculate_drive` must actually depend on `body_temp` when thermal is on.

    THE ANTI-CIRCULARITY TEST, at its smallest. An implementation that takes the
    two-axis branch on a thermal-on config — the exact mutation "gate the axis off
    in both branches" — passes every bit-parity check in this repository and fails
    only here and in the two below.

    The expected value is the F1 form written out independently: the thermal axis
    is `(T - T_setpoint) * max_satiation / max_temperature`, i.e. scaled INTO
    satiation units rather than the other two axes being scaled down. The design's
    literal normalised form would be 100x smaller and is rejected by the numbers.
    """
    params = _params(_thermal_only_config(-10.0))
    scale = float(params.max_satiation) / float(params.max_temperature)
    assert scale == pytest.approx(100.0 / 15.0), (
        f"the exchange rate moved: max_satiation/max_temperature = {scale}, expected 100/15")

    sat = jnp.asarray(float(params.setpoint))     # hunger axis exactly zero
    inj = jnp.asarray(0.0)
    t_set = float(params.temperature_setpoint)

    at_setpoint = float(calculate_drive(sat, inj, params, jnp.asarray(t_set)))
    assert at_setpoint == pytest.approx(0.0, abs=1e-5), (
        "with satiation on its setpoint, no injury and body temperature at the "
        "thermal setpoint, the drive must be exactly zero")

    for dev in (-8.0, -3.0, 1.5, 6.0):
        got = float(calculate_drive(sat, inj, params, jnp.asarray(t_set + dev)))
        assert got == pytest.approx(abs(dev) * scale, rel=1e-5), (
            f"drive at a {dev:+.1f} degree deviation is {got:.5f}; the F1 form gives "
            f"|{dev:+.1f}| * {scale:.4f} = {abs(dev) * scale:.5f}. A value of "
            f"{abs(dev):.5f} means the axis was never scaled into satiation units; "
            f"a value of 0.0 means it was never added to the norm at all.")

    # Three axes, all live together: no term silently dropped when the others are
    # non-zero. Independent closed form, computed in numpy.
    sat2, inj2, dev2 = 60.0, 12.0, -4.0
    got = float(calculate_drive(jnp.asarray(sat2), jnp.asarray(inj2), params,
                                jnp.asarray(t_set + dev2)))
    want = float(np.sqrt((sat2 - float(params.setpoint)) ** 2 + inj2 ** 2
                         + (dev2 * scale) ** 2))
    assert got == pytest.approx(want, rel=1e-5), (
        f"three-axis drive is {got:.5f}, closed form {want:.5f}")


def test_reward_tracks_the_thermal_axis_alone():
    """Cool into the cold, then warm back: reward strictly negative, then positive.

    The plan's "walk out and come back", with the walk replaced by a change of
    field so the result does not depend on where the fire was placed. Phase A puts
    the agent in a -10 field: body temperature falls away from the setpoint every
    step, so the drive rises and the reward must be strictly NEGATIVE. Phase B
    continues from that cooled state in a field at the setpoint: the body warms
    back, the drive falls, and the reward must be strictly POSITIVE.

    The sign alone would still be satisfied by an implementation that made the
    drive depend on temperature in any monotone way, so the magnitudes are also
    checked against a numpy closed form built from the recorded temperatures.
    """
    params = _params(_thermal_only_config(-10.0))
    scale = float(params.max_satiation) / float(params.max_temperature)
    t_set = float(params.temperature_setpoint)

    def expected_rewards(body_temp_traj):
        """|T - T_set| * scale is the whole drive here; reward = prev - curr."""
        drive = np.abs(np.asarray(body_temp_traj) - t_set) * scale
        return drive[:-1] - drive[1:]

    # ── Phase A: cooling away from the setpoint ───────────────────────────────
    cold, state = _rest_rollout(params, 40, field_value=-10.0)
    _assert_other_axes_flat(cold, params)
    assert cold["body_temp"][0] == pytest.approx(t_set, abs=1e-6), \
        "the episode must start at the thermal setpoint for the sign argument to hold"
    assert np.all(np.diff(cold["body_temp"]) < 0), "the body must actually cool in a -10 field"
    assert np.all(cold["reward"] < 0), (
        f"reward must be strictly negative on every step of a walk into the cold; "
        f"max was {cold['reward'].max():.6f}. A reward of exactly 0.0 means the "
        f"thermal axis is not in the drive at all — with nutrition and injury off "
        f"and satiation on its setpoint there is nothing else left to move it.")
    np.testing.assert_allclose(
        cold["reward"], expected_rewards(cold["body_temp"]), atol=1e-4,
        err_msg="cooling rewards disagree with |T - T_set| * max_satiation/max_temperature")

    # ── Phase B: the return — same episode, field back at the setpoint ────────
    assert cold["body_temp"][-1] < t_set - 1.0, "phase A must leave the body clearly cold"
    warm, _ = _rest_rollout(params, 40, field_value=t_set, start_state=state)
    _assert_other_axes_flat(warm, params)
    assert np.all(np.diff(warm["body_temp"]) > 0), "the body must warm back toward the setpoint"
    assert np.all(warm["reward"] > 0), (
        f"reward must be strictly positive on every step of the return to warmth; "
        f"min was {warm['reward'].min():.6f}")
    np.testing.assert_allclose(
        warm["reward"], expected_rewards(warm["body_temp"]), atol=1e-4,
        err_msg="warming rewards disagree with the closed form")

    # The two phases must be commensurate: this is the drive scale, and if the
    # axis were normalised the design's way instead these numbers would be 100x
    # smaller than any reward this project has ever logged.
    assert np.abs(cold["reward"]).max() > 0.1, (
        f"the largest thermal reward step is {np.abs(cold['reward']).max():.6f}, "
        f"which is ~100x below the scale of this project's rewards — the axis was "
        f"probably normalised by max_temperature without the max_satiation rescale (F1)")


def test_info_drive_thermal_is_the_squared_normalised_deviation():
    """`info['drive_thermal']` follows its two siblings, not the norm's axis.

    `drive_hunger` and `drive_injury` are squared NORMALISED deviations and are
    *not* the quantities `calculate_drive` feeds to the norm. `drive_thermal` must
    match them — `((T - T_set)/max_temperature)^2` — or the three logged series are
    incommensurable and every plot that puts them on one axis is wrong.

    The failure this catches is the natural mistake: logging the norm's axis,
    `(T - T_set) * max_satiation/max_temperature`, which is unsquared and 100x
    larger.
    """
    params = _params(_thermal_only_config(-10.0))
    t_set = float(params.temperature_setpoint)
    t_max = float(params.max_temperature)

    rec, _ = _rest_rollout(params, 30, field_value=-10.0)
    post_temps = rec["body_temp"][1:]        # info is emitted with the POST-step body
    want = ((post_temps - t_set) / t_max) ** 2
    np.testing.assert_allclose(
        rec["drive_thermal"], want, atol=1e-6,
        err_msg="info['drive_thermal'] is not ((T - T_setpoint)/max_temperature)^2 — "
                "it must share the squared-normalised convention of drive_hunger and "
                "drive_injury, which are also diagnostics rather than the norm's axes")
    assert rec["drive_thermal"].max() > 0.0, "the diagnostic never moved"
    # Explicitly NOT the norm's axis, which is unsquared and ~100x bigger here.
    axis = np.abs(post_temps - t_set) * float(params.max_satiation) / t_max
    assert not np.allclose(rec["drive_thermal"], axis, atol=1e-3), (
        "info['drive_thermal'] is logging the drive's unsquared axis, not the "
        "squared-normalised diagnostic its two siblings use")


def test_drive_thermal_absent_and_body_temp_required_when_thermal_off():
    """Thermal off: no `drive_thermal` key, and `body_temp` cannot break anything.

    The key is gated because `max_temperature` is the inert placeholder 0.0 on a
    thermal-off config, so an ungated version would divide by zero and write a NaN
    into every existing run's logs. Consumers must therefore use `.get`.
    """
    with open(os.path.join(_ROOT, "configs", "environment", "default.yaml")) as f:
        params = load_env_params(Config(yaml.safe_load(f)))
    assert not params.thermal_enabled
    assert float(params.max_temperature) == 0.0, (
        "the thermal-off placeholder for max_temperature changed; if it is no longer "
        "zero, re-check whether info['drive_thermal'] still needs to be gated")

    state = jax_reset(params, jax.random.PRNGKey(SEED))
    _, _, _, info = jax_step(state, REST, params)
    assert "drive_thermal" not in info, (
        "info['drive_thermal'] is emitted on a thermal-off config, where "
        "max_temperature is 0.0 — that is a division by zero logged as NaN")
    assert "drive_hunger" in info and "drive_injury" in info


def test_calculate_drive_raises_without_body_temp_when_thermal_on():
    """A missing third axis is loud, not silently the setpoint.

    Defaulting `body_temp` to the setpoint would make a forgotten call site look
    like a perfectly comfortable agent and would be invisible in the reward.
    """
    params = _params(_thermal_only_config(-10.0))
    with pytest.raises(ValueError, match="body_temp"):
        calculate_drive(jnp.asarray(100.0), jnp.asarray(0.0), params)
