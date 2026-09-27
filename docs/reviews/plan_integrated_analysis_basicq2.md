---
title: "Plan review — integrated exploratory analysis of the basic-levels modulator comparison"
topic: basic_levels_q2_default
status: active
created: 2026-09-23
last_updated: 2026-09-23
---

# Plan review — "Where does the modulator matter?" integrated analysis

**Verdict: NOT READY.** Three findings would each produce a wrong clue rather than a missing one.

## Verdict (plain language)

The plan proposes to collect a fresh set of recorded episodes from five late training checkpoints of
every run (22 runs, 100,000 episodes each), then re-run every analysis the project has already
published on its earlier "Sensor Ladder" and "What makes this agent hide?" pages, across three
worlds and five difficulty levels, and publish one exploratory page of clues about when the
neuromodulated agent differs from the ordinary one. The intent is sound and the design correctly
bakes in one of today's three lessons (never read a single final checkpoint). It does not yet bake in
the other two (which panel is causal; whose spread a band shows), and it rests on three facts that are
false on disk:

1. **Five of the twenty sighted runs never reached the 80 % training mark**, and three of them are
   still training as of 21:04 tonight. For those runs the "five checkpoints nearest 80–100 %" all
   resolve to the *same* checkpoint, so their "spread across five checkpoints" is zero by construction
   — which the page would read as *most robust*. Worse, at level 02 the modulated agent stopped at
   56–58 % of training and the ordinary one at 78–82 %, so the level-02 "modulated − ordinary gap" is a
   training-length difference wearing a modulator costume.
2. **100,000 episodes per checkpoint is a third of the sample the project already found unreliable.**
   The Sensor Ladder page carries a correction block recording that its hypervigilance / odour claims
   flipped between 300,000 and 1,000,000 episodes. The odour regression uses only 11 % of episodes
   (exactly one predator and one rabbit), so at 100k it would run on ~11,000.
3. **Level 02 has no randomised starting injury** (`random_start_injury: false` in its own saved
   config; the existing context-dependence result confirms every causal-panel row lands in the
   injury-0 bin). Every injury-causal family the plan lists — dose-response, sensed-vs-assigned,
   the three hypervigilance figures, competing drives, window-and-variable, and the level-06-vs-05
   thread — is empty at level 02. The plan says only levels 00/01 lack it.

What flips the verdict: gate collection on training completion and on five *distinct* resolved
checkpoint steps per run (or state a matched-training-length rule for levels 02/03 and label them);
keep the existing 1,000,000-episode final-checkpoint stores as the primary sample for the
small-cell measures and use the late-checkpoint stores as a stability check on the coarse ones; and
publish an empty-cell map before the figure build. Details and exit conditions below.

Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run ·
🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

## Findings

| # | Sev | Location | Issue | Suggested fix | Owner |
|---|---|---|---|---|---|
| C1 | 🔴 | plan §Scope table; §Phase 0 step 1; §Phase 1 | Runs that never reached 80 % (last checkpoint under `models/`): Wave 1 lvl02 modulated **5.8M**, lvl02 control **8.2M**, lvl03 modulated **8.8M**; Wave 2 lvl02 control **7.8M**, lvl02 modulated **5.6M**, lvl03 modulated **7.4M** — the last three still writing checkpoints at 20:47–21:04. "Nearest 80/85/90/95/100 %" resolves to one repeated step for these (e.g. `[5800019 ×5]`), so the five-checkpoint spread is zero and reads as robust; and the level-02 gap compares a 56–58 %-trained agent against a 78–82 %-trained one. `REANALYSIS_INVENTORY.md §Known caveats` already records the Wave 1 truncation; the plan drops it. | Phase 1 pre-flight: every run's max checkpoint ≥ the budget **and** the five resolved steps are pairwise distinct — refuse otherwise. For Wave 1 levels 02/03 (permanent), either drop them from the store-based grid or collect *both* arms at matched steps (e.g. both at ≤5.8M for level 02) and label the column "matched at N %"; never mix. Wait for Wave 2 lvl02/03 to finish. | experiment-designer |
| C2 | 🔴 | plan §Phase 0 step 1 (100,000 episodes) vs `docs/experiments/active/sensor_ladder/sensor_ladder.md:737-745` | The ladder's own correction: at 300k/arm the hypervigilance split held in 14/14 arms and the sight/no-sight split was claimed; at 1M neither held. The plan's per-checkpoint sample is 3× smaller than the sample that produced that artefact. Denominators (`sensor_ladder.md:203-213`): odour regression 11 % of episodes → ~11k at 100k; rabbit-odour and distance figures ~66 %; the hypervigilance cells are a quarter of that by injury and a slice by distance. | Keep the 1M final-checkpoint stores (already on disk for 20 of 22 runs) as the primary sample for A5, A10–A12, B1, B2; use the five 100k stores only for A3/A4/A8/A13/A15-class measures with a pre-stated minimum row count per cell. **Before collecting anything**, recompute each ported figure's published number on the first 20 shards (100k episodes) of its own 1M store and report the shift — this is the power check and costs nothing. | experiment-designer |
| C3 | 🔴 | plan §Scope ("Levels 00/01 are out … no randomised starting injury at either"); §Phase 2 A8–A14, E3 | Level 02's saved config: `random_start_injury: false` (Wave 1 lvl02 `models/config.yaml:126`); `results/analysis/basicq2_w1/context/lvl02_*.json` `randomised_early` puts 100 % of rows in `injury 0`, `cells_used = 1`. Every injury-causal family is empty at level 02; a figure script fed this cell will either crash the build or draw a gap from an empty bin. Other structurally empty cells the plan never lists: blind world → no thermal (E1/E2/D3), no probe battery (D1/D2); levels 03/04 → no thermal (E1/E2/D3); Wave 1 → no animal probes on the fixed bush (D1 Wave 1 column); body temperature is never randomised at start (no `random_start_*temp*` key) → E1 has **no causal panel at all**. | Add an "empty-cell map" table to the plan (world × level × family) with the reason per cell, and have the page builder assert each figure's declared empty cells against the data it actually finds. Restrict level 02 to A3/A4/A5/A15/D1. Mark E1 "observational only". | experiment-designer |
| M1 | 🟡 | plan §Phase 0 step 1 ("new collection spec") | The collector cannot express "nearest N % per run": `checkpoints:` is spec-global (`run_collection.py:167`), the only per-run override is `seed_base` (`:166`), and `resolve_checkpoint` accepts `final` or an exact step (`collect_trajectories.py:140-146`). Exact steps differ per run (8000007 vs 8000012 …). | Decide: 22 one-run specs, or a collector change (per-run `checkpoints` override or a percent syntax) with a test and a same-change `SCRIPTS_DEPENDENCY_MAP.md` row. Say which in the plan. | developer |
| M2 | 🟡 | plan §Phase 1 / §Verification ("401 files per store") | 401 is the 1M-episode count (200 shards × 2 tables + manifest). At 100k with `shard_episodes: 5000` a correct store has **41** files; the check as written fails every correct store (or `shard_episodes` must drop to 500 and the plan must say so). | Derive the expected count from the spec (`ceil(episodes/shard) × 2 + 1`). | experiment-designer |
| M3 | 🟡 | plan §Phase 2 A13, B1; any `--state nutrition` | Fullness scale differs by wave: Wave 1 and blind `max_satiation: 100`, start 100 (full, one-sided); Wave 2 `max_satiation: 200`, setpoint 100, start 100 (two-sided). `NUT_EDGES = [25, 50, 75]` are absolute (`context_dependence.py:86`) and the `nutrition` column is raw state (`trajectory_store.py:126`). "≥ 75" means near-full in Wave 1 and 37 % of maximum in Wave 2; B1's fullness coefficient is monotone in Wave 1 and U-shaped in Wave 2. | Bin fullness as distance from each run's own setpoint (read from its saved config), or split Wave 2 into under/over-setpoint terms; state the rule on every fullness figure. | experiment-designer |
| M4 | 🟡 | plan §Phase 0 (missing step); §Verification ("reproduce one published number") | The reusable ports (`grid_ladder_figures.py`, `injury_dose_response.py`, `olf_hypervigilance.py`, `olf_window_and_variable.py`) read `ladderstyle/` aggregates written by `studies/sensor_ladder/collect_arm_data.py --manifest`, whose manifest comes from `make_manifest.py` — `GRIDS` knows four grids, one store per cell, neither wave. That tooling step is absent from Phase 0. And the reproduce gate as written can pass by re-reading cached aggregates (`_ladder.load_all()`), which exercises none of the new path — circular. | Add the manifest/aggregation step to Phase 0. Make the gate: run `collect_arm_data.py --manifest` through the *new* manifest on one ladder arm's store and diff against `results/analysis/ladder/<arm>.json`; then the 100k-subset variant from C2. | developer |
| M5 | 🟡 | plan §Phase 2 (every family except A8) | Today's error #2 (reading the confounded observed panel) is not structurally prevented: only A8 is tagged causal. B1 is the whole-episode carried-injury model (dilution documented in the dependency map's `olf_window_and_variable.py` row; `hiding_drivers.py:214` contemporaneous-binning bug still open, registry row "hiding-drivers cross-tabs bin injury from the same step"). E1 is observational by construction (C3). | Tag every figure "causal (assigned at t = 0)" or "observational"; the clue table gets a column for it; the page builder refuses an untagged figure. | experiment-designer |
| M6 | 🟡 | plan §Phase 2 preamble ("five-seed unmodulated reference, blind world only") | The five seeds are the `cmp10m` runs — olfactory range 0, observation width 27, a different environment (`make_manifest.py:34-41`; the dependency map says the olf grids "get no band and say so"). They are not the blind world's own seeds. And the checkpoint spread is within-run policy drift, not run-to-run — today's error #3. | Label the band "seed spread from a different world (range-0 blind)", or drop it; print "spread = within-run checkpoints" on every figure that shows one. | experiment-designer |
| M7 | 🟡 | plan §Phase 0 steps 2, 4; §Phase 3 | Maintenance contracts unmentioned: changed/new scripts (`context_dependence.py --state body_temp`, `lad03` fix, new spec, new figure scripts under `studies/basicq2_waves/`, any collector change) require a same-change `SCRIPTS_DEPENDENCY_MAP.md` update; the `lad03` fix closes Known-Bugs row "how episodes end hardcodes three outcomes" — cite it and hand the row to `bug-curator`. | Add both to the plan's file-changes list. | developer, bug-curator |
| M8 | 🟡 | plan §Phase 2–3 (page size); sibling docs | ~26 figures × (3 worlds × 5 levels) × (gap + raw) is not one readable page. Two sibling plans in the same folder — `FIGURE_PLAN.md` (three revisions) and `REANALYSIS_INVENTORY.md` (which tiers A4/A5/B2 as "skip: about the world, not the question") — are neither cited nor superseded. | Say this plan supersedes `FIGURE_PLAN.md` (status + links) and overrides the inventory's tiering by user choice. Suggested cuts: A4/A5/A14 → appendix; A10–A12 → one three-panel figure; C4 → a table; E4 *is* the clue table, not a separate figure. | experiment-designer |
| M9 | 🟡 | plan §Purpose ("Level 04, Measured Again" — deleted; "The World, Not the Brain" — URL reused) | Deleting a page published at 20:51 today and overwriting another's URL are irreversible, outward-facing steps buried in the preamble. The artifact guide keeps corrections on the page. | Call both out for explicit user confirmation at publish time; keep the level-04 correction visible on the new page. | experiment-designer |
| M10 | 🟡 | plan §Phase 0 step 1 ("~1.1 GB per store, ~120 GB total") | A 1M store is 57–65 GB on disk (`du` of the Wave 2 lvl06 and Wave 1 lvl02 stores), so a 100k store is ~6 GB and 110 of them ~650 GB. NAS has 34 TB free, so space is not the risk; the unestimated cost is the analysis scans — `hiding_drivers` is serial and NAS-bound (7–12 GB per store per the map) × 110 stores × families. Collection time (Wave 2's six 1M stores ran 15:14→15:49) is plausible. | Re-estimate storage; add a scan-time estimate; this strengthens the C2 fix (fewer, larger stores). | experiment-designer |
| M11 | 🟡 | plan §Phase 2 C1–C3 | No checkpoint is named for the modulator internals — the one family the "never the final alone" rule does not cover. The freeze test rebuilds the environment from the saved config (`replay.py:74-84`); Known-Bugs row "a finished run's saved config stops loading once a new key becomes mandatory" — untested for the 2026-09-09 blind runs. Freeze metric is survival steps (`run_freeze.py:154`) — compliant. | Run C1–C3 on the same five checkpoints; verify the blind runs' saved configs load with today's code before counting on C3 for the blind column. | developer |
| L1 | 🟢 | plan §Phase 0 step 3 | The name-pattern extension already landed (`ckpt_io.py:53-57`, commit `a7b56282`, same commit as the plan). `discover_runs` still defaults to the two old grids — pass `--grids basicq2 bq2cover`. | Mark done. | — |
| L2 | 🟢 | plan §Phase 2 preamble (world × level grid) | Blind has no level and a different world (olfaction-only, non-blocking bush, width 47). As a column in a level grid it implies an ordering. | Draw it as a detached column labelled "blind (no level; closest to the 03/04 world)". | experiment-designer |

## Assumptions the plan rests on

| assumption | status |
|---|---|
| All 22 runs reached the full budget, so five late checkpoints exist per run | **false** — see C1 (verified on disk) |
| 100k episodes per checkpoint is enough for every ported measure | **unverified, contradicted** by the ladder's own 300k→1M correction — see C2 |
| The collector can select "nearest N %" per run from one spec | **false** — see M1 |
| Every level 02–06 has randomised starting injury | **false** at level 02 — see C3 |
| Fullness bins mean the same thing in both waves | **false** — see M3 |
| The blind world has a five-seed reference of its own | **false** — different world — see M6 |
| Body temperature is delivered raw in `obs_true` | **verified** — `sensor.py:573` ("raw degrees") |
| Body temperature can be randomised at start for a causal panel | **false** — no such key in the saved config |
| The 09-09 blind runs' saved configs still load for replay | ❓ unverified — see M11 |
| Late-checkpoint 100k stores are paired row-for-row with the 1M stores | statistically yes (same `seed_base`, same checkpoint); not bit-identical (Known-Bugs row on reset compilation drift) — fine |
| Nodes 106–112 are free | live state; the plan correctly defers to a pre-flight |

## Project-rule check

- Survival steps, not reward: no reward-based measure in the plan; the freeze test reports survival
  steps explicitly. Pass.
- No fallback defaults: the plan says the body-temperature slot is read from the run's own breakdown
  and verified, not assumed. Pass as stated; the implementation must raise on a missing slot.
- Maintenance contracts: **missing** (M7).
- Version numbers: none invented. Pass.
- Data-loss hazards: none — no git operations, no deletions under `results/`.

## Structural check against today's three errors

| error | prevented? |
|---|---|
| reading a behaviour off the final checkpoint | yes for store-based families (five checkpoints, "never the final alone"); yes for D (last-20 window); **no** for C (no checkpoint named — M11); **hollow** for the truncated runs where the five checkpoints are one (C1) |
| reading the observed panel instead of the randomised one | **no** — only A8 is tagged causal (M5); E1 cannot be causal (C3) |
| quoting within-run spread as run-to-run | **partly** — "labelled as borrowed" is there, but the band is from a different world and the checkpoint spread is not labelled as within-run (M6) |

## What has to change for the verdict to flip

1. C1: a training-completion + distinct-checkpoint gate in Phase 1, and a stated rule for Wave 1
   levels 02/03 (drop, or matched-length with a label).
2. C2: primary sample = the existing 1M final stores for the small-cell families; the 100k-subset
   shift computed on the ladder's own store before any collection is launched.
3. C3: an empty-cell map in the plan, asserted by the page builder.

With those three, the remaining findings are Moderate and the plan can proceed as SOUND WITH CONCERNS.

## Cost of being wrong

If launched as written: one to three cluster-hours and ~650 GB, then a day or two of figure
building — recoverable — but the page's level-02/03 columns would compare half-trained agents to
finished ones, its hypervigilance panels would sit at a sample size the project has already shown
produces artefacts, and its fullness columns would compare different drives across waves. Since the
page's stated purpose is to choose the next architecture direction (hypernetwork vs FiLM-style state
dependence), the real cost is a mis-steered direction, not the compute.

Reviewed by: plan-reviewer (2026-09-23)
