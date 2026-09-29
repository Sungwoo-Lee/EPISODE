"""Driver: A1 layer similarity (linear CKA and cross-network linear predictivity) and A3's inputs.

Plain-language purpose: "do the ordinary and the modulated agent compute the same thing?"
For every pair of agents, and every verdict layer, it measures how alike the two agents'
activity is on identical stored inputs, in two ways: linear CKA (the page's stated measure),
and linear predictivity (how well a linear map from one agent's layer predicts the other's,
held out on episodes the map never saw; unlike CKA it is unchanged by the modulator's fixed
per-unit gain). Each number carries a bootstrap interval over resampled episode groups. The
pairs are sorted into the rules' pair sets (ordinary vs ordinary across seeds = the seed
yardstick; modulated vs ordinary at different and at the same seed; untrained networks).

Where the manifest's evidence status allows verdict words (rules evidence_status), it first
reads each run's survival and food bites from its own WandB log (gate G5, and the survival
difference A3 pattern c needs), drops runs that fail G5, checks the shared start (A3
precondition) on the untrained networks, and only then hands the statistics to
decision_rules.evaluate_A1 / evaluate_A3. Where the status allows none (the pilot), no decision
function is called and the outputs carry numbers and the rules' label only; a written output
containing a verdict word raises (driver_io.guard_no_verdict_words).

Inputs: the run_activations output of the same manifest. Outputs, in the same directory:
similarity.json (stamped with the rules sha256 and commit, the git sha and the evidence
status; with a data statement) and similarity.csv. Every size (split repeats, test fraction,
bootstrap interval) comes from the pinned rules' `parameters:`, and every tool setting (ridge
grid, inner folds, bootstrap_n, seeds, min_rows_per_column, self_similarity_atol) from the
manifest. Each ridge fit's chosen penalty and whether it sits at an end of the grid is kept.

Usage:
  /home/vncuser/miniconda3/envs/grid_world_pain/bin/python scripts/analysis/nmn/run_similarity.py \\
      --manifest docs/experiments/active/modulator_clues/algorithmic_null_pilot.yaml

Plan: docs/develop/active/neuromodulation/ALGORITHMIC_NULL_ANALYSIS_TOOLING.md, File Changes §8,
§E, §A1/A3/A4 statistics. (A4 is not built in this driver yet.)
"""
from __future__ import annotations

import argparse
import os
import sys
import time

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import numpy as np  # noqa: E402


def _log(*a):
    print(*a, flush=True)

DESCRIPTIVE_SITES = ("enc.uni", "enc", "rnn", "actor", "critic")


def _q(draws, P) -> tuple:
    """(lower, upper) bootstrap-interval quantiles (parameters.common.bootstrap_interval) of the
    finite draws, and the count of non-finite draws (reported, never dropped silently)."""
    from scripts.analysis.nmn import decision_rules as dr
    lo, hi = dr.param(P, "common.bootstrap_interval")
    d = np.asarray(draws, float)
    fin = d[np.isfinite(d)]
    if not fin.size:
        return None, None, int(d.size)
    q = np.quantile(fin, [float(lo), float(hi)])
    return float(q[0]), float(q[1]), int(d.size - fin.size)


def agents_of_cell(caps, man, cell, entered, roles) -> dict:
    """{name: {label, selector, arm, seed, untrained}} of the cell: every entered run at the
    cell's checkpoint, and the untrained network of every entered ordinary run."""
    sel, pid = cell
    out = {}
    for r in man["runs"]:
        lab = r["label"]
        if lab not in entered:
            continue
        ro = roles[lab]
        out[lab] = {"label": lab, "selector": sel, "arm": ro["arm"], "seed": ro["seed"],
                    "untrained": False}
        if ro["arm"] == "ordinary" and (lab, "untrained", pid) in caps.reports:
            out[f"untrained_{lab}"] = {"label": lab, "selector": "untrained", "arm": "ordinary",
                                       "seed": ro["seed"], "untrained": True}
    return out


class _Fits:
    """Records every ridge fit's chosen penalty and grid-edge flag for the data statement."""

    def __init__(self):
        self.n, self.edge = 0, []

    def add(self, where: str, maps, first: int = 0) -> list:
        """`maps` are the fits of split repeats first, first + 1, ..."""
        out = []
        for i, m in enumerate(maps, start=first):
            self.n += 1
            out.append({"alpha": m.alpha, "alpha_at_edge": m.alpha_at_edge})
            if m.alpha_at_edge:
                self.edge.append({"fit": f"{where} repeat {i}", "alpha": m.alpha,
                                  "edge": m.alpha_at_edge})
        return out


def predictivity(Xa, Xb, groups, splits, boots, rs, fits, where, *, with_draws=True) -> dict:
    """Both directions of held-out linear predictivity, maps fitted once per split repeat and
    held fixed; draws score each repeat's resampled held-out groups (joint across pairs)."""
    from scripts.analysis.nmn import draw_stats as ds
    from scripts.analysis.nmn import representation as rep
    res = {}
    for d, (X, Y) in (("ab", (Xa, Xb)), ("ba", (Xb, Xa))):
        maps = rep.fit_maps(X, Y, groups, splits, alphas=rs["alphas"], inner_folds=rs["inner_folds"])
        pts, draws = [], []
        for i, (s, m) in enumerate(zip(splits, maps)):
            P_ = m.predict(X[s.test])
            pts.append(rep.r2_weighted(Y[s.test], P_))
            if with_draws:
                c = ds.counts_from_positions(boots[i], len(s.test_groups))
                draws.append(ds.r2_draws(Y[s.test], P_, ds.row_positions(groups[s.test],
                                                                            s.test_groups), c))
        res[d] = {"per_repeat": [float(v) for v in pts], "mean": float(np.mean(pts)),
                  "fits": fits.add(f"{where} {d}", maps), "draws": draws}
    out = {"point": min(res["ab"]["mean"], res["ba"]["mean"]),
           "r2_ab": res["ab"]["mean"], "r2_ba": res["ba"]["mean"],
           "r2_ab_per_repeat": res["ab"]["per_repeat"], "r2_ba_per_repeat": res["ba"]["per_repeat"],
           "fits_ab": res["ab"]["fits"], "fits_ba": res["ba"]["fits"]}
    if with_draws:
        out["draws"] = np.concatenate([np.minimum(a, b) for a, b in
                                       zip(res["ab"]["draws"], res["ba"]["draws"])])
    return out


def analyse_cell(caps, man, P, cell, agents, verdict_layers, *, primary: bool,
                 headline: bool, log=_log) -> dict:
    """Every A1 statistic of one (checkpoint, probe) cell. Pure statistics: no rule."""
    from scripts.analysis.nmn import draw_stats as ds
    from scripts.analysis.nmn import driver_io as dio
    from scripts.analysis.nmn import representation as rep
    sel, pid = cell
    probe = caps.probes[pid]
    groups = probe.row_seed
    n_rows = int(groups.size)
    rs = rep.ridge_settings(man)
    B = int(man["bootstrap_n"])
    bseed = int(man["probe_split"]["bootstrap_seed"])
    atol = float(man["tool_checks"]["self_similarity_atol"])
    mrc = float(man["min_rows_per_column"])
    splits = dio.make_splits(groups, P, int(man["probe_split"]["seed"]))
    boots = rep.joint_group_bootstrap(groups, splits, B, bseed)
    ug, pos = rep.whole_probe_bootstrap(groups, B, bseed)
    cka_counts = ds.counts_from_positions(pos, len(ug))
    cka_rg = ds.row_positions(groups, ug)
    sets = dio.pair_sets(agents, man["comparisons"])
    fits = _Fits()
    out = {"checkpoint": sel, "probe": pid, "primary": primary, "headline": headline,
           "agents": agents, "pair_sets": {k: list(v) for k, v in sets.items()},
           "rows_used": n_rows, "rows_available": n_rows,
           "groups": int(np.unique(groups).size),
           "test_groups_per_repeat": dio.split_counts(splits, groups),
           "layers": {}, "self_similarity": {}, "refused_layers": {}}

    def X_of(name, key):
        a = agents[name]
        return caps.layer(a["label"], a["selector"], pid, key)

    for key in verdict_layers:
        t0 = time.time()
        X = {n: X_of(n, key) for n in agents}
        d = next(iter(X.values())).shape[1]
        if n_rows < mrc * d:
            out["refused_layers"][key] = f"{n_rows} rows < min_rows_per_column {mrc} x {d} columns"
            log(f"  [{sel} / {pid}] {key}: refused, {out['refused_layers'][key]}")
            continue
        fself = {n: ds.centred_frobenius(x, x, cka_rg, cka_counts) for n, x in X.items()}
        selfdev = {n: abs(rep.linear_cka(x, x) - 1.0) for n, x in X.items()}
        out["self_similarity"][key] = selfdev
        if max(selfdev.values()) > atol:
            raise RuntimeError(f"{cell} {key}: an agent's CKA with itself deviates from 1 by "
                               f"{max(selfdev.values()):.3e} > self_similarity_atol {atol}")
        lay = {"cka": {}, "predictivity": {}}
        for sname, pairs in sets.items():
            for pname, (a, b) in pairs.items():
                cd = ds.cka_draws(X[a], X[b], cka_rg, cka_counts, fself[a], fself[b])
                lo, hi, nan = _q(cd, P)
                lay["cka"][pname] = {"pair_set": sname, "point": rep.linear_cka(X[a], X[b]),
                                     "q_lo": lo, "q_hi": hi, "nonfinite_draws": nan, "draws": cd}
                pr = predictivity(X[a], X[b], groups, splits, boots, rs, fits,
                                  f"{sel}/{pid}/{key}/{pname}")
                lo, hi, nan = _q(pr["draws"], P)
                lay["predictivity"][pname] = {"pair_set": sname, **pr, "q_lo": lo, "q_hi": hi,
                                              "nonfinite_draws": nan}
        if primary:          # reference rows: raw input, and untrained vs trained (points only)
            ref = {}
            xin = dio.symlog(probe.obs_all[probe.rows])
            for n, x in X.items():
                ref[f"input|{n}"] = {"cka": rep.linear_cka(xin, x), **_pred_point(
                    xin, x, groups, splits, rs, fits, f"{sel}/{pid}/{key}/input|{n}")}
            for u in [n for n in agents if agents[n]["untrained"]]:
                for t in [n for n in agents if not agents[n]["untrained"]]:
                    ref[f"{u}|{t}"] = {"cka": rep.linear_cka(X[u], X[t]), **_pred_point(
                        X[u], X[t], groups, splits, rs, fits, f"{sel}/{pid}/{key}/{u}|{t}")}
            lay["reference"] = ref
        out["layers"][key] = lay
        log(f"  [{sel} / {pid}] {key}: {sum(len(v) for v in sets.values())} pairs, "
            f"{time.time() - t0:.0f}s")
    if headline:
        out["descriptive"] = descriptive(caps, agents, pid, sets, groups, splits, rs, fits,
                                         n_rows, mrc, log)
    out["ridge_fits"] = {"n": fits.n, "at_grid_edge": fits.edge,
                         "grid": {"n_values": len(rs["alphas"]), "lowest": rs["alphas"][0],
                                  "highest": rs["alphas"][-1]},
                         "inner_folds": rs["inner_folds"]}
    return out


def _pred_point(Xa, Xb, groups, splits, rs, fits, where) -> dict:
    p = predictivity(Xa, Xb, groups, splits, None, rs, fits, where, with_draws=False)
    return {"predictivity": p["point"], "r2_ab": p["r2_ab"], "r2_ba": p["r2_ba"]}


def descriptive(caps, agents, pid, sets, groups, splits, rs, fits, n_rows, mrc, log) -> dict:
    """Rules common.descriptive_layers at the headline capture (points only, never
    verdict-bearing): for every trained pair, X.raw with X.raw, X.mod with X.mod and
    enc.uni.out with enc.uni.out where both have the key, and for ordinary vs modulated pairs
    ordinary X.raw with modulated X.mod (after the gain and offset)."""
    from scripts.analysis.nmn import representation as rep
    out = {}
    trained = [(p, ab) for s, v in sets.items() if s != "UNTRAINED" for p, ab in v.items()]
    for pname, (a, b) in trained:
        A, B = agents[a], agents[b]
        ka = caps.keys(A["label"], A["selector"], pid)
        kb = caps.keys(B["label"], B["selector"], pid)
        combos = []
        for site in DESCRIPTIVE_SITES:
            for stage in ("raw", "mod"):
                k = f"{site}.{stage}"
                if k in ka and k in kb:
                    combos.append((k, k))
            if A["arm"] != B["arm"] and f"{site}.raw" in ka and f"{site}.mod" in kb:
                combos.append((f"{site}.raw", f"{site}.mod"))
        if "enc.uni.out" in ka and "enc.uni.out" in kb:
            combos.append(("enc.uni.out", "enc.uni.out"))
        for ka_, kb_ in combos:
            Xa = caps.layer(A["label"], A["selector"], pid, ka_)
            Xb = caps.layer(B["label"], B["selector"], pid, kb_)
            name = f"{pname} {ka_}~{kb_}"
            if n_rows < mrc * max(Xa.shape[1], Xb.shape[1]):
                out[name] = {"refused": f"{n_rows} rows < min_rows_per_column {mrc} x "
                                        f"{max(Xa.shape[1], Xb.shape[1])} columns"}
                continue
            t0 = time.time()
            out[name] = {"cka": rep.linear_cka(Xa, Xb),
                         **_pred_point(Xa, Xb, groups, splits, rs, fits, name)}
            log(f"  descriptive {name}: {time.time() - t0:.0f}s")
    return out


def evaluate(cell_res, P, policy, verdict_layers, gates, g5, survival, start) -> dict:
    """A1 and A3 at the primary cell, through decision_rules only (verdict statuses)."""
    from scripts.analysis.nmn import decision_rules as dr
    yard = bool(g5["yardstick_complete"])
    gw = [k for k, v in gates.items() if not v]
    inputs, summ = {}, {}
    for key in verdict_layers:
        lay = cell_res["layers"][key]
        if yard and not gw:
            s = {}
            for stat in ("predictivity", "cka"):
                pairs = {}
                for pname, v in lay[stat].items():
                    pairs.setdefault(v["pair_set"], {})[pname] = {"point": v["point"],
                                                                  "draws": v["draws"]}
                s[stat] = dr.summarise_pairs(pairs, P)
            summ[key] = s
            inputs[key] = s
        else:
            inputs[key] = {}
    a1 = dr.evaluate_A1(inputs, P, policy=policy, verdict_layers=verdict_layers, gates=gates,
                        yardstick_complete=yard)
    a3_in = {}
    for key in verdict_layers:
        if key in summ:
            p = summ[key]["predictivity"]
            a3_in[key] = {"a1_verdict": a1["layer_words"][key], "mo_same": p["mo_same"],
                          "mo_diff": p["mo_diff"], "U": p["band"][1],
                          "mo_same_mean_q_lo": p["mo_same_mean_q"][0],
                          "mo_diff_mean_q_hi": p["mo_diff_mean_q"][1]}
        else:
            a3_in[key] = {}
    a3 = dr.evaluate_A3(a3_in, P, policy=policy, verdict_layers=verdict_layers, gates=gates,
                        yardstick_complete=yard, precondition_shared_start=bool(start["holds"]),
                        survival=survival)
    return {"A1": a1, "A3": a3, "summaries": summ}


def _strip_draws(obj):
    if isinstance(obj, dict):
        return {k: _strip_draws(v) for k, v in obj.items() if k != "draws"}
    if isinstance(obj, list):
        return [_strip_draws(v) for v in obj]
    return obj


def csv_rows(cell_res) -> list[dict]:
    rows = []
    for c in cell_res:
        for key, lay in c["layers"].items():
            for stat in ("cka", "predictivity"):
                for pname, v in lay[stat].items():
                    rows.append({"checkpoint": c["checkpoint"], "probe": c["probe"],
                                 "layer": key, "statistic": stat, "pair_set": v["pair_set"],
                                 "pair": pname, "point": v["point"], "q_lo": v["q_lo"],
                                 "q_hi": v["q_hi"], "r2_ab": v.get("r2_ab"),
                                 "r2_ba": v.get("r2_ba")})
            for pname, v in lay.get("reference", {}).items():
                rows.append({"checkpoint": c["checkpoint"], "probe": c["probe"], "layer": key,
                             "statistic": "reference", "pair_set": "reference", "pair": pname,
                             "point": v["cka"], "q_lo": None, "q_hi": None,
                             "r2_ab": v["r2_ab"], "r2_ba": v["r2_ba"]})
    return rows


def data_statement(stamp, man, cells_res, P) -> dict:
    from scripts.analysis.nmn import decision_rules as dr
    s = dr.split_settings(P)
    fits = [c["ridge_fits"] for c in cells_res]
    return {
        "rules": stamp["decision_rules"], "git_sha": stamp["git_sha"],
        "git_dirty": stamp["git_dirty"], "evidence_status": stamp["evidence_status"],
        "label": stamp["label"], "verdict_statement": stamp["verdict_statement"],
        "rows": {f"{c['checkpoint']} / {c['probe']}": {
            "used": c["rows_used"], "available": c["rows_available"],
            "percent": 100.0 * c["rows_used"] / c["rows_available"],
            "distinct_episode_seed_groups": c["groups"],
            "held_out_groups_per_repeat": c["test_groups_per_repeat"],
            "refused_layers": c["refused_layers"]} for c in cells_res},
        "split": {**s, "seed": man["probe_split"]["seed"],
                  "grouping": "episode_seed; one split object shared by every agent and pair"},
        "bootstrap": {"draws_per_repeat": int(man["bootstrap_n"]),
                      "pooled_predictivity_draws": int(man["bootstrap_n"]) * s["n_repeats"],
                      "cka_draws": int(man["bootstrap_n"]),
                      "interval": list(dr.param(P, "common.bootstrap_interval")),
                      "seed": man["probe_split"]["bootstrap_seed"],
                      "unit": "episode_seed group, joint across all agents and pairs"},
        "ridge": {"fits": sum(f["n"] for f in fits),
                  "fits_at_grid_edge": sum(len(f["at_grid_edge"]) for f in fits),
                  "at_grid_edge": [e for f in fits for e in f["at_grid_edge"]],
                  "grid": fits[0]["grid"] if fits else None,
                  "inner_folds": fits[0]["inner_folds"] if fits else None},
        "statistics": "CKA: linear, feature-space, column-centred float64. Predictivity: "
                      "min(R2(A->B), R2(B->A)), each the mean over split repeats of held-out "
                      "variance-weighted R2; bootstrap draws pool the per-draw minimum over "
                      "the repeats.",
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--manifest", required=True)
    args = ap.parse_args(argv)
    os.environ.setdefault("JAX_PLATFORMS", "cpu")
    from scripts.analysis.nmn import decision_rules as dr
    from scripts.analysis.nmn import driver_io as dio

    man_path = dio._abs(args.manifest)
    man = dio.load_manifest(man_path)
    pinned, policy = dio.open_rules(man)
    P = pinned.parameters
    verdict_layers = list(pinned.rules["common"]["verdict_layers"])
    listed = [l["key"] for l in man["layers"]]
    miss = [k for k in verdict_layers if k not in listed]
    if miss:
        raise ValueError(f"manifest layers lack the rules' verdict layers {miss}")
    stamp = dio.stamp(pinned, policy, man_path)
    print(f"[run_similarity] {man['name']}: {policy.status} — {policy.label or policy.prefix}; "
          f"{stamp['verdict_statement']}; rules {pinned.path} {pinned.sha256[:12]} @ "
          f"{(pinned.commit or 'uncommitted')[:8]}", flush=True)
    caps = dio.Captures(man, pinned)
    roles = caps.meta["roles"]
    all_cells = dio.cells(caps, man)
    primary = dio.primary_cell(pinned, policy.status, all_cells)
    hc = man["headline_capture"]
    head = (str(hc["checkpoint"]), hc["probe"]) if hc else None

    surv = start = None
    entered = [r["label"] for r in man["runs"]]
    if policy.allowed:        # G5 exclusions come first (plan §A1/A3/A4 statistics)
        surv = dio.survival_block(dio.read_survival(man, roles), P, policy.status)
        entered = [l for a in ("ordinary", "modulated") for l in surv["gate_G5"]["entered"][a]]
        start = dio.shared_start(man, roles)
    t0 = time.time()
    cells_res = []
    for cell in all_cells:
        agents = agents_of_cell(caps, man, cell, entered, roles)
        cells_res.append(analyse_cell(caps, man, P, cell, agents, verdict_layers,
                                      primary=(cell == primary), headline=(cell == head)))
    doc = {**stamp, "driver": "run_similarity", "analysis": "A1 (and A3 inputs)",
           "primary_cell": list(primary), "not_built": "A4 (movement, drift, co-movement)"}
    if policy.allowed:
        pc = next(c for c in cells_res if c["primary"])
        reps = [caps.reports[(a["label"], a["selector"], primary[1])]
                for a in pc["agents"].values()]
        from scripts.analysis.nmn import representation as rep  # noqa: F401
        probe = caps.probes[primary[1]]
        splits = dio.make_splits(probe.row_seed, P, int(man["probe_split"]["seed"]))
        g4 = dio.g4_controls(probe, splits, man, dio.quantities(pinned))
        g6 = dr.gate_G6({"bootstrap_n": man["bootstrap_n"],
                         "test_groups": {"predictivity": pc["test_groups_per_repeat"]}}, P)
        gates = {**{k: v for k, v in dio.capture_gates(reps, P).items() if k != "generating_captures"},
                 "G4": dr.gate_G4(g4, P),
                 "G6": g6["bootstrap_ok"] and all(g6["per_key"].values())}
        doc.update({"survival": surv["survival"], "gate_G5": surv["gate_G5"],
                    "survival_per_run": surv["per_run"], "shared_start": start,
                    "gates": gates, "g4_controls": g4,
                    "evaluation": evaluate(pc, P, policy, verdict_layers, gates,
                                           surv["gate_G5"], surv["survival"], start)})
    else:
        doc["evaluation"] = None
    doc["cells"] = cells_res
    doc["data_statement"] = data_statement(stamp, man, cells_res, P)
    doc["elapsed_s"] = round(time.time() - t0, 1)
    dio.write_outputs(caps.out, "similarity", _strip_draws(doc), csv_rows(cells_res), policy)
    print(f"[run_similarity] wrote {caps.out / 'similarity.json'} ({doc['elapsed_s']}s)", flush=True)
    for c in cells_res:
        for key, lay in c["layers"].items():
            for stat in ("cka", "predictivity"):
                for pname, v in lay[stat].items():
                    print(f"  {c['checkpoint']:>12s} {c['probe']:>18s} {key:10s} {stat:12s} "
                          f"{pname:32s} {v['point']:.4f} [{v['q_lo']:.4f}, {v['q_hi']:.4f}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
