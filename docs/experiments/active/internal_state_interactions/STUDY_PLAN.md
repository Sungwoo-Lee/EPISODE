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
