---
title: "Water and thirst: a fixed pond per episode and a two-sided hydration axis"
topic: env_entities
status: active
created: 2026-09-29
last_updated: 2026-09-30
aliases: [thirst_water_plan]
---

# Water and thirst: a fixed pond per episode and a two-sided hydration axis

> **Status**: APPROVED 2026-09-30 (Revision 1; see "Approval" at the end) — being implemented on branch `v5.0` in the worktree `.claude/worktrees/thirst`. Revision 1 answers the plan-reviewer and math-reviewer blocks at the end of this file. Frontmatter says `active` because the develop-index validator accepts only `active` / `superseded` / `archive`, and `draft` would fail it. The same goes for the folder: `thirst` is not a registered topic, so the doc is filed under `env_entities`. Adding a topic means editing `scripts/claude/regen_dev_index.py`, which this plan may not do.
> **Opened**: 2026-09-29
> **Related**: [[thermal_implementation_plan]] (method template: staged, byte-parity first) · [[warming_cooling_rate_scales]] (target-first calibration template) · [[STATE_DEPENDENT_BODY_MECHANICS]] (the parity-fixture and saved-config-compat pattern reused here) · [[BUSH_FIRE_CLEARANCE]] (placement post-pass pattern) · [[RENDERER_LAYOUT_REDESIGN]] (owner of the episode-video dashboard) · [[SAVED_RUN_CONFIG_COMPAT]] · Known Bugs registry: `docs/develop/active/issues/KNOWN_BUGS.md` (rows cited in §A11)
> **Decision record**: user alignment session 2026-09-29, `tmp/20260929_173459_thirst_alignment.md` (gitignored; its decisions table is copied verbatim below)

---

## Context

The agent in this grid world keeps its body in range. Today it tracks hunger, injury and, in the campfire world, body temperature. This plan adds a fourth need: **thirst**. It also adds **water** to drink.

Water is different from food. Food items are scattered, get eaten up and come back somewhere else. Water is **one pond per episode**: a small block of cells, 2×2 by default. The pond never runs dry and never moves during the episode. It moves **between** episodes, though. The agent can smell and see which way things lie, so a pond in the same place every episode would turn into a memorised route. Each episode draws the pond from a short list of candidate spots in the config, or at random, or at the grid centre.

Standing on a pond cell drinks, on every step. Drinking too much is fatal, just as drinking too little is. Hydration mirrors the nutrition axis rebuilt on 2026-09-22: it drains a little each step, has its comfortable level in the **middle** of its range, and kills at either end. Predators may walk into the pond, so the pond is also an ambush point where thirst has to be traded against danger.

**What the plan claims.**

- Every world that does not switch water on stays **byte-for-byte the same**: same random numbers, same observations, same rewards. The plan requires parity tests that prove this against rollouts recorded before any code change.
- A new ladder level, **06 "pond + thirst"**, is added on top of the campfire world.
- The current noise level is renamed from 06 to **07** and now sits on top of the pond world.

The Analysis section checks every mechanism against the code as it stands today. The previous (thermal) plan's assumptions about the code were wrong at every stage, so none are taken on trust here.

---

## Settled decisions (user, 2026-09-29) — copied verbatim, not reopened

| # | Decision | Chosen |
|---|---|---|
| 1 | Placement modes | `placement: list | random | center`; list = candidate locations in config, one drawn per episode |
| 2 | Pond shape/count | ONE pond per episode, multi-cell block (e.g. 2x2); list entries = top-left cell |
| 3 | Thirst dynamics | MIRROR NUTRITION: linear drain per step, drinking refills; two-sided axis, setpoint in the middle, death at W<=0 and W>=max (like overeating_death since 09-22) |
| 4 | Vision | Do not worry: current default visual sensor is ONE channel ("Visible"); pond just writes into it |
| 5 | Smell | KEEP 5 olfactory dims. Water property vector mixes Food + Tree dims, e.g. [0.5,0,0,0,0.5] (Tree dim is dead in maintained levels: tree count 0). Per-cell weight scaled so a 2x2 pond is not 4x louder than one food. Rename Tree channel label (e.g. "Odour C"). User: deliberately LESS clear than EVAAA; water and food share info. |
| 6 | Drinking | Pond cells WALKABLE; drink every step standing on a pond cell; pond never disappears. Over-drinking death is the brake. |
| 7 | Ladder | NEW level 06 = campfire world + pond (extends 05); 06-sensory_noise renumbers to 07 |
| 8 | Water clock | SLOWER than food: ~150-200 steps setpoint->death (food 100, cold ~92; episode cap 500) |
| 9 | Predators | Animals walk into the pond freely (watering-hole ambush; thirst-vs-danger trade) |

**Defaults assumed by the alignment note (user may override; this plan implements them as written):**

- Hydration is **observable**, like satiation: one observation dimension, always present when water is on.
- The water term enters the homeostatic drive (and therefore the reward) **the same way satiation does**.
- The pond location is drawn **uniformly** from the list each episode.
- Every other entity (food, fires, rocks, bushes, hiding predators, animals) and the agent's start are placed **after** the pond and **never on it**.
- Thirst is **not** coupled to body temperature. A later off-by-default switch, in the style of `thermal.metabolic_coupling`, is possible but is not part of this plan.

---

## Analysis

Each subsection states what the code does today (file:line at `81d28c36`), then what that means for water. Line numbers drift; the developer re-locates by the quoted code, not by the number.

### A1. The template being mirrored: the two-sided nutrition axis (commit `379ec8fc`)

- `update_body` (`src/environment/core.py:155-541`) owns every body variable. Nutrition decays linearly (`new_nutrition = prev_nutrition - params.metabolic_cost`), refills on `info['ate_food']`, and is clipped once to `[0, max_nutrition]`. Death is folded into `done` **inside `update_body`**, both ends, the upper end under the static `params.overeating_death` gate (`core.py:~430-440`).
- `jax_step` stamps the termination label from the **same predicate** under the same static gate (`core.py:~1110-1125`). That is the fix for registry row "Over-eating never ended the episode…" (KNOWN_BUGS ~#192). Row ~#160 records the design guard that goes with it: compute the death test once in `update_body`, return it, and never re-derive it in `jax_step`.
- The drive (`calculate_drive`, `core.py:72-127`) is a Euclidean norm in **satiation units**. A second physical axis is rescaled by `range_S / range_axis`, where `range_S = satiation_deviation_range(params) = max(setpoint, max_satiation - setpoint)` (`core.py:49-70`). At shipped values `range_S = 100`, so every axis sits exactly 100 drive units from its own death, and that equals `death_penalty` (100). **The water axis must keep this property.**
- The thermal-off path of `calculate_drive` is the pre-thermal expression **verbatim**, reached by a static `if params.thermal_enabled:`. Water follows the same rule: a new static branch **before** the thermal branch, so the water-off path falls through to today's code unchanged.
- The logged `info['drive_hunger']` is written divide-first (`(S/range_S) - (setpoint/range_S)`) because the natural form differs by up to 2 ULP on half the axis. `info['drive_thirst']` uses the same divide-first form.

### A2. Reset, placement and the PRNG stream (`jax_reset`, `core.py:1707-2260`)

- The outer split is **5-way and byte-locked**: `key, agent_key, placement_key, body_key, property_key = jax.random.split(key, 5)`. Every later feature added streams with `jax.random.fold_in(<existing key>, <unique constant>)` instead of widening a split. Constants in use: `0xAE1`, `0x7150A1`, `0xA77AC7`, `0xC0A1–0xC0A3`, `0x7EE7`, `0xF00D`, `0xB05E`, and `999` for observation noise. **Water uses fold-in only**, with new constants `0xD81` (pond draw), `0xD82` (agent-start repair), `0xD83` (respawn repair) and `0xD84` (random start hydration). Grep confirms none of them is taken at the time of writing. The developer re-greps before committing.
- **Agent start** (`core.py:1731-1732`): `random_pos = randint(agent_key, (2,), 0, [H, W])`, drawn over the **whole grid** with **no** check against entities. The agent can start on a food, a bush or a hiding predator today. So "never on the pond" needs new code. It cannot be had by reordering.
- **Entity placement**: every maintained ladder world uses `placement.mode: per_entity`. This was measured by loading levels 00–06 through the trainer's loader. In that mode each entity samples a cell in its own spawn area, and then `resolve_overlaps_global` (`core.py:1328-1422`) runs **one** permutation and walks it, moving each entity whose cell is already taken to the first free in-area cell. Its occupancy mask starts **all-False** (`occupancy = jnp.zeros(total_cells, …)`). Seeding that mask with the pond cells is the cheapest correct exclusion: zero extra draws, and the pond is treated as already occupied.
- Two optional **post-passes** use `relocate_blocked_entities` (`core.py:1425-1495`): food-to-fire distance (D3) and bush-to-fire clearance. Each rebuilds its occupancy **from entity positions only** (`occupancy = zeros.at[flat0].set(True)`), so either pass could move a food or bush **onto** a pond cell. Both are off at every maintained level (`thermal.food_min_fire_distance: 0`, `thermal.bush_min_fire_distance: 0` in `configs/environment/default.yaml:~519, ~530`). This plan refuses water together with either pass at load time (§D3). Proving pond-aware feasibility for those passes is not needed for any world this plan ships.
- The `per_type` mode (`core.py:~1948-1981`, `place_in_area`) also starts from an all-False occupancy mask. No maintained world uses it, and water is refused with it at load (§D3).
- **Registry row ~#117** ("An entity whose spawn area is full is silently parked at cell (0,0)…"): both `resolve_overlaps_global` and `relocate_blocked_entities` fall back to flat index 0 with nothing raised. A pond takes up to `h·w` cells and makes that fallback more reachable, so this plan adds a **load-time capacity check** (§D3). The pond's own location is never computed by those functions. It comes from a table validated at load, so **pond placement cannot fall back; an infeasible pond configuration raises `ValueError` at load**.
- **Respawn** (`jax_step`, `core.py:~925-935`): a consumed resource respawns at `randint(res_keys[i], (2,), area[:2], area[2:])`, uniform in its area with **no** occupancy check. A respawning food or hiding predator can land on a pond cell. It needs the same "replace if on the pond" repair as the agent start (§D4).
- **Body init** (`core.py:~2005-2040`): `body_key1, body_key2, body_key3 = split(body_key, 3)`. `body_key1` is taken by random start body temperature (B1), `body_key2` by random start nutrition, `body_key3` by random start injury. Random start hydration needs its own `fold_in(body_key, 0xD84)`.
- **Registry row ~#94** (`body.start_satiation` is a dead knob): the loader reads it and nothing in `core.py` uses it. `jax_reset` sets `nutrition = params.start_nutrition` and derives satiation from that. Water must not repeat this: `water.start_hydration` must be the value `jax_reset` writes into `state.hydration` when the random start is off, and a test must fail if it is not (§T3).

### A3. Olfaction, and a smell normalisation consistent with the existing falloff

`sense_resource` (`src/environment/sensor.py:5-28`) is the one smell kernel. For a sampling point `x` it sums, over a pool of sources, `property_i · f(d_i)`, masked by `active_i` and `d_i <= sensor_radius`:

$$
f(d) = \begin{cases} 0.5^{-\gamma} & d < 0.001 \\ \dfrac{1}{d^{\gamma} + 10^{-10}} & \text{otherwise} \end{cases}
$$

Here `γ` = `sensory.decay_power` (1.0, registry setting) and `d` is Euclidean. `_sense_olfaction_at` (`sensor.py:30-41`) adds the three pools in the fixed order **res + animal + obs**, and the docstring notes that this order is bit-identical to older code. With `olfactory_grid_range: 1` (default) the field is sampled at a 5-cell diamond, so Olfaction is 25 dims.

**Pond smell.** A pond is a fourth pool of `n = h·w` sources, one per cell, each carrying the **per-cell** vector `p / n`, where `p` is the configured water vector (`[0.5, 0, 0, 0, 0.5]`):

$$
S_{\text{water}}(x) = \sum_{c \in P} \frac{p}{n}\, f\big(\lVert c - x \rVert\big), \qquad n = |P| = h\,w
$$

- **It uses the same `f`.** The kernel is `sense_resource` itself, called on the pond cells, so the distance falloff, the on-source rule and the radius mask cannot drift from what food uses.
- **Far field.** When `‖x − c‖ ≫` the pond's size, `f` is nearly equal over the cells and `S ≈ p · f(d̄)`: exactly one source of vector `p` at the pond's centroid. **A 2×2 pond smells like one item of total strength 1.0 (0.5 on the food channel, 0.5 on channel 4), not four.** For comparison, one food's `p` is `[1, 0, 0, 0, 0]`.
- **Near field**, `γ = 1`, 2×2 pond, per channel with weight 0.5:

  | Agent position | Sum of `f` over 4 cells ÷ 4 | Smell on food channel | One food at same spot (ch 0) |
  |---|---|---|---|
  | on a pond corner cell | (2 + 1 + 1 + 1/√2)/4 = **1.177** | 0.5 × 1.177 = 0.588 | on-source: 2.0 |
  | beside the pond (distance 1 to nearest cell) | (1 + 1/2 + 1/√2 + 1/√5)/4 = **0.664** | 0.332 | distance 1: 1.0 |

  So the pond is **quieter** than one food up close and equal far away. That is intended: the user asked for it to be less clear than EVAAA, with water and food sharing information. `math-reviewer` should check these two rows independently (§T4 pins them in a test, computed by numpy, not by the env).
- **Ordering and parity.** The water term is added **after** the obs pool, inside a static `if params.water_enabled:`. With water off the three-pool sum is not touched, so accumulation is bit-identical.
- **No per-episode jitter.** Water carries no `properties_std`. The vector is a static config constant (§D1).

**Channel labels live in two places, and neither is the observation.**
1. `sensory.olfactory_channel_names` in the config (`configs/environment/default.yaml:~263-268`, currently `Food / Odour A / Odour B / Bush / Tree`). The production video dashboard reads this through `channel_display_from_config` (`src/utils/eval_recording.py:~120`). It is display only, and the recording writer requires exactly `vector_size` entries.
2. A hard-coded list `['FOOD', 'AN-A', 'AN-B', 'BUSH', 'TREE']` in `sensor.build_sensory_viz` (`sensor.py:645`). This is read by the **old** renderer only (`renderer.py`), which is frozen pending retirement ([[RENDERER_LAYOUT_REDESIGN]] Revision 30).

The rename is done **in the pond world's config** (level 06, inherited by 07). It is not done in `default.yaml`, because in every non-water world channel 4 really is tree-only. This is a call made in this plan; see "Calls" at the end. The old renderer's hard-coded `TREE` token is left alone (frozen file). Water worlds render through the new dashboard.

### A4. Vision

`sense_visual` (`sensor.py:288-405`) concatenates `[res, animal, obs]` positions, properties, masks and sight-blockers. It builds a weight matrix (a Gaussian point-spread, since `visual_blur_enabled: true`), multiplies it by the properties, then clamps at 1.0 (`visual_value_mode: clamp`). At the default `visual_vector_size: 1` every entity writes 1.0 into the single "Visible" channel.

For water, each pond cell is appended as one more visual entity **after** the obstacles (static gate). It has visual vector `water.visual_properties` (`[1.0]`), is always active, has visual mask 0 ("none", always visible) and does not block sight. **Pond cells are not per-cell normalised in vision.** Vision reports presence per cell, so a 2×2 pond looks like a 2×2 block of "something is here", the same way four rocks would. Decision 4 asks for nothing more.

### A5. Observation layout, breakdown and noise — three places that must agree

- `get_observation` (`sensor.py:454-559`) appends named blocks and **raises** if the name order differs from `get_observation_breakdown` (`sensor.py:561-617`). The breakdown feeds every name-keyed consumer: the stats CSV (`src/utils/evaluation_core.py::_sensor_stat_columns`, which raises on an unknown name), `build_sensory_viz` (raises on an unknown name, `sensor.py:~725`), the dashboard panel registry, and the rPPO modulator input slicer (`src/models/recurrent_ppo_network.py:27`, resolved by name).
- **Hydration goes directly after "Body Temperature" and before "Interoceptive Nociception".** That keeps the directly-delivered levels contiguous (Satiation, Body Temperature, Hydration) ahead of the delayed percept, as body temperature did. The value is `hydration / max_hydration`, in `[0, 1]`, reading 0.5 at the setpoint. Satiation is normalised the same way.
- **Perceptual noise** (`sensor.py:407-452`) looks each breakdown name up in `params.noise_modality_order`, which the loader builds from the YAML key order of `perceptual_noise.modalities` via `_YAML_KEY_TO_SENSOR_NAME` (`config_loader.py:~2859-2884`). An unknown YAML key raises at load. A breakdown name with no modality raises a bare `KeyError` inside the jit trace, and the thermal plan recorded that failure as naming neither the config nor the fix. So:
  - add `"hydration": "Hydration"` to `_YAML_KEY_TO_SENSOR_NAME`;
  - add a `hydration:` block to `default.yaml`'s modalities **at the end of the list** (after `location`). Lookups are by name, so appending leaves **every existing noise index unchanged**, and the jitted noise code bakes in no shifted constant;
  - add a load-time check: `water.enabled` true without a `hydration` modality raises a named `ValueError`.
- **The noise arrays are padded to 13 slots** (`_NOISE_SLOTS = 13`, `config_loader.py:~2916`). Today 12 are used, so **hydration takes the last free slot.** No widening is needed, but the next modality after this one must widen the pad. The plan requires a comment saying so.
- **Observation noise draws** use `normal(fold_in(state.key, 999), obs.shape)`. With water off the shape is unchanged, so the noise is byte-identical. With water on the width grows by 1, which is a different world anyway.
- **Measured widths today** (resolved through `load_env_config` + `load_env_params`, CPU): levels 00/01 = 44, 02/03/04 = 52, 05 = 58, current 06 (noise) = 58. After this plan: new 06 = **59**, new 07 = **59**.
- **Obs-size flow to the agents.** rPPO takes `obs_dim` from a probe observation's shape (`train.py:~877`) and builds per-modality encoders from the breakdown (`recurrent_ppo_network.py:149-164`). dreamer_srl probes `obs_dim` and **asserts** it equals the breakdown total (`src/algorithms/dreamer_srl/dreamer_srl_main.py:~745-760`). Neither needs code for a new width. Both need the breakdown to be right, and §T6 builds both against level 06.
- **Curriculum modality fingerprint** (`train.py:~808-870`, mirrored in `dreamer_srl_main.py:~820-845`): recomputed at run time and never persisted, so appending a field breaks no saved run. Add `p.water_enabled` (defence in depth, since the width changes too).

### A6. Death, labels and where death causes go

Termination codes are an integer chain in `jax_step` (`core.py:~1105-1125`): 0 alive, 1 step limit, 2 starvation, 3 over-eating, 4 injury, 5 thermal. **Later assignments win**; thermal sits after truncation so a thermal death on the final step reports 5. This plan adds **6 = dehydration** and **7 = over-drinking**, stamped **after** thermal, inside a static `if params.water_enabled:`, from the predicates `update_body` returns.

Consumers of the codes, found by grep:

| Consumer | What it does | Change |
|---|---|---|
| `src/models/recurrent_ppo_trainer.py:~464, 484, 516, 542, 555` | real death = `termination_reason >= 2` | **none needed**: 6 and 7 are ≥ 2. Pinned by a test (§T3) |
| `src/algorithms/dreamer_srl/dreamer_srl_main.py:~1719` | truncation = `reason == 1` | none needed |
| `src/behavior/episode_metrics.py:40-45, 234-238, 258-277` | `Episode/Term_*` one-hot (sheeprl bridge path) | add `Term_Dehydration`, `Term_Overdrinking` |
| `train.py:1628, 2176, 2382, 2535`; `dreamer_srl_main.py:1248` | five **copies** of the literal `[(1,'MaxSteps'),…,(5,'Thermal')]` | replace all five with one shared constant (§D6) |
| `src/behavior/balance_metrics.py:75` | `_DEATH_CAUSES` | import the shared constant |
| `src/utils/trajectory_store.py:140-175` | column docstrings list codes 1–5 | text only |
| `check_env.py:35-36` | printed legend | text only |
| `scripts/eval/eval_rollout.py:121, 273, 471` | stores the integer per episode | none: 6/7 flow through as integers |
| `scripts/analysis/ladder/lad03_how_it_ends.py` | hard-codes three outcomes (step limit, starved, predator); registry row ~#116 already notes that it never checks its shares sum to 1 | **out of scope, noted.** Any level-06 or level-07 run read through it silently drops codes 6/7 from the shares. Ask `bug-curator` to extend row ~#116 |
| `scripts/analysis/studies/context_exploration/part4_readout.py:440` | reads `Term_Starvation / Term_Injury / Term_Thermal` columns only | **out of scope, noted.** It will not show thirst deaths |
| `src/utils/eval_recording.py::_snapshot_state` | recordings store **state snapshots only; no termination reason** | add `hydration` / `water_pos` snapshot fields. A recording's cause of death is derivable from the snapshot (`hydration` at 0 or max on the final frame). Adding a stored reason is out of scope; see Open items |

**Registry row ~#494** (the termination reason is unreliable when a body system is switched off: the injury code fires even with injury disabled) is the latent class to avoid. Codes 6 and 7 are stamped **only** inside the water gate, from the returned predicates. A water-off world has no hydration at all (`state.hydration is None`, §D2), so it cannot stamp them, and §T3 asserts over real rollouts of levels 00–05 that no reason outside `{0…5}` ever appears.

### A7. State shape and why the water-off graph can stay identical

`EnvState` and `EnvParams` are `flax.struct.dataclass`es (`src/environment/state.py:30-113, 115-511`). Existing parity gates compare **jaxpr SHA-1s** of `jax_step`, `jax_reset` and `update_body`: `tests/env/test_body_mechanics_parity.py::test_jaxpr_sha_identical` and `tests/env/test_bush_fire_clearance.py`, via `scripts/fixtures/generate_body_mechanics_parity_fixture.py::jaxpr_shas`, which passes params **traced**. Any new traced leaf renumbers those strings (the body-mechanics plan made every new field static for this reason).

- **New `EnvState` fields default to `None`.** `None` is an empty pytree, so a water-off state has exactly today's leaves and today's jaxpr. `update_body` already returns `starved = None` on off-paths for the same reason (`core.py:~176-181`). Code that reads `state.hydration` on a water-off world then gets `None` and fails loudly, the same idea as `thermal_field` being a `[0, 0]` array. Fixture code that iterates `dataclasses.fields(state)` and calls `np.asarray` already skips non-numeric dtypes (`scripts/fixtures/generate_metabolic_coupling_fixture.py:66-77`: `None` → object dtype → skipped).
- **New `EnvParams` fields are all static** (`pytree_node=False`). Arrays are held as tuples (the pond top-left table, the smell and visual vectors). Floats are static like the body-mechanics floats. The price is a recompile per distinct water setting, which is acceptable because these are not swept inside a run.
- **Consequence the plan relies on and must verify (§T1):** for every water-off world the jaxpr SHAs of all three functions are unchanged. If the developer finds that impossible, **stop and report**. Do not re-baseline those gates.

### A8. The renderer

Production episode videos have come from the new dashboard package (`src/environment/dashboard/`) since the user opened the retirement gate on 2026-09-18 ([[RENDERER_LAYOUT_REDESIGN]] Revisions 29–30, [[EVAL_RENDERER_SWITCHOVER]]). The old `renderer.py` stays on disk until two or three training runs have produced their videos through the new path. The dashboard:

- places vitals rows from a declarative registry (`dashboard/panels.py:~512-570`). Each row pairs an **observed** face with a **hidden** twin (the observed-versus-hidden rule, registry row ~#128 / D10);
- sizes panels from `min_size` functions, where a height mismatch between registry and painter is a live known defect (row ~#130);
- has a process-global icon cache that can make frame comparisons depend on test order (row ~#129);
- still has open layout defects on the old renderer (row ~#126).

**This plan does not patch the old renderer** beyond one change. It adds a `"Hydration"` branch to `build_sensory_viz` (required anyway: without it that function raises for a water world, and the dashboard also calls it). The pond, the hydration row and the renamed smell label are drawn **only in the dashboard**, under that package's own rules (§D8), and the frame-audit instruments are the gate.

### A9. EVAAA reference, and deliberate departures

`vendor/evaaa/evaaa_unity/Assets/Scripts/Agent/InteroceptiveAgent.cs`: `waterLevelRange` (L102), death when out of range (L585), drink on a `water`/`pond` tag via the **eat** interaction (L531-540), and `WaterUpdate` (L850-859), a rate that is a weighted sum of all three body levels plus a coupling term, scaled by `Time.fixedDeltaTime`. Departures, all deliberate per the decisions table:

1. **Linear drain**, not coupled to food or temperature.
2. **Drinking is automatic** on every step on a pond cell. There is no drink action and no new action dimension, so `action_dim` stays 6.
3. **The pond moves between episodes** (EVAAA's is fixed), because this grid world's senses reveal direction.
4. **Smell shares channels with food**, so it is less clear than EVAAA by design.

### A10. The 06 → 07 rename: which files actually reference `06-sensory_noise`

Grep over the tree, excluding gitignored data directories:

| File | Reference | Action |
|---|---|---|
| `configs/environment/experiment/basic/06-sensory_noise_10x10.yaml` | the file itself | `git mv` → `07-sensory_noise_10x10.yaml`; `extends:` → the new 06; header note; explicit hydration noise (§D7) |
| `tests/env/test_dashboard_layout.py:65, 615` | ladder world list; one test pins the noise world | repoint to 07; add the new 06 to the list |
| `tests/env/test_config_layer_silent_failures_20260723.py:49-52` | path constant `_NOISE_05` | repoint to 07; add Hydration to the "interoception clean" assertion |
| `tests/env/test_truncation_not_death.py:31, 42` | **comments only** (the test loads level 04) | untouched: historical note |
| `scripts/eval/make_render_fixture_recordings.py:71, 77, 231` | `NOISE_WORLD` constant + comments | repoint to 07; add a `POND_WORLD` for the renderer checkpoint |
| `configs/environment/experiment/behavior_probes/thermal/generate_thermal_probes.py:61` | `NOISE_SRC` (copies the noise block as raw YAML) | repoint to 07. Re-running it would now copy a `hydration:` noise entry into probe configs. That is harmless (water is off in those worlds) but is a text change to regenerated probes; tell `experiment-designer`, who owns them |
| `train_command-agent.sh:685, 4069` (live) and `:671, 1045, 1153, 1229, 4179` (comments / historical records) | launch lines | repoint the **two live** `--config` lines. Leave historical comment blocks as launched |
| `docs/environment/SCRIPTS_DEPENDENCY_MAP.md:232` | `make_render_fixture_recordings.py` row | update the path; add the new generator row (§D9) |
| `docs/experiments/active/basic_levels_q2_default/BASIC_LEVELS_Q2_DEFAULT.md:82` | obs-width table row | append a dated note row for 06 (59) and 07 (59); do not rewrite the historical row |
| `docs/develop/active/refactors/RENDERER_LAYOUT_REDESIGN.md`, `docs/develop/active/thermal/WARMING_COOLING_RATE_SCALES.md`, `docs/develop/active/issues/diag_fable5_20260704/fix_plan_h1h2h3_resume_config.md`, `docs/experiments/active/behavior_measures/thermal_probe_battery_bush_hiding.md`, `docs/reviews/…`, `docs/llm_wiki/…`, `docs/develop/active/meta/code_graph_benchmark/…`, `configs/…/archive/…` | historical | **untouched** |

**A naming hazard the rename creates.** Analysis scripts label past runs of the noise world as `lvl06`, for example `scripts/analysis/studies/modulator_clues/_inj.py:15-20` and `scripts/analysis/studies/injury_dependence/run_manipulations.py:42-48`. Those labels are tied to run IDs trained on the **old** level 06, and renaming them would falsify history, so they stay. Two more text labels go stale the same way and also stay: `scripts/analysis/nmn/run_mod_distribution.py:145` ("ON at basic level 06") and `scripts/analysis/studies/internal_state_reward/f04_thermal_scale.py:59` ("only basic/05 and basic/06 switch the temperature system on"; 07 now does too). From this change on, "level 06" means the pond world in configs and the noise world in those scripts. The plan requires a one-line entry in the critical-settings change log (§D7) naming this, so an analyst reading `lvl06` checks the run date.

### A11. Known-bug rows this plan relies on (from `docs/develop/active/issues/KNOWN_BUGS.md`)

| Row (approx. line) | What it says, in brief | How this plan uses it |
|---|---|---|
| ~#94 | `body.start_satiation` is loaded and never used | `water.start_hydration` must be written at reset; §T3 fails if inert |
| ~#117 | full spawn area → entity silently parked at (0,0) | load-time capacity check; runtime test that no active entity leaves its area or sits on the pond (§T2); pond itself raises at load, never falls back |
| ~#123 | saved run configs stop loading when a key becomes mandatory | `water.enabled` gets a `_ERA_KEYS` row in `saved_config_compat.py` (§D5) |
| ~#124 | backward-compat test skips every ladder world | this plan adds its own loader test over levels 00–07 (§T5) |
| ~#126, #128, #129, #130 | dashboard defects: overlap, observed-vs-hidden, icon cache, panel geometry | renderer work goes through the dashboard's rules and audit (§D8, C6) |
| ~#132, #133, #134 | known-red tests (archived-config pin; 17 factor fragments; 3 hard-coded 8-wide-vision tests) | recorded as the inherited baseline (§T0); they must not halt implementation |
| ~#160 | compute a death test once in `update_body`, never re-derive in `jax_step` | hydration death predicates are returned, and `jax_step` reads them |
| ~#192 | over-eating label without a death | the same one-predicate rule for codes 6/7 |
| ~#371 | a noise config claimed clean interoception but inherited 10× noise | level 07 sets hydration sigma **0.0 explicitly** |
| ~#494 | termination code unreliable when a body system is off | codes 6/7 cannot exist on a water-off world; asserted over rollouts |

`bug-curator` was not consulted; the rows above were read directly at the line numbers the requester supplied. After implementation, ask `bug-curator` to record any new rows (for example the naming hazard in §A10 if it bites).

---

## Target-first water clock (calibration)

**Targets, stated before any numbers are solved:**

| # | Target | Source |
|---|---|---|
| W1 | Setpoint → dehydration death, standing away from water: **150–200 steps** | decision 8 |
| W2 | Death at both ends, judged on the raw clipped value: `W <= 0` and `W >= max` | decision 3 |
| W3 | Setpoint at the **middle** of `[0, max]`, so each end is the same distance from comfort | decision 3 |
| W4 | Full-scale water deviation weighs the same drive as full-scale hunger (100 units = `death_penalty`) | A1 invariant |
| W5 | A thirsty agent refills to the setpoint in **roughly 10–20 steps** on the pond: long enough that the pond is an exposed place to wait, short enough that it is a trip, not a camp | derived from decision 9 (ambush trade); proposed here, user may move it |
| W6 | Over-drinking from the setpoint takes **roughly 15–25 steps** of continuous standing: reachable, so it is a real brake (decision 6), but avoidable by stepping off. Every cell of a 2×2 pond touches its edge, so one move always exits | derived from decision 6; proposed here |
| W7 | Arithmetic **exact in float32**, so death steps are integers a test can pin without tolerance | engineering |

**Solving.** Mirror nutrition's axis: `max_hydration = 200`, `hydration_setpoint = 100` (W3, W4: `range_W = max(100, 200 − 100) = 100`, so the drive scale factor `range_S / range_W = 1` and one hydration unit costs one satiation unit). Then:

- W1 with W7: drain `d` with `100 / d ∈ [150, 200]` and `d` exactly representable. **`d = 0.625` (= 5/8)** gives `100 / 0.625 = 160` steps exactly.
- W5 / W6 with W7: gain per step on the pond `g`, net `g − d` per step. **`g = 5.625` (= 45/8)** gives a net of **+5.0 exactly**. Refilling from 50 to 100 takes 10 steps, from 25 takes 15 (W5). Over-drinking from 100 takes `100 / 5 = 20` steps (W6).
- Order within a step, mirroring nutrition: `W' = clip(W − d + g·on_pond, 0, max)`. Drain and refill both happen before the single clip, so a step on the pond is net +5 and never "drain, die, then drink".

**Clock table (every value from setpoint, `death_penalty = 100`, episode cap 500):**

| Clock | What kills | Rate | Steps setpoint → death | Arithmetic | Share of 500-step cap |
|---|---|---|---|---|---|
| Food | starvation, `N <= 0` | −1.0 / step (`body.metabolic_cost`) | **100** | 100 / 1.0 | 20 %. Each eaten item nets +5 (gain 6 − eating cost 1), so refilling 100 steps of clock is ~20 items and a full 500-step episode ~80 items |
| Cold | body temp < −15 away from a fire | shipped: world −31..−29, `k_loss` 0.02, warming 2.0 / cooling 0.25 | **~92**: the midpoint of **86–99**, measured on 600 real resets at shipped values (`CONFIG_CRITICAL_SETTINGS.md` change log, 2026-09-19) | quoted, not re-derived here | ~18 % |
| **Water** | dehydration, `W <= 0` | **−0.625 / step** | **160** | 100 / 0.625 | 32 %. **At least one pond visit per episode is unavoidable**, and one well-timed visit can cover a whole episode: walk 153 steps, drink 39 (to 199.375), walk 318 = 510 steps. A cautious agent needs two |
| Water, upper end | over-drinking, `W >= 200`, standing on the pond | **+5.0 / step net** | **20** | (200 − 100) / (5.625 − 0.625) | — |
| Refill 50 → 100 | on the pond | +5.0 net | 10 | 50 / 5 | — |
| Refill 25 → 100 | on the pond | +5.0 net | 15 | 75 / 5 | — |

Water is the slowest clock (decision 8). It is still short enough that every full episode needs at least one pond visit, and a refill from near-empty to near-full takes about 39 steps standing on the pond. So the pond cannot be ignored, and filling up means a long, exposed stay.

**Random start hydration** (mirroring level 03's nutrition draw of `[0, 200]`): level 06 turns it on over the full reachable span `[0, 200]`. **Half** of episodes then start within 50 units of an end, and a quarter within 25. One that starts at 195 and walks onto the pond dies on its first step there, which is the same property the nutrition draw already has. **Policy-independent early deaths:** with drain 0.625, a fraction `0.625·k/200` of episodes is dead of thirst by step k whatever the agent does. That is about **5 % by step 16** and about 16 % by step 50, before a pond can plausibly be reached. Level 03's nutrition draw has the same property at `1.0·k/200`. Survival steps is the project's metric, so this is surfaced as a user call below. This is a call; see "Calls".

---

## Implementation Plan

### Design

**One gate.** A new top-level config block `water:` with a mandatory `enabled` key, the same pattern as `thermal.enabled` (no fallback). Every other water key is **conditional-mandatory**: read with `config.get_mandatory(...)` only inside `if water_enabled:` in the loader. When the gate is off, the loader fills `EnvParams` with inert sentinels and **reads no other water key**, so a water-off config may omit them. Every consumer in `core.py` / `sensor.py` is behind a **static** `if params.water_enabled:`.

**Data flow per episode.**

```
load:  water block ──► validate ──► static top-left table T (list | random | center)
reset: k_pond = fold_in(placement_key, 0xD81) ─► idx ~ U{0..|T|-1} ─► water_pos = T[idx] + offsets(h,w)
       pond mask ─► seeded into resolve_overlaps_global occupancy (entities never on pond)
       agent start: if on pond ─► first non-pond cell of permutation(fold_in(agent_key, 0xD82))
       hydration0 = start_hydration  | U[low, high] via fold_in(body_key, 0xD84)
step:  respawn: if on pond ─► first non-pond in-area cell of permutation(fold_in(respawn_key, 0xD83), i)
       on_pond = any(water_pos == new_agent_pos)          → info['drank']
       update_body: W' = clip(W − d + g·drank, 0, max); dehydrated = W' <= 0; overdrank = W' >= max
                    done |= dehydrated | overdrank ; return (W', dehydrated, overdrank)
       jax_step:    reason 6 / 7 from the returned predicates (after thermal's 5)
       drive:       extra axis (W − W_set)·range_S/range_W
       obs:         "Hydration" = W / max after Body Temperature; smell pool 4; visual entities appended
```

**Placement modes, one code path.** All three modes reduce at load time to a **static table of top-left cells** `T`, stored in 0-based array coordinates. Reset draws `idx = randint(k_pond, (), 0, len(T))` and looks the cell up. `center` has `|T| = 1`. The draw still happens, and it costs nothing observable because it is a fold-in stream.

**Coordinate convention: 1-based in YAML, like every other coordinate in these configs.** Measured on the resolved level-06 params: YAML `start_pos: [5, 5]` loads as array `(4, 4)`. Spawn areas are written 1-based inclusive (`_apply_edge_margin`, `config_loader.py:375-400`) and load as 0-based half-open, so `[[1, 1], [10, 10]]` is the **whole** 10×10 grid, `[0, 0, 10, 10]`. `generate_thermal_probes.py:64` states the same rule: config `[R, C]` is array `(R−1, C−1)`. So a `water.candidates` entry `[r, c]` is 1-based, and the loader subtracts 1. The rest of this plan quotes blocks in **array** coordinates unless it says "YAML".

### D1. Config schema — every new key (all under `water:`)

| YAML path | `default.yaml` value | Level 06 value | Read when | Validation (at load, `ValueError` naming the key) |
|---|---|---|---|---|
| `water.enabled` | `false` | `true` | **always (mandatory)** | bool |
| `water.placement` | `list` | `list` | enabled | one of `list`, `random`, `center` |
| `water.size` | `[2, 2]` | inherited | enabled | two ints ≥ 1 |
| `water.candidates` | `[[2, 2], [2, 8], [8, 2], [8, 8]]` (YAML, 1-based top-left) | inherited | enabled **and** placement == list | non-empty; list of `[r, c]` ints, 1-based like `start_pos`; no duplicates; each block inside the grid and inside `edge_margin`; none covers `environment.start_pos` when `environment.random_start_pos` is false |
| `water.edge_margin` | `1` | inherited | enabled | int ≥ 0; applies to **all three modes** (below) |
| `water.max_hydration` | `200.0` | inherited | enabled | > 0 |
| `water.hydration_setpoint` | `100.0` | inherited | enabled | `0 <= setpoint <= max` (same guard as nutrition, `config_loader.py:~2510-2530`) |
| `water.start_hydration` | `100.0` | inherited | enabled **and** `random_start_hydration` false | `0 < start < max` (a start at either end is dead on arrival) |
| `water.random_start_hydration` | `false` | `true` | enabled | bool |
| `water.start_hydration_low` / `water.start_hydration_high` | `0.0` / `200.0` | `0.0` / `200.0` | enabled **and** random flag true | `0 <= low <= high <= max`. **The random draw may land exactly on the floor.** `jax.random.uniform` samples `[low, high)`, so `low = 0.0` can give 0.0, which dies on step 1 with reason 6, while a fixed `start_hydration` of 0 is refused. This mirrors `start_nutrition_low: 0` and is accepted; set `low > 0` if a step-1 death is unwanted |
| `water.drain_per_step` | `0.625` | inherited | enabled | ≥ 0 |
| `water.drink_gain_per_step` | `5.625` | inherited | enabled | ≥ 0 |
| `water.properties` | `[0.5, 0.0, 0.0, 0.0, 0.5]` | inherited | enabled | length == `sensory.vector_size`, each in `[0, 1]`. Spelled `properties` like entities, never `property` (the env-config-reviewer's known `property` vs `properties` trap) |
| `water.visual_properties` | `[1.0]` | inherited | enabled | length == `sensory.visual_vector_size`, each ≥ 0 |
| `perceptual_noise.modalities.hydration` | `{mode: state_dependent, sigma: 0.1, injury_noise_scale: 1.5, clip_min: 0.0, clip_max: 1.0}`, **appended last** | inherited from default (noise off at 06) | when noise is enabled and water is on | must exist when `water.enabled` (named `ValueError`) |

The default candidates are the four quadrant blocks of the 10×10 world, array rows/cols 1–2 and 7–8. That respects `edge_margin: 1`, which excludes the border ring of array rows/cols 0 and 9. None of them covers YAML `[5, 5]`, the default `start_pos` (array `(4, 4)`). Candidate values are experiment design; `experiment-designer` may change them for level 06 in the same change without touching code.

**Placement validation, per mode (all at load, `ValueError` naming the mode, the offending cell and the grid):**

- Rules are stated in **array** coordinates, after the loader's 1-based → 0-based conversion. Block for top-left `(r, c)` = rows `r … r+h−1`, cols `c … c+w−1`. "Inside grid" = `0 <= r`, `r + h <= H`, same for columns. "Inside margin `m`" = `m <= r` and `r + h <= H − m`, same for columns. That is the same inset `_apply_edge_margin` applies to obstacle areas.
- **list**: every candidate inside grid and margin; no duplicates (a duplicate silently doubles one location's probability); if `random_start_pos` is false, no candidate's block contains `start_pos`.
- **random**: `T` = every `(r, c)` inside grid and margin, minus those whose block contains `start_pos` when `random_start_pos` is false. `|T| = 0` → `ValueError` ("grid too small for a h×w pond with margin m"). `candidates` is **not read**.
- **center**: `T = {((H − h) // 2, (W − w) // 2)}`, floor for odd remainders (documented). Must be inside the margin and must not contain a fixed `start_pos`, else `ValueError`. **Note**: on the default 10×10, center = array rows/cols 4–5, which **contains the default `start_pos`** (YAML `[5, 5]` = array `(4, 4)`). That is legal only because `random_start_pos: true` at every ladder level (measured); a fixed-start center world is refused.
- **Refused combinations** (named `ValueError`): `placement.mode: per_type` with water on; `thermal.food_min_fire_distance > 0` or `thermal.bush_min_fire_distance > 0` with water on (§A2; lift later with a pond-aware feasibility proof if a world needs it).
- **Capacity check (registry ~#117)**: `resolve_overlaps_global` visits slots in the fixed concat order `[res, pred, obs, neutral]` (`core.py:~1832`), and each earlier slot occupies at most one cell. So for slot `i` at scan position `k_i` (0-based) with **post-inset** spawn area `A_i`, require `|A_i| − max over t in T of |pond(t) ∩ A_i| >= k_i + 1`. When that holds, the scan always finds a free, in-area, non-pond cell and the (0,0) fallback cannot fire from the pond. A check against the total slot count would be simpler, but it **wrongly refuses level 06** (campfire area 25 cells < 45 slots).
  - **Level 06, computed from the resolved config.** Spawn areas were measured on today's level-06 params: every resource, animal and non-campfire obstacle area is `[0, 0, 10, 10]` (100 cells), and the campfire's is `[2, 2, 8, 8]` (36 cells) after its `edge_margin: 2`. Scan order: food 4 + hiding predator 12 (positions 0–15), predator 2 (16–17), campfire 3 (18–20), rock 12 (21–32), tree 0, bush 10 (33–42), rabbit 2 (43–44).
  - Campfire: every default candidate touches the 36-cell area in exactly one corner cell, so the largest overlap is 1, and 36 − 1 = 35 ≥ 21. Passes.
  - Every other slot: 100 − 4 = 96 ≥ 45. Passes.
  - The fire-separation rule (`thermal.min_fire_separation`) tightens fire placement further. That is pre-existing and not covered by this check, and the plan does not claim otherwise.

### D2. `src/environment/state.py`

```python
# EnvState — APPEND at the very end (after `last_action`), both with default None:
    # Water (THIRST_WATER_PLAN). None on every water-off world: None is an empty
    # pytree, so the state has exactly the pre-water leaves and every jaxpr built
    # over it is unchanged (tests/env/test_water_parity.py pins the SHAs). A read on
    # a water-off world therefore gets None and fails loudly, like thermal_field's
    # [0, 0] shape trick.
    hydration: Optional[jnp.ndarray] = None   # [] float32
    water_pos: Optional[jnp.ndarray] = None   # [h*w, 2] int32, fixed for the episode

# EnvParams — new STATIC fields (pytree_node=False), grouped with a header comment:
    water_enabled: bool
    water_block_h: int
    water_block_w: int
    water_topleft_table: tuple            # ((r, c), ...) — validated at load, never empty when enabled
    water_max_hydration: float
    water_hydration_setpoint: float
    water_start_hydration: float
    water_random_start_hydration: bool
    water_start_hydration_low: float
    water_start_hydration_high: float
    water_drain: float
    water_drink_gain: float
    water_cell_property: tuple            # properties / (h*w), length vector_size (A3 normalisation)
    water_visual_property: tuple          # length visual_vector_size (NOT normalised, A4)
```

Water-off sentinels: `False, 0, 0, (), 0.0, 0.0, 0.0, False, 0.0, 0.0, 0.0, 0.0, (), ()`. Flax requires defaulted fields to come after every non-default field; the two `EnvState` fields go last for that reason. If `Optional` and default `None` are not accepted by the installed flax, **stop and report**. Do not switch to zero-size arrays, which would change the jaxpr.

### D3. `src/environment/config_loader.py`

1. In `load_env_params`, next to the thermal gate (`~1650-1661`): `_water_on = bool(config.get_mandatory('water.enabled'))`. Inside `if _water_on:` read every D1 key with `get_mandatory`, validate (D1 rules, per-mode placement, refused combinations, capacity check), build `water_topleft_table` and `water_cell_property = tuple(p / (h*w))`. Else set the sentinels and read nothing else.
2. `_YAML_KEY_TO_SENSOR_NAME` (`~2859`): add `"hydration": "Hydration"`, with a comment that it and the `default.yaml` block are mutually blocking and must land together (the existing comment pattern).
3. `_parse_noise_config` (`~2885-2957`): no logic change. Extend the `_NOISE_SLOTS` comment to say hydration took the 13th and last slot, so the next modality must widen `EnvParams.noise_*`.
4. After noise parse, if `_water_on` and `"Hydration" not in noise_modality_order`, raise `ValueError("water.enabled needs a perceptual_noise.modalities.hydration entry …")`.

### D4. `src/environment/core.py`

1. **Constants** next to `_THERMAL_*_KEY` (`~1554`): `_WATER_POND_KEY = 0xD81`, `_WATER_AGENT_KEY = 0xD82`, `_WATER_RESPAWN_KEY = 0xD83`, `_WATER_START_KEY = 0xD84`, with the same uniqueness comment.
2. **Helper** `water_deviation_range(params)` = `max(setpoint, max_hydration − setpoint)`, mirroring `satiation_deviation_range`.
3. **`calculate_drive(satiation, injury, params, body_temp=None, hydration=None)`**: new static branch **first**. If `params.water_enabled` and `hydration is None`, raise a named `ValueError`. Build axes `[satiation, injury]`, append the thermal axis if thermal is on (the same expression as today), then append `w_axis = (hydration − W_set) * (range_S / range_W)`. Targets are `[setpoint, 0, (0), 0]`, and the result is the norm. **The existing thermal-on and thermal-off paths below it are not edited.**
4. **`resolve_overlaps_global(…, pre_occupied=None)`**: new keyword. Under `if pre_occupied is not None:` (static) the initial `occupancy = pre_occupied`. The off path is unchanged.
5. **`jax_reset`**, all under `if params.water_enabled:`:
   - before "# 1. Agent Position": `T = jnp.asarray(params.water_topleft_table)`; `idx = jax.random.randint(jax.random.fold_in(placement_key, _WATER_POND_KEY), (), 0, T.shape[0])`; `water_pos = T[idx] + offsets` (static `offsets` from `h, w`); `pond_flat` / `pond_mask[H*W]`.
   - after `agent_pos` is computed: `on = pond_mask[agent_pos flat]`; `perm = jax.random.permutation(fold_in(agent_key, _WATER_AGENT_KEY), H*W)`; first `perm` entry with `~pond_mask`; `agent_pos = where(on, that cell, agent_pos)`. That is uniform over non-pond cells (A2 derivation: `P(c) = 1/N + (k/N)·1/(N−k) = 1/(N−k)`).
   - `per_entity` branch: pass `pre_occupied=pond_mask` to `resolve_overlaps_global`.
   - body: `hydration0 = uniform(fold_in(body_key, _WATER_START_KEY), (), low, high)` if the random flag is set, else `params.water_start_hydration`.
   - `EnvState(..., hydration=jnp.float32(hydration0), water_pos=water_pos)`. Water-off: the two fields are not passed, so they stay `None`.
6. **`jax_step`**:
   - respawn (after `res_pos_after_reg`, under the gate): for respawned slots whose new cell is a pond cell, replace it with the first in-area non-pond cell of a per-slot permutation drawn from `fold_in(respawn_key, _WATER_RESPAWN_KEY)`, vmapped over slots (split that fold-in key `num_res` ways; it is a new stream, so this is not a widening). This excludes pond cells only; it adds no general occupancy check, which is pre-existing behaviour and out of scope.
   - **Named fallback if the per-slot permutations cost too much (§S).** Draw **one** permutation of `H·W` per step from the same fold-in key. The k-th respawning slot that needs a repair (ranked by slot index with a cumulative sum over the "needs repair" mask) takes the k-th cell of that permutation that is in its area and off the pond. At level 06 every resource shares one full-grid area, so "k-th valid cell" is a single `cumsum` over the permutation. Where areas differ, the loader refuses the fallback with a named error. Both variants live under the static water gate, so the water-off graph is untouched either way. The developer implements the per-slot version first and switches only if §S measures level 06 more than 5 % slower than level 05 with the respawn repair as the dominant cost (profile it to show that).
   - `info['drank'] = jnp.any(jnp.all(state.water_pos == new_agent_pos, axis=-1))`, under the gate.
   - `update_body` returns an **11th element** `water_out`: `None` when off; `(new_hydration, dehydrated, overdrank)` when on. **Extend the ten-name unpack at `core.py:~1099`** (`new_satiation, …, done, starved = update_body(...)`) **to eleven names** (`…, done, starved, water_out`). That unpack is the one production caller, and leaving it at ten raises `ValueError: too many values to unpack` on every world. The test and script callers index or slice the tuple (`test_body_mechanics_units.py:139/428`, `test_thermal_rate_scales.py:192/218`, `scripts/analysis/studies/internal_state_interactions/validate.py:121` uses `out[:9]`), so they are unaffected. This follows the "append, never insert" rule set by `starved`.
   - reason chain: after `if params.thermal_enabled: reason = where(thermal_death, 5, reason)`, add `if params.water_enabled: reason = where(dehydrated, 6, reason); reason = where(overdrank, 7, reason)`.
   - drive: pass `hydration=state.hydration` / `hydration=new_hydration` **only** under the gate (a separate call form, so the off path's call is textually today's).
   - `info['drive_thirst'] = ((W'/range_W) − (W_set/range_W))**2` under the gate (divide-first, A1).
   - `new_state = state._replace(..., **({'hydration': new_hydration} if water_enabled else {}))`. `water_pos` carries through untouched.
7. **`update_body`**: after the thermal block, `if params.water_enabled:` compute `new_W = jnp.clip(state.hydration − params.water_drain + jnp.where(info['drank'], params.water_drink_gain, 0.0), 0.0, params.water_max_hydration)`; `dehydrated = new_W <= 0.0`; `overdrank = new_W >= params.water_max_hydration`; `done = where(dehydrated | overdrank, True, done)`; `water_out = (new_W, dehydrated, overdrank)`. Else `water_out = None`. Update the docstring's return description.

### D5. `src/environment/saved_config_compat.py`

- New era constant `_ERA_WATER = "THIRST_WATER_PLAN C2 (<commit date>)"` and row `"water.enabled": (False, _ERA_WATER, "static `if params.water_enabled` everywhere in core/sensor; false = no water leaves, no water ops (tests/env/test_water_parity.py)")`.
- `apply_saved_config_compat`: add `to_supply.extend(_check_block(cfg, "water", source))`, always, like the body block. A saved config without a `water` block gets `water.enabled: false`, logged. No other water key is supplied, because none is read when the gate is off.
- Update the module docstring's list of eras.

### D6. Termination-reason names: one shared constant

`src/behavior/episode_metrics.py` is pure numpy and already holds the codes, so it gets:

```python
TERMINATION_REASONS = ((1, "MaxSteps"), (2, "Starvation"), (3, "Overeating"),
                       (4, "Injury"), (5, "Thermal"), (6, "Dehydration"), (7, "Overdrinking"))
```

`episode_finalise_episode` and `episode_wandb_keys` are built from it (the key count goes 21 → 23; update the module docstring). The module-level `_TERM_*` constants (`episode_metrics.py:40-45`) and the one-hot lines at `:234-238` are **derived from `TERMINATION_REASONS`** (or deleted), so that they do not become a sixth copy. `train.py` (4 sites), `dreamer_srl_main.py` (1 site) and `balance_metrics._DEATH_CAUSES` (codes ≥ 2) import it and stop carrying literals. On water-off runs this logs two always-zero keys, the same as `Term_Thermal` does on thermal-off runs today.

### D7. Configs

1. **`configs/environment/default.yaml`**: add the `water:` block (D1 values, `enabled: false`) with a header comment in the thermal block's style: gate mandatory, everything else conditional-mandatory, no entity-list entries (list-replace hazard). Append the `hydration:` noise modality **last**, with a comment that it is at the end so no existing index moves.
2. **New `configs/environment/experiment/basic/06-pond_thirst_10x10.yaml`**: `extends: environment/experiment/basic/05-campfire_thermal_10x10`. Plain-language header (purpose, what it adds, composition). Contents:
   - `water: {enabled: true, random_start_hydration: true, start_hydration_low: 0.0, start_hydration_high: 200.0}`, everything else inherited;
   - `sensory.olfactory_channel_names` redeclared in full: `{Food, "shared with water"}`, `{Odour A, predator-leaning}`, `{Odour B, neutral-leaning}`, `{Bush, ""}`, `{Odour C, water-leaning}`. It must be redeclared whole (lists replace wholesale; §A3).
   - It does **not** redeclare `obstacles:`, so the `blocks_animals` list-replace trap does not arise.
3. **`git mv configs/environment/experiment/basic/06-sensory_noise_10x10.yaml configs/environment/experiment/basic/07-sensory_noise_10x10.yaml`**, then edit:
   - `extends: environment/experiment/basic/06-pond_thirst_10x10`;
   - header note "RE-LEVELED 2026-09-29 … THE WORLD CHANGED: now also carries the pond and thirst";
   - under `perceptual_noise.modalities` add `hydration: {mode: "constant", sigma: 0.0, injury_noise_scale: 0.0}` next to the other clean interoceptive channels (registry ~#371: the sigma is stated, not inherited).
4. **Every stand-alone full config and inline test config that lacks an `extends:` gains `water: {enabled: false}`.** The grep at plan time (`^thermal:` or inline `'thermal': {` without `extends:`) found:
   - `configs/verification/{observability_gates_S1..S4, olfaction_parity_neutral, olfaction_parity_predator}.yaml`
   - `configs/continual/nmn_double_return_stages/01..05_*.yaml`
   - `tests/fixtures/trajectory_collection/dual_format_config.yaml`
   - inline configs in `tests/environment/test_behavior_measures.py`, `tests/environment/test_per_tag_distance_logging.py`, `tests/env/{test_behaviour_validation, test_body_temperature_observation, test_bush_blocks_animals, test_disengage_on_contact, test_distributional_yaml, test_entities_schema, test_inactive_animal_offgrid, test_inclusive_integer_range_sampling, test_initial_state_ranges, test_int_distributional_sampling, test_no_recompile, test_per_episode_count, test_per_episode_logging, test_per_episode_sampling, test_predator_jump, test_thermal_reward_gate, test_visual_properties}.py`, `tests/scripts/{test_eval_stochastic_key_distinct, test_parallel_eval_step0_seeding}.py`
   - `scripts/eval/make_render_fixture_recordings.py` if it builds a raw config.

   **The authoritative list is whatever raises `water.enabled is required but missing` when each module is run.** The grep above is the starting point, not a proof.
5. **`tests/env/fixtures/frozen_parity_worlds/environment__default.yaml`**: add `water: {enabled: false}` plus a row in its README's "Mandatory keys added after the freeze" table (allowed: mandatory and provably inert, proven by `test_unified_parity.py` staying green).
6. **`tests/env/fixtures/saved_run_configs/*.yaml`**: **not edited**. These are frozen runs; compat supplies the key (D5).
7. **Archived configs** (`configs/environment/experiment/archive/`): **not migrated**, per project policy.
8. **`configs/environment/experiment/level05_body_interactions/factors/*.yaml`**: these fragments have no `extends:` and no `thermal:` block, so they are not full worlds (row ~#133). Not edited.

### D8. Renderer (episode-video dashboard) — built under [[RENDERER_LAYOUT_REDESIGN]]'s rules

These are requirements. Painter detail follows that plan's conventions, and its owner or `visual-design-reviewer` may adjust colours and glyphs.

1. `src/environment/sensor.py::build_sensory_viz`: add `"Hydration"` to the `("Satiation", "Nutrition", "Injury", "Interoceptive Nociception")` intensity-tile group. That group is picked up by name, and without this branch the function raises for every water world.
2. `src/environment/dashboard/episode.py`: `VIZ_NAME["Hydration"] = "Hydration"`; a vitals row `("hydration", "Hydration", …)` whose **true** value is `state.hydration / max_hydration` and whose **observed** value comes from the sense only if `self.has("Hydration")`, with a setpoint mark at 0.5.
3. `src/environment/dashboard/panels.py`: a `PanelSpec(key="hydration", group="vitals", order=55, kind="vital_row", breakdown_names=("Hydration",), present=lambda ctx: ctx.water and ctx.observed("Hydration"), …)` and its `hydration_hidden` twin (`ctx.water and not ctx.observed("Hydration")`). The twin keeps the observed-vs-hidden rule (~#128) intact for any future config that hides hydration. `LayoutContext.from_params` gains `water = bool(params.water_enabled)`.
4. **Arena and minimap**: the pond is drawn as **ground cover** on its cells, under occupants. That is the redesign's "variant H" (terrain as ground cover, occupants in slots on top). A predator standing in the pond therefore stays visible. The snapshot carries `water_pos` (below).
5. `src/utils/eval_recording.py::_snapshot_state`: `if getattr(state, 'hydration', None) is not None: snap['hydration'] = float(...)`; the same for `water_pos` (`np.asarray`). Old recordings lack both keys and render as before.
6. **Smell label**: nothing to code. The dashboard reads `sensory.olfactory_channel_names` from the run's config (D7.2).
7. **Old renderer (`renderer.py`)**: no drawing change (frozen, retiring). Requirement: rendering a level-06 recording through it must **not raise**. Missing pond and hydration on that path are accepted and must be stated in its module docstring.
8. **Gates for this checkpoint**:
   - `tests/env/test_dashboard_layout.py` with levels 06 and 07 added. The packer must fit the vitals card with the extra row at the fixed canvas; the known ~#130 height mismatch is exactly what could bite here, so check the rendered frame, not the registry.
   - a level-06 recording made with `scripts/eval/make_render_fixture_recordings.py` (`POND_WORLD`) and rendered;
   - `scripts/eval/render_layout_audit.py` over that frame, no new findings.
   - Run layout tests in their own process (icon-cache hazard ~#129).

### D9. Scripts and fixtures

- **New** `scripts/fixtures/generate_water_parity_fixture.py`: the same shape as `generate_body_mechanics_parity_fixture.py`, whose `rollout_world`, `jaxpr_shas` and `_leaf_name` it **imports**, so there is one copy of the rollout loop. `--src-root` is required with no default, and it refuses a tree with uncommitted `src/` or `configs/` changes. Worlds: `configs/environment/default.yaml` and `basic/00–05`, plus `basic/06-sensory_noise_10x10.yaml` under its **pre-change** name. Seeds 0–15 × 300 auto-resetting steps (the `MAX_T` / `SEEDS` of the body-mechanics generator). It records every `EnvState` leaf by path, the observation with and without noise, reward, done, `termination_reason`, every `info` key, and the three jaxpr SHAs. Output: `tests/env/fixtures/water_parity/pre_change_rollouts.npz` + `README.md` naming the source commit SHA and command.
- `scripts/eval/make_render_fixture_recordings.py`: `NOISE_WORLD` → 07; new `POND_WORLD` → 06.
- `configs/environment/experiment/behavior_probes/thermal/generate_thermal_probes.py`: `NOISE_SRC` → 07 (A10).
- `scripts/verification/verify_noise.py` builds an `EnvState` by hand. It needs **no** change because the new fields default to `None`; §C2 confirms by running it.

### D10. Documentation, same change as the code (maintenance contracts)

| Doc | Change | Commit |
|---|---|---|
| `docs/environment/CONFIG_GUIDE.md` | new `water:` gate section (conditional-mandatory pattern, list-replace note for `candidates`, placement modes); Maintenance Contract item 4 note that the parity gate for this change is `test_water_parity.py` | C2 |
| `docs/environment/02_config_schema.md` | every D1 key with type, default, "read when" | C2 |
| `docs/environment/CONFIG_CRITICAL_SETTINGS.md` | registry rows `water.enabled`, `water.drain_per_step`, `water.drink_gain_per_step`, `water.max_hydration` / `water.hydration_setpoint`, `water.placement` / `candidates`; **dated change-log entry** (what, why, blast radius: water-off worlds byte-identical, measured; level 06 new; old 06 → 07 and the world changed; the `lvl06` naming hazard in analysis scripts) | C2 (entries), C5 (ladder part of the log entry) |
| `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` | row for `generate_water_parity_fixture.py` (HAND + TEST IMPORT; imports from the body-mechanics generator; a move must update `tests/env/test_water_parity.py`'s `sys.path`); the `make_render_fixture_recordings.py` row gets the 07 path + `POND_WORLD`; the body-mechanics generator row gains "also imported by `generate_water_parity_fixture.py`" | C0, C5 |
| `docs/environment/05_body_homeostasis.md`, `06_reward_and_termination.md`, `03_entity_placement.md`, `09_sensors_and_observation.md`, `10_perceptual_noise.md`, `01_state_and_params.md`, `ENVIRONMENT_SUMMARY.md`, `TRAJECTORY_STORE_SCHEMA.md` (codes 6/7), `WANDB_METRICS_REFERENCE.md` (two new keys) | describe what the code does | C2–C4 |
| `docs/develop/active/behavior/WANDB_METRICS_REFERENCE.md` | two new keys | C4 |
| `docs/experiments/active/basic_levels_q2_default/BASIC_LEVELS_Q2_DEFAULT.md` | dated note row (A10) | C5 |

### Commit sequence

| Commit | Content | Must be true before moving on |
|---|---|---|
| **C0** | generator script + SCRIPTS map row; **no env change**. Record the baseline test run (§T0) in the Implementation Report | the generator runs clean against a detached worktree of C0 |
| **C1** | the fixture from `--src-root=<worktree of C0>` + README pinning the C0 SHA | fixture file committed; the generator refused a dirty tree when tried |
| **C2** | schema + inert plumbing: `state.py`, loader (gate, validation, sentinels), `default.yaml` block + noise modality, compat era, every stand-alone/inline config gains `enabled: false`, frozen-world row, CONFIG_GUIDE / 02_schema / critical registry. **Water cannot yet be switched on** (the loader raises "not implemented" if `enabled: true`) | §T1 parity green on all worlds; every previously green module still green |
| **C3** | mechanics: placement, hydration, drive, death, labels, obs, smell, vision; tests T2–T4 | T1 still green; T2–T4 green; they **fail on C2** (checked by running them there) |
| **C4** | logging fan-out: shared reason constant, episode/balance metrics, train.py / dreamer sites, snapshot fields, CSV and viz branches, fingerprints, docs | T3's metric-key test green |
| **C5** | ladder: new 06, `git mv` 06 → 07 + edits, reference updates (A10), T5 | T5 green; T1's "07 with water off = pre-change 06" case green |
| **C6** | dashboard rendering (D8) | D8 gates |
| **C7** | speed measurement + Implementation Report | §S |

Each commit uses an explicit pathspec, one coherent change per commit.

---

## Tests and verification

**Test-suite rule**: never run `tests/env/` as one process (XLA core dumps; backend drift). Run **per module**:

```bash
cd /media/nas01/projects/Interoceptive-AI/grid_world_pain
for f in tests/env/test_*.py; do
  echo "== $f"; JAX_PLATFORMS=cpu /home/vncuser/miniconda3/envs/grid_world_pain/bin/python -m pytest -q "$f" 2>&1 | tail -3
done | tee tmp/$(date +%Y%m%d_%H%M%S)_thirst_suite.txt
```

The same loop covers `tests/environment/`, `tests/models/`, `tests/training/` and `tests/scripts/`. `tests/env/conftest.py` pins CPU for `tests/env/`; the other directories need `JAX_PLATFORMS=cpu` set explicitly as above.

### T0. Baseline (C0, before any env change)

Run the loop on C0 and record per-module pass/fail/skip counts in the Implementation Report. **Inherited known reds, recorded, not fixed, not blocking:**

- `tests/env/test_channel_names_match_configs.py`: 17 failures on the level-05 factor fragments (~#133). After C5 it also sweeps the new 06 and 07, and **those two must pass**.
- `tests/models/test_modulation_input_slice.py::test_hand_computed_breakdown_matches_the_live_environment`, `tests/training/test_continual_bm_transition.py::test_continual_bm_stage_transition_no_crash`, `tests/training/test_continual_resume_rebuild.py::test_continual_resume_rebuilds_stage_env` (~#134).
- `tests/env/test_inactive_animal_offgrid.py::test_allactive_config_no_offgrid_parking` (~#132).
- `tests/env/test_backward_compat_configs.py` is green while skipping every ladder world (~#124). Treat it as providing no evidence; T5 replaces it for this plan.

After each commit, the gate is **no module worse than its T0 line**, except the changes this plan names.

### T1. Byte-parity when water is off — `tests/env/test_water_parity.py` (new)

- Imports the generator (`sys.path` insert, as `test_body_mechanics_parity.py` does). A missing fixture or config **fails**, never skips (the lesson in wiki `20260909_1402_parity_gates_green_without_comparing`).
- For `default.yaml` and levels 00–05, replay the fixture's seeds and assert **byte-identical**: every pre-existing state leaf, `obs` clean and noisy, reward, done, `termination_reason`, every pre-existing `info` key, **and the three jaxpr SHAs**.
- Also assert that `state.hydration is None`, `state.water_pos is None` and that `info` has no `drank` / `drive_thirst` keys.
- **Case "old noise world"**: the new 07 loaded through `load_env_config` with `water.enabled` forced to `false` **in memory** must equal the fixture's pre-change `06-sensory_noise` rollouts byte for byte. This is the proof that the ladder rewire changed nothing except water. The display-only `olfactory_channel_names` differ, but they never reach `EnvParams` (grep: only `eval_recording.py` reads them), so the comparison is unaffected.
  - **What this case asserts: rollouts AND the three jaxpr SHAs.** At 07 the noise modality list gains `Hydration` (13 entries instead of 12) and `noise_modes[12]` becomes 1 instead of the pad 0. `noise_modality_order` is static and unused by `jax_step` / `jax_reset` / `update_body`; `noise_modes` is a traced input of unchanged shape. So both rollouts and SHAs are expected equal.
  - If the rollouts match but a SHA differs, record it in the Implementation Report as a **finding**, with the jaxpr diff. Do not re-baseline, and do not treat it as a parity break of the rollouts.
- **Contrast half** (this is what fails on pre-change code): the same world with `water.enabled: true` must change the rollout **and** the `jax_step` / `jax_reset` / `update_body` jaxprs.
- **Coverage assert, with the expected sets hard-coded in the test** (not derived from the fixture, which would be circular): levels 00–04 and `default.yaml` must contain termination codes `{1, 2, 4}`; level 05 and the pre-change noise world `{1, 2, 4, 5}`. Code 3 (over-eating) is added to a world's set only if the C1 count table shows it. The generator writes a per-world, per-code count table into the fixture README. **If a required code is absent at C1, extend seeds or steps before freezing the fixture.** Never shrink the expected set to fit the data.
- The existing gates `test_body_mechanics_parity.py`, `test_bush_fire_clearance.py`, `test_thermal_parity.py`, `test_thermal_reward_gate.py`, `test_metabolic_coupling.py`, `test_thermal_rate_scales.py`, `test_visual_parity.py`, `test_unified_parity.py`, `test_extero_noc_parity.py`, `test_two_sided_nutrition.py` and `test_directional_sensors.py` must stay green **with zero fixture edits**. They read fixtures captured before this plan, so they are independent evidence.

### T2. Placement — `tests/env/test_water_placement.py` (new)

Each case uses real `jax_reset` / `jax_step` outputs, never a re-derivation through the loader's own table.

- **Load-time refusals**, one test each, each asserting that the message names the key: candidate off the grid; candidate inside `edge_margin`; duplicate candidate; empty list; center block inside the margin; center or candidate covering a fixed `start_pos` with `random_start_pos: false`; random mode on a grid too small (`|T| = 0`); `placement.mode: per_type`; `food_min_fire_distance > 0` / `bush_min_fire_distance > 0` with water; capacity check failing (a 5×5 world packed with entities); `properties` length ≠ `vector_size`; missing `hydration` noise modality; `start_hydration` at 0 or at max.
- **Runtime, level 06, 2,000 resets** (seeds 0–1999):
  - `water_pos` equals one candidate's block every time;
  - candidate frequencies pass a chi-square uniformity test at p > 0.001 (the draw is uniform);
  - **no active resource, animal or obstacle occupies a pond cell**;
  - every active entity lies inside its own spawn area. **This assertion, not the load-time capacity check, is the guard against the (0,0) fallback (~#117) for campfires**: the capacity check ignores `min_fire_separation: 4`, and three separated fires in a 36-cell area, one corner of which a pond can take, is exactly where the fallback could fire;
  - the agent is never on a pond cell at reset.
- **Random mode, 2,000 resets**: every top-left lies inside the margin, and the empirical support equals the analytically enumerated set.
- **Center mode**: `water_pos` is identical across seeds.
- **Respawn**: a level-06 world with `max_consumption: 1` for food (in memory), 5,000 random-action steps. No active resource ever sits on a pond cell.
- **Predators may enter**: a scripted scenario puts a hunting predator next to the pond with the agent across it, and the predator's path includes a pond cell within N steps (decision 9 holds, and the pond is not accidentally an obstacle).

### T3. Hydration dynamics and death — `tests/env/test_hydration_dynamics.py` (new)

**Oracle.** A numpy float32 recurrence written in the test, `W = np.clip(np.float32(W) - np.float32(d) + np.float32(g) * on, 0, max)`. It is independent of `core.py`.

- **Controlled world**: `default.yaml` + water on, with in-memory overrides `with_nutrition: false`, no animals and no resources. Nutrition must be off because food's 100-step clock would kill first. Pond at a known candidate.
  - Agent parked far from the pond, rest action every step, start 100: `done` first true at **step 160**, `termination_reason == 6` on that step and **on no earlier step**. It matches the oracle exactly.
  - Agent on a pond cell, rest action every step, start 100: `done` first at **step 20**, reason 7, matching the oracle.
  - Refill from 50 → 100 in 10 on-pond steps (oracle).
- **`start_hydration` is live** (~#94): `start_hydration: 37` → `jax_reset(...).hydration == 37.0`. Random start: 500 resets lie inside `[low, high]` and are not all equal.
- **One predicate** (~#160 / ~#192): 200 random-policy episodes on level 06. For every step, `reason in {6, 7}` ⇒ `done`, and `done` with `W' <= 0` ⇒ `reason == 6` unless a later code wins (7 only). The count of label-without-death must be **0**.
- **Water-off worlds never stamp 6/7** (~#494): 50 episodes each on levels 00–05, where every observed reason must be in `{0, …, 5}`.
- **Real death reaches the trainers**: a unit check that the rPPO trainer's real-death mask (`termination_reason >= 2`) is 1 for codes 6 and 7. Drive a real step that dies of dehydration through the trainer's mask expression.
- **Drive / reward**: on level 06, `reward` equals `prev_drive − curr_drive (− death_penalty on death)` where the drives are computed in the test by numpy from `(S, I, T, W)` with the A1 scales. At the setpoint (`S = 100, I = 0, T = 0, W = 100`) the drive is 0. A pure water deviation of 100 gives a drive of 100.
- **Metric keys**: `episode_finalise_episode(reason=6)` sets `Episode/Term_Dehydration = 1`; `episode_wandb_keys()` has 23 keys; `train.py` and `dreamer_srl_main.py` have no literal `(5, 'Thermal')` left (grep assert).

### T4. Observation, noise and smell — `tests/env/test_water_observation.py` (new)

- Level 06 breakdown order equals `[Satiation, Body Temperature, Hydration, Interoceptive Nociception, Extero Nociception, Thermoception, Olfaction, Collision, Proprioception, Visual]`, total 59. `get_observation` does not raise.
- The Hydration column equals `state.hydration / 200` on real steps (clean obs).
- **Noise uses the hydration slot**: level 06 with noise enabled in memory and a hydration override of `mode: constant, sigma: 0.5, clip_min: -10.0, clip_max: 10.0`, over 2,000 steps. The wide clip is required: the default `[0, 1]` clip around a value near 0.5 would clip about a third of the draws and give a std of about 0.39. The sample std of `obs_noisy − obs_clean` on the Hydration column must be within 10 % of 0.5, and on another column (Satiation) must match that modality's own sigma, which shows the lookup went to the hydration slot and not a neighbour.
- **Level 07 is clean on hydration** (~#371): resolved `noise_sigmas[order.index("Hydration")] == 0.0`, from the loaded params, not the YAML. This asserts **hydration only**. It does not mean "all interoception is clean": today's noise level never sets `body_temperature`'s sigma, which is inherited from `default.yaml`. That hole predates this plan and is out of scope (listed in Open items).
- `build_sensory_viz` and `evaluation_core._sensor_stat_columns` accept a level-06 observation, and the slices after Hydration are unshifted: the column counts match the breakdown.
- **Smell equations (A3)**, computed by numpy in the test. Every assertion pins the **centre sampling cell of the olfaction diamond, channel 0**: flattened olfaction index 0, which is Olfaction offset 0 (the agent's own cell) × channel 0. The other four cells of the diamond read other values (e.g. 0.489 × 0.5 at the pond's diagonal neighbour) and are not pinned.
  - the agent on a pond corner: water's contribution equals `0.5 × (2 + 1 + 1 + 1/√2)/4`;
  - the agent beside the pond equals `0.5 × (1 + 1/2 + 1/√2 + 1/√5)/4`;
  - at centroid distance ≥ 8 the pond's contribution is within 3 % of the **analytic single-source value** `0.5 · f(d̄)`, with `d̄` measured to the pond's **fractional** centroid (e.g. `(1.5, 1.5)` for the candidate at array `(1, 1)`). math-reviewer measured ≤ 0.18 %;
  - **not-4×-louder**: the same comparison against a single source of `p` placed at the fractional centroid through `sense_resource` itself (it accepts float positions). It must not be compared with a 1×1 pond on a grid cell, which cannot sit at a half-cell centroid and differs by 6.8–8.5 % on correct code (math-reviewer M1).
- **Vision**: pond cells raise the "Visible" channel where the pond is in the diamond. With water off the visual output is unchanged (covered by T1).

### T5. Ladder loads through the trainer's path — `tests/env/test_ladder_worlds_load.py` (new)

For each of the eight files `basic/00` … `basic/07`: `load_env_config` → `load_env_params` → `jax_reset` → 5 `jax_step`s.

- Assert `sum(breakdown) == [44, 44, 52, 52, 52, 58, 59, 59][i]`.
- Assert `water_enabled == [F, F, F, F, F, F, T, T][i]` and `perceptual_noise_enabled` true only for 07.
- Assert that the files in `configs/environment/experiment/basic/` whose names match `^0[0-9]-` are exactly those eight, so an unplanned new rung or a missed rename fails. The folder also holds two non-rung worlds, `forage_5x5.yaml` and `slow_predator_bush_5x5.yaml`, which the assertion ignores.
- It **fails on C0** (no 06-pond, no 07).

### T6. Agents build against the new width

- rPPO: build the network with level 06's breakdown and run one forward pass. Then a CPU smoke run: `train.py` on level 06 with the smallest budget the CLI allows, which must reach its first log line.
- dreamer_srl: a smoke run on level 06, passing `--episodes` / `--log-interval` on the CLI (the single-config budget gotcha in the auto-memory). The `obs_dim == breakdown` assertion must pass.
- A curriculum pre-flight with stage 0 = level 05 and stage 1 = level 06 **must refuse** (fingerprint and width), and 06 → 07 must pass the fingerprint check.

### S. Speed (C7)

Same node, same seed, CPU and one GPU. Measure 64 envs × 300 jitted vmapped `jax_step` calls, 3 reps, before (C0 worktree) and after:

- **level 05 must be within run-to-run spread** (its graph is unchanged);
- level 06 against level 05 at the after tip: the expected cost is small (one extra 4-source smell pool at 5 cells, 4 extra visual entities, one equality test, and the respawn repair). Anything over 5 % is discussed in the report. Over 15 % blocks **until the named fallback in §D4.6 (one shared permutation per step) has been tried and re-measured**. If it still exceeds 15 % after the fallback, stop and report to the user.

### Reviews to run on the implementation

`code-reviewer` (PRNG discipline, static gates, None leaves, vmap over None), `math-reviewer` (A3 smell rows, the drive axis, the clock arithmetic), `env-config-reviewer` (levels 06/07, noise ↔ breakdown sync, mandatory keys, the critical-settings entry). Then `senior-developer` verification against this plan.

---

## Checkpoints

- [x] **C0** Baseline suite recorded per module; generator committed; the SCRIPTS map row added. — `359d192a`; T0 in the Implementation Report.
- [x] **C1** Fixture generated from a detached worktree of the C0 SHA; README names the SHA and command; the generator refused a dirty tree when tried. — `b9c4b569`; refusal exit 1 listing the dirty files.
- [x] **C2** `water.enabled` missing → `ValueError` naming the key (test). T1 green for all worlds including the jaxpr SHAs. `scripts/verification/verify_noise.py` still runs. Every T0-green module still green. Registry and change-log entry present in the same commit. — `21200553`; T1 41 passed; every module at its T0 line. `verify_noise.py` does NOT run, but fails identically on the pre-change commit (11 older EnvState fields missing; decision 5).
- [x] **C3** T2, T3 and T4 green, and each **fails when run on C2** (record the failing count). T1 still green. — `7d2443d4`; on C2: placement 7 failed + 3 errors, hydration 10 failed, observation 8 failed; T1 43/43.
- [x] **C4** No literal termination-name list left in `train.py` / `dreamer_srl_main.py` (grep). A level-06 eval rollout's `termination_reason` column contains codes from `{1,…,7}` only. — `2af12e4d`; the grep is asserted in a test. The codes check ran on 200 real random-policy level-06 episodes (T3), not through `eval_rollout.py`, which needs a trained level-06 checkpoint (none exists).
- [x] **C5** `git log --follow` on `07-sensory_noise_10x10.yaml` shows the old history. T5 green. The "07 with water off = pre-change 06" parity case green. `test_channel_names_match_configs.py` passes on 06 and 07. — `9db9b3ac`; `--follow` reaches `b093023e`; rollouts AND jaxpr SHAs equal.
- [x] **C6** Dashboard gates (D8.8) pass on a real level-06 recording. The old renderer renders the same recording without raising. — `87ad70be`; 0 new audit findings, 0 cell findings; both renderers render all 81 frames.
- [x] **C7** Speed table filled; the three reviewers' verdicts linked. — speed table in the Implementation Report (level 06 vs 05: −12.6 % GPU, −7.4 % CPU, after the respawn-repair rewrite of decision 13). Reviews NOT yet run: `code-reviewer`, `math-reviewer`, `env-config-reviewer` are the next step (the parent spawns them).

---

## Calls made in this plan that the user should know about

1. **Frontmatter status and topic.** `status: active` with a DRAFT banner, and `topic: env_entities`, because `draft` and `thirst` fail the develop-index validator and registering them means editing a script.
2. **Numbers chosen by the calibration**: drain **0.625**, gain **5.625** (160-step dehydration, 20-step over-drinking, net +5 refill). They are exact in float32 so the death step is an integer a test can pin. Targets W5 and W6 (refill and over-drink windows) are this plan's proposal, not a user statement.
3. **⚠ Level 06 randomises the start hydration over `[0, 200)`**, mirroring the nutrition draw. **Consequence for the survival metric: about 5 % of episodes are dead of thirst by step 16, and about 16 % by step 50, whatever the agent does**, and half of all episodes start within 50 units of a lethal end. Alternatives: a fixed start at 100, or a narrower range such as `[50, 150]`. Please decide.
4. **Channel labels at level 06**: channel 4 becomes `Odour C (water-leaning)`, and channel 0 stays `Food` with qualifier `shared with water`. The rename is **not** made in `default.yaml`, where channel 4 is still tree-only. The old renderer's hard-coded `TREE` token is left alone.
5. **No over-drinking on/off flag.** Over-drinking death is always on when water is on. Nutrition has `overeating_death`; adding the mirror key is one line if wanted.
6. **No "hydration hidden" flag.** Hydration is always observed when water is on. The dashboard still gets a hidden twin row, so adding the flag later needs no renderer change.
7. **Refused combinations** (instead of new placement proofs): water with the `per_type` placement mode, and water with either fire-distance placement pass.
8. **`edge_margin` applies to all three modes.** A list candidate inside the margin is refused rather than silently allowed.
9. **Termination code precedence**: codes 6/7 are stamped after thermal's 5. If an agent dies of cold and thirst on the same step it is labelled a water death; `done` is the same either way.
10. **A shared termination-names constant** replaces five duplicated literal lists. That is a small refactor beyond "add two codes", taken because adding the codes to five copies is how the lists drift.
11. **Hydration noise modality appended last** in the noise list (not next to satiation), so no existing noise index moves. It takes the 13th and last padded slot.
12. **`water.candidates` are 1-based in YAML** (loader subtracts 1), because every other coordinate in these configs (`start_pos`, spawn `area`) is 1-based. A 0-based list would be the one exception and would be misread.

## Open items (not in this plan)

- Recordings store no termination reason. A dying frame shows the hydration value, but the cause is not stored. Add one only if a qualitative read needs it.
- The trajectory store and `traj_scan` record no body temperature today and would record no hydration. That is a separate plan if analyses need it.
- A thirst ↔ body-temperature coupling switch (EVAAA couples them), off by default, as a later plan.
- Whether the neuromodulator's interoceptive input should include Hydration. Inputs are named per config, so nothing changes silently.
- The `lvl06` label collision in historical analysis scripts (A10).
- Level 07's noise block does not state a sigma for `body_temperature` (inherited from `default.yaml`), so "interoception clean" is not fully true there. This predates the plan (plan-reviewer assumption 6).
- `lad03_how_it_ends.py` and `part4_readout.py` will not show codes 6/7 (A6). Ask `bug-curator` to extend row ~#116.
- Back-links: this doc links to the thermal, renderer and compat plans, but they do not link back yet. Adding those back-links edits other owners' docs, so it is left to them.

---

## Revision 1 — response to review (2026-09-29)

Both reviews are appended below, unedited. The math review found the equations correct and asked for four fixes. The plan review was **SOUND WITH CONCERNS**: nothing blocking, and six Moderate items that would each have halted an unattended run or weakened a gate. Every finding is addressed in the body; none is rejected.

| Finding | What changed | Where |
|---|---|---|
| plan-reviewer M1 (unpack) | The ten-name unpack at `core.py:~1099` is extended to eleven; the test callers are named as unaffected | §D4.6 |
| plan-reviewer M2 (nine files in `basic/`) | T5 asserts only the `^0[0-9]-` files equal the eight rungs | §T5 |
| plan-reviewer M3 (clipped σ) | Noise test widens the clip to ±10 and checks a neighbour column's own sigma | §T4 |
| plan-reviewer M4 (circular coverage) | Expected death-code sets hard-coded per world; extend seeds or steps at C1 if a code is absent | §T1 |
| plan-reviewer M5 (no speed fallback) | Fallback named: one shared permutation per step, the k-th repair takes the k-th valid cell; the 15 % gate blocks only after it has been tried | §D4.6, §S |
| plan-reviewer M6 (analysis consumers) | `lad03_how_it_ends.py` and `part4_readout.py:440` added as out-of-scope rows; `bug-curator` to extend ~#116 | §A6, Open items |
| plan-reviewer L1 | Two more stale labels added to the naming note | §A10 |
| plan-reviewer L2 | Index regenerated; see the commit note for what was committed | — |
| plan-reviewer L3 | `episode_metrics._TERM_*` derived from the shared constant | §D6 |
| plan-reviewer assumption 3 | The "07 with water off" case asserts rollouts **and** jaxpr SHAs; a SHA-only mismatch is reported as a finding, not a parity break | §T1 |
| plan-reviewer assumption 4 | T2's 2,000-reset in-area assertion is named as the (0,0) guard for campfires | §T2 |
| plan-reviewer assumption 5 | Early thirst deaths (~5 % by step 16) are quantified and surfaced as user call #3 | clock section, Calls |
| plan-reviewer assumption 6 | "Clean on hydration" is stated to mean hydration only; the `body_temperature` hole is an open item | §T4, Open items |
| math-reviewer M1 | Far-field test compares against a source at the fractional centroid, or the analytic value; never a 1×1 pond on a cell | §T4 |
| math-reviewer M2 | Trips column corrected: water needs at least one visit (two if cautious); food ~20 items per 100-step refill, ~80 per episode | clock table |
| math-reviewer M3 | "A quarter within 50" corrected to half (a quarter within 25) | clock section |
| math-reviewer M4 | Cold clock cited as 86–99 at shipped values (2026-09-19 change log) | clock table |
| math-reviewer M5 | T4 pins olfaction index 0 (centre cell, channel 0) | §T4 |
| math-reviewer M6 | D1 notes that the random start can draw exactly 0.0 | §D1 |

---

## Implementation Report

> **Implemented by**: developer
> **Date**: 2026-09-30
> **Where**: branch `v5.0`, worktree `.claude/worktrees/thirst`. Nothing pushed, nothing merged into `v4.0` / `develop` / `main`.

### In plain words

Water and thirst are in the environment. Every world that leaves `water.enabled` off (all
of them except levels 06 and 07) behaves exactly as before: the same random numbers,
observations, rewards, endings and traced graphs, compared byte for byte with rollouts
recorded from the commit before any change. With water on, each episode has one 2×2 pond
at one of four spots, the agent has a hydration level that falls 0.625 per step and rises
+5 net per step on the pond, and it dies at either end (code 6 dehydration after exactly
160 steps away from water, code 7 over-drinking after exactly 20 steps in the pond from the
comfortable level). The ladder has eight rungs: the new 06 is the campfire world plus the
pond, and the noise rung moved to 07 on top of it. The renderer work done earlier by the
rendering session now runs on real level-06 recordings.

### Commits

| Checkpoint | Commit | Content |
|---|---|---|
| C0 | `359d192a` | water parity fixture generator + scripts-map rows |
| C1 | `b9c4b569` | fixture from a detached worktree of `359d192a` (its `src/` and `configs/` equal `711bdc22`) + README with the code-count table |
| C2 | `21200553` | schema + inert plumbing, gate off everywhere; docs (CONFIG_GUIDE §3.10, 02 schema, critical settings) |
| C3 | `7d2443d4` | mechanics: placement, drinking, drive, deaths 6/7, senses; T2–T4; environment docs |
| C4 | `2af12e4d` | shared termination-reason constant, metrics, fingerprints, schema doc |
| C5 | `9db9b3ac` | ladder: new 06, `git mv` 06 → 07, references, T5 |
| C6 | `87ad70be` | dashboard gates on a real level-06 recording; renderer contract fixes |
| C7 | (this commit) | respawn-repair rewrite after the speed check (decision 13), repair test, speed table, this report |

### What changed, per checkpoint

- **C0/C1.** `scripts/fixtures/generate_water_parity_fixture.py` imports the body-mechanics
  generator's rollout loop, action rule and jaxpr hashing (one copy). Worlds: `default.yaml`,
  basic 00–05 and the noise rung under its old name. Fixture: 13 MB (decision 1 explains the
  extra `__trunc` variants). The generator refused a tree with uncommitted `src/`/`configs/`
  changes (exit 1, listing them).
- **C2.** `EnvState.hydration` / `water_pos` default `None`; 14 static `EnvParams` fields;
  `config_loader._load_water` (all D1 validation, the three placement modes resolved to a
  0-based top-left table, refusals, capacity check); `hydration` noise modality appended
  last (13th and last padded slot); `saved_config_compat` era supplying `water.enabled:
  false`; `water: {enabled: false}` in every stand-alone config and inline test base
  (continual, verification, frozen parity world + README row, test fixtures). C2 refused
  `enabled: true` ("not implemented yet").
- **C3.** `core.py`: pond draw (`0xD81`), overlap scan pre-occupied by the pond, agent start
  repair (`0xD82`), start hydration (`0xD84`), respawn repair (`0xD83`), `info['drank']`,
  11-element `update_body`, reasons 6/7 after thermal from the returned predicates, fourth
  drive axis in a static branch before the thermal one, `info['drive_thirst']`.
  `sensor.py`: Hydration observation, fourth smell pool, pond visual entities.
  `evaluation_core`: `intero_hydration` CSV column. `state.py`: `EnvParams.__setstate__`
  (decision 8).
- **C4.** `TERMINATION_REASONS` in `episode_metrics.py` (23 WandB keys), imported by
  `train.py` (4 sites), the dreamer trainer and `balance_metrics` (whose death mask now
  counts every listed code); `water_enabled` in both curriculum fingerprints; trajectory
  store column text + regenerated `TRAJECTORY_STORE_SCHEMA.md`; `check_env.py` legend;
  the dreamer trainer's hard-coded `sys.path` (decision 10).
- **C5.** New `06-pond_thirst_10x10.yaml`; `git mv` to `07-sensory_noise_10x10.yaml`,
  re-parented, hydration sigma 0.0 stated; the two live `train_command-agent.sh` lines
  (with dated notes), `generate_thermal_probes.py`, `make_render_fixture_recordings.py`
  (`NOISE_WORLD`, `POND_WORLD`), the dashboard-layout and silent-failures tests; T5; dated
  entries in CONFIG_CRITICAL_SETTINGS (incl. the `lvl06` naming hazard) and
  BASIC_LEVELS_Q2_DEFAULT; scripts-map row.
- **C6.** Cell `W1` (level 06) recorded; §D8.8 audit; `renderer.py` docstring; two
  contract fixes (decisions 8, 9).

### Tests

**T0 baseline** (C0 tree, one process per module; `tmp/20260930_T0_baseline`,
`tmp/20260930_T0_extra`). 86 modules in the plan's five directories, 52 more in
`tests/{algorithms,analysis,behavior,utils}` and `tests/*.py`. Pre-existing reds, none
touched by this change:

| Module | T0 |
|---|---|
| `tests/env/test_channel_names_match_configs.py` | 25 failed — `test_every_maintained_config_can_write_a_recording` over `configs/continual/continual_worlds/*` and `level05_body_interactions/factors/*` (missing `sensory.visual_value_mode`) |
| `tests/models/test_modulation_input_slice.py` | 5 failed (incl. ~#134) |
| `tests/models/test_modulation_sites.py` | 4 failed (golden files) |
| `tests/training/test_continual_bm_transition.py`, `test_continual_resume_rebuild.py` | 1 failed each (~#134) |
| `tests/environment/test_behavior_measures.py` | 1 failed (`visual_properties` required at V=1) |
| `tests/scripts/test_evaluation_model_rebuild.py` | 4 failed (same cause) |
| `tests/scripts/test_context_dependence_b0.py` | 1 failed (NaN rest rate) |
| `tests/scripts/test_dreamer_srl_offline_wm_test.py` | 1 error (same `visual_properties` cause) |
| `tests/algorithms/dreamer_srl/*` | checkpoint 7 errors, eval_recording 4 errors, eval_rollout 3 errors, eval_rollout_batched 5 errors, eval_telemetry 1 error, eval_telemetry_wandb 2 failed, eval_video_smoke 2 failed, render_upload 1 failed, continual_resume_rebuild 1 failed |
| `tests/test_trajectory_collection.py` | 3 failed |

`test_inactive_animal_offgrid.py` (plan ~#132) was **green** at T0 (3 passed).
`test_backward_compat_configs.py` skips every ladder world, as ~#124 says (T5 replaces it).

**New tests** (final tree): T1 `test_water_parity.py` 43 · T2 `test_water_placement.py` 38 ·
T3 `test_hydration_dynamics.py` 17 · T4 `test_water_observation.py` 9 · T5
`test_ladder_worlds_load.py` 9 — all passing. On C2 (before the mechanics): placement 7
failed + 3 errors, hydration 10 failed, observation 8 failed, ladder 3 failed. Diagnostics:
candidate χ² 4.29 over 2,000 resets; 128–130 respawns in 5,000 steps; the repair test
(decision 13) χ² 0.1 / 9.9 and it fails with the repair disabled; a hunting predator's path
(1,0)→(1,1)→(1,2)→(1,3) crosses the pond; noise std 0.500 on Hydration (σ 0.5) and 0.049 on
Satiation (σ 0.05); 14 dehydration deaths and 0 over-drinking deaths in 200 random-policy
episodes (over-drinking is exercised by the controlled test, death at step 20).

**Per-checkpoint suites.** C2: all 86 modules at their T0 line (dashboard_water and
saved_config_compat +1 new test each). C3: all 138 modules at T0 except
`tests/test_provenance.py` (decision 12, intermittent). C4/C5/C6: every module that imports the touched
code at T0 or better. **Final (C7) full run, 143 modules (`tmp/20260930_final`): no module
worse than T0.** 130 identical to T0 (every pre-existing red unchanged); 8 better
(channel-names +1 pass for 06/07; dashboard layout +3; maintained-worlds bush +1;
saved-config compat +1; and `test_dashboard_frames` 13, `test_dashboard_water` 15,
`test_render_audit_controls` 68 and `test_render_recordings_v2` 8 now run instead of
skipping, because this worktree has the `M4`/`W1` recordings); 5 new modules green;
`test_provenance` 12/12 on this run.

**T6.** `train.py` (rPPO) on level 06 builds and trains: "Observation Dim: 59 (… Body
Temperature=1, Hydration=1 …)", 74 iterations, exit 0. dreamer_srl on level 06:
`obs_dim=59`, the `obs_dim == breakdown` assertion passed, exit 0 (too short for gradient
steps). Curriculum pre-flight: 05 → 06 refused ("changes obs_dim (58 -> 59)"; the width
check fires before the fingerprint), 06 → 07 accepted.

**C6 gates.** Real level-06 recording (cell `W1`, 2 episodes, 13 + 68 steps; snapshots
carry `water_pos` and `hydration`). Dashboard frames at steps 0 and 67 audited against the
same frames with water removed: 0 new findings, 0 `cell_*` findings, hydration row inside
the vitals card. Both `render_recordings_v2.py` and the frozen `render_recordings.py` render
every frame. `test_dashboard_layout.py` covers 06/07 (126 passed). With the `M4` fixture
copied into this worktree's gitignored `results/`, `test_dashboard_water.py` 15/15 and
`test_dashboard_frames.py` 13/13 (both partly skipped at T0 for lack of it).

### Speed (§S)

`tmp/20260930_speed_check.py`: 64 envs × 300 `jax_step` calls, vmapped, inside one jitted
`lax.scan` per rep, 5 reps, seed 0, median env-steps/s; RTX 4090 (GPU 0) and the shared
CPU; before (`/tmp` worktree of `359d192a`) and after interleaved.

| World | Backend | Before | After | Change |
|---|---|---|---|---|
| level 05 | GPU | 928–933k | 924–934k | −0.3 % (within spread; its graph is byte-identical) |
| level 05 | CPU | 28.6–29.5k | 29.0–29.2k | 0 % (within spread) |
| level 06 vs level 05 (after) | GPU | — | 814k vs 932k | **−12.6 %** |
| level 06 vs level 05 (after) | CPU | — | 26.9k vs 29.0k | **−7.4 %** |

Both are under the 15 % block and over the 5 % discussion line. How the level-06 cost was
found and cut is decision 13. With the respawn repair removed entirely, level 06 costs
−2.8 % (GPU) and 0 % (CPU), so the remaining cost is the repair.

### Decisions made during implementation (numbered)

1. **Termination-code coverage needed a short-clock variant.** Every shipped world has
   `max_steps: 500` and the shared random policy never lives that long (0 step-limit endings
   in 16 seeds × 2,000 steps), so the plan's 16 × 300 budget can never contain code 1. Each
   world also gets `<world>__trunc` with `environment.max_steps: 30` in memory (8 seeds ×
   150 steps), recorded and replayed identically. Coverage is the union; the expected sets
   are hard-coded as planned. Code 3 never occurs, so it is in no set.
2. **Fixture source**: the C0 commit `359d192a` (`src/` and `configs/` identical to
   `711bdc22`, verified by diff).
3. **Archived configs were not migrated.** Live tests that read archived raw configs
   (unified parity, visual parity, the thermal suites, extero-noc parity, distributional and
   per-episode logging, per-entity info, body-temperature observation, thermal reward gate)
   supply `water: {enabled: false}` in memory at their load point, with a comment. The
   body-mechanics change had edited those archive files instead; project policy now forbids
   that.
4. **Drift checks** in the body-mechanics and bush-clearance parity tests ignore the new
   `water` block and `hydration` noise entry (test edit; no fixture edited).
5. **`scripts/verification/verify_noise.py` does not run** — it fails identically on the
   pre-change commit (11 older `EnvState` fields missing). Not fixed (out of scope).
6. **T1's contrast half** ("water on changes rollout and all three jaxprs") landed at C3:
   at C2 the loader refused water on by design.
7. **The stats-CSV Hydration column** landed at C3 (T4 needs it), not C4.
8. **`EnvParams.__setstate__`** (C3). Recordings pickle `EnvParams` into `run_meta.pkl`;
   `get_observation_breakdown` now reads `water_enabled`, so every pre-water recording
   raised `AttributeError` when rendered (measured on a params pickle from `359d192a`). The
   water-off sentinels are filled on unpickle (one table, `state.WATER_OFF_FIELDS`, also used
   by the loader). Confirmed by `test_dashboard_frames.py` 13/13 on old recordings.
9. **Dashboard contract fixes** (C6, `dashboard/episode.py`, one guard): the "no default
   maximum" check also refuses `water_max_hydration <= 0`, because the field now always
   exists (0.0 when off) and the old `hasattr` test could no longer fire. The rendering
   session's tests: "params cannot say" became "a pre-water params pickle renders as
   water-off"; the hidden-twin case drops Hydration from the breakdown by hand; the
   integration helper sets `water_enabled=True` when it injects a pond. No field or key the
   dashboard reads was renamed.
10. **`dreamer_srl_main.py` hard-coded `sys.path.insert(0, '<shared folder>')`** replaced by
    the repo root derived from the file (same path in the shared folder). In any git
    worktree the literal made the trainer import the shared folder's `src`.
11. **Editable install**: the conda env maps `src` to the shared folder, and modules under
    `tests/algorithms/` (no `__init__.py` above them) resolved part of `src` there, in T0 as
    well. Those modules were re-run with baseline and final both on their own trees; all 27
    match.
12. **`tests/test_provenance.py`** fails on a dirty worktree here: `git status` takes ~28 s on
    this NAS and the provenance helper times out at 10 s, returning "unknown". Its killed
    `git status` left 0-byte `index.lock` files three times; each was removed only when empty
    and more than 10 minutes old (CLAUDE.md rule). Environmental and intermittent: it
    passed 12/12 in the final full run.
13. **Respawn repair rewritten after the speed check.** The plan's per-slot permutations
    cost −21 % (GPU); its named fallback, one shared permutation, cost −22 % (the sort is the
    cost, not the batching); a Gumbel-max draw −14 % GPU but −59 % CPU; a cumsum draw −16 % /
    −15 %. Shipped: draw `u` uniformly over the allowed ranks and skip the pond's ranks with
    the fixed point `v = u + #{pond ranks ≤ v}` — exactly uniform over area minus pond, touches
    only the h·w pond cells, per-slot areas allowed (no new load restriction), −12.6 % GPU /
    −7.4 % CPU. New test `test_respawn_repair_is_uniform_over_area_minus_pond` (fails with the
    repair disabled). This is a deviation from the named fallback's form, for the reason
    measured above; the water-off graph is untouched either way.
14. **Test-side corrections**: Hydration column compared at 1e-6 relative (XLA folds `/200`
    into a reciprocal multiply); `drive_thirst` normalised by `range_W` = 100 as the plan says;
    the per_type refusal tested on a thermal-off world (the campfire world refuses per_type
    earlier on its own); the visual contrast pins the diamond cells that are pond cells.
15. **Speed harness** times a jitted `lax.scan` of the 300 steps rather than 300 Python
    calls: per-call timing on this shared machine ranged 21k–54k between reps.
16. **Render fixture `W1` is not loosened**: the demonstration loosening is refused by the
    thermal structure check since the 2026-09-19 retune (`M4` fails the same way;
    pre-existing).

### For the rendering session

- Field and key names are exactly as the dashboard reads them: snapshot `water_pos`
  `[h·w, 2]` and `hydration`; `params.water_enabled`, `params.water_max_hydration`;
  observation block "Hydration" directly after "Body Temperature".
- Two small edits to your code: the `water_max_hydration <= 0` guard in
  `dashboard/episode.py`, and three test adjustments in `test_dashboard_water.py`
  (decision 9). `EnvParams.__setstate__` keeps pre-water recordings rendering.
- `make_render_fixture_recordings.py` has cell `W1` (level 06, unloosened). The
  demonstration loosening no longer loads (decision 16); M3/M4/M4b/M6b are affected.
- The old renderer's docstring now states it draws neither pond nor hydration.

### Follow-ups (not done here)

- Reviews: `code-reviewer`, `math-reviewer`, `env-config-reviewer`, then `senior-developer`
  verification.
- `bug-curator`: extend row ~#116 (codes 6/7 dropped by `lad03_how_it_ends.py` /
  `part4_readout.py`); consider rows for the editable-install mixing (decision 11), the
  provenance timeout leaving index locks (decision 12), `verify_noise.py` (decision 5), the
  loosening refused by the structure check (decision 16), and pre-thermal recordings, whose
  pickled params lack `thermal_*` fields (the same class as decision 8, older).
- `dreamer_srl_main.py:~516` and `eval.py:~551` still hard-code the shared-folder
  `_project_root` (not touched).
- `experiment-designer`: re-running `generate_thermal_probes.py` now copies a `hydration`
  noise entry into the probes (harmless; water is off there).

## Verification Report

> **Verified by**: —
> **Date**: —

| File | Change | Status | Notes |
|------|--------|:------:|-------|
| | | | |

**Conclusion**: —

---

## Feedback from `math-reviewer` (2026-09-29, reviewed at commit `c7cb7e54`)

### Verdict, in plain language

The arithmetic this plan rests on holds, checked against the code in `src/environment/` rather than the plan's description of it. Standing away from the pond, hydration falls from the comfortable level (100 of 200) to zero in **exactly 160 steps**; standing on the pond it climbs to the fatal ceiling in **exactly 20 steps**; a half-empty agent refills in 10 steps and a quarter-full one in 15. All four numbers were reproduced with a single-precision (float32) recurrence and every intermediate value is exact, so a test can pin the death step as a whole number with no tolerance. The order of operations the plan proposes (drain, then drink, then one clip, then the death test on the clipped value) is the order the nutrition axis actually uses today, so "drink and drain in the same step" nets out to +5 as claimed, and there is no off-by-one against the food clock (100 steps, reproduced the same way). The smell weighting of one quarter per pond cell does what it is meant to: from any cell the agent can stand on off the pond, a 2×2 pond smells within 5 % of a single item sitting at the pond's middle, and within 3 % from about three cells away or more; the food-channel reading is always quieter than one food at the nearest pond cell (33–46 % of it). The fourth drive axis is an exact mirror of the hunger axis at the shipped numbers and stays a correct mirror if the hydration range is ever changed. **Nothing here blocks implementation.**

Four things need correcting before the tests are written or the numbers are quoted elsewhere: one smell test in §T4 will fail as written (it compares a 2×2 pond with a 1×1 pond, but a 1×1 pond cannot sit where the 2×2's middle is); the "trips per episode" column of the clock table is wrong for both food and water (one well-timed pond visit covers a whole 500-step episode); the random-start sentence miscounts (half, not a quarter, of episodes start within 50 units of an end); and the cold-clock range cited is from before the thermal retune.

**Severity legend:** 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run · 🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

### Findings

| # | Severity | Where | Issue | Correction |
|---|---|---|---|---|
| M1 | 🟡 Moderate | §T4, fourth smell bullet ("a 2×2 pond's far-field total equals, within that tolerance, a 1×1 pond's with the same `p`") | The tolerance inherited from the previous bullet is 3 %. A 1×1 pond occupies a grid cell; a 2×2 pond's centroid is at a half-cell. With the 1×1 placed on the 2×2's top-left cell (the only natural "same place"), the two readings differ by **6.8–8.5 %** at every cell whose centroid distance is ≥ 8 on the 10×10 grid (γ = 1), so the test as specified **fails on correct code**. | Put the 1×1 comparison source at the 2×2's centroid (fractional coordinates; `sense_resource` takes float positions and the kernel is `1/d`), or compare against the analytic `f(d̄)` as the third bullet already does, or widen this bullet's tolerance to ≥ 10 %. |
| M2 | 🟡 Moderate | Clock table, "Share of 500-step cap" column, and the sentence "a 500-step episode needs at least three pond visits" | Wrong for both rows. **Water:** one visit suffices — walk 153 steps (W = 4.375), drink 39 steps (W = 199.375, still under the ceiling), walk 318 more: 510 steps > cap. The minimum is **one** pond visit; a cautious agent needs two. **Food:** one item nets `food_nutrition_gain − eating_nutrition_cost = 6 − 1 = +5` nutrition (`default.yaml:176-177`, not overridden on the ladder), so refilling the 100-step clock is 20 items and a 500-step episode needs **80 items**, not "5 trips". The clocks themselves (100 / 160 / 20) are right; only the trip column is wrong. | Replace with: "at least one pond visit per episode is unavoidable; a refill from near-empty to near-full is ~39 on-pond steps" and state the food figure in items (80) or drop it. The design conclusion ("the pond cannot be ignored") survives. |
| M3 | 🟢 Low | "Random start hydration" paragraph | "About a quarter of episodes then start within 50 units of an end." For `U[0, 200]`: `P(W < 50) + P(W > 150) = 0.5`. A quarter is the share within **25** units of an end. | Change the number to half, or the width to 25. |
| M4 | 🟢 Low | Clock table, Cold row | "74–127 across the per-episode world baseline range (§D14)" is the **pre-retune** table (world −28..−22, `k_loss` 0.01, cooling 0.3). At the shipped values (world −31..−29, `k_loss` 0.02, warming 2.0 / cooling 0.25) the critical-settings change log (2026-09-19) measured **86–99** on 600 real resets; "~92" is that band's midpoint. | Cite 86–99 from `CONFIG_CRITICAL_SETTINGS.md` (2026-09-19 entry). |
| M5 | ❓ Open | §A3 near-field table and the first two §T4 smell bullets | The two rows are correct **at the centre olfaction cell** (offset index 0 of the 5-cell diamond). The other four sampled cells read differently — e.g. the pond's diagonal neighbour reads `0.489` (sum ÷ 4), a value not in the table. Not an error, but the test must say which of the 25 olfaction entries it pins. | Add "centre cell, olfaction index 0" to the T4 assertions. |
| M6 | ❓ Open | §D1: `start_hydration` validated `0 < start < max`, but `start_hydration_low` may be `0.0` | `jax.random.uniform` draws on `[low, high)`, so a random start can be exactly `0.0` and dies on step 1 with reason 6, while a fixed `start_hydration: 0` is refused at load. This mirrors nutrition (`start_nutrition_low: 0`) and is internally consistent, but the two validations disagree about whether a dead-on-arrival start is legal. | One sentence in D1 saying the random draw may include the floor, or set `low > 0` if a step-1 death is unwanted. |

### What was checked and holds

**1. Water clock (§"Target-first water clock").** With `d = 0.625 = 5/8` and `g = 5.625 = 45/8`, every hydration value on the fixed-start paths is a multiple of `1/8` below `2^8`, which needs 11 significant bits — well inside float32's 24 — so the recurrence

$$
W_{k+1} = \operatorname{clip}\!\big(W_k - d + g\,[\text{on pond}],\; 0,\; 200\big)
$$

is exact at every step. Reproduced in numpy float32: away from the pond from 100, `W ≤ 0` first at **k = 160** (`W_160 = 0.0` exactly); on the pond from 100, `W ≥ 200` first at **k = 20**; refill 50 → 100 in **10**, 25 → 100 in **15**; a start at 195 dies on its **first** on-pond step (`195 − 0.625 + 5.625 = 200`). The food clock reproduced the same way (`N_{k+1} = clip(N_k − 1, 0, 200)` from 100) dies at **k = 100**, so "step k" means the same thing on both axes: the k-th `jax_step` call after reset.

**2. Order of operations, against `update_body` as coded.** Nutrition today (`core.py`, "Nutrition Dynamics" block) is: linear decay → optional thermoregulatory drain → refill on `info['ate_food']` → **one** clip to `[0, max]` → death tests `new_nutrition <= 0` and `new_nutrition >= max_nutrition` on the **clipped** value, both folded into `done` inside `update_body`, and `jax_step` stamps the reason from the same predicates. The plan's `clip(W − d + g·drank, 0, max)` → `dehydrated = W' <= 0` / `overdrank = W' >= max` → `done |= …` is this order term for term. `info['ate_food']` is computed from the post-move position, so `info['drank'] = any(water_pos == new_agent_pos)` is the matching convention. There is no "drain, die, then drink" path and no off-by-one.

**3. Smell normalisation (§A3), against `sense_resource` as coded.** The kernel is `f(d) = 1/(d^γ + 1e-10)` with `f = 0.5^{−γ} = 2` on-source, γ = 1, radius 20 (never binding on a 10×10 grid, whose largest agent-to-centroid distance is 10.6). Both table rows reproduce exactly at the centre cell: on a pond cell `(2 + 1 + 1 + 1/√2)/4 = 1.17678`, beside the pond `(1 + 1/2 + 1/√2 + 1/√5)/4 = 0.66358`; food-channel readings `0.588` and `0.332`. **"Equals one item at the centroid" is asymptotic, not exact**, and the plan's wording ("≈", "far field") is right. To leading order, for a pond with cell-centre covariance `Σ`,

$$
\frac{1}{n}\sum_{c\in P} f(\lVert c-x\rVert) \;=\; f(\bar d) \;+\; \tfrac{1}{2}\,\operatorname{tr}\!\big(\nabla^2 f\,\Sigma\big) \;+\; O(\bar d^{-4}),
\qquad \Sigma_{2\times2} = \tfrac{1}{4} I,\quad \Delta\!\left(\tfrac{1}{r}\right) = \tfrac{1}{r^{3}} \text{ in 2-D},
$$

so the relative excess is about `1/(8 d̄²)`: 3.1 % at `d̄ = 2`, 1.4 % at 3, 0.2 % at 8, always positive (Jensen; `1/r` is convex, so the pond reads slightly louder than a point at its middle). Measured over every off-pond cell of the 10×10 grid with the pond at the default candidate `(1,1)`: +4.9 % at the eight edge-adjacent cells (`d̄ = 1.58`), +3.7 % at the four diagonal cells (2.12), ≤ 3 % at every cell with `d̄ ≥ 2.55`, ≤ 1.1 % for `d̄ ≥ 3`, and ≤ **0.18 %** for `d̄ ≥ 8` (12 cells). The T4 "within 3 % at distance ≥ 8" assertion therefore passes with a wide margin; it would pass from 2.55 on. The mix vector interacts linearly and as intended: the per-cell vector is `[0.125, 0, 0, 0, 0.125]` (exact in float32), and the far-field sum is `[0.5, 0, 0, 0, 0.5]·f(d̄)` — half a food on the food channel, half on channel 4, total strength 1.0 — so a 2×2 pond is not 4× louder than one food. "Quieter than one food up close" is true everywhere, not just up close: the food-channel reading divided by one food at the nearest pond cell is 0.33 (beside), 0.35 (diagonal), 0.40 (grid centre), 0.46 (far corner); the quietness comes from the 0.5 mix weight and from the centroid being farther than the nearest cell, and the `1/n` weight is what stops the count of cells from adding to it.

**4. Drive axis (§A1, §D4.3).** `calculate_drive` as coded is `‖[S − S_set, I, (T − T_set)·range_S/max_T]‖` with `range_S = max(setpoint, max_satiation − setpoint) = max(100, 100) = 100` and `max_injury = 100`, so each existing axis is exactly 100 drive units from its own death (`death_penalty = 100`). The proposed `w_axis = (W − W_set)·range_S/range_W` with `range_W = max(100, 200 − 100) = 100` has factor `100/100 = 1.0` exactly in float32, so `w_axis = W − 100` with no rounding. Checked: drive is 0 at the joint setpoint; `W = 0` alone and `W = 200` alone each give exactly 100, the same as `S = 0`, `I = 100` or `T = 15` alone. **When `max_hydration ≠ max_satiation` the scale still holds**: at `max_W = 100, W_set = 50` the factor is 2 and a full-scale deviation is again 100 (one hydration unit then costs two satiation units, and the same 0.625 drain costs 1.25 drive units per step). At `max_W = 300, W_set = 100` only the far end reaches 100 (the floor is 50) — the same asymmetry satiation itself would show off-centre, which is what "mirror" means; W3 (setpoint in the middle) is what makes both ends equal. Reward is `prev_drive − curr_drive − death_penalty·[real death]`, with pre-step `state.hydration` in the first call and post-step `W'` in the second, the pairing satiation and body temperature already use. `info['drive_thirst']` divide-first matches `drive_hunger`. One consequence worth knowing, inherited from the Euclidean form rather than introduced here: with the other axes at setpoint, a thirst step costs 0.625 reward against hunger's 1.0 (the slower clock is proportionally less urgent per step), and when another axis is already far off the marginal cost of a thirst step is tiny (`0.0039` when satiation is 50 units off).

**5. Other equations.** (a) Agent-start repair (§D4.5): `P(c) = 1/N + (k/N)·1/(N−k) = 1/(N−k)` for every non-pond cell — correct, given the permutation stream is independent of the first draw (a `fold_in` of `agent_key` is). The respawn repair is the same argument restricted to the spawn area. (b) Capacity check (§D1): earlier slots hold at most one cell each, so `|A_i| − max_t |pond(t) ∩ A_i| ≥ k_i + 1` guarantees a free in-area non-pond cell at scan position `k_i`; the level-06 numbers (campfire `36 − 1 = 35 ≥ 21`, others `100 − 4 = 96 ≥ 45`) follow from the stated areas. (c) Center mode on 10×10 with a 2×2 block: `((10−2)//2, (10−2)//2) = (4, 4)`, block rows/cols 4–5, contains array `(4, 4)` — as the plan says. (d) Default candidates YAML `[2,2] … [8,8]` → array rows/cols 1–2 and 7–8, inside margin 1 (`1 ≥ 1`, `9 ≤ 9`). (e) `Hydration = W / max_hydration` reads 0.5 at the setpoint, and `Satiation` is coded as `state.satiation / params.max_satiation` (`sensor.py:476`), so the two observations are normalised the same way. (f) Reasons 6 and 7 come from mutually exclusive predicates (`W' ≤ 0` and `W' ≥ 200` cannot both hold), so their stamping order is immaterial.

### Numbers computed for this review

| Quantity | Value | How |
|---|---|---|
| Dehydration step from 100, resting away | 160 | float32 recurrence, exact at every step |
| Over-drinking step from 100, on pond | 20 | same |
| Refill 50 → 100 / 25 → 100 | 10 / 15 | same |
| Food clock from 100 | 100 | same recurrence with cost 1.0 |
| Longest survival with one pond visit | 510 steps (walk 153, drink 39, walk 318) | integer search over visit timing |
| Smell, on a pond cell (sum ÷ 4) | 1.17678 | real kernel, centre cell |
| Smell, beside the pond (sum ÷ 4) | 0.66358 | same |
| Smell, diagonal neighbour (sum ÷ 4) | 0.48877 | same |
| Pond vs. one source at the centroid | +4.9 % (d̄ 1.58), +3.7 % (2.12), ≤ 3 % for d̄ ≥ 2.55, ≤ 0.18 % for d̄ ≥ 8 | all 96 off-pond cells of the 10×10 grid |
| Pond vs. a 1×1 pond on the top-left cell, d̄ ≥ 8 | 6.8–8.5 % | same (basis of M1) |
| Drive, one axis at full scale (S, I, T or W) | 100.0 each | 4-axis norm with `range_S/range_W` |
| Share of `U[0,200]` starts within 50 of an end | 0.5 | (basis of M3) |

**Conclusion:** the plan's equations are correct and match the code they mirror; fix M1 before writing T4, correct the M2 trip counts before the table is quoted anywhere, and the two Low items when the doc is next touched.

Reviewed by: math-reviewer

---

## Feedback from plan-reviewer

> **Reviewed**: 2026-09-29, against the plan at `c7cb7e54` and the code at `81d28c36` (the commit the plan cites). Settled decisions were not reopened; this review asks only whether the plan delivers them safely.
> **Verdict**: **SOUND WITH CONCERNS** — no finding would produce a wrong conclusion, destroy data, or break a hard project rule, so nothing blocks approval. Six Moderate findings would each halt an unattended implementation run or leave a gate silently weaker; all are one-line fixes to the plan text. No report file is written (no Critical finding).
>
> Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run · 🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

### What was checked, and held

Every claim below was verified against the live code or by running it, not taken from the plan:

- **Byte-parity mechanism (the plan's central claim).** Tested directly with the installed flax: a `struct.dataclass` with two trailing `Optional = None` fields has the **same leaf count** as one without them, the **same jaxpr SHA-1** for a function over it, `.replace()` works, and `vmap` over it works. `EnvState._replace` (`state.py:111`) is a one-line alias for flax's `replace`, so D4.6's call form is valid. No hand-built `EnvParams(...)` exists outside the loader, so the new non-default static fields break nothing. Perceptual noise is applied by iterating the **breakdown** names (`sensor.py:420-424`), so a 13th modality slot that no breakdown names is inert — the "append last, nothing shifts" claim holds; 12 modalities are in `default.yaml` today, `_NOISE_SLOTS = 13` (`config_loader.py:2916`), and `_parse_noise_config` runs whether or not noise is enabled (`:2856`), so the D3.4 load-time check fires at level 06 as intended. The `extends:` merge is base-first, child-on-top (`config_loader.py:33-43`), so a child's `hydration:` entry keeps the base's (last) position.
- **The parity test can fail.** Its contrast half (water on must change the rollout and the three jaxprs) fails on pre-change code, where the `water` block is simply never read; the `state.hydration is None` assertion raises `AttributeError` there too. The fixture comes from a detached worktree of the pre-change commit through a generator that asserts `core` was imported from `--src-root` and refuses a dirty tree (`generate_body_mechanics_parity_fixture.py:192-234`), so the comparison is post-change code against frozen pre-change ground truth — not circular.
- **Obs widths.** Measured through the trainer's loader (`load_env_config` + `load_env_params`): levels 00–06 today are **44 / 44 / 52 / 52 / 52 / 58 / 58**, with `Body Temperature` immediately before `Interoceptive Nociception` at 05/06, so the plan's 59 / 59 and its T4 breakdown order are right. Level-05 spawn areas match the capacity arithmetic (campfire `[2,2,8,8]` ×3, 16 resources, 25 obstacles, all others full-grid); `min_fire_separation` is 4 there, which the plan correctly says its check ignores.
- **06 → 07 rename.** `git grep '06-sensory_noise'` over tracked non-doc files returns exactly the plan's table (config, `generate_thermal_probes.py:61`, `make_render_fixture_recordings.py:77`, the two tests, `train_command-agent.sh` live lines 685/4069 plus five comment lines).
- **Death codes.** Exactly four literal lists in `train.py` (1628/2176/2382/2535) plus one in the Dreamer trainer (1248), `balance_metrics._DEATH_CAUSES:75`, and the rPPO real-death mask is `termination_reason >= 2` at four sites — all as stated. `jax_step` has no auto-reset (the rollout loops reset), so T3 reading `new_state.hydration` as `W'` is correct.
- **1-based YAML coordinates**: `start_pos` loads as `jnp.array(...) - 1` (`config_loader.py:2768`) and `_apply_edge_margin` insets from `1 + margin`; the convention claim is right.
- **Project rules.** All new keys read with `get_mandatory` under the gate; the compat entry is a declared, logged supply (not a silent default); every maintenance contract the plan touches is paired in D10 (critical-settings registry + change log, scripts map, config guide + schema); no version strings; `status: active` / `topic: env_entities` are the only values `regen_dev_index.py` accepts (`VALID_STATUS = {active, superseded, archive}`, `env_entities ∈ VALID_TOPICS`; the folder name is not validated), so Call #1 is correct. No `git clean`, force-checkout, stash-drop or branch switch anywhere — the detached worktree for the fixture is safe.
- **Prior art.** The Known Bugs registry has no water / thirst / pond / hydration row; every row the plan cites (#94, #117, #123, #124, #160, #192, #494 family) says what §A11 says it says. No prior plan on water exists under `docs/develop/` or the wiki (only EVAAA-comparison memos mention thirst).

### Findings

| # | Sev | Location | Issue (plain language) | Suggested fix | Owner |
|---|---|---|---|---|---|
| M1 | 🟡 | §D4.6 (`update_body` "11th element … callers that index 0–9 are unaffected") vs `src/environment/core.py:1099` | The plan says existing callers index the tuple, so appending an 11th element is safe. The one production caller **unpacks** it into exactly ten names (`new_satiation, …, done, starved = update_body(...)`). An 11th element raises `ValueError: too many values to unpack` on the first trace of **every** world, so T1 goes red at C3 for a reason that has nothing to do with water. | Rewrite D4.6: "extend the ten-name unpack at `core.py:1099` to eleven (`…, starved, water_out`)". The test callers are fine (`test_body_mechanics_units.py:139/428` and `test_thermal_rate_scales.py:192/218` index; `validate.py:121` slices `out[:9]`). | senior-developer → developer |
| M2 | 🟡 | §T5, "assert the file set is exactly those eight names" | `configs/environment/experiment/basic/` holds **nine** files today: the seven rungs plus `forage_5x5.yaml` and `slow_predator_bush_5x5.yaml`. The assertion as written fails at C5 and halts the run. | Assert that the files matching `^0[0-9]-` are exactly the eight rung names; leave the two non-rung files alone. | senior-developer |
| M3 | 🟡 | §T4, noise-slot test (hydration `sigma: 0.5, mode: constant`, "sample std within 10 % of 0.5") | The hydration column is clipped to `[0, 1]` and sits near 0.5, so with σ = 0.5 roughly a third of the samples are clipped and the measured std is ≈ 0.39, not 0.5 ± 10 %. "Unclipped-region" is not defined, so a literal implementation fails and halts. | In the in-memory override set `clip_min: -10, clip_max: 10` (or σ = 0.02), or compare against a numpy oracle of the clipped Gaussian. | senior-developer |
| M4 | 🟡 | §T1, coverage assert ("fails if a kind is missing **when the pre-change world produces it**") | Circular: the fixture *is* what the pre-change world produces, so the condition can never be false. If the generator's deterministic action rule (`action_at`, rest every third 20-step block) and 16 seeds × 300 steps happen to produce no thermal or over-eating death, terminal-step parity for those codes is "proven" on zero samples with no signal. | Hard-code the expected set per world (e.g. level 05 must contain codes {1, 2, 4, 5}; levels 00–04 {1, 2, 4}); have the generator print the per-code count table into the fixture README; if a code is absent at C1, extend seeds / steps **before** freezing the fixture. | senior-developer |
| M5 | 🟡 | §D4.6 respawn repair + §S ("over 15 % blocks") | A `jax.random.permutation(H·W)` per resource slot per step (16 slots at level 06, vmapped, executed whether or not anything respawned) is the largest new per-step op. If it trips the 15 % gate at C7 the plan says "blocks" and names no fallback — a halt with no exit. | State the fallback now: one shared permutation per step, the k-th respawning slot taking the k-th valid cell; or reject-and-retry a small fixed number of `randint` draws under the fold-in stream. Either keeps the water-off graph untouched. | senior-developer |
| M6 | 🟡 | §A6 consumer table ("found by grep") | The table covers `src/` and `train.py` but analysis scripts also hard-code the outcome set: `scripts/analysis/ladder/lad03_how_it_ends.py` (registry row ~#116 — "hardcodes three outcomes and never checks its shares add up") and `scripts/analysis/studies/context_exploration/part4_readout.py:440` (`Term_Starvation / Term_Injury / Term_Thermal / Term_MaxSteps` columns). Any level-06 run read through them later silently drops dehydration / over-drinking deaths from the shares — a future wrong number, not a blocker now. | Add both as "out of scope, noted" rows; ask `bug-curator` to extend row ~#116 with "codes 6/7 also dropped once water lands". | senior-developer; bug-curator |
| L1 | 🟢 | §A10 rename table | Two more analysis-script text labels become stale after the rename: `scripts/analysis/nmn/run_mod_distribution.py:145` ("ON at basic level 06") and `scripts/analysis/studies/internal_state_reward/f04_thermal_scale.py:59` ("only basic/05 and basic/06 switch the temperature system on" — 07 now does too). Add to the naming-hazard paragraph. | senior-developer |
| L2 | 🟢 | `docs/develop/INDEX.md` | The index at `c7cb7e54` does not list this plan; the regenerated index sits uncommitted in the working tree and may carry other sessions' rows. Diff it and commit only your hunks with the next docs commit. | senior-developer |
| L3 | 🟢 | §D6 shared termination-names constant (Call #10) | Not necessary — the surgical alternative is two tuples added to five lists — but bounded, declared, and justified by drift. Acceptable. One addition: the `_TERM_*` names at `episode_metrics.py:234-238` must be derived from the same constant or they become the sixth copy. | user decides; senior-developer |

### Assumptions the plan rests on (❓ unless marked verified)

1. **Verified** — flax accepts trailing `Optional = None` fields; `None` adds no leaves and leaves the jaxpr text unchanged (tested above). The plan's "stop and report if not" clause will not trigger.
2. **Verified** — noise is applied per breakdown name, so an unused 13th slot cannot change any water-off observation; `noise_modality_order` is static, and used indices do not move under base-first merge.
3. ❓ **The "07 with water off = pre-change 06" case compares rollouts, not jaxprs.** At 07 `noise_modality_order` gains `Hydration` (13 vs 12 entries) and `noise_modes` slot 12 becomes 1 instead of pad 0. Rollouts are byte-equal (assumption 2); the jaxpr SHA is very likely equal too, but the plan should say which it asserts so a SHA mismatch there is not misread as a parity break.
4. ❓ **Fire separation and the (0,0) fallback.** With `min_fire_separation: 4`, three campfires in a 36-cell area, and the pond now able to take one corner cell of that area, the capacity check (which ignores separation, as stated) is not what stops the fallback — the 2,000-reset "every active entity lies inside its own area" assertion in T2 is. Name it as the guard for this case.
5. ❓ **Uniform start hydration over [0, 200) is policy-independent survival noise.** With drain 0.625, a fraction 0.625·k/200 of episodes are dead of thirst by step k whatever the agent does (≈ 5 % by step 16, ≈ 16 % by step 50, before a pond can plausibly be reached). Level 03's nutrition draw has the same property at 1.0·k/200, so this is consistent, but survival steps is the project's metric and the user should own this (Call #3).
6. ❓ **Level 07's "interoception clean" claim already has a hole the plan inherits**: the current noise config sets σ = 0 for satiation / interoceptive / extero nociception but **not** for `body_temperature`, which inherits `default.yaml`'s value. Out of scope, but the T4 "clean on hydration" assertion should not be read as "all interoception clean".
7. ❓ **`Config.merge` is a deep dict update.** Read from the docstring, not the body; if it ever replaced mappings wholesale, 07's `modalities:` block would drop the inherited entries — which today's 06 already relies on not happening.

### Cost of being wrong

If the six Moderate items go in as written, the unattended run halts three times (C3 on the unpack, C4/T4 on the clipped σ, C5 on the nine-file set) — each an hour or two, no wrong conclusion, no data at risk. The one silent failure is M4: a coverage gate that cannot fail leaves terminal-step parity unproven for whichever death kind the fixture happens to lack, which only bites when a later change touches the death path. Nothing here changes a training result or a claim.

*Reviewed by: plan-reviewer*

---

## User decisions after Revision 1 (2026-09-29)

- **Call 1 — random start hydration at level 06: KEEP the full 0–200 draw.** User's rationale, verbatim in substance: the full range exists so the agent experiences *every* internal-state condition during training, because the downstream experiment environment manipulates internal states directly and must test the agent in all of them. The ~5 % by step 16 / ~16 % by step 50 policy-independent thirst deaths are accepted as the cost of that coverage. Analyses reporting survival steps on level 06 should state this and, where it matters, report survival conditional on start hydration.
- **Implementation: NOT approved yet.** The user wants an artifact for this topic first; implementation waits for that.

## Feedback from plan-reviewer — design-page review (2026-09-29)

The design page that supports this plan (`docs/develop/active/thirst/thirst_water.template.html`) was reviewed as an analysis verdict before publication: **supported with caveats**. The 10×10 headline (water costs a scripted agent about 3 percentage points of full-length episodes) holds under variation of the scripted agent's own choices, and the page's correction to this plan's "~5 % dead of thirst by step 16 whatever the agent does" stands (1.8–2.4 % simulated; the 5 % is the no-drinking ceiling). One headline is not a property of the rules: "41 % survival at 20×20 when the pond must be found" is 44–77 % depending on how late the scripted agent starts looking. Findings and exact wording changes: [[plan_thirst_water_page]] (`docs/reviews/plan_thirst_water_page.md`). No settled decision is reopened.

---

## Renderer work done ahead of the environment (2026-09-29)

The rendering session implemented §D8 against snapshot fields only, before any environment change, at the user's request for the design page. Committed as `5818c086` (dashboard) and `7deaee53` (frames + generator).

- **Keys the env must produce.** Snapshot `water_pos` of shape `[h*w, 2]` (every pond cell, array coordinates) and `hydration`; static `params.water_max_hydration`. The recorder (`eval_recording._snapshot_state`) already writes both keys via `getattr`, so they flow through once `EnvState` has them. When `params.water_enabled` exists, `LayoutContext.from_params` asserts it agrees with the recording.
- **Pond look (user decision):** inset with two wave lines, the square's temperature colour kept as a rim, drawn as ground cover under every occupant.
- **§D8.8 audit gate, resolved:** the audit's `cell_overdraw` rule counted the pond's inset as an occupant (21 findings, none a real occlusion). The painter now tags the pond drawing `ground_cover`; the audit excludes tagged ground cover from the occupant count but fails with zero tolerance if ground cover is ever the last thing painted on an occupant pixel. Both directions are permanent tests in `tests/env/test_dashboard_water.py`.
- **Setpoint mark** added as a vital-row option, on for hydration only. Turning it on for nutrition (two-sided since 09-22) is an open follow-up for the user.
- The design page with the calculations and the three mock-up frames: `docs/develop/active/thirst/thirst_water.html`.

---

## Approval (2026-09-30)

**Approved for implementation by the user on 2026-09-30**, after the design page ([[thirst_water]], published https://claude.ai/artifact/5wzcGrqcMRk97CzuFHjAQK). Implementation happens on branch **`v5.0`** in the git worktree `.claude/worktrees/thirst` (cut from `develop` at `711bdc22`); the shared folder is never switched. Nothing merges back into `v4.0`/`develop` without asking the user.

What the approval covers, and what it does not change:
- The plan as written through Revision 1 plus the user decisions above (full 0–200 start-hydration range kept). The design page's correction — the "~5 % dead by step 16 whatever the agent does" figure is an upper bound (simulated 1.8–2.4 %) — changes no code.
- Grid size stays 10 × 10 at level 06; whether to grow the ladder is a separate, open decision.
- **§D8 renderer work is already done** by the rendering session (`5818c086`, `7deaee53`; see "Renderer work done ahead of the environment"). The implementation must produce exactly the fields it reads — snapshot `water_pos` `[h*w, 2]` and `hydration`, static `params.water_max_hydration`, `params.water_enabled` — and must not redo the dashboard work. D8.1 (`build_sensory_viz` "Hydration" branch) is also done.
