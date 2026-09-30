# Water parity fixture (pre-change rollouts)

Ground truth for `tests/env/test_water_parity.py` (THIRST_WATER_PLAN §T1): every
world with `water.enabled: false` must replay these arrays byte for byte.

- **Source commit**: `359d192adb180045f932e8b00f591564a7d3850f` (a detached worktree of the pre-change commit)
- **Command**: `JAX_PLATFORMS=cpu /home/vncuser/miniconda3/envs/grid_world_pain/bin/python scripts/fixtures/generate_water_parity_fixture.py --src-root <worktree of the SHA above>`
- **Source tree used**: `/tmp/gwp_water_baseline`
- **Variants**: each world as shipped (seeds 0-15 x 300 steps), and `<world>__trunc` with `environment.max_steps: 30` in memory (seeds 0-7 x 150 steps) so the step-limit ending (code 1) is exercised. See the generator's docstring.

## Termination-code counts (steps carrying each code)

Codes: 0 alive, 1 step limit, 2 starvation, 3 over-eating, 4 injury, 5 thermal.

| Variant | code 0 | code 1 | code 2 | code 3 | code 4 | code 5 |
|---|---|---|---|---|---|---|
| `default` | 4595 | 0 | 1 | 0 | 204 | 0 |
| `default__trunc` | 1141 | 19 | 0 | 0 | 40 | 0 |
| `lvl00` | 4748 | 0 | 21 | 0 | 31 | 0 |
| `lvl00__trunc` | 1159 | 33 | 0 | 0 | 8 | 0 |
| `lvl01` | 4581 | 0 | 2 | 0 | 217 | 0 |
| `lvl01__trunc` | 1132 | 18 | 0 | 0 | 50 | 0 |
| `lvl02` | 4693 | 0 | 10 | 0 | 97 | 0 |
| `lvl02__trunc` | 1155 | 28 | 0 | 0 | 17 | 0 |
| `lvl03` | 4610 | 0 | 31 | 0 | 159 | 0 |
| `lvl03__trunc` | 1137 | 23 | 6 | 0 | 34 | 0 |
| `lvl04` | 4636 | 0 | 29 | 0 | 135 | 0 |
| `lvl04__trunc` | 1138 | 24 | 5 | 0 | 33 | 0 |
| `lvl05` | 4616 | 0 | 30 | 0 | 141 | 13 |
| `lvl05__trunc` | 1128 | 18 | 7 | 0 | 44 | 3 |
| `noise06` | 4616 | 0 | 30 | 0 | 141 | 13 |
| `noise06__trunc` | 1128 | 18 | 7 | 0 | 44 | 3 |

Do not regenerate from a post-change tree: it would compare the code with itself and prove nothing.
