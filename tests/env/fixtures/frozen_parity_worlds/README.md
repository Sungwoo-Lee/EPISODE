# Frozen parity worlds — pinned pre-change test inputs

**These are not live configs. Do not update them to match `configs/`. That is the whole point.**

## What this directory is

Three environment configs, frozen at commit `f02e76b9` (**2026-09-15**), used as **test inputs** by
three byte-parity gates. They are copies of the world as it was *before* the bush became
impassable to animals.

| Frozen file | Copy of | Read by |
|---|---|---|
| `environment__default.yaml` | `configs/environment/default.yaml` | `test_unified_parity.py`, `test_visual_parity.py`, `test_directional_sensors.py` |
| `environment__experiment__basic__01-slow_predator_5x5.yaml` | `configs/environment/experiment/basic/01-slow_predator_5x5.yaml` | `test_visual_parity.py` |
| `environment__experiment__basic__02-predator_and_rabbit_10x10.yaml` | `configs/environment/experiment/basic/02-predator_and_rabbit_10x10.yaml` | `test_visual_parity.py` |

## Why they exist

On 2026-09-14 the bush gained `blocks_animals: true` — an animal can no longer walk into a bush,
so the agent gets a real refuge. That is a **deliberate** change to the live world (commit A1 of
[[BUSH_REFUGE_AND_LOCATION_DEPENDENT_RECOVERY]]). It moves animal trajectories, and through them
the PRNG stream and every observation downstream.

Three test suites went red on it. But those three do **not** ask *"is today's world still
correct?"* — they ask *"did a **past refactor** change the observations it promised to preserve?"*:

- `test_visual_parity.py` pins the pre-`DIRECTIONAL_SENSORS` visual sensor. Its own module
  docstring says the fixtures **"must NOT be regenerated after the refactor."**
- `test_directional_sensors.py::test_observation_is_bit_identical_to_stored_pre_change_fixture`
  pins the same era.
- `test_unified_parity.py` pins the pre-unified-animal-refactor environment.

Their fixtures are **evidence about code that shipped months ago**. Re-baselining them against the
post-A1 world would quietly convert that evidence into a snapshot of today, and no future reader
would know it had happened. So we froze **the world** instead of the fixture.

## The distinction that matters

`tests/env/fixtures/thermal_parity/` is deliberately the **opposite** of this directory, and the
inconsistency is intentional:

| Family | Reads | Purpose | On an intended behaviour change |
|---|---|---|---|
| `thermal_parity/` (72) | **live** configs | tracks the **current** world | **regenerate** — going red is its loudness function |
| `parity/` (34) | frozen (default only) | pins the unified-animal refactor | **freeze the world**, keep the fixture |
| `visual_parity/` (12) | frozen (3 configs) | pins the visual-sensor refactor | **freeze the world**, keep the fixture |
| `directional_sensors/` (1) | frozen (default) | pins the visual-sensor refactor | **freeze the world**, keep the fixture |

A1 regenerated exactly one `thermal_parity/` fixture (`configs__environment__default.npz`) and
froze the worlds for the other three. **Do not "harmonise" these four into one policy** — they
answer different questions.

## Provenance

Taken from git, never from a working copy:

```bash
git show f02e76b9:configs/environment/default.yaml
git show f02e76b9:configs/environment/experiment/basic/01-slow_predator_5x5.yaml
git show f02e76b9:configs/environment/experiment/basic/02-predator_and_rabbit_10x10.yaml
```

`environment__default.yaml` is **identical apart from the prepended header comment, and resolves to an identical `EnvParams`** — the file carries a
48-line explanatory header prepended by this freeze, and everything after it is byte-for-byte
the original (it is standalone, so no `extends:` resolution was needed). Verify with:

```bash
diff <(git show f02e76b9:configs/environment/default.yaml) \
     <(tail -n +49 tests/env/fixtures/frozen_parity_worlds/environment__default.yaml)
```

The other two are **pre-resolved**: the originals carry `extends: environment/default`, and
`extends:` targets resolve **only** under `configs/` (`config_loader.py::_resolve_extends`). A byte
copy would therefore still have read the **live** base, so freezing the file alone would not have
frozen its world — a later edit to the live `default.yaml` would leak in and redden the gate again.
The chain was resolved at the frozen commit and inlined, in the loader's own merge order, with the
`extends:` key stripped. Equivalence is not asserted in a comment; it is **proven by the gates** —
these worlds reproduce the pinned pre-change fixtures byte-for-byte, or the tests fail.

## What is NOT frozen, and why — `basic/03` and `basic/04`

**The freeze was scoped by which configs went red, not by which worlds A1 changed.** Those are not
the same set, and a reader should not conclude the freeze is complete.

A1 edited `configs/environment/experiment/basic/03-random_init_10x10.yaml`, and
`04-jump_attack_10x10.yaml` inherits from it. Both are in `test_visual_parity.py`'s config list,
and both still read the **live** tree. They stayed green anyway.

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

## If one of these gates goes red in future

Ask **"did my change alter observations that a past refactor promised to preserve?"** — not "how do
I make these files current". If a gate is legitimately retired, delete its entry; do not silently
re-baseline it. Note that `test_visual_parity.py` auto-generates a fixture when one is *missing*,
so a broken path here would self-rebaseline rather than fail — the test-side slug overrides exist
to make that impossible.
