# 05 — Body & Homeostasis

> **Source**: `src/environment/core.py` (`update_body` `core.py:44–117`, `calculate_drive` `core.py:38–42`) | **Back to hub**: [ENVIRONMENT_SUMMARY](ENVIRONMENT_SUMMARY.md)

---

## What this doc is about

The agent has an internal body — a small physiological simulation that runs inside every step of the environment. Three numbers matter: **nutrition** (how much energy the agent has stored), **satiation** (a subjective sense of fullness derived from nutrition), and **injury level** (accumulated physical damage). The agent dies of starvation when nutrition hits zero, of over-eating when nutrition reaches its ceiling, or of injury when accumulated damage reaches its maximum. In between, drive-reduction reward pushes the agent to keep its body close to a healthy setpoint.

**Food is a two-sided axis (since 2026-09-22).** Nutrition runs `0..200` with the healthy setpoint at **100 — the middle, not the top**. Too much food is punished exactly as much as too little, and both ends are lethal. Before that date the setpoint *was* the ceiling, so more food was always better and the only thing to regulate was not running out.

A fourth number, **body temperature**, exists only when the temperature system is switched on (`thermal.enabled: true`). It drifts toward the temperature of the cell the agent is standing on while the agent's own physiology pulls it back toward a comfortable setpoint, and leaving its survivable band ends the episode with termination code 5. On every config that does not enable the temperature system it is a constant zero that nothing reads — see [Body Temperature](#body-temperature-thermal) below.

This doc describes exactly how those numbers change each step, including all constants, clip bounds, and the two supporting buffers — the injury smoothing ring buffer and the nociception history buffer — that connect body state to the interoceptive sensor (doc 09).

---

## Body State Fields in `EnvState`

All fields are scalars (shape `[]`) unless noted. Declared in `src/environment/state.py:61–68`.

| Field | Shape | dtype | Description |
|-------|-------|-------|-------------|
| `satiation` | `[]` | float32 | Subjective fullness derived each step from nutrition |
| `nutrition` | `[]` | float32 | Objective energy store; decays each step |
| `injury_level` | `[]` | float32 | Accumulated physical damage, smoothed and recoverable |
| `injury_buffer` | `[smoothing_duration]` | float32 | Ring buffer that spreads a single damage event across future steps |
| `nociception_history_buffer` | `[interoceptive_kernel_length]` | float32 | Sliding window of past `injury_level` values; idx 0 = most recent |
| `last_collision_noc` | `[]` | float32 | Nociception intensity of the most recent wall/obstacle collision |
| `rest_streak` | `[]` | int32 | Consecutive resting steps (used to accelerate recovery) |
| `body_temp` | `[]` | float32 | Body temperature. Updated only when `thermal.enabled=True`; a constant `temperature_setpoint` (0.0) otherwise |

---

## Hidden Body States

A core design principle is the decoupling of **Ground Truth Body State** from **Sensory Observation**:

1. **Ground Truth Authority**: The fields `injury_level` and `nutrition` in `EnvState` are the source of truth for the agent's survival. If `injury_level >= max_injury` or `nutrition <= 0`, the agent dies, regardless of whether it can "feel" or "see" these values.
2. **Masking (Hidden States)**:
   - `injury_observable = False`: The `Injury` slot is removed from the observation vector. The agent must rely on delayed, convolved interoceptive signals (see doc 09) to infer its state.
   - `nutrition_observable = False`: The `Nutrition` slot is removed. The agent must rely on `Satiation` (which is always observable) or behavior to manage its energy.
3. **Internal Dynamics**: These ground truth values always update normally behind the scenes, ensuring consistent physics and reward calculation even in "blind" configurations.

---

## Nutrition Dynamics

`core.py:50–58`

**Governing equation** (applied each step when `with_nutrition=True`):

```
new_nutrition = clip(prev_nutrition - metabolic_cost - thermal_drain + ate_food_gain,
                     0.0, max_nutrition)

where:
  ate_food_gain = food_nutrition_gain - eating_nutrition_cost   (if ate_food else 0)
  thermal_drain = metabolic_coupling_rate * |k_loss * (T - temperature_setpoint)|
                                                (if thermal.metabolic_coupling else 0)
```

**The order of those four operations is pinned and is not recoverable from the
config**: linear decay, then the thermoregulatory drain, then the refill from food,
then a **single** clip to `[0, max_nutrition]`. Putting the clip last is what decides
whether a cold step can starve an agent that also ate this step — eating offsets the
drain *within* the step rather than after it — and it is also what stops the drain from
going anywhere near a negative nutrition value: the termination test reads the clipped
number, so an arbitrarily large drain lands on exactly `0.0` and dies of starvation
(code 2) rather than slipping past the check.

- `metabolic_cost` (default 1.0): drained unconditionally every step, even while resting.
- `food_nutrition_gain` (default 6): gross nutrition from consuming a food resource.
- `eating_nutrition_cost` (default 1.0): the physical cost of the eating act, subtracted from gain.
- Net gain from eating: `6 - 1 = 5` nutrition in the default config.
- `thermal_drain` (default: absent — `thermal.metabolic_coupling` is `false`): see
  [Metabolic coupling](#metabolic-coupling-thermal) below.
- Clamped to `[0.0, max_nutrition]` — one clip, after everything else.

**When `with_nutrition=False`**: `new_nutrition = prev_nutrition` — no decay, no gain, no starvation death (`core.py:57–58`).

**Starvation death**: triggered inside `update_body` at `core.py:108–110` when `new_nutrition <= 0.0` (termination reason code 2).

**Starvation timeline with defaults** (`max_nutrition=200`, `start_nutrition=100` — the setpoint — `metabolic_cost=1.0`, net eating gain=5): from the shipped start the agent starves in exactly 100 steps without eating, and in 200 steps from a completely full body; it needs to eat at least once every 5 steps to hold its level. Eating *more* often than that is not free — it pushes nutrition above the setpoint, which costs drive and eventually kills.

**Over-eating death**: when `overeating_death=True` (the shipped default since 2026-09-22), `update_body` sets `done=True` when `new_nutrition >= max_nutrition`, and `jax_step` stamps termination-reason code 3 on the same predicate. It is a **real death**: it is captured before the truncation merge, so the `death_penalty` fires exactly as it does for starvation. Both ends of the food axis are wired identically — starvation at `new_nutrition <= 0.0`, over-eating at `new_nutrition >= max_nutrition`.

> Until 2026-09-22 this was telemetry only, and wrong telemetry at that: reason 3 was stamped from `new_satiation >= max_satiation` while `done` had no over-eating branch at all, so an agent that merely reached full satiation carried a "died of over-eating" label on steps it survived. Pinned now by `tests/env/test_two_sided_nutrition.py`.

---

## Satiation Dynamics

`core.py:61–66`

Satiation is **not independently tracked** — it is re-derived deterministically from nutrition every step:

```
fullness_ratio = clip(new_nutrition / max_nutrition, 0.0, 1.0)
new_satiation  = max_satiation * fullness_ratio ^ k
```

where `k = nutrition_to_satiation_scaling_factor` (default 1.0 = linear).

This power-law mapping allows different subjective hunger curves:
- `k = 1.0`: linear — satiation tracks nutrition directly.
- `k < 1.0`: sub-linear — agent feels relatively full even with low nutrition (optimistic subjective hunger).
- `k > 1.0`: super-linear — agent feels relatively empty unless nutrition is near-full (pessimistic subjective hunger).

Since satiation is fully derived from nutrition, `random_start_satiation` is a no-op — the flag exists in `EnvParams` (`state.py:179`) but is **never read** during `jax_reset`. The initial satiation is always computed from the initial nutrition value (`core.py:915–916`).

**When `with_satiation=False`**: `new_satiation = state.satiation` — value frozen at its reset-derived level (`core.py:65–66`).

---

## Reset Initialisation of Body State

`core.py:907–925` (inside `jax_reset`)

| Field | Condition | Value |
|-------|-----------|-------|
| `nutrition` | `random_start_nutrition=True` | Uniform `[max_nutrition / 2, max_nutrition]` |
| `nutrition` | `random_start_nutrition=False` | `params.start_nutrition` |
| `satiation` | always | `max_satiation * clip(nutrition / max_nutrition, 0, 1) ^ k` |
| `injury_level` | `random_start_injury=True` | Uniform `[0, max_injury / 2]` |
| `injury_level` | `random_start_injury=False` | `0.0` |
| `injury_buffer` | always | `jnp.zeros(smoothing_duration)` |
| `nociception_history_buffer` | always | `jnp.zeros(interoceptive_kernel_length)` |
| `last_collision_noc` | always | `0.0` |
| `rest_streak` | always | `0` |
| `body_temp` | always | `params.temperature_setpoint` (0.0 with the temperature system off) |

The agent starts each episode **comfortable**, at its own setpoint, rather than at the temperature of the cell it happens to spawn on. The cold has to work on it.

---

## Injury Ring Buffer & Streak Recovery

`core.py:68–100`

### Damage Smoothing (Ring Buffer)

Rather than applying damage instantly, each step's damage is spread across `smoothing_duration` future steps. This prevents large single-hit deaths and creates a biologically realistic ramping pain experience.

```
Step-by-step when with_injury=True:

  inc           = damage / smoothing_duration        # per-step dose from new damage
  temp_buffer   = state.injury_buffer + inc          # broadcast add to all future slots
  applied_inc   = temp_buffer[0]                     # front slot applied this step
  new_injury    = prev_injury + applied_inc

  new_buffer    = jnp.roll(temp_buffer, -1).at[-1].set(0.0)
                # shift entire buffer left by 1; zero the new tail slot
```

`core.py:72–80`

A single damage event of value `D` results in `D / smoothing_duration` injury added per step for the next `smoothing_duration` steps. The front of the buffer is applied **immediately on the same step as the damage** — there is no onset delay. After the roll, the tail of the buffer is zeroed so no phantom increments persist after the window closes.

**Example**: `D=20`, `smoothing_duration=10` → `inc=2.0` per step. At step 0 (damage step), `applied_inc = 0 + 2 = 2`; steps 1–9 each apply 2 more; step 10 applies nothing (buffer cleared). Net: `+20` total injury over 10 steps.

**Special case** `smoothing_duration=1`: `inc = damage`, `applied_inc = damage` immediately. Disables smoothing — a single hit jumps injury by the full damage value.

### Recovery (Streak-Based Exponential)

`core.py:82–96`

When the agent selects action 4 (Rest, if `rest_action_enabled=True`) and no buffered damage is being applied in this step (`applied_inc <= 0`), injury recovers with an exponentially accelerating rate:

```
# 1. Update streak (purely based on action, not damage)
new_rest_streak = prev_rest_streak + 1   if info['rested']
                = 0                      otherwise

# 2. Compute multiplier using the updated (already-incremented) streak
recovery_mult   = (1 + recovery_accel_rate) ^ (max(new_rest_streak, 1) - 1)
recovery_amount = recovery_base_rate * recovery_mult

# 2b. LOCATION PREMIUM (body.recovery_in_bush_multiplier). STATIC Python guard:
#     at the shipped 1.0 these two lines are not traced at all and the graph is
#     the pre-feature one. `agent_in_bush` is the shared predicate
#     core.py::agent_in_hiding_obstacle evaluated at the POST-move cell.
if recovery_in_bush_multiplier != 1.0:              # trace-time, not jnp.where
    recovery_amount = recovery_amount * (recovery_in_bush_multiplier if agent_in_bush else 1.0)

# 3. Apply recovery only if resting AND no damage being absorbed this step
can_recover = info['rested'] AND (applied_inc <= 0)
new_injury  = new_injury - recovery_amount    if can_recover
            = new_injury                      otherwise

# 4. Clamp
new_injury = clip(new_injury, 0.0, max_injury)
```

`core.py:84, 89–94, 96`

Note: `new_rest_streak` (already incremented) is used when computing `recovery_mult`, not `prev_rest_streak`. This means the very first resting step uses streak=1 → multiplier=1.0 (base rate).

**Default recovery table** (`recovery_base_rate=0.1`, `recovery_accel_rate=0.5`). The
right-hand column shows what the same step would recover **while standing on a concealing
bush** if `recovery_in_bush_multiplier` were set to `3.0`; at the shipped `1.0` the two
columns are identical and the bush makes no difference to healing:

| Consecutive rest streak | `recovery_mult` | Recovery per step (open) | Recovery per step (in bush, multiplier 3.0) |
|------------------------|-----------------|------------------|------------------|
| 1 | 1.0 | 0.1 | 0.3 |
| 2 | 1.5 | 0.15 | 0.45 |
| 3 | 2.25 | 0.225 | 0.675 |
| 4 | 3.375 | 0.3375 | 1.0125 |
| 10 | ~57.7 | ~5.77 | ~17.3 |

**Location premium** (`body.recovery_in_bush_multiplier`, mandatory, ships at `1.0`): recovery
is multiplied by this value on any step the agent rests **on a cell occupied by an active
obstacle marked `hides_agent: true`** — a bush. The multiplier is applied to
`recovery_amount`, i.e. *inside* the existing rest-and-no-damage condition, so a premium is
only ever collected on a step that would have recovered something anyway. It must be `> 0`;
`1.0` means "resting in cover is worth exactly what resting in the open is worth", and at
exactly `1.0` the branch is a trace-time Python `if` that emits no operation, so the
environment's computation graph is identical to the pre-feature one.

**Streak reset rule**: `new_rest_streak = prev + 1 if rested else 0` (`core.py:84`). The streak depends only on the *action*, not on damage. A step where the agent rests **and** takes damage extends the streak by 1 but skips recovery (because `applied_inc > 0`). On the next undamaged rest step, full streak-multiplied recovery resumes.

**Streak reset rule — and location (decision D2, 2026-09-15)**: the streak depends only on the
*action*. It does **not** reset when the agent leaves cover, and it does not restart when the
agent enters it. This was decided rather than inherited: a location term would change
`new_rest_streak` — and through it survival — for **every** config, including those that set
`recovery_in_bush_multiplier: 1.0` and thereby opted out of the premium entirely, which would
make an inert setting non-inert. The accepted trade-off is that at a high `recovery_accel_rate`
an agent can bank a long streak resting in the open and cash the location premium on the step it
enters a bush; that exploit is self-limiting, because resting in the open is exactly where a
predator can reach it. A study using both knobs should report them together. Pinned by
`tests/env/test_recovery_in_bush.py::test_streak_not_location_dependent`; see D2 in
`docs/develop/active/refactors/BUSH_REFUGE_AND_LOCATION_DEPENDENT_RECOVERY.md`.

**No cap on `recovery_mult`**: the exponential grows without bound. At `recovery_accel_rate=0.5` and streak 20, recovery ≈ 222 per step — the injury clamp at 0 prevents over-subtraction, but very long streaks make injury vanish nearly instantaneously. Tune `recovery_accel_rate` for the desired recovery timescale.

**`with_injury=False`**: `new_injury = prev_injury`, `new_buffer = state.injury_buffer`, `new_rest_streak = prev_rest_streak` (all frozen, `core.py:97–100`). Any nonzero `damage > 0` triggers instant death directly at `core.py:115`. The injury death reason code (4) is not set because `new_injury` remains frozen at 0 — see FAQ.

---

## Nociception History Buffer

`core.py:102–104`

After `injury_level` is updated (whether `with_injury=True` or `False`), the new value is pushed into the front of `nociception_history_buffer`:

```python
new_nociception_history = jnp.roll(state.nociception_history_buffer, 1).at[0].set(new_injury)
```

- `jnp.roll(..., +1)`: shifts all existing entries one slot to the **right** (toward higher indices), so the oldest entry falls off the end.
- `.at[0].set(new_injury)`: places the latest `injury_level` at slot 0.
- Result: **slot 0 = most recent**, slot 1 = one step ago, slot `K-1` = oldest retained.

This buffer update runs **unconditionally** — it is not gated on `with_injury`. If `with_injury=False`, `new_injury` stays at `prev_injury` (0.0 from reset), so the buffer fills with zeros but the write still executes every step.

This buffer is the authoritative input for the interoceptive nociception sensor (doc 09), which convolves it with a discrete alpha kernel to produce a delayed, smoothed perception of internal injury.

**Shape**: `[interoceptive_kernel_length]` float32. Initialised to `jnp.zeros(interoceptive_kernel_length)` at reset (`core.py:925`).

---

## `last_collision_noc` — When It Is Set

`src/environment/core.py:497`, `core.py:652`

`last_collision_noc` is **not** updated inside `update_body`. It is set in `jax_step` (Stage 4, interaction logic) and written to the new state at `core.py:652`:

```python
# core.py:497
collision_noc = jnp.where(
    just_collided,
    jnp.max(jnp.where(at_attempted_obs, params.obs_nociception, 0.0), initial=0.0),
    0.0
)
# ... later in state._replace at core.py:652:
last_collision_noc = collision_noc,
```

`just_collided` is `True` when the agent attempted to move into a blocking obstacle and was rejected (`move_agent` returns `is_collision=True`, `core.py:29–36`). When a collision occurs, `collision_noc` is the `obs_nociception` value of the specific blocking obstacle that was hit (max over the obstacle array masked to the attempted cell). If no collision occurred this step, `last_collision_noc = 0.0`.

This value feeds the exteroceptive nociception sensor (doc 09, sensor #5) as one of four contact-based pain sources. It does **not** directly affect `injury_level` — collision damage flows through `info['damage']` → `update_body`, while `last_collision_noc` is a separate perceptual signal.

---

## Drive Computation

`calculate_drive(satiation, injury, params)` — `core.py:38–42`

Computes the agent's instantaneous homeostatic *drive* — how far its current body state is from the ideal (fully satiated, zero injury). Drive is the Euclidean distance in a 2-D space whose axes are satiation and injury; the bigger the distance, the worse the agent feels. Reward is granted when this distance shrinks between consecutive steps.

`Source: src/environment/core.py:38–42`
```python
def calculate_drive(satiation, injury, params):
    """Calculates homeostatic drive (Euclidean distance to setpoint)."""
    target = jnp.array([params.setpoint, 0.0])
    current = jnp.stack([satiation, injury], axis=-1)
    return jnp.linalg.norm(current - target, axis=-1)
```

> **API notes**
> - `jnp.stack([satiation, injury], axis=-1)` builds a length-2 vector from two scalars; `axis=-1` appends a new trailing axis so the result has the shape needed by `linalg.norm`. Under `vmap` across environments, both inputs are already rank-1 (one scalar per env), so `axis=-1` produces a `[N_envs, 2]` matrix — `norm(axis=-1)` then reduces along the last axis and returns a per-env scalar. [primer: jnp.stack](00_jax_primer.md#masking)
> - `jnp.linalg.norm(x, axis=-1)` is the L2 (Euclidean) norm — computes `sqrt(sum(x**2))` along the last axis. No `ord` argument needed; the default is the Frobenius/L2 norm. [primer: linalg](00_jax_primer.md#linalg)
> - Both satiation and injury use their raw scales (0–100 by default). The two axes are *not* normalised before taking the norm, so injury and satiation contribute equally in absolute units. The maximum possible drive is `sqrt(100^2 + 100^2) ≈ 141.4`.

```
target  = [params.setpoint, 0.0]          # ideal state: satiation AT setpoint, zero injury
current = [satiation, injury]
drive   = ||current - target||_2
        = sqrt((satiation - setpoint)^2 + injury^2)
```

Euclidean distance in a 2D homeostatic space (satiation axis, injury axis). Both axes use raw values, and the largest deviation either can show is 100 (satiation `0..200` about a setpoint of 100; injury `0..100` about 0), so the maximum possible drive is approximately `sqrt(100^2 + 100^2) ≈ 141.4`.

**Default setpoint**: `params.setpoint = 100`, which since 2026-09-22 is the **middle** of `[0, max_satiation]` (`max_satiation = 200`), not the ceiling. Satiation 50 above the setpoint costs exactly what satiation 50 below it costs — the term is squared, so its sign does not survive.

**Every axis is 100 drive units from its own death, and that is deliberate.** Satiation is 100 from the setpoint at both `N=0` (starvation) and `N=200` (over-eating); injury is 100 from zero at `max_injury`; body temperature is 100 satiation-equivalent units from the setpoint at ±15 °C, because of the exchange factor below. So all three axes weigh the same at full scale, and each one's full-scale deviation equals `death_penalty` (100). Nothing in the code enforces this — it is a property of the shipped numbers, and changing any of `max_satiation`, `satiation_setpoint`, `max_injury`, `max_temperature` or `death_penalty` breaks it.

**Inputs to `calculate_drive`**: called twice per step in `jax_step` (`core.py:560–562`) — once with the **previous** state, once with the **new** state — to compute reward as drive reduction:

```python
prev_drive = calculate_drive(state.satiation, state.injury_level, params)
curr_drive = calculate_drive(new_satiation,   new_injury,         params)
reward_homeostatic = prev_drive - curr_drive   # positive = moved toward homeostasis
```

**Logging components**: `drive_hunger` and `drive_injury` (written to `info`) are squared, normalised sub-components computed separately in `jax_step` at `core.py:556–558`:

```
drive_hunger = ((new_satiation - setpoint) / range_S)^2
drive_injury = (new_injury / max_injury)^2
```

where `range_S = max(satiation_setpoint, max_satiation - satiation_setpoint)` — the furthest
satiation can get from its own setpoint, **not** the ceiling. The two are the same number only
while the setpoint sits at the ceiling, which is how every config before 2026-09-22 was
written; at the shipped `max_satiation: 200` / `satiation_setpoint: 100` the ceiling is twice
`range_S`. `drive_hunger` used to read `(1 - new_satiation / max_satiation)^2`, which is the
same expression only in that old case — under the two-sided axis a perfectly regulated agent
would have logged 0.25 rather than 0, and an agent eating itself to death would have logged a
*falling* hunger drive.

These are for analysis logging **only** — they are not used in the reward formula. The actual reward uses the raw Euclidean drive via `calculate_drive`.

**Two axes, or three.** Everything above describes the drive with `thermal.enabled: false`,
which is every config that does not opt in. When thermal is on, `calculate_drive` takes a
fourth argument (`body_temp`) and the norm gains a temperature axis, scaled into the same
satiation units the other two already use:

```
drive = || ( satiation - setpoint,  injury,
             (T - temperature_setpoint) * range_S / max_temperature ) ||
```

The split is a **static** Python branch on `params.thermal_enabled`, and the thermal-off
side is the two-axis expression above unchanged — see
[06_reward_and_termination.md](06_reward_and_termination.md#the-third-axis--body-temperature)
for the full statement, including why the third axis is scaled *up* rather than the other
two scaled down (it is what keeps `death_penalty` calibrated). The factor is
`range_S / max_temperature`, which at the shipped numbers is **100 / 15 = 6.67** — one degree
of body-temperature deviation costs the same drive as 6.67 satiation units. That number is
unchanged by the two-sided axis, and that is the whole point of using `range_S` here: the
ceiling doubled to 200, so `max_satiation / max_temperature` would have silently doubled the
weight of temperature against hunger to 13.33 with no config saying so. `info` gains a matching
`drive_thermal = ((T - temperature_setpoint) / max_temperature)^2` — the same
squared-normalised logging convention as its two siblings, and likewise not part of the
reward — emitted only when thermal is on.

**Drive is not normalised**: raw values are used (satiation `0–200`, injury `0–100` with the shipped config). Both `drive_hunger` and `drive_injury` are dimensionless `[0, 1]` by construction — `drive_hunger` because it divides by `range_S`, which is by definition the largest deviation the axis can reach — but the reward-driving `drive` value is in the same units as the body state variables. Reconfiguring `max_satiation`, `satiation_setpoint` or `max_injury` changes the drive scale.

---

## `update_body` — Full Implementation

`update_body(state, info, params)` — `core.py:44–117`

Runs once per environment step. Takes the previous `EnvState`, an `info` dict populated earlier in `jax_step` (with keys `ate_food`, `rested`, `damage`), and `EnvParams`. Returns seven values: `(new_satiation, new_nutrition, new_injury, new_buffer, new_nociception_history, new_rest_streak, done)`.

The body below is presented as one block to show the full sequential logic: nutrition → satiation → injury + buffer → recovery → nociception history → termination.

### Chunk 1: Nutrition and Satiation update (`core.py:44–66`)

`Source: src/environment/core.py:44–66`
```python
def update_body(state: EnvState, info: dict, params: EnvParams) -> tuple[jnp.ndarray, jnp.ndarray, jnp.ndarray, jnp.ndarray, jnp.ndarray, jnp.ndarray, bool]:
    """Updates satiation, nutrition, and injury levels with streak-based recovery."""
    prev_nutrition = state.nutrition
    prev_injury = state.injury_level
    prev_rest_streak = state.rest_streak
    # --- Nutrition Dynamics (Linear Decay) ---
    if params.with_nutrition:
        # Nutrition decays linearly
        new_nutrition = prev_nutrition - params.metabolic_cost
        # Refill from food (immediate) - with consumption cost
        ate_food_gain = params.food_nutrition_gain - params.eating_nutrition_cost
        new_nutrition = jnp.where(info['ate_food'], new_nutrition + ate_food_gain, new_nutrition)
        new_nutrition = jnp.clip(new_nutrition, 0.0, params.max_nutrition)
    else:
        new_nutrition = prev_nutrition

    # --- Satiation Dynamics (Derived Non-linearly from Nutrition) ---
    if params.with_satiation:
        # Subjective fullness S = Max * (N/MaxN)^k
        fullness_ratio = jnp.clip(new_nutrition / params.max_nutrition, 0.0, 1.0)
        new_satiation = params.max_satiation * jnp.power(fullness_ratio, params.nutrition_to_satiation_scaling_factor)
    else:
        new_satiation = state.satiation
```

> **API notes**
> - The `if params.with_nutrition:` guard is a **Python-level static branch**, not a JAX traced branch — `params` is a `struct.dataclass` with `pytree_node=False` fields, so `with_nutrition` is a compile-time constant. Changing it requires recompilation. [primer: static-dynamic](00_jax_primer.md#static-dynamic)
> - `jnp.where(info['ate_food'], new_nutrition + ate_food_gain, new_nutrition)` is a **branchless select**: both branches are fully evaluated; `where` picks between them elementwise. This is the correct JAX pattern because `info['ate_food']` is a traced boolean, not a Python bool. [primer: branchless](00_jax_primer.md#branchless)
> - `jnp.clip(new_nutrition, 0.0, params.max_nutrition)` clamps the result to a fixed range without any conditional. [primer: masking / clip](00_jax_primer.md#masking)
> - `jnp.power(fullness_ratio, params.nutrition_to_satiation_scaling_factor)` raises each element to the power `k`. Here both arguments are scalars (or traced scalars under `vmap`). `jnp.power` is element-wise and differentiable — safe inside JIT and `vmap`. The exponent `k` comes from `params`, which is a static pytree leaf, so its *value* is baked in at trace time (it is still a traced float, not a Python literal, but it travels through `params` which is part of the JIT input pytree). [primer: jax-pytrees](00_jax_primer.md#jax-pytrees)

### Chunk 2: Injury accumulation + smoothing ring buffer (`core.py:68–80`)

`Source: src/environment/core.py:68–80`
```python
    # --- Injury Dynamics (Instant-start smoothing) ---
    damage = info['damage']
    if params.with_injury:
        # 1. Spread new damage across the buffer
        inc = damage / params.smoothing_duration
        temp_buffer = state.injury_buffer + inc
        
        # 2. Apply the first slice immediately
        applied_inc = temp_buffer[0]
        new_injury = prev_injury + applied_inc
        
        # 3. Shift the rest of the buffer for future steps
        new_buffer = jnp.roll(temp_buffer, -1).at[-1].set(0.0)
```

> **API notes**
> - `state.injury_buffer + inc` broadcasts the scalar `inc` across the entire ring-buffer array — every slot receives the same per-step dose. This is a pure functional operation; `state.injury_buffer` is never mutated. [primer: immutability](00_jax_primer.md#immutability)
> - `jnp.roll(temp_buffer, -1)` shifts all elements one position to the left (towards index 0), with the element at index 0 wrapping to the last slot. The negative shift direction means the front of the queue is consumed each step. [primer: masking / jnp.roll](00_jax_primer.md#masking)
> - `.at[-1].set(0.0)` writes a zero to the last (freshly vacated) slot using JAX's functional index-update syntax. This returns a **new** array — `temp_buffer` is unchanged. The combined expression `jnp.roll(...).at[-1].set(0.0)` is the canonical JAX idiom for a rotating ring buffer with a cleared tail. [primer: immutability / .at[].set()](00_jax_primer.md#immutability)

### Chunk 3: Recovery gating and rest-streak update (`core.py:82–100`)

`Source: src/environment/core.py:82–100`
```python
        # --- Recovery Dynamics (Exponential recovery based on rest streak) ---
        # Update rest streak
        new_rest_streak = jnp.where(info['rested'], prev_rest_streak + 1, 0)
        
        # Calculate exponential recovery: base * (1 + accel)^(streak-1)
        # streak 1 -> mult 1.0 (base)
        # streak 2 -> mult 1.5 (base * 1.5)
        recovery_mult = jnp.power(1.0 + params.recovery_accel_rate, (jnp.maximum(new_rest_streak, 1) - 1).astype(jnp.float32))
        recovery_amount = params.recovery_base_rate * recovery_mult
        
        # Recovery only applies if resting and not currently taking net damage
        can_recover = jnp.logical_and(info['rested'], applied_inc <= 0)
        new_injury = jnp.where(can_recover, new_injury - recovery_amount, new_injury)
        
        new_injury = jnp.clip(new_injury, 0.0, params.max_injury)
    else:
        new_injury = prev_injury
        new_buffer = state.injury_buffer
        new_rest_streak = prev_rest_streak
```

> **API notes**
> - `jnp.where(info['rested'], prev_rest_streak + 1, 0)` is another branchless select — streak increment or reset, no Python `if`. [primer: branchless](00_jax_primer.md#branchless)
> - `jnp.power(base, exponent)` computes `base ** exponent` element-wise. Here `base = 1.0 + params.recovery_accel_rate` (a scalar) and `exponent = max(streak, 1) - 1` (also a scalar, cast to float32 because integer exponents can cause type-promotion issues with some JAX backends). This is the compound rest-streak recovery formula: streak-1 is used as the exponent so that streak=1 → power=0 → multiplier=1.0 (base rate, no acceleration on the first rest step). Streak=2 → power=1 → multiplier=`1+accel`. Streak=3 → power=2 → multiplier=`(1+accel)^2`. The multiplier grows without a cap — recovery can eventually dominate max_injury in a single step; the `.clip(0, max_injury)` below prevents over-recovery. **`jnp.power` is not a primer section** — it is a standard element-wise power lifted from NumPy, safe in JIT and vmap.
> - `jnp.maximum(new_rest_streak, 1)` ensures the exponent is never negative (streak=0 would give exponent=-1, an inverse). [primer: branchless / masking](00_jax_primer.md#branchless)
> - `jnp.logical_and(info['rested'], applied_inc <= 0)` masks out recovery when buffered damage is still being absorbed — injury and recovery cannot cancel on the same step. [primer: masking](00_jax_primer.md#masking)
> - `jnp.clip(new_injury, 0.0, params.max_injury)` prevents over-subtraction (injury can't go negative) and over-accumulation (injury can't exceed `max_injury`). [primer: masking / clip](00_jax_primer.md#masking)

### Chunk 4: Nociception history buffer roll (`core.py:102–104`)

`Source: src/environment/core.py:102–104`
```python
    # Roll the perceptual history buffer and write the new injury at slot 0.
    # Buffer is non-conditional on `with_injury`: if injury never updates, slot 0 stays at prev_injury (0 from reset).
    new_nociception_history = jnp.roll(state.nociception_history_buffer, 1).at[0].set(new_injury)
```

> **API notes**
> - `jnp.roll(..., +1)` shifts **right** (toward higher indices), so the oldest entry falls off the end and slot 0 is freed for the new value. Compare with the injury buffer above which uses `roll(..., -1)` (left shift) — the two buffers use opposite shift directions because they have opposite slot-0 semantics (injury buffer: slot 0 = apply-now; nociception history: slot 0 = most-recent-write). [primer: immutability / .at[].set()](00_jax_primer.md#immutability)
> - `.at[0].set(new_injury)` functionally writes to slot 0 of the shifted array, returning a new array. The original `state.nociception_history_buffer` is never mutated. [primer: immutability](00_jax_primer.md#immutability)
> - This line runs **unconditionally** outside the `if params.with_injury` block — it is not a static branch. If `with_injury=False`, `new_injury` is just the frozen `prev_injury` (0.0 from reset), and the buffer fills with zeros, but the operation executes every step. [primer: static-dynamic](00_jax_primer.md#static-dynamic)

### Chunk 5: Termination computation and return (`core.py:106–117`)

`Source: src/environment/core.py:106–117`
```python
    # Termination check (Based on Nutrition and Injury)
    done = False
    if params.with_nutrition:
        done = jnp.where(new_nutrition <= 0.0, True, done)
        
    if params.with_injury:
        done = jnp.where(new_injury >= params.max_injury, True, done)
    else:
        # Instant death logic for levels without health system
        done = jnp.where(damage > 0, True, done)
    
    return new_satiation, new_nutrition, new_injury, new_buffer, new_nociception_history, new_rest_streak, done
```

> **API notes**
> - `done = False` initialises `done` as a Python bool. The subsequent `jnp.where(condition, True, done)` promotes it to a JAX scalar (`jnp.bool_`) on first use. Subsequent calls chain off that scalar — `jnp.where` always returns a JAX array. The final `done` returned is a 0-D `jnp.bool_` array. [primer: branchless](00_jax_primer.md#branchless)
> - The two `if params.with_nutrition:` / `if params.with_injury:` guards are again **static Python branches** — determined at compile time. Only the active termination condition is traced into the XLA computation graph. [primer: static-dynamic](00_jax_primer.md#static-dynamic)
> - `jnp.where(new_injury >= params.max_injury, True, done)` is the injury-death check — notice `>=` (inclusive). [primer: branchless](00_jax_primer.md#branchless)
> - The `else: done = jnp.where(damage > 0, True, done)` branch handles `with_injury=False` — any nonzero damage is instantly fatal regardless of injury level (which is frozen at 0). This is a design choice: injury tracking is entirely optional; disabling it makes any damage lethal to model a "no health bar" scenario.

---

## Body Temperature (thermal)

Present only when `thermal.enabled: true`. The whole block below sits behind a **static Python `if params.thermal_enabled:`** inside `update_body`, so a config with the temperature system off traces none of this arithmetic and its `body_temp` never moves off zero.

### The recurrence

$$
T_{t+1} = T_t + k_{\text{exchange}}\,(T_{\text{field}}[\text{agent cell}] - T_t) + k_{\text{metabolic}} - k_{\text{loss}}\,(T_t - T_{\text{setpoint}})
$$

That is the single-rate body, and it is exactly what runs at the shipped warming and cooling speeds of 1.0 / 1.0. In general the step on the right-hand side, call it `d_t = k_exchange·(T_field − T_t) + k_metabolic − k_loss·(T_t − T_setpoint)`, is applied scaled by one of two speed multipliers: the warming scale when the temperature is rising this step (`d_t > 0`), the cooling scale otherwise.

$$
T_{t+1} = T_t + s\,d_t, \qquad s = \begin{cases} \text{warming\_rate\_scale} & d_t > 0 \\ \text{cooling\_rate\_scale} & d_t \le 0 \end{cases}
$$

At `1.0 / 1.0` a static gate traces the single-rate lines verbatim, so the scaled branch does not exist in the compiled graph. Equal values other than 1.0 are a uniform slow-down or speed-up, not today's behaviour. Two rates are a deliberate departure from EVAAA, whose body uses one. Plan: [WARMING_COOLING_RATE_SCALES.md](../develop/active/thermal/WARMING_COOLING_RATE_SCALES.md).

| Constant | Config key | Default | What it does |
|---|---|---|---|
| `k_exchange` | `thermal.k_exchange` | 0.04 | Fraction of the gap to the cell's temperature the body closes each step — the world pulling on the body |
| `k_loss` | `thermal.k_loss` | 0.01 | Fraction of the deviation from setpoint that physiology undoes each step — the body pulling back |
| `k_metabolic` | `thermal.k_metabolic` | 0.0 | Constant heat the body produces per step. Still zero: the metabolic coupling added below runs the other way, charging nutrition for defence rather than feeding heat back into the body |
| `warming_rate_scale` | `thermal.warming_rate_scale` | 1.0 | Multiplies the whole step `d_t` when it is positive. Validated `> 0` and `warming_rate_scale·(k_exchange + k_loss) <= 1` |
| `cooling_rate_scale` | `thermal.cooling_rate_scale` | 1.0 | Multiplies the whole step `d_t` when it is zero or negative. Validated `> 0` and `cooling_rate_scale·(k_exchange + k_loss) <= 1` |
| `temperature_setpoint` | `thermal.temperature_setpoint` | 0.0 | The temperature the body is trying to hold |
| `min_temperature` / `max_temperature` | `thermal.min_temperature` / `.max_temperature` | −15 / +15 | Survivable band; leaving it ends the episode with code 5 |

`T_field[agent cell]` is read at the **post-move** cell — the one the agent stepped into this step, not the one it left — matching every other quantity `update_body` consumes (`damage`, `ate_food`, `rested`).

### The tug-of-war reading

The two coefficients are pulling in opposite directions, and the balance between them is the whole mechanic. Setting `T_{t+1} = T_t` gives the fixed point

$$
T^{*} = \frac{k_{\text{exchange}}\,T_{\text{field}} + k_{\text{loss}}\,T_{\text{setpoint}} + k_{\text{metabolic}}}{k_{\text{exchange}} + k_{\text{loss}}}
$$

which at the defaults is `0.8 · T_field`. **The warming and cooling scales do not appear in it**: they multiply the whole step, and a scaled step is zero exactly where the unscaled one is, so every cell has the same single settling temperature whichever direction the body arrives from. **Standing in a −25 cell settles the body at −20, not at −25**: physiology holds off 20% of the cold. That 20% is what creates a cold-but-survivable band — a world whose baseline is −25 does not kill an agent outright, so the agent can leave the fire and come back.

Delete `k_loss` and the code still *looks* correct: the body still tracks the world and still freezes in a cold enough cell. But the fixed point becomes `T_field` exactly, the survivable-ambient window collapses to `[min_temperature, max_temperature]`, and the entire cold-but-survivable band disappears. This is the failure mode `tests/env/test_thermal_body.py::test_equilibrium_and_time_to_death` exists to catch.

The gap to the fixed point shrinks by `(1 − s·(k_exchange + k_loss))` per step, with `s` the scale for the direction of travel; the time constant is `1/(s·(k_exchange + k_loss))`, 20 steps at 1.0, against a 500-step episode. Because each scale is validated so that `s·(k_exchange + k_loss) <= 1`, a step never overshoots the fixed point, the direction of travel never flips while the agent stays in one cell, and the approach stays monotone. "Warming" follows the direction of the step, not whether the body is cold: a body at −2 in a −10 cell (fixed point −8) is cooling, and a body standing on the fire is warming, **so a warming scale above 1 also makes the fire kill sooner**, and a cooling scale below 1 also slows recovery from overheating.

`k_loss` is in the [critical-settings registry](CONFIG_CRITICAL_SETTINGS.md) for a reason: at roughly `k_loss = 0.036` the survivable ambient window widens past ±25, the world's own baseline can no longer kill anything, and the thermal task quietly disappears while still appearing to be configured.

### Metabolic coupling (thermal)

Off by default (`thermal.metabolic_coupling: false`), and every config in the repo ships
it off. When it is switched on, defending body temperature stops being free: nutrition is
drained each step in proportion to the thermoregulatory work.

```
thermal_drain = metabolic_coupling_rate * |k_loss * (T_t - temperature_setpoint)|
```

| Symbol | Config key | Default | Meaning |
|---|---|---|---|
| `metabolic_coupling` | `thermal.metabolic_coupling` | false | Gate. A **static** Python `if` in `update_body`, so with it off the drain contributes nothing to the traced graph |
| `metabolic_coupling_rate` | `thermal.metabolic_coupling_rate` | 1.0 (unread while the gate is off) | Nutrition units drawn per degree-per-step of defence. Validated `>= 0` |

**What it charges for, and why that quantity.** The body's recurrence carries
`- k_loss*(T - temperature_setpoint)`: the degrees per step that physiology actively
undoes to pull the body back to setpoint — shivering in the cold, sweating in the heat.
That term *is* the defence, so its magnitude is the work, and the work is what costs
energy. Two near-misses are wrong for the same reason. Charging on `|T - setpoint|`
alone bills the agent for a deviation even when `k_loss` is 0 and the body is doing no
defending at all. Charging on the net temperature change bills for passive exchange with
the cell, which is heat moving on its own rather than the body spending anything to move
it.

**Which `T`.** The *pre*-step body temperature — exactly the `T` that appears in this
step's `k_loss` term — so the nutrition charged on step `t` pays for the defence
performed on step `t` (exactly at 1.0 / 1.0; with other warming / cooling scales the
applied defence is `scale × k_loss·(T − setpoint)`, and the bill is a per-decision charge
for the defence effort rather than for the temperature change it produced — see "Not
scaled by the warming / cooling speeds" below).

**Not scaled by the warming / cooling speeds.** The drain above is charged the same way whatever `warming_rate_scale` and `cooling_rate_scale` are. The obvious alternative, multiplying the bill by the scale for the direction the body moved this step, fails at rest. The temperature field does not change within an episode, so a body that has settled in one cell recomputes the same step every turn, and at that settled point whether the tiny leftover step counts as "warming" or "cooling" is decided by floating-point rounding: usually frozen at the direction the body arrived from, occasionally alternating. The defence term `k_loss·(T − setpoint)` is not zero there. A direction-scaled bill would therefore depend on history or jitter: two settled bodies 1.6e-5 degrees apart could pay bills that differ by the whole warming/cooling ratio. The unscaled bill is a continuous function of the body's state. It is a per-step (per-decision) cost, which equals a per-degree-moved cost only at 1.0 / 1.0. One consequence: with a warming scale above 1, a full rewarm takes fewer steps and so costs less total nutrition. This is defensible but not the only defensible choice. Two alternatives are deferred to the review of the whole thermal block (OPEN_WORK_HANDOFF E1(a)): a time-dilation reading (bill × scale) and a switch on the direction of the *defence* term, `sign(setpoint − T)`, which is zero at the setpoint and so has no path dependence. Pinned by `tests/env/test_thermal_rate_scales.py::test_metabolic_drain_is_not_scaled`.

**Symmetric.** The `k_loss` term is signed (it pushes both ways); the energy bill is not,
hence the absolute value. Defending against heat costs the same as defending against an
equal amount of cold.

**Ordering.** The drain sits between the linear decay and the food refill, before the one
clip — see [Nutrition Dynamics](#nutrition-dynamics) above for why that matters.

Proved a no-op while off by `tests/env/test_metabolic_coupling.py::test_off_by_default_is_a_provable_noop`,
against a fixture captured from source that predates the feature.

### Death

`thermal_death = (T_{t+1} < min_temperature) OR (T_{t+1} > max_temperature)`, folded into `update_body`'s `done` return **inside `update_body`** — which is what makes it a *real death* rather than merely an episode end. `jax_step` captures `real_death` from that return value before it merges truncation in, so the `death_penalty` applies. Termination code 5 is assigned separately, after the truncation line, so a thermal death on the final step reports 5 rather than 1. See [06_reward_and_termination.md](06_reward_and_termination.md).

---

## Metabolic Cost

`metabolic_cost` (default 1.0) is deducted from nutrition every step, unconditionally — it applies even when the agent is resting (`core.py:52`). Resting does not pause metabolism; it only activates injury recovery.

---

## Body State Flags Summary

| Flag | Disabled Effect |
|------|----------------|
| `with_nutrition=False` | No decay, no gain, no starvation; nutrition frozen at start value (`core.py:57–58`) |
| `with_satiation=False` | Satiation frozen at reset-derived value; excluded from drive changes (`core.py:65–66`) |
| `with_injury=False` | Injury and injury_buffer frozen; `rest_streak` frozen; any `damage > 0` → instant death (`core.py:97–100, 115`) |

All three flags are static (`pytree_node=False` in `EnvParams`), so changing them requires recompilation.

**Note**: `nociception_history_buffer` updates are **not gated** by `with_injury`. The buffer rolls unconditionally each step; if `with_injury=False`, it fills with the frozen `prev_injury` value (0.0 from reset).

---

## Clarifications / FAQ

**Q: Does `overeating_death=True` actually kill the agent?**
A: **Yes, since 2026-09-22**, and it is the shipped default. `update_body` sets `done=True` when `new_nutrition >= max_nutrition`, under a static Python gate on the flag, and `jax_step` stamps `termination_reason=3` from the *same* predicate. Because `done` is captured before the truncation merge, the `death_penalty` fires — the episode ends exactly the way starvation ends it.

> **This answer used to say "No — latent bug", and that was correct at the time.** The key set `reason=3` from `new_satiation >= max_satiation` and never touched `done`, so an agent at full satiation carried a "died of over-eating" label on live steps while the episode carried on. Both halves were fixed together: the label now reads the same nutrition predicate that ends the episode, so a reason-3 step is structurally always a terminal step. Regression tests in `tests/env/test_two_sided_nutrition.py`.

**Q: What is `applied_inc` exactly and why does it gate recovery?**
A: `applied_inc = temp_buffer[0]` is the front of the ring buffer **after** this step's damage has been added (`core.py:73–76`). If the agent took damage on this step, then `inc > 0` → `applied_inc > 0` → `can_recover=False`. The gate `applied_inc <= 0` prevents recovery from cancelling fresh pain — resting through a predator attack still leaves you hurt.

**Q: Does `rest_streak` reset to 0 if the agent takes damage while resting?**
A: No — the streak check is purely on the action (`info['rested']`), not on damage. `new_rest_streak = prev + 1 if rested else 0` (`core.py:84`). A rest-and-take-damage step **extends the streak** but skips recovery (because `applied_inc > 0`). On the next step with no new damage absorbed, full streak-multiplied recovery resumes.

**Q: Does `recovery_mult` use the old or new rest_streak?**
A: The **new** (already incremented) streak (`core.py:89`). On the very first resting step, `new_rest_streak=1`, `recovery_mult = (1+accel)^0 = 1.0` — the base rate. On the second consecutive rest step, `new_rest_streak=2`, `recovery_mult = 1+accel`.

**Q: What happens with `smoothing_duration=1`?**
A: Damage is applied in full on the step it's taken. `inc = damage / 1 = damage`, `applied_inc = damage`, the buffer tail slot is zeroed after the roll. Effectively disables smoothing. Use this for deterministic "one-shot impact" style tasks.

**Q: If I set `food_nutrition_gain = eating_nutrition_cost`, what happens?**
A: `ate_food_gain = 0`, so eating has no effect on nutrition — but `ate_food=True` still fires (lifecycle update consumes the resource, reward may include `+1` in survival mode minus `eating_reward_penalty`). Useful when food acquisition is a reward signal divorced from energy.

**Q: Can nutrition go negative?**
A: No — `clip(..., 0.0, max_nutrition)` at `core.py:56` clamps it. Starvation death fires at `new_nutrition <= 0`, which includes exactly 0.

**Q: Does `metabolic_cost` apply when resting?**
A: Yes. Rest does NOT pause metabolism (`core.py:52` deducts unconditionally). Rest only enables injury recovery.

**Q: What if damage comes from multiple sources in one step?**
A: All damage is summed into `info['damage']` before `update_body` sees it (`core.py:499` aggregates `damage_res + damage_pred + damage_obs_overlap + damage_obs_collision`). The buffer receives the total spread across `smoothing_duration` slots. There is no per-source tracking in the buffer.

**Q: Is the buffer applied before or after recovery each step?**
A: Damage is applied first (`new_injury = prev_injury + applied_inc` at `core.py:77`), then recovery subtracts (`core.py:94`) only if `can_recover`. Net effect: `new_injury = prev_injury + applied_inc - (rested AND applied_inc<=0 ? recovery : 0)`, then clamped to `[0, max_injury]`.

**Q: What's `state.satiation` when `with_satiation=False` at reset?**
A: It's still computed via the power-law from nutrition at reset (`core.py:915–916`). The flag only prevents re-derivation at *step* time — reset always initialises satiation from nutrition regardless.

**Q: What's the termination_reason when `with_injury=False` and damage kills the agent?**
A: The reason code stays at `0` (active) or `1` (truncated) because `reason = jnp.where(new_injury >= params.max_injury, 4, reason)` fires against the frozen `new_injury = prev_injury` (0.0). The episode ends (`done=True` from `core.py:115`) but the reason code is misleading. This is a minor labelling inconsistency.

**Q: Is `calculate_drive` always 2D (satiation + injury) regardless of `with_*` flags?**
A: Yes. `calculate_drive` doesn't inspect the flags; it always takes `(satiation, injury)` and computes distance to `(setpoint, 0)`. If `with_satiation=False`, satiation is frozen at its reset value — drive changes only with injury.

**Q: Does the reward ever become very large in a single step?**
A: Yes at termination: `reward = drive_delta - death_penalty`. With `death_penalty=100` (default) the terminal step typically carries a large negative reward. The drive itself can jump up to ~141 on the death step, but the penalty dominates. Some algorithms (Dreamer-style) are sensitive to this spike — consider scaling `death_penalty` when reward variance matters.

**Q: Setpoint defaults — is it always `max_satiation`?**
A: **No, not since 2026-09-22.** `configs/environment/default.yaml` ships `satiation_setpoint: 100` with `max_satiation: 200`, so the setpoint is the middle of the range and partial fullness *is* the ideal. It was the ceiling in every config written before that date, which is why so much of the code and these docs used `max_satiation` where they meant "the furthest satiation can be from target" — see `range_S` above. A setpoint at the ceiling is still a legal config and every such world behaves bit-for-bit as it did.

**Q: Can `nutrition_to_satiation_scaling_factor = 0` work?**
A: `fullness_ratio^0 = 1` for all positive fullness, so `new_satiation = max_satiation` always. Not useful. The formula is undefined for `k<0` when `nutrition=0` (0^negative), so keep `k > 0`.

**Q: What random ranges apply at reset for nutrition and injury?**
A: `random_start_nutrition=True` → `uniform[max_nutrition/2, max_nutrition]` (`core.py:910–911`). `random_start_injury=True` → `uniform[0, max_injury/2]` (`core.py:919–920`). Both use independent sub-keys split from `body_key` at `core.py:907`.

**Q: Is there a cap on `recovery_mult`?**
A: No hard cap. At `recovery_accel_rate=0.5` and streak 20, recovery ≈ 222 per step. The injury clamp at 0 prevents over-recovery, but long rest streaks make injury vanish very quickly. Tune `recovery_accel_rate` for the desired recovery timescale.

**Q: Does `last_collision_noc` affect injury?**
A: No. `last_collision_noc` is a perceptual signal only — it feeds the exteroceptive nociception sensor (doc 09). Collision damage flows via `info['damage']` into `update_body` and accumulates in `injury_level`. The two are independent; you can have a collision that causes damage (if `obs_damage > 0`) and also sets `last_collision_noc` (if `obs_nociception > 0`), or configure either to be zero.
