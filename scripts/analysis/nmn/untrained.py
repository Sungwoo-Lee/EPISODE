"""Rebuild a run's UNTRAINED network: the exact weights train.py started that run from.

Plain-language purpose: two analyses need the network as it was before any training. The
wake-up measures (B2) start their curves at step 0, and the similarity analysis (A1/A3) uses
untrained networks as a floor ("how similar are two networks that learned nothing?") and to
check that the ordinary and modulated agents of one seed begin from identical main-network
weights. No step-0 checkpoint is saved, so the network is rebuilt along train.py's own key
chain, which is NOT the obvious one:

    key = PRNGKey(seed)                                  # train.py:1152
    key, model_key, env_key = split(key, 3)              # train.py:1153 — model_key is never used
    env.reset(env_key, num_envs)                         # train.py:1156
    key, init_key = split(key)                           # train.py:1207
    ActorCriticRNN(..., rngs=nnx.Rngs(init_key), ...)    # train.py:1241-1245

`seed` is the run's saved top-level `seed:` (KNOWN_BUGS line 114: the nested training.seed is
stale), cross-checked against the `--seed` launch argument in the run's local WandB metadata.
The architecture is built from the saved config exactly as `replay.load_agent` builds it; for a
continual run that is `config.yaml`, the first stage, which is the world train.py initialises in.

Because this re-derives the trainer's steps, it is verified against the trainer itself by
tests/analysis/test_nmn_untrained.py::test_matches_train_py_construction (bitwise).

Plan: docs/develop/active/neuromodulation/ALGORITHMIC_NULL_ANALYSIS_TOOLING.md, File Changes §11
and §B2 "Untrained-network anchor".
"""
from __future__ import annotations

import copy
import glob
import json
import os
from pathlib import Path

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def launch_args(run_dir) -> list:
    """The run's launch arguments from its local WandB metadata, found by the saved top-level
    `tag:` (never by a timestamp glob alone). Exactly one folder must match."""
    import yaml
    run_dir = Path(run_dir)
    cfg = yaml.safe_load((run_dir / "models" / "config.yaml").read_text())
    tag = cfg.get("tag")
    if not tag:
        raise ValueError(f"{run_dir}: saved config has no top-level tag; cannot find its launch")
    date = run_dir.name[:8]
    hits = []
    for pat in (f"run-{date}_*", "run-*"):
        for mf in glob.glob(os.path.join(_ROOT, "wandb", pat, "files", "wandb-metadata.json")):
            try:
                args = json.load(open(mf)).get("args", [])
            except (ValueError, OSError):
                continue
            if "--tag" in args and args.index("--tag") + 1 < len(args) \
                    and args[args.index("--tag") + 1] == tag:
                hits.append((mf, args))
        if hits:
            break
    if len(hits) != 1:
        raise ValueError(f"{run_dir}: {len(hits)} local WandB folders launched with --tag {tag} "
                         f"({[h[0] for h in hits]}); exactly one is required")
    return hits[0][1]


def run_seed(run_dir) -> int:
    """Saved top-level seed, cross-checked against the launch `--seed`; mismatch raises."""
    import yaml
    cfg = yaml.safe_load((Path(run_dir) / "models" / "config.yaml").read_text())
    seed = int(cfg["seed"])
    args = launch_args(run_dir)
    if "--seed" in args:
        launched = int(args[args.index("--seed") + 1])
        if launched != seed:
            raise ValueError(f"{run_dir}: saved seed {seed} != launch --seed {launched}")
    return seed


def build(run_dir, seed: int | None = None):
    """(model, env_params) of the run at step 0. `seed=None` uses the run's own (checked)
    seed; another value builds the same architecture from another seed (reference networks)."""
    import jax
    from flax import nnx

    from src.environment.config_loader import Config, load_env_params
    from src.environment.saved_config_compat import apply_saved_config_compat
    from src.environment.sensor import get_observation_breakdown
    from src.models.modulation_compat import translate_legacy_modulation_config
    from src.models.recurrent_ppo_network import ActorCriticRNN

    run_dir = Path(run_dir)
    cfg_path = str(run_dir / "models" / "config.yaml")
    cfg = Config.load_yaml(cfg_path)
    d = copy.deepcopy(cfg.to_dict())
    apply_saved_config_compat(d, source=cfg_path)
    env_params = load_env_params(Config(d))
    bd = get_observation_breakdown(env_params)
    input_dim = sum(bd.values())
    action_dim = 4 + int(env_params.rest_action_enabled) + int(env_params.eat_action_enabled)
    agent_cfg = cfg.to_dict()["agent"]
    mod = agent_cfg.get("modulation")
    if mod is not None and mod.get("type") is None:
        mod = None
    mod = translate_legacy_modulation_config(mod, source=cfg_path)

    seed = run_seed(run_dir) if seed is None else int(seed)
    key = jax.random.PRNGKey(seed)
    key, _model_key, _env_key = jax.random.split(key, 3)     # train.py:1153
    key, init_key = jax.random.split(key)                    # train.py:1207
    model = ActorCriticRNN(
        input_dim=input_dim, action_dim=action_dim, hidden_size=agent_cfg["hidden_size"],
        rngs=nnx.Rngs(init_key), rnn_type=agent_cfg["rnn_type"],
        activation=agent_cfg["activation"], modulation_config=mod,
        observation_breakdown=bd, encoding_config=agent_cfg)
    return model, env_params


def param_arrays(model) -> dict:
    """{path string: numpy array} of the model's nnx.Param leaves."""
    import jax
    import numpy as np
    from flax import nnx
    flat, _ = jax.tree_util.tree_flatten_with_path(nnx.state(model, nnx.Param))
    return {jax.tree_util.keystr(k): np.asarray(v) for k, v in flat}
