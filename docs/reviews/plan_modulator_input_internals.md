# Plan review: internal-measures screen of the modulator-input study (before any computation)

## Verdict (plain language)

**NOT READY.** Two things must change before anything is computed. Both are cheap.

The plan looks inside four agents whose modulator reads only part of the senses. The modulator is the
small side network that rescales the main network. It asks three questions: does the modulator react to
felt injury, does felt injury move the main network more or less than in an ordinary agent, and how much
of the injured agent's extra hiding goes through the modulator.

1. **The second question repeats a withdrawn claim.** The case study's review found that "the modulated
   agent's memory shifts less with injury" comes from the size measure's divisor. In modulated agents the
   memory varies more for other reasons. The raw shift is about the same in both agents. Prediction P2
   reuses that divided measure, so its outcome is mostly fixed in advance.
2. **The third question is not yet interpretable.** The plan hides felt injury from the modulator only and
   calls the resulting behaviour change "the share that flows through the modulator". It says disruption
   "cannot happen". It can. When injured, the main network sees injury while the modulator signals none,
   a combination that never occurred in training. A drop in hiding could come from that mismatch rather
   than from a route through the modulator. The plan has no condition that tells these apart.

The rest (checkpoints, scene choice, the identity check, Q1) is sound or needs only Moderate edits.

Reviewed by: plan-reviewer, 2026-10-08. Plan: [[MODULATOR_INPUT_INTERNALS]].

## Findings

Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run · 🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

| Sev. | Location | Issue | Fix | Owner |
|---|---|---|---|---|
| 🔴 | `MODULATOR_INPUT_INTERNALS.md` §Measures Q2 (l.63-66), §Predictions P2 (l.84-85), §Question (l.21-22) | Q2 is the case study's normalised shift (shift ÷ across-state spread). The review [[plan_case_study_l05_s42_results]] (Critical row 1) showed the "damping" comes from the divisor. Modulated agents' spread is larger at 9/9 checkpoints in every pair, and the raw memory-state shift is about equal. Every input variant has the same FiLM sites, so its spread is probably larger too. A ratio below 1 is then near-guaranteed for every modulated agent. P2 needs "above 1 in a variant" while "the reference is below 1, as the case study found". That bets against a divisor artefact and cites a withdrawn claim. | Make the raw `rnn.state` shift the P2 quantity (bounded between −1 and 1, so comparable between agents). Report numerator and divisor separately for `enc.out`, `rnn.state` and `rnn.out`, as the review requires. Delete "reverses the damping" and the l.21-22 wording. Use the review's allowed C1 wording instead. | experiment-designer |
| 🔴 | §Q3 (l.30-34, l.67-75) | "The disruption … cannot happen" is not true. Unhurt identity only shows the hook is inert when felt injury is 0. In the injured condition the main network gets 0.70 and the modulator gets 0. Training never produced that combination. A lower injured dwell is consistent with (a) a route through the modulator and (b) the mismatch disturbing the policy. This is the same inference problem that defeated the case study's freeze test (C3). With one seed, a positive share cannot be read. | Add two conditions per scene and checkpoint, using the same episode seeds: **both-hidden** (felt injury 0 for the whole network, an observation-level set) and **main-only-hidden** (modulator gets the true value, main network gets 0). Report share_mod, share_main and share_both. Read share_mod as "route through the modulator" only if share_mod + share_main ≈ share_both, within the paired-episode interval. If they do not add up, report an interaction or disruption instead of a share. Use share_both as the divisor: it is the part of the injury effect that felt injury carries, as opposed to other injury consequences. Add a survival-step guard on every hidden condition. | experiment-designer |
| 🟡 | §Q3 share; §Predictions P3 (l.86-87); 7-of-9 rule (l.79-80) | The share per checkpoint divides by a noisy injury effect (30 episodes per arm). The reference's effects are about 10 pp, against a per-checkpoint standard error of several pp. At some checkpoints the effect will be near 0 or negative, and the share blows up or flips sign. A 0.25 share of a 10 pp effect is 2.5 pp, below per-checkpoint noise. So "≥ 0.25 at 7 of 9" mostly measures noise. Since unhurt runs are identical by construction, the numerator is the paired difference injured_live − injured_hidden on the same episode seeds. | Report the numerator in pp with a paired-episode interval as the primary quantity. Give the share only as a ratio of sums pooled over the 9 checkpoints. Pre-state "share undefined" when the pooled live effect's interval includes 0, and count it as not holding. Raise Q3 to ≥ 100 episodes per arm, or pool, since it is inference-only and cheap. | experiment-designer |
| 🟡 | §Q3 P3 "In the reference it is smaller than in each of them" | Hiding the felt-injury input does not stop injury reaching the modulator indirectly. The injured agent moves differently, heals 25× faster in the bush, and the reference modulator sees vision, smell and the bush. Variants I and IT keep fullness. The share measures only the *direct-input* route, and the reference has the most indirect routes. So "reference smaller" is partly built in. | Call Q3 the "direct-input share" throughout. Treat the reference comparison in P3 as descriptive, with this caveat stated. | experiment-designer |
| 🟡 | §Q3 implementation (l.74-75) "small extension" | The observation tool changes the observation *before* the network. The modulator reads a gather of the observation after symlog (`src/models/recurrent_ppo_network.py:584-587`). For the reference (`"all"`), `mod_in` is the same array the main network uses. So the hide must happen inside the network forward pass, after that branch. That touches the training code path (or an analysis-side re-implementation of `_forward`, which can drift). The felt-injury column within `mod_in` also differs by agent: it is the list position in N/I/IT (0, 1, 2) and the observation offset in the reference. Passing a `{sensor: column}` dict into a jitted function risks the alphabetical-key bug that was just recorded (Known Bugs, "hierarchical encoder … mix of sensors"). | Find the column as `agent.mod_input_idx.index(felt_obs_col)` and pass it as a static int. Do not pass a dict. Keep the `acts=None` training path op-for-op unchanged, and test that. Ground-truth check (not circular): capture `mod_in` into `acts` and assert, on the hidden runs, that the felt column is exactly 0 and every other column equals symlog of the true observation. | developer (via experiment-designer) |
| 🟡 | §Q3 "Variant X … zero by construction; second check" (l.73) | This check is a tautology. With no felt-injury column the hook does nothing, so X proves nothing about the hook. | The tool should *refuse* X for Q3, giving a loud error. Rely on the `mod_in` capture assertion above and on the both-hidden positive control. | experiment-designer |
| 🟡 | §Q1 (l.59-62) | (a) The plan makes the "natural injured trace" primary and 0.70 the stress probe. The engagement check had it the other way round ([[MODULATOR_ENGAGEMENT_CHECK]] l.72, 148). The engagement tool also has two different "natural" rows: `e1*_trace` (teacher-forced along the unhurt route) and `e1nat_*` (separate episodes, flagged *confounded*). The plan names neither. (b) The natural trace is each agent's own healing curve, and healing depends on bush dwell (×25 in cover). So between-agent E1 differences are confounded by the dose an agent's behaviour gives itself. (c) E1 is in absolute gain units. A modulator whose gain varies more overall scores higher for any input. | Name the row (`trace`, teacher-forced). Make 0.70 co-primary for the P1 cross-agent comparison, since it removes the dose confound. Report E1 next to the gain's across-state spread (the tool already emits `gainsd_*`), so P1 does not inherit a scale artefact like Q2's. Add the four runs to `modulator_engagement/runs.py`. | experiment-designer |
| 🟡 | §Outputs (l.93-94); overlap with behaviour session | Q3's live arm *is* the behaviour readout's injury effect, but on 9 of 41 checkpoints. Two different numbers for one quantity can then circulate. | Require per-checkpoint parity: the live (identity) dwell must equal the stage-1 sweep CSV under `results/eval/avoidance/metrics_history_rppo_nmninp/l05_neutral/`. The engagement tool's `_check_sweep` already does this. Quote the live injury effect from the behaviour readout, not from this study. State that P1-P3 inform the user's stage-2 judgement and are not a gate (design §5.1 has no numeric gate). | experiment-designer |
| 🟢 | §Predictions, 7-of-9 | Checkpoints within a run are strongly alike. The case study itself says the evidence unit is the pair. P2 takes "at least one of three" variants, which gives three chances. | One sentence: "7 of 9 is a temporal-consistency description, not independent evidence. P2 has three chances." | experiment-designer |
| ❓ | §Q3 identity | Felt injury is exactly 0 at every step in the unhurt neutral scenes. It is likely: no damaging object, the rabbit's damage is [0, 0], body temperature is pinned at 0, noise is off. But it has not been verified from recorded observations. If any step is non-zero, the identity assert fails mid-run. | Before Q3, read the recorded felt-injury trace of the unhurt natural episodes and assert max == 0. | experiment-designer |

## Checked and fine

- **Checkpoint alignment.** All six runs have a checkpoint within 100 steps of every 2, 3, …, 10 M grid point
  (for example N: 2000026 … 10000025; reference: 2000032 … 10000000). The nearest-checkpoint rule is enough.
- **Main network also gets felt injury.** Yes. The encoder reads the whole observation in every variant, and
  the modulator's copy is a separate gather for N, I, IT and X.
- **Unhurt identity, given the ❓ above.** Holding the modulator's input at 0 when the true value is 0 is a
  no-op (symlog(0) = 0).

## Cost of being wrong

If the plan runs as written, P2 measures the divisor artefact the previous review already withdrew. P3 can
show a "share through the modulator" that is really policy disruption or checkpoint noise. Either would
feed the user's decision to train eight more agents (stage 2, several GPU-days) and could enter the paper
as a mechanism claim. Fixing it now costs two extra inference conditions and a column change in the
predictions.

## Exit condition for the verdict

The verdict flips to SOUND WITH CONCERNS when:

- P2 is restated on the raw memory-state shift, with numerator and divisor reported separately;
- Q3 adds the both-hidden and main-only-hidden conditions with the additivity reading, and the share is
  replaced by a pooled share with an "undefined" rule.
