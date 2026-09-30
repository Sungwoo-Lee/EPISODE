# 06 — Reward & Termination

> **Source**: `src/environment/core.py` (reward: lines 550–571; termination codes: lines 534–548; termination from body: lines 106–116) | **Back to hub**: [ENVIRONMENT_SUMMARY](ENVIRONMENT_SUMMARY.md)

---

## Plain-language entry point

This document describes **how the environment scores the agent** and **when an episode ends**.

The environment offers two reward modes, selected once at config time:

- **Survival reward** (`use_homeostatic_reward=False`): sparse, food-only signal. The agent gets `+1` every time it eats food and `-death_penalty` when the episode ends. No continuous feedback about the internal body state — the agent must learn to seek food without being told it is hungry.
- **Homeostatic reward** (`use_homeostatic_reward=True`): dense, drive-reduction signal. Every step, the agent is rewarded for moving *closer to homeostasis* (less hungry, less injured) and penalised for moving further away. Death still adds an additional penalty.

**Performance is always measured in survival steps** (how long the agent stays alive), never cumulative reward. Reward shapes learning; survival steps measure success.

An episode can end in five ways (termination codes 1–5), or keep running (code 0). The integer code is in `info['termination_reason']` each step for logging.

---

## Reward — Survival Mode

**Mode**: `params.use_homeostatic_reward = False`

```python
# core.py:566–567
reward_extrinsic = jnp.where(ate_food, 1.0, 0.0)
reward_extrinsic = jnp.where(done, -params.death_penalty, reward_extrinsic)
```

**Important**: the `done` branch *replaces* the entire `reward_extrinsic` with `-params.death_penalty`. It does not subtract from an existing value. If food was eaten on the same terminal step, the `+1.0` is discarded — the terminal step yields exactly `-death_penalty` (before the eating penalty, see below).

The final combined reward (same formula applies in both modes):

```python
# core.py:569–571
reward = reward_homeostatic + reward_extrinsic
# Apply eating penalty whenever food was eaten (both modes)
reward = jnp.where(ate_food, reward - params.eating_reward_penalty, reward)
```

In survival mode, `reward_homeostatic` is always `0.0`, so:

```
reward = reward_extrinsic - (eating_reward_penalty  if ate_food else 0)
```

Typical per-step values:
- Alive, no food: `0.0`
- Alive, ate food: `1.0 - eating_reward_penalty`
- Terminal step (death or truncation): `-death_penalty` (eating penalty still applies if food was eaten on that step)

### Full reward block — verbatim

Both reward modes live in the same function and share the combined-reward tail; they are shown together so you can see the full static-flag tracing pattern in one read.

`Source: src/environment/core.py:550–571`

```python
    # 6. Reward (Homeostatic driven by Satiation)
    reward_homeostatic = 0.0
    reward_extrinsic = 0.0
    
    # Calculate components for analysis
    # drive_hunger = ((satiation - setpoint)/range_S)^2 ; drive_injury = (injury/max_injury)^2
    _range_S = satiation_deviation_range(params)
    drive_hunger = jnp.power(
        (new_satiation / _range_S) - (params.setpoint / _range_S), 2)
    drive_injury = jnp.power(new_injury / params.max_injury, 2)
    
    if params.use_homeostatic_reward:
        prev_drive = calculate_drive(state.satiation, state.injury_level, params)
        curr_drive = calculate_drive(new_satiation, new_injury, params)
        reward_homeostatic = prev_drive - curr_drive
        # Death penalty based on Nutrition starvation
        reward_homeostatic = jnp.where(done, reward_homeostatic - params.death_penalty, reward_homeostatic)
    else:
        reward_extrinsic = jnp.where(ate_food, 1.0, 0.0)
        reward_extrinsic = jnp.where(done, -params.death_penalty, reward_extrinsic)
    
    reward = reward_homeostatic + reward_extrinsic
    # Apply eating penalty if ate food
    reward = jnp.where(ate_food, reward - params.eating_reward_penalty, reward)
```

> **API notes**
>
> - **Static flag / Python `if`**: `if params.use_homeostatic_reward:` is a compile-time branch, not a runtime conditional. `use_homeostatic_reward` is declared `struct.field(pytree_node=False)`, so JIT treats it as a Python constant and traces **only one branch**. Changing the flag forces a full recompile. The same applies to `with_nutrition`, `with_injury`, and `overeating_death` throughout this file. See [primer: static vs. dynamic](00_jax_primer.md#static-dynamic).
> - **Branchless `jnp.where`**: every `reward = jnp.where(condition, x, y)` inside the traced path evaluates **both** `x` and `y` at every step; the condition selects the result without branching the execution graph. This is what makes the death penalty expressible as arithmetic rather than an `if done:` guard. See [primer: branchless](00_jax_primer.md#branchless).
> - **`reward_homeostatic = 0.0` / `reward_extrinsic = 0.0`** initialised as Python scalars. The `jnp.where` on each branch returns a JAX scalar array. The final addition is safe because NumPy broadcasting promotes `0.0` — but the *inactive* variable is never a traced zero, so its shape/dtype is invisible to JAX’s checker until the `+`. In practice this is harmless for scalar reward.
> - **`drive_hunger` / `drive_injury`** (and `drive_thermal` when `thermal.enabled`): normalised squared components, logging only. They approximate the per-axis contribution to drive for analysis scripts but are **not** fed into `reward_homeostatic`. The actual reward uses the Euclidean norm in `calculate_drive`. See [Reward — Homeostatic Mode](#reward--homeostatic-mode) below.

---

## Reward — Homeostatic Mode

**Mode**: `params.use_homeostatic_reward = True`

Dense drive-reduction reward based on `calculate_drive`:

```python
# core.py:38–42
def calculate_drive(satiation, injury, params):
    target  = jnp.array([params.setpoint, 0.0])
    current = jnp.stack([satiation, injury], axis=-1)
    return jnp.linalg.norm(current - target, axis=-1)
# i.e.: sqrt((satiation - setpoint)^2 + injury^2)
```

Per-step reward:

```python
# core.py:560–564
prev_drive = calculate_drive(state.satiation, state.injury_level, params)
curr_drive = calculate_drive(new_satiation, new_injury, params)
reward_homeostatic = prev_drive - curr_drive
# Death penalty applied on any terminal step (done=True):
reward_homeostatic = jnp.where(done, reward_homeostatic - params.death_penalty, reward_homeostatic)
```

Unlike survival mode, the death penalty here is **subtracted from** (not replaces) the existing drive-reduction term. The terminal step reward is:

```
reward_homeostatic_terminal = (prev_drive - curr_drive) - death_penalty
```

The eating penalty then applies on top if food was eaten:

```
reward = reward_homeostatic - (eating_reward_penalty  if ate_food else 0)
```

**Sign convention**: `reward_homeostatic > 0` means drive decreased (agent moved toward homeostasis — less hungry, less injured). `reward_homeostatic < 0` means drive increased (more hungry, more injured, or terminal step).

**Units**: drive is in the same units as `satiation` and `injury` (satiation ranges 0–200 about a setpoint of 100; injury 0–100 about 0, with the shipped defaults). What bounds the drive is each axis's largest possible **deviation from its own target**, which is 100 on both, so the theoretical per-step maximum magnitude is `sqrt(100^2 + 100^2) ≈ 141` — unchanged by the 2026-09-22 ceiling move, because the setpoint moved to the middle at the same time. A typical satiation gain from eating might produce a drive-change of ~5–20; severe injury can produce a per-step penalty of 30+.

**Zero drive is reachable, and reaching it is the job**: `calculate_drive` measures distance from `[setpoint, 0]`, not from `[max_satiation, 0]`. At `satiation == setpoint` and `injury == 0` the drive is **exactly 0** — the shipped world's `satiation_setpoint: 100` is an interior point of `[0, 200]`, reachable from either side, and an agent sitting on it is paid nothing further because there is nothing left to correct. (An earlier revision of this paragraph claimed a strictly positive residual drive whenever `setpoint < max_satiation`. That was wrong: what `setpoint < max_satiation` means is that a *completely full* agent is off-target, not that an *on-target* one is.)

The genuinely pathological case is a setpoint **outside** the axis. If `setpoint > max_satiation`, satiation is clipped below the target and the drive can never reach zero — the agent is punished forever for a state it cannot leave. Since 2026-09-22 the loader refuses that at load time (`0 <= satiation_setpoint <= max_satiation`), along with a zero-width axis, which would make the deviation scale `range_S` zero and turn the logged `drive_hunger` into a NaN inside the jitted step.

**Note on logged drive components** (`drive_hunger`, `drive_injury` in `info`): these are normalised squared terms computed separately for logging only — they are **not** used to compute `reward_homeostatic`:

```python
# core.py  (info only, not part of reward)
_range_S = satiation_deviation_range(params)          # max(setpoint, max_satiation - setpoint)
drive_hunger = ((new_satiation / _range_S) - (params.setpoint / _range_S)) ** 2
drive_injury = (new_injury / params.max_injury) ** 2
```

`drive_hunger` is **two-sided about the setpoint** since 2026-09-22 and divides by `range_S`,
the furthest satiation can get from its target — not by the ceiling. It previously read
`(1 − satiation/max_satiation)²`, which is the same expression only while the setpoint *is*
the ceiling; under the two-sided axis that old form would log **0.25** for a perfectly
regulated agent instead of 0, and a *falling* hunger drive for an agent eating itself to
death. It is written as a difference of two quotients rather than the tidier
`((S − setpoint)/range_S)²` on purpose: dividing first makes `setpoint/range_S` exactly 1.0 at
a ceiling setpoint, so the term is the exact IEEE negation of the old one and byte-identical
after squaring. The tidier form is up to 2 ULP off on roughly half of all satiation values,
which would cost `tests/env/test_metabolic_coupling.py`'s byte-parity fixture its meaning.

When `thermal.enabled` is true a third one joins them, `drive_thermal`, on the **same**
squared-normalised convention — `((body_temp - temperature_setpoint) / max_temperature) ** 2`
— so the three logged series stay comparable with each other and with historical runs. It
is emitted **only** when thermal is on (`max_temperature` is the inert `0.0` on a
thermal-off config), so read it with `.get`.

### The third axis — body temperature

With `thermal.enabled: true` the drive gains a temperature axis and becomes

```
drive = || ( satiation - setpoint,  injury,
             (T - temperature_setpoint) * range_S / max_temperature ) ||

where  range_S = max(satiation_setpoint, max_satiation - satiation_setpoint)
```

**Why the third axis is scaled up rather than the other two scaled down.** The design
document writes the three-axis drive normalised per axis — each term divided by its own
range — the satiation axis by `range_S`, its own largest possible deviation from target.
Written literally that is today's drive divided by `range_S` (100), so **every reward in the
project** would shrink 100-fold while `death_penalty` stayed at 100: the death penalty would
go from comparable-to-a-few-steps to overwhelming, on thermal-**off** configs as much as
thermal-on ones. Multiplying the whole expression through by `range_S` gives the
algebraically identical drive in today's units — the first two axes untouched, the
temperature axis scaled by `range_S / max_temperature`. See the temperature plan's finding F1.

At the shipped values (`range_S = 100`, `max_temperature: 15`) that factor is
**100/15 = 6.67**: one degree of body-temperature deviation costs the same drive as 6.67
satiation units. `thermal.max_temperature` is therefore the warmth-vs-hunger exchange rate
as well as the edge of the survivable band — see
[CONFIG_CRITICAL_SETTINGS.md](CONFIG_CRITICAL_SETTINGS.md).

**The numerator is `range_S`, not `max_satiation`, and the difference has teeth since
2026-09-22.** The two are the same number only while the setpoint sits at the ceiling, which
is how every config written before that date looked. The shipped world now has
`max_satiation: 200` with `satiation_setpoint: 100`, so `range_S` is 100 while the ceiling is
200: the old expression would have weighed one degree at **200/15 = 13.33** satiation units,
doubling the value of staying warm relative to staying fed with no config key recording the
change. Using `range_S` keeps the exchange factor at 6.67, the same number every thermal run
to date has used, and is a bit-for-bit no-op for every pre-2026-09-22 config.

**All three axes weigh the same at full scale, by construction of the shipped numbers.**
Satiation is 100 from target at both of its lethal ends (`N=0` and `N=200`), injury is 100
from target at `max_injury`, and temperature is 100 satiation-equivalent units from target at
±15 °C because of the 6.67 factor. Each axis's full-scale deviation therefore equals
`death_penalty` (100). Nothing enforces this in code — change any of `max_satiation`,
`satiation_setpoint`, `max_injury`, `max_temperature` or `death_penalty` and it stops holding.

Both call sites pass a temperature from the same state transition the satiation and injury
arguments come from: `state.body_temp` for `prev_drive`, the post-step temperature for
`curr_drive`. `body_temp` is **required** when thermal is on — `calculate_drive` raises
`ValueError` rather than defaulting to the setpoint, because a forgotten call site would
otherwise look exactly like a perfectly comfortable agent.

### `calculate_drive` — verbatim

`calculate_drive` is the single function that defines what “homeostasis” means numerically. It is called twice per step (before and after the body update); the difference is the reward signal.

`Source: src/environment/core.py::calculate_drive` (docstring elided)

```python
def calculate_drive(satiation, injury, params, body_temp=None):
    """Calculates homeostatic drive (Euclidean distance to setpoint)."""
    if params.thermal_enabled:
        t_axis = (body_temp - params.temperature_setpoint) * (
            satiation_deviation_range(params) / params.max_temperature)
        target = jnp.array([params.setpoint, 0.0, 0.0])
        current = jnp.stack([satiation, injury, t_axis], axis=-1)
        return jnp.linalg.norm(current - target, axis=-1)
    # ── thermal OFF: the pre-thermal expression, untouched ────────────────────
    target = jnp.array([params.setpoint, 0.0])
    current = jnp.stack([satiation, injury], axis=-1)
    return jnp.linalg.norm(current - target, axis=-1)
```

`params.thermal_enabled` is `struct.field(pytree_node=False)`, so this is a **compile-time**
branch: a thermal-off config traces only the two-axis expression, which is the pre-thermal
one character for character. That is why the reward on every existing config is
bit-identical rather than merely close, and it is checked against pre-change fixtures by
`tests/env/test_thermal_parity.py` and
`tests/env/test_thermal_reward_gate.py::test_drive_bit_identical_when_thermal_off`.

> **API notes**
>
> - **`jnp.stack([satiation, injury], axis=-1)`**: stacks two scalars into a 1-D array `[satiation, injury]`. When called under `vmap` (parallel envs), both `satiation` and `injury` are shape-`[num_envs]` vectors; `stack(..., axis=-1)` then produces shape `[num_envs, 2]`. The norm along `axis=-1` is correct in both cases, so the function is naturally vmap-composable without modification. See [primer: vmap](00_jax_primer.md#vmap).
> - **`jnp.linalg.norm(..., axis=-1)`**: Euclidean (L2) distance from the homeostatic setpoint `[params.setpoint, 0.0]`. Default `ord=2`. See [primer: linalg](00_jax_primer.md#linalg).
> - **Why L2, not L1 or squared?** L2 penalises large simultaneous hunger+injury more than the sum of independent penalties would. It is differentiable everywhere except at the setpoint (drive = 0), which is rarely hit in practice.
> - **`params.setpoint`** is a static field. Its value is baked into the compiled graph; changing it at runtime requires a recompile. See [primer: static vs. dynamic](00_jax_primer.md#static-dynamic).

---

## Combined Reward Formula (Both Modes)

```python
# core.py:569–571
reward = reward_homeostatic + reward_extrinsic   # exactly one is nonzero per mode
reward = jnp.where(ate_food, reward - params.eating_reward_penalty, reward)
```

The `info` dict always carries both `reward_homeostatic` and `reward_extrinsic`, even when one is `0.0`, to keep logging scripts mode-agnostic.

### Eating reward penalty

`params.eating_reward_penalty` (default `0.0`) is deducted whenever `ate_food = True`, in **both** modes. Setting it to a small positive value (e.g. `0.1–1.0`) discourages the agent from spamming the eat action when hunger is already satisfied. It affects only the reward signal — the actual body nutrition update (`food_nutrition_gain`, `eating_nutrition_cost`) is independent.

### Death penalty

`params.death_penalty` (default `100`) is applied on any terminal step (`done = True`), whether death is from starvation, injury, or `max_steps` truncation.

- In **survival mode**: replaces `reward_extrinsic` with `-death_penalty` (the step’s food-eat bonus is lost).
- In **homeostatic mode**: subtracted from the drive-change term (the drive change from the final body update is still included).

FAQ: Is the death penalty also applied on truncation? **Yes.** `done = done_from_body OR truncated` (core.py:548), so any `done=True` triggers the penalty regardless of cause. If you want truncation to be reward-neutral, set `death_penalty=0`.

---

## Termination Codes

`info['termination_reason']` is an `int32` scalar set every step. The `EnvState.terminated` field stores the boolean `done` flag (not the integer code).

| Code | Name | Trigger condition | `done`? | Notes |
|------|------|-----------------|---------|-------|
| 0 | Active | — (default) | No | Episode is running normally |
| 1 | Truncated | `(state.current_step + 1) >= params.max_steps` | Yes | Standard episode length limit |
| 2 | Starvation | `new_nutrition <= 0.0` — or, with B3 `healing_nutrition_shortfall: partial`, the `starved` predicate returned by `update_body` (nutrition **before** the healing charge `<= 0`) | Yes (via `update_body`) | Guarded on `params.with_nutrition` in `jax_step` since `8334d89` (2026-07-23) — see note below. **B3 partial (2026-09-26):** starvation is judged before the healing charge, so the charge never kills; `jax_step` reads the SAME returned predicate for the label as `update_body` used for `done` (static selection). In B3 `full` mode the predicate is today's, after the charge |
| 3 | Overeating | `new_nutrition >= params.max_nutrition` | Yes (via `update_body`) | Only set if `params.overeating_death=True`. **Changed 2026-09-22**: this used to be `new_satiation >= max_satiation` and set the label WITHOUT ever setting `done` — a no-op recorded as a latent bug from 2026-06-09. Both the label and `done` now read the same nutrition predicate under the same static gate, so a reason-3 label without a death is structurally impossible. |
| 4 | Injury | `new_injury >= params.max_injury` | Yes (via `update_body`) | No `with_injury` guard in `jax_step` — see note below |
| 5 | Thermal | `new_body_temp` outside `[params.min_temperature, params.max_temperature]` | Yes (via `update_body`) | Only set if `params.thermal_enabled=True`; the body-temperature recurrence is in [05_body_homeostasis.md](05_body_homeostasis.md). Reused unchanged by the 2026-09-26 body mechanics (B1 random start, B4 injury-boosted heat exchange) — no new code |
| 6 | Dehydration | `new_hydration <= 0.0` — the `dehydrated` predicate `update_body` returns in `water_out` | Yes (via `update_body`) | Only set if `params.water_enabled=True` (2026-09-30, [[thirst_water_plan]]). Stamped AFTER thermal's 5, so on a step that is both a thermal and a thirst death the label is the water one; `done` is the same either way. A water-off world has no hydration and can never produce it |
| 7 | Over-drinking | `new_hydration >= params.water_max_hydration` — the `overdrank` predicate from `water_out` | Yes (via `update_body`) | Only set if `params.water_enabled=True`. Mutually exclusive with 6 (one value cannot be at both ends). Same one-predicate rule as over-eating: the label and `done` read the same returned value, so a label without a death is structurally impossible |

**Nutrition is a two-sided axis (since 2026-09-22).** It runs 0–200 with the homeostatic
setpoint at **100**, the middle, so BOTH ends are lethal and symmetric: code 2 at
`new_nutrition <= 0` (starved) and code 3 at `new_nutrition >= max_nutrition` (overfed). The
drive rises as the agent moves away from 100 in *either* direction, so eating while already at
the setpoint is punished by the ordinary reward without any special case — measured at −4.0 for
an eat that moves nutrition 100 → 104, against +4.0 for the same eat at 50.

The old code-3 predicate was written against *satiation*, which is derived and clipped
(`satiation = max_satiation · (nutrition/max_nutrition)^k`), so `satiation >= max_satiation`
was true on every step where nutrition merely sat at its ceiling — routine after a feed. That
is why the label appeared on ordinary non-terminal steps. Keying both the label and `done` to
nutrition removes that.

**Priority** (highest code wins): `5 > 4 > 3 > 2 > 1 > 0`. Codes are applied via sequential `jnp.where` — later checks overwrite earlier ones:

```python
# core.py:540–545
reason = jnp.array(0, dtype=jnp.int32)
reason = jnp.where(truncated,                              1, reason)   # lowest priority
reason = jnp.where(new_nutrition <= 0.0,                   2, reason)   # B3 partial: where(starved, 2, reason)
if params.overeating_death:
    reason = jnp.where(new_nutrition >= params.max_nutrition, 3, reason)
reason = jnp.where(new_injury >= params.max_injury,        4, reason)
if params.thermal_enabled:
    reason = jnp.where(thermal_death,                      5, reason)   # highest priority
```

If starvation and truncation both fire in the same step, `reason=2` wins (starvation overwrites truncation). If injury and starvation both fire, `reason=4` wins. A thermal death that lands on the last step of the episode reports 5, not 1 — which is the whole reason the thermal assignment sits after the truncation line rather than before it.

### Full termination block — verbatim

The truncation check, priority-chain termination codes, `done` assembly, and where they appear in the step function, all in one place.

`Source: src/environment/core.py:534–548`

```python
    # Max Steps Truncation
    next_step = state.current_step + 1
    truncated = next_step >= params.max_steps
    
    # Termination Reason (Integer codes for JIT compatibility)
    # 0: active, 1: max_steps, 2: starvation, 3: overeating, 4: injury, 5: thermal
    reason = jnp.array(0, dtype=jnp.int32)
    reason = jnp.where(truncated, 1, reason)
    if params.with_nutrition:
        if starved is not None:          # B3 partial: update_body's returned predicate
            reason = jnp.where(starved, 2, reason)
        else:
            reason = jnp.where(new_nutrition <= 0.0, 2, reason)
        if params.overeating_death:
            reason = jnp.where(new_nutrition >= params.max_nutrition, 3, reason)
    reason = jnp.where(new_injury >= params.max_injury, 4, reason)
    if params.thermal_enabled:
        reason = jnp.where(thermal_death, 5, reason)
    
    info['termination_reason'] = reason
    done = jnp.logical_or(done, truncated)
```

(Comments abridged; `starved` is the tenth element of `update_body`'s return and is `None`
except in B3 `partial` mode — [05_body_homeostasis.md](05_body_homeostasis.md).)

> **API notes**
>
> - **Priority chain via sequential `jnp.where`**: each `reason = jnp.where(cond, new_code, reason)` overwrites `reason` when `cond` is true. Later calls have higher priority because they can overwrite earlier ones. Code 5 (thermal) is last, so it wins any simultaneous multi-condition step; with the temperature system off, code 4 (injury) is last. This is the standard JAX idiom for priority selection without branching. See [primer: branchless](00_jax_primer.md#branchless).
> - **`if params.overeating_death:`** — Python-level static branch, and it now sits **inside** the `if params.with_nutrition:` guard, so a nutrition-disabled world cannot stamp a food-related death code. When `overeating_death=False` the JIT-compiled graph contains no `jnp.where` for code 3 at all, and `update_body`'s matching `done` branch emits nothing either — measured as exactly two fewer equations in `update_body`'s jaxpr, the `>=` and the `where` (`tests/env/test_two_sided_nutrition.py`). This is a claim about those two branches only: `satiation_deviation_range` runs on the drive and diagnostic paths for every config, so the step graph as a whole did grow on 2026-09-22 even where the numbers are bit-identical. See [primer: static vs. dynamic](00_jax_primer.md#static-dynamic).
> - **`jnp.array(0, dtype=jnp.int32)`**: explicitly typed to `int32`. Without this, JAX defaults to `int32` on most platforms anyway, but the explicit dtype prevents a subtle shape-mismatch if `jnp.where` returns a different default integer type on a particular accelerator.
> - **`done = jnp.logical_or(done, truncated)`**: `done` on the right-hand side is `done_from_body`, the boolean returned by `update_body`. `truncated` is a traced boolean from the step-count comparison. `logical_or` is branchless and vmap-safe. See [primer: masking](00_jax_primer.md#masking).
> - **`params.max_steps`** is a static field. `truncated` is computed from `next_step >= params.max_steps`; the threshold is baked at compile time. See [primer: static vs. dynamic](00_jax_primer.md#static-dynamic).

### Termination from `update_body` — linked

The `done_from_body` value that feeds into the `logical_or` above is set inside `update_body` at `core.py:106–116`. Its full logic (nutrition death, injury threshold death, instant-damage death when `with_injury=False`) is owned by doc 05. The relevant excerpt:

`Source: src/environment/core.py:106–116`

```python
    # Termination check (Based on Nutrition and Injury)
    done = False
    if params.with_nutrition:
        done = jnp.where(new_nutrition <= 0.0, True, done)
        if params.overeating_death:
            done = jnp.where(new_nutrition >= params.max_nutrition, True, done)

    if params.with_injury:
        done = jnp.where(new_injury >= params.max_injury, True, done)
    else:
        # Instant death logic for levels without health system
        done = jnp.where(damage > 0, True, done)
    
```

> **API notes**
>
> - **Two static flags, up to four compiled variants**: `with_nutrition` and `with_injury` are both `struct.field(pytree_node=False)`. Each combination is a separate compiled specialisation of `update_body`. The `else` branch (`with_injury=False`, instant damage death) is compiled in only when `with_injury=False`. See [primer: static vs. dynamic](00_jax_primer.md#static-dynamic).
> - **`done = False`** starts as a Python bool. The first `jnp.where` that fires promotes it to a JAX boolean scalar. The `logical_or` in `jax_step` (line 548) then combines it with `truncated`, another JAX boolean. This promotion chain is standard JAX and safe.
> - **Structural redundancy**: `done_from_body` is set by nutrition/injury thresholds inside `update_body`, but `reason` codes 2 and 4 are set by independent `jnp.where` checks in `jax_step` against the same thresholds. They are logically redundant but structurally independent — a change to one does not automatically update the other. This is the source of the `with_nutrition` / `with_injury` mismatch bugs documented below.

### Code 3 / over-eating: a real death (since 2026-09-22)

`reason=3` **does** end the episode. `update_body` folds `new_nutrition >= max_nutrition` into
`done` under the same static `overeating_death` gate and inside the same `with_nutrition`
guard that the reason-3 label uses, so the label and the death are one predicate: a reason-3
step is always a terminal step, and `real_death` — captured in `jax_step` *before* the
truncation merge — picks it up, so the `death_penalty` fires exactly as it does for
starvation.

> **This section used to say "informational only", and that was accurate at the time.** Until
> 2026-09-22 the reason-3 branch stamped a label from `new_satiation >= max_satiation` while
> `done` had no over-eating branch at all. Because satiation is derived from nutrition and
> clipped, that predicate was true on *every* step where nutrition merely sat at its ceiling
> — routine after a feed — so live, surviving steps carried a "died of over-eating" label.
> Recorded in KNOWN_BUGS as part of "Env doc-audit latent findings" (open 2026-06-09) and
> pinned now by `tests/env/test_two_sided_nutrition.py`.

### `with_nutrition=False` and the starvation code

**Fixed 2026-07-23 (`8334d89`); this section records the defect and its repair.** The
starvation check `reason = jnp.where(new_nutrition <= 0.0, 2, reason)` originally had **no
guard for `with_nutrition`**. When `with_nutrition=False`, `update_body` keeps nutrition
frozen at its reset value (`start_nutrition`) and never decays it, so a config with
`start_nutrition = 0.0` stamped `reason=2` on every step even though `update_body` never set
`done=True` for starvation — `done` was unaffected, but `termination_reason` read 2
spuriously. Both food-axis codes now sit inside `if params.with_nutrition:` in `jax_step`
(code 2, and code 3 nested under it since 2026-09-22), so a nutrition-disabled world cannot
report a food-related death at all. The injury-side counterpart below is **not** fixed.

### `with_injury=False` and the injury code

Similarly, `core.py:545` has no `with_injury` guard. When `with_injury=False`, `new_injury` stays frozen at its reset value. If the reset value is `0.0` and `max_injury > 0`, the check never fires. However, damage *does* still terminate the episode via `update_body`’s instant-death branch (`done = jnp.where(damage > 0, True, done)` — core.py:115). In that case, `new_injury` never reaches `max_injury`, so `reason` will be `1` (truncation) or `0` — **not** `4`. The claim that code 4 fires for `with_injury=False` damage-deaths is incorrect.

---

## `done` Flag Assembly

```python
# core.py:548
done = jnp.logical_or(done, truncated)
```

Where `done` on the left is `done_from_body` returned by `update_body` (covers starvation and injury thresholds), and `truncated = (next_step >= params.max_steps)`.

`done` is returned as the third element of `jax_step` and stored in `state.terminated` (bool). The integer reason code is in `info['termination_reason']` only.

### Truncation vs body-death distinction

There is no separate truncation boolean in the step output. To distinguish truncation from body-death downstream, read `info['termination_reason']`: code `1` means pure truncation; codes `2` or `4` mean body death (noting that starvation+truncation on the same step reports `2`, not `1`).

---

## Death Conditions Summary

| Condition | `with_*` guard in `jax_step`? | `done=True` source | `reason` code |
|-----------|------------------------------|-------------------|--------------|
| `new_nutrition <= 0.0` | No (body does; `jax_step` does not) | `update_body` line 109 | 2 |
| `new_injury >= params.max_injury` | No (body does; `jax_step` does not) | `update_body` line 112 | 4 |
| `damage > 0` when `with_injury=False` | `with_injury=False` branch in `update_body` | `update_body` line 115 | 1 or 0 (not 4) |
| `next_step >= params.max_steps` | — | `jax_step` (truncated) | 1 |
| `new_nutrition >= params.max_nutrition` (overeating_death=True) | `params.with_nutrition` **and** `params.overeating_death` | `update_body` (same predicate) | 3 |
| `new_hydration <= 0.0` | `params.water_enabled` (static) | `update_body` (returned `dehydrated`) | 6 |
| `new_hydration >= params.water_max_hydration` | `params.water_enabled` (static) | `update_body` (returned `overdrank`) | 7 |

**Water adds a fourth drive axis** when `water_enabled`: `calculate_drive` appends
`(hydration − water_hydration_setpoint) · range_S / range_W` with
`range_W = max(setpoint, max_hydration − setpoint)` (100 at the shipped 100 / 200), in a static
branch placed before the thermal one, so every water-off world keeps the pre-water drive
verbatim. The reward pairs PRE-step hydration in the previous drive with POST-step hydration
in the current one, like every other axis. `info['drive_thirst']` is the squared normalised
deviation (divide-first, like `drive_hunger`) and exists only when water is on.

---

## Clarifications / FAQ

**Q: Does `overeating_death=True` actually terminate the episode?**
A: **Yes, since 2026-09-22**, and it is the shipped default. `update_body` sets `done=True` at `new_nutrition >= max_nutrition`, and `jax_step` stamps reason 3 from that same predicate, so the two cannot disagree. The death penalty fires. Before that date the answer was "no" — the label was set and `done` never was; see "Code 3 / over-eating" above.

**Q: When multiple termination conditions fire in the same step, which code wins?**
A: The highest-priority code by the `jnp.where` ordering: `5 > 4 > 3 > 2 > 1 > 0` (code 5, thermal, exists only when `thermal.enabled`). Example: starvation and truncation on the same step → `reason=2` (starvation overwrites truncation). Injury and starvation → `reason=4`.

**Q: Is the death penalty applied on truncation?**
A: Yes. `done = done_from_body OR truncated`, so truncation yields `done=True` and triggers the penalty in both reward modes. Set `death_penalty=0` for a truncation-neutral setup.

**Q: What is the reward on the very last step when no food was eaten (survival mode)?**
A: `reward = -death_penalty`. The `done` branch in `core.py:567` replaces `reward_extrinsic` entirely with `-death_penalty`.

**Q: What is the reward on a step where food is eaten AND the episode ends (survival mode)?**
A: `reward = -death_penalty - eating_reward_penalty`. The `+1.0` food bonus is discarded because the `done` branch replaces `reward_extrinsic` before the eating penalty is applied.

**Q: In homeostatic mode, what is the terminal step reward?**
A: `(prev_drive - curr_drive) - death_penalty - (eating_reward_penalty if ate_food else 0)`. Unlike survival mode, the drive-change term is retained and the penalty is additive.

**Q: Why do `reward_homeostatic` and `reward_extrinsic` both appear in the info dict?**
A: For logging separability — both are always written regardless of mode. In survival mode, `reward_homeostatic=0.0` every step; in homeostatic mode, `reward_extrinsic=0.0`. This lets a single analysis script handle both modes without mode-checking.

**Q: Does the reward sign tell me whether the agent is succeeding?**
A: Only in homeostatic mode, where `reward > 0` iff drive decreased this step. In survival mode, `reward ∈ {0, 1} - eating_reward_penalty` during the episode and `= -death_penalty` on termination.

**Q: How does `eating_reward_penalty` interact with `food_nutrition_gain`?**
A: Independently. `eating_reward_penalty` affects only the reward signal; `food_nutrition_gain` and `eating_nutrition_cost` affect the actual body state. You can configure eating as body-beneficial but reward-penalised.

**Q: Can I use homeostatic reward without injury (`with_injury=False`)?**
A: Yes. When `with_injury=False`, `new_injury` stays frozen at its reset value (typically `0.0`). Drive degenerates to `|satiation - setpoint|`. Reward depends only on satiation changes.

**Q: What's the reward shape?**
A: Scalar (`[]`). Single float per step. `ParallelEnv` wraps it to shape `[num_envs]` via vmap.

**Q: What's the bound on reward magnitude?**
A: Not strictly bounded. In homeostatic mode, the per-step drive change is bounded by the largest possible deviation on each axis, `sqrt(range_S^2 + max_injury^2) ≈ 141` with defaults (`range_S = 100`, `max_injury = 100`). Terminal step adds `-death_penalty`. Practical range: `[-(death_penalty + 141), +141]`. Survival mode: `[-death_penalty, 1.0]` per step (minus `eating_reward_penalty`).

**Q: Is reward clipped inside the environment?**
A: No. Apply clipping in the training loop if your algorithm requires it.

**Q: Does `info['termination_reason']` reliably indicate the true episode-ending cause?**
A: Mostly, with these caveats:
- `overeating_death=True` → reason=3 **and** a real termination (since 2026-09-22; before that the label appeared on surviving steps).
- `with_injury=False` → damage-triggered death produces reason=0 or 1, not 4.
- `with_nutrition=False` and `start_nutrition=0.0` → reason=2 every step (spurious) — **fixed 2026-07-23**, both food codes are now guarded on `with_nutrition`.
Prefer checking `done` for the actual termination signal; use `reason` for diagnostic labelling.
