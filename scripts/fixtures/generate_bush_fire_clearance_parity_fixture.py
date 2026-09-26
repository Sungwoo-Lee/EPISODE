"""Generate the pre-change reset fixture for the bush-to-fire clearance rule.

**What this fixture is for.** The plan `docs/develop/active/thermal/BUSH_FIRE_CLEARANCE.md`
adds `thermal.bush_min_fire_distance`, a world-generation rule that keeps bushes away from
campfires. It ships at `0` (off). The claim to defend is that at `0` world generation is
exactly the pre-change code's: the same random numbers, the same positions, the same
compiled graph. This script records the pre-change behaviour;
`tests/env/test_bush_fire_clearance.py` holds HEAD to it with `np.array_equal` (no
tolerance) and jaxpr-string equality.

**Worlds** (resolved through `load_env_config` -> `load_env_params`, as the trainer does):
  * `lvl05`    -- curriculum level 05 (campfire, thermal on);
  * `lvl05_d3` -- level 05 with `thermal.food_min_fire_distance: 4` set in memory, so the
                  food-to-fire pass that the new bush pass sits next to is exercised;
  * `lvl04`    -- curriculum level 04 (thermal off);
  * `default`  -- `configs/environment/default.yaml` (thermal off).

**Records per world:** the `jax_reset` and `jax_step` jaxpr SHA-1 (params traced, via the
body-mechanics generator's `jaxpr_shas`), every `EnvState` leaf of `jax_reset` for seeds
`0..63` (stacked along axis 0), and the resolved config as canonical YAML (so the test can
name unrelated config drift instead of reporting an unexplained mismatch).

**It must be generated from code that predates the change**, or it proves nothing.
`--src-root` is REQUIRED (no default). Point it at a detached worktree of the pre-change
commit:

    git worktree add --detach /tmp/gwp_bushclear_baseline <pre-change SHA>
    JAX_PLATFORMS=cpu /home/vncuser/miniconda3/envs/grid_world_pain/bin/python \\
        scripts/fixtures/generate_bush_fire_clearance_parity_fixture.py \\
        --src-root /tmp/gwp_bushclear_baseline
    git worktree remove /tmp/gwp_bushclear_baseline

`--src-root` supplies BOTH `src/` and `configs/`. Its SHA is stamped as
`_provenance_sha`. Output always goes to THIS checkout's `tests/env/fixtures/`.

The world list, seeds and the in-memory override are imported by the test from here.
Change them only together with a regenerated fixture.
"""
import os

# Backend pinning MUST precede any jax import (fixtures are compared on CPU).
os.environ.setdefault("JAX_PLATFORMS", "cpu")

import argparse
import subprocess
import sys

import numpy as np
import yaml

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from generate_body_mechanics_parity_fixture import _leaf_name, jaxpr_shas  # noqa: E402

OUT_REL = os.path.join("tests", "env", "fixtures", "bush_fire_clearance_parity",
                       "pre_change_resets.npz")

_LVL05 = os.path.join("configs", "environment", "experiment", "basic",
                      "05-campfire_thermal_10x10.yaml")
# world -> (config path relative to the source root, in-memory overrides)
WORLDS = {
    "lvl05": (_LVL05, {}),
    "lvl05_d3": (_LVL05, {"thermal.food_min_fire_distance": 4}),
    "lvl04": (os.path.join("configs", "environment", "experiment", "basic",
                           "04-jump_attack_10x10.yaml"), {}),
    "default": (os.path.join("configs", "environment", "default.yaml"), {}),
}
SEEDS = tuple(range(64))
JAXPR_FNS = ("jax_reset", "jax_step")


def load_world(load_env_config, load_env_params, root, world):
    """Resolve one world from `root` and apply its in-memory overrides."""
    rel, overrides = WORLDS[world]
    cfg = load_env_config(os.path.join(root, rel))
    for k, v in overrides.items():
        cfg.set(k, v)
    return cfg, load_env_params(cfg)


def reset_leaves(jax, core, params, seeds=SEEDS):
    """{leaf_name: array stacked over seeds} of `jax_reset(params, PRNGKey(seed))`."""
    reset = jax.jit(core.jax_reset)
    flats = [jax.tree_util.tree_flatten_with_path(reset(params, jax.random.PRNGKey(s)))[0]
             for s in seeds]
    return {_leaf_name(path): np.stack([np.asarray(f[i][1]) for f in flats])
            for i, (path, _) in enumerate(flats[0])}


def capture(src_root):
    sys.path.insert(0, src_root)
    import jax
    import jax.numpy as jnp
    from src.environment.config_loader import load_env_config, load_env_params
    import src.environment.core as core
    assert os.path.abspath(core.__file__).startswith(src_root + os.sep), (
        f"src imported from {core.__file__}, not from --src-root {src_root}")

    arrays = {}
    for world in WORLDS:
        cfg, params = load_world(load_env_config, load_env_params, src_root, world)
        arrays[f"{world}._config_yaml"] = np.array(
            yaml.safe_dump(cfg.to_dict(), sort_keys=True, default_flow_style=False))
        state0 = core.jax_reset(params, jax.random.PRNGKey(0))
        shas = jaxpr_shas(jax, jnp, core, params, state0)
        for fn in JAXPR_FNS:
            arrays[f"{world}._jaxpr_sha.{fn}"] = np.array(shas[fn])
        for leaf, v in reset_leaves(jax, core, params).items():
            arrays[f"{world}.reset.{leaf}"] = v
    return arrays


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src-root", required=True,
                    help="Repo root to import src/ and read configs/ from: a worktree of "
                         "the pre-change commit. Required on purpose; the working tree is "
                         "NOT a valid reference.")
    args = ap.parse_args()
    src_root = os.path.abspath(args.src_root)
    sha = subprocess.check_output(["git", "-C", src_root, "rev-parse", "HEAD"],
                                  text=True).strip()
    dirty = subprocess.check_output(["git", "-C", src_root, "status", "--porcelain",
                                     "--", "src", "configs"], text=True).strip()
    if dirty:
        raise SystemExit(f"--src-root has uncommitted src/configs changes:\n{dirty}")

    arrays = capture(src_root)
    out = os.path.join(_ROOT, OUT_REL)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    np.savez_compressed(out, _provenance_sha=np.array(sha), **arrays)
    print(f"wrote {out}")
    print(f"  source tree : {src_root}")
    print(f"  HEAD        : {sha}")
    for world in WORLDS:
        n = sum(1 for k in arrays if k.startswith(f"{world}.reset."))
        print(f"  {world}: {n} reset leaves x {len(SEEDS)} seeds")
        for fn in JAXPR_FNS:
            print(f"    jaxpr sha1 {fn:9s}: {arrays[f'{world}._jaxpr_sha.{fn}']}")


if __name__ == "__main__":
    main()
