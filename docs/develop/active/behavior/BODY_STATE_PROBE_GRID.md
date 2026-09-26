---
title: "Behaviour probes that set injury, fullness and body temperature together (body-state grid)"
topic: behavior
status: active
created: 2026-09-26
last_updated: 2026-09-26
---

# Behaviour probes that set injury, fullness and body temperature together (body-state grid)

> **Status**: PLANNED. Waiting on the user decisions in §Decisions, then `plan-reviewer`, then approval.
> **Opened**: 2026-09-26
> **Related**: [[STATE_DEPENDENT_BODY_MECHANICS]] (the level-05 body rules that motivate this) · [[INJURY_DEPENDENCE_PLAN]] (the injury-only probe battery this extends) · [[SAVED_RUN_CONFIG_COMPAT]] (how old runs' saved settings are re-opened) · [[EXPERIMENT_EVAL_DURING_TRAINING]] · `docs/experiments/active/level05_body_interactions/` (the upcoming 16-world experiment, being designed by `experiment-designer`; folder does not exist yet)

---

## Context

**What a behaviour probe is.** A behaviour probe is a small, fixed test scene. The trained agent is dropped into it and we record what it does. A typical scene has a 10×10 field, one bush to hide in, and sometimes a predator or a wandering rabbit. Every run is tested on the same scenes, so the runs can be compared.

**What exists today.** The current "injury grid" probes vary one thing: how injured the agent is at the start (0, 10, …, 90). The agent always starts at its comfortable food level, and its body temperature always starts at the comfortable value.

**Why that is no longer enough.** Level 05 now has body rules that link the internal states together (see [[STATE_DEPENDENT_BODY_MECHANICS]]):
- healing can slow down when the agent is hungry;
- healing can cost food;
- staying warm can cost food;
- each episode starts at a random body temperature.

An upcoming experiment will train agents in 16 variants of that world. It asks whether the neuromodulated agent's behaviour depends on **combinations** of body states. One example question: does an injured agent still go and hide when it is also starving and cold?

To answer that, a probe must set three things at once, and exactly: starting injury, starting fullness (food energy) and starting body temperature.

**What this plan builds.**
1. A generator that takes any trained run and writes a grid of probe scenes, one scene per combination of the three starting states.
2. A small fix so that the standard evaluation recordings save body temperature at every step. Today they drop it.
3. A tool that turns the recordings into per-combination summaries.

The generator copies the run's own body rules into the probes. Without that, an agent trained where healing costs food would be tested in a world where healing is free.

The work needs no change to the environment code (`src/`). It uses configs and scripts only, and it reuses the existing evaluation sweep. The default grid costs about 14,400 test episodes per run, at one checkpoint. For comparison, one arm of the existing injury grid costs 45,000 episodes per run.

---

## Analysis

### A0. Wiki pull gate and known bugs

- **`start_injury` is a dead setting** (LLM Wiki `config_system/20260622_1746_start_injury_dead_needs_random_range`). A plain `body.start_injury` is never read. Injury starts at 0 unless `random_start_injury: true`, and then it is drawn from `[start_injury_low, start_injury_high]`. To pin injury, use the random path with `low == high`. The existing injury grid already does this (`generate_injury_grid.py` `core_dict`).
- **`body.start_satiation` is also dead** (Known Bugs, OPEN, informational). Starting satiation is always derived from starting nutrition (`src/environment/core.py:1908-1909`). So "fullness" in this plan means **nutrition**. The generator must never write `start_satiation` as if it did something.
- **Probes must match the training regime** (wiki `behavior_measures/20260805_0118_regime_matched_probe_and_run_sweep_probe_dir`, `…/20260704_2012_noise_matched_frozen_probe`). A probe that drops a rule the agent trained under understates the agent. This is why §D2 copies the run's body rules.
- **Re-running into an old output folder mixes stale recordings** (wiki `…/20260704_2013_probe_rerun_stale_checkpoint_contamination`). Each sweep spec therefore gets a fresh `output_dir`.
- **Near-deterministic probes inflate significance** (wiki `…/20260704_2014_deterministic_probe_significance_inflates`). The no-animal scene has no randomness, so its 30 episodes are identical copies (see the note in `scene_steps.py`). The analysis tool must treat that scene's 30 episodes as **n = 1** per checkpoint.
- **Starting nutrition shortens the episode in a scene with no food** (wiki `hypervigilance/20260623_1623_nutrition_runway_confounds_hypervig_read`). The probe scenes contain no food (`resources: []`), so low-fullness cells starve partway through. See §A3 and §Decisions Q2.
- **Batched evaluation drops body temperature**: found while writing this plan, and **not in Known Bugs**. See §A4. `bug-curator` should record it (§Hand-offs).

### A1. How a probe fixes the starting state today (code as truth, `v4.0`, 2026-09-26)

Reset path, `src/environment/core.py:1897-1929`:

| State | How it is set at reset | How to pin it exactly |
|---|---|---|
| Nutrition (fullness) | `random_start_nutrition` true → uniform `[start_nutrition_low, start_nutrition_high]`; false → **`start_nutrition` is read directly** (`:1906`) | `random_start_nutrition: false`, `start_nutrition: N` |
| Satiation | Derived from nutrition (`:1908-1909`) | Not settable. It follows N. |
| Injury | `random_start_injury` true → uniform `[low, high]`; false → **0.0** (`:1917`) | `random_start_injury: true`, `start_injury_low == start_injury_high == I` |
| Body temperature | `thermal.random_start_body_temp` true → uniform `[thermal.start_body_temp_low, high]` from `body_key1`; false → the setpoint (`:1923-1929`) | `thermal.random_start_body_temp: true`, `start_body_temp_low == start_body_temp_high == T` |

**Pinning temperature.** `jax.random.uniform` with equal bounds returns exactly the lower bound. This is the verified B1 implementation (the `STATE_DEPENDENT_BODY_MECHANICS` T-B1-2 test). The loader accepts any `T` with `min_temperature <= T <= max_temperature`, which is −15 to +15 (`config_loader.py:1711-1720`). With the flag on it also prints B1's informational worst case. That printout is expected, not an error.

**The temperature draw does not shift other random streams.** `body_key1` is split whether or not B1 is on, and before B1 nothing read it (`core.py:1898`, comment at `:1919-1922`). So a probe with the flag on and `T` equal to the setpoint (0.0) starts in exactly the same state as today's probe with the flag off, and every other random draw is the same too. §CP4 uses this as a byte-exact anchor.

**How the existing generators build a probe.** `behavior_probes/injury_grid/generate_injury_grid.py` reads one of three core scenes (`core/avoidance/avoid_{none,pred,rabbitwander}_inj00.yaml`). It sets `start_injury_low/high`, then passes the result through the thermal generator's `build()` (`behavior_probes/thermal/generate_thermal_probes.py:219-240`) for four temperature "arms":

| Arm | Surroundings |
|---|---|
| `neutral` | air at 0° |
| `cool` | air at −7.5° |
| `fire_by_bush` | cold air, with a fire next to the bush |
| `fire_away` | cold air, with a fire far from the bush, so the bush is lethally cold |

It also writes two noise batteries (clean and noise-matched). Every probe **`extends: environment/default`**. The world's rules therefore come from `default.yaml`, not from the run that is being tested.

### A2. Why the probe must copy the run's body rules

`eval_rollout.py` builds the whole environment from the probe file (`_resolve_entry`, `scripts/eval/eval_rollout.py:955-975`). It does not read the run's saved config.

Measured on 2026-09-26: the settings of a level-05 run from the second wave (control and modulated agents on levels 02–06; the modulated run was used) were compared with its injury-grid probe, section by section (`body`, `thermal`, `sensory`, `perceptual_noise`). The only differences were starting-state keys, plus sub-keys that are unread because their parent switch is off. **Today the probe's rules and the run's rules agree, but only because both happen to equal `default.yaml`.**

The 16-world experiment changes that on purpose. Its worlds set `body.healing_nutrition_cost`, `body.healing_nutrition_dependence`, `thermal.metabolic_coupling`, B2 and B4 to non-default values. A probe that extends `environment/default` would switch all of those back off. §D2 copies the rule sections from the run instead, and asserts that nothing else differs.

### A3. The probe window and the fullness axis

Probe episodes last `max_steps: 100`. The scenes have no food. Nutrition runs 0–200, with 100 as the comfortable value, and drops by 1.0 per step, plus the B3 healing cost and the thermal metabolic cost when those are on.

- An agent that starts at N = 20 starves by about step 20. At N = 60 it starves by about step 60.
- That is a real outcome: survival steps are the project's performance measure. It also means behaviour after that step is simply missing.
- The analysis tool therefore reports survival steps and termination reason in every cell. Hiding and resting rates use **alive steps only**, the same convention `scene_steps.py` uses, and each is given with its denominator.

Whether to add a scene **with** food is a scene-design question (§Decisions Q2). The generator takes any list of source scenes, so a food scene can be added later without changing code.

### A4. Batched evaluation recordings drop body temperature (scripts-only fix)

The dwell sweep runs `eval_rollout.py --batched --record` (`sweep_worker.sh:74`). The batched recorder rebuilds each per-step state from `scan_out` as a `SimpleNamespace` with nine fields (`eval_rollout.py:482-512`). **`body_temp` and `thermal_field` are not among them**, and the scan (`:323-345`) never collects `next_state.body_temp`.

`_snapshot_state` (`src/utils/eval_recording.py:64-67`) writes `body_temp` only when the state object has one. So every sweep recording of a thermal world has **no body-temperature trace**. The unbatched path (`_run_episode_with_recording`) passes the real state and does record it. The body-temperature half of this study cannot be analysed without the fix.

The fix records `body_temp` only. `thermal_field` is also missing, and that costs the renderer its field panel on batched recordings. But it is a whole 10×10 array per step, and this study does not need it. It is recorded as a follow-up for `bug-curator`, not fixed here, to keep the change small.

### A5. The existing analysis scripts are not run-agnostic

`scripts/analysis/studies/injury_dependence/scene_steps.py` and `run_manipulations.py` hard-code the ten second-wave runs (`RUNS`), the scene list and the ten injury levels. Following the project rule that tools must work for any run, the reducer here is a new tool. It reads a **manifest** written by the generator, not a table of runs, and it does not parse condition names. `scripts/analysis/injury_dose_store.py` (training-world dose-response from trajectory stores) is a different reading and is unchanged.

### A6. Sweep-driver constraints that shape the design

From `scripts/eval/dwell_sweep/run_sweep.py`:
- `probe:` takes any repo-relative directory, and `conditions: all` globs `avoid_*.yaml` (`:131-152`). Every condition name must start with `avoid_`.
- Work is split **by checkpoint**. One checkpoint and all its pending conditions go to one `eval_rollout --config-list` process. At one checkpoint per run, that means one process per run evaluating every cell.
- `max_checkpoints: 1` in the spec (`:435`, `:212-213`) evaluates only the newest checkpoint.
- `plot_measures: []` renders no figures (`:401-411`). This is needed: `plot_summary.fig_for` draws one row per condition, and a 480-row history figure of one point each is useless.
- The worker always evaluates with `--seed 0` (`sweep_worker.sh:74`). That is what makes the byte-exact anchor in §CP4 possible.

---

## Implementation Plan

### Design

**D1. The grid (default values; see Q1).** All values below are inside level 05's training ranges (nutrition 0–200, injury 0–100, body temperature −10 to +5).

| Axis | Levels | Why these |
|---|---|---|
| Starting injury | 0, 30, 60, 90 (4) | All four are levels of the existing injury grid, so every cell at fullness 100 and 0° has an existing recording to compare with (CP4) |
| Starting nutrition (fullness) | 20, 60, 100, 140, 180 (5) | Symmetric around the comfortable value 100: two hungry levels, the comfortable level, two over-full levels |
| Starting body temperature | −10, −5, 0, +5 (4) | Level 05's training range for random start temperature. 0 is the comfortable value, and the anchor |
| Scene | no animal, predator, wandering rabbit (3) | The injury grid's scenes. The chasing rabbit stays excluded (it sticks to the agent; open Known Bugs row) |
| Temperature arm | `neutral`, `fire_away` (2) | The two readings that differ most. In `neutral` the body relaxes toward 0°, so only the starting temperature varies. In `fire_away` hiding costs warmth |

That gives 4 × 5 × 4 = 80 cells per scene and arm, and **80 × 3 × 2 = 480 probe conditions per run**. For a run with no temperature system (levels 02–04) the temperature axis and the arms drop out: 4 × 5 × 3 = 60 conditions, built from the core scenes.

**D2. Rules come from the run; the scene comes from the probe.** For each output cell the generator does the following.
1. Load the core scene YAML, then apply the thermal generator's `build(src, arm, 'clean', None)` (imported, as `generate_injury_grid.py` does) to add the arm's ambient temperature and fire.
2. Load the run's saved config (`<run>/models/config.yaml`) through `load_env_config`, then `apply_saved_config_compat` (the same path `eval_rollout.py` uses for a saved config, so old runs work).
3. **Replace** the probe's `body:`, `sensory:` and `perceptual_noise:` sections, and every `thermal:` key except `enabled` and `default_temp`, with the run's resolved values. `default_temp` stays under the arm's control. The scene (`environment:`) and `behavior_measures:` stay the probe's, so behaviour is measured the same way in every run.
4. Override the start keys exactly as in §A1. Set `body.random_start_nutrition: false`, `body.start_nutrition: N`, `body.random_start_injury: true`, `body.start_injury_low/high: I`. When thermal is on, also set `thermal.random_start_body_temp: true` and `thermal.start_body_temp_low/high: T`. All five are always written explicitly, because the run's own values are random ranges (level 05 randomises all three).
5. Because perceptual noise comes from the run, the "clean vs noise-matched" battery choice goes away. A level-05 run gets its own (no) noise and a level-06 run gets its own noise block, which is the noise-matched battery by construction.

**D3. Checks run on the written file, not on the recipe.** The file is loaded through `load_env_config` → `load_env_params`, and the real `ParallelEnv` is reset. The generator then checks:
- **(a)** For all 4 episodes of a `PRNGKey(0)` reset, the state's `injury_level == I`, `nutrition == N` and `body_temp == T`, exactly in float32. Satiation equals the value derived from N.
- **(b)** A **rule diff**: every flattened key under `body`, `thermal`, `sensory` and `perceptual_noise` of the loaded probe equals the loaded run config's value. The only exceptions are an explicit allowlist: the start keys from D2 step 4 and `thermal.default_temp`. Keys missing from the run config (sub-keys whose parent switch is off) are listed as "unread, from default" and do not fail the check.
- **(c)** The observation width equals the run's.
- **(d)** For thermal arms, `T.verify` (arm survivability contract, a hiding bush that also blocks animals, full-arena view).

**Any failure exits non-zero and writes no manifest.**

**D4. Where generated files live (see Q3).** The recommended location is `configs/environment/experiment/behavior_probes/body_state_grid/generated/<world_label>/`, **gitignored**, with all arms in one folder. Condition names look like `avoid_pred_fireaway_inj30_nut060_tm05`, where `tm05`/`tp05` means −5°/+5°. Next to them the generator writes `manifest.json`, which records:
- for each condition: its scene, arm, injury, nutrition and temperature;
- the source run path and the sha256 of its saved config;
- the generator's git commit;
- the rule-diff report.

Keeping the files under `configs/` matters. `eval_rollout.py` applies saved-config compatibility, which quietly fills missing keys, only to files **outside** `configs/` (`_is_under_configs`, `:804-808`). A probe that lived under `results/` would therefore quietly skip the missing-key error.

**D5. Reuse across runs of the same world.** All seeds and both agents of one world share one `<world_label>` folder. `--check-only --run <other run>` re-runs check (b) against that other run. It must pass before the run is added to that world's sweep spec. A mismatch (a different world) fails loudly.

### File Changes

No `src/` change. No config-schema change, so `CONFIG_GUIDE.md` and `02_config_schema.md` need no update. No critical-registry setting changes, so `CONFIG_CRITICAL_SETTINGS.md` needs no change-log entry.

#### 1. NEW `scripts/eval/make_body_state_grid.py`

One level under `scripts/`, so the repo root is `parents[2]` (the depth hazard in `SCRIPTS_DEPENDENCY_MAP.md`). CLI:

```text
--run <run dir>            mandatory; reads <run>/models/config.yaml
--world-label <slug>       mandatory; output subfolder name
--injury 0 30 60 90        mandatory (no default in code; the values go in the command / spec header)
--nutrition 20 60 100 140 180   mandatory
--body-temp -10 -5 0 5     mandatory when the run has thermal on; refused when it is off
--arms neutral fire_away   mandatory when thermal on; each must be a key of the thermal generator's ARMS
--scenes avoid_none avoid_pred avoid_rabbitwander   mandatory; stems under core/avoidance/
--check-only               load + assert the files on disk against --run; write nothing
```

- Every grid value comes from the command line. **No defaults** (project rule), and each is echoed into each file's header and the manifest.
- The script refuses nutrition outside `[0, max_nutrition]` (after the run's config is loaded), injury outside `[0, max_injury]`, and temperature outside `[min_temperature, max_temperature]`.
- It refuses to overwrite a `<world_label>` folder whose manifest names a source run from a **different world**, meaning check (b) fails against it.
- It imports `build`, `measure`, `verify` and `ARMS` from `generate_thermal_probes.py` by file spec (as `generate_injury_grid.py:51-55` does). It does not copy them.
- Each file's header has the same form as the injury grid's: generated, do not hand-edit, the regenerate command, the source run, the cell values.

#### 2. `scripts/eval/eval_rollout.py` (batched recorder, around `:323-345` and `:482-512`)

```python
# scan_fn step_out — ADD next to snap_injury_level:
"snap_body_temp": next_state.body_temp,

# init_state / step_state SimpleNamespace — ADD:
body_temp=states0_np.body_temp[i]            # init
body_temp=scan_out["snap_body_temp"][t, i]   # per step
```

On a thermal-off config `state.body_temp` is still a scalar that stays at the setpoint. The snapshot then gains one float, the same one the unbatched path already writes.

**Do not add `thermal_field`** (§A4). The 11 behaviour measures and all existing fields must stay byte-identical (CP1).

#### 3. NEW `scripts/analysis/body_state_grid_steps.py`

One level deep, `parents[2]`, run-agnostic. It takes `--eval-dir <sweep output_dir>`, `--label <run label>`, `--manifest <generated dir>/manifest.json` and `--out <file>.npz/.json`. Per condition, at the evaluated checkpoint, it computes:
- survival steps (mean, median, and the full per-episode list);
- termination-reason counts;
- time course of share in the bush and share resting, over alive episodes only, each with its denominator;
- mean injury, nutrition and body temperature over time (body temperature needs change 2; the tool exits non-zero if a thermal cell's recordings lack `body_temp`);
- share of steps 1–25 spent in the bush (the injured window `scene_steps.py` uses).

It reads the recordings the sweep keeps under `<output_dir>/_scratch/`. It flags the no-animal scene as `deterministic: true`, so later statistics treat it as n = 1. **Survival steps are the performance measure; reward is not read.**

#### 4. NEW `configs/eval_sweeps/body_state_grid/bodygrid_lvl05_wave2_rppo.yaml`

This is the worked example and the smoke test, for the two second-wave level-05 runs (control and modulated agents, seed 42).

```yaml
name: bodygrid_lvl05_wave2
algo: rppo
output_dir: results/eval/avoidance/metrics_history_rppo_bodygrid_lvl05_wave2   # fresh; must not exist
probe: configs/environment/experiment/behavior_probes/body_state_grid/generated/lvl05_wave2
conditions: all
episodes: 30
max_checkpoints: 1
plot_measures: []
nodes: []          # filled at launch from live GPU/diary state
runs:
  - {label: lvl05_control,   path: results/JAX_RecurrentPPO/20260922-182534_rppo_bq2cover_lvl05_t1none_s42}
  - {label: lvl05_modulated, path: results/JAX_RecurrentPPO/20260922-182538_rppo_bq2cover_lvl05_t16quad_s42}
```

The header comment states the generator command that must be run first, because the probe folder is gitignored. The 16-world specs are `experiment-designer`'s (§Hand-offs).

#### 5. `.gitignore`: add `configs/environment/experiment/behavior_probes/body_state_grid/generated/` (only if Q3 = gitignored)

#### 6. NEW `tests/scripts/test_body_state_grid.py`

Each test must fail on today's code.

- `test_cell_pins_exact_start_state`: generate 3 cells into `tmp_path` from a fixture run config (a copy of the resolved level-05 world with thermal on). Include one cell with T = −10 and one with N = 180. Reset and assert (a) exactly. It fails today because the script does not exist.
- `test_run_rules_are_copied`: the fixture run config sets `body.healing_nutrition_cost: 0.5` and `thermal.metabolic_coupling: true`. Assert that both reach the loaded `EnvParams` of the generated probe. Then assert that a probe built the injury-grid way (extending `environment/default`) has 0.0 and false. That second assertion documents the gap this plan closes.
- `test_rule_diff_catches_mismatch`: hand-edit one generated file's `body.metabolic_cost` and assert that `--check-only` exits non-zero.
- `test_batched_recording_has_body_temp`: run `eval_rollout.py --batched --record` for 2 episodes of 5 steps on a thermal probe with a tiny checkpoint fixture. If no fixture checkpoint exists in `tests/`, call the batched rollout function directly with a random-init policy, following the pattern in `tests/scripts/test_eval_rollout_online_replay.py`. Assert that each snapshot has `body_temp`, and that it equals the unbatched path's value for the same seed. It fails today because the key is absent.

#### 7. `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` (same change; Maintenance Contract)

- Add rows for `make_body_state_grid.py`, with its by-file-spec import of `configs/…/thermal/generate_thermal_probes.py`, its import of `src.environment.saved_config_compat`, and its `parents[2]` depth.
- Add a row for `body_state_grid_steps.py`.
- Add a row for the new test file as a caller of both.
- Note in the `eval_rollout.py` entry that batched recordings now carry `body_temp`.

#### 8. `scripts/eval/dwell_sweep/README.md`

Add one paragraph: body-state grid probes are generated per world (point to the generator), and the spec should use `max_checkpoints: 1` and `plot_measures: []`.

### Cost

| Item | Count |
|---|---|
| Conditions per run (thermal world, default grid) | 480 |
| Episodes per run (30 per condition, newest checkpoint only) | **14,400** (at most 1.44M environment steps) |
| Conditions per run (non-thermal world) | 60 → 1,800 episodes |
| Existing injury grid, one arm, one run, for comparison | 30 conditions × 30 episodes × 50 checkpoints = 45,000 episodes |
| 16-world experiment, per seed (2 agents per world) | 32 runs × 14,400 = **460,800 episodes** |
| Generated YAML files | 480 per world → 7,680 for 16 worlds (why Q3 matters) |

Wall time is **not estimated**. It is measured at CP5. The only number on file is ~36 s for 12 conditions × 30 episodes in one batched process on a 20-core node ([[EXPERIMENT_EVAL_DURING_TRAINING]]). Scaled linearly, that suggests roughly 20–30 CPU-minutes per run. That scaling is an assumption until CP5 measures it. Recording disk size is also measured at CP5, not assumed.

---

## Checkpoints

- [ ] **CP1: the recorder change breaks nothing.** Before and after change 2, run the parity harness `scripts/eval/parity_check_eval_rollout.py` on one level-04 and one level-05 checkpoint, plus one probe config. Every existing snapshot field and all 11 measures must be byte-identical, and the only new key must be `body_temp`.
- [ ] **CP2: the generator's own checks.** Generate `lvl05_wave2` from the modulated run. All 480 files must pass (a)–(d). Check that the rule-diff report lists only the allowlisted keys, and paste it into the Implementation Report. Then run `--check-only --run <the control run>`; it must pass. Also run it against a level-04 run; it must **fail** (different world).
- [ ] **CP3: a test that must fail.** Run `tests/scripts/test_body_state_grid.py` on a checkout without changes 1–2. Record that it fails, then that it passes with them.
- [ ] **CP4: byte-exact anchor against the existing injury grid.** For the modulated level-05 run's newest checkpoint, compare cells `fireaway × {inj00, inj30, inj60, inj90} × nut100 × temp 0` with the existing `injurygrid_fire_away_clean` recordings for the same checkpoint and conditions (`avoid_*_inj{00,30,60,90}`), under `results/eval/avoidance/metrics_history_rppo_injurygrid_fire_away_clean/lvl05_modulated`. The CSV rows (11 measures) must be identical, and the per-step actions and positions of all 30 episodes must be `np.array_equal`. This confirms that pinning temperature at the setpoint and copying the run's rules changed nothing else (§A1, §A2). **If the existing recordings are missing, this checkpoint FAILS; it does not skip.** Regenerate them with that spec and `--max-checkpoints 1` first.
- [ ] **CP5: smoke run and cost measurement.** Run the example spec (change 4) on both runs through the real driver, on nodes chosen from live GPU and diary state. Record the wall time per run, the CPU-minutes, and the disk used under `_scratch/`. Then run `body_state_grid_steps.py` on both. Check three things:
  - in the `neutral` arm, a cell's `body_temp[0]` equals its T;
  - N = 20 cells end at or before step ~20, with termination reason starvation;
  - the no-animal scene is flagged deterministic.

## Decisions (user)

- **Q1: grid size.** The default is 4 injury × 5 fullness × 4 temperature × 3 scenes × 2 arms = 480 conditions per run. A lighter option is 3 × 3 × 3 × 3 × 2 = 162: injury 0/45/90, fullness 40/100/160, temperature −10/0/+5. A heavier option uses all four temperature arms: 960.
- **Q2: a scene with food?** The current scenes have no food, so a hungry agent cannot act on its hunger. It can only run out of time. A scene with a food item away from the bush would test the "eat or hide" trade-off directly. That is scene design, which belongs to `experiment-designer`. The generator accepts any scene, so this can come later. Should it be part of the first batch?
- **Q3: where the generated files live.** Recommended: gitignored under `configs/`, regenerated on demand from the manifest command. This avoids committing about 7,700 generated files and keeps the missing-key error active. The alternative is to commit them for full provenance.
- **Q4: which checkpoint.** The default is the newest checkpoint only. The existing injury grid evaluated every checkpoint (about 50 per run), which would multiply the cost by about 50.

## Hand-offs

- `experiment-designer`: the 16-world sweep specs and grid levels in `docs/experiments/active/level05_body_interactions/`, and any food scene (Q2).
- `bug-curator`: record "batched evaluation recordings omit `body_temp` and `thermal_field`". Change 2 fixes `body_temp`; `thermal_field` stays open (render-only impact).
- `env-config-reviewer`: pre-flight on one generated world folder before the first real sweep.

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
