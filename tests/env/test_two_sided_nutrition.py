"""Nutrition as a TWO-SIDED homeostatic axis (2026-09-22).

Plain English first. Until 2026-09-22 the body's food axis only had one bad end.
Nutrition ran from 0 to 100, the "target" the agent was rewarded for reaching was
100 — the very top — and only running out killed you. So more food was always
better and there was nothing to regulate: the agent just had to keep the tank
full. This change moves the target to the MIDDLE of a range twice as wide
(0..200, target 100) and makes BOTH ends lethal, so eating too much is now as bad
as eating too little and the agent has to hold a level rather than maximise one.

Three separate things had to be true for that to work, and this module checks
each of them:

1. **`range_S`** — "how far can the food level get from its target" — used to be
   the same number as the ceiling, purely because the target WAS the ceiling.
   Anything that measured deviation with the ceiling has to switch to `range_S`,
   and that switch must change nothing at all for every world that existed
   before today (`satiation_setpoint == max_satiation`, so `range_S` is still the
   ceiling). That backward-compatibility claim is the first group of tests.
2. **The drive** (the quantity whose fall IS the reward) must read zero exactly
   at the target and give the same penalty for being equally far above it as
   below it.
3. **Over-eating must actually end the episode.** The `body.overeating_death`
   key existed since long before this change but did nothing except write a
   "died of over-eating" label onto steps the agent survived (KNOWN_BUGS, "Env
   doc-audit latent findings", open since 2026-06-09). It now ends the episode
   and pays the death penalty, exactly the way starvation does.
"""
import os

os.environ.setdefault("JAX_PLATFORMS", "cpu")

import copy
import sys

import numpy as np
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
sys.path.insert(0, _ROOT)

import jax
import jax.numpy as jnp

from src.utils.config import Config
from src.environment.config_loader import load_env_params, _resolve_extends
from src.environment.core import (
    calculate_drive,
    jax_reset,
    jax_step,
    satiation_deviation_range,
)

_DEFAULT = os.path.join(_ROOT, "configs", "environment", "default.yaml")


def _params(**overrides):
    """Live `default.yaml`, resolved through `extends:`, with dotted overrides."""
    cfg = _resolve_extends(_DEFAULT, frozenset())
    for k, v in overrides.items():
        cfg.set(k, v)
    return load_env_params(cfg)


# ── 1. range_S: the deviation scale, and its backward compatibility ───────────

@pytest.mark.parametrize("ceiling", [100.0, 50.0, 200.0, 1.0])
def test_range_S_is_exactly_the_ceiling_when_the_setpoint_is_the_ceiling(ceiling):
    """The no-op gate for the thermal-axis rescale.

    Every config that predates the two-sided axis sets the target AT the top of
    the range. There `max(setpoint - 0, ceiling - setpoint) == ceiling`, so the
    new expression must return the old number — not approximately, bit-for-bit,
    because it is multiplied into a reward.
    """
    p = _params(**{"body.max_satiation": ceiling,
                   "body.satiation_setpoint": ceiling,
                   "body.max_nutrition": ceiling,
                   "body.start_nutrition": ceiling,
                   "body.start_satiation": ceiling,
                   "body.start_nutrition_high": ceiling})
    got = np.asarray(satiation_deviation_range(p), dtype=np.float32)
    assert got.tobytes() == np.float32(ceiling).tobytes()


def test_range_S_is_half_the_ceiling_at_a_middle_setpoint():
    """The shipped two-sided world: 0..200 with the target at 100."""
    p = _params()
    assert float(p.max_satiation) == 200.0
    assert float(p.setpoint) == 100.0
    assert float(satiation_deviation_range(p)) == 100.0


def test_range_S_takes_the_larger_arm_when_the_setpoint_is_off_centre():
    """Not "half the ceiling" — the FURTHEST the axis can get from target."""
    p = _params(**{"body.max_satiation": 200.0, "body.satiation_setpoint": 40.0,
                   "body.max_nutrition": 200.0, "body.start_nutrition": 40.0,
                   "body.start_satiation": 40.0, "body.start_nutrition_high": 200.0})
    # below: 40 - 0 = 40; above: 200 - 40 = 160  ->  160
    assert float(satiation_deviation_range(p)) == 160.0


def test_thermal_axis_factor_is_bit_identical_at_a_ceiling_setpoint():
    """2b must be a no-op for every pre-existing config.

    The thermal drive axis is scaled by `range_S / max_temperature` where it used
    to be scaled by `max_satiation / max_temperature`. With the setpoint at the
    ceiling those are the same number, so the whole drive must come out with the
    same bits as an explicit recomputation of the OLD expression.
    """
    p = _params(**{"thermal.enabled": True,
                   "body.max_satiation": 100.0, "body.satiation_setpoint": 100.0,
                   "body.max_nutrition": 100.0, "body.start_nutrition": 100.0,
                   "body.start_satiation": 100.0, "body.start_nutrition_high": 100.0})
    assert bool(p.thermal_enabled)
    for sat, inj, bt in [(100.0, 0.0, 0.0), (37.0, 12.5, -18.25), (0.0, 100.0, 9.75)]:
        s, i, t = jnp.float32(sat), jnp.float32(inj), jnp.float32(bt)
        got = np.asarray(calculate_drive(s, i, p, t), dtype=np.float32)
        # The OLD expression, written out here rather than imported.
        t_axis = (t - p.temperature_setpoint) * (p.max_satiation / p.max_temperature)
        want = np.asarray(
            jnp.linalg.norm(jnp.stack([s, i, t_axis]) - jnp.array([p.setpoint, 0.0, 0.0])),
            dtype=np.float32)
        assert got.tobytes() == want.tobytes(), f"sat={sat} inj={inj} bt={bt}"


def test_thermal_axis_factor_halves_at_the_shipped_two_sided_world():
    """The defect 2b prevents, stated as the contrast case.

    At ceiling 200 / setpoint 100 the OLD expression would weigh one degree of
    temperature at 200/15 satiation units; the corrected one weighs it at
    100/15 — exactly half. If this test ever reports the two as equal, the
    rescale has been reverted.
    """
    p = _params(**{"thermal.enabled": True})
    new = float(satiation_deviation_range(p) / p.max_temperature)
    old = float(p.max_satiation / p.max_temperature)
    assert new == pytest.approx(old / 2.0)


def test_thermal_axis_uses_range_S_not_the_ceiling_at_a_middle_setpoint():
    """The DISCRIMINATING test for 2b, and the one that must fail on old code.

    The two tests above are both satisfied by an implementation that never
    changed: at a ceiling setpoint the old and new factors are the same number,
    and the third one only exercises the helper. This one runs the real
    `calculate_drive` in the shipped two-sided world and asserts it agrees with
    the `range_S` factor and DISAGREES with the ceiling factor.
    """
    p = _params(**{"thermal.enabled": True})
    assert float(p.max_satiation) == 200.0 and float(p.setpoint) == 100.0
    s, i, t = jnp.float32(p.setpoint), jnp.float32(0.0), jnp.float32(-20.0)
    got = float(calculate_drive(s, i, p, t))

    def drive_with(factor):
        t_axis = (t - p.temperature_setpoint) * factor
        return float(jnp.linalg.norm(
            jnp.stack([s, i, t_axis]) - jnp.array([p.setpoint, 0.0, 0.0])))

    want_new = drive_with(satiation_deviation_range(p) / p.max_temperature)
    want_old = drive_with(p.max_satiation / p.max_temperature)
    assert want_new != pytest.approx(want_old), "the two factors must differ here"
    assert got == pytest.approx(want_new, rel=1e-6)
    assert got != pytest.approx(want_old, rel=1e-3)


# ── 2. the drive is zero at target and symmetric about it ────────────────────

def test_drive_is_zero_at_the_setpoint():
    """Injury 0, thermal off: a perfectly regulated body has no drive at all."""
    p = _params()
    d = float(calculate_drive(jnp.float32(p.setpoint), jnp.float32(0.0), p))
    assert d == 0.0


def test_drive_is_symmetric_about_the_setpoint():
    """50 below target and 50 above it must cost the same, and must cost."""
    p = _params()
    sp = float(p.setpoint)
    lo = float(calculate_drive(jnp.float32(sp - 50.0), jnp.float32(0.0), p))
    hi = float(calculate_drive(jnp.float32(sp + 50.0), jnp.float32(0.0), p))
    assert lo == hi
    assert lo > 0.0


def test_logged_drive_hunger_is_zero_at_target_and_symmetric():
    """`info['drive_hunger']` is a DIAGNOSTIC, and it was one-sided.

    At the shipped world a perfectly regulated agent used to log 0.25 (distance
    from the ceiling) instead of 0, and an agent eating itself to death logged a
    falling hunger drive. Measured through a real step rather than by
    re-deriving the formula.
    """
    p = _params()
    key = jax.random.PRNGKey(0)
    state = jax_reset(p, key)
    sp, rng = float(p.setpoint), float(satiation_deviation_range(p))

    def hunger_at(nutrition):
        # metabolic_cost is subtracted inside the step, so aim one cost high.
        st = state.replace(nutrition=jnp.float32(nutrition + float(p.metabolic_cost)))
        _, _, _, info = jax_step(st, 4, p)  # rest: no movement, no eating
        return float(info["drive_hunger"]), float(info["termination_reason"])

    at_target, _ = hunger_at(sp)
    below, _ = hunger_at(sp - 40.0)
    above, _ = hunger_at(sp + 40.0)
    assert at_target == pytest.approx(0.0, abs=1e-6)
    assert below == pytest.approx((40.0 / rng) ** 2, rel=1e-5)
    assert above == pytest.approx(below, rel=1e-5)


def test_logged_drive_hunger_is_bit_identical_to_the_old_formula_at_a_ceiling_setpoint():
    """The ULP gate for 2c, and it is not pedantry.

    `info['drive_hunger']` is compared byte-for-byte against fixtures captured
    before the two-sided axis existed (tests/env/test_metabolic_coupling.py). The
    obvious rewrite `((S - setpoint) / range_S) ** 2` is algebraically the old
    `(1 - S / max_satiation) ** 2` when the setpoint is the ceiling, but rounds
    differently, and not just at one unlucky value: sweeping every float32
    satiation on a 0.01 grid across 11 ceilings (`math-reviewer`, 2026-09-22)
    put 10,588-12,607 of the 22,001 values per ceiling — roughly HALF the axis —
    up to 2 ULP apart. The shipped form divides first so `setpoint / range_S` is
    exactly 1.0 there.
    """
    p = _params(**{"body.max_satiation": 100.0, "body.satiation_setpoint": 100.0,
                   "body.max_nutrition": 100.0, "body.start_nutrition": 100.0,
                   "body.start_satiation": 100.0, "body.start_nutrition_high": 100.0})
    rng = satiation_deviation_range(p)
    for sat in [0.0, 1.0, 7.0, 33.0, 37.0, 64.0, 99.0, 100.0]:
        s = jnp.float32(sat)
        new = np.asarray(jnp.power((s / rng) - (p.setpoint / rng), 2), dtype=np.float32)
        old = np.asarray(jnp.power(1.0 - (s / p.max_satiation), 2), dtype=np.float32)
        assert new.tobytes() == old.tobytes(), f"satiation={sat}"


# ── 3. eating past the setpoint is punished ──────────────────────────────────

def _put_food_under_agent(state, p):
    """Switch every resource off, then park one FOOD slot on the agent's cell."""
    food_slots = np.flatnonzero(np.asarray(p.res_type) == 0)
    assert food_slots.size > 0, "config has no food resource"
    i = int(food_slots[0])
    res_pos = state.res_pos.at[i].set(state.agent_pos)
    res_active = jnp.zeros_like(state.res_active).at[i].set(True)
    return state.replace(res_pos=res_pos, res_active=res_active,
                         animal_active=jnp.zeros_like(state.animal_active))


def test_eating_at_the_setpoint_is_punished():
    """Reward is `prev_drive - curr_drive`; eating at target moves AWAY from it.

    Nothing in this test is new code: the punishment falls out of the existing
    two-sided `calculate_drive`, which already read `params.setpoint`. The
    assertion at the end checks exactly that — the reward equals the drive
    difference, so it cannot have come from anything added for this change.
    """
    p = _params()
    state = jax_reset(p, jax.random.PRNGKey(3))
    state = _put_food_under_agent(state, p)
    state = state.replace(nutrition=jnp.float32(p.setpoint),
                          satiation=jnp.float32(p.setpoint),
                          injury_level=jnp.float32(0.0))
    eat_action = 5 if bool(p.rest_action_enabled) else 4
    new_state, reward, done, info = jax_step(state, eat_action, p)

    assert bool(info["ate_food"]), "the eat action did not consume the food"
    assert float(new_state.nutrition) > float(p.setpoint), "the agent did not overeat"
    assert float(reward) < 0.0, f"eating at the setpoint paid {float(reward)}"
    assert not bool(done)

    prev_drive = float(calculate_drive(state.satiation, state.injury_level, p))
    curr_drive = float(calculate_drive(new_state.satiation, new_state.injury_level, p))
    assert float(reward) == pytest.approx(prev_drive - curr_drive, abs=1e-5)


def test_eating_while_hungry_is_still_rewarded():
    """The contrast case: the punishment is about the SETPOINT, not about eating."""
    p = _params()
    state = jax_reset(p, jax.random.PRNGKey(3))
    state = _put_food_under_agent(state, p)
    state = state.replace(nutrition=jnp.float32(float(p.setpoint) - 50.0),
                          satiation=jnp.float32(float(p.setpoint) - 50.0),
                          injury_level=jnp.float32(0.0))
    eat_action = 5 if bool(p.rest_action_enabled) else 4
    _, reward, _, _ = jax_step(state, eat_action, p)
    assert float(reward) > 0.0


# ── 4. over-eating actually ends the episode ─────────────────────────────────

def test_overeating_ends_the_episode_with_reason_3_and_the_death_penalty():
    """The regression test for the no-op `body.overeating_death`.

    Pre-fix this FAILS on `done`: the key set termination reason 3 and never
    touched `done`, so the episode carried on and the death penalty never fired.
    Mirrors starvation exactly — same `done`, same `real_death` gate, same
    penalty.
    """
    p = _params()
    assert bool(p.overeating_death), "default.yaml must ship overeating_death: true"
    state = jax_reset(p, jax.random.PRNGKey(5))
    state = _put_food_under_agent(state, p)
    # One eat (net +gain-cost, minus one metabolic_cost) lands on / past the ceiling.
    net = float(p.food_nutrition_gain) - float(p.eating_nutrition_cost) - float(p.metabolic_cost)
    state = state.replace(nutrition=jnp.float32(float(p.max_nutrition) - net),
                          satiation=jnp.float32(float(p.max_nutrition) - net),
                          injury_level=jnp.float32(0.0))
    eat_action = 5 if bool(p.rest_action_enabled) else 4
    new_state, reward, done, info = jax_step(state, eat_action, p)

    assert float(new_state.nutrition) >= float(p.max_nutrition)
    assert bool(done), "over-eating did not end the episode"
    assert int(info["termination_reason"]) == 3

    # The death penalty is on the same step, exactly as starvation pays it.
    prev_drive = float(calculate_drive(state.satiation, state.injury_level, p))
    curr_drive = float(calculate_drive(new_state.satiation, new_state.injury_level, p))
    expected = prev_drive - curr_drive - float(p.death_penalty)
    assert float(reward) == pytest.approx(expected, abs=1e-4)


def test_starvation_still_ends_the_episode_with_reason_2():
    """The other end of the same axis, unchanged — the symmetry claim."""
    p = _params()
    state = jax_reset(p, jax.random.PRNGKey(5))
    state = state.replace(nutrition=jnp.float32(float(p.metabolic_cost) / 2.0),
                          injury_level=jnp.float32(0.0))
    _, reward, done, info = jax_step(state, 4, p)
    assert bool(done)
    assert int(info["termination_reason"]) == 2
    assert float(reward) < -float(p.death_penalty) / 2.0


def test_reason_3_is_only_ever_stamped_on_a_step_that_also_ends_the_episode():
    """The half of the old defect that was visible in every log.

    Plain English: the environment writes a small integer onto every step
    saying WHY the episode ended, and 3 means "died of over-eating". Before
    2026-09-22 that 3 was written by a predicate (`satiation >= max_satiation`)
    that had nothing to do with dying, and `done` was never set alongside it —
    so a perfectly healthy, well-fed agent walked around carrying a
    "died of over-eating" label on live steps.

    WHY THIS TEST IS BUILT THE WAY IT IS. An earlier version of it walked the
    shipped world with move actions only and asserted 3 never appeared. That
    could not fail: moves cannot raise satiation (eat is a separate action), the
    world starts AT the setpoint, and with the setpoint in the middle of the
    range the old predicate `satiation >= max_satiation` was unreachable too. It
    therefore passed identically on the broken tree and proved nothing. This
    version reproduces the world the defect actually lived in — the setpoint AT
    the ceiling, which is what every config shipped before this change — and
    drives satiation onto that ceiling with a real eat step. On the old code
    that step stamps reason 3 with `done` False and the final assertion fails.
    """
    p = _params(**{"body.max_satiation": 100.0, "body.satiation_setpoint": 100.0,
                   "body.max_nutrition": 100.0, "body.start_nutrition": 100.0,
                   "body.start_satiation": 100.0, "body.start_nutrition_high": 100.0})
    assert bool(p.overeating_death), "the gate must be on or the branch is never traced"
    assert float(p.setpoint) == float(p.max_satiation), "the world the defect lived in"

    state = jax_reset(p, jax.random.PRNGKey(11))
    state = _put_food_under_agent(state, p)  # also clears the animals

    # (a) A cheap sanity guard, not the discriminating half: twenty ordinary
    #     live steps carry no death label and end no episode. Resting in the
    #     start cell rather than walking, because moving wanders into the
    #     world's damaging terrain and the agent dies of INJURY around t=16,
    #     which would make this loop fail for a reason that has nothing to do
    #     with over-eating.
    rest_action = 4 if bool(p.rest_action_enabled) else 0
    for t in range(20):
        state, _, done, info = jax_step(state, rest_action, p)
        assert int(info["termination_reason"]) != 3, f"reason 3 on a live step, t={t}"
        assert not bool(done), f"the rest was supposed to be survivable, t={t}"

    # (b) one real eat that lands ON the ceiling: the step the old predicate
    #     fired on while the episode carried on regardless.
    state = _put_food_under_agent(state, p)
    net = float(p.food_nutrition_gain) - float(p.eating_nutrition_cost) - float(p.metabolic_cost)
    state = state.replace(nutrition=jnp.float32(float(p.max_nutrition) - net),
                          satiation=jnp.float32(float(p.max_nutrition) - net),
                          injury_level=jnp.float32(0.0))
    eat_action = 5 if bool(p.rest_action_enabled) else 4
    new_state, _, done, info = jax_step(state, eat_action, p)

    assert float(new_state.satiation) >= float(p.max_satiation), "fixture missed the ceiling"
    assert int(info["termination_reason"]) == 3
    assert bool(done), "reason 3 stamped on a step the episode survived"


def test_overeating_death_off_removes_the_upper_end_death_from_values_and_graph():
    """The static gate, checked on the numbers AND on the traced graph.

    A test that only checked the ON case would pass just as happily against an
    implementation that ignored the key and always killed, so both halves matter.

    VALUES: at the nutrition level that kills with the key on, the episode
    continues and no reason 3 is stamped.

    GRAPH: `params.overeating_death` is a static (non-pytree) field, so the
    branch is resolved at trace time rather than with a runtime select. With the
    key off, `update_body`'s traced equation list is the with-it-on list minus
    exactly one contiguous pair — the `>=` comparison and the `where` that folds
    it into `done` — and nothing else moves.

    SCOPE NOTE, because the obvious stronger claim is FALSE. This says nothing
    about the step graph as a whole being unchanged by the two-sided-nutrition
    work. `satiation_deviation_range` runs on the drive and diagnostic paths for
    EVERY config, on or off, so the whole-step graph did grow: `code-reviewer`
    measured `jax_step` at 716 -> 722 equations with thermal off and 771 -> 781
    with it on, 2026-09-22. What is unchanged there is the arithmetic — at a
    ceiling setpoint the extra equations compute the same numbers bit for bit
    (the tests in section 1 pin that). Only the `done` block is literally
    op-free when the key is off, which is what the code comment claims and what
    this test checks.
    """
    import difflib

    from src.environment.core import update_body

    def _primitives(flag):
        q = _params(**{"body.overeating_death": flag})
        st = jax_reset(q, jax.random.PRNGKey(5))
        # update_body reads these four keys out of the step's info dict.
        info_in = {"ate_food": jnp.bool_(True), "damage": jnp.float32(0.0),
                   "rested": jnp.bool_(False), "agent_in_bush": jnp.bool_(False)}
        jaxpr = jax.make_jaxpr(
            lambda s, i: update_body(s, i, q, s.agent_pos))(st, info_in)
        return [str(e.primitive) for e in jaxpr.jaxpr.eqns]

    on, off = _primitives(True), _primitives(False)
    assert len(on) - len(off) == 2, f"expected a 2-equation branch; got {len(on)} vs {len(off)}"
    ops = [o for o in difflib.SequenceMatcher(a=off, b=on, autojunk=False).get_opcodes()
           if o[0] != "equal"]
    assert len(ops) == 1 and ops[0][0] == "insert", f"not a single contiguous branch: {ops}"
    inserted = on[ops[0][3]:ops[0][4]]
    assert any(name.startswith("ge") for name in inserted), \
        f"the inserted pair should contain the `>=` comparison; got {inserted}"

    p = _params(**{"body.overeating_death": False})
    state = jax_reset(p, jax.random.PRNGKey(5))
    state = _put_food_under_agent(state, p)
    net = float(p.food_nutrition_gain) - float(p.eating_nutrition_cost) - float(p.metabolic_cost)
    state = state.replace(nutrition=jnp.float32(float(p.max_nutrition) - net),
                          satiation=jnp.float32(float(p.max_nutrition) - net),
                          injury_level=jnp.float32(0.0))
    eat_action = 5 if bool(p.rest_action_enabled) else 4
    new_state, _, done, info = jax_step(state, eat_action, p)
    assert float(new_state.nutrition) >= float(p.max_nutrition)
    assert not bool(done)
    assert int(info["termination_reason"]) != 3


# ── 5. the loader refuses a satiation axis the drive cannot divide by ────────

@pytest.mark.parametrize("overrides, needle", [
    ({"body.max_satiation": 0.0, "body.satiation_setpoint": 0.0,
      "body.start_satiation": 0.0}, "body.max_satiation must be > 0"),
    ({"body.max_nutrition": 0.0, "body.start_nutrition": 0.0,
      "body.start_nutrition_high": 0.0}, "body.max_nutrition must be > 0"),
    ({"body.satiation_setpoint": 250.0}, "body.satiation_setpoint must satisfy"),
])
def test_loader_rejects_a_degenerate_satiation_axis(overrides, needle):
    """Caught at load, not inside a jitted step where the error is unreadable.

    `range_S = max(setpoint, max_satiation - setpoint)` is a DIVISOR in the
    logged hunger drive and a MULTIPLIER on the thermal axis. A zero-width axis
    makes it 0, so the drive is 0/0 -> NaN and every reward downstream is NaN
    with no traceback pointing anywhere near the config. A setpoint above the
    ceiling is the quieter failure: satiation is clipped to the ceiling, so the
    drive can never reach zero and the agent is punished forever for a state it
    cannot leave. Both loaded silently before 2026-09-22.
    """
    with pytest.raises(ValueError, match=needle):
        _params(**overrides)
