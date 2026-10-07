# Modulator engagement check: is the modulated agent's behaviour gap explained by how much its modulator works?

## Question (plain language)

In the fast-bush-healing replication ([[FAST_HEAL_REPLICATION]]), the modulated agent beat its
ordinary partner in some seeds and not in others. Read as trends rather than tests, two patterns stood
out (conversation with the user, 2026-10-07):

1. **Asymmetry.** When the modulated agent is ahead, it tends to be ahead by a lot (up to +26
   percentage points of bush dwell). When it is behind, it is usually behind by only a little. The
   exception is level 05 seed 43, which is behind by 12.4 points on the predator measure.
2. **Seeds partly move as one.** In 4 of the 9 replication pairs, the gap has the same sign in all three
   measures. Two of those are positive (level 04 seed 44, level 05 seed 42) and two negative (level 04
   seed 43, level 05 seed 43); the two 22-September originals are positive in all three. Part of this
   is built into the measures: two of the three share a test scene, "no animal, unhurt", as their
   baseline, so they move together whatever the modulator does.

That suggests a **mode**: some training runs end up with a modulator that is *engaged*, meaning its
output changes when the body is hurt, and these hide more. Others end up with a modulator that is
*idle*, close to a constant rescaling, and these behave like an ordinary agent.

This check asks whether that is so, on checkpoints that already exist and with no new training. It
measures how strongly each modulated run's modulator responds to felt injury, with everything else
held identical, and asks whether the runs that respond most are the runs whose injury-driven hiding is
largest.
- **If yes**, the target for improving the modulator becomes "make it engage in every seed", which the
  modulator-input study ([[NMN_INPUT_L05]]) is built to test.
- **If no**, the gap is behavioural variation that the modulator's injury response does not explain.

Even a clear yes shows association, not cause. The causal measure E4 below is the part that speaks to
cause.

Status: **exploratory**. The predictions below were fixed and committed before any engagement number
was computed (Revision 1, after the plan review). There is no registered verdict. With 9 pairs the
likely outcome is "unclear": even if the true correlation is 0.5, a sample correlation reaches the
0.6 bar only about a third of the time.

## Units

- **Main set (9 pairs):** levels 04, 05 and 06 × seeds 42, 43, 44, the replication pairs in Figure R1.
  For level 06 seed 42, use the relaunched pair `20261005-170252_…t1none_s42` /
  `20261005-170314_…t16quad_s42`. The 16:01 folders are dead and hold no checkpoints. Every tool
  receives an explicit list of the run folders; none discovers runs by name pattern.
- **Out-of-sample set (5 pairs), scored only after the main set:**
  - the three level-05 fixed-start-temperature pairs (`healrep_l05fix`, seeds 42–44);
  - the two 22-September originals (`bq2cover_lvl04` and `lvl05`, seed 42). These were selected *because*
    they showed the effect, so they are reported apart from the fixed-start pairs.

## Behaviour outcomes (read from existing outputs through the page's own code)

Every outcome is a per-pair value, modulated minus ordinary unless stated. Units are percentage points
of bush dwell, averaged over the 41 checkpoints from 2 to 10 M training steps, in the scenes the page
used: level 04 core scenes, levels 05 and 06 neutral scenes. Values are read from
`results/eval/avoidance/metrics_history_rppo_healrep/` through
`scripts/analysis/studies/fast_heal_replication/figures.py`, at its last committed version, `10358a45`; another session has uncommitted edits to that file, so the outcome code is read from that commit, not from the working copy.

- **Primary outcome — the injury effect with the wandering rabbit** (injured 70 minus unhurt 0). It is
  the only behaviour measure that shares no test scene with E1.
- **Secondary outcomes:**
  - the injury effect with no animal (it shares E1's scene);
  - the predator effect (it shares the "no animal, unhurt" baseline);
  - that shared baseline itself, the unhurt no-animal bush dwell.

  E1 is reported against each one separately, never combined into an average. (The average G in the
  first draft is dropped: the predator gap, about three times wider than the injury gaps, dominated it.)

## Engagement measures (modulated run only)

Computed at every one of the 41 checkpoints that the behaviour uses, then averaged. Sites are the
encoder, memory and actor; the critic is left out, because it cannot change what the agent does.

- **E1, injury responsiveness, teacher-forced (primary).**
  - Take the unhurt no-animal test episodes and replay them through the network twice, each time with
    the recorded observations and actions.
  - In the first replay nothing is changed. In the second, only the felt-injury input
    (`Interoceptive Nociception`) is replaced by the value it settles at for a starting injury of 70,
    from the first step.
  - Every other input, and every action, is identical, so any change in the modulator's output is
    caused by felt injury alone.
  - **E1γ** is the mean absolute difference in gain γ, per unit and per step, between the two replays.
    **E1β** is the same for the offset β. Both are raw, not normalised; the across-unit spread of γ is
    reported beside them.
  - Built on `scripts/analysis/obs_manipulation` (replay mode), extended to record per-unit γ/β.
- **E1-natural (secondary, labelled as confounded).** The same difference, but between the natural
  injured and unhurt test episodes. Their trajectories split once the injured agent walks to the bush,
  so this measure mixes the response to injury with the response to a different view.
- **E2, context share (secondary).** The fraction of the gain's variance that changes over time rather
  than being a fixed per-unit constant (`mod_distribution.variance_split`), on rollouts in the run's own
  training world.
- **E3, freeze cost in the run's own world (secondary).** Survival cost of freezing the gain at its
  per-unit time-mean, and separately the offset (`freeze.py`, paired episodes, equivalence verified).
- **E4, causal (secondary).** In the wandering-rabbit test scenes at injury 70 and at 0, freeze the gain
  (then separately the offset) at its per-unit time-mean from the run's own live pass in that scene, and
  measure how much of the modulated agent's injury effect disappears. Same checkpoints, same seeds. This
  speaks to whether the modulator *carries* the injury effect, not only whether it responds to injury.

## Predictions and decision rule (fixed in Revision 1, before any number)

The rank correlation is Spearman's ρ. For the level confound, each pair's E1 and outcome are demeaned
within its level, and a within-level permutation null is used: E1 is shuffled within each level, giving
3!³ = 216 arrangements, and p is the share of arrangements at least as large as the observed value.

- **P-main.** ρ(E1γ, primary outcome) over the 9 pairs:
  - **supports** the mode idea if ρ ≥ 0.6 **and** the within-level permutation p ≤ 0.05;
  - **counts against** it if ρ ≤ 0;
  - **unclear** otherwise.
- **P-own.** ρ(E1γ, the modulated agent's *own* rabbit-scene injury effect) ≥ 0.6. Required for "supports".
  Without it, a positive P-main could come from the ordinary partners' noise.
- **Negative control.** ρ(E1γ, the *ordinary* partner's rabbit-scene injury effect) is expected near 0.
  If it is ≥ 0.6, the relation is a level or scene artefact, and "supports" is withdrawn.
- **P-rank (descriptive).** Level 04 seed 44 and level 05 seed 42 in the top three on E1γ; level 04 seed
  43 and level 05 seed 43 in the bottom three.
- **P-cause (E4, descriptive).** In pairs with high E1γ, freezing removes a larger share of the injury
  effect than in pairs with low E1γ.
- **P-out (descriptive).** The sign of the relation repeats on the out-of-sample pairs.

E1β, E1-natural, E2 and E3 are reported beside the main result, but none of them can rescue a failed
P-main.

## Guards and sensitivity

- **Scene choice.** Level 05 is known to flip sign between scene sets, so the own-scene version of the
  level-05 outcome is reported as a sensitivity row.
- **Level confound.** Correlations are also given within each level (3 pairs, descriptive).
- **Selection.** The originals stay out of the main set.
- **Reproducibility.** This plan and the outcome code are committed before E1 is computed. The commit
  SHA is recorded with the results.

## Outputs

`results/analysis/modulator_engagement/`: a table of the 14 pairs × (outcomes, own effects, E1γ, E1β,
E1-natural, E2, E3, E4), the permutation null, and a manifest. A results section is appended below.

## Revision log

- **Revision 1 (2026-10-07, before any computation)**, after the plan review (NOT READY;
  `docs/reviews/plan_modulator_engagement_check.md`):
  - E1 is now teacher-forced; the natural version is kept as a labelled secondary.
  - The primary outcome is now the rabbit-scene injury effect, and G is dropped.
  - P-own now has a threshold, a negative control is added, and the within-level permutation null is
    added.
  - All 41 checkpoints are used; E1 is raw rather than normalised; the critic is dropped.
  - E4, the causal measure, is added; runs are passed as an explicit list.
  - The motivation is corrected: 4 of 9 pairs move as one, and two of the measures share a baseline.

## Feedback from plan-reviewer

*Reviewed 2026-10-07, before any computation. Verdict: **NOT READY**. The two critical findings and their
fixes are below. Full table, assumptions and prior art: [[plan_modulator_engagement_check]]
(`docs/reviews/plan_modulator_engagement_check.md`).*

Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run · 🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

- 🔴 **E1 is circular.** The modulator reads every input. In the no-animal scene, the injured replay walks
  to the bush and the unhurt one does not, so the gains differ through vision and position alone. Felt
  injury also lags (time constant 3 steps, zero at reset). And the scene is deterministic: all 30 episodes
  are one trajectory, the same pair the "injury, no animal" gap comes from. **Fix:** a teacher-forced E1.
  Take the unhurt observation stream, change only the felt-injury input, keep actions fixed, and difference
  γ/β. Keep the natural version as secondary.
- 🔴 **The predator guard is not independent.** The predator measure is (predator, unhurt) − (no animal,
  unhurt), and that second scene is E1's unhurt replay and the baseline of the injury measure. **Fix:**
  use the wandering-rabbit injury gap as the out-of-scene test, and also report E1 against the shared
  baseline gap.
- 🟡 Tool: `replay.py` cannot load a test scene or set the starting injury. The observation-manipulation
  tool can, but it records only unit-mean gains. That needs a developer change plus a SCRIPTS_DEPENDENCY_MAP
  update. The E2/E3 runners' run discovery does not match `healrep_*` names; pass an explicit run list.
- 🟡 Decision rule: G is dominated by the predator gap, so make the primary outcome the injury gaps. Give
  P-own a threshold of ρ ≥ 0.6, measured on injw, and add a negative control (E1 against the *ordinary*
  partner's effect). Make the main statistic level-stratified, with a within-level permutation null
  (216 permutations). Use the same 41 grid checkpoints as the behaviour, not 5. Define E1's normaliser
  (raw |Δγ| primary), drop the critic site, and add a level-05 own-scene sensitivity row.
- 🟡 Commit this plan, and the `figures.py` state it reads through, before any engagement number exists.
- Verified: the level-06 seed-42 identification is correct (170252 / 170314; the 16:01 folders have no
  checkpoints).

*Reviewed by: plan-reviewer*
