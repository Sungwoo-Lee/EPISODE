"""Tests for scripts/analysis/nmn/representation.py (plan File Changes §6, Checkpoint 3.1).

Synthetic data only; the sizes and alphas below are test fixture values.
"""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from scripts.analysis.nmn import representation as rep  # noqa: E402

RNG = np.random.default_rng(0)
ALPHAS = [1e-3, 1e-1, 1.0, 10.0]


def _layer(n=2000, d=16, seed=0):
    return np.random.default_rng(seed).normal(size=(n, d))


# ---------------------------------------------------------------------------------- CKA
def test_cka_self_is_one():
    X = _layer()
    assert np.isclose(rep.linear_cka(X, X), 1.0, atol=1e-12)


def test_cka_invariant_to_rotation_and_isotropic_scale():
    X = _layer()
    Q, _ = np.linalg.qr(RNG.normal(size=(16, 16)))
    assert np.isclose(rep.linear_cka(X, 3.7 * X @ Q), 1.0, atol=1e-10)


def test_cka_drops_under_per_unit_rescale():
    X = _layer()
    s = np.exp(np.linspace(-3, 3, 16))
    assert rep.linear_cka(X, X * s) < 0.9


def test_cka_weights_equal_duplication():
    X, Y = _layer(200, 5, 1), _layer(200, 4, 2)
    w = np.random.default_rng(3).integers(0, 3, 200)
    rows = np.repeat(np.arange(200), w)
    assert np.isclose(rep.linear_cka(X, Y, w), rep.linear_cka(X[rows], Y[rows]), atol=1e-12)


# ------------------------------------------------------------------------- predictivity
def _groups(n, per=10):
    return np.repeat(np.arange(n // per), per)


def _pred_r2(X, Y):
    g = _groups(len(X))
    sp = rep.episode_split(g, 1, 0.2, 0)
    m = rep.fit_maps(X, Y, g, sp, alphas=ALPHAS, inner_folds=3)[0]
    return rep.heldout_r2(m, X, Y, sp[0].test)


def test_predictivity_per_unit_rescale_and_invertible_map():
    X = _layer()
    assert _pred_r2(X, X * np.exp(np.linspace(-3, 3, 16))) > 0.999
    A = RNG.normal(size=(16, 16)) + 4 * np.eye(16)
    assert _pred_r2(X, X @ A) > 0.999


def test_predictivity_independent_noise_is_near_zero():
    assert abs(_pred_r2(_layer(seed=1), _layer(seed=2))) < 0.05


# ---------------------------------------------------------------------------- leakage
def test_leakage_row_split_vs_episode_split():
    """A feature encoding the episode identity + a per-episode constant target: a row-level
    split scores high, the episode-grouped split ~0."""
    n_ep, per = 300, 10
    g = np.repeat(np.arange(n_ep), per)
    target = np.random.default_rng(4).normal(size=n_ep)[g]
    X = np.eye(n_ep)[g]                                  # one-hot episode identity
    rows = np.random.default_rng(5).permutation(len(g))
    tr, te = rows[:2400], rows[2400:]
    m = rep.fit_ridge(X[tr], target[tr], g[tr], alphas=[1e-3], inner_folds=3)
    assert rep.heldout_r2(m, X, target, te) > 0.9
    sp = rep.episode_split(g, 1, 0.2, 0)
    m2 = rep.fit_maps(X, target, g, sp, alphas=[1e-3], inner_folds=3)[0]
    assert rep.heldout_r2(m2, X, target, sp[0].test) < 0.05


def test_episode_split_disjoint_and_repeatable():
    g = _groups(1000)
    a, b = rep.episode_split(g, 5, 0.2, 7), rep.episode_split(g, 5, 0.2, 7)
    for s, s2 in zip(a, b):
        assert not np.intersect1d(g[s.train], g[s.test]).size
        assert np.array_equal(s.test, s2.test)


# ------------------------------------------------------------------------------ clock
def _clock_setup(n_ep=400, T=30):
    g = np.repeat(np.arange(n_ep), T)
    t = np.tile(np.arange(T), n_ep)
    sp = rep.episode_split(g, 1, 0.2, 0)[0]
    return g, t, sp


def test_clock_a_nonlinear_function_of_t():
    g, t, sp = _clock_setup()
    y = np.sin(t / 3.0) ** 2 + 0.1 * t
    cm = rep.clock_baseline(t, y, sp.train)
    assert rep.clock_r2(cm, t, y, rep.clock_mask(cm, t, sp.test)) > 0.999


def test_clock_b_one_hot_t_layer_has_no_excess():
    g, t, sp = _clock_setup()
    y = np.cos(t / 4.0) + np.random.default_rng(6).normal(0, 0.3, len(t))
    cm = rep.clock_baseline(t, y, sp.train)
    rows = rep.clock_mask(cm, t, sp.test)
    X = np.eye(30)[t]
    m = rep.fit_ridge(X[sp.train], y[sp.train], g[sp.train], alphas=[1e-6], inner_folds=3)
    excess = rep.heldout_r2(m, X, y, rows) - rep.clock_r2(cm, t, y, rows)
    assert abs(excess) < 0.01


def test_clock_c_target_plus_noise_beats_clock():
    g, t, sp = _clock_setup()
    y = np.random.default_rng(7).normal(size=len(t))
    X = (y + np.random.default_rng(8).normal(0, 0.1, len(t)))[:, None]
    cm = rep.clock_baseline(t, y, sp.train)
    rows = rep.clock_mask(cm, t, sp.test)
    m = rep.fit_ridge(X[sp.train], y[sp.train], g[sp.train], alphas=ALPHAS, inner_folds=3)
    rc = rep.clock_r2(cm, t, y, rows)
    assert abs(rc) < 0.05
    assert rep.heldout_r2(m, X, y, rows) - rc > 0.9


def test_clock_d_unseen_time_step_is_masked():
    g, t, sp = _clock_setup()
    t = t.copy()
    t[sp.test[:5]] = 999                                # never in the training fold
    y = t.astype(float)
    cm = rep.clock_baseline(t, y, sp.train)
    rows = rep.clock_mask(cm, t, sp.test)
    assert len(rows) == len(sp.test) - 5 and not np.isin(sp.test[:5], rows).any()
    with pytest.raises(ValueError):
        rep.clock_r2(cm, t, y, sp.test)


# -------------------------------------------------------------------------- bootstrap
def test_maps_fitted_once_per_repeat():
    calls = []

    def counting(X, Y, g, *, alphas, inner_folds):
        calls.append(len(X))
        return rep.fit_ridge(X, Y, g, alphas=alphas, inner_folds=inner_folds)

    X = _layer()
    g = _groups(len(X))
    sp = rep.episode_split(g, 5, 0.2, 0)
    maps = rep.fit_maps(X, X, g, sp, alphas=ALPHAS, inner_folds=3, fitter=counting)
    draws = rep.joint_group_bootstrap(g, sp, 50, 0)
    for s, m, d in zip(sp, maps, draws):
        for pos in d:
            rep.heldout_r2(m, X, X, s.test, rep.draw_weights(g, s.test, s.test_groups, pos))
    assert len(calls) == 5


def test_bootstrap_is_paired_across_agents():
    """Two identical agents: the draw-wise difference is exactly 0."""
    X, Y = _layer(seed=1), _layer(seed=2) @ RNG.normal(size=(16, 16))
    g = _groups(len(X))
    sp = rep.episode_split(g, 2, 0.2, 0)
    ma = rep.fit_maps(X, Y, g, sp, alphas=ALPHAS, inner_folds=3)
    mb = rep.fit_maps(X.copy(), Y.copy(), g, sp, alphas=ALPHAS, inner_folds=3)
    for s, a, b, d in zip(sp, ma, mb, rep.joint_group_bootstrap(g, sp, 20, 1)):
        for pos in d:
            w = rep.draw_weights(g, s.test, s.test_groups, pos)
            assert rep.heldout_r2(a, X, Y, s.test, w) - rep.heldout_r2(b, X, Y, s.test, w) == 0.0


def test_bootstrap_resamples_groups_not_rows():
    """Two stores sharing episode_seed values: a seed's rows from both stores move together."""
    seeds = np.arange(100)
    g = np.concatenate([np.repeat(seeds, 5), np.repeat(seeds, 7)])      # store A, store B
    ug, pos = rep.whole_probe_bootstrap(g, 30, 0)
    rows = np.arange(len(g))
    for p in pos:
        w = rep.draw_weights(g, rows, ug, p)
        for s in seeds[:10]:
            vals = np.unique(w[g == s])
            assert len(vals) == 1                        # every row of the seed, both stores
        assert w.sum() == 100 * 12                       # 100 groups drawn, 12 rows each
