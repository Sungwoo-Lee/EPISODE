---
title: "Exclusive modulator input — hide named sensors from the main network"
topic: neuromodulation
status: active
created: 2026-10-07
last_updated: 2026-10-07
aliases: [exclusive_modulator_input]
---

# Exclusive modulator input — hide named sensors from the main network

> **Status**: PLANNED (awaiting user decisions D1–D4 and plan review)
> **Opened**: 2026-10-07
> **Related**: [[MODULATION_SITE_REFACTOR]] (Part B: what the modulator reads) · [[CROSS_STUDY_NULL_DOSSIER]] · [[20260929_nmn_null_algorithmic_film_conditions]] (§3.1, §5.1) · [[SAVED_RUN_CONFIG_COMPAT]] · [[ALGORITHMIC_NULL_ANALYSIS_TOOLING]]

---

## Context

The recurrent PPO agent can carry a small second network, the **modulator**, that reads the
agent's senses and rescales the main network's neurons at every step (FiLM: a per-neuron gain
and offset). Today a config can already choose *which* senses the modulator reads. What it
cannot do is take a sense **away from the main network**: the main network always sees every
sensor, including the injury signal ("Interoceptive Nociception"). So the modulator never
carries information the main network lacks, and across a month of studies the modulated agent
has tied the ordinary agent. A recent critique of that null result names this as one candidate
cause — the modulator's input is *redundant* — and proposes the test: give the body signals
**only** to the modulator ("exclusive" input) and compare.

This plan adds one config key, a list of sensors **withheld from the main network**. Those
columns are removed from the main network's input (its per-sense encoder simply has no branch
for them), while the modulator still reads them. With the list empty, the network is exactly
today's network — same parameters, same computation, bit for bit — and every finished run
reopens unchanged. The same key works on an ordinary (unmodulated) agent, which gives the
matched control: an ordinary agent that is blind to the same sensors. The environment, the
rollout buffer, the trajectory store and the recordings are untouched: the agent still
*receives* the full observation; the withholding happens inside the network.

Four decisions are left to the user (end of this doc): whether the key is allowed with the
modulator off (D1), which baseline the experiment uses (D2), how the key is rolled out to the
existing agent configs (D3), and whether to add a restore-time shape check (D4).

---

## Analysis

### A1. Where the observation goes today

`ActorCriticRNN._forward` (`src/models/recurrent_ppo_network.py:556–697`):

1. `x = symlog(x)` (line 579) — the full observation, width `input_dim`.
2. Modulated path: `mod_in = x` or `x[..., mod_input_idx]` (lines 587–590) — Part B's input
   slice, resolved by `_resolve_modulator_input_indices` (lines 27–83) into a static tuple of
   ints stored on the module.
3. `self.obs_encoder(x, ...)` / `forward_with_modulation(x, ...)` (lines 593–607 modulated,
   675–681 unmodulated) — the **full** `x` goes to the main network's encoder.

`ObservationEncoder.__init__` (lines 149–175) is built from `observation_breakdown`:
- **hierarchical** mode: one unimodal branch per sensor name (`GroupedMLP(len(names), max_in, …)`),
  each sensor zero-padded to `max_in`, then a multimodal hub of input width
  `len(names) * hidden_size`;
- **flat** mode: one `nnx.Linear(input_dim, hidden_size)`.

So the encoder's *structure* is a function of the breakdown it is handed. That is the hook.

### A2. Removing vs. zeroing the withheld columns

| | **Remove** (recommended) | Zero |
|---|---|---|
| What the main network has | no branch / no input weights for the sensor | a branch that always receives 0 |
| Hierarchical encoder | `n−k` groups, hub input `(n−k)·hidden`; `max_in` recomputed | `n` groups; the dead branch emits a constant `relu(LN(bias))` |
| Interaction with encoder-site FiLM | none | the encoder-stage gain/offset is broadcast across **all** branches (`gamma1[..., None, :]`, line 275), so the dead branch becomes an extra constant-input channel the modulator can write into — capacity the blinded control lacks |
| Flat encoder | `Linear(D−w, H)` | `Linear(D, H)`, `w` rows get zero gradient |
| LayerNorm | unaffected (normalises over `hidden_size`, not over senses) | unaffected |
| Checkpoint safety | parameter shapes differ, so an exclusive checkpoint cannot be silently restored into a non-exclusive model (or vice versa) | shapes identical — a checkpoint restored with the wrong key value **loads silently** and evaluates the wrong agent |
| Parameter count vs. full agent | smaller by one branch (hier.) / `w·H` weights (flat) | identical |

Removal is chosen: "the main network cannot use the signal" is then structural, not a
property of a value that happens to be zero, and a key/checkpoint mismatch fails instead of
evaluating silently. The parameter-count difference against a full-sight agent is inherent to
the question and is the same difference the blinded ordinary control has.

### A3. Static-ness under JIT

The withheld set is fixed for the life of a run. As with `mod_input_idx`, it is resolved once
in `__init__` into a plain tuple of Python ints (`self.task_input_idx`) plus a plain dict
(`self.task_breakdown`), both graphdef metadata — never `nnx.Param`/`nnx.Variable`, never
traced, never checkpointed. With an empty list, a Python-level `if` skips the gather entirely,
so the traced program is op-for-op today's program (the same pattern as `_mod_input_is_all`).

### A4. Saved runs and the no-fallback rule

The key is **mandatory** in every live rPPO agent config (missing → named `ValueError`). Every
run on disk predates the key, so the tools that rebuild a model from a run's *saved*
`models/config.yaml` must supply `[]` for it — in memory, refusing any source under `configs/`,
exactly like `translate_legacy_modulation_config` and `apply_saved_config_compat` do. `[]` is a
claim about what the old code did: the main network saw every sensor. That holds for every run
ever trained.

`apply_saved_config_compat` cannot carry this row: it is env-scoped, and several callers
(`untrained.py:89–96`, `replay.py`) build `EnvParams` from the compat'd copy but read the agent
block from the **untouched** dict. The agent-side shim already exists —
`src/models/modulation_compat.py` — and is already called at the model-build boundary of the
saved-config sites. It gets a sibling function.

**Running jobs.** The modulator capacity grid (9 runs, launched 2026-10-07) runs from the shared
folder. Its in-training checkpoint eval spawns `scripts/eval/experiment_eval_checkpoint.py →
eval_rollout.py` **without** `--agent_config`, i.e. the saved-config branch, importing whatever
`src/` is on disk at that moment. The mandatory read and the compat wiring therefore have to land
in **the same commit**, or those jobs' checkpoint evals fail from that commit on.

### A5. Who else assumes the encoder sees every sensor

| Consumer | Effect of an exclusive run | Action |
|---|---|---|
| Env, rollout buffer, PPO update, trajectory store, `.rec.gz` recordings, dashboards | none — they hold the full observation; the gather is inside `_forward` | none |
| `scripts/analysis/nmn/teacher_forced.py:_chain` (lines 75–127) | recomputes the encoder from the **full** `obs` using `enc.breakdown` → with a reduced breakdown it would slice the **wrong columns silently** | route through the model's own gather (C3) |
| `scripts/analysis/nmn/run_activations.py:_layer_widths` (217–223) | feeds a full-width zero obs and reads widths off the captures → correct automatically | none |
| `scripts/analysis/nmn/run_similarity.py:descriptive` (244–278) | CKA between `enc.uni.*` of an exclusive and a redundant run compares different sense sets; runs, but the per-sense comparison is not like-for-like | doc caveat only (experiment-analyzer's concern) |
| `scripts/analysis/nmn/ckpt_io.py:_slice_from_config` (63–90) | labels arms by `input_sensors` only → an exclusive run would be labelled like a redundant one | refuse a non-empty withheld list until a label exists (C3) |
| `scripts/analysis/obs_manipulation/run.py` | manipulates observation columns; a withheld column then reaches only the modulator — valid, interpretation differs | none (analysis note) |
| `save_snapshot.py` | already unusable (hand-builds `temp_clip`, which the model rejects; passes no `encoding_config`) | untouched; noted |
| Dreamer (`src/algorithms/dreamer_srl/`) | does not use `ActorCriticRNN`; key never read | none — verify no file there changes |

---

## Implementation Plan

### Design

**Key** (agent level, so it works with the modulator on or off):

```yaml
agent:
  task_withheld_sensors: []          # sensors the MAIN network does not see; [] = sees every sensor
  # task_withheld_sensors: ["Interoceptive Nociception"]   # exclusive-input arm
```

Read inside `ActorCriticRNN.__init__` from `encoding_config` (every construction site already
passes the whole `agent` dict there — `train.py:1257`, `evaluation.py:401`, `eval_rollout.py`,
`collect_trajectories.py`, `replay.py:133`, `untrained.py:108`), so no call-site signature
changes.

**Validation** (all named `ValueError`s, each listing the sensors available under the run's
environment config):
1. Missing or `null` key → error (no fallback).
2. Not a list (e.g. a string, including `"all"`) → error.
3. Unknown name → error (same message discipline as `_resolve_modulator_input_indices`).
4. Duplicate name → error.
5. Every sensor withheld → error (the main network would have no input).
6. **Modulator on:** every withheld sensor's columns must be inside `mod_input_idx` → otherwise
   error: "withheld from the main network and not read by the modulator — the agent would be
   blind to it".
7. **Modulator off, list non-empty:** see **D1** (recommended: allowed — this *is* the blinded
   ordinary control — with a loud startup banner line).

**Forward:** after symlog, the modulator gathers from the full `x` as today; the main network
gets `x_task = x[..., task_input_idx]` (skipped when nothing is withheld). Encoder built from
`task_breakdown` and `task_input_dim`.

### File Changes

#### C1 — `src/models/recurrent_ppo_network.py`

**(a) New module-level resolver** after `_resolve_modulator_input_indices` (after line 83):

```python
def _resolve_task_withheld_sensors(withheld, observation_breakdown: dict,
                                   mod_input_idx, modulation_enabled: bool):
    """Resolve `agent.task_withheld_sensors` -> (task_input_idx, task_breakdown).

    Plain-language purpose: names sensors the MAIN network must not see. Their columns are
    removed from the main network's input (the encoder gets no branch for them); the
    modulator still reads them. Returns (None, observation_breakdown) when nothing is
    withheld, so the caller can skip the gather and build today's encoder exactly.
    Both return values are plain Python (tuple of ints, dict) -> static graph metadata.
    """
    # validation rules 2-7 of the plan's Design section; offsets computed exactly as in
    # _resolve_modulator_input_indices (factor the offset walk into a shared helper
    # `_sensor_offsets(observation_breakdown)` used by both resolvers).
```

**(b) `ActorCriticRNN.__init__`** — after the modulation `if/else` block (after line 418, so
`self.mod_input_idx` exists) and before the encoder is built (line 444):

```python
if encoding_config is None or encoding_config.get('task_withheld_sensors') is None:
    raise ValueError(
        "Strict Config: agent.task_withheld_sensors is required but missing. Use [] for "
        "a main network that sees every sensor. See "
        "docs/develop/active/neuromodulation/EXCLUSIVE_MODULATOR_INPUT.md")
self.task_withheld_sensors = tuple(encoding_config['task_withheld_sensors'])
self.task_input_idx, task_breakdown = _resolve_task_withheld_sensors(
    encoding_config['task_withheld_sensors'], observation_breakdown,
    self.mod_input_idx, self.modulation_enabled)
self._task_input_is_all = self.task_input_idx is None
task_input_dim = input_dim if self._task_input_is_all else len(self.task_input_idx)
```

and change the encoder construction (lines 444–446):

```python
# BEFORE:
self.obs_encoder = ObservationEncoder(
    input_dim, hidden_size, observation_breakdown, encoding_config, rngs)
# AFTER:
self.obs_encoder = ObservationEncoder(
    task_input_dim, hidden_size, task_breakdown, encoding_config, rngs)
```

`NeuromodulatorRNN` keeps `obs_breakdown=observation_breakdown` (it does not use it) and
`obs_dim=len(self.mod_input_idx)` — unchanged.

**(c) One helper method, used by `_forward` and by `teacher_forced.py`:**

```python
def task_input(self, x):
    """The main network's view of an (already symlog-compressed) observation."""
    if self._task_input_is_all:
        return x
    return x[..., jnp.asarray(self.task_input_idx)]
```

**(d) `_forward`:** keep `mod_in` computed from the full `x` (lines 587–590 unchanged). Pass
`self.task_input(x)` instead of `x` to the three encoder calls (lines 594, 602, 676). Do **not**
reassign `x` before the modulator gather.

**(e)** Class docstring: one paragraph naming the key.

#### C2 — `src/models/modulation_compat.py` — saved-config shim

New function, same rules as the existing shim (copy, never mutate; nothing written to disk):

```python
def translate_saved_agent_config(agent_cfg: dict, *, source: str) -> dict:
    """Supply agent.task_withheld_sensors = [] to a SAVED run config that predates it.
    [] is what every run before 2026-10-07 had: the main network saw every sensor.
    Refuses a `source` under the repo's configs/ (a live config must carry the key).
    Leaves a present key alone. Prints one INFO line naming the key and the source."""
```

Module docstring: add the key and the list of call sites.

#### C3 — call sites (scripts + top-level)

Wire `translate_saved_agent_config` where the agent dict comes from a **saved** config, in the
same commit as C1:

| File | Where | Note |
|---|---|---|
| `evaluation.py` | before `ActorCriticRNN(...)` at line 392; pass the translated dict as `encoding_config` | eval reads saved configs |
| `scripts/eval/eval_rollout.py` | saved-config branch only (`agent_config_source is not None`, ~line 1100); the `--agent_config` branch stays strict | **this is the path the running capacity-grid jobs' checkpoint evals use** |
| `scripts/eval/traj_collect/collect_trajectories.py` | before line 442 | the trajectory store's fingerprint/manifest must keep seeing the **untouched** dict (translate a copy, as `apply_saved_config_compat` callers do) |
| `scripts/analysis/nmn/replay.py` | before line 127 | |
| `scripts/analysis/nmn/untrained.py` | before line 105 | |
| `scripts/analysis/nmn/teacher_forced.py` | `_chain` line 82: `x = model.task_input(jnp.sign(obs) * jnp.log(jnp.abs(obs) + 1.0))` | removes a silent wrong-column hazard; flat branch (line 127) uses the same `x` |
| `scripts/analysis/nmn/ckpt_io.py` | `_slice_from_config`: if the saved config carries a non-empty `task_withheld_sensors`, raise "exclusive-input runs have no slice label yet" | prevents an exclusive run being labelled as a redundant one |
| `train.py` | startup banner (lines 1229–1246): print `Main network withheld sensors: [...]` for both modulated and ordinary agents; when the modulator is off and the list is non-empty, print `SENSOR-ABLATED ORDINARY AGENT: main network blind to [...]` | no read here — the model reads the key |

#### C4 — `evaluation.py` restore shape check (**D4**, recommended)

`_merge_restored_into_module_state` (evaluation.py:78–112) copies a restored leaf without
comparing shapes. With removal (A2) a key/checkpoint mismatch would surface only as an opaque
matmul/einsum shape error at the first forward. Add at the leaf branch:

```python
if hasattr(module_state, "shape") and hasattr(restored_state, "shape") \
        and tuple(module_state.shape) != tuple(restored_state.shape):
    raise ValueError(f"checkpoint/model shape mismatch at {_path}: "
                     f"model {tuple(module_state.shape)} vs checkpoint {tuple(restored_state.shape)} "
                     "(is agent.task_withheld_sensors the same as at training time?)")
```

#### C5 — configs (rollout, **D3**)

Recommended (D3-a): add `task_withheld_sensors: []` under `agent:` with a one-line dated comment
to every live rPPO agent config — 25 in `configs/models/recurrent_ppo/`, 9 in
`nmn_capacity_grid/`, 16 in `nmn_input_site_grid/`, 16 in `nmn_input_site_grid_gaenorm/` (66
files; developer re-counts with `grep -rl "RecurrentPPO" configs/models`). The two **generated**
families must be changed through their generators, not by hand, or their `--check` fails:
- `nmn_input_site_grid/generate_site_grid_arms.py` (emits both site grids) — add the key, regenerate.
- `nmn_capacity_grid/generate_capacity_arms.py` — inherits from the regenerated reference; its
  `--verify` step compares the resolved config against a **saved** run config, which lacks the
  key: add `agent.task_withheld_sensors` (with value `[]`) to that step's allowed-difference set.

Archived agent configs (if any under `configs/**/archive/`) are not migrated (project policy).
Dreamer, DQN, DRQN and plain-PPO agent configs are not touched.

#### C6 — tests

New `tests/models/test_task_withheld_sensors.py`:

| Test | Proves |
|---|---|
| `test_missing_key_raises`, `test_null_key_raises` | no fallback default |
| `test_string_value_raises`, `test_unknown_sensor_raises_and_lists_available`, `test_duplicate_raises`, `test_withholding_every_sensor_raises` | loud failure on bad values (message asserted to contain every available sensor name) |
| `test_modulated_withheld_not_read_by_modulator_raises` | rule 6 (e.g. `input_sensors: ["Satiation"]`, withheld `["Interoceptive Nociception"]`) |
| `test_unmodulated_nonempty` | rule 7 per D1 (constructs, or raises) |
| `test_encoder_shapes_hierarchical` / `_flat` | `n−k` groups, hub input `(n−k)·H`; flat `in_features == D − w` |
| `test_main_network_cannot_see_withheld_column_unmodulated` | ordinary agent: perturbing the withheld column leaves logits, value and hidden state **exactly** equal |
| `test_main_network_sees_withheld_column_only_via_modulator` | modulated agent: perturbing the withheld column leaves `acts["enc.uni.raw"]` / `acts["enc.raw"]` (pre-FiLM) exactly equal, while `mod_info` changes |
| `test_task_idx_is_static_metadata` | `task_input_idx` is a tuple of Python ints and appears nowhere in `nnx.state(model)`; a second jitted call with a new observation does not retrace |
| `test_empty_list_builds_identical_param_tree` | `[]` gives the same param paths and shapes as the pre-change tree (the golden fixtures' param tree) |
| `test_translate_saved_agent_config_*` | supplies `[]` when absent; leaves a present value; refuses a `configs/` source; does not mutate the input |
| `test_restore_shape_mismatch_raises` (if D4) | an exclusive checkpoint restored into a non-exclusive model raises the named error, and vice versa |
| `test_teacher_forced_exclusive_model` | `teacher_forced._chain` recomputed == captured on an exclusive hierarchical model (fails before the C3 fix) |

Existing tests: add `task_withheld_sensors: []` to every hand-built `encoding_config` (≈12
files: `tests/test_trajectory_collection.py`, `tests/fixtures/modulation/generate_golden.py`,
`tests/fixtures/balance_metrics/generate_pre_change_rollout.py`,
`tests/training/test_checkpoint_restore_roundtrip.py`, `tests/models/test_{mc_fixed_mode,
capture_activations,gae_norm_mode,mc_raw_mode,modulation_compat,modulation_input_slice,
network_construction}.py`, `tests/analysis/test_nmn_spectral_bound.py`; developer re-greps for
`use_layer_norm` and `ActorCriticRNN(` under `tests/`). **Fixture files are not regenerated**:
`tests/fixtures/modulation/{flat,hier_ln}_{baseline,legacy}.npz` are the pre-change ground truth
for the bit-for-bit claim and must pass untouched. Extend the call-site guard in
`tests/scripts/test_evaluation_model_rebuild.py` to cover the new key.

#### C7 — docs (same change)

| Doc | Change |
|---|---|
| `docs/environment/CONFIG_GUIDE.md` | New short subsection under §7 ("Agent architecture keys read by `ActorCriticRNN`"): the key, its validation rules, the saved-config shim, the D3 rollout; one line in §5's recovery-path list naming the behaviour-preserving value `[]` |
| `docs/environment/02_config_schema.md` | One pointer row/paragraph: the key is an agent key, not an `EnvParams` field, and is documented in CONFIG_GUIDE §7 (contract item 2) |
| `docs/environment/CONFIG_CRITICAL_SETTINGS.md` | New registry row `agent.task_withheld_sensors` = `[]` (changes what the main network can see; changes parameter shapes, so checkpoints are not interchangeable across values) + a dated change-log line recording the row's addition |
| `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` | Under §1e (or a sibling §1f): the scripts that now import `translate_saved_agent_config`, and `ckpt_io.py`'s new refusal |
| `docs/develop/active/neuromodulation/MODULATION_SITE_REFACTOR.md` | Back-link from Part B to this plan |

Back-links from the dossier (`docs/experiments/`) and the critique (`docs/project/`) are owned by
`experiment-analyzer` / the researchers; this plan does not write there — the parent should ask
them to add a one-line link.

---

## Checkpoints

- [ ] **Before any edit**, on the pre-change commit, capture (to `tmp/YYYYMMDD_HHMMSS_exclusive_input_before.npz`) 20 PPO iterations of loss scalars (total, policy, value, entropy, grad_norm, and modulator grad_norm) for (i) one modulated config (`recurrent_ppo_nmn_het_film_g1.yaml`) and (ii) one ordinary config (`recurrent_ppo.yaml`), seed 42, CPU — the Part B V4 recipe.
- [ ] After C1+C2+C5: the same 20 iterations are **bitwise equal** for both configs with `task_withheld_sensors: []`.
- [ ] `tests/models/test_modulation_sites.py` (the golden `.npz` comparisons) passes with the fixture files untouched (`git status tests/fixtures/` clean).
- [ ] The jaxpr string of `model(x, h)` for a `[]` model equals the pre-change jaxpr string (capture the pre-change string in the same `tmp/` file) — hierarchical and flat, modulated and ordinary.
- [ ] A finished run that predates the key (e.g. one capacity-grid run's latest checkpoint, or any recent NMN run) evaluates through `scripts/eval/experiment_eval_checkpoint.py` and through `evaluation.py` with the INFO line printed and no error — proves the running jobs' eval path survives the commit.
- [ ] An exclusive smoke run (`["Interoceptive Nociception"]`, modulated, encoder site on) and a blinded ordinary smoke run each train 5 iterations, save a checkpoint, and restore through `evaluation.py`; the saved `models/config.yaml` carries the key.
- [ ] `git diff --stat` shows no file under `src/algorithms/dreamer_srl/` or `configs/models/dreamer_srl/`.
- [ ] Generator `--check` passes for both generated grids after regeneration; capacity-grid `--verify` passes with the widened allowance.
- [ ] Full test suite green (`tests/models`, `tests/scripts`, `tests/training`, `tests/analysis`, `tests/env` parity gates).
- [ ] **Speed:** steps/s for the `[]` path vs. pre-change on the same node/config/seed (expect identical: same graph), and for the exclusive smoke config vs. its redundant twin (expect ≤ 1% difference — one gather of a few columns). Record both in the Implementation Report.

## Open decisions for the user

- **D1 — Withholding with the modulator off.** The request asked for an error when the key is
  set without a modulator, *and* for a blinded ordinary agent as the fair control; one key cannot
  do both. (a) **Recommended:** allow it; the ordinary agent with withheld sensors *is* the
  blinded control, made unmistakable by the startup banner and the saved config. (b) Keep the
  error and add a second mandatory acknowledgement key (e.g. `agent.task_withheld_without_modulator: true`)
  that the control configs set.
- **D2 — Which baseline the experiment uses** (experiment-designer's call, flagged here because
  the code must support it). The blinded ordinary agent asks "does the modulator let the agent
  use a signal the main network cannot see?". The critique (§5.1, and its note to
  `plan-reviewer`) instead asks for the full-sight ordinary agent: "same information, routed
  through the modulator vs. given directly". These answer different questions; both are
  buildable after this plan (the full-sight one already exists). The plan does not pick.
- **D3 — Rollout of the mandatory key.** (a) **Recommended:** add `task_withheld_sensors: []`
  to all ~66 live rPPO agent configs (via the two generators where they exist) — every agent
  config then states what its main network sees. (b) Declare it once under `agent:` in
  `configs/train/recurrent_ppo.yaml` (1 file; but a reader of an agent config no longer sees
  the setting, and it is a layered default of the kind the balance-metrics note in CONFIG_GUIDE
  §7 cautions about).
- **D4 — Restore-time shape check** in `evaluation.py` (C4). Recommended yes: three lines that
  turn a wrong-key restore into a named error instead of an opaque shape error. It touches the
  shared restore helper, so it is listed separately.

## Implementation Report

> **Implemented by**:
> **Date**:

## Verification Report

> **Verified by**:
> **Date**:

---

## Feedback from plan-reviewer

> **Reviewed by**: plan-reviewer · **Date**: 2026-10-07 · **Plan commit**: `7486b026`
> **Verdict: SOUND WITH CONCERNS.** The core design is correct and nothing here blocks implementation. Five Moderate findings need small plan edits first. None is Critical, so no separate review file was written.

**Verdict in plain words.** Removing the hidden sensor's branch from the main network, rather than feeding it zeros, is the right choice. The regression check for an empty list is meaningful and is not circular. The saved-config shim is needed, but the plan gives the wrong reason for it. The nine capacity-grid runs now training do **not** run checkpoint evaluations during training, so this change cannot break them. What really needs protecting is every *later* evaluation of a run already on disk, plus any evaluation another session runs while files are half-edited. Three gaps can cost a re-run or give a silently wrong label: the config rollout misses a fourth generated config family, the old regression recipe's world config no longer loads, and one analysis guard is skipped for runs whose names already say which arm they are.

Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run · 🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

### Findings (ranked)

| # | Sev | Location | Issue | Suggested fix | Owner |
|---|---|---|---|---|---|
| F1 | 🟡 | §A4 "Running jobs"; C3 row `eval_rollout.py` | **The stated reason is wrong, but the conclusion holds.** All nine capacity-grid runs have `experiment.during_training.enabled: false` in their saved configs (e.g. `results/JAX_RecurrentPPO/20261006-200543_rppo_nmncap_l05_h32g8_s42/models/config.yaml:488-489`). No run has an `experiment_eval/` folder. The in-training checkpoint eval (`evaluate_jax_checkpoint`) uses the in-memory model, and the render subprocess (`render_recordings_v2.py`) never builds a model. So the running jobs never rebuild a model from `src/` and are safe whenever this lands. Two things are really exposed. (a) **Every later evaluation** of any run on disk, including the nine runs' stage-1 analysis (`configs/eval_sweeps/nmncap/`). The shim covers these. (b) **Any evaluation another session runs while the shared working tree is half-edited.** "Same commit" does not protect against (b), because the shared folder runs whatever is on disk, committed or not. | Rewrite A4 to give the real reason. Then either implement in a git worktree and fast-forward the shared folder once, or order the edits so every intermediate state works: wire the shim and call sites first (supplying `[]` is a no-op for today's code), and add the mandatory read in `__init__` **last**. | senior-developer |
| F2 | 🟡 | C5 / D3 rollout count (66) | **A fourth generated family is missing.** `configs/models/recurrent_ppo/nmn_input_l05/` is untracked work from a parallel session: four agent configs plus `generate_input_arms.py`, with eight eval specs in `configs/eval_sweeps/nmninp/`. `grep -rl use_layer_norm configs/models/recurrent_ppo` gives **70** files, not 66. Its generator copies `nmngaenorm_t16quad_ALL.yaml`, so regenerating the site grid makes its `--check` fail. Its `--verify` step [2] compares against a saved run config and needs the same widening as the capacity grid. If it launches after this lands without the key, training fails loudly, so this costs time rather than data. | Find the owning session (diary, `ListAgents`) before touching untracked files that are not yours. Add the family to C5 and the Checkpoints list. | senior-developer, owning session |
| F3 | 🟡 | C5 capacity-grid `--verify` | The plan widens "that step's allowed-difference set", but `generate_capacity_arms.py` compares against the saved config **twice**. The reference check at lines 269-273 is an exact equality (`sorted(rd) == sorted(run_name_keys)`), not a subset test, so it fails as well. `_diff_keys` uses the symmetric difference, so a key that is absent from the saved config shows up even when its value is `[]`. | Widen both checks. Do the same in the `nmn_input_l05` generator (lines 349-364). | developer |
| F4 | 🟡 | Checkpoints 1-2 ("the Part B V4 recipe") | **The V4 world config no longer loads.** The recipe's environment is `configs/environment/experiment/archive/nmn_noise_heterogeneity/p3_moderate.yaml`. It is archived and deliberately not kept loadable, and it now fails with `water.enabled is required but missing` (checked at plan time). The harness `tmp/20260907_v4_loss_capture.py` still exists. The plan also does not say to check that the "before" capture reproduces itself. Part A's first capture did **not** reproduce on GPU (MODULATION_SITE_REFACTOR §C0b). | Name a maintained world: `configs/environment/default.yaml`, or the level-05 basic config, which also has "Interoceptive Nociception" so the same world can serve the exclusive smoke test. Run "before" twice and require bitwise self-equality before comparing with "after". Keep it on CPU. | senior-developer |
| F5 | 🟡 | C3 row `ckpt_io.py` | **The guard misses runs named by arm.** `_slice_from_config` is only called when the run *name* has no slice token (`ckpt_io.py:153-155`). A run named `…_t16quad_I_s42`/`_ALL`/`_X` is labelled from its name, and an unmodulated `t1none` run never reads its config. So an exclusive run, or a blinded ordinary control named like the grid, would be labelled "redundant slice" or "unmodulated control" with no error. The plan's claim "prevents an exclusive run being labelled as a redundant one" is false on that path. | In `list_runs`, read `task_withheld_sensors` from **every** matched run's saved config, before any name-based labelling, and raise if it is non-empty. Ask experiment-designer to give exclusive and blinded runs a name token that `_RUN_RE` cannot parse as an existing arm. | developer, experiment-designer |
| F6 | 🟢 | C4 / D4 | The shape check cannot catch a run that withholds a *different* sensor of the *same width* (for example, swapping one 1-wide body signal for another). The shapes match and the restore succeeds silently. This only matters on the `--agent_config` override path, because a saved config carries its own key. | On the `--agent_config` path, compare the live key with the saved config's key when both exist. Mention this limit in the CONFIG_CRITICAL_SETTINGS row. | developer |
| F7 | 🟢 | §A2 (design note) | Removing the branch keeps the random-number draws in the same order: `GroupedLinear` draws one key per layer regardless of group count, so the GRU, the actor and critic heads and the modulator start from identical weights across the exclusive, redundant and blinded arms at a given seed. The **encoder's** starting weights still differ, because the draw has a different shape (and in flat mode the initial weight scale changes with the input width). Seed pairing across arms is therefore not weight-level pairing in the encoder. | Note this for the analysis. No code change. | experiment-designer |
| F8 | 🟢 | §A4 | The grid launched 2026-10-06 20:05, not 2026-10-07. | Fix the date. | senior-developer |

### Answers to the focus questions

- **Remove or zero.** Remove is correct. With zeroing plus encoder-site FiLM, the modulator's per-branch shift `beta1` writes into the dead branch, so that branch becomes a modulator-controlled input with full encoder capacity, which the blinded control lacks. Removing the branch also means a wrong-key restore fails instead of loading silently. Encoder-site FiLM broadcasts over `n−k` groups without change. `max_in` is recomputed correctly. For "Interoceptive Nociception" (width 1) it does not change.
- **Bitwise claim for `[]`.** It is achievable and meaningful on **CPU**, and the plan correctly runs it there. On GPU it would need `XLA_FLAGS=--xla_gpu_deterministic_ops=true` (the V4 lesson). It is not circular: the "before" half comes from the old code. It covers only the empty-list (`[]`) path, where a Python `if` skips the gather. The jaxpr equality is the stronger, backend-independent proof that the training graph is unchanged. The 20-iteration loss check adds coverage of optimiser state and parameter-tree ordering. Keep both. The exclusive path itself is covered only by the perturbation and shape unit tests plus a 5-iteration smoke run. That is adequate for code, but it is not evidence that the exclusive arm *learns*.
- **Compat shim.** The design is right: it copies rather than mutates, refuses sources under `configs/`, and is agent-scoped because `apply_saved_config_compat` is env-scoped. This **is** a supplied mandatory value, so the existing module docstring ("a saved config that is merely missing a mandatory key still fails loudly", `modulation_compat.py:20-23`) must be updated so the shim does not contradict itself. Every model-build site is covered: `obs_manipulation`, `run_wakeup`, `run_activations` and `freeze` all go through `replay.load_agent` or `untrained.build`. `save_snapshot.py` stays broken, as before (KNOWN_BUGS row "Repo-root snapshot utility…").

### Assumptions

| Assumption | Status |
|---|---|
| The running grid jobs spawn model-rebuilding evals during training | **Refuted.** `during_training.enabled: false`, see F1 |
| No *other* running rPPO job (another session's) has `during_training.enabled: true` | ❓ Unverified. Check the diary's running rows before landing |
| `tmp/20260907_v4_loss_capture.py` still matches `train.py`'s config assembly at HEAD | ❓ Unverified. It is a copy of train.py's assembly; re-diff it against `train.py` before trusting it |
| 66 configs is the full rollout | **Refuted.** 70, see F2 |
| The critique's exclusive arm withholds only nociception | ❓ The critique (§5.1) says "the two body channels"; the plan's example withholds one. experiment-designer must decide |
| Flax keeps tuple and dict attributes on `ActorCriticRNN` as static graph data | Verified by precedent (`mod_input_idx`, `ObservationEncoder.breakdown`); `test_task_idx_is_static_metadata` pins it |
| In the blinded ordinary agent, the recurrent network cannot rebuild the injury signal from other senses | ❓ Unverified, and it matters for D2. The recurrent network can integrate "Extero Nociception" hits, so "blind" may be partial |

### Decisions D1–D4: recommendations

- **D1: allow (option a).** The blinded ordinary agent is needed as a positive control (see D2), and a second acknowledgement key only adds config surface. Make it unmistakable in the startup banner, the saved config, and a distinct run-name token (F5).
- **D2: run both, and pre-register which comparison answers which question.** The critique's note to plan-reviewer is right that the scientifically meaningful comparison is **exclusive modulated vs. full-sight ordinary**: same information, different routing. Exclusive vs. *blinded* nearly always comes out positive whenever the signal matters at all, because any pathway that carries it helps. So it tests only that the signal gets through, not that modulation is better. The blinded agent is still needed as a **positive control**: if blinded ≈ full-sight, the withheld signal carries no survival-relevant information the recurrent network cannot rebuild, and the exclusive arm cannot tell the hypotheses apart. Decide that before reading any exclusive result. Owner: experiment-designer.
- **D3: option (a), at 70 files.** Coordinate the `nmn_input_l05` family with its owning session.
- **D4: yes.** First confirm that no existing restore depends on passing a mismatched leaf through, for example scalar or step leaves with no `.shape`, which the `hasattr` guard already skips. Add F6's note.

### Cost of being wrong

If F5 is left in, the most likely cost is a quietly mislabelled control in a cross-arm figure, which is a wrong claim rather than a lost run. F2 to F4 each cost an hour or two of a failed check or a stalled first checkpoint. F1 cannot destroy data (failed evaluations are offline-recoverable), so the worst case is some lost evaluation outputs and confusion during the edit window.

*Signed: plan-reviewer*
