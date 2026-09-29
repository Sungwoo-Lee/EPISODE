"""When does a quantity "wake up" over training? The registered B2 crossing rule, in pure numpy.

Plain-language purpose: the page "What Both Agents Compute" asks whether the modulator starts
to matter before or after the agent's survival levels off. For one curve (a measure of the
modulator's activity, or survival itself, sampled at every saved checkpoint), this module finds
the first checkpoint where the curve has covered a set fraction of its net change, in the
direction it actually moves, and stays there. It refuses to name a checkpoint when the net
change is within the curve's own noise, when the curve is too short to estimate that noise,
or when no crossing is sustained; each refusal is NaN with a reason, never an exception.
A curve with a missing (non-finite) point is different: the rules assign it no outcome, and a
NaN would silently drop the run from the across-worlds count, so it RAISES, naming the run,
the measure and the checkpoint (Checkpoint R.2, designer item 2).

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
- Positions: every time is also a CHECKPOINT POSITION on one scale, its number in the run's
  manifest checkpoint list (first checkpoint = 1; step 0, the untrained anchor, = 0). An
  anchored curve's array index already is that number; an unanchored curve's index is one less.
  `position` converts a time, never an index, so anchored and unanchored curves compare alike.
- Lag: lag = t_wake - t_plateau in episodes (reported; its sign gives late / early), and
  "coincident" when the two POSITIONS differ by at most `coincident_max_intervals` checkpoints
  (rules B2.lag: "checkpoint intervals ... the resolution of the checkpoint grid"). Positions,
  not an episode width, because level-05 checkpoint spacings jitter by tens of episodes.

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
            noise_window_max_fraction: float, anchored: bool, label: str) -> Result:
    """The registered crossing rule on one curve (see the module docstring).

    `x` and `m` are the curve's full grid, first point first (step 0 if `anchored`). `label`
    names the run and measure (e.g. "l05_w0000_modulated / plateau") for the non-finite raise."""
    if mode not in MODES:
        raise ValueError(f"mode {mode!r}: must be one of {MODES}")
    x = np.asarray(x, dtype=float)
    m = np.asarray(m, dtype=float)
    if x.ndim != 1 or x.shape != m.shape:
        raise ValueError("x and m must be 1-D and the same length")
    if not np.all(np.isfinite(x)):
        raise ValueError(f"{label}: the x grid holds a non-finite value")
    bad = np.flatnonzero(~np.isfinite(m))
    if bad.size:
        pts = ", ".join(f"checkpoint {int(i) if anchored else int(i) + 1} (x = {x[i]:.0f})"
                        for i in bad)
        raise ValueError(f"{label}: curve holds a non-finite point at {pts}; the rules assign no "
                         f"outcome to a missing point (a data defect, not a result)")
    if np.any(np.diff(x) <= 0):
        raise ValueError("x must be strictly increasing")
    if sustain < 1 or final_k < 1:
        raise ValueError("sustain and final_k must be at least 1")
    n = len(m)
    if n < final_k:
        raise ValueError(f"curve of {n} points is shorter than final_k = {final_k}")
    nan = math.nan
    m0 = float(m[0])
    m_final = float(np.mean(m[n - final_k:]))
    window = max(math.ceil(n / noise_window_divisor), min_noise_points + 1)

    def res(t=nan, index=None, direction=None, reason=None, degenerate=False,
            sigma=nan, margin=nan):
        return Result(t=t, index=index, direction=direction, reason=reason,
                      degenerate=degenerate, m0=m0, m_final=m_final, sigma_delta=sigma,
                      window_points=window, guard_margin=margin, anchored=anchored, mode=mode)

    delta = m_final - m0
    direction = "rising" if delta > 0 else ("falling" if delta < 0 else "flat")
    d = float(np.sign(delta))
    window_ok = window <= noise_window_max_fraction * n
    sigma, margin = nan, nan
    if window_ok:
        sigma = float(np.std(np.diff(m[n - window:]), ddof=1))
        margin = (abs(delta) / (noise_k * sigma)) if sigma > 0 else math.inf

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


def position(t: float, checkpoints) -> int:
    """The checkpoint position of time `t` (episodes) on the run's one scale: 0 for step 0 (the
    untrained anchor), i for the i-th entry of the manifest's `checkpoints` (1-based). A time
    that is neither raises (a crossing is always at a grid point)."""
    if t == 0:
        return 0
    cks = [float(c) for c in checkpoints]
    if float(t) not in cks:
        raise ValueError(f"t = {t} is not step 0 and not one of the run's checkpoints")
    return cks.index(float(t)) + 1


def lag(t_wake: float, t_plateau: float, checkpoints,
        coincident_max_intervals: float) -> dict:
    """Rules B2.lag. lag = t_wake - t_plateau in episodes (reported; its sign gives the side),
    and the reading: "coincident" when the checkpoint POSITIONS of the two times (`position`,
    one scale for anchored and unanchored curves) differ by at most `coincident_max_intervals`
    (edge included); otherwise "late" (the measure wakes after survival has levelled off) or
    "early". Either time NaN: lag NaN and reading None.

    Returns {lag, reading, pos_wake, pos_plateau, delta_positions}."""
    if not (math.isfinite(t_wake) and math.isfinite(t_plateau)):
        return {"lag": math.nan, "reading": None, "pos_wake": None, "pos_plateau": None,
                "delta_positions": None}
    pw, pp = position(t_wake, checkpoints), position(t_plateau, checkpoints)
    lg = float(t_wake - t_plateau)
    if abs(pw - pp) <= coincident_max_intervals:
        rd = "coincident"
    else:
        rd = "late" if lg > 0 else "early"
    return {"lag": lg, "reading": rd, "pos_wake": pw, "pos_plateau": pp,
            "delta_positions": pw - pp}
