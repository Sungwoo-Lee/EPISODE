"""Hydration: the water clock, the two thirst deaths and their labels (THIRST_WATER_PLAN §T3).

**Plain-language summary.** With water on, the agent has a hydration level that drains
0.625 per step and, on every step that ends on a pond cell, gains 5.625 (net +5), clipped
once to [0, 200]. Hitting 0 is death by dehydration (termination reason 6); hitting 200 is
death by over-drinking (reason 7). This test pins, against an independent numpy float32
oracle written here (never against `core.py`):

- the exact clocks: resting away from water from the setpoint dies on step **160** with
  reason 6 and no earlier label; resting on the pond dies on step **20** with reason 7;
  a refill from 50 reaches 100 in 10 on-pond steps;
- `water.start_hydration` is really written at reset (the dead-knob trap of KNOWN_BUGS
  ~#94), and the random start draws inside its range;
- ONE predicate (KNOWN_BUGS ~#160 / ~#192): over 200 random-policy level-06 episodes a
  thirst label never appears without the episode ending, and every thirst ending carries
  the right label;
- water-off worlds (levels 00-05) never stamp 6 or 7 (KNOWN_BUGS ~#494);
- the trainers' real-death mask (`termination_reason >= 2`) counts both thirst deaths;
- the reward is `prev_drive - curr_drive` (minus the death penalty on death) with the
  drive's fourth, water axis computed here from (satiation, injury, body temperature,
  hydration).

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
DEFAULT = os.path.join(_REPO, "configs", "environment", "default.yaml")
LVL05 = os.path.join(_BASIC, "05-campfire_thermal_10x10.yaml")
WATER_OFF_WORLDS = ("00-static_predator_5x5", "01-slow_predator_5x5",
                    "02-predator_and_rabbit_10x10", "03-random_init_10x10",
                    "04-jump_attack_10x10", "05-campfire_thermal_10x10")
REST = 4
D, G, MAXW = np.float32(0.625), np.float32(5.625), np.float32(200.0)


@pytest.fixture(autouse=True)
def _release_compiled_programs():
    yield
    jax.clear_caches()


def _params(d):
    return load_env_params(Config(copy.deepcopy(d)))


def _lvl06_dict():
    """Level 06 (the pond world): the campfire world with water on."""
    d = copy.deepcopy(load_env_config(LVL05).to_dict())
    d["water"].update(enabled=True, random_start_hydration=True,
                      start_hydration_low=0.0, start_hydration_high=200.0)
    return d


def _controlled(start=100.0):
    """default.yaml + water on, nothing else in the world: no food (nutrition off, or the
    100-step food clock would kill first), no animals, no obstacles. Pond fixed at array
    rows/cols 1-2; the agent starts far away at array (8, 8)."""
    d = copy.deepcopy(load_env_config(DEFAULT).to_dict())
    d["environment"].update(resources=[], entities=[], obstacles=[],
                            random_start_pos=False, start_pos=[9, 9])
    d["body"]["with_nutrition"] = False
    d["water"].update(enabled=True, candidates=[[2, 2]], random_start_hydration=False,
                      start_hydration=float(start))
    return d


def _oracle(w0, on_pond, n):
    w, out = np.float32(w0), []
    for _ in range(n):
        w = np.float32(np.clip(np.float32(w - D + G * np.float32(on_pond)), 0.0, MAXW))
        out.append(w)
    return np.asarray(out, dtype=np.float32)


def _rest_rollout(p, n, agent_pos=None):
    s = core.jax_reset(p, jax.random.PRNGKey(0))
    if agent_pos is not None:
        s = s._replace(agent_pos=jnp.asarray(agent_pos, dtype=jnp.int32))
    step = jax.jit(core.jax_step)
    W, dn, rs = [], [], []
    for _ in range(n):
        s, _, d, info = step(s, jnp.asarray(REST, dtype=jnp.int32), p)
        W.append(np.float32(s.hydration))
        dn.append(bool(d))
        rs.append(int(info["termination_reason"]))
        if bool(d):
            break
    return np.asarray(W, dtype=np.float32), np.asarray(dn), np.asarray(rs), s


# ── the clocks ────────────────────────────────────────────────────────────────

def test_dehydration_at_step_160_resting_away_from_water():
    p = _params(_controlled(100.0))
    W, dn, rs, s = _rest_rollout(p, 400)
    oracle = _oracle(100.0, 0, 160)
    assert len(W) == 160, f"episode ended at step {len(W)}, expected 160"
    assert np.array_equal(W, oracle), "hydration trajectory differs from the float32 oracle"
    assert dn[-1] and not dn[:-1].any()
    assert rs[-1] == 6 and (rs[:-1] == 0).all(), f"labels {np.unique(rs[:-1])}, last {rs[-1]}"
    assert float(W[-1]) == 0.0


def test_overdrinking_at_step_20_resting_on_the_pond():
    p = _params(_controlled(100.0))
    W, dn, rs, _ = _rest_rollout(p, 100, agent_pos=[1, 1])
    assert len(W) == 20, f"episode ended at step {len(W)}, expected 20"
    assert np.array_equal(W, _oracle(100.0, 1, 20))
    assert dn[-1] and not dn[:-1].any()
    assert rs[-1] == 7 and (rs[:-1] == 0).all()
    assert float(W[-1]) == 200.0


def test_refill_50_to_100_in_10_steps():
    p = _params(_controlled(50.0))
    W, dn, _, _ = _rest_rollout(p, 10, agent_pos=[2, 2])
    assert np.array_equal(W, _oracle(50.0, 1, 10)) and float(W[-1]) == 100.0
    assert not dn.any()


def test_drank_flag_follows_the_post_move_cell():
    """Walking ONTO the pond drinks on that same step; walking off stops it."""
    p = _params(_controlled(100.0))
    s = core.jax_reset(p, jax.random.PRNGKey(0))._replace(
        agent_pos=jnp.asarray([1, 3], dtype=jnp.int32))
    s1, _, _, i1 = core.jax_step(s, jnp.asarray(3, dtype=jnp.int32), p)   # Left -> (1, 2)
    assert bool(i1["drank"]) and float(s1.hydration) == 105.0
    s2, _, _, i2 = core.jax_step(s1, jnp.asarray(1, dtype=jnp.int32), p)  # Right -> (1, 3)
    assert not bool(i2["drank"]) and float(s2.hydration) == 104.375


# ── start hydration is live ───────────────────────────────────────────────────

def test_start_hydration_is_written_at_reset():
    p = _params(_controlled(37.0))
    assert float(core.jax_reset(p, jax.random.PRNGKey(3)).hydration) == 37.0


def test_random_start_hydration_draws_inside_the_range():
    d = _controlled()
    d["water"].update(random_start_hydration=True, start_hydration_low=20.0,
                      start_hydration_high=180.0)
    p = _params(d)
    keys = jax.vmap(jax.random.PRNGKey)(jnp.arange(500))
    h = np.asarray(jax.vmap(lambda k: core.jax_reset(p, k).hydration)(keys))
    assert h.min() >= 20.0 and h.max() < 180.0
    assert len(np.unique(h)) > 400


# ── one predicate, and no 6/7 on water-off worlds ─────────────────────────────

def _random_episodes(p, n_envs, n_steps, seed):
    """n_envs random-policy episodes, each until its first `done` (steps after are masked)."""
    def one(key):
        k_reset, k_act = jax.random.split(key)
        s0 = core.jax_reset(p, k_reset)

        def body(carry, k):
            s, alive = carry
            a = jax.random.randint(k, (), 0, 6)
            s2, _, d, info = core.jax_step(s, a, p)
            w = s2.hydration if p.water_enabled else jnp.float32(-1.0)
            out = (alive, info["termination_reason"], d, w)
            return (s2, alive & ~d), out
        _, out = jax.lax.scan(body, (s0, jnp.array(True)), jax.random.split(k_act, n_steps))
        return out
    keys = jax.random.split(jax.random.PRNGKey(seed), n_envs)
    alive, reason, done, w = jax.jit(jax.vmap(one))(keys)
    return (np.asarray(alive), np.asarray(reason), np.asarray(done), np.asarray(w))


def test_thirst_labels_come_from_the_death_predicate():
    p = _params(_lvl06_dict())
    alive, reason, done, w = _random_episodes(p, 200, 500, seed=11)
    m = alive                                           # steps actually taken
    label_no_death = m & np.isin(reason, [6, 7]) & ~done
    assert label_no_death.sum() == 0, f"{label_no_death.sum()} thirst labels without death"
    dry = m & done & (w <= 0.0)
    full = m & done & (w >= 200.0)
    assert (reason[dry] == 6).all(), f"dehydration endings labelled {np.unique(reason[dry])}"
    assert (reason[full] == 7).all(), f"over-drinking endings labelled {np.unique(reason[full])}"
    assert (reason[m & (reason == 6)] == 6).all()
    n6, n7 = int((m & (reason == 6)).sum()), int((m & (reason == 7)).sum())
    print(f"[labels] dehydration {n6}, over-drinking {n7} of 200 episodes")
    assert n6 > 0, "no dehydration death in 200 episodes: the check is vacuous"


@pytest.mark.parametrize("world", WATER_OFF_WORLDS)
def test_water_off_worlds_never_stamp_6_or_7(world):
    p = _params(load_env_config(os.path.join(_BASIC, world + ".yaml")).to_dict())
    assert p.water_enabled is False
    alive, reason, _, _ = _random_episodes(p, 50, 500, seed=5)
    seen = set(np.unique(reason[alive]).tolist())
    assert seen <= {0, 1, 2, 3, 4, 5}, f"{world}: reasons {sorted(seen)}"


def test_trainer_real_death_mask_counts_thirst_deaths():
    """The rPPO trainer's real-death mask is `termination_reason >= 2` (five sites). Run a
    real dehydration and a real over-drinking death through that exact expression."""
    src = open(os.path.join(_REPO, "src", "models", "recurrent_ppo_trainer.py")).read()
    assert src.count("(trajectories.step_info.termination_reason >= 2)") == 5
    p = _params(_controlled(100.0))
    _, _, r_dry, _ = _rest_rollout(p, 400)
    _, _, r_full, _ = _rest_rollout(p, 100, agent_pos=[1, 1])
    reasons = jnp.asarray([r_dry[-1], r_full[-1]], dtype=jnp.int32)
    assert list(np.asarray(reasons)) == [6, 7]
    terminateds = (reasons >= 2).astype(jnp.float32)
    assert list(np.asarray(terminateds)) == [1.0, 1.0]


# ── drive and reward ──────────────────────────────────────────────────────────

def _np_drive(S, I, T, W, p):
    rs = max(p.setpoint, p.max_satiation - p.setpoint)
    rw = max(p.water_hydration_setpoint, p.water_max_hydration - p.water_hydration_setpoint)
    ax = np.stack([np.asarray(S, np.float64) - p.setpoint, np.asarray(I, np.float64),
                   (np.asarray(T, np.float64) - p.temperature_setpoint) * (rs / p.max_temperature),
                   (np.asarray(W, np.float64) - p.water_hydration_setpoint) * (rs / rw)], axis=-1)
    return np.linalg.norm(ax, axis=-1)


def test_drive_axis_scale():
    p = _params(_lvl06_dict())
    f = lambda S, I, T, W: float(core.calculate_drive(
        jnp.float32(S), jnp.float32(I), p, body_temp=jnp.float32(T), hydration=jnp.float32(W)))
    Tset = p.temperature_setpoint
    assert f(100.0, 0.0, Tset, 100.0) == 0.0
    assert f(100.0, 0.0, Tset, 0.0) == pytest.approx(100.0, abs=1e-4)
    assert f(100.0, 0.0, Tset, 200.0) == pytest.approx(100.0, abs=1e-4)
    with pytest.raises(ValueError, match="hydration"):
        core.calculate_drive(jnp.float32(100.0), jnp.float32(0.0), p, body_temp=jnp.float32(Tset))


def test_reward_is_the_four_axis_drive_difference():
    p = _params(_lvl06_dict())
    step = jax.jit(core.jax_step)
    rows, n_death = [], 0
    for seed in range(8):
        s = core.jax_reset(p, jax.random.PRNGKey(seed))
        akey = jax.random.PRNGKey(100 + seed)
        for _ in range(200):
            akey, k = jax.random.split(akey)
            a = jax.random.randint(k, (), 0, 6)
            s2, r, d, info = step(s, a, p)
            prev = _np_drive(s.satiation, s.injury_level, s.body_temp, s.hydration, p)
            curr = _np_drive(s2.satiation, s2.injury_level, s2.body_temp, s2.hydration, p)
            real_death = int(info["termination_reason"]) >= 2
            n_death += real_death
            want = prev - curr - (p.death_penalty if real_death else 0.0) \
                - (p.eating_reward_penalty if bool(info["ate_food"]) else 0.0)
            rows.append((float(r), want))
            # range_W = max(100, 200 - 100) = 100, the same scale the drive axis uses.
            ref = ((float(s2.hydration) / 100.0) - (100.0 / 100.0)) ** 2
            assert float(info["drive_thirst"]) == pytest.approx(ref, abs=1e-6)
            s = s2
            if bool(d):
                break
    got, want = np.array(rows).T
    assert np.allclose(got, want, atol=2e-3), f"max |diff| {np.abs(got - want).max()}"
    assert n_death > 0


# ── metric keys (C4) ──────────────────────────────────────────────────────────

def test_thirst_deaths_have_their_own_metric_keys():
    """One shared list of termination names; codes 6 and 7 get Term_Dehydration /
    Term_Overdrinking; no trainer carries its own literal copy of the list any more."""
    from src.behavior.balance_metrics import _DEATH_CAUSES, late_death_log
    from src.behavior.episode_metrics import (TERMINATION_REASONS, episode_finalise_episode,
                                              episode_wandb_keys, make_episode_state)
    assert (6, "Dehydration") in TERMINATION_REASONS and (7, "Overdrinking") in TERMINATION_REASONS
    keys = episode_wandb_keys()
    assert len(keys) == 23 and len(set(keys)) == 23
    st = make_episode_state(1)
    for code, name in ((6, "Dehydration"), (7, "Overdrinking")):
        out = episode_finalise_episode(st, 0, code)
        assert out[f"Episode/Term_{name}"] == 1.0
        assert sum(v for k, v in out.items() if k.startswith("Episode/Term_")) == 1.0
        assert set(out) == set(keys)
    assert dict(_DEATH_CAUSES)[6] == "Dehydration" and dict(_DEATH_CAUSES)[7] == "Overdrinking"
    bal = late_death_log([30, 30, 30, 30], [6, 7, 1, 2], early_death_max_steps=20)
    assert bal["Episode/Bal_LateDeathShare"] == 0.75
    assert bal["Episode/Bal_LateDeath_Dehydration"] == pytest.approx(1 / 3)
    for rel in ("train.py", os.path.join("src", "algorithms", "dreamer_srl", "dreamer_srl_main.py")):
        src = open(os.path.join(_REPO, rel)).read()
        assert "(5, 'Thermal')" not in src and '(5, "Thermal")' not in src, rel
