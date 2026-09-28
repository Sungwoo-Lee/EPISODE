---
title: "Plan review — continual worlds, Revision 2 (post-pilot plan update)"
topic: continual_worlds
status: active
created: 2026-09-28
last_updated: 2026-09-28
---

# Plan review: continual worlds, Revision 2

## Verdict

**Plan: NOT READY. Pilot read-out: SUPPORTED WITH CAVEATS.**

The continual-worlds study moves two pre-trained agents — an ordinary recurrent agent and the same
agent with a small "modulator" side-network — between outside worlds whose body rules never change,
and asks whether the modulated agent copes better with each switch. Before the long runs, short pilot
runs tested each candidate world. Revision 2 of the design document reads those pilots out and says
what launches next.

The read-out itself is right: every per-world pass / fail, every stage length, the branch point and
the from-scratch warm-up pass follow the rules that were written down before the pilots ran, and I
re-checked each number against the read-out data. Nothing was quietly re-labelled: the extra scouting
runs are called exploratory everywhere, the two draft replacement sequences say "do not launch" inside
their own files, and the two places where the working assumption differed from the rules (stage length
set per world, branch at 11 million episodes) are resolved in the rules' favour and put to the user.

What is not ready is one measurement rule. Two of the four planned "did the modulator help" votes —
how far survival drops at a switch, and how long it takes to climb back — are defined relative to
**each agent's own** settled level in that world. The pilots now show the two agents settle 37 survival
steps apart in the cold world (Winter: 198 vs 161). With that gap, those two votes measure "whose
settled level is lower", not "who adapts faster": the pilot already shows the artefact at 3× (recovery
132k vs 40k episodes with near-identical starting survival). The fix is a paragraph in the analysis
plan, pre-registered before the first main run launches; no run is wasted. With it, the verdict is
SOUND WITH CONCERNS.

Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run ·
🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

## Findings

The ranked table, open assumptions and cost-of-being-wrong statement are appended to the plan doc:
[[CONTINUAL_WORLDS]] § "Feedback from plan-reviewer (Revision 2)". Summary:

| # | Sev | What | Owner |
|---|---|---|---|
| R1 | 🔴 | Dip and recovery relative to each agent's own reference level confound plateau level with adaptation speed; pilot shows it at 3× in Winter. Pre-register a common-reference companion reading and require both signs to agree (as F3 did for episodes vs environment steps). | experiment-designer |
| R2 | 🟡 | "Winter levelled off" overstates: the modulated agent's trailing mean peaks at 175.7 (2.54 M) and ends 8.5 % lower, outside the plateau band. Show the trajectory; feeds decision D6. | experiment-designer |
| R3 | 🟡 | "Pilot 2 pass" is 3 of 4 pre-registered clauses; the forgetting sweep has never run and run 14 is unfinished. Label provisional; run the sweep on run 15 now. | experiment-designer |
| R4 | 🟡 | Per-world stage lengths make the two returns in P3 unequal (3 M vs 1 M of interference); state it, report forgetting next to interfering episodes. | experiment-designer / experiment-analyzer |
| R5 | 🟡 | Launch checklist names a `[STAGE]` line a branch will not print and omits the expected `[RESUME] ... != schedule-derived stage (1)` warning. | experiment-designer → training-runner |
| R6 | 🟢 | Failure mode 7.4 cited for the wrong condition; "best window" is not a criterion. | experiment-designer |
| R7 | 🟢 | Manifest statuses stale. | experiment-designer |

## Evidence checked

- Pilot numbers: `tmp/20260928_pilot_readout_run4.log` and `results/analysis/continual_worlds/pilot_readout.json`
  against every cell of the doc's 3.7.1 / 3.7.2 tables; survivable lines are 50 % of the recomputed
  last-10 % Home levels (249.8 / 253.4); the three drops apply 3.6 literally (soften once by the
  pre-named step, re-pilot, drop).
- Stage lengths follow the 3.3 formula; the 3.7.3 argument that `L_Forage` cannot leave the 1 M floor is
  arithmetically airtight (`T` > 666,667 needs a best window > 498.3 of a 500-step cap).
- Branch point: step directories `11000025` / `11000022` and `config.yaml` exist in the Forage pilot
  dirs; the pre-trained dirs were not written into by Pilot 1, so the read-only copy cannot collide.
- Restore path: `train.py:1559-1580` rebuilds the schedule-derived stage unconditionally (Known Bug H2
  fix); per-animal logging widths are fixed at `train.py:1413` from stage 0 (Known Bug A2 workaround
  intact); Pilot 2 exercised the identical steady state through the transition path.
- Pilot 2 logs: 4 `[STAGE]` lines per run, 0 tracebacks, 51 checkpoints (run 15); runs 13 / 15 / 16
  "Training complete", run 14 not.
- Pilot 3: all six rows and the no-collapse check match the log; pooled cross-checks agree.
- Code drift: no commit touched `train.py` / `src/` since the 13:16 launch.
- Node 114: SSH times out; the abandoned rows 39–41 wrote no data.
- Known Bugs registry: A2 (handled), B5 (single-config only), H2 (fixed, verified above), stale continual
  tests (recorded). Nothing new for `bug-curator`.
- Critical-settings registry carries 2026-09-28 entries for the scout configs; no canonical value changed.

## Exit condition

R1 resolved in 5.1 before P3 (rows 23–24) launches. Then: SOUND WITH CONCERNS, with R2–R5 as the
concerns.

Reviewed by: plan-reviewer
