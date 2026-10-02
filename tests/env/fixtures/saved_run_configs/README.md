# Saved run configs (verbatim copies)

Byte-for-byte copies of two finished training runs' own saved settings files
(`results/JAX_RecurrentPPO/<run>/models/config.yaml`), copied 2026-09-26. `results/` is
gitignored, so the test needs its own copies.

| File | Source run | Sweep | sha1 |
|---|---|---|---|
| `20260921-114858_rppo_basicq2_lvl05_t1none_s42.yaml` | `results/JAX_RecurrentPPO/20260921-114858_rppo_basicq2_lvl05_t1none_s42/models/config.yaml` | Wave 1, level 05 | `5c368d5044c047aa842da4e408de8d09bc324c60` |
| `20260922-182534_rppo_bq2cover_lvl05_t1none_s42.yaml` | `results/JAX_RecurrentPPO/20260922-182534_rppo_bq2cover_lvl05_t1none_s42/models/config.yaml` | Wave 2, level 05 | `803041fdd47a5107e7e128dac934548558033142` |

Used by `tests/env/test_saved_config_compat.py` (the gate of
`docs/develop/active/thermal/STATE_DEPENDENT_BODY_MECHANICS.md` §A7). **Do not edit
these files** — the test's point is that a frozen, pre-change saved config re-opens through
`src/environment/saved_config_compat.py`. They are meant to move into the era-fixture set
of `docs/develop/active/refactors/SAVED_RUN_CONFIG_COMPAT.md` when that plan lands.
