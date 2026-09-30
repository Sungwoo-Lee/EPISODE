---
title: "Plan review: the level-06 (pond + thirst) training pilot — launch path, thresholds and where the outputs go"
topic: thirst_pilot
status: active
created: 2026-10-01
last_updated: 2026-10-01
---

# Plan review: level-06 training pilot (pre-launch gate)

> **Object reviewed**: `docs/experiments/active/thirst_pilot/THIRST_PILOT.md` at commit `9d969d04`
> (branch `v5.0`, worktree `.claude/worktrees/thirst`).
> **Reviewed by**: plan-reviewer · 2026-10-01
> **Feedback appended to the plan**: [[THIRST_PILOT]] §"Feedback from plan-reviewer".

Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run · 🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

## Verdict

**NOT READY — one Critical, cheap to fix; everything else is Moderate or lower.**

The pilot trains the ordinary and the modulated agent for 2 million episodes each in the new
"pond + thirst" world (three seeds each), plus one run of the old campfire world on the new code
as a control, and asks whether the world is learnable and sane before any modulator comparison.
The design is careful: the launch path that keeps runs on the water branch is genuinely
airtight as far as I could break it, the death-cause bookkeeping is safe, the "drinking step"
rule is exact, and the level-05 comparison is like-for-like.

The one thing that must change before launch is **where the outputs live**. Every checkpoint,
provenance file and log lands inside the worktree's gitignored folders. A worktree is a
temporary checkout that exists to be deleted after its branch merges, and `git worktree remove`
deletes gitignored files silently — it does not even ask for `--force`, because ignored files do
not count as "unclean". The plan says this in a warning box and leaves the timing to the user,
but has no step, no destination and no owner. Twenty GPU-hours of training would vanish in one
routine cleanup command that a parallel session might run without knowing. The fix is one
decision (a destination outside any worktree) and one line in the launch or post-run procedure.

Three Moderate findings: the speed metric the plan medians is a *cumulative* average, not a
rate; one of the five "did this run use the new code" checks asserts WandB metadata values that
have never been observed for a worktree launch and would kill a valid run if the format differs;
and the "learned to drink" pass line halves a first-tenth value without subtracting the floor of
thirst deaths that no policy can avoid, so it can fail an agent that drinks well.

**To flip the verdict**: name the output destination and add the copy (or `--results-dir`)
step; make WandB-metadata check informational; redefine the speed read-out as a windowed
rate; state the early-death floor in the drinking pass line.

## Findings

| # | Severity | Location | Issue | Suggested fix | Owner |
|---|---|---|---|---|---|
| C1 | 🔴 | THIRST_PILOT §2.5 "Where outputs land" + warning box; `.gitignore:12,19,20` | Checkpoints, `provenance.json`, WandB binaries and nohup logs all land in `<worktree>/results`, `/wandb`, `/logs`, all gitignored. `git worktree remove` treats ignored files as clean and deletes the directory without `--force`; a worktree under `.claude/worktrees/` exists to be removed after merge, and parallel sessions cannot tell runs live there. §4.2 then writes the stored episodes to the same place. The plan names the hazard but has no step, destination, owner or timing. | Either (a) launch with `--results-dir <NAS path outside any worktree>/JAX_RecurrentPPO/<ts>_<TAG>` (`train.py:446`, used as given at `train.py:939-942`, so the runner supplies the full per-run path) and point `--log` there too; or (b) add a numbered post-run step "copy `results/JAX_RecurrentPPO/*l06pilot*` and `logs/` to `<destination>`" that the runner executes when each run finishes, before any analysis. In both cases the user names the destination now (the shared folder is off-limits under the session rule), and a diary row "worktree `thirst` holds live training outputs — do not `git worktree remove`" goes in at launch. | user (destination) · experiment-designer (doc step) · training-runner (execution) |
| M1 | 🟡 | §2.7 P4; `train.py:2003` | `Time/sps_env` is `global_step / seconds since training start` — a running mean over the whole run, not a rate. A median over rows after the first 5 % is the median of a running mean that still carries compile + warm-up in every row; it is biased low and depends on run length. P4 divides two runs with different episode lengths (different wall time), so the bias does not cancel. | Define P4 as a windowed rate: Δ`timesteps` / Δ`_runtime` between the row nearest 50 % of the run and the last row (or simply the last-row value = total steps / total time). Read the reference speeds in the §2.7 table the same way. | experiment-designer |
| M2 | 🟡 | §2.7 P5(c)(d); §5 row 1; `wandb_settings.py:2033-2095`; `provenance.py` `_GIT_TIMEOUT_S` | A P5 failure stops the run as invalid. (d) asserts `program` = `<worktree>/train.py` and `root` = `<worktree>` — values produced by WandB's own path/git detection, never observed for a worktree launch. A benign format difference kills a valid 3-hour run. (c) accepts `git_dirty: "unknown"` but not `git_sha: "unknown"`, yet the same 10-second git timeout applies to all three provenance calls. | Gate on (a), (b), (c) and (e). Make (d) informational until the first run's `wandb-metadata.json` has been read, then pin the observed values. For (c), an `"unknown"` sha falls back to the HEAD the runner recorded in the manifest plus (a); it does not invalidate. | experiment-designer |
| M3 | 🟡 | §2.7 P1 pass line | "Last tenth ≤ half of first tenth" does not subtract the floor of policy-independent thirst deaths (0.625·k/200 by step k: ~3 % for a 10-step walk to the pond; the design page simulated 1.8–2.4 %). Untrained agents mostly die of injury or starvation first (level-05 first-tenth survival ≈ 51 steps), so the first-tenth thirst share may be modest and the halving target may sit 2–3 points above the floor. An agent that drinks well can then fail the pass line. | State the floor explicitly (measure it from the 0.4 M store: episodes whose start hydration cannot reach a pond cell in time) and phrase the pass line as "last tenth ≤ 0.10 **and** ≤ max(0.5 × first tenth, floor + 0.03)". | experiment-designer |
| L1 | 🟢 | §2.7 P5(a) | "The log's first line is `[v5-gate] OK …`": `import train` emits JAX/absl warnings on stderr before the gate prints, and the log is `2>&1`. | Say "the log contains". | experiment-designer |
| L2 | 🟢 | §4.2 checkpoints | Checkpoint keys are the episode count at save time (`checkpointer.save(total_episodes_completed)`, `train.py:2625`), e.g. `400123`, not round numbers; the collector takes `final` or an explicit step (`collect_trajectories.py:904`). | Say "the checkpoint nearest 0.4 M and 1.2 M, and `final`"; confirm from a finished run's `models/` listing that `final` is ≥ 2,000,000 (see A3). | experiment-designer |
| L3 | 🟢 | §2.7 P1 "≥ 80 % … drank" | 100 % by construction (the plan says so). | Label it a data-integrity check, not a pass line. | experiment-designer |
| L4 | 🟢 | §4.2 "small reader"; Known Bugs "stale second copy of the seed" (`KNOWN_BUGS.md:114`) | If the reader lives under `scripts/`, `SCRIPTS_DEPENDENCY_MAP.md` must change in the same commit. Seeds for runs 2/3/5/6 must be read from the saved config's top-level `seed:` or provenance `argv`, never `training.seed` (always reads 42). | Add both notes to §4.2. | experiment-designer / developer |
| L5 | 🟢 | §2.5 "The problem" | The worktree's `run_command.py` derives its default log dir from its own location (`run_command.py:43`), not the shared folder. Harmless: `--log` is explicit. | Correct the sentence. | experiment-designer |

## What I tried to break and could not

- **Launch path (§2.5).** The gate reads what the import system actually resolved (`src.__path__`, every loaded module's `__file__`), then checks the imported `EnvParams` carries `water_enabled` and the worktree branch is `v5.0`. It is not circular: it inspects the process's own import state, not a re-derivation. Its one blind spot — modules imported lazily at run time — is closed by a static scan I re-ran: no bare `import`/`from` of `environment`, `models`, `utils`, `behavior`, `algorithms` or `pytorch_agents` anywhere in `train.py`, `src/` or `scripts/eval/`, indented lines included (the only hit is a docstring, `src/environment/dashboard/layout.py:17`). Every child process follows the worktree: the async render helper locates the repo from `src/utils/async_render.py:54`, the experiment-eval dispatcher from `train.py:252`, and `render_recordings_v2.py:72`, `eval_rollout.py:47`, `experiment_eval_checkpoint.py:48-50` and `collect_trajectories.py:55-57` each insert their own `parents[k]`. No persistent JAX compilation cache is configured. `results_dir` is cwd-relative (`train.py:942`); WandB gets no `dir=`, so `wandb/` sits under cwd. A `PYTHONPATH` exported by a node's shell profile would be caught by the `src.__path__` check (the plan tested this).
- **Death-cause consumers (§4.4).** All seven `Episode/Term_*` keys come from one list (`episode_metrics.py:46-48`), the late-death split covers codes 2–7 (`balance_metrics.py:78`), and the trajectory store documents codes 6/7 (`trajectory_store.py:140-142, 173-177`). The three excluded tools are correctly excluded.
- **Drinking-step rule (§4.2).** `core.py:599-604`: hydration' = clip(hydration − 0.625 + 5.625·[on pond], 0, 200), drain applied on the pond too, death judged on the clipped value at both ends. Off the pond hydration strictly falls (or the episode is over); on the pond it rises by exactly 5 (less only on the death step at 200, still a rise). "Hydration rose ⇔ on pond" is exact; the 1.6 × start-hydration deadline is exact.
- **Level-05 like-for-like (Q3).** Both reference commits (`4209024d`, `f00f6c61`) are ancestors of HEAD. Commits touching the rPPO path since: balance metrics (`89f3cb78`, parity-tested bit-identical), the shared key recipe (`18e1e5f0`, golden keys for seeds 42–44 identical), opt-in activation capture (`d7fa3f68`), the shared termination list (`2af12e4d`), and water (static-gated, parity 43/43). Train configs gained only the two balance keys; the agent configs and levels 03–05 are untouched; the references ran on 3090s. The control run therefore catches gross regressions, not bit-level ones (see A5).
- **Rules.** No version scheme invented (`v4.0` / `v5.0` are branch names); no new configs; `--seed` on the CLI is flagged as the deviation it is; no code, so no fallback-default exposure; survival steps everywhere, reward never read.

## Assumptions the plan rests on

| # | Assumption | Status |
|---|---|---|
| A1 | WandB records `program` as the absolute worktree path and `root` as the worktree for a launch from a worktree. | Unverified (M2). Python ≥ 3.9 makes `__main__.__file__` absolute, so `program` is plausible; `root` depends on GitPython's worktree handling. Read the first run's `wandb-metadata.json`. |
| A2 | `git` is installed on every node used. Without it the gate aborts with a traceback (loud, fine) but provenance reads `unknown`. | Unverified. One `which git` per node in pre-flight. |
| A3 | A finished 2 M-episode run's `models/` contains a checkpoint key ≥ 2,000,000 (so `final` is the end of training, not ~1.8 M). | Unverified from this worktree (the reference runs live in the shared folder). Check on P0a before §4.2 runs. |
| A4 | P4's "0–10 % slower" attributes the cost to the water code. Level 06's shorter episodes also mean more resets per step, which costs on its own. | Not separated. If the 15 % flag trips, split reset-rate cost from water-op cost before concluding. |
| A5 | The ±6 band for the control uses a seed s.d. of 1.5 estimated from three runs; the true s.d. could be 2–3, making the band about 2 s.d. | Accepted risk: ~5 % chance of a false flag; the flag costs a pause, not a rerun. |
| A6 | The reference S values were read from WandB *sampled* history; the pilot will be read "exactly the same way". | Fine if the same sampling is used for both arms; `scan_history` is cleaner. |

## Cost of being wrong

The Critical is not a wrong-conclusion risk but an irrecoverable-data one: if the worktree is
removed after the branch merges — the normal end of a worktree's life — before the outputs are
copied, all seven runs (about 20 GPU-hours) and the stored episodes are gone and the pilot is
re-trained. The Moderates cost at most one false "invalid, stopped" verdict on a good 3-hour run,
a mis-sized speed number, or a false "did not learn to drink" flag that pauses the study until
someone notices the floor.

Reviewed by: plan-reviewer
