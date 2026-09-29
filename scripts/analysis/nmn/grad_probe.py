"""The gradient probe: how much of each training update reaches the modulator, at one saved state.

Plain-language purpose: the wake-up analysis (B2) asks when, during training, the modulator
starts to matter. One sign is how much of the training signal (the gradient) flows into the
modulator's weights rather than the rest of the network, and through which part of the loss
(the policy term, the value term, the entropy term). Training logs only the total, so this
module re-runs ONE training iteration at a saved checkpoint (or at the untrained network) on a
throw-away copy, with the trainer's own code, and reads the gradients off it.

What it reports, per probe:
- (a) **first update, per loss term**: the gradient of `policy_loss`, `vf_coef * value_loss`
  and `ent_coef * entropy_loss` separately, at the parameters BEFORE any update of the
  iteration (probability ratio = 1, clipping inactive). For each term: ||grad_mod||^2,
  ||grad_all||^2 and their ratio, the term's share of the modulator. The three terms' gradients
  are checked to sum to the trainer's own total-loss gradient norm of that update.
- (b) **full iteration, like-for-like with the log**: the mean over the run's `K_epochs`
  updates of the trainer's own `update_step` outputs `grad_norm` and `mod_grad_norm`, which
  is exactly what train.py logs as `loss/grad_norm` (per iteration, before its rolling
  window) and `modulator/grad_norm`.
(a) is biased upward relative to the log: later updates of an iteration run at a ratio != 1,
where clipped samples give no policy gradient, and at parameters that have already moved.
The comparison with the log is a SANITY BAND, not a proof: the world is re-warmed, not
restored (checkpoints carry no environment state), and one logged value is one iteration.

How it reuses the trainer (tooling plan File Changes §11, "reuse the code, do not re-derive"):
the probe calls `recurrent_ppo_trainer.train_iteration` itself, jitted as train.py jits it,
so rollout collection, advantages and the `PPOBatch` are the trainer's own. The per-term split
is taken inside the trainer's own call of `update_step`: for the duration of the probe the
module-level `update_step` is wrapped by one that, on the first update of the iteration only,
also differentiates each loss term, then calls the original `update_step` unchanged. The model
and optimiser are deep copies (`nnx.clone`); the checkpoint on disk is only read.

Plan: docs/develop/active/neuromodulation/ALGORITHMIC_NULL_ANALYSIS_TOOLING.md, File Changes §11
(`grad_probe.py`), §D, Checkpoint 4.2.
"""
from __future__ import annotations

import contextlib
import os
from typing import NamedTuple

import numpy as np

TERMS = ("policy", "value", "entropy")
STATEMENT = ("(a) is the first update only (ratio = 1, before any in-iteration parameter "
             "change) and is biased upward relative to the log; (b) is the log's own definition; "
             "the world was re-warmed, not restored.")


class PPOConfig(NamedTuple):
    """Field-for-field copy of train.py's PPOConfig (train.py cannot be imported without
    running its argv pre-parser). The trainer reads it by attribute only;
    tests/analysis/test_nmn_grad_probe.py checks the field list equals train.py's."""
    num_steps: int
    num_epochs: int
    gamma: float
    gae_lambda: float
    clip_eps: float
    ent_coef: float
    vf_coef: float
    lr: float
    balance_metrics: bool
    rnn_type: str = "LSTM"
    activation: str = "tanh"
    return_mode: str = "MC"
    max_grad_norm: float = 0.5


def ppo_config(cfg) -> PPOConfig:
    """PPOConfig as train.py builds it for RecurrentPPO, from the run's saved config (a
    `src.environment.config_loader.Config`); every key mandatory. One field differs on purpose:
    `balance_metrics` is always False. That switch only adds read-only per-step logging fields
    (`step_info.balance`: "pure reads ... no random key, not used by the loss",
    recurrent_ppo_trainer.collect_trajectories), so it cannot change a gradient, and runs saved
    before the key existed (level-05) carry no value for it."""
    from src.models.recurrent_ppo_trainer import validate_return_mode
    g = cfg.get_mandatory
    return PPOConfig(
        num_steps=int(g("agent.sequence_length")), num_epochs=int(g("agent.K_epochs")),
        gamma=g("agent.gamma"), gae_lambda=g("agent.gae_lambda"), clip_eps=g("agent.eps_clip"),
        ent_coef=g("agent.entropy_coef"), vf_coef=g("agent.vf_coef"), lr=g("agent.lr_actor"),
        balance_metrics=False, rnn_type=g("agent.rnn_type"),
        activation=g("agent.activation"),
        return_mode=validate_return_mode(g("agent.return_mode")),
        max_grad_norm=g("agent.max_grad_norm"))


def make_optimizer(model, config: PPOConfig):
    """The optimiser exactly as train.py builds it (clip by global norm, then Adam)."""
    import optax
    from flax import nnx
    return nnx.Optimizer(model, optax.chain(optax.clip_by_global_norm(config.max_grad_norm),
                                            optax.adam(config.lr)), wrt=nnx.Param)


def restore_optimizer(models_dir, step: int, model, optimizer, num_envs: int) -> dict:
    """Restore `model` and `optimizer` in place from checkpoint `step`, strictly: the target is
    the exact payload train.py saves (src/utils/checkpoint_restore.py's target, for a chosen
    step rather than the latest), and orbax raises on any structure/shape/dtype mismatch."""
    import jax
    import orbax.checkpoint as ocp
    from flax import nnx
    target = {"model": nnx.state(model, nnx.Param), "optimizer": nnx.state(optimizer),
              "h_state": model.initial_state(num_envs), "key": jax.random.PRNGKey(0),
              "iteration": 0, "step": 0, "episode": 0, "stage": 0}
    restored = ocp.CheckpointManager(os.path.abspath(str(models_dir))).restore(
        int(step), args=ocp.args.StandardRestore(item=target))
    nnx.update(model, restored["model"])
    nnx.update(optimizer, restored["optimizer"])
    return {k: np.asarray(restored[k]).tolist() for k in ("iteration", "step", "episode", "stage")}


def _per_term_sq_norms(model, batch, config):
    """||grad||^2 over all parameters and over the modulator, per loss term, plus the norm of
    their sum (the total-loss gradient), at `model`'s current parameters. Mirrors
    `update_step.batch_loss_wrapped`: the loss is vmapped over environments and each aux term
    is averaged over them."""
    import jax
    import jax.numpy as jnp
    import optax
    from flax import nnx
    from src.models import recurrent_ppo_trainer as rpt

    b_axes = rpt.PPOBatch(obs=1, actions=1, log_probs=1, values=1, advantages=1, targets=1,
                          dones=1, h_init=0)
    coefs = {"policy": None, "value": config.vf_coef, "entropy": config.ent_coef}

    def term_loss(j, coef):
        def f(m):
            _, aux = jax.vmap(lambda mm, bb: rpt.ppo_loss_fn(mm, bb, config.clip_eps,
                                                              config.ent_coef, config.vf_coef),
                              in_axes=(None, b_axes))(m, batch)
            v = jnp.mean(aux[j])
            return v if coef is None else coef * v
        return f

    out, grads = {}, []
    for j, t in enumerate(TERMS):
        g = nnx.grad(term_loss(j, coefs[t]))(model)
        grads.append(g)
        out[f"{t}_all_sq"] = optax.global_norm(g) ** 2
        out[f"{t}_mod_sq"] = optax.global_norm(g["modulator"]) ** 2
    total = jax.tree_util.tree_map(lambda a, b, c: a + b + c, *grads)
    out["sum_all_norm"] = optax.global_norm(total)
    out["sum_mod_norm"] = optax.global_norm(total["modulator"])
    return out


@contextlib.contextmanager
def _split_first_update(num_epochs: int):
    """Wrap the trainer's module-level `update_step` for the duration of the probe: on the first
    update of each traced iteration (call index 0 modulo `num_epochs`, which is how
    train_iteration's Python epoch loop calls it) the wrapper appends the per-term norms to the
    returned aux; every call then runs the ORIGINAL update_step unchanged."""
    from src.models import recurrent_ppo_trainer as rpt
    original = rpt.update_step
    calls = {"n": 0}

    def wrapped(model, optimizer, batch, config):
        first = calls["n"] % num_epochs == 0
        calls["n"] += 1
        extra = _per_term_sq_norms(model, batch, config) if first else None
        loss, aux = original(model, optimizer, batch, config)
        return loss, (*aux, extra)

    rpt.update_step = wrapped
    try:
        yield
    finally:
        rpt.update_step = original


_JIT = {}


def _jitted():
    """train_iteration jitted as train.py jits it (config static). One per process, so the
    wrapped update_step is the only one it is ever traced with."""
    if "train_iteration" not in _JIT:
        from flax import nnx
        from src.models.recurrent_ppo_trainer import train_iteration
        _JIT["train_iteration"] = nnx.jit(train_iteration, static_argnums=(6,))
        from src.models.recurrent_ppo_trainer import collect_trajectories
        _JIT["collect"] = nnx.jit(collect_trajectories, static_argnums=(5, 6, 7),
                                  static_argnames=("balance_metrics",))
    return _JIT["train_iteration"], _JIT["collect"]


def probe(model, optimizer, env_params, config: PPOConfig, *, num_envs: int, seed: int,
          warmup_iters: int) -> dict:
    """One probe at the given (model, optimizer). Both are cloned; the originals are untouched.

    The world: `num_envs` environments reset from PRNGKey(seed), then `warmup_iters` rollouts of
    `config.num_steps` steps with the model but no update (checkpoints carry no env state).
    Then one training iteration (the trainer's own `train_iteration`) on the clones."""
    import jax
    from flax import nnx
    from src.environment.wrapper import ParallelEnv

    if warmup_iters < 0:
        raise ValueError("warmup_iters must be >= 0")
    train_it, collect = _jitted()
    m, opt = nnx.clone(model), nnx.clone(optimizer)
    key = jax.random.PRNGKey(int(seed))
    key, reset_key = jax.random.split(key)
    env_state, _ = ParallelEnv(env_params).reset(reset_key, int(num_envs))
    h = m.initial_state(int(num_envs))
    for _ in range(int(warmup_iters)):
        _, _, env_state, h, key, _ = collect(m, env_params, env_state, h, key, config.num_steps,
                                             config.rnn_type, config.return_mode,
                                             balance_metrics=config.balance_metrics)
    with _split_first_update(config.num_epochs):
        _, _, _, epoch_losses, _, _ = train_it(m, opt, env_params, env_state, h, key, config)
    epoch_losses = jax.tree_util.tree_map(np.asarray, epoch_losses)
    if len(epoch_losses) != config.num_epochs:
        raise AssertionError(f"{len(epoch_losses)} updates, expected K_epochs = {config.num_epochs}")
    per_update = [{"grad_norm": float(aux[3]), "mod_grad_norm": float(aux[4])}
                  for _, aux in epoch_losses]
    first = {k: float(v) for k, v in epoch_losses[0][1][5].items()}
    if any(aux[5] is not None for _, aux in epoch_losses[1:]):
        raise AssertionError("per-term split taken on an update other than the first")
    # the per-term gradients must add up to the trainer's own first-update gradient
    gn0 = per_update[0]["grad_norm"]
    rel = abs(first["sum_all_norm"] - gn0) / max(gn0, np.finfo(np.float32).tiny)
    out = {"first_update": {}, "first_update_sum_vs_trainer_rel_dev": rel,
           "first_update_trainer_grad_norm": gn0,
           "first_update_trainer_mod_grad_norm": per_update[0]["mod_grad_norm"]}
    for t in TERMS:
        a, md = first[f"{t}_all_sq"], first[f"{t}_mod_sq"]
        out["first_update"][t] = {"all_sq": a, "mod_sq": md,
                                  "share": md / a if a > 0 else float("nan")}
    tot_a = first["sum_all_norm"] ** 2
    out["first_update"]["total"] = {"all_sq": tot_a, "mod_sq": first["sum_mod_norm"] ** 2,
                                    "share": first["sum_mod_norm"] ** 2 / tot_a
                                    if tot_a > 0 else float("nan")}
    gn = float(np.mean([u["grad_norm"] for u in per_update]))
    mgn = float(np.mean([u["mod_grad_norm"] for u in per_update]))
    out["full_iteration"] = {"grad_norm_mean": gn, "mod_grad_norm_mean": mgn,
                             "share": mgn ** 2 / gn ** 2 if gn > 0 else float("nan"),
                             "per_update": per_update}
    out["statement"] = STATEMENT
    out["settings"] = {"num_envs": int(num_envs), "seed": int(seed),
                       "warmup_iters": int(warmup_iters), "num_steps": config.num_steps,
                       "num_epochs": config.num_epochs, "return_mode": config.return_mode}
    return out
