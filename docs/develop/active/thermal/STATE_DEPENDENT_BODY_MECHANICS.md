---
title: "Four body mechanics that make the best action depend on combinations of internal states (level 05)"
topic: sensors
status: active
created: 2026-09-26
last_updated: 2026-09-26
aliases: [state_dependent_body_mechanics]
---

# Four body mechanics that make the best action depend on combinations of internal states (level 05)

> **Status**: PLANNED, Revision 3 (2026-09-26). Adds B5 (healing speed depends on nutrition). Changes B1 and B4 warnings from load refusals to logged, informational messages (user: "allow, make visible"). Folds in the `plan-reviewer` addendum (N1–N6). See §Revision log. Waiting on §Still open for the user, then approval.
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
- **B5**: healing is faster when the agent is well fed and slower when it is hungry. As food runs low, healing (and therefore B3's spending of food on healing) slows down. Whether being over-full also slows healing is a separate setting.

Where a mechanic can make a situation lethal — for example, a warm random start followed by a step onto a fire — the world is **allowed** to be that way. The loader prints the worst case so it is visible; it does not refuse the world.

Following the user's rule for this work, every interaction is a config setting; no behaviour choice is hard-coded. Each setting has an exact "off" value at which the environment behaves as it does today, byte for byte, and a test compares against rollouts recorded from the current code.

**What is switched on:**
- B1 is enabled in level 05, and level 06 inherits it.
- B3 will be used by one variant world, written later by `experiment-designer`.
- B2, B4 and B5 ship off. B5 stays off in the first test batch unless the parameter study (below) says otherwise.

Choosing parameter ranges for B1–B5 is a separate, later design step: a scripted, agent-free simulation of nutrition, injury and temperature under these mechanics, run before any training. It is not part of this plan (§Out of scope).

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

The stability bound **stays a refusal**. It is not a statement about outcomes: above it the discrete update overshoots its own settling point and oscillates, which is a numerical defect. The load-time structure check also relies on the approach being monotone.

**Worst-case first step onto a fire (`both` mode; math-reviewer's expression). Logged, not refused** — Revision 3, aligned with the user's "allow, make visible":

$$
T_{1} = T_{high} + s_w\bigl(k_{ex}(1+g)(F_{max} - T_{high}) - k_{loss}(T_{high} - T_{set}) + k_{met}\bigr)
$$

- `F_max` is the model's fire-cell temperature at the hottest corner (`ratio_high·|default_temp_low|` through `_thermal_single_fire_field`).
- `T_high = max(B1 upper start (or T_set if B1 is off), full-injury ring equilibrium)`. The ring term is this plan's addition: a body settled beside a fire is the calibrated starting point for "first step onto the fire".
- The loader always logs `T_1`. When `T_1 > T_max` it logs at WARNING level ("an injured agent can die on its first step onto a fire — allowed by configuration"); otherwise at INFO level.
- Why the reviewer's stronger option is not taken: `plan-reviewer`'s addendum (N6) recommended a refusal. The user decided against it. A lethal step onto a fire is a behavioural outcome the agent can learn to avoid, not a broken world. Merged fires are not in the single-fire model; CP8 measures them.

Level 05 (baseline −31, `F_max` 79.73):

| g | ring equilibrium at full injury | `T_1` from `max(+5, ring)` | log level |
|---|---|---|---|
| 0 | +5.94 | +11.61 | INFO |
| 0.5 | +6.68 | +15.18 | WARNING (lethal possible) |
| 1 | +7.13 | +18.46 | WARNING (lethal possible) |

**The full-injury structure pass follows the same principle.** When `g > 0`, the second `_check_thermal_structure` evaluation at full injury **logs** its verdict (WARNING when the ring is lethal for a fully injured agent) instead of raising. The injury-0 pass is the existing check; it is untouched and **still refuses**. That refusal is existing project policy for worlds where the task itself is lost, and this plan does not change it.

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

### A4b — B5: healing speed depends on food energy (Revision 3)

**What it models.** A well-fed body heals at full speed; a hungry one heals slower. The user's rationale is self-balancing with B3: as nutrition falls, healing slows, so B3's spending of nutrition on healing slows too. §A4b's simulation qualifies that claim (see "What the self-balancing buys" below).

**Defined on nutrition, not satiation.**
- Nutrition (0–200) is the physical energy store that B3 charges, so the rate and the bill read the same quantity.
- Satiation is a derived, subjective reading of it (`S = max_S·(N/max_N)^k`). At level 05, `k = 1` and `max_S = max_N = 200`, so the two are numerically identical there. In a world with `k ≠ 1` they differ, and nutrition is the consistent choice.
- It uses the **pre-step** nutrition (`state.nutrition`), the same convention as B2 (pre-step temperature) and B4 (pre-step injury).

**Form: a low-side ramp times an optional high-side ramp**, both in [0, 1]:

$$
f_{hunger}(N) = f_h + (1-f_h)\,\mathrm{clip}\!\Bigl(\frac{N - N_{lo}}{N_{hi} - N_{lo}},\,0,\,1\Bigr),\qquad
f_{over}(N) = 1 - (1-f_o)\,\mathrm{clip}\!\Bigl(\frac{N - N_{os}}{N_{max} - N_{os}},\,0,\,1\Bigr)
$$

$$
r \leftarrow r \cdot f_{hunger}(N)\cdot f_{over}(N)
$$

It applies alongside B2's factor, after the bush premium, so it inherits the rest-and-no-net-damage condition.

**Keys** (all under `body:`, all static):

| Key | Symbol | Meaning | Read when | Default in `default.yaml` |
|---|---|---|---|---|
| `healing_nutrition_dependence` | — | on/off (static gate; `false` = not traced) | always | `false` |
| `healing_hunger_low` | `N_lo` | at or below this nutrition, healing runs at the floor | dependence on | 0.0 |
| `healing_hunger_high` | `N_hi` | at or above this nutrition, the hunger factor is 1 | dependence on | 100.0 (the setpoint) |
| `healing_hunger_floor` | `f_h` | factor at or below `N_lo` (0 = no healing when starving) | dependence on | 0.0 |
| `healing_overfull_floor` | `f_o` | factor at `max_nutrition`; **1.0 = being over-full does not slow healing** | dependence on | 1.0 |
| `healing_overfull_start` | `N_os` | where the over-full slowdown begins | dependence on **and** `f_o < 1` | 150.0 |

**Validation:**
- `0 ≤ N_lo < N_hi ≤ max_nutrition`; `f_h, f_o ∈ [0, 1]`; `N_hi ≤ N_os < max_nutrition`. The two ramps cannot overlap, so the product is piecewise: rising, flat, then falling.
- Dependence on requires `with_nutrition` and `with_injury`, the same refusal as B3. If nutrition is frozen the factor is a constant, and with no injury system it does nothing.

**Over-full is a real modelling choice, so it is a setting.** Nutrition above the setpoint (100) is already penalised by the reward, and 200 kills (over-eating). Whether a bloated body *also* heals slower adds a second, separate "overeat vs heal" interaction. The user's rationale covers only the hungry side, so the default is `f_o = 1.0` (no over-full slowdown), which keeps B5 monotone. `f_o < 1` switches the over-full ramp on; the factor then rises, plateaus, and falls, monotone on each side.

**Healing per rest step in a bush at level 05** (base 5.0; B2 off). Example parameters, not decisions — the parameter study chooses them.

| Nutrition | `f_h = 0.2, N_lo = 20, N_hi = 100` | `f_h = 0, N_lo = 0, N_hi = 100` | first column plus over-full `f_o = 0.5, N_os = 150` |
|---|---|---|---|
| 20 | 1.00 | 1.00 | 1.00 |
| 50 | 2.50 | 2.50 | 2.50 |
| 100 | 5.00 | 5.00 | 5.00 |
| 150 | 5.00 | 5.00 | 5.00 |
| 180 | 5.00 | 5.00 | 3.50 |

**Interaction with B3: heal 70 injury points by resting in a bush without eating** (level 05: metabolic cost 1/step, B5 as the first column, B2 off, scripted with the §A3 rules):

| Start nutrition | c | B5 | `partial`: steps / healed / end nutrition / outcome | `full`: steps / healed / end nutrition / outcome |
|---|---|---|---|---|
| 60 | 1.0 | off | 11 / 50 / 0 / starves | 10 / 50 / 0 / starves |
| 60 | 1.0 | on | 25 / 36 / 0 / starves | 24 / 37 / 0 / starves |
| 120 | 1.0 | off | 14 / 70 / 36 / healed (spent 84) | same |
| 120 | 1.0 | on | 21 / 70 / 29 / healed (spent 91) | same |
| 60 | 0.5 | off | 14 / 70 / 11 / healed (spent 49) | same |
| 60 | 0.5 | on | 34 / 52.5 / 0 / starves | 34 / 53.5 / 0 / starves |
| 120 | 0.5 | off | 14 / 70 / 71 / healed (spent 49) | same |
| 120 | 0.5 | on | 16 / 70 / 69 / healed (spent 51) | same |

**What the self-balancing buys, and what it does not.**
- **It buys time.** A hungry, injured agent that keeps resting lives about **2.4× longer** before starving: 10–11 steps become 24–25 at start 60 and `c = 1`. That is a longer window to break off and go and eat.
- **It does not save food per point healed.** B3 charges per point healed, so a slower heal costs the same food per point. It also spans more steps, and each step pays the 1.0 metabolic cost. So with B5 on, healing the same injury costs **more** total nutrition (91 vs 84 at start 120), and an agent that rests until it starves heals **less** (36 vs 50).
- The self-balance is therefore a rate effect (a longer runway), not an efficiency gain. That is still the intended pressure — "stop healing and go eat" becomes a real option — but the parameter study should confirm it at the chosen values.

Recorded for that study. `partial` and `full` differ only on the final step here, because the cap binds only once.

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
- **The loader logs this, never refuses it** (user decision, Revision 3). Whenever B1 is on, the loader computes the first step onto the hottest single-fire corner from `start_body_temp_high`:

  `T_1 = high + s_w·(k_ex·(F_max − high) − k_loss·(high − T_set) + k_met)`

  - If B4 is on in `both` mode, `k_ex·(1+g)` replaces `k_ex`, and the computation is the one in §A2.
  - It is logged at INFO level, or at WARNING when `T_1 > max_temperature` ("a warm random start can die on its first step onto a fire — allowed by configuration").
  - Level 05 logs **+10.78 (INFO)**; a +10 upper start would log **+15.18 (WARNING)** and still load.
  - **Record:** the loader has no load-summary object; it reports only through its module logger `_log` (`config_loader.py:100`), as the structure check does ("thermal structure check PASSED…", line 703). That log line is the record, and it lands in the trainer's and each tool's stdout log. The developer confirms there is still no summary object at implementation time. If one has appeared, the value goes there too.
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

**Unconditional keys `body.healing_nutrition_cost` and `body.healing_nutrition_dependence`** (B3 and B5; their sub-keys are read only when the parent is on). Same population as `recovery_in_bush_multiplier` on 2026-09-15:
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
- the unconditional B3 and B5 keys break **every** saved config, including all of Wave 1 and Wave 2 (28 runs).

**User decision: build a minimal compatibility step first** (C0). It is scoped to exactly this change's keys and is designed to be absorbed by [[SAVED_RUN_CONFIG_COMPAT]], which is PLANNED, not implemented (`src/environment/saved_config_compat.py` does not exist as of 2026-09-26). C0 follows that plan's own specification (its §Design and §File Changes) so the owner can extend rather than replace it:

- **Same module path and function:** `src/environment/saved_config_compat.py`, `apply_saved_config_compat(cfg: dict, *, source: str) -> list[str]`. It mutates the dict it is given, and **callers pass it a deep copy** (see the fingerprint rule below).
- **`_ERA_KEYS` holds only this change's keys:**

| Key | Supplied value | Condition | Why the value is inert |
|---|---|---|---|
| `thermal.random_start_body_temp` | `False` | only if the saved `thermal.enabled` is true | `jax_reset` static branch |
| `thermal.healing_cold_sensitivity` | `0.0` | same | `update_body` static gate |
| `thermal.healing_warm_sensitivity` | `0.0` | same | same |
| `thermal.injury_heat_exchange_gain` | `0.0` | same | same |
| `body.healing_nutrition_cost` | `0.0` | always | same |
| `body.healing_nutrition_dependence` | `False` | always | same (B5) |

  The conditional keys (B1 range, B4 mode, B3 shortfall, B5 ramp keys) are never supplied: they are read only when their parent is non-inert.

- **Refusal rules** (from the compat plan's list):
  - (a) raise if `source` resolves under the repo's `configs/` — the live path keeps hard-erroring;
  - (b) a key already present is left alone;
  - (c) **all-or-none per block** — a saved `thermal:` block carrying some of the four thermal keys but not all, or a `body:` block carrying one of the two body keys but not the other, is an edited or foreign file, so raise;
  - (d) if the saved config lacks `thermal.enabled` altogether (a pre-thermal run), supply none of the thermal keys and let the loader fail on `thermal.enabled` as it does today. That key belongs to the compat plan's Stage 1, not here.
- **Loud:** one WARNING line naming every key supplied, its value and `source`. The function returns the sorted list, and callers print it.
- **The trajectory-store fingerprint and manifest never see the injected keys** (reviewer N1). This is the compat plan's §A10 decision, and it is load-bearing here: a store started before C2 must resume into the **same** directory after C2. Revision 2's wording ("the injection runs after the hash") could not be satisfied, because the load (`collect_trajectories.py:727`) comes before the hash (`:745`).
  - **Specified mechanism:** after the existing opt-in sensory shims, take `cfg_load = copy.deepcopy(cfg)`; call `apply_saved_config_compat(cfg_load, source=…)`; build params with `load_env_params(Config(cfg_load))`.
  - `cfg`, which keeps today's content, is what `env_fingerprint(cfg)` at `:745` and `build_manifest(cfg=cfg, …)` receive.
  - The same deep-copy pattern is used at every call site, including the ones that never hash, so there is one pattern to review.
- **Call sites** (the compat plan's §A4 Group 1): `scripts/eval/traj_collect/collect_trajectories.py` (699–727), `scripts/eval/eval_rollout.py` (959/1007; only when the resolved `--config` is outside `configs/`), `scripts/analysis/nmn/replay.py` (82–84), `scripts/analysis/trajectory_glm.py` (54), `scripts/analysis/supplementary/parity.py` (26–31). The developer re-greps `load_env_params` for any site added since 2026-09-10.
- **Eval recordings** (reviewer O1). `.rec.gz` files pickle `EnvParams`, and an unpickled old object lacks the new fields. Recordings are only rendered, never stepped. The developer greps for `.replace(` / `dataclasses.replace` on unpickled params before C2; the renderer already works around this at `render_recordings_v2.py:184–193` with `object.__setattr__`. No change is expected; any hit is fixed the same way.

**Failable gate (reviewer M3).** C2 may not be committed unless, **after** C2, two verbatim saved configs:
- `20260921-114858_rppo_basicq2_lvl05_t1none_s42` (Wave 1, level 05)
- `20260922-182534_rppo_bq2cover_lvl05_t1none_s42` (Wave 2, level 05)

— copied into `tests/env/fixtures/saved_run_configs/` — **fail** `load_env_params(Config(raw))` with the missing-key error **and succeed** through `apply_saved_config_compat`, supplying exactly the six keys above. The store directory must also equal `env_fingerprint(raw)`, checked end to end (N1). A committed test (`tests/env/test_saved_config_compat.py`) and CP-C0 run it; the negative half ("raw load **must** fail") is committed in C2 as an unconditional assertion (N5).

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

The design has five mechanics, fifteen keys and one rule: **every new field is static** (`struct.field(pytree_node=False)`; floats `float()`-coerced, strings validated against their enum). Each mechanic sits behind a trace-time Python `if` that emits nothing at its off value.

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

**D2b (B5, immediately after D2; the same statement position):**

```python
if params.healing_nutrition_dependence:              # static
    _N = state.nutrition                             # pre-step
    _fh = params.healing_hunger_floor
    _ramp = jnp.clip((_N - params.healing_hunger_low)
                     / (params.healing_hunger_high - params.healing_hunger_low), 0.0, 1.0)
    _factor = _fh + (1.0 - _fh) * _ramp
    if params.healing_overfull_floor != 1.0:         # static
        _fo = params.healing_overfull_floor
        _factor = _factor * (1.0 - (1.0 - _fo) * jnp.clip(
            (_N - params.healing_overfull_start)
            / (params.max_nutrition - params.healing_overfull_start), 0.0, 1.0))
    recovery_amount = recovery_amount * _factor
```

B2 and B5 are both multipliers on `recovery_amount`, so their order does not change the value beyond float rounding. The order is fixed (B2, then B5) and pinned by T-B5-4. B3's `h_nom` is computed from the resulting `recovery_amount`, so B3 automatically pays for the slowed heal.

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

- `update_body` returns `starved` as a new element **appended at index 9**, never inserted (reviewer N4). `tests/env/test_thermal_rate_scales.py:192,218` index `[6]` positionally, and `core.py:981` unpacks the tuple; the developer updates that unpack. It is `None` on every path except B3-partial; `None` is an empty pytree, so the off-path `update_body` jaxpr is unchanged.
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
- A second structure evaluation at full injury. In `cooling_only` mode the boosted coefficient is used only for rings on the cooling side, decided by the sign of `k_loss·(T_set − T_amb) + k_met`; in `both` mode it is used for every ring. **Logged, not raised** (Revision 3). This needs `_check_thermal_structure` to have a `raise_on_failure: bool` keyword (default `True`, so the existing injury-0 call is unchanged) that logs a WARNING prefixed "at full injury — allowed by configuration" instead of raising.
- The worst-case first step onto a fire (§A2) is logged: INFO, or WARNING when lethal. Never raised.

**Loader, B1 (flag on).** The worst-case first step from `start_body_temp_high` (§A5) is logged: INFO, or WARNING when lethal. Never raised. When B4 `both` is also on, one combined line is logged, not two.

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
| `body.healing_nutrition_dependence` | always | `false` | bool; requires `with_nutrition ∧ with_injury` if true |
| `body.healing_hunger_low` | dependence true | `0.0` | `0 ≤ low < high` |
| `body.healing_hunger_high` | dependence true | `100.0` | `high ≤ max_nutrition` |
| `body.healing_hunger_floor` | dependence true | `0.0` | `[0, 1]`, not NaN |
| `body.healing_overfull_floor` | dependence true | `1.0` | `[0, 1]`, not NaN; `1.0` = no over-full slowdown |
| `body.healing_overfull_start` | dependence true and overfull floor `< 1` | `150.0` | `hunger_high ≤ start < max_nutrition` |

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
  - **Claim the path first (reviewer N3).** Before C0 work starts, post a diary `note` claiming `src/environment/saved_config_compat.py` for this plan. **Immediately before committing C0**, run `git log --oneline -- src/environment/saved_config_compat.py` and check the working tree. If the file exists (the other session landed first), add the six rows to its table instead of creating it, and record that in the Implementation Report.
- **Wire the five call sites of §A7** using the deep-copy pattern: inject into `cfg_load = deepcopy(cfg)` and load from it. The fingerprint and manifest use the untouched `cfg`. Each site prints the returned list.
- `tests/env/fixtures/saved_run_configs/` (NEW): the two saved configs copied **verbatim**, with a README naming the source run and the date copied.
- `tests/env/test_saved_config_compat.py` (NEW). It fails rather than skips if a fixture is missing.
  - (i) Both fixtures load through the shim, returning exactly the six keys. C0 carries **only this positive half**.
  - (ii) **Added in C2, unconditional (N5):** the raw load of each fixture raises the missing-key error. No commit-dependent branching in any test.
  - (iii) A `source` under `configs/` raises.
  - (iv) A thermal block carrying two of the four thermal keys raises, and a body block carrying one of the two body keys raises.
  - (v) Present keys are not overwritten.
  - (vi) After the call, the caller's original dict is unchanged, i.e. the deep-copy pattern is used (unit level).
  - (vii) A thermal-off saved config gets only the two body keys.
  - **End-to-end fingerprint check (N1).** A committed test cannot hold a checkpoint, because `results/` is gitignored, so this is checkpoint CP-C0(b), with the output pasted into the report. After C2, run `collect_trajectories.py` on the real Wave 2 level-05 run, on CPU, for a few episodes, into a scratch `--out-root`. Assert that the created store directory name equals `env_fingerprint(yaml.safe_load(<run>/models/config.yaml))`. This same run is the real-call-site check N2 asks for.
- `docs/environment/SCRIPTS_DEPENDENCY_MAP.md`: note the new `src/` import in the five scripts.

**Commit C2 — mechanics, keys, tests, docs (everything inert).** Blocked on the M3 gate and the pre-flight in §A7.

`src/environment/state.py`:
- `healing_nutrition_cost: float`, `healing_nutrition_shortfall: str`, `healing_nutrition_dependence: bool`, `healing_hunger_low: float`, `healing_hunger_high: float`, `healing_hunger_floor: float`, `healing_overfull_floor: float` and `healing_overfull_start: float`, next to `recovery_in_bush_multiplier`. All static.
- In the thermal block: `thermal_random_start_body_temp: bool`, `thermal_start_body_temp_low: float`, `thermal_start_body_temp_high: float`, `thermal_healing_cold_sensitivity: float`, `thermal_healing_warm_sensitivity: float`, `thermal_injury_heat_exchange_gain: float`, `thermal_injury_heat_exchange_mode: str`. **All static.**
- A comment on why static (M1).
- Update the `body_temp` comment.

`src/environment/config_loader.py`:
- Thermal-on arm, after the rate-scale block (~1591): B1, B2, B4 per the table, and the B4 stability extension (still a refusal).
- Thermal-off arm (1647–1672): sentinels.
- Structure-check call (~2019): the full-injury pass when `g > 0` (logged, not raised; the new `raise_on_failure` keyword).
- The B1 / B4 worst-case first-step log line (§A5, §A2).
- Body block: the B5 keys and their validation.
- Body block (after 2233): B3 keys.
- `EnvParams(...)`: the fifteen fields.

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
  # B5 — healing speed depends on nutrition (the pre-step energy store). false = off.
  # Factor = hunger ramp (floor at/below hunger_low, 1 at/above hunger_high) x an optional
  # over-full ramp (1 up to overfull_start, falling to overfull_floor at max_nutrition).
  # Requires with_nutrition and with_injury. The ramp values below are placeholders and are
  # read only when the flag is true; the parameter study chooses real ones.
  healing_nutrition_dependence: false
  healing_hunger_low: 0.0
  healing_hunger_high: 100.0
  healing_hunger_floor: 0.0
  healing_overfull_floor: 1.0     # 1.0 = being over-full does not slow healing
  healing_overfull_start: 150.0   # read only when healing_overfull_floor < 1
```

**Raw-loaded configs** (§A6):
- the thermal keys go into the two archived campfire test inputs;
- `body.healing_nutrition_cost: 0.0` goes into the 34-file set, the frozen parity world, and the archived test inputs the developer lists.

`tests/env/test_body_mechanics_parity.py` (NEW):
- CPU only. It **fails, never skips**, on a missing fixture, config or provenance.
- Loads both worlds at HEAD through the resolving loader. After C3, it sets `thermal.random_start_body_temp: false` in memory for basic/05 (and records that it did).
- **Named drift check (O3):** the resolved dict minus the fifteen new keys must equal the fixture's stamped dict, so unrelated config drift fails with its own message.
- `np.array_equal` on every recorded array.
- `jax_step` / `jax_reset` jaxpr SHA-1 equality.
- **Contrast half:** B1 [−5, −5]; B2 `s_c = 0.1`; B2 `s_w = 0.1` in a warm scene; B3 `c = 1` in each shortfall mode, on both worlds; B4 `g = 1` in each mode; B5 on (`f_h = 0.2, N_lo = 20, N_hi = 100`), and B5 with over-full `f_o = 0.5`. Each must change the rollout and the jaxpr.
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
- **B5** (resting in a bush, no damage, injury 50, B2 and B3 off; `f_h = 0.2, N_lo = 20, N_hi = 100`)
  - T-B5-1: pre-step N = 10 → I 49.0; 20 → 49.0; 50 → 47.5; 100 → 45.0; 150 → 45.0.
  - T-B5-2: over-full `f_o = 0.5, N_os = 150` → N 180 gives 46.5, N 150 gives 45.0.
  - T-B5-3: flag off → today's value exactly, at every N.
  - T-B5-4: B2 `s_c = 0.1` at T = −5 and N = 50 → recovery 5·0.5·0.5 = 1.25 → I 48.75.
  - T-B5-5: B3 `c = 1` `full`, N 50 → heal 2.5, N 50 − 1 − 2.5 = 46.5.
  - T-B5-6: loader — flag missing → `ValueError`; `N_lo ≥ N_hi`; `N_hi > max_nutrition`; floors outside [0, 1] or NaN; `N_os < N_hi` or `N_os ≥ max_nutrition` (only when `f_o < 1`); flag true without `with_nutrition` / `with_injury` → `ValueError`; `overfull_start` missing with `f_o = 1` → loads.
- **B1 / B4 logging** (pytest `caplog`)
  - T-LOG-1: level 05 with C3 values logs a first-step value of +10.78 (±0.01) at INFO.
  - T-LOG-2: `start_body_temp_high: 10` loads and logs +15.18 at WARNING.
  - T-LOG-3: B4 `both` `g = 1` loads and logs a WARNING with the combined value.
  - T-LOG-4: the full-injury structure failure loads and logs "at full injury" at WARNING.
  - T-LOG-5: the injury-0 structure failure still raises, unchanged.
- **Graph-identity** tests in the style of `test_recovery_in_bush.py`: `state.body_temp` is unused by the injury block at B2 off; `state.injury_level` is unused by the thermal block at B4 off. The leaf is located positionally.

**Must stay green unmodified:** `test_thermal_parity`, `test_unified_parity`, `test_visual_parity`, `test_metabolic_coupling`, `test_thermal_rate_scales`, `test_recovery_in_bush`, `test_two_sided_nutrition`, `test_thermal_reward_gate` (**no regeneration**), `test_no_recompile`, `test_truncation_not_death`, `test_config_layer_silent_failures_20260723`, `test_dashboard_layout`.

**Docs, in the same commit:**
- `CONFIG_GUIDE.md` §5: the new keys, the conditional reads, "pin with `low == high`", and the saved-config compat step and its rule.
- `02_config_schema.md`: fifteen rows.
- `05_body_homeostasis.md`: the order, B2, B3 (both modes, the death labels, the alive-at-0 state), B4 (why `k_exchange`; the modes), B5 (nutrition, not satiation; the ramps; over-full as a setting; the §A4b runway finding) and B1 (logged worst case, no refusal).
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

C0 creates, or extends, `src/environment/saved_config_compat.py` with the API and refusal rules that plan specifies. Its `_ERA_KEYS` holds **only** the six rows of §A7 (Revision 3 added `body.healing_nutrition_dependence` for B5), each with the branch that makes it inert. The parity instrument that plan demands for those rows is this plan's `tests/env/test_body_mechanics_parity.py`.

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

Nothing blocks approval. Decided in Revision 3: alive-at-0 accepted; B1 hot start logged, not refused.

Three items for later or for awareness:
1. **B5's "self-balancing" is a runway effect, not a saving.** With B5 on, a hungry, injured agent lives about 2.4× longer before starving (10–11 steps → 24–25 at start nutrition 60, `c = 1`). But healing the same injury costs *more* total food (91 vs 84), because the slower heal pays metabolism for more steps (§A4b). This is for the parameter study to weigh; no plan change is needed.
2. **The trajectory-store body-temperature column** is a separate plan and needs a `SCHEMA_VERSION` decision there.
3. **The parameter study** (§Out of scope) chooses the B2–B5 values before any batch turns them on.

---

## Out of scope

- The injury × starting-fullness probe scenes (a later plan).
- The level-05 variant worlds, including the B3-`partial` world (`experiment-designer`, outside `basic/`).
- The trajectory-store body-temperature column (a separate plan).
- `calculate_drive` or the reward.
- The general compatibility layer beyond these six keys.
- **The parameter study** ("interactions between internal states"): scripted, agent-free simulations of nutrition, injury and temperature under B1–B5, to choose parameter ranges before training. It is a separate, later design step (`experiment-designer` / `senior-developer`). §A4b's table is a first data point for it.

---

## Checkpoints

- [x] **CP1 — C1 first.** Done `8a865d9c` from a worktree of `eef30212`; coverage lvl05 1772/70/177/7 (heal/bush-heal/deaths/eats), span 33.1°; lvl04 1794/122/164/5; `_provenance_sha` + stamped YAML recorded. Streams auto-reset (deviation 1). Fixture from a pre-change worktree; coverage counts non-zero; `_provenance_sha` and the stamped config recorded.
- [x] **CP-C0 — compat.** Claim diary note `34310732`; `git log` on the path empty before C0 (`eef30212`); positive half green at C0, negative half + shim green after C2; end-to-end collection store dir `ac5f70226a` = `env_fingerprint(raw)`; key lists in the report.
  - (a) **Before C0 starts:** a diary note claims the module path (N3). **Immediately before committing C0:** `git log --oneline -- src/environment/saved_config_compat.py`, with the output pasted.
  - (b) At C0: `test_saved_config_compat.py` (the positive half) is green. **After C2 (M3 gate):** the unconditional negative half is green (both raw loads fail), and the shim loads succeed with exactly six keys.
  - (c) **End to end, after C2 (N1 + N2):** a few-episode CPU `collect_trajectories.py` run on the Wave 2 level-05 run into a scratch out-root. Paste its printed injected-key list. Assert the store directory name equals `env_fingerprint` of the raw saved config.
  - (d) Also run the shim on the live saved configs of both gate runs and one Wave 1 level-06 run, and paste the key lists.
- [x] **CP2 — B1 stream isolation** (T-B1-3). Green: 1000 resets, every other leaf identical to the flag-off reset.
- [x] **CP3 — Off = today, three ways.** `test_body_mechanics_parity.py` 21 passed: rollouts byte-identical, jaxpr SHAs identical, all 11 contrasts change rollout + jaxpr. Parity test green, including jaxpr SHA equality and the contrast half. SHAs recorded.
- [x] **CP4 — B3 off path.** `update_body` jaxpr SHA identical at c = 0 on both worlds (lvl05 `b5a89ad6`, lvl04 `b58206f3`). `update_body` jaxpr string identical before and after at `c = 0` on both worlds.
- [x] **CP5 — Unit tests** green: `test_body_mechanics_units.py` 85 passed.
- [x] **CP6 — Loader.** All 15 keys raise when missing inside their read condition; B4 bound (10.9 / 11.5), full-injury pass, `both` threshold (g* = 0.4731, logged), `with_injury` refusal exercised; level 05 structure holds at g ∈ {0,1,2} cooling_only. Every key raises when missing within its read condition; B4 bounds, structure pass, `both` transient and `with_injury` refusal exercised; the level-05 structure check passes at `g` ∈ {0, 1, 2} in `cooling_only`.
- [x] **CP7 — Roll-out and pre-flight.** tests/env 1109 → 1256 passed, 0 failed; parity families unchanged; archived 41 → 35 loadable; pre-flight clean (no live collection on 109–113) at 20:37 before `11b9a1b7`. `tests/` green on CPU with per-family pass/skip counts compared to the 2026-09-17 entry. Archived before/after counts reported. **Immediately before committing C2:** the live-collection pre-flight of §A7 run and its output pasted into the report; any live process means C2 waits.
- [x] **CP8 — Level 05 after C3, adversarial.** (a) 600/600 in range (05 and 06); (b) pinned +5 × 1000 resets → max first step +10.779, max F +79.737, fire counts 330/334/336; (c) ring-settle +12.39; loader logs +10.78 INFO; (d) tests/env 1256 passed after C3.
  - The loader resolves B1 on with [−10, 5] for levels 05 and 06.
  - (a) 600 real resets at the configured range → every start within range.
  - (b) **Pinned `low == high == +5`**, at least 600 real resets, with the per-episode fire count logged so multi-fire layouts are visibly included. For every active fire cell, compute the first step onto it from +5 using that reset's real field value: `5 + s_w·(k_ex·(F − 5) − k_loss·5)`. Report the max and the max `F`. The level-05 range was chosen so this stays below +15. A value at or above +15 is **reported to the user, not a failure** ("allow, make visible"). Also confirm that the loader's own log line for level 05 reads +10.78 (INFO).
  - (c) The same from the loader-model ring settle, as a cross-check against the 09-19 figure of 12.3.
  - (d) `tests/` green after C3 (reviewer L4), including `test_truncation_not_death.py`.
- [x] **CP9 — Reward untouched.** `calculate_drive` not in the diff; `test_thermal_reward_gate.py` 18 passed, fixture not regenerated. No diff inside `calculate_drive`; `test_thermal_reward_gate.py` green without regeneration.
- [x] **CP10 — Speed.** Local RTX 4090, 512 envs × 200-step scan: median SPS within run-to-run noise before/after on both levels (graph identical). Steps per second before/after on levels 05 and 04: same node, GPU and seed, with a budget past warm-up.
- [x] **CP11 — Docs** as listed, in the same commits (C0: map §1e; C1: map §3; C2: guide, schema, 05, 06, registry, map §1c; C3: registry change log).
- [ ] **CP12 — Hand-offs.** Not done by `developer` (no `Agent` tool): named for the parent in the Implementation Report.
  - `bug-curator`: the mandatory-key roll-out row, and "B3 partial starvation shares one predicate".
  - Compat-plan owner: the §Hand-off section.
  - `experiment-designer`: the §A0 observability caveat, and that the variant must state `healing_nutrition_shortfall: partial` explicitly.

---

## Implementation Report

> **Implemented by**: developer (session `4efbe660`)
> **Date**: 2026-09-26

**In plain words.** The five body mechanics (B1–B5) are in the environment, every one switched off by default, and the environment is provably unchanged when they are off: rollouts recorded from the old code match byte for byte, and the compiled step/reset graphs are identical. Old training runs' saved settings still load, through a small logged compatibility step that landed first. The only behaviour change is that curriculum level 05 (and level 06, which builds on it) now starts each episode at a random body temperature between −10 and +5; the worst first step onto a fire from +5 is +10.78, below the +15 death line, measured over 1,000 real resets including multi-fire layouts.

### Commits

| Step | Commit | What |
|---|---|---|
| claim | `34310732` | diary note claiming `src/environment/saved_config_compat.py` (N3) |
| C0 | `eef30212` | saved-config compat step + 6 wired call sites + positive-half test + 2 verbatim saved configs; map §1e |
| C1 | `8a865d9c` | pre-change fixture (from a worktree of `eef30212`) + generator; map §3 |
| C2 | `11b9a1b7` | the mechanics, 15 keys, loader, inert-key roll-out, parity + units tests, compat negative half, docs |
| C3 | `8d07a00f` | B1 on in level 05 ([−10, +5]); level 06 header note; registry change log |

Order C0 → C1 → C2 → C3. The fixture was generated from a checkout of the pre-change commit (`eef30212` = C0, which touches no environment code) and committed before the mechanics.

### File by file

- **`src/environment/saved_config_compat.py`** (new, C0): `apply_saved_config_compat(cfg, *, source) -> list[str]`; `_ERA_KEYS` = the six §A7 rows, each with value, era and inert branch; refusal rules (a)–(d); one WARNING line. N3: `git log --oneline --all -- src/environment/saved_config_compat.py` was **empty** immediately before committing C0; no other session had landed the file.
- **Call sites** (C0), all `cfg_load = copy.deepcopy(...)` → shim → `load_env_params(Config(cfg_load))`, each printing the key list: `collect_trajectories.py` (fingerprint/manifest keep the raw `cfg`), `eval_rollout.py` (only when the resolved config is outside `configs/`, new `_is_under_configs`), `nmn/replay.py`, `trajectory_glm.py`, `supplementary/parity.py`, **plus `obs_manipulation/run.py` (`--world training`)**, added 2026-09-24 and found by the plan's re-grep (deviation 2). The Dreamer probe paths were checked and left alone: they load probe configs from `configs/` merged over `default.yaml`, never a saved config. O1 grep: no `.replace(` on unpickled recording params beyond the existing `object.__setattr__` in `render_recordings_v2.py`.
- **`state.py`** (C2): 15 static fields, M1 comment, `body_temp` comment.
- **`config_loader.py`** (C2): B1/B2/B4 in the thermal arm (after the rate-scale block) with off-arm sentinels; B3/B5 after `recovery_in_bush_multiplier`; `_thermal_radial_equilibria(k_exchange_boosted, boost_mode)` with the per-ring same-side rule; `_check_thermal_structure(raise_on_failure, …)` (full-injury pass logs WARNING "at full injury — allowed by configuration"); new `_thermal_first_fire_step` for the B1 / B4-`both` log (one combined line). There is still no load-summary object (grep), so the log line is the record.
- **`core.py`** (C2): D1 (`body_key1`), D2, D2b, D3, D4; `starved` appended at index 9; `jax_step` unpack and static reason-2 selection; ORDER comment extended; `calculate_drive` untouched.
- **Configs** (C2): `default.yaml` (the plan's YAML verbatim, plus a doc-link line); body keys into the 11 standalone worlds (`configs/continual/nmn_double_return_stages/0[1-5]*`, `configs/verification/{observability_gates_S1-4,olfaction_parity_*}`), the frozen parity world ("ADDED AFTER THE FREEZE"), `tests/fixtures/trajectory_collection/dual_format_config.yaml`, and the 29 archived configs carrying the 2026-09-15 live-test-input note (27 body-only; the two campfire worlds also got the four thermal keys). `archive/basic_vec8/default.yaml` also carries the bush line but nothing loads it, so it was left alone.
- **Inline YAML bases in 19 test modules** (C2): the two body keys next to `recovery_in_bush_multiplier` (the §A6 "34-file set"; the grep now returns 36 because it also matches the two verbatim C0 saved-run fixtures, which were not edited). This includes `test_no_recompile.py` and `test_visual_properties.py`: config lines only, no assertion changed.
- **Tests**: `test_saved_config_compat.py` (16 at C0, 18 with the C2 negative half), `test_body_mechanics_parity.py` (21), `test_body_mechanics_units.py` (85). **R2**: the units module docstring explains why B5 is not in the graph-identity set. **R1**: `05_body_homeostasis.md` says B5 reads nutrition before this step's decay, with the 46.5-vs-46.55 example.
- **Docs**: `CONFIG_GUIDE.md` §5 (keys, read conditions, pin with `low == high`, the compat step and its `_ERA_KEYS` rule); `02_config_schema.md` (mandatory lists, a table covering all 15 keys, static-field row); `05_body_homeostasis.md` (order, B1–B5, alive-at-0, runway finding); `06_reward_and_termination.md` (reason 2 under B3 partial, reason 5 reused, verbatim block); `CONFIG_CRITICAL_SETTINGS.md` (5 registry rows, C2 and C3 change-log entries); `SCRIPTS_DEPENDENCY_MAP.md` (§1e, §3, §1c).

### Test results

| Check | Result |
|---|---|
| `tests/env/`, CPU, pre-change (worktree `eef30212`) | 1109 passed, 1569 skipped, 0 failed |
| `tests/env/` after C2 | **1256 passed, 1530 skipped, 0 failed** |
| `tests/env/` after C3 | **1256 passed, 1530 skipped, 0 failed** (includes `test_truncation_not_death`) |
| `test_body_mechanics_parity.py` | 21 passed (rollouts, jaxpr SHAs, drift check, coverage, 11 contrasts) |
| `test_body_mechanics_units.py` | 85 passed |
| `test_saved_config_compat.py` after C2 | 18 passed (both raw loads fail; shim supplies exactly six keys) |
| Parity families, before → after | `thermal_parity` 12 / 398 skipped → same; `unified_parity` 34 / 711 → same; `visual_parity` 8 → 8; `extero_noc_parity` 3 → 3; `metabolic_coupling` 11 → 11; `directional_sensors` 28 → 28 |
| Must-stay-green list | `thermal_rate_scales` 14, `recovery_in_bush` 8, `two_sided_nutrition` 22, `thermal_reward_gate` 18 (**not regenerated**), `no_recompile` 3, `truncation_not_death` 2, `config_layer_silent_failures_20260723` 5, `dashboard_layout` 123 — identical before and after |
| `tests/ --ignore=tests/env`, main tree after C2 | 62 failed, 559 passed, 29 errors — all pre-existing: the 38 `test_trajectory_collection.py` failures/errors are `sensory.visual_value_mode ... required but missing` (also at the pre-C0 script: 33 F + 8 E); `test_modulation_input_slice::test_hand_computed_breakdown…` fails at the baseline too; `dreamer_srl/test_loss.py::test_symlog…` is flaky (4/4 on rerun). No failure names a new key. The worktree baseline (no `results/`) is not directly comparable. |

jaxpr SHA-1s (params traced), identical before and after: level 05 `jax_step` `e3ddd681…`, `jax_reset` `96af4b00…`, `update_body` `b5a89ad6…`; level 04 `5c891836…`, `7625cffb…`, `b58206f3…`.

### CP-C0 — compatibility gate

- (b) Raw loads of both fixtures fail with `Configuration key 'thermal.random_start_body_temp' is required but missing`; through the shim both load with exactly the six keys.
- (c) End to end on a real call site (N1 + N2): `collect_trajectories.py --run results/JAX_RecurrentPPO/20260922-182534_rppo_bq2cover_lvl05_t1none_s42 --episodes 4 --seed-base 900000 --shard-episodes 4 --obs-precision float32 --device cpu` into a scratch out-root printed `[collect] saved-config compat supplied: ['body.healing_nutrition_cost', 'body.healing_nutrition_dependence', 'thermal.healing_cold_sensitivity', 'thermal.healing_warm_sensitivity', 'thermal.injury_heat_exchange_gain', 'thermal.random_start_body_temp']` and created `…/10000012/ac5f70226a`; `env_fingerprint` of the raw saved config = `ac5f70226a` — **equal**. All 23 existing Wave 1 / Wave 2 store directories also equal `env_fingerprint` of their raw saved configs.
- (d) Live saved configs of Wave 1 lvl05 `20260921-114858…`, Wave 2 lvl05 `20260922-182534…` and Wave 1 lvl06 `20260921-114905…`: raw load fails; the shim supplies the same six keys; the world builds.
- Population: 542 saved `models/config.yaml`; 40 loaded at the pre-change commit; after C2, 0 load raw and **all 40 load through the shim** (16 thermal-on get six keys, 24 thermal-off get two).

### CP7 — roll-out and pre-flight

- Archived configs through `load_env_config` → `load_env_params`: 335 files, **41 → 35** loadable; the 6 lost are all `archive/basic_vec8/` (no test input; policy-accepted).
- Pre-flight at 20:37:15, immediately before C2: `run_command.py --foreground <n> "pgrep -af 'collect_trajectories|run_collection'"` → `NONE` on 109–113; `gpu_status.py`: all ten GPUs on 109–113 FREE; today's diary: no collection entry.

### CP8 — level 05 after C3, on real resets

- Levels 05 and 06 resolve `random_start_body_temp: true`, [−10, +5]; loader log for both: `body +5.00 -> +10.78 (single-fire model, fire cell +79.73 at default_temp=-31, ratio=11)` at **INFO**.
- (a) 600 resets each of levels 05 and 06: all in range (min −10.00, max +4.98, mean −2.57).
- (b) Start pinned at +5, **1,000** resets, fire count 1 / 2 / 3 = 330 / 334 / 336: worst first step onto any active fire **+10.779** (per count 10.778 / 10.779 / 10.778); hottest fire cell **+79.737**. Nothing reached +15.
- (c) From the ring settle beside each fire: worst first step **+12.39** (ring settle +6.84), against the 2026-09-19 figure of 12.3.
- (d) `tests/env/` 1256 passed / 0 failed after C3.

### CP10 — speed

Local RTX 4090 (GPU 0), `tmp/20260926_bodymech_sps_bench.py`: 512 envs, 200-step jitted scan, 9 reps, two runs each. Median SPS before → after: level 05 4.60M / 4.80M → 4.65M / 4.62M; level 04 4.60M / 4.61M → 4.63M / 4.95M. Within run-to-run noise, as expected from an identical off-path graph. Not measured on a lab node.

### Deviations (none silent)

1. **Fixture streams auto-reset on `done`** (C1). The plan says "up to 300 steps each". With its action rule, random start injury up to 100 ends most level-04/05 episodes within ~5–40 steps, and 16 single episodes produced **zero** eat events, so the plan's own coverage gate refused to write. Each seed is now a 300-step stream that resets with `fold_in(PRNGKey(seed), e)` on `done`. Action rule, seeds, step budget and all coverage requirements are as planned.
2. **Sixth call site** `scripts/analysis/obs_manipulation/run.py` (`--world training`), found by the §A7 re-grep; same deep-copy pattern; listed in the compat test and map §1e.
3. **T-B4-6 / T-B4-7 follow Revision 3, not their Revision-2 wording** (they still say "refused"). T-B4-6 computes the level-05 `both` threshold from the loader model, **g\* = 0.4731**, and asserts 0.9 g\* logs INFO and 1.1 g\* logs WARNING and loads. T-B4-7 uses a synthetic ratio-14 world (ring +13.20 at injury 0, +15.84 at full injury in `both`) and asserts a WARNING in `both` and none in `cooling_only`. T-LOG-5 uses ratio 16.
4. **`jax.clear_caches()` teardown in the two new test modules.** The first whole-suite run aborted inside XLA compilation in `test_bush_blocks_animals.py`: the new modules compile many distinct worlds and the process reached **65,479** memory mappings against this machine's `vm.max_map_count` of 65,530. With a per-test clear (parity) and a per-module clear (units) the peak is ~20k. Not a product bug; relevant to any future test that compiles many worlds in one process.
5. **Strict bool validation** for the two new flags (`random_start_body_temp`, `healing_nutrition_dependence` must be YAML booleans), because `bool("false")` is `True`; existing flags use `bool(...)` coercion.
6. `_ERA_KEYS` names the era "STATE_DEPENDENT_BODY_MECHANICS C2 (2026-09-26)" rather than a hash (C2 did not exist when C0 was written); the hash is `11b9a1b7`.

### Needs the parent / user

- **CP12 hand-offs** (no `Agent` tool here): `bug-curator` — the mandatory-key roll-out row and "B3 partial starvation shares one predicate"; the owner of [[SAVED_RUN_CONFIG_COMPAT]] — §Hand-off (the module exists since `eef30212` with six rows; their doc was not touched); `experiment-designer` — the §A0 observability caveat and that the B3 variant must state `healing_nutrition_shortfall: partial` explicitly.
- Pre-existing, not introduced here: the 38 `tests/test_trajectory_collection.py` failures on `sensory.visual_value_mode` and one `test_modulation_input_slice` assertion. `bug-curator` may want to confirm both are recorded.
- The plan-reviewer's addendum 2 (R1/R2) was uncommitted in this doc when implementation started; it is committed with this report.

*Implemented by: developer*

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


## Feedback from plan-reviewer — addendum (confirming pass on Revision 2, commit `50ccc0b2`)

> **Verdict**: **SOUND WITH CONCERNS — ready for user approval once §A7's collector-ordering sentence is corrected (N1).** M1, M2 and M3 are resolved as claimed. The four mechanics introduce no new problem; the three Moderate items below are all in commit C0's implementation detail.

**Resolved, confirmed against code:** M1 — nine static fields, no new jaxpr leaves; the added `None` return is an empty pytree, so CP4's `update_body` string stays comparable. M2 — every restated number recomputed (+10.78 / +15.18 at −31; ceiling 9.80; `both`-mode rows 11.61 / 15.18 / 18.46; ring at full injury 6.68 / 7.13); CP8(b) uses each reset's real field value, so merged fires are inside the measurement. M3 — C0 has a failable gate and a pre-flight. **B3 partial starvation:** `clip(N_pre) ≤ 0` is exactly "starving from metabolism alone"; the charge can reach 0 but never cross it, and the predicate is computed once and returned, so `done` and reason 2 cannot diverge. Alive-at-0 is the only new state and is correctly put to the user. **C0 refusal rules:** all-or-none is safe because the loader would have refused to *train* a thermal-on world carrying a partial set, so no such saved config can exist; the `Config` class is strict on missing keys only, so injecting keys the loader does not yet read (test (i) before C2) is tolerated. **Static keys vs recompiles:** no new problem — every value is a per-run constant, NaN is refused so cache keys stay equal, `test_no_recompile.py` is unaffected, and curriculum stages that differ in one of these keys recompile once per stage, which every existing static field already does.

| # | Sev | Location | Issue | Fix | Owner |
|---|---|---|---|---|---|
| N1 | 🟡 | §A7 "the new injection runs after the hash and after the manifest's `resolved_env_config` is taken" | **Unsatisfiable as written.** In `collect_trajectories.py` the load is at `:727` (`load_env_params(Config(cfg))`) and the hash at `:745` (`env_fingerprint(cfg)`), with `build_manifest(cfg=cfg, …)` after that. The injected keys must exist *before* the load, which is before the hash — so injecting into `cfg` in place changes the fingerprint and forks the store directory, restarting the Wave 1 collection from block 0: the exact failure C0 exists to prevent. | Specify one of: inject into a **deep copy** used only for `load_env_params` (keep `cfg` pristine for the hash and manifest), or move the fingerprint above the load. Replace test (vi) — which tests the function, not the script — with an end-to-end few-episode CPU collection on the fixture run asserting the store directory name equals `env_fingerprint(raw)`. | `senior-developer` → `developer` |
| N2 | 🟡 | CP-C0 | The gate exercises `apply_saved_config_compat` directly; nothing runs the **five wired call sites**. A site that forgets the import dies at config load exactly as today, and the gate stays green. | After C2, run one real call site end-to-end on the Wave 2 level-05 run (`trajectory_glm.py`, or the N1 collection) and paste its printed key list into the report. | `developer` |
| N3 | 🟡 | C0 / §Hand-off | `src/environment/saved_config_compat.py` is absent now, but the owning plan was revised twice today (`50b14376`, `04c709e5`) and its doc is `MM` in another session. The "if it exists, add rows instead" rule is checked only at implementation time; two sessions can create the same file in the same hour. | Post a diary `note` claiming the module path **before** C0 starts, and run `git log -- src/environment/saved_config_compat.py` immediately before committing C0. | `developer` (process) |
| N4 | 🟢 | D3 `starved` return | `tests/env/test_thermal_rate_scales.py:192,218` index `update_body(...)[6]` positionally, and that file is on the "must stay green unmodified" list. | State that the new element is **appended** (index 9), never inserted. | `developer` |
| N5 | 🟢 | `test_saved_config_compat.py` (i)/(ii) | A test whose assertion depends on which commit it runs under is the "green without comparing" shape the plan cites in §A0. | Put the negative half (raw load **must** fail) in C2 as an unconditional assertion; C0 carries only the positive half. | `developer` |
| N6 | 🟢 | Still open 2 | Recommend **yes**: the `both`-mode inequality with `T_high = start_body_temp_high` at the configured gain/mode is one extra call, and it turns a variant-world edit above +9.8 into a load refusal instead of a silent calibration break that CP8 measured only once. | User decision. | user |

**Cost of being wrong now:** no data loss. N1 mis-implemented forks a 14-run million-episode store on five nodes and restarts it — days of GPU time; N2/N3 cost a confused afternoon. Nothing in the four mechanics themselves carries a wrong-conclusion risk at their inert values.

*Reviewed by: plan-reviewer — addendum 2026-09-26*

### Revision 3 — 2026-09-26, the user's decisions plus the `plan-reviewer` addendum (N1–N6)

| Item | Resolution |
|---|---|
| Alive-at-0 in `partial` | Accepted by the user as specified (§A3). |
| B1 fire first step | **No refusal** (user). The loader logs the worst-case first step from `start_body_temp_high` onto the hottest single-fire corner: INFO, or WARNING when lethal. There is no load-summary object, so the log line is the record (§A5). N6's refusal recommendation was declined by the user. |
| B4 `both`, aligned to "allow, make visible" | The first-step value is logged, not refused. The full-injury structure pass is logged, not raised, via a new `raise_on_failure` keyword; the injury-0 structure check still raises (existing project policy). **Kept as a refusal:** the stability bound `scale·(k_ex(1+g) + k_loss) ≤ 1`, because it is a numerical-validity condition (the discrete update overshoots and oscillates beyond it), not a behavioural outcome (§A2). |
| New B5 | §A4b and D2b. Defined on pre-step nutrition (the store B3 charges), with a low-side ramp and an optional over-full ramp. Over-full slowing is a setting (`healing_overfull_floor`, 1.0 = off), because it adds a separate "overeat vs heal" interaction. Six static keys; the gate is a boolean. Worked table plus a B3 × B5 heal-70 simulation. Finding: B5 extends the starvation runway about 2.4× but raises the total food cost of a heal. Off in the first batch. |
| Parameter study | Forward pointer only (§Context, §Out of scope). |
| N1 | The deep-copy pattern at every site; fingerprint and manifest use the untouched `cfg`; an end-to-end collection check replaces the unit-level test (vi) (§A7, C0, CP-C0(c)). |
| N2 | CP-C0(c): a real call site end to end on the Wave 2 level-05 run, with the printed key list pasted. |
| N3 | A diary claim before C0; `git log` on the path immediately before committing C0 (C0, CP-C0(a)). |
| N4 | `starved` is appended at index 9; the `core.py:981` unpack is updated; the `[6]` indexing in `test_thermal_rate_scales.py` is unaffected. |
| N5 | The negative half ("raw load must fail") is committed in C2 as an unconditional assertion; C0 carries only the positive half. |
| Key count | Fifteen keys (nine from Revision 2 plus six B5 keys); six compat rows. |


## Feedback from plan-reviewer — addendum 2 (confirming pass on Revision 3, commit `2004b234`)

> **Verdict**: **SOUND — ready for user approval.** N1–N5 are resolved as claimed; B5's mathematics and every worked number check; "log, don't refuse" introduces no hazard beyond the one the user accepted. Two Low notes, neither blocking.

**(a) B5 math — verified.** `f_hunger ∈ [f_h, 1]` non-decreasing, `f_over ∈ [f_o, 1]` non-increasing, product in [0, 1]; `N_lo < N_hi` and `N_os < N_max` are strict so neither denominator can be zero; `N_hi ≤ N_os` keeps the ramps disjoint, so the product is rising / flat / falling as stated. Off = flag false = untraced. The worked table (1.0 / 2.5 / 5.0 / 5.0 at 20 / 50 / 100 / 150; 3.5 at 180 with the over-full ramp) and T-B5-1…5 all recompute exactly. **The B3×B5 table was re-simulated from §A3's rules in both shortfall modes: all eight rows reproduce** (the plan's 37, 52.5 and 53.5 are roundings of 36.986, 52.476 and 53.476). Ordering: B2 → B5 → B3 `h_nom` is a chain of multipliers, so B3 pays for the slowed heal automatically. B5 reads `state.nutrition` (before this step's decay) while B3-partial caps on `N_pre` (after decay, drain and food) — a deliberate one-step lag consistent with B2/B4/A1's pre-step convention, and T-B5-5 pins it (factor at 50, not 49).

**(b) Logging instead of refusing — no new hazard.** The stability bound still refuses (a numerical defect, not an outcome); the injury-0 structure check still refuses via the default `raise_on_failure=True`, so world-validity policy is untouched and only outcome-level checks under configurable mechanics are demoted to WARNING. T-LOG-1 (level 05 logs +10.78 at INFO) is now the standing regression guard on the fire calibration, which is the right place for it once the loader no longer enforces it.

**(c) N1–N5 — resolved.** Deep-copy injection with unit test (vi) and the end-to-end CP-C0(c) (N1 + N2); diary claim plus `git log` before committing C0 (N3); `starved` appended at index 9 (N4); negative half unconditional in C2 (N5).

**(d) New — Low only.**

| # | Sev | Location | Note | Owner |
|---|---|---|---|---|
| R1 | 🟢 | §A4b / `05_body_homeostasis.md` | Say explicitly that B5 reads nutrition **before this step's decay** (one step behind B3's `N_pre` cap). It is correct and pinned, but a reader comparing T-B5-5 (46.5) with a post-decay expectation (46.55) will otherwise suspect a bug. | `developer` (docs) |
| R2 | 🟢 | File Changes, graph-identity tests (line 691) | The list correctly omits B5 — `state.nutrition` is always consumed by the nutrition block, so a positional "leaf unused" test cannot express B5's inertness; parity + jaxpr SHA cover it. State that in the test module docstring so nobody later "completes" the set and gets a false failure. | `developer` |

**Cost of being wrong now:** unchanged from addendum 1 — no data loss; the mechanics carry no wrong-conclusion risk at their inert values.

*Reviewed by: plan-reviewer — addendum 2, 2026-09-26*
