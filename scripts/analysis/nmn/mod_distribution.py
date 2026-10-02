"""Method 2 — the distribution of the gain and the offset, with sign and zero structure.

Plain-language purpose: at each modulation site the side network emits, every step,
128 multipliers (gains, gamma) and 128 shifts (offsets, beta). The training logs
record only their pooled mean and standard deviation, which cannot tell apart two
completely different behaviours: a modulator that has settled on a fixed per-unit
re-tuning, and one that swings each unit around with context. This module takes the
whole (unit x timestep) table produced by a replay and reports the shape of it.

Three things it reports that a mean cannot
------------------------------------------

**Sign.** Our gain is *linear* -- `gamma * a + beta`, with no sigmoid squashing it
into the positive half-line -- so a gain can be negative, and a negative gain in
front of a rectifier flips which half of the activation distribution survives. That
is a qualitatively different operation from turning a feature down, and a
single-signed gate cannot express it. Perez et al. (2018) report **36% of gains
negative** and **76% of offsets negative** for their trained FiLM generators; those
are the published comparison points.

**Zeros.** Perez also reports "a sharp peak at zero" in the gain histogram -- whole
channels switched off. A near-zero gain is not a small effect; it is a feature being
deleted, and it shows up in a mean as an unremarkable number.

**Where the spread lives.** The pooled standard deviation the training run logs is
the total over units *and* time. It splits exactly:

    Var_{i,t}[gamma] = Var_i( E_t[gamma_it] )  +  E_i( Var_t[gamma_it] )
                       ------ across units ------   ------ across time -----
                       static per-unit re-tuning     contextual modulation

and the second term over the total is the **contextual fraction** `rho`. A modulator
that has degenerated into a fixed re-parameterisation has `rho -> 0` no matter how
far its mean has travelled, and no matter how large its pooled standard deviation
is. The identity is exact whenever every unit is observed at the same timesteps,
which is true here (the alive/dead mask is per timestep, not per unit) -- and it is
asserted, not assumed.

`rho` is a necessary condition, not a sufficient one. Variation the policy does not
use is not modulation; that is what method 3 tests.
"""
from __future__ import annotations

import numpy as np

#: Perez et al. 2018 sec 4.2, via docs/project/references/FiLM/reviews/perez_2018_film.md
PEREZ_FRAC_GAMMA_NEGATIVE = 0.36
PEREZ_FRAC_BETA_NEGATIVE = 0.76

#: |gamma| below this counts as "switched off" for the zero-peak statistic. Perez
#: reports a peak at zero without a threshold; 0.05 is ours, stated so it can be
#: argued with rather than discovered.
ZERO_BAND = 0.05

#: A unit counts as genuinely two-signed only if its minority sign holds at least
#: this share of its live timesteps. Ours, not Perez's; stated so it can be argued
#: with. Without it, one excursion across zero in tens of thousands of steps would
#: label a unit "sign-flipping".
SIGN_MINORITY_BAND = 0.05


def _quantiles(v: np.ndarray, prefix: str) -> dict[str, float]:
    qs = np.quantile(v, [0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99])
    names = ["q01", "q05", "q25", "median", "q75", "q95", "q99"]
    out = {f"{prefix}_{n}": float(q) for n, q in zip(names, qs)}
    out[f"{prefix}_mean"] = float(v.mean())
    out[f"{prefix}_sd"] = float(v.std())
    out[f"{prefix}_min"] = float(v.min())
    out[f"{prefix}_max"] = float(v.max())
    return out


def variance_split(x: np.ndarray, valid: np.ndarray) -> dict[str, float]:
    """Split the spread of a (T, n_ep, H) signal into across-units and across-time.

    Args:
        x: the signal, shape (timesteps, episodes, units).
        valid: (timesteps, episodes) bool -- True where the agent was still alive.

    Returns:
        ``var_total``, ``var_across_units``, ``var_across_time`` and their ratio
        ``rho`` (the contextual fraction). The identity
        ``total = across_units + across_time`` is checked to floating-point
        tolerance and raises if it fails, since a silent violation would mean the
        mask is not shared across units and the decomposition is meaningless.
    """
    if x.ndim != 3:
        raise ValueError(f"expected (T, n_ep, units), got shape {x.shape}")
    if valid.shape != x.shape[:2]:
        raise ValueError(f"valid has shape {valid.shape}, expected {x.shape[:2]}")
    # float64 deliberately: the signals arrive as float32 and a run pools ~10^4
    # timesteps per unit, where float32 accumulation loses enough precision to break
    # the closure check below at the 1e-6 level. Widening the tolerance instead would
    # have hidden a real axis error just as effectively as it hides rounding.
    v = x[valid].astype(np.float64)               # (n_samples, units)
    if v.shape[0] < 2:
        raise ValueError("need at least two valid timesteps to split a variance")
    per_unit_mean = v.mean(axis=0)                # E_t[gamma_it]
    per_unit_var = v.var(axis=0)                  # Var_t[gamma_it]
    total = float(v.var())
    across_units = float(per_unit_mean.var())
    across_time = float(per_unit_var.mean())
    if not np.isclose(total, across_units + across_time, rtol=1e-6, atol=1e-9):
        raise AssertionError(
            f"variance decomposition does not close: total={total!r} vs "
            f"across_units + across_time = {across_units + across_time!r}. This can "
            f"only happen if the valid mask differs between units, which would make "
            f"the split meaningless.")
    return {"var_total": total, "var_across_units": across_units,
            "var_across_time": across_time,
            "rho": float(across_time / total) if total > 0 else float("nan")}


def summarise_site(gamma: np.ndarray, beta: np.ndarray,
                   valid: np.ndarray) -> dict[str, float]:
    """Every method-2 number for one site of one arm.

    Args:
        gamma, beta: (timesteps, episodes, units) signals from `replay.rollout`.
        valid: (timesteps, episodes) alive mask.
    """
    g = gamma[valid]
    b = beta[valid]
    n = int(g.size)

    out: dict[str, float] = {
        "n_values": n,
        "n_units": int(gamma.shape[-1]),
        "n_timesteps": int(valid.sum()),
    }
    out.update(_quantiles(g.ravel(), "gamma"))
    out.update(_quantiles(b.ravel(), "beta"))

    # --- sign and zero structure -------------------------------------------------
    out["frac_gamma_lt1"] = float((g < 1.0).mean())
    out["frac_gamma_negative"] = float((g < 0.0).mean())
    out["frac_gamma_near_zero"] = float((np.abs(g) < ZERO_BAND).mean())
    out["frac_beta_negative"] = float((b < 0.0).mean())
    out["perez_gamma_negative"] = PEREZ_FRAC_GAMMA_NEGATIVE
    out["perez_beta_negative"] = PEREZ_FRAC_BETA_NEGATIVE

    # --- per-unit sign stability -------------------------------------------------
    # A unit whose gain is negative at some times and positive at others is doing
    # something a single-signed gate cannot do. A unit that is always negative has
    # simply had its feature's sign absorbed, which the layer's own weights could
    # equally have done -- so the two are worth counting apart.
    neg_share = (gamma < 0)[valid].mean(axis=0)      # per unit, share of live steps
    always_neg = neg_share == 1.0
    always_pos = neg_share == 0.0
    out["frac_units_gain_always_negative"] = float(always_neg.mean())
    out["frac_units_gain_always_positive"] = float(always_pos.mean())
    out["frac_units_gain_sign_flips"] = float((~(always_neg | always_pos)).mean())
    # The line above is a weak criterion: with tens of thousands of live timesteps
    # per unit, ONE excursion across zero makes a unit "flipping". The robust
    # version asks that the minority sign hold for a non-trivial share of the time,
    # so a unit only counts if BOTH signs are part of what it actually does.
    out["frac_units_gain_sign_flips_5pct"] = float(
        ((neg_share >= SIGN_MINORITY_BAND) & (neg_share <= 1 - SIGN_MINORITY_BAND)).mean())
    out["frac_units_gain_negative_share_mean"] = float(neg_share.mean())
    out["frac_units_mean_gain_negative"] = float((gamma[valid].mean(axis=0) < 0).mean())
    out["frac_units_mean_gain_lt1"] = float((gamma[valid].mean(axis=0) < 1).mean())

    # --- where the spread lives --------------------------------------------------
    for name, arr in (("gamma", gamma), ("beta", beta)):
        for k, v in variance_split(arr, valid).items():
            out[f"{name}_{k}"] = v
    return out


def histogram(x: np.ndarray, valid: np.ndarray, bins: int = 80,
              lo: float | None = None, hi: float | None = None) -> dict:
    """Counts for plotting the distribution, on a range shared across arms."""
    v = x[valid].ravel()
    lo = float(np.quantile(v, 0.001)) if lo is None else lo
    hi = float(np.quantile(v, 0.999)) if hi is None else hi
    counts, edges = np.histogram(v, bins=bins, range=(lo, hi))
    return {"counts": counts.tolist(), "edges": edges.tolist(),
            "n_below_range": int((v < lo).sum()), "n_above_range": int((v > hi).sum())}
