# Analysis-verdict review: results of the level-05 seed-42 case study

## Verdict (plain language)

**SUPPORTED WITH CAVEATS** for the main verdict. **NOT SUPPORTED** for one headline claim.

The case study looked inside one ordinary agent and one modulated agent, the pair whose modulated agent
showed the largest extra bush hiding after injury. Before computing anything, it fixed three measures and
a rule for when a difference counts as a clue. None passed. That verdict follows the rule as written and
stands.

The claim that does not hold is the one the results section leads with: that felt injury moves the
modulated agents' memory *less* than their ordinary partners', so that the modulator "damps" felt injury.
The study's size measure divides how far injury moves a layer by how much that layer varies across
ordinary moments. In every modulated agent, at every checkpoint, the layer varies more (36 of 36
agent-checkpoints at the encoder output, memory state and memory output). The injury shift itself, in the
memory state's own units, is about the same in both agents. These units can be compared between agents
because the memory state is bounded between −1 and 1. So "shifts less" means "varies more for other
reasons", not "registers injury less". The verdict that no measure qualified survives either way.

The decomposition of the dwell lead ("hides less when unhurt, not more when injured") is correct. It holds
over the replication's full 41-checkpoint window too. It reframes the replication page; it does not
contradict it.

## Findings

Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run · 🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

| Sev. | Location | Issue | Fix | Owner |
|---|---|---|---|---|
| 🔴 | `CASE_STUDY_L05_S42.md` §Results "What was found" (1), Verdict table C1 "Direction reversed", §1 C1 bullets, §2 "From the encoder output onward…", §6 item 2 | The "reverse C1" and "modulator damps felt injury" claims come from the denominator of the size measure, not from the shift. Recomputed from `a1/*.csv` (both scenes, acting on true input). The modulated agent's across-state spread is larger at **9/9 checkpoints in all four pairs** at `enc.out`, `rnn.state` and `rnn.out`. The raw shift (numerator) in the memory state, natural trace: modulated larger at 4/9 (case), 4/9 (same seed), 1/9 (seed 43, dose-confounded †), 6/9 (fixed start). Medians: 1.76 vs 1.83, 1.54 vs 1.84, 1.43 vs 4.64†, 1.65 vs 1.55. Under the equal-dose 0.70 probe, the memory-state numerators are within 2–6 % (6.26/6.65, 6.60/6.46, 5.77/5.90, 5.63/5.75). The memory output's are *larger* in the modulated agent at 8–9/9 in every pair. "Robust to every variant computed" is true, but every variant shares the same denominator. Revision 1 also required "numerator and denominator reported separately", and the results section does not report them. | Withdraw "reverse direction", "general difference between the two kinds of agent" and "damps felt injury". Allowed wording below. Add a numerator/denominator table for `enc.out`, `rnn.state` and `rnn.out`. Rewrite §6 item 2: compare the raw memory-state shift (bounded units) and the across-state spread separately, rather than proposing the normalised size as the body-only check. | experiment-analyzer |
| 🟡 | §2 "From the encoder output onward, modulated agents shift less … in every pair" | It is false past the memory layer even on the normalised measure. At `actor.out` the fixed-start modulated agent shifts more (median 0.48 vs 0.42, 6/9 checkpoints), and at `critic.out` it is 5/9. Section 6.2 repeats "from the encoder output onward, four of four". | Restrict to "at the encoder output and the memory layer, on the normalised measure". Even then, add the denominator caveat above. | experiment-analyzer |
| 🟡 | §4 "The steady part of the modulator's output at memory and actor is enough" / "not at those two places" | Each place was frozen alone. A contribution shared between memory and actor, where either one alone suffices, would also give a null for each single freeze. The all-places freeze is disrupted, and memory and actor together were not run. Per-checkpoint changes are within ±3 points at 8/9 checkpoints in both seed-42 agents. Effects smaller than that cannot be seen. | "Freezing the modulator at the memory or at the actor alone leaves both unhurt dwell and the injury effect unchanged, within about ±3 points. A contribution shared between the two is not excluded." | experiment-analyzer |
| 🟢 | §3 "Acting and noticing can be separated in every main-network layer"; brief: "near-orthogonal … aligned in the modulator's own memory" | These compare two decoder *weight* vectors. In 128 units, two unrelated directions have cosines of about ±0.09, so a median within ±0.06 is what chance gives. It shows the readout does not restate the injury decoder. It does not show that the layer separates the two. In the modulator's 16-unit memory, chance is about ±0.25. Its medians (−0.16 to +0.32) change sign across agents. Only single checkpoints reach 0.81–0.96. "Aligned" overstates this. | Allowed wording below. | experiment-analyzer |
| 🟢 | §3 "the readout mostly reads where the agent is relative to the bush … closer to 'near the bush' than 'intends to go'" | This is inferred from AUC being uniform across layers. It was not tested. | Label it as interpretation. | experiment-analyzer |
| 🟢 | §0 dwell table / §6 item 3 | The case lead comes from low unhurt dwell, but the same-seed pair's smaller lead comes from *higher injured* dwell (20.8 vs 18.7; unhurt 12.0 vs 12.5). The two seed-42 "leads" are built differently. That weakens reading C2's two-pair agreement as a shared mechanism. | Add one sentence. | experiment-analyzer |

## Answers to the five questions

1. **Do the verdicts follow from the pre-registered rule?** Yes. I checked C1 2/1/0, C2 6/6/1 and C3
   (guard fails, 5/9 before the guard) against `scores/c_cells.csv`, `reading_rule.json` and the
   per-checkpoint files. The C2 near miss was not relabelled, and the C3 premise correction is right. The
   rule's measure was the normalised size, so C1 "not a candidate" stands. It also stands on the raw shift
   (case 4/9).
2. **Reverse C1 / "every modulated agent shifts less"?** Not licensed. This is the Critical finding above.
   - Normalisation: the claim comes from the denominator, as shown above. The gain affects the
     modulated layers' scale, but `rnn.state` is not modulated directly and is bounded, so its raw units
     are comparable between agents. There the shift is about equal.
   - Orientation: the reversed orientation gives the same sign, so the claim does not depend on which
     copy acts. But each agent is probed along its own unhurt route (case modulated agent 3.6 % on the
     bush vs 17.6 %), which also shapes the denominator.
   - Natural trace: it is each agent's own injured episode, so the dose depends on the agent's own
     healing. The † cases are disclosed. The constant probe removes the dose difference and leaves the
     same denominator-driven pattern.
3. **Dwell decomposition vs the replication's +9?** It is the same quantity on a subset. The replication
   page's Figure R1 reports injury 70 minus injury 0, as the mean over 41 checkpoints (2–10 M, every
   0.2 M). The case study uses 9 of those 41, the same scenes and the same episodes (exact sweep parity).
   Over all 41, recomputed from the neutral sweep, I get: ordinary 17.6 unhurt and 20.5 injured;
   modulated 4.8 unhurt and 17.4 injured. That is a gap of +9.7, against +11.0 on the 9 checkpoints.
   The decomposition holds over the replication window. It corrects the case study's own Question
   section ("hides more when injured"). It does not contradict the replication page, which already
   describes the modulated agent's calm-scene hiding "starting low … while an ordinary agent sits higher
   and flatter".
4. **Descriptive read as finding?** Three places: the reverse-C1 generalisation, "property of the
   modulated design", and "steady part is enough". The modulator-memory "shifts most in the case agent" is
   correctly labelled as description.
5. **§6 for the body-only experiment?** It is clearly labelled as interpretation. Items 1, 3, 4, 5 and 6
   are reasonable. Item 2 rests on the Critical finding and would fix an artefact as a check for the next
   experiment, so it must be rewritten before it is used.

## Allowed wording per claim

- **No primary cell is a candidate:** as written. Also: "this holds on the raw shift too".
- **C1:** "Not a candidate: felt injury does not move the case modulated agent's memory state more than
  its partner's. On the pre-registered normalised size, the modulated agent's is smaller (7/9, 8/9, 9/9).
  This is because its memory state varies more across states (9/9 in every pair). The injury shift itself
  is about equal in both agents (modulated larger at 4/9 and 4/9 in the seed-42 pairs)." Do not use
  "reverse direction", "general difference" or "damps".
- **C2:** as written ("fails by one checkpoint; small; depends on the measurement choice").
- **C3:** as written ("undetermined (disruption)").
- **Dwell lead:** "The case agent's larger injury effect comes from low unhurt dwell (3.6 % vs 17.6 %;
  4.8 vs 17.6 over all 41 checkpoints). When injured it hides about as much as its partner, or slightly
  less. The same-seed pair's smaller lead is the other way round."
- **"Every modulated agent shifts less from the encoder output onward":** "On the normalised measure, at
  the encoder output and the memory layer, every modulated agent's shift is smaller relative to its
  across-state spread. In raw units the shifts are similar. The spread is larger." Drop "onward".
- **Readout vs decoder:** "The bush readout's weights are no more related to the felt-injury decoder's
  weights than chance in the main network. In the modulator's own memory they are close at single
  checkpoints, with unstable sign."
- **Memory and actor freezes:** "pass the guard. Each alone changes the injury effect by less than about
  3 points. A shared contribution is not excluded."

## Exit condition

To lift the Critical finding: withdraw or reword the reverse/damping claims as above. Add the
numerator/denominator table that Revision 1 required. Rewrite §6 item 2. No recomputation is needed; the
numbers are already in `results/analysis/case_l05_s42/a1/*.csv`.

## Cost of being wrong

Low in compute, high in claims. No rerun is at stake. But "the all-senses modulator damps felt injury"
would enter the body-only experiment as a fixed check and as a written result. That would steer the next
design and a paper sentence on a quantity that measures layer variance rather than injury response.

Note: my own first review recommended the across-state normalisation. It is a reasonable pre-registered
measure for within-agent comparisons across layers. For between-architecture comparisons it needs the
numerator reported beside it, which the plan required and the results omit.

Reviewed by: plan-reviewer (2026-10-08)
