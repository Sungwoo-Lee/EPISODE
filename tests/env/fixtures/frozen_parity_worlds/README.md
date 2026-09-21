# Frozen parity worlds — pinned pre-change test inputs

**These are not live configs. Do not update them to match `configs/`. That is the whole point.**

## What this directory is

**One** environment config, frozen at commit `f02e76b9` (**2026-09-15**), used as a **test input**
by two consumers. It is a copy of the world as it was *before* the bush became impassable to
animals.

| Frozen file | Copy of | Read by (verified by grep, 2026-09-21) |
|---|---|---|
| `environment__default.yaml` | `configs/environment/default.yaml` | `tests/env/test_unified_parity.py` (`_FROZEN_LOAD_PATH`), `scripts/verification/capture_sensor_baseline.py` (`PARITY_WORLD`) |

**It held three until 2026-09-21** — see "The 2026-09-21 removal" below for why two of them were
deleted and why this one stayed. The earlier version of this table also listed
`test_directional_sensors.py` as a reader of `environment__default.yaml`; that was **not** true of
the code as committed — that module reads `configs/environment/default.yaml` live (its `DEFAULT`
constant). Corrected here rather than left standing.

## Why they exist

On 2026-09-14 the bush gained `blocks_animals: true` — an animal can no longer walk into a bush,
so the agent gets a real refuge. That is a **deliberate** change to the live world (commit A1 of
[[BUSH_REFUGE_AND_LOCATION_DEPENDENT_RECOVERY]]). It moves animal trajectories, and through them
the PRNG stream and every observation downstream.

Three test suites went red on it. Those three did **not** ask *"is today's world still
correct?"* — they asked *"did a **past refactor** change the observations it promised to
preserve?"*:

- `test_unified_parity.py` pins the pre-unified-animal-refactor environment. **Still true today,
  and the reason this directory still exists.**
- `test_directional_sensors.py::test_observation_is_bit_identical_to_stored_pre_change_fixture`
  pins the pre-`DIRECTIONAL_SENSORS` era. (It reads the **live** default, not this directory —
  see the correction above.)
- `test_visual_parity.py` pinned the same era. **No longer — as of 2026-09-21 it reads live
  configs and tracks the current world**; see "The 2026-09-21 removal" below.

Their fixtures are **evidence about code that shipped months ago**. Re-baselining them against the
post-A1 world would quietly convert that evidence into a snapshot of today, and no future reader
would know it had happened. So we froze **the world** instead of the fixture.

## The distinction that matters

`tests/env/fixtures/thermal_parity/` is deliberately the **opposite** of this directory, and the
inconsistency is intentional:

| Family | Reads | Purpose | On an intended behaviour change |
|---|---|---|---|
| `thermal_parity/` | **live** configs | tracks the **current** world | **regenerate** — going red is its loudness function |
| `parity/` (34) | frozen (`default` only) | pins the unified-animal refactor | **freeze the world**, keep the fixture |
| `visual_parity/` | **live** configs since 2026-09-21 (was: frozen, 3 configs) | tracks the **current** world | **regenerate**, with the cause recorded |
| `directional_sensors/` (1) | live default | pins the visual-sensor refactor | — |

A1 (2026-09-14) regenerated exactly one `thermal_parity/` fixture
(`configs__environment__default.npz`) and froze the worlds for the other three. **Do not
"harmonise" the remaining families into one policy** — they still answer different questions; the
2026-09-21 change moved `visual_parity/` from the second row's policy to the first's *deliberately*
and for a reason recorded below, not because the distinction was dropped.

## Provenance

Taken from git, never from a working copy:

```bash
git show f02e76b9:configs/environment/default.yaml
# the two deleted on 2026-09-21 came from the same commit:
git show f02e76b9:configs/environment/experiment/basic/01-slow_predator_5x5.yaml
git show f02e76b9:configs/environment/experiment/basic/02-predator_and_rabbit_10x10.yaml
```

`environment__default.yaml` carries a 48-line explanatory header prepended by this freeze;
everything after it was byte-for-byte the original (it is standalone, so no `extends:`
resolution was needed) **until 2026-09-15**, when one mandatory key had to be added — see
"Mandatory keys added after the freeze" below. Verify with:

```bash
diff <(git show f02e76b9:configs/environment/default.yaml) \
     <(tail -n +49 tests/env/fixtures/frozen_parity_worlds/environment__default.yaml)
```

which must show **only** the `body.recovery_in_bush_multiplier` block and nothing else.

## Mandatory keys added after the freeze

**Adding a key here is allowed only when the key is mandatory and its value is provably inert.
Everything else about these files stays frozen.** A frozen world that no longer *loads* does
not preserve any evidence — the gates it feeds die on a config error before they compare a
single byte — so keeping them loadable is part of keeping them frozen, not a departure from it.
The safety condition is that the added value must not change the world, and the gate itself is
the proof: these files still reproduce their pinned pre-change fixtures byte-for-byte or the
tests fail.

| Date | Key | Value | Why it is inert |
|---|---|---|---|
| 2026-09-15 | `body.recovery_in_bush_multiplier` | `1.0` | Gates a **trace-time Python `if`** in `core.py::update_body` (the field is `struct.field(pytree_node=False)`), so at `1.0` the branch emits no operation and the graph is character-for-character the pre-feature one. Pinned by `tests/env/test_recovery_in_bush.py::test_multiplier_one_is_graph_identical`. Commit B2 of [[BUSH_REFUGE_AND_LOCATION_DEPENDENT_RECOVERY]]. |

**What is still forbidden**: changing any value that already exists in these files, re-syncing
them to the live tree, or regenerating their fixtures. If a future mandatory key is *not*
provably inert, do not add it here — that is a decision for the plan owner, because it means the
gate can no longer read the world it was captured under.

The other two (deleted 2026-09-21) were **pre-resolved**: the originals carry
`extends: environment/default`, and
`extends:` targets resolve **only** under `configs/` (`config_loader.py::_resolve_extends`). A byte
copy would therefore still have read the **live** base, so freezing the file alone would not have
frozen its world — a later edit to the live `default.yaml` would leak in and redden the gate again.
The chain was resolved at the frozen commit and inlined, in the loader's own merge order, with the
`extends:` key stripped. Equivalence is not asserted in a comment; it is **proven by the gates** —
these worlds reproduce the pinned pre-change fixtures byte-for-byte, or the tests fail.

## What was NOT frozen, and why — `basic/03` and `basic/04` (historical, and one live defect)

**Moot as of 2026-09-21** — nothing in `test_visual_parity.py` is frozen any more. Kept because its
second half records a defect in that gate which is **still open**.

**The freeze was scoped by which configs went red, not by which worlds A1 changed.** Those are not
the same set, and a reader should not conclude the freeze was complete.

A1 edited `configs/environment/experiment/basic/03-random_init_10x10.yaml`, and
`04-jump_attack_10x10.yaml` inherits from it. Both are in `test_visual_parity.py`'s config list,
and both read the **live** tree. They stayed green anyway.

**They stayed green because the check is vacuous for them**, not because A1 left them alone: their
visual slice is **constant** — one distinct row across all 1000 steps — so it cannot register any
behavioural change, including this one. `00-static_predator_5x5.yaml` is vacuous too, for the
different reason that it declares `obstacles: []` and has no bush at all.

Freezing `03` and `04` was therefore rejected as **cosmetic**: it would have added two more pinned
worlds to maintain while the gate they feed still checks nothing. The vacuity is a **pre-existing
defect** in that gate, recorded separately and routed to `bug-curator`; it is not this change's to
fix, and fixing it is what would make freezing them meaningful.

Also not frozen, and also deliberate: **nine further maintained worlds stay permeable** —
`configs/verification/observability_gates_S{1..4}.yaml` (verification instruments, whose world
defines what they verify) and `configs/continual/nmn_double_return_stages/0{1..5}_*.yaml` (a
curriculum tied to a specific study). See the 2026-09-14 entry in
`docs/environment/CONFIG_CRITICAL_SETTINGS.md` for that decision and its consequence for
evaluation.

## The 2026-09-21 removal — two frozen worlds deleted, one kept

**What happened.** Commit `47b1b8c3` (2026-09-21) changed the *default sensory settings*
(`olfactory_grid_range` 0 → 1, `visual_sensor_range` 0 → 2, `visual_vector_size` 8 → 1,
`visual_value_mode` `sum` → `clamp`, blur off → on) — the sensor ladder's `Q2_presence_binary` arm.
`tests/env/test_visual_parity.py` then failed for its three **live** cases and **passed** for its
three **frozen** ones, because the pre-resolved copies still carried the *old* sensory block. Those
three were asserting byte-parity for a world that existed nowhere in the tree.

**Why that is worse than a red gate.** A skipped or missing case is visible; a passing one is not.
Half this gate detected a change to the agent's senses and half did not, purely by where each case
sourced its config — and every future sensory change would have split the same way.

**The decision (the user's, taken deliberately).** `test_visual_parity.py` now reads the **live**
tree for all seven cases and its goldens were re-baselined against `47b1b8c3`. That changes what
the gate pins: it is now a **current-world** gate like `thermal_parity/`, not refactor evidence.
The two frozen worlds it was the sole reader of —
`environment__experiment__basic__01-slow_predator_5x5.yaml` and
`environment__experiment__basic__02-predator_and_rabbit_10x10.yaml` — were **deleted** rather than
left behind: an unread frozen input is exactly the thing that invites this bug a third time.

**What preserves the evidence the freeze existed to protect** (it is not lost, it is relocated, and
each of these is checked by a test that runs today):

1. `tests/env/test_unified_parity.py` still reads `environment__default.yaml` and still pins the
   **unified-animal refactor** across 34 fixtures. Unchanged, and the reason this directory stays.
2. `scripts/verification/capture_sensor_baseline.py` still reads it for the same reason.
3. The **pre-`DIRECTIONAL_SENSORS` visual-sensor** claim specifically survives inside
   `test_visual_parity.py` itself: its `08-singlePredRabbit_disengage` case is a **self-contained
   archived world** with its own `sensory:` block (`visual_sensor_range: 0`, `visual_value_mode:
   sum`, 8-wide vector) and no `extends:`, so `47b1b8c3` did not reach it. It compares against its
   **original, never-regenerated** fixture and passed throughout this change.
4. The retired goldens remain in git. The pre-`47b1b8c3` artefacts are recoverable with
   `git show 47b1b8c3~1:tests/env/fixtures/visual_parity/<slug>.npz`, and the re-baseline records
   its cause in `tests/env/fixtures/visual_parity/README.md`.

**Why pre-resolution existed at all, for anyone tempted to reintroduce it.** It was never about
speed or insulation from config churn. `extends:` resolves against `configs/` by literal path
(`config_loader.py::_resolve_extends`), so a byte copy of `basic/01` would still have read the
**live** `default.yaml` — freezing the file alone would not have frozen the world. Pre-resolution
was the mechanism that made a freeze real. With the freeze gone, so is the need for it; the gate
calls `_resolve_extends` on the live path like every other case.

## If one of these gates goes red in future

Ask **"did my change alter observations that a past refactor promised to preserve?"** — not "how do
I make these files current". If a gate is legitimately retired, delete its entry; do not silently
re-baseline it. Note that `test_visual_parity.py` auto-generates a fixture when one is *missing*,
so a broken path here would self-rebaseline rather than fail — the test-side slug overrides exist
to make that impossible.
