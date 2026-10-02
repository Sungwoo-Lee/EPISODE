---
title: "How often does food land inside a campfire's warm ring?"
topic: thermal
status: active
created: 2026-09-09
last_updated: 2026-09-09
develop_link: docs/develop/active/thermal/IMPLEMENTATION_PLAN.md
---

# How often does food land inside a campfire's warm ring?

## 1. Question, in plain English

The grid world recently gained a **temperature system**. The world is cold everywhere by
default, campfires warm the cells around them, and the agent has a body temperature it must
keep inside a survivable band or it dies. The intended lesson of a thermal episode is a
**trade-off**: warmth is in one place, food is in another, so the agent has to keep leaving
the fire to eat and keep coming back before it freezes.

That lesson only exists if the world actually separates the two. If a food item happens to
spawn right next to a fire, the episode has no trade-off in it at all — the agent can park
itself on that one cell, stay warm indefinitely, and eat. It still counts as a thermal
episode in every average we compute, but it teaches nothing about the thing the temperature
system was built to teach.

There is a switch that would prevent this: a setting that refuses to place food within a
chosen number of cells of a fire. It is currently **off** (set to zero), by an explicit
decision to wait for evidence. This document is that evidence. It reports, over 20,000
freshly generated worlds built by the real environment code, how often a food item lands
within one step of a fire, how warm those cells actually are, and whether the switch is
genuinely wired into the placement code or merely parsed from the file.

**Headline.** Roughly **29 out of every 100 episodes** put at least one food item one step
from a fire, and in **27 of those 100** that food is on a cell warm enough for the agent to
sit there forever without freezing. Those 27 episodes contain no warmth-versus-food conflict.
**Recommendation: turn the separation on, at a value of 2 cells, before any real training
run.** The full reasoning, and the honest counter-argument, are in §5.

**One thing this measurement does *not* depend on.** A separate review is looking at whether
the thermal *drive* — how the body-temperature error is turned into reward — is only correct
because the comfortable target temperature happens to be zero. That question is about the
reward function. Everything measured here is about where entities are *placed* when an
episode starts, which happens before any drive is evaluated and does not read the drive at
all. If the drive is changed, **these placement numbers stand and do not need redoing**.
The one number below that would move is the "warm enough to sit forever" share in §4.3,
because that one is derived from the body-temperature dynamics; the raw distance
distribution in §4.2 is untouched by any reward-side change.

---

## 2. What was measured, and how

**Config under test.** The campfire world at
`configs/environment/experiment/thermal/campfire_world.yaml` — the only config in the tree
with the temperature system switched on, and a complete standalone config (no `extends:`
layering), so there is no merge ambiguity about what it sets.

**Code path.** The same two functions the trainer uses, in the same order:
`load_env_config(path)` → `load_env_params(config)` → `jax_reset(params, key)`, the last one
vectorised with `jax.vmap` exactly as `ParallelEnv.reset` does. No placement logic was
reimplemented, and no second loader was used to cross-check the first — the numbers come out
of the environment the trainer would actually run.

**Sample.** 20,000 environment resets, master seed `20260909`, in 40 vectorised batches of
500, on CPU (`JAX_PLATFORMS=cpu`). At this sample size a 29% share carries a 95% confidence
interval of about ±0.6 percentage points, which is far tighter than any threshold the
decision turns on.

**What counts.** Only **active** entities. The scene draws a fresh entity count each episode
and parks the unused slots off-grid; an inactive food slot or an inactive campfire is
excluded from every statistic below. Distances are **Manhattan** (steps on the grid, no
diagonals).

**Scripts** (working files, not part of the source tree):

| Path | Purpose |
|---|---|
| `tmp/20260909_thermal_food_fire_measure.py` | The 20,000-reset measurement. |
| `tmp/20260909_thermal_food_fire_result.txt` | Its captured stdout. |
| `tmp/20260909_thermal_food_fire_raw.npz` | Per-reset raw arrays, for re-analysis without re-running. |
| `tmp/20260909_thermal_knob_wiring_check.py` | The §3 wiring check. |

---

## 3. Verification: is the switch actually connected?

This was checked against the code and then against the running environment, because a
recommendation to turn on a knob that does nothing would be worse than no recommendation.
The implementation plan for this system was wrong about the codebase at every one of its
seven stages, so nothing here is taken from the documentation.

**Read at load time — yes, and mandatorily.** `src/environment/config_loader.py:1513` reads
it through `config.get_mandatory('thermal.food_min_fire_distance')`, so a config missing the
key raises rather than silently defaulting. It is validated `>= 0` with the key named in the
message, and stored on the environment parameters as a static (non-traced) integer,
`EnvParams.thermal_food_min_fire_distance` (`src/environment/state.py:355`).

**Used at reset time — yes, in a second placement pass.** `src/environment/core.py:1504`
gates a call to `relocate_blocked_entities` behind a static Python `if _food_min_dist > 0`.
The pass is separate from the main overlap-resolution scan for a real reason: that scan
places entities in the order *resources → predators → obstacles → neutrals*, so **no fire
exists yet when food is placed** and the constraint cannot be a term in the first pass at
all. The second pass builds the set of cells within the chosen distance of any fire and
moves only the food items sitting in it; every other entity keeps the cell it already has,
which is what stops a relocated food from displacing the very fire the exclusion zone was
computed from.

**The distance convention.** The block is `distance < M`, so `M = 2` forbids distance 0 and
1 and guarantees a minimum food-to-fire distance of 2. `M = 1` would forbid only distance 0,
which is already impossible — two entities cannot share a cell. **The smallest value that
does anything is 2.**

**Confirmed empirically on the shipped config**, 1,000 resets, seed 4242:

| Setting | Smallest food→fire distance seen | Share of resets with food within 1 cell | Active food per reset | Entities parked outside their own spawn area |
|---|---|---|---|---|
| `0` (today) | 1 | 30.3% | 3.98 | 0 |
| `2` | **2** | **0.00%** | 3.98 | 0 |
| `3` | **3** | 0.00% | 3.98 | 0 |

The switch binds, it binds at the documented distance, and it costs nothing: the number of
food items placed is unchanged, and no entity was pushed into the silent failure mode
described in §4.4. **The knob works.**

One caveat worth recording. The exclusion zone is computed from **every allocated fire
slot**, including slots that the per-episode count draw will deactivate a few lines later.
Turning the switch on therefore blocks slightly more area than the fires that actually burn
in that episode. This is conservative in the safe direction and had no measurable cost above,
but a future reader comparing the blocked-cell count against the visible fires should expect
the mismatch rather than treat it as a bug.

**Not usable in one placement mode.** If `environment.placement.mode` is set to `per_type`,
the loader raises rather than silently ignoring the constraint (`config_loader.py:2003`).
The campfire config uses `per_entity`, so this does not bite here.

---

## 4. Results

### 4.1 What the config actually places

| Quantity | Value |
|---|---|
| Grid | 10 × 10 (100 cells) |
| Food slots allocated | 6 (of 10 resource slots) |
| Active food per episode | 2–6, drawn uniformly; mean **4.00** |
| Campfire slots allocated | 3 (of 25 obstacle slots) |
| Active campfires per episode | 1–3, drawn uniformly; mean **1.99** |
| Where fires may spawn | rows 2–7, columns 2–7 (a 6×6 interior; the config insets the fire's spawn box by 2 cells from the wall) |
| Where food may spawn | the **entire** 10 × 10 grid, walls included |
| Minimum separation between two fires | 3 cells (already enforced) |

The asymmetry in the last two rows is the mechanism behind the whole result: fires are
confined to the middle of the board while food is scattered across all 100 cells, so food
routinely lands next to a fire simply because the fires are where the board is busiest.

### 4.2 The stated question, and the shape around it

Share of resets whose closest food-to-fire distance is at or below each threshold, with 95%
Wilson binomial confidence intervals, n = 20,000:

| Threshold | Share of resets | 95% CI | Count |
|---|---|---|---|
| ≤ 0 (same cell) | 0.00% | [0.00, 0.02] | 0 / 20000 |
| **≤ 1 (the question)** | **28.66%** | **[28.03, 29.29]** | 5731 / 20000 |
| ≤ 2 | 60.07% | [59.38, 60.74] | 12013 / 20000 |
| ≤ 3 | 80.75% | [80.19, 81.29] | 16149 / 20000 |
| ≤ 4 | 91.19% | [90.79, 91.57] | 18238 / 20000 |

Full distribution of the **minimum** food-to-fire distance per reset:

| Distance | Resets | Share | Cumulative |
|---|---|---|---|
| 1 | 5731 | 28.66% | 28.66% |
| 2 | 6282 | 31.41% | 60.07% |
| 3 | 4136 | 20.68% | 80.75% |
| 4 | 2089 | 10.45% | 91.19% |
| 5 | 1012 | 5.06% | 96.25% |
| 6 | 457 | 2.28% | 98.53% |
| 7 | 196 | 0.98% | 99.52% |
| 8 | 68 | 0.34% | 99.86% |
| 9 | 16 | 0.08% | 99.94% |
| 10 | 11 | 0.06% | 99.99% |
| 11 | 2 | 0.01% | 100.00% |

Mean 2.45, median 2, maximum 11. Distance 0 never occurs, as expected — the placement scan
gives every entity its own cell.

**Is the answer robust to the choice of threshold 1?** Yes, in the sense that matters. The
distribution is smooth and unimodal with no cliff at 1, so the ≤1 share is not an artefact of
where the line was drawn. But the *interesting* structure is not in the distances at all — it
is in how warm those cells are, which is §4.3, and there the cliff is real and it sits
exactly between distance 1 and distance 2.

**Per-item view.** Counting food items rather than episodes: **8.30%** of all active food
items sit within one cell of a fire, a mean of 0.33 such items per episode.

### 4.3 How warm is "one step from a fire", really?

Distance is a proxy. The thing that decides whether an episode has a trade-off is whether the
agent can *survive indefinitely* while standing on the food.

Body temperature moves each step toward the local field temperature and leaks back toward the
comfortable target: `T' = T + 0.04 · (cell − T) − 0.01 · (T − 0)`. Standing still on one cell,
that settles at `T* = 0.8 × cell`. The agent dies outside −15 to +15, so a cell is
**indefinitely survivable** when its field is between about −18.8 and +18.8. The world's
baseline is −22 to −28, i.e. **standing anywhere away from a fire is eventually fatal** —
which is the point of the design.

Field temperature at the fire-nearest food, and the resting body temperature it implies:

| Distance to fire | Resets | Field (mean) | Field (5th–95th pct) | Resting body temp `T*` | Share survivable | Share near the comfortable target (`|T*| < 5`) |
|---|---|---|---|---|---|---|
| **1** | 5731 | **+11.12** | +7.51 → +19.70 | **+8.89** | **94.6%** | 0.0% |
| 2 | 6282 | −17.38 | −25.36 → −10.63 | −13.90 | 51.8% | 0.6% |
| 3 | 4136 | −24.55 | −27.18 → −21.86 | −19.64 | 0.0% | 0.0% |
| 4 | 2089 | −25.00 | −27.67 → −22.30 | −20.00 | 0.0% | 0.0% |
| 5 | 1012 | −25.01 | −27.63 → −22.30 | −20.01 | 0.0% | 0.0% |

This is the decisive table, and it says the warm ring is **one cell wide**. At distance 1 the
agent settles at roughly +9 °, comfortably alive. At distance 2 it settles at roughly −14 °,
which is inside the survivable band only about half the time and is one degree from death
even then — technically not fatal, but deep in thermal-drive penalty and not a place a
reward-maximising agent would choose to camp. At distance 3 and beyond, sitting still is
simply lethal.

Aggregate, over all 20,000 resets:

| Measure | Share | 95% CI |
|---|---|---|
| At least one active food on an indefinitely-survivable cell | 46.21% | [45.52, 46.90] |
| **At least one food that is both within 1 cell of a fire and on a survivable cell** | **27.37%** | **[26.75, 27.99]** |
| — of which, that food is at distance 1 | 27.37% of all resets | — |
| — survivable food at distance 2 (the marginal, near-lethal band) | 18.84% of all resets | — |
| Survivable food at distance ≥ 3 | 0.00% | — |

The two headline numbers — **28.66%** of resets with food within one step of a fire, and
**27.37%** of resets where such a food is genuinely warm enough to camp on — **point the same
way**, and they are nearly the same number because almost every distance-1 cell (94.6%) is in
fact comfortable. The 27.37% figure is the one that matters for the stated concern: it is the
share of episodes in which sitting still and eating is genuinely viable, and therefore the
share of episodes that contain no warmth-versus-food conflict.

### 4.4 The silent-placement bug — checked for, not found

`resolve_overlaps_global` has a documented silent failure: when no cell satisfies an entity's
validity mask, the entity is parked at cell (0, 0), outside its own declared spawn area, with
nothing raised. Tightening any placement constraint makes it more reachable, so it was
checked directly rather than assumed absent.

- **Fires outside their own spawn box: 0 of 20,000 resets.** Since the fires' box is rows 2–7
  / columns 2–7, a fire at (0, 0) would be unmistakable. None occurred.
- **Food at (0, 0): 832 resets — legitimate, not the bug.** Food's spawn area is the entire
  grid, so (0, 0) is a perfectly valid draw for it. At roughly 4 food items over 100 cells,
  about 4% of resets should show one there by chance; 832 / 20000 = 4.2%. This is the
  expected rate, not a failure signature.
- With the constraint switched on at 2 and at 3 (§3), still **zero** entities outside their
  own spawn area over 1,000 resets each.

No evidence of the bug in any configuration tested. Nothing in this report is skewed by it.

---

## 5. Recommendation

**Turn the separation on. Set it to 2, before any real training run on the thermal config.**

The reasoning, in plain terms:

1. **About one episode in four is currently a free lunch.** In 27.4% of resets (95% CI 26.8 –
   28.0) at least one food item sits on a cell that is both adjacent to a fire and warm
   enough for the agent to stay there forever. In those episodes the optimal policy is to
   walk to that cell and stop. There is no warmth-versus-food conflict to learn, yet the
   episode is counted in every thermal average alongside episodes that do pose the conflict.
   That is a quarter of the evidence diluting the measurement of the exact effect the
   temperature system exists to produce.

2. **The value 2 is the right value, and it is not arbitrary.** The switch blocks food at
   distances *strictly below* the number given, so 2 is the smallest setting that does
   anything at all, and §4.3 shows it is also sufficient: the comfortable ring is exactly one
   cell wide. Going further to 3 would additionally clear the distance-2 band, but that band
   is not a free lunch — an agent resting there settles at about −14 °, one degree from death,
   and is outright killed by it in half of cases. Pushing food out to 3 would remove a
   genuinely difficult, genuinely thermal region of the design space for no benefit.

3. **It is verified to work and it is cheap.** §3 confirms the parameter is read mandatorily,
   is genuinely wired into a second placement pass, and binds at exactly the documented
   distance on the shipped config. At 2 it left the number of placed food items unchanged
   (3.98 per reset, identical to the unconstrained world) and produced no silently misplaced
   entities over 1,000 resets. The cost is one extra placement pass at reset.

**The honest counter-argument.** The effect is concentrated in *episodes*, not in *foraging*.
Only **8.30%** of individual food items are within one cell of a fire — a mean of 0.33 items
out of about 4 per episode. An agent that has already learned to forage across the whole board
is not trapped by this and will spend the overwhelming majority of its eating on food that
does pose a thermal cost. So the case for the switch is not "the task is broken"; it is "a
quarter of the episodes are silently not testing the thing, and the fix is a one-line config
change with a measured zero cost." If the switch is left at 0, the consequence is not a wrong
agent — it is a noisier and optimistically biased estimate of thermal competence, because a
quarter of the episodes can be solved by standing still.

**A second-order note if the switch stays off.** Should the decision be to leave it at 0, then
any thermal analysis should segment episodes by whether a free-lunch cell existed at reset —
the raw per-reset data needed to do that is exactly what §4.3 computes, and the script is
preserved. Reporting a single pooled thermal mean over both kinds of episode would mix two
different tasks under one number.

**Change to make, if accepted.** In the campfire config's `thermal:` block, set
`food_min_fire_distance: 2` (currently `0`). This is a value change to a setting already
present in every full config, so no schema change and no loader work is needed. Because it
alters entity placement, it is a change to a high-impact setting and requires a dated entry in
the critical-settings registry (`docs/environment/CONFIG_CRITICAL_SETTINGS.md`) in the same
change, per that document's logging protocol. It will also change the environment's random
draws for the thermal config, so it must not be applied mid-way through a study whose runs are
meant to be comparable.

---

## 6. Reproducing this

```
JAX_PLATFORMS=cpu /home/vncuser/miniconda3/envs/grid_world_pain/bin/python \
    tmp/20260909_thermal_food_fire_measure.py 20000 500 20260909
JAX_PLATFORMS=cpu /home/vncuser/miniconda3/envs/grid_world_pain/bin/python \
    tmp/20260909_thermal_knob_wiring_check.py
```

Roughly a minute of CPU for the first, seconds for the second. No GPU is involved: this is a
placement measurement and never steps the environment.

## 7. Links

- Temperature-system implementation spec: `docs/develop/active/thermal/IMPLEMENTATION_PLAN.md`
  (decision D3 is the one this document supplies evidence for).
- Entry point and open tasks: `docs/develop/active/thermal/HANDOVER.md` (Task 4).
- Config under test: `configs/environment/experiment/thermal/campfire_world.yaml`.
- Placement code: `src/environment/core.py` — `resolve_overlaps_global` (first pass, and the
  fire-separation constraint), `relocate_blocked_entities` (the food-distance second pass),
  `jax_reset` (which gates both).
- Existing test coverage: `tests/env/test_thermal_field.py` —
  `test_fires_respect_min_separation`, `test_food_min_fire_distance_is_enforced_when_enabled`,
  `test_placement_constraints_are_noops_when_disabled`.
