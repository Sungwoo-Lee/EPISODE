"""Regression test — Bug 4 (Track B, 2026-07-23 eval/logging fix plan, latent):
`_run_episode` (and `_run_episode_with_recording`) in scripts/eval/
eval_rollout.py passed the same frozen episode-level `rng_key` into
`policy_fn` on every step, so stochastic eval sampling (`eval_policy_mode:
"stochastic"`) drew every step's action with an identical key -- a
perfectly-correlated, near-deterministic "stochastic" eval.

Fix (docs/develop/active/issues/FIX_EVAL_LOGGING_TRACK_B_20260723.md, Bug 4):
split a fresh per-step key from a running `step_key` before each call to
`policy_fn`.

Uses a stub `policy_fn` that records every key it is handed and asserts the
recorded keys are pairwise distinct.
"""
import os
import sys

import jax
import numpy as np
import yaml

_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _REPO)
sys.path.insert(0, os.path.join(_REPO, "scripts", "eval"))

from src.utils.config import Config
from src.environment.config_loader import load_env_params

import eval_rollout as er  # noqa: E402

_ENV_YAML = """\
environment:
  height: 10
  width: 10
  start_pos: [5, 5]
  max_steps: 5
  rest_action_enabled: false
  eat_action_enabled: false
  random_start_pos: false
  placement:
    mode: per_entity
  resources: []
  neutral_animals: []
  predators: []
  obstacles: []
  location_areas:
    - type: "grass"
      area: [[1, 1], [10, 10]]
body:
  with_satiation: false
  with_nutrition: false
  with_injury: false
  random_start_satiation: false
  random_start_nutrition: false
  random_start_injury: false
  max_satiation: 100
  max_nutrition: 100
  max_injury: 100
  metabolic_cost: 1.0
  food_nutrition_gain: 6
  eating_nutrition_cost: 0.0
  eating_reward_penalty: 0.0
  nutrition_to_satiation_scaling_factor: 1.0
  satiation_setpoint: 100
  start_satiation: 100
  start_nutrition: 100
  recovery_base_rate: 0.0
  recovery_accel_rate: 0.0
  recovery_in_bush_multiplier: 1.0   # inert; mandatory key, no fallback default
  healing_nutrition_cost: 0.0          # inert; mandatory key, no fallback default
  healing_nutrition_dependence: false   # inert; mandatory key, no fallback default
  injury_smoothing_duration: 1
  use_homeostatic_reward: false
  death_penalty: 0.0
  overeating_death: false
# Thermal system OFF — `thermal.enabled` is a mandatory gate with no fallback
# default (docs/develop/active/thermal/IMPLEMENTATION_PLAN.md, F6).
water:
  enabled: false   # THIRST_WATER_PLAN: mandatory gate; no pond in this world
thermal:
  enabled: false

sensory:
  visual_value_mode: sum
  visual_occlusion_enabled: false
  using_sensory: true
  olfactory_enabled: false
  sensor_radius: 5
  vector_size: 5
  decay_power: 2.0
  olfactory_grid_range: 0
  visual_blur_enabled: false
  visual_blur_radial_scale: 0.5
  visual_blur_anisotropy: 3.0
  visual_blur_sigma_floor: 0.5
  collision_sensor_range: 1
  location_sensor: false
  nociception_enabled: false
  nociception_size: 1
  visual_sensor_enabled: false
  visual_sensor_range: 0
  proprioception_enabled: false
  injury_observable: false
  nutrition_observable: false
  interoceptive_nociception_enabled: false
  interoceptive_convolution_enabled: false
  interoceptive_kernel_tau: 3.0
  interoceptive_kernel_length: 1
visualization:
  local_view_size: 3
"""


def _make_config(yaml_str):
    return Config(yaml.safe_load(yaml_str))


def test_policy_fn_receives_distinct_keys_per_step():
    config = _make_config(_ENV_YAML)
    params = load_env_params(config)

    seen_keys = []

    def stub_policy_fn(obs, carry, key, deterministic=True):
        seen_keys.append(np.asarray(key))
        return 0, carry  # always move (action 0); carry unused by this stub

    er._run_episode(
        params=params,
        policy_fn=stub_policy_fn,
        rng_key=jax.random.PRNGKey(0),
        max_steps=params.max_steps,
        deterministic=False,
    )

    assert len(seen_keys) == params.max_steps
    unique_keys = {tuple(k.tolist()) for k in seen_keys}
    assert len(unique_keys) == len(seen_keys), (
        f"expected {len(seen_keys)} pairwise-distinct per-step keys, got "
        f"{len(unique_keys)} unique (pre-fix: every step reuses the same frozen key)"
    )


# ---------------------------------------------------------------------------
# Regression test — action-key / env-key aliasing (code-reviewer, 2026-10-18).
# The per-episode action-sampling chain used to start at the reset key
# PRNGKey(seed) itself, which jax_reset / jax_step also split for the
# environment's own randomness. Because split(k, 2)[i] == split(k, n)[i] in this
# JAX build, the action chain walked in lockstep with state.key: the step-1
# action key equalled the reset agent_key and the action key at t+1 equalled the
# env respawn_key at t. Fix: the chain starts at
# fold_in(PRNGKey(seed), er._ACTION_KEY_FOLD) in both the legacy loops and the
# batched path.
# ---------------------------------------------------------------------------

def _key_tuple(k):
    return tuple(np.asarray(k).tolist())


def _legacy_action_and_env_keys(params, seed):
    """Run `_run_episode` with a stub policy; return (action keys, env keys)."""
    action_keys, env_keys = [], set()
    reset_key = jax.random.PRNGKey(seed)
    for k in jax.random.split(reset_key, 5):          # jax_reset's 5-way split
        env_keys.add(_key_tuple(k))
    env_keys.add(_key_tuple(reset_key))

    def stub_policy_fn(state, carry, key, deterministic=True):
        action_keys.append(_key_tuple(key))
        env_keys.add(_key_tuple(state.key))
        for k in jax.random.split(state.key, 6):      # jax_step's 6-way split
            env_keys.add(_key_tuple(k))
        return 0, carry

    er._run_episode(params=params, policy_fn=stub_policy_fn, rng_key=reset_key,
                    max_steps=params.max_steps, deterministic=False)
    return action_keys, env_keys


def test_action_key_chain_disjoint_from_env_key_chain():
    params = load_env_params(_make_config(_ENV_YAML))
    for seed in (0, 1, 12345):
        action_keys, env_keys = _legacy_action_and_env_keys(params, seed)
        assert len(action_keys) == params.max_steps
        shared = set(action_keys) & env_keys
        assert not shared, (
            f"seed={seed}: {len(shared)} of {len(action_keys)} action-sampling keys equal "
            "an environment key (reset key, jax_reset sub-key, state.key or a jax_step "
            "sub-key) -- the action chain aliases the env chain"
        )


def test_batched_action_chain_matches_legacy(monkeypatch):
    """The batched path must start the action chain from the same folded key as the
    legacy loop (so sampled batched == sampled legacy), not from the reset key."""
    import flax.nnx as nnx

    params = load_env_params(_make_config(_ENV_YAML))
    seeds = [0, 1, 12345]
    captured = {}

    class _Captured(Exception):
        pass

    def fake_jit(fn, **_kw):
        def call(model, p, states0, h0, act_keys0, max_steps, deterministic=True):
            captured["act_keys0"] = np.asarray(act_keys0)
            captured["reset_keys"] = np.asarray(states0.key)
            raise _Captured
        return call

    class _StubModel:
        action_dim = 5

        def initial_state(self, batch_size):
            return np.zeros((batch_size, 1), np.float32)

    monkeypatch.setattr(nnx, "jit", fake_jit)
    try:
        er._run_episodes_batched(params, _StubModel(), seeds, params.max_steps,
                                 deterministic=False)
    except _Captured:
        pass
    assert "act_keys0" in captured, "fake nnx.jit was not reached"

    for i, s in enumerate(seeds):
        chain0 = captured["act_keys0"][i]
        assert not np.array_equal(chain0, np.asarray(jax.random.PRNGKey(s))), (
            f"seed={s}: batched action chain starts at the reset key PRNGKey(seed)")
        legacy_keys, _ = _legacy_action_and_env_keys(params, s)
        first_batched = _key_tuple(jax.random.split(jax.numpy.asarray(chain0))[1])
        assert first_batched == legacy_keys[0], (
            f"seed={s}: batched step-1 action key differs from the legacy loop's")
