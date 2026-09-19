---
id: 20260919_1317_checks_that_cannot_fail
date: 2026-09-19
time: "13:17"
folder: episode_renderer
tags: [learned_lesson, testing, meta]
summary: "Four checks in one session could not have failed — a unit-green change that broke the product, a fixture that died before its assertion, greps whose patterns could not match, and a pixel census consistent with both hypotheses it was meant to separate."
headline: "Four checks that could not fail in one session, and the cheap guard against each"
related: ["20260919_1315_eval_videos_moved_to_v2_renderer", "20260919_1316_two_modules_one_geometry_drift"]
session_origin: claude_code
session_label: "eval renderer switchover (v4.0)"
importance: high
status: settled
valid_until: null
confidence: high
supersedes: []
raw_source: none
raw_completeness: none
---

# Four checks that could not fail, and the guard that would have caught each

## Key conclusion

A check is worthless unless it can distinguish the world where the claim is true from the
world where it is false. Four checks in a single session failed that test in four different
ways, and each produced a confident wrong conclusion that survived until something external
contradicted it. The cheap guard is always the same: **run the check against the state where
it should fail, before trusting it against the state where it should pass** — and make the
ground truth the rendered or decoded artefact rather than the code's own report.

## Evidence, measurements, facts

- **Unit-green, product-broken.** A minimum-first band allocator passed **18 new unit tests**
  and the full `tests/env` suite, while regressing a previously working configuration end to
  end (zero videos, `TextFitError: caption 'predator-leaning' needs 90px ... its slot is 55px`).
  The tests asserted the *allocation rule*, and the rule had been specified against declared
  minimums that did not match what the painter needed. Reverted, never committed.
- **A fixture that died before its assertion.** A first version of the regression test built a
  bare Matplotlib Axes, but the painter reads `ax._px_w` (`episode.py:304`), so every execution
  case raised in the colour ramp before reaching the geometry it was meant to check. It was
  green for the wrong reason until re-run against the unfixed source.
- **Greps whose patterns could not match.** `grep -c 'one mark per occupied square'` returned 0
  on a page where the phrase was split across a line by `<strong>` markup — the count proved
  nothing about the text it was checking. Separately, `cut -c1-125` truncated exactly where the
  `_v2` suffix would have appeared, so output offered as proof of a repoint showed nothing of
  the kind. A `zsh` glob loop aborted on its first non-matching pattern and reported a total of
  0 while never reaching the directories that held the files.
- **A measurement consistent with both hypotheses.** A pixel census found zero food-coloured
  pixels in a shared World-map cell. That was read as "only one mark is drawn", but it is
  equally the signature of two marks with one painted over — the agent's dot is `0.32 × cell`
  at zorder 6 over a food circle of `0.24 × cell` at zorder 4, so it covers it completely.
  Both hypotheses predict exactly zero pixels. The census could never have separated them, and
  the false conclusion was published before the painter was read.
- **Scale of the consequence.** Across the session seven claims were overturned, including
  three consecutive wrong causes for one refusal. None was caught by the checks that were run;
  each was caught by an external contradiction — a reviewer's measurement, or the user
  counting maps in a published figure.

## Decisions and actions

- **Require a demonstrated pre-change failure.** Every regression test in this work was run
  against unmodified source first, and its failure output recorded, before the fix was trusted
  (`tests/env/test_dashboard_band_span.py`: 15 of 18 failed pre-fix, 18 passed after).
- **Make the end-to-end artefact the gate, not the unit suite.** For renderer work that means
  rendering a real recording and *looking at the frame*: file existence and a green suite both
  passed while the product was broken.
- **Prefer checks whose ground truth is decoded output.** Frame counts read back out of the
  finished MP4 with `ffprobe`, and a WandB artefact downloaded from the cloud and md5-matched,
  both held where self-reported counts would not have.
- **Distrust a measurement that is consistent with the comfortable answer** until it has been
  shown to exclude the alternative.

## Open questions and follow-ups

None. The pattern is recorded; the specific defects it produced are in `KNOWN_BUGS.md`.

## References

- Related: [[20260919_1316_two_modules_one_geometry_drift]], [[20260919_1315_eval_videos_moved_to_v2_renderer]]
- `docs/develop/active/issues/KNOWN_BUGS.md` — the fixed width row carries the three wrong
  diagnoses; its latent height twin is the live instance of the same class.
- Prior art in this wiki: `20260909_1402_parity_gates_green_without_comparing` (`cluster_ops`)
  is the same failure mode in the parity fixtures.
