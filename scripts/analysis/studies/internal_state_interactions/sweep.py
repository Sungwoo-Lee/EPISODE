"""Solve the ideal planner for every world in the sweep; one JSON summary + NPZ policy per world.

Each world changes ONE setting from today's level 05 with the random starting temperature (B1),
and is solved on both maps (no warm bush / warm bush) and pooled 0.59 / 0.41. Also: the survival
share of the ideal policy (rollouts from 2,000 training-style starts per map); every world is also
solved at discount 0.99 (the runs train at 0.95) and summarised at tie margins 0 / 0.5 / 2; checks
that are not settings: a finer grid (noise floor of the metric) and the predator hazard at 0 and
doubled. Resumable: existing JSONs are skipped.

  python sweep.py --procs 8 --out results/analysis/internal_state_interactions/sweep
"""
import argparse, json, os, sys
from concurrent.futures import ProcessPoolExecutor
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bodysim as B
import planner as PL

BASE = B.Body()
TRIP = {"O": 2, "B": 2, "W": 2, "R": 2, "F": 2}


def worlds():
    """(name, group, label, value, body kwargs, trip overrides, world kwargs)."""
    W = []
    def add(group, label, value, body=None, trip=None, world=None):
        W.append((f"{group}__{label}__{value}", group, label, value, body or {}, trip or {}, world or {}))
    add("baseline", "level 05", "today")
    for r in (0.5, 1.0, 2.0, 4.0):
        add("A1", "staying warm costs food (rate)", r, body=dict(coupling=True, coupling_rate=r))
    for c in (0.25, 0.5, 1.0, 2.0):
        add("B3", "healing costs food (per point)", c, body=dict(heal_cost=c, shortfall="partial"))
    for d in (4, 6, 8):
        add("A4", "trip to food (steps)", d, trip=dict(F=d))
    for g in (3.0, 2.0):
        add("A4", "food per bite (net)", g, body=dict(food_gain_net=g))
    for d in (4, 6, 8):
        add("A5", "trip to a bush (steps)", d, trip=dict(B=d, W=d))
    for s in (1 / 30, 1 / 15, 1 / 10):
        add("B2", "healing slows off 0 deg (per deg)", round(s, 4), body=dict(heal_cold_s=s, heal_warm_s=s))
    for g in (0.5, 1.0, 2.0):
        add("B4", "injury speeds cooling (gain)", g, body=dict(inj_gain=g, inj_mode="cooling_only"))
    for f, lo in ((0.5, 20.0), (0.2, 20.0), (0.0, 0.0)):
        add("B5", "healing slows when hungry (floor)", f, body=dict(b5=True, b5_floor=f, b5_low=lo, b5_high=100.0))
    # checks, not settings
    add("check", "finer grid", "81x41x91", world=dict(grid=(81, 41, 91)))
    add("check", "predator hazard (times measured)", 0.0, world=dict(hazard_rest=0.0, hazard_move=0.0))
    add("check", "predator hazard (times measured)", 2.0, world=dict(hazard_rest=0.24, hazard_move=1.40))
    return W


MEAS = json.load(open(os.path.join(HERE, "..", "..", "..", "..",
                             "results/analysis/internal_state_interactions/world_measurements.json")))
_g = set(MEAS["gamma"].values())
assert _g == {PL.World().gamma}, f"planner discount {PL.World().gamma} != training runs' {_g} (plan-reviewer R7)"
MARGINS = (0.0, 0.5, 2.0)


def solve_pair(body, t, wkw, gamma):
    sols = []
    for warm, weight in ((False, 1 - PL.WARM_BUSH_SHARE), (True, PL.WARM_BUSH_SHARE)):
        sols.append((PL.solve(PL.World(body=BASE.with_(**body), trip=t, warm_bush=warm, gamma=gamma, **wkw)), weight))
    return sols


def run(job):
    name, group, label, value, body, trip, wkw, out = job
    path = os.path.join(out, f"{name}.json")
    if os.path.exists(path):
        return path, "skip"
    t = dict(TRIP); t.update(trip)
    sols = solve_pair(body, t, wkw, PL.World().gamma)
    surv, arrays = {}, {}
    for sol, _ in sols:
        warm = sol["world"].warm_bush
        surv[f"warm{int(warm)}"] = PL.rollout_survival(sol)
        cat, tie = PL.best_category(sol, "O", 0.5)
        arrays[f"cat_warm{int(warm)}"] = np.array([PL.CATEGORIES.index(c) for c in cat], np.uint8)
        arrays[f"tie_warm{int(warm)}"] = tie
    summ = PL.summarise(sols, margin=0.5)
    by_margin = {str(m): PL.summarise(sols, margin=m)["combination_gain"] for m in MARGINS}
    survival = sum(wt * surv[f"warm{int(s['world'].warm_bush)}"][0] for s, wt in sols)
    mean_steps = sum(wt * surv[f"warm{int(s['world'].warm_bush)}"][1] for s, wt in sols)
    iters = [s["iters"] for s, _ in sols]; delta = [s["delta"] for s, _ in sols]
    grid = list(sols[0][0]["world"].grid)
    del sols
    s99 = solve_pair(body, t, wkw, 0.99)                         # plan-reviewer R1: every world at 0.99
    summ99 = PL.summarise(s99, margin=0.5)
    res = dict(name=name, group=group, label=label, value=value, body=body, trip=t, world=wkw,
               grid=grid, iters=iters, delta=delta,
               summary=summ, gain_by_margin=by_margin, survival_share=survival, mean_survival_steps=mean_steps,
               survival_by_map=surv, summary_gamma099=dict(combination_gain=summ99["combination_gain"],
                                                           balance=summ99["balance"], tie_share=summ99["tie_share"]))
    np.savez_compressed(path.replace(".json", ".npz"), grid=np.array(grid), **arrays)
    json.dump(res, open(path, "w"), indent=1)
    return path, "ok"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--procs", type=int, required=True)
    ap.add_argument("--out", required=True); a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    jobs = [(n, g, l, v, b, t, wk, a.out) for (n, g, l, v, b, t, wk) in worlds()]
    with ProcessPoolExecutor(a.procs) as ex:
        for p, s in ex.map(run, jobs):
            print(s, os.path.basename(p), flush=True)


if __name__ == "__main__":
    main()
