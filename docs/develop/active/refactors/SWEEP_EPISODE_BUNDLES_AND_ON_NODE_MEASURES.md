---
title: "Behaviour-test sweep: score on the node, bundle the raw episodes, migrate the old folders"
topic: refactors
status: active
created: 2026-10-07
last_updated: 2026-10-07
---

# Behaviour-test sweep: score on the node, bundle the raw episodes, migrate the old folders

> **Status**: PLANNED (not implemented; awaiting plan review and user approval)
> **Opened**: 2026-10-07
> **Related**: [scripts/eval/dwell_sweep/README.md](../../../../scripts/eval/dwell_sweep/README.md) (the pipeline this changes) · [[EVAL_ROLLOUT_BATCHING_PERF]] (the batched test path) · [[SCRIPTS_DEPENDENCY_MAP]] (maintenance contract) · [[EXPERIMENT_EVAL_DURING_TRAINING]] (a second caller of the same scoring function)

---

## Context

**What the pipeline does.** The behaviour-test sweep takes a set of trained agents and, for every saved checkpoint, plays 30 test episodes in each of 12–40 fixed test scenes ("a predator is present, agent starts injured", "no animal, agent unhurt", …). From every episode it computes 11 behaviour measures (time hiding in the bush, closest approach to the animal, survival time, …) and writes one row per checkpoint into a per-scene table. Those tables feed the results pages.

**The problem (measured 2026-10-07).** The test machines write every episode to the shared NAS as separate small files — in fact about **64 files per checkpoint × scene** (30 episode recordings of ~8 KB, 30 compact episode arrays of ~2.5 KB, plus 4 metadata files). One sweep of 6 agents × 51 checkpoints × 12 scenes is ~3,700 checkpoint×scene cells, i.e. **~235,000 files**; this morning's four sweeps wrote ~680,000. Playing the episodes took only 13–20 minutes on one node per sweep, but the separate scoring step then re-read every file over the NAS from a single machine, taking 8–20 minutes per sweep. One scoring run died without leaving any trace and nobody noticed for three hours.

**What this plan does.** (1) Score each checkpoint on the test machine itself, right after it plays the episodes, and write one small results table per machine; the final step just merges those tables (seconds). (2) Keep every raw episode, but packed into **one archive file per checkpoint × scene** instead of 64 loose files — the archive holds the exact same files, byte for byte. (3) Prove on a finished sweep that the new path reproduces today's tables exactly. (4) Convert every existing test folder to the archive format, verifying each archive against the originals before any original is deleted. (5) Spread each sweep over all listed machines and make a dead worker or a dead scoring step visible within minutes instead of hours.

**What it does not change.** The episodes themselves (same test program, same seeds, same scenes), the 11 measures and their formulas, the per-scene tables the pages read, the provenance snapshot each launch saves, or the incremental "only test new checkpoints" rule.

---

## Analysis

### A1. What one checkpoint × scene cell holds today

Measured on `results/eval/avoidance/metrics_history_rppo_healrep/l05fix_own/_scratch/l05fix_modulated_s42/avoid_pred_inj70/10000021/`:

```
<cell> = _scratch/<run_label>/<cond>/<step>/
  <run_tag>/<step>/episodes/0000.npz … 0029.npz          30 × ~2.6 KB  (np.savez_compressed; step arrays)
  <run_tag>/<step>/recordings/<step>/episode_000000.rec.gz … 30 × ~8 KB (gzip-pickle; what the measures read)
  <run_tag>/<step>/recordings/<step>/run_meta.pkl          1
  <run_tag>/<step>/windows/threat_onsets.parquet           1
  <run_tag>/<step>/online_replay.json, metadata.json       2
                                                           = 64 files, 5 directories, ~436 KB
```

`<run_tag>` varies by vintage (`20261006-074133_rppo_healrep_l05fix_t16quad_s42`, or `models` in older sweeps such as `metrics_history_rppo_basic04_variants`). Dreamer cells have only `recordings/` + `metadata.json` (no `episodes/*.npz`, no `online_replay.json`), and episode numbers start at 1. Any bundling therefore has to be **layout-agnostic**: pack whatever is under the cell directory, keyed by its relative path.

The user's brief named the `.npz` files; the scoring step actually reads the larger `.rec.gz` recordings (`run_sweep.py::_measure_cell` globs `**/episode_*.rec.gz`). Both are kept in the bundle.

### A2. Where the time goes

- Workers: `sweep_worker.sh` → one `eval_rollout.py --batched --record --config-list` per checkpoint (all pending scenes in one process). 300 lines in 762–1172 s on one node each, this morning (`_run_markers/prog_*`).
- Scoring: `run_sweep.py::aggregate()` runs on the launching container after `poll_done()`. For every (run, scene) group with pending work it **re-globs every step directory of that group, including all previously scored steps**, decompresses every recording and recomputes every row. That is 235k NAS file opens per collation of a full sweep, every time — the steady-state cost does not shrink with incremental launches.
- `scripts/analysis/studies/f7b_across_runs/aggregate_only.py` calls the same `aggregate()`.

### A3. Why a death goes unnoticed

- `poll_done()` loops forever until `_run_markers/done_<node>` appears. A worker killed by OOM, a node reboot, or a lost SSH session never writes it, and nothing else is checked — the driver waits silently.
- `aggregate()` writes no marker at all; if the driver process is killed during collation there is no record that collation started.
- `sweep_worker.sh` sends each failed `eval_rollout.py` call to `fail_<node>`, but the driver never reads that file.

### A4. Every reader of the per-episode files (consumer inventory)

Grep over `scripts/`, `src/`, `tests/` (worktrees excluded) for `_scratch`, `rec.gz`, `load_episode`, `episodes/*.npz`:

| # | Reader | What it reads from a sweep cell | Planned action | Owner |
|---|---|---|---|---|
| R1 | `scripts/eval/dwell_sweep/run_sweep.py` `_measure_cell`, `aggregate` | `**/episode_*.rec.gz` | rewrite (this plan) | this plan |
| R2 | `scripts/analysis/studies/f7b_across_runs/aggregate_only.py` | via R1 | rewrite to the new collation | this plan |
| R3 | `scripts/eval/experiment_eval_checkpoint.py` (during-training eval, launched by `train.py`) | calls `_measure_cell(dir)` on its own output dirs | **no change**; `_measure_cell` keeps accepting a directory | this plan (regression test only) |
| R4 | `scripts/analysis/basic_behaviour/probe_pond.py` `episodes_in` | `*/*/episodes/*.npz` + matching `.rec.gz` | port to bundle reader | this plan |
| R5 | `scripts/analysis/studies/basicq2_waves/_traj.py` | `<ck>/*/*/recordings/*/episode_*.rec.gz` | port | this plan |
| R6 | `scripts/analysis/studies/thermal_probes/t04_variance_budget.py` | `**/episode_*.rec.gz` | port | this plan |
| R7 | `scripts/analysis/studies/injury_dependence/scene_steps.py` | `<ck>/*/<ck>/recordings/<ck>/episode_*.rec.gz` | port | this plan |
| R8 | `scripts/analysis/studies/injury_dependence/run_manipulations.py` | passes a cond dir to `obs_manipulation/run.py --check-against-sweep` | no change once R9 is ported | — |
| R9 | `scripts/analysis/obs_manipulation/run.py` `_parity` | `<step>/*/<step>/recordings/<step>/episode_*.rec.gz`; raises if count ≠ N | **port required — FLAGGED: owned by the "Training: neuromodulation" session, which has 95+/26− uncommitted lines in this file right now** | other session |
| R10 | `scripts/analysis/case_l05_s42/case.py` `_parity` | `os.path.isdir(scratch/<step>)` → exact parity via R9, **else silently falls back to a weaker CSV-mean check** | **port required — FLAGGED: other session, file untracked** | other session |
| R11 | `tests/analysis/test_case_l05_s42.py` | same `isdir` gate → parity block silently skipped | port — FLAGGED, other session, untracked | other session |
| R12 | `tests/analysis/test_modulator_engagement.py:165` | same `isdir` gate | port — FLAGGED, most likely the same session (modulator engagement work) | other session (confirm) |
| R13 | `scripts/eval/trajectory_story.py`, `render_recordings.py`, `render_recordings_v2.py`, `render_layout_audit.py` | a recordings **directory** (`run_meta.pkl` + `episode_*.rec.gz`) | no code change; use the new `extract` subcommand first; README + `trajectory-story` skill note | this plan (docs) |
| R14 | `scripts/behavior_measures/avoidance_stats_heatmap.py` collect mode, `motif_cluster.py`, `parity_check_eval_rollout.py`, `continual_forgetting_matrix.py` | direct `eval_rollout.py` outputs under `results/eval/<name>/models/…`, not sweep cells | none — out of migration scope | — |

**The hazard behind R10–R12.** Those readers test for the *directory* `…/<step>`. Once a cell becomes `<step>.zip` they do not fail — they quietly switch to a weaker check (R10) or skip a check (R11, R12). The pilot folder the user named (`healrep/l05fix_own`) is exactly the sweep those tools read. **Deleting its originals before R9–R12 read bundles would silently weaken another session's parity checks.** The plan therefore puts a hard hold on deletion for every root those tools read until the other session confirms the port (Phase M, step M1.4).

### A5. Design choices and the alternatives rejected

| Choice | Picked | Rejected and why |
|---|---|---|
| Bundle unit | **one archive per checkpoint × scene cell** (`<cond>/<step>.zip`, replacing `<cond>/<step>/`) | per worklist line (one checkpoint, all scenes): 12× fewer files still, but a checkpoint can be pending on only some scenes, so re-tests would rewrite other scenes' data; every consumer would need cell lookups inside a larger archive. Per (run, scene) across all checkpoints: an append-only archive rewritten on every incremental launch — a write-amplification and corruption hazard. Per cell gives 64× fewer files and maps 1:1 onto today's directory, so every consumer change is "directory → archive of the same tree". |
| Bundle format | **uncompressed ZIP (`ZIP_STORED`) whose members are the original files byte for byte**, named by their path relative to the cell directory | a re-encoded container (one big npz / parquet): migration could only be verified by re-parsing, not by checksum, and every reader would need a new decoder. The members are already compressed (gzip / npz), so storing them uncompressed costs nothing. Python's `zipfile` reads members as file objects, and `gzip.open` accepts a file object, so `load_episode` works unchanged. |
| Where scoring happens | **on the node, in the same worker job, immediately after the test process, from a node-local staging copy (`/tmp`)** | inside `eval_rollout.py` from in-memory episodes (the brief's literal wording): Dreamer's batched path writes its recordings inside `src/algorithms/dreamer_srl/eval.py` and returns no recorder objects, so the two algorithms would need two scoring paths and an edit to the Dreamer source; it would also put the 11-measure function inside the generic test program that six other callers use. Scoring the staged files reuses the **identical function on identical bytes** as today's collation (exact by construction), touches neither `eval_rollout.py` nor the Dreamer source, and still never reads the NAS. Cost: one short Python start per checkpoint line (measured in the speed check). **Open decision D1.** |
| Where bundles live | **unchanged location under `_scratch/`** (`_scratch/<label>/<cond>/<step>.zip`) | renaming to `_episodes/` is clearer (the files are now kept, not scratch) but breaks R4–R12 paths twice. **Open decision D2.** |
| Results table | **one CSV per node per launch** at `_scratch/_rows/<launch_id>/rows_<node>.csv`, assembled from per-line pieces | one shared table appended by all nodes: concurrent appends over the NAS are not safe; file locks over SMB are unreliable. |

---

## Implementation Plan

### Design — data flow after the change

```
run_sweep.py SPEC [--nodes 101,103,…]
  build_groups (unchanged: incremental skip by CSV max step)
  lpt_partition over ALL listed nodes (unchanged algorithm)
  write_provenance (unchanged) ──► launch_id = provenance snapshot folder name (YYYYMMDD_HHMMSS)
  launch sweep_worker.sh <worklist> <node> <npar> <episodes> <launch_id>      (one per node)
        per worklist line (one checkpoint, k pending scenes):
          eval_rollout.py --config-list (outputs → node-local /tmp staging, one dir per scene)   [unchanged program]
          finish_cells.py: for each scene → score staged recordings (cell_row)
                                         → pack staging dir into <cell>.zip.partial on NAS, verify, rename to <cell>.zip
                                         → append row to piece _rows/<launch_id>/<node>/<line>.csv (atomic)
                                         → delete staging
        heartbeat _run_markers/alive_<node> every 60 s; EXIT trap writes exit_<node>
        end: concatenate pieces → _rows/<launch_id>/rows_<node>.csv ; touch done_<node>
  poll_done: done / dead (exit without done) / stalled (heartbeat > 10 min old) / never started (5 min)
  collate(launch_id): markers collate_<launch_id>.started → read rows_<node>.csv for this launch's nodes
        → check every worklist cell has exactly one row with n_episodes == episodes
        → merge into <out>/<label>/<cond>.csv (same columns, same string formatting) → .done / .failed
  plot (unchanged)
run_sweep.py SPEC --status          → node + collation liveness report (for humans and /wake polls)
run_sweep.py SPEC --collate-only [--launch ID | --from-bundles]   → recovery paths
```

Single source of truth for one CSV row: **`cell_row(step, recordings)`** — the body of today's `_measure_cell` moved into a small module and called by (a) the on-node finisher, (b) `_measure_cell` for directories (R3) and archives, (c) `--from-bundles` recovery and the exactness gates.

Migration (Phase M) uses the **same pack + verify functions** as the live finisher, so the code that preserves bytes is exercised on every sweep, not only once.

### File Changes

New config keys: **none** (no YAML schema change; `CONFIG_GUIDE.md` / `CONFIG_CRITICAL_SETTINGS.md` unaffected). Spec loader gains no new keys; the only new inputs are CLI flags.

#### F1. NEW `src/utils/episode_bundle.py` (~150 lines) — the bundle format, reader, packer, verifier, guarded deleter

Placed in `src/utils/` beside `eval_recording.py` because readers under `scripts/analysis/` already import `src.utils.eval_recording`, and both sweep code and analysis code need it. Pure Python (`zipfile`, `hashlib`, `gzip`, `pickle`, `pathlib`); no JAX import.

```python
BUNDLE_SUFFIX = ".zip"

def cell_path(cond_dir, step) -> Path | None:
    """The cell for (cond_dir, step): <cond_dir>/<step>.zip if it exists, else the legacy
    directory <cond_dir>/<step>/ if it exists, else None. Both existing = mid-migration;
    the archive wins (it was verified equal before it was renamed into place)."""

def members(cell, pattern="**/episode_*.rec.gz") -> list[str]:
    """Relative POSIX member names matching `pattern`, sorted as today's
    sorted(step_dir.glob(pattern)) sorts them (PurePosixPath ordering).
    Works on an archive or a legacy directory."""

def open_member(cell, name) -> BinaryIO
def load_recording(cell, name) -> dict          # load_episode on the member's file object
def load_npz(cell, name) -> dict                # np.load(BytesIO(...)), allow_pickle=False

def pack(src_dir, zip_path) -> dict:
    """Write src_dir's tree into <zip_path>.partial-<host>-<pid> (ZIP_STORED, members sorted,
    names relative POSIX, directory entries included so empty dirs survive), fsync, run
    verify(src_dir, partial), and only then os.replace(partial, zip_path). On any mismatch:
    delete the partial, raise BundleMismatch. Returns the manifest {name: (size, sha256)}."""

def verify(src_dir, zip_path) -> dict:
    """Exact equality or raise BundleMismatch: same set of file names, same sizes, same
    sha256 of every member vs every source file, zipfile.testzip() is None."""

def delete_verified(cell_dir, zip_path, log_path) -> int:
    """The ONLY function that deletes originals. In one call: path guard (cell_dir matches
    .../_scratch/<label>/<cond>/<digits>, zip_path is its sibling <digits>.zip, both resolve
    under <repo>/results/eval/), verify(cell_dir, zip_path) again, append the manifest
    (cell, name, size, sha256) to log_path and fsync BEFORE unlinking, unlink exactly the
    verified files, then os.rmdir bottom-up (never rmtree). A file that appeared after
    verification makes rmdir fail -> raise, leaving it in place. No flag skips verification."""

def extract(zip_path, dest_dir)                  # for directory-based tools (R13)
```

#### F2. NEW `scripts/eval/dwell_sweep/cell_measures.py` (~40 lines) — one CSV row

Moves today's `_measure_cell` body (`scripts/eval/dwell_sweep/run_sweep.py:288–309`) here **verbatim in its arithmetic** (same `np.nanmean` under `warnings.catch_warnings`, same `f"{step / 1e6:.4f}"`, same `"" if not finite else f"{x:.4f}"`), parameterised on an iterable of episode payloads:

```python
from avoidance_stats_heatmap import episode_measures, KEYS   # bare-name import, sys.path as run_sweep.py
HEAD = ["step", "step_M"] + KEYS

def cell_row(step: int, episodes) -> list | None:
    rows = [episode_measures(ep) for ep in episodes]
    if not rows:
        return None
    ...  # unchanged aggregation + formatting
    return vals          # [step, step_M, 11 formatted strings]

def measure_cell(cell) -> tuple[int, list] | None:
    """cell = legacy dir OR .zip. step = int(name without .zip). Episodes in members() order."""
```

`avoidance_stats_heatmap` pulls in matplotlib/seaborn at import (~1–2 s). Acceptable once per checkpoint line; measured in the speed check. If it exceeds the 5 % budget, the follow-up is to move `episode_measures`/`KEYS` into a plotting-free module re-exported by `avoidance_stats_heatmap` (keeps the parity-harness rule "same function" intact) — not done pre-emptively.

#### F3. NEW `scripts/eval/dwell_sweep/finish_cells.py` (~80 lines) — the on-node finisher

```
finish_cells.py --pairs STAGE1=CELL1 STAGE2=CELL2 ... --rows-piece <path> --episodes N
```
For each pair: locate the staged recordings (`members(STAGE)`), `cell_row(step, …)` with `step = int(Path(CELL).name)`, `pack(STAGE, CELL + ".zip")`, collect the row `[run_label, cond] + row + [n_episodes, bundle_relpath]` where `run_label, cond = Path(CELL).parts[-3:-1]`. Write all rows of the line to `<rows-piece>.tmp` then `os.replace` (atomic). Exit non-zero if any cell has `n_episodes != N` or no recordings (the row is still written with `n_episodes` so collation can report it). Staging deletion is done by the worker (F5) after this exits 0.

Rows table columns: `run_label, cond, step, step_M, <11 measures>, n_episodes, bundle`.

#### F4. `scripts/eval/dwell_sweep/run_sweep.py` (563 lines; expected net +150 / −40)

1. **Imports (L47–52):** add `sys.path` entry is already there for `_HERE.parent`; import `cell_row, measure_cell, HEAD` from `cell_measures`; import `src.utils.episode_bundle as EB`.
2. **`_measure_cell` (L288–309):** becomes `return measure_cell(step_dir)` — same name and signature, accepts dir or `.zip` (keeps R3 `experiment_eval_checkpoint.py` working; keeps the `SCRIPTS_DEPENDENCY_MAP` row true).
3. **`aggregate()` (L312–365) → replaced by `collate(groups, scratch_root, launch_id, nodes, worklist_cells, episodes)`:** reads `_rows/<launch_id>/rows_<node>.csv` for this launch's nodes, builds `{(label, cond): {step: vals}}`, checks coverage — every `(label, cond, step)` in the worklists has exactly one row, `n_episodes == episodes` — and merges into the existing CSV with the unchanged read/merge/write logic (L327–330, L353–364 kept verbatim). Missing / short cells are **listed and the function raises after writing the complete groups** (never silently drops). Old `aggregate()` kept as `aggregate_from_bundles(groups, scratch_root, n_workers)` — today's code with the glob replaced by `EB.cell_path`/`measure_cell` over both `<step>/` dirs and `<step>.zip` files — used by `--collate-only --from-bundles` and the exactness gates.
4. **Collation markers:** `collate()` and `aggregate_from_bundles()` are wrapped by `_with_collate_markers(scratch_root, launch_id, fn)`: writes `_run_markers/collate_<id>.started` (`host`, `pid`, start time, n groups) before; `.done` (CSVs written, rows merged, seconds) on success; `.failed` (traceback) in `except`, re-raising. A SIGKILL leaves `.started` alone → detectable by `--status`.
5. **`write_worklist()` (L233–250):** unchanged line format.
6. **`launch_node()` (L253–259):** pass `launch_id` as the 5th worker argument.
7. **`poll_done()` (L262–274) → liveness-aware:** per node, each interval: `done_<n>` → done; `exit_<n>` present and no `done_<n>` → **dead**; `alive_<n>` older than `HEARTBEAT_STALE_S = 600` → **stalled**; no `alive_<n>` within `START_GRACE_S = 300` of launch → **never started**. On dead / stalled / never-started: print the node, its `prog_`/`fail_` tail, write `_run_markers/FAILED_<n>`, and `raise SystemExit(2)` after the healthy nodes finish (the partial rows of healthy nodes are still collated first; the exit code is non-zero). Module constants, not spec keys (operational thresholds, not experiment settings).
8. **Stale-marker clearing (L541–545):** also clear `exit_`, `alive_`, `FAILED_` for the nodes being launched.
9. **`fail_<node>` reporting:** after polling, print the count + first lines of every `fail_<node>`; non-zero exit if any.
10. **New CLI:** `--nodes 101,103,…` (overrides `spec.nodes`; recorded in provenance through the existing `nodes` field), `--status` (prints per-node started/alive-age/done/exit/fail-count and per-launch collation state; for `.started` without `.done`/`.failed`: if same host and pid not alive → `DEAD`, else `RUNNING?`), `--collate-only [--launch ID | --from-bundles]` (the replacement for `aggregate_only.py`'s job; refuses if any node of that launch lacks `done_` unless `--from-bundles`).
11. **Single-node warning:** if `len(nodes) == 1` and pending checkpoint lines > 50, print a warning recommending listing all free nodes (`gpu-status` skill) — does not block.
12. **Lock against migration:** refuse to launch if `_scratch/_bundle.lock` exists (F7 holds it).
13. **`write_provenance()` (L398–431): unchanged.** Its folder name is reused as `launch_id`.

#### F5. `scripts/eval/dwell_sweep/sweep_worker.sh` (84 lines; expected net +40)

- Signature: `sweep_worker.sh <worklist> <node> <npar> <n_episodes> <launch_id>` (5th arg mandatory; error if missing).
- At start: `echo "host=$(hostname) pid=$$ $(date +%s)" > $MARK/started_$NODE`; heartbeat `( while sleep 60; do date +%s > "$MARK/alive_$NODE"; done ) & HB=$!`; write `alive_` once immediately; `trap 'rc=$?; kill $HB 2>/dev/null; echo "rc=$rc $(date +%s)" > "$MARK/exit_$NODE"; rm -rf "$STAGE_ROOT"' EXIT`.
- `STAGE_ROOT=/tmp/dwellsweep_${LAUNCH_ID}_${NODE}_$$`.
- `runeval()`: per line, make `stage=$(mktemp -d -p "$STAGE_ROOT")`; the `--config-list` file maps each scene to `$stage/<k>` instead of the final cell path (final paths are still read from the worklist line); after `eval_rollout.py` succeeds, run `finish_cells.py --pairs "$stage/<k>=<final_cell_k>" … --rows-piece "$ROWS/<node>/<line-hash>.csv" --episodes "$NEP"`; on success `rm -rf "$stage"`; on any failure append `FAIL <stage-of-failure> <line>` to `fail_$NODE` and keep going (as today).
- End: concatenate `$ROWS/<node>/*.csv` (one header) into `$ROWS/rows_$NODE.csv` via tmp + `mv`, then `touch done_$NODE`. Pieces kept until concatenation succeeds, then removed.
- Thread caps, compile cache, xargs `-P $NPAR` unchanged.

#### F6. `scripts/analysis/studies/f7b_across_runs/aggregate_only.py` (43 lines)

Becomes a thin wrapper over `run_sweep.py --collate-only` semantics: default reads the newest launch's rows tables; `--from-bundles` calls `aggregate_from_bundles` with its own `--workers` (keeps the container-load safeguard that motivated the file). Keeps the done-marker refusal.

#### F7. NEW `scripts/eval/dwell_sweep/bundle_scratch.py` (~200 lines) — migration CLI

Subcommands (all take one or more scratch roots, or `--all` = every `_scratch` under `results/eval/avoidance/` found by `os.walk`, any depth):

- `inventory` — read-only. Per root: number of legacy cell dirs, already-bundled cells, files, bytes, whether a sweep is live (below). Writes `tmp/<stamp>_bundle_inventory.csv`. Also lists, **without touching**, per-episode eval folders outside `results/eval/avoidance/` (e.g. `results/eval/<name>/models/<ck>/episodes/`) for decision D3.
- `pack [--dry-run]` — for each legacy cell `_scratch/<label>/<cond>/<digits>/` without a sibling `.zip`: `EB.pack(cell, cell.zip)`. Originals untouched. Resumable (skips cells with a valid `.zip`; a leftover `.partial-*` is deleted and redone).
- `verify` — re-verifies every cell that has both a dir and a `.zip`; writes a per-root report `_scratch/_bundle_log/verify_<stamp>.csv` (cell, n files, bytes, status).
- `gate` — runs Gate G1 (below) for a root: `aggregate_from_bundles` into a temp dir and byte-compares against `<out>/<label>/<cond>.csv`; per (run, scene, step) report.
- `delete` — for each cell with both forms: `EB.delete_verified(...)`. Refuses a root unless (a) its latest `verify` report is all-OK, (b) its `gate` report is all-OK **or** the root is listed in `--accept-gate-exceptions <file>` written by the user, and (c) the root is not in `HOLD_ROOTS` (a constant listing the roots read by R9–R12 until the other session confirms; see M1.4).
- `extract <zip> <dest>` — for R13 tools.

Safety rails (all structural, not procedural): takes `_scratch/_bundle.lock` (`O_CREAT|O_EXCL`) per root for the duration; refuses a root whose `_run_markers` show a live sweep (any `npar_<n>`/`started_<n>` newer than its `done_<n>`, or `alive_<n>` < 10 min old); never opens anything outside `_scratch/<label>/<cond>/<digits>[/…]` for writing or deletion — the per-scene CSVs at `<out>/<label>/*.csv`, figures, and `_provenance/` are outside every path it can delete (asserted in `EB.delete_verified`'s path guard, and covered by a test).

#### F8. Reader ports (this plan's own files)

Each replaces its glob with `EB.cell_path` + `EB.members` + `EB.load_recording` / `EB.load_npz`, keeping its own logic; each must accept both legacy dirs and archives:

| File | Lines | Change |
|---|---|---|
| `scripts/analysis/basic_behaviour/probe_pond.py` | `episodes_in` L126–137, and its caller at L319 | yields `(run, cell, npz_member, rec_member)` and `measure_episodes` loads through EB |
| `scripts/analysis/studies/basicq2_waves/_traj.py` | `_episodes` L33–45 | |
| `scripts/analysis/studies/thermal_probes/t04_variance_budget.py` | L27–40 | |
| `scripts/analysis/studies/injury_dependence/scene_steps.py` | L60–75 | |

#### F9. Flagged ports for the other session (NOT edited by this plan)

Hand to the "Training: neuromodulation" session (or to `developer` once that session has committed and agrees):

- `scripts/analysis/obs_manipulation/run.py::_parity` L407–415: replace the glob with `cell = EB.cell_path(sweep_dir, step)`; `recs = EB.members(cell)`; `ep = EB.load_recording(cell, name)`; raise if `cell is None`.
- `scripts/analysis/case_l05_s42/case.py::_parity` L146–147: `if EB.cell_path(scratch, step) is not None:` instead of `os.path.isdir(...)`.
- `tests/analysis/test_case_l05_s42.py` L160–161 and `tests/analysis/test_modulator_engagement.py` L165–166: same one-line change.

Until these land, `HOLD_ROOTS` (F7) blocks deletion for: every `metrics_history_rppo_healrep/*` root, every `metrics_history_rppo_modeng_e4/*` root, `metrics_history_rppo_basicq2_wave2_blocking_bush`, `metrics_history_rppo_thermalprobe_neutral_clean`, and every `metrics_history_rppo_injurygrid_*` root (R8 → R9). The developer re-derives this list from `scripts/analysis/modulator_engagement/runs.py`, `case_l05_s42/case.py` and `injury_dependence/run_manipulations.py` at implementation time and records it in the Implementation Report.

#### F10. Tests

- **NEW `tests/scripts/test_episode_bundle.py`** (no checkpoints, no NAS; uses `tmp_path` and synthetic recordings written by the real `EpisodeRecorder.write` + `np.savez_compressed`):
  - `test_pack_roundtrip_bytes_equal` — every member's bytes equal the source file's.
  - `test_pack_preserves_empty_dirs_and_nested_layout` — `models/<ck>/…` and `<run_tag>/<ck>/…` layouts, an empty `windows/`.
  - `test_measure_cell_dir_equals_zip` — `measure_cell(dir) == measure_cell(zip)` element-for-element, rPPO layout (0-based) and Dreamer layout (1-based, no npz).
  - `test_verify_detects_changed_byte`, `…_missing_member`, `…_extra_source_file`.
  - `test_delete_refuses_after_source_changed` — modify one original after pack → `delete_verified` raises, nothing deleted.
  - `test_delete_leaves_file_created_after_verify` — new file appears → it survives, dir survives, raises.
  - `test_delete_path_guard` — a cell outside `_scratch/<label>/<cond>/<digits>` or a sibling CSV → raises; the per-scene CSV next to `_scratch` is never touched.
  - `test_pack_is_atomic` — simulated failure mid-pack leaves no `<step>.zip`.
- **NEW `tests/scripts/test_dwell_sweep_collate.py`**:
  - `test_collate_matches_aggregate_from_bundles` — synthetic rows tables vs `aggregate_from_bundles` on the same synthetic cells → byte-identical CSVs.
  - `test_collate_merges_without_dropping_old_rows` (the existing invariant).
  - `test_collate_raises_on_missing_cell` and `…_on_short_episode_count`.
  - `test_poll_detects_dead_worker` (exit marker, no done), `…_stalled_heartbeat`, `…_never_started` — `poll_done` with injectable clock/interval.
  - `test_status_reports_dead_collation` — `.started` with a dead pid on this host → `DEAD`.
  - **Regression test for the silent-death bug:** `test_poll_done_does_not_wait_forever_on_dead_worker` — must **fail on the current `poll_done`** (it would loop; the test runs it with a 5 s timeout) and pass after.
- **Existing tests that must still pass:** everything importing `run_sweep` / `_measure_cell` (`experiment_eval_checkpoint` tests if present: `grep -rl experiment_eval_checkpoint tests/`), `tests/analysis/test_basic_behaviour.py` (probe_pond), `tests/scripts/test_eval_rollout_online_replay.py`, `tests/algorithms/dreamer_srl/test_eval_rollout_batched.py`.

#### F11. Docs (same change)

- `scripts/eval/dwell_sweep/README.md`: Files table (+`cell_measures.py`, `finish_cells.py`, `bundle_scratch.py`); "Recursive-glob aggregation" tuning note replaced by "On-node scoring + rows tables"; Output layout (`<step>.zip` cells, `_rows/<launch_id>/`, new markers); **`_scratch/` is no longer "safe to delete" — it holds the kept episode archives; only `_worklists/`, `_run_markers/`, `_rows/` are transient**; Node safety section: recommend listing all free nodes and `--nodes`; new "Liveness and `--status`" and "Reading raw episodes" (EB API + `extract`) sections; "Migrating old folders" section.
- `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` (maintenance contract): rows for the three new scripts and `src/utils/episode_bundle.py`'s script callers; update the `run_sweep.py` row (new `cell_measures` import; `_measure_cell` still exported for `experiment_eval_checkpoint.py`); `sweep_worker.sh` row (5th arg, `finish_cells.py` subprocess); `aggregate_only.py` (f7b row); `probe_pond.py` (basic_behaviour row: "The dwell sweep's `_scratch/` must survive" → reads archives); R5–R7 rows if present.
- `.claude/skills/trajectory-story/SKILL.md`: one line — sweep recordings are archives now; `bundle_scratch.py extract` first.

### Phase order, gates, and stop points

**Phase A — code (F1–F6, F8, F10, F11).** Unit tests green before Phase B.

**Gate G1 — scoring from archives reproduces today's tables exactly (existing data, no new tests run).**
On `metrics_history_rppo_healrep/l05fix_own` (all rows from one launch this morning at commit `b2ba9cf`): `bundle_scratch.py pack` (originals kept) → `verify` → `gate`. **Pass criterion, stated in advance: zero tolerance — for every run × scene × step present in the current CSV, the recomputed row's 13 strings are identical to the CSV's; all 72 CSVs (6 runs × 12 scenes) byte-identical.** Any CSV row with no matching archive is listed and counts as a failure for this folder.

**Gate G2 — the new on-node path reproduces today's tables exactly (fresh test runs).**
A spec copy of the `l05fix_own` sweep written to `tmp/` with a fresh `output_dir` (e.g. `results/eval/avoidance/_bundle_gate/l05fix_own`), `--max-checkpoints 2`, all 6 runs, `--nodes` = ≥2 free nodes. Pass criteria, stated in advance: (a) every new row (6 × 2 × 12 = 144) string-identical to the current CSV's row for the same run/scene/step; (b) for every one of the 144 cells, every recording in the new archive decodes to a payload equal to the old archive's (G1) member — `snapshots` dict-by-dict with `np.array_equal`, `obs`, `true_obs`, `actions`, `rewards` with `np.array_equal`, scalars `==`; `episodes/*.npz` arrays equal; (c) collation wall time recorded (expect seconds). The episodes are deterministic (greedy policy, `--seed 0`, CPU, batched — the property `obs_manipulation` already relies on for exact parity), so any difference is a bug, not noise.

**Gate G3 — Dreamer keeps working.** `configs/eval_sweeps/basic04_rr_dreamer.yaml` copy in `tmp/` with fresh `output_dir`, `--max-checkpoints 1`, one run: (a) worker completes, archive written, row present; (b) row string-identical to the existing Dreamer CSV row at that step if one exists, else `rows table == measure_cell(archive)` and the batched-Dreamer determinism question is reported, not forced.

**Speed check.** Same node, same spec, same seed: old vs new worker wall time for the same 2 checkpoints × 6 runs (the G2 workload). Report: test wall time (budget: ≤ 5 % slower; the finisher's Python start is the expected cost), collation wall time old (re-measure `aggregate()` on the G2 output from legacy-format cells) vs new, files written per cell (64 → 1). **Stop and report if > 5 %.**

**Phase M — migration.**
- **M0 inventory** (read-only, all roots). Report counts/bytes; the user sees it.
- **M1 pilot on `metrics_history_rppo_healrep/l05fix_own`:**
  1. pack + verify (done in G1);
  2. G1 passed;
  3. smoke-read through the ported readers (R4–R7 on any root they normally read, from archives);
  4. **HOLD:** this root is in `HOLD_ROOTS` (R10–R12 read it). Deletion needs the other session's ports (F9) merged **and** the user's go. Ask the user; do not proceed silently;
  5. `delete` → re-run `gate` from archives alone (must still pass) → report files and bytes before/after.
- **M2 all roots:** `pack` + `verify` + `gate` over `--all`. Roots with an all-OK verify and gate and not in `HOLD_ROOTS` → `delete`. Roots whose gate differs (older CSVs written by older measure code, e.g. before the 2026-09-07 `bush_dwell → bush_hiding` rename, or rows whose cells were already removed) are **listed for the user, not deleted** until the user writes the exceptions file. The archive check (byte equality) is mandatory for every deletion regardless.
- **M3 (decision D3):** per-episode eval folders outside `results/eval/avoidance/` — inventory only in this plan.

Snapshot rule (CLAUDE.md git-safety): the migration is not a git operation, and a full copy of 1.7 GB / 235k files per root would itself be the slow NAS operation being removed. The protection is structural instead: originals are deleted only by `delete_verified`, which re-hashes every file against its archive member in the same call, writes a write-ahead log of what it deletes with sha256, and cannot be told to skip verification. **Plan-reviewer: please challenge whether this is sufficient for the pilot, or whether the pilot root should additionally be copied once (e.g. `tar` to `results/_backup/`) before M1.5.**

## Checkpoints

- [ ] `cell_row` is the only place the row arithmetic exists (grep `nanmean` in `scripts/eval/dwell_sweep/` → one hit).
- [ ] `experiment_eval_checkpoint.py` still imports `_measure_cell, HEAD, KEYS` from `run_sweep` and works on a directory (run its test or a one-checkpoint dry call).
- [ ] New unit tests pass; the regression test `test_poll_done_does_not_wait_forever_on_dead_worker` was shown to fail (timeout) on the pre-change `poll_done` — paste that output into the Implementation Report.
- [ ] `--dry-run` on the `l05fix_own` spec prints the 5-argument worker command and unchanged LPT loads.
- [ ] A killed worker (`kill -9` the xargs parent on one node during G2's first minute, in a throwaway output dir) is reported as dead by `poll_done` within `HEARTBEAT_STALE_S` + one interval, and `--status` shows it.
- [ ] A killed collation (`kill -9` during `--collate-only --from-bundles`) shows `DEAD` in `--status`.
- [ ] G1, G2, G3 pass with the pre-stated criteria; numbers pasted into the Implementation Report.
- [ ] Speed check within budget.
- [ ] No file under `<out>/<label>/*.csv`, `FIG_*.png`, or `_provenance/` changed mtime during migration (list mtimes before/after for the pilot root).
- [ ] `HOLD_ROOTS` re-derived from the three source files and recorded.
- [ ] README, SCRIPTS_DEPENDENCY_MAP, trajectory-story skill updated in the same commit as the code they describe.

## Open decisions (for the user)

- **D1 — where scoring runs.** Plan: on the node, in the same worker job right after the test program, from a node-local copy (no NAS reads; identical scoring function on identical bytes; no edit to the test program or the Dreamer source). Alternative: inside `eval_rollout.py` from in-memory episodes (literal reading of decision 1) — needs a second scoring path for Dreamer and edits to two shared programs.
- **D2 — folder name.** Keep archives under `_scratch/` (plan) or rename to `_episodes/` (clearer, but every reader's path changes again).
- **D3 — scope of "any similar".** Plan migrates every `_scratch` under `results/eval/avoidance/` (119 roots found at depth ≤ 4). Per-episode folders elsewhere under `results/eval/` (one-off tests read directly by the video/story tools) are inventoried only. Include them?
- **D4 — pilot backup.** Rely on verified-before-delete (plan) or also take one full copy of the pilot root before deleting.
- **D5 — coordination with the neuromodulation session.** Who ports R9–R12 (that session, or `developer` after it commits), and when the hold on the healrep / modulator-engagement / injury-grid roots may be lifted.

## Implementation Report

> **Implemented by**:
> **Date**:

## Verification Report

> **Verified by**:
> **Date**:

| File | Change | Status | Notes |
|------|--------|:------:|-------|
| | | | |

**Conclusion**:
