"""Tests for src/behavior/balance_metrics.py (plan Part B: T3-T9, T11).

Plain-language context: the balance metrics count, per training step, whether the agent
was in a bush / on a warm cell / eating, split by its body state before the step. These
tests pin the definitions: ratios are pooled over the window (not averaged per
episode), empty bins omit their ratio but still log their step count, switched-off
modalities emit no keys, the warm-cell rule looks at the cell (not the body), the
config switch has no default, and the per-run calibration record reads the live params.

T3 runs the REAL rollout (`collect_trajectories`) to prove the body state is read
before the step, not after.

Plan: docs/develop/active/behavior/BALANCE_METRICS_TRAINING_LOGGING.md
"""
import os

os.environ.setdefault("JAX_PLATFORMS", "cpu")

import numpy as np
import pytest

from src.behavior import balance_metrics as bm
from src.utils.config import Config


def _counts(n=150.0, i=10.0, felt=None, t=None, warm=None, near=None, ate=0, bush=0,
            thermal_on=False, felt_on=False):
    a = lambda v: np.asarray([v])
    return bm.step_counts(
        a(n), a(i), None if felt is None else a(felt), None if t is None else a(t),
        None if warm is None else a(warm), None if near is None else a(near),
        a(ate), a(bush), thermal_on=thermal_on, felt_on=felt_on)[0]


def _episode(rows):
    return np.sum(np.stack(rows), axis=0).astype(np.int32)


# ---------------------------------------------------------------------------
# T4: ratio of pooled sums
# ---------------------------------------------------------------------------
def test_window_ratio_is_ratio_of_sums():
    ep1 = _episode([_counts(n=30.0, ate=1)])                         # hungry 1 step, ate
    ep2 = _episode([_counts(n=30.0, ate=0) for _ in range(99)])      # hungry 99 steps, never ate
    log = bm.window_log([ep1, ep2], thermal_on=False, felt_on=False)
    assert log["Episode/Bal_N_Hungry"] == 100.0
    assert log["Episode/Bal_EatShare_Hungry"] == pytest.approx(0.01)   # mean of ratios would be 0.5


# ---------------------------------------------------------------------------
# T5: zero denominators
# ---------------------------------------------------------------------------
def test_zero_denominator_omits_share_ratio_but_logs_N():
    # Only hungry, barely-injured steps: the fed bin and the injured bin are empty.
    ep = _episode([_counts(n=30.0, i=5.0, ate=1, bush=1) for _ in range(5)])
    log = bm.window_log([ep], thermal_on=False, felt_on=False)
    assert log["Episode/Bal_N_Fed"] == 0.0
    assert log["Episode/Bal_N_InjHi_True"] == 0.0
    assert log["Episode/Bal_N_InjHi_True_Hungry"] == 0.0
    for k in ("EatShare_Fed", "EatRatio", "BushShare_InjHi_True", "HideRatio_True",
              "BushShare_InjHi_True_Hungry", "HideGap_True_Hungry", "HideRatio_True_Hungry"):
        assert f"Episode/Bal_{k}" not in log, k
    assert log["Episode/Bal_EatShare_Hungry"] == 1.0
    assert log["Episode/Bal_BushShare_InjLo_True"] == 1.0
    # "off" bin share 0 -> ratio not computable, but both shares logged.
    ep_hi = _episode([_counts(n=150.0, i=80.0, bush=1), _counts(n=150.0, i=5.0, bush=0)])
    log2 = bm.window_log([ep_hi], thermal_on=False, felt_on=False)
    assert log2["Episode/Bal_BushShare_InjLo_True"] == 0.0
    assert "Episode/Bal_HideRatio_True" not in log2
    assert log2["Episode/Bal_HideGap_True_Fed"] == 1.0


# ---------------------------------------------------------------------------
# T6: static gating
# ---------------------------------------------------------------------------
def test_thermal_off_and_felt_off_emit_no_keys():
    ep = _episode([_counts(n=30.0, i=80.0, bush=1), _counts(n=150.0, i=5.0)])
    log = bm.window_log([ep], thermal_on=False, felt_on=False)
    assert log, "expected some keys"
    for k in log:
        assert "Warm" not in k and "Cold" not in k and "NearFire" not in k, k
        assert "Felt" not in k, k
    # And with both on, they appear.
    ep_on = _episode([_counts(n=30.0, i=80.0, felt=70.0, t=-10.0, warm=1, near=0, bush=1,
                              thermal_on=True, felt_on=True)])
    log_on = bm.window_log([ep_on], thermal_on=True, felt_on=True)
    for k in ("TimeWarm", "TimeNearFire", "N_Cold", "N_Warm", "WarmShare_Cold",
              "N_InjHi_Felt", "BushShare_InjHi_Felt", "N_InjHi_Felt_Hungry"):
        assert f"Episode/Bal_{k}" in log_on, k
    # Inputs must match the flags: no silent substitution.
    with pytest.raises(ValueError):
        _counts(felt=50.0, felt_on=False)
    with pytest.raises(ValueError):
        _counts(thermal_on=True)          # thermal on but no body temp / cell inputs


# ---------------------------------------------------------------------------
# T7: warm cell is a property of the cell, not of the body
# ---------------------------------------------------------------------------
SETPOINT, OPEN_HIGH = 0.0, -29.0


def _cell_flags(cell_t):
    on_warm = cell_t > SETPOINT
    near = (cell_t > OPEN_HIGH) and not on_warm       # the scan_fn rule (plan A4)
    return on_warm, near


def test_warm_cell_uses_cell_not_body():
    # (a) -16 degC cell, -20 degC body: cell warmer than body, still NOT warm; near_fire.
    w, nf = _cell_flags(-16.0)
    c = _counts(t=-20.0, warm=w, near=nf, thermal_on=True)
    assert c[bm.IDX["warm"]] == 0 and c[bm.IDX["near_fire"]] == 1
    assert c[bm.IDX["warm_cold"]] == 0 and c[bm.IDX["n_cold"]] == 1
    assert c[bm.IDX["elsewhere"]] == 1
    # (b) +8.8 degC cell, +10 degC body: cell cooler than body, still warm; not near_fire.
    w, nf = _cell_flags(8.8)
    c = _counts(t=10.0, warm=w, near=nf, thermal_on=True)
    assert c[bm.IDX["warm"]] == 1 and c[bm.IDX["near_fire"]] == 0
    assert c[bm.IDX["warm_warmT"]] == 1 and c[bm.IDX["elsewhere"]] == 0
    # (c) -30 degC open ground: neither.
    w, nf = _cell_flags(-30.0)
    c = _counts(t=-20.0, warm=w, near=nf, thermal_on=True)
    assert c[bm.IDX["warm"]] == 0 and c[bm.IDX["near_fire"]] == 0


def test_scan_fn_warm_rule_matches_cell_flags():
    """The trainer's jitted rule is the one the T7 helper encodes (source pin)."""
    import inspect
    from src.models import recurrent_ppo_trainer as rpt
    src = inspect.getsource(rpt.collect_trajectories)
    assert "cell_t > env_params.temperature_setpoint" in src
    assert "(cell_t > env_params.thermal_default_temp_high) & ~on_warm" in src


# ---------------------------------------------------------------------------
# T8: definitions
# ---------------------------------------------------------------------------
def test_elsewhere_is_complement():
    rng = np.random.default_rng(0)
    shp = (50, 7)
    bush = rng.integers(0, 2, shp)
    warm = rng.integers(0, 2, shp).astype(bool)
    eat = rng.integers(0, 2, shp)
    c = bm.step_counts(rng.uniform(0, 200, shp), rng.uniform(0, 100, shp),
                       rng.uniform(0, 100, shp), rng.uniform(-15, 15, shp),
                       warm, np.zeros(shp, bool), eat, bush, thermal_on=True, felt_on=True)
    assert c.shape == shp + (bm.K,) and c.dtype == np.uint8
    expect = ~((bush != 0) | warm | (eat != 0))
    np.testing.assert_array_equal(c[..., bm.IDX["elsewhere"]], expect.astype(np.uint8))


def test_late_death_partition():
    cut = 20
    lengths = [20, 21, 500, 5, 300, 40]
    reasons = [2, 4, 1, 3, 5, 4]          # early starve, late injury, truncation, early overeat, late thermal, late injury
    log = bm.late_death_log(lengths, reasons, early_death_max_steps=cut)
    assert log["Episode/Bal_EarlyDeathShare"] == pytest.approx(2 / 6)
    assert log["Episode/Bal_LateDeathShare"] == pytest.approx(3 / 6)   # all episodes in denominator
    assert log["Episode/Bal_LateDeath_Injury"] == pytest.approx(2 / 3)
    assert log["Episode/Bal_LateDeath_Thermal"] == pytest.approx(1 / 3)
    assert log["Episode/Bal_LateDeath_Starvation"] == 0.0
    # The cut-off is the config value, not a constant.
    log10 = bm.late_death_log([15], [2], early_death_max_steps=10)
    assert log10["Episode/Bal_LateDeathShare"] == 1.0
    # No late deaths -> no cause shares.
    log0 = bm.late_death_log([500, 3], [1, 2], early_death_max_steps=cut)
    assert log0["Episode/Bal_LateDeathShare"] == 0.0
    assert not any(k.startswith("Episode/Bal_LateDeath_") for k in log0)


# ---------------------------------------------------------------------------
# T9: the switch and the cut-off have no default
# ---------------------------------------------------------------------------
def test_flag_is_mandatory():
    with pytest.raises(ValueError):
        bm.resolve_balance_metrics_flag(Config({"logging": {"episode": {}}}))
    for bad in ("true", 1, 0):
        with pytest.raises(ValueError):
            bm.resolve_balance_metrics_flag(Config({"logging": {"episode": {"balance_metrics": bad}}}))
    assert bm.resolve_balance_metrics_flag(
        Config({"logging": {"episode": {"balance_metrics": False}}})) is False
    # Early-death cut-off.
    with pytest.raises(ValueError):
        bm.resolve_early_death_max_steps(Config({"logging": {"episode": {}}}))
    for bad in (True, 20.0, -1, "20"):
        with pytest.raises(ValueError):
            bm.resolve_early_death_max_steps(
                Config({"logging": {"episode": {"balance_early_death_max_steps": bad}}}))
    assert bm.resolve_early_death_max_steps(
        Config({"logging": {"episode": {"balance_early_death_max_steps": 20}}})) == 20


def test_shipped_rppo_train_config_sets_both_keys():
    """configs/train/recurrent_ppo.yaml carries the switch (true) and the cut-off (20);
    configs/train/default.yaml deliberately does not (a value there would silently
    satisfy a missing rPPO key)."""
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    rppo = Config.load_yaml(os.path.join(root, "configs", "train", "recurrent_ppo.yaml"))
    assert bm.resolve_balance_metrics_flag(rppo) is True
    assert bm.resolve_early_death_max_steps(rppo) == 20
    dflt = Config.load_yaml(os.path.join(root, "configs", "train", "default.yaml"))
    assert dflt.get("logging.episode.balance_metrics") is None
    assert dflt.get("logging.episode.balance_early_death_max_steps") is None


# ---------------------------------------------------------------------------
# T11: calibration record reads the live params
# ---------------------------------------------------------------------------
class _P:
    pass


def test_calibration_record_reads_params():
    p = _P()
    p.max_nutrition, p.max_injury = 150.0, 80.0
    p.temperature_setpoint, p.thermal_default_temp_high = 1.5, -27.0
    rec = bm.calibration_record(p, thermal_on=True, felt_on=True, early_death_max_steps=17)
    assert rec["max_nutrition"] == 150.0 and rec["max_injury"] == 80.0
    assert rec["temperature_setpoint"] == 1.5 and rec["thermal_default_temp_high"] == -27.0
    assert rec["early_death_max_steps"] == 17
    for k in ("HUNGRY_LT", "FED_GE", "COMB_FED_LO", "COMB_FED_HI", "INJ_HI_GE",
              "INJ_LO_LE", "COLD_LE", "WARM_GE"):
        assert rec[k] == getattr(bm, k), k
    rec_off = bm.calibration_record(p, thermal_on=False, felt_on=False, early_death_max_steps=17)
    assert "temperature_setpoint" not in rec_off
    q = _P()
    q.max_nutrition = 200.0
    with pytest.raises(AttributeError):
        bm.calibration_record(q, thermal_on=False, felt_on=False, early_death_max_steps=20)


# ---------------------------------------------------------------------------
# T3: the REAL scan_fn bins the PRE-step body state (plan A2)
# ---------------------------------------------------------------------------
def _one_step_rollout(action_id, set_state):
    """One `collect_trajectories` step on the level-05 world with every env forced to
    `action_id` (the actor is monkeypatched; the env step is real). `set_state(state,
    params)` edits the batched reset state before the step."""
    import jax
    import jax.numpy as jnp
    from src.environment.config_loader import load_env_config, load_env_params
    from src.environment.core import jax_reset
    from src.models import recurrent_ppo_network as rpn
    from src.models import recurrent_ppo_trainer as rpt

    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    params = load_env_params(load_env_config(os.path.join(
        root, "configs", "environment", "experiment", "basic", "05-campfire_thermal_10x10.yaml")))
    assert params.thermal_enabled and params.interoceptive_nociception_enabled
    state = jax.vmap(jax_reset, in_axes=(None, 0))(params, jax.random.split(jax.random.PRNGKey(0), 2))
    state = set_state(state, params)

    def fake_act(model, obs, h, key):
        return jnp.int32(action_id), jnp.float32(0.0), jnp.float32(0.0), h, None

    def fake_model(obs, h):
        return jnp.zeros((6,)), jnp.zeros((1,)), h, None

    orig = rpn.get_action_and_value_nnx
    rpn.get_action_and_value_nnx = fake_act
    try:
        traj, _, final_state, _, _, _ = rpt.collect_trajectories(
            fake_model, params, state, jnp.zeros((2, 4)), jax.random.PRNGKey(1), 1,
            rnn_type="GRU", return_mode="MC", balance_metrics=True)
    finally:
        rpn.get_action_and_value_nnx = orig
    return params, state, traj, final_state


def _counts_from_traj(traj, params):
    si, b = traj.step_info, traj.step_info.balance
    return bm.step_counts(
        np.asarray(b.nutrition), np.asarray(b.injury), np.asarray(b.felt_injury),
        np.asarray(b.body_temp), np.asarray(b.on_warm_cell), np.asarray(b.near_fire),
        np.asarray(si.ate_food), np.asarray(si.agent_in_bush),
        thermal_on=True, felt_on=True)[0]   # [B, K] for the single step


def test_pre_step_state_is_binned():
    import jax.numpy as jnp

    # --- Eating: on food at N = 59, eats -> post-step N >= 60; must count as hungry.
    def on_food(state, params):
        food = int(np.flatnonzero((np.asarray(params.res_type) == 0)
                                  & np.asarray(state.res_active[0]))[0])
        pos = state.res_pos[:, food, :]
        return state.replace(agent_pos=pos, nutrition=jnp.full_like(state.nutrition, 59.0),
                             body_temp=jnp.zeros_like(state.body_temp),
                             animal_active=jnp.zeros_like(state.animal_active))
    eat_id = 5 if bool(params_rest_enabled()) else 4
    params, s0, traj, s1 = _one_step_rollout(eat_id, on_food)
    assert bool(np.all(np.asarray(traj.step_info.ate_food))), "setup: the agent must eat"
    assert not bool(np.any(np.asarray(traj.done)))
    assert np.all(np.asarray(s1.nutrition) >= bm.HUNGRY_LT), \
        f"setup: post-step N must leave the hungry bin, got {np.asarray(s1.nutrition)}"
    c = _counts_from_traj(traj, params)
    assert np.all(c[:, bm.IDX["n_hungry"]] == 1) and np.all(c[:, bm.IDX["eat_hungry"]] == 1)
    np.testing.assert_array_equal(np.asarray(traj.step_info.balance.nutrition), 59.0)

    # --- Hiding: in a bush at I = 61, rests -> post-step I < 60; must count as badly injured.
    def in_bush(state, params):
        bush = int(np.flatnonzero(np.asarray(params.obs_hides_agent)
                                  & np.asarray(state.obs_active[0]))[0])
        pos = state.obs_pos[:, bush, :]
        return state.replace(agent_pos=pos, injury_level=jnp.full_like(state.injury_level, 61.0),
                             nutrition=jnp.full_like(state.nutrition, 120.0),
                             body_temp=jnp.zeros_like(state.body_temp),
                             animal_active=jnp.zeros_like(state.animal_active))
    params, s0, traj, s1 = _one_step_rollout(4, in_bush)
    assert bool(np.all(np.asarray(traj.step_info.agent_in_bush))), "setup: the agent must be in a bush"
    assert bool(np.all(np.asarray(traj.step_info.rested)))
    assert np.all(np.asarray(s1.injury_level) < bm.INJ_HI_GE), \
        f"setup: post-step I must leave the injured bin, got {np.asarray(s1.injury_level)}"
    c = _counts_from_traj(traj, params)
    assert np.all(c[:, bm.IDX["n_inj_hi_true"]] == 1) and np.all(c[:, bm.IDX["bush_inj_hi_true"]] == 1)
    np.testing.assert_array_equal(np.asarray(traj.step_info.balance.injury), 61.0)


def params_rest_enabled():
    from src.environment.config_loader import load_env_config, load_env_params
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    p = load_env_params(load_env_config(os.path.join(
        root, "configs", "environment", "experiment", "basic", "05-campfire_thermal_10x10.yaml")))
    return p.rest_action_enabled
