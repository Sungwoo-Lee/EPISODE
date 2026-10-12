---
title: "Evaluation and readout tooling for the level-05 half-factorial world screen"
topic: hypervigilance
status: active
created: 2026-10-13
last_updated: 2026-10-13
---

# Evaluation and readout tooling for the level-05 half-factorial world screen

> **Status**: PLANNED (awaiting plan review and user answers to the three open questions at the end)
> **Opened**: 2026-10-13
> **Related**: [[LOOKALIKE_HALF_FACTORIAL_L05]] (the experiment design this tooling serves; its sections
> "Outcome measures", "Data", "Pass rule" and "Metrics requested"), [[LOOKALIKE_ANIMALS_CLOSE_POUNCE]]
> (world 1 and its frozen test scenes), [[FAST_HEAL_REPLICATION]] (the six level-05 runs used to measure
> seed-to-seed noise), [[TRAJECTORY_COLLECTION_PIPELINE]] (the recorder this plan builds on).

---

## Context

The project is training 16 agents in eight variants of its cold, predator-and-rabbit grid world (a
"half-factorial screen": four groups of world settings — predator threat, food economy, hazard
concealment and hazard load — each switched on in four of the eight worlds). The experiment design
fixes, in advance, one behavioural measure per group: how much more dangerous a step spent eating is
than other time in the open; how much an unhurt agent hides in a bush when the harmless rabbit is
close; how the agent reacts to stepping on a rock it could not see, compared with one it could; and
the injury-dependent hiding pattern measured in fixed test scenes. None of these measures can be
computed with the tools in the repository today. This plan specifies the tools: a recorder check, the
measure extraction, standard errors and data minimums, a driver that records more evaluation episodes
until the minimums are met, a test-scene builder that works for any world, and a background watcher
that runs all of it on GPU cards as soon as our own training runs free them, without taking a card the
queued training resumes need. The tools must also measure the seed-to-seed noise from eight
already-finished runs (six from the fast-healing replication and the two seed-43 runs of world 1),
because the pass rule needs that noise before any comparison is read.

**Headline of the recorder check (step 0).** The evaluation script named in the request does **not**
record enough: its per-episode files have no injury, no damage and no damage source, and its full
recordings (kept for 10 episodes only) have injury but still no damage or source. The project's
**trajectory store** (the large-scale recorder already used for the 27-million-episode foraging-death
analysis) records everything needed. On a real stored level-05 run, every damaging step is
attributed to exactly one source (predator, hidden trap or rock) with no unexplained remainder. So the
plan builds the episode-recording driver on the trajectory-store collector and changes no recorder.
Details and numbers in "Analysis §A1".

---

## Analysis

### A1. Step 0 — what the recorders actually capture (checked on real recordings, 2026-10-13)

Two recorders exist. Both were checked against files a real run produced, not against their source.

**(a) `scripts/eval/eval_rollout.py --record`.** Real output inspected:
`results/eval/avoidance/restprem/_scratch/a01_prem1/avoid_none_inj00/700127/20260810-185749_rppo_restprem_a01_n106/700127/`.

| Need | `episodes/<i>.npz` (every episode) | `recordings/…/episode_*.rec.gz` (first `--record-n-episodes`, default 10) |
|---|---|---|
| per-step action | yes (`action`) | yes (`actions`) |
| `agent_in_bush` | yes | no |
| injury | **no** | yes (`snapshots[t].injury_level`) |
| animal positions | **no** (only `dist_per_predator` / `dist_per_neutral`, which carry a documented one-step staleness bug) | yes (`snapshots[t].animal_pos`), but no class labels in the file |
| animal type | no | no (must be re-derived from the config) |
| damage per step | **no** | **no** |
| damage source (rock / trap / predator) | only `hit_predator`; **no trap flag, no rock flag** | **no** |
| newly entered cell | derivable from `agent_pos` | derivable |

Keys found in the real `.npz`: `agent_pos, action, ate_food, agent_in_bush, dist_per_predator,
dist_per_neutral, hit_predator, hit_neutral, nociception (always 0), termination_reason, length, seed`.
Keys in the real `.rec.gz`: `version, episode_index, train_episode, seed, snapshots, obs, true_obs,
actions, rewards`; snapshot keys `agent_pos, satiation, nutrition, injury_level, rest_streak, res_pos,
res_active, animal_pos, obs_pos`. The dwell-sweep pipeline additionally deletes recordings after
scoring. **Verdict: insufficient for readouts (a), (b) and the surprise response.**

**(b) The trajectory store (`scripts/eval/traj_collect/collect_trajectories.py`).** Real store
inspected: `results/trajectories_hvsmell/20261001-002402_rppo_hv1ch_t1none_s42/10000038/cfde8dd044/`
(level-05 world with rocks, traps, two predators, two rabbits; collected on an RTX 3090 in GPU mode).
Per-step columns include `action, rested, agent_in_bush, injury_level, damage, hit_predator,
hit_hiding_predator, ate_food, agent_row/col, animal_row/col, res_row/col/active, obs_row/col`; the
manifest carries `animal_classes` (`predator`/`neutral`), `animal_is_damaging`, `res_type`
(0 food, 1 hidden trap), `obstacle_names` (`rock`, `bush`, …), `obs_damage`, `res_damage`, and the
episode table carries `animal_active` and `obs_active`.

The environment's `info` dict has per-source damage (`damage_predator`, `damage_hiding_predator`,
`damage_obstacle`, `src/environment/core.py:1190-1198`) but the store saves only the total. Whether the
source is still recoverable was tested on shard `steps_00000` (1,322,735 rows) with the script in
Appendix A:

| Quantity | Count |
|---|---:|
| steps with damage > 0 | 29,094 |
| … with `hit_predator` | 5,778 |
| … with `hit_hiding_predator` (trap) | 5,874 |
| … with the agent on an active rock cell | 17,670 |
| … with **no** identifiable source | **0** |
| trap and rock on the same step | 0 (reset placement resolves overlaps, `core.py:1461`) |
| predator and rock on the same step | 150 (excluded by the design's event rule) |
| on an active rock cell with **no** damage (t ≥ 1) | 0 |
| rock-only damage range | 1.0002 – 4.9999 (config 1–5) |
| trap-only damage range | 15.001 – 44.999 (config 15–45) |
| rock-damage steps on a newly entered cell / standing still | 8,017 / 9,503 |
| episodes starting on a rock (t = 0, no damage recorded at t = 0, arrival convention) | 484 |

**Verdict: the trajectory store is sufficient; the source is exactly recoverable from flags plus
positions, and "newly entered" from the position change between rows t−1 and t. No recorder change
is needed.** The extraction code still carries a guard (Design §D3) that counts and fails loudly on any
damage step without a unique source, so a future world where trap and rock can share a cell cannot be
silently misattributed.

Consequence for item (v) of the request: the block-extension driver wraps the **collector**, not
`eval_rollout.py --record`. The collector already has everything (v) needs: fixed episode blocks, seed
`seed_base + i` per episode, bit-identical resume, a GPU mode at about 460 episodes/s on an RTX 3090
(measured: `[collect] DONE: 1000000 episodes, 200 blocks, 2178.1s (459.1 eps/s)` in the hvsmell
collection logs), a strict restore check against the checkpoint, and a manifest that records which
world and card produced it. This is Open Question 1.

### A2. Existing analysis code to promote

`tmp/20261011_foraging_deaths/predator_deaths.py` (163 lines, gitignored) reads trajectory-store shards
and computes, per store: deaths by cause, for each injury death the source of the last damaging step
(`visible` = animal predator, `hidden` = the trap, `other` = rock), the activity state at that step
(`bush`, `out_ate20` = state (i), `out_toward` = state (ii), `out_other` = state (iii)), and the steps
and predator hits per state. `summarize.py` (40 lines) prints the table. Three things must change on
promotion:

1. **The trap is not a predator in this design.** The old script's "predator deaths" are
   `visible + hidden + both`, i.e. they include trap deaths (the trap's resource type is named
   `hiding_predator`). Readout (a) in [[LOOKALIKE_HALF_FACTORIAL_L05]] is about the hunting animal
   (group A changes it; the trap belongs to groups C and D). The promoted code reports animal-predator
   deaths and trap deaths separately, and readout (a) uses animal-predator deaths only.
2. **Time shares** per state are added (share of out-of-bush steps in each state), as the design
   requires beside every death share.
3. **Per-episode output.** The old script sums per shard; the bootstrap needs per-episode counts.

The old script's state definitions are kept exactly (eating-recent includes the current row; "heading
to food" uses food active on the previous row and `res_type == 0` only — the KNOWN_BUGS row
"Simulation study measured distance to food with hiding predators counted as food" is the hazard it
already avoids). A golden check (Checkpoint C2) proves the promoted code reproduces the old script's
numbers on one real store before any new number is believed.

### A3. Test scenes for readout (c): the world-1 builder is hard-wired

`configs/environment/experiment/behavior_probes/lookalike/generate_lookalike_variants.py` (111 lines)
writes copies of the replication's probe scenes with constants typed into the file: smell
`[0, 0.6, 0.6, 0, 0]`, predator `detection_range 3`, `attack_range 3`, `attack_success_rate 0.5`, one
food item of `max_consumption 6` at `[2, 5]`. It never reads the training world. Worlds 2–8 differ in
exactly those values (predator ranges `[2, 3]`, food 9 bites with `body.food_nutrition_gain 16`,
masked rocks and traps), so a generalised builder that **reads the world config** is needed (user
decision 2026-10-13: scenes are rebuilt per world). `experiment-designer` is specifying the seven scene
sets in parallel; this plan covers only the builder and its proof of equivalence on world 1.

The test-scene sweep itself (`scripts/eval/dwell_sweep/run_sweep.py`) takes one result folder per run
(`runs[].path`), so it cannot see the checkpoints of a run that was stopped and resumed into a second
folder (A4).

### A4. Six runs have their checkpoints split across two folders

From the launch manifest and the folders on disk (2026-10-13):

| Run | Original folder: last checkpoint | Resumed folder: first / last checkpoint |
|---|---|---|
| w7 ordinary | `20261012-150902_…`: 2200046 | `20261012-203757_…`: 2200159 / 5600051 (still training) |
| w8 modulated | `20261012-150919_…`: 1800048 | `20261012-203804_…`: running |
| w3 modulated | `20261012-151320_…`: 1800026 | `20261012-234627_…`: 2200034 so far |
| w4 ordinary, w2 modulated, w6 modulated | 2000000 / 2200035 / 2400022 | queued in the resume watcher, no folder yet |

Ground truth for the link is the resumed run's own `models/provenance.json`, whose `argv` contains
`--load-checkpoint results/JAX_RecurrentPPO/<original folder>/models`. Checkpoint names are the
training episode counter (one save about every 200,000 episodes); "the 2 M checkpoint" therefore
means the saved checkpoint nearest to 2,000,000. The resumed folder's first save (e.g. 2200159) comes
about 100 episodes after the restore point (2200046); keeping both would put two nearly identical
checkpoints into the whole-training series. The saved `config.yaml` of the original and resumed w7
ordinary folders are identical (checked with `diff`).

### A5. Live constraints for the watcher

- The resume watcher `tmp/20261012_hf_resume_watch/watch.py` polls every 15 minutes, needs a card free
  on two checks in a row, launches queued resumes from `queue.json` (three entries on 2026-10-13), and
  treats any diary row `| NNN:G | running` as a claimed card **except rows containing the string
  `lookalike_hf`** (its own runs). Eval diary rows must therefore never contain `lookalike_hf`, and
  must use the same `| NNN:G | running` form so the resume watcher sees eval cards as taken.
- `scripts/lab/gpu_status.py --free` lists free cards; the project rule is that GPU pre-flight also
  checks the diary and `pgrep` (processes in their CPU start-up phase are invisible to `nvidia-smi`).
- Card models: only RTX 3090, RTX 4090 and RTX 6000 Ada (user). The collector's manifest refuses to
  extend a store on a different card model than it was started on (`compute_device_kind` is
  manifest-guarded), so one run's whole collection must stay on one card (Design §D5).
- `scripts/eval/traj_collect/collect_worker.sh` sets no `CUDA_VISIBLE_DEVICES`, so every GPU worker
  lands on GPU 0 (README "GPU limitation"). The new driver calls the collector itself with
  `CUDA_VISIBLE_DEVICES` set, and does not use `collect_worker.sh`.

### A6. Known-bug rows that touch this work (grep of `docs/develop/active/issues/KNOWN_BUGS.md`, 2026-10-13)

| Row (line) | Relevance | Handling in this plan |
|---|---|---|
| "A trajectory store replays exactly only under the matmul precision mode it was collected in" (139) | New stores record card and mode; resume refuses a card change | One run's collection stays on one card (§D5); stores are re-collected, not extended, if a job moves |
| "Two checkpoints of the same run collected on one node would write to the same collector log file" (144) | Our driver collects several checkpoints of one run on one node with identical block ranges | The driver does not use `collect_worker.sh`; it names each log `<run>_<ckpt>_<blocks>.log` |
| "The trajectory-collection launcher's end-of-run check inspects every store in a run's folder" (143) | False "invalid" reports when two batches write to one run | The driver validates only the store directories it wrote, by explicit path |
| "A finished run's own saved config stops loading once a new key becomes mandatory" (123) | Fast-heal runs (2026-10-05) must load under current code | Checkpoint C6 runs the collector's own loading path on all six before any σ number |
| "The hiding-drivers cross-tabs bin injury from the same step as the bush outcome" (505) and its siblings (314, "Time-control analysis pass bins by the current value", 504) | Conditioning on the same row as the outcome is a known error class here | Conditions are read on the decision row t−1, outcomes on row t (§D3, Open Question 3) |
| "Simulation study measured distance to food with hiding predators counted as food" (186) | Trap slots look like food slots by position | Food = `res_type == 0` only |
| "Single-config resume pairs restored memory with fresh worlds" (104) and "Resume silently restored nothing" (445, fixed) | Resumed runs: was the checkpoint really restored? | Checkpoint C5 compares weights across the resume seam |
| Store schema "Deliberately not recorded": `dist_per_predator` carries a one-step staleness bug | Animal distances | Distances are recomputed from recorded positions; the env's distance fields are never used |

---

## Implementation Plan

### Design

**Data flow.**

```
run manifest (YAML) ──► run_lineage (merge split folders, pick 2/4/6/8/10 M checkpoints)
        │
        ├─► rollout_blocks.py ──► collect_trajectories.py (GPU, one card, 2,000-episode blocks)
        │        ▲      │                       results/trajectories_<name>/<folder>/<ckpt>/<env_fp>/
        │        │      ▼
        │        └── half_factorial/minimums.py (counts only) ── extend until met or 20,000
        │
        ├─► build_world_scenes.py (per world, once, before the sweep) ──► configs/…/behavior_probes/<set>/
        ├─► run_sweep.py (multi-folder runs) ──► results/eval/avoidance/<output_dir>/…/<scene>.csv
        │
        └─► half_factorial/extract.py ──► per-episode statistics (parquet) ──► readouts.py
                                                                        (values, bootstrap SEs, minimums)
eval_watch.py: decides WHEN and WHERE each run's job (rollouts → scene sweep → extraction) runs.
```

#### D1. Run manifest and lineage (run-agnostic input)

Every tool takes a **run manifest** YAML; nothing is hard-wired to this experiment:

```yaml
name: half_factorial_l05                    # used in output folder names; must not contain "lookalike_hf"
out_root: results/trajectories_half_factorial_l05
episodes_target: 10000000                   # a run is "finished" when its merged newest checkpoint >= this
checkpoints_m: [2, 4, 6, 8, 10]             # target checkpoints, in millions of training episodes
extend_at_m: [6, 8, 10]                     # checkpoints extended in blocks until minimums are met
block_episodes: 2000
cap_episodes: 20000
seed_base: 1000000                          # same for every run and checkpoint
runs:
  - id: w1_t1none_s42                       # short id; must not contain "lookalike_hf"
    root: results/JAX_RecurrentPPO/20261009-175459_rppo_lookalike_l05_t1none_s42
    world: 1                                # free label for the analysis (world number, "fh", …)
    agent: ordinary
    scene_sets: [<designer's world-1 sets>] # empty list = rollouts only (fast-heal σ runs)
    training: {node: 110, gpu: 0}           # card it trained on (eligibility for the watcher); null for old runs
```

`root` is the run's **first** folder. `src/utils/run_lineage.py` resolves the rest:

- Scan `results/JAX_RecurrentPPO/*/models/provenance.json`; a folder whose `argv` has
  `--load-checkpoint <root>/models` is a child. Follow recursively (a resumed run can be resumed again).
- Children with **no** numeric checkpoint folder (an aborted start, e.g. the w3 modulated attempt on
  node 102 at 20:36) are ignored with a warning.
- Merge: all parent checkpoints ≤ the restore point (= the parent's newest checkpoint; assert that the
  parent has none after it), then the child's checkpoints **strictly greater than restore point +
  checkpoint_frequency / 2** (drops the immediate post-resume save such as 2200159; each dropped step
  is logged and written to the lineage record). `checkpoint_frequency` is read from the parent's saved
  `config.yaml` (`training.checkpoint_frequency`, mandatory; 200000 here).
- Assert that the saved `config.yaml` of parent and child are equal after removing the keys that only
  the command line sets (`load_checkpoint`, `wandb.resume_id`, `tag`, `wandb.name`, timestamps). Any
  other difference is an error.
- `pick(target)` returns the merged checkpoint with the smallest |step − target|; ties go to the
  earlier step; |step − target| > checkpoint_frequency / 2 is an error. The returned record carries
  `(folder, step)` and is written into every output so the analysis reports the step actually used.
- `finished(lineage)` = merged newest step ≥ `episodes_target`.

#### D2. Rollout driver with block extension — `scripts/eval/rollout_blocks.py`

For one manifest run on one card:

1. For each target checkpoint `T` in `checkpoints_m`: `(folder, step) = pick(T)`.
2. Call the collector as a subprocess with `CUDA_VISIBLE_DEVICES=<g>`:
   `collect_trajectories.py --run <folder> --checkpoint <step> --out-root <out_root> --episodes <cap>
   --shard-episodes <block> --seed-base <seed_base> --blocks <b>:<b+1> --obs-precision float32
   --device gpu`. Declaring `--episodes = cap` (20,000) from the first call keeps the manifest's
   `n_episodes` constant, so later blocks extend the same store (the collector refuses a manifest
   change). Logs go to `<out_root>/_logs/<run id>_<step>_<b>.log` (avoids KNOWN_BUGS row 144).
3. After each block, run `half_factorial/extract.py` on the new shard only (per-episode statistics
   are appended per block) and `minimums.py` on the accumulated statistics.
4. At targets not in `extend_at_m`: stop after block 0. At targets in `extend_at_m`: add blocks while
   any minimum is unmet and blocks < cap / block (10). The decision uses **counts only** (contributing
   episodes, deaths per state), never readout values, so the stopping rule cannot steer a value.
5. Validate each store it wrote with `validate_store_structure(store, expected_blocks=range(n))`,
   `validate_store_shapes`, `validate_store_draws` — by explicit path only (KNOWN_BUGS row 143).
6. Write `<out_root>/<run id>/index.json`: per target `{folder, step, store_dir, blocks, episodes,
   minimums: {readout: met|short + counts}, card, started, finished}`. Re-running is idempotent:
   completed blocks are skipped by the collector, and the index is rebuilt from the stores on disk.

Card rule: one invocation handles all checkpoints of one run on one card. If a job dies part-way and
the next job lands on a different card model, the driver deletes that run's partial stores
(only stores listed in its own index) and starts again; with 2–20 minutes per run (§Compute) that is
cheaper than special-casing.

#### D3. Readout extraction — `scripts/analysis/studies/half_factorial/`

All extraction is per shard → **per-episode statistics** (one parquet row per episode), so the
bootstrap (D4) resamples episodes by summing their rows. Row convention is the store's ARRIVAL
convention (`docs/environment/TRAJECTORY_STORE_SCHEMA.md` §1): row t holds the state after the step
and the action that produced it.

Shared helpers (`_store.py`): read a shard's needed columns; build per-row arrays of: episode start
index; active predator / rabbit slots (from `animal_classes` + episode `animal_active`); Manhattan
distance from the agent to the nearest active predator and nearest active rabbit (recomputed from
positions); active rock cells (`obstacle_names == "rock"` and episode `obs_active`); active food slots
(`res_type == 0`).

**Conventions (decision row).** A condition the agent could react to is read on row t−1 (what it
observed when it chose the action that produced row t); the outcome is read on row t. This applies to
injury, animal distances and the hazard-event filters. It is the project's standard after the
contemporaneous-binning bugs (A6) and is Open Question 3 because the design text does not state it.

| Quantity | Definition on rows (t ≥ 1 unless stated) |
|---|---|
| in bush | `agent_in_bush[t]` |
| healing step | in bush **and** `rested[t]` **and** `injury_level[t−1] ≥ 1` |
| hiding step | in bush and not a healing step |
| activity state (out of bush only) | (i) `ate_food` in rows (t−20, t] (row t included, as the old script); (ii) not (i) and the move t−1→t reduced the distance to the nearest food active at t−1; (iii) otherwise |
| predator death | episode ends with `termination_reason == 4` (injury) and the last row with `damage > 0` has `hit_predator`; its state is the activity state of that row (bush deaths kept as a separate count) |
| trap death | the same with `hit_hiding_predator` and not `hit_predator` |
| rock death | last damaging row is a rock-source row |
| damage source of a row with `damage > 0` | predator if `hit_predator`; else trap if `hit_hiding_predator`; else rock if the agent stands on an active rock cell; **anything else raises** (guard; also raises if trap and rock coincide) |
| hazard-hit event | rock- or trap-source row t with t ≥ 1, position at t ≠ position at t−1 (newly entered), `hit_predator[t]` false |

**(i) `foraging_deaths.py`** (promoted `predator_deaths.py`) — per episode: out-of-bush steps per state
(i)/(ii)/(iii), bush steps, animal-predator hits per state, predator deaths per state, trap deaths,
rock deaths, length, termination reason. Run-level outputs: time share of each state (steps in state ÷
out-of-bush steps), predator hits and deaths per 1,000 steps by state, endings mix (share ending at
full length 500, by predator, trap, rock, starvation, over-eating, cold/heat), mean survival steps,
and **readout (a)**:

$$
\log \mathrm{RR}_{\mathrm{(i)}} = \log \frac{D_{\mathrm{(i)}} / S_{\mathrm{(i)}}}{D_{\mathrm{(iii)}} / S_{\mathrm{(iii)}}}
$$

with D = predator deaths and S = steps in the state, summed over episodes; the same for state (ii)
against (iii). Undefined when either D is 0 (then the value is reported as "too few events", never 0).
A `--legacy` flag reproduces the old script's JSON (trap counted with the predator) for the golden
check; it is never used for readouts. `summarize_foraging_deaths.py` (promoted `summarize.py`) prints
the table from the run-level JSON, with time shares added.

**(ii) `hiding_healing.py`** — per episode: hiding steps, healing steps, bush steps (context only), and
for **readout (b)** the qualifying rows (decision row: `injury_level[t−1] < 1`, nearest active rabbit
at t−1 within 2, no active predator at t−1 within 4) and how many of them are in a bush at t. Readout
(b) = Σ in-bush qualifying rows ÷ Σ qualifying rows. Also reported: (b) restricted to hiding steps
(the design calls bush time at injury < 1 caution; at injury < 1 a bush row cannot be a healing row by
the definition above, so the two coincide — reported once, with that note).

**(iii) `hazard_events.py`** — one row per hazard-hit event (event table) plus per-episode sums:

- windows: pre = rows t−20 … t−1, post = rows t+1 … t+20;
- flags: `pre_complete` (t ≥ 20), `post_complete` (t + 20 ≤ T), `cut_by_death` (episode ends before
  t + 20 by death), `cut_by_time_limit` (ends at the 500-step limit before t + 20);
- primary response = hiding-step share(post) − hiding-step share(pre) on complete windows; a
  truncated-window version (available rows only) beside it;
- secondary responses: change in healing-step share, cells moved in the post window (count of rows
  with a position change), re-entry of the same cell within the post window;
- **readout C filters (R3)**: `injury_level[t−1] < 1` and no active predator within 3 cells in any of
  rows t−20 … t−1 (needs `pre_complete`);
- per run: counts of all events, kept events, share kept, truncation counts and shares, overlapping
  events (another hazard hit inside the post window — kept, counted);
- **trap-vs-rock difference-in-differences input**: events with the event definition but **without**
  the R3 filters (otherwise rock events would all sit in the lowest injury bin and trap events in
  higher ones, leaving no overlap), binned by `injury_level[t]` (injury after the hit) in 10-point bins.
  Per bin: n and mean response for trap and for rock. Per run: (trap − rock) = Σ_bins w·(m_trap − m_rock)
  ÷ Σ w with w = n_trap·n_rock / (n_trap + n_rock) over bins where both n ≥ 1; overlap per bin is
  written out. The C+ minus C− difference is formed by the analysis, not by this tool.

**`readouts.py`** — CLI: `--index <out_root>/<run id>/index.json` (or a list), runs extraction where
the per-episode file is missing or older than the store, then writes
`results/analysis/half_factorial/<name>/<run id>/<step>.json`: every readout value, its bootstrap SE,
contributing-episode counts, minimum flags, episodes used, the `(folder, step)` actually used, and the
store directories and their manifest `collection_git_sha`.

**Readout (c)** is not computed from stores. `readouts.py --scenes` reads the per-run sweep CSVs and
applies the lookalike pilot's estimator (per-checkpoint contrasts; newest-20 mean with the
lag-1-autocorrelation-corrected t-interval; whole-training share of positive checkpoints and largest
jump). The estimator code is moved from `scripts/analysis/studies/lookalike_pilot/build_page.py`
(`contrast`, and the newest-20 logic it uses) into `half_factorial/scene_estimator.py` and imported back
by `build_page.py`, so there is one implementation (Checkpoint C8 proves the pilot page's numbers are
unchanged).

#### D4. Standard errors and minimums — `bootstrap.py`, `minimums.py`

- `bootstrap.py`: given the per-episode table of one run × checkpoint and a readout function of
  column sums, draw 1,000 resamples of episode indices with replacement (NumPy `default_rng(seed)`,
  seed recorded), recompute, return the standard deviation of the replicates, plus the count of
  replicates where the readout is undefined (reported; excluded from the SD).
- `minimums.py` (the same function serves the driver and the readout CLI):
  - every readout: ≥ 50 contributing episodes ((a): episodes with ≥ 1 out-of-bush step in states (i)
    and (iii); (b): ≥ 1 qualifying row; C: ≥ 1 kept event with complete windows);
  - readout (a): ≥ 100 animal-predator deaths, ≥ 10 in state (i) and ≥ 10 in state (iii);
  - returns per-readout `met` / `short` with the counts. A run still short at the cap is written as
    "too few events" and the analysis treats its group as unresolved (pass rule item 4).

#### D5. Test-scene builder — `scripts/eval/build_world_scenes.py`

```
build_world_scenes.py --spec <scene-set spec YAML> [--check]
```

The spec (written by `experiment-designer`, one per world and scene set):

```yaml
world: configs/environment/experiment/basic/lookalike_hf_w2_newAD_10x10.yaml
sources: [behavior_probes/injury_grid/neutral_clean, behavior_probes/thermal/neutral_clean]
keep: []                                   # optional scene-name prefixes
out: configs/environment/experiment/behavior_probes/<set name>
copy_from_world:                           # read from the RESOLVED world config (extends chain applied)
  - {entity_tag: pred,   fields: [properties, detection_range, attack_range, attack_success_rate]}
  - {entity_tag: rabbit, fields: [properties]}
  - {resource: food,     fields: [max_consumption, properties, visual_properties]}
  - {key: body.food_nutrition_gain}
overrides:                                 # fixed values written after copying
  entities: {"*": {properties_std: [0, 0, 0, 0, 0]}}
  resources: {food: {count: 1, spawn_area: [[2, 5], [2, 5]], regeneration_delay: 0}}
```

Behaviour: resolve the world through the same `extends:` loader the trainer uses; for each source
scene write `extends: <source>` plus only the copied and overridden blocks (as the world-1 generator
does); refuse if a source scene already has resources (as today); write a header naming the spec and
the world. `--check` (i) re-loads every output with `load_env_params` (the eval script's loader) and
asserts that every copied value equals the world's resolved value, (ii) asserts that each output
differs from its source only in the declared blocks. The world-1 generator is left untouched (its
output is frozen); equivalence is proved by Checkpoint C7.

#### D6. Test-scene sweep across split folders — `scripts/eval/dwell_sweep/run_sweep.py`

`runs[]` entries gain an optional `lineage: true`; when set, `path` is the root folder and the
checkpoint list comes from `run_lineage` (each checkpoint carries its own folder into the worklist
line via `checkpoint_path`). Without the key, behaviour is byte-for-byte unchanged (existing specs and
`basic_behaviour/probes.py`, which imports `list_checkpoints` and `resolve_run_dir`, are unaffected).
The watcher writes each sweep spec on the fly under `<sweep output_dir>/_specs/` from the manifest
(`scene_sets`), with `nodes: [<node>]` and `npar` from the watcher (Open Question 2); `run_sweep.py`
already copies the spec into `_provenance/`.

#### D7. Eval watcher — `scripts/eval/eval_watch.py`

```
eval_watch.py --manifest <runs YAML> --resume-queue tmp/20261012_hf_resume_watch/queue.json
              [--interval-min 10] [--dry-run] [--once]
```

Every interval:

1. **Which runs are ready.** A manifest run is ready when `finished(lineage)` is true **and** no
   training process is alive for it: `ssh <node> pgrep -af "train.py.*--tag[ =]\"?<tag>"` on every
   node in 101–114 (the tag alone would also match eval jobs whose command lines contain the folder
   name). Runs already marked done in the watcher state are skipped. A run whose process is gone but
   whose newest checkpoint is below the target is reported as **stalled** in the log and never
   evaluated (relaunching is the user's call).
2. **Which cards are eligible.** A card is eligible only if (a) a manifest run trained on it and that
   run is now finished with no process (cards freed by **our** finished runs, user rule; the card list
   comes from the manifest's `training:` fields plus the resume watcher's `launched_*.json` files), (b)
   it is an RTX 3090, RTX 4090 or RTX 6000 Ada (same model match as `watch.py`), (c) it is listed by
   `scripts/lab/gpu_status.py --free`, (d) no running row in today's or yesterday's diary claims it,
   **except** rows of manifest runs that step 1 has proven finished (their training rows may never have
   been flipped to done), (e) `pgrep -af "cuda:<g>"` on the node shows no process, and (f) it passed
   (a)–(e) on the previous check as well (two checks in a row, as the resume watcher).
3. **Priority to queued resumes.** Let q = number of entries in `queue.json` (0 if the file is gone).
   If q > 0 and eligible cards ≤ q: idle. Otherwise sort the eligible cards as `watch.py` does (by node,
   then GPU), leave the first q to the resume watcher, and use the rest. (`watch.py` considers every free
   card, not just ours, so leaving it the first q of ours is sufficient, not necessary; the rule errs
   toward the resumes.)
4. **Pack node first.** Assign ready runs to the remaining cards, filling both cards of one node
   before the next. Order of runs: manifest order.
5. **Launch** each job with the existing CIFS-bypass pattern (write a job script to the node's `/tmp`
   over SSH, start it with `./run_command.py --no-tail --log <log> <node> "bash <script>"`). The job
   script runs, in order: `rollout_blocks.py` (GPU), the run's scene sweeps (`run_sweep.py` with the
   generated spec), `readouts.py`. It traps EXIT to write a done/failed marker.
6. **Diary.** Before launch: `diary_append.py training-start --tag hfeval_<run id> --node N --gpu G
   --cell "eval: rollouts, scenes, readouts" --wandb - --doc docs/develop/active/hypervigilance/HALF_FACTORIAL_EVAL_TOOLING.md`;
   on the marker: `training-done`. The watcher asserts that the row text it is about to write does not
   contain `lookalike_hf` (the resume watcher would ignore it) and that it matches the resume
   watcher's regex `\|\s*(\d{3}):(\d)\s*\|\s*running`.
7. **State** in `<out_root>/_watch/state.json` (runs: pending / running(node, gpu, pid file, log) /
   done / failed; cards in use). A failed job is not retried automatically; it is logged and left for a
   person.

`--dry-run --once` prints, for the live cluster, the ready/stalled runs, each card's eligibility with
the reason it failed, the idle decision, the job script and the diary command, and launches nothing.

### File Changes

New files (all paths from the repo root; Python files under `scripts/<a>/<b>/` walk three levels to the
root, under `scripts/<a>/<b>/<c>/<d>/` five; follow the depth rule in `SCRIPTS_DEPENDENCY_MAP.md` §0):

| File | Purpose |
|---|---|
| `src/utils/run_lineage.py` | D1: lineage discovery, merge, `pick`, `finished`, config-equality assert |
| `scripts/eval/rollout_blocks.py` | D2: block-extension collection driver |
| `scripts/eval/build_world_scenes.py` | D5: world-reading scene builder |
| `scripts/eval/eval_watch.py` | D7: eval watcher |
| `scripts/analysis/studies/half_factorial/_store.py` | D3 shared shard helpers |
| `scripts/analysis/studies/half_factorial/extract.py` | per-shard → per-episode statistics (calls the three modules below) |
| `scripts/analysis/studies/half_factorial/foraging_deaths.py` | (i), promoted from `tmp/20261011_foraging_deaths/predator_deaths.py` |
| `scripts/analysis/studies/half_factorial/summarize_foraging_deaths.py` | promoted `summarize.py` |
| `scripts/analysis/studies/half_factorial/hiding_healing.py` | (ii) |
| `scripts/analysis/studies/half_factorial/hazard_events.py` | (iii) |
| `scripts/analysis/studies/half_factorial/bootstrap.py`, `minimums.py` | D4 |
| `scripts/analysis/studies/half_factorial/scene_estimator.py` | readout (c) estimator moved out of `lookalike_pilot/build_page.py` |
| `scripts/analysis/studies/half_factorial/readouts.py` | CLI writing per run × checkpoint JSON |
| `configs/eval_sweeps/half_factorial/runs_l05.yaml` | the manifest: 14 new runs, world 1 seeds 42 and 43 (4 runs), six fast-heal level-05 runs (rollouts only, `scene_sets: []`). Values from the experiment doc's manifest and §A4; `experiment-designer` fills `scene_sets` |
| `tests/utils/test_run_lineage.py` | fake folder trees: single, one resume, two resumes, aborted child, mismatched config, post-resume drop rule, `pick` ties and out-of-range |
| `tests/analysis/test_half_factorial_readouts.py` | hand-built tiny stores (written with `src/utils/trajectory_store.build_table`) with known answers for every row of the D3 table, the source guard raising, truncation flags, the R3 filters, DiD weights, bootstrap on a constant readout (SE 0), minimums |
| `tests/scripts/test_eval_watch_decisions.py` | the decision function of D7 with mocked cluster / diary / queue inputs: queue priority, two-check rule, pack-node-first, diary-row regex and the `lookalike_hf` assert, finished-but-diary-says-running |
| `tests/scripts/test_build_world_scenes.py` | builder on a temporary world + source scene; `--check` catches a wrong copied value |

Modified files:

| File | Change |
|---|---|
| `scripts/eval/dwell_sweep/run_sweep.py` | `build_groups` (around lines 210–282) and `write_worklist` (300–318): optional `lineage: true` per run (D6). `resolve_run_dir`, `list_checkpoints`, `checkpoint_path` keep their signatures |
| `scripts/eval/dwell_sweep/README.md` | document `lineage: true` |
| `scripts/analysis/studies/lookalike_pilot/build_page.py` | import the estimator from `half_factorial/scene_estimator.py` instead of defining it |
| `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` | **required by its Maintenance Contract**: §1a rows for the new bare-name/same-folder imports (`readouts.py` → its siblings; `lookalike_pilot/build_page.py` → `half_factorial/scene_estimator.py`; `eval_watch.py` → `rollout_blocks.py` if imported); §1c rows for the three new test files; §3 rows for every new file and the changed `run_sweep.py`; §4 a new cluster "half-factorial eval" (`eval_watch.py`, `rollout_blocks.py`, `half_factorial/*`, `run_sweep.py`, `traj_collect/collect_trajectories.py` as a subprocess callee, `scripts/lab/gpu_status.py` and `scripts/claude/diary_append.py` as subprocess callees) |
| `scripts/eval/traj_collect/README.md` | one paragraph: `rollout_blocks.py` as a second caller, and how it avoids the GPU-0 and log-clobber limitations |

No change to `src/environment/`, the trajectory-store schema, `collect_trajectories.py`,
`eval_rollout.py`, any training config, or the critical-settings registry. No new config key in the
environment schema, so `CONFIG_GUIDE.md` and `02_config_schema.md` are unaffected. The `tmp/` scripts
stay as they are (gitignored).

Not in this plan: the seven scene-set specs (experiment-designer), the group-contrast and σ arithmetic
of the pass rule (experiment-analyzer reads the per-run JSON), any change to `watch.py`.

### Compute estimate (per run)

| Step | Typical (minimums met at 2,000 episodes) | Worst case (cap reached at 6, 8 and 10 M) |
|---|---|---|
| Rollouts, RTX 3090 GPU mode, ~460 episodes/s | 10,000 episodes ≈ 25 s + 5 collector start-ups × ~40 s ≈ **4 min** | 64,000 episodes ≈ 2.3 min + 32 start-ups ≈ **24 min** |
| Store size (≈ 44 KB per episode, measured on the level-05 store) | ≈ 0.45 GB | ≈ 2.8 GB |
| Extraction + minimum checks (CPU, 4 processes) | ≈ 2–5 min | ≈ 15 min |
| Scene sweeps, ~50 checkpoints × the run's scene sets (world-1 pilot measured ≈ 108 core-seconds per checkpoint for the 30-scene injury grid at 30 episodes) | ≈ 3 core-hours if the designer's sets resemble the pilot's four → ≈ 45 min at 4 processes | scales with the designer's scene count |
| **Card held per run** | **≈ 1 h** (hf and world-1 runs); **≈ 10 min** (fast-heal runs, no scenes) | ≈ 1.5–2 h |

All 24 manifest runs: about 18 card-hours typical, 40 worst case; disk about 11 GB typical, 67 GB
worst case under `results/` (gitignored, NAS).

---

## Checkpoints

Each check names what it fails on. "Real" means files produced by an actual run or store, not a
reload of the source that should produce them.

- [ ] **C1 — Unit tests** (`tests/utils/test_run_lineage.py`, `tests/analysis/test_half_factorial_readouts.py`,
  `tests/scripts/test_eval_watch_decisions.py`, `tests/scripts/test_build_world_scenes.py`) pass. Each
  readout test must be shown to **fail** when its definition is perturbed (e.g. reading injury on row t
  instead of t−1 changes the expected hiding count) — record one such mutation per module in the
  Implementation Report. Fails on: any definition in D3 implemented differently from the table.
- [ ] **C2 — Golden check of the promoted foraging-death code.** Run `foraging_deaths.py --legacy` on
  the store `results/trajectories_hvsmell/20261001-002402_rppo_hv1ch_t1none_s42/10000038/cfde8dd044`
  and compare with that store's entry in `tmp/20261011_foraging_deaths/predator_deaths.json`
  (`hvsmell/rppo_hv1ch_t1none_s42`): `steps`, `hits`, `reasons`, `fatal.{visible,hidden,both,other}`
  equal exactly. Then the non-legacy run: animal-predator deaths + trap deaths + "both" equal the legacy
  "predator" total. Fails on: any drift in state or death attribution during promotion.
- [ ] **C3 — Source guard on a real store.** `extract.py` over all 200 shards of the same store raises
  nothing, and its counts of predator / trap / rock damage rows on shard 0 equal Appendix A's table.
- [ ] **C4 — Hand check of 20 events.** For 10 rock and 10 trap events drawn at random from a world-1
  store, print rows t−2 … t+2 (position, damage, flags, injury, rock and trap cells) and check by eye
  that each is a first damage step on a newly entered cell; paste the printout into the Implementation
  Report. Use `scripts/eval/trajectory_story.py` or a raw dump. Fails on: an off-by-one between the
  arrival convention and the event rule.
- [ ] **C5 — Checkpoint merge on one resumed run (w7 ordinary).** (a) `run_lineage` lists the
  original folder's checkpoints up to 2200046, drops 2200159, then the resumed folder's from 2400036
  on; (b) the restore-point assert holds; (c) **weights across the seam**: the relative parameter
  distance between 2200046 (original) and the resumed folder's 2200159 is far smaller than between
  2000064 and 2200046 (two ordinary consecutive checkpoints) — read from the checkpoint files, not from
  the training log. This proves the resumed folder continues from the original (the KNOWN_BUGS "resume
  restored nothing" class). (d) The collector run on `pick(4 M)` writes its store under the resumed
  folder's name and `pick(2 M)` under the original's, with the same `env_fp`.
- [ ] **C6 — Fast-heal configs load through the collector.** For each of the six fast-heal level-05
  runs, run `rollout_blocks.py` at the 2 M target only (one 2,000-episode block). All six stores
  validate. Fails on: the saved-config mandatory-key wall (KNOWN_BUGS row 123).
- [ ] **C7 — Scene builder equivalence on world 1.** A world-1 spec (lookalike world, the four
  frozen source folders, copy/override lists equivalent to the old generator's constants) written to a
  temporary folder produces files that load (`load_env_params`) to the same params as the frozen
  `configs/environment/experiment/behavior_probes/lookalike/` scenes, scene by scene (compare the
  resolved env-params pytree leaves). Fails on: the builder silently missing a field the old one set.
- [ ] **C8 — Scene sweep path and estimator unchanged.** (a) `run_sweep.py` with `lineage: true` on
  world 1 seed 42 (one folder, so the lineage is trivial), the C7 scenes in a fresh output folder,
  `--max-checkpoints 3`: the CSV rows equal the pilot's rows in
  `results/eval/avoidance/metrics_history_rppo_lookalike/grid/lookalike_ordinary_s42/` for those three
  checkpoints (deterministic policy, same seeds; if they differ, report the size and the cause before
  going on). (b) `lookalike_pilot/build_page.py` regenerates its page with byte-identical numbers after
  the estimator move. (c) A dry-run of a `lineage: true` spec for w7 ordinary lists worklist lines whose
  checkpoint paths switch folders at the seam.
- [ ] **C9 — End-to-end on the world-1 seed 42 / 43 pair (the main acceptance test).** Run the full
  job (rollouts at 2/4/6/8/10 M with extension, scene sweep, readouts) for the two seed-42 and two
  seed-43 world-1 runs through `eval_watch.py --once` on a real freed card (or, if none is free yet,
  `rollout_blocks.py` + `readouts.py` by hand on a card that passes the same pre-flight). Then verify
  against ground truth, not re-derivation: (a) each store manifest's `resolved_env_config` world
  sections equal the run's own `models/config.yaml` (191 world leaf keys, 0 differ, as in the design's
  reuse check); (b) mean survival steps and the endings mix at 10 M from the store are compared with
  the same run's training-time evaluation in WandB at the nearest step (they differ in policy mode and
  episodes, so report the numbers and the difference; a gap larger than ~20 % of survival steps is
  investigated before sign-off); (c) every readout JSON has a value or an explicit "too few events",
  an SE, and minimum flags; (d) the index lists the episodes actually used per checkpoint.
- [ ] **C10 — Watcher dry-run on the live cluster.** `eval_watch.py --dry-run --once` with the real
  manifest and queue: w5 ordinary (finished 2026-10-12 ~23:35) is listed ready; the queued resumes'
  original folders are "not finished"; with three queued resumes and at most three eligible cards the
  decision is "idle"; the printed diary command contains no `lookalike_hf`. Paste the output.
- [ ] **C11 — Speed.** `run_sweep.py` on one checkpoint of world 1 seed 42 (one scene set) before and
  after the change, same node and npar: wall time within 5 %. The collector is not modified; record
  the eps/s it prints in C9 next to the 459 eps/s reference.
- [ ] **C12 — Maintenance contract.** `SCRIPTS_DEPENDENCY_MAP.md` rows exist for every new and changed
  file; `grep -rn "half_factorial\|eval_watch\|rollout_blocks\|build_world_scenes\|run_lineage" --include=*.py --include=*.md .`
  reconciles with the map.

---

## Open questions for the user

1. **Recorder.** The request named `eval_rollout.py --record` as the base of the block-extension
   driver. It lacks damage and damage source (A1), while the trajectory-store collector has everything
   and is ~460 episodes/s on a 3090. The plan uses the collector and changes no recorder. Confirm, or
   say if you want `eval_rollout.py` extended instead (a recorder change plus a new per-episode format).
2. **Where the test-scene sweeps compute.** The sweep tool runs on CPU. Options: (a) run it on the
   freed card's node with 4 CPU processes while the job holds that card (no code change; ~45 min per
   run; may take a little CPU from a training run on the node's other card); (b) add a GPU mode to the
   sweep worker (a change to `sweep_worker.sh` and `run_sweep.py`, speed unmeasured). The plan assumes
   (a).
3. **Three definitional readings the design text does not fix** (they move numbers; the plan picks
   the first option each time and would ask `experiment-designer` to record them in the design doc):
   conditions (injury, animal distance) read on the step **before** the outcome, as in the project's
   other bug-fixed tools, rather than the same step; rock-hit events need a complete 20-step window
   **before** the hit as well (early events counted and excluded), not only after; the trap-versus-rock
   comparison uses events **without** the "unhurt before the hit" filter (with it, the two kinds of hit
   never share an injury bin).

---

## Implementation Report

> **Implemented by**:
> **Date**:

<!-- developer: record per checkpoint C1–C12 the command, the output, and any deviation. -->

## Verification Report

> **Verified by**:
> **Date**:

| File | Change | Status | Notes |
|------|--------|:------:|-------|
| | | | |

**Conclusion**:

---

## Appendix A — step-0 source check (reproducible)

Run with the project interpreter, argument = a store directory, optional shard number.

```python
import json, sys, numpy as np, pyarrow.parquet as pq, pyarrow.compute as pc
D = sys.argv[1]; sh = sys.argv[2] if len(sys.argv) > 2 else "00000"
m = json.load(open(D + "/_manifest.json")); R, B = m["dims"]["R"], m["dims"]["B"]
tb = pq.read_table(f"{D}/steps_{sh}.parquet")
def mat(c, w): return pc.list_flatten(tb.column(c)).to_numpy(zero_copy_only=False).reshape(tb.num_rows, w)
g = {c: tb.column(c).to_numpy(zero_copy_only=False) for c in
     ["episode_seed", "t", "agent_row", "agent_col", "damage", "hit_predator", "hit_hiding_predator"]}
ep = pq.read_table(f"{D}/episodes_{sh}.parquet", columns=["episode_seed", "obs_active"])
es = ep.column("episode_seed").to_numpy()
oa = pc.list_flatten(ep.column("obs_active")).to_numpy(zero_copy_only=False).reshape(ep.num_rows, B)
o = np.argsort(es); erow = o[np.searchsorted(es[o], g["episode_seed"])]
orow, ocol = mat("obs_row", B), mat("obs_col", B)
rock = np.array(m["obstacle_names"]) == "rock"
ar, ac, t = g["agent_row"], g["agent_col"], g["t"]
on_rock = ((orow == ar[:, None]) & (ocol == ac[:, None]) & rock[None] & oa[erow]).any(1)
dmg, hp, ht = g["damage"] > 0, g["hit_predator"], g["hit_hiding_predator"]
prev = np.maximum(np.arange(len(t)) - 1, 0)
moved = (t >= 1) & ((ar != ar[prev]) | (ac != ac[prev]))
print("damage", dmg.sum(), "pred", (dmg & hp).sum(), "trap", (dmg & ht).sum(), "rock", (dmg & on_rock).sum())
print("no source", (dmg & ~hp & ~ht & ~on_rock).sum(), "trap&rock", (dmg & ht & on_rock).sum())
print("rock newly entered / standing", (dmg & on_rock & moved & ~hp & ~ht).sum(), (dmg & on_rock & ~moved & ~hp & ~ht).sum())
```
