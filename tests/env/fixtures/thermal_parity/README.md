# Thermal-parity goldens — and the one re-baselined on 2026-09-21

## In one paragraph

Each `.npz` records a **100-step episode from seed 0** for one world: the full observation (clean
and noisy), the reward, both homeostatic drives, the PRNG key, entity positions and the sampled
entity properties. `tests/env/test_thermal_parity.py` replays it and asserts equality (one narrow,
derived float32-ulp exemption — see that module's docstring). Unlike the refactor-pinning families,
this one deliberately tracks the **current** world: going red on an intended behaviour change is
its loudness function, and the response is to regenerate with the cause recorded.

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

**How it was regenerated.** Via the repo's own generator,
`scripts/fixtures/generate_thermal_parity_fixtures.py`, calling its `generate_fixture()` for this
single config on the CPU backend. Its `main()` was deliberately **not** run: `main()` walks
`collect_configs()` and would both rewrite all 12 existing goldens and create ~20 new ones for
configs that currently have none — silently expanding what this gate adjudicates. Recover the
previous artefact with `git show 47b1b8c3~1:tests/env/fixtures/thermal_parity/configs__environment__default.npz`.

## Why the run reports 20 skips

`_collect_configs()` walks 32 maintained configs; only the 12 with a golden here are adjudicated and
the rest are **skipped, not passed**. That is the module's documented "honest coverage statement"
(thermal plan, F6) and is unchanged by this re-baseline — read a green run as 12 worlds checked, not 32.
