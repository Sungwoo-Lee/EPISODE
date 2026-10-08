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

## Implementation Report (developer, 2026-10-07)

Tooling and computation only. No interpretation here; the verdict is the analyst's.

**Built** (commits `e62ccd86`, `d0c8f5b4`):
- `scripts/analysis/obs_manipulation/run.py`: `--orientation act_manipulated|act_true` (default = the original behaviour); `run_checkpoint(capture=True)` keeps both passes' `forward_with_activations` tensors, observations and modulator outputs as a separate evaluation, so trajectories are unchanged; a traced per-step override plays a recorded felt-injury trace in one compiled program. With `act_true`, every condition must follow the identity route (asserted).
- `scripts/analysis/case_l05_s42/case.py`, with subcommands `a12`, `a3-prepare`, `a3-collect` and `score`. `measures.py` uses numpy only, because the lab-node environments lack scikit-learn.
- `tests/analysis/test_case_l05_s42.py` has 10 tests, all passing:
  - readout labels exclude on-bush steps and the censored tail (also checked against a brute-force definition);
  - identity reproduces live exactly, with the sweep recordings matching step for step;
  - a nociception-blind network gives exactly zero shift at every layer;
  - the critic freeze is a null control;
  - the numpy fitters agree with scikit-learn.
- The existing engagement tests still pass (8/8).
- `SCRIPTS_DEPENDENCY_MAP.md` is updated.

**Comparability precondition (fatal): passed.** Both 22-Sep case agents were checked at the 6 M checkpoint in the no-animal scenes at injury 0 and 70. In all four runs, 30 of 30 episodes were identical to the 23-Sep sweep recordings: agent position at every step, bush dwell and survival. The older saved configs needed 8 compatibility keys filled in:
- `body.healing_nutrition_cost=0.0`, `body.healing_nutrition_dependence=False`
- `thermal.bush_min_fire_distance=0`, `thermal.healing_cold_sensitivity=0.0`, `thermal.healing_warm_sensitivity=0.0`, `thermal.injury_heat_exchange_gain=0.0`, `thermal.random_start_body_temp=False`
- `water.enabled=False`

They affect only how the agent is rebuilt; the test worlds are the current probe files.

**Computed** (node 108, CPU; claimed and released in the diary). Outputs are in `results/analysis/case_l05_s42/`:
- `a1/`, `a2/`: 8 agents × 9 checkpoints.
- `checks/`: per-checkpoint parity, chain and trace records.
- `a3/a3_effects.csv`, `a3/a3_summary.csv`, plus the edited checkpoints.
- Dwell sweeps under `results/eval/avoidance/metrics_history_rppo_case_l05_s42/`.
- `scores/c_cells.csv`, `scores/reading_rule.json`.

**Run checks:**
- Exact sweep parity held in 288 of 288 scene-checkpoints for Analyses 1–2, and in 108 of 108 for Analysis 3's live passes.
- Chain assertions: largest deviation 4.3e-7, against a tolerance of 1e-5.
- The capture never changed a logit (difference 0).
- The critic freeze was bit-identical in-tool at all 27 checkpoints, and equal to the live results at sweep level.
- All 72 memory-output readouts were fitted: held-out AUC 0.93–0.996, and |cosine| with the felt-injury decoder at most 0.07.

**Deviations and choices for the plan owner:**
1. **Readout feature space.** The readout is fitted on centred activity with one global scale per layer, not on per-unit z-scores. In the smoke test, memory units with an unhurt SD of about 1e-5 are flipped by about 1 under the 0.70 probe. Per-unit scaling turns that into 10⁴-SD shifts and pushes of about 600 log-odds SDs.
2. **Ridge strength.** It is chosen by single-level grouped 5-fold CV, and the held-out AUC and log-loss come from those same folds. Selecting among 5 values makes the scores negligibly optimistic. This was chosen over nested CV for speed.
3. **Scene pooling.**
   - C1 uses Analysis 1 pooled over both neutral scenes.
   - C3 and the guard use the mean of the two scenes' injury effects; per-scene rows are also written.
   - The natural trace for both scenes is the same seed's injured **no-animal** episode.
4. **Dropped units.** Analysis 1 drops units with zero unhurt variance, as planned. The shift inside those units is reported as `numerator_dropped_units`. At `enc.uni.raw`, the whole felt-injury-carrying input group is silent when unhurt, so its entire shift falls in the dropped units.
5. **Natural trace peaks.** The trace does not always peak at about 0.52. It reaches 0.70 at some checkpoints of agents that do not reach the bush, mostly the seed-43 ordinary agent (6 of 9 checkpoints).
6. **`rnn.mod` and `rnn.out`** are identical, as Revision 1b says. **`rnn.state` equals `rnn.raw`** (the GRU emits its state).

**Found, outside scope (owner: `bug-curator` → `senior-developer`).** Inside `nnx.jit`, `ObservationEncoder.breakdown` is iterated in sorted key order, but the flat observation is in config order (`src/models/recurrent_ppo_network.py:196-200, 255-259`). The hierarchical encoder's "unimodal" groups therefore receive scrambled slices: felt injury enters group slot 1, element 1, together with body temperature, extero-nociception and two thermoception values. Training and evaluation are both jitted, so behaviour is consistent, but per-sensor encoder groups are not per-sensor. This bears on C3's phrase "its input stage reads felt injury first". It is not in the Known Bugs registry.

**Time:**
- Capture: about 50 s per agent-checkpoint.
- Analysis: 3–7 min per agent-checkpoint.
- Analyses 1–2 in total: 58 min wall time with 8 parallel processes.
- Analysis 3 prepare: 7 min with 3 processes.
- Analysis 3 sweeps: 4.5 min, 540 checkpoint-evals.
- Speed check: not applicable (analysis-only change; training's hot path untouched).

Implemented by: developer

## Results (experiment-analyzer, 2026-10-08)

### What was found (plain language)

This study looked inside one ordinary agent and one modulated agent, the pair whose modulated member showed
the largest extra hiding after injury, and compared them against two other pairs: the same training seed
re-run (where the modulated agent also hides somewhat more) and a different seed (where it does not). Three
measurements were fixed in advance as the only ones that could count, together with a rule for when a
difference counts as a clue to how the modulator works.

**None of the three passed.** (1) Felt injury (nociception) does *not* move the modulated agent's memory
more than the ordinary agent's. It is the other way round: in every pair, including the different seed,
the ordinary agent's memory moves more. So this is a general difference between the two kinds of agent,
not something special to the pair that hides more. (2) The change in memory output pushes slightly more
toward "about to go to the bush" in the modulated agents of both same-seed pairs and not in the different
seed, but the pair studied falls one checkpoint short of the fixed threshold, and the push is small. (3)
Switching off the modulator's response at the encoder changes the agent's behaviour so much, even when
unhurt, that it cannot say whether the encoder carries the extra hiding (undetermined).

Overall, the study found no candidate mechanism for the extra hiding.

### Verdict

| Primary cell (fixed before computation) | Case pair (needs ≥ 7/9) | Same-seed pair (needs ≥ 6/9) | Seed-43 pair (needs < 6/9) | Reading |
|---|---|---|---|---|
| **C1**: felt injury shifts the memory state more in the modulated agent (natural trace) | 2/9: **fails** | 1/9: fails | 0/9: holds | **Not a candidate. Direction reversed**: the ordinary agent's memory shifts more, at 7/9, 8/9 and 9/9 checkpoints of the three pairs |
| **C2**: the memory-output shift pushes more toward the bush in the modulated agent (natural trace) | 6/9: **fails by one checkpoint** | 6/9: holds | 1/9: holds (reversed, 8/9) | **Not a candidate.** Expected direction in both seed-42 pairs, absent in seed 43; small; fragile (see C2 below) |
| **C3**: freezing the modulator at the encoder lowers the injury effect, with the disruption guard passed | 5/9 lowered, **guard fails** | 7/9 lowered, guard fails | 3/9 lowered, guard fails | **Undetermined (disruption).** Unhurt bush dwell moves by 67, 53 and 40 points on average, against limits of 7, 4 and 3 |

**Overall verdict on the study question: no candidate mechanism.** The modulated agent of the case pair
does not register felt injury more strongly in its memory (it registers it less, as every modulated agent
here does). Its memory output points slightly more toward going to the bush, but not consistently enough
to pass the rule fixed beforehand. Where the modulator's contribution could be removed without breaking
behaviour (memory and actor), removing it changed nothing measurable. Where it breaks behaviour (encoder,
all places), the test is uninformative. The prior chance that at least one of the three cells passes by
luck alone was about 1 in 3, so this null is not strong evidence that no mechanism exists. With three pairs
and one seed per condition, the study could only find large and consistent differences.

These counts were checked: C1 and C2 were recomputed for all four pairs directly from the per-checkpoint
files `a1/*.csv` and `a2/*.csv`, and C3 from `a3/a3_summary.csv`. Every count matches the developer's
`scores/c_cells.csv` and the numbers in the request (C1 2/1/0, C2 6/6/1, C3 guard failed in every agent).

### 0. Run checks and what the "lead" is at these checkpoints

- **Pipeline checks** (`checks/*.jsonl`, all 72 agent-checkpoints): exact parity with the sweep recordings
  in every scene; the activity capture never changed a logit (largest difference 0); chain deviations at
  most 4.3 × 10⁻⁷. The critic freeze, a null control, was identical to live behaviour in all 27
  agent-checkpoints, so Analysis 3 did not have to stop.
- **Survival** was 101 steps, the full scene length, in every live and frozen condition of Analysis 3. It
  is at its ceiling and cannot tell conditions apart.
- **Behaviour at the nine checkpoints used here** (both neutral scenes, from the same live passes; injury
  effect = bush dwell at injury 70 minus bush dwell unhurt, percentage points):

  | Pair | Modulated injury effect | Ordinary injury effect | Gap | Checkpoints modulated > ordinary | Injured dwell, mod. vs ord. | Unhurt dwell, mod. vs ord. |
  |---|---|---|---|---|---|---|
  | Case | 13.5 | 2.5 | +11.0 | 8/9 | 17.1 vs 20.0 | 3.6 vs 17.6 |
  | Same-seed | 8.8 | 6.2 | +2.6 | 6/9 | 20.8 vs 18.7 | 12.0 vs 12.5 |
  | Seed 43 | 5.5 | 7.9 | −2.4 | 3/9 | 30.8 vs 35.0 | 25.3 vs 27.1 |
  | Fixed start (descriptive) | 4.5 | −3.0 | +7.4 | 6/9 | 20.9 vs 22.9 | 16.4 vs 25.9 |

  The behaviour itself follows the reading rule's pattern (8/9, 6/9, 3/9), so the internal measures were
  tested against a behavioural difference that is present at these checkpoints. One correction to the
  Question section's wording: the case agent's lead is a lead in the *injury effect*. When injured, it
  does **not** spend more time on the bush than its partner (17.1 against 20.0 %, more at only 1 of 9
  checkpoints). Its larger injury effect comes from staying off the bush when unhurt (3.6 against 17.6 %).

### 1. Primary cells in detail

Per-checkpoint differences, modulated minus ordinary, at 2, 3, …, 10 M training steps. A † marks a
checkpoint where the ordinary agent's natural felt-injury trace peaked at about 0.70 rather than about
0.52: its injured episode did not reach the bush, so it never healed, and its probe was stronger.

**C1: memory-state shift size** (units: the layer's own spread across states).

| Pair | 2 M | 3 M | 4 M | 5 M | 6 M | 7 M | 8 M | 9 M | 10 M | > 0 |
|---|---|---|---|---|---|---|---|---|---|---|
| Case | −1.51† | −0.30 | +0.02 | −0.21 | +0.13 | −0.02 | −0.16 | −0.07 | −0.14 | 2/9 |
| Same-seed | +0.11 | −0.11 | −0.08 | −0.03 | −0.12 | −0.20 | −0.09 | −0.04 | −0.31† | 1/9 |
| Seed 43 | −1.82† | −1.36† | −1.64† | −1.65† | −0.21 | −0.07 | −0.22 | −0.28† | −1.29† | 0/9 |
| Fixed start | −0.25 | −0.10 | −0.06 | −0.05 | −0.04 | +0.06 | +0.01 | +0.00 | −0.12 | 3/9 |

- **Direction: reversed.** The ordinary agent's memory moves more under felt injury in every pair. The
  differences are small (about −0.1 to −0.3 of the layer's spread) except at † checkpoints. Dropping the
  † checkpoints leaves 2/8, 1/8 and 0/3, so the stronger probe explains the size of the seed-43 reversal,
  not its sign.
- **Robust to every variant computed:** the 0.70 stress probe (2/9, 0/9, 0/9), the reversed orientation
  (0/9, 1/9, 0/9), and each scene alone (2/9 or less in both seed-42 pairs).

**C2: memory-output push toward the bush** (units: the readout's own standard deviation of predicted
log-odds over unhurt steps).

| Pair | 2 M | 3 M | 4 M | 5 M | 6 M | 7 M | 8 M | 9 M | 10 M | > 0 |
|---|---|---|---|---|---|---|---|---|---|---|
| Case | +0.70† | −0.01 | +0.11 | −0.35 | +0.58 | +0.37 | +0.32 | +0.62 | −0.18 | 6/9 |
| Same-seed | −0.76 | +0.34 | +0.21 | +0.54 | +0.40 | +0.32 | −0.18 | +1.11 | −0.08† | 6/9 |
| Seed 43 | −2.98† | −0.17† | −1.85† | −0.34† | +0.40 | −0.68 | −0.49 | −0.35† | −2.62† | 1/9 |
| Fixed start | −0.33 | +0.00 | −0.20 | −0.30 | −0.46 | −0.32 | −0.04 | −0.20 | −0.08 | 1/9 |

- **Direction: expected in both seed-42 pairs, reversed in seed 43.** Under the fixed rule this fails,
  because the case pair reaches 6 of the 7 checkpoints required. It is not re-labelled here.
- **Size: small.** The modulated agents' median push is +0.17 (case) and +0.17 (same-seed) of the readout's
  spread, against −0.06 and −0.05 for their partners. The cosine between the mean shift and the readout is
  0.14 and 0.10. Natural felt injury moves the memory output's "going to the bush" reading by about a
  sixth of how much that reading varies across ordinary unhurt states.
- **Fragile.** Variants that were *not* primary land on both sides of the threshold:
  - the 0.70 stress probe gives 7/9, 7/9, 3/9, and the raw log-odds push (not divided by the readout's
    spread) gives 7/9, 6/9, 1/9; both would pass;
  - the sensitivity readout, fitted on both injury levels with felt injury as a covariate, gives 6/9, 7/9
    and **7/9**, so the seed-43 contrast disappears;
  - the **fixed-start pair** goes the other way (1/9), although it shows the behavioural lead (6/9 in the
    table above).

  Choosing among these after the fact is exactly what the fixed rule exists to prevent. Together they say
  the C2 pattern depends on how it is measured, and it does not follow the behaviour across the four pairs.
- The memory *state* push (descriptive, not primary, and nearly the same quantity as C2) gives 7/9, 6/9,
  1/9, which would pass the rule. With about 5 chance passes expected across all the descriptive cells
  (plan review), and the fixed-start pair again at 1/9, it is reported only as description.

**C3: encoder freeze.** See Analysis 3 below. The guard fails in all three agents, so the reading is
"undetermined (disruption)". Even before the guard, the case agent's count on the mean of the two scenes
is 5/9, below the 7/9 required. Each scene alone gives 7/9 (no animal) and 6/9 (rabbit); the mean of the two
scenes is the developer's stated choice (Implementation Report, deviation 3), and no choice changes the
reading.

**Premise correction for C3.** Revision 1 justified C3 with "its input stage reads felt injury first". The
developer found that the hierarchical encoder's first-stage groups receive mixed slices of the
observation: the code iterates the sensor groups in alphabetical order, while the observation is laid
out in config order. Felt injury therefore enters one first-stage group together with body temperature,
nociception from outside the body and two thermal values. The correct premise is: *the encoder's first stage is
where the felt-injury input enters the network, mixed with four other sensor values in one group*. This
does not change any C3 number.

### 2. Analysis 1: how much felt injury moves each layer (descriptive, all agents)

Median over the nine checkpoints. Natural felt-injury trace, acting agent on the true observations, both
scenes pooled. Size = mean length of the shift ÷ the layer's spread across unhurt states, with units that
are silent when unhurt left out.

Layer names: `enc.uni` = the encoder's first stage (per-group); `enc` = the encoder's second stage;
`rnn.state` = the carried memory state (C1); `rnn.out` = the memory's output (C2); `actor` / `critic` = the
hidden layers of the action head and the value head; `mod.state` = the modulator's own memory. `.raw` =
before the modulator acts at that layer (but after any upstream modulation), `.mod` = after the
modulator's gain and offset, before the activation function, `.out` = after the activation. Ordinary agents
have no `.mod` values and no modulator. `rnn.raw` equals `rnn.state` and `rnn.mod` equals `rnn.out`, so both are
omitted.

| Layer | Case mod. | Case ord. | Same-seed mod. | Same-seed ord. | Seed-43 mod. | Seed-43 ord. | Fixed-start mod. | Fixed-start ord. |
|---|---|---|---|---|---|---|---|---|
| `enc.uni.raw` | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| `enc.uni.mod` | 0.46 | – | 0.36 | – | 0.28 | – | 0.30 | – |
| `enc.uni.out` | 0.29 | 0.00 | 0.19 | 0.00 | 0.21 | 0.00 | 0.21 | 0.00 |
| `enc.raw` | 0.25 | 0.48 | 0.25 | 0.38 | 0.21 | 1.79 | 0.26 | 0.43 |
| `enc.mod` | 0.72 | – | 0.64 | – | 0.32 | – | 0.47 | – |
| `enc.out` | 0.35 | 0.53 | 0.36 | 0.43 | 0.23 | 1.82 | 0.27 | 0.46 |
| `rnn.state` | 0.63 | 0.73 | 0.50 | 0.65 | 0.44 | 1.85 | 0.52 | 0.58 |
| `rnn.out` | 0.55 | 0.73 | 0.46 | 0.65 | 0.41 | 1.85 | 0.47 | 0.58 |
| `actor.raw` | 0.49 | 0.61 | 0.46 | 0.55 | 0.35 | 1.77 | 0.45 | 0.46 |
| `actor.mod` | 0.48 | – | 0.45 | – | 0.40 | – | 0.45 | – |
| `actor.out` | 0.46 | 0.59 | 0.47 | 0.55 | 0.47 | 1.65 | 0.48 | 0.42 |
| `critic.raw` | 0.56 | 0.63 | 0.49 | 0.54 | 0.42 | 1.65 | 0.47 | 0.55 |
| `critic.mod` | 0.57 | – | 0.52 | – | 0.50 | – | 0.47 | – |
| `critic.out` | 0.38 | 0.46 | 0.35 | 0.41 | 0.36 | 1.20 | 0.37 | 0.39 |
| `mod.state` | 0.71 | – | 0.48 | – | 0.50 | – | 0.53 | – |

Shift inside the units that are silent when unhurt (not part of the size above; same units as the numerator,
not divided by the spread):

| Layer | Case mod. | Case ord. | Same-seed mod. | Same-seed ord. | Seed-43 mod. | Seed-43 ord. | Fixed-start mod. | Fixed-start ord. |
|---|---|---|---|---|---|---|---|---|
| `enc.uni.raw` | 3.34 | 2.97 | 3.37 | 2.73 | 1.80 | 15.42 | 2.96 | 2.95 |
| `enc.uni.mod` | 0.00 | – | 0.00 | – | 0.00 | – | 0.00 | – |
| `enc.uni.out` | 0.57 | 1.34 | 0.51 | 1.21 | 0.55 | 7.98 | 0.55 | 1.23 |
| `enc.raw` | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| `enc.mod` | 0.00 | – | 0.00 | – | 0.00 | – | 0.00 | – |
| `enc.out` | 0.07 | 0.05 | 0.18 | 0.20 | 0.02 | 0.42 | 0.13 | 0.17 |
| `rnn.state` | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| `rnn.out` | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| `actor.raw` | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| `actor.mod` | 0.00 | – | 0.00 | – | 0.00 | – | 0.00 | – |
| `actor.out` | 0.08 | 0.31 | 0.13 | 0.11 | 0.04 | 0.24 | 0.08 | 0.18 |
| `critic.raw` | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| `critic.mod` | 0.00 | – | 0.00 | – | 0.00 | – | 0.00 | – |
| `critic.out` | 0.08 | 0.67 | 0.14 | 0.21 | 0.09 | 0.23 | 0.18 | 0.40 |
| `mod.state` | 0.00 | – | 0.00 | – | 0.00 | – | 0.00 | – |

Checkpoints where the modulated agent's size exceeds the ordinary agent's (natural trace), next to the same count
for the Analysis 2 push:

| Layer | A1 size: case | same-seed | seed 43 | fixed start | A2 push: case | same-seed | seed 43 | fixed start |
|---|---|---|---|---|---|---|---|---|
| `enc.uni.out` | 9/9* | 9/9* | 9/9* | 9/9* | 8/9* | 9/9* | 4/9 | 4/9 |
| `enc.raw` | 0/9 | 0/9 | 0/9 | 0/9 | 4/9 | 3/9 | 3/9 | 7/9 |
| `enc.out` | 0/9 | 0/9 | 0/9 | 0/9 | 5/9 | 6/9 | 5/9 | 7/9 |
| `rnn.state` | 2/9 | 1/9 | 0/9 | 3/9 | 7/9 | 6/9 | 1/9 | 1/9 |
| `rnn.out` | 2/9 | 0/9 | 0/9 | 0/9 | 6/9 | 6/9 | 1/9 | 1/9 |
| `actor.raw` | 3/9 | 0/9 | 0/9 | 1/9 | 5/9 | 6/9 | 1/9 | 0/9 |
| `actor.out` | 4/9 | 1/9 | 0/9 | 6/9 | 5/9 | 3/9 | 3/9 | 3/9 |
| `critic.raw` | 3/9 | 3/9 | 0/9 | 2/9 | 3/9 | 4/9 | 2/9 | 2/9 |
| `critic.out` | 4/9 | 1/9 | 1/9 | 5/9 | 3/9 | 7/9 | 3/9 | 4/9 |

\* True by construction: in ordinary agents the whole first-stage shift lies in units that are silent when
unhurt, so their kept-unit shift is exactly 0.

What the table shows:
- **First encoder stage.** Before the modulator acts (`enc.uni.raw`), the whole felt-injury shift sits in
  units that are silent when unhurt, in every agent (the developer's caveat 4). The modulator spreads it
  into units that *are* active when unhurt (`enc.uni.mod`, 0.28–0.46), which the ordinary agent never
  does. After the activation, the ordinary agent carries more shift in the silent units than the modulated
  agent (about 1.2–1.3 against 0.5–0.6; seed-43 ordinary 8.0, a † agent).
- **From the encoder output onward, modulated agents shift less than ordinary agents, in every pair.** At
  the encoder output the count is 0/9 in all four pairs. The modulator enlarges the encoder shift before the
  activation (`enc.raw` 0.25 → `enc.mod` 0.72 in the case agent), but after the activation it is smaller
  than the ordinary agent's (0.35 against 0.53). This is a property of the modulated design in these runs,
  not of the case pair.
- **The modulator's own memory** shifts most in the case agent (0.71, against 0.48–0.53 in the other three
  modulated agents). This is a single agent with no rule attached, so it is a description only.
- The seed-43 ordinary agent's large values (1.2–1.85) come from its stronger natural probe (†, 6 of 9
  checkpoints).
- Under the 0.70 stress probe the ordering is the same at the encoder and memory (for example memory
  state, case 2.24 against 2.46). Full stress-probe medians are in `a1/*.csv` (`probe == const`).

### 3. Analysis 2: readout quality, injury-decoder alignment and push per layer (descriptive)

**Held-out AUC of the "arrives on the bush within 5 steps" readout** (median over checkpoints; all 9
readouts fitted in every agent and layer):

| Layer | Case mod. | Case ord. | Same-seed mod. | Same-seed ord. | Seed-43 mod. | Seed-43 ord. | Fixed-start mod. | Fixed-start ord. |
|---|---|---|---|---|---|---|---|---|
| `enc.uni.raw` | 0.98 | 0.99 | 0.98 | 0.99 | 0.98 | 0.99 | 0.98 | 0.99 |
| `enc.uni.mod` | 0.99 | – | 0.99 | – | 0.98 | – | 0.98 | – |
| `enc.uni.out` | 0.99 | 0.99 | 0.99 | 0.99 | 0.98 | 0.99 | 0.99 | 0.99 |
| `enc.raw` | 0.99 | 0.99 | 0.98 | 0.99 | 0.98 | 0.99 | 0.98 | 0.99 |
| `enc.mod` | 0.99 | – | 0.99 | – | 0.99 | – | 0.99 | – |
| `enc.out` | 0.99 | 0.99 | 0.99 | 0.99 | 0.98 | 0.99 | 0.98 | 0.99 |
| `rnn.state` | 0.99 | 0.99 | 0.99 | 1.00 | 0.99 | 0.99 | 0.98 | 0.99 |
| `rnn.out` | 0.99 | 0.99 | 0.99 | 1.00 | 0.99 | 0.99 | 0.98 | 0.99 |
| `actor.raw` | 0.99 | 0.99 | 0.99 | 1.00 | 0.98 | 0.99 | 0.98 | 0.99 |
| `actor.mod` | 0.99 | – | 0.99 | – | 0.99 | – | 0.98 | – |
| `actor.out` | 0.99 | 0.99 | 0.98 | 0.99 | 0.96 | 0.98 | 0.98 | 0.99 |
| `critic.raw` | 0.99 | 0.99 | 0.98 | 1.00 | 0.99 | 0.99 | 0.98 | 0.99 |
| `critic.mod` | 0.99 | – | 0.99 | – | 0.99 | – | 0.99 | – |
| `critic.out` | 0.98 | 0.98 | 0.98 | 0.98 | 0.96 | 0.84 | 0.97 | 0.99 |
| `mod.state` | 0.99 | – | 0.97 | – | 0.98 | – | 0.97 | – |

**Cosine between the bush readout and the felt-injury decoder**: median over checkpoints, with the
largest absolute value in brackets. Near 0 means "going to the bush" and "felt injury" are separate
directions in that layer, so acting and noticing can be told apart there.

| Layer | Case mod. | Case ord. | Same-seed mod. | Same-seed ord. | Seed-43 mod. | Seed-43 ord. | Fixed-start mod. | Fixed-start ord. |
|---|---|---|---|---|---|---|---|---|
| `enc.uni.raw` | -0.01 (0.03) | -0.00 (0.02) | +0.03 (0.08) | +0.00 (0.04) | +0.01 (0.09) | +0.00 (0.13) | +0.00 (0.02) | +0.00 (0.02) |
| `enc.uni.mod` | -0.00 (0.00) | – | +0.00 (0.00) | – | +0.00 (0.00) | – | -0.00 (0.00) | – |
| `enc.uni.out` | -0.00 (0.00) | +0.00 (0.06) | -0.00 (0.01) | +0.01 (0.06) | +0.00 (0.01) | -0.00 (0.29) | -0.00 (0.02) | +0.00 (0.10) |
| `enc.raw` | +0.01 (0.04) | -0.00 (0.01) | +0.00 (0.05) | -0.00 (0.04) | +0.00 (0.08) | +0.01 (0.03) | -0.01 (0.02) | -0.00 (0.03) |
| `enc.mod` | +0.02 (0.04) | – | +0.00 (0.04) | – | -0.00 (0.05) | – | +0.00 (0.09) | – |
| `enc.out` | +0.01 (0.08) | +0.01 (0.08) | +0.01 (0.08) | +0.01 (0.06) | +0.01 (0.07) | +0.01 (0.07) | -0.01 (0.18) | -0.01 (0.03) |
| `rnn.state` | -0.01 (0.09) | -0.03 (0.05) | -0.02 (0.06) | -0.01 (0.04) | +0.01 (0.08) | +0.01 (0.07) | -0.01 (0.04) | -0.01 (0.03) |
| `rnn.out` | +0.00 (0.01) | -0.03 (0.05) | -0.00 (0.02) | -0.01 (0.04) | -0.00 (0.02) | +0.01 (0.07) | -0.00 (0.05) | -0.01 (0.03) |
| `actor.raw` | +0.00 (0.01) | -0.01 (0.03) | -0.00 (0.01) | -0.01 (0.02) | -0.00 (0.04) | -0.00 (0.02) | -0.00 (0.03) | -0.00 (0.03) |
| `actor.mod` | -0.00 (0.02) | – | +0.00 (0.08) | – | -0.01 (0.16) | – | -0.00 (0.05) | – |
| `actor.out` | +0.02 (0.10) | +0.02 (0.31) | -0.01 (0.16) | -0.00 (0.13) | +0.00 (0.25) | -0.05 (0.16) | -0.01 (0.30) | -0.04 (0.15) |
| `critic.raw` | +0.00 (0.01) | -0.01 (0.03) | -0.00 (0.02) | -0.00 (0.01) | -0.00 (0.05) | -0.00 (0.03) | -0.00 (0.02) | -0.00 (0.02) |
| `critic.mod` | +0.01 (0.03) | – | -0.02 (0.09) | – | -0.00 (0.22) | – | -0.02 (0.09) | – |
| `critic.out` | +0.02 (0.31) | +0.04 (0.39) | +0.03 (0.31) | -0.06 (0.19) | -0.01 (0.11) | +0.03 (0.18) | +0.01 (0.21) | +0.03 (0.22) |
| `mod.state` | -0.01 (0.43) | – | -0.16 (0.96) | – | -0.16 (0.93) | – | +0.32 (0.81) | – |

**Push toward the bush under the natural trace** (median over checkpoints, in readout spreads):

| Layer | Case mod. | Case ord. | Same-seed mod. | Same-seed ord. | Seed-43 mod. | Seed-43 ord. | Fixed-start mod. | Fixed-start ord. |
|---|---|---|---|---|---|---|---|---|
| `enc.uni.raw` | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| `enc.uni.mod` | -0.04 | – | +0.04 | – | -0.01 | – | -0.00 | – |
| `enc.uni.out` | +0.07 | +0.00 | +0.18 | +0.00 | -0.01 | +0.00 | -0.00 | +0.00 |
| `enc.raw` | +0.17 | +0.24 | +0.11 | +0.23 | +0.09 | +0.08 | +0.13 | -0.02 |
| `enc.mod` | +0.06 | – | -0.40 | – | +0.06 | – | +0.12 | – |
| `enc.out` | +0.14 | +0.18 | +0.03 | +0.00 | +0.03 | -0.45 | +0.17 | -0.06 |
| `rnn.state` | +0.24 | -0.06 | +0.14 | -0.05 | +0.01 | +0.50 | -0.07 | +0.06 |
| `rnn.out` | +0.17 | -0.06 | +0.17 | -0.05 | +0.07 | +0.50 | -0.20 | +0.06 |
| `actor.raw` | +0.14 | +0.18 | +0.26 | +0.14 | +0.00 | +0.35 | -0.22 | +0.11 |
| `actor.mod` | +0.20 | – | +0.18 | – | +0.09 | – | -0.01 | – |
| `actor.out` | +0.13 | +0.12 | +0.17 | +0.35 | +0.12 | +0.24 | +0.14 | +0.09 |
| `critic.raw` | +0.31 | +0.39 | +0.17 | +0.11 | -0.01 | +0.38 | -0.07 | +0.13 |
| `critic.mod` | +0.10 | – | +0.05 | – | +0.04 | – | -0.06 | – |
| `critic.out` | -0.07 | +0.21 | -0.04 | -0.23 | +0.25 | +1.79 | +0.19 | +0.27 |
| `mod.state` | -0.05 | – | -0.10 | – | -0.22 | – | -0.00 | – |

What these show:
- **Readout quality is uniformly high.** The AUC is 0.96–1.00 everywhere, except the seed-43 ordinary critic
  output (0.84). It is as high in the encoder's first stage as in the actor layer, which suggests the
  readout mostly reads where the agent is relative to the bush, a cue present in every layer. The "bush
  direction" is therefore closer to "near the bush" than to "intends to go". That is the right thing to
  project onto, but it means a small push is expected.
- **Acting and noticing can be separated in every main-network layer.** The median cosine is within ±0.06
  in all of them. The largest single-checkpoint values, 0.3–0.4, are in the post-activation heads
  (`actor.out`, `critic.out`); elsewhere they stay below 0.3.
- **The modulator's own memory is the exception.** Its median cosine is −0.16 to +0.32, reaching 0.81–0.96
  at some checkpoints of three of the four modulated agents. There, the felt-injury direction and the
  "going to the bush" direction can nearly coincide, so this layer cannot separate acting from noticing.
- **Felt injury is linearly readable almost everywhere.** The held-out R² of the felt-injury decoder is
  ≥ 0.9 in every layer past the first stage, in every agent (first stage before the modulator, with
  silent units dropped: 0.63–0.90). Every agent therefore "notices" injury in the sense of carrying it. What differs is how
  far it moves each layer (Analysis 1) and where it points (above).
- **The pushes are small throughout** (mostly within ±0.3 readout spreads), except in the seed-43 ordinary
  agent's critic output (+1.79, a † agent). Under the 0.70 stress probe, they grow to between 0.2 and 3.1 spreads
  in the memory and actor layers (`a2/*.csv`, `probe == const`).

### 4. Analysis 3: freezing the modulator one place at a time

Means over the nine checkpoints, averaged over the two neutral scenes. The injury effect and unhurt dwell
are in percentage points of bush dwell. "Lowered" counts checkpoints where the frozen injury effect is
below the live one. The guard requires the mean absolute change in unhurt dwell to be under half the live
injury effect. The log-odds column gives the injury effect as log-odds of bush dwell, injured minus unhurt,
live → frozen, with the count of checkpoints where it is lowered. Survival is in steps over every scene and
checkpoint.

| Agent | Freeze place | Injury effect live | Injury effect frozen | Lowered | Unhurt dwell live → frozen | Mean abs. unhurt change (limit) | Log-odds effect live → frozen (lowered) | Survival (steps) | Reading |
|---|---|---|---|---|---|---|---|---|---|
| Case mod. | encoder | 13.5 | 1.5 | 5/9 (4 raised) | 3.6 → 69.9 | 67.1 (6.7) | 2.22 → 0.68 (7/9) | 101 | undetermined (disruption) |
| Case mod. | memory | 13.5 | 13.4 | 7/9 (2 raised) | 3.6 → 3.0 | 1.2 (6.7) | 2.22 → 2.31 (5/9) | 101 | guard passed |
| Case mod. | actor | 13.5 | 14.7 | 2/9 (7 raised) | 3.6 → 2.6 | 1.4 (6.7) | 2.22 → 2.44 (1/9) | 101 | guard passed |
| Case mod. | critic (null control) | 13.5 | 13.5 | 0/9 | 3.6 → 3.6 | 0.0 (6.7) | 2.22 → 2.22 | 101 | identical to live |
| Case mod. | all | 13.5 | 8.6 | 6/9 (3 raised) | 3.6 → 54.3 | 50.7 (6.7) | 2.22 → 0.85 (6/9) | 101 | undetermined (disruption) |
| Same-seed mod. | encoder | 8.8 | 6.9 | 7/9 (2 raised) | 12.0 → 63.3 | 52.5 (4.4) | 0.77 → 0.95 (6/9) | 101 | undetermined (disruption) |
| Same-seed mod. | memory | 8.8 | 8.7 | 5/9 (4 raised) | 12.0 → 12.0 | 1.5 (4.4) | 0.77 → 0.85 (4/9) | 101 | guard passed |
| Same-seed mod. | actor | 8.8 | 9.1 | 5/9 (4 raised) | 12.0 → 11.5 | 1.1 (4.4) | 0.77 → 0.79 (5/9) | 101 | guard passed |
| Same-seed mod. | critic (null control) | 8.8 | 8.8 | 0/9 | 12.0 → 12.0 | 0.0 (4.4) | 0.77 → 0.77 | 101 | identical to live |
| Same-seed mod. | all | 8.8 | 5.0 | 7/9 (2 raised) | 12.0 → 63.2 | 52.6 (4.4) | 0.77 → 0.82 (7/9) | 101 | undetermined (disruption) |
| Seed-43 mod. | encoder | 5.5 | 2.5 | 3/9 (6 raised) | 25.3 → 65.2 | 40.0 (2.8) | 0.49 → 0.46 (3/9) | 101 | undetermined (disruption) |
| Seed-43 mod. | memory | 5.5 | 9.9 | 4/9 (5 raised) | 25.3 → 20.9 | 6.0 (2.8) | 0.49 → 0.72 (4/9) | 101 | undetermined (disruption) |
| Seed-43 mod. | actor | 5.5 | 4.5 | 4/9 (5 raised) | 25.3 → 25.3 | 3.0 (2.8) | 0.49 → 0.46 (5/9) | 101 | undetermined (disruption) |
| Seed-43 mod. | critic (null control) | 5.5 | 5.5 | 0/9 | 25.3 → 25.3 | 0.0 (2.8) | 0.49 → 0.49 | 101 | identical to live |
| Seed-43 mod. | all | 5.5 | −6.4 | 6/9 (3 raised) | 25.3 → 78.5 | 53.2 (2.8) | 0.49 → −0.42 (6/9) | 101 | undetermined (disruption) |

What it shows:
- **Encoder and all-places freezes break behaviour.** Unhurt dwell jumps to 54–78 % on average, with
  individual checkpoints in both directions: the case agent's encoder freeze gives 0 % unhurt at 8 M and
  96 % at 9 M, and its frozen injury effect ranges from −60 to +23 points across checkpoints. The guard was
  written for exactly this case, and the encoder result says nothing about whether the encoder carries the
  extra hiding.
- **Memory and actor freezes leave behaviour intact in both seed-42 agents, and remove nothing.** The case
  agent's injury effect is 13.5 live, 13.4 with the memory freeze and 14.7 with the actor freeze. The
  same-seed agent's is 8.8, 8.7 and 9.1. The memory freeze "lowers" the effect at 7/9 checkpoints in the
  case agent, but by 0.1 points on average. In the seed-43 agent, the live effect (5.5) is so small that
  even a 3–6-point unhurt change fails the guard.
- **The steady part of the modulator's output at memory and actor is enough** for the behaviour these
  agents show. Whatever the injury-dependent part of the modulator contributes, it is not at those two
  places, in either seed-42 agent.

### 5. Caveats carried from the Implementation Report

- **Readout feature space.** The readouts were fitted on activity centred on the unhurt mean, with one scale
  per layer, not on per-unit z-scores. Per-unit scaling blew up near-silent memory units (unhurt SD about
  10⁻⁵) into shifts of 10⁴ SDs. One scale per layer leaves cosines and the push in readout spreads
  unchanged, but it means the ridge penalty treats all units of a layer alike.
- **Ridge strength** was chosen by single-level grouped 5-fold cross-validation, and the held-out AUC and
  log-loss come from the same folds. The selection is among 5 values, so the optimism is small, but the
  scores are not nested estimates.
- **C1 pools both scenes.** The natural trace for both scenes is the same seed's injured no-animal
  episode. Each scene alone gives the same reading (above).
- **Silent units.** Shifts in units that are silent when unhurt are reported in their own column, not in
  the size. At the encoder's first stage before the modulator acts, the whole felt-injury group is silent
  when unhurt, so its entire shift is in that column.
- **The natural trace sometimes peaks at about 0.70**, not 0.52: in agents whose injured episode never reaches the
  bush (the † checkpoints: 6 of 9 for the seed-43 ordinary agent, 1 each for the case and same-seed
  ordinary agents). Those agents receive a stronger probe, which inflates their shift. The C1 direction
  survives dropping them; the size of the seed-43 reversals in C1 and C2 does not.
- **Encoder groups mix sensors** (the out-of-scope bug above), so no result here can be read per sensor
  at the encoder's first stage.
- **Selection.** The case pair was chosen for its large lead, so condition 1 was biased toward passing. Both
  C1 and C2 failed it anyway.

### 6. What this suggests for the body-only modulator experiment (interpretation, not a finding)

The following is interpretation for the next experiment, [[NMN_INPUT_L05]], in which the modulator reads
only body signals. None of it is supported by a rule passed here.

1. **No internal target to carry over.** No primary cell passed, so the case study gives no mechanism the
   body-only design should aim to strengthen. The body-only experiment should stand on its own behavioural
   readout, as it is designed to.
2. **The all-senses modulator damps felt injury in the main network rather than amplifying it.** From the
   encoder output onward, every modulated agent here (four of four, including the one that hides less)
   shifts less under natural felt injury than its ordinary partner. If the body-only idea works as
   intended, the first internal sign should be this reversing: the encoder-output and memory shift under
   felt injury should match or exceed the ordinary agent's. That is cheap to check with this tooling (Analysis
   1 on the body-only agents' checkpoints), and it is worth fixing as a check before their results are
   read.
3. **Report the two parts of the injury effect separately.** The case agent's lead came from hiding *less
   when unhurt*, not more when injured. The body-only readout should report injured dwell and unhurt dwell
   beside the injury effect, so that a "lead" made of lower unhurt hiding is not mistaken for stronger
   injury-driven hiding.
4. **Use a non-disruptive way to remove the modulator's injury response.** Freezing the gain and offset at
   their average breaks the encoder. In the body-only variant that reads felt injury alone, setting the
   modulator's felt-injury input to its unhurt value removes exactly the injury-driven part and leaves the
   unhurt agent untouched by construction. That would make the "which place carries it" question answerable.
   In the variants with more inputs, the same input clamp applies to the felt-injury channel only.
5. **If C2 is followed up**, it should be pre-registered as one primary measure in the body-only runs, with
   the seed as the unit and the stress-probe and covariate-readout versions stated in advance as secondary.
   Here it depended on the measurement choice and went the wrong way in the fixed-start pair.
6. **Do not use the modulator's own memory as an "acting" measure.** Its injury direction and bush
   direction can nearly coincide, so a push there cannot be separated from simply registering felt injury.

### Related issues

- **Encoder group order** (developer's finding): the hierarchical encoder's first-stage groups receive
  scrambled slices of the observation (sorted group keys against config-order observation). It is not in the
  Known Bugs registry. Owner: `bug-curator` → `senior-developer`. It does not change any number here, but it
  invalidates any per-sensor reading of the encoder's first stage, here and in the body-only experiment's
  encoder.

### Metrics requested

None for training. One analysis-side addition would sharpen Analysis 3 in later studies:

| Subfield | Content |
|---|---|
| **Metric** | Injury effect with the modulator's felt-injury *input* clamped to its unhurt value (percentage points of bush dwell), per freeze place |
| **Why now** | Freezing gain and offset breaks behaviour at the encoder, so C3 is undetermined in every agent |
| **Where it'd live** | `scripts/analysis/obs_manipulation/run.py` (a modulator-only input override) and `case.py a3-*` |
| **Cost** | Cheap: one more live condition per checkpoint, no training |

### Data and code

- Results: `results/analysis/case_l05_s42/` (`a1/`, `a2/`, `a3/a3_effects.csv`, `a3/a3_summary.csv`,
  `checks/`, `scores/c_cells.csv`, `scores/reading_rule.json`).
- Code: `scripts/analysis/case_l05_s42/case.py` (`score` builds C1–C3), `measures.py` (rule and
  measures).
- Analyst's working notes: `tmp/20261008_120000_case_l05_s42_results.md`.

Analysed by: experiment-analyzer (2026-10-08)
