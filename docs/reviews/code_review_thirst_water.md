---
title: "Code review — water / thirst implementation (JAX/Flax correctness)"
topic: thirst
status: active
created: 2026-09-30
last_updated: 2026-09-30
---

# Code review: the pond and the hydration axis (JAX/Flax correctness)

## Verdict

**APPROVED — no Critical or Moderate findings.** The water/thirst change (a pond the agent
drinks from, a hydration level that drains each step, two new ways to die: dehydration and
over-drinking) is implemented the way this codebase requires: every new piece of environment
state and every new setting is gated behind one on/off switch, and with the switch off the
environment computes literally the same graph and the same numbers as before the change.
I verified this by running the parity test suite (byte-for-byte replay of pre-change rollouts
plus graph fingerprints), and by probing the parts a test cannot easily show — the pickling
hook, the random-number streams, vectorised execution, and the uniformity of the new food
respawn repair — with small scripts. Everything held.

What I looked at, in plain words: (1) the two new state fields that are absent (`None`) on
every world without water; (2) the fourteen new static settings and the hook that fills them
in when an old recording's parameters are unpickled; (3) whether the pond's random draws
are kept out of the existing random streams; (4) the order in which hydration is drained,
refilled, clipped and judged lethal; (5) which death code wins when two deaths coincide;
(6) whether the observation vector and the perceptual-noise table agree on where the new
Hydration number sits; (7) whether the "move a respawned food off the pond" repair is truly
uniform and shape-stable under vectorisation; (8) what forces a recompile; and (9) the
Dreamer trainer's import-path fix.

Four Low / Open notes follow. None needs a re-run; two are one-line hardening suggestions,
two are observations for the record.

**Severity legend:** 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a
re-run · 🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

## Scope

- Diff: `git diff df1ca31a..292a1450 -- src/ tests/ scripts/` (8 commits, C0–C7 of
  `docs/develop/active/thirst/THIRST_WATER_PLAN.md`), plus `train.py` (outside the requested
  paths but part of the same change: the shared termination-name constant and the curriculum
  fingerprint).
- `git diff --stat`: 62 files, +2,361 / −97. The one disproportionate entry is the 13 MB
  binary fixture `tests/env/fixtures/water_parity/pre_change_rollouts.npz`, which is the
  point of C1 (pre-change ground truth) and is expected.
- Prior-art pass: `grep -i 'water|thirst|hydrat|pond'` on the Known Bugs registry returns no
  rows — this is new territory. The rows the code cites (~#117 silent `(0, 0)` parking,
  ~#160/~#192 label-without-death, ~#494) were read; the new code does not reintroduce any
  of them (see findings 3 and 4 for the one place ~#117's shape survives in a degenerate
  configuration).

## Findings

| # | Severity | Where | Issue | Suggested fix |
|---|---|---|---|---|
| 1 | 🟢 Low | `src/environment/config_loader.py:2673-2681` | The loader refuses `water.enabled: true` unless `perceptual_noise.modalities` has a `hydration` entry, **even when `perceptual_noise.enabled` is false** — in that case `apply_perceptual_noise` returns before any name lookup (`src/environment/sensor.py:434-435`), so the `KeyError` it guards against cannot fire. Over-strict, and loud, so harmless; but a noise-off water world written from scratch will be turned away for a table it never uses. | Either gate the check on `perceptual_noise.enabled`, or keep it and say in the message that the entry is required regardless of the noise switch. |
| 2 | 🟢 Low | `src/environment/core.py:1895-1896` | `assert params.placement_mode == 'per_entity'` inside `jax_reset`. Redundant with the loader's refusal (`config_loader.py:2939-2944`) and stripped under `python -O`. | Drop it, or turn it into a `ValueError` with the loader's message. Cosmetic. |
| 3 | ❓ Open | `src/environment/config_loader.py:3037-3052` (capacity check) vs `core.py:1524-1531` (scan) | The load-time capacity check counts pond cells and earlier slots but not the fire-to-fire separation ring (`thermal.min_fire_separation`), which also removes cells from `valid`. So the silent `(0, 0)` parking of ~#117 is still reachable for a campfire on a world where the pond and the separation ring together exhaust a small spawn area. This is the pre-existing hazard the scan's own docstring records, made marginally more reachable by the pond; the shipped level 06 is covered by the 2,000-reset runtime test (`test_water_placement.py:202`), not by the check. | Record on the ~#117 row that the pond pre-occupancy is a second contributor (owner: `bug-curator`), or extend the check with the ring's worst case. Not a regression. |
| 4 | 🟢 Low | `src/environment/core.py:1904-1910` | Agent-start repair: `_perm[jnp.argmax(~pond_mask[_perm])]` returns index 0 when **no** cell is pond-free, silently starting the agent on the pond at `(0, 0)`. Reachable only with `edge_margin: 0`, `size == [H, W]`, `random_start_pos: true` **and** zero entity slots (otherwise the capacity check refuses). A degenerate world, but the failure mode is the ~#117 shape. | One line in `_load_water`: refuse a pond that leaves fewer than one free cell (`h * w >= H * W`). |

No finding touches a training result: none changes a number on the shipped level 06/07 or on any water-off world.

## What was verified, and how

### EnvState / EnvParams additions

- `EnvState.hydration` / `water_pos` (`state.py:118-119`) default to `None` and sit last, as the
  dataclass rule requires. `None` is an empty pytree, so a water-off state has exactly the
  pre-water leaves: confirmed by `test_water_parity.py::test_jaxpr_sha_identical` (graph
  fingerprints of `jax_step` / `jax_reset` / `update_body` equal the pre-change commit's on
  eight worlds) and by my probe (vmapped reset+step on level 05 leaves both fields `None`; on
  level 06 they batch to `[8]` and `[8, 4, 2]`). The auto-reset merge in
  `src/environment/wrapper.py:50` (`lax.select` over the tree) and the trajectory-store
  flattener (`trajectory_store.py:774`, `is_leaf=hasattr(x, "shape")`) both pass `None`
  through. `eval_recording.py:72-75` guards with `getattr(..., None)`.
- The 14 new `EnvParams` fields (`state.py:527-546`) are all `pytree_node=False`, with tuples
  for the two vectors and the candidate table, so they live in the treedef and are hashable.
  Probe: treedef hash equal before/after pickling; `jax.jit(jax_step)` cache size stays 1
  after being called with a pickled copy and a `_replace()` copy of the same params.
- `EnvParams.__setstate__` (`state.py:572-586`): flax's `struct.dataclass` defines no
  `__getstate__`/`__setstate__` of its own (checked), pickle state is a plain `dict`, and
  `self.__dict__.update` is the standard way past a frozen dataclass's `__setattr__`. Probe:
  stripped the 14 `water_*` keys from a level-05 params' pickle state and restored → the
  water-off sentinels fill in, the treedef equals the freshly-loaded params, and
  `get_observation_breakdown` renders the pre-water layout. `EnvParams` is broadcast (not
  batched) under vmap, so the hook never meets a batched object.

### PRNG threading

- Water off: no new `split`, no new `fold_in`, no new draw — this is what the jaxpr SHA parity
  proves, not just the code reading.
- Water on: four new streams via `fold_in` on existing sub-keys with constants
  `0xD81–0xD84` (3457–3460), unique in the file (`core.py:1703-1710`; existing constants
  0xAE1, 0x7150A1, 0x7EE7, 0xF00D, 0xB05E, 0xC0A1–3, 0xA77AC7, 999). One subtlety worth
  recording: this environment runs JAX 0.9.0.1 with `jax_threefry_partitionable=True`
  (checked), under which `fold_in(key, d)` **equals** `split(key, n)[d]` whenever `n > d`.
  The parents used here are also split — `split(respawn_key, num_res)`,
  `split(placement_key, 6)`, `split(body_key, 3)`, and `randint(agent_key)`'s internal
  2-way split — so a collision needs a split count above 3457. Not reachable. Safe; a
  one-line comment at the constants would save the next reader the derivation.
- The pond draw folds the **original** `placement_key` before it is re-split
  (`core.py:1889` vs `1987`); the respawn repair folds `respawn_key` while
  `split(respawn_key, num_res)` still feeds the food draws untouched (`core.py:996`, `1028`).
  The main key advances exactly as before (`core.py:984`, `1879`).

### Placement, capacity, and the raise paths

- `resolve_overlaps_global(pre_occupied=pond_mask)` (`core.py:1508-1512`) seeds the occupancy
  mask; the permutation and the scan are unchanged, so zero extra draws. The pond forbids
  `per_type` placement and the two thermal second passes at load (`config_loader.py:2939-2952`),
  correctly, since those rebuild occupancy from entity positions only.
- The capacity check (`config_loader.py:3037-3052`) walks the same `[res, pred, obs, neutral]`
  order as `jax_reset`'s concatenation (`core.py:2018-2031`), using the same post-inset areas
  (`animal_spawn_area[predator_indices]`, etc.). It is a sufficient (worst-case) condition —
  see finding 3 for what it omits.
- All refusals are `ValueError`s that name the key; every water key is read with
  `get_mandatory` under the gate (`config_loader.py:2954-3109`). `water.enabled` itself is
  mandatory (`config_loader.py:1970`).

### Hydration update order and death

- `update_body` (`core.py:598-608`): `W' = clip(W − drain + gain·[drank], 0, max)` — drain
  and refill land before the single clip; `dehydrated = W' <= 0`, `overdrank = W' >= max` are
  judged on the clipped value; both are folded into `done` **inside** `update_body`, and
  `jax_step` reads reasons 6/7 from the same returned predicates (`core.py:1252-1255`), so a
  label without a death is structurally impossible (~#160/~#192 do not recur;
  `test_hydration_dynamics.py:184` checks it on 200 random episodes). `real_death = done` is
  captured before the truncation merge (`core.py:1215`), so the death penalty fires on thirst
  deaths and not on timeouts.
- `info['drank']` is the post-move cell (`core.py:1206-1207`), the `ate_food` convention.
- The 11th return value is appended, `None` when off (empty pytree), so positional readers
  of indices 0–9 and the off-path graph are unchanged; the four external `update_body`
  callers (`validate.py:121`, three tests) index by position ≤ 9.

### Termination code priority and the shared name list

- Chain order in `jax_step`: 1 (timeout) → 2 → 3 → 4 → 5 → **6 → 7**, later wins
  (`core.py:1220-1255`). So dehydration or over-drinking on the same step as an injury or
  thermal death reports 6/7. That is the plan's stated order; 6 and 7 are mutually exclusive
  since `max_hydration > 0` is enforced.
- `TERMINATION_REASONS` (`src/behavior/episode_metrics.py:46-48`) is the one copy; consumers
  in `train.py` (4 sites), `dreamer_srl_main.py:1256`, `balance_metrics.py:76-79`
  (`late_death_log` now counts codes 6/7 as deaths via `np.isin`), and
  `episode_wandb_keys` (23 keys) all derive from it. No circular import
  (`episode_metrics` imports only numpy).

### Observation ↔ perceptual-noise sync

- `get_observation` appends `("Hydration", hydration / max)` after Body Temperature and before
  Interoceptive Nociception (`sensor.py:517-519`); `get_observation_breakdown` inserts the
  same name at the same position (`sensor.py:612-613`); `get_observation` raises if the two
  orders disagree. `apply_perceptual_noise` looks modalities up **by name** from the
  breakdown (`sensor.py:440-452`), so the YAML order is irrelevant; the `hydration` entry is
  appended last in `default.yaml:806` (13th of 13 padded slots, `config_loader.py:3181`) so no
  existing index moves, and level 07 restates it at sigma 0.0. `evaluation_core.py:180` and
  the viz name list (`sensor.py:733`) know the new name. `test_water_observation.py` (9
  tests) pins the width, the column value and the noise slot.

### Respawn repair (uniformity and shape stability)

- `core.py:1019-1039`. The rank-walk `v ← u + #{e_j ≤ v}` started at `v = u` converges to the
  `u`-th non-pond rank in at most `m` strict increases (`m` = pond cells inside the area),
  and the static loop runs `h·w ≥ m` rounds, so it is exact. Pond cells outside the area are
  given rank `n_A`, which `v ≤ n_A − 1` can never reach. I brute-forced every `u` for a full
  overlap (10×10 area, 4 pond cells → bijection onto the 96 free cells), a partial overlap
  (`m = 1`) and no overlap (`m = 0`): each is a bijection from `[0, n_A − m)` onto
  area-minus-pond, i.e. exactly uniform. The shipped test (`test_water_placement.py:338`)
  adds a chi-square on real `jax_step` output.
- Shapes: everything is `[R]`, `[R, P]` or `[R, 2]` with `R = num_res`, `P = h·w`, both
  static; `randint` broadcasts a per-row `maxval`; under vmap `state.water_pos.shape[0]`
  is the per-env `P`. Only respawned slots (`respawn_mask & on_pond`) move, and only pond
  cells are excluded — the same "no general occupancy check" the raw respawn already had.

### Recompilation triggers

- Every new field is static, so any change to a water setting recompiles once — the plan's
  stated price, and nothing sweeps them inside a run. `test_no_recompile.py` (3 passed) is
  unchanged apart from the mandatory gate. No new traced-vs-static branch; every `if
  params.water_enabled` is Python-static.

### `dreamer_srl_main.py` path change

- `sys.path.insert(0, abspath(join(dirname(__file__), "..", "..", "..")))`
  (`dreamer_srl_main.py:44-45`) resolves `src/algorithms/dreamer_srl/` → repo root, so a
  worktree imports its own `src` instead of the shared folder's. Correct, and the right fix
  for the bug it names. `import os as _os` is a harmless re-import.

## Tests run (one process per module, CPU)

| Module | Result |
|---|---|
| `tests/env/test_water_parity.py` | 43 passed (5 min) |
| `tests/env/test_water_placement.py` | 38 passed |
| `tests/env/test_hydration_dynamics.py` | 17 passed |
| `tests/env/test_water_observation.py` | 9 passed |
| `tests/env/test_no_recompile.py` | 3 passed |
| `tests/env/test_saved_config_compat.py` | 22 passed |
| `tests/env/test_ladder_worlds_load.py` | 9 passed |

Plus the ad-hoc probe described above (pickle / old-pickle restore / treedef hash / jit cache /
vmap / repair bijection), all assertions passing.

## Conventions audit

| Convention | Status | Note |
|---|---|---|
| Pytree & immutability | ✅ | `_replace` everywhere; `None` trailing fields; no in-place mutation |
| JIT recompilation | ✅ | 14 static fields, all Python-static branches; no traced-to-static move on existing fields |
| vmap & batch | ✅ | `EnvParams` broadcast; state leaves batch on axis 0; shapes static |
| PRNG key threading | ✅ | no new draws when off; independent fold-in streams when on; main key advances as before |
| Sensor / breakdown sync | ✅ | Hydration at the same position in both; noise lookup by name; entry in `default.yaml` and level 07 |
| Configuration protocol | ✅ | gate mandatory; every water key `get_mandatory` under the gate; loader refusals name the key |
| Known-bug recurrence | ✅ | ~#160/~#192/~#494 do not recur; ~#117 shape survives only in a degenerate config (findings 3, 4) |

## Conclusion

Approved as JAX/Flax-correct; the four Low/Open notes are hardening, not blockers.

Reviewed by: code-reviewer
