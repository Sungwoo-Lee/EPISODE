---
title: "Level 05 body interactions: does the modulator's advantage grow when the right action depends on several body states at once?"
topic: level05_body_interactions
status: active
created: 2026-09-26
last_updated: 2026-09-26
wandb_tag: "rppo_l05body_*"
develop_link: docs/develop/active/thermal/STATE_DEPENDENT_BODY_MECHANICS.md
---

# Level 05 body interactions: a 2×2×2×2 world screen

## 1. Question

In the campfire world (curriculum level 05) the agent has to manage three body quantities: how
full it is, how injured it is, and how warm it is. A recent analysis found that both the
ordinary agent and the neuromodulated agent learned the same simple habit for injury: when hurt,
go to a bush and rest. Healing there is fast and free, so the habit is right whatever the
agent's hunger or temperature. A neuromodulator is a small side network that rescales the main
network according to what the body feels, so it should help most when the right action depends on
a **combination** of body states, for example "injured *and* starving: eat first, then hide".

This experiment adds four body rules, each switched on or off, and trains both agents in all 16
combinations. The four rules are:

- healing slows when the agent is hungry;
- healing uses up food energy;
- staying warm uses up food energy;
- food is scarcer.

It asks two things. Does the gap between the modulated and the ordinary agent in
state-dependent behaviour grow when these rules are on? And which rule, or which pair of rules,
makes it grow?

Before the 32 main runs, short calibration trainings of the ordinary agent choose how strong each
rule is. A simulation study with an ideal planner predicted that "healing slows when hungry"
matters most, "healing uses food" matters a little, "warmth uses food" does nothing, and scarcer
food works against the effect. Those predictions are registered here before any training runs.
There is one training run per agent per world, so this is a **screen**: it finds which rules
deserve a properly seeded follow-up, and it cannot confirm anything by itself.

**Status:** designed, configs written and loader-validated, nothing launched. The four
selected strengths are **provisional** until the stage-1 pilots run (§2.3).

---

## 2. Design

### 2.1 Research question (falsifiable form)

Consider level 05 with random start body temperature, and four on/off factors at
pilot-calibrated strengths:

- B5, healing slows when hungry;
- B3, healing costs food, with partial shortfall;
- A1, staying warm costs food;
- A4, scarcer food.

Does switching on B5 increase the modulated-minus-ordinary difference in state-dependent behaviour
(§4.1) by more than the factorial's own noise margin (Lenth's margin of error over the 15
factorial effects, §4.3)? And is B5's effect the largest of the four main effects? The design
uses 1 seed (42) and 10,000,000 training episodes per run.

### 2.2 Hypotheses and pre-registered predictions

The simulation study ([[STUDY_PLAN]], `docs/experiments/active/internal_state_interactions/`)
computed an ideal planner's **combination gain** for each rule in isolation. Combination gain is
how much knowing a second body variable improves the prediction of the best action, compared with
knowing only one. Its numbers are for a planner, not a trained network. We take them as the
predicted **direction and rank** of each factor's main effect on the agents' modulator advantage.
They are not predicted magnitudes.

| Factor | Simulation (planner combination gain vs today, points; pooled / map without a warm bush, 59 % of episodes) | Predicted main effect on the modulated-minus-ordinary difference |
|---|---|---|
| B5 healing slows when hungry | floor 0.2: **+3.3 / +5.2**; floor 0.0: +3.3 / +5.2; floor 0.5: +1.0 | **positive, largest of the four** |
| B3 healing costs food | cost 0.5 → 2.0: +0.5 → +1.1 pooled | positive but small; expected **not** to clear the noise margin |
| A1 staying warm costs food | rate 0.5 → 4: −0.1 → −1.4 | none (within noise) |
| A4 scarcer food | trip 4/6/8: −1.8 / −2.4 / −2.9; net per bite 3/2: −1.5 / −2.3 | **negative** |

- **Confirms (for this screen):** B5's main effect on the §4.1 primary measure is positive,
  exceeds Lenth's margin of error, and is the largest positive main effect.
- **Refutes:** B5's main effect is ≤ 0 or inside the margin. The same applies if another factor's
  positive effect exceeds B5's by more than the margin, since then the planner's ranking does not
  transfer to trained agents.
- **Shape predicted:** a B5-on world has a larger gap because the modulated agent's injury
  response becomes nutrition-dependent (it hides less, and eats first, when injured *and* hungry),
  while the ordinary agent keeps the fixed "hurt → hide" habit. The gap should appear in the
  late-training window and stay there, not flicker (§4.4).
- **Interactions:** the simulation varied one factor at a time, so there is **no directional
  prediction** for any pair. B5×B3 is the designed pair (as food runs low, slower healing also
  slows the food spent on healing; [[STATE_DEPENDENT_BODY_MECHANICS]] §A4b), so it is read first.
  Every pairwise effect is reported and labelled exploratory.
- **Survival:** each factor is predicted to lower both agents' survival steps. No directional
  prediction is made for the modulated-minus-ordinary survival difference. In the earlier
  level-05 runs, which started every episode at 0 degrees, it was 256 against 252 steps.

### 2.3 Stage 1: calibration pilots and the pick rule (fixed before any pilot runs)

**What runs.** 15 short trainings of the **ordinary agent only**, each 2,000,000 episodes:

- two runs of unchanged level 05 (seeds 42 and 43), which give the reference and a seed-noise
  estimate;
- three strengths each of B5, B3 and A1;
- two strengths of each A4 form.

The two A4 forms are fewer food items (the "trip" form, because the nearest food is farther
away) and less energy per bite (the "bite" form).

**Why 2,000,000 episodes.** The earlier level-05 ordinary run (Wave 2, WandB `z2u1orlf`) averaged
192 survival steps at 1.0 M episodes, **230 at 1.8 M** and 252 at 10 M. By 2 M it is past the
steep part of the curve (≈ 91 % of final), and that point took about 1 h 55 min on an RTX 3090.

**Strength grid**, chosen from the simulation sweep:

| Factor | Pilot strengths (weak → strong) | Why these |
|---|---|---|
| B5 hunger floor (ramp 20 → 100 nutrition, no over-full slowdown) | 0.5, 0.2, 0.0 | the simulation's three floors; 0.2 and 0.0 tie in the planner, 0.5 is a third as strong |
| B3 cost per injury point healed (`partial`) | 0.5, 1.0, 2.0 | the simulation's range minus its weakest 0.25 (its effect was +0.1 points). A full 100-point heal costs 50 / 100 / 200 of the 0–200 nutrition range |
| A1 coupling rate | 2, 4, **8** | the planner saw nothing up to 4, because it keeps itself warm. A trained agent spends more time cold (starts average −2.6 degrees), so the grid reaches one rung **beyond** the simulation. At −10 degrees the extra drain is 0.4 / 0.8 / 1.6 per step, against the 1.0 metabolic cost |
| A4 bite form: `food_nutrition_gain` | 6 → 4, 6 → 3 (net per bite 5 → 3, 2) | exactly the simulation's two bite values |
| A4 trip form: food items per episode | 1–4 → 1–2, → exactly 1 | measured nearest-food trip, 300 real resets: median **4 → 5 → 6** steps (mean 4.3 / 5.2 / 5.9). A 10×10 map cannot reach the simulation's 8 |

**Read-out.** Survival S is the mean of `Episode/Steps` over training episodes in the last 10 %
of the pilot (episodes 1.8 M–2.0 M), read from full-resolution WandB history. Starvation share is
`Episode/Term_Starvation` over the same window. Reward is not used anywhere.

- `S_base` is the mean S of the two unchanged-level-05 pilots.
- `n` is the absolute difference between those two pilots' S (seed noise).
- `starve_base` is their mean starvation share.

**Definitions:**

- A strength is **non-negligible** if `S_base − S ≥ max(2n, 0.05·S_base)`.
- A strength is **survivable** if `S ≥ 0.80·S_base` **and** its starvation share is at most
  `starve_base + 0.20`.

**Pick rule, per factor:** choose the **weakest** strength that is both non-negligible and
survivable. Weakest is chosen deliberately: three of the four factors drain food energy, and
stacking them is the main risk (§2.4). Edge cases:

- **No strength is non-negligible:** pick the strongest survivable one and flag "no measurable
  survival effect at the tested strengths". The user decides whether to add one stronger pilot.
- **Even the weakest strength is not survivable:** stop and report to the user. Nothing weaker
  than the grid is tried without the user's approval.
- **Survival does not fall steadily with strength:** report it. The rule still applies as written.

**A4 form choice (keep one).** Apply the pick rule to each form separately. Then:

- If exactly one form yields a non-negligible pick, keep that form.
- If both do, keep the **bite form**. It changes one number and leaves the map, the food count, and
  what the agent sees and smells unchanged. The trip form removes food items, which also changes
  the scent field and the vision field.
- If neither does, keep the bite form at gain 3 and flag it.

**Recording the pick.** The pick is written into `factors/selected_<factor>.yaml`, one line each
(§3.2), together with the pilot numbers. The pick is recorded in this doc's §6 before stage 2.

### 2.4 Stage 2: the stacking check (fixed before any pilot runs)

The selected strengths were each calibrated alone. B3, A1 and A4 all remove food energy, and B5
makes a hungry agent heal slower. Together they could make the all-four world a starvation
world, where every other behaviour is swamped.

- **p14** trains the all-four world, identical to factorial cell `w1111`, for 2 M episodes with
  the ordinary agent.
- **p15** runs at the same time. It is the all-four world with each of the three food-draining
  factors (B3, A1, A4) moved **one rung weaker** on its pilot grid; if a pick is already the
  weakest rung, it stays. B5 is unchanged because it spends no food. The designer writes p15's
  config at the stage-1 → 2 gate, because its rungs depend on the picks.
- **Collapse** means p14 has `S < 0.60·S_base`, **or** starvation share > 0.60, **or** starvation
  share > `starve_base + 0.35`.
- **Not collapsed:** the factorial launches at the selected strengths. p15 is recorded and not
  used.
- **Collapsed:** stop. The user decides between three options, with p14 and p15 in hand:
  - (a) run the factorial as selected, reading and reporting the collapsed cells as collapsed;
  - (b) run it with p15's weaker drainers, which then replace the selected strengths for every
    cell, so the factorial stays a clean 2⁴;
  - (c) something else.
- **Strengths are never weakened without that decision.** They are also never weakened for only
  some cells, because a factor at different strengths in different cells is no longer a factorial.

### 2.5 Stage 3: the factorial

There are 16 worlds, and each is one on/off combination of the four factors at its selected
strength. Two agents train in each, which gives 32 runs:

- the ordinary agent (`t1none`);
- the full modulator (`t16quad`: it writes to all four sites and reads every sensor).

These are the same agent configs as the Wave-2 level-05 runs in [[BASIC_LEVELS_Q2_DEFAULT]]. Each
run uses seed 42 and 10,000,000 episodes, with the same launch flags as Wave 2 (`--log-interval
10`). Cell `w0000` is unchanged level 05 **with** random start body temperature. It is a fresh
baseline: the Wave-2 level-05 runs started every episode at 0 degrees and are not like-for-like.

### 2.6 Controls (pinned)

- **World:** everything not under test comes from `basic/05-campfire_thermal_10x10.yaml` and its
  ladder:
  - random start body temperature on, [−10, +5];
  - random start nutrition [0, 200] and injury [0, 100];
  - pouncing predators, with bushes that block animals;
  - bush healing 5.0 per rest step, 0.2 in the open;
  - metabolic cost 1.0 per step;
  - 12 bites per food item;
  - 58-number observation.

  Validation (§3.3) confirmed that each world file differs from basic/05 **only** in its factor
  keys.
- **Agents:** `nmngaenorm_t1none.yaml` and `nmngaenorm_t16quad_ALL.yaml`. They are identical
  except `modulation.type`, both with γ = 0.95.
- **Training:** 10 M episodes, seed 42, default checkpoint cadence (every 200 k episodes, 50
  checkpoints).
- **Hardware:** the two agents of a world share a node and card model where possible, as in Wave
  2.
- **Reward** is untouched by every factor. B3/B5/A1 change body dynamics only, and A4 changes food
  yield or placement.

### 2.7 Observability caveat (from [[STATE_DEPENDENT_BODY_MECHANICS]] §A0)

At level 05 the agent never sees its true **injury**. It feels injury through *Interoceptive
Nociception*: a delayed, smoothed copy that peaks about 3 steps after the damage and fades over
about 12. **Nutrition** is seen through Satiation, which at level 05 is numerically equal to
nutrition. **Body temperature** is observed directly, in degrees.

B5 and B3 therefore couple a *hidden* quantity (injury, and how fast it heals) to a *seen* one
(nutrition). An agent can learn "hungry and hurting → eat first" only from the felt signal, and
healing progress is visible only as that signal fading. The modulator also reads the felt signal,
not true injury. Consequences for reading the results:

- Behaviour is analysed against **both** true injury and felt injury (§4.1).
- A null result is ambiguous between "the modulator does not help" and "the combination is not
  perceivable well enough to learn".

The observability flags are **not** switched on to remove this ambiguity. Hidden injury is a
project design decision, recorded in the LLM Wiki entry
`20260901_1528_interoceptive_channel_is_two_dims_by_design`.

### 2.8 Confounds and limitations

| Confound | Affects | Severity | Handling |
|---|---|---|---|
| 1 seed per cell: seed noise is indistinguishable from world-to-world residual | every effect | High | effects are judged against Lenth's margin from the higher-order interactions (§4.3), and against across-checkpoint spread; the result is a screen, not a verdict (§6 follow-up) |
| Pilots calibrate the **ordinary** agent only | strength choice | Medium | stated; the modulated agent's survival in each cell is reported, and any cell where it collapses and the ordinary agent did not is flagged |
| Strengths calibrated one factor at a time | combined cells | Medium | stage 2 stacking check with a pre-registered collapse rule (§2.4) |
| The trip form of A4 also changes the scent and vision landscape | A4 if the trip form is kept | Low–Medium | the bite form is preferred when both qualify (§2.3) |
| Hidden injury (§2.7) | B3, B5 | Medium | analyse against true and felt injury; state the ambiguity of a null |
| Survival changes the composition of the data (a world where agents die early has fewer late-episode, high-injury steps) | behaviour measures | Medium | measures are binned by body state and require a minimum count per bin (§4.1); bins below it are dropped and counted |
| The simulation's food-trip baseline counted ambush predators as food (§6) | the size of the A4 trip-form prediction, not its direction | Low | the trip form is calibrated from real resets here; reported to the simulation study's owner |

### 2.9 Where the configs live, and why

The variant configs live in `configs/environment/experiment/level05_body_interactions/`, a new
topic folder next to `basic/` and `behavior_probes/`, as the user decided ("we first test several
worlds and will select only important configs").

- **Not maintained.** Per CLAUDE.md, only `default.yaml` and `basic/` are maintained. Every file
  in this folder says in its header that it is experimental and not maintained. A schema change
  that breaks these files is **not** migrated. A world that proves important is promoted into
  `basic/` as a new, maintained file.
- **The placement is flagged for the user.** CLAUDE.md says everything else under
  `experiment/` "belongs in `archive/`". Putting this folder in `archive/` now would be wrong: it
  is live and must load for the next few weeks. After the study, the folder should be moved to
  `archive/`, or its winners promoted into `basic/`.
- **The existing test gate is unaffected.** `test_backward_compat_configs.py` loads every
  non-archived file here with the raw loader, which does not resolve `extends:`. It therefore skips
  them as "missing mandatory key", as it already does for every `basic/` world.

Layout (the one source of truth for strengths is the four `selected_*` files):

```
level05_body_interactions/
  factors/   13 strength fragments (one factor at one strength; NOT worlds on their own)
             selected_b5 / selected_b3 / selected_a1 / selected_a4  -> each extends ONE fragment
  pilots/    p01..p13 = basic/05 + one fragment;  p14 = basic/05 + all four selected_*
  worlds/    w0000..w1111 = basic/05 + the selected_* of each factor that is on
```

Worlds use the loader's list form of `extends:`, which merges the bases in order and then the
file itself. Fragments carry no `extends:`, so layering two of them cannot re-merge basic/05 over
an earlier layer. The factor keys are disjoint, except that B3 and B5 both write under `body:`
(dicts merge key by key). The A4 trip fragment restates the whole `resources:` list, because lists
replace wholesale. It keeps level 03's hiding-predator entry verbatim, and validation confirmed
the hiding predators are unchanged.

---

## 3. Launch Manifest

Group `level05_body_interactions` for every row. Job type `pilot` for stage 1–2 and `prod` for the
factorial. Tag = wandb-name, always. Node, GPU, launch time, WandB id and log path are filled in
by `training-runner`.

### 3.0 Stage 1 and 2 pilots (ordinary agent, 2,000,000 episodes)

| Run | Status | Cell | Tag (= wandb-name) | wandb-group | wandb-job-type | Seed | Node | GPU | Launched at | WandB run ID | Log path |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P0a | planned | unchanged level 05 | `rppo_l05body_p00_base_t1none_s42` | level05_body_interactions | pilot | 42 | — | — | — | — | — |
| P0b | planned | unchanged level 05 | `rppo_l05body_p00_base_t1none_s43` | level05_body_interactions | pilot | 43 | — | — | — | — | — |
| P01 | planned | B5 floor 0.5 | `rppo_l05body_p01_b5floor0p5_t1none_s42` | level05_body_interactions | pilot | 42 | — | — | — | — | — |
| P02 | planned | B5 floor 0.2 | `rppo_l05body_p02_b5floor0p2_t1none_s42` | level05_body_interactions | pilot | 42 | — | — | — | — | — |
| P03 | planned | B5 floor 0.0 | `rppo_l05body_p03_b5floor0p0_t1none_s42` | level05_body_interactions | pilot | 42 | — | — | — | — | — |
| P04 | planned | B3 cost 0.5 | `rppo_l05body_p04_b3cost0p5_t1none_s42` | level05_body_interactions | pilot | 42 | — | — | — | — | — |
| P05 | planned | B3 cost 1.0 | `rppo_l05body_p05_b3cost1p0_t1none_s42` | level05_body_interactions | pilot | 42 | — | — | — | — | — |
| P06 | planned | B3 cost 2.0 | `rppo_l05body_p06_b3cost2p0_t1none_s42` | level05_body_interactions | pilot | 42 | — | — | — | — | — |
| P07 | planned | A1 rate 2 | `rppo_l05body_p07_a1rate2_t1none_s42` | level05_body_interactions | pilot | 42 | — | — | — | — | — |
| P08 | planned | A1 rate 4 | `rppo_l05body_p08_a1rate4_t1none_s42` | level05_body_interactions | pilot | 42 | — | — | — | — | — |
| P09 | planned | A1 rate 8 | `rppo_l05body_p09_a1rate8_t1none_s42` | level05_body_interactions | pilot | 42 | — | — | — | — | — |
| P10 | planned | A4 bite, gain 4 | `rppo_l05body_p10_a4bitegain4_t1none_s42` | level05_body_interactions | pilot | 42 | — | — | — | — | — |
| P11 | planned | A4 bite, gain 3 | `rppo_l05body_p11_a4bitegain3_t1none_s42` | level05_body_interactions | pilot | 42 | — | — | — | — | — |
| P12 | planned | A4 trip, food 1–2 | `rppo_l05body_p12_a4tripfood1to2_t1none_s42` | level05_body_interactions | pilot | 42 | — | — | — | — | — |
| P13 | planned | A4 trip, food 1 | `rppo_l05body_p13_a4tripfood1to1_t1none_s42` | level05_body_interactions | pilot | 42 | — | — | — | — | — |
| P14 | planned (stage 2) | all four, selected | `rppo_l05body_p14_all4sel_t1none_s42` | level05_body_interactions | pilot | 42 | — | — | — | — | — |
| P15 | planned (stage 2; config written at the gate) | all four, drainers one rung weaker | `rppo_l05body_p15_all4weaker_t1none_s42` | level05_body_interactions | pilot | 42 | — | — | — | — | — |

### 3.0b Stage 3 factorial (10,000,000 episodes). Launch only after §2.3–2.4 are recorded in §6

Cell code = B5 B3 A1 A4 (1 = on). Agents: **o** = ordinary (`t1none`), **m** = modulated (`t16quad`).

| Run | Status | Cell | Tag (= wandb-name) | wandb-group | wandb-job-type | Seed | Node | GPU | Launched at | WandB run ID | Log path |
|---|---|---|---|---|---|---|---|---|---|---|---|
| F01 | planned | w0000 o | `rppo_l05body_w0000_t1none_s42` | level05_body_interactions | prod | 42 | — | — | — | — | — |
| F02 | planned | w0000 m | `rppo_l05body_w0000_t16quad_s42` | level05_body_interactions | prod | 42 | — | — | — | — | — |
| F03 | planned | w0001 o | `rppo_l05body_w0001_t1none_s42` | level05_body_interactions | prod | 42 | — | — | — | — | — |
| F04 | planned | w0001 m | `rppo_l05body_w0001_t16quad_s42` | level05_body_interactions | prod | 42 | — | — | — | — | — |
| F05 | planned | w0010 o | `rppo_l05body_w0010_t1none_s42` | level05_body_interactions | prod | 42 | — | — | — | — | — |
| F06 | planned | w0010 m | `rppo_l05body_w0010_t16quad_s42` | level05_body_interactions | prod | 42 | — | — | — | — | — |
| F07 | planned | w0011 o | `rppo_l05body_w0011_t1none_s42` | level05_body_interactions | prod | 42 | — | — | — | — | — |
| F08 | planned | w0011 m | `rppo_l05body_w0011_t16quad_s42` | level05_body_interactions | prod | 42 | — | — | — | — | — |
| F09 | planned | w0100 o | `rppo_l05body_w0100_t1none_s42` | level05_body_interactions | prod | 42 | — | — | — | — | — |
| F10 | planned | w0100 m | `rppo_l05body_w0100_t16quad_s42` | level05_body_interactions | prod | 42 | — | — | — | — | — |
| F11 | planned | w0101 o | `rppo_l05body_w0101_t1none_s42` | level05_body_interactions | prod | 42 | — | — | — | — | — |
| F12 | planned | w0101 m | `rppo_l05body_w0101_t16quad_s42` | level05_body_interactions | prod | 42 | — | — | — | — | — |
| F13 | planned | w0110 o | `rppo_l05body_w0110_t1none_s42` | level05_body_interactions | prod | 42 | — | — | — | — | — |
| F14 | planned | w0110 m | `rppo_l05body_w0110_t16quad_s42` | level05_body_interactions | prod | 42 | — | — | — | — | — |
| F15 | planned | w0111 o | `rppo_l05body_w0111_t1none_s42` | level05_body_interactions | prod | 42 | — | — | — | — | — |
| F16 | planned | w0111 m | `rppo_l05body_w0111_t16quad_s42` | level05_body_interactions | prod | 42 | — | — | — | — | — |
| F17 | planned | w1000 o | `rppo_l05body_w1000_t1none_s42` | level05_body_interactions | prod | 42 | — | — | — | — | — |
| F18 | planned | w1000 m | `rppo_l05body_w1000_t16quad_s42` | level05_body_interactions | prod | 42 | — | — | — | — | — |
| F19 | planned | w1001 o | `rppo_l05body_w1001_t1none_s42` | level05_body_interactions | prod | 42 | — | — | — | — | — |
| F20 | planned | w1001 m | `rppo_l05body_w1001_t16quad_s42` | level05_body_interactions | prod | 42 | — | — | — | — | — |
| F21 | planned | w1010 o | `rppo_l05body_w1010_t1none_s42` | level05_body_interactions | prod | 42 | — | — | — | — | — |
| F22 | planned | w1010 m | `rppo_l05body_w1010_t16quad_s42` | level05_body_interactions | prod | 42 | — | — | — | — | — |
| F23 | planned | w1011 o | `rppo_l05body_w1011_t1none_s42` | level05_body_interactions | prod | 42 | — | — | — | — | — |
| F24 | planned | w1011 m | `rppo_l05body_w1011_t16quad_s42` | level05_body_interactions | prod | 42 | — | — | — | — | — |
| F25 | planned | w1100 o | `rppo_l05body_w1100_t1none_s42` | level05_body_interactions | prod | 42 | — | — | — | — | — |
| F26 | planned | w1100 m | `rppo_l05body_w1100_t16quad_s42` | level05_body_interactions | prod | 42 | — | — | — | — | — |
| F27 | planned | w1101 o | `rppo_l05body_w1101_t1none_s42` | level05_body_interactions | prod | 42 | — | — | — | — | — |
| F28 | planned | w1101 m | `rppo_l05body_w1101_t16quad_s42` | level05_body_interactions | prod | 42 | — | — | — | — | — |
| F29 | planned | w1110 o | `rppo_l05body_w1110_t1none_s42` | level05_body_interactions | prod | 42 | — | — | — | — | — |
| F30 | planned | w1110 m | `rppo_l05body_w1110_t16quad_s42` | level05_body_interactions | prod | 42 | — | — | — | — | — |
| F31 | planned | w1111 o | `rppo_l05body_w1111_t1none_s42` | level05_body_interactions | prod | 42 | — | — | — | — | — |
| F32 | planned | w1111 m | `rppo_l05body_w1111_t16quad_s42` | level05_body_interactions | prod | 42 | — | — | — | — | — |

All 50 tags are unique. None collides with an existing `results/JAX_RecurrentPPO/` directory,
since the prefix `rppo_l05body_` is new.

### 3.1 Configs to Produce

Folder prefix `configs/environment/experiment/level05_body_interactions/`. The agent-config
prefix is `configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/`.

| Run | Config (env) | Config (agent) |
|---|---|---|
| P0a, P0b | `configs/environment/experiment/basic/05-campfire_thermal_10x10.yaml` (unchanged) | `nmngaenorm_t1none.yaml` |
| P01–P13 | `pilots/p01_b5_floor0p5.yaml` … `pilots/p13_a4trip_food1to1.yaml` (one per row, same number) | `nmngaenorm_t1none.yaml` |
| P14 | `pilots/p14_all4_selected.yaml` | `nmngaenorm_t1none.yaml` |
| P15 | `pilots/p15_all4_weaker.yaml`: **written at the stage-1 → 2 gate** | `nmngaenorm_t1none.yaml` |
| F(odd) | `worlds/w<code>.yaml` | `nmngaenorm_t1none.yaml` |
| F(even) | `worlds/w<code>.yaml` | `nmngaenorm_t16quad_ALL.yaml` |

Strength fragments (not worlds on their own):

- `factors/b5_hunger_slows_healing__floor{0p5,0p2,0p0}.yaml`
- `factors/b3_healing_costs_food__cost{0p5,1p0,2p0}.yaml` (each states `healing_nutrition_shortfall: partial`)
- `factors/a1_warmth_costs_food__rate{2,4,8}.yaml`
- `factors/a4_scarcer_food_bite__gain{4,3}.yaml`
- `factors/a4_scarcer_food_trip__food1to{2,1}.yaml`

The selectors are `factors/selected_{b5,b3,a1,a4}.yaml`. They are **PROVISIONAL** and currently
point at B5 floor 0.2, B3 cost 1.0, A1 rate 4, and A4 bite gain 4.

**Launch command** (for `training-runner`, one per row, via `run_command.py`; node and GPU are
chosen at launch time):

```
/home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
  --config <env config> --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/<agent>.yaml \
  --episodes <2000000 for P-rows | 10000000 for F-rows> --device cuda:<gpu> --log-interval 10 \
  --tag "<tag>" --wandb-name "<tag>" \
  --wandb-group "level05_body_interactions" --wandb-job-type "<pilot|prod>"
```

Only P0b adds `--seed 43`. Every other row uses the config-owned seed 42 and does not pass
`--seed`, which is the Wave-2 convention.

**Pre-flight discriminators for the runner:**

- every banner prints observation width **58**;
- `t16quad` banners print `Neuromodulation: ENABLED (… sites=[encoder,rnn,actor,critic] …)`, and
  `t1none` banners print `DISABLED`;
- the run's saved `models/config.yaml` shows the cell's factor keys, which is the ground truth. For
  example, `w0100` must show `body.healing_nutrition_cost: 1.0` and
  `healing_nutrition_shortfall: partial`, and `w0000` must show cost 0.0 and dependence false;
- for factorial rows, the four `selected_*.yaml` headers no longer say PROVISIONAL.

**Compute.** Stage 1 is 15 × ~2 h GPU (ordinary agent, 3090-class), and fits in one wave on the 30
free GPUs. Stage 2 is 2 × ~2 h. Stage 3 is 16 × ~14 h (ordinary) + 16 × ~18 h (modulated) ≈ 510
GPU-hours. The ~14 h and ~18 h are Wave-2 level-05 wall-clock on a 3090; harder worlds end
episodes sooner and run faster per episode. On 30 GPUs that is about one day, with two runs
queued or doubled up.

### 3.2 Validation performed (2026-09-26, the live loader, the project interpreter)

Every pilot and world file was resolved through `load_env_config` → `load_env_params`, built, reset
and stepped 5 times on CPU. Its resolved `EnvParams` was then diffed field by field against
basic/05:

- **Pilots:** p01–p03 differ only in `healing_nutrition_dependence` / `healing_hunger_low` /
  `healing_hunger_floor`. p03's floor 0.0 equals the inert default, so it does not show in the
  diff. p04–p06 differ only in `healing_nutrition_cost`, with shortfall `partial` present in the
  raw YAML. p07–p09 differ only in the two coupling keys, and p10–p11 only in
  `food_nutrition_gain`. p12–p13 differ only in the food slots; the hiding-predator arrays are
  unchanged.
- **Factorial worlds:** the diff of every `wXXXX` equals the union of its on-factors' keys, and
  `w0000` has an **empty** diff.
- **Random start body temperature** is on, [−10, +5], in all of them.

The validator script is in the session scratchpad and not committed; the diff listing is
summarised here.

---

## 4. Analysis plan (pre-specified)

### 4.1 Measures (per run, then modulated minus ordinary per world = `D_w`)

The training-world recordings are collected at the **final** checkpoint and at the four
checkpoints before it, with the existing trajectory collector, as for Wave 2
(`results/trajectories_basicq2_w2`, `_late`). Body temperature per step is read from the recorded
observation (`obs_true`, which carries body temperature in degrees at level 05); no new store
column is needed. Bins with fewer than 200 steps are dropped and counted.

1. **Primary — nutrition-dependence of injury-driven hiding.** Compute the share of steps spent
   in a bush against true injury (bins of 10), separately for low (< 60) and adequate (≥ 100)
   nutrition. The measure is the injury slope when fed minus the injury slope when hungry. A
   "hurt → hide regardless" habit scores ≈ 0. An agent that eats first when hurt and hungry scores
   > 0. Repeat against **felt** injury as a check (§2.7).
2. **Primary — survival steps.** Mean `Episode/Steps` over the last 10 % of training, plus the
   termination shares (injury, starvation, thermal, over-eating, time limit).
3. **Secondary — injury-dependence of feeding.** Compute the eating rate against injury, by
   nutrition band, as the same slope contrast as measure 1.
4. **Secondary — behavioural combination gain.** This is the simulation's own measure, applied to
   the agent. Label each step with the agent's activity (in cover, warming on a fire ring, eating,
   in the open). Then find the best single-variable predictor of that activity, and the best
   two-variable predictor, using nutrition, injury and body temperature, each in 10 bins. The
   gain is pair accuracy minus single accuracy. This measure ties the result back to the
   simulation's predictions.
5. **Context — scene battery.** The injury-level scene battery of [[INJURY_DEPENDENCE_PLAN]]
   (starting injury 0…90, the thermal versions) is run on the final checkpoints if the user wants
   it. It is secondary, and it is not needed for the verdict.

### 4.2 Pre-registered primary statistic

For each measure there are 16 values of `D_w`. The analysis computes the full 2⁴ effect set on
`D_w`:

- 4 main effects. Each is the mean of the 8 on-cells minus the mean of the 8 off-cells.
- 6 two-way interactions, 4 three-way interactions and 1 four-way interaction, each as the
  standard ± contrast.

The same is done for each agent's own measure, which shows whether an effect on `D_w` comes from
the modulated agent changing or from the ordinary agent changing.

### 4.3 How noise is judged (honest about 1 seed)

With one run per cell there is no replicate, so run-to-run (seed) noise cannot be separated from
genuine world differences. Two noise yardsticks are used, and both are reported:

1. **Lenth's pseudo standard error (PSE)** over the 15 effects. This is the standard method for an
   unreplicated two-level factorial: it treats the bulk of small effects as noise. An effect is
   **noted** when |effect| > t(0.975, 5) × PSE ≈ 2.57 × PSE. It is **not** called significant.
2. **Across-checkpoint spread.** This is the standard deviation of `D_w` over the newest 5
   checkpoints. It follows the reading rule of [[INJURY_DEPENDENCE_PLAN]]: a per-world gap is
   stated only when it exceeds both agents' across-checkpoint spread.

Seed noise itself is **not** measured by either yardstick, so every noted effect is a candidate
for the follow-up, not a finding.

### 4.4 Temporal evolution

Measure 1 and survival are computed at every checkpoint (50 per run) on a 50k-episode
recording subset. This gives:

- the time course of `D_w` per world;
- the checkpoint at which it first exceeds its late-window spread;
- whether a noted effect is present over the last 20 checkpoints, rather than only at the final one.

An effect present only at the final checkpoint is reported as unstable.

### 4.5 Follow-up this screen feeds (named now)

Take the noted factors plus `w0000`: at most 4 cells, for example the 2×2 of B5 × the
strongest other factor. Train them with **5 seeds** per agent, at 10 M episodes, which is
≤ 40 runs. That replicated 2×2 is the experiment that can confirm. This screen only decides which
2×2 it is.

---

## 5. Failure-mode catalog (decided in advance)

| Outcome | Reading |
|---|---|
| A pilot NaNs or diverges | a bad run, not evidence about the strength; rerun once with seed 43; if it repeats, the strength is treated as not survivable |
| All three strengths of a factor are negligible | "no measurable survival effect"; pick the strongest survivable (§2.3) and flag; the user may add one stronger pilot |
| All-four world collapses | stop; the user chooses (a)/(b)/(c) of §2.4; nothing weakened silently |
| A factorial cell collapses for one agent only (survival < 0.60 × `w0000` of that agent) | that cell's `D_w` is reported and marked; effects are computed with and without it; a factor whose effect depends on that cell is reported as fragile |
| The modulated run NaNs (critic explosion, modulator saturation) | the run failed, not the architecture: one rerun; if it fails twice the cell is marked "modulator unstable in this world", which is itself reported per factor |
| `D_w` on survival is large but the behaviour measures show nothing | a performance effect without a state-dependence mechanism; reported as such, and does not confirm §2.2 |
| All effects fall inside Lenth's margin | a null screen at 1 seed; the simulation's ranking did not transfer detectably. The follow-up is then **not** automatic, and the PI is consulted |
| B5's effect exists only against felt injury, or only against true injury | reported separately; felt-only is the more interesting, because the modulator reads felt injury |

---

## 6. Records (filled at the gates)

### 6.1 Stage-1 pick record

*(empty; filled from the pilots under §2.3, before stage 2)*

### 6.2 Stage-2 stacking record

*(empty)*

### 6.3 Note for the simulation study's owner

`scripts/analysis/studies/internal_state_interactions/measure_world.py` computes the "trip to
food" from `st.res_pos[st.res_active]`, which includes the **hiding-predator** resource slots
(resource type 1) as well as food (type 0). With the filter to food only, on 300 real level-05
resets, the median nearest-food trip is **4 steps** (mean 4.3), not the 2 the study used.

The consequences:

- The study's "trip 4" world is roughly today's real world.
- Its baseline makes eating look closer and cheaper than it is.
- That is the direction that could make every food-related prediction (A4, and B3 through the
  cost of re-eating) look milder than it is.

This design does not depend on the number; the A4 trip form is calibrated from real resets.
The owner of [[STUDY_PLAN]] should re-check it. This doc does not edit that study.

---

## Metrics Requested

None blocking. Every measure in §4 is computable from existing WandB keys (`Episode/Steps`,
`Episode/Term_*`) and existing trajectory-store columns (`nutrition`, `injury_level`,
`agent_in_bush`, `ate_food`, `rested`, `obs_true`). The separate trajectory-store body-temperature
column ([[STATE_DEPENDENT_BODY_MECHANICS]] "Still open" item 2) would make measure 4 simpler but
is not required.

| Metric | Why now | Where it'd live | Cost |
|---|---|---|---|
| Per-episode mean nutrition spent on healing (B3) and mean healing factor (B5) | would show directly how much each mechanic *engaged* per cell, rather than inferring it from injury / nutrition deltas | `src/environment/core.py::update_body` info → trainer episode logger | cheap (scalar per step) |

---

## Links

- Implementation of the four mechanics: [[STATE_DEPENDENT_BODY_MECHANICS]]
  (`docs/develop/active/thermal/STATE_DEPENDENT_BODY_MECHANICS.md`)
- Simulation study and sweep: [[STUDY_PLAN]]
  (`docs/experiments/active/internal_state_interactions/`); numbers from
  `results/analysis/internal_state_interactions/reading_rule.json` and `sweep/*.json`
- Agents and prior level-05 runs: [[BASIC_LEVELS_Q2_DEFAULT]]; runs
  `results/JAX_RecurrentPPO/20260922-182534_rppo_bq2cover_lvl05_t1none_s42` and
  `20260922-182538_rppo_bq2cover_lvl05_t16quad_s42` (WandB `z2u1orlf`, `ihq3tt7f`)
- Injury-dependence measures and reading rule: [[INJURY_DEPENDENCE_PLAN]]
- Registry entry: `docs/environment/CONFIG_CRITICAL_SETTINGS.md`, change log 2026-09-26
