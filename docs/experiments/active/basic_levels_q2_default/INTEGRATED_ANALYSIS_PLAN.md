# Integrated exploratory analysis — where, when and why does the modulator make a difference?

## Purpose (plain language)

Two agents have been trained in three versions of a grid world: an **ordinary** agent, and one
carrying a **neuromodulator** — a small network that reads the agent's internal state (injury,
hunger, and at the thermal levels body temperature) and rescales signals in the rest of its brain,
FiLM-style. The long-term goal is a modulator that produces behaviour which genuinely depends on the
body's state. This analysis does **not** decide whether the modulator "works". It is a quantitative
survey that gathers clues — **when, how and why** the modulated agent behaves the same as, better
than, or worse than the ordinary one — to choose which directions to explore next (which worlds,
which modulation site, which internal signal, which architecture).

It re-runs the same analyses the project already published for the **Sensor Ladder** and **What
makes this agent hide?**, on the new runs, so every result can be set beside its earlier counterpart
and the effect of each environment update read off. Levels 05 and 06 get extra attention: they were
built to *need* state-dependent behaviour (a third homeostatic need, and smell that degrades with
injury), so they are where a modulator effect should be most likely to appear.

The published page replaces two earlier ones ("The World, Not the Brain" — reused URL, renamed —
and "Level 04, Measured Again" — deleted). "The Last Checkpoint Lies" stays as a separate page on
measurement method.

## Scope

| world | runs (ordinary / modulated) | levels |
|---|---|---|
| blind — olfaction grid, 2026-09-09 | `rppo_olfgae_t1none_s42` / `rppo_olfgae_t16quad_ALL_s42` | one world, no curriculum levels |
| Wave 1 — vision on, 2026-09-21 | `rppo_basicq2_lvl0{2..6}_t1none_s42` / `..._t16quad_s42` | 02–06 |
| Wave 2 — cover heals, two-sided hunger, 2026-09-22 | `rppo_bq2cover_lvl0{2..6}_t1none_s42` / `..._t16quad_s42` | 02–06 |

22 runs, one training seed each. Levels 00/01 are out: no bush at 00, no randomised starting injury
at either.

## Phase 0 — tooling (before any collection)

1. **Late-checkpoint trajectory stores.** New collection spec: for every run, the 5 saved checkpoints
   nearest 80 / 85 / 90 / 95 / 100 % of training, **100,000 episodes each**, `seed_base: 1000000`
   (so every store is paired row-for-row with the existing 1M final-checkpoint stores and across
   runs). Estimated ~1.1 GB per store, ~120 GB total, ~2–3 cluster-hours. Store-based results are
   reported as the spread across the five checkpoints, never the final one alone.
2. **Body temperature as a state** in `scripts/analysis/context_dependence.py`: new `--state body_temp`,
   read from `obs_true` at the Body Temperature slot (index verified against the run's own
   observation breakdown, not assumed). Binned on the degree scale around the setpoint.
3. **Modulator internals on Wave 1/2 runs**: extend the run-name pattern in
   `scripts/analysis/nmn/ckpt_io.py` to recognise `basicq2` / `bq2cover` runs, then run gain
   decomposition (share of gain variance that tracks time vs is fixed per channel), freeze test,
   and a new "what does the gain track" regression of gain on injury / hunger / body temperature.
4. **Ladder figure 3 (how episodes end)** fixed to count over-eating and thermal deaths.
5. **Guards**: every figure script runs the `figguards` checks after layout; the page builder
   asserts `<title>` = `<h1>`, figure order, and every standing requirement.

## Phase 1 — collection

22 runs × 5 checkpoints on free 3090 nodes (106–112 at last check; live GPU + diary pre-flight
before launch). Validate: 401 files per store, contiguous seeds, manifest step equals the requested
checkpoint.

## Phase 2 — analyses, mirroring the earlier pages

Every analysis reports, per world × level: both agents' values and the **modulated − ordinary gap**,
with the spread across the 5 checkpoints; where a run-to-run scale is available (the five-seed
unmodulated reference, blind world only) it is shown as a reference band, labelled as borrowed.

**A. From the Sensor Ladder page**
- A3 how episodes end (fixed) · A4 threat-distance curve · A5 threat discrimination (predator vs
  identical-motion rabbit) · A8 injury dose-response (causal, assigned injury) · A9 sensed vs assigned
  injury and its lag · A10–12 hypervigilance by proximity, by odour, odour false alarm · A13 competing
  drives · A14 robustness to window and variable · A15 price of hiding.

**B. From "What makes this agent hide?"**
- B1 the multivariate hiding model (injury, fullness, predator distance, odour in one fit) — which
  inputs drive hiding in each agent and world · B2 its odour regression.

**C. Modulator internals** (modulated runs only)
- C1 share of gain variance that tracks state, by site · C2 which internal signals the gain follows
  · C3 freeze test (replace the gain with its per-channel average; does behaviour change?) · C4 training
  health.

**D. Controlled-scene probes** (already collected, windowed over the last 20 checkpoints)
- D1 threat ladder and endpoint-vs-window (levels 02–04, blocking bush) · D2 idle hiding across
  training · D3 thermal-comfort scenes at levels 05/06 (four temperature arms; noise-matched at 06).

**E. Levels 05/06 — the levels built to need state dependence**
- E1 body temperature as a state (hiding, fire-seeking, foraging vs coldness) · E2 three competing
  needs (warmth vs cover vs food; uses fire-away / fire-by-bush scenes) · E3 injury-gated uncertainty:
  level 06 vs level 05 on the hypervigilance measures, isolating the smell noise · E4 does the agent
  gap grow with level: a level × agent table across every measure above.

## Phase 3 — page

Title in the family of *"Where Does the Modulator Matter?"* (non-committal). Sections mirror the old
pages' order (A, then B), followed by C, D, E. Each figure leads with the gap by world × level, raw
values beside. Ends with a **clue table**: observation · where it appears · how robust (checkpoint
spread, seed caveat) · which direction it points to explore. No section concludes that the
modulator does or does not work.

## Verification

- Each store: file count, seed contiguity, manifest checkpoint step.
- Each ported analysis: reproduce one published number from its original run first (e.g. a
  sensor-ladder arm's figure-8 value) before trusting it on new runs.
- `body_temp` state: assert the obs slot against the saved config's observation breakdown, and check
  its range matches the thermal physics (settles near −20 away from fire at ambient −30).
- Before publishing: `plan-reviewer` on the page's claims as an analysis verdict; `artifact-format-reviewer`
  on the rendering.

## Known limits, stated up front

One training seed per cell; blind and sighted worlds differ in two ways (vision, and a bush that
blocks predators); the two waves differ in three ways (healing in cover, two-sided hunger,
over-eating death); Wave 1's probe sweeps predate the bush fix and are used only for scenes without
animals.

## Feedback from plan-reviewer (2026-09-23)

**Verdict: NOT READY** — three Critical findings, each of which would put a *wrong* clue on the page
rather than a missing one. Full table, assumption list, exit conditions and owners in
[[plan_integrated_analysis_basicq2]] (`docs/reviews/plan_integrated_analysis_basicq2.md`).

1. 🔴 **Five of the twenty sighted runs never reached 80 % of training** (Wave 1: lvl02 modulated
   5.8M, lvl02 control 8.2M, lvl03 modulated 8.8M; Wave 2: lvl02 control 7.8M, lvl02 modulated
   5.6M, lvl03 modulated 7.4M — the last three still training at 21:04). "Five checkpoints nearest
   80–100 %" collapse to one repeated step for these, so their checkpoint spread is zero and reads as
   robust; and the level-02 gap compares a 56–58 %-trained agent to a 78–82 %-trained one. Gate
   collection on completion **and** on five distinct resolved steps; state a matched-length rule (or
   drop) for Wave 1 levels 02/03. `REANALYSIS_INVENTORY.md` already carries this caveat.
2. 🔴 **100,000 episodes per checkpoint is a third of the sample the ladder page itself documents as
   unreliable** (`sensor_ladder.md:737-745`: the hypervigilance / odour claims flipped between 300k
   and 1M; the odour regression keeps 11 % of episodes). Keep the existing 1M final stores as the
   primary sample for A5, A10–A12, B1, B2; before collecting anything, recompute each ported number on
   the first 20 shards (100k) of its own 1M store and report the shift.
3. 🔴 **Level 02 has no randomised starting injury** (`random_start_injury: false` in its saved
   config; the existing `context/lvl02_*.json` puts every causal-panel row in the injury-0 bin), so
   A8, A9, A10–A12, A13, A14 and E3 are empty there. Other empty cells the plan does not list: no
   thermal at blind/03/04 (E1, E2, D3), no probes for blind (D1, D2), no animal probes for Wave 1
   (D1), and body temperature is never randomised at start, so E1 has no causal panel. Add an
   empty-cell map and have the page builder assert it.

Moderate (see the review for fixes): the collector cannot express "nearest N %" per run from one
spec (`checkpoints:` is spec-global; `resolve_checkpoint` takes exact steps); "401 files per store"
is the 1M count — a correct 100k store has 41; fullness bins are absolute (`NUT_EDGES = [25,50,75]`)
while Wave 2's `max_satiation` is 200 with a setpoint at 100 and Wave 1's is 100 starting full — not
comparable as written; the ported ladder families need `make_manifest.py` / `collect_arm_data.py
--manifest` extended to the waves and to per-checkpoint cells, and the reproduce gate must go
through that new path rather than re-read cached aggregates; only A8 is tagged causal — every figure
needs a causal/observational tag; the five-seed band is from the range-0 `cmp10m` world, not the
blind world; no `SCRIPTS_DEPENDENCY_MAP.md` update named for the new/changed scripts and the `lad03`
fix closes an open Known-Bugs row; the page as scoped (~26 figures × 15 cells) will not be readable —
`FIGURE_PLAN.md` is neither cited nor superseded; the deletion of "Level 04, Measured Again" and the
URL reuse need explicit confirmation; storage is ~6 GB per 100k store (~650 GB), not 1.1 GB; the
modulator-internals family names no checkpoint.

Already done: the `ckpt_io.py` name pattern (Phase 0 step 3) landed in commit `a7b56282`.

Structural check against today's three errors: final-checkpoint reading — prevented for A/B/D, not
for C, hollow for the truncated runs; observed-vs-randomised — **not** prevented (only A8 tagged);
within-run vs run-to-run — partly (band labelled "borrowed", but from a different world, and the
checkpoint spread is not labelled as within-run).

Cost of being wrong: compute and disk are recoverable; the page exists to choose the next
architecture direction, so the cost is a mis-steered direction.

Reviewed by: plan-reviewer

## Revision 2 — after plan-reviewer (NOT READY → exit conditions)

Review: `docs/reviews/plan_integrated_analysis_basicq2.md`. The three Criticals were facts about the
data that this plan got wrong; each is now a rule.

**C1 — unequal training length.** Five runs never reached 80 % of training; three (Wave 2 level 02
both arms, level 03 modulated) are still training as of 21:28. Rule: an agent pair is compared only
at **matched training steps**, over the last 20 % of the SHORTER run, and a store-set counts only if
its five checkpoints are pairwise distinct. Consequences: Wave 1 level 02 is compared at ≤ 5.8 M
steps (58 %), Wave 1 level 03 at ≤ 8.8 M (88 %), both labelled with that percentage; **Wave 2 levels
02 and 03 are marked "still training" and excluded** until their runs finish. The core of the page is
levels 04–06, complete in both waves, plus the blind world.

**C2 — sample size.** The existing **1M final-checkpoint stores are the primary sample** for every
filtered analysis (hypervigilance, odour, the multivariate hiding model, discrimination). Late-
checkpoint stores serve only COARSE measures (causal state span, bush-entry change, how episodes
end, survival), and only if the power check passes: each coarse measure recomputed on the first
100k episodes of its own 1M store (`context_dependence.py --max-blocks 20`) must move by less than
the checkpoint-to-checkpoint spread it is meant to reveal. If it fails, late-checkpoint stores are
not collected and every store-based number is labelled single-checkpoint.

**C3 — empty cells.** An explicit map, asserted by the page builder:

| family | blind | level 02 | level 03 | level 04 | level 05 | level 06 |
|---|---|---|---|---|---|---|
| causal injury measures (A8, A9, A13, A14, context) | ✓ | ✗ no random injury | ✓ | ✓ | ✓ | ✓ |
| hypervigilance, odour, hiding model (A10–12, B1–B2) | ✓ | ✓ observational only | ✓ | ✓ | ✓ | ✓ |
| controlled-scene probes (D1–D2) | ✗ no probe world | W2 only* | W2 only* | ✓ W2 blocking; W1 empty scene only | thermal scenes, W2 | thermal scenes, W2 |
| body temperature (E1, E2) | ✗ | ✗ | ✗ | ✗ | ✓ **observational** (never randomised at start) | ✓ observational |
| injury-gated smell noise (E3) | ✗ | ✗ | ✗ | ✗ | reference | ✓ |
| modulator internals (C) | ✓ | matched steps | matched steps | ✓ | ✓ | ✓ |

\* Wave 2 levels 02/03 pending training completion.

**Moderate findings adopted.** Fullness is binned by distance from each run's OWN setpoint (Wave 1
setpoint = ceiling 100, Wave 2 setpoint 100 of 200) (M3). Every figure is tagged *causal* or
*observational* and the builder refuses an untagged one (M5). The five-seed band is labelled "a
different, simpler world" wherever it appears, and every checkpoint spread is labelled "within one
run" (M6). The page keeps to ~12 figures: A4/A5/A14 to an appendix, A10–12 merged, C4 a table, E4 is
the closing clue table (M8). `FIGURE_PLAN.md` is superseded by this plan (M8). Store-file count is
derived from each spec, not hard-coded (M2). Modulator internals use the same checkpoints as the
behaviour, and the blind runs' saved configs are load-tested first (M11). Any new or changed script
gets its `SCRIPTS_DEPENDENCY_MAP.md` row in the same commit (M7). Storage estimate corrected to
~6 GB per 100k-episode store (M10). The deletion of "Level 04, Measured Again" and the reuse of the
URL were confirmed explicitly by the user on 2026-09-23 (M9); the page keeps that page's correction.
