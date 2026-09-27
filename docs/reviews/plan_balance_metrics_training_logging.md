# Plan review: balance metrics logged during rPPO training

## Verdict

**NOT READY** — one Critical finding (a merge step with no data snapshot and no conflict strategy),
plus Moderate issues. The plan's core technical claims hold: the on/off switch is a static jit
argument that removes the extra operations when off, the extra per-step fields never reach the
training update, and the body-state-before-action pairing follows the project's convention. What
gates it is procedural: the plan proposes merging a feature branch into the shared working tree
without the `results/` snapshot the project requires before any merge, and without saying what
happens when `train.py` conflicts with a parallel session's edits.

Severity legend — 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run ·
🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

## What was reviewed

`docs/develop/active/behavior/BALANCE_METRICS_TRAINING_LOGGING.md` at commits `1b1a4110` and
`9ca368fd`, against `src/models/recurrent_ppo_trainer.py`, `train.py`, `src/environment/{core,sensor,state}.py`,
`scripts/analysis/studies/internal_state_interactions/planner.py`, the study plan Revisions 2–2c,
the Known Bugs registry, and the in-flight saved-config compatibility plan.

## Findings

The full table, assumption list and cost-of-being-wrong statement are appended to the plan doc
under "Feedback from plan-reviewer" and are not duplicated here.

- 🔴 Merge-back without `cp -a results /tmp/results-bk-$(date +%s)` and without a rebase-in-worktree /
  fast-forward-only rule (plan §A9(a), Checkpoint 1). Exit condition: add that step.
- 🟡 Test T7 asserts a −16 °C cell counts as warm, contradicting the plan's own definition (§A4).
- 🟡 The "matches the planner exactly" claim for the warm-cell definition is vacuous for the −16 °C
  diagonal cell, which the planner never modelled; `Bal_TimeWarm` feeds a pass/fail criterion.
- 🟡 T1/T2 do not name a world with thermal and interoceptive nociception on.
- 🟡 Level-05-calibrated thresholds are emitted for every rPPO run in every world with no
  calibration record.
- ❓ Late-death denominator, the felt-buffer zero-start artefact, and pooled-vs-fixed-horizon weighting.

Reviewed by: plan-reviewer
