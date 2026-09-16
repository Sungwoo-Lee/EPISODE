#!/usr/bin/env python
"""Generate the render-audit fixture recordings (RENDERER_LAYOUT_REDESIGN.md, section D5.1).

WHAT THIS IS. The renderer redesign needs one saved episode recording per "matrix cell" —
one per kind of world the dashboard has to draw (a default world, a world with perceptual
noise on, the campfire temperature world, a world with a directional smell, and so on).
This script produces them by stepping the REAL environment with a seeded random policy and
writing the result through the PRODUCTION recording writer, so a fixture is byte-shaped
exactly like a recording a real evaluation run would leave behind. Nothing here is a mock.

WHERE THE WORLDS COME FROM (Revision 10 of the plan; the config-maintenance rule).
Only two places are maintained: `configs/environment/default.yaml` and
`configs/environment/experiment/basic/`. Everything else under `configs/environment/
experiment/` is archive and is deliberately NOT kept loadable. So every cell loads one of
those two, then applies an **in-memory override** — a small dict of YAML keys set on the
resolved config before the environment is built. No config file is ever written by this
script, and a cell pointing anywhere outside the maintained set raises.

WHAT EACH FIXTURE RECORDS ABOUT ITSELF. `run_meta.pkl`'s `extras` carries, per cell:
  synthetic            True when in-memory overrides were applied (so "E7" cannot be
                       mistaken for a config file that exists on disk)
  overrides            the exact key -> value map applied
  overrides_source     where the override VALUES were copied from, as text, when they
                       reproduce an archived world
  provenance           plain-language warning, when the cell's world reproduces an
                       archived one but NOT under the archived rules, so that anyone
                       comparing these recordings with older ones knows which rules they
                       were recorded under (cells M4/M4b: the current bush rule)
  config_path          the maintained config that was loaded
  config_sha256        sha256 of the RESOLVED config (after `extends:` layering, before
                       overrides), serialised as sorted-key JSON
  config_chain_sha256  {file: sha256} for every file in the `extends:` chain
so that a later edit to a config by another session makes "M4" visibly mean something
different rather than silently changing.

USAGE
    python scripts/eval/make_render_fixture_recordings.py                  # CP0.2 cells
    python scripts/eval/make_render_fixture_recordings.py --cells M4 M4b
    python scripts/eval/make_render_fixture_recordings.py --report-only    # re-print CP0.2

Output goes to `results/render_audit/recordings/<cell>/<cell>/` (gitignored). The doubled
leaf name is deliberate: `render_recordings.py` derives its video directory as
`<rec_dir>.parent.parent / "videos" / <rec_dir>.name`, so a unique leaf keeps two cells'
videos from colliding (wiki `render_recordings_output_path_collision`).

This script imports the frozen V1 modules READ-ONLY and edits none of them.
"""
from __future__ import annotations

import argparse
import dataclasses
import gzip
import hashlib
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

os.environ.setdefault("XLA_PYTHON_CLIENT_PREALLOCATE", "false")
os.environ.setdefault("JAX_PLATFORMS", "cpu")

DEFAULT_CONFIG = "configs/environment/default.yaml"
BASIC_PREFIX = "configs/environment/experiment/basic/"
DEFAULT_OUT = "results/render_audit/recordings"

# The campfire temperature world regenerated for this plan (Revision 10, cell M4).
CAMPFIRE = BASIC_PREFIX + "06-campfire_thermal_10x10.yaml"
NOISE_WORLD = BASIC_PREFIX + "05-sensory_noise_10x10.yaml"

# Where override values that reproduce an archived world were copied from, AS TEXT.
_LADDER = "configs/environment/experiment/archive/sensory_ladder/"

# Cells M4/M4b copy the archived campfire world's numbers but run under the CURRENT bush
# rule, so their recorded behaviour is not the archived world's. Carried in run_meta so a
# later reader comparing these recordings with pre-2026-09-14 ones cannot miss it.
_CAMPFIRE_PROVENANCE = (
    "Reproduces the archived campfire world "
    "(configs/environment/experiment/archive/thermal/campfire_world.yaml) ON THE CURRENT "
    "BUSH RULE: bushes block animals (obs_blocks_animals True), where the archived world's "
    "bushes did not. That is the only differing field of 190, and the 33-dim observation is "
    "identical, but src/environment/core.py:609 feeds the flag into the animal movement "
    "mask, so animal trajectories and rewards diverge from the archived world at step one. "
    "These recordings are POST-BUSH-CHANGE (rule canonical since 2026-09-14) and are NOT "
    "frame-comparable with anything recorded before it."
)


@dataclasses.dataclass(frozen=True)
class Cell:
    """One matrix cell: a maintained config plus an in-memory override."""
    config: str
    overrides: dict
    what: str                       # plain-language description, printed in the report
    overrides_source: str = ""      # where the override VALUES came from, as text
    provenance: str = ""            # which RULES this world was recorded under, as text
    no_true_obs: bool = False       # record `true_obs=None` (the "true obs not recorded" path)

    @property
    def synthetic(self) -> bool:
        return bool(self.overrides)


# Vision radius 2, blur and occlusion off — the base every E-cell vision override builds on.
_E2 = {
    "sensory.visual_sensor_enabled": True,
    "sensory.visual_sensor_range": 2,
    "sensory.visual_blur_enabled": False,
    "sensory.visual_occlusion_enabled": False,
}

CELLS: dict[str, Cell] = {
    # ---- M cells: the CP0.2 set -------------------------------------------------------
    "M1": Cell(DEFAULT_CONFIG, {}, "default world, spectrum smell, perceptual noise off"),
    "M1x": Cell(DEFAULT_CONFIG, {"sensory.interoceptive_nociception_enabled": False},
                "default world with interoceptive nociception DISABLED (the 'no row' case "
                "for CP2.5; default.yaml now ships it on)"),
    "M2": Cell(DEFAULT_CONFIG, {},
               "interoceptive nociception observed, noise off. Revision 10 re-sources this "
               "to default.yaml, which already ships nociception on and noise off, so M2's "
               "world is identical to M1's by construction"),
    "M3": Cell(NOISE_WORLD, {},
               "same, with injury-gated perceptual noise on (level-05 basic world; "
               "interoceptive nociception is already on via inheritance, so no override)"),
    "M4": Cell(CAMPFIRE, {},
               "campfire temperature world: observation lacks Nutrition/Injury and includes "
               "Body Temperature and Thermoception",
               provenance=_CAMPFIRE_PROVENANCE),
    "M4b": Cell(CAMPFIRE, {"thermal.body_temp_observable": False},
                "M4 with body temperature removed from the observation, so the temperature "
                "row takes the 'not observed' path",
                provenance=_CAMPFIRE_PROVENANCE),
    "M5": Cell(DEFAULT_CONFIG, {"sensory.olfactory_grid_range": 1},
               "olfaction as a directional grid (radius 1)"),
    "M6": Cell(DEFAULT_CONFIG, {"sensory.location_sensor": True},
               "location sensor on"),
    "M6b": Cell(NOISE_WORLD, {},
                "M3's world recorded WITHOUT true observations, exercising the "
                "'true obs not recorded' caption",
                no_true_obs=True),

    # ---- E cells: extended-range senses (Phase 2 / CP2.7; defined here, not run at CP0.2)
    "E1": Cell(DEFAULT_CONFIG,
               {"sensory.olfactory_grid_range": 1, "sensory.visual_sensor_range": 0},
               "directional smell radius 1, vision at radius 0",
               overrides_source=_LADDER + "B_olf_only.yaml (olfactory_grid_range: 1, "
                                          "visual_sensor_range: 0)"),
    "E1n": Cell(NOISE_WORLD, {"sensory.olfactory_grid_range": 1},
                "smell radius 1 with perceptual noise on"),
    "E2": Cell(DEFAULT_CONFIG, dict(_E2, **{"sensory.olfactory_grid_range": 1}),
               "vision radius 2, sharp (no blur, no occlusion)",
               overrides_source=_LADDER + "V5_sharp.yaml (visual_sensor_range: 2, "
                                          "visual_blur_enabled: false, "
                                          "visual_occlusion_enabled: false, "
                                          "olfactory_grid_range: 1)"),
    "E2n": Cell(NOISE_WORLD, dict(_E2, **{"sensory.olfactory_grid_range": 1}),
                "vision radius 2 with perceptual noise on"),
    "E3": Cell(DEFAULT_CONFIG, dict(_E2, **{
        "sensory.olfactory_grid_range": 1,
        "sensory.visual_blur_enabled": True,
        "sensory.visual_blur_radial_scale": 4.0,
        "sensory.visual_blur_anisotropy": 3.0,
        "sensory.visual_blur_sigma_floor": 0.5,
    }), "vision radius 2 with anisotropic blur",
        overrides_source=_LADDER + "V1_blur40.yaml (visual_blur_radial_scale: 4.0, "
                                   "visual_blur_anisotropy: 3.0, "
                                   "visual_blur_sigma_floor: 0.5)"),
    "E4": Cell(DEFAULT_CONFIG, dict(_E2, **{
        "sensory.olfactory_grid_range": 1,
        "sensory.visual_blur_enabled": True,
        "sensory.visual_blur_radial_scale": 0.5,
        "sensory.visual_blur_anisotropy": 1.0,
        "sensory.visual_blur_sigma_floor": 0.5,
    }), "vision radius 2 with isotropic blur",
        overrides_source=_LADDER + "P1_blur05_iso.yaml (visual_blur_radial_scale: 0.5, "
                                   "visual_blur_anisotropy: 1.0, "
                                   "visual_blur_sigma_floor: 0.5)"),
    "E5": Cell(DEFAULT_CONFIG, dict(_E2, **{
        "sensory.olfactory_grid_range": 1,
        "sensory.visual_blur_enabled": True,
        "sensory.visual_occlusion_enabled": True,
        "sensory.visual_occlusion_cone_deg": 15.0,
        "sensory.visual_occlusion_strength": 1.0,
    }), "vision radius 2 with line-of-sight occlusion",
        overrides_source=_LADDER + "O3_occl_all.yaml (visual_occlusion_enabled: true, "
                                   "visual_occlusion_cone_deg: 15.0, "
                                   "visual_occlusion_strength: 1.0, "
                                   "visual_blur_enabled: true)"),
    "E6sum": Cell(DEFAULT_CONFIG, dict(_E2, **{
        "sensory.olfactory_grid_range": 1,
        "sensory.visual_blur_enabled": True,
        "sensory.visual_value_mode": "sum",
        "sensory.visual_vector_size": 1,
    }), "vision radius 2, single visual channel, SUMMED presence values",
        overrides_source=_LADDER + "Q1_presence_sum.yaml (visual_vector_size: 1, "
                                   "visual_value_mode: sum)"),
    "E6bin": Cell(DEFAULT_CONFIG, dict(_E2, **{
        "sensory.olfactory_grid_range": 1,
        "sensory.visual_blur_enabled": True,
        "sensory.visual_value_mode": "clamp",
        "sensory.visual_vector_size": 1,
    }), "vision radius 2, single visual channel, BINARY presence values",
        overrides_source=_LADDER + "Q2_presence_binary.yaml (visual_vector_size: 1, "
                                   "visual_value_mode: clamp)"),
    "E7": Cell(DEFAULT_CONFIG, dict(_E2, **{
        "sensory.visual_sensor_range": 3, "sensory.olfactory_grid_range": 3,
    }), "synthetic stress: vision and smell at radius 3"),
    "E8": Cell(DEFAULT_CONFIG, dict(_E2, **{
        "sensory.visual_sensor_range": 4, "sensory.olfactory_grid_range": 4,
    }), "synthetic stress: vision and smell at radius 4"),
    "E9": Cell(DEFAULT_CONFIG, {
        "sensory.olfactory_grid_range": 4, "sensory.visual_sensor_enabled": False,
    }, "synthetic stress: smell at radius 4 with vision off"),
}

# The cells CP0.2 asks for. The E cells belong to CP2.7 (Phase 2) and are generated only
# when named explicitly.
CP02_CELLS = ["M1", "M1x", "M2", "M3", "M4", "M4b", "M5", "M6", "M6b"]

# The plan's real trained-policy cells. They load through their own saved run_meta.pkl,
# never through a config file, so the config-maintenance rule does not touch them. Read-only
# here; this script never writes into them.
REAL_RECORDINGS = {
    "M7": "results/eval/noPredator_chasingRabbit/models/9520028/recordings/9520028",
    "M8": "results/JAX_RecurrentPPO/20260501-005013_interoNocicept_predRange5_decoy75_std4"
          "/recordings/100049",
    "M9": "results/JAX_RecurrentPPO/20260501-050423_interoNocicept_predRange5_decoy75_std4"
          "_noise/recordings/100023",
}


# --------------------------------------------------------------------------- config utils


def _require_maintained(config_rel: str) -> None:
    """Refuse any config outside the maintained set (Revision 10)."""
    if config_rel != DEFAULT_CONFIG and not config_rel.startswith(BASIC_PREFIX):
        raise ValueError(
            f"config {config_rel!r} is outside the maintained set. A fixture cell may load "
            f"only {DEFAULT_CONFIG!r} or a file under {BASIC_PREFIX!r}; everything else "
            f"under configs/environment/experiment/ is archive and is deliberately not kept "
            f"loadable (CLAUDE.md, config maintenance scope). Express the world as an "
            f"in-memory override, or regenerate it as a maintained config."
        )


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _extends_chain(config_rel: str) -> dict:
    """{file: sha256} for the config and every file in its `extends:` chain."""
    import yaml
    chain, todo, seen = {}, [config_rel], set()
    configs_root = REPO_ROOT / "configs"
    while todo:
        rel = todo.pop(0)
        if rel in seen:
            continue
        seen.add(rel)
        path = REPO_ROOT / rel
        chain[rel] = _sha256_file(path)
        raw = yaml.safe_load(path.read_text()) or {}
        ext = raw.get("extends")
        if ext is None:
            continue
        for base in ([ext] if isinstance(ext, str) else list(ext)):
            todo.append(str((configs_root / (base + ".yaml")).relative_to(REPO_ROOT)))
    return chain


def _resolved_sha256(cfg) -> str:
    """sha256 of the resolved config (post-`extends:`), as sorted-key JSON."""
    return hashlib.sha256(
        json.dumps(cfg.to_dict(), sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()


# Conditional-mandatory keys: read only when their gate is on, and therefore absent (or
# commented out) from default.yaml while the gate is off. An override may legitimately
# introduce these; every other override key must already exist, or it is a typo.
_CONDITIONAL_KEYS = frozenset({
    "sensory.visual_occlusion_cone_deg",
    "sensory.visual_occlusion_strength",
})


def build_params(cell: Cell):
    """Resolve a cell to (params, config, extras-fragment). Overrides are in memory only."""
    from src.environment.config_loader import load_env_config, load_env_params

    _require_maintained(cell.config)
    cfg = load_env_config(str(REPO_ROOT / cell.config))
    meta = {
        "config_path": cell.config,
        "config_sha256": _resolved_sha256(cfg),
        "config_chain_sha256": _extends_chain(cell.config),
        "synthetic": cell.synthetic,
        "overrides": dict(cell.overrides),
        "overrides_source": cell.overrides_source,
        "provenance": cell.provenance,
        "cell_description": cell.what,
        "true_obs_recorded": not cell.no_true_obs,
    }
    for key, value in cell.overrides.items():
        if cfg.get(key, None) is None and key not in _CONDITIONAL_KEYS:
            # A typo'd override key would otherwise be silently inert.
            raise ValueError(
                f"override key {key!r} is not present in {cell.config!r}; an override that "
                f"names no existing key would silently do nothing. If the key is genuinely "
                f"conditional-mandatory (read only when its gate is on, and therefore "
                f"commented out while the gate is off), add it to _CONDITIONAL_KEYS."
            )
        cfg.set(key, value)
    return load_env_params(cfg), cfg, meta


def _icon_config():
    """The same `visualization.icons` mapping every production video is drawn with."""
    from src.utils.config import Config
    viz = Config.load_yaml(str(REPO_ROOT / "configs/visualization/default.yaml"))
    return viz.get("visualization.icons", None)


def _action_map(params):
    names = ["Up", "Right", "Down", "Left"]
    if params.rest_action_enabled:
        names.append("Rest")
    if params.eat_action_enabled:
        names.append("Eat")
    return names


# --------------------------------------------------------------------------- generation


def _clear_stale_recordings(rec_dir: Path, out_root: Path, name: str) -> list:
    """Remove THIS cell's own episode files before regenerating it.

    WHY. The cell directory is reused (`mkdir(exist_ok=True)`), so a run that writes
    FEWER episodes than the previous one used to leave orphans behind: regenerate with
    `--episodes 2` over an old `--episodes 3` run and `episode_000003.rec.gz` survived.
    `v1_path_guard.py` hashes every `episode_*.rec.gz` it finds in the directory, so the
    orphan made the guard report FIXTURE CHANGED for a fixture that had in fact been
    regenerated identically — a spurious failure that would train the reader to re-record
    the frame baseline to silence it.

    SCOPE, deliberately narrow. This deletes files under gitignored `results/`, and this
    project has lost `results/` once already (CLAUDE.md, Git safety). So: the directory
    must be exactly `<out_root>/<cell>/<cell>` or this raises; only individual regular
    files matching `episode_*.rec.gz` are unlinked; never a directory, never a symlink,
    never a recursive tree, never a glob outside this one cell. `run_meta.pkl` is left
    alone deliberately — `write_run_meta` rewrites it in place in the same call, so no
    stale copy of it can survive regeneration anyway.
    """
    expected = (out_root / name / name).resolve()
    if rec_dir.resolve() != expected:
        raise ValueError(
            f"refusing to clear {rec_dir}: it is not cell {name!r}'s own directory "
            f"({expected}). Only a cell's own recordings are ever removed."
        )
    removed = []
    for p in sorted(rec_dir.glob("episode_*.rec.gz")):
        if p.is_symlink() or not p.is_file():
            raise ValueError(f"refusing to remove {p}: not a regular file")
        p.unlink()
        removed.append(p.name)
    return removed


def generate_cell(name: str, cell: Cell, out_root: Path, episodes: int,
                  max_steps: int, seed: int) -> Path:
    """Step the real environment and write recordings through the production writer."""
    import jax
    from src.environment.core import jax_reset, jax_step
    from src.environment.sensor import get_observation
    from src.utils.eval_recording import EpisodeRecorder, write_run_meta

    params, _cfg, meta = build_params(cell)
    rec_dir = out_root / name / name
    rec_dir.mkdir(parents=True, exist_ok=True)
    stale = _clear_stale_recordings(rec_dir, out_root, name)
    if stale:
        print(f"  {name}: cleared {len(stale)} stale recording(s) from a previous run: "
              f"{stale}")

    record_true_obs = not cell.no_true_obs
    checkpoint_pct = 100

    write_run_meta(
        rec_dir, params, _icon_config(), _action_map(params), cell.config,
        extras={"checkpoint_pct": checkpoint_pct, "seed": seed,
                "generator": "scripts/eval/make_render_fixture_recordings.py",
                "cell": name, "policy": "seeded random", **meta},
    )

    for ep in range(episodes):
        key = jax.random.PRNGKey(seed + ep)
        key, reset_key = jax.random.split(key)
        state = jax_reset(params, reset_key)
        obs = get_observation(state, params)
        true_obs = get_observation(state, params, apply_noise=False) if record_true_obs else None

        recorder = EpisodeRecorder(episode_index=ep + 1, train_episode=checkpoint_pct,
                                   seed=seed + ep)
        recorder.append(jax.device_get(state), obs, true_obs, action_idx=-1, reward=0.0)

        done, steps = False, 0
        while not done and steps < max_steps:
            key, action_key = jax.random.split(key)
            action_idx = int(jax.random.randint(action_key, (), 0, params.action_dim))
            state, reward, done_arr, _info = jax_step(state, action_idx, params)
            done = bool(done_arr)
            steps += 1
            obs = get_observation(state, params)
            true_obs = (get_observation(state, params, apply_noise=False)
                        if record_true_obs else None)
            recorder.append(jax.device_get(state), obs, true_obs,
                            action_idx=action_idx, reward=float(reward))

        recorder.write(rec_dir / f"episode_{ep + 1:06d}.rec.gz")
        print(f"  {name}: episode {ep + 1} -> {steps + 1} snapshots"
              f"{'' if record_true_obs else ' (true_obs NOT recorded)'}")
    return rec_dir


# --------------------------------------------------------------------------- CP0.2 report


def _noise_mapping(params, breakdown):
    """breakdown name <-> perceptual-noise order name + mode, per plan section D4.2."""
    order = list(getattr(params, "noise_modality_order", None) or ())
    # `noise_modes` is a jnp array: `or []` would ask it for a truth value and raise.
    modes_raw = getattr(params, "noise_modes", None)
    modes = [] if modes_raw is None else [int(m) for m in modes_raw]
    rows, unresolved = [], []
    for bname in breakdown:
        if bname in order:
            idx = order.index(bname)
            rows.append(f"{bname} -> noise[{idx}] mode={modes[idx] if idx < len(modes) else '?'}")
        else:
            unresolved.append(bname)
    return rows, unresolved


def report_cell(name: str, out_root: Path, render_step0: bool, frame_dir: Path) -> dict:
    """Read a written fixture back from disk and print every CP0.2 fact about it."""
    import numpy as np
    from src.environment.sensor import (build_sensory_viz, get_observation_breakdown,
                                        get_visual_offsets)
    from src.utils.eval_recording import load_episode, load_run_meta

    rec_dir = (REPO_ROOT / REAL_RECORDINGS[name] if name in REAL_RECORDINGS
               else out_root / name / name)
    meta = load_run_meta(rec_dir)
    params = meta["params"]
    extras = meta["extras"]
    ep_files = sorted(rec_dir.glob("episode_*.rec.gz"))
    ep = load_episode(ep_files[0])

    snap = ep["snapshots"][0]
    true_obs0 = ep["true_obs"][0] if ep["true_obs"] is not None else None
    try:
        breakdown = get_observation_breakdown(params)
        viz = build_sensory_viz(np.asarray(ep["obs"][0]), _snap_shim(snap), params, true_obs0)
    except AttributeError as exc:
        # An archived recording's pickled EnvParams predates a field the CURRENT frozen
        # sensor.py reads unconditionally. The plan's answer is `_recording_flag`
        # (section D4.1), which is Phase 1 code; the frozen file may not be edited to
        # work around it. Report rather than crash, so the rest of the matrix still runs.
        print(f"\n=== {name} — BLOCKED at current code")
        print(f"  recordings dir         {rec_dir}")
        print(f"  episodes               {[p.name for p in ep_files]}")
        print(f"  snapshot keys          {sorted(snap)}")
        print(f"  true_obs is None       {ep['true_obs'] is None}")
        print(f"  get_observation_breakdown / build_sensory_viz raise: "
              f"{type(exc).__name__}: {exc}")
        print(f"  => V1 cannot render this recording, so it has no frame baseline. "
              f"Needs _recording_flag (plan section D4.1, Phase 1).")
        return {"blocked": f"{type(exc).__name__}: {exc}"}
    rows, unresolved = _noise_mapping(params, breakdown)

    print(f"\n=== {name} — {extras.get('cell_description', '(real trained-policy recording)')}")
    print(f"  config_path            {extras.get('config_path', '(saved run_meta only)')}")
    print(f"  config_sha256          {extras.get('config_sha256', '(n/a)')}")
    print(f"  config_chain_sha256    {extras.get('config_chain_sha256', '(n/a)')}")
    print(f"  synthetic              {extras.get('synthetic', False)}")
    print(f"  overrides              {extras.get('overrides', {})}")
    if extras.get("overrides_source"):
        print(f"  overrides_source       {extras['overrides_source']}")
    if extras.get("provenance"):
        print(f"  provenance             {extras['provenance']}")
    print(f"  episodes               {[p.name for p in ep_files]}")
    print(f"  snapshot keys          {sorted(snap)}")
    print(f"  true_obs is None       {ep['true_obs'] is None}")
    print(f"  observation breakdown  {breakdown}  (total {sum(breakdown.values())})")
    print(f"  breakdown<->noise      {rows}")
    if unresolved:
        print(f"  UNRESOLVED mapping     {unresolved}  (no perceptual-noise entry)")
    print(f"  build_sensory_viz      {[(v['name'], v['type']) for v in viz]}")
    bt = [v for v in viz if v["name"] == "Body Temperature"]
    print(f"  Body Temperature       in breakdown={'Body Temperature' in breakdown}"
          f"{', viz keys=' + str(sorted(bt[0])) if bt else ''}")
    print(f"  thermal_field present  {'thermal_field' in snap}")
    print(f"  diamond-offset fn      src/environment/sensor.py::{get_visual_offsets.__name__}")

    result = {"breakdown": breakdown, "true_obs_none": ep["true_obs"] is None,
              "snapshot_keys": sorted(snap), "unresolved": unresolved,
              "viz": [(v["name"], v["type"]) for v in viz]}

    if ep["true_obs"] is not None:
        diff = float(np.max(np.abs(np.asarray(ep["obs"]) - np.asarray(ep["true_obs"]))))
        print(f"  max |obs - true_obs|   {diff:.6g}")
        result["max_obs_true_gap"] = diff

    if render_step0:
        frame = _render_v1_step0(ep, params, meta["icon_config"])
        frame_dir.mkdir(parents=True, exist_ok=True)
        _save_png(frame, frame_dir / f"{name}_step0.png")
        print(f"  V1 render step 0       OK {frame.shape} -> {frame_dir / (name + '_step0.png')}")
        result["frame_shape"] = tuple(frame.shape)
    return result


class _Snap:
    pass


def _snap_shim(snap):
    """Attribute view over a snapshot dict — the same shim render_recordings.py builds."""
    s = _Snap()
    for k, v in snap.items():
        setattr(s, k, v)
    return s


def _render_v1_step0(ep, params, icon_config):
    """Render step 0 with the FROZEN V1 renderer, read-only (CP0.2)."""
    import matplotlib
    matplotlib.use("Agg")
    import numpy as np
    from src.environment.renderer import render_jax_state, thermal_color_limits
    from src.environment.sensor import build_sensory_viz

    snap = ep["snapshots"][0]
    s = _snap_shim(snap)
    true0 = ep["true_obs"][0] if ep["true_obs"] is not None else None
    sensory = build_sensory_viz(np.asarray(ep["obs"][0]), s, params, true0)
    clim = thermal_color_limits(snap.get("thermal_field"), params)
    return render_jax_state(
        s, params, episode=ep["episode_index"], step=0, train_episode=100,
        action=None, sensory_data=sensory, info=None, icon_config=icon_config,
        thermal_clim=clim,
    )


def _save_png(frame, path: Path):
    import imageio
    imageio.imwrite(str(path), frame)


# --------------------------------------------------------------------------- CLI


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--cells", nargs="+", default=CP02_CELLS,
                    help=f"cells to generate (default: the CP0.2 set {CP02_CELLS}). "
                         f"Known: {sorted(CELLS)}")
    ap.add_argument("--episodes", type=int, default=2)
    ap.add_argument("--max-steps", type=int, default=120)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--no-true-obs", action="store_true",
                    help="record true_obs=None for every selected cell")
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--report-only", action="store_true",
                    help="skip generation; print the CP0.2 report from what is on disk")
    ap.add_argument("--no-report", action="store_true")
    ap.add_argument("--report-cells", nargs="+", default=None,
                    help="cells to report on (default: the generated cells, plus M7)")
    args = ap.parse_args(argv)

    unknown = [c for c in args.cells if c not in CELLS]
    if unknown:
        raise SystemExit(f"unknown cell(s) {unknown}; known: {sorted(CELLS)}")

    out_root = Path(args.out)
    if not out_root.is_absolute():
        out_root = REPO_ROOT / out_root

    if not args.report_only:
        print(f"Generating {len(args.cells)} cell(s) -> {out_root}")
        for name in args.cells:
            cell = CELLS[name]
            if args.no_true_obs:
                cell = dataclasses.replace(cell, no_true_obs=True)
            generate_cell(name, cell, out_root, args.episodes, args.max_steps, args.seed)

    if not args.no_report:
        report_cells = args.report_cells if args.report_cells is not None else list(args.cells)
        frame_dir = out_root.parent / "step0_frames"
        print("\n" + "=" * 78)
        print("CP0.2 report — read back from the recordings on disk")
        print("=" * 78)
        for name in report_cells:
            try:
                report_cell(name, out_root, render_step0=True, frame_dir=frame_dir)
            except FileNotFoundError as exc:
                print(f"\n=== {name}: NOT AVAILABLE ({exc})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
