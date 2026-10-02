---
title: "Re-loading archived runs: a read-only compatibility layer for saved run configs"
topic: refactors
status: active
created: 2026-09-09
last_updated: 2026-09-10
---

# Re-loading archived runs: a read-only compatibility layer for saved run configs

> **Status**: PLANNED
> **Opened**: 2026-09-09
> **Related**: [[KNOWN_BUGS]] (row "Mandatory config keys keep landing without migrating the archive", row "A run's saved config file carries a stale second copy of the seed and episode budget") · [[IMPLEMENTATION_PLAN]] (thermal) finding F9 · `src/models/modulation_compat.py` and `tests/models/test_modulation_compat.py` (the presence-shaped precedent) · `scripts/eval/traj_collect/collect_trajectories.py` `apply_sensor_compat` (the absence-shaped precedent)

---

## Context

Every training run writes a frozen copy of its own settings next to its checkpoints, and every offline analysis tool rebuilds the simulated world from **that frozen copy** rather than from the maintained settings files — which is correct, because the frozen copy is what the run actually trained with. The problem is that the world-builder refuses to run unless certain settings are spelled out explicitly, and the list of settings it demands has grown over time. A run finished in July cannot know about a switch invented in September, so its frozen copy does not mention it, and the world-builder stops with an error instead of rebuilding the run's world. No analysis of that run is possible.

The immediate trigger was the body-temperature ("thermal") system, whose on/off switch became a required setting on 2026-09-09. That switch blocks the 32-run grid comparing where a neuromodulatory signal is injected into the network (16 runs using Monte-Carlo returns, 16 using normalised advantage estimates, all trained 2026-09-07) — the substrate for the representational analyses already published under `results/analysis/nmn_representation/`, and for more analyses expected on the same runs.

**The headline finding of this investigation is that the body-temperature switch is not the problem; it is the fifth instance of the problem.** Measured, not estimated: of the 493 frozen run-configs currently on disk, **only 33 can be rebuilt at the current code**. Four earlier required settings — three about vision, one about smell — already block hundreds of runs, and they have been blocking them silently since August, because nobody tried to re-analyse those runs. A fix that only teaches the tools about the temperature switch would restore 120 runs and leave 340 broken, and the sixth key would be discovered exactly the same way: by someone hitting it.

**What this is currently blocking.** The nearest pending piece of science is the "freeze-at-mean" test — an intervention that pins the neuromodulator's output at its average value and asks whether the agent's behaviour changes, i.e. whether the modulator's moment-to-moment variation is doing any work at all. Today that test has only been run on the condition where the modulator sees *every* sense at once: `results/analysis/nmn_representation/freeze_at_mean/paired_differences.csv` holds 42 rows, all of them the all-senses arm. Extending it to the two informative slices — modulator fed only the body's internal signals, and modulator fed only the outside-world senses — would say **which inputs** make the modulator's variation load-bearing. It needs no new training and no new GPU time; it needs only to re-open the already-trained runs, which is exactly what is broken. A second consequence, measured below (§A12): the script that supplies this plan's own parity evidence cannot itself run at the current code.

This plan therefore proposes **one small read-only compatibility layer**, applied only where a *frozen run copy* is read and never where a *maintained settings file* is read, that supplies each historically-added setting at the value which reproduces the behaviour the run actually had. It keeps the strict "no silent defaults" guarantee fully intact on the live path — that guarantee is what makes a typo in a settings file fail loudly instead of training the wrong experiment — and it pins that asymmetry with a named test, exactly as the existing neuromodulation compatibility shim does. It also proposes the piece that stops the next recurrence: a handful of tiny era-representative frozen configs committed as test fixtures, so the day someone makes a sixth setting mandatory, the test suite goes red instead of an analysis six weeks later.

One thing this plan discovered while answering the reviewer, and which changes how the central design question should be read: **the project already applies an automatic, silent, and unbounded version of this compatibility layer** — it just applies it to 77 runs by accident rather than to the archive by design. Details in §A11.

**And a second discovery, which is the argument for putting this in one place rather than a sixth.** A registry sweep for prior work on this problem found that the compatibility machinery the project already has is effectively **undiscoverable**: it is two command-line flags, one shim function, three call sites, and two commits that made keys mandatory (`0e8a4ef`, `9771e98`), spread across a script and a loader, with **no entry in the known-bugs registry and no doc that names it**. Nothing a person would search for returns it. The measurable consequence is in this document's own history — the first draft of this plan rediscovered the whole surface from scratch instead of starting from the working solution that already existed for four of the five keys, and inherited none of the reasoning its author had written down. That is the cost this plan is really paying off: not five broken keys, but a compat surface nobody can find. Consolidating it into one named module with one table, one test file and one manifest field is what makes the sixth key a test failure instead of a fifth rediscovery. (The undiscoverability itself is being recorded separately with `bug-curator`.)

---

## Analysis

### A1 — The reproducer

```
python -c "
import yaml
from src.utils.config import Config
from src.environment.config_loader import load_env_params
p='results/JAX_RecurrentPPO/20260907-045531_rppo_nmnsite_t1none_s42/models/config.yaml'
load_env_params(Config(yaml.safe_load(open(p))))"
```

```
ValueError: Strict Config: Configuration key 'thermal.enabled' is required but missing.
  src/environment/config_loader.py:1476  _thermal_on = bool(config.get_mandatory('thermal.enabled'))
  src/utils/config.py:74
```

### A2 — The measured blast radius (this is the finding that changes the plan)

A cascading sweep over every `results/*/*/models/config.yaml`: try `load_env_params`; on a *missing mandatory key* error, inject that key's value from `configs/environment/default.yaml`; retry; record the chain. Working file: `tmp/20260909_saved_cfg_cascade.txt`. Independently reproduced by `plan-reviewer` through the same load path (`tmp/20260909_plan_review_sweep.{py,json,log}`), which is the count used below.

**The archive is a moving target and the table must be read that way.** The first sweep saw 477 files; sixteen `olfgae` runs launched at 16:11 on 2026-09-09 took it to **493** while this plan was under review. The *chain* counts (184 / 150 / 120 / 6) are era populations and do not move; the clean set and the totals do. Numbers below are as of 493 files. No checkpoint in this plan may hard-code a total — see CP5.

| Frozen configs | Chain of missing mandatory keys, in the order the loader hits them | Era |
|---:|---|---|
| 33 | *(none — rebuilds cleanly at HEAD)* | 2026-09-09 onward |
| 120 | `thermal.enabled` | 2026-08-26 → 2026-09-07 (includes all 32 target runs) |
| 6 | `sensory.visual_value_mode` → `sensory.visual_occlusion_enabled` → `thermal.enabled` | 2026-08-26, same day, pre-merge |
| 184 | `sensory.visual_value_mode` → `sensory.olfactory_grid_range` → `sensory.visual_blur_enabled` → `sensory.visual_occlusion_enabled` → `thermal.enabled` | 2026-05-28 → 2026-08-16 |
| 150 | the same five keys, **then** a non-missing-key error | 2026-04-20 → 2026-05-21 |

Per-key totals — the number of frozen run-configs each key alone is enough to block:

| Key | Blocks | Made mandatory by | Date |
|---|---:|---|---|
| `thermal.enabled` | 460 | `dd3b5dfa` (thermal Stage 1) | 2026-09-09 |
| `sensory.visual_value_mode` | 340 | `9771e98c` (visual value mode + occlusion) | 2026-08-26 |
| `sensory.visual_occlusion_enabled` | 340 | `9771e98c` | 2026-08-26 |
| `sensory.olfactory_grid_range` | 334 | `0949ddb2` rename + `4a5fcd44` validation | 2026-08-26 |
| `sensory.visual_blur_enabled` | 334 | `0e8a4ef8` (directional olfaction + point spread) | 2026-08-21 |

The 150-run tail fails on something structurally different and **out of scope for this plan**: 130 raise on `environment.predator_enabled` (a key *removed* in v2.0, guarded at `config_loader.py:1738`) and 20 on `Resource: missing required key 'properties_std'` (a schema *rename*, `config_loader.py:711`). Supplying a missing key cannot fix a removed key or a renamed schema; those need a translation, which is `modulation_compat`'s shape, and they should be their own plan if anyone ever needs those April/May runs.

A sixth key, `sensory.injury_observable` (mandatory since `980fa09b`, 2026-04-30, read at `config_loader.py:2072`), is absent from 40 frozen configs — but all 40 are inside that 150-run tail and fail earlier on `predator_enabled` / `properties_std`, so supplying it changes nothing. Deliberately excluded; recorded here so a later reader does not think it was missed.

**Recovery arithmetic.** Supplying the five keys takes the archive from **33 / 493 rebuildable (6.7 %)** to **343 / 493 (70 %)**, and covers **32 / 32** of the runs that prompted this plan. The invariant that survives the archive growing is the one to quote: *everything except the 150-run pre-v2.0 tail becomes rebuildable*, and every run launched from now on is born rebuildable.

### A3 — Is this the same shape as `modulation_compat`? No, and the difference is the whole design

`src/models/modulation_compat.py` fires on a **positive signature**: the archived config *contains* the obsolete flat `temp_clip` key, which is a fact no current config can produce, so the shim can translate it with no risk of touching anything else. Its own docstring draws the boundary this plan must not cross:

> "It is also not a general defaulting layer: it fires only on the specific legacy shape (flat `temp_clip` present), and a saved config that is merely missing a mandatory key still fails loudly."

A missing `thermal.enabled` **is** "merely missing a mandatory key". So the honest answer to "follow the established pattern" is: yes, follow an established pattern — but the *other* one. The project already has a second, absence-shaped precedent, in `scripts/eval/traj_collect/collect_trajectories.py:333` (`apply_sensor_compat` + `PRE_V31_SENSOR_DEFAULTS` / `PRE_V32_SENSOR_DEFAULTS`), which solves precisely this problem for the four sensory keys. Its three properties are the ones this plan generalises:

1. Values chosen to reproduce the *pre-feature* behaviour, each justified against a specific trace-time branch in `sensor.py` — not "sensible defaults".
2. **Verified, not asserted**: replaying 25 real episodes (5,298 steps) through today's code against observations the old code wrote gave a max difference of 2.4e-07 across all 27 channels (`scripts/analysis/supplementary/parity.py`).
3. A refusal guard: if the config already sets any key the shim would supply, it raises rather than overwriting.
4. **It is opt-in, and its author said in the file why.** This plan's first draft listed the three properties above and omitted the fourth, which is the one that argues *against* this plan's central design choice. Quoting it in full so it cannot be routed around (`collect_trajectories.py:308-311`):

   > "This is deliberately an explicit opt-in flag and NOT a default. The project's no-fallback-defaults rule exists to stop exactly this kind of silent substitution, and a run that genuinely used v3.1 sensors must never be quietly reinterpreted as pre-v3.1."

   §Design decision 2 now argues with this text directly rather than around it.

Its weakness is that it lives inside one script. `eval_rollout.py`, `scripts/analysis/nmn/replay.py` and `scripts/analysis/trajectory_glm.py` have no access to it, which is why those tools cannot replay a pre-2026-08-26 run **at all** today.

### A4 — Every call site that reads a frozen run config (found, not guessed)

Enumerated from `grep -rn "load_env_params\|config.yaml" --include=*.py src scripts`. Two groups.

**Group 1 — rebuild the world from a frozen config (broken today; the shim's insertion points):**

| # | Site | Line | How the frozen config gets in |
|---|---|---|---|
| 1 | `scripts/eval/eval_rollout.py` | `959` (`load_env_config`), `1007` (`load_env_params`) | `--config` commonly points at `<run>/models/config.yaml`; `_resolve_continual_stage_config` (line 677) may redirect to a per-stage copy under the same checkpoint root. **May also be a live file** — needs the same live/saved discrimination the modulation shim does at line 1063 (`agent_config_source`). |
| 2 | `scripts/eval/traj_collect/collect_trajectories.py` | `699` (read), `727` (`load_env_params`) | Always `<run>/models/config.yaml`; refuses anything else. Already has the opt-in sensory shim at `713`–`723`. |
| 3 | `scripts/analysis/nmn/replay.py` | `82`–`84` | `<models_dir>/config.yaml`. Always saved. **This is the site the 32 target runs' analyses go through.** |
| 4 | `scripts/analysis/trajectory_glm.py` | `54` | `f"{run}/models/config.yaml"`. Always saved. |
| 5 | `scripts/analysis/supplementary/parity.py` | `26`, `31` | `RUN + '/models/config.yaml'`. Always saved. |

**Group 2 — read a frozen config as a plain dictionary, never build the world (unaffected; listed so the developer does not touch them):** `scripts/analysis/nmn/ckpt_io.py:129` (`run_config`), `scripts/analysis/hiding_drivers.py:346`, `scripts/analysis/context_dependence.py:475`, `scripts/analysis/figures/_common.py:136`, `scripts/analysis/ladder/_ladder.py:144`, `scripts/analysis/supplementary/{prox_full,allarms_glm,armpain,modeleffect}.py`, `src/utils/trajectory_store.py:824` (error text only).

`src/utils/evaluation_core.py` does **not** call `load_env_params`; it receives already-built params. Not a site.

### A5 — What a pre-thermal run's rebuilt world should be, verified rather than repeated

The claim under test: `thermal.enabled: false` is sufficient, and nothing else in the temperature block is read when the gate is off.

**Verified at load time.** `config_loader.py:1476` reads the gate; `1477`–`1591` is the `if _thermal_on:` arm where all ~20 sub-keys are read via `get_mandatory`; `1592`–`1629` is the `else:` arm, which assigns every one of them an inert literal and calls `get_mandatory` zero times. The load-time structural check `_check_thermal_structure` (defined `530`, called `2019`) sits inside `if _thermal_on:`. The only thermal-adjacent code that runs unconditionally is `_read_temperature` (`336`), which reads per-entity heat declarations with a plain `entry.get('temperature', 0.0)` — a genuine "this entity is not a heat source" default, not a `get_mandatory` — and returns `(0.0, 0.0, 0.0)` for every entity in a pre-thermal config.

**Verified at run time.** Every consumer is behind a *static* Python branch on `params.thermal_enabled`, so a thermal-off config traces the identical computation graph — and therefore draws the identical random numbers — that pre-thermal code did: `core.py:77` (homeostatic drive), `247`, `854`, `913`, `1773`; `sensor.py:485` (thermoception channel) and `541` (observation width); `state.py:95`. `config_loader.py:1596`–`1600` explains why the two placement constraints must be `0` in the off-arm for exactly this reason. Both renderers reach for the field through `getattr(params, 'thermal_enabled', False)` (`renderer.py:630`, `renderer_v2.py:307`), so drawing an old recording is already handled.

**Verified empirically, and this already exists.** `tests/env/test_thermal_parity.py` replays a fixed 100-step episode from seed 0 for every fixtured config against pre-thermal reference captures and requires exact equality on reward, both drives, `state.key`, termination reason, entity positions and every observation slice but one (a documented ≤1-ulp exemption on sampled properties, with a derived Olfaction tolerance). It is adjudicated against **72 committed `.npz` reference captures** (`tests/env/fixtures/thermal_parity/`) — this plan's first draft said 34, which was wrong; 72 verified by `git ls-files` and by `plan-reviewer`'s own run of the suite (72 passed). It is a real comparator, not an empty gate. That test **is** the instrument for "thermal-off equals pre-thermal", it is committed, and it is green. This plan does not need to build a new one; it needs to cite this one and add a per-key equivalence test (§Checkpoint 4).

**Confirmed measurement:** injecting only `thermal.enabled: false` into all 16 `nmnsite` frozen configs and all 16 `nmngaenorm` frozen configs makes `load_env_params` succeed on 32 / 32.

### A6 — Is the substitution ambiguous? Measured: no, on this population

The reason `apply_sensor_compat` is opt-in is the fear of reinterpreting a run that genuinely used the feature. On frozen run-configs that fear is checkable, and it was checked:

- A frozen config is written by the trainer **after** `load_env_params` has already succeeded. At any commit where a key is mandatory, a run that reached checkpoint-save time necessarily had the key. So on this population, absence of a key means "trained before the key existed" — it cannot mean "the author forgot it", which is what the mandatory-key rule protects against on the live path.
- Measured: `thermal:` block present in 33 frozen configs, absent in 460. No frozen config has a `thermal:` block without `enabled`.
- The one real hazard was the rename `olfactory_sensor_range` → `olfactory_grid_range` (`0949ddb2`): a config carrying the *old* spelling with a real non-zero value would be silently reinterpreted as `0`. Measured across all 493 frozen configs: **zero** carry the old spelling. Hazard empirically absent — but the plan still adds a guard for it (§Checkpoint 3) rather than relying on the measurement staying true.

### A7 — Option B (pinned-commit analysis policy): assessed, not workable

*Policy:* analyse pre-thermal runs at the commit they were trained at; no shim, no code change.

Honest assessment — three failures, the third decisive:

1. **Back-porting is per-script and permanent.** `scripts/analysis/nmn/` is nine modules at HEAD and growing; every new analysis would have to be authored against, or copied back to, a September-7 tree. The standing project rule is the opposite ("build eval/analysis tooling run-agnostic — analysis questions arrive after development").
2. **The mechanics are hazardous here.** A pinned checkout rewrites `src/`, `configs/` and `scripts/` under any live training run reading them (CLAUDE.md git-safety rule). Doing it properly means a `git worktree` per era plus discipline about which tree an analyst is in — and `results/` is a NAS path shared across trees, so a mis-targeted write lands in the same archive.
3. **It cannot express a cross-era comparison, and it fails silently when it tries.** The archive spans five eras. There is no commit at which a pre-2026-08-21 run and a post-2026-09-09 run both rebuild. Worse than the error: at a pre-v3.2 commit, a *later* run's frozen config still loads, because the loader ignores keys it does not ask for — so a run that actually trained with `visual_value_mode: clamp` and line-of-sight occlusion is replayed by code that has neither, and produces plausible, wrong observations with no error. A policy whose failure mode is silent wrong numbers is worse than the current loud one.

**Verdict: reject as a policy.** Keep it as the documented escape hatch for the 150 pre-v2.0 runs, where no shim exists and the alternative is nothing.

### A8 — Option C (back-fill the frozen configs on disk): assessed, reject

*Policy:* write the missing keys into the 460 files under `results/`.

1. **Irreversible on unbacked data.** `results/` is gitignored, has no history, and was destroyed once in this project (recovery required re-training). A 460-file in-place rewrite has no undo and no diff to review.
2. **It rewrites the provenance record of a finished run.** The frozen config is the evidence of what the run trained with. Editing it makes the archive assert that a July run declared a September setting — the "verify actual state, not a re-derivation" rule points the other way.
3. **It silently invalidates provenance already recorded elsewhere.** `collect_trajectories.py:391` stores `train_config_mtime` and `build_manifest` stores `env_fp = env_fingerprint(cfg)` into every trajectory store's manifest as guarded fields. Touching the files changes the mtime and, for any key the fingerprint covers, the fingerprint — retroactively breaking stores that were correct.
4. **It walks into an open design question.** A recorded bug (2026-09-04) notes every frozen config carries a *duplicate stale* `training.seed` / `training.episodes` block permanently reading 42 / 100, and that pair still needs a wire-or-remove decision. Any tool that rewrites these files has to decide what to do with it. Scope grows from "add one key" to "own the file format".
5. **It is the same treadmill with write side-effects.** The sixth mandatory key requires re-running it over an archive that keeps growing.
6. **It does not even finish the job** — the 150 pre-v2.0 runs stay broken.

A softer variant — write a *sidecar* `models/config_compat.yaml` rather than editing the original — avoids (1)–(3) but is strictly worse than Option A: it is Option A with a disk cache that can go stale against the compat table. **Reject.**

### A9 — Relationship to the recorded bug

`KNOWN_BUGS.md` already carries "Mandatory config keys keep landing without migrating the archive", re-measured 2026-09-09: 68 of 141 stand-alone **authored** configs under `configs/` fail to load, and the standing user decision there is **lazy migration** — fix one when a run next needs it. Two things follow, and the developer must not blur them:

- That row's population is `configs/` (files a human wrote and can edit). **This plan's population is `results/` (files a finished run wrote and nobody should edit).** Same root cause, different object, opposite correct remedy: you migrate an authored config, you shim a frozen one.
- **This plan does not touch `configs/` and does not perform any bulk migration.** The lazy-migration decision stands untouched.

### A10 — Fingerprint drift: what happens to the 110 existing trajectory stores

**The question in plain terms.** When the tools collect episodes from a finished run, they file the results in a folder named after a short hash of that run's settings — so two different settings can never write into the same folder and quietly mix. If this plan's compatibility layer runs *before* that hash is computed, the hash changes for every run trained before the temperature switch existed. The tools would then not recognise the folder that already holds that run's episodes: instead of adding to it, they would start a fresh, empty one beside it, and re-collect a million episodes that already exist. That is real GPU time, so the plan has to make an explicit choice rather than inherit one.

**Measured, not assumed.** The mechanism is `env_fingerprint` (`src/utils/trajectory_store.py:428`), a SHA-256 over the whole resolved config dict; the store path is `out_root / <run> / <ckpt_step> / <env_fp>` (`collect_trajectories.py:744`), and how much work remains is read from that directory (`completed_blocks(store_dir)`, line 775). A changed fingerprint therefore does not error — it silently starts at block 0.

First, a correction to the reviewer's count. The glob `results/trajectories*/*/*/*/` returns **118** directories, but eight of those are `_scratch/.../_run_markers` and `_worklists` bookkeeping folders, not stores. There are **110** real stores, each with a `_manifest.json`.

| Measurement | Result |
|---|---|
| Stores whose manifest `resolved_env_config` contains a `thermal:` block | **0 / 110** — every existing store is pre-thermal, so post-shim hashing moves *all* of them |
| Stores where `hash(saved config file exactly as it sits on disk) == recorded env_fp` | **101 / 110** |
| Stores where it does not | **9 / 110** — all nine carry a non-null `pre_v31_sensor_keys`, i.e. their fingerprint was taken *after* the historical sensory shim ran |

**Decision: the fingerprint is computed PRE-shim** — over the config as read from disk, before `apply_saved_config_compat` touches it.

Three reasons, in order of weight:

1. **It is the only choice under which existing work resumes.** Pre-shim hashing reproduces the recorded fingerprint for 101 of 110 stores, including all six million-episode `restprem_a0*` stores. Post-shim hashing forks all 110.
2. **It is the correct equivalence class, not a convenient one.** The fingerprint exists so that two collections which would produce *different episode data* cannot share a directory. The keys this shim supplies are verified behaviourally inert — §A5 shows a thermal-off config traces an identical computation graph and therefore draws identical random numbers, and §A3 property 2 shows the sensory values reproduce recorded observations to 2.4e-07. Two configs differing only by these keys produce byte-identical episodes. Hashing pre-shim quotients by exactly that equivalence, which is what a content address should do.
3. **The risk post-shim hashing was protecting against is real, but a hash is the wrong instrument for it.** The genuine hazard is *table drift*: if an `_ERA_KEYS` value ever changes, two collections of the same run under different tables would share a directory. This is not hypothetical — it already happened (see the nine stores below). A hash cannot tell you *what* differed; a recorded key→value map can, and can refuse.

#### A10a — The convention this reverses, its licence, and how both behaviours coexist

**This decision departs from a convention a previous author wrote down on purpose, and the plan says so before arguing with it.** `collect_trajectories.py:311-312`, in the comment block immediately above `PRE_V31_SENSOR_DEFAULTS`:

> "Patching happens before `env_fingerprint`, so the store's `env_fp` — a guarded manifest field — reflects the config actually used."

The same principle is asserted a second time, in the refusal message the store itself prints (`trajectory_store.py:557-559`):

> "the store path is content-addressed by env config fingerprint precisely so two configurations cannot collide."

Both say the address should describe **the environment that was built**, and both are right about what a content address is for. This plan hashes the config **as it sits on disk, before the shim** — i.e. it addresses the file, not the built environment. That is a reversal of a stated convention, not an oversight, and it is the same shape as the opt-in question in §A3 property 4: an earlier author left a reason, and the plan owes it a reply rather than a detour.

**The reply: the two only look different because the shim's keys carry no information about the environment.** A fingerprint's job is to keep two collections that would produce *different episode data* out of the same directory — it identifies the environment that produced the episodes, not the bytes of the config that described it. The shim is a **deterministic, total function from the raw file to the built environment**: a fixed table, one value per key, no free parameters. So identical raw bytes imply an identical built environment, and hashing the bytes is a faithful — merely finer-grained — address for the environment. Pre-shim hashing can therefore *split* one environment across two directory names (a run that omits `visual_blur_enabled` and an otherwise-identical run that writes `false` explicitly hash differently); it can never *merge* two environments into one directory, which is the failure the convention exists to prevent. The convention's goal is preserved; only its instrument changes.

**Where the behavioural evidence is actually load-bearing — and it is not where it first appears.** Determinism alone licenses the *ordering*. What the parity evidence licenses is the thing the ordering makes possible: **resuming a store whose earlier blocks were generated by older code, so that pre-shim-era and post-shim-era episodes sit in one parquet population.** That concatenation is only legitimate if supplying the era keys reconstructs the same environment the earlier blocks were collected in. Hence the per-key audit below. (Cross-code-version mixing on resume is not created by this plan — it is already possible and already surfaced, by the `collection_git_sha` warning at `trajectory_store.py:559-565`.)

**Per-key: does the equivalence-class argument hold? Yes for all five — on three grades of evidence, and the grades are not interchangeable.**

| Supplied key | Value | Evidence that the era value reconstructs the pre-feature environment | Grade |
|---|---|---|---|
| `thermal.enabled` | `False` | `tests/env/test_thermal_parity.py` — 100-step replay from seed 0 for **72 committed `.npz`** reference captures, exact equality on reward, both drives, `state.key`, termination reason, entity positions and every observation slice but a documented ≤1-ulp exemption (§A5) | **Measured** (replay vs. committed references) |
| `sensory.olfactory_grid_range` | `0` | `parity.py` — 25 real episodes / 5,298 steps replayed against observations the **pre-v3.1 code itself wrote** into the a01 store on 2026-08-20; max difference 2.4e-07 over all 27 channels | **Measured** (replay vs. system-produced ground truth) |
| `sensory.visual_blur_enabled` | `False` | same run of `parity.py` (its `NEW` dict injects this key and the three blur knobs) | **Measured**, as above |
| `sensory.visual_value_mode` | `'sum'` | static trace-time branch `sensor.py:394` (`if params.visual_value_mode == 'clamp':`) — `'sum'` takes the else-arm, i.e. the original per-cell accumulation is not approximated but left untouched | **Argued from source**, not yet replayed |
| `sensory.visual_occlusion_enabled` | `False` | static trace-time branch `sensor.py:389` (`if params.visual_occlusion_enabled:`) — likewise the else-arm | **Argued from source**, not yet replayed |

**Which one is weakest, stated plainly, because the reviewer asked which would break the argument.** None breaks it, but the last two are the only two resting on a reading of the source rather than a measurement, and the reason is chronological: `parity.py`'s ground truth is the a01 store recorded 2026-08-20, and the v3.2 keys did not exist until `9771e98` on 2026-08-26 — so the recorded 2.4e-07 was measured on a code version where `visual_value_mode` and `visual_occlusion_enabled` were absent, and it says nothing about them. This does **not** change the decision: a static Python branch evaluated at trace time cannot alter the traced graph, so it cannot alter the random numbers drawn, and the two keys are structurally inert in the same way `thermal.enabled` is.

**And the gap closes with a checkpoint that is already in this plan.** Once Stage 2 lands, `parity.py` runs again with the shim supplying **all five** keys, replaying against the same 2026-08-20 a01 ground truth — which predates both the v3.1 *and* the v3.2 features. **CP13 is therefore load-bearing for this fingerprint decision, not merely a restoration of a broken script**: its post-fix number is the first measurement that covers `visual_value_mode` and `visual_occlusion_enabled`. If that number is not of the recorded ~2.4e-07 order, the two keys are not inert, resuming a pre-v3.2 store is not safe, and the developer must stop and re-open this section rather than adjust the tolerance. CP13's wording already requires the number rather than a pass/fail; this is why.

**Reconciling the two behaviours, which will both leave traces in the tree.** The old flags stamp post-shim; this layer stamps pre-shim. Measured on the one store where the distinction is live today — `results/trajectories_sens/20260826-144838_sens_A_baseline_n114g0/10000063/`, collected 2026-08-26 with `--assume-pre-v32-sensors`:

| Hash of | Value |
|---|---|
| the raw saved config as it sits on disk (**what this layer would stamp**) | `d3b5e5979b` |
| raw + today's v3.2 era values (**what the old flag stamped — and it still reproduces exactly**) | `085a28834a` |
| the directory name actually on disk | `085a28834a` |
| raw + **all five** of today's era keys | `3aa18a567a` |

Three things follow, and the fourth row is the one that settles the design question:

1. **The two paths disagree for exactly the 9 stores enumerated above, and for no others** — 8 stamped under the July table, 1 (`sens_A_baseline`) under the August table. For the other 101 the raw hash *is* the recorded name, because no shim ran.
2. **Going forward they cannot disagree, because only one path survives.** After Stage 2, `apply_sensor_compat` is deleted and the flags are no-ops, so nothing in the tree stamps post-shim. The disagreement is not a live fork in behaviour; it is frozen in 9 directory names.
3. **How it would bite, and it would bite silently.** A resume of an affected store resolves to the raw-hash directory, finds no manifest there, and — because `assert_manifest_compatible` only runs when a manifest already exists at the resolved path — writes a fresh one and collects from block 0 without error. Worse, the fork is then *structurally indistinguishable from a legitimate second pass*: `hiding_drivers.find_stores` globs `{root}/{run}/{ckpt}/*/` and unions every sibling **by design** (its docstring: a store's `n_episodes` is guarded, so a genuine top-up must go to a fresh store with a continuing seed base). The only discriminator is the seed-contiguity assert in `aggregate`, which §Revision-log 🟡1b measured as firing correctly — but which `main` skips whenever `aggregate.npz` is cached, and 9 such caches exist. **Blast radius, measured:** of the 9 affected stores, 8 are complete at 200/200 blocks and 1,000,000 episodes (a resume would find nothing to do even if it resolved correctly) and 1 holds 0 of 1 blocks and no episode data. So the mechanism is real and the exposure is nil — which is why the disposition in §A10 is "no action", not "no problem".
4. **Row four is the argument against keeping post-shim stamping at all.** `sens_A_baseline` reproduces its recorded name under the v3.2 table, so it is *not* orphaned today — yet under post-shim ordering it would fork anyway the moment `thermal.enabled` joined the table, because the shim now adds a `thermal:` block its config never had (`3aa18a567a`). Post-shim stamping is not stable against its own future: **every new era key re-forks the entire archive, permanently.** Pre-shim stamping is stable by construction, because the file on disk never changes. That is a structural property, not a headcount, and it is the strongest reason of the four in §A10 above.

**Disposition of the old flags' post-shim stamping — the direct answer.** It is neither changed-to-match nor left alone: **it is deleted with the code that implements it**, and the flags survive as accepted no-ops purely so the recorded invocation in `docs/experiments/active/trajectory_factors/nmn_film_vs_unmodulated.md:233` keeps working. Three consequences the developer must implement, because "no live contradiction" is not the same as "no contradiction a reader can find":

- **Carve-out to the verbatim-comment instruction.** §Stage 2 tells the developer to move the `PRE_V31`/`PRE_V32` comment blocks into `_ERA_KEYS` "verbatim, comments included". `collect_trajectories.py:311-312` — the two lines quoted at the top of this section — are the **one exception**: copying them verbatim would carry a now-false statement into the new module. Replace them with a note that states the reversal, dates it, and points here: *"Ordering reversed 2026-09-09 (plan §A10a): the fingerprint is now taken over the raw file BEFORE this table is applied, so a store collected before the shim existed still resumes. Table drift is caught by the manifest's `saved_config_compat` map instead, which — unlike a hash — can say what differed."*
- **The deprecation line must name the ordering change, not just the automation.** "now applied automatically for saved run configs" tells a reader the *what* and hides the part that changes where their episodes land. It must also say the fingerprint is now taken pre-shim and link this section.
- **The refusal guard deliberately softens, and that is the second axis on which old and new differ for the same run.** `apply_sensor_compat` *raises* when a key it would supply is already present (`collect_trajectories.py:341-346`) — correct for an explicit flag, where "you asked me to treat this as pre-v3.1 but it isn't" is user error. §Design requirement 2 instead *skips silently*, which is correct for an automatic layer, where a present key is the ordinary later-era case. §A3 property 3 lists refusal-on-present among the properties this plan generalises; it does not survive the opt-in→automatic switch, and the module docstring must say so rather than leaving the two readings to collide. The protection it provided does not vanish: the rename guard (`_RENAMED_FROM`) and the gate-key guard still raise, and those are the cases where a present key means something is genuinely wrong.


**The guard that replaces it.** `build_manifest` gains a field `saved_config_compat`: the exact `{dotted key: value}` map the shim supplied (`{}` when it supplied nothing). On resume, `assert_manifest_compatible` compares it and raises on any difference, naming both maps.

Two implementation constraints the developer must not get wrong, both verified against the code:

- **Do NOT add `saved_config_compat` to `MANIFEST_GUARDED_FIELDS`.** That tuple is checked with `_req` (`trajectory_store.py:478`), which raises on a key that is *missing or `None`*. All 110 existing manifests lack the field, so guarding it would hard-error every legacy store on resume — converting this plan's fix into a wider breakage. The comparison must be a dedicated block that treats **absence as "legacy store, unknown"** and emits a loud `warnings.warn`, in the same style as the existing `collection_git_sha` warning (`trajectory_store.py:560`). The same reasoning explains why `pre_v31_sensor_keys` could never have been guarded: it is `None` in 101 of 110 manifests.
- **Do NOT bump `SCHEMA_VERSION`** (`trajectory_store.py:60`). No parquet column changes, and `schema_version` *is* guarded — bumping it would reject every existing store.

**Disposition of the nine stores that do not reproduce.** Both groups are safe to leave alone, and neither is caused by this plan:

- **Eight stores under `results/trajectories_nmn/`** (the `b03`/`b04` GAE and MC runs of 2026-07-22 → 07-26). Their manifests record five supplied keys — `olfactory_sensor_range` (the *old* spelling), `visual_blur_enabled`, and three blur knobs — whereas today's table has two keys and the new spelling. Measured on `f01e696927`: none of `hash(raw)`, `hash(raw + today's pre-v3.1 values)`, `hash(raw + today's pre-v3.2 values)`, or `hash(raw + both)` reproduces it. **These stores are already unreachable by a resume at HEAD, before this plan changes anything** — the table drifted under them in August. They are also complete: 200 / 200 blocks, 1,000,000 episodes each, so no top-up is possible in the first place (`n_episodes` is a guarded field; extending a store is not a supported operation). Analyses reach them by explicit `--store` path and are unaffected. **Action: none.**
- **One store under `results/trajectories_sens/`** (`sens_A_baseline`, `085a28834a`). It holds **0 of 1** blocks — an aborted collection with no episode data. **Action: none required**; if a top-up is ever run it will simply collect into the pre-shim-named directory, and the empty one can be removed by hand.

**The check that proves a top-up resumes rather than forks** — CP11, below. It is a dry-run over the real archive, not an argument.

### A11 — The 77 saved configs that carry `extends:`, and the silent shim that already exists

**The plain-language version.** Seventy-seven finished runs from 2026-06-19 → 07-03 have a line at the top of their saved settings file saying "start from the standard settings file, then apply mine on top". That line is a fossil of a recorded bug: the trainer of that era **ignored it**, so those runs actually trained on the stripped-down settings alone, without the standard base. The first draft of this plan asserted no saved config carries the line and proposed to hard-error if one did — which would have broken all 77.

**Measured at HEAD, and this is the part that matters.** Because today's `load_env_config` *does* honour `extends:`, those 77 configs load **successfully** right now — by merging today's `configs/environment/default.yaml` underneath them. Verified on three of them end-to-end: `load_env_config` returns, `load_env_params` succeeds, and the five era keys come back as `thermal.enabled=False`, `visual_value_mode=sum`, `visual_occlusion_enabled=False`, `olfactory_grid_range=0`, `visual_blur_enabled=False`.

So the project **already** performs an automatic, silent substitution on the saved path. It is worse than the one this plan proposes in three specific ways:

1. **It is unbounded.** It supplies today's value for *every* key those files omit — the whole of `default.yaml`, not an enumerated table of five. A sixth key needs no code change to be silently supplied.
2. **Its values are not pinned and are not justified.** They are era-correct today only by coincidence: `default.yaml` still happens to hold the pre-feature value for all five. The day someone sets `visual_value_mode: clamp` in `default.yaml`, those 77 runs replay under a vision model they never trained with, and nothing says so.
3. **It reconstructs an environment the run never had.** The whole point of the `22c73bac` bug row is that the inheritance was *not* applied at training time.

**Decision: on the saved branch, DROP `extends:` and do not resolve it, then apply the era table.** Rationale in one line: replay must reproduce what the trainer did, and the trainer of that era ignored `extends:` — so honouring it now would be reconstructing a world the run never inhabited.

**Verified sufficient, on all 77 rather than a sample.** With `extends:` removed and the five era keys applied, `load_env_params` succeeds on **77 / 77**. Without the era keys it fails on `sensory.visual_value_mode`, confirming the era table is doing the work and the merge is not needed for anything else. Working command recorded in §Checkpoints (CP12).

**Interaction with this plan's shim.** They do not compose — they are alternatives, and the plan chooses. On the saved branch, `extends:` is dropped and only the enumerated table applies; on the live branch, `load_env_config` keeps resolving `extends:` exactly as today. The observable change for those 77 runs is that five values acquire a named justification, a log line, and a test, and the other ~200 keys stop being supplied at all. That is a narrowing of silent behaviour, not a widening — which is the honest way to score this plan against the no-fallback-defaults rule.

**Not silently absorbed.** Dropping `extends:` is a real behavioural change for 77 runs, so the shim must print it: one INFO line naming the dropped `extends:` target and citing the bug row, every time.

### A12 — The parity script itself does not run at HEAD

Stated separately because this plan *cites* `scripts/analysis/supplementary/parity.py` as the evidence for the sensory values (§A3 property 2). Measured: it hand-injects five v3.1 keys and then calls `load_env_params`, which raises `ValueError: Configuration key 'sensory.visual_value_mode' is required but missing`. **The instrument that supplies this plan's own evidence is one of the broken call sites.** Its recorded result stands (it was produced when it could still run), but it cannot be re-run to re-confirm anything until Stage 2 lands. This is the clearest single illustration of what the treadmill costs.

---

## Implementation Plan

### Design

One new module, `src/environment/saved_config_compat.py`, holding a single table and a single function. Placed in `src/environment/` rather than `scripts/` because five call sites across three directories need it, and because it belongs next to the loader whose contract it complements.

```
        LIVE PATH (unchanged, still hard-errors)
        configs/**.yaml ──► load_env_config ──► load_env_params ──► ValueError on any missing mandatory key

        SAVED PATH (new)
        results/<algo>/<run>/models/config.yaml
                │
                ├─ apply_saved_config_compat(cfg, source=<path>)   # in memory; nothing written to disk
                │     • refuses if source resolves under configs/           (structural live-path guard)
                │     • refuses if a key it would supply is already present (already a later-era run)
                │     • refuses if a parent block is present without its gate key (the typo case)
                │     • prints one INFO line naming every key supplied
                │
                └─► load_env_params ──► EnvParams
```

Four decisions and why:

- **Absence-shaped, not presence-shaped.** Generalises `apply_sensor_compat` (§A3), not `modulation_compat`. `modulation_compat` stays exactly as it is — it solves a different problem (a *translated* key) at the same boundary, and the two compose.
- **Automatic at the saved boundary, not behind a per-tool flag. Recommended, and argued below against the text that says otherwise.**

  `apply_sensor_compat`'s author wrote the counter-argument into the file, and it deserves a direct answer rather than a detour (`collect_trajectories.py:308-311`): *"This is deliberately an explicit opt-in flag and NOT a default. The project's no-fallback-defaults rule exists to stop exactly this kind of silent substitution, and a run that genuinely used v3.1 sensors must never be quietly reinterpreted as pre-v3.1."*

  Four answers, the last one decisive:

  1. **The specific harm that sentence names is structurally impossible here, and that is the same guard the author relied on.** "A run that genuinely used v3.1 sensors" *has* the key in its saved config — the trainer could not have reached checkpoint-save time otherwise (§A6). The shim skips every key already present, so a v3.1 run cannot be reinterpreted as pre-v3.1 by any code path. That is not a promise; it is `apply_sensor_compat`'s own refusal guard, generalised.
  2. **The population the no-fallback-defaults rule protects is `configs/`, not `results/`.** The rule exists so a typo in a file a human wrote fails loudly instead of training the wrong experiment. On a *finished run's* frozen copy there is no author to have made a typo — absence can only mean "trained before the key existed" (§A6, measured: 460 configs lack `thermal`, 33 have it, none has the block without the gate key). Applying a rule outside the population it was written for is not caution; it is cargo-culting.
  3. **The flag's own failure mode argues against it at this scale.** A flag that must be passed for ~93 % of the archive stops being a decision and becomes muscle memory. It then *reads* as deliberate in a command log while carrying no thought, which is a worse audit trail than an automatic substitution that prints what it did.
  4. **Decisive: the choice is not "silent substitution or none". It is "an unbounded implicit one that nobody chose, or a bounded enumerated one that is logged and tested."** §A11 measures the status quo: 77 saved configs already get an *automatic, silent, unbounded* shim today, because `load_env_config` resolves their fossil `extends:` line and merges the whole of today's `default.yaml` underneath them. Nobody opted into that; there is no flag, no log line, and no pinned value. Making this plan opt-in would leave that intact while adding a flag on top of it. Making it automatic and enumerated *replaces* it with five values that each name the branch that makes them true.

  **What stops this becoming the substitution that comment warns about**, concretely: (a) an enumerated table — a sixth mandatory key is not defaulted, it fails loudly, which is the property `plan-reviewer` independently agreed makes the position defensible; (b) refusal when the key is present; (c) refusal when a gated block exists without its gate; (d) refusal on a renamed predecessor spelling; (e) an INFO line naming every key supplied and the source path; (f) the supplied map persisted into any artifact the tool writes (`saved_config_compat` in the trajectory-store manifest, §A10), so the substitution is auditable *after* the log has scrolled away — not just at the moment it happens.

  **Honest statement of what the guard is and is not.** The `configs/`-path refusal is a *convention* check — it catches a live config handed to the shim by mistake, but a future author could still wire the shim into the live loader and the path check would never see it. The live guarantee therefore rests on a different, structural property: **no module on the training path imports `saved_config_compat`.** That is the property the test suite must pin (§Stage 3, and finding 4 of the review), and the plan's first draft did not pin it.

  **Fallback if the user prefers opt-in:** a single `--legacy-config-compat` flag threaded through all five sites. The module is byte-identical either way, so this stays a late-binding decision — but note that opt-in does *not* restore strictness for the 77 `extends:` configs, which are silently shimmed today by a different mechanism regardless of what this plan does.
- **Never a fallback default.** The module supplies keys *only* when handed a path outside `configs/`, refuses when the key is already present, and refuses when a block is present but its gate key is not. `config.get('thermal.enabled', False)` remains forbidden everywhere.
- **Loud.** One INFO line per invocation naming every key supplied and the source path, in the style of `modulation_compat`'s. A substitution nobody can see in a log is a substitution nobody can audit.

**Staging.** Stage 1 unblocks the 32 target runs and is independently shippable. Stage 2 absorbs the sensory keys and the remaining call sites. Stage 3 is the recurrence guard. If the reviewer wants to cut scope, cut Stage 2 — not Stage 3.

**Staging note added in revision:** the two hazards the review surfaced — the store fingerprint (§A10) and the `extends:` fossil (§A11) — both live entirely in **Stage 2**. Verified: neither Stage 1 site computes a fingerprint or opens a trajectory store (`replay.py` builds an environment only; `trajectory_glm.py` receives a store path from `--store` and computes no hash). So Stage 1 remains exactly what it was — the narrow fix for the 32 runs, with no exposure to either hazard — and the parts a reviewer might want to slow down are separable from it.

### File Changes

#### NEW — `src/environment/saved_config_compat.py`

Module docstring must state, in the `modulation_compat` register: what it does, what it deliberately does not do (soften the live path), and that it writes nothing to disk.

```python
"""Read-only compatibility layer for SAVED run configs (archived-run re-analysis).
... (see modulation_compat.py for the register; state the live-path asymmetry explicitly)
"""
from pathlib import Path

# Each entry: dotted key -> (value that reproduces the pre-feature behaviour,
#                            commit that made it mandatory, one-line justification).
# A value here is a CLAIM ABOUT WHAT THE OLD CODE DID and must name the branch
# that makes it true. Do not add an entry without one.
#
# CHANGING A VALUE HERE IS A BREAKING CHANGE for any trajectory store already
# collected under the old value. It has happened before, unrecorded: the historical
# table in collect_trajectories.py carried five keys including the OLD spelling
# `olfactory_sensor_range`, and the eight stores collected under it can no longer be
# resumed at HEAD (§A10). The manifest's `saved_config_compat` map exists so the next
# such change fails loudly instead of silently.
_ERA_KEYS = {
    # Stage 1
    "thermal.enabled": (
        False, "dd3b5dfa",
        "gate; config_loader.py:1592 else-arm reads no other thermal key, and every "
        "runtime consumer sits behind a static `if params.thermal_enabled:` "
        "(core.py:77/247/854/913/1773, sensor.py:485/541). Parity instrument: "
        "tests/env/test_thermal_parity.py"),
    # Stage 2 — moved verbatim from collect_trajectories.PRE_V31/V32_SENSOR_DEFAULTS
    "sensory.visual_value_mode":        ("sum",  "9771e98c", "original per-cell accumulation"),
    "sensory.visual_occlusion_enabled": (False,  "9771e98c", "static branch in sensor.py"),
    "sensory.olfactory_grid_range":     (0,      "0949ddb2", "0 = original single-point sample"),
    "sensory.visual_blur_enabled":      (False,  "0e8a4ef8", "blur knobs conditional-mandatory since 35a26452"),
}

# A block whose gate key is missing but whose block EXISTS is the typo case the
# mandatory-key rule exists to catch. Never supply into one.
_GATE_KEYS = {"thermal": "enabled"}

# Renamed predecessors: if the OLD spelling is present, the run predates the
# rename and its real value must not be silently replaced by the era default.
_RENAMED_FROM = {"sensory.olfactory_grid_range": "sensory.olfactory_sensor_range"}


def apply_saved_config_compat(cfg: dict, *, source: str) -> list[str]:
    """Supply era keys a frozen run config predates. In memory only.

    Raises if `source` resolves under `configs/` (the live path must keep
    hard-erroring), if a key it would supply is already present, if a gated
    block is present without its gate key, or if a renamed predecessor spelling
    is present. Returns the sorted list of keys supplied.
    """
```

Behavioural requirements the developer must implement exactly:

1. Resolve `source`; if it is under the repo's `configs/` directory, raise `ValueError` naming the path — the live path is structurally excluded, not excluded by convention.
2. For each key in `_ERA_KEYS`: if already present in `cfg`, skip it silently (a later-era run legitimately sets it). If **any** key in a group is present while others are missing, that is fine — keys are independent.
3. If a gated block exists but its gate key does not (`thermal:` present, `thermal.enabled` absent), raise — do not supply.
4. If a renamed predecessor spelling is present, raise with the old and new names.
5. Print one INFO line listing every key supplied, its value, and `source`.
6. Mutate a **copy** if the caller passes one; the docstring must say which. (Recommendation: mutate `cfg` in place and return the supplied map, since callers need both the patched dict and the map — the latter now goes into the trajectory-store manifest, §A10.)
7. **Return a `{dotted key: value}` map, not just a list of key names** (revision; §A10). The value is what the table-drift guard compares, and a bare list cannot detect that `olfactory_grid_range` was supplied as `0` in one collection and something else in another. `apply_sensor_compat`'s list-of-names return is the shape that let the 2026-07 table drift go unrecorded.
8. **Drop `extends:` if present, and log it** (§A11). `raw.pop("extends", None)` with an INFO line naming the dropped target and the `22c73bac` bug row. Do **not** resolve it: the trainer of that era ignored it.
9. **The module must not import anything from `src/environment/config_loader.py` or `src/utils/config.py` at module scope**, so the import-graph test in Stage 3 stays a one-directional check with no cycle to reason about.

#### Stage 1 — `scripts/analysis/nmn/replay.py` (lines 82–84)

```python
# BEFORE:
    cfg_path = os.path.join(models_dir, "config.yaml")
    cfg = Config.load_yaml(cfg_path)
    env_params = load_env_params(cfg)

# AFTER:
    from src.environment.saved_config_compat import apply_saved_config_compat
    cfg_path = os.path.join(models_dir, "config.yaml")
    _raw = yaml.safe_load(open(cfg_path))
    apply_saved_config_compat(_raw, source=cfg_path)
    cfg = Config(_raw)
    env_params = load_env_params(cfg)
```

`Config.load_yaml` must be replaced by an explicit `yaml.safe_load` + `Config(...)` so the shim can see the dict. Add `import yaml` at module scope if absent.

#### Stage 1 — `scripts/analysis/trajectory_glm.py` (line 54)

```python
# BEFORE:
    p = load_env_params(Config(yaml.safe_load(open(f"{run}/models/config.yaml"))))

# AFTER:
    _cfg_path = f"{run}/models/config.yaml"
    _raw = yaml.safe_load(open(_cfg_path))
    apply_saved_config_compat(_raw, source=_cfg_path)
    p = load_env_params(Config(_raw))
```

#### Stage 2 — `scripts/eval/traj_collect/collect_trajectories.py` (lines 296–347, 713–726)

- Delete `PRE_V31_SENSOR_DEFAULTS`, `PRE_V32_SENSOR_DEFAULTS` and `apply_sensor_compat`; their content moves into `_ERA_KEYS` **verbatim, comments included** — those comments carry the parity evidence and must not be lost. **One carve-out (§A10a):** the two lines at `collect_trajectories.py:311-312` asserting that patching happens *before* `env_fingerprint` are reversed by this plan and must **not** be copied; replace them with the dated reversal note given in §A10a.
- **Ordering — REVISED, and this is the change the review forced (§A10).** Compute `env_fingerprint` on the config **as read from disk, before the shim**, then apply the shim. Concretely: after `cfg = yaml.safe_load(f)` at line 700, take `raw_fp = env_fingerprint(cfg)` first; then call `apply_saved_config_compat(cfg, source=str(cfg_path))`; then continue as today. `store_dir` (line 744) and the manifest's `env_fp` both use `raw_fp`. The first draft had this backwards and would have forked all 110 existing stores.
- **New manifest field `saved_config_compat`** in `build_manifest` (line 352): the exact `{dotted key: value}` map the shim supplied, `{}` when it supplied nothing. This is what replaces the fingerprint as the table-drift guard.
- **`assert_manifest_compatible` gains a dedicated comparison for it** in `src/utils/trajectory_store.py` — **not** an entry in `MANIFEST_GUARDED_FIELDS`. Reason, verified: that tuple is checked with `_req` (line 478), which raises on a key that is missing *or* `None`; all 110 existing manifests lack the field, so guarding it would hard-error every legacy store. Required behaviour: field absent in the stored manifest → `warnings.warn` naming the store and saying its compat set is unknown (same register as the existing `collection_git_sha` warning at line 560); field present and different → `ValueError` printing both maps.
- **Do not bump `SCHEMA_VERSION`** (line 60). No parquet column changes, and `schema_version` *is* guarded — a bump rejects every existing store.
- `resolved_env_config` in the manifest stays **post-shim** (it is the config the episodes were generated under). Only the fingerprint moves. State this in a comment; the two now deliberately disagree, and a future reader will otherwise assume it is a bug.
- Keep `--assume-pre-v31-sensors` / `--assume-pre-v32-sensors` as accepted no-op flags that print a deprecation line. **The line must name the ordering change, not just the automation** (§A10a) — e.g. "now applied automatically for saved run configs; the env fingerprint is taken BEFORE the substitution, so this run resolves to a different store directory than it would have under this flag (plan §A10a)". Recorded invocations exist in `docs/experiments/active/trajectory_factors/nmn_film_vs_unmodulated.md:233`; silently removing them breaks a documented command.
- Thread `pre_v31_sensor_keys=` in `build_manifest` (line 356) from the shim's return value so the manifest keeps recording which keys were supplied. Rename the parameter only if the developer also updates `tests/test_trajectory_collection.py`.

#### Stage 2 — `scripts/eval/eval_rollout.py` (lines 949–1007)

This is the only site that may receive **either** a live or a saved config, so it needs discrimination — the same asymmetry `modulation_compat` already gets right at line 1063 via `agent_config_source`.

```python
# In _resolve_entry, after config_path_i is determined (line 958) and BEFORE
# load_env_config at line 959:
#   - resolve config_path_i
#   - saved := it lies under the checkpoint root (ckpt_root / "config.yaml", or a
#     per-stage sibling produced by _resolve_continual_stage_config)
#   - if saved: read the YAML, apply_saved_config_compat(..., source=config_path_i),
#     and build the Config from the patched dict
#   - else: today's load_env_config(config_path_i) unchanged
```

**`extends:` handling — REVISED (§A11).** The first draft claimed no frozen config carries `extends:` and told the developer to raise on presence. That is wrong and would have hard-errored 77 runs: **77 of the 493 saved configs carry `extends:`** (2026-06-19 → 07-03), the era of the recorded "Config inheritance ignored" bug (`KNOWN_BUGS.md:316`, fixed in `22c73bac`).

Required behaviour:

- **Live branch:** `load_env_config(config_path_i)` unchanged — `extends:` is resolved exactly as today (line 959).
- **Saved branch:** `raw.pop("extends", None)` — **drop it, do not resolve it.** The trainer that produced those runs ignored `extends:`; resolving it now would rebuild a world the run never had. Then apply `apply_saved_config_compat` and build the `Config` from the patched dict.
- **Print it.** One INFO line per occurrence: the dropped target, the run name, and a pointer to the `22c73bac` bug row. This is a real behavioural change for 77 runs and must not be silent.
- **Verified sufficient, measured on all 77 rather than a sample:** with `extends:` dropped and the five era keys applied, `load_env_params` succeeds on **77 / 77**; without the era keys it fails on `sensory.visual_value_mode`. See CP12.

#### Stage 2 — `scripts/analysis/supplementary/parity.py` (lines 22–31)

**Not the same edit shape as `trajectory_glm.py` — this one REMOVES keys** (review finding 6). The script currently hand-injects **five** keys via its own `NEW` dict: `olfactory_grid_range: 0`, `visual_blur_enabled: False`, and three blur knobs at `0.0` (`visual_blur_radial_scale`, `visual_blur_anisotropy`, `visual_blur_sigma_floor`). Today's `_ERA_KEYS` carries only the first two, because commit `35a26452` made the three knobs *conditional*-mandatory — read only when `visual_blur_enabled` is true. So replacing `NEW` with the shim drops three injections.

The developer must show that this changes nothing rather than assert it: build `EnvParams` both ways (script's current five-key `NEW` dict vs. the shim) and assert field-by-field equality. Record the result in the Implementation Report. If they are not equal, stop — the era table is wrong, not the script.

**Also note, and this is why the script is in scope at all:** `parity.py` **does not run at HEAD**. Measured — it raises `ValueError: Configuration key 'sensory.visual_value_mode' is required but missing`, because its `NEW` dict predates the v3.2 keys (§A12). Its recorded 2.4e-07 result stands as historical evidence, but the script cannot be re-run to re-confirm it until this edit lands. Restoring it to runnable is a deliverable of Stage 2, not a side effect — and re-running it is the strongest available end-to-end check on the sensory half of the table.

#### Stage 3 — NEW `tests/fixtures/saved_config_eras/*.yaml` (5 files, ~9.5 KB each)

Copy one real frozen config per era, renamed to describe the era, with a `README.md` naming the source run and its training date. Five, not four — the review surfaced a fifth era (the `extends:` fossil) that the first draft did not know existed:

| Fixture | Source run | Era it represents |
|---|---|---|
| `era_2026-06-19_extends_fossil.yaml` | `20260619-004318_rppo_basic00_forage_n113` | carries `extends: environment/default`; needs all five keys **and** the drop (§A11) |
| `era_2026-08-16_pre_v32.yaml` | a `20260816-*_rppo_restpremNH_*` run | needs all five keys |
| `era_2026-08-26_mid_v32.yaml` | `20260826-144838_sens_D_vision_blur_n114g3` | needs three keys |
| `era_2026-09-07_pre_thermal.yaml` | `20260907-045531_rppo_nmnsite_t1none_s42` | needs `thermal.enabled` only |
| `era_2026-09-09_current.yaml` | `20260909-023638_rppo_olfmc_t1none_s42` | needs nothing |

These are committed because `results/` is gitignored — without them the recurrence guard cannot run in CI.

#### Stage 3 — NEW `tests/environment/test_saved_config_compat.py`

Named tests, mirroring `tests/models/test_modulation_compat.py`'s structure and its file-level docstring explaining the asymmetry:

| Test | Asserts |
|---|---|
| `test_no_live_path_module_imports_the_shim` | **This is the test that pins the live guarantee** (review finding 4). Parse `train.py`, `src/environment/config_loader.py`, `src/utils/config.py` and `src/algorithms/dreamer_srl/dreamer_srl_main.py` with `ast`, walk every `Import` / `ImportFrom`, and assert none references `saved_config_compat`. Then sweep every `*.py` under `src/` (excluding the module itself) and assert the same, so the only importers live under `scripts/`. Fails the moment someone wires the shim into the live loader — which is precisely the failure the first draft's test could not see. |
| `test_live_loader_still_hard_errors_on_a_missing_mandatory_key` | Copy `configs/environment/default.yaml` to a temp dir, delete `thermal.enabled`, and run the **live entry point** `load_env_config` → `load_env_params`; assert `ValueError` matching `thermal.enabled`. Uses the live function, not the internal one. |
| `test_live_config_missing_thermal_enabled_still_hard_errors` | Kept as a plain regression check on `load_env_params` with the key deleted. **Explicitly NOT the live guarantee** — the loader was never the thing in doubt, and this test cannot fail if the shim is later wired into `load_env_config`. The docstring must say so, so nobody mistakes it for the guard again. |
| `test_compat_refuses_a_source_path_under_configs` | `apply_saved_config_compat(cfg, source="configs/environment/default.yaml")` raises. A **convention** guard — it catches a live config handed to the shim by mistake. It is not the live guarantee; `test_no_live_path_module_imports_the_shim` is. |
| `test_saved_config_with_thermal_block_but_no_enabled_key_still_hard_errors` | A dict with `thermal: {sigma: 0.7}` and no `enabled` raises — the typo case stays loud. |
| `test_saved_config_that_already_sets_a_key_is_left_alone` | A config with `thermal.enabled: true` is not overwritten and is not reported as supplied. |
| `test_renamed_predecessor_spelling_is_refused` | `sensory.olfactory_sensor_range` present raises, naming both spellings. |
| `test_supplied_thermal_off_equals_an_explicit_thermal_off_config` | `EnvParams` built from (pre-thermal fixture + shim) is field-by-field equal to `EnvParams` built from (same fixture + literal `thermal: {enabled: false}`). Proves the shim adds nothing beyond the key. |
| `test_every_era_fixture_loads` | Each of the four fixtures rebuilds via shim + `load_env_params`. **This is the recurrence guard**: the next mandatory key turns this red at CI time. |
| `test_era_fixture_from_the_current_era_needs_no_keys` | The 2026-09-09 fixture has an empty supplied-key list — proves the earlier fixtures are failing for era reasons, not because the shim always fires. |
| `test_saved_config_with_extends_is_dropped_not_resolved` | A fixture carrying `extends: environment/default` rebuilds via the saved branch **without** the base being merged: assert a key that exists only in `default.yaml` and not in the fixture is absent from the resulting config, and that the drop was logged (§A11). |
| `test_fingerprint_is_taken_before_the_shim` | `env_fingerprint` of the pre-thermal fixture equals the fingerprint computed on the raw dict, and is **unchanged** by `apply_saved_config_compat`. Pins §A10's decision so a later refactor cannot quietly reorder the two calls. |
| `test_legacy_manifest_without_the_compat_field_warns_and_does_not_raise` | `assert_manifest_compatible` against a manifest fixture shaped like today's 110 (no `saved_config_compat` key) emits a warning and returns. Guards against the `_req` trap in §A10 — the failure mode where this plan's fix breaks every existing store. |
| `test_manifest_compat_field_mismatch_raises` | Same call with a *different* supplied map raises, naming both maps. The table-drift guard that replaces the fingerprint's role. |

Every one of the first five must **fail on pre-fix code by not existing**; `test_every_era_fixture_loads` must fail on pre-fix code because `apply_saved_config_compat` is absent — the developer must record, in the Implementation Report, the pre-fix failure of a temporary variant that calls `load_env_params` directly on the pre-thermal fixture (this is the test that reproduces the reported bug).

#### `docs/environment/CONFIG_GUIDE.md`

Add a short subsection "Reading a finished run's frozen config" under the authoring section: the live/saved asymmetry, the module that implements it, and the rule that a new mandatory key requires an `_ERA_KEYS` entry **and** a new era fixture in the same commit. Required by that guide's Maintenance Contract because this changes how configs are loaded, though not the schema.

#### `docs/environment/SCRIPTS_DEPENDENCY_MAP.md`

Listed because four files under `scripts/` gain a new dependency on `src/environment/saved_config_compat.py`. No file under `scripts/` is added, moved, renamed or deleted, so this is an edge update, not a structural one.

#### `docs/environment/CONFIG_CRITICAL_SETTINGS.md` — **no change required**

Stated explicitly so a reviewer does not have to work it out: this plan alters no value of any registry setting. It changes only what happens when a *frozen* config omits a key. No dated change-log entry is due.

---

## Checkpoints

Verify **during** implementation, in order:

- [ ] **CP1 — Reproduce before fixing.** Run the §A1 command; confirm the `thermal.enabled` `ValueError`. Paste it into the Implementation Report.
- [ ] **CP2 — Stage 1 unblocks all 32 target runs, not just one.** Loop `load_env_params` through the shim over all 16 `*_rppo_nmnsite_*` and 16 `*_rppo_nmngaenorm_*` frozen configs; expect 32 / 32 and exactly one supplied key (`thermal.enabled`) each.
- [ ] **CP3 — The live guarantee is intact.** `pytest tests/environment/test_saved_config_compat.py -k "hard_errors or refuses" -v` green, and `pytest tests/models/test_modulation_compat.py` still green (the two shims must compose).
- [ ] **CP4 — The substitution changes nothing but the key.** `test_supplied_thermal_off_equals_an_explicit_thermal_off_config` green, and `pytest tests/env/test_thermal_parity.py` still green — the pre-existing instrument for "thermal-off equals pre-thermal" must not have moved.
- [ ] **CP5 — Archive-wide count, measured not assumed, and stated as an invariant rather than a total.** Re-run the §A2 cascading sweep with the shim in place. **Do not compare against a hard-coded total** — the archive grows (477 → 493 during this plan's own review), so a fixed number will falsely fail. The expectation is: *every frozen config rebuilds **except** the 150-run pre-v2.0 tail*, i.e. `rebuildable == total_files_found - 150` and `failures == 150`, with the total measured at run time and reported. A failure count that is not 150 means the table is wrong (or a new era has appeared); report it rather than adjusting the table to match.
- [ ] **CP6 — The 150 still fail loudly.** Confirm the remaining failures are the two legacy-schema errors and are unchanged in message — the shim must not have turned a loud failure into a quiet one.
- [ ] **CP7 — Fingerprint ordering preserved.** In `collect_trajectories.py`, confirm the shim runs before `env_fingerprint(cfg)` and that `build_manifest` still records the supplied keys. `pytest tests/test_trajectory_collection.py` green.
- [ ] **CP8 — Nothing written to disk.** Record `md5sum` of the 32 target frozen configs before and after the full test run; they must be identical. This is the one property the whole design rests on.
- [ ] **CP9 — Speed.** This is a load-time-only change on a path that runs once per analysis invocation and never inside a training step; no training-loop code is touched. State that in the Implementation Report **with the diff as evidence** (no file under `src/algorithms/` or `src/models/` modified). If the diff does touch a training path, a before/after speed measurement is required instead.
- [ ] **CP10 — Full suite.** `pytest tests/env tests/environment tests/models -q` green.
- [ ] **CP11 — A top-up resumes rather than forks. This is the check that protects GPU time (§A10).** Dry-run only, writing nothing: for every one of the ~110 real stores under `results/trajectories*/*/*/*/`, load `_manifest.json`, read its `run_path`, load that run's saved `config.yaml` **raw**, compute `env_fingerprint` on it, and compare to the directory name. Expect **101 matches and exactly the 9 known non-matches enumerated in §A10** (8 under `trajectories_nmn/`, 1 under `trajectories_sens/`). Then, for one real pre-thermal run with an existing store, run `collect_trajectories.py` with `--episodes` set to the store's existing `n_episodes` and confirm from its own stdout that it resolves to the **existing** `store_dir` and reports **0 blocks remaining** — i.e. it resumes into the old directory and collects nothing. Abort before any write if the resolved `store_dir` differs from the existing one. Paste the store path and the blocks line into the Implementation Report.
- [ ] **CP12 — The 77 `extends:` configs, measured on all 77 (§A11).** With `extends:` dropped and the shim applied, loop `load_env_params` over every saved config matching `grep -l '^extends:' results/*/*/models/config.yaml`. Expect **77 / 77 OK**. Also confirm the negative control: without the era keys the same loop fails on `sensory.visual_value_mode`, proving the era table is what makes them load and the `default.yaml` merge is not needed.
- [ ] **CP13 — `parity.py` runs again, and measures the same thing (§A12, §Stage 2 parity.py).** Before the edit, record the `ValueError: ... 'sensory.visual_value_mode' ...` it raises at HEAD. After the edit, run it and record the max observation difference; it must stay at the recorded ~2.4e-07 order, not merely "pass". Separately assert field-by-field `EnvParams` equality between the script's old five-key `NEW` dict and the shim's two keys, proving the three dropped blur knobs were inert. **This checkpoint is load-bearing for the fingerprint decision, not only for restoring the script (§A10a).** The a01 ground truth was recorded 2026-08-20 and therefore predates the v3.2 features, so the post-fix run is the **first measurement** covering `sensory.visual_value_mode` and `sensory.visual_occlusion_enabled`, which until now rest on a reading of the static branches at `sensor.py:389/394`. If the number is not of the recorded ~2.4e-07 order, **stop**: those two keys are not inert, resuming a pre-v3.2 store is not safe, and §A10a must be re-opened. Do not widen the tolerance to make it pass.
- [ ] **CP14 — Legacy manifests still open.** `test_legacy_manifest_without_the_compat_field_warns_and_does_not_raise` green, and a real legacy manifest (e.g. `results/trajectories_nmnsite2/…/_manifest.json`) passes `assert_manifest_compatible` with a warning and no exception. Confirms the new field did not land in `MANIFEST_GUARDED_FIELDS` and `SCHEMA_VERSION` was not bumped.

---

## Implementation Report

> **Implemented by**: [agent/person]
> **Date**: [date]

<!-- Filled by the implementing agent. Must include: the CP1 pre-fix error text; the CP5 measured
     split reported as "<total measured> total, <n> rebuildable, 150 legacy failures" (no hard-coded
     total); the CP8 md5 comparison; the CP9 speed justification with its evidence; the CP11 resume
     evidence (store path + "0 blocks remaining" line); the CP12 77/77 result; and the CP13
     before/after parity numbers. -->

## Verification Report

> **Verified by**: [agent/person]
> **Date**: [date]

| File | Change | Status | Notes |
|------|--------|:------:|-------|
| | | | |

**Conclusion**: [one-line summary]

---

## Open questions for the reviewer

1. **Automatic vs. opt-in** (§Design, decision 2). **Still recommended automatic, and the recommendation is stronger after review**, because §A11 measured that the status quo already applies an automatic, silent, *unbounded* shim to 77 saved configs via `extends:` resolution. The choice is between that and a bounded, enumerated, logged, tested one — not between substitution and strictness. The fallback remains one `--legacy-config-compat` flag threaded through five sites; the module is identical either way. **This is the decision to give the user explicitly**, since it is the one the file's own author would have argued the other way.
2. **Stage 2 scope.** Absorbing the four sensory keys is what takes the fix from 120 runs to 327. It is also the part that edits a working script (`collect_trajectories.py`). Cutting it is defensible; cutting Stage 3 is not.
3. **Bug registry.** Once this lands, `bug-curator` should record the `results/`-population instance (distinct from the recorded `configs/` row), plus the two unrecorded legacy breakages `environment.predator_enabled` and `Resource: properties_std`, plus two more the review surfaced: **`parity.py` cannot run at HEAD** (§A12) and **the historical sensory-table drift orphaned 8 trajectory stores from resume** (§A10, no data loss, complete stores, recorded so nobody re-derives it).
4. **The eight orphaned stores** (§A10). The plan's recommendation is to leave them: they are complete (200/200 blocks, 1M episodes) and unreachable-by-resume already at HEAD, so nothing is lost. The alternative — renaming the directory and editing `env_fp` inside the manifest — is a write into `results/`, which this plan otherwise never does. **Recommend no action; flagging it so the user makes that call rather than inheriting it.**

---

## Revision log — 2026-09-09, response to plan-reviewer

Every 🟡 and 🟢 finding below is addressed in the body of the plan rather than only acknowledged here. The two facts the reviewer flagged as unverified were **verified rather than inherited**, and one of them changed a decision.

| Finding | Where it is now answered | Outcome |
|---|---|---|
| **Follow-up 2026-09-10 — the fingerprint decision did not argue with the convention it reverses** | **new §A10a**, Context (motivation), CP13 re-scoped | The `collect_trajectories.py:311-312` post-shim convention is now quoted and answered rather than routed around, in the same register as §A3 property 4. Equivalence-class argument made explicitly and audited **per key**: it holds for all five, on three grades of evidence — `thermal.enabled` and the two v3.1 sensory keys are replay-measured, while `visual_value_mode` and `visual_occlusion_enabled` rest on static trace-time branches because `parity.py`'s ground truth predates them. **CP13 is now load-bearing for this decision**, being the first measurement that will cover those two. Old-vs-new stamping reconciled with measured hashes on `sens_A_baseline`; the old behaviour is **deleted, not left alone**, with a carve-out to the verbatim-comment instruction so the reversed sentence is not copied into the new module. |
| 🟡 1 — fingerprint drift | **new §A10**, revised `collect_trajectories.py` entry, new **CP11**, two new tests | **Decision: fingerprint PRE-shim.** Measured: 0/110 existing stores are post-thermal, and 101/110 reproduce their recorded fingerprint from the raw file, so pre-shim hashing is the only rule under which existing work resumes. The 9 that do not are enumerated and dispositioned (8 already orphaned at HEAD by a *previous* table change and complete at 1M episodes; 1 is an empty aborted store). Table-drift protection moves to a new `saved_config_compat` manifest field with a tolerant legacy path. |
| 🟡 1a — "are all 118 stores pre-thermal?" (left unverified by the reviewer) | §A10 | **Verified.** There are **110** stores, not 118 — the glob also catches 8 `_scratch/_run_markers` and `_worklists` folders. **0 / 110** carry a `thermal:` block. |
| 🟡 1b — "does the contiguity assert actually fire on duplicate seeds?" (left unverified) | §A10 note below | **Verified — it fires**, but there is a caveat the reviewer's read could not see. |
| 🟡 2 — 77 saved configs carry `extends:` | **new §A11**, rewritten `eval_rollout.py` entry, new **CP12**, new fixture + test | **Decision: DROP `extends:` on the saved branch, do not resolve it**, and log the drop. Verified on **77/77**, not a sample. The reviewer's related observation is not just noted but promoted to the plan's central argument — see finding 3. |
| 🟡 3 — the precedent's fourth property | **§A3 property 4** (quoted in full), **§Design decision 2** (rewritten, four numbered answers) | **Argued, not routed around.** Recommendation stays *automatic*, on new evidence: §A11 measures that the status quo already applies an automatic, silent, unbounded shim to those 77 configs. Fallback to opt-in remains one flag, and is flagged to the user as the decision to make. |
| 🟡 4 — the live-guarantee test | **Stage 3 test table** | **Replaced.** The pinning test is now `test_no_live_path_module_imports_the_shim` (AST walk over `train.py`, `config_loader.py`, `config.py`, `dreamer_srl_main.py`, plus a sweep of `src/`). The old test is kept, demoted, and its docstring must say it is *not* the guarantee. The `configs/`-path guard is now described as convention, in both §Design and the test table. |
| 🟢 5 — CP5's hard-coded 327/477 | **CP5** | Rephrased as an invariant: `failures == 150`, total measured at run time. The finding proved itself during review — the archive moved 477 → 493. |
| 🟢 6 — `parity.py` removes keys | **Stage 2 `parity.py` entry**, **new §A12**, new **CP13** | Corrected, plus a new measured fact: `parity.py` **does not run at HEAD** (raises on `sensory.visual_value_mode`). The instrument supplying this plan's own evidence is one of the broken call sites. |
| 🟢 — §A5 said 34 fixtures | **§A5** | Corrected to **72**. |
| — archive 477 → 493 | Context, §A2, §A11 | Updated throughout; clean set 33, post-shim total 343. §A2 now says explicitly that totals move and chain counts do not. |

**The contiguity-assert caveat (🟡 1b).** The check in `hiding_drivers.aggregate` (`scripts/analysis/hiding_drivers.py:136`) is `seed.max() - seed[0] + 1 != len(seed)`. Simulated on the actual scenarios: a sibling store re-collected at the **same** seed base **fires** (`SystemExit`), as does any partial overlap or gap; only a genuinely disjoint continuing seed base passes, which is the intended multi-pass design. So duplicate episodes from a forked store would be caught loudly — **provided `aggregate` runs**. It often will not: `main` skips it entirely when `aggregate.npz` already exists (line 359, `and not os.path.exists(cache)`), and **9 such caches exist today** under `results/analysis/hiding_drivers/`. For those runs a forked store would be silently ignored and the stale cache reused. That is a pre-existing hazard this plan does not create and does not fix; it is recorded here, and it is a second reason to prefer the pre-shim fingerprint, which never creates the fork in the first place.

**Scope decision upheld and not re-argued.** The 150-run pre-v2.0 tail stays out of scope (§A2, §A7). The reviewer re-derived the chain counts independently through the real analysis load path and they reproduced exactly (184 / 150 / 120 / 6).

**Reproducer confirmed on the real path, by the user.** `load_env_params` was run directly on three of the grid runs (`t2enc_I`, `t2enc_X`, `t2enc_ALL`); each raised `ValueError: Configuration key 'thermal.enabled' is required but missing` — the same call `replay.py:82-84` makes. This is the production load path, not a tooling-loader artifact.

---

## Feedback from plan-reviewer

**Verdict: SOUND WITH CONCERNS** (2026-09-09). No Critical finding; no `docs/reviews/` file written. Full inline report returned to the parent session. Evidence: independent cascade sweep `tmp/20260909_plan_review_sweep.{py,json,log}`; `tests/env/test_thermal_parity.py` run log `tmp/20260909_plan_review_parity_pytest.log` (72 passed, 285 skipped).

**Independently confirmed.** The chain counts reproduce exactly (184 / 150 / 120 / 6) through the same load path the analysis tools use; the archive has grown to **493** files (16 `olfgae` runs launched 16:11 today), so the clean set is 33 and the post-shim total is 343 — the arithmetic is right, the snapshot is stale. `thermal.enabled: false` is sufficient (else-arm calls `get_mandatory` zero times; no pre-thermal saved config declares an entity `temperature`/`temperature_ratio`). Zero saved configs carry `olfactory_sensor_range`; all 47 with `olfactory_grid_range: 1` carry it explicitly, so the B_olf hazard is absent. `test_thermal_parity.py` is a real comparator (72 committed `.npz` adjudicated), not one of today's empty gates. Nothing in the plan writes to `results/`.

**Must be resolved by the author before implementation (all 🟡 Moderate):**

1. **Fingerprint drift is unaddressed.** `env_fingerprint` (`src/utils/trajectory_store.py:428`) hashes the whole dict, so the shim changes `env_fp` for every pre-thermal run — i.e. for all ~118 existing stores (sample: `results/trajectories_nmnsite2/…/a4cbd376c9/_manifest.json` has no `thermal` in `resolved_env_config`). Post-shim `collect_trajectories` on any of those runs silently opens a *new* sibling `<env_fp>/` dir instead of resuming, and `hiding_drivers.find_stores` with `--checkpoint` unions sibling dirs. Decide and state: fingerprint pre- or post-shim, and what happens to the existing stores.
2. **77 saved configs carry `extends:`** (2026-06-19 → 07-03, the era of the recorded "Config inheritance ignored" bug, `KNOWN_BUGS.md:316`, fixed `22c73bac`). §Stage 2 eval_rollout says none do and proposes to raise on presence; that would hard-error those 77 at one site. Faithful handling is to *drop* `extends:` on the saved branch (the trainer ignored it), citing the registry row. Note also that HEAD's `load_env_config` already fills their missing keys from `default.yaml` via `extends:` resolution — a pre-existing silent shim.
3. **The "right precedent" argues against you on the one contested decision.** `collect_trajectories.py:308-311` says the flag is "deliberately an explicit opt-in flag and NOT a default … the no-fallback-defaults rule exists to stop exactly this kind of silent substitution". §A3 lists its three properties and omits this fourth. Argue with that text explicitly in §Design decision 2; do not route around it.
4. **The live-guarantee test cannot fail in the way that matters.** `test_live_config_missing_thermal_enabled_still_hard_errors` exercises `load_env_params` on a dict with the key deleted — the loader was never in question. The property to pin is that the *trainer's* path never reaches the shim: assert `train.py` / `load_env_config` / `config_loader.py` do not import `saved_config_compat` (or run `load_env_config` on a temp copy of `default.yaml` with `thermal` removed). The `configs/`-path guard is convention, not structure — say so.

🟢 Low: §A5 says 34 fixtured configs (it is 72); CP5's hard-coded 327/477 will trip its own "any other number means the table is wrong" rule — express it as "all but the 150 legacy tail"; `parity.py` already hand-injects blur knobs, so the edit removes keys rather than mirroring `trajectory_glm.py`.

Reviewed by: plan-reviewer
