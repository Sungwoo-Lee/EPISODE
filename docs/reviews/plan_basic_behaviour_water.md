# Plan review: Basic Behaviour Analysis — adding water (thirst-task runs)

Reviewed by: plan-reviewer · 2026-10-02 · plan [[BASIC_BEHAVIOUR_WATER]] at commit `92cd1be8` (branch `v5.0`)

## Verdict

**NOT READY** — most of the design is sound, but two problems would make the overnight loop either
stall or produce numbers that break the thirst study's own pre-registered rules.

The plan teaches the Basic Behaviour pipeline (the tool that builds a "what do these agents do"
web page from stored test episodes) to handle the new thirst worlds: a sixth behaviour, "standing
on the pond", the agent's water level, and the two new deaths. The core method holds up. The
pond is rebuilt from each episode's random seed and then checked against the water level the
episode actually recorded. That check is independent, and the existing reference checks on the
old worlds really are untouched by the water code. What blocks it:

1. **The data it needs does not exist yet, and the rule that picks which checkpoint to use has not
   been applied.** All 18 thirst runs finished their full 10 M episodes tonight. No early stop was
   recorded, and none of the stored test episodes has been collected. The plan's new water check
   and its population step both name the "final (b\*) store". The thirst study says everything a
   run learns after its stop point b\* is ignored. The plan's probe-scene step replays *every*
   saved checkpoint, which breaks that rule.
2. **The population builder needs a code change, not a doc edit.** It only knows the three
   hypervigilance world names and expects a different table format.

Below these are moderate problems: the hydration-by-drinking panel is biased by drinking bouts,
the probe-scene pond defaults are confounded with map size, d9's hypervigilance page would break
on its next rebuild, and one change-log entry is missing.

## Findings

Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run · 🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

| # | Sev | Location | Issue | Suggested fix | Owner |
|---|---|---|---|---|---|
| 1 | 🔴 | plan §Gates (Gate 3 "final store"), D11 (`--checkpoint-nearest <b* store>`), D12 ("every saved checkpoint"), Checkpoints C3–C8 | **Precondition missing, and a pre-registration breach.** All 18 run dirs hold 50 checkpoints up to ~10 000 000 and every log ends "Training complete". THIRST_TASK §10 records no b\* decision, §9 still says `running`, and `results/analysis/thirst_task/` (the §5.5 stores) does not exist. Gate 3, C4 and C5 cannot run. An unattended loop will either stall at C3 or improvise a "final" checkpoint (most likely 10 M). THIRST_TASK §4 says "Anything a run trains after b\* is ignored". D12 replays every checkpoint, and `probes.py` summarises the **newest 20**, which would be post-b\* checkpoints whenever b\* < 10 M. | Add a **C0**: b\* per world recorded in THIRST_TASK (by the thirst session that owns §4/§10), and the §5.5 stores collected. The loop stops after C2 unless C0 holds. D12 uses only checkpoints ≤ b\* of that world, and the probes' 20-checkpoint window ends at b\*. To get Gate 3-style validation tonight, run it on a **pilot** store against the pilot readout (finding 5). | senior-developer (plan), thirst session (b\*, collection) |
| 2 | 🟡 | D11 | **"Not a code change here" is wrong.** `make_population.py:42` maps worlds `{"1ch","1chm","2ch"}` only, and `:166` splits the Cell column on `·`. THIRST_TASK §9 cells read `g10sW ordinary`, so the split raises a bare `ValueError` before the missing `run dir` is even reached. `--runs` mode takes one `--world` per call, so the fallback is 9 population files that no downstream tool merges. b\* also differs per world, so one `--checkpoint-nearest` value cannot serve all 18. | Name the change and its owner: a per-world `--checkpoint-nearest`, plus either a thirst world map/format in `from_study_doc` or a small merge step. `make_population.py` lives under `studies/hypervigilance/`, so d9 reviews it. Its caller relation goes into SCRIPTS_DEPENDENCY_MAP. Also have the thirst session edit §9 (Status `completed` + `run dir` cells). | senior-developer → developer; d9 review |
| 3 | 🟡 | D8 (`hyd_nut__<target>`) | **Drinking bouts contaminate hydration at t−1** (same family as Known Bugs row 502, "contemporaneous binning"). Each pond step adds +5. A 10-step bout carries hydration across a whole 50-unit band, so "on the pond at t" is largely "on the pond at t−1, which already raised hydration(t−1)". The pond × hydration panel will show drinking at high hydration that is mostly bout continuation, not thirst-driven choice. Bush / eating × hydration are barely affected. | For the pond target, bin by hydration at **bout onset** (rows where the agent was off the pond at t−1, i.e. the arrival rate), or show both. Say which on the page. | developer; bug-curator to note the new instance |
| 4 | 🟡 | D12 (ii)–(iii) | **Probe pond defaults are confounded with map size.** The layout is pinned to absolute north-west coordinates and the pond goes to "the farthest corner". So the pond is ~3 squares from the start on 10×10 but ~8–12 on 15×15 / 20×20 (candidates `[12,12]`, `[16,16]`), and its pull depends on smell reach. Start hydration 100 drains to 37.5 by step 100, deep into the thirsty range, so a rising thirst drive competes with bush dwell inside the scene. Over-drinking (code 7) is also possible: 20 consecutive pond steps from 100. The plan only rules out code 6. Bush-dwell differences between map sizes therefore partly measure pond distance × thirst. The plan records the pond-visit share but pre-states no rule for using it. | (a) Put the pond at the **same distance from the start at every size** (the same absolute top-left is valid at 15/20; this matches the plan's own "absolute coordinates" logic). (b) Pre-state a rule: report bush dwell over steps before the first pond visit beside the full scene, and flag a world whose pond-visit share exceeds a stated threshold. (c) Consider a start hydration ≥ 162.5 so it stays ≥ setpoint all scene; trade-off: faster over-drinking. Ask the user. | experiment-designer (generator) |
| 5 | 🟡 | Gates, Gate 3(c) | **Gate 3(c) is redundant, not circular.** D3 already hard-stops on any step where "on a replayed pond cell" ≠ "hydration rose". So a completed sweep makes 3(c)'s two counts equal by construction. The truly independent leg (replayed pond vs recorded hydration) is D3 itself, and it is sound: the env is unchanged since the frozen commit `583b022f` (empty `git diff --stat` on `src/environment/`), and a wrong index or key recipe fails loudly. | Replace 3(c) with a check against an **external reference made earlier by other code**: run the pipeline on a pilot store and require integer equality with `results/analysis/thirst_pilot/readout/<agent>_<seed>_<ckpt>.json` drinking-step counts. It also runs before any thirst store exists. | developer |
| 6 | 🟡 | Gates, "Pass is added to `_golden_pass.json`" | **Gate 3 couples the shared stamp to thirst data.** `fit.require_stamp` reads that one stamp for every population. If Gate 3 is inside it, d9 cannot re-stamp (so cannot fit hvsmell) until a thirst store exists, and a Gate 3 failure blocks hvsmell too. | Write a separate water stamp that only water populations require. Gates 1/2 keep writing the shared one. | developer |
| 7 | 🟡 | File Changes (`_fig.py`, `f1`, `page_template.html`); Gates "source-hash consequence" | **d9's hvsmell page breaks or changes on its next rebuild.** (a) `f1_behaviours_survival.py:42,62` index `inv["targets"][t]` for every `REG.TARGETS`. Existing hvsmell inventories have no `pond` key, so F1 raises `KeyError` until all 18 hv runs are re-swept (~1.5 h). (b) `TERM_NAMES` 6/7 add two always-empty "died of thirst / over-drank" columns to a waterless page. (c) Shared template wording changes the hvsmell text. (d) d9 is active in the shared folder: an untracked `basic_behaviour_hvsmell/figures/` dir exists, and `2106c104` says "rebuilt, not published". Mid-edit `registry.py` saves there are live for d9's imports at once. | Termination columns and template wording keyed on the population (water enabled), not global. F1 iterates the targets present in the inventory. Develop in a worktree and merge once with Gates 1/2 green. Tell d9 *before* the merge that hvsmell caches will refuse `--reuse-cache`. | developer; d9 |
| 8 | 🟡 | "No critical-settings change" | **Missing change-log entry by precedent.** The 108 scene files override registry rows `water.placement` / `water.candidates` and the start-hydration draw locally. The 2026-09-23 thermal-probe and 2026-10-01 thirst entries log exactly this kind of local override ("NO CANONICAL VALUE CHANGED…"). | Add a same-commit CONFIG_CRITICAL_SETTINGS change-log entry for the thirst probe set. | experiment-designer |
| 9 | 🟡 | C8, D12 "Nodes" | **Node launch while the user sleeps.** The probe sweep needs lab nodes (CPU), and project memory says node choices are collected from the user up front. The node-avoid list (106, 107, 109–114) is stale because training has finished. | Mark C8 as **not** part of the unattended loop. Refresh the node note from live `gpu-status` + the diary at launch. | parent |
| 10 | 🟡 | D10, page text | **n = 1 honesty.** F3/F4 intervals come from 10 000 episodes of **one trained policy**. They will look tight and "significant", but they measure episode-to-episode spread, not seed-to-seed spread. The F7 t-interval measures checkpoint-to-checkpoint spread. Side-by-side ordinary/modulated panels invite a modulator reading that THIRST_TASK §5.4 forbids from one seed ("cannot support any modulator claim … any 'no difference' claim"). The behaviour shares also have no seed-noise estimate at all. §5.4's 6 % line is for survival. | Put a fixed caption on F1–F4/F6/F7 that intervals are within-run. Add a page-level box quoting §5.4. No "modulated minus ordinary" panel or sentence. State that greedy-store numbers are never pooled with training-log numbers (§5.5). | developer |
| 11 | 🟢 | File Changes | `_fig.FACTOR_LABEL` (new factor names) and `f1.TERM_SHORT` / `f1.TARGET_KEY` (codes 6/7, `pond`) are not listed. Both fail loudly, not silently. | List them. | developer |
| 12 | 🟢 | D12 env-config check list | The hvsmell generator's thermal contract check (bush warm/survivable, start cell not) is not in the list. One fire on a larger cold map must still hold. | Keep that check per world. | experiment-designer |

## Assumptions

| Assumption | Status |
|---|---|
| Hydration slot is found by name and differs from its alphabetical position | **Verified here**: rebuilt params at 10×10 and 20×20 give D = 59, Hydration at index 2, alphabetical 7 |
| Perceptual noise is off in all nine worlds | **Verified here**: `perceptual_noise.enabled: false` in all nine saved run configs. It is irrelevant to correctness anyway, because `obs_true` is pre-noise |
| Pond replay uses the code the runs used | **Verified here**: no `src/environment/` diff between `583b022f` and HEAD |
| "Hydration rose ⇔ on pond" is exact | Plausible (+5 / −0.625 per step, float32-exact). D3 enforces it per step on every store, so a violation stops the sweep |
| Gates 1/2 stay byte-identical | Plausible: they compare CSVs + factor order only, and every water path is gated on `water.enabled`. Note they exercise **no** water code |
| b\* per world is known | ❓ **Unverified / currently false** (finding 1) |
| §5.5 stores exist and match `make_population`'s `<root>/<tag>/<ckpt>/<hash>/` layout | ❓ Stores do not exist yet |
| One pond 3 squares away does not change bush dwell | ❓ Untested (finding 4) |
| Thirst runs never hit the (0,0) placement fallback at 15/20 | ❓ THIRST_TASK §5.5 delegates this to the same replay. This plan could report it for free from D2's resets |

## What would flip the verdict

Finding 1 resolved: a C0 precondition with b\* recorded per world and stores collected, the loop
halting after C2 otherwise, and F7 restricted to checkpoints ≤ b\*. Finding 2 resolved as a named,
owned code change. With those two the plan is **SOUND WITH CONCERNS**, and findings 3–10 can be
accepted knowingly or fixed in revision.

## Cost of being wrong

If the loop runs as written, the likely outcome is a stall at C3, which wastes the night but loses
nothing. The worse case is a loop that improvises the 10 M checkpoint as "final" and replays all
50 checkpoints. That yields a full thirst page (several CPU-hours of probe sweeps plus about 1.5 h
of local sweeps) whose numbers contradict the study's pre-registered stop rule and must be redone.
Separately, d9's hypervigilance page would fail to rebuild until about 1.5 h of re-sweeping.
There is no data-loss hazard.
