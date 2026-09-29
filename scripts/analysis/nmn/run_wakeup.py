"""Driver: B2 "when does the modulator wake up?" over the runs of a wake-up manifest.

Plain-language purpose: for each modulated run, find the checkpoint where each measure of the
modulator's activity has covered half of its change, and the checkpoint where the agent's
survival has levelled off, then compare the two, and ask across the 16 level-05 worlds whether
the modulator systematically wakes up late, early, or neither (tooling plan Stage 4).

What it does:
- loads the manifest, checks the pinned rules file's sha256 (rules_pin.load), takes the
  evidence status's policy from the rules (rules_pin.evidence_policy), refuses to run on an
  uncommitted rules file whenever that status allows verdict words (`b2_wakeup` does;
  rules_pin.require_clean), stamps every output with rules_pin.stamp, and checks the
  manifest's `wakeup:` block equals the rules' `parameters.B2` exactly;
- builds ONE x grid per run from the manifest's `checkpoints` list and checks it is the run's
  complete checkpoint list (every saved checkpoint of a non-continual run; for a continual run
  every checkpoint up to `stage_end:0`, whose successor must carry a different saved stage,
  plan T8). Every measure is sampled on that grid (plus step 0, the untrained network, for the
  anchorable ones) and every curve is asserted to use it. A manifest carrying any per-measure
  point set raises;
- `--measures plateau` (CPU, local WandB logs only): survival binned per checkpoint interval
  with the registered row weighting, then the registered signed crossing with `plateau_f`,
  per run; writes the Checkpoint 4.0 table. The plateau checkpoint is a POSITION on the run's
  one scale (`wakeup.position`: the i-th entry of `checkpoints` = i, 1-based; step 0 = 0), the
  scale every lag is read on. A WandB binary still being written may end in a half-written
  record; the run is then accepted only if a later stage has logged rows;
- the GPU sweep (`--measures grad_probe update_size rho swing freeze`, optionally `--runs`
  for one worker per GPU): at every grid point, the gradient probe (grad_probe.py: the
  trainer's own update step for the run's K_epochs updates on a throw-away copy; the
  full-iteration mean beside the first-update per-term split), the relative update size, the
  contextual fraction rho (mod_distribution.variance_split on a greedy rollout), the gain
  swing (spectral_bound, weights only) and the freeze cost (freeze.py: gain and offset frozen
  separately, paired episodes; freeze equivalence verified at every point). One JSON per
  point under points/<label>/, resumable. Refuses to start unless the plateau table exists
  for the same manifest and rules sha256 with no NaN plateau. Needs JAX_PLATFORMS=cuda,cpu;
- `--timing K` (Checkpoint 4.5): one run, step 0 plus K checkpoints spread over its grid;
  seconds per item and the projected wall-clock of the full sweep. Writes timing/ only;
- `--summarise` (CPU): the total-loss gradient share from the logs, every curve, the headline
  crossing (the rules' threshold_mode_headline, with B2.f) and the literal one beside it (with
  B2.literal_f), the lag against the plateau (B2.lag_coincident_max_intervals, on grid
  positions), the Checkpoint 4.2 sanity band, and per headline measure
  decision_rules.evaluate_B2: the sign test across the 16 level-05 worlds, with the three May
  seeds reported only as agree / do not agree. The headline set is the manifest's registered
  `b2_headline_curves` (raises if the computed set differs in names or count, or if a run's
  FiLM sites differ from the registered ones). Per-run wake points are written as numbers only,
  each with the registered caveat (PER_RUN_CAVEAT) and no late / early / coincident word.
  Writes curves/, b2_reading.json and .csv.
- the GPU sweep and --timing log whether JAX's persistent compile cache is active
  (JAX_COMPILATION_CACHE_DIR, set by the launcher) and stamp it into their outputs.

Usage:
  JAX_PLATFORMS=cpu  python scripts/analysis/nmn/run_wakeup.py --manifest M --measures plateau
  JAX_PLATFORMS=cuda,cpu python scripts/analysis/nmn/run_wakeup.py --manifest M \\
      --measures grad_probe update_size rho swing freeze --runs <label> [<label> ...]
  python scripts/analysis/nmn/run_wakeup.py --manifest M \\
      --measures grad_share grad_probe update_size rho swing freeze --summarise
  (M = docs/experiments/active/modulator_clues/algorithmic_null_wakeup.yaml)

Outputs go to <manifest out_root>/<manifest name>/ (out_root is a required manifest key).

Plan: docs/develop/active/neuromodulation/ALGORITHMIC_NULL_ANALYSIS_TOOLING.md, File Changes §11,
§B2, Checkpoints 4.0-4.5.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "scripts", "eval", "traj_collect"))

import numpy as np   # noqa: E402
import yaml          # noqa: E402

MEASURES = ("plateau", "grad_share", "grad_probe", "update_size", "rho", "swing", "freeze")
GPU_MEASURES = tuple(m for m in MEASURES if m != "plateau")
# anchorable at step 0 (the untrained network), plan §B2 table
# update_size is a quantity of an INTERVAL: its first value is untrained -> first checkpoint
# (that is what the plan's "anchorable: yes" buys it), so its curve has one point per
# checkpoint and its m0 is that first interval, not a step-0 value.
ANCHORABLE = {"plateau": False, "grad_share": False, "grad_probe": True, "update_size": False,
              "rho": True, "swing": True, "freeze": True}
MOD_GN, LOSS_GN = "modulator/grad_norm", "loss/grad_norm"
# Checkpoint 4.2 sanity band (plan text: "the 5th-95th percentile of logged values in a
# +-1-checkpoint window"); a tool check that decides no reading
SANITY_Q = (0.05, 0.95)
TOP_KEYS = {"name", "evidence_status", "decision_rules", "wakeup", "runs", "out_root"}
# developer-owned Stage 4 keys (plan §8); any other top-level key is refused, so a
# per-measure point set cannot hide in the manifest
OPTIONAL_KEYS = {"rollout_episodes", "rollout_seed_base", "warmup_iters",
                 # the designer's registered B2 headline family (commit 322a5966); required by
                 # --summarise, which raises if the headline set it computes differs from it
                 "b2_headline_curves"}
RUN_KEYS = {"label", "path", "checkpoints"}
SURVIVAL_KEY = "Episode/Steps"
# The consequence registered with `b2_headline_curves` (wake-up manifest, commit 322a5966): the
# per-curve false-pass rate of the registered guard, with the noise SD estimated from the curve's
# own end, is far above the original target. Written in words next to every per-run wake point.
PER_RUN_CAVEAT = (
    "Descriptive only. No single run's wake point counts as evidence that a measure changed: "
    "the registered guard (noise_k = 3, noise SD estimated from the curve's own end) passes a "
    "curve that does not change about 0.26 % of the time on a level-05 curve (51 / 50 points) "
    "and 1.8 % on a May curve (16 / 15 points), well above the original target, so about 1-4 "
    "false wake points are expected across the 323 headline curves from noise alone. Only the "
    "across-worlds sign test over the 16 level-05 worlds carries a reading; the three May seeds "
    "stay descriptive. Registered with b2_headline_curves in the wake-up manifest.")


def _np(o):
    """json default: numpy scalars and arrays to Python values."""
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(f"not JSON serialisable: {type(o)}")


def _req(d: dict, key: str, where: str = "manifest"):
    if key not in d:
        raise ValueError(f"{where}: mandatory key {key!r} is missing")
    return d[key]


def _abs(p) -> Path:
    p = Path(p)
    return p if p.is_absolute() else Path(_ROOT) / p


def _git(*args) -> str:
    try:
        return subprocess.run(["git", "-C", _ROOT, *args], capture_output=True, text=True,
                              timeout=60).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def load_manifest(path) -> dict:
    man = yaml.safe_load(Path(path).read_text())
    for k in TOP_KEYS:
        _req(man, k)
    extra = set(man) - TOP_KEYS - OPTIONAL_KEYS
    if extra:
        raise ValueError(f"manifest: unknown top-level keys {sorted(extra)}. There is no "
                         f"per-measure point set (plan Revision 3, T1): every measure uses each "
                         f"run's `checkpoints`.")
    for r in man["runs"]:
        for k in RUN_KEYS:
            _req(r, k, f"manifest.runs[{r.get('label')}]")
        if set(r) - RUN_KEYS:
            raise ValueError(f"manifest.runs[{r['label']}]: unknown keys {sorted(set(r) - RUN_KEYS)} "
                             f"(no per-measure point set is allowed)")
        cks = r["checkpoints"]
        if not cks or not all(isinstance(c, int) and not isinstance(c, bool) for c in cks):
            raise ValueError(f"run {r['label']}: checkpoints must be a list of saved steps (<int>)")
        if any(b <= a for a, b in zip(cks, cks[1:])):
            raise ValueError(f"run {r['label']}: checkpoints must be strictly increasing")
    if "b2_headline_curves" in man:
        hc = man["b2_headline_curves"]
        if not isinstance(hc, list) or not hc or \
                not all(isinstance(n, str) and n for n in hc) or len(set(hc)) != len(hc):
            raise ValueError("manifest.b2_headline_curves must be a non-empty list of distinct "
                             "curve names")
    return man


def registered_sites(registered: list) -> list:
    """The FiLM sites the registered headline set names: the <site> of its `rho.<site>` and
    `swing.<site>` curves, which must name the same sites."""
    rho = sorted(n.split(".", 1)[1] for n in registered if n.startswith("rho."))
    swing = sorted(n.split(".", 1)[1] for n in registered if n.startswith("swing."))
    if rho != swing or not rho:
        raise ValueError(f"b2_headline_curves: rho sites {rho} and swing sites {swing} must be "
                         f"the same non-empty set")
    return rho


def check_sites(label: str, sites, registered: list) -> None:
    """A run's enabled FiLM sites must be exactly the sites the registered headline set lists."""
    want = registered_sites(registered)
    if sorted(sites) != want or len(sites) != len(set(sites)):
        raise ValueError(f"run {label}: enabled FiLM sites {sorted(sites)} differ from the "
                         f"{len(want)} registered in b2_headline_curves {want}")


def check_headline_set(label: str, curves: dict, registered: list) -> None:
    """The headline curves the code computes must equal the registered family exactly: same
    names, same count (sites are part of the names)."""
    got = sorted(n for n, c in curves.items() if c["headline"])
    want = sorted(registered)
    if got != want:
        raise ValueError(f"run {label}: computed headline set ({len(got)} curves) differs from "
                         f"b2_headline_curves ({len(want)}): missing from the registration "
                         f"{sorted(set(got) - set(want))}, registered but not computed "
                         f"{sorted(set(want) - set(got))}")


def per_run_wake_point(r: dict) -> dict:
    """One run's wake point as written out: the crossings and the lag in NUMBERS (episodes and
    checkpoint positions) with the registered caveat beside them. The lag's late / early /
    coincident word is not written for a single run; it feeds only the across-worlds sign test."""
    return {"headline_mode": r["headline_mode"], "headline": r["headline"],
            "beside_mode": r["beside_mode"], "beside": r["beside"],
            "lag": {k: v for k, v in r["lag"].items() if k != "reading"},
            "caveat": PER_RUN_CAVEAT}


def compile_cache_status() -> dict:
    """Whether JAX's persistent compile cache is active in this process (set by the launcher's
    JAX_COMPILATION_CACHE_DIR; performance only, identical programs and numbers)."""
    import jax
    d = jax.config.jax_compilation_cache_dir
    st = {"active": bool(d), "dir": d or None,
          "min_entry_size_bytes": jax.config.jax_persistent_cache_min_entry_size_bytes,
          "min_compile_time_secs": jax.config.jax_persistent_cache_min_compile_time_secs}
    if d:
        st["entries_at_start"] = len(os.listdir(d)) if os.path.isdir(d) else 0
    return st


def check_wakeup_block(man: dict, settings: dict) -> None:
    """The manifest's `wakeup:` values must equal parameters.B2, key for key."""
    wk = man["wakeup"]
    if set(wk) != set(settings):
        raise ValueError(f"manifest wakeup keys {sorted(wk)} != rules parameters.B2 keys "
                         f"{sorted(settings)}")
    bad = {k: (wk[k], settings[k]) for k in settings if wk[k] != settings[k]}
    if bad:
        raise ValueError(f"manifest wakeup values differ from the rules' parameters.B2: {bad}")


def check_grid(run: dict) -> dict:
    """The run's checkpoint grid is complete (no thinning): every saved checkpoint of a
    non-continual run; for a continual run every checkpoint up to stage_end:0, whose
    successor carries a different saved stage (plan T8, via the one selector implementation
    `collect_trajectories.resolve_checkpoint_info`)."""
    import collect_trajectories as ct
    run_dir = _abs(run["path"])
    steps = ct._checkpoint_steps(run_dir / "models")
    listed = list(run["checkpoints"])
    info = {"continual": bool(ct.is_continual(run_dir)), "saved_checkpoints": len(steps)}
    if info["continual"]:
        end = ct.resolve_checkpoint_info(run_dir, "stage_end:0")
        want = [s for s in steps if s <= end["step"]]
        info.update({"stage_end_0": end["step"], "successor": end["successor"],
                     "successor_stage": end["successor_stage"], "stage_index": 0})
    else:
        want = steps
        info["stage_index"] = None
    if listed != want:
        missing = sorted(set(want) - set(listed))
        extra = sorted(set(listed) - set(want))
        raise ValueError(f"run {run['label']}: listed checkpoints are not the run's complete "
                         f"grid (missing {missing[:5]}{'...' if len(missing) > 5 else ''}, "
                         f"not saved / past the stage {extra[:5]})")
    return info


def grid_x(run: dict, anchorable: bool) -> np.ndarray:
    """The one x grid of a run: its checkpoints, with step 0 first when the measure is
    anchorable (the untrained network)."""
    x = [float(c) for c in run["checkpoints"]]
    return np.asarray(([0.0] if anchorable else []) + x)


def assert_curve_grid(run: dict, measure: str, x) -> None:
    if not np.array_equal(np.asarray(x, float), grid_x(run, ANCHORABLE[measure])):
        raise AssertionError(f"run {run['label']}, {measure}: curve grid differs from the "
                             f"manifest's checkpoint grid")


def plateau_crossing(label: str, rows: list, x, B2: dict, surv: dict):
    """The pure half of the plateau (rules B2.plateau: 'the same signed rule, guard and sustain
    applied to survival ... m0 for survival is its first binned point'): survival binned per
    checkpoint interval from the rows' own start counter with the registered row weighting,
    then t_cross with plateau_f. Returns (Result, binned curve, binning info)."""
    from scripts.analysis.nmn import wakeup, wandb_history as wh
    start = wh.start_counter(rows)
    edges = np.concatenate([[start], np.asarray(x, float)])
    m, info = wh.interval_means(rows, SURVIVAL_KEY, edges, surv["row_weight"],
                                surv["min_window_n"])
    r = wakeup.t_cross(x, m, mode=B2["threshold_mode_headline"], f=B2["plateau_f"],
                       sustain=B2["sustain"], final_k=B2["final_k"], noise_k=B2["noise_k"],
                       min_noise_points=B2["min_noise_points"],
                       noise_window_divisor=B2["noise_window_divisor"],
                       noise_window_max_fraction=B2["noise_window_max_fraction"],
                       anchored=ANCHORABLE["plateau"], label=f"{label} / plateau")
    return r, m, {**info, "start_counter": start}


def read_scanned(label: str, wdir, stage_index) -> dict:
    """The run's WandB rows. A half-written trailing record (a run still training) is accepted
    only when the stage read is `stage_index` of a continual run and a LATER stage has logged
    rows, which establishes that the stage is complete; otherwise it raises."""
    from scripts.analysis.nmn import wandb_history as wh
    scanned = wh.scan(wdir, allow_truncated=True)
    if scanned["truncated"]:
        later = stage_index is not None and any(
            wh.STAGE in r and int(r[wh.STAGE]) > stage_index for r in scanned["rows"])
        if not later:
            raise RuntimeError(f"run {label}: {scanned['file']} ends in an unreadable record "
                               f"({scanned['truncated']}) and no later stage establishes that the "
                               f"stage read is complete")
    return scanned


def plateau_row(run: dict, grid: dict, B2: dict, surv: dict) -> dict:
    """Survival plateau of one run (Checkpoint 4.0 table row)."""
    from scripts.analysis.nmn import wakeup, wandb_history as wh
    tag = wh.run_tag(_abs(run["path"]))
    wdir = wh.resolve_by_tag(tag)
    scanned = read_scanned(run["label"], wdir, grid["stage_index"])
    rows = wh.episode_rows(scanned, grid["stage_index"])
    x = grid_x(run, ANCHORABLE["plateau"])
    assert_curve_grid(run, "plateau", x)
    r, m, info = plateau_crossing(run["label"], rows, x, B2, surv)
    pos = wakeup.position(r.t, run["checkpoints"]) if r.index is not None else None
    if pos is not None and pos != r.index + 1:      # unanchored: array index 0 = checkpoint 1
        raise AssertionError(f"run {run['label']}: position {pos} != index + 1 = {r.index + 1}")
    return {"label": run["label"], "tag": tag, "wandb_dir": os.path.relpath(wdir, _ROOT),
            "wandb_truncated": scanned["truncated"],
            "n_points": len(x), "window_points": r.window_points,
            "t_plateau_checkpoint": pos,
            "t_plateau_episode": r.t, "direction": r.direction, "m0": r.m0,
            "m_final": r.m_final, "sigma_delta": r.sigma_delta, "guard_margin": r.guard_margin,
            "nan_reason": r.reason, "start_counter": info.pop("start_counter"), "binning": info,
            "curve": [float(v) for v in m], "grid": grid}


# =========================================================================== GPU measures ===
# The B2 curves, per run. HEADLINE curves are the rules' measure families (rules B2 question;
# `noise_k` principle: "per-site rho and swing, per-term shares, gain/offset freeze", plus the
# total-loss share and the relative update size of the plan's §B2 table): each gets the
# crossing, the lag and the across-worlds reading. Every other number computed at a point is
# kept as a DESCRIPTIVE value in the point files and curves (no crossing, no reading), so a
# crossing on it can be computed later without the GPU.
#   grad_share.total                  (modulator/grad_norm / loss/grad_norm)^2 per logged row,
#                                     mean within each checkpoint interval (logs; unanchored)
#   grad_probe.first_update.<term>    ||grad_mod||^2 / ||grad_all||^2 of one loss term at the
#                                     first update of a probe iteration (grad_probe (a))
#   update_size.modulator             ||theta_mod(x_i) - theta_mod(x_{i-1})|| / ||theta_mod(x_{i-1})||
#   rho.<site>                        contextual fraction of the GAIN at the site (greedy rollout)
#   swing.<site>                      mean reachable swing of the GAIN at the site (weights only;
#                                     spectral_bound `gamma_swing_mean`)
#   freeze.gain / freeze.offset       mean paired change in survival steps when the gain (offset)
#                                     is frozen at its per-unit time-mean (frozen - live)

def _clone_agent(agent):
    import dataclasses
    from flax import nnx
    return dataclasses.replace(agent, model=nnx.clone(agent.model))


def _flat(params: dict, prefix: str = "") -> dict:
    out = {}
    for k in sorted(params):
        v = params[k]
        out.update(_flat(v, f"{prefix}/{k}") if isinstance(v, dict) else
                   {f"{prefix}/{k}": np.asarray(v)})
    return out


def model_params(model) -> dict:
    """Nested {name: numpy} of a live model's nnx.Param leaves, the layout ckpt_io.load_params
    returns (checked equal at each run's first checkpoint)."""
    from flax import nnx
    import jax
    return jax.tree_util.tree_map(np.asarray, nnx.state(model, nnx.Param).to_pure_dict())


def split_norms(params: dict) -> dict:
    """Flattened modulator and main-network parameter vectors (float64)."""
    f = _flat(params)
    mod = [f[k].ravel() for k in f if k.startswith("/modulator/")]
    main = [f[k].ravel() for k in f if not k.startswith("/modulator/")]
    if not mod or not main:
        raise ValueError("update size needs both a modulator and a main network")
    return {"mod": np.concatenate(mod).astype(np.float64),
            "main": np.concatenate(main).astype(np.float64)}


def update_size(prev: dict, cur: dict) -> dict:
    """Relative change of the modulator's and the main network's parameters between two
    consecutive grid points (prev -> cur)."""
    a, b = split_norms(prev), split_norms(cur)
    out = {}
    for part in ("mod", "main"):
        if a[part].shape != b[part].shape:
            raise ValueError(f"{part}: parameter vector length changed between points")
        out[f"{part}_delta_norm"] = float(np.linalg.norm(b[part] - a[part]))
        out[f"{part}_prev_norm"] = float(np.linalg.norm(a[part]))
        out[f"{part}_rel"] = out[f"{part}_delta_norm"] / out[f"{part}_prev_norm"]
    out["mod_over_main"] = out["mod_rel"] / out["main_rel"] if out["main_rel"] > 0 else math.nan
    return out


class RunContext:
    """Everything one run's sweep needs, loaded once: its saved config, the untrained network,
    the manifest's rollout settings."""

    def __init__(self, run: dict, grid: dict, man: dict):
        from src.environment.config_loader import Config
        self.run, self.grid = run, grid
        self.run_dir = _abs(run["path"])
        self.models = self.run_dir / "models"
        self.cfg = Config.load_yaml(str(self.models / "config.yaml"))
        self.agent_cfg = self.cfg.to_dict()["agent"]
        self.num_envs = int(self.cfg.get_mandatory("training.num_envs"))
        self.episodes = int(_req(man, "rollout_episodes"))
        self.seed_base = int(_req(man, "rollout_seed_base"))
        self.warmup_iters = int(_req(man, "warmup_iters"))
        self._untrained = None

    def agent(self, step: int):
        """The LoadedAgent at `step`; step 0 is the untrained network (untrained.build)."""
        from scripts.analysis.nmn import replay, untrained
        if step != 0:
            return replay.load_agent(self.models, step)
        if self._untrained is None:
            from src.environment.sensor import get_observation_breakdown
            model, env_params = untrained.build(self.run_dir)
            bd = get_observation_breakdown(env_params)
            self._untrained = replay.LoadedAgent(
                model=model, env_params=env_params, agent_cfg=self.agent_cfg, step=0,
                obs_breakdown=bd,
                action_dim=4 + int(env_params.rest_action_enabled) + int(env_params.eat_action_enabled),
                env_config_path=str(self.models / "config.yaml"))
        return _clone_agent(self._untrained)

    def params(self, step: int, agent=None) -> dict:
        from scripts.analysis.nmn import ckpt_io
        if step == 0:
            return model_params((agent or self.agent(0)).model)
        return ckpt_io.load_params(self.models, step)


def measure_rollout(ctx: RunContext, agent, want: set) -> dict:
    """rho (every enabled site, gain and offset) and the freeze cost (gain and offset frozen
    separately), from one greedy live rollout plus one rollout per frozen signal, all on the
    manifest's fixed paired episode seeds. Freeze equivalence (Checkpoint 4.3) is verified at
    every point, and every frozen signal is checked bit-constant in its own replay."""
    from scripts.analysis.nmn import freeze, mod_distribution, replay
    seeds = replay.episode_seeds(ctx.episodes, ctx.seed_base)
    live = replay.rollout(agent, seeds)
    out = {"live_survival_mean": float(live["lengths"].mean()), "n_episodes": len(seeds)}
    if not live["gamma"]:
        raise ValueError(f"{ctx.run['label']}: no enabled modulation site in the rollout")
    if "rho" in want:
        out["rho"] = {s: {"gamma": mod_distribution.variance_split(live["gamma"][s], live["valid"]),
                          "beta": mod_distribution.variance_split(live["beta"][s], live["valid"])}
                      for s in sorted(live["gamma"])}
    if "freeze" in want:
        means = freeze.per_unit_time_means(live)
        eq = freeze.verify_freeze_equivalence(lambda: _clone_agent(agent), means, sorted(means))
        out["freeze_equivalence"] = {"exact": eq["exact"], "worst_deviation": eq["worst_deviation"]}
        for cond, fg, fo in (("gain", True, False), ("offset", False, True)):
            fa = _clone_agent(agent)
            freeze.apply_freeze(fa.model, means, freeze_gain=fg, freeze_offset=fo)
            fr = replay.rollout(fa, seeds)
            v = fr["valid"]
            for site in fr["gamma"]:
                arr, what = (fr["gamma"][site], "gamma") if fg else (fr["beta"][site], "beta")
                if float(np.ptp(arr[v], axis=0).max()) != 0.0 or \
                        float(np.abs(arr[v] - means[site][what][None, :]).max()) != 0.0:
                    raise AssertionError(f"{ctx.run['label']} step {agent.step}: frozen {what} at "
                                         f"{site} is not constant at its mean in the replay")
            out[f"freeze_{cond}"] = freeze.paired_differences(live["lengths"], fr["lengths"])
    return out


def measure_swing(ctx: RunContext, params: dict) -> dict:
    from scripts.analysis.nmn import spectral_bound
    rows = spectral_bound.checkpoint_bounds(params, ctx.agent_cfg)
    keep = ("gamma_swing_mean", "gamma_swing_max", "beta_swing_mean", "beta_swing_max")
    return {r["site"]: {k: float(r[k]) for k in keep} for r in rows}


def measure_grad_probe(ctx: RunContext, agent) -> dict:
    from scripts.analysis.nmn import grad_probe as gp
    config = gp.ppo_config(ctx.cfg)
    opt = gp.make_optimizer(agent.model, config)
    restored = None
    if agent.step != 0:
        restored = gp.restore_optimizer(ctx.models, agent.step, agent.model, opt, ctx.num_envs)
        if int(restored["episode"]) != int(agent.step):
            raise AssertionError(f"checkpoint {agent.step} records episode {restored['episode']}")
    out = gp.probe(agent.model, opt, agent.env_params, config, num_envs=ctx.num_envs,
                   seed=ctx.seed_base, warmup_iters=ctx.warmup_iters)
    out["optimizer"] = "fresh (as train.py builds it at step 0)" if agent.step == 0 else \
        f"restored from the checkpoint (iteration {restored['iteration']})"
    return out


def point_path(out: Path, label: str, x: int) -> Path:
    return out / "points" / label / f"{int(x)}.json"


def sweep_run(ctx: RunContext, want: set, out: Path, stamp: dict, points=None,
              write_points: bool = True) -> list:
    """Compute every wanted GPU measure at every point of the run's grid (or at `points`, the
    timing mode's subset, which never writes point files). Resumable: a point file already
    holding a measure (for the same rules sha256 and settings) is not recomputed.
    Returns [(x, seconds per measure, measures)]."""
    label, cks = ctx.run["label"], list(ctx.run["checkpoints"])
    grid = [0] + cks
    todo = grid if points is None else list(points)
    settings = {"rollout_episodes": ctx.episodes, "rollout_seed_base": ctx.seed_base,
                "warmup_iters": ctx.warmup_iters}
    timings, prev_params = [], None
    for x in todo:
        pf = point_path(out, label, x)
        rec = json.loads(pf.read_text()) if (write_points and pf.exists()) else {}
        if rec and (rec.get("rules_sha256") != stamp["sha256"] or rec.get("settings") != settings):
            raise ValueError(f"{pf}: computed under other rules or settings; move it away first")
        need = {m for m in want if m not in rec.get("measures", {})}
        if "update_size" in need and x == 0:
            need.discard("update_size")            # no interval ends at step 0
        t_point = {}
        if need:
            t0 = time.time()
            agent = ctx.agent(x)
            t_point["load"] = time.time() - t0
            meas = dict(rec.get("measures", {}))
            if need & {"swing", "update_size"}:
                t0 = time.time()
                params = ctx.params(x, agent)
                if x == cks[0] and x != 0:
                    ref, got = _flat(params), _flat(model_params(agent.model))
                    if set(ref) != set(got) or any(not np.array_equal(ref[k], got[k]) for k in ref):
                        raise AssertionError(f"{label}: ckpt_io and the restored model disagree")
                if "swing" in need:
                    meas["swing"] = measure_swing(ctx, params)
                if "update_size" in need:
                    i = grid.index(x)
                    if prev_params is None or prev_params[0] != grid[i - 1]:
                        prev = grid[i - 1]
                        prev_params = (prev, ctx.params(prev))
                    meas["update_size"] = {**update_size(prev_params[1], params),
                                           "interval": [grid[i - 1], x]}
                prev_params = (x, params)
                t_point["weights"] = time.time() - t0
            if need & {"rho", "freeze"}:
                t0 = time.time()
                r = measure_rollout(ctx, agent, need & {"rho", "freeze"})
                for m in ("rho", "freeze"):
                    if m in need:
                        meas[m] = {k: v for k, v in r.items()
                                   if k in (("rho",) if m == "rho" else
                                            ("freeze_gain", "freeze_offset", "freeze_equivalence"))
                                   or k in ("live_survival_mean", "n_episodes")}
                t_point["rollouts"] = time.time() - t0
            if "grad_probe" in need:
                t0 = time.time()
                meas["grad_probe"] = measure_grad_probe(ctx, agent)
                t_point["grad_probe"] = time.time() - t0
            rec = {"label": label, "x": int(x), "rules_sha256": stamp["sha256"],
                   "settings": settings, "measures": meas,
                   "seconds": {**rec.get("seconds", {}), **t_point},
                   "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
            if write_points:
                pf.parent.mkdir(parents=True, exist_ok=True)
                tmpf = pf.with_suffix(".json.tmp")
                tmpf.write_text(json.dumps(rec, default=_np))
                os.replace(tmpf, pf)
        timings.append((int(x), t_point, rec.get("measures", {})))
        print(f"  point {label} x={x}: " + ", ".join(f"{k} {v:.1f}s" for k, v in t_point.items()),
              flush=True)
    return timings


# ---------------------------------------------------------------------------- assembly -----
def _curve_values(label: str, pts: dict, xs: list, fn) -> list:
    vals = []
    for x in xs:
        if x not in pts:
            raise ValueError(f"{label}: point x={x} missing (sweep incomplete)")
        vals.append(float(fn(pts[x]["measures"])))
    return vals


def run_curves(run: dict, pts: dict, sites: list, log_share: tuple) -> dict:
    """{curve name: {x, m, anchored, headline}} for one run, from its point files and the
    total-loss share from the logs. Every curve's x is asserted to be the run's one grid."""
    cks = [int(c) for c in run["checkpoints"]]
    anch = [0] + cks
    curves = {}

    def add(name, measure, xs, fn, headline):
        m = _curve_values(run["label"], pts, xs, fn)
        assert_curve_grid(run, measure, xs)
        curves[name] = {"x": [float(v) for v in xs], "m": m, "measure": measure,
                        "anchored": ANCHORABLE[measure], "headline": headline}

    x_share, m_share = log_share
    assert_curve_grid(run, "grad_share", x_share)
    curves["grad_share.total"] = {"x": [float(v) for v in x_share], "m": list(m_share),
                                  "measure": "grad_share", "anchored": False, "headline": True}
    for t in ("policy", "value", "entropy", "total"):
        add(f"grad_probe.first_update.{t}", "grad_probe", anch,
            lambda M, t=t: M["grad_probe"]["first_update"][t]["share"], t != "total")
    add("grad_probe.full_iteration", "grad_probe", anch,
        lambda M: M["grad_probe"]["full_iteration"]["share"], False)
    for name, k, head in (("modulator", "mod_rel", True), ("main", "main_rel", False),
                          ("mod_over_main", "mod_over_main", False)):
        add(f"update_size.{name}", "update_size", cks, lambda M, k=k: M["update_size"][k], head)
    for s in sites:
        add(f"rho.{s}", "rho", anch, lambda M, s=s: M["rho"]["rho"][s]["gamma"]["rho"], True)
        add(f"rho.{s}.beta", "rho", anch, lambda M, s=s: M["rho"]["rho"][s]["beta"]["rho"], False)
        add(f"swing.{s}", "swing", anch, lambda M, s=s: M["swing"][s]["gamma_swing_mean"], True)
        add(f"swing.{s}.beta", "swing", anch, lambda M, s=s: M["swing"][s]["beta_swing_mean"], False)
    for c in ("gain", "offset"):
        add(f"freeze.{c}", "freeze", anch,
            lambda M, c=c: M["freeze"][f"freeze_{c}"]["mean_diff"], True)
    add("freeze.live_survival", "freeze", anch, lambda M: M["freeze"]["live_survival_mean"], False)
    return curves


def grad_share_curve(run: dict, scanned: dict, stage_index) -> tuple:
    """Total-loss gradient share from the run's own log: per logged row
    (modulator/grad_norm / loss/grad_norm)^2, averaged (unweighted: rows are evenly spaced in
    iterations) within each checkpoint interval (x_{i-1}, x_i], x_0 = the episode rows' start
    counter. Rows are placed at an episode count by wandb_history's join, never by arithmetic.
    Returns (x, m, info, (episodes, logged mod_grad_norm)) — the last for the sanity band."""
    from scripts.analysis.nmn import wandb_history as wh
    series, info = wh.read_keys(scanned, [MOD_GN, LOSS_GN])
    (e1, v1), (e2, v2) = series[MOD_GN], series[LOSS_GN]
    if not np.array_equal(e1, e2):
        raise ValueError(f"{run['label']}: {MOD_GN} and {LOSS_GN} are not logged on the same rows")
    rows = wh.episode_rows(scanned, stage_index)
    x = grid_x(run, False)
    edges = np.concatenate([[wh.start_counter(rows)], x])
    ratio = (v1 / v2) ** 2
    m, counts = [], []
    for lo, hi in zip(edges[:-1], edges[1:]):
        sel = (e1 > lo) & (e1 <= hi)
        counts.append(int(sel.sum()))
        m.append(float(ratio[sel].mean()) if sel.any() else math.nan)
    return x, m, {**info, "rows_per_interval": counts}, (e1, v1)


def sanity_band(run: dict, pts: dict, logged: tuple, q_lo: float, q_hi: float) -> dict:
    """Checkpoint 4.2: the probe's (b) full-iteration mean of mod_grad_norm against the logged
    modulator/grad_norm values in a +-1-checkpoint window around each checkpoint. A sanity
    band, not a correctness proof."""
    cks = [int(c) for c in run["checkpoints"]]
    e, v = logged
    rows = []
    for i, c in enumerate(cks):
        lo = cks[i - 1] if i > 0 else 0
        hi = cks[i + 1] if i + 1 < len(cks) else cks[i]
        w = v[(e > lo) & (e <= hi)]
        b = pts[c]["measures"]["grad_probe"]["full_iteration"]["mod_grad_norm_mean"]
        a = math.sqrt(pts[c]["measures"]["grad_probe"]["first_update"]["total"]["mod_sq"])
        if w.size:
            ql, qh = (float(np.quantile(w, q)) for q in (q_lo, q_hi))
            rows.append({"x": c, "probe_b": b, "probe_a_first_update": a, "logged_n": int(w.size),
                         "q_lo": ql, "q_hi": qh, "inside": bool(ql <= b <= qh)})
        else:
            rows.append({"x": c, "probe_b": b, "probe_a_first_update": a, "logged_n": 0,
                         "inside": None})
    return {"rows": rows, "n_inside": sum(r["inside"] is True for r in rows),
            "n_checked": sum(r["inside"] is not None for r in rows)}


def measure_reading(label: str, curve: dict, checkpoints, t_plateau: float, B2: dict) -> dict:
    """The registered B2 reading of ONE curve: the headline crossing (the rules'
    `threshold_mode_headline`), the other mode beside it, and the lag against the run's
    plateau (positions on the run's one checkpoint scale). Uses B2.f for fraction_of_rise,
    B2.literal_f for fraction_of_final and B2.lag_coincident_max_intervals for the lag."""
    from scripts.analysis.nmn import wakeup
    kw = dict(sustain=B2["sustain"], final_k=B2["final_k"], noise_k=B2["noise_k"],
              min_noise_points=B2["min_noise_points"],
              noise_window_divisor=B2["noise_window_divisor"],
              noise_window_max_fraction=B2["noise_window_max_fraction"],
              anchored=curve["anchored"])
    res = {"fraction_of_rise": wakeup.t_cross(curve["x"], curve["m"], mode="fraction_of_rise",
                                              f=B2["f"], label=f"{label} / rise", **kw),
           "fraction_of_final": wakeup.t_cross(curve["x"], curve["m"], mode="fraction_of_final",
                                               f=B2["literal_f"], label=f"{label} / final", **kw)}
    head = B2["threshold_mode_headline"]
    if head not in res:
        raise ValueError(f"threshold_mode_headline {head!r} is not a mode")
    beside = [k for k in res if k != head][0]
    lg = wakeup.lag(res[head].t, t_plateau, checkpoints, B2["lag_coincident_max_intervals"])
    return {"headline_mode": head, "headline": res[head].as_dict(),
            "beside_mode": beside, "beside": res[beside].as_dict(), "lag": lg}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--measures", nargs="+", required=True, choices=MEASURES)
    ap.add_argument("--runs", nargs="+", default=None,
                    help="GPU sweep: only these manifest labels (one worker per GPU); the "
                         "summary always needs every run")
    ap.add_argument("--timing", type=int, default=None, metavar="K",
                    help="timing gate (Checkpoint 4.5): ONE run (--runs), step 0 plus K "
                         "checkpoints spread over the grid; writes timing only, never a curve")
    ap.add_argument("--summarise", action="store_true",
                    help="assemble curves, crossings, lags and the across-worlds reading from "
                         "the point files (CPU); needs all six GPU measures on every run")
    args = ap.parse_args(argv)
    if set(args.measures) == {"plateau"} or args.summarise:
        os.environ["JAX_PLATFORMS"] = "cpu"          # logs + point files; orbax stage reads on CPU
    elif "cpu" not in os.environ.get("JAX_PLATFORMS", "cpu").split(","):
        raise ValueError("GPU measures read each continual run's saved stage on the CPU backend "
                         "(the T8 grid check): run with JAX_PLATFORMS=cuda,cpu")

    from scripts.analysis.nmn import decision_rules as dr

    man_path = _abs(args.manifest)
    man = load_manifest(man_path)
    pinned = dr.load(man)
    policy = dr.verdict_policy(pinned, man["evidence_status"])
    dr.enforce_order(pinned, policy)
    P = pinned.parameters
    B2 = dr.b2_settings(P)
    check_wakeup_block(man, B2)
    surv = dr.survival_settings(P)
    out = _abs(man["out_root"]) / man["name"]
    out.mkdir(parents=True, exist_ok=True)
    from scripts.analysis.nmn import rules_pin
    rstamp = rules_pin.stamp(pinned)
    stamp = {"decision_rules": rstamp,
             "evidence_status": policy.status, "label": policy.label,
             "manifest": os.path.relpath(man_path, _ROOT), "git_sha": _git("rev-parse", "HEAD"),
             "git_dirty": bool(_git("status", "--porcelain", "--", "scripts/analysis/nmn")),
             "python": platform.python_version()}
    print(f"[run_wakeup] {man['name']}: {policy.status} — {policy.label}; rules {pinned.path} "
          f"{pinned.sha256[:12]} @ {(pinned.commit or 'uncommitted')[:8]}", flush=True)

    grids = {}
    for r in man["runs"]:
        grids[r["label"]] = check_grid(r)
        print(f"  grid ok  {r['label']}: {len(r['checkpoints'])} checkpoints"
              + (f" (stage_end:0 = {grids[r['label']]['stage_end_0']}, successor stage "
                 f"{grids[r['label']]['successor_stage']})" if grids[r['label']]['continual'] else ""),
              flush=True)

    if "plateau" in args.measures:
        t0 = time.time()
        rows = []
        for r in man["runs"]:
            row = plateau_row(r, grids[r["label"]], B2, surv)
            rows.append(row)
            print(f"  plateau  {row['label']:24s} ckpt {row['t_plateau_checkpoint']}  "
                  f"ep {row['t_plateau_episode']}  margin {row['guard_margin']:.1f}  "
                  f"reason {row['nan_reason']}", flush=True)
        nan_runs = [r["label"] for r in rows if not math.isfinite(r["t_plateau_episode"])]
        doc = {**stamp, "measure": "plateau",
               "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
               "settings": {"plateau_f": B2["plateau_f"], "sustain": B2["sustain"],
                            "final_k": B2["final_k"], "noise_k": B2["noise_k"],
                            "min_noise_points": B2["min_noise_points"],
                            "noise_window_divisor": B2["noise_window_divisor"],
                            "noise_window_max_fraction": B2["noise_window_max_fraction"],
                            "mode": B2["threshold_mode_headline"],
                            "row_weight": surv["row_weight"],
                            "min_window_n": surv["min_window_n"]},
               "statement": "survival plateau per run (Checkpoint 4.0); no wake-up reading",
               "checkpoint_numbering": "t_plateau_checkpoint is 1-based: the i-th entry of the "
                                       "run's manifest `checkpoints` list is checkpoint i (step 0, "
                                       "the untrained anchor, would be 0). Every lag compares "
                                       "positions on this one scale (wakeup.position).",
               "wandb_truncated_runs": [r["label"] for r in rows if r["wandb_truncated"]],
               "nan_plateau_runs": nan_runs, "runs": rows,
               "elapsed_s": round(time.time() - t0, 1)}
        (out / "plateau.json").write_text(json.dumps(doc, indent=1))
        with open(out / "plateau.csv", "w", newline="") as f:
            w = csv.writer(f)
            cols = ["label", "n_points", "t_plateau_checkpoint", "t_plateau_episode", "m0",
                    "m_final", "sigma_delta", "guard_margin", "nan_reason"]
            w.writerow(cols)
            for r in rows:
                w.writerow([r[c] for c in cols])
        print(f"[run_wakeup] wrote {out / 'plateau.json'}; NaN plateaus: {nan_runs or 'none'}")
        if nan_runs:
            print("[run_wakeup] STOP: a NaN plateau blocks every GPU measure (Checkpoint 4.0).")
            return 2

    gpu = [m for m in args.measures if m in GPU_MEASURES]
    if gpu:
        pf = out / "plateau.json"
        if not pf.exists():
            raise ValueError("GPU measures need the plateau table first (--measures plateau)")
        prev = json.loads(pf.read_text())
        if prev["decision_rules"]["sha256"] != pinned.sha256 or \
                prev["manifest"] != os.path.relpath(man_path, _ROOT):
            raise ValueError("plateau table was computed for another manifest or rules file")
        if prev["nan_plateau_runs"]:
            raise ValueError(f"NaN plateau in {prev['nan_plateau_runs']}: GPU measures refused")
        labels = [r["label"] for r in man["runs"]]
        sel = labels if args.runs is None else args.runs
        unknown = sorted(set(sel) - set(labels))
        if unknown:
            raise ValueError(f"--runs {unknown}: not in the manifest")
        sweep_measures = {m for m in gpu if m != "grad_share"}   # grad_share reads logs only
        if args.summarise:
            return summarise(man, man_path, out, stamp, rstamp, prev, grids, B2, pinned, policy, dr)
        if args.timing is not None:
            if len(sel) != 1 or args.timing < 1:
                raise ValueError("--timing needs exactly one run (--runs) and K >= 1")
            return timing(man, sel[0], grids, out, rstamp, stamp, sweep_measures, args.timing)
        import jax
        stamp["device"] = str(jax.devices()[0].device_kind)
        stamp["compile_cache"] = compile_cache_status()
        print(f"[run_wakeup] persistent compile cache: {stamp['compile_cache']}", flush=True)
        print(f"[run_wakeup] sweep {sorted(sweep_measures)} on {stamp['device']} for {sel}",
              flush=True)
        for r in man["runs"]:
            if r["label"] not in sel:
                continue
            t0 = time.time()
            ctx = RunContext(r, grids[r["label"]], man)
            sweep_run(ctx, sweep_measures, out, rstamp)
            (out / "points" / r["label"] / "_done.json").write_text(json.dumps(
                {**stamp, "measures": sorted(sweep_measures), "elapsed_s": round(time.time() - t0, 1),
                 "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}))
            print(f"[run_wakeup] {r['label']} done in {time.time() - t0:.0f}s", flush=True)
    return 0


def timing(man, label, grids, out, rstamp, stamp, want, k) -> int:
    """Checkpoint 4.5: seconds per item on step 0 plus K checkpoints spread over one run's grid,
    extrapolated to the full every-checkpoint sweep of every run. Writes timing/<label>.json
    only; the timed points are never written as point files, so they cannot become a curve."""
    import jax
    stamp = {**stamp, "compile_cache": compile_cache_status()}
    print(f"[run_wakeup] persistent compile cache: {stamp['compile_cache']}", flush=True)
    run = [r for r in man["runs"] if r["label"] == label][0]
    cks = list(run["checkpoints"])
    idx = sorted({round(i * (len(cks) - 1) / max(k - 1, 1)) for i in range(k)})
    points = [0] + [cks[i] for i in idx]
    t0 = time.time()
    ctx = RunContext(run, grids[label], man)
    tm = sweep_run(ctx, want, out, rstamp, points=points, write_points=False)
    wall = time.time() - t0
    per = [sum(t.values()) for _, t, _ in tm]
    steady = float(np.mean(per[1:])) if len(per) > 1 else float(per[0])
    first_extra = max(per[0] - steady, 0.0)
    n_points = sum(len(r["checkpoints"]) + 1 for r in man["runs"])
    total = n_points * steady + len(man["runs"]) * first_extra
    doc = {**stamp, "device": str(jax.devices()[0].device_kind), "run": label,
           "points_timed": points, "measures": sorted(want),
           "seconds_per_point": [{"x": x, **t} for x, t, _ in tm],
           "values_not_a_curve": {str(x): m for x, _, m in tm},
           "steady_seconds_per_point": steady, "first_point_extra_seconds": first_extra,
           "wall_seconds": wall, "n_points_full_sweep": n_points,
           "projected_gpu_hours_total": total / 3600,
           "projected_wall_hours": {str(w): total / 3600 / w for w in (1, 2, 4)},
           "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "note": "compile cost is counted once per run (first point minus the steady mean); "
                   "grad_share reads logs only and is not timed"}
    (out / "timing").mkdir(parents=True, exist_ok=True)
    (out / "timing" / f"{label}.json").write_text(json.dumps(doc, indent=1, default=_np))
    print(f"[run_wakeup] timing {label}: steady {steady:.1f}s/point, first +{first_extra:.1f}s; "
          f"{n_points} points -> {total / 3600:.2f} GPU-h; wall on 2 GPUs "
          f"{total / 3600 / 2:.2f} h, on 4 GPUs {total / 3600 / 4:.2f} h", flush=True)
    return 0


def run_sites(run: dict) -> list:
    """The FiLM sites a run's saved agent config switches on."""
    from src.environment.config_loader import Config
    from scripts.analysis.nmn.spectral_bound import enabled_sites
    return enabled_sites(Config.load_yaml(str(_abs(run["path"]) / "models" / "config.yaml"))
                         .to_dict()["agent"])


def summarise(man, man_path, out, stamp, rstamp, plateau, grids, B2, pinned, policy, dr) -> int:
    """Curves, crossings, lags and the across-worlds reading (CPU), from the point files and
    the logs. Needs every GPU measure at every point of every run."""
    from scripts.analysis.nmn import wandb_history as wh
    need = {"grad_probe", "update_size", "rho", "swing", "freeze"}
    registered = list(_req(man, "b2_headline_curves"))
    sites = {r["label"]: run_sites(r) for r in man["runs"]}
    for r in man["runs"]:                      # every run's sites, before anything is written
        check_sites(r["label"], sites[r["label"]], registered)
    plat = {r["label"]: r for r in plateau["runs"]}
    per_run, readings = {}, {}
    for r in man["runs"]:
        label, cks = r["label"], [int(c) for c in r["checkpoints"]]
        pts = {}
        for x in [0] + cks:
            pf = point_path(out, label, x)
            if not pf.exists():
                raise ValueError(f"{label}: point file {pf} missing; the sweep is incomplete")
            rec = json.loads(pf.read_text())
            if rec["rules_sha256"] != rstamp["sha256"]:
                raise ValueError(f"{pf}: computed under another rules file")
            miss = need - set(rec["measures"]) - ({"update_size"} if x == 0 else set())
            if miss:
                raise ValueError(f"{pf}: missing measures {sorted(miss)}")
            pts[x] = rec
        if plat[label]["n_points"] != len(cks):
            raise ValueError(f"{label}: plateau table grid has {plat[label]['n_points']} points, "
                             f"the manifest {len(cks)}")
        scanned = read_scanned(label, wh.resolve_by_tag(wh.run_tag(_abs(r["path"]))),
                               grids[label]["stage_index"])
        xs, ms, sh_info, logged = grad_share_curve(r, scanned, grids[label]["stage_index"])
        curves = run_curves(r, pts, sites[label], (xs, ms))
        check_headline_set(label, curves, registered)
        t_pl = float(plat[label]["t_plateau_episode"])
        rd = {name: measure_reading(f"{label} / {name}", c, cks, t_pl, B2)
              for name, c in curves.items() if c["headline"]}
        band = sanity_band(r, pts, logged, SANITY_Q[0], SANITY_Q[1])
        eq = [pts[x]["measures"]["freeze"]["freeze_equivalence"]["exact"] for x in pts]
        per_run[label] = {"continual": grids[label]["continual"], "curves": curves,
                          "grad_share_info": sh_info, "sanity_band": band,
                          "freeze_equivalence_exact_points": int(sum(eq)), "points": len(eq)}
        readings[label] = rd
        (out / "curves").mkdir(parents=True, exist_ok=True)
        (out / "curves" / f"{label}.json").write_text(json.dumps(
            {**stamp, "label": label, "t_plateau_episode": t_pl, **per_run[label],
             "per_run_caveat": PER_RUN_CAVEAT,
             "wake_points": {n: per_run_wake_point(v) for n, v in rd.items()}},
            indent=1, default=_np))
    names = sorted({n for rd in readings.values() for n in rd})
    b2 = {}
    for n in names:
        l05 = [readings[l][n]["lag"]["reading"] for l in readings
               if n in readings[l] and not per_run[l]["continual"]]
        may = [readings[l][n]["lag"]["reading"] for l in readings
               if n in readings[l] and per_run[l]["continual"]]
        b2[n] = {**dr.evaluate_B2(l05, may, pinned.parameters, policy=policy),
                 "may_status": "descriptive (the May seeds carry no reading of their own)"}
    doc = {**stamp, "measure": "b2_reading",
           "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "statement": "B2 wake-up reading per measure: level-05 worlds by the sign test; the May "
                        "seeds reported only as agree / do not agree (descriptive). Per-run wake "
                        "points below are numbers only, each with the registered caveat.",
           "headline_curves": registered,
           "per_run_caveat": PER_RUN_CAVEAT,
           "reading": b2,
           "sanity_band": {l: {"n_inside": per_run[l]["sanity_band"]["n_inside"],
                               "n_checked": per_run[l]["sanity_band"]["n_checked"]}
                           for l in per_run},
           "per_run_wake_points": {l: {n: per_run_wake_point(readings[l][n]) for n in readings[l]}
                                   for l in readings}}
    (out / "b2_reading.json").write_text(json.dumps(doc, indent=1, default=_np))
    with open(out / "b2_reading.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["measure", "reading", "n_def", "k_star", "n_late", "n_early", "may"])
        for n in names:
            b = b2[n]
            w.writerow([n, b["reading"], b["n_def"], b["k_star"], b["n_late"], b["n_early"], b["may"]])
    print(f"[run_wakeup] wrote {out / 'b2_reading.json'}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
