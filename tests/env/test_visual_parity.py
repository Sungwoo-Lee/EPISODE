"""Visual-obs byte-parity gate (CP0/CP1 — v3.0 configurable visual properties).

Parametrized over 7 configs, every one of them read from the LIVE config tree:
  - configs/environment/default.yaml
  - configs/environment/experiment/basic/{00-static_predator_5x5,01-slow_predator_5x5,
    02-predator_and_rabbit_10x10,03-random_init_10x10,04-jump_attack_10x10}.yaml
  - configs/environment/experiment/archive/hypervigilance/08-singlePredRabbit_disengage.yaml

For each config: reset from seed 0, run 1000 steps, extract the Visual slice via
get_observation_breakdown, assert BYTE-IDENTICAL to the pinned fixture at
tests/env/fixtures/visual_parity/<slug>.npz.

2026-09-21 — WHAT THIS GATE PINS CHANGED. Until today three of the seven cases loaded
pre-resolved frozen copies of their config so the module could keep pinning a PAST
refactor (the pre-DIRECTIONAL_SENSORS visual sensor). Commit 47b1b8c3 showed what that
cost: it changed the default sensory settings, and those three cases stayed GREEN while
the live ones went red — a half-blind gate that reads as coverage. See the de-blinding
note below the imports. Every case now reads the live tree, and the goldens are a
CURRENT-world baseline: going red on an intended sensory change is the loudness function,
and a deliberate re-baseline (with its cause recorded) is the response.

Legacy test (kept): test_visual_channel_layout — asserts predator default row is one_hot(5),
neutral default row is one_hot(7). This still holds because the defaults are the one-hots
of those channels at V=8.

Usage:
  # Run parity gate (strict byte-equality against pinned fixtures):
  pytest tests/env/test_visual_parity.py -q

  # Regenerate fixtures on the pre-change commit ONLY (before any code change):
  pytest tests/env/test_visual_parity.py --gen-fixtures
"""
import os
import re
import sys
import warnings

import numpy as np
import pytest

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, _ROOT)

import jax

from src.utils.config import Config
from src.environment.config_loader import load_env_params, _resolve_extends
from src.environment.core import jax_reset, jax_step
from src.environment.sensor import get_observation, get_observation_breakdown

# ── Paths ─────────────────────────────────────────────────────────────────────

_FIXTURE_DIR = os.path.join(_ROOT, "tests", "env", "fixtures", "visual_parity")

# ── Live-world sourcing (de-blinded 2026-09-21) ───────────────────────────────
# EVERY case below reads the LIVE config tree. There are no exceptions, and reintroducing
# one is the bug this comment exists to prevent.
#
# The exception used to be deliberate, so here is why it was right and why it stopped
# being right. From 2026-09-15 to 2026-09-21 three cases (`default`, `basic/01`,
# `basic/02`) loaded PRE-RESOLVED copies under tests/env/fixtures/frozen_parity_worlds/.
# This module pinned a PAST refactor — the DIRECTIONAL_SENSORS visual-sensor rewrite — so
# when `blocks_animals: true` changed the live world on 2026-09-14, freezing the WORLD
# preserved that evidence where re-baselining the fixtures would have destroyed it.
#
# On 2026-09-21 commit 47b1b8c3 changed the DEFAULT sensory settings themselves
# (olfactory_grid_range 0 -> 1, visual_sensor_range 0 -> 2, visual_vector_size 8 -> 1,
# visual_value_mode sum -> clamp, blur off -> on). The three live cases went red. The three
# frozen ones stayed GREEN — still asserting byte-parity for a world that exists nowhere in
# the tree, because the pre-resolved copies had the old sensory block baked in. A gate that
# is green on half its cases purely by config provenance is worse than an absent one: it
# reads as coverage. Recorded in KNOWN_BUGS (test-gate-hygiene family).
#
# Resolution (user decision, 2026-09-21): source every case from the live tree, so all six
# maintained worlds track the real one. What this gate pins therefore CHANGES — it becomes
# a CURRENT-world gate like tests/env/test_thermal_parity.py, where going red on an
# intended sensory change is the loudness function rather than a defect.
#
# Slugs need no override any more: the live path of each de-blinded case derives exactly
# the slug its existing fixture already carries, so the comparison target is unchanged.

# Multi-config parametrize list: (slug_label, config_path)
# 2026-08-26: the five `basic/` entries here previously named `00-forage_5x5`,
# `01-slowPred_5x5`, `02-fastPred_8x8`, `03-multiPred_10x10`, `04-keenPred_10x10` — files
# that no longer exist under any name. The `basic/` curriculum was replaced, and because
# the gate then skipped a missing path rather than failing, FIVE OF SEVEN configs were
# silently not being checked. Repointed at the live curriculum.
_BASIC = os.path.join(_ROOT, "configs", "environment", "experiment", "basic")
_PARITY_CONFIGS = [
    ("default",                      os.path.join(_ROOT, "configs", "environment", "default.yaml")),
    ("00-static_predator_5x5",       os.path.join(_BASIC, "00-static_predator_5x5.yaml")),
    ("01-slow_predator_5x5",         os.path.join(_BASIC, "01-slow_predator_5x5.yaml")),
    ("02-predator_and_rabbit_10x10", os.path.join(_BASIC, "02-predator_and_rabbit_10x10.yaml")),
    ("03-random_init_10x10",         os.path.join(_BASIC, "03-random_init_10x10.yaml")),
    ("04-jump_attack_10x10",         os.path.join(_BASIC, "04-jump_attack_10x10.yaml")),
    # Self-contained archived world: it carries its OWN `sensory:` block (range 0, sum,
    # 8-wide vector) and no `extends:`, so 47b1b8c3 did not touch it and its fixture is
    # still the original pre-DIRECTIONAL_SENSORS artefact. Live path, not a frozen copy.
    ("08-singlePredRabbit_disengage", os.path.join(_ROOT, "configs", "environment", "experiment", "archive", "hypervigilance", "08-singlePredRabbit_disengage.yaml")),
]

# Legacy single-config parity (the original fixture used by pre-v3.0 test)
_LEGACY_PARITY_CFG = os.path.join(
    _ROOT, "configs", "experiment", "hypervigilance",
    "01-interoNocicept_sameProp.yaml"
)
_LEGACY_FIXTURE_PATH = os.path.join(
    _ROOT, "tests", "env", "fixtures", "visual_parity_ref.npz"
)

ACTIONS = ([0, 1, 2, 3, 4] * 200)  # 1000 steps


def _config_slug(config_path: str) -> str:
    """Convert config path to filesystem-safe slug."""
    rel = os.path.relpath(config_path, _ROOT)
    slug = re.sub(r'[/\\]', '__', rel)
    slug = re.sub(r'\.yaml$', '', slug)
    slug = re.sub(r'[^A-Za-z0-9_.-]', '_', slug)
    return slug


def _load_params(config_path: str):
    """Load env params (with extends: support)."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        cfg = _resolve_extends(config_path, frozenset())
        return load_env_params(cfg)


def _get_visual_slice(obs: np.ndarray, params) -> np.ndarray:
    """Extract the Visual sensor slice from a flattened observation vector."""
    breakdown = get_observation_breakdown(params)
    offset = 0
    for sensor_name, dim in breakdown.items():
        if sensor_name == "Visual":
            return obs[offset: offset + dim]
        offset += dim
    raise KeyError("'Visual' sensor not found in observation breakdown.")


def _run_episode(params, seed: int = 0) -> np.ndarray:
    """Reset + 1000 steps. Returns [1000, visual_dim] float32 array."""
    key = jax.random.PRNGKey(seed)
    state = jax_reset(params, key)
    visual_slices = []
    for action in ACTIONS:
        state, _, _, _ = jax_step(state, action, params)
        obs = np.array(get_observation(state, params, apply_noise=False))
        visual_slices.append(_get_visual_slice(obs, params))
    return np.stack(visual_slices, axis=0)  # [1000, visual_dim]


def _fixture_path(config_path: str) -> str:
    # One rule, no exceptions: the slug is derived from the config's own live path.
    # The override table that used to sit here existed only to keep a frozen COPY
    # pointing at the original's fixture; with the copies gone there is nothing to
    # override, and nothing that can silently point a case at the wrong artefact.
    return os.path.join(_FIXTURE_DIR, f"{_config_slug(config_path)}.npz")


def _generate_fixture(config_path: str, params) -> np.ndarray:
    """Generate and save a fixture. Must be called only on the PRE-CHANGE commit."""
    os.makedirs(_FIXTURE_DIR, exist_ok=True)
    fp = _fixture_path(config_path)
    visual_all = _run_episode(params)
    np.savez_compressed(fp, visual_all=visual_all)
    print(f"  Generated fixture: {fp}")
    return visual_all


# ── pytest option ─────────────────────────────────────────────────────────────

def pytest_addoption(parser):
    """Add --gen-fixtures option to pytest."""
    try:
        parser.addoption(
            "--gen-fixtures",
            action="store_true",
            default=False,
            help="Regenerate visual/extero-noc parity fixtures (pre-change commit only).",
        )
    except ValueError:
        pass  # option already registered by another conftest


# ── Multi-config byte-parity gate (CP1 — primary acceptance gate) ─────────────

@pytest.mark.parametrize("label,cfg_path", _PARITY_CONFIGS)
def test_visual_parity_byte_equal(label, cfg_path, request):
    """Visual sensor slice must be byte-identical to the pinned pre-change fixture."""
    if not os.path.exists(cfg_path):
        # Deliberately a FAILURE, not a skip: a silently-skipped parity config is
        # indistinguishable from a passing one, which is how five of these rotted
        # away unnoticed. If a config is legitimately retired, remove its entry.
        pytest.fail(f"Parity config listed but missing: {cfg_path}")

    params = _load_params(cfg_path)
    fp = _fixture_path(cfg_path)

    gen = request.config.getoption("--gen-fixtures", default=False)
    if gen:
        # The ONLY route to writing a fixture, and it is deliberate + explicit.
        ref = _generate_fixture(cfg_path, params)
    elif not os.path.exists(fp):
        # Deliberately a FAILURE, never a generate. Regenerating on absence means a
        # missing reference is recaptured from TODAY's code and then compared against
        # itself — a gate that reports green while testing nothing. KNOWN_BUGS row 156
        # records this hazard and the fix already applied to test_extero_noc_parity.py;
        # this is the sibling it names. `--gen-fixtures` remains the deliberate
        # re-baseline route, and it is only ever correct on a PRE-CHANGE commit.
        pytest.fail(
            f"[{label}] Pinned fixture missing: {fp}\n"
            f"Config read: {cfg_path}\n"
            f"NOT generating one — that would silently re-baseline this gate against "
            f"post-change code and report green. If the fixture was lost, restore it from "
            f"git. If this gate is being deliberately re-baselined, run with "
            f"--gen-fixtures on the pre-change commit."
        )
    else:
        ref = np.load(fp)["visual_all"]

    visual_new = _run_episode(params)

    assert visual_new.shape == ref.shape, (
        f"[{label}] Shape mismatch: got {visual_new.shape}, expected {ref.shape}"
    )
    np.testing.assert_array_equal(
        visual_new, ref,
        err_msg=(
            f"[{label}] Visual sensor slice differs from pinned pre-change fixture — "
            f"CP1 byte-parity regression. "
            f"First differing step: {np.where((visual_new != ref).any(axis=1))[0][:5]}"
        ),
    )


# ── Channel layout test (CP2) ─────────────────────────────────────────────────

def test_visual_channel_layout():
    """Predators default to one_hot(5), neutral animals to one_hot(7) at V=8 (CP2)."""
    cfg_path = os.path.join(
        _ROOT, "configs", "environment", "experiment", "archive",
        "hypervigilance", "08-singlePredRabbit_disengage.yaml"
    )
    if not os.path.exists(cfg_path):
        pytest.skip(f"Reference config not found: {cfg_path}")
    params = _load_params(cfg_path)
    # Verify params.animal_visual_channel encodes predator=5, neutral=7
    channels = list(params.animal_visual_channel)
    pred_channels = [channels[i] for i in params.predator_indices]
    neutral_channels = [channels[i] for i in params.neutral_indices]
    assert all(c == 5 for c in pred_channels), (
        f"Predator visual channels should all be 5, got {pred_channels}"
    )
    assert all(c == 7 for c in neutral_channels), (
        f"Neutral visual channels should all be 7, got {neutral_channels}"
    )
    # Also verify animal_visual_property rows: predator → one_hot(5), neutral → one_hot(7)
    import numpy as np
    vp = np.array(params.animal_visual_property)
    for i in params.predator_indices:
        expected = np.zeros(8)
        expected[5] = 1.0
        np.testing.assert_array_equal(
            vp[i], expected,
            err_msg=f"Predator at index {i}: animal_visual_property row should be one_hot(5)"
        )
    for i in params.neutral_indices:
        expected = np.zeros(8)
        expected[7] = 1.0
        np.testing.assert_array_equal(
            vp[i], expected,
            err_msg=f"Neutral at index {i}: animal_visual_property row should be one_hot(7)"
        )
