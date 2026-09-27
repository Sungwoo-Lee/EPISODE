# Interactions between internal states — a simulation study to choose level-05 settings

## Question

Level 05 is becoming the project's main level for studying whether a neuromodulated agent's
behaviour depends on its body state more than an ordinary agent's does. The analysis page
*Injury, Behaviour and the Modulator* found that, today, injury dependence is a simple habit both
agents learn equally: when injured, hide and rest — right regardless of hunger or cold. A modulator
(which rescales the network according to the body) should matter when the best action depends on
**combinations** of body states: injured *and* hungry, injured *and* cold.

Five new body rules are being implemented (plan:
[[STATE_DEPENDENT_BODY_MECHANICS]]): B1 random starting body temperature, B2 healing slows when too
cold or too warm, B3 healing uses food energy, B4 injury speeds heat loss, B5 healing speed depends
on food energy; plus existing, currently-off settings (A1 staying warm costs food; A4 scarcer food;
A5 fewer bushes). This study asks, **before any training**: for which settings does the best action
depend on more than one body state at once — and does no single need win everywhere? It uses a
small simulator of the body rules and an idealised planner, not a trained agent, so it runs in
minutes and can sweep many settings.

## What is simulated

**The body, exactly as the environment updates it** (level-05 values; `src/environment/core.py::
update_body` and the plan's formulas for B1–B5): food energy (0–200, ideal 100; −1 per step; +5 net
per bite; death at 0 and at 200), injury (0–100; healing only while resting and not being hurt,
0.2 per step in the open, ×25 in a bush; death at 100), body temperature (death outside −15..+15;
`d = 0.04(T_cell − T) − 0.02(T − 0)`, applied ×2.0 when warming and ×0.25 when cooling). Reward per
step = decrease in the drive `sqrt((N − 100)² + I² + (T·100/15)²)`, −100 on death — the
environment's own reward.

**The world, reduced to five places** an agent can be: open cold ground (cell −30), a bush in the
cold (−30), a bush beside a fire (the warm ring, cell ≈ +8.5), the open warm ring (+8.5), and a food
item (−30). Moving between places takes a fixed number of steps through cold ground (4 by default;
scarcer food or fewer bushes = a longer trip to that place). At a place the agent can rest or, at
food, eat. Food items allow 12 bites and then reappear elsewhere; the simulator ignores depletion
(stated limitation).

**Validation, before any result is read.** The simulator's one-step body update is compared with
the real environment's `update_body` on thousands of random states and actions: today's rules now,
and B1–B5 once the implementation lands. Any mismatch beyond float tolerance blocks the page.

## What is computed

1. **Single-rule curves** — healing per step against body temperature (B2) and food energy (B5);
   time to freeze against injury (B4); food spent to heal a wound (B3). What each rule does alone.
2. **Scripted routines** — e.g. "rest in the cold bush until healed", "eat first, then heal",
   "warm up first, then heal", from representative starting states: steps, food spent, whether the
   agent survives. How the rules trade off in plain cases.
3. **An ideal planner** — value iteration (dynamic programming: the best long-run return from every
   state, computed exactly on a grid of food × injury × temperature × place) gives the best next
   activity for every body state: go/stay and rest in a bush, go eat, go warm up at the fire.
4. **Two numbers per world**, over the states a training episode can start in (injury 0–100,
   food 0–200, temperature −10..+5 at open ground):
   - **need balance** — the share of starting states in which each activity is best. A world where
     one activity is best in over 80 % of states is dominated by one need.
   - **interaction share** — the share of starting states whose best activity cannot be predicted
     from any *single* body variable (for each variable alone, the best predictor is "the most
     common best activity at that value"; the interaction share is 1 minus the accuracy of the best
     such predictor). Higher = the task needs combinations of states.
5. **Sweeps** — each setting varied alone from today's level 05 (with B1): A1 coupling rate,
   B3 cost (partial mode), A4 (trip to food and food value), A5 (trip to a bush; warm bush present or
   not), and, for completeness, B2, B4, B5.

## Reading rule, fixed now

A setting is **recommended for training** when, relative to today's level 05 with B1: the
interaction share rises by at least 5 percentage points, **and** no activity is best in more than 80 %
of starting states, **and** at least one activity other than "rest in a bush" is best in at least
10 %. Settings are ranked by interaction share among those that pass. This is a planning tool, not
evidence about agents: an ideal planner is not a trained network, and the reduced world omits
predators, depletion and the exact map.

## Deliverable

An artifact page (house style, figures by scripts, guide §11 requirements), plan-reviewer check of
its claims and a format review before publishing; results feed the experiment designer's level-05
variant configs (outside `basic/`, user decision).

## Files

- Simulator + validation: `scripts/analysis/studies/internal_state_interactions/`
- Outputs: `results/analysis/internal_state_interactions/`
- Page: `docs/experiments/active/internal_state_interactions/`

## Revision 1 (2026-09-26) — answers to the plan-reviewer, written before any sweep result was read

The first sweep (discount 0.99) was stopped and deleted unread except one smoke test of the baseline
(interaction share 0.33 at 0.99, before any of the changes below; not used). Changes:

**Terms.** A1 = `thermal.metabolic_coupling` (staying warm costs food); A4 = scarcer food (longer
trip to food, or less food energy per bite); A5 = fewer bushes (longer trip to cover). B1–B5 as in
[[STATE_DEPENDENT_BODY_MECHANICS]].

**Measured, not assumed** (`measure_world.py` → `results/analysis/internal_state_interactions/world_measurements.json`,
300 real level-05 resets and the Wave 2 level-05 training recordings):
- discount **0.95** — the level-05 training runs' own `agent.gamma` (C1). 0.99 is a sensitivity check.
- trips: nearest bush, food item and fire ring are each a median **2** steps from a random open cell
  (p90 4–5) → base trip 2 steps; A4/A5 lengthen the one trip to 4, 6, 8 (M9).
- fire-ring cell **+8.8** (median; p10–p90 8.4–9.2); every other cell ≈ −30 except two steps from a
  fire (≈ −16.5). One number used everywhere (L1).
- warm bush (a bush on a fire ring) in **41 %** of episodes → every world solved on both maps,
  summaries pooled 0.59 / 0.41 (M5).
- **predator hazard 0.64** expected injury per step outside a bush (0 inside; both agents' recordings
  agree to 0.01) → added to every non-bush step (M3). Sensitivity 0 and 1.28.
- the last step of a trip is taken in the destination cell, as in the environment (L2).

**Metric (M1, M2).** Four choice categories: rest in cover (cold or warm bush), warm up (fire ring),
eat, stay in the open (wait or rest in the open, merged). A state is a **tie** when the best and
second-best categories are within 0.5 return units; ties are excluded from the accuracies and their
share is reported. The measure the rule uses is the **combination gain** = (accuracy of the best
two-variable rule) − (accuracy of the best one-variable rule): how much knowing a second body variable
improves the best choice, which a mere rebalancing of categories does not raise. The noise floor is
today's world re-solved on a finer grid (81 × 41 × 91).

**Survival (M6).** The ideal policy is rolled out from 2,000 training-style starts per map for 500
steps; the survival share is reported per world.

**Food depletion (M4)** is not modelled; its bias is stated: it makes eating look cheaper, so worlds
that depend on scarce food (A4) are, if anything, under-rated by the planner.

**Injury lag (O1).** The agent feels injury through a delayed signal; the planner sees injury
directly. Stated as a limitation; it affects every world alike.

### Reading rule (pre-registered; replaces the one above)

A world is **recommended for training** when, against today's level 05 with B1, at discount 0.95,
pooled over both maps:
1. its combination gain is at least **5 points** higher **and** the difference exceeds twice the noise
   floor (|finer-grid − baseline| on the same measure);
2. no category is best in more than **80 %** of start states, and a category other than "rest in
   cover" is best in at least **10 %**;
3. its survival share is at most **5 points** below today's;
4. the same direction holds at discount 0.99 (reported as robust or not; not a veto).
Recommended worlds are ranked by combination gain. The page reports every world, pass or not.

**Gates (M7, M8).** The page build refuses to run unless `validation_current_rules.json` shows
`pass: true`, and — once B1–B5 land — a validation of the new rules at the sweep's extreme values
(B3 cost 2, B2 1/10, B4 gain 2, B5 floor 0) also passes; until then the page states that the new-rule
numbers are simulator-only. The new `scripts/` folder gets its rows in the scripts dependency map in
the same commit.

**Prior art (L4).** `docs/experiments/active/recovery_in_bush_tuning/` (recovery_math.py, closed-loop
validation through a stripped world) and the internal-state reward study are the precedents; this
study reuses their approach of checking a numeric model against the real `update_body`.

### Revision 1b (2026-09-26) — answers to the confirming pass (R1–R8), before any sweep result was read

The sweep started after Revision 1 was stopped and deleted unread. Changes: every world is solved at
0.99 as well, so rule 4 is evaluated per world (R1); accuracies and the combination gain are computed
within each map and then pooled 0.59 / 0.41 (R2); the predator hazard is split — **0.12** per resting
step and **0.70** per other step outside a bush (measured; both agents agree within 0.04), with the
mean-field and selection caveats stated (R3); the gain is also reported at tie margins 0 and 2
alongside 0.5, and a world whose tie share exceeds **40 %** is flagged and not ranked (R4); the
validation record carries the source commit (`2004b234`) and the page build checks it (R5); arriving
in a bush counts as cover on the arrival step (R6); the sweep asserts the planner discount equals the
training runs' measured one (R7); the page build refuses without passing validation (R8).

## Feedback from plan-reviewer

**Verdict: NOT READY** (2026-09-26, reviewed against the plan above and the scripts that had
appeared in `scripts/analysis/studies/internal_state_interactions/` at review time). Full report
with the evidence: [[plan_internal_state_interactions]]
(`docs/reviews/plan_internal_state_interactions.md`).

**In plain language.** The study is a sound idea and the body simulator is validated the right way
(it is checked against the real environment's own update function, not against a copy). But the
one setting that decides what the "ideal planner" calls best — how far ahead it looks (the discount
factor) — is not stated in the plan, and the code sets it to 0.99 while every agent this project
trains uses 0.95 (a 100-step horizon versus a 20-step one). The processes the sweeps vary — slow
healing, longer trips to food and cover — are exactly the ones that horizon changes, so the label
map, and with it the recommended settings, would be computed for an agent the project does not
train. Fix: pre-register the discount in this plan, read it from the training agent's config, run
0.95 as the headline and 0.99 as a sensitivity check.

**Also to settle before data is read** (Moderate): the "interaction share" is inflated by exact
ties and grid interpolation between "wait" and "rest in the open" (about the size of the 5-point
threshold) and is capped by how balanced the activities are, so it needs an indifference margin, a
measured noise floor, and the pair-over-single gain reported beside it; the reduced world omits
predators and food depletion in a direction that makes cover look worse and eating look cheaper
than in the real world, which is the direction the current "hide when injured" habit would exploit;
the reading rule leaves open which layout (warm bush present / absent) is compared and whether
"rest in cover (warm)" and "wait" count as activities; the ideal policy's survival share per world
should be reported so no unsurvivable world is recommended; validation must gate the sweep and
the page (today nothing enforces it) and cover the sweep's extreme values; the new `scripts/`
directory needs rows in the scripts dependency map; and the plan says trips take 4 steps while the
code uses 3 and cites a measurement the plan does not record.

**What would flip the verdict to SOUND WITH CONCERNS:** the discount named in this plan with its
source and matched in the code, and the reading rule's category list, layout comparison and
indifference margin written down here before the sweep is read.

Reviewed by: plan-reviewer

## Feedback from plan-reviewer — addendum (confirming pass on Revision 1, commit `ad96c082`)

**Verdict: SOUND WITH CONCERNS.** The Critical finding is resolved: the discount is 0.95, read from
the two level-05 training runs' saved configs and recorded in `world_measurements.json`, with 0.99
kept as a sensitivity check. Of the nine Moderate findings, seven are resolved in both plan and code
(M1 tie margin + merged categories, M2 combination gain + finer-grid floor, M4 stated, M5 pooled
maps + fixed categories, M6 survival rollout, M8 map row, M9 measured trips); M3 and M7 are
resolved in design but each leaves one concern below. The simulator validation passed (4,000
states, max difference 2e-5, no death-flag mismatch).

**Concerns to settle before the page is read** (none blocks the sweep from running):

| # | Sev | Where | Concern | Fix |
|---|---|---|---|---|
| R1 | 🟡 | Reading rule condition 4; `sweep.py:47` | The 0.99 check is solved for the baseline only, so "the same direction holds at 0.99" cannot be evaluated per world. | Solve every world (or every world that passes 1–3) at 0.99 too; it is the same code with `gamma=0.99`. |
| R2 | 🟡 | `planner.summarise` (pooled accuracies) | Both maps are pooled *before* the accuracies are computed, so a label that differs between the maps at the same body state counts as "unexplained by any body variable". Map identity is not a body-state interaction; it lowers single and pair accuracy together and moves the gain in a direction that is not sign-determined. | Compute single / pair accuracy and the gain per map, then pool the gains 0.59 / 0.41 (balance and tie share can stay pooled). |
| R3 | 🟡 | `measure_world.py:60-66`; `planner.one_step` | The hazard 0.64 is the mean damage over *all* open steps, moving and resting alike, but it is charged identically to "rest in the open", "warm up", "eat" and travel. Walking into hidden predators and being pounced while resting are different rates, and the rest-vs-cover split is the choice the metric hinges on. The 0 / 1.28 sensitivity brackets it only for the baseline. | Split the measurement by action (rest vs not) outside bushes and use two hazards (rest, move). Expected-value treatment is fine to first order — a 3 % chance of a ~21-point hit has the same mean — but say on the page that deaths from a single large hit at high injury are under-counted by a deterministic drift. |
| R4 | 🟡 | Reading rule (ties excluded) | Excluding ties changes the population the gain is computed over; a world with a large tie share is compared on a different subset than the baseline. The finer-grid floor calibrates the grid, not the margin. | Add to the rule: a world whose tie share exceeds a stated cap (e.g. 20 %) is flagged, not ranked; report the baseline's gain at margins 0 / 0.5 / 2 so the margin's leverage is visible. |
| R5 | 🟡 | `validation_current_rules.json` (`src_root` is a session scratchpad path) | The gate's meaning is "validated against *these* rules", but the record names a temporary copy that will not exist tomorrow. | `validate.py` records the commit SHA of the frozen tree (and `sweep`/page build print it); the gate compares it with the SHA the sweep ran against. |
| R6 | 🟢 | `planner.macro:95` | The arrival step of a trip is flagged `bush=False`, so a trip *to* cover is charged one hazard step the environment would not charge (animals cannot enter the bush). Small (0.64 injury) and one-directional against cover. | Use `IN_BUSH[place]` on the last step. |
| R7 | 🟢 | `planner.World.gamma` literal | 0.95 is typed, while the plan says it is read from the runs. | `sweep.py` asserts the literal equals `world_measurements.json["gamma"]`. |
| R8 | 🟢 | Gates | The page-build refusal without a passing validation is a plan promise; no `build_page.py` exists yet. Expected at this stage; must be in the build script when it appears. | — |

**Checked and holds:** the hazard's death and drive accounting (`one_step:82-86`); the pair-key
construction cannot collide on this grid; the start mask's −10 / +5 bounds fall on grid points at
both resolutions; the rollout's step accounting and 500-step cap; the trip measurement (nothing
blocks movement on this map, so Manhattan distance is the path length); the map row.

**Cost of being wrong now:** rankings could shift at the margin by R2/R3/R4, and condition 4 is
unevaluable until R1 — a re-run of a minutes-long sweep, not a wrong horizon.

Reviewed by: plan-reviewer

## Feedback from plan-reviewer — analysis-verdict review of the built page (commit `71e0d770`)

**Verdict: SUPPORTED WITH CAVEATS**, one 🔴 Critical on interpretation. The rule was applied exactly
as pre-registered and every number checked is right; but the passing world's pooled +6.9 splits
+3.0 on the map without a warm bush (inside that map's noise) and +12.5 on the map with one (where
the change also moves the warm bush away and breaks its dominance), while B5 splits +5.4 / +0.4 —
the ranking inverts on the majority map. Callout and §07 must report the per-map split before the
batch is chosen. Full table: [[plan_internal_state_interactions]] § "Analysis-verdict review".

Reviewed by: plan-reviewer

---

## Revision 2 (2026-09-27) — the balance study, written before any Revision-2 result was read

### Question, in plain words

The first version of this study asked which single rule makes the best action depend on
combinations of body states. The user reframed the goal: the new body rules exist to **lower the
weight of injury recovery by raising the weight of the other needs** — but if food or temperature
become too important, the agent just forages or warms all the time, hiding collapses, and the
world is as one-sided as before in the other direction. What is wanted is a **balanced** world:
hiding, eating and warming each matter in a good share of situations, no single danger causes most
deaths, and which action is best depends on how injured, hungry and cold the agent is at once.
The expected shape is an inverted U: as food/temperature pressure rises, combination dependence
rises, peaks, then falls as one need takes over. This revision (a) finds where the balanced region
lies in the simulation, over the settings that shape it, and (b) turns the findings into the
balance metrics and criteria that real (ordinary-agent-only) training will be judged by. The
simulation guides where to look; trained agents decide (user, 2026-09-27).

Every setting that can shift the balance is listed in [[BALANCE_SETTINGS_INVENTORY]] (109 settings,
with level-05 values and whether the simulator models them). A correction from the user
discussion: the simulator **did** include the eating cost (net +5 per bite, then −1 per step, so an
eating step nets +4; validated against `update_body`) — the error was the parent session describing
the "less food per bite" pick as "6 → 4 per bite" instead of "+4 → +2 per eating step".

### What changes in the simulator (each validated or measured before use)

The inventory's unmodeled settings most likely to move the balance, and what is done about each:

| # | Setting | Change | Source of numbers |
|---|---|---|---|
| E1 | Food runs out after 12 bites and reappears elsewhere | After each bite, with probability 1/12 the item moves: the agent is back at open ground and must pay the food trip again (a geometric stand-in with the same mean of 12 bites; the "bites left" state is not tracked) | config (`max_consumption 12`, `regeneration_delay 0`) |
| E2 | Predator and ambusher hits are single large events, not a steady average | Outside cover, each step carries a probability of a hit whose size is drawn from the measured hit-size distribution (summarised by 5 quantiles); the planner averages its value over the outcomes, so an injured agent faces a real chance of a lethal hit | Wave-2 level-05 recordings: per-step hit probability resting / not resting outside a bush, and the size distribution of hits (`damage > 0`) |
| E3 | Healing is blocked while a hit lands (3 steps) | Not modeled; stated as a limit (it slightly understates the cost of being hit) | — |
| E4 | Injury is felt late and smoothed | Not modeled (the planner knows its injury); stated as the main limit. It belongs to the trained-agent test | — |
| E5 | Food may sit on a warm ring; the cooler diagonal cell near a fire | Not modeled; stated | — |
| E6 | Start position anywhere; 500-step limit | Rollouts start at open ground and run 500 steps, as before | — |

The existing mean-field hazard stays available as a check: every Revision-2 world is also solved
with E2 off, so the effect of the modelling change itself is visible.

### Balance measures (computed per world, pooled over the two maps as before)

From the planner's solution at training start states (as before):
- **B-choice** — share of start states where each choice (rest in cover, eat, warm up, stay in the open) is best.
- **B-comb** — combination gain (as before).

From rollouts of the ideal policy (2,000 training-style starts per map, 500 steps):
- **B-time** — share of steps spent in each activity: in cover, eating, warming (at the ring), elsewhere.
- **B-need** — share of steps on which each need is the largest part of the drive: hunger `|S − 100|`, injury `I`, temperature `|T|·100/15`.
- **B-death** — share of deaths by cause: starvation, over-eating, injury, cold, heat.
- **B-surv** — survival share (as before).
- **B-hide** — injury-driven hiding: among well-fed states (food 80–160), steps in cover when injury ≥ 60 vs when injury ≤ 20; and the same gap among hungry states (food < 60) — the "combination" version of hiding.

### Balance criteria (pre-registered; a world is **balanced** only if all hold)

1. **B-time:** no activity takes more than 70 % of steps, and cover, eating and warming each take at least 10 %.
2. **B-need:** each of hunger, injury and temperature is the largest need on at least 15 % of steps.
3. **B-death:** no single cause accounts for more than 60 % of deaths (if at least 5 % of starts die).
4. **B-surv:** survival at least 80 % of today's level 05 under the same simulator.
5. **B-hide:** among well-fed states, hiding at high injury is at least twice hiding at low injury (injury still drives hiding).
6. **B-comb:** combination gain above today's by more than twice the noise floor (re-measured on a finer grid with E1–E2 on).

A world meeting 1–5 but not 6 is "balanced but not combinational"; a world meeting 6 but failing
1–3 is "combinational but one-sided". Both are reported. No threshold moves after results are read.

### What is swept

Today's level 05 (with B1) under E1–E2 is the baseline. Axes, each with today's value and a range
that crosses from "injury dominates" to "food/temperature dominates":

| Pressure | Setting | Values |
|---|---|---|
| Food | energy per bite (gross; eating cost 1 stays) | 6 (today), 5, 4, 3 |
| Food | trip to food (steps) | 4 (today, measured), 6, 8 |
| Food | bites per item | 12 (today), 6 |
| Injury | hit probability outside cover | ×0.5, ×1 (today), ×2 |
| Injury | healing in a bush (multiplier) | 25 (today), 10 |
| Temperature | bush on a fire ring | allowed (41 % of episodes, today) / never (bush-fire clearance on) |
| Temperature | cooling rate scale | 0.25 (today), 0.5 |
| Coupling | the four rules of the running 16-world experiment, at their picked strengths (hungry healing floor 0; healing costs 0.5 food per point; cold/heat costs food at rate 2; gross food per bite 4) | on / off, one at a time and all four |

Design: one axis at a time from the baseline (≈ 20 worlds), then a **2-D grid of food pressure ×
injury pressure** (energy per bite 6/5/4/3 × hit probability ×0.5/×1/×2 = 12 worlds) at both bush-
fire settings (24 worlds) — the grid is where the inverted U, if any, shows. Every world is solved
on both maps (warm bush / none) at discount 0.95 and, as a check, 0.99. About 50–60 worlds; each
takes minutes on 16 processes.

### Deliverables

1. The study page *Interactions Between Internal States* updated: a new lead section on balance (the
   inverted-U question, the measures, where the balanced region lies, and which settings move it),
   the inventory summarised, the first version's single-rule results kept as the second section, and
   the correction box extended.
2. A short "what the trained-agent metrics should measure" section: which of the B-measures can be
   logged during training, which need recorded episodes, and proposed thresholds — the input to the
   metric implementation plan that follows this study (owner: senior-developer).

### Validation before any result is read

- E1 and E2 change only the planner's world model, not the body update (bodysim stays validated).
- E2's numbers are measured and written to `world_measurements.json` before the sweep runs; the
  measurement reads the Wave-2 level-05 recordings of **both** agents and reports each separately.
- With E1 and E2 switched off, the new code must reproduce the Revision-1 corrected sweep
  (`sweep_food4/`) exactly for the baseline and three other worlds.

### Limits stated in advance

The planner knows its injury exactly (E4), sees predators only as measured hit odds (no chasing,
no escape by running), and uses the Wave-2 runs' hit odds, which came from agents that started at
0 °C and were not trained under these settings. The simulation locates candidate balanced settings;
the ordinary-agent training that follows is what tests them.

## Feedback from plan-reviewer — Revision 2 (the balance study), before any Revision-2 result

**Verdict: NOT READY** (2026-09-27). Two Critical findings, both cheap to fix; eight Moderate; full
table with the measured evidence: [[plan_balance_study]] (`docs/reviews/plan_balance_study.md`).

**In plain language.** The study's idea and its measurement discipline are sound, but two pieces
must change before the sweep runs. First, balance criterion 2 — "each need is the largest part of
the drive on at least 15 % of steps" — is decided by the map, not by the settings: no cell lets
the body settle at 0 °C (the warm ring settles it at +5.9 °C, which the drive weighs as 39 units),
so a healed, fed agent always has temperature as its largest need, and injury can be the largest
need on 15 % of a 500-step rollout only in a world hostile enough to fail the survival, cover and
hiding criteria. The set is likely unsatisfiable, and it is a reward-shaped measure besides. Drop
it, or make it behavioural or relative to today's world, and show one world can pass before using
it as a gate. Second, E2 as written (five quantiles of one pooled hit-size distribution) drops the
lethal tail it exists to model: measured on the first Wave-2 block, 61 % of hits outside cover are
rock scrapes of 1–5 points and only 3.9 % are 100 or more, so the 10–90 % quantiles run 1.7 to
66 and no hit kills below ~34 injury. Hit odds also differ by activity in the direction that
decides eat-versus-hide (eating steps: 0.056 per step, mean hit 11; moving: 0.027, mean 27;
resting: 0.0018, mean 72). Use fixed size bins with a ≥ 100 bin (or per source), per activity,
from both agents, and assert the mean-field hazard is reproduced.

**Moderate, to settle before the page is read:** "warming = at the ring" is never best on the
warm-bush map (the warm bush dominates the ring), so criterion 1's thresholds depend on the map
mix and the two bush-fire settings are judged against different effective thresholds — count
overlapping shares or apply criteria per map (M1, and the same for B-hide, M7); B-death's cause
shares will be dominated by start-doomed deaths near the 5 % gate — exclude early deaths and
report counts (M2); B-comb lost its 5-point floor while the tie margin alone moves today's gain
2.6 points against a 1.0-point grid floor — restore it (M3); the food axis has today at one end,
so an inverted U cannot be shown — add gross 8 and 10, and note that bites-per-item and
trip-to-food are one effective axis in the geometric model (M4); the E1/E2-off reproduction guards
the shared path only — add E2-collapsed-to-mean ≡ E2-off, mean bites per visit ≈ 12, and
both-agent agreement (M5); the hit-probability axis has no config knob — name the knobs and the
mapping, or call it diagnostic (M6); new modules need scripts-dependency-map rows in the same
commit (M8). Open: which agent's hazard numbers are used; true vs felt injury in the trained-agent
metrics; hazard is place-independent although eating steps are hit twice as often as moving steps.

**What flips the verdict:** criterion 2 replaced or dropped, and E2 respecified as above, in this
plan, before the sweep runs.

Reviewed by: plan-reviewer

### Revision 2a (2026-09-27) — answers to the plan-reviewer (`26190c89`), before any Revision-2 result

| Finding | Change |
|---|---|
| **C1** "largest drive component" is set by map geometry and the reward's weighting | **B-need is dropped as a criterion** (reported only, relative to today). Replaced by **B-drive — each need drives its own behaviour**: on the rollouts, (a) eating: share of steps eating when food energy < 60 vs ≥ 100; (b) warming: share of steps on a warm cell (ring or warm bush) when body temperature < −5 vs > 0; (c) hiding: share of steps in cover when injury ≥ 60 vs ≤ 20. Criterion 2 becomes: each ratio ≥ 2. Before it gates anything, it is computed on today's level 05 and reported; if today fails it for a reason of geometry rather than settings, that is stated and the criterion is reported, not gated. |
| **C2** five quantiles contain no lethal hit; hit odds differ by activity | **E2 respecified.** Per activity outside cover — eating, moving, resting — a per-step probability of a hit and a distribution over **fixed size bins** (0–5, 5–15, 15–30, 30–60, 60–100, ≥ 100 lethal), measured from the Wave-2 level-05 recordings for **each agent separately**. The ordinary agent's numbers are primary (the balance study concerns ordinary agents); the modulated agent's are reported as a check. Assertion before use: for each activity, probability × mean hit size reproduces the recordings' mean damage per step within 5 %. The planner's hazard therefore depends on what the agent is doing (eating steps are hit about twice as often as moving steps). |
| **M1/M7** the warm bush dominates the ring, so time shares depend on the map mix | **Criteria are applied per map; the primary verdict is on the map without a warm bush** (the common map, and the only one once bushes are kept off fire rings). The warm-bush map is reported. B-time uses overlapping shares: in cover, on a warm cell (ring or warm bush), eating. |
| **M2** start-doomed deaths dominate B-death | B-death excludes deaths in the first 20 steps; counts reported. |
| **M3** B-comb floor dropped | Criterion 6: combination gain above today's by at least max(5 points, twice the noise floor, the spread across tie margins 0 / 0.5 / 2). |
| **M4** the food axis cannot show a peak; trip and bites are one axis | Food energy per bite (gross) 10, 8, 6 (today), 5, 4, 3, so today sits inside the range. "Food search cost" = trip ÷ bites per item, one axis: trip 4 / 6 / 8 × bites 12 / 6, plotted as trip/bites. The 2-D grid uses gross 10 / 8 / 6 / 5 / 4 / 3. |
| **M5** reproduction check guards the shared path only | Added: E2 collapsed to its mean reproduces the E2-off result; E1 rollouts average ≈ 12 bites per food visit; both agents' hazard numbers compared. |
| **M6** hit-probability ×0.5/×2 has no config knob | Relabelled as a **diagnostic** ("if hazards were half / double"), not a setting to adopt; reported separately. |
| **M8** new modules need dependency-map rows | Added in the same commit as the code. |
| **L1** travel in the time shares | "Elsewhere" (open ground, travel) counts as an activity under the 70 % cap. |
| Open: true vs felt injury for trained-agent metrics | The metrics section will specify both, and cite the registry rows on the felt-pain leak and contemporaneous binning. |

## Feedback from plan-reviewer — confirming pass on Revision 2a (`e2568cef`)

**Verdict: SOUND WITH CONCERNS** (2026-09-27, before any Revision-2 result). Both Critical findings
of the Revision-2 review are resolved as written (C1: B-need dropped to report-only, replaced by the
behavioural B-drive; C2: E2 respecified with fixed size bins including a lethal ≥ 100 bin, per
activity, per agent, ordinary agent primary). M1–M8 and L1 are resolved in the plan. No new
Critical. One concern must be written into the plan **before any Revision-2 result is read**;
the others can be settled while the sweep runs.

**In plain language.** The reviewer computed the new B-drive ratios on today's level 05 with the
existing (Revision-1) planner, so the "is it satisfiable today?" question the plan defers to the
sweep is answered now. On the primary map (no warm bush) two of the three pass with margin —
eating when hungry vs fed 3.0, hiding when injured vs healed 3.3 (and criterion 5, B-hide among the
well-fed, 3.96) — but **warming when cold vs warm fails at 1.31** (share of steps on a warm cell
0.245 when body temperature < −5 vs 0.187 when > 0). The reason is the ideal policy's behaviour, not
a setting: it runs a thermostat, holding temperature between about −1.2 and +0.7 by shuttling
between the ring and elsewhere, so the warm-cell share is flat (0.15–0.42) across every temperature
band and steps below −5 are 50–66 % start transients. No choice of bands makes (b) discriminative,
and the cooling-rate and B4 axes tighten the thermostat rather than create a cold→warm gradient.
The plan's fallback ("if today fails for a reason of geometry rather than settings, report, not
gate") is honest in direction — it demotes a criterion, it does not promote a result — but it is not
decidable as written: "geometry rather than settings" has no test, and the decision would be taken
after the number is seen. The number is known now; decide now.

| # | Sev | Where | Concern | Fix |
|---|---|---|---|---|
| N1 | 🟡 (must be written before results are read) | Rev 2a, C1 row — B-drive (b) and its fallback | (b) fails today at 1.31 on the primary map for the thermostat reason above; the fallback fires post hoc with no decision rule. | Pre-register the disposition now: either drop (b) from the gate (report only; criterion 2 = (a) and (c), both satisfiable today), or replace it with the per-decision version — from the choice map, the share of start states where "warm up" is best at T ≤ −5 vs T ≥ 0 — and state that (a)/(c) pass today at 3.0 / 3.3. |
| N2 | 🟡 | Rev 2a, M5 row — the three added checks | (i) "E2 collapsed to its mean reproduces E2-off" cannot hold: E2-off has two activity classes (rest 0.12 / other 0.70), E2 has three whose means are eating ≈ 0.62, moving ≈ 0.73, resting ≈ 0.13. (ii) "≈ 12 bites per food visit" measures the agent's choice to leave when sated, not the geometric draw. (iii) "p × mean size reproduces mean damage within 5 %" is an identity when both come from the same recordings. | (i) collapse size to its mean **and** pool activities to rest / other, then require equality. (ii) check relocation events per bite ≈ 1/12. (iii) name the independent path: per-activity mean damage computed as Σ damage / steps from the recordings, versus p × Σ(bin share × bin mean) from the binned model — that tests the binning; and note the eating class is ~11 % below the Revision-1 pooled "other" value, so a 5 % check against 0.70 would fail by design. |
| N3 | 🟡 | Rev 2a, C2 row — E2 bins | The value the planner uses for a hit in each bin is unstated (midpoint vs measured bin mean); the ≥ 100 bin has no upper edge. | Use the measured bin mean, clip at 100; the choice feeds N2(iii). |
| N4 | 🟢 | Rev 2a, M1/M7 row × "bush on a fire ring" axis | With the primary verdict on the no-warm-bush map, the "never" setting is the same solve as the "allowed" primary map, so 12 of the 24 grid worlds are duplicates for the verdict; the axis only moves the secondary report. | Say so on the page, or skip the duplicate solves. |
| N5 | 🟢 | Rev 2a, M2 row — B-death | Whether the "≥ 5 % of starts die" gate is counted before or after the 20-step exclusion is unstated (today: 80 deaths, 77 in the first 20 steps, all starvation, 3 remain = 0.15 %). Also define the (a)–(c) ratios when a denominator is 0 (treat as pass). | One sentence each. |
| N6 | 🟢 | Rev 2a, M4 row — trip ÷ bites axis | trip 8 / bites 12 and trip 4 / bites 6 give the same value (0.67); under E1 their hazard per bite is also equal. | Name the pair as a built-in consistency check of "one effective axis". |

**Open assumptions.** ❓ The reviewer's numbers come from the Revision-1 planner (mean-field
hazard, E1/E2 off, food trip 4, 2,000 starts per map); E2 moves the injury side, not the thermostat,
and (c)/criterion 5 have margin, so the conclusion on (b) should survive E2 — verify on the first E2
baseline. ❓ Per-activity hit odds come from Wave-2 agents started at 0 °C, untrained under any swept
setting (stated in the plan; unverified). ❓ Finer-grid noise-floor solve with E2 on (7 outcomes ×
8 corners per transition) is untested for run time.

**Passes with nothing to report:** data-loss hazards (analysis outputs only); fallback defaults
(simulator constants); prior art (registry rows on the felt-pain leak and contemporaneous binning
are already cited by the plan; nothing new for `bug-curator`); doc framing (entry point is plain
language); version numbers (none invented).

**Cost of being wrong.** Minutes of sweep. The downstream cost of leaving N1 open is a criterion
demoted after the data, which makes the "balanced" set larger than the pre-registered one and sends
the ordinary-agent training to settings chosen on a softer rule.

Reviewed by: plan-reviewer
