"""Generate the single-rate body-temperature fixture for the warming/cooling speed keys.

**What this fixture is for.** `thermal.warming_rate_scale` and
`thermal.cooling_rate_scale` multiply the body's per-step temperature change,
one when the temperature is rising and the other when it is falling. Both ship
at 1.0, and the claim to defend is that at 1.0 / 1.0 nothing moved: the body
warms and cools exactly as the single-rate code did. The only older thermal-on
fixture (`metabolic_coupling/thermal_on_coupling_off.npz`) cannot defend that
claim, because its body never warms (0 warming steps in 300), so a mistake in
the warming half of the change would pass it.

So this records four rollouts in a world whose temperature is one constant value
everywhere, with the agent resting in place for 150 steps:

| name       | cell temp | start body temp | metabolic coupling | exercises |
|------------|-----------|-----------------|--------------------|-----------|
| `warm_off` | +10.0     | -14.0           | off                | warming only (settles at +8) |
| `cool_off` | -10.0     | +14.0           | off                | cooling only (settles at -8) |
| `warm_on`  | +10.0     | -14.0           | on, rate 1.0       | warming; the drain changes sign at 0 |
| `cool_on`  | -10.0     | +14.0           | on, rate 1.0       | cooling; the drain changes sign at 0 |

`tests/env/test_thermal_rate_scales.py` holds the current code to it with
`np.array_equal` and no tolerance.

**The scenario table, `SEED`, `N_STEPS` and `REST` are duplicated in
`tests/env/test_thermal_rate_scales.py`.** Change one and you must change the
other, or the test compares two different rollouts.

**It must be generated from code that predates the change**, or it proves
nothing: a fixture regenerated from the edited source agrees with whatever the
edited source does. That is why `--src-root` is REQUIRED (no default). Point it at
a git worktree of the pre-change tip:

    git worktree add --detach /tmp/gwp_prescale_baseline <pre-change SHA>
    /home/vncuser/miniconda3/envs/grid_world_pain/bin/python \
        scripts/fixtures/generate_thermal_rate_scale_fixture.py \
        --src-root /tmp/gwp_prescale_baseline
    git worktree remove /tmp/gwp_prescale_baseline

`--src-root` supplies BOTH the `src/` package and the config, so the captured
world is entirely that commit's. Its SHA is stamped into the .npz as
`_provenance_sha`. The output always goes to THIS checkout's `tests/env/fixtures/`.

Plan: docs/develop/active/thermal/WARMING_COOLING_RATE_SCALES.md
"""
import os

# Backend pinning MUST precede any jax import: fixtures generated on GPU and
# compared on CPU differ in the last bits and the gate becomes noise.
os.environ.setdefault("JAX_PLATFORMS", "cpu")

import argparse
import copy
import subprocess
import sys

import numpy as np
import yaml

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))

CONFIG_REL = os.path.join(
    "configs", "environment", "experiment", "archive", "thermal", "campfire_world.yaml")
OUT_REL = os.path.join(
    "tests", "env", "fixtures", "thermal_rate_scales", "single_rate_rollouts.npz")

# Duplicated in tests/env/test_thermal_rate_scales.py — keep the two in step.
SEED = 0
N_STEPS = 150
REST = 4
SCENARIOS = {
    # name: (cell temperature, start body temperature, metabolic coupling on?)
    "warm_off": (10.0, -14.0, False),
    "cool_off": (-10.0, 14.0, False),
    "warm_on": (10.0, -14.0, True),
    "cool_on": (-10.0, 14.0, True),
}
COUPLING_RATE = 1.0


def uniform_world(raw, cell_temp, coupling):
    """The campfire world with a constant field and nothing that can end the episode.

    Copied verbatim from `tests/env/test_thermal_body.py::_uniform_field_config`
    (heat sources off, degenerate `default_temp`, no entities, only campfire
    obstacles, only food resources, `max_steps=500`, `body.metabolic_cost=0.0`),
    plus the metabolic-coupling switch for the `*_on` scenarios.
    """
    d = copy.deepcopy(raw)
    d["thermal"]["use_object_sources"] = False
    d["thermal"]["use_random_spots"] = False
    d["thermal"]["default_temp"] = [float(cell_temp), float(cell_temp)]
    d["environment"]["entities"] = []
    d["environment"]["obstacles"] = [
        o for o in d["environment"]["obstacles"] if o.get("name") == "campfire"]
    d["environment"]["resources"] = [
        r for r in d["environment"]["resources"] if r.get("type") == "food"]
    d["environment"]["max_steps"] = 500
    d["body"]["metabolic_cost"] = 0.0
    if coupling:
        d["thermal"]["metabolic_coupling"] = True
        d["thermal"]["metabolic_coupling_rate"] = COUPLING_RATE
    return d


def rollouts(src_root):
    sys.path.insert(0, src_root)
    import jax
    import jax.numpy as jnp
    from src.utils.config import Config
    from src.environment.config_loader import load_env_params
    from src.environment.core import jax_reset, jax_step
    import src.environment.core as _core
    # The whole fixture is worthless if `src` resolved to some other checkout.
    assert os.path.abspath(_core.__file__).startswith(src_root + os.sep), (
        f"src imported from {_core.__file__}, not from --src-root {src_root}")

    with open(os.path.join(src_root, CONFIG_REL)) as fh:
        raw = yaml.safe_load(fh)

    arrays = {}
    for name, (cell, t0, coupling) in SCENARIOS.items():
        params = load_env_params(Config(uniform_world(raw, cell, coupling)))
        assert params.thermal_enabled, f"{name}: world must be thermal-ON"
        assert params.with_nutrition, f"{name}: world must have nutrition ON"
        assert bool(params.thermal_metabolic_coupling) is coupling, name

        state = jax_reset(params, jax.random.PRNGKey(SEED))
        state = state.replace(body_temp=jnp.asarray(t0, dtype=state.body_temp.dtype))
        body_temp, nutrition = [np.asarray(state.body_temp)], [np.asarray(state.nutrition)]
        done, reason, ate = [], [], []
        for _ in range(N_STEPS):
            state, _reward, d, info = jax_step(state, REST, params)
            body_temp.append(np.asarray(state.body_temp))
            nutrition.append(np.asarray(state.nutrition))
            done.append(np.asarray(d))
            reason.append(np.asarray(info["termination_reason"]))
            ate.append(np.asarray(info["ate_food"]))
        arrays[f"{name}.body_temp"] = np.stack(body_temp)
        arrays[f"{name}.nutrition"] = np.stack(nutrition)
        arrays[f"{name}.done"] = np.stack(done)
        arrays[f"{name}.termination_reason"] = np.stack(reason)
        arrays[f"{name}.ate_food"] = np.stack(ate)
    return arrays


def check_non_vacuous(arrays):
    """The fixture must actually contain warming, cooling and a drain, and nothing else.

    Shared in spirit with the test, which repeats these asserts on the loaded file.
    """
    for name in SCENARIOS:
        diffs = np.diff(arrays[f"{name}.body_temp"].astype(np.float64))
        if name.startswith("warm"):
            assert int((diffs > 0).sum()) >= 100, f"{name}: fewer than 100 warming steps"
        else:
            assert int((diffs < 0).sum()) >= 100, f"{name}: fewer than 100 cooling steps"
        assert not arrays[f"{name}.done"].any(), f"{name}: episode ended inside the rollout"
        assert not arrays[f"{name}.ate_food"].any(), f"{name}: the resting agent ate food"
    for kind in ("warm", "cool"):
        on = float(arrays[f"{kind}_on.nutrition"][-1])
        off = float(arrays[f"{kind}_off.nutrition"][-1])
        assert off - on > 1.0, f"{kind}: coupling-on nutrition not lower by > 1.0 ({on} vs {off})"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src-root", required=True,
                    help="Repo root to import src/ and read the config from: a worktree "
                         "of the pre-change tip. Required on purpose; the working tree "
                         "is NOT a valid reference.")
    args = ap.parse_args()
    src_root = os.path.abspath(args.src_root)

    try:
        sha = subprocess.check_output(
            ["git", "-C", src_root, "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        sha = "unknown"

    arrays = rollouts(src_root)
    check_non_vacuous(arrays)
    out = os.path.join(_ROOT, OUT_REL)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    np.savez(out, _provenance_sha=np.array(sha), **arrays)
    print(f"wrote {out}")
    print(f"  source tree : {src_root}")
    print(f"  HEAD        : {sha}")
    for name in SCENARIOS:
        bt = arrays[f"{name}.body_temp"]
        nu = arrays[f"{name}.nutrition"]
        print(f"  {name:9s}: body {bt[0]:+.3f} -> {bt[-1]:+.4f}   "
              f"nutrition {nu[0]:.3f} -> {nu[-1]:.3f}")


if __name__ == "__main__":
    main()
