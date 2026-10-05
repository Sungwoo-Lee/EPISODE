---
title: Fast-bush-healing replication — level 04, + temperature, + temperature and thirst
created: 2026-10-05
last_updated: 2026-10-05
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
