---
title: "Level 05 body interactions: does the modulator's advantage grow when the right action depends on several body states at once?"
topic: level05_body_interactions
status: active
created: 2026-09-26
last_updated: 2026-09-27
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
- being away from the comfortable body temperature (0 degrees), whether too cold or too warm,
  uses up food energy;
- food is scarcer.

It asks two things. Does the gap between the modulated and the ordinary agent in
state-dependent behaviour grow when these rules are on? And which rule, or which pair of rules,
makes it grow?

Before the 32 main runs, short calibration trainings of the ordinary agent choose how strong each
rule is. A simulation study with an ideal planner was meant to say in advance which rule matters
most. Its first version put "healing slows when hungry" on top, but that version placed food about
2 steps from the agent when the real distance is about 4. Re-run with the correct distance, the
simulation **no longer singles out any rule**: "healing uses food" now edges ahead, "healing slows
when hungry" shrinks to a small effect, and no rule's effect on the most common map is larger than
the simulation's own noise band (§2.2, Revision 2). So the factorial is registered as a **screen
with no favourite**: it asks which rules, if any, widen the gap, and it expects the two healing
rules to be the likelier candidates. There is one training run per agent per world, so it finds
which rules deserve a properly seeded follow-up and cannot confirm anything by itself.

**Status:** designed, configs written and loader-validated, nothing launched. The four
selected strengths are **provisional** until the stage-1 pilots run (§2.3). Revised after plan
review (Revision 1) and after the corrected simulation (Revision 2, §1.3). The user's five
pre-pilot decisions, plus two related ones, were made on 2026-09-26 (§1.2).

### 1.1 Revision 1 (2026-09-26): changes after plan review and config review

Resolves the plan-reviewer's findings (appended at the end of this doc) and the
env-config-reviewer's notes (verdict GO WITH NOTES).

| Finding | Change |
|---|---|
| M1 pick thresholds can cross | Third unchanged-level-05 pilot **P0c** (seed 44) added, and the "non-negligible" threshold is **capped at 15 % of baseline survival**, so a band of strengths that is both non-negligible and survivable always exists (§2.3). |
| M2 simulation facts not disclosed | §2.2 now states that every B5 world failed the simulation study's own 5-point pass rule and that B5's gain falls **below** baseline at discount 0.99. It also carries a placeholder row for the re-run with the corrected food distance. §2.8 and §6.3 now agree: the food-distance error touches **every** prediction's baseline, not only A4's trip form. |
| M3 weakest vs strongest pick for B5 | Left to the user at Revision 1; **decided 2026-09-26** as recommended (§1.2, D1). |
| M4 multiple effects vs one margin | Lenth's simultaneous margin (SME ≈ 5.22 × PSE) is reported beside the individual margin (ME ≈ 2.57 × PSE). Exploratory effects are "noted" only above SME. Two effects are compared against √2 × ME (§4.3; the refutation clause in §2.2). |
| M5 slope over varying injury ranges; no tooling | Measure 1 (and 3) is now a **fixed contrast** over pre-registered injury ranges with a "not computable" rule. Temperature for measure 4 comes from `obs_true` in raw degrees. The four new analysis scripts, their dependency-map rows and their owner (`developer`) are named (§4.1, §4.6). |
| M6 recording volume uncosted | Episode counts, precision, cadence and a terabyte estimate are fixed in §4.5. §4.4 cadence is set to every fifth checkpoint. |
| M7 base-world drift over weeks | Each launch records the git state of the basic/05 → 04 → 03 → default ladder. After the last launch, all 32 saved configs are diffed pairwise (§2.6, §3.1 launch checklist). The pending bush-fire clearance key is named as an expected, inert difference. |
| L1 WandB window means | The read-out is an `Episode/_window_n`-weighted mean over rows selected by `Episode/Number` (§2.3). |
| L2 A1 is symmetric | A1's wording is changed to "being away from 0 degrees costs food" wherever the direction matters (§1, §2.1, §2.3, measure 4). |
| L3 scene battery regime mismatch | Measure 5 is marked **invalid on factor-on cells** until the body-state probe grid plan lands (§4.1). |
| L4 folder placement | Left to the user at Revision 1; **approved 2026-09-26** (§1.2, D2). |
| env-config-reviewer: PROVISIONAL guard | `grep -l PROVISIONAL` over the four selector files is a **blocking** launch-checklist step for P14 and every factorial row (§3.1). |
| env-config-reviewer N2 | The pre-flight names `healing_nutrition_cost` as the B3 discriminator. `healing_nutrition_shortfall: partial` is already the default in every cell and so tells nothing (§3.1). |

### 1.2 Decisions made by the user (2026-09-26, before any pilot launched)

All were taken as recommended. No decision is open before the pilots.

| # | Question | Decision | Where it acts |
|---|---|---|---|
| D1 | Which strength each factor gets (M3) | **"Healing slows when hungry" (B5) takes the strongest survivable strength**, because it drains no food and its weakest strength is the planner's weakest. **The three food-draining rules (B3 healing costs food, A1 being away from 0 degrees costs food, A4 scarcer food) take the weakest noticeable strength**, to keep the all-four world from starving. | §2.3 pick rule |
| D2 | Folder placement next to `basic/` (L4) | **Approved.** After the study the folder moves to `archive/`, and the worlds that matter are promoted into `basic/` as new maintained files. | §2.9 |
| D3 | Rate 8 for "being away from 0 degrees costs food" | **Kept** in the pilot grid, one rung beyond the simulation's rate 4. | §2.3 grid |
| D4 | Pilot count | **16 stage-1 + 2 stage-2 pilots** (18 in all, ≈ 36 GPU-hours), including the third base seed P0c and the weaker-drainer stacking pilot P15. | §2.3, §2.4, §3.0 |
| D5 | Hidden injury | **Accepted** for this screen. Injury observability stays off; every behaviour measure is analysed against **both** true injury and felt injury, and a null on the healing rules is reported as ambiguous. | §2.7, §4.1 |
| D6 | Bush-fire clearance ([[BUSH_FIRE_CLEARANCE]]) | Built with **2 cells of clearance (key value 3), around burning fires only**. During this experiment the key stays at its **inert default** in every pilot and world, so placement is unchanged; the M7 rule in §2.6 applies (inert value recorded, not a confound; any active value is a confound). | §2.6 |
| D7 | Probe scenes (measure 5) | **A grid of 480 conditions per run, including a food scene, at the final checkpoint only.** The grid is written as a **combination spec** (factors × levels), not as one config file per condition. | §4.1 measure 5 |

### 1.3 Revision 2 (2026-09-26): re-registration after the corrected simulation

The Revision 1 registration carried a placeholder row for a re-run of the simulation with the
correct food distance, and a trigger: if that re-run reversed a sign or B5's rank, the predictions
would be revised **before** the pilots. The re-run (commit `e2991ceb`) fired the trigger. B5 is no
longer first (B3 overtakes it), B5's effect on the common map vanishes (+5.2 → +0.1), and no
single change clears the common-map noise band. §2.2 now carries the Revision 2 predictions; the
Revision 1 predictions stay below them, marked superseded. §2.1, §4.3 and §5 are changed to match
the screen framing: no main effect is privileged, so every effect is judged against the
simultaneous margin. No pilot had launched when this revision was made.

---

## 2. Design

### 2.1 Research question (falsifiable form)

Consider level 05 with random start body temperature, and four on/off factors at
pilot-calibrated strengths:

- B5, healing slows when hungry;
- B3, healing costs food, with partial shortfall;
- A1, being away from 0 degrees costs food (in either direction: cold *and* warm bodies are
  taxed);
- A4, scarcer food.

**Revision 2 (screen form).** Which of the four factors, if any, changes the modulated-minus-ordinary
difference in state-dependent behaviour (§4.1) by more than the factorial's own simultaneous noise
margin (Lenth's SME over the 15 factorial effects, §4.3), and do the signs of the four main effects
match the corrected simulation's pattern (B3 and B5 non-negative, A1 null, A4 non-positive)? The
design uses 1 seed (42) and 10,000,000 training episodes per run.

*Superseded (Revision 1):* "Does switching on B5 increase the modulated-minus-ordinary difference
in state-dependent behaviour (§4.1) by more than the factorial's own noise margin (Lenth's margin
of error over the 15 factorial effects, §4.3)? And is B5's effect the largest of the four main
effects?"

### 2.2 Hypotheses and pre-registered predictions

The simulation study ([[STUDY_PLAN]], `docs/experiments/active/internal_state_interactions/`)
computed an ideal planner's **combination gain** for each rule in isolation. Combination gain is
how much knowing a second body variable improves the prediction of the best action, compared with
knowing only one. Its numbers are for a planner, not a trained network. We take them as the
predicted **direction and rank** of each factor's main effect on the agents' modulator advantage.
They are not predicted magnitudes.

#### 2.2.1 Revision 2 predictions (registered 2026-09-26, before any pilot) — current

Source: `results/analysis/internal_state_interactions/sweep_food4/*.json` (base food trip 4 steps,
the measured real value), compared with `sweep/*.json` (the Revision 1 source, base trip 2).
Baseline combination gain 11.9 points pooled; 17.1 on the map without a warm bush (the common map,
59 % of episodes) and 4.3 on the warm-bush map. The noise floor on the common map is 1.6, so the
study's "twice the noise floor" band is ±3.2. Numbers are points of change from that baseline,
pooled (common map / warm-bush map), discount 0.95 unless marked 0.99.

| Factor | Corrected simulation, trip 4 (was, trip 2) | Discount 0.99, trip 4 (was) | Predicted main effect on the modulated-minus-ordinary difference |
|---|---|---|---|
| B5 healing slows when hungry | floor 0.5: +0.1 (−0.9 / +1.6) (was +1.0); floor 0.2: **+1.6 (+0.1 / +3.9)** (was +3.3 (+5.2 / +0.7)); floor 0.0: +1.6 (+0.2 / +3.8) (was +3.3) | +3.2 / +1.8 / +1.4 (was −2.2 / −3.6 / −4.0) | **small positive or null.** Under the strongest-survivable rule (D1) the pick is likely floor 0.2 or 0.0, where the planner gains +1.6. The effect sits on the warm-bush map; on the common map it is nil |
| B3 healing costs food | cost 0.5: −0.3 (−2.9 / +3.4) (was +0.5); cost 1.0: **+3.1 (+2.9 / +3.4)** (was +0.7); cost 2.0: +3.2 (+1.1 / +6.2) (was +1.1) | +2.3 / +1.7 / −0.7 (was −0.8 / −3.0 / −5.1) | **positive if the pick is cost 1.0 or 2.0; null if it is cost 0.5.** The planner's response is not monotone: cost 0.5 is below baseline on the common map. The weakest-noticeable rule (D1) can land on 0.5, and the pick record (§6.1) states which case applies before stage 3 |
| A1 being away from 0 degrees costs food | rate 2: −0.2; rate 4: **−0.9 (−1.5 / −0.1)** (was −1.4); rate 8: not simulated | +1.3 / +1.0 (was −1.4 / −0.0) | **none (within noise).** The two discounts disagree in sign |
| A4 scarcer food | net per bite 3: **−0.8 (−0.4 / −1.5)** (was −1.5); net per bite 2: −1.0 (was −2.3); trip 6 / 8 / 10: −0.7 / −1.2 / −1.3 (pilot trip form measures 5–6 steps) | bite 3 / 2: −2.2 / −3.3; trip 6: −1.7 | **small negative, likely within noise** |

**What the corrected simulation says, plainly.** It no longer singles out a factor. The largest
pooled change among the four factors is B3 at +3.1 to +3.2; B5 is +1.6. No change to any of the
four clears the common-map band of ±3.2 (the nearest is B3 cost 1.0 at +2.9). None reaches the
study's own 5-point pass mark. Two things improved relative to Revision 1: B5's sign now agrees
between discounts 0.95 and 0.99, and B3 at cost 1.0 is positive under both. The prior for any
single factor remains weak, and the factorial is therefore read as a **screen**: which of the four,
if any, stands out in trained agents.

- **Screen outcome (primary):** each of the 15 effects on the §4.1 primary measure is reported with
  ME and SME (§4.3). An effect is **noted** as a follow-up candidate when it exceeds SME. No main
  effect has a privileged margin.
- **Sign pattern (secondary):** the simulation's direction for the four main effects is B3 ≥ 0,
  B5 ≥ 0, A1 ≈ 0, A4 ≤ 0. The pattern is **contradicted** if any main effect clears SME in the
  opposite direction to its prediction, or A1 clears SME in either direction. It is **consistent**
  otherwise; that includes an all-null screen, which is reported as uninformative about transfer,
  not as support.
- **Expected candidates:** the healing rules (B3, B5) and their pair B3×B5. A noted B3 or B5 effect
  is read as "consistent with the corrected planner", never "confirmed as predicted".

#### 2.2.2 Revision 1 predictions — superseded 2026-09-26 by §2.2.1

Kept for the record. These were registered from the simulation with food at trip 2 and were
superseded when the corrected re-run fired the revision trigger in the last row.

| Factor | Simulation (planner combination gain vs today, points; pooled / map without a warm bush, 59 % of episodes) | Predicted main effect on the modulated-minus-ordinary difference |
|---|---|---|
| B5 healing slows when hungry | floor 0.2: **+3.3 / +5.2**; floor 0.0: +3.3 / +5.2; floor 0.5: +1.0 | **positive, largest of the four** |
| B3 healing costs food | cost 0.5 → 2.0: +0.5 → +1.1 pooled | positive but small; expected **not** to clear the noise margin |
| A1 being away from 0 degrees costs food | rate 0.5 → 4: −0.1 → −1.4 | none (within noise) |
| A4 scarcer food | trip 4/6/8: −1.8 / −2.4 / −2.9; net per bite 3/2: −1.5 / −2.3 | **negative** |
| **Re-run with corrected food distance — done 2026-09-26** (base trip 4, `results/analysis/internal_state_interactions/sweep_food4/`; baseline combination gain 11.9 pooled, 17.1 / 4.3 on the no-warm-bush / warm-bush maps; noise floor on the common map 1.6, so its ±2× band is ±3.2) | Change in combination gain vs baseline, pooled (common map / warm-bush map), discount 0.95, at the provisional strengths — B5 floor 0.2: **+1.6** (+0.1 / +3.9), was +3.3 (+5.2 / +0.7) · B3 cost 1.0: **+3.1** (+2.9 / +3.4), was +0.7 · A1 rate 4: **−0.9** (−1.5 / −0.1), was −1.4 · A4 net food per bite 3: **−0.8** (−0.4 / −1.5), was −1.5. Discount 0.99: B5 +1.8, B3 +1.7, A1 +1.0, A4 −2.2. **The revision trigger fired:** B5 no longer ranks first (B3 overtakes it), and B5's effect on the common map vanishes; no single change clears the common-map noise band. | the predictions above stand unless this row reverses a sign or B5's rank; if it does, the registration is revised **before** the pilots and the revision is dated here. **Fired; revised 2026-09-26 as Revision 2 (§2.2.1)** |

**What the trip-2 simulation did not support (disclosed at Revision 1, M2; superseded).** Two facts from the same simulation
output (`reading_rule.json`) weaken the B5 prediction:

- **No B5 world passed the study's own pre-registered rule.** Rule 1 asks for a gain of at least
  5 points over baseline; B5's pooled gain is +3.3 at best, and all three B5 worlds are recorded as
  `passes: false`. Only one world in the whole sweep passed (A5, a bush 8 steps away).
- **At discount 0.99 the sign flips.** The study's robustness check (rule 4) re-plans with a
  longer horizon. There, B5's gain is **below** the baseline: 0.139 / 0.124 / 0.120 (floor
  0.5 / 0.2 / 0.0) against 0.160, i.e. −2.2 / −3.6 / −4.0 points.

The prediction is registered from the discount-0.95 result because 0.95 is the agents' own γ
(§2.6). The prior behind "B5 positive, largest" is therefore weak. A positive B5 result in this
screen is read as "consistent with the 0.95 planner", **not** as "confirmed as predicted", and the
0.99 disagreement is repeated wherever the result is reported.

- *(Superseded)* **Confirms (for this screen):** B5's main effect on the §4.1 primary measure is
  positive, exceeds Lenth's margin of error, and is the largest positive main effect.
- *(Superseded)* **Refutes:** B5's main effect is ≤ 0 or inside the margin (ME, §4.3). The same
  applies if another factor's positive effect exceeds B5's by more than **√2 × ME**, since then the
  planner's ranking does not transfer to trained agents. The √2 applies because the difference of
  two effects carries the noise of both.

#### 2.2.3 Shape, interactions and survival (unchanged; apply to Revision 2)

- **Shape predicted:** a world with a healing rule on (B5 or B3) has a larger gap because the
  modulated agent's injury response becomes nutrition-dependent (it hides less, and eats first,
  when injured *and* hungry), while the ordinary agent keeps the fixed "hurt → hide" habit. The gap
  should appear in the late-training window and stay there, not flicker (§4.4).
- **Interactions:** the simulation varied one factor at a time, so there is **no directional
  prediction** for any pair. B5×B3 is the designed pair (as food runs low, slower healing also
  slows the food spent on healing; [[STATE_DEPENDENT_BODY_MECHANICS]] §A4b), so it is read first.
  Every pairwise effect is reported and labelled exploratory.
- **Survival:** each factor is predicted to lower both agents' survival steps. No directional
  prediction is made for the modulated-minus-ordinary survival difference. In the earlier
  level-05 runs, which started every episode at 0 degrees, it was 256 against 252 steps.

### 2.3 Stage 1: calibration pilots and the pick rule (fixed before any pilot runs)

**What runs.** 16 short trainings of the **ordinary agent only**, each 2,000,000 episodes:

- three runs of unchanged level 05 (seeds 42, 43 and 44), which give the reference and a
  seed-noise estimate. The third seed (P0c) was added in Revision 1: one difference between two
  seeds is a very weak noise estimate, and the third costs about 2 GPU-hours;
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
| A1 coupling rate (charged for distance from 0 degrees in either direction) | 2, 4, **8** (rate 8 kept by the user, §1.2 D3) | the planner saw nothing up to 4, because it keeps itself warm. A trained agent spends more time cold (starts average −2.6 degrees), so the grid reaches one rung **beyond** the simulation. At −10 degrees (or +10) the extra drain is 0.4 / 0.8 / 1.6 per step, against the 1.0 metabolic cost; sitting on the +8.8-degree fire ring costs 0.35 / 0.7 / 1.4 |
| A4 bite form: `food_nutrition_gain` | 6 → 4, 6 → 3 (net per bite 5 → 3, 2) | exactly the simulation's two bite values |
| A4 trip form: food items per episode | 1–4 → 1–2, → exactly 1 | measured nearest-food trip, 300 real resets: median **4 → 5 → 6** steps (mean 4.3 / 5.2 / 5.9). A 10×10 map cannot reach the simulation's 8 |

**Read-out.** Survival S is the mean of `Episode/Steps` over training episodes in the last 10 %
of the pilot (episodes 1.8 M–2.0 M), read from full-resolution WandB history. Each WandB row is
itself a mean over a window of episodes whose size varies (`Episode/_window_n`, `train.py:1552`),
so S is the **`Episode/_window_n`-weighted** mean of the rows whose `Episode/Number` falls in
1.8 M–2.0 M, not a plain mean of rows. Starvation share is `Episode/Term_Starvation`, weighted and
selected the same way. Reward is not used anywhere.

- `S_base` is the mean S of the three unchanged-level-05 pilots (P0a, P0b, P0c).
- `n` is the sample standard deviation of those three S values (seed noise).
- `starve_base` is their mean starvation share.

**Definitions:**

- A strength is **non-negligible** if `S_base − S ≥ min(max(2n, 0.05·S_base), 0.15·S_base)`.
- A strength is **survivable** if `S ≥ 0.80·S_base` **and** its starvation share is at most
  `starve_base + 0.20`.

**Why the cap (M1).** Without it, the two thresholds can cross: if the seeds differ by more than
10 % of `S_base`, no strength can be both non-negligible and survivable. The rule would then
wrongly report "no measurable effect" and fall through to the *strongest* strength. With the
non-negligible threshold capped at 15 %, any strength with S between 0.80 and 0.85 of `S_base`
always qualifies (subject to the starvation check), so the band never closes. If the cap binds
(`2n > 0.15·S_base`), that fact is recorded in §6.1: it means seed noise at 2 M episodes is too
large for a survival-based pick to be sharp, and the pick is flagged as noise-limited. The cap and
the third seed were both adopted. The cap is the structural guarantee; the third seed makes `n`
less of a coin toss.

**Pick rule, per factor (user decision D1, 2026-09-26):**

- **B3, A1, A4 (the food-draining rules):** choose the **weakest noticeable** strength, i.e. the
  weakest that is both non-negligible and survivable. Weakest is chosen deliberately: these three
  drain food energy, and stacking them is the main risk (§2.4).
- **B5 (healing slows when hungry):** choose the **strongest survivable** strength. B5 drains no
  food, so the stacking argument does not apply, and its weakest strength (floor 0.5) is the one
  the planner rates lowest (§2.2.1). Whether that strength is also non-negligible is recorded in
  §6.1 but is not required.

*Superseded (Revision 1):* "choose the weakest strength that is both non-negligible and survivable"
for all four factors.

Edge cases:

- **No strength is non-negligible (B3, A1, A4):** pick the strongest survivable one and flag "no
  measurable survival effect at the tested strengths". The user decides whether to add one
  stronger pilot.
- **B3 lands on cost 0.5:** record in §6.1 that the corrected planner predicts no gain there
  (−0.3 pooled, −2.9 on the common map; §2.2.1), so a null B3 effect is then the expected outcome.
  The pick is not overridden.
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
- **Launch guard:** p14 is not launched while any `selected_*.yaml` still says PROVISIONAL
  (§3.1 checklist).
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
- **Base world held fixed over weeks (M7).** Every pilot and world resolves through
  `basic/05 → 04 → 03 → default.yaml`. Those files are maintained and edited by parallel sessions,
  and the study spans weeks. A default changed between launches would put cells on different base
  worlds, and a check on the factor keys alone would not see it. Two checks are pre-registered:
  1. **At each launch**, the runner records `git rev-parse HEAD` and
     `git log -1 --format=%H -- configs/environment/default.yaml configs/environment/experiment/basic/`
     in the manifest row's Log-path cell (or a sibling note).
  2. **After the last factorial launch**, all 32 saved `models/config.yaml` files are diffed
     pairwise. They must be identical outside the factor keys, and identical outside the factor
     keys to the P0a pilot's saved config. Any other difference is a registered confound, reported
     with the cells it splits.

  **One expected difference is named in advance.** The bush-fire clearance plan
  ([[BUSH_FIRE_CLEARANCE]], `docs/develop/active/thermal/BUSH_FIRE_CLEARANCE.md`) adds
  `thermal.bush_min_fire_distance: 0` to `default.yaml`. It may land mid-study. At its inert value 0
  it leaves placement unchanged, so if it appears in some saved configs and not others **at 0**, it
  is recorded but not a confound. Any non-zero value is a confound. The user decided (D6,
  2026-09-26) that the feature is built with 2 cells of clearance (value 3) around burning fires
  only, and stays at its inert default throughout this experiment, so a saved config showing 3 is
  a confound.
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
| Survival changes the composition of the data (a world where agents die early has fewer late-episode, high-injury steps) | behaviour measures | Medium | measures 1 and 3 use **fixed** injury ranges and nutrition bands that every run must cover with ≥ 200 steps, else the run is "not computable" (§4.1); measure 4 uses fixed bins, and bins below the count are dropped and counted |
| The simulation's food-trip baseline counted hiding predators as food (§6.3), so its base world had food about 2 steps away instead of about 4 | the **baseline of every simulated world**, so the size, and for the small effects possibly the sign, of all four §2.2 predictions; most plausibly it makes the food-draining rules (A4, B3) look milder than they are | Resolved for the registration | the A4 trip form is calibrated from real resets here; the simulation was re-run with base trip 4 (`sweep_food4/`) and the predictions re-registered from it before the pilots (Revision 2, §2.2.1). As expected, B3 grew; B5 also shrank, which was not foreseen |

### 2.9 Where the configs live, and why

The variant configs live in `configs/environment/experiment/level05_body_interactions/`, a new
topic folder next to `basic/` and `behavior_probes/`, as the user decided ("we first test several
worlds and will select only important configs").

- **Not maintained.** Per CLAUDE.md, only `default.yaml` and `basic/` are maintained. Every file
  in this folder says in its header that it is experimental and not maintained. A schema change
  that breaks these files is **not** migrated. A world that proves important is promoted into
  `basic/` as a new, maintained file.
- **The placement was approved by the user (D2, 2026-09-26).** CLAUDE.md says everything else
  under `experiment/` "belongs in `archive/`". Putting this folder in `archive/` now would be
  wrong: it is live and must load for the next few weeks. **After the study**, the folder moves to
  `archive/` and the worlds that matter are promoted into `basic/` as new, maintained files.
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
| P0a | running | unchanged level 05 | `rppo_l05body_p00_base_t1none_s42` | level05_body_interactions | pilot | 42 | 106 | cuda:0 | 2026-09-27T00:43:26 | `nz0o6b70` | `logs/20260927_004326.log` · HEAD `4209024d` · ladder `8187c570` |
| P0b | running | unchanged level 05 | `rppo_l05body_p00_base_t1none_s43` | level05_body_interactions | pilot | 43 | 106 | cuda:1 | 2026-09-27T00:43:31 | `p4tlq5fq` | `logs/20260927_004331.log` · HEAD `4209024d` · ladder `8187c570` |
| P0c | running | unchanged level 05 | `rppo_l05body_p00_base_t1none_s44` | level05_body_interactions | pilot | 44 | 107 | cuda:0 | 2026-09-27T00:43:36 | `qwrtf2x5` | `logs/20260927_004336.log` · HEAD `4209024d` · ladder `8187c570` |
| P01 | running | B5 floor 0.5 | `rppo_l05body_p01_b5floor0p5_t1none_s42` | level05_body_interactions | pilot | 42 | 107 | cuda:1 | 2026-09-27T00:43:41 | `a2mnxvdo` | `logs/20260927_004341.log` · HEAD `4209024d` · ladder `8187c570` |
| P02 | running | B5 floor 0.2 | `rppo_l05body_p02_b5floor0p2_t1none_s42` | level05_body_interactions | pilot | 42 | 108 | cuda:0 | 2026-09-27T00:43:46 | `g06iwqng` | `logs/20260927_004346.log` · HEAD `4209024d` · ladder `8187c570` |
| P03 | running | B5 floor 0.0 | `rppo_l05body_p03_b5floor0p0_t1none_s42` | level05_body_interactions | pilot | 42 | 108 | cuda:1 | 2026-09-27T00:43:52 | `l0m2u80f` | `logs/20260927_004352.log` · HEAD `4209024d` · ladder `8187c570` |
| P04 | running | B3 cost 0.5 | `rppo_l05body_p04_b3cost0p5_t1none_s42` | level05_body_interactions | pilot | 42 | 109 | cuda:0 | 2026-09-27T00:43:57 | `yqgfofeg` | `logs/20260927_004357.log` · HEAD `4209024d` · ladder `8187c570` |
| P05 | running | B3 cost 1.0 | `rppo_l05body_p05_b3cost1p0_t1none_s42` | level05_body_interactions | pilot | 42 | 109 | cuda:1 | 2026-09-27T00:44:02 | `zjsj372y` | `logs/20260927_004402.log` · HEAD `4209024d` · ladder `8187c570` |
| P06 | running | B3 cost 2.0 | `rppo_l05body_p06_b3cost2p0_t1none_s42` | level05_body_interactions | pilot | 42 | 110 | cuda:0 | 2026-09-27T00:44:07 | `o58en3za` | `logs/20260927_004407.log` · HEAD `4209024d` · ladder `8187c570` |
| P07 | running | A1 rate 2 | `rppo_l05body_p07_a1rate2_t1none_s42` | level05_body_interactions | pilot | 42 | 110 | cuda:1 | 2026-09-27T00:44:11 | `85eqet0o` | `logs/20260927_004411.log` · HEAD `4209024d` · ladder `8187c570` |
| P08 | running | A1 rate 4 | `rppo_l05body_p08_a1rate4_t1none_s42` | level05_body_interactions | pilot | 42 | 111 | cuda:0 | 2026-09-27T00:44:16 | `dqm4du57` | `logs/20260927_004416.log` · HEAD `4209024d` · ladder `8187c570` |
| P09 | running | A1 rate 8 | `rppo_l05body_p09_a1rate8_t1none_s42` | level05_body_interactions | pilot | 42 | 111 | cuda:1 | 2026-09-27T00:44:21 | `glqka8g7` | `logs/20260927_004421.log` · HEAD `4209024d` · ladder `8187c570` |
| P10 | running | A4 bite, gain 4 | `rppo_l05body_p10_a4bitegain4_t1none_s42` | level05_body_interactions | pilot | 42 | 112 | cuda:0 | 2026-09-27T00:44:26 | `z8ew4j46` | `logs/20260927_004426.log` · HEAD `4209024d` · ladder `8187c570` |
| P11 | running | A4 bite, gain 3 | `rppo_l05body_p11_a4bitegain3_t1none_s42` | level05_body_interactions | pilot | 42 | 112 | cuda:1 | 2026-09-27T00:44:32 | `sr9scxml` | `logs/20260927_004432.log` · HEAD `4209024d` · ladder `8187c570` |
| P12 | running (stuck at compile on 113 (node SSH-unreachable), relaunched on 101 at 01:16; 113 copy abandoned: WandB `c3wd9snn`, `logs/20260927_004436.log`) | A4 trip, food 1–2 | `rppo_l05body_p12_a4tripfood1to2_t1none_s42` | level05_body_interactions | pilot | 42 | 101 | cuda:0 | 2026-09-27T01:16:49 | `e8pc7ajl` | `logs/20260927_011649.log` · HEAD `4209024d` · ladder `8187c570` |
| P13 | running (stuck at compile on 113 (node SSH-unreachable), relaunched on 101 at 01:16; 113 copy abandoned: WandB `35f5vjgq`, `logs/20260927_004441.log`) | A4 trip, food 1 | `rppo_l05body_p13_a4tripfood1to1_t1none_s42` | level05_body_interactions | pilot | 42 | 101 | cuda:1 | 2026-09-27T01:16:55 | `nuy4mx32` | `logs/20260927_011655.log` · HEAD `4209024d` · ladder `8187c570` |
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

All 51 tags are unique. None collides with an existing `results/JAX_RecurrentPPO/` directory,
since the prefix `rppo_l05body_` is new.

### 3.1 Configs to Produce

Folder prefix `configs/environment/experiment/level05_body_interactions/`. The agent-config
prefix is `configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/`.

| Run | Config (env) | Config (agent) |
|---|---|---|
| P0a, P0b, P0c | `configs/environment/experiment/basic/05-campfire_thermal_10x10.yaml` (unchanged; P0c needs no new file, only `--seed 44`) | `nmngaenorm_t1none.yaml` |
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

Only P0b adds `--seed 43` and P0c adds `--seed 44`. Every other row uses the config-owned seed 42
and does not pass `--seed`, which is the Wave-2 convention.

**Launch checklist (blocking, in this order):**

1. **Provisional guard.** Before P14, P15 or any F-row:
   `grep -l PROVISIONAL configs/environment/experiment/level05_body_interactions/factors/selected_*.yaml`
   must print **nothing**. Any file printed means the pilot pick has not been written into it, and
   the launch stops. (Pilots P0a–P13 do not read the selectors and are exempt.)
2. **Ladder state (M7).** Record `git rev-parse HEAD` and
   `git log -1 --format=%H -- configs/environment/default.yaml configs/environment/experiment/basic/`
   for the row (§2.6).
3. The discriminators below, from each run's banner and saved config.

**Pre-flight discriminators for the runner:**

- every banner prints observation width **58**;
- `t16quad` banners print `Neuromodulation: ENABLED (… sites=[encoder,rnn,actor,critic] …)`, and
  `t1none` banners print `DISABLED`;
- the run's saved `models/config.yaml` shows the cell's factor keys, which is the ground truth. For
  example, `w0100` must show `body.healing_nutrition_cost` equal to the selected B3 cost (non-zero),
  and `w0000` must show cost 0.0 and `healing_nutrition_dependence: false`. The B3 discriminator is
  `healing_nutrition_cost`. `healing_nutrition_shortfall: partial` is the default in every cell
  (`default.yaml:221`), so its presence tells nothing;
- for factorial rows, the four `selected_*.yaml` headers no longer say PROVISIONAL.

**Compute.** Stage 1 is 16 × ~2 h GPU (ordinary agent, 3090-class), and fits in one wave on the 30
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

The training-world recordings are collected with the existing trajectory collector, as for Wave 2
(`results/trajectories_basicq2_w2`, `_late`); episode counts, precision and cadence are fixed in
§4.5. **Body temperature** per step is read from the recorded observation `obs_true`, whose "Body
Temperature" slot carries it in raw degrees at level 05 (`src/environment/sensor.py:488`). The
design does **not** depend on a trajectory-store body-temperature column; that column is deferred
to a separate job.

**Fixed ranges, registered now (M5).** An earlier draft fitted a slope over whatever injury bins
had enough data. That made the fitted range differ by cell and by agent, so slopes were not
comparable. Measures 1 and 3 now use one fixed contrast:

- nutrition bands: **hungry** = nutrition < 60, **fed** = nutrition ≥ 100;
- true-injury ranges: **low** = injury 0–20, **high** = injury 60–100 (`injury_level`);
- a run is **computable** at a checkpoint only if all four band × range cells hold ≥ 200 steps.
  If the final checkpoint alone falls short, the five late checkpoints are pooled for that run
  (and for its partner agent in the same world, so `D_w` compares like with like). If it still
  falls short, measure 1 is reported as **not computable** for that world, and the 2⁴ effects for
  that measure are not computed. The user is told, and any changed range is labelled post hoc.

1. **Primary — nutrition-dependence of injury-driven hiding.** Let `B(band, range)` be the share of
   steps spent in a bush (`agent_in_bush`). Then
   `M1 = [B(fed, high) − B(fed, low)] − [B(hungry, high) − B(hungry, low)]`.
   A "hurt → hide regardless" habit scores ≈ 0. An agent that eats first when hurt and hungry
   scores > 0. **Felt-injury check (§2.7):** the same contrast on felt injury, the Interoceptive
   Nociception slot of `obs_true`, with its low/high ranges set to the bottom and top fifth of felt
   injury in the `w0000` ordinary run's final-checkpoint recording. Those cut-points are frozen
   before any other run is read and applied to all 32.
2. **Primary — survival steps.** Mean `Episode/Steps` over the last 10 % of training
   (`Episode/_window_n`-weighted, rows selected by `Episode/Number`, as in §2.3), plus the
   termination shares (injury, starvation, thermal, over-eating, time limit).
3. **Secondary — injury-dependence of feeding.** The same fixed contrast and computability rule,
   with the eating rate (`ate_food`) in place of bush share:
   `M3 = [E(hungry, high) − E(hungry, low)] − [E(fed, high) − E(fed, low)]`.
   A value > 0 means injury raises eating more when hungry, i.e. "eat first when hurt and hungry".
4. **Secondary — behavioural combination gain.** This is the simulation's own measure, applied to
   the agent. Label each step with the agent's activity (in cover, warming on a fire ring, eating,
   in the open). Then find the best single-variable predictor of that activity, and the best
   two-variable predictor, using nutrition, injury and body temperature. Each is cut into 10
   **fixed** bins: nutrition 0–200 and injury 0–100 in equal widths; body temperature (from
   `obs_true`) in equal widths between the `w0000` ordinary run's 0.5th and 99.5th percentiles,
   frozen as above, with open-ended outer bins. The gain is pair accuracy minus single accuracy.
   Under A1, "warming on a fire ring" is itself taxed (A1 charges distance from 0 degrees in
   either direction), so an A1 effect on this measure may reflect less time spent warming rather
   than a new combination rule.
5. **Context — scene battery. Invalid on factor-on cells for now.** The injury-level scene battery
   of [[INJURY_DEPENDENCE_PLAN]] builds its scenes from `environment/default`. On any cell with a
   factor switched on, it would therefore test the agent in a world where that factor is off: a
   regime mismatch ([[BODY_STATE_PROBE_GRID]] §A2). Until that plan lands and the battery can
   inherit the cell's own world, the battery is valid **only on `w0000`**, and no factor-on result
   from it is reported. **Probe-scene scope (user decision D7, 2026-09-26):** once the probe grid
   lands, each of the 32 runs is probed on a grid of **480 conditions, including a food scene, at
   the final checkpoint only**. The grid is defined as a combination spec (factors × levels), not
   as one config file per condition.

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
   unreplicated two-level factorial: it treats the bulk of small effects as noise. Two margins are
   computed from it and **both are reported for every effect**:
   - **ME** (margin of error) = t(0.975, 5) × PSE ≈ **2.57 × PSE**. Reported beside every effect
     for context. *(Superseded, Revision 1: ME was the decision margin for the one pre-registered
     contrast, B5's main effect. Revision 2 has no privileged contrast.)*
   - **SME** (simultaneous margin of error) = t(γ, 5) × PSE with γ = (1 + 0.95^(1/15)) / 2, which
     is ≈ **5.22 × PSE**. It guards against the fact that with 15 effects, at least one clears ME
     by chance about half the time in a pure-noise screen. Under Revision 2 **every** effect (all
     4 main effects, the 11 interactions, and the same set on each agent's own measure) is
     **noted** only when it exceeds SME, and the §2.2.1 sign-pattern check uses SME.
   - **Comparing two effects** (for example, "B3 beats B5") uses **√2 × SME**, since the
     difference of two effects carries the noise of both. *(Revision 1 used √2 × ME ≈ 3.64 × PSE
     for "another factor beats B5".)*

   Nothing is called significant.
2. **Across-checkpoint spread.** This is the standard deviation of `D_w` over the newest 5
   checkpoints. It follows the reading rule of [[INJURY_DEPENDENCE_PLAN]]: a per-world gap is
   stated only when it exceeds both agents' across-checkpoint spread.

Seed noise itself is **not** measured by either yardstick, so every noted effect is a candidate
for the follow-up, not a finding.

### 4.4 Temporal evolution

Survival is read from WandB at full resolution across all of training. Measure 1 is computed at
**every fifth checkpoint**: 10 points, at 1 M, 2 M, … 10 M episodes, on the recordings of §4.5.
Every fifth rather than every checkpoint was chosen to cut the recording volume from ≈ 3.8 TB to
≈ 0.6 TB (M6). This gives:

- the time course of `D_w` per world;
- the sampled checkpoint at which it first exceeds its late-window spread;
- whether a noted effect is present at the last four sampled points (7 M–10 M episodes), rather
  than only at the final one.

An effect present only at the final checkpoint is reported as unstable.

### 4.5 Recordings and their cost (M6)

Recordings use the Wave-2 collector settings (`seed_base: 1000000`, the same evaluation seeds)
unless stated otherwise. The sizes below scale linearly from the Wave-2 level-05 precedent, ≈ 47 GB
per 1 M episodes at float32. They are **upper bounds**: harder worlds end episodes sooner, so they
write fewer steps.

| Recording | Checkpoints | Episodes each | Precision | ≈ per run | ≈ 32 runs |
|---|---|---|---|---|---|
| Final | 50 (10 M) | 1,000,000 | float32, to stay comparable with the Wave-2 stores | 47 GB | 1.5 TB |
| Late window (§4.3 spread) | 46–49 | 100,000 | float32 | 4 × 3.4 = 14 GB | 0.44 TB |
| Time course (§4.4) | 5, 10, …, 40 (checkpoints 45 and 50 reuse the late and final recordings) | 50,000 | float16 | ≤ 8 × 2.4 = 19 GB | ≤ 0.6 TB |
| **Total** | | | | **≤ 80 GB** | **≤ 2.6 TB** |

- **float16** is the collector's lossy option. It is used only for the time-course set, whose
  stores are compared only with each other. It affects only float columns inside `obs_true`: body
  temperature in degrees and felt injury survive it at the needed resolution. Measure 1's true
  injury, nutrition and bush flags are separate columns. The float16 saving after compression is
  uncertain (floats compress about 2×), so the table budgets the float32 size.
- The NAS had ≈ 31 TB free at review time; the runner re-checks free space before collection.
- **Collection GPU time** was not measured for this design. The first factorial run's collection is
  timed and the figure is recorded here before the other 31 are queued.

### 4.6 Analysis tooling needed, and who builds it (M5)

No existing script computes measures 1, 3 or 4, or the factorial effects.
`scripts/analysis/injury_dose_store.py` bins by injury only, with no nutrition split. The following
are requested through `feature-workflow` (`senior-developer` plans, **`developer`** implements).
Each new file needs a row in `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` in the same change,
including the three-levels-deep `sys.path` note.

| Script (proposed path) | Computes | Needed by |
|---|---|---|
| `scripts/analysis/studies/level05_body_interactions/pilot_pick.py` | §2.3 read-out: `_window_n`-weighted S and starvation share from WandB full history, the pick rule and cap, and the §2.4 collapse rule | the stage-1 → 2 gate |
| `scripts/analysis/studies/level05_body_interactions/state_contrasts.py` | measures 1 and 3 (true and felt injury), per run and checkpoint, with the per-cell step counts and the computability verdict | before the factorial finishes |
| `scripts/analysis/studies/level05_body_interactions/behavioural_combination_gain.py` | measure 4; body temperature from the `obs_true` slot, not a store column | before the factorial finishes |
| `scripts/analysis/studies/level05_body_interactions/factorial_effects.py` | §4.2–4.3: the 15 effects on `D_w` and on each agent, PSE / ME / SME / √2 × ME, and with/without collapsed cells (§5) | before the factorial finishes |

**Known-input check:** each store-reading script is first run on the Wave-2 level-05 stores
(`results/trajectories_basicq2_w2`, both agents). There, measure 1 is expected to be ≈ 0 for both
agents, because both learned "hurt → hide" whatever their nutrition. That is a sanity check, not a
test of this study's hypothesis.

### 4.7 Follow-up this screen feeds (named now)

Take the noted factors plus `w0000`: at most 4 cells, i.e. the 2×2 of the two strongest noted
factors (Revision 2; Revision 1 named "B5 × the strongest other factor"). Train them with **5 seeds** per agent, at 10 M episodes, which is
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
| Every effect inside SME (§4.3) | a null screen at 1 seed, uninformative about whether the simulation transfers. The follow-up is then **not** automatic, and the PI is consulted. *(Revision 1 wording: "B5's effect inside ME and every other effect inside SME".)* |
| A healing-rule effect (B5 or B3) exists only against felt injury, or only against true injury | reported separately; felt-only is the more interesting, because the modulator reads felt injury |

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
- Because the error sits in the **base** world, it shifts the baseline that every simulated
  gain in §2.2 is measured against: all four predictions, not only A4's. The most plausible
  direction is that the food-draining rules (A4, and B3 through the cost of re-eating) look milder
  than they are. For B5 and A1 the direction is not known in advance. §2.8 states the same scope
  (reconciled in Revision 1).

The A4 trip form's strength is calibrated from real resets, so the pilots do not depend on the
number. The **registered predictions** do. The simulation was re-run with base trip 4
(`results/analysis/internal_state_interactions/sweep_food4/`, fix in commit `e2991ceb`), and the
predictions were re-registered from it before any pilot launched (Revision 2, §2.2.1). This doc
does not edit that study.

---

## Metrics Requested

None blocking. Every measure in §4 is computable from existing WandB keys (`Episode/Steps`,
`Episode/Term_*`, `Episode/_window_n`, `Episode/Number`) and existing trajectory-store columns
(`nutrition`, `injury_level`, `agent_in_bush`, `ate_food`, `rested`, `obs_true`). New *analysis
scripts* are needed (§4.6), but no new logged metric. The trajectory-store body-temperature column
([[STATE_DEPENDENT_BODY_MECHANICS]] "Still open" item 2) has been deferred by the user to a
separate job. This design does **not** depend on it: temperature comes from `obs_true`.

| Metric | Why now | Where it'd live | Cost |
|---|---|---|---|
| Per-episode mean nutrition spent on healing (B3) and mean healing factor (B5) | would show directly how much each mechanic *engaged* per cell, rather than inferring it from injury / nutrition deltas | `src/environment/core.py::update_body` info → trainer episode logger | cheap (scalar per step) |

---

## Links

- Implementation of the four mechanics: [[STATE_DEPENDENT_BODY_MECHANICS]]
  (`docs/develop/active/thermal/STATE_DEPENDENT_BODY_MECHANICS.md`)
- Simulation study and sweep: [[STUDY_PLAN]]
  (`docs/experiments/active/internal_state_interactions/`); Revision 2 numbers from
  `results/analysis/internal_state_interactions/sweep_food4/*.json`; superseded Revision 1
  numbers from `reading_rule.json` and `sweep/*.json`
- Agents and prior level-05 runs: [[BASIC_LEVELS_Q2_DEFAULT]]; runs
  `results/JAX_RecurrentPPO/20260922-182534_rppo_bq2cover_lvl05_t1none_s42` and
  `20260922-182538_rppo_bq2cover_lvl05_t16quad_s42` (WandB `z2u1orlf`, `ihq3tt7f`)
- Injury-dependence measures and reading rule: [[INJURY_DEPENDENCE_PLAN]]
- Registry entry: `docs/environment/CONFIG_CRITICAL_SETTINGS.md`, change log 2026-09-26

---

## Feedback from plan-reviewer

**Verdict: SOUND WITH CONCERNS** (2026-09-26, reviewed against commit `ec92b077`, before any pilot launched).

Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run · 🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

### What passes

The metric is survival steps throughout and reward is never read (§2.3, §4.1). A refutation criterion is registered before data (§2.2). The training budget is passed explicitly (`--episodes`; `train.py:394`), `--seed` exists (`train.py:395`), and seed 42 is config-owned (`configs/train/default.yaml:83`). No learning-rate or entropy schedule is keyed to the episode budget (none in `train.py` or `src/algorithms/`), so a 2 M-episode pilot is, in expectation, the first 2 M episodes of a 10 M run. The loader's list form of `extends:` is real (`src/environment/config_loader.py:37-73`); §3.2's validation went through the trainer's own loader, and §3.1's pre-flight reads the run's saved `models/config.yaml`, so neither is circular. Every factor key is read with `get_mandatory` (`config_loader.py:1775-1778`, `2481-2528`). The registry change-log entry exists (`CONFIG_CRITICAL_SETTINGS.md:50`). The two agent configs differ only in `modulation` (diffed). The registered simulation numbers match `results/analysis/internal_state_interactions/reading_rule.json` exactly. Level 04 does not restate `resources:`, so the trip fragment's verbatim level-03 list is the right base. Body temperature **is** recoverable from `obs_true` in raw degrees (`src/environment/sensor.py:488`), so the diary's 22:06 decision (no store column) is honoured. Known Bugs registry checked (rows on the stale nested `training.seed` copy, mandatory-key breakage of saved configs, the B3 `partial` starvation guard, termination codes with a body system off): none is walked into; nothing unrecorded was found.

### Findings

| # | Sev | Where | Issue | Suggested fix | Owner |
|---|---|---|---|---|---|
| M1 | 🟡 | §2.3 pick rule | The two thresholds can cross. Non-negligible needs `S_base − S ≥ max(2n, 0.05·S_base)`; survivable needs `S ≥ 0.80·S_base`. If the two base seeds differ by more than 10 % of `S_base` (`n > 0.10·S_base`), **no strength can satisfy both**, and the edge case then mis-diagnoses "no measurable effect" and picks the *strongest* survivable strength — the opposite of the stated intent. Level-05 survival was still climbing steeply near 2 M (192 → 230 between 1.0 M and 1.8 M), so a 10 % seed gap is plausible. One |Δ| from two seeds is also a very weak noise estimate (25 % of the time it is under 0.4 σ). | Cap the non-negligible threshold so a band always remains (e.g. `min(max(2n, 0.05·S_base), 0.15·S_base)`), or fix it at `0.05·S_base` and report `n` as context; or add a third base seed. Decide before P0a/P0b run. | experiment-designer |
| M2 | 🟡 | §2.2 predictions | Two facts from the simulation's own output are not disclosed: every B5 world **failed** the study's pre-registered 5-point rule (`passes: false`), and at discount 0.99 B5's combination gain is **below** baseline (0.120–0.139 vs 0.160) — the sign flips on the study's own robustness check (its rule 4). Registering "positive, largest" from the 0.95 result alone is defensible (0.95 is the agents' γ) but must be said, or a positive B5 reads as "confirmed as predicted" with a stronger prior than the evidence gives. Separately, §6.3 says the trip mis-measurement could soften *every* food-related prediction including B3, while §2.8 says "the A4 trip-form prediction only" — the two sections disagree. | Add both facts to the §2.2 table. Re-running the sweep with the corrected base trip (4) costs minutes; do it before the pilots so the registration rests on a baseline that matches the real world, and reconcile §2.8 with §6.3. | experiment-designer (+ the study's owner) |
| M3 | 🟡 | §2.3 "weakest" pick | For B5 the simulation rates floor 0.5 at one-third the gain of 0.2 / 0.0. The weakest-non-negligible rule will pick 0.5 whenever it dents survival by ≥ 5 %, deflating the one factor the screen exists to detect. The stacking rationale for "weakest" is food drain, and §2.4 itself notes B5 drains no food. | Pick the **strongest survivable** strength for B5; keep "weakest" for the three drainers (B3, A1, A4). | experiment-designer |
| M4 | 🟡 | §4.3 noise rule | Lenth's margin (2.57 × PSE) is a real, decidable criterion for the **one** pre-registered contrast (B5's main effect). Applied to all 15 effects it notes at least one effect by chance about 54 % of the time under a pure-noise screen, so "noted when it stands out" is not a criterion for the 14 exploratory effects. The refutation clause "another factor exceeds B5 by more than the margin" compares two effects, whose difference carries √2 × the noise. | Report Lenth's simultaneous margin (SME ≈ 5.2 × PSE at m = 15) beside the individual one; an exploratory effect is "noted" only above SME. Use √2 × ME for the between-effect comparison. | experiment-designer |
| M5 | 🟡 | §4.1 measure 1 | (a) The slope is fitted over injury bins with < 200-step bins dropped, so the fitted range differs by cell and by agent (worlds where agents die young have no high-injury / low-nutrition steps); slopes over different ranges are not comparable. (b) No existing script computes it: `scripts/analysis/injury_dose_store.py` bins by injury only (ten bins, `EDGES` at line 36) with no nutrition split. Measures 1, 3 and 4 need new analysis scripts, which need `SCRIPTS_DEPENDENCY_MAP.md` rows, and no owner is named. | Pre-register a fixed injury range that every cell must cover (else "not computable"), or replace the slope with a fixed contrast (bush share at injury 60–100 minus 0–20, per nutrition band). Name the analysis tooling and its owner in §4 now. | experiment-designer → developer |
| M6 | 🟡 | §4.1 / §4.4 volume | Recording cost is uncosted. Wave-2 precedent: 1 M episodes at the final checkpoint = 47 GB per level-05 run (float32 obs); five late checkpoints × 100 k = 17 GB. Repeating both for 32 runs ≈ 2 TB; §4.4's 50 checkpoints × 50 k episodes ≈ 118 GB per run ≈ 3.8 TB, plus collection GPU-time. The NAS has 31 TB free, so it is feasible, but not free. | State the episode counts per checkpoint, the `obs_precision` (float16 is the collector's lossy option; degrees survive it), and the expected TB, and decide §4.4's cadence (every checkpoint vs every fifth) before the factorial finishes. | experiment-designer |
| M7 | 🟡 | §2.6 controls, over weeks | Every pilot and world resolves through `basic/05 → 04 → 03 → default.yaml`, all maintained and edited by parallel sessions (a bush-fire clearance change to that ladder is queued at commit `8f87df9f`; mandatory keys keep landing). A default-value change between the pilots and the factorial, or mid-factorial, puts cells on different base worlds, and §3.1's pre-flight checks only the factor keys, so nothing would detect it. | Pre-register two checks: at each launch record `git rev-parse HEAD` and `git log -1 -- configs/environment/default.yaml configs/environment/experiment/basic/`; after the last launch, diff the 32 saved `models/config.yaml` files pairwise — identical outside the factor keys, and identical to the pilot base outside the factor keys. Any difference is a registered confound. | training-runner / experiment-designer |
| L1 | 🟢 | §2.3 read-out | WandB `Episode/Steps` rows are window means with a varying `Episode/_window_n` (`train.py:1552`). "Mean over episodes 1.8–2.0 M" should be an `_window_n`-weighted mean over rows selected by `Episode/Number`, not a plain mean of rows. | Say so in §2.3. | experiment-designer |
| L2 | 🟢 | §1, §2.1 wording of A1 | The mechanic (`src/environment/core.py:266-269`) charges `rate × 0.02 × |T − 0|` symmetrically: sitting on the +8.8° fire ring costs 0.35 / 0.7 / 1.4 per step, the same as being at −8.8°. The fragment headers have the right formula; the doc's prose ("staying warm costs food") does not, and it matters for measure 4, where the "warm up" activity is itself taxed. | Reword to "being away from the comfortable temperature costs food, in either direction". | experiment-designer |
| L3 | 🟢 | §4.1 measure 5 | The injury scene battery extends `environment/default`, so on any on-cell it tests the agent in a world with its factor switched off (regime mismatch; [[BODY_STATE_PROBE_GRID]] §A2). It is invalid for on-cells until that plan lands, not merely "secondary". | Say so. | experiment-designer |
| L4 | 🟢 | §2.9 placement | The folder sits outside `basic/` and `archive/`, which CLAUDE.md's letter forbids; the doc flags it and `behavior_probes/` is precedent, so the user should approve it explicitly. The compat test does glob it (`tests/env/test_backward_compat_configs.py:33`); the fragments and selectors skip on "required but missing" as the design says. Mechanical YAML soundness is `env-config-reviewer`'s. | User's call. | user / env-config-reviewer |

### Open assumptions (❓)

- **O1.** A harder world's learning curve may be slower than the base world's, so "not survivable at 2 M" may be survivable at 10 M; the rule rejects slow-learning strengths. The "91 % of final by 2 M" figure also comes from a B1-off Wave-2 run, while the pilot base is B1-on.
- **O2.** Seed noise on level-05 survival at 2 M is unknown; the whole pick rule rests on one |Δ| between seeds 42 and 43 (M1).
- **O3.** §2.4's collapse rule fires at `S < 0.60·S_base`; four independently survivable factors each at the 0.80 limit compound to 0.41 with **no interaction at all**. Fine as an analysability gate; do not read "collapsed" as evidence of an interaction.
- **O4.** The ordinary GRU agent also sees satiation and felt injury and can learn the same conjunction; §4.2's per-agent decomposition covers this, but it compounds §2.7's null ambiguity.
- **O5.** "30 free GPUs" is live state; `gpu-status` at launch, not this doc.

### Cost of being wrong

If the pick rule mis-selects (M1, M3) or the base ladder drifts under the study (M7), the ~510 GPU-hour factorial answers a different question than the one registered for at least one factor, and that factor's half must be rerun (~250 GPU-hours, about a day on the cluster). M2 and M4 cost no compute but would turn a chance "noted" effect into a claimed confirmation. There is no data-loss exposure in this plan.

*Reviewed by: plan-reviewer*
