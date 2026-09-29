"""draw_stats (per-group-sum bootstrap draws) equals the reviewed statistics in representation.py.

For random data with repeated episode_seed groups, every draw of `draw_stats.cka_draws` and
`draw_stats.r2_draws` must equal `representation.linear_cka` / `representation.r2_weighted`
evaluated with the row multiplicities `representation.draw_weights` gives for that draw.
Pure numpy; test fixture data, not study data.
"""
import os
import sys

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
from scripts.analysis.nmn import draw_stats as ds  # noqa: E402
from scripts.analysis.nmn import representation as rep  # noqa: E402


def _data(seed=0, n_groups=40, per=6, dx=7, dy=5):
    """Groups of UNEQUAL size (1 to 2 * per rows), as kept rows per episode_seed are when
    short episodes keep fewer rows (code review)."""
    rng = np.random.default_rng(seed)
    sizes = rng.integers(1, 2 * per + 1, n_groups)
    groups = np.repeat(rng.choice(10_000, n_groups, replace=False), sizes)
    rng.shuffle(groups)
    X = rng.normal(size=(groups.size, dx)) + 3.0
    Y = X[:, :dy] * 2.0 + rng.normal(size=(groups.size, dy)) * 0.5
    return groups, X, Y


def test_counts_match_draw_weights():
    groups, _, _ = _data()
    ug, pos = rep.whole_probe_bootstrap(groups, 5, seed=3)
    counts = ds.counts_from_positions(pos, len(ug))
    rows = np.arange(groups.size)
    rg = ds.row_positions(groups, ug)
    for d in range(5):
        w = rep.draw_weights(groups, rows, ug, pos[d])
        assert np.array_equal(counts[d][rg], w)


def test_cka_draws_equal_linear_cka_with_weights():
    groups, X, Y = _data()
    ug, pos = rep.whole_probe_bootstrap(groups, 25, seed=1)
    counts = ds.counts_from_positions(pos, len(ug))
    rg = ds.row_positions(groups, ug)
    got = ds.cka_draws(X, Y, rg, counts)
    rows = np.arange(groups.size)
    for d in range(25):
        w = rep.draw_weights(groups, rows, ug, pos[d])
        assert abs(got[d] - rep.linear_cka(X, Y, weights=w)) < 1e-10
    # unit weights reproduce the point estimate
    ones = np.ones((1, len(ug)))
    assert abs(ds.cka_draws(X, Y, rg, ones)[0] - rep.linear_cka(X, Y)) < 1e-12


def test_r2_draws_equal_r2_weighted_on_heldout_rows():
    groups, X, Y = _data(seed=4)
    splits = rep.episode_split(groups, 2, 0.3, seed=0)
    draws = rep.joint_group_bootstrap(groups, splits, 20, seed=2)
    for s, pos in zip(splits, draws):
        m = rep.fit_ridge(X[s.train], Y[s.train], groups[s.train], alphas=[0.1, 1.0, 10.0],
                          inner_folds=2)
        P = m.predict(X[s.test])
        counts = ds.counts_from_positions(pos, len(s.test_groups))
        rg = ds.row_positions(groups[s.test], s.test_groups)
        got = ds.r2_draws(Y[s.test], P, rg, counts)
        for d in range(20):
            w = rep.draw_weights(groups, s.test, s.test_groups, pos[d])
            assert abs(got[d] - rep.heldout_r2(m, X, Y, s.test, w)) < 1e-10
        one = ds.r2_draws(Y[s.test, 0], P[:, 0], rg, np.ones((1, len(s.test_groups))))[0]
        assert abs(one - rep.r2_weighted(Y[s.test, 0], P[:, 0])) < 1e-12


def test_row_positions_refuses_an_unknown_group():
    import pytest
    with pytest.raises(ValueError):
        ds.row_positions(np.array([1, 5]), np.array([1, 2, 3]))


def test_unit_mean_draws_equal_per_unit_r2_weighted():
    groups, X, Y = _data(seed=7)
    Y[:, 0] = 2.0                                        # one constant unit: left out
    splits = rep.episode_split(groups, 1, 0.3, seed=0)
    s = splits[0]
    pos = rep.joint_group_bootstrap(groups, splits, 15, seed=4)[0]
    m = rep.fit_ridge(X[s.train], Y[s.train], groups[s.train], alphas=[1.0], inner_folds=2)
    P = m.predict(X[s.test])
    counts = ds.counts_from_positions(pos, len(s.test_groups))
    rg = ds.row_positions(groups[s.test], s.test_groups)
    got, left = ds.r2_unit_mean_draws(Y[s.test], P, rg, counts)
    for d in range(15):
        w = rep.draw_weights(groups, s.test, s.test_groups, pos[d])
        ref = [rep.r2_weighted(Y[s.test, j], P[:, j], w) for j in range(1, Y.shape[1])]
        assert abs(got[d] - np.mean(ref)) < 1e-10 and left[d] == 1
