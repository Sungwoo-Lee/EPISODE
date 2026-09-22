"""Resting inside a bush can heal faster than resting in the open.

**Plain-language summary.** The world contains bushes. A bush already hides the
agent from a hunting predator, and since 2026-09-14 an animal cannot walk into
one at all. This adds a second reason to be in a bush: a setting called
`body.recovery_in_bush_multiplier` that multiplies how much injury a resting
agent heals per step **while it is standing on a concealing bush**. It ships at
`1.0`, which means "no difference at all", so no world the project runs today
behaves any differently because of it.

Because it ships inert, **the inertness proof is the important test in this
file**, not the feature test. The standard it is held to is the same one
`calculate_drive`'s thermal-off path and Stage 5's metabolic coupling are held
to: the gate is a **trace-time Python `if`** on a static `EnvParams` field, so at
`1.0` the multiplier branch is not compiled into the environment's computation
graph at all and the three lines around it are character-for-character the
pre-feature code. That makes bit-parity with every run trained before this key a
property of the *source*, not a number somebody measured once.

`test_multiplier_one_is_graph_identical` is what turns that argument into a
measurement. It traces `update_body` and asks whether the traced graph consumes
the obstacle array `obs_hides_agent` at all — no at `1.0`, yes at `3.0`. A jaxpr
carries no variable *names*, so the leaf is identified **positionally**: flatten
the params pytree, find the index of that array by object identity, and look at
the jaxpr input variable at the same index. Checking only the OFF case would pass
just as happily if the feature had never been wired up, which is why the `3.0`
half is there.

The remaining tests stop the inertness proof from being satisfied by an
implementation that does nothing: the premium must actually fire in a bush, must
inherit the existing "only while resting, and only on a step with no net damage"
condition rather than replacing it, and must **not** make the rest streak depend
on where the agent is standing (decision D2 of the plan — the streak is a
function of the *action* alone, and
`docs/environment/05_body_homeostasis.md` says so).
"""
import os

# Backend pinning MUST precede any jax import — same form as the other
# environment tests in this directory.
os.environ.setdefault("JAX_PLATFORMS", "cpu")

import copy
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

DEFAULT_CONFIG = os.path.join(_ROOT, "configs", "environment", "default.yaml")

KEY = "body.recovery_in_bush_multiplier"
REST = 4            # `jax_step`: rested = rest_action_enabled AND action == 4
MOVES = (0, 1, 2, 3)


def _default_dict():
    with open(DEFAULT_CONFIG) as fh:
        return yaml.safe_load(fh)


def _one_bush_world(multiplier, start_injury=50.0, n_bush=1):
    """A world with a pinned patch of bush, nothing that can hurt the agent, injury live.

    Every choice is load-bearing for the closed-form assertions below:

    * **entities stripped** — a predator or a rabbit would move the agent off the
      cell whose recovery is under test, and a predator would also add damage,
      which the recovery gate deliberately suppresses.
    * **only the food resource kept** — `hiding_predator` deals 15–45 damage on
      contact, and a damaged rest step recovers nothing by design, so leaving it
      in would make the feature test flaky rather than wrong.
    * **the bush patch is pinned to an exact cell range** — so "on the bush" and
      "off the bush" are known cells rather than something to search for. The
      rock entry is dropped as well: it is non-blocking and deals 1–5 damage,
      which is the same hazard as the ambush resource.
    * **injury starts at 50** — recovery is subtractive and clipped at 0, so a
      healthy agent would recover nothing and the test would pass vacuously.

    `n_bush=2` pins two horizontally adjacent bush cells, which is what makes a
    *move* that stays inside cover possible; with a single cell every move action
    leaves the bush and the not-resting branch cannot be isolated.
    """
    d = _default_dict()
    env = d["environment"]
    env["entities"] = []
    env["resources"] = [r for r in env["resources"] if r.get("type") == "food"]
    bush = copy.deepcopy(
        [o for o in env["obstacles"] if o.get("hides_agent")][0])
    bush["count_low"] = int(n_bush)
    bush["count_high"] = int(n_bush)
    bush.pop("count", None)
    bush["area"] = [[3, 3], [3, 2 + int(n_bush)]]
    env["obstacles"] = [bush]
    d["body"]["random_start_injury"] = True
    d["body"]["start_injury_low"] = float(start_injury)
    d["body"]["start_injury_high"] = float(start_injury)
    d["body"][KEY.split(".", 1)[1]] = multiplier
    return d


def _load(d):
    return load_env_params(Config(d))


def _off_bush_cell(state):
    """A cell that is on the grid and is not occupied by any obstacle."""
    taken = {tuple(p) for p in np.array(state.obs_pos)}
    for r in range(1, 9):
        for c in range(1, 9):
            if (r, c) not in taken:
                return jnp.array([r, c], dtype=state.agent_pos.dtype)
    raise AssertionError("no free cell found")


# ══════════════════════════════════════════════════════════════════════════════
# 1. The key is mandatory — no silent fallback
# ══════════════════════════════════════════════════════════════════════════════

def test_missing_key_raises():
    """A config without the key must fail to load, naming the key.

    This is the project's no-fallback-defaults rule at the one place it can be
    enforced. If somebody later gives the read a default of `1.0` "to keep old
    configs working", this test is what says no: a world must state what its
    recovery premium is, because `1.0` and `3.0` are different experiments and a
    config that does not say which one it is cannot be reproduced from its file.
    """
    d = _default_dict()
    assert KEY.split(".", 1)[1] in d["body"], (
        "configs/environment/default.yaml does not ship the key at all — the "
        "rollout was skipped, and this test would pass for the wrong reason")
    d["body"].pop(KEY.split(".", 1)[1])
    with pytest.raises(ValueError) as exc:
        _load(d)
    assert KEY in str(exc.value), (
        f"the error must name the missing key; got: {exc.value}")


def test_shipped_value_is_live_and_a_float():
    """The base settings file ships `25.0`, and it arrives as a Python float.

    The value stopped being inert on 2026-09-22. At the previous `1.0` the
    premium branch was never traced, which is what made runs bit-identical to
    runs predating the key; `25.0` switches that branch on, so the environment's
    computation graph is no longer the pre-feature one. The tuning study behind
    the number is at docs/experiments/active/recovery_in_bush_tuning/ -- at the
    old settings an agent cleared the whole 100-point injury scale resting on
    open ground, so cover had no healing role at all.

    The `float()` on the read is not cosmetic, and that half is unchanged. The
    field is `struct.field(pytree_node=False)`, i.e. part of JAX's trace-cache
    key, and YAML parses a bare `25` as an `int`. Without the coercion a
    curriculum whose stages spell the same value `25` and `25.0` would recompile
    the whole environment between them for no behavioural reason.
    """
    params = _load(_default_dict())
    assert isinstance(params.recovery_in_bush_multiplier, float)
    assert params.recovery_in_bush_multiplier == 25.0
    # An integer in the YAML must still arrive as a float, or the cache key splits.
    d = _default_dict()
    d["body"][KEY.split(".", 1)[1]] = 25
    assert isinstance(_load(d).recovery_in_bush_multiplier, float)
    assert (_load(d).recovery_in_bush_multiplier
            == params.recovery_in_bush_multiplier)


def test_the_inert_regime_is_still_reachable_by_an_explicit_override():
    """`1.0` no longer ships, but a world may still ask for no premium at all.

    Kept as its own case because the untraced branch at exactly 1.0 is what any
    future bit-parity claim against a pre-2026-09-15 run would rest on.
    """
    d = _default_dict()
    d["body"][KEY.split(".", 1)[1]] = 1.0
    assert _load(d).recovery_in_bush_multiplier == 1.0


def test_non_positive_multiplier_raises():
    """Zero or negative is rejected at the point of read.

    A negative multiplier would make resting in cover *inflict* injury, which is
    not a configuration of this feature — it is a different feature nobody asked
    for. Same discipline as the thermal rate constants.
    """
    for bad in (0.0, -1.0):
        d = _default_dict()
        d["body"][KEY.split(".", 1)[1]] = bad
        with pytest.raises(ValueError) as exc:
            _load(d)
        assert KEY in str(exc.value)


# ══════════════════════════════════════════════════════════════════════════════
# 2. The inertness proof — at 1.0 the gate is not in the graph
# ══════════════════════════════════════════════════════════════════════════════

def _obs_hides_agent_is_consumed(params, state, info, new_pos):
    """Does the traced `update_body` graph read `params.obs_hides_agent`?

    A jaxpr carries no variable *names*, so "the graph mentions obs_hides_agent"
    is not directly assertable. It is assertable positionally: `tree_flatten`
    gives the leaves in the same order `make_jaxpr` assigns input variables, so
    the leaf's index is the input variable's index. The leaf is located by object
    **identity**, not equality — several boolean obstacle arrays in `EnvParams`
    have identical contents.

    `obs_hides_agent` is a traced leaf (not `pytree_node=False`), which is what
    puts it in `invars` at all. If that ever changes, rewrite this helper rather
    than delete the test.
    """
    leaves, _ = jax.tree_util.tree_flatten(params)
    idx = next(i for i, leaf in enumerate(leaves)
               if leaf is params.obs_hides_agent)
    jaxpr = jax.make_jaxpr(
        lambda p: update_body(state, info, p, new_pos))(params)
    invar = jaxpr.jaxpr.invars[idx]
    return any(invar in eqn.invars for eqn in jaxpr.jaxpr.eqns)


def _traceable_inputs(params):
    state = jax_reset(params, jax.random.PRNGKey(0))
    info = {
        "ate_food": jnp.array(False),
        "damage": jnp.array(0.0, dtype=jnp.float32),
        "rested": jnp.array(True),
    }
    return state, info, state.obs_pos[0]


def test_multiplier_one_is_graph_identical():
    """At `1.0` the emitted graph never touches the obstacle array; at `3.0` it does.

    The first half is the inertness contract: a trace-time `if` on a static field
    means the multiplier branch does not exist in the compiled environment, so a
    run at `1.0` cannot differ from a run that predates the key even by a
    floating-point rounding step.

    The second half stops that from passing for the wrong reason. A test that only
    checked the OFF case would be equally green if the gate had never been wired
    in at all.
    """
    p_off = _load(_one_bush_world(1.0))
    assert p_off.recovery_in_bush_multiplier == 1.0
    state, info, pos = _traceable_inputs(p_off)
    assert _obs_hides_agent_is_consumed(p_off, state, info, pos) is False, (
        "at multiplier 1.0 the traced update_body graph consumes "
        "obs_hides_agent — the gate is being traced when it should not be, so "
        "the inertness argument is false")

    p_on = _load(_one_bush_world(3.0))
    assert p_on.recovery_in_bush_multiplier == 3.0
    state, info, pos = _traceable_inputs(p_on)
    assert _obs_hides_agent_is_consumed(p_on, state, info, pos) is True, (
        "at multiplier 3.0 the traced update_body graph does NOT consume "
        "obs_hides_agent — the gate was never wired up, and the 1.0 half of "
        "this test is passing vacuously")


# ══════════════════════════════════════════════════════════════════════════════
# 3. The premium is real when switched on
# ══════════════════════════════════════════════════════════════════════════════

def test_premium_applies_in_bush():
    """One rest step on the bush heals exactly 3× one rest step off it.

    Both steps start from the same reset state and the same injury, and the rest
    streak is 1 in both (so the streak's own exponential multiplier is exactly
    1.0 and cannot be confused with the location premium). The only difference is
    the cell the agent stands on.

    Tolerance, not exact equality: the injury delta is a difference of two
    `float32` values around 50, so the recovered 0.1 carries ~4e-5 of relative
    rounding. The ratio is what is under test, and it is asserted to 1e-3.
    """
    params = _load(_one_bush_world(3.0))
    state = jax_reset(params, jax.random.PRNGKey(0))
    bush_cell = state.obs_pos[0]
    assert bool(params.obs_hides_agent[0]) and bool(state.obs_active[0])

    in_state = state.replace(agent_pos=bush_cell)
    out_state = state.replace(agent_pos=_off_bush_cell(state))

    s_in, _, _, info_in = jax_step(in_state, REST, params)
    s_out, _, _, info_out = jax_step(out_state, REST, params)

    assert bool(info_in["agent_in_bush"]) and bool(info_in["rested"])
    assert not bool(info_out["agent_in_bush"]) and bool(info_out["rested"])
    assert float(info_in["damage"]) == 0.0 and float(info_out["damage"]) == 0.0, (
        "the agent took damage — the recovery gate suppresses recovery on a "
        "damaged step, so this comparison would be between two zeros")
    assert int(s_in.rest_streak) == 1 and int(s_out.rest_streak) == 1

    healed_in = float(in_state.injury_level) - float(s_in.injury_level)
    healed_out = float(out_state.injury_level) - float(s_out.injury_level)

    assert healed_out > 0.0, "the control step healed nothing — nothing to scale"
    np.testing.assert_allclose(healed_out, float(params.recovery_base_rate),
                               rtol=1e-3)
    np.testing.assert_allclose(healed_in, 3.0 * healed_out, rtol=1e-3)


def test_premium_requires_rest_and_no_damage():
    """Standing in the bush without resting, and resting there while hurt, heal zero.

    This is the check that the gate went on `recovery_amount` and not on
    `can_recover`. Multiplying the amount inherits the existing "only while
    resting, and only on a step taking no net damage" condition; moving the gate
    to the condition would let an agent collect a premium on a step it was being
    bitten on, which is a different feature.
    """
    # Two adjacent bush cells, so that a *move* can stay inside cover — with one
    # cell every move leaves the bush and (a) would test nothing.
    params = _load(_one_bush_world(3.0, n_bush=2))
    state = jax_reset(params, jax.random.PRNGKey(0))
    bush_cell = state.obs_pos[0]
    in_state = state.replace(agent_pos=bush_cell)

    # (a) In the bush, but not resting.
    moved = None
    for action in MOVES:
        s, _, _, info = jax_step(in_state, action, params)
        if bool(info["agent_in_bush"]) and not bool(info["rested"]):
            moved = (s, info)
            break
    assert moved is not None, (
        "no move action left the agent on a bush cell — cannot test the "
        "not-resting branch on this world")
    s_move, info_move = moved
    assert float(info_move["damage"]) == 0.0
    assert float(s_move.injury_level) == pytest.approx(
        float(in_state.injury_level), abs=1e-5), (
        "injury fell on a step the agent did not rest — the premium is firing "
        "outside the rest condition")

    # (b) In the bush, resting, but taking net damage this step. The damage comes
    # from the injury smoothing buffer rather than from an animal, so the world
    # stays deterministic: `applied_inc = injury_buffer[0]` is what the recovery
    # gate tests, and any positive value there suppresses recovery.
    pending = 0.6
    hurt = in_state.replace(
        injury_buffer=in_state.injury_buffer.at[0].set(pending))
    s_hurt, _, _, info_hurt = jax_step(hurt, REST, params)
    assert bool(info_hurt["agent_in_bush"]) and bool(info_hurt["rested"])
    assert float(info_hurt["damage"]) == 0.0
    # Injury went UP by exactly the buffered slice: no recovery was subtracted,
    # premium or otherwise.
    np.testing.assert_allclose(
        float(s_hurt.injury_level),
        float(hurt.injury_level) + pending, rtol=1e-4)


def test_streak_not_location_dependent():
    """Three rest steps in the open then one in a bush give a streak of 4, not 1.

    Decision D2 of the plan, pinned so a later change has to argue with it.
    `rest_streak` is a persisted state field whose documented contract
    (`docs/environment/05_body_homeostasis.md`, "Streak reset rule") is that it
    depends on the **action** alone. Making it depend on position would change
    `new_rest_streak` — and through it survival — for **every** config, including
    the ones that set this multiplier to `1.0` and thereby opted out of the
    feature entirely. If banking a streak in the open and cashing it in cover
    turns out to matter, that is its own change with its own key and its own
    evidence.
    """
    params = _load(_one_bush_world(3.0))
    state = jax_reset(params, jax.random.PRNGKey(0))
    bush_cell = state.obs_pos[0]
    open_cell = _off_bush_cell(state)

    s = state.replace(agent_pos=open_cell)
    for _ in range(3):
        s, _, _, info = jax_step(s, REST, params)
        assert not bool(info["agent_in_bush"])
    assert int(s.rest_streak) == 3

    s = s.replace(agent_pos=bush_cell)
    s, _, _, info = jax_step(s, REST, params)
    assert bool(info["agent_in_bush"])
    assert int(s.rest_streak) == 4, (
        "the rest streak reset on entering cover — that is a location term in "
        "a field documented to depend only on the action, and it would move "
        "survival for configs sitting at multiplier 1.0")
