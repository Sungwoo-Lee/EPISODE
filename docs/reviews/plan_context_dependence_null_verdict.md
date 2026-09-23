---
title: "Review of the context-dependence null verdict (modulator × vision)"
topic: reviews
status: active
created: 2026-09-23
last_updated: 2026-09-23
---

# Review: "a neuromodulator does not increase state-dependence, and vision does not rescue it"

Reviewed by: plan-reviewer · 2026-09-23 · second-round review (first round gated at 12:52, see diary)

## Verdict

**NOT SUPPORTED BY THE EVIDENCE SHOWN — for the claim as worded.** This is a statement about the
argument, not a claim that the opposite is true.

In plain language: the analysis compares six trained agents — with and without a neuromodulator,
in a world where the agent cannot see and in a world where it can — and concludes that the
modulator never makes hiding depend more on how injured the agent is, and that giving the agent
eyes does not change that. Two of the three sentences in that conclusion are not what the data
show:

1. **"Injury shifts baseline hiding by the same ~21 points in all six cells"** is read from the
   estimator the author has already declared confounded (the *observed* panel). Under the
   estimator the author trusts (episodes whose starting injury was assigned at random), the same
   quantity is **2.8–4.5 points in the blind world and 8.1–8.2 points in the sighted world** — it
   roughly doubles with vision. The 21-point figure is flat because it is measuring something
   common to every run (a predator encounter causes both the injury and the hiding), not because
   nothing changes.
2. **"The blindness excuse does not survive giving it vision"** rests on one run pair, at one
   level, with two variables changed at once (vision, and the bush becoming predator-proof), where
   the "vision" added is a 13-cell presence map in which predator, rabbit, food, bush and rock all
   look identical. Three further sighted levels with usable data sit in the same output folder and
   were not used, although the plan pre-registered its reading "on most levels".
3. The narrow claim — **no modulator effect was detected at one seed per cell, in either world** —
   is consistent with the data, including the bush-entry measure the tool itself names as its
   headline, which the verdict does not report.

Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run ·
🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

## Findings

| Sev | Location | Issue | Suggested fix | Owner |
|---|---|---|---|---|
| 🔴 | verdict point 1; `observed.metrics.state_span` in every JSON | F1 is taken from the *observed* panel while F2 is taken from the *causal* panel. Under `randomised_early` F1 is 4.52/2.78 (blind GAE ctrl/mod), 3.01/4.16 (blind MC), 8.20/8.08 (sighted lvl04) — vision doubles it. The observed ~21 pp is dominated by reverse causation: an agent at injury ≥50 mid-episode was just bitten during a predator encounter, and the encounter is what put it in the bush. Same mechanic in all six runs, hence flat. | Report F1 from the causal panel, or drop the "flat" sentence. State that observed F1 is a signature of the encounter, not of the policy. | experiment-analyzer |
| 🔴 | verdict headline, second clause | "Does not survive" is not carried by one pair, one level, two changed variables, identity-free vision. The sighted agent's only object-identifying channel is olfaction, exactly as in the blind arm; the visual channel is a binary occupancy map (`visual_properties: [1.0]` for every entity, `visual_vector_size: 1`, range 2). The refuge bush also raises the value of hiding, which is the very thing a state-dependent policy would modulate — a masking (cancelling) effect cannot be excluded at n=1. | Reword to: "the null is not rescued by adding an identity-free presence sense in a world where the bush is also a physical refuge; single seed; two-variable step." Design a blind arm with `blocks_animals: true` (or a sighted arm without it) to make the step single-variable. | experiment-analyzer (wording); experiment-designer (arm) |
| 🟡 | JSON `entry.b0.*` — unreported | The tool's docstring names B0 (bush-entry out of the open on a movement decision) as *the headline behavioural measure* and the occupancy measures as "weakest evidence". Δ_B0 (first 25 steps, predator near) is **−1.75±0.18 / −1.77±0.18** (blind GAE ctrl/mod), **−2.02 / −1.78** (blind MC), **−2.62 / −2.34** (lvl04): significantly *negative* in every cell — wounded agents enter bushes *less* under threat, opposite to the pre-registered direction. The modulator does not move it consistently (B3 range 2.06/1.57, 2.57/1.93, 2.29/2.99). This both strengthens the modulator null and is a finding in its own right that the verdict leaves out. | Add a B0/B3 row set; state the negative Δ_B0. | experiment-analyzer |
| 🟡 | `results/analysis/basicq2_w1/context/lvl03,05,06_*.json` | Pre-registration (FIGURE_PLAN "What would count as a result") reads F2 "on most levels". Only lvl04 is used. Levels 03/05/06 have populated causal panels (lvl01/02 do not randomise starting injury and are legitimately unusable). Modulated−control causal F2: lvl03 −0.39, lvl04 −0.93, lvl05 −0.40, lvl06 −1.16 — four sighted levels all negative, which the one-level table cannot show. | Use all usable levels or state why lvl04 alone. | experiment-analyzer |
| 🟡 | every store manifest: `ckpt_step ≈ 10,000,0xx` | All six populations are the *final* checkpoint. Today's diary (19:06) records that reading a behaviour measure off the final checkpoint manufactured a 60 pp effect that is 0.8 pp over the last ten checkpoints, with checkpoint-to-checkpoint policy variation 2–19× sampling error. One million episodes remove sampling error, not checkpoint-to-checkpoint policy drift. | Either state the endpoint-only limitation explicitly or re-collect a small store at 2–3 late checkpoints for one pair to bound the drift. | experiment-analyzer |
| 🟡 | verdict points 2–3; question 4 | Within-run CIs (±0.06–0.07 pp/bin on causal F2; ±0.05 on F1) make *every* difference "significant", including the ones that flip sign across pairs. The relevant noise is run-to-run. The only in-data estimate: the two blind controls (same world, same seed, differ only in return estimator) differ by 0.63 pp/bin causal and 1.20 observed — 9× and 30× the within-run CI. Modulator differences (0.07–0.95 blind, 0.4–1.2 sighted) are within ~1.5× of that. | Do not quote `b0_ci95`/binomial CIs for between-arm claims. Compute F1/F2/B0 on the five unmodulated reference stores (`results/trajectories/20260904-17*_rppo_cmp10m_{mc,gaenorm}_s42..s46`, five seeds, blind world) to get a seed SD, and express modulator differences in those units. | experiment-analyzer |
| 🟡 | `context_dependence.py` `sweep()` early block | The causal window (t = 2..25) keeps 0.88/0.87/0.80 of expected rows by starting-injury bin in the blind world and 0.90/0.89/0.86 in the sighted one: the high-injury bin loses 8–9 pp more rows than the low bin (blind) and 4–5 pp more (sighted). Survivors in the ≥50 bin are selected toward hiders, and the selection differs by world. Rest rate in that window for ≥50 starters is 56–62%, so "hiding" is largely "where it rested". | Note the selection in the write-up; consider a row-level survival weight or a t≤10 sensitivity check. Registry row candidate. | experiment-analyzer; bug-curator to decide on a row |
| 🟢 | FIGURE_PLAN F1 axis text vs computed quantity | The plan defines F1's axis as "difference in bush-entry rate"; the JSON field is occupancy `state_span`. Same mismatch the 12:52 gate flagged. | Align the label with the field actually plotted. | experiment-analyzer |
| 🟢 | `state: injury` in all JSONs | The tool's default and stated preference is `felt_pain` (the lagged signal the agent actually receives). Using raw injury is defensible for the causal panel (starting value) but should be stated. | One sentence. | experiment-analyzer |

## Assumptions the verdict rests on

| Assumption | Status |
|---|---|
| The blind→sighted step changes only vision and `blocks_animals` | **Verified** from saved run configs: the only other differing keys are inert (`thermal.enabled: false` and `perceptual_noise.enabled: false` in both; `recovery_in_bush_multiplier: 1.0` = no effect). Entities/resources differ only in visual vectors. |
| Both modulated arms are the same mechanism | **Verified**: FiLM, `input_sensors: all`, all four sites, identical init, in both worlds. |
| Populations are paired and equal | **Verified**: 1,000,000 episodes, `seed_base 1000000`, `deterministic_argmax` in all six manifests. |
| The modulator was actually active (its gain varies with injury) in the modulated runs | ❓ **Unverified.** If the modulator output is near-constant, the behavioural null is trivial and says nothing about the hypothesis. `repr_analysis` / `nmn_health` exist for this and were not run. |
| Final-checkpoint behaviour represents the trained policy | ❓ Unverified; contradicted in spirit by today's checkpoint-drift finding. |
| The within-run CI is the right noise scale for arm comparisons | **False** — see the 🟡 row; run-to-run differences are an order of magnitude larger. |
| "Vision" in Wave 1 gives the modulator something new to gate | ❓ Weak: identity-free presence map; identity still comes from olfaction, as in the blind arm. |
| Hiding under threat is not at a ceiling in the refuge world | ❓ Unverified (hide-under-threat 60–69% in the causal window; geometric ceiling unknown). |

## Alternative explanations not ruled out

1. A real modulator effect smaller than run-to-run spread (underpowered null).
2. An inactive modulator (no evidence shown that FiLM gain depends on injury).
3. In the sighted arm, a vision-enabled effect masked by the refuge bush saturating the hiding response.

## Cost of being wrong

No rerun is at stake; the cost is a sentence in a paper — "vision does not rescue the modulator" —
that a reviewer dismantles in one paragraph (n = 1, two variables, identity-free vision, endpoint
only, headline measure omitted), and possibly a live direction shelved on an underpowered null.
The omitted bush-entry result (wounded agents enter bushes *less* under threat, in every cell) is
a real finding currently being left on the table.

## What would flip this to SUPPORTED WITH CAVEATS

1. Read F1 from the causal panel and drop "flat across all six".
2. Report B0/B3 alongside F1/F2 and state the negative Δ_B0.
3. Use lvl03–06 or justify lvl04 alone.
4. Replace within-run CIs with a seed-spread estimate from the five reference stores.
5. Reword the vision clause to "not rescued by … at n = 1, two-variable step, presence-only vision".
6. Show the modulator's gain varies with injury in at least one modulated run.
7. State the endpoint-only limitation.

## Pointers

- Analysis outputs: `results/analysis/basicq2_w1/{context,context_prev,context_prevmc_mc}/*.json`
- Tool: `scripts/analysis/context_dependence.py` (docstring lines 1–60 name B0 as headline)
- Pre-registration: `docs/experiments/active/basic_levels_q2_default/FIGURE_PLAN.md` §"What would count as a result"
- Saved configs: `results/JAX_RecurrentPPO/<run>/models/config.yaml` for the six runs
- First-round gate: `docs/diary/2026-09-23.md` 12:52 row; checkpoint-drift finding: 19:06 row
