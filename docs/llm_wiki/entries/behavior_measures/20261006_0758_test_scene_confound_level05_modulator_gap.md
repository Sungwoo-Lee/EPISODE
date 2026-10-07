---
id: 20261006_0758_test_scene_confound_level05_modulator_gap
date: 2026-10-06
time: 07:58
folder: behavior_measures
tags: [hypervigilance, nmn, learned_lesson, refutation, testing]
summary: "The 22-Sep level-05 'modulated agent beats ordinary' result on the cross-run page came mostly from its test scenes: it was the only level-05 pair ever tested in the thermal 'neutral' scenes (air 0 C, no fire), where its ordinary agent's injury effect is +4 against +7 to +12 in the other three thermal variants, while later level-05 runs were tested only in their own cold + campfire scenes. Compare runs only within one test-scene set."
related: []
session_origin: claude_code
session_label: "hypervigilance F7b across runs / fast-heal replication (4efbe660)"
importance: high
status: active
valid_until: null
confidence: high
supersedes: []
raw_source: claude_data/.claude/projects/-media-nas01-projects-Interoceptive-AI-grid-world-pain/4efbe660-28c2-4643-b231-d3c6d2635b5a.jsonl
raw_completeness: full
---

# A level-05 modulator result that came from the test scenes, not from training

## Key conclusion
On the cross-run page (Figure B1, "most effective conditions") the 22-Sep level-05 pair was the second-strongest case of a modulated agent beating an ordinary one (injury effect +13 vs +4). That gap exists almost only in the thermal **neutral** test scenes (air 0 C everywhere, no campfire, start body temperature fixed at 0), which the ranking chose for every temperature-set run, and only the 22-Sep pairs were ever tested there. In the three other thermal variants the same 22-Sep ordinary agent shows +7 to +12, and the later level-05 runs (smell study) were tested only in their own scenes (cold air -31..-29 C, campfire beside the bush, random start temperature), where ordinary and modulated agents look alike. Two things differed between the groups at once, training (random start temperature) and test scenes, and no run group had been tested in both scene sets. **Rule: compare runs only within one test-scene set, and state the scene set behind every number.**

**Update 09:50 (re-test done).** All 66 later runs re-tested in neutral copies of their own scenes. The
neutral scenes do not create a one-seed oddity; the own scenes HIDE a real difference. In neutral scenes
the modulated agent's injury effect with the wandering rabbit is the larger one in 20 of 24 matched
level-05 pairs (body rules 13/15, median +7.1 pp; smell study 7/9, +3.9), against 13 of 24 in the own
scenes (medians about 0). Thirst (level 06): 5/9 in both. Reading: in cold scenes with a warm bush every
agent has a temperature reason to sit in the bush, which masks injury-driven hiding; with that reason
removed, ordinary agents lose much of their injury effect and modulated agents keep it. Caveat: neutral
scenes are warmer than training, so this is about carrying the injury response into an unfamiliar world.

## Evidence, measurements, facts
- Injury effect with no animal (injury 70 minus 0, bush dwell pp), mean over 2-10 M training steps, 22-Sep level 05 seed 42, ordinary / modulated: neutral **+4.0 (73% of checkpoints) / +13.2**; cool (-7.5 C) +11.3 / +12.7; fire beside bush (cold) +7.1 / +12.6; fire away (cold) +12.1 / +14.8. Smell-study control in its own scenes, seeds 42/43/44: ordinary +10.5 / +7.5 / +14.0, modulated +10.8 / +13.1 / +13.2 (results/analysis/f7b_across_runs/ckpt_summary.csv).
- Only sweep specs touching neutral scenes: configs/eval_sweeps/thermal_probes/thermalprobe_neutral_*.yaml and injury_grid/injurygrid_{,chase_}neutral_*.yaml; runs listed: the four 22-Sep runs (level 05 and 06, seed 42) only.
- Resolved scene settings (load_env_config): thermal/neutral_clean default_temp [0,0], no campfire, random_start_body_temp false; hvsmell/two_channel default_temp [-31,-29], campfire at config [5,3] beside the bush [5,2], random_start_body_temp true (-10..+5); thermal/fire_by_bush_clean as hvsmell but start temperature fixed.
- Training check (saved models/config.yaml, full diff, and provenance.json): 22-Sep level 05 (efdbc842) vs smell control (f00f6c61 seed 42, 7ec62720 seeds 43/44) differ only in thermal.random_start_body_temp (absent = off vs true); all other differences are later keys at off values, logging switches, names and seeds; agent block identical. Code changes between the versions are inert: body mechanics shipped off with bit-parity tests, balance metrics read-only, init-key refactor 18e1e5f0 keeps seed 42-44 keys bit-identical.
- Level 04 (no temperature system, core scenes only) is unaffected: ordinary +2 vs modulated +12.

## Decisions and actions
- Smell-study control runs (6) re-tested in thermal neutral scenes: configs/eval_sweeps/hvsmell_thermal/hvsmell_thermal_neutral_clean_rppo.yaml, node 113, 2026-10-06; registered in scripts/analysis/studies/f7b_across_runs/collect.py as family "Smell study (level 05)", scene set "thermal".
- Cross-run page to be corrected (state the scene choice behind B1 and show the 22-Sep level-05 pair across all thermal variants).
- Fixed-start-temperature level-05 arm (l05fix, 6 runs on 104/105/112) launched for the training-side question; both level-05 replication arms to be tested in the same full scene set.

- 2026-10-06 09:50: neutral re-test of 60 more runs (smell single/matched, body rules x15, thirst x9) via
  configs/eval_sweeps/neutral_variants/ (scenes: behavior_probes/neutral_variants/generate_neutral_variants.py,
  verified identical to thermal/neutral_clean for the control world). run_sweep.py now writes a provenance
  snapshot per launch (spec, git, resolved scenes) so this cannot recur silently.

## Open questions and follow-ups
- Does the smell-study ordinary agent also lose its injury effect in the neutral scenes? If yes, the neutral result is a property of ordinary agents in an off-distribution warm world (a different and possibly interesting claim); if no, the 22-Sep gap is specific to that seed.
- Whether random start temperature in training changes the modulator gap is open until the l05fix and replication level-05 arms are tested in the same scenes.

## References
- Page: docs/experiments/active/hypervigilance/f7b_across_runs/ (https://claude.ai/artifact/EnRWJ5Q5NfJj8a2C6TYibz); design doc docs/experiments/active/hypervigilance/FAST_HEAL_REPLICATION.md.
- Thermal battery rationale: docs/experiments/active/behavior_measures/thermal_probe_battery_bush_hiding.md; CONFIG_CRITICAL_SETTINGS change logs 2026-09-23, 2026-09-26, 2026-10-06.
- Raw conversation: synced via `./sync-agent-data.sh claude push`. To read on another node: `./sync-agent-data.sh claude pull`, then either `claude --resume 4efbe660-28c2-4643-b231-d3c6d2635b5a` (re-enter the session) or `python scripts/claude/claude_jsonl_to_md.py <jsonl> /tmp/<id>.md` (one-shot markdown view).

<!-- BACKLINKS — auto-generated by scripts/regen_wiki_graph.py; do not edit -->
## Backlinks
- [[20261007_1142_fast_heal_replication_modulator_effect_not_replicated]] (nmn_diagnosis, 2026-10-07) — The 22-Sep pattern (modulated agent with a larger, steadier injury-driven bush h
<!-- END BACKLINKS -->
