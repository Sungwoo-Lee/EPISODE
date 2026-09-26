"""Hand-computed unit tests for the five state-dependent body mechanics.

**Plain-language summary.** `docs/develop/active/thermal/STATE_DEPENDENT_BODY_MECHANICS.md`
adds five mechanics to the body update:

* **B1** — each episode starts at a random body temperature;
* **B2** — healing slows when the body is too cold or too warm;
* **B3** — healing costs food energy (`partial`: heal only what you can pay for;
  `full`: heal fully and starve if you cannot pay);
* **B4** — injury makes the body exchange heat with its cell faster;
* **B5** — healing is faster when well fed and slower when hungry.

`tests/env/test_body_mechanics_parity.py` proves that all five are exactly inert at their
off values. This file pins what they do when ON, with literal numbers computed by hand in
the plan (T-B1-1 ... T-LOG-5), the loader's refusals, and its logged worst cases.

Every scene is curriculum level 05 (the campfire world: recovery 0.2/step, x25 in a bush
= 5.0 per rest step; metabolic cost 1.0; k_exchange 0.04, k_loss 0.02, warming x2.0,
cooling x0.25) with the animals and hiding predators removed, fires off and a uniform
temperature field, so each number depends only on the mechanic under test. Tolerance
1e-5; off cases are compared exactly.

**Graph-identity tests (last section) and why B5 is not among them.** They trace
`update_body` and walk the jaxpr backwards: at B2 off, the injury output must not depend
on `state.body_temp`; at B4 off, the body-temperature output must not depend on
`state.injury_level`; and both dependencies must appear when the mechanic is on. B5 is
deliberately NOT in that set. Its input, `state.nutrition`, is always consumed by the
nutrition update, and the injury output legitimately depends on nutrition in no off path —
but a "does the injury output reach `state.nutrition`" walk cannot tell B5 apart from the
B3 charge path or future couplings, and a positional "leaf unused" test is impossible
because the leaf is always used. B5's inertness is covered by the parity test's rollout
equality and jaxpr-SHA equality instead. Do not "complete the set" by adding B5 here.
"""
import copy
import logging
import math
import os
import re

import jax
import jax.numpy as jnp
import numpy as np
import pytest

import src.environment.config_loader as L
from src.environment.config_loader import load_env_config, load_env_params
from src.environment.core import jax_reset, jax_step, update_body
from src.utils.config import Config

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_LVL05 = os.path.join(_REPO, "configs", "environment", "experiment", "basic",
                      "05-campfire_thermal_10x10.yaml")
_LOGGER = "src.environment.config_loader"
ATOL = 1e-5
REST = 4


@pytest.fixture(autouse=True, scope="module")
def _release_compiled_programs():
    """Drop this module's compiled programs afterwards.

    Each distinct world compiles its own step/reset programs, and every compiled CPU
    program holds memory mappings. Kept alive across a whole-suite run they exhaust the
    kernel's per-process limit (vm.max_map_count = 65530 here) and a LATER, unrelated
    module aborts inside XLA compilation. Measured 2026-09-26: without this, a
    `pytest tests/env` run reached 65,479 mappings and died in
    test_bush_blocks_animals.py.
    """
    yield
    jax.clear_caches()


# ══════════════════════════════════════════════════════════════════════════════
# Scene helpers
# ══════════════════════════════════════════════════════════════════════════════

def _lvl05():
    """Level 05 as resolved, with B1 OFF (C3 turns it on in the file)."""
    assert os.path.isfile(_LVL05), _LVL05
    d = copy.deepcopy(load_env_config(_LVL05).to_dict())
    d["thermal"]["random_start_body_temp"] = False
    return d


def _controlled(cell=0.0):
    """Level 05 with no animals, no hiding predators, no fires, a uniform field."""
    d = _lvl05()
    for e in d["environment"]["entities"]:
        e["count_low"] = 0
        e["count_high"] = 0
    for r in d["environment"]["resources"]:
        if r["type"] == "hiding_predator":
            r["count_low"] = 0
            r["count_high"] = 0
    d["thermal"]["use_object_sources"] = False
    d["thermal"]["use_random_spots"] = False
    d["thermal"]["default_temp"] = [float(cell), float(cell)]
    return d


def _p(d):
    return load_env_params(Config(copy.deepcopy(d)))


def _cells(params, state):
    """(bush cell, open cell) for this reset."""
    hides = np.asarray(params.obs_hides_agent) & np.asarray(state.obs_active)
    obs_pos = np.asarray(state.obs_pos)
    bush = obs_pos[np.flatnonzero(hides)[0]]
    taken = {tuple(x) for x in obs_pos[np.asarray(state.obs_active)]}
    taken |= {tuple(x) for x in np.asarray(state.res_pos)[np.asarray(state.res_active)]}
    open_cell = next((r, c) for r in range(params.height) for c in range(params.width)
                     if (r, c) not in taken)
    return jnp.asarray(bush, dtype=jnp.int32), jnp.asarray(open_cell, dtype=jnp.int32)


def _scene(params, N=100.0, I=50.0, T=0.0, cell=None, where="bush"):
    state = jax_reset(params, jax.random.PRNGKey(0))
    bush, open_cell = _cells(params, state)
    pos = bush if where == "bush" else open_cell
    kw = dict(agent_pos=pos, nutrition=jnp.float32(N), satiation=jnp.float32(N),
              injury_level=jnp.float32(I), body_temp=jnp.float32(T),
              injury_buffer=jnp.zeros_like(state.injury_buffer),
              rest_streak=jnp.int32(0))
    if cell is not None:
        kw["thermal_field"] = jnp.full(state.thermal_field.shape, cell, jnp.float32)
    return state.replace(**kw), pos


def _info(rested=True, ate=False, damage=0.0):
    return {"rested": jnp.array(rested), "ate_food": jnp.array(ate),
            "damage": jnp.float32(damage)}


def _body(params, **scene):
    """One update_body step; returns a dict of the named outputs."""
    info = _info(**{k: scene.pop(k) for k in ("rested", "ate", "damage") if k in scene})
    state, pos = _scene(params, **scene)
    out = update_body(state, info, params, pos)
    names = ("satiation", "nutrition", "injury", "buffer", "history", "streak",
             "body_temp", "thermal_death", "done", "starved")
    return dict(zip(names, out))


def _with(d, **over):
    d = copy.deepcopy(d)
    for k, v in over.items():
        blk, key = k.split("__")
        d[blk][key] = v
    return d


# ══════════════════════════════════════════════════════════════════════════════
# B1 — random starting body temperature
# ══════════════════════════════════════════════════════════════════════════════

def _reset_leaves(params, keys):
    states = jax.vmap(lambda k: jax_reset(params, k))(keys)
    return {jax.tree_util.keystr(p): np.asarray(v)
            for p, v in jax.tree_util.tree_flatten_with_path(states)[0]}


def _other_leaves_equal(a, b):
    for k in a:
        if k == ".body_temp":
            continue
        assert np.array_equal(a[k], b[k]), f"reset leaf {k} moved when B1 changed"


def test_B1_1_off_is_setpoint_and_other_leaves_unchanged():
    keys = jax.random.split(jax.random.PRNGKey(7), 32)
    off = _reset_leaves(_p(_lvl05()), keys)
    on = _reset_leaves(_p(_with(_lvl05(), thermal__random_start_body_temp=True,
                                thermal__start_body_temp_low=-7.0,
                                thermal__start_body_temp_high=-7.0)), keys)
    assert np.all(off[".body_temp"] == 0.0)
    _other_leaves_equal(off, on)


def test_B1_2_pinned_start_is_exact():
    p = _p(_with(_lvl05(), thermal__random_start_body_temp=True,
                 thermal__start_body_temp_low=-7.0, thermal__start_body_temp_high=-7.0))
    bt = _reset_leaves(p, jax.random.split(jax.random.PRNGKey(3), 16))[".body_temp"]
    assert np.all(bt == np.float32(-7.0))


def test_B1_3_range_mean_and_stream_isolation():
    """CP2: 1000 resets in [-10, 5], mean -2.5 +/- 0.5, every other leaf unchanged."""
    keys = jax.random.split(jax.random.PRNGKey(11), 1000)
    off = _reset_leaves(_p(_lvl05()), keys)
    on = _reset_leaves(_p(_with(_lvl05(), thermal__random_start_body_temp=True,
                                thermal__start_body_temp_low=-10.0,
                                thermal__start_body_temp_high=5.0)), keys)
    bt = on[".body_temp"]
    assert bt.min() >= -10.0 and bt.max() <= 5.0
    assert abs(float(bt.mean()) + 2.5) < 0.5, bt.mean()
    _other_leaves_equal(off, on)


@pytest.mark.parametrize("low,high", [(5.0, -5.0), (-16.0, 0.0), (0.0, 16.0),
                                      (float("nan"), 0.0)])
def test_B1_4_loader_refuses_bad_range(low, high):
    d = _with(_lvl05(), thermal__random_start_body_temp=True,
              thermal__start_body_temp_low=low, thermal__start_body_temp_high=high)
    with pytest.raises(ValueError, match="start_body_temp_low/high"):
        _p(d)


def test_B1_4_flag_must_be_bool():
    with pytest.raises(ValueError, match="random_start_body_temp must be true or false"):
        _p(_with(_lvl05(), thermal__random_start_body_temp="yes"))


def test_B1_4_thermal_off_loads_with_every_thermal_key_deleted():
    d = _lvl05()
    d["thermal"] = {"enabled": False}
    p = _p(d)
    assert p.thermal_random_start_body_temp is False
    assert p.thermal_injury_heat_exchange_gain == 0.0
    assert p.thermal_injury_heat_exchange_mode == "cooling_only"


# ══════════════════════════════════════════════════════════════════════════════
# B2 — healing needs warmth
# ══════════════════════════════════════════════════════════════════════════════

def _b2(sc, sw):
    return _p(_with(_controlled(), thermal__healing_cold_sensitivity=sc,
                    thermal__healing_warm_sensitivity=sw))


@pytest.mark.parametrize("T,want", [(0.0, 45.0), (-5.0, 47.5), (-10.0, 50.0),
                                    (6.0, 46.5), (-30.0, 50.0)])
def test_B2_1_asymmetric(T, want):
    out = _body(_b2(0.1, 0.05), I=50.0, T=T)
    assert float(out["injury"]) == pytest.approx(want, abs=ATOL)


def test_B2_2_warm_side_off():
    assert float(_body(_b2(0.1, 0.0), I=50.0, T=6.0)["injury"]) == pytest.approx(45.0, abs=ATOL)


def test_B2_3_cold_side_off():
    assert float(_body(_b2(0.0, 0.05), I=50.0, T=-5.0)["injury"]) == pytest.approx(45.0, abs=ATOL)


def test_B2_4_both_zero_is_today_exactly():
    p_off = _p(_controlled())
    for T in (-12.0, -5.0, 0.0, 6.0):
        a = _body(p_off, I=50.0, T=T)["injury"]
        b = _body(_b2(0.0, 0.0), I=50.0, T=T)["injury"]
        assert float(a) == float(b) == 45.0


@pytest.mark.parametrize("scene", [dict(rested=False), dict(damage=6.0)])
def test_B2_5_inherits_rest_and_no_damage(scene):
    out = _body(_b2(0.1, 0.05), I=50.0, T=-5.0, **scene)
    assert float(out["injury"]) >= 50.0


@pytest.mark.parametrize("key", ["healing_cold_sensitivity", "healing_warm_sensitivity"])
@pytest.mark.parametrize("val", [-0.1, float("nan"), float("inf")])
def test_B2_6_refuses_negative_and_nan(key, val):
    with pytest.raises(ValueError, match=key):
        _p(_with(_lvl05(), **{f"thermal__{key}": val}))


# ══════════════════════════════════════════════════════════════════════════════
# B3 — healing uses energy
# ══════════════════════════════════════════════════════════════════════════════

def _b3(mode, c=1.0, base=None):
    return _p(_with(base if base is not None else _controlled(),
                    body__healing_nutrition_cost=c, body__healing_nutrition_shortfall=mode))


def test_B3_1_full_normal():
    out = _body(_b3("full"), N=100.0, I=50.0)
    assert float(out["nutrition"]) == pytest.approx(94.0, abs=ATOL)
    assert float(out["injury"]) == pytest.approx(45.0, abs=ATOL)


def test_B3_2_full_small_wound_charges_only_what_heals():
    out = _body(_b3("full"), N=100.0, I=3.0)
    assert float(out["nutrition"]) == pytest.approx(96.0, abs=ATOL)
    assert float(out["injury"]) == pytest.approx(0.0, abs=ATOL)


@pytest.mark.parametrize("mode", ["partial", "full"])
def test_B3_3_uninjured_pays_nothing(mode):
    assert float(_body(_b3(mode), N=100.0, I=0.0)["nutrition"]) == pytest.approx(99.0, abs=ATOL)


def _step(params, state, action=REST):
    return jax_step(state, jnp.int32(action), params)


def test_B3_4_full_shortfall_starves():
    p = _b3("full")
    state, _ = _scene(p, N=4.0, I=50.0)
    s1, _r, done, info = _step(p, state)
    assert float(s1.nutrition) == 0.0
    assert float(s1.injury_level) == pytest.approx(45.0, abs=ATOL)
    assert bool(done) and int(info["termination_reason"]) == 2


def test_B3_5_partial_heals_what_it_can_and_the_charge_never_kills():
    p = _b3("partial")
    state, _ = _scene(p, N=4.0, I=50.0)
    s1, _r, done, info = _step(p, state)
    assert abs(float(s1.nutrition)) <= 1e-6
    assert float(s1.injury_level) == pytest.approx(47.0, abs=ATOL)
    assert not bool(done) and int(info["termination_reason"]) == 0
    s2, _r, done2, info2 = _step(p, s1)      # no food this step -> metabolism starves it
    assert bool(done2) and int(info2["termination_reason"]) == 2
    assert float(s2.injury_level) == pytest.approx(47.0, abs=ATOL)


def test_B3_6_partial_already_starving_dies_from_metabolism():
    p = _b3("partial")
    out = _body(p, N=0.5, I=50.0)
    assert float(out["injury"]) == pytest.approx(50.0, abs=ATOL)       # h = 0
    assert bool(out["done"]) and bool(out["starved"])
    state, _ = _scene(p, N=0.5, I=50.0)
    _s, _r, done, info = _step(p, state)
    assert bool(done) and int(info["termination_reason"]) == 2


@pytest.mark.parametrize("c,want_n,want_dead", [(1.0, 199.8, False), (0.0, 200.0, True)])
def test_B3_7_auto_eat_overeating_judged_after_the_charge(c, want_n, want_dead):
    base = _controlled()
    base["environment"]["eat_action_enabled"] = False
    base["body"]["healing_nutrition_cost"] = c
    base["body"]["healing_nutrition_shortfall"] = "full"
    p = _p(base)
    assert float(p.food_nutrition_gain) == 6 and float(p.eating_nutrition_cost) == 1.0
    out = _body(p, N=196.0, I=50.0, where="open", ate=True)
    assert float(out["nutrition"]) == pytest.approx(want_n, abs=ATOL)
    assert bool(out["done"]) is want_dead


def test_B3_8_with_metabolic_coupling_drain():
    base = _with(_controlled(), thermal__metabolic_coupling=True,
                 thermal__metabolic_coupling_rate=1.0)
    out = _body(_b3("full", base=base), N=100.0, I=50.0, T=-10.0)
    assert float(out["nutrition"]) == pytest.approx(93.8, abs=ATOL)


def test_B3_9_pays_for_the_B2_slowed_heal():
    base = _with(_controlled(), thermal__healing_cold_sensitivity=0.1)
    out = _body(_b3("full", base=base), N=100.0, I=50.0, T=-5.0)
    assert float(out["nutrition"]) == pytest.approx(96.5, abs=ATOL)


def test_B3_10_damage_step_charges_nothing():
    out = _body(_b3("full"), N=100.0, I=95.0, damage=30.0)
    assert float(out["nutrition"]) == pytest.approx(99.0, abs=ATOL)
    assert float(out["injury"]) == pytest.approx(100.0, abs=ATOL)
    assert bool(out["done"])


def test_B3_11_loader():
    base = _lvl05()
    for flag in ("with_injury", "with_nutrition"):
        d = _with(base, body__healing_nutrition_cost=1.0, **{f"body__{flag}": False})
        with pytest.raises(ValueError, match="healing_nutrition_cost > 0 requires"):
            _p(d)
    with pytest.raises(ValueError, match="healing_nutrition_shortfall must be"):
        _p(_with(base, body__healing_nutrition_cost=1.0,
                 body__healing_nutrition_shortfall="some"))
    d = copy.deepcopy(base)
    del d["body"]["healing_nutrition_cost"]
    with pytest.raises(ValueError, match="body.healing_nutrition_cost"):
        _p(d)
    d = _with(base, body__healing_nutrition_cost=1.0)
    del d["body"]["healing_nutrition_shortfall"]
    with pytest.raises(ValueError, match="body.healing_nutrition_shortfall"):
        _p(d)
    d = copy.deepcopy(base)
    del d["body"]["healing_nutrition_shortfall"]
    assert _p(d).healing_nutrition_cost == 0.0           # not read at c = 0
    for bad in (-1.0, float("nan"), float("inf")):
        with pytest.raises(ValueError, match="healing_nutrition_cost must be finite and >= 0"):
            _p(_with(base, body__healing_nutrition_cost=bad))


# ══════════════════════════════════════════════════════════════════════════════
# B4 — injury speeds heat exchange
# ══════════════════════════════════════════════════════════════════════════════

def _b4(g, mode="cooling_only", scales=None):
    d = _with(_controlled(), thermal__injury_heat_exchange_gain=g,
              thermal__injury_heat_exchange_mode=mode)
    if scales is not None:
        d["thermal"]["warming_rate_scale"], d["thermal"]["cooling_rate_scale"] = scales
    return _p(d)


def _bt(params, I, cell, T=0.0):
    return float(_body(params, I=I, T=T, cell=cell, rested=False)["body_temp"])


@pytest.mark.parametrize("I,want", [(50.0, -0.45), (100.0, -0.60)])
def test_B4_1_cooling_boost(I, want):
    assert _bt(_b4(1.0), I, -30.0) == pytest.approx(want, abs=ATOL)


def test_B4_1_uninjured_is_exactly_gain_zero():
    assert _bt(_b4(1.0), 0.0, -30.0) == _bt(_p(_controlled()), 0.0, -30.0)
    assert _bt(_b4(1.0), 0.0, -30.0) == pytest.approx(-0.30, abs=ATOL)


def test_B4_2_unit_scales():
    assert _bt(_b4(1.0, scales=(1.0, 1.0)), 50.0, -30.0) == pytest.approx(-1.8, abs=ATOL)


def test_B4_3_warm_cell_depends_on_mode():
    g0 = _bt(_p(_controlled()), 50.0, 10.0)
    assert _bt(_b4(1.0, "cooling_only"), 50.0, 10.0) == g0
    assert g0 == pytest.approx(0.8, abs=ATOL)
    assert _bt(_b4(1.0, "both"), 50.0, 10.0) == pytest.approx(1.2, abs=ATOL)


def test_B4_4_settle_point():
    p = _b4(1.0, scales=(1.0, 1.0))
    state, pos = _scene(p, I=100.0, T=0.0, cell=-10.0)
    for _ in range(400):
        out = update_body(state, _info(rested=False), p, pos)
        state = state.replace(body_temp=out[6])
    assert float(state.body_temp) == pytest.approx(-8.0, abs=1e-4)


def test_B4_5_stability_bound_is_a_refusal():
    assert _p(_with(_lvl05(), thermal__injury_heat_exchange_gain=10.9))
    with pytest.raises(ValueError, match="overshoots"):
        _p(_with(_lvl05(), thermal__injury_heat_exchange_gain=11.5))


def _first_step_g(params, g):
    worst = L._thermal_first_fire_step(
        obs_temperature=np.asarray(params.obs_temperature),
        obs_ratio_low=np.asarray(params.obs_temp_ratio_low),
        obs_ratio_high=np.asarray(params.obs_temp_ratio_high),
        res_temperature=np.asarray(params.res_temperature),
        res_ratio_low=np.asarray(params.res_temp_ratio_low),
        res_ratio_high=np.asarray(params.res_temp_ratio_high),
        use_object_sources=True, default_temp_low=params.thermal_default_temp_low,
        default_temp_high=params.thermal_default_temp_high, sigma=params.thermal_sigma,
        kernel_radius=params.thermal_kernel_radius, grid_h=params.height,
        grid_w=params.width, k_exchange=params.thermal_k_exchange,
        k_loss=params.thermal_k_loss, k_metabolic=params.thermal_k_metabolic,
        setpoint=params.temperature_setpoint,
        warming_scale=params.thermal_warming_rate_scale,
        t_high=params.temperature_setpoint,
        k_exchange_boosted=params.thermal_k_exchange * (1.0 + g), boost_mode="both")
    return worst[0]


def _first_step_records(caplog):
    return [r for r in caplog.records
            if r.name == _LOGGER and "worst-case first step onto a fire" in r.getMessage()]


def test_B4_6_both_mode_threshold_is_logged_not_refused(caplog):
    """Revision 3: the 'both'-mode first step is logged (INFO / WARNING), never refused.

    g* is where the loader's own single-fire model puts the first step onto the hottest
    fire exactly at max_temperature; 0.9 g* logs INFO, 1.1 g* logs WARNING and loads.
    """
    p0 = _p(_lvl05())
    lo, hi = 0.0, 2.0
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if _first_step_g(p0, mid) < 15.0 else (lo, mid)
    g_star = 0.5 * (lo + hi)
    print(f"level-05 'both'-mode lethal first-step threshold g* = {g_star:.4f}")
    assert 0.0 < g_star < 0.5                      # table: 11.61 at g=0, 15.18 at g=0.5
    for factor, level in ((0.9, logging.INFO), (1.1, logging.WARNING)):
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=_LOGGER):
            _p(_with(_lvl05(), thermal__injury_heat_exchange_gain=factor * g_star,
                     thermal__injury_heat_exchange_mode="both"))
        recs = _first_step_records(caplog)
        assert len(recs) == 1 and recs[0].levelno == level, (factor, recs)


def _ratio_world(ratio, g, mode):
    d = _with(_lvl05(), thermal__injury_heat_exchange_gain=g,
              thermal__injury_heat_exchange_mode=mode)
    for o in d["environment"]["obstacles"]:
        if o["name"] == "campfire":
            o["temperature_ratio"] = [ratio, ratio]
    return d


def _full_injury_warnings(caplog):
    return [r for r in caplog.records if r.name == _LOGGER and r.levelno == logging.WARNING
            and "at full injury" in r.getMessage()]


def test_B4_7_full_injury_ring_is_logged_per_mode(caplog):
    """Ratio 14: the ring survives at injury 0 (+13.20) but not at full injury in 'both'
    (+15.84). The ring is on the warming side, so 'cooling_only' never boosts it."""
    with caplog.at_level(logging.INFO, logger=_LOGGER):
        _p(_ratio_world(14, 1.0, "cooling_only"))
    assert not _full_injury_warnings(caplog)
    caplog.clear()
    with caplog.at_level(logging.INFO, logger=_LOGGER):
        _p(_ratio_world(14, 1.0, "both"))
    assert _full_injury_warnings(caplog)


def test_B4_8_requires_injury_system():
    with pytest.raises(ValueError, match="requires body.with_injury"):
        _p(_with(_lvl05(), thermal__injury_heat_exchange_gain=1.0, body__with_injury=False))


def test_B4_9_bad_mode():
    with pytest.raises(ValueError, match="injury_heat_exchange_mode must be"):
        _p(_with(_lvl05(), thermal__injury_heat_exchange_gain=1.0,
                 thermal__injury_heat_exchange_mode="sometimes"))


@pytest.mark.parametrize("val", [-0.5, float("nan")])
def test_B4_refuses_negative_and_nan_gain(val):
    with pytest.raises(ValueError, match="injury_heat_exchange_gain must be >= 0"):
        _p(_with(_lvl05(), thermal__injury_heat_exchange_gain=val))


@pytest.mark.parametrize("g", [0.0, 1.0, 2.0])
def test_CP6_level05_structure_holds_in_cooling_only(caplog, g):
    with caplog.at_level(logging.INFO, logger=_LOGGER):
        _p(_with(_lvl05(), thermal__injury_heat_exchange_gain=g))
    assert not _full_injury_warnings(caplog)


# ══════════════════════════════════════════════════════════════════════════════
# B5 — healing speed depends on nutrition
# ══════════════════════════════════════════════════════════════════════════════

def _b5(base=None, **over):
    d = _with(base if base is not None else _controlled(),
              body__healing_nutrition_dependence=True, body__healing_hunger_low=20.0,
              body__healing_hunger_high=100.0, body__healing_hunger_floor=0.2,
              body__healing_overfull_floor=1.0)
    return _p(_with(d, **over))


@pytest.mark.parametrize("N,want", [(10.0, 49.0), (20.0, 49.0), (50.0, 47.5),
                                    (100.0, 45.0), (150.0, 45.0)])
def test_B5_1_hunger_ramp(N, want):
    assert float(_body(_b5(), N=N, I=50.0)["injury"]) == pytest.approx(want, abs=ATOL)


@pytest.mark.parametrize("N,want", [(180.0, 46.5), (150.0, 45.0)])
def test_B5_2_overfull_ramp(N, want):
    p = _b5(body__healing_overfull_floor=0.5, body__healing_overfull_start=150.0)
    assert float(_body(p, N=N, I=50.0)["injury"]) == pytest.approx(want, abs=ATOL)


def test_B5_3_off_is_today_exactly():
    p_off = _p(_controlled())
    for N in (0.0, 10.0, 50.0, 100.0, 180.0, 199.0):
        assert float(_body(p_off, N=N, I=50.0)["injury"]) == 45.0


def test_B5_4_multiplies_with_B2():
    base = _with(_controlled(), thermal__healing_cold_sensitivity=0.1)
    out = _body(_b5(base=base), N=50.0, I=50.0, T=-5.0)
    assert float(out["injury"]) == pytest.approx(48.75, abs=ATOL)


def test_B5_5_B3_pays_for_the_slowed_heal_on_pre_step_nutrition():
    """Factor from nutrition BEFORE this step's decay (50, not 49): heal 2.5, N 46.5."""
    base = _with(_controlled(), body__healing_nutrition_cost=1.0,
                 body__healing_nutrition_shortfall="full")
    out = _body(_b5(base=base), N=50.0, I=50.0)
    assert float(out["injury"]) == pytest.approx(47.5, abs=ATOL)
    assert float(out["nutrition"]) == pytest.approx(46.5, abs=ATOL)


def test_B5_6_loader():
    base = _lvl05()
    d = copy.deepcopy(base)
    del d["body"]["healing_nutrition_dependence"]
    with pytest.raises(ValueError, match="body.healing_nutrition_dependence"):
        _p(d)
    on = dict(body__healing_nutrition_dependence=True)
    bad = [
        (dict(body__healing_hunger_low=100.0, body__healing_hunger_high=100.0), "hunger_low/high"),
        (dict(body__healing_hunger_low=50.0, body__healing_hunger_high=20.0), "hunger_low/high"),
        (dict(body__healing_hunger_high=250.0), "hunger_low/high"),
        (dict(body__healing_hunger_floor=1.5), "healing_hunger_floor"),
        (dict(body__healing_hunger_floor=float("nan")), "healing_hunger_floor"),
        (dict(body__healing_overfull_floor=-0.1), "healing_overfull_floor"),
        (dict(body__healing_overfull_floor=0.5, body__healing_overfull_start=90.0),
         "healing_overfull_start"),
        (dict(body__healing_overfull_floor=0.5, body__healing_overfull_start=200.0),
         "healing_overfull_start"),
        (dict(body__with_nutrition=False), "requires body.with_nutrition"),
        (dict(body__with_injury=False), "requires body.with_nutrition"),
    ]
    for over, msg in bad:
        with pytest.raises(ValueError, match=msg):
            _p(_with(base, **on, **over))
    with pytest.raises(ValueError, match="must be true or false"):
        _p(_with(base, body__healing_nutrition_dependence=1))
    d = _with(base, **on)
    del d["body"]["healing_overfull_start"]
    assert _p(d).healing_nutrition_dependence is True     # not read at overfull_floor 1.0
    d = _with(base, **on, body__healing_overfull_floor=0.5)
    del d["body"]["healing_overfull_start"]
    with pytest.raises(ValueError, match="body.healing_overfull_start"):
        _p(d)


# ══════════════════════════════════════════════════════════════════════════════
# Every key raises when missing inside its read condition (CP6)
# ══════════════════════════════════════════════════════════════════════════════

_MISSING = [
    ("thermal", "random_start_body_temp", {}),
    ("thermal", "start_body_temp_low", {"thermal__random_start_body_temp": True}),
    ("thermal", "start_body_temp_high", {"thermal__random_start_body_temp": True}),
    ("thermal", "healing_cold_sensitivity", {}),
    ("thermal", "healing_warm_sensitivity", {}),
    ("thermal", "injury_heat_exchange_gain", {}),
    ("thermal", "injury_heat_exchange_mode", {"thermal__injury_heat_exchange_gain": 1.0}),
    ("body", "healing_nutrition_cost", {}),
    ("body", "healing_nutrition_shortfall", {"body__healing_nutrition_cost": 1.0}),
    ("body", "healing_nutrition_dependence", {}),
    ("body", "healing_hunger_low", {"body__healing_nutrition_dependence": True}),
    ("body", "healing_hunger_high", {"body__healing_nutrition_dependence": True}),
    ("body", "healing_hunger_floor", {"body__healing_nutrition_dependence": True}),
    ("body", "healing_overfull_floor", {"body__healing_nutrition_dependence": True}),
    ("body", "healing_overfull_start", {"body__healing_nutrition_dependence": True,
                                        "body__healing_overfull_floor": 0.5}),
]


@pytest.mark.parametrize("blk,key,cond", _MISSING, ids=[f"{b}.{k}" for b, k, _ in _MISSING])
def test_missing_key_raises_inside_its_read_condition(blk, key, cond):
    d = _with(_lvl05(), **cond)
    del d[blk][key]
    with pytest.raises(ValueError, match=re.escape(f"{blk}.{key}")):
        _p(d)


# ══════════════════════════════════════════════════════════════════════════════
# B1 / B4 logging (Revision 3: allowed, made visible)
# ══════════════════════════════════════════════════════════════════════════════

def _first_step_value(rec):
    m = re.search(r"-> ([+-]\d+\.\d\d)", rec.getMessage())
    assert m, rec.getMessage()
    return float(m.group(1))


def _b1_c3(d):
    return _with(d, thermal__random_start_body_temp=True,
                 thermal__start_body_temp_low=-10.0, thermal__start_body_temp_high=5.0)


def test_LOG_1_level05_calibration_logs_10_78_at_info(caplog):
    with caplog.at_level(logging.INFO, logger=_LOGGER):
        _p(_b1_c3(_lvl05()))
    recs = _first_step_records(caplog)
    assert len(recs) == 1 and recs[0].levelno == logging.INFO
    assert _first_step_value(recs[0]) == pytest.approx(10.78, abs=0.01)


def test_LOG_2_hot_start_loads_and_warns_15_18(caplog):
    with caplog.at_level(logging.INFO, logger=_LOGGER):
        _p(_with(_b1_c3(_lvl05()), thermal__start_body_temp_high=10.0))
    recs = _first_step_records(caplog)
    assert len(recs) == 1 and recs[0].levelno == logging.WARNING
    assert _first_step_value(recs[0]) == pytest.approx(15.18, abs=0.01)
    assert "allowed by configuration" in recs[0].getMessage()


def test_LOG_3_B1_plus_B4_both_is_one_combined_warning(caplog):
    with caplog.at_level(logging.INFO, logger=_LOGGER):
        _p(_with(_b1_c3(_lvl05()), thermal__injury_heat_exchange_gain=1.0,
                 thermal__injury_heat_exchange_mode="both"))
    recs = _first_step_records(caplog)
    assert len(recs) == 1 and recs[0].levelno == logging.WARNING
    assert "B1" in recs[0].getMessage() and "B4" in recs[0].getMessage()
    assert _first_step_value(recs[0]) == pytest.approx(18.46, abs=0.01)


def test_LOG_4_full_injury_structure_failure_loads_and_warns(caplog):
    with caplog.at_level(logging.INFO, logger=_LOGGER):
        p = _p(_ratio_world(14, 1.0, "both"))
    assert p.thermal_injury_heat_exchange_gain == 1.0
    assert _full_injury_warnings(caplog)


def test_LOG_5_injury_zero_structure_failure_still_raises():
    with pytest.raises(ValueError, match="thermal structure check FAILED"):
        _p(_ratio_world(16, 0.0, "cooling_only"))


# ══════════════════════════════════════════════════════════════════════════════
# Graph identity — the input does not reach the output when the mechanic is off
# (B5 deliberately omitted: see the module docstring)
# ══════════════════════════════════════════════════════════════════════════════

def _reaches(params, in_leaf, out_idx):
    """Does output `out_idx` of the traced update_body depend on state leaf `in_leaf`?

    A jaxpr carries no variable names, so the leaf is located POSITIONALLY in the
    flattened state, and the dependency is found by walking the equations backwards
    from the output variable (an equation depends on all of its inputs).
    """
    state, pos = _scene(params, I=50.0, T=-5.0)
    info = _info()
    leaves = jax.tree_util.tree_flatten_with_path(state)[0]
    idx = next(i for i, (p, _) in enumerate(leaves)
               if jax.tree_util.keystr(p) == f".{in_leaf}")
    closed = jax.make_jaxpr(lambda s: update_body(s, info, params, pos))(state)
    jp = closed.jaxpr
    needed = set()
    out = jp.outvars[out_idx]
    if not type(out).__name__.endswith("Literal"):
        needed.add(out)
    for eqn in reversed(jp.eqns):
        if any(o in needed for o in eqn.outvars):
            needed.update(v for v in eqn.invars if not type(v).__name__.endswith("Literal"))
    return jp.invars[idx] in needed


_OUT_INJURY, _OUT_BODY_TEMP = 2, 6


def test_graph_B2_off_injury_ignores_body_temp():
    assert _reaches(_p(_controlled()), "body_temp", _OUT_INJURY) is False
    assert _reaches(_b2(0.1, 0.0), "body_temp", _OUT_INJURY) is True


def test_graph_B4_off_body_temp_ignores_injury():
    assert _reaches(_p(_controlled()), "injury_level", _OUT_BODY_TEMP) is False
    assert _reaches(_b4(1.0), "injury_level", _OUT_BODY_TEMP) is True
