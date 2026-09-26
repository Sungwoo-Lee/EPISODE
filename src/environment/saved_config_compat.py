"""Read-only compatibility layer for SAVED run configs (archived-run re-analysis).

What it does
------------
Evaluation, replay and trajectory collection rebuild a finished run's world from the
run's OWN frozen copy of its settings, ``results/<algo>/<run>/models/config.yaml``.
When a later change makes a new config key mandatory, every such frozen copy stops
loading: ``load_env_params`` raises "Configuration key ... is required but missing".
``apply_saved_config_compat`` supplies exactly the enumerated keys in ``_ERA_KEYS``, at
the value that reproduces what the old code did, so the frozen run can be re-opened.

What it deliberately does NOT do
--------------------------------
* It never softens the LIVE path. A ``source`` that resolves under the repo's
  ``configs/`` directory is refused: a file a human wrote must keep hard-erroring on a
  missing key (the project's no-fallback-defaults rule). Only saved run configs are
  eligible.
* It never supplies a key that is not in ``_ERA_KEYS``. A new mandatory key that is not
  listed here still fails loudly.
* It never overwrites a key that is already present (a later-era run set it for real).
* It writes nothing to disk. It mutates the dict it is handed, and **callers pass it a
  deep copy** (``cfg_load = copy.deepcopy(cfg)``) and build ``EnvParams`` from that copy.
  The untouched original is what anything that hashes or records the config sees -- in
  particular the trajectory store's ``env_fingerprint`` and manifest, so a store started
  before a key became mandatory resumes into the SAME directory afterwards
  (SAVED_RUN_CONFIG_COMPAT §A10).
* It does not import ``config_loader`` or ``src.utils.config`` (no import cycle to reason
  about), and no module on the training path imports it.

Scope and lineage
-----------------
This module is the FIRST SLICE of the plan
``docs/develop/active/refactors/SAVED_RUN_CONFIG_COMPAT.md`` (PLANNED, owned by another
session), created by ``docs/develop/active/thermal/STATE_DEPENDENT_BODY_MECHANICS.md``
(commit C0). It follows that plan's module path, function name and refusal rules so the
owner can extend it rather than replace it. ``_ERA_KEYS`` holds ONLY the six keys of the
body-mechanics change. The owner adds the Stage 1/2 rows (``thermal.enabled``, the
sensory keys) and the manifest ``saved_config_compat`` field.

Rule for ``_ERA_KEYS`` rows (the compat plan's rule): every row needs the supplied
value, the era it became mandatory, and the branch that makes that value inert. A value
here is a CLAIM ABOUT WHAT THE OLD CODE DID. Changing a value is a breaking change for
any trajectory store collected under the old value.
"""
from __future__ import annotations

import logging
from pathlib import Path

_log = logging.getLogger(__name__)

# Repo root = two levels above src/environment/.
_CONFIGS_DIR = (Path(__file__).resolve().parents[2] / "configs").resolve()

_ERA = "STATE_DEPENDENT_BODY_MECHANICS C2 (2026-09-26)"

# dotted key -> (value that reproduces the pre-change behaviour, era, branch that makes it inert)
_ERA_KEYS = {
    # --- thermal block: supplied only when the saved thermal.enabled is true -------------
    "thermal.random_start_body_temp": (
        False, _ERA,
        "B1: static `if params.thermal_random_start_body_temp` in core.jax_reset; false "
        "keeps body_temp0 = temperature_setpoint (today's reset). Range keys not read."),
    "thermal.healing_cold_sensitivity": (
        0.0, _ERA,
        "B2: static gate `if s_c != 0 or s_w != 0` in core.update_body; both 0 = untraced."),
    "thermal.healing_warm_sensitivity": (
        0.0, _ERA,
        "B2: same static gate as healing_cold_sensitivity."),
    "thermal.injury_heat_exchange_gain": (
        0.0, _ERA,
        "B4: static gate `if gain != 0` in the body-temperature block of core.update_body; "
        "0 = k_exchange unchanged. The mode key is not read."),
    # --- body block: always supplied --------------------------------------------------
    "body.healing_nutrition_cost": (
        0.0, _ERA,
        "B3: static gate `if params.healing_nutrition_cost != 0` in core.update_body; 0 = "
        "today's statements in today's order. The shortfall key is not read."),
    "body.healing_nutrition_dependence": (
        False, _ERA,
        "B5: static `if params.healing_nutrition_dependence` in core.update_body; false = "
        "untraced. The ramp keys are not read."),
}

# Parity instrument for every row above: tests/env/test_body_mechanics_parity.py.

_THERMAL_KEYS = tuple(k for k in _ERA_KEYS if k.startswith("thermal."))
_BODY_KEYS = tuple(k for k in _ERA_KEYS if k.startswith("body."))


def _has(cfg: dict, dotted: str) -> bool:
    d = cfg
    for part in dotted.split("."):
        if not isinstance(d, dict) or part not in d:
            return False
        d = d[part]
    return True


def _set(cfg: dict, dotted: str, value) -> None:
    parts = dotted.split(".")
    d = cfg
    for part in parts[:-1]:
        d = d.setdefault(part, {})
    d[parts[-1]] = value


def _under_configs(source: str) -> bool:
    p = Path(source).resolve()
    return p == _CONFIGS_DIR or _CONFIGS_DIR in p.parents


def apply_saved_config_compat(cfg: dict, *, source: str) -> list[str]:
    """Supply the era keys a frozen run config predates. In memory only.

    MUTATES ``cfg``. Callers pass a deep copy and build ``EnvParams`` from it; the
    original (unmodified) dict is what fingerprints and manifests must see.

    Rules:
      (a) ``source`` resolving under the repo's ``configs/`` -> ``ValueError`` (the live
          path keeps hard-erroring).
      (b) a key already present is left alone.
      (c) all-or-none per block: a thermal-on block carrying some but not all of the four
          thermal keys, or a body block carrying one of the two body keys but not the
          other, is an edited or foreign file -> ``ValueError``.
      (d) the thermal keys are supplied only when the saved ``thermal.enabled`` is true.
          A config lacking ``thermal.enabled`` altogether (a pre-thermal run) gets none of
          them, and the loader fails on ``thermal.enabled`` as it does today.

    Logs one WARNING line naming every key supplied, its value and ``source``.
    Returns the sorted list of keys supplied (callers print it).
    """
    if not isinstance(cfg, dict):
        raise TypeError(f"apply_saved_config_compat expects a dict, got {type(cfg).__name__}")
    if _under_configs(source):
        raise ValueError(
            f"apply_saved_config_compat refused: {source!r} resolves under {_CONFIGS_DIR}. "
            "The compat step is for SAVED run configs only; a live config under configs/ "
            "must carry every mandatory key.")

    to_supply: list[str] = []

    # --- thermal block (only when thermal.enabled is true) ---
    thermal = cfg.get("thermal")
    thermal_on = isinstance(thermal, dict) and thermal.get("enabled") is True
    if thermal_on:
        present = [k for k in _THERMAL_KEYS if _has(cfg, k)]
        if present and len(present) != len(_THERMAL_KEYS):
            missing = [k for k in _THERMAL_KEYS if k not in present]
            raise ValueError(
                f"apply_saved_config_compat refused ({source}): the thermal block carries "
                f"{present} but not {missing}. A saved config carries all four or none; a "
                "partial set means an edited or foreign file.")
        if not present:
            to_supply.extend(_THERMAL_KEYS)

    # --- body block (always) ---
    present = [k for k in _BODY_KEYS if _has(cfg, k)]
    if present and len(present) != len(_BODY_KEYS):
        missing = [k for k in _BODY_KEYS if k not in present]
        raise ValueError(
            f"apply_saved_config_compat refused ({source}): the body block carries "
            f"{present} but not {missing}. A saved config carries both or neither; a "
            "partial set means an edited or foreign file.")
    if not present:
        to_supply.extend(_BODY_KEYS)

    for k in to_supply:
        _set(cfg, k, _ERA_KEYS[k][0])

    supplied = sorted(to_supply)
    if supplied:
        _log.warning(
            "saved-config compat: supplied %s for %s",
            ", ".join(f"{k}={_ERA_KEYS[k][0]!r}" for k in supplied), source)
    return supplied
