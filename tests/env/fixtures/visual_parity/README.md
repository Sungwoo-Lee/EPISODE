# Visual-parity goldens — what they pin, and why they were re-baselined

## In one paragraph

Each `.npz` here holds the **visual slice of the observation vector for 1000 fixed steps from
seed 0** in one world — the numbers the agent's eyes actually produce. `tests/env/test_visual_parity.py`
replays the same episode against today's code and asserts the result is **byte-identical**. A red
test means something changed what the agent sees. Until 2026-09-21 these were *refactor evidence*
(a promise that a past sensor rewrite changed nothing); they are now a **current-world baseline**,
so an intended sensory change is expected to redden them and the response is a deliberate,
recorded re-baseline — never a quiet one.

## The 2026-09-21 re-baseline

| | |
|---|---|
| **Cause** | commit **`47b1b8c3`** — *"default sensory becomes the ladder's Q2 arm (olf 1 / vis 2 / vec 1 / clamp)"* |
| **Date** | 2026-09-21 |
| **Files re-baselined** | 6 (`default`, `basic/00`, `basic/01`, `basic/02`, `basic/03`, `basic/04`) |
| **Files deliberately NOT re-baselined** | `…archive__hypervigilance__08-singlePredRabbit_disengage.npz` (see below) |

**What changed about the agent's senses.** `configs/environment/default.yaml` adopted the sensor
ladder's `Q2_presence_binary` arm, five settings at once:

| Setting | Before | After | In plain words |
|---|---|---|---|
| `olfactory_grid_range` | 0 | 1 | smell is sampled at 5 cells instead of 1, so it carries a **direction** |
| `visual_sensor_range` | 0 | 2 | sight sees a 13-cell diamond instead of only the agent's own cell |
| `visual_vector_size` | 8 | 1 | each cell reports **one** number, not eight — *that* something is there, never *what* |
| `visual_value_mode` | `sum` | `clamp` | two things in one cell read `1.0`, not `2.0` |
| `visual_blur_enabled` | false | true | distant cells are blurred |

Observation width moved **27 → 44** on levels 00/01 (vision pinned to range 1 there), **27 → 52** on
`default` and levels 02/03/04. Those widths are independently declared in the test
(`_EXPECTED_OBS_WIDTH`) and were cross-checked against them before any golden was written.

**Why a re-baseline rather than freezing the world.** Because the freeze was what broke the gate.
Three of these cases previously read pre-resolved copies under `tests/env/fixtures/frozen_parity_worlds/`
and therefore stayed **green** through `47b1b8c3` — asserting parity for a world that existed
nowhere in the tree, while the three live cases went red. Full account in that directory's README
and in `docs/develop/active/issues/KNOWN_BUGS.md` (test-gate-hygiene family).

**What still pins the old sensor.** `configs__…__08-singlePredRabbit_disengage.npz` is the original,
never-regenerated artefact. Its world is self-contained (its own `sensory:` block — range 0, `sum`,
8-wide vector, no `extends:`), so `47b1b8c3` did not reach it; it passed throughout and its declared
width is still 27. The pre-`47b1b8c3` versions of the other six remain recoverable from git:
`git show 47b1b8c3~1:tests/env/fixtures/visual_parity/<slug>.npz`.

## How these were regenerated (and a defect found doing it)

The module's docstring advertises `pytest tests/env/test_visual_parity.py --gen-fixtures`.
**That flag does not work.** `pytest_addoption` is only honoured in `conftest.py` and plugins, never
in a test module, so pytest rejects the argument (`unrecognized arguments: --gen-fixtures`) and
`request.config.getoption("--gen-fixtures", default=False)` silently returns its default — the
generate branch is unreachable. `tests/env/test_extero_noc_parity.py` carries the same dead hook.
Moving the hook into `tests/env/conftest.py` would fix both; that was left to the owner of those
files rather than done here.

The six goldens were therefore written by the gate's **own** generator (`_generate_fixture` →
`_run_episode` → the real sensor), driven config-by-config, on the **CPU** backend
(`JAX_PLATFORMS=cpu` — a GPU-captured fixture differs in the last bits and makes the gate noise).
Nothing here is hand-written.

## Coverage warning — three of these cases barely test anything

Distinct observation rows across the 1000 recorded steps, measured at regeneration:

| Case | distinct rows / 1000 |
|---|---|
| `default` | 995 |
| `02-predator_and_rabbit_10x10` | 828 |
| `01-slow_predator_5x5` | 59 |
| `00-static_predator_5x5` | 4 |
| `03-random_init_10x10` | 4 |
| `04-jump_attack_10x10` | 4 |

A case with 4 distinct rows can register a change of *shape* (which is how `47b1b8c3` was caught)
but is close to blind to a change that keeps the width and moves the values. This is a
**pre-existing** defect, noted before this change in `frozen_parity_worlds/README.md`, and it is not
fixed here — it is recorded so nobody reads a green run as more than it is.

## Retired slugs still present

Five `.npz` files name configs that no longer exist — `…basic__00-forage_5x5`, `01-slowPred_5x5`,
`02-fastPred_8x8`, `03-multiPred_10x10`, `04-keenPred_10x10`. The `basic/` curriculum was replaced
and the gate repointed on 2026-08-26; **nothing reads these**. They are left in place as pre-change
evidence rather than deleted, but they are inert — do not add a case that consumes one.
