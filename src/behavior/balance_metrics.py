"""Balance metrics for rPPO training logs (pure NumPy, no JAX).

Plain-language purpose
----------------------
The internal-state interaction study asks whether a world is *balanced*: the agent has
to hide in bushes to heal, eat, and warm up by a fire, each takes a real share of its
time, and each need drives its own behaviour (hungry agents eat more, badly injured
agents hide more, cold agents warm up more). This module turns per-step rollout data
into those measures:

- time shares: in a bush, on a warm cell, eating, elsewhere (plus the report-only
  "near the fire but not warm" share);
- eat / hide / warm-up rates split by body state, hiding split by true injury and by
  the injury the agent actually feels;
- the hiding gap for hungry versus fed agents;
- early- versus late-death shares.

Training (`train.py`, rPPO branch) calls `step_counts` on arrays built from the rollout's
`StepInfo`, accumulates the per-step counters per episode, and calls `window_log` /
`late_death_log` when it emits an `Episode/*` row. The functions are pure, so they
never touch training itself.

Definitions come from the study plan (docs/experiments/active/internal_state_interactions/STUDY_PLAN.md,
Revisions 2, 2a, 2b, 2c) and the implementation plan
docs/develop/active/behavior/BALANCE_METRICS_TRAINING_LOGGING.md (A2-A7).

Timing convention (the contemporaneous-binning guard, plan A2)
--------------------------------------------------------------
The body-state *predictor* (nutrition, injury, felt injury, body temperature) is read
from the PRE-step state -- the state the agent observed when it chose its action. The
*outcome* (in a bush, on a warm cell, ate) is read from this step's post-step result.
Binning on the post-step body state is the mistake recorded three times in the Known
Bugs registry ("contemporaneous binning").

Felt injury (plan A3)
---------------------
"Felt" injury is the environment's own interoceptive-nociception percept (noise-free),
multiplied by `max_injury` so the same injury thresholds apply. The percept's buffer is
zeroed at reset and covers the last `interoceptive_kernel_length` (12) steps, so it
under-reads for roughly the first 12 steps of EVERY episode. In worlds with random
starting injury (level 05) this inflates `Bal_N_InjLo_Felt` at episode starts by
construction and pulls `Bal_HideRatio_Felt` down for a reason unrelated to the policy.
These steps are kept on purpose; true injury decides the hiding criterion.

Warm cell (plan A4)
-------------------
A step is "warm" when the cell the agent lands on is above the body-temperature
setpoint (a property of the cell, not of the body). "Near fire" is a cell the fire
heats (above the upper edge of the open-ground temperature range) but that is still at
or below the setpoint -- the fire's outer (blurred) ring. It is report-only.

Thresholds are absolute units calibrated to the level-05 body (max nutrition 200, max
injury 100). They are constants on purpose: runs must stay comparable. Every run records
the calibration it was measured under (`calibration_record`).
"""
from __future__ import annotations

from typing import Iterable, Sequence

import numpy as np

# ---------------------------------------------------------------------------
# Bin edges (study plan Rev 2 / 2a / 2b; planner.py rollout_balance). Absolute units.
# ---------------------------------------------------------------------------
HUNGRY_LT = 60.0      # hungry: pre-step nutrition N < 60           (Rev 2a C1(a))
FED_GE = 100.0        # fed:    pre-step nutrition N >= 100         (Rev 2a C1(a))
COMB_FED_LO = 80.0    # combination "fed": 80 <= N <= 160           (Rev 2 B-hide)
COMB_FED_HI = 160.0
INJ_HI_GE = 60.0      # badly injured: I >= 60                      (Rev 2a C1(c))
INJ_LO_LE = 20.0      # barely injured: I <= 20                     (Rev 2a C1(c))
COLD_LE = -5.0        # cold body: T <= -5 degC                     (Rev 2b (b'))
WARM_GE = 0.0         # warm body: T >= 0 degC                      (Rev 2b (b'))

# Reason codes (core.py jnp.where chain; src/behavior/episode_metrics.py).
_DEATH_CAUSES = ((2, "Starvation"), (3, "Overeating"), (4, "Injury"), (5, "Thermal"))

_HIDE = ("n_inj_hi", "bush_inj_hi", "n_inj_lo", "bush_inj_lo")
COUNTER_NAMES = (
    ("steps",
     "bush", "warm", "eat", "elsewhere",
     "n_hungry", "eat_hungry", "n_fed", "eat_fed")
    + tuple(f"{c}_true" for c in _HIDE)
    + tuple(f"{c}_felt" for c in _HIDE)
    + ("n_cold", "warm_cold", "n_warmT", "warm_warmT")
    + tuple(f"{c}_true_{f}" for f in ("hungry", "fed") for c in _HIDE)
    + tuple(f"{c}_felt_{f}" for f in ("hungry", "fed") for c in _HIDE)
    + ("near_fire",)
)
K = len(COUNTER_NAMES)
IDX = {name: i for i, name in enumerate(COUNTER_NAMES)}
assert K == 38, K


# ---------------------------------------------------------------------------
# Config resolution (no defaults)
# ---------------------------------------------------------------------------
def resolve_balance_metrics_flag(config) -> bool:
    """`logging.episode.balance_metrics` -- mandatory, must be a real bool."""
    val = config.get_mandatory('logging.episode.balance_metrics')
    if not isinstance(val, bool):
        raise ValueError(
            "Strict Config: 'logging.episode.balance_metrics' must be true or false, "
            f"got {val!r} ({type(val).__name__}).")
    return val


def resolve_early_death_max_steps(config) -> int:
    """`logging.episode.balance_early_death_max_steps` -- mandatory when the balance
    switch is on. An episode that dies at length <= this value is an "early" death
    (excluded from the late-death criterion). Must be a non-negative int."""
    key = 'logging.episode.balance_early_death_max_steps'
    val = config.get_mandatory(key)
    if isinstance(val, bool) or not isinstance(val, int) or val < 0:
        raise ValueError(
            f"Strict Config: '{key}' must be a non-negative integer, got {val!r}.")
    return val


def calibration_record(params, *, thermal_on: bool, felt_on: bool,
                       early_death_max_steps: int) -> dict:
    """The calibration a run's balance metrics were measured under (plan A5).

    `max_nutrition` / `max_injury` (and, with thermal on, `temperature_setpoint` /
    `thermal_default_temp_high`) are read from the live `params` by attribute access --
    a missing attribute raises, there is no default. Bin edges come from the module
    constants; the early-death cut-off comes from the config.
    """
    rec = {
        "max_nutrition": float(params.max_nutrition),
        "max_injury": float(params.max_injury),
        "HUNGRY_LT": HUNGRY_LT, "FED_GE": FED_GE,
        "COMB_FED_LO": COMB_FED_LO, "COMB_FED_HI": COMB_FED_HI,
        "INJ_HI_GE": INJ_HI_GE, "INJ_LO_LE": INJ_LO_LE,
        "COLD_LE": COLD_LE, "WARM_GE": WARM_GE,
        "early_death_max_steps": int(early_death_max_steps),
        "thermal_on": bool(thermal_on),
        "felt_on": bool(felt_on),
    }
    if thermal_on:
        rec["temperature_setpoint"] = float(params.temperature_setpoint)
        rec["thermal_default_temp_high"] = float(params.thermal_default_temp_high)
    return rec


# ---------------------------------------------------------------------------
# Per-step counters
# ---------------------------------------------------------------------------
def step_counts(nutrition, injury, felt_injury, body_temp, on_warm_cell, near_fire,
                ate_food, in_bush, *, thermal_on: bool, felt_on: bool) -> np.ndarray:
    """Per-step 0/1 counters, shape `(*lead, K)` uint8, order `COUNTER_NAMES`.

    All inputs share one leading shape (`[T, B]` in training). Body-state inputs are
    PRE-step values; `ate_food`, `in_bush`, `on_warm_cell`, `near_fire` are this step's
    outcome. `felt_injury` must be None exactly when `felt_on` is False, and
    `body_temp` / `on_warm_cell` / `near_fire` exactly when `thermal_on` is False.
    """
    for name, v, on in (("felt_injury", felt_injury, felt_on),
                        ("body_temp", body_temp, thermal_on),
                        ("on_warm_cell", on_warm_cell, thermal_on),
                        ("near_fire", near_fire, thermal_on)):
        if (v is None) == bool(on):
            raise ValueError(f"step_counts: {name} is {'None' if v is None else 'set'} "
                             f"but its flag is {bool(on)}")

    n = np.asarray(nutrition)
    i_true = np.asarray(injury)
    bush = np.asarray(in_bush) != 0
    eat = np.asarray(ate_food) != 0
    zeros = np.zeros(n.shape, dtype=bool)
    if thermal_on:
        warm = np.asarray(on_warm_cell) != 0
        near = np.asarray(near_fire) != 0
        t = np.asarray(body_temp)
        cold, warm_t = t <= COLD_LE, t >= WARM_GE
    else:
        warm = near = cold = warm_t = zeros

    hungry = n < HUNGRY_LT
    fed = n >= FED_GE
    comb_fed = (n >= COMB_FED_LO) & (n <= COMB_FED_HI)

    def hide(i_arr):
        hi, lo = i_arr >= INJ_HI_GE, i_arr <= INJ_LO_LE
        return hi, lo

    def hide_block(hi, lo, restrict=None):
        if restrict is not None:
            hi, lo = hi & restrict, lo & restrict
        return [hi, hi & bush, lo, lo & bush]

    hi_t, lo_t = hide(i_true)
    if felt_on:
        hi_f, lo_f = hide(np.asarray(felt_injury))
    else:
        hi_f = lo_f = zeros

    cols = (
        [np.ones(n.shape, dtype=bool),
         bush, warm, eat, ~(bush | warm | eat),
         hungry, hungry & eat, fed, fed & eat]
        + hide_block(hi_t, lo_t)
        + hide_block(hi_f, lo_f)
        + [cold, cold & warm, warm_t, warm_t & warm]
        + hide_block(hi_t, lo_t, hungry) + hide_block(hi_t, lo_t, comb_fed)
        + hide_block(hi_f, lo_f, hungry) + hide_block(hi_f, lo_f, comb_fed)
        + [near]
    )
    assert len(cols) == K
    return np.stack(cols, axis=-1).astype(np.uint8)


# ---------------------------------------------------------------------------
# Window aggregation -> WandB keys (plan A6: ratio of pooled sums)
# ---------------------------------------------------------------------------
def _share(num, den):
    return float(num) / float(den) if den > 0 else None


def _put(out, key, val):
    if val is not None:
        out[key] = val


def _ratio(hi_share, lo_share):
    if hi_share is None or lo_share is None or lo_share == 0:
        return None
    return hi_share / lo_share


def window_log(counts_list: Sequence[np.ndarray], *, thermal_on: bool,
               felt_on: bool) -> dict:
    """Sum per-episode counters over the window and emit `Episode/Bal_*` keys.

    Ratio of pooled sums (never a mean of per-episode ratios). A share / ratio / gap
    whose denominator bin is empty in the window is omitted; `N` (window-total step
    count) keys are always emitted, including 0. A ratio is omitted when the "off"
    bin's share is 0. Warm keys are absent with thermal off, `_Felt` keys with felt
    injury off.
    """
    if len(counts_list) == 0:
        return {}
    c = np.sum(np.stack([np.asarray(x, dtype=np.int64) for x in counts_list]), axis=0)
    g = lambda name: int(c[IDX[name]])
    out: dict = {}
    p = "Episode/Bal_"

    steps = g("steps")
    _put(out, p + "TimeBush", _share(g("bush"), steps))
    _put(out, p + "TimeEat", _share(g("eat"), steps))
    _put(out, p + "TimeElsewhere", _share(g("elsewhere"), steps))
    if thermal_on:
        _put(out, p + "TimeWarm", _share(g("warm"), steps))
        _put(out, p + "TimeNearFire", _share(g("near_fire"), steps))

    # Eating vs hunger
    out[p + "N_Hungry"] = float(g("n_hungry"))
    out[p + "N_Fed"] = float(g("n_fed"))
    eh = _share(g("eat_hungry"), g("n_hungry"))
    ef = _share(g("eat_fed"), g("n_fed"))
    _put(out, p + "EatShare_Hungry", eh)
    _put(out, p + "EatShare_Fed", ef)
    _put(out, p + "EatRatio", _ratio(eh, ef))

    # Hiding vs injury (+ combination with nutrition)
    sources = [("True", "true")] + ([("Felt", "felt")] if felt_on else [])
    for S, s in sources:
        out[f"{p}N_InjHi_{S}"] = float(g(f"n_inj_hi_{s}"))
        out[f"{p}N_InjLo_{S}"] = float(g(f"n_inj_lo_{s}"))
        hi = _share(g(f"bush_inj_hi_{s}"), g(f"n_inj_hi_{s}"))
        lo = _share(g(f"bush_inj_lo_{s}"), g(f"n_inj_lo_{s}"))
        _put(out, f"{p}BushShare_InjHi_{S}", hi)
        _put(out, f"{p}BushShare_InjLo_{S}", lo)
        _put(out, f"{p}HideRatio_{S}", _ratio(hi, lo))
        for F, f in (("Hungry", "hungry"), ("Fed", "fed")):
            out[f"{p}N_InjHi_{S}_{F}"] = float(g(f"n_inj_hi_{s}_{f}"))
            out[f"{p}N_InjLo_{S}_{F}"] = float(g(f"n_inj_lo_{s}_{f}"))
            hi_f = _share(g(f"bush_inj_hi_{s}_{f}"), g(f"n_inj_hi_{s}_{f}"))
            lo_f = _share(g(f"bush_inj_lo_{s}_{f}"), g(f"n_inj_lo_{s}_{f}"))
            _put(out, f"{p}BushShare_InjHi_{S}_{F}", hi_f)
            _put(out, f"{p}BushShare_InjLo_{S}_{F}", lo_f)
            if hi_f is not None and lo_f is not None:
                out[f"{p}HideGap_{S}_{F}"] = hi_f - lo_f
            _put(out, f"{p}HideRatio_{S}_{F}", _ratio(hi_f, lo_f))

    # Warming vs body temperature
    if thermal_on:
        out[p + "N_Cold"] = float(g("n_cold"))
        out[p + "N_Warm"] = float(g("n_warmT"))
        wc = _share(g("warm_cold"), g("n_cold"))
        ww = _share(g("warm_warmT"), g("n_warmT"))
        _put(out, p + "WarmShare_Cold", wc)
        _put(out, p + "WarmShare_Warm", ww)
        _put(out, p + "WarmRatio", _ratio(wc, ww))
    return out


def late_death_log(lengths: Iterable[int], reasons: Iterable[int], *,
                   early_death_max_steps: int) -> dict:
    """Early / late death shares over ALL window episodes (plan A7, study Rev 2b N5).

    A death is reason code 2-5. Early = death at length <= `early_death_max_steps`;
    late = death at a longer length. `Bal_EarlyDeathShare` / `Bal_LateDeathShare` divide
    by all window episodes (truncations and early deaths included). The four cause
    shares are among late deaths and are omitted when there are none.
    """
    l = np.asarray(list(lengths), dtype=np.int64)
    r = np.asarray(list(reasons), dtype=np.int64)
    if l.size == 0:
        return {}
    death = (r >= 2) & (r <= 5)
    early = death & (l <= early_death_max_steps)
    late = death & (l > early_death_max_steps)
    n_late = int(late.sum())
    out = {
        "Episode/Bal_EarlyDeathShare": float(early.sum()) / l.size,
        "Episode/Bal_LateDeathShare": float(n_late) / l.size,
    }
    if n_late > 0:
        for code, name in _DEATH_CAUSES:
            out[f"Episode/Bal_LateDeath_{name}"] = float((late & (r == code)).sum()) / n_late
    return out
