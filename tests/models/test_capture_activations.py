"""Tests for the opt-in layer-capture path `ActorCriticRNN.forward_with_activations`.

Plain-language context: the analysis tooling of "What Both Agents Compute" needs to read
the network's internal layers (encoder, memory, actor and critic hidden layers, before and
after the modulator's gain and offset). The capture is a second public method that runs
the SAME computation as `__call__` and additionally returns a dict of named tensors. These
tests defend four promises:

  1. Capturing changes nothing: the four outputs of `forward_with_activations` equal
     `__call__`'s, inside `nnx.jit` + `lax.scan`, for every network shape in use.
  2. Construction is untouched: the parameter tree built from a fixed key hashes to the
     golden value recorded on the commit BEFORE the capture edit (872b0e04), for the real
     ordinary and t16quad agent blocks of the level-05 study.
  3. No state leak: a capture call adds no variable to the module state (a sown variable
     would break every strict checkpoint restore in the project).
  4. The key set is exactly the documented one; a `.mod` key exists iff that site's FiLM
     is enabled.

The reconstruction ("each captured tensor recomputed from its neighbour") is tested in
`test_capture_chain_reconstruction` with the same chain function the replay tool runs on
real checkpoints (scripts/analysis/nmn/teacher_forced.py).

Plan: docs/develop/active/neuromodulation/ALGORITHMIC_NULL_ANALYSIS_TOOLING.md, File Changes §1-2.
"""
import copy
import hashlib
import os
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

import jax
jax.config.update("jax_platform_name", "cpu")

import jax.numpy as jnp
import numpy as np
import pytest
from flax import nnx

from src.models.recurrent_ppo_network import ActorCriticRNN

# ── Real agent blocks (copied from the level-05 w0000 runs' saved models/config.yaml) ────
L05_BREAKDOWN = {"Satiation": 1, "Body Temperature": 1, "Interoceptive Nociception": 1,
                 "Extero Nociception": 1, "Thermoception": 5, "Olfaction": 25,
                 "Collision": 5, "Proprioception": 6, "Visual": 13}
L05_D, L05_A = 58, 6
AGENT_BASE = {
    "hidden_size": 128, "use_layer_norm": True, "rnn_type": "GRU", "activation": "relu",
    "encoding_mode": "hierarchical",
    "hierarchical_params": {"default_mlp": [128, 128],
                            "unimodal_overrides": {"visual": [128, 128], "olfaction": [128, 128]},
                            "multimodal_hub": [128, 128]},
}
T16QUAD_MOD = {"type": "FiLM", "mod_hidden_size": 16, "grouping_size": 1,
               "percept_bias_init": 3.0, "percept_add_bias_init": 0.0, "memory_bias_init": 0.0,
               "memory_clip": [-2.0, 2.0], "input_sensors": "all",
               "sites": {"encoder": True, "rnn": True, "actor": True, "critic": True},
               "rnn_mechanism": "activation", "temperature": {"enabled": False}}

# Recorded on commit 872b0e04 (network file unmodified) with
# tmp/20260930_stage1_hashes.py, BEFORE forward_with_activations was added (Checkpoint 1.1).
GOLDEN_PARAM_SHA256 = {
    "ordinary": "3923c5b4e558b857e3e15e5cfdf93a58b11dd85aed09525d237566063dd5ced5",
    "t16quad": "b8684a9c68f716128b6057d62641d3050caac89e805e0fde1d8b3cfe81cb9172",
}


def _build(mod=None, *, encoding="hierarchical", ln=True, activation="relu", key=0,
           breakdown=None, D=None, A=None, hidden=None):
    agent = copy.deepcopy(AGENT_BASE)
    agent["encoding_mode"] = encoding
    agent["use_layer_norm"] = ln
    if hidden is not None:
        agent["hidden_size"] = hidden
        agent["hierarchical_params"] = {"default_mlp": [hidden], "multimodal_hub": [hidden]}
    bd = L05_BREAKDOWN if breakdown is None else breakdown
    return ActorCriticRNN(
        input_dim=D or L05_D, action_dim=A or L05_A, hidden_size=agent["hidden_size"],
        rngs=nnx.Rngs(jax.random.PRNGKey(key)), rnn_type="GRU", activation=activation,
        modulation_config=copy.deepcopy(mod), observation_breakdown=bd, encoding_config=agent)


def _mod(type_="FiLM", *, encoder=True, rnn=True, actor=True, critic=True,
         mechanism="activation", temperature=False):
    m = copy.deepcopy(T16QUAD_MOD)
    m["type"] = type_
    m["mod_hidden_size"] = 8
    m["sites"] = {"encoder": encoder, "rnn": rnn, "actor": actor, "critic": critic}
    m["rnn_mechanism"] = mechanism
    m["temperature"] = {"enabled": True, "clip": [0.5, 3.0]} if temperature else {"enabled": False}
    return m


SMALL_BD = {"a": 3, "b": 5, "c": 2}
# name -> kwargs for _build. Small hidden sizes keep the scan fast; the real 128-wide
# blocks are covered by the golden-hash test and by the run-time assertions of Stage 2.
CONFIGS = {
    "ordinary_hier_ln": dict(mod=None, breakdown=SMALL_BD, D=10, A=6, hidden=16),
    "t16quad_film_activation": dict(mod=_mod(), breakdown=SMALL_BD, D=10, A=6, hidden=16),
    "film_gate_bias_temp": dict(mod=_mod(mechanism="gate_bias", temperature=True,
                                         actor=False, critic=False),
                                breakdown=SMALL_BD, D=10, A=6, hidden=16),
    "film_actor_only": dict(mod=_mod(encoder=False, rnn=False, critic=False),
                            breakdown=SMALL_BD, D=10, A=6, hidden=16),
    "flat_ordinary": dict(mod=None, encoding="flat", breakdown=SMALL_BD, D=10, A=6, hidden=16),
    "flat_film": dict(mod=_mod(), encoding="flat", breakdown=SMALL_BD, D=10, A=6, hidden=16),
    "preactivation": dict(mod=_mod("PreActivation"), breakdown=SMALL_BD, D=10, A=6, hidden=16),
    "multiplicative_no_ln": dict(mod=_mod("Multiplicative"), ln=False, breakdown=SMALL_BD,
                                 D=10, A=6, hidden=16),
}


def expected_keys(model) -> set:
    keys = {"rnn.state", "rnn.raw", "rnn.out", "actor.raw", "actor.out",
            "critic.raw", "critic.out", "enc.raw", "enc.out", "logits", "value"}
    if model.obs_encoder.mode == "hierarchical":
        keys |= {"enc.uni.raw", "enc.uni.out"}
    if model.site_encoder:
        keys.add("enc.mod")
        if model.obs_encoder.mode == "hierarchical":
            keys.add("enc.uni.mod")
    if model.site_rnn and not model._uses_gate_bias:
        keys.add("rnn.mod")
    if model.site_actor:
        keys.add("actor.mod")
    if model.site_critic:
        keys.add("critic.mod")
    return keys


def _scan_both(model, xs, h0):
    def body(m, xs, h0):
        def step(carry, x):
            h_a, h_b = carry
            la, va, ha, _ = m(x, h_a)
            lb, vb, hb, _, acts = m.forward_with_activations(x, h_b)
            return (ha, hb), (la, va, lb, vb, ha, hb, acts)
        return jax.lax.scan(step, (h0, h0), xs)[1]
    return nnx.jit(body)(model, xs, h0)


def _param_sha(model) -> str:
    flat, _ = jax.tree_util.tree_flatten_with_path(nnx.state(model, nnx.Param))
    h = hashlib.sha256()
    for k, v in sorted(flat, key=lambda kv: jax.tree_util.keystr(kv[0])):
        a = np.asarray(v)
        h.update(jax.tree_util.keystr(k).encode()); h.update(str(a.dtype).encode())
        h.update(str(a.shape).encode()); h.update(np.ascontiguousarray(a).tobytes())
    return h.hexdigest()


@pytest.mark.parametrize("name", list(CONFIGS))
def test_capture_equals_call(name):
    model = _build(**CONFIGS[name])
    B, T = 4, 20
    xs = 3.0 * jax.random.normal(jax.random.PRNGKey(7), (T, B, CONFIGS[name]["D"]))
    h0 = model.initial_state(B)
    la, va, lb, vb, ha, hb, acts = _scan_both(model, xs, h0)
    for a, b, what in ((la, lb, "logits"), (va, vb, "value")):
        a, b = np.asarray(a), np.asarray(b)
        dev = float(np.max(np.abs(a - b)))
        assert dev <= 1e-6 * max(1.0, float(np.max(np.abs(a)))), (name, what, dev)
        print(f"{name} {what}: max|Δ| = {dev:.3g} (bitwise equal: {np.array_equal(a, b)})")
    for a, b in zip(jax.tree_util.tree_leaves(ha), jax.tree_util.tree_leaves(hb)):
        assert float(np.max(np.abs(np.asarray(a) - np.asarray(b)))) <= 1e-6
    assert np.array_equal(np.argmax(np.asarray(la), -1), np.argmax(np.asarray(lb), -1))
    assert np.array_equal(np.asarray(acts["logits"]), np.asarray(lb))
    assert set(acts) == expected_keys(model), (name, sorted(set(acts) ^ expected_keys(model)))


@pytest.mark.parametrize("name", list(CONFIGS))
def test_no_state_leak(name):
    model = _build(**CONFIGS[name])
    before = jax.tree_util.tree_map(lambda x: getattr(x, "shape", None), nnx.state(model))
    paths_before = sorted(jax.tree_util.keystr(k) for k, _ in
                          jax.tree_util.tree_flatten_with_path(nnx.state(model))[0])
    x = jnp.ones((2, sum(CONFIGS[name]["breakdown"].values())))
    h = model.initial_state(2)
    nnx.jit(lambda m, x, h: m.forward_with_activations(x, h))(model, x, h)
    model.forward_with_activations(x, h)          # eager call too
    after = jax.tree_util.tree_map(lambda x: getattr(x, "shape", None), nnx.state(model))
    paths_after = sorted(jax.tree_util.keystr(k) for k, _ in
                         jax.tree_util.tree_flatten_with_path(nnx.state(model))[0])
    assert paths_before == paths_after
    assert jax.tree_util.tree_structure(before) == jax.tree_util.tree_structure(after)
    assert jax.tree_util.tree_leaves(before) == jax.tree_util.tree_leaves(after)


@pytest.mark.parametrize("which", ["ordinary", "t16quad"])
def test_construction_pinned_golden_hash(which):
    mod = None if which == "ordinary" else T16QUAD_MOD
    model = _build(mod=mod, key=0)
    assert _param_sha(model) == GOLDEN_PARAM_SHA256[which]


def test_ordinary_rnn_raw_is_state():
    """nnx.GRUCell returns (h, h): for the ordinary agent rnn.raw == rnn.state == rnn.out."""
    model = _build(**CONFIGS["ordinary_hier_ln"])
    x = jnp.ones((3, 10))
    _, _, _, _, acts = nnx.jit(lambda m, x, h: m.forward_with_activations(x, h))(
        model, x, model.initial_state(3))
    assert np.array_equal(np.asarray(acts["rnn.raw"]), np.asarray(acts["rnn.state"]))
    assert np.array_equal(np.asarray(acts["rnn.out"]), np.asarray(acts["rnn.raw"]))
