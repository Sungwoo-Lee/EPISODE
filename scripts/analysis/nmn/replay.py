"""Rebuild a finished run's agent, roll it out on a fixed episode set, keep `mod_info`.

Plain-language purpose: methods 2 and 3 both need the same thing — take one saved
snapshot of a trained agent, put it back in the world, and watch what the
neuromodulator emits at every step. The network already computes and returns that
signal on every forward pass (`recurrent_ppo_network.py`, the fourth return value);
the project's evaluation script simply throws it away. This module is the version
that keeps it.

Three properties are load-bearing and are asserted rather than assumed:

* **Episodes are paired.** Every episode is started from `jax.random.PRNGKey(seed)`
  for a fixed list of seeds, actions are greedy (argmax), and these runs have
  perceptual noise switched off — so the same seed produces the *same world and the
  same trajectory* for any two agents that would act identically. That is what turns
  a comparison between conditions into a distribution of per-episode paired
  differences rather than a difference of two means.
* **The restore is complete.** A partial restore that silently leaves layers at
  their fresh random values is a defect this project has already had once (Known
  Bugs, "Eval silently keeps random weights", Finding L3). Every parameter is
  checked for presence and shape and a mismatch is fatal.
* **The forward pass goes through `nnx.jit`.** Calling a restored NNX model eagerly
  reads a stale view of its own parameters — documented at length in
  `scripts/eval/eval_rollout.py::_rollout_scan_jit`. The scan here is wrapped the
  same way, for the same reason.

Survival steps, never cumulative reward: episode length is `argmax(done) + 1`,
identical to the definition `eval_rollout._run_episodes_batched` uses.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Any

import numpy as np

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


#: The five FiLM sites, mapped to the two `ModulatorOutput` fields that carry the
#: gain and the offset for each. `None` fields mean the site is off in this run.
SITE_FIELDS = {
    "encoder_unimodal":   ("z_unimodal", "z_unimodal_add"),
    "encoder_multimodal": ("z_multimodal", "z_multimodal_add"),
    "rnn":                ("z_rnn", "z_rnn_add"),
    "actor":              ("z_actor", "z_actor_add"),
    "critic":             ("z_critic", "z_critic_add"),
}


@dataclass
class LoadedAgent:
    model: Any            # ActorCriticRNN, weights restored
    env_params: Any       # EnvParams
    agent_cfg: dict       # the run's own saved `agent` block
    step: int             # which checkpoint was restored
    obs_breakdown: dict
    action_dim: int
    env_config_path: str  # the file the world was built from (a stage file for continual runs)


def load_agent(models_dir, step: int | None = None) -> LoadedAgent:
    """Rebuild the agent described by a run's own saved config and restore `step`.

    `step=None` restores the last checkpoint. For a continual run (`models/schedule.yaml`
    present) the WORLD (`env_params`) is built from the checkpoint's own stage file, chosen
    by the `stage` saved in the checkpoint (`eval_rollout._resolve_continual_stage_config`);
    the agent block always comes from `config.yaml`, the only file that carries it.
    """
    import jax
    import orbax.checkpoint as ocp
    from flax import nnx

    from src.environment.config_loader import Config, load_env_params
    from src.environment.sensor import get_observation_breakdown
    from src.models.recurrent_ppo_network import ActorCriticRNN
    from src.models.modulation_compat import translate_legacy_modulation_config

    from scripts.analysis.nmn import ckpt_io

    models_dir = os.path.abspath(str(models_dir))
    import copy
    from src.environment.saved_config_compat import apply_saved_config_compat

    cfg_path = os.path.join(models_dir, "config.yaml")
    cfg = Config.load_yaml(cfg_path)

    steps = ckpt_io.list_steps(models_dir)
    step = steps[-1] if step is None else int(step)
    if step not in steps:
        raise ValueError(f"checkpoint step {step} not among the {len(steps)} saved "
                         f"under {models_dir}")

    # Continual runs: the world of the checkpoint's own stage (tooling plan
    # ALGORITHMIC_NULL_ANALYSIS_TOOLING, File Changes §3). None for a non-continual run.
    env_cfg_path = cfg_path
    if os.path.exists(os.path.join(models_dir, "schedule.yaml")):
        from scripts.eval.eval_rollout import _resolve_continual_stage_config
        env_cfg_path = _resolve_continual_stage_config(
            cfg_path, os.path.join(models_dir, str(step)), quiet=True)
        if env_cfg_path is None:
            raise ValueError(f"{models_dir}: schedule.yaml present but no stage config "
                             f"resolved for step {step}")
    print(f"[replay] world built from {env_cfg_path}")
    env_cfg = cfg if env_cfg_path == cfg_path else Config.load_yaml(env_cfg_path)
    # Saved-config compat (STATE_DEPENDENT_BODY_MECHANICS C0): era keys go into a deep
    # copy used only to build env params; `cfg` (read for the agent block) is untouched.
    _cfg_load = copy.deepcopy(env_cfg.to_dict())
    print(f"[replay] saved-config compat supplied: "
          f"{apply_saved_config_compat(_cfg_load, source=env_cfg_path)}")
    env_params = load_env_params(Config(_cfg_load))
    obs_breakdown = get_observation_breakdown(env_params)
    input_dim = sum(obs_breakdown.values())
    action_dim = (4 + int(env_params.rest_action_enabled)
                  + int(env_params.eat_action_enabled))

    agent_cfg = cfg.to_dict()["agent"]
    modulation_cfg = agent_cfg.get("modulation")
    if modulation_cfg is not None and modulation_cfg.get("type") is None:
        modulation_cfg = None
    modulation_cfg = translate_legacy_modulation_config(modulation_cfg, source=cfg_path)

    model = ActorCriticRNN(
        input_dim=input_dim, action_dim=action_dim,
        hidden_size=agent_cfg["hidden_size"],
        rngs=nnx.Rngs(jax.random.PRNGKey(0)),
        rnn_type=agent_cfg["rnn_type"], activation=agent_cfg["activation"],
        modulation_config=modulation_cfg,
        observation_breakdown=obs_breakdown, encoding_config=agent_cfg,
    )

    current = nnx.state(model)
    dev = jax.local_devices()[0]
    restore_args = jax.tree_util.tree_map(
        lambda _x: ocp.ArrayRestoreArgs(
            restore_type=jax.Array,
            sharding=jax.sharding.SingleDeviceSharding(dev)),
        current)
    restored = ocp.CheckpointManager(models_dir).restore(
        step, args=ocp.args.PyTreeRestore(item={"model": current},
                                          restore_args={"model": restore_args},
                                          partial_restore=True))["model"]

    flat_restored, _ = jax.tree_util.tree_flatten_with_path(restored)
    flat_current, treedef = jax.tree_util.tree_flatten_with_path(current)
    by_path = {str(k): v for k, v in flat_restored}
    bad = []
    for k, cur in flat_current:
        ks = str(k)
        if ks not in by_path:
            bad.append(f"missing from checkpoint: {ks}")
        elif getattr(cur, "shape", None) != getattr(by_path[ks], "shape", None):
            bad.append(f"shape mismatch {ks}: ckpt {getattr(by_path[ks], 'shape', '?')} "
                       f"vs model {getattr(cur, 'shape', '?')}")
    if bad:
        raise ValueError(
            "Checkpoint restore is INCOMPLETE — refusing to evaluate a partly-random "
            "network:\n" + "\n".join("  " + b for b in bad))
    nnx.update(model, jax.tree_util.tree_unflatten(
        treedef, [by_path[str(k)] for k, _ in flat_current]))

    return LoadedAgent(model=model, env_params=env_params, agent_cfg=agent_cfg,
                       step=step, obs_breakdown=obs_breakdown, action_dim=action_dim,
                       env_config_path=str(env_cfg_path))


def _scan_body(model, env_params, states0, h0, max_steps: int):
    """Greedy batched rollout that KEEPS the modulator's output.

    MUST be entered through `nnx.jit` (see the module docstring). Mirrors
    `eval_rollout._rollout_scan_jit` for the environment half and adds `mod_info`
    plus the modulator's hidden state to the per-step outputs.
    """
    import jax
    import jax.numpy as jnp

    from src.environment.core import jax_step
    from src.environment.sensor import get_observation

    v_step = jax.vmap(jax_step, in_axes=(0, 0, None))
    v_obs = jax.vmap(get_observation, in_axes=(0, None))

    def step_fn(carry, _):
        state, h = carry
        logits, value, h_new, mod_info = model(v_obs(state, env_params), h)
        action = jnp.argmax(logits, axis=-1)
        next_state, reward, done, info = v_step(state, action, env_params)
        # `mod_h` is the modulator's own GRU state; recorded to check the bound in
        # spectral_bound.py assumption A1 (|h| < 1) against what actually happens.
        mod_h = h_new[1] if model.modulation_enabled else None
        out = {"action": action, "done": done, "value": value.squeeze(-1),
               "mod_info": mod_info, "mod_h": mod_h,
               "satiation": state.satiation, "injury": state.injury_level,
               "termination_reason": info["termination_reason"]}
        return (next_state, h_new), out

    return jax.lax.scan(step_fn, (states0, h0), None, length=max_steps)[1]


def rollout(agent: LoadedAgent, seeds, max_steps: int | None = None) -> dict:
    """Run one greedy episode per seed and return per-step arrays plus lengths.

    Returns a dict with:
        ``lengths``  (n_ep,) int   -- survival steps, `argmax(done) + 1`
        ``valid``    (T, n_ep) bool -- True for steps the agent was still alive at
        ``gamma``/``beta``  {site: (T, n_ep, H)} for every ENABLED site
        ``mod_h``    (T, n_ep, m) or None
        plus ``action``, ``value``, ``satiation``, ``injury``, ``termination_reason``.
    """
    import jax
    import jax.numpy as jnp
    from flax import nnx

    from src.environment.core import jax_reset

    max_steps = int(agent.env_params.max_steps if max_steps is None else max_steps)
    seeds = [int(s) for s in seeds]
    keys = jnp.stack([jax.random.PRNGKey(s) for s in seeds])
    states0 = jax.vmap(jax_reset, in_axes=(None, 0))(agent.env_params, keys)

    # Parity guard, copied in spirit from eval_rollout: the batched reset must
    # produce exactly the state a single unbatched reset would, or the episode set
    # is not the one the seeds name and nothing downstream is paired.
    for i, s in enumerate(seeds):
        ref = jax_reset(agent.env_params, jax.random.PRNGKey(s)).key
        if not bool(jnp.array_equal(states0.key[i], ref)):
            raise RuntimeError(
                f"batched reset PRNG parity check failed at seed index {i} (seed={s})")

    h0 = agent.model.initial_state(batch_size=len(seeds))
    out = nnx.jit(_scan_body, static_argnames=("max_steps",))(
        agent.model, agent.env_params, states0, h0, max_steps)
    out = jax.tree_util.tree_map(np.asarray, out)

    done = out["done"]                                   # (T, n_ep)
    lengths = np.argmax(done, axis=0) + 1
    if not bool(np.all(done.any(axis=0))):
        raise RuntimeError(
            f"{int((~done.any(axis=0)).sum())} episodes never terminated within "
            f"max_steps={max_steps}; the environment truncates at "
            f"params.max_steps, so this means the rollout window is too short.")
    valid = np.arange(max_steps)[:, None] < lengths[None, :]

    # The unmodulated control returns `None` for the whole ModulatorOutput -- a
    # valid EMPTY pytree, which is how the model signals "there is no modulator"
    # rather than an error. It has nothing to describe, but it still has survival
    # steps, which is why it is replayed at all.
    mod = out.pop("mod_info")
    gamma, beta = {}, {}
    for site, (g_field, b_field) in (SITE_FIELDS.items() if mod is not None else ()):
        g = getattr(mod, g_field)
        if g is None:
            continue
        gamma[site] = np.asarray(g)
        beta[site] = np.asarray(getattr(mod, b_field))

    out.update(lengths=lengths, valid=valid, gamma=gamma, beta=beta,
               seeds=np.asarray(seeds), max_steps=max_steps)
    return out


def episode_seeds(n: int, base: int = 90_000) -> list[int]:
    """The fixed episode set every arm and every condition is evaluated on.

    A plain contiguous block, so the set is reproducible from two numbers and any
    later analysis can widen it without disturbing the episodes already used.
    """
    return list(range(base, base + int(n)))
