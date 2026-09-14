"""Every maintained world with a concealing bush must also block animals from it.

WHAT THIS PINS
    On 2026-09-14 the bush became a physical refuge: `blocks_animals: true` in
    `configs/environment/default.yaml` (A1 of BUSH_REFUGE_AND_LOCATION_DEPENDENT_RECOVERY).
    An animal can no longer step onto a bush; the agent still can. That asymmetry is
    the feature.

WHY A TEST, AND WHY THIS SHAPE
    The loader reads the key with a FALLBACK — `o.get('blocks_animals', False)`
    (`config_loader.py:1851`), kept as a deliberate dated exception to the project's
    no-fallback-defaults rule (see CONFIG_CRITICAL_SETTINGS.md). Deep-merge replaces
    LISTS wholesale (CONFIG_GUIDE.md §1), so any config that redeclares its own
    `obstacles:` list and omits the key silently gets `false` — it does NOT inherit the
    base's `true`, and nothing warns. A config can therefore reverse a project-wide
    decision by omission, and the YAML text looks perfectly ordinary.

    That is why this test asserts on RESOLVED `EnvParams`, not on the YAML. A grep over
    config text re-derives the answer from exactly the source that hides the problem and
    cannot see a list-replace revert. `test_bush_blocks_animals.py` is a good test of the
    MECHANISM but builds its worlds from inline YAML, so it asserts nothing about the
    configs actually shipped — this module covers that gap.

SCOPE
    The maintained environment worlds: `configs/environment/default.yaml` plus every
    `configs/environment/experiment/basic/*.yaml`. The directory is ENUMERATED, never
    hard-coded, so a newly added `basic/` world is covered the day it lands.

    DELIBERATELY OUT OF SCOPE: nine further maintained worlds stay permeable ON PURPOSE —
    `configs/verification/observability_gates_S{1..4}.yaml` (verification instruments:
    changing their world changes what they verify) and
    `configs/continual/nmn_double_return_stages/0{1..5}_*.yaml` (a curriculum tied to a
    specific study). That decision is recorded in CONFIG_CRITICAL_SETTINGS.md's
    2026-09-14 entry. If you widen this test to them, revisit that entry first — do not
    simply make them pass.
"""
import glob
import os
import sys

os.environ.setdefault("JAX_PLATFORMS", "cpu")

import pytest

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, _ROOT)

from src.environment.config_loader import load_env_config, load_env_params


def _maintained_worlds():
    """Enumerate, never hard-code — a new basic/ world is covered automatically."""
    paths = [os.path.join(_ROOT, "configs", "environment", "default.yaml")]
    paths += sorted(glob.glob(os.path.join(
        _ROOT, "configs", "environment", "experiment", "basic", "*.yaml")))
    return paths


_WORLDS = _maintained_worlds()


def test_the_maintained_world_set_is_not_empty():
    """Guards the parametrize below: a bad glob would make every test vanish, and a
    suite that silently collects nothing is indistinguishable from one that passes."""
    assert len(_WORLDS) >= 8, f"expected at least 8 maintained worlds, found {_WORLDS}"


@pytest.mark.parametrize("cfg_path", _WORLDS, ids=lambda p: os.path.relpath(p, _ROOT))
def test_concealing_bush_also_blocks_animals(cfg_path):
    """Resolved through the real loader — `extends:` and all — then asserted on arrays.

    A world may have no concealing obstacle; that passes VACUOUSLY and is correct.
    `basic/00-static_predator_5x5.yaml` is exactly that case: it declares
    `obstacles: []` (an explicitly empty list, the §1 idiom for "suppress the base's
    scene"), so it resolves to n_obs = 0. Its pass is NOT coverage — do not read the
    green tick as evidence that anything about bushes was checked there.
    """
    params = load_env_params(load_env_config(cfg_path))
    hides = params.obs_hides_agent
    blocks = params.obs_blocks_animals

    assert hides.shape == blocks.shape, (
        f"{cfg_path}: obs_hides_agent {hides.shape} and obs_blocks_animals "
        f"{blocks.shape} must be the same per-obstacle shape"
    )

    permeable = hides & ~blocks
    assert not bool(permeable.any()), (
        f"{os.path.relpath(cfg_path, _ROOT)}: {int(permeable.sum())} of "
        f"{int(hides.sum())} concealing obstacle slot(s) have hides_agent=True but "
        f"blocks_animals=False — a bush an animal can still walk into.\n"
        f"This is almost certainly a LIST-REPLACE revert: the config redeclares its own "
        f"`obstacles:` list and omits `blocks_animals`, so it silently got the loader "
        f"fallback False instead of inheriting the base's True "
        f"(CONFIG_GUIDE.md §1; config_loader.py:1851).\n"
        f"Fix: add `blocks_animals: true` to the bush entry in that file."
    )


def test_at_least_one_maintained_world_actually_has_a_blocking_bush():
    """Stops the whole module passing for the wrong reason.

    Every assertion above is satisfied by a world with NO obstacles, so if the bush were
    deleted from every config — or the loader stopped reading `hides_agent` at all —
    this suite would go green while testing nothing. At least one maintained world must
    really carry a bush that really blocks.
    """
    total_blocking_bushes = 0
    for cfg_path in _WORLDS:
        params = load_env_params(load_env_config(cfg_path))
        total_blocking_bushes += int((params.obs_hides_agent & params.obs_blocks_animals).sum())
    assert total_blocking_bushes > 0, (
        "No maintained world has a single obstacle slot with hides_agent=True AND "
        "blocks_animals=True. Either the bush was removed from every world, or the "
        "loader stopped reading these keys — in both cases the tests above are vacuous."
    )
