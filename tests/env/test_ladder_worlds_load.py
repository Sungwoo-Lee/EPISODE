"""Every rung of the basic ladder loads, resets and steps through the trainer's path.

**Plain-language summary.** The maintained curriculum ("ladder") is the eight worlds
`configs/environment/experiment/basic/00-` … `07-`. THIRST_WATER_PLAN added rung 06 (the
campfire world plus a pond and thirst) and moved the noise rung from 06 to 07, on top of
the pond world. This test loads each rung exactly as the trainer does
(`load_env_config` -> `load_env_params`), resets, takes five steps, and checks the
observation width, which rungs have water, and which has perceptual noise. It also
checks that the rung files are exactly these eight, so a missed rename or an unplanned
new rung fails here. (`test_backward_compat_configs.py` skips every ladder world,
KNOWN_BUGS ~#124, so it is no evidence for this.)

CPU only (conftest).
"""
import os
import re

import jax
import jax.numpy as jnp
import pytest

from src.environment import core
from src.environment.config_loader import load_env_config, load_env_params
from src.environment.sensor import get_observation, get_observation_breakdown

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_BASIC = os.path.join(_REPO, "configs", "environment", "experiment", "basic")

RUNGS = (
    # file, observation width, water, perceptual noise
    ("00-static_predator_5x5.yaml", 44, False, False),
    ("01-slow_predator_5x5.yaml", 44, False, False),
    ("02-predator_and_rabbit_10x10.yaml", 52, False, False),
    ("03-random_init_10x10.yaml", 52, False, False),
    ("04-jump_attack_10x10.yaml", 52, False, False),
    ("05-campfire_thermal_10x10.yaml", 58, False, False),
    ("06-pond_thirst_10x10.yaml", 59, True, False),
    ("07-sensory_noise_10x10.yaml", 59, True, True),
)


@pytest.fixture(autouse=True)
def _release_compiled_programs():
    yield
    jax.clear_caches()


def test_the_rung_files_are_exactly_the_eight():
    """Only files named like a rung (`NN-...`) are checked; the folder's two non-rung
    worlds (forage_5x5, slow_predator_bush_5x5) are ignored."""
    on_disk = sorted(f for f in os.listdir(_BASIC) if re.match(r"^0[0-9]-", f))
    assert on_disk == [r[0] for r in RUNGS]


@pytest.mark.parametrize("name,width,water,noise", RUNGS, ids=[r[0][:2] for r in RUNGS])
def test_rung_loads_resets_and_steps(name, width, water, noise):
    p = load_env_params(load_env_config(os.path.join(_BASIC, name)))
    assert sum(get_observation_breakdown(p).values()) == width
    assert p.water_enabled is water
    assert bool(p.perceptual_noise_enabled) is noise
    s = core.jax_reset(p, jax.random.PRNGKey(0))
    assert get_observation(s, p).shape == (width,)
    step = jax.jit(core.jax_step)
    for t in range(5):
        s, _, _, info = step(s, jnp.asarray(t % 6, dtype=jnp.int32), p)
    assert get_observation(s, p).shape == (width,)
    assert (s.hydration is not None) is water
