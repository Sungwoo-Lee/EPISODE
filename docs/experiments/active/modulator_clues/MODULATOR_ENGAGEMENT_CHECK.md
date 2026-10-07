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

## Implementation Report (developer, 2026-10-07)

**In short.** The tooling for this plan (Revision 1a) is built, tested and committed (`0b9c1c67`, fix `3f4a8457`, branch `v5.0`).
After the coordinator's go, E1, E1-natural, E2 and E3 were computed for all 14 pairs on the 41-point
checkpoint grid. After a second go, E4 was computed for all 14 pairs at 9 checkpoints (see "E4 run").
No statistics or verdict have been computed on the real data: `analyze.py` has been run only on
synthetic inputs. Running it, and interpreting the result, is the analysis step
(experiment-analyzer, then plan-reviewer's verdict gate).

### What was built (file by file)

- `scripts/analysis/obs_manipulation/run.py` (live mode, extended):
  - The shadow's modulator output, previously discarded, is now kept.
  - Each step records, per FiLM site, the unit-mean |acting − shadow| gain (`absdgain_*`) and
    offset (`absdoffset_*`), plus the shadow's across-unit gain SD (`gainsd_*`).
  - The shadow's per-unit gain and offset are returned on request.
  - The per-checkpoint core is factored into `run_checkpoint()`.
  - `episodes.csv` gains `_mean` columns. Existing columns are bit-identical to before (checked).
- `scripts/analysis/obs_manipulation/manip.py`: `from_spec()` compiles an in-memory manipulation,
  with the same schema and checks as a YAML file.
- `scripts/analysis/modulator_engagement/runs.py`: the explicit 14-pair list.
  - Each folder is checked: it holds checkpoints, the modulated run is FiLM and the ordinary run
    has no modulator, and the top-level seed matches.
  - The dead 16:01 level-06 seed-42 folders are refused.
  - Each pair's probe directory, episodes and output leaf are read from its sweep spec, and the
    spec's paths for those labels are checked against the folders.
  - The 22-Sep level-05 pair is `20260922-182534` (ordinary) / `20260922-182538` (modulated): the
    pair the `thermalprobe_neutral_clean` sweep, and so `figures.REFERENCE`, used.
- `scripts/analysis/modulator_engagement/outcomes.py`: behaviour gaps read through `figures.py` at
  `10358a45`. **Deviation:** a `git archive` tree of `scripts/` at that commit is used, not a
  `git worktree`.
  - Why: the same pinned files result, without writing to the shared `.git`. A full worktree is a
    1.5 GB checkout, and sparse-checkout on git 2.34 risks changing the main worktree's config.
  - The import chain's blob hashes are checked against the commit (`figures.py`, `highlight.py`,
    `collect.py`, `checkpoint_stats.py`).
  - The 9 main pairs are asserted equal to the working copy (they are exactly equal).
  - l05fix is read from the working copy and labelled so.
  - Values match the plan's quoted numbers (e.g. level 05 seed 43 predator gap −12.4, level 04
    seed 44 +25.8).
- `scripts/analysis/modulator_engagement/engagement.py`, with subcommands `e1`, `e2`, `e3`,
  `e4-prepare` and `e4-collect`. Details are in its docstring.
  - E1 uses live mode as Revision 1a sets out. The acting network sees felt injury 0.70 from step 0.
  - 0.70 is checked per world as start/max injury, with a fixed start, a kernel that sums to 1, and
    no perceptual noise.
  - The trace sensitivity row replays the natural injury-70 episode's felt-injury trace step by step.
  - E1-natural is computed step-aligned on steps that are live in both episodes.
  - Every checkpoint's identity episodes are checked against the dwell-sweep CSV (bush dwell equal
    within CSV rounding; fatal otherwise).
- `scripts/analysis/modulator_engagement/analyze.py`:
  - Level-demeaned Spearman with the exact 216-arrangement within-level null, for P-main, P-own and
    the negative control.
  - The decision rule.
  - The secondary rows, the pooled ρ, within-level ρ, P-rank, the level-05 (and 05+06) own-scene
    sensitivity rows, P-out and P-cause.
  - Engagement is averaged over each pair's own tested grid points. A missing point is fatal.
- `tests/analysis/test_modulator_engagement.py` (8 tests) and `docs/environment/SCRIPTS_DEPENDENCY_MAP.md`
  (new row, a test-suite row, and caller updates for `nmn/{replay,ckpt_io,mod_distribution,freeze}`,
  `obs_manipulation` and `fast_heal_replication`).

### Choices the plan left open

The coordinator confirmed choices 1 and 2 below, and the `git archive` pin (see `outcomes.py` above),
on 2026-10-07 with the E4 go: "keep everything else as you chose".

1. **E1 site average.** `e1g_mean4` is the mean of the four non-critic FiLM heads (encoder unimodal,
   encoder multimodal, task GRU, actor), weighted equally. This is the same as pooling every
   non-critic unit, since every head has 128 units. The encoder therefore weighs 2 of 4, not 1 of 3.
   Per-site values are in the CSVs, so a 3-site average can be computed without re-running.
2. **E2/E3 episodes:** 128 greedy episodes in the training world, seeds 90000–90127, the defaults
   of the existing method-2/3 runners. The plan does not give a number.
3. **E3** freezes all five sites, as `freeze.py` does (the critic cannot affect behaviour).
   Conditions: gain frozen, offset frozen. `freeze_both` is not run.
4. **E4 freeze target:** per checkpoint, the per-unit time-mean over every live step of both rabbit
   scenes (injury 70 and 0, 30 episodes each), pooled step-weighted.
5. **Pair checkpoint set** = grid points where both agents' rabbit-scene injury effect was measured.
   This is 41 for every pair except level 04 seed 44 (39; its testing stopped at 9.6 M).

### Tests

- `tests/analysis/test_modulator_engagement.py`: **8 passed** (52 s, CPU).
  - Permutation null on synthetic data: exactly 216 level-preserving arrangements; a perfect
    within-level relation gets p = 1/216; a level effect alone gives demeaned ρ = −1 and p = 1;
    under independence the null is centred and p ≈ uniform; the decision-rule cases.
  - The identity condition reproduces the plain rollout exactly. On a real checkpoint (level 05
    seed 42, step 6000007), the tool's identity condition equals an independent `nmn.replay`
    rollout of the same seeds bit for bit (actions, lengths, per-unit γ and β), with |Δ| exactly 0.
    It also equals the dwell sweep's recorded agent positions (`_parity`).
    - Note: at a different batch size the two programs differ by ≤ 7e-7 (float32 rounding of a
      different compiled program), so the test compares at equal batch size.
  - E1 ≈ 0 for a modulator blind to nociception. The felt-injury row of the modulator GRU's input
    kernel is zeroed. E1 (γ, β; constant and trace; every site) is then < 1e-6, while the task
    network still reacts (bush dwell changes).
    - Positive control: the unedited checkpoint gives E1γ, E1β > 0.01, with both sweep checks
      matching.
- Existing tests: `tests/env/test_saved_config_compat.py`, `tests/analysis/test_nmn_freeze.py` and
  `tests/analysis/test_nmn_mod_distribution.py` give **53 passed**.
- Bug found while computing, and fixed in `3f4a8457`: E3's first row per run had one more column
  (the equivalence result), so the CSV schema guard stopped every E3 job after one checkpoint. No
  wrong numbers were written; the rerun resumed. No regression test was added: the guard itself
  caught the bug.

### Speed check

- `obs_manipulation/run.py` live mode, before versus after this change:
  - Setup: same command, 3 checkpoints, 30 episodes, CPU, run twice each.
  - Before: 22.6 s and 23.0 s. After: 23.1 s and 23.1 s. The change is about +1 %, within noise.
- The training hot path is untouched.

### Smoke-test number

Level 05 seed 42, checkpoint 6000007 (6.0 M steps), unhurt no-animal neutral scene:
- E1γ = 0.352 per unit per step, mean of the four sites; per site: encoder-uni 0.493, encoder-multi
  0.347, GRU 0.248, actor 0.321.
- E1β = 0.335.
- Shadow across-unit SD of γ = 0.550.
- The natural felt-injury trace peaks at 0.52 (healing starts before the 0.70 plateau), and its
  trace E1γ = 0.042.
- E1-natural γ = 0.077.
- Sweep checks: both match.

### Computation done (E1, E1-natural, E2, E3)

- **Where:** all under `results/analysis/modulator_engagement/`, run on local CPU with 7 workers
  (12:31–13:59 KST, 2026-10-07; no lab GPU used).
  - `outcomes.json` holds the behaviour gaps (pinned `10358a45`, provenance inside).
  - `e1/`, `e2/` and `e3/` hold one CSV per pair, with one row per checkpoint.
  - Each pair also has a manifest.
  - Batch scripts and logs are in `logs/`.
- **Coverage:** E1, E2 and E3 are 574 rows each, 14 pairs × 41 grid checkpoints, with 0 failed jobs.
  Every pair's tested checkpoint set is fully covered: 41 everywhere except level 04 seed 44, which
  has 39.
- **E1 checks:** at 572 of 574 checkpoints, the identity episodes reproduced the dwell sweep's bush
  dwell in both the unhurt and injured no-animal scenes.
  - The other 2 are level 04 seed 44 at 9.8 M and 10.0 M. Testing stopped there, so there is no
    sweep value; both points fall outside that pair's tested set and are not averaged.
  - Every scene was deterministic: one felt-injury trace group per checkpoint.
- **E2:** 128 greedy episodes per checkpoint in the training world (seeds 90000–90127).
- **E3:** paired survival steps under the gain freeze and the offset freeze, same episodes. The
  freeze-by-weight-edit equivalence check gave a worst deviation of exactly 0.0 on all 14 runs.
- **Not computed:** correlations, the permutation null or the verdict (`analyze.py`), and E4.

### E4 run (2026-10-07, after the coordinator's go)

- **Preparation** (local CPU, 7 workers, 13:59–14:09 KST): `engagement.py e4-prepare --pairs all
  --checkpoints every5`. This is 126 checkpoints, grid points 0, 5, …, 40 (2.0, 3.0, …, 10.0 M) for
  each pair.
  - The edited copies are under `results/analysis/modulator_engagement/e4/ckpts/JAX_RecurrentPPO/`:
    28 run folders, 598 MB. The originals were not touched; the writer refuses any path inside a
    source run.
  - The pooled freeze targets are saved as `targets_<pair>_<step>.npz`.
  - Every saved copy was read back bit for bit, and its frozen signal was checked constant at the
    target.
  - Live passes reproduced the original sweep's rabbit-scene bush dwell at 125 of 126 checkpoints.
    The exception is level 04 seed 44 at 10.0 M, which that sweep never tested.
- **Scoring:** the six generated specs in `e4/sweeps/` (same probe battery and 30 episodes as each
  outcome sweep; the two rabbit-wander scenes only) were run with `scripts/eval/dwell_sweep/run_sweep.py`.
  - Node: 104 (CPU, NPAR 18), 14:09–14:23 KST. It was chosen after `gpu_status`: 36 cores, load 0.3,
    NAS mounted, no diary claim today.
  - The node was claimed and released in the diary (`modeng_e4_sweep`).
  - Results: 56 CSVs under `results/eval/avoidance/metrics_history_rppo_modeng_e4/`, 9 checkpoints
    each, 0 failures.
- **Collected:** `engagement.py e4-collect` wrote `e4/e4_effects.csv`, 126 rows. Each row holds the
  modulated agent's rabbit-scene injury effect live, gain-frozen and offset-frozen.
  - The live column comes from the original outcome sweep CSVs.
  - Cross-check: the full sweep reproduces the earlier hand-scored smoke checkpoint exactly (level 05
    seed 42 at 6.0 M: live +8.25 pp, gain frozen −3.00 pp, offset frozen +7.63 pp).
  - Level 04 seed 44 at 10.0 M has no live value. `analyze.py`'s P-cause now drops any checkpoint
    lacking live or frozen values, so all three means use the same checkpoints: 8 for that pair, 9
    for the others.

### E4 budget (as estimated before the go)

- **`e4-prepare`** (local CPU): about 28 s per checkpoint, measured. Steps per checkpoint: two live
  rabbit passes, the pooled target, two edited checkpoints written and read back bit for bit, and a
  constancy check.
  - All 14 pairs × 9 checkpoints = 126 checkpoints: about 1 h of serial CPU, about 10 min with 7
    workers.
  - Disk: 252 × 2.5 MB ≈ 0.63 GB under `results/analysis/modulator_engagement/e4/ckpts/`.
- **Scoring sweep:** 252 checkpoint evaluations (126 × gain/offset) × 2 rabbit scenes × 30 episodes.
  - About 20–28 s each on CPU, measured with `eval_rollout.py` called exactly as the sweep worker
    calls it. That is about 1.5–2 CPU-process-hours in total.
  - **The dwell sweep runs on CPU (`--device cpu`), so the GPU budget is zero.** One lab node at
    NPAR = 8 would take about 15–20 min.
  - Restricting to the 9 main pairs: 162 evaluations, about 1–1.3 CPU-hours.
- The specs are generated with `nodes: []`, so nothing launches by accident. The training-runner
  fills the nodes after `gpu_status` and the diary check.
- Then `engagement.py e4-collect` and `analyze.py` (P-cause).
- Verified on one checkpoint:
  - `eval_rollout.py` restores the edited checkpoint without complaint.
  - On the original checkpoint it reproduces the sweep's bush dwell (0.1964 / 0.1139).
  - The frozen-gain copy scores (smoke only, not a result): rabbit-scene injury effect −3.0 pp,
    against +8.3 pp live.

### Follow-ups

- All inputs to `analyze.py --data results/analysis/modulator_engagement` now exist (outcomes,
  E1–E4). Running it, and the verdict, belong to the analysis step (experiment-analyzer, then
  plan-reviewer).

*Implemented by: developer*

## Results

*Written by experiment-analyzer, 2026-10-07, after the fixed rule above (Revision 1a) was applied
unchanged. Numbers from `analyze.py` at commit `f234ba9f`; outcome code pinned at `10358a45`.*

### What was found (plain language)

**The idea that some modulated agents have an "engaged" modulator and hide more, while others have an
"idle" one, is not supported. By the rule fixed before the computation, the main result counts
against it.** Across the 9 replication pairs, and comparing pairs only within the same training level,
the modulators that respond most to felt injury belong to the pairs where the modulated agent's lead
in injury-driven bush hiding is *smallest*, not largest. The rank correlation is −0.75, against the
+0.6 that "supports" would have needed.

Three further points matter as much as the verdict:

1. **There is no idle mode to find.** Every one of the 14 modulated runs responds to felt injury, and
   by similar amounts: the strongest response is only 1.5 times the weakest. A modulator that cannot
   see felt injury scores practically zero on the same measure, below one millionth (the developer's control
   test). So the runs differ in *how much* their modulator responds, never in *whether* it responds.
   The plan's premise of two modes is not what the data show.
2. **The negative result mostly comes from the ordinary partner.** The plan's negative control did not
   come out near zero; it came out at +0.78. Within a level, the pair whose modulator responds most
   tends to be the pair whose *ordinary* agent, which has no modulator, hides most when injured. The
   modulated agent's own injury effect is only weakly related to the modulator's response, and in the
   wrong direction (−0.43). A modulated-minus-ordinary gap then falls as the response rises. The plan
   assumed the ordinary partner's behaviour would be unrelated to its partner's modulator. That
   assumption is false here, and it is not explained by level, because level is removed before the
   correlation is taken. The only thing a pair shares beyond its level is its seed. With 3 pairs per
   level, this may also be chance (see Contradictions).
3. **The modulator does carry part of the injury effect, but this does not depend on how strongly it
   responds.** Freezing the modulator's gain at a fixed value removes on average about half of the
   modulated agent's injury-driven hiding in the rabbit scene (47 %; 7 of 9 pairs lose some).
   Freezing its offset removes none. The pairs that respond more strongly do not lose more when the
   gain is frozen, so the causal prediction is not borne out either.

The held-out pairs agree in part. The three level-05 fixed-start-temperature pairs show the same
negative relation. The two 22-September originals, which were chosen because they showed the effect,
both sit above their level on response and on gap, but two hand-picked pairs cannot set a direction.

Bottom line: on these checkpoints, how strongly the modulator responds to felt injury does not explain
which seeds show a modulated-agent advantage. The variation between seeds looks like ordinary
behavioural variation, with the ordinary partner's variation as large a part of the gap as the
modulated agent's.

### Data, provenance and cross-checks

- **Inputs:** `results/analysis/modulator_engagement/` (outcomes, `e1/`–`e3/` per-pair CSVs, `e4/e4_effects.csv`).
  `analyze.py` wrote `pair_table.csv`, `permutation_null.csv` and `stats.json` there (git HEAD
  `f234ba9f`). Working file: `tmp/20261007_142805_modulator_engagement_analyze.md`.
- **Outcome pinning:** the 9 main pairs and both originals come from `figures.py` at `10358a45`. The
  main pairs are asserted equal to the working copy (`main_pinned_equals_working: true`). The three
  `l05fix` pairs come from the working copy and are labelled so, as Revision 1a allows.
- **Independent cross-checks (analyzer):**
  - The rabbit-scene injury effect was recomputed directly from the dwell-sweep CSVs: `bush_hiding`,
    `avoid_rabbitwander_inj70` minus `inj00`, checkpoints 2–10 M. It matches `outcomes.json` exactly
    for three pairs:

    | Pair | Modulated (pp) | Ordinary (pp) | Gap (pp) |
    |---|---|---|---|
    | Level 05 seed 42 | 8.394 | 0.642 | 7.752 |
    | Level 06 seed 43 | 6.220 | 2.097 | 4.123 |
    | Level 04 seed 44 | 6.826 | −1.191 | 8.017 |

  - E1γ for the same three pairs, recomputed from the per-checkpoint E1 CSVs over each pair's own
    checkpoints, matches the pair table: 0.3331, 0.2606 and 0.2483 (39 checkpoints for the last).
  - The level-demeaned Spearman correlations and the 216-arrangement nulls were re-implemented
    separately with `scipy.stats.spearmanr`. P-main, P-own and the negative control are reproduced to
    every digit.
- **One small inconsistency in the outcome code:** for level 04 seed 44, the modulated agent's effect
  is averaged over its 39 tested checkpoints, but the ordinary agent's over 41.
  - On the matched 39, the ordinary effect is −1.87 rather than −1.19, and the gap is 8.69 rather
    than 8.02.
  - The pair stays the largest gap in level 04, so every within-level rank, and every correlation
    below, is unchanged.

### P-main: does the injury response predict the hiding gap? Counts against

| Statistic (9 main pairs, values demeaned within level) | ρ | One-sided p (216 arrangements, P(null ≥ observed)) |
|---|---|---|
| **P-main**: E1γ against the rabbit-scene injury gap (modulated − ordinary) | **−0.75** | 0.995 |
| **P-own**: E1γ against the modulated agent's own rabbit-scene injury effect | −0.43 | 0.903 |
| **Negative control**: E1γ against the ordinary partner's rabbit-scene injury effect | **+0.78** | 0.009 |

**Verdict under the fixed rule: counts against** (ρ ≤ 0).
- "Supports" was out of reach on P-main alone. It would have failed on P-own as well (−0.43 < 0.6),
  and it would have been withdrawn by the negative control (0.78 ≥ 0.6).
- For reference, the opposite tail of the P-main null is P(null ≤ −0.75) = 0.009 (2 of 216
  arrangements). The rule has no clause for a significantly negative relation, so this is reported, not
  used. It is close to a mirror image of the negative control.
- Pooled across levels, not demeaned (descriptive): P-main −0.42, P-own +0.28, control +0.63.

### P-rank: the 9 pairs ranked by E1γ (not borne out)

E1γ is the mean absolute change in the modulator's gain, per unit and per step, when felt injury is
set to 0.70. It is averaged over the encoder (two heads), memory and actor, and over the pair's own
checkpoints. Effects are rabbit-scene injury effects, injured 70 minus unhurt, in percentage points of
bush dwell, averaged over 2–10 M steps. The last column flags the pairs P-rank made a prediction for.

| E1γ rank | Pair | E1γ | E1γ − level mean | Gap (pp) | Modulated effect | Ordinary effect | P-rank prediction |
|---|---|---|---|---|---|---|---|
| 1 | Level 05 seed 44 | 0.356 | +0.012 | −1.73 | 7.10 | 8.82 | |
| 2 | Level 05 seed 43 | 0.343 | −0.001 | −5.80 | 3.36 | 9.16 | predicted bottom 3: **missed** |
| 3 | Level 05 seed 42 | 0.333 | −0.011 | +7.75 | 8.39 | 0.64 | predicted top 3: **hit** |
| 4 | Level 04 seed 43 | 0.326 | +0.026 | −3.28 | 6.62 | 9.90 | predicted bottom 3: **missed** |
| 5 | Level 04 seed 42 | 0.324 | +0.025 | +3.44 | 8.76 | 5.32 | |
| 6 | Level 06 seed 42 | 0.307 | +0.028 | −4.53 | 0.95 | 5.49 | |
| 7 | Level 06 seed 44 | 0.270 | −0.009 | −2.25 | 1.30 | 3.55 | |
| 8 | Level 06 seed 43 | 0.261 | −0.018 | +4.12 | 6.22 | 2.10 | |
| 9 | Level 04 seed 44 | 0.248 | −0.051 | +8.02 | 6.83 | −1.19 | predicted top 3: **missed (last)** |

- One of the four placements is right. Level 04 seed 44, the pair with the largest gap, has the
  *least* responsive modulator of all nine.
- The ranking is mostly a level ranking: level 05 high, level 06 low. Within a level the differences
  are small, 0.01–0.08.
- The standard error of each pair's E1γ across its checkpoints is 0.003–0.009 (treating checkpoints as
  independent, which flatters it). The level-04 and level-06 outliers (seeds 44 and 42, about 0.05
  from the rest) are clearly resolved. Level 05's three values (0.333, 0.343, 0.356) are only about
  two standard errors apart, and level 04 seeds 42 and 43 (0.324 against 0.326) are not resolved at
  all. So within-level ranks rest on small differences.

**Over training, E1γ rises in every pair** (mean over each third of the checkpoints, 2–4.6 M / 4.8–7.2 M / 7.4–10 M).
- Level 05 seed 42: 0.30 / 0.35 / 0.36. Level 06 seed 43: 0.19 / 0.29 / 0.30. Level 04 seed 44: 0.20 / 0.27 / 0.29.
- The gap does not follow it. In level 05 seed 42, the gap shrinks from +13.4 to +9.1 to +0.9 while
  E1γ rises. In level 04 seed 44, it grows from +3.8 to +11.7 while E1γ stays the lowest of all.
- A stronger response to felt injury is something every run acquires with training, independently of
  whether it hides more than its partner.

### Secondary rows (reported; none can rescue P-main)

All are demeaned within level, 9 main pairs, with one-sided p from the same 216-arrangement null. The
upper tail of that null is what a positive relation would need.

| Row | ρ | p |
|---|---|---|
| E1γ against the no-animal injury gap (shares E1's scene) | −0.77 | 0.977 |
| E1γ against the predator gap | −0.40 | 0.819 |
| E1γ against the shared baseline gap (unhurt, no animal; modulated − ordinary) | +0.67 | 0.069 |
| E1β (offset response) against the primary gap | −0.53 | 0.894 |
| E1-natural γ (natural injured against unhurt episodes; confounded by a different view) against the primary gap | −0.53 | 0.894 |
| Natural-trace sensitivity: E1γ with felt injury following the recorded injury-70 trace | −0.72 | 0.995 |
| Level-05 own-scene sensitivity (level-05 gaps from the own-scene set) | −0.75 | 0.995 |
| Same, levels 05 and 06 both from the own-scene set | −0.67 | 0.986 |
| E2, the share of gain variance that changes over time, in the training world | +0.12 | 0.454 |
| E3, the survival-step change from freezing the gain, in the training world | +0.83 | 0.014 |
| E3, the survival-step change from freezing the offset (analyzer's computation, same method) | −0.37 | 0.787 |
| Per-site E1γ against the primary gap: encoder-unimodal / encoder-multimodal / memory / actor (analyzer) | −0.47 / −0.57 / −0.80 / −0.65 | 0.88 / 0.89 / 0.99 / 0.99 |
| Three-site E1γ (encoder heads averaged as one site; analyzer) | −0.75 | 0.995 |

**Within-level ρ** (3 pairs each, descriptive; the only possible values are ±1 and ±0.5):

| Level | E1γ against the gap | E1γ against the modulated agent's effect | E1γ against the ordinary agent's effect |
|---|---|---|---|
| 04 | −1.0 | −0.5 | +1.0 |
| 05 | −0.5 | −0.5 | +0.5 |
| 06 | −1.0 | −1.0 | +1.0 |

How to read the secondary rows:
- **Every other way of measuring E1, and every other behaviour gap except the baseline, gives the same
  negative sign.** This includes the offset, the natural-trace version, every single site, the
  own-scene sensitivity rows, and the injury and predator gaps. The result does not depend on one
  choice of measure.
- **The natural-trace E1γ is about 8 times smaller** than the constant-0.70 version: 0.03–0.05 per
  unit per step, against 0.25–0.37. In the real injured episode, felt injury peaks at about 0.5 and
  then falls as the agent heals. The constant 0.70 is the stronger, off-distribution probe the
  re-review warned about. Both versions rank the pairs much the same.
- **E1γ against the shared baseline gap is +0.67** (p 0.069). Pairs whose modulator responds more tend
  to be pairs where the *unhurt* modulated agent dwells in the bush more than its partner, in the same
  no-animal scene E1 is measured in. This is the scene-sharing link that the first plan review flagged,
  and it is why the baseline was kept out of the primary outcome.
- **E3 against the gap is +0.83** (p 0.014), but in a direction that does not help the mode idea.
  - E3 is frozen minus live survival steps; every value is negative, from −15 to −49 steps on a live
    survival of 255–315 steps.
  - Pairs where freezing the gain costs the *fewest* survival steps have the *largest* injury gap. So
    the agents that depend least on their gain's moment-to-moment variation in their own world hide
    more.
  - This is one of more than a dozen secondary correlations, with no correction for multiple comparisons. Treat it as a lead,
    not a finding.
- **Per-pair secondary values:**

  | Pair | E1β | E2 (gain) | E3 gain freeze (survival steps) | E3 offset freeze (survival steps) | Live survival (steps) |
  |---|---|---|---|---|---|
  | Level 04 seed 42 | 0.309 | 0.205 | −20.5 | −47.6 | 314.9 |
  | Level 04 seed 43 | 0.336 | 0.157 | −49.0 | −42.4 | 314.3 |
  | Level 04 seed 44 | 0.251 | 0.150 | −24.2 | −38.8 | 313.6 |
  | Level 05 seed 42 | 0.318 | 0.147 | −28.8 | −48.4 | 281.5 |
  | Level 05 seed 43 | 0.322 | 0.153 | −37.6 | −26.7 | 285.9 |
  | Level 05 seed 44 | 0.337 | 0.170 | −29.1 | −30.4 | 285.8 |
  | Level 06 seed 42 | 0.266 | 0.120 | −25.4 | −32.8 | 257.0 |
  | Level 06 seed 43 | 0.266 | 0.151 | −15.2 | −31.6 | 255.4 |
  | Level 06 seed 44 | 0.241 | 0.186 | −19.0 | −32.8 | 259.9 |

  (Level 04 seed 44's E3 values are over its 39 tested checkpoints; its live survival is over all 41.)

### P-cause (E4): does freezing remove more of the effect where the response is stronger? Not borne out

- **Method.** At 9 checkpoints per pair (2, 3, …, 10 M; 8 for level 04 seed 44), the modulated agent's
  rabbit-scene injury effect was rescored in three versions:
  - live;
  - with the gain frozen at its pooled per-unit time-mean;
  - with the offset frozen at its pooled per-unit time-mean.
- "Share removed" is 1 − frozen/live, as `analyze.py` computes it. A share above 1 means the frozen
  effect reversed sign. A negative share means freezing *increased* the effect.
- Because several live effects are near zero, which makes the share unstable, the table also gives
  the effect removed in percentage points, with a 95 % t-interval across that pair's checkpoints
  (analyzer's computation).

| Pair | E1γ | Live effect (pp) | Gain frozen: share removed | Gain frozen: pp removed [95 % CI] | Offset frozen: share removed | Offset frozen: pp removed [95 % CI] |
|---|---|---|---|---|---|---|
| Level 04 seed 42 | 0.324 | 11.81 | −0.26 | −3.1 [−9.5, 3.2] | −0.74 | −8.7 [−21.8, 4.4] |
| Level 04 seed 43 | 0.326 | 9.59 | 0.30 | 2.9 [−5.7, 11.4] | 0.03 | 0.3 [−4.1, 4.8] |
| Level 04 seed 44 | 0.248 | 6.49 | 0.13 | 0.8 [−5.1, 6.8] | −0.12 | −0.8 [−7.0, 5.4] |
| Level 05 seed 42 | 0.333 | 8.22 | 1.05 | 8.6 [−3.9, 21.2] | 0.14 | 1.1 [−4.1, 6.3] |
| Level 05 seed 43 | 0.343 | 3.48 | −0.35 | −1.2 [−24.3, 21.9] | −2.72 | −9.5 [−29.0, 10.1] |
| Level 05 seed 44 | 0.356 | 10.51 | 1.01 | 10.6 [−3.4, 24.6] | 0.67 | 7.0 [−4.0, 18.0] |
| Level 06 seed 42 | 0.307 | 1.55 | 2.19 | 3.4 [0.3, 6.4] | 1.19 | 1.8 [−0.9, 4.6] |
| Level 06 seed 43 | 0.261 | 5.41 | 0.55 | 3.0 [−3.9, 9.8] | 0.34 | 1.8 [−2.5, 6.2] |
| Level 06 seed 44 | 0.270 | 1.12 | 2.11 | 2.4 [−0.1, 4.8] | 0.26 | 0.3 [−9.9, 10.5] |
| *Out of sample:* Level 05 fixed start, seed 42 | 0.327 | 5.02 | 2.39 | 12.0 [−1.5, 25.5] | 0.20 | 1.0 [−4.4, 6.4] |
| *Out of sample:* Level 05 fixed start, seed 43 | 0.354 | −4.37 | 1.28 | −5.6 [−16.3, 5.1] | −0.18 | 0.8 [−10.2, 11.8] |
| *Out of sample:* Level 05 fixed start, seed 44 | 0.346 | 11.84 | 1.23 | 14.6 [−1.3, 30.5] | −0.19 | −2.3 [−6.4, 1.9] |
| *Out of sample:* 22-Sep original, level 04 | 0.303 | 15.44 | 0.46 | 7.1 [−0.7, 15.0] | 0.38 | 5.8 [−10.0, 21.6] |
| *Out of sample:* 22-Sep original, level 05 | 0.372 | 12.73 | 0.68 | 8.7 [−3.4, 20.8] | 0.37 | 4.8 [−4.2, 13.7] |

- **Main 9 pairs, pooled.** The mean live effect is 6.46 pp. With the gain frozen it is 3.43 pp, so
  47 % is removed: 3.0 pp, 95 % CI across pairs [−0.3, 6.4]; 7 of 9 pairs are positive. With the
  offset frozen it is 7.19 pp, so −11 % is removed: −0.7 pp [−4.7, 3.3].
  - So the gain, not the offset, carries some of the injury effect. This is the closest thing to a
    positive finding in this check.
  - Per pair, though, only one interval excludes zero (level 06 seed 42, gain).
  - At 30 episodes per scene, a single checkpoint's frozen score is noisy. For example, level 04
    seed 42 at 2 M scores +67 pp with the offset frozen, against +16 pp live.
- **Relation to E1γ (descriptive).**
  - In the 4 main pairs above the median E1γ, freezing the gain removes a mean share of 0.50. In the
    5 at or below the median, it removes 0.94. That is the opposite of the prediction.
  - Rank correlation of E1γ with the share removed by the gain freeze: −0.12 (pooled). With the
    percentage points removed: +0.30 pooled, +0.07 demeaned within level (analyzer).
  - None of these is a relation. **P-cause is not borne out.**

### P-out: do the held-out pairs repeat the sign? Partly

- **Three level-05 fixed-start-temperature pairs** (outcomes from the working copy):

  | Pair | E1γ | Gap (pp) | Modulated effect | Ordinary effect |
  |---|---|---|---|---|
  | Seed 42 | 0.327 | +5.17 | 6.86 | 1.69 |
  | Seed 43 | 0.354 | −6.98 | 0.98 | 7.96 |
  | Seed 44 | 0.346 | −2.04 | 10.57 | 12.61 |

  - Raw ρ(E1γ, gap) = **−1.0**, the same sign as the main set. The same split repeats: E1γ against the
    modulated agent's effect is −0.5, and against the ordinary agent's effect it is +0.5.
  - With 3 pairs, ρ = −1 has a chance probability of 1/6.
- **Two 22-September originals**, reported apart because they were selected for showing the effect.
  Two points from two different levels cannot give a correlation, so each is placed against its level's
  three main pairs:
  - **Level 04 original:** E1γ 0.303, against a main level-04 mean of 0.299 (range 0.248–0.326). Its
    gap is +8.57, against a level mean of +2.73.
  - **Level 05 original:** E1γ 0.372, above all three main level-05 pairs (0.333–0.356). Its gap is
    +10.18, against a level mean of +0.07.
  - Both sit above their level on gap, which is guaranteed by how they were chosen. On E1γ, the level-05
    original is high and the level-04 original is ordinary. Their direction is the opposite of the main
    set's, but the selection makes this uninformative.
- All five together (raw, mixing levels, descriptive): ρ = 0.0.

### Contradictions with the plan's assumptions

1. **"Idle" modulators do not exist in this set.**
   - The plan's motivation pictured some runs with a modulator "close to a constant rescaling".
   - Across all 14 runs, E1γ lies between 0.248 and 0.372 per unit per step. That is 53–72 % of the
     gain's own spread across units (0.43–0.57). A modulator blind to felt injury gives below 1e-6.
   - The question the plan could answer was therefore "do *more* responsive modulators go with larger
     gaps?", not "do engaged ones differ from idle ones?". The answer to the first is no.
2. **The ordinary partner is not independent of its modulated partner's engagement.**
   - The negative control was "expected near 0", and the plan read a value ≥ 0.6 as "a level or scene
     artefact".
   - Level is removed by demeaning, and the ordinary agent's effect is measured in the rabbit scene,
     which E1 does not use. So neither explanation the plan offered fits.
   - The remaining candidates are:
     - something tied to the shared seed, such as the same environment random stream during training;
     - chance. With 3 pairs per level and 216 arrangements, two arrangements reach this value, and many
       correlations are reported here.
   - Either way, any modulated-minus-ordinary gap from these pairs carries as much of the ordinary
     partner's seed-to-seed variation as the modulated agent's. This matters for reading the
     replication's per-seed gaps generally, not just for this check.
3. **Pair checkpoint sets differ slightly from what the plan describes.** The plan says level 04
   seed 44's outcome uses its own tested checkpoint set, but the ordinary side is averaged over 41.
   This is harmless here (see Data), but it is worth fixing in the outcome code.

### Follow-ups for the user (not acted on)

- A plan-reviewer verdict gate on this Results section, then the PI, per the project's analysis flow.
- If the shared-seed link (Contradiction 2) matters for the modulator-input study's design, a direct test
  is cheap and needs no training. Correlate the ordinary agents' injury effects with their *modulated
  partners'* effects within level, across all 12 non-original pairs. This is a question for
  experiment-designer.
- E4's per-checkpoint scores use 30 episodes per scene. Most per-pair intervals span ±5–25 pp. A
  pre-registered rerun of the gain freeze with more episodes, on the main 9 pairs, would show whether
  the pooled 47 % holds pair by pair.
