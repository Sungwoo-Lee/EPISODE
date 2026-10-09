---
title: Lookalike animals, close pounce, small food — a world built to make injury-driven caution pay
topic: hypervigilance
status: active
created: 2026-10-09
last_updated: 2026-10-09
wandb_tag: rppo_lookalike_l05
---

# Lookalike animals, close pounce, small food

## Question

The project wants the agent to show **hypervigilance**: when it is injured, the mere presence of a
harmless wandering rabbit should make it hide in bushes *more* than when no animal is around, while
an unhurt agent should not hide much more because of the rabbit. In the current training world
(level 05: a cold 10×10 map with campfires, bushes, a hunting predator that pounces, and a harmless
rabbit) the opposite or nothing happens: the extra hiding caused by injury is about the same or a
little *smaller* when the rabbit is present (by 1 to 6 percentage points of time spent on a bush).

Three features of level 05 plausibly make hypervigilance useless there. The agent can **tell the two
animals apart by smell**, so a rabbit is never a reason for caution. The predator **gives itself
away from afar**: it can start hunting up to 7 cells away and walks straight at the agent, so the
agent can wait and see. And **hiding costs little**, so there is no trade-off for injury to shift.

This experiment trains the ordinary and the neuromodulated agent (two seeds each) in a new world
that removes those three features, and asks: **in this world, is the injury effect on bush hiding
larger with the rabbit present than with no animal, while the rabbit alone barely moves an unhurt
agent?** Exploratory (two seeds per agent, chosen by the user); a positive result is a clue to
follow up, not a confirmation.

## The world: four decisions relative to level 05

| # | Change | Level 05 | New world | Why |
|---|---|---|---|---|
| 1 | Same smell for both animals | predator smell `[0, 0.7, 0.5, 0, 0]`, rabbit `[0, 0.5, 0.7, 0, 0]`, both with per-episode spread `[0, 0.3, 0.3, 0, 0]` | both `[0, 0.6, 0.6, 0, 0]`, spread unchanged | Without a smell difference, an animal approaching could be either; the safe response to an uncertain animal should depend on how costly a hit would be, which is what injury changes. The midpoint keeps each animal's total smell strength (channel sum 1.2) and noise exactly as before, so "an animal is near" is as easy to sense as in level 05 — only *which* animal is hidden. Sight was already identical (every entity shows as `[1.0]`). |
| 2 | Predator notices the agent only when it can already pounce | notices at 1–7 cells (drawn per episode), pounces from 2–3 cells | notices at **3**, pounces from **3**, every episode | Until the agent is within 3 cells, the predator does the same random walk as the rabbit; the moment it notices the agent, it pounces that same step (verified in simulation below). No long visible approach, so "wait and see" stops working. Fixed `[3, 3]` for both rather than e.g. noticing at 2–3: it meets the "noticing never exceeds pounce reach" requirement in every episode by construction, gives one reach the agent can learn, and makes the test-time "animal within 3 cells" event the same as "inside the danger zone". Pounce success 0.5 and the 1–3 step cooldown are level 05's. |
| 3 | Smaller food items | an item lasts 12 bites, then reappears elsewhere | **6 bites** | A bush-sitting agent must come out twice as often to stay fed, so hiding has a real cost and an unhurt agent has a reason not to hide. Food count (1–4 items per episode), 6 nutrition per bite and the metabolic cost are level 05's. |
| 4 | Bush healing | resting on a bush heals 25× faster | **unchanged (25×)** | User decision: keep. |

Everything else is level 05 (cold air, 1–3 campfires, random start position, start nutrition,
start injury and start body temperature, ambush predators, rocks, bushes that animals cannot enter).

## How this differs from earlier attempts

Four earlier studies took identity away from the animals or made caution costly. This world combines
their manipulations and removes the one escape route each of them left open.

| Earlier study | What it did | What happened | What this world changes |
|---|---|---|---|
| Same-smell rounds 1–2 ([[sameprop_round2_design]], May 2026) | both animals smelled identical (`[0, 1, 0, 0, 0]`) | the agent still kept further from the predator than from the rabbit; round 2 (disable hunting, separate food from rabbits) was stopped at 4–5% of its budget with no verdict | the escape route was movement |
| Discriminating-channels memo ([[sameprop_discriminating_channels]], §4) | listed every channel that could still separate same-smelling animals | ranked the predator's **straight approach toward the agent** (it noticed the agent at 5 cells and walked at it) as the dominant pre-contact cue | here the predator notices the agent only at 3 cells, its pounce reach, so its first move toward the agent **is** the pounce; no long approach is left. The two movement cues that remain (diagonal steps, walking back to the centre) are listed below and measured |
| Scarcity + smell ambiguity ([[20260620_hypervig_scarcity_olfactory_ambiguity]], June 2026) | near-identical, heavily jittered smells, a one-bite lethal predator, scarce vs abundant food | its preceding step found the agent never learned to keep its distance; it survived by **getting bitten, then healing and hiding**, and the lethal predator killed it in 40–70% of episodes. No results are recorded in that doc for the scarcity runs themselves | predator damage is level 05's (15–120, not one-bite), food is made costly by smaller items rather than fewer patches, and the question is the injury × rabbit interaction, not hunger gating |
| Single-channel smell ([[SINGLE_CHANNEL_SMELL_HYPERVIGILANCE]], Sep–Oct 2026) | made the two animals harder (not impossible) to tell apart by smell, inside level 05 | stage-1 reading (2026-10-03, three seeds) was inconclusive on every decision and triggered a seed top-up | smell identity is removed completely (same mean), **and** the predator's long visible approach is removed, **and** hiding is given a food cost — the three features of level 05 the Question names |

**Likeliest failure, named in advance: "get bitten, then heal and hide".** This is the strategy the
scarcity study's preceding step found, and it stays available here because bush healing is kept at
25× (user decision). See the failure-mode list for how it is recognised.

## What the agent can still use to tell the animals apart (not fixed here)

Checked in the code (`src/environment/core.py`, `_hunt_step` and `_wander_step`) and in a 256-episode
random-action simulation of the new world:

- **Diagonal steps (a real, learnable cue before any attack).** While wandering, the rabbit takes a
  random step in both axes at once, so it moves diagonally in 42.5% of its moves (17,070 of 40,189 in
  the simulation). The predator draws the same random step, but a diagonal is resolved to one axis
  at random, so it **never** moves diagonally (0 of 23,093 wandering moves). Both stand still in 1 of
  9 steps. With a 13-cell sight diamond and a 5-cell smell diamond, an animal that changes both row
  and column in one step is in principle visible to the agent, so a network could learn "diagonal
  mover = rabbit". **No config key controls this**; removing it needs a code change (for example a
  mandatory key that makes the wanderer resolve diagonals the same way, which also changes the
  random-number stream and therefore needs a parity decision). Routed as an open question to the
  user, not implemented.
- **Everything else is the same before an attack**: same count range (0–2 each), spawn area and patrol
  area (the whole map), the same speed setting (moves every step), same sight, same smell
  distribution, both blocked by bushes, placement by the same rule.
- **Walking back to the centre (a second movement cue; corrected 2026-10-09 after plan review).** When
  a hunting predator loses interest — the agent steps onto a bush, gets more than 4.5 cells away
  (noticing range 3 × 1.5), or the predator runs out of stamina — it switches to a third mode and walks
  straight to the patrol centre (cell 5,5), one axis per step, until it is within 2 cells of it; only
  then does it wander again. The rabbit never does this. With noticing range 3 the "more than 4.5
  cells away" exit is reached far more easily than in level 05 (where it was 1.5–10.5 cells), so an
  agent that flees or hides after a pounce will send predators back to the centre often, and the
  predator can end up over-represented near the centre. A straight multi-step walk toward the centre
  is therefore a predator signature that the agent can see **before the next pounce**, not only after.
- **"Came within 3 cells and did not pounce" means rabbit, by design.** A rested predator that comes
  within 3 cells of an agent standing in the open pounces at once, so an animal that sits within 3
  cells for a step or two without pouncing is almost always the rabbit. This cue costs the agent the
  first step of the encounter (pounce success 0.5), but it exists.
- **Random-action simulation, 2026-10-09** (256 parallel streams × 500 steps with automatic reset =
  128,000 agent steps, about 6,000 episodes per world; script
  `tmp/20261009_lookalike_difficulty/mode_sim.py`). A random agent dies quickly (about 21 steps per
  episode) and never flees, so these numbers describe the world's mechanics, not a trained agent's
  experience; the trained agents' version is measured during testing (cue-use readout below).

  | | New world | Level 05 |
  |---|---|---|
  | predator-steps (active predator × step; the denominator) | 83,958 | 82,392 |
  | — wandering | 72,739 (86.6%) | 62,235 (75.5%) |
  | — hunting | 10,662 (12.7%) | 18,916 (23.0%) |
  | — walking back to the centre | 557 (0.7%) | 1,241 (1.5%) |
  | losses of interest | 421: 418 agent on a bush, 3 agent > 4.5 cells, 0 stamina | 829: 703 bush, 7 distance, 119 stamina |
  | share of steps within 2 cells of the centre: predator / rabbit | 12.8% / 12.5% | 13.7% / 12.8% |
  | predator first comes within 3 cells of an agent in the open | 3,212 times; followed by a pounce attempt within 2 steps in 2,836 (88%) | 4,118; 2,602 (63%) |
  | rabbit first comes within 3 cells of an agent in the open | 6,505 times; never a pounce | 6,311 |
  | rabbit moves that are diagonal | 42,580 of 99,645 (42.7%) | 42,850 of 100,379 (42.7%) |

  Reading: in the new world, an animal that comes within 3 cells and does not pounce within 2 steps
  is the rabbit in 6,505 of 6,881 cases (94.5%) for this random agent. Centre clustering does **not**
  appear with a random agent (its losses of interest are almost all bush-triggered and short), so
  whether it appears for a trained agent that flees is an open question for the test phase.
- These cues do not remove the ambiguity the world is built for — **at the moment an animal first
  comes within 3 cells**, before it has pounced or not, and before any return walk, both animals look
  and smell the same apart from the diagonal-step cue — but they mean the agent can learn to tell the
  animals apart over a few steps. The cue-use readout below checks whether it does.
- Touching an animal: contact with the predator is an attack (damage and a pain signal); contact with
  the rabbit produces no signal (`nociception_intensity` is read only for damaging animals). Unchanged
  from level 05.

## Runs

Same agents and training settings as the level-05 arm of the fast-bush-healing replication
([[FAST_HEAL_REPLICATION]]): the ordinary recurrent-PPO agent and the agent with a FiLM modulator at
encoder, recurrent core, actor and critic, `--episodes 10000000`, `--log-interval 10`, seeds passed
explicitly. Only the world differs. Verified: the saved configs of the replication's level-05 runs
(seeds 42 and 43, both agents) differ from today's assembly of the same files only in the
command-line keys (episodes, seed, log interval, tag and WandB names) — so passing the same flags
reproduces their training settings exactly.

### Launch manifest

WandB group `lookalike_animals`, job type `pilot` (two seeds; exploratory). Tag = WandB name.

| Run | Agent | Seed | Tag | node:GPU | Status | Launched | WandB ID | Log |
|---|---|---|---|---|---|---|---|---|
| 1 | ordinary | 42 | rppo_lookalike_l05_t1none_s42 | 110:0 | planned | — | — | — |
| 2 | modulated | 42 | rppo_lookalike_l05_t16quad_s42 | 110:1 | planned | — | — | — |
| 3 | ordinary | 43 | rppo_lookalike_l05_t1none_s43 | 111:0 | planned | — | — | — |
| 4 | modulated | 43 | rppo_lookalike_l05_t16quad_s43 | 111:1 | planned | — | — | — |

Nodes chosen by the user (RTX 3090). Tags checked unique in `train_command*.sh`, `configs/` and
`docs/experiments/` on 2026-10-09.

### Configs

| Run | World | Agent config |
|---|---|---|
| 1, 3 | `configs/environment/experiment/basic/lookalike_animals_close_pounce_small_food_10x10.yaml` | `configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml` |
| 2, 4 | same | `configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml` |

### Launch block (for `train_command-agent.sh`; the training-runner adds and launches it)

```bash
# ---------------------------------------------------------------------------
# lookalike_animals — same-smell animals, close pounce, small food, at level 05 (4 runs, seeds 42/43)
# Plan: docs/experiments/active/hypervigilance/LOOKALIKE_ANIMALS_CLOSE_POUNCE.md (launch manifest).
# World = basic/05 + identical predator/rabbit smell, detection = pounce range = 3, food 6 bites.
# Agents/episodes/flags identical to the fast-heal replication's level-05 arm. --seed passed explicitly.
# --num-envs / --checkpoint-frequency config-owned. User-chosen node:GPU placement.
# [110:0] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/lookalike_animals_close_pounce_small_food_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml --episodes 10000000 --seed 42 --device cuda:0 --log-interval 10 --tag "rppo_lookalike_l05_t1none_s42" --wandb-name "rppo_lookalike_l05_t1none_s42" --wandb-group "lookalike_animals" --wandb-job-type "pilot"
# [110:1] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/lookalike_animals_close_pounce_small_food_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml --episodes 10000000 --seed 42 --device cuda:1 --log-interval 10 --tag "rppo_lookalike_l05_t16quad_s42" --wandb-name "rppo_lookalike_l05_t16quad_s42" --wandb-group "lookalike_animals" --wandb-job-type "pilot"
# [111:0] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/lookalike_animals_close_pounce_small_food_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml --episodes 10000000 --seed 43 --device cuda:0 --log-interval 10 --tag "rppo_lookalike_l05_t1none_s43" --wandb-name "rppo_lookalike_l05_t1none_s43" --wandb-group "lookalike_animals" --wandb-job-type "pilot"
# [111:1] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/lookalike_animals_close_pounce_small_food_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml --episodes 10000000 --seed 43 --device cuda:1 --log-interval 10 --tag "rppo_lookalike_l05_t16quad_s43" --wandb-name "rppo_lookalike_l05_t16quad_s43" --wandb-group "lookalike_animals" --wandb-job-type "pilot"
```

## What would count as a clue (decided before training)

Measured in test scenes built on this world (next section), per run, at every saved checkpoint
(not only the end of training), with **bush dwell** = share of test-episode steps spent on a bush:

- **Injury effect** with an animal of a given kind = bush dwell when injured − bush dwell when unhurt.
- **Interaction** = injury effect with the rabbit − injury effect with no animal.
- **Rabbit effect on unhurt agents** = bush dwell (unhurt, rabbit) − bush dwell (unhurt, no animal).

**Estimator** (the same as [[SINGLE_CHANNEL_SMELL_HYPERVIGILANCE]] §Pre-stated reading, item 2): each
contrast is formed per checkpoint first; each run's series is summarised by the mean of its **newest
20 checkpoints** (of about 50; one every ~200,000 episodes), with a 95% t-interval on the effective
sample size 20·(1−r)/(1+r), where r is the lag-1 autocorrelation across those checkpoints (no
correction when r ≤ 0). That interval is checkpoint-to-checkpoint drift within one run, not
run-to-run variation.

A run shows the **hypervigilance signature** if all three hold:

1. its newest-20 interval for the **interaction excludes zero on the positive side**;
2. its newest-20 mean interaction is **larger than 1.4 percentage points** — the seed-to-seed
   spread of probe bush hiding already measured on the rabbit response (five seeds of one
   configuration; critical-settings registry, 2026-09-21). The same registry entry puts the spread
   of the stricter injury-driven measure at 1.05–2.67 points; the interaction is a difference of two
   differences, so its own spread is probably at the upper end. Values above 2.67 are reported as
   clearing that stricter bar as well;
3. its newest-20 mean **rabbit effect on unhurt agents** is smaller in size than its interaction.

A **clue worth following up** is the signature in **both seeds of the same agent**; a
**modulator-specific clue** is the signature in both modulated runs and in neither ordinary run.
Two seeds cannot separate an effect from seed-to-seed variation (that needs the complete-separation
logic of the single-channel study at three or more seeds); a clue here only justifies adding seeds.

**Whole-training view, reported for every run beside the late mean** (not only the newest 20): the
interaction per checkpoint across all checkpoints, the share of checkpoints with a positive
interaction (over all checkpoints and over the second half of training), and the largest
checkpoint-to-checkpoint jump. A late-window signature that is not matched by a majority of positive
checkpoints over the second half is flagged as "late-window only" in the write-up.

**Context, not a baseline:** the replication's level-05 runs at the same seeds showed an interaction
of −1 to −6 points. Those numbers come from different test scenes (old smells, old predator ranges,
12-bite food) and agents trained on different animals, so they say the signature was absent there;
they are not a reference value that the new runs are compared against.

A null or negative interaction in both seeds of both agents says these three world changes are not
enough, at two seeds.

Health checks read alongside, not as the result: **survival steps** over training (the project's
performance measure; see the abort rule below), death causes (predator pounce / other injury /
starvation / cold), time spent feeding, and pounce hits per episode.

## Failure modes, decided in advance

- **Survival collapses during training** (agents die early from starvation or pounces and never learn
  to hide well): the world is too hard; this is a design failure, not evidence against
  hypervigilance. **Abort rule:** at the first logged point at or after training episode 2,000,000,
  compare each run's mean survival steps (WandB episode-length curve, smoothed over the surrounding
  ~100,000 episodes) with the replication's level-05 run of the same agent and seed at the same
  episode. If it is **below 50%** of that value, stop the run and report; revisit food size or pounce
  reach. (The difficulty check below shows agents not trained here keeping 76–90% of their level-05
  survival, so a learner below 50% is far outside what the world change alone explains.)
- **A test scene too deadly to read:** a run whose newest-20 mean survival in a test scene is **below
  95 steps** has that scene reported, not interpreted (same bound as the single-channel study).
- **Agents hide almost all the time whatever their state:** if a run's bush dwell **with no animal
  exceeds 90%** (unhurt or injured), its contrasts are reported as **at ceiling** and not interpreted —
  the interaction cannot show; design failure (hiding still too cheap or the pounce too deadly).
- **Get bitten, then heal and hide** — the likeliest failure, carried from the scarcity study's
  preceding step (below). With bush healing kept at 25×, an agent can ignore animals, take a pounce
  (damage 15–120, half the pounces miss), and then heal quickly on a bush. Injury would then raise
  hiding because hiding heals, equally with or without a rabbit, and the interaction stays near zero.
  Readout that identifies it: the share of bush time that starts within ~10 steps of a hit, and the
  injury effect computed separately for the no-animal and rabbit scenes — equal injury effects with
  hiding concentrated after hits are read as this failure, not as absence of hypervigilance in
  general.
- **The two seeds disagree in sign**: inconclusive at two seeds; add seeds before drawing anything.
- **Training instability** (NaN, value explosion): the run is bad, not the hypothesis; rerun.

## Test scenes needed (not written yet)

The existing test scenes for the replication (the sweep specs under `configs/eval_sweeps/healrep/`
and `healrep_noheal/` — the "no-temperature" and "training-like" scene sets, and the injury grid
built from `behavior_probes/injury_grid/`) place animals with the **old** smells, the **old**
predator noticing and pounce ranges and **12-bite** food. Run in those scenes, the new agents would
meet animals they never trained on. New test specifications must have:

1. **Same smell for both animals** in every scene (`[0, 0.6, 0.6, 0, 0]`, spread `[0, 0.3, 0.3, 0, 0]`),
   so a scene's "rabbit" condition is the same stimulus the agent was trained on.
2. **The close-range predator** in the predator conditions (notices at 3, pounces from 3, success 0.5,
   cooldown 1–3), so the agent faces the danger it learned.
3. **Food present in every scene, with 6-bite items**, placed away from the bush, so hiding has a cost
   in the test as in training (otherwise dwell measures only safety, not the trade-off).
4. **The same four conditions as the existing injury tests**: injured vs unhurt × rabbit vs no animal
   (plus predator conditions as a positive control that the agent hides from real danger at all).
5. **A per-encounter measure**: for each time an animal first comes within 3 cells of the agent
   (Manhattan distance, the predator's danger zone), record what the agent does over the next few
   steps — moves to / stays on a bush, keeps feeding, or moves away — split by injury and by animal
   kind. This is the closest measure to "how does the agent react to an animal it cannot identify",
   and it does not depend on how often animals happen to wander near.
6. Both the "no-temperature" variant (temperature system neutralised, as in the existing sets) and the
   "training-like" variant (scene built on this world, with a campfire beside the bush), so results
   compare with the replication's existing readouts.
7. **Cue-use readout (planned, 2026-10-09).** In the rabbit scenes, split every 3-cell encounter of
   item 5 by whether the rabbit's **last one or two moves before it came within 3 cells included a
   diagonal step** (only the rabbit ever wanders diagonally). If the agent's reaction (bush within
   the next few steps, keeps feeding, moves away) differs between the two groups, the agent is using
   the movement cue, and the "cannot tell the animals apart" premise holds only for the non-diagonal
   encounters; the interaction is then also reported on non-diagonal encounters alone. A matching
   split for predator scenes is not possible (the wandering predator never steps diagonally), so the
   predator scenes report the return-to-centre mode share and the predator's share of time within 2
   cells of the centre instead, to show whether the second movement cue (walking back to the centre)
   is common for trained agents.
8. **Frozen before reading.** The test-scene specifications are written and committed **while the four
   runs train, before any checkpoint of these runs is evaluated**, and the commit SHA is recorded here.
   Any later change to a scene is a new, separately named scene set, never an edit of the frozen one.

   Frozen test-scene commit: *(to be filled when the specs are written)*.

## Verification record (2026-10-09)

Through `train.py`'s own assembly order (default config → train defaults → rPPO train defaults →
evaluation defaults → logger → visualization → `load_env_config(--config)` → agent config), level 05
vs the new world:

```
environment.entities[pred].attack_range[0]: 2 -> 3
environment.entities[pred].detection_range[0]: 1 -> 3
environment.entities[pred].detection_range[1]: 7 -> 3
environment.entities[pred].properties[1]: 0.7 -> 0.6
environment.entities[pred].properties[2]: 0.5 -> 0.6
environment.entities[rabbit].properties[1]: 0.5 -> 0.6
environment.entities[rabbit].properties[2]: 0.7 -> 0.6
environment.resources[food].max_consumption: 12 -> 6
(596 leaf keys in each)
```

Environment parameters the simulator actually uses (`load_env_params`, 222 fields compared) differ
only in `res_max_cons` (food slots 12 → 6), `animal_property` (all four animal slots →
`[0, 0.6, 0.6, 0, 0]`), `animal_detect_low/high` (predator slots 1/7 → 3/3) and
`animal_attack_range_low` (2 → 3). Observation width 58 in both worlds. Today's resolution of level 05
is identical, environment-side, to the saved configs of the replication's level-05 runs. A
256-episode random-action rollout ran without error; every predator drew pounce reach 3, and at the
step a predator switched to hunting, the agent was at distance ≤ 3 in all 1,360 cases.

## Difficulty check before launch (2026-10-09)

**Question.** Is the new world so much harder than level 05 that survival would collapse? Before
spending four 10M-episode runs, the already-trained level-05 agents of the fast-heal replication (the
ordinary and the modulated agent, seeds 42 and 43, final checkpoints) play 200 episodes each in level 05
and in the new world, at the training episode length (500 steps).

**What this can and cannot say.** These agents learned level 05: they have never seen same-smelling
animals, a predator that pounces the moment it notices them, or 6-bite food, and they cannot learn
during the test. Their drop in survival therefore **overstates** how hard the world is for an agent
trained in it — it is an upper bound on difficulty, not a forecast of the new runs. A small drop is
reassuring; a large drop is a warning, not proof.

**Reading rule (written before any result was looked at).** Primary policy mode: actions sampled from
the policy, as during training (deterministic best-action runs reported alongside). Per agent
(checkpoint):

- **Survival ratio** = mean survival steps in the new world ÷ the same agent's mean survival steps in
  level 05.
- **Predator-death share** = share of new-world episodes that end in an injury death with a predator
  pounce landing in the last 3 steps (injury damage is spread over 3 steps, so a fatal pounce shows up
  within that window).

An agent **fails** the check if its survival ratio is **below 0.60** or its predator-death share is
**above 25%**. The world is called **too hard** (do not launch; revisit food size or pounce reach) if
**3 or more of the 4 agents fail**; **borderline** (launch, and watch the 2M-step abort rule below
closely) if 1–2 fail; **fine** if none fail.

Why these numbers: 0.60 allows the expected drop from two un-learnable changes (halved food items
and a pounce with no visible approach) while flagging a world in which a competent level-05 forager
loses close to half its life; a learner that can adapt should do better than this. 25% predator
deaths means one episode in four ends by a pounce before the agent has any chance to learn the new
cues; above that, early training would be dominated by dying, which is the "survival collapses"
failure mode below. The 3-of-4 aggregation stops a single unlucky checkpoint from deciding.

Results: see "Difficulty check — results" below.

### Difficulty check — results

**Headline.** Survival does not collapse: the four level-05 agents keep **76–90%** of their level-05
survival in the new world (sampled actions). But **every agent fails the pre-stated rule** on the
second criterion: 44–48% of new-world episodes end in a predator-pounce death, above the 25% bar —
so by the rule as written the world is **too hard**. The bar was set without first checking the
level-05 value, and it turns out that the same agents in their **own** world already die by pounce in
32–38% of episodes (they would fail the 25% bar at home). The rule is not changed here; the
observation is recorded so the user can decide whether to launch anyway, change the world, or re-state the bar (a re-stated bar would be a post-hoc change and must be labelled as one).

What changes between worlds, per agent: survival −25 to −60 steps, predator-pounce deaths +8 to +12
points, pounce hits per episode +0.16 to +0.36, episodes reaching the 500-step limit −8 to −15
points; starvation and bush time barely move (food at 6 bites did not starve these agents, and they
did not hide more).

**Verification that the given world was simulated.** The tool is the project's offline evaluation
rollout (`scripts/eval/eval_rollout.py --batched`, which accepts any world config and checkpoint),
called unchanged from a driver (`tmp/20261009_lookalike_difficulty/driver.py`) that wraps its
parameter loader and saves the parameters actually used in each run next to its output
(`resolved_params.json`). All 8 new-world runs used food 6 bites, predator noticing 3–3, pounce reach
3, and smell `[0, 0.6, 0.6, 0, 0]` for all four animal slots; all 8 level-05 runs used 12 bites,
noticing 1–7, reach 2–3, and the two distinct smells. Episode limit 500 in both.

**Method.** Node 110 (RTX 3090), 2026-10-09 17:47–17:51 KST, after the reading rule above was written.
Checkpoints: the final checkpoint (~10M episodes) of the replication's level-05 runs, ordinary and
modulated agent, seeds 42 and 43. 200 episodes per agent and world, the evaluation's fixed 200 reset
seeds (identical starts across agents and worlds), observation noise as in training. Death cause:
the environment's termination code; injury deaths are split into "predator pounce" when a predator
hit landed in the last 3 steps and "other injury" (ambush bush, rocks) otherwise.

Sampled actions (primary):

| agent | world | mean survival (95% CI) | reached 500 | pounce death | other injury | starvation | cold | pounce hits / ep | bush time |
|---|---|---|---|---|---|---|---|---|---|
| ordinary s42 | level 05 | 258 ± 28 | 34% | 32% | 4% | 29% | 1% | 1.10 | 36% |
| ordinary s42 | new | 215 ± 28 | 26% | 44% | 6% | 22% | 2% | 1.32 | 34% |
| ordinary s43 | level 05 | 242 ± 28 | 34% | 35% | 3% | 28% | 0% | 0.98 | 39% |
| ordinary s43 | new | 217 ± 27 | 24% | 44% | 1% | 30% | 1% | 1.34 | 37% |
| modulated s42 | level 05 | 250 ± 28 | 33% | 36% | 2% | 26% | 3% | 1.04 | 36% |
| modulated s42 | new | 198 ± 26 | 20% | 44% | 4% | 30% | 1% | 1.20 | 33% |
| modulated s43 | level 05 | 251 ± 29 | 35% | 38% | 4% | 23% | 0% | 1.00 | 33% |
| modulated s43 | new | 191 ± 26 | 20% | 48% | 6% | 23% | 3% | 1.16 | 33% |

Over-eating deaths: 0 in every cell. Rule check (sampled actions): survival ratio 0.83 / 0.90 / 0.79 /
0.76 (all pass ≥ 0.60); pounce-death share 44 / 44 / 44 / 48% (all fail ≤ 25%) → 4 of 4 agents fail →
**too hard** by the pre-stated rule.

Best-action (deterministic) runs, for comparison: survival ratio 0.84 / 0.88 / 0.86 / 0.86, pounce-death
share 50 / 42 / 45 / 46% (level 05: 36 / 33 / 36 / 36%), pounce hits per episode 1.22–1.46 (level 05
0.97–1.09). Same picture. Full tables: `tmp/20261009_lookalike_difficulty/summarize.py` output.

## Results / Conclusions

To be filled after training and testing.

## Links

- [[FAST_HEAL_REPLICATION]] — the level-05 reference runs and agent settings.
- [[NMN_INPUT_L05]], [[NMN_CAPACITY_GRID_L05]] — the other current level-05 hypervigilance follow-ups.
- `docs/environment/CONFIG_CRITICAL_SETTINGS.md` — change-log entry of 2026-10-09 for this world.
- Earlier attempts compared in "How this differs from earlier attempts": [[sameprop_round2_design]],
  [[sameprop_discriminating_channels]] (§4), [[20260620_hypervig_scarcity_olfactory_ambiguity]],
  [[SINGLE_CHANNEL_SMELL_HYPERVIGILANCE]] (estimator: §Pre-stated reading, item 2).
- Difficulty-check and simulation working files (gitignored): `tmp/20261009_lookalike_difficulty/`
  (`driver.py`, `run.sh`, `summarize.py`, `mode_sim.py`, `out/`).

## Launch decision (2026-10-09)

The difficulty check failed its own pre-stated pounce-death bar (more than 25 % of episodes) for all four
agents, but that bar was set without checking level 05, where the same agents already die by pounce in
32–38 % of episodes. Survival held at 76–90 % of level 05, so it did not collapse. The user's instruction
was to launch after the check unless survival collapsed, so the four runs were launched. The 25 % bar is
**not** re-stated; this launch is recorded as a decision against a failed pre-stated rule, not as a pass.
