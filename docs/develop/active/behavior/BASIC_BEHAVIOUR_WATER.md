---
title: "Basic Behaviour Analysis: water (pond time, hydration, pond features, thirst deaths) for the 18 thirst-task runs"
topic: behavior
status: active
created: 2026-10-02
last_updated: 2026-10-03
---

# Basic Behaviour Analysis — adding water

> **Status**: **Revision 1** (2026-10-03) — answers the plan review ([[plan_basic_behaviour_water]],
> verdict NOT READY on commit `92cd1be8`); see §R1. Awaiting the reviewer's re-check. Nothing implemented.
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

## R1. Revision 1 — response to review (2026-10-03)

The review ([[plan_basic_behaviour_water]], and the signed block at the end of this doc, kept as
written) found one Critical and nine Moderate problems. The parent session decided each one in the
user's absence, following the user's earlier choices. The table says what changed and where.
Anything marked **default, user may revisit** is open for the user to reverse.

| Finding | Decision and change | Where |
|---|---|---|
| 1 🔴 no stop point (b\*), no stores | **Early stopping was not applied: the user cancelled the hourly stop-checker loop, so every run trained the full 10 M episodes.** The endpoint for every world is the **final checkpoint (≥ 10 M episodes)**. The page says so in plain words: "early stopping not applied; user cancelled the checker". Stores: 1 M episodes per run at the final checkpoint, spec `configs/trajectory_collection/thirst_task.yaml`, out-root `results/trajectories_thirst_task/`, collection started 23:49 (2026-10-02) on nodes 106–114. New **C0 "stores collected and validated"**; the loop waits at C0 and runs nothing that reads a thirst store before it. The probe step replays all 50 checkpoints, as hvsmell does, and its summary window is the newest 20, ending at 10 M | Status, D11, D12, Gates, C0 |
| 2 🟡 population builder needs code | A named code change to `make_population.py` (the developer writes it; d9 reviews; listed in SCRIPTS_DEPENDENCY_MAP): (a) the nine thirst cell names in `CELL_WORLD`, mapping to themselves (`g10sW` … `g20s3`); (b) `Cell` split on `·` **or** whitespace (§9 reads `g10sW ordinary`); (c) no `--checkpoint-nearest`: each run has one store, `final`. §9 rows still need `completed` and a `run dir` entry in the Log-path cell; the thirst session makes that doc edit | D11 |
| 3 🟡 bouts contaminate hydration at t−1 | For the **pond** target, the hydration panel bins by hydration **at the start of a bout**: the denominator is the steps where the agent was off the pond at t−1, the numerator is arrivals. So the panel shows the arrival rate by thirst, not bout continuation. The page says which binning it uses. The other five targets keep the row-t−1 binning. Known Bugs note filed later through `bug-curator`; not blocking | D8 |
| 4 🟡 probe pond confounded with map size | The pond sits at the **same distance from the scene at every map size**: its top-left at the start cell + (3, 3), which is the 10×10 geometry (level-06 candidate [8,8] with start [5,5]). Each world keeps its own pond size (2×2 / 3×3 / 4×4), so the pond's total smell stays what that world trained with. The generator asserts the replayed offset (nearest pond cell − agent start) is identical in all nine worlds. Start hydration stays **100** (the user's earlier default, **default, user may revisit**). Pre-registered rule: the pond-visit share (episodes in which the agent stands on the pond at least once) is reported for every scene × checkpoint. A scene × checkpoint cell with **more than 3 of its 30 episodes (> 10 %)** on the pond is **dropped** from every F7 summary, and the drop count is shown. Over-drinking (code 7) needs at least **20 consecutive pond steps** from 100 (net +5 per step to reach 200), so it can only occur in pond-visiting episodes, which the rule already covers | D12 (iii) |
| 5 🟡 Gate 3(c) redundant | Replaced. The water gate runs the pipeline on a **thirst-pilot store** and must equal the pilot readout files written earlier by other code (`results/analysis/thirst_pilot/readout/<agent>_<seed>_<ckpt>.json`): chosen steps = `check2_steps_checked`; drinking steps = `bouts_per_episode × n_episodes × steps_per_bout_mean` (an integer to 1e-6, else the gate fails); share of episodes that drank = `share_episodes_drank`; death shares = `term_share`. It runs before any thirst store exists | Gates |
| 6 🟡 shared stamp coupled | The water gate writes its **own stamp**, `results/analysis/basic_behaviour/_water_pass.json`. Only populations with water require it. Gates 1/2 keep writing `_golden_pass.json` unchanged | Gates |
| 7 🟡 hvsmell page would break | Every water part depends on **whether the population has water** (any cell's saved config has `water.enabled: true`). Termination columns 6/7, the pond target, template wording and F6 hydration rows exist only then. F1 iterates the targets present in the inventory, so old inventories without `pond` still work. Development happens in an **isolated git worktree branch**, merged into `v5.0` only after the hvsmell page rebuilds **byte-identical (figures)** and d9 has reviewed. d9 is warned **before** the merge that the source-hash change makes hvsmell caches refuse `--reuse-cache` | D13, Gates, C2b |
| 8 🟡 change-log entry missing | Same-commit CONFIG_CRITICAL_SETTINGS change-log entry for the 108 probe scenes' local `water.placement` / `water.candidates` / `random_start_hydration` / `start_hydration` overrides ("NO CANONICAL VALUE CHANGED", as on 2026-09-23 and 2026-10-01) | File Changes |
| 9 🟡 node launch while the user sleeps | The user explicitly asked for the probe sweeps to run overnight, so C8 stays. The launcher picks nodes from **live `gpu_status`**, runs the pre-flight checks (NAS mount, `pgrep` for CPU-phase claimants, today's diary) and **claims the nodes in the diary at launch**. CPU only. The stale node-avoid list is removed | D12 Nodes, C8 |
| 10 🟡 n = 1 honesty | Every F3, F4 and F7 error bar is captioned **within-run (one trained policy)**: episode-to-episode or checkpoint-to-checkpoint spread, not seed-to-seed. A page-level box quotes [[THIRST_TASK]] §5.4, that one seed "cannot support any modulator claim" nor any "no difference" claim. No modulated-minus-ordinary panel or sentence. Greedy-store numbers are never pooled with training-log numbers (§5.5) | D10 |
| 11 🟢 labels unlisted | `_fig.FACTOR_LABEL` (new factor names), `f1.TERM_SHORT` (codes 6/7) and `f1.TARGET_KEY` (`pond`) added to File Changes | File Changes |
| 12 🟢 thermal contract | The hvsmell generator's thermal-contract check (bush warm and survivable, start cell not) is kept per world in the thirst generator's `--check-only` | D12 env-config check |

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
**Revision 1 (finding 3):** for the **pond** target only, hydration is binned at the **start of a
bout**. Trials are the chosen steps where the agent was off the pond at t−1, successes are arrivals
on the pond at t, and the bands are read from hydration at t−1. Cross-table `hyd_nut_onset__pond`.
The page states this binning under the panel.

**D9. Termination codes.** `_fig.TERM_NAMES` gains `6: "died of thirst"`, `7: "over-drank"`. F1's
"other" bucket must be 0 % on every thirst cell (asserted).

**D10. One run per cell.** `screen.py` already refuses and writes `screen/<target>/prefit.json
{"refused": …}`. `build_page.py` renders that reason in the F5 block instead of "not yet produced".
F1–F4 and F6 are built per run as usual. F7 part 7e gets the same treatment (D12).
**Revision 1 (finding 10):** every F3, F4 and F7 interval is captioned "within-run (one trained
policy)". A page-level box quotes [[THIRST_TASK]] §5.4, and the page carries no
modulated-minus-ordinary reading. The endpoint note reads "early stopping not applied; user
cancelled the checker".

**D11. Population (Revision 1).** `scripts/analysis/studies/hypervigilance/make_population.py
--from-study-doc docs/experiments/active/thirst_task/THIRST_TASK.md --population thirst --store-root
results/trajectories_thirst_task --out results/analysis/basic_behaviour/thirst/`. Stores: one per
run, the **final checkpoint (≥ 10 M episodes)**, 1 M episodes, from `configs/trajectory_collection/thirst_task.yaml`.
**Code change** (developer writes, d9 reviews): thirst cell names in `CELL_WORLD`; `Cell` split on
`·` or whitespace; no `--checkpoint-nearest` (one store per run). **Doc edit** (thirst session):
§9 rows set to `completed` with a `run dir \`…\`` entry in the Log-path cell. Required: 18 cells,
`world` ∈ the nine cell names, `agent` ∈ {t1none, t16quad}, seed 42, all `completed`.

**D12. Probe scenes (Figure 7) for the thirst population.** Every saved checkpoint (all 50,
ending at the final ≥ 10 M checkpoint; early stopping was not applied) of each run is replayed in the 12 fixed scenes (no animal; hunting predator; chasing rabbit; chasing rabbit with
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
  **Revision 1 (finding 4):** `placement: list` with **one** candidate whose top-left is the start
  cell + (3, 3), the 10×10 geometry, at **every** map size. Each world keeps its own pond size, and
  pond smell and sight stay as trained. The pre-registered pond rule (report the visit share; drop
  any scene × checkpoint cell with > 3 of 30 episodes on the pond) is in §R1. Over-drinking needs
  ≥ 20 consecutive pond steps from 100, so it is covered by that rule. Alternatives: a small environment change adding `water.placement: none` (its own
  plan, `src/` change), or a deliberate pond scene as a follow-up.
- (iv) `probes.py` and `f7_probes.py` refuse 7e (seed-to-seed budget) when any world has < 2 runs,
  as F5 does, and the page shows the reason. World-difference panels are descriptive at one seed.
  The summary window is the newest 20 checkpoints, ending at the final (10 M) checkpoint.
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
  start, bush, fire and pond where intended, with the nearest-pond-cell offset from the start
  identical in all nine worlds. The hvsmell thermal-contract check (bush warm and survivable, start
  cell not) is kept per world. The generator, scenes and sweep specs are configs, so
  `experiment-designer` produces them, with the CONFIG_CRITICAL_SETTINGS entry in the same commit.
- **Nodes (Revision 1, finding 9):** the user asked for the probe sweeps to run overnight. The
  launcher picks nodes from **live `gpu_status`** at launch and avoids any node with live training or
  trajectory collection (the collection started 23:49 on 106–114). It runs the pre-flight checks:
  NAS mount (`df | grep nas01`), `pgrep` for CPU-phase claimants that `nvidia-smi` cannot see, and
  today's diary. It **claims the nodes in the diary at launch**. CPU only.
  Node time per world is measured on the first world before the rest (hvsmell: 9–15 min with 6
  runs per world; thirst has 2 runs per world but larger maps). Collation, 60–90 min on the
  launching container, must not be restarted mid-way.

### Gates

- **Gate 1 (a01 byte-identity) and Gate 2 (single-channel hv1ch store) stay byte-identical**, plus
  the thermal replay. Every water path is gated on `water.enabled`, false in both reference worlds.
- **hvsmell unchanged (Revision 1, finding 7):** before the merge, the hvsmell page is rebuilt twice
  from the same hvsmell stores into a scratch root: once with `v5.0` code and once with the branch.
  Every PNG must be byte-identical between the two (SVG/PDF compared after stripping their date
  metadata). Plus d9's review.
- **Source-hash consequence (state it to d9 before merging):** `registry.py` and `sweep.py` are in
  `SWEEP_SOURCES`, so editing them changes the golden stamp's hash and makes existing hvsmell
  caches refuse `--reuse-cache`. The gate is re-run once on the final diff; hvsmell re-sweeps are
  scheduled with d9, not forced by surprise.
- **Water gate (Revision 1, findings 5 and 6)**, a separate mode of `golden_gate.py`, on a
  **thirst-pilot store** (`results/analysis/thirst_pilot/<run>/<ckpt>/<hash>/`, the one behind
  `readout/t16quad_s42_2000001.json`): (a) the Hydration index found by name is not its
  alphabetical position (index 2 vs 7, verified by the reviewer); (b) 20 episodes replayed with
  `jax_reset`: replayed `state.hydration` at t = 0 equals `max × obs_true[Hydration]` within 1e-4;
  (c) **external reference**: the pipeline's numbers equal the pilot readout JSON, written earlier
  by other code. Chosen steps `n_steps.sum()` = `check2_steps_checked`; pond steps `y__pond.sum()`
  = `bouts_per_episode × n_episodes × steps_per_bout_mean` (integer to 1e-6, else fail); share of
  episodes with any pond step = `share_episodes_drank`; termination shares = `term_share`; (d) the
  D3 checks report zero exceptions; (e) the audit has no unhandled row. Pass writes **its own
  stamp** `results/analysis/basic_behaviour/_water_pass.json`, required only by populations with
  water. `_golden_pass.json` is untouched by it. On the thirst stores (after C0) the D3 checks run
  on every store during the sweep.

### Speed

The sweep already reads `obs_true` on thermal worlds (~14 min per run locally). Water adds one
vmapped reset per store (seconds) and a vectorised pond-mask lookup per shard. Expected ≤ 5 %;
measured on the gate store before/after and recorded. All sweeps and fits run **in the local
container** at `nice -n 19` — lab nodes lack `statsmodels` (Known Bugs, "node env drift"). 18 runs
at `--workers 3`: about 1.5 h wall. Only the F7 probe sweep uses nodes. The hvsmell
byte-identity rebuild (two re-sweeps of 18 hv cells) adds about 3 h locally.

### D13. Isolation (Revision 1, finding 7)

Development happens on a branch in its own worktree (`git worktree add -b bb-water
.claude/worktrees/bb-water v5.0`), merged into `v5.0` only after Gates 1/2, the hvsmell
byte-identity rebuild, and d9's review. **Hazard the developer must handle:** the pipeline finds
data from its own file location (`registry.ROOT`, `readings.ROOT`), and the NAS has no symlinks,
so worktree code cannot see `results/`. Minimal fix, part of the d9-reviewed diff: one environment
variable `BB_DATA_ROOT`. When it is set, data paths (population, stores, references) resolve under
it, and **every** output (sweeps, fits, figures, both stamps) goes under
`results/analysis/basic_behaviour/_water_dev/`. Source hashes keep using the code's own location.
When it is unset, behaviour is unchanged. So no worktree run can overwrite d9's `hvsmell/` outputs
or the shared `_golden_pass.json`. The developer verifies this by listing the mtimes of
`hvsmell/` and `_golden_pass.json` before and after each worktree run (unchanged).

### File Changes

Edits to `f7_probes.py`, `page_template.html` (and `build_page.py`, which d9 also edits) start
**only after d9 says its edit is committed**.

| File | Change |
|---|---|
| `scripts/analysis/basic_behaviour/registry.py` | D1, D2 (`pond_cells`), D4 target, D5 factors/consequences, D6 world features, D7 audit |
| `scripts/analysis/basic_behaviour/sweep.py` | params rebuild when water on; Hydration read; replay + D3 checks; `y_pond`, `hyd0`, `hyd_sum1`, `pond_corner`, `d_pond0`; `hyd_nut__*` row-t−1 cross-tables; `factor_arrays` kinds `start_hydration`, `spawn_dist_pond` |
| `scripts/analysis/basic_behaviour/_fig.py` | `TERM_NAMES` 6, 7 (water populations only); `FACTOR_LABEL` for `start_hydration`, `spawn_dist_to_pond`, `mean_hydration`, `frac_time_on_pond` |
| `scripts/analysis/basic_behaviour/f1_behaviours_survival.py` | iterate the targets present in the inventory; `TERM_SHORT` 6/7 and `TARGET_KEY` `pond`; assert "other" = 0 on water worlds; endpoint note |
| `scripts/analysis/basic_behaviour/f3_univariate.py`, `f4_multivariate.py` | "within-run (one trained policy)" interval captions (finding 10) |
| `scripts/analysis/studies/hypervigilance/make_population.py` | thirst `CELL_WORLD` names; `Cell` split on `·` or whitespace (D11; d9 reviews) |
| `scripts/analysis/basic_behaviour/registry.py`, `scripts/analysis/studies/hypervigilance/readings.py` | `BB_DATA_ROOT` (D13) |
| `docs/environment/CONFIG_CRITICAL_SETTINGS.md` | dated change-log entry for the probe scenes' local water overrides (finding 8; same commit as the scenes) |
| `scripts/analysis/basic_behaviour/f2_factor_inventory.py` | pond-corner shares and world features |
| `scripts/analysis/basic_behaviour/f6_crosstabs.py` | hydration × nutrition heat maps (D8); bout-onset binning for `pond` |
| `scripts/analysis/basic_behaviour/build_page.py` | refusal reasons for F5 / 7e (D10); `pond` target accepted (after d9) |
| `scripts/analysis/basic_behaviour/page_template.html` | pond / hydration wording, refusal text (after d9) |
| `scripts/analysis/basic_behaviour/probes.py`, `f7_probes.py` | D12 generalisation, 7e refusal, data-driven x range and run total (f7 after d9) |
| `scripts/analysis/basic_behaviour/golden_gate.py` | water-gate mode with its own stamp `_water_pass.json`; `fit.require_stamp` also requires it for water populations |
| `configs/environment/experiment/behavior_probes/thirst/generate_thirst_probes.py` + 9 × 12 scene YAMLs | D12 (i)–(iii) |
| `configs/eval_sweeps/thirst/thirst_<cell>_rppo.yaml` × 9 | D12 sweep specs |
| `tests/analysis/test_basic_behaviour.py` | tests below |
| `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` | new caller relations (registry → `core.jax_reset`; golden_gate water mode → pilot readout; make_population thirst source), new generator and sweep specs — same commit |
| `docs/develop/active/behavior/BASIC_BEHAVIOUR_ANALYSIS_PIPELINE.md` | one dated cross-link line to this plan |

No `src/` change, no store-schema change, no new config key, no version number anywhere. One
critical-settings change-log entry (local overrides only, no canonical value changed).

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

- [ ] C0 **stores collected and validated**: 18 final-checkpoint (≥ 10 M) stores of 1 M episodes
      under `results/trajectories_thirst_task/`, each with a manifest, D = 59, `obs_precision`
      float32, contiguous seeds. **The loop waits here**; nothing that reads a thirst store runs
      before it (C1–C3 and C7 may)
- [ ] C1 worktree branch (D13); registry + sweep water paths; tests 1–6 pass
- [ ] C2 Gates 1 and 2 byte-identical on the edited code; thermal replay passes
- [ ] C2b hvsmell page rebuilt byte-identical (figures) from `v5.0` vs branch; d9 warned about cache refusal
- [ ] C3 water gate passes on the pilot store (`_water_pass.json`); speed before/after recorded
- [ ] C4 population.json: 18 completed cells (D11; needs C0 and the §9 doc edit)
- [ ] C5 sweep of all 18 cells locally; D3 checks zero exceptions on every store (incl. 20×20); no
      unhandled audit row; F1 "other" = 0
- [ ] C6 F1–F4, F6 built for all six targets; F5 shows its refusal reason
- [ ] C7 (after d9's go) build_page / template / f7 edits; probe generator + 108 scenes;
      `--check-only` + `env-config-reviewer` pass
- [ ] C8 probe sweep launched overnight: nodes from live `gpu_status`, pre-flight checks, diary
      claim at launch, CPU only; collation; pond-visit rule applied; F7 built with 7e refusal
- [ ] C9 page through `publish-page` + `artifact-format-reviewer`; diff to d9 for review; merge
      into `v5.0` after d9's review

## Implementation Report

*(developer fills)*

## Verification Report

*(senior-developer fills)*

## Feedback from plan-reviewer

*Reviewed by: plan-reviewer, 2026-10-02, on commit `92cd1be8`. Full report with evidence:
[[plan_basic_behaviour_water]] (`docs/reviews/plan_basic_behaviour_water.md`).*

**Verdict: NOT READY.** The design is mostly sound. The pond rebuild is checked against
independently recorded data, and the old-world reference checks really are untouched. But the
plan assumes data and a stop-point decision that do not exist yet, and its probe step would use
checkpoints the thirst study says to ignore.

Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run · 🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

| # | Sev | Where | Issue → fix |
|---|---|---|---|
| 1 | 🔴 | Gate 3, D11, D12, C3–C8 | All 18 runs ran to 10 M with no b\* recorded (THIRST_TASK §9 still `running`, §10 empty), and no §5.5 store exists. Add **C0** (b\* per world recorded and stores collected); the loop halts after C2 otherwise. D12 / probes use only checkpoints ≤ b\* (THIRST_TASK §4: "anything after b\* is ignored"). |
| 2 | 🟡 | D11 | The parser needs a **code** change: `make_population.py` knows only hv world names (`:42`) and splits Cell on `·` (`:166`). b\* differs per world, so one `--checkpoint-nearest` cannot serve all 18. Name the change and its owner (d9 reviews). |
| 3 | 🟡 | D8 | Hydration at t−1 is raised by the drinking bout itself (+5/step), so pond × hydration mostly shows bout continuation. Bin the pond target by hydration at bout onset (off-pond at t−1). Same family as Known Bugs row 502. |
| 4 | 🟡 | D12 (ii)–(iii) | The pond is ~3 squares away on 10×10 vs ~8–12 on 15/20, and hydration drains 100 → 37.5 in-scene. Map-size bush-dwell differences would partly measure pond distance × thirst. Code 7 is possible in-scene. Use the same pond distance at every size, and pre-state a pond-visit rule. Start-hydration choice goes to the user. |
| 5 | 🟡 | Gate 3(c) | Redundant with D3 (it equals D3 by construction once the sweep passes). Instead, compare with the pilot readout JSONs on a pilot store: an external reference that can run tonight. |
| 6 | 🟡 | Gate 3 → `_golden_pass.json` | Couples the shared stamp to thirst data and would block hvsmell fits. Use a separate water stamp. |
| 7 | 🟡 | `_fig`/`f1`/template | Old hvsmell inventories lack `pond`, so F1 `KeyError`s (`f1:42,62`). Codes 6/7 add empty columns to a waterless page. Shared template text changes. Make these population-conditional. Work in a worktree. Warn d9 before the merge. |
| 8 | 🟡 | "No critical-settings change" | Scene files override `water.placement` / `candidates` locally. By the 2026-09-23 and 2026-10-01 precedent, add a change-log entry. |
| 9 | 🟡 | C8 | Lab-node launch while the user sleeps. Exclude C8 from the loop. The node list is stale (training is done). |
| 10 | 🟡 | Page text | F3/F4/F7 intervals are within-run (episodes / checkpoints), not seed noise. Caption them so, quote THIRST_TASK §5.4, and include no modulated-minus-ordinary reading. |
| 11–12 | 🟢 | File Changes; D12 checks | List `FACTOR_LABEL`, `TERM_SHORT`, `f1.TARGET_KEY`. Keep the hvsmell generator's thermal-contract check. |

Verified here: Hydration index 2 (alphabetical 7) at 10×10 and 20×20; noise off in all nine
saved configs; no `src/environment/` change since the frozen run commit `583b022f`.

**Flips to SOUND WITH CONCERNS when** findings 1 and 2 are resolved (C0 + ≤ b\* restriction; the
population-builder change named and owned).
