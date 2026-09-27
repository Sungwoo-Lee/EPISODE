---
title: "Balance metrics logged during rPPO training, plus a post-hoc companion"
topic: behavior
status: active
created: 2026-09-27
last_updated: 2026-09-27
---

# Balance metrics logged during rPPO training, plus a post-hoc companion

> **Status**: PLANNED (awaiting plan review and user approval; no code written)
> **Opened**: 2026-09-27
> **Related**: [[STUDY_PLAN]] (internal-state interaction study, Revisions 2, 2a and 2b: the balance measures and criteria) · study page `internal_state_interactions.template.html` §03 ("how balance is judged") and §07 ("what the training runs should measure") · [[BALANCE_SETTINGS_INVENTORY]] · [[WANDB_METRICS_REFERENCE]] · [[behavior_measure_toolkit_v1_plan]] (the last metric family added to this same logging loop) · [[TRAJECTORY_COLLECTION_PIPELINE]] · Known Bugs rows: *contemporaneous binning* (3 instances), *reconstructed felt-pain leak*, *rPPO continual stage swap keeps stage-0 metric accumulators*

---

## Context

The internal-state interaction study wants level-05-style worlds that are **balanced**. In a
balanced world the agent has to hide in bushes to heal, eat, and warm up by a fire, and each
of these takes a real share of its time. Each need drives its own behaviour: hungry agents eat
more, badly injured agents hide more, cold agents warm up more. No single danger causes most
deaths, and whether hiding is the right move depends on more than one body state at once (for
example, a hungry, injured agent should hide less than a well-fed one).

The study defined these tests on a planning simulator. It then decided that the real verdict
comes from **training ordinary agents (no modulator)** across candidate settings and measuring
the same things on the trained agents. Today, rPPO (the project's recurrent PPO trainer) logs
survival steps and cause of death, but none of the behaviour measures.

This plan adds them to rPPO's episode logging, so each dashboard point also reports:
- time shares: in a bush, on a warm cell, eating, elsewhere;
- eat, hide and warm-up rates split by body state, with hiding split both by true injury and by
  the injury the agent actually feels;
- the hiding gap for hungry agents versus fed agents.

These counts are read from data the rollout already produces, so training itself does not
change, and a test proves this. A separate offline script computes the one measure that
cannot be counted during training: whether knowing two body states predicts the agent's choice
better than knowing one. It reads recorded episodes.

---

## Analysis

### A1. Where rPPO episode metrics are produced today (verified 2026-09-27)

The pipeline has two halves. **Neither half computes a metric inside the JIT.** The jitted
rollout only *emits per-step raw values*. All accumulation happens in NumPy on the host.

| Stage | Where | What happens |
|---|---|---|
| Per-step raw values (device, jitted) | `src/models/recurrent_ppo_trainer.py:7-26` (`StepInfo` NamedTuple), filled at `:309-328` inside `collect_trajectories.scan_fn` (`:247-338`) | `StepInfo` is a copy of fields from `jax_step`'s `info` dict. It includes `ate_food`, `agent_in_bush` and `termination_reason`, and is returned in `Transition.step_info` with shape `[T, B]`. |
| Loss path | `train_iteration` (`:398-544`) | Reads `trajectories.step_info.termination_reason` for the real-death mask only (`:417`, `:437`, `:469`, `:495`, `:508`). **No other StepInfo field reaches the loss.** |
| Device→host | `train.py:1701-1711` | `info_np[k] = np.array(getattr(step_info, k))` for `BEHAVIOR_KEYS` (`train.py:1356`), `BEHAVIOR_DIST_KEYS`, `termination_reason`, `agent_in_bush`. |
| Per-episode accumulation (host) | `train.py:1741-1826` | A `for t in range(num_steps)` loop adds each row into per-env accumulators. On `done`, it builds `ep_data` (a dict that includes `termination_reason` and the length `l`) and pushes it into the rolling window `ep_window`, then resets that env slot. |
| Window aggregation + WandB | `train.py:1546-1593` (`_emit_episode_row`) | A mean over the window's episode dicts. `Episode/Term_*` is the fraction of the window's episodes with each code (`:1582-1584`), and `Episode/Steps` is the mean length (`:1561`). This function is shared by the two-level logging path (`:1814`) and the legacy path (`:1831`). |
| Stage transition wipe | `train.py:1627-1654` | Zeroes every per-env accumulator when a continual-learning stage changes. |

**Consequence for the design.** Everything the balance metrics need is either already in
`StepInfo` (`ate_food`, `agent_in_bush`, `termination_reason`) or is a pure read of the
**pre-step `state`** that `scan_fn` already holds, or of the pre-reset `next_state`. That
covers pre-step nutrition, injury, body temperature, the felt-injury percept, and the cell
temperature where the agent lands. None of these reads draws a random key or feeds the loss.

### A2. The one timing convention that matters (contemporaneous-binning class)

Known Bugs records **three** silent instances of the same analysis mistake. Each paired a body
state read at row `t` with an outcome at row `t`, when the action that produced row `t` was
chosen while the agent was still in row `t−1`. Inside `scan_fn` the correct pairing is
available without any shifting:

- **Predictor (body-state bin)**: read from `state`, the carry at the top of `scan_fn`. This is
  the exact state `get_observation` was called on (`:252`) and from which the action was
  sampled.
- **Outcome (in a bush / on a warm cell / ate)**: read from this step's `info` and from
  `next_state` (the pre-auto-reset state, `:275`). `info['agent_in_bush']` already uses the
  post-step position (`core.py:1272-1279`). `info['ate_food']` is "eat action taken on a food
  cell" (`core.py:990-1000`).

This is the same convention the planner's rollout uses (`planner.py:474-497`: pre-step
`n0, i0, t0` binned against this step's cell and activity). The thresholds therefore carry
over. A regression test (T3 below) pins the convention: it must fail if an implementer bins on
the post-step body state.

### A3. Felt injury: read the environment's own percept, do not reconstruct it

"Felt injury" is the interoceptive nociception percept: an alpha-kernel convolution of the
last 12 steps of injury, `sensor.py:169-185`, returning a value in [0, 1]. Two registry rows
bear on it:

- **Reconstructed felt-pain leak** (FIXED): an analysis re-derived the percept from recorded
  injury and got the episode boundary wrong. **This plan does not reconstruct.** In training it
  calls `sense_interoceptive_nociception(state, params)` on the same pre-step `state`. In the
  post-hoc script it reads the noise-free observation (`obs_true` in the trajectory store,
  `true_obs` in recordings). Either way, the value is the one the environment computed.
- **Contemporaneous binning** (3 instances): handled as in A2. The percept is read from the
  pre-step state.

Two consequences, both deliberate and to be documented in the metrics reference:

- **Noise.** The felt value is the **noise-free** percept. In worlds with perceptual noise on
  the interoceptive channel, the agent's input is this value plus noise. Binning on the noisy
  draw would blur the thresholds with a random quantity that is not part of the body state.
- **Units.** The percept is multiplied by `params.max_injury` so that the same 60 / 20 injury
  thresholds apply to both the true and the felt versions.

**A real effect, not a leak.** The felt-injury buffer is zeroed at reset (`core.py:2039`), so
an agent that starts badly injured *feels* nothing for its first few steps. Those steps fall
into the felt "≤ 20" bin. That is what the agent experiences, and it is exactly the true-vs-felt
difference the study wants to see.

### A4. "Warm cell": proposed definition and justification

**Proposal:** a step counts as *on a warm cell* when the temperature of the cell the agent lands
on is above the body-temperature setpoint:
`next_state.thermal_field[agent_row, agent_col] > params.temperature_setpoint` (0 °C in level 05).

| Why this and not the alternatives | |
|---|---|
| Matches the planner exactly | The planner's rollout uses `warm = cell > 0` (`planner.py:481`) with setpoint 0. The study's thresholds therefore carry over unchanged. In level 05 this selects the fire ring (≈ +8.8 °C) and a bush on the ring. It excludes open ground (≈ −30 °C) and the cooler diagonal (≈ −16 °C). |
| It is a property of the **cell**, not of the body | The alternative, "cell warmer than the body", depends on body temperature, which is the binning variable of the warming ratio. A cold agent at −14 °C on the −16 °C diagonal would not count, but a −14 °C agent on a −12 °C cell would, and the cold bin would get "warm" steps by construction. A cell-only definition keeps the numerator and the bin independent. |
| Physically meaningful | With `k_exchange`/`k_loss` the body settles at about ⅔ of the cell temperature (inventory §D). A cell above the setpoint is exactly a cell where staying pushes the body above the setpoint. |
| Edge case stated | The fire cell itself (≈ 77 °C, lethal in 2–3 steps) also counts as warm. Its step share is negligible, and it is kept rather than special-cased. |

`thermal_field` holds raw °C (`state.py:85-89`; `[0, 0]` when thermal is off). When thermal is
off (a static flag), the warm fields and keys are simply absent.

### A5. Thresholds (fixed as module constants, cited to the study plan)

| Measure | Low / "off" bin | High / "on" bin | Variable | Source |
|---|---|---|---|---|
| Eating | fed: `N ≥ 100` | hungry: `N < 60` | nutrition `N` (pre-step) | Rev 2a C1(a); `planner.py:484` |
| Hiding | barely injured: `I ≤ 20` | badly injured: `I ≥ 60` | injury (true, and felt × max_injury) | Rev 2a C1(c); `planner.py:489` |
| Warming | warm: `T ≥ 0` | cold: `T ≤ −5` | body temperature °C (pre-step) | user spec + Rev 2b (b′); see note |
| Combination (hiding gap) | fed: `80 ≤ N ≤ 160` | hungry: `N < 60` | nutrition × injury (true and felt) | Rev 2 B-hide; `planner.py:490-492` |
| Early death | length `≤ 20` | — | episode length | Rev 2a M2; `planner.py:521` (`death_t ≥ 20` ⇔ length ≥ 21) |

- **Warming edges.** The planner's rollout used strict `< −5` / `> 0`. The pre-registered
  per-decision measure (b′, Rev 2b) and the task spec use `≤ −5` / `≥ 0`. The plan follows the
  spec. The two differ only for a body exactly at the bound. That matters only in a world
  without random starting temperature, where every episode starts at exactly 0 °C (such
  episodes join the ≥ 0 bin).
- **Nutrition, not satiation.** The variable is `state.nutrition`, the energy store that
  starvation and over-eating are defined on and the planner's `N`. In level 05, satiation
  equals nutrition (scaling factor 1.0, inventory §A).
- **Constants, not config.** The thresholds are hard-coded as constants in
  `src/behavior/balance_metrics.py`, with a comment citing the study plan. They are
  measurement definitions, and letting them vary per run would make runs incomparable.
  Changing one is a code change with a plan. They are absolute units calibrated to the level-05
  family (max nutrition 200, max injury 100); the metrics reference must say so.

### A6. Zero denominators

Ratios are computed **once per window, from pooled step counts** (ratio of sums, never the mean
of per-episode ratios; test T4). When a bin has zero steps in the window, the corresponding
share, ratio and gap are **not logged** in that row, and WandB shows a gap. This follows the
existing `_append_per_measure_mean` pattern (`train.py:1413-1419`), which skips NaN. When the
"off" bin's share is 0, the ratio is not logged either ("not computable", Rev 2b N5). The
**denominator step counts are always logged**, including 0, so an absent ratio can be told
apart from a bug.

### A7. Death causes and survival: reuse, do not duplicate

`Episode/Term_*` and `Episode/Steps` already exist and are not touched. **One gap:** the
pre-registered death criterion excludes deaths in the first 20 steps (start-doomed episodes).
The existing Term_* shares cannot be split by early versus late after the fact, because the
window aggregates them. Proposed, and **pending user decision D2**: six derived keys computed
at emit time from the `l` and `termination_reason` already in every `ep_data`. They need no
new counters and no new device data.

### A8. Out of scope (checked)

- **Dreamer.** `src/algorithms/dreamer_srl/` has its own collector and its own logging
  (`dreamer_srl_main.py:1248`). The sheeprl bridge uses `src/behavior/episode_metrics.py`.
  Neither goes through `recurrent_ppo_trainer.StepInfo` or `train.py`'s rPPO loop. The Dreamer
  stack also has no body-state hooks for this, per the auto-memory note that the srl stack is
  the live one. Not touched.
- **Plain PPO / DQN / DRQN branches of `train.py`.** Not touched. The emit-time code is gated
  on the presence of balance counts in the episode dicts, which only the rPPO branch produces.
- **The planner-side B-need and B-choice measures.** These are simulator quantities, not
  logged in training (§07 of the page).

### A9. Safety for the 32 runs currently training from HEAD

**Implementation can proceed now without affecting them, under the conditions below.** Why:

1. A running `train.py` process has already imported `train.py` (as `__main__`),
   `recurrent_ppo_trainer.py`, the env modules and the config files. It has already traced and
   compiled `train_iteration`. Python does not re-read an imported module from disk, so editing
   these files on the NAS does not change a live process.
2. The **only** code a live run loads *later* comes from subprocesses at checkpoints:
   `scripts/eval/render_recordings_v2.py` (async MP4, `src/utils/async_render.py:56`) and
   `scripts/eval/experiment_eval_checkpoint.py` (`train.py:238`). A grep on 2026-09-27 shows
   that **neither imports** `recurrent_ppo_trainer`, `train`, or the new module. This plan does
   not modify `src/environment/*`, `src/utils/eval_recording.py`, or `src/environment/dashboard.py`,
   which those subprocesses do import.
3. The new logic lives in a **new** module (`src/behavior/balance_metrics.py`) that no live
   process references, so there is no lazy-import hazard.

**Conditions.**
- **(a)** Implement in a separate `git worktree` outside the repo directory, not in the shared
  working tree. Merge back when the tests are green. Other parallel sessions launch new runs
  from the shared tree, and a half-edited `train.py` there is the one real hazard.
- **(b)** Do not `git checkout` an older commit in the shared tree to produce the golden
  fixture in T1. Use the worktree.
- **(c)** Run the speed benchmark on a GPU that the 32 runs are not using. Check with the
  `gpu-status` skill and the diary.
- **(d)** Any **relaunch or resume** of those runs after the merge will run the new code
  (metrics on). T2 shows training dynamics are identical, but their WandB history would gain
  `Episode/Bal_*` keys partway through the run. If a run must stay byte-for-byte on its launch
  commit, relaunch it from a worktree pinned to that commit.

Those 32 runs will **not** carry the online balance keys. Judging them requires the post-hoc
script (Part C) on trajectory-store collections of their checkpoints, with the policy caveat in
C4.

---

## Implementation Plan

### Design

```
scan_fn (jitted, per step)                              host (NumPy, per iteration)
───────────────────────────                             ───────────────────────────
state (pre-step) ──► nutrition, injury, body_temp,      info_np + bal_np  [T,B]
                     felt = sense_interoceptive_  ─┐        │
                            nociception(state)*maxI│        ▼
next_state (pre-reset) ──► on_warm_cell            ├─► balance_metrics.step_counts(...) → C [T,B,K] (uint8)
info ──► ate_food, agent_in_bush (existing)       ─┘        │  (vectorised once per iteration)
                                                            ▼
             StepInfo.balance = BalanceStepInfo | None   episode_balance[B,K] += C[t]   (one op per t)
                                                            │ on done: ep_data['bal_counts'] = row copy; row = 0
                                                            ▼
                                             _emit_episode_row: balance_metrics.window_log(eps) → Episode/Bal_*
```

- **Static switch** `logging.episode.balance_metrics` (bool, mandatory for rPPO, pending
  decision D1). It is carried in `PPOConfig`, which is already a static jit argument
  (`train.py:1246`, `static_argnums=(6,)`). When `false`, `scan_fn` sets
  `StepInfo.balance=None`. The traced program and its outputs are then identical to today's,
  which T1 proves against a golden captured before the change. When `true`, the program gains
  a few extra outputs and **no change to any existing output** (T2).
- **One definition, two consumers.** `src/behavior/balance_metrics.py` is pure NumPy. Training
  calls it with arrays built from `StepInfo`, and the post-hoc script calls it with arrays built
  from recorded episodes. Online and offline numbers therefore come from the same function.
- **K counters per step** (`uint8` masks, summed into `int32` per-episode counts). The counter
  list is `COUNTER_NAMES` in the module, in this order:

| # | Counter | Meaning (one step counts 1 if…) |
|---|---|---|
| 0 | `steps` | always |
| 1–4 | `bush`, `warm`, `eat`, `elsewhere` | lands in a bush; lands on a warm cell; ate; none of the three (the first three may overlap, Rev 2a M1) |
| 5–8 | `n_hungry`, `eat_hungry`, `n_fed`, `eat_fed` | pre-step N < 60 (and ate); N ≥ 100 (and ate) |
| 9–12 | `n_inj_hi_true`, `bush_inj_hi_true`, `n_inj_lo_true`, `bush_inj_lo_true` | true I ≥ 60 (and in bush); I ≤ 20 (and in bush) |
| 13–16 | same with `_felt` | felt I (× max_injury) |
| 17–20 | `n_cold`, `warm_cold`, `n_warmT`, `warm_warmT` | pre-step T ≤ −5 (and on warm cell); T ≥ 0 (and on warm cell) |
| 21–28 | `{n,bush}_inj_{hi,lo}_true_{hungry,fed}` | the hiding counters 9–12 restricted to hungry (N < 60) / fed (80 ≤ N ≤ 160) |
| 29–36 | same with `_felt` | |

K = 37. When thermal is off, counters 2, 17–20 are identically 0 and their keys are not
emitted. `elsewhere` is then "not bush and not eating". When interoceptive nociception is off,
the `_felt` counters are 0 and their keys are not emitted. Both flags are read from `params`
(static) and are recomputed on a stage swap (see the Known Bugs "stage swap keeps stage-0
accumulators" row: the flags must follow the **new** stage's params).

### WandB keys (all under `Episode/`, so the existing `define_metric("Episode/*", step_metric="Episode/Number")` at `train.py:1043` applies)

Shares are fractions in [0, 1] of the steps in the window. `N` keys are **window-total step
counts**. Unlike other `Episode/*` keys they are not per-episode means, and the reference doc
must say so.

| Family | Keys |
|---|---|
| Time split | `Episode/Bal_TimeBush`, `Episode/Bal_TimeWarm`, `Episode/Bal_TimeEat`, `Episode/Bal_TimeElsewhere` |
| Eating vs hunger | `Episode/Bal_EatShare_Hungry`, `Episode/Bal_EatShare_Fed`, `Episode/Bal_EatRatio`, `Episode/Bal_N_Hungry`, `Episode/Bal_N_Fed` |
| Hiding vs injury (S ∈ `True`, `Felt`) | `Episode/Bal_BushShare_InjHi_{S}`, `Episode/Bal_BushShare_InjLo_{S}`, `Episode/Bal_HideRatio_{S}`, `Episode/Bal_N_InjHi_{S}`, `Episode/Bal_N_InjLo_{S}` |
| Warming vs temperature | `Episode/Bal_WarmShare_Cold`, `Episode/Bal_WarmShare_Warm`, `Episode/Bal_WarmRatio`, `Episode/Bal_N_Cold`, `Episode/Bal_N_Warm` |
| Combination (S × F ∈ `Hungry`, `Fed`) | `Episode/Bal_BushShare_InjHi_{S}_{F}`, `Episode/Bal_BushShare_InjLo_{S}_{F}`, `Episode/Bal_HideGap_{S}_{F}` (= Hi − Lo), `Episode/Bal_HideRatio_{S}_{F}`, `Episode/Bal_N_InjHi_{S}_{F}`, `Episode/Bal_N_InjLo_{S}_{F}` |
| Late deaths (D2, if approved) | `Episode/Bal_EarlyDeathShare` (share of episodes dying at length ≤ 20), `Episode/Bal_LateDeathShare` (share dying at length ≥ 21: the 5 % gate), `Episode/Bal_LateDeath_{Starvation,Overeating,Injury,Thermal}` (cause shares **among late deaths**) |

Criterion mapping, for the analyzer:

| Study criterion | Keys |
|---|---|
| 1, time | `Bal_Time*` |
| 2, drive: eat and hide ratio ≥ 2 | `Bal_EatRatio`, `Bal_HideRatio_True`; the rollout warming ratio `Bal_WarmRatio` is report-only per Rev 2b N1 |
| 3, deaths | `Bal_LateDeath*` |
| 4, survival | existing `Episode/Steps` |
| 5, fed hiding ≥ 2× | `Bal_HideRatio_True_Fed` |
| Combination during training | `Bal_HideGap_*` |

### File Changes

#### Part A: training-time metrics

##### `src/behavior/balance_metrics.py` (NEW, pure NumPy, no JAX)

- Module docstring: plain-language purpose, citation to [[STUDY_PLAN]] Rev 2–2b, and the
  timing convention (pre-step body state versus post-step outcome).
- Constants: `HUNGRY_LT = 60.0`, `FED_GE = 100.0`, `COMB_FED_LO, COMB_FED_HI = 80.0, 160.0`,
  `INJ_HI_GE = 60.0`, `INJ_LO_LE = 20.0`, `COLD_LE = -5.0`, `WARM_GE = 0.0`,
  `EARLY_DEATH_MAX_LEN = 20`, `COUNTER_NAMES` (the 37 above, in order), `K = len(COUNTER_NAMES)`.
- `resolve_balance_metrics_flag(config) -> bool`: `config.get_mandatory('logging.episode.balance_metrics')`,
  which raises `ValueError` unless the value is a real `bool`. No default.
- `step_counts(nutrition, injury, felt_injury, body_temp, on_warm_cell, ate_food, in_bush, *, thermal_on, felt_on) -> np.ndarray[..., K] uint8`.
  All inputs have the same leading shape (`[T, B]` in training, `[n]` post-hoc). `felt_injury`,
  `body_temp` and `on_warm_cell` may be `None` exactly when their flag is off. Assert this; do
  not substitute a value.
- `window_log(counts_list: list[np.ndarray[K]], *, thermal_on, felt_on) -> dict[str, float]`:
  sums the counts, then emits the keys in the table, applying the A6 rules.
- `late_death_log(lengths, reasons) -> dict[str, float]` (D2). Reason codes 2–5 are deaths,
  per `episode_metrics.py:40-44`. Cause shares are not emitted when there are 0 late deaths.

##### `src/models/recurrent_ppo_trainer.py`

- `:7-26`: add a new NamedTuple `BalanceStepInfo(nutrition, injury, felt_injury, body_temp, on_warm_cell)`.
  Unused fields are `None`, per the static flags. Add a field `balance: Any` to `StepInfo`
  (required, **no default**) and set it explicitly at `:309-328`.
- `:231`: `collect_trajectories(..., return_mode="MC", *, balance_metrics: bool)`, a required
  keyword-only argument.
- `scan_fn` (after `:275`, before the auto-reset block):

```python
if balance_metrics:   # static Python bool — resolved at trace time
    felt = (jax.vmap(sense_interoceptive_nociception, in_axes=(0, None))(state, env_params)[:, 0]
            * env_params.max_injury) if env_params.interoceptive_nociception_enabled else None
    if env_params.thermal_enabled:
        cell_t = jax.vmap(lambda f, p: f[p[0], p[1]])(next_state.thermal_field, next_state.agent_pos)
        on_warm = cell_t > env_params.temperature_setpoint
        body_t = state.body_temp
    else:
        on_warm = body_t = None
    balance = BalanceStepInfo(nutrition=state.nutrition, injury=state.injury_level,
                              felt_injury=felt, body_temp=body_t, on_warm_cell=on_warm)
else:
    balance = None
```

  `state` is the pre-step carry and `next_state` is pre-reset. Import
  `sense_interoceptive_nociception` next to `get_observation` (`:234`). The developer confirms
  that the params field names (`interoceptive_nociception_enabled`, `thermal_enabled`,
  `temperature_setpoint`, `max_injury`) are static or traced as used in `sensor.py:492` and
  `core.py:473`. A Python `if` on a traced value would raise at trace time, which is a
  detectable failure.
- `train_iteration` (`:407`): pass `balance_metrics=config.balance_metrics`.

##### `train.py`

- `:102-114` `PPOConfig`: add `balance_metrics: bool` **before** the defaulted fields, so that
  it has no default. Set it in the rPPO construction at `:1226` from
  `resolve_balance_metrics_flag(config)`. The plain-PPO construction at `:1328` does not use
  `PPOConfig.balance_metrics` in its trainer, but the NamedTuple now requires it, so set
  `balance_metrics=False` there **explicitly**, with a comment ("plain PPO has no balance
  logging; not a fallback").
- After the `info_np` extraction (`:1701-1711`), when `ppo_config.balance_metrics`, convert
  `step_info.balance` fields with `np.asarray` and compute `bal_C = step_counts(...)`, of shape
  `[T, B, K]`, once per iteration.
- Accumulator `episode_balance = np.zeros((num_envs, K), np.int32)`, allocated next to
  `episode_behavior` (`:1362`). In the `t` loop (`:1741`): `episode_balance += bal_C[t]`. On
  done (`:1765-1790`): `ep_data['bal_counts'] = episode_balance[i].copy()`, plus a reset of the
  row in the reset block (`:1816-1826`).
- Stage-transition wipe (`:1627-1654`): `episode_balance[:] = 0`, and recompute
  `bal_thermal_on` / `bal_felt_on` from the new `params`.
- `_emit_episode_row` (`:1546-1593`): when any episode in `eps` has `'bal_counts'`, call
  `ep_log.update(window_log([ep['bal_counts'] for ep in eps if 'bal_counts' in ep], ...))`.
  With D2, also `ep_log.update(late_death_log(...))` from `ep['l']` and `ep['termination_reason']`.

##### `configs/train/recurrent_ppo.yaml` (logging block)

```yaml
logging:
  episode:
    smoothing_episodes: 5000
    interval_episodes: 4000
    # Balance metrics (docs/develop/active/behavior/BALANCE_METRICS_TRAINING_LOGGING.md):
    # time split + need-behaviour ratios + hiding gap, Episode/Bal_* keys. Pure function of
    # rollout data; training is bit-identical on/off (tests/models/test_balance_metrics_parity.py).
    balance_metrics: true
```

##### `configs/train/default.yaml`

Add a **comment only** (no value) in its logging block: "`logging.episode.balance_metrics` is
rPPO-only and lives in `recurrent_ppo.yaml`; it is deliberately absent here because a value in
this fallback layer would silently satisfy a missing rPPO key." This departs from the
"`default.yaml` declares every knob" convention (CONFIG_GUIDE §7) for a stated reason, and the
guide row says so.

#### Part B: tests (all must be added; T1–T4 are the ones that prove the claims)

| # | Test | Proves | Fails when |
|---|---|---|---|
| T1 | `tests/models/test_balance_metrics_parity.py::test_off_matches_pre_change_golden` | Switch off gives outputs identical to today's code | Any bitwise difference in `collect_trajectories` outputs (all `Transition` fields, final state, key, bootstrap value) versus `tests/fixtures/balance_metrics/pre_change_rollout.npz`. The fixture is generated on the pre-change commit, in a worktree, with the tiny GRU fixture used by `tests/models/test_mc_fixed_mode.py:225-236`, a fixed key and 8 steps on CPU. A small generator script is committed next to it and records the commit SHA inside the npz. |
| T2 | `…::test_train_iteration_on_vs_off_bitwise` | Metrics on does not change training | A jitted `train_iteration` run for 3 iterations from identical model, optimizer, key and env state, on and off. Any bitwise difference in losses, every parameter leaf, optimizer state, env state, key, or any shared `Transition` field fails the test. |
| T3 | `tests/behavior/test_balance_metrics.py::test_pre_step_state_is_binned` | The A2 convention in the **real** `scan_fn` | A tiny thermal config with the eat action. The agent is placed on food at N = 59 and eats (post-step N ≈ 63), so the step must count in `eat_hungry`. The agent is placed in a bush at I = 61 and rests (post-step I ≈ 56), so the step must count in `bush_inj_hi_true`. Both fail if post-step state is used. |
| T4 | `…::test_window_ratio_is_ratio_of_sums` | A6 pooling | Episode 1 is hungry for 1 step and ate; episode 2 is hungry for 99 steps and never ate. The pooled share is 0.01, while the mean of per-episode ratios would be 0.5. |
| T5 | `…::test_zero_denominator_omits_share_ratio_but_logs_N` | A6 | A share, ratio or gap key is present with an empty bin, or an `N` key is absent. |
| T6 | `…::test_thermal_off_and_felt_off_emit_no_keys` | Static gating | Any `Warm*`, `TimeWarm` or `*_Felt*` key is emitted with its flag off. |
| T7 | `…::test_warm_cell_uses_cell_not_body` | A4 | A −16 °C cell with a −14 °C body counts as warm. |
| T8 | `…::test_elsewhere_is_complement` and `…::test_late_death_partition` | Definitions | `elsewhere` is not equal to `¬(bush ∨ warm ∨ eat)`; episode length 20 is not counted as early, or length 21 as late. |
| T9 | `…::test_flag_is_mandatory` | No fallback | `resolve_balance_metrics_flag` on a config without the key, or with a non-bool value, does not raise `ValueError`. |
| T10 | Extend `tests/training/test_continual_bm_transition.py` (subprocess `train.py`, 2 stages) with the balance switch on, **including a thermal-on → thermal-off stage pair** | Stage-swap wipe and flag recompute | Crash, or a warm key emitted after the swap to thermal off. |

**Existing tests to update** (a signature change, not a behaviour change):
- `tests/models/test_mc_fixed_mode.py`, `tests/models/test_mc_raw_mode.py` and
  `tests/models/test_gae_norm_mode.py`: add `balance_metrics=False` to the `fake_collect`
  signatures (`test_mc_fixed_mode.py:94` and siblings), to each `_Cfg`, and to each direct
  `rpt.collect_trajectories(...)` call (`test_mc_fixed_mode.py:246`, `test_mc_raw_mode.py:274,288`,
  `test_gae_norm_mode.py:248,264`).

**Full suite**: `tests/models/`, `tests/behavior/`, `tests/training/`, `tests/env/` must stay
green. The env parity families are untouched, because no env code changes.

#### Part C: post-hoc companion (separate script)

##### `scripts/analysis/balance_posthoc.py` (NEW; `scripts/<subdir>/<file>.py` → repo root via `parents[2]`)

**Purpose.** For one or more trained runs, compute (1) the same counters and keys as Part A,
through `balance_metrics.step_counts` / `window_log`, from recorded episodes; and (2) the
**full combination measure**, which cannot be accumulated online.

**Inputs**: `--store <dir> [<dir> …]` (trajectory store; uses `scripts/analysis/core/store.py`
and `scan.py`) **or** `--recordings <glob>` (`.rec.gz` from `eval_rollout.py --record`), plus
`--out <json>`. The run config comes from the store manifest or recording metadata. It is
never guessed.

**C1. Where each quantity comes from**

| Quantity | Trajectory store | Recordings (`.rec.gz`) |
|---|---|---|
| Nutrition, true injury | columns `nutrition`, `injury_level` (state at t) | snapshot `nutrition`, `injury_level` |
| Body temperature | **not a column** (user deferred it). Recovered from `obs_true` at the `"Body Temperature"` slice. Offset comes from `get_observation_breakdown(params)`. `sensor.py:479-488` appends `state.body_temp` in **raw °C** when `thermal_enabled and thermal_body_temp_observable`. **Verified in source 2026-09-27.** If `body_temp_observable` is false, the script exits with an error (no fallback). | snapshot `body_temp` (`eval_recording.py:66-67`) |
| Felt injury | `obs_true` `"Interoceptive Nociception"` slice × `max_injury` | `true_obs` same slice (`eval_recording.py:80-100`) |
| Warm cell at row t | Thermoception block, **centre element** (offset 0 of the diamond, `sensor.py:65-90`), plus body temperature when `thermal.relative` is true (`default.yaml:594`). The store holds no `thermal_field`. | snapshot `thermal_field[agent_row, agent_col]` |
| Ate / in bush | `ate_food` (arriving at t), `agent_in_bush` (state at t) | per-step fields of the recording |

**Timing (contemporaneous-binning guard).** Store rows are "state at t" and the action
arriving at t. Predictors come from **row t−1** and outcomes from **row t**, within an episode
only (t ≥ 1, same `episode_seed`). This matches the online A2 convention exactly and must be
stated in the script's docstring.

**Precision.** When the store was written with `obs_precision: float16`, body temperature
(range ±15) is quantised to about 0.01 °C and felt injury to about 0.05 injury units. The
effect at the thresholds is negligible. Record the precision in the output JSON.

**C2. Combination measure (the planner's estimator, made honest for finite noisy data).**
The planner's gain is "best accuracy knowing two body variables − best accuracy knowing one",
where each accuracy comes from predicting "the most common choice in each cell"
(`planner.py:240-271`). Applied **in-sample** to trained-agent data, it is biased upwards,
because pairs have more cells and each cell's majority fits its own noise. The script
therefore:
- bins nutrition in 20-unit steps (0–200), injury in 10-unit steps (0–100; the true and felt
  versions give separate results), and body temperature in 2 °C steps (−15 to +15);
- labels each decision step with a choice category (see D3);
- computes accuracy **held out by episode**: 5 folds split on `episode_seed`, majority learned
  on 4 folds and scored on the fifth;
- reports the gain with a 95 % bootstrap interval over episodes and a **label-permutation
  null**: labels are shuffled within episodes, preserving each episode's choice frequencies,
  200 permutations. The null is the gain expected from bin count alone.

**C3. Outputs.** A JSON with the Part A keys (same names, with a `posthoc_` provenance field),
the combination block (single and pair accuracies, gain, CI, null quantiles, per injury
source), row counts used / available per quantity (guide §11's "how much data" rule), and the
run IDs and store paths.

**C4. Stated limit.** Store and recording episodes come from the **evaluation** policy.
`action` is `argmax(logits)` (`trajectory_store.py:121`), whereas training metrics come from
the **sampling** policy with exploration. The two sets of numbers answer the same question for
two policies and must not be pooled or thresholded interchangeably. The output JSON records
which policy produced it.

**C5. Post-hoc tests** (`tests/analysis/test_balance_posthoc.py`):
- (i) On a real reset plus 5 steps of the level-05 config: the `get_observation(apply_noise=False)`
  body-temperature slice equals `state.body_temp`, and centre plus body equals
  `thermal_field[pos]` bit-exactly in float32. This proves the C1 recovery paths.
- (ii) A synthetic 3-episode table where the true gain is known (the choice depends only on
  N × I jointly) gives a positive held-out gain, and a table with a choice that depends on N
  only gives a gain inside the permutation null.
- (iii) The row t−1 / row t pairing, shown on a hand-built store fragment where a
  contemporaneous read gives a different count.

#### Part D: documentation (same change)

| Doc | Change |
|---|---|
| `docs/develop/active/behavior/WANDB_METRICS_REFERENCE.md` | New section, "Balance metrics (rPPO)": every `Episode/Bal_*` key, its definition, the ratio-of-sums rule, window-total `N` keys, the zero-denominator rule, noise-free felt injury, absolute-unit thresholds, and the training-policy versus eval-policy caveat. Bump `last_updated`. |
| `docs/environment/CONFIG_GUIDE.md` §7 | A table row for `logging.episode.balance_metrics` (`default.yaml`: absent by design; `recurrent_ppo.yaml`: `true`), with the reason it is absent from `default.yaml`. |
| `docs/environment/02_config_schema.md` (`training:` block around `:376`) | Add the `logging.episode.balance_metrics` line under the configs/train layer notes. |
| `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` | Row for `scripts/analysis/balance_posthoc.py`: HAND + TEST, `parents[2]`, imports `src.behavior.balance_metrics` and `scripts/analysis/core/*`. |
| `docs/environment/CONFIG_CRITICAL_SETTINGS.md` | **No entry.** A logging switch is not a registry setting (checked 2026-09-27: the registry lists no `logging.*` keys). The verifier confirms that no registry setting changed. |
| Study docs (owned by `experiment-designer`) | Hand-off: a back-link from [[STUDY_PLAN]] and page §07 to this plan. Not written here, because `docs/experiments/` is outside this role's write scope. |

### Cost estimate

| Item | Estimate | Basis |
|---|---|---|
| Extra device output per rollout | ≈ 17 B/step × `T·B` = 17 × 128 × 128 ≈ **0.28 MB** | 4 × float32 + 1 bool per step; T = `agent.sequence_length` (128), B = `training.num_envs` (128 in `recurrent_ppo.yaml`) |
| Device→host transfer | same 0.28 MB/iteration | alongside the existing StepInfo transfer (`train.py:1705`) |
| Extra jitted compute | one 12-tap dot product (felt) + one gather (cell temp) per env-step | negligible next to the network forward |
| Host masks | `[T,B,K]` uint8 ≈ **0.6 MB** transient; ~40 vectorised ops over 16 k elements once per iteration (≲ 1 ms) | |
| Host accumulate | **one** `+=` of a `[B,K]` array per `t` → 128 ops/iteration (≲ 1 ms) | one op per t instead of K ops per t (design choice) |
| Rolling window | 5000 episodes × 37 × int32 ≈ **0.74 MB** | `smoothing_episodes` 5000 |
| Emit | a stack-and-sum of 5000×37 per emitted row (every 4000 episodes), a few ms | |
| Compile | one extra trace when on; the off path compiles exactly as today | |

**Expected step-time change: < 1 %.** The developer **measures** it (checkpoint 7). Per the
verification protocol, more than 5 % needs discussion and more than 15 % blocks the merge.

---

## Decisions needed from the user (before implementation)

- **D1: switch or always-on?** *Recommended: switch.* Add a mandatory on/off key
  (`logging.episode.balance_metrics`, set to `true` in the rPPO training config). The switch
  lets the parity test compare on against off in one build, and "off" stays exactly today's
  program. The alternative is no key and always on: one fewer config key, but parity then rests
  only on the pre-change golden (T1).
- **D2: log late-death shares?** *Recommended: yes.* The pre-registered death criterion ignores
  deaths in the first 20 steps. The existing death shares cannot be split by early versus late
  after the fact. This adds six keys, computed from data already in each episode record, with
  no new counters.
- **D3: what counts as the agent's "choice" in the offline combination measure?**
  *Recommended: "heading to".* Each step is labelled with the first of {bush, eat, warm cell}
  the agent reaches within the next 10 steps, and "open" otherwise. This is closest to the
  planner's choice ("go and rest in cover"). Travel steps then carry the destination, instead
  of all reading as "open". The alternative is to label only what the agent is doing on that
  step. The script reports both; the decision is which one is primary.

---

## Checkpoints

- [ ] 1. Worktree created outside the repo directory. T1 golden generated **there, on the
  pre-change commit** (SHA recorded in the npz and in the Implementation Report). No checkout
  in the shared tree.
- [ ] 2. `balance_metrics.py` unit tests T4–T9 green before any trainer edit.
- [ ] 3. `StepInfo.balance is None` when off, confirmed by printing `jax.tree_util.tree_structure(trajectories.step_info)` off vs on. T1 green.
- [ ] 4. T2 green on CPU. Then on one free GPU: 20 iterations on the level-05 world, **off vs
  off** first. If off-vs-off is not bitwise on GPU (XLA GPU reductions can be
  nondeterministic), report that and compare on vs off against the off-vs-off spread instead
  of bitwise.
- [ ] 5. T3 green, and fails when the pre-step reads are temporarily swapped to `next_state`
  (red-green demonstration recorded in the report).
- [ ] 6. CPU smoke: `train.py` with the level-05 world, 4 envs, `WANDB_MODE=offline`, enough
  episodes for 2 emitted rows. The offline run file contains the `Episode/Bal_*` keys, the time
  shares sum to at least 1 (they overlap) with `TimeElsewhere` ≤ 1, and no share is outside
  [0, 1].
- [ ] 7. Speed: same free GPU, same world, 128 envs, 300 iterations after a 20-iteration
  warm-up, off vs on. Report s/it both ways and host-loop time.
- [ ] 8. T10 green (stage swap, thermal on → off).
- [ ] 9. Post-hoc C5 tests green. Run the script on one existing level-05 trajectory store and
  one `.rec.gz` set, and report key values next to the same run's online row where one exists.
  They are not expected to match (C4), but a gross mismatch is flagged.
- [ ] 10. Docs in Part D updated. `regen_dev_index.py` run. `SCRIPTS_DEPENDENCY_MAP.md` row
  present.

## Implementation Report

> **Implemented by**:
> **Date**:

## Verification Report

> **Verified by**:
> **Date**:

| File | Change | Status | Notes |
|------|--------|:------:|-------|
| | | | |

**Conclusion**:
