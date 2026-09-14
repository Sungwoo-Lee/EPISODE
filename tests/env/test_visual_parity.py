"""Visual-obs byte-parity gate (CP0/CP1 — v3.0 configurable visual properties).

Parametrized over 7 configs:
  - configs/environment/default.yaml
  - configs/environment/experiment/basic/{00-forage,01-slowPred,02-fastPred,03-multiPred,04-keenPred}.yaml
  - configs/environment/experiment/archive/hypervigilance/08-singlePredRabbit_disengage.yaml

For each config: reset from seed 0, run 1000 steps, extract the Visual slice via
get_observation_breakdown, assert BYTE-IDENTICAL to the pinned pre-change fixture at
tests/env/fixtures/visual_parity/<slug>.npz.

Fixtures were captured on the PRE-CHANGE commit (before any code change in this plan),
so byte-equality proves that the refactored sensor produces the same visual observations
as the old hard-coded one-hot implementation. These fixtures must NOT be regenerated
after the refactor.

Legacy test (kept): test_visual_channel_layout — asserts predator default row is one_hot(5),
neutral default row is one_hot(7). This still holds because the defaults are the one-hots
of those channels at V=8.

Usage:
  # Run parity gate (strict byte-equality against pinned fixtures):
  pytest tests/env/test_visual_parity.py -q

  # Regenerate fixtures on the pre-change commit ONLY (before any code change):
  pytest tests/env/test_visual_parity.py --gen-fixtures
"""
import glob
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

# ── Frozen (pinned pre-change) worlds ─────────────────────────────────────────
# THIS GATE PINS A PAST REFACTOR, NOT THE CURRENT WORLD.
#
# The fixtures in tests/env/fixtures/visual_parity/ were captured before the
# DIRECTIONAL_SENSORS sensor rewrite; this module's docstring says in so many words
# that they "must NOT be regenerated after the refactor". They are evidence about
# code that shipped months ago.
#
# On 2026-09-14 the bush gained `blocks_animals: true` (A1 of
# BUSH_REFUGE_AND_LOCATION_DEPENDENT_RECOVERY), a deliberate change to the LIVE
# world: an animal can no longer enter a bush, so animal trajectories — and every
# observation downstream of them — moved. Three configs here went red.
#
# Re-baselining would have destroyed the refactor evidence, so the WORLD is frozen
# instead of the fixture: these three configs are read from pinned pre-change copies
# under tests/env/fixtures/frozen_parity_worlds/ (see its README). Every OTHER config
# in the list below still reads the live tree, deliberately.
#
# CONTRAST — do not "harmonise" these: tests/env/fixtures/thermal_parity/ reads the
# LIVE configs on purpose, because it tracks the CURRENT world and going red on an
# intended behaviour change is its loudness function. Four fixture families, two
# jobs. A1 regenerated thermal_parity's affected fixture AND froze these worlds;
# both were correct.
_FROZEN_DIR = os.path.join(_ROOT, "tests", "env", "fixtures", "frozen_parity_worlds")
_FROZEN = {
    "configs/environment/default.yaml":
        os.path.join(_FROZEN_DIR, "environment__default.yaml"),
    "configs/environment/experiment/basic/01-slow_predator_5x5.yaml":
        os.path.join(_FROZEN_DIR, "environment__experiment__basic__01-slow_predator_5x5.yaml"),
    "configs/environment/experiment/basic/02-predator_and_rabbit_10x10.yaml":
        os.path.join(_FROZEN_DIR, "environment__experiment__basic__02-predator_and_rabbit_10x10.yaml"),
}
# The fixture filename is derived from the config PATH, so repointing a config at its
# frozen copy would change its slug, make `_fixture_path` miss, and send the test down
# the `not os.path.exists(fp)` branch — which GENERATES a fixture. That would silently
# re-baseline the very thing the freeze exists to protect. This map pins each frozen
# config back to its ORIGINAL slug so the existing fixture is still the one compared.
_SLUG_OVERRIDE = {v: "configs__" + k[len("configs/"):].replace("/", "__")[:-len(".yaml")]
                  for k, v in _FROZEN.items()}


def _assert_frozen_map_is_sound():
    """Fail at IMPORT if the frozen-world wiring is wrong, in either direction.

    The keys of `_FROZEN` are free strings that nothing checks against the filesystem —
    they exist only to derive the slug. So a typo in a KEY (`defualt` for `default`)
    would silently produce a slug with no fixture behind it. Paired with a
    generate-on-missing branch that is a SILENT RE-BASELINE reported as green: the gate
    would manufacture a new "pre-change" artefact from post-change code and pass.

    KNOWN_BUGS row 156 records exactly this hazard, fixed once in
    `test_extero_noc_parity.py` and naming THIS module as the unfixed sibling. Both
    halves of the recipe are applied: the generate branch below is now gated on
    `--gen-fixtures` alone, and this function closes the typo path that fed it.

    Two directions, because each catches what the other cannot:
      1. every override VALUE maps to a fixture that exists -> a bad key is caught;
      2. every config under _FROZEN_DIR has an override      -> a frozen world added
         to the directory but never wired into `_FROZEN` is caught, which would
         otherwise sit unused while its live counterpart was still being tested.
    """
    for frozen_path, slug in _SLUG_OVERRIDE.items():
        fp = os.path.join(_FIXTURE_DIR, f"{slug}.npz")
        if not os.path.exists(fp):
            raise AssertionError(
                f"Frozen-world wiring is broken: {os.path.basename(frozen_path)} maps to "
                f"slug {slug!r}, but no fixture exists at {fp}.\n"
                f"The _FROZEN key that derives this slug is almost certainly misspelt — it "
                f"must be the ORIGINAL repo-relative config path, e.g. "
                f"'configs/environment/default.yaml'. Fix the key; do NOT generate a "
                f"fixture to match it."
            )
        if not os.path.exists(frozen_path):
            raise AssertionError(
                f"Frozen-world wiring is broken: _FROZEN points at {frozen_path}, "
                f"which does not exist."
            )
    _wired = {os.path.abspath(v) for v in _FROZEN.values()}
    for f in sorted(glob.glob(os.path.join(_FROZEN_DIR, "*.yaml"))):
        if os.path.abspath(f) not in _wired:
            raise AssertionError(
                f"Frozen world {os.path.basename(f)} exists under {_FROZEN_DIR} but is not "
                f"wired into _FROZEN, so its live counterpart is still being tested and the "
                f"freeze is not in effect for it. Add it to _FROZEN or delete the file."
            )


_assert_frozen_map_is_sound()

# Multi-config parametrize list: (slug_label, config_path)
_PARITY_CONFIGS = [
    ("default",         _FROZEN["configs/environment/default.yaml"]),
    # 2026-08-26: the five entries here previously named `00-forage_5x5`,
    # `01-slowPred_5x5`, `02-fastPred_8x8`, `03-multiPred_10x10`,
    # `04-keenPred_10x10` — files that no longer exist under any name. The
    # `basic/` curriculum was replaced, and because the gate below skips a
    # missing path rather than failing, FIVE OF SEVEN configs were silently not
    # being checked. Repointed at the live curriculum.
    ("00-static_predator_5x5", os.path.join(_ROOT, "configs", "environment", "experiment", "basic", "00-static_predator_5x5.yaml")),
    ("01-slow_predator_5x5",   _FROZEN["configs/environment/experiment/basic/01-slow_predator_5x5.yaml"]),
    ("02-predator_and_rabbit_10x10", _FROZEN["configs/environment/experiment/basic/02-predator_and_rabbit_10x10.yaml"]),
    ("03-random_init_10x10",   os.path.join(_ROOT, "configs", "environment", "experiment", "basic", "03-random_init_10x10.yaml")),
    ("04-jump_attack_10x10",   os.path.join(_ROOT, "configs", "environment", "experiment", "basic", "04-jump_attack_10x10.yaml")),
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
    # A frozen config keeps its ORIGINAL slug — see _SLUG_OVERRIDE above. Without
    # this, repointing at a frozen copy would look like "fixture missing" and the
    # gate would quietly generate a new one instead of comparing against the pinned
    # pre-change artefact.
    # `.get(...) or ...` would DEGRADE a missed override to a path-derived slug; the
    # import-time check above is what makes a miss impossible rather than silent.
    slug = _SLUG_OVERRIDE[config_path] if config_path in _SLUG_OVERRIDE else _config_slug(config_path)
    return os.path.join(_FIXTURE_DIR, f"{slug}.npz")


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
