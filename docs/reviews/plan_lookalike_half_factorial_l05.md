# Plan review: lookalike half-factorial at level 05

Reviewed by: plan-reviewer, 2026-10-11
Object: [[LOOKALIKE_HALF_FACTORIAL_L05]] (experiment design + 7 world configs, 14 planned runs)

## Verdict

**NOT READY.** The worlds and the launch block are sound. The weak part is the rule that decides
which of the four groups of world changes is "worth replicating". As written, that rule can
pass a group without ever testing what the study asks, which is whether hiding versus foraging
becomes a real choice:

1. **The pass rule is met automatically for two groups.** Having fewer predators (group A) cuts
   predator deaths, and having more food (group B) cuts starvation deaths. Both of these clear the
   pre-set "5 percentage points on any ending" bar whatever the agent learns. The user's headline
   problem, being killed while foraging, appears in none of the pass criteria.
2. **Time in a bush mixes hiding with healing.** The user raised this confound, and the design does
   not remove it. The concealment test (group C) compares how much time the agent spends in a bush
   after a trap hit (25–60 damage) with the same after a rock hit (1–5 damage). A bigger wound means
   more bush healing, so a large gap is guaranteed. The comparison also never uses the
   visible-hazard worlds, so it is not a measure of concealment at all.

Both fixes are edits to the design document only. No config changes and no extra runs are needed,
so the launch date can hold.

## Critical findings

| # | Location | Issue | Fix | Owner |
|---|---|---|---|---|
| C1 | §Outcome measures, "Group effect" rule | The rule is an OR across about 10 readouts, and A and B pass it mechanically: halving the maximum predator count lowers the predator-death share, and 4.5× more food per item lowers the starvation share. Measure 2 (predator deaths while foraging) feeds no criterion. The screen therefore cannot tell "this group creates a real choice" apart from "this group changes the death mix". | Pre-register **one primary behavioural readout per group**, defined so that a choice is visible. Examples: the share of predator deaths that happen while foraging (a share, not a per-state rate, because A lowers every rate); hiding share = bush steps with injury 0, conditioned on an animal being in view; the injury × animal-type interaction (rabbit only vs no animal) from the hypervigilance signature. Demote the endings mix to a descriptive readout. | experiment-designer |
| C2 | §Outcome measures 3 and 4; the C criterion | Bush healing applies only on a step where the agent **rests** in a bush and takes no damage (`src/environment/core.py` ≈ lines 383 and 431, `can_recover = rested & applied_inc <= 0`). The split at injury ≤ 25 vs > 25 leaves the healing motive in the lower band too. The C criterion (trap-minus-rock post-hit bush share ≥ 10 pp in C+ worlds) compares wounds whose sizes differ about 10×, so the healing need alone clears it, and it uses no C− worlds, so it is not a C effect. | Hiding = bush steps at injury 0, or bush steps **without** the rest action. Healing = rest-in-bush at injury > 0. Report both. For surprise, compare **rock hits in C+ worlds with rock hits in C− worlds**: same 1–5 damage, and the only difference is whether the hit could be predicted. Keep trap-minus-rock only as a difference-in-differences (C+ minus C−), matched on injury after the hit. | experiment-designer |

Exit condition: rewrite the pass rule so C1 and C2 are resolved. The verdict then becomes
SOUND WITH CONCERNS, with the Moderate findings (returned inline to the caller) left for the user
to accept or fix.

## Cost of being wrong

The cost is not lost compute. It is ~205 GPU-hours that produce a confident "A and B (and C) are
worth replicating". That screen result would then drive a 3-seed replication and the level-06 copy
of the design, both resting on effects that were built into the worlds rather than learned.

---

## Re-review of the revised design (2026-10-12)

Reviewed by: plan-reviewer

### Verdict

**NOT READY, by one narrow Critical.** C2 is resolved. C1 is resolved for the threat, concealment
and hazard-load groups, but not for the food group. Its primary readout is the share of predator
deaths that happen while eating. Bigger food items cut eating time by design, so that share falls
with no change in what the agent learns. The design's text already says the death share must be
read against the time share, but the pass rule does not do that. The 20-death minimum makes the
same readout too noisy in the safest worlds. Both fixes are text edits to the pass rule.

### Status of the original Criticals

| # | Status | Note |
|---|---|---|
| C1 | **Partly open (food group)** | Threat, concealment and hazard load now have readouts that the world change cannot move on its own. Food does not (R1). |
| C2 | **Resolved** | Hiding and healing are split using the rest-action condition in `core.py`. Concealment is measured on rock hits, hidden versus visible worlds, with the same 1–5 damage. Trap-minus-rock appears only as a difference-in-differences matched on injury. One bush rest step heals 5 points, more than a rock does, so the split adds at most one step of bias per event. |

### Critical

| # | Location | Issue | Fix | Owner |
|---|---|---|---|---|
| R1 | §Primary readouts, food row; §Failure modes, the 20-death minimum | Under bigger food items a meal is about 7 eating steps instead of about 25, so the time in "ate within the last 20 steps" drops by construction. The death share in that state then drops with it, and the group passes on a change built into the world. Separately, a 20-death floor gives a share with about ±11 percentage points of sampling error (at a share near 0.5), well above any seed-to-seed σ measured on runs with hundreds of deaths. The worlds most likely to fall short (4 and 8, the safest) are food-group worlds, so the group can also fail for lack of data exactly where it works. | Make the primary readout time-normalised: the risk ratio (deaths in the state ÷ steps in the state) ÷ (the same for all other out-of-bush steps). A ratio within a world also cancels the overall predator rate, which was the reason a share was chosen. Raise the floor to about 100 deaths by extending evaluation episodes until it is met (with a cap), or add the sampling variance to the bar. | experiment-designer |

Exit condition: fix R1 and the verdict becomes SOUND WITH CONCERNS. The other findings from
this round were returned inline to the caller.

## Final verdict (2026-10-12, third pass)

**SOUND WITH CONCERNS.** R1 is resolved. The food readout is now a risk ratio within each world,
with at least 100 deaths (10 per state), evaluation extended up to 20,000 episodes, and sampling
error included in the bar. The bar formula is correct, provided the two agents' seed noise is
independent. They share the seed and the world, so if their noise is correlated the bar
(2 × SD, which equals σ when sampling error is negligible) works out nearer 1.4 standard errors
than 2: acceptable for a screen. Remaining items are for the user, not defects:

- R6, whether to rebuild the test scenes for each world, is still open.
- Whether to launch given the planner's "no real choice" result is a question for `pi` and the
  user.
- The analysis tooling and the extended evaluation must exist before any contrast is read.

Reviewed by: plan-reviewer
