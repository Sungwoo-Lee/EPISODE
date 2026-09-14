# Config Guide — how to author and extend environment configs (v3.0)

> **Source**: `src/environment/config_loader.py` (the source of truth for keys) | **Deep reference**: [02_config_schema.md](02_config_schema.md) | **Back to hub**: [ENVIRONMENT_SUMMARY](ENVIRONMENT_SUMMARY.md)

---

## What this document is about

Every experiment in this project is just a **variation of one environment**. The environment is configured entirely through YAML files under `configs/environment/`. This guide is the collaborator-facing introduction to *how those config files work* and *how to write or change one* — it is a workflow guide, not an exhaustive key list (that lives in [02_config_schema.md](02_config_schema.md)).

The one thing to understand first: there is a single canonical "standard setup" file, `configs/environment/default.yaml`, called the **base config**. As of v3.0, a new experiment config no longer copies the whole world spec. Instead it writes one line — `extends: environment/default` — and then lists **only the handful of values that differ** from the base (a smaller grid, a different scene, a noise tweak). At load time the system **deep-merges** the base underneath those overrides, so the agent still receives a complete config. ("Deep-merge" = walk both files key-by-key; where both have a nested block, merge recursively; where a value is present in the experiment, it wins.) This is called a **sparse, layered** config.

A config that does **not** carry an `extends:` line loads **standalone** — exactly as before v3.0, byte-for-byte. This is how the ~91 older "full" configs (now archived) keep working untouched. So the rule is simple: **new work is sparse and layered; old work is standalone and frozen.**

The rest of this guide explains the merge model and its one footgun, where configs live, the five v3.0 features you will meet, how to author a new config and add a new config key, and the parity test that guards all of it. It ends with a **Maintenance Contract** that binds the config-caring agents to keep this guide and the schema doc in step with the code.

---

## 1. The model — base + sparse overrides

### Standalone vs. layered

| Config style | Has `extends:`? | How it loads | Who uses it |
|---|---|---|---|
| **Layered (sparse)** | yes | base deep-merged underneath; this file's keys win | all new experiment configs |
| **Standalone (full)** | no | loaded exactly as written, byte-for-byte (pre-v3.0 behaviour) | the base itself + the ~91 archived configs |

The single chokepoint that implements this is `load_env_config(path)` in `config_loader.py`. It resolves any `extends:` chain (a config may extend a config that itself extends another), strips the `extends:` key (it is metadata, not an env param), deep-merges, and hands the merged result to the existing `load_env_params(...)`. Mandatory-key validation runs **after** the merge — so a sparse config satisfies a required key *through the base*, and the no-fallback contract still holds.

**Missing config file = hard error.** As of the 2026-07-04 strict-load fix (H3, [[fix_plan_h1h2h3_resume_config]]), the low-level loader `Config.load_yaml` raises `FileNotFoundError` when the given path does not exist — it no longer prints a warning and returns an empty config. A typo'd `--config` path used to train silently on `configs/environment/default.yaml`; now it dies immediately. Intentional *optional* loads (train/eval/logger/visualization defaults, etc.) must guard with `os.path.exists(path)` at the call site — every existing optional call site already does.

### Deep-merge semantics and the list-replace footgun

Deep-merge treats **dicts** and **lists** differently:

- **Dicts merge recursively.** If the base has `body: { max_nutrition: 100, death_penalty: 5 }` and your config sets only `body: { death_penalty: 0 }`, the result keeps `max_nutrition: 100` and overrides `death_penalty`.
- **Lists replace wholesale.** If your config declares `resources:` (a list), it **completely replaces** the base's `resources:` list — elements are *not* merged in.

The list rule is the **footgun**. The base config carries scene lists — `entities:` (animals), `resources:`, `obstacles:`. To get a *clean* scene (e.g. a world with no animals), you must declare the list **explicitly empty**:

```yaml
environment:
  entities: []     # SUPPRESSES the base's rabbits + predator
  obstacles: []    # SUPPRESSES the base's rocks/bushes
```

If you **omit** `entities:` instead of setting it to `[]`, the base's animals survive the merge and silently appear in your world. **Omitting a list does not remove it — only an explicit empty list does.** This is the single most common authoring mistake; keep it in mind whenever you want fewer entities than the base.

#### The footgun's sharper edge: a redeclared list can silently reverse a project-wide decision

Omitting a list is the common mistake. The rarer and nastier one runs the other way: you
*do* declare the list, and by declaring it you **drop every field the base set on those
entries** — including a field you have never heard of, that somebody else set deliberately,
project-wide, months ago.

`blocks_animals` is the worked example. A bush with `hides_agent: true` conceals the agent
from a hunting predator. Since 2026-09-14 `configs/environment/default.yaml` also ships
`blocks_animals: true` on that bush, which makes it a physical barrier an animal cannot step
onto — a real refuge rather than only concealment. The loader reads the key with a fallback,
`o.get('blocks_animals', False)` (`config_loader.py:1851`), kept deliberately as a dated
exception to the no-fallback-defaults rule (see
[CONFIG_CRITICAL_SETTINGS.md](CONFIG_CRITICAL_SETTINGS.md)). Put the two together:

```yaml
environment:
  obstacles:                     # <- redeclares the list, so the BASE's bush is gone
    - name: "bush"
      hides_agent: true
      # blocks_animals not written  ->  falls back to FALSE
      ...                        # your bush is permeable; the base's is not
```

This config loads without a warning, runs without an error, and trains an agent in a world
where the bush is not a refuge — the opposite of the project's decision, reached silently
through an omission. Nothing in the YAML text shows it; the only place the truth is visible
is the resolved `EnvParams`.

Two habits follow:

- **If you redeclare `obstacles:` and your list contains a `hides_agent: true` bush, write
  `blocks_animals: true` explicitly.** All four maintained world files with a bush do.
- **Check bindings at the loader, never by grepping YAML.** A grep re-derives the answer from
  the same text that hides the problem. The check that actually binds resolves the config and
  asserts on the arrays:

  ```python
  params = load_env_params(load_env_config(path))
  assert not bool((params.obs_hides_agent & ~params.obs_blocks_animals).any()), path
  ```

  The same shape of check applies to any base-set field on a scene-list entry.

---

## 2. Where configs live

```
configs/environment/
├── default.yaml                    ← the canonical BASE (full, standalone)
└── experiment/
    ├── basic/                      ← live curriculum: sparse `extends:` configs
    │   ├── 00-forage_5x5.yaml
    │   ├── 01-slowPred_5x5.yaml
    │   └── ...
    ├── <your-topic>/               ← new sparse configs go here, grouped by topic
    └── archive/                    ← the ~91 pre-v3.0 full configs (frozen)
```

- **New work** → `configs/environment/experiment/<topic>/` as a sparse `extends: environment/default` file.
- **`archive/`** holds the pre-v3.0 configs, relocated by `git mv` (history preserved). They are **frozen but still loadable** — they have no `extends:` key, so they load standalone exactly as they always did. Do not edit them to "modernise"; if you need a variant, author a fresh sparse config.

---

## 3. v3.0 feature quick-reference

Five capabilities landed in the v3.0 config overhaul. Each is opt-in and defaults to today's behaviour.

### 3.1 `extends:` layering (covered above)

```yaml
extends: environment/default       # or a list: [environment/default, environment/foo]
```
Absent → standalone load. Present → base(s) deep-merged underneath.

### 3.2 Configurable visual properties

Each entity (resource, animal, obstacle) may carry a `visual_properties` appearance vector — the vision analogue of the olfactory `properties` vector. Its length must equal `sensory.visual_vector_size` (default **8**). Omit it and the entity falls back to its historical one-hot channel.

Default channels at V=8: predator→5, neutral→7, food→3, hiding_predator→4, obstacle→6, background grass/sand/plain→0/1/2.

```yaml
- type: "food"
  visual_properties: [0,0,0,1,0,0,0,0]   # one-hot channel 3 = today's default
```

At `visual_vector_size ≠ 8` the class→channel defaults are undefined, so **every** entity must declare an explicit `visual_properties`, and `sensory.visual_background_properties` (a 3×V table, rows = grass/sand/plain) becomes required.

### 3.3 Per-episode visual sampling

An optional `visual_properties_std` (same length V) makes appearance jitter per episode via Gaussian sampling. Default is **zeros → deterministic** (sampled value equals the mean exactly, byte-identical to no sampling). The visual sampler uses an **independent PRNG stream**, so turning it on does not perturb olfactory sampling.

```yaml
  visual_properties:     [0,0,0,1,0,0,0,0]
  visual_properties_std: [0,0,0,0,0,0,0,0]   # zeros = deterministic
```

### 3.4 Initial-state randomization ranges

When you randomize the agent's starting nutrition or injury, you can now set the exact band. The four range keys are **conditional-mandatory** — required only when the matching flag is on:

```yaml
body:
  random_start_nutrition: true
  start_nutrition_low: 0
  start_nutrition_high: 100     # full range; the old code was locked to the upper half
  random_start_injury: true
  start_injury_low: 0
  start_injury_high: 100
```

With the flag `false` the range keys are not read (and need not be present). `default.yaml` carries them explicitly with the flags off (inert).

### 3.5 `eval_seeds` generator spec

The behaviour-measure block's `behavior_measures.eval_seeds` accepts either an explicit list **or** a compact generator spec that derives `eval_n_episodes` seeds deterministically:

```yaml
behavior_measures:
  eval_n_episodes: 64
  eval_seeds: { rng: 12345, sort: true }   # 64 seeds from RNG 12345, sorted
```

`rng` is mandatory inside the dict; `sort: true` (the default) keeps the seed order fixed so episode *i* is comparable across runs.

### 3.6 Per-episode entity count ranges (v3.0 PER\_EPISODE\_ENV\_VARIANCE)

Instead of a fixed `count: N`, each entity entry may declare a range. The engine draws an actual count K uniformly from `[count_low, count_high]` at each episode reset:

```yaml
environment:
  resources:
    - name: "food"
      type: "food"
      count_low: 2          # per-episode lower bound (inclusive)
      count_high: 6         # per-episode upper bound (inclusive); allocation size
      spawn_area: [[1, 1], [10, 10]]
      # ... other fields unchanged
```

**How it works.** The loader allocates `count_high` entity slots — the array shape is fixed (JAX requires it). At each episode reset, K is redrawn and the surplus `count_high − K` slots are **marked inactive**: their positions are parked off-grid so they cannot collide, cause damage, or be sensed.

**Backward compatibility.** `count: N` (no range keys) behaves exactly as before — it is treated as `count_low = count_high = N`, so all K slots are always active (all-True mask). The K-draw is **skipped entirely** when every entry in a class uses a degenerate range, so existing configs produce byte-identical output.

**Constraint.** Do not specify both `count` and `count_low`/`count_high` on the same entry — the loader raises `ValueError`. Use one style or the other.

**Applies to all three entity classes:**
- `resources:` — food, hiding\_predator
- `entities:` — predator, rabbit (any `class`/`behaviour` animal)
- `obstacles:` — rock, bush, tree

### 3.7 Predator jump / pounce (`attack_range` + `attack_success_rate`)

A hunting animal may occasionally lunge several cells in one step instead of its normal 1-cell chase move, either landing on the agent (hit) or beside it (miss) — see [PREDATOR_JUMP_MECHANISM.md](../develop/active/env_entities/PREDATOR_JUMP_MECHANISM.md) for the full design. Both keys are **optional**; omitting either leaves the jump disabled (byte-identical to today):

```yaml
    attack_range: [3, 5]          # or a scalar, e.g. 4. Absent -> [0,0] = disabled.
    attack_success_rate: 0.6      # float in [0,1]. Absent -> 0.0.
```

A bushed (`hides_agent`) agent can never be jumped onto — the jump reuses the existing `agent_hidden` gate.

---

### 3.8 Directional sensors (DIRECTIONAL_SENSORS feature set)

Six `sensory:` knobs and two per-entity keys that let smell carry a direction and
vision be positionally uncertain. **Every one defaults to the pre-change behaviour**,
so a config that sets none of them is byte-identical to before. Deep key list:
[02_config_schema.md](02_config_schema.md#directional-sensors-directional_sensors-feature-set).

```yaml
sensory:
  # --- smell can point ---
  olfactory_grid_range: 1      # radius of the SAMPLING diamond; 1 -> 5 cells, 2 -> 13
                               # NOT sensor_radius, which is how far a smell carries
  # --- vision can be uncertain ---
  visual_sensor_range: 2       # blur needs cells to spread into; >= 1 required
  visual_blur_enabled: true
  visual_blur_anisotropy: 3.0  # 1.0 == isotropic, i.e. a one-value ablation
  # --- vision can be coarse ---
  visual_value_mode: clamp     # presence instead of a count
  # --- vision can be blocked ---
  visual_occlusion_enabled: true
  visual_occlusion_cone_deg: 5.0
  visual_occlusion_strength: 1.0

environment:
  obstacles:
    - name: "rock"
      blocks_sight: true       # independent of `blocking` and `hides_agent`
    - name: "hiding_predator"
      visual_mask: far         # visible ONLY when the agent is standing on it
```

Three things that bite:

- **Blur is inert at `visual_sensor_range: 0`.** One cell, nothing to spread into.
- **`olfactory_grid_range` and `sensor_radius` are different quantities** with
  confusingly similar names. The first is where the field is *sampled*; the second is
  how far the field *reaches*. `default.yaml` carries a note to the same effect.
- **Occlusion is aggressive on the shipped scene** — up to 36 entities on 100 cells.
  Obstacles-only blocking hides 31% of live entities at 5° and 59% at 15°. Start narrow
  and check before assuming a null result means the mechanism did nothing.
- **Occlusion costs about 4.6% of a step** (+3.7 µs at 128 envs, measured paired and
  interleaved against occlusion-off at `visual_sensor_range: 2`). The cone angle does **not**
  change the cost — the tensor shapes are identical either way, only the threshold moves. So
  sweep the angle freely; it is a science knob, not a budget one.

Two groups of keys are **conditional-mandatory** (§5 pattern), read only when their
enabling flag is true, so a config that never uses a feature need not carry its settings:

| enabling flag | keys it gates |
|---|---|
| `visual_blur_enabled` | `visual_blur_radial_scale`, `visual_blur_anisotropy`, `visual_blur_sigma_floor` |
| `visual_occlusion_enabled` | `visual_occlusion_cone_deg`, `visual_occlusion_strength` |

This matters beyond tidiness: every training run freezes its own config at launch, and a
run from before a key existed can never gain it. Every key made unconditionally mandatory
is a key that some historical run snapshot will fail to load without. Keep the mandatory
surface as small as the feature allows.

### 3.9 Thermal — the body-temperature system (`thermal:`)

The world can be made cold everywhere with a campfire in it. Each episode builds a
`[H, W]` map of how warm every cell is; the agent's temperature will drift toward
whatever cell it stands on, so it freezes if it wanders and burns if it sits on the
fire. **Everything ships off** — `thermal.enabled: false` in `default.yaml` — and the
thermal-off path is a static branch that traces the identical graph, so a config that
leaves it off is byte-identical to before. Deep key list:
[02_config_schema.md](02_config_schema.md#thermal-temperature-system).

```yaml
thermal:
  enabled: true
  sigma: 0.7                # blur width; the tight band is 0.6-0.8
  default_temp: [-28, -22]  # world baseline, drawn once per episode
  use_random_spots: false
  use_object_sources: true
  min_fire_separation: 3    # Manhattan, between heat sources
  food_min_fire_distance: 0 # Manhattan, food to fire; 0 = today's behaviour
  temperature_setpoint: 0.0 # the body temperature the agent is trying to hold
  min_temperature: -15.0    # survivable band; leaving it ends the episode (code 5)
  max_temperature: 15.0
  k_exchange: 0.04          # per step, fraction of the gap to the cell's temperature
  k_loss: 0.01              # per step, fraction of the deviation from setpoint undone
  k_metabolic: 0.0          # constant heat produced per step
  grid_range: 1             # thermoceptor RADIUS; 1 -> 5 cells (+5 obs dims)
  relative: true            # report `field - body_temp`, not the raw field
  body_temp_observable: true  # hand the agent its OWN temperature (+1 obs dim)

environment:
  obstacles:
    - name: "campfire"
      count_low: 1
      count_high: 3
      area: [[1, 1], [10, 10]]
      edge_margin: 2              # inset applied to `area` at LOAD time
      temperature_ratio: [11, 13] # heat = ratio x |default_temp|, per fire
      blocking: false
```

Six things that bite:

- **The campfire entry must NOT go into `default.yaml`.** `Config.merge` replaces lists
  wholesale (§1's list-replace footgun), so an obstacle entry in the base file silently
  gives a fire to all 216 layered configs that do not declare their own `obstacles:`
  block — and it would be nearly undetectable, because the campfire is non-blocking,
  renders on the same visual channel as a rock, and has no thermal effect while thermal
  is off. It is simply an extra entity in the placement occupancy mask, shifting where
  everything else spawns. Put it in a config under
  `configs/environment/experiment/thermal/` instead; `campfire_world.yaml` is the worked
  example.
- **`thermal.enabled` is mandatory in every full config** (one without `extends:`). It has
  no fallback default, deliberately: `config.get('thermal.enabled', False)` would let a
  config with a misspelled `thermal:` block train as if thermal were off. A full config
  missing the key raises `Configuration key 'thermal.enabled' is required` at load.
- **Fires must not merge, and 3 is the measured threshold.** Adjacent fires **add** their
  stamps, and the merged field is lethal exactly where the agent needs to stand. Measured
  at sigma 0.7, campfire 300, world -25:

  | Manhattan separation between two fires | comfort-ring (d = 1) equilibrium | verdict |
  |---|---|---|
  | 1 | **+33.0** | past the +15 death threshold — the ring is lethal |
  | 2 | **+15.4** | past the threshold — the ring is lethal |
  | **3** | **+8.4** | intact, and matches the single-fire reference |
  | single fire (reference) | +8.1 | — |

  So a two-fire draw at separation 1 or 2 gives an episode with **no survivable position
  near the fire at all** — burn or freeze — while every metric still calls it a normal
  thermal episode. `0` is documented as "disabled, accepts merged fires" for anyone who
  wants to study that regime on purpose.
- **The default separation is feasible; do not "fix" a placement failure that is not
  happening.** `edge_margin: 2` leaves a 6x6 interior on a 10x10 grid, and three fires
  each 3 or more apart fit there comfortably (the four corners of that interior plus its
  centre already satisfy it). If fires look wrongly placed, the cause is the silent
  cell-`(0,0)` fallback in `resolve_overlaps_global` (an entity parked outside its own
  spawn area when the area fills up), not the separation value.
- **`k_loss` is the number most likely to be changed by accident, and it can delete the
  task.** The body's equilibrium is
  `T* = (k_exchange·T_field + k_loss·temperature_setpoint + k_metabolic) / (k_exchange + k_loss)`.
  On the shipped config `temperature_setpoint` and `k_metabolic` are both `0`, which
  collapses it to `k_exchange·T_field/(k_exchange + k_loss)`, i.e.
  `0.8 · T_field` — but that shorter form is the special case, not the rule, and the
  load-time structure check uses the general one because a config with either key non-zero
  would otherwise be certified against a world it does not build. At the shipped values: standing in a −25 cell settles the body at −20,
  not at −25, because physiology holds off 20% of the cold. That 20% is exactly what makes
  a −25 world cold-but-survivable rather than instantly lethal. Raise `k_loss` to about
  0.036 and the survivable ambient window reaches ±25 — the world's own baseline can no
  longer kill anything and the thermal task disappears, while the config still reads as
  fully configured. Lower it toward 0 and the body simply becomes the cell it stands on.
  It has a [critical-settings registry](CONFIG_CRITICAL_SETTINGS.md) row for this reason.
  Full recurrence and the tug-of-war reading:
  [05_body_homeostasis.md](05_body_homeostasis.md#body-temperature-thermal).
- **`food_min_fire_distance` is a knob that is off, and turning it on is a research
  decision.** At `0` food spawns anywhere, exactly as today. The risk it exists to
  address: an episode whose food lands inside the comfort ring has **no thermal trade-off
  at all** — sit on the ring, eat, stay warm is optimal — and it teaches the agent nothing
  about thermoregulation while still counting as a thermal episode in every metric. If
  such episodes are common the results will understate the task's difficulty. Measure the
  frequency before switching it on.

All the sub-keys are **conditional-mandatory** (§5 pattern), read only when
`thermal.enabled` is true, and the `random_spots.*` trio only when `use_random_spots` is
true as well. The body sub-keys validate at the point they are read: `min_temperature <
max_temperature`, `temperature_setpoint` inside that band, `k_exchange` and `k_loss` each
`>= 0` and summing to `<= 1`, and `grid_range >= 0`. `metabolic_coupling` is read too,
and `metabolic_coupling_rate` is conditional-mandatory one level deeper — read only when
`metabolic_coupling` is true, and validated `>= 0` there. `body_temp_observable` is
conditional-mandatory in the same way, and is the one key in the block that **changes
`obs_dim`**: with it true the agent receives its own body temperature as one extra
observation number, in RAW DEGREES, immediately after Satiation. A 32-wide checkpoint
cannot be restored into a 33-wide run, and a curriculum that mixes the two is rejected by
the pre-flight `obs_dim` + modality-fingerprint check — so flipping it is a new run, not a
resume.

**A mis-tuned thermal config fails at load, and the message tells you how to retune it.**
Beyond the per-key validation above, a thermal config with a real fire in it gets its
radial profile *simulated* at load: the loader builds a single-fire field with the same
blur `jax_reset` uses, at the corners and midpoint of the sampled ranges, and checks that
standing on the fire is lethal, that the ring one cell out is survivable indefinitely, and
that three cells out the cold kills. If any of those three fails it raises `ValueError`
naming the key, the drawn values, the three equilibria and which condition broke — because
the alternative is a run that looks healthy for a week while the agent learns a different
task. The full contract — the four preconditions that decide whether it runs, why an
absolute `temperature:` is skipped rather than certified, and why
`min_fire_separation: 0` with more than one fire is refused outright — is in
[02_config_schema.md](02_config_schema.md#the-load-time-structure-check-stage-6b).

Two things follow for anyone editing a thermal config. **A skip is logged, never silent** —
if you are not sure whether your config was checked, the load log says either
`thermal structure check PASSED` or `thermal structure check SKIPPED: <reason>`. And **the
check is deliberately narrow**: it certifies the pain-plus-comfort structure and nothing
else, so a config it skips is not thereby endorsed.

**Videos of a thermal episode show two new things**, and both come from
`src/environment/renderer.py`. The world's temperature is painted under the grid as a
diverging blue–red underlay whose colour limits are **fixed for the whole episode** and
centred on `temperature_setpoint` (a per-frame rescale would make a cooling world look
stable, which is the one thing the picture exists to disprove), and the agent's own body
temperature appears as a gauge in the vitals stack with the two death thresholds marked.
`render_jax_state` also takes `debug_thermal_cells=True`, off by default, which outlines
the five cells the thermoceptor actually reads. Recordings made before the thermal system
carry neither field and render exactly as they always did — the recording format was not
versioned for this, the reader simply treats both fields as optional.

**`metabolic_coupling` makes staying warm compete with staying fed, and it is off.**
With it false — which is every config in the repo — nothing changes: the drain sits behind
a static Python `if`, so it contributes no operation to the traced graph, and a thermal-on
rollout is bit-identical to what it was before the feature existed
(`tests/env/test_metabolic_coupling.py::test_off_by_default_is_a_provable_noop`, held
against a fixture captured from source that predates it). Switch it on and each step costs
`metabolic_coupling_rate * |k_loss * (body_temp − temperature_setpoint)|` nutrition — the
magnitude of the `k_loss` term of the body recurrence, i.e. the thermoregulatory work the
body is actually doing, rather than the raw deviation it is doing it against. Turning it
on is a research decision, not a tuning one: it changes the task from "keep warm" to "keep
warm *and* keep fed, out of one budget", and every run before the switch is on the other
task. Mechanism and the pinned update ordering:
[05_body_homeostasis.md](05_body_homeostasis.md#metabolic-coupling-thermal).

**`max_temperature` has a second job: it is the warmth-vs-hunger exchange rate.** From
Stage 4 the homeostatic drive has three axes, and the third one is body temperature. The
drive is the Euclidean norm in *satiation units* — the two existing axes are untouched and
the thermal axis is scaled up by `max_satiation / max_temperature`:

```
drive = || ( satiation - satiation_setpoint,  injury,
             (T - temperature_setpoint) * max_satiation / max_temperature ) ||
```

That is the design's per-axis-normalised drive multiplied through by `max_satiation`, and
the multiplication is not cosmetic: writing the normalised form literally would divide
**every reward in the project** by 100 while `death_penalty` stayed at 100, changing the
relative weight of dying by two orders of magnitude on thermal-**off** configs too. With
the shipped numbers (`max_satiation: 100`, `max_temperature: 15`) the factor is
**100/15 = 6.67**, i.e. **one degree of body-temperature deviation costs the same drive as
6.67 satiation units**. Nothing else in the config makes that exchange rate visible, so
halving `max_temperature` does not merely narrow the survivable band — it doubles how much
the agent is paid to stay warm. On `thermal.enabled: false` the drive is the two-axis
expression it has always been, character for character, behind a static Python branch
(`core.py::calculate_drive`).

`info['drive_thermal']` joins `drive_hunger` and `drive_injury` in the step info dict when
thermal is on, and follows *their* convention rather than the drive's: it is the **squared
normalised** deviation `((T - temperature_setpoint) / max_temperature)²`, so the three
logged series stay comparable with each other and with historical runs. It is emitted only
when thermal is on — `max_temperature` is `0.0` on a thermal-off config — so consumers must
read it with `.get`.

**Turning thermal on widens the observation, and that is a one-way door for curricula.**
`grid_range: 1` adds **five** dimensions (`2r² + 2r + 1` cells of a Manhattan diamond),
inserted after Extero Nociception and before Olfaction. The curriculum pre-flight check
compares `obs_dim` across stages *before* it compares the modality fingerprint, so a
curriculum that mixes thermal and non-thermal stages is rejected with "changes obs_dim".
That is correct and must not be relaxed: **a curriculum is thermal throughout or
non-thermal throughout.** A thermal curriculum whose early stages have no fire still
declares `thermal.enabled: true` with a neutral field, so the width stays constant.
`relative` is in the modality fingerprint for the complementary reason — it changes what
the five numbers *mean* at an identical width, which the `obs_dim` check cannot see. `temperature` and `temperature_ratio` are mutually exclusive on one entry,
and **an animal entry declaring either one raises** — the field is built once at reset and
animals move.

---

---

## 4. How to author a new config (worked example)

Goal: a 5×5 foraging world with food only — no animals, no obstacles — inheriting everything else (body, sensors, noise) from the base.

```yaml
# configs/environment/experiment/basic/00-forage_5x5.yaml
extends: environment/default

environment:
  height: 5
  width: 5
  start_pos: [3, 3]

  resources:                       # REPLACES the base resource list wholesale
    - name: "food"
      type: "food"
      count: 2
      spawn_area: [[1, 1], [5, 5]]
      properties: [1.0, 0.0, 0.0, 0.0, 0.0]
      properties_std: [0.0, 0.0, 0.0, 0.0, 0.0]
      visual_properties: [0,0,0,1,0,0,0,0]
      visual_properties_std: [0,0,0,0,0,0,0,0]
      max_consumption: 12
      regeneration_delay: 0
      damage: [0.0, 0.0]
      nociception_intensity: 0.0

  entities: []                     # explicit empty → SUPPRESS base rabbits + predator
  location_areas:
    - { type: "grass", area: [[1, 1], [5, 5]] }
```

Everything not mentioned — the whole `body:`, `sensory:`, `perceptual_noise:`, `behavior_measures:` blocks — comes from `default.yaml` unchanged. This is the real `00-forage_5x5.yaml`; read the live `configs/environment/experiment/basic/` files for more patterns.

---

## 5. How to add a new config key (the no-fallback workflow)

The project rule is **no fallback defaults**: critical keys are read with `config.get_mandatory('key')` and a missing key raises `ValueError`. Adding a new key is therefore a multi-step change that must land **atomically**:

1. **Add the key to `configs/environment/default.yaml`** with an explicit value and an inline comment explaining it. The base must always carry every key it reads, so layered configs inherit a valid default-of-record.
2. **Read it in `config_loader.py`** via `config.get_mandatory(...)` (or, for a conditional key, gate the `get_mandatory` behind its enabling flag — see the initial-state range keys for the pattern). If it is shape-determining, store it on `EnvParams` as a static field (`struct.field(pytree_node=False)`); otherwise as a traced leaf.
   - **The gating flag of a conditional block is itself unconditionally mandatory, and never gets a fallback default.** `thermal.enabled` is the worked example: `config.get('thermal.enabled', False)` would let a config with a misspelled `thermal:` block load clean and train as if the feature were off. The fallback is also what would make deferring a config migration unsafe — a deferred config is only safe because `get_mandatory` fails loudly and names the missing key.
   - **`Config` does not resolve `extends:`.** `load_env_config` in `train.py` does; `Config.load_yaml` is `cls(yaml.safe_load(f))` and nothing more. So the fixture generators and the parity tests, which build params straight from a raw `Config`, cannot inherit a new gate from `default.yaml` — **every full config** (one with no `extends:`) has to carry the key itself, as do the test modules with inline YAML bases. Budget for that migration in the same change; commit `0e8a4ef8` (`visual_blur_enabled`) and the 2026-09-08 thermal change are the two precedents.
   - **Or choose the conditional shape specifically so there is no migration to budget for.** `thermal.body_temp_observable` (2026-09-14) is the worked example. It could have been read unconditionally, next to `sensory.injury_observable`; instead it is read inside the existing `if thermal_enabled:` block. The reason is arithmetic, not taste: **72** stand-alone configs carry a committed byte-parity fixture, every one of them ships `thermal.enabled: false`, and an unconditional `get_mandatory` would have raised on all 72 at load — turning the project's main regression gate red before it compared a single byte, and requiring a 72-file inline migration plus ~20 test modules with inline YAML bases. Under the conditional shape **zero** fixture configs changed and the suite stayed at 72 passed. Put a new key under an existing gate when one fits; take the migration only when the key genuinely has to be read on every config. **And never soften the deferral with a fallback default** — the 68 configs left unmigrated are safe *only* because `get_mandatory` fails loudly and names the key, which is what `tests/env/test_backward_compat_configs.py` keys its skip on.
3. **Document it here** (in the quick-reference if it is a feature surface) **and in [02_config_schema.md](02_config_schema.md)** (the deep key list). Both move in the same change.
4. **Add or extend a test** that proves the key is read and that a missing/invalid value raises. For a regression-class change, the test must fail before the code change and pass after.
5. **For sensory / noise keys, keep observation↔noise width in sync.** Observation width is computed in one place, `get_observation_breakdown`; the per-modality noise block auto-resizes from it. A new sensor or a width change must keep the noise modality list aligned — route through `env-config-reviewer`.

If the key is experiment-facing, the schema/loader work is `senior-developer` + `developer`'s job first; only then does `experiment-designer` author configs that use it.

---

## 6. The parity gate

Two regression tests are the safety net for the entire config system:

- **`tests/env/test_unified_parity.py`** — for each config, instantiates `EnvParams` and checks a reset+rollout against a committed fixture. It protects the byte-for-byte behaviour of every config, including all archived ones.
- **`tests/env/test_visual_parity.py`** — the same discipline for the visual observation slice, across the base plus the basic curriculum.

These gates must stay **green** on every config-system or schema change. A red parity test means a change perturbed a config that was supposed to be byte-identical — **stop and diff**, do not regenerate fixtures to make it pass (regenerating hides the very regression the gate exists to catch). Fixtures are regenerated only deliberately, on a pre-change commit, when the change *intends* to alter observations.

---

## 7. Training-config layering (`configs/train/`)

This guide is mostly about `configs/environment/` (the world spec), but the same base-plus-override pattern also governs the **training-run** config — checkpoint cadence, logging cadence, and similar knobs that are not part of the environment itself. Two trainers read this layer: **rPPO** (`train.py`) and **Dreamer** (`src/algorithms/dreamer_srl/dreamer_srl_main.py`).

**The rule: `configs/train/default.yaml` is the reference/documentation file** — it declares every training/logging knob with a generic default value, and doubles as the fallback for algorithms that load neither per-algo layer (DQN, DRQN, PPO). Anything rPPO or Dreamer wants different from that generic default lives in that trainer's own override file, merged **above** `default.yaml` (see the "Self-contained per-algo files" note below — the two layers now intentionally duplicate keys rather than one being authoritative-only):

- `configs/train/recurrent_ppo.yaml` — rPPO's per-algo layer. `train.py` merges it **only** when the agent config declares `agent.algorithm == "RecurrentPPO"` — a real gate, because `train.py` is shared across algorithms and must not apply rPPO's values to a non-rPPO run.
- `configs/train/dreamer_srl.yaml` — Dreamer's per-algo layer. `dreamer_srl_main.py` merges it **unconditionally**, at both its merge sites (single-config and the `--configs-dir` curriculum path). There is no algorithm gate here, and this is a deliberate asymmetry with rPPO, not an oversight: `dreamer_srl_main.py` is a Dreamer-only entry point, so the gate would have no job to do — and it would actively break two real agent configs (`configs/models/dreamer_srl/agent_xs.yaml`, `configs/models/dreamer_srl/01_food_only_smoke.yaml`) that do not declare `agent.algorithm` at all.

Full merge order (each stage's keys win over the ones before it):

```
get_default_config() (built-in seed)
  → configs/train/default.yaml            (algorithm-neutral)
  → configs/train/<algo>.yaml             (recurrent_ppo.yaml or dreamer_srl.yaml)
  → configs/evaluation/default.yaml
  → configs/visualization/default.yaml
  → env --env-config  (or, for Dreamer curriculum, the per-stage env YAML)
  → --agent-config
  → CLI flags (e.g. --log-interval, --checkpoint-frequency)
```

**Self-contained per-algo files (v3.0 convention — reverses an earlier structural-enforcement design).** Each of `recurrent_ppo.yaml` and `dreamer_srl.yaml` declares its **own complete set of training/logging values** — `training.num_envs`, `training.checkpoint_frequency`, `training.max_checkpoints_to_keep`, and all four `logging.*` knobs (`episode.smoothing_episodes`, `episode.interval_episodes`, `step.smoothing_iters`, `step.interval_iters`) — so either file can be read top-to-bottom without cross-referencing `default.yaml` or the other algo's file. `configs/train/default.yaml` **also** declares every one of these keys, with generic default values: it is the reference/documentation layer (read it to see every knob that exists) **and** the fallback for algorithms that load neither per-algo file (DQN, DRQN, PPO — see the merge order above). The per-algo file wins for its own algorithm because it is merged **above** `default.yaml`.

**Async checkpoint-video render keys (added 2026-07-27, [[ASYNC_CHECKPOINT_VIDEO_RENDER]]).** Three `training.*` keys govern whether the checkpoint-triggered MP4 render blocks the training loop:

| Key | `default.yaml` | `recurrent_ppo.yaml` / `dreamer_srl.yaml` | Meaning |
|---|---|---|---|
| `training.async_video_render` | `false` | `true` | `true` → the MP4 render runs as a non-blocking CPU subprocess (dispatch/poll/drain, `src/utils/async_render.py`); the trainer polls once per iteration and uploads the finished MP4 from the parent process. `false` → legacy blocking `subprocess.run` render inline in the loop (the kill-switch, and the pre-plan behavior — still the fallback for DQN/DRQN/PPO). Read via `get_mandatory`. |
| `training.render_every_n_checkpoints` | `1` | `1` | Render the MP4 only every Nth checkpoint (async path only). Recordings (`.rec.gz`) and checkpoints are still written at **every** checkpoint regardless; a skipped MP4 is offline-recoverable via `scripts/eval/render_recordings.py`. Read via `get_mandatory`. |
| `training.render_workers` | `null` | `8` | `--workers` cap passed to the render subprocess; `null` = the renderer's own default (`cpu_count − 1`). Largely inert: the renderer parallelises per episode, so with `eval_video_episodes: 3` at most 3 workers ever do work. Read via `.get` — `null` is a legitimate declared value, and `get_mandatory` treats `None` as missing. |

Recordings, `run_meta.pkl`, and Orbax checkpoints are byte-identical in both modes; only the MP4 drawing + WandB upload move off the critical path (the video lands on the dashboard ~1–4 min later, at a later — still forward-monotone — step).

An earlier revision of this split enforced `logging.episode.smoothing_episodes` (how many episodes are averaged into each dashboard point) **structurally identical** across algorithms by declaring it *only* in `default.yaml` and omitting it from both per-algo files, so they inherited the same value by construction. **That structural enforcement has been intentionally reversed** — the user may legitimately want different smoothing per algorithm, so it must not be locked. `smoothing_episodes` is now declared explicitly in `default.yaml`, `recurrent_ppo.yaml`, and `dreamer_srl.yaml` (currently all `5000`, by convention, not by code). **Keeping the value equal across the two per-algo files is a documented convention, not a structural constraint** — the comparability guarantee (a Dreamer curve and an rPPO curve being equally noisy) now depends on a human keeping the two copies in sync, not on the merge order making drift impossible. See [[DREAMER_TRAIN_CONFIG_SPLIT]] for the full design history, including the superseded rationale.

---

## 8. Pointers

- **[02_config_schema.md](02_config_schema.md)** — the deep, key-by-key reference (YAML → `EnvParams`, mandatory keys, expansion rules).
- **`src/environment/config_loader.py`** — the source of truth. When the doc and the code disagree, the code wins and the doc is wrong; fix the doc.
- **[ENVIRONMENT_SUMMARY.md](ENVIRONMENT_SUMMARY.md)** — the environment hub (observation table, latent-bug FAQ, reading order).
- Design rationale (not required reading): [`docs/develop/active/refactors/CONFIG_LAYERING_AND_EXPERIMENT_REORG.md`](../develop/active/refactors/CONFIG_LAYERING_AND_EXPERIMENT_REORG.md), [`docs/develop/active/refactors/CONFIGURABLE_INITIAL_STATE_RANGES.md`](../develop/active/refactors/CONFIGURABLE_INITIAL_STATE_RANGES.md), [`docs/develop/active/sensors/CONFIGURABLE_VISUAL_PROPERTIES_PLAN.md`](../develop/active/sensors/CONFIGURABLE_VISUAL_PROPERTIES_PLAN.md).

---

## Maintenance Contract

**Any change to the config schema or the config system MUST, in the same change:**

1. **Update `configs/environment/default.yaml`** — add/rename the key with its explicit value and update its inline comment.
2. **Update this guide AND [02_config_schema.md](02_config_schema.md)** — keep the workflow guide and the deep key reference in step with the code.
3. **Add or extend a test** that exercises the new/changed behaviour (and proves a missing/invalid value raises, for mandatory keys).
4. **Keep the parity gate green** (`tests/env/test_unified_parity.py`, `tests/env/test_visual_parity.py`) — or, if the change deliberately alters observations, regenerate fixtures on a pre-change commit and say so explicitly.

**The agents below are bound to READ this guide before any config work and to UPDATE it (and `02_config_schema.md`) in the same change whenever the schema or system changes:**

- `env-config-reviewer` and `experiment-designer` — primary config owners.
- `developer`, `senior-developer`, `code-reviewer` — secondary, whenever their work touches `config_loader.py`, `state.py` (`EnvParams`), or `configs/`.
