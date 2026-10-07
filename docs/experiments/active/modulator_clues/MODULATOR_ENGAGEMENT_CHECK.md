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

## Revision 1a (2026-10-07, before any computation), settling the re-review's concerns

These items override the sections above where they differ.

- **E1 route: live mode with the shadow pass** (`scripts/analysis/obs_manipulation/run.py`).
  - The acting network sees felt injury set to **0.70** from step 0. That is the settled value for a
    constant injury of 70: the felt-injury kernel sums to 1 and perceptual noise is off in the saved
    configs.
  - The shadow network is fed the true observations of the *same* trajectory.
  - E1 is the per-unit, per-step mean absolute difference in γ (and β) between the acting and shadow
    networks. The comparison is teacher-forced along the manipulated path.
  - The tool is extended to record per-unit absolute differences, and to keep the shadow's modulator
    output.
  - Replay mode is not used: it needs stored observation files, which none of these runs have.
- **E1 sensitivity row:** felt injury follows the recorded trace of a natural injury-70 no-animal
  episode, instead of the constant 0.70.
- **E4 freeze target:** one target per checkpoint for both injury conditions, namely the per-unit
  time-mean pooled over the injured and unhurt live passes in the rabbit scene. A separate mean per
  condition would keep the steady shift that injury causes in gain, and so hide the effect being
  measured.
  - The weight-edited checkpoints are written to a separate directory, never over the originals, and
    scored with the same eval sweep that produced the outcomes.
  - E4 uses every fifth checkpoint of the 41-point grid, 9 checkpoints per run, to bound GPU time. The
    budget is reported before launch.
- **Outcome code pinning.**
  - The 9 main pairs are scored from a `git worktree` at `10358a45`; extracting the file alone would break
    its import of `highlight.py`. The result is checked against the working copy.
  - The `l05fix` pairs are not in `10358a45`. They are scored from the working copy and labelled as such,
    or from a commit by the owning session if one exists by then.
- **Decision rule, stated in full:** P-main, P-own and the negative control are all computed on values
  demeaned within each level, each with its own 216-arrangement null.
- **Checkpoints:** E1 is averaged over each pair's own tested checkpoint set, where that has fewer than 41.

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

## Feedback from plan-reviewer (re-review of Revision 1)

*Reviewed 2026-10-07, before any computation. Verdict: **SOUND WITH CONCERNS**. Both critical findings
from the first review are resolved: E1 is now teacher-forced, and the primary outcome (the rabbit-scene
injury effect) shares no scene with E1. The decision rule, P-own threshold, negative control and the
within-level null are all in place. Four edits remain. None changes the logic of the plan, but E1 and
E4 cannot run as written.*

Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run · 🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

- 🟡 **E1 cannot run on the named tool path.** Replay mode needs a trajectory store, a parquet file of
  recorded observations (`replay_mode.py:87-90`), and allows exactly one store, so one checkpoint, per
  run. No store exists for any `healrep_*` run, and the sweep's `_scratch` holds environment snapshots,
  not observations. Running E1 on 41 checkpoints means either (a) collecting 14 × 41 stores in the
  unhurt no-animal scene and lifting the one-store-per-run limit, or (b) using **live mode**
  (`run.py`, which already takes a test-scene `--world`, `--checkpoints all`, and a parity check against
  the sweep's scratch) with `set` on felt injury. In (b), the shadow pass receives the true inputs of
  the same trajectory, so acting-minus-shadow γ is still teacher-forced, only along the manipulated
  trajectory. Pick one and write it in. Either way the developer change also needs: per-unit |Δγ|,
  because live mode records only the acting pass's unit-mean gain (`run.py:134-137`) and replay records
  a signed unit-mean difference (`replay_mode.py:63-64`); the shadow pass's modulator output (live mode
  drops it at `run.py:115`); and a SCRIPTS_DEPENDENCY_MAP entry for any new driver script. Owner:
  developer.
- 🟡 **E4's freeze target as worded removes the wrong thing.** "Per-unit time-mean from the run's own
  live pass *in that scene*" can be read as a separate mean for the injured scene and for the unhurt
  scene. Freezing at those means would keep the tonic injury-driven shift in γ and remove only the
  variation within each episode, so E4 would report "freezing removes little" even if the modulator
  carries the whole effect. **Fix:** use one target for both injury conditions, the mean pooled over the
  injury-0 and injury-70 passes (or the injury-0 mean), and state which. Implementation:
  `run_freeze.py` rolls out only in the training world, so the practical route is to write the
  weight-edited checkpoints to a **separate** directory (never over the originals) and score them with
  the same dwell sweep that produced the outcomes. Then the outcome is measured by the same pipeline as
  the outcome itself. State E4's checkpoint subset and budget: 41 checkpoints × 2 heads × 9+ runs is a
  full re-sweep. Owner: experiment-designer / developer.
- 🟡 **Pinning to `10358a45` excludes the out-of-sample pairs.** At that commit `LEVELS` has no `l05fix`
  (`figures.py:42` at 10358a45). The level-05 fixed-start pairs exist only in the uncommitted working
  copy, so P-out cannot be computed from the pinned code. The working-copy diff only adds `l05fix`
  entries and a docstring paragraph; `leaf`, `effect` and `MEASURES` are unchanged, and the imported
  `f7b_across_runs/highlight.py` has not changed since that commit. **Fix:** compute the main set from
  the pinned commit, using a `git worktree` at 10358a45 (extracting the file alone breaks its
  `HERE`-relative import of `highlight`). Assert that it matches the working copy on those 9 pairs, and
  take `l05fix` from a commit that adds it (ask the owning session to commit) or label it as
  working-copy-derived. Owner: experiment-analyzer.
- 🟢 **Decision-rule basis is unstated.** Say whether ρ for P-main, P-own and the negative control is
  computed on the within-level-demeaned values (it should be, all three the same way, with the 216-way
  null as the p-value for each). As written, "demeaned" appears only in the permutation sentence.
  (p ≤ 0.05 is attainable: the smallest possible p is 1/216.)
- ❓ **"Settled value" is determinable, and it is 0.70.** Felt injury is injury history convolved with a
  normalised kernel (length 12, kernel[0] = 0, `config_loader.py:2507`). Perceptual noise is off in the
  saved run config. So a constant injury of 70 settles at 70 / max_injury 100 = **0.70**, and the plan
  should write the number. As a counterfactual it is reasonable but stronger than anything the agent
  meets: real felt injury starts at 0 at reset and climbs over about 12 steps, and in the real injured
  episode it then falls as the agent heals, at 5 points per step in a bush. A constant 0.70 from step 0
  is therefore off-distribution for the first few steps and longer-lasting than in reality. Suggested
  sensitivity row: the same Δγ with the recorded felt-injury trace of the injury-70 no-animal episode,
  indexed by step, in place of the constant.
- 🟢 Some pairs have fewer than 41 tested checkpoints (`figures.py` notes "testing stopped before
  10 M"). Use each pair's own checkpoint set for E1, so engagement and behaviour are averaged over the
  same checkpoints.

**Resolved from the first review:** circular E1 (now teacher-forced); predator guard (rabbit-scene
injury effect primary, shared baseline reported); G dropped; P-own threshold and negative control
added; within-level null; 41 checkpoints; raw E1; critic dropped; explicit run list; level-05
own-scene row; plan committed before computation (6a50a4a9).

**Cost of being wrong:** low. Nothing is trained. The worst case is a few GPU-hours of E4 re-sweeps
spent on a freeze target that cannot detect the effect, and a misleading "the modulator does not carry
the injury effect" caveat. E1 and P-main are sound once the tool route is chosen.

*Reviewed by: plan-reviewer*
