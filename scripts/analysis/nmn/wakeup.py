"""When does a quantity "wake up" over training? The registered B2 crossing rule, in pure numpy.

Plain-language purpose: the page "What Both Agents Compute" asks whether the modulator starts
to matter before or after the agent's survival levels off. For one curve (a measure of the
modulator's activity, or survival itself, sampled at every saved checkpoint), this module finds
the first checkpoint where the curve has covered a set fraction of its net change, in the
direction it actually moves, and stays there. It refuses to name a checkpoint when the net
change is within the curve's own noise, when the curve is too short to estimate that noise,
or when no crossing is sustained; each refusal is NaN with a reason, never an exception.

Every number comes from the caller, which reads them from `parameters.B2` of the sha-pinned
rules file (docs/experiments/active/modulator_clues/algorithmic_null_decision_rules.yaml,
section 8b). There are no defaults, and a test fails on any numeric literal in this file other
than 0 and 1. The across-worlds reading (the sign test) is `decision_rules.evaluate_B2`, not
here.

The rule, as registered (B2.definition / headline_wake_point / literal_beside / plateau / lag):
- m0 = the first point of the curve (step 0, the untrained network, where the measure is
  anchorable; otherwise the first checkpoint; `anchored` records which). m_final = mean of the
  last `final_k` points. d = sign(m_final - m0).
- Noise window = the last max(ceil(N / noise_window_divisor), min_noise_points + 1) points
  (N counts every point, step 0 included). If that exceeds noise_window_max_fraction x N:
  NaN, "too few points to estimate noise". sigma_delta = SD of consecutive differences over
  the window.
- Guard: |m_final - m0| <= noise_k x sigma_delta -> NaN, "net change within the measure's own
  noise band".
- fraction_of_rise (headline): the first x_i with d x (m_i - m0) >= f x |m_final - m0| holding
  at `sustain` consecutive points; none -> NaN, "no sustained crossing".
- fraction_of_final (literal, reported beside): the first x_i with m_i >= f x m_final, at
  `sustain` consecutive points; flagged degenerate when m0 already satisfies it or d is
  falling. The noise estimate is reported with it, but the guard and window refusal belong to
  the headline rule only (the rules state neither for the literal).

Plan: docs/develop/active/neuromodulation/ALGORITHMIC_NULL_ANALYSIS_TOOLING.md, File Changes §11
and §B2 "Wake-up definition".
"""
from __future__ import annotations

import math
from dataclasses import dataclass, asdict

import numpy as np

MODES = ("fraction_of_rise", "fraction_of_final")
R_TOO_FEW = "too few points to estimate noise"
R_NOISE = "net change within the measure's own noise band"
R_NO_SUSTAIN = "no sustained crossing"
R_NAN_INPUT = "curve holds a non-finite point"


@dataclass
class Result:
    t: float                    # the crossing's x (episodes), or NaN
    index: int | None           # position of t in the grid, or None
    direction: str | None       # "rising" / "falling" / "flat"
    reason: str | None          # None, or why t is NaN
    degenerate: bool            # literal mode: m0 already satisfies it, or d falling
    m0: float
    m_final: float
    sigma_delta: float          # NaN when the window is refused
    window_points: int
    guard_margin: float         # |m_final - m0| / (noise_k * sigma_delta)
    anchored: bool              # m0 is step 0 (the untrained network), not a checkpoint
    mode: str

    def as_dict(self) -> dict:
        return asdict(self)


def _first_sustained(ok: np.ndarray, sustain: int) -> int | None:
    n = len(ok)
    for i in range(n - sustain + 1):
        if bool(np.all(ok[i:i + sustain])):
            return i
    return None


def t_cross(x, m, *, mode: str, f: float, sustain: int, final_k: int, noise_k: float,
            min_noise_points: int, noise_window_divisor: float,
            noise_window_max_fraction: float, anchored: bool) -> Result:
    """The registered crossing rule on one curve (see the module docstring).

    `x` and `m` are the curve's full grid, first point first (step 0 if `anchored`)."""
    if mode not in MODES:
        raise ValueError(f"mode {mode!r}: must be one of {MODES}")
    x = np.asarray(x, dtype=float)
    m = np.asarray(m, dtype=float)
    if x.ndim != 1 or x.shape != m.shape:
        raise ValueError("x and m must be 1-D and the same length")
    if np.any(np.diff(x) <= 0):
        raise ValueError("x must be strictly increasing")
    if sustain < 1 or final_k < 1:
        raise ValueError("sustain and final_k must be at least 1")
    n = len(m)
    if n < final_k:
        raise ValueError(f"curve of {n} points is shorter than final_k = {final_k}")
    nan = float("nan")
    m0 = float(m[0])
    m_final = float(np.mean(m[n - final_k:]))
    window = max(math.ceil(n / noise_window_divisor), min_noise_points + 1)

    def res(t=nan, index=None, direction=None, reason=None, degenerate=False,
            sigma=nan, margin=nan):
        return Result(t=t, index=index, direction=direction, reason=reason,
                      degenerate=degenerate, m0=m0, m_final=m_final, sigma_delta=sigma,
                      window_points=window, guard_margin=margin, anchored=anchored, mode=mode)

    if not np.all(np.isfinite(m)):
        return res(reason=R_NAN_INPUT)
    delta = m_final - m0
    direction = "rising" if delta > 0 else ("falling" if delta < 0 else "flat")
    d = float(np.sign(delta))
    window_ok = window <= noise_window_max_fraction * n
    sigma, margin = nan, nan
    if window_ok:
        sigma = float(np.std(np.diff(m[n - window:]), ddof=1))
        margin = (abs(delta) / (noise_k * sigma)) if sigma > 0 else float("inf")

    if mode == "fraction_of_rise":
        if not window_ok:
            return res(direction=direction, reason=R_TOO_FEW)
        if abs(delta) <= noise_k * sigma:
            return res(direction=direction, reason=R_NOISE, sigma=sigma, margin=margin)
        ok = d * (m - m0) >= f * abs(delta)
        i = _first_sustained(ok, sustain)
        if i is None:
            return res(direction=direction, reason=R_NO_SUSTAIN, sigma=sigma, margin=margin)
        return res(t=float(x[i]), index=int(i), direction=direction, sigma=sigma, margin=margin)

    # fraction_of_final (literal)
    thr = f * m_final
    ok = m >= thr
    degenerate = bool(m0 >= thr) or direction == "falling"
    i = _first_sustained(ok, sustain)
    if i is None:
        return res(direction=direction, reason=R_NO_SUSTAIN, degenerate=degenerate,
                   sigma=sigma, margin=margin)
    return res(t=float(x[i]), index=int(i), direction=direction, degenerate=degenerate,
               sigma=sigma, margin=margin)


def lag(t_wake: float, t_plateau: float, interval: float,
        coincident_max_intervals: float) -> tuple[float, str | None]:
    """lag = t_wake - t_plateau in episodes, and its reading: "late" (the measure wakes after
    survival has levelled off), "early", or "coincident" when |lag| is within
    `coincident_max_intervals` checkpoint intervals of length `interval` (edge included).
    NaN and None when either time is NaN."""
    if not (math.isfinite(t_wake) and math.isfinite(t_plateau)):
        return float("nan"), None
    if not interval > 0:
        raise ValueError(f"interval must be positive, got {interval}")
    lg = float(t_wake - t_plateau)
    band = coincident_max_intervals * interval
    if abs(lg) <= band:
        return lg, "coincident"
    return lg, ("late" if lg > 0 else "early")
