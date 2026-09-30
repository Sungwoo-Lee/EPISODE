"""Water off = today: every world without the pond behaves exactly as before the change.

**Plain-language summary.** `docs/develop/active/thirst/THIRST_WATER_PLAN.md` adds a pond
and a thirst (hydration) axis behind one switch, `water.enabled`. Every world that leaves
the switch off must be byte-for-byte the environment it was before the change: the same
random numbers, observations (clean and noisy), rewards, termination codes and traced
graphs. This test is the proof, three ways (plan §T1):

1. **Rollouts.** For `default.yaml` and ladder rungs 00-05, and for the noise rung, the
   recorded seeds are replayed and every array compared with `np.array_equal` (no
   tolerance) against rollouts recorded from a worktree of the pre-change commit
   (`tests/env/fixtures/water_parity/pre_change_rollouts.npz`, written by
   `scripts/fixtures/generate_water_parity_fixture.py`, whose rollout loop this test
   imports rather than copies). Each world is also replayed with a short step limit
   (the `__trunc` variant) so the step-limit ending is compared too.
2. **Graphs.** The `jax_step` / `jax_reset` / `update_body` jaxpr SHA-1s (params traced)
   are unchanged. That is only possible because every new `EnvParams` field is static
   and both new `EnvState` fields are `None` (an empty pytree) when water is off.
3. **Contrast.** The same world with water on changes the rollout AND all three
   jaxprs, so (1) and (2) cannot pass merely because water was never wired in.

The noise rung is recorded under its pre-change name `06-sensory_noise`. The plan
renames it to 07 and re-parents it onto the pond world; this test loads the renamed file
with `water.enabled` forced false IN MEMORY and holds it to the same recording, which is
the proof that the ladder rewire changed nothing but water.

Fails, never skips, on a missing fixture, config or provenance. CPU only (conftest).
"""
import copy
import hashlib
import os
import sys

import jax
import jax.numpy as jnp
import numpy as np
import pytest

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(_REPO, "scripts", "fixtures"))
import generate_water_parity_fixture as G  # noqa: E402
from generate_body_mechanics_parity_fixture import REST, jaxpr_shas  # noqa: E402

import src.environment.core as core  # noqa: E402
from src.environment.config_loader import load_env_config, load_env_params  # noqa: E402
from src.environment.sensor import get_observation  # noqa: E402
from src.utils.config import Config  # noqa: E402

FIXTURE = os.path.join(_REPO, G.OUT_REL)

# Where each recorded world lives in THIS checkout. The noise rung was recorded as
# basic/06-sensory_noise; after the ladder rename it is basic/07 (water forced off below).
_BASIC = os.path.join("configs", "environment", "experiment", "basic")
CURRENT_PATH = dict(G.WORLDS)

# Termination codes each world MUST show across its two variants, HARD-CODED (plan §T1,
# reviewer M4): deriving them from the fixture would be circular. 1 step limit,
# 2 starvation, 3 over-eating, 4 injury, 5 thermal. Code 3 is added to a world only
# where the C1 count table shows it (see the fixture README).
EXPECTED_CODES = {
    "default": {1, 2, 4},
    "lvl00": {1, 2, 4},
    "lvl01": {1, 2, 4},
    "lvl02": {1, 2, 4},
    "lvl03": {1, 2, 4},
    "lvl04": {1, 2, 4},
    "lvl05": {1, 2, 4, 5},
    "noise06": {1, 2, 4, 5},
}
assert set(EXPECTED_CODES) == set(G.WORLDS)

VARIANTS = G.variants()
VARIANT_IDS = [v[0] for v in VARIANTS]


@pytest.fixture(autouse=True)
def _release_compiled_programs():
    """Drop compiled programs after each test (the vm.max_map_count hazard, see
    tests/env/test_body_mechanics_parity.py)."""
    yield
    jax.clear_caches()


@pytest.fixture(scope="module")
def fx():
    assert os.path.isfile(FIXTURE), (
        f"water parity fixture missing: {FIXTURE}. Regenerate it from a PRE-change "
        "worktree (see the generator's docstring); never from this checkout.")
    data = np.load(FIXTURE)
    assert "_provenance_sha" in data.files, "fixture has no _provenance_sha"
    sha = str(data["_provenance_sha"])
    assert len(sha) == 40, f"bad provenance sha {sha!r}"
    return {k: data[k] for k in data.files}


def _world_dict(world, max_steps=None):
    """The world as resolved at HEAD; water forced off for the noise rung."""
    path = os.path.join(_REPO, CURRENT_PATH[world])
    assert os.path.isfile(path), f"world config missing: {path}"
    d = copy.deepcopy(load_env_config(path).to_dict())
    if max_steps is not None:
        d["environment"]["max_steps"] = int(max_steps)
    if d.get("water", {}).get("enabled"):
        assert world == "noise06", f"{world} unexpectedly has water on"
        d["water"]["enabled"] = False
        print(f"[parity] {world}: water.enabled True -> False (in memory)")
    return d


def _params(d):
    return load_env_params(Config(copy.deepcopy(d)))


def _variant(name):
    for v in VARIANTS:
        if v[0] == name:
            return v
    raise KeyError(name)


def _shas(params):
    state0 = core.jax_reset(params, jax.random.PRNGKey(0))
    return jaxpr_shas(jax, jnp, core, params, state0)


# ── 1. off = today ────────────────────────────────────────────────────────────

@pytest.mark.parametrize("var", VARIANT_IDS)
def test_rollouts_byte_identical(fx, var):
    """Every recorded array equal, no tolerance: state leaves, obs (noisy + clean),
    reward, done, termination_reason and every info key."""
    _, world, max_steps, seeds, max_t = _variant(var)
    params = _params(_world_dict(world, max_steps))
    arrays = G.roll_variant(jax, jnp, core, get_observation, params, seeds, max_t)
    want = sorted(k[len(var) + 1:] for k in fx if k.startswith(var + ".s"))
    assert want, f"{var}: fixture holds no arrays for this variant"
    assert sorted(arrays) == want, (
        f"{var}: recorded field set differs: extra {sorted(set(arrays) - set(want))[:8]}, "
        f"missing {sorted(set(want) - set(arrays))[:8]}")
    bad = []
    for k in want:
        ref, got = fx[f"{var}.{k}"], arrays[k]
        if ref.shape != got.shape or ref.dtype != got.dtype or not np.array_equal(ref, got):
            bad.append(k)
    assert not bad, f"{var}: {len(bad)} arrays differ from the pre-change fixture: {bad[:12]}"


@pytest.mark.parametrize("world", sorted(G.WORLDS))
def test_jaxpr_sha_identical(fx, world):
    """jax_step, jax_reset and update_body trace the pre-change graph."""
    now = _shas(_params(_world_dict(world)))
    for fn in ("jax_step", "jax_reset", "update_body"):
        want = str(fx[f"{world}._jaxpr_sha.{fn}"])
        print(f"[parity] {world} {fn}: {now[fn]}")
        assert now[fn] == want, f"{world}: {fn} jaxpr changed ({want} -> {now[fn]})"


@pytest.mark.parametrize("world", sorted(G.WORLDS))
def test_water_leaves_absent_when_off(world):
    """A water-off world carries no water state and no water info keys."""
    p = _params(_world_dict(world))
    assert p.water_enabled is False
    s = core.jax_reset(p, jax.random.PRNGKey(0))
    assert s.hydration is None and s.water_pos is None
    s2, _, _, info = core.jax_step(s, jnp.asarray(REST, dtype=jnp.int32), p)
    assert s2.hydration is None and s2.water_pos is None
    assert "drank" not in info and "drive_thirst" not in info


def test_water_enabled_is_mandatory():
    """No fallback on the gate: a config without `water.enabled` does not load."""
    d = _world_dict("lvl05")
    d.pop("water")
    with pytest.raises(ValueError, match=r"water\.enabled"):
        _params(d)


@pytest.mark.parametrize("world", sorted(G.WORLDS))
def test_fixture_coverage(fx, world):
    """The fixture is not vacuous: each world's hard-coded ending codes all occur."""
    seen = set()
    for var in (world, world + G.TRUNC_SUFFIX):
        seen |= {int(c) for c, n in fx[f"{var}._codes"] if n > 0}
    missing = EXPECTED_CODES[world] - seen
    assert not missing, f"{world}: fixture never shows termination code(s) {sorted(missing)}"
