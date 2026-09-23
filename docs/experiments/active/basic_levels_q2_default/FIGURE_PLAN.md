---
title: "Figure plan for the two-wave internal-state comparison"
topic: basic_levels_q2_default
status: active
created: 2026-09-23
last_updated: 2026-09-23
---

# Figure plan for the two-wave internal-state comparison

## What the page has to answer

Three questions, in order. Each figure below exists to answer one of them, and a figure that
answers none should be cut.

1. **Does this agent's behaviour depend on the state of its own body at all?**
2. **Does a neuromodulator strengthen that dependence?** This is the project's sharp prediction and
   the reason both arms exist. It is an *interaction*, not a main effect: the claim is not "the
   modulated agent behaves differently" but "the modulated agent's response to the outside world
   varies more with its internal state".
3. **Does making cover the only place healing works change either answer?** Wave 1 trained where a
   bush healed no faster than open ground; Wave 2 after that was fixed. This contrast is new and
   could not be asked before 2026-09-22.

The measure throughout is **bush hiding**, and mostly one careful form of it: `B0`, the probability
of *entering* a bush given the agent was not in one and chose a movement action. Entry rather than
occupancy, because a wounded agent mostly freezes to heal, and whether that registers as "hiding"
depends only on whether it happened to stop on a bush. Scoring a decision instead of a location
puts a freezing agent in the denominator rather than the numerator.

## The figures

### A — the two headline answers

**F1. Does injury change behaviour at all?**
The *state span*: baseline hiding when no animal is near, at the lowest injury bin against the
highest. One value per cell.
**Axes.** Horizontal: basic level, 01–06, categorical. Vertical: state span in percentage points —
the difference in bush-entry rate between an uninjured and a badly injured agent, with no threat
present. Paired bars per level (control, modulated), one panel per wave, shared vertical scale.

**F2. Does injury change the RESPONSE TO THREAT?** *(the one that matters)*
The *proximity-effect trend*: how much the predator-proximity effect grows per injury bin. Positive
means a more injured agent reacts more strongly to a nearby threat — the hypervigilance-like
signature. This is the prediction the modulator is supposed to move.
**Axes.** Horizontal: basic level, 01–06. Vertical: percentage points of proximity effect per injury
bin, zero line drawn. Same paired-bar layout as F1.

### B — the check that stops F2 being believed too easily

**F3. Observed against randomised-start.**
The same trend computed two ways: over whatever injury the agent happened to have (associational),
and over the first 25 steps of episodes whose starting injury was *assigned at random* (causal).
They already disagree in sign on one cell — `lvl04_control` gives **+1.02** observed and **−0.95**
randomised — so this is not a formality.
**Axes.** Horizontal: the observed trend, pp per bin. Vertical: the randomised-start trend, same
units. One point per cell, control and modulated in different marks, the y = x line drawn. Points
far off that line are cells where the causal and associational readings disagree.

### C — the raw numbers behind the summaries

**F4. Hiding by injury bin, calm against threatened.**
The table each summary metric is computed from, drawn. Four injury bins × {no animal near, animal
near}, per cell.
**Axes.** Horizontal: starting injury bin (0, 0–25, 25–50, ≥50), categorical. Vertical: bush-entry
rate, percent of eligible movement decisions. Two lines per panel (calm, threatened); one panel per
level; control and modulated overlaid. Small multiples share a vertical scale so heights are
comparable across panels.

### D — the wave contrast

**F5. What the environment change did.**
Bush use with **no animal in the world at all**, Wave 1 against Wave 2. On level 04's control this
moved from near zero to roughly half the episode, which is the environment change doing what it was
meant to do — the bush stops being only a hiding place and becomes somewhere to go and recover.
**Axes.** Horizontal: basic level. Vertical: percent of the episode spent in a bush with no animal
present. Paired bars (Wave 1, Wave 2), control and modulated as separate panels.

**F6. Hiding across training.**
The checkpoint history already produced by the probe sweep, but cross-run rather than one run per
figure: how hiding under a predator develops over 10M episodes.
**Axes.** Horizontal: training, million steps, 0–10. Vertical: percent of the 100-step probe episode
spent in a bush. One line per run; wave by line style, arm by colour.

### E — guards against misreading

**F7. The price of hiding.**
Hiding is not free: a hiding agent is not foraging. Without this, "hides more" reads as "does
better".
**Axes.** Horizontal: bush-entry rate, percent. Vertical: survival steps, the project's performance
measure. One point per cell, wave by mark, arm by colour.

**F8. How episodes end.**
Outcome shares per cell — starved, killed, over-ate, survived.
**BLOCKED**: the existing script recognises only three outcomes and would silently score over-eating
deaths as zero while its bars fail to total 100%. Over-eating is newly reachable in Wave 2, so this
must be fixed before the figure is drawn, not after.

**F9. What each number rests on.**
Episodes and step-rows per cell, which cells are excluded and why.
Level 00 is excluded throughout and not as a failure: it declares `entities: []` and
`obstacles: []`, so it has **no bush and no moving animal** — its "predator" is a static resource.
A bush-hiding measure needs a bush. Levels 05 and 06 are absent from every probe-sweep figure
because the probe scenes contain no heat source and the agent freezes to death inside them.

### F — mechanism, if the behaviour turns out to show anything

**F10. Which factors drive hiding, adjusted for each other.**
A multivariate fit putting internal state (injury, fullness) and the world (predator distance, odour)
in the same model, so an injury effect cannot be a predator effect in disguise.
**Axes.** Horizontal: change in hiding per standard deviation of each predictor, percentage points.
Vertical: predictor, one row each. Control and modulated as paired marks; one panel per level.

## Sequencing, and what is ready now

| figure | needs | ready? |
|---|---|---|
| F1–F4 | the context-dependence JSONs | **Wave 1 yes** (12 cells); Wave 2 as stores land |
| F5 | probe sweep, both waves | partial — Wave 2 has only level 04's control |
| F6 | probe sweep across runs | same |
| F7 | context JSONs + survival from the stores | Wave 1 yes |
| F8 | a fix to the outcome script first | blocked |
| F9 | emitted by the figure scripts | with F1–F4 |
| F10 | the hiding-drivers GLM, not yet run | needs a pass over the stores |

Drawing rules, so these do not have to be re-litigated per figure: one script per figure under
`scripts/analysis/studies/basicq2_waves/`, every figure through `house.py`, used/available counts
emitted by the script rather than typed, and both axes named in words in every caption.

## What would count as a result

Stated before the figures are drawn, so the answer cannot be chosen after seeing them:

- **F2 positive and larger for the modulated arm, on most levels, in both waves** — the prediction
  holds.
- **F2 near zero for both arms** — the modulator does not do the thing it was built to do, on an
  agent that can now see. The two earlier grids found this on a *blind* agent, where "it had nothing
  to gate" was an available excuse. Wave 1 removes that excuse.
- **F1 large but F2 near zero** — injury changes behaviour without changing the response to threat.
  That is the pattern `lvl04_control` already shows, and it is a different claim from either of the
  above: state-dependent behaviour, but not hypervigilance.

---

# REVISION 2 (2026-09-23) — after looking at the figures instead of the measure definitions

The plan above was written from what each measure is *supposed* to show. Opening the rendered
figures and then measuring how much each measure actually varies contradicted it in three places.
The revision is not a refinement; two planned figures would have been flat lines.

## What the rendered figures showed

**Survival is saturated.** `FIG_survival_steps` for level 04's modulated arm is pinned at the
100-step cap in **10 of 12 probe conditions** — the probe episode is 100 steps and the agent simply
survives it unless a predator is present. Measured across all twelve conditions: `survival_steps` is
perfectly flat in 10, `fid` in 8.

**So planned figure F7 — "the price of hiding", survival against hiding rate — cannot be drawn as
designed.** It would be a horizontal line for five sixths of the data. Survival discriminates only
in the two predator probes, and there it varies 70–90. That is a real limit of the probe design, not
of the agent: a 100-step episode with no predator has nothing to kill you.

**The measure that should replace it is `injury_change`** — damage taken over the probe. Its
between-condition spread is **40.1**, by far the largest of the eleven, against `survival_steps`'
8.1 concentrated in two conditions. Damage is the graded outcome that survival is the censored
version of.

**`bush_use_rate` is near-constant** (between-condition spread 0.007) while `bush_hiding` varies
(0.192). Every agent enters a bush at some point in nearly every episode; what differs is how long
it stays. Any figure using "does it use cover" as a contrast is measuring nothing — the contrast
lives in dwell time.

## What the user saw that the plan had missed

Reading the hiding panels rather than the metrics, the difference between arms is **selectivity**:
the modulated agent hides *when a predator is present* and barely at all otherwise, while the
control hides substantially either way. Measured as `hiding under a predator − hiding with no
animal`, per checkpoint, on level 04:

| | mean | sd | checkpoints below zero |
|---|---|---|---|
| Wave 1 control | 50.3 pp | 25.4 | 1 / 50 |
| Wave 1 modulated | 55.4 pp | **15.3** | **0 / 50** |
| Wave 2 control | 34.1 pp | 29.9 | **7 / 50**, worst −29.6 |
| Wave 2 modulated | 55.3 pp | **18.3** | **0 / 50** |

The means differ modestly. What differs sharply is **reliability**: the modulated arm's spread is
about half its control's in both waves and never goes negative, while the control repeatedly hides
*more* when safe than when hunted. Every summary figure in the plan above averages over exactly the
variability that distinguishes the arms, so none of them would have shown this.

## The revised figure set

Replacing F5–F7 of the plan above; F1–F4 (the injury-dependence set, from the trajectory stores)
and F10 (the multivariate fit) stand unchanged.

**R1. Threat selectivity across training.** *(built; new headline)*
Hiding with a predator minus hiding with no animal, per checkpoint, raw plus a rolling median.
**Axes.** Horizontal: training, million steps, 0–10. Vertical: selectivity in percentage points;
zero drawn — at zero, hiding is unconditional; below zero the agent hides more when safe.

**R2. Reliability of selectivity.** The distribution of R1 per arm, not its mean: spread, and the
share of checkpoints falling below zero.
**Axes.** Horizontal: arm × wave, categorical. Vertical: selectivity, percentage points, one point
per checkpoint with the median marked. The claim is about the spread, so the spread is what is drawn.

**R3. Damage taken, replacing survival.** `injury_change` per probe condition and arm.
**Axes.** Horizontal: probe condition, categorical. Vertical: injury accumulated over the 100-step
probe, in injury points. Survival is added as a second panel **for the two predator conditions
only**, with a stated note that it is at the cap everywhere else.

**R4. How long cover is held, not whether it is used.** `bush_hiding` against `bush_entry_step` —
dwell time against how quickly cover is first reached.
**Axes.** Horizontal: step at which the bush is first entered, 0–100. Vertical: share of the episode
spent in a bush, percent. One point per checkpoint; arm by colour, condition by panel.

## What this revision cost, and the rule it suggests

Two of ten planned figures were undrawable and one measure was mis-specified, and all three would
have been discovered only when the figure came out flat. The check that would have caught it is
cheap and mechanical: **before planning a figure on a measure, compute that measure's spread across
the conditions it will be plotted over, and treat a saturated one as unusable.** That is now the
first step of the build rather than a lesson.

---

# REVISION 3 (2026-09-23) — after reading the trajectories instead of the summaries

Revision 2 was written from rendered figures and measure spreads. Reading the raw step-by-step
recordings contradicted it again, and this time the correction is not to a figure choice but to the
central behavioural claim. The recordings were on disk throughout.

## What the trajectories showed

Level 04, Wave 2, final checkpoint, 30 episodes per condition. `hide%` is the share of steps
standing on a bush; `contingency` is that share when an animal is within 2 cells minus when it is
not; `exposure` is the share of steps with an animal within 2.

| condition | arm | hide% | contingency | exposure | mean length |
|---|---|---|---|---|---|
| no animal | control | **86.1** | — | — | 101 |
| no animal | modulated | **5.9** | — | — | 101 |
| no animal, injured | control | 80.2 | — | — | 101 |
| no animal, injured | modulated | **20.8** | — | — | 101 |
| predator | control | 80.1 | **−11.2** | 26.0 | 85 |
| predator | modulated | 58.3 | +1.5 | **56.6** | 75 |
| rabbit chase | control | 78.9 | **−22.2** | 23.8 | 101 |
| rabbit chase | modulated | 22.6 | −10.6 | 59.1 | 101 |
| rabbit wander | control | 65.3 | −13.4 | 12.2 | 101 |
| rabbit wander | modulated | 8.9 | +4.5 | 17.6 | 101 |

**The control is parked.** It stands on a bush 65–86% of the time *whatever is in the world*,
including when the world is empty, and its contingency is **negative in every condition** — it hides
LESS when an animal is close. That is the signature of a default posture from which an approaching
animal occasionally displaces it, not of a response to threat.

**The modulated agent's hiding is conditional.** 5.9% with nothing present against 58.3% with a
predator; 20.8% when injured with nothing present; and it separates threat *types* — 58.3% for a
predator, 22.6% for a chasing rabbit, 8.9% for a wandering one — where the control gives
80.1 / 78.9 / 65.3, near-identical.

**The measurement lesson, which invalidates most of the plan above.** `bush_hiding` as a SHARE OF
THE EPISODE cannot distinguish these two strategies. It reports 80% against 58% and reads as "the
control hides more". Every figure specified in Revision 1 and 2 uses that share.

## Where my earlier readings went wrong, and why

Three successive claims, each drawn from one level up the abstraction ladder and each wrong:

1. From summary metrics: *"the modulator does not strengthen state-dependent threat response"* —
   drawn from the **occupancy** metric, which the analysis script's own docstring disqualifies.
2. From t-statistics across measures: *"the modulated agent is a rover, the control a hider"* —
   drawn from radius-of-gyration means, comparing panels whose y-axes were not shared.
3. From the rendered figures: *"it roams when safe and parks under threat"* — gyration is low
   whenever an agent is parked ANYWHERE, in cover or not, so the measure cannot see cover at all.

Only the recordings distinguish parked-in-a-bush from parked-in-the-open from moving. **The rule
this suggests: for a claim about what an agent DOES, the trajectory is the evidence and every
aggregate is a lossy summary of it. Establish the behaviour from recordings first, then choose
summary measures that preserve the distinction found.**

## The revised figure set

Replacing R1–R4 of Revision 2. F1–F4 (injury dependence from the trajectory stores) and F10 (the
multivariate fit) stand.

**T1. Conditional hiding — the headline.** Share of steps on a bush, per probe condition, both arms.
**Axes.** Horizontal: probe condition, ordered empty → wandering rabbit → chasing rabbit → predator,
categorical. Vertical: percent of steps standing on a bush, 0–100. Paired bars per condition. The
claim is the SHAPE across conditions, not any single height: flat means unconditional, rising means
responsive.

**T2. Contingency — does an animal being close make it hide?** Hiding when an animal is within 2
cells minus hiding when it is not.
**Axes.** Horizontal: probe condition, categorical. Vertical: percentage points, zero drawn.
Negative means the agent hides LESS when the animal is near, which is the control's pattern
everywhere and is the single most diagnostic number in the set.

**T3. Exposure — how often an animal is actually close.** The denominator behind T2, and a cost
measure in its own right.
**Axes.** Horizontal: probe condition. Vertical: percent of episode steps with an animal within 2
cells. The modulated agent is at 56.6% under a predator against the control's 26.0%.

**T4. What injury does when nothing is there.** Hiding with no animal present, uninjured against
injured, both arms. Isolates internal state with the world held empty — no threat to confound it.
**Axes.** Horizontal: starting injury, two categories. Vertical: percent of steps on a bush.

**T5. The cost.** Mean episode length and damage taken, per condition and arm.
**Axes.** Horizontal: probe condition. Vertical: mean steps survived (left panel, note the 100-step
cap) and injury accumulated (right panel). The modulated agent's predator episodes run 75 steps
against 85 — the conditional strategy costs something and the page must say so.

**T6. One episode, drawn.** A single predator episode per arm as a path over the grid, bush and
predator marked, step index along the path. The tables above are counts; this is the thing a reader
can check against the video.

## For the artifact

The page's spine becomes the correction rather than a tidy result, because that is what happened and
it is the more useful thing to publish:

1. **What we set out to measure** — internal-state dependence of hiding, and the modulator's
   predicted effect on it.
2. **What the summary measures said** — no effect, then a rover-versus-hider story. Both wrong, with
   the specific reason each failed.
3. **What the trajectories say** — T1 through T6.
4. **Why the aggregates could not see it** — a share-of-episode statistic is blind to the difference
   between a parked agent and a responsive one, and radius of gyration cannot see cover at all.
5. **What is still open** — one seed per arm; the exposure and survival costs; whether this
   replicates on other levels, where level 02 already shows a different regime.

Corrections stay ON the page rather than being quietly fixed, per the artifact guide. The occupancy
table and the rover claim both appear, marked as superseded, with what replaced them.

---

## Feedback from plan-reviewer (2026-09-23, second-round gate on the null verdict)

The six-cell F1/F2 table built from these figures was reviewed as an analysis verdict and returned
**NOT SUPPORTED BY THE EVIDENCE SHOWN** for the claim as worded ("the modulator does not increase
state-dependence, and vision does not rescue it"). Two Critical findings: F1's "flat ~21 pp across
all six cells" is read from the *observed* panel, and under the randomised-start panel the same
quantity doubles with vision (2.8–4.5 pp blind vs 8.1–8.2 pp sighted); and the "blindness excuse does
not survive" clause rests on one level, one seed, a two-variable step (vision + `blocks_animals`),
and a presence-only visual channel. The narrower "no modulator effect detected at n = 1" is
consistent with the data, including the unreported B0 bush-entry measure this plan itself names as
the headline. Full findings, exit conditions and owners:
[[plan_context_dependence_null_verdict]] (`docs/reviews/plan_context_dependence_null_verdict.md`).
