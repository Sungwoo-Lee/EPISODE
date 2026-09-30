"""Where the pond goes, and that nothing else lands on it (THIRST_WATER_PLAN §T2).

**Plain-language summary.** A water world has one pond per episode: a 2x2 block of
walkable cells, drawn each episode from a short list of candidate spots (or at random, or
at the grid centre). This test checks three things against real `jax_reset` / `jax_step`
output, never against a re-derivation through the loader's own table:

1. **Bad configurations are refused at load**, each with a message that names the key:
   a pond off the grid or inside the edge margin, a duplicate or empty candidate list, a
   pond over a fixed start, a grid too small for a random pond, the unsupported
   placement mode and fire-distance passes, a failing capacity check, a wrong-length smell
   vector, a missing hydration noise entry, a start hydration at either lethal end.
2. **Placement at runtime** over 2,000 level-06 resets: the pond is always exactly one
   candidate's block, the candidates are drawn uniformly (chi-square), no active food,
   animal or obstacle sits on a pond cell, every active entity is inside its own spawn
   area (this, not the load-time capacity check, is the guard against the silent (0, 0)
   parking of KNOWN_BUGS ~#117 for campfires), and the agent never starts on the pond.
   Random mode covers exactly the analytically legal top-lefts; centre mode never moves.
3. **Respawns avoid the pond**, and **predators can walk into it** (it is not an obstacle).

CPU only (conftest).
"""
import copy
import os

import jax
import jax.numpy as jnp
import numpy as np
import pytest

from src.environment import core
from src.environment.config_loader import load_env_config, load_env_params
from src.utils.config import Config

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_BASIC = os.path.join(_REPO, "configs", "environment", "experiment", "basic")
LVL05 = os.path.join(_BASIC, "05-campfire_thermal_10x10.yaml")
DEFAULT = os.path.join(_REPO, "configs", "environment", "default.yaml")

N_RESETS = 2000


@pytest.fixture(autouse=True)
def _release_compiled_programs():
    yield
    jax.clear_caches()


LVL06 = os.path.join(_BASIC, "06-pond_thirst_10x10.yaml")


def _lvl06_dict():
    """Level 06, the pond world, resolved as the trainer resolves it."""
    return copy.deepcopy(load_env_config(LVL06).to_dict())


def _params(d):
    return load_env_params(Config(copy.deepcopy(d)))


def _block(r, c, h=2, w=2):
    return {(r + i, c + j) for i in range(h) for j in range(w)}


def _resets(params, n=N_RESETS, offset=0):
    keys = jax.vmap(jax.random.PRNGKey)(jnp.arange(offset, offset + n))
    return jax.jit(jax.vmap(lambda k: core.jax_reset(params, k)))(keys)


# ── 1. load-time refusals ─────────────────────────────────────────────────────

def _mut(fn):
    def build():
        d = _lvl06_dict()
        fn(d)
        return d
    return build


def _set_water(**kw):
    return _mut(lambda d: d["water"].update(**kw))


def _fixed_start(d, pos):
    d["environment"]["random_start_pos"] = False
    d["environment"]["start_pos"] = list(pos)


def _per_type_world():
    """per_type placement on a thermal-OFF world (the campfire world refuses per_type
    and min_fire_separation 0 on its own, before the water check is reached)."""
    d = copy.deepcopy(load_env_config(DEFAULT).to_dict())
    d["environment"].setdefault("placement", {})["mode"] = "per_type"
    d["water"]["enabled"] = True
    return d


def _no_hydration_noise(d):
    d["perceptual_noise"]["modalities"].pop("hydration")


def _giant_center_pond(d):
    # An 8x8 pond at array (1, 1) covers the campfire's whole 36-cell area.
    d["water"].update(placement="center", size=[8, 8], edge_margin=1)


REFUSALS = {
    "candidate_off_grid": (_set_water(candidates=[[10, 10]]), r"water\.candidates\[0\].*off the"),
    "candidate_in_margin": (_set_water(candidates=[[1, 1]]), r"water\.candidates\[0\].*edge_margin"),
    "candidate_duplicate": (_set_water(candidates=[[2, 2], [2, 2]]), r"water\.candidates\[1\].*duplicate"),
    "candidate_empty": (_set_water(candidates=[]), r"water\.candidates must be a non-empty"),
    "candidate_bad_shape": (_set_water(candidates=[[2]]), r"water\.candidates\[0\]"),
    "center_in_margin": (_set_water(placement="center", edge_margin=5), r"water\.placement: center.*edge_margin"),
    "center_covers_fixed_start": (_mut(lambda d: (_fixed_start(d, [5, 5]), d["water"].update(placement="center"))),
                                  r"water\.placement: center.*start_pos"),
    "candidate_covers_fixed_start": (_mut(lambda d: (_fixed_start(d, [5, 5]), d["water"].update(candidates=[[4, 4]]))),
                                     r"water\.candidates\[0\].*start_pos"),
    "random_grid_too_small": (_set_water(placement="random", size=[9, 9]), r"water\.placement: random.*too small"),
    "unknown_placement": (_set_water(placement="nearby"), r"water\.placement must be one of"),
    "bad_size": (_set_water(size=[0, 2]), r"water\.size"),
    "per_type_mode": (_per_type_world, r"water\.enabled: true is not supported with environment\.placement\.mode"),
    "food_min_fire_distance": (_mut(lambda d: d["thermal"].update(food_min_fire_distance=3)),
                               r"water\.enabled: true cannot be combined with thermal\.food_min_fire_distance"),
    "bush_min_fire_distance": (_mut(lambda d: d["thermal"].update(bush_min_fire_distance=2)),
                               r"water\.enabled: true cannot be combined with thermal\.food_min_fire_distance"),
    "capacity_check": (_mut(_giant_center_pond), r"water: capacity check failed"),
    "properties_length": (_set_water(properties=[0.5, 0.5]), r"water\.properties"),
    "properties_range": (_set_water(properties=[1.5, 0, 0, 0, 0]), r"water\.properties"),
    "visual_properties_length": (_set_water(visual_properties=[1.0, 1.0]), r"water\.visual_properties"),
    "missing_hydration_noise": (_mut(_no_hydration_noise), r"perceptual_noise\.modalities\.hydration"),
    "start_hydration_zero": (_set_water(random_start_hydration=False, start_hydration=0.0),
                             r"water\.start_hydration"),
    "start_hydration_max": (_set_water(random_start_hydration=False, start_hydration=200.0),
                            r"water\.start_hydration"),
    "random_range_above_max": (_set_water(start_hydration_high=250.0), r"water\.start_hydration_low/high"),
    "setpoint_above_max": (_set_water(hydration_setpoint=300.0), r"water\.hydration_setpoint"),
    "max_hydration_zero": (_set_water(max_hydration=0.0), r"water\.max_hydration"),
    "negative_drain": (_set_water(drain_per_step=-1.0), r"water\.drain_per_step"),
}


@pytest.mark.parametrize("name", sorted(REFUSALS))
def test_loader_refusals(name):
    build, pattern = REFUSALS[name]
    with pytest.raises(ValueError, match=pattern):
        _params(build())


def test_missing_sub_key_is_named():
    """Conditional-mandatory: with water on, a missing sub-key raises naming it."""
    d = _lvl06_dict()
    d["water"].pop("drain_per_step")
    with pytest.raises(ValueError, match=r"water\.drain_per_step"):
        _params(d)


def test_water_off_reads_no_other_key():
    """With the gate off, a config may omit every other water key."""
    d = copy.deepcopy(load_env_config(LVL05).to_dict())
    d["water"] = {"enabled": False}
    p = _params(d)
    assert p.water_enabled is False and p.water_topleft_table == ()


def test_level06_resolves_the_candidate_table():
    """YAML candidates are 1-based; the table is 0-based array coordinates."""
    p = _params(_lvl06_dict())
    assert p.water_topleft_table == ((1, 1), (1, 7), (7, 1), (7, 7))
    assert (p.water_block_h, p.water_block_w) == (2, 2)
    assert p.water_cell_property == (0.125, 0.0, 0.0, 0.0, 0.125)
    assert p.water_visual_property == (1.0,)


# ── 2. runtime placement, level 06 ────────────────────────────────────────────

@pytest.fixture(scope="module")
def lvl06_resets():
    p = _params(_lvl06_dict())
    return p, jax.device_get(_resets(p))


def _cells(pos):
    return {(int(r), int(c)) for r, c in np.asarray(pos)}


def test_pond_is_always_one_candidate_block_and_uniform(lvl06_resets):
    p, s = lvl06_resets
    blocks = {tl: _block(*tl) for tl in p.water_topleft_table}
    counts = {tl: 0 for tl in blocks}
    for i in range(N_RESETS):
        cells = _cells(s.water_pos[i])
        hit = [tl for tl, b in blocks.items() if b == cells]
        assert len(hit) == 1, f"reset {i}: pond cells {sorted(cells)} are not one candidate block"
        counts[hit[0]] += 1
    exp = N_RESETS / len(blocks)
    chi2 = sum((c - exp) ** 2 / exp for c in counts.values())
    # df = 3; the p = 0.001 critical value is 16.266.
    print(f"[placement] candidate counts {counts}, chi2 {chi2:.2f}")
    assert chi2 < 16.266, f"candidate draw is not uniform: {counts} (chi2 {chi2:.2f})"


def test_no_active_entity_on_the_pond_and_every_entity_in_its_area(lvl06_resets):
    p, s = lvl06_resets
    groups = (("res", s.res_pos, s.res_active, np.asarray(p.res_spawn_area)),
              ("animal", s.animal_pos, s.animal_active, np.asarray(p.animal_spawn_area)),
              ("obs", s.obs_pos, s.obs_active, np.asarray(p.obs_spawn_area)))
    on_pond, out_of_area, checked = [], [], 0
    for i in range(N_RESETS):
        pond = _cells(s.water_pos[i])
        for name, pos, active, areas in groups:
            for j in range(pos.shape[1]):
                if not bool(active[i, j]):
                    continue
                checked += 1
                r, c = int(pos[i, j, 0]), int(pos[i, j, 1])
                if (r, c) in pond:
                    on_pond.append((i, name, j, (r, c)))
                r0, c0, r1, c1 = (int(v) for v in areas[j])
                if not (r0 <= r < r1 and c0 <= c < c1):
                    out_of_area.append((i, name, j, (r, c), (r0, c0, r1, c1)))
    assert checked > 0
    assert not on_pond, f"{len(on_pond)} active entities on a pond cell, e.g. {on_pond[:5]}"
    assert not out_of_area, (f"{len(out_of_area)} active entities outside their own spawn "
                             f"area (the (0,0) fallback), e.g. {out_of_area[:5]}")


def test_agent_never_starts_on_the_pond(lvl06_resets):
    _, s = lvl06_resets
    bad = [i for i in range(N_RESETS)
           if (int(s.agent_pos[i, 0]), int(s.agent_pos[i, 1])) in _cells(s.water_pos[i])]
    assert not bad, f"agent started on the pond in resets {bad[:10]}"


def test_agent_start_repair_is_exercised_and_uniform_off_pond():
    """The repair must actually fire (the raw draw lands on the pond ~4% of the time), and
    the repaired start covers every non-pond cell."""
    d = _lvl06_dict()
    d["water"]["candidates"] = [[2, 2]]          # pond fixed at array rows/cols 1-2
    p = _params(d)
    s = jax.device_get(_resets(p, n=4000))
    starts = {(int(r), int(c)) for r, c in np.asarray(s.agent_pos)}
    pond = _block(1, 1)
    assert not (starts & pond)
    assert starts == {(r, c) for r in range(10) for c in range(10)} - pond


def test_random_mode_support_is_the_legal_set():
    d = _lvl06_dict()
    d["water"]["placement"] = "random"
    p = _params(d)
    legal = {(r, c) for r in range(1, 8) for c in range(1, 8)}   # 2x2 inside margin 1 of 10x10
    assert set(p.water_topleft_table) == legal
    s = jax.device_get(_resets(p))
    seen = {(int(s.water_pos[i, 0, 0]), int(s.water_pos[i, 0, 1])) for i in range(N_RESETS)}
    assert seen == legal, f"missing {sorted(legal - seen)[:5]}, extra {sorted(seen - legal)[:5]}"


def test_center_mode_never_moves():
    d = _lvl06_dict()
    d["water"]["placement"] = "center"
    p = _params(d)
    s = jax.device_get(_resets(p, n=200))
    for i in range(200):
        assert _cells(s.water_pos[i]) == _block(4, 4)


# ── 3. respawn and predators ──────────────────────────────────────────────────

def test_respawned_resources_avoid_the_pond():
    """Food eaten once respawns at a random in-area cell; never on the pond."""
    d = _lvl06_dict()
    for r in d["environment"]["resources"]:
        r["max_consumption"] = 1
        r["regeneration_delay"] = 0
    p = _params(d)
    step = jax.jit(core.jax_step)
    reset = jax.jit(core.jax_reset)
    state = reset(p, jax.random.PRNGKey(7))
    akey = jax.random.PRNGKey(99)
    respawns, eps = 0, 0
    for t in range(5000):
        akey, k = jax.random.split(akey)
        a = jax.random.randint(k, (), 0, 6)
        prev_pos = np.asarray(state.res_pos)
        state, _, done, _ = step(state, a, p)
        pos, act = np.asarray(state.res_pos), np.asarray(state.res_active)
        pond = _cells(state.water_pos)
        respawns += int(np.any(pos != prev_pos, axis=-1).sum())
        on = [j for j in range(pos.shape[0]) if act[j] and (int(pos[j, 0]), int(pos[j, 1])) in pond]
        assert not on, f"step {t}: active resource(s) {on} on the pond {sorted(pond)}"
        if bool(done):
            eps += 1
            state = reset(p, jax.random.PRNGKey(1000 + eps))
    print(f"[respawn] {respawns} respawn moves over 5000 steps, {eps} episodes")
    assert respawns >= 20, f"only {respawns} respawns: the check is close to vacuous"


def test_a_hunting_predator_walks_into_the_pond():
    """Decision 9: the pond is not an obstacle. A predator hunting an agent on the far side
    of the pond steps onto a pond cell on its way."""
    d = _lvl06_dict()
    d["water"]["candidates"] = [[2, 2]]              # pond at array rows/cols 1-2
    p = _params(d)
    s = core.jax_reset(p, jax.random.PRNGKey(0))
    hunters = list(p.hunt_idx)
    assert hunters, "level 06 has no hunting animal"
    k = hunters[0]
    n = s.animal_pos.shape[0]
    only_k = jnp.arange(n) == k
    s = s._replace(
        agent_pos=jnp.array([1, 3], dtype=jnp.int32),
        animal_pos=s.animal_pos.at[k].set(jnp.array([1, 0], dtype=jnp.int32)),
        animal_active=only_k,
        animal_state=s.animal_state.at[k].set(1),                       # HUNT
        animal_stamina=s.animal_stamina.at[k].set(1e6),
        animal_detect_sampled=s.animal_detect_sampled.at[k].set(20),
        animal_move_timer=s.animal_move_timer.at[k].set(0),
        animal_move_int_sampled=s.animal_move_int_sampled.at[k].set(1),
        animal_attack_range_sampled=jnp.zeros_like(s.animal_attack_range_sampled),
        obs_active=jnp.zeros_like(s.obs_active),                         # nothing in the way
        res_active=jnp.zeros_like(s.res_active),
    )
    pond = _block(1, 1)
    path = [tuple(int(v) for v in np.asarray(s.animal_pos[k]))]
    step = jax.jit(core.jax_step)
    for _ in range(10):
        s, _, _, _ = step(s, jnp.asarray(4, dtype=jnp.int32), p)
        s = s._replace(agent_pos=jnp.array([1, 3], dtype=jnp.int32))   # hold the agent still
        path.append(tuple(int(v) for v in np.asarray(s.animal_pos[k])))
    print(f"[predator] path {path}")
    assert any(c in pond for c in path), f"predator never entered the pond: {path}"


@pytest.mark.parametrize("area,allowed_n", [
    ((1, 1, 4, 3), 2),    # rows 1-3, cols 1-2: 6 cells, 4 of them pond -> (3,1), (3,2)
    ((0, 0, 4, 4), 12),   # rows 0-3, cols 0-3: 16 cells with the pond inside -> 12 cells
])
def test_respawn_repair_is_uniform_over_area_minus_pond(area, allowed_n):
    """Force every resource to respawn on every step into an area that overlaps the pond
    (pond at array rows/cols 1-2). The raw draw lands on the pond often; after the repair
    every respawn is inside the area, off the pond, and the cells are hit uniformly."""
    d = _lvl06_dict()
    d["water"]["candidates"] = [[2, 2]]
    p = _params(d)
    n = p.res_type.shape[0]
    p = p.replace(res_spawn_area=jnp.tile(jnp.asarray(area, dtype=p.res_spawn_area.dtype), (n, 1)))
    r0, c0, r1, c1 = area
    allowed = {(r, c) for r in range(r0, r1) for c in range(c0, c1)} - _block(1, 1)
    assert len(allowed) == allowed_n

    def one(key):
        s = core.jax_reset(p, key)
        s = s._replace(res_active=jnp.zeros_like(s.res_active),
                       res_reg_timer=jnp.zeros_like(s.res_reg_timer),
                       res_allocated=jnp.ones_like(s.res_allocated))
        s2, _, _, _ = core.jax_step(s, jnp.asarray(4, dtype=jnp.int32), p)
        return s2.res_pos
    pos = np.asarray(jax.jit(jax.vmap(one))(jax.vmap(jax.random.PRNGKey)(jnp.arange(400))))
    cells = [tuple(int(v) for v in rc) for rc in pos.reshape(-1, 2)]
    assert set(cells) <= allowed, f"respawns outside area-minus-pond: {sorted(set(cells) - allowed)[:5]}"
    counts = np.array([cells.count(c) for c in sorted(allowed)])
    exp = len(cells) / len(allowed)
    chi2 = float(((counts - exp) ** 2 / exp).sum())
    from scipy.stats import chi2 as _chi2
    print(f"[repair] area {area}: {len(cells)} respawns over {len(allowed)} cells, chi2 {chi2:.1f}")
    assert set(cells) == allowed
    assert _chi2.sf(chi2, len(allowed) - 1) > 0.001, counts
