---
title: "Four body mechanics that make the best action depend on combinations of internal states (level 05)"
topic: sensors
status: active
created: 2026-09-26
last_updated: 2026-09-26
aliases: [state_dependent_body_mechanics]
---

# Four body mechanics that make the best action depend on combinations of internal states (level 05)

> **Status**: PLANNED (awaiting `plan-reviewer`, then user approval of the open decisions in §Open decisions)
> **Opened**: 2026-09-26
> **Related**: [[INJURY_DEPENDENCE_PLAN]] (the analysis that motivated this) · [[WARMING_COOLING_RATE_SCALES]] (the fixture-from-a-pre-change-worktree precedent, and the body-temperature recurrence) · [[BUSH_REFUGE_AND_LOCATION_DEPENDENT_RECOVERY]] (the precedent for a static-gated body key and its roll-out cost) · [[SAVED_RUN_CONFIG_COMPAT]] (old-run loading; read, not edited — another session owns it) · [[recovery_in_bush_tuning]] · [[IMPLEMENTATION_PLAN]] (thermal)

---

## Context

The project is making the campfire world — curriculum level 05, a cold 10×10 grid with one to three campfires, where the agent must keep three body quantities near their comfortable values (how full it is, how injured it is, and its body temperature) — the main world for studying whether a neuromodulated agent's behaviour depends on its internal state. A recent analysis found that, in both the modulated and the unmodulated agent, the response to injury is a simple habit that ignores everything else: healing is fast and costs nothing (five injury points per step while resting in a bush), so "injured → go to a bush and rest" is always right, whatever the agent's hunger or temperature.

This plan adds four mechanics that change the **consequences** of actions on the body, so that the best action depends on **combinations** of internal states. The reward formula is untouched.

- **B1**: each episode starts at a random body temperature, not always at the comfortable value.
- **B2**: healing slows when the body is far from its comfortable temperature, so a cold injured agent must warm up before resting pays off.
- **B3**: healing costs food energy, so a hungry injured agent must choose between eating and healing.
- **B4**: injury makes the body lose heat faster, so an injured agent freezes sooner away from a fire.

Each mechanic has an exact "off" value at which the environment behaves exactly as today, byte for byte. That claim is tested against rollouts recorded from the current code before the change.

---

## Analysis

### A0 — Wiki pull gate and known bugs

Read the `config_system` and `env_entities` folders of the LLM Wiki. Four entries bear on this plan:

- `20260622_1746_start_injury_dead_needs_random_range`: `body.start_injury` is never read, and a fixed non-zero start needs a random range with `low == high`. **B1 does not add a fixed-value key at all**, so it cannot recreate that dead key. A pinned start temperature is written as flag on with `low == high`, and a unit test pins that this works (T-B1-2).
- `20260909_1402_parity_gates_green_without_comparing`: a parity gate must **fail**, not skip, when its fixture, config or backend is missing. §File Changes → parity test carries that requirement.
- `20260820_1606_reset_ulp_divergence_is_compiler_fusion`: two compilations can differ by one float32 ULP. The no-change test is pinned to CPU on both sides, and also compares the jaxpr, so it does not rely on rollout equality alone.
- `20260901_1528_interoceptive_channel_is_two_dims_by_design`: injury and nutrition are **not observed** at level 05 (`sensory.injury_observable: false`, `nutrition_observable: false`). B2/B3 couple hidden states. That is a question for the experiment design (can the agent infer the combination from nociception and its own history?), not a defect here. Flagged for `experiment-designer`.

Known bugs (from `bug-curator`, supplied with the task) and how each is handled:

| Known bug | Handling in this plan |
|---|---|
| `start_satiation` / `start_injury` inert unless the random range is used | B1 has no fixed-start key. Pinning = flag + `low == high`; T-B1-2 asserts the exact value. The default range is the degenerate `[setpoint, setpoint]`, so switching only the flag on reproduces today's start. |
| Termination-reason codes untrustworthy when a body system is disabled (`core.py:1010`, the ungated `new_injury >= max_injury → 4` line) | B3 **refuses to load** unless `with_nutrition` and `with_injury` are both true. B3 and B4 add **no new reason code and no new predicate**: a B3 starvation reaches reason 2 through the existing clipped-nutrition test, and a B4 freeze reaches reason 5 through the existing `thermal_death`. |
| 227/265 standalone configs already fail to load; each new mandatory key extends this (accepted policy) | Stated with measured numbers in §A6. Archived worlds are not migrated. The only exceptions are the archived files that are **live test inputs**, following the 2026-09-15 precedent (§A6). |
| `tests/env/test_backward_compat_configs.py` skips every `basic/` world because it does not resolve `extends:` | The no-change test loads `basic/05` and `basic/04` through `load_env_config` → `load_env_params` (the resolving loader the trainer uses). |
| Render-audit fixtures rejected by the thermal structure check (`config_loader.py:682-701`) | B1's start range does **not** enter the structure check (the check is about settle temperatures, not starting ones). B4 extends the check **only when its gain is non-zero**. At the inert 0.0 the check is literally the same code path, so no fixture that passes today can start failing. |
| `tests/env/test_thermal_reward_gate.py` reference data must be regenerated if `calculate_drive` changes | `calculate_drive` is **not touched**. That test must pass unchanged; regenerating its data is forbidden in this change (Checkpoint CP9). |
| Interoceptive nociception buffer zeroed at reset (`core.py:1112` area) | Kept. B1 changes only `body_temp` at reset. |
| Nutrition two-sided 0–200, setpoint 100 (`379ec8fc`) | B3 charges before the single clip, so the over-eating ceiling test and the starvation floor test both read the post-charge value (§A3). |

### A1 — Where things are today (code as truth, HEAD of `v4.0`, 2026-09-26)

**Level 05 resolved through the real loader** (`load_env_config` → `load_env_params` on the level-05 campfire world config): recovery base 0.2/step, compounding 0.0, bush multiplier 25.0, so healing is **5.0 injury points per rest step in a bush** and 0.2 in the open. Metabolic cost 1.0/step. Nutrition range [0, 200], setpoint 100, over-eating death on. Random start nutrition [0, 200], random start injury [0, 100]. Thermal: setpoint 0.0, death outside [-15, +15], `k_exchange` 0.04, `k_loss` 0.02, `k_metabolic` 0.0, warming scale 2.0, cooling scale 0.25, metabolic coupling off, world baseline sampled from [-31, -29], fire = 11 × |baseline|.

Settle temperatures at the level-05 values, from the loader's own `_thermal_radial_equilibria`, at baseline −30: fire cell +51.4 (lethal), ring one cell out **+5.75** (survivable; the ring cell itself is +8.6°), three cells out −19.7 (lethal). Away from a fire the body cools from 0 to −15 in **92 steps**. Leaving the ring at +5.8, it takes 17 steps to reach 0, 36 to reach −5 and 63 to reach −10. Rewarming from −14 at the ring takes 10 steps.

**The update order inside `core.py::update_body` (lines 155–422):**

1. Nutrition (183–255): decay `− metabolic_cost` → thermal drain A1 (`thermal.metabolic_coupling`, static gate, 245–249, billed on the **pre-step** body temperature) → add food → **one clip** to [0, max_nutrition] (253).
2. Satiation derived from the clipped nutrition (258–263).
3. Injury (265–323): damage slice from the smoothing buffer → rest streak → `recovery_amount = base·(1+accel)^(streak−1)` → bush premium (static gate on `recovery_in_bush_multiplier != 1.0`, 309–313) → `can_recover = rested ∧ applied_inc ≤ 0` → subtract → clip [0, max_injury].
4. Death: `new_nutrition <= 0` / `>= max_nutrition` (gated) / `new_injury >= max_injury` (330–358).
5. Body temperature (373–420), static on `thermal_enabled`, then static on `warming == cooling == 1.0`. Recurrence `T ← T + s·[k_ex·(T_cell − T) + k_met − k_loss·(T − T_set)]`.

**Consequence for B3:** nutrition is finalised (clipped, and satiation derived from it) **before** the injury block computes how much was healed. B3 therefore has to move the clip and the satiation derivation behind the injury block. §Design D3 does this with static branches so the off path is unchanged.

**Reset (`core.py:1775`):** `body_key1, body_key2, body_key3 = jax.random.split(body_key, 3)`. `body_key2` draws nutrition and `body_key3` draws injury. **`body_key1` is split and never used.** B1 draws from `body_key1`. That touches no existing stream: switching B1 on changes nothing about positions, nutrition, injury, properties or `state.key`, and switching it off leaves the reset graph identical. `body_temp` is set at `core.py:2064` to `params.temperature_setpoint`.

**Loader:** the thermal body constants are conditional-mandatory under `thermal.enabled` (`config_loader.py:1523–1621`), with inert literals in the `else` arm (1647–1672). The rate-scale bound `scale·(k_ex + k_loss) ≤ 1` is at 1571–1591. The structure check `_check_thermal_structure` is at 530–706 and is called from inside the thermal-on arm. The body start ranges follow the "flag → conditional-mandatory range, else sentinel" pattern at 2154–2209. `recovery_in_bush_multiplier` is unconditional-mandatory and `float()`-coerced because it is a static field (2211–2233).

### A2 — B4: the task wording names the wrong coefficient, so B4 scales `k_exchange`, not `k_loss`

The task says "the `k_loss` term grows with injury". In this code `k_loss` is **not** heat loss. It is the body's **defence**: the fraction of the deviation from the setpoint that physiology undoes each step (loader message at `config_loader.py:1551`: "the per-step fraction of the deviation from setpoint that physiology undoes"; `core.py:365–370`). Raising `k_loss` with injury would pull an injured body **closer** to its setpoint, so injury would protect against the cold. That is the opposite of the intent.

The coefficient that sets how fast the body loses heat to a cold cell is `k_exchange`. B4 therefore scales `k_exchange` with injury:

$$
k_{ex}^{\text{eff}} = k_{ex}\,\Bigl(1 + g\,\frac{I}{I_{\max}}\Bigr),\qquad g \ge 0,\quad I \in [0, I_{\max}]
$$

- **Off value:** `g = 0.0`, exactly (static gate; the code keeps using `params.thermal_k_exchange` itself).
- **Bounds:** the factor lies in [1, 1+g]. It is monotone increasing in injury.
- **Effect on settle points:** `T* = (k_ex^eff·T_cell + k_loss·T_set + k_met)/(k_ex^eff + k_loss)`, which moves toward the cell's temperature as injury rises. The derivative with respect to `k_ex^eff` has a sign that does not depend on `k_ex^eff`, so settle points are monotone in injury. Checking injury 0 and injury max is therefore enough (used in §Design D4).
- **Symmetric by construction:** next to a fire an injured body also warms faster (ring settle +5.75 → +6.9 at g = 1 and full injury; the ring cell is +8.6°, so it can never exceed that). A cold-only variant is Open decision D-B4.
- **A1 drain unaffected:** the metabolic-coupling bill is `rate·|k_loss·(T − T_set)|` and does not involve `k_exchange`.

Level-05 numbers (cell −30, cooling scale 0.25):

| g | injury 0 | injury 50 | injury 100 |
|---|---|---|---|
| steps from 0 °C to freezing (< −15) | 92 / 92 / 92 at g = 0 | 55 at g = 1 | 39 at g = 1 |
| g = 0.5 | 92 | 69 | 55 |
| g = 2 | 92 | 39 | 25 |
| settle temperature, g = 1 | −20.0 | −22.5 | −24.0 |
| first step from 0 °C, g = 1 | −0.30 | −0.45 | −0.60 |

**The stability bound that B4 can break.** The loader enforces `k_ex + k_loss ≤ 1` and `scale·(k_ex + k_loss) ≤ 1` for each scale. With B4 the effective sum is largest at full injury: `k_ex·(1+g) + k_loss`. At level 05 the binding case is the warming scale 2.0: `2.0·(0.04·(1+g) + 0.02) ≤ 1` ⇒ **g ≤ 11**. Nothing plausible is near that. The loader must still check the full-injury value (D4), because another world (or a later retune) could break it.

**Structure check.** At g = 1 and g = 2 and full injury, the level-05 profile stays certified (d0 +61.7 / +66.1 still lethal, d1 +6.9 / +7.4 survivable, d3 −23.7 / −25.3 lethal). D4 evaluates the check at both ends of the injury range when g > 0.

### A3 — B3 ordering, and its interaction with the two lethal ends of nutrition

"Healed" must mean **injury points actually removed by recovery this step**, not the nominal `recovery_amount`:

- At injury 3 with a nominal 5-point heal, the clip at 0 removes only 3. The agent is charged for 3.
- At injury 0 nothing is healed and nothing is charged.
- **Pitfall:** on a step where damage pushes injury past `max_injury`, the upper clip also lowers injury. That is not healing. Using `injury_before − injury_after` without the `can_recover` mask would charge for it. The formula is therefore masked: `healed = where(can_recover, max(injury_after_damage − injury_after_clip, 0), 0)`. Under `can_recover`, `applied_inc ≤ 0`, so the upper clip cannot fire. T-B3-5 pins this.

**Order (proposed, pinned in code comments and in `05_body_homeostasis.md`):**

1. linear decay `− metabolic_cost`
2. A1 thermal drain (if on)
3. food refill (if ate)
4. **B3 healing charge `− c · healed`** (new; `healed` comes from the injury block, which runs before this step when B3 is on)
5. **one** clip to [0, max_nutrition]
6. satiation derived from the clipped value

This keeps the existing invariant, "exactly one clip, after every debit and credit", which is what lets the termination tests read the clipped value:

- **Starvation:** a heal that costs more than the agent has lands on exactly 0.0, sets `done` through the existing `new_nutrition <= 0.0` line, and is labelled reason 2 through the existing jax_step predicate. Nothing new is added. So **healing can starve an agent**. That is the intended trade-off. The alternative, capping healing by available energy, is Open decision D-B3.
- **Over-eating:** charged before the clip, so a step that both eats up to the ceiling and heals is tested against the ceiling **after** paying for the heal. This can only happen in auto-eat worlds (`eat_action_enabled: false`), where standing on food and resting coincide. At level 05 eating and resting are separate actions (4 = rest, 5 = eat), so they never coincide. T-B3-6 pins the auto-eat case.

B3 needs `with_injury` (to heal) and `with_nutrition` (to pay). The loader refuses `c > 0` otherwise, so B3 cannot create another "label without the system" instance of the `core.py:1010` bug.

B3 and B2 compose multiplicatively and without special handling: the charge is per point healed, so a B2-slowed heal costs proportionally less per step.

Level-05 numbers (B2 off, in a bush, resting, no damage, 5 points healed per step):

| c | extra nutrition per heal step | cost of a full 100-point heal | full heal as a share of the 0–200 range |
|---|---|---|---|
| 0.5 | 2.5 | 50 | 25 % |
| 1.0 | 5.0 | 100 | 50 % |

Each rest step also pays the ordinary 1.0 metabolic cost.

### A4 — B2 functional form

$$
w(T) = \max\bigl(0,\; 1 - s\,\lvert T - T_{set}\rvert\bigr),\qquad \text{recovery} \leftarrow \text{recovery}\cdot w(T)
$$

- `s ≥ 0` is the fraction of healing lost per degree of deviation (unit 1/°C). **Off value `s = 0.0` exactly** (static gate; the branch is not traced).
- **Bounded** in [0, 1]: healing can be slowed or stopped, never reversed and never boosted.
- **Monotone** decreasing in |T − T_set|. Healing reaches zero at |ΔT| = 1/s.
- The multiplier applies to `recovery_amount` after the bush premium, so it inherits the rest-and-no-net-damage condition, exactly as the bush premium does.
- It uses the **pre-step** body temperature (`state.body_temp`). The body update runs later in `update_body`, and the A1 drain already bills on the pre-step temperature, so this keeps one convention for "the body's state at the start of the step drives this step's physiology". It also avoids reordering the function.

Healing per rest step in a bush at level 05 (base 5.0/step):

| body temp | s = 1/15 (healing stops at the death threshold) | s = 0.1 (healing stops at ±10°) |
|---|---|---|
| 0 | 5.00 | 5.00 |
| −5 | 3.33 | 2.50 |
| −10 | 1.67 | 0.00 |
| −15 | 0.00 | 0.00 |
| +6 (ring beside a fire) | 3.00 | 2.00 |

**The +6 row is the reason for Open decision D-B2.** The task specifies "closeness to the setpoint", which is symmetric. The warm spot next to a fire, where a body settles, is about +5.8°, so a symmetric form **slows healing at the fire**. That arguably contradicts "healing needs warmth". A cold-only form, `max(0, 1 − s·max(0, T_set − T))`, heals at full speed at the ring. Either is a one-line difference in the same static branch. The plan implements the symmetric form (the task's wording) unless the user picks otherwise.

### A5 — B1 key placement and the random draw

Keys live under `thermal:`, next to `temperature_setpoint` / `min_temperature` / `max_temperature`, and are conditional-mandatory under `thermal.enabled`. This mirrors both existing patterns:

- body-temperature constants are read only when thermal is on;
- the injury start pattern is flag → range conditional-mandatory → sentinel otherwise.

Validation: `min_temperature ≤ low ≤ high ≤ max_temperature`, finite. This is the same closed-interval shape as `start_injury_low/high` (a start exactly on the boundary is survivable, because death is strictly outside it). The draw is `jax.random.uniform(body_key1, (), minval=low, maxval=high)`. With `low == high` JAX's uniform returns exactly `low` (`u·0 + low`), and T-B1-2 pins that.

**Proposed level-05 range [−10, +5] (Open decision D-B1).** Reasoning at level-05 values:

- The upper end stays below the ring's settle temperature (+5.75), so an agent that spawns beside a fire and steps onto it survives the first step, as the 2026-09-19 calibration target requires: 5 + 2.0·(0.04·(79.7 − 5) − 0.02·5) = +10.8, below +15. From +10 it would be +14.96, a knife-edge.
- The lower end leaves 46 steps before freezing at the coldest cell, and fewer than 10 steps to rewarm at a ring.

**Consequence the user already accepted:** Wave 2 level-05 runs stop being a like-for-like baseline. **Also:** the sensory-noise world (level 06) `extends:` level 05, so **level 06 inherits B1 as well** (Open decision D-L06).

### A6 — Roll-out cost of the new mandatory keys (measured, 2026-09-26)

**Thermal-conditional keys (B1, B2, B4).** These are read only when `thermal.enabled`. The raw-loaded thermal-on inputs are:

- `configs/environment/default.yaml` (thermal off by default; carries the keys for inheritance);
- two **archived test inputs**, `configs/environment/experiment/archive/thermal/campfire_world.yaml` and `campfire_world_body_temp_hidden.yaml`. These are loaded from a raw `Config` by nine `tests/env/test_thermal_*` / `test_metabolic_coupling` / `test_thermoception` / `test_body_temperature_observation` / `test_dashboard_layout` modules and by `scripts/fixtures/generate_{metabolic_coupling,thermal_rate_scale}_fixture.py`.

The 2026-09-17 warming/cooling change added its keys inline to both archived files (lines 357–360 of `campfire_world.yaml`), and the 2026-09-15 bush change did the same for 29 archived test inputs. That precedent is followed: **these are live test inputs, not a migration of the archive.**

The `basic/` worlds inherit through `extends:`.

**Unconditional key (B3, `body.healing_nutrition_cost`).** This has the same roll-out population as `body.recovery_in_bush_multiplier` on 2026-09-15:

- every non-archive file that carries `recovery_in_bush_multiplier` today: 36 files by `grep -rl recovery_in_bush_multiplier configs tests | grep -v experiment/archive` (default.yaml, 5 `configs/continual/nmn_double_return_stages/*`, 6 `configs/verification/*`, about 24 test modules and fixture YAMLs with inline `body:` blocks);
- the frozen world `tests/env/fixtures/frozen_parity_worlds/environment__default.yaml`, with the same "ADDED AFTER THE FREEZE, inert" comment block its line 225 uses;
- every archived file that carries the inline `recovery_in_bush_multiplier` line **and** is loaded by a test. The developer finds this set by the same grep restricted to `experiment/archive` intersected with the paths referenced under `tests/` and `scripts/fixtures/`.

**Accepted breakage, to be measured and stated in the change log.** Archived configs that are not test inputs are not migrated. The developer re-runs the 2026-09-15 before/after count ("resolve every config under `experiment/archive/` through `load_env_config` → `load_env_params`") and records the numbers. The expectation is that nearly every archived world that still loads today stops loading, because B3 is unconditional.

### A7 — Old level-05 checkpoints: what breaks, measured on real saved configs

Evaluation, replay and trajectory collection rebuild the world from the run's **own frozen copy**, `results/<algo>/<run>/models/config.yaml`, never from `configs/`. The call sites (`collect_trajectories.py:699–727`, `eval_rollout.py:959/1007`, `scripts/analysis/nmn/replay.py:82`, `trajectory_glm.py:54`, `supplementary/parity.py`) are enumerated in [[SAVED_RUN_CONFIG_COMPAT]] §A4.

Verified today on `results/JAX_RecurrentPPO/20260922-182534_rppo_bq2cover_lvl05_t1none_s42/models/config.yaml`: it is fully resolved (no `extends:`), carries `thermal.enabled: true` and `recovery_in_bush_multiplier: 25.0`, and `load_env_params(Config(yaml))` succeeds at HEAD.

When this plan lands without a compatibility step:

| New key | Saved configs that stop loading | Which |
|---|---|---|
| `thermal.random_start_body_temp` / `healing_temperature_sensitivity` / `injury_heat_exchange_gain` (thermal-conditional) | **12** of the 45 saved configs written since 2026-09-14 | The 8 Wave 1 + Wave 2 level-05 / level-06 runs (`20260921-1148*/1149*`, `20260922-18253*/18254*`) and 4 render-audit / smoke runs |
| `body.healing_nutrition_cost` (unconditional) | **every** saved config, including all 36 of the 45 recent ones that load today | All of Wave 1 and Wave 2 (28 runs), plus every other currently rebuildable run |

The error is `Strict Config: Configuration key '<key>' is required but missing.`

**This collides with in-flight work.** `configs/trajectory_collection/basicq2_wave1.yaml` (untracked, another session) collects trajectory stores for all 14 Wave 1 runs from their saved configs. If this plan's keys land before that collection (and any Wave 2 collection) finishes, a resume dies at config load. See Open decision D-COMPAT.

**Proposed route, consistent with [[SAVED_RUN_CONFIG_COMPAT]] (which is PLANNED, not implemented — `src/environment/saved_config_compat.py` does not exist yet):** add these keys to that plan's `_ERA_KEYS` table (its §File Changes) at their inert values, each justified by the static branch that makes it inert. This plan's no-change test is the parity instrument that table demands ("A value here is a CLAIM ABOUT WHAT THE OLD CODE DID and must name the branch that makes it true").

| Key | Era value | Justification |
|---|---|---|
| `thermal.random_start_body_temp` | `False` | `jax_reset` static branch; start at setpoint |
| `thermal.healing_temperature_sensitivity` | `0.0` | `update_body` static gate |
| `thermal.injury_heat_exchange_gain` | `0.0` | `update_body` static gate |
| `body.healing_nutrition_cost` | `0.0` | `update_body` static gate |

- The range keys need no entry: they are read only when the flag is true.
- One design point for that plan's owner: the three thermal-conditional keys should be supplied only when the (possibly supplied) `thermal.enabled` is true. Supplying them into a thermal-off config is harmless but inflates the logged "supplied" list, and also the store fingerprint (its §A10).
- **This plan does not edit that document or implement that module.** The hand-off is a message to its owner (or a signed appended "Feedback from `senior-developer`" block once that session has finished editing it).

Without fallback defaults and without that layer, the only other correct way to analyse an old run after this lands is to run the analysis tool from a **git worktree of a pre-change commit**. That works today and needs no code.

### A8 — Termination reason and per-step drive terms (requirement 5)

| Quantity | Trainer / WandB | Trajectory store (Parquet) | Eval recordings (`.rec.gz`) |
|---|---|---|---|
| Termination reason | ✅ `Episode/Term_{MaxSteps,Starvation,Overeating,Injury,Thermal}` one-hot (`src/behavior/episode_metrics.py`) | ✅ per-episode and per-step `termination_reason` (`trajectory_store.py:140,172`) | ✅ |
| Satiation, nutrition, injury (state at t) | — | ✅ columns | ✅ |
| **Body temperature (state at t)** | — | ❌ **no column** | ✅ `snap['body_temp']` (`eval_recording.py:66`) |
| Per-axis drive terms | — | ❌ (not stored; `info['drive_hunger' / 'drive_injury' / 'drive_thermal']` exist in `jax_step` but no consumer records them) | ❌ |

The per-axis drives are pure functions of stored state plus the run's params, so "which need is most pressing" is **derivable** offline from satiation, injury and body temperature. It is **not derivable from the store for any thermal world**, because body temperature is missing. B1 makes starting body temperature a per-episode draw, which makes that gap worse.

**Gap to close:** add `body_temp` (float32, "state at t", `state.body_temp`) to the store's step columns. The store contract (`trajectory_store.py:115–116`) says no column may be inserted without a `SCHEMA_VERSION` bump (currently `1`), and the reader hard-errors on unknown versions (line 525). **Bumping a version needs the user's permission** (project rule). This is therefore Part L below, gated on Open decision D-L. Recommended: add only `body_temp` (derive the drives offline using the same deviation scales as `calculate_drive`); do not store drives.

No new termination codes are needed. B3 starvation → 2 and B4 freezing → 5 go through existing predicates. After this change, "why episodes end" is exactly as available as today.

---

## Implementation Plan

### Design

Four static-gated mechanics, one mandatory key each (plus B1's two range keys). Every gate is a **trace-time Python `if` on a static `EnvParams` field**, so at the inert value the branch emits no operation and the traced graph is the same as today. That is the `recovery_in_bush_multiplier` / warming-scale discipline. It is proved three ways:

1. rollout equality against a pre-change fixture;
2. jaxpr equality against the pre-change jaxpr;
3. a per-mechanic contrast test showing each gate, once non-inert, **does** change the rollout.

All four new static float fields are `float()`-coerced at load (a static field is part of JAX's trace-cache key, and YAML `0` vs `0.0` would otherwise recompile).

**D1 (B1, reset).** In `jax_reset`, after the injury draw:

```python
if params.thermal_random_start_body_temp:          # static; False on every thermal-off config
    body_temp0 = jax.random.uniform(
        body_key1, (), minval=params.thermal_start_body_temp_low,
        maxval=params.thermal_start_body_temp_high)
else:
    body_temp0 = params.temperature_setpoint
...
body_temp=jnp.asarray(body_temp0, dtype=jnp.float32),   # was: params.temperature_setpoint
```

`body_key1` is already split and unused, so no existing stream moves. The comment at `core.py:2061–2063` is updated accordingly.

**D2 (B2, `update_body` injury block, right after the bush premium at line 313):**

```python
if params.thermal_healing_temperature_sensitivity != 0.0:   # static; 0.0 on thermal-off
    _warmth = jnp.maximum(
        0.0, 1.0 - params.thermal_healing_temperature_sensitivity
        * jnp.abs(state.body_temp - params.temperature_setpoint))
    recovery_amount = recovery_amount * _warmth
```

**D3 (B3, `update_body`).** Three static edits, and on the off path the executed statements are the same as today, in the same order:

```python
# nutrition block — replace line 253
if params.healing_nutrition_cost == 0.0:
    new_nutrition = jnp.clip(new_nutrition, 0.0, params.max_nutrition)
# (else: clip deferred until after the injury block)

# satiation block — derive here only on the off path
if params.with_satiation and params.healing_nutrition_cost == 0.0:
    <today's two lines, verbatim>
elif not params.with_satiation:
    new_satiation = state.satiation
# (else: derived after the charge)

# injury block — capture before recovery, compute healed after the clip
_injury_before_recovery = new_injury                       # after the damage slice
... existing recovery + clip ...
if params.healing_nutrition_cost != 0.0:
    _healed = jnp.where(can_recover,
                        jnp.maximum(_injury_before_recovery - new_injury, 0.0), 0.0)

# after the injury block, before the death checks
if params.healing_nutrition_cost != 0.0:        # loader guarantees with_nutrition and with_injury
    new_nutrition = new_nutrition - params.healing_nutrition_cost * _healed
    new_nutrition = jnp.clip(new_nutrition, 0.0, params.max_nutrition)
    if params.with_satiation:
        <today's two satiation lines, verbatim>
```

The `_injury_before_recovery = new_injury` alias is a Python name binding, not an op, so it is safe on the off path. The ORDER comment at `core.py:184–193` is rewritten to list step 4 (B3 charge) and state that the single clip sits after it.

**D4 (B4, body-temperature block, lines 385–409):**

```python
if params.thermal_injury_heat_exchange_gain != 0.0:          # static
    _k_ex = params.thermal_k_exchange * (
        1.0 + params.thermal_injury_heat_exchange_gain
        * state.injury_level / params.max_injury)
else:
    _k_ex = params.thermal_k_exchange                        # the same traced leaf; no op
```

Then replace `params.thermal_k_exchange` with `_k_ex` in **both** branches (the 1.0/1.0 branch at 389 and the scaled branch at 402). Nothing else in the recurrence changes. It uses pre-step injury (`state.injury_level`), the same convention as B2's pre-step temperature.

**Loader, D4.** When g ≠ 0:

- extend both stability checks to the full-injury coefficient: `k_ex·(1+g) + k_loss ≤ 1`, and `scale·(k_ex·(1+g) + k_loss) ≤ 1` per scale, with an error message naming `thermal.injury_heat_exchange_gain`;
- call `_check_thermal_structure` a second time with `k_exchange = k_ex·(1+g)`, and prefix its failure message with "at full injury (thermal.injury_heat_exchange_gain = g)".

Endpoint checks suffice because settle points are monotone in `k_ex` (§A2). When g = 0 the loader path is byte-identical to today.

**Loader, validation per key.** All keys are read with `get_mandatory`. All are refused when NaN (write the check as `not (x >= 0)`).

| Key | Scope | Validation |
|---|---|---|
| `thermal.random_start_body_temp` | conditional under `thermal.enabled` | bool |
| `thermal.start_body_temp_low/high` | conditional under the flag; sentinel `(setpoint, setpoint)` otherwise; `(0.0, 0.0)` when thermal is off | `min_temperature ≤ low ≤ high ≤ max_temperature` |
| `thermal.healing_temperature_sensitivity` | conditional under `thermal.enabled`; sentinel `0.0` when off | `≥ 0` |
| `thermal.injury_heat_exchange_gain` | conditional under `thermal.enabled`; sentinel `0.0` when off | `≥ 0`, plus the bound checks above |
| `body.healing_nutrition_cost` | **unconditional** | `≥ 0`; if `> 0` then `with_nutrition` and `with_injury` must both be true, else `ValueError` explaining why |

**Why B3 is unconditional and B2/B4 are not.** B2 and B4 read body temperature, which does not exist in a thermal-off world. B3 has no natural gate, and it follows the `recovery_in_bush_multiplier` precedent. Its broader roll-out and saved-run cost are stated in §A6 and §A7.

**Part L (gated on D-L).** Add the `body_temp` step column to the trajectory store with a `SCHEMA_VERSION` bump, and teach the reader to accept both 1 and 2 (a v1 store has no `body_temp`, and readers must not assume it). This is a separate commit. It may be split into its own plan if the user prefers.

### File Changes

**Commit C1 — the pre-change fixture (made FIRST, from a worktree of the pre-change tip; no `src/` change)**

#### NEW `scripts/fixtures/generate_body_mechanics_parity_fixture.py`

- Modelled on `scripts/fixtures/generate_thermal_rate_scale_fixture.py`: `--src-root` is **required** (no default); `JAX_PLATFORMS=cpu` is set before any jax import; the SHA of `--src-root` is stamped as `_provenance_sha`; output always goes to this checkout's `tests/env/fixtures/body_mechanics_parity/pre_change_rollouts.npz`.
- **Worlds** (both loaded through `load_env_config` → `load_env_params` from the `--src-root` tree): `configs/environment/experiment/basic/05-campfire_thermal_10x10.yaml` (thermal) and `configs/environment/experiment/basic/04-jump_attack_10x10.yaml` (non-thermal parent; random start injury and nutrition, bush healing, pounce).
- **Episodes:** 16 reset seeds (0–15) × up to 300 steps each, stepped with `jax.jit(jax_step)` until `done`.
- **Actions:** a deterministic stream. `action_t = 4 (rest)` when `(t // 20) % 3 == 2`, otherwise `jax.random.randint(fold_in(PRNGKey(1234), seed·1000 + t), (), 0, 6)`. The rest bursts produce rest streaks, and therefore healing.
- **Recorded per step:** every leaf of `EnvState` via `jax.tree_util.tree_flatten` (including `key`, `body_temp`, `nutrition`, `injury_level`, `rest_streak`; `thermal_field` once per episode), `reward`, `done`, every numeric `info` entry (at minimum `termination_reason`, `drive_hunger`, `drive_injury`, `drive_thermal` where present, `damage`, `rested`, `ate_food`, `agent_in_bush`), and `get_observation(state, params)`. Padded arrays plus per-episode lengths.
- **Also recorded:** `sha1(str(jax.make_jaxpr(jax_step)(state0, action0, params)))` and the same for `jax_reset`, per world.
- **Refuses to write** (non-zero exit) unless the rollouts cover what the test must see. Per world:
  - ≥ 1 rest step with a positive injury decrease;
  - ≥ 1 rest step on a bush with a positive injury decrease;
  - ≥ 1 real death (termination reason ≥ 2);
  - ≥ 1 eat event;
  - for level 05, a body temperature range spanning ≥ 5°.

  It prints the counts. If a threshold is not met, raise the step budget or the seed count; do not lower the threshold.
- Module docstring states: the scenario constants (seeds, step budget, action rule, worlds) are duplicated in the test and must be changed in both places; and it must be generated from pre-change code.

#### NEW `tests/env/fixtures/body_mechanics_parity/pre_change_rollouts.npz`

Generated with `git worktree add --detach /tmp/gwp_bodymech_baseline <pre-change SHA>` → run the generator with `--src-root` → `git worktree remove`. Record the SHA in the Implementation Report.

#### `docs/environment/SCRIPTS_DEPENDENCY_MAP.md`

Add a row for the new generator. Callers: the test in C2 (by docstring reference) and a human running it. `sys.path` root depth: 2, the same as its sibling generators.

**Commit C2 — mechanics, keys, tests and docs (everything inert; no world behaves differently)**

#### `src/environment/state.py` (EnvParams)

- Next to `recovery_in_bush_multiplier` (line 259): `healing_nutrition_cost: float = struct.field(pytree_node=False)`, with a comment in the style of lines 251–258 (why static; `float()` coercion).
- In the thermal block, near lines 393–424:
  - `thermal_random_start_body_temp: bool = struct.field(pytree_node=False)`
  - `thermal_start_body_temp_low: float` (traced)
  - `thermal_start_body_temp_high: float` (traced)
  - `thermal_healing_temperature_sensitivity: float = struct.field(pytree_node=False)`
  - `thermal_injury_heat_exchange_gain: float = struct.field(pytree_node=False)`
- Update the `body_temp` comment at lines 90–95 ("initialised to the setpoint, or drawn from [low, high] when `thermal_random_start_body_temp`").

#### `src/environment/config_loader.py`

- Thermal-on arm (after the rate-scale block at 1591, before metabolic coupling at 1593): read and validate B1, B2 and B4 per the table in §Design. Extend the two stability checks when g ≠ 0.
- Thermal-off `else` arm (1647–1672): inert sentinels `False, 0.0, 0.0, 0.0, 0.0`, with a comment that they are never read and why the values are the no-op ones.
- Structure check call (around line 2019): second invocation at the full-injury `k_exchange` when g ≠ 0.
- Body block (after 2233): `body.healing_nutrition_cost`, unconditional, `float()`, validated per §Design.
- `EnvParams(...)` construction (around 2333–2400): pass the six new fields.

#### `src/environment/core.py`

- `update_body` (155–422): D2, D3 and D4 exactly as specified. Update the Returns/ORDER comments. `calculate_drive` (72–127) is **not touched**.
- `jax_reset` (1775–1792, 2061–2064): D1.
- `jax_step` termination chain (994–1016): **no change** (B3 and B4 reuse existing predicates). Add one comment line at the reason-2 line: "B3 starvation lands here via the single clip in update_body".

#### `configs/environment/default.yaml`

Under `thermal:` (after `metabolic_coupling_rate`, line 546):

```yaml
  # Random starting body temperature (B1). Read ONLY when thermal.enabled. The range is
  # read ONLY when random_start_body_temp is true; there is no fixed-start key (pin a
  # start with low == high). Default range = the setpoint, so flipping only the flag
  # reproduces today's start exactly.
  random_start_body_temp: false
  start_body_temp_low: 0.0
  start_body_temp_high: 0.0
  # Healing needs warmth (B2): fraction of injury recovery lost per degree the body is
  # away from temperature_setpoint (1/deg). 0.0 = off (today's recovery, byte-identical).
  healing_temperature_sensitivity: 0.0
  # Injury speeds heat exchange (B4): k_exchange is multiplied by 1 + gain*injury/max_injury.
  # 0.0 = off. NOTE: scales k_exchange, NOT k_loss — k_loss is the body's DEFENCE toward
  # setpoint, and raising it with injury would make injury protective.
  injury_heat_exchange_gain: 0.0
```

Under `body:` (after `recovery_in_bush_multiplier`):

```yaml
  # Healing uses energy (B3): nutrition charged per injury point actually healed this step,
  # before the single clip to [0, max_nutrition]. 0.0 = off. Requires with_nutrition and
  # with_injury. A heal that costs more than the agent has starves it (termination 2).
  healing_nutrition_cost: 0.0
```

#### Raw-loaded configs that need the inert keys (§A6)

- **Thermal keys** (inline, with the same "kept loadable because a test loads it from a raw Config" comment the 2026-09-17 lines carry): `configs/environment/experiment/archive/thermal/campfire_world.yaml` and `campfire_world_body_temp_hidden.yaml`.
- **`body.healing_nutrition_cost: 0.0`** in:
  - every file in the 36-file non-archive set (`grep -rl recovery_in_bush_multiplier configs tests | grep -v experiment/archive`);
  - `tests/env/fixtures/frozen_parity_worlds/environment__default.yaml` (comment block modelled on its lines 225–233);
  - the archived test inputs identified in §A6.

  The developer lists every touched file in the Implementation Report, with the before/after load counts.

#### NEW `tests/env/test_body_mechanics_parity.py` — the no-change test (requirement 2)

- `JAX_PLATFORMS=cpu` is set before the jax import. **Fails, never skips**, if the fixture, a world config, or `_provenance_sha` is missing.
- Loads both worlds at HEAD via `load_env_config` → `load_env_params`. For level 05, once C3 has landed, it sets `thermal.random_start_body_temp: false` **in memory** on the resolved dict before building params. It also asserts that every other new key already resolves to its inert value, so a later default change cannot silently turn this into a comparison of a different world.
- Replays the identical scenario. Asserts `np.array_equal` (no tolerance) on every recorded array, per step, per episode, including `state.key`, reward, `termination_reason` and observations.
- Asserts the jaxpr SHA-1s for `jax_step` and `jax_reset` equal the fixture's (inert worlds).
- **Contrast half** (anti-vacuous), on level 05 unless noted: switching on
  - B1 (flag on, range [−5, −5]),
  - B2 (s = 0.1),
  - B3 (c = 1.0, on both worlds),
  - B4 (g = 1.0)

  each yields a rollout that **differs** from the fixture, and a jaxpr SHA that differs.
- Re-asserts the fixture's coverage counts (§C1) so a regenerated, degenerate fixture cannot pass.

#### NEW `tests/env/test_body_mechanics_units.py` — per-mechanic unit tests (requirement 3)

Hand-built `EnvState` / `info` fed directly to `update_body` (and `jax_reset` for B1), with params from level 05 via the resolving loader plus in-memory overrides. Expected values are hand-computed and written as literals in the test. Tolerance is `atol=1e-5` for arithmetic values; **exact equality** for the off cases.

- **B1**
  - T-B1-1: flag off → `body_temp == temperature_setpoint`, and every other reset leaf equals the pre-change reset for 32 keys.
  - T-B1-2: flag on, `low == high == −7.0` → `body_temp == −7.0` exactly (the trap test).
  - T-B1-3: flag on, [−10, 5] over 1000 keys → all in range, sample mean within ±0.5 of −2.5, and **every non-body_temp reset leaf equals the flag-off reset for the same key** (stream isolation).
  - T-B1-4: loader — flag missing with thermal on → `ValueError` naming the key; low > high, low < min_temperature, high > max_temperature → `ValueError`; thermal off with all B1/B2/B4 keys deleted → loads.
- **B2** (resting, in a bush, no damage, injury 50, s = 0.1)
  - T-B2-1: T = 0 → 45.0; T = −5 → 47.5; T = −10 → 50.0; T = +6 → 48.0; T = −30 → 50.0 (factor floors at 0, never negative).
  - T-B2-2: in the open at T = −5 → 49.9.
  - T-B2-3: s = 0 → exactly today's value at all T.
  - T-B2-4: not resting, or taking damage → no recovery regardless of T.
  - T-B2-5: s < 0 / NaN → `ValueError`.
- **B3** (c = 1.0, resting in a bush, T = 0, B2 off, prev nutrition 100, metabolic 1.0)
  - T-B3-1: injury 50 → nutrition 94.0.
  - T-B3-2: injury 3 → 96.0 (charged for 3, not 5).
  - T-B3-3: injury 0 → 99.0.
  - T-B3-4: prev nutrition 4, injury 50 → nutrition 0.0, `done` true, and through `jax_step` `termination_reason == 2`.
  - T-B3-5: a damage step that pushes injury past max → no charge.
  - T-B3-6 (auto-eat world, `eat_action_enabled: false`): rest on food in the open, injury 50, prev nutrition 196, gain 6, eat cost 1 → 196 − 1 + 5 − 0.2 = 199.8, and **no** over-eating death. With c = 0 the same step lands on 200 and dies (documents the order).
  - T-B3-7: A1 coupling on at rate 1, T = −10, k_loss 0.02 → 100 − 1 − 0.2 − 5 = 93.8.
  - T-B3-8: B2 s = 0.1 at T = −5 → healed 2.5 → 96.5.
  - T-B3-9: `c > 0` with `with_injury: false` or `with_nutrition: false` → `ValueError`; c < 0 → `ValueError`; key missing → `ValueError`.
- **B4** (uniform cell −30, T = 0, level-05 scales)
  - T-B4-1: g = 1, I = 50 → T' = −0.45; I = 100 → −0.60; I = 0 → −0.30 exactly equal to g = 0.
  - T-B4-2: 1.0/1.0 scales: I = 50 → −1.8 versus −1.2 at g = 0.
  - T-B4-3: warm cell +10, T = 0, I = 50 → +1.2 (symmetric exchange, warming scale 2).
  - T-B4-4: settle point after 3000 steps at cell −10, I = 100, g = 1, scales 1/1 → −8.0 (versus −6.667 at g = 0).
  - T-B4-5: loader — g = 11.5 at level-05 values → `ValueError` naming the gain (bound `2.0·(0.04·12.5 + 0.02) = 1.04 > 1`); g = 11 → loads; g < 0 / NaN → `ValueError`.
  - T-B4-6: a synthetic world whose ring is survivable at I = 0 but lethal at full injury → structure check raises with the "at full injury" prefix; the same world at g = 0 loads.
- **Graph identity, in the style of `test_recovery_in_bush.py::test_multiplier_one_is_graph_identical`:** at each inert value the traced `update_body` does not consume the relevant input; at a non-inert value it does. Inputs: `state.body_temp` for B2 inside the injury block; `state.injury_level` for B4 inside the thermal block. Locate the leaf positionally.

#### Existing tests that must stay green **unmodified**

`test_thermal_parity.py`, `test_unified_parity.py`, `test_visual_parity.py`, `test_metabolic_coupling.py`, `test_thermal_rate_scales.py`, `test_recovery_in_bush.py`, `test_two_sided_nutrition.py`, `test_thermal_reward_gate.py` (**no fixture regeneration permitted** — `calculate_drive` is untouched), `test_no_recompile.py`, `test_truncation_not_death.py`, `test_config_layer_silent_failures_20260723.py`, `test_dashboard_layout.py`. Only the inline-YAML additions of §A6 may touch test files.

#### Docs (same commit — maintenance contracts)

- `docs/environment/CONFIG_GUIDE.md`: §5 (conditional-mandatory keys). Add the three thermal-conditional keys, the unconditional body key, the "pin a start with low == high; there is no fixed-start key" note, and the recovery path for a repo config missing a key (add the inert value; never edit a saved run config).
- `docs/environment/02_config_schema.md`: rows for all six keys (path, type, unit, inert value, validation, read condition).
- `docs/environment/05_body_homeostasis.md`: the new update ORDER (step 4, the B3 charge), the B2 multiplier, the B4 coefficient (and why `k_exchange`, not `k_loss`), and B1 at reset.
- `docs/environment/06_reward_and_termination.md`: one line saying that B3 starvation and B4 freezing reuse reasons 2 and 5, and that the reward formula is unchanged.
- `docs/environment/CONFIG_CRITICAL_SETTINGS.md`:
  - registry rows for the four mechanics (canonical value 0.0 / false in `default.yaml`);
  - a dated change-log entry "2026-09-2x — new keys …, shipped inert". It carries the jaxpr SHAs before and after, the parity-family pass counts, the archived before/after load counts, the saved-run count (§A7 table), and the roll-out file list.

**Commit C3 — enable B1 in level 05 (the only behaviour change in this plan)**

#### `configs/environment/experiment/basic/05-campfire_thermal_10x10.yaml`

In the `thermal:` block (currently only `enabled: true`), plus a header note:

```yaml
thermal:
  enabled: true
  # Random starting body temperature (B1), enabled 2026-09-2x as a standard internal
  # state of this world. Range: Open decision D-B1 in
  # docs/develop/active/thermal/STATE_DEPENDENT_BODY_MECHANICS.md. The upper end stays
  # below the fire-ring settle temperature (+5.75) so the first step onto a fire stays
  # survivable (+10.8 < +15).
  random_start_body_temp: true
  start_body_temp_low: -10.0
  start_body_temp_high: 5.0
```

Update the header comment's list of values that differ from default.yaml, and note that level 06 inherits this (per D-L06).

#### `docs/environment/CONFIG_CRITICAL_SETTINGS.md`

A dated change-log entry: "B1 enabled in level 05 (and, by inheritance, level 06)". **Why:** per the 2026-09-26 decision, level 05 becomes the main world for state-dependence. **Consequence:** Wave 2 level-05 and level-06 runs are no longer like-for-like baselines for anything trained after this line. Also: render-fixture recordings of M3/M4 differ on regeneration. Include the measured start-temperature distribution over 600 real resets through the live loader (min, max, mean) and the first-step-onto-fire maximum measured over those resets.

**Commit C4 — Part L (only if D-L is approved)**

- `src/utils/trajectory_store.py`: `SCHEMA_VERSION` bumped to the value the user approves. Add `Column("body_temp", None, "float32", "state at t", "state.body_temp")` after `injury_level`. The reader accepts the old and new versions; a v1 store yields no `body_temp` column, and `validate_*` must not require it.
- The writer site in `scripts/eval/traj_collect/collect_trajectories.py` (wherever step columns are filled): fill `body_temp`.
- `docs/environment/TRAJECTORY_STORE_SCHEMA.md`: the new column and the version note.
- `docs/environment/SCRIPTS_DEPENDENCY_MAP.md`: only if a script's callers change.
- Test: extend the store round-trip test to assert that `body_temp` equals `state.body_temp` on a short level-05 collection, and that a v1 store still reads.

---

## Open decisions (for the user)

- **D-B1 — Level-05 start range.** Proposed [−10, +5]. The upper end keeps the first step onto a fire survivable (+10.8 against +15); the lower end leaves 46 steps before freezing at the coldest cell. Alternatives: [−10, +10], which makes the first fire step a knife-edge (+14.96); or a narrower [−5, +5].
- **D-B2 — Symmetric vs cold-only healing penalty.** The symmetric form (the task's wording) slows healing at the warm ring beside a fire (+5.8° → 3.0/step at s = 1/15). Cold-only heals at full speed there. Also: which sensitivity to use in the B2 test world — 1/15 (healing stops at the death threshold) or 0.1 (stops at ±10°)? B2 ships off, so this only matters when it is turned on.
- **D-B3 — When a heal costs more than the agent has.** Proposed: charge, and let the single clip starve it (reason 2). Alternative: cap healing at what the remaining nutrition can pay, so healing never kills. That is more code and a second coupling, but perhaps more "biological".
- **D-B4 — Confirm the coefficient.** B4 scales `k_exchange`, not `k_loss` (§A2: raising `k_loss` makes injury protective). Symmetric (injured bodies also warm faster at a fire) vs cold-only (the gain applies only when the cell is colder than the body).
- **D-L06 — Level 06 inherits B1** through `extends:`. Accept, or pin it off in the level-06 file?
- **D-COMPAT — Sequencing against old-run analysis.** Once C2 lands, all Wave 1 and Wave 2 saved configs stop loading (B3 is unconditional), and the Wave 1 trajectory collection now being prepared would die at config load. Options:
  - (a) land [[SAVED_RUN_CONFIG_COMPAT]] Stage 1 first, with these four era keys added to its table;
  - (b) hold C2 until the pending collections finish, and run later analyses of old runs from a pre-change git worktree;
  - (c) land now and accept the gap.

  Recommended: (a), or (b) if the compat plan is not ready.
- **D-L — Trajectory-store `body_temp` column.** It needs a `SCHEMA_VERSION` bump (your permission is needed for any version change). Without it, "which need is most pressing" cannot be computed from stores in the thermal world. Alternatives: use `.rec.gz` eval recordings (which already carry body temperature, but only for small N), or split Part L into its own plan.
- **D-ARCH — Two archived thermal worlds are de-facto test fixtures.** `campfire_world.yaml` and `campfire_world_body_temp_hidden.yaml` sit under `archive/` but are loaded by about nine test modules. This plan adds the inert keys to them (precedent 2026-09-17). Moving them to `tests/env/fixtures/` is out of scope here, but recommended as a follow-up.

---

## Out of scope

- The injury × starting-fullness probe scenes (a separate, later plan).
- Level-05 variant world configs, for example the B3-on world (these belong to `experiment-designer`, outside `basic/`). The keys above make them expressible: a variant `extends:` level 05 and sets `body.healing_nutrition_cost`.
- Any change to `calculate_drive` or the reward.
- Implementing `saved_config_compat.py` (owned by [[SAVED_RUN_CONFIG_COMPAT]]).

---

## Checkpoints

- [ ] **CP1 — C1 before any `src/` edit.** Fixture generated from a worktree of the pre-change tip. Coverage counts printed and all non-zero. `_provenance_sha` recorded in the Implementation Report. The fixture is committed on its own.
- [ ] **CP2 — B1 stream isolation.** After D1, T-B1-3 passes: a flag-on reset differs from a flag-off reset **only** in `body_temp`, over 1000 keys.
- [ ] **CP3 — Inert = today, measured three ways.** `test_body_mechanics_parity.py` is green (rollouts plus jaxpr SHAs) for both worlds, and its contrast half is green (every mechanic, once on, changes the rollout). Record the jaxpr SHA-1s in the Implementation Report.
- [ ] **CP4 — B3 off path.** `str(jax.make_jaxpr(update_body)(…))` at c = 0 is identical before and after D3 on both worlds. This checks specifically that moving the clip and satiation behind static branches emitted the same ops in the same order.
- [ ] **CP5 — Unit tests.** All of T-B1 … T-B4 green, with the hand-computed literals in the test source.
- [ ] **CP6 — Loader.** Every new key raises when missing in its read condition; thermal-off configs load with the thermal keys deleted; B4 bound and structure-check extensions exercised (T-B4-5, T-B4-6); the level-05 structure check still passes at g ∈ {0, 1, 2}.
- [ ] **CP7 — Roll-out.** `tests/` fully green on CPU, run file by file for the parity families (report passed / skipped counts per family and compare them with the counts in the 2026-09-17 change-log entry; any new skip needs an explanation). Report archived before/after load counts. Report the saved-run count that stops loading (§A7 table, re-measured).
- [ ] **CP8 — Level 05 through the real loader after C3.** `load_env_config` → `load_env_params` resolves `thermal_random_start_body_temp == True`, the range [−10, 5] (or the approved range), and the other three keys inert. 600 real resets: every `body_temp` in range, and the max first-step-onto-fire temperature below +15. Level 06 resolves per D-L06.
- [ ] **CP9 — Reward untouched.** `git diff` shows no change inside `calculate_drive`. `tests/env/test_thermal_reward_gate.py` passes with its **unregenerated** reference data.
- [ ] **CP10 — Speed.** SPS on level 05 (B1 on) and level 04 before and after, same node, GPU and seed, with a step budget long enough to pass warm-up. Expected change within noise: B1 adds one scalar draw per reset, and the other three are not traced.
- [ ] **CP11 — Docs.** CONFIG_GUIDE §5, 02_config_schema, 05_body_homeostasis, 06_reward_and_termination, the CONFIG_CRITICAL_SETTINGS registry plus two change-log entries (C2, C3), and the SCRIPTS_DEPENDENCY_MAP row. All in the same commits as the code they describe.
- [ ] **CP12 — Hand-offs.**
  - `bug-curator`: update the "mandatory keys land without migrating the archive" row with this plan's counts, and note that B3 adds no reason-code path.
  - The [[SAVED_RUN_CONFIG_COMPAT]] owner: the four era-key rows of §A7.
  - `experiment-designer`: the observability caveat in §A0 (injury and nutrition are not observed at level 05).

---

## Implementation Report

> **Implemented by**: [agent/person]
> **Date**: [date]

<!-- Filled by `developer`. Must include: pre-change SHA + fixture coverage counts (CP1); jaxpr SHA-1s
     before/after for jax_step, jax_reset, update_body on both worlds (CP3/CP4); the full list of files
     that received inert keys; parity-family pass/skip counts; archived before/after load counts;
     saved-run count that no longer loads; the 600-reset B1 measurement (CP8); SPS before/after (CP10);
     any deviation from this plan and why. -->

## Verification Report

> **Verified by**: [agent/person]
> **Date**: [date]

| File | Change | Status | Notes |
|------|--------|:------:|-------|
| | | | |

**Conclusion**: [one-line summary]
