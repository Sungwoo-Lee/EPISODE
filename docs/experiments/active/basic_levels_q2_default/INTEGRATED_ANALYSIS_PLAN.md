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
