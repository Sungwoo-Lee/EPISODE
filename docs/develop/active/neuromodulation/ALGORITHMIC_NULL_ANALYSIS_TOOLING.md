---
title: "Analysis tooling for 'What Both Agents Compute' — layer capture, stored-episode replay, similarity, decoding, modulator wake-up"
topic: neuromodulation
status: active
created: 2026-09-29
last_updated: 2026-09-30
---

# Analysis tooling for "What Both Agents Compute"

> **Status**: PLANNED, **Revision 4** (2026-09-30): decisions raised by the Stage 0–2/5 Implementation Report and the code review of those stages (§Revision 4). Stages 0, 1, 2 and 5 are implemented (Implementation Report). Revision 3 (2026-09-30) answered `plan-reviewer`'s third review; Revision 4 awaits `plan-reviewer`. The R4-1 collector change must land before the May-replication collection.
> **Opened**: 2026-09-29
> **Related**: the published plan page [[algorithmic_null]] (`docs/experiments/active/modulator_clues/algorithmic_null.template.html`), its running list [[ALGORITHMIC_NULL_TODO]], the evidence file [[CROSS_STUDY_NULL_DOSSIER]], the three-seed May replication design [[MAY_DOUBLE_RETURN_REPLICATION]], the earlier gradient audit [[TRAINING_HEALTH_AUDIT]], the collection pipeline [[TRAJECTORY_COLLECTION_PIPELINE]], the saved-config compatibility plan [[SAVED_RUN_CONFIG_COMPAT]], the modulation-site refactor [[MODULATION_SITE_REFACTOR]]. Review: [[plan_algorithmic_null_tooling]] (`docs/reviews/plan_algorithmic_null_tooling.md`).

---

## Context

**What this is.** The project trains two kinds of recurrent agent: an ordinary one, and one with a small side network (the *modulator*) that rescales and shifts units inside the main network at every step. Across a month of studies they come out almost the same, in very different worlds. The page "What Both Agents Compute" reorders the open questions. First: **what do the two agents compute internally, and is it the same thing?** Second: **why does the modulator not help?** It lists the analyses that would answer them. None can run yet, because the tools do not exist. This plan specifies those tools. It covers analysis software only; it launches no training.

**What it builds.**
- A switch that makes the network also return its internal layer activity. With the switch off, nothing changes.
- A way to replay a stored episode's exact observations through any agent.
- Scripts that compare two agents layer by layer, and that read hunger, injury, predator distance and remaining survival time out of each layer.
- Measures of when, during training, the modulator starts to matter.
- Figure checks for the page builder.

**What changed in Revision 1.** A reviewer found two ways the tools could print a wrong sentence without any error. The "modulator wakes up at checkpoint *k*" measure could misfire on quantities that shrink or that end where they began; it now follows the direction of the change, refuses to name a checkpoint when the change is within noise, and starts from the untrained network. And nothing fixed in advance what counts as "the two agents compute the same thing"; `experiment-designer` has since written those rules down, before any number exists (§Revision 1).

**What changed in Revision 2.** The rules now exist as a separate file, and the reviewer found that this plan and that file described different tools. This plan now adopts the file's design. Every analysis manifest pins the rules file by its fingerprint (a sha256 hash), the pilot included. The rules stay in plain words; the tooling turns each rule's logic into tested code and takes every number from a `parameters:` list inside the rules file, so no threshold is typed into a script. The plan also now computes five inputs the rules need and it did not produce: three untrained reference networks (one per ordinary seed), within-stage drift for the across-worlds analysis, survival and food intake from the training logs, the rules' "clock-only" baseline, and the rules' bootstrap. It also sizes the probes so there are enough independent episodes (§Revision 2).

**What changed in Revision 3.** The reviewer found one way the wake-up measure could print a wrong sentence. Two of its six measures were to be sampled only at every fifth saved checkpoint early in training, which is where the modulator wakes up. A measure that truly woke at the same time as survival levelled off would then be reported up to four checkpoints *late*, on every world alike, and the across-worlds count would turn that rounding into a finding. Every wake-up measure is now sampled at every checkpoint, which roughly doubles the wake-up sweep. The sweep also now starts with a cheap check on the training logs that every run's survival actually levels off at a nameable checkpoint. The rest are wording fixes that align the plan with the committed rules (§Revision 3).

**What changed in Revision 4.** Building the first stages showed that a recorded episode replays exactly only in the arithmetic mode it was recorded in, and graphics cards differ in their default mode. Every future store is now recorded in full 32-bit arithmetic and says so. The plan also cuts the saved layer activity from about 200 GB to about 43 GB by keeping only what the pre-registered rules read, makes the trainer and the analysis share one recipe for each run's starting network, and fixes a few smaller points (§Revision 4).

**Why now.** One pair of agents from an earlier 16-world study already has stored episodes and loads under current code, so the tools can be built and checked on it today. A second study is still training: a replication of a May experiment with three seeds of each agent. It is the only design that can say whether two agents are "the same" by more than two ordinary agents from different seeds are. The plan is staged, so partial results reach the page before that training ends.

---

## Revision 1 — response to plan-reviewer (2026-09-29)

| # | Finding | Disposition | Where |
|---|---|---|---|
| 1 🔴 | Wake-up definition degenerates on falling and rise-then-return curves; `m₀` is mid-training | **Fixed.** Signed crossing, a noise-band guard that returns NaN with a reason, and an untrained-network anchor rebuilt through `train.py`'s own code path. **Correction to the review:** the network is not built from `model_key` at `train.py:1153`. That key is never used. The network's key comes from a second split at `train.py:1207`, and a reconstruction that follows the review's recipe would build the wrong network. The anchor is verified against a real `train.py` construction, so it cannot silently diverge | §B2, File Changes §11, Checkpoints 4.1, 4.4 |
| 2 🔴 | No pre-registered rule for "same computation" | **Referenced, not written here.** `experiment-designer` writes the `decision_rules` block into the May-replication analysis manifest. The tools read it, stamp its hash on every output, and print no verdict without it. The block must be committed before the first similarity output of any manifest, the pilot included | §E, File Changes §8, Stage R, Checkpoint R.1 |
| 3 🟡 | Side outputs are pinned only on synthetic weights | **Fixed.** Run-time chain assertions on real checkpoints at every captured key and site | File Changes §4, Checkpoint 2.3 |
| 4 🟡 | Satiation R² cannot see a one-row shift; shift control has no number | **Fixed.** A step-discontinuous alignment check through the probe's own row index, a one-pass row index, and numeric bounds | §Probe sets, Checkpoint 2.2 |
| 5 🟡 | Gradient probe is not like-for-like with the logged mean | **Fixed.** The probe runs the trainer's own `update_step` for the run's `K_epochs` updates on a throw-away copy and reports the same mean. The band is labelled a sanity band | §D, File Changes §11, Checkpoint 4.2 |
| 6 🟡 | Timestamp globs match 2 of 6 WandB folders | **Fixed.** Resolution by `--tag` (exactly one hit); six logs listed by path | §C, File Changes §7, §12 |
| 7 🟡 | Shared `figures/` folder | **Fixed.** Own subfolder `figures/algorithmic_null/`; the unused-figure check never looks outside it | File Changes §9, §10 |
| 8 🟡 | Collector fingerprint unspecified | **Fixed.** Exact dict defined, plus three tests | File Changes §5 |
| 9 🟡 | `steps_remaining` rewards the clock | **Fixed.** Censored-excluded is the headline; time-only baseline and the excess over it are reported per layer | §A2 decoding |
| 10–14 🟢 | Paths, stage numbering, group key, CKA tolerance, `enc.uni.*` shape | **Fixed** | inline |
| ❓ | `make_jaxpr` capture | **Tested today; works.** Method and hashes in Checkpoint 1.3 | Checkpoint 1.3 |
| ❓ | Stage 4 compute | **Budgeted**, with a timing gate | §Stage 4 budget |
| ❓ | WandB-to-episode join | **Resolved by reading the binaries** | File Changes §7 |

**Where I depart from the review.**
- The untrained-network key (above): `split(PRNGKey(seed), 3)` alone is not enough; the second split is needed.
- The review's fingerprint list (`environment`, `sensory`, `body`, `thermal`, `perceptual_noise`) is used. The plan adds one rule: any *other* top-level key that differs between the stage file and `config.yaml`, apart from `agent`, `tag` and `wandb`, is an error rather than silently kept. A future stage file that changes `training.*` would otherwise pass unnoticed.
- `stage_end:<k>` is redefined as **the last saved checkpoint whose saved `stage` field equals *k***, not "the first checkpoint at or after boundary *k*". `eval_rollout._resolve_continual_stage_config` documents that a checkpoint's recorded stage can lag the boundary by one. Under the old rule, the checkpoint just past boundary *k* could still be a stage-*k* checkpoint, or it could be the first of stage *k*+1.
- **Which manifest holds the rules.** *[Superseded by Revision 2, R1: the rules live in their own file, pinned by `decision_rules: {file, sha256}` in every manifest. The text below is kept as history.]* Two manifests are meant, and they are different files:
  - **May replication (evidence):** `docs/experiments/active/modulator_clues/algorithmic_null_mayrep.yaml`, a new file. The May design doc has no analysis-manifest YAML (its launch manifest is a table in [[MAY_DOUBLE_RETURN_REPLICATION]]), so this file is the one that governs these analyses. `decision_rules` goes here, and `experiment-designer` owns that block.
  - **Pilot:** `docs/experiments/active/modulator_clues/algorithmic_null_pilot.yaml`, a new file with `decision_rules_ref: null`. The pilot compares two agents that share seed 42 and has no seed yardstick, so no rule can apply to it. It prints numbers and no verdict.
  - **Not a target:** `docs/experiments/active/level05_body_interactions/analysis_manifest.yaml` is the *schema precedent* and the source of the level-05 WandB ids. It belongs to the level-05 store scripts, which would never read a `decision_rules` block placed there. If `experiment-designer` has already put the block elsewhere, `decision_rules_ref` points at it, so no content has to move (File Changes §8).

---

## Revision 2 — response to plan-reviewer's re-review (2026-09-30)

The re-review ([[plan_algorithmic_null_tooling]] §Re-review) ruled for this plan on all four earlier disagreements. All four are kept:
- the untrained network's key comes from `init_key` (`train.py:1207`);
- the rules live in a separate file;
- `stage_end:<k>` is the last checkpoint whose saved stage is *k*;
- the fingerprint is strict.

The blocking finding was that this plan and `experiment-designer`'s rules file described different tooling. **The designer's shape is the one kept.**

| # | Finding | Disposition | Where |
|---|---|---|---|
| R1 🔴 | Plan ↔ rules contract mismatch (key name, pilot handling, hash scope, machine-readable vs prose rules) | **Adopted the designer's contract.** Every manifest, the pilot and the new wake-up manifest included, carries `decision_rules: {file, sha256}`, a whole-file hash checked at load (mismatch raises). The pilot's no-verdict status is the registered rule `evidence_status.pilot.verdict_words_allowed: false`. `decision_rules_ref` and the `reads`/`outcomes` block are **dropped**. Rules stay prose. The evaluator implements each rule's logic in code with fixture tests, reads **every** numeric constant from the rules file's `parameters:` block, and is checked by a test that finds no numeric literal but 0 and 1 in it. `experiment-designer` signs off the fixture table before any real number is computed (new Checkpoint R.2) | §E, File Changes §6, §8, §9, §10, Stage R, Checkpoints R.1, R.2 |
| R2 🔴 | Untrained references: rules pin the wrong key recipe; plan built two arbitrary keys | **Plan side fixed.** The reference set is `untrained.build` on **every ordinary run's own seed** (three for the May replication, so three pairs). `untrained_reference_keys` is dropped. The pilot has one ordinary run, so it has no untrained pair and no informative gate; it has no verdict either. The rules' recipe text is the designer's to correct | §A1/A3/A4 statistics, File Changes §8 |
| R3 🔴 | Wake-up parameters unregistered; §B2 contradicted itself | **Plan side fixed.** Every wake-up value, the headline mode included, is read from `parameters.B2` of the sha-pinned rules file; the B2 runs from `experiment-designer`'s new `algorithmic_null_wakeup.yaml`, which pins the rules file (any B2 value it also states must match). Stage 4 waits for both to be committed. The plan no longer names a headline. §B2 now follows the rules' `B2` section, including its lag and across-worlds reading, and the plan samples the sparse measures densely enough for the rules' noise window | §B2, File Changes §8, §11, Stage R, Checkpoint R.1 |
| R4 🟡 | A4 within-stage drift has no checkpoints and no computation | **Fixed.** New selectors `stage_end:<k>:prev` and `final:prev` (the checkpoint just before, which must have the same saved stage). `d_a` and the movement gate are computed as the rules state | §A4, File Changes §5, §6, Checkpoint 5.1 |
| R5 🟡 | Survival difference (A3 pattern c) and gate G5 inputs not produced | **Fixed.** `wandb_history.stage_level` reads survival and food bites per run and stage from the local WandB binary (folder resolved by tag). `run_similarity` computes the 3-seed survival difference with the May design's floored standard error, and G5 per run. Both go into the driver JSON. The windowed means are cross-checked against the May replication's own readout (`pilot_readout.py`) | §A3, File Changes §7, §8, Checkpoint 4.6 |
| R6 🟡 | A2 clock baseline and excess differ from the rules | **Fixed to the rules.** The clock is the per-time-step mean of the training fold. The excess is `R² − R²_clock`, with the bootstrap 5th percentile of the excess. The one-hot ridge on `t` bins, `t_bin_width`, and the `R²(layer ⊕ t) − R²(t)` form are removed | §A2, File Changes §6 |
| R7 🟡 | Bootstrap: 200 over episodes vs the rules' procedure | **Adopted the rules' procedure.** `bootstrap_n` comes from the manifest and must meet the rules' minimum. The unit is the `episode_seed` group. Ridge maps are fixed per split repeat, and draws are joint across all agents and pairs | §A1/A3/A4 statistics, File Changes §6 |
| R8 🟡 | Shared `seed_base` collapses the pooled probe to `n_per_store` groups | **Fixed.** Stated, and the probe uses the manifest's `n_per_store`. `probe_set.build` asserts and prints the distinct group count, and fails below what gate G6 needs | §Probe sets, File Changes §4, Checkpoint 2.1 |
| R11–R13 (plan side) | Checkpoint 3.3 did not name the study | **Fixed.** 3.3 runs on the May configs for seeds 42, 43 and 44 | Checkpoint 3.3 |

R9, R10, R11 (rule text), R13 (the May design sentence) and the TODO wording are `experiment-designer`'s. The designer's in-progress rules revision (seen in the working tree on 2026-09-30, not yet committed) adds B2 logic beyond this plan's Revision 1: a noise window of `max(ceil(N/3), min_noise_points + 1)` points, a separate `literal_f`, lag, and a sign-test reading across worlds. §B2 follows it, and File Changes §11 plans the sampling it requires. This plan writes nothing under `docs/experiments/`.

**Points in the designer's contract this plan cannot implement as written.** Each is listed so that the designer can settle it in the rules revision, before any number exists. Until then, the evaluator raises on the case rather than choosing.
1. **G3 has no near-tie allowance.** G1 allows near-ties (margin < 1e-4 on ≤ 0.1% of rows); G3 requires 100% with no allowance, on the same kind of rows. As written, one near-tie among the sampled rows blocks every verdict. The plan applies G1's allowance to G3 only if the rules say so.
2. **Clock baseline at an unseen time step.** The per-time-step mean is undefined for a held-out row whose `t` has no row in the training fold (likely only in the long tail of `steps_remaining` on death-only episodes). The plan excludes such rows from the layer score and the clock score alike, and counts them in the data statement. The rules should say whether that is the registered handling.
3. **Bootstrap count per repeat or in total.** "`bootstrap_n ≥ 1000`" with "pooling the draws of the 5 repeats" can mean 1,000 per repeat (5,000 pooled) or 1,000 pooled. The plan draws `bootstrap_n` **per repeat** (it meets G6 under either reading); the rules should say which.
4. **Structural counts as parameters.** The rules contain counts inside their logic (`floor(n/3)`, "≥ 2 of 3 seeds", "≥ 2 of 5 layers", "≥ 3 of 5 layers", the split repeats and fraction, the stage analysed per evidence status). The designer's in-progress `parameters:` block covers most of them. Any left in prose only is found by the no-literal test (File Changes §6); the developer then stops and asks the designer.
5. **Survival row weighting: settled by the rules.** *[Rewritten in Revision 3, T2. The earlier text said the rules chose `Episode/_window_n`; that described `933f1978`, and the rules have since changed.]* The committed rules (`39b269a1`) register `parameters.common.survival.row_weight: delta_episode_number`: each WandB episode row is weighted by the episodes it adds (the increase in `Episode/Number` since the previous row), and rows whose `Episode/_window_n` is below `parameters.common.survival.min_window_n` are skipped. That is exactly what `pilot_readout.Series` does (`pilot_readout.py:296-308`) when it computes the May replication's own verdict, so the `S_k` on this page equals the May analysis's `S_k`. The value is read from `parameters:` like any other entry: `run_similarity` and `run_wakeup` pass it to `stage_level` / `interval_means` as `weighting`. The accepted value names are `delta_episode_number` (the registered weighting) and `window_n` (weight by `Episode/_window_n`, a printed diagnostic only, never the registered choice); any other value raises. Checkpoint 4.6 checks the registered weighting against `pilot_readout` to 1e-9 relative, a direct equality, and prints the `window_n` value beside it. (The May design's §5 prose still says rows are weighted by `_window_n`; the code and the rules weight by the increase in `Episode/Number`. That note is `experiment-designer`'s.)

---

## Revision 3 — response to plan-reviewer's third review (2026-09-30)

The third review ([[plan_algorithmic_null_tooling]] §Third review) found that the plan and the rules file now describe the same tooling. It blocked Stage 4 only. **Stages 0, 1, 2 and 5 are unchanged in substance.** `developer` is implementing them now against Revision 2. The one fix that could reach code already written for Stage 2 is marked **Addendum (in-flight Stage 2)** in File Changes §8; it applies only if that code validates `evidence_status`.

| # | Finding | Disposition | Where |
|---|---|---|---|
| T1 🔴 | Per-term gradient share and freeze cost sampled at every 5th checkpoint early on round `t_wake` up to the next multiple of 5, a systematic false "late" against a one-checkpoint coincidence band | **Fixed.** Every B2 measure is sampled at **every** checkpoint, plus step 0 where anchorable, on level-05 as already planned for May. No measure has its own point set: `run_wakeup` asserts every curve's x grid is the manifest's checkpoint list, and the manifest key for a sparse point set is **dropped**. Budget updated: freeze ≈ 2,600 rollouts, probe ≈ 860. The timing gate and the second-node rule are unchanged, and no measure is thinned. The reviewer's ❓ is scheduled as the first step of Stage 4: the survival (plateau) half of B2, CPU only, on all 19 runs, before any rollout (new Checkpoint 4.0) | §D table, §B2, §Stage 4 budget, Staging (Stage 4), File Changes §8, §11, Checkpoint 4.0 |
| T2 🟡 | Plan still said the rules weight survival by `_window_n` | **Fixed.** Aligned to the registered `row_weight: delta_episode_number`, which equals `pilot_readout.Series`; 4.6 is now a direct equality check | §Revision 2 point 5, §A3 survival, §B2 "Points", File Changes §7, Checkpoint 4.6 |
| T3 🟡 | `evidence_status` enum rejects `b2_wakeup`; `require_clean` would skip it | **Fixed.** The enum is the set of keys of the rules' `evidence_status` mapping. `require_clean` applies whenever that status's `verdict_words_allowed` is true. Figures print `label` wherever the status has one | §E point 6, File Changes §6, §8 (with the Stage 2 addendum), §9 |
| T4 🟡 | `noise_window_divisor` unread and typed as `/3`; `wakeup.py` outside the no-literal test; `remedy.*` unread; A4 lists and `gates.G5.stage` in prose | **Fixed.** `noise_window_divisor` is a required `t_cross` keyword read from `parameters.B2`. The no-literal test covers `wakeup.py`. `remedy.*` is **reported**, not exempt: `study_reading_A1` prints whether the remedy is triggered and which seeds it names, and acts on neither. A4's sequence, probes and drift pairs and G5's stage are read from `parameters:`, with the 1-based to `stage/index` translation stated | §A3 statistics, §A4, §B2, File Changes §6, §11 |
| T6 🟢 | Stale "about 25 points; window 9" | **Deleted** with T1 | §B2 |
| T7 🟢 | Stage 4b's check column did not name Checkpoint 3.3 | **Fixed** | Staging (Stage 4b) |

Not mine and not changed here: **T5** (the "guard passes but no point is sustained" outcome) is a rules revision by `experiment-designer`, then a fixture row the developer adds to §11's table with the reason text the rules register. **T8** (the driver also asserts that the checkpoint after the last listed May stage-0 checkpoint has a different saved stage) is the developer's, in `run_wakeup`.

---

## Revision 4 — decisions raised by the Stage 0–2/5 Implementation Report (2026-09-30)

**What this settles.** The developer's report (end of this doc, §Deviations) raised five points that have to be fixed before the May replication's episodes are recorded. That collection can start around 08:30 on 2026-09-30, when training ends.
1. **Arithmetic mode.** A recorded episode replays exactly only in the arithmetic mode it was recorded in. RTX 3090-class cards multiply by default in a reduced-precision format (TF32); older cards do not. No store says which one it used. From now on, every store is recorded in full 32-bit arithmetic, checks this at start-up, and names its mode and card in its manifest.
2. **Storage.** Saving every layer of every agent at every checkpoint would take about 200 GB. Saving only what the pre-registered rules read takes about 43 GB.
3. **Rules loader.** The small rules-loading file the developer added becomes part of the plan, and it is the only loader.
4. **A check near its tolerance.** The layer-consistency check itself does not accumulate error along an episode. One side comparison did; it is re-specified. The registered tolerance does not change.
5. **A wrong sentence** about the last row of an episode is removed.
6. **Untrained networks.** The code that rebuilds each run's starting network copies the trainer's random-key recipe instead of sharing it, so a future change to the trainer would silently rebuild old runs wrong. Both now call one shared function, and every run the analysis uses is checked.
7. Four small review items.

**Order.** Only R4-1 (collector side) and the R4-7 collector item gate the collection. The rest gate the first May *analysis* run, not the collection.

| # | Point | Decision | Where |
|---|---|---|---|
| R4-1 | Store precision (decided by the parent session) | Collect in full float32 with TF32 off, verified by a start-up self-test. Record the mode and GPU model in the manifest, and guard both on resume. The replay reads the recorded mode; every kept activation is float32 | below; File Changes §4, §5, §8; Checkpoints R4.1, R4.2, 6.1 |
| R4-2 | Activation storage | Verdict layers at every capture. Descriptive layers only at one headline capture. A `:prev` checkpoint only on its drift-pair probe | below; File Changes §8; Checkpoint R4.3 |
| R4-3 | `rules_pin.py` not in File Changes | Listed (§14). One loader: `decision_rules.py` imports it | File Changes §6, §13, §14; Checkpoint R4.5 |
| R4-4 | G2 margin | The chain check recomputes one step from the captured previous state, so it is already length-independent; unchanged. The sampled-vs-full comparison is the length-dependent one and not a G2 quantity; it becomes a per-row tool check with a planted control | File Changes §4; Checkpoint R4.4 |
| R4-5 | "`action_next` at `t = T−1` is masked" | Removed: row T exists, so nothing is masked | §Probe sets |
| R4-6 | `untrained.build` re-derives `train.py`'s key chain (`code-reviewer` 🟡) | One shared helper used by the trainer and `untrained.build`, pinned by golden keys; the per-run check runs on every run the analysis uses, with its launch git sha | below; File Changes §15; Checkpoints R4.6, 4.4 |
| R4-7 | Small review items | Docstring, a `del` that becomes a raise, a dead constant, a Stage 3 note | below |

### R4-1 Store precision

**Collector** (`scripts/eval/traj_collect/collect_trajectories.py`):
- **New `float32_matmul_selftest(precision: str) -> float`.** Under `jax.default_matmul_precision(precision)`, it runs a jitted `jnp.dot` of two fixed float32 matrices on JAX's default device and returns `max|C − C₆₄| / max|C₆₄|` against the numpy float64 product. The matrices are 256×512 and 512×256, uniform in [−1, 1], from `np.random.default_rng(0)`.
- **New module constant `FLOAT32_MATMUL_MAX_REL_ERR = 1e-5`.** Its comment states the basis. Float32 accumulation over 512 terms gives about 1e-7 relative error. TF32 (10-bit mantissa inputs) gives about 1e-4 to 1e-3. The constant sits at least 10× from each. It is a tool guard, not a study parameter. The measured values in both modes are recorded at Checkpoint R4.1.
- **The mode is forced for the whole run.** `main()` runs its whole body inside `with jax.default_matmul_precision("highest"):`. It uses a context, not a global `jax.config.update`, so an in-process test caller does not inherit it.
  - The first statement inside the context is `rel = float32_matmul_selftest("highest")`. It raises `RuntimeError`, naming the device, when `rel > FLOAT32_MATMUL_MAX_REL_ERR`. This happens before any store directory exists.
  - There is **no CLI flag**. The mode is not a choice, and a flag would be a second route to TF32.
- **Three new manifest fields.** `build_manifest` gains three required keyword arguments and writes:
  - `matmul_precision`: the value read back from JAX's config inside the context, not a typed literal. It must equal `"highest"`.
  - `compute_device_kind`: `jax.devices()[0].device_kind`, for example `"NVIDIA GeForce RTX 3090"` or `"cpu"`.
  - `matmul_selftest_max_rel_err`: `rel`.
- **Resume guard** (`src/utils/trajectory_store.py`): add `matmul_precision` and `compute_device_kind` to `MANIFEST_GUARDED_FIELDS`, with a comment citing this revision. Consequences:
  - A store can never mix modes or card models across resumed workers.
  - Resuming a store written before this change raises through `_req`, because its manifest lacks the keys, and nothing is written. This is correct: mixing an unrecorded mode with float32 is exactly the hazard. No completed store needs resuming.
  - The May spec (§12: 10,000 episodes, `shard_episodes: 5000`, `blocks_per_cell: 2`) puts each store in one worklist cell, so one worker on one card writes it. A future multi-cell GPU collection across card models would be refused, loudly.
- **No `SCHEMA_VERSION` bump.** The schema doc's "fixed key list" (§3) is the columns. Manifest fields have been added without a bump before (`training_git_sha` and siblings, commit `0edb2bd6`). The manifest-field table and the "Manifest guard" list in `docs/environment/TRAJECTORY_STORE_SCHEMA.md` are updated in the same commit.
- **Unchanged:** `collect_worker.sh` and `run_collection.py`. The per-node compile cache is safe, because the matmul precision is part of the lowered program. The self-test would catch a stale TF32 program anyway.

**Collector tests** (`tests/test_trajectory_collection.py`):
- A collection on the existing CPU fixture writes the three fields, with `matmul_precision == "highest"` and `compute_device_kind == jax.devices()[0].device_kind`.
- A resume raises and writes nothing in three cases: the store manifest's `matmul_precision` edited to `"default"`; `compute_device_kind` edited; a manifest lacking both keys.
- **The self-test can fail** (CPU-runnable): monkeypatch the product to add 1e-4 relative noise, and `main` raises before any store directory is created.
- `test_schema_doc_matches_code` still passes.

**Reader** (`probe_set.py`, `run_activations.py`, `teacher_forced.py`):
- `probe_set` copies each store's `matmul_precision` and `compute_device_kind` into `store_meta`. A missing field becomes `None`. That absence is how a store from before Revision 4 is recognised; it is never filled with a default.
- **`probes[].store_matmul_precision` stays mandatory, one entry per store, in the order of `stores`.** Accepted entries:
  - `recorded`: use the store manifest's `matmul_precision`. Raises if the store records none.
  - `highest` or `default`: accepted **only** for a store whose manifest records no mode (a legacy store). On a store that records a mode, an explicit value must equal the recorded one, or it raises.

  So the pilot's `[highest, default]` keeps working unchanged, and the May manifests write `recorded` for every store.
- **`capture_matmul_precision` stays mandatory**, but its only accepted value is now `highest` (it was `highest | default`); the pilot already uses it. So every kept activation, every chain assertion and the cross-agent agreement are computed in float32.
- `run_activations` calls `float32_matmul_selftest("highest")` once at start. It imports the function from the collector module, which it already imports for `resolve_checkpoint_info`. It writes the value and the replay device kind into its `manifest.json`, and raises above the constant.
- Each activation JSON records, per store, the resolved check mode, the store's `compute_device_kind` and the replay device kind. For every May store the check mode equals the capture mode, so the existing code skips its second pass (`teacher_forced.py:272`), and self-replay and capture are one pass.
- **Why a float32 store replays on any card.** Two cards computing in float32 differ only in reduction order: about 1e-7 relative on the logits. That can flip only rows whose top-two margin is below G1's near-tie margin (1e-4), and G1 already allows those. A replay device that silently ran TF32 fails G1 loudly, as the pilot showed.
- **Reader tests** (`tests/analysis/test_nmn_probe_set.py`, or a new `tests/analysis/test_nmn_run_activations_manifest.py`): the resolution cases above (`recorded` on a recording store; `recorded` on a legacy store raises; a matching explicit value; a conflicting explicit value raises; an explicit value on a legacy store), plus `capture_matmul_precision: default` raises.

### R4-2 Activation storage

**Which statistics need row-level activations kept on disk.** Every rules statistic that compares or decodes layers needs them: A1 (CKA and predictivity), A2 (decoding and the clock baseline), A3 (built from A1's pair statistics), A4 (movement and drift) and G4. G4's input-layer control reads the probe file. There are three reasons:
1. The bootstrap resamples `episode_seed` groups jointly across all agents and pairs, so each draw needs every agent's rows of the drawn groups.
2. Predictivity and decoding maps are fitted once per split repeat, then scored on every resample. That is two passes over the same rows.
3. CKA's centring depends on which rows are drawn.

Streaming would need sufficient statistics per group. A 128×128 cross-product per group and pair holds 16,384 numbers. The raw activations it would replace hold 640 per group and agent (5 rows × 128 units), so streaming would be 25× larger. Keeping rows is therefore the smallest form. G1–G3 are computed during replay and need nothing kept. B2 uses rollouts, not stored activations.

**What is kept.** This is the smallest design the rules allow. `n_per_store` (5,000) and the five verdict layers are unchanged, and `rows_per_episode` stays 5, the value the pilot was built and checked with.
1. **At every capture:** the verdict layers `enc.out`, `rnn.state`, `rnn.out`, `actor.out` and `critic.out` (5 × 128 units), plus logits and value. About 2.6 KB per row.
2. **Only at the headline capture:** the descriptive layers, meaning the `.raw` / `.mod` keys and `enc.uni.*`. The rules list them as descriptive, used to find where a difference arises at the A1 headline.
   - The capture is set by the manifest's `headline_capture`. Evidence manifest: `{checkpoint: final, probe: active}`. Interim: `null` (verdict layers only). Pilot: `{checkpoint: final, probe: w0000_pair_final}`, so its output does not change.
   - Untrained networks keep verdict layers only, because the rules pair UNTRAINED on `X.out` and `rnn.state`.
   - The raw-input reference comes from the probe file, not from each agent's capture.
3. **A `:prev` checkpoint is replayed only on its drift pair's probe:** `final:prev` on active and `stage_end:3:prev` on passive, read from `parameters.A4.drift_pairs`. Every other selector is replayed on every probe.

**Size.** Upper bound: 150,000 kept rows per probe (30,000 episodes × 5; the pilot kept 4.86 per episode), so one verdict capture is about 0.39 GB.

| Part | Count | Size |
|---|---|---|
| Evidence manifest, verdict layers | 6 agents × (5 stage ends × 2 probes + 2 `:prev`) = 72, plus 3 untrained × 2 probes = 6, so 78 captures | ≈ 30 GB |
| Evidence manifest, descriptive layers at the headline | 3 modulated × 2.6 GB + 3 ordinary × 1.7 GB | ≈ 13 GB |
| **Evidence manifest, total** | | **≈ 43 GB** (≈ 200 GB if everything were kept) |
| Interim manifest | 9 verdict captures | ≈ 3.5 GB |

Probe files stay as now, about 2 GB per May probe.

Float16 storage is rejected. It adds about 5e-4 relative error to the statistics' inputs, 50× the float32 tolerance of G2.

**Manifest keys** (developer-owned, mandatory, §8):
- `layers[].keep: every_capture | headline_only`. Every verdict layer, `logits` and `value` must be `every_capture`, or the load raises.
- `headline_capture: {checkpoint, probe} | null`.

`run_activations` prints the expected bytes for the whole manifest before the first replay, and the measured total after the last. Both go in the Implementation Report.

### R4-4 G2 margin

The report gives two numbers, and they measure different things. The report's stated cause (error accumulating over up to 500 recurrent steps) is **wrong for the first** and right only for the second; `code-reviewer` reached the same reading independently (Stages 0–2/5 review, 2026-09-30).

**Chain assertions (largest 4.93e-6, `rnn.state`): already length-independent. No change.**
- Each tensor is recomputed from its *captured* upstream neighbour at the same step. `rnn.state[t]` is recomputed from the captured `rnn.state[t−1]` (`teacher_forced._chain`, l.147–152: `h_prev = concat(h_init, acts["rnn.state"][:-1])`).
- So no rounding difference passes from one step to the next. Each row's deviation is a one-step difference between two compilations of the same arithmetic (kernel choice and fusion), bounded by a few float32 ULPs of that step's operands whatever `t` is. Longer episodes add rows, not accumulation. The May network has the same widths (128) and runs in the same mode, so the one-step bound is the same.
- The check's form stays exactly as implemented (block normaliser, G2's formula). The only addition is a diagnostic: the capture JSON reports the maximum deviation in each quarter of the checked length, so the absence of growth with `t` is shown on data rather than argued.
- **Rules hand-off: not needed, in this plan's reading.** `code-reviewer` suggested that `experiment-designer` register a relative tolerance for recurrent tensors. Since the only G2 quantity is per-step, this plan does not ask for it. If `experiment-designer` decides otherwise, the change must be committed before the first May capture (the rules' `revision_policy`). This plan writes nothing in the rules file.

**Sampled-vs-full comparison (largest 8.3e-6): length-dependent, and not a G2 quantity.**
- It compares the kept rows of the 2,500-episode replay with a separate full replay of 8 episodes. These are two independent recurrences from `h0`, so a rounding difference at step 1 is carried through the memory to step 500.
- The rules' G2 lists only the neighbour reconstructions (logits, value, `rnn.state`, `X.mod`). The code held this extra check to G2's number (`teacher_forced.py:435`).
- The comparison exists to catch a buffer written into the wrong (step, episode) slot. Such an error moves a value by the change between steps, orders of magnitude above rounding.
- **Change: a separate tool check, `tool_checks.buffer_index_rel_tol: 1.0e-3`, computed per row.** It is a developer-owned manifest key, like `shift_change_rows_max`, and decides no verdict. Per row means `max_j |Δ_ij| / max(1, max_j |ref_ij|)` for each kept row `i`, then the maximum over rows, so neither the normaliser nor the error is pooled across a probe of any length. The capture JSON reports it per quarter of the episode length as well.
  - **Planted positive control on the pilot:** shift the kept rows' slots by one step. The check must fail, with a deviation at least 10× the tool tolerance, and the value is recorded.
  - Basis for 1e-3: at least 100× above the observed rounding, and, as the control must confirm, at least 10× below a one-step slot error.
- This is a third, redundant guard on slot indexing, so moving it off G2's number removes no protection. The exact guards are the buffer-vs-index argmax check (1.0) and the step-discontinuous alignment (100 % on action-change rows). A key bound to the wrong tensor is caught by the chain assertions, which stay at 1e-5.

**For `plan-reviewer`:** this moves a check that the code, not the rules, held to G2's number, so the move should be reviewed.

### R4-3 `rules_pin.py`: one loader

- `scripts/analysis/nmn/rules_pin.py` joins File Changes as §14, as built in Stage 2 (commit `e38a2b2f`).
- `decision_rules.py` (Stage 3) imports `load`, `param` and `evidence_policy` from it and defines no loader of its own. Where §6 says `decision_rules.load`, read `rules_pin.load`. Where it says `verdict_policy(rules, evidence_status)`, read `rules_pin.evidence_policy(pinned, status)`, which returns the same `verdict_words_allowed` / `prefix` / `label` mapping.
- §6's `require_clean` moves into `rules_pin` as `require_clean(pinned)`. It raises when `pinned.dirty`. This is fail-closed: `load` already sets `dirty=True` when git cannot be read.
- **Tests:** `decision_rules.load is rules_pin.load`, and `decision_rules.py` imports neither `hashlib` nor `yaml`. The contract tests of §6 (sha mismatch, status not in the rules, dirty file) target `rules_pin`.
- The no-literal test does not cover `rules_pin.py`: it evaluates no rule, and its one literal is a subprocess timeout. The coverage test counts reads made through `rules_pin.param`.
- `SCRIPTS_DEPENDENCY_MAP.md` already has its row (added with Stage 2). When Stage 3 lands, its caller column gains `decision_rules.py`.

### R4-6 One key recipe for the untrained networks

**The problem (`code-reviewer`, 🟡).** `untrained.build` (`scripts/analysis/nmn/untrained.py:106–109`) copies `train.py`'s key chain (`train.py:1152–1153`, then `:1207`) instead of calling it. Its bitwise test (`tests/analysis/test_nmn_untrained.py`) proves the two agree at HEAD only. If `train.py`'s chain ever changes, runs launched before the change would be rebuilt with the new chain, and the test would still pass.

**Change.**
- **New `src/utils/init_keys.py` with one function, `trainer_init_keys(seed) -> (key, env_key, init_key)`.** It is exactly today's chain:
  ```python
  key = jax.random.PRNGKey(seed)
  key, _model_key, env_key = jax.random.split(key, 3)   # _model_key: never used (Revision 1)
  key, init_key = jax.random.split(key)
  return key, env_key, init_key
  ```
  It lives in `src/` rather than `train.py`, because importing `train.py` runs its argv pre-parser and sets environment variables at import time.
- **`train.py`.**
  - l.1152–1153 become `key, env_key, init_key = trainer_init_keys(seed)`.
  - The four algorithm branches drop their own `key, init_key = jax.random.split(key)` (l.1207 RecurrentPPO, l.1290 DQN, l.1312 DRQN, l.1342 PPO).
  - This is value-preserving. Nothing reads `key` between l.1153 and those splits (checked with grep), and every branch makes the same split, so all three keys are bit-identical to today's for every algorithm.
  - The docstring states that changing the function changes the starting network of every run launched after, and breaks the rebuild of every run launched before.
- **`untrained.build`** replaces its two split lines with `_, _, init_key = trainer_init_keys(seed)`.
- **Tests** (`tests/utils/test_init_keys.py`, new):
  - **golden keys:** the raw `uint32` data of `key`, `env_key` and `init_key` for seeds 42, 43 and 44, recorded on the commit **before** the edit (state its sha in the test);
  - `untrained.py` contains no `jax.random.split` (source check), so the recipe cannot be copied back in.

  The existing integration test `test_nmn_untrained.py` (bitwise against `train.main()`'s own construction) must still pass.
- **Training program unchanged.** Keys are inputs to the traced programs, not part of them. Still, run Checkpoint 1.3's jaxpr-hash method (`tmp/20260930_stage1_hashes.py`) on the 4 real agent blocks before and after; all 8 hashes must be identical. No speed run is needed if they are.
- **`KNOWN_BUGS.md` l.114 (stale nested seed) is unaffected:** the helper takes the seed the trainer already resolved.

**Checkpoint 4.4, second half, on every run.** The check is that the own-seed rebuild is closer to the run's first saved checkpoint than the rebuilds for two other seeds. It now runs on **every** run on which `untrained.build` is called, not a sample:
- the 6 May runs (UNTRAINED references for the 3 ordinary runs, and the B2 step-0 anchor for the 3 modulated runs);
- the 16 level-05 modulated runs (B2 anchors).

That is 22 runs. Each row records the run's launch git sha from `wandb-metadata.json` (`git.commit`, folder found through `wandb_history.resolve_by_tag`) beside `training_git_sha` from `models/provenance.json`; the two must agree. A run launched before the commit that introduces `trainer_init_keys` is still covered, because the helper reproduces today's chain bit for bit (golden test). A run that fails the closeness check stops the analysis that uses its untrained network; the list goes to the user and `experiment-designer`. The plan does not decide an exclusion.

### R4-7 Small review items

1. **`forward_with_activations` docstring** (`src/models/recurrent_ppo_network.py`): add that equality with `__call__` is bitwise on CPU. On GPU it holds to ≤ 1e-6 relative with identical argmax, because XLA may fuse the two programs differently. The test's tolerance clause already allows for this. Docstring only; the jaxpr is unchanged.
2. **`continual_resolved_config`** (`collect_trajectories.py:297–298`): a world section present in `config.yaml` but absent from the stage file is now a `ValueError` naming the section and the stage file. Today the section is silently deleted, which would record a different world than the one trained. Add a test (a stage file without `thermal` raises).
   - **Safe for the collection:** on 2026-09-30 at 02:30, all five world sections are present in `config.yaml` and all five stage files of all six May runs (checked by script).
   - This touches the collector, so it lands with R4-1, before the collection.
3. **Remove the unused `SITE_OF`** (`teacher_forced.py:35`).
4. **Stage 3 note.** Under the capture mode (float32), the pilot's modulated agent agrees with its own TF32-recorded store on 0.9981 of rows. Any pilot statistic keyed to the *stored* action therefore inherits that 0.2 % mismatch; the pilot figures state it in their data statement. It does not arise for May stores, which are recorded in float32 (R4-1).

---

## Analysis

### A. Where the network computes what the page asks about

`src/models/recurrent_ppo_network.py` (read at HEAD, 625 lines):

| Page layer name | Where it is formed | Ordinary agent | Modulated agent |
|---|---|---|---|
| encoder, per sense (9 senses × 128) | `ObservationEncoder.__call__` l.193–196 / `forward_with_modulation` l.232–246 | after LayerNorm → ReLU | after LayerNorm → **FiLM** → ReLU |
| encoder output (128) | l.200–203 / l.250–264 | `x_proj` | after LayerNorm → **FiLM** → ReLU |
| memory state (128) | `rnn_cell` l.538–542 / l.580–583 | `h_new` | `h_new` (the carry is never modulated, D5) |
| memory output (128) | l.542–548 | `x_h` (== `h_new` for `nnx.GRUCell`) | `x_h` then **FiLM** `z_rnn·x_h + z_rnn_add` (l.548) |
| actor hidden (128) | l.551–554 / l.585 | `actor_fc1` → ReLU | `actor_fc1` → **FiLM** → ReLU |
| critic hidden (128) | l.562–565 / l.588 | `critic_fc1` → ReLU | `critic_fc1` → **FiLM** → ReLU |

The network applies **symlog to its own input** (l.503: `x = sign(x)·log(|x|+1)`). The environment stays agent-agnostic. So a replay must feed the *raw* observation, not a symlogged one. When the temperature site is on, `logits = actor_fc2(a_h) / temperature` (l.556–557). It is off in both studies here, but the chain assertions (File Changes §4) handle both cases.

### B. The stored observation is exactly the network input

The trajectory collector's scan (`scripts/eval/traj_collect/traj_scan.py` l.158–201) **carries** the observation. `obs_noised` in row *t* is the same array passed to `policy_step(model, obs, h)`, which calls `model(obs, h)`, and the model applies symlog internally. The row convention (`src/utils/trajectory_store.py` header): row *t* holds the state at *t*, plus the action that *arrived* at *t*. So `action[t+1] = argmax(logits(obs_noised[t]))`. Row 0 has `action = -1`. The memory starts at `initial_state` (zeros) for every episode. Both studies store `obs_precision: float32` (verified in the level-05 manifest), so the stored input is lossless. Both studies also train with `perceptual_noise.enabled: false`, which makes `obs_noised == obs_true`. The tools still read `obs_noised`, because that column is the policy's input by definition.

**The correctness check follows directly.** Take the agent/checkpoint that generated a store (its manifest `checkpoint_path`). Replay it on that store: its argmax action at row *t* must equal the stored `action` at row *t+1*. Under teacher forcing a disagreement cannot compound, because the memory depends only on the stored inputs, never on the replayed action. So the agreement rate is a clean per-step statistic. **Logits and values are not stored**, so this argmax agreement is the only link from the captured tensors to a stored ground truth. No stronger stored-output check exists. Everything upstream of the logits is therefore pinned by chaining each captured tensor to its neighbour (File Changes §4).

### C. Data inventory — what exists now vs later

| Source | Stores on disk | Loads at HEAD? | Use |
|---|---|---|---|
| **Level-05 body-interactions factorial**: 16 worlds × {ordinary, modulated}, seed 42 | **All 32 complete** under `results/trajectories_l05body/<run>/<final ckpt>/<env_fp>/`: 200 shards each, 1,000,000 episodes, `seed_base 1000000` (same reset draws for both agents), float32, observation width 58, ~47 GB per store | **Yes.** `scripts/analysis/nmn/replay.load_agent` restored the w0000 pair strictly on 2026-09-29, and compat supplied nothing. The other 30 are re-checked in Stage 0 | Pilot (tool validation) for A1/A2. **B2 now**, on all 16 modulated runs (50 checkpoints each, episodes 200,019 … 10,000,021) |
| **May replication** (continual worlds, 5 stages alternating an *active* world, where the predator hunts, and a *passive* world, where it never hunts: `detection_range 0`, `hunt_stamina_threshold 1.1`, confined to the top-left) | **None.** Checkpoints every 100 k episodes | **Yes.** Both agent types restored strictly at HEAD on 2026-09-29. Observation width 52 in every stage (the stage configs differ only in `environment.entities`) | A1–A4 in full, after training. **The first stage, `01_active` (episodes 0–1.5 M), has already finished for all six runs**, so B2 on it and an early A3 at its end can run now (§Staging) |
| Wave 1/2 basic levels, bq2cover | stores exist (`results/trajectories_basicq2_*`) | per the TODO, yes; not re-verified here | not needed by this plan |
| **Site × input grid** (MC and GAE_NORM, both olfaction twins) | stores exist | **No.** Registry row at `KNOWN_BUGS.md` line 123: the saved configs lack keys that later became mandatory. Stage 1 of [[SAVED_RUN_CONFIG_COMPAT]] is unimplemented | **Excluded** |

**Stage names.** The May replication's saved stage files are `stage_00_01_active.yaml`, `stage_01_02_passive.yaml`, `stage_02_03_active.yaml`, `stage_03_04_passive.yaml`, `stage_04_05_active.yaml`. This plan names stages by their saved names (`01_active` … `05_active`). The selector `stage_end:<k>` uses the **0-based** index that the checkpoint's `stage` field stores: `stage_end:0` is the end of `01_active`, and `stage_end:3` is the end of `04_passive`.

**The six May-replication runs** (resolved by tag, never by timestamp glob; listed in the May manifest):

| Tag (`--tag`) | Run dir (`results/JAX_RecurrentPPO/`) | Training log | Local WandB folder |
|---|---|---|---|
| `rppo_cw_mayrep_t1none_s42` | `20260929-153635_…` | `logs/20260929_153606.log` | `wandb/run-20260929_153646-ftqkqmzb` |
| `rppo_cw_mayrep_t16quad_s42` | `20260929-153644_…` | `logs/20260929_153614.log` | `wandb/run-20260929_153655-n7htz71a` |
| `rppo_cw_mayrep_t1none_s43` | `20260929-153652_…` | `logs/20260929_153623.log` | `wandb/run-20260929_153704-8c5kmmj2` |
| `rppo_cw_mayrep_t16quad_s43` | `20260929-153702_…` | `logs/20260929_153632.log` | `wandb/run-20260929_153714-rfxw1g7x` |
| `rppo_cw_mayrep_t1none_s44` | `20260929-153712_…` | `logs/20260929_153641.log` | `wandb/run-20260929_153724-0ojcf4d8` |
| `rppo_cw_mayrep_t16quad_s44` | `20260929-153723_…` | `logs/20260929_153650.log` | `wandb/run-20260929_153734-5er602ge` |

The log↔tag and folder↔tag pairs were read from the log contents and from `wandb-metadata.json` `--tag` on 2026-09-29. `logs/20260929_153602.log` and `…153603.log` are 0 bytes and belong to no run. The WandB folders are **not** looked up from this table at run time. `wandb_history.resolve_by_tag` resolves them and must reproduce it, which is a check on the resolver (Checkpoint 4.2).

**Collection gap for the May replication (found during this investigation).** The collector always builds the world from a run's `models/config.yaml` (`collect_trajectories.py` l.699). For a continual run, that file is the stage-0 world. The later stage files carry no `agent:` block. The collector also cannot pick "the checkpoint at the end of stage *k*": `checkpoints:` is spec-wide (`run_collection.expand_cells` l.167), and each run's stage-end step number is different. Consequences:
- Stores at the final checkpoint are **correct by coincidence**. The last stage, `05_active`, has env sections identical to stage 0 (verified by a key-level diff of the five stage files; `stage_00_01_active.yaml` is identical to `config.yaml` in every key).
- A store for the passive world, which A4 needs, **cannot be collected correctly today**. The collector would put a `04_passive` checkpoint into the active world without any error.

`scripts/eval/eval_rollout.py::_resolve_continual_stage_config` (l.677) and `scripts/eval/continual_forgetting_matrix.py` (`read_saved_stage` l.86, `resolve_rows` l.102) already solve both problems for evaluation. This plan brings the same logic into the collector (File Changes §5).

**Launcher.** The finished-runs-only launcher `scripts/analysis/studies/level05_body_interactions/launch_collection.py` works for any spec. It detects finished runs from the log line `Training complete. Results saved to …` (`train.py` l.2763, printed by continual runs too). Its only log selector today is `--logs-glob`. This plan adds an explicit `--logs <path> …` alternative (File Changes §12), so the six May logs are named, not globbed. Moving the launcher is out of scope.

### D. B2 — what the trainer already logs

`src/models/recurrent_ppo_trainer.py::update_step` (l.406–442) computes `grad_norm = optax.global_norm(grads)` and `mod_grad_norm = global_norm(grads['modulator'])`. Both are taken on the **total** loss and **before** clipping. `train_iteration` runs `update_step` once per epoch on the **whole** batch (l.583–586; no minibatches), so one iteration has `K_epochs` (= 4 in both studies) updates.

In `train.py` l.1919–1923, `avg_grad_norm` and `avg_mod_grad_norm` are the **means over those `K_epochs` updates of one iteration**. The logged values differ:
- `modulator/grad_norm` is that iteration mean, emitted only at log iterations (l.1966). It is the most recent iteration, not windowed.
- `loss/grad_norm` is a rolling-window spread of the per-iteration means.

The loss split (`ppo_loss_fn` l.173–208) is computed but never differentiated per term. Later epochs of an iteration run at a probability ratio ≠ 1, where clipped samples contribute no policy gradient, and at parameters that have already moved inside the iteration. A first-update-only number is therefore biased upward relative to the log. The probe (File Changes §11) reports both.

| B2 measure | Retroactive for loadable runs? | How |
|---|---|---|
| Gradient share, **total loss** `‖∇θ_mod‖² / ‖∇θ_all‖²` | **Yes, approximately**, from local WandB | ratio of `modulator/grad_norm`² to `loss/grad_norm`² (window mean). Noisy per point; binned to checkpoint intervals |
| Gradient share **by loss term** (policy / value / entropy) | **Yes, at checkpoints**, through the new *gradient probe* | first update of one training-shaped iteration (ratio = 1, clipping inactive), per term. Reported beside the probe's own full-iteration mean, which is like-for-like with the log |
| Relative update size `‖Δθ_mod‖/‖θ_mod‖` vs main network | **Yes, at checkpoint resolution**, from saved weights, plus the untrained network as the first point | `ckpt_io.load_params` + untrained reconstruction, CPU only |
| Output activity: contextual fraction ρ and gain swing | **Yes**, per checkpoint and at the untrained network | ρ: `replay.rollout` → `mod_distribution.variance_split`. Swing: `spectral_bound` (weights only) |
| Freeze cost | **Yes**, at every checkpoint and at the untrained network (Revision 3, T1; was every 5th) | `freeze.apply_freeze` + `replay.rollout`, paired seeds (`freeze.paired_differences`) |
| Per-update gradient share by term; per-update update size | **Future runs only** | needs trainer logging. Deferred (§Deferred) |

**Checkpoints do not save the environment.** The training checkpoint payload is `model`, `optimizer`, `h_state`, `key`, `iteration`, `step`, `episode`, `stage` (`train.py` l.2608–2616). There is no `env_state`. So the probe's batch comes from a fresh world warmed up for `warmup_iters` iterations, not from the world the trainer was in. This is one reason the probe-vs-log comparison is a sanity band, not a correctness proof.

The existing drivers (`run_mod_distribution.py`, `run_freeze.py`, `run_spectral_bound.py`) find runs through `ckpt_io.discover_runs`. Its regex (`ckpt_io.py` l.61) matches only the grid and basic-level names, not `l05body` or `cw_mayrep`. The new drivers therefore take an explicit **analysis manifest** that lists run directories. The old drivers are left untouched.

### E. The similarity measure robust to per-unit rescaling (A1), and who decides "the same"

Linear CKA is unchanged by rotations and by a uniform rescaling, but **not by per-unit rescaling**. The modulator's time-averaged gain is exactly a large fixed per-unit rescaling (the percept gain starts near 3: `percept_bias_init: 3.0`). So on a post-gain layer, CKA would report "different" for a difference the network can absorb for free. The freeze method's own docstring shows that the time-averaged gain and offset are gauge quantities (`freeze.py` "Interpreting a null").

**Chosen:** *linear predictivity*. Fit a ridge regression from agent A's layer to agent B's layer on training episodes, and score R² on held-out episodes, in both directions.
- It is unchanged by **any** invertible linear map of either layer, including per-unit rescaling. A pure constant-gain difference scores ≈ 1. What is left is the part of the modulation that varies with the situation, which is the part that matters.
- It reuses the A2 probe code (ridge + episode-grouped split + held-out R²). One tested component serves both analyses.
- Its asymmetry is informative: "A's layer contains B's information, but not the reverse".

**Not chosen:** SVCCA. It is also linear-invariant, but it depends on how many singular directions are kept (a free parameter that changes the answer). CCA on 128-wide layers overfits unless the rows vastly outnumber the units. And it has no held-out evaluation, so it would need its own episode-split machinery.

Linear CKA stays as the headline measure because it is the page's stated method. The two are reported side by side on every layer.

**Who decides what "the same computation" means (reviewer finding 2; contract per re-review R1).** This plan sets **no** threshold and **no** verdict wording for A1–A4. Both live in `experiment-designer`'s pre-registered rules file, `docs/experiments/active/modulator_clues/algorithmic_null_decision_rules.yaml`. The rules are prose for logic. Every number they use lives in the file's `parameters:` block, which the designer adds.

**The contract (the designer's shape; this plan implements it):**
1. **Pin.** Every analysis manifest carries the mandatory key `decision_rules: {file, sha256}`, where `sha256` is the hash of the **whole file**. This includes the pilot and the wake-up manifest. At load, the tooling hashes the file and compares; a mismatch raises `ValueError`. There is no `null` form and no fallback.
2. **What each evidence status may say comes from the rules.** `evidence_status.<status>.verdict_words_allowed` decides whether any verdict word is written. For the pilot it is `false`: the drivers do not call the decision functions at all, and every data statement carries the rules' own pilot `label` ("tool validation — the two agents share seed 42; not evidence") plus "no verdict is drawn". For `interim`, every verdict word carries the rules' `verdict_prefix`.
3. **Logic in code, numbers from `parameters:`.** `decision_rules.py` implements each rule's logic as a function: gates G1–G6, then A1, A2, A3, A4, and the study-level readings. Each function's docstring quotes the rule text it implements, verbatim. Every numeric constant is read from `parameters:` by name. A test parses the module's syntax tree and fails on any numeric literal other than 0 and 1, so a threshold cannot be typed into code. A second test loads the real rules file and checks that every `parameters:` entry is read by some function, and every entry a function reads exists. The key names are the designer's.
4. **A case the prose does not cover raises.** If the inputs reach a combination that no rule assigns (for example "predictivity same, CKA uninformative" before the designer's R10 revision), the evaluator raises `ValueError` and names the case. It never picks an outcome.
5. **The reading is signed off before any number exists.** The fixture tests set out, per rule, input → expected outcome on made-up values marked "test fixture, not the study's rule". `experiment-designer` reads that table and signs it in this plan's Implementation Report (Checkpoint R.2) **before** the first real `run_similarity`, `run_decoding` or `run_wakeup` output. That sign-off is what registers the code's reading of the prose.
6. **Prove the order.** On any manifest whose status has `verdict_words_allowed: true` in the rules (today `interim`, `evidence` and `b2_wakeup`; Revision 3, T3), the driver refuses to run if the rules file has uncommitted changes (`require_clean`). Every output is stamped with the rules file path, its sha256 and its last commit sha. The page builder refuses a figure whose stamped sha256 differs from the file at HEAD.

Lists the rules fix, such as `common.verdict_layers`, are also read from the file. The drivers assert that every verdict layer appears in the manifest's `layers`.

### F. Predator identity (A2)

The store manifest carries `animal_classes` (for example `["predator","predator","neutral","neutral"]`) and `animal_is_damaging`. The per-episode table carries `animal_active` (which slots exist in this episode). A predator is `animal_classes[i] == "predator"` and `animal_active[i]`. Distance is **Manhattan**, the metric the environment uses for hunt detection (`src/environment/core.py` l.614: `dist = sum(|hunt_pos − agent_pos|)`). Rows in episodes with no active predator are excluded from that target and counted in the data statement. Level-05 draws 0–2 predators per episode.

### G. Known bugs consulted (`bug-curator`, 2026-09-29)

The numbers below are **line numbers in `KNOWN_BUGS.md`**, not row ids.
- **line 123** (saved configs stop loading): the reason the site × input grid is excluded.
- **line 107** (the modulated gate-bias cell has a different init): **does not apply** to the runs used here. Both t16quad configs use `rnn_mechanism: activation`, so both agents build `nnx.GRUCell`. The D11 construction order then gives the modulated agent **exactly** the ordinary agent's starting weights at the same seed. Stage 3 verifies this, because A3's reading depends on it.
- **line 114** (stale nested seed): read the top-level `seed:` key.
- **line 138** (noise defaults off when the key is missing): the replay never rebuilds noise. It feeds stored `obs_noised`.
- **line 159** (reset differs by at most 1 ULP across compilations, in `animal_property_sampled` only): irrelevant to teacher forcing. It is noted for the action-agreement tolerance.
- **lines 460/461** (partial restore keeps random weights): every load goes through the strict `load_agent` check.
- There is no row on replay, trajectory stores, `scripts/analysis/nmn/`, gradient-norm logging, or construction order beyond lines 107/389.

---

## Implementation Plan

### Design

```
 analysis manifest (YAML: runs, checkpoints, stores, probe sizes, evidence_status,
                    decision_rules: {file, sha256} → experiment-designer's rules file,
                    whose parameters: block holds every number the rules use)
        │
        ├─► probe_set.py ── ONE pass over the store parquet → one row-index array
        │                   → obs, next action, targets all indexed by that array
        │                   → probe_<id>.npz
        │
        ├─► teacher_forced.py ── load_agent(run, ckpt) → nnx.jit scan of
        │        model.forward_with_activations over probe obs (memory reset at t=0)
        │        → chain assertions on the real checkpoint (§4)
        │        → acts_<run>__<ckpt>__<probe>.npz  (+ agreement + assertion report)
        │
        ├─► representation.py (pure numpy/sklearn): linear CKA, linear predictivity,
        │        episode-grouped ridge probes
        │   decision_rules.py (pure python): load + sha256-check the rules file; gates G1–G6
        │        and A1–A4 logic in code, every constant from its parameters: block
        │        run_similarity.py (A1, A3, A4)   run_decoding.py (A2)
        │
        └─► wakeup.py (pure numpy) + untrained.py + grad_probe.py + wandb_history.py
                 run_wakeup.py (B2) — reuses replay.py, mod_distribution.py,
                 spectral_bound.py, freeze.py, ckpt_io.py
                              │
                              ▼
     figure scripts an01..an06 (house.apply / house.save / .data.txt)
       → docs/experiments/active/modulator_clues/figures/algorithmic_null/
                              ▼
     build_algorithmic_null_page.py (gains the §11 figure checks, scoped to that subfolder)
```

**Run-agnostic by construction.** Nothing names a study. Every run, checkpoint, store, probe size, layer list and threshold comes from a manifest, and every key is mandatory (`_req` → `ValueError`, the pattern of `load_manifest` in `scripts/analysis/studies/level05_body_interactions/_common.py`). Agent roles (arm, seed) are read from each run's own saved `models/config.yaml` (top-level `seed:`, per `KNOWN_BUGS.md` line 114; `agent.modulation.type`), not from directory names. A future run is analysed by writing a manifest.

**Intermediate capture — explicit method, not `nnx.sow`.** `nnx.sow` is the wrong tool in this codebase:
1. Sown values become `nnx.Intermediate` variables **in the module's state**. Three places compare `nnx.state(model)` against a checkpoint and hard-fail on any key the checkpoint lacks: `replay.load_agent` (l.137–149), the collector's `assert_restored_tree_matches`, and the training checkpoint writer. A sown variable left on a model would break restores, or leak into saved checkpoints.
2. The model is called inside `jax.lax.scan` closures entered through `nnx.jit` (trainer `ppo_loss_fn` l.176, `collect_trajectories` l.269, `traj_scan`, `replay._scan_body`). Mutating module state inside those scans is exactly the pattern NNX punishes with tracer leaks.
3. The codebase has no `sow` usage anywhere. It would be a first, placed in the hottest function.

**Chosen:** a new public method `ActorCriticRNN.forward_with_activations(x, h)`, and a shared private `_forward(x, h, acts)`.
- `__call__(x, h)` becomes `return self._forward(x, h, None)`, with its **signature and return value unchanged**.
- `acts` is a plain Python `dict` or `None`. Every capture is `if acts is not None: acts[name] = tensor`, which is Python-level only. With `acts=None` the traced program is **op-for-op identical** to today, so no retrace, no recompilation and no speed change on the training path. That is verified by jaxpr identity (Checkpoint 1.3), not assumed.
- **No parameter is created and no `rngs` stream is touched.** Construction (`__init__`, l.277–475) is not edited, so the D11 order is preserved by not being changed. A golden parameter-tree hash test pins it.
- `ObservationEncoder.__call__` and `.forward_with_modulation` gain the same optional `acts=None` keyword, to expose the per-sense and hub tensors before and after FiLM.

**Canonical layer names** (identical keys for both agents where the tensor exists):

| key | meaning | ordinary | modulated |
|---|---|---|---|
| `enc.uni.raw` | per-sense encoding after LayerNorm, before modulation / ReLU (…, 9, 128) | ✓ | ✓ (pre-FiLM) |
| `enc.uni.mod` | after modulation, before ReLU (for `Multiplicative`: after ReLU·gate) | — | ✓ |
| `enc.uni.out` | after ReLU | ✓ | ✓ |
| `enc.raw` / `enc.mod` / `enc.out` | hub output, the same three stages (`enc.out` == `x_proj`) | raw, out | all three |
| `rnn.state` | GRU carry `h_new` | ✓ | ✓ |
| `rnn.raw` / `rnn.mod` / `rnn.out` | emitted memory output before FiLM / after FiLM / the tensor fed to the heads | raw, out (`out`==`raw`) | all three (`out`==`mod`) |
| `actor.raw` / `actor.mod` / `actor.out` | `actor_fc1` output / after FiLM / after activation | raw, out | all three |
| `critic.raw` / `critic.mod` / `critic.out` | same for the critic | raw, out | all three |
| `logits`, `value` | outputs | ✓ | ✓ |

A `.mod` key is present only when that site is enabled. The comparison drivers pair ordinary `X.raw` with modulated `X.raw` (before the gain) **and** with modulated `X.mod` (after the gain), and pair `X.out` with `X.out`. This is the page's "before and after gain/offset" requirement.

**Shape of the per-sense layers (finding 14).** For CKA and predictivity, the `enc.uni.*` layers are **flattened to 9 × 128 = 1152 columns** and compared as one representation. Per-sense scoring is out of scope. The manifest's `layers` entry records `flatten: senses_x_units` for these keys. Because 1152 columns need many rows, the drivers refuse any layer whose probe has fewer than `min_rows_per_column` × columns rows (mandatory manifest key), rather than fitting an underdetermined ridge.

**Teacher-forced replay.** A new sibling, `scripts/analysis/nmn/teacher_forced.py`. `replay.py` stays the environment-rollout tool; it gains only a continual-aware world choice (§3). Per batch of probe episodes:
- Pad `obs_noised` rows `0..T−1` to `T_max` with a validity mask.
- Run `h0 = model.initial_state(B)`, then an `nnx.jit`-entered `jax.lax.scan` of `forward_with_activations` (the stale-view hazard documented in `replay.py`'s docstring).
- Keep only the requested layers at the probe's sampled rows (`rows_per_episode`, below), so memory stays bounded while the recurrence still runs over every step.

**Hard input checks before any forward pass:**
- The store manifest's `observation_breakdown` must equal `get_observation_breakdown(agent.env_params)` (same names, order, widths).
- `dims.D` must equal the model's `input_dim`.
- `schema_version == 1`.

**Action agreement.** Computed on every replay. If the replayed checkpoint is the store's generating checkpoint (`manifest.checkpoint_path` resolves to the same directory), the replay **fails** on any mismatch whose top-two logit margin is at or above gate G1's near-tie margin, or if near-ties exceed G1's maximum share of rows (both from `parameters:`; the rules as written say `1e-4` and 0.1%). Otherwise the agreement is recorded as a statistic: how often the other agent would have chosen the same action is itself an A1-adjacent result.

**Probe sets.** A probe set is `n_per_store` episodes drawn from each listed store, starting at block 0 so only the first shard is read.
- **One pass, one row index (finding 4).** `probe_set.build` reads each shard **once** with pyarrow. From that read it builds a single row-index array `rows = (store_id, episode_seed, t)`. Everything is then gathered with that same array object: `obs`, the full `obs_noised` sequences for replay, `action_next = action[t+1]`, and every target. Nothing is re-read or re-sorted between them.
- Asserted at build time:
  - within each episode, `t` runs `0..T−1`, strictly increasing and contiguous;
  - the row count per episode equals the episode table's `T`;
  - `action_next[t] == action[t+1]` for every `t` in `0..T−1`. Row `T` (the terminal state) exists in the store, so it supplies `action_next` for `t = T−1`, and nothing is masked (Revision 4, R4-5).
- It stores:
  - `obs` at the sampled rows;
  - the full `obs_noised` sequences needed for replay;
  - the row index;
  - `action_next`;
  - targets: `satiation`, `injury_level`, `nearest_predator_manhattan` (with a validity mask), `steps_remaining = T − t`, `truncated` (`termination_reason == 1`, max steps reached).

Rows are subsampled per episode (`rows_per_episode`, seeded), and the whole episode is replayed. A probe set's sha256 over the row index is written into every activation file and re-checked on load, so activations from different probes can never be silently paired.

For **the May replication**, the probe for a world pools an equal number of episodes from all six agents' stores in that world. Every agent is judged on the same inputs, and no agent's own behaviour dominates. Results are also broken down by source store as a sensitivity check. The **pilot** pools the pair's two stores.

**Group count (re-review R8).** All six May stores, and both pilot stores, are collected with the same `seed_base` (1,000,000). The first `n_per_store` episodes of every store therefore carry the **same** `episode_seed` values: the same reset draw, followed by different trajectories. The rules make each `episode_seed` one group, for the split and for the bootstrap (`common.grouping_unit`). So a pooled probe has only `n_per_store` distinct groups, not six times that. The held-out fold holds a fraction `test_frac` of them, and gate G6 requires at least a minimum number per held-out fold (both numbers come from `parameters:`; the rules as written say 20% and 500). So `n_per_store` must be at least `min_test_groups / test_frac` (2,500 before exclusions); the registered value is **5,000**, because survival-steps-remaining drops groups whose every copy was truncated (26.4% of the pilot's first shard), which leaves ~736 test groups at 5,000 but ~368 at 2,500. The value is the manifest's `probes[].n_per_store`, set by `experiment-designer`; it is never a default. Block 0 of every store holds 5,000 episodes, so one shard per store still suffices. `probe_set.build`:
- computes the number of distinct `episode_seed` groups and prints it, with the per-store episode counts;
- raises before any replay if `distinct_groups × test_frac < min_test_groups`;
- records `n_groups` in `probe_<id>.json`.

**Size.** A May probe is `6 × n_per_store` episodes (30,000 at the registered 5,000), replayed through every agent and checkpoint that needs it (A4: six agents × seven checkpoints × two probes, plus three untrained networks). Only `rows_per_episode` rows per episode are kept, so the activation files scale with `6 × n_per_store × rows_per_episode × layer width`. The developer sets `rows_per_episode`, computes the expected bytes before the first May run, and records the measured bytes.

After the split, `run_similarity` and `run_decoding` assert the actual held-out group count of every repeat against the same minimum (gate G6), so a rounding in the split cannot slip under it. **Per quantity, after that quantity's exclusions** (as the designer's G6 revision states): the predator-distance target keeps only groups with a valid row, and the `steps_remaining` headline keeps only groups with at least one death-ended episode. A group count below the minimum for one quantity blocks that quantity ("blocked by gate G6"), and the count is printed.

**Alignment controls (finding 4).** Computed by `teacher_forced` on the **sampled rows through the probe's row index**, so they test the same indexing the targets use:

| Control | Computed as | Required |
|---|---|---|
| **Step-discontinuous alignment** | `argmax(acts.logits[row]) == action_next[row]` on the generating agent's own store | 100% (the near-tie allowance of the action-agreement rule only) |
| Same, on **action-change rows only** (`action[t] ≠ action[t+1]`) | as above | 100% |
| **Shift-by-one** | `argmax(acts.logits[row]) == action[t]` (the action that *arrived* at *t*, one row early) | below gate G3's maximum overall (`parameters:`; 95% as written), and below `tool_checks.shift_change_rows_max` (a plan-level stop, 5%) on action-change rows. On those rows a correct alignment gives 0% by construction. If the overall number reaches G3's maximum, the control is **inconclusive**, not passed: stop and report, because the agent's action runs are too long for it to discriminate |

The satiation input-layer R² stays as a positive control for the target *values*, not for alignment: satiation drops by a fixed step each tick, so it cannot detect a one-row shift.

**A1 / A3 / A4 statistics.**
- Linear CKA uses the feature-space form ‖YᵀX‖²_F / (‖XᵀX‖_F‖YᵀY‖_F) on column-centred float64 features.
- Linear predictivity is ridge with the α-grid chosen by episode-grouped CV inside the training fold. It reports held-out R² (variance-weighted over output units) in both directions, and the rules' mutual value `P(A,B) = min(R²(A→B), R²(B→A))`, averaged over the split repeats.
- **Bootstrap (re-review R7; the rules' `common.bootstrap`, adopted as written).**
  - The resampling unit is the **`episode_seed` group**: all rows of that reset draw, from every store in the pooled probe.
  - The number of draws is the manifest's `bootstrap_n`, asserted at load to be at least the rules' G6 minimum. It is drawn **per split repeat** (see §Revision 2, point 3).
  - **Joint.** Each draw is one resample of groups, applied to every agent and every pair at once. So pair-to-pair and agent-to-agent comparisons are paired.
  - **Predictivity: fixed maps.** For each split repeat (the rules' number of repeats and test fraction, grouped by `episode_seed`; one split object shared by every agent), the ridge maps are fitted **once**, on the training fold, and held fixed. Each draw resamples that repeat's **held-out** groups with replacement and recomputes held-out R² from the fixed maps. The draws of all repeats are pooled into one distribution.
  - **CKA** has no fitted map. Each draw resamples groups over the whole probe and recomputes CKA.
  - Intervals are the rules' percentiles (`interval`, from `parameters:`). The band `[L, U]` (`seed_band`) and every "bootstrap distribution of the MO_diff mean" are computed from the same joint draws: per draw, the mean over the pairs entered, then its percentiles.
- **Reference rows** make a number readable:
  - the probe's raw input (symlog of `obs`);
  - **untrained networks (re-review R2): `untrained.build` on every ordinary run in the manifest, each with that run's own seed.** For the May replication that is three networks (seeds 42, 43, 44), giving the rules' three UNTRAINED pairs. They set the informative gate: per layer and statistic, the ordinary-vs-ordinary band must not overlap their envelope. The pilot has one ordinary run, so one untrained network and **no** untrained pair. Its informative gate is not computable, which is moot because the pilot has no verdict. The untrained networks are replayed on the probe like any agent, with chain assertions and without the self-replay check (they generated no store);
  - same-agent same-checkpoint (`isclose(…, 1.0, atol=tool_checks.self_similarity_atol)`; a check, not a result).
- **G5 exclusions come first.** A run that fails gate G5 (below) is dropped before any pair set is formed. `n` (the number of MO_diff pairs) and every count are recomputed, as the rules require. Below the rules' minimum number of seeds per arm, every verdict reads "undetermined — yardstick incomplete".
- **A3 triangle** (May replication, per layer): ordinary–ordinary across seeds (3 pairs), modulated–modulated across seeds (3), modulated–ordinary same seed (3), modulated–ordinary different seeds (6). The fair comparison for "the same computation" is **modulated–ordinary at different seeds vs ordinary–ordinary at different seeds**. The same-seed cell measures what the shared start (D11) contributes. `decision_rules.evaluate_A3` turns these cells into a pattern (§E).
- **Survival and food-intake inputs (re-review R5).** A3 pattern (c) versus (c′) depends on whether the two agents' survival differs, and gate G5 on each run's stage-1 competence. Neither is in the activations; both come from the training logs.
  - Read by `wandb_history.stage_level` (File Changes §7) from each run's local WandB binary. The folder is resolved from the run's saved top-level `tag:` in `models/config.yaml`, with exactly one match required.
  - Per run and stage *k* (0-based `stage/index`): `S_k`, the mean of `Episode/Steps` over the last `window` episodes of the stage, and the same mean of `Episode/FoodEaten`. Each row is weighted per `parameters.common.survival.row_weight` (`delta_episode_number`: the episodes the row adds, as `pilot_readout.Series` does; §Revision 2, point 5); rows with `Episode/_window_n` below `parameters.common.survival.min_window_n` are skipped. `window` is `parameters.common.survival.window_episodes`. This is the May design's §5.1 quantity. The stage must be complete; otherwise the value is `null`, pattern (c)/(c′) reads "survival not available", and the rules assign "none".
  - **G5 per run:** `S ≥` the survival minimum **and** food bites `≥` the bite minimum, at the stage `parameters.gates.G5.stage` names. That entry is **1-based** (May design naming; `1` = `01_active`), so the driver reads `stage/index = G5.stage − 1`. The two minima and the per-arm seed minima are `parameters.gates.G5.*`.
  - **Survival difference** for the stage whose end is analysed, read from `parameters.A3.survival_stage_by_status.<evidence_status>` (1-based, so `stage/index = k − 1`; as registered, stage 5 → `stage/index` 4 for `evidence`, stage 1 → `stage/index` 0 for `interim`): `mean_diff = mean(S_k, modulated seeds) − mean(S_k, ordinary seeds)`. `SE_k = sqrt(sd_ord²/n_ord + sd_mod²/n_mod)` (sample SD) and `SE_used = max(SE_k, SE_floor)`. "Survival the same" is `|mean_diff| ≤ multiplier × SE_used`. The floor and the multiplier are `parameters.common.survival.se_floor_steps` and `se_multiplier` (3.6 steps and 2 as registered, May design §5.2).
  - All of it is written into the `run_similarity` driver JSON (`survival: {per_run, per_arm, mean_diff, se_raw, se_used, floored, same}`, `gate_G5: {per_run, pass}`), which the evaluator reads.
  - **Cross-check.** `stage_level` is an independent implementation of a quantity that `scripts/analysis/studies/continual_worlds/pilot_readout.py` already computes for the May verdict. Checkpoint 4.6 requires the two to agree on every run.
- **A4** (re-review R4), per agent and verdict layer, on both world probes. **Every list here is read from `parameters.A4`, not typed** (Revision 3, T4): the checkpoint sequence is `A4.stage_sequence`, the probe worlds are `A4.probes`, and the drift pairs are `A4.drift_pairs`. The values quoted below are the registered ones, for orientation only. `run_similarity` asserts that the manifest's runs list every checkpoint these entries name, `:prev` included.
  - **movement** `m = 1 − P(a at c_i, a at c_{i+1})` for each consecutive pair `(c_i, c_{i+1})` of `A4.stage_sequence` (registered: `stage_end:0` … `stage_end:3`, `final`, so four transitions), on each probe of `A4.probes` (registered: active, passive): an 8-entry profile as registered;
  - **within-stage drift** `d_a`, the mean over the entries `{prev, checkpoint, probe}` of `A4.drift_pairs` of `1 − P(a at prev, a at checkpoint)` on that probe (registered: `final:prev` → `final` on the active probe, and `stage_end:3:prev` → `stage_end:3` on the passive probe). `:prev` is the checkpoint just before, in the same saved stage (File Changes §5). The episode gap of each `:prev` pair is recorded; the rules describe it as 100,000 episodes;
  - **movement gate:** per draw, `mean(profile) − d_a`; an arm moves if, for at least `parameters.A4.movement_min_seeds` of its seeds, the bootstrap lower percentile of that difference is above 0;
  - **co-movement** `r(a, b)`, the Pearson correlation of two agents' profiles, from the same joint draws, judged by A1's per-statistic rule with the OO pairs as yardstick;
  - the A1 layer verdict at each of the five stage ends, each on its own world's probe (active for stage ends 0, 2 and `final`; passive for 1 and 3). So the A1 machinery, including the untrained references, runs on both probes.
  - `decision_rules.evaluate_A4` reads all of these.

**A2 decoding.**
- Ridge regression (standardisation fitted on the training fold only). The score is held-out R², the mean over the split repeats shared by all agents, with the bootstrap above.
- Split by **`episode_seed` alone** with `GroupShuffleSplit` (the rules' number of repeats and test fraction, a manifest seed), so the **same split is used for every agent** on a probe and comparisons are paired. In the pooled May probe, one `episode_seed` appears in all six stores: the same reset, with different trajectories. Grouping by seed alone keeps one world draw out of both folds. **Do not group by `(store, episode_seed)`**, because that leaks the draw (finding 12).
- An assertion that no `episode_seed` appears in both folds.
- Targets: `satiation`, `injury_level`, `nearest_predator_manhattan` (valid rows only), `steps_remaining`.
- **`steps_remaining` (finding 9).** **The headline excludes truncated episodes.** An episode cut off at `max_steps = 500` has a censored remaining lifetime, and `steps_remaining = 500 − t` is then just a clock. 33.5% of pilot episodes are truncated (measured by the reviewer on shard 0 of both w0000 stores). The all-episodes version is kept as a sensitivity row that decides nothing. The exclusion biases the headline toward shorter lives, and the data statement says so.
- **Clock baseline (re-review R6; the rules' `A2.clock_baseline`, adopted as written).** `R²_clock` is the held-out R² of predicting the target from the time step alone, **fitted as the per-time-step mean of the target on the training fold**: for each `t` present in the training fold, the mean of the target over training rows at that `t`. It is scored on the same held-out rows and splits as the layers, for every target. It depends only on the probe, so it is one number per target and split, shared by every agent. It is drawn as a reference line on each layer's panel.
  - A held-out row whose `t` has no training row has no clock prediction. Such rows are dropped from the layer score and the clock score alike, and counted in the data statement (§Revision 2, point 2).
  - The earlier one-hot ridge on `t` bins, the `t_bin_width` key, and the `R²(layer ⊕ t) − R²(t)` column are **removed**.
- **Excess over the clock** (the rules' `beats_clock`): per agent, target and layer, `excess = R² − R²_clock`. Its bootstrap distribution uses the same joint draws: the clock's R² is recomputed on each draw's resampled held-out groups, from the same fixed per-step means. The reported numbers are the point excess and its lower bootstrap percentile. The margin and the percentile come from `parameters:`, and "beats the clock" is decided only in `decision_rules.evaluate_A2`.
- Controls: the input layer (a **positive control**: satiation is itself an observation channel, the `Satiation` sensor, so R² at the input must meet gate G4's minimum; if not, target values are wrong), and **shuffled targets across episodes** (a negative control: R² at or below G4's maximum). Row alignment is checked separately (Alignment controls, above).
- Whether two agents' profiles "match" is `decision_rules.evaluate_A2`.

**B2 wake-up.**

| Measure | Source | Resolution | Untrained anchor (step 0) |
|---|---|---|---|
| total-loss gradient share | local WandB, `modulator/grad_norm`² / `loss/grad_norm`² | log points, binned to checkpoint intervals | no (first log point ≈ iteration 50) |
| per-term gradient share | `grad_probe.py` at every checkpoint (level-05 and May alike; Revision 3, T1) | checkpoints | **yes** (probe on the untrained network with a freshly initialised optimiser, which is exactly the trainer's state at step 0) |
| relative update size | `ckpt_io.load_params` at consecutive checkpoints, modulator vs main | checkpoint intervals | **yes** (first interval is untrained → first checkpoint) |
| contextual fraction ρ | `replay.rollout` (greedy, fixed seeds 90 000+) → `mod_distribution.variance_split` per site | checkpoints | **yes** |
| gain swing | `spectral_bound` (weights only) | checkpoints | **yes** |
| freeze cost | `freeze.apply_freeze` (gain frozen, offset frozen, separately) + `replay.rollout` + `freeze.paired_differences` | checkpoints (every one) | **yes** |
| survival (for the plateau) | local WandB `Episode/Steps`, binned per checkpoint interval (`wandb_history.interval_means`) | checkpoint intervals | no (first binned point) |

**Where the wake-up rule and numbers come from (re-review R3).** The B2 rule is registered in the rules file's `B2` section (written by `experiment-designer`), and every B2 number lives in `parameters.B2` of that sha-pinned file. This plan fixes **no value** and does **not** choose the headline; `parameters.B2.threshold_mode_headline` does. The B2 runs are listed in the wake-up manifest, `docs/experiments/active/modulator_clues/algorithmic_null_wakeup.yaml`, which pins the rules file like every other manifest. If that manifest also states any B2 value, it must equal `parameters.B2` (mismatch raises). `wakeup.py` has no defaults; `run_wakeup` passes every value explicitly. Stage 4 does not start until the rules revision and the wake-up manifest are committed (Stage R). The summary below follows the rules' `B2` section; where the two differ, the rules win and the code follows them.

**Wake-up definition (finding 1; rules `B2`).**
- **Points.** The run's saved checkpoints (episode count), plus step 0, the untrained network, for the measures marked anchorable above. **Every measure uses the same grid: every saved checkpoint the wake-up manifest lists, plus step 0 for the anchorable ones.** No measure is sampled more sparsely (Revision 3, T1). A measure logged more often than checkpoints (total-loss gradient share, survival) is first averaged within each checkpoint interval `(x_{i−1}, x_i]`. Survival rows are weighted per `parameters.common.survival.row_weight` (`delta_episode_number`, the episodes each row adds) and skipped below `parameters.common.survival.min_window_n`, as the rules' `x_grid` states (§Revision 2, point 5). So `sustain`, `final_k`, the noise band and the lag's coincidence band mean the same for every curve, and one interval is one checkpoint for all of them.
- `m₀` is the step-0 value where anchorable; otherwise the first available point, and the output says which. For survival, `m₀` is its first binned point.
- `m_final` is the mean of the last `final_k` points. `d = sign(m_final − m₀)`, recorded as `rising` or `falling`.
- **Noise band.** σ_Δ is the standard deviation of consecutive differences over the **noise window**: the last `max(ceil(N / noise_window_divisor), min_noise_points + 1)` points, `N` counting step 0. `noise_window_divisor` is `parameters.B2.noise_window_divisor` (3 as registered), passed to `t_cross` like every other B2 value (Revision 3, T4). If that window would exceed `noise_window_max_fraction × N` points, the result is NaN, reason "too few points to estimate noise".
- **Minimum-change guard.** If `|m_final − m₀| ≤ noise_k · σ_Δ`, the result is NaN, reason "net change within the measure's own noise band". A checkpoint is never named in that case.
- **Signed crossing** (`fraction_of_rise`): `t_wake` is the first `x_i` with `d·(m_i − m₀) ≥ f·|m_final − m₀|` that holds at `sustain` consecutive points (`x_i` is the first of them).
- **Literal crossing** (`fraction_of_final`, always beside, never headlined): the first `x_i` with `m_i ≥ literal_f·m_final`, flagged `degenerate: true` when `m₀` already satisfies it (the known trap: the gain swing starts at ≈ 61% of its final value) or when `d` is `falling`.
- **Plateau.** `t_plateau` is the signed rule, guard and `sustain` applied to binned survival with fraction `plateau_f`.
- **Lag.** `lag = t_wake − t_plateau` in episodes; `|lag| ≤ lag_coincident_max_intervals` checkpoint intervals reads "coincident"; NaN if either time is NaN.
- **Reading per measure across the 16 level-05 worlds.** `n_def` = runs with a defined lag. `k*` = the smallest `k` with `P(Binomial(n_def, ½) ≥ k) ≤ sign_test_alpha`. "late" if at least `k*` runs have lag above the coincidence band, "early" if at least `k*` below, otherwise "undetermined across worlds". The three May seeds are reported as "agree" or "do not agree" and decide nothing alone. This reading is evaluated in `decision_rules.evaluate_B2`, with the same no-literal and fixture-sign-off discipline as A1–A4.

**Sampling: every checkpoint, for every measure (the rules' `known_consequence`; Revision 3, T1).** Per-term gradient share and freeze cost were once planned at every 5th checkpoint, and Revision 2 added a dense final third on level-05. Both are withdrawn. The reason is resolution, not only point count. `t_wake` is the first *sampled* point that crosses, so on a sparse stretch it rounds **up** to the next sampled checkpoint: always later, never earlier. The rules' coincidence band is one checkpoint interval (`lag_coincident_max_intervals`). On the level-05 w0000 modulated run, the registered plateau rule lands at checkpoint 13 (the reviewer's reading of the local WandB log). A measure that truly woke at checkpoint 11–14 would have been reported at 15, a lag of +1 to +4 checkpoints, which reads "late" for a coincident measure. The bias has the same direction on every world, so the across-worlds sign test could accept it.
- **level-05:** every checkpoint (50) plus step 0 for the anchorable measures: `N` = 51, window `max(ceil(51/3), 6)` = 17 points; `N` = 50 without the anchor, window 17. Both within `noise_window_max_fraction × N`.
- **May `01_active`:** every checkpoint (15) plus step 0: `N` = 16, window 6; `N` = 15, window 6. Both within bounds.

`run_wakeup` builds one grid per run from the manifest's `checkpoints` list (plus step 0 where anchorable) and asserts that every measure's curve uses exactly that grid. There is no per-measure point set, in the manifest or in code. It computes `N` and the window per curve before any rollout, and refuses to start a measure that cannot meet the window. This is decided now, before any curve exists.

Both definitions and the guard's verdict are always reported. The wake-up tests (File Changes §11) use their own fixture values, marked as such.

For continual runs, B2 uses **`01_active` only** (episodes 0–1.5 M, the only stage trained from scratch), with the stage-local final value.

**Survival plateau first (the third review's open question; Checkpoint 4.0).** Every lag needs `t_plateau`, and a lag is undefined wherever the plateau is NaN. The survival half of B2 needs only the local WandB logs, so it runs **first**, on CPU, for all 19 runs (16 level-05 modulated, 3 May modulated `01_active`), before any rollout or gradient probe. Per run it records `t_plateau` (checkpoint and episode), `m₀`, `m_final`, σ_Δ, the guard margin `|m_final − m₀| / (noise_k·σ_Δ)`, and the NaN reason if any. The reviewer checked one run (w0000: plateau at checkpoint 13, guard margin ≈ 100×). **If any run's plateau is NaN, the GPU sweep does not start.** The list goes to the user and `experiment-designer`, because reading B2 on the remaining runs changes `n_def` and the sign test's `k*`. That is their call, not the tooling's.

**Untrained-network anchor.** `train.py` builds the network as follows (verified at HEAD):
```
key = PRNGKey(seed)                                  # train.py:1152, seed = --seed or config seed (l.785)
key, model_key, env_key = split(key, 3)              # train.py:1153 — model_key is NEVER used
env.reset(env_key, num_envs)                         # train.py:1156
key, init_key = split(key)                           # train.py:1207
ActorCriticRNN(..., rngs=nnx.Rngs(init_key), ...)    # train.py:1241-1245
```
The new helper `untrained.build(run_dir)` follows this key chain, and builds the architecture from the run's saved `config.yaml` exactly as `replay.load_agent` does. `seed` is the saved top-level `seed:`, cross-checked against the `--seed` argument in the run's `wandb-metadata.json`; a mismatch raises. Because this reconstruction re-derives the trainer's steps, it is **verified against the trainer itself** (Checkpoint 4.4). A small harness imports `train`, replaces the `ActorCriticRNN` name in `train`'s namespace with a subclass that records `nnx.state(self, nnx.Param)` after `__init__` and then raises a sentinel exception, and runs `train.main()` with the run's own launch arguments (from `wandb-metadata.json`, with `--no-wandb` and a scratch `--results-dir`). The recorded parameters must equal `untrained.build`'s bitwise. A second, independent check uses saved state: the reconstruction for the run's own seed must be closer (cosine similarity of flattened main-network parameters) to the run's **first saved checkpoint** than the reconstructions for two other seeds are.

### Staging, and the verifiable check at each stage

| Stage | When | Work | Verifiable check (must pass to proceed) |
|---|---|---|---|
| **0 — preflight** | now, CPU, no code change | Strict `load_agent` on every run in both manifests. Key-level diff of the May replication's stage files. Read `observation_breakdown` from one store of each study | All loads pass. Active stages' env sections equal `config.yaml`'s. Store/model breakdown equal. Result recorded in the Implementation Report |
| **R — rules on file** | **before Stages 3 and 4**; owner `experiment-designer` | (a) The rules file `algorithmic_null_decision_rules.yaml`, revised with its `parameters:` block and `B2` section, committed, and every manifest re-pinned to its sha256 in the same commit. (b) The wake-up manifest `algorithmic_null_wakeup.yaml` committed. (c) The designer's sign-off of the evaluator's fixture table (after Stage 3's unit tests exist, before any real output) | Commit sha and time recorded (Checkpoint R.1). The rules commit **precedes** the `generated_utc` of the first `run_similarity` / `run_decoding` output of **any** manifest, pilot included, and of the first `run_wakeup` output. The sign-off precedes the first real `run_similarity` / `run_decoding` output (Checkpoint R.2). The pilot's same-seed numbers are exactly the kind of number a post-hoc threshold would be fitted to |
| **1 — capture switch** | now | File Changes §1–2 | `tests/models/test_capture_activations.py` passes. **The jaxpr of the training loss gradient and of `get_action_and_value_nnx` is textually identical before and after** (Checkpoint 1.3, method tested on 2026-09-29). The golden parameter hash is unchanged. Existing `tests/models/` pass |
| **2 — replay + pilot probe** | now | §3–4. Probe on the level-05 **w0000 pair** (`n_per_store` episodes from block 0 of each store, the pilot manifest's value; 5,000 as registered in the manifests, §Probe sets) | Distinct group count printed and above the G6 floor. Each agent on its **own** store: 100% action agreement (near-tie allowance only). Alignment controls pass at their numeric bounds. Chain assertions pass on the real checkpoints. Same-agent CKA ≈ 1 (`tool_checks.self_similarity_atol`) |
| **3 — pilot A1/A2 + figures** | after Stage R (a) and (c) | §6, §8–9. Figures `an01`–`an03` in *pilot* mode. Builder §11 checks (§10) | Unit tests pass, including the no-literal and parameter-coverage tests. Controls meet gate G4's bounds (read from `parameters:`). Page builds. `artifact-format-reviewer` passes. Every pilot figure's data statement carries the rules' pilot label (**"tool validation — the two agents share seed 42; not evidence"**) **and** "no verdict is drawn", because the rules set `verdict_words_allowed: false` for the pilot; the decision functions are never called |
| **4 — B2 on existing runs** | after Stage R (a), (b) and (c), in parallel with 3 | §7, §11, driven by the wake-up manifest. All 16 level-05 modulated runs, plus May-replication **`01_active`** for the three modulated runs. **Order:** the survival plateau for all 19 runs first (CPU, logs only), then the timing gate, then the GPU sweep with every measure at every checkpoint | **Survival plateau defined for all 19 runs before any rollout (Checkpoint 4.0).** Every measure's grid is the manifest's full checkpoint list (plus step 0 where anchorable). Wake-up values equal the rules' `B2` section. Untrained anchor verified (Checkpoint 4.4). Shared start verified on the May configs (Checkpoint 3.3). Gradient probe inside the sanity band (Checkpoint 4.2). Freeze equivalence: `freeze.verify_freeze_equivalence` passes before each sweep. ρ closure identity (asserted in `mod_distribution`) holds. Timing gate (§Stage 4 budget) passed before the full sweep |
| **4b — early yardstick (optional)** | after Stage R | Collect the **`stage_end:0`** checkpoint (end of `01_active`) of all six May-replication runs (world = stage 0 = `config.yaml`, correct with the current collector), 10,000 episodes each, **one spec per run with an explicit step** through `run_collection.py`. Then A1/A3 at the end of `01_active`, with stage-1 survival and G5 from the logs (§A3) | As Stage 2 for every store. **Checkpoint 3.3 passed for all three seeds (42, 43, 44)**: the shared start that A3's same-seed reading relies on. Stage-1 survival cross-check passes (Checkpoint 4.6). A3 figure in *interim* mode; every verdict word carries the rules' interim prefix ("provisional — end of stage 1 of 5") |
| **5 — collector continual-awareness** | now, so it is ready when training ends | §5 | New tests in `tests/test_trajectory_collection.py` pass. On a real May-replication run, `stage_end:0` and `stage_end:3` resolve to checkpoints whose saved `stage` is 0 and 3, and the `stage_end:3` world has `detection_range: 0` |
| **6 — May replication, full** | after training, **and after Checkpoint R4.1** (Revision 4: every store in full float32, recorded in its manifest; this applies to the Stage 4b stores too) | Launch collection of `final` + `stage_end:3` (end of `04_passive`) for all six runs via the finished-runs-only launcher with the six logs **named** (§12). Then A1–A4 (activations at `stage_end:0..3`, `final`, `stage_end:3:prev` and `final:prev` on both world probes; the `:prev` checkpoints need no stores of their own) and B2 `01_active` are final | Every store validates (`validate_store_structure/shapes/draws`). Each store's `resolved_env_config.environment` equals its stage file's. Action agreement 100% per generating agent. The figures switch to `evidence_status: evidence` |

What the page can carry when:
- **After Stage 3:** pilot A1/A2 figures, labelled as tool validation, no verdicts.
- **After Stage 4:** real B2 results (level-05 ×16, May `01_active` ×3 modulated).
- **After Stage 4b:** an interim A3.
- **After Stage 6:** A1–A4 on the May replication.

**Stage 4 budget (the reviewer's open question).** Work items:
- update size and swing: weights only, 16 × 51 + 3 × 16 points, CPU, minutes;
- survival plateau (Checkpoint 4.0): 19 local WandB binaries, CPU, minutes; runs first;
- ρ: one 128-episode greedy rollout per point, ≈ 16 × 51 + 3 × 16 ≈ **864 rollouts**;
- freeze cost: every point (§B2: 51 per level-05 run, 16 per May run), 3 conditions (live, gain frozen, offset frozen), ≈ 16 × 51 × 3 + 3 × 16 × 3 ≈ **2,600 rollouts** (Revision 3, T1; was 1,344);
- gradient probe: the same points, ≈ 16 × 51 + 3 × 16 ≈ **860 probes** (was 448). Each probe is `warmup_iters` + 1 training-shaped iterations with 128 envs × 128 steps, and 4 updates.

Scale: 128 episodes × ≤ 500 steps is 500 sequential scan steps at batch 128. Level-05 training ran ≈ 143 episodes/s including updates, so one probe iteration is well under a second once compiled. The sweep is **compile-dominated**: a few jit compilations per run (one per model structure and rollout shape), not per checkpoint. The Revision 2 estimate was ≈ 6–12 GPU-hours for ≈ 2,660 items. At every checkpoint the sweep is ≈ 4,320 items (freeze and probe roughly doubled, ρ unchanged), so the estimate becomes **≈ 10–20 GPU-hours in total** (Revision 3). It runs as two worker processes on the **two GPUs of one low-tier node** (RTX 2080 Ti class, per [LAB_NODE_GPU_SPEC](../../../environment/LAB_NODE_GPU_SPEC.md); routine small-network work), so **≈ 5–10 h wall-clock**, and the upper half of that range triggers the second-node rule below. The node is chosen from `gpu-status` plus the diary, pack-node-first. This is an estimate, so it is gated:
- **Timing gate:** before the full sweep, time one run × 3 checkpoints × every measure, and record seconds per item in the Implementation Report. Extrapolate.
- If the extrapolation exceeds **8 h wall-clock**, spread the sweep over a second node's GPUs (pack-node-first). **No measure is thinned**: thinning changes `N`, the noise window and what `sustain` means, all of which are registered. Decide and record this *before* the full sweep.

### File Changes

All new Python under `scripts/analysis/nmn/` is two levels deep. Drivers insert the repo root three `..` up. Library modules walk nothing and are imported as `scripts.analysis.nmn.<mod>` (the `ckpt_io.py` pattern, [[SCRIPTS_DEPENDENCY_MAP]] §0).

#### 1. `src/models/recurrent_ppo_network.py` — explicit capture path (no construction change)

```python
# ObservationEncoder.__call__ (l.177) and .forward_with_modulation (l.205):
#   add keyword `acts=None`; after each stage,
#   if acts is not None: acts["enc.uni.raw"] = encoded_all   (post-LN, pre-mod/ReLU)
#                        acts["enc.uni.mod"] = <after modulation>   (modulated path only)
#                        acts["enc.uni.out"] = <after ReLU>
#   and likewise enc.raw / enc.mod / enc.out for the hub. Flat mode: enc.raw/mod/out only.
#   Expressions are unchanged; only named intermediates are bound to local variables.

# ActorCriticRNN:
def __call__(self, x, h):                        # signature + 4-tuple return UNCHANGED
    return self._forward(x, h, None)

def forward_with_activations(self, x, h):
    """Same computation as __call__, plus a dict of named intermediate tensors.
    Analysis-only. Adds no parameters and draws no RNG."""
    acts = {}
    logits, value, h_new, mod_info = self._forward(x, h, acts)
    acts["logits"], acts["value"] = logits, value
    return logits, value, h_new, mod_info, acts

def _forward(self, x, h, acts):                  # body of today's __call__ (l.503-591),
    ...                                          # with `if acts is not None: acts[k] = t`
```

`__init__` (l.277–475) is **not edited**. `get_action_and_value_nnx` (l.613) is not edited.

#### 2. `tests/models/test_capture_activations.py` — new

- **Equality with `__call__`:** inside `nnx.jit`, over a 20-step scan with random inputs, `forward_with_activations(...)[:4]` equals `__call__(...)`. Bitwise is expected. If XLA fuses the two programs differently, the tolerance is `max|Δ| ≤ 1e-6·max|x|` with identical argmax, and the observed deviation is recorded in the test output. Configurations: ordinary hierarchical + LayerNorm; the modulated four-site FiLM `activation` config (the t16quad agent block); FiLM `gate_bias`; flat encoder mode; `PreActivation`.
- **Reconstruction:** the same chain as the run-time assertions of §4, on synthetic weights.
- **No state leak:** the `nnx.state(model)` path set and shapes are identical before and after a capture call.
- **Construction pinned:** the sha256 of the flattened parameter tree of `ActorCriticRNN(..., rngs=nnx.Rngs(PRNGKey(0)))` equals a golden hash for the ordinary and the t16quad configs. **The developer records the golden values by running the hash on the pre-change commit, before editing the network**, and states the commit in the test.
- **Key set:** exactly the documented keys per configuration. A `.mod` key exists iff that site is enabled.

#### 3. `scripts/analysis/nmn/replay.py` — continual-aware world (small)

`load_agent(models_dir, step=None)`: for a run whose `models/` holds `schedule.yaml`, build `env_params` from the checkpoint's **own stage** file, reusing `scripts.eval.eval_rollout._resolve_continual_stage_config(cfg_path, ckpt_dir)`. The agent block still comes from `config.yaml`. Print the resolved world. `LoadedAgent` gains `env_config_path: str`. This matters for ρ and freeze-cost rollouts at later-stage checkpoints. Teacher forcing only needs the observation layout, which is identical across stages.

#### 4. `scripts/analysis/nmn/teacher_forced.py` + `scripts/analysis/nmn/probe_set.py` — new

- `probe_set.build(stores: list[Path], n_per_store, rows_per_episode, seed) -> Probe`:
  - reads the step and episode shards from block 0 upward with pyarrow, **once**;
  - uses decision rows `0..T−1` (the `read_decision_rows` convention in `scripts/analysis/studies/level05_body_interactions/_common.py`);
  - builds the single row-index array and gathers `obs`, `action_next` and all targets through it (§Probe sets);
  - derives targets (§F for predators, via the manifest's `animal_classes` and the episode `animal_active`);
  - counts the distinct `episode_seed` groups, prints them with the per-store episode counts, and raises if `n_groups × test_frac` is below gate G6's held-out minimum (re-review R8, §Probe sets). `test_frac` and the minimum come from `parameters:`, passed in by the driver;
  - writes `probe_<id>.npz` and `probe_<id>.json` (sources, counts, `n_groups`, sha256 of the row index).
- `teacher_forced.replay(agent, probe, layers, batch_size) -> Activations` plus the agreement report and the alignment controls (§Design). The npz is keyed by layer name and carries the probe hash.
- **Run-time chain assertions on the real checkpoint (finding 3).** Every capture checks a batch of `assert_n_episodes` whole episodes (mandatory key), using **consecutive** rows so that `h_prev` is available. Every captured key is recomputed from its upstream neighbour with the model's own submodules, eagerly and outside the scan. Let `x̃ = symlog(obs)` and γ, β the per-step values from the returned `mod_info` (FiLM; for `PreActivation`/`Multiplicative` the corresponding sigmoid forms):

  | Assertion | Applies when |
  |---|---|
  | `enc.uni.raw == unimodal_ln(unimodal_grouped(pad(x̃)))` | hierarchical |
  | `enc.uni.mod == γ_uni[..., None, :]·enc.uni.raw + β_uni[..., None, :]` | encoder site on |
  | `enc.uni.out == relu(enc.uni.mod)` (or `relu(enc.uni.raw)` if the site is off) | hierarchical |
  | `enc.raw == multimodal_ln(multimodal_hub(enc.uni.out.reshape(…, −1)))` (flat mode: `flat_ln(monolith(x̃))`) | always |
  | `enc.mod == γ_multi·enc.raw + β_multi`; `enc.out == relu(enc.mod or enc.raw)` | encoder site on / always |
  | `(rnn.state, rnn.raw) == rnn_cell(rnn.state[t−1], enc.out[t])`, with `rnn.state[−1] = initial_state` | always |
  | `rnn.mod == γ_rnn·rnn.raw + β_rnn`; `rnn.out == rnn.mod or rnn.raw` | rnn site on / always |
  | `actor.raw == actor_fc1(rnn.out)`; `actor.mod == γ_actor·actor.raw + β_actor`; `actor.out == relu(actor.mod or actor.raw)` | always / actor site on / always |
  | the same three for `critic.*` | always / critic site on / always |
  | `logits == actor_fc2(actor.out)` (`/ temperature` if the temperature site is on); `value == critic_fc2(critic.out)` | always |
  | `argmax(logits[t]) == stored action[t+1]` | generating agent (the only link to stored ground truth) |

  Tolerance: `max|Δ| ≤ tol · max(1, max|reference|)` in float32, with `tol` = gate G2's reconstruction tolerance from `parameters:` (1e-5 in the designer's revision). The recomputation is a separate XLA program, so bitwise equality is not expected. Every assertion's max deviation is written into the activation file's JSON. Any failure aborts the capture. Because each key is checked against its neighbour, a single key bound to the wrong tensor fails at least one row of this table.

**Revision 4 amendments to §4** (details in §Revision 4): the chain check's form is unchanged, and its JSON gains the per-quarter maximum (R4-4). The sampled-vs-full comparison is held to `tool_checks.buffer_index_rel_tol`, per row, with a planted off-by-one control (R4-4). The store's matmul mode is resolved as in R4-1 (`recorded`, or an explicit value for a legacy store), and `capture_matmul_precision` must be `highest`. `run_activations` runs the float32 self-test at start (R4-1). Only the layers the manifest marks for a capture are kept (R4-2). The unused `SITE_OF` goes (R4-7).

#### 5. `scripts/eval/traj_collect/collect_trajectories.py` — continual-aware collection

- `resolve_checkpoint(run_dir, which)` accepts `stage_end:<k>`: **the last saved checkpoint whose saved `stage` field equals *k*** (0-based; reuse `continual_forgetting_matrix.read_saved_stage`). If no checkpoint has stage *k*, it raises. For a run with no `schedule.yaml`, `stage_end:<k>` raises.
- **`:prev` selectors (re-review R4).** `stage_end:<k>:prev` is the saved checkpoint immediately before `stage_end:<k>` in numeric step order. `final:prev` is the one immediately before `final`. Each **must have the same saved `stage`** as the checkpoint it precedes, so both lie inside one stage; otherwise, or if there is no earlier checkpoint, it raises. `final:prev` on a non-continual run is allowed (no stage check; there is only one stage). The resolver returns the episode gap between the pair, which the A4 driver records.
- This one resolver is the only checkpoint-selector implementation. The analysis drivers (`run_activations`, `untrained`, `run_wakeup`) import it, so the collector and the analysis can never disagree on what `stage_end:3:prev` means.
- For a run with `schedule.yaml`, the collector resolves the checkpoint's own stage file (via `_resolve_continual_stage_config`) and builds the **dict that is fingerprinted and stored as `resolved_env_config`** as follows (finding 8):
  1. start from a deep copy of `config.yaml`;
  2. replace its **world sections** `environment`, `sensory`, `body`, `thermal`, `perceptual_noise` with the stage file's;
  3. keep `agent`, `seed`, `tag`, `wandb` and everything else from `config.yaml`;
  4. if any **other** top-level key differs between the stage file and `config.yaml` (apart from `agent`, `tag`, `wandb`), raise and name the key. The world definition must not change without the fingerprint knowing.
  
  `env_fp = env_fingerprint(that dict)`. `seed` is still read from the top level (`KNOWN_BUGS.md` line 114), so it is the run's own seed.
- `apply_saved_config_compat` and `assert_scene_unambiguous` run on that dict.
- **No schema change:** no new column, `SCHEMA_VERSION` stays 1. `train_config_mtime` keeps reading `config.yaml`.
- Non-continual runs: behaviour unchanged, verified by the existing tests.
- **Revision 4 (R4-1, R4-7), before the May collection:** `main()` runs under `jax.default_matmul_precision("highest")` after `float32_matmul_selftest` passes. The manifest gains `matmul_precision`, `compute_device_kind` and `matmul_selftest_max_rel_err`, and the first two join `MANIFEST_GUARDED_FIELDS` in `src/utils/trajectory_store.py`. `docs/environment/TRAJECTORY_STORE_SCHEMA.md` §2 is updated in the same commit, with no `SCHEMA_VERSION` bump. A world section missing from a stage file raises instead of being deleted. Tests as listed in R4-1 and R4-7.
- `run_collection.py` passes the checkpoint string through unchanged (l.167). Confirm its spec validation accepts `stage_end:<k>`.

**Tests** (`tests/test_trajectory_collection.py`, extended), on a synthetic continual `models/` fixture (`schedule.yaml`, `config.yaml`, a stage-0 file identical to it, a passive stage-1 file with a different `environment` and a different `tag`/`wandb` and no `agent`, and checkpoint dirs with saved `stage` values including a lagging one):
- `stage_end:1` resolves to the last stage-1 checkpoint; a lagging checkpoint (episode past the boundary, saved `stage` still 0) is counted as stage 0; no stage-2 checkpoint → `stage_end:2` raises;
- `stage_end:1:prev` resolves to the checkpoint before it; a fixture where only one stage-1 checkpoint exists (so the one before it is stage 0) → `stage_end:1:prev` raises; `final:prev` resolves, and raises on a fixture whose second-to-last checkpoint has a different saved stage;
- **(i)** a stage-0 checkpoint of the continual fixture gets the **same `env_fp`** as the non-continual path would give for the same `config.yaml`;
- **(ii)** a passive-stage checkpoint gets a **different `env_fp`**, so its store lands in a different directory;
- **(iii)** the manifest's `resolved_env_config["environment"]` equals the stage file's `environment`, and its `seed`/`tag` equal `config.yaml`'s;
- a stage file differing in `training` raises;
- `final` on a non-continual fixture is unchanged.

No existing store belongs to a continual run (the reviewer checked: none under `results/trajectories_*` has a `schedule.yaml`), and `pilot_readout.py` reads only WandB binaries, so this change touches neither.

#### 6. `scripts/analysis/nmn/representation.py` + `scripts/analysis/nmn/decision_rules.py` — new, pure numpy / sklearn / python

- `representation.py`: `linear_cka(X, Y)`, `fit_predictivity_maps(X, Y, split) -> maps` and `heldout_r2(maps, X, Y, rows)` (so a map is fitted once per split repeat and scored on any resample of held-out rows, re-review R7), `ridge_probe(X, y, split)` (same fit/score separation), `clock_baseline(t, y, split) -> per-step means` and `clock_r2(means, t, y, rows)` (the rules' per-time-step training-fold mean; rows whose `t` has no training row are returned as a mask so every scorer drops them alike, re-review R6), `episode_split(groups, n_repeats, test_frac, seed)` (asserts disjointness), `joint_group_bootstrap(groups, split, n, seed) -> draws` (one set of resampled held-out group indices per repeat and draw, shared by every agent and pair). Everything in float64. No threshold lives here.
- `decision_rules.py` (the contract of §E). **Revision 4 (R4-3):** the loader is `rules_pin.load` (§14), imported, not reimplemented; `verdict_policy` is `rules_pin.evidence_policy`; `require_clean(pinned)` lives in `rules_pin`.
  - `load(manifest) -> Rules`: reads `decision_rules.file`, computes the whole-file sha256, raises `ValueError` if it differs from `decision_rules.sha256`; returns the parsed rules, the `parameters:` mapping, the sha256 and the file's last commit sha;
  - `require_clean(path)`: raises on uncommitted changes. The drivers call it whenever `evidence_status.<status>.verdict_words_allowed` is true in the loaded rules (today `interim`, `evidence` and `b2_wakeup`), never on a hard-coded status list (Revision 3, T3);
  - `verdict_policy(rules, evidence_status) -> (allowed, prefix, label)`, straight from `evidence_status.<status>`; `prefix` and `label` are `None` where the rules give none. A status that is not a key of the rules' `evidence_status` mapping raises;
  - gate functions `gate_G1` … `gate_G6`, and `evaluate_A1`, `evaluate_A2`, `evaluate_A3`, `evaluate_A4`, `evaluate_B2` (the across-worlds reading), `study_reading_*`: each takes the driver's statistics and `parameters`, returns an outcome word from the rules' own vocabulary (or "blocked by gate <id>", "undetermined — yardstick incomplete"), and raises on any input combination the rules do not assign. Docstrings quote the rule text verbatim;
  - survival helpers for A3 and G5: `survival_difference(S_by_arm, params)` (mean difference, `SE_k`, `SE_used = max(SE_k, floor)`, the "same" test) and `gate_G5(per_run, params)`. The stage each reads is taken from `parameters.gates.G5.stage` and `parameters.A3.survival_stage_by_status`, both 1-based, translated once as `stage/index = k − 1` (Revision 3, T4);
  - **`remedy.*` is reported, not exempt (Revision 3, T4).** `study_reading_A1` reads `parameters.remedy.undetermined_layers_trigger` and `parameters.remedy.extra_seeds` and adds two fields to its output: `remedy_triggered` (yes when at least that many A1 layers read "undetermined") and `remedy_extra_seeds` (the list). It never acts on them: launching extra seeds is the user's decision, as the rules say. So the coverage test needs no exemption list;
  - **A4's lists are read, not typed (Revision 3, T4).** `evaluate_A4` and `run_similarity` take the checkpoint sequence, the probe worlds and the drift pairs from `parameters.A4.stage_sequence`, `.probes` and `.drift_pairs` (§A4).

**Tests** (`tests/analysis/test_nmn_representation.py`, `tests/analysis/test_nmn_decision_rules.py`):
- `isclose(CKA(X,X), 1, atol=1e-12)`;
- CKA is invariant to orthogonal rotation and isotropic scale;
- **CKA drops under a per-unit rescaling** (documents the motivating caveat);
- predictivity ≈ 1 under a per-unit rescaling and under a random invertible map, and ≈ 0 for independent noise;
- **leakage test:** a feature that encodes the episode identity plus a per-episode constant target gives high R² under a row-level split and ≈ 0 under `episode_split`;
- **clock tests:** (a) a target that is an arbitrary nonlinear function of `t` alone gets `R²_clock` ≈ 1; (b) a layer equal to the one-hot of `t` has excess `R² − R²_clock` ≈ 0; (c) a layer equal to the target plus small noise, on a target independent of `t`, has excess > 0 and `R²_clock` ≈ 0; (d) a held-out row at a `t` absent from the training fold is masked for layer and clock alike;
- **bootstrap tests:** the maps are fitted exactly once per repeat (a counting stub); every draw uses the same resampled groups for all agents (paired: the draw-wise difference of two identical agents is exactly 0); groups, not rows, are resampled (a probe with two stores sharing seeds resamples both stores' rows of a seed together);
- **rules — contract:** a manifest whose pinned sha256 differs from the file raises; the pilot policy yields `allowed = false` and the drivers do not call any `evaluate_*`; the interim policy prefixes every word; `require_clean` raises on a dirty fixture file; `b2_wakeup` is accepted, its `label` is returned, and a dirty rules file blocks it like `interim` and `evidence`; a status absent from the rules' `evidence_status` mapping raises;
- **rules — logic:** for every rule, a fixture table (input statistics → expected outcome) covering every outcome branch, the G5-exclusion recount (n = 4 MO_diff pairs), and at least one uncovered combination that must raise. Parameters are a fixture dict marked "test fixture, not the study's rule". **This table is what `experiment-designer` signs at Checkpoint R.2**;
- **rules — no constants in code:** a test walks the syntax trees of `decision_rules.py` **and `wakeup.py`** (Revision 3, T4) and fails on any numeric literal other than 0 and 1;
- **rules — coverage:** against the real rules file, every `parameters:` entry is read by some function (via a recording mapping), and a fixture run that exercises every function reads no missing entry. `wakeup.t_cross` / `lag` count as readers of the `B2` entries `run_wakeup` passes them. There is no exemption list; `remedy.*` is read by `study_reading_A1`.

#### 7. `scripts/analysis/nmn/wandb_history.py` — new

- `resolve_by_tag(tag) -> Path`: scan `wandb/run-*/files/wandb-metadata.json` for `--tag == tag` (the `pilot_readout.find_wandb_by_tag` precedent). **Exactly one** hit is required: zero or several raise, listing them. Never a timestamp glob.
- `read_keys(wandb_dir, keys, allow_truncated) -> dict[key, (episode, value)]`: a general local-binary reader, factored from `pilot_pick.read_history` (which is **not** modified).
- **Episode join (resolved 2026-09-29 by reading the binaries):**
  - *May-replication runs:* each record carrying `loss/grad_norm` also carries `Episode/Number`, `iteration`, `timesteps` and `stage/index`. Use its own `Episode/Number`, and select `01_active` by `stage/index == 0`.
  - *Level-05 runs:* loss records carry `iteration`, `timesteps`, `_step`, but **no** `Episode/Number`. Each is followed by an episode row with the **same `timesteps`** value. So the episode count is the `Episode/Number` of the episode row whose `timesteps` equals the loss record's, compared as floats (the binary writes `374374400` on one and `3.743744e+08` on the other).
  - Unmatched records are counted and reported, never interpolated. The join never converts `iteration` to episodes by arithmetic.
- `wandb_dir_for` is reused through `importlib` (the `survival_tenths.py` precedent).
- **`interval_means(wandb_dir, key, edges, weighting, min_window_n)`**: the per-checkpoint-interval means B2 needs (§B2 points). `weighting` is as in `stage_level`.
- **`stage_level(wandb_dir, stage_index, key, window, min_window_n, weighting) -> (value | None, info)`** (re-review R5). Episode rows of that `stage/index`, in `Episode/Number` order; each row weighted per `weighting` (Revision 3, T2), whose accepted values are the rules' names: `delta_episode_number` (the increase in `Episode/Number` since the previous row; the registered `parameters.common.survival.row_weight`, and the convention of `pilot_readout.Series`, which computes the May verdict) or `window_n` (`Episode/_window_n`; a diagnostic printed beside, never the registered choice). Any other value raises. Rows whose `Episode/_window_n` is below `min_window_n` are skipped. `weighting` is a required argument, which the drivers take from `parameters.common.survival.row_weight` (§Revision 2, point 5). Returns the weighted mean over the last `window` episodes of the stage, or `None` (with the reason in `info`) when the stage is incomplete or has fewer than `window` episodes. `info` records the rows used and skipped. Called for `Episode/Steps` (survival) and `Episode/FoodEaten` (bites). `window` and `min_window_n` are passed in by the caller from `parameters:`; this module holds no default.
- The run's WandB folder is found by `resolve_by_tag(<saved top-level tag: in models/config.yaml>)`; the tag is never taken from a manifest label.

**Tests** (`tests/analysis/test_nmn_stage_level.py`): on a synthetic row list, the weighting, the `min_window_n` skip, the last-`window` cut and the incomplete-stage `None` each give a hand-computed value; marked slow, the Checkpoint 4.6 cross-check against `pilot_readout.py` on the six real May runs.

#### 8. `scripts/analysis/nmn/run_activations.py`, `run_similarity.py`, `run_decoding.py` — new drivers

Each takes `--manifest <yaml>`. Outputs go under `results/analysis/algorithmic_null/<manifest name>/` (JSON + CSV + npz), each with a `manifest.json` recording the git sha, the input manifest, the probe hashes, the package versions, and **`decision_rules: {file, sha256, commit}`**, plus the evidence status and whether verdict words were allowed.

`run_similarity.py` also reads survival and bites through `wandb_history.stage_level` for every run, computes gate G5 per run and the survival difference for the analysed stage (§A3 statistics), and writes both into its driver JSON before evaluating anything. G5 exclusions are applied before any pair set is formed.

**Manifest schema (all keys mandatory; `null` is an explicit value, a missing key is a `ValueError`):**
- `name`, `evidence_status`, `out_root`. `evidence_status` must be a key of the pinned rules file's `evidence_status` mapping (today `pilot`, `interim`, `evidence`, `b2_wakeup`), checked after `decision_rules.load`; the tooling holds no list of its own (Revision 3, T3);
- **`decision_rules: {file, sha256}`** (re-review R1). Written and re-pinned by `experiment-designer` only; the developer never edits it;
- `runs: [{label, path, checkpoints: [final | final:prev | <int> | stage_end:<k> | stage_end:<k>:prev]}]`. Arm, seed and WandB tag are read from each run's saved `models/config.yaml` (top-level `seed:`, `tag:`, `agent.modulation.type`), not from the manifest;
- `probes: [{id, stores: [<store dir>], n_per_store, rows_per_episode, seed}]`. **`n_per_store` is set by `experiment-designer`** and checked against gate G6 at build time (R8);
- `layers: [{key, flatten: none | senses_x_units}]` (must include every `common.verdict_layers` entry of the rules), `comparisons` (`auto` = every pair of runs, or an explicit list);
- **`bootstrap_n`**, set by `experiment-designer`, asserted against G6's minimum at load (R7);
- `probe_split: {seed}` — the number of repeats and the test fraction are rule constants and come from `parameters:`;
- `ridge_alphas`, `min_rows_per_column`, `assert_n_episodes`;
- `tool_checks: {shift_change_rows_max, self_similarity_atol, buffer_index_rel_tol}` — the plan's own abort tolerances that no gate covers, which decide no verdict (a failed check aborts the run). They live in the manifest so that no number sits in a script. (`buffer_index_rel_tol`: Revision 4, R4-4.)
- **Revision 4 keys (developer-owned, mandatory):** `capture_matmul_precision` (only `highest`) and `probes[].store_matmul_precision` (per store: `recorded`, or `highest` / `default` for a store whose manifest records no mode), R4-1; `layers[].keep: every_capture | headline_only` and `headline_capture: {checkpoint, probe} | null`, R4-2. A `:prev` selector is replayed only on the probe its `parameters.A4.drift_pairs` entry names (R4-2).

**Addendum (in-flight Stage 2; Revision 3, T3).** Stage 2 is being implemented against Revision 2, which wrote the enum as `pilot|interim|evidence`. If the Stage 2 code already validates `evidence_status` (for example in a manifest loader used by `probe_set` or `run_activations`), replace that fixed list with the check above and add the `b2_wakeup` case to its test. If Stage 2 does not validate the status, nothing in Stage 2 changes. Nothing else in Stages 0, 1, 2 or 5 is affected by Revision 3.

Removed from the Revision 1 schema: `decision_rules_ref`, `untrained_reference_keys` (R2: the untrained references are `untrained.build` on every ordinary run in `runs`), `t_bin_width` (R6), `probe_split.n_repeats` / `test_frac`, and the runs' `tag` / `log` fields.

**The wake-up manifest** (`algorithmic_null_wakeup.yaml`, written by `experiment-designer`, re-review R3): `name`, `evidence_status`, `out_root`, `decision_rules: {file, sha256}`, `runs` (as above), plus the Stage 4 sampling keys the developer adds (`rollout_episodes`, `rollout_seed_base`, `warmup_iters`). **There is no sparse-measure point-set key** (Revision 3, T1): every measure uses each run's `checkpoints` list, plus step 0 where anchorable, and `run_wakeup` raises if the manifest carries any per-measure point set. Every B2 constant comes from `parameters.B2` of the rules file; any B2 value the manifest also states must equal it.

**Who writes what.** The four manifests are `algorithmic_null_pilot.yaml`, `algorithmic_null_mayrep_interim.yaml`, `algorithmic_null_mayrep.yaml` and `algorithmic_null_wakeup.yaml`, all in `docs/experiments/active/modulator_clues/`. `experiment-designer` owns `decision_rules`, `evidence_status`, `runs` (including the `:prev` checkpoints in the evidence manifest), `n_per_store` and `bootstrap_n`. The developer adds the remaining keys listed above, leaving every designer-owned key byte-identical, and `experiment-designer` reviews the result. The precedent is `docs/experiments/active/level05_body_interactions/analysis_manifest.yaml`, and the `_req` / `load_manifest` pattern of `scripts/analysis/studies/level05_body_interactions/_common.py`.

#### 9. Figure scripts — new, `scripts/analysis/studies/modulator_clues/an0N_*.py`

One script per figure: `an01_similarity_layers` (A1, CKA and predictivity per layer pair), `an02_decoding_profiles` (A2, with the time baseline and excess-over-clock for `steps_remaining`), `an03_seed_yardstick` (A3 triangle), `an04_across_worlds` (A4), `an05_wakeup` (B2: four measures plus survival, step-0 point, wake and plateau marked, both definitions and the guard's reason), `an06_freeze_over_training` (B2 freeze subset). Each script:
- calls `house.apply()` first and sets no colour or font of its own;
- saves via `house.save(fig, "docs/experiments/active/modulator_clues/figures/algorithmic_null/<stem>")`. The page has **its own subfolder** (finding 7); the other page's 111 files in `figures/` are never read, listed or touched;
- writes `<stem>.data.txt`: used / available / % per subset, with a reason, **computed from the driver outputs**. Examples: probe rows used per store; predator-distance rows kept vs rows in episodes with no predator; truncated episodes excluded from the `steps_remaining` headline; checkpoints sampled out of the available ones; wake-up NaN reasons;
- prefixes the data statement with the rules' wording for its evidence status: the status's `label` wherever the rules give one (today `pilot` and `b2_wakeup`), and its `verdict_prefix` on every verdict word wherever the rules give one (today `interim`). Both come from `verdict_policy`, never from a status name in the script (Revision 3, T3);
- writes a `decision_rules: <file> <sha256> @ <commit>` line on every figure, the pilot included;
- draws a verdict word only from the `evaluate_*` result in the driver JSON; when the rules forbid verdict words for the status, it writes "no verdict is drawn" instead.

Scripts before Stage 6 run on pilot, interim or partial manifests. The same scripts rerun on the evidence manifest.

#### 10. `scripts/analysis/studies/modulator_clues/build_algorithmic_null_page.py` — add the §11 figure checks

Copy the figure block from `scripts/analysis/tutorials/loop_graph_engineering/build_page.py` l.101–139:
- one `<figure>` at a time (register F16);
- `<img data-fig>` required; `<svg>`/`<canvas>` inside a figure refused (2.7);
- `<b>Axes.</b>` in the figcaption (11a); a `{{DATA:stem}}` token (11b);
- a `howto` block of 150–250 words (11c);
- a generating script at `HERE/<stem>.py`; png/svg/pdf/data.txt under **`DOC/figures/algorithmic_null/`**; no duplicates; base64 embed.

Four adjustments:
- **Unused-figure check scoped to the page's own subfolder** (finding 7). The builder lists only `figures/algorithmic_null/`, and every file there must be shown. The parent `figures/` is never listed. A test drops a stray `an09_x.png` in the subfolder (refused) and a stray `zz_other.png` in the parent (ignored). No run of the check can be satisfied by deleting the other page's files.
- **Count words excluding the `<p class="eyebrow">…</p>` element**, rather than the loop page's fixed `− 3`. The eyebrow here reads "How it is computed" (4 words), so a fixed offset would miscount.
- **Require that eyebrow text** to be exactly "How it is computed".
- **Pull the house figure viewer** (`<div class="lb fit" id="lb" …</script>`) into a `{{HOUSE_VIEWER}}` token (guide 2.6), next to the existing `{{HOUSE_SCRIPT}}`.

Plus one new check: **decision-rule consistency.** Every figure's `data.txt` must carry a `decision_rules:` line whose sha256 equals the rules file's sha256 at HEAD. A missing line or a mismatch is refused.

Replace the current blanket refusal (l.83–85) with these per-figure checks. Keep the F54, citation and token checks as they are.

The template's text and figure blocks are **content, not tooling**: `experiment-analyzer` adds them when results exist. This plan changes only the builder.

#### 11. `scripts/analysis/nmn/wakeup.py`, `untrained.py`, `grad_probe.py`, `run_wakeup.py` — new

- **`wakeup.py`** (pure numpy): `t_cross(x, m, *, mode, f, sustain, final_k, noise_k, min_noise_points, noise_window_divisor, noise_window_max_fraction, m0=None)` (every keyword required, `noise_window_divisor` included (Revision 3, T4); the noise window per §B2; `wakeup.py` is inside the no-literal test of §6), `lag(t_wake, t_plateau, interval, coincident_max_intervals)` -> Result(t, direction, reason, degenerate, m0, m_final, sigma_delta, window_points)`. The across-worlds reading (binomial `k*`) is `decision_rules.evaluate_B2`, not here. `t` is a float step or `NaN`; `reason` is `None` or a sentence.
  **Tests** (`tests/analysis/test_nmn_wakeup.py`) use synthetic curves over 50 checkpoints (x = 1…50) plus a step-0 anchor, with fixed-seed Gaussian noise σ = 0.01 and **test fixture values** (not read from the rules file) `f = 0.5`, `sustain = 2`, `final_k = 3`, `noise_k = 3`, `min_noise_points = 5`, `noise_window_divisor = 3`, `noise_window_max_fraction = 0.5`. Expected outputs:

  | Curve | `fraction_of_rise` (signed) | `fraction_of_final` (literal) |
  |---|---|---|
  | **clean rise**: logistic 0 → 1, midpoint 20 | `t ∈ [19, 21]`, `rising` | `t ∈ [19, 21]`, not degenerate |
  | **falling**: logistic 1 → 0.2, midpoint 20 | `t ∈ [19, 21]`, `falling` (**not** 0) | `degenerate: true` |
  | **rise-then-return**: 0 → 1 by 20 → back to 0.0 ± noise from 35 | `NaN`, reason "net change within the measure's own noise band" | `degenerate: true` or `NaN` |
  | **flat in noise**: 0.5 + noise throughout | `NaN`, same reason | `degenerate: true` |
  | **initial-value trap**: 0.61 → 1.0, midpoint 20 | `t ∈ [19, 21]` | `t = 0`, `degenerate: true` |
  | **non-monotone rise**: clean rise with a single one-checkpoint spike past threshold at 8 | `t ∈ [19, 21]` (spike rejected by `sustain`) | same |
  | **too few points**: 6 checkpoints plus step 0 (window 6 > 0.5 × 7) | `NaN`, reason "too few points to estimate noise" | — |
  | **no sustained crossing** (rules T5, `872b0e04`): flat 0 through checkpoint 49, then 1.0 at 50 only (net change far outside the noise band) | `NaN`, reason "no sustained crossing" (the last point can never be `t_wake` when `sustain` ≥ 2; must **not** raise) | same |
  | **divisor is read**: the clean rise with `noise_window_divisor = 2` | `window_points` = `max(ceil(51/2), 6)` = 26, which exceeds 0.5 × 51 → `NaN`, "too few points to estimate noise" (shows the keyword, not a typed 3, sets the window) | — |

  Plus `lag` cases (late, early, coincident at exactly the band edge, NaN input) and, in `test_nmn_decision_rules.py`, `evaluate_B2` fixtures: `k*` for `n_def` = 16 and a small `n_def` where no `k` qualifies (→ "undetermined across worlds").

- **`untrained.py`**: `build(run_dir) -> (model, env_params)` along the key chain in §B2. It serves both the B2 step-0 anchor and the A1 untrained reference networks (one per ordinary run, re-review R2). It reads `seed` from the saved top level and cross-checks the `--seed` launch argument; a mismatch raises. The verification harness is `tests/analysis/test_nmn_untrained.py::test_matches_train_py_construction`. It is marked slow, and it runs the trainer's own `main()` up to network construction, as described in §B2. It is run for one ordinary and one modulated run of each study and recorded at Checkpoint 4.4.
- **`grad_probe.py`** (finding 5): at a checkpoint (or at the untrained network):
  - restore `model` **and `optimizer`** strictly from the checkpoint payload. At step 0, use a freshly initialised optimiser built as `train.py` builds it;
  - warm up the environment for `warmup_iters` rollouts without updates, because checkpoints carry no `env_state`;
  - collect one batch with `recurrent_ppo_trainer.collect_trajectories` using the run's own `return_mode`, `num_envs` and `sequence_length`, and build `PPOBatch` **exactly as `train_iteration` does** (l.544–579; reuse the code, do not re-derive it);
  - **(a) per-term split:** on the first update, `nnx.grad` of `policy_loss`, `vf_coef·value_loss` and `ent_coef·entropy_loss` separately, reporting `‖∇_mod‖²`, `‖∇_all‖²` and the share per term;
  - **(b) like-for-like with the log:** on a **throw-away deep copy** of model and optimiser, call the trainer's own `update_step` `K_epochs` times on that batch, exactly as `train_iteration` l.583–586 does, and report the mean of its returned `grad_norm` and `mod_grad_norm`. This is the quantity `train.py` l.1919–1923 logs. The copy is discarded, and the checkpoint on disk is opened read-only.
  - The output states: "(a) is the first update only (ratio = 1, before any in-iteration parameter change) and is biased upward relative to the log; (b) is the log's own definition; the world was re-warmed, not restored."
- **`run_wakeup.py --manifest <wake-up manifest> --measures {plateau,grad_share,grad_probe,update_size,rho,swing,freeze}`**. It loads the manifest with `decision_rules.load` (sha256 check), calls `require_clean` because `b2_wakeup` allows verdict words, asserts that, for every `stage_end:<k>`-bounded run, the checkpoint after the last listed one carries a different saved stage (T8: re-checking only the listed checkpoints cannot catch a lagging boundary); asserts the `wakeup:` values against the rules' `B2` section, and passes every wake-up value to `wakeup.t_cross` explicitly (`wakeup.py` has no defaults). **Grid (Revision 3, T1):** one x grid per run, the manifest's `checkpoints` plus step 0 for anchorable measures; every measure is computed on exactly that grid, asserted per curve, and a manifest carrying any per-measure point set raises. **`--measures plateau`** (CPU, WandB only) computes `t_plateau` for every run and writes the Checkpoint 4.0 table; every GPU measure refuses to start unless that table exists for the same manifest and rules sha256 and has no NaN plateau. It reuses `replay`, `mod_distribution`, `spectral_bound`, `freeze` and `ckpt_io` unchanged, and adds the step-0 point through `untrained.build` for the measures marked in §B2.

#### 12. Spec + launcher

**Spec `configs/trajectory_collection/continual_mayrep_probes.yaml`** — new (authored by `experiment-designer` or the developer; config ownership rules apply):

`name: continual_mayrep_probes`, `algo: rppo`, `out_root: results/trajectories_cw_mayrep`, `episodes: 10000`, `seed_base: 1000000`, `checkpoints: [final, "stage_end:3"]`, `obs_precision: float32`, `device: gpu`, `batch_size: 5000`, `shard_episodes: 5000`, `blocks_per_cell: 2`, `npar: 1`, and six `runs` entries (labels `{ordinary,modulated}_s{42,43,44}`, paths from §C's table).

**Launcher `scripts/analysis/studies/level05_body_interactions/launch_collection.py`** — small change: add `--logs PATH [PATH …]` as a mutually exclusive alternative to `--logs-glob` (exactly one of the two is required). `--logs` requires every listed file to exist and to be non-empty. `finished_runs` reads the listed files instead of globbing. Existing `--logs-glob` behaviour is unchanged. Test: `tests/analysis/test_launch_collection_logs.py` covers a listed file that names a finished run, a missing file (raises), and both flags given (raises).

Launch after Stage 5 with:
```
launch_collection.py configs/trajectory_collection/continual_mayrep_probes.yaml \
  --logs logs/20260929_153606.log logs/20260929_153614.log logs/20260929_153623.log \
         logs/20260929_153632.log logs/20260929_153641.log logs/20260929_153650.log \
  --nodes <live-free>
```

Nodes are chosen from `gpu-status` plus the diary (project rule). Size: about 0.47 GB per store × 12 ≈ 5.6 GB, extrapolated from the level-05 stores' 47 GB per 1 M episodes; the developer records the measured bytes.

The optional Stage 4b uses six one-run specs, `…_stage0end_<label>.yaml`, each with `checkpoints: ["stage_end:0"]` once Stage 5 lands. Before Stage 5, it uses the run's explicit step, read from the last checkpoint whose saved `stage` is 0.

#### 13. `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` — same change (maintenance contract)

Add rows for every new file:
- `teacher_forced.py`, `probe_set.py`, `representation.py`, `decision_rules.py`, `wandb_history.py`, `wakeup.py`, `untrained.py`, `grad_probe.py`, `run_activations.py`, `run_similarity.py`, `run_decoding.py`, `run_wakeup.py`: callers, depth, and `src/` imports. `teacher_forced.py`, `untrained.py` and `grad_probe.py` join `replay.py` as the `nmn/` files that import `src/`. `untrained.py`'s test imports `train` (repo root).
- the six `an0N_*.py` figure scripts.

Also (Revision 4): `rules_pin.py` (already mapped with Stage 2; its callers gain `decision_rules.py` in Stage 3, R4-3), and `run_activations.py` (now imports `float32_matmul_selftest` from `collect_trajectories.py`, R4-1). `untrained.py`'s row gains its import of `src/utils/init_keys.py` (R4-6).

Update the rows for:
- `replay.py` (now imports `scripts.eval.eval_rollout`);
- `collect_trajectories.py` (now imports `eval_rollout` and the stage-reading logic; its `resolve_checkpoint` gains new callers `run_activations.py`, `untrained.py`, `run_wakeup.py`);
- `eval_rollout.py` / `continual_forgetting_matrix.py` (new callers);
- `pilot_pick.py` and `continual_worlds/pilot_readout.py` (precedents factored, not imported by the tools; `pilot_readout.py` is imported by the Checkpoint 4.6 cross-check test, `tests/analysis/test_nmn_stage_level.py`, which is a new caller);
- `launch_collection.py` (new `--logs` flag);
- `build_algorithmic_null_page.py` (now reads `figures/algorithmic_null/` and runs the §11 checks).

Also update `scripts/eval/traj_collect/README.md` (a `stage_end:<k>` selector and continual worlds, one short section).

**Not touched:** `train.py` *(touched in Revision 4, R4-6: the key-chain helper only, value-preserving, jaxpr identical)*, `recurrent_ppo_trainer.py`, `neuromodulator.py`, `ckpt_io.py`, `mod_distribution.py`, `freeze.py`, `spectral_bound.py`, `run_*` legacy drivers, the trajectory-store schema's columns and `SCHEMA_VERSION` (Revision 4 adds three manifest fields only, R4-1), `configs/environment/`, and the level-05 `analysis_manifest.yaml`. No config key is added to any training config, so neither `CONFIG_GUIDE.md` nor `CONFIG_CRITICAL_SETTINGS.md` changes.

#### 14. `scripts/analysis/nmn/rules_pin.py` — added in Stage 2 (Revision 4, R4-3)

The one loader of the pinned rules file: `load(manifest) -> PinnedRules` (whole-file sha256 against the manifest's pin, mismatch raises; returns `rules`, `parameters`, `commit`, `dirty`), `param(parameters, dotted)` (missing entry raises), `evidence_policy(pinned, status)` (a status the rules do not define raises), and, from Revision 4, `require_clean(pinned)`. `decision_rules.py`, `run_activations.py`, `run_similarity.py`, `run_decoding.py` and `run_wakeup.py` read the rules only through it. Tests as in R4-3.

#### 15. `src/utils/init_keys.py` — new; `train.py` and `untrained.py` call it (Revision 4, R4-6)

`trainer_init_keys(seed) -> (key, env_key, init_key)`, today's chain unchanged. `train.py` l.1152–1153 call it, and the four per-algorithm `key, init_key = jax.random.split(key)` lines (l.1207, 1290, 1312, 1342) are removed. `untrained.build` calls it instead of re-deriving. New `tests/utils/test_init_keys.py` (golden keys recorded before the edit for seeds 42–44, plus the source check on `untrained.py`). Checkpoint 1.3's jaxpr hashes are re-run before and after.

### Deferred (not in scope; needs its own approval)

**Trainer logging for future runs.** Two quantities:
- per-term modulator gradient norms (three extra `global_norm` calls on per-term grads, which needs three extra backward passes or `jax.vjp` reuse, so it has a real speed cost);
- per-update ‖Δθ_mod‖/‖θ_mod‖ (cheap: the params before and after the optimiser step are both in scope in `update_step`).

This belongs in a separate plan with a speed measurement. It would make B2's per-update resolution available to the "stronger start" runs of B1. A saved step-0 checkpoint for future runs would also make the untrained anchor a stored fact rather than a reconstruction.

---

## Checkpoints

- [x] **0.1** Strict `load_agent` succeeds for all 32 level-05 runs at their store checkpoints, and for all six May-replication runs at the latest checkpoint. The list is pasted into the Implementation Report. — **Done 2026-09-30 (developer):** 32/32 level-05 runs load strictly at their store checkpoints, and all 32 store/model observation breakdowns are equal; 6/6 May runs load at their latest checkpoint (D = 52). List in the Implementation Report.
- [x] **0.2** The May replication's five stage files: the env sections of `01/03/05_active` are identical to `config.yaml`'s; `02/04_passive` differ only in `environment.entities` (besides `agent`/`tag`/`wandb`). — **Done, with one finding:** env sections of `01/03/05_active` equal `config.yaml`; `02/04_passive` differ only in `environment.entities`. But for the s43 and s44 runs every later stage file also differs in top-level `seed` (42, not 43/44). See Implementation Report, Deviation 1.
- [ ] **R.1** `experiment-designer`'s revised rules file (with `parameters:` and `B2`) and the wake-up manifest are committed, and all four manifests pin the rules file's current sha256. Record the file paths, commit shas and commit times. Record the `generated_utc` of the first `run_similarity` / `run_decoding` output of any manifest and of the first `run_wakeup` output, and show each is **later** than the rules commit. (Verifier checks both from `git log` and the output `manifest.json`.) — **Partly done 2026-09-30 (developer, Stage 3):** first real `run_similarity` output (pilot) generated 2026-09-29T20:33:11Z = 05:33 KST, first `run_decoding` 05:44 KST; the rules commit `872b0e04` is 00:47 KST, so both are later. The `run_wakeup` half belongs to Stage 4.
- [ ] **R.2** `experiment-designer` has read the evaluator's fixture table (`tests/analysis/test_nmn_decision_rules.py`, the "rules — logic" cases) and signed in the Implementation Report that each row is the rules' intended reading. The signature's commit time precedes the first real `run_similarity` / `run_decoding` / `run_wakeup` output. Any row the designer rejects is a rules revision (reason 1 of the rules' `revision_policy`) or a code fix, before any number exists.
- [x] **R4.1** — **Done 2026-09-30 (developer, commit `2d54453d`):** RTX 3090 `highest` 1.376e-7 (passes), `default` 2.628e-4 (fails 1e-5). A planted failure aborts with no output directory. The smoke store's manifest records `highest` / RTX 3090 / 1.376e-7. Mode-change and card-change resumes (edited, and real 3090→4090) are refused with nothing written. The `recorded` replay agrees on 100 % (1,396,946 rows). The GPU worker needed `JAX_PLATFORMS=cuda,cpu` for continual runs (Deviation R4-a). Details in the Implementation Report. *(gates the May collection)* Collector tests of R4-1 and R4-7 pass, including the planted self-test failure and the missing-section raise. On an RTX 3090-class GPU, paste `float32_matmul_selftest("default")` (must exceed `FLOAT32_MATMUL_MAX_REL_ERR`) and `float32_matmul_selftest("highest")` (must not). A one-block smoke collection of one May run, on the card class chosen for the collection, into a throw-away `--out-root`, writes a manifest with `matmul_precision: highest`, a `compute_device_kind` and the self-test value; paste them. The commit sha of this change is recorded; every May store's `collection_git_sha` must be at or after it (checked at 6.1).
- [x] **R4.2** Reader tests of R4-1 pass. The pilot manifest, with its two precision keys unchanged (and the R4-2 keys added), reruns Stage 2 on an Ampere/Ada GPU and reproduces Checkpoint 2.2: 0 disagreements for both agents. — **Done 2026-09-30 (developer):** reader tests pass (`test_nmn_probe_set.py`, `test_nmn_run_activations_manifest.py`, `test_nmn_stage3_drivers.py`). The pilot reran on an RTX 4090 with its two precision keys unchanged: 0 disagreements for both agents (1,302,481 and 1,320,905 rows). Per-capture JSONs carry `stores_device` and `replay_device_kind`.
- [x] **R4.3** Loading a manifest with a verdict layer, `logits` or `value` marked `headline_only` raises. A unit test shows `final:prev` is replayed only on `active` and `stage_end:3:prev` only on `passive`, read from `parameters.A4.drift_pairs`. For the first May manifest, the expected bytes (printed before the first replay) and the measured bytes are pasted. — **Done 2026-09-30 (developer):** `test_a_verdict_layer_marked_headline_only_raises` (rnn.state, logits, value), `test_capture_plan_prev_only_on_its_drift_probe_and_headline_layers_once` (78 captures from the evidence shape). First May manifest (interim): expected 14.182 GB, measured 14.182 GB.
- [x] **R4.4** On the pilot, the chain-assertion JSON carries the per-quarter maximum; paste it. The sampled-vs-full check is per row against `tool_checks.buffer_index_rel_tol`: unplanted, it passes (value pasted); with the kept rows' slots shifted by one step, it fails at ≥ 10× the tolerance (value pasted). — **Done 2026-09-30 (developer):** pilot chain `rnn.state` per quarter 4.9e-6 / 2.4e-6 / 2.8e-6 / 2.1e-6 (ordinary) and 3.7e-6 / 3.7e-6 / 4.6e-6 / 3.1e-6 (modulated); sampled-vs-full per row max 1.18e-5 against 1e-3 (unplanted, passes); planted one-step shift ≥ 0.105 (≥ 100× the tolerance, fails as required).
- [ ] **R4.5** `decision_rules.load is rules_pin.load`; `decision_rules.py` imports neither `hashlib` nor `yaml`; `require_clean(pinned)` raises on a dirty fixture.
- [x] **R4.6** — **Done 2026-09-30 (developer, `18e1e5f0`, `52a671a9`):** golden keys (seeds 42–44, recorded on `a236ccf5`) identical after the edit; `test_nmn_untrained` 4/4 bitwise; 8/8 jaxpr hashes identical (trivially); Checkpoint 4.4 second half 22/22 own-seed closest, shas pasted (two May s44 launch-race mismatches, benign). Golden keys for seeds 42–44 recorded on the pre-edit commit (sha stated) and `tests/utils/test_init_keys.py` passes. `tests/analysis/test_nmn_untrained.py` still passes (bitwise against `train.main()`). Checkpoint 1.3's 8 jaxpr hashes are identical before and after. Checkpoint 4.4's second half is then run on all 22 runs of R4-6, with each run's `wandb-metadata.json` `git.commit` and `provenance.json` `training_git_sha` pasted beside it.
- [x] **1.1** Record the golden parameter hashes on the **unmodified** commit (state its sha) *before* editing the network. — **Done:** recorded on `872b0e04` (network file unmodified) before the edit. Hashes in the Implementation Report and in the test.
- [x] **1.2** `tests/models/test_capture_activations.py` passes. All of `tests/models/` passes. — **Done:** 31 passed in `test_capture_activations.py`. `tests/models/`: 231 passed, 1 failed. The failure (`test_hand_computed_breakdown_matches_the_live_environment`) is an environment-breakdown test that the network edit does not touch.
- [x] **1.3** **Jaxpr identity (the speed gate).** Method, tested on 2026-09-29 on a synthetic 8-input / 16-hidden model: `g, s = nnx.split(model)`; wrap `f(s, x, h) = get_action_and_value_nnx(nnx.merge(g, s), x, h, key, eval_mode=False)` and `L(s, b) = ppo_loss_fn(nnx.merge(g, s), b, 0.2, 0.01, 0.5)[0]`. Hash `str(jax.make_jaxpr(f)(s, x, h))` and `str(jax.make_jaxpr(jax.grad(L))(s, per_env_batch))`, where `per_env_batch` is a `PPOBatch` of one env (`obs (T, D)`, `h_init` unbatched), matching the trainer's `vmap` over envs. Three separate processes gave identical hashes for the ordinary and a four-site FiLM `activation` model, for both functions. For this checkpoint, run it on the real ordinary and t16quad agent blocks, before and after the change; the `diff` must be empty. **Positive control:** a throw-away edit inserting `x = x * 1.0` into `_forward` must change the hash (then revert it), which shows the check can fail. Paste commands and hashes. A 200-iteration timing on one node is optional. — **Done:** 8/8 jaxpr hashes are identical before and after the edit (4 real agent blocks × 2 functions). The planted `x = x * 1.0` changes 8/8, so the check can fail.
- [x] **2.1** Pilot probe built from the pilot manifest's `n_per_store`. Its data counts (episodes per store, **distinct `episode_seed` groups**, rows kept, predator-valid rows, truncated episodes) are printed and saved. The group count meets gate G6 (`n_groups × test_frac ≥` the held-out minimum); a deliberately small `n_per_store` (e.g. 1,000) is shown to raise. The one-pass row-index assertions pass. — **Done:** 10,000 episodes (5,000 per store), 5,000 distinct `episode_seed` groups, 1,000 expected held-out groups against the G6 minimum of 500. A deliberately small probe (20 per store) raises. One-pass row-index assertions pass. Counts in the Implementation Report.
- [x] **2.2** Self-replay agreement = 100% for each agent of the pair on its own store (near-ties within gate G1's allowance, read from `parameters:`). Step-discontinuous alignment on sampled rows = 100%, including on action-change rows. Shift-by-one < 95% overall and < 5% on action-change rows, with both numbers recorded (≥ 95% overall = inconclusive, stop). Cross-agent agreement is recorded. — **Done:** self-replay is 100% on all decision rows for both agents (1,302,481 and 1,320,905 rows; 0 disagreements), but only when the check runs in each store's own matmul mode (Deviation 2). Step-discontinuous alignment is 100% on all sampled rows and on action-change rows. Shift-by-one agreement is 0.5105 / 0.5163 overall and 0.0 on change rows. Cross-agent agreement is recorded.
- [x] **2.3** Chain assertions pass on both real pilot checkpoints for every row of the §4 table that applies. The max deviation per assertion is pasted. — **Done:** every applicable row passes on both real checkpoints (13 keys ordinary, 18 modulated). The largest deviation is 4.93e-6 (`rnn.state`), against G2's 1e-5.
- [x] **3.1** `tests/analysis/test_nmn_representation.py` and `test_nmn_decision_rules.py` pass, including the leakage, clock, bootstrap, sha-mismatch, no-literal and parameter-coverage tests. — **Done 2026-09-30 (developer):** `test_nmn_representation.py` + `test_nmn_draw_stats.py` 34/34, `test_nmn_decision_rules.py` 139/139 (no-literal, coverage, perturbation with the five driver-consumed parameters moved off `READ_NOT_YET_USED`).
- [x] **3.2** Positive and negative controls within gate G4's bounds (input-layer satiation R², shuffled-target R²; values pasted with the bounds read from `parameters:`). Same-agent CKA `isclose(1, atol=tool_checks.self_similarity_atol)`. The pilot's outputs carry `verdict_words_allowed: false` and contain no `evaluate_*` result. — **Done 2026-09-30 (developer, pilot):** input satiation R² 0.9920 against the G4 minimum 0.99; shuffled R² ≤ 0.0168 against the maximum 0.02; same-agent CKA deviation 0.0 against 1e-12. Outputs carry `verdict_words_allowed: false`, `evaluation: null`, and no verdict word (grep 0).
- [x] **3.3** **Shared start on the May replication (rules `A3.precondition_shared_start`; re-review R12).** For each of seeds 42, 43 and 44: `untrained.build` on the May ordinary run and on the May modulated run of that seed gives **identical** main-network parameters (every array, bitwise), and the modulator is the only extra subtree. Six runs, three comparisons, each array count and result pasted. Weights only, CPU; it needs `untrained.py` (Stage 4) and runs before any A3 evaluation. — **Done early (requested), all three seeds:** 27 of 27 main-network arrays are bitwise identical for seeds 42, 43 and 44, and the modulator (33 arrays) is the only extra subtree. `untrained.build` equals `train.main()`'s own construction bitwise on 4 runs.
- [ ] **3.4** Page builds with the pilot figures. The builder **refuses** a deliberately broken copy of the template (missing Axes; a 120-word howto; an inline `<svg>`; a stray file in `figures/algorithmic_null/`; a figure whose `decision_rules` hash differs from HEAD), and **ignores** a stray file in the parent `figures/`. Show the refusals.
- [ ] **4.0** **Survival plateau before any rollout (Revision 3; the third review's open question).** `run_wakeup --measures plateau` on the wake-up manifest, CPU only, for all 19 runs (16 level-05 modulated, 3 May modulated `01_active`). Paste the per-run table: `t_plateau` (checkpoint index and episode), `m₀`, `m_final`, σ_Δ, guard margin `|m_final − m₀| / (noise_k·σ_Δ)`, NaN reason. The w0000 row must reproduce the reviewer's reading (plateau at checkpoint 13); a different value is a disagreement to resolve before going on, not a rounding. **Any NaN plateau stops Stage 4** before the timing gate: the list goes to the user and `experiment-designer`.
- [ ] **4.1** `tests/analysis/test_nmn_wakeup.py` passes with every row of the §11 expected-output table.
- [ ] **4.2** `wandb_history.resolve_by_tag` reproduces §C's six folders. The gradient probe's **(b) full-iteration mean** of `modulator/grad_norm` lies within the 5th–95th percentile of logged values in a ±1-checkpoint window on ≥ 5 checkpoints per run, for ≥ 3 runs. This is a **sanity band**, not a proof of correctness: the world is re-warmed, and the log is one iteration's sample. Also record (a)/(b) side by side.
- [ ] **4.3** `freeze.verify_freeze_equivalence` passes for every run and checkpoint swept.
- [x] **4.4** — **Done 2026-09-30 (developer):** bitwise 4/4 (one ordinary + one modulated per study); own-seed rebuild closest on all 22 runs (cosines in the Implementation Report). Untrained anchor: `test_matches_train_py_construction` passes (bitwise) for one ordinary and one modulated run of each study. For every B2 run, the own-seed reconstruction is closer to the first saved checkpoint than the reconstructions for two other seeds (cosine similarities recorded).
- [ ] **4.6** **Survival and bites cross-check (R5; Revision 3, T2).** For all six May-replication runs, `wandb_history.stage_level` on stage 1 (`stage/index` 0) with `weighting` = the rules' `parameters.common.survival.row_weight` (`delta_episode_number`), read from the pinned file rather than typed into the test, gives `S_1` and bites that equal `pilot_readout.py`'s May-replication readout for the same run to within 1e-9 relative (`tests/analysis/test_nmn_stage_level.py`, marked slow, reads the local binaries). Because the registered weighting is `pilot_readout.Series`'s own, this is a direct equality check. The `window_n`-weighted values are pasted beside them as a diagnostic. The G5 pass/fail and the survival difference in the interim driver JSON are pasted. The same check is repeated on stage 5 after training.
- [x] **4.5** — **Done 2026-09-30 (developer):** RTX 2080 Ti, 26.4 s/point with the per-node compile cache warm → 6.4 GPU-h, ≈ 3.2 h on one 2-GPU node (≈ 3.5–4 h with one compile per world). Decision before the sweep: one node (101), no second node, nothing thinned. Stage 4 timing gate: seconds per item recorded, extrapolated wall-clock stated for the every-checkpoint sweep, and the second-node decision (spread over a second node's GPUs if the extrapolation exceeds 8 h) recorded before the full sweep. No measure is thinned (Revision 3, T1).
- [x] **5.1** Collector tests pass, including fingerprint tests (i)–(iii) and the `:prev` tests. On a real May-replication run, `stage_end:0` and `stage_end:3` resolve to checkpoints whose saved `stage` equals 0 and 3, and the `stage_end:3` world has `detection_range: 0`. After training, `stage_end:3:prev` and `final:prev` resolve to checkpoints with the same saved stage as their successors, and their episode gaps are recorded. — **Partly done:** 7 new collector tests pass. On real runs, `stage_end:0` resolves to saved stage 0 with a stage-1 successor (3 runs), and `stage_end:1` resolves to the `02_passive` world with `detection_range` 0. The `stage_end:3` check waits for the end of training: stage 3 is still running, and the resolver correctly refuses it. **Ordinary runs completed 2026-09-30 (developer):** `stage_end:3` resolves to saved stage 3 (`04_passive`, `detection_range` 0, own `env_fp`) on all three; `stage_end:3:prev` and `final:prev` share their successor's stage, gaps 99,995–100,024 episodes. Modulated runs after training.
- [ ] **6.1** After collection: all 12 stores validate. Each store's world is correct. Every store's manifest records `matmul_precision: highest`, a `compute_device_kind` and a self-test value at or below the constant, with a `collection_git_sha` at or after the R4.1 commit (Revision 4). Self-replay agreement is 100% for all 12, with `store_matmul_precision: recorded`. — **Partly done 2026-09-30 (developer):** 6 of the 12 evidence stores (ordinary × final, stage_end:3) plus the 6 interim stage-0-end stores validate; world, `highest` / RTX 3090 / 1.376e-7 and `collection_git_sha` ≥ `2d54453d` checked on all 12. Self-replay and the modulated 6 pending.
- [x] **6.2** `SCRIPTS_DEPENDENCY_MAP.md` and `traj_collect/README.md` are updated in the same commits as the files they describe. — **Stages 2 and 5 part done:** the map and README were updated in the same commits (`38b13a4f`, `e38a2b2f`).

## Implementation Report

> **Implemented by**: developer (session 96e71c7b)
> **Date**: 2026-09-30
> **Scope**: Stages 0, 1, 2 and 5, plus Checkpoint 3.3, which was requested early. Stages 3 and 4 were **not started**. The plan and the rules file were not edited.

**Summary.** The network has a new switch that returns its internal layer activity, and switching it on changes nothing else. The training program is identical before and after the change. Stored episodes can now be replayed through any agent, and a set of checks shows the captured layers are the right tensors. The trajectory collector now handles continual runs. All the checks the stages require passed. Three findings need a decision; they are listed under Deviations. The pilot outputs are **tool validation only** (the two agents share seed 42; not evidence). No verdict is drawn.

### Files (commits `d7fa3f68`, `38b13a4f`, `e38a2b2f`; all pushed to `v4.0`)

| File | Change | Stage |
|---|---|---|
| `src/models/recurrent_ppo_network.py` | Adds `forward_with_activations` and `_forward(x, h, acts)`; `__call__` delegates with `acts=None`; the two encoder methods gain `acts=None`. `__init__` and `get_action_and_value_nnx` are untouched | 1 |
| `tests/models/test_capture_activations.py` | New, 31 tests: capture equals `__call__` on 8 network shapes (bitwise, max\|Δ\| = 0), no state leak, golden parameter hash, key set, chain reconstruction on synthetic weights, and 4 mislabelled-key cases that must fail | 1, 2 |
| `scripts/eval/traj_collect/collect_trajectories.py` | `resolve_checkpoint_info` handles `final`, `<int>`, `final:prev`, `stage_end:<k>` and `stage_end:<k>:prev`. It is the single selector implementation. `continual_resolved_config` builds the fingerprinted dict. `main` uses the stage world for continual runs | 5 |
| `tests/test_trajectory_collection.py` | 7 new `test_cw_*` tests on a synthetic continual run with a lagging checkpoint and a stale-seed passive stage file | 5 |
| `scripts/eval/traj_collect/README.md` | New section on continual runs and the selectors | 5 |
| `scripts/analysis/nmn/replay.py` | `load_agent` builds a continual checkpoint's own stage world; `LoadedAgent.env_config_path` | 2 (§3) |
| `scripts/analysis/nmn/probe_set.py` | New (§4) | 2 |
| `scripts/analysis/nmn/teacher_forced.py` | New (§4): replay, G1/G3/shift controls, chain assertions | 2 |
| `scripts/analysis/nmn/run_activations.py` | New driver (§8) | 2 |
| `scripts/analysis/nmn/rules_pin.py` | **New, not listed in File Changes.** See Deviation 3 | 2 |
| `scripts/analysis/nmn/untrained.py` | New (§11, brought forward for Checkpoint 3.3) | 3.3 |
| `tests/analysis/test_nmn_probe_set.py`, `tests/analysis/test_nmn_untrained.py` | New. The second is marked `integration`: it runs `train.main()` up to network construction | 2, 3.3 |
| `docs/experiments/active/modulator_clues/algorithmic_null_pilot.yaml` | Developer keys added: `rows_per_episode: 5`, `seed`, `store_matmul_precision`, `out_root`, `capture_matmul_precision`, `assert_n_episodes: 8`, `tool_checks`, `layers`. Designer-owned keys are byte-identical. The Stage 3 keys (`comparisons`, `probe_split`, `ridge_alphas`, `min_rows_per_column`) are **not** added yet | 2 |
| `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` | Rows for the 5 new `nmn/` files; updated rows for `replay.py`, `collect_trajectories.py`, `eval_rollout.py`, `continual_forgetting_matrix.py` | 2, 5 |

### Stage 0 — preflight (no code change; script `tmp/20260930_stage0_preflight.py`, output `tmp/20260930_stage0_preflight.json`)
- **0.1** Strict `load_agent`: 32/32 level-05 runs load at their store checkpoints, and 32/32 store and model breakdowns are equal (58 wide). 6/6 May runs load at their latest checkpoint, which ranged from 2.6 M to 3.9 M episodes at the time; all are 52 wide.
- **0.2** Stage files against `config.yaml`. `stage_00` is identical. `02/04_passive` differ in `agent`, `environment` (only `environment.entities`), `tag` and `wandb`. `03/05_active` differ in `agent`, `tag` and `wandb`. **For s43 and s44, every later stage file also differs in top-level `seed`** (Deviation 1).

### Stage 1 — capture switch
- **1.1 Golden parameter sha256** was recorded on `872b0e04` before the edit, from the real agent blocks with `nnx.Rngs(PRNGKey(0))`:

  | Agent | Arrays | sha256 |
  |---|---|---|
  | level-05 ordinary | 27 | `3923c5b4e558…` |
  | level-05 t16quad | 60 | `b8684a9c68f7…` |
  | May ordinary | 27 | `730b804a65a2…` |
  | May t16quad | 60 | `0b2dc02ab159…` |

  All four are unchanged after the edit. The first two are pinned in the test.
- **1.2** 31/31 pass. `tests/models/`: 231 passed, 1 failed. The failure is `test_modulation_input_slice.py::test_hand_computed_breakdown_matches_the_live_environment` (`Olfaction 25 ≠ 5`, `Visual 13 ≠ 8`). It compares an environment breakdown with hand-written numbers, and the network edit does not touch it. It is **not caused by this change**, but I did not trace its origin; flagged for `bug-curator`.
- **1.3 Jaxpr identity.** Command: `python tmp/20260930_stage1_hashes.py {before,after,planted}`. It applies the plan's method (`nnx.split`, `make_jaxpr` of `get_action_and_value_nnx` and of `grad(ppo_loss_fn)` on a one-environment `PPOBatch`) to the 4 real agent blocks. Before and after: 8/8 hashes identical, for example action `4c7c333e…` and loss gradient `152a94a1…` for level-05 ordinary. The planted `x = x * 1.0` changes 8/8, for example to `2601dd9e…` / `b749a5d2…`; the jaxpr diff shows the inserted `mul bq 1.0`. The edit was reverted by restoring the file (0 `PLANTED` lines remain).
- **Speed check: skipped by proof.** The traced training program is byte-identical, so the compiled program is identical and the training speed cannot change. No SPS run was made.

### Stage 2 — replay and the pilot probe

Command: `run_activations.py --manifest …/algorithmic_null_pilot.yaml --batch-size 2500 --rebuild-probes`, on node 106 GPU 0 (RTX 3090), at commit `e38a2b2f`. The output `manifest.json` records `git_dirty: false`, rules sha256 `4c8508af…` from commit `872b0e04`, and `generated_utc 2026-09-29T16:40:53Z`. Outputs are in `results/analysis/algorithmic_null/algorithmic_null_pilot/`. Every JSON carries the rules' pilot label and "no verdict is drawn"; a grep of the outputs finds no verdict vocabulary. The numbers below are **tool validation — shared seed 42 — not evidence**.

- **2.1 Probe `w0000_pair_final`**
  - 10,000 episodes, 5,000 per store; **5,000 distinct `episode_seed` groups**; 1,000 expected held-out groups against the G6 minimum of 500.
  - 2,623,386 decision rows in total; 48,598 kept (5 per episode).
  - 31,452 kept rows have a valid predator distance.
  - 3,344 episodes are truncated; 3,682 groups contain at least one episode that ended in death.
  - Row-index sha256 `fef0b8f3a49c…`; probe npz is 674 MB.
  - A 20-per-store probe raises at gate G6 (40 groups × 0.2 = 4 held-out groups, against a minimum of 500).
- **2.2 Self-replay** (gate G1, all decision rows, own store, each in its store's matmul mode):

  | | Ordinary | Modulated |
  |---|---|---|
  | Decision rows | 1,302,481 | 1,320,905 |
  | Disagreements | 0 | 0 |
  | Near-tie disagreements | 0 | 0 |
  | Step-discontinuous alignment, all sampled rows | 24,327 / 24,327 | 24,271 / 24,271 |
  | Step-discontinuous alignment, action-change rows | 11,617 / 11,617 | 11,452 / 11,452 |
  | Shift-by-one, all rows with t ≥ 1 (bound: G3's 0.95) | 0.5105 | 0.5163 |
  | Shift-by-one, action-change rows (bound: 0.05) | 0.0 | 0.0 |

  Cross-agent agreement, a recorded statistic: the ordinary agent on the modulated agent's store agrees 0.7164; the modulated agent on the ordinary agent's store agrees 0.7302.
- **2.3 Chain assertions** (8 whole episodes, 4 per store; 2,786 episode steps; tolerance is G2's 1e-5)

  | Key | Ordinary | Modulated |
  |---|---|---|
  | `rnn.state`, `rnn.raw` | 4.93e-6 | 3.95e-6 |
  | `actor.raw`, `critic.raw`, `enc.raw` | ≤ 6.1e-7 | ≤ 6.8e-7 |
  | `logits` | 1.0e-7 | 0 |
  | `value` | 0 | 1.2e-7 |
  | All `.mod`, all `.out`, `enc.uni.raw` | 0 | 0 |

  The sampled-row buffer against a separate full capture differs by at most 6.2e-6 (ordinary) and 8.3e-6 (modulated). The captured-logits argmax and the per-step argmax gathered through the row index agree 1.0.
- **Measured bytes:** activations are 673 MB (ordinary; 13 keys, `.mod` keys absent and reported) and 997 MB (modulated; 18 keys).
  - At 5 rows per episode, a May probe (30,000 episodes) would be about 3 GB per modulated agent and checkpoint.
  - A4's six agents × seven checkpoints × two probes come to roughly 200 GB before any thinning of layers.
  - **Decide before Stage 6** whether A4 keeps every layer or only the verdict layers (the 1152-wide `enc.uni.*` are 70% of the bytes).
- **Same-agent CKA ≈ 1: not done.** It needs `representation.linear_cka`, which is Stage 3 code (§6). It is deferred to Stage 3 rather than written early.

### Checkpoint 3.3 — shared start (script `tmp/20260930_cp33_shared_start.py`, output `tmp/20260930_cp33_shared_start.json`)

| Seed | Saved / launch seed (ordinary, modulated) | Identical main-network arrays | Extra subtree in the modulated agent |
|---|---|---|---|
| 42 | 42/42, 42/42 | **27 / 27** bitwise | `modulator` only (33 arrays) |
| 43 | 43/43, 43/43 | **27 / 27** bitwise | `modulator` only (33 arrays) |
| 44 | 44/44, 44/44 | **27 / 27** bitwise | `modulator` only (33 arrays) |

- **Control 1:** the same architecture built from seed + 100 matches only 15 of the 27 arrays; those 15 are the constant-initialised biases and LayerNorm scales. So the comparison can fail.
- **Control 2:** the `model_key` recipe (the one the rules first pinned) also matches only 15 of 27, so it builds a different network.
- **`untrained.build` equals train.py's own construction** (`tests/analysis/test_nmn_untrained.py`, integration, 4 passed in 111 s). It is bitwise on all arrays for May t1none s43 (27 arrays), May t16quad s44 (60), level-05 w0000 t1none (27) and level-05 w0000 t16quad (60).
- The second half of Checkpoint 4.4 (the reconstruction is closer to the first saved checkpoint than other seeds' reconstructions) was **not** run. It belongs to Stage 4.

### Stage 5 — the collector's handling of continual stages
- **Tests.**
  - All 7 new `test_cw_*` tests pass: `stage_end:k` counts the saved stage, not the boundary (the lagging 310 stays stage 0); T8; `:prev`; non-continual runs; fingerprint (i) equal, (ii) different, (iii) world from the stage file with seed/tag from `config.yaml`; a stage file that differs in `training` raises.
  - The rest of `tests/test_trajectory_collection.py` is unchanged: before the change 26 passed / 33 failed / 8 errors, after it 33 passed (26 + 7) / 33 failed / 8 errors. Every failure and error is `Strict Config: 'sensory.visual_value_mode' is required but missing` on the test's old reference run, the archived-config class at `KNOWN_BUGS.md` l.119.
- **T8.** `stage_end:<k>` requires the next checkpoint to **exist** and to carry a different saved stage. So a stage still in training, and the last stage, are refused (use `final` for the last stage). The resolver is shared, so the analysis drivers inherit this.
- **Real May runs** (`tmp/20260930_stage5_realrun.json`)

  | Run | Selector | Resolved checkpoint | Result |
  |---|---|---|---|
  | s42 ordinary | `stage_end:0` | 1,500,006 | saved stage 0; next checkpoint 1,600,004 is stage 1; env_fp equals `config.yaml`'s |
  | s42 ordinary | `stage_end:0:prev` | 1,400,031 | gap 99,975 episodes |
  | s42 ordinary | `stage_end:1` | 3,000,030 | `02_passive`, `detection_range 0`, new env_fp `c119aee260`; 3,000,030 is past the 3.0 M boundary and still stage 1, a real lagging case |
  | s43 ordinary | `stage_end:0` | 1,500,000 | stage 0 |
  | s43 ordinary | `stage_end:1` | 3,000,016 | passive world, `detection_range 0`; seed kept 43 |
  | s42 modulated | `stage_end:0` | 1,500,011 | stage 0 |

  `stage_end:3` is refused on every run while stage 3 is still training, as intended. **The `stage_end:3` part of Checkpoint 5.1 waits for training to finish.**
- `run_collection.py` passes `stage_end:<k>` through unchanged. It does not validate checkpoint strings, and the worklist separator is `|`, so colons are safe.
- **Stage 5 touched no existing store and nothing of the running May replication.** It only read checkpoints' `stage` fields and config files.

### Deviations and decisions needed
1. **`seed` is exempt from the "other top-level key differs → raise" rule (§5 step 4).** The May s43 and s44 later stage files carry `seed: 42`: the launch `--seed` override reaches only the stage-0 dump. As written, the rule would have refused every later stage of four of the six runs. The plan's step 3 already keeps `seed` from `config.yaml`, so exempting it matches the plan's intent. `continual_resolved_config` keeps the run's own seed; test (iii) covers the stale-seed case. This is also a new saved-config hazard, a sibling of `KNOWN_BUGS.md` l.114, and is **not in the registry**; name `bug-curator` to record it.
2. **Self-replay needs the store's own matmul mode.**
   - The level-05 modulated store was collected on node 106 (RTX 3090, where JAX's default float32 matmul is TF32). A full-float32 replay agrees on only 99.80% of its rows: 22 of 11,074 disagreements, at logit margins up to 0.077, which fails G1. Under TF32 it agrees 100%.
   - The ordinary store (node 101, RTX 2080 Ti, no TF32) is the reverse: 100% in full float32, 99.84% under TF32.
   - I added two developer-owned manifest keys. `probes[].store_matmul_precision` is the collection mode per store, used only for the G1/G3/shift checks. `capture_matmul_precision: highest` is used for every kept activation and for the chain assertions, so all agents' layers are in one mode.
   - Store manifests record `device: gpu` but **not the card**. For the pilot I read the card from the collection worklists.
   - **For the May collection (Stage 6), decide one of:** (a) pin the collection to one card class, (b) collect with `jax_default_matmul_precision=highest`, or (c) extend the store manifest to record the GPU model. Option (c) is a collector change outside this plan. A wrong choice cannot pass silently: it fails G1 loudly.
3. **`scripts/analysis/nmn/rules_pin.py` is a file not listed in File Changes.** Stage 2 must read G1/G2/G3/G6 from the sha-pinned rules before `decision_rules.py` (Stage 3) exists. I split out only the load/pin/`param`/`evidence_policy` half of §6's `decision_rules.load`; it evaluates no rule. The evidence status is validated against the rules' own keys, so `b2_wakeup` is accepted and the Revision 3 T3 addendum is already satisfied. Stage 3's `decision_rules.py` should import `load` from it rather than duplicate it.
4. **The plan text says "`action_next` at `t = T−1` is masked out (there is no next row)".** In the store an episode of length T has T + 1 rows (row T is the terminal state). Row T therefore supplies `action_next` for t = T − 1, and nothing is masked. `tests/analysis/test_nmn_probe_set.py` asserts `action_next[t] == action[t+1]` read independently from the parquet.
5. **The store's `observation_breakdown` is key-sorted JSON**, so the "same names, order, widths" check can compare names and widths only. Order comes from `get_observation_breakdown`, as in `level05_body_interactions/_common.store_layout`.
6. **Margin to the G2 tolerance.** The largest chain deviation (`rnn.state`, 4.9e-6) and the largest sampled-vs-full deviation (8.3e-6) are within 1.2–2× of G2's 1e-5. The cause is float accumulation over up to 500 recurrent steps across two differently batched GPU programs, not an indexing error: every row-index check is exact. Longer or wider May probes may cross 1e-5. If they do, the right response is a rules decision on G2 (a relative tolerance for recurrent tensors), not a code change.

### Not done (by instruction)
- Stage 3: `representation.py`, `decision_rules.py`, the figures, and the same-agent CKA check.
- Stage 4: the wake-up sweep, `wandb_history.py`, `grad_probe.py`, `run_wakeup.py`, and the second half of Checkpoint 4.4.
- No store was collected and no training was touched.
- GPU use: local node 102 GPU 1 (RTX 4090) for about 3 minutes of diagnostics, and node 106 GPU 0 (RTX 3090) for two pilot runs of about 1 minute each. The node-106 use is logged in the diary.

### Known-bug pass
I grepped `KNOWN_BUGS.md` directly.
- l.119 (archived configs no longer load) explains the 33 pre-existing collector test failures.
- l.114 (stale nested seed) is related to Deviation 1, but the stale *top-level* seed in later stage files is new. Name `bug-curator` to record it.
- There is no row on matmul-precision reproducibility of stores (Deviation 2). Name `bug-curator` to record it as a store-provenance hazard.

Implemented by: developer

### Revision 4 — R4-1 (collector side + minimal reader) and R4-7 item 2 (2026-09-30, 02:40–03:10)

**Commit `2d54453d`** (pushed to `v4.0`). Every May store's `collection_git_sha` must be at or after it (Checkpoint 6.1).

**Files.**
- `scripts/eval/traj_collect/collect_trajectories.py`: `FLOAT32_MATMUL_MAX_REL_ERR = 1e-5` with its basis and the CPU reference value (9.13e-7) in the comment; `_matmul_product` (the test seam) and `float32_matmul_selftest(precision)` as specified; `assert_float32_matmul`, which raises `RuntimeError` naming the device. `main()` is now parse, then `with jax.default_matmul_precision("highest"):` self-test, read back `jax.config.jax_default_matmul_precision`, then `_collect(...)` (the old body). No CLI flag. `build_manifest` takes three required kwargs and raises when the mode is not `highest` or the self-test value is above the constant. R4-7: a missing world section now raises `ValueError` naming the section and the stage file.
- `src/utils/trajectory_store.py`: `matmul_precision` and `compute_device_kind` added to `MANIFEST_GUARDED_FIELDS`, with a comment.
- `scripts/eval/traj_collect/collect_worker.sh`: GPU branch `JAX_PLATFORMS=cuda,cpu` (Deviation R4-a). There is no `NVIDIA_TF32_OVERRIDE` (Deviation R4-b).
- `scripts/analysis/nmn/run_activations.py`: `resolve_store_precision(entry, recorded, store)`; entries `recorded | highest | default`; `capture_matmul_precision` accepts only `highest`; the resolved check modes and each store's `compute_device_kind` are written into `manifest.json`. The resolution runs once per probe, before any replay.
- Tests: `tests/test_trajectory_collection.py` (8 `build_manifest` call sites via `_precision_kw()`, plus 9 new tests), new `tests/analysis/test_nmn_run_activations_manifest.py` (10 tests).
- Docs, same commit: `TRAJECTORY_STORE_SCHEMA.md` (guard list, and a manifest-field row that includes the reviewer's sentence that `highest` does not mean identical to training arithmetic), `traj_collect/README.md`, `SCRIPTS_DEPENDENCY_MAP.md` (rows for `collect_worker.sh`, `collect_trajectories.py`, `run_activations.py`). The `run_collection.py` comment was updated.

**Tests.**
- New collector tests: 9/9 pass. They run the real `main()` on CPU on a current-schema May run (s42 ordinary, `stage_end:0`), because the file's reference run no longer loads (KNOWN_BUGS l.141). Covered: the three fields written; an identical resume is a no-op; a resume is refused, with every file unchanged, for a mode edited to `default`, a card edited, and a manifest lacking the fields; a planted 1e-4 relative-noise self-test failure makes `main()` raise with no `--out-root` created; `build_manifest` refuses `default` and an above-constant value; R4-7 (a stage file without `thermal` raises; the companion stage with it resolves).
- Whole file: before 33 passed / 33 failed / 8 errors (`tmp/20260930_r41_tests_baseline.log`); after 42 / 33 / 8 (`tmp/20260930_r41_tests_after.log`). The failing set is identical (`diff` of the two lists is empty), all the pre-existing `visual_value_mode` class. `test_schema_doc_matches_code` passes.
- Reader: `test_nmn_run_activations_manifest.py` 10/10, `test_nmn_probe_set.py` 4/4. The pilot manifest loads unchanged (`[highest, default]`).

**Checkpoint R4.1 on node 106 GPU 0 (RTX 3090).** Script `tmp/20260930_r41_gpu106.sh`, output `tmp/20260930_r41_gpu106.out`.

| Check | Result |
|---|---|
| `float32_matmul_selftest("highest")` | **1.376e-7**, passes (≤ 1e-5) |
| `float32_matmul_selftest("default")` | **2.628e-4**, fails the 1e-5 check, as it must (TF32) |
| Planted self-test failure through `main()` on the 3090 | `RuntimeError` "self-test failed on gpu:NVIDIA GeForce RTX 3090: relative error 2.767e-04 …"; the `--out-root` does not exist afterwards |
| One-block smoke collection: May s42 modulated (`rppo_cw_mayrep_t16quad_s42`), `stage_end:0` = step 1,500,011, 3,000 episodes, through `collect_worker.sh` with `device: gpu` | manifest `matmul_precision: "highest"`, `compute_device_kind: "NVIDIA GeForce RTX 3090"`, `matmul_selftest_max_rel_err: 1.3761e-07`, `device: gpu`, env_fp `373102b903` (the `01_active` world). The store is under `tmp/20260930_r41_smoke/root/`. |
| Resume across a mode change (the store copy's manifest set to `default`) | refused: "matmul_precision: store has 'default', this run wants 'highest'"; nothing written |
| Resume across a card change, edited (manifest says RTX 2080 Ti, run on the 3090) | refused; nothing written |
| Resume across a card change, **real** (the 3090 store resumed on node 102's RTX 4090) | refused: "compute_device_kind: store has 'NVIDIA GeForce RTX 3090', this run wants 'NVIDIA GeForce RTX 4090'"; nothing written (`tmp/20260930_r41_card_real_4090.json`) |
| Identical resume on the 3090 | "0 to do, 1 already complete"; no-op |
| Replay through `teacher_forced` via `run_activations` with `store_matmul_precision: [recorded]` (manifest `tmp/20260930_r41_replay_manifest.yaml`) | check mode resolved to `highest`; G1 self-agreement **1,396,946 / 1,396,946 decision rows (100 %)**, 0 disagreements, 0 near-tie; step-discontinuous alignment 14,833 / 14,833; `failures = []` |

**Speed check** (same 3090, same run, checkpoint, 3,000 episodes and batch; script `tmp/20260930_r41_gpu106_speed.sh`, output `tmp/20260930_r41_gpu106_speed.out`). The "before" is TF32 (`_collect` called outside the context). TF32 gave 73.7 and 74.2 eps/s. The new `highest` path gave 80.3 and 81.9 eps/s. That is **about 9 % faster, not slower**. I did not investigate why. The rollout is not matmul-bound, and the difference is consistent across both pairs.

**Incomplete stores per known root, before merge** (the reviewer's ❓). Script `tmp/20260930_r41_incomplete_stores.py`, output `tmp/20260930_r41_incomplete_stores.json`. It walks each `results/trajectories*` root exactly `<root>/<run>/<ckpt>/<env_fp>/` with one `scandir` per directory; there is no recursive search. Result: 265 stores in 14 roots, and 264 are complete. **One is incomplete:** `results/trajectories_sens/20260826-144838_sens_A_baseline_n114g0/10000063/085a28834a` has 0 of 1 blocks: a manifest-only stub from 2026-08-26 with no precision fields. It can no longer be resumed and must be re-collected into a fresh `--out-root` if anyone needs it. No other store is stranded.

**R4-7 safety check** (the reviewer asked for it by name). Script `tmp/20260930_r47_may_world_sections.py`, output `tmp/20260930_r47_may_world_sections.json`. It resolves the six May runs by the `tag` in their saved `config.yaml`. For each run it checks `config.yaml` and all five `stage_*.yaml`: 36 of 36 files carry all five world sections (`environment`, `sensory`, `body`, `thermal`, `perceptual_noise`), with `_ok: true`.

**Deviations.**
- **R4-a (blocker found and fixed): the GPU worker could not collect any continual checkpoint.**
  - The first smoke run died in every cell with `RuntimeError: Unknown backend cpu`, raised in `continual_forgetting_matrix.read_saved_stage` (`jax.local_devices(backend="cpu")`). The worker's GPU branch exported `JAX_PLATFORMS=cuda`, so the Stage 5 `stage_end:<k>` selector had no CPU backend.
  - Stage 5 was only exercised on CPU, so this was latent. **Every May GPU cell at 08:30 would have failed.**
  - Fix: the worker exports `JAX_PLATFORMS=cuda,cpu`. JAX's default device stays the GPU (the manifest records the 3090). This is `collect_worker.sh`, which the plan listed as unchanged, so it is flagged here. `scripts/analysis/nmn/ckpt_io.py:250` makes the same CPU-backend request; any GPU driver that reaches it needs `cpu` exposed too.
- **R4-b: `NVIDIA_TF32_OVERRIDE=0` was measured and dropped.** On the 3090, `default` gave 2.628e-4 with the variable and without it, so it does not change XLA's matmul mode. Shipping it would have given false assurance.
- **R4-c: the new collector tests use a May run, not the reference fixture.** The plan says "on the existing CPU fixture", but that fixture cannot load (KNOWN_BUGS l.141, several eras of missing keys). The tests skip when the May run is absent.
- **Reader, minimal by instruction.** Not done from the plan's reader list: `probe_set` copying the fields into `store_meta` (`run_activations` reads the store manifest directly instead); the start-up self-test in `run_activations`; and the per-capture JSON device fields. These gate Checkpoint R4.2, not the collection.

**Follow-ups.**
- `bug-curator`: update KNOWN_BUGS l.140 (the precision hazard) to "built at `2d54453d`".
- `bug-curator`: record the `JAX_PLATFORMS=cuda` / CPU-backend coupling (fixed in the worker, still latent in `ckpt_io.py:250` for GPU callers).
- The one incomplete `trajectories_sens` stub (above).

Implemented by: developer

### Stage 4b + Stage 6 (ordinary runs) — May-replication collection (2026-09-30, 04:30–05:05)

**Files** (commit `10915349`, pushed to `v4.0`):
- `scripts/analysis/studies/level05_body_interactions/launch_collection.py`: `--logs PATH [PATH …]`, mutually exclusive with `--logs-glob` (exactly one required, argparse group plus a `log_files()` guard). Each listed file must exist and be non-empty, checked once before any launch. The glob is still re-evaluated on every `--watch` pass. `finished_runs()` now takes the file list.
- `tests/analysis/test_launch_collection_logs.py` (new, 5 passed): a listed log naming a finished run; a missing file raises; an empty file raises; both flags refused (argparse and `log_files`); neither flag refused.
- `configs/trajectory_collection/continual_mayrep_probes.yaml` (new): `checkpoints: [final, "stage_end:3"]`, six runs, labels `{ordinary,modulated}_s{42,43,44}`.
- `configs/trajectory_collection/continual_mayrep_stage0end_<label>.yaml` ×6 (new): `checkpoints: ["stage_end:0"]`, one run each, `nodes: [109]`.
- All seven specs use `out_root: results/trajectories_cw_mayrep`, `episodes: 10000`, `seed_base: 1000000` (no per-run override), `obs_precision: float32`, `device: gpu`, `batch_size: 5000`, `shard_episodes: 5000`, `blocks_per_cell: 2` and `npar: 1`. So each store is one worklist cell on one card.
- `docs/environment/SCRIPTS_DEPENDENCY_MAP.md`: the launcher row, and only that hunk. The file had another session's uncommitted hunks, so only this hunk was staged, through `git apply --cached`.

**Log↔tag check.** Each log's `tag :` line and its `Training complete. Results saved to …` line agree with §C's table: 153606 t1none_s42, 153614 t16quad_s42, 153623 t1none_s43, 153632 t16quad_s43, 153641 t1none_s44 and 153650 t16quad_s44. At launch the three t1none logs ended in "Training complete" and the three t16quad logs did not. The launcher's dry run picked exactly the three ordinary runs.

**Selector resolution on the real runs** (CPU; `tmp/20260930_0435_mayrep_selectors.json`). This completes Checkpoint 5.1 for the ordinary runs.

| run | stage_end:0 (successor, stage) | stage_end:1 | stage_end:2 | stage_end:3:prev (gap) | stage_end:3 (successor, stage) | final:prev (gap) | final (stage) |
|---|---|---|---|---|---|---|---|
| ordinary_s42 | 1500006 (1600004, 1) | 3000030 | 3700014 | 4300014 (99,995) | 4400009 (4500024, 4) | 5000010 (100,008) | 5100018 (4) |
| ordinary_s43 | 1500000 (1600036, 1) | 3000016 | 3700029 | 4300004 (100,020) | 4400024 (4500039, 4) | 5000006 (99,997) | 5100003 (4) |
| ordinary_s44 | 1500018 (1600021, 1) | 3000015 | 3700036 | 4300003 (100,024) | 4400027 (4500020, 4) | 5000006 (100,011) | 5100017 (4) |
| modulated_s42 | 1500011 (1600017, 1) | 3000009 | 3700008 | refused (stage 3 in training) | refused | refused (pair spans stages 2/3) | 3800019 (3, not final) |
| modulated_s43 | 1500012 (1600007, 1) | 3000009 | refused (stage 2 in training) | refused | refused | — | 3700003 (2) |
| modulated_s44 | 1500008 (1600022, 1) | 3000008 | 3700003 | refused | refused | — | 3900004 (3) |

- **T8 passed for all six `stage_end:0`**: each has a successor with saved stage 1.
- For each `:prev` pair, both checkpoints carry the same saved stage.
- On the modulated runs, the resolver correctly refuses every selector whose stage is still in training.

**Launches.** Nodes came from `gpu_status.py`, the diary and a live SSH check (NAS mounted, no Python process). All GPUs were free except 110–112 GPU 1, which is the modulated training and was not used. The collector always lands on GPU 0, so each node contributes one GPU.
- RTX 3090 was chosen because it is the card class R4.1 was verified on, and it is routine mid-tier work.
- **Final capture, ordinary ×3:** `launch_collection.py continual_mayrep_probes.yaml --logs <six logs> --nodes 106 107 108` ran at 04:46 as batch `continual_mayrep_probes_b01` (6 cells). All three nodes were done in 137 s, with no `fail_*` marker.
- **Interim ×6:** the six stage-0-end specs ran one after another through `run_collection.py` on 109:0 (`tmp/20260930_mayrep_interim_chain.sh`). The chain ran 04:47–04:57, every rc was 0, and there was no `fail_*` marker.
- A single store took 31–70 s (143–319 episodes/s).

**Store verification** (`tmp/20260930_mayrep_verify_stores.py` → `.json`). It reads each store's own `_manifest.json` and files, not the spec:

| label | selector | ckpt | saved stage | stage file | env_fp | detection_range | GB |
|---|---|---|---|---|---|---|---|
| ordinary_s42 | stage_end:0 | 1500006 | 0 | 01_active | 3fc70ed8e4 | 5 | 0.693 |
| ordinary_s42 | stage_end:3 | 4400009 | 3 | 04_passive | **c119aee260** | **0** | 0.634 |
| ordinary_s42 | final | 5100018 | 4 | 05_active | 3fc70ed8e4 | 5 | 0.695 |
| ordinary_s43 | stage_end:0 | 1500000 | 0 | 01_active | 24a2b1cbbe | 5 | 0.682 |
| ordinary_s43 | stage_end:3 | 4400024 | 3 | 04_passive | **421a7c0173** | **0** | 0.656 |
| ordinary_s43 | final | 5100003 | 4 | 05_active | 24a2b1cbbe | 5 | 0.699 |
| ordinary_s44 | stage_end:0 | 1500018 | 0 | 01_active | b56f985516 | 5 | 0.695 |
| ordinary_s44 | stage_end:3 | 4400027 | 3 | 04_passive | **cc5d62af56** | **0** | 0.646 |
| ordinary_s44 | final | 5100017 | 4 | 05_active | b56f985516 | 5 | 0.688 |
| modulated_s42 | stage_end:0 | 1500011 | 0 | 01_active | 373102b903 | 5 | 0.698 |
| modulated_s43 | stage_end:0 | 1500012 | 0 | 01_active | 299fd8a879 | 5 | 0.693 |
| modulated_s44 | stage_end:0 | 1500008 | 0 | 01_active | c6ce29da2e | 5 | 0.692 |

Every store passes each of the following checks:
- `validate_store_structure/shapes/draws` pass: 2 blocks and 10,000 episodes, with **5,000 episodes in block 0**.
- The manifest has `matmul_precision: highest`, `compute_device_kind: NVIDIA GeForce RTX 3090` and `matmul_selftest_max_rel_err` 1.376e-7, which is at or below 1e-5.
- `seed_base` is 1000000, `shard_episodes` 5000 and `obs_precision` float32.
- `resolved_env_config.environment` equals the stage file's `environment`.
- `env_fp` equals the one the resolver computed before launch.
- **`collection_git_sha`** is `10915349` (9 stores) or `c0f332b9` (3 interim stores). Both descend from `2d54453d`. `c0f332b9` is another session's commit, landed during the chain. It touches only `scripts/analysis/nmn/`, tests and docs, not the collector or `src/`, so all 12 stores ran identical collector code.
- **Passive stage:** each `stage_end:3` store is in the `04_passive` world (`detection_range` 0) and has its own `env_fp`, different from the same run's active stores. The final store shares `env_fp` with that run's stage-0-end store, as expected: `05_active` equals `config.yaml`.
- `env_fp` differs between runs even in the same world, because it covers the whole resolved config including `seed`/`tag`. This does not matter here, because stores are keyed per run.

**Bytes vs the plan's estimate.** Measured 0.634–0.699 GB per store (active ≈ 0.69, passive ≈ 0.65) against §12's ≈ 0.47 GB, about 35–50 % more. Episodes here are longer per step row (≈ 470–490 step rows per episode). Collected so far: 12 stores, 8.17 GB. Projected for the evidence manifest's 12 stores: ≈ 8.0 GB, not 5.6 GB. The six interim stores total 4.15 GB.

**Speed check.** Skipped. The launcher and spec change cannot affect training or collection runtime; no hot-path code was touched.

**Discrepancies between §12 / Staging and the manifests** (the manifests win):
1. **`episodes: 10000` vs `n_per_store: 5000`.** No conflict found. The manifests require block 0 to hold at least 5,000 episodes and every store of a probe to share `seed_base`. `shard_episodes: 5000` gives exactly 5,000 in block 0 (verified on every store), and a single `seed_base` has no per-run override. §12's 10,000 total was kept. The second block (5,000 episodes, ≈ 0.33 GB per store) is not read by the registered probes. If the designer prefers 5,000 total, it can be deleted without touching block 0.
2. **Collection checkpoints vs the evidence manifest's seven selectors.** The collection specs carry only the two **probe-generating** checkpoints (`final` → `active`, `stage_end:3` → `passive`), as §12 and Stage 6 say ("the `:prev` checkpoints need no stores of their own"). `stage_end:0..2`, `stage_end:3:prev` and `final:prev` are replayed on those probes by `run_activations`. The `:prev` ones are replayed only on their drift-pair probe (R4-2), and that happens in the analysis manifest, not in a collection spec. All seven resolve on the ordinary runs (table above).
3. **Interim `headline_capture`.** R4-2 and its size table say interim = `null`, ≈ 3.5 GB. The interim manifest registers `{checkpoint: "stage_end:0", probe: active_stage0end}` (designer, R.2), which adds ≈ 13 GB of descriptive layers. This does not affect collection. The size table is stale.
4. **Evidence manifest `headline_capture`.** R4-2 prescribes `{final, active}`. The evidence manifest does not carry the key yet, so it will fail to load until the developer adds it (analysis-time, not collection).
5. **Store size:** 0.47 GB estimated vs ≈ 0.69 GB measured (above).
6. **Stage 4b wording** ("one spec per run with an explicit step"). Superseded as §12 allows: the `stage_end:0` selector exists since Stage 5, so the specs use it, not a typed step. It resolves to the steps in the table.

**Operational notes.**
- `run_collection.validate_and_report` validates **every** store under each run's directory, not only its own spec's stores. The final batch's report therefore listed the interim s42 store while it was half-written (1 block). The full re-validation above is the authoritative one.
- The per-cell collector log name is `md5(run + blocks)`. Two checkpoints of the same run on one node would share, and overwrite, one log file. Here LPT put each run's two cells on different nodes, so no log was lost. Latent; flagged for a later fix.
- `results/trajectories_cw_mayrep/_scratch/_batch_specs/continual_mayrep_probes_batches.json` now records the three ordinary runs as claimed. Re-running the same launcher command launches only the modulated runs.

**Waiting (modulated final capture).** Nothing is launched for it. After their training logs end in "Training complete", run:
```
/home/vncuser/miniconda3/envs/grid_world_pain/bin/python \
  scripts/analysis/studies/level05_body_interactions/launch_collection.py \
  configs/trajectory_collection/continual_mayrep_probes.yaml \
  --logs logs/20260929_153606.log logs/20260929_153614.log logs/20260929_153623.log \
         logs/20260929_153632.log logs/20260929_153641.log logs/20260929_153650.log \
  --nodes 106 107 108
```
Run it with `--dry-run` first. Re-check the nodes live. A run not yet finished is simply left for the next invocation.

**Known-bug pass.** `grep -i 'collect|launch_collection|trajector' KNOWN_BUGS.md`: l.140 (matmul-precision provenance; fixed for new stores at `2d54453d`) and l.141 (CUDA-only checkpoint lookup; fixed in the worker) are both handled by this collection. l.142 (red `tests/test_trajectory_collection.py`, old reference run) does not touch the launcher test. No new row. The two operational notes above are candidates for `bug-curator`.

Implemented by: developer

### Stage 4 GPU measures, R4-6 and the CUDA-only checkpoint reader (2026-09-30, 04:05–05:55)

**In plain words.** The wake-up analysis (B2) can now measure, at every saved checkpoint of every run and at the untrained network, how much of each training update reaches the modulator, how fast its weights move, how much its output varies with the situation, how large its gain swing is, and how much survival it costs to freeze it. The full sweep over all 19 runs was started on node 101 at 05:19 after every pre-launch gate passed. The trainer and the analysis now build a run's starting network from one shared key recipe, pinned by golden keys. The checkpoint reader no longer crashes in GPU-only jobs.

**Commits (all pushed to `v4.0`).** `18e1e5f0` R4-6 · `0dc6095e` `ckpt_io` fix + map rows · `52a671a9` Checkpoint 4.4 closeness function · `f3291b93` Stage 4 GPU measures. The `SCRIPTS_DEPENDENCY_MAP.md` rows for `grad_probe.py` / `run_wakeup.py` / `rules_pin.stamp` / the reused modules were written by me but landed inside the parallel Stage 3 commit `c0f332b9` (that commit staged the whole map file); they describe `f3291b93`.

**Files.**
- `src/utils/init_keys.py` (new): `trainer_init_keys(seed) -> (key, env_key, init_key)`, today's chain. `train.py` calls it at the old l.1152–1153; the four per-algorithm `key, init_key = jax.random.split(key)` lines are gone. `untrained.build` calls it (no copied chain). `untrained.py` also gained `closeness_to_first_checkpoint` (Checkpoint 4.4 second half).
- `scripts/analysis/nmn/ckpt_io.py`: `load_params` restores with `ocp.RestoreArgs(restore_type=np.ndarray)`, requesting no JAX device.
- `scripts/analysis/nmn/grad_probe.py` (new): strict restore of model + optimiser for a chosen step (the payload train.py saves); fresh optimiser at step 0; `warmup_iters` rollouts with no update; then the trainer's own `train_iteration` (nnx.jit, config static) on `nnx.clone` copies, with the module's `update_step` wrapped for the probe so the first update also differentiates `policy`, `vf_coef·value`, `ent_coef·entropy`. Reports (a) the first-update per-term shares and (b) the `K_epochs` mean of the trainer's own `grad_norm` / `mod_grad_norm`, with the plan's sanity-band sentence.
- `scripts/analysis/nmn/run_wakeup.py`: the GPU sweep (resumable per-point JSON, `--runs` per worker), `--timing K`, `--summarise`; `rules_pin.stamp` on every output; `JAX_PLATFORMS=cuda,cpu` required for GPU measures (the T8 grid check reads continual stages on the CPU backend).
- `scripts/analysis/nmn/rules_pin.py`: `stamp(pinned)`.
- `docs/experiments/active/modulator_clues/algorithmic_null_wakeup.yaml`: the three developer keys of §8, `rollout_episodes: 128`, `rollout_seed_base: 90000`, `warmup_iters: 8`, with their basis in comments. Designer-owned keys untouched; the file is not sha-pinned.
- Tests: `tests/utils/test_init_keys.py` (new), `tests/analysis/test_nmn_ckpt_io.py` (new), `tests/analysis/test_nmn_grad_probe.py` (new), additions to `test_nmn_run_wakeup.py`, `test_nmn_untrained.py`, `test_nmn_decision_rules.py` (perturbation test).

**What `run_wakeup` measures (one grid per run: the manifest's checkpoints, plus step 0 where anchorable).** Headline curves get the crossing, the lag and the across-worlds reading; every other number is stored in the point files as a descriptive value.

| Curve (headline) | Source | Grid |
|---|---|---|
| `grad_share.total` | log: `(modulator/grad_norm / loss/grad_norm)²` per row, unweighted mean per checkpoint interval | checkpoints |
| `grad_probe.first_update.{policy,value,entropy}` | probe (a) | step 0 + checkpoints |
| `update_size.modulator` | `‖Δθ_mod‖ / ‖θ_mod(prev)‖` between consecutive points; first interval = untrained → checkpoint 1 | checkpoints |
| `rho.<site>` (5 sites) | contextual fraction of the **gain**, 128-episode greedy rollout | step 0 + checkpoints |
| `swing.<site>` (5 sites) | spectral_bound `gamma_swing_mean` | step 0 + checkpoints |
| `freeze.gain`, `freeze.offset` | mean paired survival change, frozen − live, same 128 seeds | step 0 + checkpoints |

Descriptive only: probe (a) total share and (b) full-iteration share, `update_size.main` / `.mod_over_main`, offset rho and swing per site, live survival. The reading per curve is `measure_reading`: the headline mode (`fraction_of_rise`, `B2.f`), the literal mode beside (`B2.literal_f`), and the lag on grid positions (`B2.lag_coincident_max_intervals`); then `decision_rules.evaluate_B2` per headline curve (sign test over the 16 level-05 worlds; the three May seeds only "agree" / "do not agree"). The per-measure point set is refused at load (unchanged), and every curve's x is asserted equal to the run's grid.

**R4-6 evidence (Checkpoint R4.6).**
- Golden keys recorded on `a236ccf5`, before the edit (`train.py` last changed at `89f3cb78`; the recording script `tmp/20260930_r46_golden_keys.py` asserted train.py's own chain text first; output `tmp/20260930_r46_golden_keys_before.json`). After the edit, `trainer_init_keys` gives identical raw `uint32` data (`tests/utils/test_init_keys.py`, 5 passed):

  | seed | key | env_key | init_key |
  |---|---|---|---|
  | 42 | 1012194634, 3152801799 | 2465931498, 255383827 | 1705926158, 899080142 |
  | 43 | 449051237, 3616999620 | 1512537201, 2531556346 | 3471251761, 3587158380 |
  | 44 | 2001052130, 3307961423 | 1637027069, 3739161765 | 1548230112, 2157066771 |

- The test also checks, on the syntax tree (docstrings excluded), that `untrained.py` calls `trainer_init_keys` and no `jax.random.split` / `PRNGKey`, and that `train.py` holds neither old split line.
- `test_nmn_untrained.py::test_matches_train_py_construction` (bitwise against `train.main()`): 4/4 after the edit (27/60/27/60 arrays).
- Checkpoint 1.3 jaxpr hashes (`tmp/20260930_stage1_hashes.py`, outputs `tmp/20260930_stage1_hashes_r46_{before,after}.json`): **8/8 identical** (4 agent blocks × action and loss-gradient programs); the 4 parameter hashes are identical too. As the reviewer said, these are trivially equal because the keys are inputs, not program; the golden keys are the real evidence.
- The six May training runs were not touched. No speed run: the programs are identical.

**Checkpoint 4.4, second half, on all 22 runs** (`tmp/20260930_cp44_closeness.py`, output `tmp/20260930_cp44_closeness.json`). Cosine similarity of the flattened main-network parameters (27 arrays, modulator excluded) to the run's first saved checkpoint, strict load. **Own seed closest in 22/22.**

| run | seed | first ckpt | cos own | cos other | cos other | wandb `git.commit` | provenance `git_sha` |
|---|---|---|---|---|---|---|---|
| cw_mayrep_t1none_s42 | 42 | 100025 | 0.9633 | 43: 0.0608 | 44: 0.0638 | 0ebd09b9 | 0ebd09b9 |
| cw_mayrep_t16quad_s42 | 42 | 100033 | 0.9590 | 43: 0.0606 | 44: 0.0634 | 0ebd09b9 | 0ebd09b9 |
| cw_mayrep_t1none_s43 | 43 | 100069 | 0.9640 | 42: 0.0609 | 44: 0.0628 | 0ebd09b9 | 0ebd09b9 |
| cw_mayrep_t16quad_s43 | 43 | 100034 | 0.9585 | 42: 0.0601 | 44: 0.0628 | 0ebd09b9 | 0ebd09b9 |
| cw_mayrep_t1none_s44 | 44 | 100055 | 0.9634 | 42: 0.0634 | 43: 0.0632 | **6d3d42ec** | **0ebd09b9** |
| cw_mayrep_t16quad_s44 | 44 | 100021 | 0.9616 | 42: 0.0635 | 43: 0.0627 | **c6f33eb3** | **6d3d42ec** |
| l05body_w0000_t16quad | 42 | 200019 | 0.9640 | 43: 0.0514 | 44: 0.0532 | f00f6c61 | f00f6c61 |
| l05body_w0001_t16quad | 42 | 200095 | 0.9613 | 43: 0.0511 | 44: 0.0529 | f00f6c61 | f00f6c61 |
| l05body_w0010_t16quad | 42 | 200091 | 0.9654 | 43: 0.0512 | 44: 0.0530 | f00f6c61 | f00f6c61 |
| l05body_w0011_t16quad | 42 | 200133 | 0.9617 | 43: 0.0507 | 44: 0.0534 | f00f6c61 | f00f6c61 |
| l05body_w0100_t16quad | 42 | 200028 | 0.9604 | 43: 0.0512 | 44: 0.0527 | f00f6c61 | f00f6c61 |
| l05body_w0101_t16quad | 42 | 200281 | 0.9599 | 43: 0.0507 | 44: 0.0530 | f00f6c61 | f00f6c61 |
| l05body_w0110_t16quad | 42 | 200171 | 0.9658 | 43: 0.0516 | 44: 0.0530 | f00f6c61 | f00f6c61 |
| l05body_w0111_t16quad | 42 | 200228 | 0.9679 | 43: 0.0516 | 44: 0.0533 | f00f6c61 | f00f6c61 |
| l05body_w1000_t16quad | 42 | 200103 | 0.9632 | 43: 0.0514 | 44: 0.0532 | f00f6c61 | f00f6c61 |
| l05body_w1001_t16quad | 42 | 200166 | 0.9604 | 43: 0.0512 | 44: 0.0530 | f00f6c61 | f00f6c61 |
| l05body_w1010_t16quad | 42 | 200144 | 0.9643 | 43: 0.0514 | 44: 0.0527 | f00f6c61 | f00f6c61 |
| l05body_w1011_t16quad | 42 | 200258 | 0.9668 | 43: 0.0518 | 44: 0.0528 | f00f6c61 | f00f6c61 |
| l05body_w1100_t16quad | 42 | 200050 | 0.9591 | 43: 0.0508 | 44: 0.0529 | f00f6c61 | f00f6c61 |
| l05body_w1101_t16quad | 42 | 200046 | 0.9633 | 43: 0.0514 | 44: 0.0534 | f00f6c61 | f00f6c61 |
| l05body_w1110_t16quad | 42 | 200209 | 0.9625 | 43: 0.0509 | 44: 0.0532 | f00f6c61 | f00f6c61 |
| l05body_w1111_t16quad | 42 | 200062 | 0.9650 | 43: 0.0511 | 44: 0.0537 | f00f6c61 | f00f6c61 |

The provenance file's key is `git_sha` (the plan says `training_git_sha`, which is the store-manifest name). **Two May s44 runs disagree** (bold). Both were launched at 15:37 while parallel sessions committed `6d3d42ec` (15:37:19) and `c6f33eb3` (15:37:28); `provenance.json` and WandB read HEAD seconds apart. `git diff --stat 0ebd09b9 c6f33eb3 -- train.py src/models/ src/utils/` is empty, so all three commits train identically. Per the reviewer's R4-6 note, recorded and not a stop; the closeness check passes for both.

**`ckpt_io` fix (Known Bugs row "GPU analysis jobs that expose only the CUDA device crash…").** Reproduced first: `JAX_PLATFORMS=cuda` → `RuntimeError: Unknown backend cpu. Available backends are ['cuda']`. After the fix, the 667,543 restored floats (l05 w0000 t16quad @ 200019) are bit-identical to the old CPU read under `cpu`, `cuda` and `cuda,cpu`. Regression test `tests/analysis/test_nmn_ckpt_io.py` makes every device query raise; run against the pre-fix module (HEAD copy in `tmp/20260930_ckptio_prefix/`) it fails with that error, and it passes now. **Still latent elsewhere:** `scripts/eval/continual_forgetting_matrix.read_saved_stage` makes the same CPU request (reached by the `stage_end:<k>` resolver). `run_wakeup` therefore refuses GPU measures unless `cpu` is in `JAX_PLATFORMS`, and the collector worker already exports `cuda,cpu`.

**Timing gate (Checkpoint 4.5)**, one level-05 run (w0000), step 0 + checkpoints 1, 25 and 50, every GPU measure, node 101 GPU 0 (RTX 2080 Ti). Outputs `results/analysis/algorithmic_null/algorithmic_null_wakeup/timing/l05_w0000_modulated.json`; cold-cache copy `tmp/20260930_timing_coldcache.json`.

| Run | Per point (load / weights / rollouts / probe) | Projection, 864 points |
|---|---|---|
| 1. no compile cache | ~115 s steady (probe 61 s, rollouts 30 s) | 27.9 GPU-h → 13.9 h on 2 GPUs |
| 2. per-node compile cache, cold | points 3–4: 2.5 / 0.3 / 7.5 / 17 s | (average skewed by compiles) |
| 3. cache warm | **26.4 s** (2.1 / 0.2 / 6.7 / 15.8 s) | **6.4 GPU-h → 3.2 h on one 2-GPU node** |

A diagnosis with `jax_log_compiles` (`tmp/20260930_wakeup_compile_diag.py`, `logs/20260930_045546.log`) showed the cost was compilation, not compute. Each rollout recompiles about 9 s, because `replay.rollout` builds a fresh `nnx.jit` per call. The probe's `train_iteration` recompiles about 50 s at every new checkpoint, with identical shapes and argument mapping, while a repeat call on the same checkpoint takes 2.3 s. The fix is the collector's own convention: a per-node persistent XLA compile cache (`JAX_COMPILATION_CACHE_DIR=/tmp/jaxcache_wakeup_$NODE`), set in the launcher. It is a performance setting only: identical programs, identical numbers. Each new world still compiles once, about 4 min, adding roughly 40 min per worker. **Decision, recorded before the sweep: one node (101, both GPUs), no second node, nothing thinned.** Expected wall-clock is about 3.5–4 h.

**Sanity on the timed values and on the first finished run** (not a reading; `tmp/20260930_summary_dryrun.{py,log}`):
- Per-term gradients sum to the trainer's own first-update norm within 2.2e-7 relative.
- `freeze.verify_freeze_equivalence` is exact at every point, 51/51 on w0000 (Checkpoint 4.3 so far).
- Probe (b) is inside the logged 5th–95th percentile band (±1 checkpoint) at **46 of 50** w0000 checkpoints (Checkpoint 4.2 needs ≥ 5 per run on ≥ 3 runs).
- The summary path (`grad_share_curve`, `run_curves`, `measure_reading`, `sanity_band`, `evaluate_B2`) runs on real w0000 data. The plateau reproduces checkpoint 13.

**Sweep launched (05:19)** at `f3291b93`, `git_dirty: false`. Node 101, logged in the diary. Script `tmp/20260930_wakeup_sweep.sh` (via `run_command.py`).
- GPU 0 (`logs/20260930_051845.log`): w0000–w0111 + May s42, s43.
- GPU 1 (`logs/20260930_051847.log`): w1000–w1111 + May s44.
- Each worker finished its first run in about 25 min with no error; point files are under `…/algorithmic_null_wakeup/points/<label>/`.
- A CPU pass through every measure on May s42 (step 0 + checkpoint 1) ran clean beforehand. Its CPU timing file was moved to `tmp/20260930_timing_may_s42_cpu_smoke.json`.
- **After both workers print `exit 0`:** `run_wakeup.py --manifest <wake-up manifest> --measures grad_share grad_probe update_size rho swing freeze --summarise` (CPU) writes `curves/`, `b2_reading.{json,csv}` and the Checkpoint 4.2 band per run.

**Tests.**
- Affected files: 187 passed (`test_nmn_decision_rules`, `test_nmn_run_wakeup`, `test_nmn_grad_probe` incl. the real-checkpoint probe, `test_nmn_wakeup`, `test_nmn_ckpt_io`, `test_init_keys`).
- Full `tests/analysis` + `tests/utils`: 332 passed (`tmp/20260930_stage4_tests_full.log`).
- Integration: `test_nmn_untrained` 4/4 + the closeness test.
- The perturbation test now uses `B2.f`, `B2.literal_f` and `B2.lag_coincident_max_intervals` through `run_wakeup.measure_reading`. The three are off `READ_NOT_YET_USED`, which is now empty.

**Deviations and choices for review.**
1. **`update_size` is not anchored.** It measures an interval, so its first value is untrained → checkpoint 1 (what the plan's "anchorable: yes" buys it). Its curve has one point per checkpoint (N = 50 / 15, window 17 / 6, within bounds), and `m0` is that first interval.
2. **Probe `balance_metrics` is always off.** The switch only adds read-only logging fields that the loss never uses. Level-05 saved configs predate the key (`get_mandatory` raised).
3. **The headline curve set is my reading of the rules' "per-site rho and swing, per-term shares, gain/offset freeze"** (plus the plan's total-loss share and update size): gain only for rho and swing, `gamma_swing_mean` for swing (not `_max`), freeze cost = mean paired `frozen − live`. That is 17 curves per run. The offset and other variants are stored, so changing the set needs no GPU rerun. **`experiment-designer` should confirm the set before the summary is read**, because the family size enters the rules' false-positive bound (`noise_k` principle: ~15 families).
4. **Per-node persistent compile cache** in the launcher (above). Not a code change; the collector already uses it.
5. **`PPOConfig` copy.** `grad_probe.PPOConfig` is a field-for-field copy of train.py's, because importing train.py runs its argv pre-parser. A test compares the field list against train.py's syntax tree.
6. **Probe per-term split via a temporary wrapper of `recurrent_ppo_trainer.update_step`**, so the batch is the trainer's own. The coupling (train_iteration resolving `update_step` as a module global) is recorded in the map row.
7. **Sanity-band quantiles `(0.05, 0.95)` are a constant in `run_wakeup`** (`SANITY_Q`), taken from Checkpoint 4.2's text. It is a tool check that decides no reading, so it is not in the rules file.
8. The timing projection formula averages all non-first points, so it overstates while the cache is cold. Run 3 (cache warm) is the number used.

**Not done.** `--summarise` (waits for the sweep); Checkpoint 4.2's run count and 4.3 on all runs (the same); R4.2 / R4.3 / R4.4 (the parallel Stage 3 developer's).

**Known-bug pass.** `grep` of `KNOWN_BUGS.md` for recompile / compile cache / freeze / grad_norm / wake-up / init_key / balance_metrics: no collision (the Dreamer recompile rows are another stack). **For `bug-curator`:**
- (i) the row "GPU analysis jobs that expose only the CUDA device crash…" is **FIXED in `ckpt_io.py` at `0dc6095e`**, with regression test `tests/analysis/test_nmn_ckpt_io.py`. The same CPU request remains in `continual_forgetting_matrix.read_saved_stage`; it is mitigated by `JAX_PLATFORMS=cuda,cpu` in the collector worker and `run_wakeup`, but not fixed.
- (ii) Candidate new row: `replay.rollout` recompiles on every call (a fresh `nnx.jit` per call, about 9 s on a 2080 Ti). It costs time only; the persistent compile cache hides it. Owner `bug-curator` to decide.

Implemented by: developer

### `--summarise` reads the registered B2 headline family; the compile cache is recorded (2026-09-30, while the sweep runs)

**In plain words.** `experiment-designer` registered which 17 curves per run get the headline wake-up reading (manifest key `b2_headline_curves`, commit `322a5966`), together with a warning: a single run's wake point can come from noise alone more often than the rules intended. This change makes the summary step use that registered list and refuse to run if its own list, or any run's set of modulated layers, differs from it. Every per-run wake point is now written as numbers only, with the warning beside it in words. The sweep also now logs whether the compile cache that made it fast is switched on, and the exact launch settings are recorded below, because they existed only in a throw-away launcher script.

**Changes (`scripts/analysis/nmn/run_wakeup.py`, `tests/analysis/test_nmn_run_wakeup.py`).**
1. `b2_headline_curves` is a known top-level manifest key. When present, it must be a non-empty list of distinct names, otherwise `load_manifest` raises. `--summarise` requires it through `_req`, so a manifest without it raises there.
2. `--summarise` reads the registered list. For each run, `check_headline_set` compares the curves the code marks as headline with the list and raises on any difference in names or count. The sites are part of the names (`rho.<site>`, `swing.<site>`), so they are covered too. The code's own set still decides which curves are computed as headline. The registration is a check against it, not a replacement for it.
3. `registered_sites` takes the sites from the list's `rho.*` and `swing.*` entries, which must match each other. `check_sites` raises if a run's enabled FiLM sites, read from its saved agent config (`run_sites` → `spectral_bound.enabled_sites`), differ from them. All 19 runs are checked **before anything is written**, and each run's curves are then built from its own sites.
4. **The registered consequence, in the output.** `PER_RUN_CAVEAT` states that no single run's wake point counts as evidence that a measure changed, with the false-pass rate per curve: 0.26 % on level-05 and 1.8 % on May, about 1–4 expected false wake points across 323 curves. It also states that only the sign test across the 16 level-05 worlds carries a reading, and that the May seeds stay descriptive.
   - Every per-run wake point (`curves/<label>.json` → `wake_points`, `b2_reading.json` → `per_run_wake_points`, which replaces `per_run_lag`) carries that caveat.
   - It carries the crossings and the lag as numbers only: lag in episodes, `pos_wake`, `pos_plateau`, `delta_positions`.
   - The per-run `late` / `early` / `coincident` word is **not written**. It is still computed internally, and only feeds `evaluate_B2`.
   - The across-worlds reading keeps its words. Each measure's entry gains `may_status: "descriptive …"`, and the document gains `headline_curves` and `per_run_caveat`.
   - `b2_reading.csv` is unchanged.
5. `compile_cache_status()` reads `jax.config` (cache dir, min entry size, min compile time, and entries at start). The GPU sweep and `--timing` print it and write it into their stamp (`_done.json`, `timing/<label>.json`).

**Launch command and environment of the running sweep** (read on 2026-09-30 from `/proc/<pid>/{cmdline,environ}` on node 101, pids 1576024/1576030 for GPU 0 and 1576069/1576075 for GPU 1; read-only, the processes were not touched). The launcher is `tmp/20260930_wakeup_sweep.sh`, which is gitignored, so its content is reproduced here:
```bash
# via run_command.py, one worker per GPU (GPU and RUNS set in the command's environment):
./run_command.py 101 "GPU=0 RUNS='l05_w0000_modulated l05_w0001_modulated l05_w0010_modulated l05_w0011_modulated l05_w0100_modulated l05_w0101_modulated l05_w0110_modulated l05_w0111_modulated mayrep_modulated_s42 mayrep_modulated_s43' bash /media/nas01/projects/Interoceptive-AI/grid_world_pain/tmp/20260930_wakeup_sweep.sh"
./run_command.py 101 "GPU=1 RUNS='l05_w1000_modulated l05_w1001_modulated l05_w1010_modulated l05_w1011_modulated l05_w1100_modulated l05_w1101_modulated l05_w1110_modulated l05_w1111_modulated mayrep_modulated_s44' bash /media/nas01/projects/Interoceptive-AI/grid_world_pain/tmp/20260930_wakeup_sweep.sh"

# tmp/20260930_wakeup_sweep.sh
cd /media/nas01/projects/Interoceptive-AI/grid_world_pain || exit 1
NODE=$(hostname)                                   # docker-101 on node 101
export CUDA_VISIBLE_DEVICES=${GPU:?}
export JAX_PLATFORMS=cuda,cpu
export XLA_PYTHON_CLIENT_PREALLOCATE=false
export JAX_COMPILATION_CACHE_DIR="/tmp/jaxcache_wakeup_$NODE"   # = /tmp/jaxcache_wakeup_docker-101 (node-local, 19 MB at 06:10)
export JAX_PERSISTENT_CACHE_MIN_ENTRY_SIZE_BYTES=0 JAX_PERSISTENT_CACHE_MIN_COMPILE_TIME_SECS=0
mkdir -p "$JAX_COMPILATION_CACHE_DIR"
git -C . log -1 --format='code at %H %s'
nvidia-smi --query-gpu=index,name --format=csv
/home/vncuser/miniconda3/envs/grid_world_pain/bin/python scripts/analysis/nmn/run_wakeup.py \
  --manifest docs/experiments/active/modulator_clues/algorithmic_null_wakeup.yaml \
  --measures grad_probe update_size rho swing freeze --runs ${RUNS:?}
echo "exit $?"
```
The two `JAX_PERSISTENT_CACHE_MIN_*=0` settings matter. JAX's default minimum compile time is 1 s, and at that default the short rollout programs would not be cached. The running sweep, launched at `f3291b93`, predates `compile_cache_status`, so its `_done.json` files carry no `compile_cache` field. The environment above is the record for it.

**Tests** (synthetic curves only; no real point file, log or checkpoint is read; `--summarise` was **not** run on real data; the sweep's output directory was not touched).
- `JAX_PLATFORMS=cpu pytest tests/analysis/test_nmn_run_wakeup.py tests/analysis/test_nmn_decision_rules.py tests/analysis/test_nmn_wakeup.py` → **185 passed** (12 s). `test_nmn_run_wakeup.py` alone: 20 passed, 7 of them new.
- The new tests drive `summarise` end to end on a synthetic level-05-style run (50 checkpoints) and a May-style run (15), with the real pinned rules, policy and B2 settings. Only the WandB log read, the grad-share curve and the site read are monkeypatched.
  - A headline curve missing from the registered list (`freeze.offset`) raises. An extra one (`freeze.live_survival`) raises. A duplicate name is refused at manifest load.
  - A sixth site on the May run raises before `curves/` exists.
  - The per-run output (both files) carries the caveat on every wake point. It has no `reading` key in the lag, and no string equal to a verdict word (`late`, `early`, `coincident`, `undetermined across worlds`, `agree`, `do not agree`). The caveat itself contains none of those words, and at least one per-run wake point is defined, so the check sees real wake points.
  - `compile_cache_status` reports off, then on with the right directory and entry count.
- Against the pre-change module (HEAD copy in `tmp/20260930_prefix_wakeup/`), 9 tests fail. The first reason is that `load_manifest` refuses the registered manifest, which is item 1 of the request. The old summary also wrote the per-run `late` / `early` / `coincident` word under `readings` and `per_run_lag`.

**Speed check.** Skipped. `--summarise` is a CPU post-processing step, and the only change on the sweep path is one `jax.config` read plus one `listdir` per worker start, nothing per point.

**Deviations / notes for review.**
- `per_run_lag` in `b2_reading.json` is renamed `per_run_wake_points`, and `readings` in `curves/<label>.json` is renamed `wake_points`. No other code reads either (grep of `scripts/`, `src/`, `tests/`).
- The caveat's numbers (0.26 %, 1.8 %, 323, 1–4) are copied from the manifest's comment block. They are not a machine-readable key, so a change there must be mirrored in `PER_RUN_CAVEAT` by hand.
- Known-bug pass: `KNOWN_BUGS.md` row "The teacher-forced replay recompiles on every rollout…" says the cache is "not present in `run_wakeup.py` at `e956d3a5`". It is still set by the launcher, not by `run_wakeup`, but it is now logged and stamped, and the launch settings are recorded above. **For `bug-curator`:** update that row's workaround note to point here.

Implemented by: developer

### Stage 4 code-review items (2026-09-30, while the sweep runs)

**In plain words.** The code review of the Stage 4 code kept the running sweep, and asked for five small fixes. This section records them. Each point file now names the code version, evidence status and GPU that produced it. The "uncommitted changes" flag now also watches the trainer and `train.py`. The first sanity-band window starts where logging starts. The gradient probe refuses a model without a modulator. The checkpoint-reader test now proves the fixed reader returns the same bytes as the old one.

1. 🟡 **Provenance in every point record.** `sweep_run` takes `prov` (`PROVENANCE_KEYS` = `git_sha`, `git_dirty`, `evidence_status`, `device`) and writes it into each point record. Writing a point without it raises. Resuming a point that was written at another code sha also raises.
   - New back-fill script `scripts/analysis/nmn/backfill_point_provenance.py` copies those fields from each run's `_done.json` into point files that lack them, and adds `provenance_backfilled`.
   - Metadata only: every other field is checked unchanged after each atomic write.
   - It refuses unless **every** run has its `_done.json`, and on a rules-sha or provenance disagreement. The default is a dry run; `--write` writes.
   - **Not run.** At 06:05 the sweep had finished 3 of 19 runs, and neither log shows `exit`. The dry run refuses as designed and lists the 16 runs without `_done.json`.
   - To run after both `logs/20260930_051845.log` and `logs/20260930_051847.log` show `exit 0`:
     `python scripts/analysis/nmn/backfill_point_provenance.py --manifest docs/experiments/active/modulator_clues/algorithmic_null_wakeup.yaml --write`.
   - `SCRIPTS_DEPENDENCY_MAP.md` has a new row for the script.
   - Caveat: a point written by the old code has no `git_sha`, so if a worker were restarted on the new code, the resume check could not catch a code change on it. The back-fill closes that gap once it has run.
2. **`git_dirty`** is now computed over `src/ train.py scripts/analysis/nmn`.
3. 🟢 **`sanity_band`** takes `start`, the episode rows' start counter. `grad_share_curve` now returns it as `info["start_counter"]`, and the first window opens there instead of at 0.
4. 🟢 **`grad_probe._per_term_sq_norms`** raises if the gradient has no `modulator` subtree, using the same key test as the trainer. Its docstring says "modulated runs only". The real-checkpoint probe test still passes, so `in` behaves as expected on `nnx.State`.
5. 🟢 **`test_nmn_ckpt_io.py`** gains a golden sha256 over the flattened leaves: path, dtype, shape and bytes, sorted by path. The value `26fc3f85…74ac` covers 60 leaves and 667,543 floats of l05 w0000 at 200019. It was recorded by running `ckpt_io.py` at `18e1e5f0` (the parent of `0dc6095e`) from a scratch copy on CPU. The current reader gives the same digest.

**The caveat's numbers are still copied from the manifest's comment.** No manifest key holds the per-curve false-pass rates (0.26 % / 1.8 %), the family size (323) or the expected false wake points (1–4), so `--summarise` cannot build `PER_RUN_CAVEAT` from them, and I have not invented a key. **Request for `experiment-designer`:** register these values as a machine-readable key beside `b2_headline_curves`, for example a mapping holding the per-curve false-pass rate for level-05 and for May, the family size and the expected false wake points. `run_wakeup` would then read them with `_req`, assemble the caveat, and check the family size against `len(b2_headline_curves) × len(runs)`.

**Tests** (CPU, synthetic except the gitignored-checkpoint tests):
- `pytest tests/analysis/test_nmn_run_wakeup.py test_nmn_ckpt_io.py test_nmn_decision_rules.py test_nmn_wakeup.py` → **191 passed**.
- `test_nmn_grad_probe.py` → **3 passed** (65 s, including the real-checkpoint probe).
- New tests:
  - a point record carries provenance; a write without it raises; a resume across code shas raises;
  - the back-fill refuses without `_done.json`, copies exactly the provenance and leaves everything else unchanged, is idempotent, and raises on a disagreement;
  - the sanity band's first window opens at the start counter;
  - the `git_dirty` pathspec covers the probe's code;
  - the pre-fix golden digest.

**Speed check.** Skipped. The only sweep-path change is a few more keys in each point JSON.

Implemented by: developer

### The per-run caveat built from `b2_family_bound` (2026-09-30)

**In plain words.** The caveat printed next to every per-run wake point used to carry numbers copied by hand from a manifest comment. `experiment-designer` has since registered those numbers as manifest keys (commit `ecf8fbe6`). The summary now builds the caveat from those keys and refuses to run if the registered family size disagrees with the manifest. This closes the request made in the previous section.

- **Manifest key.** `b2_family_bound` is now an accepted top-level key. `--summarise` requires it.
- **Validation (`check_family_bound`).** It raises unless:
  - every key is present, and each rate is in [0, 1] under a numeric curve-length key;
  - `family_size == len(b2_headline_curves) × len(runs)`, which is 17 × 19 = 323 on the real manifest.
  - It runs before anything is written.
- **The caveat itself.** `family_caveat` replaces the removed `PER_RUN_CAVEAT` constant. Every value in it comes from the keys, except `noise_k`, which is taken from the rules' B2 block, and the level-05 / May run counts, which are counted from the runs themselves.
  - Each per-run wake point quotes the rate registered for its own curve's number of points (51 / 50 / 16 / 15). A curve length with no registered rate raises.
  - The document-level `per_run_caveat` lists every length's rate, and `b2_reading.json` also carries the `b2_family_bound` block itself.
  - No number remains hand-typed in `run_wakeup.py`: a grep for `0.26`, `1.8` and `323` finds nothing.

**Tests.** `pytest tests/analysis/test_nmn_run_wakeup.py test_nmn_ckpt_io.py test_nmn_decision_rules.py test_nmn_wakeup.py` → **195 passed**. New tests:
- the real manifest's bound matches 17 × 19;
- a family size of 322, or 18 runs against 323, raises;
- each length picks its own rate, and a 17-point curve raises;
- changing the manifest's 51-point rate to 0.0421 changes the caveat written by a synthetic `--summarise` run (the per-point caveat and the document-level one), while the May curve keeps its 16-point rate.

The existing end-to-end test now checks each written caveat against the manifest rate for that curve's length.

Implemented by: developer

### Stage 3 drivers, Revision-4 reader items, pilot and interim runs (2026-09-30, 04:10–07:55)

**Summary.** Two new analysis programs now exist. `run_similarity` compares every pair of agents layer by layer, and `run_decoding` reads hunger, injury, predator distance and remaining survival time out of each layer, next to a clock-only baseline. Both run on the level-05 pilot and on the interim May probe. The pilot prints numbers only, under the rules' label "tool validation — the two agents share seed 42; not evidence". A grep of every pilot output finds no verdict word. Every pilot control behaves as the plan requires. On the interim probe, every gate passes except G6 for remaining survival time: 92 % of the probe's episodes reach the step cap, so too few death-ended episodes remain. Every interim verdict word carries the registered prefix "provisional — end of stage 1 of 5". Two findings need a decision; they are under Deviations.

**Commits** (all pushed to `v4.0`): `c0f332b9` (drivers, reader items, tests), `4a611c6d` (R4-4), `ba2035ce` (inner-CV speed-up, interim manifest keys), `e64c84ff` (descriptive layers on their own file), `2acd8cd8` (every written verdict word prefixed; Deviation S3-h).

**Files.**
| File | Change |
|---|---|
| `scripts/analysis/nmn/run_similarity.py` | New. A1: linear CKA and cross-network linear predictivity for every verdict layer and pair. The bootstrap resamples `episode_seed` groups jointly across all agents and pairs. Reference rows are the raw input and each untrained network against the trained agents of its own seed. Descriptive layers (ordinary vs modulated pairs only) are written to `similarity_descriptive.*`, after the verdict output. Where verdict words are allowed, G5 exclusions come first, then `evaluate_A1` and `evaluate_A3`. |
| `scripts/analysis/nmn/run_decoding.py` | New. A2: ridge read-outs, the per-time-step clock, the excess over it, the G4 control inputs and reference rows. Where verdict words are allowed, `evaluate_A2`. |
| `scripts/analysis/nmn/driver_io.py` | New, **not listed in File Changes** (Deviation S3-a). Shared plumbing for both drivers: manifest keys, the rules pin and policy, reading `run_activations` output, the rules' pair sets, gates G1–G3 from the capture reports, the G4 inputs, the survival and G5 block, the A3 shared-start check, output stamps, and the verdict-word guard. |
| `scripts/analysis/nmn/draw_stats.py` | New, **not listed** (Deviation S3-a). Bootstrap draws of CKA and R² computed from per-group sums, tested equal to `representation.*` to 1e-10. |
| `scripts/analysis/nmn/run_activations.py` | Revision-4 reader items, listed below. |
| `scripts/analysis/nmn/probe_set.py` | `store_meta` gains `matmul_precision` and `compute_device_kind` (`None` when absent). `load` refuses a probe built before Revision 4. |
| `scripts/analysis/nmn/teacher_forced.py` | R4-4 per-row buffer check, per-quarter maxima and the planted shift. `SITE_OF` removed (R4-7 item 3). |
| `scripts/analysis/nmn/representation.py` | `fit_ridge`'s inner-CV scoring computed from Gram matrices (Deviation S3-b, flagged for review). |
| `tests/analysis/test_nmn_stage3_drivers.py`, `test_nmn_draw_stats.py`, `nmn_synthetic.py` (new); `test_nmn_decision_rules.py`, `test_nmn_probe_set.py`, `test_nmn_representation.py` (extended) | See Tests. |
| `docs/experiments/active/modulator_clues/algorithmic_null_pilot.yaml`, `algorithmic_null_mayrep_interim.yaml` | Developer-owned keys only; every designer-owned key is byte-identical. See below. |
| `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` | Rows for the 4 new files; updated rows for `probe_set`, `teacher_forced`, `untrained`, `run_activations`, `decision_rules`, `representation`, `wandb_history`. |

**Revision-4 reader items (R4-1, R4-2), done.**
- `probe_set` copies each store's `matmul_precision` and `compute_device_kind` into `store_meta`. `run_activations` resolves `store_matmul_precision` from them.
- `run_activations` runs `collect_trajectories.assert_float32_matmul("highest")` before reading anything. It writes the value and the replay card into `manifest.json`: 1.320e-7 on the RTX 4090, against the limit 1e-5.
- Each capture JSON has a `stores_device` entry per store (check mode, recorded mode, store card) and `replay_device_kind` (Checkpoint R4.2).
- R4-2:
  - `layers[].keep` and `headline_capture` are mandatory.
  - `check_keep` raises if a verdict layer, `logits` or `value` is not `every_capture`.
  - `capture_plan` replays a `:prev` selector only on its `parameters.A4.drift_pairs` probe; a `:prev` selector that no drift pair names raises. `headline_only` layers are kept only at the headline capture.
  - Every ordinary run's untrained network is captured on every probe, with the `every_capture` layers only.
  - Expected and measured bytes are printed.
- Also R4-4 (Deviation S3-c) and R4-7 item 3.

**Parameters the drivers now consume** (moved off `READ_NOT_YET_USED`; the perturbation test now shows each one changes an output of a driver step):
- `gates.G5.stage`: the stage whose S and bites enter G5 (`driver_io.survival_block`).
- `common.survival.window_episodes`: the S_k window (`wandb_history.stage_level` in `survival_block`).
- `A3.survival_stage_by_status.evidence` and `.interim`: the stage of the A3 survival difference.
- `common.split.test_frac`: the probe split (`driver_io.make_splits`).

The other three entries (`B2.f`, `B2.literal_f`, `B2.lag_coincident_max_intervals`) belong to `run_wakeup`, the Stage 4 developer's file. They were not touched here; that developer's uncommitted change to the same test addresses them.

**Manifest keys added** (developer-owned):
- Pilot: `keep` on every layer, `headline_capture: {final, w0000_pair_final}`, `comparisons: auto`, `probe_split: {seed: 20260930, bootstrap_seed: 20260931}`, `min_rows_per_column: 20` and `tool_checks.buffer_index_rel_tol: 1.0e-3`.
- Interim: the six `stage_end:0` store paths, `rows_per_episode: 5`, `seed`, and `store_matmul_precision: [recorded ×6]`, plus the same keys as the pilot.
- `bootstrap_seed` is a key the plan's schema lacks. The bootstrap needs a seed, and a derived one would be a typed number.
- **Not added:** the evidence manifest's keys. They go in when its stores exist; its `headline_capture` should be `{final, active}` (R4-2).

**Tests.**
- `tests/analysis/ -k nmn -m "not integration"`: **290 passed** at `c0f332b9`.
- After the later commits: `test_nmn_stage3_drivers.py` 18/18, `test_nmn_representation.py` + `test_nmn_draw_stats.py` 34/34, `tests/models/test_capture_activations.py` 31/31 (uses `chain_deviations`), `test_nmn_decision_rules.py` 139/139, `test_nmn_probe_set.py` + `test_nmn_run_activations_manifest.py` 15/15.
- End-to-end on synthetic captures against the real pinned rules:
  - **Interim:** G5 from synthetic WandB rows. A1, A2 and A3 are evaluated, and every word starts with the rules' prefix. Every output carries the rules sha256 and commit, the git sha and the status. Every fit reports its penalty and grid-edge flag.
  - **Pilot:** every decision and gate function is monkeypatched to raise, and the drivers still complete. Outputs carry the label and "no verdict is drawn", and grep finds no verdict word.
- R4.3: the capture plan built from the evidence manifest shape gives 78 captures, with `final:prev` only on `active` and `stage_end:3:prev` only on `passive`.
- Controls on synthetic data: satiation decodes from the input at R² > 0.99; shuffled targets stay ≤ 0.02; CKA falls below predictivity under a per-unit gain.

**Dry run on a tiny slice** (tmp only; `tmp/20260930_042912_stage3_slice/`, 150 episodes per pilot store). The harness lowered only the probe build's G6 floor to a fixture value of 5, and the slice manifest used `min_rows_per_column: 5`. The data statement of `similarity.json`:
- `rules` {file, sha256 `4c8508af…`, commit `872b0e04`}, `git_sha`, `git_dirty`, `evidence_status: pilot`, `label` (the rules' pilot label), `verdict_statement: "no verdict is drawn"`.
- `rows` per cell: used / available / %, distinct groups, held-out groups per repeat, refused layers.
- `split` {n_repeats 5, test_frac 0.2, seed}; `bootstrap` {2000 per repeat, 10,000 pooled, interval [0.05, 0.95], seed, unit}.
- `ridge` {fits 380, **fits_at_grid_edge 8**, the list with each fit's penalty and edge, grid 19 values 1e-2…1e7, inner_folds 5}; `statistics` (definitions).

`decoding.json` adds rows per quantity with the reason for each exclusion, held-out rows dropped for lack of a clock value, held-out groups per repeat, and the controls with their G4 bounds. Grep: 0 verdict words.

**Pilot** (`results/analysis/algorithmic_null/algorithmic_null_pilot/`; tool validation, shared seed 42, not evidence; no verdict is drawn)
- **Capture** (node 102 GPU 1, RTX 4090, `4a611c6d`).
  - Checkpoint R4.2 reproduced: self-replay has 0 disagreements for both agents (1,302,481 and 1,320,905 decision rows).
  - Step alignment is 1.0 on all rows and on change rows. Shift-by-one is 0.510 / 0.516 overall and 0.0 on change rows.
  - Chain maximum 4.93e-6. Untrained reference captured.
  - Expected = measured = 1.796 GB.
- **Checkpoint R4.4.**
  - The chain check's `rnn.state` per-quarter maxima are 4.9e-6, 2.4e-6, 2.8e-6, 2.1e-6 (ordinary) and 3.7e-6, 3.7e-6, 4.6e-6, 3.1e-6 (modulated). There is no growth with t.
  - The buffer check grows with t, as predicted: 1.8e-6, 2.0e-6, 8.1e-6, 1.18e-5 (modulated). Its maximum per-row value is 1.18e-5 against the tolerance 1e-3.
  - The planted one-step slot shift gives ≥ 0.105 (untrained) and ≥ 0.46 (trained): over 100× the tolerance.
- **Drivers** (`ba2035ce`, `git_dirty: false`; similarity generated 20:33:11Z = 05:33 KST, decoding 05:44 KST, both after the rules commit, 00:47 KST, and the R.2 signature, 04:08 KST; Checkpoints R.1 and R.2).

  | Control (plan) | Required | Pilot | Behaves? |
  |---|---|---|---|
  | An agent against itself: same-agent CKA | = 1 within 1e-12 | deviation 0.0 on all 5 layers, all 3 agents | yes |
  | Input-layer satiation decode (G4 positive) | ≥ 0.99 | 0.9920 | yes, narrowly |
  | Shuffled targets (G4 negative) | ≤ 0.02 each | satiation 0.0017, injury −0.00004, predator 0.0019, steps remaining 0.0168 | yes; steps remaining is closest to the bound |
  | Groups in both folds | none | none | yes |
  | Untrained weights | informative gate not computable (one ordinary run, no UNTRAINED pair) | untrained vs trained, same seed: CKA 0.04–0.16, predictivity 0.16–0.31. The trained pair: CKA 0.59–0.85, predictivity 0.66–0.76. Untrained layers decode satiation at R² 0.08–0.12, trained 0.39–0.89 | the reference sits far below the trained pair on every layer, as a floor should |
  | G6 held-out groups | ≥ 500 | 1,000 per repeat (A1; satiation, injury); predator 634–669; steps remaining 716–756 | yes |

  Pilot A1 numbers (ordinary vs modulated, seed 42; point [5 %, 95 %]):

  | Layer | CKA | Predictivity (min of both directions) |
  |---|---|---|
  | enc.out | 0.587 [0.580, 0.595] | 0.729 [0.717, 0.741] |
  | rnn.state | 0.825 [0.822, 0.829] | 0.683 [0.676, 0.690] |
  | rnn.out | 0.666 [0.660, 0.672] | 0.692 [0.686, 0.697] |
  | actor.out | 0.666 [0.658, 0.672] | 0.663 [0.651, 0.673] |
  | critic.out | 0.853 [0.847, 0.858] | 0.756 [0.725, 0.776] |

  Internal consistency: the descriptive `rnn.raw~rnn.raw` equals `rnn.state` (GRU output = carry), and `rnn.raw~rnn.mod` equals `rnn.out`. Ridge fits: 410 in similarity, 55 at an edge. None is a verdict-layer or reference fit; all are descriptive, at the lowest penalty (least-squares end). In decoding, 11 of 400 fits are at the lowest edge.
- The pilot `similarity.json` predates `e64c84ff`: its descriptive layers are inline rather than in `similarity_descriptive.json`. The numbers are unaffected.

**Interim** (`results/analysis/algorithmic_null/algorithmic_null_mayrep_interim/`; status interim, every verdict word prefixed "provisional — end of stage 1 of 5"). The final `similarity.json` and `decoding.json` were written at `2acd8cd8` (`git_dirty: false`, generated 21:50:20Z = 06:50 KST). A first run at `e64c84ff` gave identical numbers. The rerun only fixed unprefixed internal word fields (S3-h). A grep of the evaluation finds no verdict word without the prefix, and the CSVs have none at all. `similarity_descriptive.*` (reported only) is still computing in the background at hand-off (about 2.5 h; `tmp/20260930_065020_stage3_interim_similarity_rerun.log`).
- **Capture** (RTX 4090):
  - 9 captures (6 agents at `stage_end:0` plus 3 untrained), all tool checks pass.
  - Self-replay, `recorded` mode = `highest` on all 6 stores (RTX 3090): 0 hard disagreements. There are 0–2 near-tie disagreements per agent in 2.34–2.35 M rows, inside G1's allowance.
  - Alignment 1.0 / 1.0; shift-by-one 0.39–0.50 overall and 0.0 on change rows.
  - Chain maximum 3.2e-6; buffer maximum 3.0e-6; planted shift ≥ 0.063.
  - **Checkpoint R4.3 bytes: expected 14.182 GB, measured 14.182 GB.**
- **Probe:** 30,000 episodes, 5,000 groups, 148,528 kept rows. **27,541 of 30,000 episodes (92 %) are truncated**; only 1,155 groups hold a death-ended episode.
- **Gates:** G1 ✓ G2 ✓ G3 ✓ G4 ✓ (input satiation 0.9922; shuffled ≤ 0.0006, steps remaining −0.072) G5 ✓ (all 6 enter: S_1 464.1–467.6, bites 89.5–90.2; yardstick complete) G6 ✓ bootstrap, and ✓ for every quantity **except `steps_remaining`: 210–238 held-out groups < 500 → "blocked by gate G6"**.
- **A2 (decoding)** — study: **provisional — end of stage 1 of 5: undetermined**.
  - satiation: undetermined. rnn.state is "undetermined at 3 seeds"; the other 4 layers match.
  - injury_level: undetermined, one-layer difference (not counted) at enc.out. Only 1 of 3 ordinary seeds beats the clock there, while all 3 modulated seeds do.
  - nearest_predator_manhattan: undetermined, one-layer difference (not counted) at actor.out (gap −0.045 > spread 0.044).
  - steps_remaining: blocked by gate G6.
- **A1 / A3:** see below.

- **A1 (similarity)** at `stage_end:0` / `active_stage0end`. Gates G1–G6 ✓ for A1 (1,000 held-out groups per repeat), and G5's yardstick is complete (3 + 3 seeds). The informative gate passes on every layer and statistic. **Study verdict: provisional — end of stage 1 of 5: different**. The layers that read different are enc.out, rnn.state, rnn.out and actor.out. critic.out is undetermined at 3 seeds. The remedy is not triggered (1 undetermined layer < 3).

  | Layer | Verdict (prefixed) | Predictivity: OO band [L, U] / MO_diff (6) / MO_diff-mean 90 % | CKA: OO band / MO_diff range | MM qualifier |
  |---|---|---|---|---|
  | enc.out | different | [0.885, 0.895] / 0.836–0.855, all below L / [0.844, 0.852] | [0.922, 0.942] / 0.859–0.891 | yes |
  | rnn.state | different | [0.791, 0.799] / 0.759–0.774, all below L / [0.766, 0.771] | [0.917, 0.923] / 0.880–0.912 | yes |
  | rnn.out | different | [0.791, 0.799] / 0.756–0.765 / [0.757, 0.763] | [0.917, 0.923] / 0.811–0.872 | yes |
  | actor.out | different | [0.772, 0.786] / 0.731–0.758 / [0.743, 0.751] | [0.799, 0.840] / 0.696–0.796 | no |
  | critic.out | undetermined at 3 seeds | [0.845, 0.878] / 0.820–0.858, 2 of 6 below L / [0.832, 0.855] | [0.885, 0.942] / 0.811–0.918 | — |

  The differences are small in size: MO_diff sits about 0.02–0.05 below the OO band in predictivity. They are consistent: all 6 MO_diff pairs fall below L on 4 layers. On rnn.state and rnn.out, the **UNTRAINED band lies above the OO band** (predictivity [0.802, 0.820] vs [0.791, 0.799]). Untrained networks fed the same inputs are more alike than trained ordinary agents are. The registered informative gate tests only overlap, so these statistics count as informative.
- **A3 (seed-yardstick pattern).** Shared start: `untrained.build` gives 27/27 identical main-network arrays for seeds 42, 43 and 44, and `modulator` is the only extra subtree (precondition holds). Survival at stage 1: modulated minus ordinary = +1.79 steps; SE_k 0.83 is floored to 3.6; inside 2 × 3.6 → survival the same. E (the same-seed excess) holds on no layer. **Study reading: provisional — end of stage 1 of 5: (c) different processing, same outcome** (4 of 5 layers; critic.out reads "none of the three patterns (undetermined at 3 seeds)").
- Ridge fits: 1,650, of which 7 are at an edge, all at the lowest penalty and all in reference rows (untrained or input), none in a verdict pair. Same-agent CKA deviation is 0.0 on every layer.
- **Caution for the reader of this interim verdict (not a code defect; for `experiment-designer` / `math-reviewer`).** Held-out R² is variance-weighted over output units. That makes the weighting of units change under a per-unit rescaling of the *predicted* layer, even though each unit's R² does not. §E's "unchanged by any invertible linear map" holds for the predicting side, and for the target side only when prediction is perfect. With imperfect prediction, the modulator's per-unit gains on the modulated agent's `X.mod`-derived layers could move the weighted average. rnn.state is not modulated (D5) and still reads different, so this cannot be the whole story. Whether the registered statistic should be the unweighted mean of per-unit R² is a rules question. I have not computed any alternative.

**Deviations and flags.**
- **S3-a. Two library files not in File Changes.** They are `driver_io.py` and `draw_stats.py`, split out for the same reason as `rules_pin.py`. `draw_stats` exists because the rules' 2,000-draw joint bootstrap, recomputed row by row, would take hours per cell on a May probe. It is tested equal to `representation`'s statistics, which still give every point estimate.
- **S3-b. `representation.fit_ridge` changed (reviewed code).** Each penalty's inner-fold R² is computed as `1 − (‖R‖² − 2⟨Zv'R, c⟩ + ⟨c, Zv'Zv c⟩)/SST`, the same quantity, without forming predictions. New tests show it equals the direct scoring to 1e-9 on tall, wide, collinear, rare-unit and one-output inputs, with the same chosen penalty. One pilot fit went from 2.05 s to 0.67 s. Without it, the interim A1 was about 3 h and the evidence run about 10× that. **Please have `code-reviewer` look at it.**
- **S3-c. R4-4 implemented (not in my brief).** The pilot capture failed on the RTX 4090 at the old G2-held sampled-vs-full check (1.18e-5 > 1e-5), exactly the length-dependent quantity R4-4 moves to a per-row tool check. It is implemented as the reviewed plan specifies: `tool_checks.buffer_index_rel_tol: 1.0e-3`, per-quarter reporting, and a planted shift reported in every capture. The chain assertions are unchanged.
- **S3-d. The primary cell** of an evidence status is read from the rules' `evidence_status.<status>.primary_checkpoint` / `primary_probe_world`. A status without them (interim, pilot) must have exactly one cell, else the driver raises. A1, A2 and A3 verdicts are read only at that cell. Other cells' A1 statistics are computed (for A4) but not evaluated. **A4 is not built.**
- **S3-e. G4 control.** Run on the raw input (symlog of the observation); the "shuffle across episodes" hands each episode's kept-row values to another episode, slot by slot. **Scope choices:** reference rows, descriptive layers for MO pairs only, and untrained-vs-trained references for the same seed only. Descriptive comparisons are point estimates, not bootstrapped.
- **S3-f (finding, needs a decision). The ridge standardisation blows up on rarely active ReLU units.**
  - A unit active on a handful of training rows has a tiny training-fold standard deviation. On held-out rows where it is active, the standardised value is huge.
  - Seen three times: on the 150-episode slice (ordinary `critic.out`: one repeat R² −4,100; 36 dead and 38 < 1 %-active units); on the interim reference row untrained `ordinary_s42` `enc.out` → `steps_remaining` (R² −58.4; 7 % of rows); and as a widened interval on pilot `critic.out`.
  - It hit no verdict-bearing number on the pilot or the interim. It is a property of `representation.fit_ridge`'s standardisation (the rules say A2 is "standardised on the training fold"). A remedy is a tool or rules decision for `senior-developer` / `experiment-designer`, for example a floor on the standardisation scale or excluding near-constant columns. It is not something I changed.
- **S3-g (finding). G6 for `steps_remaining` fails at the interim** because the agents survive to the step cap on 92 % of episodes. This is registered handling ("blocked by gate G6"), not a defect. At the evidence stage, check the final-checkpoint stores' truncation share before relying on this quantity.
- **S3-h (fixed before the final interim outputs).** The evaluator's internal unprefixed word maps (`layer_words`, `pattern_words`, `profile_words`) and the per-statistic `word` fields were first written unprefixed. The drivers now drop the maps, prefix every `word` field, and `guard_prefixed` refuses an unprefixed verdict word. The interim outputs were regenerated.
- **CPU note.** On this shared node, NumPy/BLAS at full thread count stalled (13 min on one layer at ~1,300 % CPU). Runs use `OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=8`.

**GPU use.** Node 102 GPU 1 (RTX 4090, local), about 04:30–05:45, logged in the diary. The 110–112 training runs were not touched.

**Known-bug pass.** `grep -i 'ridge\|standardis\|similarity\|decod\|probe' KNOWN_BUGS.md`: no row. S3-f is a new estimator hazard; name `bug-curator` to record it.

Implemented by: developer

### `--summarise` reads B2 outputs stamped with the pre-revision rules sha, through a verified lineage check (2026-09-30)

**In plain words.** The decision rules were revised (commit `47b91611`, new sha `5ef6f731…`). The revision touches the A1, A2 and G4 rules only. Every B2 point file of the running sweep is stamped with the old sha `4c8508af…`, so `--summarise` would have refused the whole sweep. It now accepts an old-sha file only when the revision says B2 did not change, **and** the tool confirms that claim itself by comparing the old file with the current one.

**Rule (`run_wakeup.rules_lineage`).** A point file stamped with a sha other than the current one is accepted only if all three conditions hold:
- (a) the current rules' **latest** `revisions` entry names that sha as `sha256_before`;
- (b) that entry says `b2_changed: false`, exactly (a missing key is refused);
- (c) the old file is found in the git history of the rules file **by its sha256**, and its `B2`, `parameters.B2` and `evidence_status` are equal to the current ones after a YAML parse.

Otherwise it refuses as before, and the error now names which condition failed. On the real history the check finds commit `872b0e04` and all three sections are identical. It is accepted.

**Addition not in the request: flagged for review.** The plateau table (`plateau.json`) carries the old sha too, and `main` compared it before `--summarise` could run, so `--summarise` would still have refused. I applied the same check to it, **for `--summarise` only**. It also compares `common.survival_level` and `parameters.common.survival`, because the plateau is computed with those. That makes it stricter than the point-file rule, not looser, and both are identical on the real history. The GPU sweep path still refuses any sha mismatch. So **a worker restarted from the current manifest would refuse the existing point files and the plateau table.** Resuming the current sweep that way would need a decision first.

**Output.** `b2_reading.json` gains `rules_lineage`:
- `point_files.<old sha>`: the verification record (revision date, `sections_changed`, `b2_changed`, `old_file_commit`, per-section `identical`, reason), the file count, and the list of accepted files, relative to the output directory;
- `plateau`: the plateau table's verification record, or null when its sha is current.

**Tests.** `pytest tests/analysis/test_nmn_run_wakeup.py test_nmn_ckpt_io.py test_nmn_decision_rules.py test_nmn_wakeup.py` → 199 passed, 2 failed.
- The two failures are `test_nmn_decision_rules::test_parameter_coverage_real_rules` and `::test_every_parameter_is_used_not_merely_read`. They are caused by the revision's new `parameters.common.predictor_columns.min_active_fraction`, which no code reads yet. They fail identically with the previous `run_wakeup.py` (`b9c9ca84`), so they are **not from this change**. The A1 tooling owner has to implement P1.
- New tests, all passing:
  - accepted when all three conditions hold (real git history; the plateau section set too);
  - refused when `b2_changed` is true, or missing;
  - refused when the claim is false. A forged "old" file whose B2 prose differs, or whose `parameters.B2.noise_k` differs, is refused. When only `parameters.common.survival` differs, the points are accepted but the plateau table is refused;
  - refused for an unrelated sha, and for a named sha that is absent from git;
  - a synthetic `--summarise` with old-sha point files succeeds and records all 67 files and the verification. With an unrelated sha it raises.

Implemented by: developer

## Verification Report

> **Verified by**:
> **Date**:

| File | Change | Status | Notes |
|------|--------|:------:|-------|
| | | | |

**Conclusion**:

---

## Feedback from plan-reviewer

**Verdict (2026-09-29): NOT READY** — two Critical findings, both cheap to fix before any code is written. Full table, assumption list and exit conditions in [[plan_algorithmic_null_tooling]] (`docs/reviews/plan_algorithmic_null_tooling.md`).

1. 🔴 **Wake-up definition has silent degenerate cases** (§B2, §11). `fraction_of_rise` reports checkpoint 0 for any measure that *falls* over training, and a noise-driven checkpoint for any measure that ends near where it started; `sustain` cures neither. `m₀` is also the first *saved* checkpoint (200 k / 100 k episodes), not the untrained network. Fix: signed crossing in the direction of change, a minimum-change guard that returns NaN with a reason, an untrained-network anchor for the measures where it is computable, and both degenerate curves in `test_nmn_wakeup.py`.
2. 🔴 **No pre-registered rule for "same computation"** before Stage 3 / 4b figures are seen. `experiment-designer` writes a mandatory `decision_rules` block into the May manifest (threshold against the ordinary–ordinary yardstick, and the refutation outcome in words) before Stage 3 runs.

Moderate: run-time reconstruction assertions on real checkpoints so every captured key is chained to its neighbour (the argmax check cannot see side outputs); a step-discontinuous alignment control (satiation R² is blind to a one-row shift); the gradient probe is not like-for-like with the logged mean-over-updates; the `1536*` WandB glob matches 2 of 6 May runs; the new builder's "unused figures" check collides with the 111 files the other page keeps in the same `figures/`; specify which dict the continual collector fingerprints and test it; make the censored-excluded `steps_remaining` the headline with a `t`-only baseline. Low: paths for the analysis manifest and `_common`, 0/1-based stage naming, group key for the pooled probe, CKA "exactly 1.0", `enc.uni.*` flattening.

— *plan-reviewer, 2026-09-29*

## Response from senior-developer (Revision 1, 2026-09-29)

All fourteen findings are addressed in the body; the per-finding table is §Revision 1 near the top. Three points where the revision departs from the review's suggested fix, each with its reason there:
1. The untrained network's key comes from `train.py:1207`, not `model_key` at `train.py:1153`, which is unused.
2. `stage_end:<k>` is "last checkpoint with saved `stage == k`".
3. Stage files that differ from `config.yaml` outside the world sections raise.

The three open assumptions are closed or budgeted: the `make_jaxpr` capture was run and works (Checkpoint 1.3), the WandB join was read from the binaries (File Changes §7), and Stage 4 has an estimate with a timing gate. The decision thresholds are deliberately **not** written here; `experiment-designer` owns them.

— *senior-developer, 2026-09-29*

## Feedback from plan-reviewer — re-review of Revision 1 + decision rules (2026-09-30)

**Verdict: NOT READY**, for a cheaper reason than before. The first pass's two Criticals are substantively closed, and the plan is right on all four points where it departed from the review (untrained key from `train.py:1207`, rules location, `stage_end:<k>` semantics, fingerprint strictness — the last verified on the s42 stage files). What blocks is that **this plan and the designer's rules file do not describe the same tooling**: the plan's `decision_rules_ref: {path, key} | null` + machine-readable `reads`/`outcomes` contract vs. the manifests' `decision_rules: {file, sha256}` + prose rules (the plan instructs the developer to stop on exactly this); the rules pin the *wrong* untrained-key recipe (the first review's, `split(PRNGKey(seed), 3)`) and need three reference networks, not two arbitrary keys; and the wake-up thresholds (`noise_k`, `sustain`, `min_noise_points`, headline mode) are still in no manifest, with no B2 manifest on file. Moderates: A4's within-stage drift needs `:prev` checkpoints the manifests do not list and a `d_a` the plan does not compute; A3 pattern (c) and gate G5 need survival / food-bite inputs the plan does not produce; A2's clock baseline and excess are defined differently here and in the rules; bootstrap 200 vs ≥ 1,000 over `episode_seed` groups; the pooled probe has only `n_per_store` distinct groups (shared `seed_base`), so `n_per_store ≥ 2500` is needed for gate G6. Full table, owners and exit conditions in [[plan_algorithmic_null_tooling]] §Re-review.

— *plan-reviewer, 2026-09-30*

## Response from senior-developer (Revision 2, 2026-09-30)

All thirteen re-review findings with a plan side are closed in the body; the per-finding table is §Revision 2. The four points the re-review ruled in this plan's favour are kept unchanged. The designer's contract is adopted as the one kept: `decision_rules: {file, sha256}` in every manifest (pilot and wake-up included), the pilot's no-verdict status read from `verdict_words_allowed: false`, rules as prose, logic in code with fixture tests signed off by `experiment-designer` (new Checkpoint R.2), every number from `parameters:`, enforced by a no-literal test and a coverage test. The `decision_rules_ref` design and the `reads`/`outcomes` block are gone.

Four points in the contract cannot be implemented exactly as written, and a fifth is settled but worth knowing; all are handed to `experiment-designer` before any number exists (§Revision 2, "Points in the designer's contract…"): G3 has no near-tie allowance; the clock baseline is undefined at a time step absent from the training fold; `bootstrap_n` per repeat or pooled; any structural count left in prose must become a `parameters:` entry; and survival row weighting, which the committed rules settle as `_window_n` but which differs from the weighting of the code that computes the May verdict (a known, visible difference, not a blocker). Until settled, the evaluator raises on each rather than choosing.

— *senior-developer, 2026-09-30*

## Feedback from plan-reviewer — third review of Revision 2 + rules `c74bea58…` (2026-09-30)

**Verdict: NOT READY for Stage 4 only; Stages 0, 1, 2 and 5 may start now.** The plan and the rules now describe the same tooling: same pinned hash in all four manifests (equal to the file at HEAD), pilot silence read from the rules, three untrained references via `untrained.build`, per-repeat bootstrap, 5,000 episodes per store, `:prev` checkpoints, survival and clock inputs, and every R-item closed on the side that owns it. One new Critical, confined to B2: §B2 samples per-term gradient share and freeze cost at every **fifth** checkpoint before checkpoint 34, so `t_wake` rounds *up to the next multiple of 5* where wake-up actually happens, while the rules' coincidence band is ±1 checkpoint. On w0000 the registered plateau rule lands at checkpoint 13 (measured from the local WandB log), so a coincident measure would read "late" — and in the same direction on all 16 worlds, enough for the sign test. Fix in text: sample densely everywhere, as already planned for May (the budget's own "no thinning" principle says the same). Moderates: §Revision 2 point 5 and §7 still say the rules chose `_window_n` — the committed rules say `delta_episode_number` (which matches `pilot_readout.Series`); the `evidence_status` enum and `require_clean` omit `b2_wakeup`; `noise_window_divisor` and `remedy.*` are rules parameters nothing in the plan reads, and `wakeup.py` sits outside the no-literal test; the "guard passes but no sustained crossing" case is undefined on both sides. Full table, owners and exit conditions in [[plan_algorithmic_null_tooling]] §Third review.

— *plan-reviewer, 2026-09-30*

## Response from senior-developer (Revision 3, 2026-09-30)

All five third-review findings owned by this plan are closed in the body; the per-finding table is §Revision 3. **T1 (Critical):** every B2 measure, on level-05 and the May runs alike, is now sampled at every checkpoint plus step 0 where anchorable. The sparse point set and its manifest key are gone, and `run_wakeup` asserts one grid per run. The budget is re-stated at ≈ 2,600 freeze rollouts and ≈ 860 probes (≈ 10–20 GPU-hours); the timing gate and the second-node rule are unchanged. The review's open question is scheduled as Stage 4's first step: the survival plateau on all 19 runs, CPU only (Checkpoint 4.0), and any NaN plateau stops the sweep. **T2:** point 5, §A3, §B2, §7 and Checkpoint 4.6 use the registered `delta_episode_number`, which equals `pilot_readout.Series`. **T3:** the `evidence_status` enum is the rules' own key set, `require_clean` follows `verdict_words_allowed`, and figures print `label` wherever it exists. **T4:** `noise_window_divisor` is a `t_cross` keyword, `wakeup.py` is under the no-literal test, `remedy.*` is reported by `study_reading_A1` (not exempt), and A4's lists and G5's stage are read from `parameters:`. **T6** was deleted with T1, and **T7** is in 4b's check column.

Stages 0, 1, 2 and 5 are unchanged in substance. The only possible touch on in-flight work is the File Changes §8 addendum, which applies only if Stage 2 code validates `evidence_status`. T5 (the rules' "no sustained crossing" outcome, then its fixture row) and T8 (the stage-boundary assertion in `run_wakeup`) belong to `experiment-designer` and `developer`.

— *senior-developer, 2026-09-30*

## Feedback from plan-reviewer — confirmation of Revision 3 + rules `4c8508af…` (2026-09-30)

**Verdict: Stage 4 may start once its prerequisites exist.** Checked against the files at HEAD (`2327141a`, `872b0e04`, `bd3d1f65`), not against the Revision 3 table. T1–T4, T6, T7 closed in the plan body; T5 closed on the rules side (text at rules l.645–647 and l.658, revision entry `T5_no_sustained_crossing`); the May design §5 note is in (`MAY_DOUBLE_RETURN_REPLICATION.md:362-369`); the rules hash `4c8508af…` recomputes at HEAD and is pinned in all four manifests. No Critical, so no review file and no diary row.

Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run · 🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

| # | State | Where verified | Residue |
|---|---|---|---|
| T1 | closed | §B2 "Sampling: every checkpoint" (level-05 N = 51 / 50, May N = 16 / 15); Staging Stage 4 check column; §Stage 4 budget (2,600 / 860, 10–20 GPU-h); §8 "no sparse-measure point-set key … raises"; §11 `run_wakeup` grid assertion and `--measures plateau` gate; Checkpoint 4.0 (any NaN plateau stops before the timing gate; w0000 must reproduce checkpoint 13 or it is a disagreement); 4.5 "no measure is thinned" | none |
| T2 | closed | §B2 Points, §7 `stage_level` (`delta_episode_number` / `window_n`, other raises), Checkpoint 4.6 (weighting read from the pinned file, direct equality to `pilot_readout`, `window_n` printed beside) | none |
| T3 | closed | §6 `require_clean` follows `verdict_words_allowed`, `verdict_policy` raises on unknown status; §8 enum = the rules' keys; §9 figures print `label` via `verdict_policy`; §6 tests include `b2_wakeup` accepted + dirty-file block. Checked the rules: `label` exists for `pilot` and `b2_wakeup` only, `verdict_prefix` for `interim` only, as §9 says | none |
| T4 | closed | §11 `t_cross` keyword list includes `noise_window_divisor` with a fixture row that fails on a typed 3 (window 26 > 25.5 → NaN); §6 no-literal test names `wakeup.py`; `remedy.*` reported by `study_reading_A1` with no exemption list; A4 lists and `G5.stage` read from `parameters:` with the 1-based translation | none |
| T5 | closed (rules); fixture row **not yet in §11's table** | rules l.645–647, l.658; plan l.113 says the developer adds it | 🟢 The §11 fixture table is what R.2 signs; add the row ("last three points 0, 0, 1 → NaN, reason `no sustained crossing`", signed and plateau alike) to §11 now so the developer does not have to find it in the Revision 3 table. Owner: senior-developer (one line). |
| T6 | closed | stale "25 points / window 9" gone | none |
| T7 | closed | Stage 4b check column names Checkpoint 3.3 for seeds 42, 43, 44 | none |
| T8 | open (Low), correctly assigned | plan l.113 assigns the "next checkpoint after the last listed May stage-0 checkpoint has a different saved stage" assertion to the developer, but §11 `run_wakeup` does not state it — the only spec the developer reads | 🟢 One clause in §11 `run_wakeup`. Owner: senior-developer. Not a Stage 4 gate. |

**Wake-up manifest comment (l.54–55).** `algorithmic_null_wakeup.yaml:54-55` still says "Remaining schema keys (out_root, rollout sizes, **the sparse-measure point set**, …) are added by developer." This is not a stale description; it is an instruction to the developer to add the one key that §8 and §11 now say must make `run_wakeup` raise. 🟡 **Fix before Stage 4** — one comment edit by `experiment-designer` (the manifest is designer-owned; nothing pins its hash, so no re-pin is needed). If left, the developer's own manifest additions fail the driver's first load, which costs a confused hour, not a wrong result.

**Addendum (in-flight Stage 2) — safe to absorb, nothing to invalidate.** Working tree at review time: only `src/models/recurrent_ppo_network.py` modified (Stage 1). No Stage 2 file exists yet (`scripts/analysis/nmn/` has no `probe_set.py`, `teacher_forced.py` or `run_activations.py`), and `evidence_status` appears nowhere under `scripts/`, `tests/` or `src/`. So the addendum's condition ("if Stage 2 code already validates `evidence_status`") is currently false; the developer simply builds Stage 2 against §8 as revised. Stages 0, 1 and 5 are untouched by Revision 3.

**Between Stage 3 and Stage 4's start**, other than Checkpoint R.2: (1) the manifest comment above (designer, one line); (2) the §11 fixture row for T5, since R.2 signs that table (senior-developer, one line); (3) Stage 4's own prerequisites as the plan already lists them — `untrained.py` for Checkpoint 3.3 / 4.4, Checkpoint 4.0 before any rollout, the timing gate before the sweep. Nothing else.

**Cost of being wrong.** No data loss and no training relaunch. If the manifest comment is left, the cost is one confused developer hour. If the T5 row is omitted from the signed table, R.2 signs a table missing one branch and the first real curve that hits it is judged by unsigned code — a text fix, but one that should land before R.2, not after.

Reviewed by: plan-reviewer, 2026-09-30 (confirmation of Revision 3)

## Feedback from plan-reviewer — Revision 4 (2026-09-30, 02:40)

**Verdict: SOUND WITH CONCERNS. R4-1 and the R4-7 collector fix are GO now** — nothing found blocks the developer from starting them before the 08:30 collection. No Critical finding, so no review file is written. Legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run · 🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

Scope: R4-1…R4-7 and Checkpoints R4.1–R4.6 only; earlier revisions stand as reviewed.

### R4-1 store precision — closed (GO)

Checked against JAX 0.9.0.1 as installed, not from memory:
- **Coverage.** `lax.canonicalize_precision` reads `config.default_matmul_precision.value` at *trace* time whenever an op is called with `precision=None`, so the mode is baked into every `dot_general` in the jaxpr — inside `scan`, `vmap` and `nnx.jit` alike, and in the environment's own visual-PSF matmuls (`src/environment/sensor.py:243–244, 281, 393`), which do run inside the rollout. No file under `src/`, `scripts/` or `train.py` passes an explicit `precision=` to any matmul-class op, so nothing opts out; the collector has no threads that could trace outside the context; the GPU worker branch unsets `XLA_FLAGS`. Reading `jax.config.jax_default_matmul_precision` inside the context returns `"highest"` on this version (verified), so the manifest read-back works as written.
- **Self-test soundness, measured** (256×512 · 512×256, rng 0, metric as specified): local RTX 4090 `highest` **1.32e-7**, `default` **2.63e-4**; CPU `highest` = `default` **9.13e-7**. The 1e-5 constant is therefore 26× below TF32 and 76× above GPU float32 — but only **11×** above CPU float32, tighter than the plan's "~1e-7 for float32" suggests. Still a valid detector; paste both R4.1 numbers as planned and state the CPU value beside the constant's comment.
- **End-to-end confirmation already exists:** the pilot replayed the 2080 Ti (native float32) store on a 3090 under `highest` at 100 % agreement, so the mode switch demonstrably reaches the network's matmuls on Ampere. Checkpoint 6.1's 100 % self-replay on all 12 May stores is the final check.
- **Resume guard.** Legitimate: the May spec puts each store in one worklist cell on one card, and the guard is the same philosophy as the existing `device` guard. A worker relaunched on a different card class is refused, which is the intended behaviour; there are seven 3090 nodes, so same-class relaunch is easy.
- **Running training and existing stores:** untouched. Legacy stores are read with `store_matmul_precision: highest|default` explicitly; the pilot manifest keeps working.

| Sev | Where | Issue | Fix / owner |
|---|---|---|---|
| ❓ | R4-1 resume guard | "No completed store needs resuming" is asserted, not shown. A recursive scan of `results/trajectories*` for stores with fewer completed blocks than `n_episodes/shard_episodes` timed out on the NAS during this review. | Before merging, list incomplete stores per root (iterate the known store dirs, not `**`). If any exists, note that it can no longer be resumed and must be re-collected. `developer` |
| 🟢 | `build_manifest` signature | Three new required kwargs break eight test call sites (`tests/test_trajectory_collection.py:125, 1322–1385`, most through one `kw` dict). Mechanical. | Update once; `developer` |
| 🟢 | Data statement | A store collected under `highest` computes the environment's visual PSF in full float32, whereas training on Ampere/Ada computed it in TF32 (the sensor docstring says ~3 decimal digits). The episode population is therefore not bit-the-same as training-time, in the same sense a 2080 Ti store already was not. Not a registered claim; worth one sentence in the schema doc's manifest-field text so nobody later reads `matmul_precision: highest` as "identical to training". | `developer`, same commit as the schema doc update |
| 🟢 | `run_collection.py`/worker | Optional second layer: `export NVIDIA_TF32_OVERRIDE=0` in the worker's GPU branch (driver-level TF32 off). Not a CLI flag, so it does not reopen the escape hatch; redundant if XLA honours HIGHEST, which the self-test proves. | `developer`, optional |
| 🟢 | Known Bugs l.140 | The precision-hazard row reads "remedy decided, not built"; update to "built at <sha>" when R4.1 passes. | `bug-curator` |

### R4-7 collector fix (item 2) — closed (GO)
The missing-section raise is the right direction (loud rather than silently recording a different world). The "all five sections present in all five stage files of all six May runs, checked by script" claim needs its script and output named in the Implementation Report so it is inspectable, not re-derived. Items 1, 3, 4: closed, nothing to add.

### R4-2 activation storage — closed for every verdict-bearing statistic; one 🟡 on reporting
Checked against the rules `4c8508af…`: A1 pairs verdict layers only; A2 decodes verdict layers (G4's input reference comes from the probe file); A3 is A1 plus UNTRAINED pairs on `X.out` / `rnn.state` (verdict layers); A4 movement needs verdict layers at all five stage ends on both probes (`every_capture`) and within-stage drift needs `:prev` only on the probe its `drift_pairs` entry names — exactly what R4-2 keeps. G1–G3 are computed in replay; G6 counts groups. The rules' `evidence.primary_checkpoint: final` / `primary_probe_world: active` matches the evidence `headline_capture`. The kept set starves no registered comparison.

| Sev | Where | Issue | Fix / owner |
|---|---|---|---|
| 🟡 | R4-2, interim manifest `headline_capture: null` | The rules say of `interim`: "All rules below apply unchanged." Descriptive layers are reported-only, so this decides no verdict, but with `null` the interim report has no "where the difference arises" localisation at all, and an interim A1 `different` would be unexplainable at the layer-site level. Cost of keeping them at one interim capture is ~13 GB. | Either set the interim `headline_capture` to `{checkpoint: stage_end:0, probe: active}`, or state in the plan and the interim data statement that the interim omits descriptive layers. `senior-developer`; `experiment-designer` to confirm which |
| 🟢 | R4-2 | A4 applies the A1 layer verdict at *every* stage end; a `different` at a non-headline stage end will also have no descriptive localisation. Acceptable, but say so once in the A4 figure's data statement. | `senior-developer` |

### R4-4 G2 margin — closed; **not** a loosening of a registered gate
Read against the rules text (`G2_reconstruction`, l.232–236): the gate lists "logits from actor.out, value from critic.out, rnn.state from the GRU step, and X.mod == gain·X.raw + offset" — the neighbour reconstructions only. The plan's own §4, which the rules cite for the tolerance, likewise describes only the chain ("each key is checked against its neighbour"). The sampled-vs-full comparison was never in either; it was a developer-added check the code held to `g2_tol` (`teacher_forced.py:435`). Moving it to a developer-owned tool tolerance changes no registered quantity, and the chain check is verifiably one-step (`teacher_forced.py:147–152` recomputes from the *captured* previous state). No `revisions` entry is needed. The 1e-3 basis (≥100× above the observed 8.3e-6, ≥10× below a one-step slot error) is stated, and the planted shift control shows the check can fail. Two exact guards on slot indexing remain.

| Sev | Where | Issue | Fix / owner |
|---|---|---|---|
| ❓ | R4-4 chain check, `rnn.state` at 4.93e-6 vs 1e-5 | One-step deviation this large is plausibly XLA-GPU's approximate `tanh`/`logistic` differing between two fusions, not accumulation — consistent with the plan — but its size depends on the activation regime of the *trained* network, so a May network could sit 2× higher and cross 1e-5 by compilation noise alone. The plan is right **not** to widen G2 now (the `revision_policy` forbids moving a threshold on a pilot magnitude). If it fails on May, the honest path is reason (2): the gate blocks, a revision says how a compilation-noise failure reads, and the verdict is reported beside it. Say this in the plan so nobody improvises at that moment. | `senior-developer` (one sentence); `experiment-designer` is not asked to act now |
| 🟢 | R4-4 | A pre-data tooling change that is *not* a threshold move: recompute the chain on the same device with fast-math approximations off (an `XLA_FLAGS` toggle in the chain program only) and see whether 4.93e-6 drops. Optional. | `developer` |

### R4-6 shared key recipe — closed; no risk to the running jobs
- Value-preserving, verified on `train.py`: between l.1153 and each branch's split (l.1207, 1290, 1312, 1342) the only use of `key` is `env.reset(env_key, …)` at l.1156; `model_key` is unused; every branch's first act is the same split. The golden-key test pinned to the pre-edit sha is the real proof. The Checkpoint 1.3 jaxpr hashes are trivially identical (keys are inputs, not program), so do not present them as evidence for R4-6 — the plan already half-says this.
- Running May jobs: Python holds the compiled module; the trainer's only subprocess (`scripts/eval/experiment_eval_checkpoint.py`) imports `run_sweep`, not `train`. A crash-and-resume runs the edited `train.py`, restores `key` from the checkpoint (l.1543), and rebuilds the env from it — same bits either way. `src/utils/init_keys.py` is additive.

| Sev | Where | Issue | Fix / owner |
|---|---|---|---|
| 🟢 | Checkpoint 4.4 second half | "`git.commit` and `training_git_sha` must agree" has no stated outcome for disagreement (a dirty launch tree or a missing WandB git field). Say: record both; the closeness check decides; a disagreement is reported, not a stop. | `senior-developer` |

### R4-3, R4-5 — closed
One loader, tests that `decision_rules.load is rules_pin.load` and no `hashlib`/`yaml` import — sufficient. `SCRIPTS_DEPENDENCY_MAP.md` row exists. R4-5 is a corrected sentence with the test already asserting `action_next[t] == action[t+1]`.

### Passes with nothing to report
Project rules (no fallback defaults: `_req` and mandatory manifest keys throughout; survival-step metric unaffected; conda path in the worker; schema doc updated in-commit with `test_schema_doc_matches_code`); side effects (no `git clean`, no branch moves, no results writes outside a throw-away `--out-root` for R4.1); ordering (R4-1 + R4-7(2) gate collection; the rest gate analysis); prior art (Known Bugs l.139/140/162 consulted, no collision; l.140 to be updated by `bug-curator`).

**Cost of being wrong.** If R4-1 is wrong in the way I looked for (an op escaping `highest`), the cost is one 5.6 GB, ~1-hour May collection re-run, and it cannot pass silently: Checkpoint 6.1's 100 % self-replay fails. If the interim `headline_capture: null` stands, the cost is an interim page that cannot say where a difference sits — a reporting gap, not a wrong verdict. No data-loss hazard in any R4 item.

Reviewed by: plan-reviewer, 2026-09-30 (Revision 4)

## Feedback from plan-reviewer — analysis-verdict gate on the interim result (2026-09-30)

**Verdict: SUPPORTED WITH CAVEATS.** In plain words: at the end of the first of five training stages, the tool says the agent with a neuromodulator and the ordinary agent are *less interchangeable* inside than two ordinary agents trained from different seeds are, on four of the five layers checked, and it says so under the rules exactly as they were signed before any number existed. I tried to make that result come out of an estimator artefact instead of a real difference and could not. What the result does **not** yet establish is *why*: the modulated agents are also less interchangeable *with each other* than ordinary agents are, so "different computation" and "a less converged, more seed-variable arm at stage 1" fit the numbers equally well. The evidence run at the final checkpoint is the registered check that separates those two. The page may show the verdict as "provisional — different" once the four caveats below sit beside it.

Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run · 🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

### What I checked and how

- **The word follows from the numbers under the signed rules.** Rules file sha `4c8508af…` at HEAD equals the stamp in every output; the rules commit (`872b0e04`, 00:47 KST) precedes the final outputs (`2acd8cd8`, 06:50 KST) and no later commit touches the file. Per layer, from `similarity.csv` / `evaluation.summaries`: enc.out L = 0.8852, six MO_diff points 0.8358–0.8548, MO_diff-mean 95 % quantile 0.8517 < L → different. rnn.state L = 0.7914, points 0.7593–0.7738, upper quantile 0.7705 → different. rnn.out L = 0.7914, points 0.7562–0.7651, upper 0.7625 → different. actor.out L = 0.7721, points 0.7309–0.7584, upper 0.7508 → different. critic.out L = 0.8452, 2 of 6 below, lower quantile of the mean 0.8324 < L → undetermined. Informative gate: OO band strictly above the UNTRAINED band on every layer and statistic (rnn.state predictivity is the near case: OO [0.7914, 0.7993] vs UNTRAINED [0.8024, 0.8202], disjoint). A3: shared start 27/27 on all three seeds, E false on every layer, survival +1.79 inside 2 × 3.6 → (c) on the four layers. All as reported.
- **CKA agrees with predictivity on every layer**: 6 of 6 MO_diff below L on the same four layers, 4 of 6 on critic.out (undetermined). CKA has no ridge and no standardisation, so it is immune to hazards (a) and (d); it *is* sensitive to a fixed per-unit gain, which predictivity is not. Both agreeing means neither a fixed gain nor a ridge artefact explains the result on its own.
- **Direction check (existing numbers).** For a pair written `ordinary|modulated`, `r2_ab` predicts the modulated layer (the only direction hazard b, variance weighting of the modulated target, can touch) and `r2_ba` predicts the ordinary layer (the only direction hazard a, standardisation of rare modulated predictor units, can touch). On all four "different" layers, **both** directions of all six MO_diff pairs are below L. An artefactual verdict would need both hazards to fire, one per direction.
- **Robustness run (reviewer's scratch, descriptive, not a verdict):** one 80/20 episode-seed split, the penalty the CV chose (31.6), scored four ways. Registered scoring reproduces the reported numbers (enc.out OO 0.889–0.893 vs reported 0.889–0.892). Excluding units active on < 1 % of training rows from both sides, or flooring the standardisation scale at the median unit sd, moves every number on enc.out / rnn.state / actor.out by **< 0.003** and leaves the gap intact (min-of-directions: enc.out OO ≥ 0.889 vs MO_diff ≤ 0.856; rnn.state 0.793 vs 0.775; actor.out 0.777 vs 0.758). The **unweighted** mean of per-unit R² *widens* the gap (enc.out OO 0.779–0.786 vs MO_diff 0.629–0.674; rnn.state 0.759–0.766 vs 0.732–0.739; actor.out 0.635–0.652 vs 0.548–0.593), so variance weighting understates the difference rather than manufacturing it. On critic.out the same variants move modulated-target R² by up to 0.024 and the unweighted score is meaningless (rare units with near-zero held-out variance give R² down to −9): the hazard is real there, and the variance-weighted, registered statistic is the right one for that layer.
- **Hazard (d).** The Gram-matrix inner-CV path only chooses the penalty. Across all 5 repeats, the chosen penalty is the same for OO, MM and MO fits on enc.out (31.6/100 in the same proportions), rnn.state, rnn.out and actor.out (100 for every trained fit); it scatters 10–31,622 only on critic.out. A selection artefact cannot be asymmetric where the selection is uniform. `code-reviewer` still owes S3-b, but it is not a verdict risk.

### Findings

| Sev | Where | Issue | Suggested handling | Owner |
|---|---|---|---|---|
| 🟡 | A1 mm_qualifier fired on enc.out, rnn.state, rnn.out (`evaluation.A1.layers.*.qualifier`) | MM pairs sit where MO_diff pairs sit (enc.out MM 0.852–0.868 vs MO_diff 0.836–0.855; rnn.state MM 0.759–0.770 vs MO_diff 0.759–0.774). The data fit "different computation" and "a more seed-variable / less converged modulated arm at stage 1" equally. The analysis does not rule the second out; the rules' own interim note says as much ("a difference in progress, not in computation"). | Page wording "consistent with different processing", not "shows"; state the qualifier in the same sentence as the verdict; name the evidence run as the discriminator. No verdict change. | page author / `experiment-analyzer` |
| 🟡 | A3 pattern (c), `evaluation.A3.survival` | "Same outcome" is measured at the step cap: cap 500, S₁ = 464–468, 92 % of probe episodes truncated. And the raw SE is 0.83, so +1.79 steps is 2.2 raw SE; the reading rests on the registered floor 3.6 (correctly applied). | Keep the word; print both facts beside it ("same at the ceiling; inside the registered floored SE, beyond the raw SE"). | page author |
| 🟡 | Implementation Report S3-f, l.1636: "It hit no verdict-bearing number" | Inexact. The rare-unit hazard is present on critic.out, a verdict layer (numbers move ≤ 0.024, penalty choice unstable); it changes no **word**, and moves the four "different" layers by < 0.003. | Reword to "changed no verdict word; touches critic.out's numbers, not the four layers that read different". Record S3-f in the registry. Decide a scale floor / near-constant-column exclusion **before the evidence run**, where critic.out could otherwise flip on an artefact; that is a `fit_ridge` change under revision reason (1), so rules + rerun, not a silent edit. | `developer` (text), `bug-curator` (registry), `senior-developer` + `experiment-designer` (floor decision) |
| 🟢 | Report table l.1614–1620, "four of five layers" | Not four independent confirmations: for ordinary agents rnn.out *is* rnn.state (identical OO band 0.7937/0.7972/0.7971), and the modulated rnn.out differs from its rnn.state by only ~0.005 in MO predictivity; enc.out feeds the GRU. | Say "four layers, of which the two memory layers share the ordinary side". | page author |
| ❓ | Informative gate on rnn.state / rnn.out predictivity | Untrained band above the OO band. Meaning: untrained GRUs with small weights are near-linear filters of one input stream, so two of them are near-linear maps of each other and linear predictivity rewards that; training makes states nonlinear and seed-specific. On these layers predictivity has a compressed range (0.76–0.82 holds untrained, OO, MO and MM), so the 0.02–0.03 MO-vs-OO gap is the size of the untrained-vs-OO gap the other way. The registered gate (overlap) passes and is applied as signed; a one-sided gate would be a post-data rules change and is not proposed. What gives rnn.state its scale is CKA, whose floor is proper there (untrained 0.56–0.60, OO 0.917–0.923, MO_diff 0.880–0.912) and which agrees. | Note for the evidence-stage reading, not a change now. Report CKA next to predictivity on the memory layers, not below it. | `experiment-designer` |

### The proposed diagnostics — what each would be

- **Rare-unit exclusion, scale floor, unweighted R²** — descriptive robustness, reported beside the verdict. Done above on one split; the developer can produce the same three columns under the registered 5-repeat split in minutes. None changes a word; making unweighted R² the registered statistic would be a rules revision after seeing data and is not needed (it widens the gap).
- **Artificial fixed per-unit gain on an ordinary agent, OO predictivity recomputed** — a *tool check* of §E's invariance claim, cheap, reported beside. The synthetic version already ran (l.1552). If predictivity moved by more than the bootstrap width on a real layer, that would be a tool bug → fix + rerun; I expect it will not.
- **A `_standardise` floor** — a tool change; if adopted it is a rerun under a new commit, justified by revision reason (1) (the −4,100 case is a statistic that cannot be computed as written). Not required for this interim verdict.

### Assumptions the verdict rests on

Verified here: rules sha and commit order; all six runs enter G5; shared start on all three seeds; both directions below L; penalty uniformity on the four layers; robustness to rare-unit handling and weighting. Not verified, and not needed for the word: that the modulator's gain is materially non-constant at `stage_end:0` (B2 answers this; the rnn-site FiLM changes MO predictivity by only ~0.005, so the situation-dependent part there is small); where the enc.out difference arises, raw vs mod (`similarity_descriptive.*`, still computing at hand-off).

### Minimal set before the page shows "provisional — different"

1. The MM qualifier and the "progress vs computation" alternative in the verdict sentence (text).
2. The survival-ceiling and floored-SE facts beside pattern (c) (text).
3. Per-direction R² and the three robustness columns beside the A1 table (developer, registered split; descriptive).
4. S3-f reworded and recorded; floor decision scheduled before the evidence run.
Nothing here needs a rerun before publication as provisional.

**Cost of being wrong.** If "different" is an artefact I missed, the cost is one provisional sentence at stage 1 of 5 that the evidence run at the final checkpoint overwrites under the same rules — no relaunch, no data loss, and the registered interim status already forbids it overriding the evidence verdict. If the alternative reading (progress, not computation) is right and the page says "shows different processing", the cost is a wrong framing steering the research direction for the weeks until the evidence run.

Reviewed by: plan-reviewer, 2026-09-30 (analysis-verdict gate, interim)
