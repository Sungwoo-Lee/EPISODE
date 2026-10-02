"""Multi-scale trailing-window profile for a checkpoint-history behaviour measure.

WHY THIS EXISTS. A behaviour measure read off the FINAL checkpoint is one draw from a
distribution whose checkpoint-to-checkpoint spread (sd 10-27 percentage points at level 04) is
four to ten times the 30-episode sampling error (SE 2.3-2.6 pp). Reading the endpoint produced a
level-04 "result" -- control parked in the bush, neuromodulated agent hiding conditionally, a
60-point gap -- that vanished entirely (0.8 points, p=0.92) once ten checkpoints were averaged.
Picking a single window size instead merely moves the arbitrariness.

WHAT A WINDOW SWEEP BUYS. Growing the trailing window is NOT simply "more data": variance falls
roughly as 1/sqrt(w), but the window reaches back into the learning phase, so bias grows as the
average drags in a less-trained policy. Sweeping w from 1 to the whole run draws that bias-variance
profile explicitly. It makes the decision rule visible rather than asserted:

  * an effect that is real holds its sign and rough size across scales;
  * an endpoint artefact is large at w=1 and collapses as w grows;
  * a still-training effect drifts monotonically with w and never plateaus;
  * the plateau region, where the estimate stops moving, is the defensible window to quote.

AUTOCORRELATION. Averaging w checkpoints only buys sqrt(w) if they are independent. Measured
lag-1 autocorrelation across late checkpoints here is near zero (-0.06, +0.04, +0.01, +0.36), so
they behave as quasi-independent samples of the converged policy -- but that is a measurement, not
an assumption, so it is recomputed per series and the confidence interval is widened by the
effective sample size n_eff = w (1 - r1) / (1 + r1) whenever r1 is positive.

WHAT IT CANNOT DO. Every interval here describes ONE training run. With a single seed per cell the
across-checkpoint spread is within-run policy variation, not between-run variation, so nothing
here supports a claim about neuromodulation as a method -- only about these particular runs.
"""
import numpy as np
import pandas as pd
from scipy import stats


def lag1(x):
    """Lag-1 autocorrelation; 0.0 for a constant or a series shorter than 3."""
    x = np.asarray(x, float)
    if x.size < 3:
        return 0.0
    d = x - x.mean()
    den = (d * d).sum()
    return float((d[:-1] * d[1:]).sum() / den) if den > 0 else 0.0


def effective_n(w, r1):
    """Independent-sample equivalent of w correlated draws. Positive correlation only."""
    if r1 <= 0:
        return float(w)
    return float(np.clip(w * (1.0 - r1) / (1.0 + r1), 1.0, w))


def window_profile(values, windows=None):
    """Trailing-window mean and CI for every window size.

    `values` is ordered oldest -> newest; window w uses the LAST w entries.
    Returns a DataFrame with one row per window size.
    """
    v = np.asarray(values, float)
    v = v[~np.isnan(v)]
    n = v.size
    if windows is None:
        windows = sorted({1, 2, 3, 5, 8, 10, 15, 20, 25, 30, 40, n})
    rows = []
    for w in windows:
        if w < 1 or w > n:
            continue
        x = v[-w:]
        m = float(x.mean())
        if w == 1:
            rows.append(dict(window=w, mean=m, sd=np.nan, se=np.nan, lo=np.nan, hi=np.nan,
                             r1=np.nan, n_eff=1.0))
            continue
        sd = float(x.std(ddof=1))
        r1 = lag1(x)
        ne = effective_n(w, r1)
        se = sd / np.sqrt(ne)
        # t on the effective degrees of freedom, floored at 1 so a tiny n_eff stays finite
        half = stats.t.ppf(0.975, max(ne - 1.0, 1.0)) * se
        rows.append(dict(window=w, mean=m, sd=sd, se=se, lo=m - half, hi=m + half,
                         r1=r1, n_eff=ne))
    return pd.DataFrame(rows)


def difference_profile(a, b, windows=None):
    """Profile of (mean a - mean b) per window, with a Welch interval on n_eff."""
    a = np.asarray(a, float); b = np.asarray(b, float)
    pa, pb = window_profile(a, windows), window_profile(b, windows)
    out = []
    for w in sorted(set(pa.window) & set(pb.window)):
        ra = pa[pa.window == w].iloc[0]; rb = pb[pb.window == w].iloc[0]
        d = ra["mean"] - rb["mean"]
        if w == 1 or np.isnan(ra["se"]) or np.isnan(rb["se"]):
            out.append(dict(window=w, diff=d, lo=np.nan, hi=np.nan, p=np.nan))
            continue
        se = np.hypot(ra["se"], rb["se"])
        df = se**4 / ((ra["se"]**4 / max(ra["n_eff"] - 1, 1)) +
                      (rb["se"]**4 / max(rb["n_eff"] - 1, 1)))
        half = stats.t.ppf(0.975, max(df, 1.0)) * se
        p = 2 * stats.t.sf(abs(d) / se, max(df, 1.0))
        out.append(dict(window=w, diff=d, lo=d - half, hi=d + half, p=p))
    return pd.DataFrame(out)


def read_series(out_dir, run, cond, measure="bush_hiding", scale=100.0):
    """One run x condition checkpoint series from a sweep output dir, oldest -> newest."""
    import os
    f = os.path.join(out_dir, run, f"{cond}.csv")
    if not os.path.exists(f):
        return None, None
    d = pd.read_csv(f).sort_values("step")
    return d["step"].to_numpy(), d[measure].to_numpy() * scale
