# Rebalance planner — pre-registration record

**What this is.** The rule used to judge whether each candidate world offers a real choice between hiding in a
bush and going out to eat, copied verbatim from the study's working notes so the page
[[hide_or_forage_balance]] can cite a path under version control. The original file,
`tmp/20261011_233031_rebalance_planner.md`, is scratch space and not tracked by git; nothing below was edited
except this introduction, the timeline, and the copied headings demoted one level.

## Timeline (from file timestamps, Asia/Seoul)

| when | what |
|---|---|
| 2026-10-11 23:30:31 | working notes created with the pre-registered rule below (the time is the file's name) |
| 2026-10-11 23:38:42 | first world results written (planner run log) — after the rule |
| 2026-10-12, before 00:07 | exploratory lever-sweep note appended (section 2 below), before the world-8 sweep finished at 00:07:44 |
| 2026-10-12 | revision: group A "+" = exactly one predator (was 0–1), made after the first results were read; the rule did not change and the verdict did not change |
| 2026-10-12 01:38 | at the verdict review, added without a prior note: the lever sweep from world 4, the discount-0.99 check for worlds 4 and 8, and the hungry-start-states view (first computed after the first results) — all labelled exploratory or sensitivity on the page |

**Known departure.** The rule says 2,000 rollouts; the code ran 4,000 per map, which only narrows the error.

## 1. Pre-registered reading rule (verbatim)

### Question
In each of 8 half-factorial candidate worlds (lookalike base; groups A predator threat, B food economy,
C hazard concealment, D hazard load) + level 05 reference, does the ideal planner face a real choice
between hiding in the bush and going out to forage, or does one option always win?

### Pre-registered reading rule (written BEFORE any rebalance result was computed)
- Decision balance = share of training start states (food 0-200, injury 0-100, body temp -10..+5,
  agent on open ground "O") whose best choice category is (a) rest in cover [go/stay bush, incl. warm bush],
  (b) eat [go to food / eat], (c) other [warm up, stay in the open]. Ties NOT excluded (margin 0);
  pooled over the two maps (no warm bush 0.59 / warm bush 0.41), as in the old study.
- A world OFFERS A REAL CHOICE iff share(a) >= 20 % AND share(b) >= 20 %.
- Secondary (reported, not used for the verdict): the same shares at tie margin 0.5 with ties removed;
  the shares from inside a cold bush (place "B": stay vs leave); per-map shares.
- Survival = share of 2,000 rollouts (random training-style starts at open ground) alive at step 500.
- Group main effect = mean over the 4 "+" worlds minus mean over the 4 "-" worlds (half factorial,
  resolution IV: main effects aliased with 3-way interactions; 2-way interactions aliased in pairs).
No threshold will be changed after results are read.

## 2. Exploratory lever sweep note (verbatim; not pre-registered)

### EXPLORATORY lever sweep — NOT pre-registered (written before any sweep result was computed)
Purpose: what single change, starting from world 8 (++++, revised A), would make both hide and forage
>= 20 % of start states (the same yardstick as the pre-registered rule, used here descriptively only).
Levers, one at a time, everything else at world 8:
  predator hit odds x0.5 and x2 (all activities)
  trip to food 4, 6, 8 steps (world 8 = 5)
  bush healing multiplier 12.5 and 5 (today 25) -- PLANNER ONLY, "for understanding only": training
  bush healing stays fixed per the user's rule; this is not a proposal to change it.
No lever value will be added or changed after the results are seen. Also exploratory: the hungry-states-only
decision balance (food < 100), reported for every world.
