---
title: Lookalike half-factorial at level 05 — which world changes make hiding affordable and pain unexpected
topic: hypervigilance
status: active
created: 2026-10-11
last_updated: 2026-10-16
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

**Update 2026-10-15: the other half.** The user approved training the eight remaining
combinations (worlds 9–16, each changing one or three groups), so that the two halves together
cover all 16. That separates the effects the half could only read in pairs, for example "bigger
food matters more when hazards are hidden" from "the new predator matters more when hazards are
fewer". Design, configs, checks and run table: "Complementary half: worlds 9–16" below.

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
Worlds 9–16, the other half (D = −A × B × C), are listed in "Complementary half: worlds 9–16".

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

### Provisional definitions (pending plan review, 2026-10-13)

The evaluation tooling plan ([[HALF_FACTORIAL_EVAL_TOOLING]]) had to fix three readings that the
definitions above leave open. They change the numbers, so they are recorded here. They are
**provisional until the plan review of that tooling plan**, and any change after review is recorded
here, dated, before any result is read.

- **(a) Timing of conditions.** Conditions used to classify a step or an event (injury, animal
  distance) are read on the step **before** the outcome, not on the same step. The project's other
  corrected analysis tools do the same.
- **(b) Complete windows for rock hits.** A rock-hit event counts only if both the 20 steps before
  it and the 20 steps after it lie inside the episode. Events that come too early for a full
  "before" window are counted and reported, then left out. This adds a "before" requirement to the
  rule above, which asked only about the "after" window (events cut short by death).
- **(c) Trap-versus-rock difference-in-differences without the "unhurt before the hit" filter.**
  The secondary trap-versus-rock comparison uses hazard-hit events **without** the filter that keeps
  only hits on an unhurt agent. With that filter, a trap hit (25–60 or 15–45 damage) and a rock hit
  (1–5 damage) would never land in the same 10-point injury bin, so the matched comparison would be
  empty. The primary C readout keeps the filter (re-review R3).

**Trap deaths are not predator deaths.** The tooling plan found that the gitignored script behind
the 27 million-episode foraging analysis counted deaths from the hidden trap as predator deaths. The
trap's resource type is named `hiding_predator`, and the script counted animal-pounce deaths, trap
deaths and deaths where both hit together. So that analysis's "predator deaths while foraging" mix
in trap deaths. Readout (a) uses **only deaths whose fatal hit came from the hunting animal**. Trap
deaths are reported separately. The motivating claim in "Question" (agents die from the predator mostly
while foraging) rests on the old count and has not been re-checked with trap deaths removed.

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

**Decision (user, 2026-10-13, about 00:35): option 1, rebuild the test scenes for each world.**
Seven new frozen scene sets are built, one for each of worlds 2–8, in exactly the same way as
world 1's lookalike set (frozen 2026-10-10), so every agent is tested in scenes built on its own
training world. World 1 keeps its existing frozen set. The specification is the next section.

**The second, related choice is still open.** Whether the hypervigilance pattern (c) stays the
primary readout for D only, or becomes primary for every group, has **not** been decided. Until the
user decides, the design stands as written above: (c) is primary for D only.

**Correction to the mismatch examples above (found while writing the specification, 2026-10-13).**
World 1's test scenes contain **no rocks and no traps**. Every scene restates its own small list of
obstacles (one bush, plus one campfire in the "training-like" set) and of resources (one food
item), which replaces the training world's lists. So the first example (agents trained with hidden
hazards "would suddenly see them as occupied cells") does not happen: no agent meets a rock or trap
in any test scene. The other two examples (food size, predator settings) are real. The original
text is kept unchanged above; the consequences are in the next section.

**Change of plan (user, 2026-10-13, later the same day): world 1's scenes first.** The user asked to
"fix the test environment and see the results first". So **all 16 runs** (the 14 new runs and the two
world-1 runs) are tested in **world 1's existing frozen scene set**, and the user looks at those
hypervigilance results before anything else is built. For this first pass, the primary test for
readout (c) is world 1's scenes for every world. That is **option 2** of the decision above (accept
the mismatch), in place of option 1. The per-world scene sets are **deferred: decide after the
world-1-scene results**. Their specification and the user's three answers on it are kept below,
unchanged, for that later decision. So is the rest of the evaluation tooling.

**Known limitation of this pass.** Agents from worlds 2–8 are tested in scenes built on a world they
did not train in. The size of that mismatch is limited:

- the scenes contain no rocks or traps, so hidden hazards (C) and hazard counts and damage (D) do not
  appear in them at all;
- food differs from training for worlds 3, 4, 7 and 8: 6-bite items with gain 6 per bite in the
  scenes, against 9 bites and gain 16 in training;
- the predator differs from training for worlds 2, 4, 6 and 8: it notices and pounces at a fixed 3
  cells in the scenes, against a draw of 2–3 for each in training. Fixed 3 / 3 is one of the four
  combinations those agents trained on, and it appears only in the predator scenes, which are the
  positive control and not part of (c).

A group effect on (c) from this pass is therefore read as "hypervigilance as measured in world 1's
scenes". It is most exposed to the food mismatch in the B+ worlds.

## Per-world test scenes (specification, 2026-10-13; deferred)

> **Status: deferred (user, 2026-10-13). Decide after the world-1-scene results.** The first pass
> tests every run in world 1's frozen scenes (see "Change of plan" in the open-decision section
> above). Nothing in this section is to be built until the user has seen those results. The
> specification and the user's three answers are kept for that decision.

### In short

> **Updated 2026-10-13 (user decisions, see "Decisions on the scene questions" at the end of this
> section):** scenes stay hazard-free, and the predator scenes keep world 1's fixed 3 / 3 in every
> world. Only food (group B) reaches the scenes, so the sets hold two distinct contents.

Each of worlds 2–8 gets its own copy of the four scene folders that world 1 was tested in, plus the
no-healing copies of three of them. Everything about a scene stays as in world 1 (the 10×10 test
field, the agent's start cell, the single bush, where the animal enters, the injury levels, the
100-step length, the rabbit-versus-no-animal conditions, the temperature handling). Only the
settings that the world's own training config changes **and that appear in a scene** follow that
world:

- the hunting predator's noticing distance and pounce reach (group A), which appear only in the
  predator scenes, the positive control;
- the food item's size and the nutrition per bite (group B), which appear in every scene.

Groups C (hidden hazards) and D (hazard counts and damage) change nothing in the scenes, because
the scenes contain no hazards. Their effect on readout (c) can only come from what the agent
learned in training. That is what D's readout was meant to measure, but it also means the scene
sets of some worlds are identical in content (see "Which sets end up identical").

### How world 1's set was built (reconstructed and reproduced 2026-10-13)

**Step 1: the source scenes.** World 1's scenes are not built from the training-world config. They
are copies of older, fixed test scenes used by the fast-bush-healing replication. Each is a
10×10 field with the agent starting at the centre cell [5, 5], one hiding bush three cells to its
left at [5, 2], the animal (if any) entering from the right at [5, 9], nutrition 100, a fixed start
injury and 100 steps per episode. Four source folders were used:

| Source folder (`configs/environment/experiment/behavior_probes/…`) | Name in the set | Temperature | Scenes kept |
|---|---|---|---|
| `thermal/neutral_clean` | "no-temperature" | neutralised: air 0 °C, body starts at 0 | none / predator / chasing harmless rabbit / wandering rabbit × injury 0 and 70 (8) |
| `hvsmell/two_channel` | "training-like" | as in training (level 05 cold air), one campfire beside the bush at [5, 3] | the same 8 (the smell-variant scenes are left out, since smell no longer differs) |
| `injury_grid/neutral_clean` | injury grid | neutralised | none / predator / wandering rabbit × injury 0, 10, …, 90 (30) |
| `injury_grid/chase_neutral_clean` | injury grid, chasing rabbit | neutralised | chasing harmless rabbit × injury 0–90 (10) |

The no-temperature and injury-grid sources extend `default.yaml`; the training-like source extends
the level-05 control world of the single-channel smell study. In every case, the resolved body,
sensory, observation-noise and water settings equal world 1's training values except the start
state (fixed injury, fixed nutrition 100, fixed body temperature where neutralised). This was
checked on 2026-10-13 by resolving one scene of each kind and comparing it with the resolved world-1
training config.

**Step 2: the lookalike copy.** `generate_lookalike_variants.py` (in
`configs/environment/experiment/behavior_probes/lookalike/`) writes one file per source scene. Each
file `extends:` its source and restates only the animal list and the resource list:

- every animal smells `[0, 0.6, 0.6, 0, 0]` (spread 0), the lookalike smell;
- the hunting predator (tag `pred`) notices at 3 cells, pounces from 3 cells, and pounces
  successfully half the time. Its other settings come from the source: damage 15–45, stamina 30,
  pounce cooldown 3 steps, one predator;
- one food item of 6 bites at [2, 5]: three cells above the start, six steps from the bush, away
  from where the animal enters. Eating therefore means leaving the bush.

The generator's `--check` mode confirms that each copy differs from its source only in the animal
and resource lists.

**Step 3: the no-healing copies** (commit `e509d743`). `generate_no_healing_variants.py` (in
`behavior_probes/no_healing/`) writes a copy of the no-temperature and both injury-grid folders
with `body.recovery_base_rate` 0, so a start injury lasts the whole test. The training-like folder
has no no-healing copy. Its `--check` confirms that each copy differs from its source only in that
key.

**Step 4: freeze and test specs** (commit `abd52e45`, 2026-10-10, before any checkpoint was tested).
There are 56 scenes with healing and 48 without, and seven test specs in `configs/eval_sweeps/lookalike/`:
four with healing (no-temperature, training-like, grid, grid-chase) and three without. Each spec
runs 30 episodes × 100 steps per checkpoint and scene, with the test program's fixed seed 0, through
`scripts/eval/dwell_sweep/run_sweep.py`. Results go to
`results/eval/avoidance/metrics_history_rppo_lookalike{,_noheal}/`. The analysis reading those
results is `scripts/analysis/studies/lookalike_pilot/figures.py`.

**Reproduced.** Both generators, run on 2026-10-13 in `--check` mode with the invocations below,
reproduce all 104 frozen files byte for byte, and the resolved-config checks pass. So the procedure
above is complete, and the source scenes have not drifted since the freeze.

```
P=/home/vncuser/miniconda3/envs/grid_world_pain/bin/python
$P configs/environment/experiment/behavior_probes/lookalike/generate_lookalike_variants.py \
   --src behavior_probes/thermal/neutral_clean --src behavior_probes/hvsmell/two_channel \
   --src behavior_probes/injury_grid/neutral_clean --src behavior_probes/injury_grid/chase_neutral_clean \
   --keep avoid_none,avoid_pred,avoid_rabbit,avoid_rabbitwander [--check]
$P configs/environment/experiment/behavior_probes/no_healing/generate_no_healing_variants.py \
   --src behavior_probes/lookalike/thermal__neutral_clean \
   --src behavior_probes/lookalike/injury_grid__neutral_clean \
   --src behavior_probes/lookalike/injury_grid__chase_neutral_clean [--check]
```

### What is kept identical in every world's set

The same four source folders and the same 56 scenes; the same three no-healing copies (48 scenes);
the same field, start cell, bush, campfire (training-like set only), animal entry cell and paths;
injury levels 0–90; nutrition 100; 100 steps; the same temperature handling per folder; the
lookalike smell on every animal; the chasing and wandering rabbits unchanged; the predator's damage
15–45, stamina 30, pounce cooldown 3 steps and success 0.5; one predator at most and one food item
at [2, 5]; bush healing 25× (or 0 in the no-healing copies); 30 episodes per checkpoint and scene;
evaluation seed 0. These are either the same in all eight training worlds or deliberate features of
the test scenes. Keeping them makes the eight sets comparable.

### What follows from each world's own config

> **Updated 2026-10-13 (user decisions, see "Decisions on the scene questions" at the end of this
> section):** scenes stay hazard-free, and the predator scenes keep world 1's fixed 3 / 3 in every
> world. Only food (group B) reaches the scenes, so the sets hold two distinct contents.

| World | Predator scenes: notices / pounces (cells) | Food item: bites | `body.food_nutrition_gain` | Hidden hazards, hazard counts and damage | Scenes that differ from world 1 |
|---|---|---|---|---|---|
| 1 | 3 / 3 | 6 | 6 | none in any scene | (reference, existing set) |
| 2 (AD) | **2–3 / 2–3** | 6 | 6 | none in any scene | predator scenes only |
| 3 (BD) | 3 / 3 | **9** | **16** | none in any scene | all scenes |
| 4 (AB) | **2–3 / 2–3** | **9** | **16** | none in any scene | all scenes |
| 5 (CD) | 3 / 3 | 6 | 6 | none in any scene | **none** |
| 6 (AC) | **2–3 / 2–3** | 6 | 6 | none in any scene | predator scenes only |
| 7 (BC) | 3 / 3 | **9** | **16** | none in any scene | all scenes |
| 8 (ABCD) | **2–3 / 2–3** | **9** | **16** | none in any scene | all scenes |

"2–3" means the noticing distance and the pounce reach are each drawn per test episode from {2, 3},
independently, as in the world's training. That is the default the user's instruction implies; the
alternative is open question Q2. A scene-level check on 2026-10-13 confirmed that the simulator's own
loader turns a scene with these overrides into the intended values (noticing 2–3, reach 2–3, 9 bites,
gain 16), and that the `body:` override keeps the scene's start injury and nutrition.

The food count stays at one item in every world. That is inside every world's training range
(1–4 or 1–3).

### Things in world 1's procedure that do not carry over unchanged

1. **Hidden hazards have nothing to act on.** The scenes contain no rocks or traps, so concealment
   (C) and hazard load (D) change nothing in any scene, and the question of start cells on hidden
   hazards does not arise. Adding hidden hazards to the C+ sets would break "built exactly the same
   way", make those scenes differ from world 1's in a way only some worlds share, and add surprise
   hits inside a test meant to hold injury fixed. **Recommendation: add none.** Open question Q1.
2. **Over-eating becomes possible in B+ scenes.** At nutrition 100, one bite nets +14 in B+ worlds,
   so eating 8 of the 9 bites in a row reaches 200 and kills. In world 1's scenes the whole item gives
   only +24, so no scene death is possible from eating. This is the B+ worlds' own rule, so it stays.
   Over-eating deaths are reported per scene, and a scene where they push newest-20 survival below
   95 steps is reported, not interpreted (the lookalike design's existing rule).
3. **The predator control in A+ worlds is noisier.** With four predator kinds drawn at random,
   30 episodes per scene give about 7–8 of each kind. The predator scenes are only the positive
   control ("does the agent hide from real danger at all"), not part of readout (c).
4. **The generators are hard-wired to world 1 (task item 3).** `generate_lookalike_variants.py`
   takes source folders (`--src`) but no world config. Its smell, food (6 bites), predator (3 / 3,
   0.5) and output folder (`lookalike/…`) are constants, it cannot write a `body:` override, and its
   `--check` would reject one (it allows differences only in the animal and resource lists). It
   cannot produce any of the seven new sets as is. Running it for world 5 would overwrite world 1's
   frozen folder. `generate_no_healing_variants.py` is world-agnostic: run unchanged on a new
   folder, it writes `no_healing/<that folder's path with "/" → "__">/`. The generalisation is with
   the parallel senior-developer plan. **No scene configs are produced here**, because the existing
   tooling cannot produce them.

### Which sets end up identical

In content, world 5's set equals world 1's; world 6's equals world 2's; world 7's equals world 3's;
world 8's equals world 4's. Each pair differs only in C and D, which the scenes do not contain. So
seven folders hold three distinct contents. Building seven named folders anyway, as decided, keeps
"world k's scenes" a fixed path for the analysis and costs only disk space. The builder's check must
confirm these equalities (resolved scene configs identical within each pair). An inequality would
mean a world config leaked into a scene where it should not.

### What has to be produced (for the developer plan and the freeze)

- **Scenes.** `configs/environment/experiment/behavior_probes/lookalike_hf/w<k>/<source>/` for
  k = 2–8, with the same four `<source>` names as world 1 (`thermal__neutral_clean`,
  `hvsmell__two_channel`, `injury_grid__neutral_clean`, `injury_grid__chase_neutral_clean`): 56
  scenes per world. Each file `extends:` the same source scene as world 1's copy, carries the
  lookalike changes, and adds the world's predator ranges, food bites and nutrition gain from the
  table above.
- **No-healing copies.** Run the existing no-healing generator unchanged on each world's three
  folders: 48 scenes per world.
- **Builder checks**, run with the simulator's loader (`load_env_params`), not only the YAML loader:
  each new scene differs from its source only in the animal list, the resource list and (B+ worlds)
  `body.food_nutrition_gain`; the loaded predator, food and gain values equal those of the world's
  training config; observation width 58; the pairs listed above are identical; and running the
  same procedure for world 1 reproduces the frozen world-1 set byte for byte.
- **Test specs.** `configs/eval_sweeps/lookalike_hf/` with seven specs per world (four with
  healing, three without), each listing that world's two runs, 30 episodes, results under
  `results/eval/avoidance/metrics_history_rppo_lookalike_hf/w<k>/…`. These can be written once the
  scene folders exist (the sweep tool refuses a spec whose scene folder is missing). The run paths
  are in the launch manifest.
- **Freeze.** One commit containing all seven sets, their checks' output and the specs, made before
  any checkpoint of worlds 2–8 is tested. Its hash is recorded here. Any later change is a new,
  separately named set.
- Total: 728 scenes and 49 test specs. Test compute: 14 runs on 104 scenes each, about 3.5× the
  lookalike pilot's test sweep (4 runs). World 1's two runs were already tested in its own set.

### Difficulty across the scene sets (added at the user's request, 2026-10-13)

**What differs in difficulty, given the scenes.** Because the scenes contain no hazards, the
per-world scene sets differ in difficulty in only two ways: the predator's reach and noticing
distance (A+; predator scenes only), and food size with over-eating risk (B+; every scene). Hidden
rocks and traps, and hazard counts and damage (C, D), do not enter any scene. The agents, though,
differ in what they learned. An agent from a harsh world may hide more in every scene. That
difference is part of what the screen is meant to detect, not a scene artefact.

**(1) What the readout (c) contrast cancels, and what it does not.**

- *Cancelled by construction.* (c) compares the rabbit scene with the no-animal scene **inside one
  world, at one injury level, for one agent**. Anything the two scenes share cancels: food size and
  over-eating risk, the bush, temperature, the agent's general level of caution, and its general
  skill in that world. That is most of the scene difficulty.
- *Not cancelled.*
  - Difficulty that changes **how much the rabbit itself matters**. Example: in B+ scenes the agent
    may leave the bush once to eat a large item and then stay, giving the rabbit fewer chances to
    interrupt eating than in 6-bite scenes. The rabbit's effect then differs for a reason unrelated
    to hypervigilance. This is an interaction of difficulty with the animal, and no contrast inside
    one world removes it.
  - **Floor and ceiling.** Bush dwell is a share between 0 and 100 %. When the no-animal dwell is
    already near 100 % (an agent that sits in the bush whatever happens) or near 0 %, the rabbit
    cannot add or remove much, and the interaction shrinks for that reason alone. A world whose
    agents are near a bound shows a smaller (c) without being less hypervigilant.
  - The predator positive control in A+ worlds (four predator kinds) is not cancelled, but it is
    not part of (c).

**(2) Controls, their cost, and a recommendation for each.** The user decides; the recommended
setting is marked.

| Control | What it does | Cost | Recommendation |
|---|---|---|---|
| a. Identical scene geometry and seeds | Same field, bush, start cell, animal entry and paths, food cell, and the test program's seed 0 in every world | None: it is the specification above. The seed gives the same random draws at the start; trajectories still diverge once agents act differently | **Keep** (already in the spec) |
| b. Keep hazards out of the scenes | No rocks or traps in any scene, as in world 1 | None (already the case). The alternative, adding hidden hazards in C+ worlds and keeping them away from the start cell and the bush–food path, costs a new scene design, breaks "same as world 1", and puts surprise injuries into a test that fixes injury | **Keep out** (Q1) |
| c. Difficulty indicators per world | Report, per run and checkpoint: dwell in the unhurt no-animal scene (baseline), scene survival steps, deaths by cause (predator, over-eating, cold in the training-like set) and damage taken per episode | Analysis only. The test already records everything needed; the lookalike pilot's analysis script computes most of it | **Do** |
| d. Floor and ceiling rule | Pre-registered: a run and scene pair whose no-animal dwell (unhurt or injured) is above 90 % or below 5 % on the newest-20 mean is reported as "at ceiling" or "at floor" and left out of the group effect on (c), counted as missing (so the group can become unresolved, never a null). The 90 % bound is the lookalike design's existing ceiling rule; 5 % is new | Analysis only. It can turn a group "unresolved" | **Do** |
| e. Cross-test in world 1's scenes | Every agent of worlds 2–8 is also tested in world 1's frozen set. All agents then meet the same scenes, so differences between worlds come only from training. It also shows how much the scene change itself moves (c) | One more full test sweep: about the same compute as the per-world sweeps (7 healing and no-healing specs × 14 runs). Can be cut to the newest 20 checkpoints (the estimator's window), about 40 % of that | **Do, newest 20 checkpoints only**, and report it as secondary. It cannot make a group pass. If (c) in the own-world and world-1 scenes disagree in sign for a group, flag the group as "scene-dependent" (Q3) |
| f. Scene survival bound | The lookalike design's rule: a scene with newest-20 survival below 95 steps is reported, not interpreted. Applies to every world, including over-eating deaths in B+ worlds | None | **Keep** |

### Decisions on the scene questions (user, 2026-10-13)

The user answered the three questions raised by this specification. These decisions override the
text above wherever they differ, and the text above is kept as written.

1. **Scenes stay hazard-free in every world, as in world 1.** No rocks or traps are added to any
   scene, including those of the hidden-hazard (C+) worlds.
2. **The predator scenes use world 1's fixed values in every world:** it notices at 3 cells and
   pounces from 3 cells. This replaces the "2–3 / 2–3" entries for worlds 2, 4, 6 and 8 in the table
   above. As a result, **the only world setting that reaches the scenes is food (group B)**:
   9 bites and nutrition gain 16 per bite in worlds 3, 4, 7 and 8. The seven sets therefore hold
   **two** distinct contents, not three. Worlds 2, 5 and 6 equal world 1's frozen set, and worlds 3,
   4, 7 and 8 equal one another. The builder's comparison check must confirm both groups. The
   tooling plan's pairs (5/1, 6/2, 7/3, 8/4) become these two groups.
3. **Cross-test in world 1's scenes: yes.** Every agent of worlds 2–8 is also tested in world 1's
   frozen scene set, on its **newest 20 checkpoints** (the estimator's window). It is a secondary
   result and cannot make a group pass. A group whose effect on (c) has opposite signs in its own
   worlds' scenes and in world 1's scenes is flagged **"scene-dependent"**. Because of decision 2,
   for worlds 2, 5 and 6 the cross-test repeats their own-scene test in identical scenes. Those runs
   need no extra sweep: their own-scene results are used for both.

**Reproduction check: header comments may differ.** The tooling plan
([[HALF_FACTORIAL_EVAL_TOOLING]]) replaces the world-1 generator with a general builder. That
builder reproduces world 1's frozen files byte for byte **after removing the leading `#` comment
lines**, and it also checks that each file loads to identical simulator parameters. The header must
differ, because the frozen files name the old generator and a new file claiming to come from it
would misstate where it came from. This specification's reproduction check accepts that: the
requirement is that **everything except leading comment lines** is byte-identical, and that the
simulator's loader gives identical parameters. Literal byte identity including the header is not
required.

## Food-free test scenes, 2026-10-14

**What this is.** The test scenes used so far for this study (world 1's frozen lookalike scenes,
in which every agent is tested) contain **one food item of 6 bites**, placed three cells above the
agent's start. That food item was added when the scenes were written on 2026-10-10 **without the
user deciding it**. So every lookalike and half-factorial test result recorded up to today comes from
scenes with food in them, and an agent's hiding, approach or survival in those scenes may partly reflect
whether it went to eat. On 2026-10-14 the user decided: "Also test without food." A **food-free copy**
of the injury-grid scenes (no animal, hunting predator, wandering rabbit; start injury 0 to 90) now
exists so that every run can be re-tested without the food item and compared with the with-food
results. The original scenes, their results and their sweep specs are **unchanged**.

**What differs.** Only the food item. Each food-free scene is the with-food scene minus the food: the
same shared animal smell, the same predator (notices at 3 cells, pounces from 3 cells, 50% success),
the same bush, injury levels and everything else inherited from the source scene. The source
injury-grid scenes have no resources of their own, so the food-free scenes have none.

**Files.**
- Scenes: `configs/environment/experiment/behavior_probes/lookalike_nofood/injury_grid__neutral_clean/`
  (30 scenes), written by `generate_lookalike_variants.py --no-food`; no-healing copies (healing rate
  0) in `behavior_probes/no_healing/lookalike_nofood__injury_grid__neutral_clean/`.
- Sweep specs (copies of the with-food grid specs, changing only name, scene folder and output folder):
  half-factorial `configs/eval_sweeps/lookalike_hf_nofood/lookalike_hf_nofood_l05_grid_rppo.yaml` and
  `lookalike_hf_nofood_noheal_l05_grid_rppo.yaml` (35 run rows, as in the with-food specs on
  2026-10-14); world 1 `configs/eval_sweeps/lookalike_nofood/lookalike_nofood_l05_grid_rppo.yaml` and
  `lookalike_nofood_noheal_l05_grid_rppo.yaml` (4 run rows). Outputs under
  `results/eval/avoidance/metrics_history_rppo_lookalike_hf_nofood{,_noheal}/grid` and
  `..._lookalike_nofood{,_noheal}/grid`. Only the injury grid is copied; the chasing-rabbit, neutral
  and own-world scene sets are not.
- When a run row is added to a with-food half-factorial spec, add the same row to its food-free copy.

**Checks run (2026-10-14).** The generator's `--check --no-food` confirms every food-free scene
differs from its with-food sibling only in the resources list, that the removed resource is exactly the
6-bite food item, and that the remaining resources equal the source scene's own (empty). The
no-healing generator's `--check` confirms each no-healing copy differs only in the healing rate. Each
new spec passes `run_sweep.py --dry-run` (30 scenes per run), and every scene its worklists name loads
through the eval script's loader (`load_env_config` + `load_env_params`) with no resources, the bush
present, the shared smell and the 3 / 3 / 0.5 predator. The sweeps have not been run.

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
| 1 | done (10M episodes, all finished by 10-13 15:24) | w2 ordinary | `rppo_lookalike_hf_l05_w2_t1none_s42` | `lookalike_half_factorial` | pilot | 42 | 107 | cuda:0 | 2026-10-12T15:07:47 | hodrwsga | logs/20261012_150747_rppo_lookalike_hf_l05_w2_t1none_s42.log |
| 2 | done (10M episodes; resumed from checkpoint 2200035, 10-13 01:54) | w2 modulated | `rppo_lookalike_hf_l05_w2_t16quad_s42` | `lookalike_half_factorial` | pilot | 42 | 113 | cuda:1 | 2026-10-13T01:54:13 | hzmjzl2n | logs/20261013_015413_rppo_lookalike_hf_l05_w2_t16quad_s42.log |
| 3 | done (10M episodes, all finished by 10-13 15:24) | w3 ordinary | `rppo_lookalike_hf_l05_w3_t1none_s42` | `lookalike_half_factorial` | pilot | 42 | 114 | cuda:0 | 2026-10-12T15:13:10 | fp5elazc | logs/20261012_151310_rppo_lookalike_hf_l05_w3_t1none_s42.log |
| 4 | done (10M episodes; resumed from checkpoint 1800026, 10-12 23:46) | w3 modulated | `rppo_lookalike_hf_l05_w3_t16quad_s42` | `lookalike_half_factorial` | pilot | 42 | 114 | cuda:2 | 2026-10-12T23:46:22 | mkeipck0 | logs/20261012_234622_rppo_lookalike_hf_l05_w3_t16quad_s42.log |
| 5 | done (10M episodes; resumed from checkpoint 2000000, 10-13 01:53) | w4 ordinary | `rppo_lookalike_hf_l05_w4_t1none_s42` | `lookalike_half_factorial` | pilot | 42 | 113 | cuda:0 | 2026-10-13T01:53:52 | lwrw17zc | logs/20261013_015352_rppo_lookalike_hf_l05_w4_t1none_s42.log |
| 6 | done (10M episodes, all finished by 10-13 15:24) | w4 modulated | `rppo_lookalike_hf_l05_w4_t16quad_s42` | `lookalike_half_factorial` | pilot | 42 | 114 | cuda:1 | 2026-10-12T15:13:27 | wpnvxfoo | logs/20261012_151327_rppo_lookalike_hf_l05_w4_t16quad_s42.log |
| 7 | done (10M episodes, all finished by 10-13 15:24) | w5 ordinary | `rppo_lookalike_hf_l05_w5_t1none_s42` | `lookalike_half_factorial` | pilot | 42 | 114 | cuda:2 | 2026-10-12T15:13:32 | 8c7yhm2p | logs/20261012_151332_rppo_lookalike_hf_l05_w5_t1none_s42.log |
| 8 | done (10M episodes, all finished by 10-13 15:24) | w5 modulated | `rppo_lookalike_hf_l05_w5_t16quad_s42` | `lookalike_half_factorial` | pilot | 42 | 114 | cuda:3 | 2026-10-12T15:13:38 | 868ghfsm | logs/20261012_151338_rppo_lookalike_hf_l05_w5_t16quad_s42.log |
| 9 | done (10M episodes, all finished by 10-13 15:24) | w6 ordinary | `rppo_lookalike_hf_l05_w6_t1none_s42` | `lookalike_half_factorial` | pilot | 42 | 107 | cuda:1 | 2026-10-12T15:13:43 | ii0erpbj | logs/20261012_151343_rppo_lookalike_hf_l05_w6_t1none_s42.log |
| 10 | done (10M episodes; resumed from checkpoint 2400022, 10-13 02:26) | w6 modulated | `rppo_lookalike_hf_l05_w6_t16quad_s42` | `lookalike_half_factorial` | pilot | 42 | 114 | cuda:3 | 2026-10-13T02:26:39 | kna2fm1p | logs/20261013_022639_rppo_lookalike_hf_l05_w6_t16quad_s42.log |
| 11 | done (10M episodes; resumed from checkpoint 6200055, 10-13 06:02) | w7 ordinary | `rppo_lookalike_hf_l05_w7_t1none_s42` | `lookalike_half_factorial` | pilot | 42 | 114 | cuda:0 | 2026-10-13T06:01:59 | qs8mbvac | logs/20261013_060159_rppo_lookalike_hf_l05_w7_t1none_s42.log |
| 12 | done (10M episodes, all finished by 10-13 15:24) | w7 modulated | `rppo_lookalike_hf_l05_w7_t16quad_s42` | `lookalike_half_factorial` | pilot | 42 | 112 | cuda:0 | 2026-10-12T15:13:54 | jrkazhnc | logs/20261012_151354_rppo_lookalike_hf_l05_w7_t16quad_s42.log |
| 13 | done (10M episodes, all finished by 10-13 15:24) | w8 ordinary | `rppo_lookalike_hf_l05_w8_t1none_s42` | `lookalike_half_factorial` | pilot | 42 | 112 | cuda:1 | 2026-10-12T15:09:06 | wsi9563u | logs/20261012_150906_rppo_lookalike_hf_l05_w8_t1none_s42.log |
| 14 | done (10M episodes; resumed from checkpoint 4800028, 10-13 05:29) | w8 modulated | `rppo_lookalike_hf_l05_w8_t16quad_s42` | `lookalike_half_factorial` | pilot | 42 | 102 | cuda:0 | 2026-10-13T05:29:33 | plx8nfgr | logs/20261013_052933_rppo_lookalike_hf_l05_w8_t16quad_s42.log |


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

### Seed 43 and 44 replication (launched 2026-10-13)

User decisions, 2026-10-13: train seeds 43 and 44 of all 14 runs; **one run per card**; worlds 4, 6, 7 and 8 first.
Departure from the "3090-class" note above: the user chose to also use RTX 2080 Ti cards (nodes 101, 103, 104, 105).
The first 14 were launched by the training-runner; their logs are node-local (`/home/vncuser/logs/` on the node shown),
because the `--log` path was relative. The other 14 are queued in `tmp/20261013_hf_seeds_watch/` (`queue.json`, `watch.py`),
which starts each on the next card free on two checks 15 min apart (order: w8 s44, then w2/w3/w5 s43, then s44) and
resumes any run that stops. Command line identical to seed 42 except `--seed`, `--device` and the tag.

**Node 112 kept free (user, 2026-10-14 15:35):** a lab member needs a node, so node 112 (2 × RTX 3090) was taken
out of the queue program's card list. Its run still in progress, w8 modulated s44, is moved off when a card frees
elsewhere (stopped right after its next checkpoint, resumed there under the same WandB run, before the last queued
run starts); w8 ordinary s44 finishes on 112:0 itself. A moved run shows its cards as `112:1 → <new card>`.
The table below is refreshed from the logs by `tmp/20261014_hf_seed_tests/update_run_table.py` (status: training
progress in episodes, or finished and tested in world 1's scenes).

| Cell | Tag (= wandb-name) | Seed | Node:GPU | Launched at | WandB run ID | Status |
|---|---|---|---|---|---|---|
| w4 ordinary | `rppo_lookalike_hf_l05_w4_t1none_s43` | 43 | 114:0 | 2026-10-13T23:28:03 | jbosyem7 | finished, tested |
| w4 modulated | `rppo_lookalike_hf_l05_w4_t16quad_s43` | 43 | 114:1 | 2026-10-13T23:28:24 | u9yxm5ot | finished, tested |
| w6 ordinary | `rppo_lookalike_hf_l05_w6_t1none_s43` | 43 | 114:2 | 2026-10-13T23:28:44 | 31ve5q96 | finished, tested |
| w6 modulated | `rppo_lookalike_hf_l05_w6_t16quad_s43` | 43 | 114:3 | 2026-10-13T23:29:05 | kh6ity00 | finished, tested |
| w7 ordinary | `rppo_lookalike_hf_l05_w7_t1none_s43` | 43 | 113:0 | 2026-10-13T23:29:26 | 3kmi8i82 | finished, tested |
| w7 modulated | `rppo_lookalike_hf_l05_w7_t16quad_s43` | 43 | 113:1 | 2026-10-13T23:29:46 | g86nmpp5 | finished, tested |
| w8 ordinary | `rppo_lookalike_hf_l05_w8_t1none_s43` | 43 | 105:0 | 2026-10-13T23:30:07 | 9sef1pks | finished, tested |
| w8 modulated | `rppo_lookalike_hf_l05_w8_t16quad_s43` | 43 | 105:1 | 2026-10-13T23:30:28 | dafbu78p | finished, tested |
| w4 ordinary | `rppo_lookalike_hf_l05_w4_t1none_s44` | 44 | 101:0 | 2026-10-13T23:30:50 | ph6q6a72 | finished, tested |
| w4 modulated | `rppo_lookalike_hf_l05_w4_t16quad_s44` | 44 | 101:1 | 2026-10-13T23:31:10 | qgt9l0ne | finished, tested |
| w6 ordinary | `rppo_lookalike_hf_l05_w6_t1none_s44` | 44 | 103:0 | 2026-10-13T23:31:31 | d6ho30qy | finished, tested |
| w6 modulated | `rppo_lookalike_hf_l05_w6_t16quad_s44` | 44 | 103:1 | 2026-10-13T23:31:52 | 774mpxfv | finished, tested |
| w7 ordinary | `rppo_lookalike_hf_l05_w7_t1none_s44` | 44 | 104:0 | 2026-10-13T23:32:13 | t1emm55h | finished, tested |
| w7 modulated | `rppo_lookalike_hf_l05_w7_t16quad_s44` | 44 | 104:1 | 2026-10-13T23:32:34 | msskvxt5 | finished, tested |
| w8 ordinary | `rppo_lookalike_hf_l05_w8_t1none_s44` | 44 | 112:0 | 2026-10-14T01:08:40 | 1u6r6qmv | finished, tested |
| w8 modulated | `rppo_lookalike_hf_l05_w8_t16quad_s44` | 44 | 112:1 → 114:2 → 105:0 | 2026-10-14T01:09:00 | zu54un6n | finished, tested |
| w2 ordinary | `rppo_lookalike_hf_l05_w2_t1none_s43` | 43 | 102:0 | 2026-10-14T01:42:14 | kwcnjojc | finished, tested |
| w2 modulated | `rppo_lookalike_hf_l05_w2_t16quad_s43` | 43 | 107:0 | 2026-10-14T01:42:36 | o6ammaq7 | finished, tested |
| w3 ordinary | `rppo_lookalike_hf_l05_w3_t1none_s43` | 43 | 107:1 | 2026-10-14T01:42:56 | ahfv4r0j | finished, tested |
| w3 modulated | `rppo_lookalike_hf_l05_w3_t16quad_s43` | 43 | 102:1 | 2026-10-14T02:16:45 | 045e3jpn | finished, tested |
| w5 ordinary | `rppo_lookalike_hf_l05_w5_t1none_s43` | 43 | 114:2 | 2026-10-14T09:11:55 | hbj7v855 | finished, tested |
| w5 modulated | `rppo_lookalike_hf_l05_w5_t16quad_s43` | 43 | 113:0 → 104:0 | 2026-10-14T10:31:27 | h5aerd6t | finished, tested |
| w2 ordinary | `rppo_lookalike_hf_l05_w2_t1none_s44` | 44 | 114:3 → 103:1 | 2026-10-14T11:50:31 | vtu6ryat | finished, tested |
| w2 modulated | `rppo_lookalike_hf_l05_w2_t16quad_s44` | 44 | 102:0 | 2026-10-14T13:24:34 | 58s13gbi | finished, tested |
| w3 ordinary | `rppo_lookalike_hf_l05_w3_t1none_s44` | 44 | 113:1 → 107:1 | 2026-10-14T13:24:54 | 388uegdg | finished, tested |
| w3 modulated | `rppo_lookalike_hf_l05_w3_t16quad_s44` | 44 | 114:0 → 102:1 | 2026-10-14T14:13:12 | o8p3r8ue | finished, tested |
| w5 ordinary | `rppo_lookalike_hf_l05_w5_t1none_s44` | 44 | 103:0 | 2026-10-14T15:32:14 | s3aoryo4 | finished, tested |
| w5 modulated | `rppo_lookalike_hf_l05_w5_t16quad_s44` | 44 | 114:1 → 107:0 | 2026-10-14T18:26:15 | iiuwsiv9 | finished, tested |
| w8 ordinary | `rppo_lookalike_hf_l05_w8_t1none_s45` | 45 | 114:0 | 2026-10-14T22:02:47 | asluo6n1 | finished and tested, with and without food (2026-10-15) |
| w8 modulated | `rppo_lookalike_hf_l05_w8_t16quad_s45` | 45 | 114:1 | 2026-10-14T22:26:39 | srfs0e56 | finished and tested, with and without food (2026-10-15) |
| w8 ordinary | `rppo_lookalike_hf_l05_w8_t1none_s46` | 46 | 114:2 | 2026-10-14T22:36:17 | owkti0xt | finished and tested, with and without food (2026-10-15) |
| w8 modulated | `rppo_lookalike_hf_l05_w8_t16quad_s46` | 46 | 114:3 | 2026-10-14T22:51:28 | o8m7w6k2 | finished and tested, with and without food (2026-10-15) |

**World 8 extra seeds 45 and 46 (user, 2026-10-14 ~22:00):** both agents, same command as the other seeds
except `--seed`; the user wants more seeds for world 8. Placed on node 114 (four free cards) one run at a time,
starting with w8 ordinary s45 and adding the next only after ~20 min with the node up, because 113/114 crashed
twice that evening (see docs/environment/TRAINING_OPERATIONS.md §6-7).

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

## Complementary half: worlds 9–16 (added 2026-10-15)

**What this is.** The first eight worlds each switch an **even** number of groups to their new
value (none, two, or all four). That is what made them a half: with 8 of the 16 combinations, some
effects cannot be told apart. For example, "bigger food matters more when hazards are hidden"
(B × C) looks exactly like "the new predator matters more when hazards are fewer and heavier"
(A × D). On 2026-10-15 the user approved training the **other eight combinations**, every world
that switches an **odd** number of groups (one or three). For example, world 9 changes only the
predator (A), and world 16 changes everything except the predator (B, C and D). Together, the two
halves are the **full factorial**: all 16 combinations of the four groups. Each world is trained
with both agents (ordinary and modulated): 16 runs at seed 42 now, then 32 more at seeds 43 and 44
as cards free. Nothing else changes: same group values, agents, training command and tests.

| World | A threat | B food | C concealment | D hazard load | Config (`configs/environment/experiment/basic/`) |
|---|---|---|---|---|---|
| 9 | + | − | − | − | `lookalike_hf_w9_newA_10x10.yaml` |
| 10 | − | + | − | − | `lookalike_hf_w10_newB_10x10.yaml` |
| 11 | − | − | + | − | `lookalike_hf_w11_newC_10x10.yaml` |
| 12 | − | − | − | + | `lookalike_hf_w12_newD_10x10.yaml` |
| 13 | + | + | + | − | `lookalike_hf_w13_newABC_10x10.yaml` |
| 14 | + | + | − | + | `lookalike_hf_w14_newABD_10x10.yaml` |
| 15 | + | − | + | + | `lookalike_hf_w15_newACD_10x10.yaml` |
| 16 | − | + | + | + | `lookalike_hf_w16_newBCD_10x10.yaml` |

### Defining relation, and what the two halves together allow

- **First half (worlds 1–8):** D = A × B × C, defining relation **I = +ABCD**. Every world has an
  even number of "+" signs.
- **This half (worlds 9–16):** D = −A × B × C, defining relation **I = −ABCD**. Every world has an
  odd number of "+" signs. On its own it is also a resolution-IV half fraction. Its alias pairs are
  the same as the first half's, with the opposite sign: there, the A × B contrast estimates
  AB + CD; here it estimates AB − CD. Main effects are aliased with three-group interactions
  (A with −BCD here, +BCD there).
- **Both halves together: the full 2⁴ factorial.** Its 15 contrasts are 4 main effects,
  **6 two-group interactions, each now estimated on its own** (A×B, A×C, A×D, B×C, B×D, C×D), 4
  three-group interactions and the four-group interaction. Averaging the two halves' estimates
  cancels the alias: ((AB + CD) + (AB − CD)) / 2 = AB. Each main effect and each interaction
  becomes a comparison of **8 worlds against 8**, not 4 against 4.
- **Batch effect lands on the four-group interaction only.** The two halves are trained in
  separate batches (different days and card mix). Any systematic difference between the batches
  shows up only in the ABCD contrast, because ABCD is the contrast that separates the halves. It
  does not touch any main effect or two-group interaction. That holds only if the code and every
  shared config layer are identical across the batches, and if the card type is the same. **Checked
  2026-10-15:** the world-1 reuse re-check (item 4, all listed paths) prints no commit since
  `1f1b7b26` and no uncommitted change. The four-group interaction is therefore **not
  interpreted**. On launch morning the check is repeated, together with
  `timeout 120 git diff bf48ba07 -- configs/environment/experiment/basic/lookalike_hf_*`, which must
  print nothing (the 15 world configs themselves are unchanged). Either check failing stops the
  launch.
- **Card type is kept the same as the first half's seed 42 (user, 2026-10-15).** RTX 2080 Ti cards
  compute in full 32-bit precision. RTX 3090, 4090 and 6000 Ada cards use the lower-precision TF32
  format by default (KNOWN_BUGS, matmul precision row). All first-half seed-42 runs, and world 1's
  seeds 42 and 43, trained on TF32 cards. So every world 9–16 run, at every seed, trains on a
  TF32 card. Precision then cannot vary between the halves, or within one. See "Run plan" for the
  card rules.
- **World 1's offset shrinks.** The world-1 runs are reused from 2026-10-09 (see "World 1 reuse").
  In the full factorial, world 1 is one world of 16, so a shift δ in it moves every contrast by
  ±δ/8 instead of δ/4.

### Exact values: byte-identical to the first half

Each new world sets exactly the keys the first half sets for each group, with the same values and
the same comments ("Exact values" table above). A world redeclares only the lists its new groups
touch, as in the first half: the resource list for B, C or D, the animal list for A, the obstacle
list for C or D, and `body:` for B. Each redeclared list is restated in full.

**How they were made.** A generator (session scratchpad, not committed) starts from world 8 (all
groups new). For each group at its current value, it drops that group's tagged lines (C) or
replaces them with the current-value line taken from an existing first-half world. It leaves out
lists no new group touches. Run on the first half, it **reproduces worlds 2–8 byte for byte**, so
the new files follow the first half's construction exactly.

**Verification (2026-10-15, CPU, working tree at `4b4898f4` plus the eight new files).**
Configs were assembled in `train.py`'s own order (default → train defaults → rPPO train defaults →
evaluation defaults → logger → visualization → `load_env_config(--config)` → ordinary-agent
config).

1. **The assembly matches what the trainer saved.** For worlds 1–8, the world-side sections
   (`environment`, `body`, `sensory`, `thermal`, `water`, `perceptual_noise`) of today's
   assembly equal the `models/config.yaml` saved by every seed-42 ordinary-agent run folder
   (11 folders including resumes): 309–311 leaf keys, **0 differ**.
2. **Every leaf in all 16 worlds is as intended.** Each world-side leaf equals world 1's value,
   except the leaves of groups at their new level, which equal world 8's value. Result: **0
   unexpected leaves in all 16 worlds**. Worlds 9–16 differ from world 1 in 4 (A), 3 (B), 2 (C),
   5 (D), 9 (ABC), 12 (ABD), 11 (ACD) and 10 (BCD) leaves, which is exactly the sum of their
   groups' key counts (A 4, B 3, C 2, D 5). So each group's level is identical in both halves.
3. **The simulator's parameters agree.** For each group, the eight (new world, old world) pairs
   that differ only in that group differ in **the same set of simulator fields**
   (`load_env_params`). C changes only `res_visual_mask` and `obs_visual_mask`. A, B and D also
   change the slot arrays, because the simulator sizes those by the entity counts.
4. **Every world loads, resets and steps.** `jax_reset` and 5 × `jax_step` run without error.
   The observation is **58 numbers wide** in all 16 worlds. Over 300 starts, A+ worlds always have
   exactly 1 predator, and A− worlds have 0/1/2 predators in 118/100/82 starts, the same as world 1.
   The loaded values match the "Exact values" table in every world: noticing distance and pounce
   reach 2–3 (A+); 1–3 food items, 9 bites, gain 16 (B+); traps and rocks with visual mask 2,
   meaning never visible (C+); 4–8 rocks, 3–6 traps, trap damage 25–60 (D+).

**Critical-settings registry:** no registry setting changes value. As in the first half, no
change-log entry is required. **No new keys.** `default.yaml` is untouched. The maintained
`basic/` folder now holds 15 screen worlds that every schema change must carry (see "Config-system
bookkeeping", folder placement).

### Run plan

- **Seed 42 first:** 8 worlds × 2 agents = **16 runs** (manifest below). **8 start now** (runs
  15–22, worlds 9–12), and the other 8 start as TF32 cards free, in run order.
- **Seeds 43 and 44 next:** 32 runs for worlds 9–16, plus **world 1 at seed 44** (2 runs, approved
  by the user 2026-10-15), queued as TF32 cards free. Same command line except `--seed`, `--device`
  and the tag (`..._s43`, `..._s44`). Order: world 1 seed 44 first (it completes the first half's
  3 seeds), then all of seed 43 for worlds 9–16, then all of seed 44, by world number within a
  seed, with both agents of a world together. The queue is in "Seeds 43 and 44 queue" below.
- **Queue mechanism (user, 2026-10-15).** Every launch and every resume goes through the
  `training-runner` agent, spawned by the orchestrating session when a card frees. **No watcher
  script launches or resumes runs**: the 2026-10-13 `watch.py` is not reused. Each launch carries
  the runner's checklist: launch file entry, this doc's run table, diary row, absolute log path.
- **Agents, flags, horizon:** the same as the first half. Ordinary agent `nmngaenorm_t1none.yaml`,
  modulated agent `nmngaenorm_t16quad_ALL.yaml`. `--episodes 10000000` (10 M steps),
  `--log-interval 10`. `--num-envs` and `--checkpoint-frequency` stay config-owned. WandB group
  `lookalike_half_factorial`, job type `pilot`.
- **World 1 at seed 44 (approved, user 2026-10-15).** World 1 had seeds 42 and 43 only (the
  2026-10-09 lookalike pilot). Its two seed-44 runs use the lookalike world config
  (`lookalike_animals_close_pounce_small_food_10x10.yaml`) with the same flags. Tags
  `rppo_lookalike_l05_t1none_s44` and `rppo_lookalike_l05_t16quad_s44`, WandB group
  `lookalike_animals`, the same group as world 1's seeds 42 and 43.
- **Cards (user, 2026-10-15): TF32 cards only.** That means RTX 3090, RTX 4090 or RTX 6000 Ada,
  one run per card. **RTX 2080 Ti cards (nodes 101, 103, 104, 105) are never used for this study's
  training.** Node 112 is reserved for a lab member and not used. On node 114, add one run at a time
  and wait until the node has stayed up (it crashed twice on 2026-10-14). **A run never moves
  between card types:** a resume goes to a TF32 card as well. The card of every run segment is
  recorded in the run table.
  - **Exception (user, 2026-10-15 ~20:08):** the user approved RTX 2080 Ti cards (nodes 101–105)
    for the four seed-42 runs of worlds 15 and 16 (runs 27–30). So worlds 15 and 16 are flagged
    card-dependent in the seed-42 analysis, like the first half's mixed-card repeats. The
    "restart from scratch on a TF32 card" failure mode does not apply to these four runs.
- **Compute:** about 12.7 h (ordinary) and 16.7 h (modulated) per run on an RTX 3090. That is
  ≈ 235 GPU-hours for seed 42 (≈ 17 h of wall time per 8-run wave), ≈ 470 GPU-hours more for
  seeds 43 and 44, and ≈ 30 GPU-hours for world 1 at seed 44.
- **Known limitation: the first half's seeds 43 and 44 mixed card types.** Before the TF32-only
  rule, some first-half repeat runs trained on 2080 Tis (run table "Seed 43 and 44 replication"):
  at seed 43, world 8 (both agents) fully, and world 5 modulated after a move; at seed 44, worlds 4,
  6 and 7 (both agents) and world 5 ordinary fully, and world 2 ordinary and world 8 modulated
  after a move. This cannot be undone. So at seeds 43 and 44, card type is not balanced across the
  first half's worlds, and it can leak into those contrasts. Two consequences for the analysis:
  the **seed-42 full-factorial read is the hardware-clean reference** (all 32 runs on TF32 cards),
  and every 3-seed contrast is also reported with the 2080 Ti segments' runs flagged. If leaving
  them out changes a verdict, the verdict is reported as "card-dependent".

### Tests: the same as the first half

Every new run is tested exactly like the first half's runs: in **world 1's frozen test scenes**,
with food and without food, with healing and without, at every saved checkpoint. Concretely, each
run gets a row (label `hf_w<k>_<ordinary|modulated>_s<seed>`, path = its results folder) in all
nine first-half test specs:

- with food, healing on: `configs/eval_sweeps/lookalike_hf/lookalike_hf_l05_{grid,gridchase,neutral,own}_rppo.yaml`
- with food, healing off: `configs/eval_sweeps/lookalike_hf/lookalike_hf_noheal_l05_{grid,gridchase,neutral}_rppo.yaml`
- without food: `configs/eval_sweeps/lookalike_hf_nofood/lookalike_hf_nofood_l05_grid_rppo.yaml` and
  `lookalike_hf_nofood_noheal_l05_grid_rppo.yaml`

The rows can only be written once a run's results folder exists, because the folder name carries the
launch time. They are added at launch, as for seeds 43–46, and not here. The per-world scene sets
stay deferred for all 16 worlds. Recorded evaluation rollouts in each run's own training world
(readouts (a), (b) and the surprise response) follow "Data" above unchanged.

### Analysis of the full factorial (pre-specified)

The first half's pass rule stands, as written, for the first half's own read. The full-factorial
read uses the same readouts, data rules, minimums, checkpoint rules (6, 8 and 10 M sign agreement;
whole-training view) and agent rule. It changes four items, and adds a rule for when the two reads
disagree (item 5):

1. **Seeds.** Contrasts use the seeds present in **all 16 worlds and both agents**: seed 42 alone
   at first, then 42–43, then 42–44. World 8's extra seeds 45 and 46 are reported beside it, but kept out of
   the balanced contrasts. Within each agent, a world's value is the mean over those seeds.
2. **Noise from the experiment itself (plan review 2026-10-15).** As soon as **every one of the 16
   worlds has 2 or more seeds** of both agents, σ is the pooled within-world standard deviation
   across seeds, with n = the number of seeds present in all 16 worlds. That gives 16 × (n − 1)
   degrees of freedom per agent: 16 at n = 2, 32 at n = 3. This replaces the borrowed fast-heal σ,
   which is reported beside it. Before that point (seed 42 only), the first half's σ rule (item 1
   of the pass rule) applies.
3. **Bar.** A contrast is the mean, over the two agents, of (mean of the 8 "+" worlds − mean of the
   8 "−" worlds). With n seeds per world and per-run bootstrap errors SE_i over the 32n runs:

   $$
   \mathrm{SD}_{\text{contrast}} = \sqrt{\frac{\sigma^2}{8n} + \frac{1}{(16n)^2}\sum_{i=1}^{32n} SE_i^2}
   $$

   The bar is 2 × SD_contrast, as before. At n = 1 with negligible sampling error, this is
   0.71σ (the first half's bar was σ). At n = 3 it is 0.41σ.
4. **Interactions.** The six two-group interactions are each reported against the same bar, under
   their own names. Three-group interactions are descriptive only. The four-group interaction is
   not interpreted (batch effect, see above). Interactions are a secondary result and cannot make
   a group "worth replicating". **Chance crossings:** the bar is 2 SD, so with 4 main effects and 6
   two-group interactions (10 terms) about **0.46 terms are expected to cross it by chance** when
   nothing is going on (10 × 0.046, about 0.4–0.5; more if σ is underestimated). This is stated beside the interaction table. An interaction
   that crosses the bar is described as an interaction only if its sign also agrees at 6, 8 and
   10 M. Otherwise it stays descriptive.
5. **When the first-half read and the full-factorial read disagree (plan review 2026-10-15).** A
   disagreement means: a group passes in one read and not in the other, or the two effects have
   opposite signs. Then **neither read decides**. The group is reported as **"unresolved: halves
   disagree"**, never as "worth replicating", with both numbers and the two halves' separate
   estimates. Reason: the first half estimates a main effect plus a three-group interaction (for
   example A + BCD), and this half estimates the main effect minus it (A − BCD). So a disagreement
   is itself evidence of a three-group interaction (or of a batch difference). It is reported as
   that, and not resolved by picking the read that looks better. Where the two reads agree, the
   full-factorial numbers are quoted, because they compare 8 worlds against 8 and carry no alias.

**What had been seen before these full-factorial rules were written (2026-10-15).** The rules
above were written after the first half's test-scene results had been analysed and published on
the half-factorial results page. The last four versions came out on 2026-10-15: v8 `e02a45ac`,
v9 `e4d8548f`, v10 `75a46b1f`, v11 `e1680e78`. Earlier versions from 2026-10-14 showed the repeat
seeds coming in. Seen by then:

- **Readout (c) and its descriptives**, measured in world 1's frozen scenes, for worlds 1–8 at seeds
  42–44 (world 8 also 45 and 46), both agents, with and without food, healing on and off. That
  includes bush dwell by injury 0–90, the rabbit's extra bush dwell, the injury contrast over
  training, hiding with each animal at injuries 10–90, and a level-05 reference.
- **The first half's group effects on the injury contrast** (healing off, injury 70; bar 7.3
  points): predator change A +27, hidden hazards C +14, fewer but heavier hazards D −15, bigger
  food B no clear effect. Two of the three interaction pairs also cleared the bar. World 6 (A + C)
  showed the strongest pattern (+66 and +55 points). Seven of the 14 new seed-42 agents passed the
  hypervigilance check.

**Not seen:** readouts (a), (b) and the surprise response (their tooling is not built yet, see
"Metrics requested"); any rollout in a run's own training world; and anything from worlds 9–16.
So the rules in items 1–5 could have been shaped by the readout-(c) results, but not by the other
readouts. The disagreement rule (item 5) is deliberately conservative for that reason.

### Failure modes specific to this half

- A new world whose run collapses twice (first-half rule) is reported as untrainable. The full
  factorial is then **not** analysed as a balanced design. The first half's analysis stands, and
  the user decides how to proceed.
- If the launch-morning re-check finds a behaviour-changing commit, or the world configs differ
  from `bf48ba07`, the batch effect is no longer limited to GPU nondeterminism. Do not launch:
  ask the user.
- If a world 9–16 run lands on a 2080 Ti by mistake, or is resumed on one, that run segment is
  invalid for this study. The run is restarted from scratch on a TF32 card with the same seed and
  tag, and the WandB run of the invalid attempt is marked in the run table.

### Launch manifest (worlds 9–16, seed 42)

Tag = WandB name, same format as the first half. Runs are numbered on from the first half (1–14).
Odd-numbered runs use the ordinary agent, even-numbered runs the modulated agent. TF32 cards
only (see "Run plan"). Runs 15–22 start now and runs 23–30 as cards free. The training-runner
fills the empty columns, and the GPU column names the card model (for example `107:0 (3090)`).

| Run | Status | Cell | Tag (= wandb-name) | wandb-group | wandb-job-type | Seed | Node | GPU | Launched at | WandB run ID | Log path |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 15 | done | w9 ordinary | `rppo_lookalike_hf_l05_w9_t1none_s42` | `lookalike_half_factorial` | pilot | 42 | 102 | `102:0 (4090)` | 2026-10-15T19:44:28 | `nhzf0g38` | `/media/nas01/projects/Interoceptive-AI/grid_world_pain/logs/20261015_194428_rppo_lookalike_hf_l05_w9_t1none_s42.log` |
| 16 | done | w9 modulated | `rppo_lookalike_hf_l05_w9_t16quad_s42` | `lookalike_half_factorial` | pilot | 42 | 102 | `102:1 (4090)` | 2026-10-15T19:44:32 | `bm4f7ip1` | `/media/nas01/projects/Interoceptive-AI/grid_world_pain/logs/20261015_194432_rppo_lookalike_hf_l05_w9_t16quad_s42.log` |
| 17 | done | w10 ordinary | `rppo_lookalike_hf_l05_w10_t1none_s42` | `lookalike_half_factorial` | pilot | 42 | 107 | `107:0 (3090)` | 2026-10-15T19:44:29 | `j4c5pule` | `/media/nas01/projects/Interoceptive-AI/grid_world_pain/logs/20261015_194429_rppo_lookalike_hf_l05_w10_t1none_s42.log` |
| 18 | running | w10 modulated | `rppo_lookalike_hf_l05_w10_t16quad_s42` | `lookalike_half_factorial` | pilot | 42 | 107 | 107:1 (3090) | 2026-10-15T19:44:36 | `2r7kmtm8` | `/media/nas01/projects/Interoceptive-AI/grid_world_pain/logs/20261015_194435_rppo_lookalike_hf_l05_w10_t16quad_s42.log` |
| 19 | done | w11 ordinary | `rppo_lookalike_hf_l05_w11_t1none_s42` | `lookalike_half_factorial` | pilot | 42 | 106 | `106:1 (3090)` | 2026-10-15T19:44:29 | `wnchg7l6` | `logs/20261015_194429_rppo_lookalike_hf_l05_w11_t1none_s42.log` |
| 20 | running | w11 modulated | `rppo_lookalike_hf_l05_w11_t16quad_s42` | `lookalike_half_factorial` | pilot | 42 | 109 | `109:1 (3090)` | 2026-10-15T19:44:37 | `6sd1wrp6` | `/media/nas01/projects/Interoceptive-AI/grid_world_pain/logs/20261015_194436_rppo_lookalike_hf_l05_w11_t16quad_s42.log` |
| 21 | done | w12 ordinary | `rppo_lookalike_hf_l05_w12_t1none_s42` | `lookalike_half_factorial` | pilot | 42 | 110 | `110:1 (3090)` | 2026-10-15T19:44:44 | `tj7mrstm` | `/media/nas01/projects/Interoceptive-AI/grid_world_pain/logs/20261015_194443_rppo_lookalike_hf_l05_w12_t1none_s42.log` |
| 22 | running | w12 modulated | `rppo_lookalike_hf_l05_w12_t16quad_s42` | `lookalike_half_factorial` | pilot | 42 | 111 | `111:1 (3090)` | 2026-10-15T19:44:49 | `xtubdd4o` | `/media/nas01/projects/Interoceptive-AI/grid_world_pain/logs/20261015_194449_rppo_lookalike_hf_l05_w12_t16quad_s42.log` |
| 23 | done | w13 ordinary | `rppo_lookalike_hf_l05_w13_t1none_s42` | `lookalike_half_factorial` | pilot | 42 | 114 | `114:0 (6000 Ada)` | 2026-10-15T20:08:09 | `dvfeqj5j` | `/media/nas01/projects/Interoceptive-AI/grid_world_pain/logs/20261015_200809_rppo_lookalike_hf_l05_w13_t1none_s42.log` |
| 24 | done | w13 modulated | `rppo_lookalike_hf_l05_w13_t16quad_s42` | `lookalike_half_factorial` | pilot | 42 | 114 | `114:1 (6000 Ada)` | 2026-10-15T20:14:10 | `fykdkmn7` | `/media/nas01/projects/Interoceptive-AI/grid_world_pain/logs/20261015_201410_rppo_lookalike_hf_l05_w13_t16quad_s42.log` |
| 25 | done | w14 ordinary | `rppo_lookalike_hf_l05_w14_t1none_s42` | `lookalike_half_factorial` | pilot | 42 | 114 | `114:2 (6000 Ada)` | 2026-10-15T20:19:20 | `jimub1xl` | `/media/nas01/projects/Interoceptive-AI/grid_world_pain/logs/20261015_201920_rppo_lookalike_hf_l05_w14_t1none_s42.log` |
| 26 | running | w14 modulated | `rppo_lookalike_hf_l05_w14_t16quad_s42` | `lookalike_half_factorial` | pilot | 42 | 114 | `114:3 (6000 Ada)` | 2026-10-15T20:23:57 | `uz7g677v` | `/media/nas01/projects/Interoceptive-AI/grid_world_pain/logs/20261015_202356_rppo_lookalike_hf_l05_w14_t16quad_s42.log` |
| 27 | done | w15 ordinary | `rppo_lookalike_hf_l05_w15_t1none_s42` | `lookalike_half_factorial` | pilot | 42 | 101 | `101:0 (2080 Ti, user-approved)` | 2026-10-15T20:09:52 | `5qe5vgcq` | `/media/nas01/projects/Interoceptive-AI/grid_world_pain/logs/20261015_200951_rppo_lookalike_hf_l05_w15_t1none_s42.log` |
| 28 | running | w15 modulated | `rppo_lookalike_hf_l05_w15_t16quad_s42` | `lookalike_half_factorial` | pilot | 42 | 101 | `101:1 (2080 Ti, user-approved)` | 2026-10-15T20:10:03 | `9pkqdsyb` | `/media/nas01/projects/Interoceptive-AI/grid_world_pain/logs/20261015_201002_rppo_lookalike_hf_l05_w15_t16quad_s42.log` |
| 29 | running | w16 ordinary | `rppo_lookalike_hf_l05_w16_t1none_s42` | `lookalike_half_factorial` | pilot | 42 | 103 | `103:0 (2080 Ti, user-approved)` | 2026-10-15T20:10:15 | `v60ekjt5` | `/media/nas01/projects/Interoceptive-AI/grid_world_pain/logs/20261015_201014_rppo_lookalike_hf_l05_w16_t1none_s42.log` |
| 30 | running | w16 modulated | `rppo_lookalike_hf_l05_w16_t16quad_s42` | `lookalike_half_factorial` | pilot | 42 | 103 | `103:1 (2080 Ti, user-approved)` | 2026-10-15T20:10:22 | `v1sg3xfk` | `/media/nas01/projects/Interoceptive-AI/grid_world_pain/logs/20261015_201021_rppo_lookalike_hf_l05_w16_t16quad_s42.log` |

#### Configs to produce (worlds 9–16)

| Runs | Env config (`configs/environment/experiment/basic/`) | Agent config (`configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/`) |
|---|---|---|
| 15, 16 | `lookalike_hf_w9_newA_10x10.yaml` | `nmngaenorm_t1none.yaml` / `nmngaenorm_t16quad_ALL.yaml` |
| 17, 18 | `lookalike_hf_w10_newB_10x10.yaml` | same pair |
| 19, 20 | `lookalike_hf_w11_newC_10x10.yaml` | same pair |
| 21, 22 | `lookalike_hf_w12_newD_10x10.yaml` | same pair |
| 23, 24 | `lookalike_hf_w13_newABC_10x10.yaml` | same pair |
| 25, 26 | `lookalike_hf_w14_newABD_10x10.yaml` | same pair |
| 27, 28 | `lookalike_hf_w15_newACD_10x10.yaml` | same pair |
| 29, 30 | `lookalike_hf_w16_newBCD_10x10.yaml` | same pair |

#### Launch block (for `train_command-agent.sh`; the training-runner adds it and fills in `[node:GPU]`)

Run the launch-morning re-check (World 1 reuse, item 4) first. Use absolute log paths, so logs land
on the NAS (the first seed-43/44 launches used a relative path, and their logs stayed on the nodes).

```
# ---------------------------------------------------------------------------
# lookalike half-factorial, COMPLEMENTARY half: worlds 9-16 x 2 agents at level 05, seed 42 (16 runs)
# Plan: docs/experiments/active/hypervigilance/LOOKALIKE_HALF_FACTORIAL_L05.md ("Complementary half: worlds 9-16").
# [N:G] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/lookalike_hf_w9_newA_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml --episodes 10000000 --seed 42 --device cuda:G --log-interval 10 --tag "rppo_lookalike_hf_l05_w9_t1none_s42" --wandb-name "rppo_lookalike_hf_l05_w9_t1none_s42" --wandb-group "lookalike_half_factorial" --wandb-job-type "pilot"
# [N:G] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/lookalike_hf_w9_newA_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml --episodes 10000000 --seed 42 --device cuda:G --log-interval 10 --tag "rppo_lookalike_hf_l05_w9_t16quad_s42" --wandb-name "rppo_lookalike_hf_l05_w9_t16quad_s42" --wandb-group "lookalike_half_factorial" --wandb-job-type "pilot"
# [N:G] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/lookalike_hf_w10_newB_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml --episodes 10000000 --seed 42 --device cuda:G --log-interval 10 --tag "rppo_lookalike_hf_l05_w10_t1none_s42" --wandb-name "rppo_lookalike_hf_l05_w10_t1none_s42" --wandb-group "lookalike_half_factorial" --wandb-job-type "pilot"
# [N:G] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/lookalike_hf_w10_newB_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml --episodes 10000000 --seed 42 --device cuda:G --log-interval 10 --tag "rppo_lookalike_hf_l05_w10_t16quad_s42" --wandb-name "rppo_lookalike_hf_l05_w10_t16quad_s42" --wandb-group "lookalike_half_factorial" --wandb-job-type "pilot"
# [N:G] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/lookalike_hf_w11_newC_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml --episodes 10000000 --seed 42 --device cuda:G --log-interval 10 --tag "rppo_lookalike_hf_l05_w11_t1none_s42" --wandb-name "rppo_lookalike_hf_l05_w11_t1none_s42" --wandb-group "lookalike_half_factorial" --wandb-job-type "pilot"
# [N:G] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/lookalike_hf_w11_newC_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml --episodes 10000000 --seed 42 --device cuda:G --log-interval 10 --tag "rppo_lookalike_hf_l05_w11_t16quad_s42" --wandb-name "rppo_lookalike_hf_l05_w11_t16quad_s42" --wandb-group "lookalike_half_factorial" --wandb-job-type "pilot"
# [N:G] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/lookalike_hf_w12_newD_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml --episodes 10000000 --seed 42 --device cuda:G --log-interval 10 --tag "rppo_lookalike_hf_l05_w12_t1none_s42" --wandb-name "rppo_lookalike_hf_l05_w12_t1none_s42" --wandb-group "lookalike_half_factorial" --wandb-job-type "pilot"
# [N:G] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/lookalike_hf_w12_newD_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml --episodes 10000000 --seed 42 --device cuda:G --log-interval 10 --tag "rppo_lookalike_hf_l05_w12_t16quad_s42" --wandb-name "rppo_lookalike_hf_l05_w12_t16quad_s42" --wandb-group "lookalike_half_factorial" --wandb-job-type "pilot"
# [N:G] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/lookalike_hf_w13_newABC_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml --episodes 10000000 --seed 42 --device cuda:G --log-interval 10 --tag "rppo_lookalike_hf_l05_w13_t1none_s42" --wandb-name "rppo_lookalike_hf_l05_w13_t1none_s42" --wandb-group "lookalike_half_factorial" --wandb-job-type "pilot"
# [N:G] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/lookalike_hf_w13_newABC_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml --episodes 10000000 --seed 42 --device cuda:G --log-interval 10 --tag "rppo_lookalike_hf_l05_w13_t16quad_s42" --wandb-name "rppo_lookalike_hf_l05_w13_t16quad_s42" --wandb-group "lookalike_half_factorial" --wandb-job-type "pilot"
# [N:G] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/lookalike_hf_w14_newABD_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml --episodes 10000000 --seed 42 --device cuda:G --log-interval 10 --tag "rppo_lookalike_hf_l05_w14_t1none_s42" --wandb-name "rppo_lookalike_hf_l05_w14_t1none_s42" --wandb-group "lookalike_half_factorial" --wandb-job-type "pilot"
# [N:G] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/lookalike_hf_w14_newABD_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml --episodes 10000000 --seed 42 --device cuda:G --log-interval 10 --tag "rppo_lookalike_hf_l05_w14_t16quad_s42" --wandb-name "rppo_lookalike_hf_l05_w14_t16quad_s42" --wandb-group "lookalike_half_factorial" --wandb-job-type "pilot"
# [N:G] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/lookalike_hf_w15_newACD_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml --episodes 10000000 --seed 42 --device cuda:G --log-interval 10 --tag "rppo_lookalike_hf_l05_w15_t1none_s42" --wandb-name "rppo_lookalike_hf_l05_w15_t1none_s42" --wandb-group "lookalike_half_factorial" --wandb-job-type "pilot"
# [N:G] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/lookalike_hf_w15_newACD_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml --episodes 10000000 --seed 42 --device cuda:G --log-interval 10 --tag "rppo_lookalike_hf_l05_w15_t16quad_s42" --wandb-name "rppo_lookalike_hf_l05_w15_t16quad_s42" --wandb-group "lookalike_half_factorial" --wandb-job-type "pilot"
# [N:G] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/lookalike_hf_w16_newBCD_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml --episodes 10000000 --seed 42 --device cuda:G --log-interval 10 --tag "rppo_lookalike_hf_l05_w16_t1none_s42" --wandb-name "rppo_lookalike_hf_l05_w16_t1none_s42" --wandb-group "lookalike_half_factorial" --wandb-job-type "pilot"
# [N:G] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/lookalike_hf_w16_newBCD_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml --episodes 10000000 --seed 42 --device cuda:G --log-interval 10 --tag "rppo_lookalike_hf_l05_w16_t16quad_s42" --wandb-name "rppo_lookalike_hf_l05_w16_t16quad_s42" --wandb-group "lookalike_half_factorial" --wandb-job-type "pilot"
```

### Seeds 43 and 44 queue (worlds 9–16, plus world 1 at seed 44)

34 runs, started in the order below by the `training-runner` as TF32 cards free (see "Run plan":
TF32 cards only, no node 112, node 114 one run at a time, a run never changes card type). WandB job
type `pilot`. The command line is the seed-42 line with `--seed`, `--device` and the tag changed.
World 1's two runs use `--config configs/environment/experiment/basic/lookalike_animals_close_pounce_small_food_10x10.yaml`
and `--wandb-group "lookalike_animals"`. Tag = WandB name.

| Order | Cell | Tag (= wandb-name) | wandb-group | Seed | Node:GPU (card) | Launched at | WandB run ID | Status |
|---|---|---|---|---|---|---|---|---|
| 1 | w1 ordinary | `rppo_lookalike_l05_t1none_s44` | `lookalike_animals` | 44 | `102:0 (4090)` | 2026-10-16T12:20:02 | `bs2ix9an` | running |
| 2 | w1 modulated | `rppo_lookalike_l05_t16quad_s44` | `lookalike_animals` | 44 | `102:1 (4090)` | 2026-10-16T12:20:03 | `ghpm7w64` | running |
| 3 | w9 ordinary | `rppo_lookalike_hf_l05_w9_t1none_s43` | `lookalike_half_factorial` | 43 | `114:1 (6000 Ada)` | 2026-10-16T12:33:26 | `ctf45k4c` | running |
| 4 | w9 modulated | `rppo_lookalike_hf_l05_w9_t16quad_s43` | `lookalike_half_factorial` | 43 | `109:1 (3090)` | 2026-10-16T16:29:00 | `uj6htcno` | running |
| 5 | w10 ordinary | `rppo_lookalike_hf_l05_w10_t1none_s43` | `lookalike_half_factorial` | 43 | `107:0 (3090)` | 2026-10-16T12:20:04 | `oc0ff4d4` | running |
| 6 | w10 modulated | `rppo_lookalike_hf_l05_w10_t16quad_s43` | `lookalike_half_factorial` | 43 | `108:1 (3090)` | 2026-10-16T12:20:05 | `ygoqx2z6` | running |
| 7 | w11 ordinary | `rppo_lookalike_hf_l05_w11_t1none_s43` | `lookalike_half_factorial` | 43 | `110:1 (3090)` | 2026-10-16T12:20:06 | `43h570oh` | running |
| 8 | w11 modulated | `rppo_lookalike_hf_l05_w11_t16quad_s43` | `lookalike_half_factorial` | 43 | `114:0 (6000 Ada)` | 2026-10-16T12:20:07 | `i7d18nnn` | running |
| 9 | w12 ordinary | `rppo_lookalike_hf_l05_w12_t1none_s43` | `lookalike_half_factorial` | 43 | `114:2 (6000 Ada)` | 2026-10-16T12:25:15 | `svv6te98` | running |
| 10 | w12 modulated | `rppo_lookalike_hf_l05_w12_t16quad_s43` | `lookalike_half_factorial` | 43 | `111:1 (3090)` | 2026-10-16T16:29:01 | `nje53gsr` | running |
| 11 | w13 ordinary | `rppo_lookalike_hf_l05_w13_t1none_s43` | `lookalike_half_factorial` | 43 | `114:3 (6000 Ada)` | 2026-10-16T16:29:03 | `hmtsexc7` | running |
| 12 | w13 modulated | `rppo_lookalike_hf_l05_w13_t16quad_s43` | `lookalike_half_factorial` | 43 | — | — | — | queued |
| 13 | w14 ordinary | `rppo_lookalike_hf_l05_w14_t1none_s43` | `lookalike_half_factorial` | 43 | — | — | — | queued |
| 14 | w14 modulated | `rppo_lookalike_hf_l05_w14_t16quad_s43` | `lookalike_half_factorial` | 43 | — | — | — | queued |
| 15 | w15 ordinary | `rppo_lookalike_hf_l05_w15_t1none_s43` | `lookalike_half_factorial` | 43 | — | — | — | queued |
| 16 | w15 modulated | `rppo_lookalike_hf_l05_w15_t16quad_s43` | `lookalike_half_factorial` | 43 | — | — | — | queued |
| 17 | w16 ordinary | `rppo_lookalike_hf_l05_w16_t1none_s43` | `lookalike_half_factorial` | 43 | — | — | — | queued |
| 18 | w16 modulated | `rppo_lookalike_hf_l05_w16_t16quad_s43` | `lookalike_half_factorial` | 43 | — | — | — | queued |
| 19 | w9 ordinary | `rppo_lookalike_hf_l05_w9_t1none_s44` | `lookalike_half_factorial` | 44 | — | — | — | queued |
| 20 | w9 modulated | `rppo_lookalike_hf_l05_w9_t16quad_s44` | `lookalike_half_factorial` | 44 | — | — | — | queued |
| 21 | w10 ordinary | `rppo_lookalike_hf_l05_w10_t1none_s44` | `lookalike_half_factorial` | 44 | — | — | — | queued |
| 22 | w10 modulated | `rppo_lookalike_hf_l05_w10_t16quad_s44` | `lookalike_half_factorial` | 44 | — | — | — | queued |
| 23 | w11 ordinary | `rppo_lookalike_hf_l05_w11_t1none_s44` | `lookalike_half_factorial` | 44 | — | — | — | queued |
| 24 | w11 modulated | `rppo_lookalike_hf_l05_w11_t16quad_s44` | `lookalike_half_factorial` | 44 | — | — | — | queued |
| 25 | w12 ordinary | `rppo_lookalike_hf_l05_w12_t1none_s44` | `lookalike_half_factorial` | 44 | — | — | — | queued |
| 26 | w12 modulated | `rppo_lookalike_hf_l05_w12_t16quad_s44` | `lookalike_half_factorial` | 44 | — | — | — | queued |
| 27 | w13 ordinary | `rppo_lookalike_hf_l05_w13_t1none_s44` | `lookalike_half_factorial` | 44 | — | — | — | queued |
| 28 | w13 modulated | `rppo_lookalike_hf_l05_w13_t16quad_s44` | `lookalike_half_factorial` | 44 | — | — | — | queued |
| 29 | w14 ordinary | `rppo_lookalike_hf_l05_w14_t1none_s44` | `lookalike_half_factorial` | 44 | — | — | — | queued |
| 30 | w14 modulated | `rppo_lookalike_hf_l05_w14_t16quad_s44` | `lookalike_half_factorial` | 44 | — | — | — | queued |
| 31 | w15 ordinary | `rppo_lookalike_hf_l05_w15_t1none_s44` | `lookalike_half_factorial` | 44 | — | — | — | queued |
| 32 | w15 modulated | `rppo_lookalike_hf_l05_w15_t16quad_s44` | `lookalike_half_factorial` | 44 | — | — | — | queued |
| 33 | w16 ordinary | `rppo_lookalike_hf_l05_w16_t1none_s44` | `lookalike_half_factorial` | 44 | — | — | — | queued |
| 34 | w16 modulated | `rppo_lookalike_hf_l05_w16_t16quad_s44` | `lookalike_half_factorial` | 44 | — | — | — | queued |

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

## Open question for later: food and bush placement in the test scenes (user, 2026-10-14)

To discuss before any further testing with food. In the with-food test scenes the food item sits at [2, 5]
(three cells above the agent's start [5, 5]), the bush at [5, 2], and the animal enters at [5, 9]. Where
the food and the bush sit relative to each other, and to the animal's entry, may change how much an agent
hides, and so the readout. Decide the placement (or several placements) with the user first.

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

## Feedback from plan-reviewer: complementary half, worlds 9–16 (2026-10-15)

**Verdict: SOUND WITH CONCERNS.** The worlds are built correctly and checked against what the
trainer actually saved; code and the conda environment have not changed since the first half. The
main risk is not time but **card type**. The claim that a batch difference lands only on the
four-group interaction needs every first-half run of a seed to share one condition and every
second-half run another. Card type breaks that. On an RTX 2080 Ti, JAX computes in full 32-bit
precision. On RTX 3090/4090/6000 Ada cards it uses the lower-precision TF32 format by default
(KNOWN_BUGS, "A trajectory store replays exactly only under the matmul precision mode it was
collected in"). The first half's seed-42 runs were all on TF32 cards. Of the cards usable today
(excluding 112, 113 and 114), 8 of 16 are 2080 Tis. Assigning them in world order will put an
uneven share of some groups' "+" worlds on 2080 Tis. Any precision effect then moves those main
effects, not only ABCD. Nobody has measured how large that effect is (§World 1 reuse, item 5,
assumes it is small).

| Sev. | Where | Issue | Suggested fix | Owner |
|---|---|---|---|---|
| Moderate | §Run plan "Cards" | Card class (full 32-bit on 2080 Ti vs TF32 elsewhere) is not balanced across groups within the half, so it can leak into main effects | Either (a) seed 42 on TF32 cards only, matching the first half's seed 42 (8 now, 8 later); or (b) pin the 2080 Ti set to worlds {9, 10, 15, 16}. Each group then has exactly 2 of its 4 "+" worlds on 2080 Tis, and card class is aliased only with the C×D / A×B pair. For seeds 43/44, rotate the pinned set to alias a different pair each seed. Never move a run across card class mid-training. Record the card per run segment | experiment-designer, then training-runner |
| Moderate | §Analysis item 2 | If world 1 seed 44 is declined, "all 16 worlds have 3 seeds" never happens, and the 4-degree-of-freedom borrowed σ is kept even though 2 seeds per world would give 16 degrees of freedom per agent | Switch to the pooled within-world σ once every world has 2 or more seeds, n = seeds in all 16 | experiment-designer |
| Moderate | §Analysis (whole) | No precedence rule if the first-half read and the full-factorial read disagree. The full-factorial rules were written after first-half seeds 42–44 had been tested and published (page v8–v11) | State which read decides, and list which first-half results had been seen when this section was written | experiment-designer |
| Moderate | §Run plan "Seeds 43 and 44 next" | The queue mechanism is not named. If the 10-13 `watch.py` is reused, it launches outside the training-runner (relative logs last time) | Name the mechanism; a watcher must carry the runner checklist (launch file, doc table, diary, absolute log path) | training-runner |
| Low | §Analysis item 4 | 6 two-group interactions + 4 main effects against a 2-SD bar: about 0.4 false crossings expected under no effect | Say so beside the interaction table; keep interactions descriptive unless the 6/8/10 M sign check also holds | experiment-designer |
| Low | §World 1 reuse item 4 | The launch-morning path list does not cover the world configs themselves (w2–w16) | Add `git diff bf48ba07 -- configs/environment/experiment/basic/lookalike_hf_*` must be empty | training-runner |

**Unverified assumptions:** the effect of TF32 vs full 32-bit on behaviour is small next to
seed-to-seed variation; it is also additive, not dependent on the world (the environment's vision
matmuls run in TF32 too, and group C changes what vision sees). Resumed runs (6 of the 14 seed-42
first-half runs; the single-config resume restores memory with fresh worlds, KNOWN_BUGS B5) behave
like uninterrupted ones. Node 107's NAS mount is live at launch.

**Cost of being wrong:** at worst, about 235 GPU-hours (seed 42) and then 470 more (seeds 43/44)
produce main effects with an unmeasured hardware offset that cannot be removed afterwards.
Balancing the cards before launch costs nothing.

Reviewed by: plan-reviewer

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
