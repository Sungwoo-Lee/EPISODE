# Algorithmic view of the modulator null — TODO

Running TODO list from the 2026-09-29 conversation on whether the modulated-vs-ordinary
null has an algorithmic cause. Source for a later artifact; items are added as they are
agreed. Evidence and reasoning behind them:
[[CROSS_STUDY_NULL_DOSSIER]],
[[20260929_nmn_null_algorithmic_film_conditions]],
[[20260929_nmn_null_algorithmic_rl_side]].

Tooling plan for the analyses below: [[ALGORITHMIC_NULL_ANALYSIS_TOOLING]]
(`docs/develop/active/neuromodulation/`). Published page: "What Both Agents Compute",
`algorithmic_null.html` in this folder.

## Break the shared starting point

**Why.** Across very different worlds the modulated-minus-ordinary gap is not scattered
the way noise would scatter it — it is pinned near zero (level-05 factorial: +3.6 steps,
16 of 16 worlds the same sign). The code gives a reason the two arms are not independent
agents: the main network's layers are constructed *before* the modulator
(`src/models/recurrent_ppo_network.py`: encoder l.400, actor/critic l.424-429, modulator
l.458), deliberately so the RNG stream is untouched (`neuromodulator.py`, plan D11). With
the same seed the modulated agent's main network therefore starts with *exactly* the
ordinary agent's weights, sees the same environment stream, and FiLM starts near identity
(gain 1 ± 0.3, offset ≈ 0). Small clipped PPO steps can then keep both runs in the same
basin. Test whether the identical results come from that shared start or from a real
equivalence.

**Verified 2026-09-30 on the May replication's seed-42 pair** (resolving a question the
decision-rules author raised): both untrained agents built from one key through the replay /
trainer recipe share **27 of 27 main-network parameter arrays exactly**; both use a plain
`GRUCell`; the only extra parameters are the modulator's 33. The trainer's key splits before
model construction (`train.py` ~l.1152-1207) do not depend on the arm, so the environment
stream is shared as well. *[Corrected 2026-09-30, experiment-designer:]* the May design §3.4
**did** contradict this — its "Seeds" paragraph said "the two agents with the same seed number
get different initial weights". That sentence was wrong and is now corrected there with a dated
note (plan-reviewer re-review R13). Seeds 43 and 44 are still to be checked (decision rules A3
precondition).

- [ ] **Train modulated agents whose main network starts from a different seed than their
      paired ordinary agent.** If the gaps then scatter at the size of ordinary
      seed-to-seed variation, the shared start produced the identical results; if they
      stay pinned near zero, the equivalence is real.
- [ ] **Or keep the same seed but give the modulator a stronger start:** zero-initialised
      heads so FiLM is exactly identity, combined with its own learning rate, so its early
      gradient is not swamped by the ~100x larger main network.

## Measure when the modulator wakes up

**Why.** FiLM's advantage in RL is mostly learning *speed*, yet the modulated agent does
not learn faster. One candidate reason: the modulator only becomes influential late. The
training-health audit found its share of the gradient *grows* over training (40-75% of
the squared gradient norm in encoder and four-site arms by the end, under MC). A
component that only starts working in the second half can shape the final solution —
consistent with the freeze cost — but cannot shorten the early climb, which is where a
speed advantage would appear. Make "wake-up" a measured quantity rather than a story.

Metrics, per run, over training (built run-agnostic so any modulated run can be scored):

- [ ] **Gradient share** — modulator's share of the total gradient per update,
      `‖∇θ_mod‖² / ‖∇θ_all‖²`, split by loss term (policy / value / entropy), since the
      value loss also trains the modulator. Check what the trainer already logs first.
- [ ] **Relative update size** — `‖Δθ_mod‖ / ‖θ_mod‖` against the same ratio for the main
      network. Adam normalises gradients, so gradient share alone can mislead about how
      fast the modulator's weights actually move.
- [ ] **Output activity** — the contextual fraction ρ and the reachable gain swing at each
      of the 50 checkpoints: when does the modulator's *output* start varying with the
      situation? (Swing is already known to grow ~1.64x over training.)
- [ ] **Functional influence** — the freeze-at-mean survival cost at a subset of
      checkpoints (e.g. every 5th): when does the modulation become load-bearing? This is
      the expensive one (paired replays per checkpoint).
- [ ] **Wake-up lag** — the summary number. `t_wake` = first checkpoint where a metric
      reaches 50% of its final value; `t_plateau` = first checkpoint where trailing-window
      survival reaches 90% of its final value. **Lag = t_wake − t_plateau.** A positive lag
      means the modulator wakes after learning has levelled off, so it structurally cannot
      speed learning.

      *Revised 2026-09-29:* "50% of its final value" is met at the first checkpoint by any
      measure that starts above half its final value (the gain swing starts near 61%). The
      headline wake-up point is therefore **the checkpoint where a measure has covered 50% of
      its rise from the untrained network's value (or, for a measure with no untrained value,
      the first available point) to the final value, in the direction the measure actually
      moves**; the literal version is computed and reported beside it.

      *Registered 2026-09-30 (before any wake-up number):* the rule, its noise guard and every
      constant (`noise_k` 3, `sustain` 2, `min_noise_points` 5, `final_k` 3, plateau at 90% of
      the survival rise) are section B2 + `parameters.B2` of
      `algorithmic_null_decision_rules.yaml`; runs in `algorithmic_null_wakeup.yaml`.

Compare across arms: MC vs GAE_NORM (MC agents lean on the modulator ~2x more), and
body-only vs all-senses modulators. The same metrics are the success criterion for the
"stronger start" item above: exact-identity init plus the modulator's own learning rate
should pull `t_wake` earlier and shrink the lag — and if the lag shrinks but learning
speed does not change, late wake-up was not the cause.

Data note: newer runs (Wave 1/2, level-05 factorial, May replication) have 50 checkpoints
and load at HEAD; the site × input grid agents need Stage 1 of the saved-config compat
plan first. Gradient-share and update-size metrics need training logs — if the trainer
does not log them, they apply to future runs only.

## Do the two agents converge on the same computation? (CKA + decoding profiles)

**Why.** Across very different worlds the modulated and ordinary agents come out not just
similar but pinned together. Read positively: both may converge on the same information
processing, fixed by the world's structure rather than the architecture. Understanding
that shared computation comes first; it is what a helpful modulator would have to add to.

Two measures, on identical inputs:

- **CKA** (Kornblith et al. 2019): are two layers' similarity structures the same?
- **Decoding profiles**: do both agents encode hunger, injury, predator distance and value
  (survival steps remaining) equally well, and in the same layers?

Feasibility (checked 2026-09-29):

- **Have:** trajectory stores record `obs_noised`, the exact observation the policy saw, so
  one stored episode can be fed to *both* agents (memory reset at t=0) for row-aligned
  activations. Ground-truth targets per step: `satiation`/`nutrition`, `injury_level`,
  agent and animal positions and states (→ predator distance), episode end (→ survival
  steps remaining). Paired stores that load at HEAD: level-05 factorial (16 pairs), Wave
  1/2 levels, B_olf_only grids. The forward pass already returns the memory state
  (`task_h`). `sklearn` and `pyarrow` are in the env.
- **Missing:**
  - [ ] **Opt-in capture of intermediate layers** in `src/models/recurrent_ppo_network.py`
        — encoder output, GRU output, actor and critic hidden layers, and for modulated
        agents both **pre- and post-FiLM** — with a test that enabling it changes no
        output. (`senior-developer` → `developer`.)
  - [ ] **Teacher-forced replay**: feed a stored observation sequence through an agent
        instead of rolling out the environment (extends `scripts/analysis/nmn/replay.py`).
  - [ ] **CKA and decoding scripts.** Probe train/test split **by episode, never by time
        step** (consecutive steps leak). Pair linear CKA with a rescaling-robust measure
        (SVCCA or cross-network linear predictivity): linear CKA is not invariant to
        per-unit rescaling, which is exactly what the modulator's large constant gain does.
  - [ ] **Seed yardstick.** Compare modulated-vs-ordinary similarity against
        ordinary-vs-ordinary across *different* seeds. The only loadable multi-seed design
        for both arms is the **May replication** (`rppo_cw_mayrep_t1none/t16quad_s42/43/44`,
        launched 2026-09-29 15:36, still training). Its stages are different worlds, so it
        also answers whether the two agents' processing moves together across worlds.

**Decision rules, pre-registered 2026-09-29 before any number existed**
(`algorithmic_null_decision_rules.yaml` in this folder; pinned by sha256 in the three analysis
manifests `algorithmic_null_pilot.yaml`, `algorithmic_null_mayrep_interim.yaml`,
`algorithmic_null_mayrep.yaml`). In short: every modulated-vs-ordinary number is judged against
how alike two ordinary agents from different seeds are. With 3 seeds per agent, "undetermined at 3
seeds" is a legal answer; "same" means "no difference 3 seeds can resolve", not identity. The
level-05 pilot pair gives no verdict at all (it shares one seed, so it has no yardstick). Each
analysis states in advance, in words, the result that would refute "the two agents converge on
the same computation". Open item the rules expose: the tooling plan says a modulated and an
ordinary agent with the same seed start from identical main-network weights, while the May
replication design (§3.4) says they do not; the shared-start reading (A3 pattern a) waits on that
check.

Sequence:

- [ ] Build and validate the tooling on a **level-05 pair** (a tool pilot, not evidence:
      the pair shares a seed, so it has no yardstick).
- [ ] When the May replication finishes: collect stores for all six agents and run the full
      comparison layer by layer, stage by stage.
- [ ] If Stage 1 of the saved-config compat plan is approved: extend to the site × input
      grid, whose body-only arms add a contrast.

## Checkpoint R.2 — designer sign-off of the evaluator's reading (2026-09-30)

**What this is.** The decision rules are written in words. The code that applies them
(`scripts/analysis/nmn/decision_rules.py` and `wakeup.py`) was checked against those words on
made-up inputs, one row per case, in `tests/analysis/test_nmn_decision_rules.py` and
`tests/analysis/test_nmn_wakeup.py`. This sign-off, by the rules' author (`experiment-designer`),
is what registers the code's reading. It came before any similarity, decoding or wake-up result
existed. The rules file is **unchanged** (sha `4c8508af…`), so no manifest was re-pinned.

**Verdict: the 105 existing rows are SIGNED; final R.2 is HELD.** All 105 rows give the verdict
the rules intend. Two behaviours outside the table do not (items 1 and 2 below). Code review
(relayed by the coordinator on 2026-09-30) is also adding rows: non-finite summary → RAISES in
every A1–A4 function, a registered-constant "no sustained crossing" plateau row, and lag
coincidence counted on checkpoint positions. R.2 becomes final when items 1 and 2 and those rows
land and pass. The designer then checks only the new row names and expected verdicts.

1. **A3 under a failed gate or an incomplete yardstick (developer's reading 2: rejected).** The
   code writes the pattern as "none of the three patterns (undetermined at 3 seeds)" and names
   the gate in a separate field. Section 2 of the rules says a failed gate blocks *every* verdict
   word and the output reads "blocked by gate <id>". Gate G5 says every A1–A4 verdict reads
   "undetermined — yardstick incomplete". "Undetermined at 3 seeds" blames the seed count, and
   the remedy that follows from that is more seeds, which is wrong for a gate failure. The A3 text
   lists "a blocked gate" under *none* to say that a blocked layer is never given a pattern. It
   does not choose the word. **Correct reading:** under a failed gate, every A3 layer pattern and
   the A3 study reading are "blocked by gate <id>". With an incomplete yardstick they are
   "undetermined — yardstick incomplete". Both carry the interim prefix under `interim`. This
   matches A1, A2 and A4. Rows to add: "A3 gate failed" → `blocked by gate G1` (layers and study);
   "A3 yardstick incomplete" → `undetermined — yardstick incomplete` (layers and study).
2. **A curve with a non-finite point (`wakeup.py`, reason "curve holds a non-finite point").**
   The rules assign no outcome to this case. The code returns NaN, which silently drops the run
   from `n_def` and moves the sign test's threshold. Under the tooling contract ("a combination the
   prose does not assign raises"), and for the same reason as G5 below, a missing point is a data
   defect, not a result. **Correct reading:** raise `ValueError` naming the run, the measure and
   the checkpoint. Row to add: a curve with one NaN point → RAISES.

Non-blocking: the "why" of A2 row 3 says the gap is 0.083. It is 0.090 (0.61 − 0.52). The verdict
("different") is right.

**FINAL SIGNATURE — R.2 SIGNED (2026-09-30, `experiment-designer`).** Checked against commits
`99758d7f`, `af52af92` and `8c9bca5a`, with all 291 tests in `tests/analysis/` passing. Every one
of the 117 rows of `test_nmn_decision_rules.py` gives the verdict the rules intend, and so do the
B2 rows of `test_nmn_wakeup.py`. The three rejections are implemented as specified:

- the A3 gate word (table 7c: `blocked by gate G1`, `undetermined — yardstick incomplete`, and
  the interim prefix on both);
- a non-finite curve point raises, naming the run, the measure and the checkpoint;
- lag is counted on one checkpoint-position scale (anchored and unanchored curves at the same
  checkpoint → coincident, one apart → coincident, two apart → late; the jittered-grid rows).

Also accepted:

- table 11: every non-finite summary raises. In A3's survival, NaN means a failed computation
  and raises; `None` means "not available" and gives no pattern, as the rules say;
- table 7 row 14: an unknown A1 word raises;
- the registered-constant plateau row, "no sustained crossing" (guard margins 2.96 and 1.66);
- the ridge-grid edge flag;
- A2 row 3's text, now 0.090.

Eight parameters are read but not yet used, because the drivers that use them are not written.
They are listed by name in the perturbation test, which fails if any of them starts changing an
output; that list is not a gap in this table. Rules sha `4c8508af…`, unchanged. **This signature
unblocks the level-05 pilot.**

**The developer's four marked readings.**

- **B2, level-05 "undetermined" → May seeds "do not agree" (rows 2 and 10): confirmed.** "Agree"
  needs a side to agree with. With no level-05 side, the condition fails. The May seeds decide
  nothing, and the report prints their own per-seed lag readings next to the word, so it is never
  read as a contradiction.
- **A3 failed gate → "none …" with the gate in a separate field: rejected** (item 1 above).
- **G5, a run with no stage-1 survival raises: confirmed.** A missing value is not a failed
  competence test. Excluding the run would turn a data gap into an exclusion, and possibly into
  "yardstick incomplete", without anyone seeing it. A run that truly never finished stage 1 is
  taken out of the manifest by a visible, committed edit. (This differs from A3's survival, which
  the rules explicitly let be "not available" → no pattern (c).)
- **The literal "50 % of final" skips the noise guard: confirmed.** It applies `sustain`, so a
  single one-checkpoint excursion never names a point (plan §11's non-monotone row, "same"). It
  applies neither the guard nor the too-few-points refusal. It is never headlined, and its output
  carries the headline's σ_Δ and guard margin beside it.

**Designer decisions.**

- **"No sustained crossing" (rules T5): the rule text stands; no note is needed. The branch is
  live.** The test file calls it unreachable, and my first check agreed for the headline (f = 0.5),
  where only an end-of-curve see-saw reaches it (on the 51-point grid: a plateau just under half,
  then 1.0, 0.49, 1.51, guard margin 1.06; not reachable on the 16-point May grid). Code review
  corrected this for the **plateau** rule (`plateau_f` = 0.9). There the swing that defeats
  `sustain` is only about 0.15 of the rise, so a realistic survival curve reaches it. Re-checked
  here: survival that levels off at 0.85 of its range, then jumps once at the last checkpoint,
  returns "no sustained crossing" with the guard passing (margin 2.96 on 50 points, 1.66 on 15).
  Consequence: a run whose survival is still stepping up at its last checkpoint has an undefined
  plateau. Under Checkpoint 4.0 that stops the GPU sweep and goes to the user, which is the
  intended handling. The current table has no NaN plateau. The registered-constant fixture row that
  code review is adding is the right row.
- **`inner_folds` = 5, in the manifests, not in the rules.** This is the number of grouped
  cross-validation folds used to choose the ridge penalty. It is an estimator setting like
  `bootstrap_n`, `n_per_store` and `ridge_alphas`, not a constant of any decision rule, so a rules
  revision (and the re-pin that comes with it) is not warranted. It is set in the pilot, interim and
  evidence manifests, with its principle stated in the pilot manifest. **`ridge_alphas`** (the
  penalty grid, still missing from every manifest) is the same kind of choice. The developer must
  set it, with a stated principle, before the first real fit, and must not change it after a pilot
  number is seen. *Set 2026-09-30 (coordinator request, before any fit):* `ridge_alphas` =
  19 values from 10^-2 to 10^7 in half-decade steps, in the same three manifests. Principle
  (full text in the pilot manifest): inputs are standardised, so a direction is shrunk by half
  when its correlation-matrix eigenvalue equals alpha / n. Across inner-fold sizes of about 3e4
  to a few 1e5 rows, the grid runs from least squares to shrinking all but the largest few
  directions. It is wide, not tuned. A chosen alpha that lands on an end of the grid is reported,
  never used to move the grid.
- **Wake-up manifest `out_root`** = `results/analysis/algorithmic_null`: the directory that
  already holds the Checkpoint 4.0 table. The table is keyed to the manifest path and the rules
  sha, and neither changed, so it stays valid.
- **Interim `headline_capture` = `{checkpoint: "stage_end:0", probe: active_stage0end}`:
  confirmed** (plan-reviewer Revision 4, R4-2). The rules apply to the interim "unchanged", and
  the descriptive layers exist to show *where* a difference arises. An interim "different" that
  cannot be localised would be unexplainable. The descriptive layers decide no verdict, and the
  cost is about 13 GB. Note that the probe id is `active_stage0end`, not `active`.

**Registered at code review's request (implicit choices, now explicit).**

- **Held-out R²** (A1 predictivity, A2 decoding, the clock baseline) is computed with the total
  sum of squares about the **held-out** rows' own mean (sklearn `r2_score`), variance-weighted over
  output units where there are several. This is the standard out-of-sample R². The layer score and
  the clock score share the same held-out rows and the same sum of squares, so the sign of the
  excess (R² − R²_clock) does not depend on this choice. The a-priori margin
  `beats_clock_margin_r2` = 0.05 is in units of this R², and it was meant for this definition. In a
  bootstrap draw, the mean is that draw's resampled held-out rows.
- **Wake-up noise σ_Δ** is the sample SD of the consecutive differences, with ddof = 1. The rule
  says "SD"; ddof = 1 is the unbiased-variance form. It makes the guard very slightly wider than
  the ddof = 0 form, the conservative direction for the false-wake bound `noise_k` was set
  against.
- **Non-finite summaries raise** in every A1–A4 function (code review). Endorsed: a failed fit must
  never become a verdict word. It is the same principle as item 2, which still applies separately
  to `wakeup.py`'s curve input.
- **Lag coincidence on checkpoint positions** (code review): endorsed, because it implements "|lag|
  ≤ `lag_coincident_max_intervals` checkpoint intervals (the resolution of the checkpoint grid)"
  as written, with level-05 spacings that jitter by tens of episodes. **Condition:** both
  positions are ordinals on one scale, the checkpoint's number in the run's manifest list
  (first checkpoint = 1). An anchored wake-up curve has step 0 at array index 0, while the
  plateau curve has no anchor and starts at checkpoint 1. So the positions must be converted, not
  taken as raw array indices (the plateau table already reports `index + 1`). Row to add: an
  anchored wake-up curve and an unanchored plateau that cross at the same checkpoint → "coincident".
  Late / early still take their sign from the lag in episodes, which is still reported.
- `mm_qualifier` is read from the predictivity summary only: endorsed, since predictivity decides
  the layer verdict.

**Recorded outside the table.** A1 study, remedy: the count covers "undetermined" layers only (not
"uninformative"), and it is reported even when the study reads "different". A3 study reading:
(b) and (b+) are separate patterns, so 2 × (b) + 2 × (b+) + 1 other reads "mixed across layers",
with each layer listed. The refutation section already counts either pattern as support. Both
readings are literal and accepted. Suggested extra rows: an A1 study with one "uninformative"
layer and no "different" layer (→ undetermined), and A4 with co-movement "together", one stage
end "different" and none "same" (→ undetermined).

**Ordering, for the record.** The Checkpoint 4.0 plateau table (survival only, no wake-up
measure, no lag, no decision function called, no verdict word) was produced on 2026-09-30 02:44,
before this sign-off, with the user's explicit authorisation. The designer has not read its
values. It uses no rule this sign-off changes: the plateau goes through the same crossing rule,
and only the non-finite-input fix touches it, which turns a NaN plateau into an exception. Its
`nan_plateau_runs` list is the check. That list is empty (checked at sign-off; no other field was
read), so the table stands. The first
wake-up, similarity or decoding output must still come after the code fixes above.
