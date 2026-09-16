---
title: Which recovery settings make resting outside cover pointless
topic: recovery_in_bush_tuning
status: active
created: 2026-09-16
last_updated: 2026-09-16
---

# Which recovery settings make resting outside cover pointless

**Shareable page:** https://claude.ai/code/artifact/e06626a5-2a0a-4fbc-b733-31312443f847
**Source:** `docs/experiments/active/recovery_in_bush_tuning/recovery_in_bush_tuning.html`
**Republish:** rebuild, then publish that file to the URL above **through the**
[`publish-page`](../../../../.claude/skills/publish-page/SKILL.md) **skill**, never the `Artifact`
tool directly. From a session that did not publish it, read the URL first and pass it as `url` —
publishing without it makes a second artifact instead of a new version of this one.
**Rebuild:** run the six figure scripts under `scripts/analysis/studies/recovery_in_bush_tuning/`,
then `python scripts/analysis/studies/recovery_in_bush_tuning/build_page.py`.

---

## Question

In this simulation an animal heals its injuries only by choosing the **Rest** action, and it can
rest anywhere. A setting called `body.recovery_in_bush_multiplier` can make resting inside a
**bush** — a grid square that hides the animal from a hunting predator and that predators cannot
walk into — heal faster than resting on open ground. It ships at `1.0`, which means "no difference
at all".

This is a **tuning study**, not an experiment: no agent was trained. It asks what values of the
three recovery settings would make **resting out in the open not worth doing**, so that an injured
animal has to travel to cover to get better. The point of wanting that is behavioural — an earlier
measurement found that an injured agent freezes and heals wherever it happens to be standing
(resting on 86% of steps while injured, but standing in a bush on only 1–3% of them), which is the
opposite of using cover as a refuge. Making cover the only place healing actually works is the
intervention that would test whether injury can be made to *increase* cover use.

**The answer, in one line.** Set `recovery_base_rate: 0.2`, `recovery_accel_rate: 0.0`,
`recovery_in_bush_multiplier: 25`. Both settings that ship today fail the test badly: each clears
the entire 100-point injury scale out in the open, one of them in about 15 rest steps.

---

## The definition

> **Resting outside cover is "not meaningfully recoverable" when an agent that rests continuously
> in the open for its entire affordable rest budget cannot clear more than θ of the injury scale.**
> The affordable rest budget is `nutrition / metabolic_cost`, because a resting agent eats nothing.

Primary setting: **θ = 25 injury points of 100** and a **50-step budget**. Both are choices, not
facts, and the page shows what moves if either changes.

The complementary requirement, because a world where nobody can heal is not the goal: **cover must
be usable** — an agent resting in a bush should clear a typical 70-point wound within about 25 rest
steps. Throughout, **condition A** is the first and **condition B** the second.

---

## Ground truth

The arithmetic is transcribed from `src/environment/core.py` lines 226–266:

```
streak(t)       = rested ? streak(t-1) + 1 : 0
recovery_amount = recovery_base_rate * (1 + recovery_accel_rate) ** (max(streak,1) - 1)
if recovery_in_bush_multiplier != 1.0 and in_bush:  recovery_amount *= multiplier
can_recover     = rested AND applied_inc <= 0
new_injury      = clip(injury + applied_inc - recovery_amount * can_recover, 0, max_injury)
```

At `recovery_accel_rate` = 0 the two conditions reduce to one inequality each:

- **A:** `recovery_base_rate ≤ θ / budget` — and note it depends on θ and the budget **only through
  their ratio**, so halving the threshold and doubling the budget are the same move.
- **B:** `recovery_base_rate × recovery_in_bush_multiplier ≥ wound / cover steps`.

---

## Figures

One script per figure, under `scripts/analysis/studies/recovery_in_bush_tuning/`. Every figure is
written to `figures/` as SVG, PDF and PNG plus a `.data.txt` used/available statement emitted by
the script.

| Figure | What it shows | **Axes** |
|---|---|---|
| `f01_recovery_time` | The primitive question, before food or thresholds enter: how many consecutive rest steps does undoing a wound take, under each setting? Compounding almost erases wound size; flat healing scales in proportion; the in-bush multiplier is the vertical gap between the two green curves. | **Axes.** Horizontal: size of the wound to undo, injury points, 15–100. Vertical: rest steps needed, log 2–900. |
| `f02_against_hunger` | The same curves with the rest budget laid across them. The recommendation's open-ground curve sits above both budget lines at every wound size, so there is no wound it can heal outside cover before starving. | **Axes.** Identical to f01, plus two horizontal rules at the 50- and 100-step rest budgets. |
| `f03_open_ceiling` | Heat map of what the open can clear inside the rest budget, with the θ contour. Almost the whole shipped range is saturated. | **Axes.** Horizontal: `recovery_base_rate` in injury points per rest step, log 0.01–5. Vertical: `recovery_accel_rate`, linear 0–0.5 in panel (a) and 0–0.06 in panel (b). Colour (shared scale): injury points healable in the open within the 50-step budget, 0–100. |
| `f04_feasible_window` | The answer figure: the region satisfying both conditions, at accel 0, with the recommendation marked. | **Axes.** Horizontal: `recovery_base_rate`, log 0.02–6. Vertical: `recovery_in_bush_multiplier`, log 0.8×–60×. Shading is categorical, not a quantity. |
| `f05_accel_spoiler` | Rest steps to cross θ in the open against `recovery_accel_rate`, for four base rates, with each one's tolerance solved by bisection. | **Axes.** Horizontal: `recovery_accel_rate`, linear 0–0.12. Vertical: consecutive rest steps in the open to clear 25 injury points, log 3–1200. |
| `f06_env_validation` | **Not analytic.** The real environment under a scripted always-Rest policy, on a bush and off it, against the closed-form prediction. | **Axes.** (a) Horizontal: rest steps taken, 0–50. Vertical: `injury_level`, points of the 0–100 scale. (b) Horizontal: the same steps. Vertical: absolute difference between measurement and prediction, injury points, log 1e-6–3. |

---

## Result

**Recommended:** `recovery_base_rate: 0.2`, `recovery_accel_rate: 0.0`,
`recovery_in_bush_multiplier: 25`, chosen by a four-clause rule stated in `recovery_math.recommend()`
and on the page: switch compounding off; anchor the in-cover healing rate to the rest-premium
sweep's already-calibrated flat 5.0 per step; require both conditions at both budgets with strict
inequality; then take the weakest intervention that survives.

| Setting | healed in the open, 50 steps | healed in the open, 100 steps | steps to clear θ in the open | steps to close a 70-point wound in cover |
|---|---|---|---|---|
| shipped default — base 0.1, accel 0.5 | 100 | 100 | 11.9 | — |
| rest-premium arm a01 — base 5.0, accel 0.0 | 100 | 100 | 5 | 14 |
| **recommended — base 0.2, accel 0.0, ×25** | **10** | **20** | **125** | **14** |

**Acceleration.** A non-zero `recovery_accel_rate` is compatible with the design, but only a very
small one: at the recommended base rate the largest workable value is **0.033** on the 50-step
budget and **0.004** on the 100-step budget. The shipped 0.5 is one to two orders of magnitude
above every one of those.

**Validation (f06).** **Agreement.** Over 102 compared values the largest disagreement between the
simulation and the closed form is **1.53 × 10⁻⁴ injury points**, which is single-precision rounding
accumulated over 50 steps (the smallest representable gap near injury 95 is 7.6 × 10⁻⁶). In cover
the agreement is exact — every residual is zero. The same run measured nutrition falling by exactly
1.0 per rest step against a `metabolic_cost` of 1.0, which confirms the rest-budget half of the
definition rather than assuming it.

---

## Where the analysis design needed correcting

Six items, recorded in full in §11 of the page. In brief:

1. **The 50-step budget is not the shipped default's budget.** It is the median of a uniform
   [0, 100] start nutrition, which is real but only in worlds that switch randomised starting
   nutrition on. `configs/environment/default.yaml` starts at full nutrition, giving a 100-step
   budget — twice as strict. Both are carried everywhere.
2. **The quoted recurrence dropped `applied_inc`.** Immaterial for the undamaged case, but it hides
   an asymmetry: the rest streak keeps climbing during the damage-smoothing window while healing is
   blocked, so a compounding setting comes out of a hit *faster* than the clean curve suggests.
3. **"A resting agent eats nothing" is conditional.** True while eating is its own action (every
   maintained world). In an auto-eat world the flag is a function of position alone, so an agent
   resting on a food cell eats every step and its rest budget is not bounded by nutrition at all.
4. **The budget is a fatal bound**, which makes the test conservative rather than merely
   approximate — an agent that spends it all starves, so the definition grants the open more rest
   than any surviving agent could take.
5. **The definition is about possibility, not choice.** Under the homeostatic reward the
   recommended setting makes an open-ground rest step *negative* at a typical mid-episode state
   (−0.42 against +3.40 in cover), which is a stronger result and a different claim.
6. **f04 cannot show both shipped settings.** It is a plane at `recovery_accel_rate` = 0 and the
   shipped default has 0.5; plotting it there would place a point at coordinates the setting does
   not have.

---

## Limitations

- **No agent was trained.** Whether an injured agent learns to walk to a bush under these settings
  is the experiment this study exists to make worth running.
- **The validation is narrow** — two rollouts, one setting, one seed.
- **Adopting the recommendation leaves the inert regime.** At exactly 1.0 the in-bush premium is not
  compiled into the environment at all, which is what makes today's runs bit-identical to runs that
  predate the key. A multiplier of 25 switches that branch on.
- **The 70-point wound and the 25-step close are borrowed** from the rest-premium sweep's
  calibration, not measured from what wounds agents actually carry when they choose to rest.

---

## Links

- Page template + built page: `recovery_in_bush_tuning.template.html`, `recovery_in_bush_tuning.html`
- Scripts: `scripts/analysis/studies/recovery_in_bush_tuning/`
- Ground truth: `src/environment/core.py:226-266`; the feature's own tests at
  `tests/env/test_recovery_in_bush.py`
- Feature design: [[BUSH_REFUGE_AND_LOCATION_DEPENDENT_RECOVERY]]
- The behaviour that motivates it: [[a01_hiding_drivers]]
- House style: [[house_style_sheet]] · [[artifact_generation_guide]]
