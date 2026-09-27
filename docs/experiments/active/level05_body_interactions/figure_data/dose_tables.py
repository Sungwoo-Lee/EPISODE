#!/usr/bin/env python3
"""dose_tables.py -- figure tables for the level-05 body-interactions factorial (analysis working script).

Plain language: for every world and agent, how does time in cover change with how injured the agent
is, separately when it is well fed and when it is hungry; and how does eating change with how full it
is, separately when it is barely hurt and when it is badly hurt. In the spirit of
scripts/analysis/injury_dose_store.py (ten-point injury bins), with the nutrition split added.

Rows: DECISION rows t = 0..T-1 of the final-checkpoint store (the states the policy acted from; the
same convention and reader as scripts/analysis/studies/level05_body_interactions/_common.py).
  in cover   agent_in_bush at t            (same definition as measure 1)
  ate        ate_food on row t+1           (the action taken from t ate; same as measure 3)
  true injury injury_level at t, bins [0,10), [10,20) ... [90,100] (last bin closed)
  nutrition  at t; bins of 10 points from 0 to max_nutrition (last bin closed)
  fed = nutrition >= 100, hungry = nutrition < 60 (the pre-registered bands)
  injury split for eating: low = injury 0-20, high = injury 60-100 (the pre-registered ranges), + all
Every cell carries n (rows) and k (numerator); share = k / n, null when n < 200 (min_steps_per_cell).
Survival steps only; reward is never read.

Usage: PY dose_tables.py MANIFEST OUT_DIR [--workers N]
Writes OUT_DIR/dose_<label>.json per run (cached; skipped if present) and OUT_DIR/dose_tables.json.
"""
from __future__ import annotations
import argparse, json, sys
from functools import partial
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "scripts/analysis/studies/level05_body_interactions"))
import _common as C  # noqa: E402

INJ_EDGES = np.arange(0, 101, 10.0)            # 10 bins
MIN_N = 200


def _bin(x, edges):
    return np.clip(np.searchsorted(edges, x, side="right") - 1, 0, len(edges) - 2)


def _shard(shard, nut_edges, bands, ranges):
    r = C.read_decision_rows(Path(shard), ["nutrition", "injury_level", "agent_in_bush"], None, None,
                             next_cols=("ate_food",))
    nut = r["nutrition"].astype(np.float64); inj = r["injury_level"].astype(np.float64)
    bush = r["agent_in_bush"].astype(bool); ate = r["ate_food_next"].astype(bool)
    bi, bn = _bin(inj, INJ_EDGES), _bin(nut, nut_edges)
    ni, nn = len(INJ_EDGES) - 1, len(nut_edges) - 1
    out = {}
    split_n = {"fed": nut >= bands["fed"][0], "hungry": nut < bands["hungry"][1],
               "all": np.ones(nut.size, bool)}
    for s, m in split_n.items():
        out[f"cover|{s}"] = [np.bincount(bi[m], minlength=ni).tolist(),
                             np.bincount(bi[m & bush], minlength=ni).tolist()]
    split_i = {"low": (inj >= ranges["low"][0]) & (inj <= ranges["low"][1]),
               "high": (inj >= ranges["high"][0]) & (inj <= ranges["high"][1]),
               "all": np.ones(nut.size, bool)}
    for s, m in split_i.items():
        out[f"eat|{s}"] = [np.bincount(bn[m], minlength=nn).tolist(),
                           np.bincount(bn[m & ate], minlength=nn).tolist()]
    return out


def run_counts(d, man, workers):
    lay = C.store_layout(d)
    nut_edges = np.arange(0, lay["max_nutrition"] + 1e-9, 10.0)
    if nut_edges[-1] < lay["max_nutrition"]:
        nut_edges = np.append(nut_edges, lay["max_nutrition"])
    fn = partial(_shard, nut_edges=nut_edges, bands=man["nutrition_bands"], ranges=man["injury_ranges"])
    parts = C.parallel_map(fn, [str(s) for s in C.shard_files(d)], workers)
    tot = {}
    for p in parts:
        for k, (n, kk) in p.items():
            if k in tot:
                tot[k] = [np.add(tot[k][0], n).tolist(), np.add(tot[k][1], kk).tolist()]
            else:
                tot[k] = [n, kk]
    return {"store": str(d.relative_to(C.ROOT)), "ckpt_step": lay["ckpt_step"], "shards": len(parts),
            "injury_edges": INJ_EDGES.tolist(), "nutrition_edges": nut_edges.tolist(), "counts": tot}


def table(c):
    out = {}
    for k, (n, kk) in c["counts"].items():
        out[k] = [{"n": int(a), "k": int(b), "share": (b / a if a >= MIN_N else None)} for a, b in zip(n, kk)]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest"); ap.add_argument("out"); ap.add_argument("--workers", type=int, default=12)
    a = ap.parse_args()
    man = C.load_manifest(a.manifest)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    allr = {}
    for run in man["_runs"]:
        st = C.select_stores(man, run, pooled=False)
        cp = out / f"dose_{run['label']}.json"
        if cp.exists():
            c = json.loads(cp.read_text())
        elif st:
            print(f"[dose] {run['label']}", flush=True)
            c = run_counts(st[0][1], man, a.workers)
            C.write_json(cp, c)
        else:
            print(f"[dose] {run['label']}: no complete store", flush=True)
            continue
        allr[run["label"]] = {"world": run["world"], "agent": run["agent"], "store": c["store"],
                              "ckpt_step": c["ckpt_step"], "injury_edges": c["injury_edges"],
                              "nutrition_edges": c["nutrition_edges"], "tables": table(c)}
    C.write_json(out / "dose_tables.json", {
        "note": "cover|<fed,hungry,all>: share of decision steps in a bush by TRUE-injury bin; "
                "eat|<low,high,all>: share of decisions that ate by nutrition bin, split by true injury "
                "(low 0-20, high 60-100). share null when n < 200. Final-checkpoint stores, 1M episodes.",
        "fed": man["nutrition_bands"]["fed"], "hungry": man["nutrition_bands"]["hungry"],
        "injury_ranges": man["injury_ranges"], "min_n": MIN_N, "runs": allr})
    print(f"[dose] wrote {out / 'dose_tables.json'} ({len(allr)} runs)")


if __name__ == "__main__":
    main()
