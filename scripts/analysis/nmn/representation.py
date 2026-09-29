"""Layer comparison and read-out statistics for "What Both Agents Compute" (pure numpy).

Plain-language purpose: the analyses compare two agents' layers on the same stored inputs,
and read quantities (hunger, injury, predator distance, survival time left) out of a layer.
This module holds the statistics only; it decides nothing and holds no threshold.

- `linear_cka(X, Y)`: linear centred kernel alignment, ||Y'X||_F^2 / (||X'X||_F ||Y'Y||_F) on
  column-centred float64 features. Unchanged by rotations and a uniform rescale; NOT by a
  per-unit rescale (the modulator's fixed gain is exactly that, hence the next statistic).
- Linear predictivity: a ridge map from one agent's layer to the other's, fitted on training
  episodes and scored as held-out R^2 (variance-weighted over output units). Unchanged by any
  invertible linear map of either layer. `fit_maps` fits once per split repeat;
  `heldout_r2` scores any resample of the held-out rows from the fixed maps.
- Ridge read-out of a quantity (A2) is the same fit with one output column.
- The clock baseline (rules A2.clock_baseline): the per-time-step mean of the quantity on the
  training fold, scored on the same held-out rows; a held-out row whose time step has no
  training row has no clock value and is masked for the layer and the clock alike.
- Episode-grouped splits and a joint group bootstrap: one resample of held-out `episode_seed`
  groups per draw, shared by every agent and pair (rules common.bootstrap).

Every size (repeats, test fraction, alpha grid, inner folds, number of draws, seeds) is a
required argument; the drivers read them from the pinned rules' `parameters:` and the manifest.

Plan: docs/develop/active/neuromodulation/ALGORITHMIC_NULL_ANALYSIS_TOOLING.md, File Changes §6,
§A1/A3/A4 statistics, §A2 decoding.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


# -------------------------------------------------------------------------------- CKA -----
def linear_cka(X, Y, weights=None) -> float:
    """Linear CKA, feature-space form, float64. `weights` (per row, e.g. bootstrap
    multiplicities) weight the centring and the cross products."""
    X = np.asarray(X, dtype=np.float64)
    Y = np.asarray(Y, dtype=np.float64)
    if X.ndim != 2 or Y.ndim != 2 or X.shape[0] != Y.shape[0]:
        raise ValueError("X and Y must be 2-D with the same rows")
    if weights is None:
        w = np.ones(X.shape[0])
    else:
        w = np.asarray(weights, dtype=np.float64)
    sw = w.sum()
    Xc = X - (w @ X) / sw
    Yc = Y - (w @ Y) / sw
    Xw, Yw = Xc * w[:, None], Yc * w[:, None]
    yx = np.linalg.norm(Yw.T @ Xc) ** 2
    xx = np.linalg.norm(Xw.T @ Xc)
    yy = np.linalg.norm(Yw.T @ Yc)
    if xx == 0 or yy == 0:
        return float("nan")
    return float(yx / (xx * yy))


# ------------------------------------------------------------------------------ splits -----
@dataclass
class Split:
    train: np.ndarray          # row indices
    test: np.ndarray           # row indices
    test_groups: np.ndarray    # distinct groups in the test fold


def episode_split(groups, n_repeats: int, test_frac: float, seed: int) -> list[Split]:
    """Group-wise train/test splits (sklearn GroupShuffleSplit): no group on both sides,
    asserted. The same list is used for every agent on a probe."""
    from sklearn.model_selection import GroupShuffleSplit
    groups = np.asarray(groups)
    gss = GroupShuffleSplit(n_splits=n_repeats, test_size=test_frac, random_state=seed)
    out = []
    for tr, te in gss.split(np.zeros(len(groups)), groups=groups):
        gtr, gte = np.unique(groups[tr]), np.unique(groups[te])
        if np.intersect1d(gtr, gte).size:
            raise AssertionError("episode_split: a group sits in both folds")
        out.append(Split(train=np.sort(tr), test=np.sort(te), test_groups=gte))
    return out


# ------------------------------------------------------------------------------- ridge -----
@dataclass
class RidgeMap:
    x_mean: np.ndarray
    x_scale: np.ndarray
    y_mean: np.ndarray
    coef: np.ndarray           # (d_in, d_out)
    alpha: float

    def predict(self, X) -> np.ndarray:
        Z = (np.asarray(X, np.float64) - self.x_mean) / self.x_scale
        return Z @ self.coef + self.y_mean


def _standardise(X):
    mu = X.mean(axis=0)
    sd = X.std(axis=0)
    sd = np.where(sd > 0, sd, 1.0)      # a constant column is zero after centring
    return mu, sd


def _ridge_path(Z, Yc, alphas):
    """Ridge coefficients for every alpha from one SVD of the standardised inputs."""
    U, s, Vt = np.linalg.svd(Z, full_matrices=False)
    UtY = U.T @ Yc
    return [Vt.T @ ((s / (s ** 2 + a))[:, None] * UtY) for a in alphas]


def r2_weighted(Y, P, weights=None) -> float:
    """Held-out R^2, variance-weighted over output units (sklearn's 'variance_weighted'):
    1 - sum SSE / sum SST, SST about the (weighted) held-out mean."""
    Y = np.asarray(Y, np.float64)
    P = np.asarray(P, np.float64)
    Y = Y[:, None] if Y.ndim == 1 else Y
    P = P[:, None] if P.ndim == 1 else P
    if Y.shape != P.shape:
        raise ValueError(f"r2: targets {Y.shape} vs predictions {P.shape}")
    w = np.ones(Y.shape[0]) if weights is None else np.asarray(weights, np.float64)
    mu = (w @ Y) / w.sum()
    sse = float((w[:, None] * (Y - P) ** 2).sum())
    sst = float((w[:, None] * (Y - mu) ** 2).sum())
    return float("nan") if sst == 0 else 1.0 - sse / sst


def fit_ridge(X, Y, groups, *, alphas, inner_folds: int) -> RidgeMap:
    """Ridge from X to Y (standardisation of X and centring of Y fitted on these rows only),
    alpha chosen from `alphas` by episode-grouped K-fold CV inside these rows (held-out
    variance-weighted R^2), then refitted on all of them."""
    from sklearn.model_selection import GroupKFold
    X = np.asarray(X, np.float64)
    Y = np.asarray(Y, np.float64)
    if Y.ndim == 1:
        Y = Y[:, None]
    alphas = [float(a) for a in alphas]
    if len(alphas) > 1:
        score = np.zeros(len(alphas))
        for tr, va in GroupKFold(n_splits=inner_folds).split(X, groups=groups):
            mu, sd = _standardise(X[tr])
            ym = Y[tr].mean(axis=0)
            coefs = _ridge_path((X[tr] - mu) / sd, Y[tr] - ym, alphas)
            Zv = (X[va] - mu) / sd
            for i, c in enumerate(coefs):
                score[i] += r2_weighted(Y[va], Zv @ c + ym)
        alpha = alphas[int(np.argmax(score))]
    else:
        alpha = alphas[0]
    mu, sd = _standardise(X)
    ym = Y.mean(axis=0)
    coef = _ridge_path((X - mu) / sd, Y - ym, [alpha])[0]
    return RidgeMap(x_mean=mu, x_scale=sd, y_mean=ym, coef=coef, alpha=alpha)


def fit_maps(X, Y, groups, splits: list[Split], *, alphas, inner_folds: int,
             fitter=fit_ridge) -> list[RidgeMap]:
    """One ridge map per split repeat, fitted on that repeat's training fold ONCE (rules
    common.bootstrap.predictivity_detail: the maps are held fixed while the bootstrap
    resamples held-out groups). `fitter` is injectable for the fit-count test."""
    groups = np.asarray(groups)
    return [fitter(np.asarray(X)[s.train], np.asarray(Y)[s.train], groups[s.train],
                   alphas=alphas, inner_folds=inner_folds) for s in splits]


def heldout_r2(m: RidgeMap, X, Y, rows, weights=None) -> float:
    """Held-out R^2 of a fixed map on `rows` (with optional bootstrap multiplicities)."""
    rows = np.asarray(rows)
    return r2_weighted(np.asarray(Y)[rows], m.predict(np.asarray(X)[rows]), weights)


# ------------------------------------------------------------------------------- clock -----
@dataclass
class ClockMeans:
    t: np.ndarray              # time steps present in the training fold (sorted)
    mean: np.ndarray           # per-time-step training-fold mean of the quantity


def clock_baseline(t, y, train_rows) -> ClockMeans:
    """Rules A2.clock_baseline: 'predicting the quantity from the time step alone, fitted as the
    per-time-step mean on the training fold'."""
    t = np.asarray(t)[np.asarray(train_rows)]
    y = np.asarray(y, np.float64)[np.asarray(train_rows)]
    ut, inv = np.unique(t, return_inverse=True)
    sums = np.bincount(inv, weights=y)
    cnt = np.bincount(inv)
    return ClockMeans(t=ut, mean=sums / cnt)


def clock_predict(means: ClockMeans, t_rows) -> tuple[np.ndarray, np.ndarray]:
    """(prediction, has_clock) for rows at times `t_rows`; has_clock is False where the time
    step has no training row (such rows are dropped from the layer and clock scores alike)."""
    t_rows = np.asarray(t_rows)
    pos = np.searchsorted(means.t, t_rows)
    pos_c = np.clip(pos, 0, len(means.t) - 1)
    ok = means.t[pos_c] == t_rows
    pred = np.where(ok, means.mean[pos_c], np.nan)
    return pred, ok


def clock_mask(means: ClockMeans, t, rows) -> np.ndarray:
    """The held-out rows that have a clock value (the mask every scorer applies)."""
    rows = np.asarray(rows)
    _, ok = clock_predict(means, np.asarray(t)[rows])
    return rows[ok]


def clock_r2(means: ClockMeans, t, y, rows, weights=None) -> float:
    """Held-out R^2 of the clock on `rows` (callers pass rows already through `clock_mask`;
    a row with no clock value raises here rather than being scored)."""
    rows = np.asarray(rows)
    pred, ok = clock_predict(means, np.asarray(t)[rows])
    if not ok.all():
        raise ValueError("clock_r2: rows without a clock value; apply clock_mask first")
    return r2_weighted(np.asarray(y, np.float64)[rows], pred, weights)


# --------------------------------------------------------------------------- bootstrap -----
def joint_group_bootstrap(groups, splits: list[Split], n: int, seed: int) -> list[np.ndarray]:
    """Per split repeat, an (n, n_test_groups) array of resampled held-out group positions
    (with replacement): one resample per draw, shared by every agent and pair."""
    rng = np.random.default_rng(seed)
    return [rng.integers(0, len(s.test_groups), size=(n, len(s.test_groups))) for s in splits]


def whole_probe_bootstrap(groups, n: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """For statistics with no split (CKA): (distinct groups, (n, n_groups) resampled positions)."""
    ug = np.unique(np.asarray(groups))
    rng = np.random.default_rng(seed)
    return ug, rng.integers(0, len(ug), size=(n, len(ug)))


def draw_weights(groups, rows, draw_groups, draw_positions) -> np.ndarray:
    """Row multiplicities for one draw: each row of `rows` counts as many times as its group
    was drawn. `draw_groups` is the group list the positions index into."""
    counts = np.bincount(draw_positions, minlength=len(draw_groups))
    g = np.asarray(groups)[np.asarray(rows)]
    pos = np.searchsorted(draw_groups, g)
    if not np.all(draw_groups[np.clip(pos, 0, len(draw_groups) - 1)] == g):
        raise ValueError("draw_weights: a row's group is not among the drawn groups")
    return counts[pos].astype(np.float64)
