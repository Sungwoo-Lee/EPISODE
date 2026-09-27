---
title: WandB Metrics Reference
topic: behavior
status: active
created: 2026-03-09
last_updated: 2026-09-27
---

# WandB Metrics Reference

> **Status**: COMPLETED
> **Opened**: 2026-03-09
> **Related**: [train.py](../train.py), [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)

---

## Context

This document provides a comprehensive reference of all metrics logged to Weights & Biases (WandB) during training in `train.py`. It serves as context for LLM agents working on training analysis, metric additions, or dashboard configuration.

## Analysis

All metrics are extracted from `train.py`. The logging structure varies by algorithm, with some metrics shared across all algorithms and others algorithm-specific. WandB step metrics are configured at initialization (lines 385–390) to control which x-axis each metric group uses.

### Step Metric Definitions

Defined at WandB init (`train.py:385–390`):

| Pattern | X-Axis |
|---------|--------|
| `Episode/*` | `Episode/Number` |
| `loss/*` | `iteration` |
| `*` (everything else) | `timesteps` |

---

## Episode Metrics: Aggregation Pipeline & Interpretation

All `Episode/*` metrics follow a two-stage aggregation pipeline. Understanding this pipeline is essential for interpreting values correctly.

### Stage 1: Per-Episode Accumulation

During each episode, per-step data from the environment's `info` dict is accumulated into per-environment buffers (`episode_behavior`, `episode_dist_sums`). When an episode ends (done=True), these accumulators produce a single `ep_data` dict for that episode:

| Metric Category | Per-Step Accumulation | Per-Episode Value | Example |
|---|---|---|---|
| **Event counts** (FoodEaten, PredatorHits, etc.) | `episode_behavior[k] += info[k]` each step | Raw sum over all steps in the episode | Agent ate food 3 times → `ate_food = 3` |
| **Damage metrics** (TotalDamage, DamagePredator, etc.) | `episode_behavior[k] += info[k]` each step | Raw sum of damage over the episode | 5.0 damage per predator hit × 15 hits → `damage_predator = 75.0` |
| **Distance metrics** (MeanDistFood, MeanDistPredator) | `episode_dist_sums[k] += info[k]` each step | Sum divided by episode length: `dist_sum / max(ep_length, 1)` | Sum of distances = 150.0 over 50 steps → `dist_to_food = 3.0` |
| **Termination reason** | Captured once at episode end | Integer code: 1=MaxSteps, 2=Starvation, 3=Overeating, 4=Injury, 5=Thermal | Agent died from injury → `termination_reason = 4` |
| **Reward** | Accumulated by the environment | Total episode return | — |
| **Steps** | Counted by the environment | Episode length (integer) | — |

After creating `ep_data`, the accumulators for that environment are reset to zero. The episode is appended to `iteration_episodes`.

### Stage 2: Iteration-Level Aggregation (what gets logged to WandB)

At the end of each training iteration, **all episodes that completed during that iteration** are aggregated with `np.mean()` into a single WandB log call. This means:

- **Each WandB data point represents the mean across N episodes**, where N is the number of episodes that happened to finish during that iteration.
- **N varies per iteration.** With parallel environments, multiple episodes can finish in the same iteration, or none at all (in which case no `Episode/*` data is logged for that iteration).
- **This is standard RL logging convention** — the same pattern used by Stable Baselines3, CleanRL, and other frameworks.

#### How to interpret each metric type

| Metric | WandB Value Represents | Why It Can Be Non-Integer |
|---|---|---|
| `Episode/Reward` | Mean total return across N episodes | Average of different episode rewards |
| `Episode/Steps` | Mean episode length across N episodes | e.g., episodes of length 42 and 58 → 50.0 |
| `Episode/FoodEaten` | Mean food eaten per episode across N episodes | e.g., 3 episodes ate [0, 1, 0] food → 0.33 |
| `Episode/PredatorHits` | Mean predator hits per episode | Same averaging as above |
| `Episode/TotalDamage` | Mean cumulative damage per episode | Already float from per-step damage values |
| `Episode/MeanDistFood` | Mean of per-episode mean distances | Double-averaged: per-step → per-episode → per-iteration |
| `Episode/Term_Injury` | Fraction of N episodes ending in injury | e.g., 8 of 10 episodes → 0.80 |
| `Episode/Term_Thermal` | Fraction of N episodes ending in a thermal death (frozen or overheated) | Always 0.0 unless `thermal.enabled=true` |

#### Practical example

If an iteration has 4 completed episodes with `FoodEaten = [0, 0, 1, 3]`:
- `Episode/FoodEaten` = `np.mean([0, 0, 1, 3])` = **1.0**
- Early in training when agents rarely eat, most episodes have 0 food → mean is a small float like **0.14**

#### WandB x-axis

`Episode/*` metrics use `Episode/Number` (cumulative episode count) as the x-axis, not `timesteps` or `iteration`. This is set via `wandb.define_metric("Episode/*", step_metric="Episode/Number")`.

---

## Metrics by Algorithm

### Shared Metrics (All Algorithms)

Logged whenever episodes complete during an iteration. See above for aggregation details.

| Metric Key | Type | Per-Episode Aggregation | Description |
|------------|------|------------------------|-------------|
| `Episode/Reward` | float | sum of rewards | Mean episode return across the iteration |
| `Episode/Reward_Min` | float | — | Minimum single-episode return in the iteration |
| `Episode/Reward_Max` | float | — | Maximum single-episode return in the iteration |
| `Episode/Steps` | float | step count | Mean episode length across the iteration |
| `Episode/Number` | int | — | Cumulative total episodes completed (x-axis) |
| `Episode/FoodEaten` | float | sum of `ate_food` events | Mean food eaten per episode |
| `Episode/PredatorHits` | float | sum of `hit_predator` events | Mean predator hits per episode |
| `Episode/DangerHits` | float | sum of `hit_hiding_predator` events | Mean danger zone hits per episode |
| `Episode/RestCount` | float | sum of `rested` events | Mean rest actions per episode |
| `Episode/Collisions` | float | sum of `event_collided` events | Mean collisions per episode |
| `Episode/TotalDamage` | float | sum of `damage` | Mean total damage taken per episode |
| `Episode/DamagePredator` | float | sum of `damage_predator` | Mean damage from predators per episode |
| `Episode/DamageDanger` | float | sum of `damage_hiding_predator` | Mean damage from danger zones per episode |
| `Episode/DamageObstacle` | float | sum of `damage_obstacle` | Mean damage from obstacles per episode |
| `Episode/MeanDistFood` | float | sum of `dist_to_food` / ep_length | Mean per-step distance to food, averaged across episodes |
| `Episode/MeanDistPredator`| float | sum of `dist_to_pred` / ep_length | Mean per-step distance to nearest predator, averaged across episodes |
| `Episode/Term_Starvation` | float | binary (1 if reason==2) | Fraction of episodes ending in starvation (energy < 0.0) |
| `Episode/Term_Injury` | float | binary (1 if reason==4) | Fraction of episodes ending in injury (health < 0.0) |
| `Episode/Term_Overeating` | float | binary (1 if reason==3) | Fraction of episodes ending in overeating (stomach > capacity) |
| `Episode/Term_MaxSteps` | float | binary (1 if reason==1) | Fraction of episodes reaching maximum episode length |
| `Episode/Term_Thermal` | float | binary (1 if reason==5) | Fraction of episodes ending in a thermal death — body temperature outside `[thermal.min_temperature, thermal.max_temperature]`. Emitted on every run; identically 0.0 when the temperature system is off |
| `timesteps` | int | — | Global environment step counter |
| `iteration` | int | — | Training iteration counter |

> **Note**: All behavioral metrics are shared across all algorithms (RecurrentPPO, DreamerV3, DQN, DRQN, PPO). The 4 termination fractions sum to 1.0 within each iteration.

### Evaluation Metrics (All Algorithms, at Checkpoints)

Logged when `training.stats_during_training` is enabled, triggered at checkpoint intervals (`train.py:1465–1466`).

| Metric Key | Type | Description |
|------------|------|-------------|
| `Eval/MeanReward` | float | Mean reward over evaluation episodes |
| `Eval/MeanLength` | float | Mean episode length over evaluation episodes |

---

### RecurrentPPO

**Loss metrics** — logged every iteration (`train.py:866–900`):

| Metric Key | Type | Description |
|------------|------|-------------|
| `loss/total` | float | Combined PPO loss (policy + value + entropy) |
| `loss/policy` | float | Policy (actor) surrogate loss |
| `loss/value` | float | Value function MSE loss |
| `loss/entropy` | float | Entropy bonus (negative = encouraging exploration) |
| `loss/grad_norm` | float | Global gradient norm across all parameters |

**Modulator metrics** — logged only when `agent.modulation` is configured and non-null (`train.py:876–894`):

| Metric Key | Type | Description |
|------------|------|-------------|
| `modulator/grad_norm` | float | Gradient norm of modulator parameters specifically |
| `modulator/gamma_uni_mean` | float | Mean of unimodal multiplicative gain (z_unimodal) |
| `modulator/gamma_uni_std` | float | Std of unimodal multiplicative gain |
| `modulator/gamma_multi_mean` | float | Mean of multimodal multiplicative gain (z_multimodal) |
| `modulator/gamma_multi_std` | float | Std of multimodal multiplicative gain |
| `modulator/z_memory_mean` | float | Mean of memory gate signal (z_memory) |
| `modulator/z_memory_std` | float | Std of memory gate signal |
| `modulator/temperature_mean` | float | Mean policy temperature |
| `modulator/temperature_min` | float | Min policy temperature across batch |
| `modulator/temperature_max` | float | Max policy temperature across batch |

**PreActivation-only modulator metrics** — logged only when `modulation.type == "PreActivation"` (`train.py:888–894`):

| Metric Key | Type | Description |
|------------|------|-------------|
| `modulator/beta_uni_mean` | float | Mean of unimodal additive bias (z_unimodal_add) |
| `modulator/beta_uni_std` | float | Std of unimodal additive bias |
| `modulator/beta_multi_mean` | float | Mean of multimodal additive bias (z_multimodal_add) |
| `modulator/beta_multi_std` | float | Std of multimodal additive bias |

#### Balance metrics (rPPO) — `Episode/Bal_*`

Added 2026-09-27 by [[BALANCE_METRICS_TRAINING_LOGGING]] for the internal-state interaction study ([study plan](../../../experiments/active/internal_state_interactions/STUDY_PLAN.md)). They answer: *does the agent split its time between hiding in bushes, eating and warming up, and does each body need drive its own behaviour?* Switched by `logging.episode.balance_metrics` (true in `configs/train/recurrent_ppo.yaml`); logged on the same `Episode/*` rows as the metrics above (x-axis `Episode/Number`, window = `logging.episode.smoothing_episodes`). Code: `src/behavior/balance_metrics.py`. Training is bit-identical with the switch on or off.

**How each step is counted.** Body state (nutrition `N`, true injury `I`, felt injury, body temperature `T`) is read **before** the step — what the agent saw when it chose the action. The outcome (in a bush, on a warm cell, ate) is read **after** the step. (Pairing post-step body state with the outcome is the "contemporaneous binning" mistake recorded three times in the Known Bugs registry.)

| Family | Keys | Definition |
|---|---|---|
| Time split | `Bal_TimeBush`, `Bal_TimeWarm`, `Bal_TimeEat`, `Bal_TimeElsewhere`, `Bal_TimeNearFire` | Fraction of the window's steps that land in a bush / on a warm cell / eat / none of those three. Bush, warm and eat may overlap, so the four shares sum to ≥ 1. `Bal_TimeNearFire` is **report-only** (see below). |
| Eating vs hunger | `Bal_EatShare_Hungry`, `Bal_EatShare_Fed`, `Bal_EatRatio`, `Bal_N_Hungry`, `Bal_N_Fed` | Share of steps that eat among hungry (`N < 60`) and fed (`N ≥ 100`) steps; ratio = hungry ÷ fed. |
| Hiding vs injury (`S` = `True`, `Felt`) | `Bal_BushShare_InjHi_S`, `Bal_BushShare_InjLo_S`, `Bal_HideRatio_S`, `Bal_N_InjHi_S`, `Bal_N_InjLo_S` | Share of steps in a bush among badly injured (`I ≥ 60`) and barely injured (`I ≤ 20`) steps; ratio = injured ÷ barely injured. **True injury decides** the study's hiding criterion; felt is reported beside it. |
| Warming vs body temperature | `Bal_WarmShare_Cold`, `Bal_WarmShare_Warm`, `Bal_WarmRatio`, `Bal_N_Cold`, `Bal_N_Warm` | Share of steps on a warm cell among cold (`T ≤ −5 °C`) and warm (`T ≥ 0 °C`) steps. Logged, **not pass/fail** in training (study Rev 2c). |
| Combination (`F` = `Hungry` `N < 60`, `Fed` `80 ≤ N ≤ 160`) | `Bal_BushShare_InjHi_S_F`, `Bal_BushShare_InjLo_S_F`, `Bal_HideGap_S_F`, `Bal_HideRatio_S_F`, `Bal_N_InjHi_S_F`, `Bal_N_InjLo_S_F` | The hiding measures restricted to hungry / fed steps. `HideGap` = injured share − barely-injured share. `Bal_HideRatio_True_Fed` is the study's "fed hiding ≥ 2×" criterion. |
| Deaths | `Bal_EarlyDeathShare`, `Bal_LateDeathShare`, `Bal_LateDeath_{Starvation,Overeating,Injury,Thermal}` | Early = death (reason codes 2–5) at episode length ≤ `logging.episode.balance_early_death_max_steps` (20); late = longer. Early and late shares divide by **all** window episodes, step-cap truncations included (the study's 5 % late-death gate). Cause shares are **among late deaths** and are absent when there are none. |

**Rules a reader needs.**

- **Ratio of pooled sums.** Every share and ratio is computed once per window from step counts summed over all the window's episodes — never a mean of per-episode ratios. This weights long-lived episodes more heavily than short ones (the study's planner pooled fixed-length rollouts instead; same rule, different mixture of episodes).
- **`N` keys are window-total step counts**, not per-episode means like the other `Episode/*` keys.
- **Empty bins.** When a bin has no steps in the window, its share, ratio and gap are **not logged** (WandB shows a gap). A ratio is also not logged when the "off" bin's share is 0. The `N` keys are always logged, including 0, so an absent ratio can be told apart from a bug.
- **Switched-off modalities.** With thermal off, every `Warm`/`Cold`/`NearFire`/`TimeWarm` key is absent; with interoceptive nociception off, every `_Felt` key is absent.
- **Warm cell** = the landing cell's temperature is above the body setpoint (0 °C in level 05) — a property of the cell, not of the body. **Near fire** = a cell the fire heats (above the open-ground upper edge, −29 °C in level 05) but still at or below the setpoint: the fire's whole outer, blurred ring (in one level-05 reset: 5 warm cells, 8 near-fire cells, 87 open). The planner the study calibrated on never modelled these cells. `Bal_TimeWarm` alone decides the "≥ 10 % of time" criterion; if a run fails it while `Bal_TimeWarm + Bal_TimeNearFire` would pass, report that in words ("the agent warms on the fire's outer ring, not on the ring itself") and route a possible re-definition to the user — do not re-score.
- **Felt injury** is the environment's own noise-free interoceptive-nociception percept × `max_injury` (same 60 / 20 thresholds). Its buffer is zeroed at reset and covers the last 12 steps, so it **under-reads for about the first 12 steps of every episode**. With random starting injury (level 05) this inflates `Bal_N_InjLo_Felt` at episode starts by construction and pulls `Bal_HideRatio_Felt` down for a reason unrelated to the policy.
- **Absolute thresholds, calibrated to level 05** (max nutrition 200, max injury 100). Each run records the calibration it was measured under in its WandB config as `balance_calibration` (and `balance_calibration_stage_<k>` on each continual stage swap), also printed to stdout as `[balance] ...`: `max_nutrition` and `max_injury` from the run's params, every bin edge, the early-death cut-off, the thermal/felt flags and, with thermal on, the setpoint and open-ground upper edge. Judge comparability across worlds from this block.
- **Training policy, not evaluation policy.** These numbers come from the exploring (sampling) training policy. Numbers computed later from evaluation recordings or trajectory stores come from the greedy evaluation policy; never pool or threshold the two interchangeably.

---

### DreamerV3

**Episode metrics** — logged every iteration when episodes complete (`train.py:1036–1047`). Uses the shared Episode metrics listed above.

**Training/World Model metrics** — logged every 10 iterations (`train.py:1077–1103`). The specific keys depend on what the `DreamerTrainer` returns in its `metrics` dict. They are routed by prefix:

| Prefix Pattern | WandB Panel | Example Keys |
|----------------|-------------|--------------|
| `loss_actor*`, `loss_critic*`, `mean_*`, `entropy*` | `Behavior/` | `Behavior/loss_actor`, `Behavior/mean_entropy` |
| `loss_model*`, `loss_recon*`, `loss_kl*`, `loss_rew*`, `loss_cont*`, `loss_dyn*`, `loss_rep*`, `model_*` | `WorldModel/` | `WorldModel/loss_model`, `WorldModel/model_reward_mae` |
| `mod_*` | `Modulator/` | `Modulator/mod_z_reward_mean` |
| Other keys | Root namespace | — |

**Buffer/Ratio metrics** — logged every 10 iterations (`train.py:1078–1089`):

| Metric Key | Type | Description |
|------------|------|-------------|
| `Params/effective_replay_ratio` | float | Cumulative gradient steps / global env steps |
| `Params/positive_buffer_blocks` | int | Sequence blocks stored in positive-reward buffer (mixture mode only) |
| `Params/positive_buffer_utilization` | float | Positive buffer fill ratio (mixture mode only) |
| `Params/main_buffer_blocks` | int | Sequence blocks stored in main replay buffer |

---

### DQN

Logged every iteration (`train.py:1192–1205`):

| Metric Key | Type | Description |
|------------|------|-------------|
| `loss/dqn` | float | TD loss |
| `train/epsilon` | float | Current epsilon-greedy exploration rate |

---

### DRQN

Logged every iteration (`train.py:1308–1321`):

| Metric Key | Type | Description |
|------------|------|-------------|
| `loss/drqn` | float | TD loss |
| `train/epsilon` | float | Current epsilon-greedy exploration rate |

---

### PPO (non-recurrent)

Logged every iteration (`train.py:1361–1376`):

| Metric Key | Type | Description |
|------------|------|-------------|
| `loss/ppo_total` | float | Combined PPO loss |

> **Note**: Unlike RecurrentPPO, vanilla PPO does **not** log per-component loss breakdown (policy/value/entropy) to WandB. Only the aggregate total is logged.

---

## WandB Configuration

Controlled by CLI flags and config YAML (`train.py:354–392`):

| Setting | CLI Flag | Config Key | Default |
|---------|----------|------------|---------|
| Disable WandB | `--no-wandb` | `wandb.disabled` | `false` |
| Project | `--wandb-project` | `wandb.project` | (mandatory) |
| Entity | `--wandb-entity` | `wandb.entity` | (mandatory) |
| Group | `--wandb-group` | `wandb.group` | (mandatory) |
| Run name | `--wandb-name` | — | Falls back to `tag` |
| Resume ID | `--wandb-resume-id` | — | — |

Code is also logged via `wandb.run.log_code(".", include_fn=lambda path: path.endswith(".py"))` (line 392).
