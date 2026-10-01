# Config Audit — thirst task, nine worlds before the 18-run launch

**Scope:** pre-flight sweep audit (nine environment configs × two agents = 18 runs)
**Files audited:** level 06 (`configs/environment/experiment/basic/06-pond_thirst_10x10.yaml`), the eight
files in `configs/environment/experiment/thirst/`, the 2026-10-01 entry of
`docs/environment/CONFIG_CRITICAL_SETTINGS.md`; design doc [[THIRST_TASK]]
(`docs/experiments/active/thirst_task/THIRST_TASK.md`)
**Audited by:** env-config-reviewer
**Date:** 2026-10-01
**Code state:** `v5.0` worktree `.claude/worktrees/thirst`, HEAD `c631d8fa`

## Verdict (plain language)

**The question.** The thirst study trains two agents, one plain and one with a neuromodulator, in nine
worlds. All nine are the pond-and-thirst world: three map sizes (10×10, 15×15, 20×20), each with three
smell reaches (the whole map, 5 squares, 3 squares). Before 18 GPU runs start, this audit checks one thing:
does each world really differ from its neighbours only in the way the design says? Within a map size, only
the smell reach may differ. Across sizes, only the map, the pond and the scaled counts may differ.

**Answer: safe to launch.** All nine worlds load through the trainer's own loading path, the same
sequence of merges `train.py` performs. Each gives the planned 59-number observation, and every sensor in
the observation has a matching noise entry. Within each size the three worlds differ in exactly one
setting, the smell reach. Across sizes, every difference is one the design planned. Body, temperature,
water rates, rewards, noise and the 500-step episode limit are identical. The two agent configs change
nothing about the world. Level 06's header no longer presents the old pond smell as current.

**Nothing blocks the launch.** One moderate item should still be settled before the first run starts: run
all 18 at one commit (finding M1). The 10×10 worlds read the actively maintained ladder files live, and a
placement-fix plan for the environment is in flight on the same branch. If launches are spread over days, a
later run can train on a slightly different world from an earlier one.

**Severity legend:** 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run · 🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

## Findings

| # | Severity | File / YAML path | Issue | Suggested fix |
|---|---|---|---|---|
| M1 | 🟡 Moderate | Launch manifest, THIRST_TASK §9.2; `basic/05`, `basic/06`; [[PLACEMENT_FIXES_PLAN]] | The manifest records each run's commit but never requires the 18 commits to match. Two kinds of drift are possible. (a) The three 10×10 worlds inherit level 05/06 **live** through `extends:`, and `basic/` is the maintained, frequently edited ladder (level 05 was re-levelled 09-16 and gained random start body temperature 09-26). The 15×15 and 20×20 worlds are **frozen copies** of level 05's three lists. So a ladder edit made mid-sweep would reach the 10×10 runs and not the larger ones. (b) `PLACEMENT_FIXES_PLAN` (status: planned, on `v5.0`) changes how food regrows and stops the agent starting on a burning fire. If it lands between launches, the worlds differ by commit. Today, resolved through the loader, the three lists are identical to level 06's except for areas and counts (§Check 4), so this is a **hazard, not a present defect**. | Launch all 18 from one recorded commit and check that the commits match before calling the sweep valid. At minimum, launch both agents of a world at the same commit, because the §4 joint-stop comparison depends on it. `training-runner` / user. |
| O1 | ❓ Open | THIRST_TASK §7 row "Placement backstop / (0,0) cases appear in training" | Training has **no signal** for this stop rule. The (0,0) fallback (Known Bugs ~#117, OPEN) raises nothing and logs nothing; `core.py` has no counter. The fallback is mainly reachable through campfire packing, and the load-time pond capacity check does not model it: Manhattan separation ≥ 4 for up to 7 fires in an 11×11 box (15×15) and 12 in a 16×16 box (20×20). The design measured 0 in 2,000 resets per world. The 95 % upper bound of ≈0.15 % of resets, applied to ~10 M episodes per run, still allows thousands of affected episodes. Each would be a fire parked in corner (0,0), outside its inset area. The effect on survival is probably negligible, but the row as written cannot fire. | Either reword the §7 row as an accepted, measured-but-unmonitored risk, or add a post-hoc check: count fires at (0,0) in recorded evaluation episodes. `experiment-designer`. `bug-curator` already owns ~#117, so no new row is needed. |
| L1 | 🟢 Low | `water.properties` per-cell weight 1/(h·w) | The rule "the whole pond equals one food item" holds in the **far field** only. Near the pond, the bigger blocks smell weaker than a food item, and the gap grows with map size. Measured with the shipped kernel (decay power 1, on-cell value 2.0). Standing on the pond, the mean is 1.18 / 0.84 / 0.65 for 2×2 / 3×3 / 4×4, against 2.0 on a food item. One step off the pond's edge it is 0.66 / 0.53 / 0.43, against 1.0 at one step from food. Three steps off: 0.29 / 0.26 / 0.23 vs 0.33. This is the decided design (D3) and §6.3 notes the "faint plateau", but it is a size-correlated difference in the pond's local cue that the confounds table (§3.5) does not list. | Add one row to §3.5. No config change. |
| L2 | 🟢 Low | `CONFIG_CRITICAL_SETTINGS.md` 2026-10-01 entry | The entry is correct and complete: dated, what, reason, commit, blast radius, and no canonical value changed. One wording slip: "`sensor_radius` and `water.size` / `water.candidates` set locally in eight … configs". `sensor_radius` is set in all eight, but `water.size` / `candidates` only in the two whole-map files (the reach variants inherit them). Separately, `water.properties` is not a registry setting. So commit `c33d29b1` changed it in `default.yaml` correctly without a change-log entry, but the world's smell changed and the pilot trained on the old vector. That makes it a candidate for the registry. | Optional: tighten the wording; consider registering `water.properties`. |
| L3 | 🟢 Low | Frozen copies in `thirst/pond_thirst_15x15.yaml`, `thirst/pond_thirst_20x20.yaml` | The two whole-map files restate level 05's `resources` / `entities` / `obstacles` in full, as they must, because lists merge by replacement. Each header says so. They will not follow future level-05 edits. This is the long-run face of M1. | None now; say it in the study's summary if the ladder changes before the analysis. |

No 🔴 Critical findings.

## Checklist

- [x] **(1) Observation ↔ noise consistency — ✅.** Width **59** in all 9 worlds × both agents
  (Satiation 1, Body Temperature 1, Hydration 1, Interoceptive Nociception 1, Extero Nociception 1,
  Thermoception 5, Olfaction 25, Collision 5, Proprioception 6, Visual 13). Every breakdown name is in
  `noise_modality_order`. Extras in the noise table (Injury, Nutrition, Location) are harmless. Hydration
  is listed last rather than in breakdown position, which is fine because lookup is by name. The loader
  also refuses a water world without a `hydration` noise entry (`config_loader.py:2690`). Noise is off
  in all 9.
- [x] **(1.5) Bushes present when behaviour measures on — N/A.** `behavior_measures.enabled` is
  false in all 9. Bushes are present anyway (`hides_agent` and `blocks_animals` slots = 10 / 23 / 40 by size).
- [x] **(2) Mandatory-key discipline — ✅.** No new keys. Every water key is read with `get_mandatory`
  (`_load_water`). The fallback-read obstacle keys (`blocks_animals` via `o.get(..., False)`,
  `config_loader.py:2184`; `blocks_sight`; `hides_agent`) resolve identically to level 06 in every world. The
  `obs_blocks_animals` count equals the bush allocation (10 / 23 / 40), so no bush lost its flag. Known
  Bugs row 138 (noise switch read with a fallback) is not triggered, because the key is present via `default.yaml`.
- [x] **(3) Static fields and recompiles — ✅.** Each run is its own process and compiles once. Within a
  size, the three worlds differ **only** in `sensor_radius`, a dynamic (pytree) field, so the reach
  variants share every static field, including the water tables. Across sizes the static fields that
  differ are the planned ones: `height`, `width`, `max_per_type`, `num_entities`, animal index tuples,
  `water_block_h/w`, `water_topleft_table`, `water_cell_property`. Nothing is varied **during** a run
  (single `--config`, no curriculum).
- [x] **(4) Latent-bug recurrences — ⚠️ known, accepted.** ~#117, the silent (0,0) parking: 0 / 2,000 resets
  measured, no runtime signal (O1). Agent starting on a burning fire, 1.85 / 2.15 / 2.30 % of resets: known,
  owned by [[PLACEMENT_FIXES_PLAN]], same in both agents of a world. No new latent-bug trigger found.
- [x] **(5) Schema padding — ✅ (at capacity).** Noise arrays have 13 slots and 13 modalities are named
  (Hydration took the last). The loader raises a clear error if a 14th is added
  (`config_loader.py:3208`). Not triggered here.
- [x] **(6) Cross-config coherence — ✅ with M1.** Details below.

## Evidence (Methods)

**Loader path.** A scratch script replicates `train.py`'s assembly order exactly:
`get_default_config()` → `train/default.yaml` → `train/recurrent_ppo.yaml` → `load_env_config(evaluation/default.yaml)`
→ `logger/wandb.yaml` → `visualization/default.yaml` → `load_env_config(<world>)` → agent YAML →
`load_env_params`. The script then diffs every one of the 222 `EnvParams` fields with exact array equality,
and separately diffs the resolved environment config key by key. All 18 combinations loaded without error.
Resolved run settings are identical in all 18: seed 42, 128 parallel worlds, checkpoint every 200,000
episodes, `max_steps` 500, random start position on, placement `per_entity`, water drain 0.625, drink gain 5.625,
max 200, setpoint 100, random start hydration [0, 200), pond vision [1.0], smell decay power 1.0.

**Check 2, within a size (EnvParams diff, then resolved-config diff):**

| Pair | Differing fields |
|---|---|
| g10sW vs g10s5 / g10s3 | `sensor_radius` 20 → 5 / 3 only |
| g15sW vs g15s5 / g15s3 | `sensor_radius` 30 → 5 / 3 only |
| g20sW vs g20s5 / g20s3 | `sensor_radius` 40 → 5 / 3 only |
| t1none vs t16quad agent, any world | none (agent configs touch no environment key) |

**Check 3, across sizes (resolved environment config vs level 06).** Only these paths differ:
`environment.height/width`; `location_areas[0]` grass area end; `resources[0..1]` counts and spawn-area end;
`entities[0..1]` `count_high`, spawn and patrol area end; `obstacles[0,1,3]` (campfire, rock, bush) counts and area end;
`sensory.sensor_radius`; `water.size`; `water.candidates`. Everything in the `EnvParams` diff traces to
those: per-slot tables resized, plus `type_areas`, `type_counts`, `water_*` tables. Nothing unplanned:
no body, thermal, reward, noise, episode-cap or water-rate field differs. Tree stays count 0 with
its inert out-of-grid area unchanged.

| | 10×10 (level 06) | 15×15 | 20×20 |
|---|---|---|---|
| food / ambush / predator / rabbit | 1–4 / 2–12 / 0–2 / 0–2 | 2–9 / 5–27 / 0–5 / 0–5 | 4–16 / 8–48 / 0–8 / 0–8 |
| campfire / rock / bush (tree 0) | 1–3 / 6–12 / 4–10 | 2–7 / 14–27 / 9–23 | 4–12 / 24–48 / 16–40 |
| campfire area after 2-cell inset (0-based, end-exclusive) | [2,2,8,8] | [2,2,13,13] | [2,2,18,18] |

These match THIRST_TASK §3.2. The rounding was re-checked: 2.25 × {1, 2, 3, 4, 6, 10, 12} → 2, 5, 7, 9, 14, 23, 27, half up.

**Check 5, water placement.**

| | Pond | Top-left table (0-based) | Inside grid and 1-cell margin | Capacity check: minimum slack (cells spare at tightest slot) | Per-cell smell (ch. 0) | Σ over pond |
|---|---|---|---|---|---|---|
| 10×10 | 2×2 | (1,1) (1,7) (7,1) (7,7) | yes | 14 (campfire box) | 0.25 | 1.0 |
| 15×15 | 3×3 | (1,1) (1,11) (11,1) (11,11) | yes | 69 (campfire box) | 0.1111 | 1.0 |
| 20×20 | 4×4 | (1,1) (1,15) (15,1) (15,15) | yes | 163 (campfire box) | 0.0625 | 1.0 |

The loader's own capacity check (`config_loader.py:3061-3072`) passed for every world, which is why they
load. The slack column recomputes it from the loaded `EnvParams`. The check counts cells only. It does not
model fire-to-fire separation, which is O1. Smell reach is applied as Euclidean `dist <= sensor_radius` in
`sense_resource`. The whole-map values (20/30/40) exceed the largest in-grid distances (12.7/19.8/26.9), so the
cut-off never binds there.

**Check 7, level 06 header.** The old vector `[0.5, 0, 0, 0, 0.5]` appears once, in a sentence saying the
pond smelled that way *before* 2026-10-01 and that the pilot runs trained on it. The current text says the
pond smells only of food, `[1.0, 0, 0, 0, 0]` per pond, a quarter per cell. The channel-4 label is back to
"Tree". A repository-wide search finds the old vector only in dated history (`09_sensors_and_observation.md:1014`,
`CONFIG_GUIDE.md:568`).

## Conclusion

Safe to launch. No Critical items. Before the first launch, settle M1: one commit for all 18 runs, or at
least for both agents of each world. O1 and L1 are one-line edits to the design doc.

Audited by: env-config-reviewer
