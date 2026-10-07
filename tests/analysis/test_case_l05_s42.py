"""Tests for the L05 S42 case study tooling (scripts/analysis/case_l05_s42/, and the live tool's
`act_true` orientation and per-layer capture in scripts/analysis/obs_manipulation/run.py).

Plain-language context: the case study measures, layer by layer, how much a change in felt
injury alone moves the network (Analysis 1), whether that movement points toward "about to go
to the bush" (Analysis 2), and which modulator site carries the extra hiding (Analysis 3). Four
ways the numbers could be wrong without anything looking wrong:

* the comparison could leak a difference that is not the felt-injury input -> with an identity
  manipulation the two captured passes must be equal at every layer, and the acting agent must
  reproduce the dwell sweep's recorded episodes exactly;
* the shift could come from something other than felt injury -> a network that cannot see felt
  injury must give exactly zero shift at every layer, while the real one gives a clearly
  non-zero shift;
* the freeze pipeline could disturb actions it should not touch -> freezing the critic site
  must leave greedy trajectories bit-identical;
* the readout label could include steps where the agent is already on the bush (then it decodes
  position, not intent) or censored tails -> checked on a hand-built episode.

Real-checkpoint tests use the case modulated agent (22-Sep level 05 seed 42, step 6000013) and
are skipped if it is not on disk.
"""
import os
import sys

import numpy as np
import pytest

os.environ.setdefault("JAX_PLATFORMS", "cpu")
os.environ.setdefault("XLA_FLAGS", "--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=1")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from scripts.analysis.case_l05_s42 import measures as MS  # noqa: E402

PAIR_KEY, STEP = "orig_lvl05_s42", 6000013


# --------------------------------------------------------------------------
# synthetic
# --------------------------------------------------------------------------

def test_readout_labels_exclude_on_bush_steps_and_censored_tail():
    # one episode of 12 steps: positions 0..12 (13 snapshot rows); bush at (0, 0)
    onb = np.zeros((13, 1), bool)
    onb[[6, 7, 8], 0] = True                  # on the bush at snapshot rows 6-8
    T = np.array([12])
    mask, lab = MS.arrival_labels(onb, T, horizon=5)
    m, l = mask[:, 0], lab[:, 0]
    assert not m[6] and not m[7] and not m[8]          # on-bush steps never enter the readout
    assert not m[7:].any()                             # t >= T - 5 = 7 dropped (censored tail)
    assert list(np.flatnonzero(m)) == [0, 1, 2, 3, 4, 5][:6] and not m[6]
    # arrival within 5 steps: t = 1..5 see row 6 within t+1..t+5; t = 0 does not (rows 1..5)
    assert list(l[:6]) == [False, True, True, True, True, True]
    # labels only where the mask is set
    assert not (lab & ~mask).any()


def test_arrival_labels_match_a_brute_force_definition():
    rng = np.random.default_rng(0)
    onb = rng.random((101, 7)) < 0.2
    T = rng.integers(10, 101, 7)
    mask, lab = MS.arrival_labels(onb, T)
    for b in range(7):
        for t in range(100):
            want_m = (t < T[b] - 5) and not onb[t, b]
            assert mask[t, b] == want_m
            if want_m:
                assert lab[t, b] == bool(onb[t + 1: t + 6, b].any())


def test_shift_size_drops_dead_units_and_reports_both_terms():
    rng = np.random.default_rng(1)
    ref = rng.normal(size=(500, 4)); ref[:, 3] = 2.0          # unit 3 never varies
    keep, mu, sd, den = MS.spread(ref)
    assert list(keep) == [True, True, True, False]
    np.testing.assert_allclose(den, np.sqrt((ref[:, :3].std(0) ** 2).sum()))
    nat = rng.normal(size=(50, 4))
    man = nat.copy(); man[:, 0] += 3.0; man[:, 3] += 100.0     # a shift in a dead unit is ignored
    num, size, dead = MS.shift_size(man, nat, keep, den)
    assert num == pytest.approx(3.0) and size == pytest.approx(3.0 / den)
    assert dead == pytest.approx(100.0)                         # reported apart, never in the size


def test_push_is_in_logit_sd_units_and_cosine_is_scale_free():
    rng = np.random.default_rng(2)
    w = np.array([1.0, 0.0, 0.0]); Z = rng.normal(size=(1000, 3))
    res = MS.push(w, 0.0, Z, np.tile([0.5, 0.0, 0.0], (10, 1)))
    assert res["push_logodds"] == pytest.approx(0.5)
    assert res["push_sd"] == pytest.approx(0.5 / Z[:, 0].std())
    assert res["cos_shift_readout"] == pytest.approx(1.0)


def test_reading_rule_counts():
    assert MS.count_expected([1, 2, -1, np.nan, 0]) == (2, 1, 5)
    assert MS.condition_met("case", 7) and not MS.condition_met("case", 6)
    assert MS.condition_met("same_seed", 6) and not MS.condition_met("same_seed", 5)
    assert MS.condition_met("reverse", 5) and not MS.condition_met("reverse", 6)


# --------------------------------------------------------------------------
# real checkpoint
# --------------------------------------------------------------------------

def _pair():
    from scripts.analysis.modulator_engagement import runs as R
    return R.select(PAIR_KEY)[0]


def _have_checkpoint():
    try:
        return os.path.isdir(os.path.join(_pair().run_dirs["modulated"], "models", str(STEP)))
    except Exception:
        return False


needs_ckpt = pytest.mark.skipif(not _have_checkpoint(), reason="case checkpoint not on disk")


def _setup(scene="avoid_none_inj00"):
    from scripts.analysis.modulator_engagement import engagement as E, runs as R
    from scripts.analysis.nmn import replay
    om, MP = E._om()
    p = _pair()
    probe, n_ep, out_dir, labels = R.spec_scene(p)
    path, _, w, bm = E._world(probe, scene)
    seeds = E._seeds(bm, n_ep, path)
    models = os.path.join(p.run_dirs["modulated"], "models")
    return E, om, MP, p, out_dir, labels, w, seeds, models, replay


def _const(MP, E, br, Tm, value):
    return MP.from_spec({"manipulations": [{"name": "f", "sensor": E.FELT, "element": 0, "op": "set",
                                            "values": [value], "steps": [0, None]}]}, br, Tm)


@pytest.mark.integration
@needs_ckpt
def test_identity_reproduces_live_exactly_in_act_true_orientation():
    """act_true orientation, identity manipulation: the two captured passes are equal at every
    layer (zero shift), the acting episodes equal the original orientation's and the dwell
    sweep's recordings exactly, and the chain assertions hold on the captured tensors."""
    from scripts.analysis.case_l05_s42 import case as C
    sys.path.insert(0, os.path.join(ROOT, "scripts", "behavior_measures"))
    from avoidance_stats_heatmap import episode_measures
    E, om, MP, p, out_dir, labels, w, seeds, models, replay = _setup()
    agent = replay.load_agent(models, STEP)
    ident = MP.from_spec({"manipulations": [{"name": "f", "sensor": E.FELT, "element": 0, "op": "add",
                                             "values": [0.0], "steps": [0, None]}]},
                         agent.obs_breakdown, int(w.max_steps))
    r = om.run_checkpoint(agent, w, seeds, ident, "sustained", orientation="act_true", capture=True)
    o = r["out"]
    for k in o["acts_nat"]:
        if k == "value":
            # the shadow's value output is unused, and XLA compiles the two critic-output calls
            # differently (|diff| ~5e-7 observed 2026-10-07); every LAYER and the logits are exact
            np.testing.assert_allclose(o["acts_nat"][k], o["acts_man"][k], atol=1e-5, err_msg=k)
        else:
            np.testing.assert_array_equal(o["acts_nat"][k], o["acts_man"][k], err_msg=k)
    np.testing.assert_array_equal(o["h_mod"], o["h_mod_shadow"])
    assert float(o["capture_dlogit"].max()) <= 1e-6
    old = om.run_checkpoint(agent, w, seeds, ident, "sustained")           # original orientation
    assert np.array_equal(old["out"]["action"], o["action"]) and np.array_equal(old["T"], r["T"])
    scratch = os.path.join(ROOT, out_dir, "_scratch", labels["modulated"], "avoid_none_inj00")
    om._parity(scratch, STEP, seeds, r["states0_np"], o, r["T"], len(seeds), episode_measures)
    dev = C._chain(agent, o, np.arange(2 * len(seeds)), "nat")
    assert max(dev.values()) <= C.G2_TOL, dev


@pytest.mark.integration
@needs_ckpt
def test_act_true_route_is_natural_and_shift_is_nonzero():
    """With felt injury 0.70 in the shadow, the acting episodes still equal the identity's (the
    tool asserts it), and the real network's shift is clearly non-zero (positive control)."""
    E, om, MP, p, out_dir, labels, w, seeds, models, replay = _setup()
    agent = replay.load_agent(models, STEP)
    M = _const(MP, E, agent.obs_breakdown, int(w.max_steps), 0.70)
    r = om.run_checkpoint(agent, w, seeds, M, "sustained", orientation="act_true", capture=True)
    N, o, v = len(seeds), r["out"], r["valid"]
    rows = np.arange(N, 2 * N)
    d = np.abs(o["acts_man"]["rnn.state"][:, rows] - o["acts_nat"]["rnn.state"][:, rows])[v[:, rows]]
    assert float(d.mean()) > 1e-3


def _jit_slot(model, flat_idx):
    """(group, element) of the encoder's padded input that flat observation element `flat_idx`
    lands in, as the encoder packs it INSIDE nnx.jit. Under jit the module's `breakdown` dict is
    iterated in pytree (sorted-key) order, not config order, so the "unimodal" groups receive
    sorted-order slices of the config-order observation (found 2026-10-07; this test would
    otherwise zero the wrong weight). Read from a traced call, not assumed."""
    from flax import nnx
    import jax.numpy as jnp
    seen = {}

    def f(m, x):
        seen["order"] = list(m.obs_encoder.breakdown.items())
        return x
    nnx.jit(f)(model, jnp.zeros(1))
    start = 0
    for i, (_name, dim) in enumerate(seen["order"]):
        if start <= flat_idx < start + dim:
            return i, flat_idx - start
        start += dim
    raise ValueError(flat_idx)


@pytest.mark.integration
@needs_ckpt
def test_nociception_blind_model_gives_zero_shift_at_every_layer():
    """Zero every weight that reads the felt-injury input (its row in the encoder's first
    unimodal layer and in the modulator GRU's input kernel): the shift must be exactly zero at
    every captured layer and in the modulator state."""
    from scripts.analysis.case_l05_s42 import case as C
    E, om, MP, p, out_dir, labels, w, seeds, models, replay = _setup()
    blind = replay.load_agent(models, STEP)
    m = blind.model
    enc = m.obs_encoder
    assert enc.mode == "hierarchical"
    idx = MP.sensor_offsets(blind.obs_breakdown)[E.FELT][0]
    g, e = _jit_slot(m, idx)
    first = enc.unimodal_grouped.net.layers[0]
    first.weights.value = first.weights.value.at[g, e, :].set(0.0)
    assert m._mod_input_is_all
    k = m.modulator.gru.dense_i.kernel
    k.value = k.value.at[idx, :].set(0.0)
    M = _const(MP, E, blind.obs_breakdown, int(w.max_steps), 0.70)
    r = om.run_checkpoint(blind, w, seeds, M, "sustained", orientation="act_true", capture=True)
    rows = np.arange(len(seeds), 2 * len(seeds))
    arrs = C._layer_arrays(r["out"], rows, True)
    assert set(arrs) >= {"enc.uni.out", "enc.out", "rnn.state", "rnn.out", "actor.out", "critic.out", "mod.state"}
    for L, (nat, man) in arrs.items():
        assert float(np.abs(man - nat).max()) == 0.0, L


@pytest.mark.integration
@needs_ckpt
def test_critic_freeze_is_a_null_control():
    """Freezing the critic site's gain and offset (to any per-unit target) must leave greedy
    trajectories bit-identical; the freeze must actually take (critic gain constant)."""
    from scripts.analysis.case_l05_s42 import case as C
    from scripts.analysis.nmn import freeze
    E, om, MP, p, out_dir, labels, w, seeds, models, replay = _setup("avoid_rabbitwander_inj70")
    live_agent = replay.load_agent(models, STEP)
    means, live = E._pooled_means(live_agent, {"s": w}, seeds, om, MP)
    fa = replay.load_agent(models, STEP)
    freeze.apply_freeze(fa.model, {"critic": means["critic"]}, freeze_gain=True, freeze_offset=True)
    _, fr = E._pooled_means(fa, {"s": w}, seeds, om, MP)
    assert C._same_traj(fr["s"], live["s"])
    N = len(seeds)
    g = fr["s"]["out"]["ugain_critic"][:, :N][fr["s"]["valid"][:, :N]]
    assert float(np.ptp(g, axis=0).max()) == 0.0
    # the live critic gain does vary, so the control is not vacuous
    g0 = live["s"]["out"]["ugain_critic"][:, :N][live["s"]["valid"][:, :N]]
    assert float(np.ptp(g0, axis=0).max()) > 0.0
