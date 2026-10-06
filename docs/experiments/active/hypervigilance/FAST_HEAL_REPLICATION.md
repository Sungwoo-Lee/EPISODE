---
title: Fast-bush-healing replication — level 04, + temperature, + temperature and thirst
created: 2026-10-05
last_updated: 2026-10-07
status: active
---

# Fast-bush-healing replication

## Question

Two level-04 agents trained on 22 September 2026 (an ordinary agent and a neuromodulated one, seed 42,
both with injury healing 25 times faster on a bush) looked, in the fixed experiment tests, like the
combination this project is after: the modulated agent hides when a predator or a chasing rabbit
comes (and not for a harmless wandering rabbit), hides more when injured, and is steadier from
checkpoint to checkpoint than the ordinary agent. That is one seed per agent, so it cannot say whether
the modulator causes it. This experiment retrains the same pair with three seeds (42, 43, 44) in the
same world, and in the same world with body temperature (level 05) and with temperature plus a pond
and thirst (level 06), to see whether the pattern repeats and whether it survives added body states.
Exploratory; results are read with the existing experiment-test sweeps
([[f7b_across_runs]] page, "Injury and Rabbit Avoidance Across Runs").

Seed 42 at level 04 is a reproduction check of the 22-Sep pair (same settings, same seed).

## Settings

- Worlds: `configs/environment/experiment/basic/04-jump_attack_10x10.yaml` (behaviourally identical to the
  22-Sep runs' saved config: every differing key is a later option defaulting to off — checked
  2026-10-05), `05-campfire_thermal_10x10.yaml` (+ cold and campfires), `06-pond_thirst_10x10.yaml`
  (+ pond and thirst). All carry recovery_base_rate 0.2, recovery_accel_rate 0, recovery_in_bush_multiplier 25.
- Agents: `configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml` (ordinary) and
  `nmngaenorm_t16quad_ALL.yaml` (FiLM modulator at encoder, GRU, actor and critic) — unchanged since 2026-09-07.
- 10,000,000 episodes each, `--log-interval 10`; WandB group `fast_heal_replication`.

## Launch manifest

| tag | world | agent | seed | node:GPU |
|---|---|---|---|---|
| rppo_healrep_l04_t1none_s42 | level 04 | ordinary | 42 | 106:0 |
| rppo_healrep_l04_t16quad_s42 | level 04 | modulated | 42 | 106:1 |
| rppo_healrep_l04_t1none_s43 | level 04 | ordinary | 43 | 107:0 |
| rppo_healrep_l04_t16quad_s43 | level 04 | modulated | 43 | 107:1 |
| rppo_healrep_l04_t1none_s44 | level 04 | ordinary | 44 | 108:0 |
| rppo_healrep_l04_t16quad_s44 | level 04 | modulated | 44 | 108:1 |
| rppo_healrep_l05_t1none_s42 | level 05 | ordinary | 42 | 109:0 |
| rppo_healrep_l05_t16quad_s42 | level 05 | modulated | 42 | 109:1 |
| rppo_healrep_l05_t1none_s43 | level 05 | ordinary | 43 | 110:0 |
| rppo_healrep_l05_t16quad_s43 | level 05 | modulated | 43 | 110:1 |
| rppo_healrep_l05_t1none_s44 | level 05 | ordinary | 44 | 111:0 |
| rppo_healrep_l05_t16quad_s44 | level 05 | modulated | 44 | 111:1 |
| rppo_healrep_l06_t1none_s42 | level 06 | ordinary | 42 | 113:0 |
| rppo_healrep_l06_t16quad_s42 | level 06 | modulated | 42 | 113:1 |
| rppo_healrep_l06_t1none_s43 | level 06 | ordinary | 43 | 101:0 |
| rppo_healrep_l06_t16quad_s43 | level 06 | modulated | 43 | 101:1 |
| rppo_healrep_l06_t1none_s44 | level 06 | ordinary | 44 | 103:0 |
| rppo_healrep_l06_t16quad_s44 | level 06 | modulated | 44 | 103:1 |

Pre-flight 2026-10-05: all nine nodes idle (no train/eval processes, no diary claims, NAS mounted).
Node 114 excluded (hung under parallel compiles before); 112 avoided (another session's CPU job).
Seeds chosen by the user (42, 43, 44); nodes by the user.

## Reading plan (after training)

Experiment-test sweeps with the existing scene sets — level 04: core scenes
(`behavior_probes/core/avoidance`); levels 05 and 06: scenes built on each training world with a campfire
beside the bush (as for the smell and thirst studies) — then the Figure 7b view and the
animal-vs-state map on the cross-run page. Compared per seed, never pooled across levels.

## Launch record (training-runner, 2026-10-05)

All 18 runs launched 16:01–16:03 and confirmed running: one training process per tag, a results folder
under `results/JAX_RecurrentPPO/`, and the intended seed printed at startup. `--seed` was passed on every
run; 42 is also the config default, so the seed-42 runs use the same seed as the 22-Sep pair.

| tag | node:GPU | status | WandB run ID | results folder | log |
|---|---|---|---|---|---|
| rppo_healrep_l04_t1none_s42 | 106:0 | running | 3njio44x | results/JAX_RecurrentPPO/20261005-160115_rppo_healrep_l04_t1none_s42 | logs/20261005_160111_rppo_healrep_l04_t1none_s42.log |
| rppo_healrep_l04_t1none_s43 | 107:0 | running | a5dkdupt | results/JAX_RecurrentPPO/20261005-160117_rppo_healrep_l04_t1none_s43 | logs/20261005_160113_rppo_healrep_l04_t1none_s43.log |
| rppo_healrep_l04_t1none_s44 | 108:0 | running | k4nhps08 | results/JAX_RecurrentPPO/20261005-160119_rppo_healrep_l04_t1none_s44 | logs/20261005_160115_rppo_healrep_l04_t1none_s44.log |
| rppo_healrep_l04_t16quad_s42 | 106:1 | running | sqe4wi0f | results/JAX_RecurrentPPO/20261005-160228_rppo_healrep_l04_t16quad_s42 | logs/20261005_160225_rppo_healrep_l04_t16quad_s42.log |
| rppo_healrep_l04_t16quad_s43 | 107:1 | running | 262dbw7q | results/JAX_RecurrentPPO/20261005-160231_rppo_healrep_l04_t16quad_s43 | logs/20261005_160229_rppo_healrep_l04_t16quad_s43.log |
| rppo_healrep_l04_t16quad_s44 | 108:1 | running | zlj7bbv4 | results/JAX_RecurrentPPO/20261005-160235_rppo_healrep_l04_t16quad_s44 | logs/20261005_160232_rppo_healrep_l04_t16quad_s44.log |
| rppo_healrep_l05_t1none_s42 | 109:0 | running | mqiavtah | results/JAX_RecurrentPPO/20261005-160124_rppo_healrep_l05_t1none_s42 | logs/20261005_160117_rppo_healrep_l05_t1none_s42.log |
| rppo_healrep_l05_t1none_s43 | 110:0 | running | vxfnz0v9 | results/JAX_RecurrentPPO/20261005-160125_rppo_healrep_l05_t1none_s43 | logs/20261005_160119_rppo_healrep_l05_t1none_s43.log |
| rppo_healrep_l05_t1none_s44 | 111:0 | running | jr3fk9qo | results/JAX_RecurrentPPO/20261005-160126_rppo_healrep_l05_t1none_s44 | logs/20261005_160121_rppo_healrep_l05_t1none_s44.log |
| rppo_healrep_l05_t16quad_s42 | 109:1 | running | weijdqyo | results/JAX_RecurrentPPO/20261005-160241_rppo_healrep_l05_t16quad_s42 | logs/20261005_160235_rppo_healrep_l05_t16quad_s42.log |
| rppo_healrep_l05_t16quad_s43 | 110:1 | running | qfk2dedw | results/JAX_RecurrentPPO/20261005-160244_rppo_healrep_l05_t16quad_s43 | logs/20261005_160239_rppo_healrep_l05_t16quad_s43.log |
| rppo_healrep_l05_t16quad_s44 | 111:1 | running | fae5ggj7 | results/JAX_RecurrentPPO/20261005-160248_rppo_healrep_l05_t16quad_s44 | logs/20261005_160242_rppo_healrep_l05_t16quad_s44.log |
| rppo_healrep_l06_t1none_s42 | 113:0 | stopped: node 113 rebooted at 16:05, about 3 min after launch; not relaunched (awaiting user) | r8cfsgny | results/JAX_RecurrentPPO/20261005-160128_rppo_healrep_l06_t1none_s42 | logs/20261005_160123_rppo_healrep_l06_t1none_s42.log |
| rppo_healrep_l06_t1none_s43 | 101:0 | running | 2bgare7h | results/JAX_RecurrentPPO/20261005-160131_rppo_healrep_l06_t1none_s43 | logs/20261005_160125_rppo_healrep_l06_t1none_s43.log |
| rppo_healrep_l06_t1none_s44 | 103:0 | running | sw4nnljk | results/JAX_RecurrentPPO/20261005-160134_rppo_healrep_l06_t1none_s44 | logs/20261005_160127_rppo_healrep_l06_t1none_s44.log |
| rppo_healrep_l06_t16quad_s42 | 113:1 | stopped: node 113 rebooted at 16:05, about 3 min after launch; not relaunched (awaiting user) | c1f98br1 | results/JAX_RecurrentPPO/20261005-160249_rppo_healrep_l06_t16quad_s42 | logs/20261005_160246_rppo_healrep_l06_t16quad_s42.log |
| rppo_healrep_l06_t16quad_s43 | 101:1 | running | hsc6npjv | results/JAX_RecurrentPPO/20261005-160255_rppo_healrep_l06_t16quad_s43 | logs/20261005_160249_rppo_healrep_l06_t16quad_s43.log |
| rppo_healrep_l06_t16quad_s44 | 103:1 | running | fce74f2p | results/JAX_RecurrentPPO/20261005-160258_rppo_healrep_l06_t16quad_s44 | logs/20261005_160252_rppo_healrep_l06_t16quad_s44.log |

### Relaunch, 2026-10-05 17:02

The two level-06 seed-42 runs died when node 113 rebooted (~16:05, cause unknown; logs show no error).
Relaunched on node 102 (both RTX 4090 GPUs idle, pre-checked), same command and seed, user-approved:

| tag | node:GPU | run folder (`results/JAX_RecurrentPPO/`) |
|---|---|---|
| rppo_healrep_l06_t1none_s42 | 102:0 | 20261005-170252_rppo_healrep_l06_t1none_s42 |
| rppo_healrep_l06_t16quad_s42 | 102:1 | 20261005-170314_rppo_healrep_l06_t16quad_s42 |

The dead runs' folders (20261005-160128_…t1none_s42, 20261005-160249_…t16quad_s42) are not used.

## Added arm: level 05 with fixed start temperature (2026-10-06)

**Why.** Every level-05 run trained after 26 Sep starts each episode at a random body temperature in
[-10, +5]; the 22-Sep level-05 runs started at the comfortable setpoint (0.0). Those 22-Sep runs are
the only level-05 runs where the modulated and ordinary agents clearly differ (cross-run page, Figure
B1); the smell-study control (22-Sep level 05 + random start temperature, seeds 42-44) shows no
difference. So this arm repeats level 05 with the start temperature fixed, against the replication's
own level-05 arm (random start) at the same seeds: a difference that appears here and not there points
at the random start temperature; one that appears in neither points at the 22-Sep result being one seed.

**Config.** `configs/environment/experiment/hypervigilance/fixed_start_temp_l05.yaml` = `basic/05` with
`thermal.random_start_body_temp: false` only (CONFIG_CRITICAL_SETTINGS change log, 2026-10-06; resolved
config checked against the 22-Sep level-05 saved config: world keys identical). Agents, episodes,
log interval, WandB group as above. User chose nodes 104, 105, 112 (2026-10-06 07:3x).

| tag | node:GPU |
|---|---|
| rppo_healrep_l05fix_t1none_s42 | 104:0 |
| rppo_healrep_l05fix_t16quad_s42 | 104:1 |
| rppo_healrep_l05fix_t1none_s43 | 105:0 |
| rppo_healrep_l05fix_t16quad_s43 | 105:1 |
| rppo_healrep_l05fix_t1none_s44 | 112:0 |
| rppo_healrep_l05fix_t16quad_s44 | 112:1 |

**Reading.** Test in the same scenes as the level-05 arm (`behavior_probes/hvsmell` two-channel /
thermal neutral clean) so the two arms differ only in training.


**Launch record (2026-10-06 07:41, training-runner).** All six running (one process per tag, both GPUs
busy on each node). Each run's saved config (`models/config.yaml`) has `random_start_body_temp: false` and
`recovery_in_bush_multiplier: 25.0`, so the `extends:` chain resolved as intended.

| tag | node:GPU | status | WandB run ID | results folder | log |
|---|---|---|---|---|---|
| rppo_healrep_l05fix_t1none_s42 | 104:0 | running | t9eqkmfi | results/JAX_RecurrentPPO/20261006-074127_rppo_healrep_l05fix_t1none_s42 | logs/20261006_074122.log (shared, see note) |
| rppo_healrep_l05fix_t16quad_s42 | 104:1 | running | m0v23m4g | results/JAX_RecurrentPPO/20261006-074133_rppo_healrep_l05fix_t16quad_s42 | logs/20261006_0742_rppo_healrep_l05fix_t16quad_s42.launch.log |
| rppo_healrep_l05fix_t1none_s43 | 105:0 | running | feklh807 | results/JAX_RecurrentPPO/20261006-074127_rppo_healrep_l05fix_t1none_s43 | logs/20261006_074122.log (shared, see note) |
| rppo_healrep_l05fix_t16quad_s43 | 105:1 | running | z9qx3zlp | results/JAX_RecurrentPPO/20261006-074134_rppo_healrep_l05fix_t16quad_s43 | logs/20261006_0742_rppo_healrep_l05fix_t16quad_s43.launch.log |
| rppo_healrep_l05fix_t1none_s44 | 112:0 | running | ht2sa8k5 | results/JAX_RecurrentPPO/20261006-074127_rppo_healrep_l05fix_t1none_s44 | logs/20261006_074122.log (shared, see note) |
| rppo_healrep_l05fix_t16quad_s44 | 112:1 | running | 90f9y0uo | results/JAX_RecurrentPPO/20261006-074134_rppo_healrep_l05fix_t16quad_s44 | logs/20261006_0742_rppo_healrep_l05fix_t16quad_s44.launch.log |

Note: the three GPU-0 runs were launched within the same second without `--log`, so they share the
launcher's default timestamped log file; its contents are interleaved/partly overwritten. Training is
unaffected; use WandB for those runs.

## Follow-up: modulator capacity grid (designed 2026-10-06)

The replication found that the modulator does not reliably enlarge injury-driven hiding. The follow-up
tests whether a larger modulator, or one whose gains are shared across groups of neurons, changes that.
It trains a 3 × 3 grid of modulator settings at level 05, in stages: one seed first, then more seeds only
for settings that stand out. This replication's level-05 runs (both agents, seeds 42–44) are its
references and are not retrained. Design, decision rule and run table: [[NMN_CAPACITY_GRID_L05]].

## Follow-up: modulator input at level 05 (designed 2026-10-07)

The second follow-up keeps the level-05 modulated agent and changes only what the modulator reads: felt
injury alone, fullness and felt injury, those two plus body temperature, or the outside world only. The
main network still reads everything. One seed first; more seeds by the user's judgement. This
replication's level-05 runs (both agents, seeds 42–44) are its references and are not retrained. Design,
readout and run table: [[NMN_INPUT_L05]].
