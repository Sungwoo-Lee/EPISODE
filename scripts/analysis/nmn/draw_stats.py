"""Bootstrap draws of CKA and held-out R^2, computed from per-group sums (pure numpy, float64).

Plain-language purpose: the rules' bootstrap resamples whole `episode_seed` groups, thousands
of times, and recomputes every similarity and read-out score on each resample. Recomputing
`representation.linear_cka` / `representation.r2_weighted` row by row for every draw would take
hours on a May probe (150,000 rows x 2,000 draws x 18 agent pairs x 5 layers). But a resample
only changes HOW OFTEN each group counts, so every weighted sum in those two statistics is a
count-weighted sum of per-group sums. This module forms the per-group sums once and gets every
draw with one matrix product.

It is not a second definition of either statistic: the tests
(tests/analysis/test_nmn_draw_stats.py) check both against `representation.linear_cka` and
`representation.r2_weighted`, called with `representation.draw_weights`, on random draws to
1e-10. The point estimates in the drivers call `representation` itself.

Inputs everywhere: `row_group` gives, per row, the position of its group in the list the draw
counts refer to (e.g. `split.test_groups`, or the probe's distinct groups for CKA); `counts`
is (n_draws, n_groups): how many times each group was drawn (`counts_from_positions`).

Plan: docs/develop/active/neuromodulation/ALGORITHMIC_NULL_ANALYSIS_TOOLING.md, §A1/A3/A4
statistics (bootstrap), §A2 decoding.
"""
from __future__ import annotations

import numpy as np


def counts_from_positions(positions: np.ndarray, n_groups: int) -> np.ndarray:
    """(n_draws, n_groups) multiplicities from `representation.joint_group_bootstrap` /
    `whole_probe_bootstrap` positions (n_draws, n_drawn)."""
    positions = np.asarray(positions)
    n = positions.shape[0]
    flat = (positions + np.arange(n)[:, None] * n_groups).ravel()
    return np.bincount(flat, minlength=n * n_groups).reshape(n, n_groups).astype(np.float64)


def row_positions(row_groups, draw_groups) -> np.ndarray:
    """Position of each row's group in the sorted `draw_groups`; raises if one is missing."""
    draw_groups = np.asarray(draw_groups)
    g = np.asarray(row_groups)
    pos = np.searchsorted(draw_groups, g)
    ok = draw_groups[np.clip(pos, 0, len(draw_groups) - 1)] == g
    if not ok.all():
        raise ValueError("row_positions: a row's group is not among the drawn groups")
    return pos


def _group_sum(values: np.ndarray, row_group: np.ndarray, n_groups: int) -> np.ndarray:
    """Per-group sum of `values` (rows first; any trailing shape)."""
    v = np.asarray(values, np.float64)
    out = np.zeros((n_groups,) + v.shape[1:])
    np.add.at(out, row_group, v)
    return out


def _group_cross(A: np.ndarray, B: np.ndarray, row_group: np.ndarray, n_groups: int) -> np.ndarray:
    """(n_groups, da * db): per-group sum of a b' (rows sorted internally)."""
    order = np.argsort(row_group, kind="stable")
    g = row_group[order]
    A, B = np.asarray(A, np.float64)[order], np.asarray(B, np.float64)[order]
    bounds = np.searchsorted(g, np.arange(n_groups + 1))
    out = np.zeros((n_groups, A.shape[1] * B.shape[1]))
    for k in range(n_groups):
        s, e = bounds[k], bounds[k + 1]
        if e > s:
            out[k] = (A[s:e].T @ B[s:e]).ravel()
    return out


def centred_frobenius(A, B, row_group, counts) -> np.ndarray:
    """Per draw, ||sum_rows w (a - mu_a)(b - mu_b)'||_F with w the row's group multiplicity and
    mu the w-weighted means: the three norms of weighted linear CKA
    (||Y'X||_F^2 / (||X'X||_F ||Y'Y||_F) = f(Y, X)^2 / (f(X, X) f(Y, Y)))."""
    row_group = np.asarray(row_group)
    G = counts.shape[1]
    A = np.asarray(A, np.float64)
    B = np.asarray(B, np.float64)
    n_g = _group_sum(np.ones(len(row_group)), row_group, G)
    W = counts @ n_g                                         # (n_draws,)
    sa = counts @ _group_sum(A, row_group, G)                # (n_draws, da)
    sb = counts @ _group_sum(B, row_group, G)
    S = counts @ _group_cross(A, B, row_group, G)            # (n_draws, da * db)
    C = S - (sa[:, :, None] * sb[:, None, :]).reshape(S.shape) / W[:, None]
    return np.sqrt((C ** 2).sum(axis=1))


def cka_draws(X, Y, row_group, counts, fxx=None, fyy=None) -> np.ndarray:
    """Linear CKA per draw (as `representation.linear_cka(X, Y, weights)`). `fxx` / `fyy` are
    `centred_frobenius(X, X, ...)` / `(Y, Y, ...)`, passed in when the caller caches them."""
    fxx = centred_frobenius(X, X, row_group, counts) if fxx is None else fxx
    fyy = centred_frobenius(Y, Y, row_group, counts) if fyy is None else fyy
    fyx = centred_frobenius(Y, X, row_group, counts)
    with np.errstate(invalid="ignore", divide="ignore"):
        out = fyx ** 2 / (fxx * fyy)
    return np.where((fxx == 0) | (fyy == 0), np.nan, out)


def r2_draws(Y, P, row_group, counts) -> np.ndarray:
    """Held-out R^2 per draw, variance-weighted over output units (as
    `representation.r2_weighted(Y, P, weights)`): 1 - sum w |y - p|^2 / sum w |y - mu_w|^2."""
    Y = np.asarray(Y, np.float64)
    P = np.asarray(P, np.float64)
    Y = Y[:, None] if Y.ndim == 1 else Y
    P = P[:, None] if P.ndim == 1 else P
    if Y.shape != P.shape:
        raise ValueError(f"r2_draws: targets {Y.shape} vs predictions {P.shape}")
    row_group = np.asarray(row_group)
    G = counts.shape[1]
    W = counts @ _group_sum(np.ones(len(row_group)), row_group, G)
    sy = counts @ _group_sum(Y, row_group, G)
    syy = counts @ _group_sum((Y ** 2).sum(axis=1), row_group, G)
    sse = counts @ _group_sum(((Y - P) ** 2).sum(axis=1), row_group, G)
    sst = syy - (sy ** 2).sum(axis=1) / W
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(sst == 0, np.nan, 1.0 - sse / sst)


def r2_unit_mean_draws(Y, P, row_group, counts) -> tuple[np.ndarray, np.ndarray]:
    """Per draw, the UNWEIGHTED mean over output units of each unit's held-out R^2 (a
    descriptive robustness column, not a registered statistic: unlike the variance-weighted
    R^2 it is unchanged by a per-unit rescaling of the predicted layer). Units whose held-out
    values are constant in a draw (SST = 0) have no R^2 and are left out of that draw's mean.
    Returns (means, units_left_out_per_draw)."""
    Y = np.asarray(Y, np.float64)
    P = np.asarray(P, np.float64)
    Y = Y[:, None] if Y.ndim == 1 else Y
    P = P[:, None] if P.ndim == 1 else P
    row_group = np.asarray(row_group)
    G = counts.shape[1]
    W = counts @ _group_sum(np.ones(len(row_group)), row_group, G)
    sy = counts @ _group_sum(Y, row_group, G)
    syy = counts @ _group_sum(Y ** 2, row_group, G)
    sse = counts @ _group_sum((Y - P) ** 2, row_group, G)
    sst = syy - sy ** 2 / W[:, None]
    ok = sst > 1e-12 * np.maximum(syy, 1.0)          # float guard: constant units only
    with np.errstate(invalid="ignore", divide="ignore"):
        r2 = np.where(ok, 1.0 - sse / np.where(ok, sst, 1.0), np.nan)
    return np.nanmean(r2, axis=1), (~ok).sum(axis=1)
