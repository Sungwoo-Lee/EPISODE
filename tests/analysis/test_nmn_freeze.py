"""Hand-computable checks for `scripts/analysis/nmn/freeze.py` (method 3).

Plain-language context: method 3 replaces the neuromodulator's output with its own
per-unit average and asks whether behaviour changes. It does that by editing three
of the modulator's weight tensors rather than by changing any model code — zero the
head's kernel and its bias, and put the target average in the head's per-unit
baseline. If that edit is not EXACTLY a constant, every number method 3 produces is
wrong in a way that would look like a small real effect rather than a bug.

So the first four tests below check the edit against an independent numpy
implementation of the modulator's own head formula, including the case the shortcut
could plausibly get wrong: `grouping_size > 1`, where the head's bias is per-GROUP
while the target is per-UNIT, so routing the target through the bias would be
impossible and routing it through the baseline is the only correct choice. None of
the runs in this study use grouping, which is exactly why it needs a test — nothing
else would catch it.

The rest check the paired-difference summary. Its failure mode is quiet: an
unpaired comparison (or a difference taken the wrong way round) still returns
plausible numbers, and "fraction of episodes that changed" silently becomes
meaningless if ties are counted as changes.
"""
import math
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from scripts.analysis.nmn import freeze   # noqa: E402


# --------------------------------------------------------------------------
# The head formula, and the edit that makes it constant
# --------------------------------------------------------------------------

def test_head_signal_reproduces_the_models_own_formula_by_hand():
    """One modulator state, two units, no grouping.

        h      = [1, 2]
        kernel = [[10, 100],          h @ kernel = [1*10 + 2*3, 1*100 + 2*4]
                  [ 3,   4]]                     = [16, 108]
        bias   = [1, 2]               + bias      = [17, 110]
        base   = [0.5, -0.5]          + baseline  = [17.5, 109.5]
    """
    sig = freeze.head_signal(
        kernel=np.array([[10.0, 100.0], [3.0, 4.0]]),
        bias=np.array([1.0, 2.0]), baseline=np.array([0.5, -0.5]),
        h=np.array([1.0, 2.0]), grouping_size=1, width=2)
    assert np.allclose(sig, [17.5, 109.5])


def test_head_signal_repeats_each_group_across_its_units_when_grouping():
    """grouping_size 2 over a 3-wide layer: one group value drives units 0 and 1.

        h @ kernel + bias = [5, 9]  ->  repeated  [5, 5, 9]  ->  + baseline [1, 2, 3]
                                                              =  [6, 7, 12]
    """
    sig = freeze.head_signal(
        kernel=np.array([[5.0, 9.0]]), bias=np.array([0.0, 0.0]),
        baseline=np.array([1.0, 2.0, 3.0]), h=np.array([1.0]),
        grouping_size=2, width=3)
    assert np.allclose(sig, [6.0, 7.0, 12.0])


def test_frozen_params_make_the_head_emit_the_target_for_every_input():
    """The load-bearing claim, checked over many random states rather than one."""
    rng = np.random.default_rng(0)
    target = np.array([0.4, -1.7, 3.0, 0.0])
    k, b, base = freeze.frozen_head_params(target, kernel_shape=(6, 4), bias_shape=(4,))
    # Model parameters are float32, so the stored constant is the target rounded to
    # float32. What method 3 needs is that the head emits ONE value at every step;
    # that it is float32 is a property of the network, not of the freeze.
    expected = target.astype(np.float32)
    assert np.allclose(expected, target, rtol=0, atol=1e-6)
    for _ in range(64):
        h = rng.uniform(-1.0, 1.0, size=6)
        sig = freeze.head_signal(k, b, base, h, grouping_size=1, width=4)
        assert np.array_equal(sig, expected), "the frozen head is not exactly constant"


def test_a_float32_target_is_stored_and_emitted_with_no_rounding_at_all():
    """The real pipeline's targets come from float32 rollout arrays, so this is the
    case that actually runs: no rounding anywhere in the chain."""
    target = np.array([0.5, -1.25, 3.0, 0.0], dtype=np.float32)   # exact in binary
    k, b, base = freeze.frozen_head_params(target, (6, 4), (4,))
    assert np.array_equal(base, target)
    sig = freeze.head_signal(k, b, base, np.full(6, 0.7), 1, 4)
    assert np.array_equal(sig, target)


def test_frozen_params_are_exact_under_grouping_where_a_per_group_bias_could_not_be():
    """A per-unit target cannot be expressed through the per-GROUP bias at all. The
    edit routes it through the per-unit baseline, so it must still be exact here —
    and no run in this study uses grouping, so nothing but this test would catch a
    version that used the bias instead."""
    rng = np.random.default_rng(1)
    target = np.array([0.5, -0.5, 2.0, -2.0], dtype=np.float32)  # differs WITHIN a group
    k, b, base = freeze.frozen_head_params(target, kernel_shape=(3, 2), bias_shape=(2,))
    for _ in range(32):
        h = rng.uniform(-1.0, 1.0, size=3)
        sig = freeze.head_signal(k, b, base, h, grouping_size=2, width=4)
        assert np.array_equal(sig, target)


def test_the_frozen_target_must_be_per_unit_not_a_scalar():
    with pytest.raises(ValueError, match="per-unit"):
        freeze.frozen_head_params(np.float64(0.5), (4, 4), (4,))
    with pytest.raises(ValueError, match="per-unit"):
        freeze.frozen_head_params(np.zeros((2, 4)), (4, 4), (4,))


def test_the_unedited_head_is_not_constant_so_the_test_above_means_something():
    """A control on the controls: if `head_signal` returned a constant regardless,
    every test above would pass against a broken freeze."""
    sig1 = freeze.head_signal(np.array([[1.0, 2.0]]), np.zeros(2), np.zeros(2),
                              np.array([1.0]), 1, 2)
    sig2 = freeze.head_signal(np.array([[1.0, 2.0]]), np.zeros(2), np.zeros(2),
                              np.array([-1.0]), 1, 2)
    assert not np.array_equal(sig1, sig2)


# --------------------------------------------------------------------------
# Per-unit means over the alive mask
# --------------------------------------------------------------------------

def test_per_unit_means_are_per_unit_and_ignore_dead_timesteps():
    """Three timesteps, one episode, two units; the third timestep is after death
    and carries a value that would move both unit means a long way if it leaked."""
    gamma = np.array([[[1.0, 5.0]], [[3.0, 7.0]], [[999.0, 999.0]]])
    beta = np.array([[[0.0, -2.0]], [[2.0, -4.0]], [[999.0, 999.0]]])
    valid = np.array([[True], [True], [False]])
    means = freeze.per_unit_time_means(
        {"gamma": {"actor": gamma}, "beta": {"actor": beta}, "valid": valid})
    assert np.allclose(means["actor"]["gamma"], [2.0, 6.0])
    assert np.allclose(means["actor"]["beta"], [1.0, -3.0])
    assert means["actor"]["gamma"].shape == (2,), "the mean must stay per-unit"


# --------------------------------------------------------------------------
# The paired difference
# --------------------------------------------------------------------------

def test_paired_differences_are_frozen_minus_live_and_counted_by_episode():
    """Five paired episodes:

        live   = [10, 20, 30, 40, 50]
        frozen = [10, 18, 33, 40, 45]
        diff   = [ 0, -2,  3,  0, -5]     mean -0.8, median 0
        changed 3 of 5, worse 2, better 1
    """
    out = freeze.paired_differences([10, 20, 30, 40, 50], [10, 18, 33, 40, 45])
    assert out["mean_diff"] == pytest.approx(-0.8)
    assert out["median_diff"] == pytest.approx(0.0)
    assert out["min_diff"] == -5 and out["max_diff"] == 3
    assert out["frac_episodes_changed"] == pytest.approx(3 / 5)
    assert out["frac_episodes_worse"] == pytest.approx(2 / 5)
    assert out["frac_episodes_better"] == pytest.approx(1 / 5)
    assert out["mean_live"] == pytest.approx(30.0)
    assert out["mean_frozen"] == pytest.approx(29.2)


def test_an_exactly_identical_replay_reports_no_change_at_all():
    """The result method 3 must be able to report cleanly: freezing changed nothing.
    Every 'changed' counter must be zero, and the sign test undefined rather than
    silently significant."""
    out = freeze.paired_differences([10, 20, 30], [10, 20, 30])
    assert out["frac_episodes_changed"] == 0.0
    assert out["mean_diff"] == 0.0
    assert math.isnan(out["sign_test_p"])


def test_ties_are_excluded_from_the_sign_test_not_counted_as_agreement():
    """Two episodes change, both for the better, among a hundred ties. The sign test
    must see n = 2 (p = 0.5), not n = 102."""
    live = [10] * 100
    frozen = [10] * 98 + [11, 12]
    out = freeze.paired_differences(live, frozen)
    assert out["n_changed"] == 2 and out["n_better"] == 2
    assert out["sign_test_p"] == pytest.approx(0.5)


def test_unpaired_inputs_are_refused_rather_than_broadcast():
    with pytest.raises(ValueError, match="unpaired inputs"):
        freeze.paired_differences([1, 2, 3], [1, 2])


def test_the_four_conditions_are_named_and_include_both_single_freezes():
    """Perez's asymmetry is the whole reason this method exists; a version that only
    froze both together would silently answer a different question."""
    assert freeze.CONDITIONS == ("live", "freeze_gain", "freeze_offset", "freeze_both")
