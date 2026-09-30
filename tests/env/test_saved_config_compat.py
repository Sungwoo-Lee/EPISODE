"""Old training runs' saved settings files keep loading after new mandatory keys land.

**Plain-language summary.** Every finished training run keeps its own frozen copy of
its settings (`results/<algo>/<run>/models/config.yaml`). Evaluation, replay and
trajectory collection rebuild the run's world from that copy. The body-mechanics change
(`docs/develop/active/thermal/STATE_DEPENDENT_BODY_MECHANICS.md`) adds six settings
that the loader requires, and the bush-to-fire clearance change
(`docs/develop/active/thermal/BUSH_FIRE_CLEARANCE.md`) adds a seventh, so without help
every frozen copy would stop loading. `src/environment/saved_config_compat.py` fills in
exactly those seven settings, at the values that reproduce the old behaviour, and only for
saved run configs -- never for a live file under `configs/`.

The two fixtures are verbatim copies of real Wave 1 and Wave 2 level-05 saved configs
(`tests/env/fixtures/saved_run_configs/`). A missing fixture FAILS, never skips.

What is pinned here:
  (i)   both fixtures load through the shim, which supplies exactly the seven keys plus
        the water gate `water.enabled: false` (THIRST_WATER_PLAN);
  (ii)  the raw load of each fixture raises the missing-key error (the reason the shim
        exists -- unconditional, not dependent on which commit runs it);
  (iii) a `source` under `configs/` is refused;
  (iv)  a partial set of one era's thermal keys, or a partial body set, is refused;
        all-or-none is per (block, era), so a run from between two eras is NOT refused;
  (v)   keys already present are not overwritten;
  (vi)  the deep-copy pattern: the caller's dict (and so the trajectory-store
        fingerprint) is unchanged, and every wired call site injects into a deep copy;
  (vii) a thermal-off saved config gets only the two body keys.
"""
import copy
import os
import re

import pytest
import yaml

from src.environment.config_loader import load_env_params
from src.environment.saved_config_compat import apply_saved_config_compat
from src.utils.config import Config
from src.utils.trajectory_store import env_fingerprint

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_FIX_DIR = os.path.join(os.path.dirname(__file__), "fixtures", "saved_run_configs")
_FIXTURES = (
    "20260921-114858_rppo_basicq2_lvl05_t1none_s42.yaml",  # Wave 1, level 05
    "20260922-182534_rppo_bq2cover_lvl05_t1none_s42.yaml",  # Wave 2, level 05
)
_SEVEN = sorted([
    "thermal.random_start_body_temp",
    "thermal.healing_cold_sensitivity",
    "thermal.healing_warm_sensitivity",
    "thermal.injury_heat_exchange_gain",
    "body.healing_nutrition_cost",
    "body.healing_nutrition_dependence",
    "thermal.bush_min_fire_distance",   # BUSH_FIRE_CLEARANCE era
    "water.enabled",                    # THIRST_WATER_PLAN era (always supplied when absent)
])
# A path outside configs/ -- the saved-run shape. Never read; only resolved.
_SAVED_SOURCE = os.path.join(_REPO, "results", "JAX_RecurrentPPO", "x", "models", "config.yaml")

# The call sites wired in C0 (plan §A7, plus the site found by the re-grep).
_CALL_SITES = (
    "scripts/eval/traj_collect/collect_trajectories.py",
    "scripts/eval/eval_rollout.py",
    "scripts/analysis/nmn/replay.py",
    "scripts/analysis/trajectory_glm.py",
    "scripts/analysis/supplementary/parity.py",
    "scripts/analysis/obs_manipulation/run.py",
)


def _load_fixture(name):
    path = os.path.join(_FIX_DIR, name)
    assert os.path.isfile(path), (
        f"saved-run fixture missing: {path}. This test fails rather than skips -- a "
        "compat gate that skips on missing input is a gate that never compared.")
    with open(path) as fh:
        return yaml.safe_load(fh), path


def _get(cfg, dotted):
    d = cfg
    for p in dotted.split("."):
        d = d[p]
    return d


@pytest.mark.parametrize("name", _FIXTURES)
def test_fixture_loads_through_shim_with_exactly_the_era_keys(name):
    """(i) Positive half: the shim supplies exactly the era keys and the world builds."""
    raw, path = _load_fixture(name)
    cfg_load = copy.deepcopy(raw)
    supplied = apply_saved_config_compat(cfg_load, source=path)
    assert supplied == _SEVEN
    params = load_env_params(Config(cfg_load))
    assert params.thermal_enabled


@pytest.mark.parametrize("name", _FIXTURES)
def test_fixture_raw_load_fails_on_missing_key(name):
    """(ii) Negative half: without the shim the frozen config does not load.

    Unconditional: this is the reason the compat step exists once the body-mechanics keys
    are mandatory.
    """
    raw, _ = _load_fixture(name)
    with pytest.raises(ValueError, match="required but missing"):
        load_env_params(Config(copy.deepcopy(raw)))


def test_source_under_configs_is_refused():
    """(iii) The live path keeps hard-erroring."""
    raw, _ = _load_fixture(_FIXTURES[1])
    live = os.path.join(_REPO, "configs", "environment", "default.yaml")
    with pytest.raises(ValueError, match="resolves under"):
        apply_saved_config_compat(copy.deepcopy(raw), source=live)


def test_partial_thermal_block_is_refused():
    """(iv) Two of the four thermal keys present -> an edited or foreign file."""
    raw, _ = _load_fixture(_FIXTURES[1])
    cfg = copy.deepcopy(raw)
    cfg["thermal"]["random_start_body_temp"] = False
    cfg["thermal"]["healing_cold_sensitivity"] = 0.0
    with pytest.raises(ValueError, match="thermal block carries"):
        apply_saved_config_compat(cfg, source=_SAVED_SOURCE)


def test_partial_body_block_is_refused():
    """(iv) One of the two body keys present -> an edited or foreign file."""
    raw, _ = _load_fixture(_FIXTURES[1])
    cfg = copy.deepcopy(raw)
    cfg["body"]["healing_nutrition_cost"] = 0.0
    with pytest.raises(ValueError, match="body block carries"):
        apply_saved_config_compat(cfg, source=_SAVED_SOURCE)


def test_present_keys_are_not_overwritten():
    """(v) A later-era run carries the keys for real; nothing is supplied or changed."""
    raw, _ = _load_fixture(_FIXTURES[1])
    cfg = copy.deepcopy(raw)
    cfg["thermal"].update(random_start_body_temp=True, healing_cold_sensitivity=0.1,
                          healing_warm_sensitivity=0.05, injury_heat_exchange_gain=1.0,
                          bush_min_fire_distance=3)
    cfg["body"].update(healing_nutrition_cost=0.5, healing_nutrition_dependence=True)
    cfg["water"] = {"enabled": False}
    before = copy.deepcopy(cfg)
    assert apply_saved_config_compat(cfg, source=_SAVED_SOURCE) == []
    assert cfg == before


def test_deep_copy_pattern_keeps_caller_dict_and_fingerprint():
    """(vi) Unit level: the dict the caller hashes is untouched by the pattern."""
    raw, path = _load_fixture(_FIXTURES[1])
    snapshot = copy.deepcopy(raw)
    fp_before = env_fingerprint(raw)
    cfg_load = copy.deepcopy(raw)
    apply_saved_config_compat(cfg_load, source=path)
    assert raw == snapshot
    assert env_fingerprint(raw) == fp_before
    assert env_fingerprint(cfg_load) != fp_before   # the injection is real


@pytest.mark.parametrize("rel", _CALL_SITES)
def test_every_call_site_injects_into_a_deep_copy(rel):
    """(vi) Structural: each wired site passes a variable bound from `copy.deepcopy(...)`.

    Injecting into the dict the trajectory store hashes would fork every store started
    before the keys became mandatory (plan §A7, reviewer N1).
    """
    path = os.path.join(_REPO, rel)
    with open(path) as fh:
        src = fh.read()
    calls = re.findall(r"apply_saved_config_compat\(\s*(\w+)\s*,", src)
    assert calls, f"{rel}: no apply_saved_config_compat call"
    for var in calls:
        assert re.search(rf"\b{var}\s*=\s*copy\.deepcopy\(", src), (
            f"{rel}: apply_saved_config_compat({var}, ...) but {var} is not bound from "
            "copy.deepcopy(...)")


def test_thermal_off_config_gets_only_body_keys():
    """(vii) The four thermal keys are read only when thermal is on; never supplied off."""
    raw, _ = _load_fixture(_FIXTURES[1])
    cfg = copy.deepcopy(raw)
    cfg["thermal"]["enabled"] = False
    assert apply_saved_config_compat(cfg, source=_SAVED_SOURCE) == [
        "body.healing_nutrition_cost", "body.healing_nutrition_dependence",
        "water.enabled"]
    assert "random_start_body_temp" not in cfg["thermal"]


def test_pre_thermal_config_gets_no_thermal_keys():
    """Rule (d): no `thermal.enabled` at all -> supply no thermal key."""
    raw, _ = _load_fixture(_FIXTURES[1])
    cfg = copy.deepcopy(raw)
    del cfg["thermal"]
    assert apply_saved_config_compat(cfg, source=_SAVED_SOURCE) == [
        "body.healing_nutrition_cost", "body.healing_nutrition_dependence",
        "water.enabled"]
    assert "thermal" not in cfg


def test_supplied_values_are_the_inert_values():
    raw, path = _load_fixture(_FIXTURES[0])
    cfg = copy.deepcopy(raw)
    apply_saved_config_compat(cfg, source=path)
    assert _get(cfg, "thermal.random_start_body_temp") is False
    assert _get(cfg, "thermal.healing_cold_sensitivity") == 0.0
    assert _get(cfg, "thermal.healing_warm_sensitivity") == 0.0
    assert _get(cfg, "thermal.injury_heat_exchange_gain") == 0.0
    assert _get(cfg, "body.healing_nutrition_cost") == 0.0
    assert _get(cfg, "body.healing_nutrition_dependence") is False
    assert _get(cfg, "thermal.bush_min_fire_distance") == 0
    assert _get(cfg, "water.enabled") is False


# --- BUSH_FIRE_CLEARANCE C0: all-or-none is checked per (block, era), not per block ------

_BODY_MECH_THERMAL = dict(random_start_body_temp=False, healing_cold_sensitivity=0.0,
                          healing_warm_sensitivity=0.0, injury_heat_exchange_gain=0.0)


def test_body_mechanics_era_config_gets_only_the_bush_key():
    """A run trained after the body-mechanics change but before the bush-clearance key.

    It carries all four body-mechanics thermal keys and both body keys, and lacks only
    `thermal.bush_min_fire_distance`. It must get exactly that key and must NOT be refused
    as an edited file (a block-level all-or-none would call it "4 of 5 present").
    """
    raw, _ = _load_fixture(_FIXTURES[1])
    cfg = copy.deepcopy(raw)
    cfg["thermal"].update(_BODY_MECH_THERMAL)
    cfg["body"].update(healing_nutrition_cost=0.0, healing_nutrition_dependence=False)
    assert apply_saved_config_compat(cfg, source=_SAVED_SOURCE) == [
        "thermal.bush_min_fire_distance", "water.enabled"]
    assert cfg["thermal"]["bush_min_fire_distance"] == 0


def test_partial_era_group_is_still_refused():
    """Two of the four body-mechanics thermal keys, with the later bush key present, is
    still an edited file: all-or-none holds inside each era."""
    raw, _ = _load_fixture(_FIXTURES[1])
    cfg = copy.deepcopy(raw)
    cfg["thermal"].update(random_start_body_temp=False, healing_cold_sensitivity=0.0,
                          bush_min_fire_distance=0)
    with pytest.raises(ValueError, match="thermal block carries"):
        apply_saved_config_compat(cfg, source=_SAVED_SOURCE)


def test_era_grouping_is_generic(monkeypatch):
    """The grouping is built from the era strings in `_ERA_KEYS`, not from named constants:
    a synthetic third era is supplied whole when absent and refused when partial."""
    import src.environment.saved_config_compat as compat
    table = dict(compat._ERA_KEYS)
    table["thermal.synthetic_a"] = (1.5, "SYNTHETIC era (test only)", "test")
    table["thermal.synthetic_b"] = (False, "SYNTHETIC era (test only)", "test")
    monkeypatch.setattr(compat, "_ERA_KEYS", table)

    raw, _ = _load_fixture(_FIXTURES[1])
    cfg = copy.deepcopy(raw)
    cfg["thermal"].update(_BODY_MECH_THERMAL, bush_min_fire_distance=0)
    cfg["body"].update(healing_nutrition_cost=0.0, healing_nutrition_dependence=False)
    cfg["water"] = {"enabled": False}
    assert compat.apply_saved_config_compat(copy.deepcopy(cfg), source=_SAVED_SOURCE) == [
        "thermal.synthetic_a", "thermal.synthetic_b"]

    cfg["thermal"]["synthetic_a"] = 1.5
    with pytest.raises(ValueError, match="thermal block carries.*SYNTHETIC era"):
        compat.apply_saved_config_compat(cfg, source=_SAVED_SOURCE)


# --- THIRST_WATER_PLAN C2: the water gate ----------------------------------------------

def test_pre_water_config_gets_only_the_water_gate():
    """A run saved after every earlier era but before water: exactly `water.enabled: false`
    is supplied, no other water key, and the world builds with water off."""
    raw, _ = _load_fixture(_FIXTURES[1])
    cfg = copy.deepcopy(raw)
    cfg["thermal"].update(_BODY_MECH_THERMAL, bush_min_fire_distance=0)
    cfg["body"].update(healing_nutrition_cost=0.0, healing_nutrition_dependence=False)
    assert "water" not in cfg
    assert apply_saved_config_compat(cfg, source=_SAVED_SOURCE) == ["water.enabled"]
    assert cfg["water"] == {"enabled": False}
    assert load_env_params(Config(cfg)).water_enabled is False
