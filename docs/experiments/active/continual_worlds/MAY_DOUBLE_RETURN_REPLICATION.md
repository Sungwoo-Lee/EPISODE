---
title: "May double-return replication: does the modulated agent still come back better after the hunter returns, under today's body and senses?"
topic: continual_worlds
status: active
created: 2026-09-29
last_updated: 2026-09-30
phase: continual / replication of the May 2026 probe
wandb_tag: "rppo_cw_mayrep_{t1none,t16quad}_s{42,43,44}"
develop_link: docs/experiments/active/hypervigilance/NMN_CONTINUAL_DOUBLE_RETURN_PROBE.md
---

# May double-return replication, under today's settings

> **Status (2026-09-30): FINISHED AND ANALYSED.** All six runs completed the five stages. The
> pre-registered verdict is **not replicated (an underpowered null)**: the modulated agent was not
> measurably better when the hunter came back. Today's world is too easy to show an effect: in
> 90–97 % of episodes both agents survive to the 500-step limit. Results in §10, conclusions and
> next steps in §11. The status note below is the design-time record and is kept unchanged.

> **Status (2026-09-29): DESIGNED; user decisions taken (8.1). Configs are written and validated
> with the trainer's own loader. Nothing is launched.** Manifest rows M1–M6 are **ready, pending
> reviews**: they still need an `env-config-reviewer` pre-flight, a `plan-reviewer` pass on this
> design, and a GPU assignment.
>
> **Related:** the May probe being replicated: [[NMN_CONTINUAL_DOUBLE_RETURN_PROBE]] ·
> the larger continual study this sits beside, whose analysis rules it borrows: [[CONTINUAL_WORLDS]] ·
> the level-05 world whose body it keeps: [[LEVEL05_BODY_INTERACTIONS]].

> **Revision (pre-data, 2026-09-29).** These edits answer the plan-reviewer's findings (end of
> this doc). They were made while runs M1–M6 were being launched, **before any result existed
> or was looked at**, so they are still pre-registration. Replaced text is ~~struck through~~
> and left in place; new text is marked *[rev 2026-09-29]*. No config, schedule or training
> setting changed. In plain words:
> - **Verdict labels (5.1, 5.3; reviewer M2).** "Forgets less" is not independent of "comes back
>   better": it equals the return lead minus the stage-1 lead. A new **Mixed** verdict covers
>   "some readings for the modulator, some against"; **Reversed** now needs the ordinary agent
>   to be clearly ahead on at least one return.
> - **Which window decides "as large as May's" (5.1, 5.4; M3).** The May-sized comparison uses
>   May's own window, the last 10 % of each stage; the 200,000-episode window is reported next
>   to it. The 5.3 verdict still uses the 200,000-episode window.
> - **Noise floor (5.2; M4).** A difference must beat twice a between-seed error that is never
>   taken below about 3.6 steps (derived from May's seed noise), so a lucky, tiny spread across
>   three seeds cannot make a few-step difference count.
> - **Small fixes.** The logged survival key is `Episode/Steps` (L1); the lower critic learning
>   rate in May is listed as an agent difference (L2); the real May run folders are cited (L4);
>   the seed of a run is read from its stage-0 saved config only (3.5; M1); the collapse check
>   and the two-collapsed-pairs case are defined (7.6); a null inside noise is worded
>   "underpowered null" (7.7; O3).
> - **Still open (not a doc edit):** the zero-shot driver of 5.6 refuses this schedule until
>   the `developer` fix of M1 lands. That blocks only the post-training test, not training.

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
**and** a mean difference larger than twice its between-seed standard error *[rev 2026-09-29:
that error is never taken below a noise floor of about 3.6 steps, 5.2]*. The result is
**not replicated** if the differences have the wrong sign in most pairs or sit inside seed noise.
It is **reversed** if the ordinary agent is clearly ahead *[rev 2026-09-29: on at least one
return; a result with readings on both sides is **mixed**, 5.3]*. Magnitude is compared with May's
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
~~(`results/JAX_RecurrentPPO/20260511-174837_rppo_nmn_cont_dr_mod_s0_r2/models/stage_0*.yaml`),~~
*[rev 2026-09-29: the folder first cited is an aborted launch with no checkpoints. The real May
runs are `results/JAX_RecurrentPPO/20260511-175843_rppo_nmn_cont_dr_mod_s0_r2/` (modulated,
WandB `8eorbxhq`) and `results/JAX_RecurrentPPO/20260511-180151_rppo_nmn_cont_dr_unmod_s0_r2/`
(ordinary, WandB `lrzvg8k6`), files `models/stage_0*.yaml`. All four May folders' saved configs
are byte-identical (plan-reviewer L4), so no value below changes. The config-file header
comments still cite the old folder; they are left alone because the runs were launching.]*
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
mechanism. *[rev 2026-09-29: two further agent differences are shared by **both** arms, so they
are not arm-vs-arm confounds, but they are reasons a non-replication may not be interpretable
as a failure of May's result: returns MC → GAE_NORM, and critic learning rate `lr_critic`
0.0001 (May) → 0.0005 (today).]* A positive result here is therefore about **today's** modulator. Open question Q2 (section 8) is
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
~~The two agents with the same seed number get different initial weights, so pairs are **not**
matched units.~~ *[Corrected 2026-09-30, experiment-designer — the struck sentence was false.]*
The two agents with the same seed number start from **identical** main-network weights: the
modulator is built after the main network, so it does not disturb the random stream, and the
environment stream is shared too. Verified on the seed-42 pair: 27 of 27 main-network parameter
arrays identical, the modulator's 33 arrays the only extra ones
([[ALGORITHMIC_NULL_TODO]], 2026-09-30). Same-seed pairs are therefore matched on their start.
The rules in 5.3 are unchanged: they use both a per-pair sign count and a between-seed error. The
between-seed error ignores the shared start, which can only make it larger than a paired error
when paired agents are positively correlated, so it stays conservative.
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
| Stale nested `training.seed` copy in saved configs | misread hazard | ~~the runner reads the **top-level** `seed:` of each saved config, not `training.seed`~~ *[rev 2026-09-29, plan-reviewer M1]* a run's seed is read **only** from the top-level `seed:` of `models/config.yaml` (= stage 0). The trainer stamps the CLI seed, tag and WandB names into stage 0's config object only, so the saved `stage_01`–`stage_04` files carry the base config's seed (42) whatever `--seed` was: for seeds 43 and 44 they read `seed: 42`. Never read the seed from a later stage file or from `training.seed` |
| Spawn-area-full parks an entity at (0,0) | a crowded quadrant could silently misplace | measured: 0 entities outside their area and 0 stacked, 1,000 resets per world (V5) |
| **New, not in the registry:** patrol clip off-by-one | a quadrant-restricted animal can reach row/column 6 (1-indexed), i.e. a 6 × 6 box | present identically in May's code (`8bd8f10f`, the same `_parse_area` + inclusive `clip`), so the replication **matches** May; handed to `bug-curator` to record (7) |

## 4. Launch Manifest

All rows: `wandb-group` = `continual_worlds`, `wandb-job-type` = `prod`, tag = wandb-name.
Scheme `rppo_cw_mayrep_<agent>_s<seed>`. Node and GPU are assigned by the parent at launch.
Suggested: three 2-GPU mid-tier nodes (RTX 3090 class), one agent pair per node, filling each
node's GPUs before moving to the next.

| Run | Status | Cell | Tag (= wandb-name) | wandb-group | wandb-job-type | Seed | Node | GPU | Launched at | WandB run ID | Log path |
|-----|--------|------|--------------------|-------------|----------------|------|------|-----|-------------|--------------|----------|
| M1 | finished | ordinary | `rppo_cw_mayrep_t1none_s42` | continual_worlds | prod | 42 | 110 | cuda:0 | 2026-09-29T15:36:06 | ftqkqmzb | logs/20260929_153606.log |
| M2 | finished | modulated | `rppo_cw_mayrep_t16quad_s42` | continual_worlds | prod | 42 | 110 | cuda:1 | 2026-09-29T15:36:14 | n7htz71a | logs/20260929_153614.log |
| M3 | finished | ordinary | `rppo_cw_mayrep_t1none_s43` | continual_worlds | prod | 43 | 111 | cuda:0 | 2026-09-29T15:36:23 | 8c5kmmj2 | logs/20260929_153623.log |
| M4 | finished | modulated | `rppo_cw_mayrep_t16quad_s43` | continual_worlds | prod | 43 | 111 | cuda:1 | 2026-09-29T15:36:32 | rfxw1g7x | logs/20260929_153632.log |
| M5 | finished | ordinary | `rppo_cw_mayrep_t1none_s44` | continual_worlds | prod | 44 | 112 | cuda:0 | 2026-09-29T15:36:41 | 0ojcf4d8 | logs/20260929_153641.log |
| M6 | finished | modulated | `rppo_cw_mayrep_t16quad_s44` | continual_worlds | prod | 44 | 112 | cuda:1 | 2026-09-29T15:36:50 | 5er602ge | logs/20260929_153650.log |

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

The measure is survival steps per episode (~~`Episode/Steps_mean`~~ *[rev 2026-09-29: the logged
key is `Episode/Steps`, the per-row mean; plan-reviewer L1]*) over the whole run, read from
WandB episode rows (`Episode/Number`, `Episode/_window_n`, `stage/index`). Rows are weighted by
`Episode/_window_n`, and rows under 1,000 episodes are skipped, as in [[CONTINUAL_WORLDS]] 5.1.
*[note 2026-09-30, plan-reviewer T2 (`docs/reviews/plan_algorithmic_null_tooling.md`, third
review): this sentence does not match the code that computes this study's verdict.
`pilot_readout.Series` (`pilot_readout.py:296-308`) weights each row by the episodes it adds —
the increase in `Episode/Number` since the previous row — and uses `Episode/_window_n` only for
the 1,000-episode skip. Logged rows are overlapping rolling windows, so the two weightings differ.
Recorded here, not changed: the registered rule text above stands as written, and the verdict
will be computed by the code as it is. The algorithmic-null decision rules name the code's
estimator (`row_weight: delta_episode_number`).]*
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
| Forgetting advantage `G_k` | `F_k(mod) − F_k(ord)` (positive favours the modulator). *[rev 2026-09-29, plan-reviewer M2]* Algebraically `G_k = D_k − D_1`: it is the return advantage minus the stage-1 advantage, **not** a reading independent of `D_k`. It is favourable when the modulator's lead on the return exceeds its stage-1 lead | +95.8, +121.3 |
| Dip, own reference (k = 3, 5) | 1 − (mean survival over the first 20,000 episodes of stage k) / `R_A` (own) | May reported ~equal dips on a different window (200 episodes, min) |
| Dip, common reference | `R_A,common − first-20k mean`, in steps, with `R_A,common` = min(`R_A` ord, `R_A` mod) of the seed pair | — |
| Recovery | episodes **and** environment steps after the switch until the 20,000-episode running mean first reaches 0.9 × `R_A` (own) and 0.9 × `R_A,common`; censored at 700,000 | "mod climbs back within one window; ord plateaus" (qualitative) |
| Second-return change `H` | `S_5 − S_3` per run | +5.75 / −19.8 |
| Stage-1 level `S_1` and passive levels `S_2`, `S_4` | context and gates | 289.5 / 278.3; 485.9 / 487.9; 495.1 / 492.3 |

Also reported for comparison with May's tables: the **May-style tail mean**, the mean over the
last 10 % of each stage's episodes (the window May's analyzer used). *[rev 2026-09-29,
plan-reviewer M3]* It is written `T_k` (150,000 episodes in stage 1, 70,000 in stages 3 and 5);
`D_k`, `F_k` and `S_1` recomputed on `T_k` instead of `S_k` carry the suffix "(tail)". `T_k` is
what decides the May comparison of 5.4; `S_k` decides the verdict of 5.3.

### 5.2 Noise yardstick

With three seeds per agent, noise is measured directly. For each agent and stage, `sd_k` is the
SD of `S_k` across its 3 seeds. The **standard error of a mean difference** is
`SE_k = sqrt(sd_k(ord)²/3 + sd_k(mod)²/3)`. A mean difference is **beyond noise** if
`|mean diff| > 2 × SE_k`. With n = 3 this is a descriptive threshold, not a formal
significance test, which is why it is always combined with the per-pair sign count. For scale,
every difference is also printed next to May's ±4.4-step seed spread and the level-05 seed SD
(1.5 steps).

*[rev 2026-09-29, plan-reviewer M4]* **Noise floor.** An SD estimated from three values is
itself very uncertain (roughly ±50 %), so a lucky, small spread could make a few-step difference
look "beyond noise". The SE used in every `2 × SE` test on a quantity in steps is therefore
floored at a value derived from May's measured seed noise, σ = 4.4 steps (the ±4.4-step
seed-to-seed noise from the May temperature-clip rerun, read here as a per-agent SD):

$$
\text{SE}_{\text{floor}} = \sqrt{\frac{\sigma^2}{3} + \frac{\sigma^2}{3}} = \sigma\sqrt{2/3} = 4.4 \times 0.816 \approx 3.6 \text{ steps}
$$

That is the SE of a difference between two 3-seed means when each agent's seeds scatter with SD
4.4. For a difference of **changes** between two stage levels (`G_k`, and `ZA_j` of 5.6), each
per-run value is itself a difference of two levels, so its variance doubles:
`4.4 × sqrt(4/3) ≈ 5.1` steps. The rule is `SE_used = max(SE_k, floor)` with floor 3.6 for
`D_k` and the common-reference dip, 5.1 for `G_k` and `ZA_j`. The own-reference dip is a
fraction and gets no floor. In effect, no step-valued difference smaller than about 7 steps
(10 steps for `G_k`, `ZA_j`) can ever count as favourable or unfavourable.

**Why a floor and not a separate minimum effect (e.g. 10 steps).** The floor comes from a
measured quantity; a minimum effect would be a second, freely chosen constant. The floor already
works as a minimum effect (2 × 3.6 ≈ 7 steps; 2 × 5.1 ≈ 10 steps). The floor is conservative
here: May's world was harder, and today's level-05 seed SD is 1.5 steps, so real SEs are
expected at or below it. The floor does **not** fix the opposite case, an unluckily large SD
hiding a real effect. That case is covered by the "underpowered null" wording of 7.7.

### 5.3 Verdict rules (locked)

**H-ret, per return k ∈ {3, 5}:** *favourable* if `D_k > 0` in **≥ 2 of 3** seed pairs **and**
the mean difference `> 2 × SE_k`. *Unfavourable* if `D_k < 0` in ≥ 2 of 3 pairs **and** the mean
difference `< −2 × SE_k`. Otherwise *inside noise*. *[rev 2026-09-29: `SE_k` here and below is
the floored SE of 5.2.]*

**H-forget, per return:** the same rule on `G_k`. *[rev 2026-09-29: recall `G_k = D_k − D_1`
(5.1). An unfavourable H-forget with a favourable H-ret means "ahead on the return, but by less
than in stage 1", not "the ordinary agent is ahead".]*

| Overall verdict | Condition |
|---|---|
| **Replicated** | H-ret favourable on **both** returns **and** H-forget favourable on **both** returns |
| **Partly replicated** | at least one of the four readings favourable, none unfavourable |
| ~~**Not replicated**~~ | ~~no favourable reading and no unfavourable reading beyond noise~~ |
| ~~**Reversed**~~ | ~~any H-ret or H-forget reading unfavourable (the ordinary agent clearly ahead)~~ |
| **Mixed** *[rev 2026-09-29]* | at least one of the four readings favourable **and** at least one unfavourable (e.g. modulator ahead on both returns, but by less than its stage-1 lead, so H-forget unfavourable) |
| **Reversed** *[rev 2026-09-29]* | no reading favourable **and** H-ret unfavourable on at least one return (the ordinary agent clearly ahead on a return) |
| **Not replicated** *[rev 2026-09-29]* | no reading favourable **and** H-ret unfavourable on neither return. An unfavourable H-forget alone is reported beside it as "the modulator lost its stage-1 lead". Worded per 7.7 when every difference is inside noise |

*[rev 2026-09-29]* The rows are checked in the order Replicated, Partly replicated, Mixed,
Reversed, Not replicated; the five are mutually exclusive and cover every outcome.

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

*[rev 2026-09-29, plan-reviewer M3]* **Which window decides.** Every reading in this table,
and the May-sized test, is computed on the **May-style tail `T_k`** (last 10 % of each stage,
5.1), because that is the window May's own numbers came from. Reason: on a return stage where
one agent is still recovering, the wider 200,000-episode window pulls that agent's level down,
so "not May-sized" could come from the window rather than the effect. The same readings on the
200,000-episode `S_k` are reported in a second column for reference and do not decide
anything here. The overall verdict of 5.3 stays on `S_k`.

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
pairs **and** the mean `ZA_j > 2 × SE` (between-seed SE, as in 5.2; *[rev 2026-09-29] floored
at 5.1 steps*). *Unfavourable* is the
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
| 7.6 | One run of an agent collapses (return < 0.6 × its `R_A` for the whole stage) while its seed-mates do not | reported; verdict computed with and without that seed pair. *[rev 2026-09-29]* **Collapse, defined:** on return stage k, the **best** 20,000-episode running mean anywhere in the stage stays below 0.6 × that run's own `R_A` (= `S_1`); read only for completed stages. **Scope:** applies only when exactly one run of an agent collapses on that return. If 2 or 3 runs of the **same** agent collapse, collapse is that agent's behaviour (May's ordinary agent collapsed into starvation): it is kept as data and no without-version is computed. **Without-version:** the 5.3 rule on the remaining pairs; with 2 pairs left, favourable needs the sign in **both** pairs and the mean difference beyond 2 × the floored SE. **Two collapsed pairs** (one ordinary and one modulated run collapse, in different seed pairs): only one pair remains, so no without-version verdict is computed; that pair's signs are reported descriptively. **Headline:** always the all-3-pair verdict. It is marked "fragile (rests on collapsed runs)" if the without-version gives a different verdict, or if two pairs contain a collapsed run |
| 7.7 | All differences inside noise | ~~"not replicated" under today's settings; May's single-seed result stands as a May-conditions observation only~~ *[rev 2026-09-29, plan-reviewer O3]* verdict label "Not replicated" (5.3), worded as an **underpowered null**: three seeds cannot tell an effect of this size from seed noise under today's settings. It is **not** evidence that the effect is absent. A real effect of 15–30 steps, far smaller than May's 107–132, could sit here. May's single-seed result stands as a May-conditions observation only. A more-seeds follow-up is the named next step, not a verdict |
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

*Written 2026-09-30 by `experiment-analyzer` (plan `tmp/20260930_continual_analysis_plan_v2.md`,
step 7). Order: the registered verdict first, then the ceiling label, then the post-data exploratory
readings. Nothing in sections 1–9 was changed to write this.*

### 10.0 Verdict in plain words

> **What May claimed.** In May 2026, one training run per agent suggested that the modulated agent
> (the one with a small side network that rescales the main network, loosely like a neuromodulator)
> copes much better when a hunting predator returns after a harmless phase: about **107 and 132
> more survival steps per episode** on the two returns, and about 70 % less loss of what it had
> learned.
>
> **What we found.** Three seeds per agent, today's body and senses, May's schedule. The modulated
> agent was ahead by **1.5 steps** on each return (out of about 470). That is far inside the
> pre-registered noise band (a difference had to exceed about 7 steps). It lost no less than the
> ordinary agent (−0.3 steps). Both agents dipped by the same amount when the hunter came back
> (7–9 %) and recovered within the first measurement window. **Verdict: not replicated, worded as
> an underpowered null.** Three seeds could not separate an effect of this size from seed-to-seed
> noise. It does **not** show that May's effect is absent.
>
> **Why the null says little about May's effect size.** Today's world is too easy. Bushes are now
> refuges the predator cannot enter, injuries heal 25 times faster there, and smell now carries
> direction. So even the *hunting* stages end with **90–93 % of episodes at the 500-step limit**
> (96–97 % in the harmless stages). The ordinary agent already averaged about 469 steps on the
> returns, so no agent could have beaten it by more than about 31 steps. May's effect, measured
> the same way, would need about 177. The survival test had no room to show it. One reading does
> have room: the frozen-agent retention test (10.5). Frozen at the end of a harmless stage, agents
> reach the limit in only 29–48 % of hunting-world episodes. That test also shows no modulator
> advantage (both lose about 140 steps). It is a different measure from May's, so it narrows the
> picture without settling it.
>
> **Two hints worth a proper test (exploratory, chosen after seeing the data; not findings).**
> (1) In every hunting stage, **fewer modulated-agent episodes ended in death**, in all three seed
> pairs: 0.5 to 0.8 percentage points fewer, out of about 7–10 %. The same edge is present in
> stage 1, before any switch, so if real it is a general edge in the hunting world, not May's
> "comes back better". (2) **Learning from scratch in stage 1 was faster for the modulated agent in
> all three seeds.** It averaged 21 steps more over the first 100,000 episodes and 44 more over the
> first 300,000. At episode 200,000 its level was about 100 steps higher. The parallel study "What
> Both Agents Compute" had listed learning speed as never measured with seeds. Both hints need a
> pre-registered test before anyone may call them findings.

### 10.1 Registered verdict (rules of 5.3)

Survival is the mean over the last 200,000 episodes of each stage (`S_k`). Differences are
modulated minus ordinary, per seed pair (42, 43, 44). The SE is the between-seed SE with the
pre-registered floor (5.2).

| Reading | Stage | Ordinary mean | Modulated mean | Per-pair differences (s42, s43, s44) | Mean diff | SE used (raw) | 2 × SE | Rule result |
|---|---|---|---|---|---|---|---|---|
| Better return (H-ret, `D_3`) | 3, first return | 468.6 | 470.2 | +2.6, −0.4, +2.4 (2 of 3 > 0) | **+1.5** | 3.6 (0.9) | 7.2 | inside noise |
| Better return (H-ret, `D_5`) | 5, second return | 470.9 | 472.3 | +2.6, +0.5, +1.3 (3 of 3 > 0) | **+1.5** | 3.6 (0.7) | 7.2 | inside noise |
| Less forgetting (H-forget, `G_3`) | 3 | `F_3` +3.7 | `F_3` +3.4 | +0.6, −0.4, −1.0 (1 of 3 > 0) | **−0.3** | 5.1 (0.6) | 10.2 | inside noise |
| Less forgetting (H-forget, `G_5`) | 5 | `F_5` +5.9 | `F_5` +5.6 | +0.6, +0.5, −2.2 (2 of 3 > 0) | **−0.3** | 5.1 (0.7) | 10.2 | inside noise |

**Overall (5.3): not replicated.** No reading is favourable, and neither return is unfavourable.
Every difference is inside noise, so per 7.7 the verdict is worded as an **underpowered null**. All
four readings used the floor: the raw between-seed SEs (0.6–0.9 steps) were smaller than it. The
verdict is not fragile: no run collapsed (7.6).

Note the forgetting values are **positive**. On the training curve both agents did **better** on
each return than at the end of stage 1 (+3 to +6 steps). The 200,000-episode window sees no
forgetting at all to compare.

**Per-run levels** (`S_k`, steps; `F_k = S_k − S_1`; `H = S_5 − S_3`; `T` = May-style tail, last 10 %
of the stage):

| Run | Agent | Seed | S1 | S2 (harmless) | S3 (return 1) | S4 (harmless) | S5 (return 2) | F3 | F5 | H | T1 / T3 / T5 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| M1 | ordinary | 42 | 465.4 | 485.4 | 468.9 | 486.4 | 471.0 | +3.5 | +5.6 | +2.2 | 465.8 / 469.4 / 471.4 |
| M2 | modulated | 42 | 467.4 | 484.6 | 471.4 | 485.1 | 473.6 | +4.1 | +6.2 | +2.2 | 467.4 / 471.2 / 474.0 |
| M3 | ordinary | 43 | 465.4 | 484.7 | 469.6 | 485.4 | 470.8 | +4.2 | +5.4 | +1.2 | 466.1 / 470.3 / 470.8 |
| M4 | modulated | 43 | 465.4 | 481.8 | 469.2 | 477.7 | 471.3 | +3.9 | +5.9 | +2.0 | 464.7 / 469.6 / 470.8 |
| M5 | ordinary | 44 | 464.1 | 484.5 | 467.4 | 484.1 | 470.8 | +3.3 | +6.7 | +3.4 | 464.2 / 466.9 / 471.0 |
| M6 | modulated | 44 | 467.6 | 485.3 | 469.8 | 485.0 | 472.1 | +2.3 | +4.6 | +2.3 | 467.5 / 469.6 / 472.8 |

### 10.2 Secondary registered readings and failure-mode checks

| Reading | Result | Detail |
|---|---|---|
| Equal dip (H-dip, predicted null) | **equal**, as May | Own-reference dip on return 1: ordinary 7.1 %, modulated 8.7 % (diff +1.6 points, 2 × SE 3.0). Return 2: 3.6 % vs 5.0 % (diff +1.3, 2 × SE 1.8). Common-reference dips 32.8 vs 38.6 steps (diff +5.9, 2 × SE 15.3) and 16.9 vs 21.5 (diff +4.5, 2 × SE 10.3). Numerically the modulator dips slightly **more**, but inside noise on all four readings |
| Faster recovery (H-rec) | **0 of 3** favourable pairs on both returns | Return 1: s42 not counted (tie), s43 unfavourable, s44 not counted. Return 2: all three not counted. Every run reached 90 % of its stage-1 level in the **first** 20,000-episode window after the switch (one exception: M4 on return 1, 24,000), so the logging grid cannot separate the agents; ties are "not counted" (5.3) |
| Second return at least as good (H-hyper) | **not favourable** (0 of 3 pairs) | `H` is positive for **both** agents in every run (+1.2 to +3.4). The ordinary agent never declines, so May's pattern (modulated +, ordinary −) cannot occur |
| Stage-1 competence gate (5.5, 7.3) | **pass**, all 6 runs | `S_1` 464–468 (threshold 150); about 90 bites per episode (threshold 1). No run still climbing (rise over the last 300k: +0.3 to +0.7 %) |
| Switch is real (7.4) | **yes** | Harmless stages 482–486 vs hunting stages 464–473, for both agents |
| No drop at the switch (7.5) | **did not fire** | Mean own dip into return 1 is 7.1 % / 8.7 %, above the 5 % line (return 2: 3.6 % / 5.0 %) |
| Collapse (7.6) | **none** | No run's best 20k running mean on a return fell below 0.6 × its `S_1` |

### 10.3 Comparison with May's numbers (5.4)

Computed on May's own window, the last 10 % of each stage (decides, per 5.4). The 200,000-episode
values are in brackets for reference.

| Reading | May | Replication |
|---|---|---|
| Normalised return advantage `mean D_k / mean S_1(ord)` | 38 % (k=3), 48 % (k=5) | **+0.3 %** (k=3; [+0.3 %]), **+0.3 %** (k=5; [+0.3 %]) — about 1/100 of May's; the May-sized line was 19 % / 24 % |
| Forgetting ratio `mean F_k(mod) / mean F_k(ord)` | 0.35 (k=3), 0.28 (k=5) | 1.02 (k=3; [0.93]), 1.04 (k=5; [0.94]). Neither agent forgot on this measure (both `F_k` > 0), so the ratio has no meaning here |
| Sign of `H` (mod / ord) | + / − | + / + (tail means +2.4 / +2.2) |
| Passive stages near the 500-step cap, both agents | yes (486–495) | yes: tail means 484.5 / 484.2 (stage 2), 484.9 / 484.4 (stage 4) |
| Stage-1 level `S_1` (context) | 289.5 (mod) / 278.3 (ord) | 466.8 / 465.0 |

"May-sized" is n/a because the result did not replicate. The last row shows the key difference.
May's hunting world left the agents about 210 steps below the cap. Today's leaves them about 35
below. The largest normalised advantage today's hunting stage allows is (500 − 469) / 465 ≈ 7 %,
below the 19 % May-sized line. **The May-sized comparison could not have been met in this world,
whatever the modulator did.**

### 10.4 Ceiling check (read-only label, post-data; plan step 4)

Share of episodes that reached the 500-step limit (`Episode/Term_MaxSteps`) over the last 200,000
episodes of each stage. A stage is labelled **ceiling-limited** at ≥ 80 %. This label was chosen
after the data were seen. It changes no rule. It says how much a survival difference *could* show.

| Run | Stage 1 | Stage 2 | Stage 3 | Stage 4 | Stage 5 |
|---|---|---|---|---|---|
| M1 ordinary s42 | 90.5 % | 96.7 % | 91.7 % | 97.0 % | 92.6 % |
| M2 modulated s42 | 91.3 % | 96.6 % | 92.6 % | 96.7 % | 93.4 % |
| M3 ordinary s43 | 90.4 % | 96.6 % | 91.9 % | 96.8 % | 92.5 % |
| M4 modulated s43 | 90.9 % | 95.9 % | 91.9 % | 95.2 % | 92.9 % |
| M5 ordinary s44 | 90.2 % | 96.5 % | 91.5 % | 96.5 % | 92.5 % |
| M6 modulated s44 | 91.5 % | 96.6 % | 92.2 % | 96.7 % | 93.0 % |

**Every stage of every run is ceiling-limited**, so every training-curve survival reading above
carries that label. This agrees with the parallel study "What Both Agents Compute"
(`docs/experiments/active/modulator_clues/`, page `algorithmic_null.html`). It read the same six
runs at the end of training and found +1.46 steps (floored SE 3.6), with about 94 % of episodes at
the cap. Our registered `D_5` (+1.46 on the 200k window) is the same number.

### 10.5 Zero-shot retention test (5.6, registered secondary; reported next to the verdict, does not change it)

Each stage-end checkpoint was frozen and played for 2,000 episodes in each world. `A_k` is its
mean survival in the hunting world. Registered analysis: greedy actions. The sampled-action run is
a robustness check. Source: `results/analysis/continual_worlds/retention_mayrep_readout.json`
(commit `16de3d1a`).

Hunting-world survival of the frozen checkpoints (greedy; share of episodes at the cap in brackets):

| Run | A_1 (end st. 1) | A_2 (after harmless 1) | A_3 (end return 1) | A_4 (after harmless 2) | A_5 (end return 2) | Z_2 = A_2 − A_1 | Z_4 = A_4 − A_3 |
|---|---|---|---|---|---|---|---|
| ordinary s42 | 473.0 [93] | 340.5 [37] | 476.1 [93] | 355.4 [44] | 478.4 [95] | −132.5 | −120.7 |
| modulated s42 | 471.9 [92] | 334.6 [37] | 477.6 [94] | 333.0 [37] | 476.8 [94] | −137.3 | −144.6 |
| ordinary s43 | 468.6 [91] | 311.0 [30] | 471.5 [92] | 307.1 [29] | 476.8 [94] | −157.6 | −164.4 |
| modulated s43 | 472.1 [92] | 321.1 [35] | 473.9 [93] | 327.5 [37] | 475.6 [94] | −151.0 | −146.4 |
| ordinary s44 | 471.1 [91] | 327.2 [38] | 472.8 [93] | 333.0 [36] | 477.0 [94] | −143.9 | −139.8 |
| modulated s44 | 468.5 [92] | 331.0 [41] | 470.6 [92] | 366.6 [48] | 476.4 [94] | −137.5 | −104.0 |

| Reading | Per pair (s42, s43, s44) | Mean `ZA_j` | SE used | Rule result (greedy) | Sampled actions |
|---|---|---|---|---|---|
| `ZA_2` (lost less in harmless stage 1) | −4.8, +6.6, +6.4 | +2.7 | 8.6 | inside noise | +6.5 (SE 6.9), inside noise |
| `ZA_4` (lost less in harmless stage 2) | −23.9\*, +18.0\*, +35.9\* | +10.0 | 18.8 | inside noise | +9.7 (SE 22.2), inside noise |

\* The pair's difference is beyond evaluation noise on its own (combined 95 % CIs exclude 0).

**Reading.** Both agents lose about **140 hunting-world steps** per harmless stage when frozen:
mean `Z_2` −144.7 (ordinary) vs −141.9 (modulated), mean `Z_4` −141.6 vs −131.7. That is a
forgetting ratio of 0.98 and 0.93, against May's 0.35 / 0.28 on its training curve. On the
second harmless stage the three pairs each differ for real, but **in opposite directions**: two
favour the modulator, one (s42) the ordinary agent. So the second-stage difference depends on the
seed, not the agent. The harmless-world column is 476–491 for every checkpoint: training on the
hunting world does not cost harmless-world survival.

**Why this test matters for the ceiling argument.** The frozen checkpoints after a harmless stage
reach the cap in only **29–48 %** of hunting-world episodes, so `Z_2` and `Z_4` have room to
differ. Read post hoc, the plausible range of the mean `ZA_4` reaches about +48 steps
(mean + 2 × SE), and that of `ZA_2` about +20. A May-sized forgetting advantage on this scale
(65–72 % less of a ~143-step loss, roughly 90–100 steps) would lie well outside both. **Caveat:**
this is a different measure from May's. May measured forgetting on the training curve, where
learning continues, not on frozen agents. So it does not refute May. It does mean the null is not
*only* a ceiling artefact: where there was room, forgetting looked the same for both agents.

**The training curve hides forgetting almost entirely.** Frozen agents lose about 140 steps. On
the training curve, the first 20,000 episodes of a return average only 17–39 steps below the
stage-1 level (10.6), and the 200,000-episode window shows none (`F_k` > 0). The agents relearn
the hunting world within about the first 20,000 episodes (about 9 million steps), faster than the
training-curve measures of 5.1 can resolve.

### 10.6 Temporal evolution

Survival, 20,000-episode window ending at the point shown. Agent mean of 3 seeds, per-seed values
in brackets (s42, s43, s44). Source: `tmp/20260930_mayrep_temporal.json`.

**Stage 1 (hunting world, from scratch).**

| Episodes into stage | Ordinary | Modulated |
|---|---|---|
| 20k | 29.4 (28.6, 32.4, 27.1) | 38.0 (37.0, 34.4, 42.6) |
| 100k | 135.5 (154.6, 113.0, 139.0) | 194.2 (176.0, 222.6, 184.0) |
| 200k | 267.2 (273.8, 247.7, 280.0) | 369.2 (318.6, 402.3, 386.7) |
| 300k | 402.5 (436.4, 399.2, 372.0) | 425.0 (424.1, 424.2, 426.6) |
| 500k | 443.5 (451.0, 444.6, 434.9) | 453.9 (456.3, 451.3, 454.1) |
| 1.0M | 461.6 (460.6, 462.4, 461.9) | 464.1 (463.6, 462.9, 465.7) |
| end (1.5M) | 466.1 (467.9, 466.9, 463.6) | 468.1 (468.8, 467.9, 467.7) |

Shape: a fast rise to about 400 in the first 300,000 episodes, then a slow approach to the cap.
The modulated agent leads during the rise. By about 500,000 episodes both are within about 10
steps of each other, and from 1.0 M the gap is inside the ceiling-compressed noise. The seed-42 pair
reverses at 300k (436.4 vs 424.1), so the lead is not uniform along the curve.

**Returns (hunting world after a harmless stage).**

| Episodes into stage | Return 1 ordinary | Return 1 modulated | Return 2 ordinary | Return 2 modulated |
|---|---|---|---|---|
| 20k | 432.2 (434.4, 431.0, 431.2) | 426.4 (437.0, 411.9, 430.2) | 448.0 (449.1, 449.1, 445.9) | 443.5 (442.2, 436.0, 452.3) |
| 100k | 463.6 | 462.0 | 467.3 | 467.3 |
| 300k | 467.0 | 467.5 | 470.3 | 469.9 |
| end (700k) | 468.8 (470.0, 470.3, 466.0) | 470.0 (470.1, 470.0, 469.9) | 471.4 (472.3, 471.7, 470.3) | 471.7 (473.7, 469.4, 472.0) |

Shape: a small drop in the first window, back within about 5 steps of the final level by 100,000
episodes, then flat against the cap. Return 2 dips about half as much as return 1 for both agents.
No agent ever plateaus below the other on a return, which is where May's effect lived. Harmless
stages sit flat at 482–487 from the first window. One exception: modulated seed 43 slips to
475.8 in the last window of stage 2 and to 482.4 at the end of stage 4 (visible in its lower
`S_2`, `S_4` and in its frozen harmless-world value of 476.5).

**Causes of death** (last 200k, share of all episodes; agent ranges over seeds):

| Stage | Ordinary: injury / starvation | Modulated: injury / starvation |
|---|---|---|
| 1 hunting | 3.5–3.7 % / 5.7–6.2 % | 3.3–3.5 % / 5.0–5.6 % |
| 2 harmless | 1.0–1.2 % / 2.2–2.3 % | 0.9–1.3 % / 2.5–2.8 % |
| 3 return 1 | 3.2–3.7 % / 4.4–5.4 % | 2.9–3.1 % / 4.3–5.2 % |
| 4 harmless | 0.9–1.1 % / 2.1–2.5 % | 0.8–1.1 % / 2.3–3.8 % |
| 5 return 2 | 2.9–3.5 % / 3.9–4.6 % | 2.8–3.0 % / 3.8–4.3 % |

No over-eating and no thermal deaths. Starvation is the larger cause in every stage, but only
about 5 % of episodes. May's ordinary agent's collapse into starvation on the returns (68–72 %) has
no counterpart. Both agents eat about 90–96 bites per episode.

Not produced here: the 5.5 plots (all six runs on one axis, recovery against environment steps,
policy entropy per stage, modulator summaries around each boundary). The tables above stand in
for the survival curve. The plots belong on the planned results page (plan step 10).

### 10.7 Exploratory, post-data readings (no verdict)

**Label.** These outcomes were chosen on 2026-09-30, **after** the survival results were seen, to
find signals that the cap does not hide (plan step 5). They use the 5.2 seed-pair aggregation with
**no** noise floor. About 20 such comparisons were printed (death rate × 5 stages, two
early-learning areas × 4 stages, recovery × 4 stages, plus stage 1). A few will clear 2 × SE by
chance, so none of this is a finding. Each item is a hypothesis for a pre-registered test.

**E1 — Death rate per episode** (1 − share at cap, last 200k), modulated minus ordinary:

| Stage | Ordinary | Modulated | Per pair (s42, s43, s44), points | Mean diff ± SE | Favours |
|---|---|---|---|---|---|
| 1 hunting | 9.6 % | 8.8 % | −0.74, −0.47, −1.26 | −0.8 ± 0.2 | modulated, all 3 pairs, > 2 SE |
| 2 harmless | 3.4 % | 3.6 % | +0.13, +0.63, −0.06 | +0.2 ± 0.2 | ordinary, inside noise |
| 3 return 1 | 8.3 % | 7.8 % | −0.86, −0.02, −0.72 | −0.5 ± 0.2 | modulated, all 3 pairs, > 2 SE |
| 4 harmless | 3.3 % | 3.8 % | +0.28, +1.61, −0.27 | +0.5 ± 0.5 | ordinary, inside noise |
| 5 return 2 | 7.5 % | 6.9 % | −0.80, −0.41, −0.50 | −0.6 ± 0.1 | modulated, all 3 pairs, > 2 SE |

Reading: in the hunting world the modulated agent dies in about 6–9 % fewer episodes, relative to
the ordinary agent's rate, consistently across pairs. Three cautions:
- This is the same data as the survival mean, viewed as a proportion. It matches the small, same-sign
  `D_k` (+1.5 steps). It is not an independent confirmation.
- The edge is as large in **stage 1** as on the returns (`D_1` per pair: +2.0, 0.0, +3.5). So it is
  not May's "comes back better" effect, and the registered forgetting readings are null.
- Same-seed agents start from identical main-network weights (3.4), so pair-to-pair consistency
  partly reflects a shared start.

**E2 — Learning speed from scratch (stage 1).**

| Measure | Ordinary (s42, s43, s44) | Modulated (s42, s43, s44) | Per pair diff | Mean diff (SE) |
|---|---|---|---|---|
| Mean survival over the first 100k episodes | 84.1, 80.1, 82.2 | 100.5, 109.2, 99.8 | +16.5, +29.1, +17.6 | **+21.0** (3.2) |
| Mean survival over the first 300k episodes | 233.1, 205.1, 216.7 | 255.6, 278.3, 254.2 | +22.5, +73.2, +37.4 | **+44.4** (11.3) |
| 20k-window level at 200k episodes | 273.8, 247.7, 280.0 | 318.6, 402.3, 386.7 | +44.8, +154.6, +106.7 | **+102.0** (27.5) |
| Episodes to reach 90 % of own final level | 260k, 360k, 348k | 280k, 292k, 288k | +20k, −68k, −60k | 2 of 3 faster |

Reading: the modulated agent's early climb is faster in all three pairs on the area measures, by
about 25 % over the first 100,000 episodes. The time-to-threshold measure agrees in two pairs of
three: s42's modulated agent got there 20,000 episodes later. This is a learning-speed reading
**far from the cap**, where survival has room. The parallel study notes that "FiLM's advantage in
RL is mostly learning speed, yet the modulated agent does not learn faster"
(`ALGORITHMIC_NULL_TODO.md`, "Measure when the modulator wakes up"). Its results page says learning
speed "has not been measured with seeds" (its candidate 4). This is the first three-seed look, and
it points the other way. It is still one post-hoc look at one world.

**E3 — Relearning speed after a switch (stages 2–5).** Inside noise throughout. The largest mean
difference in survival over the first 100k episodes after a switch is −1.9 steps (return 1); over
the first 300k it is −0.8. The only reading beyond 2 × SE is the common-reference recovery into
harmless stage 2 (−21.7 episodes of ~20,000, all 3 pairs). It is a logging-grid effect, not a
behaviour. After the first stage, learning-speed differences are at most 1.9 steps, well inside
the ceiling.

## 11. Conclusions

### 11.1 Summary

1. **Registered verdict: not replicated, an underpowered null (5.3, 7.7).** On both returns of the
   hunter the modulated agent was ahead by 1.5 steps (floor-based noise band ±7.2). It forgot no
   less (−0.3 steps, band ±10.2). The dip was equal, recovery was a tie at the logging resolution,
   and the second return was no better. No failure mode fired: the stage-1 gate passed, the
   switch was real, both agents dropped at the switch, and nothing collapsed.
2. **The world, not the agent, limits what this can say.** Every stage of every run is 90–97 %
   capped. May's hunting world left agents at about 280 steps. Today's leaves them at about 466,
   so a May-sized advantage (38–48 % of stage-1 survival) could not have been measured. This
   matches the parallel study's end-of-training reading of the same runs (+1.46 steps, ~94 %
   capped).
3. **Where there was room, there was still no May-like effect.** The frozen-agent retention test
   is not at the ceiling after a harmless stage (29–48 % capped). It shows both agents losing
   about 140 hunting-world steps per harmless stage, with no consistent difference. The one set of
   individually real pair differences (second harmless stage) splits 2 to 1 in sign. That is a
   different measure from May's training-curve forgetting, so it bounds rather than refutes May.
4. **Two exploratory hints** (post-data, not findings): a lower death rate for the modulated agent
   in every hunting stage (all 3 pairs, including stage 1), and faster learning from scratch in
   stage 1 (all 3 pairs on area measures; 2 of 3 on time to threshold).

Answer to the question of section 1: **under today's body, senses and agents, the modulated agent
did not come back measurably better after the hunter returned.** But this world could only have
shown a much smaller effect than May's, so the answer is "not shown here", not "not there".
May's single-seed result stands as a May-conditions observation only. Per O2, this also concerns
**today's** modulator (no policy-temperature head), not May's.

### 11.2 Caveats

- **Ceiling.** Every training-curve reading is ceiling-limited (10.4). The noise floor makes it
  worse: the largest difference the world allows (~31 steps) is only about 4 times the smallest
  one the rule can count (~7).
- **Shared start within a pair.** Same-seed agents start from identical main-network weights.
  This was verified on this replication's seed-42 pair by the parallel study (27 of 27 arrays). For
  seeds 43 and 44 it follows from the same code path but has **not been checked**
  (`ALGORITHMIC_NULL_TODO.md`). The three pairs differ from each other, so the between-seed SE is
  a real three-start estimate. But the per-pair sign counts (and E1's "3 of 3") are counts over
  matched starts, not independent agents.
- **Weighting.** Survival means weight rows by episodes added, not by `Episode/_window_n` as 5 says.
  This is recorded in the 5 note (plan-reviewer T2). The verdict is what the code computes.
- **Recovery resolution.** Nearly every recovery lands in the first 20,000-episode logged row, so
  H-rec is mostly ties by construction. Frozen agents show a ~140-step loss that the training
  curve repairs inside that first window (10.5). The 5.1 recovery measure is too coarse for this
  world.
- **Exploratory outcomes** were chosen after the data and are uncorrected for about 20 comparisons.
  E1 is the same data as the (null) survival mean. E2 is one world and three pairs.
- **Agent differences from May** shared by both arms (GAE_NORM returns, critic learning rate
  0.0005 vs 0.0001, no temperature head) remain reasons a null may not transfer to May's setting
  (3.4, O2).

### 11.3 What to do next (for the user and `experiment-designer`; nothing launched)

1. **A world with room above the cap.** Re-run the double return where the hunting stage leaves the
   ordinary agent well below 500 (May: ~280). Screen candidate worlds with the ordinary agent
   first. Target a stage-1 cap share under about 50 %. Levers: permeable bushes (May's), weaker bush
   healing, May's `decay_power` 2.0, a pouncing predator. A longer episode cap would also give
   room, but it changes the task. This is the parallel study's "task with room above the step
   cap".
2. **Learning speed with seeds as a pre-registered primary outcome.** Register area under the
   survival curve over the first 100k / 300k episodes and episodes-to-threshold, for learning
   from scratch and after each switch. Set the noise rule in advance. The hint E2 comes from this
   study's stage 1 and is exactly the gap the parallel study lists as candidate 4. Hand it to its
   dossier (plan step 9).
3. **Cross-seed pairs.** Pair each modulated agent with an ordinary agent from a *different*
   main-network seed, or add an arm with a different seed. Then the pair comparison is no longer
   anchored to one shared start. Check seeds 43 and 44 for identical starts either way.
4. **More seeds only after 1.** Adding seeds in this world cannot rescue a comparison the cap
   compresses. The 7.7 "more-seeds follow-up" pays only once the world has room.
5. **Frozen-agent retention stays in any rerun.** It was the only registered measure with room here
   and the only one that sees forgetting at all. Consider making it co-primary.
6. **If death rate (E1) is to be tested,** pre-register it for the hunting stages, including stage
   1, with a between-seed rule and cross-seed pairs, since it currently rides on matched starts.

### 11.4 Metrics requested

| Metric | Why now | Where it'd live | Cost |
|---|---|---|---|
| Finer early-stage logging after a stage switch: survival per 2,000-episode block for the first 50,000 episodes of each stage | Recovery (H-rec) ties by construction because both agents are back within the first 20,000-episode logged window; the ~140-step frozen-agent loss is repaired inside it | `train.py` episode logging, gated on "within N episodes of a stage boundary" | cheap (a few extra scalar rows per switch) |
| Share of episodes at the cap per logging row, written as its own key | The ceiling check reads `Episode/Term_MaxSteps`, which works, but a named cap-share key would let every read-out flag ceiling-limited windows without study-specific code | trainer episode-summary block | cheap |

### 11.5 Related issues and hand-offs

- `plan-reviewer`: review of this verdict (plan step 8), then `pi` (section 9).
- Cross-study dossier `docs/experiments/active/modulator_clues/CROSS_STUDY_NULL_DOSSIER.md`: append the
  verdict, the ceiling label and hints E1/E2 (plan step 9, signed, append-only).
- Shared-start check for seeds 43/44: open item in `ALGORITHMIC_NULL_TODO.md`.
- No new bug found. The patrol off-by-one (3.5) stands as handed to `bug-curator` and affects both
  arms equally.

### 11.6 Sources

| What | Where |
|---|---|
| Registered read-out, ceiling check, exploratory outcomes | `results/analysis/continual_worlds/mayrep_readout.json`, text `tmp/20260930_mayrep_readout.txt` (script `scripts/analysis/studies/continual_worlds/pilot_readout.py --study mayrep`, commit `c4772791`) |
| Zero-shot retention (greedy + sampled) | `results/analysis/continual_worlds/retention_mayrep_readout.json`, log `tmp/20260930_retention_mayrep_readout.log` (commit `16de3d1a`) |
| Temporal table (10.6) | `tmp/20260930_mayrep_temporal.json` (20k-window means from `pilot_readout.scan` / `Series` on the six local WandB folders) |
| Working notes | `tmp/20260930_183000_mayrep_step7.md` |
| Parallel study's end-of-training reading and learning-speed gap | `docs/experiments/active/modulator_clues/algorithmic_null.template.html` ("What Both Agents Compute"), `ALGORITHMIC_NULL_TODO.md` |

## Feedback from plan-reviewer

*Adversarial pre-launch review, 2026-09-29, against commits `8ab84f95` + `62c2697a` (decisions 8.1 taken). Reviewed by: plan-reviewer.*

**Verdict: SOUND WITH CONCERNS.** The May → replication mapping is faithful (checked against the saved
configs of the real May runs, not the stage YAMLs), the training design can be launched as written, and
no finding is Critical, so no `docs/reviews/` file is written. Four Moderate findings are all in the
*analysis* rules and the zero-shot driver: three are doc-only edits that should be made before launch
(the read-out script mirrors this doc's text), one is a small code fix needed before the zero-shot test,
not before launch.

Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run · 🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

### Findings

| # | Sev | Location | Issue | Suggested fix | Owner |
|---|---|---|---|---|---|
| M1 | 🟡 | 5.6 (zero-shot test), 3.5 (seed row) | **The zero-shot driver will refuse this schedule as it stands.** `scripts/eval/continual_forgetting_matrix.py:145-147` requires every visit of a world to have a *byte-identical* saved stage config. The trainer makes `config` the same object as `schedule.stage_configs[0]` (`train.py:578`) and then stamps it with the CLI seed (`train.py:611`), `tag` and `wandb.name/group/job_type`, so stage 0's saved file differs from stages 1–4. Ground truth: pilot 2a's `stage_00` vs `stage_01` differ in exactly `tag`, `wandb.group`, `wandb.job_type`, `wandb.name`; May's own `stage_00` says `seed: 0` while `stage_01` says `seed: 42`. Pilots 2a/2b only revisited stages 1↔3 and 2↔4, so the stage-0-revisit path has never run. Here `active` is stages 0, 2, 4 → `ValueError: World 'active' visited twice with different saved configs`. Same stamping breaks the 3.5 rule "the runner reads the top-level `seed:` of each saved config": for seeds 43/44 the stage 1–4 files will read `seed: 42`. | `developer` (add to the Q4 hand-off): compare only the world-defining sections (`environment`, `sensory`, `body`, `thermal`, `perceptual_noise`) or strip `seed`/`tag`/`wandb`/`training` before comparing; update `SCRIPTS_DEPENDENCY_MAP.md` in the same change. In 3.5, read the seed from `models/config.yaml` (= stage 0) only. Not a launch blocker: checkpoints are kept (`max_checkpoints_to_keep: null`, confirmed on real continual runs with 51–71 checkpoints) and the saved configs persist, so the test runs once the driver is fixed. | developer; experiment-designer (3.5 wording) |
| M2 | 🟡 | 5.3 verdict table | **A plausible outcome is mislabelled "Reversed".** `G_k = F_k(mod) − F_k(ord) = D_k − D_1`, so H-forget is not an independent reading: it says "the return advantage exceeds the stage-1 advantage". If the modulator is ahead on both returns (`D_k > 0`) but its stage-1 lead is larger (`D_1 > D_k`), H-forget reads *unfavourable* and the table's "any unfavourable" rule returns "Reversed — the ordinary agent clearly ahead", which is false. Any mixed outcome (some favourable, some unfavourable) lands there too. | Add a **Mixed** row; state `G_k = D_k − D_1` in 5.1; make "Reversed" require H-ret unfavourable on at least one return. Pre-register before launch (the script's `check_mayrep_doc()` patterns must be updated in the same edit — see L3). | experiment-designer |
| M3 | 🟡 | 5.1 `S_k`, 5.4 "May-sized" | **Window mismatch between the verdict and the May comparison.** `S_k` is the last 200,000 episodes of a 700,000-episode return stage (29 % of the stage); May's numbers are the last ~10 % (~20–25 k episodes, NMN probe §5.5.2). On a stage where recovery is still under way (May: ordinary plateaus, modulated keeps climbing), the wide window pulls `S_k(mod)` down more than `S_k(ord)`, biasing `D_k` downward, so the 19 % / 24 % "May-sized" line can be missed for window reasons rather than effect reasons. | Keep 5.3 on the 200 k window (consistent with [[CONTINUAL_WORLDS]] 5.1) but pre-register that 5.4's normalised advantage and forgetting ratio are computed on the **May-style tail** (last 10 %), or report both and name which one decides "May-sized". | experiment-designer |
| M4 | 🟡 | 5.2 / 5.3 `2 × SE` rule | **The denominator is unstable at n = 3.** An SD from three values has roughly 50 % relative error, so a lucky small SD turns a few-step difference into "beyond noise" and an unlucky large one hides a 50-step effect; the 2-of-3 sign count alone is met by chance half the time under the null, so the conjunction carries the rule. The plan prints May's ±4.4 and level 05's 1.5-step seed spread next to the result but never uses them. | Pre-register a floor: `SE_k := max(SE_k, 4.4 × sqrt(2/3) ≈ 3.6 steps)` (May's measured seed spread on a harder world), or an additional minimum absolute effect (e.g. `|mean D_k| ≥ 10` steps) for a reading to count as favourable / unfavourable. | experiment-designer |
| L1 | 🟢 | 5 (intro), 5.1 | `Episode/Steps_mean` is not a logged key (`grep -c 'Episode/Steps_mean' train.py` = 0); the trainer logs `Episode/Steps`, which is what the read-out script reads. | Rename. | experiment-designer |
| L2 | 🟢 | 3.4 | The list of agent differences from May omits `lr_critic` (May 0.0001 → today 0.0005) next to MC → GAE_NORM. Both arms share it, so it is a "why a non-replication may be uninterpretable" item, not an arm-vs-arm confound. | Add to the list. | experiment-designer |
| L3 | 🟢 | 5, 8.1 Q4 | Q4 is already under way: the working tree holds an **uncommitted** 438-line extension of `pilot_readout.py` (`--study mayrep`, `MR_*` constants asserted against this doc's text by `check_mayrep_doc()`). Consequence: any wording change to 5.1–5.5 from M2–M4 must be mirrored in `MAYREP_PATTERNS`, or the script refuses to run. | Land M2–M4 in the doc first, then the script; route the script through `code-reviewer` once committed. It is not blocking the 1.5 M read if it lands before then. | developer; experiment-designer |
| L4 | 🟢 | 3.2, config headers | The cited May directory `20260511-174837_…` is an aborted launch (0 checkpoints); the real runs are `20260511-175843_…mod` (WandB `8eorbxhq`) and `20260511-180151_…unmod` (`lrzvg8k6`). All four May dirs' saved configs are byte-identical, so nothing in the mapping is wrong — but cite the real run so a reader who opens it finds checkpoints. | Cite the real directories. | experiment-designer |

### Verified — claims I tried to break and could not

- **Mapping faithful.** Read from the real May run's saved `stage_00`/`stage_01`: the four predator keys (`detection_range` 5→0, `hunt_stamina_threshold` 0.7→1.1, spawn/patrol whole grid → `[[1,1],[5,5]]`) and the tag are the only diffs; food 2+2 (two zero-count entries), ambushers 1 per quadrant, rocks 3 per quadrant `blocking: false`, bushes 5+5 `blocking: false`/`hides_agent: true` with no `blocks_animals`, bush smell `[0,0,0,1,0]`, predator = rabbit smell `[0,1,0,0,0]`, `decay_power` 2.0, `sensor_radius` 20, `visual_sensor_range` 0, `vector_size` 5, body 0–100 / no over-eating death / `recovery 0.1 + 0.5` / fixed starts, `max_steps` 500, `random_start_pos` true, noise off, `max_checkpoints_to_keep` 20, `return_mode: MC`, `temp_clip [0.5, 5]`. Every row of 3.1 and 3.2 matches.
- **Checkpoint retention in continual mode.** Stage configs are deep-copied from the base config *after* `configs/train/recurrent_ppo.yaml` is merged (`train.py:214-217`, `522-525`), so `max_checkpoints_to_keep: null` survives `config = stage_configs[0]`; real continual runs (`pilot2a/2b`, `p1`–`p3`) hold 51–71 checkpoints with `null` saved. The 1.5 M and 3.0 M stage-end checkpoints will exist.
- **Stage-end checkpoint semantics.** The switch is checked at iteration start (`train.py:1660-1673`) and the checkpoint written at iteration end with `stage: current_stage` (`train.py:2591-2621`); boundaries are multiples of the 100 k cadence and `last_checkpoint_save` is floored to a multiple, so the first checkpoint at or after each boundary is trained wholly on the old stage and carries index k — exactly what the driver asserts (`continual_forgetting_matrix.py:113-119`).
- **`--episodes` is refused** in continual mode (`train.py:721-723`); the budget is the last boundary.
- **Competence gate is satisfiable.** `Episode/FoodEaten` is the per-episode **sum** of per-step eating flags (`train.py:1818`, `core.py:997`), i.e. a bite count, so "≥ 1.0 bite per episode" is a real threshold, not a fraction.
- **Pounce is off.** A jump requires `attack_range_s > 0` (`core.py:702-703`); `[0, 0]` disables it.
- **Off-by-one is real and matches May.** `_parse_area` returns an exclusive upper bound (`config_loader.py:970-972`); `_hunt_step` clips inclusively (`core.py:679`); `8bd8f10f` is dated 2026-05-11, May's launch day.
- **No circular verification.** V1–V4 go through `train._build_continual_schedule` and `train.py` itself, not the tooling loader; V5–V7 measure the environment's behaviour.
- **Known Bugs.** A2 (same roster and tags every stage — V2), H2 (fixed; resume line named), B5 (single-config only), the (0,0) parking row (V5), the stale 8-wide continual tests (row 134; the plan names the Pilot 2 GPU run as the stand-in): all handled. Nothing unrecorded found beyond the patrol off-by-one the plan already hands to `bug-curator`.
- **Rules.** Survival steps only; no fallback defaults touched; no `scripts/`, `src/`, `default.yaml` or registry value changed by the design (the Q4 developer change does touch `scripts/` and must update `SCRIPTS_DEPENDENCY_MAP.md`); `thermal.enabled: false` and `blocks_animals: true` are canonical; no git operations; manifest has the 12 columns and the agent tokens the read-out parser expects.

### Assumptions the conclusion rests on

- ❓ **O1 — the 150-step gate is lenient for this world.** It is 60 % of level-05 Home competence with thermal on and pouncing predators; this world has neither, so 150 may be reached by an agent that has not learned the predator. The 10 % "still climbing" check is the better guard but is only a flag. Consider making "still climbing > 10 %" a pre-declared caveat on H-forget (it biases both agents' forgetting toward smaller values).
- ❓ **O2 — the modulator's effect survives without the temperature head.** May's boundary transients were carried by the temperature head (NMN probe §5.5.5). Pre-registered as "about today's modulator" (2 / 3.4), so a null is a null for today's agent, not a refutation of May — the doc says so; keep saying it in 11.
- ❓ **O3 — three seeds of a harder-to-learn contrast.** May's 107–132 steps was ~25 × its seed spread; if today's refuge bushes and long-range smell shrink the passive→active contrast (7.5 covers "no dip"), a real but smaller effect (say 15–30 steps) sits where n = 3 cannot resolve it, and 7.7 "not replicated" would be an underpowered null. Say so in 7.7.
- ❓ **O4 — GPU run of this world.** V4 is a CPU start with 4 envs; the 128-env GPU path for these two worlds has not been run (the same path ran for Pilot 2). Low risk; the runner's start-up-line check covers it.

### Cost of being wrong

If M2–M4 are left as written, six ~10–15 h runs (~70 GPU-hours) can end in a verdict that is mislabelled ("Reversed" for a mixed result, "not May-sized" for a window artefact, "beyond noise" on a lucky SD) and that label then goes into the continual-worlds story; the fix is a few sentences before launch. If M1 is left, the pre-registered zero-shot test fails on its first invocation and costs a developer half a day, but no training is lost. Nothing in this plan risks data or a rerun.

## Feedback from plan-reviewer — analysis-verdict gate (2026-09-30)

*Adversarial review of sections 10–11 and the top status box, against commit `f4a81d71`, the read-out
files `results/analysis/continual_worlds/mayrep_readout.json` and `retention_mayrep_readout.json`, and
the six local WandB folders (re-read through `pilot_readout.scan` / `Series`). Reviewed by: plan-reviewer.
Analysis plan `tmp/20260930_continual_analysis_plan_v2.md`, step 8.*

**Verdict on the verdict: SUPPORTED WITH CAVEATS.** The registered read-out is the rule of 5.3 applied
as written to all six manifest rows, and every number I recomputed matches. Three things should be said
more carefully before the conclusion is carried into the cross-study dossier or a paper: the registered
verdict turns on the pre-registered noise floor (without it one reading would have counted as favourable);
the frozen-agent retention test bounds a May-sized forgetting advantage only on the first harmless stage,
not the second; and the learning-speed hint (E2) is about half as large when measured against environment
steps instead of episodes. None of these changes the label. No finding is Critical, so no `docs/reviews/`
file is written.

Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run · 🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

### Findings

| # | Sev | Location | Issue | Suggested fix | Owner |
|---|---|---|---|---|---|
| A1 | 🟡 | 10.1, 11.1 (1) | **The verdict is floor-sensitive, and the doc does not say so.** On the second return `D_5` is +1.46 with the sign favourable in 3 of 3 pairs and a raw between-seed SE of 0.67 (`H_ret.5.se_raw`); raw `2 × SE` = 1.35 < 1.46, so without the 3.6-step floor of 5.2 H-ret at k=5 would read *favourable* and the 5.3 table would return **Partly replicated**. The floor was pre-registered before any data existed (rev 2026-09-29, plan-reviewer M4), so applying it is correct and the label stands — but a reader of the dossier should be told that one registered reading sits on the wrong side of the raw threshold and the right side of the floored one. A 1.5-step edge at 93 % cap is not a May-type effect either way. | Add one sentence to 10.1 after "All four readings used the floor": state that `D_5` would clear the raw `2 × SE` (1.35) and that the floor is what makes it a null; point to 5.2 for why the floor exists. | experiment-analyzer |
| A2 | 🟡 | 10.5 "Why this test matters", 11.1 (3) | **"A May-sized forgetting advantage would lie well outside both" is overstated for `ZA_4`.** The "plausible range" uses mean + 2 × SE with an SE estimated from three values. For n = 3 (two degrees of freedom) a 95 % interval needs t ≈ 4.3, not 2: `ZA_4` = 10.0 + 4.3 × 18.8 ≈ **+91**, which reaches the May-sized band (65–72 % of a ~143-step loss ≈ 93–103 steps). `ZA_2` = 2.7 + 4.3 × 8.6 ≈ +40 does exclude it. So the retention test rules out a May-sized advantage on the **first** harmless stage and cannot on the second, where the three pairs disagree in sign. The "not only a ceiling artefact" sentence survives on `ZA_2` alone; say so. | Reword: "`ZA_2` excludes a May-sized forgetting advantage even with a three-seed interval; `ZA_4` (three pairs of opposite sign, SE 18.8) cannot". Drop "well outside both". | experiment-analyzer |
| A3 | 🟡 | 10.7 E2, 11.1 (4), 11.3 (2) | **E2 is measured on an axis that favours the agent that survives longer.** Learning speed is read at equal *episode* counts, but a longer-surviving agent completes fewer episodes per environment step, so by the same episode count it has had more training. Ground truth from the six WandB folders (`Series.steps_to`, stage 1): by episode 100,000 the modulated runs had consumed **10.0 / 10.9 / 10.0 M** environment steps against **8.4 / 8.0 / 8.2 M** for the ordinary runs (20–36 % more gradient updates); by 200,000 episodes, 36–43 M vs 29–31 M. Re-read on the environment-step axis the lead **survives in 3 of 3 pairs but at about half the size**: mean survival over the first 10 M steps 99.9 vs 88.2 (**+11.7**, vs +21 on the 100k-episode axis); over the first 30 M steps 168.9 vs 148.2 (**+20.7**, vs +44 on 300k episodes); 20k-window level at 30 M steps 322 vs 279 (**+43**, vs +102 at 200k episodes). At 60 M steps the seed-42 pair reverses (417 vs 435) and the mean gap is +7. Time-to-90 % on environment steps: ordinary 52.5 / 84.9 / 84.5 M, modulated 75.0 / 80.0 / 72.9 M — still 2 of 3 faster, but seed 42's modulated agent is 43 % slower, not 8 %. | Report E2 on both axes (episodes and environment steps) before it goes to the dossier or a pre-registration; make the environment-step version the one a follow-up registers, since that is the RL-standard axis and the one 5.1 already uses for recovery. Numbers above are in the scratch script named in "Verified". | experiment-analyzer; experiment-designer (11.3 item 2) |
| A4 | 🟢 | 10.0, 11.2 | "May's effect, measured the same way, would need about 177" is the k=3 figure only (0.38 × 465 = 177). The k=5 figure is 0.48 × 465 ≈ **223**. | Write "177–223". | experiment-analyzer |
| A5 | 🟢 | 10.0 ("Three seeds could not separate…"), 11.3 (4) | The two sentences pull against each other. 10.0 repeats the registered 7.7 wording, which blames seed noise; 11.3 correctly says more seeds cannot rescue the comparison. The binding constraints were the floor (A1) and the cap (10.4), not the measured seed noise (raw SEs 0.6–0.9). | Keep the registered label; add "the band was set by the pre-registered floor and the step cap, not by the measured spread between seeds" so 10.0 and 11.3 agree. | experiment-analyzer |
| A6 | 🟢 | 10.7 E2, last row | Labelled "episodes to reach 90 % of own final level", but the modulated values are the **common-reference** recoveries (`recovery_common`: s42 280k, s44 288k). The own-reference values are 296k / 292k / 292k (`recovery_own`). Sign count unchanged (s42 slower, s43 and s44 faster). | Either relabel as common-reference or replace with the own values (+36k, −68k, −56k). | experiment-analyzer |
| A7 | 🟢 | 10.4, 11.1 (2) | "This matches the parallel study's end-of-training reading" reads as corroboration. The parallel page's +1.46 (floored SE 3.6) is this study's own `D_5` from the same script and window, carried over through the dossier — one computation, not two. 10.4 already says "the same number"; 11.1 should too. | Reword 11.1 (2): "the parallel study quotes this same number". | experiment-analyzer |
| A8 | 🟢 | `mayrep_readout.json` | Every run carries `"status": "running"` while `"finished": true`; M3/M5/M6's last logged row is at 5,096k episodes against a 5,100k budget (the last-200k window of stage 5 is 4k short). Neither affects a number in the doc. | Note in 11.6 or leave; the manifest status in 4 was already corrected in `72909d72`. | developer (cosmetic) |

### Verified — claims I tried to break and could not

- **Registered arithmetic.** Every `S_k`, `T_k`, `F_k`, `H`, per-pair `D_k` / `G_k`, mean, raw SE and floored SE in 10.1 matches `mayrep_readout.json` (`H_ret`, `H_forget`) to rounding; the 5.3 row order gives "not replicated" (no favourable reading; H-ret unfavourable on neither return); 7.7 wording is the registered one. H-dip "equal" on all four readings, H-rec 0 of 3 with the tie reason recorded per pair, H-hyper 0 of 3 (`H` > 0 for every run), gate pass, switch real, 7.5 not fired, no collapse — all as the JSON says.
- **Ceiling arithmetic.** 500 − 468.6 / 470.9 = 31 / 29 steps is the largest possible `D_k`; (500 − 469) / 465 = 6.7 % < the 19 % May-sized line; May's 38 % / 48 % are 106.9 / 278.3 and 132.5 / 278.3 from the probe's own table (`NMN_CONTINUAL_DOUBLE_RETURN_PROBE.md:290-294`). Cap shares in 10.4 match `ceiling_check.per_run`; `Episode/Term_*` shares sum to 1.000 in all 30 run-stages, so `Term_MaxSteps` is a clean cap share here (the Known Bugs "termination code unreliable when a body system is off" row concerns injury-disabled worlds; thermal-off did not disturb the shares).
- **Retention test.** `A_k`, `Z_j`, `ZA_j`, SEs (8.6 / 18.8, computed from each agent's between-seed SD as 5.2 says) and the three per-pair "beyond eval noise" stars match `retention_mayrep_readout.json`; the sampled-action robustness run agrees (+6.5 / +9.7, inside noise). **Greedy as the registered policy is a fair reading**: 5.6's command passes no `--eval-policy-mode`, and the driver then uses each saved config's `behavior_measures.eval_policy_mode`, which is deterministic (`continual_forgetting_matrix.py:46-49`). Checkpoints 1500006 / 3000030 / 3700014 / 4400009 / 5100018 are the first at or after each boundary. The frozen agents' own-world survival (466–478) sits within ±8 of the training-log last-20k values, so the eval world is the training world.
- **Run inventory.** All six manifest rows (M1–M6) are in the read-out, all `attempt: 1`, all finished; nothing was dropped or relaunched.
- **Pre-registration honoured.** The 5.3 rule, the 5.2 floor, the 5.4 tail window and the 5.6 quantities are applied as revised on 2026-09-29; the ceiling label and E1–E3 are marked post-data in the JSON itself (`rule: "... post-data label, plan 2026-09-30 step 4"`, `label: "EXPLORATORY, chosen after the data were seen"`), and no threshold moved after the data.
- **E1 labelling.** Death rate = 1 − cap share on the same last-200k window; the doc says it is the survival mean seen as a proportion and not independent — correct. Per-pair values match `exploratory_post_data.death_rate_last200k`.
- **Shared start (seed 42 only).** `ALGORITHMIC_NULL_TODO.md:29-36` verifies 27 of 27 main-network arrays on this replication's seed-42 pair, built from one key through the trainer recipe, and says seeds 43 / 44 are still to be checked. 11.2's wording matches. (Note it is a check at construction, not a read of the saved stage-0 checkpoints; wording could say so.)
- **Metric.** Survival steps only; reward is not read anywhere in the read-out (`pilot_readout.py` has no reward key). Temporal evolution is reported (10.6), not endpoints alone.
- **Scratch for A3:** `/tmp/claude-1000/-media-nas01-projects-Interoceptive-AI-grid-world-pain/4efbe660-28c2-4643-b231-d3c6d2635b5a/scratchpad/e2_envsteps.py` (reads the six WandB folders through `pilot_readout.scan` / `Series`; session-local, not committed).

### Assumptions the conclusion rests on

- ❓ Seeds 43 and 44 start from identical main-network weights within a pair (assumed from the code path, not checked; 11.2 says so).
- ❓ The May advantage lived in **relearning after the return**, not in what the harmless stage erased. If so, the retention test is the wrong instrument and the training curve's 20k-episode logging grid is too coarse to see it here (10.5, 11.2 say this); the null then says nothing about May in either direction.
- ❓ A "world with room above the cap" (11.3 item 1) will keep today's body and senses while leaving the ordinary agent well below 500 — an untested screening step, and the only route to a replication that can fail.

### Alternative explanation the analysis does not rule out

The modulated agent's small, same-sign edge in every hunting stage (E1; `D_1` +2.0 / 0.0 / +3.5, `D_3`, `D_5` +1.5) and its faster early learning (E2, on either axis) are both consistent with the modulator adding a few parameters that help *from the start*, and equally with a shared-start artefact that keeps the two runs in one basin with a small offset. Nothing here separates those; the doc says as much in 11.2 and 11.3 (3). The verdict does not depend on which is true.

### Cost of being wrong

If A1–A3 are left unstated, nothing is re-run and no data is lost; the cost is that the dossier inherits a "not replicated" label that a critic can show was one raw-threshold call away from "partly replicated", a retention bound that does not hold for the second harmless stage, and a learning-speed hint twice its honest size — each of which weakens the eventual paper's credibility rather than its result. If the world-with-room follow-up (11.3 item 1) is launched on the E2 episode-axis numbers, it pre-registers an effect size that the environment-step axis does not support, and its verdict rule is mis-sized from the start. That is the expensive path: about 70 GPU-hours for six runs.
