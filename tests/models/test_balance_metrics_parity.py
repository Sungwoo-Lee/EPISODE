"""Balance metrics must not change training (plan Part B, T1 and T2).

Plain-language context: the balance metrics add a few extra per-step reads to the rPPO
rollout (body state before the step, the temperature of the landing cell, the felt
injury). They are logging only. These two tests prove that claim bit for bit on the
level-05 campfire world, where thermal and felt injury are both on, so the extra reads
are really traced:

- T1: with the switch OFF, one rollout is identical to a golden captured on the commit
  BEFORE the change (tests/fixtures/balance_metrics/pre_change_rollout.npz): every
  observation, action, reward, value, step-info field, final env state, hidden state,
  random key and bootstrap value.
- T2: three jitted `train_iteration` calls with the switch ON and OFF from identical
  starting points give identical losses, parameters, optimizer state, env state, key
  and every shared rollout field. The ON run must actually carry the felt-injury,
  warm-cell and near-fire arrays.

T1 pins the pre-change program; a later, deliberate change to the env or network will
legitimately invalidate its golden (T2 remains the durable guard).

Plan: docs/develop/active/behavior/BALANCE_METRICS_TRAINING_LOGGING.md
"""
import os
import sys
from typing import NamedTuple

os.environ.setdefault("JAX_PLATFORMS", "cpu")

import jax
import numpy as np
import optax
import pytest
from flax import nnx

_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(_REPO, "tests", "fixtures", "balance_metrics"))
import generate_pre_change_rollout as gen  # noqa: E402

from src.models import recurrent_ppo_trainer as rpt  # noqa: E402


class _Cfg(NamedTuple):
    """Static config carrying the fields train_iteration reads (mirrors train.PPOConfig)."""
    num_steps: int
    num_epochs: int
    gamma: float
    gae_lambda: float
    clip_eps: float
    ent_coef: float
    vf_coef: float
    lr: float
    balance_metrics: bool
    rnn_type: str = "GRU"
    activation: str = "relu"
    return_mode: str = "MC"
    max_grad_norm: float = 0.5


def _bitwise_equal(a, b):
    a, b = np.asarray(a), np.asarray(b)
    if a.shape != b.shape or a.dtype != b.dtype:
        return False
    return np.array_equal(np.ascontiguousarray(a).view(np.uint8),
                          np.ascontiguousarray(b).view(np.uint8))


def _assert_same(flat_a, flat_b, what):
    assert set(flat_a) == set(flat_b), (
        f"{what}: key sets differ: only-a={sorted(set(flat_a) - set(flat_b))[:5]} "
        f"only-b={sorted(set(flat_b) - set(flat_a))[:5]}")
    bad = [k for k in flat_a if not _bitwise_equal(flat_a[k], flat_b[k])]
    assert not bad, f"{what}: {len(bad)} arrays differ bitwise, e.g. {bad[:5]}"


# ---------------------------------------------------------------------------
# T1
# ---------------------------------------------------------------------------
def test_off_matches_pre_change_golden():
    golden = np.load(os.path.join(os.path.dirname(gen.__file__), "pre_change_rollout.npz"))
    params, state, model = gen.build_world_and_model()   # asserts thermal + felt injury on
    assert params.thermal_enabled and params.interoceptive_nociception_enabled
    h = model.initial_state(gen.NUM_ENVS)
    outputs = rpt.collect_trajectories(
        model, params, state, h, jax.random.PRNGKey(gen.ROLLOUT_SEED), gen.NUM_STEPS,
        rnn_type="GRU", return_mode="MC", balance_metrics=False)
    assert outputs[0].step_info.balance is None
    flat = gen.flatten_outputs(outputs)
    ref = {k: golden[k] for k in golden.files if k != "_meta_commit"}
    _assert_same(ref, flat, "metrics-off rollout vs pre-change golden")


# ---------------------------------------------------------------------------
# T2
# ---------------------------------------------------------------------------
def run_train_iterations(balance_metrics, n_iters=3):
    """Fresh model/optimizer/env from fixed seeds; `n_iters` jitted train_iteration calls.
    Returns (flat shared outputs, list of per-iteration trajectories)."""
    params, env_state, model = gen.build_world_and_model()
    optimizer = nnx.Optimizer(
        model, optax.chain(optax.clip_by_global_norm(0.5), optax.adam(3e-4)), wrt=nnx.Param)
    cfg = _Cfg(num_steps=gen.NUM_STEPS, num_epochs=2, gamma=0.99, gae_lambda=0.95,
               clip_eps=0.2, ent_coef=0.01, vf_coef=0.5, lr=3e-4,
               balance_metrics=balance_metrics)
    jit_train = nnx.jit(rpt.train_iteration, static_argnums=(6,))
    h = model.initial_state(gen.NUM_ENVS)
    key = jax.random.PRNGKey(7)
    shared, trajs = {}, []
    for it in range(n_iters):
        env_state, h, key, losses, num_completed, traj = jit_train(
            model, optimizer, params, env_state, h, key, cfg)
        trajs.append(traj)
        per_it = {"losses": losses, "num_completed": num_completed,
                  "traj": traj._replace(step_info=traj.step_info._replace(balance=None))}
        for k, v in gen.flatten_outputs(per_it).items():
            shared[f"it{it}{k}"] = v
    final = {"env_state": env_state, "h": h, "key": key,
             "model": nnx.state(model), "optimizer": nnx.state(optimizer)}
    shared.update(gen.flatten_outputs(final))
    return shared, trajs


def test_train_iteration_on_vs_off_bitwise():
    off, trajs_off = run_train_iterations(False)
    on, trajs_on = run_train_iterations(True)
    for t in trajs_off:
        assert t.step_info.balance is None
    for t in trajs_on:
        b = t.step_info.balance
        for name in ("nutrition", "injury", "felt_injury", "body_temp", "on_warm_cell", "near_fire"):
            v = getattr(b, name)
            assert v is not None and hasattr(v, "shape") and v.shape == (gen.NUM_STEPS, gen.NUM_ENVS), name
    assert any(k.startswith("it0['losses']") or "losses" in k for k in off)
    _assert_same(off, on, "train_iteration metrics-off vs metrics-on")
