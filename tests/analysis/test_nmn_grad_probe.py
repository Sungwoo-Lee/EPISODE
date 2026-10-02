"""Tests for scripts/analysis/nmn/grad_probe.py (tooling plan File Changes §11, Checkpoint 4.2).

Unit: the PPOConfig copy has train.py's fields in train.py's order (read from train.py's syntax
tree; importing train.py would run its argv pre-parser); the trainer's update_step is restored
after the probe, also on an error. Integration (a real level-05 checkpoint, CPU): the per-term
gradients of the first update add up to the trainer's own gradient norm, shares lie in [0, 1],
the full-iteration mean has K_epochs updates, and the model and optimiser passed in are not
modified.
"""
import ast
import os
import sys
from pathlib import Path

import numpy as np
import pytest

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
os.environ.setdefault("JAX_PLATFORMS", "cpu")

from scripts.analysis.nmn import grad_probe as gp  # noqa: E402

RUN = _REPO / "results/JAX_RecurrentPPO/20260927-053059_rppo_l05body_w0000_t16quad_s42"
STEP = 200019


def _train_py_ppoconfig_fields():
    tree = ast.parse((_REPO / "train.py").read_text())
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "PPOConfig":
            return [s.target.id for s in node.body if isinstance(s, ast.AnnAssign)]
    raise AssertionError("train.py has no PPOConfig")


def test_ppoconfig_fields_equal_train_py():
    assert list(gp.PPOConfig._fields) == _train_py_ppoconfig_fields()


def test_update_step_restored_after_probe_context():
    from src.models import recurrent_ppo_trainer as rpt
    orig = rpt.update_step
    with pytest.raises(RuntimeError):
        with gp._split_first_update(4):
            assert rpt.update_step is not orig
            raise RuntimeError("boom")
    assert rpt.update_step is orig


@pytest.mark.integration
def test_probe_on_a_real_checkpoint():
    if not (RUN / "models" / str(STEP)).is_dir():
        pytest.skip("run not present (gitignored)")
    from flax import nnx
    from scripts.analysis.nmn import replay
    from src.environment.config_loader import Config
    agent = replay.load_agent(RUN / "models", STEP)
    cfg = Config.load_yaml(str(RUN / "models" / "config.yaml"))
    config = gp.ppo_config(cfg)
    opt = gp.make_optimizer(agent.model, config)
    meta = gp.restore_optimizer(RUN / "models", STEP, agent.model, opt, 128)
    assert meta["episode"] == STEP
    before_m = nnx.state(agent.model, nnx.Param).to_pure_dict()
    before_o = [np.asarray(x) for x in __import__("jax").tree_util.tree_leaves(nnx.state(opt))]
    out = gp.probe(agent.model, opt, agent.env_params, config, num_envs=16, seed=90000,
                   warmup_iters=1)
    assert out["first_update_sum_vs_trainer_rel_dev"] < 1e-4
    for t in gp.TERMS + ("total",):
        assert 0.0 <= out["first_update"][t]["share"] <= 1.0
    assert len(out["full_iteration"]["per_update"]) == config.num_epochs
    after_m = nnx.state(agent.model, nnx.Param).to_pure_dict()
    import jax
    assert all(np.array_equal(a, b) for a, b in zip(jax.tree_util.tree_leaves(before_m),
                                                    jax.tree_util.tree_leaves(after_m)))
    after_o = [np.asarray(x) for x in jax.tree_util.tree_leaves(nnx.state(opt))]
    assert all(np.array_equal(a, b) for a, b in zip(before_o, after_o))
