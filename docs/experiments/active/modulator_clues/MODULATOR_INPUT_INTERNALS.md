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
