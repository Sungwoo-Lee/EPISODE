---
title: "Analysis tooling for 'What Both Agents Compute' — layer capture, stored-episode replay, similarity, decoding, modulator wake-up"
topic: neuromodulation
status: active
created: 2026-09-29
last_updated: 2026-09-29
---

# Analysis tooling for "What Both Agents Compute"

> **Status**: PLANNED, **Revision 1** (2026-09-29) after `plan-reviewer` returned NOT READY. Awaiting re-review, then user approval. Nothing is implemented.
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

**What changed in this revision.** A reviewer found two ways the tools could print a wrong sentence without any error, and several weaker checks. First, the "modulator wakes up at checkpoint *k*" measure could report "awake from the start" for a quantity that shrinks over training, and a random checkpoint for one that ends where it began. It now follows the direction of the change, and it refuses to name a checkpoint when the change is within noise. It also starts from the untrained network, not the first saved checkpoint. Second, nothing fixed in advance what counts as "the two agents compute the same thing". That rule is now written by `experiment-designer` before any similarity number exists. The tools read it and never hard-code it. With no rule on file, they print numbers but no verdict. The full response to each finding is in §Revision 1.

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
- **Which manifest holds the rules.** Two manifests are meant, and they are different files:
  - **May replication (evidence):** `docs/experiments/active/modulator_clues/algorithmic_null_mayrep.yaml`, a new file. The May design doc has no analysis-manifest YAML (its launch manifest is a table in [[MAY_DOUBLE_RETURN_REPLICATION]]), so this file is the one that governs these analyses. `decision_rules` goes here, and `experiment-designer` owns that block.
  - **Pilot:** `docs/experiments/active/modulator_clues/algorithmic_null_pilot.yaml`, a new file with `decision_rules_ref: null`. The pilot compares two agents that share seed 42 and has no seed yardstick, so no rule can apply to it. It prints numbers and no verdict.
  - **Not a target:** `docs/experiments/active/level05_body_interactions/analysis_manifest.yaml` is the *schema precedent* and the source of the level-05 WandB ids. It belongs to the level-05 store scripts, which would never read a `decision_rules` block placed there. If `experiment-designer` has already put the block elsewhere, `decision_rules_ref` points at it, so no content has to move (File Changes §8).

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
| Freeze cost | **Yes**, at every 5th checkpoint and at the untrained network | `freeze.apply_freeze` + `replay.rollout`, paired seeds (`freeze.paired_differences`) |
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

**Who decides what "the same computation" means (reviewer finding 2).** This plan does **not** set any threshold for:
- "the two agents compute the same thing" (A3);
- "the two agents' decoding profiles match" (A2);
- "the two agents' processing moves together across worlds" (A4).

Those rules are pre-registered by `experiment-designer` in a `decision_rules` block. The block goes in the May-replication analysis manifest, `docs/experiments/active/modulator_clues/algorithmic_null_mayrep.yaml` (§Revision 1 says why that file). The tooling's obligations:
1. **Read, never hard-code.** Every number and every verdict label comes from the block. No threshold or verdict string appears in `scripts/`.
2. **Refuse a verdict without a rule.** If the manifest's `decision_rules_ref` is `null`, or the referenced block is absent, every figure and driver output carries numbers only. The data statement then says: *"No pre-registered decision rule is on file for this comparison, so no verdict is drawn."* The verdict field in the driver JSON is `null`.
3. **Prove the order.** On an `interim` or `evidence` manifest, the driver refuses to run if the rules file has uncommitted changes. It stamps the file's last commit sha and the sha256 of the canonicalised block into every output. The page builder refuses any figure whose stamped block hash differs from the block at HEAD, so a rule edited after results exist cannot sit silently beside them.
4. **Implement only what is written.** The rule evaluator implements exactly the condition forms that appear in the committed block, each with a unit test on a fixture block of made-up values marked "test fixture, not the study's rule". Any condition form it does not implement raises `ValueError`, naming the form.

**Contract the evaluator needs from the block.** This is the shape only; it sets no thresholds, and `experiment-designer` may extend it. Per analysis (`A2`, `A3`, `A4`) the block gives:
- `reads`: which statistics the rule uses, from those the drivers emit (`cka`, `predictivity_r2_ab`, `predictivity_r2_ba`, their bootstrap intervals, the cell labels of the A3 triangle);
- `outcomes`: an ordered list of `{label, condition}` pairs, where the first match wins and the last pair is the fall-through outcome.

If the committed block does not fit this shape, the developer stops and asks `experiment-designer`. The developer does not reshape the block.

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
                    decision_rules_ref → experiment-designer's decision_rules block)
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
        │   decision_rules.py (pure python): load + hash + evaluate the pre-registered block
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

**Action agreement.** Computed on every replay. If the replayed checkpoint is the store's generating checkpoint (`manifest.checkpoint_path` resolves to the same directory), the replay **fails** on any mismatch whose top-two logit margin is ≥ `1e-4`, or if near-ties exceed 0.1% of rows. Otherwise the agreement is recorded as a statistic: how often the other agent would have chosen the same action is itself an A1-adjacent result.

**Probe sets.** A probe set is `n_episodes_per_store` episodes drawn from each listed store, starting at block 0 so only the first shard is read.
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

**Alignment controls (finding 4).** Computed by `teacher_forced` on the **sampled rows through the probe's row index**, so they test the same indexing the targets use:

| Control | Computed as | Required |
|---|---|---|
| **Step-discontinuous alignment** | `argmax(acts.logits[row]) == action_next[row]` on the generating agent's own store | 100% (the near-tie allowance of the action-agreement rule only) |
| Same, on **action-change rows only** (`action[t] ≠ action[t+1]`) | as above | 100% |
| **Shift-by-one** | `argmax(acts.logits[row]) == action[t]` (the action that *arrived* at *t*, one row early) | **< 95%** overall, and **< 5%** on action-change rows. On those rows a correct alignment gives 0% by construction. If the overall number is ≥ 95%, the control is **inconclusive**, not passed: stop and report, because the agent's action runs are too long for it to discriminate |

The satiation input-layer R² stays as a positive control for the target *values*, not for alignment: satiation drops by a fixed step each tick, so it cannot detect a one-row shift.

**A1 / A3 / A4 statistics.**
- Linear CKA uses the feature-space form ‖YᵀX‖²_F / (‖XᵀX‖_F‖YᵀY‖_F) on column-centred float64 features.
- Linear predictivity is ridge with the α-grid chosen by episode-grouped CV inside the training fold, reporting held-out R² (variance-weighted over output units) in both directions.
- Uncertainty comes from 200 bootstrap resamples **over episodes**.
- **Reference rows** make a number readable:
  - the probe's raw input (symlog of `obs`);
  - two *untrained* networks of the same architecture built from different keys (the floor for "similar by construction");
  - same-agent same-checkpoint (`isclose(…, 1.0, atol=1e-12)`; a check, not a result).
- **A3 triangle** (May replication, per layer): ordinary–ordinary across seeds (3 pairs), modulated–modulated across seeds (3), modulated–ordinary same seed (3), modulated–ordinary different seeds (6). The fair comparison for "the same computation" is **modulated–ordinary at different seeds vs ordinary–ordinary at different seeds**. The same-seed cell measures what the shared start (D11) contributes. The rule that turns these cells into words is `decision_rules.A3` (§E), not this plan.
- **A4**: for each agent, CKA/predictivity between consecutive stage-end checkpoints on a fixed world probe (both worlds), i.e. how far its processing moves per stage. The quantities emitted are (i) the correlation across stage transitions between paired agents' movement, and (ii) modulated–ordinary similarity per stage against that stage's seed yardstick. Whether that counts as "moving together" is `decision_rules.A4`.

**A2 decoding.**
- Ridge regression (standardisation fitted on the training fold only).
- Split by **`episode_seed` alone** with `GroupShuffleSplit` (80/20, 5 repeats, fixed seed), so the **same split is used for every agent** on a probe and comparisons are paired. In the pooled May probe, one `episode_seed` appears in all six stores: the same reset, with different trajectories. Grouping by seed alone keeps one world draw out of both folds. **Do not group by `(store, episode_seed)`**, because that leaks the draw (finding 12).
- An assertion that no `episode_seed` appears in both folds.
- Targets: `satiation`, `injury_level`, `nearest_predator_manhattan` (valid rows only), `steps_remaining`.
- **`steps_remaining` (finding 9).**
  - **The headline excludes truncated episodes.** An episode cut off at `max_steps = 500` has a censored remaining lifetime, and `steps_remaining = 500 − t` is then just a clock. 33.5% of pilot episodes are truncated (measured by the reviewer on shard 0 of both w0000 stores). The all-episodes version is kept as a sensitivity row. The exclusion biases the headline toward shorter lives, and the data statement says so.
  - **A time-only baseline** is reported beside every layer, and drawn as a reference line on each layer's panel. It is the held-out R² of ridge on a one-hot basis of `t` (bins of `t_bin_width` steps, a mandatory manifest key), i.e. the best a pure clock can do.
  - Per layer, the tools also report the **excess over the clock**, R²(layer ⊕ t-basis) − R²(t-basis), and the R² of decoding `t` itself from the layer, so a reader sees how much of the layer's "prospects" signal is time.
- Controls: the input layer (a **positive control**: satiation is itself an observation channel, the `Satiation` sensor, so R² at the input must be ≈ 1; if not, target values are wrong), and **shuffled targets across episodes** (a negative control: R² ≤ ~0). Row alignment is checked separately (Alignment controls, above).
- Whether two agents' profiles "match" is `decision_rules.A2`.

**B2 wake-up.**

| Measure | Source | Resolution | Untrained anchor (step 0) |
|---|---|---|---|
| total-loss gradient share | local WandB, `modulator/grad_norm`² / `loss/grad_norm`² | log points, binned to checkpoint intervals | no (first log point ≈ iteration 50) |
| per-term gradient share | `grad_probe.py` at every 5th checkpoint | checkpoints | **yes** (probe on the untrained network with a freshly initialised optimiser, which is exactly the trainer's state at step 0) |
| relative update size | `ckpt_io.load_params` at consecutive checkpoints, modulator vs main | checkpoint intervals | **yes** (first interval is untrained → first checkpoint) |
| contextual fraction ρ | `replay.rollout` (greedy, fixed seeds 90 000+) → `mod_distribution.variance_split` per site | checkpoints | **yes** |
| gain swing | `spectral_bound` (weights only) | checkpoints | **yes** |
| freeze cost | `freeze.apply_freeze` (gain frozen, offset frozen, separately) + `replay.rollout` + `freeze.paired_differences` | every 5th checkpoint | **yes** |
| survival (for the plateau) | local WandB `Episode/Steps` weighted by `Episode/_window_n` (the `survival_tenths.py` convention) | log points | n/a |

**Wake-up definition (finding 1).** For a measure *m* sampled at training points `x_0 < x_1 < … < x_n`:
- `m₀` is the value at the **untrained network** (`x_0 = 0`, labelled "step 0" on the x-axis) where the anchor column above says yes. Otherwise it is the first available point, and the output says which.
- `m_final` is the mean of the last `final_k` points (mandatory, 3).
- `d = sign(m_final − m₀)`, the direction of the net change.
- **Noise band.** σ_Δ is the standard deviation of consecutive differences `m_{i+1} − m_i` over the **final third** of the points (at least `min_noise_points` differences, a mandatory key; otherwise NaN, reason "too few points to estimate noise"). The band half-width is `noise_k · σ_Δ` (`noise_k` mandatory).
- **Minimum-change guard.** If `|m_final − m₀| ≤ noise_k · σ_Δ`, the result is `t_wake = NaN`, reason "net change within the measure's own noise band". A checkpoint is never returned in that case.
- **Signed crossing** (`threshold_mode: fraction_of_rise`, the headline, as the TODO now defines it): `t_wake` is the first `x_i` with `d·(m_i − m₀) ≥ f·|m_final − m₀|` that holds for `sustain` consecutive points (`f`, `sustain` mandatory; f = 0.5). The output records `d` as `rising` or `falling`.
- **The literal definition stays beside it** (`fraction_of_final`): the first `x_i` with `m_i ≥ f·m_final`. It is flagged `degenerate: true` whenever `m₀` already satisfies it (the known trap: the gain swing starts at ≈ 61% of its final value), or whenever `d` is `falling` (the literal rule has no meaning for a falling measure).
- `t_plateau` uses the same signed rule with f = 0.9 on trailing-window survival.

The report always shows both definitions and the guard's verdict. **Which one the page headlines, and the value of `noise_k`, are fixed in the manifest by `experiment-analyzer` / `experiment-designer`, not by this plan.** The developer's fixture manifest uses clearly-labelled test values only.

For continual runs, B2 uses **`01_active` only** (episodes 0–1.5 M, the only stage trained from scratch), with the stage-local final value.

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
| **R — decision rules on file** | **before Stage 3**; owner `experiment-designer` | `decision_rules` block committed in `algorithmic_null_mayrep.yaml` (or wherever `decision_rules_ref` points) | Commit sha and time recorded (Checkpoint R.1). The time **precedes** the `generated_utc` of the first `run_similarity` / `run_decoding` output of **any** manifest, pilot included. The pilot's same-seed numbers are exactly the kind of number a post-hoc threshold would be fitted to |
| **1 — capture switch** | now | File Changes §1–2 | `tests/models/test_capture_activations.py` passes. **The jaxpr of the training loss gradient and of `get_action_and_value_nnx` is textually identical before and after** (Checkpoint 1.3, method tested on 2026-09-29). The golden parameter hash is unchanged. Existing `tests/models/` pass |
| **2 — replay + pilot probe** | now | §3–4. Probe on the level-05 **w0000 pair** (1,000 episodes from block 0 of each store) | Each agent on its **own** store: 100% action agreement (near-tie allowance only). Alignment controls pass at their numeric bounds. Chain assertions pass on the real checkpoints. Same-agent CKA ≈ 1 (atol 1e-12) |
| **3 — pilot A1/A2 + figures** | after Stage R | §6, §8–9. Figures `an01`–`an03` in *pilot* mode. Builder §11 checks (§10) | Unit tests pass. Positive control: satiation R² at the input ≥ 0.99. Negative control: shuffled R² ≤ 0.02. Untrained networks built with the pair's seed have **identical main-network parameters** for both agent types (confirms the shared start). Page builds. `artifact-format-reviewer` passes. Every pilot figure's data statement says **"tool validation — the two agents share seed 42; not evidence"** (from `evidence_status: pilot`) **and** "no verdict is drawn" (from `decision_rules_ref: null`) |
| **4 — B2 on existing runs** | now, in parallel with 3 | §7, §11. All 16 level-05 modulated runs, plus May-replication **`01_active`** for the three modulated runs | Untrained anchor verified (Checkpoint 4.4). Gradient probe inside the sanity band (Checkpoint 4.2). Freeze equivalence: `freeze.verify_freeze_equivalence` passes before each sweep. ρ closure identity (asserted in `mod_distribution`) holds. Timing gate (§Stage 4 budget) passed before the full sweep |
| **4b — early yardstick (optional)** | after Stage R | Collect the **`stage_end:0`** checkpoint (end of `01_active`) of all six May-replication runs (world = stage 0 = `config.yaml`, correct with the current collector), 10,000 episodes each, **one spec per run with an explicit step** through `run_collection.py`. Then A1/A3 at the end of `01_active` | As Stage 2 for every store. A3 figure in *interim* mode ("end of `01_active`, stage 1 of 5"); verdict only through `decision_rules` |
| **5 — collector continual-awareness** | now, so it is ready when training ends | §5 | New tests in `tests/test_trajectory_collection.py` pass. On a real May-replication run, `stage_end:0` and `stage_end:3` resolve to checkpoints whose saved `stage` is 0 and 3, and the `stage_end:3` world has `detection_range: 0` |
| **6 — May replication, full** | after training | Launch collection of `final` + `stage_end:3` (end of `04_passive`) for all six runs via the finished-runs-only launcher with the six logs **named** (§12). Then A1–A4 and B2 `01_active` are final | Every store validates (`validate_store_structure/shapes/draws`). Each store's `resolved_env_config.environment` equals its stage file's. Action agreement 100% per generating agent. The figures switch to `evidence_status: evidence` |

What the page can carry when:
- **After Stage 3:** pilot A1/A2 figures, labelled as tool validation, no verdicts.
- **After Stage 4:** real B2 results (level-05 ×16, May `01_active` ×3 modulated).
- **After Stage 4b:** an interim A3.
- **After Stage 6:** A1–A4 on the May replication.

**Stage 4 budget (the reviewer's open question).** Work items:
- update size and swing: weights only, 16 × 51 + 3 × 16 points, CPU, minutes;
- ρ: one 128-episode greedy rollout per point, ≈ 16 × 51 + 3 × 16 ≈ **864 rollouts**;
- freeze cost: every 5th checkpoint plus step 0, 3 conditions (live, gain frozen, offset frozen), ≈ 16 × 11 × 3 + 3 × 4 × 3 ≈ **564 rollouts**;
- gradient probe: every 5th checkpoint plus step 0, ≈ 16 × 11 + 3 × 4 ≈ **188 probes**. Each probe is `warmup_iters` + 1 training-shaped iterations with 128 envs × 128 steps, and 4 updates.

Scale: 128 episodes × ≤ 500 steps is 500 sequential scan steps at batch 128. Level-05 training ran ≈ 143 episodes/s including updates, so one probe iteration is well under a second once compiled. The sweep is **compile-dominated**: a few jit compilations per run (one per model structure and rollout shape), not per checkpoint. The estimate is **≈ 3–6 GPU-hours in total**, run as two worker processes on the **two GPUs of one low-tier node** (RTX 2080 Ti class, per [LAB_NODE_GPU_SPEC](../../../environment/LAB_NODE_GPU_SPEC.md); routine small-network work), so **≤ 4 h wall-clock**. The node is chosen from `gpu-status` plus the diary, pack-node-first. This is an estimate, so it is gated:
- **Timing gate:** before the full sweep, time one run × 3 checkpoints × every measure, and record seconds per item in the Implementation Report. Extrapolate.
- If the extrapolation exceeds **8 h wall-clock**, thin ρ to every 2nd checkpoint. Decide and record this *before* the full sweep, never after seeing results.

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
  - writes `probe_<id>.npz` and `probe_<id>.json` (sources, counts, sha256 of the row index).
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

  Tolerance: `max|Δ| ≤ 1e-5·max(1, max|reference|)` in float32. The recomputation is a separate XLA program, so bitwise equality is not expected. Every assertion's max deviation is written into the activation file's JSON. Any failure aborts the capture. Because each key is checked against its neighbour, a single key bound to the wrong tensor fails at least one row of this table.

#### 5. `scripts/eval/traj_collect/collect_trajectories.py` — continual-aware collection

- `resolve_checkpoint(run_dir, which)` accepts `stage_end:<k>`: **the last saved checkpoint whose saved `stage` field equals *k*** (0-based; reuse `continual_forgetting_matrix.read_saved_stage`). If no checkpoint has stage *k*, it raises. For a run with no `schedule.yaml`, `stage_end:<k>` raises.
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
- **(i)** a stage-0 checkpoint of the continual fixture gets the **same `env_fp`** as the non-continual path would give for the same `config.yaml`;
- **(ii)** a passive-stage checkpoint gets a **different `env_fp`**, so its store lands in a different directory;
- **(iii)** the manifest's `resolved_env_config["environment"]` equals the stage file's `environment`, and its `seed`/`tag` equal `config.yaml`'s;
- a stage file differing in `training` raises;
- `final` on a non-continual fixture is unchanged.

No existing store belongs to a continual run (the reviewer checked: none under `results/trajectories_*` has a `schedule.yaml`), and `pilot_readout.py` reads only WandB binaries, so this change touches neither.

#### 6. `scripts/analysis/nmn/representation.py` + `scripts/analysis/nmn/decision_rules.py` — new, pure numpy / sklearn / python

- `representation.py`: `linear_cka(X, Y)`, `linear_predictivity(X, Y, groups, split)`, `ridge_probe(X, y, groups, split)`, `time_baseline(t, y, groups, split, bin_width)`, `episode_split(groups, n_repeats, test_frac, seed)` (asserts disjointness), `bootstrap_over_groups(fn, groups, n)`. Everything in float64.
- `decision_rules.py`: `load(ref) -> (block | None, sha256, commit_sha)`, `require_clean(path)` (raises on uncommitted changes when `evidence_status ∈ {interim, evidence}`), `evaluate(block, analysis, stats) -> label | None`. It implements only the condition forms present in the committed block (§E) and raises on any other.

**Tests** (`tests/analysis/test_nmn_representation.py`, `tests/analysis/test_nmn_decision_rules.py`):
- `isclose(CKA(X,X), 1, atol=1e-12)`;
- CKA is invariant to orthogonal rotation and isotropic scale;
- **CKA drops under a per-unit rescaling** (documents the motivating caveat);
- predictivity ≈ 1 under a per-unit rescaling and under a random invertible map, and ≈ 0 for independent noise;
- **leakage test:** a feature that encodes the episode identity plus a per-episode constant target gives high R² under a row-level split and ≈ 0 under `episode_split`;
- **clock test:** a feature equal to `t` scores the time baseline's R² on `steps_remaining` and ≈ 0 excess over it;
- rules: `ref = null` → `evaluate` returns `None` and the figure-side formatter emits the "no verdict" sentence; a fixture block evaluates to the expected labels; an unknown condition form raises; `require_clean` raises on a dirty fixture file.

#### 7. `scripts/analysis/nmn/wandb_history.py` — new

- `resolve_by_tag(tag) -> Path`: scan `wandb/run-*/files/wandb-metadata.json` for `--tag == tag` (the `pilot_readout.find_wandb_by_tag` precedent). **Exactly one** hit is required: zero or several raise, listing them. Never a timestamp glob.
- `read_keys(wandb_dir, keys, allow_truncated) -> dict[key, (episode, value)]`: a general local-binary reader, factored from `pilot_pick.read_history` (which is **not** modified).
- **Episode join (resolved 2026-09-29 by reading the binaries):**
  - *May-replication runs:* each record carrying `loss/grad_norm` also carries `Episode/Number`, `iteration`, `timesteps` and `stage/index`. Use its own `Episode/Number`, and select `01_active` by `stage/index == 0`.
  - *Level-05 runs:* loss records carry `iteration`, `timesteps`, `_step`, but **no** `Episode/Number`. Each is followed by an episode row with the **same `timesteps`** value. So the episode count is the `Episode/Number` of the episode row whose `timesteps` equals the loss record's, compared as floats (the binary writes `374374400` on one and `3.743744e+08` on the other).
  - Unmatched records are counted and reported, never interpolated. The join never converts `iteration` to episodes by arithmetic.
- `wandb_dir_for` is reused through `importlib` (the `survival_tenths.py` precedent).

#### 8. `scripts/analysis/nmn/run_activations.py`, `run_similarity.py`, `run_decoding.py` — new drivers

Each takes `--manifest <yaml>`. Outputs go under `results/analysis/algorithmic_null/<manifest name>/` (JSON + CSV + npz), each with a `manifest.json` recording the git sha, the input manifest, the probe hashes, the package versions, and **`decision_rules: {ref, sha256, commit} | null`**.

**Manifest schema (all keys mandatory; `null` is an explicit value, a missing key is a `ValueError`):**
- `name`, `evidence_status` (`pilot|interim|evidence`), `out_root`;
- `decision_rules_ref: {path, key} | null`. The May manifest's default is `{path: <this file>, key: decision_rules}`. The block itself is owned by `experiment-designer`; the developer never writes or edits it;
- `runs: [{label, path, tag, log, checkpoints: [final | <int> | stage_end:<k>]}]`, where `tag` is used for WandB resolution and `log` for the launcher;
- `probes: [{id, stores: [<store dir>], n_per_store, rows_per_episode, seed}]`;
- `layers: [{key, flatten: none | senses_x_units}]`, `comparisons` (`auto` = every pair of runs, or an explicit list);
- `bootstrap_n`, `probe_split: {n_repeats, test_frac, seed}`, `ridge_alphas`, `untrained_reference_keys`, `min_rows_per_column`, `t_bin_width`, `assert_n_episodes`;
- `wakeup: {threshold_mode_headline, f, sustain, final_k, noise_k, min_noise_points}` (B2 manifests only; values set by `experiment-designer`/`experiment-analyzer`).

The two manifests are `docs/experiments/active/modulator_clues/algorithmic_null_pilot.yaml` (with `decision_rules_ref: null`) and `docs/experiments/active/modulator_clues/algorithmic_null_mayrep.yaml`. The developer writes every section to this schema **except `decision_rules` and the `wakeup` values**. The precedent is `docs/experiments/active/level05_body_interactions/analysis_manifest.yaml`, and the `_req` / `load_manifest` pattern of `scripts/analysis/studies/level05_body_interactions/_common.py`. `experiment-designer` reviews both manifests. If the designer created `algorithmic_null_mayrep.yaml` first with only the rules block, the developer adds the other sections around it and leaves that block byte-identical (its sha256 is checked).

#### 9. Figure scripts — new, `scripts/analysis/studies/modulator_clues/an0N_*.py`

One script per figure: `an01_similarity_layers` (A1, CKA and predictivity per layer pair), `an02_decoding_profiles` (A2, with the time baseline and excess-over-clock for `steps_remaining`), `an03_seed_yardstick` (A3 triangle), `an04_across_worlds` (A4), `an05_wakeup` (B2: four measures plus survival, step-0 point, wake and plateau marked, both definitions and the guard's reason), `an06_freeze_over_training` (B2 freeze subset). Each script:
- calls `house.apply()` first and sets no colour or font of its own;
- saves via `house.save(fig, "docs/experiments/active/modulator_clues/figures/algorithmic_null/<stem>")`. The page has **its own subfolder** (finding 7); the other page's 111 files in `figures/` are never read, listed or touched;
- writes `<stem>.data.txt`: used / available / % per subset, with a reason, **computed from the driver outputs**. Examples: probe rows used per store; predator-distance rows kept vs rows in episodes with no predator; truncated episodes excluded from the `steps_remaining` headline; checkpoints sampled out of the available ones; wake-up NaN reasons;
- prefixes the data statement with its `evidence_status` label;
- writes a `decision_rules:` line, either `<sha256> @ <commit>` or `none — no verdict is drawn`, and draws a verdict label only from `decision_rules.evaluate`.

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

Plus one new check: **decision-rule consistency.** Every figure's `data.txt` `decision_rules:` line must match the block at HEAD (sha256), or read `none — no verdict is drawn`. A mismatch is refused.

Replace the current blanket refusal (l.83–85) with these per-figure checks. Keep the F54, citation and token checks as they are.

The template's text and figure blocks are **content, not tooling**: `experiment-analyzer` adds them when results exist. This plan changes only the builder.

#### 11. `scripts/analysis/nmn/wakeup.py`, `untrained.py`, `grad_probe.py`, `run_wakeup.py` — new

- **`wakeup.py`** (pure numpy): `t_cross(x, m, *, mode, f, sustain, final_k, noise_k, min_noise_points, m0=None) -> Result(t, direction, reason, degenerate, m0, m_final, sigma_delta)`, `trailing_survival(...)`, `lag(...)`. `t` is a float step or `NaN`; `reason` is `None` or a sentence.
  **Tests** (`tests/analysis/test_nmn_wakeup.py`) use synthetic curves over 50 checkpoints (x = 1…50) plus a step-0 anchor, with fixed-seed Gaussian noise σ = 0.01 and test values `f = 0.5`, `sustain = 2`, `final_k = 3`, `noise_k = 3`, `min_noise_points = 5`. Expected outputs:

  | Curve | `fraction_of_rise` (signed) | `fraction_of_final` (literal) |
  |---|---|---|
  | **clean rise**: logistic 0 → 1, midpoint 20 | `t ∈ [19, 21]`, `rising` | `t ∈ [19, 21]`, not degenerate |
  | **falling**: logistic 1 → 0.2, midpoint 20 | `t ∈ [19, 21]`, `falling` (**not** 0) | `degenerate: true` |
  | **rise-then-return**: 0 → 1 by 20 → back to 0.0 ± noise from 35 | `NaN`, reason "net change within the measure's own noise band" | `degenerate: true` or `NaN` |
  | **flat in noise**: 0.5 + noise throughout | `NaN`, same reason | `degenerate: true` |
  | **initial-value trap**: 0.61 → 1.0, midpoint 20 | `t ∈ [19, 21]` | `t = 0`, `degenerate: true` |
  | **non-monotone rise**: clean rise with a single one-checkpoint spike past threshold at 8 | `t ∈ [19, 21]` (spike rejected by `sustain`) | same |
  | **too few points**: 6 checkpoints | `NaN`, reason "too few points to estimate noise" | — |

- **`untrained.py`**: `build(run_dir) -> (model, env_params)` along the key chain in §B2. It reads `seed` from the saved top level and cross-checks the `--seed` launch argument; a mismatch raises. The verification harness is `tests/analysis/test_nmn_untrained.py::test_matches_train_py_construction`. It is marked slow, and it runs the trainer's own `main()` up to network construction, as described in §B2. It is run for one ordinary and one modulated run of each study and recorded at Checkpoint 4.4.
- **`grad_probe.py`** (finding 5): at a checkpoint (or at the untrained network):
  - restore `model` **and `optimizer`** strictly from the checkpoint payload. At step 0, use a freshly initialised optimiser built as `train.py` builds it;
  - warm up the environment for `warmup_iters` rollouts without updates, because checkpoints carry no `env_state`;
  - collect one batch with `recurrent_ppo_trainer.collect_trajectories` using the run's own `return_mode`, `num_envs` and `sequence_length`, and build `PPOBatch` **exactly as `train_iteration` does** (l.544–579; reuse the code, do not re-derive it);
  - **(a) per-term split:** on the first update, `nnx.grad` of `policy_loss`, `vf_coef·value_loss` and `ent_coef·entropy_loss` separately, reporting `‖∇_mod‖²`, `‖∇_all‖²` and the share per term;
  - **(b) like-for-like with the log:** on a **throw-away deep copy** of model and optimiser, call the trainer's own `update_step` `K_epochs` times on that batch, exactly as `train_iteration` l.583–586 does, and report the mean of its returned `grad_norm` and `mod_grad_norm`. This is the quantity `train.py` l.1919–1923 logs. The copy is discarded, and the checkpoint on disk is opened read-only.
  - The output states: "(a) is the first update only (ratio = 1, before any in-iteration parameter change) and is biased upward relative to the log; (b) is the log's own definition; the world was re-warmed, not restored."
- **`run_wakeup.py --manifest --measures {grad_share,grad_probe,update_size,rho,swing,freeze}`**. It reuses `replay`, `mod_distribution`, `spectral_bound`, `freeze` and `ckpt_io` unchanged, and adds the step-0 point through `untrained.build` for the measures marked in §B2.

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
- `collect_trajectories.py` (now imports `eval_rollout` and the stage-reading logic);
- `eval_rollout.py` / `continual_forgetting_matrix.py` (new callers);
- `pilot_pick.py` and `continual_worlds/pilot_readout.py` (precedents factored, not imported; note only if imported);
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
- [ ] **R.1** `experiment-designer`'s `decision_rules` block is committed. Record its file, commit sha and commit time. Record the `generated_utc` of the first `run_similarity`/`run_decoding` output of any manifest, and show it is **later**. (Verifier checks both from `git log` and the output `manifest.json`.)
- [ ] **1.1** Record the golden parameter hashes on the **unmodified** commit (state its sha) *before* editing the network.
- [ ] **1.2** `tests/models/test_capture_activations.py` passes. All of `tests/models/` passes.
- [ ] **1.3** **Jaxpr identity (the speed gate).** Method, tested on 2026-09-29 on a synthetic 8-input / 16-hidden model: `g, s = nnx.split(model)`; wrap `f(s, x, h) = get_action_and_value_nnx(nnx.merge(g, s), x, h, key, eval_mode=False)` and `L(s, b) = ppo_loss_fn(nnx.merge(g, s), b, 0.2, 0.01, 0.5)[0]`. Hash `str(jax.make_jaxpr(f)(s, x, h))` and `str(jax.make_jaxpr(jax.grad(L))(s, per_env_batch))`, where `per_env_batch` is a `PPOBatch` of one env (`obs (T, D)`, `h_init` unbatched), matching the trainer's `vmap` over envs. Three separate processes gave identical hashes for the ordinary and a four-site FiLM `activation` model, for both functions. For this checkpoint, run it on the real ordinary and t16quad agent blocks, before and after the change; the `diff` must be empty. **Positive control:** a throw-away edit inserting `x = x * 1.0` into `_forward` must change the hash (then revert it), which shows the check can fail. Paste commands and hashes. A 200-iteration timing on one node is optional.
- [ ] **2.1** Pilot probe built. Its data counts (episodes per store, rows kept, predator-valid rows, truncated episodes) are printed and saved. The one-pass row-index assertions pass.
- [ ] **2.2** Self-replay agreement = 100% for each agent of the pair on its own store (near-ties ≤ 0.1% of rows, margin < 1e-4). Step-discontinuous alignment on sampled rows = 100%, including on action-change rows. Shift-by-one < 95% overall and < 5% on action-change rows, with both numbers recorded (≥ 95% overall = inconclusive, stop). Cross-agent agreement is recorded.
- [ ] **2.3** Chain assertions pass on both real pilot checkpoints for every row of the §4 table that applies. The max deviation per assertion is pasted.
- [ ] **3.1** `tests/analysis/test_nmn_representation.py` and `test_nmn_decision_rules.py` pass, including the leakage and clock tests.
- [ ] **3.2** Positive control: input-layer satiation R² ≥ 0.99. Shuffled-target R² ≤ 0.02. Same-agent CKA `isclose(1, atol=1e-12)`.
- [ ] **3.3** Untrained ordinary vs untrained t16quad, built from the same key: main-network parameters identical, with the modulator the only extra subtree.
- [ ] **3.4** Page builds with the pilot figures. The builder **refuses** a deliberately broken copy of the template (missing Axes; a 120-word howto; an inline `<svg>`; a stray file in `figures/algorithmic_null/`; a figure whose `decision_rules` hash differs from HEAD), and **ignores** a stray file in the parent `figures/`. Show the refusals.
- [ ] **4.1** `tests/analysis/test_nmn_wakeup.py` passes with every row of the §11 expected-output table.
- [ ] **4.2** `wandb_history.resolve_by_tag` reproduces §C's six folders. The gradient probe's **(b) full-iteration mean** of `modulator/grad_norm` lies within the 5th–95th percentile of logged values in a ±1-checkpoint window on ≥ 5 checkpoints per run, for ≥ 3 runs. This is a **sanity band**, not a proof of correctness: the world is re-warmed, and the log is one iteration's sample. Also record (a)/(b) side by side.
- [ ] **4.3** `freeze.verify_freeze_equivalence` passes for every run and checkpoint swept.
- [ ] **4.4** Untrained anchor: `test_matches_train_py_construction` passes (bitwise) for one ordinary and one modulated run of each study. For every B2 run, the own-seed reconstruction is closer to the first saved checkpoint than the reconstructions for two other seeds (cosine similarities recorded).
- [ ] **4.5** Stage 4 timing gate: seconds per item recorded, extrapolated wall-clock stated, and the thinning decision (if any) recorded before the full sweep.
- [ ] **5.1** Collector tests pass, including fingerprint tests (i)–(iii). On a real May-replication run, `stage_end:0` and `stage_end:3` resolve to checkpoints whose saved `stage` equals 0 and 3, and the `stage_end:3` world has `detection_range: 0`.
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
