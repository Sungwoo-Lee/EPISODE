---
title: "Placement fixes: regrown food only on free cells, no silent cell-(0,0) parking, unused slots out of the way, and a skippable auto-reset"
topic: env_entities
status: active
created: 2026-10-01
last_updated: 2026-10-01
aliases: [placement_fixes_plan]
---

# Placement fixes: regrown food only on free cells, no silent cell-(0,0) parking, unused slots out of the way, and a skippable auto-reset

> **Status**: PLANNED — draft, awaiting `plan-reviewer` and the user decisions in §0
> **Opened**: 2026-10-01
> **Related**: [[THIRST_WATER_PLAN]] (decisions 13 and 17: the measured cost of respawn-draw forms) ·
> [[OPEN_WORK_HANDOFF]] item E2 (food-vs-fire separation, deferred to an entity-allocation rewrite) ·
> [[IMPLEMENTATION_PLAN]] (thermal) D2/D3 · [[BUSH_FIRE_CLEARANCE]] · [[KNOWN_BUGS]] row ~117 ·
> [[THIRST_PILOT]] (the seven runs reading this worktree today)

---

## Context

The grid world places its objects — food, rocks, bushes, campfires, a pond, animals — at the start of
every episode, and puts food back on the grid during the episode after it has been eaten up. A
measurement on 2,000 real episode starts of the campfire world and the pond world (levels 05 and 06)
found the start-of-episode placement sound, but three defects around it:

1. **Regrown food ignores what is already there.** When a food item comes back, it picks any cell in
   its area, including a burning campfire (about 2 % of regrowths — food on a ~77 ° cell the agent
   cannot reach alive), a bush (about 7 %), any obstacle (about 18 %); counting other food and the
   agent's own cell too, about 28 % of regrowths land on a taken cell.
2. **A silent failure mode.** If an object's area is full, it is quietly put at the top-left corner
   cell, outside its own area, with no error. Nothing triggers it today, but nothing proves it cannot.
3. **Unused objects still take up room.** Levels draw a random number of each object per episode
   (for example one to three campfires). The unused slots still claim cells — and unused campfires
   still keep other campfires away — during placement, before being removed from the grid.

This plan fixes all three, cheaply (the user set a 3 % speed budget), and adds an optional speed-up
(E): the PPO trainers build a fresh episode start for every one of 128 parallel worlds on every step,
even when no world has ended — measured here at about nine-tenths of the environment's work per
step. Where the agent *starts* is deliberately left random, overlaps
included (user decision). §0 lists what the user must decide before work starts.

**Timing.** Seven pilot training runs (`rppo_l06pilot_*`, expected to finish about 16:30 KST on
2026-10-01) load code from this worktree while they run. **Implementation must not start in this
worktree until all seven have finished**, or it must happen in a separate worktree (see §3.0).

---

## 0. Decisions for the user (recommendations in bold)

| # | Question | Options | Recommendation and why |
|---|---|---|---|
| U1 | When food regrows, may it land on the agent's own cell? | exclude / allow | **Exclude.** Food comes back the step after the agent finishes it, usually while the agent still stands there; food that reappears under its feet is food it never had to find. Cost: one extra entry in the occupied list. |
| U2 | May it land on an animal's cell? | exclude / allow | **Allow.** Animals walk over food all the time (food does not block them), so an overlap at the moment of regrowth is as brief as any other; excluding animals would only make food avoid wherever animals happen to stand that step. |
| U3 | If two items are due to regrow on the same step | regrow both (needs a sequential draw) / **regrow the lowest-numbered one, the other on the next step** | **One per step.** It keeps the draw a single number per step. In the maintained levels it never fires: food is the only resource that runs out, and with a regrowth delay of 0 two items fall due together only if they were used up on the same step, which needs two items on one cell — impossible once (1) is fixed. |
| U4 | Does `food_min_fire_distance` (keep food at least M cells from a fire) also apply to regrown food? | yes / no | **Yes.** Today the setting protects only the episode's first food layout; every regrowth can undo it. With M = 0 (every level today) the extra check is compiled out, so it costs nothing until someone turns it on. Its value stays 0 — choosing a value is still open item E2. |
| U5 | How to make the corner-cell fallback impossible | (a) check at load time and refuse any world it cannot prove / (b) at run time, drop an object that does not fit and count it, in every world / **(c) both: prove at load where possible (zero run-time cost), and only in worlds that cannot be proved compile in the drop-and-count backstop, with a load-time warning** | **(c).** Placing campfires first lets an exact check prove all 11 maintained levels (§A3, §3.1). But 17 unmaintained worlds in two folders other studies use (`continual_worlds`, `context_exploration`: 15 × 15 and 20 × 20 grids with up to 7–12 campfires) cannot be proved — with that many fires a bad layout of the first few really can leave no room for the next, although 2,000 resets of three of them never hit it. Refusing them (a) would break those studies over an event never observed; (b) would charge every world for a check only those 17 need. |
| U6 | The 3 % speed budget for A+C+D, measured on the bare environment | keep as the pass/fail line / judge on whole-training speed instead | **Keep it as written, and expect to be asked again.** The CPU gets much *faster* with every prototype (+15 to +34 %). The GPU is the problem: every exact prototype so far costs 4.5–14 % of the bare environment step (§A7), so A will probably miss 3 % on the GPU. But the bare step is only about 2–3 % of an rPPO training step, so 11 % of it is about 0.3 % of training time. If no form meets 3 % on the GPU, the developer stops with the full table and the end-to-end numbers (§3.6), and the user decides then. |
| U7 | Part E (skip the reset build when no world ended) | keep if faster and identical / drop | **Measure, keep by the pre-registered rule (§3.4).** The full reset turned out to be ~90 % of the environment's per-step work (§A6); skipping it could make rPPO training roughly 10–18 % faster once episodes are long. |
| U8 | Existing trained runs and recordings were made under the old placement | — | Nothing to decide now; read §5 before comparing runs from before and after this change. |
| U9 | What a dropped object means, in the worlds that get the backstop (U5 c) | the object is simply absent this episode (like an unused slot) and the episode's drop count is recorded / re-draw the episode | **Absent and counted.** It is the same state an unused slot already has, so every consumer handles it; the count lets an analysis check it stayed at zero. A re-draw would need a loop of unknown length inside the reset. |

---

## Analysis

### A1. The measurements, re-run for this plan

The parent session's numbers were re-run unchanged by this plan's author
(`tmp/20261001_placement_audit/placement_audit.py`, `respawn_audit.py`; outputs saved next to them as
`placement.txt`, `respawn.txt`). All reproduce:

| What (2,000 resets per level unless noted) | Level 05 (campfire) | Level 06 (pond) |
|---|---|---|
| Two active food/obstacles on one cell at the start | 0.00 % | 0.00 % |
| Any active food/obstacle outside its own area (the cell-(0,0) fallback) | 0.00 % | 0.00 % |
| Agent starts on a burning fire / any obstacle / food / an animal | 1.70 / 16.55 / 8.90 / 1.95 % | 1.85 / 17.60 / 9.55 / 2.00 % |
| Agent starts on the pond | — | 0.00 % |
| A regrowth lands on a burning fire (share of the food area that is fire, averaged over starts) | 2.01 % | 2.09 % |
| … on a bush / any obstacle / an animal's start cell | 6.97 / 17.95 / 2.00 % | 7.26 / 18.69 / 2.08 % |

**How often does food regrow at all?** A food item is used up after it has been eaten **12 times**
(`max_consumption: 12`) and comes back on the very next step (`regeneration_delay: 0` for food; the
other resource type, the hiding predator, has `max_consumption: -1` and never runs out). In the
audit's own 400 random-policy rollouts of 300 steps each, **no item regrew** (`n=0` in
`placement.txt`), so the regrowth rates above are the share of the food area each kind of cell
covers, not observed events. A trained agent eats far more than a random one, so regrowths happen in
training, but how many per episode is not measured. The defect is real; its per-episode weight is
smaller than "18 %" suggests. Because the delay is 0, the agent is usually standing on the cell where
it just finished the item when the new one is placed — which is why U1 matters.

### A2. How regrowth works today (`src/environment/core.py`)

- `update_resources` (`core.py:612-645`) marks a slot due when it is inactive, its timer has reached
  0 and it was allocated this episode (`res_allocated`, the fix for the old "dead slots revive" bug).
- `jax_step` (`core.py:994-1036`) then draws a new cell for **every** slot (16 in levels 03–07),
  whether due or not, and keeps it only where due:
  - water-off worlds: `vmap(randint(key, (2,), area_lo, area_hi))` over `split(respawn_key, 16)` —
    uniform over the area, **no occupancy check at all**;
  - water worlds (decision 17 of [[THIRST_WATER_PLAN]]): one integer per slot over "area minus pond",
    mapped with the rank-skip fixed point — pond excluded, nothing else.
- Nothing reads obstacle, food, animal or agent positions. Hence A1's rows.

### A3. The silent cell-(0,0) fallback, and why a load-time check needs campfires placed first

`resolve_overlaps_global` (`core.py:1461-1565`) and `relocate_blocked_entities` (`core.py:1568-1638`)
take "the first valid cell of one pre-drawn permutation". If no cell is valid, the one-hot sum is 0
and the object goes to flat index 0 — cell (0, 0) — outside its area, silently (KNOWN_BUGS ~117,
open). Two load-time checks exist, each covering one case: the water capacity check
(`config_loader.py:3056-3071`, pond only; it counts slots but not fire-separation zones) and the
bush-clearance bound (`_check_bush_fire_clearance`, `config_loader.py:545-627`).

The placement order is `[food, predators, obstacles, neutral animals]`. In levels 05 and 06 the three
campfire slots sit at scan positions **18, 19, 20** (after 16 food and 2 predator slots), all in a
6 × 6 area (rows and columns 2–7), with `min_fire_separation: 4` (every other fire's cells within
Manhattan distance 3 are forbidden: up to D(4) = 2·4² − 2·4 + 1 = 25 cells each). A worst-case bound
in today's order, of the kind the bush check uses:

| Fire | Cells in its area | − earlier objects (all may be in the area) | − earlier fires' zones | Worst-case cells left |
|---|---|---|---|---|
| 1st | 36 | 18 | 0 | 18 |
| 2nd | 36 | 19 | 25 | **−8** |
| 3rd | 36 | 20 | 50 | **−34** |

So a guaranteed-safe load check in today's order would **refuse the shipped levels 05–07**, even
though the fallback never fired in 2,000 resets. With **campfires placed first** (only the pond
precedes them), an exact enumeration of every legal position of the first two fires (and every pond
location) shows the third fire always has a legal cell: at least **4** in level 05 (712 layouts) and
at least **3** in level 06 (2,640 layouts, 0 dead ends) — `tmp/20261001_placement_audit/c_bound.py`.
After the fires, every other object only needs one free cell in its area, which the plain capacity
count (area − pond − earlier slots) gives with a wide margin (level 05: 100 − 44 ≥ 1).

### A4. Unused slots take part in placement

`count_high` slots are allocated per entry and `_build_activation_mask` (`core.py:1933-1972`) picks
K of them per episode, but the masks are drawn in §7b (`core.py:2312-2341`), **after** placement, and
only then are unused slots parked off-grid at `(height, width)`. During the overlap scan an unused
slot still claims a cell and, if it is a campfire, still forbids its 25-cell zone to later fires. The
food-to-fire pass (D3, `core.py:2077-2101`) also builds its forbidden zone from **every** fire slot,
used or not; the bush pass already uses burning fires only (`core.py:2103-2134`). The activation
draw depends only on `property_key` and fixed config, so it can move before placement **without
changing a single drawn value** — the bush pass already does exactly this for obstacles.

### A5. `food_min_fire_distance` and item E2

`thermal.food_min_fire_distance` is 0 in every level and is applied only at reset (D3 above).
[[OPEN_WORK_HANDOFF]] E2 records that about 29 % of campfire-world episodes put food within one cell
of a fire (an episode with no warmth-versus-food trade-off), that `2` is the smallest value that would
bind, and that the user deferred the question into "a general entity-allocation rewrite". This plan
is **part** of that rewrite (regrowth, feasibility, unused slots), not all of it. It does **not**
choose a value for the setting. It makes the setting mean what its name says (U4), so that if E2
later sets it to 2, regrowths cannot quietly undo it. E2 stays open, reduced to "choose the value";
the handoff entry gets a dated note saying so (§3.7).

### A6. The auto-reset cost (part E)

| Caller | Today | Can skip when nobody finished? |
|---|---|---|
| rPPO `collect_trajectories` (`src/models/recurrent_ppo_trainer.py:334-350`) | inside the rollout `lax.scan`, builds `vmap(jax_reset)` for all envs every step, then `where(done, reset, next)` | Yes — batch-level (the step is not itself vmapped), so `lax.cond(jnp.any(done), …)` is a real branch |
| plain PPO `collect_trajectories` (`src/models/ppo_trainer.py:160-170`) | same pattern | Yes, same |
| `train.py:2044` (DQN) and `:2236` (DRQN) | eager Python loop, already converts `done` to numpy | Yes, with a Python `if` |
| Dreamer (`src/algorithms/dreamer_srl/dreamer_srl_main.py:1880-1900`) | already resets only the finished envs | Nothing to do |
| `wrapper.auto_reset_step` (`src/environment/wrapper.py:35-63`) | per-env select inside vmap; **no callers** (grep) | Out of scope; dead code noted, not deleted |

**How often can the reset be skipped?** If each of N = 128 worlds ends on a given step with
probability q ≈ 1/L (L = mean episode length), the reset is needed with probability `1 − (1 − q)^N`:

| Mean episode length L | P(some world ends this step) | Steps on which the reset is skipped |
|---|---|---|
| 25 (random policy, level 05) | 99.4 % | 0.6 % |
| 100 | 72.4 % | 27.6 % |
| 250 | 40.1 % | 59.9 % |
| 500 (the step cap) | 22.6 % | 77.4 % |

The saving is that share times the reset's share of a rollout step. **The reset is expensive**:
measured for this plan (`tmp/20261001_placement_audit/reset_cost.py`, 128 envs, jitted scan, levels
05 and 06), one vmapped step costs **72 µs** on the RTX 4090 and step-plus-full-reset **733–740 µs** —
the reset is about **90 %** of the environment's work per step (CPU: 3.1–3.3 ms versus 30–35.5 ms,
89–91 %). Against a whole rPPO training step of roughly 2.9–3.9 ms (128 envs at ~33–44 k steps/s,
THIRST_PILOT), the reset build is on the order of **17–23 % of training time**, so skipping it on
60–77 % of steps (long episodes) could plausibly make training **10–18 % faster**. This is an estimate
from different hardware and harnesses; §3.6 measures it. The saving is near zero early in training
(short episodes) and largest when the agent survives long. Because the reset is that large, any cost
C or D add to it matters more than their effect on the bare step — §3.6 measures the reset too. Two
caveats: on the GPU an XLA conditional reads its predicate back to the host, a small per-step sync
that could eat the saving, which is why E is measured and only kept if faster; and KNOWN_BUGS row
~167 (reset not bit-identical across compilations: `animal_property_sampled` may differ by one
float32 last digit) means "outcome-identical" must be tested with that documented exception.

### A7. Prototype costs of the regrowth fix (measured for this plan, not shipped)

To see whether the 3 % budget is reachable, three versions of the regrowth (one per step, U3) were
prototyped in throwaway copies of `src/` (`tmp/20261001_placement_audit/patch_proto*.py`) and timed
with the decision-13/17 harness (`tmp/20260930_speed_check.py`: 64 envs × 300 steps, jitted
`lax.scan`, 5 reps, median), pre-change and prototype interleaved, on this machine's RTX 4090 and CPU:

- **P1, grid mask:** mark occupied cells in a 100-cell mask, count free cells, draw one integer,
  find the u-th free cell with a cumulative sum.
- **P2, closed-form rank:** no grid. For the K occupied cells inside the area (K ≈ 46 in level 06),
  g(e) = (rank of e) − (number of occupied ranks below it) is the number of free cells below e, and
  the u-th free cell is u + #{e : g(e) ≤ u}. Exact with no loop, no sort, no scatter — checked by brute
  force against direct enumeration on 473,295 cases with 0 mismatches
  (`tmp/20261001_placement_audit/check_closed.py`). P2 de-duplicates only the agent's entry.
- **P3:** P2 with a general de-duplication (exact even on hand-built states with two objects on one
  cell).

Environment steps per second, median over processes of each process's 5-rep median (number of
processes in brackets; logs `tmp/20261001_placement_audit/speed_proto*.log`). Change is against the
pre-change median in the same column.

| Form | GPU level 05 | GPU level 06 | CPU level 05 | CPU level 06 |
|---|---|---|---|---|
| Pre-change | 925 k [7] (range 912–1,007 k) | 840 k [7] (833–907 k) | 31.9 k [6] (31.4–32.1 k) | 37.7 k [6] (34.9–37.9 k) |
| P1 grid mask | 792 k [4] **−14 %** | 766 k [5] **−9 %** | 42.9 k [2] **+34 %** | 43.9 k [2] **+16 %** |
| P2 closed form, agent-only de-dup (not eligible, §3.3) | 809 k [2] **−12 %** | 850 k [1] +1 % | 40.0 k [2] +25 % | 42.5 k [2] +13 % |
| P3 closed form, general de-dup | 820 k [3] **−11 %** | 802 k [3] **−4.5 %** | 39.1 k [2] **+23 %** | 43.2 k [2] **+15 %** |

Two process-level collapses to ~380–415 k steps/s (one P1 run on level 05, one P2 run on level 06)
are excluded from the table; no pre-change process showed one; the cause is unknown.

**Correctness of P3 in the real environment** (`tmp/20261001_placement_audit/proto_check.py`: levels
05 and 06 with `max_consumption: 1` and `regeneration_delay: 0` set in memory, 256 envs × 400 steps,
an eat-heavy random policy): **1,587 and 1,640 regrowths, none on an occupied cell or outside the
area, none on a burning fire, never two on one step.** The same script on the pre-change code: 441 of
1,594 and 458 of 1,609 regrowths on an occupied cell (27.7 % and 28.5 % — this count includes the
agent's cell and other food, which A1's table did not), 28 and 30 on a burning fire (1.8 %, 1.9 %),
and 26 and 33 steps on which two items regrew together (items that had been stacked on one cell). This
script is the template for T-A1/T-A2.

**Reading it.** (1) On the CPU every form is much *faster* than today, because the old code draws 16
two-number random cells per step and the new code draws one number (decision 17 saw the same
effect). (2) On the GPU every form so far costs more than 3 %: about 11–14 % on level 05, 4.5–9 % on
level 06 (level 06 already pays for the pond-only draw, which the new path replaces). P1 and P3 cost
about the same on level 05 although they compute very different things, which suggests the cost is in
what they share (choosing the due slot, the gathers, the restricted mask), not in the cell search —
the developer should profile before trying further forms. (3) The GPU numbers move by up to ~10 %
between processes running the *same* code, so a 3 % budget needs more rounds than decision 13 used
(§3.6).

**Why a few percent of the bare step is small in training.** In rPPO training the environment step
is a small part of each update: the bare harness runs ~0.9 M steps/s, rPPO training ~33–44 k
steps/s (THIRST_PILOT, 2080 Ti / 3090). So the bare step is roughly 2–3 % of training time, and an
11 % bare-step cost would be about 0.3 % of training — far smaller than what E can save (A6).

### A8. Known-bug rows (from `bug-curator`, 2026-10-01)

| Row | What | Status | Relation to this plan |
|---|---|---|---|
| ~117 | Object parked silently at cell (0, 0) when its area is full (both `resolve_overlaps_global` and `relocate_blocked_entities`) | OPEN | **Closed by C** for `per_entity` placement: proved unreachable in every maintained world, a counted drop in the 17 worlds the proof cannot cover. The registry's line references are stale (now `core.py:~1494`, `~1601`). |
| ~483 | Dead food slots came back to life (`res_allocated` fix) | Fixed | A keeps the `res_allocated` gate untouched; a test re-asserts it (T-A4). |
| ~167 | Reset not bit-identical across compilations (1 float32 ULP in `animal_property_sampled`) | Not a bug | E's equivalence test must allow exactly this. |
| ~397 | rPPO reused the reset key as the next step's key | Fixed | E keeps the `key, reset_key = split(key)` line **outside** the conditional so the key stream is unchanged. |
| ~487 | Dreamer reset storm (recompiles) | Fixed | Why Dreamer needs nothing from E. |
| ~294, ~328, ~290 | Parity fixtures stale, frozen or self-re-baselining | Fixed | The re-baselining protocol in §3.5 is written so none of these recurs. |
| — | **No row exists** for regrowth position, unused slots during placement, or the per-step reset build | — | `bug-curator` records the first two as fixed when this lands (§3.7). |

---

## Implementation Plan

### 3.0 Where and when

- **Not before the seven `rppo_l06pilot_*` runs have finished** (expected ~16:30 KST 2026-10-01; check
  `docs/diary/2026-10-01.md` rows and that no process on nodes 101–105 runs from this worktree), **or**
  in a separate worktree branched from `v5.0`'s current tip. Checkpoint-time renders start fresh
  processes that import `src/` from this worktree; editing it under them would make a pilot run
  render with half-changed code.
- Record the **pre-change commit SHA** (the `v5.0` tip you start from) in the Implementation Report.
  Make a **detached worktree of that SHA** (e.g. `/tmp/gwp_placement_baseline`) before changing
  anything; every "fails on pre-change code" proof and every pre-change capture runs there.
- Every `tmp/20261001_placement_audit/...` path in this plan, and the speed harness
  `tmp/20260930_speed_check.py`, is in the **gitignored** `tmp/` of the
  worktree `/media/nas01/projects/Interoceptive-AI/grid_world_pain/.claude/worktrees/thirst/`
  (audit and prototype scripts, speed logs, `results_senior_dev.md`). A separate worktree reads them
  by that absolute path; nothing there is committed.
- No config keys are added, renamed or removed. No version numbers are introduced anywhere.

### 3.1 Part C — campfires first, a load-time proof, and a backstop only where the proof fails

**Design.** Three pieces. The first two cost nothing per step; the third is compiled in only for
worlds the proof cannot cover.

1. **Campfires first in the placement scan.** When `thermal.enabled` and `min_fire_separation > 0`,
   the scan visits the heat-source obstacle slots first (in slot order), then every other slot in
   today's `[food, predators, obstacles, neutral]` order. No random draw changes: every object's raw
   cell is drawn exactly as today; only the order in which collisions are resolved changes. Worlds
   with no separation rule keep today's order and today's compiled graph.
2. **A load-time feasibility check**, `_check_placement_feasibility`, run for every `per_entity`
   world, counting every slot at `count_high` (worst case):
   - (i) **fires**: exact depth-first enumeration — for every pond candidate and every legal position
     of fires 1..k−1, fire k still has a legal cell (in its area, off the pond, at distance ≥ s from
     each earlier fire). Cap the enumeration with a small node budget so loading stays fast (the
     prototype uses 20,000; a 2,000,000 cap took minutes per config on the 20 × 20 many-fire worlds —
     report the load time of levels 05/06 before and after). Past the cap use the conservative bound
     `|A_k| − pond_k − k·D(s) ≥ 1`, where `A_k` is the slot's area, `pond_k` the most pond cells any
     candidate puts inside it, and `D(s) = 2s² − 2s + 1` the cells a fire forbids.
     **If (i) cannot be proved, the world still loads**: it gets the backstop (piece 3) and one
     WARNING line naming the world and the first fire that could not be proved;
   - (ii) **every slot**, in the new scan order: `|A_i| − pond_i − n_before_i ≥ 1`, where
     `n_before_i` counts the earlier slots **whose area overlaps `A_i`** (a slot in a disjoint
     quadrant can never take a cell of `A_i`). This generalises the existing water capacity check
     (which counts every earlier slot — too strict: with that count the four observability-gate
     verification worlds, quadrant layouts on a 10 × 10 grid, would be refused) to every world (water
     off → no pond); the water-specific block at `config_loader.py:3056-3071` is replaced by a call
     to the shared function;
   - (iii) **food-to-fire pass** (only when `food_min_fire_distance` M > 0): the bush-style bound
     `|A_food| − pond − n_fire·D(M) − n_other ≥ n_food`;
   - (iv) **regrowth** (part A): for each resource slot,
     `|A_j| − pond_j − n_obstacles_overlapping − n_other_resources_overlapping − 1 (agent) ≥ 1`
     (slots counted only if their area overlaps `A_j`), minus a further `n_fire·(D(M) − 1)` when the
     slot is food and M > 0.
   A failure of (ii), (iii) or (iv) means there are more objects than room — a config mistake — and
   is refused with a named `ValueError`. The existing `_check_bush_fire_clearance` stays as it is.
3. **Backstop, only for worlds where (i) is unproved** (static `EnvParams` flag
   `placement_backstop`). In `resolve_overlaps_global`, a fire slot with no valid cell is **dropped**:
   it does not move, marks no cell, adds no zone, and its activation mask is turned off, so it is
   parked off-grid and stamps no heat, exactly like an unused slot (U9). The reset records the
   number of dropped objects in a new `EnvState` leaf `placement_dropped` (int32 scalar), present
   only when the flag is on (default `None`, the water-field pattern), so other worlds' state is
   unchanged. Only fires can be dropped: every other slot is covered by (ii). With the flag off,
   none of this is traced.
4. **The (0, 0) lines stay in the code**, with docstrings changed from "silent fallback" to
   "unreachable: proved at load (`_check_placement_feasibility`), or turned into a counted drop in
   worlds the proof cannot cover".

**What the check does to today's configs.** A numpy prototype of (i), (ii) and (iv)
(`tmp/20261001_placement_audit/feas_sel.py`, fires-first order, `count_high` everywhere; full output
`feas_sweep.out` next to it):

- **All 11 maintained configs are proved** (`default.yaml` and the ten under `basic/`), and so are
  the 7 stand-alone configs that live tests load (the frozen parity world, the two saved-run configs,
  the four observability-gate verification worlds).
- **All 795 YAML files under `configs/environment/`:** 452 load today; 435 are proved; **17 cannot
  be proved**, all on (i), none on (ii)/(iv): the 13 15 × 15 and 20 × 20 worlds of
  `continual_worlds/` (up to 7 campfires in an 11 × 11 area) and 4 `context_exploration/` worlds
  (up to 12 campfires in 16 × 16). With that many fires at separation 4, a bad layout of the early
  fires really can leave no legal cell for a later one (radius-3 diamonds of 25 cells tile the grid),
  so these are not prototype artefacts. Measured on today's code over 2,000 resets each of
  `continual_worlds/danger_15x15`, `context_exploration/g20r5f4to16b12` and
  `continual_worlds/forage_20x20` (`tmp/20261001_placement_audit/fallback_rate.py`): **0.00 %** of
  episodes put any object outside its area. Under (c) these 17 load with a warning and the backstop.
- The 343 that do not load today are archived worlds broken by earlier schema changes; untouched.

**File changes.**

- `src/environment/state.py` — `EnvParams`: two new static fields,
  `placement_scan_order: tuple` (a permutation of the `[res, pred, obs, neutral]` concatenation;
  identity when no separation rule) and `placement_backstop: bool` (True only when (i) is unproved),
  both `struct.field(pytree_node=False)`. Extend `__setstate__` so a pickle without them gets both
  **recomputed from the pickled arrays** by the same helper the loader uses (heat-source mask from
  `obs_temperature` / ratios, separation, areas, slot counts, pond table) — correct for any era, so
  they are not added to `WATER_OFF_FIELDS`' all-or-none set. `EnvState`: append
  `placement_dropped` (int32 scalar) at the very end with default `None`, set only when
  `placement_backstop` (the water-field pattern: other worlds gain no leaf).
- `src/environment/config_loader.py` — new `_check_placement_feasibility(...)` (numpy only; its
  docstring states the four bounds above and which failures refuse versus enable the backstop),
  called from `load_env_params` for `per_entity` worlds; it computes `placement_scan_order` and
  `placement_backstop`. Replace the water capacity block with the shared call (keep the
  `"water: capacity check failed"` message prefix, or update `tests/env/test_water_placement.py`'s
  refusal-message match in the same commit).
- `src/environment/core.py` `jax_reset` (`~2003-2075`): when `params.placement_scan_order` is not the
  identity (a static Python test), permute `all_positions`, `all_spawn_areas`, `_is_fire_concat` (and
  D's `entity_active`) by it before `resolve_overlaps_global`, and apply the inverse permutation to
  the result. Identity → no gather is traced (today's graph). When `placement_backstop`,
  `resolve_overlaps_global` also returns a per-slot `dropped` mask (computed from the
  `first_valid_mask` it already builds); `jax_reset` ANDs the obstacle activation mask with
  `~dropped` before parking and before the thermal field is stamped, and writes
  `placement_dropped = dropped.sum()`.
- `src/environment/saved_config_compat.py` — only if it enumerates `EnvParams` fields; check, and
  record the finding either way.
- Recording / trajectory-store code that enumerates `EnvState` leaves (`src/utils/eval_recording.py`,
  `src/utils/trajectory_store.py`): check that an extra optional leaf in the 17 backstop worlds does
  not break them, as the water leaves did not; record the finding.

### 3.2 Part D — unused slots neither occupy cells nor reserve fire zones

**Design.** Draw the three activation masks before placement (same function, same keys, same fold-in
constants `0xC0A1..3` — identical values), concatenate them in scan order as `entity_active`, and:

- `resolve_overlaps_global(..., entity_active=None)`: new optional argument; `None` (static) traces
  today's graph. When given, an inactive entry is never moved, never marks `occ`, never adds to
  `fire_block`. It keeps its raw cell and is parked off-grid afterwards exactly as today.
- `relocate_blocked_entities`: the initial occupancy excludes inactive entries; `entity_mask` is
  ANDed with `entity_active`.
- D3's `_fire_block` uses burning (active) fire slots only, like the bush pass already does.
- §7b reuses the hoisted masks instead of calling `_build_activation_mask` again (the bush pass's
  separate `_obs_act` call also goes).
- Gate: only when `has_res_range or has_animal_range or has_obs_range` (static). Worlds with fixed
  counts (levels 00–02, `forage_5x5`, `slow_predator_bush_5x5`) trace today's graph exactly.

No new random draws anywhere. **File changes:** `src/environment/core.py` only (`resolve_overlaps_global`
signature and body ~1461-1565, `relocate_blocked_entities` ~1568-1638, `jax_reset` ~1930-2134 and
~2312-2341).

### 3.3 Part A — regrown food lands only on a free cell of its own area

**Behaviour (the contract the tests pin).** On a step where at least one resource slot is due:

1. Only the **lowest-numbered due slot** `i*` regrows this step (U3). Other due slots stay inactive
   with timer 0 and are due again next step. `new_active` and `new_cons_count` are recomputed from the
   restricted mask; `update_resources` itself is unchanged (it keeps the `res_allocated` gate).
2. **Occupied** cells: active obstacles of every kind (rocks, bushes, burning fires), every other
   active resource (food and hiding predators — food on a hiding predator would bite the agent that
   eats it), the pond cells (water worlds), and the agent's current pre-move cell (U1).
   Animals are **not** occupied (U2).
3. If `food_min_fire_distance` M > 0 (static gate) and `i*` is food (`res_type == 0`), cells at
   Manhattan distance < M from a burning fire are also excluded (U4).
4. The free set F is `area(i*)` minus the excluded cells, in row-major order. Draw
   `u = randint(respawn_key, (), 0, max(|F|, 1))` and put the item on the u-th cell of F. Exactly
   uniform over F.
5. If |F| = 0 the slot does not regrow this step and stays due. Unreachable when C(iv) holds; it
   exists so the code never places anything on an invalid cell.
6. `respawn_key` is used directly. The `split(respawn_key, num_res)` call goes. The 6-way split at
   the top of `jax_step` is unchanged, so no other stream (animals, damage, property resampling)
   moves. Property resampling (`core.py:1038-1056`) is unchanged and still keyed by
   `respawn_mask`, now the restricted one.
7. The water-only branch (`core.py:1001-1031`, decision 17) is **replaced** by this general path; its
   comment block goes. `0xD83` stays retired, not reused.

**Implementation form — measured, then chosen.** Candidates, all exact: P1 (grid mask + cumulative
sum), P3 (closed-form rank with general de-duplication), and any cheaper exact form the developer
finds (for example, caching the episode's fixed occupied cells — obstacles and pond — at reset so only
food and the agent are listed per step; that adds an `EnvState` leaf and must say so). **P2 is not
eligible**: it is exact only while no two listed objects share a cell, and some tests build exactly
such states (for example `tests/env/test_two_sided_nutrition.py:245` puts food on the agent's cell).
Start from **P3** (`tmp/20261001_placement_audit/patch_proto3.py` — the measured GPU leader on both
levels, and correct in the forced-regrowth smoke test, A7), profile what P1 and P3 share before
trying new cell-search forms (A7 point 2), pick the fastest candidate on the GPU that passes T-A1 to
T-A6, and record every candidate's numbers in the Implementation Report. The prototype patch is a
starting point, not reviewed code: it lacks the M > 0 branch and its comments are not final. The
M > 0 branch may use the grid-mask form regardless (it is compiled out in every level).

**File changes:** `src/environment/core.py` `jax_step` `~994-1036` (and the `new_active` /
`new_cons_count` lines that consume `update_resources`' outputs, `~989-992`).

### 3.4 Part E — skip the reset build on steps where no world ended (measured; kept only if faster)

```python
# src/models/recurrent_ppo_trainer.py ~334-350 (same shape in src/models/ppo_trainer.py ~160-170)
# BEFORE
key, reset_key = jax.random.split(key)
reset_state = jax.vmap(jax_reset, in_axes=(None, 0))(env_params, jax.random.split(reset_key, n))
final_state = jax.tree_util.tree_map(lambda r, s: select_done(done, r, s), reset_state, next_state)

# AFTER
key, reset_key = jax.random.split(key)          # stays OUTSIDE the cond: key stream unchanged
def _with_reset(_):
    reset_state = jax.vmap(jax_reset, in_axes=(None, 0))(env_params, jax.random.split(reset_key, n))
    return jax.tree_util.tree_map(lambda r, s: select_done(done, r, s), reset_state, next_state)
final_state = jax.lax.cond(jnp.any(done), _with_reset, lambda _: next_state, None)
```

- `train.py:2044` (DQN), `:2236` (DRQN): `if bool(np.any(np.asarray(done))):` around the reset
  build; else keep `env_state = next_state`. Eager code — no measurement needed beyond T-E1.
- No config switch (not requested). If E is dropped, none of this lands.
- Pre-registered **keep rule**: keep only if T-E1 passes (outcome-identical) **and** the rPPO
  end-to-end throughput on GPU is faster than without E (median over the rounds in §3.6, by more than
  the base-versus-base spread). Otherwise drop, and record the numbers.

### 3.5 Tests

Every new test must be shown to **fail on the pre-change code** (run it in the baseline worktree;
paste the failing line into the Implementation Report), except where marked.

| Id | File (new unless noted) | What it asserts | Pre-change result |
|---|---|---|---|
| T-A1 | `tests/env/test_placement_fixes.py::test_regrowth_never_on_an_occupied_cell` | Levels 05 and 06 with `max_consumption: 1`, `regeneration_delay: 0` (in memory) and an eat-heavy random policy, ≥ 256 envs × 400 steps: every regrown item is in its area and not on an active obstacle, another active resource, the pond or the agent's pre-step cell. Asserts ≥ 1,000 regrowths (not vacuous). | Fails (~18 % on obstacles) |
| T-A2 | same file `::test_regrowth_on_fire_rate_is_exactly_zero` | Same rollouts: count of regrowths on a burning fire **== 0**, with ≥ 1,000 regrowths observed. | Fails (~2 %) |
| T-A3 | same file `::test_regrowth_is_uniform_over_free_cells` | A fixed hand-built state, one due slot, 4,000 keys: support == the free set exactly, χ² test passes. | Fails (support includes occupied cells) |
| T-A4 | same file `::test_one_regrowth_per_step_and_deferral` | Two due slots: only the lower one regrows; the other regrows on the next step; an unallocated slot (`res_allocated` False) never regrows (row ~483 still holds). | Fails (both regrow) |
| T-A5 | same file `::test_no_free_cell_means_no_regrowth` | Hand-built state with the area full: the slot stays inactive and due; nothing moves to (0, 0). | Fails (item placed on an occupied cell) |
| T-A6 | same file `::test_food_min_fire_distance_applies_to_regrowth` | Level 05 with M = 2 in memory: no regrown food within distance < 2 of a burning fire. | Fails |
| T-C1 | `tests/env/test_placement_fixes.py::test_loader_refuses_infeasible_worlds` | Named refusals for (ii), (iii), (iv): more overlapping slots than cells; the food-to-fire pass with no room; regrowth with no free cell. Each message names the check. Also: `continual_worlds/danger_15x15` loads with `placement_backstop` True and logs one WARNING; level 05 loads with it False. | Fails (loads silently; fields absent) |
| T-C4 | same file `::test_backstop_drops_and_counts_instead_of_cell_zero` | A synthetic world the check cannot prove and that really does run out of room: three fires with separation 3 in a 1 × 5 strip (a first fire in the middle forbids the whole strip). Everything else is placed outside the strip so (ii) passes; if the thermal structure check refuses the strip, use the smallest geometry it accepts that still runs out of room, and say so. Over 2,000 resets: no active object outside its area, `placement_dropped` > 0 in some episodes and equal to the number of fire slots that ended inactive although activated, and a dropped fire stamps no heat. | Fails (fires land at (0, 0)) |
| T-C2 | same file `::test_shipped_levels_pass_and_never_hit_the_fallback` | Every maintained level loads; 2,000 resets each: every active object in its area, no duplicates. | Passes on both (guard) |
| T-C3 | same file `::test_fires_are_placed_first` | Level 05: `placement_scan_order` starts with exactly the heat-source obstacle slots; level 03 (no separation rule) has the identity order; and over 2,000 level-06 resets an active fire leaves its raw cell only when that cell is on the pond or closer than the separation to an earlier active fire (recompute raw draws as in T-D1). | Fails (field absent; today food and animals displace fires) |
| T-D1 | same file `::test_unused_slots_do_not_displace_used_ones` | Recompute the raw draws (same splits as `jax_reset`, ~10 lines, commented) for 2,000 level-05 resets; wherever an **unused** slot's raw cell equals a later **used** slot's raw cell, the used slot keeps its raw cell. | Fails |
| T-D2 | same file `::test_unused_fires_reserve_no_zone` | Same recomputation: a used fire is never moved because of an unused fire's zone. | Fails |
| T-E1 | `tests/models/test_reset_skip_equivalence.py` (only if E is kept) | rPPO `collect_trajectories` on level 05, fixed seed, with and without the skip: trajectories and final states identical, except `animal_property_sampled` within 1 float32 ULP (row ~167). Includes steps with and without episode endings (asserts both occur). | n/a (equivalence) |

Existing tests to update in the same commits, with a one-line reason each:
`tests/env/test_water_placement.py::test_respawn_repair_is_uniform_over_area_minus_pond` (it forces
every slot due on every step; with U3 only slot 0 regrows — assert on that slot) and
`::test_loader_refusals` (if a message changes).

### 3.5b Re-baselining the byte-parity fixtures — deliberately, with a written reason

A, C and D change random outcomes; E must not. Fixture-backed tests (grep of `tests/` for
`fixtures`): `test_unified_parity`, `test_thermal_parity`, `test_visual_parity`, `test_water_parity`,
`test_body_mechanics_parity`, `test_bush_fire_clearance`, `test_metabolic_coupling`,
`test_thermal_rate_scales`, `test_extero_noc_parity`, `test_directional_sensors`,
`test_thermal_reward_gate`, `tests/test_trajectory_collection.py`,
`tests/models/test_balance_metrics_parity.py`, `tests/models/test_modulation_*`, and the Dreamer
`tests/algorithms/dreamer_srl/test_end_to_end_parity.py`. Which ones break is **expected, not
assumed**: C touches only worlds with a separation rule, D only worlds with count ranges, A only
rollouts in which an item actually regrows (rare under the fixtures' random policies — A1).

Protocol:

1. **Before any change**, in the baseline worktree: run every module above, one process per module,
   CPU (the `tests/env/conftest.py` pin; row ~291). Save the pass/fail list. Anything already red is
   recorded and left alone.
2. **One part per commit** (C, then D, then A). After each part, rerun the list. For every case that
   turns red, run a divergence locator (developer writes it under `tmp/`): replay the same case on
   the baseline tree and the new tree, find the first differing step and array, and classify:
   - **C**: the first difference is in reset placement of a world with a separation rule, and the
     fires-first order explains it (an earlier-placed fire now takes a cell first);
   - **D**: reset placement differs in a world with count ranges, and an unused slot's raw cell or
     zone was involved;
   - **A**: the first difference is at a step where some slot was due to regrow;
   - **anything else → stop.** That is a bug, not a re-baseline.
3. **Regenerate only classified fixtures**, once, from the clean commit that contains the code change,
   with the existing generator scripts. Commit the fixtures **with** the code change that broke them
   (so every commit is green). Each fixture README gets: source SHA, the part (A/C/D), the one-line
   reason, and the classification row.
4. **Say plainly in each README** that a re-baselined fixture now pins the new behaviour and proves
   nothing about the change itself — the proof is the new tests T-A*/T-C*/T-D* and the classification
   table. Do not regenerate from a tree with uncommitted edits.
5. **E must break nothing.** If any fixture-backed test changes after E, E is wrong.

### 3.6 Speed protocol (pre-registered)

- **Harness:** `tmp/20260930_speed_check.py` unchanged (64 envs × 300 steps, jitted `lax.scan`,
  5 reps, median, seed 0), levels 05 and 06, the same RTX 4090 node and the shared CPU as decisions
  13/17, pre-change tree and new tree **interleaved for 6 rounds** (2 rounds cannot resolve 3 %: A7).
- **Budget for A + C + D together:** for each of the four cells (GPU/CPU × level 05/06), the median
  over rounds of the new tree is at most 3 % below the base. Also report vmapped `jax_reset`
  throughput for 128 envs (`tmp/20261001_placement_audit/reset_cost.py`): C and D only touch the
  reset, and rPPO builds one every step (until E). Same 3 % line.
- **Collapsed processes:** a process whose median is below 60 % of the other rounds' median for the
  same tree and level is re-run and reported, not silently dropped; if it recurs for one tree only,
  that is a finding (A7 saw two, both in prototype processes) and goes in the report.
- **If a cell misses the budget:** do not tune silently. Record every candidate form's numbers and stop
  for the user (U6), with the end-to-end numbers below.
- **End-to-end check:** short rPPO training on the level-06 pilot agent config (`--episodes` small
  enough for ~10 minutes, same node and GPU, base and new interleaved, 2 runs each), report
  `Time/sps_env`. Reported against the same 3 % line; flagged if the runs' own spread is larger.
- **E:** measured separately, after A+C+D, with the same end-to-end runs plus the reset-share
  measurement. Keep rule in §3.4.

### 3.7 Documentation in the same change (maintenance contracts)

- `docs/environment/03_entity_placement.md` — scan order (fires first when a separation rule is on),
  unused slots, the load-time feasibility check, the (0, 0) lines now unreachable.
- `docs/environment/08_resources_and_obstacles.md` and `04_step_loop.md` — the regrowth contract
  (§3.3, items 1–7).
- `docs/environment/ENVIRONMENT_SUMMARY.md` — FAQ line ~211 ("Resource respawn doesn't check
  occupancy") rewritten; agent-start FAQ (~208) unchanged (still true, by decision).
- `docs/environment/01_state_and_params.md` — the new `placement_scan_order` and `placement_backstop`
  fields and the optional `placement_dropped` state leaf.
- `docs/environment/CONFIG_GUIDE.md` and `02_config_schema.md` — the new load-time refusals (Maintenance
  Contract items 2 and 3); no key changes.
- `docs/environment/CONFIG_CRITICAL_SETTINGS.md` — **no value changes**, but the meaning of two
  registry settings changes (`min_fire_separation` now also fixes the scan order;
  `food_min_fire_distance`, if registered, now also applies to regrowth): one dated change-log entry
  saying so.
- `docs/environment/11_parallel_env_wrapper.md` — if E is kept.
- `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` — only if a file under `scripts/` is added or changed
  (for example a fixture generator); otherwise state "no `scripts/` change" in the report.
- `docs/develop/active/issues/OPEN_WORK_HANDOFF.md` E2 — dated note: regrowth now honours the setting;
  only the value is open.
- `bug-curator` (not the developer) — close row ~117 for `per_entity` (proved worlds) and note the
  counted-drop backstop for the 17 unproved ones; add fixed rows for "regrowth ignored occupancy"
  and "unused slots took part in placement".

### 3.8 Commit sequence

| # | Content | Green? |
|---|---|---|
| 0 | Baseline worktree, pre-change test list, pre-change speed rounds (no commit; logs under `tmp/`) | — |
| 1 | C + T-C1..4 + classified fixture regenerations + docs for C | yes |
| 2 | D + T-D1..2 + classified regenerations + docs for D | yes |
| 3 | A + T-A1..6 + updated water tests + classified regenerations + docs for A | yes |
| 4 | Speed table (A+C+D) in this doc | — |
| 5 | E + T-E1 (only if kept) + docs | yes |
| 6 | Implementation Report | — |

---

## Checkpoints

- [ ] **K0** Pilot runs finished (or separate worktree). Pre-change SHA and baseline worktree recorded.
  - *Appended by experiment-designer, 2026-10-01 ([[THIRST_TASK]] Revision 1 §9.3):* the placement work happens in the main `thirst` worktree only, never in `.claude/worktrees/thirst-runs`, which is frozen at the thirst-task launch commit for that series and its follow-up seeds.
- [ ] **K1** Baseline fixture-backed test list saved; pre-change speed rounds saved.
- [ ] **K2** C: the feasibility check refuses T-C1's worlds, proves every maintained level, and puts exactly the 17 worlds of §3.1 (or say why not) on the backstop;
  the list of refused and backstopped configs is in the report (expected: none refused; the 17 of §3.1 backstopped).
- [ ] **K3** C: fires-first is static; a world without a separation rule has an identical jaxpr
  before and after (compare `jax.make_jaxpr(jax_reset)` text for level 03).
- [ ] **K4** D: worlds with fixed counts have identical `jax_reset` jaxprs before and after (level 02).
- [ ] **K5** A: T-A1 and T-A2 report the number of regrowths observed (≥ 1,000 each).
- [ ] **K6** Every red fixture case classified (C/D/A) by the divergence locator; zero unclassified.
- [ ] **K7** Speed table filled for all four cells plus the reset line; budget verdict stated.
- [ ] **K8** E: T-E1 passes; keep/drop decided by the pre-registered rule; numbers recorded.
- [ ] **K9** Docs in §3.7 updated in the same commits; `python scripts/claude/regen_dev_index.py` run.

---

## 5. What this means for existing runs and recordings

- Every run trained before this change — the level-05 runs, and the seven `rppo_l06pilot_*` runs
  launched today — learned in the **old** world: regrown food could sit on rocks, bushes, fires or other
  food; unused slots shaped the start layout; campfires were placed after food.
- **Evaluating an old checkpoint on the new code** puts it in a slightly different world. Survival
  numbers stay comparable in distribution, but **not seed for seed**: the same evaluation seed gives a
  different episode wherever placement or a regrowth changed.
- **Recordings** (`.rec` files) store what happened, so they replay and render as before; they show
  the old behaviour.
- **Rule for analyses:** compare arms only when they were evaluated on the same commit; if an analysis
  must mix pre- and post-change runs, it says so and names both SHAs. The pilot's analysis should
  evaluate all its arms on one commit (either the pre-change SHA recorded here, or the new one — not a
  mix).

## 6. Out of scope

- Agent start position (user decision: keep random, overlaps included).
- `per_type` placement mode (`place_in_area` pads short placements with 0 → (0, 0)); no maintained
  config uses it. Noted for `bug-curator`, not fixed.
- Heat-source **resources**: the thermal field is stamped once at reset, so a heat-source resource
  that regrows elsewhere would leave a stale stamp. No maintained config has one (the bush rule
  refuses them when on); noted, not fixed.
- Folding D3's second pass into the main scan (now possible with fires first) — a simplification,
  not requested.
- `wrapper.auto_reset_step` (no callers) — left in place.

---

## Implementation Report

> **Implemented by**: —
> **Date**: —

## Verification Report

> **Verified by**: —
> **Date**: —

| File | Change | Status | Notes |
|------|--------|:------:|-------|
| | | | |

**Conclusion**: —

---

## Feedback from plan-reviewer (2026-10-01, on commit `e98a0689`)

**Verdict: SOUND WITH CONCERNS. No Critical findings.** The design itself holds up. Regrown food goes
only to free cells. Campfires are placed first, so a load-time check can prove that every maintained
level can never trigger the cell-(0,0) fallback; I re-checked the separation arithmetic against
`core.py:1527-1545`. The activation draw moves earlier without changing any random value. The
reset-skip (part E) keeps the random key stream unchanged. Several problems remain, and each would
cost a rerun or a wrong keep/drop decision. The main ones: the speed decision is deferred rather
than pre-registered, and the "2-3 % of training" figure behind it is an estimate whose own arithmetic
gives 3.6-5.2 %. The end-to-end check uses a speed metric already known to be biased. E would be
judged in the training regime where it cannot help. One test belongs to the wrong commit. And the
GPU timing uses a lab GPU (node 102, which is this container) with no claim step.

Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run · 🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

| # | Sev | Location | Issue | Suggested fix | Owner |
|---|---|---|---|---|---|
| R1 | 🟡 | §0 U6, §A7 "Why a few percent…", §3.6 | **The speed decision is deferred, not pre-registered.** The plan expects A to miss 3 % on the GPU and says "stop and the user decides then", so the developer builds C+D+A before the user's real choice is asked. The figure meant to inform that choice ("bare step ≈ 2-3 % of training") is **estimated, not measured**: it divides a 64-env RTX 4090 harness rate (0.84-0.93 M/s) by a 128-env 2080 Ti/3090 training rate (33-44 k/s). Those cited numbers give **3.6-5.2 %**, not 2-3 % (only A6's 72 µs/128-env figure gives ~2 %), and a slower card raises the share. The conclusion (A costs < 1 % of training) probably survives: 14 % × 5.2 % ≈ 0.7 %. But it is not what the plan states. | Ask U6 **now** with a concrete rule, e.g. "accept A if (i) the bare-step GPU cost is ≤ 15 % and (ii) the measured rollout-phase throughput loss is ≤ 1 % on the card class training actually uses (3090 / 2080 Ti), else land C+D without A". Measure the env-step share directly: time `collect_trajectories` alone, or read the `rppo_env_step` / `rppo_env_reset` named scopes in a profile, rather than dividing across harnesses. Fix the 2-3 % arithmetic. | senior-developer / user |
| R2 | 🟡 | §3.6 "End-to-end check", §3.4 keep rule | **The end-to-end evidence uses `Time/sps_env`.** THIRST_PILOT M1 (`docs/reviews/plan_thirst_pilot.md:53`) already showed this metric is `global_step / seconds since start`, a running mean that includes compile time. On a 10-minute run, compile and warm-up dominate it, and 2 runs per arm cannot resolve 3 % when the plan itself measured ~10 % spread between processes of the same code (A7). | Use a windowed rate (Δsteps / Δwall-time after warm-up) and ≥ 6 interleaved rounds, the same count §3.6 already requires for the bare harness. | senior-developer |
| R3 | 🟡 | §3.4 keep rule, §3.6 "E" | **E would be judged in the regime where it cannot help.** A 10-minute run from scratch has short episodes: L ≈ 25 → the reset is skipped on 0.6 % of steps (A6's own table). The per-step GPU predicate sync is paid on every step, so the keep rule will most likely **drop E for the wrong reason**. | Measure E where episodes are long: roll out from a trained checkpoint (e.g. a finished pilot run), or force long episodes. Pre-register two numbers: "no slower than X % at L ≈ 25" and "faster by more than the base-vs-base spread at L ≈ 250". | senior-developer |
| R4 | 🟡 | §3.5 T-C3, §3.8 commit 1 | **T-C3 cannot pass in commit 1.** It asserts that a fire leaves its raw cell only because of an earlier **active** fire. Until D lands in commit 2, unused fire slots still reserve their zones, so under C alone an active fire is still moved by an *unused* fire. Commit 1 is then red, or the test gets rewritten in commit 2. | In commit 1, phrase T-C3 against "any earlier fire slot"; tighten it to "active" in commit 2 along with T-D2. | senior-developer |
| R5 | 🟡 | §3.1 piece 3, U9 | **The backstop drop is counted but nobody reads the count.** `placement_dropped` is a state leaf, and no trainer, logger or accumulator is wired to report it. The load-time WARNING is one line in a training log. In the 17 backstop worlds, a dropped fire therefore still means "the run trains on a world other than the YAML describes" with nothing visible, which is the very complaint in KNOWN_BUGS ~117. It is not a config-default fallback, so the `get_mandatory` rule does not apply literally, but it has the same effect. | Either report the per-episode count where some consumer will see it (for example rPPO episode-end stats, a small trainer change the plan must then list), or have the user accept explicitly that the count is reachable only by hand-written analysis. Also: the fallback-rate measurement covered 3 of the 17 worlds, so state the 0.00 % as covering those 3 only. | user / senior-developer |
| R6 | 🟡 | §3.6 harness, §A7 | **A lab GPU is used for timing with no claim step.** "This machine's RTX 4090" is node 102 (`hostname` = `docker-102`), a lab node that training-runner assigns (102:0 and 102:1 carried context-exploration runs on 2026-09-29). The prototype round already used it for about an hour without asking. §3.6 pre-registers more of the same: 6 harness rounds, 4 end-to-end trainings, then E. It also skips the GPU pre-flight (gpu-status + diary + pgrep, per the project's GPU pre-flight rule). Another user's process sharing the GPU is also a live alternative explanation for A7's ~10 % spread between processes and its two unexplained "collapses". | Make the node and GPU a user decision. Add the pre-flight and a diary claim row for the timing window. Log `nvidia-smi` occupancy alongside each round. Rerun the A7 base-vs-prototype comparison on a confirmed-idle GPU before treating 4.5-14 % as the cost. | senior-developer / user |
| R7 | 🟡 | §3.5b step 3 | **The fixture regeneration step contradicts itself.** It asks for regeneration "from the clean commit that contains the code change" **and** for the fixtures to be committed *with* that code change "so every commit is green", which cannot both hold. Recording a source SHA that is later amended away is how a fixture loses its provenance (rows ~290 / ~294 / ~328). | Either use two commits per part (code + tests, then fixtures whose README cites the code commit's SHA, accepting one red commit), or regenerate from a detached worktree of a code-only commit and record that SHA. Say which. | senior-developer |
| R8 | 🟡 | §5 | **The comparability note names only the level-05 runs and the pilot.** The 17 backstop worlds belong to two active studies (`docs/experiments/active/context_exploration/`, `continual_worlds/`). Their runs so far come from the shared checkout on `v4.0`. Any continuation or extension moved onto `v5.0` would change world mid-series: fires-first order, unused slots, regrowth. | List both studies in §5 and add a dated note to each study doc when this lands. | senior-developer |
| R9 | 🟢 | §3.5 T-D1 / T-D2 | Both tests recompute the raw draws "with the same splits as `jax_reset`", which re-derives the code under test. If the recomputation is wrong, the tests can pass without checking anything. | Anchor it: assert that the recomputed raw cells equal `jax_reset`'s output for every slot that did not move. Assert a minimum count of qualifying collisions, as T-A1 does with ≥ 1,000. | developer |
| R10 | 🟢 | §3.4, §3.5 T-E1 | E edits plain PPO, DQN and DRQN, but T-E1 tests rPPO only, so three edited call sites go untested. Plain PPO's key order is `reset_key, key = split(key)` (`ppo_trainer.py:163`), the reverse of rPPO's, and the snippet shows only rPPO's. T-E1 also runs a policy in the loop, so a documented 1-ULP reset difference (row ~167) can carry into later float leaves. | Either limit E to rPPO (the live trainer; this is the surgical choice) or add a fixed-action equivalence test per edited site. In T-E1, require integer and bool leaves to match exactly and float leaves to agree within 1 ULP. | senior-developer |
| R11 | 🟢 | §3.0 | The baseline worktree under `/tmp` will hold the pre-change test list and speed logs. `git worktree remove` deletes gitignored output; this is the same trap THIRST_PILOT hit. | Write every baseline capture to `thirst/tmp/…` by absolute path. | developer |
| R12 | 🟢 | §3.7 | Fires-first changes where fires land, and two registry claims were measured on the old layout: "0 episodes without a survivable cell" (2026-09-19) and "worst first step +10.78" (2026-09-26). | Rerun those two 600-1,000-reset checks after C+D and cite the numbers in the change-log entry the plan already adds. | developer |

**Answers to the specific questions.**
1. *Speed budget:* see R1, R2 and R6. CPU passes easily. The GPU figure for the bare step is measured
   (on a GPU whose occupancy was not checked). The share-of-training figure is an estimate, and the
   arithmetic given for it is off by about 2×. The decision is deferred.
2. *E's exactness:* sound. `key, reset_key = split(key)` stays outside the conditional, `reset_key`
   has no other consumer, and when no world ended the existing `where(done, …)` already returns
   `next_state` unchanged. I checked on CPU (levels 03, 05, 06) that `jax_step` and `jax_reset`
   outputs have identical leaf dtypes, shapes and weak-types, so `lax.cond`'s two branches will
   type-check and the eager DQN/DRQN skip cannot drift a dtype. `jax_step` builds its state with
   `_replace`, so the optional `placement_dropped` leaf will carry through. Dreamer already resets per
   env, and `wrapper.auto_reset_step` has no callers. I found no `vmap` over `collect_trajectories`
   that would turn the conditional into a select.
3. *Parity:* the protocol is good: a divergence locator, classification by part, and "anything else
   → stop". The fixtures are deliberately regenerated once per part, from the post-change commit, not
   recaptured from the pre-change commit. That is correct, but see R7. New tests fail on pre-change
   code with real counts: T-A2 sees 28-30 fire landings per ~1,600 regrowths before the change. T-C1
   fails trivially before the change (the field is absent), which is acceptable for a new refusal.
4. *C:* the proof is correct for fires-first. A fire is forbidden within Manhattan distance < s,
   D(4) = 25 cells, and `c_bound.py` enumerates every legal position, a superset of the positions
   the scan can reach. With D, fewer active fires only removes constraints. The drop-and-count
   backstop is not a config-default fallback, but in practice it is silent: see R5.
5. *U1-U3:* no new silent behaviour in the maintained levels. Deferral is head-of-line by slot
   number, so a slot with no free cell would block every slot after it. Check (iv) makes that
   unreachable at load, so this is not a starvation trap, provided (iv) is a refusal as written, never
   a warning.
6. *Pilot ordering:* K0 gates on the runs having finished. Any post-hoc evaluation of the pilot
   checkpoints should run on the pre-change SHA, or after this lands with all arms re-evaluated
   together, as §5 says.
7. *Known bugs, contracts, versions:* the rows (117, 167, 397, 483, 487) are cited correctly and the
   key handling avoids reintroducing 397. The CONFIG_CRITICAL_SETTINGS change-log entry,
   CONFIG_GUIDE, the config schema doc and the scripts map are all covered. The frontmatter is
   complete. No version numbers appear.

**Assumptions.** Verified in the plan or by me: the fires-first proof for the 11 maintained levels
(script). P3's correctness under forced regrowth (script). Reset ≈ 90 % of env work per step (measured
on node 102, occupancy unchecked). E's dtype parity (checked here). Unverified: the env-step share of
training on the training GPU class (R1). That node 102 was idle during the A7 timings (R6). Per-episode
regrowth frequency in trained agents (A1 says it is unmeasured). That the 17 worlds' fallback rate is
0 beyond the 3 measured (R5). That the 20,000-node enumeration cap keeps config loading fast across
the test suite (K-item reports levels 05/06 only).

**Cost of being wrong.** Nothing here risks data loss or a wrong scientific claim. The realistic costs
are an implementation that halts at the speed gate after C+D+A are built (about a day, if U6 is not
settled first), a ~10-18 % training speed-up wrongly discarded by measuring E on short episodes, and
one red commit plus a fixture whose provenance is muddled.

Reviewed by: plan-reviewer
