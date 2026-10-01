# Plan review — Basic Behaviour Analysis pipeline

Reviewed by: plan-reviewer · 2026-10-01 · object: [[BASIC_BEHAVIOUR_ANALYSIS_PIPELINE]] at commit `d9ea3bf0`

## Verdict

**NOT READY — but only for its last statistical step.** The plan builds a reusable "first look"
at any trained population. It measures five behaviours per run (hiding in a bush, eating, being
near a rabbit, being near a predator, standing on a warm square), fits the existing hiding-page
regressions to each run, and then fits one pooled model across all 18 runs of the single-channel
smell study. Steps S0–S4 (infrastructure, per-run figures) are sound, apart from two fixable
precondition and coverage gaps. Step S5 (the pooled model) has two problems that would produce a
wrong-looking answer to the project's central question.

1. **It would re-test the smell study's own registered hypothesis by a different route.** That
   hypothesis is: does the rabbit's smell trigger more hiding the more injured the agent starts,
   and does a harder-to-read smell make that worse? The re-test would use the smell reading in the
   control world that the study itself rejected as confounded. It would pool the two agent types,
   which the study analyses separately. And it would attach p-values, outside the study's
   pre-registered decision rule.
2. **For the hypervigilance term itself, the "primary" uncertainty treats ~6 million episodes as
   independent.** That is the pseudo-replication the plan's own section A7 sets out to prevent.

Both are fixed by editing sections B5, A7 and F5 of the plan. No code exists yet. The full ranked
list is below.

Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run · 🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

## Critical findings

### C1 — F5 is an unregistered second test of the hv study's Q2 / S1, using a confounded reference reading

- **Plan:** B5 terms `rab_smell_llr:start_injury` and `rab_smell_llr:start_injury:world` with
  cluster-robust t₁₇ p-values; F5 panel (b), "per world × agent".
- **Study:** [[SINGLE_CHANNEL_SMELL_HYPERVIGILANCE]] §1 (Q2 hypervigilance, H₁b), §5.2 S1 (the
  registered scent × injury estimator), §5.3 (decision rule), §2.1 ("each agent is analysed
  separately").
- **What goes wrong.** §5.2 S1 Revision 4 decided that the control world's reference reading must be
  the **matched-control** one: channel 1 as the scent variable, with channel 2 as a covariate. The
  reason is that in both treated worlds the scent statistic *is* odour strength (identity plus
  strength). The control's `x1 − x2` log-likelihood ratio is identity only. B5 uses the plain
  `spec.llr(statistic)` in every world, so `x1 − x2` in the control. As a result,
  `rab_smell_llr:start_injury:world` compares an identity-only slope with identity-plus-strength
  slopes, which is the confound the study removed. The term also has no `:agent`, so it pools the
  two agents. And it is judged by a t-test on 17 degrees of freedom (df), not by the study's
  permutation / Mann–Whitney rule at 3 v 3 → 5 v 5.
- **Consequence.** Two answers to one registered question on the same 18 runs. The new one is
  confounded and overconfident, and it is the one on a published page.
- **Fix (owner `senior-developer`; consult `experiment-designer` as the study owner):** pick one:
  (a) on hv populations, fit F5's smell terms **per agent** with the study's matched-control
  reading in the control world, and label F5 "descriptive — the registered verdict is the study's
  §5.3"; or (b) drop world-contrast inference on smell terms from F5 and show only per-run slopes
  and per-cell means, pointing to the study for the test. Whichever is chosen, the plan must state
  how F5 relates to S1 / §5.3.
- **Exit condition:** B5 and F5 name the reference reading and the agent handling, and carry no
  p-value that competes with §5.3.

### C2 — The headline within-run slope gets an episode-level "primary" SE

- **Plan:** A7 last paragraph; B5 `coef.csv` sets `primary_se = episode` for any term without
  world or agent.
- **What goes wrong.** `rab_smell_llr:start_injury` (the hypervigilance slope) and the start-injury
  and nutrition slopes would be judged by a Pearson-scaled binomial SE on about 6 M episodes. If the
  18 per-run slopes split in sign, that SE still declares a small average significant. The plan's
  own test `test_pooled_cluster_se_detects_disagreeing_runs` expects a gap of at least 5× in exactly
  that case. Under treatment coding with `x:world` and `x:agent`, that "main" slope is also the
  slope of the reference cell only (control world, ordinary agent), estimated from 3 runs. A claim
  about "an agent of this kind" needs between-seed variance.
- **Fix (owner `senior-developer`; user decision 3 should be re-confirmed with this in view):**
  make the run-level SE (two-stage, or cluster — see M1) primary for **every** term reported as a
  property of an agent type or world. Keep the episode SE as a secondary column labelled
  "conditional on these particular runs".
- **Exit condition:** the `primary_se` rule no longer assigns `episode` to any term the page
  interprets.

## Moderate findings (summary; detail in the plan's Feedback section)

| # | Issue | Owner |
|---|---|---|
| M1 | CR1 + t with G − 1 = 17 df is anti-conservative here: 8 run-level parameters (world, agent, world:agent, seed, intercept) on 18 runs with 3 per cell. `seed` as a main effect is mis-specified (study §2.4: identical starting weights only within seed × agent; registered rule is unpaired), and the two-stage OLS omits it. A wild cluster bootstrap is unreliable with 3 clusters per cell. | senior-developer |
| M2 | Model structure: no `x:world:agent`, and the hypervigilance term has no `:agent`, yet F5(b) promises per world × agent slopes. S5.4 compares a reference-cell slope with all 18 per-run slopes. | senior-developer |
| M3 | "pp per SD" is not interpretable across worlds as specified. Effects are converted at one pooled rate. Interaction terms in pp are not marginal effects. B5's "main effect = effect at the average" is false under treatment coding. The pooled SD of the smell LLR is a different share of each world's spread. `coef.csv` reports per SD, F5 per nat. | senior-developer |
| M4 | The byte-identity gate covers only the unchanged a01 / `bush_dwell` path. The per-name resource split, single / sum layouts, new targets and exclusions are not gated. | senior-developer |
| M5 | The precondition fails today. `make_population.py --from-study-doc` hard-fails on C02 (`completed`, no store) and on stale `running` rows. `golden_a01.py`'s command lacks the required `--population` and `--agent`. | senior-developer / hv-study session |
| M6 | The plan implicitly settles the OPEN Known Bug "freeze-vs-fix" for `hiding_drivers.py` without recording it. The `t−1` assertion checks only the seed, not `t` contiguity. | bug-curator / developer |

## Cost of being wrong

No training compute is at risk, and the infrastructure costs a few local CPU hours. The real cost
is an F5 figure that answers the project's central hypervigilance question with a confounded
reading and overconfident p-values, in direct competition with the study's pre-registered verdict.
That is how a wrong claim reaches a paper.
