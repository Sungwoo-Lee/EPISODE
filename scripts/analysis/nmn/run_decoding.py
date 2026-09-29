"""Driver: A2 decoding profiles — how well each layer reads out hunger, injury, predator distance
and remaining survival time, against a clock-only baseline.

Plain-language purpose: for each agent, verdict layer and quantity, a ridge read-out is
fitted on training episodes and scored (held-out R^2) on episodes it never saw. Beside every
score sits the "clock": the best prediction of the quantity from the time step alone (its
per-time-step mean on the training episodes). A layer only counts as encoding a quantity
when it beats the clock, so a layer that merely tracks elapsed time does not look informative
about remaining survival time. Remaining survival time is scored, as its headline, on episodes
that ended in death only (a truncated episode's remaining time is censored and is a pure
clock); the all-episode variant is reported beside it and decides nothing. Predator distance
is scored on rows with an active predator. Every score carries a bootstrap interval over
resampled episode groups, joint across agents.

Controls (gate G4's inputs): satiation read from the raw input (a positive control:
satiation is an observed channel), and every quantity shuffled across episodes (a negative
control). The untrained networks and the raw input are reported as reference rows.

Where the manifest's evidence status allows verdict words, gate G5 (from each run's WandB log)
is applied first and the statistics go to decision_rules.evaluate_A2; where it allows none
(the pilot), no decision or gate function is called and the outputs carry numbers and the
rules' label only (driver_io.guard_no_verdict_words refuses an output with a verdict word).

Outputs, beside the run_activations output of the same manifest: decoding.json (stamped with
the rules sha256 and commit, the git sha and the evidence status, with a data statement) and
decoding.csv. Every size comes from the pinned rules' `parameters:` or the manifest; each
ridge fit's chosen penalty and grid-edge flag is kept.

Usage:
  /home/vncuser/miniconda3/envs/grid_world_pain/bin/python scripts/analysis/nmn/run_decoding.py \\
      --manifest docs/experiments/active/modulator_clues/algorithmic_null_pilot.yaml

Plan: docs/develop/active/neuromodulation/ALGORITHMIC_NULL_ANALYSIS_TOOLING.md, File Changes §8,
§A2 decoding.
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

SENSITIVITY = "steps_remaining_all"       # decides nothing; reported beside the headline
INPUT = "raw_input"                      # the reference row: symlog of the observation


def clock_parts(probe, splits, boots, quantity):
    """Per split repeat: the quantity's train and held-out rows, the clock (per-time-step
    training-fold mean) and its held-out predictions on the rows that have a clock value, the
    dropped-row count, the held-out group count after exclusions (gate G6) and the draw
    counts. Shared by every agent (it depends only on the probe)."""
    from scripts.analysis.nmn import draw_stats as ds
    from scripts.analysis.nmn import driver_io as dio
    from scripts.analysis.nmn import representation as rep
    rows_q = dio.quantity_rows(probe, quantity)
    y = dio.target(probe, quantity)
    t = probe.row_t
    groups = probe.row_seed
    parts = []
    for s, pos in zip(splits, boots):
        tr = np.intersect1d(s.train, rows_q)
        te = np.intersect1d(s.test, rows_q)
        means = rep.clock_baseline(t, y, tr)
        kept = rep.clock_mask(means, t, te)
        pc, _ = rep.clock_predict(means, t[kept])
        counts = ds.counts_from_positions(pos, len(s.test_groups))
        rg = ds.row_positions(groups[kept], s.test_groups)
        parts.append({"train": tr, "test": kept, "dropped_no_clock": int(te.size - kept.size),
                      "clock_r2": rep.clock_r2(means, t, y, kept),
                      "clock_draws": ds.r2_draws(y[kept], pc, rg, counts),
                      "test_groups": int(np.unique(groups[kept]).size),
                      "counts": counts, "rg": rg})
    return {"rows": rows_q, "y": y, "parts": parts}


def score_layer(X, cp, groups, rs, fits, where, P) -> dict:
    """R^2 of a ridge read-out of the quantity from X, per repeat (map fitted once on the
    training fold), the clock's R^2 on the same held-out rows, the excess, and their pooled
    bootstrap draws."""
    from scripts.analysis.nmn import draw_stats as ds
    from scripts.analysis.nmn import representation as rep
    from scripts.analysis.nmn.run_similarity import _q
    y = cp["y"]
    pts, clk, r2d, exd, fit = [], [], [], [], []
    for i, p in enumerate(cp["parts"]):
        m = rep.fit_ridge(X[p["train"]], y[p["train"]], groups[p["train"]], alphas=rs["alphas"],
                          inner_folds=rs["inner_folds"])
        fit += fits.add(where, [m], first=i)
        pr = m.predict(X[p["test"]])[:, 0]
        pts.append(rep.r2_weighted(y[p["test"]], pr))
        clk.append(p["clock_r2"])
        d = ds.r2_draws(y[p["test"]], pr, p["rg"], p["counts"])
        r2d.append(d)
        exd.append(d - p["clock_draws"])
    r2d, exd = np.concatenate(r2d), np.concatenate(exd)
    lo, hi, n1 = _q(r2d, P)
    elo, ehi, n2 = _q(exd, P)
    return {"r2": float(np.mean(pts)), "r2_per_repeat": [float(v) for v in pts],
            "r2_q": [lo, hi], "clock_r2": float(np.mean(clk)),
            "excess": float(np.mean(np.asarray(pts) - np.asarray(clk))),
            "excess_q_lo": elo, "excess_q_hi": ehi, "nonfinite_draws": n1 + n2, "fits": fit}


def analyse_cell(caps, man, P, cell, agents, verdict_layers, quantities, log=print) -> dict:
    """Every A2 statistic of one cell. Pure statistics: no rule."""
    from scripts.analysis.nmn import driver_io as dio
    from scripts.analysis.nmn import representation as rep
    from scripts.analysis.nmn.run_similarity import _Fits
    sel, pid = cell
    probe = caps.probes[pid]
    groups = probe.row_seed
    rs = rep.ridge_settings(man)
    splits = dio.make_splits(groups, P, int(man["probe_split"]["seed"]))
    boots = rep.joint_group_bootstrap(groups, splits, int(man["bootstrap_n"]),
                                      int(man["probe_split"]["bootstrap_seed"]))
    fits = _Fits()
    n = int(groups.size)
    out = {"checkpoint": sel, "probe": pid, "agents": agents, "quantities": {},
           "g4_controls": dio.g4_controls(probe, splits, man, quantities)}
    xin = dio.symlog(probe.obs_all[probe.rows])
    cps = {}
    for q in list(quantities) + [SENSITIVITY]:
        cp = cps[q] = clock_parts(probe, splits, boots, q)
        out["quantities"][q] = {
            "rows_used": int(cp["rows"].size), "rows_available": n,
            "rows_dropped_no_clock_per_repeat": [p["dropped_no_clock"] for p in cp["parts"]],
            "held_out_groups_per_repeat": [p["test_groups"] for p in cp["parts"]],
            "clock_r2": float(np.mean([p["clock_r2"] for p in cp["parts"]])),
            "clock_r2_per_repeat": [float(p["clock_r2"]) for p in cp["parts"]],
            "reference": {INPUT: score_layer(xin, cp, groups, rs, fits, f"{q}/{INPUT}", P)},
            "agents": {name: {} for name in agents}}
    mrc = float(man["min_rows_per_column"])
    for name, a in agents.items():          # each layer is read once, then every quantity
        for key in verdict_layers:
            t0 = time.time()
            X = caps.layer(a["label"], a["selector"], pid, key)
            for q, cp in cps.items():
                if cp["rows"].size < mrc * X.shape[1]:
                    out["quantities"][q]["agents"][name][key] = {
                        "refused": f"{cp['rows'].size} rows < min_rows_per_column {mrc} x "
                                   f"{X.shape[1]} columns"}
                    continue
                out["quantities"][q]["agents"][name][key] = score_layer(
                    X, cp, groups, rs, fits, f"{sel}/{pid}/{q}/{name}/{key}", P)
            log(f"  [{sel} / {pid}] {name} {key}: {time.time() - t0:.0f}s")
    out["ridge_fits"] = {"n": fits.n, "at_grid_edge": fits.edge,
                         "grid": {"n_values": len(rs["alphas"]), "lowest": rs["alphas"][0],
                                  "highest": rs["alphas"][-1]},
                         "inner_folds": rs["inner_folds"]}
    return out


def evaluate(cell_res, P, policy, verdict_layers, quantities, gates, g5, bootstrap_n) -> dict:
    """A2 at the primary cell, through decision_rules only (verdict statuses)."""
    from scripts.analysis.nmn import decision_rules as dr
    g6 = dr.gate_G6({"bootstrap_n": bootstrap_n, "test_groups": {
        q: cell_res["quantities"][q]["held_out_groups_per_repeat"] for q in quantities}}, P)
    gates = {**gates, "G6": bool(g6["bootstrap_ok"])}
    trained = {n: a for n, a in cell_res["agents"].items() if not a["untrained"]}
    inputs = {}
    for q in quantities:
        qa = cell_res["quantities"][q]["agents"]
        inputs[q] = {"g6_pass": g6["per_key"][q], "layers": {
            key: {arm: [qa[n][key] for n, a in trained.items() if a["arm"] == arm]
                  for arm in ("ordinary", "modulated")} for key in verdict_layers}}
    a2 = dr.evaluate_A2(inputs, P, policy=policy, quantities=quantities,
                        verdict_layers=verdict_layers, gates=gates,
                        yardstick_complete=bool(g5["yardstick_complete"]))
    return {"A2": a2, "gate_G6": g6, "gates": gates}


def csv_rows(c) -> list[dict]:
    rows = []
    for q, qo in c["quantities"].items():
        entries = [(INPUT, "input", qo["reference"][INPUT])]
        entries += [(n, k, v) for n, lay in qo["agents"].items() for k, v in lay.items()]
        for name, key, v in entries:
            rows.append({"checkpoint": c["checkpoint"], "probe": c["probe"], "quantity": q,
                         "agent": name, "layer": key, "r2": v.get("r2"),
                         "r2_q_lo": (v.get("r2_q") or [None])[0],
                         "r2_q_hi": (v.get("r2_q") or [None, None])[1],
                         "clock_r2": v.get("clock_r2"), "excess": v.get("excess"),
                         "excess_q_lo": v.get("excess_q_lo")})
    return rows


def data_statement(stamp, man, c, P) -> dict:
    from scripts.analysis.nmn import decision_rules as dr
    s = dr.split_settings(P)
    rf = c["ridge_fits"]
    return {
        "rules": stamp["decision_rules"], "git_sha": stamp["git_sha"],
        "git_dirty": stamp["git_dirty"], "evidence_status": stamp["evidence_status"],
        "label": stamp["label"], "verdict_statement": stamp["verdict_statement"],
        "cell": f"{c['checkpoint']} / {c['probe']}",
        "rows_per_quantity": {q: {
            "used": qo["rows_used"], "available": qo["rows_available"],
            "percent": 100.0 * qo["rows_used"] / qo["rows_available"],
            "reason": {"nearest_predator_manhattan": "rows with an active predator only",
                       "steps_remaining": "episodes that ended in death only (truncated "
                                          "episodes' remaining time is censored); this biases "
                                          "the headline toward shorter lives",
                       SENSITIVITY: "all episodes; a sensitivity row that decides nothing"
                       }.get(q, "every kept row"),
            "held_out_rows_dropped_without_a_clock_value_per_repeat":
                qo["rows_dropped_no_clock_per_repeat"],
            "held_out_groups_per_repeat": qo["held_out_groups_per_repeat"]}
            for q, qo in c["quantities"].items()},
        "split": {**s, "seed": man["probe_split"]["seed"],
                  "grouping": "episode_seed; one split object shared by every agent"},
        "bootstrap": {"draws_per_repeat": int(man["bootstrap_n"]),
                      "pooled_draws": int(man["bootstrap_n"]) * s["n_repeats"],
                      "interval": list(dr.param(P, "common.bootstrap_interval")),
                      "seed": man["probe_split"]["bootstrap_seed"],
                      "unit": "episode_seed group, joint across all agents and quantities"},
        "ridge": {"fits": rf["n"], "fits_at_grid_edge": len(rf["at_grid_edge"]),
                  "at_grid_edge": rf["at_grid_edge"], "grid": rf["grid"],
                  "inner_folds": rf["inner_folds"]},
        "controls": {"input_satiation_r2": c["g4_controls"]["input_satiation_r2"],
                     "input_satiation_r2_min (gates.G4)":
                         dr.param(P, "gates.G4.input_satiation_r2_min"),
                     "shuffled_r2": c["g4_controls"]["shuffled_r2"],
                     "shuffled_r2_max (gates.G4)": dr.param(P, "gates.G4.shuffled_r2_max"),
                     "groups_in_both_folds": not c["g4_controls"]["groups_disjoint"]},
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--manifest", required=True)
    args = ap.parse_args(argv)
    os.environ.setdefault("JAX_PLATFORMS", "cpu")
    from scripts.analysis.nmn import driver_io as dio
    from scripts.analysis.nmn.run_similarity import agents_of_cell, _strip_draws

    man_path = dio._abs(args.manifest)
    man = dio.load_manifest(man_path)
    pinned, policy = dio.open_rules(man)
    P = pinned.parameters
    verdict_layers = list(pinned.rules["common"]["verdict_layers"])
    quantities = dio.quantities(pinned)
    stamp = dio.stamp(pinned, policy, man_path)
    print(f"[run_decoding] {man['name']}: {policy.status} — {policy.label or policy.prefix}; "
          f"{stamp['verdict_statement']}; rules {pinned.path} {pinned.sha256[:12]} @ "
          f"{(pinned.commit or 'uncommitted')[:8]}", flush=True)
    caps = dio.Captures(man, pinned)
    roles = caps.meta["roles"]
    cell = dio.primary_cell(pinned, policy.status, dio.cells(caps, man))

    surv = None
    entered = [r["label"] for r in man["runs"]]
    if policy.allowed:
        surv = dio.survival_block(dio.read_survival(man, roles), P, policy.status)
        entered = [l for a in ("ordinary", "modulated") for l in surv["gate_G5"]["entered"][a]]
    t0 = time.time()
    agents = agents_of_cell(caps, man, cell, entered, roles)
    c = analyse_cell(caps, man, P, cell, agents, verdict_layers, quantities)
    doc = {**stamp, "driver": "run_decoding", "analysis": "A2", "primary_cell": list(cell)}
    if policy.allowed:
        from scripts.analysis.nmn import decision_rules as dr
        reps = [caps.reports[(a["label"], a["selector"], cell[1])] for a in agents.values()]
        gates = {**{k: v for k, v in dio.capture_gates(reps, P).items()
                    if k != "generating_captures"}, "G4": dr.gate_G4(c["g4_controls"], P)}
        doc.update({"gate_G5": surv["gate_G5"], "survival_per_run": surv["per_run"],
                    "evaluation": evaluate(c, P, policy, verdict_layers, quantities, gates,
                                           surv["gate_G5"], int(man["bootstrap_n"]))})
    else:
        doc["evaluation"] = None
    doc["cell"] = c
    doc["data_statement"] = data_statement(stamp, man, c, P)
    doc["elapsed_s"] = round(time.time() - t0, 1)
    dio.write_outputs(caps.out, "decoding", _strip_draws(doc), csv_rows(c), policy)
    print(f"[run_decoding] wrote {caps.out / 'decoding.json'} ({doc['elapsed_s']}s)", flush=True)
    for q, qo in c["quantities"].items():
        print(f"  {q:28s} clock R2 {qo['clock_r2']:.4f}  input R2 "
              f"{qo['reference'][INPUT]['r2']:.4f}")
        for name, lay in qo["agents"].items():
            print("    " + name.ljust(32) + "  ".join(
                f"{k} {v['r2']:.3f}/{v['excess']:+.3f}" for k, v in lay.items() if "r2" in v))
    return 0


if __name__ == "__main__":
    sys.exit(main())
