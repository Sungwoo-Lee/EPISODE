---
title: "Basic levels under the new default senses: does a neuromodulator help?"
topic: basic_levels_q2_default
status: active
created: 2026-09-21
last_updated: 2026-09-22
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
| *(note, 2026-09-30)* `06-pond_thirst_10x10` | **59** | NEW level 06 ([[thirst_water_plan]]): the campfire world plus a pond and thirst; adds Hydration 1. Not part of this study |
| *(note, 2026-09-30)* `07-sensory_noise_10x10` | **59** | the noise level above, RENAMED 06 → 07 and re-parented onto the pond world. This study's `06-sensory_noise` runs (width 58) used the pre-rename world |

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

## One caveat that does not block this wave but blocks a claim

`env-config-reviewer` checked, at pre-flight, whether level 06's perceptual-noise profile
still lines up with the new observation layout. Mechanically it does: the noise system
slices **by modality name**, not by index range, so olfaction's jump from 5 to 25
dimensions and vision's from 8 to 13 are covered automatically and nothing is left
un-noised or noised at the wrong width.

What has *not* been re-derived is the calibration's premise. Level 06's injury-gated
noise was tuned when smell was a 5-dimension on-cell reading and vision was an 8-dimension
on-contact identity channel. It now acts on a 25-dimension *gradient*, where the useful
signal is the difference **between** neighbouring cells rather than the value in one, and
on a 13-cell blurred field whose neighbour tails (~0.086) sit below one noise sigma (0.1)
even at zero injury. The level still runs correctly; what is unverified is whether it still
*means* what it was built to mean.

Consequence: this wave may be read for survival steps on level 06. It may **not** be read
for a hypervigilance claim on level 06 without first re-deriving that calibration — a job
for `experiment-designer`.

## How it will be read

Performance is **survival steps**, never cumulative reward (project rule). The comparison
is per level: modulated minus control. One seed per cell means a single-run-versus-single-run
comparison, so a small difference is not yet evidence — this wave is a screen for *whether
any level shows a gap worth seeding properly*, not a measurement of the gap.

## Links

- Default-config change and its evidence: `docs/environment/CONFIG_CRITICAL_SETTINGS.md`, entry dated 2026-09-21
- The sensor-ladder study that produced `Q2_presence_binary`: `docs/experiments/active/sensor_ladder/sensor_ladder.md`
- The two blind-agent neuromodulator grids: `docs/experiments/active/nmn_input_site_grid/NMN_INPUT_SITE_GRID.md` and `..._GAENORM.md`

## Launched

2026-09-21 11:48 KST, all 14 runs up, group `basic_levels_q2_default`, job-type `pilot`.
Per-run node, PID, WandB id and log path are in the wave block of `train_command-agent.sh`
(commit `662ba1e5`), and one `training-start` row per run is in `docs/diary/2026-09-21.md`.

The discriminator passed 14 of 14 — every banner printed the width its level should
resolve to (44 / 52 / 58), none printed 27, and no level's `extends:` chain reaches
`experiment/archive/`. The modulator was confirmed live on the modulated arms at both
width extremes (obs 44 and obs 58), logging `input_sensors=[all]` with all four sites, so
it is resolving against each run's own width rather than a hardcoded one.

Two recorded deviations, neither a defect: `--log-interval 10` overrides the config's 500,
giving WandB 50x the usual row density; and every banner reads `Device: gpu (cuda:0)`
because `train.py` sets `CUDA_VISIBLE_DEVICES` to the requested index, so the card is
always local 0 inside the process — physical placement was verified against `nvidia-smi`
instead (one compute app per GPU, two per node).

---

## Wave 1 was stopped and is superseded (2026-09-22)

**What happened.** Wave 1 launched on 2026-09-21 into a world where **cover had no healing role**.
`body.recovery_in_bush_multiplier` shipped at `1.0` — meaning resting inside a bush healed exactly
as fast as resting in the open — and `recovery_base_rate: 0.1` with `recovery_accel_rate: 0.5` let
an agent clear the **entire 100-point injury scale on open ground in about 12 rest steps**.

That matters because bush hiding is this project's main behavioural readout for internal-state
dependence. An injured agent had no reason to travel to cover, and measurement agreed: it rested on
**86%** of its injured steps while standing in a bush on only **1–3%** of them. So the question this
wave exists to ask — *does a neuromodulator change injury-driven cover use?* — was close to
unanswerable in that world **for either arm**. A null result would have said nothing about the
modulator.

**Why the world was wrong.** The mechanism and the correct numbers were produced by the same session
and never joined up. `body.recovery_in_bush_multiplier` landed on 2026-09-15 (`761f427f`)
deliberately inert at `1.0` so the feature could ship without changing behaviour. The tuning study
that was meant to supply the real value finished the next day and recommended
`base 0.2 / accel 0.0 / multiplier 25` — and nothing ever wrote it into the config. Wave 1 was
launched into the gap.

**Disposition.** Eight of the fourteen runs had finished when this was caught; six were stopped
between 59% and 96% complete. All fourteen are retained on disk and remain **valid as a baseline for
the pre-tuning world** — each carries its own resolved `models/config.yaml`, so what it trained
against is self-describing and unambiguous. They are **not** comparable with Wave 2.

## Wave 2 — the same question in a world where cover is the only place healing works

Identical in every respect except the three recovery settings, now at the tuning study's
recommendation:

| setting | Wave 1 | Wave 2 |
|---|---|---|
| `body.recovery_base_rate` | 0.1 | **0.2** |
| `body.recovery_accel_rate` | 0.5 | **0.0** |
| `body.recovery_in_bush_multiplier` | 1.0 (inert, untraced) | **25.0** |

Resolved on all seven levels through the live loader: **10 injury points healed in 50 open-ground
rest steps, 20 in 100** — both under the 25-point threshold the study set for "resting in the open
is not worth doing" — against **5.0 per step in cover**, closing a typical 70-point wound in **14
steps**. Observation widths are unchanged (44 / 52 / 58 re-verified, and the neuromodulated agent
still constructs against each), so this changes the *problem*, not the *interface*.

One consequence worth stating plainly: at `1.0` the premium branch was never traced, which is what
made runs bit-identical to runs predating the key. At `25.0` it is compiled in. Bit-parity with the
pre-feature environment is gone, by choice.

### Wave 2 launched

2026-09-22 18:24 KST, all 14 runs up, group `basic_levels_q2_cover`, job-type `pilot`.
Tags are `rppo_bq2cover_*` — deliberately distinct from Wave 1's `rppo_basicq2_*`, so the
two waves can never be confused in WandB or on disk. Per-run node, GPU, PID, WandB id and
log path are in the wave block of `train_command-agent.sh`, and one `training-start` row
per run is in `docs/diary/2026-09-22.md`.

| # | tag | node:GPU | WandB id | obs |
|---|---|---|---|---|
| 1 | `rppo_bq2cover_lvl00_t1none_s42` | 101:0 | `s78nhqql` | 44 |
| 2 | `rppo_bq2cover_lvl00_t16quad_s42` | 101:1 | `buubzgb2` | 44 |
| 3 | `rppo_bq2cover_lvl01_t1none_s42` | 103:0 | `39zzf48r` | 44 |
| 4 | `rppo_bq2cover_lvl01_t16quad_s42` | 103:1 | `wusb4iu7` | 44 |
| 5 | `rppo_bq2cover_lvl02_t1none_s42` | 104:0 | `m2xz2m12` | 52 |
| 6 | `rppo_bq2cover_lvl02_t16quad_s42` | 104:1 | `jkrd3m2f` | 52 |
| 7 | `rppo_bq2cover_lvl03_t1none_s42` | 105:0 | `usiopa5z` | 52 |
| 8 | `rppo_bq2cover_lvl03_t16quad_s42` | 105:1 | `g193gcfn` | 52 |
| 9 | `rppo_bq2cover_lvl04_t1none_s42` | 106:0 | `ks9ve5z0` | 52 |
| 10 | `rppo_bq2cover_lvl04_t16quad_s42` | 106:1 | `b7n83tsb` | 52 |
| 11 | `rppo_bq2cover_lvl05_t1none_s42` | 107:0 | `z2u1orlf` | 58 |
| 12 | `rppo_bq2cover_lvl05_t16quad_s42` | 107:1 | `ihq3tt7f` | 58 |
| 13 | `rppo_bq2cover_lvl06_t1none_s42` | 108:0 | `j0z4lm4b` | 58 |
| 14 | `rppo_bq2cover_lvl06_t16quad_s42` | 108:1 | `6cmhr45f` | 58 |

**The width discriminator passed 14 of 14** — every banner printed the width its level should
resolve to (44 / 52 / 58), none printed 27, and no level's `extends:` chain reaches
`experiment/archive/`. The modulator was confirmed live on the modulated arms at both width
extremes (obs 44 and obs 58), logging `input_sensors=[all]` with all four sites, and
`DISABLED (baseline)` on all seven controls.

**The body-settings check — the one this relaunch exists for — passed against each run's own
saved artefact, not a fresh reload of the source.** `models/config.yaml` was read for one run
per width group (levels 00, 02, 05) and all seven values were correct in all three:
`recovery_base_rate: 0.2`, `recovery_accel_rate: 0.0`, `recovery_in_bush_multiplier: 25.0`,
`max_nutrition: 200`, `max_satiation: 200`, `satiation_setpoint: 100`, `overeating_death: true`.

Two recorded deviations, neither a defect, both carried over from Wave 1: `--log-interval 10`
overrides the config's 500, giving WandB 50x the usual row density; and every banner reads
`Device: gpu (cuda:0)` because `train.py` sets `CUDA_VISIBLE_DEVICES` to the requested index,
so the card is always local 0 inside the process — physical placement was verified against
`nvidia-smi` instead (exactly two compute apps per node, one per GPU, 60–100% util).
