"""Generate the pre-change rollout fixture for the water / thirst plan.

**What this fixture is for.** `docs/develop/active/thirst/THIRST_WATER_PLAN.md` adds a
pond and a hydration axis behind one gate, `water.enabled`. The claim to defend is that
every world with the gate off behaves exactly as the pre-change code did: same random
numbers, same observations (clean and noisy), same rewards, same termination codes, same
jaxprs. This script records that pre-change behaviour; `tests/env/test_water_parity.py`
holds HEAD to it with `np.array_equal` and no tolerance, plus jaxpr-SHA equality.

**Worlds** (resolved through `load_env_config` -> `load_env_params`, as the trainer does):
`configs/environment/default.yaml`, the ladder rungs `basic/00` .. `basic/05`, and the
noise rung under its PRE-change name `basic/06-sensory_noise_10x10.yaml` (the plan renames
it to 07 and re-parents it onto the new pond world; the test proves that 07 with water
forced off equals this recording).

**Two variants per world.**

- `<world>`: the world as shipped. Seeds 0..15 x 300 auto-resetting steps, the rollout
  loop, action rule, seeds and step budget of `generate_body_mechanics_parity_fixture.py`
  (imported, not copied: `rollout_world`, `jaxpr_shas`, `_leaf_name`).
- `<world>__trunc`: the same world with `environment.max_steps` set to `TRUNC_MAX_STEPS`
  IN MEMORY. Every shipped world has `max_steps: 500`, and the shared random policy never
  survives that long (measured: 0 step-limit endings in 16 seeds x 2,000 steps), so the
  shipped variant alone can never exercise termination code 1 (step limit) or the
  truncation merge. The short-clock variant does; it is recorded and replayed identically,
  so it is ground truth for the same code path, not a different claim.

**Records per step** (per variant): every `EnvState` leaf (reset states included),
`reward`, `done`, every `info` entry, the observation `get_observation(state, params)`
(noisy when the world's perceptual noise is on) and, for noise-on worlds only, the clean
observation `get_observation(state, params, apply_noise=False)` as `obs_clean` (for a
noise-off world the two are the same array, and the test asserts that instead of storing
it twice). Per shipped variant: the `jax_step` / `jax_reset` / `update_body` jaxpr SHA-1s
and the resolved config as canonical YAML.

**Termination-code count table.** Printed, stored per variant as `_codes` in the npz, and
written into the fixture README. The test holds each world to a HARD-CODED expected set
(plan §T1, reviewer M4) — never one derived from this table, which would be circular.

**It must be generated from code that predates the change**, or it proves nothing.
`--src-root` is REQUIRED (no default) and refused if it has uncommitted `src/`/`configs/`
changes. Point it at a detached worktree of the pre-change commit:

    git worktree add --detach /tmp/gwp_water_baseline <pre-change SHA>
    JAX_PLATFORMS=cpu /home/vncuser/miniconda3/envs/grid_world_pain/bin/python \\
        scripts/fixtures/generate_water_parity_fixture.py \\
        --src-root /tmp/gwp_water_baseline
    git worktree remove /tmp/gwp_water_baseline

`--src-root` supplies BOTH `src/` and `configs/`, so the captured worlds are entirely that
commit's; its SHA is stamped as `_provenance_sha` and into the README. Output always goes
to THIS checkout's `tests/env/fixtures/water_parity/`.
"""
import os

# Backend pinning MUST precede any jax import (fixtures are compared on CPU).
os.environ.setdefault("JAX_PLATFORMS", "cpu")

import argparse
import copy
import subprocess
import sys

import numpy as np
import yaml

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, _HERE)
from generate_body_mechanics_parity_fixture import (  # noqa: E402  (one rollout loop)
    MAX_T, SEEDS, _leaf_name, jaxpr_shas, rollout_world)

OUT_DIR_REL = os.path.join("tests", "env", "fixtures", "water_parity")
OUT_REL = os.path.join(OUT_DIR_REL, "pre_change_rollouts.npz")
README_REL = os.path.join(OUT_DIR_REL, "README.md")

_BASIC = os.path.join("configs", "environment", "experiment", "basic")
WORLDS = {
    "default": os.path.join("configs", "environment", "default.yaml"),
    "lvl00": os.path.join(_BASIC, "00-static_predator_5x5.yaml"),
    "lvl01": os.path.join(_BASIC, "01-slow_predator_5x5.yaml"),
    "lvl02": os.path.join(_BASIC, "02-predator_and_rabbit_10x10.yaml"),
    "lvl03": os.path.join(_BASIC, "03-random_init_10x10.yaml"),
    "lvl04": os.path.join(_BASIC, "04-jump_attack_10x10.yaml"),
    "lvl05": os.path.join(_BASIC, "05-campfire_thermal_10x10.yaml"),
    # The noise rung under its PRE-change name (renamed to 07 by the plan).
    "noise06": os.path.join(_BASIC, "06-sensory_noise_10x10.yaml"),
}

TRUNC_SUFFIX = "__trunc"
TRUNC_MAX_STEPS = 30     # short clock so code 1 (step limit) and the truncation merge occur
TRUNC_SEEDS = tuple(range(8))
TRUNC_MAX_T = 150


def variants():
    """(variant name, world name, max_steps override or None, seeds, max_t)."""
    out = []
    for w in WORLDS:
        out.append((w, w, None, SEEDS, MAX_T))
        out.append((w + TRUNC_SUFFIX, w, TRUNC_MAX_STEPS, TRUNC_SEEDS, TRUNC_MAX_T))
    return out


def world_dict(load_env_config, root, world, max_steps=None):
    """The world resolved as the trainer does, optionally with max_steps overridden."""
    d = copy.deepcopy(load_env_config(os.path.join(root, WORLDS[world])).to_dict())
    if max_steps is not None:
        d["environment"]["max_steps"] = int(max_steps)
    return d


def clean_obs(jax, get_observation, params, reset_state, arrays, seed):
    """Clean observations rebuilt from the recorded post-step leaves.

    The state is re-assembled with the reset state's treedef and the recorded leaves (in
    `tree_flatten_with_path` order, which is how `rollout_world` keyed them), so this
    adds no second copy of the rollout loop.
    """
    flat, treedef = jax.tree_util.tree_flatten_with_path(reset_state)
    names = [_leaf_name(p) for p, _ in flat]
    cols = [arrays[f"s{seed}.state.{n}"] for n in names]
    out = []
    for t in range(cols[0].shape[0]):
        st = jax.tree_util.tree_unflatten(treedef, [c[t] for c in cols])
        out.append(np.asarray(get_observation(st, params, apply_noise=False)))
    return np.stack(out)


def code_counts(arrays, seeds):
    counts = {}
    for s in seeds:
        r = arrays[f"s{s}.info.termination_reason"]
        for c, n in zip(*np.unique(r, return_counts=True)):
            counts[int(c)] = counts.get(int(c), 0) + int(n)
    return dict(sorted(counts.items()))


def roll_variant(jax, jnp, core, get_observation, params, seeds, max_t):
    """rollout_world plus obs_clean for noise-on worlds."""
    arrays = rollout_world(jax, jnp, core, get_observation, params, seeds=seeds, max_t=max_t)
    if params.perceptual_noise_enabled:
        state0 = core.jax_reset(params, jax.random.PRNGKey(0))
        for s in seeds:
            arrays[f"s{s}.obs_clean"] = clean_obs(jax, get_observation, params, state0,
                                                  arrays, s)
    return arrays


def capture(src_root):
    sys.path.insert(0, src_root)
    import jax
    import jax.numpy as jnp
    from src.environment.config_loader import load_env_config, load_env_params
    import src.environment.core as core
    from src.environment.sensor import get_observation
    from src.utils.config import Config
    assert os.path.abspath(core.__file__).startswith(src_root + os.sep), (
        f"src imported from {core.__file__}, not from --src-root {src_root}")

    arrays, counts = {}, {}
    for var, world, max_steps, seeds, max_t in variants():
        d = world_dict(load_env_config, src_root, world, max_steps)
        params = load_env_params(Config(copy.deepcopy(d)))
        w = roll_variant(jax, jnp, core, get_observation, params, seeds, max_t)
        counts[var] = code_counts(w, seeds)
        arrays[f"{var}._codes"] = np.array(sorted(counts[var].items()), dtype=np.int64)
        if max_steps is None:
            arrays[f"{var}._config_yaml"] = np.array(
                yaml.safe_dump(d, sort_keys=True, default_flow_style=False))
            state0 = core.jax_reset(params, jax.random.PRNGKey(0))
            for fn, h in jaxpr_shas(jax, jnp, core, params, state0).items():
                arrays[f"{var}._jaxpr_sha.{fn}"] = np.array(h)
        for k, v in w.items():
            arrays[f"{var}.{k}"] = v
        print(f"  {var}: codes {counts[var]}", flush=True)
    return arrays, counts


def write_readme(path, sha, src_root, counts):
    lines = [
        "# Water parity fixture (pre-change rollouts)",
        "",
        "Ground truth for `tests/env/test_water_parity.py` (THIRST_WATER_PLAN §T1): every",
        "world with `water.enabled: false` must replay these arrays byte for byte.",
        "",
        f"- **Source commit**: `{sha}` (a detached worktree of the pre-change commit)",
        "- **Command**: `JAX_PLATFORMS=cpu /home/vncuser/miniconda3/envs/grid_world_pain/bin/python "
        "scripts/fixtures/generate_water_parity_fixture.py --src-root <worktree of the SHA above>`",
        f"- **Source tree used**: `{src_root}`",
        f"- **Variants**: each world as shipped (seeds 0-{len(SEEDS) - 1} x {MAX_T} steps), and "
        f"`<world>{TRUNC_SUFFIX}` with `environment.max_steps: {TRUNC_MAX_STEPS}` in memory "
        f"(seeds 0-{len(TRUNC_SEEDS) - 1} x {TRUNC_MAX_T} steps) so the step-limit ending "
        "(code 1) is exercised. See the generator's docstring.",
        "",
        "## Termination-code counts (steps carrying each code)",
        "",
        "Codes: 0 alive, 1 step limit, 2 starvation, 3 over-eating, 4 injury, 5 thermal.",
        "",
        "| Variant | " + " | ".join(f"code {c}" for c in range(6)) + " |",
        "|---|" + "---|" * 6,
    ]
    for var, c in counts.items():
        lines.append(f"| `{var}` | " + " | ".join(str(c.get(k, 0)) for k in range(6)) + " |")
    lines += ["", "Do not regenerate from a post-change tree: it would compare the code with "
              "itself and prove nothing.", ""]
    with open(path, "w") as f:
        f.write("\n".join(lines))


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

    arrays, counts = capture(src_root)
    out = os.path.join(_ROOT, OUT_REL)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    np.savez_compressed(out, _provenance_sha=np.array(sha), **arrays)
    write_readme(os.path.join(_ROOT, README_REL), sha, src_root, counts)
    print(f"wrote {out}")
    print(f"  source tree : {src_root}")
    print(f"  HEAD        : {sha}")
    for var in WORLDS:
        for fn in ("jax_step", "jax_reset", "update_body"):
            print(f"    {var} jaxpr sha1 {fn:11s}: {arrays[f'{var}._jaxpr_sha.{fn}']}")


if __name__ == "__main__":
    main()
