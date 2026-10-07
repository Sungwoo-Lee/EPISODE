"""Pure measures of the L05 S42 case study (no JAX, no checkpoints): unit-testable.

No scikit-learn: the lab nodes' environments do not all carry it (numpy only).

Plain-language purpose: the case study asks, layer by layer, how much a change in felt injury
alone moves an agent's internal activity (Analysis 1, "noticing"), and whether that movement
points toward "about to go to the bush" (Analysis 2, "acting"). This file holds the arithmetic;
`case.py` produces the activity it is applied to.

Conventions (plan docs/experiments/active/modulator_clues/CASE_STUDY_L05_S42.md, Revision 1/1b):
* Activity arrays are (T, B, W): step, episode, unit. `valid` (T, B) marks steps the episode was
  alive. A layer's units are flattened to W.
* Shift = manipulated pass minus true-input pass at the same step of the same (natural) route.
* Size (Analysis 1) = mean over valid steps of the shift's Euclidean length, divided by the
  across-state spread of the layer over the unhurt live steps of the same checkpoint: the square
  root of the trace of the activity covariance. Units with zero variance there are dropped from
  both terms. Numerator and denominator are returned separately.
* Readout (Analysis 2) = ridge-penalised logistic regression of "off the bush now, on the bush at
  one of the next 5 steps", scored on held-out EPISODES with AUC and log-loss. Features are the
  layer's activity in the SAME space as Analysis 1's shift: centred on the unhurt-step mean and
  divided by ONE global scale per layer (den / sqrt(kept units), for the optimiser only -- a
  single scalar leaves cosines and log-odds unchanged). Units are deliberately NOT z-scored one
  by one: in the case agent some memory units have an unhurt SD of ~1e-5 and the 0.70 probe
  flips them by ~1, so per-unit scaling turns a bounded shift into a 10^4-SD one and the push
  then measures ridge extrapolation, not direction (smoke test 2026-10-07, step 6000013).
  Push = mean of w . shift over the shifted steps, divided by the SD of the readout's log-odds
  over the unhurt steps.
"""
from __future__ import annotations

import numpy as np

HORIZON = 5                                   # "arrives on the bush within 5 steps"
C_GRID = (1e-3, 1e-2, 1e-1, 1.0, 10.0)       # inverse ridge strength, logistic readouts
ALPHA_GRID = (1e-1, 1.0, 10.0, 100.0, 1000.0)  # ridge strength, felt-injury decoder
OUTER_FOLDS = 5
MIN_CLASS = 10                                # fewer positives or negatives -> readout not fitted


# ------------------------------------------------------------------ positions and labels
def positions(states0_agent_pos, out_agent_pos, T):
    """(T_max + 1, B, 2) agent position at the START of each step: row 0 is the reset
    position, row t + 1 is the position after the action at step t (the sweep's snapshot list).
    Rows past an episode's end repeat whatever the scan carried; callers mask with `valid`."""
    p0 = np.asarray(states0_agent_pos)[None]
    return np.concatenate([p0, np.asarray(out_agent_pos)], 0)


def on_bush(pos, bush_pos):
    """(T_max + 1, B) bool: the agent stands on the bush cell. `bush_pos` (B, 2) is
    obs_pos[:, 0] of the reset state -- the cell `episode_measures` counts as bush dwell."""
    return np.all(pos == np.asarray(bush_pos)[None], axis=-1)


def arrival_labels(onb, T, horizon=HORIZON):
    """Readout rows and labels.

    onb (T_max + 1, B) from `on_bush`; T (B,) episode lengths (steps). A row is a step t of
    episode b with t < T[b] - horizon (the last `horizon` steps are dropped: censored) and the
    agent OFF the bush at t (steps already on the bush are excluded). The label is 1 if the
    agent is on the bush at any of the positions t+1 .. t+horizon.
    Returns (mask (T_max, B) bool, label (T_max, B) bool); label is meaningful only under mask."""
    Tm = onb.shape[0] - 1
    t = np.arange(Tm)[:, None]
    mask = (t < (np.asarray(T)[None, :] - horizon)) & ~onb[:Tm]
    lab = np.zeros((Tm, onb.shape[1]), bool)
    for k in range(1, horizon + 1):          # lab[t] |= onb[t + k]
        lab[: Tm + 1 - k] |= onb[k: Tm + 1]
    return mask, lab & mask


# ------------------------------------------------------------------ Analysis 1
def spread(ref):
    """ref (n, W) unhurt live activity. Returns (keep (W,) bool, mean (W,), sd (W,), den) with
    den = sqrt(sum of per-unit variances over the kept units) = sqrt(trace of the covariance)."""
    ref = np.asarray(ref, np.float64)
    sd = ref.std(0)
    keep = sd > 0
    return keep, ref.mean(0), sd, float(np.sqrt(np.sum(sd[keep] ** 2)))


def shift_size(man, nat, keep, den):
    """man, nat (n, W) the two passes on the same steps. Returns (numerator, size, dead): the
    mean Euclidean length of (man - nat) over the kept units, that divided by `den`, and -- not
    part of the size, reported so it is not hidden -- the same mean length over the DROPPED
    units (silent in the unhurt pass; the 0.70 probe can switch them on)."""
    d = np.asarray(man, np.float64) - np.asarray(nat, np.float64)
    if not len(d):
        return float("nan"), float("nan"), float("nan")
    num = float(np.linalg.norm(d[:, keep], axis=1).mean())
    dead = float(np.linalg.norm(d[:, ~keep], axis=1).mean())
    return num, (num / den if den > 0 else float("nan")), dead


# ------------------------------------------------------------------ Analysis 2
def _group_folds(groups, k):
    """Deterministic grouped folds (no group split across folds), balanced by size: groups in
    order of decreasing size (ties by id) go to the currently smallest fold."""
    groups = np.asarray(groups)
    ids, counts = np.unique(groups, return_counts=True)
    k = min(k, len(ids))
    order = sorted(range(len(ids)), key=lambda i: (-counts[i], ids[i]))
    load, fold_of = np.zeros(k), {}
    for i in order:
        f = int(np.argmin(load))
        fold_of[ids[i]] = f
        load[f] += counts[i]
    f_row = np.array([fold_of[g] for g in groups])
    return [(np.flatnonzero(f_row != f), np.flatnonzero(f_row == f)) for f in range(k)]


class _LogReg:
    """L2-penalised logistic regression, intercept unpenalised, the scikit-learn convention:
    minimise C * sum(log-loss) + 0.5 * |w|^2. Newton's method with backtracking (numpy only:
    the lab nodes' environments do not all carry scikit-learn)."""

    def __init__(self, C, max_iter=100, tol=1e-8):
        self.C, self.max_iter, self.tol = C, max_iter, tol

    def _obj(self, X1, y, beta):
        z = X1 @ beta
        return self.C * float(np.sum(np.logaddexp(0.0, z) - y * z)) + 0.5 * float(beta[1:] @ beta[1:])

    def fit(self, X, y):
        X = np.asarray(X, np.float64)
        y = np.asarray(y, np.float64)
        X1 = np.hstack([np.ones((len(X), 1)), X])
        P = np.eye(X1.shape[1]); P[0, 0] = 0.0
        beta = np.zeros(X1.shape[1])
        p0 = np.clip(y.mean(), 1e-6, 1 - 1e-6)
        beta[0] = np.log(p0 / (1 - p0))
        f = self._obj(X1, y, beta)
        for _ in range(self.max_iter):
            p = 1.0 / (1.0 + np.exp(-(X1 @ beta)))
            g = self.C * (X1.T @ (p - y)) + P @ beta
            H = self.C * (X1.T * (p * (1 - p))) @ X1 + P + 1e-10 * np.eye(len(beta))
            step = np.linalg.solve(H, g)
            t = 1.0
            while True:
                nb = beta - t * step
                nf = self._obj(X1, y, nb)
                if nf <= f - 1e-4 * t * float(g @ step) or t < 1e-10:
                    break
                t *= 0.5
            beta, df, f = nb, f - nf, nf
            if df < self.tol * max(1.0, abs(f)):
                break
        self.coef_, self.intercept_ = beta[1:][None], beta[:1]
        return self

    def predict_proba(self, X):
        p = 1.0 / (1.0 + np.exp(-(np.asarray(X, np.float64) @ self.coef_[0] + self.intercept_[0])))
        return np.stack([1 - p, p], 1)


def _logreg(C):
    return _LogReg(C)


def log_loss(y, p, eps=1e-15):
    y = np.asarray(y, np.float64)
    p = np.clip(np.asarray(p, np.float64), eps, 1 - eps)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def roc_auc(y, score):
    """Area under the ROC curve = Mann-Whitney U / (n_pos n_neg), ties at half weight."""
    y = np.asarray(y).astype(bool)
    s = np.asarray(score, np.float64)
    order = np.argsort(s, kind="mergesort")
    ranks = np.empty(len(s))
    ss = s[order]
    i = 0
    while i < len(ss):                       # average ranks over ties
        j = i
        while j + 1 < len(ss) and ss[j + 1] == ss[i]:
            j += 1
        ranks[order[i:j + 1]] = 0.5 * (i + j) + 1.0
        i = j + 1
    n1, n0 = int(y.sum()), int((~y).sum())
    return float((ranks[y].sum() - n1 * (n1 + 1) / 2.0) / (n1 * n0))


def _ridge(Z, t, alpha):
    """Ridge regression with an unpenalised intercept: (w, b)."""
    mz, mt = Z.mean(0), t.mean()
    Zc = Z - mz
    w = np.linalg.solve(Zc.T @ Zc + alpha * np.eye(Z.shape[1]), Zc.T @ (t - mt))
    return w, mt - mz @ w


def fit_readout(Z, y, groups):
    """Ridge logistic readout scored on held-out episodes. The ridge strength is chosen by
    grouped (by episode) 5-fold CV on all rows; the held-out AUC and log-loss are those
    out-of-fold predictions at the chosen strength (a choice among 5 values: negligible
    optimism, reported as such). The final readout is refitted on all rows. Returns a dict;
    `fitted` False (and NaNs) when either class has fewer than MIN_CLASS rows."""
    Z, y, groups = np.asarray(Z, np.float64), np.asarray(y, int), np.asarray(groups)
    n_pos, n = int(y.sum()), len(y)
    res = {"n_rows": n, "n_pos": n_pos, "n_groups": int(len(np.unique(groups))), "fitted": False,
           "C": np.nan, "auc_heldout": np.nan, "logloss_heldout": np.nan,
           "logloss_base": np.nan, "w": None, "b": np.nan}
    if n_pos < MIN_CLASS or n - n_pos < MIN_CLASS:
        return res
    folds = _group_folds(groups, OUTER_FOLDS)
    best = (None, np.inf, None)
    for C in C_GRID:
        pred = np.empty(n)
        for tr, te in folds:
            if len(np.unique(y[tr])) < 2:
                pred[te] = y[tr].mean()
                continue
            pred[te] = _logreg(C).fit(Z[tr], y[tr]).predict_proba(Z[te])[:, 1]
        ll = log_loss(y, pred)
        if ll < best[1]:
            best = (C, ll, pred)
    C, ll, pred = best
    m = _logreg(C).fit(Z, y)
    p = y.mean()
    res.update(fitted=True, C=float(C), auc_heldout=roc_auc(y, pred),
               logloss_heldout=float(ll),
               logloss_base=float(-(p * np.log(p) + (1 - p) * np.log(1 - p))),
               w=m.coef_[0].astype(np.float64), b=float(m.intercept_[0]))
    return res


def fit_decoder(Z, target, groups):
    """Ridge regression of felt injury on the layer's activity; alpha by grouped CV; held-out
    R^2 from the out-of-fold predictions at that alpha. Returns (w, r2_heldout, alpha)."""
    Z, target = np.asarray(Z, np.float64), np.asarray(target, np.float64)
    folds = _group_folds(np.asarray(groups), OUTER_FOLDS)
    best = (None, -np.inf)
    ss = float(((target - target.mean()) ** 2).sum())
    for a in ALPHA_GRID:
        pred = np.empty(len(target))
        for tr, te in folds:
            w, b = _ridge(Z[tr], target[tr], a)
            pred[te] = Z[te] @ w + b
        r2 = 1.0 - float(((target - pred) ** 2).sum()) / ss if ss > 0 else np.nan
        if r2 > best[1]:
            best = (a, r2)
    a, r2 = best
    return _ridge(Z, target, a)[0], float(r2), float(a)


def cosine(a, b):
    a, b = np.asarray(a, np.float64), np.asarray(b, np.float64)
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    return float(a @ b / (na * nb)) if na > 0 and nb > 0 else float("nan")


def push(w, b, Z_unhurt, Dz):
    """Projection of the shift Dz (n, W), in the readout's feature space, on the readout (w, b): the mean change in
    predicted log-odds, in units of the readout's log-odds SD over the unhurt steps Z_unhurt,
    plus the raw mean change, the SD, and the cosine between w and the mean shift."""
    logit_sd = float((np.asarray(Z_unhurt, np.float64) @ w + b).std())
    d = float((np.asarray(Dz, np.float64) @ w).mean())
    return {"push_logodds": d, "logit_sd": logit_sd,
            "push_sd": d / logit_sd if logit_sd > 0 else float("nan"),
            "cos_shift_readout": cosine(np.asarray(Dz).mean(0), w)}


def logit(p, eps=1e-3):
    p = np.clip(np.asarray(p, np.float64), eps, 1 - eps)
    return np.log(p / (1 - p))


# ------------------------------------------------------------------ reading rule
RULE = {"case": ("ge", 7), "same_seed": ("ge", 6), "reverse": ("lt", 6)}


def count_expected(diffs):
    """diffs: per-checkpoint (modulated - ordinary), or (live - frozen), oriented so that > 0 is
    the expected sign. NaN entries count as not-expected. Returns (n_expected, n_reversed, n)."""
    d = np.asarray(diffs, np.float64)
    return int(np.sum(d > 0)), int(np.sum(d < 0)), int(len(d))


def condition_met(role, n_expected):
    op, k = RULE[role]
    return bool(n_expected >= k) if op == "ge" else bool(n_expected < k)
