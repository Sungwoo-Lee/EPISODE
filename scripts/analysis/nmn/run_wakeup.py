"""Driver: B2 "when does the modulator wake up?" over the runs of a wake-up manifest.

Plain-language purpose: for each modulated run, find the checkpoint where each measure of the
modulator's activity has covered half of its change, and the checkpoint where the agent's
survival has levelled off, then compare the two (tooling plan Stage 4). This file is the
skeleton of that driver. What it does today:

- loads the manifest, checks the pinned rules file's sha256 (rules_pin.load), refuses to run
  on an uncommitted rules file (the `b2_wakeup` status allows verdict words), and checks the
  manifest's `wakeup:` block equals the rules' `parameters.B2` exactly;
- builds ONE x grid per run from the manifest's `checkpoints` list and checks it is the run's
  complete checkpoint list (every saved checkpoint of a non-continual run; for a continual run
  every checkpoint up to `stage_end:0`, whose successor must carry a different saved stage,
  plan T8). A manifest carrying any per-measure point set raises;
- `--measures plateau` (CPU, local WandB logs only): survival binned per checkpoint interval
  with the registered row weighting, then the registered signed crossing with `plateau_f`,
  per run; writes the Checkpoint 4.0 table. It names no wake-up verdict.

Every GPU measure (grad_share, grad_probe, update_size, rho, swing, freeze) refuses to start
unless a plateau table exists for the same manifest and rules sha256 with no NaN plateau, and
is otherwise not implemented yet: it waits for code review and the designer's sign-off of the
fixture table (Checkpoint R.2).

Usage (CPU):
  /home/vncuser/miniconda3/envs/grid_world_pain/bin/python scripts/analysis/nmn/run_wakeup.py \\
      --manifest docs/experiments/active/modulator_clues/algorithmic_null_wakeup.yaml \\
      --measures plateau --out-root results/analysis/algorithmic_null

Plan: docs/develop/active/neuromodulation/ALGORITHMIC_NULL_ANALYSIS_TOOLING.md, File Changes §11,
§B2, Checkpoint 4.0.
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
ANCHORABLE = {"plateau": False, "grad_share": False, "grad_probe": True, "update_size": True,
              "rho": True, "swing": True, "freeze": True}
TOP_KEYS = {"name", "evidence_status", "decision_rules", "wakeup", "runs"}
# developer-owned Stage 4 keys (plan §8); any other top-level key is refused, so a
# per-measure point set cannot hide in the manifest
OPTIONAL_KEYS = {"out_root", "rollout_episodes", "rollout_seed_base", "warmup_iters"}
RUN_KEYS = {"label", "path", "checkpoints"}
SURVIVAL_KEY = "Episode/Steps"


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
    return man


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


def plateau_row(run: dict, grid: dict, B2: dict, surv: dict) -> dict:
    """Survival binned per checkpoint interval, then t_cross with plateau_f (rules B2.plateau:
    'the same signed rule, guard and sustain applied to survival ... m0 for survival is its
    first binned point')."""
    from scripts.analysis.nmn import wakeup, wandb_history as wh
    tag = wh.run_tag(_abs(run["path"]))
    wdir = wh.resolve_by_tag(tag)
    scanned = wh.scan(wdir, allow_truncated=False)
    rows = wh.episode_rows(scanned, grid["stage_index"])
    start = wh.start_counter(rows)
    x = grid_x(run, ANCHORABLE["plateau"])
    edges = np.concatenate([[start], x])
    m, info = wh.interval_means(rows, SURVIVAL_KEY, edges, surv["row_weight"],
                                surv["min_window_n"])
    assert_curve_grid(run, "plateau", x)
    r = wakeup.t_cross(x, m, mode=B2["threshold_mode_headline"], f=B2["plateau_f"],
                       sustain=B2["sustain"], final_k=B2["final_k"], noise_k=B2["noise_k"],
                       min_noise_points=B2["min_noise_points"],
                       noise_window_divisor=B2["noise_window_divisor"],
                       noise_window_max_fraction=B2["noise_window_max_fraction"],
                       anchored=False)
    return {"label": run["label"], "tag": tag, "wandb_dir": os.path.relpath(wdir, _ROOT),
            "n_points": len(x), "window_points": r.window_points,
            "t_plateau_checkpoint": (r.index + 1) if r.index is not None else None,
            "t_plateau_episode": r.t, "direction": r.direction, "m0": r.m0,
            "m_final": r.m_final, "sigma_delta": r.sigma_delta, "guard_margin": r.guard_margin,
            "nan_reason": r.reason, "start_counter": start, "binning": info,
            "curve": [float(v) for v in m], "grid": grid}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--measures", nargs="+", required=True, choices=MEASURES)
    ap.add_argument("--out-root", default=None,
                    help="required when the manifest has no out_root; must equal it otherwise")
    args = ap.parse_args(argv)
    if set(args.measures) == {"plateau"}:
        os.environ["JAX_PLATFORMS"] = "cpu"          # plateau reads logs; orbax stage reads on CPU

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
    if man.get("out_root") is None and args.out_root is None:
        raise ValueError("no output location: the manifest has no out_root; pass --out-root")
    if man.get("out_root") is not None and args.out_root is not None \
            and _abs(man["out_root"]) != _abs(args.out_root):
        raise ValueError("--out-root differs from the manifest's out_root")
    out = _abs(man.get("out_root") or args.out_root) / man["name"]
    out.mkdir(parents=True, exist_ok=True)
    stamp = {"decision_rules": {"file": pinned.path, "sha256": pinned.sha256,
                                "commit": pinned.commit},
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
        raise NotImplementedError(f"{gpu}: not implemented in this stage (waits for code review "
                                  f"and Checkpoint R.2)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
