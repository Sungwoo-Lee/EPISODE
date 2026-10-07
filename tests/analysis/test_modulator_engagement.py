"""Tests for the modulator engagement check (scripts/analysis/modulator_engagement/).

Plain-language context: the check correlates how strongly a modulated agent's modulator responds
to felt injury (E1) with its behaviour gap over an ordinary partner. Three things could make that
correlation meaningless without anything looking wrong:

* the teacher-forced comparison could leak a difference that is not the manipulated input --
  then the identity condition would not reproduce the plain, unmanipulated rollout;
* E1 could pick up something other than felt injury -- then a modulator that cannot see felt
  injury would still score E1 > 0;
* the within-level permutation null could be built wrong (wrong arrangements, a level effect
  leaking in), which would make p-values of 1/216 appear where nothing is there.

The first two use one real checkpoint (level 05, seed 42, step 6000007, the replication's
modulated run) and are skipped if it is not on disk. The third is synthetic.
"""
import os
import sys

import numpy as np
import pytest

os.environ.setdefault("JAX_PLATFORMS", "cpu")
os.environ.setdefault("XLA_FLAGS", "--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=1")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from scripts.analysis.modulator_engagement import analyze as A  # noqa: E402

PAIR_KEY, STEP = "l05_s42", 6000007


# --------------------------------------------------------------------------
# Permutation null (synthetic)
# --------------------------------------------------------------------------

LEVELS = ["a"] * 3 + ["b"] * 3 + ["c"] * 3


def test_within_level_arrangements_are_the_216_level_preserving_permutations():
    arr = A.within_level_arrangements(LEVELS)
    assert arr.shape == (216, 9)
    assert len({tuple(p) for p in arr}) == 216                        # all distinct
    assert any((p == np.arange(9)).all() for p in arr)                # identity included
    lv = np.asarray(LEVELS)
    for p in arr:
        assert sorted(p) == list(range(9))                             # a permutation
        assert (lv[p] == lv).all()                                     # never crosses a level


def test_perfect_within_level_relation_gets_the_smallest_possible_p():
    """y = x within every level, levels shifted apart: rho 1 on demeaned values and only the
    observed arrangement reaches it, so p = 1/216."""
    x = np.array([1, 2, 3, 10, 12, 14, -5, -4, -2], float)
    y = x * 2 + np.repeat([100, -50, 7], 3)
    r = A.within_level_test(x, y, LEVELS)
    assert r["rho"] == pytest.approx(1.0)
    assert r["p"] == pytest.approx(1 / 216)
    assert r["n_arrangements"] == 216


def test_a_level_effect_alone_does_not_count_as_a_relation():
    """Both measures rise with level but run AGAINST each other within level: the pooled rho is
    strongly positive, the demeaned within-level rho is -1 and its p is 1."""
    base = np.repeat([0.0, 10.0, 20.0], 3)
    x = base + np.tile([0.0, 1.0, 2.0], 3)
    y = base + np.tile([2.0, 1.0, 0.0], 3)
    assert A.spearman(x, y) > 0.6
    r = A.within_level_test(x, y, LEVELS)
    assert r["rho"] == pytest.approx(-1.0)
    assert r["p"] == pytest.approx(1.0)


def test_null_is_centred_and_p_is_uniformish_under_independence():
    """Independent random data: the null of every arrangement averages ~0 and the p-values of
    many independent datasets are not piled up at small values."""
    rng = np.random.default_rng(0)
    ps = []
    for _ in range(200):
        r = A.within_level_test(rng.normal(size=9), rng.normal(size=9), LEVELS)
        assert abs(np.mean(r["null"])) < 0.15
        ps.append(r["p"])
    ps = np.asarray(ps)
    assert 0.02 <= np.mean(ps <= 0.05) <= 0.10
    assert 0.40 <= np.mean(ps) <= 0.60


def test_decision_rule():
    assert A.p_main_call(0.7, 0.04) == "supports"
    assert A.p_main_call(0.7, 0.06) == "unclear"
    assert A.p_main_call(0.5, 0.01) == "unclear"
    assert A.p_main_call(0.0, 0.5) == "counts against"
    ok, own_bad, ctl_bad = {"rho": 0.8, "p": 0.01}, {"rho": 0.3}, {"rho": 0.7}
    assert A.verdict(ok, {"rho": 0.6}, {"rho": 0.1}) == ("supports", [])
    assert A.verdict(ok, own_bad, {"rho": 0.1})[0] == "unclear"         # P-own required
    assert A.verdict(ok, {"rho": 0.9}, ctl_bad)[0] == "unclear"         # control withdraws
    assert A.verdict({"rho": -0.2, "p": 0.9}, {"rho": 0.9}, {"rho": 0.0})[0] == "counts against"


def test_spearman_handles_ties_with_average_ranks():
    assert A.spearman([1, 2, 2, 3], [1, 2, 2, 3]) == pytest.approx(1.0)
    assert np.isnan(A.spearman([1, 1, 1], [1, 2, 3]))


# --------------------------------------------------------------------------
# E1 on a real checkpoint
# --------------------------------------------------------------------------

def _pair():
    from scripts.analysis.modulator_engagement import runs as R
    return R.select(PAIR_KEY)[0]


def _have_checkpoint():
    try:
        p = _pair()
    except Exception:
        return False
    return os.path.isdir(os.path.join(p.run_dirs["modulated"], "models", str(STEP)))


needs_ckpt = pytest.mark.skipif(not _have_checkpoint(), reason="replication checkpoint not on disk")


@pytest.mark.integration
@needs_ckpt
def test_identity_condition_reproduces_the_plain_rollout_exactly():
    """The tool's identity condition (manipulation 'add 0') must equal, step for step, both the
    shadow pass and an independent plain rollout (nmn.replay's scan) of the same episodes in the
    same unhurt no-animal test scene: same actions, same per-unit gains and offsets, bit for bit.
    It must also reproduce the dwell sweep's recorded agent positions (the outcomes' episodes)."""
    import dataclasses
    from scripts.analysis.modulator_engagement import engagement as E, runs as R
    from scripts.analysis.nmn import replay
    om, MP = E._om()
    p = _pair()
    probe, n_ep, out_dir, labels = R.spec_scene(p)
    path, _, w00, bm = E._world(probe, "avoid_none_inj00")
    seeds = E._seeds(bm, n_ep, path)
    agent = replay.load_agent(os.path.join(p.run_dirs["modulated"], "models"), STEP)
    ident = MP.from_spec({"manipulations": [{"name": "f", "sensor": E.FELT, "element": 0, "op": "add",
                                             "values": [0.0], "steps": [0, None]}]},
                         agent.obs_breakdown, int(w00.max_steps))
    r = om.run_checkpoint(agent, w00, seeds, ident, "sustained", per_unit=True)
    o, N = r["out"], len(seeds)
    # both conditions are identity: acting == shadow everywhere, |delta| exactly zero
    assert (o["action"] == o["shadow_action"]).all()
    for s in E.SITES:
        assert float(np.abs(o[f"absdgain_{s}"]).max()) == 0.0
        assert float(np.abs(o[f"absdoffset_{s}"]).max()) == 0.0
    # independent plain rollout of the same seeds in the same world. Same batch size (the tool
    # tiles conditions x episodes = 2N rows): a different batch size compiles a different XLA
    # program whose float32 rounding differs by ~1e-7, which is not what this test is about.
    plain = replay.rollout(dataclasses.replace(agent, env_params=w00), seeds + seeds)
    T = plain["gamma"]["rnn"].shape[0]
    assert (o["action"][:T] == plain["action"]).all()
    assert (r["T"] == plain["lengths"]).all()
    for s in E.SITES:
        np.testing.assert_array_equal(o[f"ugain_{s}"][:T], plain["gamma"][s])
        np.testing.assert_array_equal(o[f"uoffset_{s}"][:T], plain["beta"][s])
    # and the dwell sweep's recordings of these episodes (fatal inside on any mismatch)
    sys.path.insert(0, os.path.join(ROOT, "scripts", "behavior_measures"))
    from avoidance_stats_heatmap import episode_measures
    scratch = os.path.join(ROOT, out_dir, "_scratch", labels["modulated"], "avoid_none_inj00")
    if os.path.isdir(os.path.join(scratch, str(STEP))):
        om._parity(scratch, STEP, seeds, r["states0_np"], o, r["T"], N, episode_measures)


@pytest.mark.integration
@needs_ckpt
def test_e1_is_zero_for_a_modulator_that_cannot_see_felt_injury():
    """Zero the felt-injury row of the modulator GRU's input kernel: the modulator then ignores
    felt injury exactly, so E1 (gain and offset, every site, constant and trace variants) must be
    ~0 even though the TASK network still sees the injury and the acting agent behaves
    differently. The unedited checkpoint is the positive control: its E1 must be clearly > 0."""
    import jax.numpy as jnp
    from scripts.analysis.modulator_engagement import engagement as E
    from scripts.analysis.nmn import replay
    from scripts.analysis.obs_manipulation import manip as MP
    p = _pair()
    models = os.path.join(p.run_dirs["modulated"], "models")
    blind = replay.load_agent(models, STEP)
    idx = MP.sensor_offsets(blind.obs_breakdown)[E.FELT][0]
    assert blind.model._mod_input_is_all                      # modulator input = raw observation
    k = blind.model.modulator.gru.dense_i.kernel
    k.value = k.value.at[idx, :].set(0.0)
    assert float(jnp.abs(blind.model.modulator.gru.dense_i.kernel.value[idx]).max()) == 0.0

    row = E.e1_checkpoint(p, STEP, agent=blind, check_sweep=False)
    for pre in ("e1g", "e1b", "e1g_trace", "e1b_trace"):
        for s in (*E.SITES, "mean4"):
            assert row[f"{pre}_{s}"] < 1e-6, (pre, s, row[f"{pre}_{s}"])
    assert row["bush_const"] != row["bush_nat00"]             # the task network did see it

    live = E.e1_checkpoint(p, STEP)                           # positive control, sweep-checked
    assert live["e1g_mean4"] > 1e-2 and live["e1b_mean4"] > 1e-2
    assert live["sweep_check_00"] == "match" and live["sweep_check_70"] == "match"
