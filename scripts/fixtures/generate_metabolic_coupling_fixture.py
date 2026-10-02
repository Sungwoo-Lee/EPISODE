"""Generate the Stage-5 metabolic-coupling no-op fixture.

**What this fixture is for.** Stage 5 of the temperature plan adds a nutrition
drain that fires only when `thermal.metabolic_coupling` is true, and ships with
it false. The claim that has to be defended is therefore not "the drain is
correct" but "with the drain switched off, nothing moved" — and specifically
nothing moved *on a thermal-ON config*, because that is the one the coupling
code sits inside. The Stage 0 parity fixtures cannot see this: every config in
that set is thermal-off by construction (`test_thermal_parity.py` asserts it),
so they are all blind to a coupling that leaks on a thermal-on world.

So this captures a full thermal-on rollout — every numeric state leaf, the
reward, `done`, and every numeric `info` entry, over reset + 300 steps of a fixed
action sequence from seed 0 — and `tests/env/test_metabolic_coupling.py` holds
the current code to it with `np.array_equal` and no tolerance.

**It must be generated from code that predates the Stage 5 edit**, or it proves
nothing: a fixture regenerated from the edited source is a re-derivation through
the very function under suspicion, and would agree with a coupling that fires
when disabled. That is what `--src-root` is for. Point it at a git worktree of
the Stage 4 tip:

    git worktree add --detach /tmp/gwp_stage4_baseline c0c0a619
    /home/vncuser/miniconda3/envs/grid_world_pain/bin/python \
        scripts/fixtures/generate_metabolic_coupling_fixture.py \
        --src-root /tmp/gwp_stage4_baseline

`--src-root` supplies BOTH the `src/` package and the config, so the captured
world is entirely that commit's. The commit SHA is stamped into the .npz as
`_provenance_sha` and the test reports it on failure.

Re-running this without `--src-root` regenerates the fixture from the working
tree, which defeats its purpose. Don't, unless the reference is deliberately
being re-baselined and the new baseline is stated in the commit message.
"""
import os

# Backend pinning MUST precede any jax import: fixtures generated on GPU and
# compared on CPU differ in the last bits and the gate becomes noise. Same form
# as scripts/fixtures/generate_thermal_parity_fixtures.py.
os.environ.setdefault("JAX_PLATFORMS", "cpu")

import argparse
import dataclasses
import subprocess
import sys

import numpy as np
import yaml

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))

# The config, the action sequence and the seed are duplicated in
# tests/env/test_metabolic_coupling.py. They must agree; the test says so too.
CONFIG_REL = os.path.join(
    "configs", "environment", "experiment", "archive", "thermal", "campfire_world.yaml")
OUT_REL = os.path.join(
    "tests", "env", "fixtures", "metabolic_coupling", "thermal_on_coupling_off.npz")
# 300 steps. Long enough that the agent moves around the world, eats, and lets
# its body temperature fall a long way from the setpoint — a drain that fired
# when disabled would have 300 chances to show up in `state.nutrition`.
ACTIONS = [0, 1, 2, 3, 4, 5, 1, 1, 2, 2] * 30
SEED = 0


def numeric_leaves(state, tag):
    """Every numeric field of the EnvState dataclass, as numpy, prefixed by `tag`."""
    out = {}
    for f in dataclasses.fields(state):
        value = getattr(state, f.name)
        try:
            arr = np.asarray(value)
        except Exception:
            continue
        if arr.dtype.kind in "biufc":
            out[f"{tag}.{f.name}"] = arr
    return out


def rollout(src_root):
    sys.path.insert(0, src_root)
    import jax
    from src.utils.config import Config
    from src.environment.config_loader import load_env_params
    from src.environment.core import jax_reset, jax_step

    with open(os.path.join(src_root, CONFIG_REL)) as fh:
        params = load_env_params(Config(yaml.safe_load(fh)))
    # Both assertions are the point of the fixture, not paperwork: a thermal-off
    # capture would duplicate the Stage 0 fixtures, and a nutrition-off capture
    # would be blind to the exact quantity the coupling moves.
    assert params.thermal_enabled, f"{CONFIG_REL} must be thermal-ON for this fixture"
    assert params.with_nutrition, f"{CONFIG_REL} must have nutrition ON for this fixture"

    state = jax_reset(params, jax.random.PRNGKey(SEED))
    series = {}

    def push(d):
        for k, v in d.items():
            series.setdefault(k, []).append(v)

    push(numeric_leaves(state, "state"))
    for action in ACTIONS:
        state, reward, done, info = jax_step(state, action, params)
        push(numeric_leaves(state, "state"))
        rec = {"reward": np.asarray(reward), "done": np.asarray(done)}
        for k, v in sorted(info.items()):
            try:
                arr = np.asarray(v)
            except Exception:
                continue
            if arr.dtype.kind in "biufc":
                rec[f"info.{k}"] = arr
        push(rec)
    return {k: np.stack(v) for k, v in series.items()}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src-root", default=_ROOT,
                    help="Repo root to import src/ and read the config from. Point "
                         "it at a worktree of the pre-Stage-5 tip; defaults to this "
                         "working tree, which is NOT a valid reference.")
    args = ap.parse_args()
    src_root = os.path.abspath(args.src_root)

    try:
        sha = subprocess.check_output(
            ["git", "-C", src_root, "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        sha = "unknown"

    arrays = rollout(src_root)
    out = os.path.join(_ROOT, OUT_REL)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    np.savez(out, _provenance_sha=np.array(sha), **arrays)
    print(f"wrote {out}")
    print(f"  source tree : {src_root}")
    print(f"  HEAD        : {sha}")
    print(f"  arrays      : {len(arrays)}  "
          f"({sum(a.size for a in arrays.values())} scalars over "
          f"{len(ACTIONS)} steps)")


if __name__ == "__main__":
    main()
