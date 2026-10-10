# Dwell-history / behavior-metrics sweep pipeline

## What this is

For a set of training runs, this pipeline rolls out every saved checkpoint against a
fixed battery of "behavior probe" scenarios (e.g. "a predator is present" vs "no
animal", crossed with "agent starts injured" vs "not"), computes 11 behavior measures
per rollout (time spent hiding in the bush, how close the agent lets a predator get,
how much ground it covers, etc. -- see `scripts/behavior_measures/avoidance_stats_heatmap.py`
for the full list and definitions), and plots how those measures evolve over training.
One CSV row per checkpoint, one CSV per (run, probe condition), one stacked-row figure
per measure per run.

It works identically for both algorithms the project trains: rPPO (`JAX_RecurrentPPO`)
and Dreamer (`JAX_DreamerSRL`), via the same unified `scripts/eval/eval_rollout.py
--batched --record` call -- they differ only in the `--checkpoint` path convention and
Dreamer's extra `--agent_config`.

**As of 2026-07-23**, each worker call evaluates ONE checkpoint against ALL of its still-
pending probe conditions in a single `eval_rollout.py --config-list` process, instead of
one process per (checkpoint, condition) pair -- the model is built and the checkpoint
restored ONCE and reused across every condition. This matters because a single
`eval_rollout.py` call's wall time is dominated by a flat ~7s "build model + restore
checkpoint" cost that does not depend on episode count, so evaluating a checkpoint's 12
core probe conditions used to mean paying that ~7s twelve times over; now it's paid once
per checkpoint (~5.9x fewer core-seconds measured on a real rPPO checkpoint, see "Tuning
notes").

**As of 2026-10-11**, each node also archives and scores its own cells: the test program
writes to node-local `/tmp` staging, `finish_cells.py` packs each checkpoint x scene cell into
ONE uncompressed ZIP (`<step>.zip`, the same files byte for byte) on the shared disk and writes
the cell's CSV row into a small rows table; the driver only merges rows tables. The NAS receives
1 archive per cell + 1 small table per worklist line instead of ~64 files and 5 directories per
cell, and nothing re-reads the episodes over the NAS to score them. Plan:
`docs/develop/active/refactors/SWEEP_EPISODE_BUNDLES_AND_ON_NODE_MEASURES.md`.

This was built as ad-hoc gitignored scripts under `tmp/` across ~7 real sweeps this
session (`tmp/dist_metrics_worker.sh`, `tmp/dist_dreamer_worker_batched.sh`,
`tmp/aggregate_dreamer_metrics.py`, `tmp/plot_metrics_summary.py`) and is promoted here
as one committed, reproducible, self-serve tool.

## Quick start

```bash
/home/vncuser/miniconda3/envs/grid_world_pain/bin/python \
    scripts/eval/dwell_sweep/run_sweep.py configs/eval_sweeps/basic04_variants_rppo.yaml
```

Before launching against real nodes: check which nodes are actually free
(`scripts/lab/gpu_status.py` or the `gpu-status` skill) and edit the spec's `nodes:`
list if any are busy -- the pipeline does not check this for you.

Add `--dry-run` to build the worklist and LPT partition and print the exact launch
commands without touching the cluster:

```bash
... run_sweep.py configs/eval_sweeps/basic04_variants_rppo.yaml --dry-run
```

Other flags: `--nodes 105,110` overrides the spec's `nodes:`; `--status` prints per-node
liveness and per-launch collation state; `--collate-only [--launch ID]` re-merges a finished
launch from its rows tables; `--collate-only --from-bundles` is the recovery path (scores every
pending cell from its archive or legacy folder on this host, `--agg-workers` processes).

Add `--max-checkpoints N` to cap each (run, condition) pair to its newest N *pending*
checkpoints -- useful for a quick smoke test before committing to a full sweep:

```bash
... run_sweep.py configs/eval_sweeps/basic04_variants_rppo.yaml --max-checkpoints 3
```

## Files

| File | Role |
|---|---|
| `run_sweep.py` | The driver. Reads a spec, enumerates + incrementally filters checkpoints, LPT-partitions work across nodes **by checkpoint** (see below), copies the worker files into `_provenance/<launch_id>/worker/` and launches THAT copy on each node via `run_command.py`, polls with liveness checks, collates the nodes' rows tables into CSVs (coverage-checked), renders figures. `_measure_cell(cell)` stays exported for `experiment_eval_checkpoint.py`. |
| `sweep_worker.sh` | The unified per-node worker: `sweep_worker.sh <worklist> <node> <npar> <episodes> <launch_id> <repo_root>` (all six mandatory; the repo root is passed because the copy in `_provenance/` cannot find the repo by path depth). For each worklist line (one CHECKPOINT + all its pending conditions) it runs `eval_rollout.py --batched --record --config-list` ONCE into node-local staging, then `finish_cells.py`; writes liveness markers. |
| `finish_cells.py` | On-node finisher of one worklist line: per scene, pack the staging folder into a local archive (verified), publish it to `<cell>.zip` (one copy, fsync, re-read sha256, rename), then score it into the line's rows piece. Pack before score: a scoring error keeps the archive. `--repo-root` mandatory. |
| `cell_measures.py` | `cell_row(step, episodes)` -- the ONLY place the CSV row arithmetic lives -- and `measure_cell(cell)` for a folder or `.zip`. |
| `bundle_scratch.py` | Migration + checking CLI for old folder-form roots: `inventory`, `backup-tables`, `pack [--into]`, `verify`, `gate` (Gate G1), `independent-check`, `delete`, `extract`, `unlock`, with automatic exclusions E1-E4 (see "Migrating old folders"). |
| `plot_summary.py` | Stacked-row history figures from a directory of `avoid_*.csv` files (one row per probe condition). Promoted as-is from `tmp/plot_metrics_summary.py`; `fig_for()` is imported directly by `run_sweep.py`. |

## Spec schema

A spec is a YAML file under `configs/eval_sweeps/`. Two worked examples ship in that
directory: `basic04_variants_rppo.yaml` (rPPO) and `basic04_rr_dreamer.yaml` (Dreamer).

```yaml
name: basic04_variants          # sweep name; also the default output subdir name
algo: rppo                      # rppo | dreamer -- mandatory, whole spec is one algorithm
output_dir: results/eval/avoidance/<name>   # optional; defaults to results/eval/avoidance/<name>
probe: clean                    # clean | noise -- clean = configs/.../core/avoidance,
                                 #   noise = configs/.../explore/avoidance_stat_noise
conditions: all                 # "all" (the 12 core avoidance probes) or an explicit
                                 #   list of condition names, e.g. [avoid_pred_inj00, avoid_none_inj00]
episodes: 30                    # eval + record episodes per checkpoint (default 30)
nodes: [106, 107, 108, 109]     # node IDs to fan work across (LPT-balanced by pending-checkpoint count)
npar: null                      # per-node parallelism; null -> tuned default per algo (see below)
max_checkpoints: null           # optional cap on newest-N PENDING checkpoints per (run,cond); also a CLI flag
x_axis: null                    # steps | episodes; null -> steps for rppo, episodes for dreamer
plot_measures: [bush_hiding, spatial_spread, survival_steps]   # `bush_hiding` was called `bush_dwell` before 2026-09-07   # any of the 11 measure columns
runs:
  - label: v01_slowmove         # subdirectory name under output_dir; also the figure title
    path: "results/JAX_RecurrentPPO/*rppo_b04v01_slowmove*"   # exact path OR a glob that
                                 #   must resolve to EXACTLY ONE directory (the driver
                                 #   raises if it resolves to 0 or >1)
    # agent_config: only meaningful for algo: dreamer; auto-detected as
    #   <run_dir>/models/agent_config.yaml if omitted (that's where train.py saves it)
```

A "condition" name like `avoid_pred_inj00` decodes as: animal = `pred` (a hunting
predator; other values are `none`, `rabbit`, `rabbit_olfzero`, `rabbitwander`,
`rabbitwander_predsmell`), starting injury = `00` (vs `70`). The 12 core conditions are
every animal x injury combination; see
`configs/environment/experiment/archive/behavior_probes/core/avoidance/` for the actual YAML
files (each one fully specifies the probe scenario: grid size, bush location, predator
spawn point, etc.).

## Tuning notes (why the numbers are what they are)

- **NPAR defaults: rPPO=18, Dreamer(batched)=5.** The eval sweep is CPU-bound (each
  `eval_rollout.py` process spends the bulk of its per-checkpoint time in JAX import +
  XLA compile, and that compile step is itself multithreaded). rPPO's single-env
  rollout is light enough that ~1 process per core (NPAR~=core count, here 18) keeps
  load near the core count. Dreamer's `--batched` path vmaps over all eval episodes at
  once, and that vmap parallelises across cores on its own *even with the 1-thread
  caps below* -- running it at rPPO's NPAR drove a 20-core node to load 142
  (thrashing). ~5 keeps batched Dreamer near the core count instead. If you add a new
  algorithm or change the batch size, re-measure before trusting either default.
- **Thread caps + persistent compile cache.** Every worker process runs with
  `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
  TF_NUM_INTRAOP_THREADS=1 TF_NUM_INTEROP_THREADS=1` and
  `XLA_FLAGS="--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=1"`, plus
  a per-node `JAX_COMPILATION_CACHE_DIR=/tmp/jaxcache_dwellsweep_<node>` (persistent
  across the whole worklist -- the compiled program depends only on tensor *shape*,
  identical across a model's checkpoints, so only the first eval per node pays the
  ~7s compile). Together these took a cold NPAR=16 run from load 100 down to NPAR=18
  warm-cache+capped at load 29, at ~4x lower per-eval wall time. Do not drop the
  caps or the cache dir without re-measuring.
- **Incremental.** Before building the worklist, the driver reads each target CSV's
  max `step` column and only schedules checkpoints newer than that. Re-running a spec
  after a run has trained further only evaluates the new checkpoints and MERGES the
  new rows into the existing CSV (old rows are never dropped, even if a different
  condition's CSV is further behind).
- **On-node packing, scoring and rows tables.** `eval_rollout.py --batched` writes a cell as
  `{cell}/{run_tag}/{ckpt}/recordings/{ckpt}/episode_*.rec.gz` (+ `.npz` arrays, parquet,
  JSON); Dreamer cells hold only `recordings/` + `metadata.json`. The worker points the test
  program at node-local staging; `finish_cells.py` packs whatever is under the cell (layout-
  agnostic), publishes `<cell>.zip`, and scores the cell with `cell_measures.measure_cell`
  (recursive `**/episode_*.rec.gz`, the SAME code path for both algorithms). One rows piece per
  worklist line goes to `_scratch/_rows/<launch_id>/<node>/`; at the end the worker concatenates
  them into `rows_<node>.csv` (columns: `run_label, cond, step, step_M, <11 measures>,
  n_episodes, numpy_version, bundle`). Collation checks that every launched cell has exactly one
  row with the full episode count; a (run, scene) group with ANY hole is not merged at all, so the
  incremental max-step rule re-tests it next time instead of skipping the hole forever.
- **LPT partition -- CHECKPOINT-granularity, not condition-granularity.** Work is grouped
  by (run, checkpoint) -- e.g. "v01_slowmove step 8900007" is one cell carrying every
  condition still pending for that checkpoint (a checkpoint can be ahead on some
  conditions and behind on others under the incremental filter; only the actually-pending
  ones are attached). Cells are sorted by pending-condition count descending and each
  WHOLE cell is assigned to whichever node currently has the smallest running total --
  a cell is never split across nodes, because that's what lets one `eval_rollout.py
  --config-list` process build the model + restore that checkpoint once and loop over
  every pending condition (the entire point of the 2026-07-23 change -- see the top of
  this README). The worklist line format is `CHECKPOINT|AGENT|EPISODE|CFG1,OUT1;
  CFG2,OUT2;...`; `sweep_worker.sh` expands the `;`-separated pairs into a
  `--config-list` file per invocation.

## Node safety

`run_sweep.py` does not check which nodes are busy -- that's on you (or the
`training-runner` agent) before editing a spec's `nodes:` list or passing `--nodes`. A
**usable** node has no training process running (`pgrep -f train.py`), no other sweep's live
markers on it, and no diary claim for today -- not merely "GPU free": the job is CPU-bound
(~18 processes per node). The driver warns when one node gets more than 50 lines. Never point a sweep at
a node running live GPU training; the eval workers run on CPU (`--device cpu`) so they
don't contend for GPU memory, but they do add CPU load that can starve a training run's
data pipeline. As of this pipeline's creation, nodes 106/107/111/112/114 had live
training and were excluded from validation.

## Output layout

```
results/eval/avoidance/<name>/
├── <run_label>/
│   ├── avoid_pred_inj00.csv       # step, step_M, + 11 measure columns
│   ├── avoid_none_inj00.csv
│   ├── ...
│   ├── FIG_bush_hiding.png
│   └── FIG_spatial_spread.png
├── _provenance/<YYYYMMDD_HHMMSS>/   # one per launch, KEEP (added 2026-10-06): what was tested
│   ├── spec.yaml                  # the sweep spec as given
│   ├── provenance.json            # git commit, branch, uncommitted files, host, argv, nodes,
│   │                              # npar, episodes, checkpoint steps evaluated per run
│   ├── scenes/<cond>.yaml, <cond>.resolved.yaml   # each scene as written + after `extends:`
│   └── worker/                    # sweep_worker.sh, finish_cells.py, cell_measures.py AS LAUNCHED
└── _scratch/                       # KEEP: holds the episode archives (no longer "safe to delete")
    ├── <run_label>/<cond>/<step>.zip   # one archive per checkpoint x scene cell (ZIP_STORED,
    │                                   #   original files byte for byte; old roots: <step>/ folders)
    ├── _format                     # "bundles-1" once a new-code launch wrote into this root
    ├── _worklists/worklist_<node>.txt          # transient
    ├── _run_markers/                           # transient; see "Liveness and --status"
    ├── _rows/<launch_id>/rows_<node>.csv       # transient (+ <node>/<line>.csv pieces)
    └── _logs/<launch_id>/{eval,finish}_<node>.log   # eval_rollout stderr; per-cell timings
```

Only `_worklists/`, `_run_markers/`, `_rows/` and `_logs/` are transient.

**Provenance.** Like a training run's `models/config.yaml` + `provenance.json`, each launch
records exactly what it tested. The resolved scene files matter most: a scene usually `extends:` a
training world, so an edit to that world later changes what the same scene file means (level 05
gained random start body temperature on 2026-09-26). A CSV row is matched to its snapshot by its
`step` (listed under `runs[].steps_evaluated`). A scene that fails to resolve stops the sweep before
any node is launched.

**Marker lifecycle.** `poll_done()` treats `_run_markers/done_<node>` as "this node's
worker has finished." Because `output_dir` (and therefore `_scratch/`) persists across
re-runs of the same spec (that's what makes the incremental refresh work), a `done_<node>`
marker from a PRIOR completed sweep is still on disk when you launch a new one -- if
nothing cleared it, `poll_done()` would see it immediately and report completion before
the newly launched worker had done anything. To prevent this, `run_sweep.py` deletes
`done_<node>` for every node about to be launched immediately before the launch loop
(race-free: clear -> launch -> poll, and a worker only re-touches its own marker once it
is genuinely done). `sweep_worker.sh` also clears its own `done_$NODE` marker at start,
as a defense-in-depth backstop. Since 2026-10-11 the driver clears `done_`, `exit_`, `alive_`,
`started_`, `FAILED_`, `fail_` and `lines_` of every node it launches.

## Liveness and `--status`

The worker writes `started_<node>` at start, rewrites `alive_<node>` ("<epoch> <lines done>")
every 60 s from a loop that exits with the worker, appends one line per finished worklist line
to `lines_<node>`, records failed lines in `fail_<node>` (their staging is kept in `/tmp` for
recovery), and its EXIT trap writes `exit_<node>` ("rc=..."); `done_<node>` is written only at a
normal end. `poll_done()` classifies each node at every interval: **done**; **dead** (`exit_`
without `done_`); **stalled** (heartbeat unchanged for 10 min, or no worklist line finished for
20 min); **never started** (no `started_` within 5 min). Ages are measured on the driver's clock
from when a change was last seen, so clock skew does not matter. An unhealthy node gets
`FAILED_<node>` and its marker tails printed; healthy nodes are still waited for, complete groups
are collated, and the driver exits non-zero (2 = unhealthy node, 3 = groups not merged,
4 = failed worklist lines). A killed `xargs` still ends in `done_`; its missing cells are caught
by the collation coverage check. Collation writes `collate_<id>.started`, a 60-s `.alive`
heartbeat, then `.done` or `.failed` (traceback); `--status` reports a collation whose `.alive`
is older than 5 min as **DEAD** (from any host), and "workers done, never collated" when every
node is done but no collation started. Before 2026-10-11 a dead worker made the driver wait
forever.

## Reading raw episodes

Use `src/utils/episode_bundle.py` (`EB`), which accepts a legacy folder or an archive:
`EB.step_names(cond_dir)` lists steps in either form; `EB.cell_path(cond_dir, step)` resolves one
(archive wins; a folder newer than its archive raises `CellConflict`); `EB.members(cell,
pattern)` lists members in `sorted(folder.glob(pattern))` order; `EB.load_recording` /
`EB.load_npz` read them. A tool that needs a folder (e.g. `trajectory_story.py`):
`bundle_scratch.py extract <step>.zip <dest>` first.

## Migrating old folders

`bundle_scratch.py` converts old `<step>/` cell folders to archives (`pack`), byte-compares them
(`verify`), reproduces the per-scene CSVs from the archives alone into an empty table (`gate`,
zero tolerance, exactly 30 recordings per archive), checks with the system `unzip` + `diff -r` on
a host other than the packing host (`independent-check`), and removes originals only through
`EB.delete_verified` (`delete`: needs `backup-tables` once, an all-OK `verify` written on this
host, an all-OK `gate`, and refuses on the packing host). Exclusions, re-checked at every run:
**E1** live or possibly live root (markers, fresh heartbeat, unfinished collation, all workers
done but no newer CSV, a driver/worker process on this host naming the root; a dead old sweep
counts as live until a human resolves it); **E2** any file under `scripts/ src/ tests/` that
mentions sweep episodes and is in neither `SWITCHED_READERS` nor `NON_READERS` blocks `delete`;
**E3** `_scratch/_bundle.lock` (stale after 6 h, or same host and dead pid; remove with
`unlock`); **E4** `SESSION_HOLDS` (the neuromodulation session's runs and roots; labels that
cannot be resolved to a run are held). `pack --into <gate>` writes archives into a separate gate
folder and is the only way to read a held root. `run_sweep.py` refuses to launch into a locked
root.
