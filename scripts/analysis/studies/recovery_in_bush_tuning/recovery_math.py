#!/usr/bin/env python3
"""recovery_math.py - the closed form of injury recovery, and the study's thresholds.

WHAT THIS IS. Every figure and every number on the recovery_in_bush_tuning page comes from this
one module, so a change to the arithmetic moves the whole page at once and cannot move one figure
without moving its caption. It is NOT a figure script: it draws nothing.

THE ARITHMETIC IT IMPLEMENTS, transcribed from src/environment/core.py::update_body (the lines are
quoted in `SOURCE_LINES` below so a reader can diff them against the file):

    streak(t)       = rested ? streak(t-1) + 1 : 0
    recovery_amount = recovery_base_rate * (1 + recovery_accel_rate) ** (max(streak,1) - 1)
    if recovery_in_bush_multiplier != 1.0 and in_bush:  recovery_amount *= multiplier
    can_recover     = rested AND applied_inc <= 0
    new_injury      = clip(injury + applied_inc - recovery_amount * can_recover, 0, max_injury)

Two properties of that recurrence do the work:

  * the per-step heal on the n-th CONSECUTIVE rest step is `base * (1+accel)**(n-1)`, because the
    streak is 1 on the first rest step and the exponent is `streak - 1`;
  * therefore the CUMULATIVE heal over n consecutive rest steps is a geometric sum,
    `base * n` when accel == 0 and `base * ((1+accel)**n - 1) / accel` otherwise.
    Both are derived here (`cumulative`), never typed as a number anywhere.

WHERE THE REFERENCE VALUES COME FROM. They are read out of the YAML, not transcribed: the shipped
defaults from `configs/environment/default.yaml`, and the flat-rate arm of the rest-premium sweep
from `configs/environment/experiment/archive/basic_bushrefuge_restpremium/04-restprem_a01.yaml`.
If somebody edits those files, the page moves with them.

WHAT IT DELIBERATELY DOES NOT MODEL. Damage. `can_recover` requires `applied_inc <= 0`, and injury
smoothing spreads a hit over `injury_smoothing_duration` steps, so the first few rest steps after a
hit heal nothing while the streak keeps climbing. Everything here describes an agent that is
already hurt and is taking no new damage, which is the case the study's definition is about and the
case f05 measures in the real environment.
"""
from __future__ import annotations

import os

import numpy as np
import yaml

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", "..", ".."))

DEFAULT_YAML = os.path.join(ROOT, "configs", "environment", "default.yaml")
A01_YAML = os.path.join(
    ROOT, "configs", "environment", "experiment", "archive",
    "basic_bushrefuge_restpremium", "04-restprem_a01.yaml")
RANDOM_START_YAML = os.path.join(
    ROOT, "configs", "environment", "experiment", "archive",
    "basic_bushrefuge", "03-random_init_10x10.yaml")

SOURCE_FILE = "src/environment/core.py"
SOURCE_LINES = "226-266"


# ── the shipped numbers, read from the YAML rather than transcribed ────────────────────────────
def _yaml(path):
    with open(path) as fh:
        return yaml.safe_load(fh)


def _need(d, *path):
    """Read a nested key or raise - the project's no-fallback-defaults rule, in an analysis script.

    A missing key here would silently turn a measured reference point into whatever default the
    author happened to choose, which is exactly the failure mode the rule exists to stop.
    """
    cur = d
    for k in path:
        if not isinstance(cur, dict) or k not in cur:
            raise ValueError(
                f"recovery_math: {'.'.join(path)} is missing from the config being read; "
                f"this analysis has no fallback default for it")
        cur = cur[k]
    return cur


_D = _yaml(DEFAULT_YAML)
_A = _yaml(A01_YAML)
_R = _yaml(RANDOM_START_YAML)

MAX_INJURY = float(_need(_D, "body", "max_injury"))
MAX_NUTRITION = float(_need(_D, "body", "max_nutrition"))
METABOLIC_COST = float(_need(_D, "body", "metabolic_cost"))
MAX_STEPS = int(_need(_D, "environment", "max_steps"))
SMOOTHING_DURATION = int(_need(_D, "body", "injury_smoothing_duration"))
SETPOINT = float(_need(_D, "body", "satiation_setpoint"))

# The two shipped reference settings.
SHIPPED = dict(base=float(_need(_D, "body", "recovery_base_rate")),
               accel=float(_need(_D, "body", "recovery_accel_rate")),
               mult=float(_need(_D, "body", "recovery_in_bush_multiplier")),
               label="shipped default")
A01 = dict(base=float(_need(_A, "body", "recovery_base_rate")),
           accel=float(_need(_A, "body", "recovery_accel_rate")),
           mult=float(_need(_D, "body", "recovery_in_bush_multiplier")),
           label="rest-premium arm a01")

# Start-nutrition regimes, both real and both read from a shipped file. The rest budget follows.
START_NUTRITION_FIXED = float(_need(_D, "body", "start_nutrition"))
START_NUTRITION_LOW = float(_need(_R, "body", "start_nutrition_low"))
START_NUTRITION_HIGH = float(_need(_R, "body", "start_nutrition_high"))
RANDOM_START_NUTRITION = bool(_need(_R, "body", "random_start_nutrition"))


def rest_budget(nutrition: float) -> float:
    """Consecutive rest steps a resting agent can afford, given nutrition now.

    A resting agent eats nothing (rest is action 4; eating is action 5 while `eat_action_enabled`
    is true), and nutrition falls by `metabolic_cost` every step, so the agent starves after
    `nutrition / metabolic_cost` of them. It is an UPPER bound in the strongest sense: an agent
    that actually spends the whole budget is dead at the end of it.
    """
    return nutrition / METABOLIC_COST


#: The primary budget: the median of a uniform [0, 100] start nutrition, which is the draw the
#: random-init worlds use. 50 steps at metabolic_cost 1.0.
BUDGET = rest_budget(0.5 * (START_NUTRITION_LOW + START_NUTRITION_HIGH))
#: The budget in a world that does NOT randomise start nutrition - `default.yaml` starts at 100.
BUDGET_FIXED_START = rest_budget(START_NUTRITION_FIXED)

#: θ - the injury the open must NOT be able to clear within the budget. A CHOICE, not a fact:
#: a quarter of the 0-100 injury scale, and roughly the smallest single predator hit
#: (`damage: [15, 120]` on the jump-attack world).
THETA = 25.0
#: The wound cover must be able to close, and the rest steps it may take. Also choices; the
#: 70-point wound and the ~14-step close are the calibration the rest-premium sweep was solved to.
WOUND = 70.0
COVER_STEPS = 25.0
#: Advisory only, NOT part of the definition: below this many rest steps for the 70-point wound,
#: cover stops being a place to convalesce and becomes a heal button.
COVER_STEPS_FLOOR = 5.0


# ── the closed form ───────────────────────────────────────────────────────────────────────────
def per_step(n, base: float, accel: float, mult: float = 1.0):
    """Injury healed on the n-th CONSECUTIVE rest step (n = 1 is the first)."""
    n = np.asarray(n, dtype=float)
    return base * mult * np.power(1.0 + accel, n - 1.0)


def cumulative(n, base: float, accel: float, mult: float = 1.0):
    """Injury healed over n consecutive rest steps, before the clip at injury 0.

    Geometric sum of `per_step`. The accel == 0 branch is the limit of the other as accel -> 0
    (`((1+a)**n - 1)/a -> n`), written out separately because the general form divides by accel.
    """
    n = np.asarray(n, dtype=float)
    if accel == 0.0:
        return base * mult * n
    return base * mult * (np.power(1.0 + accel, n) - 1.0) / accel


def cumulative_grid(n, base, accel, mult=1.0):
    """`cumulative` over arrays of base and accel, with the accel == 0 row handled by the limit."""
    n = np.asarray(n, dtype=float)
    base = np.asarray(base, dtype=float)
    accel = np.asarray(accel, dtype=float)
    safe = np.where(accel == 0.0, 1.0, accel)          # avoid a 0/0 inside the unused branch
    geo = (np.power(1.0 + safe, n) - 1.0) / safe
    return base * mult * np.where(accel == 0.0, n, geo)


def healable(n, base, accel, mult=1.0, max_injury=None):
    """`cumulative`, clipped at the injury scale - injury is clipped to [0, max_injury] each step.

    An agent cannot heal more than it is hurt, and the largest it can be hurt is `max_injury`, so
    the most any setting can clear in n steps is `min(cumulative, max_injury)`.
    """
    m = MAX_INJURY if max_injury is None else max_injury
    return np.minimum(cumulative_grid(n, base, accel, mult), m)


def steps_to_heal(target: float, base: float, accel: float, mult: float = 1.0):
    """Consecutive rest steps needed to clear `target` injury points. Inverse of `cumulative`.

    Returns a float (fractional steps); the environment takes whole steps, so the honest reading is
    `ceil`. Returns `inf` where the target is unreachable, which cannot happen for accel >= 0 and
    base > 0 but is left explicit so the caller is never handed a silent NaN.
    """
    base = np.asarray(base, dtype=float)
    accel = np.asarray(accel, dtype=float)
    rate = base * mult
    with np.errstate(divide="ignore", invalid="ignore"):
        linear = target / rate
        safe = np.where(accel == 0.0, 1.0, accel)
        expo = np.log1p(target * safe / rate) / np.log1p(safe)
        out = np.where(accel == 0.0, linear, expo)
    return np.where(np.isfinite(out), out, np.inf)


# ── the two conditions the study turns on ─────────────────────────────────────────────────────
def open_healable(base, accel, budget: float = None):
    """Injury points a continuously-resting agent can clear IN THE OPEN within its rest budget."""
    return healable(BUDGET if budget is None else budget, base, accel, 1.0)


def open_is_unrecoverable(base, accel, budget: float = None, theta: float = None):
    """Condition A: resting outside cover cannot clear more than θ of the injury scale."""
    return open_healable(base, accel, budget) <= (THETA if theta is None else theta)


def cover_steps_for_wound(base, accel, mult, wound: float = None):
    """Consecutive rest steps a bush needs to close a `wound`-point injury."""
    return steps_to_heal(WOUND if wound is None else wound, base, accel, mult)


def cover_is_usable(base, accel, mult, wound: float = None, steps: float = None):
    """Condition B: a bush closes a typical wound inside the stated number of rest steps."""
    return cover_steps_for_wound(base, accel, mult, wound) <= (
        COVER_STEPS if steps is None else steps)


def feasible(base, accel, mult, budget: float = None):
    """Both conditions at once - the shaded region of f03."""
    return np.logical_and(open_is_unrecoverable(base, accel, budget),
                          cover_is_usable(base, accel, mult))


# ── the recommendation, chosen by a stated rule rather than by eye ────────────────────────────
#: The grid the rule searches. Round numbers only: a config value nobody can read aloud is a
#: config value that gets mistyped.
REC_BASES = (0.05, 0.1, 0.125, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5)
REC_MULTS = (2.0, 4.0, 5.0, 8.0, 10.0, 12.5, 16.0, 20.0, 25.0, 40.0, 50.0)
#: The healing rate inside cover that the recommendation is anchored to: the flat rate the
#: rest-premium sweep already calibrated, so the injured window matches an experiment that ran.
ANCHOR_COVER_RATE = A01["base"]


def recommend():
    """Pick (base, accel, multiplier) by the rule stated below, and return the evidence with it.

    THE RULE, in four clauses, applied in order:

      1. `accel = 0`. f04 is the evidence: a positive accel makes the open's healing compound, and
         at any base large enough to be useful in cover it crosses θ inside the budget.
      2. The healing rate INSIDE cover equals `ANCHOR_COVER_RATE` (the a01 arm's flat 5.0 per
         step), so a 70-point wound closes in the same ~14 rest steps that sweep was solved to.
      3. Both conditions must hold at BOTH budgets - the 50-step median of a randomised start AND
         the 100-step budget of a world that starts at full nutrition - with strict inequality, so
         the recommendation does not sit on its own boundary.
      4. Among what survives, take the LARGEST base, i.e. the SMALLEST multiplier: the weakest
         intervention that still does the job.
    """
    cands = []
    for b in REC_BASES:
        for m in REC_MULTS:
            if abs(b * m - ANCHOR_COVER_RATE) > 1e-9:
                continue                                        # clause 2
            ok = True
            for budget in (BUDGET, BUDGET_FIXED_START):         # clause 3
                if not open_healable(b, 0.0, budget) < THETA:
                    ok = False
            if not cover_steps_for_wound(b, 0.0, m) < COVER_STEPS:
                ok = False
            if cover_steps_for_wound(b, 0.0, m) < COVER_STEPS_FLOOR:
                ok = False                                      # advisory ceiling
            if ok:
                cands.append((b, m))
    if not cands:
        raise ValueError(
            "recovery_math.recommend: no (base, multiplier) on the round-number grid satisfies "
            "the rule - the thresholds and the grid disagree, and one of them must change")
    base, mult = max(cands, key=lambda bm: bm[0])                # clause 4
    return dict(
        base=base, accel=0.0, mult=mult,
        cover_rate=base * mult,
        open_in_budget=float(open_healable(base, 0.0, BUDGET)),
        open_in_budget_fixed=float(open_healable(base, 0.0, BUDGET_FIXED_START)),
        cover_steps=float(cover_steps_for_wound(base, 0.0, mult)),
        open_steps_to_theta=float(steps_to_heal(THETA, base, 0.0, 1.0)),
        open_steps_to_wound=float(steps_to_heal(WOUND, base, 0.0, 1.0)),
        n_candidates=len(cands),
    )


# ── the homeostatic-reward cross-check (drive is what the agent actually optimises) ───────────
def drive(satiation, injury):
    """Homeostatic drive, thermal off: ||(satiation - setpoint, injury)|| (core.py::calculate_drive)."""
    return float(np.hypot(satiation - SETPOINT, injury))


def rest_step_reward(injury, nutrition, base, accel, mult=1.0, streak=1):
    """Reward for ONE rest step: prev_drive - curr_drive, with satiation == nutrition.

    `use_homeostatic_reward` is true on the shipped default, satiation = max_satiation *
    (nutrition/max_nutrition)**1.0 at the shipped scaling factor of 1.0, so satiation and nutrition
    are the same number here. The step heals some injury and loses one unit of nutrition, and the
    two pull the drive in opposite directions - which is why a heal rate can be positive and the
    step still be punished.
    """
    healed = float(per_step(streak, base, accel, mult))
    return drive(nutrition, injury) - drive(nutrition - METABOLIC_COST,
                                            max(injury - healed, 0.0))
