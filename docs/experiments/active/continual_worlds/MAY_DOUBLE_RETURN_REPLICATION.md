---
title: "May double-return replication: does the modulated agent still come back better after the hunter returns, under today's body and senses?"
topic: continual_worlds
status: active
created: 2026-09-29
last_updated: 2026-09-29
phase: continual / replication of the May 2026 probe
wandb_tag: "rppo_cw_mayrep_{t1none,t16quad}_s{42,43,44}"
develop_link: docs/experiments/active/hypervigilance/NMN_CONTINUAL_DOUBLE_RETURN_PROBE.md
---

# May double-return replication, under today's settings

> **Status (2026-09-29): DESIGNED; user decisions taken (8.1). Configs are written and validated
> with the trainer's own loader. Nothing is launched.** Manifest rows M1–M6 are **ready, pending
> reviews**: they still need an `env-config-reviewer` pre-flight, a `plan-reviewer` pass on this
> design, and a GPU assignment.
>
> **Related:** the May probe being replicated: [[NMN_CONTINUAL_DOUBLE_RETURN_PROBE]] ·
> the larger continual study this sits beside, whose analysis rules it borrows: [[CONTINUAL_WORLDS]] ·
> the level-05 world whose body it keeps: [[LEVEL05_BODY_INTERACTIONS]].

## 1. Question

In May 2026 the project ran one small experiment that favoured the **modulator**. The modulator
is a small side network that rescales the main network's layers, loosely modelled on how
neuromodulators such as noradrenaline retune the brain. An agent learned to survive in a
10 × 10 grid world while the one predator switched behaviour between training stages:
**hunting** (it notices the agent from five cells away and chases it), then **harmless-looking**
(it never hunts and just wanders in one corner, although it still bites on contact), then
hunting again, harmless again, hunting again.

When the hunter came back, the modulated agent survived about **107 and 132 steps longer per
episode** than the ordinary agent. It lost about 70 % less of what it had learned, and its
immediate drop at each switch was about the same size as the ordinary agent's. That result came
from **one training run per agent**, and the three-seed repeat it asked for was never run.

Since May, the project has changed both the agent's body and its senses. Hunger now has an
upper limit (over-eating kills). Injuries heal only while resting, 25 times faster in a bush.
Smell now carries direction, and sight no longer tells one animal from another. This experiment
asks one thing: **with today's body, senses and agents, trained from scratch on May's
hunting ↔ harmless schedule with three seeds per agent, does the modulated agent again come back
better after the hunter returns?**

We rebuild May's outside world as closely as the current config format allows, including the
predator and rabbits smelling identical. We keep today's body, senses and agents. Survival steps
per episode is the only performance measure.

## 2. Hypotheses and predicted outcomes (pre-registered)

The hypotheses mirror May's findings. Plain names come first; the symbols are shorthand used in
the tables of section 5.

- **Better return (H-ret; May's headline).** On both returns of the hunting predator (stages 3
  and 5), the modulated agent survives longer than the ordinary agent. May: +106.9 steps (stage
  3) and +132.5 (stage 5).
- **Less forgetting (H-forget).** On both returns, the modulated agent loses fewer survival steps
  relative to its own stage-1 level than the ordinary agent does. May: −51.9 vs −147.7 steps on
  the first return and −46.2 vs −167.5 on the second, i.e. 65 % and 72 % less forgetting.
- **Equal dip (H-dip, predicted null).** Right after harmless → hunting (the start of stages 3
  and 5), both agents drop by about the same amount. May saw equal dips (425 / 417 vs 432 / 446
  steps on its own 200-episode definition). The difference lay in recovery, not in the drop.
- **Faster recovery (H-rec).** After harmless → hunting, the modulated agent climbs back to 90 %
  of the reference level sooner. May described this qualitatively only.
- **Second return at least as good as the first (H-hyper; secondary, May's weakest signal).**
  For the modulated agent, stage 5 ≥ stage 3, while the ordinary agent declines (stage 5 <
  stage 3). May: +5.75 vs −19.8 steps.

**What counts as replicated (in advance).** The rules are written out in 5.3. In short, the
May result is **replicated** if the modulated agent is ahead on **both** returns **and** forgets
less on both returns. "Ahead" means the favourable sign in at least **2 of the 3** seed pairs,
**and** a mean difference larger than twice its between-seed standard error. The result is
**not replicated** if the differences have the wrong sign in most pairs or sit inside seed noise.
It is **reversed** if the ordinary agent is clearly ahead. Magnitude is compared with May's
separately (5.4), because today's body gives different absolute survival levels.

**Predicted shape.** Little or no difference in stage 1 (May: +11) or in the harmless stages
(May: both near the 500-step cap). The difference appears on the returns, stages 3 and 5.

**Not claimed either way.** Any mechanism. This design also does not test May's exact
modulated agent: today's modulated agent has no policy-temperature head (section 3.4).

## 3. Experimental design

### 3.1 What stays today's: the body, the senses, the reward

Both worlds `extends:` the level-05 world, override only external keys, and switch thermal
**off** (3.3). Verified on the live loader: apart from the thermal fields, no body, interoception,
reward or episode-length field differs from level 05 (6.1, check V3).

| Item | Value (today, kept) | May had |
|---|---|---|
| Nutrition | range 0–200, setpoint 100, metabolic cost 1/step, eating cost 1, food energy per bite 6, death at 0 **and** at 200 | range 0–100, setpoint at the ceiling, no over-eating death |
| Injury and healing | max 100; healing only while resting, base 0.2/step, no compounding, **×25 in a bush**; hits spread over 3 steps | base 0.1 with compounding 0.5, no bush premium; hits over 3 steps |
| Start of episode | random nutrition 0–200 and injury 0–100; random position | nutrition 100, injury 0; random position |
| Interoception | satiation exact; felt injury through the 12-step kernel (τ 3); injury and nutrition not observed directly | same |
| Reward | drive reduction, death penalty 100 | same |
| Episode | max 500 steps | same |
| Senses | smell sampled on a 5-cell diamond, falloff 1/distance (`decay_power` 1.0), range 20; sight on a 13-cell diamond, **1 presence channel** (blurred, capped; no identity) | smell at the agent's cell only, falloff 1/distance² (`decay_power` 2.0), range 20; sight at the agent's cell only, 8 identity channels |
| Observation width | **52** numbers (satiation 1, felt injury 1, pain 1, smell 25, collision 5, proprioception 6, sight 13) | 27 |

The width differs from May's (27) and from level 05's (58, which includes the 6 thermal
numbers). That is allowed because both agents train from scratch, and the agent configs do not
pin a width. Verified: both agents build and train against 52 (6.1, V4).

### 3.2 What mimics May: the outside world and the predator switch

Every May value below is read from the May run's **saved** stage configs
(`results/JAX_RecurrentPPO/20260511-174837_rppo_nmn_cont_dr_mod_s0_r2/models/stage_0*.yaml`),
not from `configs/continual/nmn_double_return_stages/`. The saved files are the ground truth:
they are what the trainer read, and the stage files have since been touched by later
schema work. May's `default.yaml` had no `entities:` block yet (added 2026-06-16, `e2333593`),
so the May runs trained on their own authored scene. The Known Bugs caveat about the
`nmn_double_return_stages` family training on the default scene applies to runs between
2026-06-16 and the 2026-07-23 fix, not to May.

**The predator switch.** Diffing May's saved active and passive stage files shows exactly
**four** changed predator keys and nothing else in the world:

| Predator key | Active (stages 1, 3, 5) | Passive (stages 2, 4) | Effect |
|---|---|---|---|
| `detection_range` | 5 | **0** | notices the agent only when already on its cell |
| `hunt_stamina_threshold` | 0.7 | **1.1** | needs 110 % of max stamina to start a hunt, which can never happen |
| `spawn_area`, `patrol_area` | whole grid | **top-left quadrant** | wanders in one corner, like the top-left rabbit |
| everything else | stamina 30 (recovers 1/step), gives up beyond 5 × 1.5 cells, pauses 3 steps after a hit, hit 15–45, moves every step, count 1 | same | the passive predator still **bites** (15–45) if the agent steps onto it; contact damage does not depend on hunt mode |

Measured on today's code over 256 environments × 300 random-action steps (6.1, V6): the active
predator is in hunt mode on **40.8 %** of live steps; the passive predator on **0.0 %**.

**Full May → replication mapping.**

| Aspect | May (saved config) | Replication | Same? |
|---|---|---|---|
| Grid, episode cap, start | 10 × 10, 500 steps, random start position | same | yes |
| Food | 2 in top-left + 2 in bottom-right quadrant, 12 bites each, regrows at once | same (fixed counts, same quadrants) | yes |
| Ambushers (`hiding_predator`) | 1 per quadrant, hit 15–45, back after 20 steps | same | yes |
| Rocks | 3 per quadrant, 1–5 damage, walkable | same | yes |
| Bushes | 5 top-right + 5 bottom-left, hide the agent; **animals can enter** | 5 + 5, hide the agent; **animals cannot enter** (`blocks_animals: true`) | **no** (see below) |
| Rabbits | 2: one wanders in the top-left, one in the bottom-right | same | yes |
| Predator, active / passive | see table above | same four keys, same values | yes |
| Pounce (jump attack) | did not exist | explicitly off (`attack_range [0,0]`, `attack_success_rate 0`) | yes |
| Smell of predator vs rabbits | **identical** `[0, 1, 0, 0, 0]`, no spread ("sameProp") | identical `[0, 1, 0, 0, 0]`, no spread | yes |
| Quadrant animals' roaming box | the patrol clip lets them reach one row and column past the quadrant (6 × 6) | same code behaviour (measured; 6.1, V7) | yes |
| Smell falloff | `decay_power` 2.0 | **1.0** (today's canonical, per the user) | no |
| Smell range | 20 | 20 | yes |
| Smell / sight sampling | own cell; 8 identity channels | 5-cell / 13-cell diamonds; 1 presence channel | no (today's senses) |
| Thermal | none | off | yes |
| Body | see 3.1 | today's level-05 body | no (by design) |
| Perceptual noise | off | off | yes |
| Per-tag labels | active predator `full`, passive `TL` | both `pred`; rabbits `rabbit_tl`, `rabbit_br` | no (removes May's A2 mislabel) |

**Differences that could not be avoided or were chosen, and why.**

1. **Bushes block animals.** Today's canonical bush (since 2026-09-14) is a physical refuge: a
   predator cannot step into it. In May a hunting predator lost track of an agent in a bush but
   could still walk in and bite. This is kept because the user asked to preserve today's
   recovery-related settings, and the ×25 bush healing only makes sense in a bush that is a
   refuge. It makes the active world somewhat **easier** than May's. It applies to both agents
   and all stages.
2. **Senses.** Smell now has direction, and sight shows presence but not identity. In May, sight
   told a predator from a rabbit only on the agent's own cell, that is, at contact. So both then
   and now, **before contact the only cue that separates the predator from a rabbit is how it
   moves.** That behaviour-only identification is the core of May's design, and it is kept.
3. **Smell falloff 1.0 instead of 2.0** (user instruction). Smell stays readable farther away,
   which again makes food and animals easier to locate than in May.
4. **Placement.** May's `placement: per_entity` is today's default. The only schema changes are
   that zero-count entries are omitted and each quadrant group is one entry with `count:`.
   Verified over 1,000 real resets: every entity inside its declared area, none stacked on
   another (6.1, V5).

### 3.3 Thermal: off (decision and reasoning)

**Off.** (1) May had no body-temperature system; the saved config has no `thermal:` block and
its observation has no temperature numbers. (2) Level 05's cold world (ambient about −30, with
campfires) adds a cause of death with no counterpart in May. In the continual-worlds pilots
it was a large share of deaths (Winter: 32 % ordinary, 44 % modulated). That would dilute
the one factor this experiment varies, the predator's behaviour. (3) A 10 × 10 grid already holds
4 food items, 4 ambushers, 12 rocks, 10 bushes and 3 animals. Adding 1–3 fires with their
separation rules would crowd it further and change May's layout. (4) The user allowed dropping it.

**Cost.** The observation is 52 numbers instead of level 05's 58, so these checkpoints cannot be
evaluated in the continual-worlds concept worlds, which are all thermal. Nothing in this
design needs that. `thermal.enabled: false` is the registry's canonical value, so **no
critical-settings registry value changes and no change-log entry is needed**.

### 3.4 Agents, seeds, schedule

| Arm | Agent config | What it is |
|---|---|---|
| Ordinary | `configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml` | GRU recurrent PPO, GAE_NORM returns, no modulator |
| Modulated | `configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml` | same, plus a FiLM modulator (16 hidden units) that reads every sensed number and rescales encoder, RNN, actor and critic; **policy-temperature modulation off** |

Both agents are today's ordinary / modulated pair (the continual-worlds study's). Neither is May's
exact pair: May's modulated agent was `recurrent_ppo_nmn_film_g1_tempceil5.yaml` (FiLM with a
policy-temperature head clipped to [0.5, 5], MC returns), and May's analysis found that the
temperature head moved at every boundary. Today's modulated agent cannot reproduce that
mechanism. A positive result here is therefore about **today's** modulator. Open question Q2 (section 8) is
whether to add May's agent as a third arm.

**From scratch, May's schedule unchanged.** Both agents start from random weights, as in May.

| Stage | World | Episodes (cumulative boundary) | Length |
|---|---|---|---|
| 1 | active | 0 → 1.5 M | 1.5 M |
| 2 | passive | 1.5 M → 3.0 M | 1.5 M |
| 3 | active (first return) | 3.0 M → 3.7 M | 0.7 M |
| 4 | passive | 3.7 M → 4.4 M | 0.7 M |
| 5 | active (second return) | 4.4 M → 5.1 M | 0.7 M |

**Is 1.5 M enough for stage 1 under today's body?** Probably yes, to the same degree it was in
May. May's agents were at 83 % of the 10 M-episode specialist ceiling at 1.5 M. Today's level-05
ordinary agent, from scratch in a **harder** world (thermal on, 0–2 pouncing predators, 1–4
food), averaged **192** steps at 1.0 M, **230** at 1.8 M and **252** at 10 M
([[LEVEL05_BODY_INTERACTIONS]], "Why 2,000,000 episodes"), so about 85–90 % of final at 1.5 M.
This world has no cold, one predator that cannot pounce, and 4 fixed food items. It should be
learned at least as fast. Keeping 1.5 M reproduces May's "stage 1 near but not at plateau"
condition. A longer stage 1 would change the stage-1 : stage-3 ratio that May's forgetting
numbers came from. **Pre-registered fallback:** if the stage-1 competence gate (5.5) fails, the
replication is recorded as inconclusive. The remedy, stated now, is a rerun with stage 1 at
**3.0 M** (boundaries `[3.0M, 4.5M, 5.2M, 5.9M, 6.6M]`) and everything else unchanged. A warm
start from a pre-trained level-05 agent is **not** used: those agents have a 58-wide observation
(thermal on), and a warm start would remove the "learn it from scratch" condition May had.

**Seeds.** 3 per agent (42, 43, 44), 6 runs. A seed is paired across agents only for bookkeeping.
The two agents with the same seed number get different initial weights, so pairs are **not**
matched units. The rules in 5.3 therefore use both a per-pair sign count and a between-seed error.
Three seeds is the project minimum. It is enough here because May's effect (107–132 steps) was
roughly 50 times the level-05 seed SD (about 1.5–2 steps). If the effect has shrunk toward seed noise,
3 seeds will read as "not replicated" rather than falsely positive (5.3).

**Checkpoints** every 100,000 episodes in every stage (May: 50,000 in stages 3–5). Every
boundary is a multiple of 100,000, so the stage-end checkpoint is the first one at or after each
boundary. rPPO keeps all checkpoints (`configs/train/recurrent_ppo.yaml`).

**Fixed across all runs:** 128 parallel environments, perceptual noise off, the rPPO training
defaults, the schedule and stage files below, and the same code commit (recorded at launch).

### 3.5 Known bugs checked (continual / stage rows of the registry)

| Registry row | Relevance | Handling |
|---|---|---|
| **A2**: continual stage swap keeps stage-0 per-tag animal accumulators | a roster-**size** change can crash; tag changes mislabel curves (May was mislabelled: `full` → `TL`) | every stage has the **same roster and tags** (1 `pred`, `rabbit_tl`, `rabbit_br`); stage 0 has the maximum slot count; verified (6.1, V2) |
| **H2**: continual resume ran the wrong stage's world (fixed) | only if a run is resumed | runs start at episode 0; if one must be resumed after a crash, the runner checks the `[RESUME] Stage k:...` rebuild line |
| **B5**: single-config resume pairs restored memory with fresh worlds | single-config path only | not applicable (continual path) |
| Stale continual tests (8-wide vision) | the continual stage-switch and resume paths have no passing regression test | the same five-stage switch path ran cleanly on GPU in continual-worlds Pilot 2 (2026-09-28, both agents); the first `[STAGE]` line of each run is checked at 1.5 M (6.3) |
| Stale nested `training.seed` copy in saved configs | misread hazard | the runner reads the **top-level** `seed:` of each saved config, not `training.seed` |
| Spawn-area-full parks an entity at (0,0) | a crowded quadrant could silently misplace | measured: 0 entities outside their area and 0 stacked, 1,000 resets per world (V5) |
| **New, not in the registry:** patrol clip off-by-one | a quadrant-restricted animal can reach row/column 6 (1-indexed), i.e. a 6 × 6 box | present identically in May's code (`8bd8f10f`, the same `_parse_area` + inclusive `clip`), so the replication **matches** May; handed to `bug-curator` to record (7) |

## 4. Launch Manifest

All rows: `wandb-group` = `continual_worlds`, `wandb-job-type` = `prod`, tag = wandb-name.
Scheme `rppo_cw_mayrep_<agent>_s<seed>`. Node and GPU are assigned by the parent at launch.
Suggested: three 2-GPU mid-tier nodes (RTX 3090 class), one agent pair per node, filling each
node's GPUs before moving to the next.

| Run | Status | Cell | Tag (= wandb-name) | wandb-group | wandb-job-type | Seed | Node | GPU | Launched at | WandB run ID | Log path |
|-----|--------|------|--------------------|-------------|----------------|------|------|-----|-------------|--------------|----------|
| M1 | ready — pending reviews | ordinary | `rppo_cw_mayrep_t1none_s42` | continual_worlds | prod | 42 | — | — | — | — | — |
| M2 | ready — pending reviews | modulated | `rppo_cw_mayrep_t16quad_s42` | continual_worlds | prod | 42 | — | — | — | — | — |
| M3 | ready — pending reviews | ordinary | `rppo_cw_mayrep_t1none_s43` | continual_worlds | prod | 43 | — | — | — | — | — |
| M4 | ready — pending reviews | modulated | `rppo_cw_mayrep_t16quad_s43` | continual_worlds | prod | 43 | — | — | — | — | — |
| M5 | ready — pending reviews | ordinary | `rppo_cw_mayrep_t1none_s44` | continual_worlds | prod | 44 | — | — | — | — | — |
| M6 | ready — pending reviews | modulated | `rppo_cw_mayrep_t16quad_s44` | continual_worlds | prod | 44 | — | — | — | — | — |

Tags are unique here and do not collide with any `rppo_cw_*` tag in [[CONTINUAL_WORLDS]] (the
`mayrep` token appears nowhere else).

### 4.1 Configs to Produce

| Run | Stage dir + schedule | Agent | Starts from | `--episodes` |
|---|---|---|---|---|
| M1, M3, M5 | `configs/continual/continual_worlds/may_replication_stages/` + `configs/continual/continual_worlds/may_replication.yaml` | `nmngaenorm_t1none.yaml` | scratch | none (the schedule's last boundary, 5.1 M, is the budget) |
| M2, M4, M6 | same | `nmngaenorm_t16quad_ALL.yaml` | scratch | none |

Files written by this design:

- `configs/environment/experiment/continual_worlds/may_active_10x10.yaml`: the active world (full lists restated; `extends:` level 05; thermal off).
- `configs/environment/experiment/continual_worlds/may_passive_10x10.yaml`: `extends:` the active world and restates only `entities:`. The predator entry differs in the four keys of 3.2; the rabbits are verbatim.
- `configs/continual/continual_worlds/may_replication.yaml`: boundaries `[1500000, 3000000, 3700000, 4400000, 5100000]`, checkpoints 100,000 in every stage.
- `configs/continual/continual_worlds/may_replication_stages/{01_active,02_passive,03_active,04_passive,05_active}.yaml`: each a one-line `extends:` of its world.

No agent config, no `src/`, no `default.yaml` and no registry value is changed.

### 4.2 Launch commands (for `training-runner`, via `run_command.py`, after the user's go)

`PY=/home/vncuser/miniconda3/envs/grid_world_pain/bin/python`, run from the repo root. In
continual mode `--episodes` is refused.

```bash
# M1 shown; M3/M5 change --seed and the tag; M2/M4/M6 swap in nmngaenorm_t16quad_ALL.yaml and t16quad in the tag.
$PY train.py --configs-dir configs/continual/continual_worlds/may_replication_stages \
  --continual-schedule configs/continual/continual_worlds/may_replication.yaml \
  --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
  --seed 42 --device cuda:0 \
  --tag rppo_cw_mayrep_t1none_s42 --wandb-name rppo_cw_mayrep_t1none_s42 \
  --wandb-group continual_worlds --wandb-job-type prod
```

**Expected start-up lines:** `Continual mode: 5 stages from .../may_replication_stages` with the
five `[0k] 0k_active/passive until_ep=...` rows, then `Continual mode: obs_dim=52, action_dim=6
validated consistent across 5 stages.`, then `Observation Dim: 52 (...)`. For the modulated
arm, also `Neuromodulation: ENABLED (type=FiLM, ... sites=[encoder,rnn,actor,critic] ...,
temperature=off)`. All four were seen in the CPU smoke start (6.1, V4).

**Compute.** 5.1 M episodes per run, about 1.6 billion environment steps. That assumes about
200 steps per episode in the active stages and about 480 in the passive ones, near the
500-step cap as in May. Throughput is taken from the 10 × 10 seed-43 Home legs in
[[CONTINUAL_WORLDS]]: about 0.79 M episodes/h for the ordinary agent and about 0.61 M for the
modulated one, at about 245 steps per episode, i.e. about 190 M and 150 M steps/h. That gives
**about 8–12 h per ordinary run and 11–15 h per modulated run**. May took 9.5 h and 13.3 h.
Six GPUs in parallel means about 15 h wall time, plus node variance.

## 5. Analysis plan (pre-specified)

The measure is survival steps per episode (`Episode/Steps_mean`) over the whole run, read from
WandB episode rows (`Episode/Number`, `Episode/_window_n`, `stage/index`). Rows are weighted by
`Episode/_window_n`, and rows under 1,000 episodes are skipped, as in [[CONTINUAL_WORLDS]] 5.1.
Reward is never used. The analysis reuses
`scripts/analysis/studies/continual_worlds/pilot_readout.py` (`scan` / `Series` / `recovery`,
and its own / common-reference `_vote`, commit `a72eb943`). Its per-stage logic is general: it
reads each run's own schedule and stage folder, treats a `--continual-schedule` run with no
checkpoint as a sequence, and pairs runs by tag with the agent token removed
(`rppo_cw_mayrep_s42`). Two things are missing, which makes this a small `developer`
hand-off (8, Q4), needed before the first switch at 1.5 M episodes:
- It finds runs only through the continual-worlds manifest, whose run ids are numeric. The rows
  here are `M1`–`M6` in this doc.
- It has no three-seed aggregation: the 2-of-3 sign count and the 2 × SE rule of 5.3.

### 5.1 Per-run quantities

For each run, `S_k` is the mean survival over the **last 200,000 episodes of stage k**. The
active world's reference level is `R_A = S_1`.

| Symbol | Definition | May value (mod / ord) |
|---|---|---|
| Return advantage `D_k` (k = 3, 5) | `S_k(mod) − S_k(ord)` within a seed pair; also the difference of the two agents' 3-seed means | +106.9 (k=3), +132.5 (k=5) |
| Forgetting `F_k` (k = 3, 5) | `S_k − S_1` per run (absolute steps; negative = forgot) | −51.9 / −147.7 (k=3); −46.2 / −167.5 (k=5) |
| Forgetting advantage `G_k` | `F_k(mod) − F_k(ord)` (positive favours the modulator) | +95.8, +121.3 |
| Dip, own reference (k = 3, 5) | 1 − (mean survival over the first 20,000 episodes of stage k) / `R_A` (own) | May reported ~equal dips on a different window (200 episodes, min) |
| Dip, common reference | `R_A,common − first-20k mean`, in steps, with `R_A,common` = min(`R_A` ord, `R_A` mod) of the seed pair | — |
| Recovery | episodes **and** environment steps after the switch until the 20,000-episode running mean first reaches 0.9 × `R_A` (own) and 0.9 × `R_A,common`; censored at 700,000 | "mod climbs back within one window; ord plateaus" (qualitative) |
| Second-return change `H` | `S_5 − S_3` per run | +5.75 / −19.8 |
| Stage-1 level `S_1` and passive levels `S_2`, `S_4` | context and gates | 289.5 / 278.3; 485.9 / 487.9; 495.1 / 492.3 |

Also reported for comparison with May's tables: the **May-style tail mean**, the mean over the
last 10 % of each stage's episodes (the window May's analyzer used).

### 5.2 Noise yardstick

With three seeds per agent, noise is measured directly. For each agent and stage, `sd_k` is the
SD of `S_k` across its 3 seeds. The **standard error of a mean difference** is
`SE_k = sqrt(sd_k(ord)²/3 + sd_k(mod)²/3)`. A mean difference is **beyond noise** if
`|mean diff| > 2 × SE_k`. With n = 3 this is a descriptive threshold, not a formal
significance test, which is why it is always combined with the per-pair sign count. For scale,
every difference is also printed next to May's ±4.4-step seed spread and the level-05 seed SD
(1.5 steps).

### 5.3 Verdict rules (locked)

**H-ret, per return k ∈ {3, 5}:** *favourable* if `D_k > 0` in **≥ 2 of 3** seed pairs **and**
the mean difference `> 2 × SE_k`. *Unfavourable* if `D_k < 0` in ≥ 2 of 3 pairs **and** the mean
difference `< −2 × SE_k`. Otherwise *inside noise*.

**H-forget, per return:** the same rule on `G_k`.

| Overall verdict | Condition |
|---|---|
| **Replicated** | H-ret favourable on **both** returns **and** H-forget favourable on **both** returns |
| **Partly replicated** | at least one of the four readings favourable, none unfavourable |
| **Not replicated** | no favourable reading and no unfavourable reading beyond noise |
| **Reversed** | any H-ret or H-forget reading unfavourable (the ordinary agent clearly ahead) |

**H-dip** (predicted equal, as in May): *equal* if, on both switches (into stages 3 and 5), the
mean dip difference is inside 2 × SE under **both** the own and the common reading. A dip
smaller for the modulator beyond noise under both readings is reported as a **new finding
beyond May**, not as a failure of replication.

**H-rec:** per seed pair and switch, the four-reading vote of [[CONTINUAL_WORLDS]] 5.1, with
its two pre-registered scoring choices (3.7.7): a tie is "not counted", and unanimous against
counts against. It is reported as the number of favourable pairs out of 3 per switch.
Secondary: it does not enter the overall verdict, because May's recovery claim was qualitative.

**H-hyper** (secondary): favourable if `H(mod) ≥ 0` and `H(ord) < 0` in ≥ 2 of 3 pairs. It is
reported, but kept out of the overall verdict, because May's own value (+5.75) sat inside its
seed noise.

### 5.4 Comparison with May's numbers

Absolute survival is not comparable: a different body, senses and bushes mean a different
ceiling. The comparison is made on scale-free readings:

| Reading | May | Replication (filled after training) |
|---|---|---|
| Normalised return advantage `mean D_k / mean S_1(ord)` | 38 % (k=3), 48 % (k=5) | |
| Forgetting ratio `mean F_k(mod) / mean F_k(ord)` | 0.35 (k=3), 0.28 (k=5) | |
| Sign of `H` (mod / ord) | + / − | |
| Passive stages near the 500-step cap for both agents | yes (486–495) | |

A replicated effect counts as **May-sized** if its normalised return advantage is at least half
of May's (≥ 19 % at k=3 and ≥ 24 % at k=5). Otherwise it is "replicated in direction, smaller
than May". Both are reported with the absolute numbers next to them.

### 5.5 Gates and descriptive checks

- **Stage-1 competence gate (pre-registered).** Per run: `S_1 ≥ 150` steps (about 60 % of
  today's level-05 Home competence of about 250) **and** mean `Episode/FoodEaten ≥ 1.0` bite
  per episode over the same window. If **2 or more runs of one agent** fail, the whole
  replication is **inconclusive (stage 1 too short)** and the 3.0 M stage-1 fallback (3.4) is
  proposed to the user. A single failing run is reported and kept.
- **Convergence, descriptive.** The rise in the 200,000-episode trailing mean over the last
  300,000 episodes of stage 1. More than 10 % is flagged "stage 1 still climbing" (May was at
  about 83 % of ceiling), because it biases forgetting toward smaller values for both agents.
- **Switch is real.** Survival in stages 2 and 4 is above `S_1` for both agents, as in May. If
  not, the passive world is not easier, which is failure mode 7.4.
- **Causes of death per stage** (`Episode/Term_*` shares), descriptive. May's ordinary agent
  collapsed into starvation on the returns (68–72 %).
- **Temporal evolution (mandatory).** Survival (20,000-episode running mean) against episodes,
  with stage boundaries marked. All 6 runs go on one axis, one colour per agent, plus each
  agent's 3-seed mean. Recovery is also plotted against environment steps. Policy entropy
  (`loss/entropy`, iteration stream, cut by `stage/index`) is shown per stage. For the modulated
  arm, the logged modulator summaries are shown around each boundary: descriptive only.
- **Zero-shot retention: pre-registered, adopted by the user 2026-09-29 (8.1).** The
  full rule is in 5.6.

### 5.6 Zero-shot retention test (pre-registered 2026-09-29; no training)

**What it asks, in plain words.** Freeze each agent at the end of every stage and let it play
the hunting world with no learning at all. How much of its hunting-world survival is left after
a harmless stage, before any retraining can repair it? This separates **forgetting** (what the
harmless stage erased) from **relearning speed** (what the training-curve measures in 5.1 mix
in).

**How.** For every run, after it finishes, run
`scripts/eval/continual_forgetting_matrix.py --run-dir <run> --episodes 2000 --device gpu
--output-prefix results/analysis/continual_worlds/mayrep_forgetting_<tag>`. The driver takes
the stage-end checkpoint of each of the 5 stages. That is the first checkpoint at or after
each boundary, and its saved `stage` field must equal the stage index or the driver stops.
The driver evaluates each checkpoint in both worlds of the run's own saved schedule (`active`,
`passive`; the stage-name prefixes are stripped), using the run's saved stage configs, for
2,000 episodes per cell. Seeds 0–1,999 are used in every cell, so cells are paired. No
`--start-checkpoint` is passed, because the runs start from scratch. Each cell's measure is
mean survival steps with a 95 % CI (about ±5 steps at 2,000 episodes). The driver never reads
reward.

**Pre-registered quantities** (`A_k` = survival of the stage-k-end checkpoint in the active
world):

| Symbol | Definition | Reads |
|---|---|---|
| `Z_2` | `A_2 − A_1` | hunting skill lost during the first harmless stage (1.5 M episodes) |
| `Z_4` | `A_4 − A_3` | hunting skill lost during the second harmless stage (0.7 M) |
| `ZA_j` (j = 2, 4) | `Z_j(mod) − Z_j(ord)` | positive favours the modulator (it lost less) |

**Rule (H-zeroshot, secondary).** For each j, *favourable* if `ZA_j > 0` in **≥ 2 of 3** seed
pairs **and** the mean `ZA_j > 2 × SE` (between-seed SE, as in 5.2). *Unfavourable* is the
mirror case. Otherwise it is *inside noise*. A per-pair difference is also marked "beyond eval
noise" when the two cells' 95 % CIs, combined, do not include 0. H-zeroshot is reported **next
to** the overall verdict of 5.3 and does **not** change it: the verdict stays pinned to May's own
training-curve measures, so the replication can be compared like for like. Descriptive only: the
passive-world column (whether hunting-stage training costs harmless-world survival) and
`A_5 − A_3` (whether the second return is kept better than the first).

**When.** After all six runs finish. It needs only the finished checkpoints and one GPU per run,
at about 10 cells × 2,000 episodes.

## 6. Pre-launch checks

### 6.1 Verified (2026-09-29, read-only except scratch output, project interpreter, CPU)

| # | Check | Result |
|---|---|---|
| V1 | `train._build_continual_schedule` (the trainer's own function, with the trainer's base-config merge order) builds the schedule | pass: 5 stages `01_active … 05_active`; boundaries `[1.5M, 3.0M, 3.7M, 4.4M, 5.1M]`; episode 0 → stage 0, 1,499,999 → 0, 1.5 M → 1, 3.0 M → 2, 3.7 M → 3, 4.4 M → 4 |
| V2 | Every `EnvParams` field (208) compared across stages | stages 3 and 5 identical to stage 1; stages 2 and 4 differ **only** in the predator's spawn / patrol area, detection range and hunt threshold (plus the placement bookkeeping derived from spawn areas: `type_areas`, `type_counts`, `type_entity_map`, `num_types`). Roster identical in every stage: 3 animal slots (1 predator, 2 rabbits), same tags (A2 safe) |
| V3 | Stage 1 vs level 05, every field | no body, interoception, reward or episode field differs; differences are only the scene arrays, thermal fields (off) and noise-table order (noise off in both) |
| V4 | `train.py` itself started on CPU for **both** agents (4 envs, `--no-wandb`, scratch results dir; killed after the first iterations) | pass: `Continual mode: obs_dim=52, action_dim=6 validated consistent across 5 stages` (the trainer's width + action + sensor-fingerprint check); `Observation Dim: 52 (Satiation=1, Interoceptive Nociception=1, Extero Nociception=1, Olfaction=25, Collision=5, Proprioception=6, Visual=13)`; ordinary "Neuromodulation: DISABLED"; modulated "ENABLED (type=FiLM ... sites=[encoder,rnn,actor,critic] ... temperature=off)"; training iterations ran. Nothing written to `results/` or `wandb/` |
| V5 | 1,000 real resets per world | all 8 food/ambusher, 3 animal and 22 obstacle slots active every reset; **0** outside their declared area; **0** stacked entities |
| V6 | 256 envs × 300 random-action steps per world | active predator in hunt mode on 40.8 % of live steps; passive predator on **0.0 %** |
| V7 | Roaming box of quadrant animals | passive predator and top-left rabbit reach rows/cols 0–5 (0-indexed), i.e. a 6 × 6 box; bottom-right rabbit 5–9. Same `_parse_area` + inclusive `clip` in May's code (`8bd8f10f`), so identical to May |

Scripts: scratch only (`validate_mayrep.py`, `behave_mayrep.py` in the session scratchpad); the
numbers above are their printed output.

### 6.2 Before launch

1. `env-config-reviewer` pre-flight on the two worlds, the schedule and the stage folder.
2. `plan-reviewer` on this design.
3. The user's answers to section 8.
4. Live GPU state (diary + `pgrep`, not only `nvidia-smi`) and the NAS mount on each node.

### 6.3 At launch and at the first switch (`training-runner`)

- The start-up lines of 4.2; exactly one PID per tag.
- At about 1.5 M episodes: a `[STAGE] 0:01_active -> 1:02_passive` line and no traceback; the
  stage-1 gate (5.5) is read then. Early reading allowed: if **both** agents are far below 150 at
  1.5 M, the user may stop the runs and relaunch with the 3.0 M fallback, instead of spending
  the remaining 3.6 M episodes.

## 7. Failure-mode catalog (decided in advance)

| # | Outcome | Reading |
|---|---|---|
| 7.1 | NaN / value explosion in a run | that run is invalid; relaunched once from its last good checkpoint (continual resume; check the `[RESUME] Stage k` rebuild line); not evidence |
| 7.2 | A stage switch crashes | run invalid; resume after the fix (Known Bug A2 should not fire, V2) |
| 7.3 | Stage-1 gate fails for ≥ 2 runs of one agent | inconclusive; propose the 3.0 M fallback (3.4) |
| 7.4 | Passive stages not easier than stage 1 for both agents | the switch does not reproduce May's easy / hard contrast under today's body; report; the verdict is still computed but worded "switch weaker than May's" |
| 7.5 | Neither agent drops at harmless → hunting (own dip < 5 % on both switches) | the worlds are not distinct enough under today's body and senses; **null for this design**, not a refutation of May |
| 7.6 | One run of an agent collapses (return < 0.6 × its `R_A` for the whole stage) while its seed-mates do not | reported; verdict computed with and without that seed pair |
| 7.7 | All differences inside noise | "not replicated" under today's settings; May's single-seed result stands as a May-conditions observation only |
| 7.8 | Modulated agent clearly worse on returns | "reversed"; a real finding under today's settings (either a May seed fluke or a consequence of the changed body, senses or agent) |
| 7.9 | Recovery censored (never reaches 0.9 × `R_A` in 700k) for both agents | H-rec reported but not counted for that switch |

## 8. Open questions for the user

| # | Question | Options | Recommendation |
|---|---|---|---|
| Q1 | Bushes: today's refuge (animals cannot enter) or May's permeable bush? | refuge (default) / permeable (`blocks_animals: false` in both worlds, a registry-listed setting, so a change-log line) | **refuge**: it is part of today's recovery system (×25 healing), which you asked to keep |
| Q2 | Add May's own modulated agent (FiLM g1 with the policy-temperature head) as a third arm? It would need a GAE_NORM/current-senses twin of `recurrent_ppo_nmn_film_g1_tempceil5.yaml` | no (default; 6 runs) / yes (+3 runs; new agent config) | **no for now**: the question is whether today's modulator shows the effect; if it does not, the temperature arm is the obvious next step |
| Q3 | Predator and rabbit smell identical (May's "sameProp") or today's Home odours (`[0, .7, .5]` vs `[0, .5, .7]`, which let smell tell them apart)? | identical (default) / Home odours | **identical**: it is what makes May's switch a behaviour-reading problem; with Home odours the passive predator is identifiable by smell and the task changes |
| Q4 | The continual-worlds read-out script computes the per-run readings, but only finds runs listed in the continual-worlds manifest and has no three-seed rule (5); extend it? | `developer` hand-off before 1.5 M / analyzer does it ad hoc | **hand-off**, so the pre-registered own/common readings and the 5.3 rule are computed by the same code |
| Q5 | Run the optional zero-shot retention evaluation (5.5)? | yes / no | yes, it is cheap (5 checkpoints × 2 worlds × 6 runs × 2,000 episodes) |
| Q6 | "temp" in your request: thermal body temperature (dropped here) or May's policy-temperature setting (not present in today's agent)? | — | this design reads it as **thermal**; Q2 covers the other reading |

### 8.1 Decisions (user, 2026-09-29)

*Appended 2026-09-29; the questions above are kept unchanged for the record.*

| # | Decision |
|---|---|
| Q1 | **Bushes stay today's refuge** (animals cannot enter), as designed |
| Q2 | **No third arm** with May's modulated agent (policy-temperature head). Stays 6 runs |
| Q3 | **Predator and rabbits smell identical**, as in May, as designed |
| Q4 | The analysis-script extension (run discovery from this doc's manifest + the three-seed rule of 5.3) goes to a **`developer`**, arranged by the user; needed before the first switch at 1.5 M episodes |
| Q5 | **Yes**, the zero-shot retention test is included and pre-registered in 5.6 (every stage-end checkpoint, frozen, played in the active world; `scripts/eval/continual_forgetting_matrix.py`) |
| Q6 | "temp" meant **body temperature**, so **thermal off stands** (3.3) |

Effect: manifest rows M1–M6 move to "ready, pending reviews" (`env-config-reviewer`
pre-flight + `plan-reviewer`). No config file changes.

## 9. Hand-offs

- `env-config-reviewer`: pre-flight (6.2 item 1).
- `plan-reviewer`: this design (6.2 item 2).
- `bug-curator`: record the new patrol-clip off-by-one (3.5; `src/environment/config_loader.py`
  `_parse_area` returns an exclusive upper bound, and `src/environment/core.py` `_hunt_step` /
  `_wander_step` clip to it inclusively, so a patrol area of `[[1,1],[5,5]]` lets an animal reach
  cell 6). It is not fixed here: fixing it would make this replication **differ** from May.
- `training-runner`: the 6 launches (4.2) after the user's go.
- `developer` (arranged by the user, Q4): extend the read-out script before 1.5 M episodes.
- `experiment-analyzer`: sections 10–11 after training, including the 5.6 zero-shot run, then
  `plan-reviewer` on the verdict, then `pi`.

## 10. Results

*(to be filled after training)*

## 11. Conclusions

*(to be filled after training)*
