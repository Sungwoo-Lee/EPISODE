---
id: 20260909_1404_verify_handover_claims_against_code
date: 2026-09-09
time: "14:04"
folder: subagent_engineering
tags: [meta, learned_lesson, refutation, subagent]
summary: "A handover note written by the session that did the work was wrong about the codebase in three of its six bug claims and in its central diagnosis; every claim was directionally right but wrong in the detail that determined the fix, so a receiving session must re-verify against code before acting."
related: ["20260909_1402_parity_gates_green_without_comparing", "20260909_1403_cpu_pin_directory_conftest_not_repo_wide"]
session_origin: claude_code
session_label: "thermal handover follow-up (v4.0)"
importance: high
status: settled
valid_until: null
confidence: high
supersedes: []
raw_source: claude_data/.claude/projects/-media-nas01-projects-Interoceptive-AI-grid-world-pain/75d00862-fedd-4393-8200-a49d666c3a30.jsonl
raw_completeness: full
---

# A handover's claims were right in direction and wrong in the detail that picks the fix

## Key conclusion

The temperature-system handover was written by the session that had just done the work,
and it was still wrong about the codebase in three of its six bug claims plus its two
headline diagnoses. None of the errors was a fabrication — each was directionally correct
and wrong in exactly the detail a receiving session would act on. The practical rule: a
handover tells you *where to look*, never *what is true*. Re-derive the mechanism from
code before writing a fix, a registry row, or a recommendation.

## Evidence, measurements, facts

- **Claim: a `bush_dwell` key "appears nowhere in `src/`".** True but misleading — the
  producer is `scripts/behavior_measures/avoidance_stats_heatmap.py`, not `src/`, so the
  search had been run in the wrong tree. The real cause is a rename: commit `6695aa29`
  (2026-09-07) renamed the measure to `bush_hiding` across 49 files and touched **zero**
  test files. Fix is a one-word test edit, not an investigation.
- **Claim: `RECORDING_FORMAT_VERSION` at `eval_recording.py:65` and `:82`.** Those line
  numbers were pre-thermal; it is `:20`, `:85`, `:102`. The substance (written everywhere,
  read back nowhere) holds.
- **Claim: "68 configs fail because mandatory keys were added without migrating the archive;
  thermal is the third instance, not the cause."** Re-measured: of 141 stand-alone configs,
  73 load and 68 raise. All 68 lack `sensory.injury_observable` **and** `thermal.enabled`;
  what gets *reported* is whichever check fires first — 55 on `thermal.enabled`, 13 on
  `sensory.visual_value_mode`, none on `injury_observable`. So thermal changed the error
  message for 55 configs without changing pass/fail. Also: a naive probe suggested all 216
  layered configs fail too — that is an artefact of loading them without resolving
  `extends:`, exactly the wrong-loader trap CLAUDE.md warns about, and not a finding.
- **Diagnosis: the `JAX_PLATFORMS` failure is an import-order race between modules that all
  call `os.environ.setdefault`.** Wrong, and the truth is worse: three fixture-consuming
  parity modules pin nothing at all, so they fail when run **alone**. The handover also
  attributed a runtime backend guard to `tests/env/test_directional_sensors.py`; that string
  lives in `scripts/verification/capture_sensor_baseline.py:20` and **no test asserts the
  backend**. It further recommended a marker-scoped pin, which cannot work at all.
- **Diagnosis: guard the thermal drive-axis mis-scaling by warning on a non-zero setpoint.**
  Wrong trigger. The loader checks only `min < max` and `min <= setpoint <= max`, so
  `setpoint 0, min -10, max +20` has a zero setpoint and is still mis-scaled — full-scale
  cold weighs half of full-scale heat. The real condition is asymmetry about the setpoint.
- **What the handover got right**, and why it was still worth reading: it named the six
  places to look, flagged its own file as the entry point, and carried two environment
  hazards that had already cost real time (broad `find` over the 641 GB NAS mount causing
  file-descriptor exhaustion; `pkill -f` with a pattern matching the caller's own shell).

## Decisions and actions

- Every one of the six rows was re-verified against code before filing; the three wrong
  claims were corrected **in the registry row itself**, with a note saying what the handover
  had said, so the correction survives the plan doc's archival.
- A seventh defect the handover did not know about was found during that verification —
  see [[20260909_1402_parity_gates_green_without_comparing]].
- The two calibration items were deferred to `OPEN_WORK_HANDOFF.md` (commit `90970506`)
  with the corrected guard condition recorded, not the handover's version.

## Open questions and follow-ups

- The handover's own explanation for its unreliability was structural: the implementing
  session ran with its working directory outside the repository, so none of the 22 project
  agents in `.claude/agents/` were registered — including the reviewers that would normally
  catch this. Whether a cheap pre-flight check ("am I rooted where the agents live?") is
  worth adding has not been decided.

## References

- Handover: `docs/develop/active/thermal/HANDOVER.md`; detail in the sibling
  `IMPLEMENTATION_PLAN.md` (slated for archival — which is why the corrections were pushed
  into the registry instead).
- Registry: `docs/develop/active/issues/KNOWN_BUGS.md` (`82d2c12b`, `73a19a31`).
- Related: [[20260909_1402_parity_gates_green_without_comparing]] ·
  [[20260909_1403_cpu_pin_directory_conftest_not_repo_wide]]
- Raw conversation: synced via `./sync-agent-data.sh claude push`. To read on another node:
  `./sync-agent-data.sh claude pull`, then either `claude --resume 75d00862-fedd-4393-8200-a49d666c3a30`
  or `python scripts/claude/claude_jsonl_to_md.py <jsonl> /tmp/<id>.md`.

<!-- BACKLINKS — auto-generated by scripts/regen_wiki_graph.py; do not edit -->
## Backlinks
- [[20260909_1402_parity_gates_green_without_comparing]] (env_entities, 2026-09-09) — Two of the environment's byte-identity gates were reporting success without comp
<!-- END BACKLINKS -->
