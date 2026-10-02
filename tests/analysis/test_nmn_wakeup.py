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
    return wakeup.t_cross(X[:len(m)], m, mode="fraction_of_rise", anchored=True,
                          label="synthetic / fixture", **{**FIX, **kw})


def lit(m, **kw):
    return wakeup.t_cross(X[:len(m)], m, mode="fraction_of_final", anchored=True,
                          label="synthetic / fixture", **{**FIX, **kw})


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

    FIXTURE NOTE: for THIS curve, with the registered noise_k = 3, the guard fires before the
    "no sustained crossing" branch (the final jump is inside the noise window, so sigma_delta
    ~ 0.25 and noise_k * sigma_delta ~ 0.75 > |m_final - m0| ~ 1/3); asserted below. That is a
    property of this curve, NOT of the branch: the branch is reachable under the registered
    constants (see test_plateau_no_sustained_crossing_registered_constants). Here it is also
    exercised with noise_k = 1 (a fixture value), where the guard passes and only the last
    point crosses."""
    m = np.zeros(51) + noise(8)
    m[50] = 1.0
    g = rise(m)                                  # plan fixture constants: the guard wins
    assert math.isnan(g.t) and g.reason == wakeup.R_NOISE
    r, l = rise(m, noise_k=1), lit(m, noise_k=1)
    assert r.guard_margin > 1
    assert math.isnan(r.t) and r.reason == wakeup.R_NO_SUSTAIN
    assert math.isnan(l.t) and l.reason == wakeup.R_NO_SUSTAIN


def _level_then_jump(n):
    """Survival that climbs in a straight line to 0.85 of its net rise, then jumps once at the
    last checkpoint (the pre-jump level c solves c = 0.85 x (m_final - m0))."""
    c = 0.6
    for _ in range(200):
        m = np.append(c * np.arange(n - 1) / (n - 2), 1.0)
        c = 0.85 * (np.mean(m[-3:]) - m[0])
    return np.append(c * np.arange(n - 1) / (n - 2), 1.0)


@pytest.mark.parametrize("n,margin", [(50, 2.96), (15, 1.66)])
def test_plateau_no_sustained_crossing_registered_constants(n, margin):
    """Code review L1 / designer R.2: under the REGISTERED constants and plateau_f = 0.9, a
    survival curve that reaches 0.85 of its rise and jumps at the last checkpoint gives NaN with
    reason "no sustained crossing", the guard passing (margin 2.96 on the 50-checkpoint
    level-05 grid, 1.66 on the 15-checkpoint May grid). No point before the jump reaches 90 %
    of the rise, and the jump itself is a single point, so `sustain = 2` is never met."""
    m = _level_then_jump(n)
    x = np.arange(1, n + 1, dtype=float) * 200000.0            # unanchored, like survival
    r = wakeup.t_cross(x, m, mode="fraction_of_rise", anchored=False, label="synthetic / plateau",
                       **{**FIX, "f": 0.9})
    assert math.isnan(r.t) and r.reason == wakeup.R_NO_SUSTAIN
    assert r.guard_margin > 1 and r.guard_margin == pytest.approx(margin, abs=0.02)
    assert np.all(m[:-1] < 0.9 * (r.m_final - r.m0))


def test_nonfinite_point_raises_naming_run_measure_checkpoint():
    """Designer R.2 item 2: a curve with one NaN point RAISES (a data defect; returning NaN
    would silently drop the run from n_def and move the sign test's k*). The message names the
    run and measure (label) and the checkpoint (its position on the run's one scale)."""
    m = logistic(0.0, 1.0) + noise(1)
    m[17] = float("nan")
    with pytest.raises(ValueError, match=r"w0000 / rho.*checkpoint 17 \(x = 17\)"):
        wakeup.t_cross(X, m, mode="fraction_of_rise", anchored=True, label="w0000 / rho", **FIX)
    xu = np.arange(1, 51, dtype=float)                       # unanchored: index 16 = checkpoint 17
    with pytest.raises(ValueError, match=r"checkpoint 17 \(x = 17\)"):
        wakeup.t_cross(xu, m[1:], mode="fraction_of_final", anchored=False, label="w / plateau", **FIX)


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
    r = wakeup.t_cross(X[1:], m[1:], mode="fraction_of_rise", anchored=False, label="u", **FIX)
    assert r.anchored is False and 19 <= r.t <= 21


def test_guard_margin_reported():
    m = logistic(0.0, 1.0) + noise(1)
    r = rise(m)
    assert r.guard_margin == pytest.approx(abs(r.m_final - r.m0) / (3 * r.sigma_delta))


# -------------------------------------------------------------------------------------- lag
# The run's one scale: checkpoint i of the manifest list is position i (1-based), step 0 is 0.
# A level-05-like grid whose spacings jitter: 200,036 and 199,992 episodes, alternating.
JITTER = np.cumsum([200019.0] + [200036.0 if i % 2 == 0 else 199992.0 for i in range(49)])


def _lag(tw, tp, grid=JITTER, k=1):
    r = wakeup.lag(tw, tp, grid.tolist(), k)
    return r["lag"], r["reading"]


def test_position_scale():
    g = JITTER.tolist()
    assert wakeup.position(0.0, g) == 0 and wakeup.position(g[0], g) == 1
    assert wakeup.position(g[12], g) == 13
    with pytest.raises(ValueError):
        wakeup.position(g[12] + 1, g)


LAG_ROWS = [
    {"case": "one checkpoint late on a wide interval",
     "why": "wake one checkpoint after the plateau across a 200,036-episode interval: one "
            "position apart -> coincident (an episode band of one 'interval' could read late)",
     "input": (JITTER[13], JITTER[12]), "expect": (200036.0, "coincident")},
    {"case": "one checkpoint early on a narrow interval",
     "why": "wake one checkpoint before, across 199,992 episodes -> coincident",
     "input": (JITTER[13], JITTER[14]), "expect": (-199992.0, "coincident")},
    {"case": "two checkpoints late", "why": "two positions apart -> late; lag in episodes reported",
     "input": (JITTER[14], JITTER[12]), "expect": (JITTER[14] - JITTER[12], "late")},
    {"case": "two checkpoints early", "input": (JITTER[10], JITTER[12]),
     "expect": (JITTER[10] - JITTER[12], "early")},
    {"case": "same checkpoint", "input": (JITTER[12], JITTER[12]), "expect": (0.0, "coincident")},
    {"case": "wake at step 0", "why": "the untrained anchor is position 0; plateau at checkpoint 1 "
            "-> one position apart", "input": (0.0, JITTER[0]), "expect": (-JITTER[0], "coincident")},
]


@pytest.mark.parametrize("row", LAG_ROWS, ids=lambda r: r["case"])
def test_lag_on_checkpoint_positions(row):
    lg, rd = _lag(*row["input"])
    assert lg == pytest.approx(row["expect"][0]) and rd == row["expect"][1]


def test_lag_nan_and_off_grid():
    r = wakeup.lag(float("nan"), JITTER[3], JITTER.tolist(), 1)
    assert math.isnan(r["lag"]) and r["reading"] is None
    with pytest.raises(ValueError):
        wakeup.lag(JITTER[3] + 5, JITTER[3], JITTER.tolist(), 1)


def _crossing_at(k, anchored):
    """A step curve on the JITTER grid that first reaches half its rise at checkpoint k."""
    x = np.concatenate([[0.0], JITTER]) if anchored else JITTER
    pos = np.arange(len(x)) if anchored else np.arange(1, len(x) + 1)
    m = np.where(pos >= k, 1.0, 0.0) + np.random.default_rng(k).normal(0, 0.01, len(x))
    return wakeup.t_cross(x, m, mode="fraction_of_rise", anchored=anchored, label="synthetic", **FIX)


ANCHOR_ROWS = [
    {"case": "anchored wake and unanchored plateau at the same checkpoint",
     "why": "designer R.2 condition: the anchored curve's array index is 20, the plateau's is 19; "
            "both are checkpoint 20 on the one scale -> coincident, lag 0",
     "input": (20, 20), "expect": (0, "coincident")},
    {"case": "anchored wake one checkpoint after an unanchored plateau",
     "why": "checkpoints 21 and 20 -> coincident; raw array indices (21 vs 19) would read late",
     "input": (21, 20), "expect": (1, "coincident")},
    {"case": "anchored wake two checkpoints after an unanchored plateau",
     "why": "checkpoints 22 and 20 -> late", "input": (22, 20), "expect": (2, "late")},
]


@pytest.mark.parametrize("row", ANCHOR_ROWS, ids=lambda r: r["case"])
def test_lag_anchored_vs_unanchored(row):
    kw, kp = row["input"]
    w, p = _crossing_at(kw, True), _crossing_at(kp, False)
    assert (w.index, p.index) == (kw, kp - 1)          # raw indices differ by one scale step
    r = wakeup.lag(w.t, p.t, JITTER.tolist(), 1)
    assert (r["delta_positions"], r["reading"]) == row["expect"]
    assert r["lag"] == pytest.approx(w.t - p.t)
