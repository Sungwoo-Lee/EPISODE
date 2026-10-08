# Modulator input study, inside the networks: does a body-only modulator respond to felt injury, and does the hiding flow through it?

## Question (plain language)

The modulator-input study ([[NMN_INPUT_L05]]) trained four modulated agents at level 05 that differ only in what
the modulator reads:

| Variant | What the modulator reads |
|---|---|
| **N** | felt injury only |
| **I** | fullness and felt injury |
| **IT** | fullness, body temperature and felt injury |
| **X** | the outside world only: contact pain, heat around it, smell, collision, sight; no body signal |
| *reference* | everything (the standard modulated agent, the replication's level-05 seed-42 run) |

In every variant the main network still reads everything. The behaviour session reads these agents' behaviour.
This document asks what happens **inside** them. Two earlier analyses motivate it:

- The engagement check ([[MODULATOR_ENGAGEMENT_CHECK]]) found that the standard modulator barely reacts to
  felt injury at realistic levels.
- The case study ([[CASE_STUDY_L05_S42]], verdict under review) found that felt injury changes the modulated
  agent's network *less* than the ordinary agent's, and that freezing the modulator disturbs behaviour too much
  to tell which part of it matters.

This study asks three things of each variant:

1. **Does its modulator respond to felt injury?** This is measured the same way as in the engagement check.
2. **Does felt injury change its main network more or less than an ordinary agent's?** The case study measured
   this for the standard modulated agent.
3. **How much of its injury-driven hiding flows through the modulator?** The test hides felt injury from the
   modulator alone, by setting the modulator's copy of the felt-injury input to its unhurt value, while the main
   network still receives the true value. This replaces freezing. An unhurt agent's felt injury is already at its
   unhurt value, so unhurt behaviour is unchanged by construction, and the disruption that defeated the case
   study's freeze test cannot happen.

There is one seed per variant, so this is a **screen**. It describes these agents and helps decide whether
stage 2 (seeds 43 and 44) is worth training. It does not test the design. The predictions below are fixed
before any number is computed.

## Agents

- **The four input variants:** `rppo_nmninp_l05_{N, I, IT, X}_s42`.
- **Reference modulated agent:** `healrep_l05_t16quad_s42`.
- **Ordinary partner for question 2:** `healrep_l05_t1none_s42`.

Every agent trains on seed 42 and starts from the same main-network initialisation, so the comparison isolates
the modulator's input.

## Scenes and checkpoints

- **Scenes.** The replication's neutral level-05 test scenes: no animal, and a harmless wandering rabbit, at
  starting injury 0 and 70. These are the scenes the behaviour sweeps used, with the same seeds and 30 episodes
  each.
- **Checkpoints.** The nine grid points at 2, 3, …, 10 M training steps. The input runs' own checkpoint grid is
  used, and if a point is missing the nearest one is taken. The checkpoints used are recorded.

## Measures

- **Q1. Modulator injury response.** The engagement check's E1: the mean absolute change in the modulator's gain
  per unit per step. The felt-injury input follows the natural injured trace (primary); the constant 0.70 is kept
  as a stress probe. For the input variants, "the modulator's felt-injury input" is its own input slice. Variant
  X has no felt-injury input, so its value is zero by construction; that serves as a check of the tool.
- **Q2. Injury change in the main network.** The case study's Analysis 1, with the same orientation (the acting
  agent follows the natural unhurt route) and the same scale (across-state spread). Reported at the memory
  state and the memory output, as the modulated agent's shift divided by the ordinary partner's shift at the
  same checkpoint and scene.
- **Q3. Share of hiding that flows through the modulator.**
  - In the test scenes at starting injury 70 and 0, replay each modulated agent with the modulator's felt-injury
    input held at the unhurt value (0) at every step. The main network keeps the true felt-injury input.
  - **Share** = (injury effect live − injury effect with the modulator's felt injury hidden) ÷ injury effect
    live. The injury effect is injured minus unhurt bush dwell.
  - The unhurt runs must be identical to live; this is asserted, as a check of the tool.
  - Variant X has no felt-injury input, so its share is zero by construction; that serves as a second check.
  - Implementation: the observation-manipulation tool already changes inputs per step. It needs a variant that
    changes only the modulator's copy of an input, which is a small extension.

## Predictions (fixed now)

Each prediction is checked per checkpoint and counts if it holds at **at least 7 of 9**. With one seed per
variant, these are descriptive judgements for the stage-2 decision, not tests.

- **P1, body-only reading raises the modulator's injury response.** E1 (natural trace) is larger in N, I and IT
  than in the reference.
- **P2, it reverses the damping.** In at least one of N, I and IT, the memory-state shift ratio (modulated over
  ordinary) is above 1, while in the reference it is below 1, as the case study found.
- **P3, the hiding flows through the modulator.** In N, I and IT, the share in Q3 is at least 0.25 in the rabbit
  scene. In the reference it is smaller than in each of them.
- **Nesting (descriptive).** Whether adding fullness (N → I), then body temperature (I → IT), raises or lowers Q1
  and Q3.

## Revision 1 (2026-10-08, before any computation), after the plan review (NOT READY; `docs/reviews/plan_modulator_input_internals.md`)

These items override the sections above where they differ.

**Q1.**
- The felt-injury row is the engagement check's teacher-forced `trace` row, not `e1nat`, together with the
  constant 0.70; both are co-primary for P1.
- E1 is reported beside the spread of the modulator's gain (`gainsd_*`), because raw gain units differ between
  agents.
- The four runs are added to `runs.py`.

**Q2.**
- The measure is the **raw** shift of the memory state, which is bounded between −1 and 1 and so comparable
  between agents. It is compared between each modulated agent and the ordinary partner, both under the
  natural trace and under the equal dose of 0.70.
- The across-state spread is reported separately, never as a divisor in a between-agent comparison; the case
  study's review withdrew a claim built that way.
- "Damping" wording is removed throughout.
- **P2, restated:** in at least one of N, I and IT, the raw memory-state shift under the 0.70 dose exceeds the
  ordinary partner's at at least 7 of 9 checkpoints, while the reference does not. P2 gets three chances (any of
  three variants), and checkpoints within one run are strongly alike, so a pass is a hint, not a result.

**Q3, renamed the "direct-input share".**
- **Four conditions** on the same episode seeds at starting injury 70 and 0:
  - **live**;
  - **felt injury hidden from the modulator only**;
  - **hidden from the main network only**;
  - **hidden from both**.
- **Where the hiding happens.** The modulator's input is taken from the observation after log compression,
  inside the forward pass, so the hiding is done there.
  - Each agent's felt-injury column is addressed by a fixed integer index (`mod_input_idx.index(felt_col)` for
    the modulator, the observation column for the main network). This avoids passing a sensor dictionary under
    jit, which is affected by the alphabetical-order bug.
  - The training path is left unchanged and tested to be unchanged.
  - The modulator input is captured, with a check that the felt-injury column is 0 and every other column equals
    its true value.
- **Primary number:** the injured bush-dwell difference, live minus modulator-hidden, in percentage points, with a
  bootstrap interval over episodes. Each arm has **100 episodes**.
- **The share** is pooled over checkpoints, (pooled live effect − pooled modulator-hidden effect) ÷ pooled
  (live − hidden-from-both) effect. It reads "undefined" when the interval of the live injury effect includes 0.
- **The share is read only if the parts add up:** the modulator-only loss plus the main-only loss is within the
  interval of the hidden-from-both loss. Otherwise it reads "not additive: the hiding itself may disturb the
  policy".
- **Survival guard.** Survival in steps is reported per condition, and a condition that shortens injured survival
  by more than 10% is flagged.
- **Caveat.** Hiding the input does not block indirect routes: the agent's changed path, faster healing in the
  bush, and the other senses the reference modulator still reads. The share is therefore a lower bound on the
  modulator's role. The reference agent has the most such routes, so "reference smaller" is partly built in.
- **X is refused** by the tool, since it has no felt-injury input. The positive control is the hidden-from-both
  condition plus the input-capture check.
- **Precondition:** on the recorded unhurt traces, felt injury is exactly 0 at every step. This is checked
  before Q3 runs.

**Overlap with the behaviour readout.** For each checkpoint used, live dwell must equal the stage-1 sweep CSVs,
read only after the behaviour session's collation has finished. Behaviour effects are quoted from the behaviour
readout. P1–P3 inform the stage-2 judgement and are not a gate.

## Revision 1a (2026-10-08, before any computation), after the re-review (SOUND WITH CONCERNS)

- **"Undefined" rule.** The share reads "undefined" if the interval of the live injury effect includes 0, **or**
  the interval of the divisor (live − hidden-from-both) includes 0.
- **Additivity.** Bootstrap the interaction (live − mod-hidden − main-hidden + both-hidden), resampling episode
  seeds jointly across the four conditions.
  - It counts as "additive" only if the interaction's interval includes 0 **and** its half-width is under half the
    divisor.
  - Otherwise the reading is "additivity not established" and no share is read.
- **P3, restated.** In N, I and IT, the pooled share in the rabbit scene is defined, additive and at least 0.25.
  The comparison with the reference is descriptive only.
- **Input capture in every condition.** Both the modulator's input and the main network's input are captured, and
  the felt-injury column is checked to be hidden exactly where intended. The main network's column is zeroed
  after the modulator has taken its copy; for the reference agent, both read the same array.
- **Parity with the behaviour sweep.** The first 30 episode seeds of the 100 are the sweep's seeds, and parity is
  checked on that subset.
- **Smaller points.**
  - P2's "exceeds" means larger at at least 7 of 9 checkpoints. Because the reference's raw shifts are about
    equal, a pass is a hint only.
  - The share covers only the direct-input route; it is not claimed to be a lower bound.
  - The unhurt-zero check runs as an assertion on all 100 unhurt episodes.
  - A condition flagged by the survival guard is left out of the share.
- **Superseded wording.** The Question section's phrases about the main network changing "less", about
  disruption that "cannot happen", and P2's original heading are superseded by Revision 1; this section and
  Revision 1 govern.

## Outputs

Results go to `results/analysis/modinput_internals/`, with a results section appended below. The behaviour session's stage-1
readout stays the authority on behaviour; this study reports only internal measures and Q3.

## Feedback from plan-reviewer

**Verdict: NOT READY** (2026-10-08). Two Critical edits are needed before anything is computed. Full table: [[plan_modulator_input_internals]].

1. **Q2 / P2 reuse the divided shift measure that the case-study review withdrew.** The modulated agents' larger
   across-state spread makes the ratio fall below 1 almost by construction. Restate P2 on the raw memory-state
   shift (bounded units), report numerator and divisor separately, and remove the "damping" wording from the
   Question section and P2.
2. **Q3 cannot separate a route through the modulator from disruption.** When injured, the main network sees
   injury while the modulator sees none, a pairing never met in training. Add a both-hidden condition and a
   main-only-hidden condition on the same episode seeds. Read the modulator share only if modulator-only plus
   main-only adds up to both-hidden. Use both-hidden as the divisor. Add a survival-step guard.

Moderate edits:

- Report the Q3 numerator (paired difference of injured dwell, in pp) as the primary quantity. Pool the share
  over checkpoints and declare it undefined when the live effect's interval includes 0.
- Q3 needs at least 100 episodes per arm.
- Call Q3 the "direct-input share". This affects the comparison against the reference.
- Implement the hide inside the forward pass, at `mod_in`, using the column index `mod_input_idx.index(...)`.
  Do not use a sensor dict under jit. Assert on the captured `mod_in`.
- Make the X check a refusal instead of a tautology.
- For Q1, name the `trace` row. Make 0.70 co-primary for cross-agent P1 and report it next to the gain's spread.
- Assert per-checkpoint parity with the stage-1 behaviour sweep.

Open item: confirm from the recordings that felt injury is exactly 0 in the unhurt scenes.

Checkpoint alignment is fine: every run has a checkpoint within 100 steps of each grid point.

Reviewed by: plan-reviewer

## Feedback from plan-reviewer (re-review of Revision 1, 2026-10-08)

**Verdict: SOUND WITH CONCERNS.** Both Critical findings are resolved: P2 now compares the raw memory-state
shift at an equal dose, with no divisor; Q3 has the four-condition design, the additivity reading and the
survival guard. The fixed-index hiding inside the forward pass, the refusal of X, the `trace` row for Q1 and
the parity check all match the review. Six edits remain. None needs a new condition. Make them before
computing:

1. **"Undefined" rule is attached to the wrong number (Moderate).** The share's divisor is pooled
   (live − hidden-from-both), not the live injury effect. If hiding felt injury from both networks barely
   changes injured dwell, because injury acts through healing or the changed path, the divisor is near 0
   while the live effect is clearly non-zero, and the share blows up. Fix: read "undefined" when the interval
   of the divisor (live − both-hidden) includes 0. Keep the live-effect rule as well.
2. **Additivity can pass just because the intervals are wide (Moderate).** "The sum lies within the
   both-hidden interval" ignores the sum's own uncertainty, and with 100 episodes a wide interval accepts
   almost anything. Fix: compute the interaction, live − mod-hidden − main-hidden + both-hidden. Bootstrap it
   by resampling episode seeds jointly across the four conditions. Read "additive" only if its interval
   includes 0 *and* its half-width is under half the divisor. Otherwise report "additivity not established",
   not "additive".
3. **P3 was never restated (Moderate).** Revision 1 drops the per-checkpoint share, but P3 (l.86-87) still
   asks for "≥ 0.25 … at 7 of 9", which can no longer be computed. That gap leaves the threshold to be chosen
   after the data arrive. Fix: restate P3 as "in N, I and IT, the pooled direct-input share in the rabbit
   scene is defined, additive (item 2) and ≥ 0.25". State the reference comparison as descriptive only.
4. **The input-capture check covers only the modulator (Moderate).** Main-only-hidden and both-hidden change
   the main network's input, and that is not asserted. For the reference agent the modulator's input is the
   same array as the main network's input (`src/models/recurrent_ppo_network.py:584-585`, `mod_in = x`). So
   main-only-hidden must zero the column *after* the modulator's gather, or the modulator is hidden too.
   Fix: capture both inputs in all four conditions. Assert that the felt column is 0 exactly where it should
   be hidden and equals the true value everywhere else. Zeroing the flat observation column before the
   encoder is correct despite the sensor-order bug, because the encoder slices that same flat vector.
5. **Parity with the behaviour sweep vs. 100 episodes (Moderate).** The sweep has 30 episodes per scene, and
   Q3 now runs 100. State that the first 30 episode seeds are the sweep's seeds, and assert parity on that
   subset only. Otherwise the parity check cannot pass, or it gets loosened silently.
6. **The entry point still carries the withdrawn claims (Moderate, documentation framing).** The Question
   section (l.21-22: the network changes "less") and Q3 (l.32-34: disruption "cannot happen"), plus the P2
   heading "reverses the damping", are what a fresh reader sees first. The override note sits 60 lines lower.
   Fix: reword those lines in place, or strike them through with a pointer to Revision 1.

Low: (a) P2 "exceeds" has no margin. The review found the reference's raw shifts about equal, so 7 of 9
can pass by chance. Give a margin, e.g. exceeding by more than the spread between the two scenes at that
checkpoint. (b) "The share is therefore a lower bound" is not justified: disruption that adds up could
inflate it. Say "covers only the direct-input route". (c) Run the unhurt-zero precondition as an assertion
at run time on all 100 unhurt episodes. The recorded traces cover only 30. (d) Say what a survival-guard
flag does: a flagged condition's dwell difference is not used in the share.

**Cost of being wrong:** low now. Items 1-3 could still produce a "share through the modulator" that is
really noise, feeding the stage-2 decision, which is several GPU-days. Each fix is a sentence in the plan
plus a few lines in the tool.

Reviewed by: plan-reviewer

## Implementation Report (developer, 2026-10-08)

**What was built** (commit `2a37427b`, pushed to `origin/v5.0`). It covers Revision 1 and 1a.

- `src/models/recurrent_ppo_network.py`: an analysis-only `forward_hidden(x, h, mod_col, main_col)`.
  - Felt injury is set to 0 after the log compression, at fixed integer columns. The modulator column is `mod_input_idx.index(felt_col)`.
  - The modulator takes its copy first; only then is the main network's column zeroed.
  - The inputs both networks actually received are captured as `mod.in` / `main.in`.
  - `__call__` (the training path) is unchanged. Its traced-program hash is identical to the pre-edit hash on all 9 test network configurations.
- `scripts/analysis/modulator_engagement/runs.py`: new group `nmninp` with the N, I, IT and X runs at seed 42.
- `scripts/analysis/modinput_internals/{internals,measures}.py`: subcommands `precondition`, `q1`, `q2`, `q3`, `parity`, `summarize`, `score`.
- `tests/analysis/test_modinput_internals.py`: 44 tests, all passing. They cover the no-hide identity, the input-capture assertion, the refusal of X, the unhurt-zero check, the share / undefined / additivity / survival-guard arithmetic, and P1–P3.
- `docs/environment/SCRIPTS_DEPENDENCY_MAP.md`: updated.

**Regression tests.** `tests/models` plus the engagement and case-study tests: 249 passed. One test failed, and it is already recorded in Known Bugs (`test_hand_computed_breakdown_matches_the_live_environment`: stale sensor widths since `47b1b8c3`, unrelated to this change).

**Speed check: skipped.** The training forward pass traces exactly the same program as before (hash check above), so training speed cannot change.

**Collected** (on CPU in the container, the same device as the sweeps; outputs in `results/analysis/modinput_internals/`). Nine checkpoints per agent (2 … 10 M), 100 episodes per condition. Wall time about 15 minutes, with five agents in parallel.

- `precondition.json`: felt injury is exactly 0 in every recorded unhurt sweep episode (540 episodes per agent). The run-time assertion also passed on all 100 unhurt episodes in both scenes at every checkpoint.
- `parity.json`: live dwell on the first 30 seeds equals the stage-1 / replication sweep CSV at 9 checkpoints × 4 scenes for every agent. Q1's natural-episode dwell and Q2's identity dwell both equal Q3's live dwell.
- Every Q3 input-capture assertion passed.
- `q1/<agent>.csv`, `q2/<agent>.csv`, `q3/{summary.json, per_checkpoint.csv, summary_table.txt}`, `score.json`.

**Flags for the analyst.** These are facts about the data. Nothing was changed after seeing them.

1. **The no-animal scene is deterministic.** All 100 seeds give the same episode at each checkpoint, so its bootstrap intervals have zero width. Its additivity check therefore passes only if the interaction is exactly 0.
2. **The bootstrap resamples seeds only, and the checkpoints are fixed.** The rabbit-scene intervals (half-width about 0.5 pp) therefore do not include variation between checkpoints.
3. **Hiding felt injury from both networks reproduces the unhurt episodes exactly.** This held in every injured episode (1,800 per agent). In these scenes felt injury is the only way injury reaches the agent, so the divisor (live minus both-hidden) equals the live injury effect, and the indirect-route caveat is empty here.
4. **No condition shortened survival.** All episodes ran the full 100 steps, so the survival guard never fired.
5. **The raw memory shift is reported in its natural units.** It is the Euclidean length over the 128 memory units. Each unit is bounded, so the number is comparable between agents, but it is not itself in [−1, 1].

Implemented by: developer
