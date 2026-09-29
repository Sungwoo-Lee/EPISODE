"""Driver: build a manifest's probe sets and capture every listed agent's layers on them.

Plain-language purpose: this is Stage 2 of the "What Both Agents Compute" tooling. For each
probe in an analysis manifest it samples stored episodes (probe_set), and for each run and
checkpoint it replays those episodes through the agent (teacher_forced), keeping the layer
activity at the probe's sampled rows. It enforces the tool checks (self-replay agreement,
alignment controls, chain assertions) and writes, per (run, checkpoint, probe), an
activations file and a JSON report. It computes no similarity and no verdict.

Every number it enforces comes from the pinned rules file (gates G1, G2, G3, G6 and the split
fraction) or from the manifest's `tool_checks`; none is typed here. Every output carries the
rules' wording for the manifest's evidence status; for a status whose rules forbid verdict
words (the pilot) it also says "no verdict is drawn".

Usage:
  /home/vncuser/miniconda3/envs/grid_world_pain/bin/python scripts/analysis/nmn/run_activations.py \
      --manifest docs/experiments/active/modulator_clues/algorithmic_null_pilot.yaml --batch-size 1000

Plan: docs/develop/active/neuromodulation/ALGORITHMIC_NULL_ANALYSIS_TOOLING.md, File Changes §4, §8.
"""
from __future__ import annotations

import argparse
import hashlib
import json
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

NO_VERDICT = "no verdict is drawn"
# jax.default_matmul_precision names. "default" is TF32 on an Ampere/Ada GPU and full float32
# on a Turing GPU or the CPU; "highest" is full float32 everywhere (teacher_forced.replay).
PRECISIONS = ("highest", "default")
FLATTEN = {"enc.uni.raw": "senses_x_units", "enc.uni.mod": "senses_x_units",
           "enc.uni.out": "senses_x_units"}


def _req(d: dict, key: str, where: str = "manifest"):
    if key not in d:
        raise ValueError(f"{where}: mandatory key {key!r} is missing")
    return d[key]


def _abs(p) -> Path:
    p = Path(p)
    return p if p.is_absolute() else Path(_ROOT) / p


def load_manifest(path) -> dict:
    """The keys this driver reads; every one mandatory (no defaults)."""
    man = yaml.safe_load(Path(path).read_text())
    for k in ("name", "evidence_status", "out_root", "decision_rules", "runs", "probes",
              "layers", "assert_n_episodes", "tool_checks", "capture_matmul_precision"):
        _req(man, k)
    if man["capture_matmul_precision"] not in PRECISIONS:
        raise ValueError(f"capture_matmul_precision must be one of {PRECISIONS}")
    _req(man["tool_checks"], "shift_change_rows_max", "manifest.tool_checks")
    for p in man["probes"]:
        for k in ("id", "stores", "n_per_store", "rows_per_episode", "seed",
                  "store_matmul_precision"):
            _req(p, k, f"manifest.probes[{p.get('id')}]")
        if not p["stores"]:
            raise ValueError(f"probe {p['id']}: no stores listed")
        if (len(p["store_matmul_precision"]) != len(p["stores"])
                or any(x not in PRECISIONS for x in p["store_matmul_precision"])):
            raise ValueError(f"probe {p['id']}: store_matmul_precision must list one of "
                             f"{PRECISIONS} per store, in the order of `stores`")
    for r in man["runs"]:
        for k in ("label", "path", "checkpoints"):
            _req(r, k, f"manifest.runs[{r.get('label')}]")
    for layer in man["layers"]:
        key, fl = _req(layer, "key", "manifest.layers"), _req(layer, "flatten", "manifest.layers")
        want = FLATTEN.get(key, "none")
        if fl != want:
            raise ValueError(f"layer {key}: flatten must be {want!r}, got {fl!r}")
    return man


def _git(*args) -> str:
    try:
        return subprocess.run(["git", "-C", _ROOT, *args], capture_output=True, text=True,
                              timeout=60).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--batch-size", type=int, required=True,
                    help="episodes per replay batch (memory only; every batch pads to max_steps)")
    ap.add_argument("--probes-only", action="store_true", help="build/verify probes, no replay")
    ap.add_argument("--rebuild-probes", action="store_true")
    args = ap.parse_args(argv)

    from scripts.analysis.nmn import probe_set, rules_pin, teacher_forced
    from scripts.analysis.nmn.replay import load_agent
    import collect_trajectories as ct

    man_path = _abs(args.manifest)
    man = load_manifest(man_path)
    pinned = rules_pin.load(man)
    status = man["evidence_status"]
    policy = rules_pin.evidence_policy(pinned, status)
    if policy["verdict_words_allowed"] and pinned.dirty:
        raise ValueError(f"evidence status {status!r} allows verdict words, so the rules file "
                         f"must be committed with no local changes ({pinned.path} is dirty).")
    P = pinned.parameters
    g1 = {k: float(rules_pin.param(P, f"gates.G1.{k}"))
          for k in ("action_agreement_min", "near_tie_logit_margin", "near_tie_fraction_max")}
    g3 = {k: float(rules_pin.param(P, f"gates.G3.{k}"))
          for k in ("alignment_agreement_min", "shift_control_agreement_max")}
    g2_tol = float(rules_pin.param(P, "gates.G2.reconstruction_rel_tol"))
    test_frac = float(rules_pin.param(P, "common.split.test_frac"))
    min_test_groups = int(rules_pin.param(P, "gates.G6.test_fold_groups_min"))

    label = policy.get("label") or policy.get("verdict_prefix") or ""
    statement = {"evidence_status": status, "label": label,
                 "verdict_words_allowed": bool(policy["verdict_words_allowed"]),
                 "verdict_statement": (NO_VERDICT if not policy["verdict_words_allowed"]
                                       else "verdicts only through decision_rules.evaluate_*"),
                 "decision_rules": {"file": pinned.path, "sha256": pinned.sha256,
                                    "commit": pinned.commit}}
    print(f"[run_activations] {man['name']}: {status} — {label}; "
          f"{statement['verdict_statement']}; rules {pinned.path} {pinned.sha256[:12]}", flush=True)

    out = _abs(man["out_root"]) / man["name"]
    (out / "probes").mkdir(parents=True, exist_ok=True)
    layers = [l["key"] for l in man["layers"]]
    run_meta = {"generated_utc": datetime.now(timezone.utc).isoformat(),
                "git_sha": _git("rev-parse", "HEAD"), "git_dirty": bool(_git("status", "--porcelain")),
                "manifest": str(man_path.relative_to(_ROOT)),
                "manifest_sha256": hashlib.sha256(man_path.read_bytes()).hexdigest(),
                "python": platform.python_version(), **statement,
                "gates_read": {"G1": g1, "G2": g2_tol, "G3": g3, "G6_test_fold_groups_min": min_test_groups,
                               "split_test_frac": test_frac},
                "tool_checks": man["tool_checks"], "probes": {}, "captures": []}
    import jax, flax  # noqa: E401
    run_meta["versions"] = {"jax": jax.__version__, "flax": flax.__version__,
                            "numpy": np.__version__, "device": str(jax.devices()[0])}

    probes = {}
    pdefs = {p["id"]: p for p in man["probes"]}
    for pdef in man["probes"]:
        pid = pdef["id"]
        pj = out / "probes" / f"probe_{pid}.json"
        if pj.exists() and not args.rebuild_probes:
            probe = probe_set.load(out / "probes", pid)
            if [str(_abs(s)) for s in pdef["stores"]] != probe.stores:
                raise ValueError(f"probe {pid} on disk was built from other stores; --rebuild-probes")
            print(f"[run_activations] probe {pid}: loaded, {probe.counts['distinct_episode_seed_groups']} "
                  f"distinct episode_seed groups", flush=True)
            if probe.counts["distinct_episode_seed_groups"] * test_frac < min_test_groups:
                raise ValueError(f"probe {pid}: below gate G6's group minimum")
        else:
            t0 = time.time()
            probe = probe_set.build(pid, [str(_abs(s)) for s in pdef["stores"]], pdef["n_per_store"],
                                    pdef["rows_per_episode"], pdef["seed"], test_frac=test_frac,
                                    min_test_groups=min_test_groups)
            probe_set.save(probe, out / "probes")
            print(f"[run_activations] probe {pid}: built in {time.time() - t0:.0f}s", flush=True)
        probes[pid] = probe
        run_meta["probes"][pid] = {"row_index_sha256": probe.row_sha256, "counts": probe.counts,
                                   "npz_bytes": (out / "probes" / f"probe_{pid}.npz").stat().st_size}
    if args.probes_only:
        (out / "manifest.json").write_text(json.dumps(run_meta, indent=1, default=str))
        return 0

    failures = []
    for run in man["runs"]:
        run_dir = _abs(run["path"])
        for sel in run["checkpoints"]:
            info = ct.resolve_checkpoint_info(run_dir, str(sel))
            agent = load_agent(run_dir / "models", info["step"])
            saved = yaml.safe_load((run_dir / "models" / "config.yaml").read_text())
            role = {"seed": saved["seed"], "tag": saved.get("tag"),
                    "modulation_type": (saved["agent"].get("modulation") or {}).get("type")}
            for pid, probe in probes.items():
                bd = dict(sorted(agent.obs_breakdown.items()))
                for sm in probe.store_meta:
                    from src.utils.trajectory_store import read_manifest
                    smb = dict(sorted(read_manifest(sm["store"])["observation_breakdown"].items()))
                    if smb != bd or sm["D"] != sum(bd.values()):
                        raise ValueError(f"{run['label']}: observation breakdown differs from "
                                         f"store {sm['store']}")
                ckpt = str(Path(info["ckpt_dir"]).resolve())
                gen = [i for i, sm in enumerate(probe.store_meta)
                       if str(Path(sm["checkpoint_path"]).resolve()) == ckpt]
                t0 = time.time()
                acts, rep = teacher_forced.replay(
                    agent, probe, layers, batch_size=args.batch_size, is_generating=bool(gen),
                    g1=g1, g3=g3, g2_tol=g2_tol,
                    shift_change_rows_max=float(man["tool_checks"]["shift_change_rows_max"]),
                    assert_n_episodes=int(man["assert_n_episodes"]),
                    store_id_of_agent=(gen[0] if gen else None),
                    capture_precision=man["capture_matmul_precision"],
                    check_precision=(pdefs[pid]["store_matmul_precision"][gen[0]] if gen else None))
                stem = f"acts_{run['label']}__{info['step']}__{pid}"
                nbytes = teacher_forced.save_activations(out / f"{stem}.npz", acts, probe.row_sha256)
                rep.update({"run_label": run["label"], "run_path": str(run["path"]),
                            "selector": str(sel), "checkpoint_step": info["step"],
                            "saved_stage": info["saved_stage"], "role_from_saved_config": role,
                            "env_config_path": agent.env_config_path, "probe": pid,
                            "activations_file": f"{stem}.npz", "activations_bytes": nbytes,
                            "seconds": round(time.time() - t0, 1), **statement,
                            "generated_utc": datetime.now(timezone.utc).isoformat()})
                (out / f"{stem}.json").write_text(json.dumps(rep, indent=1, default=str))
                run_meta["captures"].append({"stem": stem, "failures": rep["failures"]})
                print(f"[run_activations] {stem}: {rep['seconds']}s, {nbytes/1e6:.0f} MB, "
                      f"failures={rep['failures']}", flush=True)
                failures += [f"{stem}: {f}" for f in rep["failures"]]
    (out / "manifest.json").write_text(json.dumps(run_meta, indent=1, default=str))
    if failures:
        raise SystemExit("tool checks failed:\n  " + "\n  ".join(failures))
    return 0


if __name__ == "__main__":
    sys.exit(main())
