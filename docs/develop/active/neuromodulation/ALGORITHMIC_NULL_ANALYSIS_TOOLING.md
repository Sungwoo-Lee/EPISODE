---
title: "Analysis tooling for 'What Both Agents Compute' — layer capture, stored-episode replay, similarity, decoding, modulator wake-up"
topic: neuromodulation
status: active
created: 2026-09-29
last_updated: 2026-09-30
---

# Analysis tooling for "What Both Agents Compute"

> **Status**: PLANNED, **Revision 3** (2026-09-30) after `plan-reviewer`'s third review returned NOT READY for Stage 4 only (Revision 1: 2026-09-29; Revision 2: 2026-09-30). Stages 0, 1, 2 and 5 are being implemented by `developer` against Revision 2; Revision 3 does not change their substance (§Revision 3). Stage 4 awaits re-review.
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
  - `action_next` at `t = T−1` is masked out (there is no next row).
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
| **6 — May replication, full** | after training | Launch collection of `final` + `stage_end:3` (end of `04_passive`) for all six runs via the finished-runs-only launcher with the six logs **named** (§12). Then A1–A4 (activations at `stage_end:0..3`, `final`, `stage_end:3:prev` and `final:prev` on both world probes; the `:prev` checkpoints need no stores of their own) and B2 `01_active` are final | Every store validates (`validate_store_structure/shapes/draws`). Each store's `resolved_env_config.environment` equals its stage file's. Action agreement 100% per generating agent. The figures switch to `evidence_status: evidence` |

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
- `decision_rules.py` (the contract of §E):
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
- `tool_checks: {shift_change_rows_max, self_similarity_atol}` — the plan's own abort tolerances that no gate covers, which decide no verdict (a failed check aborts the run). They live in the manifest so that no number sits in a script.

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
- **`run_wakeup.py --manifest <wake-up manifest> --measures {plateau,grad_share,grad_probe,update_size,rho,swing,freeze}`**. It loads the manifest with `decision_rules.load` (sha256 check), calls `require_clean` because `b2_wakeup` allows verdict words, asserts the `wakeup:` values against the rules' `B2` section, and passes every wake-up value to `wakeup.t_cross` explicitly (`wakeup.py` has no defaults). **Grid (Revision 3, T1):** one x grid per run, the manifest's `checkpoints` plus step 0 for anchorable measures; every measure is computed on exactly that grid, asserted per curve, and a manifest carrying any per-measure point set raises. **`--measures plateau`** (CPU, WandB only) computes `t_plateau` for every run and writes the Checkpoint 4.0 table; every GPU measure refuses to start unless that table exists for the same manifest and rules sha256 and has no NaN plateau. It reuses `replay`, `mod_distribution`, `spectral_bound`, `freeze` and `ckpt_io` unchanged, and adds the step-0 point through `untrained.build` for the measures marked in §B2.

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

Update the rows for:
- `replay.py` (now imports `scripts.eval.eval_rollout`);
- `collect_trajectories.py` (now imports `eval_rollout` and the stage-reading logic; its `resolve_checkpoint` gains new callers `run_activations.py`, `untrained.py`, `run_wakeup.py`);
- `eval_rollout.py` / `continual_forgetting_matrix.py` (new callers);
- `pilot_pick.py` and `continual_worlds/pilot_readout.py` (precedents factored, not imported by the tools; `pilot_readout.py` is imported by the Checkpoint 4.6 cross-check test, `tests/analysis/test_nmn_stage_level.py`, which is a new caller);
- `launch_collection.py` (new `--logs` flag);
- `build_algorithmic_null_page.py` (now reads `figures/algorithmic_null/` and runs the §11 checks).

Also update `scripts/eval/traj_collect/README.md` (a `stage_end:<k>` selector and continual worlds, one short section).

**Not touched:** `train.py`, `recurrent_ppo_trainer.py`, `neuromodulator.py`, `ckpt_io.py`, `mod_distribution.py`, `freeze.py`, `spectral_bound.py`, `run_*` legacy drivers, the trajectory-store schema, `configs/environment/`, and the level-05 `analysis_manifest.yaml`. No config key is added to any training config, so neither `CONFIG_GUIDE.md` nor `CONFIG_CRITICAL_SETTINGS.md` changes.

### Deferred (not in scope; needs its own approval)

**Trainer logging for future runs.** Two quantities:
- per-term modulator gradient norms (three extra `global_norm` calls on per-term grads, which needs three extra backward passes or `jax.vjp` reuse, so it has a real speed cost);
- per-update ‖Δθ_mod‖/‖θ_mod‖ (cheap: the params before and after the optimiser step are both in scope in `update_step`).

This belongs in a separate plan with a speed measurement. It would make B2's per-update resolution available to the "stronger start" runs of B1. A saved step-0 checkpoint for future runs would also make the untrained anchor a stored fact rather than a reconstruction.

---

## Checkpoints

- [ ] **0.1** Strict `load_agent` succeeds for all 32 level-05 runs at their store checkpoints, and for all six May-replication runs at the latest checkpoint. The list is pasted into the Implementation Report.
- [ ] **0.2** The May replication's five stage files: the env sections of `01/03/05_active` are identical to `config.yaml`'s; `02/04_passive` differ only in `environment.entities` (besides `agent`/`tag`/`wandb`).
- [ ] **R.1** `experiment-designer`'s revised rules file (with `parameters:` and `B2`) and the wake-up manifest are committed, and all four manifests pin the rules file's current sha256. Record the file paths, commit shas and commit times. Record the `generated_utc` of the first `run_similarity` / `run_decoding` output of any manifest and of the first `run_wakeup` output, and show each is **later** than the rules commit. (Verifier checks both from `git log` and the output `manifest.json`.)
- [ ] **R.2** `experiment-designer` has read the evaluator's fixture table (`tests/analysis/test_nmn_decision_rules.py`, the "rules — logic" cases) and signed in the Implementation Report that each row is the rules' intended reading. The signature's commit time precedes the first real `run_similarity` / `run_decoding` / `run_wakeup` output. Any row the designer rejects is a rules revision (reason 1 of the rules' `revision_policy`) or a code fix, before any number exists.
- [ ] **1.1** Record the golden parameter hashes on the **unmodified** commit (state its sha) *before* editing the network.
- [ ] **1.2** `tests/models/test_capture_activations.py` passes. All of `tests/models/` passes.
- [ ] **1.3** **Jaxpr identity (the speed gate).** Method, tested on 2026-09-29 on a synthetic 8-input / 16-hidden model: `g, s = nnx.split(model)`; wrap `f(s, x, h) = get_action_and_value_nnx(nnx.merge(g, s), x, h, key, eval_mode=False)` and `L(s, b) = ppo_loss_fn(nnx.merge(g, s), b, 0.2, 0.01, 0.5)[0]`. Hash `str(jax.make_jaxpr(f)(s, x, h))` and `str(jax.make_jaxpr(jax.grad(L))(s, per_env_batch))`, where `per_env_batch` is a `PPOBatch` of one env (`obs (T, D)`, `h_init` unbatched), matching the trainer's `vmap` over envs. Three separate processes gave identical hashes for the ordinary and a four-site FiLM `activation` model, for both functions. For this checkpoint, run it on the real ordinary and t16quad agent blocks, before and after the change; the `diff` must be empty. **Positive control:** a throw-away edit inserting `x = x * 1.0` into `_forward` must change the hash (then revert it), which shows the check can fail. Paste commands and hashes. A 200-iteration timing on one node is optional.
- [ ] **2.1** Pilot probe built from the pilot manifest's `n_per_store`. Its data counts (episodes per store, **distinct `episode_seed` groups**, rows kept, predator-valid rows, truncated episodes) are printed and saved. The group count meets gate G6 (`n_groups × test_frac ≥` the held-out minimum); a deliberately small `n_per_store` (e.g. 1,000) is shown to raise. The one-pass row-index assertions pass.
- [ ] **2.2** Self-replay agreement = 100% for each agent of the pair on its own store (near-ties within gate G1's allowance, read from `parameters:`). Step-discontinuous alignment on sampled rows = 100%, including on action-change rows. Shift-by-one < 95% overall and < 5% on action-change rows, with both numbers recorded (≥ 95% overall = inconclusive, stop). Cross-agent agreement is recorded.
- [ ] **2.3** Chain assertions pass on both real pilot checkpoints for every row of the §4 table that applies. The max deviation per assertion is pasted.
- [ ] **3.1** `tests/analysis/test_nmn_representation.py` and `test_nmn_decision_rules.py` pass, including the leakage, clock, bootstrap, sha-mismatch, no-literal and parameter-coverage tests.
- [ ] **3.2** Positive and negative controls within gate G4's bounds (input-layer satiation R², shuffled-target R²; values pasted with the bounds read from `parameters:`). Same-agent CKA `isclose(1, atol=tool_checks.self_similarity_atol)`. The pilot's outputs carry `verdict_words_allowed: false` and contain no `evaluate_*` result.
- [ ] **3.3** **Shared start on the May replication (rules `A3.precondition_shared_start`; re-review R12).** For each of seeds 42, 43 and 44: `untrained.build` on the May ordinary run and on the May modulated run of that seed gives **identical** main-network parameters (every array, bitwise), and the modulator is the only extra subtree. Six runs, three comparisons, each array count and result pasted. Weights only, CPU; it needs `untrained.py` (Stage 4) and runs before any A3 evaluation.
- [ ] **3.4** Page builds with the pilot figures. The builder **refuses** a deliberately broken copy of the template (missing Axes; a 120-word howto; an inline `<svg>`; a stray file in `figures/algorithmic_null/`; a figure whose `decision_rules` hash differs from HEAD), and **ignores** a stray file in the parent `figures/`. Show the refusals.
- [ ] **4.0** **Survival plateau before any rollout (Revision 3; the third review's open question).** `run_wakeup --measures plateau` on the wake-up manifest, CPU only, for all 19 runs (16 level-05 modulated, 3 May modulated `01_active`). Paste the per-run table: `t_plateau` (checkpoint index and episode), `m₀`, `m_final`, σ_Δ, guard margin `|m_final − m₀| / (noise_k·σ_Δ)`, NaN reason. The w0000 row must reproduce the reviewer's reading (plateau at checkpoint 13); a different value is a disagreement to resolve before going on, not a rounding. **Any NaN plateau stops Stage 4** before the timing gate: the list goes to the user and `experiment-designer`.
- [ ] **4.1** `tests/analysis/test_nmn_wakeup.py` passes with every row of the §11 expected-output table.
- [ ] **4.2** `wandb_history.resolve_by_tag` reproduces §C's six folders. The gradient probe's **(b) full-iteration mean** of `modulator/grad_norm` lies within the 5th–95th percentile of logged values in a ±1-checkpoint window on ≥ 5 checkpoints per run, for ≥ 3 runs. This is a **sanity band**, not a proof of correctness: the world is re-warmed, and the log is one iteration's sample. Also record (a)/(b) side by side.
- [ ] **4.3** `freeze.verify_freeze_equivalence` passes for every run and checkpoint swept.
- [ ] **4.4** Untrained anchor: `test_matches_train_py_construction` passes (bitwise) for one ordinary and one modulated run of each study. For every B2 run, the own-seed reconstruction is closer to the first saved checkpoint than the reconstructions for two other seeds (cosine similarities recorded).
- [ ] **4.6** **Survival and bites cross-check (R5; Revision 3, T2).** For all six May-replication runs, `wandb_history.stage_level` on stage 1 (`stage/index` 0) with `weighting` = the rules' `parameters.common.survival.row_weight` (`delta_episode_number`), read from the pinned file rather than typed into the test, gives `S_1` and bites that equal `pilot_readout.py`'s May-replication readout for the same run to within 1e-9 relative (`tests/analysis/test_nmn_stage_level.py`, marked slow, reads the local binaries). Because the registered weighting is `pilot_readout.Series`'s own, this is a direct equality check. The `window_n`-weighted values are pasted beside them as a diagnostic. The G5 pass/fail and the survival difference in the interim driver JSON are pasted. The same check is repeated on stage 5 after training.
- [ ] **4.5** Stage 4 timing gate: seconds per item recorded, extrapolated wall-clock stated for the every-checkpoint sweep, and the second-node decision (spread over a second node's GPUs if the extrapolation exceeds 8 h) recorded before the full sweep. No measure is thinned (Revision 3, T1).
- [ ] **5.1** Collector tests pass, including fingerprint tests (i)–(iii) and the `:prev` tests. On a real May-replication run, `stage_end:0` and `stage_end:3` resolve to checkpoints whose saved `stage` equals 0 and 3, and the `stage_end:3` world has `detection_range: 0`. After training, `stage_end:3:prev` and `final:prev` resolve to checkpoints with the same saved stage as their successors, and their episode gaps are recorded.
- [ ] **6.1** After collection: all 12 stores validate. Each store's world is correct. Self-replay agreement is 100% for all 12.
- [ ] **6.2** `SCRIPTS_DEPENDENCY_MAP.md` and `traj_collect/README.md` are updated in the same commits as the files they describe.

## Implementation Report

> **Implemented by**:
> **Date**:

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
