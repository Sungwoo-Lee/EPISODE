# Level-05 balance settings inventory (2026-09-27)

**What this is.** Every environment setting that can shift the balance between the agent's three
internal needs — food energy, injury, body temperature — with its value in today's level 05, what it
does in the code, and whether the planning simulator of the internal-state interaction study models it.
It exists because the study's first version looked at a handful of rules one at a time; the balance
question needs the whole environment in view. Values come from `load_env_config` on
`configs/environment/experiment/basic/05-campfire_thermal_10x10.yaml`, checked against
`src/environment/core.py`; field temperatures from 30 real resets (they match
`results/analysis/internal_state_interactions/world_measurements.json`). Compiled by an Explore agent
for the parent session; used by [[STUDY_PLAN]] Revision 2.

**Caveat.** The Wave-2 level-05 training runs predate B1 (random starting body temperature): their saved
configs start every episode at 0.0 °C. Today's level 05 starts between −10 and +5.

Legend: **M** = modeled, **P** = partly, **N** = not modeled, in `bodysim.py` / `planner.py`.

## A. Body dynamics
| Key | L05 value | Effect on the balance | Sim |
|---|---|---|---|
| body.with_nutrition / with_satiation / with_injury | true / true / true | All three body axes live | M |
| body.metabolic_cost | 1.0 per step | Constant food drain, same when moving, resting or eating; moving costs no extra food | M |
| body.food_nutrition_gain | 6 | Energy per bite (net +5 with the eating cost) | M (as net 5) |
| body.eating_nutrition_cost | 1.0 | Subtracted per bite; an eating step nets +4 after the per-step drain | M |
| body.eating_reward_penalty | 0.0 | Inactive | N (inactive) |
| body.max_nutrition / max_satiation | 200 / 200 | Two-sided axis; dying at 200 makes eating risky near the top | M |
| body.satiation_setpoint | 100 | Middle of the axis; hunger drive is \|S−100\| | M |
| body.nutrition_to_satiation_scaling_factor | 1.0 | Satiation = nutrition | M (assumed) |
| body.overeating_death | true | Dies at N ≥ 200; eating at N ≥ 196 kills | M |
| body.random_start_nutrition, start range | true, [0, 200] | Some starts too hungry to reach food | M |
| body.random_start_injury, start range | true, [0, 100] | Some starts one hit from death | M |
| body.max_injury | 100 | Injury death; injury drive axis in raw units | M |
| environment.eat_action_enabled / rest_action_enabled | true / true | Eating and resting are separate actions; resting is the only way to heal | M |
| thermal.k_metabolic | 0.0 | No body or movement heat | M |
| thermal.metabolic_coupling / rate (A1) | false / 1.0 | Off; if on, defending temperature costs food | M |

## B. Food supply
| Key | L05 value | Effect | Sim |
|---|---|---|---|
| resources.food count | 1–4 | Scarcity and distance to food | P (median trip 4 only) |
| resources.food spawn_area | whole grid | Food may sit next to a fire | P |
| resources.food max_consumption | 12 bites | An item moves after 12 bites (≤ +48 net), forcing a new search | **N** |
| resources.food regeneration_delay | 0 | Reappears next step at a random cell, with no overlap or fire check | **N** |
| thermal.food_min_fire_distance | 0 | Food may sit on a warm ring (eat and warm at once) | **N** |
| food smell / sensor radius | clean, radius 20 | Food is easy to find | N |

## C. Injury, predators and hazards
| Key | L05 value | Effect | Sim |
|---|---|---|---|
| entities.pred count | 0–2 | A third of episodes have no hunter | P (averaged hazard) |
| entities.pred damage | U[15, 120] per contact step | ~19 % of hits kill from zero injury; risk rises steeply with injury | **P** (mean-field 0.70 / 0.12 per step) |
| entities.pred attack_delay | 1–3 | Freezes the predator after contact; **not** a damage cooldown | P |
| entities.pred attack_range / success | {2,3} / 0.5 | Jump attacks on an unhidden agent; open ground is risky | P |
| entities.pred detection / stamina | 1–7 / 30–150 | How far and how long it chases | P |
| entities.rabbit | 0–2, damage 0 | Harmless distractor | N |
| resources.hiding_predator (ambushers) | 2–12, U[15, 45] per step stood on, never used up | Hidden traps | P (averaged hazard) |
| obstacles.rock | 6–12, U[1, 5] per step stood on | Rocks hurt and block healing | P (averaged hazard) |
| body.injury_smoothing_duration | 3 | A hit lands over 3 steps; no healing while it lands | **N** |
| body.recovery_base_rate | 0.2 per rest step | Healing in the open is nearly useless | M |
| body.recovery_in_bush_multiplier | 25 | 5 per rest step in a bush; the main pull to cover | M |
| Rest requirement | rest action and no damage this step | Healing needs deliberate resting | P |
| B2–B5 (healing and warmth, healing costs food, injury chills, healing and hunger) | off | New body rules | M |

## D. Thermal
| Key | L05 value | Effect | Sim |
|---|---|---|---|
| campfire count | 1–3 | Number of warm spots | P |
| campfire temperature | ≈77 on the fire cell, ≈8.8 on the 4 adjacent cells, ≈−16 two cells away diagonally | The fire cell kills in 2–3 steps; the diagonal settles the body at −10.7 | P (ring and cold only) |
| thermal.default_temp | −31 to −29 | Open ground settles the body at −20, lethal | M |
| thermal.k_exchange / k_loss | 0.04 / 0.02 | Body settles at ⅔ of the cell temperature | M |
| thermal.warming / cooling scale | 2.0 / 0.25 | Warming fast (~10 steps from −14 to 0); cooling slow (~46–106 steps to freeze) | M |
| thermal.min/max_temperature, setpoint | −15 / +15, 0 | Death bounds; drive scale | M |
| thermal.min_fire_separation | 4 | No merged hot patches | P |
| thermal.bush_min_fire_distance | 0 | A bush can sit on a warm ring (41 % of episodes) | M (two maps) |
| random start body temp (B1) | −10 to +5 | Some starts need warmth soon | M |
| No cell settles the body at 0 | — | Staying near 0 means shuttling between warm and cold | P |
| Agent can step onto a fire | yes | Blunder risk | N |

## E. Bushes
| Key | L05 value | Effect | Sim |
|---|---|---|---|
| bush count | 4–10 | Trip to cover (median 2) | P (trip, swept in A5) |
| hides_agent / blocks_animals | true / true | No jumps, no contact damage, ×25 healing | P (hazard 0 in a bush) |

## F. Reward and drive
| Key | L05 value | Effect | Sim |
|---|---|---|---|
| use_homeostatic_reward | true | Reward = drive decrease | M |
| drive | ‖(S−100, I, T·100/15)‖ | Euclidean: fixing the largest need pays most | M |
| temperature axis scale | ×6.67 per °C | Temperature weighs heavily | M |
| death_penalty | 100 | Cost of any death; timeout not penalised | M |
| agent.gamma | 0.95 | ~20-step horizon | M |
| return mode / entropy | GAE_NORM / 0.01 | Learning only | N |

## G. Episode
| Key | L05 value | Effect | Sim |
|---|---|---|---|
| max_steps | 500 | Truncation | P |
| random_start_pos | anywhere, no exclusions | Can spawn on a fire, rock or ambusher | **N** |

## H. Perception
| Key | L05 value | Effect | Sim |
|---|---|---|---|
| satiation observed | exact | Hunger fully visible | consistent |
| injury_observable | false | True injury hidden | **N** |
| felt injury (alpha kernel, τ 3, length 12, buffer starts at 0) | on | Injury felt late and smoothed; a starting injury is not felt at step 0 | **N** |
| contact pain | 0.9 on predator, ambusher, rock | Instant pain signal | N |
| body_temp_observable | exact | Temperature fully visible | consistent |
| vision | fire, rock, bush, animals look the same | Fire recognised only by feeling heat | N |
| smell | food, bush clean; predator vs rabbit noisy | Threat ambiguity | N |

## Ten unmodeled settings most likely to shift the balance
1. Predator hit size U[15, 120] — lethal single hits, risk rising steeply with injury.
2. Food running out after 12 bites and reappearing elsewhere; only 1–4 items.
3. Healing blocked while a hit lands (3 steps).
4. Delayed felt injury; the agent does not know its injury exactly.
5. Predators that chase and jump in response to the agent (range, delay, detection, stamina).
6. Ambush predators (2–12, never used up, not smellable).
7. Rock damage (blocks healing).
8. Fire layout beyond two temperatures (lethal fire cell, cooler diagonal, food near fire).
9. Start anywhere; 500-step episode limit.
10. What the agent can see and smell.

## Surprises
- `attack_delay` is not a damage cooldown: a predator on the agent's cell damages every step.
- No cell lets body temperature settle at 0.
- The fire cell kills by heat in 2–3 steps, not on contact.
- Food at `regeneration_delay 0` relocates rather than regrows, with no overlap or fire check.
- `food_min_fire_distance` counts unlit fire slots; `bush_min_fire_distance` counts burning fires only.
- The ambusher's `regeneration_delay 20` does nothing (never used up).
- Moving costs no food; only exposure.
- A random starting injury is not felt at step 0 (felt-injury buffer starts at 0).
