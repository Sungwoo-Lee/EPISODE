"""Driver: robustness columns beside A1 — descriptive, never a verdict.

Plain-language purpose: the A1 similarity verdict rests on one registered statistic (the
smaller of the two directions of held-out linear predictivity, variance-weighted over units).
Reviewers asked how much that number depends on choices the modulator could interact with.
This driver recomputes, under the registered split repeats and joint episode-group bootstrap
of the manifest, for every trained pair (ordinary-ordinary, modulated-modulated, modulated-
ordinary at different and at the same seed) and every verdict layer:

  1. each DIRECTION of predictivity separately. For a modulated-ordinary pair, modulated ->
     ordinary is the direction exactly unchanged by the modulator's per-unit gain;
  2. the fit with predictor units active on too few training rows left out (rules common.
     predictor_columns, revision P1: this is the registered estimator of the current rules,
     `admitted`), beside the estimator of the earlier rules that keeps every column
     (`all_columns`);
  3. every column kept, but the standardisation scale floored at the median unit SD of the
     training fold (`floored_scale`);
  4. the UNWEIGHTED mean of per-unit R^2 beside the variance-weighted R^2, for each fit.

Everything here is labelled "descriptive — not a registered statistic" and decides nothing; no
decision function is called. Per pair and layer it also reports the cross-agent row-lag control.
Outputs: similarity_robustness.{json,csv} beside the manifest's run_activations output (a file
computed under other rules is never overwritten; driver_io.write_outputs).

Usage:
  OMP_NUM_THREADS=4 python scripts/analysis/nmn/run_similarity_robustness.py \\
      --manifest docs/experiments/active/modulator_clues/algorithmic_null_mayrep_interim.yaml \\
      --workers 5

Plan: docs/develop/active/neuromodulation/ALGORITHMIC_NULL_ANALYSIS_TOOLING.md (review follow-up).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import numpy as np  # noqa: E402

LABEL = "descriptive — not a registered statistic"
VARIANTS = ("all_columns", "admitted", "floored_scale")
_STATE: dict = {}


def fit_floored(X, Y, groups, *, alphas, inner_folds):
    """fit_ridge with every column kept but each training-fold standardisation scale floored at
    the median unit SD of that fold (inner folds and refit alike). Descriptive variant only."""
    from sklearn.model_selection import GroupKFold
    from scripts.analysis.nmn import representation as rep

    def stdz(A):
        mu, sd = A.mean(axis=0), A.std(axis=0)
        sd = np.maximum(sd, np.median(sd))
        return mu, np.where(sd > 0, sd, 1.0)
    X = np.asarray(X, np.float64)
    Y = np.asarray(Y, np.float64)
    Y = Y[:, None] if Y.ndim == 1 else Y
    alphas = [float(a) for a in alphas]
    score = np.zeros(len(alphas))
    for k, (tr, va) in enumerate(GroupKFold(n_splits=inner_folds).split(X, groups=groups)):
        mu, sd = stdz(X[tr])
        ym = Y[tr].mean(axis=0)
        fold = rep._cv_scores((X[va] - mu) / sd, Y[va], ym,
                              rep._ridge_path((X[tr] - mu) / sd, Y[tr] - ym, alphas))
        if not np.all(np.isfinite(fold)):
            raise ValueError(f"fit_floored: inner fold {k} gives non-finite CV scores")
        score += fold
    best = int(np.argmax(score))
    mu, sd = stdz(X)
    ym = Y.mean(axis=0)
    coef = rep._ridge_path((X - mu) / sd, Y - ym, [alphas[best]])[0]
    edge = "lowest" if best == 0 else ("highest" if best == len(alphas) - 1 else None)
    return rep.RidgeMap(x_mean=mu, x_scale=sd, y_mean=ym, coef=coef, alpha=alphas[best],
                        alpha_at_edge=edge, n_columns=X.shape[1], n_dropped=0)


def _q(d, P):
    from scripts.analysis.nmn.run_similarity import _q as q
    lo, hi, bad = q(d, P)
    return {"q_lo": lo, "q_hi": hi, "nonfinite_draws": bad}


def layer_stats(key: str) -> dict:
    """Every variant and statistic for one verdict layer (run in a worker process)."""
    from scripts.analysis.nmn import draw_stats as ds
    from scripts.analysis.nmn import representation as rep
    st = _STATE
    caps, agents, pid, sets, splits, boots, rs, P = (st[k] for k in (
        "caps", "agents", "pid", "sets", "splits", "boots", "rs", "P"))
    groups = caps.probes[pid].row_seed
    fitters = {"all_columns": rep.fit_ridge, "admitted": rs["fitter"],
               "floored_scale": fit_floored}
    X = {n: caps.layer(agents[n]["label"], agents[n]["selector"], pid, key) for n in agents}
    counts = [ds.counts_from_positions(pos, len(s.test_groups)) for s, pos in zip(splits, boots)]
    rgs = [ds.row_positions(groups[s.test], s.test_groups) for s in splits]
    out, t0 = {}, time.time()
    for sname, pairs in sets.items():
        for pname, (a, b) in pairs.items():
            rec = {"pair_set": sname, "a": a, "b": b, "variants": {}}
            for v, fit in fitters.items():
                res = {}
                for d, (A, B) in (("a_to_b", (X[a], X[b])), ("b_to_a", (X[b], X[a]))):
                    pts, upts, dr_, udr, fits = [], [], [], [], []
                    for s, c, rg in zip(splits, counts, rgs):
                        m = fit(A[s.train], B[s.train], groups[s.train], alphas=rs["alphas"],
                                inner_folds=rs["inner_folds"])
                        Pr = m.predict(A[s.test])
                        pts.append(rep.r2_weighted(B[s.test], Pr))
                        one = np.ones((1, c.shape[1]))
                        upts.append(float(ds.r2_unit_mean_draws(B[s.test], Pr, rg, one)[0][0]))
                        dr_.append(ds.r2_draws(B[s.test], Pr, rg, c))
                        udr.append(ds.r2_unit_mean_draws(B[s.test], Pr, rg, c)[0])
                        fits.append({"alpha": m.alpha, "alpha_at_edge": m.alpha_at_edge,
                                     "n_columns": m.n_columns, "n_dropped": m.n_dropped})
                    res[d] = {"weighted": np.mean(pts), "unit_mean": np.mean(upts),
                              "wdraws": np.concatenate(dr_), "udraws": np.concatenate(udr),
                              "fits": fits}
                row = {}
                for stat, pk, dk in (("weighted", "weighted", "wdraws"),
                                     ("unit_mean", "unit_mean", "udraws")):
                    for d in ("a_to_b", "b_to_a"):
                        row[f"{stat}_{d}"] = {"point": float(res[d][pk]),
                                              **_q(res[d][dk], P)}
                    row[f"{stat}_mutual"] = {
                        "point": float(min(res["a_to_b"][pk], res["b_to_a"][pk])),
                        **_q(np.minimum(res["a_to_b"][dk], res["b_to_a"][dk]), P)}
                row["fits_a_to_b"], row["fits_b_to_a"] = res["a_to_b"]["fits"], res["b_to_a"]["fits"]
                rec["variants"][v] = row
            out[pname] = rec
    return {"layer": key, "pairs": out, "seconds": round(time.time() - t0, 1)}


def summarise(layer: dict) -> dict:
    """Per variant and statistic: the OO range (lowest lower / highest upper quantile, both
    directions for a direction statistic), and the points of every pair set; for MO pairs the
    modulated -> ordinary direction (pair names are ordinary|modulated, so b_to_a)."""
    out = {}
    pairs = layer["pairs"]
    for v in VARIANTS:
        for stat in ("weighted", "unit_mean"):
            key = f"{v}/{stat}"
            oo = [p["variants"][v] for p in pairs.values() if p["pair_set"] == "OO"]
            mut = f"{stat}_mutual"
            dirs = [r[f"{stat}_{d}"] for r in oo for d in ("a_to_b", "b_to_a")]
            ent = {"OO_mutual_range": [min(r[mut]["q_lo"] for r in oo), max(r[mut]["q_hi"] for r in oo)]
                   if oo and all(r[mut]["q_lo"] is not None for r in oo) else None,
                   "OO_direction_range": [min(x["q_lo"] for x in dirs), max(x["q_hi"] for x in dirs)]
                   if dirs and all(x["q_lo"] is not None for x in dirs) else None}
            for sname in ("OO", "MM", "MO_diff", "MO_same"):
                rows = [p["variants"][v] for p in pairs.values() if p["pair_set"] == sname]
                ent[f"{sname}_mutual_points"] = [round(r[mut]["point"], 6) for r in rows]
                if sname in ("MO_diff", "MO_same"):
                    ent[f"{sname}_modulated_to_ordinary_points"] = [
                        round(r[f"{stat}_b_to_a"]["point"], 6) for r in rows]
                    ent[f"{sname}_ordinary_to_modulated_points"] = [
                        round(r[f"{stat}_a_to_b"]["point"], 6) for r in rows]
                if sname == "MM":
                    ent["MM_direction_points"] = [round(r[f"{stat}_{d}"]["point"], 6)
                                                  for r in rows for d in ("a_to_b", "b_to_a")]
            out[key] = ent
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--workers", type=int, required=True,
                    help="worker processes, one verdict layer each (memory: ~5 GB per worker "
                         "on a May probe)")
    args = ap.parse_args(argv)
    os.environ.setdefault("JAX_PLATFORMS", "cpu")
    from concurrent.futures import ProcessPoolExecutor
    from scripts.analysis.nmn import driver_io as dio
    from scripts.analysis.nmn import representation as rep
    from scripts.analysis.nmn.run_similarity import agents_of_cell

    man_path = dio._abs(args.manifest)
    man = dio.load_manifest(man_path)
    pinned, policy = dio.open_rules(man)
    P = pinned.parameters
    verdict_layers = list(pinned.rules["common"]["verdict_layers"])
    stamp = dio.stamp(pinned, policy, man_path)
    caps = dio.Captures(man, pinned)
    stamp["captures_rules_sha256"] = caps.rules_sha
    roles = caps.meta["roles"]
    cell = dio.primary_cell(pinned, policy.status, dio.cells(caps, man))
    entered = [r["label"] for r in man["runs"]]
    g5 = None
    if policy.allowed:           # the same runs as the verdict (G5 exclusions first)
        g5 = dio.survival_block(dio.read_survival(man, roles), P, policy.status)["gate_G5"]
        entered = [l for a in ("ordinary", "modulated") for l in g5["entered"][a]]
    agents = {n: a for n, a in agents_of_cell(caps, man, cell, entered, roles).items()
              if not a["untrained"]}
    sets = {k: v for k, v in dio.pair_sets(agents, man["comparisons"]).items() if k != "UNTRAINED"}
    pid = cell[1]
    groups = caps.probes[pid].row_seed
    splits = dio.make_splits(groups, P, int(man["probe_split"]["seed"]))
    boots = rep.joint_group_bootstrap(groups, splits, int(man["bootstrap_n"]),
                                      int(man["probe_split"]["bootstrap_seed"]))
    lag = {pname: dio.row_lag_control(
        caps.layer(agents[a]["label"], agents[a]["selector"], pid, "logits"),
        caps.layer(agents[b]["label"], agents[b]["selector"], pid, "logits"),
        float(man["tool_checks"]["row_lag_min_gap"]), pname)
        for pairs in sets.values() for pname, (a, b) in pairs.items()}
    _STATE.update(caps=caps, agents=agents, pid=pid, sets=sets, splits=splits, boots=boots,
                  rs=dio.ridge(man, P), P=P)
    print(f"[robustness] {man['name']}: {LABEL}; cell {cell}; {sum(len(v) for v in sets.values())} "
          f"pairs x {len(verdict_layers)} layers x {len(VARIANTS)} variants", flush=True)
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        layers = list(ex.map(layer_stats, verdict_layers))
    for l in layers:
        print(f"  {l['layer']}: {l['seconds']}s", flush=True)
    doc = {**stamp, "driver": "run_similarity_robustness", "status_of_these_numbers": LABEL,
           "note": "recomputed under the pinned rules; reported beside, never in place of, the "
                   "registered interim verdict of the captures' rules",
           "cell": list(cell), "gate_G5": g5, "row_lag_control": lag,
           "variants": {"all_columns": "every predictor column (the estimator of the captures' "
                                        "rules)",
                        "admitted": "predictor columns admitted by rules common.predictor_columns "
                                    f"(min_active_fraction "
                                    f"{_STATE['rs']['min_active_fraction']})",
                        "floored_scale": "every column; standardisation scale floored at the "
                                         "median unit SD of the training fold"},
           "statistics": {"weighted": "held-out R2, variance-weighted over output units",
                          "unit_mean": "unweighted mean of per-unit held-out R2 (units constant "
                                       "on the held-out rows left out)",
                          "mutual": "the smaller of the two directions (per draw for the "
                                    "quantiles)"},
           "split_and_bootstrap": {"n_repeats": len(splits), "draws_per_repeat": int(man["bootstrap_n"]),
                                   "seeds": man["probe_split"]},
           "layers": {l["layer"]: {"summary": summarise(l), "pairs": l["pairs"]} for l in layers},
           "elapsed_s": round(time.time() - t0, 1)}
    rows = []
    for l in layers:
        for pname, rec in l["pairs"].items():
            for v, row in rec["variants"].items():
                for stat in ("weighted", "unit_mean"):
                    for d in ("a_to_b", "b_to_a", "mutual"):
                        x = row[f"{stat}_{d}"]
                        rows.append({"layer": l["layer"], "pair_set": rec["pair_set"], "pair": pname,
                                     "variant": v, "statistic": stat, "direction": d,
                                     "point": x["point"], "q_lo": x["q_lo"], "q_hi": x["q_hi"],
                                     "label": LABEL})
    dio.write_outputs(caps.out, "similarity_robustness", doc, rows, policy)
    print(f"[robustness] wrote {caps.out / 'similarity_robustness.json'} ({doc['elapsed_s']}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
