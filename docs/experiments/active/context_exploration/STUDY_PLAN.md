# Hidden context and exploration — a study to choose larger, less observable level-05 worlds

## Question, in plain words

A modulator should help most when the right behaviour depends on something the agent cannot sense
directly and must infer or remember — "how dangerous is this episode?", "where did I last find food?".
In today's level 05 very little is hidden: the grid is 10 × 10 and smells carry 20 cells, so the agent
smells food, bushes and animals almost everywhere, and an ordinary network can simply react to what it
senses now. This study asks three things before any training (user, 2026-09-27):

1. **Do today's agents already adapt to hidden danger?** Each episode draws its own number of hunting
   predators (0–2) and hidden ambushers (2–12). If an agent behaves differently in safe and dangerous
   episodes at the same body state, it is adapting; if not, it is playing an average policy.
2. **How much is adapting worth?** If knowing the danger level barely changes the best behaviour, even a
   perfect agent has no reason to adapt, and wider danger variation would not separate the agents.
3. **Which larger, less observable worlds keep the needs balanced and make searching a real task?**
   Grid 15 × 15 or 20 × 20, a shorter smell range (not the local sampling pattern, which stays 5 cells),
   and fewer but richer food items — so the agent has to explore, and a find is worth the trip.

The simulator and the balance criteria of the internal-state interaction study (its `STUDY_PLAN.md`,
Revisions 2–2c, and `BALANCE_SETTINGS_INVENTORY.md`) are reused.

## Part 1 — do today's agents adapt to hidden danger? (existing recordings)

Data: the Wave-2 level-05 trajectory stores of both agents (ordinary and full modulator,
`results/trajectories_basicq2_w2/`), final checkpoint. Per episode, the danger context is read from the
recorded activation masks: number of active hunting predators (0 / 1 / 2) and number of ambushers (low
2–5 / high 9–12).

Measures, per agent, per context, at matched body state (bins of true injury and food energy):
share of steps in cover, share of steps eating, share of steps in the open away from cover, and steps
spent before the first bite. **Adaptation** = the difference in each share between the safest and the
most dangerous context, averaged over body-state bins that both contexts populate (at least 200 steps
each). Reported with bootstrap intervals over episodes.

Caveat stated in advance: dangerous episodes also injure the agent more, so matching on body state is
essential; and these agents started at 0 °C (they predate the random starting temperature).

## Part 2 — how much is adapting worth? (planner)

The balance sweep already solved today's world with predator hit odds ×0.5, ×1 and ×2. For each context,
compare (a) the policy solved for that context with (b) the policy solved for the average context,
followed in that context — survival share and mean survival steps from 2,000 starts, on the map without a
warm bush. **Value of knowing the danger** = (a) − (b), per context. Also the share of start states where
(a) and (b) choose differently. Pre-registered reading: if the value is under 2 survival points and the
choices differ in under 10 % of states in every context, danger variation is judged unlikely to separate
the agents in today's world.

## Part 3 — larger, less observable worlds (real resets + planner)

### Search time, measured on real resets
The planner cannot search; it needs a trip length. Trip lengths are measured on real environment resets
(300 per world) with a simple forager: from a random open cell, if any food smell is sensed (within the
smell range) it walks to the nearest food; otherwise it wanders at random (one uniform step per step,
not through rocks or fires) until a smell is sensed. **Search time** = steps until standing on food. The
same is measured for cover (bush smell) and warmth (the nearest cell warmer than 0 °C, found by feel —
thermoception is local, so warmth is searched without smell). Checked first on today's world: with range
20, search time must reproduce the measured median food trip (4 steps) within one step.

### Worlds measured
| Axis | Values |
|---|---|
| Grid | 10 × 10 (today), 15 × 15, 20 × 20 |
| Smell range (`sensory.sensor_radius`) | 20 (today), 8, 5, 3 |
| Food items | same count as today (1–4); same density as today (×2.25 at 15 × 15, ×4 at 20 × 20); "few and rich": 1–2 items |
| Bites per item (`max_consumption`) | 12 (today); 36 for "few and rich" — richer by lasting longer, not by bigger bites, because eating to 200 kills and big bites make over-eating likely |
| Fires, bushes, predators, ambushers, rocks | scaled to keep today's density (primary); same count as today (check) |

About 3 × 4 × 3 = 36 food settings per scaling, measured in minutes.

### Balance
Each world's measured search and trip times (food, cover, warmth) replace the planner's trips; bites per
item enter as food relocation (1 / bites). The planner is solved with single predator hits, as in the
balance study (hit odds per activity scaled with predator density). The balance criteria of the internal-
state study (Revisions 2a–2c: time split, each need drives its own behaviour, survival ≥ 80 % of today,
injury still drives hiding; deaths reported only, since the planner rarely starves) are applied unchanged.

### Candidate rule (pre-registered)
A world is a **candidate** if it (a) passes the balance criteria, (b) makes searching a real task: median
food search time at least twice today's, and (c) keeps the ideal agent's survival at least 80 % of today's.
Candidates are ranked by food search time. The shortest-smell-range 10 × 10 world that passes is always
reported next to the larger-grid candidates, to separate "less to sense" from "more space".

## Out of scope, flagged

- **Food that regrows in the same patch.** Today a used-up item reappears at a random cell, so remembering
  where food was has no value. A patch that regrows in place after a delay would reward memory. It needs
  new environment code, so it is a separate plan if this study's candidates look promising.
- Training: the candidates feed a later ordinary-agent balance search (with the balance metrics being
  implemented), then the modulator comparison.

## Limits stated in advance

The forager is a crude searcher (no memory), so search times are an upper bound for a trained agent in a
world with fixed food, and roughly right when food moves. The planner still knows its injury exactly and
sees predators as odds. Part 1 uses agents trained under today's world only.

## Deliverables

Result sections appended here; a short page, or a new section on the internal-state study page, after
verdict review.

## Feedback from plan-reviewer

**Verdict: NOT READY** (2026-09-27, before any part runs). Two Critical findings, seven Moderate,
four Low; full table with the measured evidence: [[plan_context_exploration]]
(`docs/reviews/plan_context_exploration.md`).

**In plain language.** Part 1 would measure a sensed signal and call it hidden: on a 10 × 10 grid
every cell is within the 20-cell smell radius, so a hunting predator is in the agent's smell field
on every step. The recordings already show the "adaptation" the plan would report — the ordinary
agent is in a bush 15 % / 35 % / 54 % of the time with 0 / 1 / 2 predators — and it is a reaction
to a present smell, not an inference about the episode. The ambusher count (no smell) is the only
hidden axis, and its effect is small (bush 24 % vs 28 %). Part 2's contexts (hazard ×0.5 / ×1 / ×2)
cover about a third of the real spread: measured from the same recordings, injury per exposed step
is 0.20 / 1.11 / 2.62 for 0 / 1 / 2 predators (×0.3 to ×4.1 of the average) and 10 % vs 97 % of
episodes end in death — so the value of knowing the danger is under-estimated and the pre-registered
negative reading could fire wrongly. Both are fixed in the plan text plus one measurement the
balance study's `measure_hazard_bins` already makes, conditioned on the per-episode predator count.

**Moderate, to settle before Part 3 runs:** hit odds are not scaled with the smell range, which is
what shortening it changes (M1); density scaling needs every hard-coded `[[1, 1], [10, 10]]`
placement box widened, the full entity lists restated, and a reset-level check for the silent
(0,0) placement fallback and for fires that cannot be packed (M2); the forager's validation at
range 20 is the Manhattan walk the study already measures and cannot fail on the search phase (M3);
the planner should take the mean or a per-step find probability, not the median, for heavy-tailed
searches (M4); criterion 3 on deaths stays gated (M5); scripts-dependency-map rows and a Files
section (M6); the "≥ 2 × today" floor needs a reason or a horizon-based value (M7).

**What flips the verdict:** C1 — ambusher count as the hidden axis, predator axis relabelled as
sensed threat (or matched on the recorded smell), time-in-episode in the matching, a pre-registered
effect size; C2 — contexts rebuilt from per-predator-count hazard bins, thresholds with units,
interval and tie margin. Both in this plan before Parts 1–2 run.

Reviewed by: plan-reviewer
