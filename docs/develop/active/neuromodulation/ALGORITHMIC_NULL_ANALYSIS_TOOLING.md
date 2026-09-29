---
title: "Analysis tooling for 'What Both Agents Compute' — layer capture, stored-episode replay, similarity, decoding, modulator wake-up"
topic: neuromodulation
status: active
created: 2026-09-29
last_updated: 2026-09-29
---

# Analysis tooling for "What Both Agents Compute"

> **Status**: PLANNED — awaiting `plan-reviewer`, then user approval. Nothing is implemented.
> **Opened**: 2026-09-29
> **Related**: the published plan page [[algorithmic_null]] (`docs/experiments/active/modulator_clues/algorithmic_null.template.html`), its running list [[ALGORITHMIC_NULL_TODO]], the evidence file [[CROSS_STUDY_NULL_DOSSIER]], the earlier gradient audit [[TRAINING_HEALTH_AUDIT]], the collection pipeline [[TRAJECTORY_COLLECTION_PIPELINE]], the saved-config compatibility plan [[SAVED_RUN_CONFIG_COMPAT]], the modulation-site refactor [[MODULATION_SITE_REFACTOR]].

---

## Context

**What this is.** The project trains two kinds of recurrent agent: an ordinary one, and one with a small side network (the *modulator*) that rescales and shifts units inside the main network at every step. Across a month of studies they come out almost the same, in very different worlds. The page "What Both Agents Compute" reorders the open questions. First: **what do the two agents compute internally, and is it the same thing?** Second: **why does the modulator not help?** It lists the analyses that would answer them. None can run yet, because the tools do not exist. This plan specifies those tools. It covers analysis software only; it launches no training.

**What it builds.**
- A switch that makes the network also return its internal layer activity. With the switch off, nothing changes.
- A way to replay a stored episode's exact observations through any agent.
- Scripts that compare two agents layer by layer, and that read hunger, injury, predator distance and remaining survival time out of each layer.
- Measures of when, during training, the modulator starts to matter.
- Figure checks for the page builder.

**Why now.** One pair of agents from an earlier 16-world study already has stored episodes and loads under current code, so the tools can be built and checked on it today. A second study is still training: a replication of a May experiment with three seeds of each agent. It finishes in roughly 5–8 hours. It is the only design that can say whether two agents are "the same" by more than two ordinary agents from different seeds are. The plan is staged, so partial results reach the page before that training ends.

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

The network applies **symlog to its own input** (l.503: `x = sign(x)·log(|x|+1)`). The environment stays agent-agnostic. So a replay must feed the *raw* observation, not a symlogged one.

### B. The stored observation is exactly the network input (question 2 of the brief)

The trajectory collector's scan (`scripts/eval/traj_collect/traj_scan.py` l.158–201) **carries** the observation. `obs_noised` in row *t* is the same array passed to `policy_step(model, obs, h)`, which calls `model(obs, h)`, and the model applies symlog internally. The row convention (`src/utils/trajectory_store.py` header): row *t* holds the state at *t*, plus the action that *arrived* at *t*. So `action[t+1] = argmax(logits(obs_noised[t]))`. Row 0 has `action = -1`. The memory starts at `initial_state` (zeros) for every episode. Both studies store `obs_precision: float32` (verified in the level-05 manifest), so the stored input is lossless. Both studies also train with `perceptual_noise.enabled: false`, which makes `obs_noised == obs_true`. The tools still read `obs_noised`, because that column is the policy's input by definition.

**The correctness check follows directly.** Take the agent/checkpoint that generated a store (its manifest `checkpoint_path`). Replay it on that store: its argmax action at row *t* must equal the stored `action` at row *t+1*. Under teacher forcing a disagreement cannot compound, because the memory depends only on the stored inputs, never on the replayed action. So the agreement rate is a clean per-step statistic.

### C. Data inventory — what exists now vs later (question 3)

| Source | Stores on disk | Loads at HEAD? | Use |
|---|---|---|---|
| **Level-05 body-interactions factorial**: 16 worlds × {ordinary, modulated}, seed 42 | **All 32 complete** under `results/trajectories_l05body/<run>/<final ckpt>/<env_fp>/`: 200 shards each, 1,000,000 episodes, `seed_base 1000000` (same reset draws for both agents), float32, observation width 58, ~47 GB per store | **Yes.** `scripts/analysis/nmn/replay.load_agent` restored the w0000 pair strictly on 2026-09-29, and compat supplied nothing. The other 30 are re-checked in Stage 0 | Pilot (tool validation) for A1/A2. **B2 now**, on all 16 modulated runs (50 checkpoints each) |
| **May replication** (continual worlds, 5 stages alternating an *active* world, where the predator hunts, and a *passive* world, where it never hunts: `detection_range 0`, `hunt_stamina_threshold 1.1`, confined to the top-left) | **None.** Checkpoints so far: t16quad s42 has 23, up to episode 2,300,001 of 5,100,000; t1none s42 is at 3,200,017 | **Yes.** Both agent types restored strictly at HEAD on 2026-09-29. Observation width 52 in every stage (the stage configs differ only in `environment.entities`) | A1–A4 in full, after training. **Stage 1 (the first 1.5 M episodes) has already finished for all six runs**, so B2 on stage 1 and an early A3 at the end of stage 1 can run now (§Staging) |
| Wave 1/2 basic levels, bq2cover | stores exist (`results/trajectories_basicq2_*`) | per the TODO, yes; not re-verified here | not needed by this plan |
| **Site × input grid** (MC and GAE_NORM, both olfaction twins) | stores exist | **No.** Registry row L123: the saved configs lack keys that later became mandatory. Stage 1 of [[SAVED_RUN_CONFIG_COMPAT]] is unimplemented | **Excluded** |

Local WandB binaries exist for all six May-replication runs (`wandb/run-20260929_1536*`), and the level-05 study's `analysis_manifest.yaml` lists its WandB ids.

**Collection gap for the May replication (found during this investigation).** The collector always builds the world from a run's `models/config.yaml` (`collect_trajectories.py` l.699). For a continual run, that file is the stage-0 world. The per-stage worlds live in `models/stage_XX_<name>.yaml`, which carry no `agent:` block. The collector also cannot pick "the checkpoint at the end of stage *k*": `checkpoints:` is spec-wide (`run_collection.expand_cells` l.167), and each run's stage-end step number is different. Consequences:
- Stores at the final checkpoint are **correct by coincidence**. The last stage, `05_active`, has env sections identical to stage 0 (verified by a key-level diff of the five stage files).
- A store for the passive world, which A4 needs, **cannot be collected correctly today**. The collector would put a stage-3 checkpoint into the active world without any error.

`scripts/eval/eval_rollout.py::_resolve_continual_stage_config` (l.677) and `scripts/eval/continual_forgetting_matrix.py` (`read_saved_stage` l.86, `resolve_rows` l.102) already solve both problems for evaluation. This plan brings the same logic into the collector (File Changes §5).

**Launcher.** Only one finished-runs-only launcher exists: `scripts/analysis/studies/level05_body_interactions/launch_collection.py`. Despite its folder, it works for any spec. It copies a spec's scientific keys verbatim and detects finished runs from the log line `Training complete. Results saved to …` (`train.py` l.2763, printed by continual runs too). The May-replication logs are `logs/20260929_1536*.log`. Use it as is. Moving it is out of scope.

### D. B2 — what the trainer already logs (question 4)

`src/models/recurrent_ppo_trainer.py::update_step` (l.406–442) computes `grad_norm = optax.global_norm(grads)` and `mod_grad_norm = global_norm(grads['modulator'])`. Both are taken on the **total** loss and **before** clipping. `train.py` l.1919–1967 logs `loss/grad_norm` (a rolling-window spread) and `modulator/grad_norm` (a single-iteration sample, taken only at emission). This is where the training-health audit's numbers came from ([[TRAINING_HEALTH_AUDIT]] §4.2 cites `recurrent_ppo_trainer.py:385`; the line has since moved to l.421–431). The loss split (`ppo_loss_fn` l.173–208) is computed but never differentiated per term.

| B2 measure | Retroactive for loadable runs? | How |
|---|---|---|
| Gradient share, **total loss** `‖∇θ_mod‖² / ‖∇θ_all‖²` | **Yes, approximately**, from local WandB | ratio of the two logged norms. Caveat: `loss/grad_norm` is a window mean and `modulator/grad_norm` is a single sample, so the ratio is noisy per point. Smooth over checkpoint intervals |
| Gradient share **by loss term** (policy / value / entropy) | **Yes, at checkpoints only**, through a new *gradient probe*: at checkpoint *k*, collect one training-shaped rollout batch with the trainer's own `collect_trajectories`, then differentiate each term separately on the first minibatch of the first epoch (probability ratio = 1, so clipping is inactive) | new `grad_probe.py`. Checked against the logged `modulator/grad_norm` |
| Relative update size `‖Δθ_mod‖/‖θ_mod‖` vs main network | **Yes, at checkpoint resolution** (every 200 k episodes for level-05, every 100 k for the May replication), from saved weights | `ckpt_io.load_params`, CPU only |
| Output activity: contextual fraction ρ and gain swing | **Yes**, per checkpoint | ρ: `replay.rollout` → `mod_distribution.variance_split`. Swing: `spectral_bound` (weights only) |
| Freeze cost | **Yes**, at every 5th checkpoint | `freeze.apply_freeze` + `replay.rollout`, paired seeds (`freeze.paired_differences`) |
| Per-update gradient share by term; per-update update size | **Future runs only** | needs trainer logging. Deferred (§Deferred), not in this plan's scope |

The existing drivers (`run_mod_distribution.py`, `run_freeze.py`, `run_spectral_bound.py`) find runs through `ckpt_io.discover_runs`. Its regex (`ckpt_io.py` l.61) matches only the grid and basic-level names, not `l05body` or `cw_mayrep`. The new drivers therefore take an explicit **analysis manifest** that lists run directories. The old drivers are left untouched.

`pilot_pick.read_history` reads only `Episode/*` rows from the local WandB binary, so B2 needs a general reader for arbitrary keys (File Changes §7).

### E. The similarity measure robust to per-unit rescaling (A1) — choice: cross-network linear predictivity

Linear CKA is unchanged by rotations and by a uniform rescaling, but **not by per-unit rescaling**. The modulator's time-averaged gain is exactly a large fixed per-unit rescaling (the percept gain starts near 3: `percept_bias_init: 3.0`). So on a post-gain layer, CKA would report "different" for a difference the network can absorb for free. The freeze method's own docstring shows that the time-averaged gain and offset are gauge quantities (`freeze.py` "Interpreting a null").

**Chosen:** *linear predictivity*. Fit a ridge regression from agent A's layer to agent B's layer on training episodes, and score R² on held-out episodes, in both directions.
- It is unchanged by **any** invertible linear map of either layer, including per-unit rescaling. A pure constant-gain difference scores ≈ 1. What is left is the part of the modulation that varies with the situation, which is the part that matters.
- It reuses the A2 probe code (ridge + episode-grouped split + held-out R²). One tested component serves both analyses.
- Its asymmetry is informative: "A's layer contains B's information, but not the reverse".

**Not chosen:** SVCCA. It is also linear-invariant, but it depends on how many singular directions are kept (a free parameter that changes the answer). CCA on 128-wide layers overfits unless the rows vastly outnumber the units. And it has no held-out evaluation, so it would need its own episode-split machinery.

Linear CKA stays as the headline measure because it is the page's stated method. The two are reported side by side on every layer.

### F. Predator identity (A2)

The store manifest carries `animal_classes` (for example `["predator","predator","neutral","neutral"]`) and `animal_is_damaging`. The per-episode table carries `animal_active` (which slots exist in this episode). A predator is `animal_classes[i] == "predator"` and `animal_active[i]`. Distance is **Manhattan**, the metric the environment uses for hunt detection (`src/environment/core.py` l.614: `dist = sum(|hunt_pos − agent_pos|)`). Rows in episodes with no active predator are excluded from that target and counted in the data statement. Level-05 draws 0–2 predators per episode.

### G. Known bugs consulted (`bug-curator`, 2026-09-29)

- **L123** (saved configs stop loading): the reason the site × input grid is excluded.
- **L107** (the modulated gate-bias cell has a different init): **does not apply** to the runs used here. Both t16quad configs use `rnn_mechanism: activation`, so both agents build `nnx.GRUCell`. The D11 construction order then gives the modulated agent **exactly** the ordinary agent's starting weights at the same seed. Stage 3 verifies this, because A3's reading depends on it.
- **L114** (stale nested seed): read the top-level `seed:` key.
- **L138** (noise defaults off when the key is missing): the replay never rebuilds noise. It feeds stored `obs_noised`.
- **L159** (reset differs by at most 1 ULP across compilations, in `animal_property_sampled` only): irrelevant to teacher forcing. It is noted for the action-agreement tolerance.
- **L460/L461** (partial restore keeps random weights): every load goes through the strict `load_agent` check.
- There is no row on replay, trajectory stores, `scripts/analysis/nmn/`, gradient-norm logging, or construction order beyond L107/L389.

---

## Implementation Plan

### Design

```
 analysis manifest (YAML: runs, checkpoints, stores, probe sizes, evidence_status)
        │
        ├─► probe_set.py ── reads N episodes per listed store (decision rows 0..T-1)
        │                   → probe_<id>.npz : obs, (episode_seed, t) row index, targets
        │
        ├─► teacher_forced.py ── load_agent(run, ckpt) → nnx.jit scan of
        │        model.forward_with_activations over probe obs (memory reset at t=0)
        │        → acts_<run>__<ckpt>__<probe>.npz  (+ action-agreement report)
        │
        ├─► representation.py (pure numpy/sklearn): linear CKA, linear predictivity,
        │        episode-grouped ridge probes
        │        run_similarity.py (A1, A3, A4)   run_decoding.py (A2)
        │
        └─► wakeup.py (pure numpy) + grad_probe.py + wandb_history.py
                 run_wakeup.py (B2) — reuses replay.py, mod_distribution.py,
                 spectral_bound.py, freeze.py, ckpt_io.py
                              │
                              ▼
     figure scripts an01..an06 (house.apply / house.save / .data.txt)
                              ▼
     build_algorithmic_null_page.py (gains the §11 figure checks)
```

**Run-agnostic by construction.** Nothing names a study. Every run, checkpoint, store, probe size, layer list and threshold comes from a manifest, and every key is mandatory (`_req` → `ValueError`, the `_common.load_manifest` pattern). Agent roles (arm, seed) are read from each run's own saved `models/config.yaml` (top-level `seed:`, per L114; `agent.modulation.type`), not from directory names. A future run is analysed by writing a manifest.

**Intermediate capture — explicit method, not `nnx.sow` (question 1).** `nnx.sow` is the wrong tool in this codebase:
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

**Teacher-forced replay (question 2).** A new sibling, `scripts/analysis/nmn/teacher_forced.py`. `replay.py` stays the environment-rollout tool; it gains only a continual-aware world choice (§3). Per batch of probe episodes:
- Pad `obs_noised` rows `0..T−1` to `T_max` with a validity mask.
- Run `h0 = model.initial_state(B)`, then an `nnx.jit`-entered `jax.lax.scan` of `forward_with_activations` (the stale-view hazard documented in `replay.py`'s docstring).
- Keep only the requested layers at the probe's sampled rows (`rows_per_episode`, below), so memory stays bounded while the recurrence still runs over every step.

**Hard input checks before any forward pass:**
- The store manifest's `observation_breakdown` must equal `get_observation_breakdown(agent.env_params)` (same names, order, widths).
- `dims.D` must equal the model's `input_dim`.
- `schema_version == 1`.

**Action agreement.** Computed on every replay. If the replayed checkpoint is the store's generating checkpoint (`manifest.checkpoint_path` resolves to the same directory), the replay **fails** on any mismatch whose top-two logit margin is ≥ `1e-4`, or if near-ties exceed 0.1% of rows. Otherwise the agreement is recorded as a statistic: how often the other agent would have chosen the same action is itself an A1-adjacent result.

**Probe sets.** A probe set is `n_episodes_per_store` episodes drawn from each listed store, starting at block 0 so only the first shard is read. It stores:
- `obs` at the sampled rows;
- the full `obs_noised` sequences needed for replay;
- a row index `(store_id, episode_seed, t)`;
- targets: `satiation`, `injury_level`, `nearest_predator_manhattan` (with a validity mask), `steps_remaining = T − t`, `truncated` (`termination_reason == 1`, max steps reached).

Rows are subsampled per episode (`rows_per_episode`, seeded), and the whole episode is replayed. A probe set's sha256 over the row index is written into every activation file and re-checked on load, so activations from different probes can never be silently paired.

For **the May replication**, the probe for a world pools an equal number of episodes from all six agents' stores in that world. Every agent is judged on the same inputs, and no agent's own behaviour dominates. Results are also broken down by source store as a sensitivity check. The **pilot** pools the pair's two stores.

**A1 / A3 / A4 statistics.**
- Linear CKA uses the feature-space form ‖YᵀX‖²_F / (‖XᵀX‖_F‖YᵀY‖_F) on column-centred float64 features.
- Linear predictivity is ridge with the α-grid chosen by episode-grouped CV inside the training fold, reporting held-out R² (variance-weighted over output units) in both directions.
- Uncertainty comes from 200 bootstrap resamples **over episodes**.
- **Reference rows** make a number readable:
  - the probe's raw input (symlog of `obs`);
  - two *untrained* networks of the same architecture built from different keys (the floor for "similar by construction");
  - same-agent same-checkpoint (must be 1.0; a check, not a result).
- **A3 triangle** (May replication, per layer): ordinary–ordinary across seeds (3 pairs), modulated–modulated across seeds (3), modulated–ordinary same seed (3), modulated–ordinary different seeds (6). The fair test of "the same computation" is **modulated–ordinary at different seeds vs ordinary–ordinary at different seeds**. The same-seed cell measures what the shared start (D11) contributes.
- **A4**: for each agent, CKA/predictivity between consecutive stage-end checkpoints on a fixed world probe (both worlds), i.e. how far its processing moves per stage. "Moving together" is (i) the correlation across stage transitions between paired agents' movement, and (ii) modulated–ordinary similarity per stage against that stage's seed yardstick.

**A2 decoding.**
- Ridge regression (standardisation fitted on the training fold only).
- Split by `episode_seed` with `GroupShuffleSplit` (80/20, 5 repeats, fixed seed), so the **same split is used for every agent** on a probe and comparisons are paired.
- An assertion that no `episode_seed` appears in both folds.
- Targets: `satiation`, `injury_level`, `nearest_predator_manhattan` (valid rows only), `steps_remaining`. A sensitivity variant excludes `truncated` episodes, where the true remaining lifetime is censored.
- Controls: the input layer (a **positive control**: satiation is itself an observation channel, the `Satiation` sensor, so R² at the input must be ≈ 1; if not, targets and rows are misaligned), and **shuffled targets across episodes** (a negative control: R² ≤ ~0).

**B2 wake-up.**

| Measure | Source | Resolution |
|---|---|---|
| total-loss gradient share | local WandB, `modulator/grad_norm`² / `loss/grad_norm`² | log points, binned to checkpoint intervals |
| per-term gradient share | `grad_probe.py` at each checkpoint (or every *k*-th, manifest key) | checkpoints |
| relative update size | `ckpt_io.load_params` at consecutive checkpoints, modulator vs main | checkpoint intervals |
| contextual fraction ρ | `replay.rollout` (greedy, fixed seeds 90 000+) → `mod_distribution.variance_split` per site | checkpoints |
| gain swing | `spectral_bound` (weights only) | checkpoints |
| freeze cost | `freeze.apply_freeze` (gain frozen, offset frozen, separately) + `replay.rollout` + `freeze.paired_differences` | every 5th checkpoint |
| survival (for the plateau) | local WandB `Episode/Steps` weighted by `Episode/_window_n` (the `survival_tenths.py` convention) | log points |

**Wake-up lag and a definitional trap.** The page defines `t_wake` as the first checkpoint where a measure reaches 50% of its final value. Taken literally, this is **zero by construction for any measure that already starts above half its final value**. The gain swing, for example, is known to grow only about 1.64× over training, so it starts at about 61% of its final value. `wakeup.py` therefore implements two definitions, selected by a mandatory manifest key `threshold_mode`:
- `fraction_of_final` (the page's literal definition);
- `fraction_of_rise`: first checkpoint where `m ≥ m₀ + f·(m_final − m₀)`.

In both, "final" is the mean of the last 3 checkpoints, and a crossing counts only if it holds for `sustain` consecutive checkpoints (mandatory key). The same applies to `t_plateau`, with f = 0.9 on trailing-window survival. The report shows both definitions. **Which one the page headlines is a decision for the user and `experiment-analyzer`, not this plan.**

For continual runs, B2 uses **stage 1 only** (episodes 0–1.5 M, the only stage trained from scratch), with the stage-local final value.

### Staging, and the verifiable check at each stage (question 6)

| Stage | When | Work | Verifiable check (must pass to proceed) |
|---|---|---|---|
| **0 — preflight** | now, CPU, no code change | Strict `load_agent` on every run in both manifests. Key-level diff of the May replication's stage files. Read `observation_breakdown` from one store of each study | All loads pass. Active stages' env sections equal `config.yaml`'s. Store/model breakdown equal. Result recorded in the Implementation Report |
| **1 — capture switch** | now | File Changes §1–2 | `tests/models/test_capture_activations.py` passes. **The jaxpr of the training loss and of `get_action_and_value_nnx` is textually identical before and after** (Checkpoint 1.3). The golden parameter hash is unchanged. Existing `tests/models/` pass |
| **2 — replay + pilot probe** | now | §3–4. Probe on the level-05 **w0000 pair** (1,000 episodes from block 0 of each store) | Each agent on its **own** store: 100% action agreement (near-tie allowance only). **Shift-by-one control fails** (obs row *t* against action row *t*: agreement well below the true alignment). Same-agent CKA = 1.0 |
| **3 — pilot A1/A2 + figures** | now | §6, §8–9. Figures `an01`–`an03` in *pilot* mode. Builder §11 checks (§10) | Unit tests pass. Positive control: satiation R² at the input ≥ 0.99. Negative control: shuffled R² ≤ 0.02. Untrained networks built with the pair's seed have **identical main-network parameters** for both agent types (confirms the shared start). Page builds. `artifact-format-reviewer` passes. Every pilot figure's data statement says **"tool validation — the two agents share seed 42; not evidence"** (emitted from the manifest's `evidence_status: pilot`) |
| **4 — B2 on existing runs** | now, in parallel with 3 | §7, §11. All 16 level-05 modulated runs, plus **May-replication stage 1** (all six runs are past episode 1.5 M) | Gradient probe: the total-loss modulator gradient norm at checkpoint *k* lies within the 5th–95th percentile of logged `modulator/grad_norm` in a ±1-checkpoint window (checked on ≥ 5 checkpoints per run). Freeze equivalence: `freeze.verify_freeze_equivalence` passes before each sweep. ρ closure identity (asserted in `mod_distribution`) holds |
| **4b — early yardstick (optional)** | now | Collect the **stage-1-end** checkpoint of all six May-replication runs (world = stage 0 = `config.yaml`, correct with the current collector), 10,000 episodes each, **one spec per run with an explicit step** through `run_collection.py`. Then A1/A3 at the end of stage 1 | As Stage 2 for every store. A3 figure in *interim* mode ("end of stage 1 of 5") |
| **5 — collector continual-awareness** | now, so it is ready when training ends | §5 | New tests in `tests/test_trajectory_collection.py` pass. On a real May-replication run, `stage_end:0` resolves to a checkpoint whose saved `stage` field is 0, and the passive-stage resolution yields a config with `detection_range: 0` |
| **6 — May replication, full** | after training (~5–8 h) | Launch collection of `final` + `stage_end:3` (the last passive-world stage end) for all six runs via the existing finished-runs-only launcher. Then A1–A4 and B2 stage 1 are final | Every store validates (`validate_store_structure/shapes/draws`). Each store's `resolved_env_config` names the right world. Action agreement 100% per generating agent. The figures switch to `evidence_status: evidence` |

What the page can carry when:
- **After Stage 3:** pilot A1/A2 figures, labelled as tool validation.
- **After Stage 4:** real B2 results (level-05 ×16, May stage 1 ×3 per arm).
- **After Stage 4b:** an interim A3.
- **After Stage 6:** A1–A4 on the May replication.

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

- **Bitwise equality:** inside `nnx.jit`, over a 20-step scan with random inputs, `forward_with_activations(...)[:4]` equals `__call__(...)`. Configurations: ordinary hierarchical + LayerNorm; the modulated four-site FiLM `activation` config (the t16quad agent block); FiLM `gate_bias`; flat encoder mode; `PreActivation`.
- **Reconstruction (bitwise):**
  - `logits == actor_fc2(acts["actor.out"])` and `value == critic_fc2(acts["critic.out"])`;
  - modulated `acts["actor.mod"] == z_actor·acts["actor.raw"] + z_actor_add`;
  - ordinary `acts["rnn.out"] == acts["rnn.state"]`.
- **No state leak:** the `nnx.state(model)` path set and shapes are identical before and after a capture call.
- **Construction pinned:** the sha256 of the flattened parameter tree of `ActorCriticRNN(..., rngs=nnx.Rngs(PRNGKey(0)))` equals a golden hash for the ordinary and the t16quad configs. **The developer records the golden values by running the hash on the pre-change commit, before editing the network**, and states the commit in the test.
- **Key set:** exactly the documented keys per configuration. A `.mod` key exists iff that site is enabled.

#### 3. `scripts/analysis/nmn/replay.py` — continual-aware world (small)

`load_agent(models_dir, step=None)`: for a run whose `models/` holds `schedule.yaml`, build `env_params` from the checkpoint's **own stage** file, reusing `scripts.eval.eval_rollout._resolve_continual_stage_config(cfg_path, ckpt_dir)`. The agent block still comes from `config.yaml`. Print the resolved world. `LoadedAgent` gains `env_config_path: str`. This matters for ρ and freeze-cost rollouts at stage-*k* checkpoints. Teacher forcing only needs the observation layout, which is identical across stages.

#### 4. `scripts/analysis/nmn/teacher_forced.py` + `scripts/analysis/nmn/probe_set.py` — new

- `probe_set.build(stores: list[Path], n_per_store, rows_per_episode, seed) -> Probe`:
  - reads the step and episode shards from block 0 upward with pyarrow;
  - uses decision rows `0..T−1` (the `_common.read_decision_rows` convention);
  - derives targets (§F for predators, via the manifest's `animal_classes` and the episode `animal_active`);
  - writes `probe_<id>.npz` and `probe_<id>.json` (sources, counts, sha256 of the row index).
- `teacher_forced.replay(agent, probe, layers, batch_size) -> Activations` plus an agreement report (§Design). The npz is keyed by layer name and carries the probe hash.

#### 5. `scripts/eval/traj_collect/collect_trajectories.py` — continual-aware collection

- `resolve_checkpoint(run_dir, which)` accepts `stage_end:<k>`. That is the first saved checkpoint at or after `schedule.yaml`'s `episode_boundaries[k]`, whose saved `stage` field must equal *k* (reuse the `continual_forgetting_matrix.read_saved_stage` logic; a mismatch is an error).
- For a run with `schedule.yaml`, the **environment** config is the checkpoint's own stage file (via `_resolve_continual_stage_config`). The **agent** block is still read from `config.yaml`.
- `apply_saved_config_compat` and `assert_scene_unambiguous` run on the stage config.
- The manifest's `resolved_env_config` / `env_fp` then describe the stage world. **No schema change:** no new column, `SCHEMA_VERSION` stays 1. `train_config_mtime` keeps reading `config.yaml`.
- Non-continual runs: behaviour unchanged, verified by the existing tests.
- `run_collection.py` passes the checkpoint string through unchanged (l.167). Confirm its spec validation accepts `stage_end:<k>`.

**Tests** (`tests/test_trajectory_collection.py`, extended):
- on a synthetic continual `models/` fixture (`schedule.yaml`, two stage files, two checkpoint dirs with a saved `stage`), `stage_end:1` resolves correctly and a mismatched `stage` raises;
- the environment config chosen for a stage-1 checkpoint is the stage-1 file;
- `final` on a non-continual fixture is unchanged.

#### 6. `scripts/analysis/nmn/representation.py` — new, pure numpy + sklearn

`linear_cka(X, Y)`, `linear_predictivity(X, Y, groups, split)`, `ridge_probe(X, y, groups, split)`, `episode_split(groups, n_repeats, test_frac, seed)` (asserts disjointness), `bootstrap_over_groups(fn, groups, n)`. Everything in float64.

**Tests** (`tests/analysis/test_nmn_representation.py`):
- `CKA(X,X)=1`;
- CKA is invariant to orthogonal rotation and isotropic scale;
- **CKA drops under a per-unit rescaling** (documents the motivating caveat);
- predictivity ≈ 1 under a per-unit rescaling and under a random invertible map, and ≈ 0 for independent noise;
- **leakage test:** a feature that encodes the episode identity plus a per-episode constant target gives high R² under a row-level split and ≈ 0 under `episode_split`. This proves the split does its job.

#### 7. `scripts/analysis/nmn/wandb_history.py` — new

`read_keys(wandb_dir, keys, allow_truncated) -> dict[key, (x, y)]`. A general local-binary reader, factored from `pilot_pick.read_history`, which is **not** modified. It returns each key with the history record's step fields. The developer must establish the join from a logging record to an episode count. Does the record that carries `loss/grad_norm` also carry `Episode/Number` or `iteration`? If only `iteration` is present, convert with the run's own `num_envs` and rollout length, state the conversion in the output, and never assume it. `wandb_dir_for` is reused through `importlib` (the `survival_tenths.py` precedent).

#### 8. `scripts/analysis/nmn/run_activations.py`, `run_similarity.py`, `run_decoding.py` — new drivers

Each takes `--manifest <yaml>`. Outputs go under `results/analysis/algorithmic_null/<manifest name>/` (JSON + CSV + npz), each with a `manifest.json` recording the git sha, the input manifest, the probe hashes and the package versions.

**Manifest schema (all keys mandatory):**
- `name`, `evidence_status` (`pilot|interim|evidence`), `out_root`;
- `runs: [{label, path, checkpoints: [final | <int> | stage_end:<k>]}]`;
- `probes: [{id, stores: [<store dir>], n_per_store, rows_per_episode, seed}]`;
- `layers`, `comparisons` (`auto` = every pair of runs, or an explicit list);
- `bootstrap_n`, `probe_split: {n_repeats, test_frac, seed}`, `ridge_alphas`, `untrained_reference_keys`.

The two manifests (`docs/experiments/active/modulator_clues/algorithmic_null_pilot.yaml`, `…_mayrep.yaml`) are written by the developer to this schema, following the `level05_body_interactions/analysis_manifest.yaml` precedent. `experiment-designer` may review them.

#### 9. Figure scripts — new, `scripts/analysis/studies/modulator_clues/an0N_*.py`

One script per figure: `an01_similarity_layers` (A1, CKA and predictivity per layer pair), `an02_decoding_profiles` (A2), `an03_seed_yardstick` (A3 triangle), `an04_across_worlds` (A4), `an05_wakeup` (B2: four measures plus survival, wake and plateau marked), `an06_freeze_over_training` (B2 freeze subset). Each script:
- calls `house.apply()` first and sets no colour or font of its own;
- saves via `house.save(fig, "docs/experiments/active/modulator_clues/figures/<stem>")`;
- writes `<stem>.data.txt`: used / available / % per subset, with a reason, **computed from the driver outputs**. Examples: probe rows used per store; predator-distance rows kept vs rows in episodes with no predator; truncated episodes; checkpoints sampled out of the available ones;
- when the manifest says so, prefixes the data statement with its `evidence_status` label.

Scripts before Stage 6 run on pilot, interim or partial manifests. The same scripts rerun on the evidence manifest.

#### 10. `scripts/analysis/studies/modulator_clues/build_algorithmic_null_page.py` — add the §11 figure checks

Copy the figure block from `scripts/analysis/tutorials/loop_graph_engineering/build_page.py` l.101–139:
- one `<figure>` at a time (register F16);
- `<img data-fig>` required; `<svg>`/`<canvas>` inside a figure refused (2.7);
- `<b>Axes.</b>` in the figcaption (11a); a `{{DATA:stem}}` token (11b);
- a `howto` block of 150–250 words (11c);
- a generating script at `HERE/<stem>.py`; png/svg/pdf/data.txt under `DOC/figures/`; no duplicates; no unused figures on disk; base64 embed.

Three adjustments:
- **Count words excluding the `<p class="eyebrow">…</p>` element**, rather than the loop page's fixed `− 3`. The eyebrow here reads "How it is computed" (4 words), so a fixed offset would miscount.
- **Require that eyebrow text** to be exactly "How it is computed".
- **Pull the house figure viewer** (`<div class="lb fit" id="lb" …</script>`) into a `{{HOUSE_VIEWER}}` token (guide 2.6), next to the existing `{{HOUSE_SCRIPT}}`.

Replace the current blanket refusal (l.83–85) with these per-figure checks. Keep the F54, citation and token checks as they are.

The template's text and figure blocks are **content, not tooling**: `experiment-analyzer` adds them when results exist. This plan changes only the builder.

#### 11. `scripts/analysis/nmn/wakeup.py`, `grad_probe.py`, `run_wakeup.py` — new

- `wakeup.py` (pure numpy): `t_cross(ckpts, values, f, mode, sustain, final_k=3)`, `trailing_survival(...)`, `lag(...)`.
  **Tests** (`tests/analysis/test_nmn_wakeup.py`) cover synthetic curves, including the trap: a curve starting at 0.61 of its final value gives `t_wake = 0` under `fraction_of_final` and a later crossing under `fraction_of_rise`. They also cover non-monotone curves with `sustain`.
- `grad_probe.py`: at a checkpoint, warm up the environment for `warmup_iters` rollouts without updates (so episodes are mid-life, as in training). Then collect one batch with `recurrent_ppo_trainer.collect_trajectories` using the run's own `return_mode`, `num_envs` and `sequence_length`, and build the minibatch **exactly as `train_iteration` does** (the developer reads l.444+ and reuses its code, not a re-derivation). Finally take `jax.grad` of `policy_loss`, `vf_coef·value_loss` and `ent_coef·entropy_loss` separately, and report `‖∇_mod‖²`, `‖∇_all‖²` and the share per term.
- `run_wakeup.py --manifest --measures {grad_share,grad_probe,update_size,rho,swing,freeze}`. It reuses `replay`, `mod_distribution`, `spectral_bound`, `freeze` and `ckpt_io` unchanged.

#### 12. Spec: `configs/trajectory_collection/continual_mayrep_probes.yaml` — new (authored by `experiment-designer` or the developer; config ownership rules apply)

`name: continual_mayrep_probes`, `algo: rppo`, `out_root: results/trajectories_cw_mayrep`, `episodes: 10000`, `seed_base: 1000000`, `checkpoints: [final, "stage_end:3"]`, `obs_precision: float32`, `device: gpu`, `batch_size: 5000`, `shard_episodes: 5000`, `blocks_per_cell: 2`, `npar: 1`, and six `runs` entries (labels `{ordinary,modulated}_s{42,43,44}`).

Launch after Stage 5 with:

```
launch_collection.py configs/trajectory_collection/continual_mayrep_probes.yaml --logs-glob 'logs/20260929_1536*.log' --nodes <live-free>
```

Nodes are chosen from `gpu-status` plus the diary (project rule). Size: about 0.47 GB per store × 12 ≈ 5.6 GB, extrapolated from the level-05 stores' 47 GB per 1 M episodes; the developer records the measured bytes.

The optional Stage 4b uses six one-run specs, `…_stage0end_<label>.yaml`, each with the run's explicit stage-0-end step.

#### 13. `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` — same change (maintenance contract)

Add rows for every new file:
- `teacher_forced.py`, `probe_set.py`, `representation.py`, `wandb_history.py`, `wakeup.py`, `grad_probe.py`, `run_activations.py`, `run_similarity.py`, `run_decoding.py`, `run_wakeup.py`: callers, depth, and `src/` imports. `teacher_forced.py` and `grad_probe.py` join `replay.py` as the `nmn/` files that import `src/`.
- the six `an0N_*.py` figure scripts.

Update the rows for:
- `replay.py` (now imports `scripts.eval.eval_rollout`);
- `collect_trajectories.py` (now imports `eval_rollout` and the stage-reading logic);
- `eval_rollout.py` / `continual_forgetting_matrix.py` (new callers);
- `pilot_pick.py` (new `importlib` caller);
- `build_algorithmic_null_page.py` (now reads `figures/` and runs the §11 checks).

Also update `scripts/eval/traj_collect/README.md` (a `stage_end:<k>` selector and continual worlds, one short section).

**Not touched:** `train.py`, `recurrent_ppo_trainer.py`, `neuromodulator.py`, `ckpt_io.py`, `mod_distribution.py`, `freeze.py`, `spectral_bound.py`, `run_*` legacy drivers, the trajectory-store schema, `configs/environment/`. No config key is added to any training config, so neither `CONFIG_GUIDE.md` nor `CONFIG_CRITICAL_SETTINGS.md` changes.

### Deferred (not in scope; needs its own approval)

**Trainer logging for future runs.** Two quantities:
- per-term modulator gradient norms (three extra `global_norm` calls on per-term grads, which needs three extra backward passes or `jax.vjp` reuse, so it has a real speed cost);
- per-update ‖Δθ_mod‖/‖θ_mod‖ (cheap: the params before and after the optimiser step are both in scope in `update_step`).

This belongs in a separate plan with a speed measurement. It would make B2's per-update resolution available to the "stronger start" runs of B1.

---

## Checkpoints

- [ ] **0.1** Strict `load_agent` succeeds for all 32 level-05 runs at their store checkpoints, and for all six May-replication runs at the latest checkpoint. The list is pasted into the Implementation Report.
- [ ] **0.2** The May replication's five stage files: the env sections of `01/03/05_active` are identical to `config.yaml`'s; `02/04_passive` differ only in `environment.entities`.
- [ ] **1.1** Record the golden parameter hashes on the **unmodified** commit (state its sha) *before* editing the network.
- [ ] **1.2** `tests/models/test_capture_activations.py` passes. All of `tests/models/` passes.
- [ ] **1.3** Dump `jax.make_jaxpr` text for (a) `get_action_and_value_nnx` and (b) `ppo_loss_fn` on a fixed dummy batch, for the ordinary and the t16quad model, **before and after** the change. `diff` must be empty. Paste the command and the result. This is the speed gate: an identical program cannot be slower. A 200-iteration timing on one node is optional.
- [ ] **2.1** Pilot probe built. Its data counts (episodes per store, rows kept, predator-valid rows, truncated episodes) are printed and saved.
- [ ] **2.2** Self-replay agreement = 100% for each agent of the pair on its own store (near-ties ≤ 0.1% of rows, margin < 1e-4). The shift-by-one control **fails**. Cross-agent agreement is recorded.
- [ ] **3.1** `tests/analysis/test_nmn_representation.py` passes, including the leakage test.
- [ ] **3.2** Positive control: input-layer satiation R² ≥ 0.99. Shuffled-target R² ≤ 0.02. Same-agent CKA = 1.0 exactly.
- [ ] **3.3** Untrained ordinary vs untrained t16quad, built from the same key: main-network parameters identical, with the modulator the only extra subtree.
- [ ] **3.4** Page builds with the pilot figures. The builder **refuses** a deliberately broken copy of the template (missing Axes; a 120-word howto; an inline `<svg>`); show the three refusals.
- [ ] **4.1** `tests/analysis/test_nmn_wakeup.py` passes, including the initial-value trap.
- [ ] **4.2** Gradient probe vs logged `modulator/grad_norm`: within the 5th–95th percentile window on ≥ 5 checkpoints per run, for ≥ 3 runs.
- [ ] **4.3** `freeze.verify_freeze_equivalence` passes for every run and checkpoint swept.
- [ ] **5.1** Collector tests pass. On a real May-replication run, `stage_end:0` and `stage_end:3` resolve to checkpoints whose saved `stage` equals 0 and 3, and the stage-3 world has `detection_range: 0`.
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
