# Thermal-parity goldens — and the two re-baselines they have had

## In one paragraph

Each `.npz` records a **100-step episode from seed 0** for one world: the full observation (clean
and noisy), the reward, both homeostatic drives, the PRNG key, entity positions and the sampled
entity properties. Two test modules replay them: `tests/env/test_thermal_parity.py` (adjudicates
everything — observations, placement, reward, drives) and `tests/env/test_thermal_reward_gate.py`
(adjudicates `reward` / `drive_before` / `drive_after` only, with no tolerance of any kind).
**Both read the same files**, which is why a re-baseline decided for one of them is automatically a
re-baseline for the other — see "The shared-file consequence" below. Unlike the refactor-pinning
fixture families, this one deliberately tracks the **current** world: going red on an intended
behaviour change is its loudness function, and the response is to regenerate with the cause
recorded.

## Provenance — which goldens are pre-thermal, and which are not

`test_thermal_reward_gate.py` is built on the claim that these fixtures were captured **before**
`calculate_drive` was edited for the thermal work, so it compares against pre-change ground truth
rather than re-deriving through the edited function. That claim is **true of 11 of the 12 goldens
and false of the twelfth**:

| Goldens | Captured | Re-derived since? | Pre-thermal reference? |
|---|---|---|---|
| The 11 `configs__continual__…` and `configs__verification__…` files | `765c8769`, 2026-09-08 | never | **yes** — genuine Stage 0 |
| `configs__environment__default.npz` | `765c8769`, 2026-09-08 | `02be34ae` (2026-09-15), `53649b40` (2026-09-21), `<this change>` (2026-09-22) | **no** — see below |

`calculate_drive` gained its thermal branch on 2026-09-09 (`c0c0a619`, Stage 4). The `default`
golden's `reward` / `drive` arrays were re-derived through the post-thermal function on
**2026-09-15** at `02be34ae` ("the bush blocks animals"), which changed agent behaviour and so
changed the reward trajectory. From that date onwards the `default` case has been a
**commit-to-commit regression anchor**, not pre-change ground truth. The 11 standalone worlds are
unaffected by config or default-world changes — each carries its own `body:` block with no
`extends:` — and they still carry the strong claim.

Do not describe the `default` case as a pre-thermal reference. Recovering one is not possible from
the test side: the 2026-09-15 divergence came from a `src/` behaviour change, not a config value.

## The shared-file consequence

Because both modules read these files, "pin the settings inside the reward gate so it keeps matching
the old fixture" and "re-baseline the golden so the parity gate tracks the live world" are **mutually
exclusive** on the same `.npz`. Pinning in one module makes the other fail. Splitting the file to
allow both was considered and rejected: the `default` reward reference has not been pre-thermal since
2026-09-15, so a frozen copy would preserve a *week-old re-derivation* while presenting it as
pre-change ground truth — strictly worse than the honest anchor, and the same self-agreeing failure
mode `b4fd22a0` removed from the visual-parity gate.

## The 2026-09-22 re-baseline

| | |
|---|---|
| **Cause** | the recovery-rate retune in `configs/environment/default.yaml`, adopting the recommendation of `docs/experiments/active/recovery_in_bush_tuning/recovery_in_bush_tuning.md` |
| **Date** | 2026-09-22 |
| **File re-baselined** | `configs__environment__default.npz` — **the only one**; the other 11 goldens were untouched and stayed green |

**What changed.** Three `body:` settings:

| Setting | Before | After |
|---|---|---|
| `body.recovery_base_rate` | 0.1 | **0.2** |
| `body.recovery_accel_rate` | 0.5 | **0.0** |
| `body.recovery_in_bush_multiplier` | 1.0 | **25.0** |

At the old values an agent cleared the entire 100-point injury scale resting on open ground in about
12 rest steps, so cover had no healing role to play. The retune is intended and permanent.

**How it reaches the reward.** The 100-step fixture episode replays `ACTIONS = [0,1,2,3,4] * 20`,
which includes the Rest action (4) twenty times. Recovery therefore changes the injury trajectory;
`calculate_drive(satiation, injury_level, params)` reads injury as its second axis; and the reward is
the drive difference across the step. Both gates failed on `'reward'` at `max |diff| = 3.440e-01`.

**Cross-check before the new golden was committed.** The regenerated fixture changed **only** the
injury-coupled fields — `reward`, `drive`, `drive_before`, `drive_after`, `obs_clean`, `obs_noisy`.
`key`, `res_pos`, `animal_pos`, `obs_pos`, all three sampled-property arrays, `termination_reason`
and `done` are **bit-identical** to the previous golden, which is what a pure body-parameter change
must look like: no PRNG drift, no placement change, no width change. `obs_breakdown_total` and
`obs_dim` stayed **52**, so `test_thermal_parity.py`'s `_EXPECTED_OBS_WIDTH` tripwire is unchanged
and still fires before the fixture is consulted.

**The gate was shown to still bite after the re-baseline.** With the thermal-off branch of
`calculate_drive` mutated (`injury` → `injury * 1.001`), the re-baselined
`configs__environment__default` case of `test_thermal_reward_gate.py` **fails**, alongside the 11
untouched Stage 0 cases. A re-baselined golden that could no longer detect a change to the
expression it guards would have been a reason to stop rather than to commit.

**How it was regenerated.** Via the repo's own generator,
`scripts/fixtures/generate_thermal_parity_fixtures.py`, calling its `generate_fixture()` for this
single config on the CPU backend — nothing hand-written. Its `main()` was deliberately **not** run:
`main()` walks `collect_configs()` and would both rewrite all 12 existing goldens and create ~20 new
ones for configs that currently have none, silently expanding what these gates adjudicate. Recover
the previous artefact with
`git show <this commit>~1:tests/env/fixtures/thermal_parity/configs__environment__default.npz`.

## The 2026-09-21 re-baseline

| | |
|---|---|
| **Cause** | commit **`47b1b8c3`** — *"default sensory becomes the ladder's Q2 arm (olf 1 / vis 2 / vec 1 / clamp)"* |
| **Date** | 2026-09-21 |
| **File re-baselined** | `configs__environment__default.npz` — **the only one**; the other 11 goldens were untouched and stayed green |

**What changed.** `configs/environment/default.yaml` adopted the sensor ladder's
`Q2_presence_binary` arm: smell gained a direction (`olfactory_grid_range` 0 → 1, 1 sampled cell →
5), sight gained a field (`visual_sensor_range` 0 → 2, a 13-cell diamond) but lost the ability to
say *what* it sees (`visual_vector_size` 8 → 1 with `visual_value_mode` `sum` → `clamp`), and
distance blurring was switched on. The observation width went **27 → 52**, which is exactly how the
gate failed:

```
configs__environment__default: sum(get_observation_breakdown(params).values()) changed 27 -> 52
```

**Cross-check before the new golden was committed:** the regenerated fixture records
`obs_breakdown_total = 52` and `obs_clean.shape = (101, 52)`, matching the width verified
independently by the user through `train.py`'s own config merge order. The test now also declares
that 52 in `_EXPECTED_OBS_WIDTH` and checks it **before** consulting the fixture, so a golden
regenerated from a stale or frozen input cannot agree with itself into a green run.

That re-baseline touched **only the observation fields** — `reward` and all three drive arrays came
back bit-identical to the pre-existing golden, which is why it did not disturb
`test_thermal_reward_gate.py`.

**How it was regenerated.** Same single-config `generate_fixture()` route described above. Recover
the previous artefact with
`git show 47b1b8c3~1:tests/env/fixtures/thermal_parity/configs__environment__default.npz`.

## Why the run reports 20 skips

`_collect_configs()` walks 32 maintained configs; only the 12 with a golden here are adjudicated and
the rest are **skipped, not passed**. That is the module's documented "honest coverage statement"
(thermal plan, F6) and is unchanged by either re-baseline — read a green run as 12 worlds checked,
not 32.

## The 2026-09-22 re-baseline (second of the day) — `configs__environment__default.npz`

**Cause.** Nutrition became a **two-sided** homeostatic axis: `body.max_nutrition` 100 → 200,
`body.max_satiation` 100 → 200, `body.satiation_setpoint` staying at 100 so it is now the
*middle* of the range rather than its ceiling, and `body.overeating_death` false → **true**.

**Why this golden moved, and why nothing else did.** The observation channel is
`state.satiation / params.max_satiation` (`src/environment/sensor.py:477`), so doubling the
ceiling **halves** the reported Satiation value at any given nutrition. Measured field by
field on the same 100-step rollout, before against after:

| field | result |
|---|---|
| `obs_clean`, `obs_noisy` | **moved** — column **0 only** (Satiation), max abs diff exactly **0.5** |
| `reward`, `drive`, `drive_before`, `drive_after` | bit-identical |
| `done`, `termination_reason`, `n_steps` | bit-identical |
| `key`, `seed` | bit-identical — no PRNG drift |
| `obs_pos`, `res_pos`, `animal_pos` and all three `*_property_sampled` | bit-identical |
| `obs_dim`, `obs_breakdown_total` | unchanged (52) |

The reward being bit-identical is the load-bearing observation. At
`nutrition_to_satiation_scaling_factor: 1.0` satiation equals nutrition on **both** sides of
the change (`100·N/100` and `200·N/200`), so the body trajectory over this rollout is
unchanged; only the *reported* fraction moved. The two worlds can first diverge once nutrition
passes 100, which the old ceiling clipped and the new one does not — this rollout never does.

**How it was regenerated.** `scripts/fixtures/generate_thermal_parity_fixtures.py::generate_fixture()`
on this single config, CPU backend. `main()` was deliberately not run: it walks
`collect_configs()` and would rewrite all twelve goldens and create roughly twenty more.

**The other eleven goldens are untouched**, and that is the gate rather than a convenience:
each is a standalone config with its own `body:` block and no `extends:`, so none of them
inherits from `configs/environment/default.yaml` and none could move. If one ever does after a
`default.yaml` edit, that edit has escaped its blast radius and the change is wrong.

