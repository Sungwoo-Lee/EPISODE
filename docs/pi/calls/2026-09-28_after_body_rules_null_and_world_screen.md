---
title: "PI call — after the body-rules null: where next, confirm the hidden-context worlds, and run the modulator comparison there?"
date: 2026-09-28
caller: pi
status: awaiting user decision
trigger: "Post-analysis PI consultation requested by the parent session, after experiment-analyzer + plan-reviewer on (1) the level-05 body-rules factorial (SUPPORTED WITH CAVEATS) and (2) context-exploration Part 4 and its 5 M extension (SUPPORTED WITH CAVEATS)."
inputs:
  - docs/experiments/active/level05_body_interactions/LEVEL05_BODY_INTERACTIONS.md
  - docs/experiments/active/context_exploration/STUDY_PLAN.md
  - docs/pi/calls/2026-09-26_level05_body_interactions_launch.md
  - docs/pi/calls/2026-09-27_context_exploration_part4_launch.md
  - docs/pi/PORTFOLIO.md
---

# PI call — after the body-rules null: where next?

> **Status: awaiting the user's decision.** The user was asleep and the PI had no question tool in
> this session, so the options below were returned to the parent session to put to the user. §1–§5 are
> the pre-decision framing and stay as written; §6–§8 are filled in once the user answers.

## §1 Plain-English entry point

**What happened.** Two experiments finished today.

1. **Body rules (32 runs).** We added four body rules to the campfire world — healing slows when
   hungry, healing uses up food, being too cold or too warm uses up food, food is scarcer — in all 16
   on/off combinations, and trained an ordinary agent and a neuromodulated agent (one with a small side
   network that re-tunes the main network according to how its body feels) in each. **No rule and no
   combination made the two agents behave differently.** The rules do change behaviour, sometimes a
   lot, but for both agents by the same amount. Two caveats from review: the modulated agent survived
   about 1.6 % longer in all 16 worlds, but every one of those comparisons started from the same pair of
   initial weights, so this is one comparison seen 16 times, not 16 replications; and the main hiding
   measure turned out not to read zero for an agent that simply "hides when hurt", so its zero point is
   not calibrated.
2. **Hidden-context world screen (8 + 4 runs, ordinary agent only).** We looked for worlds where food
   and predators are not always sensed — a shorter smell range or a bigger grid — but hunger, cold and
   injury still stay in balance. Three worlds passed on one training seed each and need a second seed:
   the 10 × 10 grid with smell range 3, the 10 × 10 grid with smell range 5, and the 20 × 20 grid with
   smell range 5 and many small food items. Big grids with long smell range and little food failed
   (agents barely find food). The planning simulation that proposed these worlds proved unreliable for
   choosing them (right on 2 of 6). The screen also found that the ambushers carry nothing an agent
   could usefully infer, whereas the number of hunting predators does — and a short smell range hides
   them, which is exactly where a modulator could matter.

**The three questions.** (a) What does the body-rules null mean for direction? (b) Launch the
second-seed checks on the three candidate worlds now? (c) Should the next modulator comparison be run
on the confirmed short-smell worlds?

**PI read in one line.** Stop adding body rules; confirm the three worlds now (cheap); run the next
modulator comparison there with at least three seeds, today's world included as a reference so the
survival lead is settled for free — but fix the hiding measure first, and agree now what a second null
means.

## §2 Where this sits

- **Paper line (Paper 1, unratified).** "A modulator produces state-dependent, pain-like behaviour an
  ordinary agent does not." G1 (show any modulator effect on behaviour) remains **blocked**.
- **Null count.** This is the second clean behaviour null on the modulator this month (the 16-setting
  placement grid, 7 Sept; now the 16-world body-rules screen). The candidate cause tested here — "the
  world never demanded state-dependent behaviour" — is weakened for *body rules* specifically. It is not
  yet tested for *hidden context*, which is a different reason the modulator might be idle: when
  everything is sensed, a network does not need an internal state to decide.
- **Pre-committed stop rule (2026-09-27 call).** "If no non-reference world is forwarded **and** the
  factorial is null, return to PI before any further world-design round." The factorial is null; the
  world screen has three candidates pending confirmation — so the stop rule has not fired, but we are
  one null away from it.
- **Portfolio.** Tracks remain unratified (fifth flag). Not re-raised as a question here; noted
  because a third null would make "which paper are we writing" unavoidable.

## §3 Question (a) — what the body-rules null means for direction

1. **One more body-rules round at stronger rule strengths.** Costs another ≈ 500 GPU-hours scale
   screen. Buys: rules out "too weak" as the reason. PI: not recommended — the rules already changed
   both agents' behaviour strongly; the problem is not that the world did not push, it is that the
   ordinary agent follows the push just as well.
2. **Move to hidden-context worlds (short smell range) — (Recommended).** Costs: the confirmation runs
   in (b) plus the comparison in (c). Buys: a test of a genuinely different reason the modulator could
   matter (the right action depends on something not currently sensed), using worlds already screened.
3. **Change the modulator itself or how it is trained** (what body signal it receives, an extra
   training objective that forces it to carry information, a different placement). Costs: an
   engineering plan plus a new screen; weeks rather than days. Buys: addresses the possibility that the
   modulator is idle whatever the world. PI: the right next move **if** (2) is also null; premature
   before it.
4. **Settle the survival lead first** (three or more seeds per agent in today's world, ≈ 6 runs,
   ≈ 100 GPU-hours at the body-rules budget). Buys: a clean answer to "does the modulated agent really
   survive longer". PI: worth doing, but as part of (c), not as a separate study — a standalone run
   delays the main question for a performance gap of ≈ 1.6 % with no mechanism.

**Pre-commitment asked with (a):** if the modulator comparison on hidden-context worlds is also null
(no behaviour difference beyond seed noise), we stop world-design rounds and move to option 3. The user
chose "decide after results" last time; the PI asks again because the next null would be the third.

## §4 Question (b) — launch the second-seed confirmations now?

Runs: 10 × 10 smell 3 and 10 × 10 smell 5 at 2 M episodes (≈ 2 GPU-hours each), and the 20 × 20 smell 5
world as a fresh 5 M run (≈ 10 GPU-hours; also checks that the resume point did not distort its first
verdict). Total ≈ 15 GPU-hours.

1. **Launch all three now — (Recommended).** Cheap, independent of every other decision, and the
   comparison in (c) cannot be designed without them. Node and GPU from the user.
2. **Launch only the two 10 × 10 worlds.** Saves ≈ 10 GPU-hours; drops the 20 × 20 world, which is
   the least hidden of the three (its food search is only about twice today's) and borderline on two
   balance values.
3. **Hold until (a) and (c) are decided.** Only sensible if the user expects to reject option (a)2.

## §5 Question (c) — run the modulator comparison on the confirmed short-smell worlds?

1. **Yes, properly powered — (Recommended).** Both agents, at least 3 seeds each, on every confirmed
   world (at most three) **plus today's world as a reference** — the reference arm replicates the
   survival lead as a by-product (answers (a)4 without a separate study). Two conditions before
   launch: (i) redefine the hiding measure's zero point (compare against the unhurt baseline at each
   hunger level) so a "hide when hurt" agent reads zero; (ii) pre-register one behaviour measure that
   depends on hidden context — e.g. does behaviour track how many hunting predators are around when
   none is currently smelled. Rough cost 100–150 GPU-hours (≈ 24 runs; `experiment-designer` to cost
   exactly). Buys: the first test of the hidden-context reason, with seed noise measured directly.
2. **Yes, minimal.** Only the smell-range-3 world (the least observable one that held up), 3 seeds per
   agent (≈ 6 runs). Cheaper and faster; weaker if that one world is idiosyncratic.
3. **Measure first, train later.** Build and validate the hidden-context measure on existing ordinary
   runs before designing any modulator runs. Slower by a few days; the PI folds this into option 1 as
   a pre-launch gate instead.
4. **No — go straight to changing the modulator or its training** ((a)3). Consistent only with
   rejecting (a)2.

## §5b PI read

The body-rules screen was a fair test and a clean answer: making the body's rules more interlocking
does not, by itself, separate the modulated agent from the ordinary one. A third world-design round on
body rules would be tunnelling. Hidden context is not the same bet re-rolled — it attacks a different
reason the modulator could be idle — and the world screen has already paid for it. The two costs worth
spending before that comparison are the ≈ 15 GPU-hours of confirmations and an hour-scale fix to the
hiding measure; launching a third comparison on a measure whose zero point is known to be wrong would
repeat the one real defect of this round. Pace: on time for (b); (c) is on time to *design* now and
launch once (b) reads out. The survival lead should not be cited anywhere until the reference arm of (c)
reports.

## §6 User decision

_Pending._

## §7 Rationale captured

_Pending._

## §8 Hand-off (after decision)

- **(b) Launch** → `training-runner` for the three second-seed runs (node and GPU from the user;
  pack-node-first).
- **(c) Design** → `experiment-analyzer` redefines the hiding measure's zero point on existing stores;
  `experiment-designer` drafts the modulator comparison (worlds conditional on (b)), then
  `plan-reviewer` and `env-config-reviewer`, then back to PI pre-launch.
- **Stop rule:** if the hidden-context modulator comparison shows no behaviour difference beyond seed
  noise, return to PI for a move to the modulator or its training (option (a)3) — no further
  world-design round (subject to the user's pre-commitment answer).
