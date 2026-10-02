#!/usr/bin/env python
"""Forgetting matrix for ONE continual (multi-stage) rPPO run -- no training.

What it answers: after each stage of a continual run, how well does the frozen agent
still survive in every world of its sequence? Rows are checkpoints (optionally the
pre-trained start, then the stage-end checkpoint of every stage); columns are the
distinct worlds of the run's schedule; each cell is the mean survival steps (episode
length, capped at the world's `environment.max_steps`) over N evaluation episodes with
a 95 % confidence interval. Survival steps only -- reward is never read.

How it works:
  1. Reads the run's OWN saved schedule (`<run>/models/schedule.yaml`, written by
     train.py) -- boundaries + stage names. `--schedule` (the source YAML) is optional
     and only cross-checked against it.
  2. With --start-checkpoint, a stage whose boundary is <= the start checkpoint's step
     (a run branched from a pre-trained checkpoint via --load-checkpoint, e.g. at the end
     of stage 0) gets no row of its own: the 'start' row is its end.
     Stage-end checkpoint of stage k = the first saved checkpoint at or after boundary k
     (saved at the end of the iteration that crossed it, before the world switches).
     Its saved `stage` field is read back and must equal k -- otherwise the run is not
     where we think it is and the script stops.
  3. Worlds = the distinct stage names with the numeric prefix stripped
     (`02_fog`, `04_fog` -> `fog`), in first-visit order. Each world is evaluated with
     the run's saved per-stage config (`stage_XX_<name>.yaml`); every visit of the same
     world must have an identical saved config in every world-defining section (the
     run-identity sections in RUN_IDENTITY_KEYS -- seed, tag, wandb.*, ... which train.py
     stamps onto stage 0 only -- are ignored). The run's seed is read from
     `models/config.yaml`.
  4. Per checkpoint, ONE `scripts/eval/eval_rollout.py --config-list --batched` process
     evaluates every world (model built + checkpoint restored once). Passing the saved
     stage configs explicitly is what bypasses eval_rollout's continual auto-resolution,
     which only fires for the stage-0 `config.yaml`. The same seeds (0..N-1) are used in
     every cell, so cells are paired.
  5. Reads `episodes/*.npz` `length` per cell and writes `<out>.json` + `<out>.csv`.
  6. Optional `--extra-world NAME=PATH` (repeatable) adds columns for worlds OUTSIDE the
     run's schedule, evaluated with the given source YAML (resolved through `extends:`).
     An extra world whose NAME equals one of the run's own worlds is NOT re-evaluated: the
     saved stage config stays authoritative, and the source YAML is only cross-checked
     against it (every key the source defines must equal the saved value) -- so one
     battery of --extra-world flags can be passed to every run of a study.

Re-running with the same --scratch-dir reuses finished cells (a cell is finished when
its eval_rollout metadata.json exists with n_episodes == N and, if --eval-policy-mode is
given, the same eval_policy_mode).

Policy: --eval-policy-mode deterministic (argmax, "greedy") or stochastic (sampled, as in
training) overrides every world config's behavior_measures.eval_policy_mode; omitted, each
saved config's own value is used (deterministic in every current config). The mode used
is recorded per cell (`eval_policy_mode` column).

Usage:
  /home/vncuser/miniconda3/envs/grid_world_pain/bin/python scripts/eval/continual_forgetting_matrix.py \\
      --run-dir results/JAX_RecurrentPPO/<ts>_<tag> \\
      --start-checkpoint results/JAX_RecurrentPPO/<pretrain_run>/models \\
      --episodes 2000 --device gpu \\
      --output-prefix results/analysis/continual_worlds/forgetting_<label> \\
      [--extra-world home=configs/environment/experiment/continual_worlds/home_10x10.yaml ...]
"""
import argparse
import csv
import json
import re
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]  # scripts/eval/<this> -> repo root
PY = "/home/vncuser/miniconda3/envs/grid_world_pain/bin/python"
EVAL_ROLLOUT = REPO_ROOT / "scripts" / "eval" / "eval_rollout.py"
sys.path.insert(0, str(REPO_ROOT))
from src.environment.config_loader import load_env_config  # noqa: E402  (resolves `extends:`)

# Top-level keys that identify the RUN, not the world: train.py stamps the CLI seed / tag /
# wandb.* onto stage 0's saved config only (and merges the agent config into it), so two
# visits of the same world can differ here without being different worlds.
RUN_IDENTITY_KEYS = ("seed", "tag", "wandb", "training", "agent", "logging", "visualization")


def _abs(p):
    p = Path(p)
    return p if p.is_absolute() else REPO_ROOT / p


def list_steps(models_dir):
    return sorted(int(p.name) for p in models_dir.iterdir() if p.name.isdigit())


def read_saved_stage(models_dir, step):
    """The stage index train.py stored in the checkpoint payload (ground truth)."""
    import jax
    import orbax.checkpoint as ocp
    dev = jax.local_devices(backend="cpu")[0]
    target = {"stage": 0}
    rargs = jax.tree_util.tree_map(
        lambda _x: ocp.ArrayRestoreArgs(restore_type=jax.Array,
                                        sharding=jax.sharding.SingleDeviceSharding(dev)),
        target)
    mngr = ocp.CheckpointManager(str(models_dir))
    out = mngr.restore(step, args=ocp.args.PyTreeRestore(item=target, restore_args=rargs,
                                                         partial_restore=True))
    return int(out["stage"])


def resolve_rows(run_dir, start_ckpt):
    models = run_dir / "models"
    sched_path = models / "schedule.yaml"
    if not sched_path.exists():
        raise ValueError(f"{sched_path} not found -- {run_dir} is not a continual run.")
    sched = yaml.safe_load(sched_path.read_text())["continual"]
    bounds = sched["episode_boundaries"]
    names = sched["stage_names"]
    if len(bounds) != len(names):
        raise ValueError(f"{sched_path}: {len(bounds)} boundaries vs {len(names)} stage names.")
    steps = list_steps(models)

    rows = []
    if start_ckpt is not None:
        sp = _abs(start_ckpt)
        if not sp.name.isdigit():
            s = list_steps(sp)
            if not s:
                raise ValueError(f"--start-checkpoint {sp} holds no numeric checkpoint steps.")
            sp = sp / str(s[-1])
        rows.append({"label": "start", "trained_through": "pre-trained start",
                     "checkpoint": str(sp), "step": int(sp.name), "saved_stage": None})
    for k, (b, name) in enumerate(zip(bounds, names)):
        if rows and rows[0]["label"] == "start" and rows[0]["step"] >= b:
            # The run was branched (--load-checkpoint) at or after this boundary: stage k
            # ended before the run started, so its end IS the start checkpoint.
            rows[0].setdefault("also_end_of", []).append(name)
            print(f"stage {k} '{name}' (boundary {b}) ended at/before the start checkpoint "
                  f"(step {rows[0]['step']}); the 'start' row stands for its end.")
            continue
        after = [s for s in steps if s >= b]
        if not after:
            raise ValueError(f"No checkpoint at or after boundary {b} (end of stage {k} "
                             f"'{name}') under {models} -- stage not finished?")
        step = after[0]
        saved = read_saved_stage(models, step)
        if saved != k:
            raise ValueError(f"Stage-end checkpoint {step} for stage {k} ('{name}') has saved "
                             f"stage {saved}, expected {k}.")
        rows.append({"label": f"end_{name}", "trained_through": name,
                     "checkpoint": str(models / str(step)), "step": step, "saved_stage": saved})
    return sched, rows


def resolve_worlds(run_dir, stage_names):
    models = run_dir / "models"
    worlds = {}
    for k, name in enumerate(stage_names):
        world = re.sub(r"^\d+_", "", name)
        cfg = models / f"stage_{k:02d}_{name}.yaml"
        if not cfg.exists():
            raise ValueError(f"Saved stage config {cfg} not found.")
        if world in worlds:
            first = worlds[world]
            a, b = _world_sections(first["config"]), _world_sections(cfg)
            if a != b:
                diff = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
                raise ValueError(f"World '{world}' visited twice with different saved configs: "
                                 f"{first['config']} vs {cfg} differ on {diff[:10]}.")
            first["stages"].append(k)
        else:
            worlds[world] = {"world": world, "config": str(cfg), "stages": [k],
                             "source": "saved_stage_config"}
    return list(worlds.values())


def _flat(d, prefix=""):
    out = {}
    for k, v in d.items():
        if isinstance(v, dict):
            out.update(_flat(v, f"{prefix}{k}."))
        else:
            out[f"{prefix}{k}"] = v
    return out


def _world_sections(path):
    d = yaml.safe_load(Path(path).read_text())
    return _flat({k: v for k, v in d.items() if k not in RUN_IDENTITY_KEYS})


def add_extra_worlds(worlds, specs):
    """Append `--extra-world NAME=PATH` columns; a NAME that is one of the run's own
    worlds is cross-checked against its saved stage config and not added twice."""
    if not specs:
        return worlds
    own = {w["world"]: w for w in worlds}
    seen = set()
    for spec in specs:
        if "=" not in spec:
            raise ValueError(f"--extra-world {spec!r}: expected NAME=PATH.")
        name, path = spec.split("=", 1)
        if name in seen:
            raise ValueError(f"--extra-world {name!r} given twice.")
        seen.add(name)
        path = _abs(path)
        if not path.exists():
            raise ValueError(f"--extra-world {name}: {path} not found.")
        src = _flat(load_env_config(str(path)).to_dict())
        if name in own:
            saved = _flat(load_env_config(own[name]["config"]).to_dict())
            diff = [k for k in src if saved.get(k, "<missing>") != src[k]]
            if diff:
                raise ValueError(f"--extra-world {name}: {path} disagrees with the run's saved "
                                 f"stage config {own[name]['config']} on {diff[:10]}.")
            own[name]["source_yaml_checked"] = str(path)
            print(f"extra world '{name}' is a run world: using saved stage config "
                  f"(source YAML {path} agrees on all {len(src)} keys)")
            continue
        worlds.append({"world": name, "config": str(path), "stages": [], "source": "extra"})
    return worlds


def cell_dir(scratch, row, world):
    return scratch / row["label"] / world["world"]


def find_meta(d):
    metas = sorted(d.glob("**/metadata.json"))
    return metas[0] if len(metas) == 1 else None


def run_checkpoint(row, worlds, scratch, n_eps, device, policy_mode=None):
    pending = []
    for w in worlds:
        m = find_meta(cell_dir(scratch, row, w))
        meta = json.loads(m.read_text()) if m is not None else {}
        if (m is None or meta.get("n_episodes") != n_eps
                or (policy_mode is not None and meta.get("eval_policy_mode") != policy_mode)):
            pending.append(w)
    if not pending:
        print(f"  {row['label']}: all cells already done, reusing", flush=True)
        return 0.0
    cl = scratch / "_config_lists" / f"{row['label']}.tsv"
    cl.parent.mkdir(parents=True, exist_ok=True)
    cl.write_text("".join(f"{w['config']}\t{cell_dir(scratch, row, w)}\n" for w in pending))
    log = scratch / "_logs" / f"{row['label']}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    cmd = [PY, str(EVAL_ROLLOUT), "--config-list", str(cl), "--checkpoint", row["checkpoint"],
           "--eval-n-episodes", str(n_eps), "--eval-seeds", *map(str, range(n_eps)),
           "--batched", "--device", device, "--quiet"]
    if policy_mode is not None:
        cmd += ["--eval-policy-mode", policy_mode]
    t0 = time.time()
    with open(log, "w") as f:
        rc = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, cwd=REPO_ROOT).returncode
    dt = time.time() - t0
    if rc != 0:
        raise RuntimeError(f"eval_rollout failed for {row['label']} (rc={rc}); see {log}")
    print(f"  {row['label']}: {len(pending)} world(s) evaluated in {dt:.0f}s", flush=True)
    return dt


def summarise(d, n_eps):
    meta_path = find_meta(d)
    meta = json.loads(meta_path.read_text())
    ep_dir = meta_path.parent / "episodes"
    files = sorted(ep_dir.glob("*.npz"))
    if len(files) != n_eps:
        raise ValueError(f"{ep_dir}: {len(files)} episode files, expected {n_eps}.")
    lengths = np.array([int(np.load(f)["length"]) for f in files], dtype=np.float64)
    cfg = load_env_config(meta["config_resolved"])  # an --extra-world YAML may use `extends:`
    max_steps = int(cfg.get_mandatory("environment.max_steps"))
    n = len(lengths)
    mean, sd = float(lengths.mean()), float(lengths.std(ddof=1))
    se = sd / np.sqrt(n)
    return {"n": n, "mean": mean, "sd": sd, "se": se,
            "ci95_lo": mean - 1.96 * se, "ci95_hi": mean + 1.96 * se,
            "frac_at_max_steps": float((lengths >= max_steps).mean()), "max_steps": max_steps,
            "eval_policy_mode": meta["eval_policy_mode"], "eval_obs_noise": meta["eval_obs_noise"],
            "rollout_mode": meta["rollout_mode"], "git_commit": meta["git_commit"]}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-dir", required=True, help="Continual rPPO run dir (holds models/).")
    ap.add_argument("--episodes", type=int, required=True, help="Evaluation episodes per cell.")
    ap.add_argument("--output-prefix", required=True, help="Writes <prefix>.json and <prefix>.csv.")
    ap.add_argument("--schedule", default=None,
                    help="Optional source schedule YAML; cross-checked against the run's saved copy.")
    ap.add_argument("--start-checkpoint", default=None,
                    help="Optional pre-trained start (models/ root -> latest step, or a step dir); "
                         "adds a 'start' row.")
    ap.add_argument("--device", required=True, choices=["cpu", "gpu"])
    ap.add_argument("--extra-world", action="append", default=[], metavar="NAME=PATH",
                    help="Repeatable. Also evaluate every checkpoint row in this world (source "
                         "YAML). A NAME equal to a run world keeps the saved stage config.")
    ap.add_argument("--eval-policy-mode", default=None, choices=["deterministic", "stochastic"],
                    help="Override every world config's behavior_measures.eval_policy_mode "
                         "(deterministic = argmax/greedy, stochastic = sampled). Omitted: the "
                         "saved configs' own value.")
    ap.add_argument("--scratch-dir", default=None,
                    help="Per-episode eval output (default <output-prefix>_scratch).")
    args = ap.parse_args()

    run_dir = _abs(args.run_dir)
    out_prefix = _abs(args.output_prefix)
    scratch = _abs(args.scratch_dir) if args.scratch_dir else Path(str(out_prefix) + "_scratch")

    sched, rows = resolve_rows(run_dir, args.start_checkpoint)
    if args.schedule:
        src = yaml.safe_load(_abs(args.schedule).read_text())["continual"]
        for k in ("episode_boundaries", "checkpoint_frequencies"):
            if src[k] != sched[k]:
                raise ValueError(f"--schedule {k} {src[k]} != run's saved {sched[k]}.")
    worlds = add_extra_worlds(resolve_worlds(run_dir, sched["stage_names"]), args.extra_world)

    run_seed = yaml.safe_load((run_dir / "models" / "config.yaml").read_text())["seed"]
    print(f"run: {run_dir}  (seed {run_seed})")
    print(f"worlds: {[w['world'] for w in worlds]}")
    for r in rows:
        print(f"row {r['label']}: step {r['step']} (saved stage {r['saved_stage']})")

    t_all = time.time()
    wall = {}
    for r in rows:
        wall[r["label"]] = run_checkpoint(r, worlds, scratch, args.episodes, args.device,
                                         args.eval_policy_mode)

    cells = []
    for r in rows:
        for w in worlds:
            c = summarise(cell_dir(scratch, r, w), args.episodes)
            cells.append({"row": r["label"], "trained_through": r["trained_through"],
                          "checkpoint_step": r["step"], "world": w["world"], **c})

    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    result = {
        "what": "Forgetting matrix: mean survival steps of the frozen agent (no training) per "
                "(checkpoint row x world). Survival = episode length, capped at max_steps.",
        "run_dir": str(run_dir.relative_to(REPO_ROOT)) if REPO_ROOT in run_dir.parents else str(run_dir),
        "run_seed": run_seed,
        "schedule": sched, "episodes_per_cell": args.episodes,
        "seeds": f"0..{args.episodes - 1} (identical in every cell)",
        "eval_policy_mode_requested": args.eval_policy_mode,
        "rows": rows, "worlds": worlds, "cells": cells,
        "eval_wall_clock_s_per_row": wall, "total_wall_clock_s": time.time() - t_all,
        "scratch_dir": str(scratch),
    }
    Path(str(out_prefix) + ".json").write_text(json.dumps(result, indent=2))
    cols = ["row", "trained_through", "checkpoint_step", "world", "n", "mean", "sd", "se",
            "ci95_lo", "ci95_hi", "frac_at_max_steps", "max_steps", "eval_policy_mode",
            "eval_obs_noise", "rollout_mode", "git_commit"]
    with open(str(out_prefix) + ".csv", "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=cols)
        wr.writeheader()
        for c in cells:
            wr.writerow({k: (f"{c[k]:.3f}" if isinstance(c[k], float) else c[k]) for k in cols})

    print("\nmean survival steps (95% CI half-width)")
    print(f"{'row':<22}" + "".join(f"{w['world']:>18}" for w in worlds))
    for r in rows:
        line = f"{r['label']:<22}"
        for w in worlds:
            c = next(x for x in cells if x["row"] == r["label"] and x["world"] == w["world"])
            line += f"{c['mean']:>10.1f} ±{1.96 * c['se']:>5.1f}"
        print(line)
    print(f"\nwrote {out_prefix}.json / .csv  (total {time.time() - t_all:.0f}s)")


if __name__ == "__main__":
    main()
