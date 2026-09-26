---
title: "Keep bushes away from campfires: a configurable world-generation rule"
topic: env_entities
status: active
created: 2026-09-26
last_updated: 2026-09-26
aliases: [bush_fire_clearance]
---

# Keep bushes away from campfires: a configurable world-generation rule

> **Status**: PLANNED. Waiting on the user's decisions in §Decisions, then `plan-reviewer`, then approval. Nothing is implemented.
> **Opened**: 2026-09-26
> **Related**: [[STATE_DEPENDENT_BODY_MECHANICS]] (the closest precedent: static off-switch keys, the parity fixture, the saved-run compat slice) · [[SAVED_RUN_CONFIG_COMPAT]] (general old-run loading plan; **read, not edited**, another session owns it) · [[IMPLEMENTATION_PLAN]] (thermal; where the fire-separation and food-distance placement rules were built) · [[WARMING_COOLING_RATE_SCALES]] (the body-temperature settling point used below) · [[KNOWN_BUGS]] (row "An entity whose spawn area is full is silently parked at cell (0,0)") · the internal-state interaction study, `docs/experiments/active/internal_state_interactions/STUDY_PLAN.md` (the motivation; owned by the experiment agents; backlink to be added by them)

---

## Context

In the campfire world (curriculum level 05), the world generator places bushes (hiding spots that conceal the agent from predators) and campfires (heat sources) independently of each other. So sometimes a bush lands right next to a fire. That one cell then offers safety from predators and warmth at the same time.

A simulation study of how the agent's body states interact found this matters. When such a "warm bush" exists, the best action depends much less on combinations of body states: the combination effect measured 7.2 with a warm bush against 18.1 without. Today 7.8% of bushes sit right beside a fire, and 41% of episodes contain at least one warm bush.

This plan adds a setting, `thermal.bush_min_fire_distance`, that keeps every bush at least a chosen number of steps away from every fire. It ships **off**. Off means the world is generated exactly as today, down to the same random numbers and the same positions, and a test proves that. When the setting is on, only bushes move. Food, predators, rocks and the fires themselves stay exactly where they would have been.

The rule is not switched on in level 05. It is for experiment variants, which `experiment-designer` writes, and the user decides later where to use it.

**Size.** Roughly 150 lines of production code (reset, loader, params, saved-run compatibility), about 350 lines of tests plus one small fixture generator, about 40 lines of docs. One `developer` session.

---

## Decisions the user must make

The plan is written so each option is a one-line switch in the File Changes. Recommendations are marked.

### D1 — How far must a bush stay from a fire?

What a cell near a fire is like, measured on 400 real level-05 resets (the full table is in §A2). "Body settles at" is where the agent's body temperature ends up if it stays in that cell. The body dies of cold below −15.

| Cell | Steps from fire | Cell temperature | Body settles at | Share of today's bushes |
|---|---|---|---|---|
| Directly beside the fire (4 cells) | 1 | +8.7 | **+5.8, comfortable** | 7.4% |
| Diagonal to the fire (4 cells) | 2 | −15.9 | **−10.6: cold, but survivable forever** | 7.7% |
| Two cells straight out (4 cells) | 2 | −27.8 | −18.6: freezes to death | 8.0% |
| Everything farther | 3+ | about −29 to −30 | about −19 to −20: freezes | 77% |

"Steps" here means grid steps without diagonal moves. The fire-separation and food-distance rules count distance the same way, and so does the study's measurement script.

The subtlety is that the diagonal cells sit at the same step count as the cold "two straight out" cells, but they are much warmer. So "one cell of clearance" and "two cells of clearance" differ in more than just distance:

- **Option A: one cell of clearance (`bush_min_fire_distance: 2`).** Bushes may not sit directly beside a fire. The comfortable warm bush disappears: the study's warm-bush share goes to 0. But a bush may still sit diagonally, where the body settles at −10.6. That is below the comfortable setpoint of 0, but the agent can hide there forever without freezing. Today 7.7% of bushes are diagonal. This option leaves a weaker version of the shortcut in place. 5 cells are blocked per fire.
- **Option B (recommended): two cells of clearance (`bush_min_fire_distance: 3`).** Bushes may not sit beside, diagonal to, or two cells straight out from a fire. No bush is anywhere the agent can survive indefinitely, so hiding and staying warm are always two separate places, at least two steps apart. The cost is that it also blocks the four "two straight out" cells, which are freezing anyway. That is a slightly bigger exclusion zone than strictly needed: 13 cells per fire instead of 9. It fits easily on the 10×10 map (§A3).
- **Option C (exact, not recommended): block the 3×3 square around each fire.** This blocks exactly the 8 cells where the body survives. It needs a second setting, a distance-metric choice, because every other placement rule here counts steps without diagonals. It is only worth it if the four freezing cells matter to the experiment.

**Recommendation: B.** The study's point is that warmth and safety should never be available in the same cell. A diagonal bush where the agent can wait indefinitely is still most of that shortcut.

### D2 — Do fires that are not burning this episode count?

Level 05 allocates three fire slots and lights one to three of them per episode. The world generator places all three slots first and decides which ones burn afterwards.

- **Burning fires only (recommended).** Bushes avoid only real fires. Compared with level 05, the bush layout changes only near fires that actually exist, which is the cleanest contrast for the experiment. It costs about 10 extra lines: the "which fires burn" draw has to be available before bushes are moved. That draw never depends on positions, so this moves no random number.
- **Every fire slot.** This matches how the two existing fire rules work. It is simpler, but in an average episode about one ghost fire leaves an unexplained bush-free patch (13 cells under D1-B) where nothing is burning.

### Not decisions (stated so they can be objected to)

- **What counts as a bush:** any obstacle slot with `hides_agent: true` that is not itself a heat source. The name uses "bush" because that is the project's word for it.
- **The value 1 is refused.** It would block only the fire's own cell, and that cell is already occupied. The value is meaningless, and the extra code it would compile would break graph parity for no reason.
- **Placement mode `per_type`** is refused with this rule on, the same as the two existing fire rules.

---

## Analysis

### A0 — Wiki pull gate and known bugs

The LLM Wiki's `env_entities` and `config_system` folders were checked. Two entries bear on this plan:

- **`20260909_1402_parity_gates_green_without_comparing`.** Parity gates must **fail, not skip**, when their fixture is missing. The new parity test carries that rule, as the body-mechanics one does.
- **`20260624_0517_bush_spawn_exclusion_free_via_overlap_resolution`.** Animals never spawn on a bush cell because the overlap scan gives every entity its own cell. The relocation pass below keeps that true: a bush moves only onto a cell that no entity holds (§Design).

Known-bug rows on placement, reset and PRNG (grepped from `KNOWN_BUGS.md`, not loaded whole):

| Row | Bearing on this plan |
|---|---|
| **An entity whose spawn area is full is silently parked at cell (0,0)** (OPEN, `KNOWN_BUGS.md:117`) | The relocation helper this plan reuses (`relocate_blocked_entities`) carries that same silent fallback. This plan does **not** fix the row. It makes the fallback unreachable for the new pass with a load-time feasibility check (§A3), and the test asserts every bush lands inside its own spawn area over 1,000 resets. After landing, `bug-curator` should note the new, guarded caller on the row. |
| **Environment reset is not bit-identical across compilations** (one-ULP float difference, 2026-08-20) | The parity fixture and test run on CPU only (conftest), as the body-mechanics precedent does. Positions are integers and are unaffected. |
| rPPO rollout reused reset and step PRNG bits; stochastic eval reused one key (both FIXED) | These concern the trainer's key handling, not `jax_reset`. Not touched here. |

### A1 — Where placement happens today (code as truth, `v4.0`, 2026-09-26)

`core.jax_reset` (`src/environment/core.py`, from line ~1700; a parallel session has uncommitted hardening edits in this file, so locate code by the anchors quoted here, not by line number):

1. **One overlap scan over every entity**, in the fixed order `[resources, predators, obstacles, neutral animals]`. Fires and bushes are both **obstacles**. Their relative order inside the obstacle block is the order of the `obstacles:` list in the config. Level 05 lists `campfire` before `bush`, but nothing guarantees that. `resolve_overlaps_global` (~1328) draws **one** permutation and walks it, with zero per-entity draws.
2. **The fire-separation rule** (`min_fire_separation`, "D2" in the thermal plan) is an extra term in that scan's validity mask, behind a static Python `if`.
3. **The food-to-fire rule** (`food_min_fire_distance`, "D3") is a **second pass**, `relocate_blocked_entities` (~1411). It moves only marked entities off a blocked-cell mask. It draws one permutation from `fold_in(resolve_key, _THERMAL_FOOD_KEY = 0xF00D)`, behind a static `if _food_min_dist > 0`. Its docstring explains why "nothing else moves" is load-bearing: a full re-scan once dragged a fire.
4. **Activation masks** (which slots are live this episode; §7b, ~2007) are drawn **after** placement from `fold_in(property_key, 0xC0A1..3)`. They depend on nothing about positions. Inactive slots are then parked off-grid at `(height, width)`.
5. **The thermal field** is built after parking, so an inactive fire stamps no heat.

The bush rule is the same shape as D3: "entity type X must not sit near a fire". It is order-independent only as a **post-pass over final positions**. A term in the first scan would work when fires come before bushes in the config and fail silently when they come after. So this plan reuses `relocate_blocked_entities` unchanged and adds a third pass after D3.

### A2 — The distance metric, and what the numbers mean

- **Thermal field** (`_gaussian_smooth_normalised`, ~1574): a separable Gaussian blur, σ = 0.7, kernel radius 3. Its weight is `exp(−(dr² + dc²)/2σ²)`, so heat falls off with **straight-line (Euclidean)** distance. That is why the diagonal cell (straight-line √2) is far warmer than "two straight out" (straight-line 2), even though both are 2 steps away.
- **`measure_world.py`**: **Manhattan** (steps without diagonals). Its `warm_bush_episode_share` counts a bush at Manhattan ≤ 1 from a fire.
- **Existing placement rules** (`min_fire_separation`, `food_min_fire_distance`): **Manhattan**, with a blocked cell meaning `distance < value`.

The new key follows the placement rules (Manhattan, `<`) so all three read the same way.

**Measured for this plan** (400 level-05 resets through the live loader and `jax_reset`, CPU; script in the session scratchpad, not committed). Classes are (Manhattan, Chebyshev) distance to the nearest burning fire. Body settling point `T* = k_exchange·T_cell/(k_exchange + k_loss) = 0.667·T_cell` at the canonical `k_exchange` 0.04, `k_loss` 0.02, `k_metabolic` 0 (registry row `thermal.k_loss`). The rate scales change how fast the body gets there, not where it settles.

| (Manhattan, Chebyshev) | What it is | Cell temp median [p10, p90] | Body settles at (median) | Share of bushes today |
|---|---|---|---|---|
| (0, 0) | fire | +76.9 [75.1, 79.3] | +51.2 (lethal heat) | — |
| (1, 1) | beside | +8.7 [8.4, 9.2] | +5.8 | 7.4% |
| (2, 1) | diagonal | −15.9 [−16.4, −15.2] | −10.6 | 7.7% |
| (2, 2) | two straight | −27.8 [−28.9, −27.0] | −18.6 | 8.0% |
| (3, 2) | knight's move | −29.1 | −19.4 | 14.5% |
| (≥3, 3) / (4+, ·) | far | ≈ −29.9 | ≈ −20 | 62% |

These reproduce the study's figures: its "d2 −16.5 [−28.6, −15.6]" is the diagonal and two-straight classes pooled. Episode shares today: a bush at Manhattan ≤ 1 in **41%** of episodes (matches `world_measurements.json`), in the 3×3 square in **64.5%**, and at Manhattan ≤ 2 in **77.5%**.

Caveat for D1: under B4 (injury speeds heat exchange, currently off everywhere) the settling point moves toward the cell temperature. A heavily injured agent in a diagonal cell would then settle below −15. The ranking of the options does not change.

### A3 — Feasibility: why the pass cannot fail on a 10×10 map, and how the loader proves it

The pass has no loops on traced values and no rejection sampling. For each bush slot in order, it takes the first cell in one pre-drawn permutation that is (i) inside the bush's spawn area, (ii) free, and (iii) not blocked. That is a fixed-length `lax.scan`, so it cannot deadlock. The only failure mode is "no such cell", which hits the silent (0,0) fallback. The loader rules that out with a worst-case bound. All slots are counted at `count_high` and every fire slot is assumed burning.

For each distinct spawn area `A` of a bush entry, require

```
|A|  −  n_fire_slots · D(v)  −  n_other_slots  ≥  n_bush_slots
```

- `D(v) = 2v² − 2v + 1` is the number of cells at Manhattan distance `< v` from a fire, the fire's own cell included. D(2) = 5, D(3) = 13 (option C: `(2v−1)²` = 9).
- `n_other_slots` = every resource, animal and non-bush, non-fire obstacle slot. Any of them might sit inside `A`.

**Why it is sufficient.** When the last bush moves, at most `n_fire·D(v)` cells of `A` are blocked, and at most `n_other + n_bush − 1` are held by other entities. So at least one valid cell remains. Edge clipping of the blocked disks only makes the real count larger.

**Level 05 at `count_high`:** |A| = 100 (bush area is the whole grid), fire slots 3, bush slots 10, other slots 45 − 10 − 3 = 32.

| Option | Left-hand side | Needed | Margin |
|---|---|---|---|
| A (v = 2) | 100 − 15 − 32 = 53 | 10 | 43 |
| B (v = 3) | 100 − 39 − 32 = 29 | 10 | 19 |
| C (3×3 square) | 100 − 27 − 32 = 41 | 10 | 31 |

The bound is conservative: it may refuse a crowded world that would in fact always fit. The error message names the three counts and says to lower the value, the bush `count_high` or the fire `count_high`, or to widen the bush area. Distinct areas are checked separately, and the message names the entry.

### A4 — Random numbers: what moves and what does not

- **Off (value 0):** the new code sits behind a static Python `if params.thermal_bush_min_fire_distance > 0`, the same pattern as D3. No `fold_in`, no permutation, no ops are emitted, so the `jax_reset` jaxpr and every reset output are identical to today. Hoisting the pure-Python definition of `_build_activation_mask` (D2 "burning only") emits nothing by itself. The parity test proves both claims instead of assuming them.
- **On:** the pass draws its one permutation from `fold_in(resolve_key, _THERMAL_BUSH_KEY)`, a **new, independent** stream. `fold_in` does not advance or consume `resolve_key`, so food, predators, neutral animals, rocks, fires, the activation masks, the thermal field, properties and the body draws are **byte-identical to the rule-off world with the same seed**. Only bush positions differ. A test asserts exactly this, which also pins the claim "only bushes move". (The episodes of course diverge after reset, because the agent meets a different layout.)
- The constant must not collide with the other `fold_in` constants on `resolve_key` (today only `0xF00D`). The proposed value is `0xB05E`.
- **Distribution:** a displaced bush takes the first valid cell in a uniform random permutation. That is a uniform draw over the allowed free cells in its area. Bushes that were already clear of fires do not move.

### A5 — Static field and recompilation

`thermal_bush_min_fire_distance: int = struct.field(pytree_node=False)` on `EnvParams`, next to `thermal_food_min_fire_distance` (`state.py:387`). It must be static because it is read by a Python `if` and fixes the graph. Consequences:

- Each distinct value compiles its own `jax_reset`/`jax_step`. This is one compile per world, the same as D2/D3. It cannot be swept inside one vmapped batch of environments.
- Changing it between runs is free. Changing it mid-run forces a recompile. Nothing does that.
- When `thermal.enabled` is false, the loader pins it to `0` without reading it, next to the D2/D3 pins at `config_loader.py:~1827`. A thermal-off config therefore does **not** need the key.

### A6 — Old runs: saved-config compatibility, and a latent bug in the compat slice

The new key is **thermal-conditional mandatory**. Every finished thermal-on run's saved `models/config.yaml` lacks it, and `load_env_params` would raise when an analysis tool re-opens that run. The fix follows [[STATE_DEPENDENT_BODY_MECHANICS]] §A7: add a row to `_ERA_KEYS` in `src/environment/saved_config_compat.py` at the inert value `0`, supplied only when the saved `thermal.enabled` is true.

**But a straight append would break the module.** Its rule (c), "all-or-none per block", is keyed on the **block prefix**: `_THERMAL_KEYS = tuple(k for k in _ERA_KEYS if k.startswith("thermal."))`. Consider a run trained after the body-mechanics change but before this one. It carries the four body-mechanics thermal keys and lacks the new one. After an append, that config would be "4 of 5 present" and **refused as an edited file**. Level-05 runs trained from today onward are exactly that population.

**Required change:** all-or-none is checked per **(block, era)** group, not per block. Each era's keys arrived together, so "some of an era's keys but not all" still means an edited file. Keys from different eras are independent. The existing error text (`"thermal block carries"`) is kept, so the existing refusal tests still match. A regression test that fails on today's code is specified in §File Changes. This matches what [[SAVED_RUN_CONFIG_COMPAT]] itself specifies ("keys are independent", its Design item 2), so the owner can absorb it.

`SAVED_RUN_CONFIG_COMPAT.md` is being edited by another session right now (`git status` shows it staged and modified). This plan does **not** touch that doc. §Hand-off records what the owner needs to know.

**Trajectory-store fingerprints are unaffected.** The compat step runs on a deep copy, and the fingerprint and manifest see the raw saved file (body-mechanics §A7 / compat §A10). Eval recordings (`.rec.gz`) pickle `EnvParams`. An unpickled old object lacks the new field, but recordings are only rendered, never reset. The developer greps for `.replace(` / `dataclasses.replace` on unpickled params (the renderer's existing workaround is at `render_recordings_v2.py:~184–193`). No change is expected.

### A7 — Roll-out: who must carry the new key

The key is read only when `thermal.enabled` is true, so the population is the **raw-loaded thermal-on inputs** (measured by grepping for the sibling key `food_min_fire_distance`):

| File | Action |
|---|---|
| `configs/environment/default.yaml` | add `bush_min_fire_distance: 0` under `thermal:` → placement constraints, with a comment. Every `basic/` world inherits it; **`basic/05` and `basic/06` are not edited.** |
| `configs/environment/experiment/archive/thermal/campfire_world.yaml`, `…/campfire_world_body_temp_hidden.yaml` | Archived, but they are **live test inputs** (loaded raw by the thermal test modules and two fixture generators). Add the off value inline, as the 2026-09-17 and body-mechanics precedents did. |
| `tests/env/fixtures/frozen_parity_worlds/environment__default.yaml` | Only if a test loads it with thermal **on**. It carries `food_min_fire_distance`, so the developer checks. If needed, add the key in its "ADDED AFTER THE FREEZE" block. |
| `configs/environment/experiment/archive/basic_vec8/default.yaml` | Archived, not a live input. **Not migrated** (project policy). |
| `tests/env/fixtures/saved_run_configs/*.yaml` | **Never edited.** These are verbatim saved configs, and the compat step supplies the key. |

The developer re-greps `configs tests scripts` for `food_min_fire_distance` at implementation time and records the list. Any inline YAML base in a test module that turns thermal on needs the key too.

---

## Implementation Plan

### Design

```
jax_reset, placement_mode == 'per_entity'
  1. sample positions               (unchanged)
  2. resolve_overlaps_global        (unchanged; D2 term if min_fire_separation > 0)
  3. D3 food pass                   (unchanged; if food_min_fire_distance > 0)
  4. NEW bush pass                  (if bush_min_fire_distance > 0; static)
       blocked  = cells at Manhattan < v from a [burning] fire slot
       movable  = [active] bush slots (hides_agent & ~heat_source)
       relocate_blocked_entities(..., key=fold_in(resolve_key, 0xB05E))
  ... activation masks, parking, thermal field  (unchanged)
```

`[burning]` and `[active]` apply under D2 "burning only". Under "every slot" both brackets are dropped and the activation hoist is not needed.

Why D3's pass is reused and not a new term in the first scan: see §A1. Why the pass keeps every earlier guarantee:

- It moves only bushes, onto free cells, so fires never move. D2 (fire separation) and D3 (food distance, which depends only on fire positions) still hold.
- Animals still never share a bush cell.
- The (0,0) fallback is unreachable by §A3.

### File Changes

#### `src/environment/state.py` (after line 387)

```python
    thermal_bush_min_fire_distance: int = struct.field(pytree_node=False)  # Manhattan; 0 = disabled
```

#### `src/environment/core.py`

(a) Next to `_THERMAL_FOOD_KEY` (~1552):

```python
_THERMAL_BUSH_KEY = 0xB05E    # bush-to-fire clearance pass (BUSH_FIRE_CLEARANCE)
```

(b) **D2 "burning only" only.** Hoist the nested `_COUNT_KEY_RES/_ANIMAL/_OBS` constants and the `def _build_activation_mask(...)` (currently in §7b, ~2007–2060) to just before `# 2. Entity Placement`, unchanged. Moving a pure-Python `def` emits no ops, and the parity test's jaxpr SHA is the proof. §7b keeps its three calls exactly as they are.

(c) In the `per_entity` branch: widen the guard that builds `_is_fire_concat` to include the new rule, and add the pass after the D3 block, inside `if all_positions.shape[0] > 0:`:

```python
        _bush_min_dist = params.thermal_bush_min_fire_distance
        ...
        if _min_fire_sep > 0 or _food_min_dist > 0 or _bush_min_dist > 0:
            ...  # builds _obs_is_fire / _is_fire_concat, unchanged

            # (after the D3 block)
            # Bush clearance — "no bush within v of a fire". A post-pass over FINAL
            # positions, so it holds whatever order fires and bushes have in the
            # obstacle list. Moves ONLY bushes; fires cannot move, so D2 and D3 still
            # hold. Unreachable when off (static), so the off graph is today's.
            if _bush_min_dist > 0:
                # D2 "burning only": the activation draw depends on property_key alone,
                # never on placement, so this is the same mask §7b draws later.
                _obs_act = _build_activation_mask(
                    params.obs_count_low, params.obs_count_high, params.obs_entry_id,
                    params.has_obs_range, _COUNT_KEY_OBS, num_obs, property_key)
                _total_cells = params.height * params.width
                _cr = jnp.arange(_total_cells) // params.width
                _cc = jnp.arange(_total_cells) % params.width
                _d = (jnp.abs(_cr[None, :] - all_positions[:, 0][:, None])
                      + jnp.abs(_cc[None, :] - all_positions[:, 1][:, None]))
                _burning = _is_fire_concat & jnp.concatenate([
                    jnp.ones(num_res, dtype=jnp.bool_),
                    jnp.ones(num_pred_class, dtype=jnp.bool_),
                    _obs_act,
                    jnp.ones(num_neutral_class, dtype=jnp.bool_)])
                _near_fire = jnp.any((_d < _bush_min_dist) & _burning[:, None], axis=0)
                _is_bush_concat = jnp.concatenate([
                    jnp.zeros(num_res, dtype=jnp.bool_),
                    jnp.zeros(num_pred_class, dtype=jnp.bool_),
                    params.obs_hides_agent & ~_obs_is_fire & _obs_act,
                    jnp.zeros(num_neutral_class, dtype=jnp.bool_)])
                _bush_key = jax.random.fold_in(resolve_key, _THERMAL_BUSH_KEY)
                all_positions = relocate_blocked_entities(
                    all_positions, all_spawn_areas, params.height, params.width, _bush_key,
                    entity_mask=_is_bush_concat, blocked_cells=_near_fire)
```

Under D2 "every slot": drop `_obs_act` and `_burning`, and use `_is_fire_concat` and `params.obs_hides_agent & ~_obs_is_fire` directly.

`_d` is recomputed after the D3 pass on purpose. It must use the positions after D3, even though only food moved.

(d) Update the `resolve_overlaps_global` / `relocate_blocked_entities` docstrings: one sentence naming the third caller and that its feasibility is checked at load.

#### `src/environment/config_loader.py`

Anchors: the D2/D3 reads (~1608–1618), the thermal-off pins (~1827), the `per_type` guard (~2240), the `EnvParams(...)` call (~2700).

1. **Read and validate** (thermal-on branch, after `_th_food_min_dist`):
   ```python
   _th_bush_min_dist = int(config.get_mandatory('thermal.bush_min_fire_distance'))
   if _th_bush_min_dist < 0 or _th_bush_min_dist == 1:
       raise ValueError(
           f"thermal.bush_min_fire_distance must be 0 (off) or >= 2 (Manhattan cells; a "
           f"bush may not sit at distance < value from a fire). 1 would block only the "
           f"fire's own cell, which is already occupied. Got {_th_bush_min_dist}.")
   ```
2. **Thermal-off pin:** `_th_bush_min_dist = 0` next to `_th_food_min_dist = 0`.
3. **`per_type` guard:** add `_th_bush_min_dist > 0` to the condition and name the key in the message.
4. **Structure and feasibility checks when `_th_bush_min_dist > 0`**, placed after the per-slot arrays exist (next to the `_check_thermal_structure` call). As a small module-level helper `_check_bush_fire_clearance(...)`, all numpy on config constants, it raises `ValueError` when:
   - no obstacle slot is a heat source (`core.heat_source_mask`), or no obstacle slot has `hides_agent`. A rule that is set but has nothing to act on is a config mistake;
   - any obstacle slot is both a heat source and `hides_agent`. The rule would be self-contradictory;
   - any **resource** slot is a heat source. Resources stamp heat into the field, but the rule only sees obstacle fires, so a warm bush could survive silently;
   - the §A3 bound fails for any bush entry's spawn area. The message names the entry, `|A|`, `n_fire_slots·D(v)`, `n_other_slots` and `n_bush_slots`.
5. Pass `thermal_bush_min_fire_distance=_th_bush_min_dist` to `EnvParams`.

A parallel session has uncommitted edits in `config_loader.py` and `core.py`. Before starting, the developer runs `git diff -- src/environment/config_loader.py src/environment/core.py`. If those hunks are still uncommitted, the developer waits or coordinates. Never commit another session's hunks.

#### `src/environment/saved_config_compat.py`

- Rename `_ERA` → `_ERA_BODY_MECHANICS` (grep the tests for imports of `_ERA` first). Add `_ERA_BUSH = "BUSH_FIRE_CLEARANCE C2 (<commit date>)"`.
- Add the row:
  ```python
  "thermal.bush_min_fire_distance": (
      0, _ERA_BUSH,
      "static `if params.thermal_bush_min_fire_distance > 0` in core.jax_reset; 0 = the "
      "bush pass is not traced (tests/env/test_bush_fire_clearance.py parity)."),
  ```
- Replace the block-level `_THERMAL_KEYS` / `_BODY_KEYS` all-or-none with per-**(block, era)** groups. Supply thermal groups only when `thermal.enabled` is true. Keep the refusal wording (`"thermal block carries"`, `"body block carries"`) and the WARNING line.
- Update the module docstring: `_ERA_KEYS` now holds two eras, and all-or-none is per era (§A6).

#### `configs/environment/default.yaml` (thermal block, after `food_min_fire_distance: 0`)

```yaml
  # Minimum Manhattan distance from a bush (any obstacle with hides_agent) to any
  # burning fire: a bush may not sit at distance < value. 0 = no constraint, which is
  # today's placement exactly (same random numbers, same positions); 1 is refused;
  # 2 = not beside a fire; 3 = not beside, diagonal to, or two cells straight out.
  # A non-zero value costs a third placement pass that moves only bushes.
  # See docs/develop/active/thermal/BUSH_FIRE_CLEARANCE.md.
  bush_min_fire_distance: 0
```

(Say "burning" or "any" according to D2.)

#### Archived test inputs (`campfire_world.yaml`, `campfire_world_body_temp_hidden.yaml`)

Add `bush_min_fire_distance: 0` inline with the precedent comment (§A7).

#### `scripts/fixtures/generate_bush_fire_clearance_parity_fixture.py` (NEW)

It is modelled on and imports from `generate_body_mechanics_parity_fixture.py` (`jaxpr_shas`, `_leaf_name`). It must be run in a **clean `git worktree` of the pre-change commit**, because a parallel session's uncommitted edits in the main checkout would contaminate it. It records, per world:

- the `jax_reset` and `jax_step` jaxpr SHA-1;
- every `EnvState` leaf of `jax_reset` for seeds `0..63`;
- the resolved config YAML;
- `_provenance_sha`.

Worlds:

- `lvl05` (thermal on);
- `lvl05_d3`: level 05 with `food_min_fire_distance: 4` in memory, so the new branch's neighbour is exercised;
- `lvl04` (thermal off);
- `default`.

Output: `tests/env/fixtures/bush_fire_clearance_parity/pre_change_resets.npz`.

#### `tests/env/test_bush_fire_clearance.py` (NEW). Fails, never skips, on a missing fixture. CPU only.

| Test | What it proves |
|---|---|
| `test_off_jaxpr_identical[world]` | `jax_reset` and `jax_step` jaxpr SHA-1 at value 0 equal the pre-change fixture. |
| `test_off_resets_byte_identical[world]` | Every `EnvState` leaf for 64 seeds `np.array_equal` to the fixture: same draws, same positions. |
| `test_no_unrelated_config_drift[world]` | The resolved config minus the new key equals the stamped one, with its own message. |
| `test_no_bush_near_a_fire[v]` (v = chosen D1 value, plus 2 if B/C chosen) | Level 05 with fire `count: 3` and bush `count: 10` fixed (stress), and again at the natural ranges. Over **1,000** vmapped resets: no active bush at Manhattan `< v` from a burning fire. Every active bush inside its own spawn area (the (0,0) guard). No two active entities share a cell. |
| `test_on_moves_only_bushes` | Same seeds on vs off. `res_pos`, `animal_pos`, every non-bush `obs_pos`, `obs_active`, `thermal_field` and all sampled properties are identical. Some bush positions differ (not vacuous). |
| `test_on_changes_the_reset_graph` | At v > 0 the `jax_reset` jaxpr SHA differs from value 0. This is the contrast that makes the off-parity test non-vacuous. |
| `test_existing_rules_still_hold_when_on` | With `food_min_fire_distance: 4` and the bush rule on: fire separation ≥ `min_fire_separation`, no food at `< 4`, no bush at `< v`. |
| `test_loader_refusals` (parametrized) | Refuses −1; refuses 1; refuses `per_type`; refuses no fire slot; refuses no bush slot; refuses a slot that is both bush and fire; refuses a resource heat source; refuses the infeasible world (e.g. 5×5 grid, 3 fires, 10 bushes). Each with a message regex. |
| `test_thermal_off_needs_no_key` | A thermal-off config without the key loads, and the field is 0. |

#### Existing tests to update

- `tests/env/test_saved_config_compat.py`:
  - `_SIX` → the seven expected keys (the two fixtures are thermal-on); rename `test_fixture_loads_through_shim_with_exactly_six_keys` accordingly;
  - **add the regression test** `test_body_mechanics_era_config_gets_only_the_bush_key`. A fixture with the four body-mechanics thermal keys and the two body keys present, but no bush key, gets exactly `["thermal.bush_min_fire_distance"]` and is not refused. **This test must fail on today's module** (it raises "thermal block carries"). The developer records that failure before the fix;
  - add `test_partial_era_group_is_still_refused` (two of the four body-mechanics thermal keys, with the bush key present, is still refused).
- `tests/env/test_body_mechanics_parity.py`: its drift check drops only its own 15 keys, and the resolved level-05 config at HEAD will now carry the new key. Add a separate `LATER_INERT_KEYS = ("thermal.bush_min_fire_distance",)`, dropped in `test_no_unrelated_config_drift`, with a comment pointing here. Its jaxpr and rollout tests must pass **unchanged**, which independently corroborates off-parity.
- `tests/env/test_thermal_field.py::test_placement_constraints_are_noops_when_disabled`: set and assert the new key at 0 alongside the two existing ones.
- `tests/env/test_thermal_validation.py`: add the new key to the missing-key parametrization (the `stage1_food_min_fire_distance` pattern, ~line 216) and a negative-value case.

#### `scripts/analysis/studies/internal_state_interactions/measure_world.py`

- Add `--bush-min-fire-distance N`, optional. When given, it sets `thermal.bush_min_fire_distance` in memory after `load_env_config` and prints that it did. No config file is written, and no `configs/` file is created or edited.
- Add `--out PATH`. It is **required when `--bush-min-fire-distance` is given**, so a variant run can never overwrite the study's `world_measurements.json`. Without the flag the script behaves and writes exactly as today.
- Add one output field, `bushes_by_fire_class`: the share of active bushes in each (Manhattan, Chebyshev) class of §A2, so the diagonal bushes are visible and not just the ring.
- Update the docstring's invocation line.

#### Docs (same change, per their maintenance contracts)

- `docs/environment/CONFIG_GUIDE.md`: the thermal block listing (~317) and the placement notes (~414): one line plus a short note (off = today, the refused values, it moves only bushes, the feasibility refusal).
- `docs/environment/02_config_schema.md`: a row next to `food_min_fire_distance` (~83) and a sentence in the placement paragraph (~171).
- `docs/environment/CONFIG_CRITICAL_SETTINGS.md`: a registry row for `thermal.bush_min_fire_distance` (canonical **0**, `default.yaml`, what it does, "0 is the only value that leaves the placement graph unchanged", read only when thermal is on). Plus a **dated change-log entry**: new key added, canonical off, no world enables it, saved runs get 0 through the compat step, parity result.
- `docs/environment/SCRIPTS_DEPENDENCY_MAP.md`: add the new fixture generator (caller: `tests/env/test_bush_fire_clearance.py`, via the fixture) and the `measure_world.py` flags in the `internal_state_interactions` row.
- Any other `docs/environment/*` page that documents `food_min_fire_distance`: the developer greps and mirrors.

### Commit sequence

| Commit | Content | Gate |
|---|---|---|
| C0 | Compat per-era grouping plus the new row, compat tests (the regression test fails first, then passes). | `pytest tests/env/test_saved_config_compat.py` green. Supplying a key the loader does not yet read is harmless, because the loader ignores unknown keys. |
| C1 | Fixture generator plus the fixture, from a pre-change worktree. | Fixture `_provenance_sha` = the C0 commit. |
| C2 | state, core, loader, default.yaml, archived test inputs, new tests, existing-test edits, docs. | `pytest tests/env` green; `test_body_mechanics_parity.py` and `test_thermal_parity.py` green unchanged except the drift ignore. |
| C3 | `measure_world.py` flags plus the verification run (CP6). | CP6 numbers recorded. |

**Pre-flight for C2.** At value 0 the change is byte-identical, so a trajectory collection that is live when C2 lands cannot mix worlds. Still, check today's diary and `pgrep -af collect_trajectories` via the `gpu-status` skill's path, as the precedent did, and record the result.

---

## Checkpoints

- [ ] **CP0**: before any code, run `git diff` on `core.py` / `config_loader.py`. If there are foreign uncommitted hunks, coordinate. Record it.
- [ ] **CP1**: the compat regression test fails on the pre-C0 module with "thermal block carries". Paste the output.
- [ ] **CP2**: the fixture was generated in a worktree at a named SHA, and `_provenance_sha` matches.
- [ ] **CP3**: off-parity: jaxpr SHAs and 64-seed reset leaves identical for all four worlds.
- [ ] **CP4**: on: 1,000 resets at each tested v give 0 violations, 0 bushes outside their area, and 0 shared cells. Non-bush state is identical to off.
- [ ] **CP5**: loader: each refusal fires with its message. The level-05 feasibility margin for the chosen v is logged and matches §A3 (53 / 29 / 41).
- [ ] **CP6**: run `measure_world.py --src-root <repo> --resets 300 --bush-min-fire-distance <v> --out tmp/<ts>_bush_clearance_measure.json`. Required: `warm_bush_episode_share == 0.0` and `share_of_bushes_on_a_fire_ring == 0.0`. Under D1-B, also 0 bushes in the diagonal class. The cell-temperature-by-distance table is unchanged from `world_measurements.json` within sampling noise, because fires do not move. Paste the JSON summary.
- [ ] **CP7**: a saved Wave 2 level-05 config still loads through the compat step and gets 0 for the new key. The store fingerprint equals `env_fingerprint(raw)`.
- [ ] **CP8 (speed)**: `jax_reset` throughput (vmapped, 1,024 envs, CPU and one GPU) at 0 vs the chosen v; plus a short level-05 rPPO run at value 0 vs HEAD. Expected: no change at 0 (identical graph), and a small reset-only cost when on. Record before/after.

## Hand-off to the owner of [[SAVED_RUN_CONFIG_COMPAT]]

- `_ERA_KEYS` gains a second era (this key). All-or-none is now checked per (block, era), not per block. This matches that plan's own "keys are independent" design item.
- The value `0` is a claim about old code: before this change there was no bush pass. Changing it later is a breaking change for trajectory stores, per that module's rule.

## Out of scope

- Enabling the rule in any world. `experiment-designer` writes the level-05 variant(s), and the user decides.
- Fixing the silent (0,0) placement fallback in general (the OPEN `KNOWN_BUGS` row). This plan only makes it unreachable for the new pass.
- Keeping **food** or other entities away from bushes, or keeping fires away from bushes. Only bushes move.
- Retuning any thermal value.

---

## Implementation Report

> **Implemented by**: _(developer)_
> **Date**: _(date)_

_(Commits, file-by-file changes, test output, CP results, speed numbers, deviations.)_

## Verification Report

> **Verified by**: _(senior-developer)_
> **Date**: _(date)_

_(Per-file table, independent checks, speed verdict, conclusion.)_
