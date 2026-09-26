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
owner can extend it rather than replace it. ``_ERA_KEYS`` holds the keys of more than one
era: the six keys of the body-mechanics change, and the bush-to-fire clearance key of
``docs/develop/active/thermal/BUSH_FIRE_CLEARANCE.md``. The owner adds the Stage 1/2 rows
(``thermal.enabled``, the sensory keys) and the manifest ``saved_config_compat`` field.

All-or-none is checked per (block, era), not per block. The keys of one era arrived
together, so a saved config carrying some of an era's keys but not all of them is an
edited or foreign file. Keys of different eras are independent: a run trained between two
eras carries every key of the earlier era and none of the later one. The groups are built
from the table itself (grouped by block prefix and era string), so an era added here later
is covered without editing the grouping logic.

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

_ERA_BODY_MECHANICS = "STATE_DEPENDENT_BODY_MECHANICS C2 (2026-09-26)"
_ERA_BUSH = "BUSH_FIRE_CLEARANCE C2 (2026-09-26)"

# dotted key -> (value that reproduces the pre-change behaviour, era, branch that makes it inert)
_ERA_KEYS = {
    # --- thermal block: supplied only when the saved thermal.enabled is true -------------
    "thermal.random_start_body_temp": (
        False, _ERA_BODY_MECHANICS,
        "B1: static `if params.thermal_random_start_body_temp` in core.jax_reset; false "
        "keeps body_temp0 = temperature_setpoint (today's reset). Range keys not read."),
    "thermal.healing_cold_sensitivity": (
        0.0, _ERA_BODY_MECHANICS,
        "B2: static gate `if s_c != 0 or s_w != 0` in core.update_body; both 0 = untraced."),
    "thermal.healing_warm_sensitivity": (
        0.0, _ERA_BODY_MECHANICS,
        "B2: same static gate as healing_cold_sensitivity."),
    "thermal.injury_heat_exchange_gain": (
        0.0, _ERA_BODY_MECHANICS,
        "B4: static gate `if gain != 0` in the body-temperature block of core.update_body; "
        "0 = k_exchange unchanged. The mode key is not read."),
    # --- body block: always supplied --------------------------------------------------
    "body.healing_nutrition_cost": (
        0.0, _ERA_BODY_MECHANICS,
        "B3: static gate `if params.healing_nutrition_cost != 0` in core.update_body; 0 = "
        "today's statements in today's order. The shortfall key is not read."),
    "body.healing_nutrition_dependence": (
        False, _ERA_BODY_MECHANICS,
        "B5: static `if params.healing_nutrition_dependence` in core.update_body; false = "
        "untraced. The ramp keys are not read."),
    # --- thermal block, bush-to-fire clearance era ---------------------------------------
    "thermal.bush_min_fire_distance": (
        0, _ERA_BUSH,
        "static `if params.thermal_bush_min_fire_distance > 0` in core.jax_reset; 0 = the "
        "bush pass is not traced (tests/env/test_bush_fire_clearance.py parity)."),
}

# Parity instruments: tests/env/test_body_mechanics_parity.py (body-mechanics era) and
# tests/env/test_bush_fire_clearance.py (bush-clearance era).


def _era_groups(block: str) -> list[tuple[str, tuple[str, ...]]]:
    """``[(era, keys), ...]`` for every era with rows in ``block``, in table order.

    Built from ``_ERA_KEYS`` at call time, grouped by the era string of each row, so it
    covers every era the table holds and is not tied to any named era constant.
    """
    groups: dict[str, list[str]] = {}
    for k, (_value, era, _branch) in _ERA_KEYS.items():
        if k.split(".", 1)[0] == block:
            groups.setdefault(era, []).append(k)
    return [(era, tuple(keys)) for era, keys in groups.items()]


def _check_block(cfg: dict, block: str, source: str) -> list[str]:
    """All-or-none per (block, era); return the keys of every wholly-absent era."""
    to_supply: list[str] = []
    for era, keys in _era_groups(block):
        present = [k for k in keys if _has(cfg, k)]
        if present and len(present) != len(keys):
            missing = [k for k in keys if k not in present]
            raise ValueError(
                f"apply_saved_config_compat refused ({source}): the {block} block carries "
                f"{present} but not {missing} (era {era!r}). A saved config carries all "
                f"{len(keys)} keys of an era or none; a partial set means an edited or "
                "foreign file.")
        if not present:
            to_supply.extend(keys)
    return to_supply


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
      (c) all-or-none per (block, era): a block carrying some but not all of one era's
          keys (e.g. two of the four body-mechanics thermal keys) is an edited or foreign
          file -> ``ValueError``. Keys of different eras are independent.
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
        to_supply.extend(_check_block(cfg, "thermal", source))

    # --- body block (always) ---
    to_supply.extend(_check_block(cfg, "body", source))

    for k in to_supply:
        _set(cfg, k, _ERA_KEYS[k][0])

    supplied = sorted(to_supply)
    if supplied:
        _log.warning(
            "saved-config compat: supplied %s for %s",
            ", ".join(f"{k}={_ERA_KEYS[k][0]!r}" for k in supplied), source)
    return supplied
