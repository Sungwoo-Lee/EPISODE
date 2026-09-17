---
title: "The dashboard renderer becomes the default for evaluation videos"
topic: refactors
status: active
created: 2026-09-17
last_updated: 2026-09-17
---

# The dashboard renderer becomes the default for evaluation videos

> **Status**: PLANNED — not implemented, not reviewed
> **Opened**: 2026-09-17
> **Related**: [[RENDERER_LAYOUT_REDESIGN]] (the plan that built the new renderer; this plan performs the first item of its retirement gate) · [[ASYNC_CHECKPOINT_VIDEO_RENDER]] (the non-blocking dispatch this plan repoints) · [[SAVED_RUN_CONFIG_COMPAT]] (why archived recordings cannot be re-opened) · [SCRIPTS_DEPENDENCY_MAP.md](../../../environment/SCRIPTS_DEPENDENCY_MAP.md) (maintenance contract triggered by this change) · [12_renderer.md](../../../environment/12_renderer.md) (renderer reference doc) · [[KNOWN_BUGS]]

---

## Context

When a training run reaches a checkpoint it records a few evaluation episodes and then turns them into a video you can watch. That video is drawn by the **old renderer** — a single script, `scripts/eval/render_recordings.py`, that three places in the codebase start as a child process. Over the last four days a **new renderer** was built beside it: a redesigned dashboard with panels that cannot overlap, its own entry point (`scripts/eval/render_recordings_v2.py`), and its own output folder. Nothing calls the new one automatically; you get it only by running that script by hand.

**This plan makes the new renderer the one training and evaluation use.** It changes three lines that name a script, adjusts the arguments passed to it, moves the folder the finished video is looked for in, and retires the freeze guard that has been protecting the old renderer from accidental edits while the new one was built. The old renderer is **not deleted** and stays runnable by hand — that is the user's explicit instruction, as is the choice to repoint the three call sites directly rather than add a switch that lets you pick a renderer from a config file.

Two things had to be worked out before this could be written, and both are decided below. First, the new renderer writes to a different folder (`videos_v2/`) than the old one (`videos/`), while the code that uploads the finished video to the experiment dashboard looks in the old folder — repoint naively and every run would upload a file that was never written. Second, the new renderer deliberately **exits with a failure code** when any single episode cannot be drawn; we had to establish what a failing render child does to a training run that is still going (answer: nothing — it prints a warning and training continues, verified at all four call sites).

**What is not in this plan:** no config key is added, renamed or given a default; no experiment is re-run; the old renderer's code is untouched; and none of the other retirement-gate work in [[RENDERER_LAYOUT_REDESIGN]] (porting the demo and benchmark scripts, deleting the old layout code, renaming sensor labels) is done here.

---

## Analysis

### A1 — The evidence base: what has actually been proved

**Proved, end to end.** The new renderer rendered fixture cell **M4r** through its own entry point with `--concat`, which is exactly how the evaluation path invokes a renderer: episode 1 = 24 steps → 24 frames verified, episode 2 = 75 steps → 75 frames verified, consolidated `eval_M4r.mp4` = 99 frames against 99 expected, **true exit code 0**. M4r carries `thermal_enabled=True`, `olfactory_grid_range=1`, `visual_sensor_range=2` — i.e. body temperature on, smell and vision both extended-range.

**The honest limit of that proof.** The fixtures come from `scripts/eval/make_render_fixture_recordings.py`, which steps the real environment and writes through the **production recording writer** (`src/utils/eval_recording.py::EpisodeRecorder` / `write_run_meta`), so the files are structurally identical to real evaluation output — same `run_meta.pkl`, same `episode_*.rec.gz`, same pickled `EnvParams`. What they do **not** contain is a trained policy's behaviour. This is not the same as "we rendered a real training run", and no real training run is available to render (see A2). The gap is behavioural, not structural: a fixture exercises every panel and every code path, but not the particular trajectories a trained agent produces.

**Not proved, and it matters (see A6):** no recording produced by the Dreamer trainer has been rendered by the new renderer. Dreamer recordings always store "no noise-free observation", a shape the fixtures do not have.

### A2 — Every real recording on disk is unrenderable, by *both* renderers

The body-temperature switch `thermal_enabled` landed on **2026-09-09** (commit `dd3b5dfa`). The newest real recordings on this machine are from **2026-08-05**. A recording saved before that date carries a pickled `EnvParams` with no `thermal_enabled` field, and the observation breakdown in the frozen `src/environment/sensor.py:577` reads that field unconditionally, so rendering one raises `AttributeError`.

This is not a new-renderer problem. Measured during the redesign (Revision 24 of [[RENDERER_LAYOUT_REDESIGN]]): **the old renderer cannot read those recordings either**, failing at the same line through the same call. The difference is in the *shape* of the failure:

| | old renderer | new renderer |
|---|---|---|
| one unreadable episode | the exception escapes the worker pool, the whole batch dies, **no MP4 at all** | that episode is reported with its full traceback, **the other episodes still render**, the consolidated video is still written |
| exit code | non-zero (uncaught traceback) | non-zero, deliberately (`return 1 if failures else 0`) |

**A correction to the premise this plan was commissioned with.** The failure belongs to *pickles written by older code*, not to *old configs*. `write_run_meta` pickles the live `EnvParams` object, which is always constructed by the current code and therefore always has every field the current class declares. A run **resumed from an old checkpoint** builds current `EnvParams` and records them, so its recordings render fine. The unreadable population is fixed and historical: recordings written before 2026-09-09. Nothing on the in-training render path can produce one.

The one-line fix at source (guarding `sensor.py:577`) would clear those recordings for **both** renderers at once. It is explicitly out of scope here (see "Not in scope") and belongs with the archived-run compatibility work in [[SAVED_RUN_CONFIG_COMPAT]].

### A3 — Problem A: the output folder moves, and a consumer hard-codes the old one

The old renderer writes `<run>/videos/<checkpoint>/episode_*.mp4` and `<run>/videos/eval_<checkpoint>.mp4`. The new one writes `<run>/videos_v2/<checkpoint>/episode_*.mp4` and `<run>/videos_v2/eval_<checkpoint>.mp4`, and its module docstring states the separation is the point: `videos/` belongs to the old pipeline and this script "never reads, writes or deletes anything there".

Three places build the consolidated path themselves and hand it to the experiment-dashboard upload:

| Site | Line | Expression |
|---|---|---|
| `src/utils/async_render.py` | 120–122 | `videos_dir = os.path.join(results_dir, "videos")` → `eval_{checkpoint_pct}.mp4` |
| `src/utils/evaluation_core.py` | 275, 378 | `video_dir = os.path.join(results_dir, "videos")` → `eval_{checkpoint_pct}.mp4` |
| `src/algorithms/dreamer_srl/eval.py` | 547 | `os.path.join(results_dir, 'videos', f'eval_{checkpoint_pct}.mp4')` |

**Decision: the three callers look in `videos_v2/`. The new renderer is not taught to write into `videos/`.**

Reasoning, in order of weight:

1. **Writing into `videos/` would silently overwrite existing videos.** The evaluation argv passes `--skip-existing`, but that flag is only consulted for *per-episode* files — the consolidated `eval_<checkpoint>.mp4` is written unconditionally. A run resumed across this change, or an offline re-render, would therefore replace a video drawn by the old renderer with one drawn by the new renderer, under the same filename, with nothing recording which is which. That is the failure mode the separate folder exists to prevent.
2. **The property is cheap to keep and expensive to re-establish.** Two tests pin it today (`test_v2_leaves_the_v1_pipeline_byte_identical`, `test_skip_existing_looks_only_in_its_own_folder`). Making the new renderer write into `videos/` would require either editing it (deleting the property in code) or passing `--output-dir <run>/videos/<checkpoint>` from the callers (deleting it in practice, and re-opening the derived-path collision that flag was added to avoid — wiki `render_recordings_output_path_collision`). Note the honest nuance: `--output-dir` already means the property is really *"it never writes to `videos/` unless a caller tells it to"*. That is an argument for not telling it to.
3. **A run with both folders is legible; a folder with both renderers' output is not.** After this change, `videos/` means "drawn by the old renderer" and `videos_v2/` means "drawn by the new one", permanently and without a lookup. A run that trained across the switch keeps both, each complete and each attributable. Someone comparing an old run with a new one reads the folder name as the renderer's name. The alternative — one folder holding two dashboards under identical filenames — forces exactly the archaeology this project keeps paying for elsewhere.

The cost, paid in full in "File Changes": every hard-coded `videos` string on the evaluation path moves, including the render child's log file, and three tests that assert on the folder name.

**Path agreement is not assumed, it is checked.** The callers predict `<results_dir>/videos_v2/eval_<checkpoint>.mp4`; the renderer derives `rec_dir.parent.parent / "videos_v2" / f"eval_{rec_dir.name}.mp4"`. With `recordings_dir = <results_dir>/recordings/<checkpoint>` these are the same path — but the agreement is structural coincidence between two files, so **CP2** asserts it against a real render rather than by reading both expressions.

**One question for the user, which is not a reopening of the switch decision:** the folder `videos_v2` is named after the renderer that is about to stop being the alternative. Renaming it is a separate change that would touch history, tooling and every existing run's layout. Recommendation: leave the name alone for now; raise it only if the user wants it raised.

### A4 — Problem B: what a failing render does to a training run

**Nothing. It cannot abort training, and it cannot hang it beyond a bounded wait.** Established by reading all four dispatch sites:

- **Non-blocking path (the default for both trainers).** `src/utils/async_render.py` dispatches with `subprocess.Popen` and the trainer polls once per iteration. On a non-zero exit, `poll_render` (L212–216) prints `[render] Warning: render for checkpoint N failed (rc=…)`, names the preserved recordings and the log file, and returns. Every trainer call site additionally wraps dispatch, poll and drain in `try/except` (`train.py:2477-2483`, `train.py:2650-2657`, `dreamer_srl_main.py:2056-2071`, `:2431-2437`, `:2455-2461`), printing "non-fatal" and continuing.
- **Hanging.** `drain_render` waits at most `RENDER_DRAIN_TIMEOUT_S = 300` s (10 s after Ctrl-C) and then **leaves the child running** rather than blocking shutdown.
- **Blocking path** (`training.async_video_render: false`, and the standalone evaluators `main.py:92` / `evaluation.py:435`): `subprocess.run` with **no timeout**. It checks the return code, prints a warning and returns `None`/no video path. It cannot abort; it does block for as long as the child runs. That is a pre-existing property of this path, identical for both renderers, and this plan does not change it.

**The consequence that *is* new, and it is about observability, not stability.** The new renderer exits 1 when *any* episode failed, even though the good episodes and the consolidated video were written. All three upload sites gate on `rc == 0`. So a partially failed render now yields **a valid video on disk and no video on the experiment dashboard**, where the old renderer would have produced no video at all.

**Decision: accept this, do not add a retry, do not loosen the upload gate.** Uploading a consolidated video that is silently missing an episode is worse than uploading nothing: the dashboard would show a video that looks complete. The failure is already loud in the right place — the render log path is printed in the same warning — and the recordings survive, so the video is recoverable offline. On the in-training path a failure here means a genuine renderer bug (a layout that cannot be packed, a text that cannot be fitted, or a frame-count mismatch), which is exactly the case where a missing dashboard video should prompt a look. **CP3** pins the behaviour so it cannot regress into a crash.

### A5 — Problem C (not previously identified): per-episode videos are never deleted again

Today's evaluation argv passes `--cleanup-per-episode`, which deletes the per-episode MP4s after the consolidated one is written, leaving one file per checkpoint. **The new renderer has no such flag and no code path that deletes a file at all** — a deliberate property, pinned by `tests/scripts/test_render_recordings_v2.py::test_there_is_no_way_to_delete_anything`.

Two consequences:

1. **A naive repoint crashes every render.** `--cleanup-per-episode` is not in the new renderer's argument list, so `argparse` exits 2 with "unrecognized arguments" before a single frame is drawn — the render would fail for every checkpoint of every run, and (per A4) each failure would be a warning nobody reads. The flag must be dropped from all three argv builders. **CP1** catches this by parsing the real argv with the real script.
2. **Disk footprint roughly doubles.** Measured on this machine: the new renderer's M4 cell holds 484 KB of per-episode MP4s beside a 404 KB consolidated file; existing old-renderer `videos/` folders on real runs measure 88–118 MB each (consolidated only, because cleanup ran). At 3 evaluation episodes per checkpoint, expect the video folder of a new run to be about twice what an equivalent old run's was.

**Decision: accept the growth; do not give the new renderer a delete path.** Adding one would spend a safety property (and its test) to save a few hundred megabytes per run. **CP5** records the measured per-checkpoint cost from a real render so the number is on the record rather than estimated; if it exceeds **500 MB for a full training run's `videos_v2/`**, stop and raise it with the user rather than deciding unilaterally.

**A benefit that comes with the same property.** The old renderer has a known defect — `--concat` together with `--skip-existing` omits already-rendered episodes from the consolidated video (diagnosed in `docs/develop/active/issues/diag_fable5_20260704/06_evaluation_path.md`, Finding 7, never fixed, never recorded as a registry row). The new renderer concatenates from every *selected* episode whose MP4 exists, not only from the ones it rendered this pass, so it does not inherit the defect. Retiring the defect by replacement is worth stating: it is one of the few things this switch fixes for free.

### A6 — Problem D (not previously identified): Dreamer recordings have a shape no fixture has

`src/algorithms/dreamer_srl/eval.py:470,488` always appends `None` for the noise-free observation ("true_obs never recorded for dreamer-srl"). The new renderer handles that case — `episode.py:284-285` passes `None` through, and `:351` / `:439` switch the panels to "not recorded" — but **no test and no fixture exercises it**, because every fixture is produced by the environment stepper, which records true observations.

One of the three repointed call sites is the Dreamer one. **CP4** closes the gap without needing a Dreamer run: copy a fixture, rewrite its payload with `true_obs=None`, render it, and assert exit 0 with the frame count intact.

### A7 — Problem E (not previously identified): the consolidated video's frame count changes

The old renderer pads the consolidated video by holding each episode's last frame for 5 extra frames ("legacy behavior", `render_recordings.py` `frame_generator`). The new renderer does not pad, and it *verifies* the consolidated frame count against the sum of episode frame counts. So a consolidated video's length changes from `Σ steps + 5·N` to `Σ steps`. Cosmetic, recorded here so nobody later reads the difference as dropped frames.

### A8 — Retiring the freeze guard: what goes, what stays, and what is lost

`scripts/eval/v1_path_guard.py` records a content hash for ten files and a pixel-level baseline of the first 8 frames the old renderer draws from three fixtures, then assigns each file a state at every phase boundary. Its baseline was recorded 2026-09-14 at commit `73d466d8`.

**Its verdict right now, run read-only while writing this plan (2026-09-17, HEAD `beb05d95`):**

```
== compared 10 file(s): PASS=10, ACCEPTED=0, ATTRIBUTED=0, UNATTRIBUTABLE=0
== fixture + frame states
  FRAMES PASS     M1  8 raw frames identical
  FRAMES PASS     M2  8 raw frames identical
  FRAMES PASS     M4  8 raw frames identical
RESULT: OK      (exit 0)
```

The guard is green: the ten frozen files are byte-identical to their baseline, and the old renderer's pixels have not moved. It is being retired at a clean stopping point, not abandoned in the red.

**What is removed** (four git-tracked paths):

| Path | Why |
|---|---|
| `scripts/eval/v1_path_guard.py` | the guard itself |
| `tests/env/test_v1_path_guard.py` | 722 lines, ~50 cases, all testing the guard's own state machine; no other subject |
| `docs/develop/active/refactors/renderer_layout_redesign/v1_guard/baseline.json` | the hash + frame baseline it reads; unreadable once the reader is gone |
| `docs/develop/active/refactors/renderer_layout_redesign/v1_guard/frozen_files_at_baseline.diff` | a snapshot of other sessions' work-in-progress at baseline time, recoverable from git history |

**What stays** (nothing else in the repository depends on the guard): the three fixture cells under gitignored `results/render_audit/recordings/` are shared with `scripts/eval/render_layout_audit.py` and `tests/scripts/test_render_recordings_v2.py` and are untouched.

**What protection is lost. Stated plainly, because it is not nothing:**

1. **Drift detection on ten files — four of which the *new* default renderer depends on read-only.** It writes every MP4 through `src/environment/renderer.py::save_jax_video`; it builds every frame's sensory values through `src/environment/sensor.py::build_sensory_viz`; it reads every recording through `src/utils/eval_recording.py`; and the icon mapping in `configs/visualization/default.yaml` reaches it through `run_meta.pkl`. After retirement, nothing detects an unattributed edit to any of them. The guard's value therefore did **not** end when the old renderer stopped being the default.
2. **The frame baseline — the only instrument in the repository that detects a change in *rendered output* caused by something outside the source files**: a changed asset, a changed config, an upgraded matplotlib. No test pins renderer pixels over time.
3. **The mixed-commit rule**, which classified any commit touching both a frozen file and a plan-owned path as unattributable whatever its trailer — the mechanism that stopped a plan session from folding an edit to a frozen file into an unrelated commit.

**What replaces it: nothing automatic.** The partial cover that survives is signature-level, not pixel-level — `tests/env/test_dashboard_v1_imports.py` pins the signatures of the sensor and recording helpers the new renderer borrows (so a rename or a changed argument list goes red), and `tests/scripts/test_render_recordings_v2.py` pins the new renderer's frame counts and its hands-off treatment of `videos/`. Neither would notice a one-pixel change in what either renderer draws.

For the record, and once only, because the user has considered and rejected it: **I advised against retirement and recommended narrowing the frozen set to the four shared files instead.** The user chose retirement. This plan implements retirement. The residual risk is item 1 above, and the honest mitigation is that it is now *visible* — a change to `save_jax_video`, `build_sensory_viz` or the recording format breaks the new renderer loudly, at the next render, rather than silently altering a video nobody compares.

**One collision this plan does not resolve.** [[RENDERER_LAYOUT_REDESIGN]] §D5.4 defines the guard and its checkpoints CP0.1a / CP0.1b / **CP-G** ("run the guard at every phase boundary"), and its Phase 4 is still unbuilt. After this change CP-G cannot run. **This plan does not edit that document** — its Revision 28 numbering is settled and another session owns it. The plan owner must be told so the retirement is recorded there in their own numbering. Flagged in "Open questions".

### A9 — Everything else that names the old script or the old folder

Checked by grep over `src/`, `scripts/`, `tests/`, `configs/`, `.claude/`, `docs/environment/`:

| Where | What it says | Disposition |
|---|---|---|
| `scripts/eval/trajectory_story.py:37` | a comment showing `python scripts/render_recordings.py …` in a worked pipeline | **Already stale** (wrong path — the script moved into `scripts/eval/` long ago). Out of scope: it is a comment in a hand-run tool and fixing it is unrelated to this change. Recorded here so the next reader does not re-find it. |
| `.claude/skills/trajectory-story/SKILL.md:60,62` | the "make a short watchable clip" recipe, rendering with the old script and reading from `videos/` | **Updated** — this is the documented route for a human rendering recordings, and it should show the default renderer. |
| `docs/environment/12_renderer.md:9,13,28,35,617` | says the old renderer "is the current production default … called by every production eval" | **Updated (two sentences + one pointer).** CP6 of [[RENDERER_LAYOUT_REDESIGN]] also edits this file (the minimap paragraph, §R23.5); the hunks are disjoint. |
| `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` rows 61, 73, 74, 75, 80, 89, 125, 183, 191, 194, 253 | who calls what | **Updated** — its Maintenance Contract requires it in the same change. |
| `docs/develop/active/refactors/ASYNC_CHECKPOINT_VIDEO_RENDER.md:209,662` | the log and video paths under `videos/` | **Appended note, not rewritten** — a completed design doc's history stays as written. |
| `docs/develop/active/issues/KNOWN_BUGS.md` | a row that says a renderer defect "must not be fixed in place" *because the file is frozen under the guard*; another deferred "to the retirement gate"; a row noting the recording format-version stamp that nothing reads | **Handed to `bug-curator`** — that agent owns the registry; this plan does not edit it. |
| `configs/train/default.yaml:64-67`, `configs/evaluation/default.yaml:8` | comments naming `render_recordings.py` | **Updated** (comments only; no key, value or default changes). |

**No config key is added, removed, renamed or re-defaulted.** Nothing here touches `config_loader.py`, `EnvParams`, or any entry in the critical-settings registry ([CONFIG_CRITICAL_SETTINGS.md](../../../environment/CONFIG_CRITICAL_SETTINGS.md)) — checked: that registry has no visualization or render entries — so no change-log entry is required there.

---

## Implementation Plan

### Design

One idea, applied three times: **the name of the script changes, the folder the caller looks in changes, and one argument is dropped.** No new abstraction, no flag, no config key, no compatibility shim. The old renderer keeps working exactly as it does today for anyone who runs it by hand.

The dropped argument is the only asymmetry between the two renderers' command lines:

| flag | old renderer | new renderer |
|---|---|---|
| `<recordings_dir>` | ✅ | ✅ |
| `--concat` | ✅ | ✅ |
| `--skip-existing` | ✅ | ✅ |
| `--fps N` | ✅ | ✅ |
| `--workers N` | ✅ | ✅ |
| `--cleanup-per-episode` | ✅ | ❌ **must be dropped** (A5) |

Order of work — each step must leave the suite green before the next begins:

1. Repoint `src/utils/async_render.py` (the default in-training path for both trainers).
2. Repoint `src/utils/evaluation_core.py` (the blocking fallback and both standalone evaluators).
3. Repoint `src/algorithms/dreamer_srl/eval.py` (the Dreamer kill-switch path).
4. Update the tests that assert on the script name and the folder name; add the four new tests.
5. Run the freeze guard one last time, record its verbatim output in the Implementation Report, then remove it and its artefacts.
6. Update the dependency map, the renderer reference doc, the skill, the config comments; append the note to the async-render design doc.

### File Changes

#### `src/utils/async_render.py` (lines 20, 56, 114, 120–139)

```python
# BEFORE (L56):
_RENDER_SCRIPT = os.path.join(_PROJECT_ROOT, "scripts", "eval", "render_recordings.py")

# AFTER:
_RENDER_SCRIPT = os.path.join(_PROJECT_ROOT, "scripts", "eval", "render_recordings_v2.py")
```

```python
# BEFORE (L120-141):
    videos_dir = os.path.join(results_dir, "videos")
    os.makedirs(videos_dir, exist_ok=True)
    consolidated_mp4 = os.path.join(videos_dir, f"eval_{checkpoint_pct}.mp4")
    # Exact command the blocking path builds (evaluation_core.py /
    # dreamer_srl/eval.py::_render_and_upload), plus optional --workers.
    cmd = [
        sys.executable, _RENDER_SCRIPT,
        str(recordings_dir),
        "--concat",
        "--skip-existing",
        "--cleanup-per-episode",
        "--fps", str(fps),
    ]

# AFTER:
    # videos_v2/ is where render_recordings_v2.py writes. The caller predicts the
    # consolidated path here; the script derives it from the recordings dir as
    # `rec_dir.parent.parent / "videos_v2" / f"eval_{rec_dir.name}.mp4"`. With
    # recordings_dir = <results_dir>/recordings/<pct> the two agree — pinned by
    # tests/training/test_async_render_dispatch.py (CP2), not assumed here.
    videos_dir = os.path.join(results_dir, "videos_v2")
    os.makedirs(videos_dir, exist_ok=True)
    consolidated_mp4 = os.path.join(videos_dir, f"eval_{checkpoint_pct}.mp4")
    # Exact command the blocking path builds (evaluation_core.py /
    # dreamer_srl/eval.py::_render_and_upload), plus optional --workers.
    # NOTE: no --cleanup-per-episode. render_recordings_v2.py has no such flag
    # and no code path that deletes a file; passing it is an argparse error 2.
    cmd = [
        sys.executable, _RENDER_SCRIPT,
        str(recordings_dir),
        "--concat",
        "--skip-existing",
        "--fps", str(fps),
    ]
```

L139 (`log_path`) needs no edit — it is built from `videos_dir`, which now points at `videos_v2/`, so the render log follows its video.

Docstring / message text naming the offline-recovery command must move to the new script: **L20** (`render_recordings.py <recordings_dir>`), **L114** (the skip-if-busy message), **L134** (the `--workers` note). The L114 message tells the reader to delete partial `episode_*.mp4` files before re-rendering with `--skip-existing`; keep that sentence — it is *more* relevant now, because per-episode files are no longer cleaned up (A5).

#### `src/utils/evaluation_core.py` (lines 275, 375–387, 410)

```python
# BEFORE (L275):
    video_dir = os.path.join(results_dir, "videos")

# AFTER:
    # videos_v2/ — where scripts/eval/render_recordings_v2.py writes. This value
    # is used ONLY to build the consolidated MP4 path below; the two eval helpers
    # it is passed to accept it and never read it (verified: no other use).
    video_dir = os.path.join(results_dir, "videos_v2")
```

```python
# BEFORE (L377, L380-387):
            render_script = os.path.join(project_root, "scripts", "eval", "render_recordings.py")
            ...
            cmd = [
                _sys.executable, render_script,
                recordings_dir,
                "--concat",
                "--skip-existing",
                "--cleanup-per-episode",
                "--fps", str(fps),
            ]

# AFTER:
            render_script = os.path.join(project_root, "scripts", "eval", "render_recordings_v2.py")
            ...
            # No --cleanup-per-episode: render_recordings_v2.py has no such flag.
            cmd = [
                _sys.executable, render_script,
                recordings_dir,
                "--concat",
                "--skip-existing",
                "--fps", str(fps),
            ]
```

L410, the "auto-render disabled" hint, must name the new script:

```python
# BEFORE:
                  f"Auto-render disabled. Render with: python scripts/eval/render_recordings.py {recordings_dir} ---", flush=True)
# AFTER:
                  f"Auto-render disabled. Render with: python scripts/eval/render_recordings_v2.py {recordings_dir} ---", flush=True)
```

#### `src/algorithms/dreamer_srl/eval.py` (lines 530, 545–557, 569)

```python
# BEFORE (L546-557):
    render_script = os.path.join(_project_root, 'scripts', 'eval', 'render_recordings.py')
    consolidated = os.path.join(results_dir, 'videos', f'eval_{checkpoint_pct}.mp4')

    cmd = [
        sys.executable,
        render_script,
        str(recordings_dir),
        '--concat',
        '--skip-existing',
        '--cleanup-per-episode',
        '--fps', str(fps),
    ]

# AFTER:
    render_script = os.path.join(_project_root, 'scripts', 'eval', 'render_recordings_v2.py')
    consolidated = os.path.join(results_dir, 'videos_v2', f'eval_{checkpoint_pct}.mp4')

    # No --cleanup-per-episode: render_recordings_v2.py has no such flag.
    cmd = [
        sys.executable,
        render_script,
        str(recordings_dir),
        '--concat',
        '--skip-existing',
        '--fps', str(fps),
    ]
```

Also update the docstring at **L530** (`videos written to results_dir/videos/` → `videos_v2/`) and the warning text at **L569** (`render_recordings.py failed` → `render_recordings_v2.py failed`).

#### `tests/training/test_async_render_dispatch.py` — two edits, two new cases

```python
# BEFORE (L119):
        assert path.endswith(os.path.join("videos", "eval_100.mp4"))
# AFTER:
        assert path.endswith(os.path.join("videos_v2", "eval_100.mp4"))

# BEFORE (L320):
    assert calls[0][1].endswith(os.path.join("scripts", "eval", "render_recordings.py"))
# AFTER:
    assert calls[0][1].endswith(os.path.join("scripts", "eval", "render_recordings_v2.py"))
```

**New — `test_dispatched_argv_is_accepted_by_the_real_renderer` (CP1).** The existing rig monkeypatches `_RENDER_SCRIPT` to a stub, so a bad flag is invisible to every case in this file. Capture the argv `dispatch_render` builds, then run **the real** `scripts/eval/render_recordings_v2.py` with that argv's tail pointed at an empty temp directory, and assert it fails at `run_meta.pkl not found` — i.e. it got past `argparse` — and specifically that stderr does **not** contain `unrecognized arguments`. *Fails before the fix* (`--cleanup-per-episode` → exit 2, "unrecognized arguments").

**New — `test_caller_predicted_video_path_matches_what_the_renderer_writes` (CP2).** Mark `integration`. Copy the M4 fixture into `tmp_path/<run>/recordings/M4/`, call `dispatch_render` with `results_dir=tmp_path/<run>`, `checkpoint_pct="M4"`, wait for the child, then assert the file at the `pending["mp4_path"]` the dispatcher recorded **exists**. Skip with an explicit reason when the fixture is absent. *Fails before the fix* (the predicted path is under `videos/`; nothing is written there).

#### `tests/algorithms/dreamer_srl/test_eval_video_smoke.py` (line 140) and `test_eval_telemetry.py` (line 50)

`videos` → `videos_v2` in the asserted directory name and in the faked directory, respectively. Both fail before the corresponding source change and pass after.

#### `tests/scripts/test_render_recordings_v2.py` — docstring + one new case

The module docstring says the new script is "a separate script nothing calls automatically" and that the old one "is what training and evaluation call". Both sentences become false; rewrite those two sentences to say that training and evaluation now call this script, that the old one remains hand-runnable, and that these tests therefore now protect the default path. Do not weaken any assertion.

**New — `test_a_recording_with_no_true_observations_renders` (CP4).** Mark `integration`. Copy the M4 fixture's short episode into `tmp_path`, load the payload, set `true_obs=None`, re-write it gzipped, render with `--concat`, and assert exit code 0 and that the MP4 decodes to the recorded step count. This is the shape every Dreamer recording has (A6) and nothing exercises it today.

#### Removals (the guard retirement)

```
git rm scripts/eval/v1_path_guard.py
git rm tests/env/test_v1_path_guard.py
git rm docs/develop/active/refactors/renderer_layout_redesign/v1_guard/baseline.json
git rm docs/develop/active/refactors/renderer_layout_redesign/v1_guard/frozen_files_at_baseline.diff
```

**Precondition, and it is a stop condition:** run `python scripts/eval/v1_path_guard.py check` immediately before the removal and paste its **verbatim** output into the Implementation Report. If any file reports `ATTRIBUTED` or `UNATTRIBUTABLE`, or any frame set differs, **stop and report to the user** — a guard that is catching something is not deleted silently. (Its verdict while this plan was written is in A8; it was clean.)

#### `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` — required by its Maintenance Contract

This change alters callers of a file under `scripts/` and deletes one, so the map must be updated in the same commit:

- **Rows 73, 74, 75** (`evaluation_core.py:365`, `dreamer_srl/eval.py:546`, `async_render.py:56`): re-point the target to `scripts/eval/render_recordings_v2.py`, correct the line numbers to what the edit produces, and record the dropped `--cleanup-per-episode` and the `videos_v2/` output.
- **Row 80** ("Rule: moving `render_recordings.py` requires editing all THREE rows…"): the rule now belongs to `render_recordings_v2.py`; `render_recordings.py` has no `src/` caller left.
- **Row 61** (the guard's bare-name import of `render_recordings`) and **row 89** (the guard's test): **delete** — both subjects are gone.
- **Row 125** (`render_recordings.py`'s consumer list) and **row 183** (its summary row): remove the three `src/` subprocess paths; it becomes a hand-run + skill-referenced script.
- **Row 191** (`v1_path_guard.py`): **delete**.
- **Row 194** (`render_recordings_v2.py`): rewrite — "none in `src/`, and that is deliberate" is now false. It is called by all three `src/` sites; the `--renderer`-flag-free dispatch-by-script-choice statement stays true and should be restated.
- **§2 Cluster B paragraph (line 253)**: the two renderers are no longer "a second, parallel renderer" and a production one; state which is which now.
- **Bottom-line paragraph (line 17)** names `render_recordings.py` as the `src/`-coupled script; correct it.

#### `docs/environment/12_renderer.md` (lines 9, 13, 28, 35)

Two factual sentences and one pointer. L9: the old renderer is no longer "the current production default" — it is the previous renderer, still runnable by hand. L13/L28/L35: the production offline render path is `scripts/eval/render_recordings_v2.py`, which draws through `src/environment/dashboard/`; the "swap the imports in lines 31 and 45" instruction describes a swap that no longer decides anything for the eval path and must say so. Leave the dormant `renderer_v2.py` paragraph and the minimap material alone (CP6 of [[RENDERER_LAYOUT_REDESIGN]] owns them).

#### `.claude/skills/trajectory-story/SKILL.md` (lines 60, 62)

```bash
# BEFORE:
python scripts/eval/render_recordings.py results/eval/<name>/models/<ckpt>/recordings/<pct>/ --workers 8 --fps 5 --concat
VD=results/eval/<name>/models/<ckpt>/videos
# AFTER:
python scripts/eval/render_recordings_v2.py results/eval/<name>/models/<ckpt>/recordings/<pct>/ --workers 8 --fps 5 --concat
VD=results/eval/<name>/models/<ckpt>/videos_v2
```

Add one sentence: the previous renderer remains available as `scripts/eval/render_recordings.py`, writing to `videos/`.

#### `docs/develop/active/refactors/ASYNC_CHECKPOINT_VIDEO_RENDER.md`

Append a dated note at the end (do **not** rewrite lines 209 / 662, which record what was true when that plan shipped):

> **2026-09-17 —** the render child is now `scripts/eval/render_recordings_v2.py` and its outputs, including `render_<ckpt>.log`, live under `<results_dir>/videos_v2/`. The dispatch/poll/drain design is unchanged. See [[EVAL_RENDERER_SWITCHOVER]].

#### `configs/train/default.yaml` (lines 64–67) and `configs/evaluation/default.yaml` (line 8)

Comment text only — the two mentions of `render_recordings.py` become `render_recordings_v2.py`. **No key, value or default changes**, so no `CONFIG_CRITICAL_SETTINGS` change-log entry is due (that registry contains no visualization or render entries).

#### Not edited by this plan

`docs/develop/active/refactors/RENDERER_LAYOUT_REDESIGN.md` (another session owns it; its Revision 28 numbering is settled) and `docs/develop/active/issues/KNOWN_BUGS.md` (owned by `bug-curator`; hand it the three affected rows — the defect deferred because a file was frozen, the housekeeping row deferred "to the retirement gate", and the never-read recording format-version stamp, which this change makes the first real second consumer of that format).

---

## Checkpoints

Each is failure-detectable: it names what goes wrong and how you would see it.

- [ ] **CP1 — the command line is accepted by the script that now receives it.** `test_dispatched_argv_is_accepted_by_the_real_renderer` passes, and stderr contains no `unrecognized arguments`. *Detects:* a left-behind `--cleanup-per-episode`, which would make every render exit 2 before drawing a frame, with only a warning in the training log.
- [ ] **CP2 — the path the caller predicts is the path the renderer writes.** `test_caller_predicted_video_path_matches_what_the_renderer_writes` passes on the M4 fixture. *Detects:* any disagreement between the caller's `<results_dir>/videos_v2/eval_<pct>.mp4` and the script's own derivation — the failure that makes a run render correctly and upload nothing.
- [ ] **CP3 — a failing render still cannot stop training.** With the stub script forced to exit 1: the existing `test_render_failure_no_upload_state_cleared` passes (no upload, state cleared, no exception escapes), and a blocking-path case asserts `evaluate_jax_checkpoint` returns normally with `last_video_path is None`. *Detects:* a repoint that turns a child's non-zero exit into a raised exception on the training thread.
- [ ] **CP4 — a recording with no noise-free observations renders.** `test_a_recording_with_no_true_observations_renders` passes with exit 0 and the frame count intact. *Detects:* the Dreamer recording shape (`true_obs=None`) failing in a panel, which no fixture would reveal.
- [ ] **CP5 — the disk cost is measured, not estimated.** Render one real checkpoint's recordings through the new path and record `du -sb` for the per-episode folder and the consolidated file in the Implementation Report, with the episode count. *Stop condition:* if the extrapolated full-run `videos_v2/` exceeds **500 MB**, stop and raise it with the user instead of proceeding.
- [ ] **CP6 — no `src/` path names the old script.** `grep -rn "render_recordings\.py" src/` returns nothing but comments that deliberately name the previous renderer. *Detects:* a missed fourth call site.
- [ ] **CP7 — the guard's final verdict is recorded before it is deleted.** Verbatim `check` output in the Implementation Report, exit code stated. Any non-`PASS` state or frame difference is a **stop and ask the user**, not a deletion.
- [ ] **CP8 — the full test suite is green**, with the removed guard test gone rather than skipped, and the `integration`-marked cases run at least once (they skip silently without the gitignored fixtures; if they skipped, say so and regenerate with `scripts/eval/make_render_fixture_recordings.py`). *Detects:* the "green because it compared nothing" shape this project has been bitten by twice.
- [ ] **CP9 — training speed is unchanged.** The render is a CPU-only child on the non-blocking path, so training steps/second should not move at all. Record before/after numbers from the same config, seed and node, over a long enough window that warm-up does not dominate. Separately note that on the **blocking** path (`training.async_video_render: false`, and the standalone evaluators) the render itself is expected to be slower per frame — the redesign's accepted speed gate measured the new renderer at 1.78× the old one per frame — and say whether any live configuration uses that path.

---

## Implementation Report

> **Implemented by**: [agent/person]
> **Date**: [date]

<!-- Fill in: what was changed; the verbatim `v1_path_guard.py check` output from CP7 with its exit
     code; the CP5 disk measurement with episode count; the CP9 before/after speed numbers with the
     config, seed, node and window length; any deviation from this plan and why; whether the
     integration-marked tests ran or skipped. -->

## Verification Report

> **Verified by**: [agent/person]
> **Date**: [date]

| File | Change | Status | Notes |
|------|--------|:------:|-------|
| | | | |

**Conclusion**: [one-line summary]

---

## Not in scope

- **Making archived recordings renderable.** The one-line guard at `src/environment/sensor.py:577` that would clear pre-2026-09-09 recordings for *both* renderers is deliberately not done here: it changes the observation-breakdown path used by live training, so it needs its own plan and its own review. See [[SAVED_RUN_CONFIG_COMPAT]].
- **Deleting the old renderer or the dormant `src/environment/renderer_v2.py`.** The user's instruction is explicit ("you don't have to remove v1 yet"), and deletion of the dormant file was separately declined.
- **The rest of the retirement gate** in [[RENDERER_LAYOUT_REDESIGN]] Phase 5: porting the demo / benchmark / snapshot callers, moving shared helpers into the package, deleting the old layout body, the sensor-label rename, and retargeting `test_thermal_rendering.py` / `test_eval_recording.py`.
- **A renderer switch of any kind** — no config key, no flag, no environment variable. Which renderer runs is decided by which script is named in the source, and by nothing else.
- **Renaming the `videos_v2` folder.** See the open question below.
- **`scripts/eval/trajectory_story.py:37`'s stale comment path**, which was already wrong before this change.

## Open questions for the user

1. **The folder name.** `videos_v2/` is named after the renderer that is about to stop being the alternative. Recommendation: leave it — renaming touches every existing run's layout and buys nothing today. Raise only if the name will bother you in six months.
2. **Telling the redesign plan's owner.** After this change, checkpoint **CP-G** of [[RENDERER_LAYOUT_REDESIGN]] ("run the freeze guard at every phase boundary") cannot run, and its §D5.4 frozen-file promise has been partly spent by design. This plan does not edit that document. Who records it there — that session, or a follow-up here?
3. **The registry rows.** Three entries in the Known Bugs registry change meaning with this commit (a defect deferred *because* a file was frozen; a housekeeping item deferred "to the retirement gate"; the recording format-version stamp nothing reads). `bug-curator` owns the registry — confirm it should be handed these after the change lands.
