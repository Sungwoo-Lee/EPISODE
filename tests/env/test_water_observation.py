"""What the agent senses of water (THIRST_WATER_PLAN §T4).

**Plain-language summary.** A water world adds one observation number, "Hydration"
(hydration / max, 0.5 at the comfortable level), placed directly after Body Temperature.
The pond also smells (only on the food channel, channel 0) and is visible. This test
checks, on real observations:

- the level-06 layout: the block order and the total width (59);
- the Hydration column equals `hydration / 200` on real steps;
- perceptual noise on Hydration uses the hydration noise slot and no neighbour's;
- the stats-CSV column builder and the sensory-viz builder accept a level-06 observation
  and the blocks after Hydration are not shifted;
- the pond's smell, `water.properties = [1.0, 0, 0, 0, 0]` (THIRST_WATER_PLAN Revision 2:
  the pond smells only of food, at one food item's strength). Expected values come from
  the real kernel (`sense_resource`, one source per pond cell carrying p/4) and are
  cross-checked against the closed form `f(d) = 1/d` (2 on-source): on a pond corner,
  beside the pond, and far away (where the 2x2 pond smells like ONE source of the whole
  vector at its centre, not four);
- on level 06 the pond's far-field channel 0 equals one food item's at the same
  distance, and channel 4 reads exactly 0 at every olfaction cell after a reset;
- pond cells light the visual channel.

Every smell assertion pins olfaction index 0: the agent's own cell (diamond offset 0),
channel 0. CPU only (conftest).
"""
import copy
import math
import os

import jax
import jax.numpy as jnp
import numpy as np
import pytest

from src.environment import core
from src.environment.config_loader import load_env_config, load_env_params
from src.environment.sensor import (build_sensory_viz, get_observation,
                                    get_observation_breakdown, get_visual_offsets,
                                    sense_resource)
from src.utils.config import Config
from src.utils.evaluation_core import _sensor_stat_columns

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_BASIC = os.path.join(_REPO, "configs", "environment", "experiment", "basic")
DEFAULT = os.path.join(_REPO, "configs", "environment", "default.yaml")
LVL05 = os.path.join(_BASIC, "05-campfire_thermal_10x10.yaml")

LVL06_ORDER = ["Satiation", "Body Temperature", "Hydration", "Interoceptive Nociception",
               "Extero Nociception", "Thermoception", "Olfaction", "Collision",
               "Proprioception", "Visual"]


@pytest.fixture(autouse=True)
def _release_compiled_programs():
    yield
    jax.clear_caches()


def _params(d):
    return load_env_params(Config(copy.deepcopy(d)))


LVL06 = os.path.join(_BASIC, "06-pond_thirst_10x10.yaml")


def _lvl06_dict():
    """Level 06, the pond world, resolved as the trainer resolves it."""
    return copy.deepcopy(load_env_config(LVL06).to_dict())


def _offset(bd, name):
    off = 0
    for k, v in bd.items():
        if k == name:
            return off
        off += v
    raise KeyError(name)


def _rollout(p, n, seed=0):
    step = jax.jit(core.jax_step)
    s = core.jax_reset(p, jax.random.PRNGKey(seed))
    akey = jax.random.PRNGKey(1000 + seed)
    out = []
    for t in range(n):
        akey, k = jax.random.split(akey)
        s, _, d, _ = step(s, jax.random.randint(k, (), 0, 6), p)
        out.append(s)
        if bool(d):
            s = core.jax_reset(p, jax.random.PRNGKey(seed * 7919 + t))
    return out


# ── layout ────────────────────────────────────────────────────────────────────

def test_level06_breakdown_order_and_width():
    p = _params(_lvl06_dict())
    bd = get_observation_breakdown(p)
    assert list(bd) == LVL06_ORDER
    assert sum(bd.values()) == 59 and bd["Hydration"] == 1
    s = core.jax_reset(p, jax.random.PRNGKey(0))
    assert get_observation(s, p).shape == (59,)


def test_hydration_column_is_hydration_over_max():
    p = _params(_lvl06_dict())
    i = _offset(get_observation_breakdown(p), "Hydration")
    for s in _rollout(p, 60):
        obs = np.asarray(get_observation(s, p, apply_noise=False))
        # 1-ULP tolerance: XLA folds the division by the constant 200 into a multiply
        # by its (inexact) reciprocal.
        assert obs[i] == pytest.approx(float(s.hydration) / 200.0, rel=1e-6)


def test_noise_uses_the_hydration_slot():
    d = _lvl06_dict()
    d["perceptual_noise"]["enabled"] = True
    mods = d["perceptual_noise"]["modalities"]
    mods["hydration"] = dict(mode="constant", sigma=0.5, injury_noise_scale=0.0,
                             clip_min=-10.0, clip_max=10.0)
    mods["satiation"] = dict(mode="constant", sigma=0.05, injury_noise_scale=0.0,
                             clip_min=-10.0, clip_max=10.0)
    p = _params(d)
    bd = get_observation_breakdown(p)
    ih, isat = _offset(bd, "Hydration"), _offset(bd, "Satiation")
    dh, ds = [], []
    for s in _rollout(p, 2000, seed=3):
        noisy = np.asarray(get_observation(s, p))
        clean = np.asarray(get_observation(s, p, apply_noise=False))
        dh.append(noisy[ih] - clean[ih])
        ds.append(noisy[isat] - clean[isat])
    sh, ss = float(np.std(dh)), float(np.std(ds))
    print(f"[noise] hydration std {sh:.4f} (sigma 0.5), satiation std {ss:.4f} (sigma 0.05)")
    assert abs(sh - 0.5) < 0.05
    assert abs(ss - 0.05) < 0.005


def test_csv_and_viz_accept_a_level06_observation():
    p = _params(_lvl06_dict())
    bd = get_observation_breakdown(p)
    names = []
    for k, v in bd.items():
        cols = _sensor_stat_columns(k, v, p, "obs_")
        assert len(cols) == v
        names += cols
    assert len(names) == 59
    assert names[_offset(bd, "Hydration")] == "obs_intero_hydration"
    assert names[_offset(bd, "Interoceptive Nociception")] == "obs_intero_nociception"
    s = core.jax_reset(p, jax.random.PRNGKey(0))
    obs = np.asarray(get_observation(s, p, apply_noise=False))
    viz = build_sensory_viz(obs, s, p)
    assert viz


# ── smell ─────────────────────────────────────────────────────────────────────

def _smell_world():
    """Nothing but the pond smells: no food, animals or obstacles. Pond at array rows/cols
    1-2 (candidate YAML [2, 2])."""
    d = copy.deepcopy(load_env_config(DEFAULT).to_dict())
    d["environment"].update(resources=[], entities=[], obstacles=[],
                            random_start_pos=False, start_pos=[9, 9])
    d["body"]["with_nutrition"] = False
    d["water"].update(enabled=True, candidates=[[2, 2]], random_start_hydration=False,
                      start_hydration=100.0)
    return _params(d)


def _olf0(p, agent):
    s = core.jax_reset(p, jax.random.PRNGKey(0))._replace(
        agent_pos=jnp.asarray(agent, dtype=jnp.int32))
    obs = np.asarray(get_observation(s, p, apply_noise=False))
    bd = get_observation_breakdown(p)
    assert np.asarray(get_visual_offsets(p.olfactory_grid_range))[0].tolist() == [0, 0]
    return float(obs[_offset(bd, "Olfaction")])        # centre cell, channel 0


def _f(d):
    return 2.0 if d < 1e-3 else 1.0 / d


WATER_P = [1.0, 0.0, 0.0, 0.0, 0.0]          # shipped `water.properties` (Revision 2)
POND_CELLS = [(1, 1), (1, 2), (2, 1), (2, 2)]  # array coords of the candidate [2, 2] pond


def test_shipped_water_vector_is_food_only():
    p = _smell_world()
    assert list(p.water_cell_property) == pytest.approx([v / 4 for v in WATER_P])


def _kernel(p, agent, sources, vec):
    """The real kernel, channel 0: `sense_resource` over `sources`, each carrying `vec`."""
    n = len(sources)
    return float(sense_resource(jnp.asarray(agent, dtype=jnp.float32),
                                jnp.asarray(sources, dtype=jnp.float32),
                                jnp.ones((n,), dtype=bool),
                                jnp.asarray([vec] * n, dtype=jnp.float32),
                                p.sensor_radius, p.sensor_decay)[0])


def _pond_kernel(p, agent):
    return _kernel(p, agent, POND_CELLS, [v / 4 for v in WATER_P])


def test_smell_on_a_pond_corner():
    p = _smell_world()
    want = _pond_kernel(p, [1, 1])
    # closed-form cross-check: 1.0 x (2 + 1 + 1 + 1/sqrt2) / 4 = 1.17678
    assert want == pytest.approx(1.0 * (2 + 1 + 1 + 1 / math.sqrt(2)) / 4, rel=1e-6)
    print(f"[smell] pond corner ch0 = {want:.6f}")
    assert _olf0(p, [1, 1]) == pytest.approx(want, rel=1e-6)


def test_smell_beside_the_pond():
    p = _smell_world()
    want = _pond_kernel(p, [1, 3])
    # closed-form cross-check: 1.0 x (1 + 1/2 + 1/sqrt2 + 1/sqrt5) / 4 = 0.66358
    assert want == pytest.approx(
        1.0 * (1 + 1 / 2 + 1 / math.sqrt(2) + 1 / math.sqrt(5)) / 4, rel=1e-6)
    print(f"[smell] beside pond ch0 = {want:.6f}")
    assert _olf0(p, [1, 3]) == pytest.approx(want, rel=1e-6)


def test_far_pond_smells_like_one_source_at_its_centroid():
    p = _smell_world()
    agent = (9, 9)
    centroid = (1.5, 1.5)
    dbar = math.hypot(agent[0] - centroid[0], agent[1] - centroid[1])
    assert dbar >= 8.0
    got = _olf0(p, list(agent))
    assert got == pytest.approx(_pond_kernel(p, list(agent)), rel=1e-6)
    analytic = 1.0 * _f(dbar)
    assert abs(got - analytic) / analytic < 0.03
    # Not four times louder: one source of the WHOLE vector p -- one food item,
    # [1.0, 0, 0, 0, 0] -- at the fractional centroid, through the same kernel.
    one = _kernel(p, list(agent), [centroid], WATER_P)
    print(f"[smell] far field ch0 = {got:.6f}, one food item at centroid = {one:.6f}")
    assert abs(got - one) / one < 0.03


def _lvl06_food_property():
    """Level 06's food smell vector (the `food` resource entry), as loaded."""
    d = _lvl06_dict()
    foods = [r for r in d["environment"]["resources"] if r.get("type", r.get("name")) == "food"]
    assert len(foods) == 1, d["environment"]["resources"]
    return foods[0]


def test_level06_pond_far_field_equals_one_food_item():
    """On level 06 as shipped, the pond's channel-0 far field equals a food item's at the
    same distance (Revision 2). Food sits at the pond's centroid, the agent far away."""
    d = _lvl06_dict()
    food = _lvl06_food_property()
    fvec = [float(v) for v in food["properties"]]
    assert fvec[0] == pytest.approx(1.0) and all(v == 0.0 for v in fvec[1:])
    assert [float(v) for v in d["water"]["properties"]] == pytest.approx(fvec)
    p = _params(d)
    agent = [9, 9]
    centroid = (1.5, 1.5)
    pond = _kernel(p, agent, POND_CELLS, [v / 4 for v in d["water"]["properties"]])
    one_food = _kernel(p, agent, [centroid], fvec)
    print(f"[lvl06] pond far ch0 = {pond:.6f}, food at same distance = {one_food:.6f}")
    assert abs(pond - one_food) / one_food < 0.03


def test_level06_channel4_is_zero_everywhere_at_reset():
    p = load_env_params(load_env_config(LVL06))
    bd = get_observation_breakdown(p)
    io, n = _offset(bd, "Olfaction"), bd["Olfaction"]
    V = p.res_property.shape[-1]
    assert V == 5 and n % V == 0
    for seed in range(8):
        s = core.jax_reset(p, jax.random.PRNGKey(seed))
        olf = np.asarray(get_observation(s, p, apply_noise=False))[io:io + n].reshape(-1, V)
        assert np.all(olf[:, 4] == 0.0), (seed, olf[:, 4])


def test_pond_cells_light_the_visual_channel():
    p = _smell_world()
    bd = get_observation_breakdown(p)
    iv, nv = _offset(bd, "Visual"), bd["Visual"]
    s = core.jax_reset(p, jax.random.PRNGKey(0))._replace(
        agent_pos=jnp.asarray([1, 3], dtype=jnp.int32))
    near = np.asarray(get_observation(s, p, apply_noise=False))[iv:iv + nv]
    far_pond = s._replace(water_pos=s.water_pos + 6)          # pond moved to rows/cols 7-8
    far = np.asarray(get_observation(far_pond, p, apply_noise=False))[iv:iv + nv]
    # visual_vector_size is 1 here, so entry k is diamond cell k. The diamond cells that
    # ARE pond cells, seen from (1, 3): (1, 2), (2, 2) and (1, 1).
    assert p.visual_vector_size == 1
    offs = [tuple(o) for o in np.asarray(get_visual_offsets(p.visual_sensor_range)).tolist()]
    pond_cells = [offs.index(o) for o in ((0, -1), (1, -1), (0, -2))]
    for k in pond_cells:
        assert near[k] > far[k] + 0.1, (k, near[k], far[k])
    assert near.sum() > far.sum()


# ── level 07: hydration noise is stated clean (C5) ────────────────────────────

def test_level07_hydration_noise_is_clean():
    """KNOWN_BUGS ~#371: read from the LOADED params, not the YAML. Hydration only -- the
    noise rung does not state a body_temperature sigma (inherited 0.0; an older, separate
    open item)."""
    p = load_env_params(load_env_config(os.path.join(_BASIC, "07-sensory_noise_10x10.yaml")))
    assert p.perceptual_noise_enabled and p.water_enabled
    order = list(p.noise_modality_order)
    i = order.index("Hydration")
    assert float(p.noise_sigmas[i]) == 0.0 and int(p.noise_modes[i]) == 1
