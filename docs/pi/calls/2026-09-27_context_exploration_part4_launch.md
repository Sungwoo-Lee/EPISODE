---
title: "PI call — launch context-exploration Part 4 (8 ordinary-agent training runs on 7 worlds) now, or wait for the body-rules factorial analysis?"
date: 2026-09-27
caller: pi
status: decided
trigger: "Pre-launch PI consultation requested by the parent session after experiment-designer (Part 4 design + Revision 1), plan-reviewer (SOUND WITH CONCERNS, all findings applied) and env-config-reviewer (GO WITH NOTES)."
inputs:
  - docs/experiments/active/context_exploration/STUDY_PLAN.md
  - docs/pi/calls/2026-09-26_level05_body_interactions_launch.md
  - docs/pi/PORTFOLIO.md
---

# PI call — launch context-exploration Part 4 now, or wait for the body-rules factorial analysis?

## §1 Plain-English entry point

**The question.** A neuromodulator should matter most when the right action depends on something the
agent cannot sense right now. In today's campfire world almost nothing is hidden (small grid, smells
reach everywhere). A simulation (no training) picked candidate worlds that are bigger and/or have a
shorter smell range, so food must actually be searched for, while hunger, cold and injury still stay
in balance. Part 4 trains the **ordinary agent (no modulator)** on seven of these worlds — today's
world twice as the yardstick, four the simulation calls balanced, two just past its predicted edge —
8 runs, about 2–4 GPU-hours each (roughly 25–30 GPU-hours total). It does two things: screens worlds
for a later modulator comparison, and checks whether the simulation's "balanced" map can be trusted.

**Why a PI call.** It is a multi-run launch. The only portfolio-level question is sequencing: the
32-run body-rules experiment (four body rules switched on/off, both agents) finishes tonight and its
analysis is pending. Should Part 4 wait for it?

**Verdict: proceed now.** Part 4 does not depend on the body-rules result.

## §2 Strategic read

- **Independence.** Part 4 trains only the ordinary agent on today's body rules; nothing in its design
  or read-out uses the factorial's outcome. Waiting buys no information for Part 4 itself.
- **Where the two studies do meet: the next modulator comparison.** Both are world-design threads
  testing the same candidate cause of the modulator null — "the world never demanded state-dependent
  behaviour". The factorial varies *body rules*; Part 4 varies *observability*. The modulator
  comparison that Part 4's §4.6 would forward to should be designed only after **both** are read, so
  that the chosen worlds can carry whichever body rules (if any) the factorial flags. This is the one
  sequencing constraint, and it is downstream of this launch, not on it.
- **Cost / opportunity.** ~25–30 GPU-hours is small (≈ 5 % of the factorial's ≈ 550), well inside an
  exploration buffer. The simulation-trust verdict (§4.5) has value on its own: it decides whether
  future world choices can go through the cheap simulation or must go through training.
- **Pace.** On time. Delaying costs a day for no gain.
- **Watch item (not a blocker).** Two world-design threads are now running at once. If the factorial
  comes back null and Part 4 also forwards no world, that is a third world-side null; at that point the
  PI will recommend moving effort to the modulator itself or its training rather than a further
  world-design round (consistent with the recommendation made, and deferred by the user, on 2026-09-26).
- **Anchors.** Paper 1 line (modulator yields state-dependent, pain-like behaviour an ordinary agent
  does not); G1 still blocked on showing any modulator effect; tracks in PORTFOLIO.md remain unratified
  (fourth flag, not re-raised here).

## §3 Options considered

1. **Proceed now (chosen).** Costs ~25–30 GPU-hours; buys world screening + sim-trust verdict a day earlier.
2. **Wait for the factorial analysis.** Costs ~1 day; buys nothing for Part 4, since its design is fixed and independent.
3. **Fold Part 4 into the next modulator study.** Saves the ordinary-only screen but loses the
   pre-registered world screen and sim-trust test; not recommended.

No user decision is needed; the user already asked for this training ("let's test this as well with
real training"; "Based on the simulation, you can select proper design for the training. Then proceed").

## §4 Decision

**Proceed as designed** (Part 4 design + Revision 1, 8 runs × 2 M episodes).

## §5 Hand-off

- **Next agent:** `training-runner` (node + GPU collected from the user first; stagger launches ≥ 2 s
  per Revision 1 §R1.7; pack-node-first around the factorial's tail).
- **Downstream constraint:** the modulator comparison forwarded under §4.6 is designed by
  `experiment-designer` only after both the Part 4 read-out and the body-rules factorial analysis exist.
- **Stop rule / return to PI:** if no non-reference world is forwarded **and** the factorial is null,
  return to PI before any further world-design round.
