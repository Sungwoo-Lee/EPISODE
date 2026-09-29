"""Synthetic fixtures for the Stage 3 driver tests (test fixture data, never study data).

- `scanned_runs`: WandB-like episode rows for six continual runs (3 ordinary, 3 modulated),
  five stages, in the shape `wandb_history.scan` returns, with survival and bites that differ
  by stage and rise within each stage (so the stage, the window and the row weighting each
  change the level read).
- `write_capture_dir`: a complete run_activations output directory (probe, activation files,
  capture reports, manifest.json) for a pooled probe, so the drivers run end to end on it.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

BOUNDARIES = [1_500_000, 3_000_000, 3_700_000, 4_400_000, 5_100_000]
LOG_EVERY = 4000


def scanned_runs(arms=("ordinary", "modulated") * 3, base_steps=200.0) -> dict:
    """{label: {"arm", "boundaries", "scanned"}} for survival_block."""
    out = {}
    for i, arm in enumerate(arms):
        rows, lo = [], 0
        for k, hi in enumerate(BOUNDARIES):
            e = lo + LOG_EVERY
            while e <= hi:
                frac = (e - lo) / (hi - lo)
                rows.append({"Episode/Number": float(e), "Episode/_window_n": 2500.0 + 7 * (i % 3),
                             "Episode/Steps": base_steps + 10.0 * k + 30.0 * frac + 2.0 * i,
                             "Episode/FoodEaten": 3.0 + 0.5 * k + frac, "stage/index": float(k)})
                e += LOG_EVERY
            lo = hi
        label = f"{arm}_s{42 + i // 2}"
        out[label] = {"arm": arm, "boundaries": list(BOUNDARIES),
                      "scanned": {"rows": rows, "exit_code": 0, "file": f"<synthetic {label}>",
                                  "truncated": None}}
    return out


VERDICT = ["enc.out", "rnn.state", "rnn.out", "actor.out", "critic.out"]


def write_capture_dir(out: Path, runs: list[dict], *, n_groups: int, width: int, rules_sha: str,
                      probe_id: str = "p", selector: str = "stage_end:0", seed: int = 0,
                      mod_gain: bool = True, headline_extra: dict | None = None) -> None:
    """runs: [{label, arm, seed}]. One store per run (pooled probe: every seed in every store),
    one kept row per episode. Every agent's layer is a linear map of a shared latent plus
    noise (modulated agents get a per-unit gain), so every statistic is finite."""
    from scripts.analysis.nmn import probe_set, teacher_forced
    rng = np.random.default_rng(seed)
    S = len(runs)
    T = 6
    ep_seed = np.tile(1_000_000 + np.arange(n_groups), S)
    ep_store = np.repeat(np.arange(S), n_groups)
    E = ep_seed.size
    ep_T = np.full(E, T, np.int64)
    ep_trunc = rng.random(E) < 0.3
    ep_off = np.arange(E, dtype=np.int64) * T
    D = 4
    obs_all = rng.normal(size=(E * T, D)).astype(np.float32)
    t_all = np.tile(np.arange(T), E)
    rows = ep_off + rng.integers(0, T, E)
    lat = rng.normal(size=(rows.size, 6))
    # satiation is an observed channel; stored so that symlog (the network's input transform)
    # returns it exactly
    obs_all[rows, 0] = np.sign(lat[:, 0]) * np.expm1(np.abs(lat[:, 0]))
    targets = {"satiation": lat[:, 0].astype(np.float64),
               "injury_level": lat[:, 1] + 0.1 * rng.normal(size=rows.size),
               "nearest_predator_manhattan": np.abs(lat[:, 2]) * 5,
               "predator_valid": rng.random(rows.size) < 0.7,
               "steps_remaining": (T - t_all[rows]).astype(np.float64) + lat[:, 3],
               "truncated": ep_trunc}
    probe = probe_set.Probe(
        probe_id=probe_id, stores=[f"<store {r['label']}>" for r in runs],
        store_meta=[{"store": f"<store {r['label']}>", "checkpoint_path": f"<ckpt {r['label']}>",
                     "D": D, "matmul_precision": "highest", "compute_device_kind": "cpu"}
                    for r in runs],
        ep_store=ep_store, ep_seed=ep_seed, ep_T=ep_T, ep_truncated=ep_trunc, ep_offset=ep_off,
        obs_all=obs_all, action_next_all=np.zeros(E * T, np.int64),
        action_cur_all=np.zeros(E * T, np.int64), t_all=t_all, rows=rows, targets=targets,
        counts={"distinct_episode_seed_groups": n_groups})
    probe.row_sha256 = probe_set.row_index_sha256(probe)
    probe_set.save(probe, out / "probes")
    captures, roles = [], {}
    agents = [(r, "trained") for r in runs] + [(r, "untrained") for r in runs
                                              if r["arm"] == "ordinary"]
    for r, kind in agents:
        roles[r["label"]] = {"seed": r["seed"], "tag": r["label"], "arm": r["arm"],
                             "modulation_type": None if r["arm"] == "ordinary" else "FiLM"}
        sel = selector if kind == "trained" else "untrained"
        acts = {}
        for j, k in enumerate(VERDICT + ["logits", "value"]):
            w = 6 if k == "logits" else (1 if k == "value" else width)
            M = np.random.default_rng(1000 * r["seed"] + j + (7 if kind == "untrained" else 0)
                                      ).normal(size=(6, w))
            a = lat @ M + 0.3 * rng.normal(size=(rows.size, w))
            if r["arm"] == "modulated" and mod_gain:
                a = a * np.linspace(0.5, 3.0, w)
            acts[k] = a.astype(np.float32)
        if kind == "trained" and headline_extra:
            for k, w in headline_extra.items():
                acts[k] = (lat @ rng.normal(size=(6, w))).astype(np.float32)
        stem = f"acts_{r['label']}__{sel if kind == 'untrained' else 1500000}__{probe_id}"
        teacher_forced.save_activations(out / f"{stem}.npz", acts, probe.row_sha256)
        rep = {"run_label": r["label"], "selector": sel, "probe": probe_id, "kind": kind,
               "activations_file": f"{stem}.npz", "failures": [],
               "chain_assertions": {"max_rel_deviation": {k: 1e-7 for k in acts}}}
        if kind == "trained":
            n = int((ep_store == runs.index(r)).sum() * T)
            rep["gate_G1_self_agreement"] = {"rows": n, "disagree_not_near_tie": 0,
                                             "disagree_near_tie": 0}
            rep["alignment_controls"] = {
                "step_discontinuous_all": {"rows": n // T, "disagree_not_near_tie": 0,
                                           "disagree_near_tie": 0},
                "shift_by_one_all_rows_with_t_ge_1": 0.5}
        (out / f"{stem}.json").write_text(json.dumps(rep))
        captures.append({"stem": stem, "label": r["label"], "kind": kind, "selector": sel,
                         "probe": probe_id, "failures": []})
    (out / "manifest.json").write_text(json.dumps({
        "decision_rules": {"sha256": rules_sha}, "captures": captures, "roles": roles,
        "probes": {probe_id: {"row_index_sha256": probe.row_sha256}}}))
