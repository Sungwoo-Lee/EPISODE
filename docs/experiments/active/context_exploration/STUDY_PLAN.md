---
title: "Hidden context and exploration — choosing larger, less observable level-05 worlds"
topic: context_exploration
status: active
created: 2026-09-27
last_updated: 2026-09-27
wandb_tag: context_exploration
---

# Hidden context and exploration — a study to choose larger, less observable level-05 worlds

> **Status**: PLANNED, **Revision 1** (2026-09-27) — every plan-reviewer finding answered (table
> below) and Part 4 (real training) added at the user's request. Nothing has run; no result has been
> read. Awaiting the plan-reviewer's confirming pass.
> **Part 4 design (Revision 3, 2026-09-27)**: seven worlds chosen from the simulation at the user's request; the
> ordinary agent is trained on each and judged by the balance tests — see "Part 4 design" at the end. Not launched.
> **Related**: internal-state interaction study [plan](../internal_state_interactions/STUDY_PLAN.md) (
> Revisions 2–2c: the balance criteria) · [[BALANCE_SETTINGS_INVENTORY]] · balance metrics in training
> [[BALANCE_METRICS_TRAINING_LOGGING]] · level-05 body-interaction study [[LEVEL05_BODY_INTERACTIONS]]
> (the pilot recipe Part 4 copies) · plan review [[plan_context_exploration]]

## Question, in plain words

A modulator should help most when the right behaviour depends on something the agent cannot sense
directly and must infer or remember — "how dangerous is this episode?", "where did I last find food?".
In today's campfire world (level 05) very little is hidden: the grid is 10 × 10 and smells carry 20
cells, so the agent smells every food item, bush and hunting animal on every step, and an ordinary
network can simply react to what it senses now. The one thing it cannot smell is the number of
**ambushers** — hidden predators that sit still and have no smell — which changes from episode to
episode (2 to 12). This study asks four things (user, 2026-09-27):

1. **Do today's agents adapt to the one hidden danger?** In episodes with many ambushers, at the same
   body state and the same point in the episode, do they hide more or wander less than in episodes
   with few?
2. **How much would adapting be worth?** Using the ideal planner from the balance study: how much
   survival does an agent gain by knowing the episode's danger level, compared with one that plays the
   best average policy?
3. **Which larger, less observable worlds keep the needs balanced and make searching a real task?**
   Grid 15 × 15 or 20 × 20, a shorter smell range, and fewer but longer-lasting food items — measured
   on real environment resets and the planner, with no training.
4. **Do ordinary trained agents confirm it?** Train the ordinary (unmodulated) agent on the few worlds
   Part 3 picks, with the new balance measures logged, and judge them by the same balance criteria.
   The modulator comparison comes later, as its own design, on the worlds that pass.

## Revision 1 (2026-09-27): response to the plan review

The first draft was judged not ready (full report [[plan_context_exploration]], summary at the end of
this doc). Its two blocking problems: Part 1 would have called a **smelled** danger (hunting predators,
always within smell range on a 10 × 10 grid) a hidden one; and Part 2's danger levels (hit odds ×0.5 to
×2) covered about a third of the real spread (×0.3 to ×4.1). This revision fixes both and every other
finding:

| Finding | Change | Where |
|---|---|---|
| 🔴 C1 predator count is sensed, not hidden | Ambusher count is the **primary hidden axis**. Predator count is reported only as **sensed threat**, matched on the recorded animal-smell channels. Time in episode added to the matching. A **minimum gap of 5 percentage points** (cover share) is pre-registered, not significance alone | Part 1 |
| 🔴 C2 danger levels too narrow, thresholds undecidable | Contexts rebuilt from **per-predator-count hit bins** measured with the balance study's own `measure_hazard_bins`, conditioned on the episode's predator count; "average context" = the pooled bins. Thresholds given units (survival share in percentage points), ≥ 3 rollout seeds × 10,000 starts with intervals, tie margin 0.5 | Part 2 |
| 🟡 M1 hit odds measured with full warning | Every world solved at hazard ×1 **and** ×2; a candidate must pass at both | Part 3, Balance |
| 🟡 M2 density scaling has no config plan | Every placement/area key listed; rounding rule; fire-packing rule; three reset-level assertions; generated configs validated by `env-config-reviewer` | Part 3, Worlds |
| 🟡 M3 circular forager check | Validated against the solved random-walk hitting time on an empty grid, and monotonicity in smell range; the range-20 check kept only as a sanity check | Part 3, Search time |
| 🟡 M4 median under-weights long searches | Planner takes a per-step find probability (1 / mean); median, mean, 90th percentile reported | Part 3 |
| 🟡 M5 deaths criterion demoted | Criterion 3 stays gated exactly as inherited; starvation share reported | Part 3, Part 4 |
| 🟡 M6 no Files section | Files section + scripts-dependency-map rows in the same commit as the scripts | Files |
| 🟡 M7 "≥ 2 × today" arbitrary | Replaced by a horizon-based floor: mean food search ≥ 20 steps, the agent's effective planning horizon | Part 3, Candidate rule |
| 🟢 L1 warmth detection undefined | "Felt" = a thermal-stencil cell ≥ 5 °C above ambient; 2 and 10 °C as sensitivity | Part 3 |
| 🟢 L2 first bite unmatched | Matched on starting food energy | Part 1 |
| 🟢 L3 forager avoids non-blocking rocks/fires | Forager crosses them like the agent does; exposure steps counted | Part 3 |
| 🟢 L4 observation width | Recorded (grid-independent) | Part 3 |
| ❓ forager may run forever | Step cap 2,000; capped share reported; > 1 % capped ⇒ world not a candidate | Part 3 |
| ❓ shared `seed_base` | Checked from the store manifests before Part 1 runs; if shared, agent comparison is paired per episode | Part 1 |
| ❓ 20 × 20 tried before? | Checked (one archived config) before Part 3 runs; outcome recorded here | Part 3 |

## Part 1 — do today's agents adapt to the hidden danger? (existing recordings)

**Data.** Wave-2 level-05 trajectory stores of both agents (ordinary and full modulator,
`results/trajectories_basicq2_w2/`), final checkpoint. Before running, the two stores' manifests are
checked for a shared `seed_base`; if shared (expected: the Wave-2 collector used 1,000,000 for every
run), each episode is paired across agents and the agent difference is computed per pair.

**Hidden axis (primary).** Ambusher count per episode, read from the allocated-resource record
filtered by the manifest's resource type (`res_allocated` × `res_type == 1`; not `res_active`, per the
Known Bugs row fixed 2026-09-26). Bands: **low 2–5** vs **high 9–12**; 6–8 excluded.

**Sensed-threat axis (secondary, never called hidden).** Hunting-predator count 0 / 1 / 2. With smell
range 20 on a 10 × 10 grid every predator is inside the smell field on every step, so a difference
here is a reaction to a present smell. It is reported matched additionally on the recorded animal
smell (the five sampled cells' animal channel in the true observation, summed, in quintiles), so the
report separates "reacts to how strong the smell is now" from anything left over.

**Matching.** Steps are compared within cells of: true injury (0–20, 20–40, 40–60, 60–80, 80–100),
food energy (0–50, 50–100, 100–150, 150–200), and **time in episode** (steps 1–50, 51–150, 151–300,
> 300). A cell counts if both contexts have ≥ 200 steps in it; gaps are averaged over counted cells
weighted by their pooled step count. Sensitivity: time-in-episode replaced by steps since last hit
(0–10, 11–50, > 50).

**Measures.** Share of steps in cover (primary), eating, in the open away from cover. Steps before
the first bite: per episode, matched on starting food energy (bins of 40).

**Pre-registered reading (cover share, high minus low ambushers, per agent).** 95 % bootstrap
interval over episodes (1,000 resamples).
- **Adapts:** gap ≥ 5 percentage points **and** the interval excludes 0.
- **Does not adapt:** the interval's upper bound < 5 points.
- **Undecided:** otherwise.
The same rule, reported not gated, for eating and open-away-from-cover shares. The raw (unmatched)
gap, 24 % vs 28 % according to the review, is quoted for context only.

**Caveats.** Dangerous episodes injure more, so matching is essential; these agents started every
episode at 0 °C (they predate the random starting temperature).

## Part 2 — how much is adapting worth? (planner)

**Contexts from the recordings.** Hit bins (probability of a hit per exposed step and the hit-size
distribution, per activity outside cover) are measured separately for episodes with **0, 1 and 2
hunting predators**, with the balance study's `measure_hazard_bins` logic, conditioned on the
episode's `animal_active` count, for both agents (context prior 1/3 each; block-0 counts 1,730 /
1,684 / 1,586). The review's figures (injury per exposed step 0.20 / 1.11 / 2.62) are the check the
new bins must reproduce within 5 %. Secondary: the same crossed with the ambusher band (6 contexts).

**Average context** = the pooled bins the balance study already uses: the best memoryless policy
under the prior, i.e. the right "no inference" baseline.

**Value of knowing the danger** = survival of (a) the policy solved for a context minus (b) the
average-context policy, both followed in that context. Units: **survival share in percentage points**
(share of starts alive at the planner's 500-step rollout end); mean survival steps reported beside
it. Rollouts: 3 seeds × 10,000 starts, on the map without a warm bush; 95 % interval over seeds and
starts. **Choice difference** = share of start states where (a)'s best choice beats (b)'s choice by
more than the tie margin **0.5** (planner value units, as in the balance study), with 0 and 2 as
sensitivity.

**Pre-registered reading.**
- **Worth knowing:** value ≥ 2 points with the interval excluding 0 in at least one context, or
  choice difference ≥ 10 % in at least one context.
- **Not worth knowing in today's world:** in every context the interval's upper bound < 2 points
  **and** choice difference < 10 %.
- **Undecided:** otherwise.

## Part 3 — larger, less observable worlds (real resets + planner)

### What is measured on real resets

The planner cannot search; it needs search times. They are measured on 300 real resets per world
with a simple forager, from the reset's own agent start (random start is on in level 05):

- **Food:** if any of the five sampled smell cells is within smell range of a food item, walk
  straight to the nearest food; otherwise take one uniform random step. Rocks and fires are crossed
  as the agent can cross them (non-blocking in level 05); steps on rocks are counted as exposure.
- **Cover:** the same with bush smell.
- **Warmth (by feel):** thermoception is local (a 5-cell relative stencil), so no smell. Detection =
  any stencil cell ≥ **5 °C** above ambient (a fire is then felt 2–3 cells away); then climb the
  gradient to a cell above 0 °C. Sensitivity at 2 and 10 °C.
- **Step cap 2,000.** The share of capped resets is reported; a world with > 1 % capped food
  searches is "search unmeasured" and not a candidate.
- Reported per world: median, **mean** and 90th percentile, and exposure steps.

Recorded (review L4): the observation width does not depend on grid size; smell falls as 1/distance
with a hard cut-off at the smell range and no amplitude floor, so "a smell is sensed" means "one of
the five sampled cells lies within range of the item".

**Forager validation (can fail).** (i) On an empty grid (10, 15, 20) with one fixed target and smell
range r ∈ {3, 5, 8}, the forager's mean search time must match the hitting time of its own walk,
solved exactly as a small Markov chain, within 10 %. (ii) In every measured world, mean and median
food search must not increase as the smell range grows (checked with the 95 % interval). (iii) Sanity
only, not diagnostic: today's world at range 20 reproduces the measured 4-step median food trip.

### Worlds measured

| Axis | Values |
|---|---|
| Grid | 10 × 10 (today), 15 × 15, 20 × 20 |
| Smell range (`sensory.sensor_radius`) | 20 (today), 8, 5, 3 (the sampled pattern stays 5 cells) |
| Food items | same count as today (1–4); same density as today; "few and rich" 1–2 items |
| Bites per item (`max_consumption`) | 12 (today); 36 for "few and rich" (richer by lasting longer: big bites make over-eating to 200, which kills, likely) |
| Fires, bushes, predators, rabbits, ambushers, rocks | density as today (primary); count as today (check) |

About 36 food settings per scaling. The earlier archived 20 × 20 config is checked before Part 3
runs, to see whether a larger grid was tried and rejected; the outcome is written here.

**Density scaling — every key that must change** (factor f = 2.25 at 15 × 15, 4 at 20 × 20). All
placement boxes in level 05 are hard-coded 1-based `[[1, 1], [10, 10]]` and are widened to
`[[1, 1], [G, G]]`:
- resources: `food.spawn_area`, `hiding_predator.spawn_area` (ambushers);
- entities: predator and rabbit `spawn_area` **and** `patrol_area`;
- obstacles: `rock.area`, `bush.area`, `campfire.area`;
- `location_areas` grass `area`;
- the grid size itself.

Lists merge by replacement, so every generated world restates the full `resources`, `entities` and
`obstacles` lists, copied from level 05 with only the keys above changed. Campfire `edge_margin: 2`
is kept (it insets the widened box at load). `placement.mode` stays `per_entity` (the per-type mode is
refused with fire separation). **Counts** are scaled as `low′ = max(1, round(f · low))`,
`high′ = round(f · high)` (round half up), except for counts whose today's low is 0 (predators, rabbits),
where `low′ = 0`. Example 20 × 20: food 1–4 → 4–16, fires 1–3 → 4–12, ambushers 2–12 → 8–48.
**Fire packing:** fire separation 4 is enforced during placement, and an unpackable fire is silently
parked at cell (0,0) (Known Bugs). If any of the 300 resets places fewer fires than drawn, the world's
fire `high′` is lowered to the largest value that places all fires on 300 of 300 resets, and the world
is labelled "fires capped at k".

**Reset-level assertions (per world, every reset; failure stops that world):**
1. entity and resource positions span the whole grid (over 300 resets, occupied rows and columns reach
   within 1 cell of every edge the inset allows);
2. no active entity or resource sits at (0,0);
3. number of fires placed = number drawn (after any cap above).

The measurement worlds are generated as throw-away YAMLs under `results/analysis/context_exploration/worlds/`
and loaded through the trainer's own loader. Only Part 4's chosen worlds become repo configs.

### Balance (planner)

Each world's measured search times replace the planner's trips, as a **per-step find probability**
(1 / mean search time) through the planner's stochastic branch; bites per item enter as food
relocation (1 / bites). Single predator hits, hit odds scaled with predator density, as in the balance
study. **Each world is solved at hazard ×1 and ×2**: at short smell ranges the agent loses the warning
the ×1 odds were measured with, so ×2 brackets it.

Criteria: those of the internal-state study (Revisions 2a–2b), unchanged — (1) time split; (2) each need
drives its own behaviour (eating ratio, hiding ratio, per-decision warming); (3) no single cause
> 60 % of deaths, **gated** whenever ≥ 5 % of starts die after step 20; (4) survival ≥ 80 % of today's;
(5) injury still drives hiding among well-fed states. Criterion 6 (combination gain) is reported, not
required. Starvation share reported per world.

### Candidate rule (pre-registered)

A world is a **candidate** if, at **both** hazard ×1 and ×2: (a) it passes criteria 1–5, and (b)
searching is a real task: **mean food search ≥ 20 steps**. Why 20: the agent discounts at 0.95, an
effective planning horizon of 1 / (1 − 0.95) = 20 steps; food farther than that in expectation cannot
be reached by reacting to a value gradient and needs search. (Today's mean is about 4.) Exposure
(mean search × hazard per moving step, against the injury one bush step heals) is reported beside it.
Candidates are ranked by mean food search. The shortest-range 10 × 10 world that passes (a) is always
reported next to them — to separate "less to sense" from "more space" — whether or not it meets (b).

## Part 4 — real training of the ordinary agent (added in Revision 1; user, 2026-09-27)

**What runs.** The ordinary agent (the grid's unmodulated `t1none` agent, the same agent config as the
Wave-2 level-05 runs and the level-05 body-interaction pilots) on:
- up to **6 Part-3 candidates**: the top 3 by mean food search at each of 15 × 15 and 20 × 20; if one
  size has fewer than 3, the other size fills the free places;
- the **short-smell-range 10 × 10 world** named in the candidate rule;
- **today's level 05** as the reference.

**Cap: at most 8 worlds.** If Part 3 finds no candidate, Part 4 does not run and the study returns to
this plan.

**Seeds.** One seed (42) per candidate world, as in the level-05 pilots: this is a screening step, not a
confirmation, and the criteria are coarse (ratios ≥ 2, shares ≥ 10 %). The **reference runs with two
seeds (42, 43)**: nobody has yet measured how much the new balance measures vary between seeds, and
the reference gap sets the noise scale. A world whose value on any criterion lies within that gap of
its threshold is **borderline** and gets a second seed (43) before it is passed downstream. The
modulator comparison that follows (later, separate design) uses ≥ 3 seeds per agent.

**Budget.** 2,000,000 episodes per run, the level-05 pilot budget (at 10 × 10 about 2 h on an RTX 3090;
larger grids with longer episodes plausibly 2–6 h). At most 9 runs (+ borderline re-runs). Read-out
from the last 10 % of training (episodes 1.8–2.0 M), weighted by each logged row's episode count, as in
the pilots. **Still-learning rule:** if survival in 1.8–2.0 M exceeds survival in 1.6–1.8 M by > 5 %, the
world is "still learning" and its verdict is undecided; extending it needs the user's approval.

**Balance measures on.** Every run has the balance-metrics switch on (`logging.episode.balance_metrics:
true`) and the early-death cut-off key at 20 steps (both required keys from the balance-metrics plan,
being implemented now). Precondition: that implementation is merged and verified before any Part-4
config is written. The worlds keep level 05's body settings (maximum food energy 200, maximum injury
100), so the logged calibration record must match level 05's; a mismatch stops the run.

**Judged by** the trained-agent criteria of the internal-state study (Revisions 2a–2c): (1) time split;
(2) eating ratio ≥ 2 and hiding ratio ≥ 2 (true injury decides, felt injury reported) — **warming ratio
logged, not pass/fail**; (3) causes of death among deaths after step 20, gated when ≥ 5 % of episodes
die late; (4) survival ≥ 80 % of the reference; (5) injury still drives hiding among well-fed states.
Before configs are written, the merged implementation's key list is checked against criteria 1–5; a
criterion with no logged key is marked "not measured in training" here, before launch. A world passing
1–5 is **trained-balanced** and goes forward to the modulator comparison.

**Configs are generated only after Part 3 picks the candidates**, outside `basic/` (like the level-05
body-interaction worlds): `configs/environment/experiment/context_exploration/<slug>.yaml`, each extending
level 05 and restating the full lists (Part 3, density scaling). `env-config-reviewer` validates every
file; the critical-settings registry gets a change-log entry if any registered setting (smell range is
one) differs from its canonical value in a new config.

**Names (fixed now).** Tag = WandB name = `rppo_ctxexp_<slug>_t1none_s<seed>`; group
`context_exploration`; job type `pilot`. Slug `g<grid>r<range>f<food>b<bites>`, e.g. `g20r3f1to2b36`;
the reference is `lvl05ref`. The Launch Manifest (rows, nodes, GPUs) is added to this doc when the
configs are generated.

**When.** Not before the 32 running level-05 runs finish (about the night of 2026-09-27 to the
morning of 2026-09-28), after Part 3's verdict, and after the pre-launch PI consultation. Mid-tier
cards (RTX 3090), packed node by node.

**Later step, not part of this plan:** the modulator comparison on the trained-balanced worlds.

## Out of scope, flagged

- **Food that regrows in the same patch.** Today a used-up item reappears at a random cell, so remembering
  where food was has no value. A patch that regrows in place would reward memory; it needs new
  environment code — a separate plan if the candidates look promising.

## Limits stated in advance

The forager has no memory, so search times are an upper bound for a trained agent when food stays put
and roughly right when food moves. The planner still knows its injury exactly and sees predators as odds;
the ×2 hazard bracket, not a model of warning, covers lost warning at short range. Parts 1–2 use agents
trained in today's world only. Part 4 uses one seed per candidate (screening).

## Files

- Scripts in a new folder `scripts/analysis/studies/context_exploration/` (one level of nesting under
  `studies/`, same depth as `internal_state_interactions/`; importing that folder's `measure_world`,
  `planner` and `balance_rule` rather than editing them):
  `hidden_context.py` (Part 1), `context_hazard.py` + `value_of_knowing.py` (Part 2),
  `make_worlds.py` + `forager.py` (with the hitting-time check) + `balance_worlds.py` (Part 3),
  `make_training_configs.py` (Part 4, run only after the Part-3 verdict).
- Outputs under `results/analysis/context_exploration/` (throw-away measurement worlds in `worlds/`).
- `docs/environment/SCRIPTS_DEPENDENCY_MAP.md`: a row for the new folder, in the **same commit** as the
  scripts.
- Part-4 configs: `configs/environment/experiment/context_exploration/` (after Part 3).

## Deliverables

Result sections appended here, then plan-reviewer on the verdict before the PI; a short page, or a new
section on the internal-state study page.

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

### Confirming pass on Revision 1 (2026-09-27)

**Verdict: SOUND WITH CONCERNS.** Every Revision-0 finding (C1, C2, M1–M7, L1–L4, the four open
assumptions) is resolved as written; Part 4 adds no Critical problem. No review file is written
(none is Critical). Verified along the way: both Wave-2 stores carry `seed_base` 1,000,000
(`_manifest.json` in each), so Part 1's paired comparison is available; the ordinary agent's
discount is 0.95 (`nmngaenorm_t1none.yaml:37`), so the 20-step horizon is real; the ambusher /
food slot arrays are allocated at `count_high` per entry (`config_loader.py:1970-1977`), so
8–48 ambushers hit no static cap; `sensory.sensor_radius` is a registered critical setting.

**Search floor (mean food search ≥ 20) — decidable, not trivial.** The forager detects an item
when any of its five diamond cells is within `sensor_radius` (Euclidean), so the detection region
is roughly a disc of radius range + 1: ≈ 50 cells at range 3, ≈ 113 at range 5, ≈ 254 at range 8.
Rough 2D hitting-time estimate (L²/π · ln(L / r_eff)): a 20 × 20 world with 1–2 items sits near
100–200 steps at range 3 and ≈ 100 at range 8; 15 × 15 with 1–2 items near 40–95; density-scaled
worlds (4–16 items at 20 × 20) cover 40–90 % of cells and sit near today's 4–15. So the floor
separates food-count regimes rather than fine-tuning within one, and the ranking will simply
order "fewest items, shortest range" first. Two things to fix so it stays decidable:
- 🟡 Say whether the point estimate or the 95 % interval's lower bound must clear 20. With 300
  resets and a geometric-like tail (SD ≈ mean), the SE is ≈ mean / 17, so a world at 22 is inside
  its own interval; 1,000 resets are cheap and halve it.
- 🟡 The sweep has no food count between "1–2" and "same density" (4–16 at 20 × 20). If the
  low-count worlds all starve (metabolic cost 1 / step, start energy uniform 0–200) and the
  dense ones all fail the floor, Part 3 returns nothing. Add one intermediate rung (e.g. 2–4 and
  2–6 at 20 × 20; 2–3 at 15 × 15) so the region around 20–60 steps is populated.

**Part 4 — Moderate, to settle before configs are written.**
- 🟡 Budget confound. The budget is in episodes, and episodes on a larger grid have a different
  step length, so 2 M episodes gives each world a different number of gradient updates. Record
  total environment steps at read-out and report survival against both; or state that the
  screening tolerates it. Criterion 4 (survival ≥ 80 % of the reference) is the one it touches.
- 🟡 Reference noise is already measured. The body-interaction base pilots P0a/b/c (same world,
  same agent, seeds 42/43/44, 2 M episodes) read 228.3 / 225.8 / 228.6 survival steps in
  1.8–2.0 M ([[LEVEL05_BODY_INTERACTIONS]] §6): a 3-seed spread of 2.8 steps (1.2 %). Use that as
  the survival noise scale; the two new reference seeds are still needed, but only for the
  `Bal_*` keys' noise. A single two-seed gap can be near zero by chance and then nothing is
  borderline.
- 🟢 "The early-death cut-off key at 20 steps" is not a config key: the balance-metrics plan fixes
  the 20-step cut-off as a module constant (its §A5, "Constants, not config"). The only required
  key is `logging.episode.balance_metrics`. Correct the sentence so `make_training_configs.py`
  does not write a key nothing reads.
- 🟢 Still-learning rule "> 5 %": say relative or percentage points. (The P0 pilots rose 1.3 %
  over the last two blocks, so the reference itself will not trip it.)
- ❓ Verifying the budget of a finished run: the saved `models/config.yaml` carries a stale second
  copy of the seed and episode budget that always reads 42 / 100 (Known Bugs, 2026-09-04). Read
  the budget from the WandB episode counter or the launch log, not the saved config.
- ❓ Part 4 is gated on the balance-metrics merge; the branch exists (`balance_metrics` worktree)
  and nothing under `src/` carries it yet. The gate is stated; the date is outside this plan.

**Passes with nothing to report.** Data loss (analysis outputs and new configs only). Fallback
defaults (no new code paths; configs to `env-config-reviewer`). Survival, not reward. Version
numbers. Doc framing. Maintenance contracts (map row and critical-settings entry both named).
Prior art: the three registry rows already cited (res_type filter, (0,0) parking, stale saved
budget) are the only relevant ones; nothing new for `bug-curator`.

**Cost of being wrong.** Part 4 wrong in the way suspected → one candidate passed or failed on a
2-seed noise estimate or a step-count confound, costing a 2–6 h re-run per world; Part 3's sweep
empty → a day of measurement and a redesign of the food axis. No unrecoverable loss.

Reviewed by: plan-reviewer

## Revision 1a (2026-09-27) — answers to the confirming pass (`3cab2d71`), before anything runs

- **Search floor rule:** the point estimate of the mean food search time over **1,000 resets** per world must be
  ≥ 20 steps (1,000 resets give a standard error of about mean/30); the 95 % interval is reported.
- **Food axis gains a middle rung:** 2–4 items at 15 × 15 and 2–6 at 20 × 20, between "few and rich" and
  "same density", so Part 3 cannot fall between two failing extremes.
- **Part 4 budget:** each run's environment steps at the read-out window are recorded from WandB / the log (not
  the saved config, whose budget copy can be stale — Known Bugs 2026-09-04); survival is reported per episode
  and per 1,000 environment steps, and criterion 4 is judged on survival steps per episode against the
  reference, with the step-count difference stated.
- **Noise scale:** survival noise for the reference world is taken from pilots P0a–P0c (228.3 / 225.8 / 228.6
  steps, same world, agent and budget); the two reference seeds of Part 4 exist for the new balance numbers'
  noise.
- **Early-death cut-off:** a required config key, by the user's decision on the balance-metrics plan
  (2026-09-27), superseding that plan's module constant; level-05 value 20.
- **Still learning:** "> 5 %" means a relative rise of more than 5 % in survival steps over the last fifth
  of training.
- **Status: approved by the user ("proceed", 2026-09-27); Parts 1–3 may run.**

## Results (raw) — Parts 1–3 (2026-09-27)

Numbers only; no reading is written here. Outputs: `results/analysis/context_exploration/` (`part1_hidden_context.json`, `part2_context_hazard.json`, `part2_value_of_knowing.json`, `part3_search_times.json`, `part3_balance_worlds.json`, `part3_balance_worlds_manifest.json`, `worlds/`). Scripts: `scripts/analysis/studies/context_exploration/`.

### Part 1 — hidden axis (ambushers high 9–12 minus low 2–5), matched on injury × food energy × time in episode

Stores: 200 of 200 blocks per agent, 1,000,000 episodes each; `seed_base` 1,000,000 in both → paired. Episodes: low 363,890, high 363,737, excluded 6–8 272,373. Cells counted 65 of 80. Gaps in percentage points, 95 % bootstrap interval (1,000 resamples).

| Agent | Measure | Gap, matched (time) | Rule | Gap, matched (steps since last hit) | Raw low → high (%) |
|---|---|---|---|---|---|
| ordinary | cover | +0.63 [+0.57, +0.70] | does not adapt | +0.72 [+0.65, +0.79] | 25.0 → 27.8 |
| ordinary | eat | -0.08 [-0.10, -0.06] | does not adapt | -0.59 [-0.61, -0.56] | 16.6 → 15.7 |
| ordinary | open | -0.58 [-0.67, -0.48] | does not adapt | -0.68 [-0.78, -0.57] | 53.4 → 51.1 |
| modulator | cover | +0.53 [+0.47, +0.59] | does not adapt | +0.43 [+0.36, +0.50] | 23.4 → 26.0 |
| modulator | eat | -0.06 [-0.08, -0.04] | does not adapt | -0.53 [-0.55, -0.50] | 16.7 → 15.8 |
| modulator | open | -0.45 [-0.54, -0.36] | does not adapt | -0.37 [-0.47, -0.28] | 55.4 → 53.3 |

| Agent | Steps before first bite, high − low (matched on starting food energy) | No-bite share low / high |
|---|---|---|
| ordinary | +1.65 [+1.54, +1.76] steps | 0.222 / 0.247 |
| modulator | +1.68 [+1.57, +1.80] steps | 0.221 / 0.244 |

Paired agent difference (modulator gap − ordinary gap): cover -0.11 [-0.16, -0.05], eat +0.02 [+0.00, +0.04], open +0.13 [+0.05, +0.20].

**Sensed-threat axis (hunting predators), cover-share gap in points** — matched on injury × food × time, and additionally on animal-smell quintile (edges 0.00, 1.33, 2.39, 4.04):

| Agent | Contrast | Cover, matched | Cover, + smell | Eat, + smell | Open, + smell | Raw cover % (0/1/2) |
|---|---|---|---|---|---|---|
| ordinary | 1 − 0 | +12.47 [+12.40, +12.53] | +9.00 [+8.94, +9.06] | +1.10 [+1.08, +1.13] | -9.67 [-9.76, -9.57] | 15.0 / 35.1 / 54.4 |
| ordinary | 2 − 0 | +23.40 [+23.29, +23.51] | +13.46 [+13.32, +13.62] | +6.38 [+6.20, +6.57] | -13.23 [-13.50, -12.97] | 15.0 / 35.1 / 54.4 |
| ordinary | 2 − 1 | +11.83 [+11.73, +11.93] | +5.98 [+5.89, +6.08] | +1.32 [+1.27, +1.38] | -5.18 [-5.30, -5.07] | 15.0 / 35.1 / 54.4 |
| modulator | 1 − 0 | +12.05 [+11.99, +12.11] | +8.61 [+8.55, +8.66] | +1.16 [+1.13, +1.18] | -8.94 [-9.03, -8.84] | 13.8 / 32.9 / 52.1 |
| modulator | 2 − 0 | +23.18 [+23.08, +23.29] | +13.69 [+13.53, +13.85] | +6.50 [+6.31, +6.70] | -12.87 [-13.15, -12.60] | 13.8 / 32.9 / 52.1 |
| modulator | 2 − 1 | +11.98 [+11.88, +12.09] | +6.61 [+6.51, +6.71] | +1.38 [+1.32, +1.44] | -5.56 [-5.69, -5.43] | 13.8 / 32.9 / 52.1 |

### Part 2 — contexts and value of knowing the danger

Check against the review's injury per exposed step (ordinary agent, 200 blocks): 0 predators 0.201 vs 0.20 (0.3%), 1: 1.102 vs 1.11 (0.7%), 2: 2.591 vs 2.62 (1.1%) — pass within 5 %. Pooled (average-context) injury per exposed step: ordinary 0.635.

Planner: balance-study baseline world (E1 + E2 bins, discount 0.95), no warm bush; 3 seeds × 10,000 starts per policy; value in survival-share points (95 % interval); choice difference = share of start states where the context policy's best category beats the average policy's by > margin.

| Agent | Context | Injury / exposed step | Survival: context policy / average policy | Mean steps (ctx / avg) | Value (points) | Choice diff @0.5 (0 / 2) |
|---|---|---|---|---|---|---|
| ordinary | pred0 | 0.20 | 0.965 / 0.966 | 483 / 483 | -0.10 [-0.39, +0.19] | 0.057 (0.105 / 0.013) |
| ordinary | pred0_amblow | 0.12 | 0.968 / 0.968 | 484 / 484 | -0.00 [-0.29, +0.28] | 0.074 (0.124 / 0.016) |
| ordinary | pred0_ambhigh | 0.28 | 0.963 / 0.963 | 482 / 482 | +0.04 [-0.26, +0.34] | 0.042 (0.086 / 0.011) |
| ordinary | pred1 | 1.10 | 0.402 / 0.355 | 323 / 308 | +4.72 [+3.94, +5.50] | 0.056 (0.086 / 0.011) |
| ordinary | pred1_amblow | 0.98 | 0.413 / 0.370 | 328 / 313 | +4.34 [+3.56, +5.12] | 0.047 (0.077 / 0.007) |
| ordinary | pred1_ambhigh | 1.24 | 0.382 / 0.342 | 317 / 302 | +4.00 [+3.23, +4.77] | 0.069 (0.098 / 0.022) |
| ordinary | pred2 | 2.59 | 0.111 / 0.064 | 202 / 168 | +4.70 [+4.25, +5.15] | 0.187 (0.203 / 0.136) |
| ordinary | pred2_amblow | 2.41 | 0.118 / 0.074 | 207 / 175 | +4.48 [+4.01, +4.95] | 0.185 (0.202 / 0.136) |
| ordinary | pred2_ambhigh | 2.78 | 0.099 / 0.058 | 195 / 162 | +4.14 [+3.71, +4.57] | 0.192 (0.207 / 0.144) |
| modulator | pred0 | 0.19 | 0.967 / 0.966 | 483 / 483 | +0.01 [-0.28, +0.29] | 0.055 (0.103 / 0.011) |
| modulator | pred0_amblow | 0.12 | 0.967 / 0.968 | 484 / 484 | -0.04 [-0.32, +0.24] | 0.071 (0.121 / 0.014) |
| modulator | pred0_ambhigh | 0.27 | 0.965 / 0.964 | 483 / 482 | +0.07 [-0.23, +0.36] | 0.041 (0.086 / 0.010) |
| modulator | pred1 | 1.09 | 0.415 / 0.372 | 328 / 313 | +4.32 [+3.54, +5.10] | 0.057 (0.084 / 0.012) |
| modulator | pred1_amblow | 0.97 | 0.434 / 0.382 | 335 / 318 | +5.12 [+4.33, +5.91] | 0.045 (0.073 / 0.010) |
| modulator | pred1_ambhigh | 1.23 | 0.399 / 0.355 | 321 / 306 | +4.35 [+3.58, +5.13] | 0.066 (0.094 / 0.020) |
| modulator | pred2 | 2.63 | 0.120 / 0.069 | 208 / 172 | +5.11 [+4.64, +5.58] | 0.182 (0.201 / 0.132) |
| modulator | pred2_amblow | 2.45 | 0.129 / 0.078 | 212 / 179 | +5.04 [+4.55, +5.53] | 0.175 (0.194 / 0.125) |
| modulator | pred2_ambhigh | 2.82 | 0.110 / 0.061 | 202 / 168 | +4.90 [+4.46, +5.35] | 0.191 (0.210 / 0.143) |

Pre-registered rule output (primary contexts pred0/1/2): ordinary — **worth knowing**; modulator — **worth knowing**. Average-context policy in the average world: ordinary survival 0.587, modulator 0.596.

### Part 3 — worlds, search times, balance

- Worlds generated: 18 reset layouts × 4 smell ranges = 72 worlds; 1,000 real resets per layout; every layout passed the span, (0,0) and fire-placement assertions; no fire count needed capping; every range's YAML differs from its range-20 world only in `sensor_radius`. Observation width 58 in every world.
- Forager validation (i) hitting time vs exact Markov chain: pass, max relative error 0.009 (18 grid/target/range cases). (ii) monotone in smell range: pass, 0 violations. (iii) today's world at range 20: forager median food search 4 (mean 4.70) vs measured median trip 4.
- Planner search option check: find probability 1 vs one-step trip — V and Q tables identical (max diff 0.0), rollout survival 0.6428 vs 0.6499 (1.05 SE).
- Archived 20 × 20 config check: one archived 20 × 20 world exists, `configs/environment/experiment/archive/2X2_area.yaml` (four-quadrant layout, fixed start, food regrowing after 100 steps, no thermal); no training result or rejection is recorded for it in `docs/`.
- Today's world as measured here (10 × 10, range 20, food 1–4): survival 0.371 at hazard ×1, 0.186 at ×2 (criterion-4 reference = ×1).

Primary scaling (other things at today's density, `od`). Search means in steps (1,000 resets); criteria string = pass(1)/fail(0) for criteria 1 time, 2 drive, 3 death, 4 survival, 5 hide.

| World | Food search mean [95 %] | median / p90 | capped | Cover | Warmth (5 °C) | Survival ×1 | Crit ×1 | Survival ×2 | Crit ×2 | Starvation share of late deaths ×1 |
|---|---|---|---|---|---|---|---|---|---|---|
| g10r20f1to4b12_od | 4.7 [4.5, 4.9] | 4 / 9 | 0.000 | 2.5 | 21.0 | 0.371 | 10111 | 0.186 | 10001 | 0.02 |
| g10r8f1to4b12_od | 4.9 [4.7, 5.2] | 4 / 9 | 0.000 | 2.5 | 21.0 | 0.377 | 10111 | 0.175 | 10001 | 0.02 |
| g10r5f1to4b12_od | 7.2 [6.4, 8.0] | 4 / 13 | 0.000 | 2.5 | 21.0 | 0.340 | 10111 | 0.128 | 10101 | 0.08 |
| g10r3f1to4b12_od | 15.7 [13.7, 17.7] | 4 / 44 | 0.000 | 3.0 | 21.0 | 0.113 | 10101 | 0.026 | 10101 | 0.44 |
| g10r20f1to2b36_od | 5.7 [5.5, 5.9] | 6 / 10 | 0.000 | 2.5 | 20.0 | 0.406 | 10011 | 0.205 | 10001 | 0.02 |
| g10r8f1to2b36_od | 6.1 [5.8, 6.4] | 6 / 10 | 0.000 | 2.5 | 20.0 | 0.399 | 10011 | 0.189 | 10001 | 0.03 |
| g10r5f1to2b36_od | 11.8 [10.4, 13.1] | 6 / 26 | 0.000 | 2.6 | 20.0 | 0.285 | 10101 | 0.112 | 10101 | 0.18 |
| g10r3f1to2b36_od | 26.7 [23.5, 29.9] | 6 / 67 | 0.000 | 3.2 | 20.0 | 0.067 | 10101 | 0.015 | 00101 | 0.57 |
| g15r20f1to4b12_od | 7.3 [7.0, 7.6] | 7 / 13 | 0.000 | 2.5 | 26.6 | 0.204 | 10101 | 0.070 | 10101 | 0.06 |
| g15r8f1to4b12_od | 14.9 [12.7, 17.1] | 7 / 26 | 0.000 | 2.5 | 26.6 | 0.063 | 10101 | 0.011 | 10101 | 0.35 |
| g15r5f1to4b12_od | 36.5 [31.1, 41.8] | 7 / 102 | 0.000 | 2.5 | 26.6 | 0.003 | 00001 | 0.000 | 00001 | 0.68 |
| g15r3f1to4b12_od | 72.2 [62.9, 81.6] | 14 / 215 | 0.000 | 3.3 | 26.6 | 0.000 | 00001 | 0.000 | 00000 | 0.78 |
| g15r20f2to9b12_od | 4.9 [4.7, 5.0] | 4 / 9 | 0.000 | 2.5 | 29.6 | 0.194 | 10101 | 0.081 | 10101 | 0.01 |
| g15r8f2to9b12_od | 5.9 [5.3, 6.5] | 4 / 9 | 0.000 | 2.5 | 29.6 | 0.182 | 10101 | 0.073 | 10101 | 0.02 |
| g15r5f2to9b12_od | 9.7 [8.2, 11.2] | 4 / 16 | 0.000 | 2.5 | 29.6 | 0.124 | 10101 | 0.034 | 10101 | 0.13 |
| g15r3f2to9b12_od | 20.5 [17.3, 23.7] | 4 / 54 | 0.000 | 2.9 | 29.6 | 0.023 | 10101 | 0.003 | 00101 | 0.45 |
| g15r20f1to2b36_od | 8.8 [8.5, 9.1] | 8 / 15 | 0.000 | 2.5 | 26.8 | 0.201 | 10101 | 0.071 | 10101 | 0.06 |
| g15r8f1to2b36_od | 23.0 [19.9, 26.1] | 8 / 57 | 0.000 | 2.5 | 26.8 | 0.051 | 10101 | 0.013 | 00101 | 0.42 |
| g15r5f1to2b36_od | 51.4 [45.3, 57.6] | 9 / 149 | 0.000 | 2.5 | 26.8 | 0.005 | 00001 | 0.001 | 00001 | 0.68 |
| g15r3f1to2b36_od | 116.1 [104.4, 127.8] | 35 / 331 | 0.000 | 3.3 | 26.8 | 0.000 | 00001 | 0.000 | 00000 | 0.79 |
| g15r20f2to4b12_od | 6.2 [6.0, 6.4] | 6 / 11 | 0.000 | 2.5 | 26.6 | 0.210 | 10101 | 0.075 | 10101 | 0.04 |
| g15r8f2to4b12_od | 8.5 [7.5, 9.5] | 6 / 12 | 0.000 | 2.5 | 26.6 | 0.186 | 10101 | 0.054 | 10101 | 0.13 |
| g15r5f2to4b12_od | 17.1 [14.8, 19.4] | 6 / 45 | 0.000 | 2.5 | 26.6 | 0.048 | 10101 | 0.010 | 00101 | 0.40 |
| g15r3f2to4b12_od | 36.9 [32.4, 41.4] | 7 / 104 | 0.000 | 3.3 | 26.6 | 0.002 | 00001 | 0.001 | 00000 | 0.69 |
| g20r20f1to4b12_od | 9.4 [9.1, 9.7] | 8 / 17 | 0.000 | 2.4 | 29.1 | 0.149 | 10101 | 0.050 | 10101 | 0.13 |
| g20r8f1to4b12_od | 38.8 [33.0, 44.5] | 8 / 96 | 0.000 | 2.4 | 29.1 | 0.003 | 00001 | 0.001 | 00001 | 0.68 |
| g20r5f1to4b12_od | 94.1 [80.6, 107.6] | 12 / 239 | 0.001 | 2.5 | 29.1 | 0.000 | 00001 | 0.000 | 00001 | 0.79 |
| g20r3f1to4b12_od | 179.0 [157.5, 200.5] | 38 / 501 | 0.009 | 2.8 | 29.1 | 0.000 | 00001 | 0.000 | 00000 | 0.82 |
| g20r20f4to16b12_od | 4.5 [4.3, 4.7] | 4 / 8 | 0.000 | 2.3 | 26.4 | 0.278 | 10101 | 0.123 | 10101 | 0.01 |
| g20r8f4to16b12_od | 5.5 [4.9, 6.1] | 4 / 8 | 0.000 | 2.4 | 26.4 | 0.271 | 10101 | 0.106 | 10101 | 0.02 |
| g20r5f4to16b12_od | 9.3 [7.6, 11.0] | 4 / 12 | 0.000 | 2.5 | 26.4 | 0.175 | 10101 | 0.056 | 10101 | 0.13 |
| g20r3f4to16b12_od | 19.7 [15.9, 23.6] | 4 / 40 | 0.000 | 3.1 | 26.4 | 0.032 | 10101 | 0.009 | 00101 | 0.50 |
| g20r20f1to2b36_od | 11.5 [11.1, 11.9] | 11 / 20 | 0.000 | 2.4 | 27.6 | 0.170 | 10101 | 0.072 | 10101 | 0.14 |
| g20r8f1to2b36_od | 75.7 [65.1, 86.4] | 11 / 208 | 0.000 | 2.4 | 27.6 | 0.001 | 00001 | 0.000 | 00001 | 0.74 |
| g20r5f1to2b36_od | 151.7 [134.8, 168.6] | 40 / 403 | 0.004 | 2.5 | 27.6 | 0.000 | 00001 | 0.000 | 00001 | 0.80 |
| g20r3f1to2b36_od | 251.4 [228.0, 274.8] | 92 / 746 | 0.008 | 2.8 | 27.6 | 0.000 | 00001 | 0.000 | 00000 | 0.82 |
| g20r20f2to6b12_od | 7.1 [6.9, 7.4] | 6 / 13 | 0.000 | 2.3 | 27.2 | 0.220 | 10101 | 0.083 | 10101 | 0.06 |
| g20r8f2to6b12_od | 17.4 [14.2, 20.6] | 6 / 22 | 0.000 | 2.3 | 27.2 | 0.051 | 10101 | 0.011 | 00101 | 0.42 |
| g20r5f2to6b12_od | 33.4 [27.9, 38.8] | 6 / 89 | 0.000 | 2.4 | 27.2 | 0.006 | 00001 | 0.000 | 00001 | 0.67 |
| g20r3f2to6b12_od | 72.2 [62.5, 81.9] | 13 / 209 | 0.000 | 2.8 | 27.2 | 0.000 | 00001 | 0.000 | 00000 | 0.78 |

Check scaling (other things at today's count, `oc`, 32 worlds): food search identical to the matching `od` world (same food positions and agent starts); cover mean 4.0–28.3; warmth mean 94.6–243.1; survival ×1 at most 0.007; criteria 1–5 passed at ×1 by 0 worlds.

Criterion failures over all 72 worlds — ×1: 1_time fails in 45, 2_drive fails in 72, 3_death fails in 43, 4_survival fails in 67, 5_hide fails in 0; ×2: 1_time fails in 51, 2_drive fails in 72, 3_death fails in 42, 4_survival fails in 72, 5_hide fails in 9. Criterion 2's per-decision warming ratio is "not computable" (no start state at body temperature ≥ 0 chooses warming) in all 72 worlds, which fails criterion 2 by the inherited rule; example eating / hiding ratios at ×1: today 2.77 / 14.26.

Worlds meeting the search floor (mean food search ≥ 20): 31 of 72; worlds with > 1 % capped food searches: 0.

**Candidate rule output: candidates = none; shortest-range 10 × 10 world passing criteria 1–5 at both hazards = none.** The candidate manifest (`part3_balance_worlds_manifest.json`) is therefore empty; Part 4, per the plan, does not run on this output.

## Implementation Report — Parts 1–3 (2026-09-27)

**Files.** New folder `scripts/analysis/studies/context_exploration/`: `hidden_context.py` (Part 1),
`context_hazard.py` + `value_of_knowing.py` (Part 2), `make_worlds.py` + `forager.py` + `balance_worlds.py`
(Part 3). Reused, with one new optional argument each and no change to existing behaviour:
`internal_state_interactions/measure_world.py` (`measure_hazard_bins(..., episode_select=None)`) and
`internal_state_interactions/planner.py` (`World.find_prob=None`; `macro_branches(..., steps=None)`;
`rollout_balance(..., dyn_world=None)`). `docs/environment/SCRIPTS_DEPENDENCY_MAP.md`: new row + the
internal-state row's "callers outside the folder". Nothing under `src/` or `configs/` was touched;
`make_training_configs.py` (Part 4) is not written.

**Validation of the reused modules.** `validate_balance.py` run before and after the edits: all gates pass,
and the two output JSONs are byte-identical. `measure_hazard_bins` with an all-episodes selector returns
exactly the default call's result (3 blocks). Planner search option: find probability 1 reproduces a
one-step trip bit for bit (above).

**Choices the plan left open (stated, not silent).**
1. Resets: 1,000 per layout (Revision 1a), not 300.
2. Assertion 2 ((0,0)) is strict only for types whose area excludes (0,0) (fires, inset by `edge_margin` 2).
   Widened areas `[[1,1],[G,G]]` include (0,0) for every other type, so there the count at (0,0) is
   reported beside the mean of the other three corners (in `worlds/*/layout.json`).
3. Warmth ambient = the episode's coldest cell (the field's fill value).
4. "In the open away from cover" = not in a bush and Manhattan distance ≥ 2 from every active bush.
5. Steps-since-last-hit sensitivity has a fourth bin, "no hit yet", for steps before the episode's first hit.
6. Bootstrap = Poisson(1) episode weights seeded by the episode seed (1,000 resamples), so the two agents'
   gaps are paired per episode; smell quintile edges fixed on block 0 of both agents.
7. Part 2 value interval = normal interval of a difference of two proportions over 30,000 starts per policy
   (seeds pooled; per-seed values in the JSON). Choice difference primary at the balance study's
   choice-category level; action level also in the JSON.
8. Part 3 planner: map without a warm bush only; find probability for food, cover and warmth
   (warmth at 5 °C); going to open ground keeps the 2-step trip; rollouts 2,000 starts, seed 0 (balance
   study default); hazard scale = hunting predators per cell (count-range midpoint) relative to today's.
   The middle food rung uses 12 bites. Criterion 4 is judged against today's world at ×1 at both hazards;
   the ratio to today at the same hazard is in the JSON (`survival_vs_today_same_hazard`).
9. Forager validation (i) raises the step cap to 100,000 so the comparison with the uncapped chain is not
   truncated (at the 2,000 cap one corner-target case read 9.2 % off).

**Speed check.** Skipped: analysis tooling only, no training hot path touched.

**Open items for `senior-developer`.** Part 3's candidate list is empty, so Part 4 does not run on this
output (plan: "the study returns to this plan"). Known Bugs consulted by grep (`res_type` filter,
(0,0) parking, stale saved budget), all as cited in the plan; nothing new for `bug-curator`.

Implemented by: developer

## Revision 2 (2026-09-27) — fixing the warmth trip in Part 3, written after Part 3's null and before its re-run

**Why.** Part 3 found no candidate, but today's level 05 itself failed the balance criteria under the
Part-3 method, so the method cannot rank worlds. The cause is the warmth trip: the forager searched for
warmth blind every time (random walk until heat is felt), giving mean trips of 20–30 steps even in today's
world, where the balance study measured 2. A trained agent does not re-search: fires are fixed within an
episode, heat is felt a few cells away, and the agent can remember where it was warm.

**Change (Part 3 only; Parts 1–2 stand).**
- **Warmth, with memory (primary):** the warmth trip is the walking distance (grid steps, around rocks and
  fires) from a random open cell to the nearest cell warmer than 0 °C, measured on the same 1,000 resets per
  world — the same definition the balance study used for its ring trip.
- **Warmth, blind search (reported):** the Revision-1 forager result, as the pessimistic bracket.
- Food and cover trips are unchanged (food moves after it is used up, so memory does not help there; cover
  is found by smell).

**Validity gate (pre-registered).** The Part-3 method is valid only if **today's level 05 passes balance
criteria 1, 2, 4 and 5 under the primary (memory) warmth trip**. If it does not, Part 3 reports "method not
valid" and no world is ranked; nothing is loosened after the fact.

**Everything else unchanged:** the candidate rule (Revision 1 / 1a: balance criteria at hazard ×1 and ×2,
mean food search ≥ 20 steps over 1,000 resets, survival ≥ 80 % of today's under the same method), the
worlds (72), and Part 4.

## Feedback from plan-reviewer — Revision 2 (2026-09-27, before the Part-3 re-run)

**Verdict: NOT READY — one Critical, fixable in the text alone.** The correction itself is legitimate,
not a rescue: the balance study defined warmth as a static ring trip (mean 2.57 steps, Manhattan, from a
random open cell — `measure_world.py:159-171`, `world_measurements.json`) *before* Part 3 existed, and
Revision 1's blind forager was the departure from it (mean 21 on the same world). I re-solved today's
world with the Part-3 pipeline (`planner.py` + `find_prob`, everything else as in `balance_worlds.py`)
with the warmth find-probability set to 1 / 2.57 instead of 1 / 21: survival **0.5775** vs the balance
study's baseline **0.5725**; late deaths injury 716 / cold 0 vs 732 / 0; eat drive 3.66 vs 3.64; hide 9.9
vs 8.3. The warmth trip is the whole discrepancy (Revision 1 gave 0.3715 with 450 cold late-deaths).
The candidate rule is untouched and the change applies to all 72 worlds alike, so this is a measurement
fix. What is wrong is the **gate**, which as written will fail on a technicality and force exactly the
after-the-fact loosening the plan forbids itself.

Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run ·
🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

| Sev | Where | Issue | Fix |
|---|---|---|---|
| 🔴 | Revision 2 "Validity gate" × `balance_rule.py:26-27`, `planner.py:595` | Criterion 2 fails today's world not because of the warmth trip but because the per-decision warming ratio is `None`: no warm-bodied (≥ 0 °C) start state ever chooses "warm up", so the denominator is zero and the inherited rule (`v is not None`) counts a perfectly specific drive as a fail. **This does not go away with the memory trip**: my re-solve gives `share_cold` 0.535, `share_warm` 0.0, ratio `None` → criterion 2 fails → the gate fails → "method not valid", while the pipeline reproduces the balance study to 0.005 in survival. The balance study's own baseline passed only by accident: `share_warm` = 6.9 × 10⁻⁵ (ratio 8797), one boundary state that the geometric feed flips. | **Pre-register now, before the re-run, uniformly for all worlds:** a `None` ratio with `share_warm` = 0 and `share_cold` ≥ a stated floor (the balance baseline's 0.60 makes 0.30 safe) is a **pass** (ratio reported as "∞, cold share x"); `None` with `share_cold` = 0 stays a fail. Record in the doc that this is a clarification of a degenerate case the balance study never hit, and correct the "Why" paragraph: the criterion-2 fail was the `None` rule; the warmth trip is what moved survival 0.57 → 0.37 and created the 450 cold deaths. |
| 🟡 | Validity gate | The gate is nearly vacuous once criterion 2 is settled: criterion 4 is today-vs-itself (ratio 1.0 by construction, `balance_worlds.py` `base = res[tslug]`), criterion 5 passed 72 / 72 worlds at ×1, criterion 1 passed today already. Nothing in it checks against ground truth *outside* the Part-3 pipeline. | Add: today's world under the memory trip must reproduce the balance study's baseline on the no-warm-bush map — survival within ±0.05 of 0.5725 and cold late-deaths ≤ 5 % of late deaths (balance: 0). The re-solve says this passes (0.5775, 0 / 720); it is the one check that would have caught Revision 1 outright. |
| 🟡 | Validity gate | Hazard is unstated. At ×2 criterion 4 compares to today's **×1** survival (Implementation Report item 8; `crit = BR.criteria(r, base[1.0], …)`), so today's own ×2 run is 0.50 of itself and fails 4 by construction. Read as "both hazards", the gate cannot pass. | State "at hazard ×1 (today's real hazard)". |
| 🟡 | Validity gate | Criterion 3 is dropped from the gate with no reason given, which reads as gerrymandering. The reason exists and is good: the balance study's baseline **fails 3** (`balance_rule.json` baseline: 732 / 732 late deaths injury; verdict "neither"), and Revision 1's today passed 3 only because 450 cold deaths diluted the injury share to 0.586. | Say so in the doc, and note the consequence: under the memory trip today fails 3 again, so a candidate must pass a criterion the reference does not — inherited from the balance study and pre-registered, but it should be visible. |
| 🟡 | Revision 2 "Warmth, with memory" | "The same definition the balance study used" is not accurate on two counts. (a) The balance ring trip is straight Manhattan distance through everything (`measure_world.py:157`), not "walking distance around rocks and fires"; rocks are non-blocking in level 05 and the Part-3 food forager crosses them, so "around rocks" is a third convention inside one method. (b) The balance planner fed the **median (2) as a deterministic trip** (`sweep_balance.py:51`); Part 3 feeds **1 / mean as a geometric find-probability** (mean 2.57, so 0.39 per step). The re-solve shows (b) changes survival by ≈ 0.005, so it is harmless — but say it. | Either use the balance study's Manhattan definition outright, or keep walking distance and state the deviation plus the feed difference. "Warmer than 0 °C" is fine: only Manhattan-1 ring cells (+8.8) and the fire cell (+77) are above 0 (`cell_temp_by_fire_distance`: d = 2 median −16.5, p90 −15.6), and the fire cell is never the nearest from an open cell. |
| 🟢 | Same | Start cell: warmth uses "a random open cell", food / cover use the reset's agent start. With random start on they coincide in distribution; say "the reset's agent start, as food and cover" or "interior open cell excluding bush / fire as `measure_world.py`". | One clause. |
| 🟢 | Same | The blind bracket is worth keeping, but note that it is pessimistic for a second reason: fires are visible on the obstacle channel, so a trained agent can walk to candidate obstacles rather than random-walk. | One clause. |

**Criterion 4 within method — confirmed in code, not just prose.** `balance_worlds.py` takes today's
reference from the same run's solve of `g10r20f1to4b12_od`, so the 0.371 baseline is recomputed under
whatever warmth feed is used; nothing is hard-coded. Correct as the plan states.

**Assumptions the re-run rests on.** (1) Fires are fixed within an episode and remembered — verified for
the planner (a static per-world trip is what the balance study used), unverified for the trained agent
(Part 4 is where that shows). (2) The memory trip stays ≈ 2–3 steps in every `od` world because fire
density is held — plausible (ring trip scales with the inter-fire distance, not the grid), unverified until
measured; in `oc` worlds it will grow and cold deaths will return, which is the intended contrast.
(3) Criterion 2's eat / hide ratios are unaffected by the warmth feed — the re-solve says yes for today
(3.66 / 9.9), not checked for other worlds.

**Cost of being wrong.** If the gate is left as written, the ~1-hour re-run over 72 worlds ends with
"method not valid" on a degenerate-denominator technicality, the author has to loosen the rule after
seeing the data, and every Part-3 ranking downstream carries a post-hoc mark it did not need. If the
gate is fixed but the survival-agreement check is not added, a future measurement flaw of the same kind
passes silently again. Neither loses data.

**To flip to SOUND:** pre-register the `None` treatment (🔴), state hazard ×1 and the criterion-3 reason,
add the survival-agreement check, and correct the "same definition" sentence. All text; no code needs to
change before the re-run except the `None` rule in `balance_worlds.py`'s criterion call, which `developer`
should apply uniformly rather than special-casing today's world. Owner: `experiment-designer` (plan text),
`developer` (the one rule change). Nothing for `bug-curator`.

Reviewed by: plan-reviewer

## Revision 2a (2026-09-27) — answers to the review of Revision 2 (`480a1cc2`), before the re-run

- **Correction to Revision 2's "Why".** Today's criterion-2 failure under Part 3 was not only the trip: the
  per-decision warming ratio was "not computable" because no warm-bodied start state ever chooses to warm
  up (share at ≥ 0 °C is exactly 0). That is the ideal pattern, not a failure. **Rule, applied uniformly to
  all worlds:** if the share at ≥ 0 °C is 0 and the share at ≤ −5 °C is at least 10 %, the warming part of
  criterion 2 **passes**; if both shares are 0 it fails. (The balance study passed today's world only through
  a single boundary state; this rule removes that fragility.) `balance_rule.py` in the internal-state study
  is not changed; the Part-3 script applies this rule and says so.
- **Validity gate, made independent:** at hazard ×1 only, today's level 05 under the primary (memory) warmth
  trip must (i) pass criteria 1, 2, 4 and 5 and (ii) reproduce the balance study's baseline — survival share
  within ±0.05 of 0.5725 and cold deaths at most 1 % of deaths after step 20.
- **Criterion 3 (deaths) is report-only in Part 3.** In the planner, injury causes 94–100 % of late deaths in
  every world (balance study, published); gating on it would reject every world, the reference included.
  Real training judges deaths (Part 4).
- **Wording:** the balance study's ring trip was a straight-line (Manhattan, through rocks) median of 2 fed
  as a fixed trip; Part 3's is walking distance around rocks and fires, fed as a per-step chance 1 / mean.
  The difference is small (re-solve: survival 0.5775 vs 0.5725) and stated.

## Results (raw) — Revision 2 (2026-09-27)

Re-run of Part 3 under Revisions 2 / 2a: warmth trip with memory (primary) and blind (bracket) both solved;
criterion 2's warming part by the Revision-2a rule (applied in `balance_worlds.py`; `balance_rule.py`
unchanged); criterion 3 report-only; candidate rule uses criteria 1, 2, 4, 5. Outputs:
`results/analysis/context_exploration/part3_search_times_rev2.json`, `part3_balance_worlds_rev2.json`
(Revision-1 files kept).

### Validity gate

- Validity gate (today's level 05, memory trip, hazard x1): criteria 1/2/4/5 = 1/1/1/1; survival 0.5770 (target 0.5725 +/- 0.05); cold deaths 0 of 722 deaths after step 20 (0.000, max 0.01). **Gate: PASS**.
- Today's survival: memory x1 0.5770, x2 0.3780; blind x1 0.3715, x2 0.1860.
- Blind-trip solves reproduce Revision 1's survival exactly in all 72 worlds × 2 hazards (max difference 0.0).
- Warmth trip with memory (walking distance, around rocks and fires, 20 random open interior cells per reset,
  1,000 resets): today's world mean 2.69, median 2, p90 6, unreachable samples 0.001; Manhattan-through
  mean 2.59 (balance study's ring trip: mean 2.57, median 2). Food, cover and blind-warmth search times are
  identical to Revision 1's.

### Worlds

Criteria strings = pass(1)/fail(0) for criteria 1 time, 2 drive (Revision-2a warming rule), 3 death
(report-only), 4 survival (vs today at ×1 under the same trip), 5 hide. Food = "count" (same count as
today, 1–4), "density" (same density), "mid" (middle rung), "fewrich" (1–2 items); b = bites per item. Others: `od` = other
entities at today's density, `oc` = at today's count. Search and warmth trips in steps.

| World | Grid | Food | Range | Others | Food search mean | Warmth memory / blind | Crit ×1 (memory) | Crit ×2 (memory) | Survival ×1 / ×2 (memory) | Cold share of late deaths ×1 | Blind: crit ×1 / ×2, survival ×1 | Meets rule (blind) | Candidate |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| g10r20f1to2b36_od | 10 | fewrich (b36) | 20 | od | 5.7 | 2.68 / 20.0 | 11011 | 11001 | 0.566 / 0.370 | 0.000 | 11011 / 11001, 0.406 | no | no |
| g10r8f1to2b36_od | 10 | fewrich (b36) | 8 | od | 6.1 | 2.68 / 20.0 | 11011 | 11001 | 0.573 / 0.365 | 0.000 | 11011 / 11001, 0.399 | no | no |
| g10r5f1to2b36_od | 10 | fewrich (b36) | 5 | od | 11.8 | 2.68 / 20.0 | 11011 | 11001 | 0.490 / 0.265 | 0.000 | 11101 / 11101, 0.285 | no | no |
| g10r3f1to2b36_od | 10 | fewrich (b36) | 3 | od | 26.7 | 2.68 / 20.0 | 11001 | 11101 | 0.166 / 0.054 | 0.000 | 11101 / 01101, 0.067 | no | no |
| g10r20f1to4b12_od | 10 | count (b12) | 20 | od | 4.7 | 2.69 / 21.0 | 11011 | 11001 | 0.577 / 0.378 | 0.000 | 11111 / 11001, 0.371 | no | no |
| g10r8f1to4b12_od | 10 | count (b12) | 8 | od | 4.9 | 2.69 / 21.0 | 11011 | 11001 | 0.577 / 0.365 | 0.000 | 11111 / 11001, 0.377 | no | no |
| g10r5f1to4b12_od | 10 | count (b12) | 5 | od | 7.2 | 2.69 / 21.0 | 11011 | 11001 | 0.545 / 0.326 | 0.000 | 11111 / 11101, 0.340 | no | no |
| g10r3f1to4b12_od | 10 | count (b12) | 3 | od | 15.7 | 2.69 / 21.0 | 11101 | 11101 | 0.299 / 0.108 | 0.000 | 11101 / 11101, 0.113 | no | no |
| g15r20f1to2b36_od | 15 | fewrich (b36) | 20 | od | 8.8 | 3.10 / 26.8 | 11011 | 11001 | 0.519 / 0.301 | 0.000 | 11101 / 11101, 0.201 | no | no |
| g15r8f1to2b36_od | 15 | fewrich (b36) | 8 | od | 23.0 | 3.10 / 26.8 | 11001 | 11101 | 0.217 / 0.072 | 0.000 | 11101 / 01101, 0.051 | no | no |
| g15r5f1to2b36_od | 15 | fewrich (b36) | 5 | od | 51.4 | 3.10 / 26.8 | 01001 | 01000 | 0.015 / 0.003 | 0.000 | 01001 / 01001, 0.005 | no | no |
| g15r3f1to2b36_od | 15 | fewrich (b36) | 3 | od | 116.1 | 3.10 / 26.8 | 01001 | 00000 | 0.001 / 0.001 | 0.000 | 01001 / 00000, 0.000 | no | no |
| g15r20f1to4b12_od | 15 | count (b12) | 20 | od | 7.3 | 3.10 / 26.6 | 11011 | 11001 | 0.533 / 0.291 | 0.000 | 11101 / 11101, 0.204 | no | no |
| g15r8f1to4b12_od | 15 | count (b12) | 8 | od | 14.9 | 3.10 / 26.6 | 11101 | 11101 | 0.294 / 0.115 | 0.000 | 11101 / 11101, 0.063 | no | no |
| g15r5f1to4b12_od | 15 | count (b12) | 5 | od | 36.5 | 3.10 / 26.6 | 01001 | 01000 | 0.014 / 0.004 | 0.000 | 01001 / 01001, 0.003 | no | no |
| g15r3f1to4b12_od | 15 | count (b12) | 3 | od | 72.2 | 3.10 / 26.6 | 01001 | 01000 | 0.000 / 0.000 | 0.000 | 01001 / 00000, 0.000 | no | no |
| g15r20f2to4b12_od | 15 | mid (b12) | 20 | od | 6.2 | 3.10 / 26.6 | 11011 | 11001 | 0.533 / 0.311 | 0.000 | 11101 / 11101, 0.210 | no | no |
| g15r8f2to4b12_od | 15 | mid (b12) | 8 | od | 8.5 | 3.10 / 26.6 | 11011 | 11001 | 0.503 / 0.258 | 0.000 | 11101 / 11101, 0.186 | no | no |
| g15r5f2to4b12_od | 15 | mid (b12) | 5 | od | 17.1 | 3.10 / 26.6 | 11101 | 11101 | 0.227 / 0.070 | 0.000 | 11101 / 01101, 0.048 | no | no |
| g15r3f2to4b12_od | 15 | mid (b12) | 3 | od | 36.9 | 3.10 / 26.6 | 01001 | 01000 | 0.015 / 0.002 | 0.000 | 01001 / 01000, 0.002 | no | no |
| g15r20f2to9b12_od | 15 | density (b12) | 20 | od | 4.9 | 3.12 / 29.6 | 11011 | 11001 | 0.539 / 0.325 | 0.000 | 11101 / 11101, 0.194 | no | no |
| g15r8f2to9b12_od | 15 | density (b12) | 8 | od | 5.9 | 3.12 / 29.6 | 11011 | 11001 | 0.538 / 0.329 | 0.000 | 11101 / 11101, 0.182 | no | no |
| g15r5f2to9b12_od | 15 | density (b12) | 5 | od | 9.7 | 3.12 / 29.6 | 11001 | 11001 | 0.454 / 0.238 | 0.000 | 11101 / 11101, 0.124 | no | no |
| g15r3f2to9b12_od | 15 | density (b12) | 3 | od | 20.5 | 3.12 / 29.6 | 11001 | 11101 | 0.142 / 0.033 | 0.000 | 11101 / 01101, 0.023 | no | no |
| g20r20f1to2b36_od | 20 | fewrich (b36) | 20 | od | 11.5 | 3.21 / 27.6 | 11011 | 11001 | 0.509 / 0.286 | 0.000 | 11101 / 11101, 0.170 | no | no |
| g20r8f1to2b36_od | 20 | fewrich (b36) | 8 | od | 75.7 | 3.21 / 27.6 | 01001 | 01000 | 0.004 / 0.001 | 0.000 | 01001 / 01001, 0.001 | no | no |
| g20r5f1to2b36_od | 20 | fewrich (b36) | 5 | od | 151.7 | 3.21 / 27.6 | 01001 | 00000 | 0.000 / 0.000 | 0.000 | 01001 / 01001, 0.000 | no | no |
| g20r3f1to2b36_od | 20 | fewrich (b36) | 3 | od | 251.4 | 3.21 / 27.6 | 01001 | 00000 | 0.000 / 0.000 | 0.000 | 01001 / 00000, 0.000 | no | no |
| g20r20f1to4b12_od | 20 | count (b12) | 20 | od | 9.4 | 3.21 / 29.1 | 11011 | 11001 | 0.502 / 0.299 | 0.000 | 11101 / 11101, 0.149 | no | no |
| g20r8f1to4b12_od | 20 | count (b12) | 8 | od | 38.8 | 3.21 / 29.1 | 01001 | 01000 | 0.018 / 0.001 | 0.000 | 01001 / 01001, 0.003 | no | no |
| g20r5f1to4b12_od | 20 | count (b12) | 5 | od | 94.1 | 3.21 / 29.1 | 01001 | 00000 | 0.001 / 0.000 | 0.000 | 01001 / 01001, 0.000 | no | no |
| g20r3f1to4b12_od | 20 | count (b12) | 3 | od | 179.0 | 3.21 / 29.1 | 01001 | 00000 | 0.000 / 0.000 | 0.000 | 01001 / 00000, 0.000 | no | no |
| g20r20f2to6b12_od | 20 | mid (b12) | 20 | od | 7.1 | 3.21 / 27.2 | 11011 | 11001 | 0.560 / 0.330 | 0.000 | 11101 / 11101, 0.220 | no | no |
| g20r8f2to6b12_od | 20 | mid (b12) | 8 | od | 17.4 | 3.21 / 27.2 | 11101 | 11101 | 0.236 / 0.090 | 0.000 | 11101 / 01101, 0.051 | no | no |
| g20r5f2to6b12_od | 20 | mid (b12) | 5 | od | 33.4 | 3.21 / 27.2 | 01001 | 01000 | 0.024 / 0.006 | 0.000 | 01001 / 01001, 0.006 | no | no |
| g20r3f2to6b12_od | 20 | mid (b12) | 3 | od | 72.2 | 3.21 / 27.2 | 01001 | 01000 | 0.001 / 0.000 | 0.000 | 01001 / 01000, 0.000 | no | no |
| g20r20f4to16b12_od | 20 | density (b12) | 20 | od | 4.5 | 3.23 / 26.4 | 11011 | 11001 | 0.590 / 0.367 | 0.000 | 11101 / 11101, 0.278 | no | no |
| g20r8f4to16b12_od | 20 | density (b12) | 8 | od | 5.5 | 3.23 / 26.4 | 11011 | 11001 | 0.584 / 0.362 | 0.000 | 11101 / 11101, 0.271 | no | no |
| g20r5f4to16b12_od | 20 | density (b12) | 5 | od | 9.3 | 3.23 / 26.4 | 11011 | 11001 | 0.525 / 0.279 | 0.000 | 11101 / 11101, 0.175 | no | no |
| g20r3f4to16b12_od | 20 | density (b12) | 3 | od | 19.7 | 3.23 / 26.4 | 11001 | 11101 | 0.165 / 0.048 | 0.000 | 11101 / 01101, 0.032 | no | no |
| g15r20f1to2b36_oc | 15 | fewrich (b36) | 20 | oc | 8.8 | 5.17 / 98.2 | 01011 | 01011 | 0.729 / 0.564 | 0.000 | 01001 / 00001, 0.005 | no | no |
| g15r8f1to2b36_oc | 15 | fewrich (b36) | 8 | oc | 23.0 | 5.17 / 98.2 | 01001 | 11001 | 0.338 / 0.229 | 0.000 | 01001 / 00001, 0.001 | no | no |
| g15r5f1to2b36_oc | 15 | fewrich (b36) | 5 | oc | 51.4 | 5.17 / 98.2 | 00001 | 01001 | 0.032 / 0.021 | 0.000 | 01001 / 01101, 0.001 | no | no |
| g15r3f1to2b36_oc | 15 | fewrich (b36) | 3 | oc | 116.1 | 5.17 / 98.2 | 01001 | 01001 | 0.002 / 0.000 | 0.000 | 01101 / 01101, 0.000 | no | no |
| g15r20f1to4b12_oc | 15 | count (b12) | 20 | oc | 7.3 | 5.17 / 94.6 | 01011 | 11011 | 0.728 / 0.555 | 0.000 | 01001 / 00001, 0.004 | no | no |
| g15r8f1to4b12_oc | 15 | count (b12) | 8 | oc | 14.9 | 5.17 / 94.6 | 01001 | 11101 | 0.457 / 0.290 | 0.000 | 01001 / 00001, 0.003 | no | no |
| g15r5f1to4b12_oc | 15 | count (b12) | 5 | oc | 36.5 | 5.17 / 94.6 | 01001 | 01001 | 0.032 / 0.015 | 0.000 | 01001 / 01101, 0.001 | no | no |
| g15r3f1to4b12_oc | 15 | count (b12) | 3 | oc | 72.2 | 5.17 / 94.6 | 01001 | 01001 | 0.002 / 0.000 | 0.000 | 01101 / 01101, 0.000 | no | no |
| g15r20f2to4b12_oc | 15 | mid (b12) | 20 | oc | 6.2 | 5.17 / 94.6 | 01011 | 11011 | 0.747 / 0.567 | 0.000 | 01001 / 00001, 0.005 | no | no |
| g15r8f2to4b12_oc | 15 | mid (b12) | 8 | oc | 8.5 | 5.17 / 94.6 | 01011 | 01011 | 0.690 / 0.532 | 0.000 | 01001 / 00001, 0.005 | no | no |
| g15r5f2to4b12_oc | 15 | mid (b12) | 5 | oc | 17.1 | 5.17 / 94.6 | 01001 | 01101 | 0.343 / 0.214 | 0.000 | 01001 / 01001, 0.003 | no | no |
| g15r3f2to4b12_oc | 15 | mid (b12) | 3 | oc | 36.9 | 5.17 / 94.6 | 01001 | 01001 | 0.032 / 0.011 | 0.000 | 01001 / 01101, 0.000 | no | no |
| g15r20f2to9b12_oc | 15 | density (b12) | 20 | oc | 4.9 | 5.17 / 95.6 | 01011 | 01011 | 0.751 / 0.578 | 0.000 | 01001 / 00001, 0.007 | no | no |
| g15r8f2to9b12_oc | 15 | density (b12) | 8 | oc | 5.9 | 5.17 / 95.6 | 01011 | 01011 | 0.748 / 0.569 | 0.000 | 01001 / 00001, 0.007 | no | no |
| g15r5f2to9b12_oc | 15 | density (b12) | 5 | oc | 9.7 | 5.17 / 95.6 | 01011 | 01001 | 0.648 / 0.458 | 0.000 | 01001 / 00001, 0.003 | no | no |
| g15r3f2to9b12_oc | 15 | density (b12) | 3 | oc | 20.5 | 5.17 / 95.6 | 01001 | 01101 | 0.220 / 0.106 | 0.001 | 01001 / 01001, 0.002 | no | no |
| g20r20f1to2b36_oc | 20 | fewrich (b36) | 20 | oc | 11.5 | 7.84 / 243.1 | 01011 | 01011 | 0.745 / 0.634 | 0.020 | 00001 / 00001, 0.000 | no | no |
| g20r8f1to2b36_oc | 20 | fewrich (b36) | 8 | oc | 75.7 | 7.84 / 243.1 | 01001 | 01001 | 0.009 / 0.005 | 0.000 | 00001 / 00001, 0.000 | no | no |
| g20r5f1to2b36_oc | 20 | fewrich (b36) | 5 | oc | 151.7 | 7.84 / 243.1 | 01001 | 01001 | 0.001 / 0.000 | 0.000 | 01001 / 00001, 0.000 | no | no |
| g20r3f1to2b36_oc | 20 | fewrich (b36) | 3 | oc | 251.4 | 7.84 / 243.1 | 01001 | 01001 | 0.000 / 0.000 | 0.001 | 01101 / 00100, 0.000 | no | no |
| g20r20f1to4b12_oc | 20 | count (b12) | 20 | oc | 9.4 | 7.83 / 236.9 | 01011 | 01011 | 0.744 / 0.626 | 0.035 | 00001 / 00001, 0.000 | no | no |
| g20r8f1to4b12_oc | 20 | count (b12) | 8 | oc | 38.8 | 7.83 / 236.9 | 01001 | 01001 | 0.025 / 0.018 | 0.000 | 00001 / 00001, 0.000 | no | no |
| g20r5f1to4b12_oc | 20 | count (b12) | 5 | oc | 94.1 | 7.83 / 236.9 | 01001 | 01001 | 0.001 / 0.001 | 0.000 | 01001 / 00001, 0.000 | no | no |
| g20r3f1to4b12_oc | 20 | count (b12) | 3 | oc | 179.0 | 7.83 / 236.9 | 01001 | 01001 | 0.000 / 0.000 | 0.000 | 01101 / 00100, 0.000 | no | no |
| g20r20f2to6b12_oc | 20 | mid (b12) | 20 | oc | 7.1 | 7.83 / 227.9 | 01011 | 01011 | 0.799 / 0.658 | 0.011 | 00001 / 00001, 0.000 | no | no |
| g20r8f2to6b12_oc | 20 | mid (b12) | 8 | oc | 17.4 | 7.83 / 227.9 | 01001 | 01001 | 0.372 / 0.256 | 0.008 | 00001 / 00001, 0.000 | no | no |
| g20r5f2to6b12_oc | 20 | mid (b12) | 5 | oc | 33.4 | 7.83 / 227.9 | 01001 | 01001 | 0.038 / 0.029 | 0.001 | 01001 / 00001, 0.000 | no | no |
| g20r3f2to6b12_oc | 20 | mid (b12) | 3 | oc | 72.2 | 7.83 / 227.9 | 01001 | 01001 | 0.001 / 0.000 | 0.000 | 01001 / 00000, 0.000 | no | no |
| g20r20f4to16b12_oc | 20 | density (b12) | 20 | oc | 4.5 | 7.84 / 237.9 | 01011 | 01011 | 0.829 / 0.704 | 0.027 | 00001 / 00001, 0.000 | no | no |
| g20r8f4to16b12_oc | 20 | density (b12) | 8 | oc | 5.5 | 7.84 / 237.9 | 01011 | 01011 | 0.804 / 0.676 | 0.007 | 00001 / 00001, 0.001 | no | no |
| g20r5f4to16b12_oc | 20 | density (b12) | 5 | oc | 9.3 | 7.84 / 237.9 | 01011 | 01011 | 0.705 / 0.528 | 0.014 | 01001 / 00001, 0.000 | no | no |
| g20r3f4to16b12_oc | 20 | density (b12) | 3 | oc | 19.7 | 7.84 / 237.9 | 01001 | 01001 | 0.241 / 0.163 | 0.007 | 01001 / 00001, 0.000 | no | no |

Criterion failures over 72 worlds — memory trip ×1: 1_time 45, 2_drive 1, 3_death 68, 4_survival 41,
5_hide 0; ×2: 1_time 41, 2_drive 5, 3_death 61, 4_survival 60, 5_hide 13. Blind trip ×1: 1_time 45,
2_drive 8, 3_death 43, 4_survival 67, 5_hide 0; ×2: 1_time 51, 2_drive 29, 3_death 42, 4_survival 72, 5_hide 9.
Warming part of criterion 2 (memory) passes in 72 / 72 worlds at both hazards — ×1: 44 by the "share at
≥ 0 °C is 0, share at ≤ −5 °C ≥ 0.10" branch, 28 by ratio ≥ 2; ×2: 64 and 8. Eating + hiding ratios pass in
71 / 72 at ×1.

Worlds passing criteria 1, 2, 4, 5 at ×1 (memory): 18; at both ×1 and ×2: 0. Today's own ×2 survival is
0.378 = 0.655 of its ×1 value (criterion 4 threshold 0.80). Reported, not the rule: with criterion 4 judged
against today at the same hazard (`criterion4_vs_today_same_hazard`), 11 worlds pass 1, 2, 4, 5 at both
hazards, food search means 4.5–7.2. Worlds meeting the search floor (≥ 20): 31; among them passing 1, 2, 4, 5
at ×1 (memory): 0. Worlds with > 1 % capped food searches: 0.

**Candidate rule output (memory trip, gate passed): candidates = none; shortest-range 10 × 10 world passing
criteria 1, 2, 4, 5 at both hazards = none. Blind bracket: worlds meeting the rule = none.** No manifest is
written.

## Implementation Report — Revision 2 / 2a re-run (2026-09-27)

**Files.** `scripts/analysis/studies/context_exploration/forager.py`: new `warmth_memory()` (multi-source
breadth-first search from every cell > 0 °C, four moves, rock and fire cells never entered, bushes crossable;
start = random interior cell that is not bush / rock / fire, 20 per reset, seed 0, as `measure_world.py`'s
ring trip; unreachable samples excluded and counted; Manhattan-through distance reported beside it), output
key `warmth_memory`. `balance_worlds.py`: both trips solved per world and hazard (288 solves, 26 min on 16
processes); `criteria_rev2a()` wraps `balance_rule.criteria` and replaces only criterion 2's warming part
(the inherited value is kept as `2_drive_inherited`); criterion 3 report-only; validity gate as Revision 2a;
candidates and manifest only when the gate passes. Nothing under `src/`, `configs/` or
`internal_state_interactions/` changed.

**Checks.** `validate_balance.py` re-run: all gates pass, output JSON identical to the stored one.
Forager validation (i) and (ii) pass as before; food / cover / blind warmth search times identical to
Revision 1; blind balance solves identical to Revision 1.

**Choices stated.** (1) "Around rocks and fires" follows the plan text (Revision 2a); the food forager
crosses rocks — the Manhattan-through number (2.59 vs walking 2.69 in today's world) bounds the difference.
(2) Warm target cells exclude fire cells (not enterable). (3) Revision-2a's rule leaves share at ≥ 0 °C = 0
with 0 < share at ≤ −5 °C < 0.10 undefined; it is treated as "ratio not computable → fail" (no world hit it
at either hazard). (4) Output files carry a `_rev2` suffix so the Revision-1 outputs cited above stay intact.

**Speed check.** Skipped: analysis tooling only.

**For `senior-developer`.** Under the gate-passing method no world passes criteria 1, 2, 4, 5 at ×2, today's
included (0.655 of today's ×1 survival), so the candidate rule as written cannot return a candidate at ×2;
the same-hazard comparison is reported above. Nothing for `bug-curator`.

Implemented by: developer

## Part 4 design (Revision 3, 2026-09-27) — which worlds the ordinary agent is trained on, and how it is judged

**In plain words.** The simulation (Part 3) could not produce a "candidate" by its own pre-registered
rule: no world stayed balanced when the danger was doubled, and no world where food takes 20 or more
steps to find stayed balanced even at today's danger. The user then asked for a training design chosen
from the simulation ("Based on the simulation, you can select proper design for the training. Then
proceed.", 2026-09-27). This section is that design, written **before any Part-4 run exists**. It trains
the ordinary agent (no modulator) on seven worlds: today's campfire world as the yardstick; the four
worlds the simulation calls balanced at today's danger where food is hardest to find (two to three
times longer searches than today: 9–12 steps against about 5); and two worlds just past the
simulation's edge, where food takes 23–27 steps to find and the simulation predicts the agent survives
far less than today. Each trained agent is then judged by the same balance tests used in the
internal-state study, and its verdict is set beside the simulation's verdict for the same world, so
the training both screens worlds for the later modulator comparison and tests whether the simulation's
balance map can be trusted.

### 4.1 Departure from the Part-4 text above (stated, not hidden)

- Part 4 (Revision 1) said: "If Part 3 finds no candidate, Part 4 does not run and the study returns
  to this plan." Part 3 found none. The study returned to the user, who authorised the selection below.
  Candidate status is **not** claimed for any world; the selection rule is new and is stated here.
- **Selection rule (applied to the Revision-2 results table, memory warmth trip):**
  (a) *balanced arm* — among the 18 worlds that pass criteria 1, 2, 4, 5 at hazard ×1, the four with the
  longest mean food search (11.8, 11.5, 9.4, 9.3 steps; the next is 8.8); the ×2 requirement and the
  20-step search floor are dropped because no world meets them together with ×1 balance;
  (b) *edge arm* — the two worlds with the longest mean food search among those that miss **only**
  criterion 4 (survival) at ×1 (26.7 and 23.0 steps; a third such world, `g15r3f2to9b12_od`, 20.5 steps,
  is not run); (c) today's level 05 as the reference.
- Seven worlds, eight runs: within Part 4's cap of 8 worlds / 9 runs.
- Other entities in every chosen world are at today's **density** (`_od`); no world at today's count
  (`_oc`) is run.

### 4.2 The worlds

The training files are byte-for-byte copies of the bodies of the simulation's own world files (only
the header comment differs), so training runs exactly the worlds the simulation measured. Sim numbers:
Revision-2 re-run, memory warmth trip, hazard ×1; survival ratio = mean survival steps against today's
(376.1 steps; the survival-share ratio used by the simulation's criterion 4 in brackets).

| # | Slug (sim id without `_od`) | Grid | Smell range | Food items × bites | Sim food search (mean, steps) | Sim criteria 1-2-3-4-5 | Sim survival vs today, steps (share) | Sim late-death cause, injury / starvation | Arm |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `lvl05ref` (= level 05 itself, `g10r20f1to4b12`) | 10 | 20 | 1–4 × 12 | 4.7 | 1 1 0 1 1 | 1.00 (1.00) | 0.99 / 0.01 | reference |
| 2 | `g10r5f1to2b36` | 10 | 5 | 1–2 × 36 | 11.8 | 1 1 0 1 1 | 0.91 (0.85) | 0.81 / 0.19 | balanced |
| 3 | `g20r20f1to4b12` | 20 | 20 | 1–4 × 12 | 9.4 | 1 1 0 1 1 | 0.92 (0.87) | 0.85 / 0.15 | balanced |
| 4 | `g20r5f4to16b12` | 20 | 5 | 4–16 × 12 | 9.3 | 1 1 0 1 1 | 0.94 (0.91) | 0.84 / 0.16 | balanced |
| 5 | `g20r20f1to2b36` | 20 | 20 | 1–2 × 36 | 11.5 | 1 1 0 1 1 | 0.91 (0.88) | 0.84 / 0.16 | balanced |
| 6 | `g10r3f1to2b36` | 10 | 3 | 1–2 × 36 | 26.7 | 1 1 0 0 1 | 0.62 (0.29) | 0.33 / 0.67 | edge |
| 7 | `g15r8f1to2b36` | 15 | 8 | 1–2 × 36 | 23.0 | 1 1 0 0 1 | 0.67 (0.38) | 0.39 / 0.61 | edge |

Sim criterion 3 fails in every world, the reference included (injury or starvation causes > 60 % of
late deaths); it was report-only in Part 3 and is judged for real here (4.4).

### 4.3 What runs (fixed)

- **Agent:** the ordinary agent, `t1none` — the unmodulated GAE_NORM agent config used by the Wave-2
  level-05 ordinary runs and the level-05 body-interaction pilots and factorial (`nmngaenorm_t1none.yaml`).
- **Budget:** 2,000,000 episodes per run, `--log-interval 10`, as the body-interaction pilots.
- **Seeds:** 42 for every world (config-owned, `configs/train/default.yaml`); the reference also 43.
  Borderline rule unchanged from Part 4: a world whose value on any criterion lies within the
  reference's seed-42/43 gap of its threshold gets a seed-43 run before it goes downstream (needs a new
  manifest row, same tag scheme).
- **Balance metrics on:** `logging.episode.balance_metrics: true` and
  `logging.episode.balance_early_death_max_steps: 20` live in `configs/train/recurrent_ppo.yaml`, which
  `train.py` merges for every `RecurrentPPO` agent config above `train/default.yaml` and below the
  experiment `--config` (`train.py:514-525`). No world file carries a `logging:` block. Verified by
  replaying that merge order for all seven worlds (4.8).
- **Calibration guard:** each run's stdout calibration record must read max food energy 200, max
  injury 100, temperature setpoint 0, open-ground upper edge −29, thermal and felt injury on — identical
  to level 05. A mismatch stops the run (Part 4 precondition).
- Everything else pinned to level 05 (body, thermal, rewards, random start body temperature
  [−10, +5], 500-step episode cap, sensors): the load-time diff against level 05 (4.8) shows only
  grid-size-, food- and smell-range-dependent fields.

### 4.4 Read-out and criteria (pre-registered)

**Window.** The last 10 % of training, episodes 1.8–2.0 M. Every logged row in the window counts,
weighted by the episodes it covers (difference of `Episode/Number` between rows). Balance shares with a
state counter (`Episode/Bal_N_*`) are pooled weighted by that counter and ratios are recomputed from the
pooled shares; the mean of per-row ratios is reported beside it. Time shares are weighted by the row's
steps (episodes × `Episode/Steps`).

**Environment steps.** For every run, the environment-step count (`timesteps`) at episode 1.8 M and
2.0 M is read from WandB (or the log), never from the saved config (Known Bugs 2026-09-04, stale saved
budget). Survival is reported per episode (`Episode/Steps`) and per 1,000 environment steps (episodes
completed ÷ environment steps × 1,000, a death-rate view); criterion 4 is judged on survival steps per
episode, with the step-count difference against the reference stated.

**Criteria** (internal-state study Revisions 2a–2c, applied to trained agents; key mapping from
[[BALANCE_METRICS_TRAINING_LOGGING]]):

1. **Time split:** no activity above 70 % of steps (`Bal_TimeBush`, `Bal_TimeWarm`, `Bal_TimeEat`,
   `Bal_TimeElsewhere`), and cover, warm cell and eating each at least 10 %. `Bal_TimeNearFire` report-only.
2. **Each need drives its own behaviour:** eating ratio (`Bal_EatRatio`) ≥ 2 **and** hiding ratio by true
   injury (`Bal_HideRatio_True`) ≥ 2. Felt-injury ratio reported. **Warming ratio (`Bal_WarmRatio`) logged,
   not pass/fail.**
3. **Deaths (gated):** if the share of all episodes dying after step 20 (`Bal_LateDeathShare`) is at least
   5 %, no single cause (`Bal_LateDeath_{Starvation,Overeating,Injury,Thermal}`) may exceed 60 % of those
   late deaths. Below 5 % the criterion passes. Early-death share reported.
4. **Survival:** mean survival steps per episode ≥ 80 % of the reference's (mean of seeds 42 and 43).
   For the reference itself this is 1.0 by construction.
5. **Injury still drives hiding among well-fed states:** `Bal_HideRatio_True_Fed` ≥ 2.

A ratio whose denominator is zero is "not computable" and fails its criterion (Revision 2b N5).
**Trained-balanced** = passes 1–5. **Still learning:** if survival steps in 1.8–2.0 M exceed those in
1.6–1.8 M by more than 5 % (relative), the world is "still learning" and its verdict is undecided;
extending it needs the user's approval. The reference's criterion values also set the noise scale
(seed 42 vs 43 gap), which defines "borderline" above.

**Temporal evolution (reported for every run):** survival steps, the five criteria's keys and the
late-death shares in 200,000-episode blocks across the whole run.

### 4.5 Simulation vs trained agent — agreement table (pre-registered)

For each world, one row: sim pass/fail on criteria 1, 2, 4, 5 (the set Part 3 judged; hazard ×1,
memory trip) against the trained agent's pass/fail on the same four, plus the trained criterion 3 (no sim
counterpart; sim failed it everywhere), sim vs trained survival ratio against today, and sim vs trained
late-death cause split.

- **Agreement per world** = the sim and the trained agent give the same pass/fail on all four of 1, 2, 4, 5.
- **Direction of the edge prediction:** the simulation predicts the two edge worlds fail criterion 4
  (trained survival < 80 % of the reference) and the four balanced worlds pass it. If an edge world's
  trained survival is ≥ 80 % of the reference, the simulation's balance edge is **too pessimistic** on
  the search axis; if a balanced world falls below 80 %, it is **too optimistic**. Either is stated as a
  finding about the simulation, not as a reason to re-run it.
- **Summary:** agreements out of 7 (6 excluding the reference, whose sim 1, 2, 4, 5 are 1 1 1 1 by the
  validity gate). The simulation is called **trustworthy for choosing worlds** if at least 5 of 6
  non-reference worlds agree **and** both criterion-4 directions hold; otherwise **not trustworthy**, and
  future world choices go through training rather than the simulation.

### 4.6 What result leads to the modulator comparison (pre-registered)

- **Goes forward:** a non-reference world that is trained-balanced (1–5), not still learning, and not
  borderline (or borderline and confirmed by its seed-43 run). Among those, priority by the simulation's
  mean food search (the longest search first, since hidden context is the point), at most three worlds
  for the modulator comparison, which is a separate design with ≥ 3 seeds per agent.
- **An edge world that turns out trained-balanced goes first**: it is the least observable world that
  holds up.
- **If no non-reference world passes 1–5:** no modulator comparison is designed from Part 4. If the
  failure is criterion 3 alone and the reference also fails criterion 3, the table says "balanced except
  deaths, as today"; that label is **reported, not forwarded**, and the decision returns to the user and
  PI — no threshold moves after the data are read.
- **If the reference itself fails criteria 1, 2 or 5**, the trained-agent criteria are not able to
  recognise today's world, which the balance study called balanced; that is reported as a finding about
  the criteria and the decision returns to the user.

### 4.7 Failure modes decided in advance

- **Run crashes / NaN / calibration mismatch:** the run is invalid, not the world; re-launch once with the
  same tag suffixed `_r2` after cause is found.
- **Wall-clock:** 20 × 20 runs may be 2–3× slower (more entities per step, possibly longer episodes);
  no run is cut short to save time — a run that has not reached 2.0 M episodes has no verdict.
- **Still learning:** undecided (4.4), not failed.
- **Edge worlds collapse early** (survival far below the reference by episode 0.5 M): expected by the
  simulation; the run continues to 2.0 M so the agreement table has a trained value.

### 4.8 Validation performed (2026-09-27, live loader, project interpreter)

A scratch validator (session scratchpad, not committed; same approach as the body-interaction study's
§3.2) did, for each of the seven worlds:

- loaded the repo file through `load_env_config` → `load_env_params`, and the simulation's world file
  the same way: **the two `EnvParams` are identical field by field** in all six new worlds, and level 05
  equals the simulation's `g10r20f1to4b12_od` world field by field;
- replayed `train.py`'s single-config merge order (default → train/default → train/recurrent_ppo →
  evaluation → logger → visualization → world → `nmngaenorm_t1none.yaml`): `balance_metrics` = true,
  early-death cut-off = 20, and the `EnvParams` built from the merged config equal the stand-alone ones;
- reset each world **300 times** (keys 0–299) and asserted the plan's per-reset checks with Part 3's own
  `check_resets`: (1) every entity and resource type spans the grid to within one cell of each edge the
  inset allows — pass; (2) no active slot sits at (0,0) where its placement box excludes (0,0) — pass
  (0,0 lies inside every 1-based `[[1,1],[G,G]]` box except the campfire's inset one, so only fires can
  show the fallback: **0 fires at (0,0)** in every world); (3) fires placed = drawn: every active fire
  inside its inset box and at least `min_fire_separation` 4 apart on 300 / 300 resets — pass (fires per
  reset: 10 × 10 1–3, 15 × 15 2–7, 20 × 20 4–12; no world is fire-capped);
- **observation width 58 in every world, equal to level 05's** (the width does not depend on grid or
  smell range);
- grid size and smell range as named.

The load-time diff against level 05 contains only the food / hiding-predator slot arrays and, for the
10 × 10 worlds, `sensor_radius`; the 15 × 15 and 20 × 20 worlds add grid size, location map and every
entity / obstacle slot array (counts and boxes scaled). Body, thermal, reward and sensor fields are
identical. `tests/env/test_channel_names_match_configs.py` and `test_backward_compat_configs.py` on
the new folder: 6 passed, 6 skipped (the usual `extends:` skip).

**Critical-settings registry:** `sensory.sensor_radius` differs from canonical 20 in **four** of the
six new files (5, 5, 3, 8: `g10r5f1to2b36`, `g20r5f4to16b12`, `g10r3f1to2b36`, `g15r8f1to2b36`); the
other two (`g20r20f1to4b12`, `g20r20f1to2b36`) keep 20. Change-log entry in `CONFIG_CRITICAL_SETTINGS.md`.
*(Corrected in Part 4 Revision 1; the original sentence said "three of the new files (5, 3, 8)". The
load-time diff sentence above is likewise corrected there: `sensor_radius` also differs in the 15 × 15
and 20 × 20 short-smell worlds, not only the 10 × 10 ones.)*

### 4.9 Launch Manifest

Group `context_exploration`, job type `pilot`, Tag = WandB name, always. Node, GPU, launch time, WandB
id and log path are filled by `training-runner`. Tags are unique; no `results/JAX_RecurrentPPO/`
directory contains `ctxexp` (checked 2026-09-27).

| Run | Status | World | Tag (= wandb-name) | wandb-group | wandb-job-type | Seed | Node | GPU | Launched at | WandB run ID | Log path |
|---|---|---|---|---|---|---|---|---|---|---|---|
| C1a | running | 1 reference | `rppo_ctxexp_lvl05ref_t1none_s42` | context_exploration | pilot | 42 | 102 | cuda:0 | 2026-09-27T18:57:03 | `v4tbwrfn` | `logs/20260927_185703.log` · HEAD `1d3a3d0f` |
| C1b | running | 1 reference | `rppo_ctxexp_lvl05ref_t1none_s43` | context_exploration | pilot | 43 | 105 | cuda:1 | 2026-09-27T19:12:05 | `qxz17vr0` | `logs/20260927_191205.log` · HEAD `ff78d2e6` |
| C2 | running | 2 balanced | `rppo_ctxexp_g10r5f1to2b36_t1none_s42` | context_exploration | pilot | 42 | 113 | cuda:1 | 2026-09-27T20:12:20 | `bci9fvu6` | `logs/20260927_201220.log` · HEAD `32c22c8b` |
| C3 | done 2026-09-27T20:09 | 3 balanced | `rppo_ctxexp_g20r20f1to4b12_t1none_s42` | context_exploration | pilot | 42 | 102 | cuda:1 | 2026-09-27T18:47:47 | `whpmbq6l` | `logs/20260927_184748.log` · HEAD `a90eb973` |
| C4 | running | 4 balanced | `rppo_ctxexp_g20r5f4to16b12_t1none_s42` | context_exploration | pilot | 42 | 113 | cuda:0 | 2026-09-27T18:47:51 | `7ctxxltq` | `logs/20260927_184752.log` · HEAD `a90eb973` |
| C5 | done 2026-09-27T20:04 | 5 balanced | `rppo_ctxexp_g20r20f1to2b36_t1none_s42` | context_exploration | pilot | 42 | 113 | cuda:1 | 2026-09-27T18:47:55 | `f8o1wgdw` | `logs/20260927_184755.log` · HEAD `a90eb973` |
| C6 | running | 6 edge | `rppo_ctxexp_g10r3f1to2b36_t1none_s42` | context_exploration | pilot | 42 | 112 | cuda:1 | 2026-09-27T20:12:23 | `5sqbvlko` | `logs/20260927_201223.log` · HEAD `32c22c8b` |
| C7 | running | 7 edge | `rppo_ctxexp_g15r8f1to2b36_t1none_s42` | context_exploration | pilot | 42 | 102 | cuda:1 | 2026-09-27T20:12:16 | `ds54a5nw` | `logs/20260927_201216.log` · HEAD `32c22c8b` |

#### 4.9.1 Configs to Produce

Agent config for every row: `configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml`.

| Run | Env config |
|---|---|
| C1a, C1b | `configs/environment/experiment/basic/05-campfire_thermal_10x10.yaml` (unchanged; no new file) |
| C2 | `configs/environment/experiment/context_exploration/g10r5f1to2b36.yaml` |
| C3 | `configs/environment/experiment/context_exploration/g20r20f1to4b12.yaml` |
| C4 | `configs/environment/experiment/context_exploration/g20r5f4to16b12.yaml` |
| C5 | `configs/environment/experiment/context_exploration/g20r20f1to2b36.yaml` |
| C6 | `configs/environment/experiment/context_exploration/g10r3f1to2b36.yaml` |
| C7 | `configs/environment/experiment/context_exploration/g15r8f1to2b36.yaml` |

The folder is experimental and not maintained (CLAUDE.md "Config maintenance scope"), like
`level05_body_interactions/`; every file says so in its header. Worlds that go forward may later be
promoted into `basic/`.

#### 4.9.2 Launch commands (for `training-runner`, one per row, via `run_command.py`)

```
/home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
  --config <env config from 4.9.1> \
  --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
  --episodes 2000000 --device cuda:<gpu> --log-interval 10 \
  --tag "<tag>" --wandb-name "<tag>" \
  --wandb-group "context_exploration" --wandb-job-type "pilot"
```

Only C1b adds `--seed 43`; every other row uses the config-owned seed 42 and does not pass `--seed`.
Example (C4):

```
/home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
  --config configs/environment/experiment/context_exploration/g20r5f4to16b12.yaml \
  --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
  --episodes 2000000 --device cuda:<gpu> --log-interval 10 \
  --tag "rppo_ctxexp_g20r5f4to16b12_t1none_s42" --wandb-name "rppo_ctxexp_g20r5f4to16b12_t1none_s42" \
  --wandb-group "context_exploration" --wandb-job-type "pilot"
```

**Pre-flight discriminators for the runner** (from each run's banner / stdout / saved `models/config.yaml`):
- banner prints `Loading rPPO train defaults from …/configs/train/recurrent_ppo.yaml` and observation
  width **58**; `Neuromodulation: DISABLED`;
- stdout calibration record as in 4.3;
- saved config: `environment.height`/`width` = the row's grid, `sensory.sensor_radius` = its smell range,
  food `count_low`/`count_high`/`max_consumption` as in 4.2, `logging.episode.balance_metrics: true`,
  `balance_early_death_max_steps: 20`;
- record `git rev-parse HEAD` per row.

**When / where.** Not before the running level-05 runs free their GPUs, after the pre-launch PI
consultation and the user's go. Mid-tier cards (RTX 3090), packed node by node. Compute: 10 × 10 about
2 h per run on a 3090 (level-05 pilots); 15 × 15 / 20 × 20 plausibly 3–6 h; total about 25–35 GPU-hours.

## Feedback from plan-reviewer — Part 4 design (Revision 3, commit `ff37eff5`), before launch

**Verdict: SOUND WITH CONCERNS.** No Critical finding; five Moderate, four Low, five open assumptions.
Nothing here needs code. Every item is a sentence in this section or a pre-launch check.

**In plain words.** The eight training runs are well specified and every number the criteria need
is actually logged. The risks are in how the verdicts will be *read*: the deaths criterion sits within a
few points of its line for today's world, so the forward rule can predictably end in "nothing goes
forward" with no rule for what happens then; the trust verdict on the simulation can blame the
simulation for a criterion that simply does not transfer to trained agents; and the fixed episode
budget gives worlds that die sooner less training, which leans the survival comparison toward
confirming the simulation. On the budget question the evidence supports **2 M episodes for all eight
runs** plus a concrete extension path — not 5 M for the larger grids alone.

Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run ·
🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

### Findings

| # | Sev | Where | Issue | Suggested fix | Owner |
|---|---|---|---|---|---|
| M1 | 🟡 | 4.4 crit. 3, 4.6 | The three level-05 pilots (`LEVEL05_BODY_INTERACTIONS.md` §6, P0a–c) put injury at ≈ 57–59 % of **all** deaths; criterion 3 is judged on deaths **after step 20** (`Bal_LateDeath_*`, `balance_metrics.py:297-320`), and removing early deaths moves the injury share in a direction nobody has measured. Seed spread on cause shares in those pilots is ≈ 1 point (starvation 0.261–0.268), so 57–59 vs 60 is not sampling noise, but it is inside the recount's reach. If the reference fails 3, 4.6 says every "fails 3 only" world is reported, not forwarded — a predictable dead end with no rule for the next step, and "no threshold moves after the data are read" forbids fixing it later. | Pre-register now, one of: (a) criterion 3 is judged **relative to the reference** — a world fails 3 only if its dominant late-death cause exceeds max(60 %, the reference's own share); or (b) criterion 3 is pass/fail in the agreement table but **report-only for forwarding**. Say which. | experiment-designer |
| M2 | 🟡 | 4.5 summary rule | Trustworthiness counts criteria 1, 2, 5 against the simulation even when the reference itself fails them in training (4.6's last bullet admits that case). Criterion 1's `Bal_TimeWarm ≥ 10 %` is the likely one: the balance study found the ideal agent holds temperature like a thermostat, and the metrics plan's A4 says diagonal cells near the fire count as "elsewhere". If the reference fails a criterion, 0 / 6 agreement would read as "simulation not trustworthy" when the criterion is what did not transfer. | Gate: a criterion the reference fails in training is **excluded** from the agreement count for every world (verdict withheld for it); the summary is then stated over the remaining criteria. | experiment-designer |
| M3 | 🟡 | 4.4 env steps, 4.5 direction | A per-episode budget gives fewer gradient updates to worlds that die sooner: at the simulation's ratios the edge worlds get ≈ 35 % fewer environment steps than the reference for the same 2 M episodes. That leans criterion 4 toward confirming the simulation's edge failure and against ever finding it "too pessimistic". The per-1,000-steps "death-rate view" is 1,000 ÷ mean survival steps — the same number rearranged, not an independent view. | State the update-count confound and its direction next to the agreement table; report the step ratio per world; drop or relabel the death-rate view. | experiment-designer |
| M4 | 🟡 | 4.3 budget, 4.4 still-learning | **2 M vs 5 M.** Level 05 at 2 M rises ≈ 2.5 % over the last fifth (P0a tenths 220, 225 → 228), so the > 5 % flag would *not* fire — yet the Wave-2 10 M run shows ≈ 10 % still to come (230 at 1.8 M → 252 at 10 M). The flag catches steep learning, not incomplete learning; harsher 10 × 10 pilots sit at the line (P08 + 4.2 %, P09 + 5.8 % over the last tenth). No 15 × 15 / 20 × 20 training exists in the project (wiki and experiments checked), so grid-size learning speed is unmeasured. **5 M for the larger grids only is the one option the evidence argues against**: criterion 4 would compare a 5 M world against a 2 M reference (the reference alone gains ≈ 5 % by 5 M), and the agreement table would mix budgets across arms. | Keep 2 M for all eight (matched to the reference and to the P0 pilots). Pre-register the extension as a command, not an intention: `--load-checkpoint <2 M checkpoint> --episodes 5000000 --wandb-resume-id <id>`, **the reference extended alongside any extended world**, and a one-off check that the resumed survival curve is continuous across the 2 M seam (Known Bugs: rPPO resume H1 FIXED; B5 "restored memory + fresh worlds" OPEN-latent, first post-resume window only). If 5 M is chosen, it is 5 M for all eight (≈ 2.5 × ≈ 65–90 GPU-h). Also say the flag compares two 200 k-episode windows (1.6–1.8 vs 1.8–2.0 M) and that "not still learning" means "not steeply", not "converged". | experiment-designer / user |
| M5 | 🟡 | 4.3 borderline, 4.6 priority | An edge world passing criterion 4 on one seed would be a ≥ 15-point simulation miss and, by 4.6, would **lead** the modulator comparison — on n = 1. The borderline test uses the reference's two-seed gap, which under-estimates the spread (one |Δ| from two seeds is below 0.4 σ a quarter of the time; the level-05 review's M1 said the same). | Any world whose trained criterion-4 verdict **disagrees with the simulation** gets a seed-43 run before forwarding, borderline or not; give the borderline band a floor (e.g. 5 points on shares / ratios, 5 % relative on survival) in addition to the seed gap. | experiment-designer |
| L1 | 🟢 | 4.2 last para, 4.5 | "Sim criterion 3 fails in every world" is false for the Revision-2 table: nine rows read `11101` (pass 1, 2, 3, 5; fail only survival — e.g. `g15r8f1to4b12_od` 14.9, `g15r5f2to4b12_od` 17.1, `g20r8f2to6b12_od` 17.4 steps). It is true for the seven chosen worlds, and the chosen set itself checks out against the table (the four longest searches among `11011` worlds are 11.8 / 11.5 / 9.4 / 9.3; the 9.7-step world is `11001`). The "a third such world … 20.5" aside is incomplete (`g20r3f4to16b12_od` 19.7 and the four `11101` worlds also miss only 4) — the pick is unchanged. | Reword to "in all seven chosen worlds"; note that the simulation does pass criterion 3 in four `_od` worlds that miss only survival, in case a criterion-3-passing comparator is wanted later. | experiment-designer |
| L2 | 🟢 | 4.4 window | Episode rows overlap: smoothing 5,000 / interval 4,000 episodes (`configs/train/recurrent_ppo.yaml:53,56`), so "difference of `Episode/Number`" (4,000) ≠ `Episode/_window_n` (5,000) and summed `Bal_N_*` counters count each episode ≈ 1.25 ×. Ratios of pooled sums are unaffected in steady state; summed `N` must not be quoted as an episode count. A ratio omitted in one row (zero bin, A6) is not the failure condition — a zero **pooled** denominator is. | Say which weighting is used (the P0 pilots used `_window_n`), and state the pooled-zero rule. | experiment-designer |
| L3 | 🟢 | 4.9.2 pre-flight | Add the top-level `seed:` to the saved-config discriminators for C1b (Known Bugs 2026-09-04: the nested copy always reads 42). Add "first Episode row carries ≥ 49 `Episode/Bal_*` keys" — 4.8's merge replay is a re-derivation; the row is what the system produced. `timesteps` is logged on iteration rows and `Episode/*` against `Episode/Number` (`train.py:1052-1055`); say how the two are joined (nearest `_step`). | Three lines in 4.9.2. | training-runner / experiment-designer |
| L4 | 🟢 | 4.3 reference | C1a / C1b are seed-42 / 43 twins of the P0a / P0b level-05 pilots (228.3 / 225.8 survival steps at 2 M, same agent config, same world; HEAD differs by the balance-metrics merge whose golden test reported unchanged dynamics). That is a free replication gate on the trainer before any world is judged. | Pre-register: C1a within ± 3 × 1.5 of 228.3 and C1b of 225.8; a miss stops the read-out and goes to `senior-developer` as code drift. | experiment-designer |

### Criterion computability (checked against the code, not the plan)

Every key the five criteria and the still-learning flag need is emitted by `window_log` / `late_death_log`
(`src/behavior/balance_metrics.py:230-320`) and `_emit_episode_row` (`train.py:1590-1650`): the four
time shares (+ `TimeNearFire`, `TimeWarm` present because thermal is on), `EatRatio`, `HideRatio_True`,
`HideRatio_True_Fed`, `WarmRatio`, the `N_*` counters for pooling, `EarlyDeathShare`, `LateDeathShare`,
`LateDeath_{Starvation,Overeating,Injury,Thermal}`, `Episode/Steps`, `Episode/Number`, `_window_n`,
`timesteps`. Late-death counts per row are `LateDeathShare × _window_n`. Nothing is "not measured in training".

### Open assumptions

- ❓ O1 The reference's **late** injury share: unknown; the direction of the early-death recount decides M1.
- ❓ O2 How fast a 20 × 20 world learns per episode: unmeasured anywhere in the project (M4).
- ❓ O3 The rPPO resume path has not been exercised in this study family since the H1 fix (M4).
- ❓ O4 Whether a trained agent spends ≥ 10 % of steps on a warm cell (`Bal_TimeWarm`): the criteria have never been applied to a trained agent; the reference run is the first test (M2).
- ❓ O5 20 × 20 wall-clock (4 × entities per step) is a guess; no run is cut short, so this is cost, not validity.

### Passes with nothing to report

Departure from Revision 1 is disclosed (4.1) and the selection rule reproduces from the Revision-2 table.
Survival steps is the metric throughout; reward is never read. Budget is passed on the CLI (`--episodes`).
No data-loss hazard (no git operation in the plan). Registry change-log entry for `sensor_radius` is in
the same commit; nothing under `scripts/` changes. Known Bugs: the cross-batch level hazard is honoured
by an in-batch reference; the stale saved seed / budget copy is covered by L3; nothing unrecorded found.
Observation width 58 in every world, no new sensor; mechanical YAML validation is `env-config-reviewer`'s
(not yet run on the new folder as far as `docs/reviews/` shows). Pass 7 skipped (not an analysis verdict).

### Cost of being wrong

Misjudging a world costs ≈ 25–35 GPU-hours and a day. The expensive failures are the two that are free
to fix now: forwarding a single-seed, simulation-disagreeing pass into a ≥ 3-seed modulator comparison
(weeks), or a predictable "nothing passes criterion 3" that returns the decision with no rule attached.

Reviewed by: plan-reviewer (2026-09-27, on `ff37eff5`)

## Part 4 Revision 1 (2026-09-27) — answers to the plan review of the Part 4 design and to env-config-reviewer, before any launch

**In plain words.** The reviewers found no error in the eight runs themselves, but several places where
the way the results will be *read* was not fixed in advance. This note fixes them now, before any run
exists, so no rule can be bent after the numbers are seen. The main changes: (1) today's world is
itself expected to have its late deaths dominated by one cause (mostly injury), so the deaths test used
to decide which worlds move on is now judged *relative to today's world* rather than against a fixed
60 % line; (2) a test that today's world fails in training is not held against the simulation when
judging whether the simulation can be trusted; (3) the fixed budget of 2 million episodes gives worlds
where the agent dies sooner fewer learning updates, which tilts the survival comparison toward agreeing
with the simulation — that bias is now stated and measured per world; (4) the budget stays 2 million
episodes for all eight runs, with an exact command for extending any world (and today's world with it)
to 5 million if it is still improving; (5) a world whose survival verdict contradicts the simulation
needs a second seed before it can lead the next study. Everything in 4.1–4.9 stands unless changed here.

### R1.1 Criterion 3 for forwarding is reference-relative (M1)

- **Criterion 3 as written in 4.4 (absolute, 60 % line) stays** and is reported in the agreement table
  and every world row.
- **Criterion 3-fwd** replaces it in 4.6 (what goes forward) only. Let `D_w` = the world's largest
  late-death cause share (the max of `Bal_LateDeath_{Starvation,Overeating,Injury,Thermal}` from the
  pooled window, R1.6) and `D_ref` = the same quantity for the reference, mean of C1a and C1b. A world
  **passes 3-fwd** if its late-death share (`Bal_LateDeathShare`) is below 5 %, **or**
  `D_w ≤ max(60 %, D_ref + 5 points)`. Margin 5 points: five times the ≈ 1-point seed spread of cause
  shares in the level-05 pilots, and equal to the borderline floor in R1.5.
- The dominant cause's *identity* is reported beside `D_w` (a world whose late deaths are 85 %
  starvation against a reference at 85 % injury passes 3-fwd, but the switch is stated as a finding).
- The reference passes 3-fwd by construction. 4.6's "balanced except deaths, as today — reported, not
  forwarded" label is withdrawn; a world that fails absolute 3 but passes 3-fwd is forwarded as
  "trained-balanced relative to today", and that wording is used downstream.

### R1.2 Criteria the reference fails are excluded from the agreement count (M2)

- A criterion among 1, 2, 5 that the reference fails in training (on the pooled C1a + C1b values, or
  on either seed alone — any reference failure excludes it) is **withheld for every world** in 4.5:
  no agreement or disagreement is scored on it; the trained pass/fail is still printed.
- Criterion 4 cannot be excluded (the reference is 1.0 by construction).
- Agreement per world is then "same pass/fail on all remaining criteria". The trust rule of 4.5
  (≥ 5 of 6 non-reference worlds agree **and** both criterion-4 directions hold) is kept, stated over the
  remaining criteria, and the summary names which criteria were withheld. If criteria 1, 2 and 5 are all
  withheld, the trust verdict rests on criterion 4 alone and is labelled "survival-only".
- A withheld criterion is also dropped from "trained-balanced" in 4.6 for forwarding, with the same
  label; per 4.6's last bullet this is reported as a finding about the criteria and goes to the user.

### R1.3 The per-episode budget and the update-count confound (M3)

- A 2 M-episode budget gives a world whose agent dies sooner fewer environment steps and so fewer
  gradient updates. At the simulation's survival ratios the edge worlds get roughly 35 % fewer steps
  than the reference. **Direction:** this lowers a slow world's trained survival, so it leans
  criterion 4 toward *confirming* the simulation's edge failure and against finding the simulation
  "too pessimistic". An edge world that fails criterion 4 is therefore weak evidence for the simulation;
  one that passes is strong evidence against it.
- **Reported per world, next to the agreement table:** step ratio = environment steps at 2.0 M episodes
  ÷ the reference's (mean C1a / C1b), from WandB `timesteps` (R1.6 join rule).
- **The "per 1,000 environment steps" survival view in 4.4 is dropped.** It is 1,000 ÷ mean survival
  steps — the same number rearranged, not an independent view.

### R1.4 Budget: 2 M for all eight, and the extension path (M4 — decided)

- **Decision:** 2,000,000 episodes for all eight runs (parent decision following the reviewer; the user
  was offered 5 M for the large grids and has not objected). No arm runs a different budget.
- **What the still-learning flag means:** it compares two 200,000-episode windows (1.6–1.8 M vs
  1.8–2.0 M); "not still learning" means "not improving steeply", **not** "converged" — level 05 itself
  gains ≈ 10 % between 2 M and 10 M while its last-fifth rise is ≈ 2.5 %.
- **Extension, triggered by the still-learning flag on any world, with the user's approval:** that world
  **and both reference runs (C1a, C1b)** are resumed to 5,000,000 episodes (`--episodes` is the total
  target; the loop runs while completed episodes < `--episodes`). Per run, same tag, same node class:

```
/home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
  --config <env config from 4.9.1> \
  --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
  --load-checkpoint results/JAX_RecurrentPPO/<run dir>/models/<highest episode-numbered checkpoint dir, ≥ 2000000> \
  --episodes 5000000 --device cuda:<gpu> --log-interval 10 \
  --wandb-resume-id <the run's WandB id> \
  --tag "<same tag>" --wandb-name "<same tag>" \
  --wandb-group "context_exploration" --wandb-job-type "pilot"
```

  (C1b adds `--seed 43`.) Checkpoints are saved every 200,000 episodes as episode-numbered
  directories under `models/`. **Seam check, before reading any extended value:** survival steps in the
  first two logged 200 k-episode blocks after the resume are within the pre-resume block's value ± 5 %;
  a break goes to `bug-curator` / `senior-developer` (Known Bugs: rPPO resume H1 fixed; B5 "restored
  memory + fresh worlds" affects the first post-resume window only). Extended worlds are then judged on
  4.9–5.0 M against the extended reference on 4.9–5.0 M; the 2 M verdicts stay in the table beside them.
  If more than half the worlds are flagged, all eight are extended (≈ 65–90 GPU-h).

### R1.5 Second seed for simulation-disagreeing survival verdicts; borderline floor (M5)

- **Any world whose trained criterion-4 verdict disagrees with the simulation's** (an edge world ≥ 80 %
  of the reference, or a balanced world < 80 %) gets a seed-43 run before it can be forwarded or lead the
  modulator comparison, borderline or not. The 4.6 rule "an edge world that turns out trained-balanced
  goes first" applies only if the seed-43 run also passes criterion 4 and 3-fwd.
- **Borderline band** = the larger of the reference's seed-42 / 43 gap and a **floor of 5 points** on
  time shares and late-death shares, **0.5** on ratios (eat / hide), and **5 % relative** on survival.
- Extra seed runs take new manifest rows `C<n>b`, tag `rppo_ctxexp_<slug>_t1none_s43`, same group and
  job type; each needs the user's go (≈ 2–6 GPU-h each).

### R1.6 Lows (L1–L4)

- **L1 — false sentence corrected.** 4.2's "Sim criterion 3 fails in every world, the reference
  included" should read "**in all seven chosen worlds**". In the full Revision-2 table the simulation
  does pass criterion 3 in several density-matched worlds that miss only survival (pattern `11101`, e.g.
  `g15r8f1to4b12_od` 14.9, `g15r5f2to4b12_od` 17.1, `g20r8f2to6b12_od` 17.4 search steps), available
  later if a criterion-3-passing comparator is wanted. 4.1's "a third such world, 20.5 steps" aside is
  incomplete (`g20r3f4to16b12_od` at 19.7 and the `11101` worlds also miss only criterion 4); the pick
  is unchanged.
- **L2 — window weighting.** Logged rows overlap (smoothing window 5,000 episodes, logged every 4,000).
  Each row in 1.8–2.0 M is weighted by its `Episode/_window_n` (as in the level-05 pilots), replacing
  4.4's "difference of `Episode/Number`"; time shares are weighted by `_window_n × Episode/Steps`; summed
  `Bal_N_*` counters are pooling weights only and are **never quoted as episode counts** (≈ 1.25 ×
  double-count). A ratio missing from one row (empty bin) is not a failure; a ratio is "not computable"
  and fails only if its **pooled** denominator over the window is zero.
- **L3 — pre-flight additions for `training-runner`** (added to 4.9.2's discriminators):
  (a) C1b's saved config shows **top-level** `seed: 43` (the nested `training.seed` always reads 42 —
  Known Bugs, stale saved seed/budget copy); likewise the saved config's `training.episodes: 100` is
  that stale copy — the budget (2,000,000) is verified from the WandB run config or the log banner;
  (b) the **first logged Episode row carries ≥ 49 `Episode/Bal_*` keys** (the system's own output,
  not 4.8's merge replay);
  (c) `timesteps` (iteration rows) is joined to `Episode/*` rows (keyed by `Episode/Number`) by nearest
  WandB `_step`.
- **L4 — replication gate on the trainer.** C1a and C1b are seed-twins of the level-05 pilots P0a / P0b
  (228.3 / 225.8 survival steps at 2 M, same world and agent config). Pre-registered: C1a must be within
  228.3 ± 4.5 and C1b within 225.8 ± 4.5 (3 × the ≈ 1.5-step pilot spread). A miss stops the read-out
  for every world and goes to `senior-developer` as possible code drift.

### R1.7 env-config-reviewer notes

- **Smell-range count corrected** in 4.8 and in `CONFIG_CRITICAL_SETTINGS.md`'s 2026-09-27 entry:
  **four** files differ from 20 (`g10r5f1to2b36` 5, `g20r5f4to16b12` 5, `g10r3f1to2b36` 3,
  `g15r8f1to2b36` 8); two keep 20 (`g20r20f1to4b12`, `g20r20f1to2b36`). 4.8's load-time diff sentence
  ("for the 10 × 10 worlds, `sensor_radius`") should read: `sensor_radius` differs in the four
  short-smell worlds of any grid size.
- **Launches staggered by more than 1 second** (Known Bugs: a fast batch launch collapses several runs'
  log files into one, because `run_command.py` names logs at one-second resolution). The runner waits
  ≥ 2 s between rows and confirms one distinct log path per row in the manifest.
- **Saved config `episodes: 100`** is the known stale nested copy (L3a); never read the budget from it.

Revised by: experiment-designer (2026-09-27, on `5e6f82e3`)
