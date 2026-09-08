---
title: "Temperature System — Implementation Plan"
topic: sensors
status: active
created: 2026-09-08
last_updated: 2026-09-08
aliases: [thermal_implementation_plan]
---

# Temperature System — Implementation Plan

> **Status**: PLANNED — nothing here is built.
> **Opened**: 2026-09-08
> **Design source**: [[temperature_system_plan]] — `docs/develop/active/thermal/temperature_system_plan/index.html` (read `page_template.html` for the prose; `index.html` is 1.9 MB of embedded figures). Calibration sandbox: `sim.py` + `build_page.py` in the same folder.
> **Reference implementation adapted (not ported)**: EVAAA at `vendor/evaaa/evaaa_unity` — `Assets/Scripts/Environment/ThermoGridSpawner.cs`, `Assets/Scripts/Agent/ThermalSensing.cs`, thermo paths in `Assets/Scripts/Agent/InteroceptiveAgent.cs`.

---

## Revision note — 2026-09-08, after plan review

`plan-reviewer` returned **NOT READY** on the first draft with four High findings, all of the same kind: the plan promised that every stage carries a test that would fail if that stage were built wrong, and in four places that promise did not hold. The design and the staging were judged sound; the amendments are local. Each was independently confirmed against the code before being written in.

| Finding | What was wrong | Where it is now addressed |
|---|---|---|
| **R1** | Stage 1 was untestable: no config in `configs/` carries a `thermal:` key, and the fixture generator's loader does not resolve `extends:`, so every fixture config would raise at load and byte-parity could not be evaluated at all. The migration scope is 140 full configs plus ~21 test modules, not the 34 committed fixtures. | Stage 1, "Config migration"; F6 |
| **R2** | The byte-parity gate collides with a known 1-ulp non-determinism in `jax_reset`, so it can go red for compiler reasons and the tempting fix retires the gate. | Stage 0, "Adjudication rule"; H14 |
| **R3** | Stage 6b's load-time structure check would make the Stage 2–5 test configs unloadable, breaking "each stage reverts independently". Two of its formulas were also wrong. | Stage 6b, rewritten |
| **R4** | `build_sensory_viz` silently mis-slices every later sensor panel when a new modality is added — no exception, just wrong videos. It was missing from the file list entirely. | F7; Stage 3; Stage 6a; H15 |

Medium and low findings are folded into the stages they belong to and are not separately tabulated.

**Fifth amendment, same day — closing the Open Decisions list.** Two more user decisions: **do not bump `RECORDING_FORMAT_VERSION`** (D4 — grounded in the finding that nothing reads it back, F10) and **keep `topic: sensors`** (D5 — matching the `dreamer_srl_v1` / `dreamer_srl_v2` / `sheeprl_bridge` precedent). The candidate-range item closes too (D6): the design page's config block has been corrected to `[-28, -22]`, so design and plan now agree. Stage 6a gains a caveat that **a separate rendering rewrite is coming and may supersede it** — with F7's `build_sensory_viz` fix explicitly exempt, since it is a correctness fix that lands with Stage 3. A third `bug-curator` handoff recorded (F10). **Open Decisions now holds one item, and it is a measurement rather than a decision.**

**Fourth amendment, same day — migration-scope decisions.** The user set the migration policy: **lazy** (D4) and **the 68 already-broken configs stay broken** (D5). Stage 1's migration shrinks from 140+ configs to roughly **55 files** — `default.yaml` (which covers the whole `basic/` level and all 216 layered configs by inheritance, since all 7 `basic/` files use `extends:`), the 34 fixtured full configs (non-negotiable: they are the measuring instrument), and the ~21 test modules plus 1 test-fixture YAML (non-deferrable: they run on every test invocation). The other 106 full configs are deferred and must **not** be touched. F6 rewritten around the policy; F9 added for the 68 pre-existing failures with a `bug-curator` handoff; every "byte-identical" claim reworded to the measured scope — **34 of 356 configs, no live experiment family among them** — which the user has accepted knowingly.

**Third amendment, same day — second plan review.** HIGH-3 (6b gating) and HIGH-4 (`build_sensory_viz`) closed; four items remained, all confirmed against the code before amending:

| Finding | What was wrong | Where it is now addressed |
|---|---|---|
| **R5** | Migration scope was wrong by an order of magnitude — 34 is the *fixture* count; `collect_configs` returns **356**, of which **140** are full configs, plus ~21 test modules with inline YAML bases. Stage 1 named `test_no_recompile.py` as a required gate while omitting the migration that keeps it green. | F6, rewritten with measured counts; Stage 1 "Config migration" |
| **R6** | The campfire was shown going into `default.yaml`, which through list-replace semantics would silently give a fire to **216 layered configs** — non-blocking, rock-coloured, mostly unfixtured, invisible. | **F8** (new); Stage 1 diff check |
| **R7** | The described placement mechanism does not exist: `resolve_overlaps_global` is a single-pass deterministic scan with **zero per-entity draws**, not reject-and-resample. Building a rejection loop would trip this plan's own H10. | Stage 1, "How the placement constraints actually attach" |
| **R8** | The ulp exemption was keyed on the observation, but the 1-ulp bound is measured on *state arrays*; a legitimate implementation can exceed it downstream. | Stage 0, adjudication rule, re-anchored upstream |

Mediums and lows folded in: a single definition of "heat source" (a slot, not an entry); the placement no-op test's reference fixture named; both pre-existing parity gates added to every stage's required-green list; the reset-blur test given a degenerate config; the numpy oracle's `H = W = 10` coupling resolved; the `mode='drop'` claim corrected; `drive_thermal`'s convention pinned. A `bug-curator` handoff for the silent cell-0 placement fallback is recorded in Stage 1.

**Second amendment, same day.** Three design questions came back decided from the user: the campfire's visual identity (D1), fire separation (D2, which also closes the review's Medium finding about single-fire calibration), and food placement (D3). They add two config keys — `min_fire_separation` and `food_min_fire_distance` — and are recorded with their reasoning under *Decisions settled by the user*. The corresponding Open Decisions entries are gone, not merely annotated.

---

## Purpose

The agent in this project currently has two things it must keep in range: how full it is (satiation) and how hurt it is (injury). A separate, already-approved design adds a third — **body temperature** — by making the world cold everywhere and putting a campfire in it. The agent's temperature drifts toward whatever cell it stands on, so it freezes if it wanders and burns if it sits on the fire; the only comfortable place is a ring one cell out from the flames. Food grows away from the fire, so eating means a timed round trip into the cold.

That design is settled. **This document is the build plan for it**: seven stages, each one independently testable, each one with the specific test that would fail if that stage were built wrong, and each one with a way to undo it. Stages 0 through 2 must leave existing behaviour byte-for-byte identical — if they do not, something has been wired into the live path that should have been behind the off switch. **What "identical" is actually measured over is 34 of the project's 356 environment configs** — the ones with a committed reference fixture. That coverage limit is a knowing trade, not an oversight; it and the lazy-migration policy behind it are set out in F6.

Five things in this plan are corrections to, or gaps in, the design document rather than restatements of it. They are called out in **Findings that change the build** below, and the most important one is that the reward formula as written in the design is *not* bit-identical to today's reward even with temperature switched off — it silently rescales every reward in the project by a factor of 100.

---

## Findings that change the build

These came out of reading the code the plan targets. Each is a place where implementing the design as literally written would break something. They are stated up front because they change what gets built, not merely how.

### F1 — The design's drive formula rescales all existing rewards by 1/100

Today's drive (`src/environment/core.py:49-53`) is **unnormalised**:

```python
def calculate_drive(satiation, injury, params):
    target = jnp.array([params.setpoint, 0.0])
    current = jnp.stack([satiation, injury], axis=-1)
    return jnp.linalg.norm(current - target, axis=-1)
```

The design's §8 writes the three-axis drive as `‖((satiation−setpoint)/max_satiation, injury/max_injury, (T−T_setpoint)/max_temperature)‖`. With `max_satiation = max_injury = 100` (`configs/environment/default.yaml:161,163`), that normalised form equals today's drive divided by 100. Reward is `prev_drive − curr_drive`, so **every reward in the project shrinks by 100×** while `death_penalty` stays at 100 (`default.yaml:182`) — the death penalty would go from comparable-to-a-few-steps to overwhelming. That is not a gated change; it fires the moment the new `calculate_drive` is called, thermal on or off.

Worse, one archived config in the parity fixture set uses `max_injury: 30` (`configs/environment/experiment/archive/2X2_area.yaml:191`), so normalisation also changes the *relative weighting between the two existing axes* there, not just the global scale.

**Build the algebraically identical form in today's units instead.** Equal normalised weight per axis is preserved exactly by scaling the third axis into satiation units rather than dividing the first two down:

```python
def calculate_drive(satiation, injury, params, body_temp=None):
    if not params.thermal_enabled:                      # static branch, trace time
        target  = jnp.array([params.setpoint, 0.0])     # UNCHANGED expression
        current = jnp.stack([satiation, injury], axis=-1)
        return jnp.linalg.norm(current - target, axis=-1)
    # thermal on: third axis scaled so an equal FRACTIONAL deviation pulls equally,
    # in the units the other two already use.
    t_axis = (body_temp - params.temperature_setpoint) * (
        params.max_satiation / params.max_temperature)
    current = jnp.stack([satiation, injury, t_axis], axis=-1)
    target  = jnp.array([params.setpoint, 0.0, 0.0])
    return jnp.linalg.norm(current - target, axis=-1)
```

This is the same design — each axis normalised by its own range — multiplied through by the constant `max_satiation`. It leaves the thermal-off path as the *identical Python expression* it is today (not merely a numerically equal one), which is what makes bit-parity provable by inspection rather than by measurement. It also keeps `death_penalty` calibrated.

The scale factor when the design's numbers are used is `100/15 ≈ 6.67`, so one degree of body-temperature deviation is worth 6.67 satiation units of drive. That number belongs in the config guide, because it is the actual exchange rate between warmth and hunger and nothing else in the config makes it visible.

### F2 — A new observation modality raises a `KeyError`, not a dimension mismatch, in any config with perceptual noise on

`apply_perceptual_noise` (`src/environment/sensor.py:386,394`) does `modality_map[sensor_name]` for **every** key `get_observation_breakdown` emits, where `modality_map` is built from `params.noise_modality_order` (the YAML key order of `perceptual_noise.modalities`, `default.yaml:312+`). Adding `breakdown["Thermoception"]` without adding a `thermoception:` modality block raises a bare `KeyError: 'Thermoception'` inside a jit trace — no message naming the config or the fix.

The noise arrays do **not** need widening — `_parse_noise_config` pads to `max(0, 13 - len(order))` (`config_loader.py:1672`), so a fourteenth modality simply produces a length-14 array. What *is* needed, and is easy to miss, is the entry `"thermoception": "Thermoception"` in **`_YAML_KEY_TO_SENSOR_NAME`** (`config_loader.py:1635-1646`), which is a strict whitelist: an unlisted YAML modality key raises "Strict Config: unknown perceptual-noise modality key(s)" at `:1651-1656`. So the config edit and the dict edit are mutually blocking — either one alone fails.

Two secondary consumers hard-fail on unknown breakdown keys by design: `src/utils/evaluation_core.py:158-196` (`_sensor_stat_columns`, raises "No stats-CSV column mapping for sensor …") and `src/algorithms/dreamer_srl/agent.py:2468-2472`. A third, `build_sensory_viz`, does **not** fail — see F7, which is the dangerous one.

**The `thermoception:` block must declare `clip_min` and `clip_max` explicitly.** They default to −100 and +100 (`config_loader.py:1688-1697`), and the relative reading on the fire cell is around **+300** — so a noise-enabled thermal run would train on a sensor clipped to a third of its range, with the fire and its comfort ring rendered indistinguishable at the top of the scale. No test would catch it: every test in the plan runs with noise off. Set the bounds from the actual field range implied by `default_temp` and the ratio, and state the derivation in the config comment.

**Stage 3 does all of this in one change**: the modality block in `configs/environment/default.yaml` with explicit clips, the `_YAML_KEY_TO_SENSOR_NAME` entry, the `_sensor_stat_columns` branch, and the `build_sensory_viz` branch. The `KeyError` is what a partial job looks like; the shifted video is what a nearly-complete one looks like.

### F3 — Out-of-bounds thermoceptor cells must edge-clamp, not read zero

`sense_olfaction_cells` (`sensor.py:52-62`) zeroes out-of-bounds cells, and the visual sensor does the same. For a *relative* thermal reading (`field − body_temp`) in a world whose baseline is −25, a zero reads as "that cell is exactly my own temperature" — the single most misleading value available, and it would make the map edge look like a warm refuge to an agent standing in the cold.

The field itself is already edge-clamped: `sim.py`'s `gaussian_smooth` renormalises by the in-bounds weight sum, which is EVAAA's `sum / weightSum` (`ThermoGridSpawner.cs:278-286`). **Sample out-of-bounds thermoceptor cells by clamping the coordinate into the grid**, so the reading is the nearest real cell. This deliberately departs from the olfaction/visual zero-fill convention; the departure must be commented at the call site and documented in `02_config_schema.md`, because a future reader will otherwise "fix" it back.

### F4 — `edge_margin` does not need to be a new mechanism

The design proposes `edge_margin: 2` on the campfire entry. Obstacles already carry a spawn rectangle — `area: [[1,1],[10,10]]`, 1-based inclusive, parsed to `[min_r, min_c, max_r, max_c]` (0-based min, exclusive max) at `config_loader.py:1262` — and `jax_reset` samples positions uniformly inside it (`core.py:996-998`). Confirmed absent: `grep -rn "edge_margin|margin|border"` over `src/` returns only matplotlib padding and colour tokens. No new runtime path is needed.

**Implement `edge_margin` as a load-time transformation of `area`**, not as a runtime constraint: intersect the entry's declared area with the rectangle inset by `edge_margin` cells on all four sides, and raise if the intersection is empty. The sampler is untouched, the constraint is enforced before any array is built, and a nonsensical margin fails at load rather than producing a degenerate spawn box.

The alternative — a rejection term in the `in_area` test inside `resolve_overlaps_global` (`core.py:870-872`) and `place_in_area` (`core.py:913-915`) — is rejected: it puts a per-episode traced condition into the shared placement scan for every entity class, to enforce something that is a config-time constant.

### F6 — A conditional-mandatory key with no config declaring it makes Stage 1 unloadable, not merely untested

`thermal.enabled` is read with `config.get_mandatory`, which raises on a missing key by design. **Zero configs under `configs/` currently carry a `thermal:` key** (verified: `grep -rln '^thermal:' configs/ | wc -l` → 0). Separately, `extends:` resolution lives in `train.py`'s `load_env_config`, *not* in `Config` — `Config.load_yaml` is `cls(yaml.safe_load(f))` and nothing more (`src/utils/config.py:30-45`), and both the fixture generator and the parity test construct params straight from `Config(yaml.safe_load(f))`. So a sparse config cannot inherit `thermal.enabled` from the base in the test harness the way it can in training.

The consequence is not a failing assertion; it is `ValueError` at load, and the blast radius is much larger than the fixture count suggests.

**The migration scope, measured.** Running `collect_configs`' own globs:

| Quantity | Count | Why it matters |
|---|---|---|
| Configs `collect_configs` returns | **356** | the set the gate walks |
| …of which **full** (no `extends:`) | **140** | each must carry the key itself |
| …of which layered (`extends:`) | 216 | inherit from `default.yaml` via the merge |
| `.npz` fixtures on disk | 34 | **only the number with a committed reference** |

The 34 figure the previous draft used was the fixture count, and it is the wrong number for migration scope: configs without a fixture are **silently skipped** by the gate, not excluded from loading. They still have to load — other tests and every training launch go through them — and they would still raise.

In principle every YAML loaded *without* `extends:` resolution needs the key — all 140 full configs. **The user has chosen not to migrate all of them.**

### The migration policy: lazy, with three non-deferrable groups

> *"Update only the default and basic levels, not the others — I will make them update when they need to be run."*

Applied concretely, that gives a Stage 1 set of roughly **55 files**, not 140+:

**(a) `configs/environment/default.yaml`** — gets the `thermal:` block. This single edit **covers the entire "basic level" and all 216 layered configs through inheritance**. Verified: all 7 files in `configs/environment/experiment/basic/` use `extends:` (four chain to `environment/default`, three chain through `basic/03` and `basic/04`), so **there are no per-file `basic/` edits to make** — a reader expecting seven of them will go looking for changes that are correctly absent. See F8 for what must *not* go into this file.

**(b) The 34 configs with a committed `.npz` fixture — non-negotiable under any policy.** All 34 are full configs (the generator uses raw `Config(yaml.safe_load(f))`, so only a full config can ever be fixtured). Measured breakdown: **archive 22, verification 6, continual 5, `default.yaml` 1**. If these do not carry `thermal.enabled` inline, `get_mandatory` raises and **the existing parity suite fails before Stage 1's own gate can run** — these are the instrument the stage is measured with, so they are exempt from deferral by construction, not by preference.

**(c) The ~21 test modules with inline YAML bases, plus `tests/fixtures/trajectory_collection/dual_format_config.yaml` — also non-deferrable.** `tests/env/test_no_recompile.py`, `tests/env/test_directional_sensors.py`, `tests/env/test_per_episode_count.py` and the rest of the `0e8a4ef8` set build params without going through `load_env_config`. **These are not configs anyone chooses to run** — they execute on every test invocation, so deferring them leaves the suite red from the moment Stage 1 lands. This plan also names `test_no_recompile.py` as a Stage 1 required-green gate, so skipping them makes the stage fail its own gate.

### What is deferred, and why that is safe

The remaining **106 non-fixtured full configs** (archive 69, sensory_ladder 14, continual 13, sensory_directional 10) are **deliberately not migrated**. The user updates each one when a run next needs it.

This is safe for one specific reason worth stating rather than assuming: a deferred config fails **loudly and self-describingly**. `get_mandatory` raises `Configuration key 'thermal.enabled' is required` — it names the missing key, at load, before anything trains. There is no silent-wrong-result path, because the no-fallback rule is what forbids one. Deferral would *not* be safe under a `.get(..., False)` default, which is a further reason that route stays forbidden.

It is also less of a change than it looks: **68 of those configs already fail to load today**, predating two earlier mandatory-key additions (see F9). Thermal does not change their status.

### The honest coverage statement

With this policy the byte-parity gate covers **34 of 356 configs (under 10%)**, and no currently-live experiment family is among them — the fixtured set is mostly archive. So the guarantee this plan can actually make is *"byte-identical on the 34 fixtured configs"*, not *"byte-identical everywhere"*. The user has accepted that trade knowingly. Every claim in this document is worded to that measured scope, and any future reader tempted to read more into a green gate should read this paragraph first.

### F9 — 68 configs are already unloadable, and that is not this work's problem

Independent of thermal, **68 full configs** — mostly under `configs/environment/experiment/archive/` — currently fail `load_env_params` because they predate two mandatory-key additions: **68 lack `sensory.injury_observable`** and **13 lack `sensory.visual_value_mode`** (the second set is a subset of the first, so the union is 68).

**Explicitly out of scope.** Not caused by this work, not fixed by it, and not Stage 1's job — the user's decision is "leave them". Recorded here so that a developer who trips over one during the migration recognises it as pre-existing rather than something they broke, and does not silently expand Stage 1 to chase it.

**Handoff to `bug-curator`:** file as its own registry item, separate from the thermal plan and from the cell-0 placement fallback (Stage 1). The bug is that mandatory-key additions have been landing without migrating the archive, so the archive is quietly accumulating unloadable configs; thermal is simply the third instance.

### F10 — The recording format carries a version stamp that nothing validates

`RECORDING_FORMAT_VERSION` is written into every `.rec` payload (`eval_recording.py:65`) and every `run_meta.pkl` (`:82`), and **no code anywhere reads it back** — not the renderer, `async_render.py`, `evaluation_core.py`, `dreamer_srl/eval.py`, or the behaviour-measure scripts.

A reader of `eval_recording.py` would reasonably assume recordings are checked for compatibility on load. They are not. Today that costs nothing, which is exactly what makes it a trap: **the first time someone makes a real format change and relies on the stamp to catch stale recordings, it will silently do nothing** and old files will be read as if they were new.

Out of scope for this plan — D4 routes around it rather than depending on it. **Handoff to `bug-curator`**, as a third registry item distinct from the archive-migration drift (F9) and the cell-0 placement fallback (Stage 1). Frame it as the pattern: *a version stamp that is written but never validated is worse than no stamp, because it advertises a guarantee that does not exist.*

**Stage 1 therefore includes an explicit config migration, in the same commit.** The `.get('thermal.enabled', False)` route is forbidden: a fallback default for a gating key is exactly what the no-fallback rule exists to prevent, and it would let a config with a typo'd `thermal:` block train as if thermal were off. Precedent for the bulk migration is commit `0e8a4ef8`, which did the same for `visual_blur_enabled`.

### F8 — The campfire must NOT go into `default.yaml`, or 216 configs silently gain a fire

This is the quietest failure in the plan and the worst, because every other one is loud.

`Config.merge` / `deep_update` **replaces lists wholesale**, and `load_env_config`'s own authoring note (`config_loader.py:88-93`) spells out the consequence: *"Omitting the key entirely causes the base's list to survive the merge unchanged."* A layered config suppresses a base list only by declaring it explicitly empty.

So if the `- name: campfire` entry lands in `default.yaml`'s `environment.obstacles:` list, **every one of the 216 `extends: environment/default` children that does not declare its own `obstacles:` block silently gains a campfire.** And it is close to undetectable:

- the campfire is `blocking: false`, so nothing collides with it;
- under D1 it renders on obstacle channel 6, so it looks exactly like a rock;
- most of those 216 children are unfixtured, so **no parity gate ever sees it**;
- with `thermal.enabled: false` the field is never built, so it has no thermal effect either — it is simply an extra non-blocking obstacle occupying a cell.

The result is that every experiment launched after Stage 1 runs in a subtly different world from its own pre-thermal baseline — one extra entity in the placement occupancy mask, shifting where everything else spawns — with no failing test and no visible symptom.

**The rule: `default.yaml` gets the `thermal:` key block ONLY.** The campfire obstacle entry lives in a new example config under `configs/environment/experiment/thermal/`, which is also where the Stage 2–6 test configs belong. The `§ Configuration` block below shows the campfire entry to document its *shape*; it is not an instruction to put it in the base file.

**Stage 1 check:** diff `configs/environment/default.yaml`'s `obstacles:` list before and after the migration and require it **unchanged**. A one-line assertion, and it is the only thing standing between this plan and a silent world change across the whole config tree.

### F7 — A new modality silently corrupts every later renderer panel

`build_sensory_viz` (`src/environment/sensor.py:540-608`) walks `get_observation_breakdown` accumulating a slice pointer, and it is an `if`/`elif` chain **with no terminal `else`**. An unrecognised sensor name matches no branch, so `ptr += dim` never runs and the pointer falls 5 behind for the rest of the walk.

Thermoception is inserted *before* Olfaction, so every panel after it — olfaction, collision, proprioception, visual, location — would render from a slice shifted by five. Nothing raises. The videos are simply wrong, and they look plausible. This is the same class as the visual-sensor stencil bug that cost this project the most time, and it was absent from the first draft's file list.

Two independent edits are required, and neither substitutes for the other: a `Thermoception` branch in `build_sensory_viz` (Stage 3), and the name added to the renderers' pod lists — `renderer.py:626` `known_sensors = ['Olfactory', 'Extero Nociception', 'Collision', 'Visual', 'LOC']` and the `pod_map` copy at `renderer_v2.py:474-479` (Stage 6a). **Add `else: raise ValueError(...)` to the chain while there**, so the next modality fails loudly instead of repeating this.

### F5 — The parity harness the plan needs does not exist yet

`tests/env/test_unified_parity.py` and its generator `scripts/fixtures/generate_parity_fixtures.py` compare **state fields and a handful of info keys**. The observation is a literal placeholder — `obs_list.append(jnp.zeros(1))  # placeholder — we record state fields` (`generate_parity_fixtures.py:64`). Reward and drive are not captured at all. `tests/env/test_visual_parity.py` covers only the visual slice of the observation.

So Stage 0 is not "run the existing gate"; it is a genuinely new fixture set covering the full observation vector, the scalar reward, and the drive. Without it, Stages 1 and 2 have nothing to be byte-identical *against*.

---

## Analysis — the code this plan targets

### Where the pieces live

| Concern | File : symbol | Note |
|---|---|---|
| Episode state | `src/environment/state.py:31` `EnvState` | gains `thermal_field`, `body_temp` |
| Static params | `src/environment/state.py:98` `EnvParams` | gains the `thermal_*` block + per-entity temperature arrays |
| Drive | `src/environment/core.py:49` `calculate_drive` | see F1 |
| Body update | `src/environment/core.py:55` `update_body` | gains the `T` recurrence and its death test |
| Termination codes | `src/environment/core.py:702-712` | the single producer; enum comment at `:703` |
| Field build | `src/environment/core.py:945` `jax_reset` | new stage, after entity placement |
| Config load | `src/environment/config_loader.py:1000` `load_env_params` | conditional-mandatory block |
| Per-entity flag pattern | `src/environment/config_loader.py:330` `_read_blocks_sight` | the pattern `temperature` copies |
| Obstacle arrays | `src/environment/config_loader.py:1228-1301` | `o.get(key, default)` per slot |
| Diamond offsets | `src/environment/sensor.py:157-185` `get_visual_offsets` | `r=1` returns `[[0,0],[-1,0],[0,1],[1,0],[0,-1]]` |
| Observation assembly | `src/environment/sensor.py:424` `get_observation` | insertion-ordered |
| Observation widths | `src/environment/sensor.py:482` `get_observation_breakdown` | must stay in lockstep with the above |
| Noise application | `src/environment/sensor.py:377` `apply_perceptual_noise` | see F2 |
| Curriculum gate | `train.py:844-873` (inside `main()`, starts `:390`) | dims first, fingerprint second |
| Dreamer's copy of the gate | `src/algorithms/dreamer_srl/dreamer_srl_main.py:771-863` | near-identical, needs the same edit |
| Renderer (**live**) | `src/environment/renderer.py:355` `render_jax_state` | terrain tiles at `:425-432` (`zorder=0`); vitals HUD at `:544-606` |
| Renderer (dormant) | `src/environment/renderer_v2.py:216` `render_jax_state_v2` | terrain tiles at `:338-347`; vital-card mosaic at `:260-262` |
| Offline-render snapshot | `src/utils/eval_recording.py:24-40` `_snapshot_state` | "Keep in lockstep with renderer.py" |

**Which renderer is live.** `render_jax_state` in `renderer.py` is the one that runs: called from `scripts/eval/render_recordings.py:93,120` (the offline video path), `scripts/media/record_env_demo.py:53`, `scripts/dreamer/visualize_dream.py:159,171`, and `scripts/eval/benchmark_render.py:39,115,135`. **`renderer_v2.py` has zero call sites anywhere in the repo** — it is dormant and imports its helpers *from* `renderer.py` (`:26-32`). Do the thermal work in `renderer.py` first; mirror it into `renderer_v2.py` so the dormant copy does not rot further. Separately, `src/environment/grid_world.py` is a stale near-verbatim copy of `renderer.py` (its own `render_jax_state` at `:344`) that nothing imports — it will appear in greps; leave it alone and do not edit it into a third divergent copy.

### The JAX shape question, answered by an existing pattern

Per-episode sampled counts already exist and already solve this. `_resolve_count_range` (`config_loader.py:965-997`) allocates `count_high` slots at load time; `_build_activation_mask` (`core.py:1195-1237`) draws `K` per entry at reset and turns the surplus slots off with a boolean mask (`state.obs_active`). Array shapes are fixed by `count_high`, which is a load-time constant. **The campfire uses this unchanged** — `count_low: 1, count_high: 3` allocates three obstacle slots, and inactive fires contribute zero temperature.

That makes the field build a masked scatter-add over a statically shaped array:

```python
# stamps ADD (design §3): .at[].add() with duplicate indices is a scatter-add in
# JAX, so two fires on one cell combine and the result does not depend on slot order.
stamp = jnp.where(state.obs_active, obs_temp_episode, 0.0)          # [num_obs]
field  = field.at[state.obs_pos[:, 0], state.obs_pos[:, 1]].add(stamp, mode='drop')
```

Inactive slots are **parked off-grid at `(height, width)`** rather than removed — `core.py:1265-1275` writes `_off_grid = jnp.array([params.height, params.width])` into the position of every masked-off slot. Two independent things keep those slots from depositing heat, and it is worth being precise about which does the work:

- **The `jnp.where` mask is the guard that matters.** It makes the deposited value zero regardless of where the index lands.
- **`mode='drop'` is explicit, not load-bearing.** JAX's default out-of-bounds behaviour for *scatter* (`.at[].add()`) is already to drop — verified empirically, not assumed; it is *gather* that clamps. Writing `mode='drop'` states the intent at the call site rather than relying on a default most readers will have to look up. **Do not "simplify" by removing the `jnp.where` mask on the strength of the drop** — the mask is the real protection, and an earlier draft of this plan had this backwards.

Three further shape hazards and their resolutions:

- **Blur radius.** `sim.py` truncates the kernel at `radius = ceil(3*sigma)` and renormalises by the in-bounds weight sum. Every calibrated number in the design depends on that truncation, so the implementation must reproduce it. `radius` is therefore a **static** field computed in Python at load (`thermal_kernel_radius: int = struct.field(pytree_node=False)`), while `thermal_sigma` stays a traced float used only for the weights. A sigma sweep recompiles only when it crosses a radius boundary. Do **not** "simplify" this to a full-grid kernel: the field values change and none of the calibration survives.
- **Random spots.** `random_spots.count` is a scalar config int, not a range, so the loop is unrolled at trace time with a static bound. If a count range is ever wanted, it uses the `count_high` + mask pattern above; it must not use a traced loop bound.
- **`default_temp` is a sampled scalar.** A per-episode `uniform` draw from a fold_in key — a traced scalar, shape `()`. It multiplies the campfire ratio; no shape depends on it.

**PRNG discipline.** Every new draw at reset must come from `jax.random.fold_in(<existing key>, <new constant>)`, never from widening an existing `split`. `jax_reset` documents this convention explicitly (`core.py:957-959`: the 5-way outer split is "byte-for-byte", and `animal_episode_key` is derived by `fold_in(property_key, 0xAE1)`). The per-episode behavioural split is locked at 7 (`core.py:1278`), and the most recent feature to need a new draw obeyed the rule rather than widening it — `attack_range_key = fold_in(animal_episode_key, 0xA77AC7)` at `core.py:1299`. The count-activation masks do the same with `_COUNT_KEY_RES/ANIMAL/OBS = 0xC0A1/0xC0A2/0xC0A3` (`core.py:1201-1203`). Follow that pattern for the two new draws (`default_temp`, per-fire ratio). Widening a split renumbers every downstream stream and the parity gate goes red across every fixtured config at once — and `state.key` is captured in the fixture precisely so that failure is legible as "the PRNG stream moved" rather than as a diffuse observation mismatch.

### Termination code 5 — what has to move with it

`termination_reason` is produced in exactly one place (`core.py:702-712`) and is **not** part of `EnvState`; it travels in the per-step `info` dict. The good news is that both PPO trainers, Dreamer, and the tests all define "real death" as `termination_reason >= 2`, so **code 5 is picked up as a death automatically** by:

`src/models/ppo_trainer.py:236,239`; `src/models/recurrent_ppo_trainer.py:415,417,437,469,495,505,508`; `src/algorithms/dreamer_srl/dreamer_srl_main.py:1692-1702`.

The bad news is the label maps, which enumerate `1..4` literally in **six** places and will silently drop thermal deaths:

- `train.py:1543, 2054, 2260, 2413` — four duplicated copies of `[(1,'MaxSteps'),(2,'Starvation'),(3,'Overeating'),(4,'Injury')]`
- `src/algorithms/dreamer_srl/dreamer_srl_main.py:1231` — a fifth copy
- `src/behavior/episode_metrics.py:41-44,196-235,269-272` — named constants. It has no runtime caller in `src/`, `train.py` or `scripts/`, but it is **not** dead: `dreamer_srl_main.py:406` names a regression test for it, and it carries a docstring contract. **Update it; do not delete it.** Deleting a module because grep found no import is how a test starts failing for a reason nobody can trace back to this change.

And two analysis paths that will **hard-fail or silently mis-total**:

- `scripts/analysis/ladder/_ladder.py:90` — `TERM_NAMES = {1: …, 2: …, 4: …}` covers only three codes; `scripts/analysis/studies/sensor_ladder/collect_arm_data.py:41,68,177` degrades anything else to a stringified int
- `scripts/analysis/studies/nmn_site_grid/grid_ladder_figures.py:150,160,168` — hard `raise SystemExit` if the three known shares do not sum to 100. A thermal run's shares will not.

Plus the schema docstrings and the pinning test: `src/utils/trajectory_store.py:140-141,172` (int8 column; existing on-disk stores carry the old codes) and `tests/models/test_gae_truncation.py:132`, which hardcodes `jnp.array([0,1,2,3,4])`.

---

## Configuration — the full key set

Added under a new top-level `thermal:` block, plus per-entity keys. Every sub-key is **conditional-mandatory**: read via `config.get_mandatory` only when `thermal.enabled` is true, and validated at the point it is read. That is the pattern `visual_blur_*` and `visual_occlusion_*` settled on (`config_loader.py:1030-1066`), and the reason it exists is on the record — an unvalidated `sigma_floor: 0.0` produced an all-NaN observation that trained silently.

```yaml
thermal:
  enabled: false            # gate; every key below is read ONLY when true

  # --- field ---
  sigma: 0.7                # tight band 0.6-0.8; validated > 0
  default_temp: [-28, -22]  # world baseline, sampled per episode
  use_random_spots: false
  use_object_sources: true
  random_spots:             # read only when use_random_spots
    count: 4
    size: 2
    temp: 40.0

  # --- placement constraints (settled 2026-09-08, see Decisions settled) ---
  min_fire_separation: 3    # Manhattan; validated >= 0. 0 = disabled, accepts merged fires
  food_min_fire_distance: 0 # Manhattan; validated >= 0. 0 = no constraint (today's behaviour)

  # --- body ---
  temperature_setpoint: 0.0
  min_temperature: -15.0    # validated min < max
  max_temperature: 15.0
  k_exchange: 0.04
  k_loss: 0.01
  k_metabolic: 0.0
  metabolic_coupling: false

  # --- sensor ---
  grid_range: 1             # validated >= 0
  relative: true            # report field - body_temp

```

**The `thermal:` block above goes into `configs/environment/default.yaml`. The obstacle block below does NOT** — it belongs in a new example config under `configs/environment/experiment/thermal/`, because a campfire in the base file propagates to 216 layered children through list-merge semantics (F8). It is shown here to document the entry's shape.

```yaml
# configs/environment/experiment/thermal/<example>.yaml  — NOT default.yaml
environment:
  obstacles:
    - name: campfire
      count_low: 1
      count_high: 3
      area: [[1, 1], [10, 10]]
      edge_margin: 2              # inset applied to `area` at LOAD time (F4)
      temperature_ratio: [11, 13] # fire = ratio x |default_temp|, sampled per fire
      blocking: false
      blocks_sight: false
      damage: [0.0, 0.0]
      nociception_intensity: 0.0
      properties: [0.0, 0.0, 0.0, 0.0, 0.0]
      properties_std: [0.0, 0.0, 0.0, 0.0, 0.0]
      visual_properties: [0,0,0,0,0,0,1,0]
      visual_properties_std: [0,0,0,0,0,0,0,0]
    - name: bush
      temperature: 0.0            # absolute; every entity type, default 0.0
```

`temperature` and `temperature_ratio` are **mutually exclusive** on one entry, and an entry declaring both raises — the same rule and the same error shape as `count` vs `count_low`/`count_high` (`_resolve_count_range`, `config_loader.py:982-986`). `temperature` reads exactly like `blocks_sight`: `float(entry.get('temperature', 0.0))`, absent → 0.0, no `get_mandatory`, because zero is a genuine default rather than a fallback for a critical value.

Why the ratio, and not an absolute fire temperature: the window of fire strengths that produces the intended structure moves with the world baseline. In a −22 world it is roughly 265–315; in a −28 world roughly 305–365. Sampling both independently over the design's ranges leaves a **10-unit overlap**, and draws outside it silently produce either a fire that does not hurt or a comfort ring that is not survivable. Sampling the fire as a multiple of the world's coldness holds the structure in 100% of draws over `[-28,-22]` and 94% over a much wider `[-32,-20]` (`build_page.py`, `structure_ok`, 600 draws).

**Critical-settings registry.** `thermal.enabled`, `thermal.sigma`, `thermal.k_loss` and `thermal.grid_range` each get a row in `docs/environment/CONFIG_CRITICAL_SETTINGS.md` with a dated change-log entry in the same commit, per that document's logging protocol. `k_loss` earns its row on its own: at `k_loss ≈ 0.036` the survivable ambient window reaches ±25 and the world's own baseline can no longer kill anything — the thermal task disappears while still appearing to be configured. It is the number in this plan most likely to be changed by accident.

---

## Stage 0 — Parity harness

**Goal.** A committed, pre-change reference for observation, reward and drive, so every later stage's byte-identity claim is checkable rather than asserted. Must be built and committed **before any other change**, on the current tip.

**Files.**
- New `scripts/fixtures/generate_thermal_parity_fixtures.py` — modelled on `scripts/fixtures/generate_parity_fixtures.py`, same `config_slug` (`:36-42`) and `collect_configs` (`:44-52`) so the fixture set matches the existing gate, same `ACTIONS = [0,1,2,3,4]*20`, `SEED = 0`.
- New `tests/env/test_thermal_parity.py`.
- New fixtures under `tests/env/fixtures/thermal_parity/<slug>.npz`.
- `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` — the new script under `scripts/fixtures/` must be recorded there in the same change, per that map's Maintenance Contract.

**Scope: `collect_configs` returns 356 configs; 34 have committed fixtures.** Those two numbers do different jobs and the plan must not conflate them, which an earlier draft did. The **gate** covers the 34 configs with a committed `.npz` — the rest are *silently skipped*, not excluded. The **migration** (Stage 1, F6) must cover all 140 full configs plus the test modules, because every config still has to load whether or not a fixture watches it. Use the same `collect_configs` so the two gates cover the same set, extend the fixture set if the coverage gap is judged too wide, and record both counts in the Implementation Report.

**What is captured, per config, per step (100 steps):** the full observation with `apply_noise=False`, the same with noise on, the scalar `reward`, `calculate_drive(state.satiation, state.injury_level, params)` before and after the step, `info['termination_reason']`, and `sum(get_observation_breakdown(params).values())`. Additionally, and specifically to make the adjudication rule below usable: **`state.key`** (integers, compared exactly — the PRNG-stream tripwire), and **all three sampled-property state arrays** — `animal_property_sampled`, `res_property_sampled`, `obs_property_sampled` — which are what the ulp exemption is actually keyed on and what explains an olfaction difference when one appears. Also capture every entity position array (`res_pos`, `animal_pos`, `obs_pos`), which the Stage 1 placement no-op test compares against.

**Adjudication rule — declared here, before anyone sees a red gate.** `jax_reset` is *not* bit-identical across XLA lowerings: it can differ by up to one float32 ulp on `animal_property_sampled`, and which lowering XLA picks depends on the surrounding graph. Stage 1 adds two leaves to the reset pytree, which changes the graph. `animal_property_sampled` feeds the olfaction slice, so **the gate can go red by 5.96e-8 on olfaction for reasons that are not a regression** — and in the moment, nobody can tell compiler noise from a real leak. The tempting fix is to switch the whole gate to `allclose`, which silently retires the instrument every later "bit-identical" claim rests on.

**Key the exemption on the state arrays, not on the observation.** The measured 1-ulp bound is a property of `animal_property_sampled` — a *state array*. Olfaction is a three-pool weighted sum over several entities' property arrays, so a 1-ulp perturbation spread across several entities can legitimately produce a **2-ulp or larger difference in the observation**. A rule that says "olfaction ≤ 1 ulp, 2 ulp is a regression" therefore fails on a correct implementation, and drops the developer into exactly the in-situ judgement call the rule exists to prevent.

So the rule is fixed in advance, and it is anchored upstream:

- **Exact equality on everything** — reward, drive, `state.key`, `termination_reason`, and every observation slice other than olfaction.
- **The three sampled-property state arrays** — `animal_property_sampled`, `res_property_sampled`, `obs_property_sampled`, all captured in the fixture — must be **exact**, except that each may differ by **≤ 1 ulp on entities whose config declares non-zero `properties_std`**. Where `properties_std` is zero there is nothing to diverge and any difference is a regression.
- **The olfaction slice bound is derived, not asserted.** The test computes its own tolerance from the number of perturbed property elements and the sensor's weights, and states the derivation in a comment. It is a consequence of the bound above, not an independent allowance.
- **Anything outside that is a regression.** Stop and diff; do not widen the tolerance, and in particular do not convert the olfaction bound into a global `allclose`.

Background and the measured bound: [[20260820_1606_reset_ulp_divergence_is_compiler_fusion]] (`docs/llm_wiki/entries/env_entities/`), and the existing precedent for this exemption at `tests/test_trajectory_collection.py:670`. The exemption must be written into the test as an explicit, commented branch keyed on `properties_std`, not as a global tolerance — the difference is that the narrow form still fails when the thing it is guarding against actually happens.

**Backend pinning.** `os.environ.setdefault("JAX_PLATFORMS", "cpu")` at the very top of both the generator and the test, before any `jax` import — the form used at `tests/test_trajectory_collection.py:66`. Fixtures generated on GPU and compared on CPU differ in the last bits and the gate becomes noise.

**Tolerance.** Exact equality (`np.array_equal`), subject only to the one narrow olfaction exception above. The whole point is byte-identity; a general tolerance would let a real perturbation through.

**The test that fails if this stage is wrong.** Not the parity test itself — that trivially passes against fixtures it just generated. The check is a **deliberate-perturbation trial**: apply a one-line throwaway edit that perturbs the satiation observation, confirm `test_thermal_parity.py` goes red on every config, then revert. A harness that stays green under that edit is not a harness.

Use `jnp.nextafter(x, jnp.inf)` — a true 1-ulp bump — or, if a visible constant is preferred, `+1e-3`. **Do not use `+1e-7`**, which was the first draft's suggestion and is wrong: at float32 it is 1–2 ulp near 1.0 and rounds away entirely for values ≥ 2, so on several configs the perturbed run would be bit-identical and the trial would "pass" by proving nothing. Record the observed failure count (expected: every fixtured config) in the Implementation Report.

**Rollback.** Delete the three new paths. Nothing else in the tree has changed.

---

## Stage 1 — Field, campfire, per-entity temperature

**Goal.** The `[H,W]` field exists in state and is built at reset. No observation change, no body change, no reward change. **Byte-identical on the 34 fixtured configs** (the measured guarantee — see F6 for what that does and does not cover).

**Files and functions.**

- `src/environment/state.py`
  - `EnvState`: `thermal_field: jnp.ndarray  # [H,W] float32`. When thermal is off this is allocated `jnp.zeros((0,0))` so the memory cost is nil and any accidental read fails loudly on shape rather than quietly on value.
  - `EnvParams`: `thermal_enabled`, `thermal_use_random_spots`, `thermal_use_object_sources`, `thermal_kernel_radius`, `thermal_spot_count`, `thermal_spot_size` as `struct.field(pytree_node=False)` (static — they gate trace-time branches or fix shapes); `thermal_sigma`, `thermal_spot_temp`, `thermal_default_temp_low/high` as traced floats; `obs_temperature` `[num_obs]`, `obs_temp_ratio_low` / `obs_temp_ratio_high` `[num_obs]`, and the matching `res_temperature` `[num_res]` / `animal_temperature` `[N]`.
- `src/environment/config_loader.py`
  - New `_read_temperature(entry, entity_label) -> tuple[float, float, float]` next to `_read_blocks_sight` (`:330`), returning `(absolute, ratio_low, ratio_high)` and raising when both styles are present.
  - New `_apply_edge_margin(area, margin, h, w, entity_label)` — the F4 load-time inset; raises when the inset rectangle is empty.
  - `min_fire_separation` and `food_min_fire_distance` (D2, D3) read in the same conditional-mandatory `thermal:` block as the rest, each validated `>= 0` with the key named in the message. Both are stored as static ints (`struct.field(pytree_node=False)`) — they bound a rejection loop, so they must be trace-time constants.
- `src/environment/core.py` placement — see **"How the placement constraints actually attach"** below. The earlier draft called this "reject-and-resample"; that is wrong and the correction matters, because building a rejection loop is what would turn the parity gate red for reasons unrelated to thermal.
  - In `load_env_params` (`:1000`), a `thermal:` block placed immediately after the existing occlusion block (`:1053-1066`), following its exact shape: `_thermal_on = bool(config.get_mandatory('thermal.enabled'))`, sub-keys read and validated only inside the `if`, inert non-zero placeholders in the `else`.
  - Per-entity: append to the three existing per-slot list builders exactly where `blocks_sight` is appended and vectorised — animals read at `:862` → array at `:918`; resources read at `:1133` → array at `:1137`; obstacles read at `:1285` → array at `:1289`. Then three new keyword arguments in the single `EnvParams(...)` construction at `:1469+`.
  - Because slots are allocated at `count_high` and each slot is expanded from the same entry dict (`for slot_i in range(hi): expanded_obstacles.append(o)`, `:1235-1241`), the per-slot temperature replicates correctly with no extra work for the count-range feature.

**Config migration — part of this commit, not a follow-up (F6).** Add `thermal: {enabled: false}` to:
- **`configs/environment/default.yaml`** — the full commented `thermal:` key block **and nothing else** (F8: no campfire entry). This one file covers the whole `basic/` level and all 216 layered configs by inheritance; **there are no per-file `basic/` edits**, because all 7 of those files use `extends:`.
- **the 33 other fixtured full configs** (archive 22, verification 6, continual 5) — the two-line gate each. Non-negotiable: they are the instrument the byte-parity claim is measured with, and without the key the existing parity suite raises before Stage 1's gate can run.
- **the ~21 test modules with inline YAML bases** — `tests/env/test_no_recompile.py`, `tests/env/test_directional_sensors.py`, `tests/env/test_per_episode_count.py` and the rest of the `0e8a4ef8` set — plus `tests/fixtures/trajectory_collection/dual_format_config.yaml`. Non-deferrable because they run on every test invocation, not when someone chooses to run them.

**Roughly 55 files.** The remaining **106 non-fixtured full configs are deliberately deferred** by user decision and must **not** be migrated here — see F6 for the policy, why a loud `get_mandatory` failure makes deferral safe, and the coverage this costs. A developer who "helpfully" migrates them has expanded the change by 100 files against an explicit decision. **The `.get('thermal.enabled', False)` route is forbidden** — a fallback default on a gating key is the failure mode the no-fallback rule exists to prevent, and it would let a config with a misspelled `thermal:` block train silently as if thermal were off. Commit `0e8a4ef8` is the precedent for the bulk edit; follow its shape.

**How the placement constraints actually attach (D2, D3).**

`resolve_overlaps_global` (`core.py:845-891`) is **not** reject-and-resample. Its docstring says "single-pass sequential scan", and the body confirms it: one `jax.random.permutation(key, total_cells)` draw up front, then a `lax.scan` that for each entity computes

```python
valid = in_area & (~occ)                                    # core.py:872
valid_in_perm   = valid[global_perm]
first_valid_mask = valid_in_perm & (jnp.cumsum(valid_in_perm) == 1)
replacement_flat = jnp.where(first_valid_mask, global_perm, 0).sum()
```

and deterministically takes the first valid cell in the pre-shuffled order. **Zero per-entity PRNG draws.**

That makes the constraint we need *easier* than the earlier draft implied, not harder — and it is the only formulation that satisfies H10:

> Add the separation constraint as an extra term in the `valid` mask, carrying a **dilated fire-occupancy mask** in the scan carry alongside `occ`. Guard the whole addition behind a **static Python `if min_fire_separation > 0`**, so a disabled config traces the identical graph and draws the identical keys it does today.

A developer who instead writes a rejection loop draws fresh keys per attempt, moves every downstream PRNG stream, and turns the parity gate red across the whole fixture set for a reason that has nothing to do with temperature. That is hazard H10 realised, and it is the single most likely way this stage goes wrong.

**Three consequences that must be built for, not discovered:**

1. **D3's enabled path needs a second pass.** The scan order is `[res, pred, obs, neutral]` (`core.py:1024-1026`), preserved for parity — so **resources are placed before any fire exists in the occupancy mask**. "No food within M of a fire" cannot be a term in the first pass; it needs a second pass over resources after obstacles are placed, also behind a static `if food_min_fire_distance > 0`. The disabled default (`0`) is unaffected and remains a provable no-op.
2. **There is a silent cell-0 fallback.** When no cell satisfies `valid`, `first_valid_mask` is all-False and `replacement_flat` sums to **0** — the entity is parked at cell `(0, 0)`, outside its own `area`, with nothing raised. Tightening `valid` makes infeasible draws *more* likely, so this becomes reachable. The feasibility argument in D2 ("three fires at 3+ apart fit the 6×6 interior") is necessary but **not sufficient**: `default.yaml` also places 6–12 rocks, 4–10 bushes, food and animals into the same occupancy mask. `test_fires_respect_min_separation` must therefore **also assert no fire sits outside its own `area`** — that assertion is what turns a silent (0,0) park into a visible failure.
3. **`per_type` placement mode bypasses `resolve_overlaps_global` entirely** (`core.py:1032-1065` uses `place_in_area` under a `lax.scan` over type groups). Either implement the same masked constraint there, or **raise at load** when `min_fire_separation > 0` or `food_min_fire_distance > 0` under `placement_mode: per_type`. Raising is the honest minimum; silently ignoring the constraint in one placement mode is how a config produces merged fires while its own validation says it cannot.

**Handoff to `bug-curator`:** the silent cell-0 placement fallback (consequence 2) is a pre-existing defect independent of this plan — an entity can already be parked outside its declared spawn area with no error whenever its area fills up. The re-review confirmed no registry row covers it. File it against `resolve_overlaps_global` regardless of whether this plan proceeds.

**Decide the resource and animal temperature arrays now, do not leave them dead.** The design says every entity type carries `temperature`, but only obstacles are stamped in the settled field build. Two acceptable resolutions, and the plan must pick one rather than loading three arrays and reading one:
- **(a)** Stamp resources as well as obstacles (food and hiding predators can then carry heat), and **raise at load if any animal declares a non-zero `temperature`** — animals move, the field is static, so a moving heat source is a promise the mechanism cannot keep.
- **(b)** Load only `obs_temperature`, and raise at load on a `temperature` key appearing on a resource or animal entry.

Recommend **(a)**: it matches the design's "we do not have to decide now" intent for scenery, while the animal check turns the one genuinely wrong configuration into a load error instead of a silently ignored key. Either way, **no dead keys** — a config key that loads and does nothing is how a future reader concludes the feature is broken.
- `src/environment/core.py`
  - New module-level `_build_thermal_field(params, obs_pos, obs_active, obs_temp, key) -> jnp.ndarray` and `_gaussian_smooth_normalised(field, sigma, radius)`.
  - In `jax_reset`, after entity placement and the activation masks are built (after `core.py:~1250`), gated by `if params.thermal_enabled:` — a static Python branch, so a thermal-off config traces the identical graph it does today and draws no extra keys.

**Field build order** (design §1, and the order is load-bearing): fill `default_temp` → random spots (if enabled) → object stamps, **additive** → one weight-normalised Gaussian blur.

Stamps add rather than overwrite. EVAAA assigns (`areaTemp[x,z] = obstacle.temperature`, `ThermoGridSpawner.cs:218`), so its last spawned source silently wins; ours must not, both because two fires making a hotter spot is the physically sensible reading and because assignment makes the result depend on slot iteration order, which puts the parity fixtures at the mercy of that order.

**The test that fails if this stage is wrong.** `tests/env/test_thermal_field.py::test_field_matches_numpy_sandbox` — build the field through `jax_reset` for a fixed seed and a config with one campfire at a known cell, then compare against the numpy sandbox's `gaussian_smooth` applied to the same raw stamps, `np.testing.assert_allclose(..., rtol=1e-5)`.

**Two constraints on the oracle.** `sim.py` hard-codes `H = W = 10` at module level and lives under `docs/`, which is not an import root for the test suite. So either (a) pin this test to a 10×10 grid and say in the docstring that the oracle is dimension-locked, or (b) **vendor a parametrised copy into `tests/env/`** with a comment naming `docs/develop/active/thermal/temperature_system_plan/sim.py` as its source and the requirement that the two stay in step. Prefer (b): it removes the `docs/`-import coupling and lets the edge-renormalisation case be checked on a non-square grid, where a row/column transposition in the kernel would show up and on a 10×10 it cannot.

This is the right test because the sandbox is an **independent oracle**: pure numpy, deliberately written not to import from `src/`, and the thing every calibrated number in the design was computed from. A test that instead re-derived the expected field with the same JAX helper would verify only that the function equals itself.

Three companion cases in the same file:
- **additivity** — two campfires on one cell sum. This one **cannot be set up through `jax_reset`**: `resolve_overlaps_global` (`core.py:845-891`) exists precisely to stop two entities sharing a cell, so the co-location never survives placement. Call `_build_thermal_field` directly with a hand-constructed `obs_pos` instead, and say so in the test's docstring, or the next reader will "fix" it into a reset-based test that quietly stops testing addition.
- **order-independence** — the field is invariant to swapping the two campfires' slot indices (this is what catches a regression to EVAAA's last-writer-wins assignment).
- **edge renormalisation** — a corner fire's blurred value equals the sandbox's, which is where a naive `jnp.convolve` silently differs.

And two placement tests for D2/D3, both of which must sample many resets rather than one, because a constraint that holds on seed 0 and fails on seed 7 is the failure mode here:

- `test_fires_respect_min_separation` — over ~500 resets of the default config, assert **every** pair of active campfires is at least `min_fire_separation` Manhattan cells apart, and that three fires are actually placed (the feasibility claim: 3 fires at 3+ apart fit the 6×6 interior left by `edge_margin: 2`). A sampler that quietly gives up and returns a merged pair would otherwise look like a rare unlucky draw.
- `test_placement_constraints_are_noops_when_disabled` — with `min_fire_separation: 0` and `food_min_fire_distance: 0`, assert `state.key` and `res_pos` / `animal_pos` / `obs_pos` are **identical** to the **Stage 0 thermal-parity fixture** (`tests/env/fixtures/thermal_parity/<slug>.npz`), which is why Stage 0's capture list includes the position arrays. The existing `tests/env/fixtures/parity/` set is the wrong reference here — it captures `obs_pos` but not the full set, and it is the gate this test is meant to be independent of. This is the H10 guard: any implementation that draws a key when it has nothing to reject moves every downstream stream.

And the migration guard, scoped to the lazy policy: **every file in the Stage 1 migration set must load** — `default.yaml`, the 34 fixtured configs, and the ~21 test modules — and the **full test suite must be green**, which is the part the test-module edits exist for. The 106 deferred configs are *expected* to raise `Configuration key 'thermal.enabled' is required`; assert that they do so with that message rather than asserting they load, so the deferral is itself tested and a future silent-default regression is caught (F6).

The thermal-off branch must not have introduced a traced conditional, which is what `test_no_recompile.py` catches.

**Required-green on this stage** (Maintenance Contract §4): `tests/env/test_thermal_parity.py`, **`tests/env/test_unified_parity.py`**, **`tests/env/test_visual_parity.py`**, and `tests/env/test_no_recompile.py`. The two pre-existing parity gates are named explicitly at every stage because the contract binds them to every config-system change, and a plan that lists only its own new gate invites them to be forgotten.

**Rollback.** Revert the commit. `thermal_field` is write-only at this stage (nothing reads it), so removal cannot leave a dangling consumer.

---

## Stage 2 — Body temperature and termination reason 5

**Goal.** `body_temp` updates each step and can end an episode. Not observable, not in the drive. **Still byte-identical on the 34 fixtured configs.**

**Recurrence** (design §5):

```
T ← T + k_exchange·(T_field[agent_cell] − T) + k_metabolic − k_loss·(T − temperature_setpoint)
```

with `k_exchange = 0.04`, `k_loss = 0.01`, `k_metabolic = 0.0`. Death on leaving `[min_temperature, max_temperature] = [−15, +15]`.

**Files and functions.**
- `state.py` — `EnvState.body_temp: jnp.ndarray  # [] float`; `EnvParams` gains `thermal_k_exchange`, `thermal_k_loss`, `thermal_k_metabolic`, `temperature_setpoint`, `min_temperature`, `max_temperature` (traced floats).
- `core.py:55` `update_body` — new block under `if params.thermal_enabled:`, returning `new_body_temp` and folding the out-of-range test into `done`. The function's return tuple widens; its single caller is `core.py:~692`.
- `core.py:702-712` — extend the enum comment to `0: active, 1: max_steps, 2: starvation, 3: overeating, 4: injury, 5: thermal` and add `reason = jnp.where(thermal_death, 5, reason)`.
- `jax_reset` — initialise `body_temp` at `temperature_setpoint`.

**Enum consumers updated in the same commit** (the list in Analysis above is the checklist): the five label-map copies (`train.py:1543,2054,2260,2413`; `dreamer_srl_main.py:1231`), `src/behavior/episode_metrics.py:41-44,196-235,269-272`, `src/utils/trajectory_store.py:140-141,172`, `scripts/analysis/ladder/_ladder.py:90`, `scripts/analysis/studies/nmn_site_grid/grid_ladder_figures.py:150,160,168`, `check_env.py:35` (whose legend is already stale — it omits 0 and 3), and the docs listed in the Maintenance section. `>= 2`-style real-death masks need no edit; confirm that by reading them, do not edit them.

**Where in the ordering.** `reason` is assigned by a `jnp.where` chain, so later assignments win. Thermal death must come **after** the truncation line so a thermal death on the final step reports 5 and not 1, matching how injury already overrides truncation at `:710`.

**The test that fails if this stage is wrong.** `tests/env/test_thermal_body.py::test_equilibrium_and_time_to_death` — hold the agent in a constant-temperature field (a config whose whole grid is one value) and check the trajectory against the closed forms the design derives, which come from the sandbox and not from `core.py`:

- equilibrium `T* = k_ex·T_field / (k_ex + k_loss)` — standing in a −25 cell settles at −20, **not** −25, because physiology holds off 20% of the cold;
- time constant `1/(k_ex + k_loss) = 20` steps;
- steps-to-death in a lethal cell, compared against `sim.body_traj` run with the same constants.

Also `test_thermal_death_reports_reason_5` — drive the agent past +15 and assert `info['termination_reason'] == 5` **and** that `reward` includes the death penalty (i.e. `real_death` is true, not just `done`). The second half is the part that catches the plausible mistake of adding the code without adding the death.

The failure this pair catches that a naive test would not: an implementation that omits the `k_loss` term reads as *working* — the body still tracks the field, still dies in the cold — but it equilibrates at exactly the cell temperature, so the survivable-ambient window collapses to `[−15,+15]` and the entire cold-but-survivable band the design depends on is gone. Only the equilibrium assertion sees that.

The recurrence sits behind a static branch, so nothing observable moves on a thermal-off config.

**Required-green on this stage** (Maintenance Contract §4): `tests/env/test_thermal_parity.py`, **`tests/env/test_unified_parity.py`**, **`tests/env/test_visual_parity.py`**, and `tests/env/test_no_recompile.py`. The two pre-existing parity gates are named explicitly at every stage because the contract binds them to every config-system change, and a plan that lists only its own new gate invites them to be forgotten.

**Rollback.** Revert. `body_temp` is not observed and not in the drive, so the only external surface is the enum — which is why the enum consumers are updated here rather than later: reverting Stage 2 alone must not leave code 5 referenced anywhere.

---

## Stage 3 — Thermoceptor (+5 observation dimensions)

**Goal.** Five new observation dimensions: `field − body_temp` over the von Neumann diamond at `grid_range: 1` — own cell plus four neighbours.

**Files and functions.**
- `sensor.py` — new `sense_thermoception(state, params)` reusing `get_visual_offsets(params.thermal_grid_range)` (`:157-185`). At `r=1` that returns the hardcoded `[[0,0],[-1,0],[0,1],[1,0],[0,-1]]` — centre, up, right, down, left — so the slice order is the project's existing convention and needs no new one. Out-of-bounds cells **clamp** (F3), they do not zero.
- `sensor.py:424` `get_observation` — append after Extero Nociception and before Olfaction, under `if params.thermal_enabled:`.
- `sensor.py:482` `get_observation_breakdown` — `breakdown["Thermoception"] = 2*r²+2*r+1` at the identical position. These two functions must be edited in the same diff; `dreamer_srl_main.py:754-759` and `agent.py:2468-2472` raise if their sums disagree, which is the intended tripwire.
- **`sensor.py:540-608` `build_sensory_viz` — a `Thermoception` branch, plus `else: raise ValueError(...)` at the end of the chain (F7).** This is not optional polish: without it the renderer's slice pointer falls five behind and every later panel draws the wrong data, with nothing raising.
- `src/utils/evaluation_core.py:158-196` — new `_sensor_stat_columns` branch naming the five cells from the offsets, exactly as the `Collision` branch does at `:176-177`.
- `src/environment/config_loader.py:1635-1646` — `"thermoception": "Thermoception"` in `_YAML_KEY_TO_SENSOR_NAME` (F2). Without it the config below raises "unknown perceptual-noise modality key(s)".
- `configs/environment/default.yaml` — a `thermoception:` block under `perceptual_noise.modalities` **with explicit `clip_min` / `clip_max`** derived from the field range (F2). The noise arrays need no widening; they already pad to `max(13, n)` (`config_loader.py:1672`).
- `train.py:796-842` `_modality_fingerprint` and `dreamer_srl_main.py:771-863` — add `thermal_enabled`, `thermal_grid_range` and **`thermal_relative`** to the fingerprint tuple. `thermal_relative` earns its place for the same reason `visual_value_mode` does: it changes what the numbers mean at an identical dimension count, which is exactly what the fingerprint exists to catch. `thermal_sigma` and the rate constants are **excluded**, matching the existing rule that continuous floats are not fingerprinted (`default.yaml:344-349`): fingerprinting a float would forbid legitimate schedules.

**The curriculum hazard, stated precisely.** `train.py:856` tests `obs_dim` and `action_dim` in one condition, **before** the fingerprint check at `:862`, so a curriculum spanning thermal and non-thermal stages is rejected with "changes obs_dim (… → …) … Continual learning forbids architecture-visible dimension changes." This is correct behaviour and must not be relaxed. The consequence to write into the config guide: **a curriculum must be thermal throughout or non-thermal throughout.** A thermal curriculum whose early stages have no fire still declares `thermal.enabled: true` with a neutral field, so the width is constant.

**The test that fails if this stage is wrong.** `tests/env/test_thermoception.py::test_reads_the_five_cells_it_claims` — build a field with a **distinct known value in every cell** (e.g. `field[r,c] = 10*r + c`), place the agent at an interior cell, and assert the five observation values equal `field[agent + offset] − body_temp` for the five offsets, in order. A uniform or symmetric test field cannot distinguish a correct stencil from one that is transposed, rotated, or off by one — and a silently-wrong stencil is the exact failure that cost this project the most time on the visual sensor.

Three companions:

- `test_oob_reads_the_clamped_neighbour` — agent on a corner, assert each out-of-bounds reading **equals the clamped in-grid cell exactly**, using the same distinct-value field. The first draft asserted only that no reading equals `−body_temp`; that is too weak, because the most likely wrong implementation — clamping the *whole coordinate pair* when only one axis is out of range, or wrapping instead of clamping — produces some other in-grid cell's value and passes. Assert the identity, not the absence of one wrong answer.
- `test_breakdown_matches_assembly` — `sum(get_observation_breakdown(params).values()) == get_observation(...).shape[0]` across a thermal-on and a thermal-off config.
- `test_sensory_viz_slices_do_not_shift` — build `build_sensory_viz` output for a thermal-on config and assert the Collision panel's vector equals the collision slice of the observation. This is the F7 tripwire, and it must compare against an independently computed slice offset (from the breakdown) rather than against `build_sensory_viz`'s own pointer, or it re-derives the bug it is checking for.

`test_thermal_parity.py` must be green **on thermal-off configs**; it is silent on thermal-on ones, since there are no thermal-on fixtures by construction.

**Required-green on this stage** (Maintenance Contract §4): `tests/env/test_thermal_parity.py`, **`tests/env/test_unified_parity.py`**, **`tests/env/test_visual_parity.py`**, and `tests/env/test_no_recompile.py`. The two pre-existing parity gates are named explicitly at every stage because the contract binds them to every config-system change, and a plan that lists only its own new gate invites them to be forgotten.

**Rollback.** Revert. Any checkpoint trained after this stage with thermal on has a different `obs_dim` and cannot be restored into the reverted code — orbax restore-to-target fails on shape, which is the desired loud failure. Note it in the Implementation Report if any such checkpoint exists.

---

## Stage 4 — Drive integration (gated)

**Goal.** Temperature becomes the third homeostatic axis. With `thermal.enabled: false`, reward is bit-identical to today's.

**Files and functions.**
- `core.py:49` `calculate_drive` — the F1 form. Signature gains `body_temp=None`; the thermal-off path keeps today's *identical expression*.
- `core.py:~725-735` — the two call sites (`prev_drive`, `curr_drive`) pass `state.body_temp` and `new_body_temp`.
- `core.py` info dict — add `info['drive_thermal']` alongside the existing `drive_hunger` / `drive_injury` (`:723-724`), so the third axis is visible in logs from the first run rather than being reverse-engineered later.
  **State the convention explicitly, because the two nearby quantities disagree.** `drive_hunger` and `drive_injury` are *squared normalised deviations* (`jnp.power(1.0 - satiation/max_satiation, 2)` and `jnp.power(injury/max_injury, 2)`) — diagnostics that are **not** the axes fed to `calculate_drive`, which uses unsquared values in satiation units. `info['drive_thermal']` must follow the **squared-normalised** convention of its two siblings, `jnp.power((body_temp - temperature_setpoint)/max_temperature, 2)`, so the three logged series remain comparable with each other and with every historical run. Say so in a comment at the definition, or the next reader will assume it is the norm axis and compare incommensurable numbers.

**The test that fails if this stage is wrong.** Two, and they test different things.

1. `tests/env/test_thermal_reward_gate.py::test_drive_bit_identical_when_thermal_off` — for every config in the Stage 0 fixture set, assert the per-step reward array equals the **Stage 0 fixture**, exactly. The fixture was generated before `calculate_drive` was touched, so this is a comparison against pre-change ground truth and not against a re-derivation through the same edited function. That distinction is the whole reason Stage 0 exists.
2. `::test_thermal_axis_actually_moves_reward` — thermal on, agent walking from the comfort ring outward into the cold, assert reward is strictly negative on the outward steps and strictly positive on the return. Without this second test, an implementation that gates the thermal axis *off in both branches* passes test 1 perfectly and does nothing.

   **De-confound it.** Satiation falls every step from `metabolic_cost`, so the reward sign on an outward walk is already negative before temperature contributes anything, and the test would pass on a broken implementation. Run it with `with_nutrition: false` so the hunger axis is flat, **or** assert on `info['drive_thermal']` directly rather than on total reward. Asserting on `drive_thermal` is the stronger of the two, because it also fails if the axis is computed but not summed into the norm.

**Rollback.** Revert. Any run started after this stage with thermal on is on a different reward scale and is not comparable with anything before it; that incomparability is permanent and is the reason the gate is mandatory rather than tidy.

---

## Stage 5 — Metabolic coupling

**Goal.** Defending body temperature draws on nutrition. `thermal.metabolic_coupling: false` by default, so this stage changes nothing until it is switched on.

**Files.** `core.py:55` `update_body` — inside the existing `if params.with_nutrition:` block, an additional drain proportional to the defence work `|k_loss·(T − temperature_setpoint)|`, gated by `if params.thermal_metabolic_coupling:` (static).

**Ordering matters and must be pinned.** Nutrition decay, then the thermal drain, then the food refill, then the clip to `[0, max_nutrition]` — because the clip is what decides whether a cold step can starve an agent that also ate this step. Write the chosen order into a comment; it is not recoverable from the config.

**The test that fails if this stage is wrong.** `tests/env/test_metabolic_coupling.py::test_off_by_default_is_a_provable_noop` — run a thermal-on config with coupling off and with the coupling code path present, and assert the nutrition trajectory is **exactly** the trajectory from the same config with coupling off before this stage (a small fixture captured at Stage 4's tip). Then `::test_on_costs_nutrition_in_the_cold` — same config, coupling on, assert nutrition falls strictly faster while the agent stands in a cold cell than while it stands at the setpoint, with the difference matching the closed form `k_loss·|T − setpoint|·coupling_rate` per step.

**Rollback.** Revert. Default-off means no prior run is affected.

---

## Stage 6 — Rendering, the load-time structure check, and documentation

**Goal.** Make the field and the body visible, and make a mis-tuned config fail at load instead of training quietly.

### 6a — Rendering

> **Check the state of the rendering rewrite before starting 6a.** A large rendering update is coming separately, and **this stage may be superseded or absorbed by it**. Whoever picks 6a up should look first rather than build against a renderer that is about to change.
>
> Two things follow. **Keep the thermal drawing additive and self-contained** — a field underlay, a body-temp gauge, a debug read-cell outline — and do **not** restructure the existing panel layout or pointer logic beyond what F7 requires. The point is to avoid entrenching assumptions the rewrite would then have to undo.
>
> **This does not defer F7's `build_sensory_viz` fix.** That is a correctness fix for a silent slice shift, it lands with **Stage 3**, and it is independent of whatever happens to the renderer — a rewritten renderer walking a mis-advanced pointer is wrong in exactly the same way.

All of this lands in **`src/environment/renderer.py`** — the renderer that actually runs. `renderer_v2.py` gets the mirrored change afterwards so the dormant copy does not diverge further; `grid_world.py` gets nothing.

- `renderer.py:425-432` — a diverging blue–red underlay drawn in the same double loop that paints terrain tiles now, at `zorder=0`, so entities (drawn later at `:447-506` via `AnnotationBbox` / `plot`) keep their current stacking untouched. **Colour limits fixed for the whole episode**, computed once from `state.thermal_field` at reset — per-frame rescaling makes a cooling world look stable, which is the one thing the visualisation exists to disprove. A diverging scale is right here because temperature has a meaningful zero: the setpoint the agent is defending.
- `renderer.py:544-606` — the left-panel vitals stack. Add a `COLORS['temperature']` token near `:104-132` and one more `draw_dual_capsule_bar` block after Injury (`:578`) or after Intero Nociception (`:606`), with the ±15 death thresholds marked, adjusting the `bar_step` / `y_ptr` arithmetic at `:552-554` for the extra bar. Without this gauge a video shows the world's temperature but not the agent's, which is the half that matters.
- **`renderer.py:626` — add `'Thermoception'` to `known_sensors`** (currently `['Olfactory', 'Extero Nociception', 'Collision', 'Visual', 'LOC']`), and the same to the `pod_map` copy at `renderer_v2.py:474-479`. Paired with the `build_sensory_viz` branch from Stage 3 (F7); the branch makes the data correct, this makes it visible.
- Debug-only outline of the five thermoceptor cells, off by default.
- Mirror the underlay and gauge into `renderer_v2.py`: underlay at `:338-347`, and a `'temperature'` row added to the left mosaic at `:260-262` plus a fourth `draw_vital_card` call after `:312`.
- `src/utils/eval_recording.py:24-40` `_snapshot_state` — add `thermal_field` and `body_temp`. Its docstring says "Exactly the fields render_jax_state reads. Keep in lockstep with renderer.py", and offline video rendering reads nothing else.
  **Do not bump `RECORDING_FORMAT_VERSION`** (D4). Handle the two fields as **present-or-absent in the reader**: check for them and skip the thermal layer when they are missing, so every pre-thermal `.rec` keeps rendering exactly as it does today. That branch is required either way — a bump would not have removed a line of it — and the stamp it would change is one that nothing reads (F10).

### 6b — The load-time structure check

The design's own §12 asks for this, and it is the difference between a failed experiment and a noticed one: the pain-plus-comfort structure exists only in a narrow band (σ near 0.7, fire 11–13× the world's coldness), and a config drifting outside it silently loses either the fire's bite or the survivable ring while the run still looks healthy.

**Where it lives: `config_loader.load_env_params`, at load, not at reset.** Reset runs under jit on every episode of every parallel environment; a Python-side profile simulation cannot run there, and a traced version would be a per-episode cost for a check whose inputs are all config constants. Everything the check needs — σ, the `default_temp` range, the ratio range, `k_exchange`, `k_loss`, `k_metabolic`, the setpoint, the death thresholds — is known at load.

**When it runs — and this is the correction that keeps the earlier stages testable.** The first draft ran the check whenever `thermal.enabled`, which would have made every thermal config from Stages 2 through 5 refuse to load: Stage 2's uniform-field config, Stage 3's distinct-value stencil config, Stage 4's gate configs and Stage 5's coupling fixture are all thermal-on and *deliberately* lack the pain-plus-comfort structure. That would have broken the plan's own promise that each stage reverts independently. Mode A (`use_random_spots: true, use_object_sources: false`) has no fire to check at all.

So the gate is:

> Run the structure check **iff** `use_object_sources` is true **and** the config declares at least one **heat source**. Otherwise log one line saying the check was skipped and why, and continue.

**"Heat source" is defined once and used everywhere.** A heat source is *an allocated entity slot whose `temperature` or `temperature_ratio` is non-zero* — a per-slot property, evaluated after `count_high` expansion. Define it as a single helper in `config_loader.py` and call it from both the placement constraints and this check. The obvious wrong reading is "an entry with `count_high > 1`", which lets **two separate single-count fire entries** slip past as "only one fire" when they can in fact spawn adjacent. Counting slots, not entries, is what closes that.

The Stage 2–5 test configs are marked "no heat source" in a comment, which is both what makes them load and what tells the next reader they are not meant to be realistic worlds.

**What it does.** For the corners of the sampled ranges (`default_temp` low/high × `temperature_ratio` low/high, four draws, plus the midpoint), it builds a single-fire field, computes the equilibrium body temperature at Manhattan distances 0, 1 and 3, and asserts the three-part structure: **distance 0 exceeds the death threshold** (the fire hurts), **distance 1 is survivable indefinitely** (the comfort ring exists), **distance 3 is lethal** (the cold is a real clock). This mirrors `structure_ok` in `build_page.py`.

Two corrections to how it computes, both of which change the verdict on real configs:

- **Use the general equilibrium**, not the setpoint-zero special case: `T* = (k_ex·T_field + k_loss·setpoint + k_metabolic) / (k_ex + k_loss)`. `temperature_setpoint` and `k_metabolic` are both config keys with non-zero-capable values; the first draft's `k_ex·T_field/(k_ex + k_loss)` is only correct when both are zero, and with either set it will pass a lethal comfort ring or reject a perfectly good one.
- **Call the same blur the reset path calls**, not a numpy re-implementation. A numpy twin validates a field the environment never builds — the exact circular-verification shape this plan is meant to avoid — and it will drift the first time the kernel is touched. Factor `_gaussian_smooth_normalised` so it is callable on host arrays outside jit, and have both the check and `jax_reset` go through it.

**On failure: raise `ValueError`.** Not a warning. A warning is what the sigma-floor incident produced, and it trained silently for a full run. The message must name the key, the drawn value, the three distances' equilibria, and which of the three conditions failed — enough that the reader can retune without opening this document.

Sampling corners rather than the true distribution is deliberate: the check must be deterministic, so that a config either always loads or never does. A random-sample check that passes on Monday and fails on Tuesday is worse than none.

**The single-fire calibration gap is closed by `min_fire_separation` (D2), not by this check.** `structure_ok` in the design sandbox models one fire, and the proposed default is `count_high: 3`; adjacent fires add their stamps and the merged d = 1 ring is lethal (+33.0 at separation 1, +15.4 at separation 2, against a +15 threshold). Rather than widening the check to a worst case that placement now forbids, the constraint is enforced where it belongs — at spawn. With `min_fire_separation: 3` every fire's ring sits at +8.4, within noise of the +8.1 single-fire reference, so **the single-fire check is valid for multi-fire worlds** and the design's "100% structure holds" figure carries over unchanged.

The check must therefore **read `min_fire_separation` and refuse to certify a config that disables it** (`0`) while allowing more than one fire: that combination reintroduces the merged-ring case the single-fire model cannot see. Raise, naming both keys, rather than silently certifying a world the check does not actually cover.

Unconditional validations in the same block: `thermal.sigma > 0`, `min_temperature < max_temperature`, `grid_range >= 0`, `k_exchange > 0`, `k_loss >= 0`, and `edge_margin` yielding a non-empty spawn rectangle.

### 6c — Documentation (Maintenance Contract)

Per the Maintenance Contract in `docs/environment/CONFIG_GUIDE.md:338-350`, a schema change must, **in the same change**: update `configs/environment/default.yaml` with explicit values and inline comments; update **both** `CONFIG_GUIDE.md` and `docs/environment/02_config_schema.md`; add tests proving a missing/invalid mandatory value raises; and keep the parity gate green.

**The contract is per-change, so this table is split by stage.** Batching four schema-adding stages (1, 2, 3, 5) into a single documentation commit at Stage 6 would violate the contract four times over and leave the schema doc wrong for the whole window in between — the exact drift the contract exists to prevent. Stage 6's own row covers only the rendering and validation work it introduces.

| Stage | Document | What changes |
|---|---|---|
| **0** | `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` | The new fixture generator under `scripts/fixtures/` |
| **1** | `docs/environment/CONFIG_GUIDE.md` | New feature section for the `thermal:` field keys, following §3.8's shape for directional sensors; the conditional-mandatory note in §5; a note that the migration added the gate to every config |
| **1** | `docs/environment/02_config_schema.md` | `thermal:` field keys with types and validation; the new obstacle fields in Obstacle Entity Fields (`:922`); `edge_margin` as a load-time area inset; **`min_fire_separation` and `food_min_fire_distance`** with their `>= 0` validation and disabled-at-`0` semantics; mandatory-key reference (`:983`) |
| **1** | `docs/environment/CONFIG_GUIDE.md` | **The D2 separation table** (+33.0 / +15.4 / +8.4 against the +15 threshold) and the feasibility note that 3 fires at 3+ apart fit the 6×6 interior — so nobody "fixes" a non-existent placement failure by lowering it; the D3 risk that food in the comfort ring removes the trade-off |
| **1** | `docs/environment/CONFIG_CRITICAL_SETTINGS.md` | Registry rows for `thermal.enabled`, `thermal.sigma`, **`thermal.min_fire_separation`** (below 3 the comfort ring goes lethal on merged draws) + dated change-log entry |
| **2** | `docs/environment/05_body_homeostasis.md` | The `T` recurrence, the two constants, the tug-of-war reading |
| **2** | `docs/environment/06_reward_and_termination.md` | Termination code 5 |
| **2** | `docs/environment/04_step_loop.md` | The "Code 0–4" table at `:944` becomes 0–5 |
| **2** | `docs/environment/TRAJECTORY_STORE_SCHEMA.md` | Code 5 in the enum at `:66,177` |
| **2** | `docs/develop/active/behavior/WANDB_METRICS_REFERENCE.md`, `.../TRAJECTORY_COLLECTION_PIPELINE.md` | `Episode/Term_Thermal`; code 5 at `:260` |
| **2** | `docs/environment/CONFIG_CRITICAL_SETTINGS.md` | Registry row for `thermal.k_loss` (the ceiling above which the task quietly disappears) + change-log entry |
| **3** | `docs/environment/02_config_schema.md` | `Thermoception` in the breakdown/slice tables; the OOB-clamp departure from the zero-fill convention (F3); the noise-modality key and its explicit clip bounds |
| **3** | `docs/environment/CONFIG_GUIDE.md` | The curriculum rule — thermal throughout or not at all |
| **3** | `docs/environment/CONFIG_CRITICAL_SETTINGS.md` | Registry rows for `thermal.grid_range`, `thermal.relative` + change-log entry |
| **4** | `docs/environment/06_reward_and_termination.md`, `CONFIG_GUIDE.md` | The three-axis drive and the warmth/hunger exchange rate from F1 |
| **5** | `docs/environment/05_body_homeostasis.md`, `02_config_schema.md` | `metabolic_coupling` and the pinned update ordering |
| **6** | `docs/environment/02_config_schema.md`, `CONFIG_GUIDE.md` | The load-time structure check: when it runs, when it is skipped, and what its message means |

**The test that fails if this stage is wrong.** For 6b, `tests/env/test_thermal_validation.py` — a table of configs that must each raise `ValueError` with a message naming the offending key: `sigma: 0.0`; `min_temperature: 15.0` with `max_temperature: -15.0`; `temperature_ratio: [3, 4]` (fire too weak — no pain at distance 0); `temperature_ratio: [25, 30]` (fire too strong — the comfort ring at distance 1 is lethal); `sigma: 1.5` (blurred flat — no pain anywhere); `edge_margin: 5` on a 10×10 grid (empty spawn rectangle); a campfire entry declaring both `temperature` and `temperature_ratio`; `min_fire_separation: -1` and `food_min_fire_distance: -1` (each must name its own key); and `min_fire_separation: 0` together with `count_high: 3` (the merged-ring case the single-fire check cannot certify — must name both keys). Each case asserts on the message text, not merely that something raised — a `ValueError` from an unrelated line would otherwise pass.

And the matching negative cases, which are what stop 6b from breaking the earlier stages: **the Stage 2, 3, 4 and 5 test configs must all still load**, plus a mode-A config (`use_random_spots: true, use_object_sources: false`) and a thermal-on config whose entities all sit at `temperature: 0.0`. A structure check that rejects any of these is over-broad, and the failure would surface as four earlier stages becoming unrunnable — which is why they are asserted here rather than discovered later.

Two more: `test_general_equilibrium_used` — a config with `temperature_setpoint: 5.0` whose ring is survivable under the general formula but lethal under the setpoint-zero one must **load**; and `test_check_uses_the_reset_blur` — assert the check's field equals the field `jax_reset` builds. **This needs a degenerate config to be well-posed**: the check evaluates the *corners of the sampled ranges* while `jax_reset` draws *one sample*, so on a normal config the two are comparing different worlds and the test cannot pass as an equality. Use a config with single-valued ranges (`default_temp: [-25, -25]`, `temperature_ratio: [12, 12]`, `count_low: 1, count_high: 1`) and one fire pinned to a fixed cell — then the corner, the midpoint and the drawn sample are all the same field, and equality is meaningful.

For 6a the check is a rendered frame, not a static read: render one thermal episode and have `artifact-format-reviewer` (or a human) look at the image. Reading the renderer source is how a page shipped with three lists rendering one word per line after two careful reviews; a colour scale that inverts or a gauge that clips is not visible in the code.

**Rollback.** Rendering and docs revert independently of 6b. Reverting 6b alone re-opens the silent-misconfiguration hole, so if only part of this stage is rolled back, keep the validation.

---

## Hazard register

| # | Hazard | Where it bites | Mitigation | Stage |
|---|---|---|---|---|
| H1 | Design's normalised drive rescales all rewards by 1/100 | `core.py:49` | Build the algebraically identical form in today's units (F1); Stage 0 fixture proves it | 4 |
| H2 | +5 obs dims rejected by the curriculum check | `train.py:856` (tested **first**, before the fingerprint at `:862`); `dreamer_srl_main.py:844` | Documented rule: a curriculum is thermal throughout or not at all; fingerprint gains `thermal_enabled`, `thermal_grid_range` **and `thermal_relative`** | 3 |
| H3 | Reward incomparable with all past runs once thermal enters the drive | every WandB history | Gate must be the *identical expression*, not a numerically equal one; proven against pre-change fixtures | 0, 4 |
| H4 | New modality → `KeyError` in `apply_perceptual_noise`, plus two hard-fail consumers | `sensor.py:394`; `evaluation_core.py:188`; `agent.py:2468` | Modality block + `_YAML_KEY_TO_SENSOR_NAME` entry + stats-column branch + `build_sensory_viz` branch, all in one commit (F2, F7). **The noise arrays need no widening** — they already pad to `max(13, n)` | 3 |
| H5 | Unvalidated `sigma` → all-NaN observation that trains silently (this has happened) | `config_loader.py` | `sigma > 0` and `min < max` validated at load, in the conditional-mandatory block | 1, 6 |
| H6 | Config drifts out of the narrow pain-plus-comfort band; run looks healthy, trains a different task | any thermal config | Load-time simulated radial-profile check over the range corners; **raises**, never warns (6b) | 6 |
| H7 | `termination_reason` 0–4 assumed by six label maps and two analysis paths | `train.py` ×4, `dreamer_srl_main.py:1231`, `episode_metrics.py`, `_ladder.py:90`, `grid_ladder_figures.py:168` (hard `SystemExit`) | All updated in the Stage 2 commit; `>= 2` death masks verified as already correct | 2 |
| H8 | Campfire in a corner wastes its warm zone; episode difficulty swings for a non-configured reason | spawn sampling | `edge_margin` applied as a load-time inset of the existing `area` (F4) | 1 |
| H9 | Sampled counts creating shape-varying arrays under jit | `jax_reset` | Existing `count_high` allocation + `obs_active` mask (`core.py:1195-1237`); scatter-add for stamps; static kernel radius | 1 |
| H10 | A new `split` at reset renumbers every downstream PRNG stream | `jax_reset:964` | Every new draw via `jax.random.fold_in` with a fresh constant; never widen a split | 1 |
| H11 | OOB thermoceptor cells reading zero look like "same temperature as me" | `sensor.py` | Edge-clamp the coordinate; document the departure from the zero-fill convention (F3) | 3 |
| H12 | Offline video rendering breaks on the new state fields | `eval_recording.py:24-40` | Snapshot updated in lockstep; format-version bump is an open decision | 6 |
| H13 | Existing Parquet stores hold `int8` termination codes under the old enum | `trajectory_store.py:140,172` | Code 5 fits int8; docstring enum updated; old stores remain valid, no migration | 2 |
| H14 | Byte-parity gate goes red on 1 ulp of compiler noise; the tempting fix retires the gate | `jax_reset` lowering; olfaction slice | Adjudication rule pre-declared in Stage 0: exact everywhere, ≤1 ulp on olfaction only where `properties_std` is non-zero, everything else a regression | 0 |
| H15 | New modality silently shifts every later renderer panel — no exception, wrong videos | `sensor.py:540-608` (no terminal `else`); `renderer.py:626`; `renderer_v2.py:474` | `Thermoception` branch + `else: raise` in the same diff; pod lists updated; slice-offset test | 3, 6 |
| H16 | Conditional-mandatory gate with no config declaring it makes full configs + ~21 test modules unloadable | `get_mandatory('thermal.enabled')`; `Config` does not resolve `extends:` | Lazy migration in the Stage 1 commit — `default.yaml` + 34 fixtured + ~21 test modules (~55 files); 106 deferred by user decision and expected to raise a *named* error; `.get(..., False)` explicitly forbidden, since it is what would make deferral unsafe | 1 |
| H17 | Load-time structure check rejects the Stage 2–5 test configs and mode A | `config_loader` | Check gated on `use_object_sources` **and** a non-zero declared temperature; negative cases asserted in the validation test | 6 |
| H18 | Noise clips at ±100 while the fire-cell relative reading is ≈ +300 | `config_loader.py:1688-1697` defaults | Explicit `clip_min`/`clip_max` in the `thermoception:` block, derived from the field range | 3 |

---

## Decisions settled by the user — 2026-09-08

Three questions the first draft left open came back decided. They are recorded here with their reasoning, because each one is the kind of choice that looks arbitrary a year later.

### D1 — The campfire shares obstacle visual channel 6

**Decided: keep the default.** The campfire is visually indistinguishable from a rock and a bush, and **thermoception is the only way to locate a fire**. `visual_vector_size` stays 8, there is no observation cost, and the modality fingerprint is unaffected.

Two reasons this is the right call rather than a compromise. First, it is consistent with what the environment already does: bush and rock *already* share channel 6 (`_read_visual_properties(o, 6, ...)`, `config_loader.py:1282`), so the campfire is not being singled out — a config that wanted per-obstacle visual identity would have to give one to bush and rock too, which is a separate change. Second, it is the whole point of adding the sense. A fire on its own visual channel would let a vision-equipped agent solve the thermal task without ever using the thermoceptor, and the experiment would measure navigation rather than thermoregulation.

**Why this is not cruel to the agent.** The obvious objection is that if fires look like rocks, identifying one costs a 3-step burn. It does not: `d = 1` is the comfort ring, the safest and best-rewarded cell in the world. The agent can stand *next to* any unidentified obstacle and read the thermoceptor, which reports a large positive value beside a fire and roughly zero beside a rock. Identification is free and survivable; the agent never has to gamble a lethal step to find out what it is looking at. This is a real property of the field geometry, not an assumption — it is the same `d = 1` result the design's radial profile is built on.

### D2 — Fire separation is a config key, `min_fire_separation: 3`

**Decided: configurable, defaulting to the measured threshold.** Adjacent fires add their stamps, and the merged field is lethal exactly where the agent needs to stand. Measured at σ 0.7, campfire 300, world −25:

| Manhattan separation between two fires | Comfort-ring (d = 1) equilibrium | Verdict |
|---|---|---|
| 1 | **+33.0** | past the +15 death threshold — ring is lethal |
| 2 | **+15.4** | past the threshold — ring is lethal |
| **3** | **+8.4** | intact, and matches the single-fire reference of +8.1 |
| single fire (reference) | +8.1 | — |

So a two-fire draw at separation 1 or 2 produces an episode with **no survivable position near the fire at all** — the agent's only options are to burn or to freeze. Three is the measured threshold, and it is the default. `0` is documented as "disabled — accepts merged fires", for anyone who wants to study that regime deliberately.

**Enforcement: an extra term in the existing placement validity mask** — `resolve_overlaps_global` is a single-pass deterministic scan over one pre-shuffled permutation, not a rejection loop, so this is a tightening of the existing `valid = in_area & (~occ)` test from "distance ≥ 1" to "distance ≥ `min_fire_separation`" among fires. Mechanism, the second pass D3 needs, and the silent cell-0 fallback are all detailed in Stage 1, "How the placement constraints actually attach".

**Feasibility.** `edge_margin: 2` leaves a 6×6 interior on a 10×10 grid. Three fires each 3 or more apart fit comfortably there (corners and a centre cell alone satisfy it), so the default is not at risk of exhausting the sampler. State this in the config guide so nobody "fixes" a non-existent placement failure by lowering the separation.

**This also closes the review's Medium finding about single-fire calibration.** `structure_ok` in the design sandbox scores one fire, while `count_high: 3` permits adjacency it never scored — that gap is what made the "structure holds in 100% of draws" figure narrower than it appeared. **With `min_fire_separation: 3` enforced, the figure becomes true for multi-fire draws too**, because every fire's d = 1 ring is then at its single-fire value. The guarantee is no longer per-fire with a caveat; it holds for the world.

### D3 — Food placement is a config key, `food_min_fire_distance: 0` (off by default)

**Decided: build the knob, leave it off, and measure before using it.** With the constraint at `0`, food spawns anywhere — exactly today's behaviour — and the user wants evidence on how often food actually lands near a fire before forcing the trade-off.

**The risk, recorded plainly so it is not forgotten.** An episode whose food spawns inside the comfort ring has **no thermal trade-off at all**. A stationary policy — sit on the ring, eat, stay warm — is optimal there, and that episode teaches the agent nothing about thermoregulation while still counting as a thermal episode in every metric. If such episodes are common, the aggregate results will understate the task's difficulty and the thermoceptor will look less useful than it is.

**The measurement that settles it**, to run before the first real training run: over ~600 sampled resets of the proposed default config, report **the share of episodes with at least one food item within the comfort ring** (Manhattan distance ≤ 1 of any fire), and the share with all food beyond it. That is a sandbox-or-reset-loop measurement, cheap, and it turns a reopened debate into a number. Belongs to `experiment-designer`.

### D4 — Do not bump `RECORDING_FORMAT_VERSION`; handle the fields as present-or-absent

**Decided: no bump.** The renderer checks for `thermal_field` and `body_temp` and skips the thermal layer when they are absent, so pre-thermal recordings render unchanged.

The grounding matters, because it changes *why* this is right rather than merely permitted. `RECORDING_FORMAT_VERSION` is written at `eval_recording.py:65` and `:82` into every `.rec` payload and every `run_meta.pkl` — and **nothing anywhere reads it back**. Not the renderer, not `async_render.py`, not `evaluation_core.py`, not `dreamer_srl/eval.py`, not the behaviour-measure scripts (verified by grep). So bumping it would change a number no code consults, while the actual work — a reader that copes with older recordings — has to be done either way. The bump buys nothing and costs a permission round-trip.

### D5 — Keep `topic: sensors`; do not touch the topic enum

**Decided: leave it.** This document lives in `docs/develop/active/thermal/` while declaring `topic: sensors`. The index validates the *enum*, not the folder name, so regeneration passes — and the arrangement follows existing precedent rather than inventing one: `dreamer_srl_v1/`, `dreamer_srl_v2/` and `sheeprl_bridge/` are all directories under `docs/develop/active/` whose names are not in `VALID_TOPICS`. **Do not edit `scripts/claude/regen_dev_index.py` or `FRONTMATTER_CONTRACT.md`.**

One observation, handed on rather than actioned here: `env_entities` is present in the script's `VALID_TOPICS` but missing from the topic list in `FRONTMATTER_CONTRACT.md`. That is a pre-existing drift between the validator and the contract that documents it. It belongs to whoever owns that doc; it is **not** an open item on this plan.

### D6 — Combination B, and the design now agrees

**Decided and no longer a divergence.** The plan recommended combination B — `count_low: 1, count_high: 3`, `temperature_ratio: [11, 13]`, `default_temp: [-28, -22]` — which holds the pain-plus-comfort structure in 100% of 600 sampled draws. The design page previously showed a wider `[-30, -20]` in its §9 example block; **that block has since been corrected to `[-28, -22]`**, so the design and the plan now say the same thing.

For the record, the wider range was **looser, not wrong**: `[-30, -20]` measures at 98%, so roughly one draw in fifty would have produced an episode missing either the fire's bite or the survivable ring. B is chosen because 100% means every episode trains the task that was specified.

---

## Open decisions

Nothing here requires a user decision. One item remains, and it is evidence to collect rather than a call to make:

1. **The comfort-ring food measurement** (from D3): over ~600 sampled resets of the proposed default config, the share of episodes with at least one food item within Manhattan 1 of any fire. It has to run before the first real training run, and it belongs to `experiment-designer`. Listed here so it does not fall between this plan and the experiment design.

Everything the first draft listed as open is now settled — see *Decisions settled by the user*.

---

## Checkpoints for the implementing agent

- [x] **S0** Fixtures generated on the pre-change tip, on CPU; the perturbation trial turned the gate red on **72 of 72** fixtured configs, and the revert turned it green again. `collect_configs` total **356**, fixtures written **72** (not 34 — see Deviation D0-1). Done 2026-09-08.
- [x] **S0** The adjudication rule is a commented `properties_std`-keyed branch at `tests/env/test_thermal_parity.py:265-289` (two asserts: exact where std == 0, <= 1 ulp where std != 0). The olfaction bound is derived in `_olfaction_tolerance` and is exactly `0.0` on 29 of the 71 olfaction-carrying configs. Done 2026-09-08.
- [x] **S1** The migration set loads — `default.yaml` + the **72** fixtured full configs (not 34; see Stage 0's deviation D0-1) + 20 test modules/fixtures. Load loop run **before** the parity gate: 72/72 loaded, 0 failures. Done 2026-09-08.
- [x] **S1** The deferred set is **68** configs, not 106 (140 full − 72 fixtured). **55** raise `Strict Config: Configuration key 'thermal.enabled' is required but missing.`; the other **13** raise earlier on the pre-existing `sensory.visual_value_mode` gap (F9). **Zero load.** Three spot-checked by hand. Finding: the 68 deferred configs are *exactly* the 68 that already fail for want of `sensory.injury_observable` — thermal adds no newly-broken config. Done 2026-09-08.
- [x] **S1** 101 files touched (102 with this plan doc): 72 configs (default + 71 fixtured), 20 test modules/fixtures, 3 `src/` files, 3 Maintenance-Contract docs, plus 3 new files (the thermal example config and two new test modules). Re-derived from 72 fixtures rather than 34, per D0-1 — the ~55 estimate was keyed to the stale count. No deferred config touched. Done 2026-09-08.
- [x] **S1** `default.yaml`'s `obstacles:` list parses identically before and after (3 entries: rock, tree, bush). The campfire lives in the new `configs/environment/experiment/thermal/campfire_world.yaml`. Done 2026-09-08.
- [ ] **S3** Render one frame with thermal on and check the Collision panel against the observation slice by hand. `build_sensory_viz` fails silently (F7); nothing else in the suite will tell you.
- [x] **S1** Asserted, not eyeballed: `test_placement_constraints_are_noops_when_disabled` compares `state.key` (plus all three position arrays) against the Stage 0 fixture, for thermal OFF *and* thermal ON with both constraints at 0. The 72-config parity gate additionally compares `state.key` at all 101 states. Done 2026-09-08.
- [x] **S1** One campfire at (3,2), `default_temp: [-25,-25]`, absolute `temperature: 300`: peak `+72.42`, d=1 ring `[+10.12, +10.12, +10.46, +10.11]`, far corner `-25.00`. Sandbox `gaussian_smooth` on the same raw stamps prints the identical numbers. Done 2026-09-08, before the test was written.
- [ ] **S2** Confirm `body_temp` equilibrates at −20 (not −25) in a uniform −25 field. If it equilibrates at −25, `k_loss` is not wired in.
- [ ] **S2** `grep -rn "termination_reason"` and tick off every consumer in the Analysis table before committing.
- [ ] **S3** `sum(get_observation_breakdown(params).values()) == get_observation(...).shape[0]` on both a thermal-on and a thermal-off config, printed, before running the suite.
- [ ] **S4** Diff `calculate_drive`'s thermal-off branch against the original character by character — it must be the same expression, not an equivalent one.
- [ ] **S6** Load every config in the Stage 1 migration set and confirm none newly raises. The structure check must be unreachable when `thermal.enabled` is false. (Deferred configs are expected to raise on `thermal.enabled` — that is the policy, not a failure; do not "fix" them here.)
- [ ] **Every stage** Record before/after steps-per-second on the same node, GPU and seed. The field build is once per episode and the recurrence is three multiply-adds per step, so a measurable slowdown means something landed in the wrong loop. Per the verification protocol, >5% warrants discussion and >15% blocks.

---

## Implementation Report

> **Implemented by**: `developer`
> **Date**: 2026-09-08

<!-- Filled by the `developer` agent. Per stage: what was done, deviations and why,
     the speed measurement, and the deliberate-perturbation result for Stage 0. -->

### Stage 0 — Parity harness (complete)

**Plain-language summary.** Before any temperature code exists, this stage recorded what the
environment currently *does* — what the agent sees, what reward it gets, and how far from
comfortable it is — for every config that runs, and committed that recording. Later stages
promise not to change any of it; this recording is what turns that promise into something a
test can check.

**Files.**

| File | Change |
|---|---|
| `scripts/fixtures/generate_thermal_parity_fixtures.py` | **New.** Hand-run generator. `config_slug` and `collect_configs` copied verbatim from `generate_parity_fixtures.py:36-52` so both fixture sets key on identical slugs. `ACTIONS = [0,1,2,3,4]*20`, `SEED = 0`, `os.environ.setdefault("JAX_PLATFORMS", "cpu")` before any jax import. |
| `tests/env/test_thermal_parity.py` | **New.** The gate. Same backend pinning, same `collect_configs`; configs without an `.npz` are skipped. |
| `tests/env/fixtures/thermal_parity/*.npz` | **New.** 72 fixtures, 848 KB total. |
| `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` | Per-file roll-up (§3) gains a row for the new script, in the same change, per that map's Maintenance Contract. |

Nothing under `src/` or `configs/` was touched.

**What is captured**, per config, over the reset state plus 100 steps: the full observation with
`apply_noise=False`; the same with noise on; the scalar `reward`; `done`;
`calculate_drive(state.satiation, state.injury_level, params)` before and after each step;
`info['termination_reason']`; `sum(get_observation_breakdown(params).values())`; the observation
dimension; `state.key` (the PRNG-stream tripwire); all three sampled-property arrays; and all
three entity position arrays. Each field is stored as one array stacked over steps rather than
one array per step — same content, ~19 arrays per `.npz` instead of ~1,300.

**The two config counts, not conflated.**

| Quantity | Count |
|---|---|
| Configs `collect_configs()` returns (the set the gate walks) | **356** |
| Configs that produced a fixture (the set the gate adjudicates) | **72** |
| Skipped — `load_env_params` raised | **284** |
| Skipped — episode raised | **0** |

**Deviation D0-1 — the plan's "34 fixtured configs" is stale, and the real number is 72.**
The plan states in three places (Stage 0 scope, F6, "The honest coverage statement") that 34
configs carry a committed fixture, and derives the migration policy's non-negotiable group (b)
from that number. 34 is the size of the **pre-existing** `tests/env/fixtures/parity/` set, which
was generated at the CP1 commit and has not been regenerated since. Re-running the same
`collect_configs` today, **72 configs load and run**. The new set is a strict superset: all 34
old slugs are present, plus 38 more, all under `configs/environment/experiment/`. Consequence
for later stages: Stage 1's non-deferrable fixtured group is **72 configs, not 34**, and the
coverage statement is **72 of 356 (20%)**, not "34 of 356 (under 10%)". `senior-developer`
should re-check F6's ~55-file migration estimate against 72 before Stage 1 starts. Flagged, not
worked around.

**The adjudication rule as implemented.** Exact equality (`np.array_equal`) on `key`, `reward`,
`done`, `termination_reason`, `drive_before`, `drive_after`, `res_pos`, `animal_pos`, `obs_pos`,
the breakdown total and the observation dimension. The three sampled-property state arrays get
the one exemption, written as an explicit two-branch check: where `properties_std == 0` any
difference at all fails; where it is non-zero the difference must not exceed one float32 ulp at
that element's magnitude. The observation is exact outside the Olfaction slice; inside it, the
tolerance is **derived**, per element, and the derivation is in the `_olfaction_tolerance`
docstring:

> `obs[cell, v] = SUM_e prop[e, v] * w(dist) * mask`, so
> `|d obs[cell, v]| <= (SUM_e ulp32(prop[e, v]) * [std[e, v] != 0]) * w_max`, with
> `w_max = max(2 ** decay_power, 1.0)` — the largest weight `sense_resource` can emit
> (`1 / 0.5**p` when the agent stands on the entity; `< 1` at any other integer-grid cell).

Measured over the 72 fixtures: 71 carry an Olfaction slice; the derived tolerance is **exactly
0.0 on 29 of them** (no entity declares a non-zero `properties_std`, so the check is strict
equality) and ranges **2.38e-07 to 7.15e-07** on the other 42. It is never a global `allclose`
and it is never a typed-in constant. The same array bounds the noisy observation, because
`apply_perceptual_noise` adds a noise term drawn from `fold_in(state.key, 999)` — and `state.key`
is asserted exactly equal — then applies a monotone clip.

**The deliberate-perturbation trial (the check that this stage is not vacuous).**

| Step | Command | Result |
|---|---|---|
| Baseline | `pytest tests/env/test_thermal_parity.py -q` | **72 passed, 284 skipped** (148 s) |
| Perturbed — `sensor.py:440` satiation obs `+ 1e-3` | same | **72 failed, 284 skipped** (150 s) |
| Reverted (`git checkout -- src/environment/sensor.py`) | same | **72 passed, 284 skipped** (148 s) |

Red on **every** fixtured config, as expected — `Satiation` is unconditional in
`get_observation_breakdown`, and it sits before the Olfaction slice, so the failure lands on the
"differs OUTSIDE the Olfaction slice" assert rather than on the exempted branch. `+1e-3` was used
rather than the rejected `+1e-7` for the reason the plan gives: at float32, `1e-7` rounds away
entirely for values >= 2 and the trial would prove nothing.

**Speed check: skipped, and why.** Stage 0 adds no code to `src/` — it is a new hand-run script,
a new test, new fixture data, and one doc row. Nothing on the env-step, model or observation hot
path changed, so there is no before/after to measure. (`git status --porcelain src/` is clean.)

**Prior-art pass.** `grep -in` over `docs/develop/active/issues/KNOWN_BUGS.md` for `parity`,
`ulp`, `fixture`, `thermal`. Two rows are relevant and both were read: **line 125** — the reset
ulp divergence, already adjudicated *NOT A BUG — documented compiler behaviour (do not
re-escalate)*, which is exactly the exemption this test encodes; and **line 159** — the 2026-08-20
stale-`observability_gates` fixtures, FIXED by regenerating four snapshots and closing with "the
gate is now 34 passed". That row is where the plan's 34 comes from, and it confirms 34 is the
current size of the *old* set rather than the number of configs that can be fixtured today.
Nothing in the registry covers **D0-1** (the old `tests/env/fixtures/parity/` set never grew to
cover the 38 configs that have since become loadable, so it under-reports the gate's reachable
coverage by more than half). That is a candidate registry row; per the developer profile I name
`bug-curator` as its owner rather than filing it myself. No `thermal` row exists.

**Blockers / follow-ups.**
1. D0-1 above — Stage 1's scope numbers need re-deriving from 72, not 34.
2. Not committed, per instruction. Working tree left dirty for verification.

Signed: `Implemented by: developer`

### Stage 1 — Field, campfire, per-entity temperature (complete)

**Plain-language summary.** The world now has a temperature map. At the start of every
episode the environment fills a 10x10 grid with a cold baseline, adds each campfire's
heat on top of whatever is already in that cell, blurs the result once, and stores it on
the episode state. **Nothing reads it yet** — the agent cannot sense it, it does not
change the body, and it does not change the reward. Two new placement rules ship with it:
fires cannot spawn on top of each other, and (off by default) food can be pushed away
from fires. When the temperature system is switched off — which is every config in the
project except the one new example — the environment is byte-for-byte what it was before
this change, and the Stage 0 recording is what proves it.

**Files changed.**

| File | Change |
|---|---|
| `src/environment/state.py` | `EnvState` gains `thermal_field` (`[H,W]` float32; `jnp.zeros((0,0))` when thermal is off). `EnvParams` gains the 12-field `thermal_*` block plus six per-entity temperature arrays (`obs_*` and `res_*`; absolute + ratio pair each). |
| `src/environment/config_loader.py` | New `_read_temperature` and `_apply_edge_margin` helpers. New conditional-mandatory `thermal:` block in `load_env_params`, placed immediately after the occlusion block and following its exact shape. Per-slot temperature arrays appended to the resource and obstacle builders; `edge_margin` applied as a load-time inset of the obstacle `area`. Load-time raises: animals declaring a temperature, `edge_margin` on a non-obstacle, both temperature styles on one entry, an empty inset rectangle, and either placement constraint under `placement_mode: per_type`. `height`/`width` moved up (they are needed by `_apply_edge_margin`), and the redundant function-local `import numpy as np` removed — it made `np` a function-local name for the whole body and would have turned every earlier use into `UnboundLocalError`. |
| `src/environment/core.py` | `resolve_overlaps_global` gains the optional D2 term. New `relocate_blocked_entities` (D3's second pass). New `_gaussian_smooth_normalised`, `_entity_temperatures`, `_stamp_sources`, `_build_thermal_field`. `jax_reset` builds the field after placement and the activation masks, under a static `if params.thermal_enabled:`. |
| `configs/environment/default.yaml` | The full commented `thermal:` key block, **and nothing else** — the `obstacles:` list is unchanged (F8 check below). |
| 71 fixtured full configs | The two-line `thermal: {enabled: false}` gate. |
| 19 test modules + `tests/fixtures/trajectory_collection/dual_format_config.yaml` | Same gate in their inline YAML bases. |
| `configs/environment/experiment/thermal/campfire_world.yaml` | **New.** The worked example: `thermal.enabled: true` plus one campfire entry with `edge_margin: 2` and `temperature_ratio: [11, 13]`. A full config, so the test harness can load it. |
| `tests/env/test_thermal_field.py`, `tests/env/thermal_sandbox_oracle.py` | **New.** Nine tests and the vendored numpy oracle. |
| `docs/environment/{CONFIG_GUIDE,02_config_schema,CONFIG_CRITICAL_SETTINGS}.md` | Stage 1's four Maintenance-Contract rows (§6c). |

**101 files touched** — 72 configs (`default.yaml` + 71 fixtured), 20 test modules/fixtures,
3 `src/` files, 3 Maintenance-Contract docs, 3 new files (this plan doc makes 102).

**Deviation D1-1 — the migration set is 72 fixtured configs, not 34, and the deferred set
is 68, not 106.** This is Stage 0's deviation D0-1 carried through, confirmed by
re-measurement: `collect_configs()` returns **356** configs (357 now that the thermal
example exists), of which **140** are full (no `extends:`) and **216** are layered.
**72** of the 140 carry a committed `.npz`, so group (b) is 72; the deferred remainder is
**68**. The plan's "roughly 55 files" was keyed to the stale 34.

**Deviation D1-2 — the deferred set is exactly the already-broken set.** All **68**
deferred full configs lack `sensory.injury_observable` and therefore already failed to
load before this change (F9). **Thermal newly breaks nothing.** Of the 68, **55** now
raise `Strict Config: Configuration key 'thermal.enabled' is required but missing.` and
the other **13** raise earlier on the pre-existing `sensory.visual_value_mode` gap — the
thermal block is read before the animal/sensory blocks those 13 trip on. Zero of the 68
load, so no fallback default crept in.

**Deviation D1-3 — no `animal_temperature` array.** The plan's field list names one, but
the plan's own resolution (a) — which the user selected — makes an animal's temperature a
**load error**. An always-zero array read nowhere is the "dead key" that resolution
forbids, so the array is not carried. Animals raise instead.

**Deviation D1-4 — D3's second pass is its own function, not another mask term.** The
first implementation followed the plan literally and added `constrained_mask` /
`blocked_cells` to `resolve_overlaps_global`, re-running the full overlap scan. That is
**wrong**, and the test caught it at roughly 1 reset in 600: a relocated food takes a
later entity's cell, that entity is displaced, and the cascade can land on the **fire's**
cell — which moves the very fire the exclusion mask was computed from, leaving food inside
the zone around its new position. `relocate_blocked_entities` moves only the marked
entities and freezes everything else, so the fires the mask describes cannot move. Same
PRNG discipline: one permutation, zero per-entity draws.

**H10 — how the placement constraints attach.** Exactly as the plan specifies. Both
constraints are extra terms in the existing validity mask, both behind a **static Python
`if`** on a config-time constant, and `load_env_params` pins both to `0` whenever
`thermal.enabled` is false. `resolve_overlaps_global` still draws exactly one
`jax.random.permutation` and walks it deterministically. No rejection loop was written.

**Test results.**

| Suite | Result |
|---|---|
| `tests/env/test_thermal_parity.py` (the Stage 0 byte-identity gate) | **72 passed, 285 skipped** |
| `tests/env/test_unified_parity.py` | **34 passed, 323 skipped** |
| `tests/env/test_visual_parity.py` | **8 passed** |
| `tests/env/test_no_recompile.py` | **3 passed** |
| `tests/env/test_thermal_field.py` (new) | **9 passed** |
| combined run of the five | **126 passed, 608 skipped, 0 failed** in 260 s |

**The parity gate stayed green — it never went red.** No tolerance was widened, and the
`properties_std`-keyed ulp exemption was not exercised beyond what Stage 0 already
measured. The skip count rose 284 → 285 only because `campfire_world.yaml` is a new config
that `collect_configs` walks and has no fixture.

**The nine new tests.**

| Test | What would fail without it |
|---|---|
| `test_field_matches_numpy_sandbox` | the blur, checked through `jax_reset` against the vendored sandbox oracle on the same raw stamps, `rtol=1e-5`. Uses a degenerate config (`default_temp: [-25,-25]`, absolute `temperature: 300`) so both per-episode draws vanish and the raw stamps are reconstructible from state alone |
| `test_stamps_are_additive` | assignment semantics (EVAAA's last-writer-wins). Two fires on ONE cell — set up by calling `_build_thermal_field` directly, because placement exists precisely to stop that co-location. Baseline pinned to 0 so the comparison is not a difference of two numbers near −25, where float32 cancellation destroys the tail values |
| `test_field_is_order_independent` | the same regression, from the other side: swapping the two fires' slot indices |
| `test_edge_renormalisation_matches_oracle` ×3 | a naive convolution at the edges, and a row/column transposition in the kernel — parametrised over 10×10, **7×13 and 13×7**, since a transposition is invisible on a square grid |
| `test_fires_respect_min_separation` | 500 resets, count pinned to a fixed 3. Asserts every pair ≥ 3 Manhattan apart **and** that no fire lands outside its own spawn area — the second assertion is what turns the silent cell-(0,0) park into a visible failure |
| `test_food_min_fire_distance_is_enforced_when_enabled` | 100 resets at `food_min_fire_distance: 4`; this is the test that found D1-4 |
| `test_placement_constraints_are_noops_when_disabled` | the H10 guard. `state.key`, `res_pos`, `animal_pos`, `obs_pos` compared for exact equality against the Stage 0 thermal-parity fixture, in **two** configurations: thermal off, and thermal **on** with both constraints at 0 — so the no-op is shown to be a property of the constraint values, not merely of the master switch |

**F8 check (the campfire must not be in the base file).** `default.yaml`'s `obstacles:`
list parses identically before and after: 3 entries, `rock` / `tree` / `bush`. The campfire
is only in `configs/environment/experiment/thermal/campfire_world.yaml`.

**Field sanity print, before any test was written.** One campfire at (3,2),
`default_temp: [-25,-25]`, absolute `temperature: 300`: peak cell **+72.42**, d=1 ring
**[+10.12, +10.12, +10.46, +10.11]**, far corner **−25.00**. The sandbox `gaussian_smooth`
on the same raw stamps prints the identical numbers.

**Speed check.** Env throughput on `default.yaml` (thermal off), 64 envs x 200 steps under
one jit, best of 3, CPU: **65,355 steps/s** at the Stage 0 tip (measured in a `git worktree`
at `765c8769`) vs **87,861 steps/s** on the working tree. The *implied* +34% is not real —
the two runs were not contention-matched (three pytest sessions were live during the
first). The change cannot plausibly affect thermal-off throughput: `jax_step` is untouched,
`jax_reset`'s thermal branch is a static Python `if` that a thermal-off config never
enters, and the parity gate proves the traced graph is unchanged (a different graph would
have moved `state.key`). Treated as **no measurable regression**; a contention-matched
re-measurement is cheap if `senior-developer` wants a defensible number. Script:
`tmp/20260908_thermal_stage1_speed.py`.

**Prior-art pass.** `grep -in 'thermal|temperature|placement|resolve_overlaps|spawn area|edge_margin'`
over `docs/develop/active/issues/KNOWN_BUGS.md`. Two hits, both unrelated (a snapshot
utility's hand-built config that mentions a `temperature` key of the neuromodulator, and a
comment nit). **No row covers the silent cell-(0,0) placement fallback** in
`resolve_overlaps_global`, confirming the plan's note. Owner named: `bug-curator`.

**`bug-curator` handoffs from this stage** (I do not file registry rows myself):
1. **The silent cell-(0,0) placement fallback** — pre-existing and independent of thermal:
   when an entity's spawn area fills up, `resolve_overlaps_global` parks it at (0,0),
   outside its own declared area, with nothing raised. Stage 1 makes it more reachable and
   guards it with a test, but does not fix it.
2. Stage 0's two open handoffs (F9 archive-migration drift, F10 unvalidated recording
   version stamp) are unchanged.

**Blockers / follow-ups.**
1. Not committed, per instruction. Working tree left dirty for verification.
2. `tests/algorithms/dreamer_srl/test_eval_rollout_batched.py::test_batched_eval_rollout_episode_measures_computable`
   fails, and it **fails identically at the Stage 0 tip** — verified by running it in a
   `git worktree` at `765c8769`. The test's expected key set contains `bush_dwell`, which
   appears nowhere in `src/`. Pre-existing and unrelated; a candidate `bug-curator` row.
3. Incidental: the edits to `resolve_overlaps_global` stripped trailing whitespace from
   several blank lines inside the function, so the diff carries a few whitespace-only
   hunks in otherwise-unchanged context.

Signed: `Implemented by: developer`


## Verification Report

> **Verified by**:
> **Date**:

| File | Change | Status | Notes |
|------|--------|:------:|-------|
| | | | |

**Conclusion**:
