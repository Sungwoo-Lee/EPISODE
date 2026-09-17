---
title: "The dashboard renderer becomes the default for evaluation videos"
topic: refactors
status: active
created: 2026-09-17
last_updated: 2026-09-17
---

# The dashboard renderer becomes the default for evaluation videos

> **Status**: PLANNED — not implemented. Reviewed by `plan-reviewer` (verdict **SOUND WITH CONCERNS**, no Critical finding) and revised 2026-09-17 against all twelve findings; two premises of the first draft were factually false and are retracted in place (see A2 and A6).
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

**Proved on a real trained policy, end to end.** The new renderer rendered checkpoint `9800039` of the recurrent-PPO run `20260914-125033_rppo_olfgae_t4act_X_s42` — a policy 9.8 M training steps into its run, three evaluation episodes of 9, 159 and 332 steps — through its own entry point with the exact evaluation argv (`--concat --skip-existing --fps 5`, `JAX_PLATFORMS=cpu`). Every episode reported "frames verified", the consolidated `eval_9800039.mp4` verified **500 frames against 500 expected**, and the process returned **exit code 0**. The render ran on a scratch copy, never in the run's own folder.

**The same checkpoint also renders under the old renderer** (exit 0), and its consolidated output came out at 956,266 B against the 956,367 B file the training run itself wrote months earlier — 0.01 % apart. That agreement is what makes every old-vs-new comparison in this plan like-for-like rather than a comparison of two different workloads.

**What the fixtures still carry that the real recording does not.** Two fixture cells remain part of the evidence base because they exercise shapes this run does not have:

| Evidence | What only it covers |
|---|---|
| real checkpoint `9800039` | a trained policy's trajectories; 500 frames; `thermal_enabled` present (value `False`), smell at radius 1, vision at radius 0 |
| fixture **M4r** | the extended-sense world — body temperature **on**, smell radius 1 **and** vision radius 2, the only case where the sensor band holds diamond maps for both senses (99 frames, exit 0) |
| fixture **M6b** | perceptual noise **on** while noise-free observations are **not** recorded (see A6) |

**The honest limit, restated.** The gap that remains is not "no real run has been rendered" — one has. It is narrower: no **Dreamer** recording has been rendered by the new renderer (A6), and no render has been observed on the in-training dispatch path rather than by hand.

### A2 — What is renderable on disk, and what is not

**Correction to the premise this plan was commissioned with, and to this section's own previous claim.** An earlier revision of this plan asserted that the newest real recordings on this machine were from 2026-08-05 and that therefore *every* real recording was unrenderable. **That was false.** Five recurrent-PPO runs carry recordings written after the body-temperature switch landed, each with **50 checkpoints** of 3 episodes:

| Run | Total recorded frames |
|---|---|
| `20260909-161137_rppo_olfgae_t2enc_I_s42` | 10,294 |
| `20260909-161137_rppo_olfgae_t2enc_X_s42` | 12,751 |
| `20260909-161137_rppo_olfgae_t2enc_ALL_s42` | 13,636 |
| `20260914-125033_rppo_olfgae_t4act_X_s42` | 12,560 |
| `20260914-125037_rppo_olfgae_t5crt_ALL_s42` | 11,730 |

Verified directly against a pickle: `20260914-125033.../recordings/9800039/run_meta.pkl` unpickles to an `EnvParams` on which `thermal_enabled` **is present** (its value is `False`), with `olfactory_grid_range=1` and `visual_sensor_range=0`. Presence, not value, is what decides renderability — the observation breakdown reads the attribute, so an object that merely *has* it cannot raise.

**What genuinely is unrenderable.** The body-temperature switch `thermal_enabled` landed on **2026-09-09** (commit `dd3b5dfa`). A recording saved before that date carries a pickled `EnvParams` with no such field, and the observation breakdown in the frozen `src/environment/sensor.py:577` reads it unconditionally, so rendering one raises `AttributeError`. The pre-thermal Dreamer runs of 2026-08-05 are in that class. The unreadable population is **fixed and historical**, not "everything".

This is not a new-renderer problem either way. Measured during the redesign (Revision 24 of [[RENDERER_LAYOUT_REDESIGN]]): **the old renderer cannot read the pre-thermal recordings either**, failing at the same line through the same call. The difference is in the *shape* of the failure:

| | old renderer | new renderer |
|---|---|---|
| one unreadable episode | the exception escapes the worker pool, the whole batch dies, **no MP4 at all** | that episode is reported with its full traceback, **the other episodes still render**, the consolidated video is still written |
| exit code | non-zero (uncaught traceback) | non-zero, deliberately (`return 1 if failures else 0`) |

**Why the failure belongs to pickles, not to configs.** `write_run_meta` pickles the live `EnvParams` object, which is always constructed by the current code and therefore always has every field the current class declares. A run **resumed from an old checkpoint** builds current `EnvParams` and records them, so its recordings render fine. Nothing on the in-training render path can produce an unreadable recording.

The one-line fix at source (guarding `sensor.py:577`) would clear the historical recordings for **both** renderers at once. It is explicitly out of scope here (see "Not in scope") and belongs with the archived-run compatibility work in [[SAVED_RUN_CONFIG_COMPAT]].

> **Do not propagate the retracted claim.** The false statement "every real recording on disk is unrenderable" must not be carried into [[SAVED_RUN_CONFIG_COMPAT]] or into the `bug-curator` hand-off. The accurate statement is: *recordings written before 2026-09-09 lack `thermal_enabled` and fail in both renderers; recordings written after it render in both.*

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
2. **Disk footprint grows about threefold — measured, not estimated.** An earlier revision of this plan said "roughly doubles". That was an estimate from fixture cells and it was too low.

**The measurement.** Both renderers were run over the *same* real checkpoint (`20260914-125033_rppo_olfgae_t4act_X_s42/recordings/9800039`, 3 episodes of 9 / 159 / 332 steps = **500 frames**) on a scratch copy, with the evaluation argv:

| | old renderer, as production runs it (`--cleanup-per-episode`) | new renderer |
|---|---|---|
| per-episode MP4s kept | none — deleted after concat | 1,416,203 B |
| consolidated MP4 | 956,266 B (515 encoded frames) | 1,377,205 B (500 encoded frames) |
| **total left on disk** | **956,266 B** (0.91 MiB) | **2,793,588 B** (2.66 MiB) |
| **bytes per recorded frame** | **1,913** | **5,587** |

**Ratio: 2.92x** on this checkpoint. An independent render of a different checkpoint (734 frames) by the plan reviewer gave 3,691,281 B vs 1,193,522 B = **3.09x**. Two checkpoints of different lengths agree, so **~3x** is the number this plan carries.

**Why it is ~3x and not ~1.5x.** Two effects stack. The never-deleted per-episode files are **50.7 %** of the new total — that is the larger half. On top of that the new consolidated file is itself denser per frame (2,754 B/frame vs the old 1,913 B/frame, ~1.44x), because the redesigned dashboard has more ink in it.

**Extrapolate per frame, never per checkpoint.** Episode lengths vary enormously — across the five renderable runs a checkpoint holds between **25 and 734** frames, with a median near 210 and a mean near 245. Multiplying one checkpoint's size by the checkpoint count is therefore unreliable in both directions: checkpoint `9800039` is a 500-frame checkpoint against its own run's 251-frame mean, so per-checkpoint extrapolation from it overstates the run by almost exactly 2x. The per-frame rate is stable and is what should be used.

**Cross-check that the per-frame rate is sound.** The run's 50 existing consolidated MP4s total 23,430,661 B over 12,560 recorded frames = **1,865 B/frame**, against the 1,913 B/frame measured on the scratch re-render — 2.5 % apart. The old rate is also stable across differently-shaped runs: 1,522 B/frame (`20260804-040711_rppo_bushrefuge_b02_n102`) and 1,857 B/frame (`20260509-183913_rppo_nmn_meta_spec_active_swapped_s0`), both sampled over 8 checkpoints.

**What that means for the five runs of this shape** (50 checkpoints, ~250 frames/checkpoint), at 5,587 B/frame:

| Run | `videos/` today | `videos_v2/` projected |
|---|---|---|
| `…t2enc_I_s42` (10,294 frames) | 18.4 MiB | **54.9 MiB** |
| `…t2enc_X_s42` (12,751 frames) | 22.7 MiB | **68.0 MiB** |
| `…t2enc_ALL_s42` (13,636 frames) | 24.5 MiB | **72.7 MiB** |
| `…t4act_X_s42` (12,560 frames) | 22.3 MiB | **66.9 MiB** |
| `…t5crt_ALL_s42` (11,730 frames) | 21.0 MiB | **62.5 MiB** |

**Decision: accept the growth; do not give the new renderer a delete path.** Adding one would spend a safety property (and its test) to save tens of megabytes on the run shape actually in use.

**The 500 MB stop condition is withdrawn, because it does not measure this change.** A flat per-run ceiling is a statement about *run shape*, not about the renderer swap: the largest `videos/` folder on this machine today is **2,251 MiB** (`20260509-183913_rppo_nmn_meta_spec_active_swapped_s0`, 1,000 checkpoints) — already 4.5x past 500 MB with the **old** renderer. A gate that a run fails before the change is made cannot tell anyone whether the change is affordable. It is replaced by two conditions in **CP5**:

- **Rate condition (this is the one that tests the change).** The measured new-renderer total must be **≤ 8 KB per recorded frame**. Two real checkpoints measured 5.0 and 5.6 KB/frame; a result materially above 8 KB/frame means something other than the known 3x is happening — stop and raise it.
- **Budget note (this one is informational, and run-shape dependent).** Multiply the rate by the run's total recorded frames. For a 50-checkpoint run of the current shape that is ~67 MiB and needs no discussion. For a 1,000-checkpoint long-episode run of the `bushrefuge` shape (~1.45 M frames) it projects to roughly **6 GB**, against ~2.1 GB today. If a run is projected past **1 GB**, raise the retention question with the user before launching it rather than after.

**The mitigation to name if that conversation happens:** the per-episode files are the deletable half. Keeping only the consolidated output would put the new renderer at 2,754 B/frame — 1.44x the old, not 3x — without touching the renderer's no-delete property, because the deletion would be a separate retention step rather than a flag on the renderer.

**A benefit that comes with the same property.** The old renderer has a known defect — `--concat` together with `--skip-existing` omits already-rendered episodes from the consolidated video (diagnosed in `docs/develop/active/issues/diag_fable5_20260704/06_evaluation_path.md`, Finding 7, never fixed, never recorded as a registry row). The new renderer concatenates from every *selected* episode whose MP4 exists, not only from the ones it rendered this pass, so it does not inherit the defect. Retiring the defect by replacement is worth stating: it is one of the few things this switch fixes for free.

### A6 — "No noise-free observation" is the *default* recording shape, not a Dreamer quirk

An earlier revision of this plan called `true_obs=None` a shape "no fixture has" and unique to Dreamer. **Both halves were wrong**, and the correction makes this the cheapest checkpoint in the plan rather than the most speculative.

**Dreamer always records it.** `src/algorithms/dreamer_srl/eval.py:470,488` appends `None` for every step ("true_obs never recorded for dreamer-srl (no noise API)").

**Recurrent PPO records it too, whenever perceptual noise is off.** `src/utils/evaluation_core.py:305-307` computes `record_true_obs` as `testing.record_true_observations AND (record_stats OR (render_video AND params.perceptual_noise_enabled))`, and `:460` sets `ep_true_obs = [] if record_true_obs else None`. So on a video-only evaluation of a noiseless world, the recording stores `None`. **Verified on disk:** the episodes of `20260914-125033_rppo_olfgae_t4act_X_s42` unpickle with `true_obs` of type `NoneType` (that run has `perceptual_noise_enabled=False`). This is the ordinary shape for both trainers; the fully-populated `true_obs` of fixture M4r is the *unusual* one.

**A fixture already covers it.** Cell **M6b** exists on disk at `results/render_audit/recordings/M6b/M6b/` — 2 episodes of 24 and 75 steps, `thermal_enabled=True`, **`perceptual_noise_enabled=True`**, and `true_obs=None` on both episodes. It is built for exactly this by `scripts/eval/make_render_fixture_recordings.py:262-273` (`no_true_obs=True`), and it is the more demanding case than a real recording, because noise is *on* while the noise-free comparison is *absent* — the combination that drives the "not recorded" caption.

**And it is already proved.** The real-checkpoint render in A1 — 500 frames, exit 0 — *was* a `true_obs=None` recording. The new renderer handles the case (`episode.py:284-285` passes `None` through; `:351` / `:439` switch the panels to "not recorded"), and that is now an observation rather than a hope.

**Consequence for the plan: do not doctor a fixture.** The previous CP4 ("copy a fixture, rewrite its payload with `true_obs=None`") is withdrawn — hand-editing a recording risks testing an artefact of the edit. **CP4** instead renders M6b, which is genuine production-writer output. The residual uncovered gap is narrower and is stated honestly in A1: no *Dreamer-written* recording has been rendered by the new renderer, though the shape its writer produces has been.

### A7 — Problem E (not previously identified): the consolidated video's frame count changes

The old renderer pads the consolidated video by holding each episode's last frame for 5 extra frames ("legacy behavior", `render_recordings.py` `frame_generator`). The new renderer does not pad, and it *verifies* the consolidated frame count against the sum of episode frame counts. So a consolidated video's length changes from `Σ steps + 5·N` to `Σ steps`. Cosmetic, recorded here so nobody later reads the difference as dropped frames.

**Confirmed by counting frames, not by reading code.** On the real checkpoint of A1 (3 episodes, 9 + 159 + 332 = 500 steps), `ffprobe` counts **515** frames in the old renderer's consolidated MP4 (= 500 + 5 × 3) and **500** in the new one. The run's own archived `eval_9800039.mp4`, written months ago by the training loop, also counts 515.

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

**4. The asymmetry nobody has stated yet: the incoming default is the one under active development.** The three risks above are about the four *shared* files. The larger exposure is the new renderer itself.

`scripts/eval/render_recordings_v2.py` and `src/environment/dashboard/` have taken **ten commits in two days** (2026-09-16 and 2026-09-17, `d83c8b22` through `1a8fc4ed`, including one hotfix — `1a8fc4ed`, "commit the package entry point the last commit left behind"). Phase 4 of [[RENDERER_LAYOUT_REDESIGN]] is still unbuilt, and **another session owns that work**. The old renderer was frozen against precisely this hazard; the new one is not frozen and is about to become production.

The mechanism that makes this sharp rather than theoretical: `src/utils/async_render.py` dispatches the render as a **subprocess that reads the script from the NAS at the moment the checkpoint fires**. The script is not imported once at trainer start and held — only the *path* is bound at import (L56); the file's contents are read fresh per dispatch. So a half-saved edit, or a commit that lands a module without its entry point, means a render that fails for whatever checkpoints fire during that window — and per A4 the failure is a printed warning nobody is watching for.

**Decision: do not gate this plan on Phase 4, and do not add machinery for it. Name the hand-off instead.** The redesign session owns the mitigation, which is cheap and local to them: **gate every commit that touches `scripts/eval/render_recordings_v2.py` or `src/environment/dashboard/` on `tests/scripts/test_render_recordings_v2.py` passing**, because after this change those files sit on the training path. Recorded as an open question with a named owner rather than as a checkpoint here, since this plan cannot enforce another session's commit discipline.

For the record, and once only, because the user has considered and rejected it: **I advised against retirement and recommended narrowing the frozen set to the four shared files instead.** The user chose retirement. This plan implements retirement. The residual risk is item 1 above, and the honest mitigation is that it is now *visible* — a change to `save_jax_video`, `build_sensory_viz` or the recording format breaks the new renderer loudly, at the next render, rather than silently altering a video nobody compares.

**One collision this plan does not resolve.** [[RENDERER_LAYOUT_REDESIGN]] §D5.4 defines the guard and its checkpoints CP0.1a / CP0.1b / **CP-G** ("run the guard at every phase boundary"), and its Phase 4 is still unbuilt. After this change CP-G cannot run. **This plan does not edit that document** — its Revision 28 numbering is settled and another session owns it. The plan owner must be told so the retirement is recorded there in their own numbering. Flagged in "Open questions".

### A9 — Everything else that names the old script or the old folder

Checked by grep over `src/`, `scripts/`, `tests/`, `configs/`, `.claude/`, `docs/environment/`:

| Where | What it says | Disposition |
|---|---|---|
| `scripts/eval/trajectory_story.py:37` | a comment showing `python scripts/render_recordings.py …` in a worked pipeline | **Already stale** (wrong path — the script moved into `scripts/eval/` long ago). Out of scope: it is a comment in a hand-run tool and fixing it is unrelated to this change. Recorded here so the next reader does not re-find it. |
| `.claude/skills/trajectory-story/SKILL.md:60,62` | the "make a short watchable clip" recipe, rendering with the old script and reading from `videos/` | **Updated** — this is the documented route for a human rendering recordings, and it should show the default renderer. |
| `docs/environment/12_renderer.md:3, 11, 26, 28, 35` | says the old renderer "is the current production default … called by every production eval" | **Updated (three sentences + one pointer).** Line numbers corrected from an earlier revision of this plan, which cited `9,13` — the claim is at **11**, and **3** (the Sources header) carries it too. CP6 of [[RENDERER_LAYOUT_REDESIGN]] also edits this file (the minimap paragraph, §R23.5); the hunks are disjoint. |
| `docs/environment/12_renderer.md:364, 617` | both say `scripts/render_recordings.py` — a path that has been wrong since the script moved into `scripts/eval/` | **Updated** in passing, since both sentences are being re-pointed anyway and leaving a knowingly-wrong path next to a corrected one is worse than fixing it. |
| `docs/environment/CONFIG_GUIDE.md:620` | the `training.render_every_n_checkpoints` row says a skipped MP4 "is offline-recoverable via `scripts/eval/render_recordings.py`" | **Updated** — missed by an earlier revision of this plan. This is the documented recovery route for a deliberately skipped render, so it must name the renderer that matches the rest of the run's videos. Comment/prose only: **no key, value or default changes**, so the guide's Maintenance Contract (schema changes) is not triggered and no `CONFIG_CRITICAL_SETTINGS` change-log entry is due. |
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

**Order of work: this lands as ONE commit.** An earlier revision of this plan sequenced the three call sites as six steps, "each step must leave the suite green before the next begins". **That ordering is impossible**, and the plan was wrong to claim it:

- The stub render script at `tests/training/test_async_render_dispatch.py:40` writes its fake MP4 into `<results_dir>/videos/`. The moment step 1 repoints `async_render.py` to look in `videos_v2/`, every upload-asserting case in that file fails — the poll finds nothing where the caller predicted it. The earlier revision listed L119 and L320 as the edits but **missed the stub**, which is the thing that actually breaks.
- The same applies at L320 for step 3, and to the Dreamer video tests, which assert on a `videos/` directory name.
- Step 6 deferred the `SCRIPTS_DEPENDENCY_MAP.md` update to the end, while that map's own Maintenance Contract — and this plan's File Changes section — require it **in the same change** as the `scripts/` edit. The plan contradicted itself.

A partially-repointed tree is red by construction, so "green between steps" cannot be satisfied and would invite whoever hits it to weaken an assertion to get moving. **Land the whole switch as a single commit** — the three call sites, every test that names the old script or folder (including the stub), the guard removal, and the dependency map together. That also makes rollback a single `git revert` (see Rollback).

Work *within* that commit, in a convenient order:

1. Repoint `src/utils/async_render.py` (the default in-training path for both trainers).
2. Repoint `src/utils/evaluation_core.py` (the blocking fallback and both standalone evaluators).
3. Repoint `src/algorithms/dreamer_srl/eval.py` (the Dreamer kill-switch path).
4. Update every test that names the old script or folder — **the stub at L40 first** — and add the new cases.
5. Run the freeze guard one last time, record its verbatim output in the Implementation Report, then remove it and its artefacts.
6. Update the dependency map, the renderer reference doc, the config guide, the skill, the config comments; append the note to the async-render design doc.
7. Run the full suite **once, at the end**. That is the only point at which green is meaningful.

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

#### `tests/training/test_async_render_dispatch.py` — three edits, two new cases

**The edit that matters most, and which an earlier revision of this plan missed: the stub script at L40.** Every case in this file monkeypatches `_RENDER_SCRIPT` to an inline stub, and that stub writes its fake MP4 into `videos/`. If it is not moved, every upload-asserting case in the file fails the moment `async_render.py` starts predicting `videos_v2/` — and the failure looks like a bug in the source change rather than a stale test.

```python
# BEFORE (L40-42, inside the STUB source string):
    videos = os.path.join(results_dir, "videos")
    os.makedirs(videos, exist_ok=True)
    with open(os.path.join(videos, "eval_%s.mp4" % ckpt), "w") as f:
# AFTER:
    videos = os.path.join(results_dir, "videos_v2")
    os.makedirs(videos, exist_ok=True)
    with open(os.path.join(videos, "eval_%s.mp4" % ckpt), "w") as f:
```

The module docstring at **L10** describes the stub as writing "the same `<results>/videos/eval_<ckpt>.mp4` the real renderer writes" — update the folder name there too, or the docstring documents the opposite of the code.

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

#### `tests/algorithms/dreamer_srl/test_render_upload.py` — message text only, but it must not be skipped

An earlier revision of this plan did not know this file existed, and it is the **strongest existing evidence in the repository** for the change being made: `test_render_and_upload_produces_mp4` (L51) drives a real Dreamer recording through the real `_render_and_upload` call site and the real render script in a subprocess. It passes today and takes ~48 s. After the repoint it exercises the new renderer end to end on the Dreamer path — which is the single biggest gap named in A1.

No assertion changes. Four strings name the old script and become misleading once it is no longer the one invoked — the module docstring at **L6** and **L9**, the comment at **L46**, and the failure message at **L93-94** (which also carries the already-stale path `scripts/render_recordings.py`, missing the `eval/` component). A failure message that names the wrong script sends the next reader to the wrong file.

`test_render_and_upload_empty_dir` (L29) needs no edit: it asserts the `None` return when the render fails, which is behaviour this change deliberately preserves (see CP3).

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

#### `docs/environment/12_renderer.md` (lines 3, 11, 26, 28, 35, 364, 617)

**Line numbers corrected.** An earlier revision of this plan cited "lines 9, 13" for the production-default claim; the claim is actually at **L11**, and **L3** (the `> **Sources**:` header) repeats it. L13 is the *dormant* `renderer_v2.py` paragraph, which this plan must **not** touch.

- **L3** and **L11**: the old renderer is no longer "the current production default" — it is the previous renderer, still runnable by hand.
- **L26** ("`render_jax_state` … is the current production default. It is imported by:") and **L28** (which calls the old script "called automatically by eval"): the production offline render path is `scripts/eval/render_recordings_v2.py`, which draws through `src/environment/dashboard/` rather than through `render_jax_state`.
- **L35**: the "swap the imports in `scripts/eval/render_recordings.py` lines 31 and 45" instruction describes a swap that no longer decides anything for the eval path, and must say so.
- **L364** and **L617**: both name `scripts/render_recordings.py`, a path that has been wrong since the script moved into `scripts/eval/`. Fix the path while re-pointing the surrounding sentences — leaving a knowingly-wrong path immediately beside a corrected one is worse than fixing it.

Leave the dormant `renderer_v2.py` paragraph (L13) and the minimap material alone — CP6 of [[RENDERER_LAYOUT_REDESIGN]] owns them, and those hunks are disjoint from these.

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

#### `docs/environment/CONFIG_GUIDE.md` (line 620)

The `training.render_every_n_checkpoints` table row tells the reader that a deliberately skipped MP4 "is offline-recoverable via `scripts/eval/render_recordings.py`". Re-point it to `render_recordings_v2.py`, so the recovery route produces a video that matches the rest of the run's `videos_v2/` rather than a differently-drawn one in `videos/`.

Prose inside a table cell — **no key, value, default or schema change** — so the guide's Maintenance Contract (which binds schema changes to `02_config_schema.md`) is not triggered, and no critical-settings change-log entry is due.

#### Not edited by this plan

`docs/develop/active/refactors/RENDERER_LAYOUT_REDESIGN.md` (another session owns it; its Revision 28 numbering is settled) and `docs/develop/active/issues/KNOWN_BUGS.md` (owned by `bug-curator`; hand it the three affected rows — the defect deferred because a file was frozen, the housekeeping row deferred "to the retirement gate", and the never-read recording format-version stamp, which this change makes the first real second consumer of that format).

---

## Checkpoints

Each is failure-detectable: it names what goes wrong and how you would see it.

- [ ] **CP1 — the command line is accepted by the script that now receives it.** `test_dispatched_argv_is_accepted_by_the_real_renderer` passes, and stderr contains no `unrecognized arguments`. *Detects:* a left-behind `--cleanup-per-episode`, which would make every render exit 2 before drawing a frame, with only a warning in the training log. *Scope limit, stated because the earlier revision of this plan overclaimed it:* this exercises **only** the argv built by `src/utils/async_render.py`. The blocking argv at `evaluation_core.py:380-387` has no test at all, and the Dreamer argv is captured by a mock but never handed to the real script. CP1 alone therefore cannot catch a stale flag at two of the three call sites — which is what CP1b is for.
- [ ] **CP1b — no call site anywhere in `src/` still passes the dropped flag.** `grep -rn "cleanup-per-episode" src/` returns **nothing**. *Detects:* the two call sites CP1 cannot reach. *Fails before the fix* — it currently returns exactly three hits (`async_render.py:130`, `evaluation_core.py:385`, `dreamer_srl/eval.py:555`), so this is a real pre/post check rather than a tautology.
- [ ] **CP2 — the path the caller predicts is the path the renderer writes.** `test_caller_predicted_video_path_matches_what_the_renderer_writes` passes on the M4 fixture. *Detects:* any disagreement between the caller's `<results_dir>/videos_v2/eval_<pct>.mp4` and the script's own derivation — the failure that makes a run render correctly and upload nothing.
- [ ] **CP3 — a failing render still cannot stop training.** With the stub script forced to exit 1, the existing `test_render_failure_no_upload_state_cleared` passes: no upload, state cleared, no exception escapes. On the blocking path, `tests/algorithms/dreamer_srl/test_render_upload.py::test_render_and_upload_empty_dir` passes: a failed render returns `None` rather than raising. **Honest status: this is a regression pin, not evidence about this change.** `poll_render` is not touched by this plan, so it cannot newly start raising; the checkpoint exists to keep that true, not to prove it. An earlier revision of this plan claimed CP3 would also add "a blocking-path case asserting `evaluate_jax_checkpoint` returns normally with `last_video_path is None`" — **no such test exists and the plan never specified one** (no file, no fixture, no account of how the model would be built), so that clause is withdrawn rather than left as an unbuildable instruction. `test_render_and_upload_empty_dir` pins the same property on real code and already exists.
- [ ] **CP4 — a recording with no noise-free observations renders.** Render fixture cell **M6b** (`results/render_audit/recordings/M6b/M6b/`, 2 episodes of 24 and 75 steps, noise on, `true_obs=None`) with `--concat`; assert exit 0 and 99 consolidated frames. *Detects:* the `true_obs=None` shape failing in a panel. *Why M6b rather than a doctored M4:* per A6 this is genuine production-writer output, whereas hand-rewriting a payload risks testing an artefact of the edit. Skip with an explicit reason if the gitignored fixture is absent, and regenerate with `scripts/eval/make_render_fixture_recordings.py`.
- [ ] **CP5 — the disk cost is measured on a scratch copy, and extrapolated per frame.** Copy one real checkpoint's `recordings/<pct>/` into a temporary directory laid out as `<scratch>/recordings/<pct>/`, render it through the new path there, and record in the Implementation Report: the checkpoint id, the episode count, the **total recorded frames**, and `du -sb` for both the per-episode folder and the consolidated file.
  - **Run it on a scratch copy, never in place.** An earlier revision said only "through the new path", which read as in-place: that would write `videos_v2/` into a real run's folder and could overwrite an existing consolidated file. The scratch copy is not a nicety — it is the difference between a measurement and a mutation.
  - **Extrapolate per frame, not per checkpoint.** Episode lengths in these runs span 25 to 734 frames per checkpoint, so multiplying one checkpoint by the checkpoint count is unreliable by a factor of ~2 in either direction (A5).
  - ***Stop condition (rate):*** if the measured total exceeds **8 KB per recorded frame**, stop and raise it. Two real checkpoints measured 5.0 and 5.6 KB/frame; materially above 8 means something other than the known ~3x is happening.
  - ***Report, do not gate (budget):*** multiply the rate by the run's total recorded frames and state the projection. The flat "500 MB per run" ceiling of the earlier revision is withdrawn — the largest `videos/` on this machine is already 2,251 MiB under the **old** renderer, so that gate fails before the change is even made and measures run shape rather than this switch (A5).
- [ ] **CP6 — no `src/` path silently still uses the old renderer or the old folder.** Assert the **exact expected residual**, not "nothing but comments" — an earlier revision's wording left the call as a judgement, and the grep does not come back empty:
  - `grep -rn "render_recordings\.py" src/` returns **exactly two** lines, both prose deliberately naming the previous renderer: `src/environment/renderer.py:568` (a frozen file, must stay untouched) and `src/algorithms/dreamer_srl/eval.py:311` (a docstring about the recording *format*, which both renderers consume unchanged). Any third hit is a missed call site. *It currently returns nine.*
  - `grep -rn '"videos"' src/` and `grep -rn "'videos'" src/` both return **nothing**. *They currently return `async_render.py:120`, `evaluation_core.py:275` and `dreamer_srl/eval.py:547` — the three hard-coded output folders.*
  - `grep -rn "cleanup-per-episode" src/` returns **nothing** (same as CP1b).
- [ ] **CP7 — the guard's final verdict is recorded before it is deleted.** Verbatim `check` output in the Implementation Report, exit code stated. Any non-`PASS` state or frame difference is a **stop and ask the user**, not a deletion.
- [ ] **CP8 — the full test suite is green**, with the removed guard test gone rather than skipped. Two classes of test must be **confirmed run, not assumed**:
  - The `integration`-marked cases (registered in `pyproject.toml`), which skip silently without the gitignored fixtures. If they skipped, say so and regenerate with `scripts/eval/make_render_fixture_recordings.py`.
  - The **`slow`-marked** cases, which an earlier revision of this plan did not know about. `slow` is **not a registered marker** in `pyproject.toml` — only `integration` is — so these run with an "unknown mark" warning rather than being selected or excluded deliberately, which is exactly how they get overlooked. Two must be named and must pass: **`tests/algorithms/dreamer_srl/test_render_upload.py::test_render_and_upload_produces_mp4`** (~48 s; drives a real Dreamer recording through the real call site and the real script — after this change, the only end-to-end proof of the Dreamer path on the new renderer) and **`tests/algorithms/dreamer_srl/test_eval_video_smoke.py::test_e2e_smoke_checkpoints_and_recordings`** (a real trainer plus a real render). *Detects:* the "green because it compared nothing" shape this project has been bitten by twice.
- [ ] **CP9 — training speed is unchanged, within a stated tolerance.** The render is a CPU-only child on the non-blocking path, so training steps/second should not move. Record before/after numbers from the same config, seed and node, over a window of **at least 200 training iterations** so warm-up does not dominate. ***Tolerance:*** a change within **±3 %** is noise and passes; **>5 %** slower warrants discussion; **>15 %** slower blocks the merge. An earlier revision gave no tolerance at all, which makes any number "fine".
  - **The render-speed expectation is corrected to an observation.** The earlier revision predicted the new renderer would be "slower per frame — 1.78× the old one", citing the redesign's synthetic speed gate. **Measured on a real recording, the opposite is true**: on the same 3 episodes (500 frames, `--workers 8`, `JAX_PLATFORMS=cpu`) the new renderer took **64 s** wall against the old renderer's **113 s**, i.e. ~0.16 s/frame against ~0.31 s/frame on the long episodes — the new renderer is roughly **2x faster** per frame. The plan reviewer measured 151 ms vs 306 ms per frame at `--workers 1` independently, which agrees. Record what is observed; do not carry the 1.78x figure forward, and do not treat a *faster* render as a failed checkpoint.
  - Note separately whether any live configuration uses the **blocking** path (`training.async_video_render: false`, and the standalone evaluators), since that is the only path where render duration is on the critical path at all.

---

## Rollback

**Nothing this change touches is destructive, and that is the first thing to know.** No recording is deleted, no existing video is overwritten, and the old renderer stays on disk and runnable. Every video this change could fail to produce can be produced again later from recordings that are still there. Rollback is therefore about restoring *behaviour*, not about recovering *data*.

**(a) Undoing the switch is one command.** Because the whole change lands as a single commit (see "Order of work"), `git revert <switch-commit>` restores all three call sites to the old renderer, restores `videos/` as the predicted output folder, and restores the four deleted freeze-guard paths — `scripts/eval/v1_path_guard.py`, `tests/env/test_v1_path_guard.py`, and both files under `docs/develop/active/refactors/renderer_layout_redesign/v1_guard/` — since a revert of a deletion is a re-addition. The guard's baseline stays valid across the round trip: it hashes the ten frozen files, none of which this plan modifies.

**(b) Recovering a run whose checkpoint videos are missing.** If a render failed during the window, the recordings are untouched under `<run>/recordings/<checkpoint>/`. Render by hand with either renderer and upload the result manually:

```bash
# the old renderer, writing to videos/ as it always did
JAX_PLATFORMS=cpu python scripts/eval/render_recordings.py \
    <run>/recordings/<checkpoint>/ --concat --skip-existing --cleanup-per-episode --fps 5
```

**This route is verified, not assumed.** The old renderer was run against a current (2026-09-14) recording while this plan was being revised: exit 0, and its consolidated output matched the file the training run itself wrote months earlier to within 0.01 % (956,266 B vs 956,367 B). The old renderer has not rotted, and it still reads today's recordings.

**(c) Runs already in flight are unaffected in both directions.** `src/utils/async_render.py` binds the script **path** at import time (L56, module level) and the child re-reads the file at each dispatch. So a trainer that imported the module before the switch landed keeps invoking the old renderer for the rest of its life, and a trainer that started after keeps invoking the new one for the rest of its life — including after a revert — until it is restarted. Neither can be broken mid-run by the on-disk change, and neither can hit a missing file, because **both scripts remain on disk in both directions** (this plan deletes neither, and a revert re-adds nothing that the new renderer needs). No running job has to be stopped to roll back, and none has to be stopped to roll forward.

**(d) The retired guard does not participate in either route.** `v1_path_guard.py` is a read-only comparison tool: it hashes files and compares rendered frames, and nothing in the training, evaluation, render or upload path imports it or calls it. Its absence cannot block a rollback, and its restoration by revert is a convenience rather than a requirement. The one thing its absence *does* cost is the ability to prove, after a rollback, that the ten frozen files are still byte-identical to their 2026-09-14 baseline — so if a rollback is ever performed because something looked wrong with V1's *output*, restore the guard from git first and run `check` before drawing conclusions.

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
3. **The registry rows.** Three entries in the Known Bugs registry change meaning with this commit (a defect deferred *because* a file was frozen; a housekeeping item deferred "to the retirement gate"; the recording format-version stamp nothing reads). `bug-curator` owns the registry — confirm it should be handed these after the change lands. **When handing them over, do not repeat this plan's retracted claim** that every real recording on disk is unrenderable (see A2) — the accurate scope is "written before 2026-09-09".

4. **Who re-numbers the stranded guard checkpoints?** [[RENDERER_LAYOUT_REDESIGN]] §D5.4 defines the freeze guard's own checkpoints **CP0.1a** and **CP0.1b** (the guard's baseline-record and verify steps) alongside **CP-G** ("run the guard at every phase boundary"). Retiring the guard strands all three: after this commit they name an instrument that no longer exists, in a document whose Phase 4 is still unbuilt. **This plan deliberately does not edit that document** — its Revision 28 numbering is settled and another session owns it. *Proposed owner: the `RENDERER_LAYOUT_REDESIGN` session*, which should record the retirement in its own numbering. Confirm that routing, or name a different owner.

5. **Commit discipline on the incoming default (A8, item 4).** The new renderer is taking ~5 commits/day and its script is re-read from the NAS at every checkpoint dispatch, so a half-landed edit breaks live renders. *Proposed owner: the `RENDERER_LAYOUT_REDESIGN` session* — gate every commit touching `scripts/eval/render_recordings_v2.py` or `src/environment/dashboard/` on `tests/scripts/test_render_recordings_v2.py`. This plan cannot enforce another session's discipline; it can only name the risk and the owner.
