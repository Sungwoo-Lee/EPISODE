---
title: "Basic Behaviour Analysis: water (pond time, hydration, pond features, thirst deaths) for the 18 thirst-task runs"
topic: behavior
status: active
created: 2026-10-02
last_updated: 2026-10-02
---

# Basic Behaviour Analysis — adding water

> **Status**: DRAFT plan, awaiting plan review. Nothing implemented.
> **Owner of the pipeline**: the hypervigilance session (grid-world-pain-d9). This plan's water
> parts are written by the thirst session in its own commits, with that session reviewing the diff.
> **Parent plan**: [[BASIC_BEHAVIOUR_ANALYSIS_PIPELINE]] · **Runs**: [[THIRST_TASK]] ·
> **Pond-replay method**: [[THIRST_PILOT]] §4.2 · **Probe scenes**: [[SINGLE_CHANNEL_SMELL_HYPERVIGILANCE]]
> ("Probe-scene sweep (exploratory)")

## Context

The Basic Behaviour Analysis is a reusable pipeline that reads stored greedy-policy episodes of any
trained population and builds one web page: how often the agents do five things (hide in a bush,
eat, stay near a rabbit, stay near a predator, stand on a warm square), how episodes end, what
per-episode conditions push those behaviours up or down, and how the agents behave in fixed test
scenes. It was built for worlds without water.

The grid world now has **thirst**: one **pond** per episode, a **hydration** level that drains each
step and rises only while the agent stands on the pond, and two new ways to die (dying of thirst,
and over-drinking). Eighteen training runs are under way in the **thirst task** — an ordinary and a
modulated agent, one run each, in nine worlds (map 10×10, 15×15 or 20×20, crossed with smell that
carries across the whole map, 5 squares, or 3 squares).

This plan lets the pipeline build its page for those 18 runs. It adds a **sixth behaviour, "time on
the pond (drinking)"**; treats **start hydration** as a condition the world sets at random each
episode; adds **current hydration** to the "behaviour by body state" panels; records the **pond's
size and which corner it sits in**; and names the two new death causes. No data-collection code
changes: hydration is already in the stored observations, and the pond's position is rebuilt from
each episode's random seed — a method the thirst pilot validated over 25 million steps with zero
exceptions. Because each world × agent has only **one** run, the cross-run comparison step refuses
by design and the page says so. The existing reference checks stay byte-identical, and a new
check proves the pond numbers against an independent count.

## Analysis

### What the store gives (schema 1, no change)

- `obs_true` carries **Hydration** = hydration / `water.max_hydration` (`sensor.py:514-519`), one
  number, placed right after Body Temperature (`sensor.py:610-613`). Level 06 has perceptual noise
  off, so `obs_true` equals what the agent saw. The store has **no** hydration column and **no**
  pond position.
- The pond is fixed for the episode. `jax_reset` draws it from `params.water_topleft_table` with a
  fold-in of the placement key (`core.py:1884-1894`); `water_pos` has `h·w` rows (4, 9 or 16 cells
  at 10/15/20). Standing on a pond cell after the move is drinking (`core.py:1205`); hydration is
  `clip(W − drain + gain·[drank], 0, max)`, with death at 0 (code 6) and at max (code 7)
  (`core.py:591-606`, `1246-1251`).
- Pilot reader (`results/analysis/thirst_pilot/readout/code/store_reader.py`): builds params from
  the run's saved `models/config.yaml` → `apply_saved_config_compat` → `load_env_params`,
  `jax.vmap(jax_reset)` over `PRNGKey(episode_seed)`, then checks (1) start cell == stored t=0 cell
  every episode and (2) every step t→t+1: hydration rose ⇔ stored cell at t+1 is a pond cell. It
  hard-codes the Hydration index (`H_IDX = 2`) and 200 — the pipeline must not.

### Where the current pipeline would go wrong on a water world

| # | Place | Problem |
|---|---|---|
| W-a | `registry.WORLD_BLOCKS` | does not include `water`, so `random_start_hydration` and the pond-corner draw are invisible to the audit — silently unmeasured rather than "unhandled" |
| W-b | `registry.audit`, `_low/_high` branch | if `water` were simply added, `start_hydration_low/_high` would hit the `start_` branch, look up **`body.random_start_hydration`** (absent) and be stamped "not a draw" — a wrong claim. The lookup must use the block the pair lives in |
| W-c | `registry.audit` | the pond-corner draw is `water.placement: list` with several `candidates` — no existing marker pattern (`random_*`, `_low/_high`, `[a, b]`, `properties_std`) matches it. Needs its own marker |
| W-d | `_fig.TERM_NAMES` | codes 6 and 7 are missing, so F1 lumps thirst deaths into "other" |
| W-e | `registry.TARGETS` / `targets()` / `sweep.aggregate` `succ` | no pond target |
| W-f | `screen.py` / F5, `probes.py` / F7 part 7e | refuse with fewer than 2 runs per cell (correct), but `build_page.py` then shows "not yet produced", which is misleading |
| W-g | `probes.py` | hard-codes the three hvsmell worlds (`SPEC_WORLD`, `WORLD_CONTRASTS`, line 225); refuses series under 20 checkpoints — early-stopped thirst runs may have fewer |

### Hidden 10×10 assumptions (item 6) — audit result

- "Within two squares" of a rabbit / predator is **Chebyshev ≤ `NEAR_D` = 2** (`sweep.py:246`,
  `hiding_drivers.py:41`): size-free. Injury / nutrition bands (`INJ_EDGES`, `NUT_EDGES`): size-free.
- Thermal blur uses `thermo["H"]`, `["W"]` from rebuilt params (`registry.thermal_info`): size-free.
- Spawn distances (`d_bush0`, `d_pred0`) are Chebyshev from real positions: correct at any size,
  but their **range grows with the map** (up to 9 / 14 / 19). Fits are per run, so slopes stay
  valid; F3 overlays of different worlds must be read per world (the page caption says so).
- `frac_time_*` consequences are shares: size-free.
- **Found, F7 only** (deferred until the d9 edit lands): `f7_probes.py:208-209` fixes the x axis at
  0–10.3 (million episodes) and `:369-371` hard-codes `total: 9` runs. Thirst runs stop early (§4
  of [[THIRST_TASK]]) and have 18 runs; both must come from the data.
- The developer re-greps `scripts/analysis/basic_behaviour/*.py` and `scripts/analysis/core/env.py`
  for literal 10 / 9 / 100 / 11 and grid-shaped constants and lists every hit in the Implementation
  Report with "size-free" or "fixed".

## Implementation Plan

### Design

**D1. Hydration slot (registry.obs_indices).** Add `out["hydration"] = idx["Hydration"][0]` (or
`None`) using the same ordered breakdown from `get_observation_breakdown(params)`, already
cross-checked against the manifest. `obs_indices` currently returns `None` when thermal is off; the
water worlds all have thermal on, but the guard becomes "thermal **or** water enabled" so a future
water-only world works. The scale is `float(cfg["water"]["max_hydration"])` via the mandatory-key
path, never 200. Rebuild params when `thermal.enabled or water.enabled` (`sweep.describe:113`).

**D2. Pond replay (new `registry.pond_cells(params, seeds)`).** `jax.vmap(jax_reset)` over
`PRNGKey(seed)` in chunks of 2048 (the pilot's code), returning `water_pos [n, h·w, 2]`, the reset
`agent_pos [n, 2]`, and the corner index = row of `params.water_topleft_table` equal to
`water_pos[:, 0]` (0-based table, so no 1-based conversion is ever typed). Every episode must match
exactly one table row, else hard stop. Params come from `registry.rebuild_params(cfg)` (already
`apply_saved_config_compat`). Sweep holds a per-episode pond mask `[n, H·W]` bool.

**D3. Integrity checks inside the sweep, every store, every episode (hard stop on any failure).**
(1) replayed start cell == stored `agent_row/col` at t = 0; (2) for every t ≥ 1 row: `on_pond(t)`
⇔ `hydration(t) > hydration(t−1)`. These are the pilot's R1 checks; they run on all 18 stores, so
the 15×15 and 20×20 pond geometry is validated where it is used. Counts land in
`inventory.json["water_checks"]`.

**D4. Sixth target "pond".** `TARGETS["pond"] = "on the pond (drinking)"`. Success at a chosen step
(t ≥ 1) = the agent's cell at t is a pond cell. Available iff `water.enabled`, Hydration is in the
observation, `obs_precision == "float32"`, `obs_true` is a step column — each with its own reason
string, mirroring `warm_cell`. Added to `succ`, `G["y_pond"]`, the trial assertion, and every
row-t−1 cross-table. `OUTCOME_CONSEQUENCE["pond"] = ["frac_time_on_pond"]`.

**D5. Hydration factors and consequences.**
- `start_hydration` — exogenous, episode, all; `max_hydration × obs_true[Hydration]` at t = 0;
  claimed by the new audit handler for `water.random_start_hydration` (handler "W1").
- `spawn_dist_to_pond` — exogenous, episode, all; Chebyshev from start cell to the nearest replayed
  pond cell; emitted when `environment.random_start_pos` is true (the analogue of handler 5).
- Consequences `mean_hydration` (chosen steps) and `frac_time_on_pond`.
- **Pond corner** (`pond_corner`, 0..K−1 by table row) is stored per episode in `episodes.npz` and
  tabulated in F2 (share of episodes per corner), **not fitted**: four equiprobable corners carry no
  ordering, and its effect on behaviour runs through `spawn_dist_to_pond`. *Default, user may
  revisit:* fit it as K−1 indicator factors instead.

**D6. World features (registry; F2 inventory + run table).** `inventory.json["world"]` gains
`pond_size: [h, w]` (from `water.size`), `pond_cells`, `pond_corners` (the table, 0-based), map
`H×W`, and `sensor_radius`, all read from the saved config. These are constants within a run; they
label worlds on the page, they are not regressors.

**D7. Audit (registry.audit).** Add `"water"` to `WORLD_BLOCKS`, walked **only when
`water.enabled` is true** (keeps a01 / hv inventories unchanged). In the `_low/_high` and
`random_start_*` branches, look the switch up in the **same block** as the pair (fixes W-b). New
marker: `placement == "list"` and `len(candidates) > 1` → claimed by "handler W2 (pond_corner,
spawn_dist_to_pond)"; `placement: random` → claimed by W2 as well (the replay handles any mode);
`center` or a single candidate → "not a draw". `size` and `candidates` are fixed parameters
(`NOT_A_DRAW`). Acceptance: on every thirst cell, `unhandled(rows)` is empty.

**D8. Hydration in F6 (state panels), no same-row hazard.** New cross-table `hyd_nut__<target>`
(4 × 4: hydration bands `<50, 50–100, 100–150, 150+` × the existing nutrition bands), both read at
**row t−1** — the state the agent was in when it chose the step (plan A6). Hydration is digitised
after `np.round(h, 3)` so float32 round-trip (e.g. 99.99998) cannot flip a band at an edge. F6 gains
one heat-map row per world × agent for water worlds; absent otherwise.

**D9. Termination codes.** `_fig.TERM_NAMES` gains `6: "died of thirst"`, `7: "over-drank"`. F1's
"other" bucket must be 0 % on every thirst cell (asserted).

**D10. One run per cell.** `screen.py` already refuses and writes `screen/<target>/prefit.json
{"refused": …}`. `build_page.py` renders that reason in the F5 block instead of "not yet produced".
F1–F4 and F6 are built per run as usual. F7 part 7e gets the same treatment (D12).

**D11. Population.** `scripts/analysis/studies/hypervigilance/make_population.py --from-study-doc
docs/experiments/active/thirst_task/THIRST_TASK.md --population thirst --checkpoint-nearest <b*
store> --out results/analysis/basic_behaviour/thirst/` (stores from the collection in
[[THIRST_TASK]] §5.5, root `results/analysis/thirst_task/`). Required: 18 cells, `world` ∈ the nine
cell names, `agent` ∈ {t1none, t16quad}, seed 42, all `completed`. If the parser cannot read §9
(it looks for `run dir \`…\`` in the Log-path cell, which §9 does not yet carry), the fix is a
§9 Status/Log-path edit by the session that keeps that table, not a code change here.

**D12. Probe scenes (Figure 7) for the thirst population.** Every saved checkpoint of each run is
replayed in the 12 fixed scenes (no animal; hunting predator; chasing rabbit; chasing rabbit with
its predator-like odour zeroed; wandering rabbit; wandering rabbit with the world's predator
smell; each at start injury 0 and 70), 30 episodes each, 100-step episodes. Defaults set in the
user's absence — **each is "default, user may revisit"**:
- (i) A new generator `configs/environment/experiment/behavior_probes/thirst/generate_thirst_probes.py`
  for the nine worlds, modelled on the hvsmell one, which is **not edited**. Each scene `extends:`
  its thirst world and overrides only the layout (blocking bush, a campfire beside it, fixed start,
  animals with zero smell spread).
- (ii) Scenes keep each world's **own map size and smell reach**, so the agent is not tested outside
  its training distribution. The core layout keeps its absolute coordinates (start [5,5], bush
  [5,2], fire [5,3], animal spawn [5,9]), so its geometry relative to the agent **and** to the north
  and west walls is identical at every size; the larger maps extend south and east. Alternative:
  the standard 10×10 arena for all worlds; or centring the layout.
- (iii) **Pond and hydration.** Start hydration fixed at the setpoint (`random_start_hydration:
  false`, `start_hydration: 100`); over 100 steps it drains to 37.5, so thirst death (step 160) is
  impossible and the scenes stay about animals and cover. **The pond cannot be removed**: with
  `water.enabled: true` the reset always places one (`core.py:1884`), and `water.enabled: false`
  drops the Hydration number from the observation (59 → 58), which the trained agents cannot take.
  Default: `placement: list` with **one** candidate at the corner farthest from the scene's cells
  (on 10×10 that is still only ~3 squares from the start — stated on the page); pond smell and sight
  left as trained. The sweep records per scene the share of episodes in which the agent ever stood
  on the pond. Alternatives: a small environment change adding `water.placement: none` (its own
  plan, `src/` change), or a deliberate pond scene as a follow-up.
- (iv) `probes.py` and `f7_probes.py` refuse 7e (seed-to-seed budget) when any world has < 2 runs,
  as F5 does, and the page shows the reason. World-difference panels are descriptive at one seed.
- `probes.py` is generalised minimally: worlds come from the sweep specs + population (no
  hv-specific `SPEC_WORLD` / `WORLD_CONTRASTS` for this population; thirst declares no contrasts),
  and the 20-checkpoint floor is reported per run, never silently dropped.
- Sweep specs: nine files `configs/eval_sweeps/thirst/thirst_<cell>_rppo.yaml` (one per world, two
  runs each), `nodes: []` with the hvsmell comment. Run by `scripts/eval/dwell_sweep/run_sweep.py`,
  CPU only.
- **Env-config check per world** (the generator's `--check-only`, then `env-config-reviewer`): every
  one of the 9 × 12 files loads through `load_env_params`; grid = the world's size; `sensor_radius`
  = the world's; observation breakdown (names, order, widths, D = 59) equals the run's saved config;
  water: fixed start 100, one candidate, pond cells disjoint from start / bush / fire / spawn / patrol
  cells; animal smell vectors equal the world's, spread 0; and 30 seeded resets show the fixed
  start, bush, fire and pond where intended.
- **Nodes** (the parent picks them at launch, from live `gpu-status` + the diary): CPU-only work;
  avoid nodes running the thirst training (currently 106, 107, 109–114 per [[THIRST_TASK]] §9) since
  the eval would starve their data pipeline; confirm the NAS mount on each (`df | grep nas01`).
  Node time per world is measured on the first world before the rest (hvsmell: 9–15 min with 6
  runs per world; thirst has 2 runs per world but larger maps). Collation, 60–90 min on the
  launching container, must not be restarted mid-way.

### Gates

- **Gate 1 (a01 byte-identity) and Gate 2 (single-channel hv1ch store) stay byte-identical**, plus
  the thermal replay. Every water path is gated on `water.enabled`, false in both reference worlds.
- **Source-hash consequence (state it to d9 before merging):** `registry.py` and `sweep.py` are in
  `SWEEP_SOURCES`, so editing them changes the golden stamp's hash and makes existing hvsmell
  caches refuse `--reuse-cache`. The gate is re-run once on the final diff; hvsmell re-sweeps are
  scheduled with d9, not forced by surprise.
- **Gate 3 (new, water)** in `golden_gate.py`, on one thirst store (g10sW ordinary, final store):
  (a) the Hydration index found by name is not its alphabetical position and equals the pilot's
  layout position; (b) 20 episodes replayed with `jax_reset`: replayed `state.hydration` at t = 0
  equals `max × obs_true[Hydration]` within 1e-4; (c) **pond time, two independent ways**:
  pipeline `y__pond.sum() / n_steps.sum()` versus a count of hydration rises read directly from the
  parquet with the pilot's reader logic (fixed index, `np.diff(h) > 0`, no replay, no registry) —
  equal integer counts, so the shares agree to the last printed digit; (d) the D3 checks report
  zero exceptions; (e) the audit has no unhandled row. Pass is added to `_golden_pass.json`.

### Speed

The sweep already reads `obs_true` on thermal worlds (~14 min per run locally). Water adds one
vmapped reset per store (seconds) and a vectorised pond-mask lookup per shard. Expected ≤ 5 %;
measured on the gate store before/after and recorded. All sweeps and fits run **in the local
container** at `nice -n 19` — lab nodes lack `statsmodels` (Known Bugs, "node env drift"). 18 runs
at `--workers 3`: about 1.5 h wall. Only the F7 probe sweep uses nodes.

### File Changes

Edits to `f7_probes.py`, `page_template.html` (and `build_page.py`, which d9 also edits) start
**only after d9 says its edit is committed**.

| File | Change |
|---|---|
| `scripts/analysis/basic_behaviour/registry.py` | D1, D2 (`pond_cells`), D4 target, D5 factors/consequences, D6 world features, D7 audit |
| `scripts/analysis/basic_behaviour/sweep.py` | params rebuild when water on; Hydration read; replay + D3 checks; `y_pond`, `hyd0`, `hyd_sum1`, `pond_corner`, `d_pond0`; `hyd_nut__*` row-t−1 cross-tables; `factor_arrays` kinds `start_hydration`, `spawn_dist_pond` |
| `scripts/analysis/basic_behaviour/_fig.py` | `TERM_NAMES` 6, 7 |
| `scripts/analysis/basic_behaviour/f1_behaviours_survival.py` | assert "other" = 0 on water worlds; sixth behaviour drawn |
| `scripts/analysis/basic_behaviour/f2_factor_inventory.py` | pond-corner shares and world features |
| `scripts/analysis/basic_behaviour/f6_crosstabs.py` | hydration × nutrition heat maps (D8) |
| `scripts/analysis/basic_behaviour/build_page.py` | refusal reasons for F5 / 7e (D10); `pond` target accepted (after d9) |
| `scripts/analysis/basic_behaviour/page_template.html` | pond / hydration wording, refusal text (after d9) |
| `scripts/analysis/basic_behaviour/probes.py`, `f7_probes.py` | D12 generalisation, 7e refusal, data-driven x range and run total (f7 after d9) |
| `scripts/analysis/basic_behaviour/golden_gate.py` | Gate 3 |
| `configs/environment/experiment/behavior_probes/thirst/generate_thirst_probes.py` + 9 × 12 scene YAMLs | D12 (i)–(iii) |
| `configs/eval_sweeps/thirst/thirst_<cell>_rppo.yaml` × 9 | D12 sweep specs |
| `tests/analysis/test_basic_behaviour.py` | tests below |
| `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` | new caller relations (registry → `core.jax_reset`; golden_gate Gate 3), new generator and sweep specs — same commit |
| `docs/develop/active/behavior/BASIC_BEHAVIOUR_ANALYSIS_PIPELINE.md` | one dated cross-link line to this plan |

No `src/` change, no store-schema change, no new config key, no critical-settings change, no
version number anywhere.

### Tests (fast, no store reads)

1. Audit on a synthetic water config: `random_start_hydration` claimed by W1; `start_hydration_low/high`
   claimed (not "not a draw" — this test **fails on the current code** once `water` is walked);
   `placement: list` with 4 candidates claimed by W2; 1 candidate "not a draw"; a01-shaped config
   (water off) gives the identical rows as before.
2. Hydration index by name on a synthetic breakdown where alphabetical ≠ true order.
3. Pond replay on level-06 params for 50 seeds: corner index matches exactly one table row; cells
   lie inside the grid; at 20×20 size 4×4 gives 16 distinct cells.
4. Hydration banding edge guard: a true 100.0 read back from float32 as 99.99998 lands in band
   100–150 (as 100.0 does); 49.99996 lands in band 50–100.
5. `TERM_NAMES` covers 1–7.
6. `targets()` on a water config: `pond` available; with `obs_precision: float16` unavailable with
   the reason string.
7. Probe generator `--check-only` passes on the generated files (run in the test only if the files
   exist).

## Checkpoints

- [ ] C1 registry + sweep water paths; tests 1–6 pass
- [ ] C2 Gates 1 and 2 byte-identical on the edited code; thermal replay passes
- [ ] C3 Gate 3 passes on the g10sW store; speed before/after recorded
- [ ] C4 population.json: 18 completed cells (D11)
- [ ] C5 sweep of all 18 cells locally; D3 checks zero exceptions on every store (incl. 20×20); no
      unhandled audit row; F1 "other" = 0
- [ ] C6 F1–F4, F6 built for all six targets; F5 shows its refusal reason
- [ ] C7 (after d9's go) build_page / template / f7 edits; probe generator + 108 scenes;
      `--check-only` + `env-config-reviewer` pass
- [ ] C8 probe sweep launched by the parent on its chosen nodes; collation; F7 built with 7e refusal
- [ ] C9 page through `publish-page` + `artifact-format-reviewer`; diff to d9 for review

## Implementation Report

*(developer fills)*

## Verification Report

*(senior-developer fills)*
