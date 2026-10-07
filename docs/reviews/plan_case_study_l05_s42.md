# Plan review: case study of the 22-September level-05 seed-42 pair

## Verdict (plain language)

**NOT READY**, but close: two fixes to Analysis 2, both cheap, before anything is computed.

The plan looks inside one pair of agents, an ordinary agent and a modulated agent, trained on
22 September at level 05 with seed 42. In this pair the modulated agent hides in the bush much more
than its partner when injured. The plan asks three things: does injury change each layer more in the
modulated agent, does that change point toward "going to the bush", and which part of the modulator
carries the extra hiding.

Question 2 is set up so that it can give a positive answer by construction:

1. The "toward the bush" direction is learned from episodes that include injured runs. In those
   episodes, being injured itself predicts going to the bush. So the direction partly *is* the injury
   direction, and the injury change will line up with it in whichever agent hides more when injured.
2. The tool the plan reuses runs the *injured-feeling* copy as the one that moves. So the change is
   measured on the injured agent's own route, which already leads toward the bush more often in the
   agent that hides more.

Both fixes are a single sentence each. With them, and the moderate edits below, the plan is sound for
an exploratory study. The 22-September pair *is* tested in the same neutral scenes as the
replication pairs. The modulator's own memory state is already recorded by the live tool. What is
missing is per-layer capture in live mode.

## Findings

Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run · 🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

| Sev | Location | Issue | Suggested fix | Owner |
|---|---|---|---|---|
| 🔴 | `CASE_STUDY_L05_S42.md` §Analysis 2, "Fitted on the natural episodes: both injury levels" | **The readout is circular.** In injured episodes the agent goes to the bush more, so a logistic readout for "bush soon" uses felt injury as a predictor. That pulls its weight vector toward the injury-coding direction. Projecting the injury shift onto it then returns a positive push by construction. The push is larger in whichever agent's injury predicts the bush more strongly, which is the agent that hides more, i.e. the behavioural result restated. | Fit the readout on **unhurt episodes only** (injury 0, both scenes) as the primary readout. Sensitivity row: fit on both, with injury as a covariate (or with the readout made orthogonal to a felt-injury decoder fitted on the same states). Report the cosine between the readout and that injury decoder for every layer, so leakage is visible. | experiment-designer |
| 🔴 | §Analysis 1 bullet 2 ("Observations and actions stay identical (live mode with a shadow copy, as in E1)") vs `scripts/analysis/obs_manipulation/run.py:126-133` | **The tool does the reverse of what the plan says.** In the live tool the copy that *receives the manipulated felt injury* acts (`action = argmax(lg_a)` with `lg_a = model(obs_m, …)`), and the shadow gets the true observations. The plan says "replay the unhurt episodes" with felt injury set in the second replay. In fact, the states visited are the felt-injured agent's route, so the modulated case agent visits more bush-near states. Combined with the readout, this is a second path to circularity. Analysis 2 also projects onto states that are not the natural unhurt states the readout was fitted on. | Swap the roles for this study: the agent **acts on the true observations** (unhurt route), and the shadow gets felt injury 0.70. This needs a flag in `run.py`, with `--memory sustained` for the shadow. Keep the E1 orientation only as a labelled sensitivity row. State the orientation in the doc. | experiment-designer → developer |
| 🟡 | §Analysis 2 "all nine checkpoints pooled per agent" vs §Reading rule (per-checkpoint counts) | A single readout across 2–10 M steps assumes the units keep their meaning while weights change. The 7/9 rule then needs per-checkpoint values from a readout that is wrong at some checkpoints (most likely early). | Fit **per checkpoint** (held out by episode, ridge strength chosen by cross-validation per layer). Report pooled-fit accuracy only as a drift diagnostic. | experiment-designer |
| 🟡 | §Analysis 2 label "on the bush within the next 5 steps" | Not well defined. (a) Steps already on the bush are trivially positive, so the readout mostly decodes *current position*, not intent. (b) Episodes that end within 5 steps are censored. (c) "On the bush" must use the same cells as `bush_hiding`. (d) Base rates differ about twofold between agents, so accuracy is not comparable. | Label only off-bush steps: "arrives on the bush within 5 steps". Drop the last 5 steps of each episode, or steps where it dies before step t+5. Cite the cell definition used by `bush_hiding`. Score with held-out AUC and log-loss against the base rate, not accuracy. Express (a) in units of the readout's own logit SD over unhurt states, because ridge-shrunk weights make raw log-odds incomparable across layers and agents. | experiment-designer |
| 🟡 | §Analysis 1 felt injury 0.70; §Analysis 2 | Off-distribution probe. The prior verdict gate found the natural peak is 0.52–0.53 in all 14 runs, and none reach 0.65. The response under the natural trace is about 8× smaller. Projecting a 0.70 shift onto a readout fitted on states that never had it is a linear extrapolation: directions with no natural variance get weights set by the ridge penalty, not by the data. | Make the **natural-trace row co-primary for Analysis 2** and keep 0.70 for Analysis 1 as a stress probe, labelled as such. | experiment-designer |
| 🟡 | §Analysis 1 "typical size of that layer's moment-to-moment variation" | Ambiguous, and the choice decides the cross-layer ranking. A step-to-step-change denominator is small for the slow GRU carry and large for the encoder, which inflates memory against encoder. The time window is also unstated (the GRU shift builds over steps). | Define the denominator as **the across-state SD** (square root of the trace of the activity covariance over unhurt live steps, per checkpoint). Report numerator and denominator separately. Fix the window (all valid steps, plus steps ≥ k after onset as a row). Exclude dead units (zero variance) from both terms. | experiment-designer |
| 🟡 | §Reading rule | (i) Checkpoints of one run are strongly autocorrelated: 7/9 measures persistence over training, not replication, and a persistent seed-level difference passes it about half the time with no mechanism. (ii) With the reverse pair's behaviour sign known, each metric has roughly a 1/8 chance of passing all three conditions by chance. Across about 7 layers × 3 measures (size, log-odds, cosine) × 2 felt-injury rows, about 5 "candidate mechanisms" are expected from noise alone. (iii) In the actor layer, "push toward the bush" is close to a restatement of the behaviour, so passing there is expected. | Name **at most 3 primary cells** before computing, for example memory output size, actor log-odds push, and modulator-GRU size. All others are description. State the chance expectation in the doc. Relabel 7/9 as "stable across training", and treat the *pair* (n = 3) as the unit of evidence. Label the actor-layer Analysis 2 result a consistency check, not a mechanism. | experiment-designer |
| 🟡 | §Analysis 3 guard ("unhurt dwell moves by less than the injury effect itself") | (a) It is unclear which injury effect is meant (live or frozen, per checkpoint or mean), and the guard is not stated as absolute. (b) Per-checkpoint noise: 30 episodes per cell, and per-checkpoint E4 intervals spanned ±5–25 percentage points. A zero-effect freeze "lowers" the effect at ≥7/9 checkpoints with probability about 0.09, and that is per site, across 5 conditions. (c) Freezing gain and offset together has never been run (E3 and E4 froze each separately). E4's gain-only freeze already doubled unhurt dwell, so the guard will probably fail for most sites, and the plan does not say what a failed guard means. (d) A ceiling compresses the effect even when unhurt dwell moves little. | Guard: the absolute change in unhurt dwell, averaged over checkpoints, is under half the live injury effect averaged over checkpoints. Also report the effect on the log-odds scale, injured vs unhurt, which is less sensitive to the ceiling. If the guard fails, the result is "**undetermined (disruption)**", never "does not carry". Report survival steps per condition. State the freeze-target pool (both scenes or rabbit only; E4 pooled the rabbit scenes only). Run Analysis 3 on the same-seed replication agent as well, at near-zero cost, since E4's tooling already covers it. | experiment-designer |
| 🟡 | §Analysis 3 "critic" listed as a candidate place | Under greedy evaluation the critic cannot change actions (`recurrent_ppo_network.py:651-663`: the critic feeds only `value`). Freezing it cannot "carry" anything. | Move the critic freeze to a **guaranteed-null control**. Trajectories must be bit-identical to live. Any difference means the pipeline is broken. | experiment-designer |
| 🟡 | §Layers ("capture code does not record [the modulator GRU] yet") | It is the other way round. The live shadow tool already records the modulator's memory (`h_mod`, `h_mod_shadow`, `run.py:157-159`) and the task carry. What it does **not** record is per-layer activity (enc / rnn.out / actor / critic). That lives only in `scripts/analysis/nmn/teacher_forced.py`, which runs in replay mode on stored observations, which these runs do not have. No `src/` change is needed: `forward_with_activations` exists. | Plan the change as "add `forward_with_activations` capture to the live scan in `run.py`, and reuse `teacher_forced._chain` assertions on one checkpoint". Name the file in a File-changes line, and update `SCRIPTS_DEPENDENCY_MAP.md` if callers change. | experiment-designer → developer |
| 🟢 | §Layers ".raw before, .out after" | `.raw` → `.out` also includes the ReLU. `.mod` is the post-FiLM, pre-activation value. `rnn.raw` and the head `.raw` values already carry the encoder's modulation, so ".raw" is not "unmodulated". | Use `.raw` vs `.mod` for "what this site's FiLM adds", and say that upstream modulation is included. | experiment-designer |
| 🟢 | §Question ("11 points more when a predator hunts") | The predator scene is cited in the motivation but is not among the test scenes. | Say that the predator scenes are excluded, and why. | experiment-designer |
| ❓ | §Scenes, case pair | **Partly verified.** The case pair was scored on 2026-09-23 17:44 (`thermalprobe_neutral_clean_rppo.yaml`) with the same probe folder (`behavior_probes/thermal/neutral_clean`) and 30 episodes as the replication spec, after the bush-blocking fix (`a8a9040b`, 17:32). The environment commits since then are shipped inert. E4's live passes reproduced the original rabbit-scene dwell at 125/126 checkpoints, including this pair. **Unverified:** the no-animal scene under current code, and that the saved config, which predates seven current keys, loads through the declared compatibility step rather than a silent default. Training also differed (fixed start temperature; older code), so the replication pairs are comparable in test scenes but not in training. | Run one live no-animal checkpoint per case agent and compare its dwell with the 09-23 CSV before Analysis 1, as a fatal check. Record which compatibility keys were supplied. | experiment-designer |
| ❓ | §Agents | The case pair was *selected* as the largest lead. Its effect, and any internal measure tied to it, will regress toward the mean on retest. Rule 1 is therefore biased toward passing. | One sentence in §Reading rule. | experiment-designer |

## Assumptions

| Assumption | Status |
|---|---|
| Case and replication pairs are tested in the same neutral scenes | Verified (same probe folder, same episode count, 125/126 live reproduction in rabbit scenes); no-animal scene unverified |
| The modulator GRU state is capturable | Verified: it is already in the live tool's carry |
| Per-layer activity is capturable in live mode | Unverified: needs a script change |
| The readout captures intent rather than position or injury | Unverified, and currently false by construction (findings 1, 4) |
| Units keep their meaning across 2–10 M checkpoints | Unverified (finding 3) |
| Freezing gain and offset together leaves behaviour interpretable | Unverified; E4 suggests not |
| The 09-23 saved config loads at current code without silent defaults | Unverified |

## Cost of being wrong

Nothing is trained. The compute cost of a rerun is hours. The real cost is that, as written,
Analysis 2 would very likely report "the modulated agent's injury signal points toward the bush,
consistent across pairs". That would be a restatement of the selection criterion, and it would be
carried into the design of the modulator-input study as a mechanism.

## What would flip the verdict

Fit the readout on unhurt episodes, with the injury-decoder cosine reported. Make the acting agent
follow the true (unhurt) observations. With those two edits the verdict becomes SOUND WITH CONCERNS,
with the Moderate items open.

Reviewed by: plan-reviewer (2026-10-07)
