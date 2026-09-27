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
