"""Stage 2 of the temperature system — body temperature and termination reason 5.

What this file checks, in plain terms: the agent now carries a body temperature.
Every step it drifts toward the temperature of the cell the agent is standing on,
while the agent's own physiology pulls it back toward its comfortable setpoint. If
it ever leaves the survivable band the episode ends, and that ending is reported as
a death (code 5) rather than as running out of time.

Two things here are easy to get wrong and both are checked deliberately:

1. **Leaving out the physiological pull-back (`k_loss`).** An implementation
   without it still *looks* right — the body still tracks the world, still freezes
   in the cold — but it settles at exactly the cell's temperature instead of
   partway back toward the setpoint. The whole "cold but survivable" band the
   design rests on then disappears. Only the equilibrium assertion sees this.
2. **Labelling the death without actually dying.** `termination_reason` is built
   by a chain of `jnp.where`s, and the death penalty is gated on a separate flag
   captured earlier in the step. It is entirely possible to make code 5 appear
   while no penalty is ever paid, so every death test here asserts the reward too.

The numbers are checked against the design's own calibration sandbox
(`tests/env/thermal_sandbox_oracle.py::body_traj`) and against the algebraic
fixed point of the recurrence — neither of which is derived from `core.py`, so
these tests cannot pass merely by agreeing with the implementation.
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
sys.path.insert(0, _HERE)          # for the vendored oracle module

import jax
import jax.numpy as jnp

from src.utils.config import Config
from src.environment.config_loader import load_env_params
from src.environment.core import jax_reset, jax_step, calculate_drive
from thermal_sandbox_oracle import body_traj

THERMAL_CONFIG = os.path.join(
    _ROOT, "configs", "environment", "experiment", "archive", "thermal", "campfire_world.yaml")
DEFAULT_CONFIG = os.path.join(_ROOT, "configs", "environment", "default.yaml")

REST = 4          # the stay-in-place action; `campfire_world.yaml` enables it


# ── config helpers ────────────────────────────────────────────────────────────

def _uniform_field_config(cell_temp, max_steps=500):
    """A thermal config whose field is one constant value everywhere.

    Both heat-source mechanisms are switched off and `default_temp` is a
    degenerate range, so the raw field is the constant `cell_temp` and blurring a
    constant returns it unchanged (up to float32). That is what makes the closed
    forms below applicable: `T_field` in the recurrence is a known constant rather
    than something that has to be read back out of the environment.

    Everything that could end the episode for a NON-thermal reason is also
    removed — the predator/rabbit entities, the damaging obstacles and the
    hiding-predator resource, and `body.metabolic_cost` is zeroed so the agent
    cannot starve. Without this the agent dies of injury around step 8 and of
    starvation at step 100, and neither the equilibrium nor the steps-to-death
    assertion would ever be reached.
    """
    d = copy.deepcopy(yaml.safe_load(open(THERMAL_CONFIG)))
    # Archived raw input: not migrated for the water gate (project policy); supplied in memory, `false` = the pre-water world (THIRST_WATER_PLAN).
    d.setdefault("water", {"enabled": False})
    d["thermal"]["use_object_sources"] = False
    d["thermal"]["use_random_spots"] = False
    d["thermal"]["default_temp"] = [float(cell_temp), float(cell_temp)]
    d["environment"]["entities"] = []
    d["environment"]["obstacles"] = [
        o for o in d["environment"]["obstacles"] if o.get("name") == "campfire"]
    d["environment"]["resources"] = [
        r for r in d["environment"]["resources"] if r.get("type") == "food"]
    d["environment"]["max_steps"] = int(max_steps)
    d["body"]["metabolic_cost"] = 0.0
    return d


def _params(d):
    return load_env_params(Config(d))


def _rollout(params, n_steps, action=REST, seed=0):
    """Rest in place until the episode ends or `n_steps` elapse.

    Returns (body_temp trajectory including the reset value, final reward,
    final termination_reason, number of steps actually taken, final state,
    previous state).
    """
    state = jax_reset(params, jax.random.PRNGKey(seed))
    traj = [float(state.body_temp)]
    reward = reason = None
    prev = state
    for i in range(n_steps):
        prev = state
        state, reward, done, info = jax_step(state, action, params)
        traj.append(float(state.body_temp))
        reason = int(info["termination_reason"])
        if bool(done):
            return np.array(traj), float(reward), reason, i + 1, state, prev
    return np.array(traj), float(reward), reason, n_steps, state, prev


def _homeostatic_reward_without_death_penalty(prev_state, state, params):
    """What the step's reward would have been if no death penalty had fired.

    Rebuilt from the drives the reward is defined as (`prev_drive - curr_drive`),
    so the death-penalty assertions below compare against a quantity that does
    not itself depend on whether the penalty fired.

    Stage 4 note: body temperature is now the third axis of the drive on a
    thermal-ON config, and every config in this file is thermal-on. Both body
    temperatures MUST be passed (pre-step for `prev_drive`, post-step for
    `curr_drive`, exactly as `jax_step` pairs them) or this helper would return
    the two-axis drive change and the death-penalty assertions would compare the
    reward against the wrong baseline — on a thermal death, by far the largest
    term. `calculate_drive` raises rather than defaulting, so an omission here is
    loud instead of silently wrong.
    """
    prev_drive = calculate_drive(prev_state.satiation, prev_state.injury_level, params,
                                 prev_state.body_temp)
    curr_drive = calculate_drive(state.satiation, state.injury_level, params,
                                 state.body_temp)
    return float(prev_drive - curr_drive)


# ── the closed-form test ──────────────────────────────────────────────────────

def test_equilibrium_and_time_to_death():
    """Hold the agent in a constant field; check against the design's closed forms.

    Three independent claims, none of them re-derived from `core.py`:

    * **Equilibrium.** The recurrence T <- T + k_ex(T_f - T) - k_loss(T - T_set)
      has fixed point T* = (k_ex*T_f + k_loss*T_set) / (k_ex + k_loss), which at
      the design's T_set = 0 is k_ex*T_f/(k_ex + k_loss). A -10 cell therefore
      settles the body at -8, NOT at -10: physiology holds off 20% of the cold.
      Drop `k_loss` and the body would settle at -10 exactly, which is what the
      second assertion refuses.
    * **Time constant.** 1/(k_ex + k_loss) = 20 steps. The discrete gap shrinks by
      (1 - k_ex - k_loss) per step, so the first step at which the remaining gap
      is under 1/e of the initial gap is exactly that number.
    * **Steps to death.** Compared against `sim.body_traj` — the sandbox loop the
      design's own steps-to-death numbers were printed from — run with the same
      constants, for a lethally cold cell and a lethally hot one.
    """
    # -- equilibrium + time constant, in a survivable cold cell -----------------
    cell = -10.0
    params = _params(_uniform_field_config(cell, max_steps=500))
    k_ex = float(params.thermal_k_exchange)
    k_loss = float(params.thermal_k_loss)
    k_met = float(params.thermal_k_metabolic)
    t_set = float(params.temperature_setpoint)
    assert (k_ex, k_loss, k_met) == (0.04, 0.01, 0.0), \
        f"the design's constants moved: k_exchange={k_ex}, k_loss={k_loss}, k_metabolic={k_met}"

    traj, _, reason, n_steps, _, _ = _rollout(params, 400)
    assert n_steps == 400 and reason == 0, \
        f"a {cell:+.0f} cell must be survivable (T* is inside the band); ended at step {n_steps} with reason {reason}"

    t_star = (k_ex * cell + k_loss * t_set + k_met) / (k_ex + k_loss)
    assert t_star == pytest.approx(-8.0), "closed form drifted from the design's worked example"
    assert traj[-1] == pytest.approx(t_star, abs=1e-3), \
        f"body settled at {traj[-1]:.4f}, closed-form equilibrium is {t_star:.4f}"
    # The k_loss-omission catcher: without the pull-back term the body would
    # equilibrate at the CELL temperature. 2.0 degrees of clear water between the
    # two answers, so this cannot be satisfied by a near-miss.
    assert abs(traj[-1] - cell) > 1.5, (
        f"body settled at {traj[-1]:.4f}, indistinguishable from the cell temperature "
        f"{cell:+.1f} — the k_loss pull-back toward the setpoint is missing")

    # Whole trajectory against the vendored sandbox loop.
    oracle = body_traj([cell] * 400, T0=float(traj[0]), k_ex=k_ex, k_loss=k_loss,
                       k_met=k_met, T_neutral=t_set)
    np.testing.assert_allclose(
        traj, oracle, atol=2e-4,
        err_msg="body-temperature trajectory disagrees with the numpy sandbox oracle")

    # Time constant: 1/(k_ex + k_loss) steps to close 1 - 1/e of the initial gap.
    tau = 1.0 / (k_ex + k_loss)
    assert tau == pytest.approx(20.0)
    gap0 = abs(traj[0] - t_star)
    first_under = int(np.argmax(np.abs(traj - t_star) < gap0 / np.e))
    assert first_under == int(round(tau)), \
        f"gap fell below 1/e at step {first_under}; time constant 1/(k_ex+k_loss) is {tau:.1f}"

    # -- steps to death, both ends of the band --------------------------------
    for cell, expect_reason in ((-25.0, 5), (30.0, 5)):
        params = _params(_uniform_field_config(cell, max_steps=500))
        lo = float(params.min_temperature)
        hi = float(params.max_temperature)
        traj, _, reason, n_steps, _, _ = _rollout(params, 400)

        oracle = body_traj([cell] * 400, T0=0.0, k_ex=k_ex, k_loss=k_loss,
                           k_met=k_met, T_neutral=t_set)
        lethal = (oracle < lo) | (oracle > hi)
        assert lethal.any(), f"a {cell:+.0f} cell should be lethal under the oracle"
        expected_step = int(np.argmax(lethal))          # index n == after n steps

        assert n_steps == expected_step, (
            f"a {cell:+.0f} cell killed the agent at step {n_steps}; the sandbox oracle "
            f"with the same constants leaves [{lo}, {hi}] at step {expected_step}")
        assert reason == expect_reason, \
            f"a {cell:+.0f} cell must end the episode with termination_reason 5, got {reason}"
        np.testing.assert_allclose(
            traj, oracle[:len(traj)], atol=2e-4,
            err_msg=f"trajectory into death at {cell:+.0f} disagrees with the oracle")


# ── the death test ────────────────────────────────────────────────────────────

def test_thermal_death_reports_reason_5():
    """Overheat the agent and check it is treated as a DEATH, not just an ending.

    The second assertion is the load-bearing one. `termination_reason` and the
    death penalty are produced at different points in `jax_step`: the penalty is
    gated on `real_death`, captured from `update_body` BEFORE the truncation
    merge, while the reason is assigned afterwards. An implementation that adds
    the reason but not the death would satisfy the first assertion and fail this
    one.
    """
    params = _params(_uniform_field_config(30.0, max_steps=500))
    traj, reward, reason, n_steps, state, prev = _rollout(params, 400)

    assert reason == 5, f"overheating must report termination_reason 5, got {reason}"
    assert traj[-1] > float(params.max_temperature), \
        f"episode ended at body temperature {traj[-1]:.4f}, still inside the survivable band"

    penalty = float(params.death_penalty)
    assert penalty > 0, "config has no death penalty; this test cannot distinguish death from truncation"
    no_penalty = _homeostatic_reward_without_death_penalty(prev, state, params)
    assert reward == pytest.approx(no_penalty - penalty, abs=1e-3), (
        f"reward on the thermal-death step was {reward:.4f}; without the death penalty it would "
        f"have been {no_penalty:.4f}. The penalty ({penalty}) did not fire — termination_reason 5 "
        f"is being reported for an episode end that `real_death` never saw.")


def test_thermal_death_on_the_final_step_overrides_truncation():
    """A thermal death landing on the last step reports 5, not 1.

    `reason` is a chain of `jnp.where`s where later assignments win, so this is
    purely a question of where the thermal line sits. Placing it before the
    truncation line would relabel exactly this episode as "ran out of time" — and
    would do so only for episodes that die on their final step, which is rare
    enough to survive casual testing.
    """
    # -25 kills at step 28 (pinned by test_equilibrium_and_time_to_death against
    # the oracle); make that the last permitted step.
    params = _params(_uniform_field_config(-25.0, max_steps=500))
    _, _, _, death_step, _, _ = _rollout(params, 400)

    params = _params(_uniform_field_config(-25.0, max_steps=death_step))
    traj, reward, reason, n_steps, state, prev = _rollout(params, 400)

    assert n_steps == death_step, "the two configs must die on the same step"
    assert reason == 5, (
        f"a thermal death on the final step reported {reason}; 1 means the thermal assignment "
        f"sits BEFORE the truncation line in the reason chain instead of after it")
    penalty = float(params.death_penalty)
    no_penalty = _homeostatic_reward_without_death_penalty(prev, state, params)
    assert reward == pytest.approx(no_penalty - penalty, abs=1e-3), \
        "a thermal death that coincides with the step limit must still pay the death penalty"


# ── which cell the body reads ─────────────────────────────────────────────────

def test_body_reads_the_post_move_cell():
    """The recurrence uses the cell the agent moved INTO, not the one it left.

    Every other quantity `update_body` consumes (damage, ate_food, rested) is
    post-move, and a constant-temperature field cannot tell the two apart — which
    is exactly why this is checked with a field where every cell differs. Reading
    the pre-move cell would make body temperature lag the agent by one step:
    stepping onto the fire would not burn until the following step, and stepping
    off it would keep burning for one more.
    """
    params = _params(_uniform_field_config(-10.0, max_steps=500))
    H, W = params.height, params.width
    # Every cell distinct, all of them mild enough that one step cannot kill.
    field = (jnp.arange(H * W, dtype=jnp.float32).reshape(H, W) - (H * W) / 2.0)

    base = jax_reset(params, jax.random.PRNGKey(0))
    base = base._replace(thermal_field=field,
                         body_temp=jnp.asarray(0.0, dtype=jnp.float32))

    k_ex = float(params.thermal_k_exchange)
    k_loss = float(params.thermal_k_loss)
    k_met = float(params.thermal_k_metabolic)
    t_set = float(params.temperature_setpoint)

    moved = 0
    for action in range(4):
        state, _, _, _ = jax_step(base, action, params)
        old = tuple(int(v) for v in np.asarray(base.agent_pos))
        new = tuple(int(v) for v in np.asarray(state.agent_pos))
        if new == old:
            continue                       # blocked or walked into a wall
        moved += 1
        f_new = float(np.asarray(field)[new])
        f_old = float(np.asarray(field)[old])
        assert f_new != f_old, "the two cells must differ or this test proves nothing"
        expected = 0.0 + k_ex * (f_new - 0.0) + k_met - k_loss * (0.0 - t_set)
        assert float(state.body_temp) == pytest.approx(expected, abs=1e-4), (
            f"action {action} moved {old} -> {new}; body temperature followed the field value "
            f"at the wrong cell (got {float(state.body_temp):.4f}, post-move cell gives "
            f"{expected:.4f}, pre-move cell would give "
            f"{k_ex * f_old + k_met - k_loss * (0.0 - t_set):.4f})")
    assert moved >= 1, "the agent never moved; the test never exercised the cell choice"


# ── the off switch ───────────────────────────────────────────────────────────

def test_body_temp_is_inert_when_thermal_is_off():
    """A thermal-off config never moves `body_temp` and never emits reason 5.

    The recurrence sits behind a static `if params.thermal_enabled:`, so this is
    a statement about the traced graph rather than about a value comparison — but
    a value comparison is what would catch someone converting that Python `if`
    into a `jnp.where`, which would silently start reading a [0, 0] field.
    """
    params = _params(yaml.safe_load(open(DEFAULT_CONFIG)))
    assert not params.thermal_enabled
    state = jax_reset(params, jax.random.PRNGKey(0))
    assert float(state.body_temp) == 0.0
    assert state.thermal_field.shape == (0, 0)

    for _ in range(50):
        state, _, done, info = jax_step(state, REST, params)
        assert float(state.body_temp) == 0.0, "body temperature moved on a thermal-off config"
        assert int(info["termination_reason"]) != 5, "reason 5 on a thermal-off config"
        if bool(done):
            break
