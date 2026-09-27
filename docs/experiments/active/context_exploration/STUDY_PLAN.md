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
