---
title: "Retiring the old episode-video renderer, and dropping \"v2\" from the new one's name"
topic: refactors
status: active
created: 2026-09-21
last_updated: 2026-09-21
aliases: [renderer_v1_retirement]
---

# Retiring the old episode-video renderer, and dropping "v2" from the new one's name

> **Status**: PLANNED — nothing implemented. Four steps, two user decisions still open (§Questions). Awaiting `plan-reviewer`.
> **Opened**: 2026-09-21 · **Revised**: 2026-09-21 (Revision 2 — adds Step 2, the audit-control replacement, and records four user decisions)
> **Related**: [[RENDERER_LAYOUT_REDESIGN]] §R30 (the retirement condition this plan executes) · [[EVAL_RENDERER_SWITCHOVER]] (the 2026-09-17 switch this cleans up after; **this plan must edit its Rollback section — see §Obligations**) · [[ASYNC_CHECKPOINT_VIDEO_RENDER]] (the dispatch mechanism that makes timing load-bearing) · [`SCRIPTS_DEPENDENCY_MAP`](../../../environment/SCRIPTS_DEPENDENCY_MAP.md) (maintenance contract fires on Steps 1, 3 and 4)

---

## Context

The project draws a video of each evaluation episode — a dashboard showing the agent on its grid alongside its hunger, injury and sensory readouts. Until four days ago those videos came from the **original renderer** (`src/environment/renderer.py`, written early in the project). On 2026-09-17 a **replacement renderer** took over: a new package (`src/environment/dashboard/`) driven by a new script whose filename ends in `_v2`. The user has since watched checkpoint videos arrive correctly from the new path and asked for the cleanup.

They asked for three things, in their words: *"I don't want to make the current renderer to be dependent any v1 script. Let's make archiving v1 plan. And as we will not distinguish them through version, new version no need to use v2 as the name."* In plain terms — (1) stop the new renderer from borrowing code from the old one, (2) retire the old one, (3) rename the new one so it no longer carries a version number, because there is no longer a second renderer to distinguish it from. They also said: *"Since the trainings are still ongoing, let's make plan and feedback first."*

**That last sentence is the governing constraint, and it is correct.** A live-cluster census found **fourteen training runs in flight**, launched at 11:52 today across seven lab machines, each budgeted for ten million episodes. Every one of them writes a video at each checkpoint by launching the render script *by filename*, and each memorised that filename when it started. **The user's decision is to wait for those runs before touching the render path at all.**

**A fourth piece was discovered after the first draft, and it reorders everything.** The project has a *pixel audit* — an instrument that inspects a rendered frame and reports defects like text printed on top of other text, or a panel silently dropped. An instrument like that has to prove it actually works, and this one proves it with seven known defects it must catch. **Every one of those seven defects lives in an old renderer.** Five are in the renderer this plan retires; two are in a dormant April file. So the audit's entire self-proof depends on old renderers being kept alive *in order to stay broken* — and deleting them destroys the proof that the audit can detect anything at all.

**The user's decision: replace all seven with deliberate breaks of the current renderer**, so no old renderer needs to exist for the audit to prove itself — and fold that work into this plan, because archiving the old renderer is what breaks them. **This makes the replacement a precondition of the archival, not a follow-up.** The order is now: break the borrowed code → replace the audit's proofs → delete the old renderer → rename the new one.

**Two decisions remain the user's** (§Questions): what the script is renamed to, and whether a dead duplicate function elsewhere in the codebase is removed as a separate change.

---

## Analysis

### A1. The live-cluster census — the first checkpoint, run before anything else

`scripts/lab/gpu_status.py` and today's diary agree, which is the cross-check that matters (the diary records intent, the GPUs record reality):

| Node | GPUs busy | Utilisation | Attributed to |
|---|---|---|---|
| 101, 103, 104, 105 | 0 and 1 (RTX 2080 Ti) | 89–95 % | 8 of the 14 runs in today's diary, launched 11:52 |
| 106, 107, 108 | 0 and 1 (RTX 3090) | 80–100 % | the remaining 6 of those 14 runs |
| 113 | GPU 0 only (RTX 4090) | 40 %, 5061 MiB | **unattributed** — no diary row today |
| 102, 109, 110, 111, 112, 114, 113:1 | — | idle | free |

The fourteen attributed runs are the `rppo_basicq2_lvl00..lvl06` × {unmodulated, neuromodulated} wave recorded in [`docs/diary/2026-09-21.md`](../../../diary/2026-09-21.md), design doc [`BASIC_LEVELS_Q2_DEFAULT`](../../../experiments/active/basic_levels_q2_default/BASIC_LEVELS_Q2_DEFAULT.md), seed 42, **10 M episodes each**. At that budget they will be running for days, not hours.

**Node 113's GPU 0 is busy and unattributed.** It carries a 5 GB process at 40 % utilisation with no diary row. This does not change the plan's conclusions — the fourteen attributed runs already settle it — but it should be identified before anyone treats that node as free.

**Verdict: runs are in flight, and will be for days.** Per the user's decision, Step 1 waits for them.

### A2. What the render dispatch re-reads, and when — broader than "the rename"

`src/utils/async_render.py:56` binds the script **path** into a module constant at import time, and `dispatch_render()` later runs `subprocess.Popen([sys.executable, _RENDER_SCRIPT, ...])`. The dependency map states the consequence: *"The script path is bound at IMPORT time, so an in-flight trainer keeps invoking whichever renderer it started with."*

**The important half is the half nobody says out loud.** The *path* is frozen in the trainer; the *file at that path* is not. The child is a brand-new Python process that reads the file — and everything the file imports — from disk at each dispatch:

| What we change | Does a live run see it? | What a mistake costs |
|---|---|---|
| `async_render.py`, `evaluation_core.py`, `dreamer_srl/eval.py` | **No.** Already imported into the running trainer. | nothing, until restart |
| `scripts/eval/render_recordings_v2.py` (**contents**) | **Yes, at the very next checkpoint.** | that checkpoint's video |
| `src/environment/dashboard/**` (**contents**, including `__init__.py`) | **Yes** — the child imports the package fresh. | that checkpoint's video |
| `scripts/eval/render_recordings_v2.py` (**filename**) | **Yes, and permanently** — the trainer's path never updates. | every remaining video of that run |

**Correction to this plan's own first draft.** Revision 1 described Step 1's additive half as having "zero live exposure". That was wrong. Adding `video.py` is inert, but the accompanying line in `dashboard/__init__.py` **executes inside every render child**, because the child imports the package fresh per dispatch. The exposure is small — a broken import would fail loudly and immediately — but it is not zero, and the claim is corrected rather than left standing. The user's decision to wait for the fourteen runs makes this moot in practice; it is recorded so no future reader relies on a false "safe" label.

The first three rows are recoverable: `.rec.gz` recordings are written at every checkpoint regardless, and `async_render.py`'s docstring records that a skipped video is *"offline-recoverable … never a data-loss event."* The fourth row is recoverable in the same offline sense but not self-healing.

### A3. What the new renderer still takes from the old one — and the one place it matters

Three import sites in `scripts/eval/render_recordings_v2.py`, and they are **not equivalent**:

| Line | Imports | Reachable when | Production? |
|---|---|---|---|
| `:223` | `save_jax_video` | per-episode MP4 write | **yes** |
| `:474` | `save_jax_video` | `--concat` consolidated write | **yes** — the training path passes `--concat` |
| `:277` | `render_jax_state`, `thermal_color_limits` | inside `_benchmark()`, only under `--benchmark` | **no** |

`:277` lives in a function whose docstring says *"Time V2 and V1 on the same recordings"* — a **measuring instrument whose subject is the old renderer**. It does not need porting; it retires with its subject. Treating all three as one problem would produce a pointless port of a comparison with nothing left to compare.

So the whole production coupling is **one function**: `save_jax_video`, at `src/environment/renderer.py:1094`. `src/environment/dashboard/` defines nothing like it.

### A4. The duplicate in `grid_world.py` is not a drop-in replacement — measured

A second `save_jax_video` sits at `src/environment/grid_world.py:701`. It is **not** the same function. The bodies diverge in one load-bearing line:

```python
# src/environment/renderer.py:1094 — streaming
with imageio.get_writer(output_path, fps=fps) as writer:
    for frame in frames:
        writer.append_data(frame)

# src/environment/grid_world.py:701 — materialising
imageio.mimsave(output_path, frames, fps=fps)
```

Both production call sites pass **generators**, not lists (`render_recordings_v2.py:237` and `:491`). `imageio.mimsave` consumes its argument as a sequence, so substituting the `grid_world.py` variant would either fail or silently materialise an entire episode's frames in memory — defeating the reason the call sites are generators. **The copy that moves is the `renderer.py` one.**

`grid_world.py::save_jax_video` has **zero callers** repo-wide. It is dead code — but dead code the user has already been asked about and has not approved removing (Q8 of [[RENDERER_LAYOUT_REDESIGN]], reaffirmed in §R30.1). Per the project rule *"don't delete pre-existing dead code unless asked — mention it instead"*, this plan does not touch it. Re-raised as Question 2.

### A5. The dependent inventory is larger than §R30.3 records — a correction

§R30.3 lists **six** dependents, measured *"by grepping `src/`, `scripts/` and `tests/`"*. Re-running that sweep at `HEAD` finds **thirteen**. Three of the seven omitted are tests, so a deletion scoped to §R30.3's table would turn the suite red.

| # | Dependent | Needs from V1 | In §R30.3? |
|---|---|---|---|
| 1 | `scripts/eval/render_recordings_v2.py` `:223 :277 :474` | `save_jax_video`; benchmark-arm helpers | yes |
| 2 | `scripts/eval/render_recordings.py` `:78 :93 :113 :219` | the old script itself | (implied) |
| 3 | `scripts/eval/benchmark_render.py` `:39` | `render_jax_state` — V1 is its subject | yes |
| 4 | `scripts/eval/render_layout_audit.py` `:418 :465` | the V1 arm of the pixel audit | yes |
| 5 | `scripts/eval/make_render_fixture_recordings.py` `:839` | draws fixture frames through V1 | yes |
| 6 | `scripts/dreamer/visualize_dream.py` `:159 :180` | draws imagined rollouts through V1 | yes |
| 7 | `src/utils/eval_recording.py:34` | a **contract**, not an import (A6) | yes |
| 8 | **`save_snapshot.py:14`** (repo root) | `render_jax_state` | **no** |
| 9 | **`scripts/media/record_env_demo.py:14`** | `render_jax_state`, `save_jax_video` | **no** |
| 10 | **`tests/env/test_thermal_rendering.py:47,:310`** | V1 drawing helpers | **no** |
| 11 | **`tests/algorithms/dreamer_srl/test_eval_recording.py:118,:138`** | renders through V1 | **no** |
| 12 | **`tests/env/test_dashboard_v1_imports.py:99,:121`** | asserts *by name* what the dashboard borrows from V1 | **no** |
| 13 | **`docs/.../renderer_layout_redesign/render_current_frames.py:44`** | the redesign's own frame generator | **no** |

Items 8 and 9 are corroborated by [`12_renderer.md`](../../../environment/12_renderer.md) lines 31–33, so the reference doc was right and §R30.3's table is the undercount.

**Item 12 deserves its own sentence.** `test_dashboard_v1_imports.py` pins what the new renderer borrows from the old one, including a subprocess check that a bare `import src.environment.dashboard` loads Matplotlib-free. Step 1 removes the last borrow, so that test's subject partly dissolves — but its **Matplotlib-free assertion must survive**, because that property is about the training path's import cost and has nothing to do with V1.

### A6. Archiving V1 rehomes a contract, not just a file

`src/utils/eval_recording.py:34` carries no import. It carries a sentence:

> *"Exactly the fields `render_jax_state` reads. Keep in lockstep with renderer.py."*

That is the **definition of the recording file format** — every `.rec.gz` this project has written is specified by reference to a function in the old renderer. Delete V1 and the format's definition points at nothing. The same docstring goes on to justify not bumping `RECORDING_FORMAT_VERSION` because *"the branch lives in `renderer.py`"* — a second sentence that also stops being true. Rehoming this is **prose, not code**, and a reader who hits the dangling reference gets no error, just a format with no stated owner.

### A7. The rename surface, measured

| Thing | Count | Where |
|---|---|---|
| `render_recordings_v2` references, all types | **139** | 24 in `.py`, 110 in `.md`, plus 2 configs, 1 shell script, 1 Claude skill |
| `videos_v2` references in `.py` | **38** | 8 files: `async_render.py` (3), `evaluation_core.py` (2), `dreamer_srl/eval.py` (2), `render_recordings_v2.py` (10), four test modules (21) |
| `videos_v2/` directories **on disk** | **26** | under `results/` |
| `videos/` directories on disk (V1's output) | **505** | under `results/` |

**The 505-vs-26 ratio is why `videos/` is not free for reuse**, and it is what the user's Decision 3 turns on (§Decisions).

### A8. The retirement condition is already running — and this plan can destroy its own evidence

§R30.2 states the user's condition: the old renderer retires once *"two or three real training runs have produced their checkpoint videos through the new script with no occasion on which anyone needed to fall back."*

**The fourteen runs from the census are exactly that**, and they are producing those videos now. Step 3 does not need a new experiment; it needs those runs to finish cleanly.

**Which produces a circularity worth naming.** Step 1 edits the code path those runs render through. A fault there means a missing video, someone hand-renders with the old script, and the fallback-free streak Step 3 depends on is broken **by the change whose purpose was to enable Step 3**. Two resolutions exist:

- **Honest (adopted):** any fallback occasion counts, including one we caused. The count resets. That keeps §R30.2 meaning what the user meant.
- **Dishonest (rejected, recorded so nobody re-derives it):** "that one doesn't count, it was our own bug." Self-serving, and it would let the condition be satisfied by a path nobody actually trusted.

The user's decision to **wait for the fourteen runs** dissolves this almost entirely: if Step 1 lands after they finish, it cannot contaminate their evidence.

### A9. Why a green test suite is not the gate here

This project has a recorded incident on exactly this code: a renderer change once passed eighteen new unit tests while breaking the product. A unit test asserts about panel boxes and frame counts; a human looking at a frame notices the picture is wrong. Every step below therefore names **a rendered artefact someone looks at**.

Step 1 additionally gets a gate most renderer changes cannot have: it relocates an **unchanged** function, so its output must be **byte-identical**. Not "looks the same" — the same MP4 bytes. Any accidental behaviour change fails it.

### A10. The pixel audit proves itself with defects in old renderers — the finding that reorders this plan

**What the audit is, in plain words.** `scripts/eval/render_layout_audit.py` inspects a rendered frame and reports defects: text printed over other text, a label lying across a panel border, a label escaping its card, a panel that should be drawn and is not, a value captioned as "observed" that the agent cannot actually sense. An instrument like that is worthless unless it can be shown to *fire* — so it carries seven positive controls, real defects it must catch.

**Every one of the seven is a defect in an old renderer.** Verified at `HEAD` by reading `CONTROLS` (`render_layout_audit.py:1732-1779`), and the control tests genuinely run — I executed `tests/env/test_render_audit_controls.py` myself: **71 passed, 0 skipped, 125 s**.

| Control | Renderer | Rule(s) | The defect |
|---|---|---|---|
| `D1` | **v1** | `text_over_text` | extero-nociception `OBS:` readout overprints the THERMOCEPTION pod title |
| `D2` | **v1** | `out_of_card`, `text_over_text` | `REAL: --` escapes its card into the EXTERO NOCICEPTION title strip |
| `D3` | **v1** | `text_over_border` | `MINIMAP` label lies across the Run Context box border |
| `D10` | **v1** | `observed_caption` | Nutrition/Injury captioned OBS/REAL though the world observes neither |
| `D12` | **v1** | `panel_absent` | Proprioception emitted by the viz adapter and never drawn |
| `D6` | **v2** (dormant April file) | `text_over_text` | COLLISION card title overprints its C/U/R/D/L labels |
| `D8` | **v2** (dormant April file) | `panel_absent` | silently drops the interoceptive-nociception panel |

All seven use cell `M4`, step 0. **Five die with V1; the April file holds the other two.**

**Seven controls, but only five distinct rules.** The per-rule enumeration the replacement must satisfy is smaller than the control count suggests, and stating it prevents two rules being quietly dropped:

| Rule | Proven today by | Renderer it needs |
|---|---|---|
| `text_over_text` | D1, D2, D6 | v1 **and** April |
| `out_of_card` | D2 | v1 |
| `text_over_border` | D3 | v1 |
| `panel_absent` | D8, D12 | v1 **and** April |
| `observed_caption` | D10 | v1 |

**Two casualties beyond the seven, both missed by the original framing.**

1. **`numeric_in_arena` is proven only by the April file.** `test_numeric_in_arena_is_reachable_and_fires` (`:587`) renders `"v2"` with `--arena-axes thermoception` and asserts exactly 5 hits. The audit's own docstring explains why it cannot move to V1: *"V1 draws its arena into an UNLABELLED Axes, so the rule cannot be pointed at V1's arena at all."* So deleting the April file costs a **third** proof, not two.

2. **The negative controls are pinned on V1 frames, and they are the half that matters most.** The audit's docstring is explicit: *"SENSITIVITY IS ONLY HALF OF CALIBRATION. An instrument that flagged EVERYTHING would pass every positive control."* What rules that out is `V1_M4_COUNTS` and `V1_M1_COUNTS` — **exact** per-rule finding counts on two V1 frames — plus `SILENT_RULES` (`clipped`, `out_of_canvas`, `legibility`, `numeric_in_arena`, `fill_over_text`) asserted silent on those same frames. Around seven further tests bind to the `v1_m4` / `v1_m1` fixtures, including `test_v1_m4_absent_panels_are_exactly_proprioception`, `test_v1_m4_out_of_card_flags_only_the_escaped_readout`, and `test_collision_controls_go_quiet_when_the_measurement_is_broken` (which renders `"v1"` to prove the pixel rules are decided by measurement rather than a constant).

**So the real casualty list of deleting V1 and the April file is: 7 positive controls + the `numeric_in_arena` proof + the entire negative-control set.** "Five of seven proofs" understates it.

**Worse: the audit's own code breaks too.** `render_capture`'s `v1` branch does `from src.environment.renderer import render_jax_state` (`:465`). Deleting V1 makes `audit.audit_frame(fi, "v1")` raise — so the controls could not even be *expressed*, let alone pass.

**What is already proven against the current renderer, and what that pattern can and cannot reach.** The existing mutations `M-E`, `M-T`, `M-C@{0.06,0.12,0.25}`, `M-G` (`test_render_audit_controls.py:921-940`) break **today's** code and are the model to follow — but they target only `cell_overdraw` and `cell_probe_blind`. **Nothing currently proves `text_over_text`, `out_of_card`, `text_over_border`, `panel_absent` or `observed_caption` by breaking current code.**

And the existing harness does **not** extend to them. `_arena_figure` (`:722`) builds a **synthetic arena** — `plt.figure`, a `page` Axes, an `arena` Axes, squares composed through `cells.py` painters. It has no cards, no titles, no panel registry, so it structurally cannot express a card-title collision or a dropped panel. **"Add seven entries to `MUTATION_CELLS`" badly understates the work**: the five rules need mutations of a *whole dashboard frame*, which is a different harness.

**The good news, which materially shrinks Step 2.** The audit never needs a new arm. It deliberately has none for the current renderer — `--renderer` accepts only `("v1","v2")` and the else-branch raises, because *"the audit must not import the thing it audits … an instrument that shares code with its subject can agree with it about a frame neither is describing."* Instead, **a caller hands the audit a frame by substituting `render_capture`** — and `tests/env/test_dashboard_frames.py:303-311` **already does exactly this**, running the full audit over a real current-renderer frame (`audit.audit_frame(fi, "dashboard", arena_axes="arena", cell_axes="arena")`, docstring: *"This runs EVERY rule"*). Step 2 reuses an established, exercised pattern rather than inventing one, and §D5.2's no-import rule is preserved untouched.

---

## User decisions recorded (2026-09-21)

| # | Decision | Effect on this plan |
|---|---|---|
| 1 | **Replace all seven controls with deliberate breaks of the current renderer**, chosen over deleting both renderers and accepting fewer proofs, and over keeping the April file until a replacement exists. | Becomes **Step 2**. |
| 2 | **Fold that work into this plan**, since archiving V1 is what breaks five of them. | Step 2 is a **precondition** of Step 3, not a follow-up. |
| 3 | **Wait for the fourteen runs** before touching the render path. | Step 1 is gated on the census going quiet. Dissolves the A8 circularity. |
| 4 | **New output-folder name; the 26 existing `videos_v2/` folders are left as-is.** | Step 4. The 26 become historical; nothing on disk is moved or deleted. |
| 5 | **Delete V1 rather than move it** when the condition is met. | Step 3 is `git rm`; git history is the rollback, per the user's own §R29 ruling. |
| 6 | **The April file stays untouched until Step 2 lands.** The removal agent stopped rather than improvising, and that judgement stands. | It is **not dead code** while `D6`, `D8` and the `numeric_in_arena` proof are live. |

---

## Implementation Plan

### Design and sequencing

Four steps, four commits, in this order. **The ordering is load-bearing and must not be rearranged.**

```
Step 0  Live-run census                                   ← gate; re-run before Steps 1 and 4
   │
   ├──── ⏸ WAIT for the 14 runs to finish        (user decision 3)
   │
Step 1  Move save_jax_video into the dashboard package
   │    gate: byte-identical MP4s
   │
Step 2  Replace the audit's seven controls with breaks of the CURRENT renderer
   │    ★ PRECONDITION OF STEP 3 — not a follow-up
   │
Step 3  Delete V1 + the April file + rehome the recording contract
   │
Step 4  Rename the script and the output folder
```

**Why Step 2 must precede Step 3, stated in words so nobody re-orders it later.** Step 3 deletes the two files that contain every defect the pixel audit uses to prove it can detect anything. If Step 3 runs first, the audit does not merely lose coverage — **its controls cannot even be expressed**, because `render_capture`'s `v1` branch imports the deleted module and raises. Whoever hit that state would face a red suite with no way to distinguish "the audit broke" from "the audit's subject was removed", and the cheapest way out would be deleting the controls, which is exactly the outcome the user rejected. Step 2 first means the audit is already self-proving when its old subjects disappear, and Step 3 becomes a deletion that changes no verdict.

**Audit coverage at each state** — what the instrument can prove about itself, at every point:

| State | `cell_overdraw`, `cell_probe_blind` | `text_over_text`, `out_of_card`, `text_over_border`, `panel_absent`, `observed_caption` | `numeric_in_arena` | Negative controls (the "doesn't flag everything" half) |
|---|---|---|---|---|
| **Today** | current renderer (M-E/M-T/M-C/M-G) | **old renderers only** (D1, D2, D3, D10, D12 on V1; D6, D8 on April) | **April only** | pinned on **V1** frames |
| **After Step 1** | unchanged | unchanged | unchanged | unchanged — Step 1 does not touch the audit |
| **After Step 2** | current renderer | **current renderer** | **current renderer** | pinned on **current-renderer** frames |
| **After Step 3** | current renderer | current renderer | current renderer | current renderer — deletion changes no verdict |
| **⚠ If Step 3 ran before Step 2** | current renderer | **none — and inexpressible**; the `v1` arm raises on import | **none** | **none** |

---

### Step 0 — Live-run census (gate, not a code change)

```bash
/home/vncuser/miniconda3/envs/grid_world_pain/bin/python scripts/lab/gpu_status.py
```

Cross-check busy GPUs against the **Training runs** tables in today's and yesterday's `docs/diary/*.md`. Any busy GPU with no diary row must be identified before proceeding.

| Step | Runs in flight? | Rule |
|---|---|---|
| Step 1 | **yes** | **WAIT** (user decision 3). |
| Step 1 | no | Proceed, byte-identity gated. |
| Step 2 | any | **Proceed.** Touches only the audit and its tests — nothing on the render path. |
| Step 3 | any | Proceed once §R30.2 is satisfied **and Step 2 has landed**. V1 is not on the live path. |
| Step 4 | **yes** | **STOP and ask.** Renaming breaks every in-flight run's video output for the life of that run. |
| Step 4 | no | Proceed. |

- [ ] **CP0.1** — census output pasted with a timestamp, every busy GPU attributed. An unattributable busy GPU is a **stop**, not a footnote.

**Rollback:** none needed.

---

### Step 1 — Break the new renderer's dependency on the old one

**Precondition: the fourteen runs have finished** (user decision 3).

##### `src/environment/dashboard/video.py` — NEW FILE

Copy the body of `src/environment/renderer.py:1094-1132` **verbatim**. Docstring, in the package's established style, must state: what it does in plain words; that it is a **copy** taken at commit `<sha>` because the old module is being deleted; that the **streaming** `get_writer`/`append_data` form is required because callers pass generators (naming `render_recordings_v2.py:237` and `:491`); and that the `imageio.mimsave` variant at `grid_world.py:701` is **not** the source and must not be substituted.

##### `src/environment/dashboard/__init__.py`

Add `from .video import save_jax_video` and `"save_jax_video"` to `__all__`. **Not** through the lazy `_LAZY` / `__getattr__` mechanism — that exists for the two Matplotlib-importing names; `video.py` imports nothing at module scope.

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

The `# read-only, frozen` comment goes with the change — it described a constraint that no longer applies. **Leave `:277` alone**; it retires in Step 3 with its subject (A3). Update the module docstring's "never called by training" paragraph, which describes a state that ended on 2026-09-17.

##### `tests/env/test_dashboard_video.py` — NEW FILE

Fails before, passes after: `save_jax_video` importable from the package; signature matches `renderer.py`'s (reuse the `inspect.signature` idiom); **a generator input produces a readable MP4 with the expected frame count** — the property the `grid_world.py` variant would break, asserted directly rather than assumed.

##### `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` (§3 row, line 191)

Rewrite *"Imports `src/environment/renderer.py::save_jax_video` READ-ONLY"* to record that the production import now resolves inside `src/environment/dashboard/`, `--benchmark` being the sole surviving V1 import until Step 3. **Maintenance contract — same commit.**

**Checkpoints:**
- [ ] **CP1.1** — `import src.environment.dashboard; dashboard.save_jax_video` resolves.
- [ ] **CP1.2** — the **existing** `tests/env/test_dashboard_v1_imports.py` passes **unmodified**: a bare package import still loads no Matplotlib. Run isolated (`-p no:randomly`) — it is a question about a whole process.
- [ ] **CP1.3** — `tests/env/test_dashboard_video.py` passes, generator case included.
- [ ] **CP1.4 — THE GATE: byte-identity.** Render a recording before the change, keep the MP4; render the same recording after; `sha256sum` both. **They must match exactly.** Use fixture `M4` (`results/render_audit/recordings/M4/M4`) **and** one real checkpoint directory. A mismatch means the relocation was not pure — **stop**.
- [ ] **CP1.5 — a human looks at a frame.** Extract frame 0 and a mid-episode frame to PNG and **look**. Byte-identity cannot fire if the *pre*-change render was already wrong.
- [ ] **CP1.6** — `grep -n "environment.renderer" scripts/eval/render_recordings_v2.py` returns **exactly one** line: `:277`.
- [ ] **CP1.7** — full suite green, once, at the end.

**Rollback:** `git revert`. **Unusually good property:** because the render child re-reads the script from disk each dispatch, a revert takes effect at the **next checkpoint** with no trainer restart. (Moot if Step 1 lands while the cluster is quiet, but true regardless.)

---

### Step 2 — Replace the audit's seven controls with breaks of the current renderer ★

**This is the precondition of Step 3.** It touches only the audit's tests and (if needed) a mutation hook — **nothing on the render path** — so it is safe under live runs.

**What it must establish**, stated so "add mutations" cannot understate it:

1. **Each of the five rules gets a deliberate break of the *current* renderer that makes the audit fire** — `text_over_text`, `out_of_card`, `text_over_border`, `panel_absent`, `observed_caption`.
2. **Plus `numeric_in_arena`**, whose only proof today is the April file (A10). Six rules total, not five.
3. **Each firing must be for the right reason** — the specific rule, on the specific participants, mirroring `_control_matches`'s `a_contains` / `b_contains` discipline. A control that fires via a different rule *counts as not firing*; this is already the project's stated standard.
4. **The negative direction for every one of them**: the **unbroken** frame must **not** fire that rule. A mutation that fires on everything proves nothing — the audit's own docstring says so, and `test_cell_overdraw_is_silent_on_every_negative_control` is the pattern.
5. **The negative-control set is rebuilt on current-renderer frames**: per-rule finding counts pinned exactly (the successor to `V1_M4_COUNTS` / `V1_M1_COUNTS`), plus the `SILENT_RULES` list asserted silent. These are what distinguish this instrument from one that flags everything.
6. **Per-rule coverage is enumerated in the test module**, so a reader can see all six covered rather than four with two quietly dropped.
7. **The successor to `test_collision_controls_go_quiet_when_the_measurement_is_broken`** — raise `MIN_OVERLAP_PX` out of reach and confirm the pixel rules stop firing while `panel_absent` survives. This is what proves the controls are decided by measured pixels rather than a constant, and it currently renders `"v1"`.

**How, concretely.** Reuse the established substitution at `tests/env/test_dashboard_frames.py:303-311`: build a frame with `EpisodeRenderer`, set `audit.render_capture = lambda _r, _fi: (frame, r.fig)`, call `audit.audit_frame(fi, "dashboard", ...)`, restore. **No new `--renderer` arm**, so §D5.2's rule that the audit never imports its subject is preserved. The mutations perturb the dashboard renderer's own drawing (e.g. forcing a card title to a colliding position for `text_over_text`; suppressing a registered panel for `panel_absent`) — a **frame-level** harness, distinct from `_arena_figure`'s synthetic arena, which cannot express card or panel defects (A10).

**Files:** `tests/env/test_render_audit_controls.py` (the seven V1/April-bound positive controls and the V1-bound negative set are replaced), `tests/env/test_dashboard_frames.py` (may host the frame-mutation harness), and `scripts/eval/render_layout_audit.py`'s `CONTROLS` dict **only if** the replacements are expressed there rather than in the test module — a design choice for the implementer, to be stated in the Implementation Report either way.

**Checkpoints:**
- [ ] **CP2.1** — a **per-rule coverage table** in the test module: all six rules, each with its breaking mutation and its silent-on-correct counterpart. A rule with no entry is a **fail**, not an omission.
- [ ] **CP2.2** — every mutation fires **via the named rule**, asserted on participants, not merely "some finding appeared".
- [ ] **CP2.3** — every mutation's unbroken counterpart produces **zero** findings for that rule.
- [ ] **CP2.4** — the rebuilt pinned counts are **exact** (not lower bounds) and `SILENT_RULES` is asserted silent on the new calibration frames.
- [ ] **CP2.5** — the measurement-is-really-a-measurement test passes against the current renderer (raise `MIN_OVERLAP_PX`; pixel rules go quiet, `panel_absent` survives).
- [ ] **CP2.6 — a human looks at each mutated frame.** Save one PNG per mutation and **look at them**: the point is that the break is the defect it claims to be, which no assertion can establish. A mutation that does not visibly show the defect is not a control.
- [ ] **CP2.7 — prove independence from the old renderers, which is the whole point of the step.** With V1 and the April file **temporarily moved aside** (`git stash` / a scratch rename, not a deletion), the full audit-control suite still passes. This is the check that Step 3 is safe, and it is deliberately performed *before* anything is deleted.
- [ ] **CP2.8** — `tests/env/test_render_audit_controls.py` passes with **0 skipped** — the current state is 71 passed / 0 skipped, and a replacement that silently skips for missing fixtures would hide exactly the regression this step exists to prevent.

**Rollback:** `git revert`. Nothing on the render or training path is touched, so a revert restores the previous calibration exactly.

---

### Step 3 — Delete V1 and the April file

**Preconditions, checked not assumed:**
1. **Step 2 has landed and CP2.7 passed** — the audit no longer needs an old renderer to prove itself.
2. **§R30.2 is satisfied** — a written tally naming each run, its checkpoints, and the absence of any hand-render. "It's been fine" is not a tally.
3. **The dependent sweep of A5 is re-run** and reconciled: `grep -rn "environment.renderer" --include="*.py" .`

**Scope: the thirteen dependents of A5, plus the April file.** Dispositions:

| Dependent | Disposition |
|---|---|
| `render_recordings_v2.py:277` + `--benchmark` / `--benchmark-frames` | **remove** — its subject is gone |
| `scripts/eval/render_recordings.py` | **delete with V1** (§R30.1: they retire together) |
| `scripts/eval/benchmark_render.py` | **delete or repoint** — V1 was its measurement subject |
| `scripts/eval/render_layout_audit.py` | **remove the `v1` and `v2` arms** of `render_capture`; keep the audit and the `dashboard` substitution path |
| `scripts/eval/make_render_fixture_recordings.py` | **repoint** to the dashboard package |
| `scripts/dreamer/visualize_dream.py` | **repoint** (Phase 5 item 3 of the redesign plan) |
| `scripts/media/record_env_demo.py` | **repoint** |
| `save_snapshot.py` (repo root) | **repoint or delete** |
| `src/utils/eval_recording.py:34` | **rehome the contract** (A6) — restate against `EpisodeRenderer` |
| `tests/env/test_thermal_rendering.py` | **repoint or retire the V1 cases** |
| `tests/algorithms/dreamer_srl/test_eval_recording.py` | **repoint** |
| `tests/env/test_dashboard_v1_imports.py` | **rewrite; keep the Matplotlib-free assertion** (A5) |
| `docs/.../render_current_frames.py` | **archive with the plan folder** |
| `src/environment/renderer_v2.py` (April) | **delete** — released by Step 2 (user decision 6) |

**Also:** `docs/environment/12_renderer.md` (a rewrite, not a line edit — it documents V1 throughout and several citations are already stale: it cites `save_jax_video` at `renderer.py:734`, actually `:1094`); `SCRIPTS_DEPENDENCY_MAP.md` rows 17, 88, 89, 123, 181, 188–191, 250, 270 (**contract — same commit**); [[EVAL_RENDERER_SWITCHOVER]] Rollback route (b) (§Obligations); [[RENDERER_LAYOUT_REDESIGN]] §R30.

**Checkpoints:**
- [ ] **CP3.1** — the §R30.2 tally is written and names specific runs.
- [ ] **CP3.2** — `grep -rn "environment.renderer\|renderer_v2" --include="*.py" .` returns **zero** hits.
- [ ] **CP3.3 — the audit still proves itself.** Full control suite green **after** the deletion, 0 skipped. Coverage must be identical to the post-Step-2 state; any rule that lost its proof means Step 2 was incomplete.
- [ ] **CP3.4 — a rendered frame.** Re-render fixture `M4` and one real checkpoint, and **look at the frames**. V1 should not be on this path at all, so this checks nothing was reached for implicitly (e.g. the process-global icon cache V1 used to warm — a recorded bug in that module).
- [ ] **CP3.5** — `eval_recording.py`'s docstring no longer names `render_jax_state` or `renderer.py`, and states an owner that exists.
- [ ] **CP3.6** — the Known Bugs row *"Five of the eleven render-audit fixture worlds can no longer be built"* is re-checked; if still open, §R30.5's insurance argument is reported to the user **before** deleting.
- [ ] **CP3.7** — full suite green.

**Rollback:** `git revert`, or `git checkout <sha> -- <paths>`. Since this is a **deletion** (user decision 5), **the pre-deletion SHA is recorded in the Implementation Report** rather than left to be found later.

---

### Step 4 — Drop "v2" from the name

**Precondition: Step 0's census shows no runs in flight**, or the user explicitly accepts the cost. This is the one step care cannot make safe.

- `git mv scripts/eval/render_recordings_v2.py scripts/eval/<new-name>.py` (Question 1).
- The **three** `src/` path bindings the dependency map itemises as the mandatory trio: `async_render.py:56`, `evaluation_core.py:382`, `dreamer_srl/eval.py:552`; plus the cosmetic hint at `evaluation_core.py:415`.
- Tests naming the script: `tests/scripts/test_render_recordings_v2.py` (itself renamed), `tests/training/test_async_render_dispatch.py`, `tests/algorithms/dreamer_srl/test_render_upload.py`.
- **Output folder** (user decision 4): a new neutral name, the **26 existing `videos_v2/` directories left exactly as they are**. The 38 `.py` occurrences across eight files change; **nothing on disk is moved, renamed or deleted.** The script's existing `--output-dir` flag means no new code is needed for a transition.
- Config **comments** naming the path: `configs/train/default.yaml:64,67`, `configs/evaluation/default.yaml:8`. These are comments, not keys — **no schema change, no new mandatory key**, so the config guide's schema-change clause does not fire. Its line 644 does name the script and must be updated.
- `.claude/skills/trajectory-story/SKILL.md:60`.
- `SCRIPTS_DEPENDENCY_MAP.md` — **the contract fires hardest here** (a `scripts/` file renamed + three `src/` callers changed): §1b rows 72–74, the rule sentence at 79, §2 121–123, §3 191, §4 250, §5 270.

**Explicitly NOT rewritten:** the 110 `.md` occurrences that are **historical record** — diary entries, wiki entries, `train_command-agent.sh`'s comment block at 3766–3780 (a dated account of the 2026-09-17 verification), and prior revisions of the redesign plan. Rewriting history to match a later name makes the record lie about what was run.

**Checkpoints:**
- [ ] **CP4.1** — census re-run **immediately** before the rename and pasted in.
- [ ] **CP4.2** — `grep -rn "render_recordings_v2" --include="*.py" --include="*.yaml" --include="*.sh" .` returns zero hits outside preserved historical comments.
- [ ] **CP4.3 — a real dispatch, not a mocked one.** Run far enough to produce a checkpoint video and confirm its `render_<pct>.log` contains **`frames verified`** — a phrase that exists only in this script (lines 444/489), so it is direct evidence of *which* renderer ran rather than an inference from the output path. The tests mock `_RENDER_SCRIPT`; only a real dispatch proves the binding.
- [ ] **CP4.4 — look at the video** the dispatch produced.
- [ ] **CP4.5** — the 26 pre-existing `videos_v2/` directories are **untouched and present**. No `results/` directory is deleted or moved.
- [ ] **CP4.6** — full suite green.

**Rollback:** rename the file back (`git revert`). A trainer live across the rename recovers at its next dispatch once the old filename exists again — the path it holds is a string, and it resolves as soon as the file is there. Videos skipped during the window are re-renderable offline from their `.rec.gz`.

---

## Obligations to other documents (recorded, deliberately not executed here)

This plan **does not edit** either document below; each edit belongs to the step that makes it true.

1. **[[EVAL_RENDERER_SWITCHOVER]] — Rollback route (b), owed by Step 3.** It names hand-rendering with `scripts/eval/render_recordings.py` as the recovery path for a run with missing videos, recorded as *verified rather than assumed* (exit 0, output matching to within 0.01 %). Deleting V1 deletes that route. Step 3 must repoint it or state plainly that hand-rendering is now single-renderer and what that costs. §R30.4 records the obligation; this plan discharges it.
2. **[[RENDERER_LAYOUT_REDESIGN]] §R30 — owed by Steps 1 and 3.** §R30.3's table loses its first row at Step 1 and is superseded at Step 3; §R30.2's condition gets its verdict recorded at Step 3. **It also needs the A5 correction (six dependents listed, thirteen found) and the A10 correction (§R30.1 calls the April file "no callers at all" — it has two live positive controls and the sole `numeric_in_arena` proof).**
3. **`docs/environment/12_renderer.md`** — owed by Step 3; a rewrite rather than a patch.

---

## Questions for the user

Two decisions remain open. (Four others were decided today and are recorded in §User decisions.)

### Q1 — What is the script called?

`scripts/eval/render_recordings_v2.py` → ?

- **`render_recordings.py`** — the cleanest end state, and the name the codebase already uses in prose. Freed by Step 3. Downside: the same filename means two different renderers depending on which commit you stand on, making `git log` and every historical doc reference ambiguous.
- **`render_episode_videos.py`** — unambiguous forever, matches the project's own phrase "episode videos", never collides with history.
- **`render_dashboard_videos.py`** — names the package that draws them.
- something else.

*(Related and also needed: the new output-folder name. Decision 4 settled that it changes and that the 26 existing folders stay put, but not what it becomes — `episode_videos/` pairs naturally with the second option above.)*

### Q2 — The dead duplicate in `grid_world.py` (Q8, still open)

`src/environment/grid_world.py:701` holds a second `save_jax_video` with **zero callers**, and `:344` an older `render_jax_state` copy. §R30.1 states today's approval does **not** cover them and Q8 still stands. This plan leaves them untouched. **Remove them as a separate change?**

---

## Checkpoints (roll-up)

- [ ] **CP0.1** — census pasted, every busy GPU attributed
- [ ] **CP1.1–CP1.3** — `save_jax_video` resolves; Matplotlib-free test still green unmodified; generator case passes
- [ ] **CP1.4** — **byte-identical MP4s** before/after, on fixture M4 *and* a real recording
- [ ] **CP1.5** — a human looked at two frames
- [ ] **CP1.6** — exactly one `environment.renderer` import left, at `:277`
- [ ] **CP1.7** — full suite green
- [ ] **CP2.1** — per-rule coverage table: all **six** rules
- [ ] **CP2.2** — each mutation fires via its named rule, on named participants
- [ ] **CP2.3** — each unbroken counterpart is silent
- [ ] **CP2.4** — rebuilt pinned counts exact; `SILENT_RULES` silent
- [ ] **CP2.5** — measurement-is-a-measurement test passes on the current renderer
- [ ] **CP2.6** — a human looked at every mutated frame
- [ ] **CP2.7** — **controls pass with V1 and the April file moved aside** (before any deletion)
- [ ] **CP2.8** — control suite green with **0 skipped**
- [ ] **CP3.1** — §R30.2 tally names specific runs
- [ ] **CP3.2** — zero `environment.renderer` / `renderer_v2` imports repo-wide
- [ ] **CP3.3** — audit still self-proving after deletion, coverage unchanged
- [ ] **CP3.4** — a human looked at a post-deletion frame
- [ ] **CP3.5** — recording-format contract names an owner that exists
- [ ] **CP3.6** — fixture-worlds bug row re-checked and reported
- [ ] **CP3.7** — full suite green
- [ ] **CP4.1–CP4.2** — census immediately before; no stale references
- [ ] **CP4.3** — a **real** dispatch produced a video (`frames verified` in its log)
- [ ] **CP4.4** — a human opened that video
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
