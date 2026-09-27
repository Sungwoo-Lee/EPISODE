---
title: "Balance metrics logged during rPPO training, plus a post-hoc companion"
topic: behavior
status: active
created: 2026-09-27
last_updated: 2026-09-27
---

# Balance metrics logged during rPPO training, plus a post-hoc companion

> **Status**: PLANNED, Revision 1 (plan-reviewer findings addressed; awaiting re-review and user decisions D1–D3; no code written)
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

## Revision 1 (2026-09-27): response to the plan review

The first draft was reviewed adversarially and judged not ready (feedback appended at the end
of this doc; full report in [[plan_balance_metrics_training_logging]]). The blocking problem was
procedural: the draft said "merge back when the tests are green" without protecting the
untracked training outputs in `results/` or saying what to do if the merge conflicts. The rest
were definitional gaps. This revision changes the plan as follows; the user decisions D1–D3
stay open.

| Review finding | Change in this revision | Where |
|---|---|---|
| 🔴 Merge-back with no data snapshot and no conflict rule | New merge-back procedure: rebase inside the worktree, snapshot `results/`, fast-forward-only merge, **stop and hand back on any conflict** | A9(a), new "Merge-back procedure", Checkpoints 1 and 11 |
| 🟡 T7 contradicts the warm-cell definition | T7 rewritten to agree with A4 (cell above setpoint, independent of body) | Part B, T7 |
| 🟡 Warm-cell rule never tested on the cooler diagonal | A4 states the gap; new `near_fire` counter and `Bal_TimeNearFire` key; how it relates to criterion 1 is stated | A4, counter table, keys, criterion mapping |
| 🟡 T1/T2 run on a world with no thermal and no felt injury | T1, T2 and Checkpoint 4 run on a level-05-derived world with thermal and interoceptive nociception on | Part B, Checkpoint 4 |
| 🟡 Level-05 thresholds applied silently in every world | The calibration (max nutrition, max injury, every absolute bin edge) is written into the run's logged config at start and on each stage swap, read from `params` and the module constants, no defaults | A5, `train.py` changes, C3 |
| 🟡 C4 caveat must reach the study page | Added to the experiment-designer hand-off | Part D |
| 🟢 Worktree location | `.claude/worktrees/balance_metrics` (project convention, gitignored) | A9(a) |
| ❓ Late-death denominator; level-05 episode cap | Denominator = all episodes in the window (study Rev 2b N5). Level 05 inherits `max_steps: 500` from the default environment config, the same 500-step horizon the planner used, so the 5 % gate transfers | A7 |
| ❓ Felt injury reads zero at episode start | Stated for the analyzer (level 05 starts injury uniformly in 0–100) | A3, Part D |
| ❓ Pooling weights long episodes | Named next to the ratio-of-sums rule | A6 |

**Study plan Revision 2c, recorded here.** The study pre-registered, after this plan was first
drafted, that in training the **warming** part of criterion 2 is logged but **not pass/fail**
(a well-regulated agent is rarely cold, so the over-time ratio sits near 1 even for the ideal
agent). Criterion 2 in training is therefore eating ratio ≥ 2 and hiding ratio ≥ 2, with both
true and felt injury reported and **true injury deciding** the hiding criterion. The criterion
mapping below follows this. Warming time share (`Bal_TimeWarm`) is a separate matter: it feeds
criterion 1 (time split), which remains pass/fail.

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

**What the analyzer must be told (Rev 1).** The buffer covers the last
`interoceptive_kernel_length` = 12 steps, so the felt value under-reads for roughly the first
12 steps of **every** episode, not only badly injured starts. Level 05 inherits
`random_start_injury: true` with start injury uniform in 0–100 (from level 03), so a large share
of episode starts are truly injured but felt as barely injured. This inflates
`Bal_N_InjLo_Felt` at episode starts by construction and pulls `Bal_HideRatio_Felt` down for a
reason unrelated to the policy. The plan keeps these steps (it is what the agent feels, and true
injury decides the criterion under Rev 2c) and does not add an exclusion window. The
sentence goes into the metrics reference (Part D) and into the module docstring.

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

**Gap stated (Rev 1): the diagonal cells were never in the planner's world.** "Matches the
planner exactly" is true only for the cells the planner modelled. Its world has two cell
temperatures, open ground at −30 °C and the fire ring at +8.8 °C (`planner.py:9-10, 35-37`), and
the study plan (E5) says the cooler diagonal cells around the fire are not modelled. So the rule
`cell > setpoint` was never exercised on a ≈ −16 °C diagonal cell. Under this plan a trained agent
parked on the diagonal does **not** count as warm: its body settles near ⅔ × −16 ≈ −10.7 °C,
which lands in the cold bin, and its steps fall into `elsewhere`. The definition is kept,
because "the cell pushes the body above its setpoint" is the physically right meaning of
warming up. What changes is that the diagonal becomes visible instead of silently folded into
`elsewhere`:

- **New counter `near_fire`**: the step lands on a cell that the fire heats but that is still at
  or below the setpoint,
  `params.thermal_default_temp_high < cell_t ≤ params.temperature_setpoint`.
  `thermal_default_temp_high` is the upper edge of the per-episode open-ground temperature
  range (−29 °C in level 05), so any cell above it has received heat from a fire. Outside the
  blur radius the field equals the open-ground value exactly, so the ring of `near_fire` cells is
  finite. It is a property of the cell only, like `warm`, and it may overlap with `bush`. It is
  disjoint from `warm` by construction. Its steps that are neither bush nor eating stay in `elsewhere` (the `elsewhere`
  definition is unchanged).
- **How it feeds criterion 1 (time split, each activity ≥ 10 % of time).** The pre-registered
  warm-up share is `Bal_TimeWarm` alone, and that key decides criterion 1. `Bal_TimeNearFire` is
  reported beside it and is **not** added to it. If a run fails criterion 1 on warming while
  `Bal_TimeWarm + Bal_TimeNearFire` would pass, the analyzer reports the case in words ("the
  agent warms on the cooler diagonal, not on the ring") and routes a possible re-definition to
  the user and `experiment-designer`. It does not re-score the run.
- **Checkpoint 6** prints how many cells of one level-05 reset fall in each class (warm,
  near_fire, open), so the extent of the ring is checked on the real field, not assumed.
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
- **Calibration recorded with every run (Rev 1).** The switch is on for every rPPO run in every
  world, but the bins only mean what the study means in a level-05-scaled body. So each run
  writes the calibration it was measured under into its logged config, where it cannot be lost:
  `wandb.config.update({"balance_calibration": {...}}, allow_val_change=True)` at run start, and
  again on every continual-learning stage swap under `balance_calibration_stage_<k>`. The block
  holds `max_nutrition` and `max_injury` **read from the live `params`** (never a default), and
  every absolute bin edge **read from the module constants** (`HUNGRY_LT`, `FED_GE`,
  `COMB_FED_LO`, `COMB_FED_HI`, `INJ_HI_GE`, `INJ_LO_LE`, `COLD_LE`, `WARM_GE`,
  `EARLY_DEATH_MAX_LEN`), plus `temperature_setpoint` and `thermal_default_temp_high` when
  thermal is on. The same block is printed to stdout, so it also lands in the run log. Nothing
  is skipped or rescaled when a world differs from level 05: the numbers are recorded, and the
  analyzer judges comparability from them. The post-hoc JSON (C3) carries the same block.

### A6. Zero denominators

Ratios are computed **once per window, from pooled step counts** (ratio of sums, never the mean
of per-episode ratios; test T4). When a bin has zero steps in the window, the corresponding
share, ratio and gap are **not logged** in that row, and WandB shows a gap. This follows the
existing `_append_per_measure_mean` pattern (`train.py:1413-1419`), which skips NaN. When the
"off" bin's share is 0, the ratio is not logged either ("not computable", Rev 2b N5). The
**denominator step counts are always logged**, including 0, so an absent ratio can be told
apart from a bug.

**Assumption named (Rev 1).** Pooling step counts weights long-lived episodes more heavily. The
planner pooled fixed-horizon rollouts, whereas training episodes end at different times, so the
same ratio-of-sums convention averages over a different mixture of episodes. This is not wrong,
but it is a difference the metrics reference states next to the rule.

### A7. Death causes and survival: reuse, do not duplicate

`Episode/Term_*` and `Episode/Steps` already exist and are not touched. **One gap:** the
pre-registered death criterion excludes deaths in the first 20 steps (start-doomed episodes).
The existing Term_* shares cannot be split by early versus late after the fact, because the
window aggregates them. Proposed, and **pending user decision D2**: six derived keys computed
at emit time from the `l` and `termination_reason` already in every `ep_data`. They need no
new counters and no new device data.

**Denominators (Rev 1, per study Rev 2b N5).** `Bal_LateDeathShare` = number of window episodes
that died (reason codes 2–5) at length ≥ 21, divided by **all** episodes in the window,
including episodes truncated at the step cap and episodes that died early. This is the
quantity the 5 % gate is pre-registered on ("after excluding deaths in the first 20 steps").
`Bal_EarlyDeathShare` uses the same all-episodes denominator. The four
`Bal_LateDeath_{cause}` keys are shares **among late deaths** (denominator = late deaths) and
are not emitted when there are none.

**Episode cap checked (2026-09-27).** None of the level-03, -04 or -05 configs overrides
`environment.max_steps`, so level 05 inherits `max_steps: 500` from
`configs/environment/default.yaml:7`. The planner's balance rollout also runs 500 steps
(`rollout_balance(..., max_steps=500, ..., early=20)`, `planner.py:427`). The 5 % gate was
calibrated on the same horizon and transfers. A world with a different cap would change the
share of episodes that can die late; the calibration block (A5) does not record `max_steps`,
because it is already in the run's logged environment config.

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
- **(a)** Implement in a separate `git worktree` at `.claude/worktrees/balance_metrics` (the
  project's convention; gitignored at `.gitignore:51`, and on the NAS so it survives a container
  restart), not in the shared working tree. Other parallel sessions launch new runs from the
  shared tree, and a half-edited `train.py` there is the one real hazard. Merge back **only** by
  the procedure below.
- **(b)** Do not `git checkout` an older commit in the shared tree to produce the golden
  fixture in T1. Use the worktree.
- **(c)** Run the speed benchmark on a GPU that the 32 runs are not using. Check with the
  `gpu-status` skill and the diary.
- **(d)** Any **relaunch or resume** of those runs after the merge will run the new code
  (metrics on). T2 shows training dynamics are identical, but their WandB history would gain
  `Episode/Bal_*` keys partway through the run. If a run must stay byte-for-byte on its launch
  commit, relaunch it from a worktree pinned to that commit.

#### Merge-back procedure (Rev 1; the review's Critical finding)

`train.py` is edited by parallel sessions most days, so a conflict at merge time is the likely
case, and a conflicted merge followed by cleanup is how `results/` was lost once. The developer
follows these steps in order and records each command's outcome in the Implementation Report:

1. **Rebase inside the worktree**, never in the shared tree, onto the current `v4.0` tip (same
   repository, so no fetch is needed): `git -C .claude/worktrees/balance_metrics rebase v4.0`.
2. **Conflict rule.** If the rebase reports any conflict: `git rebase --abort` in the worktree,
   **stop**, and hand back to the user with the list of conflicted files. Do not resolve
   conflicts by hand without the user, and do not retry with a different strategy.
3. After a clean rebase, rerun the full test list (Part B) in the worktree. Red → stop.
4. **Snapshot** the untracked data in the shared tree, immediately before merging:
   `cp -a results /tmp/results-bk-$(date +%s)` (run from the repo root). Record the path.
5. **Fast-forward only**, in the shared tree (which is on `v4.0`):
   `git merge --ff-only balance_metrics`, with git wrapped in `timeout` inside a retry loop
   per CLAUDE.md. If it refuses because `v4.0` moved since step 1, return to step 1 once; if it
   refuses because an uncommitted change from another session touches a file in the branch
   ("would be overwritten"), **stop and hand back**. Never `git stash`, `git checkout -f`,
   `git reset`, or `git clean` (with or without `-x`) to make the merge go through.
6. Remove the worktree with `git worktree remove` only after the merge landed.

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
| 37 | `near_fire` | lands on a fire-heated cell at or below the setpoint (A4, Rev 1); overlaps `bush` and `eat`, never `warm`; the rest falls in `elsewhere` |

K = 38. When thermal is off, counters 2, 17–20 and 37 are identically 0 and their keys are not
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
| Time split | `Episode/Bal_TimeBush`, `Episode/Bal_TimeWarm`, `Episode/Bal_TimeEat`, `Episode/Bal_TimeElsewhere`, `Episode/Bal_TimeNearFire` (report-only, Rev 1) |
| Eating vs hunger | `Episode/Bal_EatShare_Hungry`, `Episode/Bal_EatShare_Fed`, `Episode/Bal_EatRatio`, `Episode/Bal_N_Hungry`, `Episode/Bal_N_Fed` |
| Hiding vs injury (S ∈ `True`, `Felt`) | `Episode/Bal_BushShare_InjHi_{S}`, `Episode/Bal_BushShare_InjLo_{S}`, `Episode/Bal_HideRatio_{S}`, `Episode/Bal_N_InjHi_{S}`, `Episode/Bal_N_InjLo_{S}` |
| Warming vs temperature | `Episode/Bal_WarmShare_Cold`, `Episode/Bal_WarmShare_Warm`, `Episode/Bal_WarmRatio`, `Episode/Bal_N_Cold`, `Episode/Bal_N_Warm` |
| Combination (S × F ∈ `Hungry`, `Fed`) | `Episode/Bal_BushShare_InjHi_{S}_{F}`, `Episode/Bal_BushShare_InjLo_{S}_{F}`, `Episode/Bal_HideGap_{S}_{F}` (= Hi − Lo), `Episode/Bal_HideRatio_{S}_{F}`, `Episode/Bal_N_InjHi_{S}_{F}`, `Episode/Bal_N_InjLo_{S}_{F}` |
| Late deaths (D2, if approved) | `Episode/Bal_EarlyDeathShare` (episodes dying at length ≤ 20 ÷ all window episodes), `Episode/Bal_LateDeathShare` (episodes dying at length ≥ 21 ÷ **all** window episodes, truncations included: the 5 % gate, Rev 2b N5), `Episode/Bal_LateDeath_{Starvation,Overeating,Injury,Thermal}` (cause shares **among late deaths**) |

Criterion mapping, for the analyzer:

| Study criterion | Keys |
|---|---|
| 1, time (each activity ≥ 10 %) | `Bal_TimeBush`, `Bal_TimeWarm`, `Bal_TimeEat` decide; `Bal_TimeNearFire` is report-only and is not added to `Bal_TimeWarm` (A4) |
| 2, drive: eat and hide ratio ≥ 2 | `Bal_EatRatio`, `Bal_HideRatio_True` (true injury decides; `_Felt` reported, with the A3 start-of-episode caveat); `Bal_WarmRatio` is logged but not pass/fail in training (study Rev 2c) |
| 3, deaths (late deaths ≤ 5 % of all episodes; no cause dominates) | `Bal_LateDeathShare`, `Bal_LateDeath_*` |
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
  `EARLY_DEATH_MAX_LEN = 20`, `COUNTER_NAMES` (the 38 above, in order), `K = len(COUNTER_NAMES)`.
- `calibration_record(params, *, thermal_on) -> dict` (Rev 1): returns the A5 block. Reads
  `params.max_nutrition`, `params.max_injury` and, when thermal is on,
  `params.temperature_setpoint` and `params.thermal_default_temp_high` by attribute access
  (an `AttributeError` is the failure, never a default), and the bin edges from the constants.
- `resolve_balance_metrics_flag(config) -> bool`: `config.get_mandatory('logging.episode.balance_metrics')`,
  which raises `ValueError` unless the value is a real `bool`. No default.
- `step_counts(nutrition, injury, felt_injury, body_temp, on_warm_cell, near_fire, ate_food, in_bush, *, thermal_on, felt_on) -> np.ndarray[..., K] uint8`.
  All inputs have the same leading shape (`[T, B]` in training, `[n]` post-hoc). `felt_injury`,
  `body_temp`, `on_warm_cell` and `near_fire` may be `None` exactly when their flag is off. Assert this; do
  not substitute a value.
- `window_log(counts_list: list[np.ndarray[K]], *, thermal_on, felt_on) -> dict[str, float]`:
  sums the counts, then emits the keys in the table, applying the A6 rules.
- `late_death_log(lengths, reasons) -> dict[str, float]` (D2). Reason codes 2–5 are deaths,
  per `episode_metrics.py:40-44`. Early and late shares use all window episodes as the
  denominator (A7). Cause shares are among late deaths and are not emitted when there are 0.

##### `src/models/recurrent_ppo_trainer.py`

- `:7-26`: add a new NamedTuple `BalanceStepInfo(nutrition, injury, felt_injury, body_temp, on_warm_cell, near_fire)`.
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
        near_fire = (cell_t > env_params.thermal_default_temp_high) & ~on_warm   # A4, Rev 1
        body_t = state.body_temp
    else:
        on_warm = near_fire = body_t = None
    balance = BalanceStepInfo(nutrition=state.nutrition, injury=state.injury_level,
                              felt_injury=felt, body_temp=body_t, on_warm_cell=on_warm,
                              near_fire=near_fire)
else:
    balance = None
```

  `state` is the pre-step carry and `next_state` is pre-reset. Import
  `sense_interoceptive_nociception` next to `get_observation` (`:234`). The developer confirms
  that the params field names (`interoceptive_nociception_enabled`, `thermal_enabled`,
  `temperature_setpoint`, `thermal_default_temp_high` (`state.py:392`), `max_injury`) are static or traced as used in `sensor.py:492` and
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
- **Calibration record (A5, Rev 1).** When `ppo_config.balance_metrics` is true: after
  `wandb.init` and before the first iteration, `wandb.config.update({"balance_calibration":
  calibration_record(params, thermal_on=...)}, allow_val_change=True)` and print the same dict.
  On each stage swap, the same call under key `balance_calibration_stage_<k>` from the new
  stage's `params`. When `WANDB_MODE` is disabled the print is the record.
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
| T1 | `tests/models/test_balance_metrics_parity.py::test_off_matches_pre_change_golden` | Switch off gives outputs identical to today's code | Any bitwise difference in `collect_trajectories` outputs (all `Transition` fields, final state, key, bootstrap value) versus `tests/fixtures/balance_metrics/pre_change_rollout.npz`. The fixture is generated on the pre-change commit, in a worktree, with the tiny GRU network of `tests/models/test_mc_fixed_mode.py:225-236` but on a **level-05-derived world with thermal and interoceptive nociception both on** (Rev 1): the level-05 config loaded through the trainer's own loader, with only `num_envs` reduced (e.g. 4); a fixed key and 8 steps on CPU. The test asserts `params.thermal_enabled` and `params.interoceptive_nociception_enabled` are true before comparing, so a silently thermal-off fixture fails. A small generator script is committed next to it and records the commit SHA inside the npz. |
| T2 | `…::test_train_iteration_on_vs_off_bitwise` | Metrics on does not change training | Same level-05-derived world as T1, thermal and interoceptive nociception on (asserted), so the "on" path really traces the felt, warm-cell and near-fire reads (Rev 1). A jitted `train_iteration` run for 3 iterations from identical model, optimizer, key and env state, on and off. The test also asserts that `step_info.balance.felt_injury`, `.on_warm_cell` and `.near_fire` are arrays, not `None`, in the "on" run. Any bitwise difference in losses, every parameter leaf, optimizer state, env state, key, or any shared `Transition` field fails the test. |
| T3 | `tests/behavior/test_balance_metrics.py::test_pre_step_state_is_binned` | The A2 convention in the **real** `scan_fn` | A tiny thermal config with the eat action. The agent is placed on food at N = 59 and eats (post-step N ≈ 63), so the step must count in `eat_hungry`. The agent is placed in a bush at I = 61 and rests (post-step I ≈ 56), so the step must count in `bush_inj_hi_true`. Both fail if post-step state is used. |
| T4 | `…::test_window_ratio_is_ratio_of_sums` | A6 pooling | Episode 1 is hungry for 1 step and ate; episode 2 is hungry for 99 steps and never ate. The pooled share is 0.01, while the mean of per-episode ratios would be 0.5. |
| T5 | `…::test_zero_denominator_omits_share_ratio_but_logs_N` | A6 | A share, ratio or gap key is present with an empty bin, or an `N` key is absent. |
| T6 | `…::test_thermal_off_and_felt_off_emit_no_keys` | Static gating | Any `Warm*`, `TimeWarm` or `*_Felt*` key is emitted with its flag off. |
| T7 | `…::test_warm_cell_uses_cell_not_body` | A4 (rewritten in Rev 1 to agree with it) | Two cases, setpoint 0 °C, open-ground upper edge −29 °C. (a) A −16 °C cell with a −20 °C body (the cell is warmer than the body): must count as **not warm** and as `near_fire`. (b) A +8.8 °C cell with a +10 °C body (the cell is cooler than the body): must count as **warm** and not `near_fire`. Fails if either case is scored by comparing cell with body. Plus (c) a −30 °C cell: neither warm nor `near_fire`. |
| T8 | `…::test_elsewhere_is_complement` and `…::test_late_death_partition` | Definitions | `elsewhere` is not equal to `¬(bush ∨ warm ∨ eat)`; episode length 20 is not counted as early, or length 21 as late. |
| T9 | `…::test_flag_is_mandatory` | No fallback | `resolve_balance_metrics_flag` on a config without the key, or with a non-bool value, does not raise `ValueError`. |
| T10 | Extend `tests/training/test_continual_bm_transition.py` (subprocess `train.py`, 2 stages) with the balance switch on, **including a thermal-on → thermal-off stage pair** | Stage-swap wipe, flag recompute, per-stage calibration record | Crash, a warm or near-fire key emitted after the swap to thermal off, or no `balance_calibration_stage_1` record in the run's stdout. |
| T11 | `…::test_calibration_record_reads_params` (Rev 1) | A5 | The record does not carry `params.max_nutrition` / `max_injury` of a params object set to non-level-05 values (e.g. 150, 80), or is missing any bin-edge constant, or returns a value when `max_injury` is absent from params (must raise). |

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
| Warm cell / near fire at row t | Thermoception block, **centre element** (offset 0 of the diamond, `sensor.py:65-90`), plus body temperature when `thermal.relative` is true (`default.yaml:594`). The store holds no `thermal_field`. | snapshot `thermal_field[agent_row, agent_col]` |
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
the A5 calibration block from `calibration_record` on the run's own params,
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
| `docs/develop/active/behavior/WANDB_METRICS_REFERENCE.md` | New section, "Balance metrics (rPPO)": every `Episode/Bal_*` key, its definition, the ratio-of-sums rule and its long-episode weighting (A6), window-total `N` keys, the zero-denominator rule, noise-free felt injury **and its ≈ 12-step zero start that inflates `Bal_N_InjLo_Felt` (A3)**, absolute-unit thresholds and where the per-run calibration record lives (A5), the diagonal-cell gap and `Bal_TimeNearFire` being report-only (A4), the late-death denominators (A7), and the training-policy versus eval-policy caveat. Bump `last_updated`. |
| `docs/environment/CONFIG_GUIDE.md` §7 | A table row for `logging.episode.balance_metrics` (`default.yaml`: absent by design; `recurrent_ppo.yaml`: `true`), with the reason it is absent from `default.yaml`. |
| `docs/environment/02_config_schema.md` (`training:` block around `:376`) | Add the `logging.episode.balance_metrics` line under the configs/train layer notes. |
| `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` | Row for `scripts/analysis/balance_posthoc.py`: HAND + TEST, `parents[2]`, imports `src.behavior.balance_metrics` and `scripts/analysis/core/*`. |
| `docs/environment/CONFIG_CRITICAL_SETTINGS.md` | **No entry.** A logging switch is not a registry setting (checked 2026-09-27: the registry lists no `logging.*` keys). The verifier confirms that no registry setting changed. |
| Study docs (owned by `experiment-designer`) | Hand-off, sequenced **after** the merge lands: a back-link from [[STUDY_PLAN]] and page §07 to this plan; page §07 states the C4 caveat (online numbers are from the exploring training policy, post-hoc numbers from the greedy evaluation policy; never pooled or thresholded interchangeably) and the A4 rule that `Bal_TimeNearFire` is report-only. Not written here, because `docs/experiments/` is outside this role's write scope. |

### Cost estimate

| Item | Estimate | Basis |
|---|---|---|
| Extra device output per rollout | ≈ 18 B/step × `T·B` = 18 × 128 × 128 ≈ **0.29 MB** | 4 × float32 + 2 bool per step; T = `agent.sequence_length` (128), B = `training.num_envs` (128 in `recurrent_ppo.yaml`) |
| Device→host transfer | same 0.28 MB/iteration | alongside the existing StepInfo transfer (`train.py:1705`) |
| Extra jitted compute | one 12-tap dot product (felt) + one gather (cell temp) per env-step | negligible next to the network forward |
| Host masks | `[T,B,K]` uint8 ≈ **0.6 MB** transient; ~40 vectorised ops over 16 k elements once per iteration (≲ 1 ms) | |
| Host accumulate | **one** `+=` of a `[B,K]` array per `t` → 128 ops/iteration (≲ 1 ms) | one op per t instead of K ops per t (design choice) |
| Rolling window | 5000 episodes × 38 × int32 ≈ **0.76 MB** | `smoothing_episodes` 5000 |
| Emit | a stack-and-sum of 5000×38 per emitted row (every 4000 episodes), a few ms | |
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

- [x] 1. Worktree `.claude/worktrees/balance_metrics`, branch `balance_metrics` cut from `v4.0` at
  `dd887635`. T1 golden generated there on the unmodified commit (SHA `dd887635…` stored in the npz
  as `_meta_commit`); no checkout in the shared tree.
- [x] 2. `balance_metrics.py` unit tests T4–T9, T11 green.
- [x] 3. `StepInfo.balance` is `None` when off: `tree_structure(step_info)` has 18 leaves off, 24 on
  (`BalanceStepInfo`, 6 fields). T1 green.
- [x] 4. T2 green on CPU (level-05, thermal + felt injury asserted). GPU (102:1, RTX 4090), 20
  iterations: off-vs-off **bitwise identical** (844 arrays), so on-vs-off was compared bitwise too:
  **0 of 844 arrays differ**.
- [x] 5. T3 green; red when the pre-step reads are swapped to `next_state` (nutrition swap fails
  the `eat_hungry` assertion; injury swap fails the `bush_inj_hi_true` assertion).
- [x] 6. CPU smoke (level 05, 4 envs, offline WandB, small windows): 4 rows with 49–55 `Bal_*`
  keys; time shares sum to 1.000–1.001, `TimeNearFire ≤ TimeElsewhere + TimeBush + TimeEat`, no
  share outside [0, 1]; calibration block printed and written to the offline run config. Level-05
  reset: 5 warm / 8 near_fire / 87 open cells.
- [x] 7. Speed: GPU 102:1, 128 envs, 20 warm-up + 300 iterations each: 0.2792 → 0.2860 s/it
  (+2.4 %, inside the ±5 % block-to-block spread); host 3.4 ms/iteration. See report.
- [x] 8. T10 green (stage swap with the switch on; thermal-on → off pair impossible — see Deviations).
- [—] 9. Post-hoc companion: **dropped from scope** by user decision D3 (2026-09-27).
- [x] 10. Part D docs updated (WANDB_METRICS_REFERENCE, CONFIG_GUIDE §7, 02_config_schema). No
  `scripts/` change, so no SCRIPTS_DEPENDENCY_MAP row. `regen_dev_index.py`: see report.
- [ ] 11. Merge-back — see report.

## Implementation Report

> **Implemented by**: developer
> **Date**: 2026-09-27

**In one paragraph.** rPPO now logs the balance measures on every `Episode/*` dashboard row
(`Episode/Bal_*`: time split, eat / hide / warm-up rates by body state with true and felt injury,
the hungry-vs-fed hiding gap, and early/late death shares). The switch and the early-death cut-off
are required config keys with no default. Training is proven unchanged: with the switch off the
rollout is bit-identical to one captured before the change, and three (CPU) or twenty (GPU) full
training iterations with the switch on and off are bit-identical. The offline "choice" script
(Part C) was dropped by the user (D3) and is not implemented. Work was done in the worktree
`.claude/worktrees/balance_metrics` (branch `balance_metrics`).

### Files (by commit, branch `balance_metrics`)

| Commit | Files | What |
|---|---|---|
| `cbf8a02e` test | `tests/fixtures/balance_metrics/generate_pre_change_rollout.py`, `pre_change_rollout.npz` | T1 golden captured on unmodified `dd887635` (level-05, 4 envs, 8 steps, tiny GRU, MC, CPU; 70 arrays + `_meta_commit`). The generator uses the pre-change signature, so rerunning it after the change raises instead of writing a tautological golden. |
| `0bb857be` feat | `src/behavior/balance_metrics.py` (new) | 38 counters (`COUNTER_NAMES`), `step_counts`, `window_log` (pooled sums; empty bins omit share/ratio/gap, `N` always logged), `late_death_log`, `calibration_record`, `resolve_balance_metrics_flag`, `resolve_early_death_max_steps`. |
| | `src/models/recurrent_ppo_trainer.py` | `BalanceStepInfo`; `StepInfo.balance` (required); `collect_trajectories(..., *, balance_metrics)` required keyword; `scan_fn` reads pre-step `state` (nutrition, injury, felt = `sense_interoceptive_nociception`×`max_injury`, body temp) and pre-reset `next_state` landing cell (warm = `cell > setpoint`, near_fire = `cell > thermal_default_temp_high & ~warm`); `train_iteration` passes `config.balance_metrics`. |
| | `train.py` | `PPOConfig.balance_metrics` (no default); rPPO resolves both keys, plain PPO sets `False` explicitly; `episode_balance [B,K]` counters, one `+=` per t; `ep_data['bal_counts']`; wipe on stage swap; calibration record → `wandb.config` + stdout at start, on continual resume rebuild, and per stage swap; `window_log` + `late_death_log` in `_emit_episode_row`. Thermal / felt flags are read from the current `params` at every use. |
| | `configs/train/recurrent_ppo.yaml`, `configs/train/default.yaml` | `logging.episode.balance_metrics: true`, `logging.episode.balance_early_death_max_steps: 20`; comment-only note in `default.yaml`. |
| | `docs/environment/CONFIG_GUIDE.md` §7, `docs/environment/02_config_schema.md` | Key rows + why they are absent from `default.yaml` (config-system maintenance contract, same commit). |
| | tests | `tests/behavior/test_balance_metrics.py` (T3–T9, T11 + shipped-config and scan_fn-rule pins), `tests/models/test_balance_metrics_parity.py` (T1, T2), T10 appended to `tests/training/test_continual_bm_transition.py`; `balance_metrics` added to `_Cfg` / `fake_collect` / direct calls in `test_mc_fixed_mode.py`, `test_mc_raw_mode.py`, `test_gae_norm_mode.py`. |
| `7b1cf5cb` docs | `docs/develop/active/behavior/WANDB_METRICS_REFERENCE.md` | "Balance metrics (rPPO)" section: every key, pooled-sum rule + long-episode weighting, window-total `N`, empty-bin rule, felt 12-step under-read, warm vs near-fire (whole outer ring, report-only), late-death denominators, calibration record, training- vs eval-policy caveat. |

### New config keys (exact)

```yaml
# configs/train/recurrent_ppo.yaml
logging:
  episode:
    balance_metrics: true                 # bool, get_mandatory for RecurrentPPO; non-bool -> ValueError
    balance_early_death_max_steps: 20     # int >= 0, get_mandatory only when the switch is on
```

WandB: `Episode/Bal_*` — 5 time shares (`TimeNearFire` report-only), 5 eating, 5 × {True, Felt}
hiding, 5 warming, 6 × {True, Felt} × {Hungry, Fed} combination, 6 death keys (≤ 55 keys per row
in level 05; warm keys absent with thermal off, `_Felt` keys absent with felt injury off). WandB
config: `balance_calibration`, `balance_calibration_stage_<k>`.

### Tests

| Command (`JAX_PLATFORMS=cpu`, worktree) | Result |
|---|---|
| `pytest tests/behavior/test_balance_metrics.py tests/models/test_balance_metrics_parity.py` | 13 passed (T1–T9, T11 + pins) |
| T2 red check: inject `key, _ = jax.random.split(key)` into the ON branch | 165 of 198 arrays differ → test fails (restored after) |
| T3 red checks: swap `nutrition` / `injury` reads to `next_state` | fails on `eat_hungry` / `bush_inj_hi_true` respectively (restored after) |
| `pytest tests/models tests/behavior tests/training` | 231 passed, 3 failed — all 3 **pre-existing** (fail identically on unmodified `v4.0` in the shared tree): `test_modulation_input_slice.py::test_hand_computed_breakdown_matches_the_live_environment` (obs breakdown Olfaction 25 vs 5, Visual 13 vs 8), `test_continual_bm_transition.py::test_continual_bm_stage_transition_no_crash` and `test_continual_resume_rebuild.py::test_continual_resume_rebuilds_stage_env` (stale test YAML: `visual_properties` length 8 vs `visual_vector_size` 1) |
| `pytest tests/env` | 1291 passed, 1710 skipped, 17 failed — all in `test_channel_names_match_configs.py::test_every_maintained_config_can_write_a_recording[...level05_body_interactions/factors/*]`, **pre-existing** (`sensory.visual_value_mode` missing in those configs; reproduced on unmodified `v4.0`). No env code changed. |
| T10 (`test_continual_balance_metrics_stage_swap`) | passed: `[balance] balance_calibration` and exactly one `balance_calibration_stage_1` record (`thermal_on True`, `max_injury 100.0`, `early_death_max_steps 20`) |

Note: two modulation golden fixtures (`tests/fixtures/modulation/*_legacy.npz`) are gitignored
(`*legacy*`), so a fresh worktree lacks them; they were copied in from the shared tree to run the suite.

### Speed check

| Setting | Off | On | Δ |
|---|---|---|---|
| GPU 102:1 (RTX 4090), level 05, 128 envs × 128 steps, 4 epochs, 20 warm-up + 300 timed iterations each, interleaved 50-iteration blocks | 0.2792 s/it | 0.2860 s/it | **+2.4 %** (block spread 0.263–0.307 s/it both ways; another job shared the node) |
| CPU, 32 envs, 20 timed iterations each | 1.3800 s/it | 1.3856 s/it | +0.4 % |
| Host (NumPy) per iteration, 128 × 128: `step_counts` + 128 accumulates | — | 3.4 ms (GPU node) / 1.4 ms | ≈ +1.2 % of a 0.28 s iteration |
| `window_log` per emitted row, 5000-episode window | — | 26–65 ms | once per 4000 episodes |

Command: `tmp/20260927_speed_bench_gpu.py 128` / `tmp/20260927_speed_bench.py 32` in the worktree
(device part = jitted `train_iteration` + the host transfer of step info). Combined estimate ≈ +3–4 %,
below the 5 % discussion threshold but **flagged** because it is above the plan's "< 1 %" estimate;
the device part is within this node's run-to-run noise.

### Deviations (none silent)

1. **Early-death cut-off is a config key, not the constant `EARLY_DEATH_MAX_LEN`** (user decision D2):
   `logging.episode.balance_early_death_max_steps`, recorded in the calibration block as
   `early_death_max_steps`.
2. **Part C (post-hoc script, C1–C5, checkpoint 9) not implemented** (user decision D3). Consequently
   no `scripts/` file changed and no SCRIPTS_DEPENDENCY_MAP row was added.
3. **T10's thermal-on → thermal-off stage pair cannot be built**: `train.py` rejects continual
   schedules whose stages differ in `thermal_enabled` or `interoceptive_nociception_enabled`
   (obs-dim check + `_modality_fingerprint`). T10 instead runs two level-05 stages with the switch on
   and checks crash-freedom, the per-stage calibration record, and the emit path (WANDB_MODE=disabled
   keeps `wandb_enabled` true). The flag-follows-new-stage rule is still implemented (flags read
   from current `params` at every use) and the off-flag key suppression is covered by T6.
4. **Calibration record also carries `thermal_on`, `felt_on`, `early_death_max_steps`**, and is also
   written on the continual *resume* rebuild (same reason as the stage swap: params change).
5. **"Stand-alone configs that train rPPO"** (D1): the only rPPO training-layer config is
   `configs/train/recurrent_ppo.yaml`, merged by `train.py` for every rPPO run (single and continual);
   no other config carries a `logging:` block, so no other file needed the keys.
6. Plan Rev 1 said the "choice" measure's felt-injury note should be kept for the analyzer: it is in
   the metrics reference and the module docstring.

### Follow-ups / for other owners

- `bug-curator`: two pre-existing, apparently unrecorded failures — the obs-breakdown mismatch in
  `test_modulation_input_slice.py::test_hand_computed_breakdown_matches_the_live_environment`, and
  the stale stage YAMLs in `tests/training/test_continual_bm_transition.py` /
  `test_continual_resume_rebuild.py`; plus the 17 `level05_body_interactions/factors/*` configs that
  no longer resolve (`sensory.visual_value_mode` missing). The Known Bugs row "rPPO continual stage
  swap keeps stage-0 metric accumulators" stays OPEN (not fixed here); the new balance counters do
  not inherit it (wiped and re-flagged per stage).
- `experiment-designer` (after merge, per Part D): back-link from the study plan / page §07; state
  the C4 training-vs-eval-policy caveat and that `Bal_TimeNearFire` is report-only.
- CONFIG_CRITICAL_SETTINGS: no entry (logging switch, not a registry setting; no registry setting changed).

## Verification Report

> **Verified by**:
> **Date**:

| File | Change | Status | Notes |
|------|--------|:------:|-------|
| | | | |

**Conclusion**:

---

## Feedback from plan-reviewer

> **Reviewed**: 2026-09-27 · **Verdict**: **NOT READY** (one Critical, all else Moderate/Open) · Full report: [[plan_balance_metrics_training_logging]] (`docs/reviews/plan_balance_metrics_training_logging.md`)
>
> Severity legend — 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run · 🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

**What the plan gets right (verified against source, not from memory).** The "off" switch is genuinely
static: `PPOConfig` is `static_argnums=(6,)` (`train.py:1253`), `thermal_enabled` /
`interoceptive_nociception_enabled` are already used as Python `if`s inside jitted code
(`core.py:473`, `sensor.py:492`), and `train_iteration` builds `PPOBatch` field by field rather than
tree-mapping the whole `Transition` (`recurrent_ppo_trainer.py:523-545`), so the new arrays never enter
the update path. The pre-step-state / post-step-outcome pairing (A2) matches `agent_in_bush`'s
post-step position (`core.py:1276-1279`) and the planner (`planner.py:479-489`). The
continual path is safe: rPPO train defaults are merged (`train.py:507-514`) *before*
`_build_continual_schedule` clones `config` into every stage (`train.py:553`, `:195-200`), so the
mandatory key reaches stage configs. The 32-run safety argument holds as written.

| Sev | Location | Issue | Suggested fix | Owner |
|---|---|---|---|---|
| 🔴 | A9(a) "Merge back when the tests are green"; Checkpoint 1 | The merge into the shared tree has **no `results/` snapshot and no conflict strategy**. `train.py` is edited by parallel sessions daily, so a real (non-fast-forward) merge with conflicts is the likely case, and a failed merge followed by cleanup is exactly how `results/` was lost once. CLAUDE.md requires `cp -a results /tmp/results-bk-$(date +%s)` before any merge. | Add to Checkpoint 1/10: rebase the worktree branch onto the current `v4.0` tip **inside the worktree**, resolve conflicts there, then advance the shared tree by fast-forward only (`git merge --ff-only`); snapshot `results/` first; never `git clean -x`. State this as an explicit step. | senior-developer |
| 🟡 | T7 (Part B) | Test spec contradicts A4. T7 asserts "a −16 °C cell with a −14 °C body **counts as warm**", but under the plan's own definition (`cell_t > temperature_setpoint`, setpoint 0) a −16 °C cell is never warm. An implementer coding to spec would write an assertion the correct code fails, then "fix" the code. | Rewrite T7 as two cases: (−16 °C cell, −20 °C body) → **not** warm (cell-only, not cell-vs-body); (+8.8 °C cell, +10 °C body) → warm even though the cell is cooler than the body. | senior-developer |
| 🟡 | A4 "Matches the planner exactly" | Vacuously true for the diagonal: the planner's world has only −30 and +8.8 cells (`planner.py:8`, `TRAVEL_CELL=-30`) and STUDY_PLAN E5 says the cooler diagonal is "not modeled". So `warm = cell > 0` was never tested against a −16 °C cell. A trained agent parked on the diagonal (body settles ≈ ⅔ × −16 ≈ −10.7 °C, in the cold bin) is scored as *cold and not warming*, and its steps fall into `elsewhere`. Rev 2c makes the warming ratio report-only, but `Bal_TimeWarm` feeds criterion 1 (each activity ≥ 10 %), which is pass/fail. | Keep the definition (cell above setpoint is the physically right one) but (i) say in A4 and the metrics reference that the diagonal is a new case the planner never saw, and (ii) add one counter `near_fire` (cell above open-ground temperature, e.g. `cell_t > default_temp_high`) → `Episode/Bal_TimeNearFire`, so the diagonal is visible rather than folded into `elsewhere`. | senior-developer |
| 🟡 | T1/T2 (Part B) | Neither test names the env config. The tiny-GRU fixture from `test_mc_fixed_mode.py` is a thermal-off, interoception-off world; on it the "on" path traces `on_warm=None, felt=None` and T2 proves almost nothing about the extra ops. | State that T2 (and Checkpoint 4) run on a world with `thermal.enabled: true` **and** interoceptive nociception on (a level-05-derived test config); T1 may keep the small fixture. | senior-developer |
| 🟡 | A5 "Constants, not config" × `recurrent_ppo.yaml: balance_metrics: true` | Thresholds are absolute level-05 units (max nutrition 200, max injury 100) but the switch is on for **every** rPPO run in every world. A level-02 run logs `Bal_*` with silently mis-calibrated bins. | Have `window_log` also emit the calibration it assumed (`Bal_cal_max_nutrition`, `Bal_cal_max_injury`, read from `params`) once into `wandb.config`, or skip emission with a one-time printed warning when `params.max_nutrition`/`max_injury` differ from the calibration. Do not default; record. | senior-developer |
| 🟡 | Part D | Study docs back-link is handed off but not sequenced; the metrics reference gains ~50 keys. Fine. But `docs/environment/02_config_schema.md` + CONFIG_GUIDE rows are listed while the paired **`WANDB_METRICS_REFERENCE.md` "training-policy vs eval-policy"** caveat (C4) must also land in the study page §07, or the analyzer will pool online and post-hoc numbers. | Add "page §07 states the C4 caveat" to the experiment-designer hand-off line. | experiment-designer |
| 🟢 | A9(a), Checkpoint 1 | "worktree outside the repo directory" departs from the project's existing convention (`.claude/worktrees/`, gitignored at `.gitignore:51`). Either is fine; say which and note a `/tmp` worktree is container-local. | One clause. | senior-developer |
| ❓ | D2 / A7 | `Bal_LateDeathShare` denominator is unstated. Rev 2b N5 pre-registers the 5 % gate as *after* the 20-step exclusion, i.e. late deaths ÷ **all** episodes in the window (MaxSteps truncations included). Also unverified: level-05 `environment.max_steps` vs the planner's 500-step horizon — the 5 % gate was calibrated on the latter. | State the denominator in A7; check `max_steps` and say whether the gate transfers. | senior-developer |
| ❓ | A3 "A real effect, not a leak" | With `thermal_random_start_body_temp` and (if set) random start injury, the felt buffer is zero for the first ~12 steps of every episode, so `N_InjLo_Felt` is inflated at episode starts by construction. Accepting this is defensible (true injury decides, Rev 2c) but the analyzer must be told, or `HideRatio_Felt` will read low for a reason that has nothing to do with the policy. | One sentence in the metrics reference; optionally exclude steps `< interoceptive_kernel_length` from the `_felt` counters only. | senior-developer |
| ❓ | A6 pooling | Pooled step counts weight long-lived episodes; the planner pooled fixed-horizon rollouts. Same convention, but the mixture differs (training episodes die at different times). Not wrong — an assumption to name. | Note it next to the ratio-of-sums rule. | senior-developer |

**Passes skipped.** Pass 6 (experiment-plan specifics) does not apply: this is an engineering plan with no
arms, seeds or budget. Pass 7 does not apply (no analysis verdict).

**Prior art.** Registry rows read directly (`KNOWN_BUGS.md:101, 125, 298, 488` and the class note at
`:287`); the plan cites and handles all of them. No new registry row needed; nothing for `bug-curator`.
Collision check with the in-flight `SAVED_RUN_CONFIG_COMPAT` plan: none — that plan touches *frozen run
copies* read by eval scripts, and no eval script reads `logging.*`.

**Cost of being wrong.** The Critical costs unrecoverable training output if a conflicted merge is
"cleaned up" the way it was once before (one line prevents it). The T7/A4 pair costs a wrong
`Bal_TimeWarm` in every rPPO run from merge day on, which feeds a pass/fail criterion of the study —
a definitional error that no rerun fixes, only a re-definition and a re-read of every dashboard.

**Exit condition for NOT READY → SOUND WITH CONCERNS.** Add the snapshot + rebase-in-worktree +
`--ff-only` merge step (Critical), and fix T7 to agree with A4.

*Reviewed by: plan-reviewer*

---

## Feedback from plan-reviewer (Revision 1 re-review)

> **Reviewed**: 2026-09-27, plan at commit `94096470` · **Verdict**: **SOUND WITH CONCERNS** — every finding of the first review is resolved as written; no new Critical finding. Remaining items are one Moderate (the `results/` snapshot step may not be feasible as literally written on this container) and two Low.
>
> Severity legend — 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run · 🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

**Resolution check (each item verified against source, not against the doc's own claims).**

| First-review finding | Resolved? | Where / evidence |
|---|---|---|
| 🔴 Merge-back with no snapshot, no conflict rule | **Yes.** Rebase inside the worktree, abort-and-hand-back on any conflict, tests re-run, `results/` snapshot, `git merge --ff-only` in the shared tree, refusal → stop, never stash/checkout -f/reset/clean. | A9 "Merge-back procedure" steps 1–6; Checkpoints 1 and 11. `.claude/worktrees/` is gitignored (`.gitignore:51`, confirmed). |
| 🟡 T7 contradicts A4 | **Yes.** T7(a) −16 °C cell / −20 °C body → not warm **and** `near_fire`; (b) +8.8 °C cell / +10 °C body → warm, not `near_fire`; (c) −30 °C → neither. All three agree with `cell > setpoint` (0) and `−29 < cell ≤ 0`. | Part B T7; A4. Level 05 inherits `default_temp: [-31, -29]` (`configs/environment/default.yaml:512`), so `thermal_default_temp_high` = −29 as the plan states (`state.py:392`). |
| 🟡 Warm rule untested on the diagonal | **Yes.** Gap stated; `near_fire` counter (#37) and `Episode/Bal_TimeNearFire` added, **report-only**, not added to `Bal_TimeWarm`; analyzer routing stated. | A4, counter table, criterion mapping row 1. Random thermal spots are off by default (`default.yaml:517`, `core.py:1673`), and only the campfire carries a `temperature_ratio` in level 05 (`05-campfire_thermal_10x10.yaml:97`), so "any cell above −29 °C was heated by a fire" holds in that world. |
| 🟡 T1/T2 world unnamed | **Yes.** Level-05-derived, thermal + interoceptive nociception on, asserted inside the tests; T2 additionally asserts the three extra fields are arrays. | Part B T1, T2; Checkpoint 4. |
| 🟡 Thresholds applied silently in every world | **Yes.** `calibration_record(params, thermal_on=…)` reads `max_nutrition` / `max_injury` (`state.py:240-241`), setpoint and `thermal_default_temp_high` by attribute (AttributeError, no default); written via `wandb.config.update` at start and as `balance_calibration_stage_<k>` on swap; T11 covers it. The stage-swap block rebinds `params = load_env_params(schedule.stage_configs[new_stage])` (`train.py:1621`) **before** the accumulator wipe, so the per-stage read is well-ordered. | A5; `train.py` changes; T10, T11. |
| 🟡 C4 caveat to the study page | **Yes.** In the experiment-designer hand-off, sequenced after the merge. | Part D last row. |
| ❓ Late-death denominator; episode cap | **Yes.** All window episodes, truncations included; cause shares among late deaths. `max_steps: 500` inherited (`default.yaml:7`; no override in levels 03–05, confirmed). Study Rev 2c exists as cited (`STUDY_PLAN.md:483-490`) and the criterion mapping follows it. | A7; keys table. |
| ❓ Felt buffer zero start | **Yes.** Buffer zeroed at reset (`core.py:2038`), 12-step under-read stated for the analyzer, kept deliberately. | A3 "What the analyzer must be told"; Part D. |
| ❓ Pooling weights long episodes | **Yes.** Named next to the ratio-of-sums rule. | A6. |

**New findings.**

| Sev | Location | Issue | Suggested fix | Owner |
|---|---|---|---|---|
| 🟡 | Merge-back step 4 (`cp -a results /tmp/results-bk-$(date +%s)`) | On this container `/tmp` is a **63 GB tmpfs (RAM-backed), 55 GB free**, and `du -sh results` did not finish in 280 s (25 top-level dirs incl. every trajectory store and every algorithm's run tree). The copy is therefore likely to be either very slow or to stop with `ENOSPC` part-way — and a half-written snapshot is worse than none, because step 5 proceeds on the belief that a rollback exists. The merge itself is `--ff-only` and never touches gitignored data, so this is not a data-loss path; it is the safety net that may not be there. | Before step 4: measure (`du -sh results/*`, generous timeout). If it does not fit `/tmp`, snapshot to a NAS-side path **outside the repo** (e.g. a sibling of the project dir) and record that path; either way record the `cp` exit status in the Implementation Report and do not start step 5 on a non-zero exit. | senior-developer → developer |
| 🟢 | A4 `near_fire`; Checkpoint 6 | The field is blurred once with a Gaussian (`core.py:1707`), so `near_fire` (`cell > −29`) picks up every cell inside the blur kernel around the fire, not only the four diagonals. Checkpoint 6's printed class counts will show a wider ring than "the diagonal". Not a defect — the counter is report-only — but the analyzer wording "warms on the cooler diagonal" should read "on the fire's outer ring". | One word in A4 and the metrics reference. | senior-developer |
| 🟢 | A9 step 1 | `git -C <worktree> rebase v4.0` rebases onto the **local** `v4.0`; the plan says "no fetch needed" which is true only while no parallel session pushes to `origin/v4.0` and pulls back. Harmless today (nobody pushes), stated for completeness. | None required. | — |

**Assumptions the plan still rests on (all now verified-in-plan or stated):** the four `params` attribute names exist (verified); `thermal_enabled` / `interoceptive_nociception_enabled` are static (`state.py:344, 376`, `pytree_node=False`, verified); level-05 thermal baseline range is `[-31, -29]` (verified); `rest` in a bush at I = 61 reduces injury below 60 in one step (T3 premise — unverified here, but T3 fails loudly if it does not, which is the right shape).

**Passes skipped.** Pass 6 (experiment-plan specifics) and pass 7 (analysis verdict) are structurally inapplicable, as before. Prior-art: no new registry rows touch worktree/ff-only/`wandb.config`; nothing for `bug-curator`.

**Cost of being wrong.** If the snapshot step fails silently, the cost is zero on a clean fast-forward (the likely case) and a missing rollback on the one path the procedure already tells the developer to stop on; the procedure's stop rules, not the snapshot, are what actually protect `results/`. Nothing in Revision 1 can produce a wrong study conclusion that the first review did not already close.

*Reviewed by: plan-reviewer*

## User decisions (2026-09-27, recorded by the parent session)

- **D1 — switch:** a required config switch (read with `config.get_mandatory`, no default); stated in every
  maintained config and the stand-alone configs that train rPPO.
- **D2 — late deaths:** yes, add death-cause counts that exclude early deaths, **with the early-step cut-off
  configurable** (a required key alongside the switch; level-05 value 20, matching the study plan). Read
  only when the switch is on.
- **D3 — offline "choice" script: dropped from this plan.** User: "this should be analyzed, not a metric to
  confirm." The two-states-versus-one measure belongs to a later analysis, not to training logging; remove
  Part D's script from the scope (keep the note on felt injury for the analyzer).
- **Merge-back backup:** measure the size of `results/` first; back it up to a location outside the repo if
  it fits; if not, skip the copy and record why in the implementation report (the fast-forward-only merge
  moves tracked files only). Never start the merge after a failed copy.
- Plan-reviewer confirming pass: SOUND WITH CONCERNS (`cc6b7a23`); its two Low notes apply (`near_fire`
  covers the whole heated ring; no fetch needed only while nobody pushes the branch).
- **Status: approved for implementation.**
