---
id: 20260919_1315_eval_videos_moved_to_v2_renderer
date: 2026-09-19
time: "13:15"
folder: episode_renderer
tags: [decision, design, meta, wandb]
summary: "Evaluation checkpoint videos now come from the new dashboard renderer on both trainers; the V1 freeze guard was retired by user decision, with git revert of a single commit as the rollback."
headline: "Eval videos switched to the V2 dashboard renderer; V1 kept on disk, freeze guard retired, rollback is one revert"
related: ["20260919_1316_two_modules_one_geometry_drift", "20260919_1317_checks_that_cannot_fail"]
session_origin: claude_code
session_label: "eval renderer switchover (v4.0)"
importance: high
status: settled
valid_until: null
confidence: high
supersedes: []
raw_source: none
raw_completeness: none
---

# Evaluation videos moved to the V2 dashboard renderer, and the V1 freeze guard was retired

## Key conclusion

The three places in `src/` that turn eval recordings into MP4s now invoke
`scripts/eval/render_recordings_v2.py` instead of `render_recordings.py`, writing to
`<run>/videos_v2/`. The old renderer stays on disk and runnable by hand; rollback is
`git revert 891d2057`. The user chose a **direct repoint over a config switch**, and
chose to **retire** the V1 freeze guard rather than re-baseline it, on the reasoning that
git history is the rollback mechanism. The guard's final verdict was recorded before its
files were deleted, because that evidence becomes unreproducible afterwards.

## Evidence, measurements, facts

- **The three call sites**, all previously frozen files: `src/utils/async_render.py:56`,
  `src/utils/evaluation_core.py:380`, `src/algorithms/dreamer_srl/eval.py:546`.
- **A naive repoint crashes every render.** All three passed `--cleanup-per-episode`,
  which the V2 parser rejects — `argparse` exits 2 before a frame is drawn. Because a
  failed render only warns, training would complete normally with **no videos for the
  entire run** and one unread line in a log. No existing test could see it: they all
  monkeypatch the render script to a stub that accepts any argument.
- **Two discriminators prove which renderer ran**, and both were checked on real runs:
  the phrase `frames verified` exists only in V2, and V1 writes `videos/` while V2 writes
  `videos_v2/`. On every verified run the run directory held exactly
  `models/ recordings/ videos_v2/`.
- **Both trainers verified on real GPU runs**, not smoke tests. dreamer-srl reaches the
  renderer through the async dispatch path; recurrent PPO reaches it through the
  **blocking** branch in `evaluation_core.py`, which had no test of its own
  (`training.async_video_render: false` is the default in `configs/train/recurrent_ppo.yaml`).
- **WandB receives the video**, checked against the cloud rather than local staging: the
  run summary's `eval/video` artefact was downloaded back through the API and md5-matched
  the local render (`3b33279bfa751af2c833645053b24a6c`). Runs `1tnkacym` and `ytjaq3wc`.
- **Checkpoint cadence is 200,000 episodes for RecurrentPPO** — `configs/train/recurrent_ppo.yaml`
  overrides the 10,000 in `configs/train/default.yaml`, which is only the DQN/PPO fallback.
  Time to first video was 3m32s at ~1,088 it/s.
- **Disk roughly triples**, measured on two real checkpoints (~3.0x), about half of it
  per-episode MP4s that V2 deliberately never deletes. An earlier estimate of ~6x was
  wrong: it extrapolated a 500-frame checkpoint against a run whose mean checkpoint holds
  251 frames. Extrapolate **per frame**, never per checkpoint.
- **The guard's last verdict**, now unreproducible for its frame half: all ten frozen files
  hash-identical to their 2026-09-14 baseline at HEAD, no commit touched any since, and
  M1/M2/M4 rendered 8 raw frames byte-identical. The file half survives in git history;
  the frame half needs the deleted script plus gitignored fixtures.

## Decisions and actions

- **Direct repoint, no config switch** (user's choice when offered a switch defaulting to V2).
- **Freeze guard retired** (`scripts/eval/v1_path_guard.py` + test + two baseline artefacts
  deleted). Recorded as a trade, not a free win: git makes V1 drift *recoverable* but no
  longer *visible*, and four of the guard's ten files are read-only dependencies of the new
  default renderer.
- **CP7 recorded red and closed by user decision, deliberately not ticked green.** It was
  unsatisfiable by construction — the guard's frozen set contained the three call sites the
  plan existed to repoint, so the check contained its own subject. Reusable rule: *a gate
  must not measure the artefact the gated change is required to modify.*

## Open questions and follow-ups

- The renderer is production code but **no longer frozen or gated**, while another session
  actively develops `src/environment/dashboard/`. It is re-read from the NAS at every
  checkpoint dispatch, so a half-saved edit when a checkpoint fires means a failed render
  behind one warning line.
- Three prose references to the deleted guard survive in comments; one sits in a failure
  message a reader would hit while debugging a renderer change.
- Two earlier runs of the rPPO experiment family died mid-training at ~1.0M and ~0.8M
  episodes. Unexplained, unrelated to rendering.

## References

- **Why a new folder** (`episode_renderer`): the episode-video dashboard is a standing
  subsystem with its own plan, its own audit instrument and now its own production role;
  none of the ten existing folders covers it (`config_system` is the loader, `cluster_ops`
  is lab infrastructure, `behavior_measures` is analysis). Created with the user's explicit
  agreement, noting the wiki was already at its 10-folder audit threshold.
- Plans: `docs/develop/active/refactors/EVAL_RENDERER_SWITCHOVER.md`,
  `docs/develop/active/refactors/RENDERER_LAYOUT_REDESIGN.md` (Revision 29 records the freeze retirement).
- Commits: `891d2057` (switchover), `b3469b63` (freeze retired), `a79798ab` (launch audit records).
- WandB render checks: https://wandb.ai/sungwoolee/grid_world_pain/runs/1tnkacym ·
  https://wandb.ai/sungwoolee/grid_world_pain/runs/ytjaq3wc
- Related: [[20260919_1316_two_modules_one_geometry_drift]], [[20260919_1317_checks_that_cannot_fail]]
- Raw conversation is local-only (session `14318db1`); no archive was produced.
