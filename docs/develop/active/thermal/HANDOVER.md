---
title: "Temperature System — Handover"
topic: sensors
status: active
created: 2026-09-09
last_updated: 2026-09-09
aliases: [thermal_handover]
---

# Temperature System — Handover

## Purpose

The temperature system is **built and committed**. This note exists so a session
running *inside* the repository can pick up the loose ends, because the session that
did the work could not do some of them.

Read this first, then [[IMPLEMENTATION_PLAN]] for the detail. The design it was built
from is [[temperature_system_plan]] (`index.html` in that folder; read
`page_template.html` instead — `index.html` is 1.9 MB of embedded images).

**Follow-on work planned since**: [[body_temperature_observation]] — adds the missing
interoceptive channel that hands the agent its own body temperature (the thermoceptor
only ever reported the *world's*).

## Why a handover at all

The implementing session ran with its working directory at `/home/vncuser`, **not**
at the repository root. Claude Code loads `.claude/agents/` relative to the working
directory, so **none of the 22 project agents were registered** — not
`senior-developer`, `developer`, `plan-reviewer`, `code-reviewer`, and critically not
`bug-curator`.

The work was done by general-purpose agents instructed to read the relevant profile
file and adopt it, which preserved the role constraints. But `bug-curator` owns
`KNOWN_BUGS.md` and the agents correctly refused to write there on its behalf. **That
is the main thing left undone.**

**If you are running from the repository root, the project agents are available to
you and this is a five-minute job.**

## State

Branch `v4.0`, HEAD `e6513f3c`. Working tree clean. Nothing pushed.

| Stage | Commit | |
|---|---|---|
| 0 | `765c8769` | Byte-parity harness, 72 fixtures |
| 1 | `dd3b5dfa` | Field, campfire, per-entity `temperature` |
| 2 | `c35e9e3a` | Body temperature, termination reason 5 |
| 3 | `ef88519d` | Thermoceptor, +5 observation dims |
| 4 | `c0c0a619` | Drive integration |
| 5 | `25a55d6f` | Metabolic coupling (off by default) |
| 6 | `e6513f3c` | Rendering, load-time structure check, docs |

Also on this branch: `12aefec6` documents the version-branch and fast-forward rules in
`CLAUDE.md`; `develop` and `main` were fast-forwarded to the `v3.0` tip before `v4.0`
was cut.

The byte-parity gate held green at every stage and was never widened.

## Task 1 — file six registry rows (needs `bug-curator`)

None of these is caused by the thermal work. All are currently recorded **only** in
`IMPLEMENTATION_PLAN.md`, and will be lost when that doc is archived.

1. **Silent cell-(0,0) placement fallback.** When an entity's spawn area fills,
   `resolve_overlaps_global` (`src/environment/core.py`) parks it at cell 0 — outside
   its own declared `area` — and raises nothing. Pre-existing. Stage 1 makes it more
   reachable (tighter validity masks) and guards it with
   `test_fires_respect_min_separation`, but does not fix it.
2. **`JAX_PLATFORMS` race.** Each parity module sets `os.environ.setdefault(...)` in
   its header, which loses to whichever module imports JAX first. In a full
   `pytest tests/env/` run the backend comes up **gpu**, and every bit-identity fixture
   in the repo was captured on **cpu** — so all of them fail at once. Measured:
   **146 failed, 359 passed, 905 skipped**. `test_directional_sensors.py`'s guard names
   it directly: `parity fixture must run on CPU, got 'gpu'`. See Task 2.
3. **`scripts/analysis/ladder/lad03_how_it_ends.py`** assumes three termination codes
   and has **no share-sum guard**, so it would silently under-total on a thermal run.
   Its sibling `grid_ladder_figures.py` was fixed in Stage 2; this one sat outside that
   stage's file list. **Most likely of the six to bite a real analysis.**
4. **Recording-format version stamp is written but never validated.**
   `RECORDING_FORMAT_VERSION` is written at `src/utils/eval_recording.py:65` and `:82`
   and read back nowhere. Frame it as the pattern: a stamp that advertises a guarantee
   it does not provide is worse than no stamp.
5. **Archive-migration drift.** 68 full configs fail to load because mandatory keys were
   added without migrating the archive — all 68 lack `sensory.injury_observable`, and 13
   of those also lack `sensory.visual_value_mode`. Thermal is the third instance, not
   the cause.
6. **`tests/algorithms/dreamer_srl/test_eval_rollout_batched.py::test_batched_eval_rollout_episode_measures_computable`**
   expects a `bush_dwell` key that appears nowhere in `src/`. Verified to fail
   identically at the Stage 0 tip.

## Task 2 — decide the `JAX_PLATFORMS` fix (needs the user)

Not a defect in the thermal work, but the thermal work made it far more visible: the
suite had this flaw in one test and now has it in 145.

Options, in the order I would consider them:

- **Marker-scoped pin.** Force CPU only for the parity/bit-identity modules, via a
  `conftest.py` hook keyed on a pytest marker. Keeps GPU for everything else.
- **Suite-wide pin** in `conftest.py` or `pytest.ini`, where it runs before any module
  import. One line, but slows every GPU-capable test.
- **Document the invocation** (`JAX_PLATFORMS=cpu pytest tests/env/`) and leave the code
  alone. Cheapest; relies on everyone remembering.

Note when testing this: `JAX_PLATFORMS=cpu pytest tests/env/` aborted twice on this
machine with `Fatal Python error: Aborted` inside `backend_compile_and_load` — a
compiler-level crash under load, not a test failure. Run one file at a time, or on a
quiet box.

## Task 3 — two calibration values (research calls, not implementation)

1. **`thermal.metabolic_coupling_rate`** ships at `1.0` and is currently unread
   (`metabolic_coupling: false`). At `k_loss = 0.01` with a body at −12 it would cost
   roughly **12% on top of `metabolic_cost: 1.0`**. Nobody has calibrated it.
2. **`max_temperature` is the correct deviation scale only because
   `temperature_setpoint == 0.0`.** With, say, setpoint 37 and max 42 the exchange rate
   should be `max_satiation / (max_temperature − temperature_setpoint)` but the shipped
   form computes `max_satiation / max_temperature` — leaving the thermal drive axis
   about **8× too weak, silently**, while the loader validates only that the setpoint
   sits inside the band. Identical at shipped values. A load-time warning on a non-zero
   setpoint would be the cheap guard.

## Task 4 — the scheduled measurement (`experiment-designer`)

`thermal.food_min_fire_distance` defaults to `0` by user decision, pending evidence.
Measure the share of sampled resets with at least one food item within Manhattan 1 of a
fire. If it is common, episodes where food lands in the comfort ring have no thermal
trade-off at all — a stationary policy is optimal there and those episodes teach the
agent nothing, while still counting as thermal episodes in every aggregate.

## Practical notes for whoever continues

- Python is `/home/vncuser/miniconda3/envs/grid_world_pain/bin/python`, invoked
  directly. Never `conda run`, never system `python3`.
- **Do not run broad `find`** over the repo — it walks a 641 GB NAS mount and caused
  file-descriptor exhaustion twice (three orphaned `bfs` processes held ~16,000 fds).
  Use `glob` in Python, or `grep -r --include=`.
- **Do not use `pkill -f` with a pattern that matches your own shell** — it kills the
  command. Use the bracket trick (`patter[n]`) or the harness's background mode.
- The thermal example config is
  `configs/environment/experiment/thermal/campfire_world.yaml` — the only thermal-on
  config in the tree, and a full config so the fixture harness can load it.
- The numpy oracle that every thermal number was derived from is
  `docs/develop/active/thermal/temperature_system_plan/sim.py`; a parametrised copy is
  vendored at `tests/env/thermal_sandbox_oracle.py` so tests do not import from a docs
  folder.
- Sensor-ladder training runs from 2026-08-27 were still alive on this machine at
  handover and contribute to the load that aborts CPU test sweeps. Check whether they
  are still wanted.
