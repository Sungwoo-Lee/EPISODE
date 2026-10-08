"""Tests for the modulator-input internals screen (scripts/analysis/modinput_internals/) and the
analysis-only hide in the network (`ActorCriticRNN.forward_hidden`).

Plain-language context: the screen hides felt injury from the modulator, the main network, or
both, inside the forward pass, and reads how much injured bush dwell goes away. Ways it could be
wrong without anything looking wrong, and the test that guards each:

* the edit could change the network the agents trained and act with -> the traced program of
  `__call__` hashes to the value recorded BEFORE the edit, and `forward_hidden` without a hide
  gives `__call__`'s outputs bit for bit inside jit + scan (no-hide identity);
* the hide could land on the wrong column, leak into the other network, or touch other inputs ->
  the captured modulator and main-network inputs are checked column by column, including the
  "all" modulator whose input is the same array as the main network's, and the driver's own
  checker rejects a wrong capture (input-capture assertion);
* an agent whose modulator never reads felt injury (variant X) would give a share of 0 "by
  construction" and look like a pass -> it is refused (X refused);
* the unhurt scenes could carry non-zero felt injury, making "unhurt identical across conditions"
  false -> the run-time assertion fails loudly on any non-zero step (unhurt-zero precondition);
* the share / additivity / survival rules could be coded differently from Revision 1a ->
  synthetic data with known answers.

Real-checkpoint tests use the modulator-input runs and the replication reference at seed 42 and
are skipped if they are not on disk.
"""
import copy
import hashlib
import os
import sys

import numpy as np
import pytest

os.environ.setdefault("JAX_PLATFORMS", "cpu")
os.environ.setdefault("XLA_FLAGS", "--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=1")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests", "models"))

import jax  # noqa: E402
import jax.numpy as jnp  # noqa: E402
from flax import nnx  # noqa: E402

import test_capture_activations as TCA  # noqa: E402
from scripts.analysis.modinput_internals import internals as I  # noqa: E402
from scripts.analysis.modinput_internals import measures as M  # noqa: E402

FELT = "Interoceptive Nociception"

# sha256 of str(jax.make_jaxpr(__call__)) for the small test networks, recorded with
# tmp/20261008_modinput_jaxpr_golden.py on the network file of commit a02b2a0d, BEFORE
# forward_hidden was added.
GOLDEN_JAXPR = {
    "ordinary_hier_ln": "d281ff237efcfabdf5326d009d2023ddced184b12c54072c00ec3c49fc8e0381",
    "t16quad_film_activation": "47fa5fc71a11d11d639af5f5061d263e7d04b7b495642e10999faa43700e9854",
    "film_gate_bias_temp": "88c8735686b82d0a3883498db4acd6dcc9d3d9246fcd9def4161137a2cf69fb1",
    "film_actor_only": "2753effc7a55a5b84a9b024ad44ff42484bfba248bc1ac811f69090734b97f7d",
    "flat_ordinary": "d8eb76c20f0a48631cd5f079d4064f220d6e7c600d0ebf25e4790f5bc4fa23c6",
    "flat_film": "8c74e9e2a00251087a01eec93154e3f81d94148b93172106b37a93bb5f29a67c",
    "preactivation": "8b001cb19e664634b42ae52f48dfb35d8801d4428ab48ac5ccc4fe604d961550",
    "multiplicative_no_ln": "6c4f04530baec5efdf1da1287d869094794533bfa3cea82aefe27686e03217a4",
    "film_subset_inputs": "cbd48b1e37df2522ddac3e1d5740112c61de4523a7442521aae9065494de2a2b",
}

# a small breakdown with a felt-injury sensor at a non-zero offset (column 3)
BD = {"Satiation": 1, "Body Temperature": 2, FELT: 1, "Olfaction": 4, "Visual": 2}
D = 10


def _configs():
    c = dict(TCA.CONFIGS)
    mm = TCA._mod()
    mm["input_sensors"] = ["c", "a"]
    c["film_subset_inputs"] = dict(mod=mm, breakdown=TCA.SMALL_BD, D=10, A=6, hidden=16)
    return c


def _jaxpr_hash(model, D_):
    g, s = nnx.split(model)
    x = jnp.linspace(-1, 2, D_).astype(jnp.float32)[None].repeat(3, 0)
    h = model.initial_state(batch_size=3)
    f = lambda s, x, h: nnx.merge(g, s)(x, h)
    return hashlib.sha256(str(jax.make_jaxpr(f)(s, x, h)).encode()).hexdigest()


def _net(inputs="all", mod=True, key=1):
    m = None
    if mod:
        m = TCA._mod()
        m["input_sensors"] = inputs
    return TCA._build(mod=m, breakdown=BD, D=D, A=6, hidden=16, key=key)


def _obs(T=6, B=4, seed=0):
    x = np.random.default_rng(seed).uniform(0, 5, size=(T, B, D)).astype(np.float32)
    return jnp.asarray(x)


def _symlog(x):
    return jnp.sign(x) * jnp.log(jnp.abs(x) + 1.0)


# ------------------------------------------------------------------ no-hide identity
@pytest.mark.parametrize("name", sorted(GOLDEN_JAXPR))
def test_training_path_traced_program_unchanged(name):
    kw = _configs()[name]
    assert _jaxpr_hash(TCA._build(**kw), kw["D"]) == GOLDEN_JAXPR[name]


@pytest.mark.parametrize("inputs,mod", [("all", True), ([FELT], True), (["Satiation", FELT], True),
                                        (None, False)])
def test_forward_hidden_without_hide_is_the_same_program_and_bit_identical(inputs, mod):
    """(a) The traced program of forward_hidden(None, None) (its four outputs) is op-for-op the
    traced program of __call__. (b) Two separately compiled scans give identical bits. (Inside
    ONE compiled program XLA may fuse the two calls differently at the 1e-7 level -- see
    test_capture_activations; the q3 driver's own live check on real checkpoints requires 0.)"""
    net = _net(inputs, mod)
    xs = _obs()
    h0 = net.initial_state(batch_size=xs.shape[1])
    g, st = nnx.split(net)
    jp_call = jax.make_jaxpr(lambda s, x, h: nnx.merge(g, s)(x, h))(st, xs[0], h0)
    jp_hide = jax.make_jaxpr(lambda s, x, h: nnx.merge(g, s).forward_hidden(x, h, None, None)[:4])(st, xs[0], h0)
    assert str(jp_call) == str(jp_hide)

    def scan_with(f):
        def run(m, xs, h0):
            def step(h, x):
                lg, v, h2 = f(m, x, h)
                return h2, (lg, v, h2)
            return jax.lax.scan(step, h0, xs)[1]
        return nnx.jit(run)(net, xs, h0)

    a = scan_with(lambda m, x, h: m(x, h)[:3])
    b = scan_with(lambda m, x, h: m.forward_hidden(x, h, None, None)[:3])
    for u, v in zip(jax.tree_util.tree_leaves(a), jax.tree_util.tree_leaves(b)):
        assert np.array_equal(np.asarray(u), np.asarray(v))


# ------------------------------------------------------------------ input capture
@pytest.mark.parametrize("inputs", ["all", [FELT], ["Satiation", FELT], [FELT, "Visual"]])
@pytest.mark.parametrize("cond", I.CONDITIONS)
def test_captured_inputs_hidden_exactly_where_intended(inputs, cond):
    net = _net(inputs)
    felt_col, felt_mod_col = I.hide_columns(net, BD)
    assert felt_col == 3
    x = _obs()[0]
    h = net.initial_state(batch_size=x.shape[0])
    hm, hx = I.HIDES[cond]
    _l, _v, _h, _m, acts = nnx.jit(lambda m, x, h: m.forward_hidden(
        x, h, felt_mod_col if hm else None, felt_col if hx else None))(net, x, h)
    xs = np.asarray(_symlog(x))
    exp_mod = xs[:, list(net.mod_input_idx)]
    mod_in, main_in = np.asarray(acts["mod.in"]), np.asarray(acts["main.in"])
    # felt column: 0 where hidden, the compressed true value where not
    assert np.array_equal(mod_in[:, felt_mod_col], np.zeros(len(x)) if hm else exp_mod[:, felt_mod_col])
    assert np.array_equal(main_in[:, felt_col], np.zeros(len(x)) if hx else xs[:, felt_col])
    # every other column untouched, in both networks
    om_ = np.arange(mod_in.shape[1]) != felt_mod_col
    on_ = np.arange(D) != felt_col
    assert np.array_equal(mod_in[:, om_], exp_mod[:, om_])
    assert np.array_equal(main_in[:, on_], xs[:, on_])


def test_hidden_input_changes_output_and_main_hide_does_not_reach_all_modulator():
    """Positive control: hiding a non-zero felt input changes the output; for an "all" modulator
    a main-only hide leaves the modulator's outputs (gain/offset) exactly as live."""
    net = _net("all")
    felt_col, felt_mod_col = I.hide_columns(net, BD)
    x = _obs()[0]
    h = net.initial_state(batch_size=x.shape[0])
    f = nnx.jit(lambda m, x, h, a, b: m.forward_hidden(x, h, a, b), static_argnums=(3, 4))
    live = f(net, x, h, None, None)
    mod_only = f(net, x, h, felt_mod_col, None)
    main_only = f(net, x, h, None, felt_col)
    assert not np.array_equal(np.asarray(live[0]), np.asarray(mod_only[0]))
    assert not np.array_equal(np.asarray(live[0]), np.asarray(main_only[0]))
    for a, b in zip(jax.tree_util.tree_leaves(live[3]), jax.tree_util.tree_leaves(main_only[3])):
        assert np.array_equal(np.asarray(a), np.asarray(b))


def test_check_inputs_rejects_a_wrong_capture():
    T, B = 5, 3
    felt = np.full((T, B), 0.5, np.float32)
    base = {"felt_true_c": felt, "mod_felt": felt.copy(), "main_felt": felt.copy(),
            "mod_dev_other": np.zeros((T, B)), "main_dev_other": np.zeros((T, B)),
            "dlogit": np.zeros((T, B))}
    valid = np.ones((T, B), bool)
    I.check_inputs({"out": base, "valid": valid}, "live", "ok")           # passes
    bad = dict(base, mod_felt=felt.copy())                                 # mod not hidden
    with pytest.raises(AssertionError, match="mod felt-injury input not 0"):
        I.check_inputs({"out": bad, "valid": valid}, "mod_hidden", "t")
    bad = dict(base, mod_felt=np.zeros_like(felt))                         # main leaked into mod
    with pytest.raises(AssertionError, match="mod felt-injury input differs"):
        I.check_inputs({"out": bad, "valid": valid}, "main_hidden", "t")
    bad = dict(base, main_dev_other=np.full((T, B), 1e-7))                 # another column moved
    with pytest.raises(AssertionError, match="non-felt main input column"):
        I.check_inputs({"out": bad, "valid": valid}, "live", "t")
    bad = dict(base, dlogit=np.full((T, B), 1e-9))
    with pytest.raises(AssertionError, match="differs from __call__"):
        I.check_inputs({"out": bad, "valid": valid}, "live", "t")


# ------------------------------------------------------------------ refusals
def test_modulator_without_felt_input_is_refused():
    net = _net(["Satiation", "Olfaction", "Visual"])
    with pytest.raises(ValueError, match="refused: the modulator does not read felt injury"):
        I.hide_columns(net, BD)


def test_ordinary_agent_is_refused_and_mod_hide_raises():
    net = _net(mod=False)
    with pytest.raises(ValueError, match="refused: the agent has no modulator"):
        I.hide_columns(net, BD)
    x = _obs()[0]
    with pytest.raises(ValueError, match="no modulator"):
        net.forward_hidden(x, net.initial_state(batch_size=x.shape[0]), 3, None)


_X_RUN = os.path.join(ROOT, "results", "JAX_RecurrentPPO", "20261007-111937_rppo_nmninp_l05_X_s42", "models")


@pytest.mark.skipif(not os.path.isdir(_X_RUN), reason="variant X run not on disk")
def test_variant_x_checkpoint_refused_by_q3():
    with pytest.raises(ValueError, match="refused"):
        I.q3_checkpoint("X", I.checkpoints("X")[20], 20, episodes=2)   # refused before any rollout


# ------------------------------------------------------------------ unhurt-zero precondition
def test_unhurt_zero_assertion():
    felt = np.zeros((10, 4), np.float32)
    valid = np.ones((10, 4), bool)
    valid[7:, 1] = False
    I.assert_unhurt_zero(felt, valid, "ok")
    felt[8, 1] = 0.3                                   # after the episode ended: ignored
    I.assert_unhurt_zero(felt, valid, "ok")
    felt[2, 3] = 1e-9                                  # a live step: fatal
    with pytest.raises(AssertionError, match="UNHURT-ZERO PRECONDITION FAILED"):
        I.assert_unhurt_zero(felt, valid, "t")


_N_RUN = os.path.join(ROOT, "results", "JAX_RecurrentPPO", "20261007-111854_rppo_nmninp_l05_N_s42", "models")


@pytest.mark.skipif(not os.path.isdir(_N_RUN), reason="variant N run not on disk")
def test_q3_real_checkpoint_runs_every_check():
    """One real checkpoint, 3 episodes: every fatal check in q3_checkpoint runs and passes
    (input capture, live == __call__, unhurt zero and unhurt identity across conditions)."""
    rows, rep = I.q3_checkpoint("N", 6000052, 20, episodes=3)
    assert len(rows) == 3 * 4 * 4                       # seeds x conditions x scenes
    assert rep["felt_mod_col"] == 0
    assert all(v.startswith("skipped") for v in rep["sweep"].values())
    unh = [r for r in rows if r["injury"] == "unhurt"]
    by = {}
    for r in unh:
        by.setdefault((r["scene"], r["seed"]), set()).add(r["bush_hiding"])
    assert all(len(v) == 1 for v in by.values())


# ------------------------------------------------------------------ Q3 arithmetic
def _arrays(eff, K=9, N=100, unhurt=0.2, noise=0.0, seed=0, surv=None):
    """dwell/surv with pooled injury effects `eff` (fraction) per condition."""
    rng = np.random.default_rng(seed)
    base = rng.normal(0, noise, size=(K, N)) if noise else np.zeros((K, N))
    dw, sv = {}, {}
    for c in M.CONDITIONS:
        a = np.empty((K, N, 2))
        a[..., 1] = unhurt
        a[..., 0] = unhurt + eff[c] + base + (rng.normal(0, noise, size=(K, N)) if noise else 0)
        dw[c] = a
        s = np.full((K, N, 2), 100.0)
        if surv and c in surv:
            s[..., 0] = surv[c]
        sv[c] = s
    return dw, sv


def test_share_additive_case():
    # live 0.20, mod 0.10, main 0.15, both 0.05: interaction 0.20-0.10-0.15+0.05 = 0
    dw, sv = _arrays({"live": .20, "mod_hidden": .10, "main_hidden": .15, "both_hidden": .05}, noise=0.05)
    r = M.pooled_share(dw, sv, n_boot=2000)
    assert r["reading"] == "share"
    assert abs(r["share"] - (r["numerator_pp"] / r["divisor_pp"])) < 1e-12
    assert 0.55 < r["share"] < 0.80           # true 0.10 / 0.15
    assert r["additive"] and not r["undefined"]


def test_share_undefined_when_divisor_interval_includes_zero():
    # clear live effect, but hiding from both barely changes it: divisor ~ 0
    dw, sv = _arrays({"live": .20, "mod_hidden": .19, "main_hidden": .20, "both_hidden": .195}, noise=0.05)
    r = M.pooled_share(dw, sv, n_boot=2000)
    assert r["effect_live_ci_lo"] > 0
    assert r["divisor_ci_lo"] <= 0 <= r["divisor_ci_hi"]
    assert r["reading"] == "undefined" and r["share"] is None


def test_share_undefined_when_live_effect_interval_includes_zero():
    dw, sv = _arrays({"live": .0, "mod_hidden": -.1, "main_hidden": -.1, "both_hidden": -.2}, noise=0.3)
    r = M.pooled_share(dw, sv, n_boot=2000)
    assert r["effect_live_ci_lo"] <= 0 <= r["effect_live_ci_hi"]
    assert r["reading"] == "undefined"


def test_not_additive_is_reported_and_blocks_the_share():
    # interaction = 0.20 - 0.10 - 0.05 + 0.10 = 0.15 (far from 0)
    dw, sv = _arrays({"live": .20, "mod_hidden": .10, "main_hidden": .05, "both_hidden": .10}, noise=0.02)
    r = M.pooled_share(dw, sv, n_boot=2000)
    assert not r["additive"]
    assert r["reading"] == "additivity not established" and r["share"] is None


def test_additivity_needs_a_narrow_interval_not_just_one_containing_zero():
    # interaction 0 in expectation, but noise so large its half-width exceeds half the divisor
    dw, sv = _arrays({"live": .20, "mod_hidden": .10, "main_hidden": .15, "both_hidden": .05},
                     K=1, N=100, noise=0.6, seed=3)
    r = M.pooled_share(dw, sv, n_boot=2000)
    if r["interaction_ci_lo"] <= 0 <= r["interaction_ci_hi"]:
        assert r["interaction_halfwidth_pp"] >= 0.5 * abs(r["divisor_pp"])
        assert not r["additive"]


def test_survival_guard_excludes_the_share():
    dw, sv = _arrays({"live": .20, "mod_hidden": .10, "main_hidden": .15, "both_hidden": .05},
                     noise=0.05, surv={"live": 100.0, "both_hidden": 85.0})
    r = M.pooled_share(dw, sv, n_boot=2000)
    assert r["survival_flagged"] == "both_hidden"
    assert r["reading"] == "excluded: survival guard" and r["share"] is None
    dw, sv = _arrays({"live": .20, "mod_hidden": .10, "main_hidden": .15, "both_hidden": .05},
                     noise=0.05, surv={"live": 100.0, "mod_hidden": 91.0})
    assert M.pooled_share(dw, sv, n_boot=2000)["survival_flagged"] == ""      # 9% < 10%


def test_bootstrap_resamples_seeds_jointly():
    """Paired structure: identical seeds in two conditions with a constant offset give a
    zero-width interval for the difference (joint resampling); independent resampling would not."""
    rng = np.random.default_rng(0)
    x = rng.uniform(0, 1, size=(9, 100))
    dw = {c: np.stack([x + off, np.zeros_like(x)], -1) for c, off in
          zip(M.CONDITIONS, (0.3, 0.1, 0.2, 0.0))}
    r = M.paired_dwell_difference(dw)
    assert abs(r["ci_hi"] - r["ci_lo"]) < 1e-9 and abs(r["diff_pp"] - 20.0) < 1e-9


# ------------------------------------------------------------------ P1-P3
def test_p1_p2_p3_counting():
    ref = {"trace": np.ones(9), "const": np.ones(9)}
    v = {"N": {"trace": np.r_[np.full(7, 2.0), np.zeros(2)], "const": np.full(9, 2.0)},
         "I": {"trace": np.r_[np.full(6, 2.0), np.zeros(3)], "const": np.full(9, 2.0)}}
    r = M.p1(v, ref)
    assert r["N"]["holds"] and not r["I"]["holds"]
    o = np.ones(9)
    r = M.p2({"N": np.full(9, 2.0), "I": np.zeros(9)}, np.r_[np.full(6, 2.0), np.zeros(3)], o)
    assert r["holds"] and r["reference"]["count"] == 6
    r = M.p2({"N": np.full(9, 2.0)}, np.r_[np.full(7, 2.0), np.zeros(2)], o)
    assert not r["holds"]                                  # reference also exceeds
    ok = {"reading": "share", "share": 0.3, "share_point": 0.3}
    assert M.p3({"N": ok, "I": ok, "IT": ok})["holds"]
    assert not M.p3({"N": ok, "I": ok, "IT": dict(ok, share=0.2, share_point=0.2)})["holds"]
    assert not M.p3({"N": ok, "I": ok, "IT": {"reading": "undefined", "share": None, "share_point": 0.9}})["holds"]
