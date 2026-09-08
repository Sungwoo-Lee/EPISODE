"""Generate the thermal-parity reference fixtures (Stage 0 of the temperature plan).

Run BEFORE any thermal code exists, on the current tip. Captures observation,
reward and drive for every config that loads and runs, so that each later stage's
"byte-identical" claim can be CHECKED rather than asserted.

Why a second fixture set exists: `scripts/fixtures/generate_parity_fixtures.py`
(and `tests/env/test_unified_parity.py`) record state fields and a handful of
info keys only — the observation there is a literal placeholder
(`obs_list.append(jnp.zeros(1))`), and reward and drive are not captured at all.
See `docs/develop/active/thermal/IMPLEMENTATION_PLAN.md`, finding F5.

Captured per config, over reset + 100 steps:
  - the full observation with `apply_noise=False`
  - the full observation with noise on
  - the scalar `reward`
  - `calculate_drive(...)` before and after each step
  - `info['termination_reason']`
  - `sum(get_observation_breakdown(params).values())`
  - `state.key` (integers — the PRNG-stream tripwire)
  - all three sampled-property arrays (animal / res / obs), which are what the
    one-ulp exemption in `tests/env/test_thermal_parity.py` is keyed on
  - every entity position array (`res_pos`, `animal_pos`, `obs_pos`)

`config_slug` and `collect_configs` are the same as in
`scripts/fixtures/generate_parity_fixtures.py` (:36-42 and :44-52) so this
fixture set covers exactly the same config set as the existing gate.

Saves one .npz per config under tests/env/fixtures/thermal_parity/<slug>.npz.

Usage:
    /home/vncuser/miniconda3/envs/grid_world_pain/bin/python \
        scripts/fixtures/generate_thermal_parity_fixtures.py
"""
import os

# Backend pinning MUST precede any jax import: fixtures generated on GPU and
# compared on CPU differ in the last bits and the gate becomes noise.
# Same form as tests/test_trajectory_collection.py:66.
os.environ.setdefault("JAX_PLATFORMS", "cpu")

import sys
import re
import glob
import traceback

import numpy as np
import jax
import jax.numpy as jnp
import yaml

# Ensure project root on path
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, _ROOT)

from src.utils.config import Config
from src.environment.config_loader import load_env_params
from src.environment.core import jax_reset, jax_step, calculate_drive
from src.environment.sensor import get_observation, get_observation_breakdown

ACTIONS = [0, 1, 2, 3, 4] * 20  # 100 steps
SEED = 0

FIXTURE_DIR = os.path.join(_ROOT, "tests", "env", "fixtures", "thermal_parity")
os.makedirs(FIXTURE_DIR, exist_ok=True)


def config_slug(config_path: str) -> str:
    """Convert a config path to a filesystem-safe slug.

    Verbatim from scripts/fixtures/generate_parity_fixtures.py:36-42 — the two
    fixture sets must key on identical slugs.
    """
    rel = os.path.relpath(config_path, _ROOT)
    slug = re.sub(r'[/\\]', '__', rel)
    slug = re.sub(r'\.yaml$', '', slug)
    slug = re.sub(r'[^A-Za-z0-9_.-]', '_', slug)
    return slug


def collect_configs():
    """Verbatim from scripts/fixtures/generate_parity_fixtures.py:44-52."""
    configs = []
    configs += sorted(glob.glob(os.path.join(_ROOT, "configs", "environment", "experiment", "**", "*.yaml"), recursive=True))
    configs += sorted(glob.glob(os.path.join(_ROOT, "configs", "continual", "**", "*.yaml"), recursive=True))
    configs += sorted(glob.glob(os.path.join(_ROOT, "configs", "verification", "**", "*.yaml"), recursive=True))
    env_default = os.path.join(_ROOT, "configs", "environment", "default.yaml")
    if env_default not in configs:
        configs.append(env_default)
    return configs


# ── capture ───────────────────────────────────────────────────────────────────

# Per-state arrays: recorded for the reset state (index 0) and after each of the
# 100 steps (indices 1..100), so each stacks to shape [101, ...].
_STATE_ARRAYS = (
    "key",
    "animal_property_sampled",
    "res_property_sampled",
    "obs_property_sampled",
    "res_pos",
    "animal_pos",
    "obs_pos",
)


def _capture_state(state, params) -> dict:
    """Everything the adjudication rule reads out of one state."""
    out = {name: np.array(getattr(state, name)) for name in _STATE_ARRAYS}
    out["obs_clean"] = np.array(get_observation(state, params, apply_noise=False))
    out["obs_noisy"] = np.array(get_observation(state, params, apply_noise=True))
    out["drive"] = np.array(calculate_drive(state.satiation, state.injury_level, params))
    return out


def run_episode(params, key):
    """Reset + 100 steps.

    Returns (per_state, per_step) where `per_state` is a list of 101 dicts (the
    reset state and each post-step state) and `per_step` is a list of 100 dicts
    (one per transition).
    """
    state = jax_reset(params, key)
    per_state = [_capture_state(state, params)]
    per_step = []
    for action in ACTIONS:
        state, reward, done, info = jax_step(state, action, params)
        per_state.append(_capture_state(state, params))
        per_step.append({
            "reward": np.array(reward),
            "done": np.array(done),
            "termination_reason": np.array(info["termination_reason"]),
        })
    return per_state, per_step


def generate_fixture(config_path: str):
    slug = config_slug(config_path)
    out_path = os.path.join(FIXTURE_DIR, slug + ".npz")

    try:
        with open(config_path) as f:
            config_dict = yaml.safe_load(f)
        config = Config(config_dict)
        params = load_env_params(config)
    except Exception as e:
        print(f"  SKIP (load error): {config_path}\n    {e}")
        return False, "load_error"

    try:
        key = jax.random.PRNGKey(SEED)
        per_state, per_step = run_episode(params, key)
    except Exception:
        print(f"  SKIP (run error): {config_path}\n    {traceback.format_exc()}")
        return False, "run_error"

    npz_data = {}
    # Per-state fields stack over the 101 states; every field has a fixed shape
    # across steps, so a single stacked array per field keeps the .npz small and
    # the comparison in the test a single call per field.
    for name in per_state[0]:
        npz_data[name] = np.stack([s[name] for s in per_state])
    # Per-transition fields stack over the 100 steps.
    for name in per_step[0]:
        npz_data[name] = np.stack([s[name] for s in per_step])

    # drive_before[i] / drive_after[i] are the drive on either side of step i.
    # Stored explicitly (rather than left implicit in the stacked `drive`) so the
    # test reads the plan's wording directly.
    npz_data["drive_before"] = npz_data["drive"][:-1]
    npz_data["drive_after"] = npz_data["drive"][1:]

    breakdown = get_observation_breakdown(params)
    npz_data["obs_breakdown_total"] = np.array(sum(breakdown.values()))
    npz_data["obs_dim"] = np.array(npz_data["obs_clean"].shape[-1])
    npz_data["n_steps"] = np.array(len(ACTIONS))
    npz_data["seed"] = np.array(SEED)

    np.savez_compressed(out_path, **npz_data)
    return True, "ok"


def main():
    configs = collect_configs()
    print(f"collect_configs() returned {len(configs)} configs")

    ok_count = 0
    load_errors = 0
    run_errors = 0
    for i, cfg in enumerate(configs):
        rel = os.path.relpath(cfg, _ROOT)
        print(f"[{i+1}/{len(configs)}] {rel}", end=" ... ", flush=True)
        success, reason = generate_fixture(cfg)
        if success:
            print("OK")
            ok_count += 1
        else:
            print(f"SKIPPED ({reason})")
            if reason == "load_error":
                load_errors += 1
            else:
                run_errors += 1

    # These two numbers do different jobs and must not be conflated: the first is
    # the set the gate walks, the second is the set it can actually adjudicate.
    print(f"\nconfigs walked:   {len(configs)}")
    print(f"fixtures written: {ok_count}")
    print(f"skipped:          {load_errors} load errors, {run_errors} run errors")
    print(f"Fixture dir: {FIXTURE_DIR}")


if __name__ == "__main__":
    main()
