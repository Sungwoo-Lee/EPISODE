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


def test_score_against_clock_masks_both_and_counts():
    """L3: one call scores the layer and the clock on the SAME rows (rows with no clock value
    dropped from both, with their bootstrap multiplicities) and returns how many were dropped."""
    g, t, sp = _clock_setup()
    t = t.copy()
    t[sp.test[:7]] = 999                                  # never in the training fold
    y = np.cos(t / 4.0) + np.random.default_rng(9).normal(0, 0.3, len(t))
    X = np.c_[y + np.random.default_rng(10).normal(0, 0.5, len(t)), np.eye(30)[t % 30]]
    cm = rep.clock_baseline(t, y, sp.train)
    m = rep.fit_ridge(X[sp.train], y[sp.train], g[sp.train], alphas=ALPHAS, inner_folds=3)
    w = np.random.default_rng(11).integers(0, 3, len(sp.test)).astype(float)
    r_layer, r_clock, dropped = rep.score_against_clock(m, cm, X, y, t, sp.test, w)
    keep = ~np.isin(sp.test, sp.test[:7])
    assert dropped == 7
    assert r_layer == rep.heldout_r2(m, X, y, sp.test[keep], w[keep])
    assert r_clock == rep.clock_r2(cm, t, y, sp.test[keep], w[keep])
    r_l0, r_c0, d0 = rep.score_against_clock(m, cm, X, y, t, sp.test)
    assert d0 == 7 and r_c0 == rep.clock_r2(cm, t, y, rep.clock_mask(cm, t, sp.test))


def _svd_path(Z, Yc, alphas):
    U, s, Vt = np.linalg.svd(Z, full_matrices=False)
    return [Vt.T @ ((s / (s ** 2 + a))[:, None] * (U.T @ Yc)) for a in alphas]


@pytest.mark.parametrize("collinear", [False, True])
def test_gram_ridge_path_equals_svd(collinear):
    """L6: for rows >> columns the ridge path comes from the d x d Gram matrix; it must give the
    SVD's coefficients (also with two nearly duplicate units, the ill-conditioned case)."""
    rng = np.random.default_rng(12)
    Z = rng.normal(size=(5000, 24))
    if collinear:
        Z[:, 5] = Z[:, 4] + 1e-4 * rng.normal(size=5000)
    Z = (Z - Z.mean(0)) / Z.std(0)
    Y = Z @ rng.normal(size=(24, 3)) + rng.normal(size=(5000, 3))
    Yc = Y - Y.mean(0)
    assert Z.shape[0] >= rep.GRAM_ROW_RATIO * Z.shape[1]          # the Gram branch runs
    for a, gram, svd in zip(ALPHAS, rep._ridge_path(Z, Yc, ALPHAS), _svd_path(Z, Yc, ALPHAS)):
        assert np.allclose(Z @ gram, Z @ svd, rtol=0, atol=1e-8 * np.abs(Z @ svd).max())
        if not collinear:
            assert np.allclose(gram, svd, rtol=1e-9, atol=1e-12)


# ------------------------------------------------------------- ridge grid (registered)
def _edge_problem():
    rng = np.random.default_rng(0)
    n, d = 600, 40
    X = rng.normal(size=(n, d))
    return rng, X, np.repeat(np.arange(n // 10), 10)


@pytest.mark.parametrize("case,alphas,expect", [
    ("clean signal, grid too strong", [1e2, 1e3, 1e4], "lowest"),
    ("pure noise, grid too weak", [1e-3, 1e-2, 1e-1], "highest"),
    ("noisy signal, optimum inside", [1e-2, 1e0, 1e2, 1e4, 1e6], None),
])
def test_alpha_at_grid_edge_is_flagged(case, alphas, expect):
    """Designer (e5f29367): when a fit's inner-CV penalty lands on either end of the registered
    grid, the fit records it (the grid is never widened after a number is seen). Synthetic
    fits whose optimum lies below / above the grid are flagged; an interior optimum is not."""
    rng, X, g = _edge_problem()
    y = {"lowest": X @ rng.normal(size=40) + 1e-3 * rng.normal(size=600),
         "highest": rng.normal(size=600),
         None: X @ (0.3 * rng.normal(size=40)) + 2 * rng.normal(size=600)}[expect]
    m = rep.fit_ridge(X, y, g, alphas=alphas, inner_folds=5)
    assert m.alpha_at_edge == expect
    assert m.alpha == {"lowest": alphas[0], "highest": alphas[-1]}.get(expect, m.alpha)
    assert rep.fit_ridge(X, y, g, alphas=[1.0], inner_folds=5).alpha_at_edge is None


MANIFESTS = ["algorithmic_null_pilot.yaml", "algorithmic_null_mayrep_interim.yaml",
             "algorithmic_null_mayrep.yaml"]


@pytest.mark.parametrize("name", MANIFESTS)
def test_ridge_settings_from_the_real_manifests(name):
    import yaml
    man = yaml.safe_load(open(os.path.join(os.path.dirname(__file__), "..", "..", "docs",
                                           "experiments", "active", "modulator_clues", name)))
    s = rep.ridge_settings(man)
    assert s["inner_folds"] == 5 and len(s["alphas"]) == 19
    assert s["alphas"][0] == pytest.approx(1e-2) and s["alphas"][-1] == pytest.approx(1e7)


def test_ridge_settings_are_required():
    ok = {"ridge_alphas": [0.1, 1.0], "inner_folds": 5}
    assert rep.ridge_settings(ok) == {"alphas": [0.1, 1.0], "inner_folds": 5}
    for bad in ({"inner_folds": 5}, {"ridge_alphas": [0.1]}, {**ok, "ridge_alphas": []},
                {**ok, "ridge_alphas": [1.0, 0.1]}, {**ok, "ridge_alphas": [0.0, 1.0]},
                {**ok, "inner_folds": 1}, {**ok, "inner_folds": 5.0}):
        with pytest.raises(ValueError):
            rep.ridge_settings(bad)
