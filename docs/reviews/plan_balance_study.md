# Plan review — the balance study (Revision 2 of the internal-state interaction study, level 05)

## Verdict

**NOT READY.** Two Critical findings, eight Moderate, one Low, four open assumptions. Both
Criticals are cheap to fix (a criterion redefined, a measurement respecified) and must be written
into the plan before the sweep runs.

**What the plan is, in plain language.** The campfire world (level 05) is the project's main test
of whether a body-conditioned agent behaves differently from an ordinary one. Today the answer to
"what to do when injured" is always "hide in a bush", whatever the agent's hunger or temperature.
New body rules were added to make hunger and cold weigh more — but push them too far and the agent
just forages or warms all the time, and the world is one-sided in the other direction. Revision 2
of the study uses a small simulator of the body rules and an ideal planner (dynamic programming on
a reduced five-place map) to look for **balanced** settings: hiding, eating and warming each take a
real share of time, no single danger causes most deaths, and the best action depends on several
body states at once. It expects an inverted U — balance rises with food/temperature pressure, then
falls as one need takes over. It adds two things the earlier version left out: food that runs out
and moves (E1), and predator hits as discrete events rather than a steady drip (E2). Its second
deliverable is the set of balance measures and thresholds that real training will then be judged
by — which is why a wrong criterion here becomes the yardstick for days of GPU time.

**Why NOT READY.** (1) One of the six balance criteria — "each need is the largest part of the
drive on at least 15 % of steps" — is decided by the map's geometry, not by the settings: no cell
lets the body settle at 0 °C (the warm ring settles it at +5.9 °C, which the drive weighs as 39
units), so a healed, fed agent always has temperature as its largest need, and injury can only be
the largest need for 15 % of a 500-step rollout in a world hostile enough to fail the survival and
cover criteria. The criterion set is likely unsatisfiable by construction, so the study would
report "no balanced world" for a measurement reason. (2) E2, as written, summarises the hit-size
distribution by 5 quantiles — and the measured distribution is 60 % rock scrapes of 1–5 points,
with hits of 100+ (lethal from zero injury) being 3.9 % of hits: the 10/30/50/70/90 quantiles are
1.7 / 3.0 / 4.3 / 25.9 / 66.1, so the lethal tail E2 exists to model is absent from the model. The
hit odds also differ by activity in the direction that decides eat-versus-hide (eating steps are
hit twice as often as moving steps, but by small hits; resting steps rarely, but by large ones),
and the plan splits only rest / not-rest.

**Severity legend:** 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run ·
🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

## Findings

| # | Sev | Location | Issue | Suggested fix | Owner |
|---|---|---|---|---|---|
| C1 | 🔴 | STUDY_PLAN.md § Balance criteria, criterion 2 (B-need) | "Largest component of the drive" is set by the reward's axis weighting (×6.67 per °C) and the map's geometry, not by the settings. Ring settles the body at 8.8 × 0.04/0.06 = +5.87 °C = 39.1 drive units; cold ground drifts toward −20 °C; hunger is held within ±20 and injury heals at 5/step in cover. In steady state temperature is the largest need on nearly every step in every world; injury is largest only in the start transient (starts uniform 0–100 injury, healed in ≤ 20 steps of a 500-step rollout ≈ 2–4 % of steps) or in a world where injury cannot be kept down — which fails criteria 1, 4, 5. Criterion 2 therefore contradicts 1/4/5 and would make the balanced set empty for a reason unrelated to balance. It is also a drive-based (reward-shaped) measure, against the project's survival/behaviour rule. | Drop criterion 2, or make it behavioural: B-time already says which need the chosen activity serves. If a need measure is wanted, use a normalised distance-to-death per axis (steps to death at the current drift) and compare *relative to today's world*, not an absolute 15 %. Whatever is chosen, compute it for today's world first and show the criterion can be met by at least one world before it is used as a gate. | experiment-designer |
| C2 | 🔴 | STUDY_PLAN.md § What changes in the simulator, E2; `measure_world.py:83-96` | (a) 5 quantiles of one pooled hit-size distribution drop the lethal tail: measured on the first Wave-2 block (28,930 hits outside cover), 60.8 % of hits are ≤ 5 (rock scrapes, no animal flag), 12.9 % are ≥ 50 and 3.9 % are ≥ 100; quantiles 10/30/50/70/90 = 1.7 / 3.0 / 4.3 / 25.9 / 66.1. The planner would see no hit that kills below ~34 injury — the opposite of E2's stated purpose. (b) Hit odds differ by activity, not just rest / not-rest: eating 0.056 per step (mean hit 11), moving 0.027 (mean 27), resting 0.0018 (mean 72). The mean-field values (0.63 / 0.71 / 0.13) hide this; under E2 the *shape* differs exactly where the eat-vs-hide trade-off is decided. | Represent hit size by a histogram with fixed bins that include a ≥ 100 bin (e.g. 0–5, 5–15, 15–45, 45–100, ≥ 100), or by source (`hit_predator`, `hit_hiding_predator`, none = rock) with each source's own size law; measure hit probability and size distribution per activity (rest / eat / move-or-idle) from **both** agents and record which is used. Assert p × E[size] per activity reproduces the mean-field hazard. | experiment-designer |
| M1 | 🟡 | § Balance measures, B-time; criterion 1 | "Warming = at the ring" while a warm-bush step counts as cover. On the warm-bush map the open ring is strictly dominated (same cell temperature, no hazard, ×25 healing), so warming ≈ 0 there by construction. Pooled 0.59/0.41, "warming ≥ 10 %" needs ≥ 17 % on the cold map and "cover ≤ 70 %" needs ≤ 56 % there; under "bush on a fire ring: never" both maps collapse to the cold map, so the two bush-fire settings of the 2-D grid are judged against effectively different thresholds. | Count overlapping shares — a step is "warming" if the cell is warm and "in cover" if in a bush, both allowed — or apply criteria per map and require the pass on the majority (no warm bush) map. | experiment-designer |
| M2 | 🟡 | criterion 3 (B-death) | Doomed starts (food ≤ ~2, injury ≈ 100 with a hit, ~1–2 % of starts) are a fixed cause floor; today's ideal-policy survival is 0.96, so the "≥ 5 % of starts die" gate sits on the boundary and the cause shares of ~80–100 deaths per 2,000 starts would be dominated by start-doomed deaths. | Exclude deaths within the first k steps (or starts no policy survives), report the number of deaths per cause, and evaluate the criterion only on that population. | experiment-designer |
| M3 | 🟡 | criterion 6 (B-comb) | The 5-point absolute threshold of Revision 1 is dropped; only "2 × noise floor" remains. The measured floor is 1.0 point pooled (1.6 / 0.2 per map), while the tie margin alone moves today's gain by 2.6 points (0.1135 / 0.1186 / 0.1399 at margins 0 / 0.5 / 2). A +2.1-point gain would be called combinational while being inside the margin's leverage. | Keep the 5-point floor, or use max(2 × grid floor, margin spread). | experiment-designer |
| M4 | 🟡 | § What is swept, food axis and 2-D grid | The food axis (gross 6 / 5 / 4 / 3) has today's value at one end, so a monotone result cannot distinguish "peak at 6 or beyond" from "rising limb". Gross 2 is inert (an eating step nets 0). Separately, in the geometric E1 model "bites per item" and "trip to food" enter as one quantity (expected trip cost per bite ≈ trip / bites): 6 bites at trip 4 ≈ 12 bites at trip 8. | Add gross 8 and 10 above today so the baseline is interior; present bites-per-item and trip-to-food as one effective axis in the simulator (they differ only in the real environment). | experiment-designer |
| M5 | 🟡 | § Validation, third bullet | The E1/E2-off reproduction of `sweep_food4` guards the shared code path only; it cannot detect an E1 or E2 implementation error. | Add: E2 with the size histogram collapsed to its mean must reproduce E2-off exactly (tests the outcome averaging); E1 rollouts' mean bites per food visit ≈ 12; both agents' per-activity hit histograms agree within a stated tolerance. | experiment-designer |
| M6 | 🟡 | § What is swept, "hit probability ×0.5 / ×2" | No config knob maps to this axis; predator count (0–2), ambusher count (2–12) and attack success (0.5) map non-linearly and are unmeasured. A balanced region found at ×0.5 cannot be handed to the designer. | Pre-state the knob(s) the axis stands for and how the mapping will be measured (e.g. hit rate under a scripted non-avoiding policy vs count), or label the axis diagnostic-only. | experiment-designer |
| M7 | 🟡 | criterion 5 (B-hide) | On the warm-bush map a well-fed, uninjured agent's best place is the warm bush regardless of injury, so cover at low injury ≈ 100 % and the ratio ≈ 1: the criterion fails there by construction and the pooled result is set by the map mix. | Same as M1: per-map, or define hiding as "in a *cold* bush" when a warm bush exists. State the injury and food bands (≥ 60 / ≤ 20; 80–160; < 60) as arbitrary and report step counts per cell. | experiment-designer |
| M8 | 🟡 | § Deliverables / Files | New or changed modules under `scripts/analysis/studies/internal_state_interactions/` need rows in `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` in the same commit (maintenance contract). | Add the rows with the code. | developer |
| L1 | 🟢 | criterion 1 | Whether travel and "elsewhere" steps count toward the 70 % cap is unstated. | Say so. | experiment-designer |

## Open assumptions (unverified)

- ❓ O1 — Which agent's hazard numbers the planner uses (both are measured and reported; `World` defaults are the first run's rounded values). Say which, or average.
- ❓ O2 — Deliverable 2's trained-agent metrics: B-hide binned on *true* or *felt* injury. The registry records a felt-pain reconstruction leak and a contemporaneous-binning hazard in `hiding_drivers.py`; the metric plan must pick one and say why.
- ❓ O3 — Hazard is place-independent in the planner (same at food, ring, open). The by-activity numbers above (eating hit twice as often as moving) suggest food cells carry their own exposure (rocks, ambushers, food relocating without an overlap check). This is the unmodeled item most likely to move the eat-vs-hide balance; measuring it is the same query as C2(b).
- ❓ O4 — Wave-2 agents started at 0 °C and were not trained under any swept setting; hit odds *conditional on being outside* are plausibly robust, the time-outside distribution is not. Stated in the plan; still unverified.

## Passes with nothing to report

Data-loss hazards: none (analysis outputs only). Version numbers: none invented ("Revision 2",
"Wave 2" are existing project vocabulary). Prior art: the registry's `res_type` fix is already in
`measure_world.py`; no re-fix. Doc framing: the Revision-2 entry point is plain-language. Fallback
defaults: not applicable (simulator constants, not config reads).

## Cost of being wrong

The sweep itself is minutes. The cost is downstream: the balanced region and the criteria are the
yardstick for the ordinary-agent training that follows and for a metric-implementation plan. An
unsatisfiable criterion (C1) or a hazard model without lethal hits (C2) would send that training to
the wrong settings — days of GPU on several nodes — and put the wrong measure into code.

## What flips the verdict

Criterion 2 dropped or replaced by a behavioural / relative measure shown to be satisfiable on at
least one world; E2 respecified with a lethal-size bin and per-activity hit odds from both agents,
with the mean-field consistency assertion — both written into the plan before the sweep runs. With
those, SOUND WITH CONCERNS (M1–M8 can be settled while the sweep runs, before the page is read).

Reviewed by: plan-reviewer
