---
title: "Body Temperature as an Interoceptive Observation Channel"
topic: sensors
status: active
created: 2026-09-14
last_updated: 2026-09-14
aliases: [body_temperature_observation]
---

# Body Temperature as an Interoceptive Observation Channel

> **Status**: PLANNED — nothing here is built.
> **Opened**: 2026-09-14
> **Revised**: 2026-09-14 after `plan-reviewer` (verdict SOUND WITH CONCERNS; four named gaps, all closed below)
> **Related**: [[thermal_implementation_plan]] (the temperature system this extends), [[thermal_handover]]

---

## Context

The agent in this project has three internal bodily states: how fed it is (satiation), how hurt it is (injury), and — added recently by the temperature system — how warm its body is (body temperature). The first of those is handed to the agent as a number in its observation. **Body temperature is not.** The agent can feel how much warmer or colder the *world* is than itself (that is what the thermoceptor reports), but it is never told what its own temperature actually is, even though leaving the survivable band ends the episode.

This plan adds that missing channel: one number, the body's own temperature, delivered to the agent alongside satiation.

Why now: the user's position is that internal states have to be delivered to the agent, and the reference environment this one was adapted from (EVAAA, a Unity survival environment kept under `vendor/evaaa/`) does exactly that — it hands the agent its food, water and thermal *levels* as the first block of its observation vector. We were diverging from that reference by accident, not by design.

**Scope is the channel only.** The follow-on experiment — "does the modulator's advantage survive when body temperature must be inferred instead of given?" — is deliberately split off and is not designed here. What this plan owes that experiment is a switch it can flip in a config file without anyone editing code.

One sentence on the awkward neighbour, because this looks like a reversal of a settled decision: **body temperature is observable because, unlike injury, it has no felt-percept channel that observing it would short-circuit** — the project deliberately hides injury because the agent already perceives it indirectly through Interoceptive Nociception, and that indirection is the phenomenon under study, whereas nothing in the observation is a percept *of* body temperature at all. (Argued properly in Analysis §5. This change does not reopen `injury_observable`.)

## Analysis

### 1. What the agent sees today

A live thermal-ON training run reports its observation as **32** numbers:

| Block | Dims | Kind |
|---|---:|---|
| Satiation | 1 | interoceptive |
| Interoceptive Nociception | 1 | interoceptive |
| Extero Nociception | 1 | exteroceptive |
| Thermoception | 5 | exteroceptive |
| Olfaction | 5 | exteroceptive |
| Collision | 5 | exteroceptive |
| Proprioception | 6 | efference |
| Visual | 8 | exteroceptive |

There is no body-temperature entry. (Verified fact supplied with the task; not re-derived here.)

### 2. Why the thermoceptor does not already carry it

`sense_thermoception` (`src/environment/sensor.py:65`) reports `thermal_field[cell] - body_temp` over a five-cell diamond whenever `thermal.relative` is true, which is what every shipped thermal config sets. Every one of those five numbers is a *difference*, including the centre cell, so body temperature cannot be read off any of them.

It is *recoverable in principle*: body temperature starts at exactly `thermal.temperature_setpoint` on reset (`src/environment/core.py:1873`) and is the driving term of its own update (`core.py:249-253`), so an agent with a perfect memory of every step could integrate it. That makes it **latent, not observed** — the distinction this change is about.

### 3. The EVAAA precedent is an interoceptive channel, not a sensor channel

In the vendored reference environment, `InteroceptiveAgent.CollectObservations` (`vendor/evaaa/evaaa_unity/Assets/Scripts/Agent/InteroceptiveAgent.cs:458-460`) begins with `sensor.AddObservation(resourceLevels)` — a contiguous block of raw internal levels, of which `resourceLevels[2]` is the thermal level. Its *thermal sensor* is a separate, later block of eight surrounding directions computed as `GetThermalSense() - resourceLevels[2]` (`:785-792`), i.e. relative, with **no centre cell** — `thermoSensorCenter` is declared but only ever written in a commented-out line at `:399`.

Two things follow, and only the first is a task:

- The precedent for "the agent knows its own temperature" is the **interoceptive levels block**, not the thermal sensor. This plan copies that.
- EVAAA's `resourceLevels` also contains `[3]`, the health level — so EVAAA *does* observe health. This project deliberately does not. That divergence is intentional and is addressed in §5.

### 4. The migration trap, and the shape that avoids it

This is the single most important constraint on the design, and getting it wrong turns the project's main regression gate red before it compares anything.

`tests/env/test_thermal_parity.py` replays a fixed 100-step episode for every config that has a committed `.npz` under `tests/env/fixtures/thermal_parity/` — **72 of them** — and asserts byte-for-byte agreement. It loads each config with `yaml.safe_load` straight into a raw `Config` (`test_thermal_parity.py:230-234`). **A raw `Config` does not resolve `extends:`** (`docs/environment/CONFIG_GUIDE.md` §5). Every one of those 72 files is therefore standalone and carries every mandatory key inline; spot checks confirm it (`configs/verification/observability_gates_S1.yaml`, `configs/environment/experiment/sensory_ladder/A_baseline.yaml`, `configs/continual/nmn_double_return_stages/01_active_predator.yaml` — 380 / 512 / 392 lines each, no `extends:`, each with a full inline `thermal:` block).

So there are two possible shapes for a new key, and they cost very different amounts:

| Shape | Precedent | Cost |
|---|---|---|
| **Unconditional** `get_mandatory` | `sensory.injury_observable` (`config_loader.py:2072`) | All 72 fixture configs raise at load → parity suite red before a byte is compared. Requires a 72-file inline migration plus ~20 test modules with inline YAML bases. |
| **Conditional under `thermal.enabled`** | the whole `thermal:` body block — `temperature_setpoint`, `k_exchange`, `k_loss`, `k_metabolic`, and `metabolic_coupling_rate` at `config_loader.py:1567` | Zero fixture configs change: all 72 ship `thermal.enabled: false`, so the guarded `get_mandatory` never runs. One real config to migrate (`campfire_world.yaml`), plus `default.yaml`. |

**This plan uses the conditional shape.** The initial brief for this work named `sensory.injury_observable` as the precedent to follow; that is the wrong half of the precedent, and `bug-curator` caught it. The right half is the thermal block's own conditional read.

**There is no `.get(..., False)` fallback anywhere in this change.** Deferring a config migration is only safe because `get_mandatory` fails loudly and names the missing key — `tests/env/test_backward_compat_configs.py:78-87` skips a config exactly when the loader raises `"... is required but missing"`, and fails it on any other error. A fallback default would convert 68 deliberately-deferred configs from "loudly unmigrated" to "silently loading with a value nobody chose", which is what `CONFIG_GUIDE.md` §5 calls out as the single change that would make deferral unsafe.

### 5. Why body temperature is observable when injury is not

The wiki entry `docs/llm_wiki/entries/env_entities/20260901_1528_interoceptive_channel_is_two_dims_by_design.md` records that `sensory.injury_observable: false` and `sensory.nutrition_observable: false` are **designed defaults**, and that turning them on was ruled out because it would dissolve the nociception-versus-pain distinction the project rests on. That decision stands, and this change does not touch it.

**The tempting argument is wrong, so it is stated and discarded here.** "Body temperature is a regulated homeostatic level, and regulated levels are observable" does not survive contact with the same wiki entry: **nutrition is a regulated level too**, and it is hidden. A rule the project has already declined once cannot be the justification for this change.

**The distinction that actually holds is about percepts, not levels.** Every hidden body variable in this environment is hidden because the agent already has a *percept* of it, and the gap between the hidden quantity and the percept is what is being studied or modelled:

| Hidden variable | Its percept | Why hiding it is load-bearing |
|---|---|---|
| `injury_level` | **Interoceptive Nociception** — the hidden injury convolved with an alpha kernel, peaking ~3 steps late (`config_loader.py:2079-2095`) | Observing injury collapses cause into percept and there is no nociception-versus-pain problem left to study. |
| `nutrition` | **Satiation** — `max_satiation * (nutrition/max_nutrition)**scaling` (`core.py:181-182`), a monotone but non-linear read-out of the reservoir | Observing nutrition gives the agent the reservoir directly instead of the compressed signal an animal actually has. |
| `body_temp` | **nothing** | Thermoception is *exteroceptive*: it reports the world minus the body (`sensor.py:65-90`). There is no interoceptive percept of body temperature anywhere in the observation, so there is no cause-percept gap for an observation to short-circuit. |

Body temperature is therefore not a fourth instance of "hidden cause behind a percept" — it is a variable with **no percept at all**, which is a different situation and the one EVAAA's `resourceLevels` block handles by simply delivering the level (§3).

**And the argument does not have to be won in advance**, which is why this plan ships a switch rather than a hard-wired channel: *"can the agent regulate a level it can only infer?"* becomes the follow-on experiment's question instead of an assumption baked into the environment. Note also that `IMPLEMENTATION_PLAN.md` D6-3 reasons **from** "body temperature is NOT observed" as a fact about the code, not as a decision that was taken — hiding it was an artefact of implementation order (Stage 2 added the body; Stage 3 added a *world* sensor).

### 6. The second mutually-blocking pair

`config_loader.py:2324-2342` documents in code that a new observation modality needs **both** of these, landing together:

- an entry in `_YAML_KEY_TO_SENSOR_NAME` mapping the YAML key to the breakdown name, **and**
- a matching block under `perceptual_noise.modalities` in `configs/environment/default.yaml`.

Without the map entry the loader raises `"unknown perceptual-noise modality key(s)"`. Without the config block, `apply_perceptual_noise` raises a bare `KeyError` **inside a jit trace**, naming neither the config nor the fix. Thermoception's Stage 3 is the worked example and the comment says so.

**There is a third such pair, not named in the brief**: `src/utils/evaluation_core.py:158-199` (`_sensor_stat_columns`) raises on any breakdown key without a branch, exactly as `build_sensory_viz` (`sensor.py:660-672`) does. Both are in the File Changes list.

Two adjacent observations, neither of which is a task here:

- `_parse_noise_config` pads the noise arrays to a hard-coded **13** slots (`config_loader.py:2368`) while `_YAML_KEY_TO_SENSOR_NAME` holds **11** entries. This change makes 12. **Correction to the received framing**: 13 is a *shape-stability* device, not a bounds check — with 14 entries `pad` clamps to 0 and the arrays simply become length 14, which every lookup (by name, via `modality_map`) still handles correctly. The failure mode is that `EnvParams` array shapes start varying with the config again, not silent corruption. Still worth a named error rather than a shrug; see "Separable item" below.
- `perceptual_noise.enabled` is read with `config.get(..., False)` (`config_loader.py:2320`) — a pre-existing fallback default, flagged only, **not fixed here**.

### 7. The ordering contract with no assert

`sensor.py:481-486` and `:537-544` carry a "MUST stay at the same position" invariant between the list `get_observation` concatenates and the dict `get_observation_breakdown` emits — stated in comments, with **no runtime assert**. Downstream, `build_sensory_viz` and `_sensor_stat_columns` both raise on an unknown sensor name, which catches a *missing* modality; neither catches two modalities in a *different order*. `dreamer_srl_main.py:751-758` asserts the breakdown's **total** equals the probed `obs_dim`, so a width disagreement is caught; order is not.

A width-comparing assert would not close this either, and `plan-reviewer` caught that the first draft of this plan proposed exactly such an assert: **Body Temperature and Interoceptive Nociception are both width 1**, which is precisely the pair the chosen position creates, so swapping them satisfies any count-and-width check. Change 12 therefore compares **names**, not widths.

### 8. What is provably unaffected

| Artefact | Why it cannot change |
|---|---|
| The 72 thermal-parity fixtures | All are `thermal.enabled: false`; the new key sits behind that gate and the new channel behind a static `if`. **Demonstrated by running the suite, not asserted** — see Checkpoint 4. |
| `tests/env/fixtures/metabolic_coupling/thermal_on_coupling_off.npz` (the one thermal-**ON** fixture) | It records `EnvState` numeric leaves plus `reward` / `done` / `info` only — **no observation** (`scripts/fixtures/generate_metabolic_coupling_fixture.py:82-115`). This change adds no state field and touches no state value. Its `_provenance_sha` is a report string, not a validated hash (`tests/env/test_metabolic_coupling.py:151`). |
| Every thermal-OFF run, current or historical | The modality is behind `if params.thermal_enabled and params.thermal_body_temp_observable:` — a static Python branch at trace time, contributing no operation to the graph. |

**One artefact that IS affected, and the first draft of this plan got it wrong.** `src/utils/eval_recording.py:70-91` stores `obs` and `true_obs`, whose width goes 32 → 33 on a thermal-ON observable config. The recording is nevertheless **self-consistent**: readers slice it by the run's own observation breakdown, so a recording read with its own run's config is always correct. The hazard is pairing a recording with the *wrong* flag's config — that mis-slices silently, because the format stamp (`eval_recording.py:20,85,102`) is written and never validated. This plan **follows** the thermal work's precedent (do not bump the stamp; handle new fields present-or-absent) rather than rejecting it, on the grounds that a stamp nothing validates would not catch this either. The real mitigation is Checkpoint 8's requirement to record which side of the flag a run was on.

### 9. The units decision, and how much runway it has

**The channel carries raw degrees — `state.body_temp` itself, unnormalised.** Decided, with the user, not defaulted.

Three arguments, in increasing order of weight:

1. It matches EVAAA's raw `resourceLevels[2]`, which is the precedent the whole change is modelled on (§3).
2. It preserves the exact identity `Thermoception[centre] + BodyTemperature = thermal_field[own cell]` under the shipped `thermal.relative: true` — a real convenience for anyone reading trajectories, and a quantity a normalised channel destroys.
3. **Consistency is the decisive argument.** Thermoception is already raw and reaches about **+167** near a fire. A normalised body-temperature channel sitting beside a raw exteroceptive thermoceptor would be inconsistent in a worse way than leaving both raw.

**The cost, stated plainly.** `train.py`'s rPPO path applies **no observation normalisation at all** — no running mean/std, no `normalize_obs` — so a ±15 raw channel shares one MLP with `[0,1]` channels and the network absorbs the scale mismatch itself. Dreamer is immune, because it symlogs its inputs. Thermoception's +167 is a **pre-existing instance of this same problem, not a justification for it**; if observation normalisation is ever added, it should be added for both.

**Reversing this later is not a one-line change.** It flips the noise block's `clip_min` / `clip_max` (Change 2) and the analysis CSV column name (Change 15) as well as the observation expression (Change 10).

**How much runway there is**: a sweep of all 456 saved run configs found **zero thermal-ON training runs**. Nothing currently depends on the raw scale, so the decision is free to revisit right up until the first thermal wave launches — after which changing it costs a re-run of the whole wave.

---

## Implementation Plan

### Design

**One new config key, one new observation dimension, both gated.**

```
thermal:
  enabled: true                # existing master gate
  ...
  grid_range: 1                # existing thermoceptor radius
  relative: true               # existing
  body_temp_observable: true   # NEW — conditional-mandatory under `enabled`
```

- **Name**: `thermal.body_temp_observable`. It follows the existing `<thing>_observable` family (`sensory.injury_observable`, `sensory.nutrition_observable`) and uses the codebase's own word for the quantity (`state.body_temp`). It lives under `thermal:` rather than `sensory:` because that is what makes it conditional — see Analysis §4.
- **`EnvParams` field**: `thermal_body_temp_observable`, **static** (`struct.field(pytree_node=False)`), because it gates a trace-time branch and fixes the observation width. Same treatment as `thermal_grid_range` and `thermal_relative`.
- **Breakdown name**: `"Body Temperature"` (dim 1). **Value**: raw degrees — rationale and cost in Analysis §9.
- **Noise-modality YAML key**: `body_temperature`.

**The key in `default.yaml` is load-bearing, not decoration.** `default.yaml` ships `thermal.enabled: false`, so the key is unread *on that file as shipped* — but `tests/env/test_thermal_validation.py:213-215` builds a case by taking `_default_dict()` and setting `enabled=True`, at which point the key is read and its absence would raise. Do not delete it as unused.

**Where it goes in the observation vector: immediately after Satiation, before Interoceptive Nociception.**

New order when everything is on:

```
[Injury?] [Nutrition?] Satiation [Body Temperature?] [Intero Noci?] | [Extero Noci?] [Thermoception?] [Olfaction?] Collision [Proprio?] [Visual?] [Location?]
         <------------ interoceptive ------------>                 | <---------------- exteroceptive / efference ---------------->
```

Justification:
- It keeps the **directly-delivered body levels** contiguous (Injury, Nutrition, Satiation, Body Temperature), with the *percept* (Interoceptive Nociception) after them — mirroring EVAAA's contiguous `resourceLevels` block.
- It makes `modulation.input_sensors: ["Satiation", "Body Temperature", "Interoceptive Nociception"]` a contiguous slice for future modulator work.
- **Cost**: Interoceptive Nociception's index moves by one on thermal-ON-and-observable configs only. This is free, because every consumer resolves by **name**, not index: the modulator input slice (`src/models/recurrent_ppo_network.py:25-82`, which raises on an unknown name rather than re-indexing silently), the stats-CSV headers (`evaluation_core.py:213-219`), the renderer sensor map (`renderer.py:800`, `renderer_v2.py:331`), and the noise modality map (`sensor.py:415`). No thermal-OFF run and no existing checkpoint is affected, and there are **zero** thermal-ON runs (Analysis §9).

**Consequence for `get_observation_breakdown`**: the new key must be inserted at the **identical position** in that function. Change 12 makes that structural instead of conventional.

**Consequence for any future thermal-ON fixture**: a fixture captured with the channel ON is a 33-wide recording and is not comparable with a 32-wide one. The existing thermal-ON fixture is immune (Analysis §8), but anyone generating a *new* observation-recording fixture must state which side of the flag it was captured on.

**Where the ablation flip lives**: `configs/environment/experiment/thermal/campfire_world.yaml` — the single config in the repository with `thermal.enabled: true` (verified by sweeping every config carrying a top-level `thermal:` block). Change 4 adds a sibling with the flag off, so the flip can be exercised by *choosing a config*, not by editing one.

**Deliberately NOT done: no right-panel sensor pod.** `'Body Temperature'` is **not** added to `known_sensors` (`renderer.py:910`, `grid_world.py:613`) or to `pod_map` (`renderer_v2.py:542-549`). Those lists build the EXTEROCEPTION panel; body temperature is interoceptive and already has a left-panel gauge (Change 14). An entry there would also push the Visual pod past the `y_cursor < 0.20` floor, which is the failure `renderer.py:911-919` documents from Stage 3. **This is a choice, recorded so nobody "fixes" it later.**

### File Changes

#### 1. `configs/environment/default.yaml` (thermal block, after line 323 `relative: true`)

```yaml
# BEFORE:
  # --- sensor (read from Stage 3 onward) ---
  grid_range: 1             # validated >= 0
  relative: true            # report field - body_temp

# AFTER:
  # --- sensor (read from Stage 3 onward) ---
  grid_range: 1             # validated >= 0
  relative: true            # report field - body_temp
  # Does the agent receive its OWN body temperature as an observation?
  # true  -> one extra observation dim, RAW DEGREES, placed immediately after
  #          Satiation (the directly-delivered body levels).
  # false -> body temperature stays latent: the thermoceptor's `field - body_temp`
  #          readings are differences, so the agent can only infer it by
  #          integrating over time.
  # Read ONLY when `enabled` is true, like every key in this block. It IS read on
  # this file in tests that flip `enabled` on a copy of it
  # (tests/env/test_thermal_validation.py:213-215) — not decoration, do not delete.
  # This is the switch the "inferred vs. given" ablation flips; the two sides ship
  # as two configs under experiment/thermal/, so no file is edited between runs.
  body_temp_observable: true
```

#### 2. `configs/environment/default.yaml` (`perceptual_noise.modalities`, inserting between `satiation:` at lines 380-385 and `interoceptive_nociception:` at line 386)

```yaml
# AFTER satiation:, BEFORE interoceptive_nociception:
    body_temperature:  # index 3 (new) — interoceptive; slots between satiation
                       # and interoceptive nociception, matching the observation
                       # order assembled in sensor.py::get_observation.
      mode: "state_dependent"
      # sigma is deliberately 0.0, for the same reason as thermoception: no
      # noise magnitude has been calibrated on the DEGREES scale, and copying an
      # interoceptive 0.1 (calibrated for a [0,1] channel) would add nothing
      # while looking like it added noise.
      sigma: 0.0
      injury_noise_scale: 1.5
      # Explicit and wide, like thermoception's. apply_perceptual_noise clips
      # EVERY modality whenever perceptual_noise.enabled is true — including
      # mode "none" — so a default that binds would silently rescale the signal
      # with no test catching it (every thermal test runs noise OFF).
      # Derivation: the survivable band is [min_temperature, max_temperature] =
      # [-15, +15], and a terminal overshoot adds at most one step of the
      # recurrence, k_exchange * |T_field - T| ~ 0.04 * 167 ~ 6.7. +-100 is
      # therefore >5x headroom and can never bind on a plausible config.
      clip_min: -100.0
      clip_max: 100.0
```

**Renumber the trailing `# index N` comments** of `interoceptive_nociception` through `location` by one, exactly as the Stage 3 change did. The indices are comments; every lookup is by name.

#### 3. `configs/environment/experiment/thermal/campfire_world.yaml`

Both edits from (1) and (2), at the matching positions (thermal sensor block after line 353; `perceptual_noise.modalities` after the `satiation:` entry). Value: `body_temp_observable: true`.

#### 4. NEW `configs/environment/experiment/thermal/campfire_world_body_temp_hidden.yaml`

A **full standalone copy** of `campfire_world.yaml` (no `extends:`, matching its sibling) differing in exactly two things: `thermal.body_temp_observable: false`, and a header comment saying what it is for. Its purpose is verification, not experiment design — it is what makes Checkpoint 9 a *choice of config* rather than an edit-run-edit-run cycle on a shipped file, which is both a parallel-session hazard and a muddier claim ("no code edited between runs" is stronger when no file changed at all).

Two consequences, both harmless but worth saying so nobody is surprised:
- `test_thermal_parity.py::_collect_configs` will pick it up. With no committed `.npz` it is **skipped**, not adjudicated (`test_thermal_parity.py:229`).
- `test_backward_compat_configs.py` will load it and must pass. It will: it carries every mandatory key inline, because it is a copy.

If the follow-on ablation needs more than these two arms, `experiment-designer` owns those configs, not this plan.

#### 5. `src/environment/config_loader.py:1590-1592` (inside `if thermal_enabled:`)

```python
# BEFORE:
        _th_relative = bool(config.get_mandatory('thermal.relative'))

# AFTER:
        _th_relative = bool(config.get_mandatory('thermal.relative'))
        # Conditional-mandatory under `thermal.enabled`, exactly like the four
        # body constants above and `metabolic_coupling_rate` below. It is NOT
        # read unconditionally like `sensory.injury_observable`: the 72
        # byte-parity fixture configs are stand-alone (the generator and
        # tests/env/test_thermal_parity.py build params from a RAW Config, which
        # does not resolve `extends:`), so an unconditional read would raise on
        # every one of them and the parity gate would go red before it compared
        # a single byte. CONFIG_GUIDE.md sec.5.
        # No `config.get(..., False)` fallback, ever: the 68 deliberately
        # deferred configs are safe only because get_mandatory fails loudly and
        # names the key.
        _th_body_temp_observable = bool(
            config.get_mandatory('thermal.body_temp_observable'))
```

#### 6. `src/environment/config_loader.py:1629-1630` (the inert `else:` branch)

```python
# BEFORE:
        _th_grid_range = 0
        _th_relative = False

# AFTER:
        _th_grid_range = 0
        _th_relative = False
        # Inert. `get_observation` / `get_observation_breakdown` skip the
        # modality under a static `if params.thermal_enabled and ...`, so this
        # is never read on a thermal-off config. False is the sentinel the
        # curriculum fingerprint sees on every non-thermal config.
        _th_body_temp_observable = False
```

#### 7. `src/environment/config_loader.py:2296` (the `EnvParams(...)` call)

```python
# BEFORE:
        thermal_relative=_th_relative,

# AFTER:
        thermal_relative=_th_relative,
        thermal_body_temp_observable=_th_body_temp_observable,
```

#### 8. `src/environment/config_loader.py:2327-2329` (`_YAML_KEY_TO_SENSOR_NAME`)

```python
# BEFORE:
    "satiation":                 "Satiation",
    "extero_nociception":        "Extero Nociception",

# AFTER:
    "satiation":                 "Satiation",
    # Body temperature. This entry and the `body_temperature:` block in
    # configs/environment/default.yaml are MUTUALLY BLOCKING and must land in
    # the same change — the same pair thermoception documents below: without the
    # entry the config raises "unknown perceptual-noise modality key(s)", and
    # without the config block `apply_perceptual_noise` raises a bare KeyError
    # inside a jit trace that names neither the config nor the fix.
    "body_temperature":          "Body Temperature",
    "extero_nociception":        "Extero Nociception",
```

Note the map's key order is documentation only — `noise_modality_order` is built from the **YAML's** iteration order, not this dict's.

#### 9. `src/environment/state.py:414` (`EnvParams`)

```python
# BEFORE:
    thermal_relative: bool = struct.field(pytree_node=False)

# AFTER:
    thermal_relative: bool = struct.field(pytree_node=False)
    # Does the agent receive its own body temperature as an observation dim?
    # STATIC for both of the reasons the two fields above are: it gates a
    # trace-time branch, and it changes the observation width (by 1). Also part
    # of the curriculum modality fingerprint, as `injury_observable` and
    # `nutrition_observable` are — defence in depth, since the width change
    # means the obs_dim check already catches a mismatch.
    # Inert (False) whenever `thermal_enabled` is False.
    thermal_body_temp_observable: bool = struct.field(pytree_node=False)
```

#### 10. `src/environment/sensor.py:469-474` (`get_observation`) — the new channel

```python
# BEFORE:
    # 3. Satiation — interoceptive
    obs_parts.append(jnp.array([state.satiation / params.max_satiation]))

    # 4. Interoceptive Nociception — interoceptive

# AFTER:
    # 3. Satiation — interoceptive
    obs_parts.append(("Satiation", jnp.array([state.satiation / params.max_satiation])))

    # 3b. Body Temperature — interoceptive, delivered directly.
    #     RAW DEGREES, not normalised: it shares units with the thermoceptor, so
    #     `Thermoception[centre] + BodyTemperature == thermal_field[own cell]`
    #     under the shipped `thermal.relative: true`. Rationale and the cost
    #     (rPPO applies no observation normalisation) in the plan, Analysis sec.9.
    #     Placed with the directly-delivered LEVELS (Injury / Nutrition /
    #     Satiation), before the PERCEPT (Interoceptive Nociception), mirroring
    #     EVAAA's contiguous `resourceLevels` block.
    if params.thermal_enabled and params.thermal_body_temp_observable:
        obs_parts.append(("Body Temperature", jnp.array([state.body_temp])))

    # 4. Interoceptive Nociception — interoceptive
```

#### 11. `src/environment/sensor.py:459-517` (`get_observation`) — name every block

Convert **every** `obs_parts.append(x)` in `get_observation` (11 sites) to `obs_parts.append((<breakdown name>, x))`, using the exact string `get_observation_breakdown` emits for that block: `"Injury"`, `"Nutrition"`, `"Satiation"`, `"Body Temperature"`, `"Interoceptive Nociception"`, `"Extero Nociception"`, `"Thermoception"`, `"Olfaction"`, `"Collision"`, `"Proprioception"`, `"Visual"`, `"Location"`.

This is bookkeeping only — no numerics change, because the concatenate becomes `jnp.concatenate([a for _, a in obs_parts])` over the same arrays in the same order.

#### 12. `src/environment/sensor.py` — make the ordering contract structural

Immediately before the concatenate in `get_observation`:

```python
    # The two functions are the SAME layout stated twice, and until now nothing
    # checked it. The breakdown's TOTAL is asserted against obs_dim in
    # dreamer_srl_main.py, but a REORDER leaves the total identical and every
    # name-keyed consumer (stats CSV, renderer, modulator input slice) then
    # labels the right columns with the wrong names, silently.
    #
    # Compares NAMES, not widths, and that is the whole point: Body Temperature
    # and Interoceptive Nociception are both width 1, so a width-and-count check
    # is blind to swapping exactly the pair this layout puts next to each other.
    _names = [name for name, _ in obs_parts]
    _declared = list(get_observation_breakdown(params))
    if _names != _declared:
        raise AssertionError(
            f"get_observation assembles blocks in the order {_names}, but "
            f"get_observation_breakdown declares {_declared}. The two functions "
            f"are the same layout stated twice and they have diverged; every "
            f"name-keyed consumer downstream would mislabel columns silently."
        )

    obs = jnp.concatenate([a for _, a in obs_parts])
```

`get_observation` is `@jax.jit(static_argnames=['apply_noise'])`, so this runs **once per trace** on Python strings and costs nothing per step. A bare `assert` is avoided deliberately — `python -O` strips those.

#### 13. `src/environment/sensor.py:632` (`build_sensory_viz`)

The terminal `else: raise ValueError(...)` at `:660-672` means a new breakdown key with no branch **raises**. Add, before the existing interoceptive-tile branch:

```python
        elif sensor_name == "Body Temperature":
            # Its own branch rather than joining the intensity tiles below: that
            # group renders a [0,1] fraction, and this value is raw degrees on a
            # roughly [-15, +15] band. Keys are `value` / `true_value` rather
            # than `intensity` / `true_intensity` precisely so nothing treats it
            # as a fraction by accident (draw_intensity_pod does `min(1.0, v)`).
            # The renderers pick it up BY NAME from sensor_map (renderer.py:800,
            # renderer_v2.py:331) and feed it to the existing body-temperature
            # gauge / card as the OBSERVED value. It is deliberately NOT in
            # `known_sensors` / `pod_map`, so it gets no exteroception pod.
            bt_obs = float(obs[ptr])
            bt_true = float(true_obs[t_ptr]) if true_obs is not None else bt_obs
            ptr += dim; t_ptr += dim
            viz.append({'name': 'Body Temperature', 'value': bt_obs,
                        'true_value': bt_true, 'type': 'temperature'})
```

#### 14. `src/environment/renderer.py:193-256` and `src/environment/renderer_v2.py:112-145`

Both `draw_temperature_gauge` and `draw_temperature_card` carry docstrings saying body temperature is **not** observed, and therefore draw one value with no OBS/REAL split (`IMPLEMENTATION_PLAN.md` D6-3). That statement is what this change reverses.

Minimal, geometry-preserving edit to both: add an **optional** `obs_temp=None` parameter. When `None`, the widget is byte-for-byte what it is today (so every thermal-ON-but-not-observable frame is unchanged). When a value is passed, render it as a second numeric readout beside the true one, in the project's existing "translucent = reality, solid = perceived" grammar. **Do not change the bar geometry** — `renderer.py:809-823` hand-tunes the 5-bar vitals layout against the Run Context pod at `y = 0.48`, and a sixth row would collide with it.

Call sites: `renderer.py:884-886` and `renderer_v2.py:367-370` pass
`obs_temp=(sensor_map.get('Body Temperature') or {}).get('value')`.

Update both docstrings: body temperature is observed **when `thermal.body_temp_observable` is true**, and the widget says so.

#### 15. `src/utils/evaluation_core.py:173` (`_sensor_stat_columns`)

```python
# BEFORE:
    elif sensor_name in ("Satiation", "Nutrition", "Injury"):

# AFTER:
    elif sensor_name == "Body Temperature":
        # Named apart from the intero_* group because the value is raw degrees,
        # not a [0,1] fraction — a reader scanning the CSV must not assume the
        # column is normalised like its neighbours. No unit suffix: the project
        # names no temperature unit anywhere, and inventing one is exactly the
        # kind of made-up convention the project rules forbid.
        names = [f"{prefix}intero_body_temp"]
    elif sensor_name in ("Satiation", "Nutrition", "Injury"):
```

#### 16. `train.py:810-812` and `src/algorithms/dreamer_srl/dreamer_srl_main.py:839-841` (both `_modality_fingerprint` copies)

```python
# BEFORE (in the thermal group):
            p.thermal_relative,

# AFTER:
            p.thermal_relative,
            # Changes obs_dim by 1, so the dim check above already catches a
            # mismatched curriculum -- included as defence in depth, the same
            # reasoning that puts injury_observable / nutrition_observable in
            # this tuple.
            p.thermal_body_temp_observable,
```

Both copies must stay identical; the Dreamer one is documented as "ported verbatim from train.py". The tuple goes from 26 fields to **27** — see Change 19.

#### 17. `tests/env/test_thermoception.py` — two existing tests this change breaks

`plan-reviewer` found both; the edits are pre-decided here so `developer` does not improvise. **These are the only two tests in the 239-test thermal baseline that change.**

**(a) `:256-273` `test_thermoception_costs_exactly_five_dims_and_sits_before_olfaction`.** Its `on` params come from the shipped campfire config, which becomes 33 wide and gains `Body Temperature`, so `sum(b_on) - sum(b_off) == 5` and the trailing dict-equality assertion both fail. Restore the test's *intent* — isolate the thermoceptor's cost — by switching the new channel off on the `on` side:

```python
# BEFORE:
    off = _params(THERMAL_CONFIG, lambda d: d["thermal"].update(enabled=False))
    on = _params(THERMAL_CONFIG)

# AFTER:
    # `body_temp_observable` is switched OFF on both sides so the width delta
    # below is the thermoceptor's alone. The body-temperature channel's own +1
    # is pinned in tests/env/test_body_temperature_observation.py.
    off = _params(THERMAL_CONFIG, lambda d: d["thermal"].update(enabled=False))
    on = _params(THERMAL_CONFIG,
                 lambda d: d["thermal"].update(body_temp_observable=False))
```

Update the docstring's "identical apart from `thermal.enabled` and the campfire obstacle" to say the body-temperature channel is off on both sides.

**(b) `:283-318` `test_sensory_viz_panels_are_not_shifted`.** It is parametrized over the campfire config and raises `"unrecognised pod shape"` for any viz entry without `vector` / `intensity` / `value_text`. Change 13 emits `value` / `true_value`. Add a branch, keeping the anti-shift guarantee intact:

```python
# BEFORE:
        elif "value_text" in pod:

# AFTER:
        elif "value" in pod:
            # Body Temperature: one raw-degrees number, deliberately not keyed
            # `intensity` because it is not a [0,1] fraction.
            assert hi - lo == 1
            assert np.float32(pod["value"]) == obs[lo]
        elif "value_text" in pod:
```

#### 18. NEW `tests/env/test_body_temperature_observation.py`

Every test must **fail on pre-change code and pass after**.

| Test | Asserts |
|---|---|
| `test_key_is_mandatory_when_thermal_is_on` | Load `campfire_world.yaml` as a dict, `del d["thermal"]["body_temp_observable"]`, `pytest.raises(ValueError, match="thermal.body_temp_observable")`. Mirrors `test_metabolic_coupling.py:383-390`. |
| `test_key_is_not_read_when_thermal_is_off` | Take `default.yaml` (thermal off), `del d["thermal"]["body_temp_observable"]`, assert it still loads and `params.thermal_body_temp_observable is False`. **This is what proves the 72 fixtures are safe by construction**, not only by measurement. |
| `test_no_fallback_default` | The loader raises, and the message names the key. Guards against a `.get(..., False)` creeping in later. |
| `test_channel_present_and_is_raw_body_temp` | Thermal-ON + observable: `"Body Temperature" in breakdown`, dim 1, and after `state.replace(body_temp=jnp.float32(-7.25))` the observation slice at that offset equals `-7.25` **exactly** (noise off). A normalised, clipped or rescaled value fails. |
| `test_flag_false_removes_exactly_that_one_column` | **Self-consistency, not a historical comparison** — no pre-change thermal-ON observation fixture exists (Analysis §8) and none is captured for this. Reset **once** with the flag-false params, then call `get_observation(state, params_false)` and `get_observation(state, params_true)` on that same state (the flag is read nowhere in `core.py`, so one state is valid for both). Assert `np.delete(obs_true, idx) == obs_false` **bit-exact**, where `idx` is the offset the breakdown gives for `"Body Temperature"`. That is the ablation's real requirement: switching the channel off changes nothing except removing that column. |
| `test_position_is_after_satiation_before_intero_noci` | The breakdown keys, in order, contain `Satiation` immediately followed by `Body Temperature` immediately followed by `Interoceptive Nociception`. |
| `test_breakdown_and_observation_agree` | `sum(breakdown.values()) == obs.shape[0]` across the four combinations of (thermal on/off) × (observable true/false). |
| `test_order_assert_catches_a_reorder` | Monkeypatch `get_observation_breakdown` to return the same dict with `Body Temperature` and `Interoceptive Nociception` swapped, and assert `get_observation` raises. **This is the test that proves Change 12 is not vacuous** — the two blocks are the same width, so it also demonstrates why a width-only check would not have caught it. |
| `test_modulator_slice_resolves_under_the_new_layout` | `_resolve_modulator_input_indices(["Satiation", "Body Temperature", "Interoceptive Nociception"], breakdown, obs_dim)` returns three **contiguous** indices, and naming `"Body Temperature"` against a flag-false breakdown raises rather than silently re-indexing. |
| `test_noise_map_and_config_block_are_paired` | With the `body_temperature:` block present, `"Body Temperature" in params.noise_modality_order`; and a modality block naming a key absent from `_YAML_KEY_TO_SENSOR_NAME` still raises `"unknown perceptual-noise modality key(s)"`. |
| `test_stats_csv_and_viz_have_branches` | `build_stat_headers(...)` and `build_sensory_viz(...)` both succeed on a thermal-ON observable config — neither terminal `raise` fires — and the CSV carries an `obs_intero_body_temp` column. |
| `test_both_shipped_thermal_configs_declare_the_key` | `campfire_world.yaml` (true) and `campfire_world_body_temp_hidden.yaml` (false) both carry `thermal.body_temp_observable` inline. Cheap, and it is what stops either config silently falling into the "stale config" **skip** branch of `test_backward_compat_configs.py:78-87` — a missing key there is *skipped*, not failed. |

#### 19. Documentation, in the same change (maintenance contracts)

| Doc | Change |
|---|---|
| `docs/environment/CONFIG_GUIDE.md` §3.9 (lines 228-330) | Add `body_temp_observable` to the `thermal:` example block and to the conditional-key note at line 328. State that it changes `obs_dim` and therefore checkpoint / curriculum compatibility. |
| `docs/environment/CONFIG_GUIDE.md` §5 | Add this change beside the two existing precedents as the worked example of the **conditional** shape being chosen specifically to avoid a 72-file migration. |
| `docs/environment/02_config_schema.md` §"`thermal:` keys" (lines 63-79) | New table row: `body_temp_observable` → `thermal_body_temp_observable`, mandatory **yes** (conditional), contributes 1 observation dim. Update line 47 — it names the fingerprint fields and says **26**; Change 16 makes it **27**. Update lines 107-113 (the observation description) to name the new modality and its position. |
| `docs/environment/09_sensors_and_observation.md` | **Observation-order table at `:24-33`** — insert a row for Body Temperature between Satiation (#3) and Interoceptive Nociception (#4), renumbering the rest: flag `thermal_enabled AND thermal_body_temp_observable`, dim 1, value range `[min_temperature, max_temperature]` in **raw degrees**, formula `body_temp`. Note in the column that it is the one row whose value is not normalised to a fixed interval. Also **`:342`**, which states Olfaction's index arithmetic as `[5 : 5+vector_size]` "assuming Injury + Nutrition + Satiation + InteroNoc + ExteroNoc all enabled and occupying indices 0-4" — that sentence becomes wrong when the new channel is on; extend it rather than leave a stale worked example. |
| `docs/environment/10_perceptual_noise.md` | **Modality table at `:78`** — insert `body_temperature` / `Body Temperature` at index 3 and renumber `interoceptive_nociception`..`location` (3→4 … 10→11), matching Change 2. Add a bullet to "Notes on the default values" saying its clips are declared explicitly for the same reason thermoception's are, and that its σ is 0.0 because no noise magnitude has been calibrated on a degrees scale. |
| `docs/environment/CONFIG_CRITICAL_SETTINGS.md` | **Yes, it earns a registry row** — it gates an observation channel, changes `obs_dim`, and therefore silently breaks checkpoint restore and curriculum compatibility, which is precisely the class `sensory.olfactory_grid_range` and `thermal.grid_range` are in. Add the row **and** a dated change-log entry in the same commit, per that doc's logging protocol. The 2026-09-09 Stage 3 entry is the template; the entry must state the 72-passed parity result, the 32→33 width on the example config, and that zero thermal-ON runs predate it. |
| `docs/develop/active/thermal/IMPLEMENTATION_PLAN.md` | **Append** a note under D6-3 that its premise ("body temperature is NOT observed") is superseded by this plan, with a wikilink. Append, do not rewrite — that document is a signed record. |

`docs/environment/SCRIPTS_DEPENDENCY_MAP.md` needs **no** update: nothing under `scripts/` is added, moved, renamed, deleted, or has its callers changed.

### Separable item (drop it if a reviewer objects; say which you did)

`config_loader.py:2368` pads the noise arrays to a hard-coded 13 while the modality map now holds 12. Add, immediately before the `pad = ...` line:

```python
    _NOISE_SLOTS = 13   # the padded width EnvParams declares for the noise arrays
    if len(noise_modality_order) > _NOISE_SLOTS:
        raise ValueError(
            f"perceptual_noise.modalities names {len(noise_modality_order)} "
            f"modalities but the noise arrays are padded to {_NOISE_SLOTS} "
            f"slots. Widen the pad and the [{_NOISE_SLOTS}] shape comments on "
            f"EnvParams.noise_* together, or EnvParams array shapes start "
            f"varying with the config again."
        )
    pad = max(0, _NOISE_SLOTS - len(noise_modality_order))
```

Zero behaviour change today. Included because this change consumes the second-to-last slot; excluded from the core scope because it is adjacent code.

---

## Checkpoints

Verify **during** implementation, in order. Each names what makes it fail. `PY` below is `/home/vncuser/miniconda3/envs/grid_world_pain/bin/python`; never `conda run`, never system `python3`.

- [ ] **1 — The key is mandatory, and only when thermal is on.**
  `JAX_PLATFORMS=cpu $PY -m pytest tests/env/test_body_temperature_observation.py -k "mandatory or not_read or fallback"`.
  Fails if the read escaped its guard, or if a fallback default crept in.
- [ ] **2 — The channel is exactly one raw number in the right place.**
  `JAX_PLATFORMS=cpu $PY -m pytest tests/env/test_body_temperature_observation.py`.
- [ ] **3 — The order assert is not vacuous.** `test_order_assert_catches_a_reorder` swaps two **equal-width** blocks (Body Temperature ↔ Interoceptive Nociception) — the case a width-only check cannot see. Record the raised message in the Implementation Report. **An assert never seen to fail is not evidence**, and a demonstration that only moves a block past a *different-width* neighbour would not have tested the real hazard.
- [ ] **4 — The 72 byte-parity fixtures are untouched, demonstrated by running them.**
  `JAX_PLATFORMS=cpu $PY -m pytest tests/env/test_thermal_parity.py` → must report **72 passed**. Paste the summary line into the Implementation Report. A stated expectation is an assumption; the run is the evidence.
  **If any fixture goes red**: the discriminator (registry worked example `cc6353a`) is whether the failing set is *exactly* the configs touched, with zero unexplained residue — and the only fixtured config this change touches is `default.yaml`. Do **not** widen a tolerance, do **not** regenerate a fixture. Stop and diff.
  Known non-bug, do not re-escalate: env reset is not bit-identical across compilations on `animal_property_sampled`, ≤ 5.96e-08 (one float32 ULP, documented XLA fusion). Drift on any *other* column is real.
- [ ] **5 — The other parity gates stay green.**
  `JAX_PLATFORMS=cpu $PY -m pytest tests/env/test_unified_parity.py` and the same for `tests/env/test_visual_parity.py`, one file per process. Expect the documented 34 and 8.
- [ ] **6 — The thermal suite.** Run all 8 thermal-related files **one per process**: `test_thermal_body.py`, `test_thermal_field.py`, `test_thermal_parity.py`, `test_thermal_rendering.py`, `test_thermal_reward_gate.py`, `test_thermal_validation.py`, `test_thermoception.py`, `test_metabolic_coupling.py`.
  **Expected arithmetic, corrected**: the baseline is 239 passed / 0 failed, and Change 17 **edits two of those tests** rather than leaving the baseline untouched. So the expectation is *still 239 in these 8 files* (no test added or removed there — both edits change assertions, not counts), **plus** the new file's count from Checkpoint 2. If the 8-file total is not 239, a third test broke and was not predicted — stop and name it.
  **Never run `pytest tests/env/` in one process — it core-dumps inside XLA on this machine.**
- [ ] **7 — The rest of the suite.** `$PY -m pytest tests/ --ignore=tests/env` — **no** CPU pin (a repo-wide pin silently skips 7 GPU-path tests).
- [ ] **8 — Real run output confirms the width change, read from the run's own log.** This is the only acceptable evidence for what 32 → 33 means to the network; a fresh config-loader reload is **not** — it re-derives what should happen instead of observing what did.
  - **Trainer**: rPPO (`train.py`), because its banner prints the full per-sensor breakdown.
  - **Agent config**: `configs/models/recurrent_ppo/recurrent_ppo_M.yaml` — a plain, non-modulator config, so the run tests the observation layout and nothing else. (The modulator's name-keyed slice under the new layout is covered by a unit test instead of a second launch: Change 18, `test_modulator_slice_resolves_under_the_new_layout`.)
  - **Env config**: `configs/environment/experiment/thermal/campfire_world.yaml`.
  - **`--quiet` must be absent** from the command line. It is `action="store_true"` and `train.py:1125` gates the entire banner on `if not args.quiet:` — passing it makes this checkpoint silently unverifiable.
  - A handful of episodes is enough; the banner prints before training.
  - **Node and GPU come from the coordinator**, and the launch goes through `training-runner` / `run_command.py` — never raw SSH.
  - **Read the banner from `wandb/run-<id>/files/output.log`**, one unshared file per run. Do **not** read the `run_command.py` log: `run_command.py:77-79` collapses several runs' logs into one and shreds exactly this banner, and this change is what makes the banner matter.
  - Record verbatim: the `Observation Dim: 33 (...)` line; the per-sensor breakdown showing `Body Temperature ... 1` between `Satiation` and `Interoceptive Nociception`; and the run's own saved config, confirming the flag the trainer actually resolved.
  - **What the width change implies, to be confirmed rather than assumed by this step**: the network input layer is sized from the probed observation at startup (`train.py:1123-1130`, `dreamer_srl_main.py:742-761`), so no model file needs editing; but a 32-wide checkpoint cannot be restored into a 33-wide run, and a curriculum mixing the two is rejected by the pre-flight `obs_dim` + fingerprint check. State in the report whether the run confirmed each, or whether one went untested.
- [ ] **9 — The flip works as a flip.** Repeat Checkpoint 8 with **`configs/environment/experiment/thermal/campfire_world_body_temp_hidden.yaml`** (Change 4) — a different config file, not an edit of the first one. Confirm the banner reports **32**, with no `Body Temperature` row and every other row identical. Nothing in `src/`, `configs/` or `scripts/` is touched between the two runs, which is what makes "config flip, not code change" a demonstrated claim rather than a design intention.
- [ ] **10 — Videos still render.** Render one episode from `campfire_world.yaml` and confirm the vitals panel draws the body-temperature gauge with both readings and that the exteroception pods below are not shifted. The terminal `raise` in `build_sensory_viz` catches a *missing* branch; only looking at a frame catches a *wrong* one. Confirm no empty `BODY TEMPERATURE` pod appears in the right panel — that would mean `known_sensors` was edited against the Design note.
- [ ] **11 — Speed.** Same node, same GPU, same env + agent config, same seed, same step budget, long enough to clear warm-up and JIT compilation (a run short enough to be dominated by compilation measures nothing). Record steps/sec before and after and the hardware/config/seed all three. Expected delta ≈ 0: one extra scalar, static branches, a trace-time name check. **>5% slowdown warrants discussion; >15% blocks merge** unless explicitly accepted here — it is not.

## Out of scope — recorded and handed off, not fixed here

| Item | Owner / disposition |
|---|---|
| The follow-on ablation ("does the modulator's advantage survive when body temperature must be inferred?") | `experiment-designer`. This plan owes it only the config flip, delivered by Checkpoint 9 and the sibling config in Change 4. |
| `scripts/analysis/ladder/lad03_how_it_ends.py` hardcodes three termination outcomes with no share-sum guard; termination code 5 ("frozen or overheated") already exists, so the first thermal run published through that figure under-totals silently | Already an open row with an owner named. Mentioned only. |
| `run_command.py:77-79` collapses parallel runs' logs, shredding the `Observation Dim` banner | Not this change. Worked around in Checkpoint 8 by reading `wandb/run-*/files/output.log`. |
| `perceptual_noise.enabled` read via `config.get(..., False)` — a pre-existing fallback default | Flagged, deliberately not fixed. Fixing it would make configs that omit the key fail to load, which is a migration, not a bug fix. |
| The eval-recording format stamp is written and never validated, so a recording paired with the wrong flag's config mis-slices silently (Analysis §8) | Follows the thermal work's precedent (no stamp bump). Recorded as a standing weakness of the recording format, not introduced here and not fixed here. |
| `scripts/verification/check_observability_gates.py` covers only injury/nutrition (configs `observability_gates_S1..S4`, all thermal-OFF) | A thermal-ON `S5` case would be the consistent extension. Not needed: Change 18 covers the same ground with better tooling. Recorded as an option. |
| Observation normalisation in rPPO (Analysis §9) | Genuinely absent, and thermoception already exposes the project to it. A real design question for `professor-rl` / `senior-developer`, not a rider on this change. |
| `sensory.injury_observable` / `sensory.nutrition_observable` | Explicitly **not** reopened. See Analysis §5. |

## Implementation Report

> **Implemented by**: [agent/person]
> **Date**: [date]

<!-- Filled by `developer`. Must contain, verbatim:
     - the `test_thermal_parity.py` summary line (Checkpoint 4);
     - the message raised by the equal-width reorder test (Checkpoint 3);
     - the 8-file thermal total and the new file's count (Checkpoint 6);
     - the two startup banners, 33-wide and 32-wide, quoted from
       wandb/run-*/files/output.log (Checkpoints 8 and 9);
     - the before/after steps-per-second numbers and the hardware/config/seed
       they were measured on (Checkpoint 11);
     - whether the separable noise-slot guard was included.
     Deviations from this plan, with reasons, go here — not silently in the diff. -->

## Verification Report

> **Verified by**: [agent/person]
> **Date**: [date]

| File | Change | Status | Notes |
|------|--------|:------:|-------|
| | | | |

**Conclusion**: [one-line summary]
