---
title: "Analysis-verdict review — continual worlds, main runs (does the evidence support 'SUPPORT (fragile)'?)"
topic: continual_worlds
status: active
created: 2026-09-30
last_updated: 2026-09-30
---

# Analysis-verdict review: continual worlds, main runs

## Verdict

**NOT SUPPORTED BY THE EVIDENCE SHOWN — as labelled.** This is a statement about the *argument*, not
a claim that the modulator does nothing. The same data, relabelled as the analysis's own caveats
already imply, would be SUPPORTED WITH CAVEATS.

The study moved two agents — an ordinary recurrent agent and the same agent with a small
"modulator" side-network — back and forth between pairs of harder worlds, and asked whether the
modulated agent drops less at each switch, climbs back faster, does better on returning, and
forgets less. The analysis (design doc §10–§11) answers **"SUPPORT (fragile)"**: the rule written in
advance is met in 2 of 3 sequences, but only under one way of combining the votes.

Two things stop me accepting that label.

1. **The registered rule is not decisive on these data, so "support" is the analyst's pick between
   two registered outcomes.** The design lists Forage — the safe foraging world both agents learned
   *before* the alternation — as stage 1 of every sequence, so counting its forgetting entries is a
   fair reading. But the design also names May's forgetting on the *alternating* worlds as the
   replication target. Count Forage and the support clause fires (2 of 3). Leave it out and §2's
   **refutation** clause fires instead (P1 mixed, P2 all inside noise or beyond noise *against*) —
   under every combination rule, not just R1. The analysis presents this as "fragile support"; the
   honest label is "not decided by the registered rule".
2. **The one positive conclusion the doc draws — "the modulated agent coped better with the first
   switch into an unfamiliar world (smaller drop, faster climb back)" (§11.2) — is confounded with a
   difference that exists before any adaptation happens, and the analysis's own data show it.** The
   forgetting matrix's first row plays the two *starting* checkpoints, frozen, in every world. The
   modulated one survives longer zero-shot in all seven, and in Winter by 18.5 of the 24.5 steps the
   verdict credits to the switch. "Drops less on first entry" is largely "starts higher on first
   entry": a property of this one starting pair, not evidence about adapting.

The analysis is careful and mostly honest — the caveats are all there. What is wrong is the entry
point: the label a reader carries away. Findings below; the exit condition for SUPPORTED WITH
CAVEATS is a relabel and two paragraphs, no rerun.

Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run ·
🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

## Findings

| # | Sev | Location | Issue | Suggested fix | Owner |
|---|---|---|---|---|---|
| C1 | 🔴 | §10.8, §11.1, top results box; commit `d4f6e0cf` subject | The registered rule reaches **both** its support clause (Forage entries counted: R1, R5) and its refutation clause (alternating worlds only: R6, and R5-without-Forage, which the sensitivity table omits — P1 A/B forgetting sums to +14.4 against the modulator; P2 keeps 3 favourable signs but loses its only beyond-noise difference). §2 says refute when "in at least 2 of the 3 sequences the differences have mixed or unfavourable signs, or all lie inside noise": P1 is mixed under every rule; P2 without Forage has one beyond-noise difference and it is *against* the modulator. Choosing the label from the clause that supports is a post-hoc threshold move, however clearly flagged. | Relabel: **"registered rule not decisive — support and refutation clauses both reachable, hinge = whether Forage counts as a world of the sequence for H-forget"**. Add the R5-without-Forage row to 10.9. State the refutation-clause result next to the support-clause result at equal weight. | experiment-analyzer |
| C2 | 🔴 | §10 results box "Where the modulator does look better", §10.10, §11.1 (1), §11.2 first bullet, §11.5 (2) | "Smaller drop / faster climb back on first entry" is not separated from the starting checkpoints' **zero-shot** difference. Forgetting-matrix `start` row (greedy, 2,000 episodes, same seeds): Winter 114.3 vs 132.8 (+18.5), Danger-A 30.3 vs 34.2 (+3.9), Fog-B 38.3 vs 40.3 (+2.0), Famine +5.4, Home +3.2, Nursery +13.4. The first-20k gaps are +24.5 / +4.5 / +5.2. Recovery inherits it: an agent that starts 24 steps closer to the 0.9·R line reaches it sooner without adapting faster. The Home lead (+3.6) is the same one the level-05 factorial flagged as unlicensed (dossier row 6). | Reword to what the data show: *the modulated branch checkpoint survives longer zero-shot in every unseen world (by 2–18 steps); the first-20k advantage is mostly that head start*. If an adaptation claim is wanted, report dip and recovery **relative to the zero-shot level** (e.g. gain over the first 2,000 episodes, or time from the zero-shot level to 0.9·R) as an exploratory, post-data measure. Drop "coped better with the switch" from §11.2 unless it survives that. | experiment-analyzer |
| M1 | 🟡 | §3.4 "Confound (stated)"; §11.5 item 1 | §3.4 says the two agents "differ in initialisation, capacity and seed". Both are seed 42 and, per the parallel study's verified check (`ALGORITHMIC_NULL_TODO.md`, 2026-09-30: 27 of 27 main-network arrays identical, environment stream shared), they start from **bitwise-identical** main-network weights. The confound is therefore the opposite shape: one shared start, perturbed only by the modulator, with no yardstick for how far *any* perturbation of that start would drift. §11.5's fresh-seed recommendation (3.5: seeds 43/44, same-seed pairs) re-creates that pairing and cannot separate modulator from start on its own. | Correct §3.4 with a dated note (as the May design did). In §11.5, require a cross-seed control: ordinary-42 vs ordinary-43/44 **in these worlds** as the noise yardstick, and cross-seed pairs (ord-43 vs mod-44) alongside same-seed pairs — as `tmp/20260930_continual_analysis_plan_v2.md` step 11 already proposes. | experiment-designer |
| M2 | 🟡 | §10.3 P3 first Winter entry; §10.7 row 7.6; §10.8 P3 beyond-noise clause | The only beyond-noise dip (24.5 vs 22.6) is judged against yardstick (c) computed from **two** 200k windows (195.2, 183.9 → SD 7.99). A 200k-window SD is also the wrong scale for a 20k-window quantity: §10.6's own table shows the Winter 20k running mean swinging 60–210 within a visit. Registered as a floor, so not a rule breach — but "just beyond noise by 1.9 steps" against a two-number floor is a coin flip, and Winter recovery (84k vs 196k common) is the first crossing of a line by a curve that oscillates by ±60 steps; the D6 "oscillating curve" caveat is applied to R but not to recovery. | Say in 10.3/10.8 that Winter's threshold is an SD of two windows and that recovery there is a first crossing on an oscillating curve; do not let the Winter dip carry the beyond-noise clause alone. | experiment-analyzer |
| M3 | 🟡 | Results box; §10.5 "Reading"; §11.1 (2) | "Better retention of the foraging world … beyond noise at one or more checkpoints in every sequence" hides that P1's second Danger-A visit **reverses** it (+6.2 against, stage 4), that the effect appears only after Winter / Danger-A stages and never after Fog-B or Famine, that Forage entries are 4 of 7 H-forget votes per sequence (they dominate the tally), that the Forage `from` cell is at ceiling (95.6 % of episodes capped at 500) so baseline Forage competence cannot be compared, and that the three sequences' Forage entries share one checkpoint. An alternative reading the analysis does not rule out: the agent that adapts *less* to the hard world (the modulated agent settles lower in Winter, 174.7 vs 195.2) keeps more of the generic foraging policy — retention as the flip side of weaker specialisation. | State the P1 reversal and the after-which-worlds pattern in the box; name the "less specialisation" alternative and say it is not excluded. | experiment-analyzer |
| M4 | 🟡 | §10.5 deviation (1); §5.3 | The matrix plays the policy greedily; training curves are sampled. The diagonal check verifies each agent's *level* offset (2–18 steps), not that the *between-agent difference* survives the change of policy mode. The headline −112-step Forage entry rests on it. | Cheap check before this number travels: re-run the two cells `P3 end_02_winter × forage` for both agents in sampled mode (≈ 10 min on one GPU) and report whether the gap holds. Pre-register greedy vs sampled for the fresh seeds (already in 11.4). | developer |
| M5 | 🟡 | §10.2 (i); §10.3 tie column; §10.9 | The literal "same logged row" reading is right for 3.7.7 (a), but the parenthetical there ("resolved only to the 4,000-episode logging interval") equally admits "Δ below one logging interval = tie". Under that reading the P3 Winter-return own-episode reading (36,059 vs 40,050; Δ = 3,991) is a tie and P3 H-rec flips from "not favourable" to favourable — no verdict change, but it belongs in 10.9 (R2 is the script's bug, not this reading). Separately, H-dip has **no** tie rule, so +0.4-step (P1 stage 4) and −1.6-step (P3 stage 2) differences count as full votes; the "favourable dip in every sequence" statement rests partly on sub-noise signs. | Add the Δ-below-interval reading as a sensitivity row; say in 10.3 which dip votes are inside 2 steps. | experiment-analyzer |
| L1 | 🟢 | §10.5; §10.1 | Matrix cells record script commit `711b2abb`; the doc cites `c6f33eb3` — cite the commit the cells carry. Row 0 (pre-trained Home checkpoint) was not evaluated although §5.3 lists it; say the omission is conservative (descriptively Home favours the modulator after Winter, 168.6 vs 201.1). Manifest rows 19–24 still "running". | One-line fixes. | experiment-analyzer / experiment-designer |

### On the parent's specific questions

- **(a) Is R1 the most literal reading, or chosen for its answer?** R1 is a defensible reading of
  §2 + Revision 2a + 3.7.7 (b), and so is R5 (§5.2 speaks of a per-sequence difference); both give
  SUPPORT. Of the four "alternatives" that say otherwise, R2 is the script's mis-implementation, R3 is
  stricter than anything registered, and R4 is the *predicted shape*, not the rule. So "4 of 5
  alternatives disagree" overstates the combination-rule fragility. The real hinge is the **H-forget
  entry set** (R6 and R5-without-Forage), not the combination rule — and there the choice does
  decide between the registered support and refutation clauses (C1).
- **(b) Tie rule.** The analysis's correction of the script is right and conservative; M5 notes the
  second reading the registered text admits and the absence of any tie rule for dip.
- **(c) Forage in forgetting.** Registered-consistent (§3.3 lists Forage as stage 1; §5.3 defines
  forgetting for any previously visited world), but so is the alternating-worlds reading (§2's
  replication target). Not post-hoc in the sense of invented; post-hoc in the sense of *picked*
  after seeing which way it falls. Hence C1.
- **(d) Greedy matrices.** Stated deviation; the diagonal check is the wrong check for a
  between-agent claim (M4).
- **(e) Shared start and ceiling.** §3.4's confound statement is factually wrong in a way that
  matters for the next design (M1). The Forage ceiling does not invalidate the forgetting *drops* but
  removes any baseline comparison and is one more reason the Forage entries should not carry a
  verdict (M3).
- **(f) First-entry claim.** Does not survive: it is mostly a zero-shot property of the starting
  pair (C2), on one seed, with the beyond-noise clause resting on a two-window yardstick (M2).

## Assumptions the verdict rests on

| # | Assumption | Status |
|---|---|---|
| A1 | Forage is a "world of the sequence" for H-forget | registered-consistent but contested by §2's own framing; **decides the label** (C1) |
| A2 | First-20k survival after a switch measures adaptation, not the starting policy's zero-shot generalisation | **contradicted** by the matrix `start` row (C2) |
| A3 | Yardstick (c) from 2–3 post-plateau 200k windows is a usable floor for 20k-window quantities | registered as a floor; two-window SD in Winter (M2) |
| A4 | Greedy-mode forgetting differences equal sampled-mode ones | unverified (M4) |
| A5 | The two agents differ in initialisation and seed (§3.4) | **false** — same seed, identical main-network start (M1) |
| A6 | Manifest rows 19–24 are the complete inventory and all finished | verified (§10.1; six run directories present) |
| A7 | Survival steps only; temporal evolution shown | verified (§5, §10.6) |

## What would flip the verdict to SUPPORTED WITH CAVEATS

Relabel per C1 (both registered clauses shown at equal weight; "not decided" as the headline),
reword the first-entry conclusion per C2 (zero-shot head start named; adaptation claim dropped or
re-measured relative to the zero-shot level), and correct §3.4 per M1. No run is rerun; the
sensitivity table gains two rows; the fresh-seed design gains a cross-seed control.

## Cost of being wrong

No compute is at stake in this review. The cost is a label: "modulator supported in continual
worlds (fragile)" has already entered a commit subject and is about to enter the cross-study dossier
and a PI call; carried forward, it steers the seed-43/44 replication (six runs, ≈ 20 h GPU each)
toward a same-seed-paired design that cannot separate the modulator from its shared start, and it
turns a zero-shot generalisation difference of one checkpoint pair into a paper claim about
continual adaptation.

Reviewed by: plan-reviewer
