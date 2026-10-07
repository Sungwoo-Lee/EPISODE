---
title: "Behaviour-test sweep: score on the node, bundle the raw episodes, migrate the old folders"
topic: refactors
status: active
created: 2026-10-07
last_updated: 2026-10-07
---

# Behaviour-test sweep: score on the node, bundle the raw episodes, migrate the old folders

> **Status**: PLANNED, revision 1 (answers the plan review's NOT READY verdict; user decisions D1–D5 taken 2026-10-07; not implemented)
> **Opened**: 2026-10-07
> **Related**: [scripts/eval/dwell_sweep/README.md](../../../../scripts/eval/dwell_sweep/README.md) (the pipeline this changes) · [[EVAL_ROLLOUT_BATCHING_PERF]] (the batched test path) · [[SCRIPTS_DEPENDENCY_MAP]] (maintenance contract) · [[EXPERIMENT_EVAL_DURING_TRAINING]] (a second caller of the same scoring function) · plan review: [[plan_sweep_bundles]]

---

## Context

**What the pipeline does.** The behaviour-test sweep takes a set of trained agents and, for every saved checkpoint, plays 30 test episodes in each of 12–40 fixed test scenes ("a predator is present, agent starts injured", "no animal, agent unhurt", …). From every episode it computes 11 behaviour measures (time hiding in the bush, closest approach to the animal, survival time, …) and writes one row per checkpoint into a per-scene table. Those tables feed the results pages.

**The problem (measured 2026-10-07).** The test machines write every episode to the shared NAS as separate small files — about **64 files per checkpoint × scene**. One sweep of 6 agents × 51 checkpoints × 12 scenes writes ~235,000 files; this morning's four sweeps wrote ~680,000. Playing the episodes took 13–20 minutes per sweep, but the separate scoring step then re-read every file over the NAS from one machine (8–20 minutes). One scoring run died without leaving any trace and nobody noticed for three hours.

**What this plan does.** (1) Each test machine packs a checkpoint's episodes into **one archive file per checkpoint × scene** (the same files, byte for byte), then scores them, and writes one small results table; the final step only merges tables (seconds). (2) Converts every existing test folder to archives, checking each archive against the originals — on a different machine from the one that packed it — before any original is deleted. (3) Makes a dead test machine or a dead scoring step visible within minutes.

**Why the order matters (the review's two blocking findings).** Another session's case-study tools check results *exactly* against the raw episodes, but only when they find an episode *folder*; given an archive they silently fall back to a weaker check. So those tools are switched to read archives **first**, and verified, before the test machines start writing archives. And the worker script is not touched while any sweep is still running on it (three were running at 16:03 today), because a running shell script reads its own file as it goes.

**Another session is mid-job on some of these folders.** The neuromodulation session's case study is computing now and will next run its own sweeps. Its folders are on hold — not packed, not deleted — until it says it is done (rule E4), its sweeps count as live sweeps for the "do not touch the worker" rule, and its tools are switched only after it gives the go.

**What it does not change.** The test program, seeds and scenes; the 11 measures and their formulas; the per-scene tables the pages read; the incremental "only test new checkpoints" rule.

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

`<run_tag>` varies by vintage (`20261006-074133_rppo_healrep_l05fix_t16quad_s42`, or `models` in older sweeps). Dreamer cells have only `recordings/` + `metadata.json` and episode numbers start at 1. Bundling is therefore **layout-agnostic**: pack whatever is under the cell directory, keyed by relative path. The scoring step reads the `.rec.gz` recordings (`run_sweep.py::_measure_cell`); both those and the `.npz` arrays are kept.

### A2. Where the time goes

- Workers: `sweep_worker.sh` → one `eval_rollout.py --batched --record --config-list` per checkpoint. 300 lines in 762–1172 s on one node each, this morning.
- Scoring: `run_sweep.py::aggregate()` runs on the launching container after `poll_done()` and **re-globs every step directory of each pending (run, scene) group, including previously scored steps** — 235k NAS file opens per collation of a full sweep, every time.
- `scripts/analysis/studies/f7b_across_runs/aggregate_only.py` calls the same `aggregate()`.

### A3. Why a death goes unnoticed

- `poll_done()` loops forever until `_run_markers/done_<node>` appears; a killed worker never writes it.
- `aggregate()` writes no marker; a killed collation leaves no record.
- `sweep_worker.sh` records failed calls in `fail_<node>`, which the driver never reads.
- The eval call's output goes to `/dev/null` and Python stdout to a file is block-buffered, so a node-side death leaves an empty log. **The cause of this morning's silent death** (`healrep/l05fix_grid`: workers done 11:42, no CSVs, empty `run_command` logs) **is not yet known**; Phase 0 step P0.4 makes one bounded attempt to find it (node `dmesg` / journal for an OOM kill of the 32-process pool, CIFS soft-mount I/O errors in the kernel log) and records the result. The new design does not depend on the answer: unbuffered logs, a collation heartbeat and the coverage check (F4) make any recurrence visible.

### A4. Every reader of the per-episode files (consumer inventory)

Grep over `scripts/`, `src/`, `tests/` for `_scratch`, `rec.gz`, `load_episode`, `episodes/*.npz`. Re-run in Phase 0 (P0.3), including other worktrees, because the list is the input to the deletion rule (F7).

**Class S — sweep cells** (`…/_scratch/<label>/<cond>/<step>/`):

| # | Reader | What it reads | Action | Phase |
|---|---|---|---|---|
| R1 | `scripts/eval/dwell_sweep/run_sweep.py` `_measure_cell`, `aggregate` | `**/episode_*.rec.gz` | rewrite | 3 |
| R2 | `scripts/analysis/studies/f7b_across_runs/aggregate_only.py` | via R1 | rewrite to the new collation | 3 |
| R3 | `scripts/eval/experiment_eval_checkpoint.py` (during-training eval, launched by `train.py`) | `_measure_cell(dir)` on its own output dirs | no change; `_measure_cell` keeps accepting a directory | 3 (regression test) |
| R3b | `scripts/analysis/basic_behaviour/probes.py:136` | imports `list_checkpoints, resolve_run_dir` from `run_sweep` (no episode reads) | none; its import chain changes, so its test must still pass | 3 |
| R4 | `scripts/analysis/basic_behaviour/probe_pond.py` `episodes_in` | `*/*/episodes/*.npz` + `.rec.gz` | port | 2 |
| R5 | `scripts/analysis/studies/basicq2_waves/_traj.py` | `<ck>/*/*/recordings/*/episode_*.rec.gz` | port | 2 |
| R6 | `scripts/analysis/studies/thermal_probes/t04_variance_budget.py` | `**/episode_*.rec.gz` | port | 2 |
| R7 | `scripts/analysis/studies/injury_dependence/scene_steps.py` | `<ck>/*/<ck>/recordings/<ck>/episode_*.rec.gz` | port | 2 |
| R8 | `scripts/analysis/studies/injury_dependence/run_manipulations.py` | passes a cond dir to R9 | none once R9 is ported | — |
| R9 | `scripts/analysis/obs_manipulation/run.py` `_parity` (~L407–415) | `<step>/*/<step>/recordings/<step>/episode_*.rec.gz`; raises if count ≠ N | port — **neuromodulation session's file** | 2 |
| R10 | `scripts/analysis/case_l05_s42/case.py` `_parity` (L147) | `os.path.isdir(scratch/<step>)` → exact parity via R9, **else silently a weaker CSV-mean check** | port — **neuromodulation session's file** | 2 |
| R11 | `tests/analysis/test_case_l05_s42.py:166` | calls `om._parity` **unconditionally** — on an archive-only cell it fails loudly, not silently (corrected per review L2) | port so it passes on archives — **neuromodulation session's file** | 2 |
| R12 | `tests/analysis/test_modulator_engagement.py:166` | `isdir` gate → exact-parity block **silently skipped** | port — **neuromodulation session's file** | 2 |

**Class D — direct test-program outputs** (`results/eval/<name>/models/<ck>/{episodes,recordings}/…`, written by `eval_rollout.py` outside the sweep; 19 folders besides `avoidance/` under `results/eval/` today):

| # | Reader | Action | Phase |
|---|---|---|---|
| R13 | `scripts/eval/trajectory_story.py`, `render_recordings.py`, `render_recordings_v2.py`, `render_layout_audit.py` — read a recordings **directory** | accept a `.zip` path: extract to a temp dir through `EB.extract` and proceed (thin wrapper at argument parsing; no logic change) | 2b |
| R14 | `scripts/behavior_measures/avoidance_stats_heatmap.py` collect mode, `motif_cluster.py`, `parity_check_eval_rollout.py`, `continual_forgetting_matrix.py` | port the glob to `EB.cell_path` / `EB.members` | 2b |

**The hazard behind R10–R12 (review finding C1).** Those readers test for the *directory* `…/<step>`. If any archive-only cell appears in a folder they read — whether from migration *or from a new sweep run by the new worker* — they quietly weaken (R10) or skip (R12) the exact check. Hence the order: readers switched and verified (Phase 2) **before** the worker switch (Phase 3 lands) and before any deletion (Phase M).

### A5. Live sweeps and the worker file (review finding C2)

Bash reads a running script from disk in pieces. The three no-healing sweeps launched 16:03 on nodes 104/105/112 (`configs/eval_sweeps/healrep_noheal/*`) run the current `sweep_worker.sh`; its last lines (progress line + `touch done_$NODE`) are read only after the episodes finish. Editing the file in place in the meantime can leave those sweeps without a `done_` marker, with their drivers waiting forever, or run an arbitrary fragment. At 16:42 the `grid` sweep had `done_105` but not `done_112`, and `neutral` had `done_104`; the state must be re-checked at implementation time (P0.1, gate C2-gate). Python drivers (`run_sweep.py`) are safer — the module is read at start — but the user's rule is **no edit to either file while any sweep is live**. In addition, every launch from now on runs a **copy** of the worker stored in its provenance folder (F4.6), so no later edit can reach a running worker.

### A6. Design choices (decisions D1–D5 resolved)

| Choice | Picked (user decision 2026-10-07) | Rejected and why |
|---|---|---|
| Bundle unit | one archive per checkpoint × scene cell (`<cond>/<step>.zip`, replacing `<cond>/<step>/`) | per checkpoint line (re-tests would rewrite other scenes' data); per (run, scene) append-only archive (write amplification, corruption hazard) |
| Bundle format | uncompressed ZIP (`ZIP_STORED`), members = original files byte for byte, named by path relative to the cell | a re-encoded container: verifiable only by re-parsing, not by checksum |
| **D1** where scoring happens | **on the node, in the same worker job, right after the test program, from a node-local staging copy — PACK FIRST, THEN SCORE** (review M3) | inside `eval_rollout.py`: a second scoring path for Dreamer and edits to two shared programs. Score-then-pack: a scoring error would delete the only copy of the episodes at worker exit |
| **D2** where archives live | **keep `_scratch/`**; the README stops calling it "transient; safe to delete" | `_episodes/`: every reader's path changes twice |
| **D3** migration scope | **all test folders under `results/eval/`** (class S and class D), no user approval list. Safeguards kept: M0 inventory runs and is reported (not a gate); automatic exclusion rules E1–E4 (F7) | an approval list (user declined) |
| **D4** backup | one copy of all small irreplaceable files (per-scene CSVs, figures, `_provenance/`; MBs) before the first delete; the pilot additionally passes an independent cross-machine check (pack on one node; system `unzip` + `diff -r` on a different node) before its first deletion; every `delete` runs on a different machine from the `pack` of that archive | full copy of the pilot root (1.6 GB of the same slow I/O) |
| **D5** who ports R9–R12 | **this plan's `developer`**, as Phase 2, before the worker switch; notifies the "Training: neuromodulation" session first and checks `git diff` for its uncommitted hunks; a reader class counts as switched only after an `exact` result on an archive-only cell | that session ports them (user chose otherwise) |
| Results table | one CSV per node per launch at `_scratch/_rows/<launch_id>/rows_<node>.csv` | a shared table appended by all nodes (unsafe over SMB) |

---

## Implementation Plan

### Design — data flow after the change

```
run_sweep.py SPEC [--nodes 101,103,…]
  build_groups (unchanged: incremental skip by CSV max step)
  lpt_partition over listed nodes (unchanged algorithm)
  write_provenance ──► launch_id = provenance folder name; ALSO copies sweep_worker.sh + finish_cells.py
                       + cell_measures.py into _provenance/<launch_id>/worker/ and launches THAT copy
  launch <copy>/sweep_worker.sh <worklist> <node> <npar> <episodes> <launch_id>      (one per node)
        per worklist line (one checkpoint, k pending scenes):
          eval_rollout.py --config-list (outputs → node-local /tmp staging)      [unchanged program]
          finish_cells.py, per scene:  pack staging → <cell>.zip (verify, then rename into place)
                                       → score the ARCHIVE (cell_row)            [pack first: M3]
                                       → row piece _rows/<launch_id>/<node>/<line>.csv (atomic)
          worker deletes the line's staging only after finish_cells exits 0
        heartbeat loop (dies with the worker) writes alive_<node> = "<epoch> <lines_done>"
        EXIT trap writes exit_<node>; end: concatenate pieces → rows_<node>.csv ; touch done_<node>
  poll_done: done / dead (exit, no done) / stalled (no line finished in 20 min, or heartbeat > 10 min old)
             / never started (5 min)
  collate(launch_id): collate_<id>.started + heartbeat thread collate_<id>.alive
        → coverage: every worklist cell has exactly one row, n_episodes == episodes
        → groups with ANY missing/short cell are NOT merged (listed; non-zero exit)          [M6]
        → complete groups merged into <out>/<label>/<cond>.csv (same columns + formatting) → .done / .failed
  plot (unchanged)
run_sweep.py SPEC --status          → per node: started / alive age / lines done / done / exit / fail count;
                                      per launch: never collated | running | DEAD (stale .alive) | done | failed
run_sweep.py SPEC --collate-only [--launch ID | --from-bundles]   → recovery paths
```

Single source of truth for one CSV row: **`cell_row(step, episodes)`**, called by the on-node finisher, by `_measure_cell` (dirs and archives), by `--from-bundles` recovery and by the gates. Migration uses the **same pack + verify functions** as the live finisher.

### File Changes

New config keys: **none** (no YAML schema change; `CONFIG_GUIDE.md` / `CONFIG_CRITICAL_SETTINGS.md` unaffected). New inputs are CLI flags only.

#### F1. NEW `src/utils/episode_bundle.py` (~200 lines) — format, reader, packer, verifier, guarded deleter. Lands ALONE in Phase 1.

Placed beside `eval_recording.py` (readers under `scripts/analysis/` already import `src.utils.eval_recording`). Pure Python (`zipfile`, `hashlib`, `gzip`, `pickle`, `os`, `socket`, `pathlib`); no JAX import.

```python
BUNDLE_SUFFIX = ".zip"

def cell_path(cond_dir, step) -> Path | None:
    """<cond_dir>/<step>.zip if it exists, else legacy <cond_dir>/<step>/ if it exists, else None.
    If BOTH exist: the archive wins only if the directory's newest file mtime is <= the archive's
    pack time (stored in the zip comment). A directory written AFTER the archive (an old-code
    re-test, review M7) raises CellConflict - never silently returns stale episodes."""

def members(cell, pattern="**/episode_*.rec.gz") -> list[str]   # sorted like sorted(dir.glob(pattern))
def open_member(cell, name) -> BinaryIO
def load_recording(cell, name) -> dict          # load_episode on the member's file object
def load_npz(cell, name) -> dict                # np.load(BytesIO(...)), allow_pickle=False

def pack(src_dir, zip_path) -> dict:
    """Write src_dir's tree into <zip_path>.partial-<host>-<pid> (ZIP_STORED, members sorted,
    relative POSIX names, directory entries kept). Zip comment = JSON {pack_host, pack_time, n, bytes}.
    fsync; posix_fadvise(POSIX_FADV_DONTNEED) on the partial so the re-read is not served from this
    host's page cache (review M1); verify(src_dir, partial); only then os.replace -> zip_path.
    On mismatch: delete the partial, raise BundleMismatch. Returns the manifest {name: (size, sha256)}."""

def verify(src_dir, zip_path) -> dict:
    """Exact equality or raise: same names, same sizes, same sha256 per member, testzip() is None."""

def delete_verified(cell_dir, zip_path, wal_path) -> int:
    """The ONLY function that deletes originals. In one call:
    - path guard: cell_dir matches <repo>/results/eval/**/<cond>/<digits> (class S: under _scratch/;
      class D: under models/), zip_path is its sibling <digits>.zip; refuses anything else, and
      refuses any path ending .csv/.png/.html or containing _provenance/.
    - host guard: refuses if socket.gethostname() == the zip comment's pack_host (review M1/D4).
      No flag skips it.
    - posix_fadvise DONTNEED on the zip, then verify(cell_dir, zip_path) again.
    - append (cell, name, size, sha256) for every file to wal_path and fsync BEFORE unlinking.
    - unlink exactly the verified files, then os.rmdir bottom-up (never rmtree). A file that
      appeared after verification makes rmdir fail -> raise, file left in place.
    - RESUME (review L1): if cell_dir is a partial remnant, files already listed in the WAL for this
      cell and absent on disk are accepted; files present are verified against the archive as usual."""

def extract(zip_path, dest_dir)                  # for directory-based tools (R13)
```

#### F2. NEW `scripts/eval/dwell_sweep/cell_measures.py` (~45 lines) — one CSV row

Moves today's `_measure_cell` body (`run_sweep.py:288–309`) here **verbatim in its arithmetic** (same `np.nanmean` under `warnings.catch_warnings`, same `f"{step / 1e6:.4f}"`, same `"" if not finite else f"{x:.4f}"`), parameterised on an iterable of episode payloads:

```python
from avoidance_stats_heatmap import episode_measures, KEYS   # bare-name import, sys.path as run_sweep.py
HEAD = ["step", "step_M"] + KEYS
def cell_row(step: int, episodes) -> list | None: ...        # unchanged aggregation + formatting
def measure_cell(cell) -> tuple[int, list] | None:
    """cell = legacy dir OR .zip; step = int(name without .zip); episodes in members() order."""
```

If importing `avoidance_stats_heatmap` (matplotlib/seaborn) breaks the speed budget, the follow-up is a plotting-free module re-exported by it — not done pre-emptively.

#### F3. NEW `scripts/eval/dwell_sweep/finish_cells.py` (~90 lines) — the on-node finisher

```
finish_cells.py --pairs STAGE1=CELL1 ... --rows-piece <path> --episodes N --log <per-node log>
```

Per pair, **in this order** (review M3): (1) `EB.pack(STAGE, CELL + ".zip")` — on failure: log, exit non-zero, staging kept; (2) `measure_cell(CELL + ".zip")` — the score is computed from the archive just written, not from staging; (3) collect `[run_label, cond] + row + [n_episodes, numpy_version, bundle_relpath]`. A scoring exception is logged with traceback, the archive stays, the cell gets no row (the coverage check reports it; `--collate-only --from-bundles` recovers it). Rows of the line → `<rows-piece>.tmp` → `os.replace`. Exit non-zero if any cell failed or `n_episodes != N`. Rows table columns: `run_label, cond, step, step_M, <11 measures>, n_episodes, numpy_version, bundle` (review M8).

#### F4. `scripts/eval/dwell_sweep/run_sweep.py` (563 lines; expected net +190 / −40). **Edited on disk only after gate C2-gate (Phase 3).**

1. **Imports (L47–52):** import `cell_row, measure_cell, HEAD` from `cell_measures`; `import src.utils.episode_bundle as EB`. F2 and F4 land in **one commit** (review L3: `experiment_eval_checkpoint.py:52` imports `run_sweep` at module top, outside its failure wrapper, and is launched by live training runs).
2. **`_measure_cell` (L288–309):** `return measure_cell(step_dir)` — same name/signature; dir or `.zip` (R3).
3. **`aggregate()` (L312–365) → `collate(groups, scratch_root, launch_id, nodes, worklist_cells, episodes)`:** reads `_rows/<launch_id>/rows_<node>.csv`; coverage check — every worklist `(label, cond, step)` has exactly one row with `n_episodes == episodes`. **A (run, scene) group with any missing or short cell is not merged at all** (review M6; partial merging would let the max-step incremental rule skip the holes forever); listed, and the function exits non-zero after writing the complete groups. Merge/write logic of L327–330, L353–364 kept verbatim. The old function survives as `aggregate_from_bundles(groups, scratch_root, n_workers, seed_from_csv=True)` — glob replaced by `EB.cell_path`/`measure_cell`; `seed_from_csv=False` is what the gates use (review M2).
4. **Collation markers + heartbeat (review M5):** `_with_collate_markers(scratch_root, launch_id, fn)` writes `collate_<id>.started` (host, pid, time, n groups); starts a daemon thread touching `collate_<id>.alive` every 60 s; `.done` on success, `.failed` (traceback) in `except`. `--status`: `.started` with `.alive` older than 5 min and no `.done`/`.failed` → **DEAD**, on any host; all `done_` present but no `.started` → **"workers done, never collated"**.
5. **`write_worklist()` (L233–250):** unchanged.
6. **`launch_node()` (L253–259) + `write_provenance()` (L398–431) — launch-time worker copy (C2):** `write_provenance` additionally copies `sweep_worker.sh`, `finish_cells.py`, `cell_measures.py` into `_provenance/<launch_id>/worker/` (plus their sha256 into the provenance JSON); `launch_node` runs the copied `sweep_worker.sh`, which calls the copied `finish_cells.py` (with `sys.path` still pointing at the repo for `src.utils.episode_bundle` and `avoidance_stats_heatmap` — a stated limitation: edits to those two library modules can still reach a running sweep; they are imported per line by fresh Python processes). `launch_id` is passed as the 5th worker argument. Every node-launched command sets `PYTHONUNBUFFERED=1`.
7. **`poll_done()` (L262–274) → liveness-aware (review M4):** per node, each interval: `done_<n>` → done; `exit_<n>` and no `done_<n>` → **dead**; `alive_<n>` older than `HEARTBEAT_STALE_S = 600` → **stalled**; lines-done counter in `alive_<n>` unchanged for `PROGRESS_STALE_S = 1200` → **stalled**; no `started_<n>` within `START_GRACE_S = 300` → **never started**. Unhealthy node: print its `prog_`/`fail_`/log tail, write `FAILED_<n>`, finish waiting for healthy nodes, collate (complete groups only), `SystemExit(2)`. Module constants (operational thresholds, not experiment settings). `poll_done` takes an injectable clock + interval for tests.
8. **Stale-marker clearing (L541–545):** also clear `exit_`, `alive_`, `started_`, `FAILED_` for launched nodes.
9. **`fail_<node>` reporting:** after polling, print count + first lines of every `fail_<node>`; non-zero exit if any.
10. **New CLI:** `--nodes 101,103,…` (overrides `spec.nodes`; recorded in provenance), `--status`, `--collate-only [--launch ID | --from-bundles]` (refuses if any node of the launch lacks `done_`, unless `--from-bundles`).
11. **Node choice warning (review M10):** if one node and > 50 pending lines, print a warning to list more nodes, defining a usable node as: **no training process running (`pgrep -f train.py`), no other sweep's live markers on it, no diary claim for today** — not merely "GPU free" (the job is CPU-bound, 18 processes per node). Warning only.
12. **Lock against migration:** refuse to launch into a root holding `_scratch/_bundle.lock` unless the lock is stale (F7 rule).
13. **Old-code interlock (review M7):** the driver writes `_scratch/_format` = `bundles-1` on first new-code launch into a root. `bundle_scratch.py` treats a root as live while any old-code process exists (E1), and `cell_path` raises on a directory newer than its archive (F1), so an old checkout's re-test cannot be silently shadowed.

#### F5. `scripts/eval/dwell_sweep/sweep_worker.sh` (84 lines; expected net +55). **Edited on disk only after gate C2-gate.**

- Signature: `sweep_worker.sh <worklist> <node> <npar> <n_episodes> <launch_id>` (5th arg mandatory; error if missing). `set -o pipefail`. `export PYTHONUNBUFFERED=1`.
- Start: `echo "host=$(hostname) pid=$$ $(date +%s)" > $MARK/started_$NODE`. Heartbeat **tied to the worker** (review M4a): `WPID=$$; ( while kill -0 $WPID 2>/dev/null; do echo "$(date +%s) $(wc -l < $MARK/lines_$NODE 2>/dev/null || echo 0)" > "$MARK/alive_$NODE.tmp" && mv "$MARK/alive_$NODE.tmp" "$MARK/alive_$NODE"; sleep 60; done ) &`. Each finished line appends one line to `lines_$NODE`.
- `trap 'rc=$?; kill $HB 2>/dev/null; echo "rc=$rc $(date +%s)" > "$MARK/exit_$NODE"' EXIT`. The trap does **not** delete staging (review M3): staging dirs that still exist at exit are listed in `exit_$NODE` and left in `/tmp` for recovery; successful lines delete their own staging.
- `STAGE_ROOT=/tmp/dwellsweep_${LAUNCH_ID}_${NODE}_$$`; per line `stage=$(mktemp -d -p "$STAGE_ROOT")`; the `--config-list` maps each scene to `$stage/<k>`; after `eval_rollout.py` succeeds, `finish_cells.py --pairs … --rows-piece "$ROWS/<node>/<line-hash>.csv" --episodes "$NEP" --log "$LOG/finish_$NODE.log"`; on success `rm -rf "$stage"`; on failure append `FAIL <stage> <line>` to `fail_$NODE`. `eval_rollout.py` stderr goes to `$LOG/eval_$NODE.log` instead of `/dev/null` (review M5).
- End: record `xargs` exit status in `prog_$NODE`; concatenate pieces → `rows_$NODE.csv` (tmp + `mv`); `touch done_$NODE`. A killed `xargs` therefore still ends in `done_` — **its detection is the collation coverage check** (missing cells listed, non-zero exit), which is mandatory (review M4b).
- Thread caps, compile cache, xargs `-P $NPAR` unchanged.

#### F6. `scripts/analysis/studies/f7b_across_runs/aggregate_only.py` (43 lines)

Thin wrapper over `--collate-only` semantics: default reads the newest launch's rows tables; `--from-bundles` calls `aggregate_from_bundles` with its own `--workers` (keeps the container-load safeguard). Keeps the done-marker refusal. Lands with F4.

#### F7. NEW `scripts/eval/dwell_sweep/bundle_scratch.py` (~260 lines) — migration CLI

Roots: `--all` = every class-S `_scratch` and every class-D test folder under `results/eval/` (D3), found by `os.walk`; or explicit roots.

- `inventory` — read-only, always runs first, reported to the user (not a gate). Per root: class, legacy cells, archived cells, files, bytes, live-sweep state, **whether the source checkpoints still exist** (flag `ckpt_missing`; review D4), and which exclusion rule (E1–E4) currently applies. Writes `tmp/<stamp>_bundle_inventory.csv`.
- `backup-tables` — one-time copy of every per-scene CSV, `FIG_*.png`, `*.html` and `_provenance/` under `results/eval/` to `results/_backup/eval_tables_<stamp>/` (same relative paths); verified by sha256 list; refuses to proceed if the copy and the list differ. Required before the first `delete` (`delete` checks the backup marker exists).
- `pack [--dry-run] [--into <gate dir>]` — `EB.pack` for each legacy cell without a valid sibling `.zip` (skips E4-held cells unless `--into` writes outside the held root, which is read-only use). Originals untouched. Resumable (leftover `.partial-*` deleted and redone).
- `verify` — re-verifies every cell with both forms; `_bundle_log/verify_<host>_<stamp>.csv`.
- `gate` — Gate G1 for a class-S root (below): `aggregate_from_bundles(seed_from_csv=False)` into an **empty** temp dir, compared to `<out>/<label>/<cond>.csv`.
- `delete` — for each cell with both forms: `EB.delete_verified(...)` (which refuses on the packing host). Refuses a root unless (a) its latest `verify` report, written **on this host**, is all-OK; (b) for class S, its `gate` report is all-OK, or the row differences are only those listed in the root's inventory as "CSV older than measure code" — those roots are skipped and listed, not deleted; (c) none of E1–E4 applies; (d) `ckpt_missing` roots additionally have an independent-check report (system `unzip` + `diff -r`, as in M1) — they cannot be regenerated.
- `independent-check <root> [--sample N|--all]` — on the current host: system `unzip -q` each archive into `/tmp`, `diff -r` against the original cell; refuses if run on the packing host; writes `_bundle_log/indep_<host>_<stamp>.csv`.
- `extract <zip> <dest>` — for R13 tools.

**Automatic exclusions (D3; replace the review's allow-list, fail closed):**

- **E1 live or possibly live (review M7):** any `npar_`/`started_` marker newer than its `done_`; any `alive_` < 10 min old; any `collate_*.started` without `.done`/`.failed`; all `done_` present but no per-scene CSV newer than the newest `done_` ("possibly collating"); any `run_sweep.py`, `aggregate_only.py` or `sweep_worker.sh` process on the container (`ps`) or on any node (`ssh <node> pgrep -af`), whose spec or worklist names the root. The scan runs at the start of each `delete` for each root, not once.
- **E2 unswitched reader:** the module constant `SWITCHED_READERS = {"S": [...], "D": [...]}` lists readers whose archive support has been verified `exact` (Phase 2 / 2b). At each run, `delete` re-greps `scripts/ src/ tests/` (and every worktree under the repo) for the reader patterns of A4; **any hit not in `SWITCHED_READERS` for that class blocks deletion for the whole class** and is printed. A new reader added tomorrow therefore blocks, rather than being missed (review M11). Pack and verify are allowed; only deletion is blocked.
- **E4 session hold (requested by the "Training: neuromodulation" session, 2026-10-07):** module constant `SESSION_HOLDS` — **neither `pack` nor `delete`** touches a held cell. Held: every `_scratch/<label>/` whose label resolves (via the root's spec / provenance `run_dir`) to a training run named `*healrep_l05_*` (seeds s42, s43), `*healrep_l05fix_*s42*`, the 22-Sep `*bq2cover_lvl05_s42*` pair; and every cell under the roots `metrics_history_rppo_modeng_e4/` and `metrics_history_rppo_case_l05_s42/` (the case study's own sweeps). A label that cannot be resolved to a run is treated as held (fail closed). Holds are lifted only by that session's explicit "done" message (relayed via the session board, the coordinator, or the user), recorded in the Implementation Report with date and source, in the commit that edits `SESSION_HOLDS`. Inventory reports held cells separately. Consequence: the original pilot root `healrep/l05fix_own` (labels `l05fix_*_s42`) is held — G1 and the Phase 2 check only **read** it (packing into a separate gate folder), and the deletion pilot moves to another root (Phase M1).
- **E3 lock:** `_scratch/_bundle.lock` (`O_CREAT|O_EXCL`, contents host/pid/start). Stale rule (review L1): stale if older than 6 h with no update, or same host and pid dead; a stale lock is reported and removed only by `bundle_scratch.py unlock <root>`, which prints the lock's contents first.

Safety rails (structural): nothing outside cell paths is ever opened for write/delete (path guard in `EB.delete_verified`, tested); the per-scene CSVs, figures and `_provenance/` are never deletable.

#### F8. Reader ports (Phase 2 / 2b)

Each replaces its glob with `EB.cell_path` + `EB.members` + `EB.load_recording` / `EB.load_npz`, keeping its own logic; each accepts legacy dirs **and** archives:

| File | Lines | Phase |
|---|---|---|
| `scripts/analysis/basic_behaviour/probe_pond.py` | `episodes_in` L126–137, caller L319 | 2 |
| `scripts/analysis/studies/basicq2_waves/_traj.py` | `_episodes` L33–45 | 2 |
| `scripts/analysis/studies/thermal_probes/t04_variance_budget.py` | L27–40 | 2 |
| `scripts/analysis/studies/injury_dependence/scene_steps.py` | L60–75 | 2 |
| `scripts/analysis/obs_manipulation/run.py` | `_parity` ~L407–415: `cell = EB.cell_path(sweep_dir, step)`; raise if `None`; `recs = EB.members(cell)`; `EB.load_recording(cell, name)` | 2 (neuromodulation session's file) |
| `scripts/analysis/case_l05_s42/case.py` | `_parity` L147: `if EB.cell_path(scratch, step) is not None:` | 2 (same) |
| `tests/analysis/test_case_l05_s42.py` | L166 (unconditional call; passes once R9 reads archives) — add an archive-only case | 2 (same) |
| `tests/analysis/test_modulator_engagement.py` | L166: same one-line change as case.py | 2 (same) |
| R13 tools (4 files) | `.zip` argument → `EB.extract` to a temp dir | 2b |
| R14 readers (4 files) | glob → `EB` | 2b |

Line numbers are as of commit `d0c8f5b4`; the developer re-reads each file before editing.

#### F9. Coordination with the "Training: neuromodulation" session (D5)

That session (session id prefix `96e71c7b`) said on 2026-10-07 that its readers had no uncommitted edits at that moment (latest commits `d0c8f5b4`, `e62ccd86`) but may change during its current case-study job (computing on node 108, followed by freeze-scoring sweeps through this pipeline). **Phase 2 does not start without that session's explicit go.** Before touching any of its four files (R9–R12), the developer:

1. messages the session: `python scripts/claude/session_board.py note "senior-dev plan SWEEP_EPISODE_BUNDLES: developer asks for your go to edit obs_manipulation/run.py _parity, case_l05_s42/case.py _parity, test_case_l05_s42.py, test_modulator_engagement.py (archive-aware episode reads; behaviour unchanged on folders). Please reply go / not yet."`, checks `session_board.py show` for its current task, and, if its pane is live in tmux, sends the same message through the `tmux-claude` skill. **Waits for an explicit "go"** (via the board, the coordinator or the user); no reply = no go. Records the go (date, source) in the Implementation Report;
2. after the go, runs `git diff -- <file>` and `git diff --cached -- <file>` on each; **any hunk that is not ours → stop for that file**, ask the session, never commit another session's hunk;
3. makes only the edits in F8; commits each with an explicit pathspec; posts a second board note naming the commit, so the session rebases its own work onto it.

#### F10. Tests

- **NEW `tests/scripts/test_episode_bundle.py`** (no checkpoints, no NAS; synthetic recordings via the real `EpisodeRecorder.write` + `np.savez_compressed`): `test_pack_roundtrip_bytes_equal`; `test_pack_preserves_empty_dirs_and_nested_layout`; `test_measure_cell_dir_equals_zip` (rPPO 0-based and Dreamer 1-based layouts); `test_verify_detects_changed_byte` / `…_missing_member` / `…_extra_source_file`; `test_delete_refuses_after_source_changed`; `test_delete_leaves_file_created_after_verify`; `test_delete_path_guard` (CSV, PNG, `_provenance/` never deletable); `test_delete_refuses_on_packing_host` (monkeypatched hostname); `test_delete_resumes_from_wal`; `test_pack_is_atomic`; `test_cell_path_raises_on_dir_newer_than_zip`.
- **NEW `tests/scripts/test_dwell_sweep_collate.py`**: `test_collate_matches_aggregate_from_bundles` (byte-identical CSVs); `test_collate_merges_without_dropping_old_rows`; `test_collate_raises_on_missing_cell` / `…_on_short_episode_count`; `test_incomplete_group_not_merged_and_retested` (after a dead node, `build_groups` on the next launch lists the missing lower steps — review M6); `test_poll_detects_dead_worker` / `…_stalled_heartbeat` / `…_no_progress` / `…_never_started`; `test_status_reports_dead_collation_any_host` (stale `.alive`); `test_status_workers_done_never_collated`; `test_gate_fails_on_empty_archives` (archives with no recordings → G1 fails, not vacuous pass — review M2).
- **Regression test for the silent-death bug:** `test_poll_done_does_not_wait_forever_on_dead_worker` — must **fail (5 s timeout) on the current `poll_done`** and pass after; output pasted into the Implementation Report.
- **NEW `tests/scripts/test_bundle_scratch_exclusions.py`**: E1 (live markers, possibly-collating), E2 (an unregistered reader file in a temp tree blocks deletion), E3 (stale lock rule).
- **Existing tests that must still pass:** all `run_sweep` / `_measure_cell` importers (`grep -rl "run_sweep\|experiment_eval_checkpoint" tests/`), `tests/analysis/test_basic_behaviour.py`, `tests/scripts/test_eval_rollout_online_replay.py`, `tests/algorithms/dreamer_srl/test_eval_rollout_batched.py`, `tests/analysis/test_case_l05_s42.py`, `tests/analysis/test_modulator_engagement.py`.

#### F11. Docs (same commit as the code they describe)

- `scripts/eval/dwell_sweep/README.md`: Files table (+`cell_measures.py`, `finish_cells.py`, `bundle_scratch.py`); "On-node packing, scoring and rows tables" replaces "Recursive-glob aggregation"; Output layout (`<step>.zip` cells, `_rows/<launch_id>/`, new markers, `_provenance/<id>/worker/`); **`_scratch/` no longer described as safe to delete — it holds the kept episode archives; only `_worklists/`, `_run_markers/`, `_rows/` are transient** (D2); Node safety (usable-node definition of F4.11); "Liveness and `--status`"; "Reading raw episodes" (EB API + `extract`); "Migrating old folders" (exclusions E1–E4, cross-host rule).
- `docs/environment/SCRIPTS_DEPENDENCY_MAP.md`: rows for the three new scripts and `src/utils/episode_bundle.py`'s script callers; `run_sweep.py` row (new import; `_measure_cell` still exported; worker launched from the provenance copy); `sweep_worker.sh` (5th arg, `finish_cells.py` subprocess); `aggregate_only.py`; `probe_pond.py` and **`probes.py` → `run_sweep` edge** (review L3); R5–R7, R9–R14 rows if present. **This file had uncommitted edits from another session on 2026-10-07: `git diff` it before staging; if a hunk is not ours, coordinate, do not commit it.**
- `.claude/skills/trajectory-story/SKILL.md`: one line — sweep and test recordings may be archives; tools accept a `.zip`.
- Hand-off to `bug-curator` (not edited by us): append "scoring now runs on nodes; `numpy` version is in every rows table" to the node-env-drift row (review M8).

### Phase order, gates, and stop points

Each phase ends with its own commit(s) (explicit pathspec, pushed). No phase starts before the previous one's checks pass.

**Phase 0 — read-only preflight.**
- P0.1 Live sweeps: list every `_run_markers` under `results/eval/` with `npar_`/`started_` newer than `done_`; `ps -ef | grep -E "run_sweep|aggregate_only|sweep_worker"` on the container; `ssh <node> pgrep -af "sweep_worker|eval_rollout|run_sweep"` on 101–114. Record in the Implementation Report.
- P0.2 Node env (review M8): on every node 101–114, with the project interpreter: print `numpy` version, `import avoidance_stats_heatmap`, `which unzip`. A node that fails the import is not used for sweeps until fixed (report, do not fix envs in this plan).
- P0.3 Reader re-grep (A4) incl. worktrees; any new reader is added to F8 before Phase 2.
- P0.4 One bounded attempt (≤ 30 min) at the cause of the 11:42 silent collation death (A3); record the finding or "not determined".

**Phase 1 — `src/utils/episode_bundle.py` alone + `tests/scripts/test_episode_bundle.py`.** Nothing imports it yet; safe while sweeps run. Commit.

**Phase 2 — switch class-S readers (C1, D5). Starts only after the neuromodulation session's explicit go (F9 step 1).** Then the F8 class-S ports (R4–R7, R9–R12). R4–R7 (this plan's own files) may be ported before the go.
- **Verification — archive-only cell, positive `exact`.** Build a throwaway class-S root `results/eval/avoidance/_bundle_gate/readers/` by **copying** (never moving) one (label, scene) group of `healrep/l05fix_own` (the case study's sweep) and packing its cells there with `EB.pack`, then removing the copied directories so only archives remain. Point the ported `obs_manipulation/run.py --check-against-sweep`, `case.py`'s parity path and both tests at it. Pass criterion, pre-stated: each reports `exact` (not the CSV-mean fallback, not a skip), and the same call on the original folder-form cell also reports `exact`. R4–R7: their outputs on the archive-only copy equal their outputs on the folder copy (string-equal printouts / files).
- Then add the class-S readers to `SWITCHED_READERS["S"]` (in the Phase 3 code). Commit per file.

**Phase 2b — switch class-D readers (R13, R14).** Same pattern: copy one class-D test folder to `_bundle_gate/direct/`, pack, run each reader on both forms, outputs equal. Until this passes, class-D folders are excluded from deletion by E2 automatically (they may still be packed). Phase 2b may run after Phase 3 without blocking it.

**Gate C2-gate — before ANY edit to `sweep_worker.sh` or `run_sweep.py` in the shared folder.** Development of F2–F6 happens in a git worktree; the shared folder's copies change only when **all** of these hold, checked at that moment: (a) P0.1's checks show no live sweep anywhere (every launch's `done_` for all its nodes, no driver process on the container, no `sweep_worker`/`eval_rollout` on any node) — **this covers every session's sweeps, not just ours**, in particular the neuromodulation session's freeze-scoring sweeps; (b) today's diary (`docs/diary/YYYY-MM-DD.md`) and `session_board.py show` list no running or announced sweep; (c) the neuromodulation session has confirmed it has no sweep running or about to start (its next sweeps would otherwise switch format mid-job). Today (a) means the three no-healing sweeps of 16:03 (nodes 104/105/112) have finished and their drivers exited. If any check fails, wait; do not edit. From this commit onward every launch runs its provenance copy (F4.6), so this gate is needed only once.

**Phase 3 — new pipeline (F2–F6, F7, F10, F11) merged into the shared folder after C2-gate.** F2 + F4 + F6 in one commit. Unit tests green.

**Gate G1 — scoring from archives reproduces today's tables exactly (existing data).** Benchmark: `metrics_history_rppo_healrep/l05fix_own` (one launch, commit `b2ba9cf`, node 105). That root is under the E4 hold, so it is **only read**: `bundle_scratch.py pack --into results/eval/avoidance/_bundle_gate/g1/` writes the archives into a separate gate folder mirroring its layout (nothing is written into the held root) → `verify` → `gate` against the held root's CSVs. **Pass criterion, pre-stated, zero tolerance (review M2):** computed into an empty dict, no CSV seeding; every archive yields exactly 30 recordings; the set of computed (run, scene, step) keys equals the set of CSV rows exactly; every row's 13 strings identical; all 72 CSVs byte-identical.

**Gate G2 — the new on-node path reproduces today's tables exactly (fresh tests).** Spec copy in `tmp/` with `output_dir` `results/eval/avoidance/_bundle_gate/l05fix_own`, `--max-checkpoints 2`, all 6 runs, `--nodes` = **105 (the original node) plus at least one node of a different card/CPU generation** (review M9), all usable per F4.11. Pass criteria, pre-stated: (a) all 144 new rows string-identical to the current CSV; (b) every recording in each new archive decodes equal to the G1 archive's member (`snapshots` dict-by-dict `np.array_equal`; `obs`, `true_obs`, `actions`, `rewards` `np.array_equal`; scalars `==`; `.npz` arrays equal); (c) `numpy_version` column recorded per node; (d) collation wall time recorded. **A mismatch only on cells scored/tested on a node other than 105 is reported as a cross-node determinism finding** (it would also matter to `obs_manipulation`'s exact parity) — escalate to the user, not counted as a pipeline bug; a mismatch on 105 is a bug.

**Gate G3 — Dreamer keeps working.** `configs/eval_sweeps/basic04_rr_dreamer.yaml` copy in `tmp/`, fresh `output_dir`, `--max-checkpoints 1`, one run: (a) worker completes, archive written, row present; (b) row string-identical to the existing Dreamer CSV row at that step if one exists, else `rows table == measure_cell(archive)` and batched-Dreamer determinism is reported, not forced.

**Speed check.** Same node (105), same spec, same seed: old vs new worker wall time for G2's workload (old worker run from the commit before Phase 3, in a worktree, into a separate throwaway output dir). Budget ≤ 5 % slower; collation wall time old (`aggregate()` on legacy cells) vs new; files per cell (64 → 1). **Stop and report if > 5 %.**

**Phase M — migration (all of `results/eval/`, D3).**
- **M0 inventory** (read-only, `--all`). Reported to the user with counts, bytes, `ckpt_missing` flags and which exclusion applies. Not a gate.
- **M0.5 `backup-tables`** (D4). Must succeed before any `delete`.
- **M1 pilot root — chosen from the M0 inventory**, not `healrep/l05fix_own` (held, E4): the first class-S root that is not held, not live, has all source checkpoints present, was written by one launch with current measure code, and is read by at least one switched parity reader if any such root exists (else by R4–R7). The choice and reason go into the Implementation Report. (1) pack + verify (host A); (2) G1-style `gate` on this root passes; (3) **independent cross-machine check (D4, review M1):** on host B ≠ A, `bundle_scratch.py independent-check --all` (system `unzip` + `diff -r`) — all cells identical; (4) Phase 2 verification passed; (5) E1–E4 clear; (6) `delete` on host B → re-run `gate` from archives alone (must pass) → re-run one switched reader on the archive-only pilot (a parity reader if it reads this root: must report `exact`; else R4–R7: output equal to its pre-delete output) → report files and bytes before/after and the mtimes of `<out>/<label>/*.csv`, `FIG_*.png`, `_provenance/` before/after (must be unchanged).
- **M2 all class-S roots:** `pack` (host A) → `verify` + `gate` (host B) → `delete` (host B) where E1–E4 clear and gate all-OK. Roots whose gate differs (CSV written by older measure code, rows whose cells were already removed) are listed, not deleted. `ckpt_missing` roots need an `independent-check` report first.
- **M3 class-D folders:** after Phase 2b, same procedure (no `gate` — there is no per-scene CSV; byte verification + `independent-check` sample of 5 % per folder, all for `ckpt_missing`).

## Checkpoints

- [x] P0.1–P0.4 results recorded (live sweeps, node numpy versions + import check, reader re-grep, 11:42 death finding). (2026-10-07 17:10, developer: see Implementation Report, Phase 0; P0.1 must be re-run at C2-gate time.)
- [x] Phase 1 committed alone; nothing else imports `episode_bundle` at that commit. (2026-10-07, developer: library + 38 tests; only the test file imports it.)
- [ ] Neuromodulation session's explicit go recorded (date, source) before Phase 2's edits to its files; `git diff` checked on each; no foreign hunk committed.
- [ ] `SESSION_HOLDS` (E4) implemented as listed; no archive written into, and no file deleted from, a held cell (inventory before/after); any hold lift recorded with its source.
- [ ] Phase 2: ported parity tools report `exact` on an archive-only cell and on the folder-form cell; outputs pasted. (Partial, 2026-10-07: this plan's own readers R4–R7 ported and exact on both forms; R9–R12 still wait for the neuromodulation session's go.)
- [ ] C2-gate evidence (markers + `ps` + node `pgrep`) pasted, timestamped, immediately before the shared-folder worker/driver edit.
- [ ] Every launch after Phase 3 has `_provenance/<id>/worker/` and the driver ran that copy (`ps` on a node shows the provenance path).
- [ ] `cell_row` is the only place the row arithmetic exists (`grep nanmean scripts/eval/dwell_sweep/` → one hit).
- [ ] `experiment_eval_checkpoint.py` still imports `_measure_cell, HEAD, KEYS` from `run_sweep` and works on a directory; `probes.py` test passes.
- [ ] Regression test `test_poll_done_does_not_wait_forever_on_dead_worker` shown failing on the pre-change `poll_done`.
- [ ] `--dry-run` on the `l05fix_own` spec prints the 5-argument command against the provenance copy and unchanged LPT loads.
- [ ] Throwaway output dir: `kill -9` the worker bash on one node → `alive_` stops (heartbeat loop exits), `poll_done` reports stalled/dead within 11 min; `kill -9` its `xargs` → `done_` is written but collation lists the missing cells and exits non-zero; `--status` shows both.
- [ ] `kill -9` during `--collate-only --from-bundles` launched on a node → `--status` on the container shows `DEAD` within 6 min.
- [ ] G1, G2, G3 pass with the pre-stated criteria; numbers pasted.
- [ ] Speed check within budget.
- [ ] M0.5 backup sha256 list matches; M1 independent-check report all-identical, run on a host different from the packing host; deletes ran on host B.
- [ ] No per-scene CSV, figure or `_provenance/` file changed mtime during migration (pilot list before/after).
- [ ] README, SCRIPTS_DEPENDENCY_MAP (diffed for foreign hunks), trajectory-story skill updated in the same commit as the code; `bug-curator` handed the env-drift note.

## Decisions (resolved by the user, 2026-10-07)

- **D1** — score on the node right after the test program; pack before scoring.
- **D2** — keep `_scratch/`; README no longer calls it safe to delete.
- **D3** — migrate all test folders under `results/eval/`, no approval list; inventory reported; automatic exclusions E1–E4; `ckpt_missing` flagged.
- **D4** — small backup of tables/figures/provenance before the first delete; independent cross-machine check on the pilot; deletes on a different machine from packing.
- **D5** — our developer ports R9–R12 in Phase 2, after the neuromodulation session's explicit go (added at that session's request, 2026-10-07) and checking its uncommitted hunks; verified `exact` on an archive-only cell before the worker switch.

## Implementation Report

> **Implemented by**: developer (Phase 1; Phase 0 and Phase 2 R4–R7 on 2026-10-07 evening)
> **Date**: 2026-10-07

### Phase 1 — archive library

**Scope kept.** Only Phase 1 was implemented. `sweep_worker.sh`, `run_sweep.py`, every reader (R1–R14) and the neuromodulation session's four files were not touched (sweeps are live on 104/105 and 106/107; that session has not given its go). Nothing was packed, verified-deleted or deleted under `results/`; all tests use pytest temporary directories. Phase 0 (P0.1–P0.4) was not run in this pass — it is read-only preflight for Phase 2/3 and was outside the task given.

**Files.**
- NEW `src/utils/episode_bundle.py` — `cell_path`, `members`, `read_member`/`open_member`, `load_recording`, `load_npz`, `pack`, `verify`, `delete_verified`, `extract`, `read_comment`; exceptions `BundleMismatch`, `CellConflict`, `DeleteRefused`. Pure Python + numpy, no JAX.
- NEW `tests/scripts/test_episode_bundle.py` — 38 tests (parametrised), synthetic cells from the real `EpisodeRecorder.write` + `np.savez_compressed`, both layouts (rPPO 0-based with `.npz`/parquet/json; Dreamer 1-based recordings only).
- `docs/environment/SCRIPTS_DEPENDENCY_MAP.md`: **not changed** — Phase 1 adds no file under `scripts/` and no script imports the library yet. The map rows for `episode_bundle.py`'s script callers belong with Phase 2/3.

**Plan-reviewer re-review fixes that belong to Phase 1.**
- **N1 (repo root).** `delete_verified(cell_dir, zip_path, wal_path, *, repo_root)` — `repo_root` is a required keyword argument with no default; omitting it is a `TypeError`. The library never reads `__file__` (a test asserts this). N1's main part (the copied worker and `finish_cells.py` must receive the repo root as a mandatory argument) is Phase 3 code and is not done here.
- **N7 (`NON_READERS`).** Not applicable to Phase 1: the reader re-grep (E2) lives in `bundle_scratch.py` (F7, Phase 3). To be done there: a `NON_READERS` constant with a one-line reason per entry, separate from `SWITCHED_READERS`; candidates seen today are `src/utils/episode_bundle.py` itself, `src/utils/eval_recording.py` (writer + `load_episode` definition), `scripts/eval/eval_rollout.py` (writer), `scripts/eval/dwell_sweep/README.md`.
- **Addendum (a), class D dropped.** The path guard in `delete_verified` accepts class S only: `<repo_root>/results/eval/**/_scratch/<label>/<cond>/<digits>`, label/cond not starting with `_`, archive must be the sibling `<digits>.zip`.
- **N2 (defensive part).** A cell holding any `.csv/.png/.html/.mp4/.gif/.npy/.txt` file, or any path containing `_provenance/`, `videos/` or `motifs/`, is refused whole (fail closed) — a sweep cell never holds these.

**Deviations from F1 (all stricter, none silent).**
1. **Conflict rule uses filesystem times, not the host clock.** F1 says the archive wins if the folder's newest file mtime is ≤ the archive's *pack time*. Pack time comes from the packing host's clock while file mtimes come from the NAS, so clock skew could flip the answer. The zip comment stores `src_mtime_max_ns` (newest source-file mtime seen at pack) alongside `pack_time`, and `cell_path` compares against that. Only file mtimes are compared (directory mtimes change during a delete). A comment without these fields raises (fail closed).
2. **`pack` refuses to overwrite an existing archive** (`FileExistsError`) rather than `os.replace`-ing over it. Resumability of `.partial-*` leftovers stays with `bundle_scratch.py`.
3. **`delete_verified` re-checks each file's size + mtime after verification and before any unlink**, and refuses if the file list changed during verification — narrows the window between verify and unlink. Symlinks inside a cell are refused at pack/verify.
4. **`extract` verifies the extracted tree against the archive** and refuses a non-empty destination.
5. **`test_measure_cell_dir_equals_zip`** is in its Phase-1 form: `cell_measures.measure_cell` does not exist until Phase 3, so the test checks (a) every recording/`.npz` decodes identically from folder and archive in the same order, and (b) the current `run_sweep._measure_cell` gives the same row on the original folder and on a folder extracted from the archive. The direct `measure_cell(zip)` comparison is to be added in Phase 3.
6. Extra tests beyond F10: `members` order equals `sorted(Path.glob(pattern))` for five patterns × two layouts (12 episodes so ordering is non-trivial); corrupt archive bytes detected; `repo_root` required; a file created after the unlink pre-check survives (rmdir, not rmtree).

**Tests.**
```
/home/vncuser/miniconda3/envs/grid_world_pain/bin/python -m pytest tests/scripts/test_episode_bundle.py -q
38 passed in 2.83s
```
NAS smoke (scratch dir under `tmp/`, a CIFS mount; not `results/`): a 30-episode rPPO cell (64 files) packed and verified in 0.18 s; `os.posix_fadvise(POSIX_FADV_DONTNEED)` raises no error on CIFS. Whether it actually drops the CIFS page cache is still untested (the re-review's open assumption) — the cross-host `independent-check` remains the real safeguard.

**Speed check.** Skipped: nothing on the training or sweep hot path imports the new module at this commit (only the test file does).

**Blockers / notes for Phase 2.**
- Phase 2's ports of R9–R12 still need the neuromodulation session's explicit go (F9); R4–R7 can start now.
- `members(cell, pattern)` reproduces `Path.glob` semantics for `*`, `?`, `[...]` and `**/`; patterns are matched against member names relative to the cell, so readers that today glob from a level above the cell (e.g. `<ck>/*/*/recordings/...` from the cond dir) must first resolve the cell with `cell_path(cond_dir, step)` and drop the leading step component from their pattern.
- Plan-review N3–N6 are unaddressed by design (scope of senior-developer / Phase 3 / operations).

### Phase 0 — read-only preflight (2026-10-07, 17:09–17:20)

Raw output: `tmp/20261007_*_bundles_phase0.md` (scratch, not committed).

- **P0.1 live sweeps.** Run markers with `npar_` and no `done_`: `nmncap/{l05_gridchase,l05_own}` (node 107), `nmncap/l05_grid` (106, 107), `nmncap/l05_neutral` (106) — all live: four `run_sweep.py` drivers (PIDs 3406456/3406511/3406585/3406611, started 16:51) on the container, `sweep_worker.sh` processes on 106 and 107. `healrep_noheal/grid` node 112: `npar_112` 16:03, no `done_112`, **no worker process on 112** — the dead sweep of re-review N4, still unresolved. Stale old markers: `metrics_history_dreamer_basic04_size` (102, July), `dp1/dreamer_bins6` (111, July). No worker process on 104 or 105 at 17:10. **C2-gate does not clear today** (live nmncap sweeps + the dead 112 share).
- **P0.2 node env.** All 14 nodes (101–114): NAS mounted, `/usr/bin/unzip` present, `numpy 2.3.5`, `import avoidance_stats_heatmap` OK. No node excluded.
- **P0.3 reader re-grep** (`_scratch|rec.gz|load_episode|episodes/*.npz` over `scripts src tests`, then `"recordings"|/recordings/|episode_*|"episodes"`, plus all 9 worktrees under `.claude/worktrees/`). No class-S sweep-cell reader beyond A4's list. Other hits are writers (`eval_rollout.py`, `evaluation_core.py`, `dreamer_srl/eval.py`), class-D/recording-directory tools (render/trajectory/dreamer tools), other pipelines' `_scratch` (`traj_collect`, `launch_collection.py`), `_golden_scratch` CSV gates (`golden_gate.py`, `golden_check.py`), or `"episodes"` as a dict key. **For Phase 3's E2 grep:** worktrees `bb-water`, `thirst`, `thirst-runs` hold *unported* copies of `_traj.py`, `t04_variance_budget.py`, `scene_steps.py`, `obs_manipulation/run.py` (and `bb-water` of `probe_pond.py`); a worktree-wide E2 will block class-S deletion until those worktrees are rebased or listed in `NON_READERS` with a reason.
- **P0.4 the 11:42 silent collation death.** Not determined. `healrep/l05fix_grid` workers wrote `done_112` at 11:42:06. The container's kernel log (docker-102) has **no OOM-kill line** on 2026-10-07; it shows bursts of CIFS `Close interrupted close` / `Close cancelled mid failed rc:-9` at 11:47:46 and 11:52:35–36 (eight at once), consistent with a signal killing a multi-process pool mid-I/O (the collation pool is `min(cpu_count, 32)`), but the same messages recur all afternoon, so this is suggestive, not a cause. Bounded at ~10 min.

### Phase 2 (partial) — this plan's own readers R4–R7

**Scope.** Only R4–R7. Not touched: the neuromodulation session's four files (R9–R12; no go), `sweep_worker.sh`, `run_sweep.py` (`_measure_cell` is R1, Phase 3). Nothing under `results/` was written, packed or deleted: real cells were **copied** into `tmp/20261007_bundle_readers/` and packed there.

**Files.**
- `src/utils/episode_bundle.py`: **new function `step_names(cond_dir)`** — steps present as `<digits>/` folder or `<digits>.zip`, each once, sorted as strings; ignores `*.zip.partial-*`, `_run_markers`, a folder named `N.zip`, a file named `N`. *Deviation (addition to F1):* every reader enumerated steps with an `isdigit()` filter on directory names, which silently skips archives; one shared helper instead of four copies of the same parsing. Test `test_step_names_lists_both_forms_once`.
- `scripts/analysis/basic_behaviour/probe_pond.py` (R4): `episodes_in(cell)` uses `EB.members` (order kept: `episodes/` dirs sorted, then `.npz` sorted within); `measure_episodes` loads through `EB.load_npz` / `EB.load_recording` (failure messages print the same paths for folders); `collate` enumerates steps with `EB.step_names` + `EB.cell_path`, passes the step explicitly. `calibrate` unchanged (its local roll-out folders are read as folders).
- `scripts/analysis/studies/basicq2_waves/_traj.py` (R5): `_episodes` via `step_names` / `cell_path` / `members`; inserts the repo root on `sys.path` (it did not before). One stated narrowing: the old code took `glob(...recordings/*)[0]` (unsorted, OS order) when a cell held several recordings folders; the port takes the first in sorted order. Sweep cells hold one.
- `scripts/analysis/studies/thermal_probes/t04_variance_budget.py` (R6): reading moved into a function `newest_recordings(cond_dir)` with the selection logic verbatim, applied to member paths written as they would be for a folder; repo root from `_common.ROOT`.
- `scripts/analysis/studies/injury_dependence/scene_steps.py` (R7): `step_names` / `cell_path` / `members` / `load_recording`. Episodes are now read in **sorted** order; the old `glob.glob` order was unsorted (OS order) — on the real copy below the result was identical.
- NEW `tests/scripts/test_bundle_readers.py` (4 tests; not listed in F10 — added as the Phase 2 regression test): synthetic condition with steps 99 / 980 / 1000, folder copy vs archive-only copy, each reader's output equal.
- `docs/environment/SCRIPTS_DEPENDENCY_MAP.md`: §1c row for the new test; one row for the four ported readers (new `sys.path` repo-root edge); last-updated line. The file had no uncommitted foreign hunks.

**Verification — real cells, read-only** (`tmp/20261007_bundle_readers/{build,verify}.py`). Newest three steps of eight condition folders copied from `results/eval/avoidance/` (thirst `g10s3_ordinary_s42` ×2, basicq2_wave2 `lvl04_*` ×2, thermalprobe_fire_away_clean `lvl05_control`/`lvl06_modulated`, injurygrid_core `lvl02_control` ×2) into a folder-form tree and an archive-only tree (packed with `EB.pack`, folders removed, asserted only `.zip` remain). Each reader was run three ways: **pre-port code on folders, ported code on folders, ported code on archives.** Pre-stated criterion: all three equal (string-equal CSVs / deep-equal decoded data / array-equal npz).

```
R4 probe_pond collate (BB_DATA_ROOT = tmp tree, spec = g10s3 with the ordinary run only; driver CSVs trimmed to the 3 steps)
  [old_folder] rc=0 wrote 2 pond CSV(s)  [new_folder] rc=0 wrote 2  [new_zip] rc=0 wrote 2
  avoid_none_inj70.csv: old_folder==new_folder True; new_folder==new_zip True; rows 3; equal to real pond CSV rows for these steps True
  avoid_pred_inj00.csv: old_folder==new_folder True; new_folder==new_zip True; rows 3; equal to real pond CSV rows for these steps True
R5 _traj
  control/avoid_pred_inj00: ck 10000012 n_eps 30; episodes old==new_folder True, new_folder==new_zip True; _one equal True
  modulated/avoid_none_inj00: ck 10000055 n_eps 30; episodes old==new_folder True, new_folder==new_zip True; _one equal True
R6 t04 newest_recordings + per-episode bush share
  lvl05_control/avoid_pred_inj00: newest=9800058/.../9800058 n=30; old==new_folder True; new_folder==new_zip True
  lvl06_modulated/avoid_none_inj00: newest=9800012/.../9800012 n=30; old==new_folder True; new_folder==new_zip True
R7 scene_steps.one(core, lvl02_control, last=3)
  [old_folder] 180 episodes  [new_folder] 180  [new_zip] 180
  keys 270; conds with episodes [avoid_none_inj00, avoid_pred_inj30]; old==new_folder True; new_folder==new_zip True
```

**Synthetic, temp dir.** `pytest tests/scripts/test_bundle_readers.py tests/scripts/test_episode_bundle.py -q` → `43 passed`. The same four reader tests pointed at the **pre-port** copies fail 4/4 (the old code finds no episodes in an archive-only condition — the silent skip this phase removes).

**Existing tests.** `tests/analysis/test_basic_behaviour.py`: 25 passed, 5 failed — all 5 in the test's `load(world)` helper (`glob(..."_manifest.json")[0]` → `IndexError`, a missing data manifest), before any `probe_pond` code; the probe_pond tests (`test_prepond_truncation`, `test_calibration_rule_branches`, `test_collate_tolerance_matches_4_decimal_csv`) pass. Not caused by this change; not investigated further.

**Found, not fixed (pre-existing, outside scope).** `t04_variance_budget.py` picks the "newest" checkpoint as the largest *path string*, so `9800058` beats `10000012`: Figure 4 of the thermal-probes page is drawn from the second-newest checkpoint whenever the step count crosses a digit boundary. The port keeps this behaviour exactly (the test pins it). Owner: whoever maintains the thermal-probes page; `bug-curator` if it should be logged.

**Speed check.** Skipped: no change on the training or sweep hot path (analysis readers only). Reading from an archive is not slower in practice here (one ZIP open per member; 30 episodes per cell).

**Still blocked.** R9–R12 (neuromodulation session's go, F9). Phase 3 (C2-gate: live nmncap sweeps on 106/107 and the dead `healrep_noheal/grid` node-112 share at 17:10). `SWITCHED_READERS["S"]` is Phase 3 code; R4–R7 qualify for it.

## Verification Report

> **Verified by**:
> **Date**:

| File | Change | Status | Notes |
|------|--------|:------:|-------|
| | | | |

**Conclusion**:

## Feedback from plan-reviewer

> **Reviewed by**: plan-reviewer · 2026-10-07 · full report: [[plan_sweep_bundles]] (`docs/reviews/plan_sweep_bundles.md`)

**Verdict: NOT READY** — two ordering problems, each fixed by one added precondition; the design is otherwise careful.

- 🔴 **C1 — the hold does not cover new sweeps.** `HOLD_ROOTS` blocks only `delete`. Once the new worker is live, every new test written into a held root is archive-only, so `case_l05_s42/case.py:147` silently falls back to the CSV-mean check and `test_modulator_engagement.py:166` silently skips — the hazard §A4 names. Fix: land `episode_bundle.py` alone, then the other session's F9 ports, *then* switch the worker (or dual-write legacy folders for held roots).
- 🔴 **C2 — editing `sweep_worker.sh` while the three no-healing sweeps run.** Bash reads the script's tail (the `done_` marker line) from disk after the episodes finish; an in-place edit most likely leaves those sweeps hanging silently. Fix: no edit until every live sweep's `done_` markers exist and drivers have exited; ideally launch a per-launch copy of the worker stored with the provenance.
- 🟡 Moderate (details in the report): verification reads the same host's CIFS page cache (verify/delete from a different host; independent `unzip` + `diff -r` on the pilot); G1 can pass vacuously if it seeds from the existing CSV; score-before-pack plus the EXIT-trap cleanup loses episodes on a scoring error; the heartbeat loop outlives a killed worker and a killed `xargs` still writes `done_`; a node-side collation death is still unclassifiable (`RUNNING?` on another host) — add a collation heartbeat and unbuffered logs; partial collation + the max-step incremental rule can leave permanent holes; old-code collation has no marker and can race the migration; node Python env drift (known bug) and cross-node determinism threaten G2's "exact"; "free node" must mean no training and no other sweep, not GPU-free; `HOLD_ROOTS` should be an allow-list.
- **D1** on-node after eval — agree (pack before scoring). **D2** keep `_scratch/` — agree. **D3** inventory only — agree. **D4** no full copy needed if the pilot passes an independent cross-host check; do back up all per-scene CSVs/figures/provenance (MBs) once, and flag roots whose checkpoints are gone. **D5** the neuromodulation session ports R9–R12, before the worker switch; lift the hold per root only after a ported parity run reports `exact` on an archive-only cell.

### Response from senior-developer (revision 1, 2026-10-07)

| Finding | Where answered |
|---|---|
| C1 | Phase order: 1 (`episode_bundle.py` alone) → 2 (reader switch, verified `exact` on an archive-only cell) → Phase 3 worker switch. Ports by our developer per user D5, after F9 coordination. |
| C2 | Gate C2-gate (no edit to `sweep_worker.sh`/`run_sweep.py` while any sweep is live; development in a worktree); F4.6 launch-time worker copy in `_provenance/<id>/worker/`. |
| M1 | F1 `posix_fadvise` before re-read; `delete_verified` refuses on the packing host; M1 step 3 independent `unzip` + `diff -r` on another host. |
| M2 | `aggregate_from_bundles(seed_from_csv=False)`; G1 criterion: 30 recordings per archive, key sets equal; `test_gate_fails_on_empty_archives`. |
| M3 | Pack first, score the archive (F3); EXIT trap no longer deletes staging (F5). |
| M4 | Heartbeat exits with the worker and carries a lines-done counter; progress-stall rule; checkpoint rewritten (killed `xargs` → caught by coverage check). |
| M5 | Collation heartbeat + host-independent DEAD; `PYTHONUNBUFFERED`; eval/finisher logs; "never collated" status; P0.4 bounded root-cause attempt. |
| M6 | Incomplete groups never merged; `test_incomplete_group_not_merged_and_retested`. |
| M7 | E1 process scan + "possibly collating" rule; `cell_path` raises on a directory newer than its archive; `_format` marker. |
| M8 | P0.2 node env preflight; `numpy_version` column; bug-curator hand-off. |
| M9 | G2 includes node 105; off-node mismatch pre-declared as a determinism finding. |
| M10 | Usable-node definition in F4.11 and README. |
| M11 | User declined an allow-list (D3); replaced by fail-closed E2 (any unregistered reader blocks deletion for its class) plus E1/E3, and E4 — the explicit hold requested by the neuromodulation session (its runs and the `modeng_e4` / `case_l05_s42` roots), lifted only on its word. |
| Neuromodulation session request (2026-10-07) | E4 hold on its folders (no pack, no delete); C2-gate covers its sweeps (markers, diary, board, its confirmation); Phase 2 waits for its explicit go; G1 reads the held pilot root only (archives in a gate folder); deletion pilot moved to a non-held root chosen from M0. |
| L1 | WAL resume in `delete_verified`; lock carries host/pid/time, stale rule, `unlock` command. |
| L2 | R11 row corrected. |
| L3 | Map diffed before staging; `probes.py` edge; F2 + F4 + F6 in one commit. |

## Feedback from plan-reviewer — re-review of revision 1

> **Reviewed by**: plan-reviewer · 2026-10-07 · plan at commit `a6c33759` · earlier review: [[plan_sweep_bundles]]

**Verdict: SOUND WITH CONCERNS.** Both blocking findings of the first review are fixed, not just mentioned: the tools that check results exactly against raw episodes are switched to read archives, and shown to report `exact` on an archive-only cell, before the test machines start writing archives (Phase 2 before Phase 3; C1). The worker script cannot be edited while any sweep is live, and every later launch runs its own copy (C2-gate, F4.6; C2). All eleven Moderate and three Low findings are answered with concrete mechanisms. M11 was closed by a user decision (no approval list) and replaced by checks that block deletion when in doubt (E2, E4); I accept that. The revision does add five new Moderate problems. None loses data or weakens an exactness check, but two would cost a failed first launch or a gate that never clears, and one would break links in existing docs.

**Severity legend:** 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run · 🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

| # | Sev | Location | Issue | Suggested fix | Owner |
|---|---|---|---|---|---|
| N1 | 🟡 | §F4.6, §F5; `scripts/eval/dwell_sweep/sweep_worker.sh:23–25` | The copy of the worker made at each launch cannot find the repo. The worker sets `R` to its own folder three levels up (`SCRIPT_DIR/../../..`) and then runs `scripts/eval/eval_rollout.py` relative to `R`. From `<output_dir>/_provenance/<id>/worker/`, `R` lands inside `results/`, so every line fails. `finish_cells.py` has the same depth problem in `sys.path` (the repo-root depth hazard listed in SCRIPTS_DEPENDENCY_MAP). F4.6 says only that "sys.path still points at the repo" and gives no mechanism. The coverage check would catch the failure loudly, so this costs a failed G2 launch, not a wrong table. | The driver passes the repo root to the worker explicitly, as a mandatory argument with no default, and the worker passes it on to `finish_cells.py`. Add a unit test that runs the **copied** worker in `--dry-run` / with a stub and checks that it resolves the repo. | developer |
| N2 | 🟡 | §F7 (D3 class D), §F1 `delete_verified` path guard | Class-D cells contain more than episodes. `results/eval/*/models/<ck>/videos/eval_*.mp4` are rendered videos, and four docs link them by path (`sameprop_chasing_rabbit.md`, `sameprop_round25_design.md`, `RENDERER_LAYOUT_REDESIGN.md`, `EVAL_ROLLOUT_BATCHING_PERF.md`). `models/<ck>/motifs/` holds `motif_cluster.py` outputs, and `conflict_probe_preview/random_init/README.txt` is a README. "Pack whatever is under the cell" plus a guard that protects only `.csv/.png/.html` would move all of these into zips and delete the originals. Nothing is lost, but the doc links break, and E2 cannot catch it because it greps code, not docs. A further class-D reader, `scripts/eval/make_render_fixture_recordings.py:416` (a hard-coded `noPredator_chasingRabbit/.../recordings/9520028`), is missing from R13/R14. Several of the 19 folders are not `<name>/models/<ck>/` (`conflict_probe_preview/<init>/<scene>/…`; `20260728-…_hier_heads/97001` has no `models/` level). The guard refuses those, so "migrate all" quietly becomes "migrate some". | Delete only episode-type members (`episodes/*.npz`, `recordings/**`, `windows/*.parquet`, `online_replay.json`, `metadata.json`) and leave every other file in place. Better still, pack only those members as well. Add `.mp4/.gif/.npy/.txt` and `motifs/`, `videos/` to the never-delete list. Add the fixture script to R13. The M0 inventory should list folders the guard refuses as "not migrated", with the reason. | senior-developer (scope), developer |
| N3 | 🟡 | §Phase order: Phase 3 before G1/G2/G3/speed check | The new pipeline goes into the shared folder **before** any check that it reproduces today's tables, and before the ≤5 % speed budget. No rollback is stated. Any session that launches a sweep in that window uses an unvalidated pipeline. | Run G1–G3 and the speed check from the development worktree first. The per-launch worker copy makes that a plain `--nodes` launch from the worktree, once N1 lets it find its repo. Merge into the shared folder only after they pass. Also state the rollback: reverting Phase 3 is safe at any time, because live launches run their own copies and the Phase-2 readers accept both formats. | senior-developer |
| N4 | 🟡 | §C2-gate (a), §F7 E1 | Neither the gate nor E1 has a way out for a **dead** old-code sweep, and one exists now. The no-healing `grid` sweep has `npar_112` from 16:03 and no `done_112`. At 16:55 there was no `sweep_worker` process on node 112, and its driver (PID 3368218, `noheal_l05_grid_rppo.yaml`) is still polling. That is the silent hang this plan fixes. As written, C2-gate (a) never clears ("no driver process on the container") and E1 counts the root as live forever. Stale markers have the same effect elsewhere (`dp1/dreamer_bins6`: 7 `npar_`, 6 `done_`). | Add one rule. If a node has `npar_`/`started_` but no `done_`, no worker process on that node, and nothing newer than N min, a human declares the sweep dead and records the evidence. Then kill the driver and re-test those steps later with the new pipeline. E1 reports such roots as "dead, unresolved" rather than "live". **Operational, now:** the `grid` sweep's node-112 share needs recovering whatever happens to the plan. | developer; parent (operational) |
| N5 | 🟡 | §F7 E1, §M1–M2 "host A / host B" | E1 needs `ps` on the container plus `ssh` to every node. That works only when `delete` runs on the container. The plan never says which host is A and which is B. | Fix the roles: **pack on a node** (via `run_command.py`, after checking that node's NAS mount) and **verify, gate and delete on the container**. E1 refuses to run anywhere else. | developer |
| N6 | 🟢 | §F7 E4, §Checkpoints | (a) The checkpoint "no archive written into a held cell" contradicts Phase 3. After the switch, the case study's own a3 sweeps write archives into `metrics_history_rppo_case_l05_s42` (a held root). Reword it to "`bundle_scratch.py` writes nothing into a held cell". (b) The hold rule `*healrep_l05_*` "(seeds s42, s43)" is a pattern with a comment attached. List the exact run names instead. | Reword; enumerate the runs. | senior-developer |
| N7 | 🟢 | §F7 E2 | The E2 re-grep patterns (`rec.gz`, `load_episode`, `_scratch`) also match **writers and plumbing**: `eval_rollout.py`, `src/utils/eval_recording.py`, `episode_bundle.py` itself, the README. Without a separate, reviewed "known non-reader" list, either every class stays blocked, or someone adds a writer to `SWITCHED_READERS` to unblock it, which defeats the check. | Add a `NON_READERS` constant with a one-line reason per entry, kept separate from `SWITCHED_READERS`. | developer |

**Status of the first review's findings:** C1 resolved (Phase 2 → Phase 3, with a pre-stated positive `exact` criterion). C2 resolved (C2-gate covers every session's sweeps, plus the per-launch copy; see N1 for the copy's repo resolution). M1 resolved for migration. On the live path, staging is still deleted after a re-read on the same host; after `posix_fadvise` that is an acceptable risk, because the episodes can be regenerated, but say so in one line. M2–M10 resolved. M11 closed by user decision. L1–L3 resolved.

**Assumptions:**

| Assumption | Status |
|---|---|
| Phase-2 readers report `exact` on an archive-only cell | ❓ pre-stated criterion; not yet run |
| The copied worker can locate the repo | ✗ false as the worker stands today (N1) |
| Class-D cells hold only episode files | ✗ false: videos, motif outputs, README (N2) |
| Every live sweep eventually writes `done_` for all its nodes | ✗ false now: node 112, no-healing `grid` (N4) |
| The neuromodulation session's holds are the only ones needed | ❓ a third study (modulator capacity grid, 4 sweeps launched 16:51 today) was not asked. Its readers are in the repo, so E2 covers them |
| `posix_fadvise(DONTNEED)` drops the CIFS page cache for the re-read | ❓ plausible (generic page-cache path); not tested |

**Live state at review time (16:55):** the three no-healing sweeps are not all finished (`grid`/112 is dead, see N4). Four modulator-capacity sweeps (`configs/eval_sweeps/nmncap/*`, drivers started 16:51, workers on 106/107) are also live and are covered by C2-gate (a). The case-study job on 108 is `case.py a12` (four processes), not a sweep.

**Cost of being wrong:** N1 and N3 together cost one failed validation launch, and possibly a window in which other sessions sweep with an unchecked pipeline: hours, and recoverable. N2 costs broken video links in four docs plus a half-migrated class D. That is recoverable by extracting, but nothing would flag it. N4 means the one-time gate never clears without someone stepping in. No remaining finding risks an unrecoverable loss or a silently weakened exactness check.

**Addendum (same review, 16:57).** The user deleted the 19 one-off test folders outside `results/eval/avoidance/` (the list is in `tmp/20261007_eval_oneoff_delete_list.txt`). So the class-D migration (M3) and Phase 2b are dropped, and **N2 becomes moot for migration**. What is left of it:
- (a) **Remove class D from the plan's code paths**, not only from its phases. `bundle_scratch.py --all` should walk only class-S `_scratch` roots. `eval_rollout.py` still defaults its output to `results/eval/`, so new stand-alone test folders will keep appearing there, and `--all` must not start packing them.
- (b) **R13 still matters a little.** After migration, the sweep archives are the main remaining source of raw recordings. `trajectory_story.py` (behind the `trajectory-story` skill) and the render tools take a recordings directory, and none of them can open a `.zip`. Nothing in the repo or docs shows them being pointed at sweep cells today, so this is 🟢 Low. Either keep the thin `.zip` → `EB.extract` wrapper for `trajectory_story.py` alone, or change the F11 skill line from "tools accept a `.zip`" to "run `bundle_scratch.py extract` first". As written, F11 promises a `.zip` argument that Phase 2b would have delivered.
- (c) **Outside this plan (for the parent):** the deletion leaves dead links in four docs (the `videos/eval_*.mp4` references listed under N2). It also breaks `scripts/eval/make_render_fixture_recordings.py:416` (fixture cell M7 points at the deleted `noPredator_chasingRabbit/models/9520028/recordings/9520028`). Owner: `developer` for the script, and `bug-curator` if it should be logged.

N1, N3, N4, N5, N6, N7 stand. The verdict is unchanged: **SOUND WITH CONCERNS**.
