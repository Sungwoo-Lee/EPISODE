---
title: "Thermal Probe Battery — measuring bush hiding in the body-temperature agents"
topic: behavior_measures
status: active
created: 2026-09-23
last_updated: 2026-09-23
wandb_tag: bq2cover
aliases: [thermal-probe-battery, thermal-bush-hiding]
---

# Thermal Probe Battery — measuring bush hiding in the body-temperature agents

> **Status**: COLLECTING (configs built and verified; no evaluation launched)
> **Date**: 2026-09-23
> **Author**: `experiment-designer`
> **Related**: [[interoceptive_behavior_measure_study]] (the behaviour-measure toolkit these probes feed), the Wave 2 training runs of the `basic_levels_q2_cover` study launched 2026-09-22

---

## 1. Research Question

**Plain language, read this first.** Four agents finished training on 2026-09-22 in worlds where the
body has a temperature and the world is cold. Two of them were trained in the world where a cold body
is the only extra difficulty; two in the same world plus *sensory noise that gets worse when the agent
is hurt*. Within each pair, one agent is a plain baseline and one carries the neuromodulation
mechanism this project is testing. We want to ask all four the same behavioural question we already
ask of the agents one rung lower on the curriculum: **when a predator comes, does the agent go and
hide in the bush — and does it come back out when the danger passes?**

Right now we cannot ask that question at all. The 12 fixed "probe" scenes we use for it were built for
agents without a body temperature. Those scenes hand the agent a 52-number view of the world; these
four agents were trained to read a 58-number view, so the scenes physically do not fit them. The
obvious fix — switch the temperature system on in the probe scenes — kills the agent: the probe world
has no fire in it, the world's baseline is roughly −30 °C, the body settles near −20 °C, and anything
below −15 °C is death. The agent freezes after about 86 to 99 steps, and the probe is 100 steps long.
So the probe would be measuring *how fast the agent dies of cold*, not whether it hides.

This document specifies a replacement probe battery that fits those agents and lets them live long
enough to be measured, and it states in advance what each version of the battery should show.

**There is an unavoidable catch, and it is stated up front rather than buried.** In this environment
the temperature the agent feels is mathematically locked to the temperature it settles at: at rest the
agent's temperature sense reads exactly one third of the world's baseline temperature, and its body
sits at two thirds of it. In the world these agents trained in, that means the "I am away from the
fire" reading is about −10, and a body at about −20, which is lethal. **Reproducing the training
world's temperature sensation and surviving a 100-step probe are mutually exclusive.** Every probe the
agent can survive is therefore *off-distribution* on the temperature channel. This is a property of
the level's physics, not a flaw in the probe design, and it cannot be engineered away. The response is
to build **four different temperature worlds** rather than pick one, and to believe a behavioural
result only when it survives all four.

**The four temperature worlds, in English:**

| Arm | The world | What the agent's temperature sense says |
|---|---|---|
| **neutral** | Comfortable everywhere, baseline 0 °C | Nothing at all — the reading is exactly zero, everywhere, forever. The temperature part of the agent's internal drive vanishes, so this is the closest this battery can get to the world the lower-curriculum agents were measured in. |
| **cool** | Uniformly chilly but survivable everywhere, baseline −7.5 °C | A constant mild cold, the same in every square. The sense is switched on and carrying a real number, but it carries no information about *where* to go. |
| **fire by the bush** | The real cold world, with one campfire placed right next to the hiding bush | A strong, spatially informative gradient. Only 8 of the 100 squares are survivable — and the bush is one of them. The agent can hide **and** stay warm. Hiding is free. |
| **fire away from the bush** | The real cold world, with one campfire on the far side of the arena | Same strong gradient, but now the 8 survivable squares ring the fire and **the bush is lethal**. Hiding costs the agent its life. |

**What the fourth arm is for.** One rung lower on the curriculum we found that the baseline agent
appears to be *parked* in the bush — it sits there more or less permanently — while the
neuromodulated agent appears to hide *conditionally*, going in when threatened and coming out
afterwards. Those two behaviours look almost identical on a "fraction of time spent in the bush"
number when the bush is a free place to sit. The fire-away-from-the-bush world separates them
cleanly: **a parked agent freezes to death; a conditional agent leaves.**

**Formal hypotheses.** Writing `H₀` for "no difference" and `H₁` for "there is one":

> **H₀** (*the two agents hide the same way*): in every arm, the neuromodulated agent's bush-hiding
> time and survival steps are indistinguishable from the baseline agent's.
>
> **H₁a** (*hiding is conditional, not parked*): in the arm where the bush is lethal (fire away from
> the bush), the baseline agent's survival drops sharply relative to the neuromodulated agent,
> because it keeps returning to a square that kills it.
>
> **H₁b** (*the hiding difference is not an artefact of the temperature channel*): whatever
> difference in bush-hiding appears between the two agents has the same sign in all four arms. If it
> flips sign between arms, the difference is being driven by the temperature channel being
> off-distribution, not by hiding behaviour.

## 2. Experimental Design

This is an **evaluation** experiment on already-finished training runs. No new training is proposed.

### 2.1 Independent Variables

| Variable | Values | Rationale |
|---|---|---|
| Thermal arm | `neutral` (ambient 0.0), `cool` (ambient −7.5), `fire_by_bush` (inherited ambient, campfire at config `[5,3]`), `fire_away` (inherited ambient, campfire at config `[2,5]`) | The off-distribution problem in §1 has an unknown effect, so all four ship rather than one being chosen. `fire_away` is the arm that carries the parked-vs-conditional test. |
| Noise battery | `clean` (no perceptual noise), `noise_matched` (level 06's injury-gated noise verbatim) | Level-06 agents trained under injury-gated sensory noise. `clean` is the cross-level-comparable set; `noise_matched` is the in-distribution set for those agents only. |
| Agent | baseline vs neuromodulated, at two curriculum levels | The comparison of interest. |
| Probe scene | the 12 existing core avoidance scenes, unchanged | Predator vs. harmless rabbit vs. nothing, crossed with starting injury 0 vs 70. |

Full grid: **4 arms × 2 batteries × 12 scenes = 96 probe configs.**

### 2.2 Controlled Variables

Everything that is not a variable above is **read from the existing core probe files at generation
time**, not restated by hand, so that the 12 scenes here stay byte-identical to the 12 scenes the
lower-curriculum agents are measured on:

- grid 10×10, `max_steps: 100`, agent start at config `[5,5]`, `random_start_pos: false`
- the hiding bush at config `[5,2]` (`hides_agent: true`), the animal spawning at config `[5,9]`
- each scene's animal class, behaviour, olfactory signature, damage and detection settings
- each scene's `body:` block, including its starting injury level (0 or 70)
- `visualization.local_view_size: 10` — the deliberate full-arena video fix of 2026-09-23, without
  which a recorded episode shows a 5×5 window and the chase is unreadable
- every thermal key except `enabled` and `default_temp`: blur width, the exchange/loss/metabolic
  rates, the setpoint, the survivable band, the sensor's grid range and its relative-reading mode all
  come through `environment/default`, so the battery tracks the live schema rather than a snapshot

**Deliberate deviations from the inherited canonical values**, both local to this battery:

```yaml
thermal:
  enabled: true              # canonical false; every thermal world turns it on locally
  default_temp: [0.0, 0.0]   # `neutral` arm only; canonical is [-31, -29]
  # default_temp: [-7.5, -7.5]   # `cool` arm only
  # the two fire arms do NOT override default_temp — they inherit [-31, -29]
```

### 2.3 Confounds & Limitations

| Confound | Affected arms | Severity | Mitigation |
|---|---|---|---|
| **Off-distribution temperature channel.** No survivable probe can reproduce the training world's resting temperature reading (§1). | all four | **High, and irreducible** | Ship all four arms; believe a result only when its sign is stable across them (`H₁b`). |
| **Reward scale is not comparable with the lower-curriculum probes.** In the `cool` arm the temperature axis contributes a constant −33.3 in satiation units — a third of the full hunger scale. In the `neutral` arm it contributes exactly 0. | `cool`, `neutral` | Medium | Report **survival steps and bush-hiding time**, never cumulative reward (project rule). Do not compare reward numbers across arms or against level 04. |
| **The fire is a second attractor.** In both fire arms only 8 of 100 squares are survivable, so the agent has a thermoregulatory reason to move that has nothing to do with the predator. | `fire_by_bush`, `fire_away` | Medium | `fire_by_bush` places the fire so the bush is inside the warm ring, making hiding and warmth compatible; the difference between the two fire arms isolates the conflict. |
| **The campfire is visually indistinguishable from the bush.** Both report only "a cell is occupied" on the single visual channel — deliberate, so that only the temperature sense can tell them apart. | both fire arms | Low (by design) | Stated here so a surprising approach-to-fire result is not misread as a vision bug. |
| **A single evaluation seed per checkpoint, 30 episodes.** | all | Medium | Matches the existing core battery's protocol, so the numbers are comparable; the temporal curve across 50 checkpoints is the evidence, not any single point. |
| **Wave 1 is excluded.** Wave 1 trained with a maximum satiation of 100 and the satiation observation is the ratio of current satiation to that maximum, so a Wave-1 agent in today's probe reads 0.5 where it trained to read 1.0 and would act half-starved. | — | — | Out of scope; do not add Wave 1 runs to these specs. |

## 3. Launch Manifest

**No training runs.** This experiment evaluates four already-finished runs, so the manifest below
lists evaluation jobs rather than training launches. The `training-runner` fills Node / Launched at /
Log path at launch; **node selection is deliberately left empty in every spec** (see §3.2).

### 3.1 Subject runs

| Label | Level | Agent | Run directory | Checkpoints | Last step |
|---|---|---|---|---|---|
| `lvl05_control` | 05 (thermal) | baseline | `results/JAX_RecurrentPPO/20260922-182534_rppo_bq2cover_lvl05_t1none_s42` | 50 | 10,000,012 |
| `lvl05_modulated` | 05 (thermal) | neuromodulated | `results/JAX_RecurrentPPO/20260922-182538_rppo_bq2cover_lvl05_t16quad_s42` | 50 | 10,000,011 |
| `lvl06_control` | 06 (thermal + injury-gated noise) | baseline | `results/JAX_RecurrentPPO/20260922-182543_rppo_bq2cover_lvl06_t1none_s42` | 50 | 10,000,068 |
| `lvl06_modulated` | 06 (thermal + injury-gated noise) | neuromodulated | `results/JAX_RecurrentPPO/20260922-182547_rppo_bq2cover_lvl06_t16quad_s42` | 50 | 10,000,021 |

### 3.2 Evaluation manifest

| Job | Status | Arm | Battery | Sweep spec | Subject runs | Node | Launched at |
|---|---|---|---|---|---|---|---|
| 1 | planned | neutral | clean | `configs/eval_sweeps/thermal_probes/thermalprobe_neutral_clean_rppo.yaml` | all four | — | — |
| 2 | planned | cool | clean | `configs/eval_sweeps/thermal_probes/thermalprobe_cool_clean_rppo.yaml` | all four | — | — |
| 3 | planned | fire_by_bush | clean | `configs/eval_sweeps/thermal_probes/thermalprobe_fire_by_bush_clean_rppo.yaml` | all four | — | — |
| 4 | planned | fire_away | clean | `configs/eval_sweeps/thermal_probes/thermalprobe_fire_away_clean_rppo.yaml` | all four | — | — |
| 5 | planned | neutral | noise_matched | `configs/eval_sweeps/thermal_probes/thermalprobe_neutral_noise_matched_rppo.yaml` | lvl06 pair | — | — |
| 6 | planned | cool | noise_matched | `configs/eval_sweeps/thermal_probes/thermalprobe_cool_noise_matched_rppo.yaml` | lvl06 pair | — | — |
| 7 | planned | fire_by_bush | noise_matched | `configs/eval_sweeps/thermal_probes/thermalprobe_fire_by_bush_noise_matched_rppo.yaml` | lvl06 pair | — | — |
| 8 | planned | fire_away | noise_matched | `configs/eval_sweeps/thermal_probes/thermalprobe_fire_away_noise_matched_rppo.yaml` | lvl06 pair | — | — |

Eight specs rather than one because the sweep driver takes exactly one probe directory per spec
(`probe:` is a single path). Each spec's `nodes:` list is **empty on purpose**: which lab machines are
free changes by the hour, and a node list frozen at design time either collides with a running job or
wastes a free machine. The driver fails loudly on an empty list — `ValueError: min() arg is an empty
sequence` out of its work-partitioning step — which means "fill in the nodes", not "the spec is
broken".

Work size: jobs 1–4 are 4 runs × 12 scenes × 50 checkpoints = 2,400 checkpoint-evaluations each;
jobs 5–8 are half that. Total 14,400 checkpoint-evaluations at 30 episodes each. The driver is
incremental (it skips checkpoints already present in the output CSV), so a partial run is resumable
and re-running a spec later costs only the new work.

### 3.3 Configs produced

| What | Path | Count |
|---|---|---|
| Generator | `configs/environment/experiment/behavior_probes/thermal/generate_thermal_probes.py` | 1 |
| Probe configs | `configs/environment/experiment/behavior_probes/thermal/<arm>_<battery>/avoid_*.yaml` | 96 |
| Sweep specs | `configs/eval_sweeps/thermal_probes/thermalprobe_<arm>_<battery>_rppo.yaml` | 8 |

The eight probe directories are `neutral_clean`, `neutral_noise_matched`, `cool_clean`,
`cool_noise_matched`, `fire_by_bush_clean`, `fire_by_bush_noise_matched`, `fire_away_clean`,
`fire_away_noise_matched`, each holding the same 12 filenames as the core battery
(`avoid_none_inj00.yaml` … `avoid_rabbitwander_predsmell_inj70.yaml`). Keeping the filenames identical
is what lets the plotting step's condition parser and its row ordering work unchanged.

## 4. Methods — the physics, measured

Every number in this section was produced by loading the generated file through the project's own
config loader and resetting the real parallel environment; none of it is re-derived from config
comments, several of which are stale (level 05's header still quotes an ambient of `[-28,-22]` where
the live value is `[-31,-29]`).

**The body's resting temperature.** The environment updates body temperature by

$$T \leftarrow T + k_{ex}\,(T_{field} - T) + k_{met} - k_{loss}\,(T - T_{set})$$

whose fixed point is

$$T^{*} = \frac{k_{ex} T_{field} + k_{loss} T_{set} + k_{met}}{k_{ex} + k_{loss}}$$

With the inherited `k_ex = 0.04`, `k_loss = 0.02`, `k_met = 0`, `T_set = 0`, this is exactly
`⅔ × T_field`. The approach to it is monotone from any start, so "the fixed point lies inside the
survivable band" is exactly "the agent survives here indefinitely".

**Why the naive fix kills the agent.** The temperature sense reports `field − body`, which at rest is
`⅓ × T_field`. At the training world's ambient of −31 to −29 the body settles at −20.7 to −19.3
against a floor of −15, and the freeze arrives at step **86 to 99** (86 at ambient −31, 92 at −30, 99
at −29) — inside the 100-step probe. This is the measured basis for the claim in §1 that the
training-world sensation and probe survival are mutually exclusive.

**Per-arm measurements.** Config coordinates are 1-indexed relative to the underlying array, so
config `[2,5]` is array `(1,4)`.

| Arm | Ambient | Observation width | Survivable cells | Body at the bush, config `[5,2]` | Body at the start, config `[5,5]` | Fire core |
|---|---|---|---|---|---|---|
| `neutral` | `[0.0, 0.0]` | 58 | 100/100 | +0.00, survivable | +0.00, survivable | — |
| `cool` | `[-7.5, -7.5]` | 58 | 100/100 | −5.00, survivable | −5.00, survivable | — |
| `fire_by_bush` | inherited `[-31,-29]` | 58 | 8/100 | **+6.07, survivable** | −19.02, lethal | +52.07, lethal |
| `fire_away` | inherited `[-31,-29]` | 58 | 8/100 | **−20.24, LETHAL** | −20.24, lethal | +52.77, lethal |

The 8 survivable cells in `fire_by_bush` are config `(4,2) (4,3) (4,4) (5,2) (5,4) (6,2) (6,3) (6,4)`
— the ring around the campfire at `[5,3]`, which contains the bush at `[5,2]`. In `fire_away` they are
config `(1,4) (1,5) (1,6) (2,4) (2,6) (3,4) (3,5) (3,6)` — the ring around the campfire at `[2,5]`,
which does not.

**The loader's own thermal check.** The config loader refuses to load a thermal world whose radial
profile has lost the task: standing on the fire must be lethal, one cell out must be survivable, three
cells out must be lethal again. That check runs only when a heat source exists, so it fires on the two
fire arms and is skipped on `neutral` and `cool`. Confirmed at load: both fire arms log
`thermal structure check PASSED for 1 heat-source slot(s)`; both no-fire arms log
`thermal structure check SKIPPED … no heat source to check`.

**The campfire.** Level 05's entry verbatim, `temperature_ratio: [11, 11]` — fixed, not a range,
because a range cannot meet the "the first step onto the fire is survivable" target in every episode.
The fire shares its visual channel with rock and bush on purpose: feeling it is the only way to tell
it from a rock, which is the point of having a temperature sense at all.

**The list-replace trap.** The config system's merge **replaces lists wholesale**, so any config that
redeclares `obstacles:` must restate the bush or it silently vanishes. The generator restates it by
construction — the obstacle list it writes is the source probe's own list with the campfire appended —
and the verification pass asserts, for all 96 files, that the bush entry is byte-identical to the
source probe's.

## 5. Analysis Plan (pre-specified)

**Primary measure:** fraction of the 100-step episode spent hidden in the bush, per checkpoint, per
scene, as a curve across the 50 checkpoints of training. **Secondary:** survival steps (the project's
headline performance measure) and spatial spread. **Reward is not analysed** — it is not comparable
across arms (§2.3) and is not this project's dependent variable.

**Temporal evolution is the evidence, not the endpoint.** Each of the 50 checkpoints is a point on a
curve; a difference that exists only at the final checkpoint is reported as such and not treated as an
established behavioural difference.

**The three comparisons, and the order to read them in:**

1. **Within an arm, baseline vs neuromodulated, at the same curriculum level.** The direct test of
   `H₀`.
2. **Across the four arms, same agent pair.** The cross-check for `H₁b`. A hiding difference that
   changes sign between arms is attributed to the temperature channel, not to hiding.
3. **`fire_by_bush` against `fire_away`, same agent.** The parked-vs-conditional test (`H₁a`). The
   quantity of interest is the *drop* in survival steps when the bush becomes lethal: a parked agent
   should lose a large fraction of its survival, a conditional agent much less.

**Effect-size thresholds, fixed in advance.** For the parked-vs-conditional test, a baseline agent
losing at least 30 percentage points more of its survival steps than the neuromodulated agent, when
moving from `fire_by_bush` to `fire_away`, counts as support for `H₁a`; under 10 points counts as a
null. Between 10 and 30 is reported as inconclusive and not resolved by re-reading the same data.

**Sign stability is the acceptance rule.** A bush-hiding difference is reported as a finding only if
its sign is the same in all four arms. If it holds in three arms and flips in one, the flipping arm
is named and the claim is downgraded to arm-specific.

**Level 06 gets both batteries, and they must agree.** The `clean` battery is the cross-level
comparable set, the `noise_matched` battery is the in-distribution one. Where they disagree for a
level-06 agent, the `noise_matched` result is the one that describes the agent, and the disagreement
itself is reported — it is evidence that the behaviour depends on the sensory noise the agent was
trained under.

## 6. Failure-Mode Catalog

Decided in advance, so that an ambiguous outcome is not resolved after the fact.

| Outcome | Reading |
|---|---|
| **An agent dies of cold in the two comfortable arms.** | A defect in the probe or the agent, not a result. Both arms are survivable in all 100 cells; a cold death there means something is wrong. Stop and diagnose. |
| **Every agent dies within a few steps in both fire arms.** | Not a refutation of `H₀`. It means the fire arms are too hostile to measure hiding, and the fire-arm evidence is discarded while the two comfortable arms stand. Only 8 of 100 cells are survivable, and an agent that never trained on this ambient may simply fail to find them. |
| **Bush-hiding is at the floor (near zero) in every arm for every agent.** | A genuine null on this battery, but a weak one: it may mean the agents never learned to hide, or that the off-distribution temperature reading suppresses the behaviour. Report as a null and say which of the two cannot be distinguished. |
| **Bush-hiding saturates at the ceiling for both agents in the comfortable arms.** | Not a null: it is the exact scenario the fire-away arm was built to disambiguate. Read the fire-away arm. |
| **The hiding difference flips sign between arms.** | `H₁b` refuted. The difference is being driven by the temperature channel, not by hiding, and no hiding claim is made from this battery. |
| **The two batteries disagree for a level-06 agent.** | Not a defect. Report both; the noise-matched one describes the agent, the disagreement is itself a finding (§5). |
| **The evaluation of a checkpoint crashes or returns no episodes.** | A run-level failure, not evidence. The driver is incremental; re-run the spec. Do not treat a missing point as a zero. |
| **A result appears in only the final checkpoint.** | Reported as an endpoint observation, not a behavioural difference (§5). |

## 7. Metrics Requested

None. Every measure this design reads — bush-hiding time, survival steps, spatial spread — is already
computed by the existing behaviour-measure toolkit from the recordings the sweep driver produces. No
change to `src/` is needed for this experiment.

## 8. Verification Performed

All 96 generated configs were loaded through the project's config loader and parameter builder, and
the real parallel environment was reset on each, by a verification pass written independently of the
generator. Every one passed:

- observation width is **58** on all 96
- the survivable-cell count matches the arm's contract on all 96 (100, 100, 8, 8)
- the bush's resting temperature matches to two decimal places on all 96 (+0.00, −5.00, +6.07, −20.24)
  and its survivable/lethal verdict matches the arm's contract
- the 8 survivable cells in `fire_by_bush` are exactly the expected set
- the scene, the `body:` block and `visualization.local_view_size: 10` are byte-identical to the
  source core probe on all 96
- the bush obstacle entry survived the obstacle-list replace on all 96
- the resolved perceptual-noise parameters of every `noise_matched` config are identical to those of
  the level-06 training world, and every `clean` config's are identical to the core probe's

## 9. Results

*(blank until the evaluation runs)*

## 10. Conclusions

*(blank until the evaluation runs)*

## 11. Links

- Generator: `configs/environment/experiment/behavior_probes/thermal/generate_thermal_probes.py`
- Probe configs: `configs/environment/experiment/behavior_probes/thermal/<arm>_<battery>/`
- Sweep specs: `configs/eval_sweeps/thermal_probes/`
- Source battery: `configs/environment/experiment/behavior_probes/core/avoidance/`
- Training worlds: `configs/environment/experiment/basic/05-campfire_thermal_10x10.yaml`,
  `configs/environment/experiment/basic/06-sensory_noise_10x10.yaml`
- Sweep driver: `scripts/eval/dwell_sweep/run_sweep.py`
- The exclusion this battery removes: `configs/eval_sweeps/basicq2_wave2_rppo.yaml`
