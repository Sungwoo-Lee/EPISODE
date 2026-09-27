"""Validation of the Revision-2 planner changes (E1 food relocation, E2 hits from measured bins)
before any balance result is read (study plan Revision 2 "Validation", 2a M5, 2b N2).

Plain-language purpose: the balance sweep changes the planner's world model. These checks show that
(1) with the changes switched off the new code gives the Revision-1 results bit for bit, (2) the new
stochastic solver, fed a hazard with no randomness, is the old mean-field solver exactly, (3) the
measured hit bins are consistent with the recordings, (4) food relocation happens once per 12 bites,
and they put the two agents' hazard numbers side by side. Exits non-zero if a gating check fails.

  1  E1/E2 off reproduces sweep_food4/ exactly (JSON + choice arrays): baseline + 3 worlds  [gate]
  2  rollout_balance == Revision-1 rollout_survival on the E1/E2-off baseline               [gate]
  3a E2 collapsed to its per-activity mean (stochastic path) == per-activity mean-field
     (Revision-1 path), both maps: values and Q tables bitwise                              [gate]
  3b E2 collapsed and pooled to rest / other vs the Revision-1 E2-off baseline (0.12 / 0.70):
     survival, mean steps, combination gain within 5 % (relative); choice shares within
     0.05 (absolute)                                                                         [gate]
  4  per activity: recordings' total damage / steps vs the bin model's p x sum(share x bin
     mean) within 5 % -- two computations on one data set (consistency check, not an
     independent validation)                                                                 [gate]
  5  E1: relocation events per bite within 5 % of 1/12 in the baseline rollouts, both maps   [gate]
  6  both agents' hazard numbers side by side                                               [report]
  7  (after the sweep, --sweep-dir) N6: trip 8 / bites 12 vs trip 4 / bites 6               [report]

  python validate_balance.py --procs 4 --out results/analysis/internal_state_interactions/validation_balance.json
"""
import argparse, json, os, sys, tempfile
from concurrent.futures import ProcessPoolExecutor
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import planner as PL

ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
OUTDIR = os.path.join(ROOT, "results/analysis/internal_state_interactions")
REPRO = ["baseline__level 05__today", "A1__staying warm costs food (rate)__2.0",
         "B3__healing costs food (per point)__0.5", "A4__trip to food (steps)__8"]
TRIP = {"O": 2, "B": 2, "W": 2, "R": 2, "F": 4}


def _repro_one(args):
    name, tmp = args
    import sweep
    job = next(j for j in sweep.worlds(4) if j[0] == name)
    sweep.run((*job, tmp, 4))
    ref = os.path.join(OUTDIR, "sweep_food4", f"{name}.json")
    a, b = json.load(open(ref)), json.load(open(os.path.join(tmp, f"{name}.json")))
    za, zb = np.load(ref.replace(".json", ".npz")), np.load(os.path.join(tmp, f"{name}.npz"))
    arrays_equal = set(za.files) == set(zb.files) and all(np.array_equal(za[k], zb[k]) for k in za.files)
    diff = [k for k in a if a[k] != b.get(k)]
    return dict(world=name, json_identical=(a == b), differing_keys=diff, arrays_identical=bool(arrays_equal),
                pass_=bool(a == b and arrays_equal))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--procs", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--sweep-dir", default=None, help="after the sweep: add the N6 trip/bites consistency report")
    a = ap.parse_args()
    meas = json.load(open(os.path.join(OUTDIR, "world_measurements.json")))
    res = {}

    # 1 -- reproduction of sweep_food4 (Revision-1 code path through the new planner module)
    with tempfile.TemporaryDirectory() as tmp, ProcessPoolExecutor(a.procs) as ex:
        r1 = list(ex.map(_repro_one, [(n, tmp) for n in REPRO]))
    res["1_reproduces_sweep_food4"] = dict(worlds=r1, pass_=all(r["pass_"] for r in r1))
    print("1", res["1_reproduces_sweep_food4"]["pass_"], flush=True)

    # 2 + 3a -- per map
    col = PL.hazard_bins_from_measurements(meas, collapse=True); m = PL.mean_of_bins(col)
    r2, r3a = [], []
    for warm in (False, True):
        s = PL.solve(PL.World(trip=TRIP, warm_bush=warm))
        old = PL.rollout_survival(s); new = PL.rollout_balance(s)
        r2.append(dict(warm_bush=warm, rev1=list(old), new=[new["survival_share"], new["mean_survival_steps"]],
                       pass_=bool(old[0] == new["survival_share"] and old[1] == new["mean_survival_steps"])))
        mf = PL.solve(PL.World(trip=TRIP, warm_bush=warm, hazard_rest=m["rest"], hazard_move=m["move"], hazard_eat=m["eat"]))
        st = PL.solve(PL.World(trip=TRIP, warm_bush=warm, e2="bins", hazard_bins=col))
        q_eq = all(list(mf["q"][p][0]) == list(st["q"][p][0]) and np.array_equal(mf["q"][p][1], st["q"][p][1])
                   for p in mf["places"])
        r3a.append(dict(warm_bush=warm, means=m, iters=[mf["iters"], st["iters"]],
                        V_identical=bool(np.array_equal(mf["V"], st["V"])), Q_identical=bool(q_eq),
                        max_abs_V_diff=float(np.abs(mf["V"] - st["V"]).max()),
                        pass_=bool(np.array_equal(mf["V"], st["V"]) and q_eq)))
    res["2_rollout_matches_rev1"] = dict(maps=r2, pass_=all(r["pass_"] for r in r2))
    res["3a_collapsed_equals_mean_field"] = dict(maps=r3a, pass_=all(r["pass_"] for r in r3a))
    print("2", res["2_rollout_matches_rev1"]["pass_"], "3a", res["3a_collapsed_equals_mean_field"]["pass_"], flush=True)

    # 3b -- pooled to rest / other, collapsed, vs the Revision-1 E2-off baseline
    ro = PL.hazard_bins_from_measurements(meas, pool="rest_other", collapse=True); mro = PL.mean_of_bins(ro)
    sols_new = [(PL.solve(PL.World(trip=TRIP, warm_bush=w, e2="bins", hazard_bins=ro)), wt)
                for w, wt in ((False, 1 - PL.WARM_BUSH_SHARE), (True, PL.WARM_BUSH_SHARE))]
    ref = json.load(open(os.path.join(OUTDIR, "sweep_food4", "baseline__level 05__today.json")))
    new_sum = PL.summarise(sols_new, margin=0.5)
    surv = [PL.rollout_survival(s) for s, _ in sols_new]
    new_surv = sum(wt * sv[0] for (s, wt), sv in zip(sols_new, surv))
    new_steps = sum(wt * sv[1] for (s, wt), sv in zip(sols_new, surv))
    rel = lambda x, y: abs(x - y) / abs(y) if y else abs(x - y)
    comp = dict(survival_share=(new_surv, ref["survival_share"], rel(new_surv, ref["survival_share"])),
                mean_survival_steps=(new_steps, ref["mean_survival_steps"], rel(new_steps, ref["mean_survival_steps"])),
                combination_gain=(new_sum["combination_gain"], ref["summary"]["combination_gain"],
                                  rel(new_sum["combination_gain"], ref["summary"]["combination_gain"])))
    shares = {c: (new_sum["balance"][c], ref["summary"]["balance"][c], abs(new_sum["balance"][c] - ref["summary"]["balance"][c]))
              for c in PL.CATEGORIES}
    ok3b = all(v[2] <= 0.05 for v in comp.values()) and all(v[2] <= 0.05 for v in shares.values())
    res["3b_pooled_rest_other_vs_e2off"] = dict(
        hazard_pooled=dict(rest=mro["rest"], other=mro["move"]), hazard_e2off=dict(rest=0.12, other=0.70),
        relative=comp, choice_share_abs=shares, pass_=bool(ok3b),
        note="(new, Revision-1 sweep_food4, difference); relative for the first three, absolute for choice shares")
    print("3b", ok3b, flush=True)

    # 4 -- E2 consistency, per agent and activity
    r4 = {}
    for run, v in meas["hazard_bins"]["runs"].items():
        for act, x in v["activities"].items():
            direct = x["mean_damage_per_step"]
            model = x["p_hit"] * float(np.dot(x["bin_probs"], x["bin_mean_size"]))
            r4[f"{run}:{act}"] = dict(direct=direct, bin_model=model, rel=rel(model, direct), rows=x["rows"],
                                      pass_=bool(rel(model, direct) <= 0.05))
    res["4_e2_bin_consistency"] = dict(checks=r4, pass_=all(r["pass_"] for r in r4.values()),
                                       note="two computations on one data set; a consistency check, not an independent validation")

    # 5 -- E1 relocation per bite in the baseline (E1 + E2 bins) rollouts
    bins = PL.hazard_bins_from_measurements(meas)
    r5 = []
    for warm in (False, True):
        s = PL.solve(PL.World(trip=TRIP, warm_bush=warm, e1=True, e2="bins", hazard_bins=bins))
        e = PL.rollout_balance(s)["e1"]
        r5.append(dict(warm_bush=warm, bites=e["bites"], relocations=e["relocations"],
                       relocations_per_bite=e["relocations_per_bite"], target=1 / 12,
                       rel=rel(e["relocations_per_bite"], 1 / 12),
                       pass_=bool(rel(e["relocations_per_bite"], 1 / 12) <= 0.05)))
    res["5_e1_relocations_per_bite"] = dict(maps=r5, pass_=all(r["pass_"] for r in r5))
    print("5", res["5_e1_relocations_per_bite"]["pass_"], flush=True)

    # 6 -- both agents side by side (report)
    runs = list(meas["hazard_bins"]["runs"])
    side = {}
    for act in ("eat", "move", "rest"):
        side[act] = {r.split("_")[-2]: dict(p_hit=meas["hazard_bins"]["runs"][r]["activities"][act]["p_hit"],
                                            mean_damage_per_step=meas["hazard_bins"]["runs"][r]["activities"][act]["mean_damage_per_step"],
                                            bin_probs=meas["hazard_bins"]["runs"][r]["activities"][act]["bin_probs"],
                                            rows=meas["hazard_bins"]["runs"][r]["activities"][act]["rows"])
                     for r in runs}
    res["6_both_agents"] = dict(primary=meas["hazard_bins"]["primary_run"], by_activity=side)

    # 7 -- N6 (only after the sweep)
    if a.sweep_dir:
        pair = {}
        for v in ("t8_b12", "t4_b6"):
            p = os.path.join(a.sweep_dir, f"search__trip-to-food-x-bites-per-item__{v}__main.json")
            pair[v] = json.load(open(p)) if os.path.exists(p) else None
        if all(pair.values()):
            res["7_trip_bites_consistency"] = {
                k: {v: pair[v]["per_map"][k]["rollout"]["survival_share"] for v in pair} |
                   {f"{v}_gain": pair[v]["per_map"][k]["summary_by_margin"]["0.5"]["combination_gain"] for v in pair}
                for k in ("warm0", "warm1")}

    gates = [k for k in res if k[0] in "12345"]
    res["pass"] = all(res[k]["pass_"] for k in gates)
    res["src_commit_note"] = "planner.py / measure_world.py at the working tree this was run from"
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(res, open(a.out, "w"), indent=1, default=float)
    print(json.dumps({k: (v["pass_"] if isinstance(v, dict) and "pass_" in v else v) for k, v in res.items()
                      if k != "6_both_agents"}, indent=1))
    print(json.dumps(res["3b_pooled_rest_other_vs_e2off"], indent=1, default=float))
    sys.exit(0 if res["pass"] else 1)


if __name__ == "__main__":
    main()
