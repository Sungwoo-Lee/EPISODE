"""Driver: A4 — do the two agents' layers move together across worlds?

Plain-language purpose: the May replication alternates a hunting world and a harmless world.
Every agent was captured at the end of each stage, on both worlds' probes. For each agent and
verdict layer this driver measures how much the layer changes from one stage end to the next
("movement": one minus the A1 mutual predictivity between the agent at consecutive stage
ends, on each world's probe, 8 entries), how much it changes within one stage anyway
("within-stage drift", from the checkpoint just before a stage end), whether each arm moves
more than it drifts (the movement gate), and whether two agents' movement profiles are
correlated (co-movement, judged against the ordinary-ordinary pairs as in A1). It also
computes the A1 layer verdict at every stage end on that stage's own world probe. It then hands
all of it to decision_rules.evaluate_A4 (rules A4, verbatim definitions in the rules file).

Every list comes from the rules' parameters.A4 (stage sequence, probes, drift pairs); a stage
end's own world is read from each run's saved schedule (its stage name), never typed. Draws are
joint: both probes hold the same episode_seed groups (asserted), so draw k of every entry, on
either probe, resamples the same groups. The A1 cell at the primary checkpoint is read from
this manifest's similarity.json (same rules sha asserted), not recomputed.

Gates (tooling reading, stated in the output): G1 and G3 exist only for an agent replayed on its
own store, so for a stage-end cell they are taken from the store-generating captures on the
same world's probe; G2 from every capture used; G4 from the probe's controls; G6 from each
cell's and each movement probe's held-out groups; G5 study-wide.

Outputs: across_worlds.{json,csv} beside the manifest's other outputs (driver_io.write_outputs
never overwrites an output computed under other rules).

Usage:
  OMP_NUM_THREADS=3 python scripts/analysis/nmn/run_across_worlds.py \\
      --manifest docs/experiments/active/modulator_clues/algorithmic_null_mayrep.yaml --workers 5

Plan: docs/develop/active/neuromodulation/ALGORITHMIC_NULL_ANALYSIS_TOOLING.md, §A1/A3/A4
statistics (A4), File Changes §16.
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
import yaml  # noqa: E402

_STATE: dict = {}


def _log(*a):
    print(*a, flush=True)


# ------------------------------------------------------------------------------ layout ------
def own_world(man: dict, selector: str) -> str:
    """The world (probe id) a stage-end checkpoint belongs to: the suffix of the stage's saved
    name in each run's models/schedule.yaml (e.g. 02_passive -> passive); `final` is the last
    stage. Every run must agree."""
    from scripts.analysis.nmn import driver_io as dio
    worlds = set()
    for r in man["runs"]:
        names = yaml.safe_load((dio._abs(r["path"]) / "models" / "schedule.yaml").read_text()
                               )["continual"]["stage_names"]
        k = len(names) - 1 if selector == "final" else int(selector.split(":")[1])
        worlds.add(names[k].split("_", 1)[1])
    if len(worlds) != 1:
        raise ValueError(f"{selector}: runs disagree on its world {sorted(worlds)}")
    return worlds.pop()


def check_manifest(man: dict, layout: dict) -> None:
    """Every checkpoint parameters.A4 names (stage sequence and drift pairs, :prev included)
    is listed for every run, and every A4 probe is a manifest probe."""
    need = set(layout["stage_sequence"]) | {str(d["prev"]) for d in layout["drift_pairs"]} \
        | {str(d["checkpoint"]) for d in layout["drift_pairs"]}
    for r in man["runs"]:
        miss = need - {str(c) for c in r["checkpoints"]}
        if miss:
            raise ValueError(f"run {r['label']}: A4 needs checkpoints {sorted(miss)}")
    probes = {p["id"] for p in man["probes"]}
    if not set(layout["probes"]) <= probes:
        raise ValueError(f"A4 probes {layout['probes']} not all in the manifest {sorted(probes)}")


# ----------------------------------------------------------------------------- statistics --
def movement_entries(layout: dict) -> list[tuple[str, str, str, str]]:
    """[(kind, from, to, probe)]: the 8 profile entries (consecutive stage ends x probes, in
    decision_rules.a4_layout order) and the drift entries."""
    out = [("profile", a, b, p) for (a, b, p) in layout["profile_entries"]]
    out += [("drift", str(d["prev"]), str(d["checkpoint"]), d["probe"]) for d in layout["drift_pairs"]]
    return out


def agent_layer(key: str, name: str) -> dict:
    """Movement and drift of one agent at one layer: point and joint draws per entry."""
    from scripts.analysis.nmn.run_similarity import _Fits, predictivity
    st = _STATE
    caps, agents, splits, boots, rs, layout = (st[k] for k in (
        "caps", "agents", "splits", "boots", "rs", "layout"))
    lab = agents[name]["label"]
    fits = _Fits()
    ent = []
    for kind, a, b, pid in movement_entries(layout):
        g = caps.probes[pid].row_seed
        Xa = caps.layer(lab, a, pid, key)
        Xb = caps.layer(lab, b, pid, key)
        pr = predictivity(Xa, Xb, g, splits[pid], boots[pid], rs, fits, f"{name}/{key}/{a}->{b}/{pid}")
        ent.append({"kind": kind, "from": a, "to": b, "probe": pid, "P": pr["point"],
                    "movement": 1.0 - pr["point"], "draws": 1.0 - pr["draws"],
                    "fits_ab": pr["fits_ab"], "fits_ba": pr["fits_ba"]})
    return {"agent": name, "layer": key, "entries": ent, "fits": fits.n,
            "fits_at_grid_edge": fits.edge, "predictor_columns": fits.columns}


def agent_summary(res: dict, P) -> dict:
    """Profile (8 points), drift d_a (mean of the drift entries), and the per-draw
    mean(profile) - d_a with its bootstrap quantiles (rules A4.movement_gate)."""
    from scripts.analysis.nmn.run_similarity import _q
    prof = [e for e in res["entries"] if e["kind"] == "profile"]
    drift = [e for e in res["entries"] if e["kind"] == "drift"]
    pd = np.stack([e["draws"] for e in prof])            # (8, draws)
    dd = np.stack([e["draws"] for e in drift]).mean(axis=0)
    diff = pd.mean(axis=0) - dd
    lo, hi, bad = _q(diff, P)
    return {"profile": [e["movement"] for e in prof], "profile_draws": pd,
            "drift": float(np.mean([e["movement"] for e in drift])),
            "mean_movement_minus_drift": float(np.mean([e["movement"] for e in prof])
                                               - np.mean([e["movement"] for e in drift])),
            "q_lo": lo, "q_hi": hi, "nonfinite_draws": bad}


def pearson_rows(A, B) -> np.ndarray:
    """Pearson correlation of A[:, k] with B[:, k] for every column k (entries on axis 0)."""
    A = np.asarray(A, float) - np.mean(A, axis=0)
    B = np.asarray(B, float) - np.mean(B, axis=0)
    with np.errstate(invalid="ignore", divide="ignore"):
        return (A * B).sum(axis=0) / np.sqrt((A * A).sum(axis=0) * (B * B).sum(axis=0))


def co_movement(summ: dict, sets: dict) -> dict:
    """r(a, b) for every pair of the rules' pair sets: the point (from the point profiles) and
    the joint draws (from the draw-wise profiles), rules A4.co_movement_statistic."""
    out = {}
    for sname, pairs in sets.items():
        for pname, (a, b) in pairs.items():
            pa, pb = summ[a], summ[b]
            out.setdefault(sname, {})[pname] = {
                "point": float(pearson_rows(np.asarray(pa["profile"])[:, None],
                                            np.asarray(pb["profile"])[:, None])[0]),
                "draws": pearson_rows(pa["profile_draws"], pb["profile_draws"])}
    return out


# ------------------------------------------------------------------------ A1 at stage ends --
def cell_job(cell):
    from scripts.analysis.nmn import run_similarity as rs_
    st = _STATE
    return rs_.analyse_cell(st["caps"], st["man"], st["P"], tuple(cell), st["cell_agents"][tuple(cell)],
                            st["verdict_layers"], primary=False, headline=False, log=_log)


def cell_gates(caps, cell, cell_res, P, man, g4_by_probe) -> dict:
    """Gates of one stage-end cell: G2 from every capture of the cell, G1 / G3 from the
    store-generating captures on the same probe, G4 from the probe's controls, G6 from the
    cell's held-out groups (see the module docstring)."""
    from scripts.analysis.nmn import decision_rules as dr
    from scripts.analysis.nmn import driver_io as dio
    sel, pid = cell
    reps = [caps.reports[(a["label"], a["selector"], pid)] for a in cell_res["agents"].values()]
    gen = [r for (lab, s, p), r in caps.reports.items()
           if p == pid and r.get("gate_G1_self_agreement") is not None]
    g = dio.capture_gates(reps + gen, P)
    g6 = dr.gate_G6({"bootstrap_n": man["bootstrap_n"],
                     "test_groups": {"predictivity": cell_res["test_groups_per_repeat"]}}, P)
    return {"G1": g["G1"], "G2": g["G2"], "G3": g["G3"], "G4": dr.gate_G4(g4_by_probe[pid], P),
            "G6": bool(g6["bootstrap_ok"] and all(g6["per_key"].values()))}


def a1_words(ev_a1: dict, policy) -> dict:
    """Unprefixed A1 layer words from an evaluate_A1 result or a written evaluation."""
    if "layer_words" in ev_a1:
        return dict(ev_a1["layer_words"])
    pre = f"{policy.prefix}: " if policy.prefix else ""
    return {k: (v["verdict"][len(pre):] if pre and v["verdict"].startswith(pre) else v["verdict"])
            for k, v in ev_a1["layers"].items()}


def evaluate(layer_inputs: dict, P, policy, verdict_layers, gates, yardstick_complete) -> dict:
    """decision_rules.evaluate_A4 on the driver's inputs (the only place a verdict is formed)."""
    from scripts.analysis.nmn import decision_rules as dr
    return dr.evaluate_A4({"layout": dr.a4_layout(P), "layers": layer_inputs}, P, policy=policy,
                          verdict_layers=verdict_layers, gates=gates,
                          yardstick_complete=yardstick_complete)


# ------------------------------------------------------------------------------------ main --
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--workers", type=int, required=True,
                    help="worker processes (stage-end A1 cells, then agent x layer movement jobs)")
    args = ap.parse_args(argv)
    os.environ.setdefault("JAX_PLATFORMS", "cpu")
    from concurrent.futures import ProcessPoolExecutor
    from scripts.analysis.nmn import decision_rules as dr
    from scripts.analysis.nmn import driver_io as dio
    from scripts.analysis.nmn import representation as rep
    from scripts.analysis.nmn.run_similarity import agents_of_cell, _strip_draws, _q

    man_path = dio._abs(args.manifest)
    man = dio.load_manifest(man_path)
    pinned, policy = dio.open_rules(man)
    P = pinned.parameters
    verdict_layers = list(pinned.rules["common"]["verdict_layers"])
    layout = dr.a4_layout(P)
    check_manifest(man, layout)
    stamp = dio.stamp(pinned, policy, man_path)
    caps = dio.Captures(man, pinned)
    stamp["captures_rules_sha256"] = caps.rules_sha
    roles = caps.meta["roles"]
    _log(f"[across_worlds] {man['name']}: {policy.status}; rules {pinned.path} "
         f"{pinned.sha256[:12]}; {stamp['verdict_statement']}")

    worlds = {sel: own_world(man, sel) for sel in layout["stage_sequence"]}
    g5 = None
    entered = [r["label"] for r in man["runs"]]
    if policy.allowed:
        g5 = dio.survival_block(dio.read_survival(man, roles), P, policy.status)["gate_G5"]
        entered = [l for a in ("ordinary", "modulated") for l in g5["entered"][a]]
    trained = {n: a for n, a in agents_of_cell(caps, man, (layout["stage_sequence"][-1],
                                                           layout["probes"][0]),
                                               entered, roles).items() if not a["untrained"]}
    sets = {k: v for k, v in dio.pair_sets(trained, man["comparisons"]).items() if k != "UNTRAINED"}

    # one split and one bootstrap per probe; both probes must hold the same groups, so draw k
    # resamples the same episode_seed groups on either probe (joint across the whole profile)
    splits, boots, g4 = {}, {}, {}
    for pid in layout["probes"]:
        g = caps.probes[pid].row_seed
        splits[pid] = dio.make_splits(g, P, int(man["probe_split"]["seed"]))
        boots[pid] = rep.joint_group_bootstrap(g, splits[pid], int(man["bootstrap_n"]),
                                               int(man["probe_split"]["bootstrap_seed"]))
        g4[pid] = dio.g4_controls(caps.probes[pid], splits[pid], man, dio.quantities(pinned), P)
    ref = layout["probes"][0]
    for pid in layout["probes"][1:]:
        if not all(np.array_equal(a.test_groups, b.test_groups) for a, b in zip(splits[ref], splits[pid])):
            raise ValueError(f"probes {ref} and {pid} split their groups differently; the A4 draws "
                             f"would not be joint")
    t0 = time.time()

    # A1 at every stage end on its own world: the primary cell from similarity.json, the others here
    primary = dio.primary_cell(pinned, policy.status, dio.cells(caps, man)) if policy.allowed else None
    sim_path = caps.out / "similarity.json"
    cells = {sel: (sel, worlds[sel]) for sel in layout["stage_sequence"]}
    todo = [c for c in cells.values() if c != primary]
    cell_agents = {c: agents_of_cell(caps, man, c, entered, roles) for c in todo}
    _STATE.update(caps=caps, man=man, P=P, verdict_layers=verdict_layers, cell_agents=cell_agents,
                  agents=trained, splits=splits, boots=boots, rs=dio.ridge(man, P), layout=layout)
    _log(f"[across_worlds] A1 at {len(todo)} stage-end cells {todo}; movement: "
         f"{len(trained)} agents x {len(verdict_layers)} layers x {len(movement_entries(layout))} entries")
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        cell_res = dict(zip(todo, ex.map(cell_job, todo)))
        jobs = [(k, n) for k in verdict_layers for n in trained]
        mov = list(ex.map(agent_layer, [k for k, _ in jobs], [n for _, n in jobs]))
    _log(f"[across_worlds] computed in {time.time() - t0:.0f}s")

    stage_end = {}
    for sel, c in cells.items():
        if c == primary:
            sim = json.loads(sim_path.read_text())
            if sim["decision_rules"]["sha256"] != pinned.sha256 or tuple(sim["primary_cell"]) != c:
                raise ValueError(f"{sim_path}: not this rules sha / primary cell; run run_similarity first")
            stage_end[sel] = {"cell": list(c), "source": "similarity.json", "gates": sim["gates"],
                              "a1_words": a1_words(sim["evaluation"]["A1"], policy)}
            continue
        res = cell_res[c]
        refused = {k: v for k, v in res["refused_layers"].items() if k in verdict_layers}
        if refused:
            raise ValueError(f"cell {c}: verdict layers refused {refused}")
        gates = cell_gates(caps, c, res, P, man, g4)
        entry = {"cell": list(c), "source": "computed here", "gates": gates,
                 "test_groups_per_repeat": res["test_groups_per_repeat"],
                 "row_lag_control": res["row_lag_control"], "a1_words": None,
                 "statistics": _strip_draws(res["layers"])}
        if policy.allowed:
            inputs = {}
            for key in verdict_layers:
                s = {}
                for stat in ("predictivity", "cka"):
                    pairs = {}
                    for pname, v in res["layers"][key][stat].items():
                        pairs.setdefault(v["pair_set"], {})[pname] = {"point": v["point"],
                                                                      "draws": v["draws"]}
                    s[stat] = dr.summarise_pairs(pairs, P)
                inputs[key] = s
            a1 = dr.evaluate_A1(inputs, P, policy=policy, verdict_layers=verdict_layers,
                                gates=gates, yardstick_complete=bool(g5["yardstick_complete"]))
            entry["a1_words"] = dict(a1["layer_words"])
            entry["a1"] = dio.finalize_evaluation(a1, policy)
        stage_end[sel] = entry

    # movement, drift, gate, co-movement per layer
    by = {(m["layer"], m["agent"]): m for m in mov}
    layers, layer_inputs, csv_rows = {}, {}, []
    g6_probe = {pid: dr.gate_G6({"bootstrap_n": man["bootstrap_n"], "test_groups": {
        "movement": dio.split_counts(splits[pid], caps.probes[pid].row_seed)}}, P) for pid in splits}
    for key in verdict_layers:
        summ = {n: agent_summary(by[(key, n)], P) for n in trained}
        co = co_movement(summ, sets)
        lay = {"agents": {n: {k: v for k, v in s.items() if k != "profile_draws"}
                          | {"entries": [{k: v for k, v in e.items() if k != "draws"}
                                         for e in by[(key, n)]["entries"]]}
                          for n, s in summ.items()},
               "co_movement": {sname: {p: {"point": v["point"], **dict(zip(
                   ("q_lo", "q_hi", "nonfinite_draws"), _q(v["draws"], P)))}
                   for p, v in pairs.items()} for sname, pairs in co.items()}}
        for n, s in summ.items():
            csv_rows.append({"layer": key, "row": "movement", "name": n, "arm": trained[n]["arm"],
                             "profile": " ".join(f"{x:.4f}" for x in s["profile"]),
                             "drift": s["drift"], "value": s["mean_movement_minus_drift"],
                             "q_lo": s["q_lo"], "q_hi": s["q_hi"]})
        for sname, pairs in lay["co_movement"].items():
            for p, v in pairs.items():
                csv_rows.append({"layer": key, "row": f"co_movement {sname}", "name": p, "arm": "",
                                 "profile": "", "drift": "", "value": v["point"],
                                 "q_lo": v["q_lo"], "q_hi": v["q_hi"]})
        if policy.allowed:
            co_summary = dr.summarise_pairs({s: {p: {"point": v["point"], "draws": v["draws"]}
                                                 for p, v in co[s].items()} for s in co}, P)
            lay["co_movement_summary"] = co_summary
            layer_inputs[key] = {
                "movement": {arm: [summ[n]["q_lo"] for n in trained if trained[n]["arm"] == arm]
                             for arm in ("ordinary", "modulated")},
                "co_movement": co_summary,
                "stage_end_a1": {sel: stage_end[sel]["a1_words"][key] for sel in layout["stage_sequence"]}}
        layers[key] = lay
    doc = {**stamp, "driver": "run_across_worlds", "analysis": "A4 (movement across worlds)",
           "layout": layout, "stage_end_worlds": worlds, "gate_G5": g5,
           "gates_reading": "G1/G3 of a stage-end cell from the store-generating captures on the "
                            "same probe; G2 every capture used; G4 per probe; G6 per cell and per "
                            "movement probe; G5 study-wide",
           "stage_end_cells": {
               sel: {k: v for k, v in e.items() if k != "a1_words"}
               | {"a1_layer_verdicts": None if e["a1_words"] is None else {
                   k: (f"{policy.prefix}: {w}" if policy.prefix else w)
                   for k, w in e["a1_words"].items()}}
               for sel, e in stage_end.items()},
           "movement_g6": {pid: v for pid, v in g6_probe.items()},
           "g4_controls": {pid: {k: v for k, v in g.items() if k in ("input_satiation_r2",
                                                                     "shuffled_r2", "groups_disjoint")}
                           for pid, g in g4.items()},
           "layers": layers,
           "ridge_fits": {"movement_fits": sum(m["fits"] for m in mov),
                          "at_grid_edge": [e for m in mov for e in m["fits_at_grid_edge"]],
                          "fits_with_dropped_columns": sum(c["n_dropped"] > 0 for m in mov
                                                           for c in m["predictor_columns"])},
           "elapsed_s": round(time.time() - t0, 1)}
    if policy.allowed:
        gates = {g: all(stage_end[s]["gates"][g] for s in stage_end) for g in ("G1", "G2", "G3", "G4", "G6")}
        gates["G6"] = gates["G6"] and all(v["bootstrap_ok"] and all(v["per_key"].values())
                                          for v in g6_probe.values())
        doc["gates"] = gates
        doc["evaluation"] = dio.finalize_evaluation(
            evaluate(layer_inputs, P, policy, verdict_layers, gates,
                     bool(g5["yardstick_complete"])), policy)
    else:
        doc["evaluation"] = None
    dio.write_outputs(caps.out, "across_worlds", _strip_draws(doc), csv_rows, policy)
    _log(f"[across_worlds] wrote {caps.out / 'across_worlds.json'}")
    if doc["evaluation"]:
        for k, v in doc["evaluation"]["layers"].items():
            _log(f"  {k:10s} {v['reading']}")
        _log(f"  study      {doc['evaluation']['study']['reading']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
