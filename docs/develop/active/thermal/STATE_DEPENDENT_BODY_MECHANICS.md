---
title: "Four body mechanics that make the best action depend on combinations of internal states (level 05)"
topic: sensors
status: active
created: 2026-09-26
last_updated: 2026-09-26
aliases: [state_dependent_body_mechanics]
---

# Four body mechanics that make the best action depend on combinations of internal states (level 05)

> **Status**: PLANNED, Revision 2 (2026-09-26). The user's decisions and the `plan-reviewer` and `math-reviewer` findings are folded in; see §Revision log. Waiting on the items in §Still open for the user, then approval.
> **Opened**: 2026-09-26
> **Related**: [[INJURY_DEPENDENCE_PLAN]] (the analysis that motivated this) · [[WARMING_COOLING_RATE_SCALES]] (the fixture-from-a-pre-change-worktree precedent; the body-temperature recurrence) · [[BUSH_REFUGE_AND_LOCATION_DEPENDENT_RECOVERY]] (precedent for a static-gated body key and its roll-out cost) · [[SAVED_RUN_CONFIG_COMPAT]] (the general old-run loading plan; **read, not edited** — another session owns it; this plan builds a minimal, absorbable first slice of it, §A7 and §Hand-off) · [[recovery_in_bush_tuning]] · [[IMPLEMENTATION_PLAN]] (thermal)

---

## Context

The project is making the campfire world the main place to study whether a neuromodulated agent's behaviour depends on its internal state. That world is curriculum level 05: a cold 10×10 grid with one to three campfires, where the agent must keep three body quantities near their comfortable values — how full it is, how injured it is, and its body temperature.

A recent analysis found that, in both the modulated and the unmodulated agent, the response to injury is a simple habit that ignores everything else. Healing is fast and costs nothing (five injury points per step while resting in a bush), so "injured → go to a bush and rest" is always right, whatever the agent's hunger or temperature.

This plan adds four mechanics that change the **consequences** of actions on the body, so that the best action depends on **combinations** of internal states. The reward formula is untouched.

- **B1**: each episode starts at a random body temperature.
- **B2**: healing slows when the body is too cold or too warm, with separate settings for each side.
- **B3**: healing costs food energy. A setting decides what happens when the agent cannot pay: heal only what it can afford, or heal fully and starve.
- **B4**: injury makes the body exchange heat faster. A setting decides whether that applies only while losing heat or in both directions.

Following the user's rule for this work, every interaction is a config setting; no behaviour choice is hard-coded. Each setting has an exact "off" value at which the environment behaves as it does today, byte for byte, and a test compares against rollouts recorded from the current code.

**What is switched on:**
- B1 is enabled in level 05, and level 06 inherits it.
- B3 will be used by one variant world, written later by `experiment-designer`.
- B2 and B4 ship off.

Because every old training run's saved settings file would stop loading once these settings become mandatory, a small, logged compatibility step lands **first**. It fills in exactly these new settings, at their off values, when an analysis tool re-opens an old run.

---

## Analysis

### A0 — Wiki pull gate and known bugs

The `config_system` and `env_entities` folders of the LLM Wiki were read. Four entries bear on this plan:

- **`20260622_1746_start_injury_dead_needs_random_range`.** `body.start_injury` is never read; a fixed non-zero start needs a random range with `low == high`. **B1 adds no fixed-value key at all**, so that trap cannot recur. A pinned start is written as "flag on, `low == high`", and T-B1-2 pins that it works.
- **`20260909_1402_parity_gates_green_without_comparing`.** Parity gates must **fail**, not skip, when their inputs are missing. The parity test and the compat test both carry that requirement.
- **`20260820_1606_reset_ulp_divergence_is_compiler_fusion`.** Two compilations can differ by one float32 ULP. The fixture and the test are both pinned to CPU.
- **`20260901_1528_interoceptive_channel_is_two_dims_by_design`.** Injury and nutrition are **not observed** at level 05, so B2 and B3 couple hidden states. That is an experiment-design question for `experiment-designer`, not a defect here.

Known bugs (from `bug-curator`) and how each is handled:

| Known bug | Handling |
|---|---|
| `start_satiation` / `start_injury` inert unless the random range is used | B1 has no fixed-start key. Pinning is "flag on, `low == high`" (T-B1-2). The default range is `[setpoint, setpoint]`. |
| Termination-reason codes untrustworthy when a body system is disabled (`core.py:1010`) | The loader **refuses** B3 (`c > 0`) unless `with_nutrition` and `with_injury` are both true, and refuses B4 (`g > 0`) unless `with_injury` is true (reviewer L3). No new reason code is added. B3's partial-mode starvation test is **returned by `update_body` and read by `jax_step`**, so the label and `done` share one predicate (§A3). |
| 227/265 standalone configs already fail to load (accepted policy) | Measured and stated (§A6). Only archived files that are **live test inputs** get the off values (2026-09-15 / 09-17 precedent). |
| `test_backward_compat_configs.py` skips every `basic/` world | The no-change test loads basic/05 and basic/04 through `load_env_config` → `load_env_params`. |
| Render-audit fixtures rejected by the thermal structure check (`config_loader.py:682-701`) | B1's start range does not enter the structure check. B4 extends that check only when `g > 0`, so the `g = 0` path is the same code. |
| `test_thermal_reward_gate.py` reference data must be regenerated if `calculate_drive` changes | `calculate_drive` is not touched. The test must pass with its data **unregenerated** (CP9). |
| Interoceptive nociception buffer zeroed at reset | Kept. B1 changes only `body_temp` at reset. |
| Nutrition two-sided, 0–200 with setpoint 100 (`379ec8fc`) | Over-eating is judged after the healing charge in both B3 modes; starvation is judged after the charge in `full` mode and before it in `partial` mode (§A3). |

### A1 — Where things are today (code as truth, `v4.0`, 2026-09-26)

**Level 05 resolved through the real loader:**

| Setting | Value |
|---|---|
| Recovery | base 0.2/step, compounding 0.0, bush multiplier 25.0 → **5.0 injury points per rest step in a bush**, 0.2 in the open |
| Metabolic cost | 1.0/step |
| Nutrition | range [0, 200], setpoint 100, over-eating death on |
| Random starts | nutrition [0, 200], injury [0, 100] |
| Body temperature | setpoint 0.0, death outside [−15, +15] |
| Heat exchange | `k_exchange` 0.04, `k_loss` 0.02, `k_metabolic` 0.0 |
| Rate scales | warming 2.0, cooling 0.25 |
| Metabolic coupling | off |
| World | baseline sampled from [−31, −29]; fire = 11 × \|baseline\| |

**Temperatures from the loader's single-fire model** (`_thermal_single_fire_field` / `_thermal_radial_equilibria`). These are model values; the state temperatures measured on real resets are wider, for example ring settles of 5.56–6.78 including merged-fire layouts.

| Quantity | Baseline −31 (hot corner) | Baseline −29 |
|---|---|---|
| Fire-cell temperature | **79.73** | 74.59 |
| Ring settle (one cell out) | **+5.94** | +5.56 |
| Three cells out | about −20 | about −19 |

**Other timings at level 05:**
- Away from a fire, the body cools from 0 to −15 in 92 steps (cell −30).
- After leaving the ring at +5.8 it takes 17 / 36 / 63 steps to reach 0 / −5 / −10.
- Rewarming from −14 at the ring takes 10 steps.

**Update order inside `core.py::update_body` (155–422):**
1. **Nutrition:** decay → A1 thermal drain (static gate, pre-step body temperature) → food → **one clip** to [0, max] (line 253).
2. **Satiation** derived from the clipped nutrition (258–263).
3. **Injury:** damage slice → rest streak → recovery → bush premium (static gate, 309–313) → `can_recover = rested ∧ applied_inc ≤ 0` → subtract → clip.
4. **Death tests** (330–358).
5. **Body temperature** (373–420): static on `thermal_enabled`, then static on the scales being 1.0/1.0.

Nutrition is finalised before the injury block knows what was healed, so B3 moves the clip and the satiation derivation behind the injury block. This happens in static branches (D3).

**Reset.** At `core.py:1775`, `body_key1, body_key2, body_key3 = split(body_key, 3)`. `body_key1` is **split and never used** (the reviewer confirmed this), so B1 draws from it and no existing random stream moves.

**Static vs traced parameters.** Every `EnvParams` leaf becomes a jaxpr input whether or not it is used. A new traced field therefore renumbers the jaxpr string even on the off path (reviewer M1; verified empirically). This plan makes **every new field static** (`struct.field(pytree_node=False)`, with floats `float()`-coerced at load): one rule, no new leaves. The pre-change and post-change `jax_step` / `jax_reset` jaxprs are then comparable as strings on the off path.

### A2 — B4: scale `k_exchange` (confirmed), with a configurable direction

In this code `k_loss` is the body's **defence**, the share of the deviation that physiology undoes each step (`config_loader.py:1551`). Raising it with injury would protect the injured body. The user confirmed that B4 scales `k_exchange`, the heat swap with the cell:

$$
k_{ex}^{\text{boost}} = k_{ex}\,\Bigl(1 + g\,\frac{I}{I_{\max}}\Bigr),\qquad g \ge 0
$$

**Direction setting, `thermal.injury_heat_exchange_mode`:**
- **`cooling_only`** (default, and the value for this batch): the boost applies on a step where the cell is colder than the body (`T_cell < T`), i.e. while heat flows out. Stepping onto a fire is unaffected, so the 2026-09-19 fire calibration still holds for injured agents.
- **`both`**: the boost applies on every step. An injured agent also heats faster at a fire and can die on its **first** step onto one (math-reviewer). The loader therefore runs a first-step-onto-fire check for this mode (D4).

**Properties:**
- Off at `g = 0.0` exactly (static gate).
- The boost factor lies in [1, 1+g] and is monotone in injury.
- Settle point `T* = (k_ex'·T_cell + k_loss·T_set + k_met)/(k_ex' + k_loss)`.
- **Same-side note (math-reviewer).** The sign of `T* − T_cell` is the sign of `k_loss·(T_set − T_cell) + k_met`, which does not depend on `k_ex'`. So whether a cell is on the "body warmer than cell" (cooling) side does not change with injury, and in `cooling_only` mode each cell uses one coefficient consistently. Settle points are monotone in `k_ex'` on each side, so checking injury 0 and injury max is sufficient.

**Level-05 numbers** (cold cell −30, cooling scale 0.25; identical in both modes because heat only flows out):

| g | steps from 0 °C to freezing, injury 0 / 50 / 100 | settle temperature at injury 100 | first step from 0 °C at injury 100 |
|---|---|---|---|
| 0 | 92 / 92 / 92 | −20.0 | −0.30 |
| 0.5 | 92 / 69 / 55 | −22.5 at g = 1, injury 50 | — |
| 1 | 92 / 55 / 39 | −24.0 | −0.60 |
| 2 | 92 / 39 / 25 | −25.7 | — |

**Stability bound.** The loader enforces `scale·(k_ex + k_loss) ≤ 1`. The boost can apply on a warming step even in `cooling_only` mode: when `T_cell < T < T_set`, `k_loss` can pull the body up while the cell pulls it down. So the bound is checked at `k_ex·(1+g)` for **both** scales in **both** modes. At level 05 the binding case is warming 2.0: `2.0·(0.04·(1+g) + 0.02) ≤ 1` ⇒ g ≤ 11. The tests use g = 10.9 (loads) and g = 11.5 (refused), not the exact boundary (reviewer L1).

**First-step-onto-fire check (`both` mode only; math-reviewer's inequality):**

$$
T_{high} + s_w\bigl(k_{ex}(1+g)(F_{max} - T_{high}) - k_{loss}(T_{high} - T_{set}) + k_{met}\bigr) \le T_{max}
$$

- `F_max` is the model's fire-cell temperature at the hottest corner (`ratio_high·|default_temp_low|` through `_thermal_single_fire_field`).
- `T_high = max(B1 upper start (or T_set if B1 is off), full-injury ring equilibrium)`. Including the ring term is this plan's addition: a body settled beside a fire is the calibrated starting point for "first step onto the fire".

Level 05 (baseline −31, `F_max` 79.73):

| g | ring equilibrium at full injury | first step from `max(+5, ring)` | verdict |
|---|---|---|---|
| 0 | +5.94 | +11.61 | ok |
| 0.5 | +6.68 | +15.18 | **refused** |
| 1 | +7.13 | +18.46 | **refused** |

So `both` mode admits roughly g ≲ 0.45 at level 05; the developer computes the exact value in the test. Merged fires are not in the single-fire model; CP8 measures them.

### A3 — B3: healing uses energy, with a configurable shortfall mode

**Keys:**
- `body.healing_nutrition_cost` (`c ≥ 0`, nutrition per injury point healed; off at 0.0).
- `body.healing_nutrition_shortfall` ∈ {`partial`, `full`}. It is read **only when `c > 0`** (conditional-mandatory, the same shape as `thermal.metabolic_coupling_rate`). `default.yaml` carries `partial`, which is inert because `c = 0`. The variant world sets `c` and states `partial` explicitly.

**Definitions** (all quantities for one step):

| Symbol | Meaning |
|---|---|
| `I_d` | injury after this step's damage slice. Under `can_recover`, `applied_inc == 0`, so `I_d == prev_injury` (reviewer: `damage ≥ 0`). |
| `r` | `recovery_amount` after the bush premium and after B2 |
| `N_pre` | nutrition after decay, A1 drain and food, **before** the charge and before the clip |
| `h_nom` | `where(can_recover, min(r, I_d), 0)` — what would be healed if unpaid |

**Healed amount:**

$$
h = \begin{cases} h_{nom} & \texttt{full} \\ \min\bigl(h_{nom},\ \max(N_{pre}, 0)/c\bigr) & \texttt{partial} \end{cases}
$$

In `partial` this is the user's `min(recovery, prev_injury, available_nutrition / c)`, with available nutrition = `max(N_pre, 0)`.

**Updates:**
- `I' = clip(where(can_recover, I_d − h, I_d), 0, I_max)`. In `full` mode this equals today's `clip(I_d − r, 0, I_max)` exactly: `I_d − min(r, I_d)` is `I_d − r` when `r ≤ I_d`, and 0 otherwise. So the injury path does not change.
- `N' = clip(N_pre − c·h, 0, N_max)`: one clip, after every debit and credit.
- Satiation is derived from `N'`.

**Death labels** (one predicate, shared by `done` and the reason code):
- **Over-eating (both modes):** `N' ≥ N_max`, judged after the charge. It can only coincide with healing in auto-eat worlds (T-B3-6).
- **Starvation, `full` mode:** `N' ≤ 0`, the existing predicate. A heal that costs more than the agent has lands on 0 and the agent starves (reason 2).
- **Starvation, `partial` mode:** `clip(N_pre) ≤ 0`, i.e. judged **before** the charge. The charge can bring nutrition to 0 (or within a rounding ulp of it) but can never be the cause of death: "no death from the charge itself". If `N_pre ≤ 0` the agent was already starving from metabolism alone. Then `h = 0` and it dies with reason 2, exactly as today. This predicate is computed in `update_body` and **returned**; `jax_step`'s reason-2 line uses the returned value (static branch), so the label and `done` cannot diverge — the failure class the `core.py:1010` bug belongs to.
- **New reachable state in `partial` mode:** an agent can be alive at `N = 0`. On the next step decay drives `N_pre` negative, so it starves unless it eats that step. That is the intended "healed with its last reserves" situation, and a user-visible behaviour to know about.

**The loader refuses:** `c > 0` without both `with_nutrition` and `with_injury`; `c < 0` or NaN; a shortfall value other than the two names.

**Level-05 examples** (in a bush, resting, no damage, B2 off, `h_nom = 5`, `c = 1`):

| Nutrition before the step | `N_pre` | `full`: healed / N' / dies? | `partial`: healed / N' / dies? |
|---|---|---|---|
| 100 | 99 | 5 / 94 / no | 5 / 94 / no |
| 4 | 3 | 5 / 0 / **yes (2)** | 3 / 0 / no |
| 0.5 | −0.5 | 5 / 0 / yes (2) | 0 / 0 / yes (2), from metabolism |

**Cost scale at `c = 1`:** a full 100-point heal costs 100, half the 0–200 range. At `c = 0.5` it costs 50.

### A4 — B2: healing needs warmth, with separate cold and warm sensitivities

$$
w(T) = \max\Bigl(0,\; 1 - s_c\,\max(0, T_{set}-T) - s_w\,\max(0, T - T_{set})\Bigr),\qquad r \leftarrow r\cdot w(T)
$$

- **Keys:** `thermal.healing_cold_sensitivity` (`s_c`) and `thermal.healing_warm_sensitivity` (`s_w`), each ≥ 0, unit 1/°C.
- Equal values give the symmetric form. With both at 0 the branch is not traced (static gate on `s_c != 0 or s_w != 0`). Inside the branch, a side whose sensitivity is 0 contributes no term (static).
- `w` is bounded in [0, 1], never negative and never a boost, and monotone in the deviation on each side.
- It multiplies `recovery_amount` after the bush premium, so it inherits the rest-and-no-net-damage condition.
- It uses the pre-step body temperature, the same convention as the A1 drain.

**Healing per rest step in a bush at level 05** (base 5.0; the fire ring settles near +6):

| Body temp | cold-only `s_c = 1/15, s_w = 0` | symmetric `s_c = s_w = 1/15` | cold-strong, warm-mild `s_c = 0.1, s_w = 1/30` |
|---|---|---|---|
| +6 (ring beside a fire) | 5.00 | 3.00 | 4.00 |
| 0 | 5.00 | 5.00 | 5.00 |
| −5 | 3.33 | 3.33 | 2.50 |
| −10 | 1.67 | 1.67 | 0.00 |
| −15 | 0.00 | 0.00 | 0.00 |

With `1/15`, healing reaches zero exactly at the death threshold.

### A5 — B1: key placement, the draw, and the level-05 range (decided: [−10, +5])

**Keys:** `thermal.random_start_body_temp` (bool) and `thermal.start_body_temp_low` / `_high`.
- They are conditional-mandatory under `thermal.enabled`; the range is read only when the flag is on.
- Validation: `min_temperature ≤ low ≤ high ≤ max_temperature`, finite.
- The draw is `uniform(body_key1, (), low, high)`. With `low == high` it returns exactly `low`.

**Level 05 uses [−10, +5] (user decision).** Recomputed at the hot corner (baseline −31, fire cell 79.73) per reviewer M2:

| Start | First step onto a single fire, baseline −31 | Baseline −30 |
|---|---|---|
| +5 | **+10.78** | +10.57 |
| +10 | **+15.18 — lethal** | +14.97 |

- **Safe single-fire ceiling:** `(15 − 2·0.04·79.73)/(1 − 2·0.06) = 9.80`, so the rejected [−10, +10] alternative would have killed agents in hot-corner episodes.
- **Merged fires** can raise the fire-cell temperature above the single-fire model; the 2026-09-19 change log measured a ring-start worst case of 12.3. That is why CP8's measurement is **adversarial**: start pinned at +5 across many resets including multi-fire layouts, as described in CP8.
- **Cold end:** 46 steps before freezing at the coldest cell; under 10 steps to rewarm at a ring.

**Consequences (accepted):**
- Wave 2 level-05 runs are no longer a like-for-like baseline.
- **Level 06 inherits B1** through `extends:` (user decision: yes).
- The M3/M4 render-fixture recordings will differ when regenerated.

### A6 — Roll-out cost of the new mandatory keys (measured 2026-09-26)

**Thermal-conditional keys** (B1 flag, B2 ×2, B4 gain; plus the conditional B1 range and B4 mode). The only raw-loaded thermal-on inputs are:
- `configs/environment/default.yaml`;
- two archived **test inputs**, `experiment/archive/thermal/campfire_world.yaml` and `campfire_world_body_temp_hidden.yaml`. They are loaded from a raw `Config` by the thermal test modules and by `scripts/fixtures/generate_{metabolic_coupling,thermal_rate_scale}_fixture.py`. Their off values are added inline (user decision, 2026-09-17 precedent), with the same comment.

The `basic/` worlds inherit.

**Unconditional key `body.healing_nutrition_cost`.** Same population as `recovery_in_bush_multiplier` on 2026-09-15:
- `grep -rl --include='*.yaml' --include='*.py' recovery_in_bush_multiplier configs tests | grep -v experiment/archive` → **34 files**: 12 under `configs/`, 22 under `tests/` (reviewer L2).
- `tests/env/fixtures/frozen_parity_worlds/environment__default.yaml`, with an "ADDED AFTER THE FREEZE" block modelled on its lines 225–233.
- The archived files that carry the inline bush line **and** are loaded by a test or fixture script. The developer lists them.

**Accepted breakage.** Other archived configs are not migrated. The developer records the before/after count from resolving every `experiment/archive/` config through `load_env_config` → `load_env_params`.

### A7 — Old runs: what would break, and the minimal compatibility step that lands first

Evaluation, replay and trajectory collection rebuild a run's world from its **own saved copy** of the settings, `results/<algo>/<run>/models/config.yaml`. Measured on 45 saved configs written since 2026-09-14:
- **12** are thermal-on: the 8 Wave 1 / Wave 2 level-05 and level-06 runs, plus 4 render-audit / smoke runs.
- **36** load at HEAD today; the Wave 2 level-05 config was checked directly.

Once C2 lands:
- the thermal-conditional keys break the 12;
- the unconditional B3 key breaks **every** saved config, including all of Wave 1 and Wave 2 (28 runs).

**User decision: build a minimal compatibility step first** (C0). It is scoped to exactly this change's keys and is designed to be absorbed by [[SAVED_RUN_CONFIG_COMPAT]], which is PLANNED, not implemented (`src/environment/saved_config_compat.py` does not exist as of 2026-09-26). C0 follows that plan's own specification (its §Design and §File Changes) so the owner can extend rather than replace it:

- **Same module path and function:** `src/environment/saved_config_compat.py`, `apply_saved_config_compat(cfg: dict, *, source: str) -> list[str]`, mutating `cfg` in place.
- **`_ERA_KEYS` holds only this change's keys:**

| Key | Supplied value | Condition | Why the value is inert |
|---|---|---|---|
| `thermal.random_start_body_temp` | `False` | only if the saved `thermal.enabled` is true | `jax_reset` static branch |
| `thermal.healing_cold_sensitivity` | `0.0` | same | `update_body` static gate |
| `thermal.healing_warm_sensitivity` | `0.0` | same | same |
| `thermal.injury_heat_exchange_gain` | `0.0` | same | same |
| `body.healing_nutrition_cost` | `0.0` | always | same |

  The conditional keys (B1 range, B4 mode, B3 shortfall) are never supplied: they are read only when their parent is non-inert.

- **Refusal rules** (from the compat plan's list):
  - (a) raise if `source` resolves under the repo's `configs/` — the live path keeps hard-erroring;
  - (b) a key already present is left alone;
  - (c) **all-or-none per gate group** — a saved thermal block carrying some of the four thermal keys but not all is an edited or foreign file, so raise;
  - (d) if the saved config lacks `thermal.enabled` altogether (a pre-thermal run), supply none of the thermal keys and let the loader fail on `thermal.enabled` as it does today. That key belongs to the compat plan's Stage 1, not here.
- **Loud:** one WARNING line naming every key supplied, its value and `source`. The function returns the sorted list, and callers print it.
- **The trajectory-store fingerprint is computed on the config before injection.** This is the compat plan's §A10 decision. It is load-bearing here: a store started before C2 must resume into the **same** directory after C2, and hashing after injection would silently fork it and restart from block 0. `collect_trajectories.py` currently hashes after its opt-in sensory shims (lines 713–745). That stays as it is; the new injection runs after the hash and after the manifest's `resolved_env_config` is taken.
- **Call sites** (the compat plan's §A4 Group 1): `scripts/eval/traj_collect/collect_trajectories.py` (699–727), `scripts/eval/eval_rollout.py` (959/1007; only when the resolved `--config` is outside `configs/`), `scripts/analysis/nmn/replay.py` (82–84), `scripts/analysis/trajectory_glm.py` (54), `scripts/analysis/supplementary/parity.py` (26–31). The developer re-greps `load_env_params` for any site added since 2026-09-10.
- **Eval recordings** (reviewer O1). `.rec.gz` files pickle `EnvParams`, and an unpickled old object lacks the new fields. Recordings are only rendered, never stepped. The developer greps for `.replace(` / `dataclasses.replace` on unpickled params before C2; the renderer already works around this at `render_recordings_v2.py:184–193` with `object.__setattr__`. No change is expected; any hit is fixed the same way.

**Failable gate (reviewer M3).** C2 may not be committed unless, **after** C2, two verbatim saved configs:
- `20260921-114858_rppo_basicq2_lvl05_t1none_s42` (Wave 1, level 05)
- `20260922-182534_rppo_bq2cover_lvl05_t1none_s42` (Wave 2, level 05)

— copied into `tests/env/fixtures/saved_run_configs/` — **fail** `load_env_params(Config(raw))` with the missing-key error **and succeed** through `apply_saved_config_compat`, supplying exactly the five keys above. They must also give the same collector fingerprint as the raw file. A committed test (`tests/env/test_saved_config_compat.py`) and CP-C0 run it.

**Pre-flight (reviewer M3).** `run_collection.py` launches per-run subprocesses that import `src/` fresh from the NAS. If C2 lands mid-collection, later runs in the same collection execute the new code, and the store mixes code versions. Before C2 is committed:
- no `collect_trajectories` / `run_collection` process may be live on nodes 109–113: `gpu-status` skill, plus `pgrep -af collect_trajectories` on each node through the same direct-SSH path, plus today's diary;
- if one is live, **C2 waits**.

### A8 — Termination reason and per-step drive terms

- **Termination reason** is available to the trainer (`Episode/Term_*`, `src/behavior/episode_metrics.py`), in the trajectory store (per episode and per step) and in eval recordings. B3 and B4 add no reason code: starvation → 2 and freezing → 5 go through existing labels.
- **Per-axis drives** are pure functions of satiation, injury and body temperature plus the run's params, so they are derivable offline.
- **Gap:** the trajectory store has **no body-temperature column** (eval recordings do). Per the user's decision this is a **separate plan**, out of scope here. It needs a `SCHEMA_VERSION` change, which requires the user's permission.

---

## Implementation Plan

### Design

The design has four mechanics, nine keys and one rule: **every new field is static** (`struct.field(pytree_node=False)`; floats `float()`-coerced, strings validated against their enum). Each mechanic sits behind a trace-time Python `if` that emits nothing at its off value.

The claim "off = today" is proved three ways:
1. rollout equality against a fixture recorded from pre-change code;
2. `jax_step` / `jax_reset` jaxpr-string equality. This is valid because no new leaves exist (reviewer M1);
3. a contrast half showing that each mechanic, once on, changes both the rollout and the jaxpr.

**D1 (B1, `jax_reset`):**

```python
if params.thermal_random_start_body_temp:          # static
    body_temp0 = jax.random.uniform(body_key1, (),
        minval=params.thermal_start_body_temp_low, maxval=params.thermal_start_body_temp_high)
else:
    body_temp0 = params.temperature_setpoint
...
body_temp=jnp.asarray(body_temp0, dtype=jnp.float32),
```

**D2 (B2, after the bush premium, `core.py:313`):**

```python
_sc = params.thermal_healing_cold_sensitivity; _sw = params.thermal_healing_warm_sensitivity
if _sc != 0.0 or _sw != 0.0:                        # static
    _dev = state.body_temp - params.temperature_setpoint
    _loss = 0.0
    if _sc != 0.0: _loss = _loss + _sc * jnp.maximum(-_dev, 0.0)
    if _sw != 0.0: _loss = _loss + _sw * jnp.maximum(_dev, 0.0)
    recovery_amount = recovery_amount * jnp.maximum(0.0, 1.0 - _loss)
```

**D3 (B3, `update_body`).** Static on `params.healing_nutrition_cost != 0.0`. On the off path the executed statements are today's, in today's order.

```python
# nutrition block: line 253's clip runs here ONLY when c == 0; else keep N_pre unclipped
# satiation block: derived here ONLY when c == 0 (else after the charge)
# injury block, B3 on:
_I_d = new_injury                                    # after the damage slice
_h_nom = jnp.where(can_recover, jnp.minimum(recovery_amount, _I_d), 0.0)
if params.healing_nutrition_shortfall == 'partial':  # static
    _h = jnp.minimum(_h_nom, jnp.maximum(_N_pre, 0.0) / params.healing_nutrition_cost)
else:
    _h = _h_nom
new_injury = jnp.clip(jnp.where(can_recover, _I_d - _h, _I_d), 0.0, params.max_injury)
# after the injury block, B3 on:
new_nutrition = jnp.clip(_N_pre - params.healing_nutrition_cost * _h, 0.0, params.max_nutrition)
<satiation derived from new_nutrition, today's two lines>
# death block, B3 on and partial:
_starved = jnp.clip(_N_pre, 0.0, params.max_nutrition) <= 0.0
done = jnp.where(_starved, True, done)               # replaces the N' <= 0 line in this mode only
```

- `update_body` returns `starved` as a new final element: `None` on every path except B3-partial.
- `jax_step` statically picks `reason = where(starved, 2, reason)` when `starved is not None`; otherwise it keeps today's line (`core.py:999`).
- The ORDER comment at `core.py:184–193` is rewritten.
- `calculate_drive` is not touched.

**D4 (B4, body-temperature block, `core.py:385–409`):**

```python
if params.thermal_injury_heat_exchange_gain != 0.0:  # static
    _boost = params.thermal_k_exchange * (1.0 + params.thermal_injury_heat_exchange_gain
                                          * state.injury_level / params.max_injury)
    if params.thermal_injury_heat_exchange_mode == 'both':   # static
        _k_ex = _boost
    else:                                                     # 'cooling_only'
        _k_ex = jnp.where(cell_temp < state.body_temp, _boost, params.thermal_k_exchange)
else:
    _k_ex = params.thermal_k_exchange
```

`_k_ex` replaces `params.thermal_k_exchange` in both the 1.0/1.0 branch and the scaled branch.

**Loader, B4 (`g > 0`):**
- Refuse if `with_injury` is false (reviewer L3).
- Stability checks at `k_ex·(1+g)` for both scales.
- A second `_check_thermal_structure` pass at full injury. In `cooling_only` mode the boosted coefficient is used only for rings on the cooling side, decided by the sign of `k_loss·(T_set − T_amb) + k_met`. In `both` mode it is used for every ring. The failure message is prefixed "at full injury".
- In `both` mode only: the first-step-onto-fire check of §A2, naming both keys in the error.

**Loader validation table:**

| Key | Read when | Inert / sentinel | Validation |
|---|---|---|---|
| `thermal.random_start_body_temp` | `thermal.enabled` | `false` | bool |
| `thermal.start_body_temp_low` / `_high` | flag true | `(setpoint, setpoint)`; `(0.0, 0.0)` if thermal off | `min_T ≤ low ≤ high ≤ max_T`, finite |
| `thermal.healing_cold_sensitivity` | `thermal.enabled` | `0.0` | `≥ 0`, not NaN |
| `thermal.healing_warm_sensitivity` | `thermal.enabled` | `0.0` | `≥ 0`, not NaN |
| `thermal.injury_heat_exchange_gain` | `thermal.enabled` | `0.0` | `≥ 0`, not NaN; `with_injury` if `> 0`; bounds and checks above |
| `thermal.injury_heat_exchange_mode` | gain `> 0` | `cooling_only` | ∈ {`cooling_only`, `both`} |
| `body.healing_nutrition_cost` | always | `0.0` | `≥ 0`, not NaN; `with_nutrition ∧ with_injury` if `> 0` |
| `body.healing_nutrition_shortfall` | cost `> 0` | `partial` | ∈ {`partial`, `full`} |

### File Changes

**Commit C1 — pre-change fixture (first; no `src/` change)**

`scripts/fixtures/generate_body_mechanics_parity_fixture.py` (NEW), modelled on `generate_thermal_rate_scale_fixture.py`:
- `--src-root` is required; `JAX_PLATFORMS=cpu` is set before any jax import; `_provenance_sha` is stamped.
- **Worlds:** basic/05 and basic/04, loaded through `load_env_config` → `load_env_params` from the worktree.
- **Episodes:** 16 seeds (0–15), up to 300 steps each.
- **Actions:** deterministic. Rest (4) when `(t // 20) % 3 == 2`; otherwise `randint(fold_in(PRNGKey(1234), seed·1000 + t), 0, 6)`.
- **Records:** every `EnvState` leaf per step (including `key` and `body_temp`), `reward`, `done`, every numeric `info` entry (`termination_reason`, `drive_*`, `damage`, `rested`, `ate_food`, `agent_in_bush`), `get_observation`, and the `jax_step` / `jax_reset` jaxpr SHA-1s per world.
- **Also stamps** the full resolved config dict of each world as canonical YAML (reviewer O3).
- **Refuses to write** unless each world has at least one rest step with healing, at least one rest step in a bush with healing, at least one real death, and at least one eat event; for level 05 the body temperature must also span at least 5°. It prints the counts.

Output: `tests/env/fixtures/body_mechanics_parity/pre_change_rollouts.npz`, generated via `git worktree add --detach /tmp/gwp_bodymech_baseline <SHA>` → generator → `git worktree remove`.

`docs/environment/SCRIPTS_DEPENDENCY_MAP.md`: a row for the generator.

**Commit C0 — minimal saved-config compatibility step (before C2)**

- `src/environment/saved_config_compat.py` (NEW), per §A7. The docstring states that it is the first slice of [[SAVED_RUN_CONFIG_COMPAT]], and that `_ERA_KEYS` rows need a value, the era commit and the branch that makes the value inert (the compat plan's rule).
  - **If that module exists by the time C0 is implemented** (the other session landed first), add the five rows to its table instead of creating the file, and note it in the Implementation Report.
- **Wire the five call sites of §A7.** Fingerprint and manifest `resolved_env_config` are taken **before** injection. Each site prints the returned list.
- `tests/env/fixtures/saved_run_configs/` (NEW): the two saved configs copied **verbatim**, with a README naming the source run and the date copied.
- `tests/env/test_saved_config_compat.py` (NEW). It fails rather than skips if a fixture is missing.
  - (i) Both fixtures load through the shim, returning exactly the five keys (the negative half of the gate becomes active after C2; before C2 the test asserts that injection returns the five keys and the load succeeds).
  - (ii) After C2: the raw load raises the missing-key error.
  - (iii) A `source` under `configs/` raises.
  - (iv) A thermal block carrying two of the four thermal keys raises.
  - (v) Present keys are not overwritten.
  - (vi) The collector's fingerprint of each fixture equals `env_fingerprint(raw)`.
  - (vii) A thermal-off saved config gets only `body.healing_nutrition_cost`.
- `docs/environment/SCRIPTS_DEPENDENCY_MAP.md`: note the new `src/` import in the five scripts.

**Commit C2 — mechanics, keys, tests, docs (everything inert).** Blocked on the M3 gate and the pre-flight in §A7.

`src/environment/state.py`:
- `healing_nutrition_cost: float` and `healing_nutrition_shortfall: str` next to `recovery_in_bush_multiplier`, both static.
- In the thermal block: `thermal_random_start_body_temp: bool`, `thermal_start_body_temp_low: float`, `thermal_start_body_temp_high: float`, `thermal_healing_cold_sensitivity: float`, `thermal_healing_warm_sensitivity: float`, `thermal_injury_heat_exchange_gain: float`, `thermal_injury_heat_exchange_mode: str`. **All static.**
- A comment on why static (M1).
- Update the `body_temp` comment.

`src/environment/config_loader.py`:
- Thermal-on arm, after the rate-scale block (~1591): B1, B2, B4 per the table, the B4 stability extension and the `both`-mode transient check.
- Thermal-off arm (1647–1672): sentinels.
- Structure-check call (~2019): the full-injury pass when `g > 0`.
- Body block (after 2233): B3 keys.
- `EnvParams(...)`: the nine fields.

`src/environment/core.py`:
- D1 (1775–1792, 2061–2064);
- D2, D3, D4 in `update_body`, plus the `starved` return;
- `jax_step`: the static reason-2 selection only;
- `calculate_drive` untouched.

`configs/environment/default.yaml`, under `thermal:` after `metabolic_coupling_rate`:

```yaml
  # B1 — random starting body temperature. Read only when thermal.enabled; the range only
  # when the flag is true. No fixed-start key: pin a start with low == high.
  random_start_body_temp: false
  start_body_temp_low: 0.0
  start_body_temp_high: 0.0
  # B2 — healing needs warmth. Fraction of injury recovery lost per degree the body is
  # below (cold) / above (warm) temperature_setpoint. Equal = symmetric; both 0.0 = off.
  healing_cold_sensitivity: 0.0
  healing_warm_sensitivity: 0.0
  # B4 — injury speeds heat exchange: k_exchange x (1 + gain*injury/max_injury). 0.0 = off.
  # Scales k_exchange, NOT k_loss (k_loss is the body's defence toward setpoint).
  injury_heat_exchange_gain: 0.0
  # Read only when gain > 0. cooling_only: boost only while the cell is colder than the
  # body. both: also at a fire (the loader then checks the first step onto a fire).
  injury_heat_exchange_mode: cooling_only
```

`configs/environment/default.yaml`, under `body:` after `recovery_in_bush_multiplier`:

```yaml
  # B3 — healing uses energy: nutrition per injury point healed, charged before the single
  # clip. 0.0 = off. Requires with_nutrition and with_injury.
  healing_nutrition_cost: 0.0
  # Read only when healing_nutrition_cost > 0. partial: heal only what remaining nutrition
  # pays for, and the charge never kills. full: heal fully, and a shortfall starves.
  healing_nutrition_shortfall: partial
```

**Raw-loaded configs** (§A6):
- the thermal keys go into the two archived campfire test inputs;
- `body.healing_nutrition_cost: 0.0` goes into the 34-file set, the frozen parity world, and the archived test inputs the developer lists.

`tests/env/test_body_mechanics_parity.py` (NEW):
- CPU only. It **fails, never skips**, on a missing fixture, config or provenance.
- Loads both worlds at HEAD through the resolving loader. After C3, it sets `thermal.random_start_body_temp: false` in memory for basic/05 (and records that it did).
- **Named drift check (O3):** the resolved dict minus the nine new keys must equal the fixture's stamped dict, so unrelated config drift fails with its own message.
- `np.array_equal` on every recorded array.
- `jax_step` / `jax_reset` jaxpr SHA-1 equality.
- **Contrast half:** B1 [−5, −5]; B2 `s_c = 0.1`; B2 `s_w = 0.1` in a warm scene; B3 `c = 1` in each shortfall mode, on both worlds; B4 `g = 1` in each mode. Each must change the rollout and the jaxpr.
- Re-asserts the coverage counts.

`tests/env/test_body_mechanics_units.py` (NEW). Hand-computed literals; `atol = 1e-5`; exact equality for off cases.

- **B1**
  - T-B1-1: off → setpoint; other reset leaves unchanged over 32 keys.
  - T-B1-2: `low == high == −7` → exactly −7.
  - T-B1-3: [−10, 5] over 1000 keys → in range, mean −2.5 ± 0.5, and every other leaf equals the flag-off reset (stream isolation).
  - T-B1-4: loader refusals, and thermal-off loads with all thermal keys deleted.
- **B2** (resting in a bush, no damage, injury 50, `s_c = 0.1`, `s_w = 0.05`)
  - T-B2-1: T = 0 → 45.0; −5 → 47.5; −10 → 50.0; +6 → 46.5; −30 → 50.0.
  - T-B2-2: `s_w = 0` → +6 gives 45.0.
  - T-B2-3: `s_c = 0`, `s_w = 0.05` → −5 gives 45.0.
  - T-B2-4: both 0 → today's value exactly.
  - T-B2-5: not resting, or taking damage → no recovery.
  - T-B2-6: negative / NaN → `ValueError`.
- **B3** (`c = 1`, in a bush, T = 0, B2 off, metabolic 1)
  - T-B3-1: `full`, N 100, I 50 → N 94, I 45.
  - T-B3-2: `full`, I 3 → N 96, I 0.
  - T-B3-3: I 0 → N 99 in both modes.
  - T-B3-4: `full`, N 4, I 50 → N 0, I 45, `done`, reason 2.
  - T-B3-5: `partial`, N 4, I 50 → N 0 (≤ 1e-6), I 47, **not** `done`, reason 0. The next rest step with no food → `done`, reason 2, I 47.
  - T-B3-6: `partial`, N 0.5 → h 0, `done`, reason 2.
  - T-B3-7: auto-eat world, rest on food in the open, I 50, N 196, gain 6, eat cost 1 → 199.8 and no over-eating death; with `c = 0` → 200 and death.
  - T-B3-8: A1 coupling rate 1, T = −10 → 93.8.
  - T-B3-9: B2 `s_c = 0.1` at T = −5 → h 2.5 → N 96.5.
  - T-B3-10: a damage step pushing injury past the max → no charge.
  - T-B3-11: loader — `c > 0` without `with_injury` or `with_nutrition` → `ValueError`; bad shortfall string → `ValueError`; cost missing → `ValueError`; shortfall missing with `c > 0` → `ValueError`; shortfall missing with `c = 0` → loads.
- **B4** (cell −30, T = 0, level-05 scales)
  - T-B4-1: `g = 1`, I 50 → −0.45; I 100 → −0.60; I 0 → −0.30, exactly equal to `g = 0`.
  - T-B4-2: scales 1/1, I 50 → −1.8.
  - T-B4-3: warm cell +10, I 50 → +0.8 in `cooling_only` (exactly the `g = 0` value), +1.2 in `both`.
  - T-B4-4: settle point at cell −10, I 100, `g = 1`, scales 1/1 → −8.0.
  - T-B4-5: `cooling_only`, `g = 10.9` loads; `g = 11.5` refused.
  - T-B4-6: `both` at level 05, `g = 1` → refused by the first-step check; the developer computes the level-05 `both` threshold from the loader model and tests at 0.9× (loads) and 1.1× (refused).
  - T-B4-7: synthetic world with a ring survivable at injury 0 but lethal at full injury → refused "at full injury".
  - T-B4-8: `g > 0` with `with_injury: false` → refused.
  - T-B4-9: bad mode string → refused.
- **Graph-identity** tests in the style of `test_recovery_in_bush.py`: `state.body_temp` is unused by the injury block at B2 off; `state.injury_level` is unused by the thermal block at B4 off. The leaf is located positionally.

**Must stay green unmodified:** `test_thermal_parity`, `test_unified_parity`, `test_visual_parity`, `test_metabolic_coupling`, `test_thermal_rate_scales`, `test_recovery_in_bush`, `test_two_sided_nutrition`, `test_thermal_reward_gate` (**no regeneration**), `test_no_recompile`, `test_truncation_not_death`, `test_config_layer_silent_failures_20260723`, `test_dashboard_layout`.

**Docs, in the same commit:**
- `CONFIG_GUIDE.md` §5: the new keys, the conditional reads, "pin with `low == high`", and the saved-config compat step and its rule.
- `02_config_schema.md`: nine rows.
- `05_body_homeostasis.md`: the order, B2, B3 (both modes, the death labels, the alive-at-0 state), B4 (why `k_exchange`; the modes) and B1.
- `06_reward_and_termination.md`: reasons 2 and 5 reused; partial-mode starvation is judged before the charge.
- `CONFIG_CRITICAL_SETTINGS.md`: registry rows, plus a change-log entry "new keys, shipped inert" carrying the jaxpr SHAs, the parity-family counts, the archived before/after counts, the saved-run counts and the compat step.

**Commit C3 — enable B1 in level 05 (the only behaviour change).** `configs/environment/experiment/basic/05-campfire_thermal_10x10.yaml`:

```yaml
thermal:
  enabled: true
  # B1 — random starting body temperature, a standard internal state of this world
  # (decided 2026-09-26). Upper end +5: the first step onto a single hot-corner fire lands
  # at +10.78 (< +15); +10 would reach +15.18 and kill. Level 06 inherits this.
  random_start_body_temp: true
  start_body_temp_low: -10.0
  start_body_temp_high: 5.0
```

Also:
- update the header list of differences from `default.yaml` in the level-05 file, and add a header note in the level-06 file that it inherits B1;
- `CONFIG_CRITICAL_SETTINGS.md` change log: B1 enabled in levels 05 and 06; Wave 2 level-05 and level-06 runs are no longer like-for-like baselines; the CP8 measurements.

---

## Hand-off to the owner of [[SAVED_RUN_CONFIG_COMPAT]]

This section is for the session that owns that plan; this plan does not edit it.

C0 creates, or extends, `src/environment/saved_config_compat.py` with the API and refusal rules that plan specifies. Its `_ERA_KEYS` holds **only** the five rows of §A7, each with the branch that makes it inert. The parity instrument that plan demands for those rows is this plan's `tests/env/test_body_mechanics_parity.py`.

To absorb it:
1. Add the Stage 1 / 2 rows (`thermal.enabled`, the four sensory keys).
2. Keep the "thermal keys only when `thermal.enabled` is true" condition and the all-or-none group rule.
3. Keep the pre-injection fingerprint (that plan's own §A10).
4. Move the two `tests/env/fixtures/saved_run_configs/` files into that plan's era-representative fixture set.

**Not done here, deliberately:**
- the manifest `saved_config_compat` field (that plan's §A10);
- `thermal.enabled` and the sensory keys;
- the opt-in vs automatic debate (C0 is automatic at saved-path sites, following that plan's recommendation, and narrow).

The hand-off is delivered by message through the coordinator, and a signed "Feedback from `senior-developer`" block may be appended to that doc once its session has finished editing it.

---

## Still open for the user

1. **Partial mode leaves a new state reachable.** An agent can be alive at nutrition 0 after spending its last reserves on healing; it then starves on the next step unless it eats. This follows directly from "no death from the charge itself". Confirm that this is what is wanted. The alternative is to judge starvation after the charge, but then an emptying charge kills, which contradicts the spec.
2. **No loader guard for B1's hot start.** The first-step-onto-fire check runs only for B4 `both` mode, as specified. B1's start range is protected by measurement (CP8), not by a loader refusal, so a variant world that raises `start_body_temp_high` above about +9.8 at level-05 temperatures would load and silently break the fire calibration. Should the same check also run whenever B1 is on?
3. **Carried over, not re-asked:** the trajectory-store body-temperature column is a separate plan and needs a `SCHEMA_VERSION` decision there.

---

## Out of scope

- The injury × starting-fullness probe scenes (a later plan).
- The level-05 variant worlds, including the B3-`partial` world (`experiment-designer`, outside `basic/`).
- The trajectory-store body-temperature column (a separate plan).
- `calculate_drive` or the reward.
- The general compatibility layer beyond these five keys.

---

## Checkpoints

- [ ] **CP1 — C1 first.** Fixture from a pre-change worktree; coverage counts non-zero; `_provenance_sha` and the stamped config recorded.
- [ ] **CP-C0 — compat.** `test_saved_config_compat.py` green. At C0 time the shim returns the five keys and the fingerprint is unchanged. Recheck after C2 (M3 gate): the raw loads of both fixtures **fail** and the shim loads **succeed**. Also run the shim against the live `results/…/models/config.yaml` of both runs and against one Wave 1 level-06 run. The printed key lists go in the report.
- [ ] **CP2 — B1 stream isolation** (T-B1-3).
- [ ] **CP3 — Off = today, three ways.** Parity test green, including jaxpr SHA equality and the contrast half. SHAs recorded.
- [ ] **CP4 — B3 off path.** `update_body` jaxpr string identical before and after at `c = 0` on both worlds.
- [ ] **CP5 — Unit tests** green.
- [ ] **CP6 — Loader.** Every key raises when missing within its read condition; B4 bounds, structure pass, `both` transient and `with_injury` refusal exercised; the level-05 structure check passes at `g` ∈ {0, 1, 2} in `cooling_only`.
- [ ] **CP7 — Roll-out and pre-flight.** `tests/` green on CPU with per-family pass/skip counts compared to the 2026-09-17 entry. Archived before/after counts reported. **Immediately before committing C2:** the live-collection pre-flight of §A7 run and its output pasted into the report; any live process means C2 waits.
- [ ] **CP8 — Level 05 after C3, adversarial.**
  - The loader resolves B1 on with [−10, 5] for levels 05 and 06.
  - (a) 600 real resets at the configured range → every start within range.
  - (b) **Pinned `low == high == +5`**, at least 600 real resets, with the per-episode fire count logged so multi-fire layouts are visibly included. For every active fire cell, compute the first step onto it from +5 using that reset's real field value: `5 + s_w·(k_ex·(F − 5) − k_loss·5)`. Report the max, which must be < +15, and the max `F`.
  - (c) The same from the loader-model ring settle, as a cross-check against the 09-19 figure of 12.3.
  - (d) `tests/` green after C3 (reviewer L4), including `test_truncation_not_death.py`.
- [ ] **CP9 — Reward untouched.** No diff inside `calculate_drive`; `test_thermal_reward_gate.py` green without regeneration.
- [ ] **CP10 — Speed.** Steps per second before/after on levels 05 and 04: same node, GPU and seed, with a budget past warm-up.
- [ ] **CP11 — Docs** as listed, in the same commits.
- [ ] **CP12 — Hand-offs.**
  - `bug-curator`: the mandatory-key roll-out row, and "B3 partial starvation shares one predicate".
  - Compat-plan owner: the §Hand-off section.
  - `experiment-designer`: the §A0 observability caveat, and that the variant must state `healing_nutrition_shortfall: partial` explicitly.

---

## Implementation Report

> **Implemented by**: [agent/person]
> **Date**: [date]

<!-- Filled by `developer`. Must include: pre-change SHA + fixture coverage counts (CP1); compat gate
     results and printed key lists (CP-C0); jaxpr SHA-1s (CP3/CP4); files that received inert keys;
     parity-family pass/skip counts; archived before/after counts; the live-collection pre-flight output
     (CP7); the CP8 adversarial numbers (max first-step temperature, max F, fire-count distribution);
     SPS before/after (CP10); deviations and why. -->

## Verification Report

> **Verified by**: [agent/person]
> **Date**: [date]

| File | Change | Status | Notes |
|------|--------|:------:|-------|
| | | | |

**Conclusion**: [one-line summary]

---

## Feedback from plan-reviewer

> **Reviewed**: 2026-09-26 at commit `958f8c37` · **Verdict**: **SOUND WITH CONCERNS** — no Critical finding, so no `docs/reviews/` file. Three Moderate findings to resolve before C2; the rest are Low or Open.
>
> Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run · 🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

### What was checked against the code and holds

- **Off path is the same graph in the same order.** D1, D2 and D4 are pure trace-time branches. D3 was read against `core.py:253`, `258–263`, `316–319`: on the off path the clip stays inside `if params.with_nutrition:`, the satiation lines stay where they are, and the injury block is unchanged; the `_injury_before_recovery` alias is a name binding. The *instrument* for proving it has a defect (M1 below), but the design claim is right.
- **Not circular.** `_CONFIGS_ROOT` is `dirname(config_loader.__file__)/../../configs` (`config_loader.py:29`), so a generator that imports `src` from `--src-root` resolves `extends:` inside the worktree, not this checkout. `train.py:70,202,527` builds the world with the same `load_env_config` → `load_env_params` the test uses.
- **`body_key1` is split and never read** — the only reference is the split at `core.py:1775`.
- **B3 masking and labels.** `damage ≥ 0` so `applied_inc ≥ 0`, hence `can_recover ⇒ applied_inc == 0 ⇒ injury_before == prev_injury ≤ max_injury`: the upper clip cannot fire under the mask, and `healed = min(recovery, prev_injury)`. Reasons 2 and 5 are reused at `core.py:999` / `:1014` with no new predicate. The "only in auto-eat worlds" claim for T-B3-6 holds: `rested = rest_action_enabled ∧ action == 4` (`core.py:952`) and `ate_food_auto` requires `not eat_action_enabled` (`core.py:874–876`).
- **B4 arithmetic.** Recomputed every number in §A2 and T-B4-1…4 (settle −20 / −22.5 / −24; first step −0.30 / −0.45 / −0.60; ring +6.9 at g = 1; g ≤ 11). `_check_thermal_structure` takes `k_exchange` as a keyword (`config_loader.py:530`), so the second call at full injury is feasible. The stability checks are where §A1 says (`:1553–1591`).
- **Project rules.** `get_mandatory` throughout; every maintenance-contract doc is paired in the same commit; frontmatter present; the archive carve-out for test inputs follows the recorded 2026-09-15 / 09-17 precedent; `SCHEMA_VERSION` is a real in-code scheme (`trajectory_store.py:115–116`, reader hard-fails at `:525`), and the bump is explicitly gated on user permission (D-L) — compliant with the no-versions rule. No `git clean` / force-checkout anywhere; `worktree add --detach` + `remove` is safe.
- **Prior art.** No doc under `docs/` names any of the six keys; the KNOWN_BUGS rows cited in §A0 exist and say what the plan says they say; all four wiki entries exist.

### Findings

| # | Sev | Location | Issue | Suggested fix | Owner |
|---|---|---|---|---|---|
| M1 | 🟡 | §Design (state.py: `thermal_start_body_temp_low/high` **traced**); §File Changes → parity test (jaxpr SHA-1 equality); CP3; CP4 | **The jaxpr-SHA assertion fails by construction on the inert path.** Every pytree leaf of `params` becomes an input variable of the jaxpr whether or not it is used, and all later variables are renumbered. Verified in this env with a two-field vs four-field `flax.struct` dataclass: `str(jaxpr)` differs, `eqns` are identical. Two new traced floats therefore change `sha1(str(make_jaxpr(jax_step)))`, `jax_reset` and `update_body` (CP4) even when no operation changed — and the contrast half ("SHA differs when on") becomes vacuous, because the SHA already differs when off. The 2026-09-17 SHAs held only because those keys were static. | Either make the two range keys `struct.field(pytree_node=False)` + `float()`-coerced (they are config constants; pinning with `low == high` is a static value anyway — and then all six keys are static, one rule), **or** compare `[str(e) for e in jaxpr.eqns]` / the precedent's `_count_primitives` (`tests/env/test_thermal_rate_scales.py:244`) instead of `str(jaxpr)`. Say which in §Design so the developer does not discover it as a red gate. | `senior-developer` (plan) → `developer` |
| M2 | 🟡 | §A1 (ring +5.75, fire settle +51.4 are baseline −30), §A5 and D-B1 (`79.7` is the baseline −31 fire cell) | **Two baselines are mixed, and the [−10, +10] alternative is not a knife-edge — it is lethal at the hot corner.** Real loader field at baseline −31: fire cell 79.7, first step from +10 = **+15.18 > 15**; at −30 it is +14.97. From +5 the first step is 10.78 (−31) / 10.57 (−30), so the proposed range survives the single-fire case. But the 2026-09-19 change-log entry records that merged fires raised the ring-start worst case from ~11.2 to **12.3** (and to +16.3 before `min_fire_separation` went to 4), so the multi-fire corner is the one that decides D-B1, and 600 *uniform* draws over [−10, 5] will almost never place a +5 start beside a merged pair. | Restate the D-B1 table at baseline −31 and say [−10, +10] kills in hot-corner episodes. Make CP8's measurement adversarial, not uniform: pin the start at the upper end (`low == high == +5`, the plan's own pin mechanism), sweep 600 resets, and report the max first-step-onto-fire temperature from that pinned start. | `senior-developer` |
| M3 | 🟡 | §A7, D-COMPAT, CP12 | **The recommended route (a) has no step that can fail.** It depends on `src/environment/saved_config_compat.py`, which does not exist, in a doc another session is editing right now (`git status` shows it `MM`), and the plan's hand-off is "a message". If (a) is chosen and C2 lands first anyway, every Wave 1 / Wave 2 saved config (28 runs) stops loading and the untracked 14-run × 1M-episode collection on nodes 109–113 dies at resume — days of GPU time, not a wrong conclusion. | State explicitly that **C2 is blocked on the user's D-COMPAT choice**. Under (a): add to CP7 "`load_env_params` through the shim succeeds on one Wave 1 and one Wave 2 saved `models/config.yaml`" — a check that can fail. Under (b): add to CP1/CP7 a pre-flight that no `collect_trajectories` process is live on 109–113 (`gpu-status` + diary) before C2 is committed. | user (decision) → `senior-developer` |
| L1 | 🟢 | T-B4-5 (`g = 11 → loads`) | The bound is exactly 1.0 at g = 11; whether float64 lands on 1.0 or 1.0000000000000002 depends on the association order the developer writes. A boundary case is a flaky test. | Test g = 10.9 loads / g = 11.5 refuses, or pin the expression order in the plan. | `developer` |
| L2 | 🟢 | §A6 "36 files" | Measured 34 with `--include='*.yaml' --include='*.py'`; the plan's bare `grep -rl` also counts `.md`/binary hits. Harmless — the developer re-measures — but the number is quoted as a population. | Re-state with the exact grep. | `developer` |
| L3 | 🟢 | §Design loader table, B4 | `injury_heat_exchange_gain > 0` with `with_injury: false` loads and is silently inert (`injury_level` stays 0). B3 refuses the analogous case. | Refuse, or document the asymmetry in `02_config_schema.md`. | `senior-developer` |
| L4 | 🟢 | C3 / CP8 | `tests/env/test_truncation_not_death.py` builds basic/05 by path and resets with fixed seeds; C3 changes that world's reset. The "must stay green unmodified" list sits under C2 only. Probably green (`max_steps` 3), but nothing in CP8 runs it. | Add "`tests/` green after C3" to CP8. | `developer` |
| O1 | ❓ | §A7 (compat surface) | Eval recordings (`.rec.gz`) pickle `EnvParams`. Six new fields on the class mean any `replace()` / rebuild on an old recording's params raises — `scripts/eval/render_recordings_v2.py:184–193` already works around exactly this for `thermal_warming_rate_scale`. Recordings are not listed as a compatibility surface. | `developer`: grep for `.replace(` / `dataclasses.replace` on unpickled params before C2; note recordings in §A7. | `developer` |
| O2 | ❓ | §A7 counts (12 / 45, 36 / 45) | Not re-verified here; CP7 re-measures. Fine as stated. | — | — |
| O3 | ❓ | C1 / parity test | The fixture rolls out the **worktree's** basic/04 and basic/05; the test rolls out **HEAD's**. Parallel sessions edit `configs/`. The test asserts the six new keys resolve inert but not that every *other* key is unchanged, so unrelated config drift would surface as an unexplained rollout mismatch. | Have the generator stamp the resolved config dict (or its hash) and have the test compare it minus the six new keys — drift becomes a named failure. | `developer` |

### Assumptions the plan rests on

| Assumption | Status |
|---|---|
| Unused pytree leaves do not change the jaxpr string | **False** (M1) — verified empirically |
| `body_key1` is unused | Verified (`core.py:1775` only) |
| The trainer resolves `extends:` with the same loader the test uses | Verified (`train.py:70,202,527`) |
| `_CONFIGS_ROOT` follows the imported module, so `--src-root` is not circular | Verified (`config_loader.py:29`) |
| Thermal-conditional keys need only `default.yaml` + the two archived campfire files | Verified — `warming_rate_scale` appears inline in exactly those config files (plus the unreferenced `archive/basic_vec8/default.yaml`) |
| Fire-cell numbers in §A5 are the worst-case corner | Partly — mixed baselines (M2) |
| The compat layer will exist before C2 | Unverified; module absent, doc in flight (M3) |
| basic/04 and basic/05 do not drift between the pre-change SHA and HEAD | Unverified (O3) |
| Saved-config counts in §A7 | Unverified here (O2) |

### Cost of being wrong

No data-loss path exists in this plan. If M1 is left as written, the parity gate goes red on the inert path and the developer either loses an hour or weakens it — a confused afternoon. If D-COMPAT is mishandled, 28 finished runs and a 14-run million-episode collection become un-analysable by current code until the compat layer lands: days of GPU time to re-collect, not a wrong conclusion. If D-B1 is decided from the mixed-baseline table and lands on [−10, +10], the "first step onto a fire is survivable" calibration silently fails in hot-corner episodes and the B1 training world is mis-specified from the first launch.

*Reviewed by: plan-reviewer*

---

## Revision log

### Revision 2 — 2026-09-26, the user's decisions plus the `plan-reviewer` and `math-reviewer` findings

**User rule:** every interaction is configurable. It produced two new mode keys (`injury_heat_exchange_mode`, `healing_nutrition_shortfall`), and B2's single sensitivity was split into cold and warm.

| Item | Resolution |
|---|---|
| D-B1 | [−10, +5] adopted (C3); level 06 inherits it (§A5). |
| D-B2 | Separate cold and warm sensitivities; table recomputed (§A4). |
| D-B3 | `healing_nutrition_shortfall: partial \| full`; exact formula, clip order and labels in §A3; `partial` starvation judged before the charge and shared through the returned predicate. |
| D-B4 | `k_exchange` confirmed; `injury_heat_exchange_mode: cooling_only \| both`, default `cooling_only`; `both` has the first-step check (§A2). |
| D-COMPAT | Minimal compat step C0 lands first, with a failable gate and a pre-flight (§A7). |
| D-store | Moved to a separate plan; Part L and C4 removed. |
| D-archived | Kept (§A6). |
| M1 | All nine new fields are static, so no new jaxpr leaves; SHA equality is valid; stated in §A1 and §Design. |
| M2 | Numbers restated at −31: +5 → +10.78, +10 → +15.18 (lethal), safe single-fire ceiling 9.80; CP8 is adversarial with a pinned +5 start across multi-fire resets. |
| M3 | C2 blocked on the CP-C0 gate and the CP7 pre-flight. |
| L1 | 10.9 / 11.5. |
| L2 | Exact grep, 34 files. |
| L3 | B4 refused without `with_injury`. |
| L4 | CP8(d). |
| O1 | Grep step in §A7. |
| O3 | Stamped config and named drift check. |
| Math: ring numbers | Labelled as loader-model; measured-state range 5.56–6.78 noted (§A1). |
| Math: same-side | Stated (§A2). |
| Math: redundant `max(·,0)` | Removed. `h_nom = min(r, I_d)` under the mask replaces "before − after". |

