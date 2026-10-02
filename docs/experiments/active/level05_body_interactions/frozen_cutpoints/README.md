# Frozen cut-points (level-05 body-interactions factorial)

Copies of the two cut-point files frozen on 2026-09-28 from the complete final-checkpoint store of the
plain level-05 ordinary run (`w0000_ordinary`, 1,000,000 episodes, 254,074,602 decision rows), before
any other run's complete store was read. The working copies the scripts read live in the gitignored
`results/analysis/level05_body_interactions/`; these tracked copies are the record.

- `frozen_felt_injury.json` - felt injury (the "Interoceptive Nociception" observation slot).
  Low = felt injury <= 0.0, i.e. exactly 0 (51.8 % of steps; the pre-registered bottom fifth cannot be
  formed because more than a fifth of steps sit at 0 - see the design doc's pre-analysis decision).
  High = felt injury >= 0.0878 (top fifth, 20.0 % of steps).
- `frozen_temperature_bins.json` - body temperature bins for the behavioural combination gain:
  10 equal bins between the 0.5th and 99.5th percentiles (-11.94 to +4.88 degrees), outer bins open.

Produced by `scripts/analysis/studies/level05_body_interactions/{state_contrasts,behavioural_combination_gain}.py --freeze`.
