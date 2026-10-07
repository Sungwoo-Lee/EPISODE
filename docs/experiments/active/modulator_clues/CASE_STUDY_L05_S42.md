# Case study: inside the 22-September level-05 pair, seed 42

## Question (plain language)

Of all the ordinary-vs-modulated pairs tested in the fast-bush-healing replication ([[FAST_HEAL_REPLICATION]]),
the pair trained on 22 September at level 05 with seed 42 shows the largest and most consistent lead for the
modulated agent. When injured it hides in the bush more than its ordinary partner by 9 points with no animal
around, 10 points with a harmless rabbit around, and 11 points more when a predator hunts. (These are
percentage points of the time spent on the bush.)

The engagement check ([[MODULATOR_ENGAGEMENT_CHECK]]) found that, across many pairs, the size of such leads
is not explained by how strongly the modulator reacts to felt injury. This case study looks *inside* the one
pair where the lead is largest, to see what differs between its two networks. It asks three questions:

1. **Does injury change each layer's activity more in the modulated agent?** In other words, does it notice
   injury more strongly?
2. **Does that change push the network toward going to the bush?** An agent can register injury and still not
   act on it. This separates noticing injury from acting on it, layer by layer.
3. **Which part of the modulator carries the extra hiding?** The modulator acts at several places; freezing it at
   one place at a time shows which one matters.

A single pair can only produce ideas, not proof. So every finding is read against two comparison pairs: one
that should share the mechanism, and one that should not. The results are meant to feed the next experiment,
in which the modulator listens only to the body ([[NMN_INPUT_L05]]).

Status: **exploratory case study**. The reading rule below is fixed before any number is computed. There is no
registered verdict.

## Agents

| Pair | Ordinary run | Modulated run | Role |
|---|---|---|---|
| **Case**: 22-Sep level 05, seed 42 | `20260922-182534_rppo_bq2cover_lvl05_t1none_s42` | `20260922-182538_…lvl05_t16quad_s42` | largest, consistent lead (+9 / +10 / +11) |
| **Same-seed replication**: level 05, seed 42 | `healrep_l05_t1none_s42` | `healrep_l05_t16quad_s42` | same seed, same direction, smaller (+6 / +7 / +6) |
| **Reverse**: level 05, seed 43 | `healrep_l05_t1none_s43` | `healrep_l05_t16quad_s43` | ordinary hides more (−6 / −6 / −13) |
| *Closest settings (descriptive)*: level 05 fixed start temperature, seed 42 | `healrep_l05fix_t1none_s42` | `healrep_l05fix_t16quad_s42` | episodes start at the setpoint temperature, as on 22 Sep |

Exact folders are taken from `scripts/analysis/modulator_engagement/runs.py`, which already resolves and
checks them.

## Scenes, checkpoints and inputs

- **Scenes.** The replication's neutral level-05 test scenes (air at 0 °C, no campfire), with no animal and
  with the wandering rabbit, at starting injury 0 and 70: 30 episodes each, the same seeds as the outcome sweeps.
- **Checkpoints.** The nine grid points at 2, 3, …, 10 M training steps, the same set the engagement check's
  freeze test used.
- **Layers.**
  - Encoder output (and its unimodal stage), memory state (the carried GRU state), memory output, actor hidden
    layer, critic hidden layer.
  - For modulated agents, also the modulator's own hidden state (its GRU). The capture code does not record it
    yet, so it has to be exposed. Where a layer is modulated, both the value before the modulator is applied
    (`.raw`) and after (`.out`) are kept.

## Analysis 1: how much injury changes each layer (noticing)

The test changes felt injury and nothing else.
- Replay the unhurt episodes twice. In the second replay, the felt-injury input is set to 0.70 from step 0;
  that is its settled value for an injury of 70.
- Observations and actions stay identical (live mode with a shadow copy, as in the engagement check's E1).
- For each layer, the **injury shift** is the per-step difference in activity between the two replays.
- Its **size** is the mean of the shift's length, divided by the typical size of that layer's moment-to-moment
  variation in the unhurt replay. This scaling makes layers and agents comparable.
- Sensitivity row: the same, with felt injury following the natural trace of a real injured episode, which
  peaks at about 0.52.

## Analysis 2: does the shift point toward the bush (acting)?

- **Bush direction.** For each agent and each layer, fit a linear readout predicting *the agent is on the bush
  within the next 5 steps*.
  - Fitted on the natural episodes: both injury levels, both scenes, all nine checkpoints pooled per agent.
  - Uses ridge-penalised logistic regression, scored on held-out episodes. The held-out accuracy is reported, so
    a layer whose readout fails is not over-read.
- **Push toward the bush.** Project the injury shift from Analysis 1 onto that readout and report two things:
  - (a) the change in the readout's predicted log-odds of reaching the bush;
  - (b) the alignment between the shift and the bush direction (cosine), which says how much of the noticing is
    directed at acting.
- **Layers.** All layers of Analysis 1, including the critic and the modulator's own hidden state, as the user
  asked (2026-10-07). The actor layer is the most direct link to the decision. The critic and the modulator's
  state show whether "hurt means go to the bush" is also present where it does not drive the action directly.

## Analysis 3: which part of the modulator carries the extra hiding (modulated agents only)

- In the same test scenes, freeze the modulator at **one place at a time**: encoder (both stages together),
  memory, actor, critic. Then freeze all places at once as a reference.
- Freeze the gain and the offset together. The target is the per-unit average pooled over the injured and
  unhurt live passes, so the steady effect of injury on the modulator is removed rather than kept.
- Edited copies go to a separate folder and are scored with the same sweep that produced the behaviour
  numbers, as in the engagement check's E4.
- **Report** the injury effect (injured minus unhurt bush dwell, both scenes) live vs frozen per place. Also
  report the unhurt dwell level for each condition, because freezing can disturb behaviour in general (the
  engagement check saw unhurt hiding double). A place "carries" the effect only if freezing it reduces the
  injury effect without a comparable change in unhurt dwell.

## Reading rule (fixed now)

A pattern counts as a candidate mechanism only if all three hold:
1. In the **case** pair, the modulated agent differs from its ordinary partner in the expected direction (more
   noticing, more push toward the bush) at **at least 7 of the 9 checkpoints**.
2. In the **same-seed replication** pair, the difference has the same sign at at least 6 of 9 checkpoints.
3. In the **reverse** pair (seed 43), the difference is absent (fewer than 6 of 9 checkpoints with that sign)
   or reversed.

The fixed-start pair is reported but does not enter the rule. For Analysis 3, a place carries the effect if,
in the case agent, freezing it lowers the injury effect at at least 7 of 9 checkpoints while unhurt dwell
moves by less than the injury effect itself.

Everything else is description. No result here is a test of the modulator design in general (one pair per
condition, one seed each). Felt injury is described as felt injury (nociception), never "pain"; behaviour is
bush dwell; survival, where reported, is in steps.

## Revision 1 (2026-10-07, before any computation), after the plan review (NOT READY; `docs/reviews/plan_case_study_l05_s42.md`)

These items override the sections above where they differ.

**Analysis 1: orientation and scale.**
- The **acting** agent receives the true observations and follows the natural unhurt route. A **shadow** copy is
  fed the same observations with felt injury replaced. The shift is measured along the unhurt route. The
  opposite orientation, as in the engagement check's tool, is kept only as a labelled sensitivity row.
- Two felt-injury inputs, both primary: the **natural trace** (the felt-injury time course of a real injury-70
  episode, peaking at about 0.52) and the constant **0.70**, which is labelled a stress probe because it lies
  above anything the agent meets.
- **Scale.** The shift's mean length is divided by the spread of that layer's activity *across states*, over
  unhurt live steps of the same checkpoint, in the same window: all steps of the 100-step scene. Units with zero
  variance in the unhurt pass are dropped. Numerator and denominator are reported separately.
- **Modulated layers** are compared before and after the modulator acts (`.raw` vs `.mod`: after the gain and
  offset, before the activation function).

**Analysis 2: a readout that cannot restate injury.**
- **Label.** At a step where the agent is *off* the bush, the label is whether it *arrives* on the bush within
  the next 5 steps. Steps already on the bush are excluded, as are the last 5 steps of an episode. "Bush" means
  the same cells the bush-dwell measure counts.
- **Fitted on unhurt episodes only**, with logistic regression and a ridge penalty, per checkpoint, scored on
  held-out episodes with AUC and log-loss, never accuracy. A sensitivity row fits on both injury levels with felt
  injury given as an extra covariate.
- **Reported per layer:** the cosine between the bush readout and a felt-injury decoder fitted on the same layer.
  If they are close to aligned, that layer cannot separate acting from noticing.
- **Push.** The injury shift (Analysis 1) projected onto the readout, expressed in units of the readout's own
  spread of predicted log-odds over unhurt steps, plus the cosine alignment.
- The **actor-layer** push is a consistency check, not a finding: it nearly restates the behaviour.

**Analysis 3: guards.**
- **Freeze target:** the per-unit average pooled over the injured and unhurt live passes in **both** scenes (no
  animal, wandering rabbit) at that checkpoint.
- **Run on two agents:** the case modulated agent *and* the same-seed replication modulated agent.
- **Disruption guard.** A freeze place "carries" the effect only if the average absolute change in unhurt bush
  dwell is under **half** the live injury effect of the same agent and scene. A place that fails the guard reads
  "undetermined (disruption)". The effect is also reported on a log-odds scale, and survival in steps is
  reported beside it.
- **The critic freeze is a null control.** Under greedy evaluation it cannot change actions, so its trajectories
  must be bit-identical to the live ones. If they are not, the pipeline is wrong and the analysis stops.

**Primary cells.** Only three are named. Everything else is descriptive.
- **C1.** Analysis 1, natural trace: the injury shift's size in the **memory state**. The modulator does not act
  on this layer directly. Does felt injury reach the agent's memory more in the modulated agent?
- **C2.** Analysis 2, natural trace: the push toward the bush in the **memory output**. This is the step before
  the decision layer, and the modulator acts on it.
- **C3.** Analysis 3: the **encoder** freeze place in the case agent. Its input stage reads felt injury first.

**Reading rule, restated.**
- The evidence unit is the **pair**, not the checkpoint. Checkpoints within a run are strongly alike, so 7 of 9
  measures stability over training, not replication.
- A primary cell is a **candidate mechanism** only if it is consistent within the case pair (7 of 9 checkpoints),
  holds with the same sign in the same-seed pair (6 of 9), and does not hold in the seed-43 pair (fewer than 6
  of 9, or reversed).
- Any one metric passes all three by chance about 1 time in 8, and three pairs are all the evidence there is, so
  a candidate is a hypothesis for the body-only experiment, nothing more.
- **Selection.** The case pair was picked *because* its lead is the largest, so its differences are biased
  toward passing condition 1 and are expected to shrink on retest. Condition 2 is the meaningful one.

**Comparability check (a fatal precondition).** Before Analysis 1:
- re-score one no-animal checkpoint per case agent under the current code, and require the original bush-dwell
  values to be reproduced;
- log which compatibility keys the older saved configs needed filled in.
The predator scene is not used in this study; its +11 lead is quoted only as context.

**Tooling.** Per-layer activity capture (`forward_with_activations`) is added to the live tool, with the chain
checks from `teacher_forced.py`, plus a flag for the shadow orientation. No `src/` change is needed. The
modulator's own memory state is already recorded. File changes go into
`docs/environment/SCRIPTS_DEPENDENCY_MAP.md` in the same commit.

## Revision 1b (2026-10-07, before any computation), after the re-review (SOUND WITH CONCERNS)

- **C3 has its own rule.**
  - In the case modulated agent, the encoder freeze lowers the injury effect at at least 7 of 9 checkpoints
    with the guard passed.
  - In the same-seed modulated agent, the same holds at at least 6 of 9.
  - In the **seed-43 modulated agent**, added as the contrast with the same tooling, it does not hold (fewer
    than 6 of 9, or reversed).
- **Chance across cells.** Each cell passes by chance about 1 time in 8, so across the three primary cells the
  chance that at least one passes by luck is about 1 in 3, which is 1 − (7/8)³.
- **Comparability check.** "Reproduced" means an exact match: same seeds, greedy actions, identical bush
  dwell per episode.
- The sections of the original plan that Revision 1 overrides are **superseded**: Analysis 1's orientation and
  scale, Analysis 2's readout and pooling, Analysis 3's target and guard, and the first reading rule. At the
  memory layer, the "after the modulator" value is the layer's output, so `rnn.mod` is the same as `rnn.out`.

## TODO (after 1–3)

4. **Similarity across the six agents.** CKA and linear predictivity, layer by layer. Do the two seed-42
   modulated agents that hide more share an internal solution that the seed-43 modulated agent lacks?
5. **How readable injury is per layer.** Decode felt injury and injury level from each layer, to see whether
   injury stays clearer deeper into the case's modulated agent.
6. **Training history.** When the extra hiding appeared across checkpoints, and whether the modulator's injury
   response (the engagement check's E1) grew at the same time.

## Outputs

`results/analysis/case_l05_s42/`, with a results section appended below. If the user wants it, a page follows
later.

## Feedback from plan-reviewer (2026-10-07)

**Verdict: NOT READY. Two cheap fixes to Analysis 2 flip it to SOUND WITH CONCERNS.** Full table:
[[plan_case_study_l05_s42]] (`docs/reviews/plan_case_study_l05_s42.md`).

Critical:
1. **The readout is circular.** Fitting "bush soon" on episodes that include injured runs lets felt
   injury predict the bush, so the readout absorbs the injury direction. The projection is then
   positive by construction, and largest in the agent that hides more. Fit on unhurt episodes only.
   Report the cosine between the readout and a felt-injury decoder per layer.
2. **The shadow orientation is reversed.** In `obs_manipulation/run.py` the copy fed the
   manipulated felt injury is the one that acts. So the "unhurt replay" is really the felt-injured
   agent's route, which is bush-rich in the case agent. For this study, the agent should act on the
   true observations and the shadow should get 0.70.

Moderate edits:
- Fit the readout per checkpoint, not pooled.
- Label the readout only on off-bush steps ("arrives within 5 steps"), and drop censored tails. Score
  it with AUC or log-loss. Express the log-odds push in units of the readout's own logit SD.
- Make the natural-trace row co-primary for Analysis 2.
- Normalise Analysis 1 by the across-state SD, not step-to-step change, and fix the time window.
- Name at most 3 primary cells. About 5 chance "candidates" are expected across all the layer ×
  measure cells. 7/9 checkpoints measures stability across training, not replication. The
  actor-layer push is a consistency check, not a mechanism.
- Analysis 3: state the guard as absolute and averaged over checkpoints. A failed guard means
  "undetermined". Make the critic freeze a guaranteed-null control (it must be bit-identical to
  live). Freezing gain and offset together has never been run. State which scenes the freeze target
  is pooled over.
- Feasibility: the modulator GRU is already recorded by the live tool. What is missing is per-layer
  capture in live mode (`forward_with_activations` plus the `teacher_forced._chain` checks).

Verified: the case pair uses the same neutral probe folder and 30 episodes as the replication pairs,
and E4 live passes reproduced its rabbit-scene dwell. Still open: the no-animal scene under current
code, and how the saved config loads.

Reviewed by: plan-reviewer

## Feedback from plan-reviewer: re-review of Revision 1 (2026-10-07)

**Verdict: SOUND WITH CONCERNS.** Both critical findings are resolved, and so are most of the moderate
ones. Three small edits remain. None of them blocks the tooling work.

Resolved:
- **Readout.** It is fitted on unhurt episodes only, with arrival-only labels on off-bush steps. Censored
  tails are dropped, and the bush cells match the bush-dwell measure. It is fitted per checkpoint and
  scored with AUC and log-loss. The cosine to an injury decoder is reported for each layer. The
  sensitivity row uses felt injury as a covariate.
- **Orientation.** The acting agent follows the true observations, and the shadow is the one injured.
  The reversed orientation is kept only as a labelled sensitivity row.
- **Normalisation and probes.** The scale is the spread across states, with a fixed window and dead units
  dropped. The natural trace is co-primary, and 0.70 is labelled a stress probe.
- **Primary cells and evidence.** Three primary cells (C1 to C3) are named, and the pair is the unit of
  evidence. The actor-layer push is a consistency check, and selection bias is stated.
- **Analysis 3.** The guard is now absolute (under half the live effect). A failed guard reads
  "undetermined (disruption)". A log-odds row and survival in steps are reported beside it. The freeze
  target pools both scenes, and the replication modulated agent is included. The critic freeze is a
  bit-identical null control that stops the analysis if it fails.
- **Comparability.** The comparability check is fatal. The predator scene is excluded. The tooling scope
  is correct, and the dependency map is paired.
- **C1 framing.** I checked the code. At the memory site the modulator scales only the emitted output and
  leaves the carry untouched (`src/models/recurrent_ppo_network.py:623-630`). So "the modulator does not
  act on the memory state directly" is right. Note that the carry still receives the modulated encoder
  output.

Remaining edits (owner: experiment-designer):
1. 🟡 **C3 has no reading rule it can satisfy.** The restated rule compares the modulated agent with its
   ordinary partner, and requires the effect to be absent in the seed-43 pair. Analysis 3 runs on
   modulated agents only, and not on seed 43. Write C3's own rule: in the case agent, the injury effect
   is lower at 7 of 9 checkpoints *and* the guard passes; the same holds in the replication modulated
   agent at 6 of 9. Either add the seed-43 modulated agent as the contrast (same E4 tooling, cheap), or
   state that C3 has no negative pair.
2. 🟡 **Chance across the three cells.** About 1 in 8 per cell means roughly a 1-in-3 chance
   (1 − (7/8)³) that at least one of C1 to C3 passes by chance. Add this to the "1 time in 8" sentence.
3. 🟢 **Cosmetic and stale text.**
   - Say what "reproduced" means in the comparability check: an exact match is expected, given the
     same seeds and greedy actions; otherwise give a tolerance.
   - Lines 50–52 ("does not record [the modulator GRU] yet") and lines 103–105 (the old guard) are
     overridden by Revision 1. A one-word "superseded" marker there would stop a reader from acting on
     them.
   - At the memory site, `.mod` has no activation after it, so it equals `.out`.

Cost of being wrong: low. Without edit 1, C3 can be called a "candidate" on the case agent alone,
which is the selected and biased one. That is a wording risk, not a rerun.

Reviewed by: plan-reviewer
