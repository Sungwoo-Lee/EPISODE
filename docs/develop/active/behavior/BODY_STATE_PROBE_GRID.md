---
title: "Behaviour probes that set injury, fullness and body temperature together (body-state grid)"
topic: behavior
status: active
created: 2026-09-26
last_updated: 2026-09-26
---

# Behaviour probes that set injury, fullness and body temperature together (body-state grid)

> **Status**: PLANNED, **Revision 2**. The user's decisions of 2026-09-26 are folded in (§Decisions). Two points still need the user (§Decisions, "Still open"). Revision 2 has not yet been through `plan-reviewer`; it should be, before approval, because the test-condition design changed.
> **Opened**: 2026-09-26

> **Revision 2 (2026-09-26), in response to the user's decisions.** What changed, in plain words:
> - **No test-condition files on disk.** The user found 480 generated config files per run too many. The grid is now a short **recipe file** per study: the list of injury, fullness and temperature values, the scenes, and the two temperature settings. Each test condition is assembled **in memory** at evaluation time from that recipe plus the tested run's own saved settings. Nothing per-condition is written as YAML. (Replaces Revision 1's generator, D4 folder layout and `.gitignore` change.)
> - **The strict-loading guarantee is kept, and re-derived** (§D3). Revision 1 kept the files under `configs/` because a file outside it gets missing settings quietly filled in. With no file there is no location to rely on, so the in-memory path has to be strict by construction. §D3 says exactly how, and a new test proves a missing setting still stops the run.
> - **Every condition is checked where it runs.** The rule check against the run's own loaded parameters, and the exact start-state check, now run inside the evaluation process on the very state the agent is tested in. A check failure now **stops the sweep loudly**; today a failed evaluation is only written to a marker file the sweep driver never reads (found while revising, §A6).
> - **Each run's conditions are built from that run's own settings.** The rules can no longer come from a different run by mistake, so Revision 1's "one folder per world, cross-checked against every run" step is gone.
> - **A food scene is added** (§D1): one food item on the opposite side from the bush, so a hungry, injured agent must choose between eating and hiding. Scene content is `experiment-designer`'s to confirm.
> - **The sweep driver accepts the recipe** instead of a folder of files (change 3), and a **manifest** records, per condition, everything needed to rebuild it exactly (§D4).
> - Tests, checkpoints, cost and `SCRIPTS_DEPENDENCY_MAP.md` rows are updated to match.
>
> Revision 1 (plan-reviewer findings M1–M6, L1–L2, O1–O4) is still in force except where noted; its summary is kept in git history (commit `86daf2ab`).

**Related**: [[STATE_DEPENDENT_BODY_MECHANICS]] (the level-05 body rules that motivate this) · [[INJURY_DEPENDENCE_PLAN]] (the injury-only probe battery this extends) · [[SAVED_RUN_CONFIG_COMPAT]] (how old runs' saved settings are re-opened) · [[EXPERIMENT_EVAL_DURING_TRAINING]] · `docs/experiments/active/level05_body_interactions/` (the upcoming 16-world experiment, designed by `experiment-designer`)

---

## Context

**What a behaviour probe is.** A behaviour probe is a small, fixed test scene. The trained agent is dropped into it and we record what it does. A typical scene has a 10×10 field, one bush to hide in, and sometimes a predator or a wandering rabbit. Every run is tested on the same scenes, so the runs can be compared.

**What exists today.** The current "injury grid" probes vary one thing: how injured the agent is at the start (0, 10, …, 90). Fullness and body temperature always start at their comfortable values.

**Why that is no longer enough.** Level 05 now has body rules that link the internal states (see [[STATE_DEPENDENT_BODY_MECHANICS]]): healing can slow down when the agent is hungry, healing can cost food, staying warm can cost food, and each episode starts at a random body temperature. An upcoming experiment trains agents in 16 variants of that world and asks whether behaviour depends on **combinations** of body states. For example: does an injured agent still go and hide when it is also starving and cold? And, with food in reach, does a hungry injured agent eat first or hide first?

To answer that, a probe must set three things at once, and exactly: starting injury, starting fullness (food energy) and starting body temperature.

**What this plan builds.**
1. A **recipe file** per study that lists the values to test. From it plus a trained run's own saved settings, a small library builds every test condition in memory: 480 per run in a world with a temperature system (640 if the food scene counts toward it; see §Decisions).
2. Support in the evaluation program and the sweep driver for "evaluate these recipe conditions" instead of "evaluate these config files".
3. A small fix so the standard evaluation recordings save body temperature at every step. Today they drop it.
4. A tool that turns the recordings into per-condition summaries.

The test conditions copy the run's own body rules. Without that, an agent trained where healing costs food would be tested where healing is free. Only the newest saved checkpoint of each run is tested. **Recurrent-PPO runs only** for now; Dreamer runs load their evaluation settings differently and are refused.

---

## Analysis

### A0. Wiki pull gate and known bugs

- **`start_injury` is a dead setting** (LLM Wiki `config_system/20260622_1746_start_injury_dead_needs_random_range`). To pin injury, use the random path with `low == high`.
- **`body.start_satiation` is also dead** (Known Bugs row 94). Satiation is derived from nutrition (`src/environment/core.py:1908-1909`), so "fullness" means **nutrition**. The builder never writes `start_satiation` as if it did something.
- **Probes must match the training regime** (wiki `behavior_measures/20260805_0118_regime_matched_probe_and_run_sweep_probe_dir`, `…/20260704_2012_noise_matched_frozen_probe`). This is why §D2 copies the run's rules.
- **Re-running into an old output folder mixes stale recordings** (wiki `…/20260704_2013_probe_rerun_stale_checkpoint_contamination`). §D5 makes the driver refuse an output folder whose manifest does not match.
- **Near-deterministic probes inflate significance** (wiki `…/20260704_2014_deterministic_probe_significance_inflates`). The no-animal scene and the new food scene have no randomness, so their 30 episodes count as **n = 1**.
- **Starting nutrition shortens the episode in a scene with no food** (wiki `hypervigilance/20260623_1623_nutrition_runway_confounds_hypervig_read`). See §A3. The food scene is the direct answer to this.
- **Batched evaluation drops body temperature** (§A4). Not yet in Known Bugs; `bug-curator` should record it.
- **The sweep driver never reads its own failure markers** (§A6). Not yet in Known Bugs; `bug-curator` should record it.

### A1. How a starting state is pinned (code as truth, `v4.0`, 2026-09-26)

Reset path, `src/environment/core.py:1897-1929`:

| State | How it is set at reset | How to pin it exactly |
|---|---|---|
| Nutrition (fullness) | `random_start_nutrition` true → uniform `[low, high]`; false → `start_nutrition` read directly (`:1906`) | `random_start_nutrition: false`, `start_nutrition: N` |
| Satiation | Derived from nutrition (`:1908-1909`) | Not settable |
| Injury | `random_start_injury` true → uniform `[low, high]`; false → 0.0 (`:1917`) | `random_start_injury: true`, `start_injury_low == start_injury_high == I` |
| Body temperature | `thermal.random_start_body_temp` true → uniform `[low, high]` from `body_key1`; false → setpoint (`:1923-1929`) | `thermal.random_start_body_temp: true`, `start_body_temp_low == start_body_temp_high == T` |

`jax.random.uniform` with equal bounds returns the bound exactly in float32 (verified by plan-reviewer for −10, 0, 5, 30, 60, 180). `body_key1` is split whether or not B1 is on (`core.py:1898`), so pinning T at the setpoint leaves every other random draw unchanged; §CP4 uses this as a byte-exact anchor. The range keys are **static** fields of `EnvParams` (`src/environment/state.py:456-458`): turning the flag on recompiles `jax_reset`, which can shift `animal_property_sampled` by 1 ulp (Known Bugs row 153). CP4 pre-registers exactly that tolerance.

### A2. Why conditions must copy the run's rules

`eval_rollout.py` builds the whole environment from the probe config (`_resolve_entry`, `scripts/eval/eval_rollout.py:955-975`); it never reads the run's saved config. Today's probes all `extends: environment/default`, so their rules equal `default.yaml`. The 16-world experiment sets `body.healing_nutrition_cost`, `body.healing_nutrition_dependence`, `thermal.metabolic_coupling`, B2 and B4 to non-default values on purpose. A default-based probe would switch them all back off. §D2 copies the rule sections from the run instead.

### A3. The probe window and the fullness axis

Probe episodes last `max_steps: 100`. Nutrition runs 0–200 (comfortable 100) and drops by 1.0 per step, plus the healing and thermal costs when on. In the three no-food scenes an agent starting at N = 20 starves by about step 20. That is a real outcome (survival steps are the performance measure), but behaviour after it is missing. The reducer reports survival steps and termination reason in every cell, and hiding / resting rates over alive steps only, each with its denominator.

The `fire_away` arm has the same "runway" effect for temperature (plan-reviewer O1): from −10° the body reaches the −15° floor quickly unless the agent reaches the fire, so there the temperature axis partly measures survival time.

### A4. Batched evaluation recordings drop body temperature

The sweep runs `eval_rollout.py --batched --record` (`sweep_worker.sh:74`). The batched recorder rebuilds each per-step state as a `SimpleNamespace` with nine fields (`eval_rollout.py:482-512`); `body_temp` and `thermal_field` are not among them, and the scan (`:323-345`) never collects `next_state.body_temp`. `_snapshot_state` (`src/utils/eval_recording.py:64-67`) writes `body_temp` only when present. So no batched recording of a thermal world has a body-temperature trace. The fix records `body_temp` only; `thermal_field` (a 10×10 array per step, render-only) stays a follow-up.

### A5. The existing analysis scripts are not run-agnostic

`scripts/analysis/studies/injury_dependence/scene_steps.py` and `run_manipulations.py` hard-code the ten second-wave runs, the scenes and the ten injury levels. The reducer here is a new tool that reads a **manifest**, not a run table, and never parses condition names.

### A6. How the sweep driver and the evaluation program take conditions today

- **Sweep driver** (`scripts/eval/dwell_sweep/run_sweep.py`). `probe:` names a directory; `conditions: all` globs `avoid_*.yaml` in it (`:131-152`). `build_groups` (`:168-235`) turns each condition into a file path, asserts it exists (`:206-208`), and groups all pending conditions of one checkpoint into one worklist line `CHECKPOINT|AGENT|EPISODE|CFG1,OUT1;CFG2,OUT2;…` (`write_worklist`, `:253-263`). `max_checkpoints: 1` evaluates only the newest checkpoint; `plot_measures: []` draws no figures.
- **Worker** (`sweep_worker.sh`). Turns the `CFG,OUT` pairs into a `--config-list` file (one `<cfg>\t<out>` line each) and calls `eval_rollout.py --config-list … --batched --record --seed 0`, with **stdout and stderr discarded** (`>/dev/null 2>&1`). On a non-zero exit it appends `FAIL <line>` to `_run_markers/fail_<node>`.
- **Driver never reads those failure markers.** `grep` of `run_sweep.py` finds `_run_markers` only for `done_<node>` (`:284`, `:475`). A failed evaluation therefore leaves a condition with no recordings and the driver reports success. For this plan that is decisive: a failed rule check at run time must stop the sweep, not vanish. Change 3 closes it for grid sweeps.
- **Evaluation program** (`eval_rollout.py`). `--config-list` lines are `<config_path>\t<output_root>` (`_parse_config_list`, `:778-801`). `_resolve_entry` (`:955-975`) loads each path with `load_env_config`, then applies `apply_saved_config_compat` **only when the path is outside `configs/`** (`_is_under_configs`, `:804-808`). The model is built from the first entry and every entry must share its architecture (`:1399`, `:1471`).

### A7. Where "missing settings get silently filled in" can happen, and why in-memory is safe only if built a certain way

Revision 1 kept probe files under `configs/` for one reason: a file outside `configs/` goes through `apply_saved_config_compat`, which supplies missing era keys instead of erroring. With no file, that gate no longer applies, so each fill-in route has to be closed by construction. There are exactly three routes:

1. **The compat step.** It exists for a run's own saved config, and must run on that (an old run's config lacks keys its era did not have; compat supplies the values the run actually trained under, and names every one). It must **never** run on the assembled condition. `apply_saved_config_compat` itself refuses a path under `configs/` (`saved_config_compat.py:135-139`), but an in-memory dict has no path, so the builder must simply never call it on the assembled dict.
2. **`extends:` merging.** A scene file `extends: environment/default`, so resolving it fills every section from `default.yaml`. If the run's rule sections were then *deep-merged* over it, any key missing from the run would silently keep `default.yaml`'s value. The builder must **replace** each rule section wholesale (assignment, not merge) after the scene has been resolved. A key absent from the run is then absent from the condition.
3. **Loader fallbacks.** Some keys are read with a code fallback (for example `blocks_animals`, `config_loader.py:1888`). That is a pre-existing property of the loader, identical for files and in-memory dicts; the rule check in §D3 catches any difference it causes, because it compares loaded parameters.

With those three closed, the assembled condition goes to `load_env_params`, whose `get_mandatory` calls raise on anything missing, exactly as for a file under `configs/`.

---

## Implementation Plan

### Design

**D1. The grid (decided, Q1 = 480 base; food scene see §Decisions).** Recorded in the study's recipe file, never as code defaults.

| Axis | Levels | Why these |
|---|---|---|
| Starting injury | 0, 30, 60, 90 (4) | All four are injury-grid levels, so each cell at fullness 100 and 0° has a comparison (CP4) |
| Starting nutrition | 20, 60, 100, 140, 180 (5) | Symmetric around the comfortable 100 |
| Starting body temperature | −10, −5, 0, +5 (4) | Level 05's random-start range; 0 is the anchor. Thermal-on runs only |
| Scene | no animal, predator, wandering rabbit, **food** (4) | The injury grid's three scenes plus the new food scene. The chasing rabbit stays excluded (Known Bugs row 99) |
| Temperature setting | `neutral`, `fire_away` (2) | Thermal-on runs only. In `neutral` only the start temperature varies; in `fire_away` hiding costs warmth |

Per run: 4 × 5 × 4 × 2 = 160 conditions per scene. **Three scenes = 480 (the user's figure); with the food scene, 640.** A thermal-off run (levels 02–04) drops temperature and settings: 4 × 5 × 4 scenes = 80.

**Food scene (new, minimal; `experiment-designer` owns and must confirm the content).** A copy of the no-animal scene with one food item added:
- agent at [5,5], bush at [5,2] (three cells left), unchanged;
- **one food item at [5,8]**, three cells right, the mirror of the bush, so reaching food and reaching cover cost the same number of steps;
- `count_low: 1`, `count_high: 1`, `spawn_area: [[5,8],[5,8]]`, food properties and visuals as `default.yaml`'s `food` entry;
- `max_consumption` and `regeneration_delay` are **left to `experiment-designer`**: the question is whether one visit should be able to restore a starving agent within the 100-step window. The plan does not guess;
- no animals, so the scene is deterministic (n = 1 per checkpoint).

File: `configs/environment/experiment/behavior_probes/core/avoidance/avoid_food_inj00.yaml`, written by `experiment-designer`, not by this plan's implementer. Its header follows the core-scene convention. In the `fire_away` setting the food cell's survivability is whatever the fire field gives; `experiment-designer` should say whether food in a lethally cold spot is intended.

**Training-range caveat (Revision 1, M3, still in force).** The second-wave level-05 runs used as the worked example predate the random start temperature: they always started at 0°. Their −10, −5, +5 cells are off-distribution. The manifest records each run's own training start ranges and flags off-range cells; those cells are a pipeline check only for those runs.

**D2. The recipe file and how one condition is assembled.**

The recipe (one small committed file per study; example `configs/eval_sweeps/body_state_grid/grids/lvl05_wave2.yaml`):

```yaml
# Body-state grid recipe. Conditions are assembled in memory per run by
# scripts/eval/body_state_grid.py; no per-condition config file exists.
name: lvl05_wave2
axes:
  injury:    [0, 30, 60, 90]
  nutrition: [20, 60, 100, 140, 180]
  body_temp: [-10, -5, 0, 5]        # applied only to thermal-on runs
settings: [neutral, fire_away]       # thermal generator ARMS keys; thermal-on runs only
scenes:
  - {name: none,         file: configs/environment/experiment/behavior_probes/core/avoidance/avoid_none_inj00.yaml}
  - {name: pred,         file: configs/environment/experiment/behavior_probes/core/avoidance/avoid_pred_inj00.yaml}
  - {name: rabbitwander, file: configs/environment/experiment/behavior_probes/core/avoidance/avoid_rabbitwander_inj00.yaml}
  - {name: food,         file: configs/environment/experiment/behavior_probes/core/avoidance/avoid_food_inj00.yaml}
```

Every key is mandatory; an unknown key is an error. Each scene file must resolve under `configs/` (the builder refuses otherwise) and must declare `environment.obstacles`. Condition ids are `avoid_<scene>_<setting>_inj030_nut060_tm05` (thermal on; `tm05`/`tp05` = −5°/+5°) or `avoid_<scene>_inj030_nut060` (thermal off). The id is a label only; nothing parses it.

Assembly of one condition, in `build_condition(recipe, run_dir, cond)`:
1. **Run side, once per run.** Read `<run>/models/config.yaml`; refuse if it contains `extends:`, is a Dreamer run, or has per-stage `stage_*.yaml` files (continual runs; out of scope). Deep-copy, apply `apply_saved_config_compat(copy, source=<that path>)` (the same call `eval_rollout.py` makes for a saved config), and keep the returned list of supplied keys. Compute `run_params = load_env_params(Config(copy))`. This is the only compat call anywhere in this design.
2. **Scene side.** `scene = load_env_config(scene_file).to_dict()`. The scene file is under `configs/`, so this is the strict path. If the run has thermal on, call the thermal generator's `build(scene_file, setting, 'clean', None)` (imported by file spec, not copied) and take exactly two things from its output: `environment.obstacles` (the scene's own list plus the campfire, if the setting has one) and `thermal.default_temp` (only if the setting sets one). If thermal is off, skip `build()`; `settings` are ignored for that run.
3. **Replace, never merge.** `cond = deepcopy(scene)`; then `cond['body'] = deepcopy(run['body'])`, and likewise `sensory`, `perceptual_noise` and `thermal`. Then set `cond['environment']['obstacles']` from step 2, and `cond['thermal']['default_temp']` from the setting when it sets one (otherwise the run's own ambient stays, the cold the agent trained in; the survivability check (d) confirms the setting still means what it says). `environment:`, `behavior_measures:` and `visualization:` stay the scene's.
4. **Pin the start.** `body.random_start_nutrition: false`, `body.start_nutrition: N`, `body.random_start_injury: true`, `body.start_injury_low/high: I`; when thermal is on, `thermal.random_start_body_temp: true` and `thermal.start_body_temp_low/high: T`. All written explicitly.
5. **Load strictly.** `params = load_env_params(Config(cond))`. No compat call. A missing key raises here.
6. **Rule check (b)** against `run_params`, then return `(Config(cond), params, record)`, where `record` is the manifest entry of §D4.

The builder also refuses values outside `[0, max_nutrition]`, `[0, max_injury]`, `[min_temperature, max_temperature]`, read from `run_params`.

**D3. The checks, and where each one runs.** The same four checks as Revision 1. What changed is that each now runs where the condition is actually used.

| Check | What it asserts | Pre-launch (`body_state_grid.py check`) | At evaluation time (inside `eval_rollout.py`) |
|---|---|---|---|
| (a) exact start | every episode's reset state has `injury_level == I`, `nutrition == N`, `body_temp == T` exactly; satiation equals the value derived from N | on a `PRNGKey(0)` reset of `ParallelEnv(params)`, 4 episodes | on the **rollout's own** `states0_np`, all episodes (`_run_episodes_batched`, after `:443`) |
| (b) rules | `params` equals `run_params` on every field except two named, printed lists: **scene fields** (loaded from `environment:`, `behavior_measures:`, `visualization:`; the developer builds this list by reading `load_env_params`, each entry naming its YAML section) and **start fields** (the five start keys, the three B1 fields, and the field loaded from `thermal.default_temp`). The field loaded from `thermal.enabled` is never exempt | yes | yes, per condition, in `build_condition` |
| (c) obs width | the condition's observation width equals the run's | yes | yes (a width mismatch would also break the model; checked explicitly first for a clear message) |
| (d) setting contract | for thermal settings, the thermal generator's `verify(None, setting, m)` passes (survivable-cell count, bush survivable or not, hiding bush blocks animals, full-arena view) | yes | yes, from `states0_np.thermal_field[0]` |

(d) needs one refactor in the thermal generator: `measure(path)` loads a file. Split it into `measure_params(p, state, obs)`, which does the arithmetic, and `measure(path)`, a thin wrapper that loads and resets then calls it. `verify` already uses only `arm` and `m`, so it is called with `path=None`. The generator's own output must not change (CP1(c)).

**Any failure raises.** At evaluation time the process exits non-zero, which the worker records as `FAIL`, which the driver now reads (change 3). One failed condition fails its whole checkpoint group, loudly.

**D4. What is recorded instead of the files (the manifest).** `body_state_grid.py check` writes `<output_dir>/<run_label>/manifest.json`, one per run. It holds:
- **Inputs**: recipe path and sha256; run dir and sha256 of its `models/config.yaml`; the compat keys supplied to the run (list, empty for current runs); sha256 of each scene file; the thermal generator file's sha256; git commit.
- **World fingerprint**: sha256 of the canonical JSON (sorted keys) of the run's four copied rule sections after compat. Two runs with the same fingerprint were tested in the same world; the reducer warns when a comparison mixes fingerprints (replaces Revision 1's cross-run folder check).
- **Per condition**: id, scene name, setting, I, N, T; **`config_sha256`**, the sha256 of the canonical JSON of the assembled condition dict; observation width; the rule-check report (fields that differed and which named list allowed each); `in_training_range: {injury, nutrition, body_temp}` from the run's own start ranges; `deterministic: true` for animal-free scenes.
- **Run's training start ranges** per axis (M3).

At evaluation time `eval_rollout.py` writes a small `condition.json` into each condition's output folder (the same folder as its `.rec.gz` files) with the id, the `config_sha256` it actually built, the checks passed, and its git commit. The reducer requires every sidecar's `config_sha256` to equal the manifest's. That ties each recording to the exact condition, with no file on disk.

To see or reproduce one condition as YAML (for a reviewer, or for debugging): `body_state_grid.py dump --recipe … --run … --cond <id>` prints the assembled dict. It writes nothing unless `--out` is given, and `--out` refuses any path under `configs/`, so no generated file can ever be mistaken for a maintained config.

**D5. Output-folder rule (replaces Revision 1's "assert absent").** `check` refuses to write into `<output_dir>/<run_label>/` when a manifest is already there **and differs** in recipe sha, run-config sha or condition list. An identical manifest is allowed, so an interrupted sweep can be resumed safely: the recordings were made from the same conditions. The driver repeats this comparison before launching (change 3), so stale recordings cannot be mixed in.

### File Changes

No config-schema change (no new environment key), so `CONFIG_GUIDE.md` and `02_config_schema.md` need no update. No critical-registry setting changes, so `CONFIG_CRITICAL_SETTINGS.md` needs no entry. No `src/` change: the in-memory path uses `load_env_config` (on the scene file), `load_env_params` and `apply_saved_config_compat` as they are.

#### 1. NEW `scripts/eval/body_state_grid.py` (library + CLI)

One level under `scripts/`; repo root is `parents[2]` (the depth hazard in `SCRIPTS_DEPENDENCY_MAP.md`). Imported by `eval_rollout.py`, `run_sweep.py`, the reducer and the tests; keep import-time side effects to none (no JAX work at import).

Library functions:
- `load_recipe(path) -> dict`: strict parse; all keys mandatory; unknown keys error; scene files must exist under `configs/`; no `,`, `;`, `|`, tab or `#` in the recipe path (they are worklist / config-list delimiters, change 3).
- `load_run_side(run_dir) -> RunSide`: step 1 of §D2 (with refusals).
- `enumerate_conditions(recipe, run_side) -> list[CondSpec]`: the product of §D1, thermal-aware.
- `build_condition(recipe, run_side, cond) -> (Config, EnvParams, record)`: steps 2–6 of §D2 plus checks (b) and (c).
- `check_start_state(states0_np, cond)` and `check_setting(params, thermal_field, cond)`: checks (a) and (d) on a given state.
- `condition_ref(recipe_path, cond_id) -> str` and `parse_condition_ref(s)`: the string `bodygrid:<recipe repo-relative path>#<cond_id>`.

CLI subcommands (every value from the recipe or the command; no defaults):

```text
check --recipe <recipe.yaml> --run <run dir> --output-dir <sweep output_dir> --label <run label>
      builds every condition, runs (a)-(d) with its own reset, writes <output_dir>/<label>/manifest.json (§D4, §D5)
list  --recipe <recipe.yaml> --run <run dir>         print condition ids and counts; writes nothing
dump  --recipe <recipe.yaml> --run <run dir> --cond <id> [--out <path outside configs/>]
```

#### 2. `configs/environment/experiment/behavior_probes/thermal/generate_thermal_probes.py`

Split `measure(path)` (`:242-255`) into `measure_params(p, state, obs)` plus the existing `measure(path)` as a wrapper. No behaviour change. Its existing `--check-only` must pass unchanged (CP1(c)).

#### 3. `scripts/eval/dwell_sweep/run_sweep.py`: accept a recipe

- New spec key `grid:` (recipe path). **Mutually exclusive with `probe:` and `conditions:`**; either both of those or `grid:`, else error. `grid:` requires `algo: rppo`.
- In grid mode, `build_groups` (`:168-235`) calls `load_run_side` + `enumerate_conditions` **per run** (a thermal-off run gets 80 conditions, a thermal-on run 480 or 640) and sets each condition's `cfg_path` to `condition_ref(...)` instead of a file path. The file-existence check (`:206-208`) is skipped only in grid mode. `out_csv` and the scratch layout are unchanged.
- Before writing worklists, for every run: require `<output_dir>/<label>/manifest.json` and require its recipe sha, run-config sha and condition list to equal what the driver just computed. Mismatch or absence → exit non-zero naming the `check` command to run (§Pre-launch).
- **Failure markers.** Before launch, clear `_run_markers/fail_<node>` alongside `done_<node>` (`:475-477`). After `poll_done`, if any `fail_*` file is non-empty, print its lines and exit non-zero **before** aggregating. Applied in grid mode; in file mode print the lines as a warning only, so existing sweeps' exit behaviour does not change in this plan (the general fix goes to `bug-curator`, §Hand-offs).
- `plot_measures` must be `[]` in grid mode (a per-condition history figure with 480+ rows of one point is useless); error otherwise.

`sweep_worker.sh` needs **no change**: the reference string passes through its `CFG,OUT` pairs and `--config-list` file unchanged, because the recipe path is checked for delimiter characters.

#### 4. `scripts/eval/eval_rollout.py`

**(a) Recipe conditions in `_resolve_entry` (`:955-975`).** If `config_arg` starts with `bodygrid:`:
- require `--batched` (error otherwise) and an rPPO checkpoint;
- derive the run dir from `--checkpoint` (`<run>/models/<step>` → `<run>`). The rules therefore always come from the run being evaluated; there is no way to pass another run;
- skip `_resolve_continual_stage_config` and the whole compat branch (`:962-971`); call `load_run_side` once per process (cache it) and `build_condition` per entry;
- use the returned `Config` for `load_behavior_measure_cfg` exactly as the file path does;
- remember `cond` on the entry for the checks below.
A plain path behaves byte-identically to today.

**(b) Checks (a) and (d) on the real state.** In `_run_episodes_batched`, accept an optional `on_reset` callback; call it with `states0_np` right after `:443`. For recipe entries, `main` passes a callback that runs `check_start_state` and `check_setting`. For file entries none is passed.

**(c) Sidecar.** After a recipe entry's recordings are written, write `condition.json` (§D4) into that entry's output root.

**(d) Body temperature in batched recordings** (unchanged from Revision 1):

```python
# scan_fn step_out — ADD next to snap_injury_level:
"snap_body_temp": next_state.body_temp,

# init_state / step_state SimpleNamespace — ADD:
body_temp=states0_np.body_temp[i]            # init
body_temp=scan_out["snap_body_temp"][t, i]   # per step
```

Do **not** add `thermal_field` to recordings. The 11 measures and all existing snapshot fields stay byte-identical (CP1).

#### 5. NEW `scripts/analysis/body_state_grid_steps.py`

One level deep, `parents[2]`, run-agnostic. `--eval-dir <sweep output_dir> --label <run label> --out <file>.npz/.json`. It reads `<eval-dir>/<label>/manifest.json` (exit non-zero if missing), walks every manifest condition, and **requires** each to have its `condition.json` with a matching `config_sha256` and the expected number of recordings. A missing or mismatched condition is an error, not a gap. Per condition it computes survival steps (mean, median, per-episode list), termination-reason counts, time courses of in-bush and resting share over alive episodes with denominators, mean injury / nutrition / body temperature over time (exit non-zero if a thermal condition lacks `body_temp`), share of steps 1–25 in the bush, and **for the food scene, the step of first eating and the step of first entering the bush** (the "eat or hide first" read). It copies `deterministic` and `in_training_range` onto each cell and prints the off-range count. With several `--label`s it warns when their world fingerprints differ. **Survival steps are the performance measure; reward is not read.**

#### 6. NEW recipe `configs/eval_sweeps/body_state_grid/grids/lvl05_wave2.yaml` and sweep spec `configs/eval_sweeps/body_state_grid/bodygrid_lvl05_wave2_rppo.yaml`

The recipe is §D2's example. The worked-example sweep spec, for the two second-wave level-05 runs (control and modulated agents, seed 42):

```yaml
name: bodygrid_lvl05_wave2
algo: rppo
output_dir: results/eval/avoidance/metrics_history_rppo_bodygrid_lvl05_wave2
grid: configs/eval_sweeps/body_state_grid/grids/lvl05_wave2.yaml
episodes: 30
max_checkpoints: 1
plot_measures: []
nodes: []          # filled at launch from live GPU/diary state
runs:
  - {label: lvl05_control,   path: results/JAX_RecurrentPPO/20260922-182534_rppo_bq2cover_lvl05_t1none_s42}
  - {label: lvl05_modulated, path: results/JAX_RecurrentPPO/20260922-182538_rppo_bq2cover_lvl05_t16quad_s42}
```

Header comment: the `check` commands to run first; that these runs never trained with a random start temperature, so their off-0° cells are a smoke test only. If the food scene is not yet written by `experiment-designer`, the developer drops its line from this recipe for the smoke test and says so in the Implementation Report. The 16-world recipes and specs are `experiment-designer`'s.

#### 7. NEW `tests/scripts/test_body_state_grid.py`

Each test must fail on today's code. Fixture: a copy of a resolved level-05 run config (thermal on) in `tmp_path`, laid out as `<run>/models/config.yaml`, plus the fixture checkpoint pattern of `tests/scripts/test_eval_rollout_online_replay.py` where a policy is needed.

- `test_cell_pins_exact_start_state`: build three conditions (including T = −10 and N = 180), reset, assert (a) exactly.
- `test_run_rules_are_copied`: fixture sets `body.healing_nutrition_cost: 0.5` and `thermal.metabolic_coupling: true`; both reach the condition's `EnvParams`. A probe built the injury-grid way (extends `environment/default`) has 0.0 and false, documenting the gap.
- `test_missing_run_key_is_not_filled` (**new, the in-memory strictness proof**): delete a mandatory `body` key that compat does not supply (for example `body.metabolic_cost`) from the fixture run config. Assert `build_condition` raises `ValueError` from the loader, and that the key did **not** come back from `default.yaml`. Fails if any step merges instead of replacing.
- `test_compat_runs_once_on_run_only` (**new**): spy on `apply_saved_config_compat`; build all conditions; assert exactly one call, with `source` equal to the run's `models/config.yaml`, never with the assembled dict.
- `test_in_memory_equals_file`: `dump --out` three conditions to `tmp_path`, `load_env_params(load_env_config(file))`, assert every `EnvParams` field equals the in-memory one. Proves the in-memory path gives what a file would.
- `test_rule_check_catches_mismatch`: tamper the assembled dict's `body.metabolic_cost` through a test hook before the check; assert failure.
- `test_rule_check_catches_switch_turned_on`: turn on a parent switch that is off in the run (for example `body.healing_nutrition_dependence`) without its sub-keys; assert failure.
- `test_thermal_enabled_is_never_exempt`: condition from a thermal-on scene against a run side with `thermal.enabled: false` injected; assert failure.
- `test_eval_rollout_runs_recipe_ref`: run `eval_rollout.py --config-list` with one `bodygrid:` line, 2 episodes; assert recordings exist, `condition.json` has the manifest's `config_sha256`, and a plain-path line in the same list is unaffected.
- `test_eval_rollout_refuses_bad_start`: monkeypatch the pinned N after assembly so the reset disagrees with `cond.N`; assert non-zero exit.
- `test_sweep_driver_grid_mode`: `build_groups` on a spec with `grid:` gives the expected per-run counts (thermal-on and thermal-off fixtures), `cfg_path` values are `bodygrid:` refs; the driver refuses `grid:` together with `probe:`, refuses a missing or mismatched manifest, and exits non-zero when a `fail_<node>` marker has content.
- `test_batched_recording_has_body_temp`: as Revision 1: every snapshot has `body_temp`, equal to the unbatched path's value for the same seed.

#### 8. `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` (same change; Maintenance Contract)

- Add `scripts/eval/body_state_grid.py`: `parents[2]`; imports `configs/…/thermal/generate_thermal_probes.py` by file spec and `src.environment.saved_config_compat`; **callers**: `scripts/eval/eval_rollout.py`, `scripts/eval/dwell_sweep/run_sweep.py` (note its own repo-root depth and how it imports the module), `scripts/analysis/body_state_grid_steps.py`, `tests/scripts/test_body_state_grid.py`.
- Add `scripts/analysis/body_state_grid_steps.py` (`parents[2]`; reads manifest + sidecars).
- `eval_rollout.py` entry: accepts `bodygrid:` references in `--config-list`; batched recordings carry `body_temp`; writes `condition.json` for recipe entries.
- `run_sweep.py` entry: `grid:` spec mode; reads `fail_*` markers.
- `generate_thermal_probes.py` entry: new caller (`body_state_grid.py`), new `measure_params`.
- Add the new test file as a caller of all of the above.

#### 9. `scripts/eval/dwell_sweep/README.md`

One paragraph: grid mode (`grid:` instead of `probe:` / `conditions:`), the `check` step before launch, `max_checkpoints: 1`, `plot_measures: []`, and that failures now stop a grid sweep.

**Removed from Revision 1**: `make_body_state_grid.py`, the `generated/` folder, and the `.gitignore` change. None of them is created.

### Cost

| Item | Count |
|---|---|
| Conditions per run, thermal world | 480 (three scenes) or **640** (with the food scene) |
| Episodes per run (30 per condition, newest checkpoint only) | 14,400, or **19,200** with food |
| Conditions per run, thermal-off world | 60, or **80** with food |
| 16-world experiment, per seed (32 runs) | 460,800 episodes, or **614,400** with food |
| Existing injury grid, one arm, one run, for comparison | 45,000 episodes |
| Config files written | **0** (Revision 1: 7,680 for 16 worlds) |
| Committed files per study | 1 recipe (plus sweep specs) |

**Compiles.** The start-temperature fields are static, and each scene has its own shapes, so each (temperature × scene × setting) is a separate compile of the batched rollout: 4 × 4 × 2 = **32 per run** with food (24 without), against about 6 for the injury grid. Expect compile time to be a visible share; CP5 measures it.

**Build and check overhead (new).** At evaluation time each condition costs one `load_env_params` plus one field-by-field comparison; the run side is loaded once per process. `check` additionally resets the environment once per condition. Neither is measured yet; CP2 records `check`'s wall time per run and CP5 records the in-process overhead. If `check` exceeds a few minutes per run, the fallback is to parallelise it across runs, not to skip it.

**Disk.** About 10 KB per recording (measured by plan-reviewer): about 145 MB per run without food, about 190 MB with it; about 6.1 GB for one seed of the 16-world experiment with food. Manifests are a few hundred KB each. CP5 confirms.

**Wall time** is not estimated; CP5 measures it on the real driver.

---

## Checkpoints

- [ ] **CP1: the recorder change and the thermal-generator split break nothing.**
  - **(a) Measures.** Before and after change 4(d), run `scripts/eval/parity_check_eval_rollout.py` on one level-04 and one level-05 checkpoint plus one probe config. All 11 measures identical.
  - **(b) Recordings.** On one thermal probe and one level-05 checkpoint, `eval_rollout.py --batched --record --seed 0` on the commit without change 4 and with it. Every payload key and array `np.array_equal`, except `snapshots[*]['body_temp']`, present after and absent before. Paste the compared-key list.
  - **(c) Thermal generator.** `generate_thermal_probes.py --check-only` passes, and regenerating its battery to a scratch directory gives byte-identical files before and after change 2.
  - **(d) File path unchanged.** A plain-path `--config-list` run gives byte-identical recordings before and after change 4(a)–(c).
- [ ] **CP2: `check` on the worked example.** Run `check` for the modulated run: every condition passes (a)–(d). Paste the scene-field and start-field lists and one rule-check report. Confirm `in_training_range` marks T = −10, −5, +5 off-range for this run. Run it for the control run: same world fingerprint. Run `list` on a level-04 run: 80 (or 60) conditions, observation width 52. Record `check` wall time per run.
- [ ] **CP3: the tests fail first.** `tests/scripts/test_body_state_grid.py` fails on a checkout without changes 1–4, then passes with them. `test_missing_run_key_is_not_filled` and `test_compat_runs_once_on_run_only` must be among the tests shown failing before.
- [ ] **CP4: byte-exact anchor against the injury grid, both made with today's code** (Revision 1, M1/M2, unchanged in substance). Re-run the injury-grid `fire_away` clean spec at HEAD for the modulated level-05 run, `--max-checkpoints 1`, conditions `avoid_{none,pred,rabbitwander}_inj{00,30,60,90}`, into a fresh folder (asserted absent). Compare with the grid's `fire_away × inj{00,30,60,90} × nut100 × 0°` cells of the three original scenes: CSV rows identical, per-step actions and positions `np.array_equal` for all 30 episodes. This also proves the in-memory path reproduces the file path on real runs. Pre-registered tolerance: if the only reset-state difference is ≤ 1 ulp in `animal_property_sampled` (Known Bugs row 153), record it and pass on the 11 measures; anything else fails. Diffing the fresh reference against the 2026-09-24 recordings is optional and reported separately. If the reference cannot be produced, CP4 fails.
- [ ] **CP5: smoke run through the real driver.** Run the worked-example spec (change 6) on both runs, on nodes chosen from live GPU and diary state. Record wall time, CPU-minutes, compile share and disk under `_scratch/`. Then run the reducer on both. Check:
  - every condition has a `condition.json` whose `config_sha256` matches the manifest;
  - in the `neutral` setting a cell's `body_temp[0]` equals its T;
  - N = 20 cells of the no-food scenes end at or before step ~20 with termination reason starvation;
  - the animal-free scenes are flagged deterministic;
  - the T = −10, −5, +5 cells are reported off-range for both runs (**a pipeline check, not a finding; never quoted**);
  - if the food scene is included: at reset exactly one active food item at [5,8].
- [ ] **CP6: a runtime check failure stops the sweep.** Copy the control run to a scratch run dir, change one rule in its `models/config.yaml` after `check` has written its manifest, and run the driver on it: it must refuse before launch (manifest mismatch). Then bypass the driver's manifest check with a test flag or a hand-built worklist and confirm the worker's `FAIL` line makes `run_sweep.py` exit non-zero before aggregating. Delete the scratch run afterwards.

## Pre-launch steps (every grid sweep)

These replace Revision 1's list. Each fails loudly; none may be skipped.

1. **`check`** for **every** run in the spec: `body_state_grid.py check --recipe <recipe> --run <run> --output-dir <output_dir> --label <label>`. This writes each run's manifest (§D4) and enforces the output-folder rule (§D5).
2. **Pre-flight** (`env-config-reviewer`) on the first real sweep of each world: `dump` two or three conditions per setting to a scratch path outside `configs/` and review those, plus the recipe and the manifest's rule-check report.
3. **Launch** `run_sweep.py`. It re-verifies every manifest before writing worklists (change 3).

## Decisions (user)

**Decided, 2026-09-26:**
- **Q1, grid size: 480 per run** (4 injury × 5 fullness × 4 start temperatures × scenes × 2 temperature settings). Kept.
- **Q2, food scene: yes.** Added in §D1: one food item mirrored opposite the bush. `experiment-designer` confirms the content.
- **Q3, where the conditions live: nowhere on disk.** The user: "480 conditions per run is quite large to be config files. Just make the combinations not the real configs yet." Replaced by the recipe + in-memory build (§D2–§D5).
- **Q4, which checkpoint: the newest one only.** `max_checkpoints: 1`.

**Still open, need the user:**
- **Q5: does the food scene count inside the 480, or on top of it?** 480 was three scenes × 160. Adding the food scene as a fourth gives **640 per run** (19,200 episodes; about 614,000 for one seed of the 16-world experiment). Keeping exactly 480 would mean dropping a scene (the no-animal one is the natural candidate, since the food scene also has no animals, but it is also the injury grid's baseline). The plan assumes 640 until told otherwise.
- **Q6: where the recipe files live.** The plan puts them next to the sweep specs, `configs/eval_sweeps/body_state_grid/grids/`. The alternative is next to the scenes under `configs/environment/experiment/behavior_probes/`. Either works; this is only about where people will look.

## Hand-offs

- `experiment-designer`: write and confirm the food scene (`avoid_food_inj00.yaml`, including `max_consumption`, `regeneration_delay`, and whether food in a lethally cold spot under `fire_away` is intended); the 16-world recipes and sweep specs in `docs/experiments/active/level05_body_interactions/`.
- `bug-curator`: record (1) "batched evaluation recordings omit `body_temp` and `thermal_field`" (change 4 fixes `body_temp`; `thermal_field` stays open, render-only); (2) "`run_sweep.py` never reads the worker's `fail_*` markers and the worker discards stderr, so failed evaluations vanish silently" (change 3 fixes it for grid sweeps only).
- `plan-reviewer`: review Revision 2 before approval (the condition-assembly design is new).
- `env-config-reviewer`: pre-flight step 2.

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

> **Reviewed by**: plan-reviewer · **Date**: 2026-09-26 · **Object**: this plan at commit `bf71048c`
> **Verdict**: **SOUND WITH CONCERNS** — no Critical finding; six Moderate items worth fixing before implementation, four open assumptions.
>
> Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run · 🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

### What I checked against the code (all confirmed)

- **The three pins really pin.** `jax.random.uniform(key, (), minval=x, maxval=x)` returns `x` exactly in float32 — run in the project env for −10, 0, 5, 30, 60, 180, 0.3, 7.1. `body_key1` is split unconditionally (`src/environment/core.py:1898`) and read only by B1; `random_start_nutrition: false` reads `start_nutrition` directly (`:1906`); reset stores `body_temp` as a float32 scalar on every config (`:2200`), so the batched recorder's `states0_np.body_temp[i]` (`scripts/eval/eval_rollout.py:443` is a `tree_map`) will exist. `test_B1_2_pinned_start_is_exact` exists (`tests/env/test_body_mechanics_units.py:180`).
- **Sweep-driver claims** (`run_sweep.py:131-152, 212-213, 384, 401`): `probe:` accepts any dir, `conditions: all` globs `avoid_*`, `max_checkpoints` caps to newest-N, `plot_measures: []` draws nothing, `x_axis` is optional.
- **Compat gate**: `_is_under_configs` (`eval_rollout.py:804-808`) and the compat call only outside `configs/` (`:962-971`) — the "keep generated files under `configs/`" reasoning in §D4 is correct.
- **§A2's measurement reproduced**: flattened diff of the wave-2 modulated run (after compat) vs `injury_grid/fire_away_clean/avoid_pred_inj30.yaml` differs only on `random_start_nutrition`, `start_injury_low/high`, and keys absent from the run (B3/B4/B5 sub-keys, B1 range keys). Control vs modulated runs have **identical** env sections (only `agent.modulation.*` differs), so §D5's one-folder-per-world premise holds for wave 2.
- **Known Bugs**: `start_satiation` dead knob (row 94, plan already handles), glued rabbit (row 99, excluded), reset 1-ulp across lowerings (row 153, see M2), termination reason unreliable with a body system off (row 473 — only bites nutrition-off worlds, not these). No earlier plan on a joint body-state grid; [[STATE_DEPENDENT_BODY_MECHANICS]] is the right citation.
- **Maintenance contracts**: no new mandatory key, no registry setting changed, `SCRIPTS_DEPENDENCY_MAP.md` update is in the change list, `parents[2]` is right for both new scripts.

### Findings

| Sev | Location | Issue | Suggested fix | Owner |
|---|---|---|---|---|
| 🟡 M1 | §CP4 | **The anchor is not produced by the same code as the new recordings.** The existing `injurygrid_fire_away_clean` recordings for checkpoint 10000011 are dated **2026-09-24 13:01**; the four `src/environment` commits of 2026-09-26 (C0 `eef30212`, C2 `11b9a1b7`, `c073ce99`, `7b77d13d`) and change 2 all post-date them. If CP4 fails there are three candidate causes (C2 src change, recorder change, probe/rule change) and "FAILS; does not skip" gives no diagnosis path. | Regenerate the four anchor conditions at HEAD into a fresh output dir with `--max-checkpoints 1` (~2 min) and use *that* as the CP4 reference. Optionally diff the fresh anchor against the 09-24 one as a separate, separately-attributable check that C2 is inert on this run. | `senior-developer` (plan), `developer` |
| 🟡 M2 | §CP4 | `np.array_equal` on positions/actions is stricter than the reset code guarantees across a re-lowering: Known Bugs row 153 (documented, not a bug) — a 1-ulp difference on `animal_property_sampled` when the trace changes. Flipping `thermal.random_start_body_temp` (a **static** field, `src/environment/state.py:456`) changes `jax_reset`'s trace. | Pre-register the fallback: on mismatch, first diff both probes' reset states; if the only difference is ≤ 1 ulp on `animal_property_sampled`, record it and pass CP4 on the measures; anything else fails. | `senior-developer` |
| 🟡 M3 | §D1, §Context | "All values are inside level 05's training ranges (body temperature −10 to +5)" is **false for the worked-example runs**: the wave-2 level-05 runs predate B1 (their saved config has no `random_start_body_temp`; compat supplies `false`; the critical-settings change log of 2026-09-26 says "Wave 2 level-05 and level-06 runs started every episode at 0.0"). T = −10 / −5 / +5 are off-distribution starts for them. Fine for a smoke test, wrong if CP5's readout is ever quoted as a result. | Say so in §D1 and §CP5. Have the manifest record the run's own start ranges per axis (read from the run config) so the reducer flags off-range cells. | `senior-developer` |
| 🟡 M4 | §D3 (b) | The rule-diff exemption is broader than stated: "keys missing from the run config do not fail" is applied without checking that the parent switch is off, and the check is a YAML re-derivation rather than what the env reads. Today the missing keys are exactly the B3/B4/B5 sub-keys and B1 range keys, so it passes for the right reason — but a future world that turns a parent on in the probe would slip through. | Prefer comparing resolved `EnvParams` scalar/static fields between `load_env_params(probe)` and `load_env_params(run + compat)`, excluding scene-derived arrays and the allowlisted start fields — that is the ground truth. If the YAML diff stays, permit a missing key only when its parent switch *in the probe* is off, with B1's range keys the sole named exception. | `senior-developer` |
| 🟡 M5 | §D4, change 3 | `manifest.json` (the provenance record) is gitignored with the generated files, and the reducer reads it from the generated dir. Regenerating a world folder with different levels silently pairs an older sweep output with the wrong manifest. | Copy `manifest.json` into the sweep `output_dir` at launch and have the reducer read it from there; un-ignore `manifest.json` with a negation pattern (or commit copies under the experiment folder). | `senior-developer` |
| 🟡 M6 | §CP1 | `parity_check_eval_rollout.py` compares only the 11 measures per episode (legacy vs batched); it never opens snapshot fields, so "every existing snapshot field byte-identical" is not something CP1 as written can establish. | Add an explicit recording diff: batched run on one probe before and after change 2 (same seed, same commit otherwise); load both `.rec.gz`; assert every payload key/array equal except `snapshots[*]['body_temp']`. Test 4 covers batched-vs-unbatched, not batched-before-vs-after. | `developer` |
| 🟢 L1 | change 4, §D2 step 1 | `output_dir` "fresh; must not exist" is not enforced by `run_sweep.py` (incremental by design). §D2 step 1 says `build()` is always applied, but `--arms` is refused for thermal-off runs. | Assert the dir is absent in the launch step (or the spec header). State that `build()` is skipped when thermal is off. | `developer` |
| 🟢 L2 | §Cost | `thermal_start_body_temp_low/high` are static (`state.py:457-458`), so each T value is a separate compile of the batched rollout: ~4 T × 3 scenes × 2 arms = 24 compiles per run vs 6 for the injury grid; the 36 s / 12-condition figure came from a battery that shared traces, so linear scaling underestimates. Disk: existing injury-grid `.rec.gz` files are ~10 KB each (measured), so ~145 MB per run, ~4.6 GB for 32 runs. | Nothing to change — CP5 measures — just do not be surprised by the compile overhead. | — |

### Open assumptions (❓)

- **O1 — thermal runway in `fire_away`.** From T = −10 the body reaches the −15 floor within a fraction of the 100-step window unless the agent reaches the fire (bush equilibrium −20.24). In that arm the T axis is partly a survival-runway axis, like N in §A3. The reducer's termination-reason counts will show it; §A3 should say it.
- **O2 — rPPO-only saved config.** The generator assumes `<run>/models/config.yaml` with resolved env sections and no `extends:`. Verified for wave 2; not verified for Dreamer runs (the sweep supports `algo: dreamer`, whose probe eval layers train/eval/visualization defaults under the probe). Scope the generator to rPPO or verify one Dreamer run.
- **O3 — env identical across a world's agent arms** (the §D5 premise). True for wave 2; for the 16-world experiment it depends on `experiment-designer` keeping env sections identical across agent arms. `--check-only` catches a mismatch only if it is run per run before launch — make that a listed pre-launch step, not an optional one.
- **O4 — `thermal.enabled` in the diff.** The "except `enabled`" copy exemption must not become a diff allowlist entry, or `--check-only` against a level-04 run (CP2) would not fail as required.

### Cost of being wrong

If M1/M2 bite, CP4 fails on a phantom and the developer loses a day untangling three causes. If M4 bites during the 16-world sweep, a probe silently drops a body rule and 32 runs × 14,400 episodes (~10–16 CPU-hours) measure a different world than the agents trained in — a wrong conclusion about state-combination behaviour, which is the paper's claim. No data-loss hazard anywhere in this plan.

*Reviewed by: plan-reviewer*

## User decision 2026-09-26 (recorded by the parent session)

- **Q5 (scene count):** all four scenes are documented in the combination recipe — no animal, predator, wandering rabbit, and the food scene — giving 640 conditions per run. User: "Just document them to remember not generate any config files." The recipe records the combinations; **no per-condition config files are generated**, now or at run time (conditions are built in memory, as Revision 2 specifies).
- **Q6 (recipe location):** next to the sweep specs, as the plan proposes.
