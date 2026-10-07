# Plan review: modulator engagement check

Reviewed by: plan-reviewer · 2026-10-07 · object: [[MODULATOR_ENGAGEMENT_CHECK]] (untracked draft, before any computation)

## Verdict

**NOT READY** — fixable with edits to the plan; no new training is involved.

**What the plan wants to do.** In the fast-bush-healing replication, nine pairs of agents were trained
(an ordinary one and one with a neuromodulator, three levels × three seeds). The modulated agent beat its
partner in some pairs and not others. The plan asks whether the pairs where it won are the ones where
its modulator actually changes its output when the body is hurt. The main measure (called E1) compares
the modulator's gains and offsets between two replays of the same small test scene: one where the agent
starts injured and one where it starts unhurt.

**Why it is not ready.** As written, a positive result could not be interpreted. The modulator reads the
agent's whole observation, including what it sees. In the no-animal test scene, an injured agent walks
to the bush and an unhurt one does not, so the two replays see different things after a few steps.
The modulator's output then differs whether or not it responds to injury at all. That makes E1 largely
a re-measurement of the behaviour it is supposed to explain. The test scene is also deterministic: all
30 episodes are the same trajectory, so E1 and the "injury, no animal" behaviour measure come from the
**same trajectory pair**. Two more problems: the planned safeguard against this circularity (the
predator measure) shares its baseline scene with E1; and the named replay tool cannot run test scenes.

**What flips it.** Define E1 so that only the injury input differs and behaviour cannot feed back.
Correct the predator safeguard. Name the tool that will actually run E1 (the existing
observation-manipulation tool is close). Fix the decision rule at n = 9, including the level structure.
Commit the plan before any engagement number is computed.

## Findings

Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run · 🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

| # | sev | location | issue | suggested fix | owner |
|---|---|---|---|---|---|
| 1 | 🔴 | plan §Engagement measures, E1 | **E1 is behaviour-contaminated, so it is circular.** The modulator reads every input (`input_sensors: all`, saved config of every t16quad run). In the injured replay the agent reaches the bush 3 cells away within a few steps; in the unhurt replay it does not. Vision, position and smell then differ, so γ/β differ even for a modulator with zero injury sensitivity. Worse, felt injury lags the true injury (`interoceptive_kernel_tau: 3`; it is 0 at reset, INJURY_DEPENDENCE_PLAN §Risks 4), so the injury signal *rises while the trajectories are already diverging*. On top of that, the scene is deterministic: per-checkpoint `bush_hiding` values are k/101 (e.g. `l04_core/l04_modulated_s44/avoid_none_inj70.csv`: 0.5545 = 56/101), so all 30 episodes are one trajectory. E1 and the "inj" gap would therefore be computed on the same trajectory pair. A positive P-main/P-own is then expected even under the null. | Redefine E1 as a **teacher-forced counterfactual**: take the unhurt scene's observation stream and replace only the felt-injury slot (`Interoceptive Nociception`) with the injured replay's felt-injury trace (or a `set` 0.7 ladder). Run the network on that stream without letting its actions change the world, and difference γ/β against the unmanipulated stream. Actions and visual input are then identical by construction. Keep the natural-scene version as a labelled secondary measure. | experiment-designer (definition), developer (tool) |
| 2 | 🔴 | plan §What would mislead, bullet 4 | **"The predator gap, a scene E1 never used" is false.** `figures.py:80-82` defines pred = (predator, injury 0) − (no animal, injury 0). The second term is E1's unhurt replay, and it is also the baseline of the "inj" measure. Inj and pred therefore share the term −(mod − ord bush dwell in the no-animal, unhurt scene), which by itself makes the two gaps co-move. That shared term also accounts for part of motivating pattern 2 ("seeds move as one"). | The only behaviour measure that shares no scene with E1 is **injw** (wandering rabbit, 70 − 0). Make injw the out-of-scene test. Also report E1 against the shared baseline gap itself (no animal, unhurt, mod − ord). If E1 predicts the baseline, the "relation" is a scene artefact. | experiment-designer |
| 3 | 🟡 | §Engagement measures, tools | **The named tool cannot do E1.** `replay.load_agent` (`scripts/analysis/nmn/replay.py:66-168`) always builds the world from the run's own `models/config.yaml`; there is no way to load a probe scene or set the starting injury (`jax_reset` uses the training world's params). The tool that can is `scripts/analysis/obs_manipulation/run.py` (`--world <probe>`, `set`/`add` on `Interoceptive Nociception`, dwell-sweep parity check). But it records only the **unit-mean** gain/offset per site (`run.py:135-137`), not per-unit γ/β, and its world follows the *manipulated* network, not a frozen trajectory. The "analysis-only" framing hides the code change this needs. | State the tool explicitly: extend `obs_manipulation` with per-unit γ/β recording and a teacher-forced mode (world follows the identity condition; a side copy sees the manipulated inputs). This is a `developer` change, so `SCRIPTS_DEPENDENCY_MAP.md` must be updated in the same change. Run its existing parity check against the healrep sweep recordings before use. | developer |
| 4 | 🟡 | E2/E3, run discovery | **The E2/E3 runners will not find these runs.** `ckpt_io._RUN_RE` (`scripts/analysis/nmn/ckpt_io.py:53-57`) matches only `nmnsite|nmngaenorm|olfmc|olfgae|basicq2|bq2cover` with `lvlNN_`; `healrep_l04_…` and `healrep_l05fix_…` match neither the grid name nor the level pattern. A naive regex widening would also pick up the **dead level-06 seed-42 folders** (`20261005-160128_…t1none_s42`, `20261005-160249_…t16quad_s42`). Both have a `models/` directory with no checkpoints, so `list_steps` raises, or the seed-42 tag gets duplicated. | Pass an explicit run list (the 9 + 5 folders, written once into the plan) instead of regex discovery, or exclude by folder name. Assert exactly one modulated run per (level, seed). | developer |
| 5 | 🟡 | §Predictions, G | **G is dominated by the predator gap and is construct-mismatched to E1.** Pred gaps run from −12.4 to +25.8 pp; injury gaps from −6.6 to +9.5 pp. A raw mean of the three is mostly the predator response, measured at injury 0. Injury responsiveness (E1) has no stated mechanism for predicting it. | Primary outcome = mean of the two **injury** gaps (inj, injw), with pred reported separately. Alternatively, make G a mean of within-measure ranks or z-scores. Fix the choice now. | experiment-designer |
| 6 | 🟡 | §Predictions, P-own | **P-own has no threshold and no combination rule.** "Correlates positively" can be satisfied by ρ = 0.1. The plan also never says what P-main supported plus P-own failed would mean. | P-own at the same ρ ≥ 0.6 bar, on the modulated agent's **injw** effect (not the no-animal effect, which shares E1's trajectory). Add a **negative control**: E1 against the *ordinary* partner's injury effect. If that correlation is as strong as the gap correlation (negatively), the gap relation comes from ordinary-agent noise. Write the rule as "mode supported only if P-main ≥ 0.6 AND P-own ≥ 0.6 AND the negative control is near 0". | experiment-designer |
| 7 | 🟡 | §What would mislead, level confound | **The level guard is descriptive only and cannot rule the confound out.** Within-level Spearman with 3 pairs can only take the values ±0.5 or ±1. A pooled ρ over 9 is open to a Simpson effect, because E1 is measured in a different scene per level (core / thermal neutral clean / thirst neutral). E1's scale may differ by level even if G does not (level means of G ≈ +4.5, +0.5, +2.0). | Make the decision statistic level-stratified: the mean within-level rank correlation, with a **within-level permutation** null (3!³ = 216 permutations, minimum p ≈ 0.005). Report the pooled ρ alongside it. Pre-register that a pooled ρ ≥ 0.6 with a stratified ρ ≤ 0 counts as "level artefact", not support. | experiment-designer |
| 8 | 🟡 | §Engagement measures, checkpoints | **5 checkpoints is too few against a noisy single-trajectory measure, and too few for the deterministic scene's cheapness.** Per-checkpoint dwell swings 0.55 → 0.15 → 0.50 between neighbouring checkpoints (same CSV). Behaviour uses 41 grid checkpoints (39 for l04 s44, `figures.py:143-147`), and each checkpoint here is one trajectory, so all 41 are cheap. | Compute E1 on the **same** grid checkpoints the behaviour uses for each run (`checkpoint_stats.on_grid`, 2–10 M at 0.2 M), not 5. Optional, and more powerful: the within-run checkpoint-level association of E1 with the modulated agent's own injury effect. It is immune to between-run and level confounds. | experiment-designer |
| 9 | 🟡 | §Engagement measures, E1 normalisation | **The normaliser is ill-conditioned and partly measures something else.** Dividing by the across-unit SD of γ in the unhurt run rewards a near-uniform γ (tiny denominator, inflated E1). It also penalises a modulator with large static per-unit re-tuning, which is the very spread E2 calls "not contextual". "Across-unit SD" is not defined per step, pooled, or per checkpoint. The critic site (`sites.critic: true`) cannot affect behaviour, yet it enters "mean over sites". | Primary E1 = raw mean \|Δγ\| per site (γ is a dimensionless gain applied after LayerNorm, so raw units are interpretable). Secondary = the change in the modulated pre-activation, \|Δγ·a + Δβ\| / sd(a), which combines γ and β on one scale. Exclude the critic from the site mean; report encoder (uni + multi), GRU and actor separately. Fix all of this in the plan. | experiment-designer |
| 10 | 🟡 | §Predictions | **Power and the "unclear" band are not stated.** At n = 9 a true ρ of 0.5 reaches the 0.6 bar only about 35 % of the time, so "unclear" is the most likely outcome. The plan needs to say what "unclear" licenses. | Add one line: "unclear" is reported as unclear, never as "partly supports", and does not by itself justify the "make it engage in every seed" direction. | experiment-designer |
| 11 | 🟡 | §Units / §Behaviour gap | **Scene-choice sensitivity is a known flip for level 05.** In the own scenes the level-05 sign reverses (1/3 vs 3/3; wiki `20261006_0758_test_scene_confound_level05_modulator_gap`, `20261007_1142_…`). | Pre-specify a sensitivity row: G and the correlation recomputed in the own scenes (`l05_own`, `l06_own` exist). A conclusion that holds in only one scene set is reported as scene-dependent. | experiment-designer |
| 12 | 🟡 | doc state | **"Fixed before any engagement number" is not verifiable.** The plan is untracked (`?? docs/experiments/active/modulator_clues/MODULATOR_ENGAGEMENT_CHECK.md`). `figures.py`, which the gaps are read "through", has uncommitted edits from another session (the l05fix arm). | Commit the revised plan, and the figures.py state it relies on, **before** any E computation, and cite the SHA in the results section. | plan owner |
| 13 | 🟢 | §Question, motivation | Pattern 2 overstates: only 4 of 9 replication pairs have all three gaps the same sign. The other 5 are mixed (e.g. l05 s44: −0.2, −1.7, +11.2; l06 s43: +3.8, +4.1, −4.7). Pattern 1's "behind by only a little" is contradicted by l05 s43 pred −12.4. | Soften the wording to "4 of 9 pairs". | plan owner |
| 14 | 🟢 | doc hygiene | No cross-link from [[FAST_HEAL_REPLICATION]] to this plan. E3 runs in the training world, so it measures survival cost rather than the behaviour gap. | Add a back-link. See the alternative-explanation note below for an E3 variant. | plan owner |

## Assumptions

| assumption | status |
|---|---|
| l06 seed-42 = `20261005-170252_…t1none_s42` + `20261005-170314_…t16quad_s42` | **verified**: the sweep spec `configs/eval_sweeps/healrep/healrep_l06_neutral_rppo.yaml` points there; both have 50 checkpoints and `seed: 42`; the 16:01 folders hold no checkpoints |
| Replay tooling can set starting injury and capture per-unit γ/β in a test scene | **false** for `replay.py`; partial for `obs_manipulation` (unit-mean only) |
| Changes in γ between the injured and unhurt replays reflect injury responsiveness | **false as defined** (finding 1) |
| The predator gap is independent of E1's scene | **false** (finding 2) |
| E2/E3 runners can discover the healrep runs | **false** (finding 4) |
| Out-of-sample l05fix behaviour metrics exist | ❓ the runs are trained (50 checkpoints each); `figures.py` returns no l05fix numbers today, so the tests have not finished or written their files yet |
| The deterministic no-animal scene gives one trajectory per checkpoint | **verified** (k/101 values) |
| FiLM γ is the raw applied gain (no sigmoid) | **verified**: `recurrent_ppo_network.py:273-276` |

## Alternative explanation a positive result would still not rule out

Even with a clean, teacher-forced E1, both networks learn from the same gradients and the modulator reads
the injury input. A run whose *main* network became strongly injury-sensitive could also have a modulator
that tracks injury, without the modulator causing the behaviour. The direct test would scope E3 to the
behaviour: freeze the modulator at its per-unit mean (`freeze.apply_freeze`, equivalence check as built)
**in the test scenes**, then measure how much of the modulated agent's injury effect, and its gap over the
partner, disappears. Recommended as the secondary measure that can upgrade "consistent with" to "explained by".

## Cost of being wrong

Running the plan as written would take about a day of GPU and analysis time. The bigger cost is that it
would probably return a positive correlation by construction. That would commit the next direction
("make the modulator engage in every seed") to an artefact, wasting weeks of training. Nothing destructive
is involved.

## Prior art checked

- Known Bugs: no row for replay/E1 tooling. Relevant: the `start_injury` dead-knob note (set injury via
  `start_injury_low/high`, as the probes do) and row 141 (replay recompiles; time cost only).
- [[INJURY_DEPENDENCE_PLAN]] built the observation-manipulation tool and already flagged that a clamp on
  felt injury reaches the modulator too (its plan-reviewer feedback). This plan should reuse that tool rather
  than `replay.py`.
- Wiki `20261007_1142_fast_heal_replication_modulator_effect_not_replicated`: training is not reproducible
  seed-for-seed, and ordinary-agent variation is as large as the agent difference. This supports P-own and
  the negative control.
