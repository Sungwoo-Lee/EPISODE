"""The trainer's random-key recipe for a run's starting state, in one place.

Plain-language purpose: a training run's starting network and its first world are drawn from
random keys derived from the run's seed. No step-0 checkpoint is saved, so the analysis tools
rebuild a run's untrained network from the same keys (scripts/analysis/nmn/untrained.py).
Both `train.py` and that rebuild call this one function, so they cannot drift apart.

The chain is not the obvious one: the middle key of the first split (`_model_key`) is never
used; the network is built from `init_key`, a second split.

**Changing this function changes the starting network and first world of every run launched
after the change, and breaks the rebuild of every run launched before it.** It is pinned by
golden keys for seeds 42-44 (tests/utils/test_init_keys.py), recorded on the commit before
this function existed.

Plan: docs/develop/active/neuromodulation/ALGORITHMIC_NULL_ANALYSIS_TOOLING.md, Revision 4, R4-6.
"""
from __future__ import annotations

import jax


def trainer_init_keys(seed: int):
    """(key, env_key, init_key) for a run with top-level `seed`.

    `env_key` resets the first world; `init_key` builds the network (nnx.Rngs(init_key));
    `key` is the carry the training loop continues from."""
    key = jax.random.PRNGKey(seed)
    key, _model_key, env_key = jax.random.split(key, 3)   # _model_key: never used
    key, init_key = jax.random.split(key)
    return key, env_key, init_key
