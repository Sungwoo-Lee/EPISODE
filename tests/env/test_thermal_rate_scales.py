"""Separate warming and cooling speeds for body temperature.

What this file checks, in plain terms: two settings, `thermal.warming_rate_scale`
and `thermal.cooling_rate_scale`, multiply the body's whole per-step temperature
change — the warming one when the temperature is rising this step, the cooling
one otherwise. Because the WHOLE change is scaled, the temperature the body
finally settles at in any cell does not move; only how fast it gets there does.
Both ship at 1.0, and at 1.0 / 1.0 the environment must be exactly today's.

The tests fall into four groups:

1. **Nothing moved at 1.0 / 1.0** (T01, T02). T01 replays four resting rollouts
   and compares them bit-for-bit with a fixture recorded from the code BEFORE the
   keys existed. T02 shows the scaled branch is absent from the traced graph at
   1.0 / 1.0 and present just above it.
2. **The scaled body is right** (T03-T10), each against a reference that does not
   come from `src/`: hand-computed single steps, a closed-form settling
   temperature, and a two-rate NumPy recurrence written from the plan's equation.
3. **The nutrition drain is deliberately NOT scaled** (T11, plan decision D3).
4. **The loader** (T12, T13) and **a jitted episode** (T14).

**The fixture.** `tests/env/fixtures/thermal_rate_scales/single_rate_rollouts.npz`
is written by `scripts/fixtures/generate_thermal_rate_scale_fixture.py`, run once
with `--src-root` pointed at a worktree of the pre-change commit. **Do not
regenerate it from the working tree**: a fixture recorded from the edited code
agrees with whatever the edited code does, and the byte-identity gate is gone.
Its scenario table, `SEED`, `N_STEPS` and `REST` are duplicated below; change one
and you must change the other.

Plan: docs/develop/active/thermal/WARMING_COOLING_RATE_SCALES.md
"""
import os

# Belt-and-braces with tests/env/conftest.py: the fixture was captured on CPU.
os.environ.setdefault("JAX_PLATFORMS", "cpu")

import copy
import io
import logging
import sys

import numpy as np
import pytest
import yaml

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
sys.path.insert(0, _ROOT)

import jax
import jax.numpy as jnp

from src.utils.config import Config
from src.environment.config_loader import load_env_params
from src.environment.core import jax_reset, jax_step, update_body

# Needed by T14's compile counter; harmless for the rest of this module.
jax.config.update("jax_log_compiles", True)

CAMPFIRE_CONFIG = os.path.join(
    _ROOT, "configs", "environment", "experiment", "archive", "thermal", "campfire_world.yaml")
DEFAULT_CONFIG = os.path.join(_ROOT, "configs", "environment", "default.yaml")
FIXTURE = os.path.join(
    _HERE, "fixtures", "thermal_rate_scales", "single_rate_rollouts.npz")

# ── Duplicated in scripts/fixtures/generate_thermal_rate_scale_fixture.py ─────
SEED = 0
N_STEPS = 150
REST = 4
SCENARIOS = {
    # name: (cell temperature, start body temperature, metabolic coupling on?)
    "warm_off": (10.0, -14.0, False),
    "cool_off": (-10.0, 14.0, False),
    "warm_on": (10.0, -14.0, True),
    "cool_on": (-10.0, 14.0, True),
}
COUPLING_RATE = 1.0
# ─────────────────────────────────────────────────────────────────────────────

# The commit the fixture was captured from (see T01).
PRE_CHANGE_SHA = "1b5d1ed59877fcb4795ee034e79c7b0b87b62ebf"

# T14's action sequence, copied from tests/env/test_metabolic_coupling.py.
ACTIONS = [0, 1, 2, 3, 4, 5, 1, 1, 2, 2] * 30

_REST_INFO = {
    "ate_food": jnp.array(False),
    "damage": jnp.array(0.0, dtype=jnp.float32),
    "rested": jnp.array(True),
}


# ── config helpers ────────────────────────────────────────────────────────────

def _campfire_dict():
    """The live archived campfire world (thermal ON), as a raw dict."""
    with open(CAMPFIRE_CONFIG) as fh:
        d = yaml.safe_load(fh)
    # Archived raw input: not migrated for the water gate (project policy); supplied in memory, `false` = the pre-water world (THIRST_WATER_PLAN).
    d.setdefault("water", {"enabled": False})
    return d


def _uniform(cell, **thermal_overrides):
    """The campfire world with one constant temperature everywhere.

    Same transformation as the fixture generator (itself copied from
    `test_thermal_body.py::_uniform_field_config`): heat sources off, a
    degenerate `default_temp`, and nothing that can end the episode for a
    non-thermal reason. `thermal_overrides` are written into `thermal:`.
    """
    d = copy.deepcopy(_campfire_dict())
    d["thermal"]["use_object_sources"] = False
    d["thermal"]["use_random_spots"] = False
    d["thermal"]["default_temp"] = [float(cell), float(cell)]
    d["environment"]["entities"] = []
    d["environment"]["obstacles"] = [
        o for o in d["environment"]["obstacles"] if o.get("name") == "campfire"]
    d["environment"]["resources"] = [
        r for r in d["environment"]["resources"] if r.get("type") == "food"]
    d["environment"]["max_steps"] = 500
    d["body"]["metabolic_cost"] = 0.0
    d["thermal"].update(thermal_overrides)
    return d


def _scenario_dict(name, **thermal_overrides):
    cell, _t0, coupling = SCENARIOS[name]
    if coupling:
        thermal_overrides = dict(
            thermal_overrides, metabolic_coupling=True, metabolic_coupling_rate=COUPLING_RATE)
    return _uniform(cell, **thermal_overrides)


def _scales(w, c):
    return {"warming_rate_scale": w, "cooling_rate_scale": c}


def _params(d):
    """Load, and check that the two scale fields carry what the dict asked for.

    The fields are read FIRST, before the dict is touched, so that on code without
    the feature the failure is an AttributeError here rather than a KeyError from
    a dict that does not have the keys yet. The check also catches a loader that
    drops or rewrites a value. Every SUCCESSFUL load outside T01 goes through
    here; a load that is expected to raise calls the loader directly (plan D20),
    because on a load that must fail this check is meaningless.
    """
    p = load_env_params(Config(d))
    w, c = p.thermal_warming_rate_scale, p.thermal_cooling_rate_scale
    assert type(w) is float and type(c) is float, (type(w), type(c))
    if d["thermal"]["enabled"]:
        assert w == float(d["thermal"]["warming_rate_scale"]), w
        assert c == float(d["thermal"]["cooling_rate_scale"]), c
    else:
        assert w == 1.0 and c == 1.0, (w, c)
    return p


def _params_raw(d):
    """A plain load with no field check — for T01 only.

    T01's job on the pre-change code is to PASS, showing the fixture matches the
    code it was recorded from; `_params` would make it fail there on purpose.
    """
    return load_env_params(Config(d))


# ── rollouts ──────────────────────────────────────────────────────────────────

def _rest_rollout(params, t0, n=N_STEPS):
    """Mirror of the generator: reset, set the body temperature, rest `n` steps."""
    state = jax_reset(params, jax.random.PRNGKey(SEED))
    state = state.replace(body_temp=jnp.asarray(t0, dtype=state.body_temp.dtype))
    body_temp, nutrition = [np.asarray(state.body_temp)], [np.asarray(state.nutrition)]
    done, reason, ate = [], [], []
    for _ in range(n):
        state, _reward, d, info = jax_step(state, REST, params)
        body_temp.append(np.asarray(state.body_temp))
        nutrition.append(np.asarray(state.nutrition))
        done.append(np.asarray(d))
        reason.append(np.asarray(info["termination_reason"]))
        ate.append(np.asarray(info["ate_food"]))
    return {
        "body_temp": np.stack(body_temp),
        "nutrition": np.stack(nutrition),
        "done": np.stack(done),
        "termination_reason": np.stack(reason),
        "ate_food": np.stack(ate),
    }


def _trace_scan(params, state, info, pos, n):
    def body(bt, _):
        new_bt = update_body(state.replace(body_temp=bt), info, params, pos)[6]
        return new_bt, new_bt
    _, traj = jax.lax.scan(body, state.body_temp, None, length=n)
    return jnp.concatenate([state.body_temp[None], traj])


_trace_jit = jax.jit(_trace_scan, static_argnums=(4,))


def _update_body_trace(params, t0, cell_pos, n):
    """Iterate `update_body` directly with the agent held on `cell_pos`.

    Bypasses `jax_step`, so episode termination cannot freeze the body: this is
    how a settling temperature past the death line (the fire) can be reached.
    Returns the body temperature including the start value, length n + 1.
    """
    state = jax_reset(params, jax.random.PRNGKey(SEED))
    state = state.replace(body_temp=jnp.asarray(t0, dtype=state.body_temp.dtype))
    pos = jnp.asarray(cell_pos, dtype=state.agent_pos.dtype)
    return np.asarray(_trace_jit(params, state, _REST_INFO, pos, n)).astype(np.float64)


def _one_step(params, t0):
    """One `update_body` step at the agent's reset cell; returns the new body temperature."""
    state = jax_reset(params, jax.random.PRNGKey(SEED))
    state = state.replace(body_temp=jnp.asarray(t0, dtype=state.body_temp.dtype))
    return float(update_body(state, _REST_INFO, params, state.agent_pos)[6])


# ── independent references (nothing imported from src/) ──────────────────────

def _oracle(cell, t0, k_ex, k_loss, k_met, setpoint, ws, cs, n):
    """Two-rate float64 recurrence written from the plan's equation."""
    out = [float(t0)]
    t = float(t0)
    for _ in range(n):
        d = k_ex * (cell - t) + k_met - k_loss * (t - setpoint)
        t = t + (ws if d > 0 else cs) * d
        out.append(t)
    return np.array(out)


def _closed_form_T_star(t_field, k_ex, k_loss, k_met, setpoint):
    return (k_ex * t_field + k_loss * setpoint + k_met) / (k_ex + k_loss)


def _thermal_constants(d):
    th = d["thermal"]
    return (float(th["k_exchange"]), float(th["k_loss"]), float(th["k_metabolic"]),
            float(th["temperature_setpoint"]))


def _count_primitives(closed_jaxpr):
    """Primitive-name counts over the jaxpr INCLUDING nested sub-jaxprs.

    `jnp.where` traces as a nested `jit[_where]` whose body holds the `select_n`,
    so a count over the top-level equations alone cannot see it.
    """
    counts = {}

    def walk(jx):
        for eqn in jx.eqns:
            counts[eqn.primitive.name] = counts.get(eqn.primitive.name, 0) + 1
            for v in eqn.params.values():
                for item in (v if isinstance(v, (tuple, list)) else (v,)):
                    if hasattr(item, "jaxpr") and hasattr(item.jaxpr, "eqns"):
                        walk(item.jaxpr)
                    elif hasattr(item, "eqns"):
                        walk(item)

    walk(closed_jaxpr.jaxpr)
    return counts


def _assert_settles_without_crossing(traj, t_star, label, tol=2e-3):
    e = traj - t_star
    assert abs(e[-1]) < tol, f"{label}: final {traj[-1]!r} not within {tol} of T* {t_star!r}"
    s0 = np.sign(e[0])
    far = np.abs(e) >= tol
    assert np.all(np.sign(e[far]) == s0), (
        f"{label}: the body crossed its settling temperature {t_star!r} before "
        f"getting within {tol} of it")


def _assert_non_vacuous_fixture(fx):
    for name in SCENARIOS:
        diffs = np.diff(fx[f"{name}.body_temp"].astype(np.float64))
        if name.startswith("warm"):
            assert int((diffs > 0).sum()) >= 100, f"{name}: fewer than 100 warming steps"
        else:
            assert int((diffs < 0).sum()) >= 100, f"{name}: fewer than 100 cooling steps"
        assert not fx[f"{name}.done"].any(), name
        assert not fx[f"{name}.ate_food"].any(), name
    for kind in ("warm", "cool"):
        assert float(fx[f"{kind}_off.nutrition"][-1]) - float(fx[f"{kind}_on.nutrition"][-1]) > 1.0


def _load_fixture():
    with np.load(FIXTURE) as z:
        return {k: z[k] for k in z.files}


# ══════════════════════════════════════════════════════════════════════════════
# 1. Nothing moved at 1.0 / 1.0
# ══════════════════════════════════════════════════════════════════════════════

def test_single_rate_is_byte_identical_to_pre_change_fixture():
    """T01: the four resting rollouts equal the pre-change recording, bit for bit."""
    fx = _load_fixture()
    _assert_non_vacuous_fixture(fx)
    sha = str(fx["_provenance_sha"])
    # PINNED on purpose. This fixture is evidence only because it was recorded from
    # code that predates the warming/cooling scales. 1b5d1ed5 is that commit (an
    # ancestor of the change whose core.py has no `warming_rate_scale`). A fixture
    # regenerated from the working tree would carry a different SHA and would
    # otherwise pass here silently, agreeing with whatever the edited code does.
    assert sha == PRE_CHANGE_SHA, (
        f"fixture provenance {sha!r} is not the pre-change commit {PRE_CHANGE_SHA!r}; "
        f"it was re-baselined, so byte-identity no longer proves anything")
    expected_keys = {f"{n}.{f}" for n in SCENARIOS
                     for f in ("body_temp", "nutrition", "done", "termination_reason", "ate_food")}
    assert set(fx) - {"_provenance_sha"} == expected_keys
    for name, (_cell, t0, _coupling) in SCENARIOS.items():
        params = _params_raw(_scenario_dict(name))
        got = _rest_rollout(params, t0)
        for field, arr in got.items():
            ref = fx[f"{name}.{field}"]
            assert arr.dtype == ref.dtype and arr.shape == ref.shape, (name, field)
            if not np.array_equal(arr, ref):
                diff = np.max(np.abs(arr.astype(np.float64) - ref.astype(np.float64)))
                pytest.fail(f"{name}.{field} differs from the fixture recorded at {sha}: "
                            f"max |diff| = {diff!r}")


def test_gate_is_off_at_one_and_on_just_above_one():
    """T02: at 1.0 / 1.0 (float or YAML int) the graph is one thing; anything else adds a select."""
    cases = {
        "float_one": (1.0, 1.0), "int_one": (1, 1),
        "warm_up": (1.0, 1.0000001), "cool_up": (1.0000001, 1.0), "half": (0.5, 0.5),
    }
    jaxprs = {}
    state = pos = None
    for label, (w, c) in cases.items():
        d = _campfire_dict()
        d["thermal"].update(_scales(w, c))
        p = _params(d)
        if state is None:
            state = jax_reset(p, jax.random.PRNGKey(SEED))
            pos = state.agent_pos
        jaxprs[label] = jax.make_jaxpr(lambda pp: update_body(state, _REST_INFO, pp, pos))(p)
    base = str(jaxprs["float_one"])
    assert str(jaxprs["int_one"]) == base, "YAML int 1 traced a different graph from 1.0"
    base_counts = _count_primitives(jaxprs["float_one"])
    for label in ("warm_up", "cool_up", "half"):
        assert str(jaxprs[label]) != base, f"{label}: the scaled branch was not traced"
        counts = _count_primitives(jaxprs[label])
        assert counts.get("select_n", 0) > base_counts.get("select_n", 0), (label, counts, base_counts)
        assert counts.get("gt", 0) >= base_counts.get("gt", 0), (label, counts, base_counts)


# ══════════════════════════════════════════════════════════════════════════════
# 2. The scaled body is right
# ══════════════════════════════════════════════════════════════════════════════

def test_equal_non_unit_scales_are_not_todays_behaviour():
    """T03: 0.5 / 0.5 is a uniform slow-down, not the single-rate body."""
    fx = _load_fixture()
    for name in ("warm_off", "cool_off"):
        cell, t0, _ = SCENARIOS[name]
        d = _scenario_dict(name, **_scales(0.5, 0.5))
        bt = _rest_rollout(_params(d), t0)["body_temp"].astype(np.float64)
        assert np.max(np.abs(bt - fx[f"{name}.body_temp"])) > 1e-2, name
        ref = _oracle(cell, t0, *_thermal_constants(d), 0.5, 0.5, N_STEPS)
        np.testing.assert_allclose(bt, ref, atol=2e-4, rtol=0, err_msg=name)


def _field_cells(state):
    field = np.asarray(state.thermal_field)
    fire = np.unravel_index(int(np.argmax(field)), field.shape)
    ring = None
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        r, c = fire[0] + dr, fire[1] + dc
        if 0 <= r < field.shape[0] and 0 <= c < field.shape[1]:
            ring = (int(r), int(c))
            break
    assert ring is not None
    return field, (int(fire[0]), int(fire[1])), ring


def test_equilibrium_unchanged_from_above_and_below_ring_and_fire():
    """T04: settling temperatures on the ring and the fire do not depend on the scales."""
    pairs = [(1.0, 1.0), (3.0, 0.3), (0.3, 3.0)]
    n = 4000
    loaded = {}
    for pr in pairs:
        d = _campfire_dict()
        d["thermal"].update(_scales(*pr))
        loaded[pr] = (d, _params(d))
    d0, p0 = loaded[(1.0, 1.0)]
    field, fire, ring = _field_cells(jax_reset(p0, jax.random.PRNGKey(SEED)))
    k_ex, k_loss, k_met, setpoint = _thermal_constants(d0)
    offsets = {"ring": (-22.0, 14.0), "fire": (-40.0, 15.0)}
    for cell_name, cell_pos in (("ring", ring), ("fire", fire)):
        t_star = _closed_form_T_star(float(field[cell_pos]), k_ex, k_loss, k_met, setpoint)
        print(f"T04 {cell_name} cell {cell_pos}: field {float(field[cell_pos]):.4f}, T* {t_star:.4f}")
        trajs = {}
        for pr in pairs:
            _d, p = loaded[pr]
            for side, off in zip(("below", "above"), offsets[cell_name]):
                traj = _update_body_trace(p, t_star + off, cell_pos, n)
                label = f"{cell_name} {pr} from {side}"
                _assert_settles_without_crossing(traj, t_star, label)
                trajs[(pr, side)] = traj
            assert abs(trajs[(pr, "below")][-1] - trajs[(pr, "above")][-1]) < 2e-3, (cell_name, pr)
        for pr in pairs[1:]:
            for side in ("below", "above"):
                assert abs(trajs[(pr, side)][-1] - trajs[((1.0, 1.0), side)][-1]) < 2e-3, (cell_name, pr, side)
                # Discriminator: the scale was actually applied.
                assert np.max(np.abs(trajs[(pr, side)] - trajs[((1.0, 1.0), side)])) > 1e-2, (
                    f"{cell_name} {pr} from {side}: trajectory equals the 1.0/1.0 one")


def test_equilibrium_unchanged_at_extreme_ratio_and_general_fixed_point():
    """T05: ratio 100 with a nonzero k_metabolic and setpoint; the fast side sits on the bound."""
    n = 4000
    pairs = [(1.0, 1.0), (20.0, 0.2), (0.2, 20.0)]
    over = dict(k_metabolic=0.3, temperature_setpoint=5.0)
    loaded = {pr: _params(_uniform(-10.0, **over, **_scales(*pr))) for pr in pairs}
    d0 = _uniform(-10.0, **over, **_scales(1.0, 1.0))
    k_ex, k_loss, k_met, setpoint = _thermal_constants(d0)
    state = jax_reset(loaded[(1.0, 1.0)], jax.random.PRNGKey(SEED))
    cell_pos = tuple(int(x) for x in np.asarray(state.agent_pos))
    t_field = float(np.asarray(state.thermal_field)[cell_pos])
    t_star = _closed_form_T_star(t_field, k_ex, k_loss, k_met, setpoint)
    trajs = {}
    for pr in pairs:
        for side, off in (("below", -12.0), ("above", 12.0)):
            traj = _update_body_trace(loaded[pr], t_star + off, cell_pos, n)
            _assert_settles_without_crossing(traj, t_star, f"{pr} from {side}")
            trajs[(pr, side)] = traj
        assert abs(trajs[(pr, "below")][-1] - trajs[(pr, "above")][-1]) < 2e-3, pr
    for pr in pairs[1:]:
        for side in ("below", "above"):
            assert abs(trajs[(pr, side)][-1] - trajs[((1.0, 1.0), side)][-1]) < 2e-3, (pr, side)
            assert np.max(np.abs(trajs[(pr, side)] - trajs[((1.0, 1.0), side)])) > 1e-2, (pr, side)


def test_whole_step_scaled_with_zero_exchange():
    """T06: with k_exchange = 0 the k_loss term alone is still scaled."""
    d = _uniform(-10.0, k_exchange=0.0, k_loss=0.05, k_metabolic=0.0,
                 temperature_setpoint=0.0, **_scales(1.0, 0.5))
    got = _one_step(_params(d), 10.0)
    assert got == pytest.approx(9.75, abs=1e-5)
    assert abs(got - 9.5) > 1e-3, "only k_exchange was scaled (or nothing was)"


def test_whole_step_scaled_with_metabolic_heat():
    """T07: k_metabolic is part of the scaled step, alone and with both other terms."""
    d = _uniform(0.0, k_exchange=0.0, k_loss=0.05, k_metabolic=0.3,
                 temperature_setpoint=0.0, **_scales(2.0, 1.0))
    assert _one_step(_params(d), 0.0) == pytest.approx(0.6, abs=1e-5)

    ws, cs = 2.0, 0.5
    cell, k_ex, k_loss, k_met, setpoint = -10.0, 0.04, 0.01, 0.3, 2.0
    d = _uniform(cell, k_exchange=k_ex, k_loss=k_loss, k_metabolic=k_met,
                 temperature_setpoint=setpoint, **_scales(ws, cs))
    p = _params(d)
    for t0 in (-12.0, 12.0):
        step = k_ex * (cell - t0) + k_met - k_loss * (t0 - setpoint)
        assert step != 0.0 and abs(k_ex * (cell - t0)) > 0 and abs(k_loss * (t0 - setpoint)) > 0
        hand = t0 + (ws if step > 0 else cs) * step
        assert _one_step(p, t0) == pytest.approx(hand, abs=1e-5), t0


def test_scale_is_chosen_by_sign_of_the_step():
    """T08: the branch follows this step's direction, not the setpoint or the cell."""
    ws, cs = 3.0, 0.5
    d = _uniform(-10.0, k_exchange=0.04, k_loss=0.01, k_metabolic=0.0,
                 temperature_setpoint=0.0, **_scales(ws, cs))
    p = _params(d)
    # Below T* = -8: warming.
    assert _one_step(p, -14.0) == pytest.approx(-13.1, abs=1e-5)
    assert abs(_one_step(p, -14.0) - (-13.85)) > 1e-3
    # Below the setpoint and above the cell, yet above T*: cooling.
    assert _one_step(p, -2.0) == pytest.approx(-2.15, abs=1e-5)
    assert abs(_one_step(p, -2.0) - (-2.9)) > 1e-3
    # Above everything: cooling.
    hand = 14.0 + cs * (0.04 * (-10.0 - 14.0) - 0.01 * (14.0 - 0.0))
    assert _one_step(p, 14.0) == pytest.approx(hand, abs=1e-5)


def test_zero_step_stays_put():
    """T09: at d == 0 exactly (cooling branch by definition) the body does not move.

    Documents the branch; it cannot discriminate it, since s * 0 == 0 either way.
    """
    d = _uniform(-8.0, k_exchange=0.5, k_loss=0.5, k_metabolic=0.0,
                 temperature_setpoint=0.0, **_scales(1.0, 0.5))
    assert _one_step(_params(d), -4.0) == -4.0


def test_scaled_rollouts_match_two_rate_oracle():
    """T10: whole resting trajectories at (3.0, 0.3) follow the two-rate recurrence."""
    fx = _load_fixture()
    for name, (cell, t0, _) in SCENARIOS.items():
        d = _scenario_dict(name, **_scales(3.0, 0.3))
        bt = _rest_rollout(_params(d), t0)["body_temp"].astype(np.float64)
        ref = _oracle(cell, t0, *_thermal_constants(d), 3.0, 0.3, N_STEPS)
        np.testing.assert_allclose(bt, ref, atol=2e-4, rtol=0, err_msg=name)
        assert np.max(np.abs(bt - fx[f"{name}.body_temp"])) > 1e-2, name


# ══════════════════════════════════════════════════════════════════════════════
# 3. The drain is not scaled (plan D3)
# ══════════════════════════════════════════════════════════════════════════════

def test_metabolic_drain_is_not_scaled():
    """T11: nutrition pays rate * |k_loss * (T - setpoint)| per step, whatever the scales."""
    fx = _load_fixture()
    ws, cs = 3.0, 0.3
    for name in ("warm_on", "cool_on"):
        cell, t0, _ = SCENARIOS[name]
        d = _scenario_dict(name, **_scales(ws, cs))
        roll = _rest_rollout(_params(d), t0)
        assert not roll["ate_food"].any(), f"{name}: agent ate, so the drain formula does not apply"
        bt = roll["body_temp"].astype(np.float64)
        nu = roll["nutrition"].astype(np.float64)
        k_ex, k_loss, k_met, setpoint = _thermal_constants(d)
        rate = float(d["thermal"]["metabolic_coupling_rate"])
        max_nu = float(d["body"]["max_nutrition"])
        assert float(d["body"]["metabolic_cost"]) == 0.0
        work = np.abs(k_loss * (bt[:-1] - setpoint))
        expected = np.clip(nu[:-1] - rate * work, 0.0, max_nu)
        np.testing.assert_allclose(nu[1:], expected, atol=1e-4, rtol=0, err_msg=name)
        step = k_ex * (cell - bt[:-1]) + k_met - k_loss * (bt[:-1] - setpoint)
        scale = np.where(step > 0, ws, cs)
        scaled_alt = np.clip(nu[:-1] - scale * rate * work, 0.0, max_nu)
        assert np.max(np.abs(nu[1:] - scaled_alt)) > 1e-2, (
            f"{name}: cannot tell the unscaled drain from the scaled one")
        assert np.max(np.abs(bt - fx[f"{name}.body_temp"])) > 1e-2, (
            f"{name}: body temperature equals the single-rate fixture, so no scale was applied")


# ══════════════════════════════════════════════════════════════════════════════
# 4. Loader and jitted episode
# ══════════════════════════════════════════════════════════════════════════════

def test_conditional_mandatory():
    """T12: thermal-off loads without the keys; thermal-on without either one raises."""
    # (a) thermal off, keys absent -> loads, inert 1.0 / 1.0.
    with open(DEFAULT_CONFIG) as fh:
        d = yaml.safe_load(fh)
    assert d["thermal"]["enabled"] is False
    for key in ("warming_rate_scale", "cooling_rate_scale"):
        d["thermal"].pop(key, None)
    _params(d)
    # (b), (c) thermal on, one key missing -> ValueError naming it. Loader called directly (D20).
    for key in ("warming_rate_scale", "cooling_rate_scale"):
        d = _campfire_dict()
        d["thermal"].pop(key, None)
        with pytest.raises(ValueError) as exc:
            load_env_params(Config(d))
        assert f"thermal.{key}" in str(exc.value), str(exc.value)
    # (d) YAML int 1 for both -> float 1.0.
    d = _campfire_dict()
    d["thermal"].update(_scales(1, 1))
    p = _params(d)
    assert p.thermal_warming_rate_scale == 1.0 and p.thermal_cooling_rate_scale == 1.0


def test_stability_and_positivity_checks_fire_per_key():
    """T13: each scale is checked on its own; the existing k_exchange + k_loss check stays."""
    base = dict(k_exchange=0.25, k_loss=0.25)          # K = 0.5 exactly
    # (1) warming over the per-scale bound.
    with pytest.raises(ValueError) as exc:
        load_env_params(Config(_uniform(-10.0, **base, **_scales(2.001, 1.0))))
    msg = str(exc.value)
    assert "thermal.warming_rate_scale" in msg and "cooling" not in msg, msg
    # (2) the mirror.
    with pytest.raises(ValueError) as exc:
        load_env_params(Config(_uniform(-10.0, **base, **_scales(1.0, 2.001))))
    msg = str(exc.value)
    assert "thermal.cooling_rate_scale" in msg and "warming" not in msg, msg
    # (3) not strictly positive, NaN included.
    for key in ("warming_rate_scale", "cooling_rate_scale"):
        for bad in (0.0, -1.0, float("nan")):
            sc = _scales(1.0, 1.0)
            sc[key] = bad
            with pytest.raises(ValueError) as exc:
                load_env_params(Config(_uniform(-10.0, **base, **sc)))
            assert f"thermal.{key}" in str(exc.value), (key, bad, str(exc.value))
    # (4) the pre-existing k_exchange + k_loss <= 1 check, even with small scales.
    with pytest.raises(ValueError) as exc:
        load_env_params(Config(_uniform(-10.0, k_exchange=0.6, k_loss=0.6, **_scales(0.5, 0.5))))
    assert "thermal.k_exchange + thermal.k_loss must be <= 1" in str(exc.value), str(exc.value)
    # (5) last: exactly on the bound loads.
    p = _params(_uniform(-10.0, **base, **_scales(2.0, 1.0)))
    assert p.thermal_warming_rate_scale == 2.0


class _CompileCounter:
    """Counts 'Compiling jit(jax_step)' log records.

    Copied from tests/env/test_no_recompile.py (not imported from another test module).
    """

    def __init__(self):
        self._buf = io.StringIO()
        self._handler = logging.StreamHandler(self._buf)
        self._handler.setLevel(logging.WARNING)
        self._logger = logging.getLogger("jax._src.interpreters.pxla")
        self._original_level = self._logger.level

    def __enter__(self):
        self._buf.truncate(0)
        self._buf.seek(0)
        self._logger.addHandler(self._handler)
        self._logger.setLevel(logging.WARNING)
        return self

    def __exit__(self, *args):
        self._logger.removeHandler(self._handler)
        self._logger.setLevel(self._original_level)

    @property
    def count(self) -> int:
        return self._buf.getvalue().count("Compiling jit(jax_step)")


def _episode_body_temps(params):
    state = jax_reset(params, jax.random.PRNGKey(SEED))
    temps = []
    for action in ACTIONS:
        state, _r, _d, _info = jax_step(state, action, params)
        temps.append(state.body_temp)
    return state, temps


def test_jitted_episode_unequal_scales_no_nan_no_recompile():
    """T14: a jitted campfire episode at (3.0, 0.3) compiles once and stays finite."""
    d = _campfire_dict()
    d["thermal"].update(_scales(3.0, 0.3))
    params = _params(d)
    jax.clear_caches()
    with _CompileCounter() as counter:
        state = jax_reset(params, jax.random.PRNGKey(SEED))
        state, _r, _d, _info = jax_step(state, ACTIONS[0], params)
        assert counter.count == 1, counter.count
        temps = [state.body_temp]
        for action in ACTIONS[1:]:
            state, _r, _d, _info = jax_step(state, action, params)
            temps.append(state.body_temp)
        assert counter.count == 1, counter.count
    assert all(t.dtype == jnp.float32 for t in temps)
    scaled = np.array([float(t) for t in temps])
    assert np.all(np.isfinite(scaled))
    assert np.all(np.isfinite(np.asarray(state.thermal_field)))
    # Discriminator, outside the counter (a different static configuration compiles on its own).
    d1 = _campfire_dict()
    d1["thermal"].update(_scales(1.0, 1.0))
    _s, temps1 = _episode_body_temps(_params(d1))
    single = np.array([float(t) for t in temps1])
    assert np.max(np.abs(scaled - single)) > 1e-2, "the (3.0, 0.3) episode equals the single-rate one"
