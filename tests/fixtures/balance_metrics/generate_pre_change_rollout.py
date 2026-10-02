"""Golden-fixture generator for the balance-metrics parity test (T1).

Plain-language purpose: this script freezes what one short rPPO rollout produced
BEFORE the balance-metrics logging was added, so that afterwards a test can prove
that switching the new logging OFF gives back exactly the same program — every
observation, action, reward, value, hidden state and random key, bit for bit.

The world is the level-05 campfire world (thermal on, felt injury on), loaded
through the trainer's own loaders (`load_env_config` resolves the `extends:`
chain, `load_env_params` builds EnvParams), with only the number of parallel
environments reduced to 4. The network is the tiny GRU used by
`tests/models/test_mc_fixed_mode.py`. The rollout is 8 steps, MC return mode, on CPU.

CRITICAL ORDERING RULE: run this on the PRE-CHANGE commit (the commit before the
balance-metrics change), in a worktree, never after the change. The script calls
`collect_trajectories` with the pre-change signature, so running it on a later
commit raises a TypeError instead of silently writing a tautological fixture.
The commit SHA it ran on is stored inside the npz (`_meta_commit`).

Plan: docs/develop/active/behavior/BALANCE_METRICS_TRAINING_LOGGING.md (Part B, T1).

Usage (from the repo root, pre-change commit):
    JAX_PLATFORMS=cpu python tests/fixtures/balance_metrics/generate_pre_change_rollout.py

Deliberately lives under `tests/` rather than `scripts/` so it does not trigger the
SCRIPTS_DEPENDENCY_MAP maintenance contract for a test-only helper.
"""
import os
import subprocess
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

import jax
jax.config.update("jax_platform_name", "cpu")

import numpy as np
from flax import nnx

FIXTURE_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURE_PATH = os.path.join(FIXTURE_DIR, "pre_change_rollout.npz")
LEVEL05 = os.path.join(_REPO, "configs", "environment", "experiment", "basic",
                       "05-campfire_thermal_10x10.yaml")
NUM_ENVS = 4
NUM_STEPS = 8
RESET_SEED = 0
ROLLOUT_SEED = 3


def build_world_and_model():
    """Level-05 params, a batch of NUM_ENVS reset states, and the tiny GRU model.

    Shared with the parity tests so the fixture and the comparison build the same
    inputs. Asserts thermal and interoceptive nociception are on, so a silently
    thermal-off world cannot produce (or pass against) the fixture.
    """
    from src.environment.config_loader import load_env_config, load_env_params
    from src.environment.core import jax_reset
    from src.environment.sensor import get_observation, get_observation_breakdown
    from src.models.recurrent_ppo_network import ActorCriticRNN

    params = load_env_params(load_env_config(LEVEL05))
    assert params.thermal_enabled, "level-05 world must have thermal on"
    assert params.interoceptive_nociception_enabled, "level-05 world must have felt injury on"
    state = jax.vmap(jax_reset, in_axes=(None, 0))(
        params, jax.random.split(jax.random.PRNGKey(RESET_SEED), NUM_ENVS))
    obs = jax.vmap(get_observation, in_axes=(0, None))(state, params)
    action_dim = 4 + int(params.rest_action_enabled) + int(params.eat_action_enabled)
    model = ActorCriticRNN(
        input_dim=int(obs.shape[-1]), action_dim=action_dim, hidden_size=8,
        rngs=nnx.Rngs(0), rnn_type="GRU", activation="relu", modulation_config=None,
        observation_breakdown=get_observation_breakdown(params),
        encoding_config={"encoding_mode": "flat", "use_layer_norm": False},
    )
    return params, state, model


def flatten_outputs(outputs):
    """Flatten a pytree into {path-string: np.ndarray}. `None` leaves vanish, so a
    `step_info.balance=None` field adds no entries and the pre-/post-change key sets
    match by name."""
    leaves, _ = jax.tree_util.tree_flatten_with_path(outputs)
    out = {}
    for path, leaf in leaves:
        name = jax.tree_util.keystr(path)
        arr = np.asarray(jax.random.key_data(leaf)) if jax.dtypes.issubdtype(
            getattr(leaf, "dtype", np.float32), jax.dtypes.prng_key) else np.asarray(leaf)
        out[name] = arr
    return out


def main():
    from src.models import recurrent_ppo_trainer as rpt

    params, state, model = build_world_and_model()
    h = model.initial_state(NUM_ENVS)
    # PRE-CHANGE signature: no `balance_metrics` keyword (see the ordering rule).
    outputs = rpt.collect_trajectories(
        model, params, state, h, jax.random.PRNGKey(ROLLOUT_SEED), NUM_STEPS,
        rnn_type="GRU", return_mode="MC")
    flat = flatten_outputs(outputs)
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=_REPO, text=True).strip()
    dirty = subprocess.check_output(["git", "status", "--porcelain", "--", "src", "train.py"],
                                    cwd=_REPO, text=True).strip()
    if dirty:
        raise SystemExit(f"src/ or train.py has uncommitted changes; refusing to write a golden:\n{dirty}")
    np.savez(FIXTURE_PATH, _meta_commit=np.array(sha), **flat)
    print(f"wrote {FIXTURE_PATH}: {len(flat)} arrays, commit {sha}")


if __name__ == "__main__":
    main()
