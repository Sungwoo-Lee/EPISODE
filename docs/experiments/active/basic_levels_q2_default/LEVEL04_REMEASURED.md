# Level 04, re-measured — draft verdict for review

## Headline (plain language)

The level-04 analysis published on 2026-09-22 claimed the ordinary agent is "parked" in the bush
while the neuromodulated agent hides only when threatened. Two defects voided it: it read one
checkpoint (the endpoint), and the probe bush let predators walk in. Re-measured with both fixed, the
two agents **discriminate threats the same way**, the ordinary agent **hides more in absolute terms in
the artificial probe scene only**, and making cover heal (Wave 2) **roughly triples calm hiding in the
training world for both agents alike**.

## Data

- Probe sweep, blocking bush, 50 checkpoints × 12 conditions × 30 episodes per agent:
  `results/eval/avoidance/metrics_history_rppo_basicq2_wave2_blocking_bush/`.
- Wave 1 probe sweep (`metrics_history_rppo_basicq2_wave1/`) was run on the PERMEABLE bush; only its
  `avoid_none_*` (no animal) conditions are used, where permeability cannot matter.
- Training-world trajectory stores, 1M episodes each, FINAL checkpoint only:
  `results/analysis/basicq2_w1/context{,_w2}/lvl04_*.json`, causal (`randomised_early`) panel.
- Estimator: mean over the last 20 checkpoints with a 95% t-interval on the lag-1-corrected effective
  sample size (`scripts/analysis/studies/basicq2_waves/window_profile.py`). One training seed per arm.

## Claims

**C1 — threat discrimination is the same in both agents.** `bush_hiding` %, last-20 mean [95% CI]:

| condition | ordinary | neuromodulated |
|---|---|---|
| no animal | 29.6 [15.9, 43.2] | 11.5 [6.1, 16.9] |
| rabbit wandering | 37.9 [20.7, 55.2] | 10.0 [6.1, 14.0] |
| rabbit wandering + predator smell | 41.1 [26.4, 55.8] | 11.5 [6.9, 16.1] |
| rabbit chasing | 64.1 [53.3, 74.9] | 35.2 [27.9, 42.5] |
| predator | 71.3 [61.8, 80.8] | 52.6 [45.9, 59.2] |

Predator-minus-empty contrast: 41.7 vs 41.1. Both rank the threats the same way.

**C2 — the ordinary agent's higher absolute hiding is specific to the probe scene.** In the probe it
exceeds the neuromodulated agent by 18–28 points in every condition. In the training world the two
are indistinguishable (causal panel, calm hiding by starting-injury quarter: 52.0/51.2, 61.6/60.4,
72.4/71.9; under threat 74.7/75.9, 77.0/78.5, 81.7/82.9). Proposed reading: the probe (fixed start,
one bush 3 cells away, full nutrition, no food) gives the agent nothing to do, and what an agent does
with nothing to do is what differs.

**C3 — making cover heal raises calm hiding far more than threatened hiding, in both agents.**
Training world, W1 → W2, lowest to highest injury quarter: calm 20.2–28.4 → 52.0–72.4 (ordinary),
22.8–30.8 → 51.2–71.9 (neuromodulated); threatened 60.6–66.8 → 74.7–81.7 and 65.2–69.4 → 75.9–82.9.

**C4 — in the empty probe only, Wave 2 raised the ordinary agent's idle hiding (9.9 → 29.6) but not
the neuromodulated agent's (12.5 → 11.5).** Single seed; contradicted in kind by C2's training-world
equality.

## Known weaknesses (for the reviewer)

1. One seed per arm. No seed-scale estimate exists for the PROBE `bush_hiding` measure — the five-seed
   floor on the published page is for a different measure in a different world.
2. C2 compares a windowed probe measure against a FINAL-checkpoint trajectory measure — the very
   endpoint reading this study has shown can be wrong. At the final checkpoint the probe says
   86.1 vs 5.9 (empty), while the training world says ~equal.
3. The probe CIs are across-checkpoint, i.e. policy drift within one run, not between runs.
4. The "nothing to do" explanation in C2 is a hypothesis, not tested.
