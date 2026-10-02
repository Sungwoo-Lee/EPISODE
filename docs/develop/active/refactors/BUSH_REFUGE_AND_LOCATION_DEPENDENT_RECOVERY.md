---
title: "The bush as a real refuge, and resting in it as a better rest"
topic: refactors
status: active
created: 2026-09-14
last_updated: 2026-09-15
---

# The bush as a real refuge, and resting in it as a better rest

> **Status**: PLANNED
> **Opened**: 2026-09-14
> **Related**: [[BUSH_BLOCKS_ANIMALS]] (the movement gate this turns on) · [[SAVED_RUN_CONFIG_COMPAT]] (the sixth-mandatory-key problem Part B knowingly walks into — D3) · [[KNOWN_BUGS]], rows "a run's saved config snapshot no longer rebuilds" and "`hiding_drivers.py` bins injury contemporaneously", both filed in `c0717e6f` · [[CONFIG_CRITICAL_SETTINGS]] · [[CONFIG_GUIDE]]

---

## Context

The world this project simulates contains bushes. Today a bush **hides** the agent — a hunting predator loses track of it — but the bush is not a physical barrier: the predator can walk into the same cell and bite. A switch that makes a bush impassable to animals while the agent can still enter (`blocks_animals`) has existed since June and is off almost everywhere. **Part A turns it on**, so a bush becomes a place an animal cannot follow you into.

**Part B adds a separate thing**: a setting that makes resting *inside a bush* heal the agent faster than resting in the open. It ships at `1.0` — "no difference" — so nothing changes until somebody sets it otherwise. The point is to give the bush a second reason to exist: cover you can heal in, so hiding becomes a decision with an upside rather than only an escape.

Part A now also carries a **settings-tree cleanup** the user has decided separately: from here, the project maintains only the base settings file and the `basic/` curriculum ladder — **8 files** — and everything else under `configs/environment/experiment/` is moved into `archive/`. Archived worlds are explicitly **not kept loadable**; when one is needed again it will be regenerated fresh. That is what makes Part A small: with only 8 maintained world files, turning the switch on is a four-file edit rather than a seventy-file sweep.

### ⚠️ What stops working, and why it is the real cost

Archiving is 227 files across 13 directories, and two of those directories are **live tooling, not old training configs**:

- **`behavior_probes/` — 134 files.** This is the evaluation probe battery. The avoidance and dwell sweeps run against it: `scripts/eval/dwell_sweep/run_sweep.py` hard-codes two of its directories as module-level constants (`:60–61`), and three sweep definitions under `configs/eval_sweeps/` name a probe directory inside it. **Archiving it stops the dwell/avoidance sweeps from running until those callers are repointed.**
- **`thermal/` — 2 files.** These are the only live worked examples of the body-temperature system — the two arms of the "given vs. inferred body temperature" comparison that shipped a week ago, referenced by name from the base settings file's own comments.

Neither is a stale artefact. The user's policy covers them, and the reference sweep in A2 is what turns a silent breakage into a listed one — but **repointing the callers is A2's actual work**, not the `git mv`. The full breakage list is in [F5](#f5--what-archiving-breaks-the-reference-sweep-is-a2s-real-work); several references are comments (harmless), and a handful are live code (not).

A second consequence, deliberately accepted: **the project's byte-parity regression gate shrinks from 72 adjudicated configs to 12**, because 60 of its 72 fixtures belong to configs that become archived. A world nobody maintains must not gate CI, so this follows from the policy — but it is a large reduction in the instrument and is logged as such in [F6](#f6--the-parity-gate-shrinks-from-72-configs-to-12-deliberately).

---

## Analysis

Every number below was **measured**, with commands given so they can be re-run.

> ⚠️ **Provenance.** Measured 2026-09-14, `HEAD` at `bbc37a1d`, tree dirty: a parallel session held uncommitted body-temperature work in `configs/environment/default.yaml` — the one shared file Part A touches. See [P1](#preconditions).

### F1 — The switch is wired into movement only. It does **not** touch entity placement, so the known (0,0) spawn-fallback bug stays unreachable.

`obs_blocks_animals` appears in exactly four places in `src/`:

| Location | Role |
|---|---|
| `src/environment/state.py:215` | `EnvParams` field, `[num_obs]` bool |
| `src/environment/config_loader.py:1851` | read from YAML: `o.get('blocks_animals', False)` |
| `src/environment/config_loader.py:1915` | zero-length array for the empty-obstacles case |
| `src/environment/core.py:560` | `obs_block_for_animals = params.obs_blocking \| params.obs_blocks_animals`, passed to `_hunt_step` (`:581`) and `_wander_step` (`:610`) |

`resolve_overlaps_global` (`core.py:1014–1108`) builds its validity mask from `in_area & (~occ)` plus, under a static guard, the thermal fire-separation term. `relocate_blocked_entities` (`core.py:1111–1177`) uses `in_area & (~occ) & (~blocked_cells)`. **Neither reads `obs_blocks_animals`, and neither reads `obs_blocking` either.** No term is added to any placement validity mask, so the open bug "an entity whose spawn area is full is silently parked at cell (0,0)" does not become more reachable. Its stated trigger does not fire. **Risk closed.**

Corollaries for older documents:

- `BUSH_BLOCKS_ANIMALS.md`'s Phase-1 caveat "animals can still *spawn* on a blocking bush" describes the code correctly but is practically moot: per wiki entry `20260624_0517_bush_spawn_exclusion_free_via_overlap_resolution`, `resolve_overlaps_global` gives every entity a unique cell (0/2000 vmapped resets). Mark stale; do not act on it.
- `move_agent` takes `obs_blocking`, not the merged array. The agent's own movement is untouched — that is the asymmetry the feature is for.

### F2 — `blocks_animals` keeps its fallback default, recorded as a deliberate exception

`config_loader.py:1851` is `o.get('blocks_animals', False)`. Deep-merge replaces list values wholesale (`CONFIG_GUIDE.md` §1, the "list-replace footgun"), so a config that redeclares its own `obstacles:` list and does not spell the key out silently keeps the old behaviour.

**Settled: the fallback stays.** Making it mandatory would raise on every config that redeclares an obstacle list — including all 227 being archived, which the policy explicitly does not keep loadable. Because retaining a fallback on a now-load-bearing setting departs from the project's no-fallback-defaults rule, **it is recorded as a dated exception in the critical-settings registry** (A1's doc list) rather than left as an unexplained inconsistency.

After A2 the exposure is small and bounded: the only maintained worlds are the 8 kept files, and A1 makes every one of them explicit.

### F3 — The maintained set is 8 files; exactly three need the key

All 7 `basic/*` files carry `extends:`, so they inherit from the base file. Which of them redeclare an obstacle list, and which of those contain a concealing bush:

| File | redeclares `obstacles:` | has `hides_agent: true` | declares `blocks_animals` | A1 action |
|---|:--:|:--:|:--:|---|
| `00-static_predator_5x5.yaml` | yes — as **`obstacles: []`** (`:42`) | **no** | no | **none** — no obstacles at all |
| `01-slow_predator_5x5.yaml` | yes | yes | no | **add the key** |
| `02-predator_and_rabbit_10x10.yaml` | yes | yes | no | **add the key** |
| `03-random_init_10x10.yaml` | yes | yes | no | **add the key** |
| `03-random_init_10x10_ckpt1k.yaml` | no | — | no | **none** — extends `03` |
| `04-jump_attack_10x10.yaml` | no | — | no | **none** — extends `03` |
| `05-sensory_noise_10x10.yaml` | no | — | no | **none** — extends `04` |

So A1 is four settings files: the base plus `01`, `02`, `03`. `00` is the one that could be got
wrong by pattern-matching on "redeclares obstacles".

> **Corrected 2026-09-14 during A1.** An earlier draft of this row said `00` "has only rocks, and
> a `blocks_animals` key on a rock is noise". That is **wrong**, and the wrong reason is what a
> future reader would rely on. `00-static_predator_5x5.yaml:42` declares **`obstacles: []`** — an
> explicitly empty list, the §1 list-replace idiom for "suppress the base's scene". It has **no
> obstacles at all**, not rocks. Measured at the loader: `n_obs = 0`. The action is unchanged
> (touch nothing), but the reason is "there is nothing there", not "there is a rock there". Its
> pass on the A1.3 invariant is therefore **vacuous** and must not be read as coverage.

### F4 — The archive move: 227 files, 13 directories

```bash
find configs/environment/experiment -name '*.yaml' -not -path '*/archive/*' -not -path '*/basic/*' | wc -l   # 227
```

| Directory | Files | | Directory | Files |
|---|---:|---|---|---:|
| `behavior_probes/` | 134 | | `basic04_variants/` | 8 |
| `sensory_directional/` | 15 | | `basic_curriculum/` | 5 |
| `sensory_ladder/` | 14 | | `basic_bushrefuge/` | 4 |
| `olfactory_ambiguity/` | 10 | | `curriculum_basic_01_02_03/` | 3 |
| `olfactory_ambiguity_lindecay/` | 10 | | `hypervig_scarcity/` | 2 |
| `basic_bushrefuge_restpremium/` | 10 | | `thermal/` | 2 |
| `basic_bushrefuge_restpremium_nohide/` | 10 | | | |

`configs/environment/experiment/archive/` already holds 99 files; after A2 it holds **326**. Directory structure is preserved under `archive/`, so `sensory_ladder/A_baseline.yaml` becomes `archive/sensory_ladder/A_baseline.yaml`.

Note the two generator scripts travel with their output: `sensory_ladder/generate_ladder.py` and `sensory_directional/generate_weakened_vision_arms.py` are not `.yaml` and so are **not** in the 227 — decide explicitly whether they move with their directories (recommended: yes, they are meaningless apart from it) and state it, because a generator left behind pointing at an archived output directory is worse than either option.

### F5 — What archiving breaks: the reference sweep is A2's real work

Measured across `scripts/`, `tests/`, `src/`, `configs/` and `train_command-agent.sh`. Split by whether the reference is live code or prose, because the two need different treatment:

**Live — breaks on use, must be repointed in A2:**

| Reference | What it is |
|---|---|
| `scripts/eval/dwell_sweep/run_sweep.py:60–61` | `CLEAN_PROBE_DIR` / `NOISE_PROBE_DIR` module-level constants → `behavior_probes/core/avoidance`, `behavior_probes/explore/avoidance_stat_noise`. **The dwell/avoidance sweep entry point.** |
| `configs/eval_sweeps/bushrefuge_rppo.yaml`, `restprem_rppo.yaml`, `restprem_nohide_rppo.yaml` | each has a `probe:` key → `behavior_probes/core/avoidance_bushrefuge` |
| `scripts/lab/launch_ladder_arm.sh` | builds `experiment/sensory_ladder/${ARM}.yaml` |
| `scripts/lab/launch_sensory_arm.sh` | builds `experiment/sensory_directional/${ARM}.yaml` |
| `tests/env/test_inactive_animal_offgrid.py` | loads `basic_curriculum/04-far_sight_predator_10x10.yaml` — **this test goes red on the `git mv`**, which is exactly the `b093023` precedent |

**Prose — update for accuracy, nothing breaks:** `train_command-agent.sh` (≈40 comment lines of launch history), `configs/environment/default.yaml` (two comments naming `experiment/thermal/`), `configs/trajectory_collection/nmn_olf_{gae,mc}_grid.yaml`, `configs/models/recurrent_ppo/nmn_input_site_grid/generate_site_grid_arms.py`, docstring examples in `scripts/eval/dreamer_srl_probe_eval.py` and `scripts/eval/parity_check_eval_rollout.py`.

**A third category, and it is the one that bites quietly.** Every `configs/continual/*.yaml` curriculum names its stage directory in a **comment only** — e.g. `basic_01_02_03_dreamer.yaml:3` points at `curriculum_basic_01_02_03/`. The functional coupling is the `--configs-dir` argument on the launch command, not the config. So archiving a stage directory **breaks nothing at rest and everything at launch**, with no test to catch it. The sweep must therefore include `--configs-dir` occurrences, and the affected curricula must be named in the Implementation Report even though nothing goes red.

**`SCRIPTS_DEPENDENCY_MAP.md`:** A2 edits files under `scripts/` but does not add, move, rename or delete any, so the Maintenance Contract does not fire on its face. Still `grep -n 'behavior_probes\|sensory_ladder\|sensory_directional' docs/environment/SCRIPTS_DEPENDENCY_MAP.md` — if the map documents these launchers' config paths, it is stale the moment A2 lands and must be updated in the same commit.

### F6 — The parity gate shrinks from 72 configs to 12, deliberately

> ## ⚠️ F6 CORRECTED 2026-09-14 (during A1) — this finding counted ONE gate; there are FOUR
>
> **Everything below this box is about `tests/env/test_thermal_parity.py` only, and the
> "72 → 12" figure is correct for that family alone.** It was written as though that family
> *were* "the project's byte-parity regression gate". It is not. `tests/env/fixtures/` holds
> **four** independent byte-parity fixture families, adjudicating **119** fixtures between them:
>
> | Family | Test | Fixtures | What it pins | Reads |
> |---|---|---:|---|---|
> | `thermal_parity/` | `test_thermal_parity.py` | 72 | the **current** world | **live** configs |
> | `parity/` | `test_unified_parity.py` | 34 | the **unified-animal refactor** | live, except `default.yaml` (frozen since A1) |
> | `visual_parity/` | `test_visual_parity.py` | 12 | the **DIRECTIONAL_SENSORS visual rewrite** | live, except 3 configs (frozen since A1) |
> | `directional_sensors/` | `test_directional_sensors.py` | 1 | the same visual rewrite | frozen since A1 |
> | **total** | | **119** | | |
>
> **Two purposes, not one — and A1 proved they need opposite treatment.** `thermal_parity/`
> tracks the world as it is now; going red on a deliberate behaviour change is its *loudness
> function*, which is why A1 regenerated its one affected fixture. The other three pin the claim
> that a **past refactor** preserved observations; their fixtures are evidence about code that
> shipped months ago, and `test_visual_parity.py`'s own docstring says they **"must NOT be
> regenerated after the refactor"**. A1 therefore froze the *world* for those three
> (`tests/env/fixtures/frozen_parity_worlds/`) and left their fixtures untouched. **Do not
> harmonise the four into one policy.**
>
> **`CONFIG_GUIDE.md`'s Maintenance Contract §4 names a different pair than this plan does.** It
> calls `tests/env/test_unified_parity.py` + `tests/env/test_visual_parity.py` "the parity gate";
> this plan cited `test_thermal_parity.py` and mentioned the other two only as *B1* checks
> expected to show "unchanged counts". **The plan cited the wrong gate.** That is why A1's
> pre-registered prediction — "exactly 1 fixture modified, 71 untouched" — was simultaneously
> *exactly right* (for `thermal_parity/`) and *blind* (to 5 further red fixtures across three
> other families). Predicting against one instrument cannot falsify a claim about four.
>
> **Post-A2 sizes, measured per family, since A2's archiving decision rests on this number:**
>
> | Family | Now | After A2 | Why |
> |---|---:|---:|---|
> | `thermal_parity/` | 72 | **12** | 60 deleted — 36 `archive` slugs + 14 `sensory_ladder__*` + 10 `sensory_directional__*`. As planned below. |
> | `parity/` | 34 | **34** | **Unchanged.** Its 34 = 5 `continual` + 6 `verification` + 1 `default` + 22 already under `experiment/archive/`. **None** belongs to the 13 directories A2 moves, so no fixture is orphaned. Note `_collect_configs()` here is **not** in A2's list of three collectors to narrow; if the archive-exclusion policy were applied to it as well it would drop **34 → 12**. That is a decision A2 must make explicitly rather than inherit. |
> | `visual_parity/` | 12 | **12** | **Unchanged.** Its one `archive`-slug fixture (`…archive__hypervigilance__08-singlePredRabbit_disengage`) is already archived, and the rest are `default` + `basic/*`, which A2 keeps. Separately: **5 of the 12 are orphans** (`00-forage_5x5`, `01-slowPred_5x5`, `02-fastPred_8x8`, `03-multiPred_10x10`, `04-keenPred_10x10`) — fixtures for configs that no longer exist under any name, left behind by the 2026-08-26 repoint. They are dead weight, not coverage; the suite runs **8** tests. |
> | `directional_sensors/` | 1 | **1** | Unchanged; reads a frozen world. |
> | **total** | **119** | **59** | |
>
> So the real headline is **119 → 59**, not 72 → 12, and the reduction is entirely inside
> `thermal_parity/`. The "a world nobody maintains must not gate CI" argument below still holds
> — it simply applies to one family, not to the instrument as a whole.


`tests/env/test_thermal_parity.py` replays a 100-step seed-0 episode for every config with a committed `.npz`, asserting exact equality on reward, both drives, `state.key`, termination reason, entity positions and every observation slice but Olfaction. It loads each config from a **raw `Config`** (no `extends:` resolution), so the fixtured set is exactly the standalone configs. Today, 72:

| Fixtured group | Count | After A2 |
|---|---:|---|
| under `experiment/archive/` (already) | 36 | **removed** |
| `sensory_ladder/` | 14 | **removed** (archived) |
| `sensory_directional/` | 10 | **removed** (archived) |
| `verification/` (4 gates + 2 olfaction-parity) | 6 | kept |
| `continual/nmn_double_return_stages/` | 5 | kept |
| `configs/environment/default.yaml` | 1 | kept |
| **total** | **72** | **12** |

**60 fixtures are deleted in A2** and the gate drops to 12 adjudicated configs. This follows directly from the policy — a world nobody maintains, and which is explicitly not kept loadable, must not gate CI; leaving the fixtures would mean the gate reddens on configs the project has decided not to keep working. It is nonetheless a **large, deliberate reduction of the project's main regression instrument** and must be logged in the critical-settings change log with the number, not merely done.

Note the pleasing invariant, which doubles as a cross-check: **the 12 surviving fixtures are exactly the 12 configs in Part B's rollout** (F7). Both sets are "standalone environment configs the project still maintains".

Two consequences for A2:
- `collect_configs()` in `scripts/fixtures/generate_thermal_parity_fixtures.py` and `_collect_configs()` in `tests/env/test_thermal_parity.py` must both exclude `*/archive/*`. They are documented as being verbatim copies of each other; keep them so.
- `tests/env/test_backward_compat_configs.py` globs the same tree and would keep collecting all 326 archived configs, skipping them one by one. It currently **skips** rather than fails, so this is not urgent — but under the new policy it is simply wrong to assert anything about them. Exclude `*/archive/*` there too, in the same commit, and record the collected-count change.

### F7 — Part B's rollout collapses to 12 configs

A new unconditionally-mandatory `body.` key breaks any config loaded from a raw `Config` that lacks it — and the parity gate `pytest.fail`s on a load error rather than skipping (`test_thermal_parity.py:234`, versus `test_backward_compat_configs.py:88` which skips). So the rollout set is "every standalone config the project still maintains", which after A2 is:

```bash
for f in $(find configs/continual configs/verification -name '*.yaml'); do
  grep -q '^extends:' "$f" || { grep -q '^body:' "$f" && echo "$f"; }
done | sort     # 11 files
```

**11 files** — `continual/nmn_double_return_stages/*` (5) and `configs/verification/*` (6) — **plus `configs/environment/default.yaml` = 12.** All 12 load cleanly today.

**Every `basic/*` file carries `extends:`**, so all 7 inherit the key from the base file and need no edit. The 227 archived configs are out of scope by policy. The 55 archived configs that already fail to load stay broken, as they already are.

Also in scope: the **20 test modules with inline YAML `body:` blocks** (`grep -rl recovery_base_rate tests/`), which build params from inline dicts and so cannot inherit anything.

### F8 — This is the sixth mandatory key to land without an archive migration

[[SAVED_RUN_CONFIG_COMPAT]] (PLANNED, 2026-09-09) measured it: **of 493 frozen run-configs on disk, only 33 rebuild at current code.** Five keys got there first — `sensory.visual_blur_enabled`, `sensory.olfactory_grid_range`, `sensory.visual_value_mode`, `sensory.visual_occlusion_enabled`, `thermal.enabled`. Its verdict applies verbatim:

> "A fix that only teaches the tools about the temperature switch would restore 120 runs and leave 340 broken, and the sixth key would be discovered exactly the same way."

`body.recovery_in_bush_multiplier` is that sixth key. **The recovery note this plan adds to `CONFIG_GUIDE.md` does not fix the saved-run population** — a run's `results/<run>/models/config.yaml` is the historical record of what it trained with and must not be edited, so the note is a lookup for a human who has already hit the wall. Put to the user with this measurement in hand; **the decision is to ship now** (D3).

### F9 — The ordering problem, and why hoisting the predicate is numerically free

`update_body` is called at `core.py:829`; `info['agent_in_bush']` is not written until `core.py:961`. The gate cannot read it as written.

It does not need to. The predicate is a pure function of the post-move cell and the obstacle arrays — `obs_pos == new_agent_pos` AND `obs_hides_agent & obs_active` — and obstacle positions are constant within an episode (`TRAJECTORY_STORE_SCHEMA`, `obs_row`). Recomputing it earlier in the same step gives the identical value. `update_body` already receives `new_agent_pos` for a closely related reason, documented at `core.py:101–109`: the thermal field must be read at the post-move cell or body temperature becomes the one body variable that lags by a step. `state.obs_pos`, `state.obs_active` and `params.obs_hides_agent` are all already in scope; `jax_step`'s call order does not change.

The predicate exists twice today:

| Site | Form |
|---|---|
| `core.py:351–355`, in `_hunt_step` as `agent_hidden` | `_eff_hides = obs_hides_agent if obs_active is None else (obs_hides_agent & obs_active)`; `jnp.any(all(obs_pos == agent_pos) & _eff_hides)` |
| `core.py:961–964`, in `jax_step` as `agent_in_bush` | `jnp.any(all(state.obs_pos == new_agent_pos) & (params.obs_hides_agent & state.obs_active))`, behind a static `if state.obs_pos.shape[0] > 0` |

A third copy is ruled out. B1 extracts one helper and rewires these two; B2 makes `update_body` its third consumer.

### F10 — Part B confounds a published analysis, and the confound is a separate recorded bug

`scripts/analysis/hiding_drivers.py:214` bins injury contemporaneously (`ib = np.digitize(inj[m], INJ_EDGES)` paired with `bu[m]` at the same row `t`) — recorded in `KNOWN_BUGS` by `c0717e6f`. A recovery change shifts the per-step injury trajectory and moves bin membership in every cross-tab it produced, so a real behavioural effect and a binning artefact become indistinguishable across the line.

**B2 requires a before/after snapshot**: run `hiding_drivers.py` on one already-trained run at the pre-B2 tree, save the output under `tmp/`, record the path. One invocation; it is the only thing that lets a later analyst separate the two.

The two published pages downstream — `docs/experiments/active/trajectory_factors/a01_hiding_drivers.html` and `hiding_factor_atlas.html` — are **not** invalidated: they report agents trained before this, and at multiplier `1.0` nothing about those agents changes. They mislead only if someone re-runs the script post-B2 and compares across the line. Flag that to `experiment-analyzer`.

### F11 — Recorded follow-ups that A2 partly resolves

- **Generator drift.** Both `sensory_ladder/generate_ladder.py` and `sensory_directional/generate_weakened_vision_arms.py` flatten `basic/04`; re-running either today, with no change at all, rewrites every arm — **43** changed lines per ladder arm, **41** per directional arm — because the thermal Stage-1 sweep hand-appended a six-line `thermal:` stub to files whose headers say *GENERATED — do not hand-edit*. Both families are archived in A2, so the drift is frozen rather than fixed. **Whoever regenerates one of these worlds later must regenerate from the generator, not resurrect the stale YAML** — that is the note to leave with them.
- **Bush-refuge equivalence.** After A1, `basic/01,02,03` become equivalent to their `basic_bushrefuge/` counterparts, so that family has no remaining reason to exist. Its `extends:`-chain hazard — 10 `restpremium` configs extend `basic_bushrefuge/04`, and each `_nohide` file extends its restpremium sibling — **resolves itself in A2**, because all 24 files move together and the chain stays closed. Verification A2.4 is what confirms that rather than assuming it.

---

## Preconditions

**P1 — `configs/environment/default.yaml` must be clean of other sessions' work.** A parallel session held uncommitted `thermal.body_temp_observable` edits there. It is the only shared file Part A touches, which makes this narrow but fully blocking: committing over someone else's unfinished work in it is the `sensory.decay_power` incident one level up. Wait for the owner to commit or revert.

**P2 — D2 is answered.** It changes B2's source.

---

## Implementation Plan

### Design

Four commits, each separately revertible and separately attributable.

| # | Name | What moves | Behaviour change |
|---|---|---|---|
| **A1** | Bush blocks animals | `default.yaml` + `basic/01,02,03` + 3 docs + 1 fixture | **yes**, deliberate |
| **A2** | Archive everything but the maintained 8 | 227 `git mv` + repointed callers + gate scope + 60 fixtures deleted | none to the kept worlds |
| **B1** | One in-bush predicate, three callers | `core.py` only | **none** — that is the check |
| **B2** | `recovery_in_bush_multiplier` | new key + 12 configs + 20 test modules + 4 docs + a new test | **none at 1.0**, by source construction |

**Execution model.** Each commit is a separate `developer` invocation: implement → run that commit's verification → hand the dirty diff to review → commit → next. Do not batch; B1 and B2 both touch `update_body` and the split is the point.

**Order matters between A1 and A2.** A1 first, because A1's only fixture consequence is the base config, and doing it before the gate shrinks means the change is adjudicated against the fuller instrument. A2 then removes 60 fixtures in one deliberate, logged step.

**Two test invocations, never one.** A whole-directory run without the CPU pin previously reported 146 failed / 359 passed / 905 skipped, all backend artefact:

```bash
JAX_PLATFORMS=cpu /home/vncuser/miniconda3/envs/grid_world_pain/bin/python -m pytest tests/env/ -q
/home/vncuser/miniconda3/envs/grid_world_pain/bin/python -m pytest tests/ --ignore=tests/env -q
```

**The loader hazard.** Any "does this still resolve the same?" claim goes through `load_env_config` — what `train.py` calls at `:581`/`:202`/`:527` — or a saved run config; never a raw `Config`, which does not resolve `extends:`. The parity gate deliberately uses a raw `Config`; that is not a violation, it is why the fixtured set is the standalone set (F6).

---

### File Changes

#### Commit A1 — the bush blocks animals

**`configs/environment/default.yaml:137`** — flip the value:

```yaml
# BEFORE:
      blocks_animals: false  # animals cannot enter when true; agent still can
# AFTER:
      blocks_animals: true   # animals cannot enter; the agent still can. The bush is a
                             # physical refuge, not only concealment.
                             # Read with a fallback of False (config_loader.py:1851), so a
                             # config that redeclares its own `obstacles:` list does NOT
                             # inherit this line. Every maintained world declares it
                             # explicitly; see the deliberate-exception entry in
                             # CONFIG_CRITICAL_SETTINGS.md.
```

**`basic/01-slow_predator_5x5.yaml`, `02-predator_and_rabbit_10x10.yaml`, `03-random_init_10x10.yaml`** — each redeclares `obstacles:` with a `hides_agent: true` bush and never declares the key. Add it to the **bush entry only** (in `03`, the entry at `:89–100`; the `rock` entry at `:101` gets nothing):

```yaml
      hides_agent: true
      blocks_animals: true   # matches environment/default; this file redeclares obstacles,
                             # so the key must be explicit (list-replace, CONFIG_GUIDE §1)
```

**Do not touch** `basic/00` (redeclares obstacles, but rocks only — no bush to block), `03-random_init_10x10_ckpt1k`, `04`, `05` (none redeclares `obstacles:`; all inherit). See F3.

**Fixtures.** `scripts/fixtures/generate_thermal_parity_fixtures.py` has **no subset mode**: `main()` rewrites every fixture whose config loads. That is safe because fixture bytes are deterministic for an unchanged config (Assumption 5) — unchanged ones rewrite identically and stay out of `git status`, which is what makes A1's artefact-of-record check work.

> **Corrected 2026-09-14 during A1 — the delete-before-staging step does not exist.** This plan
> previously said `collect_configs()` sees the two live `experiment/thermal/` configs, creates 2
> new untracked `.npz`, and that they must be `rm`'d before staging. **Measured: the generator
> never creates them.** Both `experiment/thermal/campfire_world.yaml` and
> `campfire_world_body_temp_hidden.yaml` fail at **run** time, not load time — inside
> `_capture_state` (`generate_thermal_parity_fixtures.py:126`, from `:154`) — so the generator
> reports `SKIP (run error)` and writes nothing:
>
> ```
> configs walked:   358
> fixtures written: 72
> skipped:          284 load errors, 2 run errors
> ```
>
> `git ls-files --others --exclude-standard tests/env/fixtures/` after the run contained no
> `.npz`. **There is nothing to delete; the step is removed.** Note the separate, pre-existing
> defect this exposes: the only two live worked examples of the temperature system cannot be
> fixtured at all. A2 archives them anyway, but that is not a fix.

**Docs, all in this commit:**

- **`docs/environment/CONFIG_CRITICAL_SETTINGS.md`** — two entries:
  1. A registry row for `obstacles[bush].blocks_animals`, canonical **true**, noting it is merged into the animal movement mask only (`core.py:560`) and is **not** in any placement validity mask.
  2. A **dated change-log entry** for `false → true`: the four settings files changed, the measured-vs-predicted fixture set, and the blast radius — every config inheriting the base file plus the three stages; and that every agent trained before this line learned the permeable world, so policies are not comparable across it. The same entry records the **deliberate exception to the no-fallback-defaults rule** (F2): `blocks_animals` keeps `o.get(..., False)` on purpose, because making it mandatory would raise on the 227 configs being archived, which policy does not keep loadable.
- **`docs/environment/02_config_schema.md:1152`** — Obstacle Entity Fields: keep the loader default as `False`, add that the base settings file ships `true`, that the two differ on purpose, and point at the registry exception.
- **`docs/environment/CONFIG_GUIDE.md`** — §1 "list-replace footgun" gains `blocks_animals` as the worked example of a key whose fallback lets a redeclared list silently reverse a project-wide decision. (Paired-contract requirement with `02_config_schema.md`: same commit.)
- **`docs/develop/active/refactors/BUSH_BLOCKS_ANIMALS.md`** — mark the spawn-exclusion caveat stale, citing F1.

#### Commit A2 — archive everything but the maintained 8

**Move 227 files** with `git mv`, preserving structure (`git mv` and not `mv` — `git log --follow` is the record of why these worlds existed):

```
configs/environment/experiment/<dir>/…  →  configs/environment/experiment/archive/<dir>/…
```

for the 13 directories in F4. Keep `default.yaml` and `basic/` (8 files) in place. Decide and state whether the two generator `.py` files travel with their directories — recommended yes; a generator whose output directory has moved is worse than either alternative.

**Repoint the live callers** (F5). These are the commit's real content:

| File | Change |
|---|---|
| `scripts/eval/dwell_sweep/run_sweep.py:60–61` | `CLEAN_PROBE_DIR`, `NOISE_PROBE_DIR` → `…/experiment/archive/behavior_probes/…` |
| `configs/eval_sweeps/bushrefuge_rppo.yaml`, `restprem_rppo.yaml`, `restprem_nohide_rppo.yaml` | `probe:` → archived path |
| `scripts/lab/launch_ladder_arm.sh` | arm path → archived |
| `scripts/lab/launch_sensory_arm.sh` | arm path → archived |
| `tests/env/test_inactive_animal_offgrid.py` | `basic_curriculum/04-…` → archived path — **this test goes red on the move if missed** |

**Update the prose references** for accuracy: `train_command-agent.sh` (≈40 comment lines), `configs/environment/default.yaml` (two `experiment/thermal/` comments), `configs/trajectory_collection/nmn_olf_{gae,mc}_grid.yaml`, `configs/models/recurrent_ppo/nmn_input_site_grid/generate_site_grid_arms.py`, and docstrings in `scripts/eval/dreamer_srl_probe_eval.py` and `scripts/eval/parity_check_eval_rollout.py`.

**Narrow the gate's scope** — exclude `*/archive/*` from all three collectors, in this commit:

- `scripts/fixtures/generate_thermal_parity_fixtures.py::collect_configs` (`:82–91`)
- `tests/env/test_thermal_parity.py::_collect_configs` (`:92–96`) — documented as verbatim copies of each other; keep them so
- `tests/env/test_backward_compat_configs.py::_collect_all_configs` (`:24–33`)

**Delete 60 fixtures** under `tests/env/fixtures/thermal_parity/` — the 36 with `archive` slugs plus the 14 `sensory_ladder__*` and 10 `sensory_directional__*`. Gate goes 72 → 12.

**`docs/environment/CONFIG_CRITICAL_SETTINGS.md`** — a dated change-log entry recording the policy and its cost in numbers: 227 files archived across 13 directories; the maintained set is now 8; **the byte-parity gate drops from 72 adjudicated configs to 12**; archived worlds are explicitly not kept loadable and will be regenerated when needed. The gate reduction is the part that must not be left implicit.

**`docs/environment/SCRIPTS_DEPENDENCY_MAP.md`** — the Maintenance Contract does not fire on its face (no file under `scripts/` is added, moved, renamed or deleted), but `grep -n 'behavior_probes\|sensory_ladder\|sensory_directional' docs/environment/SCRIPTS_DEPENDENCY_MAP.md`; if the map documents those launchers' config paths, update it here.

#### Commit B1 — one in-bush predicate, three callers (no behaviour change)

**`src/environment/core.py`** — new module-level helper above `update_body` (its earliest caller from B2):

```python
def agent_in_hiding_obstacle(agent_pos, obs_pos, obs_hides_agent, obs_active=None):
    """True iff `agent_pos` is on an ACTIVE obstacle marked `hides_agent`.

    ONE definition, three callers: `_hunt_step` (a hidden agent is lost by a
    hunter), `jax_step` (writes it onto `info` for the behaviour measures), and
    `update_body` (the in-bush recovery gate). It is a pure function of the cell
    and the obstacle arrays, and obstacle positions are constant within an
    episode (TRAJECTORY_STORE_SCHEMA, `obs_row`), so evaluating it at different
    points of the same step gives the same answer — which is what lets the body
    update read it before `jax_step` writes it onto `info`.

    `obs_active=None` means "every obstacle counts", preserving `_hunt_step`'s
    existing call shape. The empty-obstacle guard is static Python and matches
    `jax_step`'s; `jnp.any` over an empty array is already False, so folding the
    guard in here changes nothing for `_hunt_step`.
    """
    if obs_pos.shape[0] == 0:
        return jnp.array(False)
    eff_hides = obs_hides_agent if obs_active is None else (obs_hides_agent & obs_active)
    return jnp.any(jnp.logical_and(jnp.all(obs_pos == agent_pos, axis=-1), eff_hides))
```

Replace the two existing copies:

- `core.py:351–355` — the `_eff_hides` / `agent_hidden` block becomes
  `agent_hidden = agent_in_hiding_obstacle(agent_pos, obs_pos, obs_hides_agent, obs_active)`.
- `core.py:961–964` — the `agent_in_bush` block (including its trailing `if state.obs_pos.shape[0] > 0 else jnp.array(False)`) becomes
  `agent_in_bush = agent_in_hiding_obstacle(new_agent_pos, state.obs_pos, params.obs_hides_agent, state.obs_active)`.
  Keep the surrounding comment; update the stale "line ~150" cross-reference to name the helper.

Nothing else. No config, no doc, no fixture.

#### Commit B2 — `body.recovery_in_bush_multiplier`

**New config key.** Exact YAML path and shipped value:

| Path | Value | Where |
|---|---|---|
| `body.recovery_in_bush_multiplier` | `1.0` | `configs/environment/default.yaml`, immediately after `recovery_accel_rate` (line 176) |

```yaml
  # Recovery: Recovery = base * (1 + accel)^(rest_streak - 1)
  recovery_base_rate: 0.1
  recovery_accel_rate: 0.5
  # Location premium: recovery is multiplied by this while the agent rests ON a
  # concealing bush (an obstacle with `hides_agent: true`). 1.0 = inert, and at
  # exactly 1.0 the gate is not traced at all (static Python guard), so the
  # computation graph is identical to the pre-feature one. The rest streak is
  # NOT location-dependent — see the plan's D2.
  recovery_in_bush_multiplier: 1.0
```

**`src/environment/state.py`** — add to `EnvParams` beside `recovery_accel_rate` (`:250`) as a **static** field:

```python
    recovery_in_bush_multiplier: float = struct.field(pytree_node=False)
```

Static, not a traced leaf, deliberately — it is what allows the trace-time `if` below, and the difference between an inertness *argument* and an inertness *measurement*. The cost is a recompile when the value changes, which is irrelevant: it is fixed for the life of a run. Record the departure in `02_config_schema.md`'s static-vs-dynamic table (`:1460`), where both `recovery_*` siblings sit on the dynamic side.

**`src/environment/config_loader.py:2250`** — beneath the two existing reads:

```python
        recovery_in_bush_multiplier=float(config.get_mandatory('body.recovery_in_bush_multiplier')),
```

The `float()` is load-bearing: YAML parses `1` as an `int`, and a static `struct.field(pytree_node=False)` participates in the trace-cache key, so `1` and `1.0` are different cache entries. Without it, a curriculum whose stages write `1` and `1.0` for the same inert value recompiles between them for nothing. Validate `> 0` at the point of read, in the style of the thermal rate constants.

**`src/environment/core.py`, inside `update_body`, at `:211`** — the inertness standard is the thermal `calculate_drive` precedent: the OFF path is the pre-change expression *verbatim*, so bit-parity is a fact about the source rather than something measured.

```python
# BEFORE (core.py:207-212):
        recovery_mult = jnp.power(1.0 + params.recovery_accel_rate, (jnp.maximum(new_rest_streak, 1) - 1).astype(jnp.float32))
        recovery_amount = params.recovery_base_rate * recovery_mult

        # Recovery only applies if resting and not currently taking net damage
        can_recover = jnp.logical_and(info['rested'], applied_inc <= 0)
        new_injury = jnp.where(can_recover, new_injury - recovery_amount, new_injury)

# AFTER:
        recovery_mult = jnp.power(1.0 + params.recovery_accel_rate, (jnp.maximum(new_rest_streak, 1) - 1).astype(jnp.float32))
        recovery_amount = params.recovery_base_rate * recovery_mult

        # --- Location premium (body.recovery_in_bush_multiplier) ---
        # STATIC Python guard on a trace-time constant. At the shipped 1.0 this
        # branch does not exist in the traced graph and the three lines below are
        # character-for-character the pre-feature code, so bit-parity with every
        # run that predates this key is a property of the source rather than a
        # thing to be measured (same discipline as calculate_drive's thermal-off
        # path). The predicate is the shared helper, NOT a third copy; it is
        # evaluated here rather than read from `info['agent_in_bush']` because
        # update_body runs at jax_step:829 and that key is not written until
        # jax_step:961 — and it is legitimate to evaluate early because obstacle
        # positions are constant within an episode.
        if params.recovery_in_bush_multiplier != 1.0:
            _in_bush = agent_in_hiding_obstacle(
                new_agent_pos, state.obs_pos, params.obs_hides_agent, state.obs_active)
            recovery_amount = recovery_amount * jnp.where(
                _in_bush, params.recovery_in_bush_multiplier, 1.0)

        # Recovery only applies if resting and not currently taking net damage
        can_recover = jnp.logical_and(info['rested'], applied_inc <= 0)
        new_injury = jnp.where(can_recover, new_injury - recovery_amount, new_injury)
```

The gate multiplies `recovery_amount`, so it inherits the **existing** `can_recover` condition — a premium is only collected on a step the agent both rests and takes no net damage. That is why the gate goes here rather than on `can_recover`.

**Config rollout — 12 files** (F7): `configs/environment/default.yaml` plus the 11 standalone configs under `configs/continual/` and `configs/verification/`. One inert line each in their `body:` block. Enumerate, never hard-code:

```bash
for f in $(find configs/continual configs/verification -name '*.yaml'); do
  grep -q '^extends:' "$f" || { grep -q '^body:' "$f" && echo "$f"; }
done | sort
```

All 7 `basic/*` files carry `extends:` and inherit from the base file — **no edit**. The 227 archived worlds are out of scope by policy.

**20 test modules with inline YAML `body:` bases** — `grep -rl recovery_base_rate tests/`, including `tests/fixtures/trajectory_collection/dual_format_config.yaml`. Each needs the key.

**New test — `tests/env/test_recovery_in_bush.py`**, modelled on `tests/env/test_metabolic_coupling.py` (a body-dynamics feature, off by default, with an inertness proof):

| Test | Asserts | Fails if |
|---|---|---|
| `test_missing_key_raises` | `load_env_params` on a config without the key raises `ValueError` naming `body.recovery_in_bush_multiplier` | someone gives it a fallback default |
| `test_multiplier_one_is_graph_identical` | at `1.0` the traced graph never consumes `obs_hides_agent`; at `3.0` it does | the static guard is not static |
| `test_premium_applies_in_bush` | on a hand-built one-bush config at multiplier `3.0`, injury recovered over one rest step **on** the bush is exactly 3× the same step **off** it | the gate reads the wrong cell, or fires on the wrong step |
| `test_premium_requires_rest_and_no_damage` | standing in a bush without resting, and resting in a bush while absorbing damage, both recover **zero** | the gate was put on `can_recover` instead of `recovery_amount` |
| `test_streak_not_location_dependent` | `rest_streak` after resting 3 steps in the open then 1 in a bush is 4, not 1 | someone later adds a location reset without revisiting D2 |

The first three must fail on the pre-B2 tree. **Write the tests first and watch them fail there** — do not `git stash` to fake a pre-change tree; parallel sessions have uncommitted work under `src/environment/`, and a stash/pop across sessions is how tracked work gets lost.

**`test_multiplier_one_is_graph_identical`, implementably.** A jaxpr carries no variable *names*, so "contains no reference to `obs_hides_agent`" is not assertable as written. Identify the leaf positionally:

```python
leaves, treedef = jax.tree_util.tree_flatten(params)
idx = next(i for i, l in enumerate(leaves) if l is params.obs_hides_agent)   # identity, not equality
jaxpr = jax.make_jaxpr(lambda p: update_body(state, info, p, new_pos))(params)
invar = jaxpr.jaxpr.invars[idx]
consumed = any(invar in eqn.invars for eqn in jaxpr.jaxpr.eqns)
```

Assert `consumed is False` at `1.0` and `True` at `3.0`. The second half stops the test passing for the wrong reason — one that only checks the OFF case also passes when the feature was never wired up. `obs_hides_agent` is a traced leaf (not `struct.field(pytree_node=False)`), which is what puts it in `invars`; if that ever changes, rewrite this test rather than delete it.

**Docs, all in this commit:**

- `docs/environment/05_body_homeostasis.md` — §"Recovery (Streak-Based Exponential)" (`:162`): add the multiplier to the equation block (`:174–175`), extend the default recovery table (`:190`) with an in-bush column, and add a note under "**Streak reset rule**" (`:200`) recording the D2 decision and its reason.
- `docs/environment/02_config_schema.md` — mandatory-key reference (`:1225`), the `load_env_params` excerpt (`:1890`), and the static-vs-dynamic table (`:1460`).
- `docs/environment/CONFIG_GUIDE.md` — §5, plus the recovery-path note:
  > If an older repo config, or a saved run config under `results/<run>/models/config.yaml`, fails to load with `Configuration key 'body.recovery_in_bush_multiplier' is required but missing`, the behaviour-preserving value is `1.0`. For a **repo** config, add the key. A **saved run config must not be edited** — it is the historical record of what that run trained with; supply the value through the read-only compatibility path instead. This key is the sixth to land this way; see [[SAVED_RUN_CONFIG_COMPAT]], which measured that only 33 of 493 frozen run-configs rebuild at current code.
  (Paired-contract requirement with `02_config_schema.md`: same commit.)
- `docs/environment/CONFIG_CRITICAL_SETTINGS.md` — registry row + dated change-log entry carrying the key, its inert value, the static-guard inertness argument, the measured **12 passed with zero fixtures moved**, the 12-config + 20-test-module migration, and that this is the sixth mandatory key and does **not** fix the saved-run population.
- `docs/develop/active/refactors/SAVED_RUN_CONFIG_COMPAT.md` — append one line to its key table. Append only; do not restructure another author's plan.

---

## Verification — what can actually fail, per commit

Each check has a stated expected value the change could plausibly violate. "It passed" is not a verification; "it produced exactly the predicted set" is.

**Baseline.** The gate is **72 passed** through A1 and **12 passed** from A2 onward.

### A1
1. **The pre-registered fixture set, with git as the artefact of record.** Fixture `.npz` bytes are deterministic for an unchanged config (Assumption 5), so the set of fixtures whose bytes changed in this commit *is* the measured red set — no reliance on the developer having run the gate first and written it down:
   ```bash
   git show --stat <A1-sha> -- tests/env/fixtures/
   ```
   Prediction: **exactly 1 modified** — `configs__environment__default.npz` — **and 71 untouched**. In particular all 14 ladder, 10 directional, 6 verification, 5 continual and 36 archived fixtures must be untouched; they are standalone and do not inherit, so anything moving there means A1 reached further than intended and is a stop-and-diff. No fixture may be **added**: the two campfire `.npz` the generator creates are deleted before staging.
   Read the positive half as expected rather than guaranteed — `default.yaml` going red needs an animal to actually attempt a bush cell within 100 steps of seed 0, very likely on a 10×10 grid with 4–10 bushes and up to 6 animals, but not a law. If unchanged, use check 3 to confirm the bush really did resolve to `blocks_animals=True` before concluding anything.
2. `git status --short tests/env/fixtures/` → exactly one `M`, nothing untracked. Then `JAX_PLATFORMS=cpu pytest tests/env/test_thermal_parity.py -q` → **72 passed**.
3. **The authoritative key check, at the loader, not in the text.** A grep over YAML is a re-derivation from source and cannot see a config reverting the key via list-replace — the exact hazard F2 describes. Assert on resolved `EnvParams` across all 8 maintained worlds:
   ```python
   for p in ['configs/environment/default.yaml'] + glob('configs/environment/experiment/basic/*.yaml'):
       params = load_env_params(load_env_config(p))
       assert not bool((params.obs_hides_agent & ~params.obs_blocks_animals).any()), p
   ```
   → **8/8 pass**. `basic/00` passes vacuously (no concealing obstacle), which is the correct outcome and worth noting rather than reading as coverage.
4. **The inheritance actually carries** — `load_env_params(load_env_config('…/basic/04-jump_attack_10x10.yaml')).obs_blocks_animals` is all-True on the bush slots with **no edit to that file**. This is the check that the `extends:` chain works, and it is the one that would catch a bad merge into `basic/03`.
5. No collateral: `git diff --name-only` lists exactly `default.yaml`, `basic/01,02,03`, three docs and one fixture. Nothing else under `configs/`.
6. `tests/env/test_bush_blocks_animals.py` still passes — its `test_default_off_parity` uses inline YAML, not the base file, so it should be unaffected; a red here means the loader fallback changed, which was not in scope.
7. `CONFIG_CRITICAL_SETTINGS.md` carries the dated entry **including the fallback-default exception**. Its absence is a verification failure, not a nit — it is the only place the retained fallback is justified.

### A2
1. **Pre-move sweep, run before `git mv` and pasted into the Implementation Report.** This is the commit's load-bearing check and the `b093023` precedent at 227× scale:
   ```bash
   grep -rn 'experiment/behavior_probes\|experiment/sensory_ladder\|experiment/sensory_directional\|experiment/olfactory_ambiguity\|experiment/basic_bushrefuge\|experiment/basic04_variants\|experiment/basic_curriculum\|experiment/curriculum_basic_01_02_03\|experiment/thermal\|experiment/hypervig_scarcity\|--configs-dir' \
     --include='*.py' --include='*.sh' --include='*.yaml' scripts/ tests/ src/ configs/ train.py *.sh \
     | grep -v '^configs/environment/experiment/'
   ```
   Every hit is triaged live-vs-prose and the live ones repointed. **Post-move, the same sweep returns only the repointed references.**
2. **The whole suite, both passes, green** — and specifically `tests/env/test_inactive_animal_offgrid.py`, which loads a `basic_curriculum/` path and is the one test known to break on this move.
3. `git status --short | grep -c '^R'` → **227**. Rename-detected, not delete-plus-add; `D`/`A` pairs mean `git log --follow` is broken for every archived world.
4. **The archived `extends:` chains still resolve** — for the 24 bush-refuge configs in particular (10 `restpremium` → `basic_bushrefuge/04`, 10 `_nohide` → their siblings), `load_env_config(new_path)` must succeed. Policy says archived configs are not *kept* loadable; it does not say A2 may break them on the way out, and these chains are self-contained within the moved set so they should survive unchanged. If any raises `FileNotFoundError`, the move split a chain — investigate before accepting. Configs that already failed to load before A2 are expected to keep failing; compare against a pre-move capture rather than asserting success outright.
5. **The gate shrank by exactly the predicted set**: `git show --stat <A2-sha> -- tests/env/fixtures/` → **60 deletions, 0 modifications, 0 additions**, and the 60 are exactly the 36 `archive` slugs + 14 `sensory_ladder__*` + 10 `sensory_directional__*`. Then `pytest tests/env/test_thermal_parity.py -q` → **12 passed**.
6. The three collectors agree: `collect_configs()` and `_collect_configs()` return identical lists (they are documented as verbatim copies), and none of the three returns a path under `archive/`.
7. `CONFIG_CRITICAL_SETTINGS.md` records the 72 → 12 gate reduction **with the number**.

### B1
1. `pytest tests/env/test_thermal_parity.py -q` → **12 passed**, `git status --short tests/env/fixtures/` → **empty**. A pure refactor that moves a fixture is not a pure refactor.
2. `test_bush_blocks_animals.py`, `test_unified_parity.py`, `test_visual_parity.py` — unchanged counts.
3. No surviving inline copy: in `src/environment/core.py`, `grep -c 'jnp.all(.*obs_pos =='` → **1** (inside the helper).
4. `git diff --stat` → `src/environment/core.py` only.
5. Speed: `_hunt_step` is in the per-step hot path. Record before/after steps-per-second on the same node, config and seed, over a budget long enough that warm-up does not dominate. Expected **0%** — identical arithmetic behind a call JAX inlines. Over 5% needs discussion; over 15% blocks.

### B2
1. `pytest tests/env/test_thermal_parity.py -q` → **12 passed**, `git status --short tests/env/fixtures/` → **empty**. With the static guard and every config at `1.0`, a moved fixture means the inertness argument is wrong.
2. `pytest tests/env/test_recovery_in_bush.py -v` → 5 passed, with the first three **demonstrated red** on the untouched tree first (test-first ordering, no `git stash`).
3. **Migration completeness, without the circularity.** Once the key is mandatory, a config lacking it fails `load_env_params` and drops out of the enumerator's own output — so "every file the enumerator lists has the key" is true by construction and cannot fail. Instead:
   a. At the **pre-B2** tree, run the enumerator and save the list to `tmp/<ts>_b2_target_configs.txt` (expect 11, plus `default.yaml` = 12).
   b. After the change, assert every path in that **saved** list contains `recovery_in_bush_multiplier`.
   c. After the change, re-run the enumerator and assert it returns **the same set**. Fewer means a config that used to load no longer does — the failure (b) alone cannot see.
4. **The 7 `basic/*` files are untouched and still work** — `git diff --name-only -- configs/environment/experiment/basic/` is **empty**, and `load_env_params(load_env_config('…/basic/05-sensory_noise_10x10.yaml')).recovery_in_bush_multiplier == 1.0`. That pair is the check that inheritance really did replace the rollout, rather than the rollout having been quietly skipped.
5. `test_no_recompile.py` stays green: a constant multiplier must not recompile. (A *changed* multiplier recompiling is intended — that is what the static field buys.)
6. `CONFIG_CRITICAL_SETTINGS.md` carries the dated entry, stating the sixth-key fact rather than implying the guide note fixes saved runs.
7. `tmp/` holds the pre-B2 `hiding_drivers.py` snapshot (F10), path recorded.
8. Speed: at `1.0` the guard is not traced; expected **0%**. Same discipline as B1.

---

## Checkpoints

- [x] CP0 — **P1 holds**: `git status --short configs/environment/default.yaml` was **empty** at the start of A1; no parallel session's work in that file. ✅
- [x] CP1 — **D2 is answered: NO reset.** `rest_streak` stays location-independent, for the plan's own reasons (a location term would move `new_rest_streak` — and survival — for every config *including* those at multiplier `1.0`, making an inert setting non-inert; `05_body_homeostasis.md:200` documents the streak as a function of the action alone; and banking a streak means resting in the open, which is where predators are). Pinned by `tests/env/test_recovery_in_bush.py::test_streak_not_location_dependent` and recorded in `05_body_homeostasis.md` under "Streak reset rule". ✅
- [x] CP2 — A1: **met, after the instrument was corrected.** For `thermal_parity/` the prediction held exactly (1 modified, 0 added, 71 untouched). Three OTHER byte-parity families the plan never enumerated also went red; that was escalated rather than worked around, the user decided **freeze the worlds, not the fixtures**, and all four families are now green at their pre-A1 baselines (8 / 34 / 27 / 72) with **no fixture re-baselined**. F6 rewritten to count all four. ✅
- [x] CP3 — A2: **met, and it is what caught three plan errors.** The sweep ran before any `git mv`; artefact `tmp/20260915_012443_a2_premove_reference_sweep.txt` (five sections), triaged live-vs-prose. Re-deriving the triage rather than trusting F5 is what surfaced the 124 broken `extends:` edges, the ten joined-component callers and the two hard-coded generator `OUT` paths. Post-move sweep: zero stale references outside two deliberately-frozen comment lines. ✅
- [x] CP4 — A2: **met.** `--configs-dir` was section [3] of the sweep (150 hits). Two curricula are affected and both are named in the report: `configs/continual/basic_01_02_03_dreamer.yaml` (comment → `archive/curriculum_basic_01_02_03/`) and `configs/continual/basic_curriculum_schedule_longL4.yaml` (launched in practice with `--configs-dir …/experiment/basic_curriculum`, per `train_command-agent.sh:738–815`). Both repointed; nothing was red either way, which is the point. ✅
- [x] CP5 — A2: **met exactly.** 60 deleted (36 `archive` + 14 `sensory_ladder__*` + 10 `sensory_directional__*`), 0 modified, 0 added, nothing untracked; `test_thermal_parity.py` → **12 passed, 20 skipped**. The other three families measured separately and unchanged (34 / 8 / 27), so the four-family total is **119 → 59** as F6 predicts. ✅
- [x] CP6 — B1: **met.** `git diff --name-only -- src/ tests/ configs/ scripts/` returns exactly
  `src/environment/core.py` (34 insertions, 13 deletions); `git status --short tests/env/fixtures/`
  is empty. All four byte-parity families measured separately, before **and** after, at
  12 / 34 / 8 / 27 — unmoved. Speed 0% on an interleaved A/B against a worktree at `f3161dcc`
  (a naive sequential before/after said −6.3% and was machine drift; both numbers reported). ✅
- [x] CP7 — B2: **met, and the log is pasted.** The whole test module was written and run on the untouched tree first: **5 failed, 2 passed** (`tmp/20260915_b2_tests_PRECHANGE.log`), covering all three the plan names plus two additions. `test_premium_applies_in_bush` failed at ACTUAL `0.099998` vs DESIRED `0.299995`, i.e. it was measuring the multiplier and not something incidental. No `git stash` was used; the pre-change comparator throughout B2 was a throwaway `git worktree` at `a8986c42`. Post-change: **7 passed**. ✅
- [x] CP8 (A1 portion) — Every count in the A1 Implementation Report below is re-derived from a command whose output is pasted. None is copied from this plan.
- [x] CP8 (A2 portion) — Every count in A2's Implementation Report is re-derived from a command whose output is pasted or saved under `tmp/`. Two of the plan's own numbers were **contradicted** by that re-derivation (three collectors → four; two `trajectory_collection` files → three) and one prediction was confirmed to the file (the 60-fixture delete set). ✅
- [x] CP8 (B2 portion) — **met.** Every count in B2's report comes from a pasted command output; the migration list was captured at the pre-change tree and held fixed as B2.3 requires. Re-derivation contradicted the plan in one place and extended it in another: the rollout enumerator returned **exactly** the predicted 12, but the *archived* population the key breaks was measured at **29 live CI inputs + 36 genuinely-lost configs**, which F7 does not mention at all. The speed number was also re-derived after the first measurement disagreed with the source argument — the 3-rep figure said −6.63%, the 6-rep alternating-order figure says −0.35%, and the whole-`jax_step` jaxpr is byte-identical. ✅

---

## Open decisions

**D2 — does `rest_streak` reset when the agent leaves cover? (blocks B2's source.)**
`rest_streak` increments off `info['rested']` alone, so with a non-zero `recovery_accel_rate` an agent can bank a long streak resting in the open and cash the multiplier on the step it enters cover. Recommendation: **no reset — leave `rest_streak` location-independent.** In order of the weight each argument carries:

1. **`rest_streak` is a persisted `EnvState` field with a documented contract.** `05_body_homeostasis.md:200` states it plainly: "The streak depends only on the *action*, not on damage." A location term makes it depend on position — a second behaviour change riding inside a feature whose stated purpose is a recovery multiplier. Configs setting the multiplier to `1.0`, i.e. opting out, would still see survival move. That is the strongest objection.
2. **Scope discipline.** If banking matters empirically it is its own change, with its own key, commit and evidence — the principle that splits Part A from Part B.
3. **The exploit is bounded and self-limiting.** Banking means resting in the open, exactly where a predator can reach you, and the existing `applied_inc <= 0` gate already means a damaged rest step earns nothing.
4. *(Weakest — recorded so it is not mistaken for a law.)* Not resetting keeps the `1.0` path source-identical. Not decisive alone: a location term could sit behind the same static guard and preserve bit-parity equally well. Reasons 1 and 2 settle it.

Trade-off accepted: at high `recovery_accel_rate` the premium can be collected on a streak earned elsewhere, so a study using both knobs should report them together. `test_streak_not_location_dependent` pins the decision so a later change has to argue with it.

**D3 — sequencing against the saved-run compatibility layer. ✅ DECIDED 2026-09-14: ship now.** Put to the user with the 33-of-493 measurement in hand. Part B does not depend on [[SAVED_RUN_CONFIG_COMPAT]]. Accepted cost: this becomes the sixth key to make an already-broken archive of frozen run configs slightly more broken, and the `CONFIG_GUIDE.md` note is a lookup for a human, not a restoration of any saved run. When the compatibility layer lands, this key should join its table and its era-representative fixtures so the *seventh* key is a red test rather than a failed analysis.

---

## Named follow-ups (not in this plan)

0. **⚠️ EVALUATION HAZARD, live from the moment A1 lands — owner `experiment-designer`.**
   A1 makes the bush blocking in the **training** worlds (`basic/*`). It does **not** touch the
   probe worlds. `scripts/eval/dwell_sweep/run_sweep.py:60-61` points at
   `behavior_probes/core/avoidance` and `behavior_probes/explore/avoidance_stat_noise`, and both
   are **permeable** — a bush an animal can still walk into. So an agent trained post-A1 and
   evaluated through the dwell sweep is scored in a world whose bush semantics **differ from the
   world it trained in**. Nothing errors, nothing is visibly broken, and the number is wrong:
   hiding looks less effective than the agent learned it to be, because in the probe world a
   predator can follow it into cover.
   **Until A2 resolves it, post-A1 agents must be evaluated on the blocking `avoidance_bushrefuge`
   probes, not the un-suffixed ones.** F5 treats these two paths only as strings to repoint on the
   `git mv`; that is necessary but not sufficient — the *semantics* diverged at A1, one commit
   earlier, and repointing a path does not fix a world. Surfaced by `env-config-reviewer`'s
   482-config sweep.

1. **Repoint or retire the dwell/avoidance sweep tooling.** A2 repoints `run_sweep.py` and the three `eval_sweeps/` definitions at archived paths so they keep working, but a sweep running against a world the project no longer maintains is a temporary state, not a resting place. Decide whether the probe battery is regenerated into the maintained set or the sweeps are retired with it.
2. **Regenerate a thermal worked example when the temperature system is next used.** A2 archives the only two live examples. Per policy they are regenerated on demand — this is the note that says which files to look at.
3. **Regenerate, do not resurrect, the ladder and directional worlds** (F11). Both families are 41–43 lines drifted from their generators; the stale YAML under `archive/` is not what the generator produces today.

---

## Assumptions made

1. **"Configs" in the maintenance policy means *environment* configs.** `configs/models/`, `configs/train/`, `configs/evaluation/`, `configs/logger/`, `configs/visualization/`, `configs/eval_sweeps/` and `configs/trajectory_collection/` are untouched — they describe agents, training and tooling, not worlds. Only `configs/environment/experiment/` is archived.
2. **`configs/continual/` and `configs/verification/` stay live.** They sit outside `configs/environment/` and so are outside the policy's scope. Verified: 11 standalone configs there carry a `body:` block, which is why B2's rollout is 12 and not 1.
3. **The parity gate stops adjudicating archived configs.** This follows from the policy rather than from a separate decision: a world explicitly not kept loadable must not gate CI. Cost stated in numbers (72 → 12) and logged in the registry (F6).
4. **The two generator `.py` files travel with their output directories.** Recommended in A2 and flagged for explicit confirmation, because a generator left behind pointing at an archived output directory is worse than either alternative.
5. **Fixture `.npz` bytes are deterministic for an unchanged config** — verified on numpy 2.3.5. This lets the generator run over all fixtures while `git status` isolates the ones that genuinely moved, and it underpins A1.1. If a numpy upgrade breaks it, A1.1 falls back to running the gate before regenerating and recording by hand.
6. **`obstacles:` and `hides_agent:` sit at consistent two- and six-space indentation** — verified; the only non-conforming matches are inside comments. The binding checks are loader-level regardless.
7. **`recovery_in_bush_multiplier` is a static `EnvParams` field**, departing from its two `recovery_*` siblings, because that is what makes the `1.0` path a source-level identity rather than a measured one.
8. **The premium multiplies `recovery_amount`**, inheriting the existing rest-and-no-damage gate. A premium that also applied on damaged rest steps would be a different feature.
9. **A2 should not break archived `extends:` chains on the way out**, even though policy does not require them to keep working. Verification A2.4 compares against a pre-move capture rather than asserting success, so configs that were already broken are not mistaken for regressions.

---

## Implementation Report

> **Implemented by**: `developer`
> **Date**: 2026-09-14

### Commit A1 — the bush blocks animals

> **Status: IMPLEMENTED AND VERIFIED.** (This section was first written as
> *VERIFICATION BLOCKED*; the blocker was escalated, decided by the user, and resolved — see
> **Blocker resolution** at the end. The blocker narrative is kept intact below rather than
> rewritten, because how it was found is worth more than a tidy record.)
>
> **Original status: IMPLEMENTED, VERIFICATION BLOCKED.** The four settings-file edits and the four
> doc updates are done and the thermal byte-parity gate is green again at **72 passed**,
> exactly as predicted. But the plan's A1 verification assumed `tests/env/test_thermal_parity.py`
> is *the* byte-parity gate. It is not — there are **four** independent byte-parity fixture
> families under `tests/env/fixtures/`, and **three of them went red** on this change. Two of
> those three carry an explicit "must NOT be regenerated" contract in their own module
> docstrings. Regenerating them would destroy the evidence for guarantees **older than this
> plan**, so that decision is not the implementer's to make. Work stopped here and the tree is
> left dirty with `tests/env/` red in three files. **Details in the Blocker section below.**

#### What was implemented, file by file

| File | Change |
|---|---|
| `configs/environment/default.yaml` | bush entry `blocks_animals: false` → `true`, with the plan's 7-line explanatory comment (fallback + list-replace + pointer to the registry exception). |
| `configs/environment/experiment/basic/01-slow_predator_5x5.yaml` | `blocks_animals: true` added to the bush entry (the only `hides_agent: true` entry), 2-line comment. |
| `…/basic/02-predator_and_rabbit_10x10.yaml` | same. |
| `…/basic/03-random_init_10x10.yaml` | same — bush entry only; the `rock` entry below it is untouched. |
| `docs/environment/CONFIG_CRITICAL_SETTINGS.md` | registry row for `environment.obstacles[bush].blocks_animals` (canonical **true**, movement-mask-only, not in any placement mask) **+** a dated 2026-09-14 change-log entry carrying the four changed files, the measured-vs-predicted red set, the not-comparable-across-the-line warning, the explicit "this change intends to alter behaviour" statement CONFIG_GUIDE §4 requires, and the **deliberate no-fallback-defaults exception** with its reason. |
| `docs/environment/02_config_schema.md` | Obstacle Entity Fields row amended (loader default `False` vs. shipped `true`, on purpose) + a new note under the table explaining the divergence, the authoring rule, and the loader-level check; Optional-Keys-and-Defaults row amended to match. |
| `docs/environment/CONFIG_GUIDE.md` | §1 gains *"The footgun's sharper edge: a redeclared list can silently reverse a project-wide decision"* — `blocks_animals` as the worked example, with the silently-permeable YAML snippet and the loader-level check that actually binds. (Paired contract with `02_config_schema.md`: same change.) |
| `docs/develop/active/refactors/BUSH_BLOCKS_ANIMALS.md` | Phase-1 spawn-exclusion caveat marked **stale** citing F1 + the wiki overlap-resolution measurement; `last_updated` bumped to 2026-09-14. |
| `tests/env/fixtures/thermal_parity/configs__environment__default.npz` | regenerated (11296 → 11110 bytes). |

**`basic/00-static_predator_5x5.yaml` deliberately untouched**, and one correction to the plan
here: F3's table and the brief both describe `00` as redeclaring `obstacles:` *with rocks*. It
actually declares **`obstacles: []`** — an explicitly empty list (line 42). The action is the
same (none), and the reasoning is unchanged, but the stated reason in F3 is wrong: it is not
"rocks only, no bush to block", it is "no obstacles at all". `03-random_init_10x10_ckpt1k`,
`04-jump_attack_10x10` and `05-sensory_noise_10x10` declare no `obstacles:` list and needed
nothing, as predicted.

#### `git diff --stat` — the FINAL shape (re-run, not the pre-freeze one)

An earlier revision of this report pasted the pre-freeze stat (9 files / 99 insertions). That was
stale the moment the blocker was resolved. Re-derived:

```
 configs/environment/default.yaml                   |   8 +-
 .../experiment/basic/01-slow_predator_5x5.yaml     |   2 +
 .../basic/02-predator_and_rabbit_10x10.yaml        |   2 +
 .../experiment/basic/03-random_init_10x10.yaml     |   2 +
 .../active/refactors/BUSH_BLOCKS_ANIMALS.md        |  18 ++-
 docs/environment/02_config_schema.md               |  31 +++++-
 docs/environment/CONFIG_CRITICAL_SETTINGS.md       |  11 ++
 docs/environment/CONFIG_GUIDE.md                   |  44 ++++++++
 scripts/verification/capture_sensor_baseline.py    |  31 +++++-
 .../configs__environment__default.npz              | Bin 11296 -> 11110 bytes
 tests/env/test_directional_sensors.py              |  11 +-
 tests/env/test_unified_parity.py                   |  31 +++++-
 tests/env/test_visual_parity.py                    | 123 ++++++++++++++++++++-
 13 files changed, 296 insertions(+), 18 deletions(-)
```

Plus **4 new untracked files** under `tests/env/fixtures/frozen_parity_worlds/` (3 frozen worlds +
README) and **1 new test module**, `tests/env/test_maintained_worlds_bush_blocks_animals.py`.
So: **13 modified + 5 new**. A1.5 (no collateral) still holds — 4 configs, 4 docs, 1 regenerated
fixture, 3 repointed test modules, 1 repointed script, 1 new test, 4 new frozen-world files, and
nothing else. The plan's A1.5 says "three docs"; the File Changes list has **four**, which is right.

#### A1.3 — the binding check, at the loader (the authoritative one)

`load_env_config` → `load_env_params` over all 8 maintained worlds, asserting
`not (obs_hides_agent & ~obs_blocks_animals).any()`:

```
PASS n_obs= 22 hides= 10 blocks= 10                                   configs/environment/default.yaml
PASS n_obs=  0 hides=  0 blocks=  0 (vacuous: no concealing obstacle) .../basic/00-static_predator_5x5.yaml
PASS n_obs=  6 hides=  3 blocks=  3                                   .../basic/01-slow_predator_5x5.yaml
PASS n_obs= 22 hides= 10 blocks= 10                                   .../basic/02-predator_and_rabbit_10x10.yaml
PASS n_obs= 22 hides= 10 blocks= 10                                   .../basic/03-random_init_10x10.yaml
PASS n_obs= 22 hides= 10 blocks= 10                                   .../basic/03-random_init_10x10_ckpt1k.yaml
PASS n_obs= 22 hides= 10 blocks= 10                                   .../basic/04-jump_attack_10x10.yaml
PASS n_obs= 22 hides= 10 blocks= 10                                   .../basic/05-sensory_noise_10x10.yaml

8/8 pass
```

**A1.4 — inheritance carries with no edit to the file**, on `basic/04-jump_attack_10x10.yaml`:
bush slots (`hides_agent` True) = **10**, of those `blocks_animals` True = **10**, all-True on
bush slots = **True**. `basic/00` passes **vacuously** (0 obstacles), which is the correct
outcome and is not coverage.

#### A1.1 / A1.2 — the measured red set, recorded BEFORE regenerating anything

Baseline first, on the untouched tree: `JAX_PLATFORMS=cpu pytest tests/env/test_thermal_parity.py -q`
→ **72 passed, 286 skipped in 213.75s**.

After the four config edits, before touching any fixture, the same command:

```
FAILED tests/env/test_thermal_parity.py::test_thermal_parity[configs__environment__default]
  - AssertionError: configs__environment__default: 'reward' is not byte-identical to the
    pre-thermal reference. This is a regression — diff it, do not widen a tolerance.
1 failed, 71 passed, 286 skipped in 183.81s (0:03:03)
```

| | Predicted | Measured | |
|---|---|---|:--:|
| `thermal_parity` fixtures red | exactly 1, `configs__environment__default` | exactly 1, `configs__environment__default` (on `reward`) | ✅ |
| ladder / directional / verification / continual / archive fixtures red | 0 of 71 | 0 of 71 | ✅ |
| fixtures added | 0 | 0 | ✅ |

The positive half of A1.1 landed as hoped: an animal did attempt a bush cell within 100 steps
of seed 0 on the base config, so the change is demonstrably live rather than merely declared.

After `scripts/fixtures/generate_thermal_parity_fixtures.py`:
`git status --short tests/env/fixtures/` → **exactly one `M`**, and
`git ls-files --others --exclude-standard tests/env/fixtures/` → **empty**.
Re-running the gate: **72 passed, 286 skipped in 176.24s**.

**CONFIG_GUIDE.md Maintenance Contract §4, stated explicitly as required:** *this change
deliberately alters behaviour.* A bush cell an animal could previously step onto now rejects
it, so animal trajectories — and through them the PRNG stream and the reward series — differ
from step one on any world with a concealing bush. The affected fixture was regenerated on
that basis, deliberately and not as a tolerance widening. The same statement is recorded in
the `CONFIG_CRITICAL_SETTINGS.md` change-log entry.

#### Deviation: the two campfire `.npz` the plan says to delete were never created

The plan (File Changes → Fixtures, and A1.1) predicts the generator creates 2 new untracked
`.npz` for `experiment/thermal/campfire_world*.yaml`, to be `rm`'d before staging. **It does
not.** Both configs fail at **run** time, not load time, inside `_capture_state`
(`generate_thermal_parity_fixtures.py:126`, reached from `:154`), so the generator reports
`SKIP (run error)` and writes nothing:

```
configs walked:   358
fixtures written: 72
skipped:          284 load errors, 2 run errors
```

Nothing to delete; nothing was deleted. This is **pre-existing** and independent of A1 — the
failure is inside state capture, not in anything `blocks_animals` touches. Worth folding into
A2, which archives those two configs anyway, and worth noting that the plan's belief that they
are merely "fixture-less but runnable" is wrong.

#### ⛔ Blocker — the plan verified against ONE parity gate; there are FOUR

This is the finding that stops A1. `tests/env/fixtures/` holds four independent byte-parity
fixture families, not one:

| Family | Test | Fixtures | A1 result |
|---|---|---:|---|
| `thermal_parity/` | `test_thermal_parity.py` | 72 | **1 red → regenerated → 72 passed** ✅ (the plan's instrument) |
| `parity/` | `test_unified_parity.py` | 34 | **1 red**: `configs__environment__default` ⛔ |
| `visual_parity/` | `test_visual_parity.py` | 12 | **3 red**: `default`, `01-slow_predator_5x5`, `02-predator_and_rabbit_10x10` ⛔ |
| `directional_sensors/obs_baseline.npz` | `test_directional_sensors.py` | 1 | **1 red**: `max abs diff 1.818e+00` ⛔ |

Measured, per file, on the current tree:

```
tests/env/test_unified_parity.py         1 failed, 33 passed, 324 skipped
  FAILED test_parity[configs__environment__default]
tests/env/test_visual_parity.py          3 failed, 5 passed
  FAILED test_visual_parity_byte_equal[default-…/configs/environment/default.yaml]
  FAILED test_visual_parity_byte_equal[01-slow_predator_5x5-…]
  FAILED test_visual_parity_byte_equal[02-predator_and_rabbit_10x10-…]
tests/env/test_directional_sensors.py    1 failed, 26 passed
  FAILED test_observation_is_bit_identical_to_stored_pre_change_fixture
         - AssertionError: max abs diff 1.818e+00
```

**All three pass at the pre-change baseline** (measured in a throwaway `git worktree` at HEAD,
never by stashing the live tree): `test_directional_sensors` 27 passed, `test_unified_parity`
34 passed + 324 skipped, `test_visual_parity` 8 passed. So these are **caused by A1**, and they
are the *expected* consequence of a real behaviour change — not a mistake in the edit.

**Why this is not the implementer's call.** Each of the three pins a guarantee *older than this
plan*, and two say so in their own words:

- `test_visual_parity.py:11–15` — *"Fixtures were captured on the PRE-CHANGE commit … These
  fixtures must NOT be regenerated after the refactor."* Its `--gen-fixtures` flag is documented
  *"on the pre-change commit ONLY"*. Regenerating erases the proof that the DIRECTIONAL_SENSORS
  sensor refactor preserved visual observations.
- `test_directional_sensors.py:68` — `test_observation_is_bit_identical_to_stored_pre_change_fixture`,
  same purpose, same era.
- `test_unified_parity.py:3` — *"pre-refactor fixture"*.

Regenerating them to make A1 green would silently convert three pre-refactor guarantees into
post-`blocks_animals` snapshots, and no future reader would know. That is a scope decision for
the plan owner.

**What the plan got wrong, concretely.** F6 and the A1 verification section treat
`test_thermal_parity.py` as "the project's byte-parity regression gate" (72 → 12 configs).
`CONFIG_GUIDE.md`'s own Maintenance Contract §4 names a *different* pair — `test_unified_parity.py`
and `test_visual_parity.py` — as "the parity gate", and the plan cites those two only as *B1*
checks expected to show "unchanged counts". Nothing in A1 anticipated that a base-config
behaviour change would redden them. **A2's F6 accounting (72 → 12) is also incomplete for the
same reason** and should be revisited before A2 is implemented.

One curiosity for whoever picks this up: `visual_parity` covers `03-random_init_10x10` and
`04-jump_attack_10x10` too, and **those passed** while `default`, `01` and `02` failed. Worth
understanding before regenerating anything — it may mean no animal contests a bush cell within
that config's scripted 1000-step action sequence, or it may mean those two fixtures are stale.

#### Parity gate — both passes, as documented

**Pass 1 — `JAX_PLATFORMS=cpu pytest tests/env/`.** The whole-directory run **aborts**
(`Fatal Python error: Aborted`, exit 134) inside XLA compilation in
`tests/env/test_thermal_rendering.py`. This is **pre-existing**: the same abort reproduces at
the untouched baseline in the worktree, and the file passes **16 passed** in isolation on the
current tree. It is a cross-test resource/state interaction, not an A1 regression, and it means
a single whole-directory `tests/env/` invocation cannot report a total today. Results were
therefore measured **file by file** (36 files, all CPU-pinned, `-p no:randomly`):

```
test_backward_compat_configs.py                  74 passed, 284 skipped
test_behaviour_validation.py                     10 passed
test_body_temperature_observation.py             15 passed
test_bush_blocks_animals.py                       4 passed          <- A1.6 ✅
test_config_layer_silent_failures_20260723.py     5 passed
test_config_strict_load.py                        3 passed
test_directional_sensors.py                       1 failed, 26 passed    <- BLOCKER
test_disengage_on_contact.py                      3 passed
test_distributional_yaml.py                      12 passed
test_entities_schema.py                           5 passed, 2 skipped
test_extends_layering.py                          7 passed
test_extero_noc_parity.py                         3 passed
test_inactive_animal_offgrid.py                   3 passed
test_inclusive_integer_range_sampling.py          7 passed
test_info_dict_aliases.py                         5 skipped
test_initial_state_ranges.py                      6 passed
test_int_distributional_sampling.py               8 passed
test_metabolic_coupling.py                       11 passed
test_no_recompile.py                              3 passed
test_per_episode_count.py                        10 passed
test_per_episode_logging.py                       9 passed
test_per_episode_sampling.py                      8 passed
test_predator_jump.py                             8 passed
test_thermal_body.py                              5 passed
test_thermal_field.py                             9 passed
test_thermal_parity.py                           72 passed, 286 skipped  <- the gate ✅
test_thermal_rendering.py                        16 passed
test_thermal_reward_gate.py                      78 passed
test_thermal_validation.py                       34 passed
test_thermoception.py                            14 passed
test_truncation_not_death.py                      2 passed
test_unified_parity.py                            1 failed, 33 passed, 324 skipped  <- BLOCKER
test_v1_path_guard.py                            54 passed
test_visual_parity.py                             3 failed, 5 passed     <- BLOCKER
test_visual_properties.py                         5 passed, 2 skipped
test_visual_sampling.py                           6 passed, 1 skipped
```

**A1.6 ✅** — `test_bush_blocks_animals.py` **4 passed**; its `test_default_off_parity` uses
inline YAML, so the loader fallback is confirmed unchanged, as the plan expected.

**Pass 2 — `pytest tests/ --ignore=tests/env` (no pin, as documented).**
Measured: **51 failed, 580 passed, 2 skipped, 8 errors in 3021.76s (50:21)**.
**None is caused by A1.** Triaged in three groups:

1. **41 in `tests/test_trajectory_collection.py`** (33 failed + 8 errors), all
   `ValueError: Strict Config: Configuration key 'sensory.visual_value_mode' is required but missing`.
   Root cause traced, not guessed: `_base_cfg()` (`tests/test_trajectory_collection.py:74`)
   loads a **gitignored saved run config**,
   `results/JAX_RecurrentPPO/20260816-152742_rppo_restpremNH_a10_n112/models/config.yaml`,
   which predates a key made mandatory in August. This is precisely the population F8 measured
   (33 of 493 frozen run-configs still rebuild). A1 adds no mandatory key and does not touch
   `visual_value_mode`. **Pre-existing.**
2. **16 failures that were my own measurement error.** I ran the two passes concurrently; under
   that contention 12 `tests/models/test_modulation_*` golden bit-identity tests, 3
   `tests/scripts/test_evaluation_model_rebuild.py` topology-mismatch tests and 1
   `tests/algorithms/dreamer_srl/test_hierarchical_encoder.py` test failed. Re-run **alone** on
   the same tree: **2 failed, 151 passed** — all 16 pass. Recorded because the 51/8 headline
   above is inflated by them and should not be read as a red set.
3. **2 genuinely red, and red at baseline too** —
   `tests/algorithms/dreamer_srl/test_eval_rollout_batched.py::test_batched_eval_rollout_episode_measures_computable`
   (a `bush_entry_*` vs `bush_dwell_*` measure-name **set** mismatch — schema drift, not
   behaviour) and `tests/scripts/test_context_dependence_b0.py::test_b1_rest_rate`
   (`assert nan == 5.882…`). Both fail identically in the pre-change worktree. **Pre-existing.**

So the honest non-env result is **2 pre-existing failures + 41 pre-existing saved-config load
failures, 0 caused by A1.**

#### Speed check

**Skipped, and here is why.** A1 changes no code — the diff is 4 YAML values, 4 markdown files
and 1 regenerated fixture. `src/` is untouched (`git diff --name-only -- src/` is empty), so
there is no new instruction in the hot path: `obs_block_for_animals = obs_blocking | obs_blocks_animals`
at `core.py:560` already executed on every step with the array all-False, and now executes with
some entries True. Same shapes, same ops, same traced graph. Per the Speed Check Protocol this
is a change that provably cannot affect runtime. (Note the plan itself asks for speed numbers
only on B1 and B2, consistent with this.)

#### Known-bugs prior-art check

Ran, not skipped:
`grep -in 'bush\|blocks_animals\|parity\|fixture\|visual_value_mode\|abort\|thermal_rendering' docs/develop/active/issues/KNOWN_BUGS.md`.
**The registry already covers most of what I hit**, which is why the non-env red set is not a
finding:

| What I measured | Registry row |
|---|---|
| `test_batched_eval_rollout_episode_measures_computable` — `bush_dwell` vs `bush_hiding` key-set mismatch | **Already recorded (OPEN, diagnosed).** Commit `6695aa29` renamed the measure across 49 files and touched zero test files. One-word test edit; hand-off already names `developer`. Not mine to fix inside A1. |
| 41 `sensory.visual_value_mode' is required but missing` from a saved run config | **Already recorded**, twice and deliberately split: the tree-config row ("Mandatory config keys keep landing without migrating the archive — 68 stand-alone configs no longer load") and the saved-snapshot row ("A finished run's own saved config stops loading once a new key becomes mandatory"), the latter being [[SAVED_RUN_CONFIG_COMPAT]]'s 493/33 measurement. My case is the **saved-snapshot** population. |
| the two-pass CPU-pin invocation and the 146-false-failure history | **Already recorded as FIXED** (`tests/env/conftest.py`); I followed the documented two-pass form. |
| regenerating `tests/env/fixtures/parity/` fixtures | **Precedent recorded as FIXED** — "Four environment-parity test scenarios were red because their recorded snapshots were stale". Useful precedent for the blocker decision: there, four snapshots were regenerated *after diagnosing* that a config change had deliberately moved the start position, and the argument that it was not a regression was "the failing set is **exactly** the configs that commit touched — zero unexplained residue". **That argument holds here too**: `visual_parity` reddens on exactly `default`, `01`, `02`. |
| `test_visual_parity.py`'s regenerate-on-absence hazard | Noted in the registry as a "sibling pattern" of the extero-nociception gate row. |

**Believed unrecorded — I name `bug-curator` as owner** (I cannot spawn it):
- **`JAX_PLATFORMS=cpu pytest tests/env/` aborts** with `Fatal Python error: Aborted` (exit 134)
  inside XLA compilation in `tests/env/test_thermal_rendering.py`. Pre-existing (reproduces at
  the untouched baseline), and the file passes **16 passed** alone. Consequence: the project's
  **documented** first pass cannot report a total today; results must be gathered per file.
  This is the same class as the recorded conftest row — a gate that cannot be trusted to report —
  and it is not that row, which is marked FIXED.
- **`scripts/fixtures/generate_thermal_parity_fixtures.py` fails at run time** on both
  `configs/environment/experiment/thermal/campfire_world*.yaml` (inside `_capture_state`), so the
  only two live worked examples of the temperature system have no fixture and cannot get one.
- **`tests/scripts/test_context_dependence_b0.py::test_b1_rest_rate`** — `assert nan == 5.882…`,
  pre-existing at baseline.

I did **not** find a registry row for the "four parity families, not one" observation itself,
though the registry clearly knows the families individually.

#### Working-tree state at hand-off

Dirty and **uncommitted**, as required. Nothing staged by me.
⚠️ Two files are **staged by a parallel session** — `docs/develop/INDEX.md` and
`docs/develop/active/refactors/SAVED_RUN_CONFIG_COMPAT.md`. A bare `git commit` here would sweep
them in. Commit A1 with an explicit pathspec over the 9 files listed above. I did not run
`scripts/claude/regen_dev_index.py` despite bumping `BUSH_BLOCKS_ANIMALS.md`'s `last_updated`,
because `INDEX.md` is already modified **and staged** by that other session and regenerating it
would overwrite their in-flight work.

Scratch logs: `tmp/20260914_a1_*.log`.

#### The open question, and how it was answered

**Asked:** do the `parity/`, `visual_parity/` and `directional_sensors/` fixtures get regenerated
as part of A1, or does A1 change scope? Three options were put up — (a) regenerate all four
families and record the re-baselining, (b) keep the three pinned and give them a world that
still has the semantics they were captured under, (c) something else — and the implementer
deliberately did not pick, because each of the three pins a guarantee older than this plan and two
say so in their own docstrings.

**Answered by the user: (b) — freeze the worlds, not the fixtures.** No re-baselining, and no value
override in the test path. `thermal_parity/` explicitly excluded, since it tracks the *current*
world. What was built, what deviated, and the measured result are recorded immediately below.

### Blocker resolution — freeze the worlds, not the fixtures (user decision, 2026-09-14)

**The decision.** The three refactor-parity families keep testing the world their fixtures
captured. No re-baselining, and no value override in the test path. `thermal_parity/` is
explicitly excluded — it tracks the *current* world, so regenerating its one affected fixture was
and remains correct.

**What was built.** A new `tests/env/fixtures/frozen_parity_worlds/` holding pinned pre-A1 copies,
taken **from git** (`git show HEAD:<path>` at `f02e76b9`), never from a working copy:

| Frozen file | Copy of | Form |
|---|---|---|
| `environment__default.yaml` | `configs/environment/default.yaml` | **byte-identical** (the original is standalone) |
| `environment__experiment__basic__01-slow_predator_5x5.yaml` | `…/basic/01-slow_predator_5x5.yaml` | **pre-resolved standalone** — see below |
| `environment__experiment__basic__02-predator_and_rabbit_10x10.yaml` | `…/basic/02-predator_and_rabbit_10x10.yaml` | **pre-resolved standalone** — see below |
| `README.md` | — | what these are, why, the frozen commit, and the do-not-update contract |

Every frozen YAML also carries a ~35-line header comment stating the same, so a reader who opens
one file without the README still cannot mistake it for a live config.

**Deviation, and it is load-bearing: `basic/01` and `02` are pre-resolved, not byte copies.** Both
carry `extends: environment/default`, and `extends:` targets resolve **only** under `configs/`
(`config_loader.py::_resolve_extends` joins against `_CONFIGS_ROOT`). A byte copy would therefore
have kept reading the **live** base file — so freezing the file would not have frozen its world,
and any later edit to the live `default.yaml` would leak in and redden the gate again, which is
precisely what this directory exists to prevent. The chain was resolved **at the frozen commit**
and inlined, using the loader's own merge order (base first, this file's keys on top) with
`extends:` stripped. Equivalence is **not** asserted in a comment — it is proven by the gate:
these worlds reproduce the pinned pre-change fixtures **byte-for-byte**, or the tests fail. They
do.

**A trap found while wiring this up, worth recording.** In `test_visual_parity.py` the fixture
filename is derived from the config **path** (`_config_slug`), and the test generates a fixture
when one is **missing** (`if gen or not os.path.exists(fp)`). So naively repointing a config at its
frozen copy would have changed its slug, made the lookup miss, and sent the test down the
*generate* branch — **silently re-baselining the exact artefact the freeze exists to protect, while
reporting green.** A `_SLUG_OVERRIDE` map pins each frozen config back to its original slug; the
same shape of fix (`_FROZEN_LOAD_PATH`, with the slug computed from the original path) is used in
`test_unified_parity.py`. This is the same regenerate-on-absence hazard the KNOWN_BUGS registry
already records as a "sibling pattern" of the extero-nociception gate.

**Files changed for the freeze:**

| File | Change |
|---|---|
| `tests/env/fixtures/frozen_parity_worlds/` | **new** — 3 frozen configs + README |
| `tests/env/test_visual_parity.py` | `_FROZEN` map + `_SLUG_OVERRIDE`; 3 of 7 entries repointed; `_fixture_path` honours the override. The other 4 configs still read the live tree. |
| `tests/env/test_unified_parity.py` | `_FROZEN_LOAD_PATH`; `default.yaml` repointed, slug still computed from the original path. All other configs read the live tree. |
| `tests/env/test_directional_sensors.py` | reads `cap.PARITY_WORLD`; npz key unchanged. |
| `scripts/verification/capture_sensor_baseline.py` | `PARITY_WORLD` constant; `CONFIGS` becomes `{original_path: load_path}` so the **npz key stays the original config path** while the world read is the frozen one. |

Each of those five carries an in-code comment stating the four-families/two-purposes distinction
and naming `thermal_parity/` as the deliberate opposite, so the next reader does not "fix" the
inconsistency.

`SCRIPTS_DEPENDENCY_MAP.md` **not** updated, checked rather than assumed: no file under `scripts/`
is added, moved, renamed or deleted, the caller is unchanged, and
`grep -n capture_sensor_baseline docs/environment/SCRIPTS_DEPENDENCY_MAP.md` returns nothing — the
script is not in the map.

#### All four families, measured separately

```
JAX_PLATFORMS=cpu pytest tests/env/test_visual_parity.py -q -p no:randomly
  8 passed in 33.19s                          (was 3 failed, 5 passed)
JAX_PLATFORMS=cpu pytest tests/env/test_unified_parity.py -q -p no:randomly
  34 passed, 324 skipped in 66.94s            (was 1 failed, 33 passed, 324 skipped)
JAX_PLATFORMS=cpu pytest tests/env/test_directional_sensors.py -q -p no:randomly
  27 passed in 52.05s                         (was 1 failed, 26 passed)
JAX_PLATFORMS=cpu pytest tests/env/test_thermal_parity.py -q -p no:randomly
  72 passed, 286 skipped in 165.31s           (unchanged — the live-world gate)
```

Each number equals its **pre-A1 baseline** (8 / 34 / 27 / 72), so the freeze restored the
guarantees rather than papering over them.

#### Integrity checks

- `git status --short tests/env/fixtures/` → **one `M`**, `thermal_parity/configs__environment__default.npz`.
  **No other fixture was modified, and none was created** — the self-rebaselining trap did not fire.
- `git ls-files --others --exclude-standard tests/env/fixtures/` → exactly the **4 intended frozen
  files** and nothing else.
- **A1.3 loader invariant re-run after the freeze: 8/8 pass**, unchanged (`basic/00` vacuous at
  `n_obs = 0`).

#### Plan corrections made in this pass

- **F6 rewritten** — it counted one gate; there are four (72 + 34 + 12 + 1 = **119** fixtures).
  Post-A2 sizes now stated per family: the real reduction is **119 → 59**, entirely inside
  `thermal_parity/`. Also recorded there: `CONFIG_GUIDE.md` Maintenance Contract §4 calls
  `test_unified_parity.py` + `test_visual_parity.py` "the parity gate" — **this plan cited the
  wrong one**, which is why A1's prediction was exactly right about one family and blind to three.
  Two A2-relevant facts surfaced: `parity/`'s `_collect_configs()` is **not** among A2's three
  collectors to narrow (34 stays 34 unless A2 decides otherwise, which it should do explicitly),
  and **5 of `visual_parity/`'s 12 fixtures are orphans** for configs that no longer exist.
- **F3 corrected** — `basic/00` declares `obstacles: []`, an empty list, not "rocks only".
- **Fixtures note corrected** — the generator never creates the two campfire `.npz`; the
  delete-before-staging step was removed.

#### Review round — what the three reviewers changed (2026-09-15)

`code-reviewer`, `senior-developer` and `env-config-reviewer` all passed the freeze. Six findings
were fixed in this same commit rather than deferred; each is a real defect, not a nit.

**1. The self-rebaseline path was still open (`code-reviewer`, Moderate).** `test_visual_parity.py`
still read `if gen or not os.path.exists(fp)`, and `_fixture_path` degraded a missed override to a
path-derived slug. So a typo in a `_FROZEN` **key** — a free string nothing checked against the
filesystem — produced a slug with no fixture behind it, and the gate **generated one and reported
green**. That is the exact artefact the freeze protects. KNOWN_BUGS row 156 records this hazard,
already fixed once in `test_extero_noc_parity.py`, and **names this module as the unfixed sibling**;
this diff edits those very lines. The registry's own recipe is now applied both halves:
generation is reachable **only** via `--gen-fixtures`, a missing fixture is a `pytest.fail` naming
the path, and an import-time `_assert_frozen_map_is_sound()` checks the wiring in **both**
directions — every override value resolves to a real `.npz` (catches a bad key), and every config
under `_FROZEN_DIR` is wired into `_FROZEN` (catches a frozen world added but never used, which
would sit inert while its live counterpart was still tested). `test_unified_parity.py` and
`test_directional_sensors.py` were deliberately **not** changed: the former has no write branch at
all (a mistyped key falls back to the live path, which differs in `obs_blocks_animals`, so it goes
red loudly), and the latter's only `savez` is under `--capture` in the script's `main()`.

**Demonstrated, not asserted** — all three failure modes exercised, then restored:

| Demo | Result |
|---|---|
| typo in a `_FROZEN` **key** (`defualt`) | `AssertionError: Frozen-world wiring is broken … no fixture exists at …configs__environment__defualt.npz` — **1 error during collection**, nothing written |
| override **value** pointed at a non-existent fixture | same guard, **1 error during collection** |
| a **non-frozen** config's fixture removed (`03-random_init_10x10`, no override, normal slug) | `Failed: Pinned fixture missing … NOT generating one` — **1 failed, 7 passed**, and `ls` confirms **no fixture was written** |

`git diff` after restore is empty for all three.

**2. The registry entry told the pre-blocker story (`senior-developer`, blocking).** The
`CONFIG_CRITICAL_SETTINGS.md` 2026-09-14 entry claimed "exactly 1 of 72 … matching the
pre-registered prediction" and never mentioned the other three families, the five further red
fixtures, or why `frozen_parity_worlds/` exists. Since that entry is what a future reader uses to
reconstruct A1, it now carries the whole arc: four families / 119 fixtures, the five extra reds
named individually, that `CONFIG_GUIDE.md` §4 names a *different* pair as "the parity gate", the
freeze decision and its rationale, the four post-change green counts, and the row-156 fix.

**3. The blast radius was wrong (`env-config-reviewer`, blocking).** The entry said exposure was
bounded to "8 maintained worlds". A sweep of all **482** configs found **203** loadable configs
with `hides_agent & ~blocks_animals`; 194 are A2's archive set, but **9 are configs this plan lists
as KEPT** — `configs/verification/observability_gates_S{1..4}.yaml` and
`configs/continual/nmn_double_return_stages/0{1..5}_*.yaml`. Re-measured at the loader here: all 9
confirmed permeable (10 of 10 concealing slots each); `olfaction_parity_{neutral,predator}` have no
bush at all. **User decision: leave all nine permeable, deliberately**, and say so — the gates are
verification instruments whose world defines what they verify, and the stages are a curriculum tied
to a specific study. Flipping them would also redden 9 more `parity/` fixtures and need 9 more
frozen worlds. Recorded in the registry entry with all nine named, so a later sweep cannot "finish
the job" by accident. **The true maintained set is 19 worlds, not 8.**

**4. The evaluation hazard this creates** is recorded as **follow-up 0** above, owner
`experiment-designer`: post-A1 agents trained on blocking `basic/*` but evaluated through the
**permeable** dwell-sweep probes meet different bush semantics than they trained on. F5 treats
those two paths only as strings to repoint in A2 — necessary but not sufficient, because the
semantics diverged one commit earlier and repointing a path does not fix a world.

**5. The loader invariant is now a committed test (`senior-developer`).** A1.3 was a one-off paste;
nothing in the suite pinned it, and `test_bush_blocks_animals.py` is all inline YAML so it asserts
nothing about the shipped worlds. New: **`tests/env/test_maintained_worlds_bush_blocks_animals.py`**
— **10 passed**. It *enumerates* `configs/environment/default.yaml` + `experiment/basic/*.yaml`
(so a new `basic/` world is covered the day it lands), resolves each through
`load_env_config` → `load_env_params`, and asserts on the **arrays**, not the YAML text — a grep
re-derives the answer from exactly the source that hides a list-replace revert. It carries two
guards against passing for the wrong reason: the world set must be non-empty, and at least one
maintained world must really have a blocking bush (every other assertion is satisfied by a world
with no obstacles). `basic/00`'s vacuity is documented **in the test** so its green tick is not
misread as coverage. **Verified it actually catches the thing**: deleting the key from `basic/01`
gives `AssertionError: … 3 of 3 concealing obstacle slot(s) have hides_agent=True but
blocks_animals=False`, naming the list-replace cause and the fix; restored byte-exactly after.

**6. Documentation accuracy.** `basic/03` and `04` are **not** frozen and the README now says so in
its own section — the freeze was scoped by observed *redness*, not by which worlds A1 changed, and
those two stay green only because their visual slice is **constant** (1 distinct row over 1000
steps). Freezing them would be cosmetic while that gate checks nothing; the vacuity is a
pre-existing defect routed to `bug-curator`. Also corrected: the "byte-identical" claim is now
"identical apart from the prepended header comment, and resolves to an identical `EnvParams`", with
a runnable `diff` command whose offset was **verified** (the header is 48 lines, so `tail -n +49`);
`f02e76b9` is dated **2026-09-15**, not 09-14; the frozen `01`/`02` headers say **pre-resolved**
rather than "copy", which is the whole subtlety; and four stale citations in rows this change
already edited were fixed — `config_loader.py:704/705/706` → **`:1849/1850/1851`** and `:720` →
**`:1876`** (704-706 is thermal logging; the file had been giving two different line numbers for
one read).

`senior-developer` independently re-derived the frozen-world equivalence — full merged dict plus
all **189** `EnvParams` fields identical for all three worlds — so that claim rests on someone
else's measurement, not only on the gate.

---

### Commit A2 — archive everything but the maintained 8

> **Implemented by**: `developer`
> **Date**: 2026-09-15
> **Status: IMPLEMENTED. Green on both documented passes.** Four errors in the plan were found
> and are named below; one of them (F11 / A2.4, the `extends:` chains) would have silently
> broken 124 archived configs including the whole probe battery the commit repoints live
> tooling at, and one (F5's live-reference list) was incomplete by **ten** live code sites,
> nine of which are test modules that went red on the move.

#### Plain-English summary

Two hundred and twenty-seven world-settings files moved into an `archive/` folder, because the
project has decided to maintain only the base settings file and the seven-stage `basic/` ladder
and to regenerate anything else from its generator when it is next needed. Nothing about any
world the project still runs changed. What the commit actually had to get right was everything
that *points at* those files: two sweep scripts, three evaluation-sweep definitions, two launch
scripts, nine test modules, a fixture generator, and — the part the plan missed — the 124
inheritance links **between** the moved files themselves. The project's byte-for-byte regression
gate deliberately shrinks from 72 adjudicated worlds to 12, which is logged with its number in
the critical-settings registry because a smaller instrument is a real cost, not a detail.

#### What was done, file by file

| Group | Files | Change |
|---|---:|---|
| The move | **234 `git mv` renames** | 13 directories → `configs/environment/experiment/archive/<dir>/`, structure preserved. **227 `.yaml`** + **5 directory `README.md`** + **2 generator `.py`**. `git mv` throughout — never `mv`, never `clean`, never `checkout -f`, never `stash`. |
| `extends:` repair | **124 files** (all inside the moved set) | 124 `extends:` edges repointed to their `archive/` path. **Not in the plan — see Plan error 1.** |
| Live callers | `scripts/eval/dwell_sweep/run_sweep.py` (`CLEAN_PROBE_DIR`, `NOISE_PROBE_DIR`), `scripts/eval/experiment_eval_checkpoint.py` (`DEFAULT_PROBE_DIR` — **not in the plan**), `configs/eval_sweeps/{bushrefuge,restprem,restprem_nohide}_rppo.yaml` (`probe:`), `scripts/lab/launch_ladder_arm.sh`, `scripts/lab/launch_sensory_arm.sh` | repointed at `archive/` |
| Live callers the plan missed | `tests/env/test_{body_temperature_observation,metabolic_coupling,thermal_body,thermal_field,thermal_rendering,thermal_reward_gate,thermal_validation,thermoception}.py` + `scripts/fixtures/generate_metabolic_coupling_fixture.py` | all nine build `experiment/thermal/campfire_world.yaml` from **`os.path.join` components**, invisible to the plan's string-literal sweep. **92 tests went red before this was fixed — see Plan error 2.** |
| Live caller the plan named | `tests/env/test_inactive_animal_offgrid.py` | repointed (docstring + the joined path). The one the plan predicted; **3 passed**. |
| The archived generators | `archive/sensory_ladder/generate_ladder.py`, `archive/sensory_directional/generate_weakened_vision_arms.py` | hard-coded `OUT` repointed; `generate_weakened_vision_arms.py`'s repo-root walk `['..'] * 4 → * 5`. **See Plan error 3.** |
| Gate scope | `scripts/fixtures/generate_thermal_parity_fixtures.py::collect_configs`, `tests/env/test_thermal_parity.py::_collect_configs`, `tests/env/test_backward_compat_configs.py::_collect_all_configs`, `tests/env/test_thermal_reward_gate.py::_collect_configs` | all four exclude `*/archive/*`. **The plan lists three; there are four — see Plan error 4.** |
| Fixtures | `tests/env/fixtures/thermal_parity/` | **60 deleted**, 0 modified, 0 added |
| Prose | `configs/environment/default.yaml` (2), `configs/continual/basic_01_02_03_dreamer.yaml` (1), `configs/trajectory_collection/nmn_olf_{gae_grid,gae_rerun,mc_grid}.yaml` (1 each — the plan named **two**, there are **three**), `configs/models/recurrent_ppo/nmn_input_site_grid/generate_site_grid_arms.py` (1), `scripts/eval/dreamer_srl_probe_eval.py` (2), `scripts/eval/parity_check_eval_rollout.py` (1), `scripts/eval/dwell_sweep/README.md` (1), `scripts/behavior_measures/README.md` (1), `archive/basic_curriculum/README.md` (2), `train_command-agent.sh` (**48**) | path strings updated for accuracy. `train_command-new.sh` **not touched** (the user's file). |
| Docs | `docs/environment/CONFIG_CRITICAL_SETTINGS.md`, `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` | dated change-log entry; two stale launcher rows + `Last updated` |

**Working tree**: 234 `R`/`RM` renames + 60 `D` + **34 `M` of mine** (33 code/config/doc files plus this plan doc, whose Implementation Report and Checkpoints this section is). **Nothing committed, nothing of
the parallel session's staged** (`docs/develop/INDEX.md` and
`docs/develop/active/refactors/SAVED_RUN_CONFIG_COMPAT.md` were already staged by them before I
started and were never touched; `docs/develop/active/meta/artifact_format_bugs.md` and
`docs/diary/2026-09-14.md` are theirs too, unstaged).

#### ⚠️ Four errors in the plan

**1 — F11 and A2.4 are wrong about `extends:`, and this is the one that would have shipped
silently.** The plan says the 24 bush-refuge configs' inheritance chain "resolves itself in A2,
because all 24 files move together and the chain stays closed" (F11), and A2.4 expects the
archived chains to "survive unchanged". **They do not.** `extends:` targets resolve against
`configs/` by their **literal repo-relative string** (`config_loader.py::_resolve_extends`
joins `base_rel` onto `_CONFIGS_ROOT`), **not** relative to the extending file. Moving a base and
its dependent together therefore breaks the link exactly as surely as moving one alone. Measured
on the tree before touching anything: **124** `extends:` edges inside the moved set named a base
that also moved — 93 in `behavior_probes/`, 10 in `basic_bushrefuge_restpremium/`, 10 in
`_nohide/`, 10 in `olfactory_ambiguity_lindecay/`, 1 in `basic_bushrefuge/`. Left alone, 124
archived configs — **including the entire probe battery this very commit repoints the dwell and
avoidance sweeps at** — would have raised `ValueError: Config extends: target … not found` on
first use, with nothing red in CI to say so. The precedent confirms the hazard is real rather
than theoretical: the **99 configs archived in earlier passes** still carry `extends:` strings
naming `basic/05-random_init_10x10`, `basic/07-jump_attack_10x10` and `basic05_variants/…`,
none of which exist — those chains *were* broken on the way out and left broken.

**Deviation taken, and why**: all 124 edges were repointed to their `archive/` path. The plan's
own Assumption 9 says A2 should not break archived chains on the way out, and more decisively,
the commit's stated purpose for repointing `run_sweep.py` and the three `eval_sweeps` files is
"so they keep working" — which is false if the configs behind those paths no longer load.
**Measured both sides**: 227/227 of the moved configs resolved through `load_env_config` before
the move, 227/227 after, and the per-file OK/FAIL diff is **byte-identical**
(`tmp/20260915_012443_a2_{pre,post}move_loadability.txt`).

**2 — F5's live-reference list is incomplete by ten sites, and the missing form is the `b093023`
failure mode exactly.** F5 names one test (`test_inactive_animal_offgrid.py`). In fact **nine
test modules and one fixture generator** load `configs/environment/experiment/thermal/campfire_world.yaml`,
and every one of them builds the path from `os.path.join` **components** —
`_ROOT, "configs", "environment", "experiment", "thermal", "campfire_world.yaml"` — which the
plan's sweep pattern (a slash-joined string literal) structurally cannot see. Measured: the
first post-move whole-directory run was **92 failed, 314 passed, 374 skipped**, every failure a
`FileNotFoundError`. Fixed by repointing all ten; re-measured green. Also missing from F5:
`scripts/eval/experiment_eval_checkpoint.py:56`, a **third** live probe-directory constant
(`DEFAULT_PROBE_DIR`, the during-training evaluation hook), and a third
`configs/trajectory_collection/` file (`nmn_olf_gae_rerun.yaml`).
**The lesson for the next move: sweep for joined-component path forms and for moved
*basenames*, not only for slash-joined literals.** A basename sweep over all 164 distinct moved
filenames was run afterwards and returned 46 hits, all either already repointed or references to
the **kept** `basic/*` files (`tmp/20260915_012443_a2_basename_sweep.txt`).

**3 — F4/A2 says the generators "travel with their directories" but not that they must be
rewired.** Both carry a hard-coded `OUT` naming their pre-move output directory, so a
post-archive run would have written a fresh copy of every arm back into a directory that no
longer exists — the precise "generator pointing at a moved output" failure the instruction to
move them was meant to prevent. Worse, `generate_weakened_vision_arms.py` computes the repo root
as `['..'] * 4` from its own location; one directory deeper that resolves to `configs/`, and its
`os.chdir(_ROOT)` would have silently relocated every relative path in the file. This is the
repo-root depth hazard `SCRIPTS_DEPENDENCY_MAP.md` warns about, firing for real. Both fixed
(`* 4 → * 5`, verified to resolve to the repo root), with the regenerate-don't-resurrect warning
from F11 added as a comment in each.

**4 — "the three collectors" are four.** The plan (F6, A2 File Changes) names
`generate_thermal_parity_fixtures.py::collect_configs`,
`test_thermal_parity.py::_collect_configs` and
`test_backward_compat_configs.py::_collect_all_configs`. There is a fourth verbatim copy in
`tests/env/test_thermal_reward_gate.py::_collect_configs`. All four now exclude `*/archive/*`
and were verified to return the **identical** list of **32** configs with **0** under `archive/`.
Narrowing the fourth changed no test outcome (**18 passed** before and after), because its
parametrisation is already filtered by fixture existence — but leaving one of four copies
diverged is how this class of drift starts.

*(Note on the brief vs. the plan: the task brief named two collectors, the plan three. I followed
the plan, and then found the fourth. The brief and plan do not otherwise conflict.)*

#### The decision the plan required A2 to make explicitly

F6 says applying the archive exclusion to `tests/env/test_unified_parity.py::_collect_configs`
as well would drop that family **34 → 12**, and that A2 must decide rather than inherit.
**Decision: do not narrow it; `parity/` stays at 34.** Its fixtures, like `visual_parity/`'s and
`directional_sensors/`'s, pin the claim that a *past* refactor preserved observations — they are
evidence about code that shipped months ago, not a description of the world as it is now, and 22
of its 34 belong to configs that were already under `experiment/archive/` before A2. Deleting
them would destroy the evidence rather than retire an unmaintained gate. `thermal_parity/` is
the opposite case — it tracks the current world — which is why it is the one that shrinks.
Measured after the move: **34 passed, 324 skipped**, unchanged.

#### Verification — A2's seven checks

**A2.1 — the pre-move reference sweep (CP3), run BEFORE any `git mv`.**
Artefact: `tmp/20260915_012443_a2_premove_reference_sweep.txt` (107 hits on the plan's own
pattern, plus four further sections: bare directory names across all tracked non-doc files, all
`--configs-dir` occurrences, the ~90 doc files that mention a moved directory, and the
`SCRIPTS_DEPENDENCY_MAP.md` grep the plan asks for). Triaged live-vs-prose file by file; the
live list is the table above. **The triage was not trusted — it was re-derived**, and that is
how Plan errors 1–3 surfaced.
Post-move sweep: `tmp/20260915_012443_a2_postmove_reference_sweep.txt`. **The only remaining
non-`archive/` references to the 13 directories are two comment lines inside
`tests/env/fixtures/frozen_parity_worlds/environment__default.yaml`** — a frozen pre-A1 world
whose body must stay byte-identical to `git show f02e76b9:configs/environment/default.yaml`.
Deliberately untouched; it is a frozen test *input*, not a config.

**CP4 — `--configs-dir` was in the sweep, and here are the curricula it names.** Every
`configs/continual/*.yaml` was audited for the stage directory it names. Two are affected and
neither goes red at rest:
- `configs/continual/basic_01_02_03_dreamer.yaml:3` — comment naming
  `curriculum_basic_01_02_03/`. Repointed.
- `configs/continual/basic_curriculum_schedule_longL4.yaml` — its own header names the **kept**
  `experiment/basic`, but `train_command-agent.sh:738–815` shows the eight runs that actually
  used it were launched with `--configs-dir configs/environment/experiment/basic_curriculum`,
  now archived. All eight comment lines repointed.
The other continual configs name `experiment/basic` (kept) or directories archived long ago.

**A2.2 — both documented passes.**

*Pass 1, `JAX_PLATFORMS=cpu pytest tests/env/`* — **the pre-existing whole-directory abort did
NOT reproduce today.** A1 recorded `Fatal Python error: Aborted` (exit 134) inside
`test_thermal_rendering.py` and had to fall back to per-file runs. On this tree the whole
directory completed: **406 passed, 374 skipped, 1 warning in 1112.33s, exit 0, zero failures.**
So the whole-directory total *can* be reported this time; the abort looks intermittent rather
than deterministic, which is worth adding to the row already routed to `bug-curator`.
The per-file run was done anyway, for comparability with A1's table and because the first
attempt is what exposed the 92 `FileNotFoundError`s:

```
test_backward_compat_configs.py                  12 passed, 20 skipped      <- was 74 passed, 284 skipped
test_behaviour_validation.py                     10 passed
test_body_temperature_observation.py             15 passed                  <- repointed
test_bush_blocks_animals.py                       4 passed
test_config_layer_silent_failures_20260723.py     5 passed, 1 warning
test_config_strict_load.py                        3 passed
test_directional_sensors.py                      27 passed                  <- family 4, unchanged
test_disengage_on_contact.py                      3 passed
test_distributional_yaml.py                      12 passed
test_entities_schema.py                           5 passed, 2 skipped
test_extends_layering.py                          7 passed
test_extero_noc_parity.py                         3 passed
test_inactive_animal_offgrid.py                   3 passed                  <- the plan's predicted red, repointed
test_inclusive_integer_range_sampling.py          7 passed
test_info_dict_aliases.py                         5 skipped
test_initial_state_ranges.py                      6 passed
test_int_distributional_sampling.py               8 passed
test_maintained_worlds_bush_blocks_animals.py    10 passed                  <- A1's new loader invariant
test_metabolic_coupling.py                       11 passed                  <- repointed
test_no_recompile.py                              3 passed
test_per_episode_count.py                        10 passed
test_per_episode_logging.py                       9 passed
test_per_episode_sampling.py                      8 passed
test_predator_jump.py                             8 passed
test_thermal_body.py                              5 passed                  <- repointed
test_thermal_field.py                             9 passed                  <- repointed
test_thermal_parity.py                           12 passed, 20 skipped      <- THE GATE, was 72 passed, 286 skipped
test_thermal_rendering.py                        16 passed                  <- repointed
test_thermal_reward_gate.py                      18 passed                  <- repointed; was 78 (= 72 fixtures + 6)
test_thermal_validation.py                       34 passed                  <- repointed
test_thermoception.py                            14 passed                  <- repointed
test_truncation_not_death.py                      2 passed
test_unified_parity.py                           34 passed, 324 skipped     <- family 2, unchanged
test_v1_path_guard.py                            54 passed
test_visual_parity.py                             8 passed                  <- family 3, unchanged
test_visual_properties.py                         5 passed, 2 skipped
test_visual_sampling.py                           6 passed, 1 skipped
```
`test_thermal_reward_gate.py` was re-run after the fourth collector was narrowed: **18 passed**,
identical.

*Pass 2, `pytest tests/ --ignore=tests/env` (no pin, as documented)* — run **alone**, per A1's
contention lesson. Measured: **55 failed, 576 passed, 2 skipped, 8 errors in 4098.39s (1:08:18)**.
Baseline for comparison is A1's **51 failed, 580 passed, 2 skipped, 8 errors**. Triaged:

| Group | Count | Verdict |
|---|---:|---|
| `tests/test_trajectory_collection.py` — 33 failed + 8 errors, all `ValueError: Strict Config: key 'sensory.visual_value_mode' is required but missing` | **41** | **Pre-existing**, identical to A1. `_base_cfg()` loads a **gitignored saved run config** from `results/…/20260816-152742_rppo_restpremNH_a10_n112/models/config.yaml` that predates an August mandatory key. Both KNOWN_BUGS rows cover it. A2 adds no key and touches nothing here. |
| 12 `tests/models/test_modulation_{sites,input_slice}.py` golden bit-identity + 3 `tests/scripts/test_evaluation_model_rebuild.py` topology + 1 `tests/algorithms/dreamer_srl/test_hierarchical_encoder.py` | **16** | **Not real.** Re-run alone on this same tree together with the two new suspects: **1 failed, 160 passed** — all 16 pass. Exactly the group A1 recorded as its own measurement error; it reproduces here even though this pass ran alone, so the interference is internal to the whole-suite run rather than to a parallel job. The 55 headline is inflated by these. |
| `test_eval_rollout_batched.py::…episode_measures_computable` (`bush_entry_*` vs `bush_dwell_*` key-set mismatch) and `tests/scripts/test_context_dependence_b0.py::test_b1_rest_rate` (`assert nan == 5.882…`) | **2** | **Pre-existing**, both red at A1's baseline; the first has an OPEN KNOWN_BUGS row already naming `developer`. |
| `tests/algorithms/dreamer_srl/test_eval_telemetry_wandb.py` — `wandb.errors.CommError: Run initialization has timed out after 90.0s` | **2** | **Environmental** — the test reaches out to WandB. Nothing to do with A2. |
| `tests/algorithms/dreamer_srl/test_loss.py` — `SymlogDistribution.log_prob deviates from the reference` | **1** | **Not real** — passes when run alone (inside the 160-passed group above). Same whole-suite interaction. |
| `tests/test_provenance.py::test_write_provenance_writes_complete_valid_json` — `assert isinstance('unknown', bool)` for `git_dirty` | **1** | **Red, and the cause is measured rather than guessed.** `src/utils/provenance.py::git_dirty` shells out to `git status --porcelain --untracked-files=no` under a **10-second** budget (`_GIT_TIMEOUT_S = 10`) and returns the string `"unknown"` on timeout. Timed on this tree: **301.4 seconds** — 30× the budget, because the repo lives on a NAS and the working tree currently carries 294 staged rename/delete entries. Not a code defect and not caused by any edit in A2; it is A2's *uncommitted size* meeting a latency guard. Expect it to clear once the commit lands. Flagged rather than waved away, because it is a test that was green at A1 and is red now. |

**So the honest non-env result: zero failures caused by A2's code changes.** 41 pre-existing
saved-config load failures + 2 pre-existing reds + 2 WandB-network + 1 NAS-latency artefact of
the uncommitted tree, and 17 that pass when run alone.

**A2.3 — `git status --porcelain`, renames not delete-plus-add.**

```
   234  R / RM   (renames, rename-detected — `git log --follow` survives)
    60  D        (thermal_parity fixtures)
    35   M       (33 mine + 2 unstaged files belonging to parallel sessions)
     2  MM       (staged by a parallel session — NOT touched)
    15  ??       (parallel sessions' diary + sensor-ladder figures — NOT touched)
```

Reconciliation of the 234: **227 `.yaml`** — the number the plan and the brief both predict —
plus **5 `README.md`** (`basic04_variants`, `basic_curriculum`, `behavior_probes`,
`olfactory_ambiguity`, `olfactory_ambiguity_lindecay`) and **2 generator `.py`**. Of the 234,
107 are pure `R` and 127 are `RM` — the 127 being the 124 `extends:`-repaired configs plus the
2 generators plus `basic_curriculum/README.md`. **Zero `D`/`A` pairs among the moved files.**

**A2.4 — the archived `extends:` chains resolve, measured against a pre-move capture.**
227/227 OK before, 227/227 OK after, diff of the per-file OK/FAIL lists **identical**. See Plan
error 1: this check passes *because* the 124 edges were repaired, and would have failed 124/227
otherwise. This is the single most valuable check in the plan and it earned its place.

**A2.5 — the gate shrank by exactly the predicted set (CP5).**
`tests/env/fixtures/thermal_parity/`: **60 deleted, 0 modified, 0 added**, nothing untracked.
The 60 are exactly **36 `…__archive__…` slugs + 14 `sensory_ladder__*` + 10
`sensory_directional__*`**, the plan's prediction to the file. The 12 survivors are 5
`continual/nmn_double_return_stages`, 6 `verification/`, 1 `environment/default` — and they are
**exactly the 12 configs F6/F7 predict as Part B's rollout set**, so that cross-check holds.
`pytest tests/env/test_thermal_parity.py` → **12 passed, 20 skipped** (baseline 72 passed, 286
skipped).

**The four parity families, each measured separately, before and after.**

| Family | Test | Fixtures before | Fixtures after | Test result before | Test result after |
|---|---|---:|---:|---|---|
| `thermal_parity/` | `test_thermal_parity.py` | 72 | **12** | 72 passed, 286 skipped | **12 passed, 20 skipped** |
| `parity/` | `test_unified_parity.py` | 34 | **34** | 34 passed, 324 skipped | **34 passed, 324 skipped** |
| `visual_parity/` | `test_visual_parity.py` | 12 | **12** | 8 passed | **8 passed** |
| `directional_sensors/` | `test_directional_sensors.py` | 1 | **1** | 27 passed | **27 passed** |
| **total fixtures** | | **119** | **59** | | |

**119 → 59, with the entire reduction inside `thermal_parity/` — the plan's F6 prediction,
confirmed rather than assumed.** Each of the other three was measured at its own pre-A2 baseline
in the same session (`tmp/20260915_012443_a2_baseline.log`) and is unchanged.
`tests/env/fixtures/frozen_parity_worlds/` was not touched.

**A2.6 — the collectors agree.** All **four** (see Plan error 4) return the **identical** list of
**32** configs, with **0** under `archive/`.

**A2.7 — `CONFIG_CRITICAL_SETTINGS.md` records the reduction with its number.** A dated
2026-09-15 change-log entry carries: the policy; the 227/13/234 move counts per directory; the
60 deleted fixtures and the gate's **72 → 12**; the four-family **119 → 59**; the explicit
decision to leave `test_unified_parity.py` un-narrowed and why; the four collectors; the
repointed live callers; the 124 `extends:` edges with the 227/227-before-and-after measurement;
the `--configs-dir` curricula; and the regenerate-don't-resurrect warning for the two drifted
generator families.

**`SCRIPTS_DEPENDENCY_MAP.md`** — the plan asks for the grep rather than assuming. Run: the map
**does** document both launchers' config paths, at lines 124–125. Both rows repointed and the
`Last updated` line extended, in this change. No file under `scripts/` was added, moved, renamed
or deleted, so the Maintenance Contract did not fire on its face — the rows were simply stale
the moment the configs moved.

**Live tooling proved live, not merely repointed.** Each constant was imported and resolved:

```
run_sweep.CLEAN_PROBE_DIR        → …/archive/behavior_probes/core/avoidance              exists, 12 yaml
run_sweep.NOISE_PROBE_DIR        → …/archive/behavior_probes/explore/avoidance_stat_noise exists, 12 yaml
experiment_eval_checkpoint.DEFAULT_PROBE_DIR → …/archive/behavior_probes/core/avoidance  exists, 12 yaml
eval_sweeps {bushrefuge,restprem,restprem_nohide} probe: → …/archive/…/avoidance_bushrefuge  exists, 12 yaml each
launch_ladder_arm.sh  A_baseline → …/archive/sensory_ladder/A_baseline.yaml               exists
launch_sensory_arm.sh A_baseline → …/archive/sensory_directional/A_baseline.yaml          exists
```

#### Speed check — skipped, with the reason

`git diff -- src/` and `git diff --cached -- src/` are both **empty**: A2 changes no environment,
model or training code whatsoever. The move renames settings files; the only content edits inside
them are `extends:` strings in archived configs that no maintained world reads, and comments. No
traced graph, op, shape or array changes, so there is no hot path to measure. Per the Speed Check
Protocol this is a change that provably cannot affect runtime. (The plan likewise asks for speed
numbers only on B1 and B2.)

#### Known-bugs prior-art check

Ran, not skipped:
`grep -in 'archive\|config move\|FileNotFoundError\|configs-dir\|extends' docs/develop/active/issues/KNOWN_BUGS.md`.

| What I hit | Registry row |
|---|---|
| 92 `FileNotFoundError` from tests pointing at moved configs | **Recorded precedent, FIXED**: "Two env tests pointed at config paths retired by the basic-ladder re-level" (`b093023`, `ee8b981`+`79775e5`). Same class, caught here **before** commit rather than after. Not a new bug — but the *reason* it was nearly missed (joined-component paths are invisible to a string sweep) is a lesson the row does not carry. |
| A tool pinned at a config directory that no longer exists | **Recorded, OPEN**: "Dreamer speed benchmark points at a config folder that no longer exists". Unaffected by A2 (it names `configs/dreamer_srl/`), but it is the standing example of this failure mode rotting silently. |
| Archived configs that no longer load | **Recorded, OPEN**: "Mandatory config keys keep landing without migrating the archive — 68 stand-alone configs no longer load". A2 does **not** add to that population; it repairs 124 chains that would have joined it. |
| The whole-directory `tests/env/` abort | Routed to `bug-curator` by A1 as believed-unrecorded. **New datum: it did not reproduce today** — the full directory ran clean (406 passed). Intermittent, not deterministic. |
| `generate_thermal_parity_fixtures.py` cannot fixture the two campfire configs | Routed to `bug-curator` by A1. **Still true, and A2 makes it moot for the gate** (those configs are archived and no longer collected) **but not for the tests**: nine test modules still load them — see Follow-up 1. |

**Believed unrecorded, `bug-curator` named as owner** (I cannot spawn it):
- **`extends:` is resolved by literal path, so any config move breaks every chain into the moved
  set — and the repo already contains 99 archived configs with dead `extends:` targets from
  earlier moves.** There is no test that would catch this: `test_backward_compat_configs.py`
  *skips* a config that fails to load rather than failing. This is a structural hazard with a
  demonstrated history, not a one-off.
- **Nine test modules and one fixture generator depend on `experiment/thermal/campfire_world.yaml`,
  which policy now classifies as archived and "not kept loadable"** — see Follow-up 1.

#### Follow-ups (named, not done here)

1. **⚠️ The policy and the test suite now disagree about `experiment/thermal/`. Owner:
   `senior-developer`.** The maintenance policy says archived worlds are not kept loadable and
   will be regenerated on demand. But **nine test modules** (~140 tests: `test_thermoception`,
   `test_thermal_{body,field,rendering,reward_gate,validation}`, `test_metabolic_coupling`,
   `test_body_temperature_observation`) and one fixture generator load
   `archive/thermal/campfire_world.yaml` on every run. The entire temperature-system test suite
   now depends on a file the project has declared unmaintained. The plan's F5 and follow-up 2
   noticed that archiving removes the only live worked examples of the thermal system; neither
   noticed that the tests hold it up. Either those two configs are not really archive material,
   or the thermal tests need their own fixture world under `tests/` (the shape `frozen_parity_worlds/`
   already established). **This is a policy question, not an implementation one, which is why it
   is flagged rather than decided.**
2. **`docs/develop/active/refactors/renderer_layout_redesign/render_current_frames.py:44`** names
   `configs/environment/experiment/thermal/campfire_world.yaml` and is now broken. It is a
   figure-export script that lives under `docs/`, which this role does not edit — flagged rather
   than fixed. One-line change.
3. **Regenerate, do not resurrect** (the plan's own follow-up 3, now load-bearing): both archived
   generators produce output 41–43 lines different from the YAML on disk. The warning is now a
   comment inside each generator as well as in the registry.
4. **The evaluation hazard from A1 (plan follow-up 0) is NOT resolved by A2 and is now one commit
   older.** A2 repoints the dwell-sweep probe paths, which keeps the sweep *running*; it does not
   change the probe worlds' semantics. `archive/behavior_probes/core/avoidance` and
   `…/explore/avoidance_stat_noise` are still **permeable** (`blocks_animals` absent), while
   post-A1 `basic/*` training worlds are blocking. An agent trained after A1 and scored through
   the dwell sweep is measured in a world whose bush rules differ from the one it learned.
   Owner remains `experiment-designer`.

#### Working-tree state at hand-off

Dirty and **uncommitted**, as required. The only staged entries are my own `git mv` renames and
`git rm` fixture deletions (both stage by construction) — plus the two files a parallel session
had already staged before this work began (`docs/develop/INDEX.md`,
`docs/develop/active/refactors/SAVED_RUN_CONFIG_COMPAT.md`), which were never touched. **Commit
A2 with an explicit pathspec.** `scripts/claude/regen_dev_index.py` was **not** run: no develop-doc
frontmatter changed in A2, and `INDEX.md` is staged by that other session.

Scratch artefacts (all under `tmp/`, all timestamped `20260915_012443_a2_*`):
`premove_reference_sweep.txt`, `postmove_reference_sweep.txt`, `basename_sweep.txt`,
`premove_loadability.txt`, `postmove_loadability.txt`, `move_set.txt`, `baseline.log`,
`after.log`, `env_suite.log`, `pass2.log`, `git_status.txt`.

---

### Commit B1 — one in-bush predicate, shared by its callers (no behaviour change)

> **Implemented by**: `developer`
> **Date**: 2026-09-15
> **Status: IMPLEMENTED.** Tree left dirty for review. `src/environment/core.py` is the only
> file changed. All four byte-parity families are at their post-A2 baselines and **no fixture
> moved**. One instruction in the briefing contradicts the plan and was **not** followed — see
> **Deviation D-B1.1**, which is the first thing to read.

#### Plain-language summary

"Is the agent standing in a bush that hides it?" was written out by hand in two different places
inside the environment's step function. Both copies said the same thing, in slightly different
words. This commit writes the sentence **once**, as a small named function, and has both places
call it. Nothing about the simulation changes: the same worlds, the same numbers, the same
recorded observations, byte for byte. The point of doing it now is that the next commit (B2)
needs a **third** reader of that sentence, and a third hand-written copy is how three copies
quietly drift apart.

#### What was implemented, file by file

| File | Change |
|---|---|
| `src/environment/core.py` | **+1 helper**: `agent_in_hiding_obstacle(agent_pos, obs_pos, obs_hides_agent, obs_active=None)` at `:98`, between `calculate_drive` and `update_body` (the position the plan specifies — above `update_body`, B2's future caller). |
| `src/environment/core.py` | `_hunt_step`'s `_eff_hides` / `agent_hidden` block (was `:351–355`) → one call to the helper (now `:376–378`). The explanatory comment is kept. |
| `src/environment/core.py` | `jax_step`'s `agent_in_bush` block (was `:961–964`), **including** its `if state.obs_pos.shape[0] > 0 else jnp.array(False)` tail → one call to the helper (now `:979–986`). The stale cross-reference *"Mirrors the agent_hidden computation inside update_predators (line ~150)"* is replaced by a reference that names the helper, as the plan requires. |

Nothing else. No config, no doc, no fixture, no test file.

```
$ git diff --stat -- src/
 src/environment/core.py | 47 ++++++++++++++++++++++++++++++++++-------------
 1 file changed, 34 insertions(+), 13 deletions(-)

$ git diff --name-only -- src/ tests/ configs/ scripts/
src/environment/core.py
```

#### ⚠️ Deviation D-B1.1 — the briefing asks for a third call site; the plan rules it out. I followed the plan.

The briefing says B1 should produce *"one shared helper consumed by all three call sites, the
third being a new hoisted call above the `update_body` invocation at `:829`"*, justified as
*"B2's recovery gate has to read it, and cannot as the code stands."*

**The plan says the opposite, in three separate places, and I could not implement both:**

1. F9 (plan `:241`): *"A third copy is ruled out. B1 extracts one helper and rewires **these two**;
   **B2** makes `update_body` its third consumer."*
2. The B1 File Changes section ends with *"Nothing else."* after listing exactly two replacements.
3. B2's own source snippet does **not** read `info['agent_in_bush']`. It calls the helper
   **inside** `update_body`, behind the static `if params.recovery_in_bush_multiplier != 1.0:`
   guard, and its comment explains precisely why: *"it is evaluated here rather than read from
   `info['agent_in_bush']` because `update_body` runs at `jax_step:829` and that key is not
   written until `jax_step:961` — and it is legitimate to evaluate early because obstacle
   positions are constant within an episode."*

So the ordering problem the briefing raises is **already solved by the plan**, and the helper is
what solves it: B2 recomputes the predicate early rather than reading a value that does not exist
yet. F9's word "hoisting" means *evaluating the predicate earlier inside `update_body`* — not
restructuring `jax_step`. The plan states this explicitly: *"`jax_step`'s call order does not
change."*

Implementing the briefing's version literally would have added, in B1, a computation with **no
consumer** (B2 has not landed), i.e. dead code inside a commit whose contract is "no behaviour
change, nothing else". The only non-dead reading of it — hoist the computation above `:829` and
put it on `info` there, so `update_body` can read `info['agent_in_bush']` — is a real design
choice, but it is **B2's** design choice and it contradicts B2's written source. Since the
briefing itself says the plan is authoritative, I implemented the plan.

**If you do want the hoist**, it is a ~6-line change and it changes B2, not B1: move the
`agent_in_bush = agent_in_hiding_obstacle(...)` statement and its `info['agent_in_bush'] = ...`
assignment from `:979` up into the `info = {...}` construction at `:817`, then have B2's gate read
`info['agent_in_bush']` instead of calling the helper again. Say the word and I will do it as a
separate change. I did not do it silently.

#### The graph, measured at the primitive level — and one honest caveat

The briefing asks for source-level proof where it exists, and plain disclosure where it does not.
Both apply here, in different places. Measured with `tmp/20260915_b1_micro.py`, which traces the
helper next to verbatim copies of the two blocks it replaced:

```
n_obs > 0 -- helper vs the two originals:
  helper                       n_obs=22  eqns=6  ['and', 'broadcast_in_dim', 'eq', 'reduce_and', 'and', 'reduce_or']
  old _hunt_step longhand      n_obs=22  eqns=6  ['and', 'broadcast_in_dim', 'eq', 'reduce_and', 'and', 'reduce_or']
  old jax_step longhand        n_obs=22  eqns=6  ['broadcast_in_dim', 'eq', 'reduce_and', 'and', 'and', 'reduce_or']
  helper == old_hunt  text: True
  helper == old_step  text: False

n_obs == 0 -- the empty-obstacle guard the code-reviewer flagged:
  helper (guard folds)         n_obs=0   eqns=0  []
  old _hunt_step (no guard)    n_obs=0   eqns=6  ['and', 'broadcast_in_dim', 'eq', 'reduce_and', 'and', 'reduce_or']
  old jax_step (had guard)     n_obs=0   eqns=0  []

value equality over every cell of a small world, n_obs=3:
  mismatches over 64 mask combos x 16 cells x 2 call shapes = 0
```

Read that as three separate statements:

1. **`_hunt_step`, obstacles present — source-level identity, nothing to measure.** The helper's
   jaxpr is **text-identical** to the block it replaced. This is the `calculate_drive` standard
   the briefing asks for: the old expression survives verbatim, so parity is a fact about the
   source.
2. **`jax_step`, obstacles present — same six primitives, different emission order. I cannot claim
   source-level identity here, and I am not claiming it.** The old site computed
   `obs_hides_agent & obs_active` *inside* the `jnp.logical_and(...)` call, so it was traced
   **after** the position comparison; the helper computes it on its own line, so it is traced
   **before**. The resulting DAG is isomorphic — identical primitive multiset, identical operand
   pairing (`reduce_and` result `&` `eff_hides`), one `reduce_or` — but two independent equations
   swap places in the jaxpr. **This is unavoidable with one shared helper**: the two original
   sites had *opposite* orders, so whichever order the helper picks, one of the two sites moves.
   Values are unaffected (0 mismatches over 2,048 enumerated cases above), and the **parity gate
   carries the proof**: all four families pass unchanged with no fixture regenerated.
   Confirmed at whole-`jax_step` scale too — `tmp/20260915_b1_jaxpr_default_n_obs_gt0_{before,after}.txt`
   differ in **exactly** this one region, 5 equations in, 5 equations out, everything else byte-identical:
   ```
   < btq:i32[1,2] = broadcast_in_dim[...]      > btq:bool[22] = and ij ks
   < btr:bool[22,2] = eq kp btq                > btr:i32[1,2] = broadcast_in_dim[...]
   < bts:bool[22] = reduce_and[axes=(1,)] btr  > bts:bool[22,2] = eq kp btr
   < btt:bool[22] = and ij ks                  > btt:bool[22] = reduce_and[axes=(1,)] bts
   < btu:bool[22] = and bts btt                > btu:bool[22] = and btt btq
   ```
3. **The empty-obstacle guard `code-reviewer` flagged during A1 — handled explicitly, and it turns
   out to be unreachable in every maintained world.** The helper's static
   `if obs_pos.shape[0] == 0` guard folds a six-equation reduction over a zero-length axis into a
   constant `False` on `_hunt_step`'s path, which previously had no guard. Value-identical
   (`jnp.any` over an empty array is already `False`), but a genuine graph change, and the
   docstring says so in as many words rather than pretending otherwise. **It cannot fire in any
   world the project maintains**, because a hunter and zero obstacles never co-occur:

   | maintained world | n_obs | predators | neutrals |
   |---|---:|---:|---:|
   | `configs/environment/default.yaml` | 22 | 2 | 2 |
   | `basic/00-static_predator_5x5.yaml` | **0** | **0** | **0** |
   | `basic/01-slow_predator_5x5.yaml` | 6 | 1 | 0 |
   | `basic/02-predator_and_rabbit_10x10.yaml` | 22 | 1 | 1 |
   | `basic/03-random_init_10x10.yaml` | 22 | 2 | 2 |
   | `basic/03-random_init_10x10_ckpt1k.yaml` | 22 | 2 | 2 |
   | `basic/04-jump_attack_10x10.yaml` | 22 | 2 | 2 |
   | `basic/05-sensory_noise_10x10.yaml` | 22 | 2 | 2 |

   The only zero-obstacle world, `basic/00`, has **no animals at all**, so `_hunt_step` is never
   traced there. Confirmed end-to-end: `basic/00`'s whole-`jax_step` jaxpr is **sha1-identical**
   before and after (`d6fd8970669a` both sides).

#### Verification — every number re-derived, output pasted

**B1.1 / B1.2 — all four byte-parity families, measured separately, before and after.**
The `tests/env/` baseline was captured **before** the source edit, so these are before/after pairs
rather than a post-hoc comparison against the plan's text:

| Family | Test module | Before | After | Δ |
|---|---|---|---|:--:|
| `thermal_parity/` | `test_thermal_parity.py` | 12 passed, 20 skipped | **12 passed, 20 skipped** | — |
| `parity/` | `test_unified_parity.py` | 34 passed, 324 skipped | **34 passed, 324 skipped** | — |
| `visual_parity/` | `test_visual_parity.py` | 8 passed | **8 passed** | — |
| `directional_sensors/` | `test_directional_sensors.py` | 27 passed | **27 passed** | — |

All four match the briefing's expected post-A2 sizes (12 / 34 / 8 / 27) exactly. Any movement
would have been a behaviour change; there is none.

```
$ git status --short tests/env/fixtures/
(empty)
```

**No fixture moved, none added, none deleted.** A pure refactor that moves a fixture is not a pure
refactor.

**A1's committed test still green** — `tests/env/test_maintained_worlds_bush_blocks_animals.py`
→ **10 passed** (before **and** after). `tests/env/test_bush_blocks_animals.py` → **4 passed**
(before and after).

**B1.3 — "no surviving inline copy". The plan's stated check is wrong; here is the corrected one.**
The plan predicts `grep -c 'jnp.all(.*obs_pos ==' src/environment/core.py` → **1**. Measured: it
was **8** before this commit and is **7** after. The pattern does not isolate the concealment
predicate — it also matches `move_agent`'s obstacle-collision test (`:41`), the hunter and
wanderer **blocking** checks (`:419`, `:458`, `:518`) and the obstacle-damage tests (`:780`,
`:790`), which are a different predicate (`obs_blocking`, not `obs_hides_agent`) and are out of
scope. **The check that actually binds** is on `obs_hides_agent`, and it passes:

```
$ grep -n 'obs_hides_agent' src/environment/core.py
98:def agent_in_hiding_obstacle(agent_pos, obs_pos, obs_hides_agent, obs_active=None):   <- helper signature
121:    eff_hides = obs_hides_agent if obs_active is None else (obs_hides_agent & obs_active)   <- the ONE consumption
333:               agent_pos, obs_pos, obs_blocking_for_collision, obs_hides_agent, key,      <- _hunt_step signature
348:      - params.obs_hides_agent for the agent_hidden computation inside the function       <- docstring
376:    # agent_hidden: uses obs_hides_agent (bush concealment) AND obs_active ...             <- comment
378:    agent_hidden = agent_in_hiding_obstacle(agent_pos, obs_pos, obs_hides_agent, obs_active)  <- call
605:            params.obs_hides_agent,   # for agent_hidden (byte-parity ...)                 <- pass-through
985:        new_agent_pos, state.obs_pos, params.obs_hides_agent, state.obs_active)            <- call
```

Exactly **one** line consumes `obs_hides_agent` in an expression (`:121`, inside the helper).
Every other occurrence is a signature, a comment, a pass-through argument or a call to the helper.

**B1.4 — the diff touches `src/environment/core.py` and nothing else.** Confirmed above.
Four files in the working tree belong to a parallel session (`docs/develop/INDEX.md`,
`docs/develop/active/meta/artifact_format_bugs.md`,
`docs/develop/active/refactors/SAVED_RUN_CONFIG_COMPAT.md`, `docs/diary/2026-09-14.md`; the first
and third are **staged by that session**). **Nothing was staged by me and nothing was committed.**

**Both documented passes, CPU pin on `tests/env/`:**

```
$ JAX_PLATFORMS=cpu .../python -m pytest tests/env/ -q
406 passed, 374 skipped, 1 warning in 633.08s (0:10:33)          exit 0
```

The intermittent whole-directory abort the briefing warns about **did not fire** this time (it
fired for A1, not for A2, not here). No fallback to file-by-file was needed.

```
$ .../python -m pytest tests/ --ignore=tests/env -q
53 failed, 578 passed, 2 skipped, 1023 warnings, 8 errors in 2998.85s (0:49:58)
```

**None of those 53 is caused by B1, and I measured that rather than asserting it.** Three
independent checks, because this suite turned out to be a poor differential instrument and saying
so is part of the result:

**(a) The same suite, same invocation, run against the pre-change source.** `src/environment/core.py`
was swapped for a copy taken from the throwaway worktree at `f3161dcc`, the full non-env suite
re-run, and the file restored (verified after: helper present, `git diff --numstat -- src/` →
`34 13 src/environment/core.py`). Result:

```
pre-change : 121 failed, 500 passed, 2 skipped, 18 errors in 2619.55s (0:43:39)
post-change:  53 failed, 578 passed, 2 skipped,  8 errors in 2998.85s (0:49:58)
```

**The pre-change tree fails *more* than the post-change tree — 139 failing/erroring node IDs
against 61.** Comparing the node-ID sets:

- **Exactly one** node ID fails post-change but not pre-change:
  `tests/algorithms/dreamer_srl/test_loss.py::test_symlog_distribution_matches_reference_formula`.
  Run on its own on the post-change tree it **passes** (`1 passed in 10.98s`). Order-dependent,
  not a B1 regression — and it has no environment dependency at all.
- **79** node IDs fail pre-change and pass post-change, every one of them in `tests/models/`
  (`test_modulation_sites.py` 53, `test_modulation_input_slice.py` 13, `test_gae_norm_mode.py` 5,
  `test_mc_fixed_mode.py` 3, `test_mc_raw_mode.py` 2, `test_network_construction.py` 2,
  `test_modulation_compat.py` 1). These are neural-network golden-comparison tests that touch no
  environment code whatsoever, and they flipped **79 results** between two runs whose only
  difference was a boolean reordering inside `jax_step`. That is the suite being order-sensitive
  (`pytest-randomly` reshuffles each run), not the code moving.

**(b) A like-for-like subset comparison, which is the clean measurement.** All 61 of the
post-change failures/errors live in nine modules. Running exactly those nine, pre and post:

```
pre-change subset : 35 failed, 201 passed, 8 errors in 259.97s
post-change subset: 36 failed, 200 passed, 8 errors in 236.11s
```

Node-ID set diff — **one line**:

```
> FAILED tests/test_provenance.py::test_write_provenance_writes_complete_valid_json
```

**(c) That one line is a demonstrated flake, not a regression.** Five identical repeats of that
single test on the unchanged post-change tree: **4 failed, 1 passed**. It fails on
`assert isinstance(rec["git_dirty"], bool)` receiving the string `"unknown"` —
`src/utils/provenance.py:82` returns `"unknown"` when its `git` subprocess exceeds
`_GIT_TIMEOUT_S = 10` (`:43`). On this NAS-backed repo with parallel sessions holding the index,
`git status` routinely takes longer than that — the exact slowness `CLAUDE.md` warns about. It
imports no environment code.

**Failure classes present in both runs, all pre-existing and all already in the registry:** ~41
`Strict Config: Configuration key 'sensory.visual_value_mode' is required but missing` (the
saved-run-config wall, two registry rows, and the A1 report recorded the same 41); the
`bush_dwell` → `bush_hiding` rename leaving one Dreamer eval assertion red (registry row, OPEN);
`tests/scripts/test_context_dependence_b0.py::test_b1_rest_rate` (`assert nan == 5.88…`, recorded
as pre-existing in the A1 report); the modulation golden trees; and
`test_evaluation_model_rebuild.py`'s topology mismatch. **Note `tests/test_trajectory_collection.py::test_v4_agent_in_bush_recomputed_in_numpy`
— the one test in the suite that independently re-derives `agent_in_bush` in NumPy and compares it
to the environment's own value, i.e. the perfect regression test for this commit — errors at
config load on `sensory.visual_value_mode`, identically before and after. It could not adjudicate
B1 and did not.**

#### Speed check — the first measurement was machine drift; the interleaved A/B is the real number

`git diff -- src/` is non-empty for the first time in this plan, so the waiver the earlier commits
legitimately took does not apply. Measured with the project's own harness,
`scripts/verification/bench_sensor_sps.py::sps_for` (128 envs × 200 steps under a jitted
`lax.scan`, best of 7, `PRNGKey(0)`), on **node 102, RTX 4090, GPU 0**, same config
(`configs/environment/default.yaml`), same seed, same step budget.

**A naive sequential before/after said −6.3%, and it was wrong.** The "before" was taken on a
freshly-idle machine at the very start of the session; the "after" came after ~25 minutes of CPU
test load. That is exactly the "re-run if anything else on the machine could have skewed the
result" case:

| case | naive before | naive after | naive Δ |
|---|---:|---:|---:|
| baseline (all features off) | 1,686,338 SPS | 1,579,987 SPS | **−6.31%** |
| BOTH (chosen settings) | 1,502,587 SPS | 1,384,093 SPS | **−7.89%** |

A boolean-equation reordering cannot cost 6%, so I re-measured properly: a throwaway
`git worktree` at `f3161dcc` (the A2 tip, i.e. the pre-change source — verified: 0 occurrences of
`agent_in_hiding_obstacle`), **interleaved** pre/post three times back to back on the same GPU.
The live tree was never stashed or checked out; the worktree was removed afterwards.

| case | pre r1 | post r1 | pre r2 | post r2 | pre r3 | post r3 | median pre | median post | **Δ** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 1,578,857 | 1,570,985 | 1,567,741 | 1,579,433 | 1,575,376 | 1,576,134 | 1,575,376 | 1,576,134 | **+0.05%** |
| BOTH | 1,392,995 | 1,396,111 | 1,388,594 | 1,387,165 | 1,469,685 | 1,391,072 | 1,392,995 | 1,391,072 | **−0.14%** |

**Verdict: 0% within noise**, as the plan predicts ("identical arithmetic behind a call JAX
inlines"). Both deltas are far inside the run-to-run spread visible in the pre-change column
itself (`BOTH` pre ranges 1.389M–1.470M, a 5.8% spread with **no code change at all**). Nothing to
escalate. The naive numbers are reported anyway rather than deleted, because the failure mode —
a 25-minute gap between "before" and "after" manufacturing an 8% regression — is worth having on
the record.

**JIT / recompile check.** `tests/env/test_no_recompile.py` → **3 passed** before, **3 passed**
after. No new recompilation is introduced: the helper is an ordinary Python function inlined at
trace time, and its only static branch (`obs_pos.shape[0] == 0`) keys on a shape that was already
part of the trace-cache key.

#### Known-bugs prior-art check — run, not skipped

`grep -in 'bush\|agent_in_bush\|hides_agent\|hunt_step\|refactor\|helper\|jaxpr\|recompil' docs/develop/active/issues/KNOWN_BUGS.md`,
plus `grep -in 'avoidance_stats_heatmap\|slot 0\|obstacle slot'`.

| What I touched / hit | Registry row |
|---|---|
| Environment step results are not bit-identical across *compilations* — one float32 ULP on `animal_property_sampled`, caused by code **near** a site flipping XLA's fusion choice | **Recorded, NOT A BUG** (2026-08-20). Directly relevant: my change reorders two equations in `jax_step`. Ruled out as a hazard here — the reordered ops are **boolean** (`and` / `eq` / `reduce_and` / `reduce_or`), which carry no rounding, and all four parity families assert exact float equality and passed unchanged. |
| `agent_in_bush` consumers in analysis tooling | **Recorded, OPEN** — `hiding_drivers.py:214` bins injury contemporaneously (`c0717e6f`). Not touched by B1 (B1 changes no values); it is B2's F10 concern. |
| The `bush_dwell` → `bush_hiding` rename leaving a red Dreamer eval test | **Recorded, OPEN, diagnosed.** Pre-existing; appears in pass 2 below and is not mine. |
| A refactor missing one of several copies of the same logic, latent for weeks | **Recorded, FIXED** — "Continual stage-transition crash … a large refactor missed one of six reset sites". This is the precedent that makes B1 worth doing at all. |

**One thing the registry does not record — owner `bug-curator`.** The concealment predicate exists
in **four** places repo-wide, not two. Besides the two in `core.py` that this commit merged:

- `scripts/eval/traj_collect/traj_scan.py:90–96` holds a **correct** third copy, structurally
  identical to the pre-B1 `jax_step` form including the empty-obstacle guard. Its docstring says
  it lives outside `src/` deliberately ("this plan touches no environment code") and that a
  verification step asserts it agrees with the env at every step. It also handles a case the
  helper does not: the reset row `t = 0`, where the env emits no `info` dict. **Out of B1's scope**
  (the plan says `core.py` only) and left alone — but it is now the only copy that can drift.
- `scripts/behavior_measures/avoidance_stats_heatmap.py:75–77` holds a **knowingly wrong** fourth
  copy: `bush = obs_pos[0]`, which hardcodes obstacle slot 0 and ignores both `obs_hides_agent`
  and `obs_active`. `traj_scan.py`'s docstring calls this out as "systematically wrong whenever
  bush count varies per episode — i.e. always, in a training environment. Do not copy that."
  **This defect is recorded only in that docstring — it has no row in `KNOWN_BUGS.md`.** The
  registry's only mention of this file is the unrelated `bush_dwell`/`bush_hiding` rename row.
  It feeds a published behaviour measure, so it is not cosmetic. Flagging rather than fixing, per
  scope; `bug-curator` owns the decision to file it.

So F9's *"The predicate exists twice today"* is true **within `core.py`** and incomplete
repo-wide. B1's contract ("one in-bush predicate") should be read as one predicate in the
environment core, which is what was delivered.

**Two further things the registry does not record, found while proving the non-env failures were
pre-existing — same owner, `bug-curator`:**

- **`tests/test_provenance.py::test_write_provenance_writes_complete_valid_json` is intermittently
  red on this machine, 4 failures in 5 identical repeats.** `git_dirty()`
  (`src/utils/provenance.py:82`) returns the string `"unknown"` when its `git` subprocess exceeds
  `_GIT_TIMEOUT_S = 10` (`:43`); the test asserts a `bool`. On a NAS-backed `.git` with parallel
  sessions the timeout is reachable in normal use. The registry has **no** provenance row.
- **`tests/models/` is heavily test-order-dependent: 79 node IDs flipped between two full-suite
  runs whose only difference was a boolean reordering inside `jax_step`** — code those tests never
  execute. `pytest-randomly` reshuffles each run, so the non-env suite cannot be used as a
  differential instrument at whole-suite granularity without `-p no:randomly`. The registry
  records two *stale-golden-fixture* rows but nothing about order dependence.

**One operational note, not a code defect.** A stale `.git/index.lock` was present for the second
half of this session (timestamp 07:12:51) with **no live `git` process** on the machine. Per
`CLAUDE.md` I did **not** delete it; I worked around it by copying `core.py` between file copies
instead of using `git checkout`. Worth a glance before the next git operation.

#### Plan errors found (three)

1. **B1 verification check 3 is unrunnable as written.** `grep -c 'jnp.all(.*obs_pos =='` →
   predicted **1**, measured **8 before / 7 after**. The pattern catches five unrelated
   `obs_blocking` sites. Corrected check given above.
2. **F9 undercounts the copies.** "The predicate exists twice today" is `core.py`-only; there are
   two further live copies under `scripts/` (one correct, one wrong). See the prior-art section.
3. **The briefing contradicts the plan on B1's third call site.** Full write-up in Deviation
   D-B1.1 above. This is the one that needs a decision before B2 is written, because B2's source
   differs depending on the answer.

#### Blockers / follow-ups

- **Decision needed before B2**: the D-B1.1 hoist question. B2's `update_body` gate either calls
  the helper (plan) or reads `info['agent_in_bush']` (briefing). Either works; they are not both
  written.
- **CP1 / D2 is still open** (does `rest_streak` reset when the agent leaves cover). The plan's
  own Checkpoints list it as unanswered and it blocks B2's source, not B1.
- `bug-curator` to decide whether three unrecorded items earn registry rows:
  `avoidance_stats_heatmap.py`'s slot-0 bush predicate, the flaky provenance test, and
  `tests/models/`'s order dependence.
- A stale `.git/index.lock` (07:12:51, no live git process) is sitting in the repo. Not deleted,
  per the project rule. Somebody with context should clear it.
- Scratch artefacts kept under `tmp/`: `20260915_b1_micro.py` (primitive-level comparison),
  `20260915_b1_jaxpr.py` + four `*_jaxpr_*.txt` captures, `20260915_b1_speed.py` +
  `*_speed_*.json`, `20260915_b1_apply.py` (the edit script),
  `20260915_b1_pass1_tests_env.log`, `20260915_b1_pass2_tests_rest.log`.

**Implemented by: `developer`**


### Commit B2 — `body.recovery_in_bush_multiplier` (no behaviour change at 1.0)

> **Implemented by**: `developer`
> **Date**: 2026-09-15
> **Status: IMPLEMENTED.** Tree left dirty, nothing staged, nothing committed. All four
> byte-parity families are at their post-A2 baselines (12 / 34 / 8 / 27) and **no `.npz` fixture
> moved**. **Read Deviation D-B2.1 first** — the mandatory key broke 29 archived configs that
> turn out to be live CI inputs, and the fix for that is the one thing in this commit that sits
> in tension with the "archived configs are NOT migrated" instruction.

#### Plain-language summary

A bush already hides the agent from a hunting predator and, since commit A1, physically blocks
animals from entering. This adds a third property: a setting that makes **resting inside a bush
heal injury faster than resting in the open**. It ships at `1.0` — "no difference" — so nothing
any agent does today changes. The point of shipping it inert is that the switch now exists and
can be turned on as a deliberate experiment.

The hard part was not the feature; it is four lines of code. The hard part is that the setting is
**mandatory** — every world file has to say what its value is, with no silent default — so every
configuration file the project loads directly had to gain one line, and every file that did not
gain one stopped loading. Most of that was planned. What was not planned is that a few dozen
files the project had already retired into an `archive/` folder turn out to be **loaded by the
test suite itself**, so retiring them was not the same as being able to break them.

#### What was implemented, file by file

| Group | Files | Change |
|---|---:|---|
| `src/environment/state.py` | 1 | `recovery_in_bush_multiplier: float = struct.field(pytree_node=False)` beside `recovery_accel_rate`, with a comment stating why it is static while its two siblings are traced. |
| `src/environment/config_loader.py` | 1 | `float(config.get_mandatory('body.recovery_in_bush_multiplier'))` read into a local above the `EnvParams(...)` call, validated `> 0` in the style of the thermal rate constants, then passed to the constructor. |
| `src/environment/core.py` | 1 | The gate inside `update_body`, immediately after `recovery_amount` is computed: a **trace-time** `if params.recovery_in_bush_multiplier != 1.0:` calling B1's `agent_in_hiding_obstacle(new_agent_pos, state.obs_pos, params.obs_hides_agent, state.obs_active)`. **26 insertions, 0 deletions** — the diff is purely additive. |
| `configs/environment/default.yaml` | 1 | `recovery_in_bush_multiplier: 1.0` after `recovery_accel_rate`, with the plan's comment block (inert, trace-time guard, D2 pointer, mandatory, `> 0`). |
| Rollout — the 11 maintained standalone configs | 11 | One inert line + 3 comment lines each: 5 `continual/nmn_double_return_stages/*`, 6 `configs/verification/*`. **Enumerated programmatically at the pre-change tree**, never hard-coded. |
| Inline-YAML test bases | 20 | 19 `.py` modules + `tests/fixtures/trajectory_collection/dual_format_config.yaml`. `test_visual_properties.py` carries **three** inline `body:` blocks, all three updated. |
| Frozen pre-A1 worlds | 3 + README | `tests/env/fixtures/frozen_parity_worlds/*.yaml` — 1 inert line each behind a 9-line comment explaining why a "do not update" file is being updated; README gains a "Mandatory keys added after the freeze" section with the rule and its one entry. |
| **Archived configs that are live CI inputs** | **29** | See **Deviation D-B2.1**. |
| New test | 1 | `tests/env/test_recovery_in_bush.py` — 7 tests. |
| Docs | 4 | `05_body_homeostasis.md`, `02_config_schema.md`, `CONFIG_GUIDE.md`, `CONFIG_CRITICAL_SETTINGS.md`. |

```
$ git diff --stat -- src/ tests/ configs/ docs/environment/
 72 files changed, 482 insertions(+), 16 deletions(-)

$ git diff --numstat -- src/
25  0  src/environment/config_loader.py
26  0  src/environment/core.py
 9  0  src/environment/state.py
```

No deletion anywhere in `src/`. The three lines the plan requires to survive verbatim
(`can_recover`, the `jnp.where` on `new_injury`, the clip) are untouched, and the blank line above
them keeps its original trailing whitespace so the diff is provably additive rather than
"additive apart from a reformat".

#### ⚠️ Deviation D-B2.1 — the mandatory key breaks 29 archived configs that the test suite loads. I gave them the inert line. This contradicts one line of the brief and I did not want to decide it silently.

**The brief says two things that collide here:**

1. *"Archived configs are explicitly NOT migrated."*
2. *"`test_unified_parity.py::_collect_configs` was deliberately left un-narrowed at 34. If any of
   those 34 are archived configs, a mandatory key will make them fail to load. Find out
   empirically, report what you find, and if it bites, say so rather than narrowing that collector
   on your own initiative."*

**It bites, and it bites harder than the brief anticipated.** Measured, in three stages:

| Stage | What was measured | Result |
|---|---|---|
| a | How many of `parity/`'s 34 fixtures are configs under `experiment/archive/` | **22** — and `test_unified_parity.py:153` `pytest.fail`s on a load error rather than skipping |
| b | `pytest tests/env/test_unified_parity.py` with the key mandatory | **22 failed, 12 passed, 324 skipped** |
| c | `pytest tests/env/test_visual_parity.py` | **2 failed, 6 passed** — `archive/hypervigilance/08-singlePredRabbit_disengage.yaml`, used both as a byte-parity fixture and by `test_visual_channel_layout` |
| d | The first full CPU-pinned `pytest tests/env/` | **73 failed, 326 passed, 374 skipped, 14 errors** — *every* failure a `body.recovery_in_bush_multiplier' is required but missing` load error |

Stage (d) is the part neither the plan nor the brief saw. It traces to **six further archived
files that A2 deliberately repointed live callers at one commit earlier**:

| Archived file | Loaded by |
|---|---|
| `archive/thermal/campfire_world.yaml` | `test_thermal_field`, `test_thermal_body`, `test_thermal_rendering`, `test_thermal_reward_gate`, `test_thermal_validation`, `test_thermoception`, `test_body_temperature_observation`, `test_metabolic_coupling`, `scripts/fixtures/generate_metabolic_coupling_fixture.py` |
| `archive/thermal/campfire_world_body_temp_hidden.yaml` | `test_body_temperature_observation` |
| `archive/v2_smoke/02-entities-distributional.yaml` | `test_distributional_yaml`, `test_per_episode_logging` |
| `archive/2X2_area.yaml` | `test_config_layer_silent_failures_20260723` |
| `archive/basic/00-5X5_NoPred.yaml` | `test_extends_layering` |
| `archive/dreamer_curriculum/01_food_only.yaml` | six modules under `tests/algorithms/dreamer_srl/` + `bench_sps.py` |

**Three options, and why I picked the third.**

- **Narrow `_collect_configs`** — explicitly forbidden by the brief, and it would delete 22 of 34
  fixtures' worth of evidence about a past refactor.
- **Ship it red** — faithful to both instructions and useless: 73 red tests and two dead gates.
- **Give those 29 files the inert line.** This is what I did.

**The argument, which is the frozen-worlds argument.** A gate that dies at *config load* preserves
no evidence at all; keeping a pinned test input loadable is part of keeping it frozen, not a
departure from it. The safety condition is that the added value must be provably inert, and here
it is proven three ways: the static guard means it emits no operation at `1.0`, the whole
`jax_step` jaxpr is byte-identical (below), and the fixtures themselves still match byte-for-byte
or the tests fail. Every one of the 29 files carries a comment saying **"NOT a migration of the
archive"** and naming the loader that needs the line.

**What it is NOT.** It is not a migration sweep. **The genuine, policy-conformant cost was measured
on both sides** by resolving all **326** configs under `experiment/archive/` through
`load_env_config` → `load_env_params`, in a throwaway worktree at `a8986c42` for the "before":

```
PRE  (worktree a8986c42) : 326 configs: 265 OK, 61 FAIL
POST (live tree)         : 326 configs: 229 OK, 97 FAIL
```

**36 archived configs become unloadable** — all 14 `sensory_ladder`, all 10 `sensory_directional`,
11 older `hypervigilance`, and `v2_smoke/01-entities-smoke.yaml`. **None is referenced by live
code**; the only hits in a basename sweep are one comment line in three
`configs/trajectory_collection/` files, and a **pre-existing** stale path at
`tests/env/test_entities_schema.py:45` that names `configs/experiment/v2_smoke/…` with
`environment/` missing and has therefore never resolved (guarded, so not red — flagged to
`bug-curator` below). The two sensory families are already the "regenerate from the generator, do
not resurrect the stale YAML" set (F11), so this costs nothing that was not already written off.

**Revert instruction, if you disagree**: `git checkout -- $(git status --short -- configs/environment/experiment/archive/ | awk '{print $2}')`.
That restores all 29 files and returns the suite to 73 red in `tests/env/` plus 22 + 2 red across
two parity families. Nothing else in this commit depends on them.

#### Other deviations

**D-B2.2 — `SAVED_RUN_CONFIG_COMPAT.md` was NOT touched, deliberately.** The plan's B2 doc list
says to append one line to its key table. The brief forbids staging that file (a parallel session
has it **modified and staged**), and the brief's own "Docs that ride in this commit" list omits
it. Editing a file another session has staged would put my line under their commit. **Left alone;
named as a follow-up.** The same applies to `docs/develop/INDEX.md`, so
`scripts/claude/regen_dev_index.py` was **not** run even though this plan doc's
`last_updated` moves.

**D-B2.3 — two tests beyond the plan's five.** The plan specifies 5 tests; the file has 7. The
additions are `test_shipped_value_is_inert_and_a_float` (pins the `float()` coercion the plan
itself calls "load-bearing" but gives no test for — it asserts a YAML `1` and a YAML `1.0` produce
the *same* Python float, which is the whole point of the coercion) and
`test_non_positive_multiplier_raises` (pins the `> 0` validation the plan asks for in the loader).
Both are additive; the plan's five are present unchanged.

#### The inertness proof, measured two ways

**1 — source-level, which is the standard the plan asks for.** The gate is
`if params.recovery_in_bush_multiplier != 1.0:` on a `pytree_node=False` field, i.e. an ordinary
Python branch evaluated once at trace time. At `1.0` its body is never executed, so nothing it
would emit exists.

**2 — measured at the whole-`jax_step` graph, against a worktree.** `configs/environment/default.yaml`
traced end to end in the pre-change worktree and in the live tree:

```
PRE  (worktree a8986c42, key ABSENT) : sha1 2b5d57e7c82e
POST (live tree, multiplier 1.0)     : sha1 2b5d57e7c82e
diff -q /tmp/b2_jaxpr_pre.txt /tmp/b2_jaxpr_post.txt  ->  JAXPRS BYTE-IDENTICAL
```

The emitted program is literally the same text. Nothing downstream of it can differ.

#### Verification — B2.1 to B2.8, every number re-derived

**B2.1 — all four byte-parity families, and no fixture moved.** Measured separately, before the
source change and again at the final tree:

| Family | Test module | Before (pre-B2) | After (final tree) | Δ |
|---|---|---|---|:--:|
| `thermal_parity/` | `test_thermal_parity.py` | 12 passed, 20 skipped | **12 passed, 20 skipped** | — |
| `parity/` | `test_unified_parity.py` | 34 passed, 324 skipped | **34 passed, 324 skipped** | — |
| `visual_parity/` | `test_visual_parity.py` | 8 passed | **8 passed** | — |
| `directional_sensors/` | `test_directional_sensors.py` | 27 passed | **27 passed** | — |

All four match the required post-A2 sizes exactly.

```
$ git status --short tests/env/fixtures/
 M tests/env/fixtures/frozen_parity_worlds/README.md
 M tests/env/fixtures/frozen_parity_worlds/environment__default.yaml
 M tests/env/fixtures/frozen_parity_worlds/environment__experiment__basic__01-slow_predator_5x5.yaml
 M tests/env/fixtures/frozen_parity_worlds/environment__experiment__basic__02-predator_and_rabbit_10x10.yaml
```

**Zero `.npz` touched** — none modified, none added, none deleted. The four entries above are the
frozen-world YAML *inputs* and their README, changed deliberately; the `diff` against
`git show f02e76b9:configs/environment/default.yaml` shows **only** the 10-line block and nothing
else, and the README's verification command was updated to say so.

**B2.2 — the new tests, red before and green after.** Written first and run on the untouched tree
(`tmp/20260915_b2_tests_PRECHANGE.log`):

```
PRE-CHANGE : 5 failed, 2 passed
  FAILED test_missing_key_raises                  - default.yaml does not ship the key at all
  FAILED test_shipped_value_is_inert_and_a_float  - 'EnvParams' object has no attribute ...
  FAILED test_non_positive_multiplier_raises      - DID NOT RAISE <class 'ValueError'>
  FAILED test_multiplier_one_is_graph_identical   - 'EnvParams' object has no attribute ...
  FAILED test_premium_applies_in_bush             - ACTUAL 0.099998 / DESIRED 0.299995
  (passed: test_premium_requires_rest_and_no_damage, test_streak_not_location_dependent)

POST-CHANGE: 7 passed in 11.47s
```

The plan requires the first three to be red pre-change; **all three are**, and so are my two
additions. The two that pass pre-change are the two the plan does not list among them, and they
pass for the right reason: with no gate in the source there is no premium to leak outside the rest
condition, and `rest_streak` was already action-only.

`test_premium_applies_in_bush` failing at exactly **0.0999 vs the required 0.2999** is the useful
part of that log — the pre-change tree heals `recovery_base_rate` and nothing more, so the test is
measuring the multiplier and not something incidental.

**A note on `test_premium_requires_rest_and_no_damage`, because it was wrong on the first pass.**
Its "in the bush but not resting" branch originally used a one-cell bush, and **every** move
action leaves a one-cell bush — so the test failed with "no move action left the agent on a bush
cell" and would have proved nothing. Fixed by giving that branch a **two-cell** bush patch, so a
sideways step stays inside cover and the branch actually isolates "not resting" from "not in a
bush". Recorded because a test that fails for a bookkeeping reason looks identical, in a summary
line, to one that fails for the right reason.

**B2.3 — migration completeness, captured at the pre-change tree so it cannot be a tautology.**

```
(a) pre-change enumerator -> tmp/20260915_b2_target_configs.txt : 11 files + default.yaml = 12
(b) every path in that SAVED list now carries the key           : b_fail=0  (n=12)
(c) enumerator re-run after the change, diffed against (a)      : IDENTICAL (12 files)
```

(c) is the half that can actually fail: fewer entries would mean a config that used to load no
longer does, which (b) alone is blind to.

**B2.4 — the 7 `basic/*` files are untouched and inherit anyway.**

```
$ git diff --name-only -- configs/environment/experiment/basic/
(empty)
```
```
     1.0 float  configs/environment/default.yaml
     1.0 float  .../basic/00-static_predator_5x5.yaml
     1.0 float  .../basic/01-slow_predator_5x5.yaml
     1.0 float  .../basic/02-predator_and_rabbit_10x10.yaml
     1.0 float  .../basic/03-random_init_10x10.yaml
     1.0 float  .../basic/03-random_init_10x10_ckpt1k.yaml
     1.0 float  .../basic/04-jump_attack_10x10.yaml
     1.0 float  .../basic/05-sensory_noise_10x10.yaml
```

8/8 resolve through `load_env_config` → `load_env_params` to `1.0`, **as a Python `float`** — the
type is checked, not assumed, because that is what the trace-cache-key coercion is for.

**B2.5 — `test_no_recompile.py` → 3 passed.** A constant multiplier introduces no recompilation.
(A *changed* multiplier recompiling is intended and is what the static field buys.)

**B2.6 — `CONFIG_CRITICAL_SETTINGS.md`** carries a registry row and a dated 2026-09-15 change-log
entry. The entry states the sixth-key fact plainly and says the guide note **does not** fix the
saved-run population, rather than implying it does; it also carries the D-B2.1 measurements
(22 / 2 / 73 red, the 29 files, the 265→229 loadability delta) so the cost is on the record with
its numbers.

**B2.7 — the F10 pre-B2 snapshot exists.**
`scripts/analysis/hiding_drivers.py --run results/JAX_RecurrentPPO/20260810-185749_rppo_restprem_a01_n106`,
output at **`tmp/20260915_b2_hiding_drivers_preB2/`** (`univariate.csv`, `multivariate.csv`,
`summary.json`, `aggregate.npz`), log at `tmp/20260915_b2_hiding_drivers_preB2.log`. Worth one
clarifying note for whoever uses it: that script reads the *saved trajectory store* and the run's
saved config YAML directly and never builds `EnvParams`, so B2 cannot change its output for
already-collected data at all. The snapshot's value is as a reference for **future** runs trained
at a non-`1.0` multiplier, which is the confound F10 actually describes.

**B2.8 — speed. Two measurements, and the first one was wrong in exactly the way B1 warned about.**
Node 102 (this container), RTX 4090 GPU 0, `CUDA_VISIBLE_DEVICES=0`, project harness
`scripts/verification/bench_sensor_sps.py::sps_for` (128 envs × 200 steps under a jitted
`lax.scan`, best of 7, `PRNGKey(0)`), same config, same seed, same budget. "Pre" is a throwaway
`git worktree` at `a8986c42`; the live tree was never stashed or checked out.

*First attempt — 3 reps, always pre-then-post:*

| case | median pre | median post | Δ |
|---|---:|---:|---:|
| baseline | 1,613,987 | 1,576,313 | **−2.33%** |
| BOTH | 1,480,548 | 1,382,333 | **−6.63%** |

−6.63% is past the plan's 5% discussion threshold, so it was not accepted. It cannot be real: the
whole-`jax_step` jaxpr is **byte-identical** (sha1 `2b5d57e7c82e` both sides), so there is no
instruction for a regression to live in. The tell is inside the numbers — the "pre" column alone
spans 1.381M–1.510M, a 9% spread with no code change at all, and a fixed pre-then-post order lets
any drift inside a rep land entirely on "post".

*Second attempt — 6 reps with the order alternating per rep:*

| case | pre (min / median / max) | post (min / median / max) | **Δ median** |
|---|---|---|---:|
| baseline | 1,568,514 / **1,577,023** / 1,593,020 | 1,570,678 / **1,591,883** / 1,693,757 | **+0.94%** |
| BOTH | 1,384,652 / **1,389,585** / 1,498,092 | 1,380,380 / **1,384,692** / 1,392,954 | **−0.35%** |

**Verdict: 0% within noise**, and the noise floor is visible in the table — a 1.69M outlier on the
*post* side and a 1.50M outlier on the *pre* side, i.e. ±7% excursions in both directions with
identical emitted code. Nothing to escalate. Raw numbers kept at `tmp/20260915_b2_speed_ab.json`
and `tmp/20260915_b2_speed_ab_6reps.json`; both attempts are reported rather than only the one
that agrees with the source argument.

#### Both documented passes

**Pass 1 — `JAX_PLATFORMS=cpu pytest tests/env/ -q`:**

```
413 passed, 374 skipped, 1 warning in 630.63s (0:10:30)      exit 0
```

**Green, and the delta is exactly the new file.** B1 recorded **406 passed, 374 skipped** on the
same invocation; `tests/env/test_recovery_in_bush.py` adds 7. No pre-existing test changed state.
(The intermittent whole-directory abort recorded for A1 did not fire.)

**Pass 2 — `pytest tests/ --ignore=tests/env -q`** (no pin, as documented):

```
54 failed, 577 passed, 2 skipped, 1019 warnings, 8 errors in 3639.59s (1:00:39)
```

B1's figure on the same invocation was 53 failed / 578 passed / 8 errors. **Not one of the 62
failing node IDs is caused by B2**, and that is measured rather than asserted:

1. **The direct check.** `grep -c 'recovery_in_bush_multiplier'` over the pass-2 log → **0**.
   Every config error in the run is the *other* key: `grep -o "Configuration key '[^']*'"` returns
   **81 × `sensory.visual_value_mode`** and nothing else. That is the saved-run-config wall, which
   has two rows in `KNOWN_BUGS.md` and was reported at the same size (41 node IDs in
   `tests/test_trajectory_collection.py`) in both the A1 and B1 reports.
2. **Like-for-like subset, pre vs post, `-p no:randomly`**, over the nine modules that hold all 62:

   ```
   post : 38 failed, 188 passed,  8 errors in 951s
   pre  : 15 failed, 168 passed, 51 skipped in 457s
   ```

   **The pre side is not a valid comparator for one module, and saying so is part of the result.**
   A `git worktree` does **not** carry gitignored data, so `/tmp/b2_pre_worktree/results/` does not
   exist — and `tests/test_trajectory_collection.py::_base_cfg()` loads a saved run config from
   `results/`. In the worktree that module **skips** (51 skipped); in the live tree it fails at
   `visual_value_mode`. The 38-node-ID gap is entirely that module. This is a real limitation of
   the worktree A/B technique and worth remembering: it is a clean instrument for `src/` and a
   blind one for anything that reads gitignored data.
3. **The remaining differences are the two order/flake effects B1 already documented.** Eight
   `tests/models/test_modulation_*` golden tests fail **pre** and pass **post** (they execute no
   environment code at all), and `tests/test_provenance.py::test_write_provenance_writes_complete_valid_json`
   fails **post** only — the recorded NAS/`git`-timeout flake where `git_dirty()`
   (`src/utils/provenance.py:82`) returns the string `"unknown"` past `_GIT_TIMEOUT_S = 10` and the
   test asserts a `bool`.

#### Known-bugs prior-art check — run, not skipped

`grep -in 'recovery\|mandatory\|rest_streak\|bush\|in_bush\|static field\|recompil' docs/develop/active/issues/KNOWN_BUGS.md`.

| What I touched / hit | Registry row |
|---|---|
| A new mandatory key widening the saved-run wall | **Recorded, OPEN** — "A finished run's own saved config stops loading once a new key becomes mandatory". It **already names `body.recovery_in_bush_multiplier` by name** as the sixth key, from the planning pass. No new row needed; the row's own count (493 frozen configs, 33 rebuild) is what the `CONFIG_GUIDE.md` note cites. |
| Tree configs left unmigrated by a mandatory key | **Recorded, OPEN** — "Mandatory config keys keep landing without migrating the archive — 68 stand-alone configs no longer load". This change moves that population; the measured delta (265 → 229 loadable of 326 archived) belongs to that row and is recorded in the registry change log here. **`bug-curator` may want to refresh the row's count.** |
| A recovery change confounding `hiding_drivers.py`'s contemporaneous injury binning | **Recorded, OPEN** — the row says in as many words *"a planned location-dependent recovery change … shifts the per-step injury trajectory"*. This is that change. Snapshot taken (B2.7); nothing fixed, per scope. |
| `test_provenance` NAS/git-timeout flake, `tests/models/` order dependence | Raised by B1 as unrecorded, owner `bug-curator`; **still unrecorded**, and both reproduced here. |
| The `bush_dwell` → `bush_hiding` rename leaving one Dreamer eval assertion red | **Recorded, OPEN, diagnosed.** Present in pass 2, pre-existing, not mine. |

**Believed unrecorded — I name `bug-curator` as owner** (I cannot spawn it):

- **`tests/env/test_entities_schema.py:45` points at `configs/experiment/v2_smoke/01-entities-smoke.yaml`** —
  a path with `environment/` missing that has never existed. The test guards on `os.path.isfile`
  and therefore reports green while asserting nothing about the file it names. Pre-existing and
  unrelated to B2; found while sweeping for live references to the 36 newly-unloadable configs.
  Same class as the recorded `test_extero_noc_parity` incident ("reported 3 skipped — green — for
  three months while testing nothing").
- **A `git worktree` is a blind instrument for any test that reads gitignored data.** Not a code
  defect, but it silently changes a test's *outcome class* (skip vs. fail) rather than erroring,
  and both B1 and B2 used worktree A/B as the project's standard differential technique. Worth a
  line somewhere a future implementer will read.

#### Plan errors found (three)

1. **F7's rollout is complete for the tree but blind to the archive's CI role.** "The 227 archived
   configs are out of scope by policy" is true of the *policy* and false of the *test suite*:
   **29** archived configs are loaded by `tests/` or by a fixture generator, and the mandatory key
   made **97** tests red across three gates before they were migrated. F7 reasons from
   `test_thermal_parity.py`'s collector (which A2 narrowed) and never asks which *other* collectors
   and hard-coded paths reach into `archive/`. The general form of the lesson is A2's own Plan
   error 2, one level up: **sweep for who LOADS a config, not for which directory it lives in.**
2. **The B2 doc list asks for an edit to `SAVED_RUN_CONFIG_COMPAT.md`, which the brief forbids
   touching.** See D-B2.2. The brief's own doc list already omits it, so the two are reconcilable
   — but the plan text still says to edit it, and a later reader following the plan alone would.
3. **The plan's B2 File Changes never mentions `tests/env/fixtures/frozen_parity_worlds/`.** That
   is not the plan's fault chronologically — the directory was created by A1's blocker resolution,
   after B2 was written — but it is now a **fourth** category of file that every future mandatory
   key must migrate, alongside standalone configs, inline-YAML test bases, and (per error 1)
   archived CI inputs. `CONFIG_GUIDE.md` §5 step 2 lists only the first two; the new §5 item 5 added
   here covers the static-field pattern but not the frozen-worlds category. **Named for
   `senior-developer`** rather than edited, because amending the guide's migration checklist is a
   contract change, not an implementation detail.

#### Blockers / follow-ups

- **D-B2.1 needs your ruling.** The 29 archived files either keep the inert line (suite green,
  gates alive) or lose it (suite red, `parity/` 34 → 12 in practice). Revert command is in D-B2.1.
- **`SAVED_RUN_CONFIG_COMPAT.md`** still needs its one-line table entry for this key, plus, when
  the compatibility layer lands, an era-representative fixture — so the *seventh* mandatory key is
  a red test rather than a failed analysis. Owner: whoever owns that plan; the file is currently
  staged by a parallel session.
- **`docs/develop/INDEX.md` not regenerated.** `scripts/claude/regen_dev_index.py` was not run
  because the index is modified **and staged** by a parallel session.
- **`bug-curator`**: the stale `test_entities_schema.py:45` path, the worktree/gitignored-data
  blind spot, and (still open from B1) the `test_provenance` flake, `tests/models/` order
  dependence, and `avoidance_stats_heatmap.py`'s slot-0 bush predicate.
- **`experiment-analyzer`**: do not compare `hiding_drivers.py` output across this commit for any
  agent trained at a non-`1.0` multiplier. The two published pages
  (`a01_hiding_drivers.html`, `hiding_factor_atlas.html`) are **not** invalidated — they report
  agents trained before this, and at `1.0` nothing about those agents changes.
- Throwaway `git worktree` at `/tmp/b2_pre_worktree` **removed** after the measurements; the live
  tree was never stashed, checked out, or cleaned.
- Scratch artefacts under `tmp/`: `20260915_b2_target_configs.txt`, `..._archived_fixtured_configs.txt`,
  `..._still_missing.txt`, `..._prechange_parity.log`, `..._postchange_parity.log`,
  `..._final_families.log`, `..._tests_PRECHANGE.log`, `..._pass1_tests_env.log`,
  `..._pass2_tests_rest.log`, `..._subset_POST.log`, `..._speed_ab.json`, `..._speed_ab_6reps.json`,
  `..._hiding_drivers_preB2/`.

#### Working-tree state at hand-off

Dirty and **uncommitted**. **Nothing staged by me.** 72 tracked files modified + 1 new
(`tests/env/test_recovery_in_bush.py`). Files belonging to parallel sessions — untouched, and two
of them **staged by that session**: `docs/develop/INDEX.md` (staged),
`docs/develop/active/refactors/SAVED_RUN_CONFIG_COMPAT.md` (staged),
`docs/develop/active/meta/artifact_format_bugs.md`, `docs/diary/2026-09-14.md`,
`docs/diary/2026-09-15.md` (untracked), and the `docs/experiments/active/sensor_ladder/figures/*.svg`.
Commit B2 with an **explicit pathspec** over its own 73 files.

**Implemented by: `developer`**

## Verification Report

> **Verified by**: `senior-developer`
> **Date**: 2026-09-15
> **Scope**: commit A1 only (uncommitted working tree), plan-adherence + judgement.

### What was checked, in plain English

A1 was meant to be a four-value settings change — a bush now stops an animal walking into it —
plus the paired documentation the project's config contracts require. Part-way through, three
*other* test suites went red because they compare today's world against snapshots of an older
one; the user's answer was to freeze the old world as a test input rather than re-take the
snapshots. This report asks two things: does what is in the working tree match what the plan
(as amended) says A1 is, and is the freeze actually sound rather than merely well-described.

**Verdict: APPROVED, with two documentation fixes to make in this same commit.** The behaviour
change is exactly the four files the plan named; the frozen worlds were verified to be a true
pre-change copy by an independent route (not by trusting the comment, and not only by the gates);
the paired config contracts are satisfied. The one real gap is that the permanent dated record in
the critical-settings registry still tells the *pre-blocker* story — it says one fixture moved and
never mentions the three other families or the new frozen-worlds directory.

### Per-file adherence

| Commit | File | Change | Status | Notes |
|---|---|---|:--:|---|
| A1 | `configs/environment/default.yaml` | `blocks_animals: false → true` + 7-line comment | ✅ | Matches the plan's snippet verbatim, bush entry only. |
| A1 | `…/experiment/basic/01-slow_predator_5x5.yaml` | key added to bush entry | ✅ | Bush entry only. |
| A1 | `…/experiment/basic/02-predator_and_rabbit_10x10.yaml` | key added to bush entry | ✅ | Bush entry only. |
| A1 | `…/experiment/basic/03-random_init_10x10.yaml` | key added to bush entry | ✅ | `rock` entry untouched, as specified. |
| A1 | `…/experiment/basic/00-static_predator_5x5.yaml` | **not touched** | ✅ | Correct, and for F3's amended reason (`obstacles: []`, `n_obs = 0`), re-confirmed at the loader here. |
| A1 | `src/environment/config_loader.py:1851` | fallback retained | ✅ | Unchanged; line citation re-checked and correct. |
| A1 | `docs/environment/CONFIG_CRITICAL_SETTINGS.md` | registry row + dated change-log entry | ⚠️ | Both present, incl. the no-fallback-defaults exception and the explicit "this change deliberately alters behaviour" statement. **But the entry predates the blocker resolution**: see Finding 1. |
| A1 | `docs/environment/02_config_schema.md` | Obstacle-fields row + note + static-defaults row | ✅ | Paired-contract half 1. Minor stale line citations noted (Finding 4). |
| A1 | `docs/environment/CONFIG_GUIDE.md` | §1 "sharper edge" worked example | ✅ | Paired-contract half 2, same change. Satisfies Maintenance Contract §2 and §4. |
| A1 | `docs/develop/active/refactors/BUSH_BLOCKS_ANIMALS.md` | spawn caveat marked stale | ✅ | **In scope, not creep** — named in the plan's A1 doc list. Edit confined to the caveat + `last_updated`. |
| A1 | `tests/env/fixtures/thermal_parity/configs__environment__default.npz` | regenerated | ✅ | Exactly one fixture, none added, 72 files still present. |
| A1+ | `tests/env/fixtures/frozen_parity_worlds/` (4 new) | frozen pre-A1 worlds + README | ✅ | Equivalence independently verified — see below. |
| A1+ | `tests/env/test_visual_parity.py` | `_FROZEN` + `_SLUG_OVERRIDE` | ✅ | Slug override lands on three fixture files that exist, so the generate-on-missing branch cannot fire. |
| A1+ | `tests/env/test_unified_parity.py` | `_FROZEN_LOAD_PATH` | ✅ | Slug still from the original path; only `default.yaml` repointed. |
| A1+ | `tests/env/test_directional_sensors.py` | reads `cap.PARITY_WORLD` | ✅ | npz key unchanged. |
| A1+ | `scripts/verification/capture_sensor_baseline.py` | `PARITY_WORLD`, `CONFIGS` list → dict | ✅ | Sole code caller is the test above, updated. `--capture` still keys by the original config path. |
| A1 | speed check | skipped | ✅ | Legitimately waived: `git diff -- src/` is empty; `obs_blocking \| obs_blocks_animals` (`core.py:560`) already ran every step on an all-False array. Same shapes, same ops, same traced graph. **No regression.** |

### The frozen worlds — verified independently, not from the comment

The load-bearing claim is that `basic/01` and `02` are **pre-resolved** rather than byte copies,
because `extends:` targets resolve only under `configs/`, so a byte copy would still have read the
live (now changed) base. Verified by re-deriving, not by reading:

- A throwaway `git worktree` at the frozen commit `f02e76b9` (removed afterwards; the live tree was
  never stashed or checked out). `git diff f02e76b9 HEAD -- configs/ src/` is **empty**, so the
  frozen commit really is the pre-A1 state of both the configs and the loader.
- For `default`, `basic/01` and `basic/02`: `load_env_config(<original>)` in the worktree vs.
  `load_env_config(<frozen copy>)` in the live tree, compared as (a) the **full merged config dict**
  and (b) all **189 `EnvParams` fields** (dtype, shape, content hash). **Identical in all three
  cases, on both comparisons.** The inlined resolution is exactly what the loader would have
  produced.
- `environment__default.yaml` is header-comment + byte-identical body to `git show f02e76b9:…`.
- The equivalence therefore rests on three independent legs — the pinned fixtures reproducing
  byte-for-byte (the developer's gate runs), the loader-level re-derivation above, and the
  provenance-from-git of the copies — not on a comment.
- No collector can pick the frozen worlds up as configs: all three (`test_thermal_parity`,
  `test_backward_compat_configs`, `test_unified_parity`) glob under `configs/` only. Putting them
  under `tests/env/fixtures/` is what makes that structural.

### Findings

**1 — ⚠️ Fix before committing. The critical-settings change-log entry still tells the pre-blocker
story.** `CONFIG_CRITICAL_SETTINGS.md`'s 2026-09-14 entry says the change reddened "exactly 1 of
72" fixtures "with 71 untouched, matching the pre-registered prediction", and stops there. It never
mentions that three further byte-parity families went red, that five more fixtures were affected,
or that `tests/env/fixtures/frozen_parity_worlds/` now exists because of this change. The registry
is the project's durable dated record of exactly this kind of decision; as written, a future reader
who finds the frozen-worlds directory and greps the registry for why it exists finds nothing, and a
reader who trusts the entry concludes A1's fixture footprint was one file. Append two or three
sentences: the four families, the 1-regenerated-plus-3-frozen split, and the rule that
`thermal_parity/` tracks the live world while the other three pin past refactors.

**2 — ⚠️ Fix before committing (cheap). The Implementation Report's diff stat and "Open question"
are pre-resolution.** The `git diff --stat` block (plan lines 709–720) lists 9 files / 99
insertions — the shape of A1 *before* the freeze. The commit is actually 13 modified + 4 new files.
Keeping the blocker narrative intact is right and was a deliberate call, but the report has no
consolidated final file list for what is about to be committed, and A1.5 ("no collateral") was never
re-run against the enlarged scope. Likewise the "Open question for the plan owner" subsection still
closes with "Until that is decided, `tests/env/` is red in three files on this tree", which the
section immediately below it contradicts. Add a final consolidated stat + a `RESOLVED — see below`
marker on that heading.

**3 — Follow-up. The freeze is applied by observed redness, not by which worlds A1 changed.**
`test_visual_parity.py` still reads the **live** `basic/03` and `basic/04` — and `basic/03` is one
of the four worlds A1 edited (`04` extends it). Those two compare a post-A1 world against a
pre-refactor fixture and pass, which the Implementation Report flagged as "one curiosity". So they
pass *empirically* (no animal contested a bush cell within that config's scripted 1000 steps), not
*by construction*, and the suite's stated contract — "these fixtures pin a past refactor" — is now
honoured for 3 of the 5 affected entries. The in-code comment says the others read the live tree
"deliberately" without saying why that is safe. Either freeze `03`/`04` too (cheap, changes no
observable behaviour since their fixtures already match) or name them explicitly in the comment and
the README with the reason.

**4 — Follow-up. Two stale line citations.** In `02_config_schema.md`'s static-vs-dynamic defaults
table, the per-obstacle `blocking` / `hides_agent` / `blocks_animals` rows cite
`config_loader.py:704/705/706`; those lines are thermal-validation logging. The real reads are
`:1849/:1850/:1851`. Pre-existing for all three rows, but A1 edited the `blocks_animals` row without
fixing its citation. Separately, `scripts/verification/capture_sensor_baseline.py` has **no row** in
`SCRIPTS_DEPENDENCY_MAP.md` at all — also pre-existing (the Maintenance Contract does not fire here:
no file under `scripts/` was added, moved, renamed or deleted, and no caller was added or removed),
but the map's per-file roll-up is meant to be complete.

**5 — Follow-up, recommended soon. The 8-world loader invariant has no committed test.** A1.3 —
`not (obs_hides_agent & ~obs_blocks_animals).any()` across the 8 maintained worlds, 8/8 — was run as
a one-off script and pasted. `tests/env/test_bush_blocks_animals.py` exercises the *mechanism* on
inline YAML and asserts nothing about the shipped worlds. Nothing now stops a future config edit
from silently reverting a maintained world to a permeable bush, which is the exact hazard
`CONFIG_GUIDE.md` §1 was just extended to warn about — and the guide tells authors to check it with
that assertion. A ~10-line parametrized test over the 8 worlds would make the guide's advice
enforced rather than advisory.

**6 — Commit hygiene, not a defect.** The working tree carries several files from parallel sessions,
two of them **staged**: `docs/develop/INDEX.md` and `docs/develop/active/refactors/SAVED_RUN_CONFIG_COMPAT.md`
(staged by another session), plus `docs/develop/active/meta/artifact_format_bugs.md`,
`docs/diary/2026-09-14.md`, and figure files under `docs/experiments/`. Commit A1 with an explicit
pathspec over its own 17 files (13 modified + 4 new) plus this plan doc, which is still untracked.
Note as a consequence that `INDEX.md` already lists both plan docs at `updated 2026-09-14` but that
change belongs to the other session — the A1 commit will land without it, and that is correct.

**Conclusion**: A1 matches the plan as amended — four settings files, the deliberate `basic/00`
omission for the corrected reason, the retained loader fallback, the paired doc contracts — and the
frozen-worlds fix is sound: the pre-resolved copies were independently re-derived to be exactly what
the loader produced at the pre-change commit, and the slug-override closes the self-rebaselining
trap. **Approved to commit once Findings 1 and 2 (both documentation edits, same commit) are made;
Findings 3–5 are follow-ups.**
