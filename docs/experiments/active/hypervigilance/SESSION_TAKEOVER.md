---
title: Hypervigilance session — takeover notes
created: 2026-10-04
last_updated: 2026-10-05
status: active
---

# Hypervigilance session — takeover notes (state at 2026-10-05 ~17:30 KST)

## Purpose

This session (Claude session `4efbe660-28c2-4643-b231-d3c6d2635b5a`, board name `grid-world-pain-d9`) is near
its context limit. These notes let a fresh session pick up exactly where it is: what is running, what the
user asked for and decided, what the findings are, what is still open, and where every file lives. The
user's working language is English with plain explanations; read section 7 (rules) before replying.

## 1. Running right now — the fast-bush-healing replication (18 runs)

**Why.** Two level-04 agents trained on 22 Sep 2026 (ordinary `t1none` and modulated `t16quad_ALL`, seed 42,
healing 25x faster on a bush) looked like the combination the user wants: the modulated agent hides for a
predator (~53 %) and a chasing rabbit (~35 %), not for a wandering rabbit or nothing (~10–12 %), hides more
when injured (+8 to +11 points), and is about twice as steady checkpoint-to-checkpoint as the ordinary agent.
One seed per agent, so the user asked to replicate with 3 seeds, in the same world and with temperature,
and with temperature + thirst. Design + manifest: [[FAST_HEAL_REPLICATION]]
(`docs/experiments/active/hypervigilance/FAST_HEAL_REPLICATION.md`).

| world (config) | ordinary / modulated, seeds 42 43 44 | node:GPU |
|---|---|---|
| level 04 `configs/environment/experiment/basic/04-jump_attack_10x10.yaml` | 6 runs | 106:0/1, 107:0/1, 108:0/1 |
| level 05 `.../basic/05-campfire_thermal_10x10.yaml` (+ cold, campfires) | 6 runs | 109, 110, 111 |
| level 06 `.../basic/06-pond_thirst_10x10.yaml` (+ cold, campfires, pond, thirst) | 6 runs | s43/s44 on 101, 103; **s42 on 102:0/1 (relaunched 17:02)** |

- Tags `rppo_healrep_l0{4,5,6}_{t1none,t16quad}_s{42,43,44}`; WandB group `fast_heal_replication`; 10 M episodes;
  agent configs `configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_{t1none,t16quad_ALL}.yaml`
  (unchanged since 2026-09-07). Launched ~16:01–16:03 KST; expected to finish ~4–8 h later.
- Run folders `results/JAX_RecurrentPPO/20261005-16*_rppo_healrep_*` (16 live) and
  `20261005-170252_rppo_healrep_l06_t1none_s42`, `20261005-170314_rppo_healrep_l06_t16quad_s42`.
  **Dead, ignore:** `20261005-160128_…l06_t1none_s42`, `20261005-160249_…l06_t16quad_s42` (node 113 rebooted itself
  ~16:05; cause unknown; user chose to relaunch on 102 rather than 113).
- Level-04 seed 42 is a reproduction check of the 22-Sep pair (`train.py --seed` default is 42).
- Verified 2026-10-05: today's level-04 file is behaviourally identical to the 22-Sep saved config (every
  differing key is a later option defaulting to off). All three worlds carry recovery_base_rate 0.2,
  recovery_accel_rate 0, recovery_in_bush_multiplier 25.
- Diary rows: 16 by the training-runner sub-agent + 2 for the relaunch (`docs/diary/2026-10-05.md`).
- Launch record (commented) in `train_command-agent.sh` (commit 8bd88951).

**Next, when training finishes (not started):**
1. Experiment-test sweeps (`scripts/eval/dwell_sweep/run_sweep.py`, new spec YAMLs, CPU nodes, check others' jobs):
   - level 04 → scenes `configs/environment/experiment/behavior_probes/core/avoidance` (bush blocks animals; same as
     the 22-Sep re-test `configs/eval_sweeps/basicq2_wave2_blocking_bush_rppo.yaml`);
   - level 05 → `behavior_probes/hvsmell/two_channel` (scenes built on level 05 + campfire beside the bush; its
     world file restates basic/05 exactly — the l05body generator asserted w0000 == two_channel);
   - level 06 → `behavior_probes/thirst/g10sW` (extends basic/06-pond_thirst, 10x10, start hydration 180).
   - Collation is slow on this container: if many sweeps, run `scripts/analysis/studies/f7b_across_runs/aggregate_only.py`
     on lab nodes (see §5 issues), not 15 at once locally.
2. Add the runs to `scripts/analysis/studies/f7b_across_runs/collect.py` REGISTRY (new family, e.g.
   "Fast-heal replication"), rebuild the cross-run page; compare per seed: unhurt baseline, animal dependence
   (predator / chasing / wandering rabbit minus no animal), injury effect, checkpoint-to-checkpoint SD,
   ordinary vs modulated. Then diary `training-done` rows.

## 2. Published pages (this session)

| page | URL | source |
|---|---|---|
| **Injury and Rabbit Avoidance Across Runs** (main current work, v8) | https://claude.ai/artifact/EnRWJ5Q5NfJj8a2C6TYibz | `docs/experiments/active/hypervigilance/f7b_across_runs/f7b_across_runs.html` from `page_template.html`; scripts `scripts/analysis/studies/f7b_across_runs/{collect,figures,build_page,factors,aggregate_only}.py`; data `results/analysis/f7b_across_runs/` |
| Basic Behaviour Analysis — hvsmell (v3) | https://claude.ai/artifact/YULHh3RkJtrc1TVE2yC5M8 | `scripts/analysis/basic_behaviour/` |
| Continual Worlds plan / results | Xvd13TcMHMcG31FbspxKfP / 2PfinPyZD791PzX3Lrokfj | handed over to "Training: neuromodulation" |

Rebuild the cross-run page: `$P collect.py --out results/analysis/f7b_across_runs` (run on a lab node via
`./run_command.py 105 "cd <repo> && $P scripts/analysis/studies/f7b_across_runs/collect.py --out ..."` — local NAS reads
are very slow), then `factors.py --data ...`, then each `figures.py --figure {rank,family,within,timeline,map,factors}`
and `--figure levels --group {ladder,july,dreamer,refuge,core_old,core,thermal,injgrid,smell,body,thirst}`
(**check each prints `wrote ….png`** — house.save can refuse silently in a filtered loop, F80), then `build_page.py
--data results/analysis/f7b_across_runs`, render with `scripts/claude/check_artifact_layout.py`, format gate
(artifact-format-reviewer, model opus), publish to the same URL.

## 3. Findings so far (exploratory; page text has the numbers)

- **Most of the injury effect is not about the rabbit.** Runs trained with 25x bush healing (76 runs, from
  22 Sep) hide ~9 points more when injured even with no animal; the 87 earlier runs ~0. Wandering rabbit adds ~0
  on top. (Cue, not proof: date, world version and food store also changed on 22 Sep.)
- **Factor ranking (Figure F, matched pairs):** fast bush healing raises injured bush dwell with a wandering rabbit
  by ~+16 (6/6 pairs); nothing else moves it >~4. Treating the wandering rabbit as a threat when injured is
  *lowered* by fast healing (~−5); small rises from a jumping predator (level 04 vs 03, ~+4) and a training bush
  that keeps animals out (~+2); removing ambush predators lowers it.
- **Two kinds:** older ordinary-method runs: injury does nothing, animal dependence varies widely (chasing rabbit
  median 16, up to 73; wandering rabbit median 4.6 over a 0.8 % empty baseline); Dreamer runs ignore animals;
  recent runs: injury-dependent (+9) with moderate animal dependence (median 19). No run strongly both — except
  the modulated 22-Sep level-04 agent is the closest example (hence the replication).
- **Blocking bush** (test or training) changes little; 22-Sep group renamed "Fast bush healing (22 Sep)".
- **Modulator (22-Sep runs, one seed):** checkpoint swing 0.4–0.5x the ordinary agent's at levels 04–05, ~1x at 06;
  lower unhurt baseline; larger injury effect at 04–05 — reproduces "Injury, Behaviour and the Modulator"
  (https://claude.ai/artifact/F2BKsyf87Ho1Vx9YAR5LoW). **Not yet on the cross-run page** (user did not answer the
  offer).
- The 23-Sep "control is parked (86 %)" answer (this session, before compaction) was the **final checkpoint
  only** of the pre-fix test (`results/eval/avoidance/metrics_history_rppo_basicq2_wave2/`); over the newest 20
  checkpoints the control's empty-scene dwell is 30 % (range 4–86). The modulated agent's pattern holds over
  checkpoints. Figures: `.../metrics_history_rppo_basicq2_wave2_blocking_bush/lvl04_{control,modulated}/FIG_bush_hiding.png`.
- The recovery-tuning page https://claude.ai/artifact/UiAbTX5TpbdNNTC8tMQAPG ("Making rest in the open not worth
  taking") designed the 25x / 0.2 / 0 settings; no agents trained there. Our results are its prediction coming
  true. Offered to link it from the cross-run page — not answered.

## 4. Open items

1. Replication: sweeps + analysis + page update when training finishes (§1).
2. Cross-run page fixes pending user OK: (a) remove duplicate rows — the injury-grid scene set repeats the same
   injury-0/70 tests as the core (level 04) and temperature (05/06) sets for the 22-Sep runs (identical values),
   so those runs are double-counted in group means and Figure F; (b) add a per-level "Modulator" section; (c)
   soften headline item "the two agent types overlap"; (d) link the recovery-tuning page.
3. Body-rules worlds with "healing costs food": agents starve in the food-free tests (values drawn hollow).
4. hvsmell F7 rows still type "30/30 episodes" by hand (f7_probes.py); reviewer oddities (matched-strength
   ~100 % bush at first checkpoint; odour-zeroed chasing rabbit reaching distance 0) unchecked.
5. hv smell study top-up (seeds 45/46) NOT launched — user: "exploration, not decision stage".
6. Branch v1.3 has 1 commit not in v5.0 (session board warning; not this session's).

## 5. Infrastructure lessons (this session)

- Sub-agents sometimes stall with zero output (developer agent twice); do work directly if so.
- 15 concurrent `run_sweep.py` collations drove the container load to ~350; run `aggregate_only.py` on lab
  nodes instead (`./run_command.py <node> "cd <repo> && $P scripts/analysis/studies/f7b_across_runs/aggregate_only.py <specs> --workers 12"`).
- `pkill -f <pattern>` kills your own shell if the pattern appears in the command line — use `[x]` tricks or PIDs.
- zsh arrays are 1-indexed.
- NAS mtimes are unreliable for staleness checks (F80); open redrawn PNGs instead.
- Git commits can take minutes on the NAS: run in background, commit with explicit pathspec, check `git log`.
- Node 113 rebooted unexpectedly 2026-10-05 16:05.

## 6. Commits this period (v5.0, not pushed unless noted)

46c610a0 (l05body scenes/sweeps + scripts), d6b638fd (page publish), ff6f2a2e (data section), cc609e18 (level
table), 22cecd57 (timeline), a10f7420 (earlier runs + map), 9fbb3d87 (wandering rabbit), 0149b3b4 (factors),
6df8553c (medians fix), FAST_HEAL_REPLICATION commits incl. 34061312; training-runner 8bd88951 (pushed).

## 7. Rules the user set (also in CLAUDE.md / memory)

- Plain language; conventional terms only ("seed-to-seed variation", never coined metaphors); "bush dwell".
- When a decision is the user's, ask with AskUserQuestion **and put the full context in the question** (user,
  2026-10-05: "If you need my decision ask me with context").
- Experiment tests = controlled scenes; training environment = the world trained in.
- Artifacts: publish-page skill, house style, figures from scripts, format gate before publish, §2.8 build order.
- Survival steps, never reward. Never node 114 for these jobs. Check other sessions' jobs before using nodes.
- Commit on v5.0 with explicit pathspec; Admin session handles pushes.
