"""Tests for scripts/analysis/nmn/wakeup.py — the B2 crossing rule.

Every row of the tooling plan's §11 expected-output table is a test here. The constants below
are TEST FIXTURE VALUES, not read from the rules file (they happen to equal the registered
ones, which is the point of the fixture: the same reading the study will get).

Plan: docs/develop/active/neuromodulation/ALGORITHMIC_NULL_ANALYSIS_TOOLING.md, File Changes §11,
Checkpoint 4.1.
"""
import math
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from scripts.analysis.nmn import wakeup  # noqa: E402

# test fixture, not the study's rule
FIX = dict(f=0.5, sustain=2, final_k=3, noise_k=3, min_noise_points=5,
           noise_window_divisor=3, noise_window_max_fraction=0.5)
X = np.arange(51, dtype=float)          # step 0 (untrained anchor) + checkpoints 1..50
SIGMA = 0.01


def noise(seed=0, n=51):
    return np.random.default_rng(seed).normal(0.0, SIGMA, n)


def logistic(lo, hi, mid=20.0, scale=1.5, x=X):
    return lo + (hi - lo) / (1.0 + np.exp(-(x - mid) / scale))


def rise(m, **kw):
    return wakeup.t_cross(X[:len(m)], m, mode="fraction_of_rise", anchored=True, **{**FIX, **kw})


def lit(m, **kw):
    return wakeup.t_cross(X[:len(m)], m, mode="fraction_of_final", anchored=True, **{**FIX, **kw})


# ---------------------------------------------------------------- the §11 expected-output table
def test_clean_rise():
    m = logistic(0.0, 1.0) + noise(1)
    r, l = rise(m), lit(m)
    assert 19 <= r.t <= 21 and r.direction == "rising" and r.reason is None
    assert 19 <= l.t <= 21 and not l.degenerate


def test_falling_is_signed_not_zero():
    m = logistic(1.0, 0.2) + noise(2)
    r, l = rise(m), lit(m)
    assert 19 <= r.t <= 21 and r.direction == "falling"
    assert r.t != 0
    assert l.degenerate is True


def test_rise_then_return_is_nan_by_guard():
    m = np.where(X < 35, logistic(0.0, 1.0), 0.0) + noise(3)
    r, l = rise(m), lit(m)
    assert math.isnan(r.t) and r.reason == wakeup.R_NOISE
    assert l.degenerate is True or math.isnan(l.t)


def test_flat_in_noise_is_nan_by_guard():
    m = 0.5 + noise(4)
    r, l = rise(m), lit(m)
    assert math.isnan(r.t) and r.reason == wakeup.R_NOISE
    assert l.degenerate is True


def test_initial_value_trap():
    m = logistic(0.61, 1.0) + noise(5)
    r, l = rise(m), lit(m)
    assert 19 <= r.t <= 21
    assert l.t == 0 and l.degenerate is True


def test_non_monotone_spike_rejected_by_sustain():
    m = logistic(0.0, 1.0) + noise(6)
    m[8] = 0.9                                   # one checkpoint past threshold, then back
    r, l = rise(m), lit(m)
    assert 19 <= r.t <= 21
    assert 19 <= l.t <= 21


def test_too_few_points():
    m = logistic(0.0, 1.0, mid=3.0, scale=0.5, x=X[:7]) + noise(7, 7)   # 6 checkpoints + step 0
    r = rise(m)
    assert r.window_points == 6 and 6 > 0.5 * 7
    assert math.isnan(r.t) and r.reason == wakeup.R_TOO_FEW


def test_no_sustained_crossing_returns_nan_not_raise():
    """Rules T5 (872b0e04): flat 0 through checkpoint 49, then 1.0 at 50 only.

    FIXTURE NOTE (reported in the Implementation Report): with the plan's fixture noise_k = 3
    this curve does NOT reach the "no sustained crossing" branch. The final jump is inside the
    noise window, so sigma_delta ~ 0.25 and noise_k * sigma_delta ~ 0.75 > |m_final - m0| ~ 1/3:
    the guard fires first (asserted below). The branch itself is exercised with noise_k = 1
    (a fixture value), where the guard passes and only the last point crosses."""
    m = np.zeros(51) + noise(8)
    m[50] = 1.0
    g = rise(m)                                  # plan fixture constants: the guard wins
    assert math.isnan(g.t) and g.reason == wakeup.R_NOISE
    r, l = rise(m, noise_k=1), lit(m, noise_k=1)
    assert r.guard_margin > 1
    assert math.isnan(r.t) and r.reason == wakeup.R_NO_SUSTAIN
    assert math.isnan(l.t) and l.reason == wakeup.R_NO_SUSTAIN


def test_divisor_is_read():
    m = logistic(0.0, 1.0) + noise(1)
    r = rise(m, noise_window_divisor=2)
    assert r.window_points == max(math.ceil(51 / 2), 6) == 26
    assert 26 > 0.5 * 51
    assert math.isnan(r.t) and r.reason == wakeup.R_TOO_FEW
    assert not math.isnan(rise(m).t)             # divisor 3 on the same curve: defined


# ------------------------------------------------------------------------------ extra checks
def test_no_defaults():
    with pytest.raises(TypeError):
        wakeup.t_cross(X, X, mode="fraction_of_rise", anchored=True)


def test_unanchored_is_recorded():
    m = logistic(0.0, 1.0) + noise(1)
    r = wakeup.t_cross(X[1:], m[1:], mode="fraction_of_rise", anchored=False, **FIX)
    assert r.anchored is False and 19 <= r.t <= 21


def test_guard_margin_reported():
    m = logistic(0.0, 1.0) + noise(1)
    r = rise(m)
    assert r.guard_margin == pytest.approx(abs(r.m_final - r.m0) / (3 * r.sigma_delta))


# -------------------------------------------------------------------------------------- lag
def test_lag_late_early_coincident_nan():
    assert wakeup.lag(900.0, 500.0, 200.0, 1) == (400.0, "late")
    assert wakeup.lag(100.0, 500.0, 200.0, 1) == (-400.0, "early")
    assert wakeup.lag(700.0, 500.0, 200.0, 1) == (200.0, "coincident")    # exactly the edge
    assert wakeup.lag(300.0, 500.0, 200.0, 1) == (-200.0, "coincident")
    lg, rd = wakeup.lag(float("nan"), 500.0, 200.0, 1)
    assert math.isnan(lg) and rd is None
