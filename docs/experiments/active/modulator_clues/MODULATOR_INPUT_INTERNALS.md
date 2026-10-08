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

## Results, Analysis and Verdict (experiment-analyzer, 2026-10-08)

### Verdict in plain language

This is a **stage-1 screen with one trained agent per variant**. It describes these particular agents and informs
whether seeds 43 and 44 are worth training. It is **not** a confirmed result.

**None of the three predictions fixed before the data was computed came true as scored.**

- **P1 not met.** P1 predicted that a modulator reading only body signals would respond more strongly to felt
  injury than the standard modulator, which reads everything. It does not. In raw gain units its response is
  smaller at almost every checkpoint.
- **P2 not met.** P2 predicted that, in at least one body-only variant, a fixed dose of felt injury would move
  the main network's memory more than it moves an ordinary agent's memory. It does not. All three variants
  move it less.
- **P3 not met.** P3 predicted that at least a quarter of the injury-driven hiding flows through the
  modulator's own copy of felt injury. This could not be read. Under the pre-registered rule, a share is read
  only if the routes add up, and they never added up closely enough.

Under that scoring, however, there is a consistent pattern. In the agent whose modulator reads felt injury only
(variant N), hiding felt injury from the modulator alone lowers the injured agent's bush dwell by 10.2 percentage
points [9.5, 10.8] with the harmless rabbit present, and lowers it at **all 9** checkpoints. Hiding felt injury
from the main network alone changes almost nothing. This is **consistent with** the agent routing its
injury-driven hiding through the modulator, **or with** disruption when the modulator alone is blind, a pairing
the agent never met in training. The data do not separate the two (§3). The agent that also reads fullness
(variant I) shows the same direction at 9 of 9 checkpoints.

The single reference agent behaves differently. Each network's copy of felt injury, when the other is hidden, is
followed by about the full injury hiding, and with both copies present, hiding the modulator's copy *raises*
hiding. These conditions are also never-trained pairings, so this too is consistent with redundancy or with
disruption.

The routes do not add up, so no share is read. All of this describes one seed per agent.

### 1. Pre-registered scores, exactly as written

Scored by `measures.py score` (`score.json`). Each prediction must hold at at least 7 of 9 checkpoints. Nothing
below is re-scored.

| Prediction (plain meaning) | N (felt injury only) | I (fullness + felt injury) | IT (all body signals) | Reference | Outcome |
|---|---|---|---|---|---|
| **P1**: the modulator's gain responds more to felt injury than the reference's (E1, the mean absolute change in gain per unit per step when only the felt-injury input changes). The natural recorded injury trace (`trace`) and a constant 0.70 are co-primary. | trace 0/9, 0.70 5/9 | trace 2/9, 0.70 0/9 | trace 0/9, 0.70 0/9 | — | **not met** |
| **P2**: the raw shift of the memory state under the 0.70 dose exceeds the ordinary partner's at ≥ 7/9 checkpoints in at least one of N/I/IT, while the reference does not | 2/9 | 0/9 | 1/9 | 2/9 | **not met** |
| **P3**: in the rabbit scene, the pooled direct-input share is defined, the routes add up ("additive") and the share is ≥ 0.25, in each of N, I and IT | additivity not established | additivity not established | additivity not established | (descriptive) | **not met** |

**Checks of the tool, all passed** (Implementation Report): parity with the stage-1 and replication behaviour
sweeps at 9 checkpoints × 4 scenes per agent; the input-capture assertions in all four conditions; felt injury
exactly 0 in every unhurt episode; and the refusal of X.

**Limitation: the survival guard was not a test here.** Every one of the 28,800 episodes reached the episode cap
of **101 steps** in every condition. It was not verified that starting injury 70 can end an episode within 101
steps under any policy. If it cannot, the guard could not have fired. "The guard never fired" is therefore not
evidence that the hiding conditions leave the policy intact. The Implementation Report says "100 steps"; the
`inj_survival_*` columns read 101.0, and dwell is counted over 101 steps, so one step is 0.99 pp. Variant X has
no felt-injury input and is not covered by Q1 or Q3, so this study cannot make the internal IT-vs-X contrast.

### 2. Q3: how much of the injury-driven hiding goes through the modulator's copy of felt injury

**Conditions.** Each agent is replayed on the same 100 episode seeds at starting injury 70 and 0, under four
conditions:

- **live**;
- **mod-hidden**: the modulator's copy of felt injury is held at 0;
- **main-hidden**: the main network's copy is held at 0;
- **both-hidden**: both copies are held at 0.

**Terms.**

- **Injury effect**: injured minus unhurt bush dwell, in pp.
- **Numerator**: the live effect minus the mod-hidden effect.
- **Interaction**: live − mod-hidden − main-hidden + both-hidden. It is 0 when the losses from the two separate
  hidings add up to the loss from hiding both.

**Pooled over 9 checkpoints, rabbit scene** (`q3/summary.json`; CIs are the pre-registered seed bootstrap):

| Agent | live | mod-hidden | main-hidden | both-hidden | numerator [95 % CI] | interaction [95 % CI] | half the divisor | point share (not readable) |
|---|---|---|---|---|---|---|---|---|
| N | 11.9 | 1.8 | 11.9 | 0.0 | **10.2** [9.5, 10.8] | −1.7 [−2.1, −1.2] | 6.0 | 0.85 |
| I | 15.2 | −2.3 | 15.4 | 0.0 | **17.5** [16.6, 18.3] | 2.1 [1.3, 2.9] | 7.6 | 1.15 |
| IT | 8.1 | 4.8 | 8.4 | 0.0 | **3.3** [2.4, 4.1] | −5.1 [−5.6, −4.6] | 4.0 | 0.41 |
| reference | 8.2 | 10.5 | 7.9 | 0.0 | **−2.3** [−2.6, −2.0] | −10.2 [−10.6, −9.7] | 4.1 | −0.28 |

**Per checkpoint, rabbit scene** (`q3/per_checkpoint.csv`). Each cell is the numerator [seed-bootstrap CI] /
the interaction, in pp.

| Checkpoint | N | I | IT | reference |
|---|---|---|---|---|
| 2 M | 7.3 [6.5, 8.1] / −5.6 | 59.9 [56.8, 62.6] / −3.4 | 32.1 [27.3, 36.9] / 1.2 | 0.7 [−0.6, 1.8] / −11.1 |
| 3 M | 23.3 [19.0, 27.4] / −1.8 | 16.4 [13.6, 19.1] / 2.1 | 18.9 [16.9, 20.9] / 0.4 | −1.5 [−1.8, −1.1] / −12.8 |
| 4 M | 11.5 [9.5, 13.6] / −0.1 | 12.6 [11.6, 13.6] / 2.3 | −0.3 [−2.1, 1.8] / −5.8 | −0.3 [−0.7, 0.1] / −11.1 |
| 5 M | 17.0 [15.7, 18.5] / 0.5 | 4.9 [3.8, 6.0] / −3.1 | −25.8 [−28.3, −23.3] / −26.4 | −2.8 [−3.1, −2.5] / −13.3 |
| 6 M | 4.5 [3.0, 6.0] / 0.8 | 13.7 [13.2, 14.3] / 0.1 | −3.3 [−5.0, −1.7] / −2.7 | −4.6 [−5.3, −3.9] / −12.5 |
| 7 M | 2.1 [0.3, 3.8] / 1.7 | 14.7 [14.0, 15.5] / 0.4 | −0.1 [−1.3, 1.0] / −0.1 | −8.8 [−9.9, −7.8] / −17.2 |
| 8 M | 12.4 [10.8, 14.1] / −4.3 | 5.9 [3.0, 8.6] / 3.2 | −0.5 [−1.5, 0.5] / −0.5 | −3.1 [−4.1, −1.9] / 0.5 |
| 9 M | 4.8 [4.1, 5.6] / −2.7 | 8.3 [6.5, 10.0] / 0.2 | 9.0 [8.1, 9.8] / −2.3 | −3.0 [−4.1, −1.9] / −8.8 |
| 10 M | 8.6 [7.4, 10.0] / −3.7 | 20.8 [17.0, 24.4] / 17.0 | −0.6 [−2.3, 0.9] / −9.9 | 2.7 [1.4, 4.1] / −5.1 |
| **numerator > 0 / < 0** | **9 / 0** | **9 / 0** | 3 / 6 | 2 / 7 |
| interaction > 0 / < 0 | 3 / 6 | 7 / 2 | 2 / 7 | 1 / 8 |

**Reading.**

- **N.** At every checkpoint, hiding the modulator's copy of felt injury lowers injured hiding. The size varies
  with the checkpoint, from 2.1 to 23.3 pp. The seed-only CIs (±0.5 to ±4 pp) are much narrower than this
  spread.
- **I.** The direction is the same at every checkpoint. The pooled mean is inflated by 2 M, where the live
  effect is 63 pp, and by 10 M.
- **IT.** The direction is not stable: 6 of 9 checkpoints are negative. The pooled value is carried by 2 M and 3 M.
- **Reference.** The numerator is negative at 7 of 9 checkpoints.

**The no-animal scene** (deterministic, see fact 1 below) points the same way. The numerator per checkpoint is
positive at 9/9 for N, 9/9 for I, 6/9 for IT, and 3/9 for the reference (5 negative, 1 zero). The pooled
numerators are N 17.6, I 15.5, IT 11.8 and reference −0.9 pp. The pooled interactions are N 3.6, I 0.7,
IT −2.1 and reference −9.8 pp.

### 3. The three facts the developer flagged

**Fact 1: the no-animal scene is deterministic.** All 100 seeds give the same episode at each checkpoint, so every
interval there has zero width. "Additive" requires the interval to include 0, so in this scene it can pass only if
the interaction is exactly 0.

- **Verdict on the no-animal "not additive" result: uninformative for I; real at one checkpoint each for N
  (8 M) and IT (6 M); real for the reference.** It is not an artefact as a whole.
  - **The interactions themselves are real.** They are exact for these 9 deterministic episodes.
  - **I: uninformative.** I's pooled interaction is 0.7 pp, an average of less than one step's dwell (0.99 pp)
    per checkpoint. Its per-checkpoint values are 0 to 3 pp.
  - **N: real at 8 M.** N's pooled 3.6 pp is carried by one genuinely non-additive checkpoint (8 M, +28.7 pp);
    the other eight lie within ±5 pp.
  - **IT: real at 6 M.** IT's pooled −2.1 pp is carried by 6 M (−10.9 pp). It stays non-additive when
    checkpoints are resampled (−2.1 [−4.6, −0.3]).
  - **Reference: real.** Its −9.8 pp is negative at 8 of 9 checkpoints and matches the rabbit-scene value.
  - **The magnitude comparison is post hoc.** Comparing these interactions with half the divisor (I 7.5, IT 6.5,
    N 6.9, reference 4.7 pp) or with a one-step tolerance is a test chosen after seeing the data. It is not the
    pre-registered criterion.
- **No pre-registered score depends on this scene.** P3 is scored in the rabbit scene only.
- **The rule stays as written.** The pre-registered rule cannot be changed after the data have been seen. It can
  only be annotated, as here. A stage-2 design that keeps a deterministic scene must fix a tolerance (for example,
  one step per checkpoint) **before** its data exist.

**Fact 2: the CIs resample seeds and hold checkpoints fixed.** The rabbit-scene intervals (about ±0.5 pp) describe
episode noise at these 9 fixed checkpoints. They do not describe how much the agent changes between checkpoints,
which is much larger: the per-checkpoint numerators above range over about 20 pp for N and 55 pp for I.

- **The checkpoint-wise statistics are in the per-checkpoint table above:** the numerator is positive at 9/9
  checkpoints in N and in I, 3/9 in IT and 2/9 in the reference.
- **Annotation only, not a score.** I resampled the 9 checkpoint values (20,000 draws). The rabbit-scene
  interaction intervals become:
  - N: −1.7 [−3.3, −0.2]; it still excludes 0;
  - I: 2.1 [−0.9, 6.3]; it would now read "additive", with a point share of 1.15;
  - IT: −5.1 [−11.1, −0.8];
  - reference: −10.2 [−13.1, −6.7].
- **The P3 outcome rests on IT.** The plan-reviewer ran a joint seed × checkpoint bootstrap. Its rabbit-scene
  interactions are N −1.7 [−3.4, −0.03], I 2.1 [−1.1, 6.5] and IT −5.1 [−11.3, −0.9]. IT's half-width (5.2)
  exceeds half its divisor (4.0). So under any wider resampling IT fails the half-width clause, and P3 stays not
  met because of IT. N's exclusion of 0 is marginal.
- **This annotation is weak in its own right.** It uses 9 strongly correlated checkpoints from one training run.
  It is not a substitute for seeds.

**Fact 3: hiding felt injury from both networks reproduces the unhurt episodes exactly** (all 1,800 injured
episodes per agent; both-hidden effect 0.0 in every row). Felt injury is the only way injury reaches these agents
in these scenes, so the divisor (live − both-hidden) equals the live injury effect. Main-hidden is also close to
live in every agent: within 2 pp at 65 of the 72 agent × scene × checkpoint cells. Exceptions: I rabbit at
4 M and 8 M (+2.5, −4.1), IT no-animal at 6 M (−7.9), IT rabbit at 10 M (−2.1), and the reference no-animal at
4 M, 8 M and 10 M (+4.0, +3.0, −5.0). Pooled,
live − main-hidden is at most 0.9 pp in absolute value in every agent × scene. It follows that

$$\text{interaction} = (\text{live} - \text{main-hidden}) - (\text{mod-hidden} - \text{both-hidden}) \approx -\,\text{mod-hidden effect}.$$

So "additive" here effectively asks whether the main network's own copy of felt injury produces **no** hiding
when the modulator is blind. When it produces some, the rule calls the routes non-additive.

**What the reference agent's numbers mean.** I checked these against `q3/summary.json`. Pooled over the rabbit
scene:

| Condition | Injury effect | What it means |
|---|---|---|
| live | 8.2 pp | the ordinary injury effect |
| main-hidden | 7.9 pp | with only the modulator's copy, about the whole effect remains |
| mod-hidden | 10.5 pp | with only the main network's copy, the whole effect and **more** |
| both-hidden | 0.0 pp | with no copy, the agent behaves as if unhurt |

- **Consistent with redundancy.** When either copy of felt injury is hidden alone, the injured agent still hides
  about as much as live. Hiding both removes all 8.2 pp.
- **That is what the −10.2 pp interaction measures.** The separate losses sum to −2.3 + 0.3 = −2.0 pp, against a
  joint loss of 8.2 pp.
- **The negative numerator.** It is −2.3 pp, negative at 7 of 9 checkpoints (from −8.8 to −0.3). When the
  reference modulator alone is blind to felt injury, the injured agent hides *more* than live. In plain words,
  hiding felt injury from this modulator alone moves behaviour in the opposite direction to the injury itself.
  One reading is that the modulator's copy tempers hiding when the main network also sees the injury.
- **Disruption caveat.** For the reference too, mod-hidden and main-hidden are pairings the agent never met in
  training. "Redundancy" and "the modulator's copy tempers hiding" are therefore readings, not established
  mechanisms. Disruption by the unfamiliar pairing would also explain them.
- **The pattern breaks at 8 M.** At 8 M the live effect is −2.0 pp and the interaction is +0.5 pp.
- **"Share −0.28" is not a quantity to interpret.** Without additivity there is no share.

The body-only variants match the reference in one direction: main-hidden ≈ live. The other direction differs.
In N, with the modulator blind, the injury effect drops to 1.8 pp, against the reference's 10.5 pp. In I it
drops to −2.3 pp.

**One reading the data do not settle.** "The main network's copy is weak without the modulator" could mean either
of two things:

- learned routing: the main network uses felt injury only through the modulator's gain, which is a
  multiplicative interaction that FiLM supports;
- disruption: the never-trained pairing "main sees injury, modulator does not" breaks the policy.

**The weak argument, withdrawn as evidence.** The opposite pairing (main-hidden) leaves behaviour close to live.
This is exactly what routing predicts, and disruption could be specific to one pairing. It therefore separates
almost nothing.

**A more direct check: reversion to unhurt behaviour.** I counted the share of injured episodes whose bush dwell
exactly equals the same seed's unhurt dwell at the same checkpoint, from `q3/<agent>_episodes.csv`, rabbit scene,
900 episodes per condition. The figure in parentheses restricts to episodes where unhurt dwell is above 0.

| Agent | live | mod-hidden | main-hidden | both-hidden | mod-hidden per checkpoint (2 … 10 M) |
|---|---|---|---|---|---|
| N | 5 % (5 %) | **32 % (29 %)** | 5 % | 100 % | 4, 62, 15, 78, 54, 14, 43, 9, 7 % |
| I | 3 % (3 %) | **40 % (21 %)** | 4 % | 100 % | 83, 54, 88, 10, 80, 10, 13, 15, 4 % |
| IT | 9 % (11 %) | **39 % (33 %)** | 10 % | 100 % | 54, 81, 18, 1, 16, 75, 68, 30, 4 % |
| reference | 2 % (2 %) | 3 % (3 %) | 1 % | 100 % | 0, 0, 0, 0, 0, 0, 24, 2, 2 % |

- **What it shows.** When the body-only agents' modulator alone is blind, the injured agent often does exactly
  what it does unhurt. It does not usually produce some third, new behaviour. The reference agent's mod-hidden
  episodes almost never match their unhurt twins.
- **What it does not separate.** Learned routing predicts reversion to unhurt behaviour. So does a disruption in
  which the unfamiliar pairing silences the main network's response to felt injury. The check rules out only a
  form of disruption that produces new, erratic behaviour, and only for the matching episodes.
- **Further limits.** The match is on dwell only, not on the step-by-step path. It varies widely between
  checkpoints (4–78 % in N). At most checkpoints most mod-hidden episodes do not match.
- **Next check.** A step-by-step trajectory-identity check of mod-hidden against unhurt would tighten this
  cheaply.

The reading remains post hoc.

### 4. Q1: does the modulator respond to felt injury? (E1, per checkpoint)

From `score.json` `Q1_table`: E1 of the gain averaged over the four non-critic sites (`mean4`), with the gain's
across-unit spread (`gainsd`) beside it.

| Checkpoint | N trace / 0.70 / gainsd | I trace / 0.70 / gainsd | IT trace / 0.70 / gainsd | Reference trace / 0.70 / gainsd |
|---|---|---|---|---|
| 2 M | 0.028 / 0.281 / 0.29 | 0.028 / 0.249 / 0.33 | 0.026 / 0.220 / 0.35 | 0.030 / 0.253 / 0.42 |
| 3 M | 0.029 / 0.310 / 0.33 | **0.114** / 0.271 / 0.35 | 0.029 / 0.250 / 0.38 | 0.036 / 0.288 / 0.47 |
| 4 M | 0.032 / 0.334 / 0.33 | **0.112** / 0.297 / 0.36 | 0.032 / 0.270 / 0.39 | 0.039 / 0.325 / 0.49 |
| 5 M | 0.029 / 0.293 / 0.34 | 0.033 / 0.275 / 0.37 | 0.035 / 0.278 / 0.41 | 0.040 / 0.335 / 0.51 |
| 6 M | 0.032 / 0.321 / 0.34 | 0.033 / 0.273 / 0.38 | 0.035 / 0.284 / 0.43 | 0.042 / 0.352 / 0.55 |
| 7 M | 0.031 / 0.301 / 0.35 | 0.034 / 0.289 / 0.37 | 0.035 / 0.289 / 0.47 | 0.042 / 0.348 / 0.55 |
| 8 M | 0.030 / **0.602** / 0.36 | 0.032 / 0.278 / 0.39 | 0.033 / 0.273 / 0.48 | 0.043 / 0.347 / 0.56 |
| 9 M | 0.030 / 0.306 / 0.37 | 0.033 / 0.287 / 0.39 | 0.035 / 0.288 / 0.49 | 0.044 / 0.361 / 0.58 |
| 10 M | 0.033 / **0.822** / 0.37 | 0.041 / 0.309 / 0.40 | 0.036 / 0.282 / 0.51 | 0.073 / 0.361 / 0.58 |

- **Under the natural trace, every body-only modulator responds less than the reference** at nearly every
  checkpoint: 0.46 to 0.96 times the reference for N, and 0.50 to 0.87 times for IT.
- **I's two "wins" (3 M, 4 M) are not a sensitivity difference; they come from a stronger probe.** At those two
  checkpoints, I's own recorded injured episode reached felt injury 0.70. Every other agent and checkpoint peaks
  at 0.52, because the agent reaches the bush and heals first. The exceptions are I at 10 M (0.587; trace E1
  0.041) and the ordinary partner at 10 M (0.70). So the probe at those two checkpoints was simply
  stronger.
- **The trace row is each agent's own recorded trace.** It is therefore not an identical dose across agents, and
  this applies to every trace comparison. The ordinary partner's trace also reaches 0.70 at 10 M.
- **N's jumps at 8 M (0.60) and 10 M (0.82) under the constant 0.70 are not a change in the natural response.**
  - N's trace E1 is flat (0.028–0.033) across all 9 checkpoints.
  - N's modulator reads felt injury only. Its gain therefore depends on nothing but the felt-injury history and
    the modulator's weights, not on where the agent walks.
  - 0.70 is the value felt injury settles to in the injury-70 scene; `engagement.py` asserts this. It lies above
    the natural test traces, which peak at 0.52 at every N checkpoint, only because the agent reaches the bush
    and heals first. Whether it lies outside N's training range was not checked. At these two checkpoints the
    modulator responds much more steeply to this settled value than to the natural test traces.
  - **The behavioural fact.** At 8 M and 10 M, holding N at the scene's settled felt injury makes it **stop
    hiding**: `bush_const` = 0.000, against 0.67–0.87 at the other seven checkpoints.
  - These two checkpoints are N's only "wins" under 0.70 that are not marginal, and they are also N's only two P2
    "wins" (memory shift 7.87 and 6.84). They reflect the response to a held settled value above the natural test
    traces, not a stronger response to the natural trace. N's other three 0.70 wins (2–4 M) exceed the reference
    by 3–11 %.
- **Gain spread (raw values only).** The gain's across-unit spread (`gainsd`) is reported beside E1 as
  pre-registered: N 0.29–0.37, I 0.33–0.40, IT 0.35–0.51, reference 0.42–0.58. No between-agent comparison
  divides E1 by this spread. Such a ratio would be inflated for the body-only agents by their smaller spreads,
  which is the denominator pattern the case-study review withdrew.

### 5. Q2: how far a felt-injury input moves the main network's memory (raw shift, never divided by a spread)

The table shows the raw shift of the memory state (Euclidean length over the 128 memory units, `rnn.state`), with
both scenes pooled, under the 0.70 dose and under the natural trace (`score.json` `Q2_table`).

| Checkpoint | N | I | IT | Reference | Ordinary partner |
|---|---|---|---|---|---|
| 2 M | 4.09 / 1.15 | 5.83 / 1.11 | 5.34 / 1.42 | 7.11 / 2.74 | 7.49 / 2.05 |
| 3 M | 4.28 / 1.36 | 5.30 / 2.74 | 4.83 / 1.23 | 6.79 / 1.75 | 7.08 / 1.96 |
| 4 M | 4.95 / 1.32 | 6.54 / 2.54 | 5.33 / 1.38 | 6.83 / 1.75 | 6.87 / 1.87 |
| 5 M | 5.17 / 1.37 | 5.13 / 1.20 | 5.54 / 0.96 | 6.61 / 1.82 | 7.00 / 1.76 |
| 6 M | 5.15 / 1.12 | 5.53 / 1.36 | 5.04 / 1.46 | 6.60 / 1.49 | 6.46 / 1.56 |
| 7 M | 4.50 / 1.16 | 5.01 / 0.92 | 5.15 / 0.99 | 6.19 / 1.54 | 6.28 / 1.84 |
| 8 M | **7.87** / 0.94 | 5.76 / 0.97 | 5.70 / 0.93 | 5.79 / 1.43 | 6.38 / 1.43 |
| 9 M | 5.40 / 1.18 | 5.35 / 1.15 | **6.94** / 1.27 | 6.16 / 1.54 | 6.10 / 1.42 |
| 10 M | **6.84** / 0.97 | 5.26 / 1.41 | 5.47 / 0.97 | 5.55 / 1.36 | 5.90 / 2.09 |
| above the ordinary agent under 0.70 | 2/9 | 0/9 | 1/9 | 2/9 | — |

Each cell gives the shift under 0.70 / the shift under the natural trace.

- **The 0.70 dose moves the memory of all three body-only agents less than it moves the ordinary agent's**, at 7
  to 9 of 9 checkpoints. It also moves it less than the reference's. Their shifts are typically 4–6, against 6–7.5.
- **The reference sits just below the ordinary agent** (2/9 above), as the case study found.
- **The natural-trace row is the same apart from probe-dose effects.** I is above the ordinary agent at 3 M and
  4 M, which are the checkpoints where I's trace reached 0.70.
- **So body-only modulation does not make felt injury move the main network's memory more.** If anything it moves
  it less, yet the behavioural injury effect is as large or larger (§6).

### 6. What the internals add to the behaviour readout

**The behaviour readout.** The behaviour session's stage-1 readout is the Modulator Capacity and Input Screen page,
built from `scripts/analysis/studies/nmn_screens/` (`figures/screen_inp_table.csv`). In the neutral scenes,
2–10 M checkpoint-wise means, it places N's rabbit-scene injury effect at 11.6 pp [8.7, 14.5]. I is at 12.3 and
IT at 8.8. The six reference runs span 0.6–9.2, and the seed-42 reference is 8.4. The behaviour page's own reading
is that "no setting changes the injury effect by more than the seed-to-seed spread".

**What the internals add.** Read with the stated one-seed caveat, these agents show five things.

1. **Behaviour that looks similar may be produced differently.** The body-only agents' injury hiding is about as
   large as the references'. In N and I, hiding felt injury from the modulator alone lowers injured hiding at every
   checkpoint; in the single reference agent it raises it at 7 of 9. This is consistent with routing through the
   modulator in N and I, or with disruption when the modulator alone is blind (§3). The behaviour readout cannot
   see either. The contrast is one agent against one agent.
2. **It bears on one stated reason for expecting a null.** NMN_INPUT_L05 confound C1 says that a body-only
   modulator beside a main network that reads the same signals "gives the policy no information it lacks". That
   is true of information. If the routing reading holds, these agents nonetheless rely on that route for their
   injury hiding; if the disruption reading holds, they do not. These data do not decide which.
3. **It does not support "a stronger modulator response causes more hiding".** N and I respond *less* in raw gain
   units (Q1), and move the memory *less* (Q2), than the reference. Yet their injury hiding is equal or larger and
   depends on the modulator's input. Whatever the modulator contributes, it is not the size of its gain change.
4. **Adding signals (descriptive nesting).**
   - N → I (adding fullness) leaves the direction intact (9/9 at both).
   - I → IT (adding body temperature) loses it (3/9).
   - IT also has the smallest rabbit-scene behaviour effect of the three (8.8 pp).
   - Confound C3 of NMN_INPUT_L05 applies: body temperature sits at 0 °C in these neutral scenes, against about
     −30 °C air in training. IT's modulator is therefore reading an input outside its training range here, and
     its Q1 and Q3 values may reflect that rather than learned routing.
   - Q3 was not run in the training-like scenes, where body temperature lies inside the training range, so this
     cannot be settled here.
5. **Q1's trace and Q2 agree with the September pattern for these agents.** That pattern was "body-only modulators
   are the least state-dependent". The gains of the body-only modulators move little.

### 7. Implication for stage 2 (the user's call; P1–P3 are not a gate)

**What would make seeds 43 and 44 informative.** Stage 2 would be worth it to test one thing that seed 42 suggests
and cannot establish: whether hiding felt injury from a felt-injury-only modulator (N, and possibly I)
consistently lowers injured hiding, and whether it does so by reverting the agent to its unhurt behaviour. The
comparison with the all-senses reference is so far one agent against one agent. A trajectory-identity check
(§3) would sharpen what stage 2 can separate.

**The behaviour readout alone gives a weaker case.** No variant separated from the six references there.

**Before stage-2 data exist, a new pre-registration should:**

- replace the additivity rule, which in these agents mostly measures whether the main network's copy acts alone;
- include a test that separates routing from disruption (for example, trajectory identity with unhurt);
  for example, report each single-route sufficiency (main-hidden vs live, mod-hidden vs both-hidden) directly;
- set a tolerance for deterministic scenes;
- resample checkpoints and seeds, not seeds alone;
- add the training-like scenes to Q3, so that IT is read inside its training range.

The present rule stands for stage 1 and is not amended here.

### 8. What the verdict reviewer should check hardest

1. **The interaction identity in §3.** Because main-hidden ≈ live, interaction ≈ −(mod-hidden effect). Check
   that this makes the additivity rule mainly a test of whether the main network's copy acts alone, and that I
   have not used this to soften the P3 "not met".
2. **The routing claim for N** rests on one seed. It also depends on the never-trained pairing "main network
   sees injury, modulator does not". The reversion check (§3) is the only evidence on disruption; check
   that its limits are stated fairly.
3. **The cause of N's 0.70 jumps.** I attribute them to a steeper response to the scene's settled value (0.70), which is
   above the natural test traces. The evidence is that N's modulator reads felt injury only, that the natural
   trace peaks at 0.52, and that `bush_const` = 0 at exactly those two
   checkpoints. Confirm that nothing else in N's modulator input (for example, the modulator's recurrent state)
   could make E1 depend on the agent's path.
4. **Trace-row comparability.** The trace row is each agent's own trace, so I's 3 M/4 M and the ordinary
   partner's 10 M Q2 values use a stronger dose.
5. **The 101-step episode length** against the Implementation Report's "100 steps".

### Metrics Requested

| Metric | Why now | Where it would live | Cost |
|---|---|---|---|
| Q3 single-route sufficiency, reported directly: (main-hidden − live) and (mod-hidden − both-hidden) per checkpoint with a seed × checkpoint bootstrap | The pre-registered additivity rule cannot distinguish redundant routes from disruption; these two numbers state each route's sufficiency directly | `scripts/analysis/modinput_internals/measures.py` (`summarize`) | cheap (from existing episode CSVs) |
| Step-by-step trajectory identity of mod-hidden against unhurt episodes | The only available disruption check uses dwell alone (§3) | `measures.py` from a recorded mod-hidden replay | moderate |
| Q3 in the training-like level-05 scenes | IT's body-temperature input is outside its training range in the neutral scenes (confound C3) | `internals.py q3` scene list | moderate (about 15 min of CPU per agent set) |
| E1 at a matched dose within the natural test traces (for example 0.52), and the felt-injury range seen in training | 0.70 lies above every natural test trace, and whether it is inside N's training range is unverified | `internals.py q1` | cheap |

### Related Issues

None. No tool bug was found. The 101-step length (§1) is a wording discrepancy in the Implementation Report, not
a defect in the data.

Analyzed by: experiment-analyzer (working notes `tmp/20261008_154552_modinput_verdict.md`)

## Feedback from plan-reviewer (analysis-verdict gate, 2026-10-08)

**Verdict: SUPPORTED WITH CAVEATS.** The three pre-registered scores are correct as written. All three predictions
are not met: the modulator does not respond more strongly to felt injury (P1), a fixed dose does not move the main
network's memory more (P2), and no share of the hiding through the modulator can be read (P3). The P3 "not met"
survives every resampling I tried. The problems are elsewhere. The plain-language verdict and §6 present a routing
mechanism as established, although §3 itself says the data cannot settle it. Some wording calls 0.70 "out of
range", and that does not hold. No Critical finding, so no review file was written.

Severity: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run · 🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

| Sev | Location | Issue | Required edit |
|---|---|---|---|
| 🟡 | Verdict in plain language, ¶ "Under that scoring…"; §6 items 1–2 | "Removes 10.2 of 11.9 pp" is the 0.85 share, which the rule declined to read, restated in words. "This agent has learned to route its injury-driven hiding mainly through the modulator" is stated as fact. §3 says the data do not separate learned routing from disruption by the never-trained pairing. | Report the numerator alone (10.2 pp [9.5, 10.8]). Write "consistent with routing through the modulator, or with disruption when the modulator alone is blind". Apply the same wording to §6.1 and §6.2. |
| 🟡 | §3 "One observation counts against general disruption" | This argument has almost no power. In N, main-hidden ≈ live is exactly what routing predicts, and disruption is specific to a pairing, so the other pairing being benign says little about this one. | Say that it is weak. A more direct check is available. In the rabbit scene, N's mod-hidden injured dwell equals the same seed's unhurt dwell in 32 % of episodes (27 % where the unhurt dwell is > 0), against 5 % for live and 3 % for the reference's mod-hidden. That points to the agent reverting to its unhurt behaviour, not to new behaviour. A step-by-step trajectory-identity check of mod-hidden against unhurt would test this cheaply. |
| 🟡 | §3 reference table and bullets | "Redundant routes" and "the modulator's copy restrains hiding" both rest on the mod-hidden and main-hidden conditions. For the reference agent, both are never-trained pairings. The disruption caveat is applied to N but not here. The pattern also fails at 8 M (live effect −2.0 pp, interaction +0.5). | Add the same disruption caveat and the 8 M exception. Use "consistent with redundancy". The reference is also one seed, so the contrast "unlike the all-senses reference" (§6.1, §7) compares one agent with one agent. |
| 🟡 | §3 Fact 1 heading ("mostly an artefact … one real exception") | The test applied is "interaction under half the divisor", which is not the pre-registered criterion and was chosen after the data. N's no-animal 3.6 pp is one real non-additive checkpoint (8 M, 28.7 pp), not an artefact. IT's no-animal interaction stays non-additive even when checkpoints are resampled: −2.1 [−4.6, −0.3]. | Say "uninformative for I; real at one checkpoint for N (8 M) and IT (6 M); real for the reference". Note that the magnitude comparison is post hoc. |
| 🟡 | §4 N's 0.70 jumps; §8.3; Metrics Requested row 3 | "Out-of-range input" overstates it. 0.70 is the value felt injury settles to in the injury-70 scene (`engagement.py` asserts this). It lies above the natural test peaks (0.52) only because agents heal first. Whether it lies outside the training range is unverified. The path-independence argument is correct: N's modulator reads only its felt-injury slice and its own recurrent state. | Say "above the natural test traces", everywhere. State the behavioural fact plainly: at 8 M and 10 M, holding N at the scene's settled injury makes it stop hiding (`bush_const` 0.000). |
| 🟡 | §4 "Gain spread" bullet | E1 ÷ the gain's spread is used for a comparison between agents ("larger than the reference's"). The body-only agents have smaller spreads, so the ratio is inflated by construction. This is the same pattern the case-study review withdrew. | Drop the ratio comparison, or state the bias next to it. |
| 🟢 | §2 Fact 2 "does not hinge on resampling" | This was shown for checkpoint-only resampling, not joint resampling. I ran a joint seed × checkpoint bootstrap. Rabbit-scene interactions: N −1.7 [−3.4, −0.03]; I 2.1 [−1.1, 6.5]; IT −5.1 [−11.3, −0.9] with half-width 5.2 > 4.0. P3 holds because IT fails the half-width clause under any wider resampling, not because N fails. | Rest the claim on IT and cite the joint numbers. |
| 🟢 | §4 "every other agent … peaks at 0.52" | I's trace at 10 M peaks at 0.587 (trace E1 0.041). | Correct the sentence. |
| ❓ | §1 survival guard; 101 steps | Every one of the 28,800 episodes reached the 101-step cap. If injury 70 cannot end an episode within 101 steps under any policy, the guard could not fire, so "never fired" is not evidence against disruption. The 100-vs-101 difference has no other effect: dwell parity matched the sweep, and the 10 % threshold is not involved. | Move the guard out of the list of "checks passed", or verify that early termination is possible. Correct "100 steps" in the Implementation Report. |

**Rules.** Survival is measured in steps; the doc does not use reward and does not use the word "pain". No
across-state spread is used as a divisor in Q2. The results section opens with a plain-language verdict. No
frontmatter is needed: this folder does not use it, and the contract covers `docs/develop/` only.

**Cost of being wrong:** moderate. The P1–P3 scores stand. If the routing claim stays as written, it could justify
stage 2 (seeds 43 and 44, several GPU-days) on a mechanism that is equally well explained by disruption.

Reviewed by: plan-reviewer
