#!/usr/bin/env python3
"""state_contrasts.py -- measures 1 and 3 of the level-05 body-interactions design, per run and per world.

Plain language: does the agent's "hide when hurt" habit depend on how hungry it is (measure 1), and
does its "eat" habit depend on how hurt it is (measure 3)? Both are fixed 2x2 contrasts over body
states, computed on the trajectory stores, first against TRUE injury and then against FELT injury
(the Interoceptive Nociception slot of obs_true, which is all the agent ever perceives).

Definitions (docs/experiments/active/level05_body_interactions/LEVEL05_BODY_INTERACTIONS.md §4.1,
Revision 1; every band, range and threshold comes from the analysis manifest):
  cells      nutrition band {hungry, fed} x injury range {low, high}, over DECISION rows (the states
             the policy acted from, t = 0..T-1; see _common.py)
  B(b, r)    share of the cell's steps with agent_in_bush at t
  E(b, r)    share of the cell's steps whose action ate (ate_food on row t+1)
  M1 = [B(fed,high) - B(fed,low)] - [B(hungry,high) - B(hungry,low)]
  M3 = [E(hungry,high) - E(hungry,low)] - [E(fed,high) - E(fed,low)]
  computable iff all four cells hold >= min_steps_per_cell steps. If a world's final checkpoint is
  short for EITHER agent, both agents are pooled over the newest `late_window_checkpoints` stores;
  if those stores do not exist or are still short, the world is "not computable" for that injury
  axis (true / felt separately).
  felt ranges: low = felt <= q_lo, high = felt >= q_hi, with q_lo / q_hi the manifest quantiles of
  felt injury over the reference run's final-checkpoint decision rows, FROZEN by `--freeze` before
  any other run is read (the frozen file is refused as input if its reference label is not the
  manifest's).
  Also reported per run (measure 2 context, from the store): mean episode length (survival steps)
  and termination shares.  The pre-registered survival read-out (WandB) is in factorial_effects.py.

Outputs (manifest `out_dir`): frozen_felt_injury.json (by --freeze), state_contrasts.json (per run
and per world), state_contrasts_worlds.csv; per-store results are cached under cache/ so re-runs
only read new stores.

Usage:
  PY=/home/vncuser/miniconda3/envs/grid_world_pain/bin/python
  $PY scripts/analysis/studies/level05_body_interactions/state_contrasts.py MANIFEST --freeze
  $PY scripts/analysis/studies/level05_body_interactions/state_contrasts.py MANIFEST [--workers 8]
  --max-shards N reads only the first N shards of each store (tooling tests; output stamped PARTIAL,
  written to *_PARTIAL files, cache not used).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime
from functools import partial
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common as C  # noqa: E402

BANDS = ("hungry", "fed")
RANGES = ("low", "high")
TERM = {1: "time_limit", 2: "starvation", 3: "overeating", 4: "injury", 5: "thermal"}


# ------------------------------------------------------------------------------- per shard --
def _shard_felt(shard, D, felt_i):
    r = C.read_decision_rows(Path(shard), [], [felt_i], D)
    return r[f"obs_{felt_i}"].astype(np.float32)


def _in(x, lo, hi, inclusive_hi):
    return (x >= lo) & ((x <= hi) if inclusive_hi else (x < hi))


def _shard_counts(shard, D, felt_i, bands, ranges, felt_cut):
    r = C.read_decision_rows(Path(shard), ["nutrition", "injury_level", "agent_in_bush"],
                             [felt_i], D, next_cols=("ate_food",))
    nut, inj = r["nutrition"].astype(np.float64), r["injury_level"].astype(np.float64)
    felt = r[f"obs_{felt_i}"]
    bush, ate = r["agent_in_bush"].astype(bool), r["ate_food_next"].astype(bool)
    band_m = {b: _in(nut, bands[b][0], bands[b][1], False) for b in BANDS}
    axes = {"true": {g: _in(inj, ranges[g][0], ranges[g][1], True) for g in RANGES},
            "felt": {"low": felt <= felt_cut[0], "high": felt >= felt_cut[1]}}
    out = {"decision_rows": int(nut.size)}
    for ax, rm in axes.items():
        for b in BANDS:
            for g in RANGES:
                m = band_m[b] & rm[g]
                out[f"{ax}|{b}|{g}"] = [int(m.sum()), int((m & bush).sum()), int((m & ate).sum())]
    return out


def _episode_stats(store_dir: Path, max_shards):
    import pyarrow.parquet as pq
    fs = C.shard_files(store_dir, max_shards, prefix="episodes")
    L, R = [], []
    for f in fs:
        t = pq.read_table(f, columns=["length", "termination_reason"])
        L.append(t.column("length").to_numpy()); R.append(t.column("termination_reason").to_numpy())
    L, R = np.concatenate(L), np.concatenate(R)
    shares = {name: float((R == code).mean()) for code, name in TERM.items()}
    unknown = float((~np.isin(R, list(TERM))).mean())
    if unknown:
        shares["unknown_code"] = unknown
    return {"episodes": int(L.size), "mean_length": float(L.mean()),
            "sd_length": float(L.std(ddof=1)) if L.size > 1 else float("nan"),
            "termination_shares": shares}


def store_counts(store_dir: Path, man, felt_cut, workers, max_shards):
    lay = C.store_layout(store_dir)
    felt_i = C.slot_index(lay, man["felt_injury_slot"])
    fn = partial(_shard_counts, D=lay["D"], felt_i=felt_i, bands=man["nutrition_bands"],
                 ranges=man["injury_ranges"], felt_cut=felt_cut)
    parts = C.parallel_map(fn, [str(s) for s in C.shard_files(store_dir, max_shards)], workers)
    tot = {}
    for p in parts:
        for k, v in p.items():
            tot[k] = (np.add(tot[k], v).tolist() if isinstance(v, list) else tot.get(k, 0) + v) \
                if k in tot else v
    return {"store": str(store_dir.relative_to(C.ROOT)), "ckpt_step": lay["ckpt_step"],
            "shards_read": len(parts), "cells": tot, "survival_store": _episode_stats(store_dir, max_shards)}


# ------------------------------------------------------------------------------- contrasts --
def contrasts(cells_list, axis, min_n):
    """Sum cell counts over one or more stores; return M1, M3, per-cell n / B / E, computable."""
    cell = {}
    for b in BANDS:
        for g in RANGES:
            n = sum(c[f"{axis}|{b}|{g}"][0] for c in cells_list)
            nb = sum(c[f"{axis}|{b}|{g}"][1] for c in cells_list)
            ne = sum(c[f"{axis}|{b}|{g}"][2] for c in cells_list)
            cell[f"{b}|{g}"] = {"n": n, "B": nb / n if n else float("nan"),
                                "E": ne / n if n else float("nan")}
    ok = all(v["n"] >= min_n for v in cell.values())
    B = {k: v["B"] for k, v in cell.items()}
    E = {k: v["E"] for k, v in cell.items()}
    m1 = (B["fed|high"] - B["fed|low"]) - (B["hungry|high"] - B["hungry|low"])
    m3 = (E["hungry|high"] - E["hungry|low"]) - (E["fed|high"] - E["fed|low"])
    return {"computable": ok, "M1": m1 if ok else None, "M3": m3 if ok else None,
            "M1_raw": m1, "M3_raw": m3, "cells": cell}


# ------------------------------------------------------------------------------------ main --
def freeze(man, workers, force, max_shards=None, ref_override=None):
    ref_label = ref_override or man["reference_label"]
    ref = [r for r in man["_runs"] if r["label"] == ref_label]
    if len(ref) != 1:
        raise ValueError(f"reference label {ref_label!r} matches {len(ref)} runs")
    st = C.select_stores(man, ref[0], pooled=False)
    if not st:
        raise RuntimeError(f"{ref[0]['label']}: no complete final-checkpoint store yet; cannot freeze")
    path = C.out_dir(man) / ("frozen_felt_injury_PARTIAL.json" if max_shards else "frozen_felt_injury.json")
    if path.exists() and not force and not max_shards:
        raise RuntimeError(f"{path} exists: cut-points are frozen. --force-refreeze overwrites "
                           "(and must be reported as a post-hoc change).")
    step, d = st[0]
    lay = C.store_layout(d)
    felt_i = C.slot_index(lay, man["felt_injury_slot"])
    vals = np.concatenate(C.parallel_map(partial(_shard_felt, D=lay["D"], felt_i=felt_i),
                                         [str(s) for s in C.shard_files(d, max_shards)], workers))
    qlo, qhi = man["felt_injury_quantiles"]
    lo, hi = (float(x) for x in np.quantile(vals, [qlo, qhi]))
    rec = {"reference_label": ref[0]["label"], "store": str(d.relative_to(C.ROOT)), "ckpt_step": step,
           "slot": man["felt_injury_slot"], "quantiles": [qlo, qhi], "cut_low_le": lo,
           "cut_high_ge": hi, "decision_rows": int(vals.size),
           "share_low": float((vals <= lo).mean()), "share_high": float((vals >= hi).mean()),
           "felt_min": float(vals.min()), "felt_max": float(vals.max()),
           "share_exact_zero": float((vals == 0).mean()),
           "frozen_at": datetime.now().isoformat(timespec="seconds"),
           "refrozen": bool(path.exists()), "partial_max_shards": max_shards}
    C.write_json(path, rec)
    print(json.dumps(rec, indent=1))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("manifest")
    ap.add_argument("--freeze", action="store_true", help="freeze felt-injury cut-points and exit")
    ap.add_argument("--force-refreeze", action="store_true")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--max-shards", type=int, default=None,
                    help="tooling tests only: first N shards per store, incomplete stores accepted, "
                         "outputs *_PARTIAL")
    ap.add_argument("--reference-override", default=None,
                    help="tooling tests only (with --freeze --max-shards): freeze from another run")
    a = ap.parse_args(argv)
    if a.reference_override and not a.max_shards:
        raise ValueError("--reference-override is for tooling tests only; it requires --max-shards")
    man = C.load_manifest(a.manifest)
    C.ALLOW_INCOMPLETE = a.max_shards is not None
    if a.freeze:
        return freeze(man, a.workers, a.force_refreeze, a.max_shards, a.reference_override)

    od = C.out_dir(man)
    fz_path = od / ("frozen_felt_injury_PARTIAL.json" if a.max_shards else "frozen_felt_injury.json")
    if not fz_path.exists():
        raise RuntimeError(f"{fz_path} missing: run with --freeze first (on the reference run).")
    fz = json.loads(fz_path.read_text())
    if not a.max_shards and fz["reference_label"] != man["reference_label"]:
        raise ValueError(f"{fz_path} was frozen from {fz['reference_label']!r}, manifest reference is "
                         f"{man['reference_label']!r}")
    felt_cut = (fz["cut_low_le"], fz["cut_high_ge"])
    key = hashlib.sha1(json.dumps([man["nutrition_bands"], man["injury_ranges"], felt_cut],
                                  sort_keys=True).encode()).hexdigest()[:10]
    partial_run = a.max_shards is not None
    cache = od / "cache" / "state_contrasts"
    cache.mkdir(parents=True, exist_ok=True)

    def counts_for(d: Path):
        cp = cache / f"{d.parts[-3]}_{d.parts[-2]}_{key}.json"
        if cp.exists() and not partial_run:
            return json.loads(cp.read_text())
        res = store_counts(d, man, felt_cut, a.workers, a.max_shards)
        if not partial_run:
            C.write_json(cp, res)
        return res

    min_n = int(man["min_steps_per_cell"])
    runs_out, by_world = {}, {}
    for run in man["_runs"]:
        st = C.select_stores(man, run, pooled=False)
        rec = {"world": run["world"], "agent": run["agent"], "run": run["run_name"],
               "final": None, "pooled": None}
        if st:
            print(f"[state_contrasts] {run['label']}: {st[0][1]}", flush=True)
            c = counts_for(st[0][1])
            rec["final"] = {"store": c["store"], "ckpt_step": c["ckpt_step"],
                            "shards_read": c["shards_read"], "survival_store": c["survival_store"],
                            "true": contrasts([c["cells"]], "true", min_n),
                            "felt": contrasts([c["cells"]], "felt", min_n)}
        else:
            print(f"[state_contrasts] {run['label']}: no complete final store yet", flush=True)
        runs_out[run["label"]] = rec
        by_world.setdefault(run["world"], {})[run["agent"]] = run

    hi, lo = man["difference"]
    worlds = {}
    for w, ag in sorted(by_world.items()):
        row = {"world": w}
        recs = {k: runs_out[f"{w}_{k}"] for k in ag}
        if any(recs[k]["final"] is None for k in (hi, lo)):
            row["status"] = "missing store"
            worlds[w] = row
            continue
        for axis in ("true", "felt"):
            basis = "final"
            res = {k: recs[k]["final"][axis] for k in (hi, lo)}
            if not all(res[k]["computable"] for k in (hi, lo)):
                basis = "pooled late window"
                pooled = {}
                for k in (hi, lo):
                    run = ag[k]
                    st = C.select_stores(man, run, pooled=True)
                    if not st:
                        pooled = None
                        break
                    cl = [counts_for(d)["cells"] for _, d in st]
                    pooled[k] = contrasts(cl, axis, min_n)
                    recs[k]["pooled"] = recs[k]["pooled"] or {}
                    recs[k]["pooled"][axis] = pooled[k] | {"ckpts": [s for s, _ in st]}
                if pooled is None or not all(pooled[k]["computable"] for k in (hi, lo)):
                    basis = "not computable" + (" (late-window stores not collected)" if pooled is None else "")
                    res = None
                else:
                    res = pooled
            row[f"{axis}_basis"] = basis
            for m in ("M1", "M3"):
                for k in (hi, lo):
                    row[f"{m}_{axis}_{k}"] = res[k][m] if res else None
                row[f"D_{m}_{axis}"] = (res[hi][m] - res[lo][m]) if res else None
        for k in (hi, lo):
            row[f"survival_store_{k}"] = recs[k]["final"]["survival_store"]["mean_length"]
        row["status"] = "ok"
        worlds[w] = row

    out = {"generated": datetime.now().isoformat(timespec="seconds"), "manifest": a.manifest,
           "partial": partial_run, "max_shards": a.max_shards, "frozen_felt_injury": fz,
           "difference": f"{hi} - {lo}", "runs": runs_out, "worlds": worlds}
    suffix = "_PARTIAL" if partial_run else ""
    C.write_json(od / f"state_contrasts{suffix}.json", out)
    cols = sorted({k for r in worlds.values() for k in r}, key=lambda k: (k != "world", k))
    with open(od / f"state_contrasts_worlds{suffix}.csv", "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=cols)
        wr.writeheader()
        for r in worlds.values():
            wr.writerow(r)
    print(f"[state_contrasts] wrote {od / f'state_contrasts{suffix}.json'}"
          f"{'  (PARTIAL: first %d shards per store)' % a.max_shards if partial_run else ''}")


if __name__ == "__main__":
    sys.exit(main())
