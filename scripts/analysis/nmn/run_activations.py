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
# Revision 4 (R4-1): every kept activation is computed in full float32, so the capture mode
# accepts only "highest". A store's check mode is `recorded` (read from the store manifest's
# `matmul_precision`, written by the collector since 2026-09-30) or, only for an older store
# that records no mode, an explicit PRECISIONS name.
CAPTURE_PRECISIONS = ("highest",)
STORE_PRECISION_ENTRIES = ("recorded",) + PRECISIONS


def resolve_store_precision(entry: str, recorded, store: str) -> str:
    """The matmul mode to self-replay `store` in, from its manifest entry.

    `recorded` is the store manifest's `matmul_precision` (None for a store collected before
    Revision 4; that absence is never filled with a default). `entry` = "recorded" uses it and
    raises if the store records none. An explicit "highest"/"default" is accepted for a legacy
    store, and on a recording store only when it equals the recorded mode."""
    if entry not in STORE_PRECISION_ENTRIES:
        raise ValueError(f"store_matmul_precision entry {entry!r} for {store} must be one of "
                         f"{STORE_PRECISION_ENTRIES}")
    if entry == "recorded":
        if recorded is None:
            raise ValueError(f"store_matmul_precision 'recorded' for {store}, but its manifest "
                             f"records no matmul_precision (collected before Revision 4). "
                             f"Give its collection mode explicitly ({PRECISIONS}).")
        if recorded not in PRECISIONS:
            raise ValueError(f"{store}: manifest matmul_precision {recorded!r} not in {PRECISIONS}")
        return recorded
    if recorded is not None and entry != recorded:
        raise ValueError(f"store_matmul_precision {entry!r} for {store} conflicts with the "
                         f"mode its manifest records ({recorded!r}); use 'recorded'.")
    return entry
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
              "layers", "assert_n_episodes", "tool_checks", "capture_matmul_precision",
              "headline_capture"):
        _req(man, k)
    if man["capture_matmul_precision"] not in CAPTURE_PRECISIONS:
        raise ValueError(f"capture_matmul_precision must be one of {CAPTURE_PRECISIONS} "
                         f"(Revision 4, R4-1: every kept activation is full float32), got "
                         f"{man['capture_matmul_precision']!r}")
    _req(man["tool_checks"], "shift_change_rows_max", "manifest.tool_checks")
    _req(man["tool_checks"], "buffer_index_rel_tol", "manifest.tool_checks")
    for p in man["probes"]:
        for k in ("id", "stores", "n_per_store", "rows_per_episode", "seed",
                  "store_matmul_precision"):
            _req(p, k, f"manifest.probes[{p.get('id')}]")
        if not p["stores"]:
            raise ValueError(f"probe {p['id']}: no stores listed")
        if (len(p["store_matmul_precision"]) != len(p["stores"])
                or any(x not in STORE_PRECISION_ENTRIES for x in p["store_matmul_precision"])):
            raise ValueError(f"probe {p['id']}: store_matmul_precision must list one of "
                             f"{STORE_PRECISION_ENTRIES} per store, in the order of `stores`")
    for r in man["runs"]:
        for k in ("label", "path", "checkpoints"):
            _req(r, k, f"manifest.runs[{r.get('label')}]")
    for layer in man["layers"]:
        key, fl = _req(layer, "key", "manifest.layers"), _req(layer, "flatten", "manifest.layers")
        want = FLATTEN.get(key, "none")
        if fl != want:
            raise ValueError(f"layer {key}: flatten must be {want!r}, got {fl!r}")
        if _req(layer, "keep", "manifest.layers") not in KEEPS:
            raise ValueError(f"layer {key}: keep must be one of {KEEPS}, got {layer['keep']!r}")
    hc = man["headline_capture"]
    if hc is not None:
        if not isinstance(hc, dict) or set(hc) != {"checkpoint", "probe"}:
            raise ValueError(f"headline_capture must be null or {{checkpoint, probe}}, got {hc!r}")
        if hc["probe"] not in [p["id"] for p in man["probes"]]:
            raise ValueError(f"headline_capture probe {hc['probe']!r} is not a manifest probe")
        if not any(str(hc["checkpoint"]) in [str(c) for c in r["checkpoints"]] for r in man["runs"]):
            raise ValueError(f"headline_capture checkpoint {hc['checkpoint']!r} is no run's checkpoint")
    elif any(l["keep"] == "headline_only" for l in man["layers"]):
        raise ValueError("layers marked headline_only, but headline_capture is null: they would "
                         "never be kept")
    return man


# ------------------------------------------------------------ R4-2: what each capture keeps ---
KEEPS = ("every_capture", "headline_only")
ALWAYS_KEPT = ("logits", "value")        # besides the rules' verdict layers


def check_keep(man: dict, verdict_layers) -> None:
    """Revision 4, R4-2: every verdict layer (the rules' common.verdict_layers), `logits` and
    `value` must be listed with keep: every_capture; otherwise the load raises."""
    keep = {l["key"]: l["keep"] for l in man["layers"]}
    for k in list(verdict_layers) + list(ALWAYS_KEPT):
        if keep.get(k) != "every_capture":
            raise ValueError(f"layer {k!r} must be listed with keep: every_capture (Revision 4, "
                             f"R4-2); the manifest has {keep.get(k)!r}")


def capture_plan(man: dict, drift_pairs, ordinary_labels) -> list[dict]:
    """Every capture the manifest asks for, with the layers it keeps (Revision 4, R4-2).

    - A trained (run, selector) is replayed on every probe, except a `:prev` selector, which
      is replayed only on the probe its `parameters.A4.drift_pairs` entry names (a `:prev`
      selector that no drift pair names raises: it would serve no statistic).
    - It keeps the `every_capture` layers, plus the `headline_only` layers when (selector,
      probe) is the manifest's `headline_capture`.
    - Every ordinary run (`ordinary_labels`, read from its saved config) also gets its
      untrained network (`untrained.build`, the network the run started from), replayed on
      every probe with the `every_capture` layers only: the rules pair UNTRAINED networks on
      verdict layers."""
    every = [l["key"] for l in man["layers"] if l["keep"] == "every_capture"]
    headline = [l["key"] for l in man["layers"] if l["keep"] == "headline_only"]
    hc = man["headline_capture"]
    probes = [p["id"] for p in man["probes"]]
    prev_probe = {}
    for d in drift_pairs:
        if d["probe"] in probes:
            prev_probe[str(d["prev"])] = d["probe"]
    plan = []
    for r in man["runs"]:
        for sel in r["checkpoints"]:
            sel = str(sel)
            if sel.endswith(":prev"):
                if sel not in prev_probe:
                    raise ValueError(f"run {r['label']}: selector {sel!r} is named by no "
                                     f"parameters.A4.drift_pairs entry whose probe is in this "
                                     f"manifest; a :prev checkpoint is replayed only on its "
                                     f"drift pair's probe")
                on = [prev_probe[sel]]
            else:
                on = probes
            for pid in on:
                is_head = hc is not None and str(hc["checkpoint"]) == sel and hc["probe"] == pid
                plan.append({"label": r["label"], "path": r["path"], "selector": sel,
                             "kind": "trained", "probe": pid,
                             "layers": every + (headline if is_head else []),
                             "headline": is_head})
        if r["label"] in ordinary_labels:
            for pid in probes:
                plan.append({"label": r["label"], "path": r["path"], "selector": "untrained",
                             "kind": "untrained", "probe": pid, "layers": list(every),
                             "headline": False})
    return plan


def _git(*args) -> str:
    try:
        return subprocess.run(["git", "-C", _ROOT, *args], capture_output=True, text=True,
                              timeout=60).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def run_role(run_dir) -> dict:
    """Arm and seed from the run's own saved config (top-level `seed:`, KNOWN_BUGS l.114;
    `agent.modulation.type`, None for the ordinary agent), never from a manifest label."""
    saved = yaml.safe_load((Path(run_dir) / "models" / "config.yaml").read_text())
    mtype = (saved["agent"].get("modulation") or {}).get("type")
    return {"seed": int(saved["seed"]), "tag": saved.get("tag"), "modulation_type": mtype,
            "arm": "ordinary" if mtype is None else "modulated"}


def _layer_widths(model, D: int) -> dict:
    """{key: columns per row} of every tensor forward_with_activations returns."""
    import jax.numpy as jnp
    from flax import nnx
    acts = nnx.jit(lambda m, x, h: m.forward_with_activations(x, h)[4])(
        model, jnp.zeros((1, D), jnp.float32), model.initial_state(1))
    return {k: int(np.prod(v.shape[1:])) for k, v in acts.items()}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--batch-size", type=int, required=True,
                    help="episodes per replay batch (memory only; every batch pads to max_steps)")
    ap.add_argument("--probes-only", action="store_true", help="build/verify probes, no replay")
    ap.add_argument("--rebuild-probes", action="store_true")
    args = ap.parse_args(argv)

    import jax
    import flax
    from scripts.analysis.nmn import probe_set, rules_pin, teacher_forced, untrained
    from scripts.analysis.nmn.replay import LoadedAgent, load_agent
    from src.environment.sensor import get_observation_breakdown
    import collect_trajectories as ct

    # Revision 4 (R4-1): the float32 self-test runs first, before anything is read or written.
    # It raises (naming the device) above the collector's FLOAT32_MATMUL_MAX_REL_ERR.
    selftest = ct.assert_float32_matmul("highest")
    replay_device_kind = jax.devices()[0].device_kind
    print(f"[run_activations] float32 matmul self-test on {replay_device_kind}: "
          f"{selftest:.3e} (limit {ct.FLOAT32_MATMUL_MAX_REL_ERR:.0e})", flush=True)

    man_path = _abs(args.manifest)
    man = load_manifest(man_path)
    pinned = rules_pin.load(man)
    status = man["evidence_status"]
    policy = rules_pin.evidence_policy(pinned, status)
    if policy["verdict_words_allowed"]:
        rules_pin.require_clean(pinned)
    P = pinned.parameters
    verdict_layers = list(pinned.rules["common"]["verdict_layers"])
    check_keep(man, verdict_layers)
    g1 = {k: float(rules_pin.param(P, f"gates.G1.{k}"))
          for k in ("action_agreement_min", "near_tie_logit_margin", "near_tie_fraction_max")}
    g3 = {k: float(rules_pin.param(P, f"gates.G3.{k}"))
          for k in ("alignment_agreement_min", "shift_control_agreement_max")}
    g2_tol = float(rules_pin.param(P, "gates.G2.reconstruction_rel_tol"))
    test_frac = float(rules_pin.param(P, "common.split.test_frac"))
    min_test_groups = int(rules_pin.param(P, "gates.G6.test_fold_groups_min"))
    roles = {r["label"]: run_role(_abs(r["path"])) for r in man["runs"]}
    plan = capture_plan(man, rules_pin.param(P, "A4.drift_pairs"),
                        [lab for lab, ro in roles.items() if ro["arm"] == "ordinary"])

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
    run_meta = {"generated_utc": datetime.now(timezone.utc).isoformat(),
                "git_sha": _git("rev-parse", "HEAD"), "git_dirty": bool(_git("status", "--porcelain")),
                "manifest": str(man_path.relative_to(_ROOT)),
                "manifest_sha256": hashlib.sha256(man_path.read_bytes()).hexdigest(),
                "python": platform.python_version(), **statement,
                "float32_matmul_selftest": {"max_rel_err": selftest,
                                            "limit": ct.FLOAT32_MATMUL_MAX_REL_ERR,
                                            "replay_device_kind": replay_device_kind},
                "gates_read": {"G1": g1, "G2": g2_tol, "G3": g3, "G6_test_fold_groups_min": min_test_groups,
                               "split_test_frac": test_frac},
                "tool_checks": man["tool_checks"], "headline_capture": man["headline_capture"],
                "roles": roles, "probes": {}, "captures": []}
    run_meta["versions"] = {"jax": jax.__version__, "flax": flax.__version__,
                            "numpy": np.__version__, "device": str(jax.devices()[0])}

    probes, check_modes = {}, {}
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
        check_modes[pid] = [resolve_store_precision(e, sm["matmul_precision"], sm["store"])
                            for e, sm in zip(pdef["store_matmul_precision"], probe.store_meta)]
        run_meta["probes"][pid] = {"row_index_sha256": probe.row_sha256, "counts": probe.counts,
                                   "npz_bytes": (out / "probes" / f"probe_{pid}.npz").stat().st_size,
                                   "store_check_precision": check_modes[pid],
                                   "store_matmul_precision_recorded": [sm["matmul_precision"]
                                                                       for sm in probe.store_meta],
                                   "store_compute_device_kind": [sm["compute_device_kind"]
                                                                 for sm in probe.store_meta]}
    if args.probes_only:
        (out / "manifest.json").write_text(json.dumps(run_meta, indent=1, default=str))
        return 0

    # R4-2: expected bytes of every planned capture, printed before the first replay
    widths = {}
    for r in man["runs"]:
        m, ep = untrained.build(_abs(r["path"]), seed=0)          # shapes only; seed irrelevant
        widths[r["label"]] = _layer_widths(m, sum(get_observation_breakdown(ep).values()))
    expected = 0
    for c in plan:
        w = widths[c["label"]]
        expected += probes[c["probe"]].rows.size * 4 * sum(w[k] for k in c["layers"] if k in w)
    run_meta["expected_activation_bytes"] = expected
    print(f"[run_activations] {len(plan)} captures planned; expected activation bytes "
          f"{expected / 1e9:.2f} GB", flush=True)

    failures, measured = [], 0
    agent_cache = {}
    for c in plan:
        run_dir = _abs(c["path"])
        if c["kind"] == "trained":
            info = ct.resolve_checkpoint_info(run_dir, c["selector"])
            key = (c["label"], info["step"])
            if key not in agent_cache:
                agent_cache.clear()
                agent_cache[key] = load_agent(run_dir / "models", info["step"])
            agent = agent_cache[key]
            step, saved_stage = info["step"], info["saved_stage"]
        else:
            model, env_params = untrained.build(run_dir)          # the run's own, checked seed
            saved = yaml.safe_load((run_dir / "models" / "config.yaml").read_text())
            bd = get_observation_breakdown(env_params)
            agent = LoadedAgent(model=model, env_params=env_params, agent_cfg=saved["agent"],
                                step=0, obs_breakdown=bd,
                                action_dim=4 + int(env_params.rest_action_enabled)
                                + int(env_params.eat_action_enabled),
                                env_config_path=str(run_dir / "models" / "config.yaml"))
            info, step, saved_stage = None, 0, None
        pid = c["probe"]
        probe = probes[pid]
        bd = dict(sorted(agent.obs_breakdown.items()))
        for sm in probe.store_meta:
            smb = dict(sorted(read_store_breakdown(sm["store"]).items()))
            if smb != bd or sm["D"] != sum(bd.values()):
                raise ValueError(f"{c['label']}: observation breakdown differs from "
                                 f"store {sm['store']}")
        gen = []
        if info is not None:
            ckpt = str(Path(info["ckpt_dir"]).resolve())
            gen = [i for i, sm in enumerate(probe.store_meta)
                   if str(Path(sm["checkpoint_path"]).resolve()) == ckpt]
        t0 = time.time()
        acts, rep = teacher_forced.replay(
            agent, probe, c["layers"], batch_size=args.batch_size, is_generating=bool(gen),
            g1=g1, g3=g3, g2_tol=g2_tol,
            shift_change_rows_max=float(man["tool_checks"]["shift_change_rows_max"]),
            buffer_index_rel_tol=float(man["tool_checks"]["buffer_index_rel_tol"]),
            assert_n_episodes=int(man["assert_n_episodes"]),
            store_id_of_agent=(gen[0] if gen else None),
            capture_precision=man["capture_matmul_precision"],
            check_precision=(check_modes[pid][gen[0]] if gen else None))
        stem = f"acts_{c['label']}__{c['selector'] if c['kind'] == 'untrained' else step}__{pid}"
        nbytes = teacher_forced.save_activations(out / f"{stem}.npz", acts, probe.row_sha256)
        measured += nbytes
        rep.update({"run_label": c["label"], "run_path": str(c["path"]), "kind": c["kind"],
                    "selector": c["selector"], "checkpoint_step": step,
                    "saved_stage": saved_stage, "role_from_saved_config": roles[c["label"]],
                    "headline_capture": c["headline"], "layers_requested": c["layers"],
                    "env_config_path": agent.env_config_path, "probe": pid,
                    # Revision 4 (R4-1), per store of the probe: the self-replay check mode,
                    # the store's collection card, and this replay's card
                    "stores_device": [{"store": sm["store"],
                                       "check_precision": check_modes[pid][i],
                                       "store_matmul_precision": sm["matmul_precision"],
                                       "store_compute_device_kind": sm["compute_device_kind"]}
                                      for i, sm in enumerate(probe.store_meta)],
                    "replay_device_kind": replay_device_kind,
                    "activations_file": f"{stem}.npz", "activations_bytes": nbytes,
                    "seconds": round(time.time() - t0, 1), **statement,
                    "generated_utc": datetime.now(timezone.utc).isoformat()})
        (out / f"{stem}.json").write_text(json.dumps(rep, indent=1, default=str))
        run_meta["captures"].append({"stem": stem, "label": c["label"], "kind": c["kind"],
                                     "selector": c["selector"], "step": step, "probe": pid,
                                     "failures": rep["failures"]})
        print(f"[run_activations] {stem}: {rep['seconds']}s, {nbytes/1e6:.0f} MB, "
              f"failures={rep['failures']}", flush=True)
        failures += [f"{stem}: {f}" for f in rep["failures"]]
    run_meta["measured_activation_bytes"] = measured
    print(f"[run_activations] activation bytes: expected {expected / 1e9:.3f} GB, measured "
          f"{measured / 1e9:.3f} GB", flush=True)
    (out / "manifest.json").write_text(json.dumps(run_meta, indent=1, default=str))
    if failures:
        raise SystemExit("tool checks failed:\n  " + "\n  ".join(failures))
    return 0


def read_store_breakdown(store) -> dict:
    from src.utils.trajectory_store import read_manifest
    return read_manifest(store)["observation_breakdown"]


if __name__ == "__main__":
    sys.exit(main())
