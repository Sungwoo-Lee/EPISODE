---
title: "Continual worlds: does the modulator help an agent move between worlds whose body rules never change?"
topic: continual_worlds
status: active
created: 2026-09-28
last_updated: 2026-09-28
phase: continual / A-B-A-B structure (user framing 2026-09-28)
wandb_tag: "rppo_cw_*"
---

# Continual worlds: an A-B-A-B test of the modulator with a stationary body

> **Status (2026-09-28):** DESIGNED, configs written and loader-validated, **nothing launched**.
> Two launch blockers are open (section 6.2): the survivability pilots have not run, and the user
> must choose how to handle a known trainer bug that crashes a run when the number of animals
> changes between stages. Awaiting `plan-reviewer`, `env-config-reviewer` and the user.
> **Related:** level-05 factorial (source of the two pre-trained agents) [[LEVEL05_BODY_INTERACTIONS]] ·
> larger / less observable worlds and their search times [[STUDY_PLAN]] (context exploration) ·
> earlier continual probe [[NMN_CONTINUAL_DOUBLE_RETURN_PROBE]] · balance logging
> [[BALANCE_METRICS_TRAINING_LOGGING]] · curriculum lessons in the LLM wiki
> (`curriculum_learning`: plasticity loss, negative transfer).

## 1. Question

Our agents live in a grid world and must keep three body quantities in range: how fed they are,
how injured they are, and how warm they are. Two agents are compared throughout: an **ordinary**
recurrent agent, and the same agent with a **modulator** (a small side network that reads the
senses and rescales the main network's layers, loosely modelled on how neuromodulators such as
noradrenaline retune the brain). So far the modulator has only been tested in one world at a
time, where it gives at most a small survival edge.

The literature on neuromodulation says its main pay-off should appear when the **world keeps
changing and old worlds come back**: switching from world A to world B and back to A, the
modulated system should lose less when the world switches, recover faster, and be better on the
second visit to A than on the first.

This experiment builds exactly that test with one strict rule: **the body never changes.** Hunger,
injury, healing, body temperature and what the agent feels from inside its body obey identical
rules in every world. Only the outside world changes: grid size, how far smells carry, how many
hunters there are and how persistent they are, how scarce food is, how cold it is, how noisy the
senses are. So the body's signals mean the same thing everywhere and can act as a stable reference
for the modulator.

Each agent starts from its already-trained self (10 million episodes in the standard campfire world,
"Home"), visits a large safe foraging world once ("Forage"), then alternates between two harsher
worlds A and B four times (A, B, A, B), 2 million episodes per world. Three A/B pairs are run now:
**dangerous vs. scarce food**, **foggy vs. dangerous**, **winter vs. scarce food**. The primary
measure is **survival steps** per episode; the headline question is whether the modulated agent's
**dips on switching are smaller, its recoveries faster, and its returns better** than the ordinary
agent's. With one seed per agent this is a **screen**: it can show a pattern worth replicating, not
confirm one.

## 2. Hypotheses and predicted outcomes (pre-registered)

Plain names first; the symbols are only shorthand used in the tables below.

- **Smaller dip (H-dip).** On each switch into a world, the modulated agent's survival falls less
  below that world's reference level than the ordinary agent's does.
- **Faster recovery (H-rec).** After each switch, the modulated agent needs fewer episodes to climb
  back to 90 % of the reference level.
- **Better return (H-ret).** On the second visit to a world, the modulated agent gains more (or
  loses less) relative to its first visit than the ordinary agent does. This is the A-B-A-B
  signature: "second visit better than first" means something was kept, not relearned.
- **Less forgetting (H-forget).** Tested without training: a checkpoint taken at the end of a stage,
  played in the *other* worlds of its sequence, keeps more of its earlier survival for the modulated
  agent (forgetting matrix, 5.3).

**What would support the modulator (in advance):** in at least **2 of the 3 sequences**, the
modulated-minus-ordinary difference has the favourable sign on **at least 3 of the 4 switch measures**
(dip, recovery, return, forgetting) **and** at least one of those differences exceeds the
pre-registered noise yardstick (5.5). Predicted shape: the difference is small or absent on the
first visit to A and B (both agents learning a new world) and appears on the **returns** (stages 4
and 5), where a mechanism that keeps world-specific settings should pay off.

**What would refute it (in advance):** in at least 2 of the 3 sequences, the differences have mixed
or unfavourable signs, or all lie inside the noise yardstick. A **null** is also recorded if both
agents show no dip at all (the switches are too easy to tell anything apart; failure mode 7.2).

**Not claimed either way:** any mechanism. A modulated advantage here shows the model *does* better
under switching; *why* needs the later analyses (modulator activity per world).

## 3. Experimental design

### 3.1 The stationary body (identical in every stage, = today's level 05)

Every concept world `extends:` the level-05 campfire world and overrides **only** external keys.
Verified on the live loader (6.1, check C2): all 8 world configs resolve to the **same** body,
thermal-body, interoception and reward parameters as level 05 (the only differing fields are
per-animal arrays whose length changes with the animal count, and the external noise table in Fog).

| Body item | Value (level 05) | Keys (inherited, never overridden) |
|---|---|---|
| Nutrition | range 0–200, setpoint 100, metabolic cost 1/step, eating cost 1, **food energy per bite 6** (fixed), death at 0 and at 200 (overeating) | `body.max_nutrition`, `satiation_setpoint`, `metabolic_cost`, `eating_nutrition_cost`, `food_nutrition_gain`, `overeating_death` |
| Injury | max 100, healing only when resting, base rate 0.2, no acceleration, **bush healing ×25** (fixed), hits spread over 3 steps | `max_injury`, `recovery_base_rate`, `recovery_accel_rate`, `recovery_in_bush_multiplier`, `injury_smoothing_duration` |
| Body temperature | exchange 0.04, loss 0.02, warming ×2, cooling ×0.25, death below −15 or above +15 | `thermal.k_exchange`, `k_loss`, `warming_rate_scale`, `cooling_rate_scale`, `min/max_temperature` |
| Body rules B2–B5 / A1 | all off (as level 05) | `healing_nutrition_cost 0`, `healing_nutrition_dependence false`, `thermal.healing_*_sensitivity 0`, `injury_heat_exchange_gain 0` |
| Random start body | nutrition 0–200, injury 0–100, body temp −10…+5 | `random_start_*`, `start_*_low/high` |
| Interoception | satiation exact, felt injury through the 12-step alpha kernel (τ 3), body temperature exact; injury and nutrition not directly observed | `interoceptive_*`, `injury_observable false`, `nutrition_observable false`, `thermal.body_temp_observable true` |
| Reward | drive reduction, death penalty 100 | `use_homeostatic_reward`, `death_penalty` |
| Episode | max 500 steps | `environment.max_steps` |
| Agent | γ 0.95 and every other agent setting unchanged (the pre-trained agents' own configs) | agent YAMLs (4.1) |

### 3.2 The concept worlds (external only)

All worlds keep the **58-number observation**: senses are never removed, only their range, blur or
noise changes; temperature sensing is always on. Placement boxes are widened to the grid and counts
of anything not named are level 05's counts scaled by area (factor (G/10)², rounding rule of the
context-exploration generator, which validated 15 × 15 and 20 × 20 placement). "Density" below means
that scaling. Search time to the nearest food (from the context-exploration Part 3 reset study, mean
steps): 15 × 15 at density with smell 5 ≈ **9.7**; 1–2 items at smell 5 ≈ 51; at smell 8 ≈ 23; at
smell 3 with density food ≈ 20.5.

| Concept | Grid | Smell range | Food (items, bites, regrow delay) | Hunting predators | Ambushers | Bushes | Fires | Temperature | Other |
|---|---|---|---|---|---|---|---|---|---|
| **Nursery** (fresh pre-training only) | 10 | 20 | 4–6, 12, 0 | exactly 1; moves every 3rd step; notices at 3–4 cells; hit 15–45 | 0–2 | 8–12 (may sit by fires) | 2–3 | ambient ≈ −30 (as level 05) | rocks 6–12, rabbits 0–2 |
| **Home** | 10 | 20 | level 05 unchanged: food 1–4, predators 0–2, ambushers 2–12, bushes 4–10, fires 1–3 | | | | | | |
| **Forage** | 20 | 5 | 4–8, 12, 0 | none | 0–2 | 16–40 | 4–12 | ≈ −30 | rocks 24–48, rabbits 0–5 (pinned, see 6.2) |
| **Danger** | 15 | 5 | 2–9, 12, 0 | 2–3; notice at 5–9 cells (L05 1–7); stamina 100–200 (L05 30–150); lose-interest 2.0 (L05 1.5); hit 15–120 | 6–12 | 8–12 | 2–7 | ≈ −30 | rocks 14–27, rabbits 0–5 |
| **Famine** | 15 | 5 | **1–2**, 12, **30 steps** | 0–1 | 5–27 | 9–23 | 2–7 | ≈ −30 | rocks 14–27, rabbits 0–5 |
| **Winter** | 15 | 5 | 2–9, 12, 0 | 0–1 | 5–27 | 9–23, **none within 3 cells of the fire** | **exactly 1**, ratio 10 | **≈ −40** | rocks 14–27, rabbits 0–5 |
| **Fog** | 15 | **3** | 2–9, 12, 0 | 1–2 | 5–27 | 9–23 | 2–7 | ≈ −30 | sight blurred 3× (see below); noise on smell σ 0.3 and sight σ 0.2 only |
| **Harsh** (later, P5) | 15 | 8 | **1–2**, 12, 0 | 1–2 | 5–27 | **2–4** | 2–7 | **≈ −35** | rocks 14–27, rabbits 0–5 |

Config keys per concept (all under `environment:` unless stated): `height`/`width`; `sensory.sensor_radius`;
food `count_low/high`, `max_consumption`, `regeneration_delay`; hunting predator entry
(`class: predator`) `count_low/high`, `move_interval`, `detection_range`, `max_stamina`,
`lose_interest_multiplier`, `damage` — absent in Forage; ambusher (`hiding_predator` resource)
`count_low/high`; `campfire` / `rock` / `bush` `count_low/high` and `area`; campfire
`temperature_ratio` (Winter only, see below); `thermal.default_temp` (Winter [−41, −39], Harsh
[−36, −34]); `thermal.bush_min_fire_distance` 3 (Winter only); Fog adds
`sensory.visual_blur_radial_scale` 1.5 and a `perceptual_noise` block (enabled, every modality
`mode: constant`, σ 0 except olfaction 0.3 and visual 0.2).

**Three departures from the brief, each forced by a measured constraint:**

1. **Fog cannot have vision range 1.** Vision range changes the observation width (58 → 50) and the
   trainer's curriculum check refuses such a schedule (`train.py` stage validation: `obs_dim` and the
   modality fingerprint, which includes `visual_sensor_range`). Fog instead blurs sight along each
   line of sight three times more than level 05 (`visual_blur_radial_scale` 0.5 → 1.5; a continuous
   value, deliberately not fingerprinted), so distance becomes vague while direction stays. Noise
   uses `constant` mode, not level 06's injury-scaled mode, because noise that grows with injury would
   be a body rule, and body rules are stationary here.
2. **Winter's fire ratio is 10, not level 05's 11.** A fire is `ratio × |ambient|` hot. At −40 with
   ratio 11, the first step from the warm ring onto the fire reached **+15.65** on 1,000 real resets
   — instant death, breaking level 05's own design target ("first step onto a fire is survivable",
   level 05 measures +10.9…+12.3). At ratio 10 the worst case is **+11.73** and only the **4 cells
   beside the fire** are survivable to stand in (level 05: ≈ 16 cells). Tested ratios: 11 → 15.65,
   10 → 11.73, 9.5 → 9.78, 9 → 7.83, 8.25 → 4.90.
3. **Famine has no edge band.** A spawn area is a single rectangle; a band along all four walls needs
   several food entries, and independent per-entry counts would allow episodes with **no food at all**.
   The brief's fallback ("fewer items") is used: 1–2 items anywhere, regrowing 30 steps after being
   eaten out (level 05: instantly).

**A known risk, stated in advance:** in context-exploration Part 4, agents trained **from scratch** on
15 × 15 or 20 × 20 worlds with 1–2 food items **never learned to eat** within 2 M episodes. Famine and
Harsh sit exactly there. Our agents start already able to eat, which may or may not carry over — the
survivability pilots (3.6) decide it before any main run.

### 3.3 Sequences, stage length and why 2 M

| Sequence | Stage 1 | 2 (A) | 3 (B) | 4 (A again) | 5 (B again) | Now / later |
|---|---|---|---|---|---|---|
| **P1** Danger ↔ Famine | Forage | Danger | Famine | Danger | Famine | now |
| **P2** Fog ↔ Danger | Forage | Fog | Danger | Fog | Danger | now |
| **P3** Winter ↔ Famine | Forage | Winter | Famine | Winter | Famine | now |
| P4 Famine ↔ Danger (P1 reversed: order control) | Forage | Famine | Danger | Famine | Danger | later |
| P5 Harsh ↔ Forage | Forage | Harsh | Forage | Harsh | Forage | later (configs for Harsh exist) |

The pre-trained agent's 10 M episodes in Home **are** the Home stage; Home is not repeated inside the
run. It still appears in the forgetting matrix (the pre-trained checkpoint is row 0).

**2,000,000 episodes per stage** (10 M per run), because:
- In context exploration, today's world from scratch reached 227 survival steps at 2 M and only
  240 at 5 M (+6 %); a world the agent can learn at all is essentially learned within 2 M.
- The 1 M-episode pilots (3.6) show the within-world learning curve from the Home agent; if a pilot
  is still climbing > 5 % over its last fifth at 1 M, that is recorded and 2 M remains the default
  (not extended), because every stage must be the same length for the dip/recovery comparisons.
- Longer stages would push each 10 M run past ~2 days of GPU time per run (level-05 10 M took 19.4 h
  on 10 × 10; 15 × 15 / 20 × 20 are slower, to be measured by the pilots) with no measurement gain:
  the recovery window of interest is the first few hundred thousand episodes after each switch.
- Equal stages keep the four switch points comparable.

### 3.4 Starting agents and the shared-start confound

| Agent | Pre-trained run (level-05 factorial, all-rules-off world) | Final checkpoint | Agent config |
|---|---|---|---|
| Ordinary | `results/JAX_RecurrentPPO/20260927-053057_rppo_l05body_w0000_t1none_s42` | episode 10,000,046 | `configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml` |
| Modulated (FiLM at encoder, RNN, actor, critic) | `results/JAX_RecurrentPPO/20260927-053059_rppo_l05body_w0000_t16quad_s42` | episode 10,000,021 | `configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml` |

Their final Home survival (factorial §7): 249.8 (ordinary) and 253.4 (modulated) steps.

**Confound (stated):** all three runs of an agent start from the **same weights, the same optimizer
state and the same random-number key** (`--load-checkpoint` restores the key, so `--seed` does not
change the run). P1–P3 therefore differ only in their worlds from stage 2 on; their **stage-1
(Forage) segments are near-duplicates** of each other, differing only by GPU non-determinism. That
makes the three Forage segments a free measurement of the run-to-run noise floor (5.5), but it also
means the 3 sequences are **not** 3 independent replicates of the agent comparison, and the ordinary
and modulated agents differ in initialisation, capacity and seed as well as in the modulator
(factorial plan-review finding A2). The fresh-seed pre-trainings (3.5) exist to remove this later.

### 3.5 Fresh pre-training for the replicated version (2 more seeds per agent)

For each agent and seeds **43** and **44**: **Nursery for 2,000,000 episodes, then Home until the
episode counter reaches 10,000,000** (8 M Home episodes). Four pre-trainings, each run as **two
consecutive single-world runs** (a Nursery leg, then a Home leg that loads the Nursery leg's final
checkpoint), not as one two-stage continual run, because Nursery has one hunting-predator slot and
Home has two, and that roster change crashes the continual trainer today (6.2, blocker B1; verified
by smoke run S-B).

Why these lengths:
- **Nursery 2 M:** the curriculum study found easy levels learned within ~0.2 M episodes and that
  long over-training on easy levels hurt later learning (plasticity loss, LLM-wiki
  `curriculum_learning`); 2 M is ample for the basics (eat, hide when hurt, warm up) without
  lingering. It is also the stage length used everywhere else here.
- **Home to 10 M total:** it gives the fresh seeds the same total experience and the same episode
  counter as the seed-42 pair, so the three schedules in 4.1 serve them unchanged (their boundaries
  are absolute counter values, 3.3).
- **Competence gate (pre-registered):** a fresh Home leg counts as competent when, over its last
  200,000 episodes, mean survival is **≥ 95 % of the same agent type's seed-42 Home level** (ordinary
  ≥ 237.3, modulated ≥ 240.7) **and** it rose < 5 % over its last fifth. If it fails at 10 M, it is
  reported, not extended silently (extension would move the counter and needs new schedule files).

### 3.6 Survivability pilots (before any main run)

One pilot per new concept (Forage, Danger, Famine, Winter, Fog, Harsh): the **ordinary** pre-trained
agent, loaded from its Home checkpoint, trained **1,000,000 episodes** in that single world
(six runs). Pre-registered **survivable rule**, on the pilot's last 200,000 episodes:

1. mean survival ≥ **50 % of the ordinary agent's Home level** (≥ 124.9 steps), **and**
2. mean bites per episode ≥ **1.0** (it still forages; the from-scratch failure mode was ≈ 0.02).

A concept that fails is softened **once**, by one pre-named step, and re-piloted; if it fails again it
is dropped and its sequence replaced by the user:

| Concept | One softening step if it fails |
|---|---|
| Forage | food 4–8 → 6–12 |
| Danger | hunting predators 2–3 → 1–2 |
| Famine | regrow delay 30 → 10 steps |
| Winter | ambient −40 → −35 (fire ratio re-checked for the first-step target) |
| Fog | noise σ halved (smell 0.15, sight 0.1) |
| Harsh | food 1–2 → 2–4 |

A concept that passes with survival ≥ 95 % of Home **and** a first-20K-episode dip < 5 % is flagged
**"too easy to be a distinct world"** and shown to the user; it is not changed automatically.

## 4. Launch Manifest

All rows: `wandb-group` = `continual_worlds`. Tag = wandb-name. Scheme:
`rppo_cw_<cell>_<agent>_s<seed>`, agent ∈ {`t1none` ordinary, `t16quad` modulated}. The seed of the
main runs is the pre-trained pair's seed (42); `--seed 42` is passed for the record, the restored key
governs.

**Launch order:** pilots (runs 1–6) → pilot verdicts + user go → main runs (7–12) and fresh
pre-training Nursery legs (13–16) → Home legs (17–20) after their Nursery leg ends.

| Run | Status | Cell | Tag (= wandb-name) | wandb-group | wandb-job-type | Seed | Node | GPU | Launched at | WandB run ID | Log path |
|-----|--------|------|--------------------|-------------|----------------|------|------|-----|-------------|--------------|----------|
| 1 | planned | pilot Forage | `rppo_cw_pilot_forage_t1none_s42` | continual_worlds | pilot | 42 | — | — | — | — | — |
| 2 | planned | pilot Danger | `rppo_cw_pilot_danger_t1none_s42` | continual_worlds | pilot | 42 | — | — | — | — | — |
| 3 | planned | pilot Famine | `rppo_cw_pilot_famine_t1none_s42` | continual_worlds | pilot | 42 | — | — | — | — | — |
| 4 | planned | pilot Winter | `rppo_cw_pilot_winter_t1none_s42` | continual_worlds | pilot | 42 | — | — | — | — | — |
| 5 | planned | pilot Fog | `rppo_cw_pilot_fog_t1none_s42` | continual_worlds | pilot | 42 | — | — | — | — | — |
| 6 | planned | pilot Harsh | `rppo_cw_pilot_harsh_t1none_s42` | continual_worlds | pilot | 42 | — | — | — | — | — |
| 7 | planned | P1 ordinary | `rppo_cw_p1_t1none_s42` | continual_worlds | prod | 42 | — | — | — | — | — |
| 8 | planned | P1 modulated | `rppo_cw_p1_t16quad_s42` | continual_worlds | prod | 42 | — | — | — | — | — |
| 9 | planned | P2 ordinary | `rppo_cw_p2_t1none_s42` | continual_worlds | prod | 42 | — | — | — | — | — |
| 10 | planned | P2 modulated | `rppo_cw_p2_t16quad_s42` | continual_worlds | prod | 42 | — | — | — | — | — |
| 11 | planned | P3 ordinary | `rppo_cw_p3_t1none_s42` | continual_worlds | prod | 42 | — | — | — | — | — |
| 12 | planned | P3 modulated | `rppo_cw_p3_t16quad_s42` | continual_worlds | prod | 42 | — | — | — | — | — |
| 13 | planned | Nursery leg | `rppo_cw_nursery_t1none_s43` | continual_worlds | prod | 43 | — | — | — | — | — |
| 14 | planned | Nursery leg | `rppo_cw_nursery_t1none_s44` | continual_worlds | prod | 44 | — | — | — | — | — |
| 15 | planned | Nursery leg | `rppo_cw_nursery_t16quad_s43` | continual_worlds | prod | 43 | — | — | — | — | — |
| 16 | planned | Nursery leg | `rppo_cw_nursery_t16quad_s44` | continual_worlds | prod | 44 | — | — | — | — | — |
| 17 | planned | Home leg (after 13) | `rppo_cw_home_t1none_s43` | continual_worlds | prod | 43 | — | — | — | — | — |
| 18 | planned | Home leg (after 14) | `rppo_cw_home_t1none_s44` | continual_worlds | prod | 44 | — | — | — | — | — |
| 19 | planned | Home leg (after 15) | `rppo_cw_home_t16quad_s43` | continual_worlds | prod | 43 | — | — | — | — | — |
| 20 | planned | Home leg (after 16) | `rppo_cw_home_t16quad_s44` | continual_worlds | prod | 44 | — | — | — | — | — |

### 4.1 Configs to Produce

Env configs are all under `configs/environment/experiment/continual_worlds/`; continual schedules
under `configs/continual/continual_worlds/`. `T1` = `configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml`,
`T16` = `.../nmngaenorm_t16quad_ALL.yaml` (unchanged, the pre-trained agents' own configs).
`CK_O` / `CK_M` = the ordinary / modulated pre-trained `models/` directories (3.4).

| Run | Env config (single world) or stage dir + schedule | Agent | Starts from | Episode flag |
|-----|---|---|---|---|
| 1–6 | `forage_20x20` / `danger_15x15` / `famine_15x15` / `winter_15x15` / `fog_15x15` / `harsh_15x15` `.yaml` | T1 | `CK_O` | `--episodes 11000000` (≈ 1 M after the restored 10,000,046) |
| 7, 8 | `p1_danger_famine_stages/` + `p1_danger_famine.yaml` | T1, T16 | `CK_O`, `CK_M` | none (schedule sets 20,000,000) |
| 9, 10 | `p2_fog_danger_stages/` + `p2_fog_danger.yaml` | T1, T16 | `CK_O`, `CK_M` | none |
| 11, 12 | `p3_winter_famine_stages/` + `p3_winter_famine.yaml` | T1, T16 | `CK_O`, `CK_M` | none |
| 13–16 | `nursery_10x10.yaml` | T1, T1, T16, T16 | scratch | `--episodes 2000000` |
| 17–20 | `home_10x10.yaml` | as its Nursery leg | its Nursery leg's `models/` | `--episodes 10000000` |

Each stage file is a one-line `extends:` of its concept file, so every visit to a concept is the
identical world. The three schedules are identical: boundaries `[12M, 14M, 16M, 18M, 20M]` on the
restored episode counter, checkpoint every 100,000 episodes (20 per stage).

### 4.2 Launch commands (for `training-runner`, via `run_command.py`, after the user's go)

```bash
# pilots (run 1 shown; runs 2-6 change the world file and the tag)
python train.py --config configs/environment/experiment/continual_worlds/forage_20x20.yaml \
  --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
  --load-checkpoint results/JAX_RecurrentPPO/20260927-053057_rppo_l05body_w0000_t1none_s42/models \
  --episodes 11000000 --seed 42 --device cuda:0 --tag rppo_cw_pilot_forage_t1none_s42 \
  --wandb-name rppo_cw_pilot_forage_t1none_s42 --wandb-group continual_worlds --wandb-job-type pilot

# main (run 8 shown)
python train.py --configs-dir configs/continual/continual_worlds/p1_danger_famine_stages \
  --continual-schedule configs/continual/continual_worlds/p1_danger_famine.yaml \
  --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml \
  --load-checkpoint results/JAX_RecurrentPPO/20260927-053059_rppo_l05body_w0000_t16quad_s42/models \
  --seed 42 --device cuda:0 --tag rppo_cw_p1_t16quad_s42 --wandb-name rppo_cw_p1_t16quad_s42 \
  --wandb-group continual_worlds --wandb-job-type prod

# fresh pre-training (run 13, then run 17 when 13 has finished)
python train.py --config configs/environment/experiment/continual_worlds/nursery_10x10.yaml \
  --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
  --episodes 2000000 --seed 43 --device cuda:0 --tag rppo_cw_nursery_t1none_s43 \
  --wandb-name rppo_cw_nursery_t1none_s43 --wandb-group continual_worlds --wandb-job-type prod
python train.py --config configs/environment/experiment/continual_worlds/home_10x10.yaml \
  --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
  --load-checkpoint results/JAX_RecurrentPPO/<run-13 dir>/models \
  --episodes 10000000 --seed 43 --device cuda:0 --tag rppo_cw_home_t1none_s43 \
  --wandb-name rppo_cw_home_t1none_s43 --wandb-group continual_worlds --wandb-job-type prod
```

`--episodes` is refused in continual mode (the schedule's last boundary is the budget). `--log-interval`
is ignored by these configs (two-level logging block), so it is not passed.

## 5. Analysis plan (pre-specified)

Survival steps per episode is the only performance measure. Reward is not used for any verdict.
All curves are read from each run's local WandB episode rows (`Episode/Number`, survival,
`stage/index`), never end-of-training snapshots alone.

### 5.1 Reference level and the three switch measures

For each world X in a sequence, its **reference level** `R_X` = mean survival over the **last 200,000
episodes of X's first visit**. For every switch into a visit v of world X:

- **Dip** = 1 − (mean survival over the first 20,000 episodes of visit v) / `R_X`. On a first visit
  this is zero-shot transfer from the previous world; on a return it is what was kept.
- **Recovery** = episodes after the switch until the 20,000-episode running mean first reaches
  **0.9 × `R_X`** (censored at 2,000,000 if never; censored values are reported as "not recovered").
- **Return** (visits 4 and 5 only) = (mean over the last 200,000 episodes of the return visit) − `R_X`,
  and the change in dip and recovery from first visit to return.
- The **previous stage's end level** (last 200,000 episodes of the stage before the switch, in its own
  world) is reported alongside every switch for context.

The first logged rows after a switch are partial windows (the trainer clears its rolling episode
window at a stage switch); the analysis uses rows' `Episode/_window_n` to weight or skip rows under
1,000 episodes.

### 5.2 Modulator comparison

For every switch measure, the **modulated-minus-ordinary difference** (for dip and recovery, a
negative difference favours the modulator; for return, positive). Reported per switch (4 per
sequence), per sequence and pooled across the 3 sequences, always next to the noise yardstick (5.5).
The support/refute rule is section 2's.

### 5.3 Forgetting matrix (no training)

Checkpoints: the pre-trained start (row 0) and the **stage-end checkpoint** of each of the 5 stages
(the first checkpoint saved at or after each boundary; it is saved at the end of the iteration that
crossed the boundary, before the next iteration switches the world). Each is evaluated on **all eight
concept worlds** (Nursery, Home, Forage, Danger, Famine, Winter, Fog, Harsh) for **500 episodes**,
with the eval sweep driver (`scripts/eval/dwell_sweep/run_sweep.py`, `probe:
configs/environment/experiment/continual_worlds`, `conditions:` the eight file stems, `algo: rppo`).
The sweep spec is written after the main runs exist (it needs their result paths). Entries: mean
survival steps with 95 % CI. **Forgetting of world X at stage k** = survival on X at the end of X's
latest visit − survival on X at the end of stage k. Secondary: all 100 checkpoints at 50 episodes for
a within-stage trace, if cluster time allows.

### 5.4 Plasticity and balance (logged; descriptive)

- **Policy entropy** (`loss/entropy`) per stage: mean over the stage and over the first and last
  200,000 episodes; a stage-over-stage decline in within-visit learning speed (recovery) together with
  falling entropy is read as plasticity loss.
- **Balance metrics** already logged per episode (time shares in bush / on warm cell / eating,
  need-driven rates, cause-of-death shares; [[BALANCE_METRICS_TRAINING_LOGGING]]) per stage, first vs.
  last 200,000 episodes, and first visit vs. return. Descriptive only; no verdict rests on them.
- The same modulated-minus-ordinary difference is reported for entropy and the balance shares.

### 5.5 Noise yardstick

With one seed per agent, differences are judged against: (a) the spread of the **three
near-duplicate Forage segments** of each agent (P1–P3 stage 1; GPU non-determinism only, a lower
bound on noise), and (b) the factorial's seed SD of survival at level 05 (1.5 steps, so ≈ 2.1 steps for
a difference of two single runs). A modulated-minus-ordinary difference counts as "beyond noise" only
if it exceeds **2 × the larger of (a) and (b)**, on the survival scale of that world.

### 5.6 Temporal evolution

Every figure is a curve over training episodes with the stage boundaries marked: survival (20,000-
episode running mean), entropy, balance shares, both agents on one axis per sequence.

## 6. Pre-launch checks

### 6.1 Verified now (2026-09-28, read-only, project interpreter, CPU)

| # | Check | Result |
|---|---|---|
| C1 | All 8 new world configs load through `load_env_config` → `load_env_params` (the trainer's path) | pass |
| C2 | Observation width 58 on every world (breakdown sum and a real `ParallelEnv.reset`); modality fingerprint identical to level 05; body / thermal-body / interoception / reward fields identical to level 05 | pass (only per-animal array lengths and Fog's external noise table differ) |
| C3 | 1,000 real resets per world: every placed type spans its allowed area to within 1 cell; no item of a type whose area excludes (0,0) sits there; every drawn fire placed inside its inset area and ≥ 4 from other fires (checks from `make_worlds.py`) | pass on all 8 generated worlds; mean fires placed = mean drawn (e.g. Forage 8.01, Winter 1.00) |
| C4 | Thermal: every reset has ≥ 1 survivable cell; worst first step from the warm ring onto a fire < +15 | pass: worst +12.4 (Home 12.29, Harsh 14.37, Winter 11.73 at ratio 10); at ratio 11 Winter fails (+15.65), hence 3.2 departure 2 |
| C5 | Hunting-predator / rabbit slot counts per world | Home 2/2, Nursery 1/2, Forage 0/5, Danger 3/5, Famine 1/5, Winter 1/5, Fog 2/5, Harsh 2/5 |
| C6 | Pre-trained checkpoints exist and are final | ordinary 10,000,046; modulated 10,000,021 (log: "Training complete") |
| C8 | The three real schedules, built by `train._build_continual_schedule` itself | 5 stages each, boundaries `[12M … 20M]`; the restored counters 10,000,046 / 10,000,021 map to stage 0; every stage resolves to its concept world. Note: on the continual path the noise table is listed alphabetically (the schedule builder deep-copies the base through `yaml.dump`), on a bare load in file order; every noise value stays attached to the same named sense, and lookups are by name, so Fog's noise is the same either way |
| C7 | The two stale stage tests (Known Bugs row "8-wide vision") | still fail exactly as recorded: `'visual_properties' has length 8 but visual_vector_size is 1` in both `test_continual_bm_transition.py` and `test_continual_resume_rebuild.py` |
| S-A | Smoke run: the ordinary pre-trained checkpoint loaded into a 6-stage continual run Forage 20×20 → Danger → Famine → Winter → Fog → Danger 15×15 (CPU, WandB off, scratch output) | **pass**: restored 27 parameter leaves + optimizer at episode 10,000,046; Stage 0 world rebuilt after restore; five switches (grid 20 → 15, hunting-predator slots 0 → 3 → 1 → 1 → 2 → 3, noise off → on → off) each recompiled and trained on; `Training complete`, exit 0. Dumped stage configs carry each world's grid / smell range / noise |
| S-B | Smoke run: fresh Nursery → Home as one continual run (hunting-predator slots 1 → 2) | **crash, as predicted by Known Bug A2**: at the Nursery → Home switch, `train.py:1825` `ValueError: non-broadcastable output operand with shape (128,1) doesn't match the broadcast shape (128,2)`. Hence the two-leg pre-training (3.5) |
| S-C | Smoke run: the modulated checkpoint loaded into Forage → Danger | **pass**: modulated checkpoint restored at 10,000,021; Forage → Danger switch trained on; exit 0 |

### 6.2 Blockers and hand-offs

- **B1 — roster-size change between stages (Known Bugs A2, open).** The trainer sizes its per-animal
  distance accumulators from the **first** stage's number of hunting-predator and rabbit slots and
  never resizes them. A later stage with **more** slots crashes; fewer slots silently mislabels.
  This design stays clear of it without code changes: every main-run stage has **5 rabbit slots**
  (Forage's rabbits pinned at 0–5 instead of density 0–8), and stage 1 (Forage) has **no hunting
  predator**, so per-predator distance logging is off for the whole run (the nearest-predator distance
  and all survival / balance logging are unaffected). The cost: no per-predator distance curves. The
  fresh pre-training avoids it by running Nursery and Home as two runs. **Decision for the user:**
  accept this, or have `developer` fix A2 first (per-stage resizing) to regain the per-predator curves.
- **B2 — pilots not yet run.** No main run launches before runs 1–6 pass (3.6).
- **Hand-off to `developer` (via `senior-developer`):** fix the two stale continual tests (C7) — shrink
  their inline stage worlds' `visual_properties` to the default vector width or pin the width. Until
  fixed, the continual stage-switch and resume paths have no passing regression test; smoke runs S-A…S-C
  are this design's substitute, not a replacement.
- **Known and accepted:** Known Bugs B5 (a resumed single-world run pairs restored recurrent memory
  with fresh worlds for its first window) affects the first rows of pilots and Home legs only; the
  continual path re-initialises memory correctly.

### 6.3 Still to check at launch (`training-runner` / `env-config-reviewer`)

- `env-config-reviewer` pre-flight on all files in 4.1 (not yet run).
- Live GPU state and NAS mount on the chosen nodes; checkpoint directories readable from the node.
- First stage switch of each main run: log line `[STAGE] 0:01_forage -> 1:02_...` and no traceback.

## 7. Failure-mode catalog (decided in advance)

| # | Outcome | Reading |
|---|---|---|
| 7.1 | NaN / value explosion in one run | that run is invalid, relaunched once from its last good checkpoint; not evidence about the modulator |
| 7.2 | Neither agent dips at any switch (dip < 5 % everywhere) | the worlds are not distinct enough; null for this design, not for the hypothesis |
| 7.3 | A world is never recovered (censored) for both agents | that world is too hard at 2 M; its switch measures are reported but excluded from the support/refute count |
| 7.4 | Only one agent collapses in a world (survival < 0.6 × its `R_X` for the whole visit) | reported and marked; the verdict is computed with and without that sequence |
| 7.5 | Late stages learn more slowly for both agents (recovery on return slower than first visit) | plasticity loss, recorded as a result in its own right (5.4); not a design flaw |
| 7.6 | Differences all within the noise yardstick | null for this screen; the fresh-seed replication decides |
| 7.7 | A stage switch crashes | run invalid; resume from its last checkpoint after the fix (the resume path rebuilds the right stage world) |

## 8. Metrics requested (optional, for the user)

| Metric | Why now | Where it'd live | Cost |
|---|---|---|---|
| Per-stage modulator activity (mean and spread of the FiLM scale and shift per site, per stage) | the "why" behind any H-dip / H-ret effect; logged once per stage window | `train.py` rPPO logging, `mod_info` already returned by the train step | cheap |
| Per-predator distance curves across roster changes | lost under B1's workaround | `train.py` continual stage switch (A2 fix) | cheap |

If accepted, route through `feature-workflow` before launch; neither blocks the design.

## 9. Open decisions for the user

1. **B1:** accept the no-code workaround (no per-predator distance curves) or fix Known Bug A2 first.
2. **Fog's sight:** vision range 1 is impossible at width 58; accept "3× blur + noise" as Fog's sight change?
3. **Winter's fire:** accept fire ratio 10 (first step onto the fire survivable, 4 warm cells) instead of 11?
4. **Famine:** accept "1–2 items, regrowing after 30 steps, anywhere" in place of the edge band?
5. **Forage is repeated in all three runs of an agent** (near-identical copies). Alternative: run Forage
   once per agent and branch P1–P3 from its end checkpoint (saves 8 M episodes of GPU time, but the
   three branches must wait for Forage to finish and the noise-floor measurement 5.5a is lost).

## 10. Results

*(blank until the runs finish)*

## 11. Conclusions

*(blank until the runs finish)*

## Feedback from plan-reviewer

**Verdict: SOUND WITH CONCERNS** (2026-09-28, reviewed against commit `95b34d01`, before any launch).
The A-B-A-B design is measurable in survival steps only, its refutation rule is written down in
advance, its configs resolve through the trainer's own loader, and the stage-switch path was
exercised end to end by real smoke runs. What is not ready is the **pilot phase as committed**:
the manifest names six ordinary-only 1 M-episode pilots (§3.6, §4 rows 1–6), while the pilots
the user asked to launch now are (Pilot 1) a single switch from the Home agent into each of the
six new worlds for **both** agents, up to 3–4 M episodes, to measure the dip, the time to level off
and survival; (Pilot 2) short 1 M-per-stage A-B-A-B runs of P1 and P2 for both agents; and
(Pilot 3) Nursery from scratch for both agents. None of those is in the doc, no schedule file
exists for Pilot 2, and the rule that turns "time to level off" into a stage length is not yet
written down. That is doc-and-config work (an hour, `experiment-designer`), not a flaw in the
science, but launching from the manifest as it stands would launch the wrong pilots. No Critical
finding: no `docs/reviews/` file is written.

Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run ·
🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

### Findings

| # | Sev | Location | Issue | Suggested fix | Owner |
|---|---|---|---|---|---|
| F1 | 🟡 | §3.6, §4 rows 1–6, §4.1 | The committed pilots (ordinary only, 1 M, `--episodes 11000000`) are not the pilots requested. Pilot 1 needs 12 rows (both agents; `--episodes 13000000`–`14000000` on the restored counter), Pilot 2 needs two new schedule files with boundaries `[11M, 12M, 13M, 14M, 15M]` and their stage folders (4 rows), Pilot 3 is manifest rows 13 and 15 as written (Nursery legs, seed 43) — say so, or use a dedicated seed so the pilot is not also a production leg. | Rewrite §3.6 and the manifest to the three-pilot set before `training-runner` is spawned; add the Pilot 2 schedules under `configs/continual/continual_worlds/`. | experiment-designer |
| F2 | 🟡 | §3.3, §3.6 (stage-length rule) | "Stage length = 1.5 × time to plateau" has no pre-registered definition of *plateau*, no rule for combining the two worlds of a pair (and the two agents), no fallback if a pilot has not levelled off by 3–4 M, and no feasibility cap. A 3 M plateau gives 4.5 M stages and 22.5 M-episode main runs — 4–5 GPU-days each at 15 × 15 speed (§3.3's own 2-day ceiling would be breached). Also: the pilots switch **Home → X**; the main runs switch Forage → A and A ↔ B, so the pilot's dip is not the main run's dip — only the plateau time and the survivability verdict transfer. | Pre-register: plateau = first episode at which the 20 000-episode running mean stays within 5 % of the pilot's last-200 000 mean for the rest of the pilot; stage length = 1.5 × the **largest** plateau over both worlds and both agents of the pair, rounded up to 100 000 and **capped at 3 M** (3 × 5 = 15 M episodes on top of 10 M); if a world has not levelled off by the pilot's end, that is a survivability fail (§3.6 softening step), not a longer stage. Schedules are regenerated from that number, so §4.1's `[12M…20M]` are provisional and must be marked so. | experiment-designer |
| F3 | 🟡 | §5.1 Recovery, §2 H-rec | Stages and recovery are counted in **episodes**, but the trainer updates per iteration of fixed environment steps (`num_envs × num_steps`), so an agent that survives longer gets **more gradient updates per 20 000 episodes**. Recovery-in-episodes therefore favours whichever agent already survives longer — the same agent H-dip favours — a systematic bias, not noise. It also makes a 2 M-episode stage in a 120-step world half the training of one in a 250-step world. | Report every recovery time in both units: episodes and cumulative environment steps (reconstructible per row as Σ `Episode/Steps_mean × window episodes`; `global_step` is not on the episode rows). Make the H-rec vote require the favourable sign in **both** units. Keep episode-based boundaries (the trainer supports nothing else) but state the per-stage update count in the results. | experiment-designer (rule); experiment-analyzer (extraction) |
| F4 | 🟡 | §5.5 Noise yardstick | Yardstick (b) is the **Home** seed SD (1.5 steps at ~250 survival) applied to Danger / Famine / Winter / Fog, where nobody has measured seed spread and where the earlier continual probe saw ±4.4 steps on a harder world. Yardstick (a) (three near-duplicate Forage segments) measures GPU non-determinism only. A 5-step Famine gap can clear "2 × the larger" and still be seed noise. | Say the yardstick is a floor, not an estimate; add the across-checkpoint spread of the 200 000-episode window means within a visit (the factorial's own device) as yardstick (c); and, if Open decision 5 is taken (branch from one Forage run), drop (a) with nothing lost. | experiment-designer |
| F5 | 🟡 | §5.3 Forgetting matrix | 500 evaluation episodes per cell gives a 95 % CI of roughly ±9–13 survival steps (per-episode survival SD is ~100–150 in these worlds), so the matrix cannot resolve differences at the §5.5 scale, and H-forget's vote in the §2 rule has no noise criterion of its own. The sweep spec's episode count is the `episodes:` key (default 30), so it must be set explicitly. | Set `episodes: 2000` (evaluation is cheap: one model build per checkpoint) and pre-register H-forget's "beyond noise" as non-overlapping CIs. | experiment-designer |
| F6 | 🟡 | §1 ("So far the modulator has only been tested in one world at a time"), §2 | Prior art: [[NMN_CONTINUAL_DOUBLE_RETURN_PROBE]] (2026-05) already ran a 5-stage A-B-A-B-A external-world switch (active ↔ passive predator; body unchanged) and reported the modulated agent ~107–132 steps ahead on the return stages, less forgetting confirmed, and the dip predicate found ill-posed. This design is a **replication at scale** of that positive (tiny 1 500-episode stages, MC returns, single seed then) with a stationary-body framing — say so, and let the pre-registered prediction inherit its lesson that the dip lives in recovery speed, not depth. As written the doc contradicts a result the project already has. | Rewrite the §1 sentence; add one paragraph in §2 positioning H-ret / H-forget as the replication targets and the earlier ±4.4-step noise. | experiment-designer |
| F7 | 🟡 | §2 support rule | "2 of 3 sequences" counts sequences as independent votes; §3.4 already says they are not (same weights, same optimizer state, same key; P1 and P3 share Famine, P1 and P2 share Danger). A single lucky initialisation pairing wins 3 of 3. | Keep the rule but state that its support verdict is "one initialisation pair, three world-pairs"; the fresh-seed replication (§3.5) is the only route to "the modulator". | experiment-designer |
| F8 | 🟢 | §4.2 | Launch commands read `python train.py`; the project runs `/home/vncuser/miniconda3/envs/grid_world_pain/bin/python`. The runner's script owns the interpreter, but the doc should not show the wrong one. | Replace the interpreter. | experiment-designer |
| F9 | 🟢 | §5.4 | `loss/entropy` is on the iteration stream, not the episode rows; "per stage, first / last 200 000 episodes" needs the iteration → episode mapping. | Say the entropy windows are cut by `stage/index` on the iteration stream. | experiment-analyzer |

### Verified — claims I tried to break and could not

- **A2 workaround holds.** `train.py:1410-1415` sizes the per-animal accumulators from stage 0; `train.py:1773` never puts `dist_per_predator` into the info dict when `num_predator_for_log == 0`, so a Forage-first run never touches the crashing line (`train.py:1825`). The behaviour-measure toolkit is off (`behavior_measures.enabled: false` in the pre-trained runs' saved config), so nothing else is sized from stage 0. Cost is exactly what §6.2 says: no per-predator distance curves. Nearest-predator distance (`dist_to_pred`), survival, food eaten and the balance counters come from the current stage's environment.
- **Grid size is not a direct cue.** The pre-trained agents have `location_sensor: false` (saved config), so no absolute-position channel rescales with the grid; walls are only seen within vision range 2. And within every A ↔ B pair both worlds are 15 × 15 — the grid changes once (Forage → A) and never on the alternation being measured. Good property; state it in §3.2.
- **Stage-end checkpoint claim** (§5.3): the transition check runs at the top of an iteration (`train.py:1663`) and the checkpoint scheduler at the bottom (`train.py:2601`); boundaries are multiples of 100 000, so the first checkpoint at or after a boundary is the crossing iteration's, saved before the world switches. One extra checkpoint is written at the first iteration after a restore (`last_checkpoint_save` starts at 0) — harmless, it is row 0.
- **Restore picks the right checkpoint** — `mngr.latest_step()` (numeric), not a string sort; S-A/S-C confirm 10 000 046 / 10 000 021.
- **Fog's noise table** lists all 12 modalities in `default.yaml`'s order; `env-config-reviewer` owns the mechanical obs ↔ noise check.
- **Episode-vs-checkpoint arithmetic**: `--episodes` is the absolute counter (`train.py:1656`), so `--episodes 11000000` on a 10 000 046 restore is ≈ 1 M more; Nursery 2 M → Home `--episodes 10000000` lands the fresh seeds on the same counter the schedules assume.
- Registry change-log entry present (CONFIG_CRITICAL_SETTINGS.md, 2026-09-28); no `scripts/` change; no schema change; no destructive git step anywhere in the plan.

### Can the pilots answer "is it working as expected"?

- **Pilot 1 (single switch, both agents, 3–4 M)** answers survivability, plateau time and the Home → X zero-shot dip, per world and per agent. It does **not** measure the main run's dips (different source world) and, with the same weights and key as the main runs, its Forage segment is a near-copy of main-run stage 1. Worth it, provided F2's plateau rule is written first — otherwise the number it produces has no consumer.
- **Pilot 2 (1 M-per-stage A-B-A-B, both agents)** is a **pipeline shakedown**, not a science pilot: four GPU stage switches on the real checkpoints, checkpoint cadence, `stage/index` rows, the forgetting-matrix sweep on a real continual run (`eval_rollout` refuses stage-0 `config.yaml` for continual runs — the sweep's per-condition `--config` bypasses it; test that once here). By §3.3's own argument 1 M is below plateau, so its return-visit numbers must not be read as evidence. Frame it that way in the doc.
- **Pilot 3 (Nursery from scratch, both agents)** has no pass criterion — only the Home leg has one (§3.5). Pre-register one (e.g. last-200 000 survival and bites ≥ 1, no collapse), otherwise the leg cannot fail.

### Assumptions the conclusion rests on

| Assumption | Status |
|---|---|
| The pre-trained pair is competent enough that Famine / Harsh do not reproduce context-exploration's "never learns to eat" | unverified — that is what Pilot 1 tests (good) |
| Seed noise in the new worlds is of the Home order (1.5 steps) | unverified; F4 |
| 15 × 15 / 20 × 20 throughput keeps a 10–15 M-episode run under ~2–3 days | unverified; Pilot 1 measures it — record it/s in the manifest |
| `nmngaenorm_t1none.yaml` is the no-modulator baseline (not a one-site modulator) | verified via the level-05 factorial's own labelling; not re-derived here |
| The three smoke runs (S-A … S-C) ran on the same code as the launch will | unverified — HEAD moves; re-run S-A once on the launch node before run 7 |
| GPU non-determinism is small relative to seed noise | untested; the three Forage copies will show it, or branching removes the question |

### Cost of being wrong

If the pilots launch from the manifest as committed, the cost is one day of six wrong 1 M runs
and a second pilot round. If the stage length is set without F2's rule, the cost is twelve
10–20 M-episode main runs (2–5 GPU-days each) whose return-visit measure sits below plateau and
cannot be re-read. If F3 is left as is, the headline "recovers faster" claim carries a built-in
bias in the modulator's favour and would not survive a referee. Nothing here risks data loss.

Reviewed by: plan-reviewer
