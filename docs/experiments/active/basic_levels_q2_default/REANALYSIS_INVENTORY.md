---
title: "Which existing analyses are worth re-running on the two basic-levels waves"
topic: basic_levels_q2_default
status: active
created: 2026-09-23
last_updated: 2026-09-23
---

# Which existing analyses are worth re-running on the two basic-levels waves

## Question

Two waves of fourteen training runs now exist for the same comparison — an ordinary agent against
one carrying a neuromodulator, across the seven standard worlds. **Wave 1** (2026-09-21) trained in
a world where hiding in a bush healed no faster than standing in the open and where the agent could
only die of *under*-eating. **Wave 2** (2026-09-22) trained after both of those were fixed: cover is
now the only place healing meaningfully works, and fullness has a target in the middle of its range
with death at both ends.

This project has already built and published a number of analyses that measure **how much of an
agent's behaviour depends on the state of its own body** — mostly through one behaviour, sitting in
a bush. This document is an inventory of those analyses: what each one measures, what it needs in
order to run, and whether it is worth pointing at these two waves. It is a shopping list, not a
plan; nothing here has been run yet.

## The one fact that decides most of it

The analyses split into two families by **what they read**, and the two families are not equally
ready:

- **Checkpoint-based.** Roll each saved checkpoint out against fixed probe scenarios. Needs only
  the training run's own checkpoints, which both waves have. **Ready now.**
- **Trajectory-store-based.** Read a Parquet store of a million recorded episodes per run. **No
  store exists for either wave** — `results/trajectories*/` contains stores for the ladder, the
  sensory arms and the neuromodulator grids, and nothing for `basicq2`. Every one of these needs a
  collection pass first.

That collection pass is the single largest cost in front of any of this, and it is worth stating
plainly before choosing: roughly 10–12 GB and about twenty GPU-minutes per run, so about 300 GB and
ten GPU-hours for all twenty-eight runs, which spread across free nodes is a couple of hours of
wall-clock per wave.

**One thing collection does NOT suffer from**, which the probe sweep did: it replays each run in
**its own world**, so there is no observation-width mismatch. The trajectory route therefore reaches
all fourteen runs of each wave, including levels 00/01 and the two thermal levels that the probe
battery cannot currently touch.

## Tier 1 — directly answers the question, and is run-agnostic already

| analysis | what it measures | source |
|---|---|---|
| `context_dependence.py` | Literally this question. Its own first line reads *"Does the agent's behaviour depend on its INTERNAL STATE, and does a neuromodulator strengthen that dependence?"* Measures bush entry as a function of injury, and the change in that relationship. | purpose-built |
| **What makes this agent hide?** (`a01_hiding_drivers`) | A multivariate model of bush hiding that puts internal state (injury, fullness) and the state of the world (predator distance, odour) into the *same* fit, so each is adjusted for the others. Without this, an injury effect can be a predator effect wearing a disguise. | published artifact |
| Ladder figure **8** — injury dose-response | The causal test. Episodes begin with a randomly assigned injury the agent did nothing to earn, so behaviour that tracks it is *caused* by it. | published artifact |
| Ladder figure **9** — sensed vs assigned injury | Whether behaviour follows the injury the body *has* or the signal the agent *senses*, and with what lag. Separates the interoceptive channel from the body state. | published artifact |
| Ladder figures **10, 11, 12** — hypervigilance | Whether being injured makes the agent treat a *harmless* animal as threatening. This is the closest thing the project has to a pain-like signature, rather than mere damage avoidance. | published artifact |
| Ladder figure **13** — two competing drives | Injury says hide, hunger says forage. Which wins, and does the modulator change the balance. Directly relevant to Wave 2, where hunger became two-sided. | published artifact |

## Tier 2 — worth having, cheaper, and one is already done

| analysis | status |
|---|---|
| **Bush-hiding checkpoint sweep** (`dwell_sweep`) | **Already run for Wave 1 levels 02–04.** Needs no store. Blocked on levels 00/01 (needs a 44-width probe battery) and 05/06 (the agent freezes in a fireless thermal probe — measured, not assumed). |
| Ladder figure **14** — window and variable | A robustness check on figure 8: whether an injury result survives changing the measurement window and the variable. This project has already had one injury finding reverse under exactly that test, so it earns its place. |
| Ladder figure **15** — the price of hiding | What hiding costs in survival. Guards against reading "hides more" as "does better". |
| **Modulator Training Health** (`nmn_health`) | Cheap, and answers "did the modulated arm train properly at all" before any behavioural claim rests on it. |

## Tier 3 — skip, or fix first

| analysis | why |
|---|---|
| Ladder figures **1, 2** | They compare *sensory arms*. Every run in both waves shares one sensory configuration, so there is nothing to compare. |
| Ladder figure **3** — how episodes end | **Broken for these waves.** It recognises only three outcomes, and over-eating deaths — newly reachable in Wave 2 — would silently score zero while the bars fail to total 100%. Fix before use; it is an open registry row with a named fix to copy. |
| Ladder figures **4, 5, 6, 7** | About the world and threat discrimination rather than internal state. Useful context, not the question asked. |
| **Looking Inside the Modulator** (`repr_analysis`) | Reads modulator internals from checkpoints rather than behaviour. A different question — *what the modulator does* rather than *what the agent does* — but it is what turns a behavioural null into a mechanism, so it is worth running once the behaviour is known. |

## What comparing the two waves actually buys

Wave 1 is not a failed run to be discarded. It is the **control for the environment change itself**:
the same agents, the same seven worlds, the same comparison, in a world where hiding had no healing
value and fullness could not be overshot. So three contrasts exist rather than one:

1. modulated against unmodulated, within Wave 1
2. modulated against unmodulated, within Wave 2
3. **Wave 2 against Wave 1** — does making cover the only place healing works, and making fullness
   two-sided, increase how much behaviour depends on internal state *at all*, for either arm

The third is the one that could not be asked before today, and it is the reason to run the same
analysis on both waves rather than only the new one.

## Known caveats to carry into any result

- **One seed per cell.** Every comparison is one run against one run. This is the largest threat to
  any conclusion drawn here and it applies to both waves equally.
- **Wave 1 is truncated on four runs.** Levels 00–03's modulated arms were stopped between 59% and
  96%. Comparisons at matched training length are fine; comparisons at each run's endpoint are not.
- **Wave 1's hiding cannot be about healing.** In that world a bush healed exactly as fast as open
  ground, so any injury-dependent hiding there is predator avoidance, not recovery.
