# Verdict-gate review: modulator engagement check (Results section)

## Verdict (plain language)

**SUPPORTED WITH CAVEATS** for the main conclusion; **one sentence is NOT SUPPORTED by the evidence shown.**

The check asked whether, among nine pairs of agents trained with and without a modulator, the pairs
whose modulator reacts most strongly to felt injury are the pairs where the modulated agent out-hides
its ordinary partner when injured. The Results say no, and that is the right headline. By the rule
written down before any number was computed, the result "counts against" the idea. But two things
about it must be said with it. First, that rule's bar (a correlation at or below zero) is met by
chance about half the time when there is no relation at all, so it means "no support", not "evidence
of the opposite". Second, the negative sign comes almost entirely from the *ordinary* agent.

The claim that does not survive is **"the modulator does carry part of the injury effect"** (freezing
the modulator's gain "removes about half" of the injured agent's extra hiding). The interval crosses
zero. Freezing the gain also roughly doubles how much the *unhurt* agent hides (from 24 % to 47 % of
the time). So a smaller injured-minus-unhurt difference is just as well explained by general
disruption and a ceiling as by the gain carrying the injury signal. This sentence must be downgraded
before the result is reported.

"There are no idle modulators" holds only in a narrow sense: no run is blind to felt injury, and the
runs do not split into two groups.

## Findings

Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run · 🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

| Sev | Location | Issue | Fix | Owner |
|---|---|---|---|---|
| 🔴 | `MODULATOR_ENGAGEMENT_CHECK.md` §What was found item 3; §P-cause "Main 9 pairs, pooled"; commit subject `c092db43` | "The modulator does carry part of the injury effect … removes about half" is stated as a finding. (a) The 95 % CI on the pp removed is [−0.3, 6.4]. 7 of 9 pairs are positive, a one-sided sign-test p of about 0.09. Only 1 of 9 per-pair CIs excludes 0. (b) **Unreported:** freezing changes the agent's behaviour wholesale. Mean bush dwell over the 9 main pairs at E4's checkpoints is: live 30.3 % injured / 23.8 % unhurt; gain frozen 50.4 / 46.8; offset frozen 48.1 / 40.8. The unhurt baseline roughly doubles, and some pairs sit near ceiling (level 05 seed 43, gain frozen: 82 / 78). E3 also shows the gain freeze costs 15–49 survival steps in the training world. A shrunken difference on a doubled baseline is equally explained by generic disruption or ceiling compression. The offset freeze is a partial internal control: it also lifts the baseline (by 17 points against 23) but keeps the effect. That argues against *pure* disruption, but does not rule it out. | Reword (see allowed wording). Report the frozen and live injured/unhurt dwell levels next to the effect, and name the disruption/ceiling explanation as not ruled out. A pre-registered rerun with more episodes, plus a dwell-matched or baseline-normalised effect, is the route to a real claim. | experiment-analyzer |
| 🟡 | §What was found, first paragraph; §P-main | The lead sentence ("the modulators that respond most belong to the pairs where the lead is *smallest*") invites the reading that engagement *harms* hiding. The pre-registered "ρ ≤ 0 → counts against" is honoured. But under a null of no relation it fires about 50 % of the time, so it licenses "no support", not "an inverse relation". The modulated agent's own relation (P-own −0.43) has a lower-tail permutation p of 0.12, so it is indistinguishable from zero. | Keep the label "counts against (pre-registered rule)". Lead instead with "no positive relation between modulator response and the modulated agent's own injury hiding". State that the negative gap correlation mirrors the ordinary partner. | experiment-analyzer |
| 🟡 | §What was found item 2; Bottom line | The gap is dominated by the ordinary agent, and more strongly than written. Within-level SD of the ordinary agent's effect is 3.57 pp, against 1.94 for the modulated agent (variance ratio ≈ 3.4). The demeaned mod/ord effects correlate −0.43, which further inflates the gap variance. Of the gap's within-level variance (22.4), roughly 57 % is ordinary, 17 % modulated and 27 % (negative) covariance. "As large a part as the modulated agent's" understates this. Consequence: P-main is mostly a test of E1γ against the ordinary agent, and should not be interpreted as a statement about the modulator. | Replace with "the ordinary partner's seed-to-seed variation is the larger part of the gap". Read P-own as the substantive modulator test. | experiment-analyzer |
| 🟡 | §What was found item 1; §Contradictions 1 | "There is no idle mode … every run responds" is licensed only at an off-distribution probe. Felt injury held at 0.70 from step 0 lies above the natural peak, which is 0.52–0.53 in all 14 runs; no natural episode reaches 0.65. Under the natural trace, E1γ is 7.3–8.1× smaller (0.032–0.051), about 7–10 % of the gain's across-unit spread, not 53–72 %. The blind-modulator control (< 1e-6) is a trivial floor: any trained nonzero input weight beats it. E2 in the same table shows only 12–21 % of gain variance is time-varying in the training world, which is close to the plan's own definition of "idle" ("close to a constant rescaling") for *every* run. | Allowed: "no run's modulator is blind to felt injury, and the 14 runs do not split into an engaged and an idle group: response strength varies only 1.5-fold". Not allowed: "every modulator is engaged" / "the premise of an idle modulator is false". Report the natural-trace magnitude next to the 0.70 one. | experiment-analyzer |
| 🟡 | §P-cause "Relation to E1γ"; commit subject "unrelated to E1" | "Unrelated" / "does not depend on how strongly it responds" is an underpowered null. There are 9 pairs, per-pair E4 CIs span ±5–25 pp, and within-level E1γ differences are 0.01–0.08 with per-pair SE 0.003–0.009. Level 05's three values are barely resolved. | "No relation was detected; the test cannot exclude a moderate one." | experiment-analyzer |
| 🟡 | §Secondary rows, "How to read" bullet 1 | "Every other way of measuring E1 … gives the same negative sign; the result does not depend on one choice" overstates independence. The rows share the same ordinary-dominated gap. The E1 variants rank the pairs almost identically (the trace/constant ratio is near-constant, 7.3–8.1). So they are one observation re-expressed, not corroboration. | Say "the ranking of pairs by E1 is robust to the choice of E1 variant". Drop "the result does not depend on one choice". | experiment-analyzer |
| 🟢 | §Secondary rows, baseline bullet; E3 bullet | The baseline row (+0.67, p 0.069) is read as confirming "the scene-sharing link". The E3 row (+0.83) carries an interpretive sentence ("agents that depend least … hide more") despite the multiplicity caveat. Both are secondaries among about 15 correlations. Under that multiplicity, one row reaching p ≤ 0.009 (the negative control itself) is also not surprising. | Drop the mechanism sentences, or mark them as speculation. | experiment-analyzer |
| ❓ | §Contradictions 2 | The shared-seed explanation for the +0.78 control is untested. Unknown: whether partners with the same seed share world layout or initial state in training. Chance remains equally live, since the 2-of-216 tail sits among many rows. | Check what the seed fixes in the two partners' training; the follow-up already proposed (mod-vs-ord effect correlation within level) is the cheap test. | experiment-designer |

Verified (no finding): 14/14 pairs included, with no dropped runs. P-main, P-own and the control use
the pre-registered within-level-demeaned 216-arrangement null and the pre-registered primary outcome.
The thresholds were not moved; the opposite-tail p is reported as unused. E1γ's 1.5-fold range (0.248
to 0.372) is correct. E1γ rises from the first to the last third of training in all 14 runs (monotone
in 12; the level-05 fixed-start seed 42 and level-04 original runs dip slightly in the last third).
The P-out descriptions are appropriately hedged.

## Allowed wording per headline claim

1. P-main: "By the rule fixed before computing, the result counts against the engaged/idle idea: the
   modulator's response to felt injury does not predict a larger modulated-agent advantage (ρ = −0.75,
   9 pairs, within level). The negative sign reflects the ordinary partner. The modulator's response
   is not related to the modulated agent's own injury hiding (ρ = −0.43, indistinguishable from zero),
   and a strong positive relation is unlikely."
2. P-own: "−0.43; no positive relation; not distinguishable from zero (lower-tail p 0.12)."
3. Negative control: "+0.78 (p 0.009, uncorrected): the ordinary partner's injury hiding tracks its
   modulated partner's modulator response. The cause is unknown (a shared seed, or chance among about
   15 comparisons). It means the gap measure mostly reflects the ordinary agent."
4. No idle modulators: "No run's modulator is blind to felt injury, and the runs do not split into two
   groups. Under a strong probe the response varies 1.5-fold and grows with training. Under the
   natural injury time-course it is about 8× smaller."
5. E4: "Freezing the gain lowered the modulated agent's injury effect on average from 6.5 to 3.4
   points (95 % CI on the reduction −0.3 to 6.4; 7 of 9 pairs). Freezing also roughly doubled unhurt
   bush dwell. The result is therefore consistent with the gain carrying part of the effect, but
   general disruption is not ruled out. No relation to E1γ was detected (underpowered)."
6. E3 and the other secondaries: "leads, uncorrected", with no mechanism sentence.

## Cost of being wrong

If the E4 sentence stands, the project carries "the modulator's gain causally carries about half the
injury response" into the modulator-input study and possibly a paper, on an interval that crosses
zero and a manipulation that doubles baseline hiding. That is a false causal claim, not a lost run.
The P-main verdict itself is low-risk: nothing is trained, and the honest reading ("no support") is
what the data show.

Reviewed by: plan-reviewer (2026-10-07)
