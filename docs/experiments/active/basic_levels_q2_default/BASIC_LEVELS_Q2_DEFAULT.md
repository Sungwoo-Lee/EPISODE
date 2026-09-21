---
title: "Basic levels under the new default senses: does a neuromodulator help?"
topic: basic_levels_q2_default
status: active
created: 2026-09-21
last_updated: 2026-09-21
---

# Basic levels under the new default senses: does a neuromodulator help?

## Question

The agent's default senses were just rebuilt. Until now the default agent was **blind**
(`visual_sensor_range: 0`) and had a single omnidirectional whiff of smell
(`olfactory_grid_range: 0`). It now has a small visual field two cells across and a
five-cell directional smell field — and, critically, its vision no longer tells it **what**
it is looking at, because every entity's appearance collapsed to the same single number
(`visual_vector_size: 1` with `visual_value_mode: clamp`). Identity did not leave the world;
it moved to the nose, where a predator smells `[0, 0.7, 0.5, 0, 0]` and a harmless animal
smells `[0, 0.5, 0.7, 0, 0]` and only the *ratio* tells them apart.

A precision worth stating, because the obvious shorthand for this is wrong: what vision
delivers is **not** a binary "occupied / empty" flag. The sensor sums each entity's blurred
contribution before capping the total at 1.0, so a lone entity reads about 0.64 on its own
cell, two entities in one cell read more than one until the sum saturates, and an entity
outside `visual_sensor_range` still leaks attenuated mass inward — `visual_sensor_range`
bounds the cells *sampled*, not the entities *sensed*. The honest description is a
presence-capped blurred density that is identity-free. The identity claim — the one this
wave depends on — holds exactly.

That combination is the sensor-ladder study's `Q2_presence_binary` arm, adopted as the
project default in commit `47b1b8c3`. The reason for adopting it is that it is the only
configuration with a real visual field in which the agent still has to **fuse two
modalities doing different jobs** — vision answers *where*, olfaction answers *what* —
and the ladder showed it demonstrably fails to fuse them, which is a specific, nameable
failure rather than general incompetence.

This wave asks the first question that follows: **on each of the seven standard worlds,
does adding a neuromodulator to this agent change anything?** A neuromodulator here is a
small second network that reads the agent's senses and outputs a per-unit gain and offset
applied to the main network's activations (a FiLM modulation) — the project's analog of an
ascending modulatory system like acetylcholine or noradrenaline.

Two earlier neuromodulator grids answered a version of this question and answered it
*no* — the modulator moved nothing, on any behavioural measure, in twelve of twelve
grid-by-measure combinations. But **both of those grids trained a blind agent**
(`visual_sensor_range: 0`). The modulator was asked to gate a perceptual stream that
barely existed. This wave is the first test of the same mechanism on an agent that has
something to gate.

## Arms

Two agent configurations, seven worlds, one seed (42), 10,000,000 episodes each = 14 runs.

| arm | config | what it is |
|---|---|---|
| control | `configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml` | the unmodulated agent |
| modulated | `configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml` | the same agent with the modulator writing to **all four sites** (encoder, recurrent core, actor head, critic head) and reading **all** sensors |

The two files are identical in every key except `modulation.type`, which is `null` in the
control. Same hierarchical encoder, same `lr_critic` 0.0005, same `return_mode: GAE_NORM`.
A difference between the arms is therefore attributable to modulation and to nothing else —
which is why the grid's own `t1none` was chosen over the project's plain recurrent-PPO
baseline, whose encoder and critic learning rate both differ.

`t16quad_ALL` is the maximal cell of the site-by-input grid: every site, every input. It is
the arm most likely to show an effect if one exists, and therefore the right first probe.

## Worlds

Seven levels, `configs/environment/experiment/basic/`. Observation width is the load-bearing
pre-flight discriminator — a run whose banner prints the wrong number loaded the wrong world:

| level | observation width | note |
|---|---|---|
| `00-static_predator_5x5` | **44** | pins `visual_sensor_range: 1` |
| `01-slow_predator_5x5` | **44** | pins `visual_sensor_range: 1` |
| `02-predator_and_rabbit_10x10` | **52** | |
| `03-random_init_10x10` | **52** | |
| `04-jump_attack_10x10` | **52** | the two earlier neuromodulator grids' world, at width 27 |
| `05-campfire_thermal_10x10` | **58** | adds Body Temperature 1 + Thermoception 5 |
| `06-sensory_noise_10x10` | **58** | |

A run printing **27** loaded an archived eight-channel config and is void.

## Pre-flight already performed

The neuromodulated agent was **constructed** against all seven levels through `train.py`'s
own configuration merge order, and the modulator's resolved input width asserted equal to
the observation width in each case (44/44, 52/52, 58/58), with all four site flags live on
both the model and the modulator module. This check exists because the grid generator
hardcodes `27` in its own assertions, and because this project has previously shipped a
silently-unmodulated agent. `input_sensors: "all"` is confirmed width-agnostic.

## Launch manifest

| # | level | arm | node:GPU | tag |
|---|---|---|---|---|
| 1 | 00 | control | 101:0 | `rppo_basicq2_lvl00_t1none_s42` |
| 2 | 00 | modulated | 101:1 | `rppo_basicq2_lvl00_t16quad_s42` |
| 3 | 01 | control | 103:0 | `rppo_basicq2_lvl01_t1none_s42` |
| 4 | 01 | modulated | 103:1 | `rppo_basicq2_lvl01_t16quad_s42` |
| 5 | 02 | control | 104:0 | `rppo_basicq2_lvl02_t1none_s42` |
| 6 | 02 | modulated | 104:1 | `rppo_basicq2_lvl02_t16quad_s42` |
| 7 | 03 | control | 105:0 | `rppo_basicq2_lvl03_t1none_s42` |
| 8 | 03 | modulated | 105:1 | `rppo_basicq2_lvl03_t16quad_s42` |
| 9 | 04 | control | 106:0 | `rppo_basicq2_lvl04_t1none_s42` |
| 10 | 04 | modulated | 106:1 | `rppo_basicq2_lvl04_t16quad_s42` |
| 11 | 05 | control | 107:0 | `rppo_basicq2_lvl05_t1none_s42` |
| 12 | 05 | modulated | 107:1 | `rppo_basicq2_lvl05_t16quad_s42` |
| 13 | 06 | control | 108:0 | `rppo_basicq2_lvl06_t1none_s42` |
| 14 | 06 | modulated | 108:1 | `rppo_basicq2_lvl06_t16quad_s42` |

Each level's two arms share a node and a card, so the comparison that matters is never
across hardware. Nodes 102 and 109–114 are deliberately untouched.

`--seed`, `--num-envs` and `--checkpoint-frequency` are config-owned and not passed.
`--episodes 10000000` is passed explicitly, per the launch convention.

## How it will be read

Performance is **survival steps**, never cumulative reward (project rule). The comparison
is per level: modulated minus control. One seed per cell means a single-run-versus-single-run
comparison, so a small difference is not yet evidence — this wave is a screen for *whether
any level shows a gap worth seeding properly*, not a measurement of the gap.

## Links

- Default-config change and its evidence: `docs/environment/CONFIG_CRITICAL_SETTINGS.md`, entry dated 2026-09-21
- The sensor-ladder study that produced `Q2_presence_binary`: `docs/experiments/active/sensor_ladder/sensor_ladder.md`
- The two blind-agent neuromodulator grids: `docs/experiments/active/nmn_input_site_grid/NMN_INPUT_SITE_GRID.md` and `..._GAENORM.md`
