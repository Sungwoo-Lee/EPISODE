"""Checks that the rebalance planner's two additions are wired correctly before any world is read.

  1  per-source hazard plug-in == old planner: the old study's measured level-05 hazard bins, written
     as a per-source table and solved through rp.hazard_dist, give the same values and choice tables
     as the old planner's own bins code path (max |V difference| <= 1e-6; best choice identical in
     every state). Both maps.                                                              [gate]
  2  rp.rollout == planner.rollout_balance on the same solution: survival share within 3 standard
     errors, mean survival steps within 3 %, bush and eating time shares within 0.02.       [gate]
     (different random streams, so not bitwise)
  3  report: the decomposed level-05 reference vs the old study's level-05 result (balance sweep
     baseline): what the change of hazard model alone moves.                               [report]

  python validate_planner.py --out docs/experiments/active/rebalance_planner/figures/validation_planner.json
"""
import argparse, json, os, sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rp

PL, ROOT = rp.PL, rp.ROOT
MEAS = os.path.join(ROOT, "results/analysis/internal_state_interactions/world_measurements.json")
OLD_BASE = os.path.join(ROOT, "results/analysis/internal_state_interactions/balance/baseline__level-05__today__main.json")
TRIP = {"O": 2, "B": 2, "W": 2, "R": 2, "F": 4}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); a = ap.parse_args()
    meas = json.load(open(MEAS)); bins = PL.hazard_bins_from_measurements(meas)
    table = {"_rebalance": True}
    for what, act in (("move", "move"), ("idle", "move"), ("eat", "eat"), ("rest", "rest")):
        p, probs, sizes = bins[act]
        table[what] = [(p * q, x, 0) for q, x in zip(probs, sizes) if p * q > 0]
    res = {"1_plugin_equals_old": [], "2_rollout_equals_old": []}
    for warm in (False, True):
        kw = dict(trip=TRIP, warm_bush=warm, e1=True, bites_per_item=12.0, e2="bins", gamma=0.95)
        old = PL.solve(PL.World(hazard_bins=bins, **kw))
        new = PL.solve(PL.World(hazard_bins=table, **kw))
        dv = float(np.abs(old["V"] - new["V"]).max())
        same = all(np.array_equal(old["q"][p][1].argmax(0), new["q"][p][1].argmax(0)) for p in old["places"])
        res["1_plugin_equals_old"].append(dict(warm_bush=warm, max_abs_V_diff=dv, best_choice_identical=bool(same),
                                               pass_=bool(dv <= 1e-6 and same)))
        print("1", warm, dv, same, flush=True)
        r_old = PL.rollout_balance(old, n_starts=4000, seed=1)
        r_new = rp.rollout(new, n_starts=4000, seed=0)
        se = np.sqrt(r_old["survival_share"] * (1 - r_old["survival_share"]) / 4000 * 2)
        ok = (abs(r_new["survival"] - r_old["survival_share"]) <= 3 * se
              and abs(r_new["mean_steps"] / r_old["mean_survival_steps"] - 1) <= 0.03
              and abs(r_new["time_share"]["bush"] - r_old["time_share"]["cover"]) <= 0.02
              and abs(r_new["time_share"]["eat"] - r_old["time_share"]["eat"]) <= 0.02)
        res["2_rollout_equals_old"].append(dict(
            warm_bush=warm, survival=(r_new["survival"], r_old["survival_share"]), se_of_difference=float(se),
            mean_steps=(r_new["mean_steps"], r_old["mean_survival_steps"]),
            bush=(r_new["time_share"]["bush"], r_old["time_share"]["cover"]),
            eat=(r_new["time_share"]["eat"], r_old["time_share"]["eat"]), pass_=bool(ok)))
        print("2", warm, res["2_rollout_equals_old"][-1], flush=True)
    m = rp.load_mappings()["worlds"]["level05"]
    old_base = json.load(open(OLD_BASE))
    rep = {}
    for warm in (False, True):
        key = f"warm{int(warm)}"
        s = PL.solve(rp.make_world(m, warm))
        r = rp.rollout(s)
        ob = old_base["per_map"][key]
        rep[key] = dict(new_survival=r["survival"], old_survival=ob["rollout"]["survival_share"],
                        new_decision=rp.decision_shares(s), old_balance=ob["summary_by_margin"]["0.0"]["balance"],
                        new_time=r["time_share"], old_time=ob["rollout"]["time_share"])
        print("3", key, json.dumps(rep[key], default=float), flush=True)
    res["3_level05_decomposed_vs_old"] = rep
    res["pass_"] = all(x["pass_"] for k in ("1_plugin_equals_old", "2_rollout_equals_old") for x in res[k])
    json.dump(res, open(a.out, "w"), indent=1, default=float)
    print("PASS" if res["pass_"] else "FAIL")
    sys.exit(0 if res["pass_"] else 1)


if __name__ == "__main__":
    main()
