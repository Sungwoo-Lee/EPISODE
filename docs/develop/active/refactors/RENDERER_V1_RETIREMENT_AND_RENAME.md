---
title: "Retiring the old episode-video renderer, and dropping \"v2\" from the new one's name"
topic: refactors
status: active
created: 2026-09-21
last_updated: 2026-09-21
aliases: [renderer_v1_retirement]
---

# Retiring the old episode-video renderer, and dropping "v2" from the new one's name

> **Status**: PLANNED — nothing implemented, nothing approved. Awaiting `plan-reviewer` and four user decisions (§Questions).
> **Opened**: 2026-09-21
> **Related**: [[RENDERER_LAYOUT_REDESIGN]] §R30 (the retirement condition this plan executes) · [[EVAL_RENDERER_SWITCHOVER]] (the 2026-09-17 switch this plan cleans up after; **this plan must edit its Rollback section — see §Obligations**) · [[ASYNC_CHECKPOINT_VIDEO_RENDER]] (the dispatch mechanism that makes timing load-bearing) · [`SCRIPTS_DEPENDENCY_MAP`](../../../environment/SCRIPTS_DEPENDENCY_MAP.md) (maintenance contract fires on all three steps)

---

## Context

The project draws a video of each evaluation episode — a dashboard showing the agent on its grid alongside its hunger, injury and sensory readouts. Until four days ago those videos came from the **original renderer** (`src/environment/renderer.py`, written early in the project). On 2026-09-17 a **replacement renderer** took over: a new package (`src/environment/dashboard/`) driven by a new script whose filename ends in `_v2`. The user has since watched checkpoint videos arrive correctly from the new path and asked for the cleanup.

They asked for three things, in their words: *"I don't want to make the current renderer to be dependent any v1 script. Let's make archiving v1 plan. And as we will not distinguish them through version, new version no need to use v2 as the name."* In plain terms — (1) stop the new renderer from borrowing code from the old one, (2) retire the old one, (3) rename the new one so it no longer carries a version number, because there is no longer a second renderer to distinguish it from. They also said: *"Since the trainings are still ongoing, let's make plan and feedback first."*

**That last sentence is the governing constraint, and it is correct.** A live-cluster census run while writing this plan found **fourteen training runs in flight**, launched at 11:52 today across seven lab machines, each budgeted for ten million episodes. Every one of them writes a video at each checkpoint by launching the render script *by filename*, and each of them memorised that filename when it started. Rename the file and all fourteen runs keep calling a name that no longer exists — and the failure appears only as a warning line and an absent video, which is this project's signature quiet failure.

**The three pieces are separable and this plan keeps them separate**, because they carry very different risk. Piece 1 is a code move that can be verified by comparing video files byte-for-byte. Piece 2 is a deletion gated on a condition the user already wrote down and that the fourteen live runs are in the middle of satisfying. Piece 3 is a rename whose cost falls on whatever is running at the moment it happens. Conflating them would hide piece 3's timing hazard inside piece 1's easy verification.

**Nothing here is approved yet.** Four decisions are the user's and are listed in §Questions; the largest is that twenty-six completed runs already have their videos in a folder named `videos_v2/`, so renaming that folder is a question about existing data, not about code.

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

**The brief that commissioned this plan reported node 113 as idle on both GPUs.** It is not, as of the census: GPU 0 carries a 5 GB process at 40 % utilisation. Whatever it is, it is not in today's diary, and per the project's own GPU pre-flight rule (`nvidia-smi` alone under-reports; the diary is the claim ledger) it should be identified before anyone assumes that node is free. It does not change this plan's conclusions — the fourteen attributed runs already settle the question — but it is recorded because "I checked one node" is how a cluster gets double-booked.

**Verdict: runs are in flight, and will be for days.** The plan is therefore written so that the pieces which are safe under live runs happen now, and the one piece that is not is explicitly deferred to a user decision about timing.

### A2. What the render dispatch actually re-reads, and when — broader than "the rename"

`src/utils/async_render.py:56` binds the script **path** into a module constant at import time:

```python
_RENDER_SCRIPT = os.path.join(_PROJECT_ROOT, "scripts", "eval", "render_recordings_v2.py")
```

and `dispatch_render()` later runs `subprocess.Popen([sys.executable, _RENDER_SCRIPT, ...])`. The dependency map states the consequence plainly: *"The script path is bound at IMPORT time, so an in-flight trainer keeps invoking whichever renderer it started with."*

**The important half of that sentence is the half nobody says out loud.** The *path* is frozen in the trainer; the *file at that path* is not. The child is a brand-new Python process that reads the file — and everything the file imports — from disk at each dispatch. So the exposure of a live run to this plan is not limited to a rename:

| What we change | Does a live run see it? | What a mistake costs |
|---|---|---|
| `src/utils/async_render.py`, `evaluation_core.py`, `dreamer_srl/eval.py` | **No.** Already imported into the running trainer. | nothing, until restart |
| `scripts/eval/render_recordings_v2.py` (**contents**) | **Yes, at the very next checkpoint.** | that checkpoint's video |
| `src/environment/dashboard/**` (**contents**) | **Yes** — the child imports the package fresh. | that checkpoint's video |
| `scripts/eval/render_recordings_v2.py` (**filename**) | **Yes, and permanently** — the trainer's path never updates. | every remaining video of that run |

The first three rows are recoverable: the `.rec.gz` recordings are written at every checkpoint regardless, and `async_render.py`'s own docstring records that a skipped video is *"offline-recoverable via `scripts/eval/render_recordings_v2.py <recordings_dir>` — never a data-loss event."* The fourth row is recoverable in the same offline sense but not self-healing: nothing that run produces will ever render itself again.

**This is why "break the V1 dependency" is not a free step, and the brief's framing under-states it.** Editing the new script in place is live-exposed too. The mitigation is not to avoid the edit but to make the part that touches the live path as small and as checkable as possible — see §Design.

### A3. What the new renderer still takes from the old one — and the one place it matters

Three import sites in `scripts/eval/render_recordings_v2.py`, and they are **not equivalent**:

| Line | Imports | Reachable when | Production? |
|---|---|---|---|
| `:223` | `save_jax_video` | per-episode MP4 write | **yes** |
| `:474` | `save_jax_video` | `--concat` consolidated write | **yes** — the training path passes `--concat` |
| `:277` | `render_jax_state`, `thermal_color_limits` | inside `_benchmark()`, only under `--benchmark` | **no** |

`:277` lives in a function whose docstring says *"Time V2 and V1 on the same recordings"* — it is a **measuring instrument whose subject is the old renderer**. It does not need porting; when V1 goes, the arm it measures goes with it. Treating all three sites as one problem (as the brief does) would produce a pointless port of a comparison that has nothing left to compare.

So the whole production coupling is **one function**: `save_jax_video`, defined at `src/environment/renderer.py:1094`, and `src/environment/dashboard/` defines nothing like it.

### A4. The duplicate in `grid_world.py` is not a drop-in replacement — measured

There is a second `save_jax_video` at `src/environment/grid_world.py:701`. It is **not** the same function. The bodies diverge in exactly one line, and that line is load-bearing:

```python
# src/environment/renderer.py:1094 — streaming
with imageio.get_writer(output_path, fps=fps) as writer:
    for frame in frames:
        writer.append_data(frame)

# src/environment/grid_world.py:701 — materialising
imageio.mimsave(output_path, frames, fps=fps)
```

The new script passes **generators**, not lists, at both production call sites:

```python
# render_recordings_v2.py:237
save_jax_video((renderer.frame(t) for t in range(steps)), str(out), ...)
# render_recordings_v2.py:491
save_jax_video(frame_generator(), str(consolidated), fps=args.fps, quiet=True)
```

`imageio.mimsave` consumes its argument as a sequence, so substituting the `grid_world.py` variant would either fail or silently materialise an entire episode's frames in memory — defeating the reason the call sites are generators. **The copy that moves is the `renderer.py` one.** This is stated because "there are two copies, pick one" is a trap here, not a convenience.

`grid_world.py::save_jax_video` has **zero callers** anywhere in the repository (`grep -rn "save_jax_video" --include="*.py"` returns only its own definition line for that file). It is dead code — but it is dead code the user has already been asked about and has not approved removing (Q8 of [[RENDERER_LAYOUT_REDESIGN]], reaffirmed in §R30.1: *"NOT COVERED by today's approval — Q8 still stands over it"*). Per the project rule *"don't delete pre-existing dead code unless asked — mention it instead"*, this plan **does not touch it** and re-raises it as Question 4.

### A5. The dependent inventory is larger than §R30.3 records — a correction

[[RENDERER_LAYOUT_REDESIGN]] §R30.3 lists **six** things depending on the old renderer, and says it was measured *"by grepping `src/`, `scripts/` and `tests/`"*. Re-running that sweep at `HEAD` `75a2685c` finds **thirteen**. The seven it omits are real files, and three of them are tests — so a deletion scoped to §R30.3's table would turn the suite red.

| # | Dependent | Needs from V1 | In §R30.3? |
|---|---|---|---|
| 1 | `scripts/eval/render_recordings_v2.py` `:223 :277 :474` | `save_jax_video`; `render_jax_state`+`thermal_color_limits` (benchmark arm only) | yes |
| 2 | `scripts/eval/render_recordings.py` `:78 :93 :113 :219` | the old script itself — retired *with* V1 | (implied) |
| 3 | `scripts/eval/benchmark_render.py` `:39` | `render_jax_state` — V1 is its measurement subject | yes |
| 4 | `scripts/eval/render_layout_audit.py` `:418 :465` | V1 arm of the pixel audit | yes |
| 5 | `scripts/eval/make_render_fixture_recordings.py` `:839` | draws fixture frames through V1 | yes |
| 6 | `scripts/dreamer/visualize_dream.py` `:159 :180` | draws imagined rollouts through V1 | yes |
| 7 | `src/utils/eval_recording.py:34` | a **contract**, not an import (see A6) | yes |
| 8 | **`save_snapshot.py:14`** (repo root) | `render_jax_state` | **no** |
| 9 | **`scripts/media/record_env_demo.py:14`** | `render_jax_state`, `save_jax_video` | **no** |
| 10 | **`tests/env/test_thermal_rendering.py:47,:310`** | imports V1 drawing helpers directly | **no** |
| 11 | **`tests/algorithms/dreamer_srl/test_eval_recording.py:118,:138`** | renders through V1 to check the recording payload | **no** |
| 12 | **`tests/env/test_dashboard_v1_imports.py:99,:121`** | asserts *by name* that a bare dashboard import loads V1 and nothing more | **no** |
| 13 | **`docs/.../renderer_layout_redesign/render_current_frames.py:44`** | the redesign's own before/after frame generator | **no** |

Items 8 and 9 are independently corroborated by [`docs/environment/12_renderer.md`](../../../environment/12_renderer.md) lines 31–33, which lists them — so the reference doc was right and §R30.3's table is the undercount.

**Item 12 deserves its own sentence.** `tests/env/test_dashboard_v1_imports.py` exists to pin *what the new renderer borrows from the frozen old one*, including a subprocess check that a bare `import src.environment.dashboard` loads Matplotlib-free. Step 1 of this plan removes the last borrow. That test's subject therefore partly dissolves — but its **Matplotlib-free assertion must survive**, because that property is about the training path's import cost and has nothing to do with V1. Rewriting it is in Step 1's scope; deleting it is not.

### A6. Archiving V1 rehomes a contract, not just a file

`src/utils/eval_recording.py:34` carries no import. It carries a sentence:

> *"Exactly the fields `render_jax_state` reads. Keep in lockstep with renderer.py."*

That is the **definition of the recording file format** — every `.rec.gz` this project has ever written is specified by reference to a function in the old renderer. Delete V1 and the format's definition points at nothing. The same docstring goes on to explain that `RECORDING_FORMAT_VERSION` was deliberately not bumped for the thermal fields because *"the branch lives in `renderer.py`"* — a second sentence that also stops being true.

Rehoming this is Step 2 work and it is **prose, not code**: the contract must be restated against `src/environment/dashboard/` (specifically what `EpisodeRenderer` reads), in the same change that removes V1. A reader who hits a dangling reference here will not get an error; they will get a format with no stated owner, which is worse.

### A7. The rename surface, measured at `HEAD` `75a2685c`

| Thing | Count | Where |
|---|---|---|
| `render_recordings_v2` references, all file types | **139** | 24 in `.py`, 110 in `.md`, plus 2 configs, 1 shell script, 1 Claude skill |
| `videos_v2` references in `.py` | **38** | 8 files: `async_render.py` (3), `evaluation_core.py` (2), `dreamer_srl/eval.py` (2), `render_recordings_v2.py` (10), and four test modules (21) |
| `videos_v2/` directories **on disk** | **26** | under `results/` |
| `videos/` directories on disk (the old renderer's output) | **505** | under `results/` |

The brief's figures (133 / 38 / 26) were right at the time; the first has drifted to 139 because commit `75a2685c` added §R30. The `.py`-only figure of 24 for the script name is the number that matters for code work — the other 115 are documents and historical records, most of which **should not be rewritten** (see §Obligations).

**The 505 vs 26 ratio is the whole shape of Question 1.** The name `videos/` is not free for reuse: it is occupied, by half a thousand directories of output from the renderer being retired. Whatever the new folder ends up called, it cannot simply inherit `videos/` without a decision about what those 505 directories mean.

### A8. The retirement condition is already running — and this plan can destroy its own evidence

[[RENDERER_LAYOUT_REDESIGN]] §R30.2 states the condition the user set:

> *The old renderer and its offline script are retired once **two or three real training runs** have produced their checkpoint videos through the new script **with no occasion on which anyone needed to fall back** to the old renderer to get a video.*

with "real training run" defined as *"a full run on a lab node that writes checkpoint recordings and uploads the resulting videos to WandB."*

**The fourteen runs found by the census are exactly that.** They started at 11:52 today and are producing checkpoint videos through the new script right now. This is a fortunate alignment: Step 2 does not need a new experiment, it needs those runs to keep going.

**And that produces the sharpest hazard in this plan.** Step 1 edits the code path those runs render through. If Step 1 introduces a fault, a video goes missing, someone hand-renders it with the old script — and the fallback-free streak that Step 2 depends on is broken **by the change whose purpose was to enable Step 2**. The circularity is real and it has an honest resolution and a dishonest one:

- **Honest (adopted):** any fallback occasion counts, including one we caused. The count resets. That keeps §R30.2 meaning what the user meant.
- **Dishonest (rejected, recorded so nobody re-derives it):** "that fallback doesn't count, it was our own bug." This is self-serving and would let the condition be satisfied by a path nobody actually trusted.

The consequence is that Step 1 must be verified to a standard where a fault is caught *before* a checkpoint dispatch hits it — which is what §Design's byte-identity gate is for.

### A9. Why a green test suite is not the gate here

The project has a recorded incident on exactly this code: a renderer change once passed eighteen new unit tests while breaking the product. The reason is structural — a unit test asserts about panel boxes and frame counts; a human looking at a frame notices that the picture is wrong. Every step below therefore names **a rendered artefact someone looks at**, and Step 1 additionally gets a stronger machine gate that most renderer changes cannot have:

**Step 1 is a pure relocation of an unchanged function, so its output must be *byte-identical*.** Not "looks the same", not "frame count matches" — the same MP4 bytes. That is a check that fails loudly on any accidental behaviour change, and it is available precisely because nothing about the function is being redesigned. If the bytes differ, the copy was not pure and the step is wrong.

---

## Implementation Plan

### Design

Three steps, landed as **three separate commits**, in this order. The ordering is not stylistic: Step 2 cannot start until Step 1 removes the production dependency, and Step 3 should not start until Step 2 has settled what the script is for.

```
Step 0  Live-run census                      ← gate, re-run immediately before Step 1 and Step 3
   │
Step 1  Move save_jax_video into the dashboard package     ← safe under live runs, with care
   │    1a additive: add the new module, nothing imports it   (zero live exposure)
   │    1b flip: one-line import change in the new script     (small live exposure, byte-identity gated)
   │
   ├──── ⏸ WAIT: §R30.2 condition (2–3 runs, no fallback) — the 14 live runs are the evidence
   │
Step 2  Archive the old renderer + its script + rehome the contract
   │
Step 3  Rename the script and (per Q1) the output folder   ← NOT safe under live runs
```

**Why 1a/1b split.** Adding a new module that nothing imports cannot affect a running render. Flipping one import line can. Splitting them means the risky part of Step 1 is a single reviewable line, applied at a moment of our choosing, with the new code already proven by then.

**Why `save_jax_video` goes to `src/environment/dashboard/video.py` — the decision and its justification.**

1. **The dashboard package is the new renderer's home**, and this function is the last thing its script reaches outside of it. Putting it anywhere else (a `src/utils/` helper, a new top-level module) leaves the new renderer still borrowing from a neighbour, which is the exact condition the user asked to end.
2. **Copy, do not import — and that is the package's own established convention, not an invention.** `src/environment/dashboard/thermal.py`'s docstring states the rule verbatim: *"The plan says a helper that needs a behaviour change is **copied** into this package, never edited in place."* `render_recordings_v2.py` already copies V1's `_raise_fd_limit` for the same reason. This move is the third instance of a rule the codebase already follows.
3. **A new module rather than an existing one.** `cells.py`, `painters.py`, `panels.py` and `episode.py` are all drawing code and all import Matplotlib. Writing an MP4 is not drawing. A 40-line `video.py` keeps the one non-drawing responsibility separable and keeps it out of the Matplotlib-importing half of the package.
4. **It must not change what a bare package import costs.** `tests/env/test_dashboard_v1_imports.py` pins, in a subprocess, that `import src.environment.dashboard` does not pull in Matplotlib — because layout runs once per episode on the training path and must not pay for a drawing library. `video.py` satisfies this for free: the function body already defers `import imageio` and `import os` to call time in both existing copies, so a top-level re-export in `__init__.py` adds a module object and nothing else. **The existing subprocess test is the check**, unchanged.
5. **The source is `renderer.py:1094`, not `grid_world.py:701`** — see A4. The streaming body is required by the generator call sites.

**What happens to the duplicate in `grid_world.py`: nothing, in this plan.** It has zero callers, so it is dead; but Q8 is open over it and the user has not been asked. It is raised as Question 4 and left byte-for-byte untouched. Folding a dead-code deletion into a renderer retirement is how an unrelated regression gets attributed to the wrong change.

---

### Step 0 — Live-run census (gate, not a code change)

**Do this first, and again immediately before Step 3.** Not from memory, not from one node.

```bash
/home/vncuser/miniconda3/envs/grid_world_pain/bin/python scripts/lab/gpu_status.py
```

Cross-check the busy GPUs against today's and yesterday's `docs/diary/*.md` **Training runs** tables. For any busy GPU with no diary row, identify the process on that node before proceeding.

**Rule for what to do if runs are in flight** (they are, as of 2026-09-21 — see A1):

| Step | Runs in flight? | Rule |
|---|---|---|
| Step 1a | any | **Proceed.** Nothing imports the new module; zero exposure. |
| Step 1b | any | **Proceed, gated on the byte-identity check passing first** (CP1.4). A fault here costs one checkpoint's video and self-heals on revert at the next dispatch. |
| Step 2 | any | **Proceed** once §R30.2 is satisfied. V1 is not on the live path — removing it cannot affect a running render. |
| Step 3 | **yes** | **STOP and ask the user.** Renaming the script breaks every in-flight run's video output permanently for the life of that run. This is Question 2b. |
| Step 3 | no | Proceed. |

**Failure-detectable check (CP0.1):** the census output is pasted into the Implementation Report with a timestamp, listing every busy GPU and its attribution. A census that cannot attribute a busy GPU is a **stop**, not a footnote.

**Rollback:** none needed — no change is made.

---

### Step 1 — Break the new renderer's dependency on the old one

#### Step 1a (additive — zero live exposure)

##### `src/environment/dashboard/video.py` — NEW FILE

Copy the body of `src/environment/renderer.py:1094-1132` **unchanged**. Add a docstring in the package's established style stating: what the function does in plain words; that it is a **copy** of `renderer.py`'s implementation taken at commit `<sha>` because the old module is being retired; that the **streaming** `get_writer`/`append_data` form is required because callers pass generators (naming `render_recordings_v2.py:237` and `:491`); and that the divergent `imageio.mimsave` variant in `grid_world.py:701` is **not** the source and must not be substituted.

```python
# The function body is copied verbatim. Signature, defaults and the quiet-mode
# fd redirection are unchanged:
def save_jax_video(frames, output_path, fps=5, quiet=False):
    ...
    with imageio.get_writer(output_path, fps=fps) as writer:   # streaming — see docstring
        for frame in frames:
            writer.append_data(frame)
```

##### `src/environment/dashboard/__init__.py`

Add `from .video import save_jax_video` alongside the existing eager imports, and add `"save_jax_video"` to `__all__`. **Do not** route it through the lazy `_LAZY` / `__getattr__` mechanism — that exists for the two Matplotlib-importing names, and `video.py` imports nothing at module scope.

##### `tests/env/test_dashboard_video.py` — NEW FILE

A test that fails on the pre-change tree and passes after:

- `save_jax_video` is importable from `src.environment.dashboard`.
- Its signature matches `renderer.py`'s exactly (reuse the `inspect.signature` idiom from `test_dashboard_v1_imports.py`).
- **A generator input produces a readable MP4** with the expected frame count — this is the property `grid_world.py`'s variant would break, so it must be asserted directly, not assumed.

**Checkpoints:**
- [ ] **CP1.1** — `import src.environment.dashboard; dashboard.save_jax_video` resolves.
- [ ] **CP1.2** — the **existing** subprocess test `tests/env/test_dashboard_v1_imports.py` still passes unmodified: a bare package import must still load no Matplotlib. Run it in isolation (`pytest tests/env/test_dashboard_v1_imports.py -p no:randomly`), because it is a question about a whole process.
- [ ] **CP1.3** — `tests/env/test_dashboard_video.py` passes, including the generator case.

**Rollback:** `git revert` the commit, or simply delete the new file — nothing imports it yet. No running process is affected either way.

#### Step 1b (the flip — small live exposure)

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

The trailing `# read-only, frozen` comment goes with the change — it described a constraint that no longer applies.

##### `scripts/eval/render_recordings_v2.py` (line 277 and the `--benchmark` arm)

**Leave `:277` alone in this step.** It is inside `_benchmark()`, reachable only under `--benchmark`, and its purpose is to time the old renderer against the new one (A3). It is retired in **Step 2** together with its subject. Touching it here would be scope growth with no benefit.

Update the module docstring's FD-limit note and the "never called by training" paragraph, both of which describe a state that ended on 2026-09-17.

##### `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` (§3 row for `render_recordings_v2.py`, line 191)

The row currently reads *"Imports `src/environment/renderer.py::save_jax_video` READ-ONLY (and, under `--benchmark` only, …)"*. Rewrite to record that the production import now resolves inside `src/environment/dashboard/`, and that `--benchmark` remains the sole surviving V1 import until Step 2. **Maintenance-contract obligation — same commit, not later.**

**Checkpoints:**
- [ ] **CP1.4 — THE GATE: byte-identity on a real recording.** Before the flip, render a recording with the current script and keep the MP4. After the flip, render the *same* recording again. `sha256sum` both. **They must match exactly.** Use the committed fixture cell `M4` (`results/render_audit/recordings/M4/M4`, the campfire world used by `tests/scripts/test_render_recordings_v2.py`'s integration cases) **and** one checkpoint directory from a currently-running run, so the gate covers both a frozen fixture and live-shaped data. A mismatch means the relocation was not pure — **stop, do not proceed**.
- [ ] **CP1.5 — a human looks at a frame.** Extract frame 0 and a mid-episode frame from the post-flip M4 video to PNG and **look at them**. Byte-identity already proves nothing changed, so this is cheap; it is required anyway because the project's rule for renderer work is a rendered frame someone looked at, and because CP1.4 cannot fire if the *pre*-flip render was already wrong.
- [ ] **CP1.6 — no V1 import survives on the production path.** `grep -n "environment.renderer" scripts/eval/render_recordings_v2.py` returns **exactly one** line: `:277`, inside `_benchmark()`. Any other hit is a missed site.
- [ ] **CP1.7 — a live checkpoint renders.** After the flip, wait for one of the fourteen in-flight runs to hit a checkpoint and confirm its video appeared: check `<results_dir>/videos_v2/render_<pct>.log` for the phrase **`frames verified`**, which exists only in this script (lines 444 / 489) and is therefore direct evidence of which renderer ran rather than an inference from the output path — the same evidence idiom `train_command-agent.sh` used for the 2026-09-17 switch.
- [ ] **CP1.8** — full suite green, run once at the end.

**Rollback:** `git revert` the flip commit. **This rollback has an unusually good property, worth stating:** because the render child re-reads the script from disk at every dispatch, the revert takes effect at the **very next checkpoint** with no trainer restart and no interruption to any of the fourteen runs. Nothing needs to be re-launched.

**If CP1.7 fails and someone hand-renders with the old script to recover a video: that is a fallback occasion and it resets the §R30.2 count (A8).** Record it in the Implementation Report; do not rationalise it away.

---

### Step 2 — Archive the old renderer

**Precondition, checked not assumed:** §R30.2 is satisfied — two or three real training runs have produced checkpoint videos through the new script with **no** fallback occasion. The fourteen runs from the census are the candidate evidence. The check is a written tally in the Implementation Report naming each run, its checkpoints, and the absence of any hand-render.

**Second precondition:** re-run the dependent sweep of A5 and reconcile. The point of §R30.3 is that the surface shrinks; trust the fresh grep, not this table.

```bash
grep -rn "environment.renderer" --include="*.py" . | grep -v "^./.git/"
```

**Scope:** the thirteen dependents of A5. Each needs a disposition, and they are not all the same kind of work:

| Dependent | Disposition | Note |
|---|---|---|
| `render_recordings_v2.py:277` + `--benchmark` / `--benchmark-frames` flags | **remove** | its subject is gone; a benchmark with one arm measures nothing it did not already measure |
| `scripts/eval/render_recordings.py` | **archive with V1** | per §R30.1 they retire together |
| `scripts/eval/benchmark_render.py` | **archive** or repoint — user decision (Q3 follow-on) | V1 is its measurement subject; repointing changes what its recorded numbers mean |
| `scripts/eval/render_layout_audit.py` | **remove the V1 arm**, keep the audit | the V2 arm and the controls stay; `--arena-axes` already could not run on V1 |
| `scripts/eval/make_render_fixture_recordings.py` | **repoint to the dashboard package** | see §R30.5 hazard below |
| `scripts/dreamer/visualize_dream.py` | **repoint to the dashboard package** | already listed as Phase 5 item 3 of the redesign plan |
| `scripts/media/record_env_demo.py` | **repoint** | *missing from §R30.3* |
| `save_snapshot.py` (repo root) | **repoint or archive** — user decision | *missing from §R30.3*; a stray root-level script |
| `src/utils/eval_recording.py:34` | **rehome the contract** (A6) | prose, not code; restate the payload definition against `EpisodeRenderer` |
| `tests/env/test_thermal_rendering.py` | **repoint or retire the V1 cases** | *missing from §R30.3* |
| `tests/algorithms/dreamer_srl/test_eval_recording.py` | **repoint** | *missing from §R30.3* |
| `tests/env/test_dashboard_v1_imports.py` | **rewrite, keep the Matplotlib-free assertion** | *missing from §R30.3*; see A5 |
| `docs/.../renderer_layout_redesign/render_current_frames.py` | **archive with the plan folder** | *missing from §R30.3* |

**Also in Step 2's File Changes:**
- `docs/environment/12_renderer.md` — a substantial rewrite, not a line edit. It documents V1's internals throughout, and several of its line citations are **already stale** (it cites `save_jax_video` at `renderer.py:734`; it is at `:1094`). It also still describes `renderer_v2.py`, deleted separately today.
- `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` — rows at lines 17, 88, 89, 123, 181, 188, 189, 190, 191, 250, 270 all name V1 or its script. **Maintenance contract — same commit.**
- **[[EVAL_RENDERER_SWITCHOVER]] Rollback route (b)** — see §Obligations. Must be edited in this commit.
- **[[RENDERER_LAYOUT_REDESIGN]] §R30** — record that the condition was met, by which runs, and that §R30.3's inventory was an undercount.

**Checkpoints:**
- [ ] **CP2.1** — the §R30.2 tally is written out and names specific runs. "It's been fine" is not a tally.
- [ ] **CP2.2** — `grep -rn "environment.renderer" --include="*.py" .` returns **zero** hits outside the archive location.
- [ ] **CP2.3 — a rendered frame, again.** Re-render fixture `M4` and one live checkpoint after the archival and **look at the frames**. V1 should not be on this path at all, so this is a check that nothing was reached for implicitly (e.g. a process-global icon cache that V1 used to warm — a recorded bug in that module).
- [ ] **CP2.4** — `src/utils/eval_recording.py`'s docstring no longer names `render_jax_state` or `renderer.py`, and states an owner that exists.
- [ ] **CP2.5** — the five unrebuildable fixture cells are re-checked: if the Known Bugs row *"Five of the eleven render-audit fixture worlds can no longer be built"* is **still open**, §R30.5's insurance argument still holds and the user is told before anything is deleted.
- [ ] **CP2.6** — full suite green.

**Rollback:** `git revert`, or `git checkout <sha> -- src/environment/renderer.py scripts/eval/render_recordings.py`. Per §R29's user decision, git history is the rollback mechanism and no bespoke guard is built. **Note the asymmetry:** if V1 is *deleted* rather than *moved* (Question 3), rollback requires knowing the pre-deletion SHA — so that SHA is recorded in the Implementation Report, not left to be found later.

---

### Step 3 — Drop "v2" from the name

**Precondition: Step 0's census shows no runs in flight, OR the user has explicitly accepted the cost on the live runs (Question 2b).** This is the one step that cannot be made safe by care.

**Scope is decided by Questions 1 and 2.** Pending those answers, the shape is:

- `git mv scripts/eval/render_recordings_v2.py scripts/eval/<new-name>.py`
- The **three** `src/` path bindings, which the dependency map's §1b rule already itemises as the mandatory trio: `src/utils/async_render.py:56`, `src/utils/evaluation_core.py:382`, `src/algorithms/dreamer_srl/eval.py:552`. Plus the cosmetic hint string at `evaluation_core.py:415`.
- Tests that name the script: `tests/scripts/test_render_recordings_v2.py` (itself renamed), `tests/training/test_async_render_dispatch.py`, `tests/algorithms/dreamer_srl/test_render_upload.py`.
- Config comments naming the path: `configs/train/default.yaml:64,67`, `configs/evaluation/default.yaml:8`. **These are comments, not keys** — no schema change, no new mandatory key, so [`CONFIG_GUIDE`](../../../environment/CONFIG_GUIDE.md)'s schema-change clause does not fire. Its line 644 *does* name the script path and must be updated.
- `.claude/skills/trajectory-story/SKILL.md:60`.
- `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` — **the contract fires hardest here**: a file under `scripts/` is renamed and three `src/` callers change. §1b rows (72, 73, 74), the §1b rule sentence (79), §2 (121–123), §3 (191), §4 (250) and §5 (270).
- If Question 1 chooses a new output folder: the **38** `videos_v2` occurrences across the eight `.py` files of A7.

**Explicitly NOT rewritten:** the 110 `.md` occurrences that are **historical record** — diary entries, wiki entries, the `train_command-agent.sh` comment block at lines 3766–3780 (a dated account of the 2026-09-17 verification), and prior revisions of the redesign plan. Rewriting history to match a later name makes the record lie about what was run. Only *forward-looking* references (reference docs, the config guide, the skill, the dependency map) change.

**Checkpoints:**
- [ ] **CP3.1** — re-run Step 0's census **immediately before** the rename and paste it in. A census from this morning is not a census.
- [ ] **CP3.2** — `grep -rn "render_recordings_v2" --include="*.py" --include="*.yaml" --include="*.sh" .` returns zero hits outside deliberately-preserved historical comments.
- [ ] **CP3.3 — a real dispatch, not a mocked one.** Launch a short run (or resume one) far enough to produce its first checkpoint video, and confirm `videos*/render_<pct>.log` contains **`frames verified`**. The tests mock `_RENDER_SCRIPT`; only a real dispatch proves the path binding is right. This is the same evidence standard `train_command-agent.sh` applied to the 2026-09-17 switch.
- [ ] **CP3.4 — look at the video.** Open the MP4 the dispatch produced.
- [ ] **CP3.5** — if the output folder was renamed: the 26 pre-existing directories are in the state Question 1 chose, and that state is recorded. No `results/` directory is deleted under any option.
- [ ] **CP3.6** — full suite green.

**Rollback:** rename the file back (`git revert` does this). **A trainer that was live across the rename recovers at its next dispatch once the old filename exists again** — the path it holds is a string, and the string resolves as soon as the file is there. This makes "restore the old name" a genuine rollback rather than a partial one. It does **not** recover videos already skipped during the window; those are re-renderable offline from their `.rec.gz`.

---

## Obligations to other documents (recorded, deliberately not executed here)

Per the brief, this plan **does not edit** either document below. Both edits belong to the step that makes them true.

1. **[[EVAL_RENDERER_SWITCHOVER]] — Rollback route (b), owed by Step 2.** That section names hand-rendering with `scripts/eval/render_recordings.py` as the recovery path for a run whose checkpoint videos are missing, and records it as *verified rather than assumed* (exit 0, output matching to within 0.01 %). Archiving V1 deletes that route. Step 2 must either repoint route (b) at the surviving script or state plainly that hand-rendering is now single-renderer and what that costs. **§R30.4 already records this obligation; this plan is the thing that discharges it.**

2. **[[RENDERER_LAYOUT_REDESIGN]] §R30 — owed by Steps 1 and 2.** §R30.3's dependent table loses its first row at Step 1 and is superseded at Step 2; §R30.2's condition gets its verdict recorded at Step 2. **It also needs the correction from A5: the table is an undercount of six versus thirteen.** Flagging this now rather than at Step 2, because a future reader checking the condition against that table would under-scope the work.

3. **`docs/environment/12_renderer.md`** — owed by Step 2, and it needs a rewrite rather than a patch (A5, Step 2 File Changes). Several of its line citations are already stale today.

---

## Questions for the user

Four decisions, none of which this plan takes on its own.

### Q1 — What happens to `videos_v2/`? (**a data question, not a code question**)

**26 completed runs already have their videos in a folder called `videos_v2/`. A further 505 directories called `videos/` hold output from the renderer being retired.** So `videos/` is not a free name.

| Option | What happens | Cost |
|---|---|---|
| **(a) Keep `videos_v2/`** | nothing changes on disk or in code | The name keeps a version number in a project that no longer versions renderers — the opposite of what was asked. Zero risk. |
| **(b) Reuse `videos/`** | new runs write where V1 wrote | Collides with 505 existing directories. A single run could contain output from two renderers in one folder with no way to tell them apart. **Not recommended.** |
| **(c) New neutral name, old folders left alone** | e.g. `episode_videos/`; the 26 existing `videos_v2/` stay where they are | Clean going forward. The 26 become orphans — still readable, but any tool that looks only at the new name stops seeing them. |
| **(d) New neutral name + move the 26** | same, then `mv` the existing directories | No orphans. But it mutates result data on a NAS, **while fourteen runs are writing**, in a repo with a recorded `results/` loss incident. If chosen, it happens at Step 3 with no run in flight and after a `cp -a` snapshot. |

*(If (c) or (d): the script already has an `--output-dir` flag, so a transitional period where both names work is possible without new code.)*

### Q2 — What is the script called, and when does the rename happen?

**(2a) The name.** `scripts/eval/render_recordings_v2.py` → ?
- `render_recordings.py` — the cleanest end state, and the name the whole codebase already uses in prose. Only available *after* Step 2 frees it. Downside: the same filename means two different renderers depending on which commit you are standing on, which makes `git log` and every historical doc reference ambiguous.
- `render_episode_videos.py` — unambiguous forever, matches the project's own phrase "episode videos", never collides with history.
- `render_dashboard_videos.py` — names the package that draws them.
- something else.

**(2b) The timing.** The fourteen live runs are budgeted at 10 M episodes and will run for **days**. Waiting for a quiet cluster is therefore not a short wait. Choose one:
- **Wait** for no runs in flight (clean, possibly a long wait);
- **Rename anyway** and accept that the in-flight runs stop producing videos for the rest of their lives — recoverable offline from their `.rec.gz` recordings, but not automatically;
- **Rename and immediately hand-render** the affected runs' checkpoints offline as they accumulate.

### Q3 — Is V1 deleted, or moved somewhere?

- **Delete** (`git rm`) — consistent with the user's own §R29 ruling that *"git history, not a bespoke guard, is the rollback mechanism"*. Simplest.
- **Move** to an archive location, keeping it runnable — §R30.5 argues for this: five of the eleven render-audit fixture worlds **cannot currently be rebuilt** (a config loader check now rejects their thermal settings), so those recordings are the only copies that exist, and a second renderer able to read them is cheap insurance until that bug is closed. Note there is **no existing `src/` archive convention** to follow, so this option means inventing a location — which should be named explicitly rather than assumed.

*Check before deciding: is the Known Bugs row for those five fixture worlds still open?*

### Q4 — The dead duplicate in `grid_world.py` (Q8, still open)

`src/environment/grid_world.py:701` holds a second `save_jax_video` with **zero callers**, and `:344` holds an older `render_jax_state` copy. §R30.1 states explicitly that today's approval does **not** cover them and Q8 still stands. This plan leaves them untouched. **Should they be removed — as a separate change, not folded into this one?**

---

## Checkpoints (roll-up)

- [ ] **CP0.1** — live-run census pasted with timestamp; every busy GPU attributed
- [ ] **CP1.1** — `save_jax_video` resolves from the dashboard package
- [ ] **CP1.2** — existing Matplotlib-free subprocess test still passes, unmodified
- [ ] **CP1.3** — new video test passes, generator case included
- [ ] **CP1.4** — **byte-identical MP4s** before/after the flip, on fixture M4 *and* a live recording
- [ ] **CP1.5** — a human looked at two frames from the post-flip render
- [ ] **CP1.6** — exactly one `environment.renderer` import left in the new script, at `:277`
- [ ] **CP1.7** — a live checkpoint rendered; `frames verified` present in its log
- [ ] **CP1.8** — full suite green
- [ ] **CP2.1** — §R30.2 tally written, naming specific runs
- [ ] **CP2.2** — zero `environment.renderer` imports repo-wide
- [ ] **CP2.3** — a human looked at frames from a post-archival render
- [ ] **CP2.4** — the recording-format contract names an owner that exists
- [ ] **CP2.5** — the five-unrebuildable-fixtures bug row re-checked and reported
- [ ] **CP2.6** — full suite green
- [ ] **CP3.1** — census re-run immediately before the rename
- [ ] **CP3.2** — no stale script references outside preserved history
- [ ] **CP3.3** — a **real** dispatch produced a video; `frames verified` in its log
- [ ] **CP3.4** — a human opened that video
- [ ] **CP3.5** — the 26 existing directories are in the chosen state; nothing deleted
- [ ] **CP3.6** — full suite green

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
