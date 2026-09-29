"""Run every simulated setting the thirst page shows, once, and store summaries as JSON.

  python sweep.py            # writes results/analysis/thirst_water/sweep.json (a few minutes)

Settings (each 2,000 episodes, seed fixed per setting so reruns reproduce):
  drain        drain per step {0.3125 ... 1.6} at grid 10, list placement, gain 5.625
  grid_mode    grid {8,10,12,14,16,18,20} x placement {list, random, center}, drain 0.625
  drain_grid   drain x grid, list placement  (the difficulty map)
  drain_gain   drain x gain at grid 10, list placement
  *_search     the same with search=True: the agent must find the pond each episode (watersim docstring)
  no_water     reference: the same world with water inert (drain 0, gain 0, start 100) per grid size
               (`python sweep.py --no-water-only` adds just this key to an existing sweep.json)
  margin       the scripted agent's own timing: slack margin {25, 50, 100} x grid {10,14,20}, knows / must find
               (plan-reviewer finding 1: the must-find numbers depend on it)
  start        the level-06 design point with per-episode start hydration kept (for the start figure)
"""
import json, os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C
import watersim as S

E = 2000
DRAINS = [0.3125, 0.4, 0.5, 0.625, 0.8, 1.0, 1.25, 1.6]
GRIDS = [8, 10, 12, 14, 16, 18, 20]
MODES = ["list", "random", "center"]
GAINS = [1.625, 2.625, 3.625, 5.625, 8.625, 12.625, 20.625]


def summary(res):
    life = res["life"]; cz = res["cause"]
    on = res["share"]
    walk_w, drink = on[:, 0], on[:, 1]
    v = np.maximum(res["visits"], 1)
    nd = res["drinks"].sum()
    return dict(drinks=float(res["drinks"].mean()), walkthroughs=float((res["visits"] - res["drinks"]).mean()),
                steps_per_drink=float(res["drink_steps"].sum() / max(nd, 1)),
                arrival_W=float(res["arr_sum"].sum() / max(nd, 1)),mean_life=float(life.mean()), survive=float((cz == 0).mean()),
                causes=S.cause_shares(res),
                share={a: float(on[:, i].mean()) for i, a in enumerate(S.ACTS)},
                steps_per_visit=float(np.mean((drink * life)[res["visits"] > 0] / v[res["visits"] > 0])),
                visits=float(res["visits"].mean()), E=int(res["E"]),
                found_median=(float(np.median(res["first_found"][res["first_found"] >= 0]))
                              if (res["first_found"] >= 0).any() else None))


def no_water():
    inert = S.Water(drain=0.0, gain=0.0, start_low=100.0, start_high=100.0)
    return {str(g): summary(S.run(S.World(grid=g, water=inert), E, seed=12)) for g in GRIDS}


def main():
    os.makedirs(C.OUT, exist_ok=True)
    if "--no-water-only" in sys.argv:
        p = os.path.join(C.OUT, "sweep.json"); out = json.load(open(p))
        out["no_water"] = no_water(); json.dump(out, open(p, "w")); print("added no_water"); return
    out = {"_meta": dict(E=E, drains=DRAINS, grids=GRIDS, modes=MODES, gains=GAINS,
                         world=repr(S.World()))}
    t0 = time.time()
    out["drain"] = {str(d): summary(S.run(S.World(water=S.Water(drain=d)), E, seed=11)) for d in DRAINS}
    print("drain", round(time.time() - t0)); 
    out["grid_mode"] = {f"{g}|{m}": summary(S.run(S.World(grid=g, water=S.Water(placement=m)), E, seed=12))
                        for g in GRIDS for m in MODES}
    print("grid_mode", round(time.time() - t0))
    out["drain_grid"] = {f"{d}|{g}": summary(S.run(S.World(grid=g, water=S.Water(drain=d)), E, seed=13))
                         for d in DRAINS for g in GRIDS}
    print("drain_grid", round(time.time() - t0))
    out["drain_gain"] = {f"{d}|{a}": summary(S.run(S.World(water=S.Water(drain=d, gain=a)), E, seed=14))
                         for d in DRAINS for a in GAINS}
    print("drain_gain", round(time.time() - t0))
    out["grid_mode_search"] = {f"{g}|{m}": summary(S.run(S.World(grid=g, search=True, water=S.Water(placement=m)), E, seed=12))
                               for g in GRIDS for m in MODES}
    print("grid_mode_search", round(time.time() - t0))
    out["drain_grid_search"] = {f"{d}|{g}": summary(S.run(S.World(grid=g, search=True, water=S.Water(drain=d)), E, seed=13))
                                for d in DRAINS for g in GRIDS}
    print("drain_grid_search", round(time.time() - t0))
    out["no_water"] = no_water()
    out["margin"] = {f"{mg}|{g}|{sr}": summary(S.run(S.World(grid=g, margin=float(mg), search=sr), E, seed=13))
                     for mg in (25, 50, 100) for g in (10, 14, 20) for sr in (False, True)}
    print("margin", round(time.time() - t0))
    r = S.run(S.World(), E=20000, seed=15)
    out["start"] = dict(W0=r["W0"].round(3).tolist(), life=r["life"].tolist(), cause=r["cause"].tolist())
    json.dump(out, open(os.path.join(C.OUT, "sweep.json"), "w"))
    print("wrote", os.path.join(C.OUT, "sweep.json"), round(time.time() - t0), "s")


if __name__ == "__main__":
    main()
