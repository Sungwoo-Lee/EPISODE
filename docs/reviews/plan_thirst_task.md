---
title: "Plan review: the thirst task (9 worlds x 2 agents, one seed) — code pinning, the early-stop rule, and what one seed can show"
topic: thirst_task
status: active
created: 2026-10-01
last_updated: 2026-10-01
---

# Plan review: thirst task, pre-launch gate

> **Object reviewed**: `docs/experiments/active/thirst_task/THIRST_TASK.md` at commit `c631d8fa`
> (branch `v5.0`, worktree `.claude/worktrees/thirst`), with its eight configs under
> `configs/environment/experiment/thirst/`.
> **Reviewed by**: plan-reviewer · 2026-10-01
> **Feedback appended to the plan**: [[THIRST_TASK]] §"Feedback from plan-reviewer".

Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run · 🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

## Verdict

**NOT READY: one Critical finding. The fix is a paragraph of text, not new code.**

The design trains the ordinary agent and the agent with a modulator (a small side network that
rescales the main network according to what the body feels). Each trains once, in nine versions of
the pond-and-thirst world: three map sizes crossed with three smell ranges. The aim is to see whether
every world can be learned, and whether the modulated agent pulls clearly ahead anywhere. The
design is careful. The configs change only what they claim to change: I re-derived that through the
trainer's own config loader. Every output is written outside the worktree. The early-stop rule can
be computed from what the trainer actually logs.

**The one blocker:** the design never says that the code must not change while the series runs.
All 18 runs, any relaunch after a crash, and the follow-up seeds read their code from a worktree
that someone is still developing in. The placement-fixes plan is cleared to start editing the
environment code in that same worktree as soon as the pilot finishes, and the pilot finished at
17:48 today. Already-running jobs would mostly be safe, because their code is already loaded. But
runs launched later, relaunches and the seeds-43/44 follow-up would train in a *different world*
(different food regrowth, different placement order), and nothing in the design would detect it.

**Exit condition (flips to SOUND WITH CONCERNS):** add a "code pinning and run validity"
subsection to §9 as described in C1 below, and add a matching line to the placement plan's start
gate. The Moderates can be fixed in the same edit or accepted knowingly.

## Findings

| # | Sev | Location | Issue | Suggested fix | Owner |
|---|---|---|---|---|---|
| C1 | 🔴 | THIRST_TASK §3.4 "Code", §9.2; PLACEMENT_FIXES_PLAN `:44-46`, `:583` (K0) | **No code freeze.** The 18 runs take about 2 days of wall time at the longest, and any follow-up takes more. The design pins no launch SHA and does not forbid edits. It also does not carry over the pilot's runner pre-flight or its run-validity checks: [[THIRST_PILOT]] §3.2 (clean worktree, branch `v5.0`, NAS mounted, git on the node, no existing results directory, the "do not touch the worktree" diary note) and §2.7 P5. §9.2 inherits only §2.5, the launch script. The placement plan's start gate (K0) names only the seven pilot runs, which are now done (diary 2026-10-01 17:48), so the env core may be edited in this worktree at any moment. A running process has already imported and compiled its code, so its training is not affected. Three things are: (a) any of the 18 launched after an edit (18 GPUs at once is not guaranteed); (b) the §7 "relaunch once from scratch with the same seed"; (c) the §5.4 seeds 43/44. All three would silently train on a world with the placement fix. Checkpoint-time video renders also re-import `src/` from the worktree (`train.py` async render), so their videos would show the edited code. | Add §9.3 "Code pinning and run validity": (1) record one launch SHA. All 18 runs, every relaunch and the seed-43/44 addendum run at that SHA. If the code must move first, the addendum re-runs seed 42 too. (2) No edits to `src/`, `train.py`, `configs/` or runtime `scripts/` in this worktree until the last run (including follow-ups) ends. Placement work goes in a separate worktree. (3) Diary freeze note at launch. (4) Carry over pilot §3.2 pre-flight verbatim. (5) Per-run validity, as pilot P5 (a)(b)(c)(e), plus: the saved `models/config.yaml` shows `water.properties [1,0,0,0,0]` (the Revision-2 smell; the pilot's runs had the old one), and the cell's height/width, `water.size` and `sensory.sensor_radius`. Also add "THIRST_TASK runs finished" to PLACEMENT_FIXES_PLAN K0. | experiment-designer (design); senior-developer (K0 line) |
| M1 | 🟡 | §4 rules 3–4, §9.2 last line | **The stop point is defined in wall-clock terms ("SIGINT right after the 1 M checkpoint"), but nobody can act at that moment.** 18 runs cross 1 M boundaries every 1.4–5 h, round the clock, for about 2 days. The ordinary agent runs about 20–25 % faster than the modulated one (§8), so when the modulated run reaches boundary b, its partner is already well past it. "Last 1 M before the stop" then means different episode windows for the two agents unless the doc defines it. Also missing: who checks at what cadence, with what tool, and how the signal is sent (`terminate_command.py` uses `pkill -f <pattern>`; a second SIGINT force-quits, `train.py:138-145`). | Define the stop **retroactively**: the stop boundary b* is the first boundary at which both runs satisfy rules 1–2. The final model is checkpoint b* (all are kept). S_final and Δ use episodes [b*−1 M, b*] for both runs. Anything after b* is ignored, whenever the SIGINT actually lands. Name a reader script, tested now on the pilot's runs (rows every 4,000 episodes, so a full history scan is cheap), a cadence (e.g. a `/wake` loop or two fixed daily checks), and the exact stop command: the full unique tag as the pattern, sent once. Put both agents of a world on the same card class. | experiment-designer |
| M2 | 🟡 | §4 rule 2 | **"Has learned" is judged on survival alone.** A run that has learned to eat but not yet to drink can reach 1.5 × its first-block survival and sit flat, then be stopped. This is the context-exploration lesson again: long flat stretches before a skill appears. The plateau test also passes on a *falling* curve. | Add "§5.1(a) passes in the current block" to the stop conditions. Treat two consecutive falls as a flag, not a stop. | experiment-designer |
| M3 | 🟡 | Purpose; §5.3; §5.4 | **The 6 % line is pre-registered but rests on thin ground, and the follow-up is not.** The 2.6 % spread comes from 3 seeds, at 2 M episodes, on the old pond smell, at 10×10 only. With 2 degrees of freedom its 95 % range is about 1.4–16 %. In the pilot's own world, one of its three seed pairs already differed by +7.3 % (ordinary s44 190.8 vs modulated s44 204.7, THIRST_PILOT §7.2), so the rule would flag a "lead" there. At σ = 2.6 % and 9 worlds, the chance of at least one false lead is about 38 %. That is acceptable for a trigger, but: (a) the follow-up compute is not budgeted (one 20×20 lead is 4 runs, about 130–170 GPU-h on 3090s); (b) if seed 42 is pooled into the 3-seed test, it brings the selection that picked the world (winner's curse); (c) the 3-seed decision rule is not written; (d) only positive leads are followed up. | Pre-register now: the confirmation reads seeds 43/44 only (or states how seed 42's selection is handled); the 3-seed decision rule; a compute ceiling for follow-ups; whether a ≤ −6 % world also gets seeds. | experiment-designer |
| M4 | 🟡 | §5.2 last two bullets; §5.3 "Exploratory hypothesis"; §5.4 third bullet | **Some claims are stronger than one seed allows.** (a) §5.2 gives reach × size a *refutation* criterion, but §5.4 says one seed cannot support an interaction claim, and a difference of two differences has noise of about 2σ ≈ 5 %, so 6 % is about 1.2 noise units. (b) The exploratory hypothesis is "supported" whenever leads fall in harder worlds, and 8 of 9 worlds are "harder", so a single noise lead supports it about one time in three. Read literally, "the leads, if any" is also satisfied when there are no leads. (c) "≥ 10 % is readable from one run" uses a σ measured only at 10×10. | Reword (a) and (b) as descriptive ("consistent with / not consistent with"), close the "if any" loophole, and condition (c) on the spread actually seen at the larger sizes. | experiment-designer |
| M5 | 🟡 | §3.5 row 2; §5 primary DV | **Equal episodes are not equal experience, and only the episode-matched Δ is pre-registered.** The pilot found 25–31 % less experience at equal episodes (THIRST_PILOT §7.5). Within a world, the agent that survives longer gets more PPO updates per episode, which inflates its lead. Across sizes, the harder world gets fewer updates. | Pre-register an equal-environment-steps read-out for every Δ and for the size/reach costs, as the pilot did after the fact, as co-primary or as a required robustness check for any lead. | experiment-designer |
| M6 | 🟡 | §3.3, §3.5 row 4, §5.2 mechanism and refutation | **Smell range is cut on all five smell channels, not just food and pond.** `sensor_radius` feeds the resource, animal, obstacle and water kernels (`src/environment/sensor.py:37-51`). Predators carry odour (properties `[0, 0.7, 0.5, 0, 0]`), and so do rabbits and bushes. Range 3 therefore also removes early warning of predators. The predicted mechanism ("a thirst cost, not starvation") and its refutation clause ignore injury. | State this in §3.3 and §3.5. Add injury to §5.2's three-way outcome (thirst / starvation / injury). | experiment-designer |
| M7 | 🟡 | §5 secondaries; §3.5 row 6; §6.4 last paragraph | **Two promised read-outs are not in the training log.** No `Episode/*` or `Bal_*` key records drinking or start hydration (checked: `src/behavior/balance_metrics.py`, `train.py` logging). The pilot got drinking bouts and start-hydration bands from greedy-policy stored episodes (THIRST_PILOT §4.2). This design has no analysis-plan section: which checkpoints, which collector, run from the worktree, and which v4.0 tools must not be used (pilot §4.4). | Add a short §5.5 analysis plan, or drop those read-outs. | experiment-designer |
| L1 | 🟢 | §3.5, §6.2 | Regrown food landing on a fire (~2 %) or a bush (~7 %), from [[PLACEMENT_FIXES_PLAN]] item 1, is not listed among the known placement issues. Only the start-on-fire share is. | One row in §3.5. | experiment-designer |
| L2 | 🟢 | §6 | The check evidence (`validate_all.json`, scripts) lives only in the worktree's gitignored `tmp/`, which `git worktree remove` deletes. | Copy it to the shared `tmp/`, or note that it is disposable. | experiment-designer |

## Assumptions

| Assumption | Status |
|---|---|
| Same-size worlds differ only in smell range | **Verified by me.** The resolved configs (default.yaml + `load_env_config`) differ in exactly `sensory.sensor_radius` (20/5/3, 30/5/3, 40/5/3) |
| 15×15 / 20×20 whole-map worlds differ from level 06 only in size, areas, counts, pond and range | **Verified by me.** The diff is limited to height/width, location_areas, resources, entities, obstacles, `water.size`/`candidates`, `sensor_radius` |
| All outputs land outside the worktree | **Verified** (`--results-dir`, `WANDB_DIR`, `--log`). The pilot left no run output in the worktree; its `results/` holds only an older render audit |
| The stop rule is computable from the log | **Verified.** `Episode/Steps`, `Episode/Number` and `Episode/_window_n` are logged every 4,000 episodes (`configs/train/recurrent_ppo.yaml`) |
| SIGINT stops without an extra checkpoint; every checkpoint is kept | **Verified** (`train.py:1661` break; no save after the loop; `max_checkpoints_to_keep: null`) |
| Revision-2 smell is in the code that will run | Verified at HEAD now. **Not checked per run** (C1) |
| The worktree code stays fixed for the series and the follow-ups | **Unverified, and currently not protected** (C1) |
| 18 GPUs are free at once | ❓ Unverified. If launches are staggered, C1 matters more |
| Seed spread at 15×15 / 20×20 is like 10×10's 2.6 % | ❓ Unverified (M3, M4) |
| The 20×20 speed factor (0.48) holds for the modulated agent and on 3090/2080 Ti | ❓ Taken from ordinary runs on a 4090; marked "errs long" |
| Critical-settings change-log entry present | Verified (`CONFIG_CRITICAL_SETTINGS.md:56`) |
| A study folder outside `basic/` is allowed | Precedent exists (`context_exploration/`, `continual_worlds/`, `level05_body_interactions/`); the headers carry the not-maintained notice |

## Answers to the requested checks, briefly

1. **Launch path:** the script and output routing are correct, and everything goes outside the worktree. The gaps are the pilot's pre-flight and validity checks, which are not inherited, and the missing code freeze (C1).
2. **Early stop:** it is computable. Stopping both agents of a world together does not favour either agent: the later-plateauing one is never cut off, and the earlier one gains under 1 % per extra block by definition. The biases that remain are the experience gap (M5) and the undefined overshoot window (M1). "Who checks, and when" is not specified (M1).
3. **One seed:** the rule is pre-registered. Its noise basis is weak, and its follow-up is not pre-registered (M3). §5.2 and §5.3 overreach (M4).
4. **Confounds:** reach is the only change within a size (verified). Steps of experience are reported but not pre-registered as a read-out (M5). Smell range also removes predator odour (M6).
5. **Placement:** the fire-start rate and the (0,0) fallback are stated and measured; regrowth-on-fire is not (L1). The landing hazard is C1.
6. **Comparability:** handled correctly. The 10×10 whole-map world is *not* the pilot's world (old smell), and the doc says so. The context-exploration numbers are used only for predictions.
7. **Rules:** survival steps only, no invented versions, folder precedent, change-log entry: all compliant.

## Cost of being wrong

If C1 bites, the placement fix lands mid-series. Runs launched after it, relaunches and the follow-up
seeds then train in a different world from the seed-42 runs. That is invisible in WandB and would
surface, if at all, only at analysis. The cost is roughly 30–170 GPU-hours of reruns per affected
world, plus the risk that a modulator "lead" is confirmed or killed by seeds from a different world.
The Moderates cost interpretability (a wrong stop window, an overstated hypothesis), not data. No
data-loss hazard was found.

Reviewed by: plan-reviewer
