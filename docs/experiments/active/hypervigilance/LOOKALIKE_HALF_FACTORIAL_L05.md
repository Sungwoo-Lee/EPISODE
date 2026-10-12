---
title: Lookalike half-factorial at level 05 — which world changes make hiding affordable and pain unexpected
topic: hypervigilance
status: active
created: 2026-10-11
last_updated: 2026-10-12
wandb_tag: rppo_lookalike_hf_l05
---

# Lookalike half-factorial at level 05

## Question

In the current training world (level 05 with lookalike animals: a cold 10×10 map with campfires,
bushes, a hunting predator and a harmless rabbit that smell identical), agents die from the predator
mostly **while foraging**. An analysis of 27 million recorded level-05 episodes (2026-10-11) found
the reason: small food items force the agent to keep going out to eat, so hiding in a bush costs
food. Under those conditions there is little room for caution, and none for the behaviour this
project is looking for: an injured agent hiding more when an ambiguous animal is around.

The user wants a world where **hiding is affordable** and where **pain can come without warning**.
Four groups of world settings could get there. Each is tried at its current value ("−") and at a
new value ("+"):

- **A. Predator threat**: always exactly one predator (now 0–2, the same average), which notices
  the agent and pounces from 2–3 cells instead of always 3.
- **B. Food economy**: fewer but much bigger food items. A meal takes about 7 eating steps instead
  of about 25, so the agent makes fewer, shorter trips out. It does **not** give a bigger reserve
  after a meal (see "Food").
- **C. Hazard concealment**: the hidden trap and the rocks become completely invisible, so a hit is
  a true surprise. This also removes them from the agent's view of the map, so C is "concealment
  plus less visual clutter".
- **D. Hazard load**: fewer rocks and fewer traps, but traps hurt more.

Trying all 16 combinations would take 32 training runs. This experiment uses a standard **half
factorial**: 8 of the 16 worlds, chosen so that each group's effect can still be estimated by
comparing the 4 worlds where it is new with the 4 where it is not. One of the 8 is the existing
lookalike world, already trained, so **7 new worlds × 2 agents (ordinary and modulated) = 14 new
runs**, one seed each, 10 million steps.

Each group has **one pre-registered behavioural readout**, defined so that it cannot be moved by
the world change alone:

- **Food (B):** how much more dangerous each step spent eating is than other time in the open
  (predator deaths per step while eating ÷ per step otherwise).
- **Threat (A):** time in a bush while unhurt, with the harmless rabbit close and no predator
  near.
- **Concealment (C):** the reaction to a rock hit when rocks are hidden versus visible.
- **Hazard load (D):** the hypervigilance pattern.

It is a **screen**: one seed, eight worlds. It picks the groups worth replicating with more seeds.
It confirms nothing on its own. Level 06 (level 05 plus thirst and a pond) follows later with the
same design.

## The eight worlds

| World | A threat | B food | C concealment | D hazard load | Config | Trained? |
|---|---|---|---|---|---|---|
| 1 | − | − | − | − | the lookalike world itself | **already trained**, reused (see "World 1 reuse") |
| 2 | + | − | − | + | `lookalike_hf_w2_newAD_10x10.yaml` | new |
| 3 | − | + | − | + | `lookalike_hf_w3_newBD_10x10.yaml` | new |
| 4 | + | + | − | − | `lookalike_hf_w4_newAB_10x10.yaml` | new |
| 5 | − | − | + | + | `lookalike_hf_w5_newCD_10x10.yaml` | new |
| 6 | + | − | + | − | `lookalike_hf_w6_newAC_10x10.yaml` | new |
| 7 | − | + | + | − | `lookalike_hf_w7_newBC_10x10.yaml` | new |
| 8 | + | + | + | + | `lookalike_hf_w8_newABCD_10x10.yaml` | new |

Each filename carries the world number and the groups at their new value (`newAD` = A and D new).
All files live in `configs/environment/experiment/basic/` and extend the lookalike world
(`lookalike_animals_close_pounce_small_food_10x10.yaml`, design in [[LOOKALIKE_ANIMALS_CLOSE_POUNCE]]).
D's sign is set by the rule D = A × B × C (the product of the other three signs). That rule is
what makes this the standard 2⁴⁻¹ half factorial.

### Exact values

| Group | Setting | − (now, lookalike world) | + (new) |
|---|---|---|---|
| A | predator `detection_range` (cells; drawn per predator per episode) | [3, 3] | [2, 3] |
| A | predator `attack_range` (pounce reach; drawn independently) | [3, 3] | [2, 3] |
| A | predator count per episode (`count_low`–`count_high`) | 0–2 (mean 1) | **exactly 1** |
| B | food items per episode | 1–4 | 1–3 |
| B | food `max_consumption` (bites per item) | 6 | 9 |
| B | `body.food_nutrition_gain` (gross per bite) | 6 | 16 |
| B | → net nutrition per eating step (gain − 1 eating cost − 1 metabolic cost) | +4 | +14 |
| B | → nutrition in one full item | ≈ 24 | ≈ 126 |
| C | `visual_mask` on the trap (`hiding_predator` resource) and on the rock obstacle | absent (visible) | `all` (never visible) |
| D | rock count | 6–12 | 4–8 |
| D | trap count | 2–12 | 3–6 |
| D | trap damage | 15–45 | 25–60 |

Unchanged in every world:

- **Predator and rabbit.** Predator damage 15–120, pounce cooldown 1–3 steps, stamina 30–150,
  pounce success 0.5, the lookalike smell. The rabbit stays at 0–2 with the same smell.
- **Hazards.** Rock damage 1–5. Both hazards carry the same pain signal (0.9) and no smell.
- **Body rules.** Bush healing stays 25× faster in a bush (user rule: never change training bush
  healing). `overeating_death: true` (death at nutrition ≥ 200). Eating needs the eat action.
- **World.** The 10×10 grid, 500-step episodes, the cold air and 1–3 campfires. Random start
  position, nutrition, injury and body temperature.

### What each group changes, and what it tests

- **A (predator threat).** The 27 M-episode analysis says predator deaths are the main cost of
  being out. A+ changes the predator's **sight and pounce reach**: some predators notice the agent
  only at 2 cells. It also changes the **spread** of the predator count: always 1 instead of
  0, 1 or 2. The average count stays 1, but episodes with two predators and episodes with none both
  disappear. The rabbit count is unchanged. Tests: *does a more predictable, less concentrated
  threat change how cautious the agent is around animals when it has no wound to heal?*
- **B (food economy).** The reward pulls nutrition toward 100, and eating to 200 kills. So a bigger
  item does **not** let the agent store a bigger reserve: after a meal it is still about 100 steps
  from starving, as today (env-config review, 2026-10-12). What B changes is the **cost of a meal**.
  Refilling from near-empty to 100 takes about 7 eating steps instead of about 25. It also needs
  one item instead of about four, so there are fewer trips across the map. Tests: *does making each
  meal shorter and cheaper move predator deaths away from foraging?*
- **C (hazard concealment plus less visual clutter).** Today the trap and rocks are visible. Vision
  here has a single channel that only shows that a cell is occupied, so they appear as occupied
  cells, and a careful agent can learn where not to step. Masked, they leave no trace in vision or
  smell, and the only signal is contact pain on the step the agent stands on one. Masking also
  removes up to 24 occupied cells from the agent's view, which makes food, animals and bushes
  stand out. So **C+ is concealment plus less visual clutter, and the two cannot be separated
  here**. Tests: *is a hit the agent could not predict followed by a different reaction than the
  same hit when it was visible?*
- **D (hazard load).** Fewer hazards with heavier trap hits. The mean trap count falls from 7 to
  4.5 and the mean trap damage rises from 30 to 42.5, so the expected total trap damage on the map
  is roughly unchanged (≈ 210 → ≈ 191). Each hit is larger and rarer. Tests: *do rarer, bigger
  injuries change the injury-dependent part of the agent's caution?*

## Mechanics the reader must know

### Pounce reach and sight are drawn independently (group A)

The rules come from `src/environment/core.py`, `_hunt_step`:

- A predator starts hunting when the agent is within its noticing distance (`detection_range`) and
  not in a bush.
- It pounces only **while hunting**, and only when the agent is within its pounce reach
  (`attack_range`).
- It stops hunting when the agent is in a bush, when its stamina runs out, or when the agent is
  farther away than noticing distance × 1.5 (`lose_interest_multiplier`).

Under A+, each episode draws the predator's noticing distance and pounce reach independently from
{2, 3}, so four kinds of predator are equally likely:

| Notices at | Pounces from | What the agent experiences |
|---|---|---|
| 3 | 3 | as in world 1: the first move toward the agent is the pounce |
| 2 | 2 | the same, one cell closer |
| 3 | 2 | notices at 3 and takes **one visible step** toward the agent before it can pounce. This is a short approach cue that the lookalike world had removed |
| 2 | 3 | notices at 2. Reach 3 matters only **mid-chase**: if the agent flees from 2 to 3 cells, the predator is still hunting (it loses interest only beyond 2 × 1.5 = 3 cells) and can still pounce from 3 |

So in a quarter of episodes, A+ partly restores the "watch it approach" cue. That is part of what
group A changes.

### Food is a fixed approximation (group B)

The user asked for 120–160 nutrition per item and 10–20 per bite. The environment has **no
per-item or per-bite random draw**. `body.food_nutrition_gain` is one number for the whole body,
and `max_consumption` is a fixed integer per resource entry. So B+ uses fixed values: 16 gross per
bite and 9 bites.

The metabolic cost (1.0 per step) is also charged on the step the agent eats (`core.py:266` and
`:321`). An eating step therefore nets **+14** (16 − 1 eating cost − 1 metabolic cost), about 126
per item. Getting a real random draw would need a code change (a new mandatory key), which is not
in scope.

Side effect: over-eating kills at nutrition ≥ 200, so a single bite now kills from **186** upward
(today from 196). Start nutrition is drawn uniformly from 0–200, so **7.0 %** of episodes start
inside that band (today 2.0 %). Eating is a deliberate action, so the agent can learn to wait.
Over-eating deaths are reported as an ending, not treated as a design flaw.

## What the ideal planner predicts (rebalance planner, 2026-10-11)

A parallel study solved each of the eight worlds with an ideal planner. The planner chooses the
best action from the true body dynamics and the true map, before any agent is trained. Results are
in `docs/experiments/active/rebalance_planner/figures/results.json`.

- **Verdict: no world offers a real choice** by that study's pre-registered rule, which needs
  hiding best in ≥ 20 % and foraging best in ≥ 20 % of start states.
  - Hiding is the best choice in 62–77 % of start states.
  - Foraging is best in 7–16 %.
  - Hiding wins whenever injury is above about 20. Foraging wins only when food is below about 70
    and injury is low.
  - Bush healing is fast, so the planner heals first and eats second.
- **Group effects on the share of start states where foraging is best:** A +2.2, B +4.1, C −3.1,
  D −0.2 percentage points. These were computed on the configs of 2026-10-11, where A+ had 0–1
  predators. The A effect was not recomputed for "exactly 1".

What this implies for reading the trained runs:

1. **Expect a lot of bush time in every world.** Raw bush share will sit near its ceiling and
   compress the differences between worlds. That is one more reason why no primary readout below
   uses raw bush share.
2. **Healing will dominate bush time after any injury.** The planner heals before it eats. So
   separating hiding from healing (next section) is necessary, not optional.
3. **The planner's signs are a reference direction.** B and A should make the trained agent forage
   somewhat more, and C somewhat less. A trained-run effect clearly opposite to the planner's sign
   points to a learning problem or to something the planner does not model (for example the agent
   not knowing where hidden hazards are). It is reported as such, not as a finding about the world.
4. **The screen is not expected to produce a world with a real hide-or-forage choice.** If that
   choice is the goal, the lever is probably outside these four groups. Bush healing is the obvious
   one, and the user has ruled out changing it.

## Verification record (2026-10-11, re-run 2026-10-12 after the predator-count change)

All checks used `train.py`'s own assembly order: default config → train defaults → rPPO train
defaults → evaluation defaults → logger → visualization → `load_env_config(--config)` → agent
config. They ran on CPU, on the working tree at `5f6af25f` plus these uncommitted configs. The
scripts are in the session scratchpad and are not committed.

**Every world loads, resets and steps.** `load_env_params`, `jax_reset` and 5 × `jax_step` ran
without errors. The observation is 58 numbers wide in every world, the same as world 1, so the
agents' input layer is unchanged.

**Intended values, read from the loaded simulator parameters (not from the YAML):**

| World | food items / bites / gross gain | predators: count range → active in 300 starts / notices / pounces | traps: count / damage / hidden | rocks: count / hidden |
|---|---|---|---|---|
| 1 | 1–4 / 6 / 6 | 0–2 → 0: 107, 1: 106, 2: 87 / 3–3 / 3–3 | 2–12 / 15–45 / no | 6–12 / no |
| 2 (AD) | 1–4 / 6 / 6 | **1–1 → 1 in all 300** / **2–3** / **2–3** | **3–6 / 25–60** / no | **4–8** / no |
| 3 (BD) | **1–3 / 9 / 16** | 0–2 → as world 1 / 3–3 / 3–3 | **3–6 / 25–60** / no | **4–8** / no |
| 4 (AB) | **1–3 / 9 / 16** | **1–1 → 1 in all 300** / **2–3** / **2–3** | 2–12 / 15–45 / no | 6–12 / no |
| 5 (CD) | 1–4 / 6 / 6 | 0–2 → as world 1 / 3–3 / 3–3 | **3–6 / 25–60 / yes** | **4–8 / yes** |
| 6 (AC) | 1–4 / 6 / 6 | **1–1 → 1 in all 300** / **2–3** / **2–3** | 2–12 / 15–45 / **yes** | 6–12 / **yes** |
| 7 (BC) | **1–3 / 9 / 16** | 0–2 → as world 1 / 3–3 / 3–3 | 2–12 / 15–45 / **yes** | 6–12 / **yes** |
| 8 (ABCD) | **1–3 / 9 / 16** | **1–1 → 1 in all 300** / **2–3** / **2–3** | **3–6 / 25–60 / yes** | **4–8 / yes** |

These are the loaded fields:

| What | Loaded fields |
|---|---|
| Counts | `res_count_low/high`, `animal_count_low/high`, `obs_count_low/high` |
| Food | `res_max_cons`, `food_nutrition_gain` |
| Predator | `animal_detect_low/high`, `animal_attack_range_low/high` |
| Trap damage | `res_damage` |
| Hidden | `res_visual_mask` and `obs_visual_mask` = 2 ("never visible") on every trap and rock slot, and 0 on the campfire, tree and bush slots |
| Active animals | `animal_active` after `jax_reset`, over 300 random starts |

The rabbit counts after a reset are identical in all eight worlds: 95 / 89 / 116 starts with
0 / 1 / 2 rabbits.

In all eight worlds, `eating_nutrition_cost` 1.0, `metabolic_cost` 1.0, `max_nutrition` 200,
`overeating_death` true and `recovery_in_bush_multiplier` 25 are identical.

Every resource, obstacle and predator entry was also compared with world 1 field by field (the
smell and sight properties, pain, spawn areas, bush `hides_agent` / `blocks_animals`, campfire
temperature, predator stats). Only the intended changes differ.

**Concealment works on the observation, not only in the parameters.** For worlds 5–8, 300 starts
each, two observations of the same state were compared: one with the hidden traps and rocks present,
and one after removing every trap and rock. They differed **only in slot 3, the contact pain signal
("Extero Nociception"), and only when the agent started standing on a trap or rock** (40–54 of 300
starts). Nothing differed in vision or smell. In world 1, where they are visible, un-masking always
changes the observation. So under C+ a hazard is detectable only by stepping on it.

## World 1 reuse

World 1 is not retrained (user decision, 2026-10-12). The two seed-42 runs of the lookalike pilot
serve as its cell:

- `results/JAX_RecurrentPPO/20261009-175459_rppo_lookalike_l05_t1none_s42` (ordinary agent)
- `results/JAX_RecurrentPPO/20261009-175502_rppo_lookalike_l05_t16quad_s42` (modulated agent)

Both were launched on 2026-10-09 from commit `1f1b7b26` (recorded in their `provenance.json`).
That is the commit that created the lookalike world. Reuse conditions, checked 2026-10-11:

1. **No world-behaviour commit since.** `git log --since=2026-10-09` on `src/environment`,
   `configs/environment/default.yaml`, level 05 and the lookalike config is **empty**.
   `git log 1f1b7b26..HEAD` on all of `src/`, `configs/` and `train.py` shows two commits, both
   adding test-scene configs (`abd52e45`, `e509d743`). Neither touches the training world or any
   code. There are no uncommitted changes under `src/`, `configs/` or `train.py`.
2. **The saved world config equals today's.** The world-side sections (`environment`, `body`,
   `sensory`, `thermal`, `water`, `perceptual_noise`) of both runs' saved `models/config.yaml` match
   today's assembly of the lookalike world: 191 leaf keys, 0 differ.
3. **Same agent and training settings.** Today's full assembly with each agent config differs from
   the saved config only in the command-line keys (episodes, log interval, tag, WandB
   name/group/job type). The launch lines below therefore reproduce the world-1 training settings
   exactly.
4. **Launch-morning re-check (required; plan review M4a).** Immediately before launch, both of the
   following must print nothing that changes behaviour:
   - `timeout 120 git log 1f1b7b26..HEAD --oneline -- <paths>`
   - `timeout 120 git status --porcelain -- <paths>`

   `<paths>` is:
   - `src/` and `train.py`;
   - the training layers: `configs/train/default.yaml`, `configs/train/recurrent_ppo.yaml`,
     `configs/evaluation/default.yaml`, `configs/logger/wandb.yaml` and
     `configs/visualization/default.yaml`;
   - the world layers: `configs/environment/default.yaml`, `basic/03`, `basic/04`, `basic/05` and
     the lookalike config;
   - both agent configs: `configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml`
     and `nmngaenorm_t16quad_ALL.yaml`.

   A behaviour-changing commit means world 1 is retrained alongside the others, with the same seed
   and the same flags (2 extra runs).
5. **Same class of card.** World 1 trained on node 110 (RTX 3090). The 14 new runs launch on
   RTX 3090-class nodes (106–112).

   **Deviation at launch (2026-10-12, user decision).** Most 3090s were in use by another lab
   member, so the runs went two per card: worlds 2, 6, 7 and 8 on RTX 3090s (nodes 107 and 112),
   and worlds 3, 4 and 5 on RTX 6000 Ada cards (node 114). Both agents of a world share one card
   type, so the within-world ordinary-versus-modulated comparison is not affected by the card. The
   Ada set {w3, w4, w5} puts one or two of each group's four "new" worlds on Ada, so no group
   contrast lies wholly on one card type. Card type can change floating-point results slightly. That
   is expected to be far smaller than seed-to-seed variation, but it is listed here as one more
   possible source of the offset δ described below.

**Known limitation (plan review M4b): world 1 sits on the "old" side of every group contrast.**
Any systematic difference between the two world-1 runs and the new batch moves all four group
effects by the same amount. Possible sources are a different launch day and node, GPU
nondeterminism, or a change missed by the re-check. A shift δ in world 1 moves every group effect
by −δ/4 and every interaction pair by ±δ/4. Checks 1–5 exist to make δ zero apart from GPU
nondeterminism. The residual is accepted, not estimated. The world-1 runs are in WandB group
`lookalike_animals`, not this experiment's group, so the analysis must pull from both groups.

## Experimental design

- **Independent variables:** the four groups A–D, at − / + across the 8 worlds above; and agent
  type: ordinary (`nmngaenorm_t1none`) and modulated (`nmngaenorm_t16quad_ALL`), the same pair as
  the lookalike runs.
- **Fixed:** everything listed under "Exact values → unchanged". Agent and training settings are
  identical to the lookalike runs. Seed 42. 10 M steps (`--episodes 10000000`, the same flag the
  lookalike runs used).
- **Seeds:** **one** (user decision). The project rule is ≥ 3 seeds for any confirmation, so this
  experiment confirms nothing on its own. Its job is to screen four groups for 14 runs. Every
  conclusion is worded as "worth replicating" or "not worth replicating".
- **What the design can and cannot separate.**
  - A 2⁴⁻¹ design with D = ABC is "resolution IV": each group's main effect is estimated cleanly if
    three-group interactions are negligible.
  - The two-group interactions come in **inseparable pairs**: A×B with C×D, A×C with B×D, and A×D
    with B×C. For example, if trap concealment matters only when food is plentiful (B×C), the
    design cannot tell that apart from A×D.
  - The 8 worlds give 7 contrasts (4 main effects and 3 interaction pairs) and nothing left over to
    estimate noise. The noise level is therefore taken from other runs (next section).
- **Compute:** the world-1 runs took ≈ 12.7 h (ordinary agent) and ≈ 16.7 h (modulated agent) on
  an RTX 3090. The 14 runs need ≈ 205 GPU-hours, about 17 h of wall time on 14 RTX 3090-class GPUs
  (7 nodes × 2, filling one node before the next).

## Outcome measures (pre-specified)

### Definitions

These definitions are shared by all readouts.

- **In a bush:** the agent is on an active bush cell (`agent_in_bush`).
- **Hiding step:** in a bush **and** either injury < 1 point or the action was not "rest".
  **Healing step:** in a bush, the action was "rest" and injury ≥ 1. Bush healing applies only on a
  step where the agent rests in a bush and takes no damage (`core.py`,
  `can_recover = rested & applied_inc <= 0`). So a non-resting bush step, or any bush step at
  injury 0, cannot be explained by healing. Hiding and healing are always reported separately.
  Raw bush share is reported only as context.
- **Animal in view:** at least one animal (predator or rabbit) within Manhattan distance 2. That is
  the agent's 13-cell sight diamond (`visual_sensor_range` 2).
- **Activity states:** each out-of-bush step is in one of three states.
  - (i) **eating-recent:** the agent ate within the last 20 steps;
  - (ii) **heading to food:** not (i), and the step moved the agent closer to the nearest active
    food;
  - (iii) **other**.

  States (i) and (ii) are always kept **separate**, never merged into one "foraging" state. The
  definitions follow the 27 M-episode analysis. Note that B changes how often the agent eats: a
  meal is about 7 eating steps instead of about 25, and the agent needs fewer items. So under B+
  state (i) covers a different fraction of time for purely mechanical reasons. Every death share
  below is therefore reported next to the **time share** of the same state (the share of
  out-of-bush steps in it). A drop in the death share that only mirrors a drop in the time share
  is read as "less time foraging", not as "safer foraging".
- **Hazard-hit event (plan review M3):** a step on which the agent takes rock (or trap) damage
  **on a cell it entered on that step**, that is, the first damage step after moving onto the
  cell. Further damage steps from standing still on the same cell are not new events. Step 0 is
  excluded, because the agent can start on a hazard (13–18 % of starts in the concealed worlds).
  Steps where a predator also hit the agent are excluded. The response window is the 20 steps after
  the event, compared with the 20 steps before it. **Events cut short by death** (the episode ends
  within 20 steps) are counted and reported per world, as a number and a share. The response is
  computed on complete windows only, with the truncated-window version reported beside it.

### Primary readouts, one per group (plan review C1)

| Group | Primary readout | Why this one cannot be moved by the world change alone |
|---|---|---|
| **B food** | **(a) Foraging risk ratio** (re-review R1). For each run: (predator deaths whose fatal hit came in state (i), eating-recent ÷ steps in state (i)) **÷** (predator deaths in state (iii), other out-of-bush ÷ steps in state (iii)). The same ratio for state (ii), heading to food, is reported separately, against the same reference state (iii). The group effect is computed on the **logarithm** of the ratio | Deaths are divided by the time spent in each state, so the shorter meals of B+ cannot lower the readout just by cutting eating time. The ratio is taken inside one world, so the world's overall predator rate (moved by A) cancels. It moves only if eating becomes more or less dangerous **per step** than other time in the open. This is the user's headline problem |
| **A threat** | **(b) Unhurt caution near the lookalike** (re-review R2) = share of steps in a bush, among steps with injury < 1, **the rabbit within 2 cells and no predator within 4 cells** | At injury < 1 there is nothing to heal, so bush time is caution, not healing (plan review C2). With no predator within 4 cells, the bush time is a response to an ambiguous animal that is in fact harmless, not an escape from a real threat. Fewer or different predators (A) do not enter these steps directly |
| **C concealment** | **Surprise response** = (change in hiding-step share in the 20 steps after a **rock** hit, minus the 20 before) in C+ worlds **minus** the same in C− worlds. Only events where the agent was **unhurt (injury < 1) before the hit** and had **no predator within 3 cells in any of the 20 steps before** are kept (re-review R3). The number of events kept, and the share of all rock-hit events, are reported per run and checkpoint | Rock damage is 1–5 in every world, so the wound, and with it the healing motive, is the same on both sides. The only difference is whether the hit could be predicted (plan review C2). Hiding steps exclude resting-to-heal. The filters remove hits taken while already wounded or while fleeing a predator, where bush time would have other causes |
| **D hazard load** | **(c) Hypervigilance pattern** = the injury × rabbit interaction on bush dwell in the experiment's test scenes: (injured − unhurt, rabbit) − (injured − unhurt, no animal), with the rabbit effect on unhurt agents as its check, exactly as defined in [[LOOKALIKE_ANIMALS_CLOSE_POUNCE]] §"What would count as a clue" | D changes how often and how badly the agent is hurt, so its target is the injury-dependent part of caution. The test scenes fix the injury and the animal, so the world's hazard rate does not enter the measure |

The assignment of readout (c) to D is the weakest link in this table: D has no behavioural target
of its own. See "Open decision for the user" below. Every primary readout is also **reported for every group**
as a secondary result, and secondary results cannot make a group "worth replicating".

### Secondary and descriptive readouts

- **Surprise response, other parts:** after a rock hit, the change in rest-in-bush share (healing),
  cells moved, and whether the agent steps on the same cell again within 20 steps. Each is reported
  for C+ and C− worlds.
- **Trap versus rock, as a difference-in-differences only:**
  (trap − rock response)<sub>C+</sub> − (trap − rock response)<sub>C−</sub>. Events are matched on
  injury after the hit, in 10-point bins compared within bin, so the healing need is the same on
  both sides. The overlap is reported per bin, because rock events seldom reach high injury. A raw
  trap-minus-rock gap in C+ worlds is **not** a concealment measure: the wounds differ about
  10-fold. It is never used as one.
- **Endings mix (descriptive only):** the share of episodes ending at full length (500 steps), by
  predator, by trap, by starvation, by over-eating, and by cold or heat. Survival steps (mean
  episode length) are reported as the project's performance measure. Neither is a pass criterion:
  A and B move them by construction.
- **Predator hits and deaths per 1,000 steps by activity state**, with time shares.

### Data

- **Recorded evaluation rollouts** in each run's own training world, at checkpoints 2, 4, 6, 8 and
  10 M. These feed readouts (a), (b) and the surprise response. World 1 uses its existing runs'
  checkpoints at the same steps.
  - At 2 M and 4 M (descriptive only): 2,000 episodes per run.
  - At 6 M, 8 M and 10 M (the checkpoints the decision uses): start at 2,000 episodes per run and
    extend in blocks of 2,000 until the minimums below are met, **up to a cap of 20,000 episodes
    per run per checkpoint** (re-review R1). The number of episodes actually used is reported per
    cell.
- **Minimums per run and checkpoint (re-review R5).** They are counted in **episodes**, because
  steps and events inside one episode are not independent:
  - every readout needs at least **50 contributing episodes** (episodes with at least one
    qualifying step or event);
  - readout (a) also needs at least **100 predator deaths**, with at least 10 in state (i) and 10
    in state (iii).
- **Sampling error (re-review R5).** Every per-run value gets a standard error from a bootstrap that
  resamples **whole episodes** (1,000 resamples), never steps or events.
- **Test-scene sweeps at every saved checkpoint**, using the lookalike pilot's estimator, for (c).
- **WandB training curves** (episode length and termination shares) over the whole run.

### Pass rule: "worth replicating" (plan review M1; re-review R1, R4, R5, R7, R8)

1. **Seed-to-seed noise σ, measured before any contrast here is read (re-review R7).** For each
   primary readout, computed exactly as for this experiment (same checkpoints, same rollout
   rules):
   - **Fast-heal estimate σ_fh.** Use the six level-05 runs of the fast-bush-healing replication
     (seeds 42, 43, 44 × ordinary and modulated; [[FAST_HEAL_REPLICATION]]). Take the standard
     deviation across the three seeds within each agent, then pool the two agents' variances.
     That gives 2 + 2 = 4 degrees of freedom.
   - **Lookalike estimate σ_lk.** Use the lookalike world's two seeds, with both seed-43 runs
     (`20261009-175506_rppo_lookalike_l05_t1none_s43` and `20261009-175510_rppo_lookalike_l05_t16quad_s43`).
     For each agent, the spread is |s42 − s43| / √2. Pool the two agents as the root mean square,
     which gives 2 degrees of freedom.
   - **Rule.** σ = σ_fh, unless σ_lk > 2 σ_fh, in which case σ = σ_lk. (The fast-heal world is
     plain level 05, not the lookalike world, so the lookalike pair guards against a world where
     seeds differ much more.)
   - **For readout (c)**, use the spread already recorded in the critical-settings registry for
     the injury-driven test measure, at its upper end: σ = 2.67 points.
   - **Imprecision, stated plainly.** A standard deviation from 4 degrees of freedom is rough: the
     95 % range for the true σ runs from about **0.6× to 2.9×** the estimate. So the bar below can
     be too strict or too lenient by that factor. This is accepted for a screen, and the estimate
     is reported with that range.
2. **Bar (re-review R1 and R5: the sampling error is folded in).** A group effect is the mean, over
   the two agents, of (mean of the 4 "+" worlds − mean of the 4 "−" worlds). Its noise has two
   parts: seed-to-seed noise and the sampling error of each of the 16 per-run values (the
   episode-bootstrap standard errors SE_i).

   $$
   \mathrm{SD}_{\text{contrast}} = \sqrt{\frac{\sigma^2}{4} + \frac{1}{64}\sum_{i=1}^{16} SE_i^2}
   $$

   The bar is **2 × SD_contrast**. When the sampling errors are negligible, this equals σ (the
   two-agent mean of two 4-against-4 contrasts, each with noise ≈ 0.71σ). For readout (a) the
   values are on the log-ratio scale. If the sampling error is not negligible, it is because a
   world produced few events. The bar then grows and the group is harder to pass, rather than
   passing or failing on a noisy cell.
3. **Decision (re-review R8).** A group is **worth replicating** if both of these hold:
   - its effect on its primary readout, computed on the mean of the 8 M and 10 M checkpoints (for
     (c), the newest-20-checkpoint estimator), exceeds the bar;
   - the effect has the **same sign at each of the 6 M, 8 M and 10 M checkpoints**.

   It is **not worth replicating** if every cell is present and either condition fails.
4. **Unresolved (re-review R4).** If any run of the 16 misses the minimums for that readout at
   6, 8 or 10 M, even at the 20,000-episode cap, the group is **unresolved**, not "not worth
   replicating". Missing data is never read as a null result. The write-up names the world, run
   and checkpoint that fell short.
5. **Agents.** Agreement between the two agents is not required. If one agent's own contrast
   exceeds the bar with the sign opposite to the pooled effect, the group is flagged as
   "agent-dependent".
6. **Interaction pairs** (A×B+C×D, A×C+B×D, A×D+B×C) are reported against the same bar, and are
   never read as one named interaction.

The whole-training view (per-checkpoint values, the share of checkpoints in the same direction,
and the largest jump) is reported beside every number, in line with the project's checkpoint-wise
rule.

## Open decision for the user: test scenes for the hypervigilance readout (re-review R6)

**The mismatch.** Readout (c) is measured in fixed test scenes: a set injury level, with the
rabbit present or with no animal. Those scenes were built and frozen on the **base lookalike world**
(world 1), on 2026-10-10. Agents trained in worlds 2–8 would therefore be tested in a world they
never trained in. For example:

- agents trained with hidden rocks and traps (C+) would suddenly see them as occupied cells;
- agents trained on big food items (B+) would meet 6-bite, 6-gain food;
- agents trained against one predator with 2–3-cell reach (A+) would face the base predator
  settings, insofar as the scenes contain one.

A difference between worlds on (c) could then reflect how well each agent copes with an unfamiliar
world, not its hypervigilance.

**Options (not chosen here):**

1. **Rebuild the test scenes for each world.** Make seven new frozen scene sets, one per new
   world, built the same way as the lookalike set, so each agent is tested in its own training
   world. This costs scene-building and checking work before the analysis. It keeps (c)
   interpretable as a world effect.
2. **Accept the mismatch.** Keep the one scene set for all eight worlds and report (c) with this
   limitation. A group effect on (c) is then read as "hypervigilance as measured in the base
   world", and a world that differs most from the base (world 8) is the most exposed.

**A second, related choice:** whether the hypervigilance pattern should be the primary readout for
**every** group, since it is the study's ultimate target, or stay primary for D only (as now), with
A, B and C keeping their own behavioural readouts. Making it primary for every group would mean four
tests on one readout, and a group could pass on (c) without changing its own target behaviour.
Keeping it for D only leaves D with a readout that is not specific to D.

Both choices are for the user; the design does not pick.

## Failure modes, decided in advance

- **A run diverges or collapses** (NaN, or episode length collapses) in one world. That is a run
  failure: relaunch the same seed once. If it fails again, the world is reported as untrainable at
  these settings. That is a result about the world, not a missing cell to be filled by estimation.
- **A world is trivially safe** (for example world 4 or 8) and survival saturates near 500. That is
  not a design flaw, but it compresses differences. The primary readouts are built not to depend on
  survival.
- **Too few events.** The minimums are at least 50 contributing episodes for every readout, and for
  (a) at least 100 predator deaths (≥ 10 in each of states (i) and (iii)), with evaluation extended
  up to 20,000 episodes. If a run still falls short, that cell is reported as "too few events",
  never as zero, and the group is **unresolved** (pass rule, item 4). Most at risk: readout (a) in
  the safest worlds (4 and 8) and the filtered surprise events in worlds with few rocks (D+).
- **Over-eating dominates the endings in B+ worlds.** It is reported as a cost of the fixed-food
  approximation. If over-eating exceeds 10 % of endings, flag it before B is chosen for a follow-up.
- **The effect is still drifting at 10 M.** Report it as "not settled". It is not resolved by
  running longer inside this experiment.
- **"Get bitten, then heal and hide".** This is the strategy the lookalike design named. It stays
  available because bush healing is unchanged. It shows up as high healing-step share and low
  hiding-step share, which is why the two are separated.

## Launch manifest

WandB group `lookalike_half_factorial`; WandB job type `pilot` (a single-seed screen, the same job
type as the lookalike runs). Tag = WandB name, in the format
`rppo_lookalike_hf_l05_w<world>_<agent>_s42`. Launch on RTX 3090-class cards (nodes 106–112).

| Run | Status | Cell | Tag (= wandb-name) | wandb-group | wandb-job-type | Seed | Node | GPU | Launched at | WandB run ID | Log path |
|---|---|---|---|---|---|---|---|---|---|---|---|
| — | reused | w1 ordinary | `rppo_lookalike_l05_t1none_s42` | `lookalike_animals` | pilot | 42 | 110 | 0 | 2026-10-09T17:54:54 | 272ytkfm | logs/20261009_175454_rppo_lookalike_l05_t1none_s42.log |
| — | reused | w1 modulated | `rppo_lookalike_l05_t16quad_s42` | `lookalike_animals` | pilot | 42 | 110 | 1 | 2026-10-09T17:54:57 | vthv4edn | logs/20261009_175457_rppo_lookalike_l05_t16quad_s42.log |
| 1 | running | w2 ordinary | `rppo_lookalike_hf_l05_w2_t1none_s42` | `lookalike_half_factorial` | pilot | 42 | 107 | cuda:0 | 2026-10-12T15:07:47 | hodrwsga | logs/20261012_150747_rppo_lookalike_hf_l05_w2_t1none_s42.log |
| 2 | queued (stopped 19:48, waiting for a free card) | w2 modulated | `rppo_lookalike_hf_l05_w2_t16quad_s42` | `lookalike_half_factorial` | pilot | 42 | 107 | cuda:0 | 2026-10-12T15:08:06 | hzmjzl2n | logs/20261012_150806_rppo_lookalike_hf_l05_w2_t16quad_s42.log |
| 3 | running | w3 ordinary | `rppo_lookalike_hf_l05_w3_t1none_s42` | `lookalike_half_factorial` | pilot | 42 | 114 | cuda:0 | 2026-10-12T15:13:10 | fp5elazc | logs/20261012_151310_rppo_lookalike_hf_l05_w3_t1none_s42.log |
| 4 | running (resumed from checkpoint 23:46) | w3 modulated | `rppo_lookalike_hf_l05_w3_t16quad_s42` | `lookalike_half_factorial` | pilot | 42 | 114 | cuda:2 | 2026-10-12T23:46:22 | mkeipck0 | logs/20261012_234622_rppo_lookalike_hf_l05_w3_t16quad_s42.log |
| 5 | queued (stopped 19:47, waiting for a free card) | w4 ordinary | `rppo_lookalike_hf_l05_w4_t1none_s42` | `lookalike_half_factorial` | pilot | 42 | 114 | cuda:1 | 2026-10-12T15:13:22 | lwrw17zc | logs/20261012_151322_rppo_lookalike_hf_l05_w4_t1none_s42.log |
| 6 | running | w4 modulated | `rppo_lookalike_hf_l05_w4_t16quad_s42` | `lookalike_half_factorial` | pilot | 42 | 114 | cuda:1 | 2026-10-12T15:13:27 | wpnvxfoo | logs/20261012_151327_rppo_lookalike_hf_l05_w4_t16quad_s42.log |
| 7 | done (10M episodes, ~23:35) | w5 ordinary | `rppo_lookalike_hf_l05_w5_t1none_s42` | `lookalike_half_factorial` | pilot | 42 | 114 | cuda:2 | 2026-10-12T15:13:32 | 8c7yhm2p | logs/20261012_151332_rppo_lookalike_hf_l05_w5_t1none_s42.log |
| 8 | running | w5 modulated | `rppo_lookalike_hf_l05_w5_t16quad_s42` | `lookalike_half_factorial` | pilot | 42 | 114 | cuda:3 | 2026-10-12T15:13:38 | 868ghfsm | logs/20261012_151338_rppo_lookalike_hf_l05_w5_t16quad_s42.log |
| 9 | running | w6 ordinary | `rppo_lookalike_hf_l05_w6_t1none_s42` | `lookalike_half_factorial` | pilot | 42 | 107 | cuda:1 | 2026-10-12T15:13:43 | ii0erpbj | logs/20261012_151343_rppo_lookalike_hf_l05_w6_t1none_s42.log |
| 10 | queued (stopped 19:48, waiting for a free card) | w6 modulated | `rppo_lookalike_hf_l05_w6_t16quad_s42` | `lookalike_half_factorial` | pilot | 42 | 107 | cuda:1 | 2026-10-12T15:13:49 | kna2fm1p | logs/20261012_151349_rppo_lookalike_hf_l05_w6_t16quad_s42.log |
| 11 | running | w7 ordinary | `rppo_lookalike_hf_l05_w7_t1none_s42` | `lookalike_half_factorial` | pilot | 42 | 113 | cuda:0 | 2026-10-12T20:37:53 | qs8mbvac | logs/20261012_203753_rppo_lookalike_hf_l05_w7_t1none_s42.log |
| 12 | running | w7 modulated | `rppo_lookalike_hf_l05_w7_t16quad_s42` | `lookalike_half_factorial` | pilot | 42 | 112 | cuda:0 | 2026-10-12T15:13:54 | jrkazhnc | logs/20261012_151354_rppo_lookalike_hf_l05_w7_t16quad_s42.log |
| 13 | running | w8 ordinary | `rppo_lookalike_hf_l05_w8_t1none_s42` | `lookalike_half_factorial` | pilot | 42 | 112 | cuda:1 | 2026-10-12T15:09:06 | wsi9563u | logs/20261012_150906_rppo_lookalike_hf_l05_w8_t1none_s42.log |
| 14 | running | w8 modulated | `rppo_lookalike_hf_l05_w8_t16quad_s42` | `lookalike_half_factorial` | pilot | 42 | 113 | cuda:1 | 2026-10-12T20:37:59 | plx8nfgr | logs/20261012_203759_rppo_lookalike_hf_l05_w8_t16quad_s42.log |


**Card un-sharing, 2026-10-12 evening (user decision; reason: the RTX 4090s on 102 and 113 were free, and the goal is one run per card).**
The six runs below were stopped with SIGINT at 19:47–19:48 (exact PID, clean exit). Training stops at the next
iteration and SIGINT writes no final checkpoint. So a run resumes (`--load-checkpoint <original folder>/models
--wandb-resume-id <original id>`, otherwise the same command line) from its last periodic checkpoint, and the
episodes after that checkpoint are lost. The original results folders are kept, because they hold the checkpoints.

| Run | Original folder (`results/JAX_RecurrentPPO/`) | Original log | WandB | Stopped at ep. | Resume ckpt | Now |
|---|---|---|---|---|---|---|
| 11 | `20261012-150902_rppo_lookalike_hf_l05_w7_t1none_s42` | `logs/20261012_150855_…w7_t1none_s42.log` | qs8mbvac | 2,324,843 | 2200046 | **resumed from checkpoint 2200046 on 113:0** at 20:37:53; new folder `20261012-203757_…w7_t1none_s42` |
| 14 | `20261012-150919_rppo_lookalike_hf_l05_w8_t16quad_s42` | `logs/20261012_150912_…w8_t16quad_s42.log` | plx8nfgr | 1,803,024 | 1800048 | **resumed from checkpoint 1800048 on 113:1** at 20:37:59; new folder `20261012-203804_…w8_t16quad_s42` |
| 4 | `20261012-151320_rppo_lookalike_hf_l05_w3_t16quad_s42` | `logs/20261012_151316_…w3_t16quad_s42.log` | mkeipck0 | 1,980,011 | 1800026 | **resumed from checkpoint 1800026 on 114:2** at 23:46:22 (card freed by w5 ordinary; free on two checks 10 min apart); new folder `20261012-234627_…w3_t16quad_s42`. Earlier: planned for 102:0, but 102 picked up a foreign job just before launch; a resume attempt there at 20:36:21 was stopped during startup. |
| 5 | `20261012-151326_rppo_lookalike_hf_l05_w4_t1none_s42` | `logs/20261012_151322_…w4_t1none_s42.log` | lwrw17zc | 2,156,904 | 2000000 | queued (planned for 102:1, same reason; never launched) |
| 2 | `20261012-150813_rppo_lookalike_hf_l05_w2_t16quad_s42` | `logs/20261012_150806_…w2_t16quad_s42.log` | hzmjzl2n | 2,201,668 | 2200035 | queued (user: one run per card; its partner w2 ordinary keeps 107:0) |
| 10 | `20261012-151355_rppo_lookalike_hf_l05_w6_t16quad_s42` | `logs/20261012_151349_…w6_t16quad_s42.log` | kna2fm1p | 2,457,476 | 2400022 | queued (user: one run per card; its partner w6 ordinary keeps 107:1) |

The queued rows keep their original node/GPU/launch/log columns until they are resumed. On WandB each resumed
curve retraces the span between its checkpoint and its stop point, so two sets of points overlap there.

The reused rows' result folders are `results/JAX_RecurrentPPO/20261009-175459_…_t1none_s42` and
`20261009-175502_…_t16quad_s42`.

### Configs to produce

| Runs | Env config (`configs/environment/experiment/basic/`) | Agent config (`configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/`) |
|---|---|---|
| 1, 2 | `lookalike_hf_w2_newAD_10x10.yaml` | `nmngaenorm_t1none.yaml` / `nmngaenorm_t16quad_ALL.yaml` |
| 3, 4 | `lookalike_hf_w3_newBD_10x10.yaml` | same pair |
| 5, 6 | `lookalike_hf_w4_newAB_10x10.yaml` | same pair |
| 7, 8 | `lookalike_hf_w5_newCD_10x10.yaml` | same pair |
| 9, 10 | `lookalike_hf_w6_newAC_10x10.yaml` | same pair |
| 11, 12 | `lookalike_hf_w7_newBC_10x10.yaml` | same pair |
| 13, 14 | `lookalike_hf_w8_newABCD_10x10.yaml` | same pair |

Odd-numbered runs use `nmngaenorm_t1none.yaml` (ordinary agent); even-numbered runs use
`nmngaenorm_t16quad_ALL.yaml` (modulated agent).

### Launch block (for `train_command-agent.sh`; the training-runner adds it and fills in `[node:GPU]`)

The flags are identical to the lookalike runs. `--num-envs` and `--checkpoint-frequency` stay
config-owned. Run the launch-morning re-check (World 1 reuse, item 4) first.

```
# ---------------------------------------------------------------------------
# lookalike half-factorial — 7 new worlds x 2 agents at level 05, seed 42 (14 runs), RTX 3090-class nodes
# Plan: docs/experiments/active/hypervigilance/LOOKALIKE_HALF_FACTORIAL_L05.md (launch manifest).
# World 1 = the lookalike world, reused from the 2026-10-09 runs (not relaunched).
# [N:G] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/lookalike_hf_w2_newAD_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml --episodes 10000000 --seed 42 --device cuda:G --log-interval 10 --tag "rppo_lookalike_hf_l05_w2_t1none_s42" --wandb-name "rppo_lookalike_hf_l05_w2_t1none_s42" --wandb-group "lookalike_half_factorial" --wandb-job-type "pilot"
# [N:G] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/lookalike_hf_w2_newAD_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml --episodes 10000000 --seed 42 --device cuda:G --log-interval 10 --tag "rppo_lookalike_hf_l05_w2_t16quad_s42" --wandb-name "rppo_lookalike_hf_l05_w2_t16quad_s42" --wandb-group "lookalike_half_factorial" --wandb-job-type "pilot"
# [N:G] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/lookalike_hf_w3_newBD_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml --episodes 10000000 --seed 42 --device cuda:G --log-interval 10 --tag "rppo_lookalike_hf_l05_w3_t1none_s42" --wandb-name "rppo_lookalike_hf_l05_w3_t1none_s42" --wandb-group "lookalike_half_factorial" --wandb-job-type "pilot"
# [N:G] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/lookalike_hf_w3_newBD_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml --episodes 10000000 --seed 42 --device cuda:G --log-interval 10 --tag "rppo_lookalike_hf_l05_w3_t16quad_s42" --wandb-name "rppo_lookalike_hf_l05_w3_t16quad_s42" --wandb-group "lookalike_half_factorial" --wandb-job-type "pilot"
# [N:G] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/lookalike_hf_w4_newAB_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml --episodes 10000000 --seed 42 --device cuda:G --log-interval 10 --tag "rppo_lookalike_hf_l05_w4_t1none_s42" --wandb-name "rppo_lookalike_hf_l05_w4_t1none_s42" --wandb-group "lookalike_half_factorial" --wandb-job-type "pilot"
# [N:G] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/lookalike_hf_w4_newAB_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml --episodes 10000000 --seed 42 --device cuda:G --log-interval 10 --tag "rppo_lookalike_hf_l05_w4_t16quad_s42" --wandb-name "rppo_lookalike_hf_l05_w4_t16quad_s42" --wandb-group "lookalike_half_factorial" --wandb-job-type "pilot"
# [N:G] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/lookalike_hf_w5_newCD_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml --episodes 10000000 --seed 42 --device cuda:G --log-interval 10 --tag "rppo_lookalike_hf_l05_w5_t1none_s42" --wandb-name "rppo_lookalike_hf_l05_w5_t1none_s42" --wandb-group "lookalike_half_factorial" --wandb-job-type "pilot"
# [N:G] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/lookalike_hf_w5_newCD_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml --episodes 10000000 --seed 42 --device cuda:G --log-interval 10 --tag "rppo_lookalike_hf_l05_w5_t16quad_s42" --wandb-name "rppo_lookalike_hf_l05_w5_t16quad_s42" --wandb-group "lookalike_half_factorial" --wandb-job-type "pilot"
# [N:G] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/lookalike_hf_w6_newAC_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml --episodes 10000000 --seed 42 --device cuda:G --log-interval 10 --tag "rppo_lookalike_hf_l05_w6_t1none_s42" --wandb-name "rppo_lookalike_hf_l05_w6_t1none_s42" --wandb-group "lookalike_half_factorial" --wandb-job-type "pilot"
# [N:G] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/lookalike_hf_w6_newAC_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml --episodes 10000000 --seed 42 --device cuda:G --log-interval 10 --tag "rppo_lookalike_hf_l05_w6_t16quad_s42" --wandb-name "rppo_lookalike_hf_l05_w6_t16quad_s42" --wandb-group "lookalike_half_factorial" --wandb-job-type "pilot"
# [N:G] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/lookalike_hf_w7_newBC_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml --episodes 10000000 --seed 42 --device cuda:G --log-interval 10 --tag "rppo_lookalike_hf_l05_w7_t1none_s42" --wandb-name "rppo_lookalike_hf_l05_w7_t1none_s42" --wandb-group "lookalike_half_factorial" --wandb-job-type "pilot"
# [N:G] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/lookalike_hf_w7_newBC_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml --episodes 10000000 --seed 42 --device cuda:G --log-interval 10 --tag "rppo_lookalike_hf_l05_w7_t16quad_s42" --wandb-name "rppo_lookalike_hf_l05_w7_t16quad_s42" --wandb-group "lookalike_half_factorial" --wandb-job-type "pilot"
# [N:G] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/lookalike_hf_w8_newABCD_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml --episodes 10000000 --seed 42 --device cuda:G --log-interval 10 --tag "rppo_lookalike_hf_l05_w8_t1none_s42" --wandb-name "rppo_lookalike_hf_l05_w8_t1none_s42" --wandb-group "lookalike_half_factorial" --wandb-job-type "pilot"
# [N:G] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/lookalike_hf_w8_newABCD_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml --episodes 10000000 --seed 42 --device cuda:G --log-interval 10 --tag "rppo_lookalike_hf_l05_w8_t16quad_s42" --wandb-name "rppo_lookalike_hf_l05_w8_t16quad_s42" --wandb-group "lookalike_half_factorial" --wandb-job-type "pilot"
```

## Config-system bookkeeping

- **No new keys.** Every key used (`visual_mask`, `count_low/high`, `detection_range`,
  `attack_range`, `max_consumption`, `damage`, `body.food_nutrition_gain`) is existing schema.
  `visual_mask` is already documented in `docs/environment/02_config_schema.md` and in CONFIG_GUIDE,
  so neither needs an update. `default.yaml` is untouched.
- **Critical-settings registry.** No registry setting changes value: none of the changed keys is a
  registry row, and every registry row resolves to its canonical value in all seven worlds. So no
  change-log entry is required by the protocol.
- **List-replace footgun.** Each config restates in full every list it redeclares (`resources`,
  `entities`, `obstacles`). This was verified by the per-entry comparison above.
- **Folder placement (plan review L1).** The seven worlds live in `basic/`, the maintained folder
  (user decision, 2026-10-12). The cost: every schema change must now carry seven more files,
  although only the worlds the screen keeps will matter afterwards. The level-05 body-interaction
  screen chose the other way ([[LEVEL05_BODY_INTERACTIONS]], decision D2). It kept its 16 screen
  worlds in a sibling, unmaintained folder and promoted only the winners into `basic/`.
  Recommendation: after this screen, move the worlds that are not taken forward to `archive/`.

## Metrics requested

Readout (a) and the surprise response need tooling that is not yet in `scripts/`:

| Metric | Why now | Where it would live | Cost |
|---|---|---|---|
| Predator deaths and hits by activity state, with time shares | Readout (a) | The 27 M-episode script exists only as a gitignored working file (`tmp/20261011_foraging_deaths/predator_deaths.py`). Promote it to `scripts/analysis/studies/` and add the time-share output | cheap (reads existing trajectory stores) |
| Hiding versus healing split; unhurt hiding near animals | Readouts (b) and C | New analysis over the same stores. Needs the per-step action, `agent_in_bush`, injury and animal positions | cheap |
| Hazard-hit events (newly entered cell) and 20-step response, with truncation counts | C readout, trap-versus-rock difference-in-differences | New analysis over the same stores. Needs the per-step damage source | cheap |
| Episode-bootstrap standard errors; evaluation extended in 2,000-episode blocks up to the 20,000 cap | Pass rule (bar with sampling error), minimums | Analysis script plus a loop around `scripts/eval/eval_rollout.py --record` | moderate (up to 10× the evaluation compute at 6, 8 and 10 M) |

If accepted, route these through `feature-workflow` before the analysis phase. They are not
needed for launch, but the σ measurement on the fast-heal runs needs them, and that comes before
any contrast is read.

## Level 06 follow-up (not now)

The same eight-world design will be repeated at level 06 (level 05 plus thirst and a pond,
`06-pond_thirst_10x10.yaml`), with the same groups and values on top of a level-06 lookalike base.
It is not configured here.

## Feedback from plan-reviewer, and response (2026-10-12)

The review is at `docs/reviews/plan_lookalike_half_factorial_l05.md`. Its verdict was NOT READY
(two critical findings); the moderate findings were returned inline. Every finding is addressed
below. This is a doc-only response: the only config change is the user's predator-count decision.

| Finding | What it said | Response | Where |
|---|---|---|---|
| C1 | The old pass rule was an OR over about 10 readouts. A and B pass it mechanically. Foraging deaths fed no criterion | One primary behavioural readout per group: B → foraging share of predator deaths; A → unhurt hiding near animals; C → rock-hit surprise response, hidden versus visible; D → hypervigilance pattern. The endings mix is now descriptive only | §Primary readouts, §Secondary readouts |
| C2 | Bush share mixes hiding with healing. The C test compared trap and rock wounds about 10× apart and used no C− worlds | Hiding = bush steps at injury < 1 or without the rest action; healing is reported separately. C = rock hits in C+ minus rock hits in C− (same 1–5 damage). Trap-minus-rock is kept only as a C+ minus C− difference-in-differences, matched on injury after the hit | §Definitions, §Primary readouts |
| M1 | Thresholds were not tied to noise; requiring both agents to agree was too strict for a screen | σ is measured from the fast-heal level-05 seeds 42–44 (and checked against the world-1 seed pair). Bar = 1.4σ, about 2× the noise of a 4-against-4 contrast. Agent agreement is no longer required; disagreement is flagged | §Pass rule |
| M2 | C is not pure concealment | C is reported as "concealment plus less visual clutter" | §Question, §What each group changes |
| M3 | Hazard events were ill-defined; deaths cut windows short | Event = first damage step on a newly entered cell, excluding step 0. Events cut short by death are counted and reported; complete windows are primary | §Definitions |
| M4a | The launch-morning re-check was too narrow | Extended to `src/`, `train.py`, the five training-layer configs, the world ladder and both agent configs | §World 1 reuse, item 4 |
| M4b | World 1 is on the "−" side of every contrast | Stated as a known limitation (±δ/4 on every contrast). The user chose reuse; same card class at launch | §World 1 reuse |
| M5 | The rebalance-planner results were not used | Linked, summarised, with four implications for reading the trained runs | §What the ideal planner predicts |
| M6 | Measure definitions were loose; B changes eating frequency | States (i) eating-recent and (ii) heading to food are kept separate; every death share is read against its time share | §Definitions |
| L1 | Screen configs in the maintained folder | Kept in `basic/` (user decision); trade-off stated, citing [[LEVEL05_BODY_INTERACTIONS]] D2 | §Config-system bookkeeping |

Also from the env-config review: group B's purpose is reworded (shorter, cheaper meals, not a
bigger reserve), and the arithmetic is corrected (+14 per eating step, the one-bite over-eating
band starts at 186, 7.0 % of starts).

Changed with the user's decision of 2026-10-12: A+ has exactly one predator. The four A+ configs
were updated and the load check re-run (verification table).

### Response to the re-review (2026-10-12, second round)

The re-review found the design NOT READY on one narrow critical finding (R1). The other findings
were returned inline. All responses are doc-only, and no config changed.

| Finding | What it said | Response | Where |
|---|---|---|---|
| R1 (Critical) | The food readout was a death share. Shorter meals cut eating time, and the share falls with it by construction. A 20-death floor was far too noisy | The readout is now a time-adjusted risk ratio within each world: deaths per step while eating ÷ deaths per step in other out-of-bush time, with heading-to-food reported separately against the same reference, on the log scale. The floor is 100 predator deaths (≥ 10 each in the two states compared). Evaluation is extended in 2,000-episode blocks up to a cap of 20,000 episodes per run and checkpoint. The episode-bootstrap sampling error is also folded into the bar | §Primary readouts, §Data, §Pass rule items 2 and 4 |
| R2 | The threat readout mixed caution near the rabbit with escape from real predators | Only steps with injury < 1, the rabbit within 2 cells and no predator within 4 cells count | §Primary readouts |
| R3 | Rock-hit events included hits taken while already hurt or near a predator | Only events with injury < 1 before the hit and no predator within 3 cells in the 20 steps before are kept. The counts kept, and the share of all events, are reported | §Primary readouts |
| R4 | Missing data turned into "not worth replicating" | A group with any run short of the minimums at 6, 8 or 10 M is **unresolved** | §Pass rule item 4, §Failure modes |
| R5 | Minimums were in steps or events, which are not independent | The minimums are ≥ 50 contributing episodes (plus 100 deaths for food). Errors come from a bootstrap over whole episodes | §Data, §Pass rule item 2 |
| R6 | The hypervigilance test scenes come from the base world, so agents from other worlds are tested off their training world | Written up as an open decision for the user (rebuild scenes per world, or accept the mismatch; and whether (c) should be primary for every group). Not chosen | §Open decision for the user |
| R7 | The noise rule was vague | Written out. σ_fh is pooled over the fast-heal seeds 42–44 (4 degrees of freedom). σ_lk = \|s42 − s43\| / √2 per agent with both seed-43 lookalike runs, pooled as the root mean square. σ_lk is used if it exceeds 2 σ_fh. The 95 % range of 0.6–2.9× is stated | §Pass rule item 1 |
| R8 | The sign check across checkpoints was too loose | The sign must agree at 6 M, 8 M and 10 M | §Pass rule item 3 |
| Open assumption (KNOWN_BUGS row: saved run configs stop loading once a key becomes mandatory) | The noise measurement needs the fast-heal level-05 runs to load at current code | Checked 2026-10-12 on one run (`20261005-160124_rppo_healrep_l05_t1none_s42`): its saved `models/config.yaml`, loaded with a plain `Config.load_yaml` and `load_env_params`, builds without any compatibility step, resets and steps. It shows level 05's own values (predator notices at 1–7, 12-bite food). The other five fast-heal level-05 runs were saved the same day from the same code, so they are expected to load too. They were not each checked, and the evaluation tool's own loading path was not exercised | — |

## Results / Conclusions

To be filled in after training and evaluation.

## Links

- [[LOOKALIKE_ANIMALS_CLOSE_POUNCE]]: the base world (world 1), its runs, and the hypervigilance
  clue criteria used for readout (c).
- [[FAST_HEAL_REPLICATION]]: origin of the agent pair and training settings, and the level-05 seeds
  used to measure σ.
- [[LEVEL05_BODY_INTERACTIONS]]: an earlier level-05 world screen, and its folder-placement
  decision.
- Plan review: `docs/reviews/plan_lookalike_half_factorial_l05.md`.
- Rebalance planner: `docs/experiments/active/rebalance_planner/figures/results.json`. Scripts are
  in `scripts/analysis/studies/rebalance_planner/` and working notes in
  `tmp/20261011_233031_rebalance_planner.md`.
- 27 M-episode foraging-death analysis: `tmp/20261011_foraging_deaths/` (gitignored).
