---
title: "PI call — launch the 32-run body-rules screen as designed, add a noise check, or stage it?"
date: 2026-09-26
caller: pi
status: awaiting-user-decision
trigger: "Pre-launch PI consultation requested by the parent session, after experiment-designer (Revision 2), env-config-reviewer (GO WITH NOTES) and plan-reviewer (SOUND WITH CONCERNS, resolved)."
inputs:
  - docs/experiments/active/level05_body_interactions/LEVEL05_BODY_INTERACTIONS.md
  - docs/pi/calls/2026-09-01_sensor_ladder_replication.md
  - docs/pi/PORTFOLIO.md
  - docs/project/project_plan.md
---

# PI call — launch the 32-run body-rules screen as designed, add a noise check, or stage it?

> **Status: awaiting the user's decision.** The PI's question tool was not available in this
> session, so the options below were returned to the parent session to put to the user. §5–§7
> are filled in once the user answers; §1–§4 are the pre-decision framing and stay as written.

## §1 Plain-English entry point

**The question.** In the campfire world, the ordinary agent and the agent with a
neuromodulator (a small side network that re-tunes the main network according to how the body
feels) ended up with the same simple habit: when hurt, go to a bush and rest. That habit is right
no matter how hungry or cold the agent is, so the neuromodulator has nothing to add. The planned
experiment adds four body rules that should make the right action depend on *several* body states
at once — healing slows when hungry, healing uses up food, being too cold or too warm uses up food,
and food is scarcer — and trains both agents in all 16 on/off combinations: 32 main runs, one
training seed each, after about 18 short calibration runs.

**Why a PI call.** The experiment is sound and the user chose the full 16-world design
knowingly; this call does not reopen that. It asks two narrower questions. First, the simulation
that was supposed to say which rule matters most no longer favours any rule after a measurement
error was corrected, so the screen is looking for effects that may be small, with one training
run per world — how will we tell a real effect from re-training noise? Second, the project has
already had one clean null this month (the 16-configuration modulator placement grid, 7 Sept): no
modulator setting changed behaviour beyond an ordinary agent. If this screen is also null, what do
we conclude?

**Where it sits.** This is the most direct test yet of one candidate reason the modulator has not
shown an effect: *the world never demanded state-dependent behaviour.* That puts it squarely on
Paper 1's line (a modulator that produces pain-like behaviour an ordinary agent does not).

## §2 Costs as designed

- Calibration: 18 short runs, about 36 GPU-hours.
- Main screen: 16 × ~14 h (ordinary) + 16 × ~18 h (modulated) ≈ 510 GPU-hours — about a day on
  the ~30 free GPUs.
- Recordings for analysis: up to ≈ 2.6 TB on the NAS (≈ 31 TB free).

## §3 Options put to the user

**Question 1 — how to spend the compute**

1. **Launch exactly as designed.** Buys the full screen fastest. Cost: ≈ 550 GPU-hours. Weakness:
   the only estimate of "how much would this number move if we simply trained again" comes from
   the pattern of the 16 results themselves, which is least reliable when many effects are small
   and none stands out — the situation the corrected simulation now predicts.
2. **As designed, plus four repeat runs (PI recommendation).** Re-train the no-rules world and the
   all-four-rules world with a second seed, for both agents. Cost: about +64 GPU-hours (≈ 12 %),
   launched alongside, no delay. Buys a direct, measured size for re-training noise at the two
   worlds that matter most, so a "this rule widens the gap" claim can be checked against it.
3. **Extremes first.** After calibration, train only the no-rules and all-rules worlds, both
   agents, three seeds (12 runs, ≈ 190 GPU-hours). Run the other 14 worlds only if the all-rules
   world opens a gap. Saves ≈ 60 % if nothing happens; costs about a day's wait if something does;
   departs from the full screen the user chose.
4. **Hold until the discount question is settled.** The agent currently values a reward 40 steps
   ahead at about 0.13 of its face value (discount 0.95); whether that is right was left open on
   27 July and still is. The simulation's own check at a longer-sighted discount (0.99) reshuffles
   which rules help. Buys runs that do not need redoing if the discount changes; costs an
   open-ended delay on a question nobody is currently working.

**Question 2 — what a null result means (decided now, before the data)**

1. **Stop adding body rules (PI recommendation).** If no rule widens the gap between the two
   agents beyond the noise margin, record "the world was not the bottleneck" and move effort to the
   modulator itself or how it is trained. Reason: that would be the second clean null in a row, and
   a third world-design round would be tunnelling.
2. **One more round at stronger rule strengths**, then decide.
3. **No pre-commitment** — decide after seeing the results.

## §4 PI read

Option 1.2 is recommended because the cost is small next to the risk it removes: with one
seed and a simulation that no longer predicts a winner, the screen's most likely failure is a
noise-driven "effect" that gets written up. Option 1.4 is honest about a real open question but is
not recommended: the discount question has been open two months with no owner, and holding on it
is indecision, not caution. The screen's per-rule finding would still guide a follow-up at any
discount. Option 2.1 is recommended so that a null is a finished answer rather than an invitation
to redesign the world again.

## §5 User decision

_Pending._

## §6 Rationale captured

_Pending._

## §7 Hand-off

- **Next agent (after decision):** `experiment-designer` if repeat runs or staging are chosen (add
  rows/configs to §3 of the design); otherwise straight to `training-runner` for the stage-1
  pilots (node and GPU collected from the user first).
- **Stop rule:** as chosen in Question 2.
