#!/usr/bin/env python3
"""behavioural_combination_gain.py -- measure 4 of the level-05 body-interactions design.

Plain language: how much better can you predict what the agent does next if you know TWO of its body
readings (food energy, injury, body temperature) instead of the single most informative one? A
large gain means the agent's choices depend on combinations of body states. This is the ideal
planner's own "combination gain" (scripts/analysis/studies/internal_state_interactions/planner.py,
`summarise_map`) applied to the agent's recorded behaviour.

Definitions (LEVEL05_BODY_INTERACTIONS.md §4.1 measure 4; every constant from the analysis manifest):
  rows        DECISION rows t = 0..T-1 (see _common.py); body state read at t
  activity    what the action taken from state t led to, in priority order:
                eating  -- ate_food on row t+1
                cover   -- agent_in_bush on row t+1
                ring    -- the agent's cell on row t+1 is at Manhattan distance exactly 1 from an
                           active fire obstacle (fire = obstacle slot with obs_temp_ratio_high > 0 in
                           the run's own params; active = the episode's obs_active draw), the
                           "fire ring" of internal_state_interactions/measure_world.py
                open    -- anything else
  variables   nutrition (store column) in `gain_bins` equal bins over gain_nutrition_range; injury
              (injury_level) likewise over gain_injury_range; body temperature from the obs_true
              "Body Temperature" slot (raw degrees) in equal bins between the reference run's
              `gain_temperature_percentiles`, FROZEN by --freeze before other runs are read, with the
              outer bins open-ended. Values outside the nutrition/injury ranges are clipped in.
  accuracy    single(v)  = sum over v's bins of the most common activity's count / N
              pair(u, v) = the same over the joint (u, v) bins
  gain        max pair accuracy - max single accuracy (percentage points in the output)
  sparse bins any variable bin holding < min_steps_per_gain_bin rows is dropped (all its rows), and
              the dropped bins and rows are counted in the output.
  Caveat carried from the design: under A1, "ring" is itself taxed, so an A1 effect here can be
  less warming rather than a new combination rule.

Outputs (manifest out_dir): frozen_temperature_bins.json (by --freeze), combination_gain.json,
combination_gain_worlds.csv; per-store count tables cached under cache/.

Usage:
  PY=/home/vncuser/miniconda3/envs/grid_world_pain/bin/python
  $PY scripts/analysis/studies/level05_body_interactions/behavioural_combination_gain.py MANIFEST --freeze
  $PY scripts/analysis/studies/level05_body_interactions/behavioural_combination_gain.py MANIFEST
  --max-shards N: tooling tests (incomplete stores accepted; *_PARTIAL outputs; no cache).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime
from functools import partial
from itertools import combinations
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common as C  # noqa: E402

ACTS = ("eating", "cover", "ring", "open")
VARS = ("nutrition", "injury", "body_temperature")


def _shard_temp(shard, D, temp_i):
    r = C.read_decision_rows(Path(shard), [], [temp_i], D)
    return r[f"obs_{temp_i}"].astype(np.float32)


def _edges(lo, hi, n):
    return np.linspace(lo, hi, n + 1)[1:-1]            # interior edges; outer bins open-ended


def _shard_table(shard, D, temp_i, fire_slots, nb, nut_rng, inj_rng, temp_edges):
    import pyarrow.parquet as pq
    shard = Path(shard)
    r = C.read_decision_rows(shard, ["nutrition", "injury_level", "obs_row", "obs_col"], [temp_i], D,
                             next_cols=("ate_food", "agent_in_bush", "agent_row", "agent_col"))
    ep = pq.read_table(shard.with_name(shard.name.replace("steps_", "episodes_")),
                       columns=["episode_seed", "obs_active"])
    ep_seed = ep.column("episode_seed").to_numpy()
    from src.utils.trajectory_store import _list_column_to_2d
    active = _list_column_to_2d(ep, "obs_active", len(fire_slots)).astype(bool)
    order = np.argsort(ep_seed)
    pos = order[np.searchsorted(ep_seed[order], r["episode_seed"])]
    if not np.array_equal(ep_seed[pos], r["episode_seed"]):
        raise ValueError(f"{shard}: step rows name episodes absent from the episode shard")
    fire_act = active[pos][:, fire_slots]                              # (n, F)
    orow = r["obs_row"][:, fire_slots].astype(np.int64)
    ocol = r["obs_col"][:, fire_slots].astype(np.int64)
    dist = (np.abs(orow - r["agent_row_next"].astype(np.int64)[:, None])
            + np.abs(ocol - r["agent_col_next"].astype(np.int64)[:, None]))
    ring = np.any((dist == 1) & fire_act, axis=1)
    act = np.full(ring.size, 3, np.int64)                              # open
    act[ring] = 2
    act[r["agent_in_bush_next"].astype(bool)] = 1
    act[r["ate_food_next"].astype(bool)] = 0

    def binv(x, lo, hi):
        return np.clip(np.floor((x - lo) / (hi - lo) * nb), 0, nb - 1).astype(np.int64)
    bn = binv(r["nutrition"].astype(np.float64), *nut_rng)
    bi = binv(r["injury_level"].astype(np.float64), *inj_rng)
    bt = np.searchsorted(temp_edges, r[f"obs_{temp_i}"], side="right").astype(np.int64)
    flat = ((bn * nb + bi) * nb + bt) * len(ACTS) + act
    return np.bincount(flat, minlength=nb ** 3 * len(ACTS))


def store_table(store_dir, man, temp_edges, workers, max_shards):
    lay = C.store_layout(store_dir)
    temp_i = C.slot_index(lay, man["temperature_slot"])
    nb = int(man["gain_bins"])
    fn = partial(_shard_table, D=lay["D"], temp_i=temp_i, fire_slots=lay["fire_slots"], nb=nb,
                 nut_rng=tuple(man["gain_nutrition_range"]), inj_rng=tuple(man["gain_injury_range"]),
                 temp_edges=np.asarray(temp_edges))
    parts = C.parallel_map(fn, [str(s) for s in C.shard_files(store_dir, max_shards)], workers)
    tab = np.sum(parts, axis=0)
    return {"store": str(store_dir.relative_to(C.ROOT)), "ckpt_step": lay["ckpt_step"],
            "shards_read": len(parts), "fire_slots": int(lay["fire_slots"].sum()),
            "counts": tab.tolist()}


def gain(counts, nb, min_n):
    T = np.asarray(counts, np.int64).reshape(nb, nb, nb, len(ACTS))    # (nut, inj, temp, act)
    keep = [T.sum(axis=tuple(a for a in range(4) if a != v)) >= min_n for v in range(3)]
    dropped = {VARS[v]: {"bins": int((~keep[v]).sum()),
                         "rows": int(T.sum(axis=tuple(a for a in range(4) if a != v))[~keep[v]].sum())}
               for v in range(3)}
    T = T[np.ix_(keep[0], keep[1], keep[2], np.ones(len(ACTS), bool))]
    N = int(T.sum())
    if N == 0:
        return {"N": 0, "dropped": dropped, "gain": None}

    def acc(vs):
        red = T.sum(axis=tuple(v for v in range(3) if v not in vs))
        return float(red.reshape(-1, len(ACTS)).max(axis=1).sum() / N)
    single = {VARS[v]: acc((v,)) for v in range(3)}
    pair = {f"{VARS[u]} + {VARS[v]}": acc((u, v)) for u, v in combinations(range(3), 2)}
    shares = (T.sum(axis=(0, 1, 2)) / N).tolist()
    g = max(pair.values()) - max(single.values())
    return {"N": N, "dropped": dropped, "activity_shares": dict(zip(ACTS, shares)),
            "single_accuracy": single, "pair_accuracy": pair,
            "best_single": max(single, key=single.get), "best_pair": max(pair, key=pair.get),
            "gain": g, "gain_points": 100 * g}


def freeze(man, workers, force, max_shards, ref_override):
    ref_label = ref_override or man["reference_label"]
    ref = [r for r in man["_runs"] if r["label"] == ref_label]
    if len(ref) != 1:
        raise ValueError(f"reference label {ref_label!r} matches {len(ref)} runs")
    st = C.select_stores(man, ref[0], pooled=False)
    if not st:
        raise RuntimeError(f"{ref_label}: no complete final-checkpoint store yet; cannot freeze")
    path = C.out_dir(man) / ("frozen_temperature_bins_PARTIAL.json" if max_shards
                             else "frozen_temperature_bins.json")
    if path.exists() and not force and not max_shards:
        raise RuntimeError(f"{path} exists: bins are frozen. --force-refreeze overwrites (post hoc).")
    step, d = st[0]
    lay = C.store_layout(d)
    temp_i = C.slot_index(lay, man["temperature_slot"])
    vals = np.concatenate(C.parallel_map(partial(_shard_temp, D=lay["D"], temp_i=temp_i),
                                         [str(s) for s in C.shard_files(d, max_shards)], workers))
    plo, phi = man["gain_temperature_percentiles"]
    lo, hi = (float(x) for x in np.percentile(vals, [plo, phi]))
    nb = int(man["gain_bins"])
    rec = {"reference_label": ref_label, "store": str(d.relative_to(C.ROOT)), "ckpt_step": step,
           "slot": man["temperature_slot"], "percentiles": [plo, phi], "lo": lo, "hi": hi,
           "bins": nb, "interior_edges": _edges(lo, hi, nb).tolist(), "decision_rows": int(vals.size),
           "temp_min": float(vals.min()), "temp_max": float(vals.max()),
           "frozen_at": datetime.now().isoformat(timespec="seconds"), "refrozen": bool(path.exists()),
           "partial_max_shards": max_shards}
    C.write_json(path, rec)
    print(json.dumps(rec, indent=1))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("manifest")
    ap.add_argument("--freeze", action="store_true")
    ap.add_argument("--force-refreeze", action="store_true")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--max-shards", type=int, default=None)
    ap.add_argument("--reference-override", default=None)
    a = ap.parse_args(argv)
    if a.reference_override and not a.max_shards:
        raise ValueError("--reference-override is for tooling tests only; it requires --max-shards")
    man = C.load_manifest(a.manifest)
    C.ALLOW_INCOMPLETE = a.max_shards is not None
    if a.freeze:
        return freeze(man, a.workers, a.force_refreeze, a.max_shards, a.reference_override)

    od = C.out_dir(man)
    partial_run = a.max_shards is not None
    fz_path = od / ("frozen_temperature_bins_PARTIAL.json" if partial_run else "frozen_temperature_bins.json")
    if not fz_path.exists():
        raise RuntimeError(f"{fz_path} missing: run with --freeze first (on the reference run).")
    fz = json.loads(fz_path.read_text())
    if not partial_run and fz["reference_label"] != man["reference_label"]:
        raise ValueError(f"{fz_path} was frozen from {fz['reference_label']!r}")
    nb, min_n = int(man["gain_bins"]), int(man["min_steps_per_gain_bin"])
    edges = fz["interior_edges"]
    key = hashlib.sha1(json.dumps([nb, man["gain_nutrition_range"], man["gain_injury_range"], edges],
                                  sort_keys=True).encode()).hexdigest()[:10]
    cache = od / "cache" / "combination_gain"
    cache.mkdir(parents=True, exist_ok=True)

    runs_out, by_world = {}, {}
    for run in man["_runs"]:
        st = C.select_stores(man, run, pooled=False)
        rec = {"world": run["world"], "agent": run["agent"], "run": run["run_name"], "final": None}
        if st:
            d = st[0][1]
            print(f"[combination_gain] {run['label']}: {d}", flush=True)
            cp = cache / f"{d.parts[-3]}_{d.parts[-2]}_{key}.json"
            if cp.exists() and not partial_run:
                tab = json.loads(cp.read_text())
            else:
                tab = store_table(d, man, edges, a.workers, a.max_shards)
                if not partial_run:
                    C.write_json(cp, tab)
            rec["final"] = {k: tab[k] for k in ("store", "ckpt_step", "shards_read", "fire_slots")} \
                | gain(tab["counts"], nb, min_n)
        else:
            print(f"[combination_gain] {run['label']}: no complete final store yet", flush=True)
        runs_out[run["label"]] = rec
        by_world.setdefault(run["world"], {})[run["agent"]] = run["label"]

    hi, lo = man["difference"]
    worlds = {}
    for w, ag in sorted(by_world.items()):
        f = {k: runs_out[ag[k]]["final"] for k in (hi, lo)}
        if any(v is None or v.get("gain") is None for v in f.values()):
            worlds[w] = {"world": w, "status": "missing store"}
            continue
        worlds[w] = {"world": w, "status": "ok", f"gain_points_{hi}": f[hi]["gain_points"],
                     f"gain_points_{lo}": f[lo]["gain_points"],
                     "D_gain_points": f[hi]["gain_points"] - f[lo]["gain_points"]}

    out = {"generated": datetime.now().isoformat(timespec="seconds"), "manifest": a.manifest,
           "partial": partial_run, "max_shards": a.max_shards, "frozen_temperature_bins": fz,
           "activities": ACTS, "difference": f"{hi} - {lo}", "runs": runs_out, "worlds": worlds}
    suffix = "_PARTIAL" if partial_run else ""
    C.write_json(od / f"combination_gain{suffix}.json", out)
    cols = sorted({k for r in worlds.values() for k in r}, key=lambda k: (k != "world", k))
    with open(od / f"combination_gain_worlds{suffix}.csv", "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=cols)
        wr.writeheader()
        for r in worlds.values():
            wr.writerow(r)
    print(f"[combination_gain] wrote {od / f'combination_gain{suffix}.json'}")


if __name__ == "__main__":
    sys.exit(main())
