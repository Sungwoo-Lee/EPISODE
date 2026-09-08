"""Hand-computable checks for `scripts/analysis/nmn/mod_distribution.py` (method 2).

Plain-language context: the module under test reduces a table of gains and offsets
-- one row per timestep the agent was alive, one column per hidden unit -- to a set
of fractions and a variance split. Two things in it can go quietly wrong and produce
a plausible number rather than a crash.

The first is the **alive mask**. Episodes have different lengths, so the raw array
is padded with whatever the environment produced after the agent died. Pooling those
rows in would mix a dead agent's readings into the distribution. Every statistic here
must be blind to them, and the test proves it by filling the masked-out rows with
values chosen to wreck every statistic if they leak.

The second is the **variance split**. `Var over (unit, time)` equals `Var across
units of the per-unit time-mean` plus `mean over units of the per-unit time-variance`
-- but only when every unit is observed at the same timesteps. Get the axis wrong and
the two terms still look like variances and still sum to something; they just do not
sum to the total. The module asserts the identity closes; this file checks the
assertion fires, and pins each term to a number worked out on paper.

The worked example (2 timesteps, 1 episode, 2 units):

    gamma = [[ 1, -1 ],        values pooled: 1, -1, 3, 0     mean 0.75
             [ 3,  0 ]]

    per-unit time means: unit0 (1+3)/2 = 2      unit1 (-1+0)/2 = -0.5
    per-unit time vars : unit0 1                unit1 0.25

    across units = Var([2, -0.5])              = 1.5625
    across time  = mean([1, 0.25])             = 0.625
    total        = Var([1, -1, 3, 0])          = 2.1875 = 1.5625 + 0.625  OK
    rho          = 0.625 / 2.1875              = 0.285714...
"""
import math
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from scripts.analysis.nmn import mod_distribution as md   # noqa: E402


GAMMA = np.array([[[1.0, -1.0]], [[3.0, 0.0]]])          # (T=2, ep=1, units=2)
BETA = np.array([[[-2.0, 0.5]], [[-4.0, -1.0]]])
VALID = np.ones((2, 1), dtype=bool)


def _padded(arr, pad_value):
    """The same signal with a third, DEAD timestep carrying wrecking values."""
    pad = np.full((1,) + arr.shape[1:], pad_value)
    return np.concatenate([arr, pad], axis=0)


PADDED_VALID = np.array([[True], [True], [False]])


# --------------------------------------------------------------------------
# The variance split
# --------------------------------------------------------------------------

def test_variance_split_matches_the_hand_arithmetic():
    out = md.variance_split(GAMMA, VALID)
    assert out["var_across_units"] == pytest.approx(1.5625)
    assert out["var_across_time"] == pytest.approx(0.625)
    assert out["var_total"] == pytest.approx(2.1875)
    assert out["rho"] == pytest.approx(0.625 / 2.1875)


def test_variance_split_closes_and_says_so_when_it_cannot():
    """The identity is the module's own guard. Feed it a mask that differs between
    units -- impossible through `replay.rollout`, which is exactly why the guard has
    to be tested directly -- and it must refuse rather than return two numbers that
    do not add up."""
    with pytest.raises(ValueError, match="expected \\(T, n_ep, units\\)"):
        md.variance_split(np.zeros((2, 2)), np.ones((2, 2), dtype=bool))
    with pytest.raises(ValueError, match="valid has shape"):
        md.variance_split(GAMMA, np.ones((3, 1), dtype=bool))


def test_variance_split_ignores_timesteps_after_the_agent_died():
    """A dead-timestep gain of 1000 would raise every variance term by orders of
    magnitude if the mask leaked."""
    out = md.variance_split(_padded(GAMMA, 1000.0), PADDED_VALID)
    assert out["var_across_units"] == pytest.approx(1.5625)
    assert out["var_across_time"] == pytest.approx(0.625)
    assert out["rho"] == pytest.approx(0.625 / 2.1875)


def test_rho_is_zero_for_a_perfectly_static_modulator():
    """The case the method exists to detect: per-unit gains that never change with
    context. All the spread is across units, none across time."""
    static = np.stack([np.array([[0.2, -1.7]])] * 5)      # (5, 1, 2), constant in t
    out = md.variance_split(static, np.ones((5, 1), dtype=bool))
    assert out["var_across_time"] == pytest.approx(0.0, abs=1e-12)
    assert out["rho"] == pytest.approx(0.0, abs=1e-12)
    assert out["var_across_units"] == pytest.approx(out["var_total"])


def test_rho_is_one_when_every_unit_moves_together_around_a_shared_mean():
    """The opposite extreme: no per-unit offset at all, everything is context."""
    moving = np.array([[[-1.0, -1.0]], [[1.0, 1.0]]])
    out = md.variance_split(moving, VALID)
    assert out["var_across_units"] == pytest.approx(0.0, abs=1e-12)
    assert out["rho"] == pytest.approx(1.0)


# --------------------------------------------------------------------------
# Sign and zero structure
# --------------------------------------------------------------------------

def test_sign_fractions_count_the_pooled_values_not_the_units():
    out = md.summarise_site(GAMMA, BETA, VALID)
    # gains pooled: 1, -1, 3, 0  ->  below 1: {-1, 0} = 2/4 ; negative: {-1} = 1/4
    assert out["frac_gamma_lt1"] == pytest.approx(0.5)
    assert out["frac_gamma_negative"] == pytest.approx(0.25)
    # offsets pooled: -2, 0.5, -4, -1  ->  negative: 3/4
    assert out["frac_beta_negative"] == pytest.approx(0.75)


def test_near_zero_band_catches_a_switched_off_channel_a_mean_would_hide():
    """gain values -1 and +1 average to exactly 0 but nothing is switched off;
    a gain of 0.01 IS switched off. The two must not be confused."""
    swinging = np.array([[[-1.0]], [[1.0]]])
    off = np.array([[[0.01]], [[-0.01]]])
    zeros = np.zeros((2, 1, 1))
    assert md.summarise_site(swinging, zeros, VALID)["frac_gamma_near_zero"] == 0.0
    assert md.summarise_site(off, zeros, VALID)["frac_gamma_near_zero"] == 1.0


def test_per_unit_sign_stability_separates_flipping_from_always_negative():
    """unit0 is +1 then +3 (always positive); unit1 is -1 then 0 (never positive
    strictly, but 0 counts as non-negative, so it flips)."""
    out = md.summarise_site(GAMMA, BETA, VALID)
    assert out["frac_units_gain_always_positive"] == pytest.approx(0.5)
    assert out["frac_units_gain_always_negative"] == pytest.approx(0.0)
    assert out["frac_units_gain_sign_flips"] == pytest.approx(0.5)
    # unit means are 2 and -0.5, so exactly one unit has a negative mean gain
    assert out["frac_units_mean_gain_negative"] == pytest.approx(0.5)


def test_every_statistic_ignores_timesteps_after_the_agent_died():
    """The whole summary, not just the variance split. The padded row is chosen so
    that a leak changes EVERY fraction: a huge positive gain (raises the mean, is
    not below 1, is not negative, is not near zero) and a positive offset."""
    ref = md.summarise_site(GAMMA, BETA, VALID)
    padded = md.summarise_site(_padded(GAMMA, 1000.0), _padded(BETA, 1000.0),
                               PADDED_VALID)
    for k, v in ref.items():
        assert padded[k] == pytest.approx(v), f"statistic {k!r} leaked a dead timestep"


def test_quantiles_and_counts_are_over_live_values_only():
    out = md.summarise_site(_padded(GAMMA, 1000.0), _padded(BETA, 1000.0), PADDED_VALID)
    assert out["n_values"] == 4          # 2 live timesteps x 2 units
    assert out["n_timesteps"] == 2
    assert out["gamma_max"] == pytest.approx(3.0)
    assert out["gamma_mean"] == pytest.approx(0.75)


def test_published_comparison_points_are_the_perez_numbers():
    out = md.summarise_site(GAMMA, BETA, VALID)
    assert out["perez_gamma_negative"] == pytest.approx(0.36)
    assert out["perez_beta_negative"] == pytest.approx(0.76)


def test_variance_split_needs_more_than_one_live_timestep():
    with pytest.raises(ValueError, match="at least two valid timesteps"):
        md.variance_split(GAMMA, np.array([[True], [False]]))


def test_sign_flip_count_has_a_robust_version_that_a_single_excursion_cannot_trip():
    """Ten live timesteps, one unit. Its gain is negative on exactly one of them.

    The weak criterion calls that unit "sign-flipping" (it did take both signs). The
    robust criterion does not, because the minority sign holds 10% ... which IS above
    the 5% band, so it counts. Drop it to one step in forty and it must not.
    """
    def unit(neg_steps, total):
        g = np.ones((total, 1, 1))
        g[:neg_steps] = -1.0
        return g, np.zeros((total, 1, 1)), np.ones((total, 1), dtype=bool)

    g, b, v = unit(1, 10)                      # 10% negative -> above the 5% band
    out = md.summarise_site(g, b, v)
    assert out["frac_units_gain_sign_flips"] == pytest.approx(1.0)
    assert out["frac_units_gain_sign_flips_5pct"] == pytest.approx(1.0)

    g, b, v = unit(1, 40)                      # 2.5% negative -> below the band
    out = md.summarise_site(g, b, v)
    assert out["frac_units_gain_sign_flips"] == pytest.approx(1.0), \
        "the weak criterion should still fire -- that is the point of having both"
    assert out["frac_units_gain_sign_flips_5pct"] == pytest.approx(0.0)
    assert out["frac_units_gain_negative_share_mean"] == pytest.approx(0.025)


def test_a_unit_that_never_crosses_zero_counts_under_neither_criterion():
    g = np.array([[[0.2]], [[0.9]], [[1.4]]])
    b = np.zeros((3, 1, 1))
    v = np.ones((3, 1), dtype=bool)
    out = md.summarise_site(g, b, v)
    assert out["frac_units_gain_always_positive"] == pytest.approx(1.0)
    assert out["frac_units_gain_sign_flips"] == pytest.approx(0.0)
    assert out["frac_units_gain_sign_flips_5pct"] == pytest.approx(0.0)


def test_robust_sign_flip_band_is_two_sided():
    """A unit that is negative 98% of the time is not "two-signed" any more than one
    that is positive 98% of the time -- its 2% of positive steps is noise around a
    settled negative gain. The band must be applied at BOTH ends, so the criterion
    means "spends a real share of its time on each side" rather than "is negative
    sometimes".
    """
    total = 50
    g = -np.ones((total, 1, 1))
    g[:1] = 1.0                                 # 2% positive, 98% negative
    b = np.zeros((total, 1, 1))
    v = np.ones((total, 1), dtype=bool)
    out = md.summarise_site(g, b, v)
    assert out["frac_units_gain_negative_share_mean"] == pytest.approx(0.98)
    assert out["frac_units_gain_sign_flips"] == pytest.approx(1.0)
    assert out["frac_units_gain_sign_flips_5pct"] == pytest.approx(0.0), \
        "a 98%-negative unit is settled, not sign-flipping"
