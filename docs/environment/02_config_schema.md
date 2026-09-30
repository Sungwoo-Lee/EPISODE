# 02 — Config Schema

> **Source**: `src/environment/config_loader.py`, `src/environment/state.py`, `configs/environment/default.yaml` | **Back to hub**: [ENVIRONMENT_SUMMARY](ENVIRONMENT_SUMMARY.md)

> **v3.0 updates** — For the config-system workflow (`extends:` layering, sparse overrides, authoring), see the companion [CONFIG_GUIDE.md](CONFIG_GUIDE.md). New v3.0 fields not yet enumerated below in full: top-level `extends:` (layered-config marker); per-entity `visual_properties` / `visual_properties_std` plus `sensory.visual_vector_size` (default 8) and `sensory.visual_background_properties` (3×V, required when V≠8); conditional-mandatory `body.start_{nutrition,injury}_{low,high}`; `behavior_measures.eval_seeds` list-or-`{rng, sort}`-spec form; and per-entity `count_low`/`count_high` for per-episode count ranges (see [Entity Count Expansion](#entity-count-expansion) and CONFIG_GUIDE §3.6).

---

## Directional sensors (DIRECTIONAL_SENSORS feature set)

Eight keys added by the directional-sensors work. **All default to the pre-change
behaviour**, so a config that sets none of them produces byte-identical observations.
Full rationale: [[DIRECTIONAL_SENSORS_PLAN]], [[DIRECTIONAL_SENSORS_REPORT]].

### `sensory:` keys

| Key | Type | Default | Meaning |
|---|---|---|---|
| `olfactory_grid_range` | int, static | `0` | Radius of the diamond of olfactory **sampling cells**. `0` = the single pre-DIRECTIONAL_SENSORS sample at the agent's own cell. Contributes `(2r²+2r+1) × vector_size` dims. **Not to be confused with `sensor_radius`**, which is how far a smell *carries*; this is where it is *measured*. A radius, not a side length: `1` → 5 cells, `2` → 13. Out-of-bounds cells read exactly zero. |
| `visual_blur_enabled` | bool, static | `false` | **Gates the three knobs below** — they are read only when this is true (CONFIG_GUIDE §5 conditional-key pattern), so a config that never blurs need not carry them. Replaces the exact cell match with an anisotropic gaussian point-spread. Needs `visual_sensor_range ≥ 1` to have anywhere to spread. |
| `visual_blur_radial_scale` | float, traced | *(conditional)* | `σ_parallel = scale × distance` — how fast distance judgement degrades. |
| `visual_blur_anisotropy` | float, traced | *(conditional)* | `ρ = σ_parallel / σ_perp`. `1.0` is exactly an isotropic kernel, which makes an ablation a one-value change. |
| `visual_blur_sigma_floor` | float, traced | *(conditional)* | Lower bound on both widths, in cells. **Required, not cosmetic**: mass normalisation divides by `2π σ_par σ_perp`, so an entity on the agent's own cell would otherwise give an infinite peak. Half a cell is the grid's sampling limit. |
| `visual_value_mode` | enum, static | `sum` | How per-cell entity contributions combine. `sum` = weighted sum (two rocks read 2.0); `clamp` = per-channel presence capped at 1.0. Applies to the **entity** contribution only — terrain keeps its own value. |
| `visual_occlusion_enabled` | bool, static | `false` | Line-of-sight occlusion. An entity is hidden when a nearer `blocks_sight` entity lies inside the shadow cone of the ray to it. |
| `visual_occlusion_cone_deg` | float | *(conditional)* | Half-angle of the shadow cone, in `(0, 90)`. **Read only when occlusion is enabled** (CONFIG_GUIDE §5 conditional-key pattern). |
| `visual_occlusion_strength` | float | *(conditional)* | `1.0` hides fully, lower values attenuate. Range `[0, 1]`. Conditional as above. |
| `olfactory_channel_names` | list of `{name, qualifier}` | *(required when olfaction is enabled)* | Reader-facing name per smell channel, printed under that channel's map in the episode video. **Display only** — changes no observation, no agent input, no training. Exactly `vector_size` entries. `name` and `qualifier` are two fields, never one string: the painter sets the qualifier in a lighter style beside the name and must never parse its own label text. Read at **recording-write time**, not by `load_env_params`, so it never reaches the byte-parity gates. |
| `olfactory_channel_groups` | list of `{name, channels}` | `[]` | Channels drawn as ONE map instead of one map each. Normally empty for smell — two smells can be present at once. |
| `visual_channel_names` | list of `{name, qualifier}` | *(required when the visual sensor is enabled)* | As above, exactly `visual_vector_size` entries. **A config that sets its own `visual_vector_size` must redeclare this in the same file**: a child config replaces a list wholesale or not at all and cannot shorten an inherited one. |
| `visual_channel_groups` | list of `{name, channels}` | `[]` at V=1; `[{name: Terrain, channels: [0,1,2]}]` at V=8 | Which channels merge into a single map. `channels` must be a contiguous run, every index must exist, no channel may appear in two groups, and a group may not exceed the merged map's palette (3 colours). **The channels a group names are the channels the merged map READS** — declaring `[1,2,3]` draws a map coloured from channels 1–3. |

**Enabled-sense rule.** A sense's two display keys are read **only when that sense resolves enabled** (`olfactory_enabled` / `visual_sensor_enabled`). A vision-off config needs no vision names, and display keys left behind for a disabled sense are ignored rather than refused. **No fallback defaults**: a missing key on an enabled sense raises `ValueError` naming the key when a recording is written.

### Per-entity keys

| Key | Applies to | Default | Meaning |
|---|---|---|---|
| `visual_mask` | resources, entities, obstacles | `none` | `none` \| `far` \| `all`. `far` = visible **only** when the agent is co-located with it; `all` = never visible. Gates on the **entity's** distance, not the cell's — gating per cell leaks the entity's blur tail into the agent's own cell. An unrecognised string raises. |
| `blocks_sight` | resources, entities, obstacles | `false` | Whether this entity occludes things behind it. **Distinct from `blocking`** (movement) and **`hides_agent`** (concealment from predators); all three are independent. |

### Calibration warning

The shipped scene holds up to 36 entities on 100 cells, so occlusion is aggressive.
Measured share of live entities hidden, obstacles-only blocking: **5° → 31%, 10° → 47%,
15° → 59%, 30° → 75%**. Start narrow.

### Curriculum-fingerprint interaction

`olfactory_grid_range`, `visual_blur_enabled`, `visual_value_mode`,
`visual_occlusion_enabled` and the three per-entity mask/blocks arrays are part of the
27-field modality fingerprint (`train.py`, `dreamer_srl_main.py`) — as are
`thermal_enabled`, `thermal_grid_range`, `thermal_relative` and
`thermal_body_temp_observable` — they change what an
observation *means* at an identical width, which the `obs_dim` check cannot catch. The
continuous blur and cone knobs are deliberately **out**: fingerprinting floats would
forbid legitimate schedules.

---

## Thermal (temperature system)

The world gets a per-episode `[H, W]` temperature map — cold everywhere, hot near a
campfire. Stage 1 builds the map and stores it on `EnvState.thermal_field`; Stage 2 gives
the agent a `body_temp` that drifts toward the cell it stands on and can end the episode
(termination code 5); Stage 3 lets the agent **feel** the field through a five-cell
thermoceptor. Temperature is not in the reward yet (Stage 4). Plan:
[[thermal_implementation_plan]].

### `thermal:` keys

| Key | EnvParams field | Static | Validation | Meaning |
|---|---|---|---|---|
| `enabled` | `thermal_enabled` | **yes** | — | master gate; unconditionally mandatory, no fallback |
| `sigma` | `thermal_sigma` | no | `> 0` | blur width in cells |
| `default_temp` | `thermal_default_temp_low/high` | no | `low <= high` | world baseline, drawn uniformly once per episode |
| `use_random_spots` | `thermal_use_random_spots` | **yes** | — | gates the `random_spots:` sub-block |
| `use_object_sources` | `thermal_use_object_sources` | **yes** | — | whether entity `temperature` is stamped at all |
| `random_spots.count` | `thermal_spot_count` | **yes** | `>= 0` | number of random square stamps |
| `random_spots.size` | `thermal_spot_size` | **yes** | `>= 1` | stamp width in cells |
| `random_spots.temp` | `thermal_spot_temp` | no | — | stamp magnitude; sign is drawn per spot |
| `min_fire_separation` | `thermal_min_fire_separation` | **yes** | `>= 0` | Manhattan; `0` disables |
| `food_min_fire_distance` | `thermal_food_min_fire_distance` | **yes** | `>= 0` | Manhattan; `0` disables. Counts **every** fire slot, burning or not |
| `bush_min_fire_distance` | `thermal_bush_min_fire_distance` | **yes** | `0` or `>= 2` (`1` refused) | Manhattan, bush (`hides_agent`, not a heat source) to fire; `0` disables and is today's placement exactly. Counts **burning** fires only (unlit slots do not count). Static. [[BUSH_FIRE_CLEARANCE]] |
| `warming_rate_scale` | `thermal_warming_rate_scale` | **yes** | `> 0`; `× (k_exchange + k_loss) <= 1` | multiplies the body's per-step temperature change when it is positive; 1.0 = single-rate. Conditional-mandatory under `enabled` |
| `cooling_rate_scale` | `thermal_cooling_rate_scale` | **yes** | `> 0`; `× (k_exchange + k_loss) <= 1` | multiplies the body's per-step temperature change when it is zero or negative; 1.0 = single-rate. Conditional-mandatory under `enabled` |
| `grid_range` | `thermal_grid_range` | **yes** | `>= 0` | thermoceptor **radius**; contributes `2r²+2r+1` observation dims |
| `relative` | `thermal_relative` | **yes** | — | `true` reports `field − body_temp`; `false` reports the raw field |
| `body_temp_observable` | `thermal_body_temp_observable` | **yes** | — | `true` hands the agent its OWN body temperature as **1** observation dim, in raw degrees, immediately after Satiation; `false` leaves it latent. Conditional-mandatory under `enabled`, like every key in this block |

`thermal_kernel_radius` is derived, not configured: `ceil(3 * sigma)`, static because it
fixes the number of unrolled shifts in the blur.

### How the field is built

`_build_thermal_field` (`src/environment/core.py`) runs once per episode inside
`jax_reset`, after placement and after the per-episode activation masks have parked
inactive slots off-grid. The order is load-bearing:

1. fill the whole grid with `default_temp`;
2. random spots, if enabled;
3. entity stamps — **additive**, never assignment;
4. **one** weight-normalised Gaussian blur.

Stamps add because two fires making a hotter spot is the physically sensible reading, and
because assignment would make the result depend on slot iteration order. The blur drops
out-of-bounds neighbours from both the weighted sum and the weight sum (EVAAA's
`sum / weightSum`), so an edge cell is the mean of its real neighbours; a plain convolution
differs there.

When `thermal.enabled` is false the whole build is skipped by a **static Python branch** and
`thermal_field` is `jnp.zeros((0, 0))` — so an accidental read fails loudly on shape rather
than quietly on value, and the traced graph (and therefore every PRNG stream) is identical
to the pre-thermal environment.

### The thermoceptor (Stage 3)

`sense_thermoception` (`src/environment/sensor.py`) samples `thermal_field` over the same
Manhattan diamond the collision and visual sensors use — `get_visual_offsets(grid_range)`,
so at `grid_range: 1` the five values are **centre, up, right, down, left** in that order.
With `relative: true` each value is `field[cell] − body_temp`: "how much warmer than me is
that cell", which is the quantity the agent can act on. The modality is inserted after
Extero Nociception and before Olfaction, in `get_observation` and
`get_observation_breakdown` alike, and is absent entirely when `thermal.enabled` is false.

### The body-temperature channel (`body_temp_observable`)

Every thermoceptor reading is a *difference*, including the centre cell, so the agent's own
body temperature cannot be read off any of them. `thermal.body_temp_observable: true` adds
it as a separate, **interoceptive** modality named `"Body Temperature"`, width **1**,
carrying `state.body_temp` in **raw degrees** — deliberately not normalised, so that
`Thermoception[centre] + BodyTemperature == thermal_field[own cell]` under the shipped
`relative: true`. Its position is immediately **after Satiation and before Interoceptive
Nociception**, which keeps the directly-delivered body levels (Injury, Nutrition, Satiation,
Body Temperature) contiguous and puts the *percept* after them. With it false the quantity
stays latent: recoverable only by integrating the recurrence over the whole episode.

It changes `obs_dim` by one, so it participates in the modality fingerprint and in
checkpoint/curriculum compatibility: a 32-wide checkpoint cannot be restored into a 33-wide
run. `get_observation` now raises `AssertionError` if its block order disagrees with
`get_observation_breakdown` — comparing **names**, not widths, because Body Temperature and
Interoceptive Nociception are both width 1 and a count-and-width check cannot see them
swapped.

**Out-of-bounds cells CLAMP; they do not read zero.** This is a deliberate departure from
the convention `sense_olfaction_cells` and `sense_visual` follow, and it must not be
"fixed" back. On a *relative* reading, zero means "that cell is exactly my own
temperature" — the single most misleading value available, and in a world whose baseline
is −25 it would make the map edge look like a warm refuge to an agent standing in the
cold. Clamping the coordinate reports the nearest real cell instead, which is also what
the field itself does at its edges: `_gaussian_smooth_normalised` renormalises by the
in-bounds weight sum rather than averaging in zeros.
`tests/env/test_thermoception.py::test_oob_reads_the_clamped_neighbour` asserts the
clamped identity exactly, not merely the absence of a zero.

**The `thermoception:` perceptual-noise block declares its clips explicitly**, and must.
`apply_perceptual_noise` clips every modality whenever `perceptual_noise.enabled` is true
— including modalities in mode `none` — and the loader's defaults are ±100, while a
fire-cell relative reading measures up to about +170 on the shipped example. The declared
bounds are `[-100, 400]`; the derivation is in the YAML comment. See
[10_perceptual_noise.md](10_perceptual_noise.md).

### The two placement constraints

Both attach as extra terms in `resolve_overlaps_global`'s validity mask, **not** as a
rejection loop. That function draws exactly one `jax.random.permutation` up front and then
walks it deterministically — zero per-entity draws — so a rejection loop would draw fresh
keys, shift every downstream PRNG stream, and break byte-parity across the whole project
for a reason unrelated to temperature. Both are gated by a static Python `if` on a
config-time constant, so `0` traces the pre-thermal graph exactly.

- **`min_fire_separation`** is enforced in the first pass, by carrying a dilated
  fire-occupancy mask in the scan carry alongside the ordinary occupancy mask.
- **`food_min_fire_distance`** needs a **second pass** (`relocate_blocked_entities`): the
  scan order is `[res, pred, obs, neutral]`, so resources are placed before any fire
  exists. The second pass moves *only* food and leaves every other entity where the first
  pass put it — re-running the full overlap scan instead lets a displaced entity cascade
  onto the fire's own cell, moving the very fire the exclusion mask was computed from.
- **`bush_min_fire_distance`** is a **third pass** after the food pass, reusing
  `relocate_blocked_entities` with its own stream (`fold_in(resolve_key, 0xB05E)`): it
  moves *only* bushes (obstacle slots with `hides_agent` that are not heat sources) off
  every cell at Manhattan `< value` from a **burning** fire, so fires, food, animals and
  rocks keep the cells (and the random numbers) the rule-off world gives them. Unlike the
  food rule it ignores unlit fire slots, so it needs the per-episode obstacle activation
  mask before placement; that draw depends on `property_key` alone. At load the rule is
  refused unless the world has a fire and a bush, no slot is both, no resource is a heat
  source, and a worst-case count bound proves every bush can always find a cell (so the
  `(0, 0)` fallback below cannot fire for it). Plan: [[BUSH_FIRE_CLEARANCE]].
- Under **`placement.mode: per_type`** none of the three constraints is supported (that mode uses
  `place_in_area` and bypasses the validity mask), and a non-zero value **raises at load**
  rather than being silently ignored.

**A pre-existing silent fallback both constraints make more reachable.** When no cell
satisfies the validity mask, `resolve_overlaps_global` parks the entity at cell `(0, 0)` —
outside its own spawn area — with nothing raised. `tests/env/test_thermal_field.py::test_fires_respect_min_separation`
therefore also asserts that every fire lands inside its own area.

### The load-time structure check (Stage 6b)

**What it is for.** The temperature task only exists inside a narrow band of settings. The
fire has to be hot enough to hurt when the agent stands on it, the ring one cell out has to
be somewhere the agent can survive indefinitely, and three cells out the cold has to
actually end the episode. Miss that band — by changing `sigma`, `default_temp`, the fire's
`temperature_ratio`, or the grid size — and the run still looks perfectly healthy while the
agent learns a different task: a fire with no bite, or a world with nowhere survivable
beside it, or a cold that never runs out. `thermal.sigma` has already produced one silent
all-NaN training run in this project. This check makes the next one **fail at load**.

**Where it runs.** `config_loader.load_env_params`, at load — not at reset. Reset runs under
`jit` on every episode of every parallel environment, and every input the check needs is a
config constant.

**What it computes.** For the corners of the sampled ranges (`thermal.default_temp`
low/high × the entity's `temperature_ratio` low/high — four draws — plus the midpoint) it
builds a single-fire field on the config's own grid, using the **same blur `jax_reset`
calls** (`core._gaussian_smooth_normalised`, never a numpy twin), averages it over the
Manhattan rings at distance 0, 1 and 3, and converts each ring's mean into the body
temperature the recurrence settles at:

$$
T^{*} = \frac{k_{ex} \cdot T_{field} + k_{loss} \cdot T_{setpoint} + k_{met}}{k_{ex} + k_{loss}}
$$

This is the **general** fixed point. The special case `k_ex·T_field / (k_ex + k_loss)`
quoted in the design sandbox is only correct when `temperature_setpoint` and `k_metabolic`
are both zero; both are config keys with non-zero-capable values, and with either set the
special case will pass a lethal comfort ring or reject a perfectly good one. The approach to
`T*` is monotone, so "equilibrium inside `[min_temperature, max_temperature]`" is exactly
"survivable indefinitely" and "outside" is exactly "dies eventually". The two rate scales
(`warming_rate_scale`, `cooling_rate_scale`) do not enter this check: they multiply the whole
per-step change, so the fixed point is the same, and the per-scale `<= 1` bound keeps the
approach monotone.

Corners rather than a random draw is deliberate: the check must be **deterministic**, so a
config either always loads or never does. One that passed on Monday and failed on Tuesday
would be worse than none.

**When it runs.** All four of these, or the check logs one line saying which precondition
failed and continues:

1. `thermal.enabled` is true.
2. `thermal.use_object_sources` is true — mode A (`use_random_spots: true`,
   `use_object_sources: false`) has no fire to check at all.
3. At least one allocated **slot** is a heat source. A heat source is *a slot with a
   non-zero declared temperature in either style*, defined once in `core.heat_source_mask`
   and shared with the placement constraints. Slots, not entries: two separate
   single-count fire entries are two fires, and they can spawn adjacent.
4. At least one heat-source slot declares its heat as a **`temperature_ratio`**. The
   calibrated band is stated as a multiple of the world's coldness (11–13× |`default_temp`|),
   so an absolute `temperature:` stamp — the documented escape hatch that adds a number
   straight into the field — is outside the band's domain and is **not certified**. The log
   line says so; it never passes silently.

**It also refuses `min_fire_separation: 0` with more than one heat-source slot.** The check
models a single fire. With the separation constraint disabled two fires can spawn adjacent,
their stamps add, and the merged comfort ring goes lethal exactly where the agent would
have to stand (+33.0 at separation 1 and +15.4 at separation 2 against a +15 threshold,
versus +8.4 at the shipped separation of 3). Certifying a world the model does not cover is
worse than not certifying it, so this raises and names **both** keys.

**On failure it raises `ValueError`, never warns.** A warning is what the sigma-floor
incident produced, and it trained silently for a full run. The message names the offending
key, the drawn corner, all three distances' equilibria, the survivable band, and which of
the three conditions failed — enough to retune without opening this document:

```
thermal structure check FAILED for heat source 'campfire'. Drawn corner:
thermal.default_temp = -28 (declared range [-28, -22]), temperature_ratio = 3
(declared range [3, 4]) -> a single fire of +84.0 on a 10x10 grid with
thermal.sigma = 0.7.
  Equilibrium body temperature by Manhattan distance from the fire:
  d0 = +2.53, d1 = -18.28, d3 = -22.06; survivable band
  [thermal.min_temperature, thermal.max_temperature] = [-15, 15].
  Failed: the fire does not hurt: standing ON it settles at +2.53, inside the
  survivable band [-15.0, 15.0]; there is no comfort ring: one cell out settles
  at -18.28, ...
  Retune thermal.default_temp, the entity's temperature_ratio, or thermal.sigma.
  The calibrated band is sigma near 0.7 with a ratio of 11-13.
```

`tests/env/test_thermal_validation.py` holds both halves: the configs that must be refused
(each asserting on the message text, not merely that something raised) and — equally
important — the Stage 1–5 test configs, mode A and an all-zero-temperature world, which
must all still **load**. A check that rejected any of those would surface as four earlier
stages becoming unrunnable.

---

## Water (the pond and thirst)

One pond per episode (an `h × w` block of walkable cells, fixed within the episode, redrawn
between episodes) and a two-sided **hydration** axis that drains every step, refills on every
step spent on a pond cell, and kills at both ends (reason 6 dehydration, 7 over-drinking).
Plan: [[thirst_water_plan]]. Workflow notes: `CONFIG_GUIDE.md` §3.10.

### `water:` keys

Parsed by `config_loader._load_water`, which runs just before `EnvParams` is built (it needs
the resolved spawn areas and start position). Every `EnvParams` water field is **static**
(`pytree_node=False`); arrays are held as tuples. With `enabled: false` the loader reads no
other key and fills the sentinels `False / 0 / 0.0 / ()`.

| Key | EnvParams field | Read when | Validation (`ValueError` naming the key) | Meaning |
|---|---|---|---|---|
| `enabled` | `water_enabled` | **always** (mandatory) | — | master gate, no fallback |
| `placement` | (resolves `water_topleft_table`) | enabled | `list` / `random` / `center` | how the pond's top-left is chosen each episode |
| `size` | `water_block_h`, `water_block_w` | enabled | two ints `>= 1` | `[rows, cols]` of the pond |
| `candidates` | (resolves `water_topleft_table`) | enabled and `placement: list` | non-empty; `[r, c]` ints, **1-based**; no duplicates; block inside the grid and inside `edge_margin`; must not cover a fixed `start_pos` | candidate top-left cells, one drawn uniformly per episode |
| `edge_margin` | — (used at load) | enabled | int `>= 0` | border ring the pond may not touch, all three modes |
| `max_hydration` | `water_max_hydration` | enabled | finite, `> 0` | top of the axis; `W >= max` is fatal |
| `hydration_setpoint` | `water_hydration_setpoint` | enabled | `0 <= set <= max` | the comfortable level (drive target) |
| `start_hydration` | `water_start_hydration` | enabled and the random flag false | `0 < start < max` | fixed start; written into `state.hydration` at reset |
| `random_start_hydration` | `water_random_start_hydration` | enabled | bool | draw the start uniformly on `[low, high)` |
| `start_hydration_low` / `_high` | `water_start_hydration_low/high` | enabled and the random flag true | `0 <= low <= high <= max` | draw range; `low = 0` can land exactly on the floor (dies on step 1) |
| `drain_per_step` | `water_drain` | enabled | finite, `>= 0` | lost every step |
| `drink_gain_per_step` | `water_drink_gain` | enabled | finite, `>= 0` | gained on every step ending on a pond cell (before the single clip) |
| `properties` | `water_cell_property` (= `properties / (h·w)`) | enabled | length `sensory.vector_size`, each in `[0, 1]` | smell vector of the whole pond; per cell it is divided by the cell count |
| `visual_properties` | `water_visual_property` | enabled | length `sensory.visual_vector_size`, each `>= 0` | written by every pond cell into the visual channel(s); not normalised |

`water_topleft_table` holds the resolved top-left cells in **0-based array coordinates**:
`list` → the candidates minus 1; `random` → every top-left inside the margin (minus any
covering a fixed start); `center` → `((H − h) // 2, (W − w) // 2)`. `jax_reset` draws one
index into it per episode (fold-in stream `0xD81`).

**Refused combinations**: `environment.placement.mode: per_type`;
`thermal.food_min_fire_distance > 0`; `thermal.bush_min_fire_distance > 0`; a missing
`perceptual_noise.modalities.hydration`; a failing **capacity check** — for every entity slot at
overlap-scan position `k` (order `[res, pred, obs, neutral]`) with post-inset area `A`,
`|A| − max over ponds |pond ∩ A| >= k + 1`.

**Coupled state and observation.** `EnvState.hydration` (`[]` float32) and `EnvState.water_pos`
(`[h·w, 2]` int32, every pond cell) are `None` when water is off. When on, the observation
gains **"Hydration"** (`hydration / max_hydration`) directly after "Body Temperature", and the
info dict gains `drank` and `drive_thirst`.

---

## Overview — what this document is about

This document describes how a YAML configuration file is translated into the typed `EnvParams` data structure that the JAX-based GridWorld uses at runtime. The translation is performed by `load_env_params(config)` in `src/environment/config_loader.py`.

**Why this matters for a new reader:** The environment is configured entirely through YAML. The loader enforces a strict "no silent failure" policy: any field declared mandatory raises `ValueError` if absent. Several fields that existed in v1.x have been removed or renamed (most notably, the old separate `predators:` and `neutral_animals:` sections have been merged into a single "unified animal entity" system). If your config was written before v2.0, read the migration notes in the entity section below.

`EnvParams` is a JAX Flax struct used inside JIT-compiled functions. Fields marked `pytree_node=False` (called **static** below) are baked into the compiled function — changing them triggers a full JIT recompilation.

---

## Transformation Pipeline (v2.0)

`load_env_params(config: Config) → EnvParams` (`config_loader.py:614`) executes in this order:

1. **Guard** — if `environment.predator_enabled` is present, raise `ValueError` immediately (`config_loader.py:666`). This key was removed in v2.0.
2. **Resources** — parse `environment.resources` list, expand each entry by its `count` field, build `res_*` arrays (`config_loader.py:617–661`).
3. **Unified animals** — call `_load_animals(config)` (`config_loader.py:673–689`), which detects whether the config uses the legacy dual-section schema (`environment.predators:` + `environment.neutral_animals:`) or the new unified `environment.entities:` schema, then expands, validates, and builds all `animal_*` arrays. See §Unified Animal Entity for details.
4. **Obstacles** — parse `environment.obstacles` list, expand by `count`, build `obs_*` arrays (`config_loader.py:692–732`).
5. **Location grid** — parse `environment.location_areas` list → fill `grid_location_type [height, width]` numpy array with type codes (0: plain, 1: grass, 2: sand) (`config_loader.py:735–748`).
6. **Placement grouping** — concatenate spawn areas in `[resources | predator-class animals | obstacles | neutral-class animals]` order, group by identical spawn-area bounding box, build `type_areas`, `type_counts`, `type_entity_map`, `max_per_type`, `num_types`, `num_entities` (`config_loader.py:751–800`).
7. **Interoceptive sensor** — read `sensory.injury_observable`, `sensory.nutrition_observable`, `sensory.interoceptive_*` keys; build normalized alpha kernel if convolution is enabled (`config_loader.py:803–826`).
8. **Noise config** — call `_parse_noise_config(config)` → build five noise arrays of length 13 (`config_loader.py:957–1002`).
9. **Construct `EnvParams`** — assemble all arrays and scalars into the Flax struct (`config_loader.py:828–941`).

---

## YAML Top-Level Structure

```
environment:
  height, width, max_steps
  start_pos, random_start_pos
  rest_action_enabled, eat_action_enabled
  placement.mode                       # "per_entity" | "per_type"
  resources: [ list of resource defs ]
  predators: [ list — LEGACY; auto-projected as class=predator, behaviour=hunt ]
  neutral_animals: [ list — LEGACY; auto-projected as class=neutral, behaviour=wander ]
  entities: [ list — NEW unified schema (CP3) ] # precedence: legacy `predators:`/`neutral_animals:` win when the USER FILE authors them (even if `entities:` arrived only via the default.yaml base underlay); see FIX_CONFIG_LAYER_SILENT_FAILURES_20260723
  obstacles: [ list of obstacle defs ]
  location_areas: [ list of area type defs ]
  # NOTE: predator_enabled was REMOVED in v2.0 — raises ValueError if present

body:
  max_satiation, max_nutrition, max_injury
  metabolic_cost, food_nutrition_gain, eating_nutrition_cost, eating_reward_penalty
  nutrition_to_satiation_scaling_factor, satiation_setpoint
  start_satiation, start_nutrition
  recovery_base_rate, recovery_accel_rate, recovery_in_bush_multiplier, injury_smoothing_duration
  use_homeostatic_reward, death_penalty, overeating_death
  with_satiation, with_nutrition, with_injury
  random_start_satiation, random_start_nutrition, random_start_injury

sensory:
  olfactory_enabled, sensor_radius, vector_size, decay_power
  olfactory_grid_range                                   # DIRECTIONAL_SENSORS
  collision_sensor_range
  nociception_enabled, nociception_size
  visual_sensor_enabled, visual_sensor_range
  visual_blur_enabled, visual_blur_radial_scale,         # DIRECTIONAL_SENSORS
    visual_blur_anisotropy, visual_blur_sigma_floor      # DIRECTIONAL_SENSORS
  visual_value_mode                                      # DIRECTIONAL_SENSORS
  visual_occlusion_enabled                               # DIRECTIONAL_SENSORS
    [+ visual_occlusion_cone_deg, visual_occlusion_strength
       — read ONLY when occlusion is enabled]
  proprioception_enabled
  location_sensor
  injury_observable, nutrition_observable
  interoceptive_nociception_enabled, interoceptive_convolution_enabled
  interoceptive_kernel_tau, interoceptive_kernel_length

visualization:
  local_view_size

perceptual_noise:
  enabled: bool
  modalities:
    injury / nutrition / satiation / interoceptive_nociception /
    extero_nociception / olfaction / collision / proprioception /
    visual / location:
      mode, sigma, injury_noise_scale, clip_min, clip_max

behavior_measures:           # optional block; absent → feature off
  enabled, cue_radius, obs_window, eval_n_episodes, eval_seeds
  eval_policy_mode, eval_max_steps, eval_obs_noise
  motif_window_K, motif_features, motif_kmeans_k, motif_kmeans_seed
  motif_standardise, eval_output_root

training:                    # configs/train/ layer — NOT read by config_loader.py;
                             # see CONFIG_GUIDE.md §7 for the layering + full key list.
  # 2026-07-27 additions (ASYNC_CHECKPOINT_VIDEO_RENDER):
  async_video_render         # bool — non-blocking checkpoint-video render (src/utils/async_render.py);
                             #   false = legacy blocking render (kill-switch; DQN/DRQN/PPO fallback)
  render_every_n_checkpoints # int — MP4 every Nth checkpoint (async path only); recordings unaffected
  render_workers             # int|null — --workers cap for the render subprocess (null = cpu_count-1)

logging:                     # configs/train/ layer — NOT read by config_loader.py (CONFIG_GUIDE.md §7)
  episode:
    # 2026-09-27 additions (BALANCE_METRICS_TRAINING_LOGGING) — rPPO only, in
    # configs/train/recurrent_ppo.yaml; deliberately ABSENT from configs/train/default.yaml:
    balance_metrics                # bool, mandatory for RecurrentPPO — Episode/Bal_* logging on/off
    balance_early_death_max_steps  # int >= 0, mandatory when balance_metrics is true — deaths at
                                   #   length <= this are "early" (excluded from Bal_LateDeath*); 20
```

---

## Integer Encoding Maps (v2.0 constants)

Defined at `config_loader.py:32–41` and used throughout the animal-entity builder.

| Concept | String | Integer | Field(s) in EnvParams |
|---------|--------|---------|----------------------|
| Animal class | `"predator"` | `0` | `animal_classes_int` |
| Animal class | `"neutral"` | `1` | `animal_classes_int` |
| Animal behaviour | `"wander"` | `0` | `animal_behaviours_int` |
| Animal behaviour | `"hunt"` | `1` | `animal_behaviours_int` |
| Animal behaviour | `"static"` | `2` | `animal_behaviours_int` |
| Visual channel | predator class | `5` | `animal_visual_channel` |
| Visual channel | neutral class | `7` | `animal_visual_channel` |
| Damaging classes | `{"predator"}` | derived bool | `animal_is_damaging` |
| Resource type | food | `0` | `res_type` |
| Resource type | hiding\_predator | `1` | `res_type` |
| Location area | plain (default) | `0` | `grid_location_type` |
| Location area | grass | `1` | `grid_location_type` |
| Location area | sand | `2` | `grid_location_type` |

### Implementation

These five module-level constants are the single source of truth for all integer encodings in the codebase. Every `jnp.array(...)` call that touches class/behaviour codes reads from these dicts rather than hardcoding integers, so adding a new class or behaviour requires changing only these lines.

`Source: src/environment/config_loader.py:31–42`

```python
# ── Animal entity constants (v2.0) ────────────────────────────────────────────
ANIMAL_CLASS_TO_INT = {"predator": 0, "neutral": 1}
ANIMAL_CLASS_TO_VIS_CHANNEL = {"predator": 5, "neutral": 7}
ANIMAL_DAMAGING_CLASSES = {"predator"}
ANIMAL_BEHAVIOUR_TO_INT = {"wander": 0, "hunt": 1, "static": 2}
DISTRIBUTIONAL_FIELDS = (
    "detection_range",
    "max_stamina",
    "stamina_recovery_rate",
    "hunt_stamina_threshold",
    "lose_interest_multiplier",
)
```

> **API notes**
> These are plain Python dicts/sets/tuples — host-side only. They are consulted during `_load_animals()` to build integer arrays (`animal_classes_int`, `animal_behaviours_int`, etc.) that are then wrapped with `jnp.array(...)` and stored as JAX-traceable leaves of `EnvParams`. The string keys themselves become `pytree_node=False` static tuples (`animal_classes`, `animal_behaviours`, `animal_tags`). `DISTRIBUTIONAL_FIELDS` names the five YAML keys whose `[lo, hi]` pairs are stored as paired `_low`/`_high` arrays and sampled per episode inside `jax_reset` (a `lax.scan` walks them). See [primer: static vs dynamic fields](00_jax_primer.md#static-dynamic), [primer: JAX pytrees](00_jax_primer.md#jax-pytrees), and [primer: scan](00_jax_primer.md#scan).

---

## Unified Animal Entity (v2.0 refactor)

The old separate `predators:` + `neutral_animals:` YAML sections that produced distinct `pred_*` and `neutral_*` arrays **no longer exist at the array level**. They are replaced by a single unified `animal_*` array family. `_load_animals()` (`config_loader.py:202`) handles both the old (legacy) and new schema automatically.

### Two supported YAML schemas

**Schema A — Legacy (all pre-v2.0 configs)**

```yaml
environment:
  predators:
    - name: "predator"
      count: 1
      properties: [0.0, 0.7, 0.5, 0.0, 0.0]
      properties_std: [0.0, 0.4, 0.4, 0.0, 0.0]
      move_interval: 1
      damage: [15.0, 45.0]
      nociception_intensity: 0.9
      spawn_area: [[1,1],[10,10]]
      patrol_area: [[1,1],[10,10]]
      detection_range: 5          # mandatory for predator/hunt
      max_stamina: 30
      stamina_recovery_rate: 1
      hunt_stamina_threshold: 0.7
      attack_delay: 3
      lose_interest_multiplier: 1.5
  neutral_animals:
    - name: "rabbit"
      count: 1
      properties: [0.0, 0.5, 0.7, 0.0, 0.0]
      properties_std: [0.0, 0.4, 0.4, 0.0, 0.0]
      move_interval: 1
      nociception_intensity: 0.1
      spawn_area: [[1,1],[5,5]]
      patrol_area: [[1,1],[5,5]]
```

Legacy predators are re-projected as `class='predator'`, `behaviour='hunt'`. Legacy neutrals are re-projected as `class='neutral'`, `behaviour='wander'`. The five distributional fields (`detection_range` etc.) are read as scalars from legacy entries and stored as degenerate ranges `[s, s]`. Legacy neutrals never carried `damage`/`attack_delay` — the loader auto-fills `[0.0, 0.0]` and `0` internally (NC-1 fix; not a user-facing default).

**Schema B — Unified (CP3 and later)**

```yaml
environment:
  entities:
    - class: "predator"
      behaviour: "hunt"
      tag: "alpha"
      count: 1
      properties: [0.0, 0.7, 0.5, 0.0, 0.0]
      properties_std: [0.0, 0.4, 0.4, 0.0, 0.0]
      move_interval: 1
      damage: [15.0, 45.0]
      nociception_intensity: 0.9
      attack_delay: 3
      spawn_area: [[1,1],[10,10]]
      patrol_area: [[1,1],[10,10]]
      detection_range: [3, 7]     # distributional: [low, high]
      max_stamina: [20, 40]
      stamina_recovery_rate: [0.5, 1.5]
      hunt_stamina_threshold: [0.5, 0.9]
      lose_interest_multiplier: [1.0, 2.0]
    - class: "neutral"
      behaviour: "wander"
      tag: "rabbit"
      count: 2
      ...
```

**Precedence (updated by FIX_CONFIG_LAYER_SILENT_FAILURES_20260723):** if the user file itself authors legacy `predators:`/`neutral_animals:` sections, they take precedence and define the scene — even if an `entities:` list arrived only via the `default.yaml` base underlay (e.g. under `train.py`'s `get_default_config()` + `merge()`). A `DeprecationWarning` still fires (now naming the legacy scene as authoritative) so authors know to migrate. Only when the user file has NO legacy sections does the `entities:` list (own or inherited) take the path. This makes `train.py`/`dreamer_srl_main.py` (which underlay `default.yaml`) agree with `eval_rollout.py` (which loads bare, no underlay) on every legacy config's animal scene. See [[FIX_CONFIG_LAYER_SILENT_FAILURES_20260723]] for the full analysis.

### Mandatory / optional per entity

| Field | `behaviour: hunt` | `behaviour: wander` / `static` |
|-------|--------------------|-------------------------------|
| `class` | **mandatory** | **mandatory** |
| `behaviour` | **mandatory** | **mandatory** |
| `move_interval` | **mandatory** | **mandatory** |
| `damage` | **mandatory** | **mandatory** (unified schema); auto-filled for legacy neutrals |
| `attack_delay` | **mandatory** | **mandatory** (unified schema); auto-filled for legacy neutrals |
| `properties` | **mandatory** | **mandatory** |
| `properties_std` | **mandatory** | **mandatory** |
| `detection_range` | **mandatory** | optional (auto-filled `[0,0]`) |
| `max_stamina` | **mandatory** | optional (auto-filled `[0,0]`) |
| `stamina_recovery_rate` | **mandatory** | optional (auto-filled `[0,0]`) |
| `hunt_stamina_threshold` | **mandatory** | optional (auto-filled `[0,0]`) |
| `lose_interest_multiplier` | **mandatory** | optional (auto-filled `[0,0]`) |
| `nociception_intensity` | optional (default `0.9`) | optional (default `0.0`) |
| `spawn_area` | optional (default full grid) | optional (default full grid) |
| `patrol_area` | optional (default full grid) | optional (default full grid) |
| `tag` | optional (default `idx{i}`) | optional (default `idx{i}`) |
| `count` | optional (default `1`) | optional (default `1`) |
| `attack_range` | optional (default `[0,0]` = jump disabled) | optional (default `[0,0]`) |
| `attack_success_rate` | optional (default `0.0`) | optional (default `0.0`) |

### Distributional fields (per-episode sampling)

The five fields in `DISTRIBUTIONAL_FIELDS` (`config_loader.py:36–41`) can be a scalar or a `[low, high]` list. A scalar `s` is stored as `[s, s]` (deterministic). At each episode reset, a value is sampled uniformly from `[low, high]` for each animal individually.

| YAML key | `_low` array | `_high` array | Cadence |
|----------|-------------|--------------|---------|
| `detection_range` | `animal_detect_low` | `animal_detect_high` | per-episode |
| `max_stamina` | `animal_max_stamina_low` | `animal_max_stamina_high` | per-episode |
| `stamina_recovery_rate` | `animal_recovery_low` | `animal_recovery_high` | per-episode |
| `hunt_stamina_threshold` | `animal_hunt_thresh_low` | `animal_hunt_thresh_high` | per-episode |
| `lose_interest_multiplier` | `animal_lose_interest_low` | `animal_lose_interest_high` | per-episode |

`damage` is separately per-event (re-sampled on every collision hit) and uses `[lo, hi]` format stored in `animal_damage [N, 2]`.

### Jump/pounce feature (predator lunge attack)

Two further **OPTIONAL** fields on any entity (both default to a jump-disabled no-op) — see [PREDATOR_JUMP_MECHANISM.md](../develop/active/env_entities/PREDATOR_JUMP_MECHANISM.md) for the full design and JAX-correctness argument:

| YAML key | Meaning | Cadence | Array(s) |
|----------|---------|---------|----------|
| `attack_range` | scalar or `[lo, hi]` Manhattan-distance jump-trigger range. Missing → `[0,0]` (jump disabled). | per-episode, sampled from an **independent `fold_in` stream** — NOT part of the size-7 `ep_keys` split used by the five `DISTRIBUTIONAL_FIELDS` above | `animal_attack_range_low [N]`, `animal_attack_range_high [N]` (`EnvParams`) → `animal_attack_range_sampled [N]` (`EnvState`, sampled at reset) |
| `attack_success_rate` | float in `[0,1]`, probability a fired jump lands on the agent. Missing → `0.0`. | plain `EnvParams` leaf — **NOT per-episode sampled** | `animal_attack_success_rate [N]` |

Trigger (all must hold, evaluated in `_hunt_step`): predator in HUNT this step (post-transition `next_state==1`), agent within `attack_range_sampled` (Manhattan), agent not hidden in a bush, cooldown up (`attack_timer<=0`), and `attack_range_sampled>0`. A fired jump **replaces** that step's normal 1-cell chase move: on success the predator lands exactly on the agent (existing on-cell damage logic then applies, unchanged); on a miss it lands on a uniformly-random valid (in-bounds, non-blocking — bush cells count as valid) Chebyshev-1 neighbour of the agent, with a stay-put fallback. The cooldown (`attack_delay`, reused from the existing field) is set on **any** attempt, hit or miss.

The static `EnvParams.has_attack_feature` bool (True iff any animal has `attack_range_high>0`) gates the entire jump code path in `_hunt_step` at trace time — a disabled config (the default) takes the byte-identical pre-feature code path, guaranteeing PRNG-stream parity for every existing config.

### Index dispatch tuples (static)

After expansion the loader builds index tuples that allow `jax_reset` and `update_animals` to slice behaviour/class subsets without dynamic shapes:

| Tuple field | Content | Use |
|-------------|---------|-----|
| `hunt_idx` | global indices where `behaviour == 'hunt'` | hunt-specific update loop |
| `wander_idx` | global indices where `behaviour == 'wander'` | wander update loop |
| `static_idx` | global indices where `behaviour == 'static'` | static update (no-op) |
| `predator_indices` | global indices where `class == 'predator'` | placement, damage masking |
| `neutral_indices` | global indices where `class == 'neutral'` | placement |

All five are `pytree_node=False` (static).

### Canonical entity concat order for placement

`pred_spawn_area_for_placement` and `neutral_spawn_area_for_placement` are derived from `animal_spawn_area` by indexing with `predator_indices` / `neutral_indices` (`config_loader.py:587–594`). The global placement array is then built as:

```
all_spawn_areas = concat([res_spawn_area, pred_spawn_area_for_placement,
                          obs_spawn_area, neutral_spawn_area_for_placement])
```

This `[resources | predator-class | obstacles | neutral-class]` order determines each entity's **global index** in `type_entity_map` and must match `jax_reset`'s `all_positions` split.

### Legacy `predator_tags` / `neutral_tags`

These fields were removed from `EnvParams` as struct fields (M1/M2 fix). They are now derived via `@property` accessors on the struct (`state.py:234–247`) that filter `animal_tags` by class. Existing consumer code (e.g. `dreamer_srl_main.py:522–523`) continues to work until the accessors are removed in a future release.

---

## Implementation: `_load_animals`

`_load_animals` is the largest host-side function in the loader. It does all the Python-level work of detecting schema version, iterating entries, validating fields, and building the 32 JAX arrays that `load_env_params` unpacks. Everything in this function runs once at config-load time on the CPU; none of it is JIT-compiled.

`Source: src/environment/config_loader.py:202–278` (docstring + closure definitions)

```python
def _load_animals(config: Config):
    """Build unified animal arrays from the YAML config (v2.0).

    Supports two YAML paths, detected automatically:
      1. `environment.predators:` + `environment.neutral_animals:` (legacy) — all 86
         pre-v2.0 configs. Predators are re-projected with class='predator',
         behaviour='hunt'; neutrals with class='neutral', behaviour='wander'.
         The five distributional fields are read as scalars from the legacy YAML
         and stored as degenerate ranges [s, s]. `attack_delay` and `damage` for
         neutrals are internally auto-filled to 0 and [0.0, 0.0] (NC-1 fix —
         the legacy schema never carried them on neutral entries).
      2. `environment.entities:` (new schema) — now the canonical animal schema:
         the modern `configs/environment/default.yaml` base and the live
         basic-curriculum configs (`configs/environment/experiment/basic/`) use it.
         If detected, a deprecation warning is emitted when the legacy sections
         are also present (the unified `entities:` schema takes precedence).

    Returns a flat tuple of all unified `animal_*` arrays and dispatch tuples,
    ordered as expected by the `load_env_params` caller.

    YAML cadence notes:
      - `damage: [lo, hi]` is per-event (re-sampled on every collision).
      - `detection_range: [lo, hi]` (and four siblings in DISTRIBUTIONAL_FIELDS)
        are per-episode (re-sampled at reset). Cadence is determined by field name.

    Mandatory-key rule by behaviour:
      - `behaviour: hunt` — all five distributional fields are MANDATORY.
        Missing → ValueError (no fallback default, per project rule).
      - `behaviour: wander` / `static` — distributional fields are OPTIONAL.
        If missing, loader auto-fills [0, 0] (internal projection detail;
        the wander/static code path never reads these arrays at runtime).
      - Legacy `neutral_animals:` re-projection always behaves as wander/optional.

    v1.x → v2.0 semantic change note: `lose_interest_multiplier` was previously
    optional in the predator loader (soft default 2.0). It is now MANDATORY for
    `behaviour: hunt`. All 86 pre-v2.0 predator entries carry an explicit value,
    so no existing config breaks; this change is flagged for reference.
    """
    h = config.get_mandatory('environment.height')
    w = config.get_mandatory('environment.width')

    def _parse_area(area, default_h=h, default_w=w):
        a = area if area is not None else [[1, 1], [default_h, default_w]]
        return [a[0][0]-1, a[0][1]-1, a[1][0], a[1][1]]

    def _parse_distributional(entry, field, mandatory, entity_label, idx):
        """Read a scalar or [lo, hi] distributional field.
        Returns (low, high) as floats.
        """
        val = entry.get(field)
        if val is None:
            if mandatory:
                raise ValueError(
                    f"Animal entity {entity_label!r} (index {idx}) is missing mandatory "
                    f"distributional field '{field}' (required for behaviour='hunt'). "
                    f"No fallback default exists."
                )
            else:
                _log.debug(
                    "Animal entity %r (index %d): '%s' not specified; auto-filling [0, 0] "
                    "(wander/static — field is unused at runtime).", entity_label, idx, field
                )
                return 0.0, 0.0
        if isinstance(val, list):
            if len(val) != 2:
                raise ValueError(
                    f"Animal entity {entity_label!r} (index {idx}): '{field}' must be a scalar "
                    f"or a 2-element list [low, high]; got {val!r}."
                )
            lo, hi = float(val[0]), float(val[1])
            if hi < lo:
                raise ValueError(
                    f"Animal entity {entity_label!r} (index {idx}): '{field}' range "
                    f"must satisfy low <= high; got [{lo}, {hi}]."
                )
        else:
            lo = hi = float(val)
        return lo, hi

```

`Source: src/environment/config_loader.py:279–397` (entry-list construction — entities: path and legacy path)

```python
    # ── Build the expanded entry list ──────────────────────────────────────────
    entries = []  # list of dicts with unified fields

    # Check for new entities: schema (CP3 will add full support)
    has_entities = config.get('environment.entities') is not None
    has_legacy_predators = config.get('environment.predators') is not None
    has_legacy_neutrals = config.get('environment.neutral_animals') is not None

    if has_entities:
        # CP3 path — parse unified entities: list directly
        if has_legacy_predators or has_legacy_neutrals:
            warnings.warn(
                "Config has both 'environment.entities:' and legacy "
                "'environment.predators:'/'environment.neutral_animals:'. "
                "The unified 'entities:' schema takes precedence; legacy sections are ignored.",
                DeprecationWarning,
                stacklevel=3,
            )
        raw_entities = config.get('environment.entities') or []
        for i_raw, ent in enumerate(raw_entities):
            count = ent.get('count', 1)
            for _ in range(count):
                cls = ent.get('class')
                if cls is None:
                    raise ValueError(f"entities[{i_raw}]: missing required field 'class'.")
                beh = ent.get('behaviour')
                if beh is None:
                    raise ValueError(f"entities[{i_raw}]: missing required field 'behaviour'.")
                # Validate behaviour string FIRST (before building index tuples)
                if beh not in ANIMAL_BEHAVIOUR_TO_INT:
                    raise ValueError(
                        f"Unknown behaviour {beh!r} for entity tag={ent.get('tag', '?')}. "
                        f"Must be one of {list(ANIMAL_BEHAVIOUR_TO_INT)}."
                    )
                mandatory_dist = (beh == 'hunt')
                tag_raw = ent.get('tag')
                tag_label = str(tag_raw) if tag_raw else f'entity{len(entries)}'
                entries.append({
                    'class': cls,
                    'behaviour': beh,
                    'tag_raw': tag_raw,
                    'tag_label': tag_label,
                    'type_label': f'Entity[{i_raw}]',
                    'property': _read_properties(ent, f'Entity[{i_raw}]'),
                    'property_std': _read_properties_std(ent, f'Entity[{i_raw}]'),
                    'nociception': ent.get('nociception_intensity', 0.0),
                    'move_interval': ent.get('move_interval'),
                    'damage': ent.get('damage'),
                    'attack_delay': ent.get('attack_delay'),
                    'spawn_area': ent.get('spawn_area'),
                    'patrol_area': ent.get('patrol_area'),
                    'mandatory_dist': mandatory_dist,
                    'dist_source': ent,
                })
    else:
        # Legacy path: re-project predators (hunt) + neutrals (wander)
        raw_predators = config.get('environment.predators') or []
        for i_raw, p in enumerate(raw_predators):
            count = p.get('count', 1)
            for _ in range(count):
                tag_raw = p.get('tag')
                tag_label = str(tag_raw) if tag_raw else f'pred{len(entries)}'
                def _p_get(key, _p=p, _label=tag_label):
                    val = _p.get(key)
                    if val is None:
                        raise ValueError(
                            f"Strict Config: Predator (tag={_label!r}) field '{key}' is required."
                        )
                    return val
                entries.append({
                    'class': 'predator',
                    'behaviour': 'hunt',
                    'tag_raw': tag_raw,
                    'tag_label': tag_label,
                    'type_label': 'Predator',
                    'property': _read_properties(p, 'Predator'),
                    'property_std': _read_properties_std(p, 'Predator'),
                    'nociception': p.get('nociception_intensity', 0.9),
                    'move_interval': _p_get('move_interval'),
                    'damage': _p_get('damage'),
                    'attack_delay': _p_get('attack_delay'),
                    'spawn_area': p.get('spawn_area'),
                    'patrol_area': p.get('patrol_area'),
                    'mandatory_dist': True,  # hunt — all dist fields mandatory
                    'dist_source': p,
                })

        raw_neutrals = config.get('environment.neutral_animals') or []
        for i_raw, n in enumerate(raw_neutrals):
            count = n.get('count', 1)
            for _ in range(count):
                tag_raw = n.get('tag')
                tag_label = str(tag_raw) if tag_raw else f'rabbit{len(entries)}'
                def _n_get(key, _n=n, _label=tag_label):
                    val = _n.get(key)
                    if val is None:
                        raise ValueError(
                            f"Strict Config: Neutral Animal (tag={_label!r}) field '{key}' is required."
                        )
                    return val
                entries.append({
                    'class': 'neutral',
                    'behaviour': 'wander',
                    'tag_raw': tag_raw,
                    'tag_label': tag_label,
                    'type_label': 'Rabbit',
                    'property': _read_properties(n, 'Neutral Animal'),
                    'property_std': _read_properties_std(n, 'Neutral Animal'),
                    'nociception': n.get('nociception_intensity', 0.0),
                    'move_interval': _n_get('move_interval'),
                    # NC-1 fix: legacy neutrals never had damage/attack_delay;
                    # auto-fill internally (not user-facing fallback defaults).
                    'damage': [0.0, 0.0],
                    'attack_delay': 0,
                    'spawn_area': n.get('spawn_area'),
                    'patrol_area': n.get('patrol_area'),
                    'mandatory_dist': False,  # wander — dist fields optional
                    'dist_source': n,
                })
```

`Source: src/environment/config_loader.py:399–451` (zero-animal fast path)

```python
    N = len(entries)
    chem_dim = 5  # default; updated below if entries exist

    if N == 0:
        # Zero-animal case (M6 smoke) — return empty arrays
        animal_property = jnp.zeros((0, chem_dim))
        animal_property_std = jnp.zeros((0, chem_dim))
        animal_nociception = jnp.zeros(0)
        animal_move_int = jnp.zeros(0, dtype=jnp.int32)
        animal_damage = jnp.zeros((0, 2))
        animal_attack_delay = jnp.zeros(0, dtype=jnp.int32)
        animal_spawn_area = jnp.zeros((0, 4), dtype=jnp.int32)
        animal_patrol = jnp.zeros((0, 4), dtype=jnp.int32)
        animal_detect_low = jnp.zeros(0)
        animal_detect_high = jnp.zeros(0)
        animal_max_stamina_low = jnp.zeros(0)
        animal_max_stamina_high = jnp.zeros(0)
        animal_recovery_low = jnp.zeros(0)
        animal_recovery_high = jnp.zeros(0)
        animal_hunt_thresh_low = jnp.zeros(0)
        animal_hunt_thresh_high = jnp.zeros(0)
        animal_lose_interest_low = jnp.zeros(0)
        animal_lose_interest_high = jnp.zeros(0)
        animal_classes_int = jnp.zeros(0, dtype=jnp.int32)
        animal_behaviours_int = jnp.zeros(0, dtype=jnp.int32)
        animal_is_damaging = jnp.zeros(0, dtype=jnp.bool_)
        animal_visual_channel = jnp.zeros(0, dtype=jnp.int32)
        animal_classes = ()
        animal_behaviours = ()
        animal_tags = ()
        hunt_idx = ()
        wander_idx = ()
        static_idx = ()
        predator_indices = ()
        neutral_indices = ()
        pred_spawn_area_for_placement = jnp.zeros((0, 4), dtype=jnp.int32)
        neutral_spawn_area_for_placement = jnp.zeros((0, 4), dtype=jnp.int32)
        return (
            animal_property, animal_property_std, animal_nociception,
            animal_move_int, animal_damage, animal_attack_delay,
            animal_spawn_area, animal_patrol,
            animal_detect_low, animal_detect_high,
            animal_max_stamina_low, animal_max_stamina_high,
            animal_recovery_low, animal_recovery_high,
            animal_hunt_thresh_low, animal_hunt_thresh_high,
            animal_lose_interest_low, animal_lose_interest_high,
            animal_classes_int, animal_behaviours_int,
            animal_is_damaging, animal_visual_channel,
            animal_classes, animal_behaviours, animal_tags,
            hunt_idx, wander_idx, static_idx,
            predator_indices, neutral_indices,
            pred_spawn_area_for_placement, neutral_spawn_area_for_placement,
        )
```

`Source: src/environment/config_loader.py:453–611` (array construction and return)

```python
    # ── Build per-field arrays ─────────────────────────────────────────────────
    props_list = [_read_properties(e, e['tag_label']) if 'property' in e and not isinstance(e.get('property'), list) else e['property'] for e in entries]
    stds_list = [e['property_std'] for e in entries]
    chem_dim = len(props_list[0])

    noc_list = [float(e['nociception']) for e in entries]
    move_int_list = [int(e['move_interval']) for e in entries]

    damage_list = []
    for i, e in enumerate(entries):
        d = e['damage']
        if d is None:
            raise ValueError(
                f"Animal entity {e['tag_label']!r} (index {i}) is missing mandatory field 'damage'."
            )
        damage_list.append(d if isinstance(d, list) else [float(d), float(d)])

    attack_delay_list = []
    for i, e in enumerate(entries):
        a = e['attack_delay']
        if a is None:
            raise ValueError(
                f"Animal entity {e['tag_label']!r} (index {i}) is missing mandatory field 'attack_delay'."
            )
        attack_delay_list.append(int(a))

    spawn_list = [_parse_area(e['spawn_area'], h, w) for e in entries]
    patrol_list = [_parse_area(e['patrol_area'], h, w) for e in entries]

    # Distributional fields (per entry)
    dist_field_names = (
        ("detection_range", "animal_detect"),
        ("max_stamina", "animal_max_stamina"),
        ("stamina_recovery_rate", "animal_recovery"),
        ("hunt_stamina_threshold", "animal_hunt_thresh"),
        ("lose_interest_multiplier", "animal_lose_interest"),
    )
    dist_lows = {k: [] for _, k in dist_field_names}
    dist_highs = {k: [] for _, k in dist_field_names}
    for i, e in enumerate(entries):
        for yaml_key, arr_key in dist_field_names:
            lo, hi = _parse_distributional(
                e['dist_source'], yaml_key,
                mandatory=e['mandatory_dist'],
                entity_label=e['tag_label'], idx=i
            )
            dist_lows[arr_key].append(lo)
            dist_highs[arr_key].append(hi)

    # Class / behaviour codes
    classes_int_list = []
    behaviours_int_list = []
    is_damaging_list = []
    visual_channel_list = []
    classes_tuple = []
    behaviours_tuple = []
    tags_tuple = []
    hunt_idx_list = []
    wander_idx_list = []
    static_idx_list = []
    predator_idx_list = []
    neutral_idx_list = []

    for i, e in enumerate(entries):
        cls = e['class']
        beh = e['behaviour']
        # Validate behaviour string (for entities: path; legacy path is already validated)
        if beh not in ANIMAL_BEHAVIOUR_TO_INT:
            raise ValueError(
                f"Unknown behaviour {beh!r} for entity tag={e['tag_label']!r}. "
                f"Must be one of {list(ANIMAL_BEHAVIOUR_TO_INT)}."
            )
        if cls not in ANIMAL_CLASS_TO_INT:
            raise ValueError(
                f"Unknown class {cls!r} for entity tag={e['tag_label']!r}. "
                f"Must be one of {list(ANIMAL_CLASS_TO_INT)}."
            )
        classes_int_list.append(ANIMAL_CLASS_TO_INT[cls])
        behaviours_int_list.append(ANIMAL_BEHAVIOUR_TO_INT[beh])
        is_damaging_list.append(cls in ANIMAL_DAMAGING_CLASSES)
        visual_channel_list.append(ANIMAL_CLASS_TO_VIS_CHANNEL[cls])
        classes_tuple.append(cls)
        behaviours_tuple.append(beh)
        tags_tuple.append(_normalise_tag(e['tag_raw'], i, e.get('type_label', e['tag_label'])))

        if beh == 'hunt':
            hunt_idx_list.append(i)
        elif beh == 'wander':
            wander_idx_list.append(i)
        else:
            static_idx_list.append(i)

        if cls == 'predator':
            predator_idx_list.append(i)
        elif cls == 'neutral':
            neutral_idx_list.append(i)

    # Build JAX arrays
    animal_property = jnp.array(props_list, dtype=jnp.float32)
    animal_property_std = jnp.array(stds_list, dtype=jnp.float32)
    animal_nociception = jnp.array(noc_list, dtype=jnp.float32)
    animal_move_int = jnp.array(move_int_list, dtype=jnp.int32)
    animal_damage = jnp.array(damage_list, dtype=jnp.float32)
    animal_attack_delay = jnp.array(attack_delay_list, dtype=jnp.int32)
    animal_spawn_area = jnp.array(spawn_list, dtype=jnp.int32)
    animal_patrol = jnp.array(patrol_list, dtype=jnp.int32)

    animal_detect_low = jnp.array(dist_lows['animal_detect'], dtype=jnp.float32)
    animal_detect_high = jnp.array(dist_highs['animal_detect'], dtype=jnp.float32)
    animal_max_stamina_low = jnp.array(dist_lows['animal_max_stamina'], dtype=jnp.float32)
    animal_max_stamina_high = jnp.array(dist_highs['animal_max_stamina'], dtype=jnp.float32)
    animal_recovery_low = jnp.array(dist_lows['animal_recovery'], dtype=jnp.float32)
    animal_recovery_high = jnp.array(dist_highs['animal_recovery'], dtype=jnp.float32)
    animal_hunt_thresh_low = jnp.array(dist_lows['animal_hunt_thresh'], dtype=jnp.float32)
    animal_hunt_thresh_high = jnp.array(dist_highs['animal_hunt_thresh'], dtype=jnp.float32)
    animal_lose_interest_low = jnp.array(dist_lows['animal_lose_interest'], dtype=jnp.float32)
    animal_lose_interest_high = jnp.array(dist_highs['animal_lose_interest'], dtype=jnp.float32)

    animal_classes_int = jnp.array(classes_int_list, dtype=jnp.int32)
    animal_behaviours_int = jnp.array(behaviours_int_list, dtype=jnp.int32)
    animal_is_damaging = jnp.array(is_damaging_list, dtype=jnp.bool_)
    animal_visual_channel = jnp.array(visual_channel_list, dtype=jnp.int32)

    animal_classes = tuple(classes_tuple)
    animal_behaviours = tuple(behaviours_tuple)
    animal_tags = tuple(tags_tuple)

    hunt_idx = tuple(hunt_idx_list)
    wander_idx = tuple(wander_idx_list)
    static_idx = tuple(static_idx_list)
    predator_indices = tuple(predator_idx_list)
    neutral_indices = tuple(neutral_idx_list)

    # Per-class spawn areas for placement (N1 fix: jax_reset uses [res, pred, obs, neutral] order)
    pred_spawn_area_for_placement = (
        animal_spawn_area[jnp.array(list(predator_indices), dtype=jnp.int32)]
        if predator_indices else jnp.zeros((0, 4), dtype=jnp.int32)
    )
    neutral_spawn_area_for_placement = (
        animal_spawn_area[jnp.array(list(neutral_indices), dtype=jnp.int32)]
        if neutral_indices else jnp.zeros((0, 4), dtype=jnp.int32)
    )

    return (
        animal_property, animal_property_std, animal_nociception,
        animal_move_int, animal_damage, animal_attack_delay,
        animal_spawn_area, animal_patrol,
        animal_detect_low, animal_detect_high,
        animal_max_stamina_low, animal_max_stamina_high,
        animal_recovery_low, animal_recovery_high,
        animal_hunt_thresh_low, animal_hunt_thresh_high,
        animal_lose_interest_low, animal_lose_interest_high,
        animal_classes_int, animal_behaviours_int,
        animal_is_damaging, animal_visual_channel,
        animal_classes, animal_behaviours, animal_tags,
        hunt_idx, wander_idx, static_idx,
        predator_indices, neutral_indices,
        pred_spawn_area_for_placement, neutral_spawn_area_for_placement,
    )
```

> **API notes — host—device boundary**
> Every `jnp.array(python_list, dtype=...)` call above is the host—device transfer point. The Python lists assembled from YAML (NumPy-free, pure Python) are handed to `jnp.array`, which allocates a device buffer and copies the data. After this call the data lives on the accelerator and is immutable. The returned arrays become pytree leaves of `EnvParams`; from this point on, JAX traces through them rather than re-reading Python. See [primer: JAX pytrees](00_jax_primer.md#jax-pytrees) and [primer: static vs dynamic fields](00_jax_primer.md#static-dynamic).
>
> The five dispatch tuples (`hunt_idx`, `wander_idx`, etc.) are Python `tuple`s of ints, not arrays. They are stored as `pytree_node=False` static fields on `EnvParams`, meaning JIT bakes their contents into the compiled binary as constants. If you change the number of hunt animals the compiled function must be discarded and retraced. See [primer: static vs dynamic fields](00_jax_primer.md#static-dynamic).
>
> The `for yaml_key, arr_key in dist_field_names` loop at lines 492–500 is a plain Python loop — it runs at config-load time, not inside a JIT kernel. The resulting `_low`/`_high` arrays are then used by a `lax.scan` in `jax_reset` at runtime. See [primer: scan](00_jax_primer.md#scan).


---

## Implementation: coordinate conversion and olfactory key helpers

### `_parse_area` — 1-based inclusive —— 0-based exclusive

`_parse_area` is a local closure defined inside `_load_animals`. It converts the human-readable 1-based inclusive YAML format into the 0-based exclusive format that `jax.random.randint` expects.

`Source: src/environment/config_loader.py:241–243`

```python
    def _parse_area(area, default_h=h, default_w=w):
        a = area if area is not None else [[1, 1], [default_h, default_w]]
        return [a[0][0]-1, a[0][1]-1, a[1][0], a[1][1]]
```

The formula: subtract 1 from the lower-left coordinates to convert 1-based —— 0-based, but leave the upper-right coordinates unchanged —— `randint(minval, maxval)` already treats `maxval` as exclusive, so the 1-based inclusive upper bound `[r2, c2]` is used directly as the exclusive upper bound. YAML `[[1,1],[5,5]]` —— stored `[0, 0, 5, 5]` (rows 0–4, cols 0–4).

> **API notes**
> `jax.random.randint(key, shape, minval, maxval)` draws integers in `[minval, maxval)`. The 0-based exclusive convention keeps the stored area spec directly usable by `randint` without any further arithmetic at reset time. See [primer: PRNG](00_jax_primer.md#prng).

---

### `_read_properties` / `_read_properties_std` — olfactory key rename shim

These two small helpers enforce the `property` —— `properties` rename and emit a `DeprecationWarning` for old YAML keys. They are used everywhere a chemical signature is read (resources, animals, obstacles).

`Source: src/environment/config_loader.py:176–200`

```python
def _read_properties(entry, entity_label):
    """Read olfactory signature, preferring `properties` (plural)."""
    if 'properties' in entry:
        return entry['properties']
    if 'property' in entry:
        warnings.warn(
            f"{entity_label}: YAML key 'property' is deprecated — rename to 'properties'.",
            DeprecationWarning,
            stacklevel=2,
        )
        return entry['property']
    raise ValueError(f"{entity_label}: missing required key 'properties'.")

def _read_properties_std(entry, entity_label):
    """Same, for the `*_std` variant."""
    if 'properties_std' in entry:
        return entry['properties_std']
    if 'property_std' in entry:
        warnings.warn(
            f"{entity_label}: YAML key 'property_std' is deprecated — rename to 'properties_std'.",
            DeprecationWarning,
            stacklevel=2,
        )
        return entry['property_std']
    raise ValueError(f"{entity_label}: missing required key 'properties_std'.")
```

> **API notes**
> Python's `warnings.warn(..., DeprecationWarning, stacklevel=2)` sets `stacklevel=2` so the warning points at the *caller's* line (e.g. the resource loop in `load_env_params`) rather than at the inside of this helper — making it actionable in the log output. The returned list is later passed to `jnp.array(...)` by the caller.


---

## Entity Count Expansion

Each entity definition in YAML carries an optional `count` field (default `1`). The loader expands each definition `count` times into a flat list before building JAX arrays. `count: 0` produces zero expansions — a clean way to disable an entity kind without deleting its YAML block.

When an entity list is empty (e.g. no animals configured), the loader builds zero-size arrays of the correct dtype and shape so `jax.vmap` does not need entity-count conditionals.

### Per-episode count ranges (v3.0 PER\_EPISODE\_ENV\_VARIANCE)

An entity entry may declare a **count range** instead of a fixed `count`, causing the engine to redraw the actual count K at every episode reset:

| YAML keys | Meaning | Fallback |
|-----------|---------|---------|
| `count_low: L` + `count_high: H` | allocate H slots; draw K ∈ [L, H] at reset | — |
| `count: N` only | degenerate range: `count_low = count_high = N` → K always N; byte-identical to pre-v3.0 | — |
| neither | `count_low = count_high = 1` (same as `count: 1`) | — |
| both `count` and `count_low`/`count_high` present | `ValueError` (ambiguous) | — |

**Slot allocation.** The loader always allocates `count_high` slots — the JAX array shape is static. The surplus `count_high − K` slots are marked inactive each episode via three boolean masks stored in `EnvState`:

| Mask | Shape | Guards |
|------|-------|--------|
| `res_active` | `[num_res]` bool | resource sensing (olfaction, extero-noc, visual), interaction logic |
| `animal_active` | `[num_animal]` bool | animal movement, damage, olfaction, visual, distance metrics |
| `obs_active` | `[num_obs]` bool | obstacle collision, damage, bush concealment, visual, olfaction |

Inactive slots are also **parked off-grid** (position set to `(height, width)`) so they cannot physically overlap the agent or resolve-overlaps candidates.

**Per-entry K-draw.** K is drawn **per YAML entry** from a `fold_in`-derived PRNG key in `jax_reset`, after the existing animal-field draws. The draw is **skipped** when every entry in a class is degenerate (ensures byte-identical PRNG streams for configs that use only `count: N`).

**EnvParams fields added for count ranges:**

| Field | Shape | Class | Notes |
|-------|-------|-------|-------|
| `res_count_low` | `[num_res_entries]` int | resource | per-entry lower bound |
| `res_count_high` | `[num_res_entries]` int | resource | per-entry upper bound = allocation per entry |
| `res_entry_id` | `[num_res]` int | resource | maps each slot to its entry |
| `has_res_range` | scalar bool | resource | True if any entry has `count_low < count_high` |
| `animal_count_low` | `[num_animal_entries]` int | animal | per-entry lower bound |
| `animal_count_high` | `[num_animal_entries]` int | animal | per-entry upper bound |
| `animal_entry_id` | `[num_animal]` int | animal | maps each slot to its entry |
| `has_animal_range` | scalar bool | animal | True if any entry has range |
| `obs_count_low` | `[num_obs_entries]` int | obstacle | per-entry lower bound |
| `obs_count_high` | `[num_obs_entries]` int | obstacle | per-entry upper bound |
| `obs_entry_id` | `[num_obs]` int | obstacle | maps each slot to its entry |
| `has_obs_range` | scalar bool | obstacle | True if any entry has range |

---

## Resource Entity Fields

Each entry under `environment.resources` (after `count` expansion):

| YAML key | EnvParams field | Mandatory | Notes |
|----------|----------------|-----------|-------|
| `type` | `res_type [N]` int | yes | `"food"` → 0, `"hiding_predator"` → 1; `"danger"` → DeprecationWarning then 1 |
| `properties` | `res_property [N, V]` | yes | olfactory chemical signature |
| `properties_std` | `res_property_std [N, V]` | yes | std dev for per-episode sampling |
| `spawn_area` | `res_spawn_area [N, 4]` | yes | 1-based → 0-based exclusive |
| `max_consumption` | `res_max_cons [N]` | yes | steps until resource depletes |
| `regeneration_delay` | `res_reg_delay [N]` | yes | steps before respawn |
| `damage` | `res_damage [N, 2]` | yes | `[lo, hi]` per-event; scalar → `[s, s]` |
| `nociception_intensity` | `res_nociception [N]` | optional | default `0.9` for hiding\_predator/danger, `0.0` for food |
| `count` | (expansion only) | optional | default `1`; mutually exclusive with `count_low`/`count_high` |
| `count_low` | `res_count_low [E]` (per-entry) | optional | v3.0: per-episode lower bound; requires `count_high`; absence → `count` fallback |
| `count_high` | `res_count_high [E]` (per-entry) | optional | v3.0: per-episode upper bound = slot allocation; requires `count_low` |
| `temperature` | `res_temperature [N]` | optional | thermal: absolute heat stamped into the field (default `0.0`). Mutually exclusive with `temperature_ratio` |
| `temperature_ratio` | `res_temp_ratio_low/high [N]` | optional | thermal: `[low, high]`; heat = `ratio × abs(default_temp)`, drawn per slot per episode |

**Animals carry no temperature array.** `temperature` / `temperature_ratio` on an animal
entry **raises at load**, naming the entity. The thermal field is built once at reset from
static positions and animals move, so a moving heat source is a promise the mechanism
cannot keep — and a key that loaded and did nothing would read as a broken feature.

---

## Obstacle Entity Fields

Each entry under `environment.obstacles` (after `count` expansion):

| YAML key | EnvParams field | Mandatory | Default | Notes |
|----------|----------------|-----------|---------|-------|
| `area` | `obs_spawn_area [N, 4]` | yes | — | 1-based → 0-based exclusive |
| `properties` | `obs_property [N, V]` | yes | — | olfactory signature |
| `properties_std` | `obs_property_std [N, V]` | yes | — | std dev |
| `blocking` | `obs_blocking [N]` bool | optional | `True` | blocks movement for both agent and animals |
| `hides_agent` | `obs_hides_agent [N]` bool | optional | `False` | bush-type concealment |
| `blocks_animals` | `obs_blocks_animals [N]` bool | optional | `False` (loader) — but `default.yaml` ships **`true`** on the bush | blocks animal movement; agent still enters freely. See the note below. |
| `damage` | `obs_damage [N, 2]` | optional | `0.0` → `[0,0]` | per-event damage range |
| `nociception_intensity` | `obs_nociception [N]` | optional | `0.3` | |
| `name` | `obs_type [N]` int | optional | `"rock"` | index into `obstacle_names` |
| `count` | (expansion only) | optional | `1` | mutually exclusive with `count_low`/`count_high` |
| `count_low` | `obs_count_low [E]` (per-entry) | optional | — | v3.0: per-episode lower bound; requires `count_high` |
| `count_high` | `obs_count_high [E]` (per-entry) | optional | — | v3.0: per-episode upper bound = slot allocation | |
| `temperature` | `obs_temperature [N]` | optional | `0.0` | thermal: absolute heat stamped into the field. Mutually exclusive with `temperature_ratio` |
| `temperature_ratio` | `obs_temp_ratio_low/high [N]` | optional | `[0, 0]` | thermal: `[low, high]`; heat = `ratio × abs(default_temp)`, ratio drawn per slot per episode. Mutually exclusive with `temperature` |
| `edge_margin` | (transforms `area` at load) | optional | `0` | thermal: insets `area` by N cells on all four sides **at load time**; an empty intersection raises |


**`blocks_animals`: the loader default and the shipped value differ, on purpose.** The loader
reads it as `o.get('blocks_animals', False)` (`config_loader.py:1851`) while
`configs/environment/default.yaml` ships `blocks_animals: true` on the bush entry. That is not
drift — it is a **deliberate, dated exception** to the project's no-fallback-defaults rule,
recorded in
[CONFIG_CRITICAL_SETTINGS.md](CONFIG_CRITICAL_SETTINGS.md) (registry row + the 2026-09-14
change-log entry). Making the key mandatory would raise at load on every config that
redeclares its own `obstacles:` list without spelling the key out, which is a project-wide
migration the owning change deliberately did not take on.

The consequence you must hold in mind when authoring: because lists **replace** wholesale
(see [CONFIG_GUIDE.md](CONFIG_GUIDE.md) §1), a config that redeclares `obstacles:` and omits
`blocks_animals` gets `false` — it does **not** inherit the base's `true`, and nothing warns
you. If your config declares its own obstacle list and contains a `hides_agent: true` bush,
**write `blocks_animals: true` explicitly**. Every maintained world does.

`obs_blocks_animals` is merged into the ANIMAL movement mask only
(`obs_block_for_animals = obs_blocking | obs_blocks_animals`, `core.py:560`) and is **not**
read by any placement validity mask, so animals can still *spawn* on a blocking bush.

`obstacle_names` is the **sorted unique** tuple of all obstacle `name` values (`config_loader.py:1876`). Renaming an obstacle can shift its index — don't hardcode indices outside the config.

---

## Placement Configuration

Controlled by `environment.placement.mode` (`config_loader.py:779`):

| Mode | Description | Best for |
|------|-------------|----------|
| `per_entity` | vmap sample per entity → `resolve_overlaps_global` sequential scan | Small grids (≤100 cells) |
| `per_type` | `lax.scan` over spawn-area groups via `place_in_area` | Large grids or high entity density |

`placement_mode` is a **static** field — changing it forces JIT recompilation.

**Type group construction** (always built, regardless of mode): entities are grouped by their spawn-area bounding box. Entities with identical bounding boxes share a group, across all entity kinds.

| EnvParams field | Shape | Static | Description |
|----------------|-------|--------|-------------|
| `type_areas` | `[T, 4]` | no | one bounding box per group (0-based exclusive) |
| `type_counts` | `[T]` | no | entity count per group |
| `type_entity_map` | `[T, max_per_type]` | no | global entity indices (0-padded) |
| `max_per_type` | scalar | **yes** | maximum entities in any single group |
| `num_types` | scalar | **yes** | number of groups T |
| `num_entities` | scalar | **yes** | total entity count across all types |

---

## Coordinate Convention and Area Parsing

YAML area specifications use **1-based inclusive coordinates** in the format `[[row_min, col_min], [row_max, col_max]]`. The helper `_parse_area()` (`config_loader.py:241–243`) converts these to **0-based with exclusive upper bound** for JAX's `jax.random.randint`:

```python
[a[0][0]-1, a[0][1]-1, a[1][0], a[1][1]]
```

Example: YAML `[[1,1],[5,5]]` → stored as `[0, 0, 5, 5]` (rows 0–4, cols 0–4).

`location_areas` uses the same convention applied via numpy slice (`grid_np[r1-1:r2, c1-1:c2]`, `config_loader.py:748`). Later entries overwrite earlier ones at overlapping cells (last writer wins).

---

## Mandatory Key Reference

All keys accessed via `config.get_mandatory()` — missing → `ValueError` with no fallback.

### `load_env_params` mandatory keys

```
environment.height                     environment.width
environment.max_steps                  environment.start_pos
environment.random_start_pos           environment.rest_action_enabled
environment.eat_action_enabled         environment.resources
environment.obstacles                  environment.location_areas

body.max_satiation                     body.max_nutrition
body.max_injury                        body.food_nutrition_gain
body.satiation_setpoint                body.start_satiation
body.start_nutrition                   body.metabolic_cost
body.nutrition_to_satiation_scaling_factor
body.recovery_base_rate                body.recovery_accel_rate
body.recovery_in_bush_multiplier
body.healing_nutrition_cost            body.healing_nutrition_dependence
body.injury_smoothing_duration         body.death_penalty
body.overeating_death                  body.use_homeostatic_reward
body.with_satiation                    body.with_nutrition
body.with_injury                       body.random_start_satiation
body.random_start_nutrition            body.random_start_injury
body.eating_nutrition_cost             body.eating_reward_penalty

sensory.sensor_radius                  sensory.decay_power
sensory.collision_sensor_range         sensory.visual_sensor_enabled
sensory.visual_sensor_range            sensory.olfactory_enabled
sensory.nociception_enabled            sensory.proprioception_enabled
sensory.location_sensor                sensory.vector_size
sensory.nociception_size               sensory.injury_observable
sensory.nutrition_observable           sensory.interoceptive_nociception_enabled
sensory.interoceptive_convolution_enabled
sensory.interoceptive_kernel_length    sensory.interoceptive_kernel_tau

visualization.local_view_size

thermal.enabled
water.enabled
```

**Water conditional keys** (2026-09-30, [[thirst_water_plan]]): only when `water.enabled` is
true: `water.placement`, `water.size`, `water.edge_margin`, `water.max_hydration`,
`water.hydration_setpoint`, `water.random_start_hydration`, `water.drain_per_step`,
`water.drink_gain_per_step`, `water.properties`, `water.visual_properties`; additionally
`water.candidates` only when `placement` is `list`, `water.start_hydration` only when the random
flag is false, `water.start_hydration_low` / `_high` only when it is true. See the "Water"
section above for validation.

**Conditional-mandatory — read ONLY when `thermal.enabled` is true:**

```
thermal.sigma                          thermal.default_temp
thermal.use_random_spots               thermal.use_object_sources
thermal.min_fire_separation            thermal.food_min_fire_distance
thermal.bush_min_fire_distance
thermal.temperature_setpoint           thermal.min_temperature
thermal.max_temperature                thermal.k_exchange
thermal.k_loss                         thermal.k_metabolic
thermal.metabolic_coupling             thermal.grid_range
thermal.relative                       thermal.warming_rate_scale
thermal.cooling_rate_scale             thermal.random_start_body_temp
thermal.healing_cold_sensitivity       thermal.healing_warm_sensitivity
thermal.injury_heat_exchange_gain
```

and, only when `thermal.random_start_body_temp` is true: `thermal.start_body_temp_low`,
`thermal.start_body_temp_high`; only when `thermal.injury_heat_exchange_gain > 0`:
`thermal.injury_heat_exchange_mode`.

**Body-mechanics conditional keys** (2026-09-26): only when `body.healing_nutrition_cost > 0`:
`body.healing_nutrition_shortfall`; only when `body.healing_nutrition_dependence` is true:
`body.healing_hunger_low`, `body.healing_hunger_high`, `body.healing_hunger_floor`,
`body.healing_overfull_floor`, and — only when that floor is `< 1` —
`body.healing_overfull_start`.

and, only when `thermal.use_random_spots` is true:

```
thermal.random_spots.count             thermal.random_spots.size
thermal.random_spots.temp
```

and, only when `thermal.metabolic_coupling` is true:

```
thermal.metabolic_coupling_rate
```

`thermal.enabled` itself is **unconditionally mandatory** and has no fallback default —
`config.get('thermal.enabled', False)` is explicitly forbidden, because a fallback on a
gating key would let a config with a misspelled `thermal:` block train as if thermal were
off. Every key in `default.yaml`'s `thermal:` block is now read.

**Satiation / nutrition axis validation** (added 2026-09-22; raises `ValueError` naming the
offending key, at load, in `config_loader.py` beside the existing start-range checks):

| Key | Type | Validation |
|---|---|---|
| `body.max_satiation` | float | must be `> 0`. The homeostatic drive divides by `range_S = max(satiation_setpoint, max_satiation − satiation_setpoint)`; a zero-width axis makes that divisor 0, so the logged `drive_hunger` becomes `0/0 → NaN` **inside the jitted step**, with no traceback pointing at the config |
| `body.max_nutrition` | float | must be `> 0`. Nutrition is clipped into `[0, max_nutrition]` and death fires at **both** ends of that interval |
| `body.satiation_setpoint` | float | must satisfy `0 <= satiation_setpoint <= max_satiation`. A setpoint above the ceiling is unreachable — satiation is clipped below it — so the drive can never reach zero and the agent is punished forever for a state it cannot leave. All three loaded silently before this check existed |
| `body.start_nutrition_low` / `_high` | float | conditional on `body.random_start_nutrition`; must satisfy `0 <= low <= high <= max_nutrition` |
| `body.start_injury_low` / `_high` | float | conditional on `body.random_start_injury`; must satisfy `0 <= low <= high <= max_injury` |

**Thermal-block validation** (all raise `ValueError` naming the offending key, at the point
the key is read):

| Key | Type | Validation |
|---|---|---|
| `thermal.temperature_setpoint` | float | must lie inside `[min_temperature, max_temperature]` — a setpoint outside the survivable band makes the body's own resting state lethal |
| `thermal.min_temperature` | float | must be `< max_temperature` |
| `thermal.max_temperature` | float | — (also the drive's thermal scale: the third homeostatic axis is `(T − temperature_setpoint) · range_S / max_temperature`, where `range_S = max(satiation_setpoint, max_satiation − satiation_setpoint)` is the furthest satiation can get from its own target. So this key sets the warmth-vs-hunger exchange rate as well as the survivable band — **6.67 satiation units per degree** at the shipped `range_S = 100`. It reads `range_S` and not `max_satiation`, which matters since 2026-09-22: the ceiling doubled to 200 while the setpoint stayed at 100, so `max_satiation` would have silently doubled this factor. See CONFIG_GUIDE.md) |
| `thermal.k_exchange` | float | `>= 0`, and `k_exchange + k_loss <= 1` |
| `thermal.k_loss` | float | `>= 0`, and `k_exchange + k_loss <= 1` (above 1 the discrete update overshoots its own fixed point every step and body temperature oscillates instead of settling) |
| `thermal.warming_rate_scale` | float | `> 0` (written `not (x > 0)`, so NaN is rejected), and `warming_rate_scale × (k_exchange + k_loss) <= 1`, checked per key with an error naming this key. Multiplies the body's whole per-step change when it is positive; 1.0 / 1.0 is the single-rate body |
| `thermal.cooling_rate_scale` | float | `> 0` (NaN rejected), and `cooling_rate_scale × (k_exchange + k_loss) <= 1`, checked per key with an error naming this key. Multiplies the whole per-step change when it is zero or negative |
| `thermal.k_metabolic` | float | — (may be any sign; still zero — the metabolic coupling below runs the other way, charging nutrition for defence rather than feeding heat back into the body) |
| `thermal.metabolic_coupling` | bool | — (gate; when true, defending body temperature drains nutrition. **Static** — it gates a Python `if` in `update_body`, so with it false the drain contributes nothing to the traced graph) |
| `thermal.metabolic_coupling_rate` | float | `>= 0`, read **only** when `metabolic_coupling` is true. Nutrition units drawn per degree-per-step of thermoregulatory defence: the per-step drain is `rate * \|k_loss * (body_temp − temperature_setpoint)\|`, charged inside the `with_nutrition` block after the linear decay and before the food refill and the single clip to `[0, max_nutrition]`. A negative rate would pay the agent for being cold |

**State-dependent body mechanics** (2026-09-26, [[STATE_DEPENDENT_BODY_MECHANICS]]). Fifteen
keys, all **static** `EnvParams` fields behind trace-time `if`s (floats `float()`-coerced,
strings checked against their enum), so at the off values the step/reset jaxprs are the
pre-change strings. Validation raises `ValueError` naming the key:

| Key | Type | Read when | Validation / meaning |
|---|---|---|---|
| `thermal.random_start_body_temp` (B1) | bool | `thermal.enabled` | must be a YAML bool. True: `jax_reset` draws the start body temperature uniformly from the range below using `body_key1` (split, previously unused — no existing stream moves) |
| `thermal.start_body_temp_low` / `_high` | float | B1 flag true | finite, `min_temperature <= low <= high <= max_temperature`. Pin a start with `low == high`; there is no fixed-start key |
| `thermal.healing_cold_sensitivity` (B2) | float | `thermal.enabled` | `>= 0` (NaN refused). Fraction of recovery lost per °C the **pre-step** body is below `temperature_setpoint` |
| `thermal.healing_warm_sensitivity` (B2) | float | `thermal.enabled` | `>= 0` (NaN refused). Same, above the setpoint. Factor `w = max(0, 1 − s_c·max(0, T_set−T) − s_w·max(0, T−T_set))` multiplies recovery after the bush premium |
| `thermal.injury_heat_exchange_gain` (B4) | float | `thermal.enabled` | `>= 0` (NaN refused); `> 0` requires `body.with_injury` and `scale·(k_exchange·(1+gain) + k_loss) <= 1` for **both** scales (a refusal). `k_exchange' = k_exchange·(1 + gain·injury/max_injury)` on the pre-step injury; scales `k_exchange`, **not** `k_loss` |
| `thermal.injury_heat_exchange_mode` | str | gain `> 0` | `cooling_only` (boost only while the cell is colder than the body) or `both`. With `gain > 0` the structure check is repeated at full injury and **logged** (WARNING "at full injury — allowed by configuration"), never raised; in `both` mode the worst first step onto a fire is logged too |
| `body.healing_nutrition_cost` (B3) | float | always | `>= 0` (NaN refused); `> 0` requires `with_nutrition` and `with_injury`. Nutrition charged per injury point healed, before the single nutrition clip |
| `body.healing_nutrition_shortfall` | str | cost `> 0` | `partial` (heal `min(h_nom, max(N_pre,0)/c)`; starvation judged **before** the charge, so the charge never kills — an agent can be alive at `N = 0`) or `full` (heal fully; a shortfall lands on 0 and starves, reason 2) |
| `body.healing_nutrition_dependence` (B5) | bool | always | must be a YAML bool; true requires `with_nutrition` and `with_injury`. Recovery × `f_hunger(N)·f_over(N)` on the **pre-step** nutrition (before this step's decay) |
| `body.healing_hunger_low` / `_high` | float | B5 on | `0 <= low < high <= max_nutrition`; factor is the floor at/below `low`, 1 at/above `high` |
| `body.healing_hunger_floor` | float | B5 on | `[0, 1]` (NaN refused) |
| `body.healing_overfull_floor` | float | B5 on | `[0, 1]`; `1.0` = being over-full does not slow healing |
| `body.healing_overfull_start` | float | B5 on and overfull floor `< 1` | `healing_hunger_high <= start < max_nutrition` (the ramps cannot overlap) |

With B1 on (or B4 in `both` mode) the loader logs the worst-case first step onto a single fire,
`T_1 = T_high + s_w·(k_ex'·(F_max − T_high) − k_loss·(T_high − T_set) + k_met)`, at INFO — or
WARNING when `T_1 > max_temperature`; it never refuses. Level 05's B1 range [−10, +5] logs
+10.78. Saved run configs that predate these keys are re-opened through
`src/environment/saved_config_compat.py` (CONFIG_GUIDE §5).

The first eight drive the body-temperature recurrence documented in
[05_body_homeostasis.md](05_body_homeostasis.md#body-temperature-thermal), and leaving the
band `[min_temperature, max_temperature]` ends the episode with **termination code 5**
([06_reward_and_termination.md](06_reward_and_termination.md)). From Stage 4 the first two also
enter the **reward**: `calculate_drive` is three-axis when `thermal.enabled` is true, and
`info['drive_thermal']` — the squared normalised deviation
`((T − temperature_setpoint)/max_temperature)²`, matching `drive_hunger` / `drive_injury` —
is emitted alongside them, only when thermal is on.

**Removed in v2.0 (raises `ValueError` if present):** `environment.predator_enabled`

**Not mandatory at top-level but required by `_load_animals`:**  
`environment.height`, `environment.width` (re-read for default area bounds, `config_loader.py:238–239`).

### `load_behavior_measure_cfg` mandatory keys (14 total)

Applies only when `behavior_measures:` block is present in the YAML. If absent, the function returns `None` (feature off, backward-compatible).

```
behavior_measures.enabled              behavior_measures.cue_radius
behavior_measures.obs_window           behavior_measures.eval_n_episodes
behavior_measures.eval_seeds           behavior_measures.eval_policy_mode
behavior_measures.eval_max_steps       behavior_measures.eval_obs_noise
behavior_measures.motif_window_K       behavior_measures.motif_features
behavior_measures.motif_kmeans_k       behavior_measures.motif_kmeans_seed
behavior_measures.motif_standardise    behavior_measures.eval_output_root
```

Validated enum fields:

| Key | Allowed values |
|-----|---------------|
| `eval_policy_mode` | `"deterministic"`, `"stochastic"` |
| `eval_obs_noise` | `"training"`, `"zero"`, `"custom"` |
| `motif_standardise` | `"zscore_pooled"`, `"zscore_per_agent"`, `"none"` |
| `motif_features` | non-empty subset of the 10 v1 names in `_DEFAULT_FEATURE_NAMES` (`config_loader.py:70–75`) |

Additional constraints: `cue_radius > 0`, `obs_window >= 1`, `eval_n_episodes >= 1`, `len(eval_seeds) == eval_n_episodes`, seeds unique, `eval_max_steps >= 1`, `motif_window_K >= 1`, `motif_kmeans_k >= 2`.

---

## Implementation: `load_behavior_measure_cfg`

This function is the schema guardian for the optional behavior-measure toolkit. It returns `None` immediately if the `behavior_measures:` YAML block is absent, making it backward-compatible with every pre-feature config. When the block is present, every field is mandatory and the function validates enums, ranges, seed counts, and feature names before constructing a frozen `BehaviorMeasureCfg` dataclass.

`Source: src/environment/config_loader.py:78–155`

```python
def load_behavior_measure_cfg(config) -> "BehaviorMeasureCfg | None":
    """Load behavior_measures: from the YAML config.

    Returns None if the top-level key is absent (backwards compatibility — existing
    configs that pre-date this feature load unchanged).  If the block IS present,
    every leaf key is mandatory and missing keys raise ValueError.
    """
    if config.get("behavior_measures") is None:
        return None  # backwards-compat: feature off, online accumulators no-op.

    enabled         = config.get_mandatory("behavior_measures.enabled")
    cue_radius      = config.get_mandatory("behavior_measures.cue_radius", float)
    obs_window      = config.get_mandatory("behavior_measures.obs_window", int)
    eval_n_eps      = config.get_mandatory("behavior_measures.eval_n_episodes", int)
    eval_seeds_raw  = config.get_mandatory("behavior_measures.eval_seeds")
    eval_pol_mode   = config.get_mandatory("behavior_measures.eval_policy_mode")
    eval_max_steps  = config.get_mandatory("behavior_measures.eval_max_steps", int)
    eval_obs_noise  = config.get_mandatory("behavior_measures.eval_obs_noise")
    motif_K         = config.get_mandatory("behavior_measures.motif_window_K", int)
    motif_features  = config.get_mandatory("behavior_measures.motif_features")
    motif_k         = config.get_mandatory("behavior_measures.motif_kmeans_k", int)
    motif_seed      = config.get_mandatory("behavior_measures.motif_kmeans_seed", int)
    motif_std       = config.get_mandatory("behavior_measures.motif_standardise")
    eval_output     = config.get_mandatory("behavior_measures.eval_output_root")

    # ----- validation -----
    if cue_radius <= 0:
        raise ValueError(f"behavior_measures.cue_radius must be > 0; got {cue_radius}.")
    if obs_window < 1:
        raise ValueError(f"behavior_measures.obs_window must be >= 1; got {obs_window}.")
    if eval_n_eps < 1:
        raise ValueError(f"behavior_measures.eval_n_episodes must be >= 1; got {eval_n_eps}.")
    if not isinstance(eval_seeds_raw, (list, tuple)):
        raise ValueError(f"behavior_measures.eval_seeds must be a list/tuple; got {type(eval_seeds_raw)}.")
    if len(eval_seeds_raw) != eval_n_eps:
        raise ValueError(
            f"behavior_measures.eval_seeds length ({len(eval_seeds_raw)}) != eval_n_episodes ({eval_n_eps})."
        )
    eval_seeds = tuple(int(s) for s in eval_seeds_raw)
    if len(set(eval_seeds)) != len(eval_seeds):
        raise ValueError("behavior_measures.eval_seeds contains duplicates.")
    if eval_pol_mode not in _ALLOWED_POLICY_MODES:
        raise ValueError(f"behavior_measures.eval_policy_mode must be in {_ALLOWED_POLICY_MODES}; got {eval_pol_mode!r}.")
    if eval_max_steps < 1:
        raise ValueError(f"behavior_measures.eval_max_steps must be >= 1; got {eval_max_steps}.")
    if eval_obs_noise not in _ALLOWED_NOISE_MODES:
        raise ValueError(f"behavior_measures.eval_obs_noise must be in {_ALLOWED_NOISE_MODES}; got {eval_obs_noise!r}.")
    if motif_K < 1:
        raise ValueError(f"behavior_measures.motif_window_K must be >= 1; got {motif_K}.")
    if not motif_features or not all(isinstance(f, str) for f in motif_features):
        raise ValueError("behavior_measures.motif_features must be a non-empty list of strings.")
    unknown_features = set(motif_features) - set(_DEFAULT_FEATURE_NAMES)
    if unknown_features:
        raise ValueError(
            f"behavior_measures.motif_features contains unknown names: {sorted(unknown_features)}. "
            f"Allowed v1 features: {_DEFAULT_FEATURE_NAMES}."
        )
    if motif_k < 2:
        raise ValueError(f"behavior_measures.motif_kmeans_k must be >= 2; got {motif_k}.")
    if motif_std not in _ALLOWED_STANDARDISE:
        raise ValueError(f"behavior_measures.motif_standardise must be in {_ALLOWED_STANDARDISE}; got {motif_std!r}.")

    return BehaviorMeasureCfg(
        enabled=bool(enabled),
        cue_radius=float(cue_radius),
        obs_window=int(obs_window),
        eval_n_episodes=int(eval_n_eps),
        eval_seeds=eval_seeds,
        eval_policy_mode=str(eval_pol_mode),
        eval_max_steps=int(eval_max_steps),
        eval_obs_noise=str(eval_obs_noise),
        motif_window_K=int(motif_K),
        motif_features=tuple(str(f) for f in motif_features),
        motif_kmeans_k=int(motif_k),
        motif_kmeans_seed=int(motif_seed),
        motif_standardise=str(motif_std),
        eval_output_root=str(eval_output),
    )
```

> **API notes**
> `BehaviorMeasureCfg` is a `@dataclass(frozen=True)` — a plain Python frozen dataclass, not a Flax struct. It is entirely host-side; it never enters a JIT kernel. The `eval_seeds` and `motif_features` fields are stored as Python `tuple`s (not JAX arrays) because they are consumed by evaluation-loop Python code, not by traced JAX functions. The frozen dataclass pattern gives dict-like access with immutability guarantees without involving JAX at all.


---

## Optional Keys and Defaults

| YAML key | Default | Source |
|----------|---------|--------|
| `environment.placement.mode` | `"per_entity"` | `config_loader.py:779` |
| `perceptual_noise.enabled` | `False` | `config_loader.py:940` |
| Per-resource `nociception_intensity` | `0.9` (hiding\_predator), `0.0` (food) | `config_loader.py:652` |
| Per-resource `count` | `1` | `config_loader.py:622` |
| Per-animal `nociception_intensity` | `0.9` (predator), `0.0` (neutral / unified entities) | `config_loader.py:356,387,324` |
| Per-animal `spawn_area` | full grid `[[1,1],[h,w]]` | `config_loader.py:242` |
| Per-animal `patrol_area` | full grid `[[1,1],[h,w]]` | `config_loader.py:242` |
| Per-animal `count` | `1` | `config_loader.py:299,337,368` |
| Per-animal `tag` | `"idx{i}"` | `_normalise_tag()` `config_loader.py:165` |
| Per-obstacle `blocking` | `True` | `config_loader.py:1849` |
| Per-obstacle `hides_agent` | `False` | `config_loader.py:1850` |
| Per-obstacle `blocks_animals` | `False` (loader) — `default.yaml` ships `true` on the bush, a dated exception; see Obstacle Entity Fields | `config_loader.py:1851` |
| Per-obstacle `damage` | `0.0` → `[0,0]` | `config_loader.py:708` |
| Per-obstacle `nociception_intensity` | `0.3` | `config_loader.py:711` |
| Per-obstacle `count` | `1` | `config_loader.py:695` |
| Per-obstacle `name` | `"rock"` | `config_loader.py:720,722` |

---

## Static vs Dynamic Fields in `EnvParams`

**Static** fields (`pytree_node=False`, `state.py:85–221`) are baked into JIT-compiled code; changing any one triggers full recompilation.

| Category | Static (`pytree_node=False`) | Dynamic (traced by JAX) |
|----------|------------------------------|------------------------|
| Grid shape | `height`, `width`, `max_steps` | `grid_location_type [H,W]` |
| Animal metadata | `animal_classes`, `animal_behaviours`, `animal_tags`, `hunt_idx`, `wander_idx`, `static_idx`, `predator_indices`, `neutral_indices`, `has_attack_feature` | `animal_property [N,V]`, `animal_property_std [N,V]`, `animal_nociception [N]`, `animal_move_int [N]`, `animal_damage [N,2]`, `animal_attack_delay [N]`, `animal_spawn_area [N,4]`, `animal_patrol [N,4]`, all ten `animal_*_low/high` arrays, `animal_attack_range_low [N]`, `animal_attack_range_high [N]`, `animal_attack_success_rate [N]` (jump/pounce feature — see [PREDATOR_JUMP_MECHANISM.md](../develop/active/env_entities/PREDATOR_JUMP_MECHANISM.md)), `animal_classes_int [N]`, `animal_behaviours_int [N]`, `animal_is_damaging [N]`, `animal_visual_channel [N]` |
| Obstacles | `obstacle_names` | `obs_blocking [N]`, `obs_hides_agent [N]`, `obs_blocks_animals [N]`, `obs_spawn_area [N,4]`, `obs_damage [N,2]`, `obs_property [N,V]`, `obs_property_std [N,V]`, `obs_nociception [N]`, `obs_type [N]` |
| Placement | `max_per_type`, `num_types`, `num_entities`, `placement_mode` | `type_areas [T,4]`, `type_counts [T]`, `type_entity_map [T,max_per_type]` |
| Body flags | `recovery_in_bush_multiplier` (**see note below**), the eight B3/B5 `healing_*` fields and the seven B1/B2/B4 `thermal_*` body-mechanics fields (all static for the same reason — no new jaxpr leaves), `smoothing_duration`, `overeating_death`, `use_homeostatic_reward`, `with_satiation`, `with_nutrition`, `with_injury`, `random_start_satiation`, `random_start_nutrition`, `random_start_injury`, `random_start_pos`, `rest_action_enabled`, `eat_action_enabled` | `max_satiation`, `max_nutrition`, `max_injury`, `food_nutrition_gain`, `setpoint`, `start_satiation`, `start_nutrition`, `metabolic_cost`, `nutrition_to_satiation_scaling_factor`, `recovery_base_rate`, `recovery_accel_rate`, `death_penalty`, `eating_nutrition_cost`, `eating_reward_penalty`, `start_pos [2]` |
| Sensory flags | `sensor_range`, `visual_sensor_enabled`, `visual_sensor_range`, `local_view_size`, `olfactory_enabled`, `nociception_enabled`, `location_sensor_enabled`, `injury_observable`, `nutrition_observable`, `interoceptive_nociception_enabled`, `interoceptive_convolution_enabled`, `interoceptive_kernel_length`, `proprioception_enabled`, `action_dim`, `olfactory_vector_size`, `nociception_size` | `sensor_radius`, `sensor_decay`, `interoceptive_kernel [K]` |
| Noise | `perceptual_noise_enabled`, `noise_modality_order` | `noise_modes [13]`, `noise_sigmas [13]`, `noise_injury_scales [13]`, `noise_clip_min [13]`, `noise_clip_max [13]` |

> **Why `recovery_in_bush_multiplier` is static while its two `recovery_*` siblings are not.**
> `recovery_base_rate` and `recovery_accel_rate` are traced floats: changing either changes a
> number inside an unchanged graph, so a curriculum can vary them without recompiling.
> `recovery_in_bush_multiplier` is deliberately the opposite. It gates a **trace-time Python
> `if`** in `core.py::update_body`, so at the shipped `1.0` the location-premium branch emits no
> operation at all and the environment's graph is character-for-character the pre-feature one.
> That turns bit-parity with every run predating the key from a measurement into a property of
> the source. The price is a recompile when the value changes, which does not matter: it is
> fixed for the life of a run. `config_loader` coerces the read with `float()` for the same
> reason — a static field participates in JAX's trace-cache key, and YAML's `1` and `1.0` would
> otherwise be two different cache entries for the same inert setting.

---

## Olfactory YAML Keys

All entity types now uniformly use the **plural** form. The singular forms are deprecated and emit `DeprecationWarning` at load time but still function as a fallback (`config_loader.py:176–200`).

| Entity | Chemical signature key | Std dev key |
|--------|------------------------|-------------|
| Resource | `properties` | `properties_std` |
| Animal (predator / neutral / any) | `properties` | `properties_std` |
| Obstacle | `properties` | `properties_std` |

**Deprecated (rename these in your YAML):** `property` → `properties`, `property_std` → `properties_std`.

---

## Noise Configuration Parsing

Implemented in `_parse_noise_config()` (`config_loader.py:957`).

The YAML key order under `perceptual_noise.modalities` is the single source of truth for which index in the noise arrays corresponds to which modality. **Unknown keys now raise `ValueError`** (updated by FIX_CONFIG_LAYER_SILENT_FAILURES_20260723 — was previously silently dropped by the `if k in _YAML_KEY_TO_SENSOR_NAME` filter). The error message lists the valid keys, matching the table below.

All five noise arrays are padded to length **13** (`pad = max(0, 13 - len(noise_modality_order))`, `config_loader.py:968`). This keeps the array shape static regardless of how many modalities are configured.

YAML key → sensor name mapping (`config_loader.py:944–955`):

| YAML key | Sensor name | Default index in `default.yaml` |
|----------|-------------|--------------------------------|
| `injury` | `"Injury"` | 0 |
| `nutrition` | `"Nutrition"` | 1 |
| `satiation` | `"Satiation"` | 2 |
| `body_temperature` | `"Body Temperature"` | 3 |
| `interoceptive_nociception` | `"Interoceptive Nociception"` | 4 |
| `extero_nociception` | `"Extero Nociception"` | 5 |
| `thermoception` | `"Thermoception"` | 6 |
| `olfaction` | `"Olfaction"` | 7 |
| `collision` | `"Collision"` | 8 |
| `proprioception` | `"Proprioception"` | 9 |
| `visual` | `"Visual"` | 10 |
| `location` | `"Location"` | 11 |
| `hydration` | `"Hydration"` | 12 — appended last (2026-09-30) so no index above moved |

13 modalities defined — all 13 padded slots are used. The next modality must widen the pad
and `EnvParams.noise_*` together (the loader raises a named error otherwise). A world with
water on must carry the `hydration` entry (refused at load otherwise). `sensor.py` builds `modality_map = {name: i for i, name in enumerate(params.noise_modality_order)}` at observation-assembly time.

Per-modality optional keys (defaults apply when absent):

| Key | Default |
|-----|---------|
| `mode` | `"none"` (encoded as `0`) |
| `sigma` | `0.0` |
| `injury_noise_scale` | `0.0` |
| `clip_min` | `-100.0` |
| `clip_max` | `100.0` |

Mode encoding: `"none"` → `0`, `"constant"` → `1`, `"state_dependent"` → `2`. **Any other `mode` string now raises `ValueError`** (updated by FIX_CONFIG_LAYER_SILENT_FAILURES_20260723 — was previously silently mapped to `0` = noise off, e.g. a `"state-dependent"` hyphen typo).

Detail: see `docs/environment/10_perceptual_noise.md`.

### Implementation: `_parse_noise_config`

`_parse_noise_config` is a compact function that builds five parallel JAX arrays from the flat `perceptual_noise.modalities` YAML dict. It is called near the end of `load_env_params` (as `_noise_fields = _parse_noise_config(config)`, just before the water block, which checks the parsed order for a `"Hydration"` entry) and its return dict is splatted into the `EnvParams` constructor with `**_noise_fields`.

`Source: src/environment/config_loader.py:944–1002`

```python
_YAML_KEY_TO_SENSOR_NAME = {
    "injury":                    "Injury",
    "nutrition":                 "Nutrition",
    "satiation":                 "Satiation",
    "extero_nociception":        "Extero Nociception",
    "interoceptive_nociception": "Interoceptive Nociception",
    "olfaction":                 "Olfaction",
    "collision":                 "Collision",
    "proprioception":            "Proprioception",
    "visual":                    "Visual",
    "location":                  "Location",
}

def _parse_noise_config(config: Config):
    modalities_cfg = config.get('perceptual_noise.modalities') or {}
    
    def _parse_mode(s):
        return 2 if s == 'state_dependent' else 1 if s == 'constant' else 0

    noise_modality_order = tuple(
        _YAML_KEY_TO_SENSOR_NAME[k]
        for k in modalities_cfg
        if k in _YAML_KEY_TO_SENSOR_NAME
    )
    pad = max(0, 13 - len(noise_modality_order))

    noise_modes = jnp.pad(jnp.array([
        _parse_mode(modalities_cfg[k].get('mode', 'none'))
        for k in modalities_cfg if k in _YAML_KEY_TO_SENSOR_NAME
    ], dtype=jnp.int32), (0, pad))
    
    noise_sigmas = jnp.pad(jnp.array([
        modalities_cfg[k].get('sigma', 0.0)
        for k in modalities_cfg if k in _YAML_KEY_TO_SENSOR_NAME
    ], dtype=jnp.float32), (0, pad))
    
    noise_injury_scales = jnp.pad(jnp.array([
        modalities_cfg[k].get('injury_noise_scale', 0.0)
        for k in modalities_cfg if k in _YAML_KEY_TO_SENSOR_NAME
    ], dtype=jnp.float32), (0, pad))
    
    noise_clip_min = jnp.pad(jnp.array([
        modalities_cfg[k].get('clip_min', -100.0)
        for k in modalities_cfg if k in _YAML_KEY_TO_SENSOR_NAME
    ], dtype=jnp.float32), (0, pad))
    
    noise_clip_max = jnp.pad(jnp.array([
        modalities_cfg[k].get('clip_max', 100.0)
        for k in modalities_cfg if k in _YAML_KEY_TO_SENSOR_NAME
    ], dtype=jnp.float32), (0, pad))

    return {
        "noise_modality_order": noise_modality_order,
        "noise_modes": noise_modes,
        "noise_sigmas": noise_sigmas,
        "noise_injury_scales": noise_injury_scales,
        "noise_clip_min": noise_clip_min,
        "noise_clip_max": noise_clip_max,
    }
```

> **API notes**
> `noise_modality_order` is a Python tuple of strings stored as `pytree_node=False` (static). The five numeric arrays are JAX-traced dynamic leaves. The `jnp.pad(..., (0, pad))` calls add trailing zeros to bring each array to exactly 13 elements, keeping the shape constant regardless of how many modalities are listed in the YAML — avoiding a JIT recompile when adding/removing modalities. See [primer: static vs dynamic fields](00_jax_primer.md#static-dynamic) and [primer: masking](00_jax_primer.md#masking) (the spare padding slots are always read as zero by `sensor.py`).

---

## Implementation: `load_env_params`

`load_env_params` is the main entry point. It is a pure host-side Python function — no JAX tracing happens inside it. Its job is to translate a `Config` object into a fully populated `EnvParams` Flax struct. The struct is then passed to JIT-compiled functions.

`Source: src/environment/config_loader.py:614–671` (resources + v2.0 guard)

```python
def load_env_params(config: Config) -> EnvParams:
    """Loads environment parameters from a Config object with strict retrieval."""
    
    # Build resource arrays
    raw_resources = config.get_mandatory('environment.resources')
    expanded_resources = []
    if raw_resources:
        for r in raw_resources:
            count = r.get('count', 1) 
            for _ in range(count):
                expanded_resources.append(r)
    
    if expanded_resources:
        def r_get(r, key):
            val = r.get(key)
            if val is None: raise ValueError(f"Strict Config: Resource field '{key}' is required.")
            if key == 'type' and val == 'danger':
                warnings.warn(
                    "Resource type 'danger' is deprecated — rename to 'hiding_predator'.",
                    DeprecationWarning,
                    stacklevel=2,
                )
            return val

        # 0: food, 1: hiding_predator
        res_type = jnp.array([0 if r_get(r, 'type') == 'food' else 1 for r in expanded_resources], dtype=jnp.int32)
        res_property = jnp.array([_read_properties(r, 'Resource') for r in expanded_resources])
        chem_dim = res_property.shape[-1]
        res_property_std = jnp.array([_read_properties_std(r, 'Resource') for r in expanded_resources])
        # Subtract 1 for minval (0-based) but keep maxval as is for JAX's exclusive upper bound
        res_spawn_area = jnp.array([[a[0][0]-1, a[0][1]-1, a[1][0], a[1][1]] for a in [r_get(r, 'spawn_area') for r in expanded_resources]])
        res_max_cons = jnp.array([r_get(r, 'max_consumption') for r in expanded_resources], dtype=jnp.int32)
        res_reg_delay = jnp.array([r_get(r, 'regeneration_delay') for r in expanded_resources], dtype=jnp.int32)
        
        # Damage can be scalar (Feb 12) or range [min, max] (tuningEnv)
        raw_damage = [r_get(r, 'damage') for r in expanded_resources]
        res_damage = jnp.array([d if isinstance(d, list) else [d, d] for d in raw_damage])
        
        res_nociception = jnp.array([r.get('nociception_intensity', 0.9 if r_get(r, 'type') in ('hiding_predator', 'danger') else 0.0) for r in expanded_resources])
    else:
        res_type = jnp.zeros(0, dtype=jnp.int32)
        res_property = jnp.zeros((0, 5))
        res_property_std = jnp.zeros((0, 5))
        res_nociception = jnp.zeros(0)
        res_spawn_area = jnp.zeros((0, 4), dtype=jnp.int32)
        res_max_cons = jnp.zeros(0, dtype=jnp.int32)
        res_reg_delay = jnp.zeros(0, dtype=jnp.int32)
        res_damage = jnp.zeros((0, 2))

    # ── Guard against stale `predator_enabled` key (removed in v2.0) ──────────
    # The 86 migrated configs have this key stripped by the CP1 migration sweep.
    # Any config that still carries it after migration raises a clear error.
    if config.get('environment.predator_enabled') is not None:
        raise ValueError(
            "Config key 'environment.predator_enabled' was removed in v2.0. "
            "Strip this line from your YAML (it was always True for 85 of 86 configs; "
            "for the neutral-only case, use 'predators: []' which is already present)."
        )
```

`Source: src/environment/config_loader.py:673–801` (animals + obstacles + location grid + placement grouping)

```python
    # ── Build unified animal arrays via _load_animals() ──────────────────────
    (
        animal_property, animal_property_std, animal_nociception,
        animal_move_int, animal_damage, animal_attack_delay,
        animal_spawn_area, animal_patrol,
        animal_detect_low, animal_detect_high,
        animal_max_stamina_low, animal_max_stamina_high,
        animal_recovery_low, animal_recovery_high,
        animal_hunt_thresh_low, animal_hunt_thresh_high,
        animal_lose_interest_low, animal_lose_interest_high,
        animal_classes_int, animal_behaviours_int,
        animal_is_damaging, animal_visual_channel,
        animal_classes, animal_behaviours, animal_tags,
        hunt_idx, wander_idx, static_idx,
        predator_indices, neutral_indices,
        pred_spawn_area_for_placement, neutral_spawn_area_for_placement,
    ) = _load_animals(config)

    # Build Obstacle arrays
    raw_obstacles = config.get_mandatory('environment.obstacles')
    expanded_obstacles = []
    for o in raw_obstacles:
        count = o.get('count', 1)
        for _ in range(count):
            expanded_obstacles.append(o)
            
    if expanded_obstacles:
        def obs_get(o, key):
            val = o.get(key)
            if val is None: raise ValueError(f"Strict Config: Obstacle field '{key}' is required.")
            return val
        obs_blocking = jnp.array([o.get('blocking', True) for o in expanded_obstacles], dtype=jnp.bool_)
        obs_hides_agent = jnp.array([o.get('hides_agent', False) for o in expanded_obstacles], dtype=jnp.bool_)
        
        # Obstacle damage ranges
        raw_obs_damage = [o.get('damage', 0.0) for o in expanded_obstacles]
        obs_damage = jnp.array([d if isinstance(d, list) else [d, d] for d in raw_obs_damage])
        
        obs_nociception = jnp.array([o.get('nociception_intensity', 0.3) for o in expanded_obstacles], dtype=jnp.float32)
        # Unified: Obstacles can have properties too
        chem_dim = res_property.shape[-1]
        obs_property = jnp.array([_read_properties(o, 'Obstacle') for o in expanded_obstacles])
        obs_property_std = jnp.array([_read_properties_std(o, 'Obstacle') for o in expanded_obstacles])
        # Adjust for 0-based min and exclusive max
        obs_spawn_area = jnp.array([[a[0][0]-1, a[0][1]-1, a[1][0], a[1][1]] for a in [obs_get(o, 'area') for o in expanded_obstacles]])
        
        # Obstacle types for visual sensor
        obstacle_names = tuple(sorted(list(set([o.get('name', 'rock') for o in expanded_obstacles]))))
        name_to_idx = {name: i for i, name in enumerate(obstacle_names)}
        obs_type = jnp.array([name_to_idx[o.get('name', 'rock')] for o in expanded_obstacles], dtype=jnp.int32)
    else:
        obs_blocking = jnp.zeros(0, dtype=jnp.bool_)
        obs_hides_agent = jnp.zeros(0, dtype=jnp.bool_)
        obs_damage = jnp.zeros((0, 2), dtype=jnp.float32)
        obs_nociception = jnp.zeros(0, dtype=jnp.float32)
        chem_dim = res_property.shape[-1]
        obs_property = jnp.zeros((0, chem_dim))
        obs_property_std = jnp.zeros((0, chem_dim))
        obs_spawn_area = jnp.zeros((0, 4), dtype=jnp.int32)
        obs_type = jnp.zeros(0, dtype=jnp.int32)
        obstacle_names = ("rock",)
    
    # Build Grid Location Types
    import numpy as np
    height = config.get_mandatory('environment.height')
    width = config.get_mandatory('environment.width')
    grid_np = np.zeros((height, width), dtype=np.int32)
    location_areas = config.get_mandatory('environment.location_areas')
    for area_config in location_areas:
        a_type = area_config.get('type')
        type_idx = 1 if a_type == 'grass' else 2 if a_type == 'sand' else 0
        area = area_config.get('area')
        if area:
            # 1-based conversion: [r1, c1] to [r2, c2] inclusive maps to grid[r1-1:r2, c1-1:c2]
            r1, c1, r2, c2 = area[0][0], area[0][1], area[1][0], area[1][1]
            grid_np[r1-1:r2, c1-1:c2] = type_idx
    grid_location_type = jnp.array(grid_np)
    
    # ── Type-Level Placement: Group entities by spawn area ──
    # Preserve today's [res, pred, obs, neutral] index order for type_entity_map
    # (N1 fix: jax_reset placement uses this ordering for the resolve-scan).
    all_spawn_areas_np = np.concatenate([
        np.array(res_spawn_area), np.array(pred_spawn_area_for_placement),
        np.array(obs_spawn_area), np.array(neutral_spawn_area_for_placement)
    ], axis=0)  # [N, 4]
    num_total_entities = all_spawn_areas_np.shape[0]
    
    # Group by unique spawn area
    groups_by_area = {}  # tuple(area) -> list of entity global indices
    for eidx in range(num_total_entities):
        area_key = tuple(all_spawn_areas_np[eidx].tolist())
        groups_by_area.setdefault(area_key, []).append(eidx)
    
    # Build type-level arrays
    area_keys_list = list(groups_by_area.keys())
    num_types = len(area_keys_list)
    type_counts_list = [len(groups_by_area[k]) for k in area_keys_list]
    max_per_type = max(type_counts_list) if type_counts_list else 1
    
    type_areas_np = np.array([list(k) for k in area_keys_list], dtype=np.int32)
    type_entity_map_np = np.full((num_types, max_per_type), 0, dtype=np.int32)
    for tidx, k in enumerate(area_keys_list):
        ents = groups_by_area[k]
        type_entity_map_np[tidx, :len(ents)] = ents
    
    # Parse placement mode
    placement_mode = config.get('environment.placement.mode', 'per_entity')
    assert placement_mode in ('per_entity', 'per_type'), f"Unknown placement mode: {placement_mode}"

    _log.debug("=" * 60)
    _log.debug("ENTITY PLACEMENT STRATEGY: %s", placement_mode)
    _log.debug("=" * 60)
    _log.debug("Grid: %d×%d (%d cells)", height, width, height * width)
    _log.debug("Total entities: %d", num_total_entities)
    if placement_mode == 'per_type':
        _log.debug("Type groups: %d (one lax.scan step each)", num_types)
        for tidx, k in enumerate(area_keys_list):
            area = list(k)
            cnt = type_counts_list[tidx]
            area_cells = (area[2] - area[0]) * (area[3] - area[1])
            _log.debug(
                "  Group %d: area %s → %d entities / %d cells (%.0f%%)",
                tidx, area, cnt, area_cells, 100 * cnt / area_cells if area_cells else 0
            )
        _log.debug("Max entities per group: %d", max_per_type)
        _log.debug("Sequential steps: %d", num_types)
    else:
        _log.debug("Sequential steps: %d (one per entity)", num_total_entities)
    _log.debug("=" * 60)
```

`Source: src/environment/config_loader.py:803–941` (interoceptive kernel + EnvParams construction)

```python
    # Hidden-state observability flags
    injury_observable = bool(config.get_mandatory('sensory.injury_observable'))
    nutrition_observable = bool(config.get_mandatory('sensory.nutrition_observable'))

    # Interoceptive nociception (delayed-peak perception of hidden injury)
    interoceptive_nociception_enabled = bool(config.get_mandatory('sensory.interoceptive_nociception_enabled'))
    interoceptive_convolution_enabled = bool(config.get_mandatory('sensory.interoceptive_convolution_enabled'))
    interoceptive_kernel_length = int(config.get_mandatory('sensory.interoceptive_kernel_length'))
    interoceptive_kernel_tau = float(config.get_mandatory('sensory.interoceptive_kernel_tau'))

    if interoceptive_convolution_enabled:
        # Build normalized alpha kernel: k_raw[i] = (i/τ)·exp(1 - i/τ); k[i] = k_raw[i] / Σk_raw
        _k_idx = np.arange(interoceptive_kernel_length, dtype=np.float32)
        _k_raw = (_k_idx / interoceptive_kernel_tau) * np.exp(1.0 - _k_idx / interoceptive_kernel_tau)
        _k_sum = float(_k_raw.sum())
        if _k_sum <= 0.0:
            raise ValueError(
                f"interoceptive_kernel produced non-positive sum ({_k_sum}). "
                f"Check tau ({interoceptive_kernel_tau}) and length ({interoceptive_kernel_length})."
            )
        interoceptive_kernel = jnp.array(_k_raw / _k_sum, dtype=jnp.float32)
    else:
        # Passthrough mode — kernel is unused but kept as zeros for shape stability.
        interoceptive_kernel = jnp.zeros(interoceptive_kernel_length, dtype=jnp.float32)

    return EnvParams(
        height=height,
        width=width,
        max_steps=config.get_mandatory('environment.max_steps'),
        grid_location_type=grid_location_type,
        res_type=res_type,
        res_property=res_property,
        res_property_std=res_property_std,
        res_nociception=res_nociception,
        res_spawn_area=res_spawn_area,
        res_max_cons=res_max_cons,
        res_reg_delay=res_reg_delay,
        res_damage=res_damage,
        # Unified animal arrays (M2 fix: no predator_tags= / neutral_tags= kwargs)
        animal_property=animal_property,
        animal_property_std=animal_property_std,
        animal_nociception=animal_nociception,
        animal_move_int=animal_move_int,
        animal_damage=animal_damage,
        animal_attack_delay=animal_attack_delay,
        animal_spawn_area=animal_spawn_area,
        animal_patrol=animal_patrol,
        animal_detect_low=animal_detect_low,
        animal_detect_high=animal_detect_high,
        animal_max_stamina_low=animal_max_stamina_low,
        animal_max_stamina_high=animal_max_stamina_high,
        animal_recovery_low=animal_recovery_low,
        animal_recovery_high=animal_recovery_high,
        animal_hunt_thresh_low=animal_hunt_thresh_low,
        animal_hunt_thresh_high=animal_hunt_thresh_high,
        animal_lose_interest_low=animal_lose_interest_low,
        animal_lose_interest_high=animal_lose_interest_high,
        animal_classes_int=animal_classes_int,
        animal_behaviours_int=animal_behaviours_int,
        animal_is_damaging=animal_is_damaging,
        animal_visual_channel=animal_visual_channel,
        animal_classes=animal_classes,
        animal_behaviours=animal_behaviours,
        animal_tags=animal_tags,
        hunt_idx=hunt_idx,
        wander_idx=wander_idx,
        static_idx=static_idx,
        predator_indices=predator_indices,
        neutral_indices=neutral_indices,
        obs_blocking=obs_blocking,
        obs_hides_agent=obs_hides_agent,
        obs_damage=obs_damage,
        obs_property=obs_property,
        obs_property_std=obs_property_std,
        obs_nociception=obs_nociception,
        obs_spawn_area=obs_spawn_area,
        obs_type=obs_type,
        obstacle_names=obstacle_names,
        type_areas=jnp.array(type_areas_np, dtype=jnp.int32),
        type_counts=jnp.array(type_counts_list, dtype=jnp.int32),
        type_entity_map=jnp.array(type_entity_map_np, dtype=jnp.int32),
        max_per_type=max_per_type,
        num_types=num_types,
        num_entities=num_total_entities,
        placement_mode=placement_mode,
        max_satiation=config.get_mandatory('body.max_satiation'),
        max_nutrition=config.get_mandatory('body.max_nutrition'),
        max_injury=config.get_mandatory('body.max_injury'),
        food_nutrition_gain=config.get_mandatory('body.food_nutrition_gain'),
        setpoint=config.get_mandatory('body.satiation_setpoint'),
        start_satiation=config.get_mandatory('body.start_satiation'),
        start_nutrition=config.get_mandatory('body.start_nutrition'),
        metabolic_cost=config.get_mandatory('body.metabolic_cost'),
        nutrition_to_satiation_scaling_factor=config.get_mandatory('body.nutrition_to_satiation_scaling_factor'),
        recovery_base_rate=config.get_mandatory('body.recovery_base_rate'),
        recovery_accel_rate=config.get_mandatory('body.recovery_accel_rate'),
        # STATIC field — read + validated (> 0) above the constructor and
        # coerced with float(), because a static field is part of the trace-cache
        # key and YAML's `1` and `1.0` would otherwise be two cache entries.
        recovery_in_bush_multiplier=_recovery_in_bush_mult,
        smoothing_duration=config.get_mandatory('body.injury_smoothing_duration'),
        death_penalty=config.get_mandatory('body.death_penalty'),
        overeating_death=config.get_mandatory('body.overeating_death'),
        use_homeostatic_reward=config.get_mandatory('body.use_homeostatic_reward'),
        with_satiation=config.get_mandatory('body.with_satiation'),
        with_nutrition=config.get_mandatory('body.with_nutrition'),
        with_injury=config.get_mandatory('body.with_injury'),
        random_start_satiation=config.get_mandatory('body.random_start_satiation'),
        random_start_nutrition=config.get_mandatory('body.random_start_nutrition'),
        random_start_injury=config.get_mandatory('body.random_start_injury'),
        random_start_pos=config.get_mandatory('environment.random_start_pos'),
        start_pos=jnp.array(config.get_mandatory('environment.start_pos')) - 1,
        rest_action_enabled=config.get_mandatory('environment.rest_action_enabled'),
        eat_action_enabled=config.get_mandatory('environment.eat_action_enabled'),
        eating_nutrition_cost=config.get_mandatory('body.eating_nutrition_cost'),
        eating_reward_penalty=config.get_mandatory('body.eating_reward_penalty'),
        sensor_radius=config.get_mandatory('sensory.sensor_radius'),
        sensor_decay=config.get_mandatory('sensory.decay_power'),
        sensor_range=config.get_mandatory('sensory.collision_sensor_range'),
        visual_sensor_enabled=config.get_mandatory('sensory.visual_sensor_enabled'),
        visual_sensor_range=config.get_mandatory('sensory.visual_sensor_range'),
        local_view_size=config.get_mandatory('visualization.local_view_size'),
        proprioception_enabled=config.get_mandatory('sensory.proprioception_enabled'),
        olfactory_enabled=config.get_mandatory('sensory.olfactory_enabled'),
        nociception_enabled=config.get_mandatory('sensory.nociception_enabled'),
        location_sensor_enabled=config.get_mandatory('sensory.location_sensor'),
        olfactory_vector_size=config.get_mandatory('sensory.vector_size'),
        nociception_size=config.get_mandatory('sensory.nociception_size'),
        action_dim=4 + int(config.get_mandatory('environment.rest_action_enabled')) + int(config.get_mandatory('environment.eat_action_enabled')),

        # Hidden-state observability flags
        injury_observable=injury_observable,
        nutrition_observable=nutrition_observable,

        # Interoceptive nociception (delayed-peak perception of hidden injury)
        interoceptive_nociception_enabled=interoceptive_nociception_enabled,
        interoceptive_convolution_enabled=interoceptive_convolution_enabled,
        interoceptive_kernel_length=interoceptive_kernel_length,
        interoceptive_kernel=interoceptive_kernel,

        # Perceptual Noise Configuration
        perceptual_noise_enabled=config.get('perceptual_noise.enabled', False),
        **_noise_fields,          # = _parse_noise_config(config), parsed just above

        # Water / thirst (sentinels when water.enabled is false)
        **_water_fields,          # = _load_water(...) or _WATER_OFF
```

> **API notes — the host–device boundary in full**
> `load_env_params` is the single crossing point between the host (Python/NumPy config-loading world) and the device (JAX-traced world). Every `jnp.array(...)` call here converts a Python list or NumPy array into a device buffer. After `EnvParams(...)` is constructed and returned, the entire struct is a JAX pytree; its dynamic leaves can be passed to `jax.jit`, `jax.vmap`, or `lax.scan` without any further explicit transfers. See [primer: JAX pytrees](00_jax_primer.md#jax-pytrees).
>
> Several fields go through an intermediate NumPy step (e.g. `type_entity_map_np`, `type_areas_np`, `all_spawn_areas_np`) because grouping logic is easier to express with NumPy's `np.concatenate` / `np.full` than with `jnp`. These NumPy arrays are not device buffers; they become device buffers only at the `jnp.array(...)` calls on the last few lines of that block.
>
> `start_pos=jnp.array(config.get_mandatory('environment.start_pos')) - 1` converts 1-based YAML coordinates to 0-based in-place: `jnp.array([5,5]) - 1 = jnp.array([4,4])`. The subtraction is evaluated eagerly (outside any JIT context). See [primer: immutability](00_jax_primer.md#immutability).
>
> `action_dim` is computed from two bool flags and stored as a static int. Adding a new action requires bumping `action_dim` in the config and retracing all JIT-compiled functions. See [primer: static vs dynamic fields](00_jax_primer.md#static-dynamic).
>
> The interoceptive alpha kernel formula `k_raw[i] = (i/τ) * exp(1 - i/τ)` peaks at `i = τ` and is normalized to sum to 1. The computation is done in NumPy before the `jnp.array(...)` call; the resulting fixed-shape kernel array is a dynamic leaf of `EnvParams` and can be updated between episodes without triggering recompilation (its shape is static, but its values are traced).


---

## Default Values Reference

Full annotated listing from `configs/environment/default.yaml`:

```yaml
environment:
  height: 10                        # 10×10 grid
  width: 10
  start_pos: [5, 5]                 # 1-based; stored as [4, 4] (0-based)
  max_steps: 500
  rest_action_enabled: true         # action 4 = rest
  eat_action_enabled: true          # action 5 = eat
  random_start_pos: true
  placement:
    mode: per_entity                # fastest for 10×10

  resources:
    - type: "food"
      count: 2
      spawn_area: [[1,1],[5,5]]
      properties: [1.0, 0.0, 0.0, 0.0, 0.0]
      properties_std: [0.0, 0.0, 0.0, 0.0, 0.0]
      max_consumption: 12
      regeneration_delay: 0
      damage: [0.0, 0.0]
      nociception_intensity: 0.0

    - type: "hiding_predator"       # static trap resource (not a moving animal)
      count: 1
      spawn_area: [[1,1],[5,5]]
      properties: [0.0, 0.0, 0.0, 0.0, 0.0]
      properties_std: [0.0, 0.0, 0.0, 0.0, 0.0]
      max_consumption: -1
      damage: [15.0, 45.0]
      regeneration_delay: 20
      nociception_intensity: 0.9

  predators:                        # legacy schema — re-projected as class=predator, behaviour=hunt
    - name: "predator"
      count: 1
      properties: [0.0, 0.7, 0.5, 0.0, 0.0]
      properties_std: [0.0, 0.4, 0.4, 0.0, 0.0]
      move_interval: 1
      damage: [15.0, 45.0]
      nociception_intensity: 0.9
      spawn_area: [[1,1],[10,10]]
      patrol_area: [[1,1],[10,10]]
      detection_range: 5
      max_stamina: 30
      stamina_recovery_rate: 1
      hunt_stamina_threshold: 0.7
      attack_delay: 3
      lose_interest_multiplier: 1.5

  neutral_animals:                  # legacy schema — re-projected as class=neutral, behaviour=wander
    - name: "rabbit"
      count: 1
      properties: [0.0, 0.5, 0.7, 0.0, 0.0]
      properties_std: [0.0, 0.4, 0.4, 0.0, 0.0]
      move_interval: 1
      nociception_intensity: 0.1
      spawn_area: [[1,1],[5,5]]
      patrol_area: [[1,1],[5,5]]

  obstacles:
    - name: "rock"
      count: 3
      area: [[1,1],[5,5]]
      blocking: false
      damage: [1, 5]
      nociception_intensity: 0.9
      properties: [0.0, 0.0, 0.0, 0.0, 0.0]
      properties_std: [0.0, 0.0, 0.0, 0.0, 0.0]
    - name: "bush"
      count: 5
      area: [[1,6],[5,10]]
      blocking: false
      hides_agent: true
      damage: [0.0, 0.0]
      nociception_intensity: 0.0
      properties: [0.0, 0.0, 0.0, 1.0, 0.0]
      properties_std: [0.0, 0.0, 0.0, 0.0, 0.0]

  location_areas:
    - type: "grass"
      area: [[1,1],[10,10]]         # whole grid is grass

body:
  with_satiation: true
  with_nutrition: true
  with_injury: true
  random_start_satiation: false
  random_start_nutrition: false
  random_start_injury: false
  max_satiation: 100
  max_nutrition: 100
  max_injury: 100
  metabolic_cost: 1.0
  food_nutrition_gain: 6
  eating_nutrition_cost: 1.0
  eating_reward_penalty: 0.0
  nutrition_to_satiation_scaling_factor: 1.0
  satiation_setpoint: 100
  start_satiation: 100
  start_nutrition: 100
  recovery_base_rate: 0.1
  recovery_accel_rate: 0.5
  recovery_in_bush_multiplier: 1.0
  injury_smoothing_duration: 3
  use_homeostatic_reward: true
  death_penalty: 100
  overeating_death: false

sensory:
  olfactory_enabled: true
  sensor_radius: 20                 # effectively whole 10×10 grid
  vector_size: 5                    # 5-dim chemical property
  decay_power: 2.0                  # inverse square distance decay
  collision_sensor_range: 1         # 5-cell Manhattan diamond
  location_sensor: false
  nociception_enabled: true
  nociception_size: 1
  visual_sensor_enabled: true
  visual_sensor_range: 0            # single-cell (agent's own cell only)
  proprioception_enabled: true
  injury_observable: false          # hidden (perceived via nociception only)
  nutrition_observable: false       # hidden (perceived via olfaction / intero)
  interoceptive_nociception_enabled: true
  interoceptive_convolution_enabled: true
  interoceptive_kernel_tau: 3.0
  interoceptive_kernel_length: 12

visualization:
  local_view_size: 5

perceptual_noise:
  enabled: false
  modalities:
    injury:
      mode: "state_dependent"
      sigma: 0.0
      injury_noise_scale: 1.5
      clip_min: 0.0
      clip_max: 1.0
    interoceptive_nociception:
      mode: "state_dependent"
      sigma: 0.1
      injury_noise_scale: 1.5
      clip_min: 0.0
      clip_max: 1.0
    extero_nociception:
      mode: "state_dependent"
      sigma: 0.1
      injury_noise_scale: 1.5
      clip_min: 0.0
      clip_max: 100.0
    olfaction:
      mode: "state_dependent"
      sigma: 0.2
      injury_noise_scale: 1.5
      clip_min: 0.0
      clip_max: 100.0
    collision:
      mode: "constant"
      sigma: 0.01
      injury_noise_scale: 0.0
      clip_min: 0.0
      clip_max: 1.0
    visual:
      mode: "state_dependent"
      sigma: 0.2
      injury_noise_scale: 1.5
      clip_min: 0.0
      clip_max: 100.0
    location:
      mode: "constant"
      sigma: 0.01
      injury_noise_scale: 0.0
      clip_min: -1.0
      clip_max: 1.0
```

---

## Clarifications / FAQ

**Q: What happens if I set `count: 0` on an entity entry?**
A: `range(0)` produces zero expansions, so the entry is skipped entirely. It is a clean way to disable a specific entity kind without deleting its YAML block — useful for ablations.

**Q: What if I leave `count` out entirely?**
A: Defaults to `1` (`config_loader.py:299,337,368,622,695`). One entity is spawned.

**Q: Scalar vs range `damage` — which format is right?**
A: Both work. A scalar `damage: 10` expands to `[10, 10]` (deterministic). A list `damage: [5, 15]` specifies a uniform distribution. The `*_damage` array is always shape `[N, 2]`.

**Q: Can distributional fields like `detection_range` also be scalars?**
A: Yes. `detection_range: 5` is stored as `[5.0, 5.0]` (deterministic per episode). `detection_range: [3, 7]` samples uniformly from [3, 7] at each reset.

**Q: What happens if `location_areas` has overlapping entries?**
A: Later entries overwrite earlier ones at the overlapping cells (`config_loader.py:748`). Order your YAML so the desired foreground terrain appears last.

**Q: What does `placement.mode` actually affect at runtime?**
A: Only the reset-time placement algorithm — after step 0, the two modes produce identical behaviour. Changing the mode triggers JIT recompilation because `placement_mode` is static. See `docs/environment/03_entity_placement.md`.

**Q: When is a type group created?**
A: At config-load time, entities are grouped by the exact tuple of their 0-indexed spawn-area bounding box (`config_loader.py:762–764`). Entities from different kinds (food, predator, obstacle, neutral) with the same bounding box share a group.

**Q: How is `obstacle_names` built — does order matter?**
A: `obstacle_names` is the **sorted unique** set of obstacle `name` values (`config_loader.py:720`). `obs_type[o]` is the index of obstacle `o`'s name in this tuple. Renaming an obstacle may shift its index — don't hardcode indices.

**Q: If I omit `name` on an obstacle, what happens?**
A: Defaults to `"rock"` (`config_loader.py:720,722`). If all obstacles are nameless, `obstacle_names = ("rock",)`.

**Q: The old doc listed `environment.predator_enabled` as mandatory — is it still needed?**
A: No. It was **removed entirely in v2.0**. If your YAML still contains `environment.predator_enabled`, `load_env_params` raises `ValueError` with a migration message (`config_loader.py:666–671`). Strip that line from your YAML.

**Q: Are `body.start_satiation` and `body.random_start_satiation` actually used?**
A: They are mandatory in the schema and copied into `EnvParams`, but satiation at reset is derived from nutrition in `core.py`. These are legacy fields.

**Q: What does `sensor_radius: 20` do on a 10×10 grid?**
A: Olfaction scales intensity by distance with decay `decay_power`. `sensor_radius` is the normalisation distance. A radius ≥ max grid distance means every source is detectable (intensity still decays). See `docs/environment/09_sensors_and_observation.md`.

**Q: If `perceptual_noise.enabled: false`, does `modalities` still need to be present?**
A: No — `_parse_noise_config` safely returns zeros for absent modalities. Leaving `modalities` absent is fine.

**Q: Does `config.get(...)` raise on missing keys?**
A: No. `config.get('key', default)` returns the default. Only `config.get_mandatory('key')` raises `ValueError`.

**Q: Is `default.yaml` loaded automatically?**
A: No — you must explicitly point your training script at it (or merge it) via `Config.merge()`. There is no auto-loading.

**Q: The noise array is padded to 13. Why 13?**
A: A fixed static shape: padding keeps the array shape the same however many modalities a config lists, avoiding recompilation. Unused slots are zero-valued and never indexed. **Since 2026-09-30 the default config lists 13 modalities, so every slot is used** (`hydration` took the last); a 14th must widen `_NOISE_SLOTS` and the `EnvParams.noise_*` arrays together.

**Q: What happens if my YAML lists a modality name not in `_YAML_KEY_TO_SENSOR_NAME`?**
A: It is silently dropped from `noise_modality_order` (`config_loader.py:965`). No error is raised. Typos are silent — double-check the 10 valid keys in the table above.

**Q: Does `start_pos: [5, 5]` match row/col or x/y?**
A: Row/col, 1-indexed and inclusive. Stored as `[4, 4]` (0-indexed) in `EnvParams.start_pos` (`config_loader.py:910`).

**Q: The old doc says `predator_tags` and `neutral_tags` are passed to the EnvParams constructor — is that still true?**
A: No. In v2.0 these are `@property` accessors on the struct (`state.py:234–247`), not constructor arguments. They filter `animal_tags` by class on the fly. The corresponding struct fields have been removed (M1 fix).

**Q: Is `environment.predators` or `environment.neutral_animals` still required?**
A: Neither is mandatory. The loader uses `config.get()` (not `config.get_mandatory()`) for both (`config_loader.py:335,366`). An absent or empty list results in zero animals of that class. The new `environment.entities:` schema is entirely optional too — if all three sections are absent, the environment has zero animals.
