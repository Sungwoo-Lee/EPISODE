---
title: "Retiring the old episode-video renderer, and dropping \"v2\" from the new one's name"
topic: refactors
status: active
created: 2026-09-21
last_updated: 2026-09-22
aliases: [renderer_v1_retirement]
---

# Retiring the old episode-video renderer, and dropping "v2" from the new one's name

> **Status**: PLANNED — nothing implemented. Four steps. **No open user questions.** Reviewed `SOUND WITH CONCERNS`; all findings applied in Revision 3, which then gate-passed `SOUND — nothing blocks implementation`.
> **As of 2026-09-22**: §R30.2's retirement condition is **met** and **Step 2 is available now**; Steps 1, 3 and 4 still wait — see [§Current state](#current-state-2026-09-22).
> **Opened**: 2026-09-21 · **Revision 3** (2026-09-21) — applies the `plan-reviewer` findings, chiefly moving one audit fix into Step 2 and replacing an inoperable `git stash` instruction
> **Related**: [[RENDERER_LAYOUT_REDESIGN]] §R30 (the retirement condition this executes) · [[EVAL_RENDERER_SWITCHOVER]] (the 2026-09-17 switch this cleans up after; **this plan must edit its Rollback section — §Obligations**) · [[ASYNC_CHECKPOINT_VIDEO_RENDER]] (the dispatch mechanism that makes timing load-bearing) · [`plan_renderer_v1_retirement`](../../../reviews/plan_renderer_v1_retirement.md) (the review) · [`SCRIPTS_DEPENDENCY_MAP`](../../../environment/SCRIPTS_DEPENDENCY_MAP.md) (contract fires on Steps 1, **2**, 3 and 4)

---

## Context

The project draws a video of each evaluation episode — a dashboard showing the agent on its grid alongside its hunger, injury and sensory readouts. Until four days ago those videos came from the **original renderer** (`src/environment/renderer.py`). On 2026-09-17 a **replacement** took over: a new package (`src/environment/dashboard/`) driven by a script whose filename ends in `_v2`. The user has since watched checkpoint videos arrive correctly from the new path and asked for the cleanup.

They asked for three things: stop the new renderer borrowing code from the old one, retire the old one, and rename the new one so it no longer carries a version number — *"as we will not distinguish them through version, new version no need to use v2 as the name."* And: *"Since the trainings are still ongoing, let's make plan and feedback first."*

**Fourteen training runs are in flight**, launched 11:52 today across seven machines at ten million episodes each. Each writes its videos by launching the render script *by filename*, and each memorised that filename at startup. **The user's decision is to wait for those runs before touching the render path at all.**

**A fourth piece surfaced after the first draft and reorders everything.** The project has a *pixel audit* — an instrument that inspects a rendered frame and reports defects like text printed over other text, or a panel silently dropped. Such an instrument is worthless unless it can be shown to actually *fire*, and this one proves itself with seven known defects it must catch. **Every one of those seven lives in an old renderer** — five in the one being retired, two in a dormant April file. So the audit's self-proof depends on old renderers being kept alive *in order to stay broken*, and deleting them destroys the evidence that the audit can detect anything at all. **The user's decision: replace all seven with deliberate breaks of the current renderer**, and fold that into this plan — which makes it a **precondition** of the archival, not a follow-up.

**Revision 3 applies an adversarial review.** The verdict was `SOUND WITH CONCERNS` with no critical finding: the ordering is right and every measurement re-verified. But the review found that **Step 2's own exit gate could not pass as written** — the audit reaches into the old renderer on a path Step 2 depends on, and the plan had scheduled that fix for Step 3 — and that one instruction in Step 2 (`git stash`) would have reverted a parallel session's uncommitted work. Both are fixed below, along with a byte-identity gate that assumed something the project's own record contradicts.

**Nothing is open.** The script becomes `render_episode_videos.py`; a dead duplicate elsewhere in the codebase is recorded as a named follow-up rather than folded in.

---

## Analysis

### A1. The live-cluster census — the first checkpoint, run before anything else

`scripts/lab/gpu_status.py` and today's diary agree, which is the cross-check that matters (the diary records intent, the GPUs record reality):

| Node | GPUs busy | Utilisation | Attributed to |
|---|---|---|---|
| 101, 103, 104, 105 | 0 and 1 (RTX 2080 Ti) | 89–95 % | 8 of the 14 runs in today's diary, launched 11:52 |
| 106, 107, 108 | 0 and 1 (RTX 3090) | 80–100 % | the remaining 6 of those 14 |
| 113 | GPU 0 only (RTX 4090) | 40 %, 5061 MiB | **unattributed** — no diary row today |
| 102, 109–112, 114, 113:1 | — | idle | free |

The fourteen are the `rppo_basicq2_lvl00..lvl06` × {unmodulated, neuromodulated} wave ([`docs/diary/2026-09-21.md`](../../../diary/2026-09-21.md), design [`BASIC_LEVELS_Q2_DEFAULT`](../../../experiments/active/basic_levels_q2_default/BASIC_LEVELS_Q2_DEFAULT.md), seed 42, **10 M episodes each**). They will run for days.

**Node 113:0 is busy and unattributed** — a 5 GB process at 40 % with no diary row. It must be identified before Step 4's census is trusted: the one thing it must not be is a fifteenth run rendering through the script.

### A2. What the render dispatch re-reads, and when — broader than "the rename"

`async_render.py:56` binds the script **path** into a module constant at import time; `dispatch_render()` then runs `subprocess.Popen([sys.executable, _RENDER_SCRIPT, ...])`. The dependency map records the consequence: *"an in-flight trainer keeps invoking whichever renderer it started with."*

**The half nobody says out loud:** the *path* is frozen in the trainer; the *file at that path* is not. The child is a new process that reads the file — and everything it imports — from disk at each dispatch.

| What we change | Does a live run see it? | Cost of a mistake |
|---|---|---|
| `async_render.py`, `evaluation_core.py`, `dreamer_srl/eval.py` | **No.** Already imported into the running trainer. | nothing, until restart |
| `scripts/eval/render_recordings_v2.py` (**contents**) | **Yes, next checkpoint.** | that checkpoint's video |
| `src/environment/dashboard/**` (**contents**, incl. `__init__.py`) | **Yes** — imported fresh by the child. | that checkpoint's video |
| `scripts/eval/render_recordings_v2.py` (**filename**) | **Yes, permanently** — the path never updates. | every remaining video of that run |

**Correction carried from Revision 1.** That draft called Step 1's additive half "zero live exposure". Wrong: the line added to `dashboard/__init__.py` **executes inside every render child**. Small, but not zero. The wait decision makes it moot in practice; the claim is corrected rather than left standing — and row 3 is exactly why Step 2 must be monkeypatch-only (§A11.4).

### A3. What the new renderer still takes from the old one

| Line | Imports | Reachable when | Production? |
|---|---|---|---|
| `:223` | `save_jax_video` | per-episode MP4 write | **yes** |
| `:474` | `save_jax_video` | `--concat` consolidated write | **yes** — training passes `--concat` |
| `:277` | `render_jax_state`, `thermal_color_limits` | inside `_benchmark()`, `--benchmark` only | **no** |

`:277` is a **measuring instrument whose subject is the old renderer**. It retires with its subject rather than being ported. The whole production coupling is **one function**: `save_jax_video` at `renderer.py:1094`.

### A4. The duplicate in `grid_world.py` is not a drop-in replacement — measured

```python
# renderer.py:1094 — streaming
with imageio.get_writer(output_path, fps=fps) as writer:
    for frame in frames:
        writer.append_data(frame)

# grid_world.py:701 — materialising
imageio.mimsave(output_path, frames, fps=fps)
```

Both production call sites pass **generators** (`:237`, `:491`). `imageio.mimsave` consumes a sequence, so the duplicate would fail or silently materialise an episode in memory. **The copy that moves is `renderer.py`'s.** The duplicate has zero callers and is handled as a follow-up (§Follow-ups).

### A5. The dependent inventory is larger than §R30.3 records

§R30.3 lists **six**; a fresh sweep finds **thirteen** V1 dependents, three of them tests — plus a **fourteenth belonging to the April file**.

| # | Dependent | Needs | In §R30.3? |
|---|---|---|---|
| 1 | `scripts/eval/render_recordings_v2.py` `:223 :277 :474` | `save_jax_video`; benchmark helpers | yes |
| 2 | `scripts/eval/render_recordings.py` | the old script itself | (implied) |
| 3 | `scripts/eval/benchmark_render.py` `:39` | `render_jax_state` — V1 is its subject | yes |
| 4 | `scripts/eval/render_layout_audit.py` **`:418`**, `:465` | **`thermal_color_limits` in `load_inputs` (§A11.1)**, plus the `v1` render arm | yes |
| 5 | `scripts/eval/make_render_fixture_recordings.py` `:839` | draws fixtures through V1 | yes |
| 6 | `scripts/dreamer/visualize_dream.py` `:159 :180` | draws imagined rollouts through V1 | yes |
| 7 | `src/utils/eval_recording.py:34` | a **contract**, not an import (A6) | yes |
| 8 | **`save_snapshot.py:14`** (repo root) | `render_jax_state` | **no** |
| 9 | **`scripts/media/record_env_demo.py:14`** | `render_jax_state`, `save_jax_video` | **no** |
| 10 | **`tests/env/test_thermal_rendering.py:47,:310`** | V1 drawing helpers | **no** |
| 11 | **`tests/algorithms/dreamer_srl/test_eval_recording.py:118,:138`** | renders through V1 | **no** |
| 12 | **`tests/env/test_dashboard_v1_imports.py:99,:121`** | asserts by name what the dashboard borrows | **no** |
| 13 | **`docs/.../render_current_frames.py:44`** | the redesign's frame generator | **no** |
| 14 | **`test_c4.py` (repo root) `:5,:21`** | `render_jax_state_v2` — **an April-file dependent, not a V1 one** | **no** |

Items 8–9 are corroborated by [`12_renderer.md`](../../../environment/12_renderer.md) lines 31–33. **Item 14 is why my thirteen-item sweep excluded it**: it imports `renderer_v2`, so it belongs to the April column and must be handled when that file goes.

**Item 12 needs care.** `test_dashboard_v1_imports.py` pins what the new renderer borrows, including a subprocess check that a bare package import is Matplotlib-free. Step 1 removes the last borrow, so its subject partly dissolves — but the **Matplotlib-free assertion must survive**; that property is about the training path's import cost, not V1.

### A6. Archiving V1 rehomes a contract, not just a file

`src/utils/eval_recording.py:34` carries no import — it carries a sentence: *"Exactly the fields `render_jax_state` reads. Keep in lockstep with renderer.py."* That is the **definition of the recording format**: every `.rec.gz` is specified by reference to a function in the old renderer. The same docstring justifies not bumping `RECORDING_FORMAT_VERSION` because *"the branch lives in `renderer.py`"* — also about to stop being true. Rehoming is **prose, not code**, and the dangling reference produces no error, just a format with no stated owner.

### A7. The rename surface, measured

| Thing | Count | Where |
|---|---|---|
| `render_recordings_v2` refs, all types | **139** | 24 `.py`, 110 `.md`, 2 configs, 1 shell script, 1 skill |
| `videos_v2` refs in `.py` | **38** | 8 files |
| `videos_v2/` directories **on disk** | **26** | under `results/` |
| `videos/` directories on disk (V1's) | **505** | under `results/` |

### A8. The retirement condition is already running

§R30.2: the old renderer retires once *"two or three real training runs have produced their checkpoint videos through the new script with no occasion on which anyone needed to fall back."* **The fourteen live runs are exactly that.** Step 3 needs them to finish cleanly, not a new experiment.

**The circularity, and its honest resolution.** Step 1 edits the path those runs render through; a fault there sends someone back to the old script and resets the streak Step 3 depends on. Adopted: **any fallback counts, including one we caused.** Rejected and recorded so nobody re-derives it: *"that one doesn't count, it was our own bug"* — self-serving, and it would let the condition be met by a path nobody trusted. **The wait decision dissolves this**: Step 1 lands after the runs finish, so it cannot contaminate their evidence.

### A9. Why a green test suite is not the gate

A renderer change here once passed eighteen new unit tests while breaking the product. A unit test asserts about boxes and frame counts; a human looking at a frame notices the picture is wrong. **Every step below names a rendered artefact someone looks at.**

### A10. The pixel audit proves itself with defects in old renderers

Verified at `HEAD` by reading `CONTROLS` (`render_layout_audit.py:1732-1779`); the control tests genuinely run — I executed `tests/env/test_render_audit_controls.py`: **71 passed, 0 skipped, 125 s**.

| Control | Renderer | Rule(s) | Defect |
|---|---|---|---|
| `D1` | **v1** | `text_over_text` | `OBS:` readout overprints the THERMOCEPTION pod title |
| `D2` | **v1** | `out_of_card`, `text_over_text` | `REAL: --` escapes its card into the EXTERO NOCICEPTION title strip |
| `D3` | **v1** | `text_over_border` | `MINIMAP` label lies across the Run Context border |
| `D10` | **v1** | `observed_caption` | Nutrition/Injury captioned OBS/REAL though the world observes neither |
| `D12` | **v1** | `panel_absent` | Proprioception emitted by the viz adapter, never drawn |
| `D6` | **v2** (April) | `text_over_text` | COLLISION title overprints its C/U/R/D/L labels |
| `D8` | **v2** (April) | `panel_absent` | silently drops the interoceptive-nociception panel |

**Seven controls, but only five distinct rules** — `text_over_text` (D1, D2, D6), `out_of_card` (D2), `text_over_border` (D3), `panel_absent` (D8, D12), `observed_caption` (D10). Stating this prevents two rules being quietly dropped.

**Two casualties beyond the seven.**

1. **`numeric_in_arena` is proven only by the April file.** `test_numeric_in_arena_is_reachable_and_fires` (`:587`) renders `"v2"` with `--arena-axes thermoception`, asserting 5 hits. It cannot move to V1 — the audit's docstring: *"V1 draws its arena into an UNLABELLED Axes, so the rule cannot be pointed at V1's arena at all."* Deleting April costs a **third** proof. **So the replacement covers six rules, not five.**
2. **The negative controls are pinned on V1 frames** — the half the audit's own docstring calls the one *"no positive control can make"*. `V1_M4_COUNTS` / `V1_M1_COUNTS` pin **exact** per-rule counts on two V1 frames; `SILENT_RULES` (`clipped`, `out_of_canvas`, `legibility`, `numeric_in_arena`, `fill_over_text`) are asserted silent on them; ~7 further tests bind the `v1_m4` / `v1_m1` fixtures, including `test_collision_controls_go_quiet_when_the_measurement_is_broken`, which proves the rules are decided by measured pixels rather than a constant.

**And the audit's own code breaks:** `render_capture`'s `v1` branch does `from src.environment.renderer import render_jax_state` (`:465`), so after deletion the controls could not be *expressed*, only deleted.

**What already breaks current code, and what that pattern cannot reach.** `M-E`, `M-T`, `M-C@{0.06,0.12,0.25}`, `M-G` (`test_render_audit_controls.py:921-940`) break today's renderer — but target only `cell_overdraw` and `cell_probe_blind`. **Nothing proves the six rules above by breaking current code.** And the harness does not extend: `_arena_figure` (`:722`) builds a **synthetic arena** (`plt.figure`, a `page` Axes, an `arena` Axes, squares via `cells.py`) with no cards, titles or panel registry, so it structurally cannot express a card-title collision or a dropped panel. **"Add seven entries to `MUTATION_CELLS`" badly understates the work.**

**The good news that shrinks Step 2.** No new audit arm is needed. The audit deliberately has none for the current renderer — `--renderer` accepts only `("v1","v2")` and the else-branch raises, because *"the audit must not import the thing it audits."* Callers instead **hand it a frame by substituting `render_capture`**, and `tests/env/test_dashboard_frames.py:303-311` **already does this**, running the full audit over a real current-renderer frame (*"This runs EVERY rule"*). Step 2 reuses an exercised pattern; §D5.2's no-import rule is preserved.

### A11. What the plan review changed

Verdict `SOUND WITH CONCERNS`, no critical finding; ordering confirmed, every A10 claim re-verified, no data-loss path. I re-verified each finding below against the code rather than accepting it.

**A11.1 — `load_inputs` reaches into V1 on every call, including the substitution path (blocking).** `render_layout_audit.py:418` opens with `from src.environment.renderer import thermal_color_limits`, unconditional, used at `clim = thermal_color_limits(...)`. And `test_dashboard_frames.py:299` calls `audit.load_inputs(...)` **before** substituting `render_capture`. So with V1 moved aside, every replacement control fails at load and **CP2.7 cannot pass**. Revision 2 scheduled this edit for Step 3. **It moves into Step 2.** Fix: push the call into `render_capture`'s `v1` branch — its only consumer — or drop the field.

**A11.2 — the `CONTROLS` edit is mandatory, and `--controls` cannot survive (blocking).** `run_controls` does `audit_frame(fi, ctl["renderer"])` for every entry, and all seven say `"v1"`/`"v2"`. Revision 2's "only if" was wrong. Separately, `--controls` as a **CLI mode** cannot survive Step 3: the audit may not import the dashboard, so it cannot render a current frame itself. Its fate, the USAGE docstring and dependency-map **row 190** are decided in the same commit — **so the map's maintenance contract fires on Step 2, not only Step 3.**

**A11.3 — `git stash` was inoperable and dangerous (my error, from Revision 2's CP2.7).** `git stash` saves *changes* and resets to HEAD; it cannot move an unmodified tracked file aside, and `rm` + stash puts the file **back**. Its natural failure mode is `git rm` + commit — precisely the deletion CP2.7 exists to avoid. Worse, in this repo a plain stash sweeps **parallel sessions' uncommitted work**: today a staged `SAVED_RUN_CONFIG_COMPAT.md` and a modified `artifact_format_bugs.md`, reverted under another session with no warning. **Replaced with `mv` out and `git checkout --` back. There is no `git stash` anywhere in this plan.**

**A11.4 — Step 2 is only live-safe if it is monkeypatch-only.** If the mutation hook lands under `src/environment/dashboard/`, Step 2 is on the render path while fourteen runs are live — breaching the wait decision and repeating the Revision-1 error (A2, row 3). **Every deliberate break must be a test-process monkeypatch with no package line changed**, or Step 2 inherits Step 1's wait gate.

**A11.5 — CP1.4's byte-identity assumed reproducible MP4 encoding; the record points the other way.** [[EVAL_RENDERER_SWITCHOVER]] records the **same renderer on the same recording** at **956,266 B vs 956,367 B** (lines 35, 587, 754-755) — 101 bytes apart. That was a re-render months later rather than a same-session repeat, so it is not conclusive, but it is real counter-evidence. **Settle it before Step 1** (CP1.0). A gate that fails for the wrong reason invites someone to weaken it.

**A11.6 — nothing enforces the coverage table.** A hand-written table can silently omit a rule. **Derive the rule list from the audit and parametrise over it**, which is what makes the ordering enforceable rather than aspirational. This needs a canonical list, which **does not exist today**: rules are emitted in *three* shapes — `Finding("clipped", ...)` literals, `rule, detail = "text_over_text", ...` assignments, and bare positional strings on their own line inside multi-line calls (`out_of_card` `:1619`, `cell_probe_blind` `:1225`, `outline_like_token` `:1264`, `cell_overdraw` `:1294`). **My own two-form grep missed `out_of_card` entirely** — direct evidence the list cannot be hand-maintained. The full vocabulary is **14 rules**: `text_over_text`, `text_over_border`, `text_over_fill`, `fill_over_text`, `out_of_card`, `clipped`, `out_of_canvas`, `panel_absent`, `observed_caption`, `legibility`, `numeric_in_arena`, `cell_overdraw`, `cell_probe_blind`, `outline_like_token`.

**A11.7 — pin zero per defect rule, not the old non-zero counts.** V1's exact counts worked because V1 was **frozen**. The dashboard is **live** and carries an open defect — the height twin of the width bug, `panels._map_h` declaring 36 px less than the painter needs at every range (Known Bugs, OPEN, latent, arms at sensor range ≥ 5). Non-zero pins on a live renderer break on every legitimate change and train people to edit the number. **The stable pin is zero on every defect rule.** And this must be **measured first**: no test today asserts the current renderer scores clean on the non-`cell_` rules — `test_a_real_frame_measures_every_square...` checks only `cell_*` and `outline_like_token`. Run the full audit on M4/M1 through the substitution path **before** writing any pin.

**A11.8 — `panel_absent`'s mutation is intercepted before the audit sees it.** `EpisodeRenderer.__init__` calls `check_completeness(self.ctx)` *before anything is drawn* (`episode.py:175`), and it **raises `ValueError`** naming any breakdown name with no panel. So dropping a panel to create the defect raises instead of rendering. The mutation needs **two monkeypatches** — suppress the guard, drop the panel — **plus a paired assertion that the unpatched guard really does raise**, otherwise the bypass silently proves nothing about the guard.

**A11.9 — lows, applied.** `test_c4.py` (repo root) is the fourteenth dependent, of the **April file** (A5). CP3.2's grep hits **prose**: `sensor.py:689` (a comment naming `renderer.py:800, renderer_v2.py:331`) and `dashboard/__init__.py:32` (the NAMING paragraph) — so it must be scoped to import statements. And `video.py`'s required docstring can trip `test_no_file_in_the_package_names_the_frozen_renderer_at_all`, which skips lines starting `#` **or containing a quote character**, then flags any line holding both `renderer` and `import` — note **"imported" contains "import"**, so a docstring line like *"copied from the old renderer rather than imported"* with no quote character on it would fail.

**A11.10 — a risk the review surfaced and nothing can fix here.** The `M4`/`M1` fixture recordings Step 2's calibration depends on are **gitignored and cannot be regenerated** (Known Bugs: five of the eleven fixture worlds can no longer be built). A `results/` loss would take Step 2's calibration with it. This argues for doing Step 2 promptly once started, and for the standing snapshot habit before any non-trivial git operation.

---

## User decisions recorded (2026-09-21)

| # | Decision | Effect |
|---|---|---|
| 1 | **Replace all seven controls with deliberate breaks of the current renderer** — chosen over deleting both renderers and accepting fewer proofs, and over keeping the April file until a replacement exists. | Becomes **Step 2**. |
| 2 | **Fold it into this plan**, since archiving V1 is what breaks five of them. | Step 2 is a **precondition** of Step 3. |
| 3 | **Wait for the fourteen runs** before touching the render path. | Gates Step 1; dissolves the A8 circularity. |
| 4 | **New output-folder name; the 26 existing `videos_v2/` folders left as-is.** | Step 4; nothing on disk moves or is deleted. |
| 5 | **Delete V1 rather than move it.** | Step 3 is `git rm`; git history is the rollback, per §R29. |
| 6 | **The April file stays untouched until Step 2 lands.** | It is **not dead code** while D6, D8 and the `numeric_in_arena` proof are live. |
| 7 | **The script becomes `render_episode_videos.py`** — chosen over reusing `render_recordings.py` so one filename never means two renderers across git history. | Step 4. |
| 8 | **`grid_world.py`'s dead duplicate is a separate change after this lands.** | §Follow-ups — deliberately not folded in. |

---

## Current state (2026-09-22)

**Two of the fourteen runs have finished, and they satisfy the retirement condition.**

`rppo_basicq2_lvl05_t1none_s42` and `rppo_basicq2_lvl06_t1none_s42` both reached the full ten-million-episode budget. Their logs (`logs/20260921_114852.log`, `logs/20260921_114900.log`) end with `Training complete.`; each run holds **50 checkpoints**, the last at episode **10,000,058** and **10,000,060**. Through the logs' final stretch every `[CHECKPOINT] Saving model` line is followed by a matching `[render] … render finished` line pointing into `videos_v2/`, including the final checkpoint of each run.

At a 2026-09-22 00:15 snapshot: **150 files in each of those two runs' `videos_v2/`**, **1,305 across all fourteen runs**, and **zero in any `videos/`**. Nobody fell back to the old renderer at any point. *(The 150 is a directory count, not a per-checkpoint derivation — the new renderer also keeps per-episode MP4s, and the exact breakdown was not measured.)*

§R30.2 asks for *"two or three real training runs [that] have produced their checkpoint videos through the new script with no occasion on which anyone needed to fall back."* **That condition is met**, and met by production runs rather than a constructed test — which is what §A8 intended.

### What this unblocks, and what it does not

| Step | State as of 2026-09-22 | Why |
|---|---|---|
| **Step 1** | **still waits** | Twelve runs are rendering through that path right now (decision 3). |
| **Step 2** | **available now** | Step 0's gate table admits it with runs in flight: monkeypatch-only, nothing under `src/environment/dashboard/` changes (§A11.4). |
| **Step 3** | blocked on **Step 2 only** | Its other precondition, §R30.2, is now met. |
| **Step 4** | **still waits** | Hard stop while any run is live. |

**Step 2 is therefore the one piece of this plan that can be worked today.** Landing it means Step 3 can go as soon as the last run stops, rather than starting cold then.

### CP0.1 cannot be ticked yet

Census at 2026-09-22 00:30 — twelve busy GPUs attribute cleanly to the twelve surviving runs (101:0/1, 103:0/1, 104:0/1, 105:0/1, 106:0/1, 107:1, 108:1). **Node 114's four GPUs were busy and unattributed** at that moment: 100 % utilisation, ~13.7 GB each, and no diary row from 2026-09-14 onward claiming them. Per CP0.1 an unattributable busy GPU is a **stop, not a footnote**, so it was chased rather than noted.

**Resolved: they stopped.** Asked directly, node 114 reports all four GPUs at **0 % utilisation and 4 MiB used**, with no compute applications — against 13,716–14,153 MiB at the census. GPU memory occupancy is reported by the device and does not depend on which PID namespace the query runs in, so the drop to 4 MiB is evidence the work ended, not evidence that a container hid it.

> The first attempt at this proved nothing and is recorded so it is not repeated: `ps` on the PIDs `nvidia-smi` had printed returned an empty list, which looks like "the processes are gone" but is equally "the PIDs are not visible from this shell" — `gpu_status.py` prints `[Not Found]` for **every** PID on **every** node, including runs known to be alive. Device-reported memory was the discriminator; the process list was not.

**CP0.1 is still not ticked, and should not be.** Nothing is attributable now because nothing is busy there — but the gate is a census taken **immediately before Steps 1 and 4** (§Step 0; CP4.1), not one taken days earlier. Whoever runs Step 1 re-runs it then. Node 114 is recorded here only so the next reader does not re-investigate four cards that have already gone quiet. None of this gates **Step 2**.

> **A note on how the two completions were established**, since §A9 and §A10 are about checks that cannot fail. The first reading of these runs called the last checkpoint `9,800,010` and the runs ambiguous. That came from `ls -1 | tail -3`, which sorts **lexicographically**: as text `"9800010"` sorts after `"10000058"`, so the real final checkpoint sat earlier in the listing and was never looked at. `sort -n` and the log's own `Training complete.` line are what settled it. A freed GPU alone never distinguishes *finished* from *died* — two rPPO runs in this project have died mid-training — so the completion marker, not the idle card, is the evidence.

*Recorded by top-level Claude, session `14318db1`.*

---

## Implementation Plan

### Design and sequencing

Four steps, four commits. **The ordering is load-bearing and must not be rearranged.**

```
Step 0  Live-run census                                ← gate; re-run before Steps 1 and 4
   │
   ├──── ⏸ WAIT for the 14 runs                        (decision 3)
   │
Step 1  Move save_jax_video into the dashboard package
   │    gate: CP1.0 determinism probe, then byte-identity (or decoded-frame equality)
   │
Step 2  Replace the audit's controls with breaks of the CURRENT renderer
   │    ★ PRECONDITION OF STEP 3 — includes the load_inputs fix (A11.1) and the
   │      CONTROLS / --controls decision (A11.2). Monkeypatch-only (A11.4).
   │
Step 3  Delete V1 + the April file + rehome the recording contract
   │
Step 4  Rename to render_episode_videos.py + the new output folder
```

**Why Step 2 must precede Step 3, in words so nobody re-orders it.** Step 3 deletes the two files holding every defect the audit uses to prove it detects anything. Run first, the audit does not merely lose coverage — **its controls cannot be expressed**, because `render_capture`'s `v1` branch imports the deleted module and raises. Whoever hit that state would face a red suite with no way to tell "the audit broke" from "its subject was removed", and the cheapest escape would be deleting the controls — the outcome the user rejected. Step 2 first means the audit is already self-proving when its old subjects disappear, and Step 3 changes no verdict.

**Audit coverage at each state:**

| State | `cell_overdraw`, `cell_probe_blind` | the six defect rules | `numeric_in_arena` | Negative controls |
|---|---|---|---|---|
| **Today** | current renderer | **old renderers only** | **April only** | pinned on **V1** frames |
| **After Step 1** | unchanged | unchanged | unchanged | unchanged — Step 1 does not touch the audit |
| **After Step 2** | current renderer | **current renderer** | **current renderer** | pinned (at zero) on **current-renderer** frames |
| **After Step 3** | current renderer | current renderer | current renderer | unchanged — deletion changes no verdict |
| **⚠ Step 3 before Step 2** | current renderer | **none — and inexpressible** (`v1` arm raises at import; `load_inputs` raises too) | **none** | **none** |

---

### Step 0 — Live-run census (gate)

```bash
/home/vncuser/miniconda3/envs/grid_world_pain/bin/python scripts/lab/gpu_status.py
```

Cross-check busy GPUs against the **Training runs** tables in today's and yesterday's diary.

| Step | Runs in flight? | Rule |
|---|---|---|
| Step 1 | **yes** | **WAIT** (decision 3). |
| Step 2 | any | **Proceed** — monkeypatch-only, nothing on the render path (A11.4). |
| Step 3 | any | Proceed once §R30.2 is met **and Step 2 has landed**. |
| Step 4 | **yes** | **STOP and ask.** |

- [ ] **CP0.1** — census pasted with a timestamp, every busy GPU attributed. **Node 113:0 must be identified**; an unattributable busy GPU is a **stop**, not a footnote.

**Rollback:** none needed.

---

### Step 1 — Break the new renderer's dependency on the old one

**Precondition: the fourteen runs have finished.**

- [ ] **CP1.0 — settle MP4 determinism BEFORE relying on it (A11.5).** Render fixture `M4` twice with the tree unchanged; `sha256sum` both.
  - **Equal** → byte-identity is a valid gate; CP1.4 stands as written.
  - **Unequal** → byte-identity is void. Fall back to: (a) feed a **fixed in-memory frame list** through old and new `save_jax_video` **in-process** and compare output bytes, and (b) assert **decoded-frame equality** (every decoded frame array equal) between a before and after render. Record which gate is in force and the measured evidence.

##### `src/environment/dashboard/video.py` — NEW FILE

Copy `renderer.py:1094-1132` **verbatim**. Docstring must state: what it does in plain words; that it is a **copy** taken at commit `<sha>`; that the **streaming** `get_writer`/`append_data` form is required because callers pass generators (`render_recordings_v2.py:237`, `:491`); and that `grid_world.py:701`'s `imageio.mimsave` variant is **not** the source.

> **Docstring constraint (A11.9).** `test_no_file_in_the_package_names_the_frozen_renderer_at_all` skips lines that start with `#` **or contain a quote character**, then flags any line containing both `renderer` and `import`. **"imported" contains "import"** — so a line like *copied from the old renderer rather than imported* would fail the test. Keep the two words on separate lines, or include a quoted token (e.g. ``renderer.py``) on any line carrying both.

##### `src/environment/dashboard/__init__.py`

Add `from .video import save_jax_video` and `"save_jax_video"` to `__all__`. **Not** via the lazy `_LAZY` / `__getattr__` mechanism — that exists for the Matplotlib-importing names; `video.py` imports nothing at module scope.

##### `scripts/eval/render_recordings_v2.py` (lines 223, 474)

```python
# BEFORE (:223):
        from src.environment.renderer import save_jax_video
# AFTER:
        from src.environment.dashboard import save_jax_video
```

```python
# BEFORE (:474):
        from src.environment.renderer import save_jax_video  # read-only, frozen
# AFTER:
        from src.environment.dashboard import save_jax_video
```

The `# read-only, frozen` comment goes with the change. **Leave `:277`** — it retires in Step 3 with its subject. Update the module docstring's "never called by training" paragraph.

##### `tests/env/test_dashboard_video.py` — NEW FILE

Fails before, passes after: importable from the package; signature matches `renderer.py`'s; **a generator input produces a readable MP4 with the expected frame count** — the property the duplicate would break, asserted rather than assumed.

##### `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` (§3 row 191)

Record that the production import now resolves inside `src/environment/dashboard/`; `--benchmark` is the sole surviving V1 import until Step 3. **Contract — same commit.**

**Checkpoints:**
- [ ] **CP1.1** — `dashboard.save_jax_video` resolves.
- [ ] **CP1.2** — existing `test_dashboard_v1_imports.py` passes **unmodified** (both the subprocess Matplotlib check and the static naming check). Run isolated (`-p no:randomly`).
- [ ] **CP1.3** — `test_dashboard_video.py` passes, generator case included.
- [ ] **CP1.4 — THE GATE**, in whichever form CP1.0 established: byte-identical MP4s, or in-process + decoded-frame equality. On fixture `M4` **and** one real checkpoint directory. A mismatch means the relocation was not pure — **stop**.
- [ ] **CP1.5 — a human looks at a frame.** Frame 0 and a mid-episode frame to PNG, and **look**. The machine gate cannot fire if the *pre*-change render was already wrong.
- [ ] **CP1.6** — `grep -n "environment.renderer" scripts/eval/render_recordings_v2.py` returns **exactly one** line: `:277`.
- [ ] **CP1.7** — full suite green, once, at the end.

**Rollback:** `git revert`. Because the child re-reads the script per dispatch, a revert takes effect at the **next checkpoint** with no trainer restart.

---

### Step 2 — Replace the audit's controls with breaks of the current renderer ★

**Precondition of Step 3.** Safe under live runs **only because it is monkeypatch-only** (A11.4).

**Scope, which is wider than Revision 2 had it.** Three things must land together, because each blocks the others' verification:

**(a) The `load_inputs` V1 reach-through (A11.1, moved from Step 3).** `render_layout_audit.py:418` imports `thermal_color_limits` from V1 on every call. Push it into `render_capture`'s `v1` branch — its only consumer — or drop the field. **Without this, CP2.7 cannot pass**, and the replacement controls cannot even load their inputs.

**(b) The `CONTROLS` dict and `--controls` (A11.2).** The entries are rewritten, not optionally: `run_controls` renders `ctl["renderer"]` for all seven. Decide `--controls`' fate as a CLI mode — it cannot survive Step 3, since the audit may not import the dashboard and so cannot render a current frame itself; the natural home for the replacements is the test module, which may import both. **Update the USAGE docstring and `SCRIPTS_DEPENDENCY_MAP.md` row 190 in the same commit** — the maintenance contract fires on this step.

**(c) The replacement controls themselves.**

**What they must establish:**

1. **Each of the six rules gets a deliberate break of the current renderer that makes the audit fire** — `text_over_text`, `out_of_card`, `text_over_border`, `panel_absent`, `observed_caption`, **`numeric_in_arena`** (A10: its only proof today is the April file).
2. **Each firing is for the right reason** — the named rule, on named participants, mirroring `_control_matches`'s `a_contains` / `b_contains` discipline. A control firing via another rule **counts as not firing**.
3. **The negative direction for every one** — the **unbroken** frame must not fire that rule. A mutation that fires on everything proves nothing.
4. **The negative-control set is rebuilt on current-renderer frames, pinned at ZERO per defect rule** (A11.7) — not the old non-zero counts, because the dashboard is live and carries an open height-twin defect. **Measure first**: run the full audit on M4/M1 through the substitution path and record what it actually reports, since no test asserts the current renderer scores clean on the non-`cell_` rules today. A non-zero finding is a **stop and report**, not a number to pin.
5. **`panel_absent` needs the renderer's own guard handled** (A11.8): `check_completeness` raises in `EpisodeRenderer.__init__` before drawing. Two monkeypatches — suppress the guard, drop the panel — **plus a paired assertion that the unpatched guard does raise**, so the bypass does not silently retire a real safeguard.
6. **Coverage is enforced, not asserted** (A11.6): add a canonical rule list to the audit (it has none — rules appear in three emission shapes, and a hand grep of two of them misses `out_of_card`), then **parametrise the coverage test over it** so a new rule with no control fails rather than passing unnoticed. Rules deliberately out of scope (e.g. `legibility`, `clipped`) are named with a reason rather than omitted.
7. **The successor to `test_collision_controls_go_quiet_when_the_measurement_is_broken`** — raise `MIN_OVERLAP_PX` out of reach; the pixel rules go quiet while `panel_absent` survives. This proves the controls are decided by measured pixels, not a constant.

**How.** Reuse `tests/env/test_dashboard_frames.py:303-311`: build a frame with `EpisodeRenderer`, set `audit.render_capture = lambda _r, _fi: (frame, r.fig)`, call `audit.audit_frame(fi, "dashboard", ...)`, restore. **No new `--renderer` arm**, so §D5.2's no-import rule is preserved. **Every break is a test-process monkeypatch; no line under `src/environment/dashboard/` changes** (A11.4) — if that proves impossible for any rule, Step 2 inherits Step 1's wait gate rather than quietly editing the package.

**Files:** `scripts/eval/render_layout_audit.py` (the `load_inputs` fix, the rule-list constant, `CONTROLS`, USAGE), `tests/env/test_render_audit_controls.py`, `tests/env/test_dashboard_frames.py` (may host the frame-mutation harness), `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` row 190.

**Checkpoints:**
- [ ] **CP2.0 — measure before pinning (A11.7).** Full audit on M4 and M1 through the substitution path; record every finding per rule. Any non-`cell_` finding on a correct current frame is a **stop and report**.
- [ ] **CP2.1 — coverage is derived and parametrised (A11.6)**, not a hand-written table. A rule with no control and no stated exemption **fails**.
- [ ] **CP2.2** — every mutation fires **via its named rule**, on named participants.
- [ ] **CP2.3** — every unbroken counterpart produces **zero** findings for that rule.
- [ ] **CP2.4** — rebuilt pins are **zero** per defect rule; `SILENT_RULES` asserted silent.
- [ ] **CP2.5** — the measurement-is-a-measurement test passes on the current renderer.
- [ ] **CP2.6 — a human looks at every mutated frame.** One PNG per mutation. A mutation that does not visibly show the defect it claims is not a control.
- [ ] **CP2.7 — prove independence from the old renderers.** **No `git stash` (A11.3).** Exactly:
  ```bash
  SCRATCH=/tmp/claude-1000/.../scratchpad
  mv src/environment/renderer.py src/environment/renderer_v2.py "$SCRATCH"/
  # run the full audit-control suite here
  git checkout -- src/environment/renderer.py src/environment/renderer_v2.py
  git status --short src/environment/     # MUST be empty
  ```
  The suite must pass with both files absent. Restore with `git checkout --`, then **assert `git status --short src/environment/` is clean**. Never `git rm`, never `git stash`.
- [ ] **CP2.8** — the control suite passes with **0 skipped** (today: 71 passed / 0 skipped). A replacement that skips on missing fixtures would hide the exact regression this step prevents.

**Rollback:** `git revert`. Nothing on the render or training path is touched.

---

### Step 3 — Delete V1 and the April file

**Preconditions:** Step 2 landed and **CP2.7 passed**; §R30.2 satisfied (a written tally naming each run and the absence of any hand-render); the A5 sweep re-run and reconciled.

| Dependent | Disposition |
|---|---|
| `render_recordings_v2.py:277` + `--benchmark` flags | **remove** — subject gone |
| `scripts/eval/render_recordings.py` | **delete with V1** |
| `scripts/eval/benchmark_render.py` | **delete or repoint** |
| `scripts/eval/render_layout_audit.py` | **remove the `v1` and `v2` render arms**; keep the audit and the `dashboard` substitution path (`load_inputs` already fixed in Step 2) |
| `scripts/eval/make_render_fixture_recordings.py` | **repoint** |
| `scripts/dreamer/visualize_dream.py` | **repoint** |
| `scripts/media/record_env_demo.py` | **repoint** |
| `save_snapshot.py` (repo root) | **repoint or delete** |
| `src/utils/eval_recording.py:34` | **rehome the contract** (A6) |
| `tests/env/test_thermal_rendering.py` | **repoint or retire the V1 cases** |
| `tests/algorithms/dreamer_srl/test_eval_recording.py` | **repoint** |
| `tests/env/test_dashboard_v1_imports.py` | **rewrite; keep the Matplotlib-free assertion** |
| `docs/.../render_current_frames.py` | **archive with the plan folder** |
| **`test_c4.py` (repo root)** | **delete or repoint — April-file dependent** (A5 item 14) |
| `src/environment/renderer_v2.py` (April) | **delete** — released by Step 2 |

**Also:** `docs/environment/12_renderer.md` (a rewrite — it documents V1 throughout and cites `save_jax_video` at `renderer.py:734`, actually `:1094`); `SCRIPTS_DEPENDENCY_MAP.md` rows 17, 88, 89, 123, 181, 188–191, 250, 270 (**contract**); [[EVAL_RENDERER_SWITCHOVER]] Rollback (b); [[RENDERER_LAYOUT_REDESIGN]] §R30.

**Checkpoints:**
- [ ] **CP3.1** — the §R30.2 tally names specific runs.
- [ ] **CP3.2** — no surviving V1/April **imports**. Scope the grep to import statements — a bare text search hits **prose** at `sensor.py:689` and `dashboard/__init__.py:32` (A11.9), which are comments and must not be "fixed".
- [ ] **CP3.3 — the audit still proves itself.** Full control suite green after deletion, **0 skipped**, coverage identical to post-Step-2. Any rule that lost its proof means Step 2 was incomplete.
- [ ] **CP3.4 — a rendered frame.** Re-render `M4` and one real checkpoint and **look**. V1 is not on this path, so this catches anything reached for implicitly (e.g. the process-global icon cache V1 warmed — a recorded bug).
- [ ] **CP3.5** — `eval_recording.py`'s docstring names an owner that exists.
- [ ] **CP3.6** — the unrebuildable-fixtures bug row re-checked; if still open, §R30.5's insurance argument is reported **before** deleting.
- [ ] **CP3.7** — full suite green.

**Rollback:** `git revert`, or `git checkout <sha> -- <paths>`. Since this is a deletion, **the pre-deletion SHA is recorded in the Implementation Report**.

---

### Step 4 — Rename to `render_episode_videos.py`

**Precondition: no runs in flight** (census re-run immediately before), or explicit user acceptance.

- `git mv scripts/eval/render_recordings_v2.py scripts/eval/render_episode_videos.py` (decision 7).
- The **three** `src/` bindings: `async_render.py:56`, `evaluation_core.py:382`, `dreamer_srl/eval.py:552`; plus the cosmetic hint at `evaluation_core.py:415`.
- Tests: `tests/scripts/test_render_recordings_v2.py` (renamed), `tests/training/test_async_render_dispatch.py`, `tests/algorithms/dreamer_srl/test_render_upload.py`.
- **Output folder** (decision 4): a new neutral name — `episode_videos/` pairs with the script — with the **26 existing `videos_v2/` directories left exactly as they are**. The 38 `.py` occurrences change; **nothing on disk is moved, renamed or deleted.** The existing `--output-dir` flag covers any transition without new code.
- Config **comments**: `configs/train/default.yaml:64,67`, `configs/evaluation/default.yaml:8`. Comments, not keys — **no schema change, no new mandatory key**. `CONFIG_GUIDE.md:644` names the script and must be updated.
- `.claude/skills/trajectory-story/SKILL.md:60`.
- `SCRIPTS_DEPENDENCY_MAP.md` — **contract fires hardest here**: §1b rows 72–74, the rule sentence at 79, §2 121–123, §3 191, §4 250, §5 270.

**Explicitly NOT rewritten:** the 110 `.md` occurrences that are **historical record** — diary and wiki entries, `train_command-agent.sh`'s comment block at 3766–3780, prior plan revisions. Rewriting history to match a later name makes the record lie about what was run.

**Checkpoints:**
- [ ] **CP4.1** — census re-run **immediately** before, pasted in.
- [ ] **CP4.2** — no stale script references outside preserved history.
- [ ] **CP4.3 — a real dispatch, not a mocked one.** Produce a checkpoint video and confirm its `render_<pct>.log` contains **`frames verified`** — a phrase only this script emits (lines 444/489), so it is direct evidence of *which* renderer ran. The tests mock `_RENDER_SCRIPT`; only a real dispatch proves the binding.
- [ ] **CP4.4 — look at the video.**
- [ ] **CP4.5** — the 26 `videos_v2/` directories **untouched and present**; no `results/` directory moved or deleted.
- [ ] **CP4.6** — full suite green.

**Rollback:** rename back (`git revert`). A trainer live across the rename recovers at its next dispatch once the old filename exists again — the path it holds is a string. Videos skipped in the window are re-renderable offline from their `.rec.gz`.

---

## Obligations to other documents (recorded, not executed here)

1. **[[EVAL_RENDERER_SWITCHOVER]] — Rollback route (b), owed by Step 3.** It names hand-rendering with `render_recordings.py` as the recovery path, recorded as *verified rather than assumed*. Deleting V1 deletes that route. Step 3 must repoint it or state plainly that hand-rendering is now single-renderer. §R30.4 records the obligation; this plan discharges it.
2. **[[RENDERER_LAYOUT_REDESIGN]] §R30 — owed by Steps 1 and 3.** §R30.3 loses its first row at Step 1 and is superseded at Step 3. **It also needs two corrections: six dependents listed against thirteen found (plus a fourteenth for the April file), and §R30.1's "no callers at all" for the April file — which has two live positive controls and the sole `numeric_in_arena` proof.**
3. **`docs/environment/12_renderer.md`** — owed by Step 3; a rewrite, not a patch.

## Follow-ups (named, deliberately out of scope)

- **`grid_world.py`'s dead render copies** — `save_jax_video` at `:701` (zero callers) and the older `render_jax_state` at `:344`. Q8 of [[RENDERER_LAYOUT_REDESIGN]] stands over them. **A separate change after this plan lands** (decision 8); folding a dead-code deletion into a renderer retirement would attribute any regression to the wrong change.

---

## Checkpoints (roll-up)

- [ ] **CP0.1** — census pasted; every busy GPU attributed, including node 113:0
- [ ] **CP1.0** — MP4 determinism settled; the gate form recorded
- [ ] **CP1.1–CP1.3** — import resolves; V1-imports test green **unmodified**; generator case passes
- [ ] **CP1.4** — the established gate passes on fixture M4 *and* a real recording
- [ ] **CP1.5** — a human looked at two frames
- [ ] **CP1.6** — exactly one `environment.renderer` import left, at `:277`
- [ ] **CP1.7** — full suite green
- [ ] **CP2.0** — current renderer's findings on M4/M1 measured before any pin
- [ ] **CP2.1** — coverage derived from the audit and parametrised
- [ ] **CP2.2–CP2.3** — each mutation fires via its named rule; each correct counterpart silent
- [ ] **CP2.4** — pins are **zero** per defect rule
- [ ] **CP2.5** — measurement-is-a-measurement test passes on the current renderer
- [ ] **CP2.6** — a human looked at every mutated frame
- [ ] **CP2.7** — controls pass with both old renderers **`mv`'d aside**, restored by `git checkout --`, `git status` clean
- [ ] **CP2.8** — control suite green, **0 skipped**
- [ ] **CP3.1–CP3.2** — §R30.2 tally written; no surviving imports (grep scoped to imports, not prose)
- [ ] **CP3.3** — audit still self-proving after deletion, coverage unchanged
- [ ] **CP3.4** — a human looked at a post-deletion frame
- [ ] **CP3.5** — recording-format contract names an owner that exists
- [ ] **CP3.6** — fixture-worlds bug row re-checked and reported
- [ ] **CP3.7** — full suite green
- [ ] **CP4.1–CP4.2** — census immediately before; no stale references
- [ ] **CP4.3–CP4.4** — a **real** dispatch produced a video; a human opened it
- [ ] **CP4.5** — the 26 existing directories untouched and present
- [ ] **CP4.6** — full suite green

---

## Implementation Report

> **Implemented by**: _(not started)_
> **Date**: —

---

## Verification Report

> **Verified by**: _(not started)_
> **Date**: —

| File | Change | Status | Notes |
|------|--------|:------:|-------|
| | | | |

**Conclusion**: —

---

## Feedback from plan-reviewer

> **Reviewed at**: commit `78141d20` (Revision 2) · 2026-09-21 · **Verdict: SOUND WITH CONCERNS** (no Critical finding).
> Full report: [`docs/reviews/plan_renderer_v1_retirement.md`](../../../reviews/plan_renderer_v1_retirement.md).

The ordering is right and every claim in A10 re-verified. What is short is **Step 2's own scope**: its exit gate (CP2.7, "controls pass with both old renderers moved aside") cannot pass as written, because (1) the audit's `load_inputs` imports `thermal_color_limits` from V1 at `render_layout_audit.py:418` on every call — including on the substitution path Step 2 reuses — and the plan schedules that edit for Step 3; and (2) `run_controls` iterates `CONTROLS`, whose seven entries still render `"v1"`/`"v2"`, so the `CONTROLS` change the plan marks "only if" is mandatory, and the `--controls` CLI cannot survive Step 3 at all (the audit may not import the dashboard, so it cannot render a current frame itself) — which also fires the dependency-map contract on Step 2. Three more Moderates: `git stash` cannot move an unmodified tracked file aside and would sweep parallel sessions' uncommitted edits — specify `mv` out + `git checkout --` back; Step 2's "safe under live runs" is only true if the deliberate breaks are test-process monkeypatches and nothing under `src/environment/dashboard/` changes — say so or give Step 2 the Step 1 wait gate; and CP1.4's byte-identity assumes reproducible MP4 encoding, which [[EVAL_RENDERER_SWITCHOVER]] §Rollback (b)'s own 956,266 B vs 956,367 B record contradicts — establish twice-render determinism before Step 1 or fall back to decoded-frame equality. Two Opens decide Step 2's shape: nobody has yet looked at the current renderer's non-cell findings on M4/M1 (the only full-audit test asserts `cell_*` only), and pinning **non-zero** exact counts on a live renderer will break on every legitimate change — the stable pin is zero on every defect rule. Lows: `test_c4.py` (repo root) is a fourteenth dependent of the April file; CP3.2's grep will hit prose (`sensor.py:689`, `dashboard/__init__.py:32`); and `video.py`'s required docstring can trip `test_no_file_in_the_package_names_the_frozen_renderer_at_all` if one line carries both "renderer" and "import" without a quote character.

*— plan-reviewer, 2026-09-21*

> **Response from senior-developer, 2026-09-21 (Revision 3).** All thirteen findings applied; each re-verified against the code rather than accepted on report. The two blocking ones are now **§A11.1** (the `load_inputs` reach-through moves into Step 2 as scope item (a)) and **§A11.2** (`CONTROLS` is mandatory, `--controls`' fate and dependency-map row 190 land in the same commit, so the maintenance contract fires on Step 2). The `git stash` instruction was **mine** and is replaced with `mv` out / `git checkout --` back plus a clean-tree assertion (**§A11.3**); no `git stash` appears anywhere in this plan. Step 2 is now explicitly monkeypatch-only (**§A11.4**), CP1.0 settles MP4 determinism before CP1.4 relies on it (**§A11.5**), coverage is derived and parametrised (**§A11.6**) — and while checking that, a hand grep of two of the audit's three rule-emission shapes **missed `out_of_card`**, which is the argument for deriving it; pins are zero per defect rule and measured first (**§A11.7**); `panel_absent` gets two monkeypatches plus a paired assertion the unpatched guard raises (**§A11.8**); and the lows are applied verbatim (**§A11.9**), including the `"imported" contains "import"` trap in the new docstring. One addition of my own: **§A11.10** records that the `M4`/`M1` fixtures Step 2 calibrates against are gitignored and unregenerable, so a `results/` loss would take the calibration with it.

*— senior-developer, 2026-09-21*

> **Second pass from plan-reviewer, at Revision 3 (`bac725b7`), 2026-09-21 — Verdict: SOUND. Nothing blocks implementation.** Step 2's gate is reachable (the V1 reach-through, the mandatory `CONTROLS` rewrite and `--controls`' retirement are all in scope; no `src/` module besides the April file imports V1, so the `mv`-aside suite can run), Step 2 touches nothing a render child imports, and CP2.7's restore cannot reach another session's work. **CP1.0 is settled by measurement, not left to the developer:** two renders of fixture `M4` through the unchanged script are byte-identical on this container, so byte-identity is a valid CP1.4 gate provided the before/after pair is rendered on the same machine. One Moderate, handed to `developer` as an instruction rather than a plan revision: **the audit emits 16 rules, not 14** — `cell_opacity` (`:1329`) and `cell_foreign_axes` (`:1336`) are missing from §A11.6, both in the multi-line-call shape a grep misses — so the "canonical list" must be enforced at emission (`Finding.__post_init__` rejecting an unregistered rule) rather than transcribed. Lows: `check_completeness` has a second call site at `panels.py:713`, so the `panel_absent` bypass needs both bindings patched (or, simpler, an inkless title painter with the guard left intact); narrow CP2.7's clean-tree assertion to the two paths; name the `:638` all-True-ink test's successor; only `M4` is unregenerable (`M1` rebuilds) and its 31 KB is worth one `cp -a` before Step 2; say "retire `--controls`" rather than "decide". Details in [`plan_renderer_v1_retirement`](../../../reviews/plan_renderer_v1_retirement.md) §Second pass.

*— plan-reviewer, second pass, 2026-09-21*
