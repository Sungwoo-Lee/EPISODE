"""The balance sweep (study plan Revision 2 / 2a / 2b): solve the ideal planner under E1 (food runs
out) and E2 (single hits drawn from measured size bins) for every world, and compute the balance
measures from its choice map and from rollouts of its policy.

Plain-language purpose: find where, in the settings that trade hunger, cold and injury against each
other, a world is "balanced" -- hiding, eating and warming each matter, no single danger causes most
deaths, and the best action depends on several body states at once. This script only COMPUTES the
measures; the pre-registered criteria are applied when the results are read.

Worlds (today's level 05 with random starting temperature B1, E1 + E2 on, is the baseline):
  one at a time  food energy per bite (gross) 10/8/5/4/3 (6 today); food search cost = trip to food
                 4/6/8 x bites per item 12/6; bush healing multiplier 10 (25 today); cooling-rate scale
                 0.5 (0.25 today); the four rules of the running level-05 factorial at their picked
                 strengths (hungry-healing floor 0, healing costs 0.5 food per point, warmth costs food
                 at rate 2, gross food per bite 4) singly and all four
  diagnostic     hit probability outside cover x0.5 / x2 ("if hazards were half / double"; no config knob)
  2-D grid       gross food 10/8/6/5/4/3 x hazard x0.5/x1/x2; cells already on an axis are not re-solved
                 (manifest.json maps every cell to its world)
  noise floor    the baseline on a finer grid (81 x 41 x 91), E1-E2 on
Every world is solved on both maps (no warm bush / warm bush). The "bush never on a fire ring"
setting IS the no-warm-bush map of the same world (plan N4), so it is not solved twice.
Variants per world (one JSON each; resumable -- existing JSONs are skipped):
  main   discount 0.95 (the training runs' own), E1 + E2 bins
  g099   discount 0.99 check
  e2off  E1 on, E2 replaced by its per-activity mean-field (the modelling change's own effect)
Per map in each JSON: planner summaries at tie margins 0 / 0.5 / 2 (choice shares, combination gain),
the per-decision warming measure (b'), and rollout measures (B-time, B-drive, B-need, B-death, B-surv,
B-hide, E1 counts) from 2,000 training-style starts x 500 steps.

  python sweep_balance.py --procs 16 --out results/analysis/internal_state_interactions/balance
  python sweep_balance.py --procs 2 --out tmp/<ts>_smoke --only baseline__level-05__today,food__gross-per-bite__10 --variants main
"""
import argparse, json, os, sys, time
from concurrent.futures import ProcessPoolExecutor
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bodysim as B
import planner as PL

ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
MEAS_PATH = os.path.join(ROOT, "results/analysis/internal_state_interactions/world_measurements.json")
MEAS = json.load(open(MEAS_PATH))
_g = set(MEAS["gamma"].values())
assert _g == {PL.World().gamma}, f"planner discount {PL.World().gamma} != training runs' {_g} (plan-reviewer R7)"
if "hazard_bins" not in MEAS:
    raise SystemExit("world_measurements.json has no hazard_bins: run measure_world.py --hazard-bins-only first")
BINS = PL.hazard_bins_from_measurements(MEAS)             # primary (ordinary) agent, per activity
BINS_MEAN = PL.mean_of_bins(BINS)
BASE = B.Body()
TRIP = {"O": 2, "B": 2, "W": 2, "R": 2, "F": 4}           # measured medians (food: predators excluded)
MARGINS = (0.0, 0.5, 2.0)
VARIANTS = ("main", "g099", "e2off")
FOOD_GROSS = (10, 8, 6, 5, 4, 3)
HAZARD = (0.5, 1.0, 2.0)
PICKED = dict(b5=dict(b5=True, b5_floor=0.0, b5_low=20.0, b5_high=100.0, b5_over_floor=1.0),
              b3=dict(heal_cost=0.5, shortfall="partial"),
              a1=dict(coupling=True, coupling_rate=2.0),
              a4=dict(food_gain_net=4.0 - 1.0))
PICKED_LABEL = dict(b5="hungry-healing floor 0", b3="healing costs 0.5 food per point",
                    a1="warmth costs food at rate 2", a4="gross food per bite 4")


def _slug(s):
    return str(s).replace(" ", "-").replace("/", "per")


def worlds():
    """[(name, group, label, value, body kwargs, trip overrides, world kwargs)] and the manifest."""
    W, grid_map, alias = [], {}, {}

    def add(group, label, value, body=None, trip=None, world=None):
        name = f"{group}__{_slug(label)}__{_slug(value)}"
        W.append((name, group, label, value, body or {}, trip or {}, world or {}))
        return name
    base = add("baseline", "level 05", "today")
    food = {6: base}
    for g in FOOD_GROSS:
        if g != 6:
            food[g] = add("food", "gross per bite", g, body=dict(food_gain_net=g - 1.0))
    for t in (4, 6, 8):
        for b in (12, 6):
            if (t, b) != (4, 12):
                add("search", "trip to food x bites per item", f"t{t}_b{b}", trip=dict(F=t),
                    world=dict(bites_per_item=float(b)))
    haz = {1.0: base}
    for h in (0.5, 2.0):
        haz[h] = add("hazard_diagnostic", "hit probability outside cover (times measured)", h,
                     world=dict(hazard_scale=h))
    add("injury", "bush healing multiplier", 10, body=dict(bush_multiplier=10.0))
    add("temperature", "cooling rate scale", 0.5, body=dict(cool_scale=0.5))
    for k in ("b5", "b3", "a1"):
        add("coupling", PICKED_LABEL[k], "on", body=PICKED[k])
    alias[f"coupling__{_slug(PICKED_LABEL['a4'])}__on"] = food[4]      # same world as the food axis at 4
    allb = {}
    for k in ("b5", "b3", "a1", "a4"):
        allb.update(PICKED[k])
    add("coupling", "all four picked rules", "on", body=allb)
    for g in FOOD_GROSS:
        for h in HAZARD:
            if h == 1.0:
                grid_map[f"g{g}_h{h}"] = food[g]
            elif g == 6:
                grid_map[f"g{g}_h{h}"] = haz[h]
            else:
                grid_map[f"g{g}_h{h}"] = add("grid", "gross food x hazard", f"g{g}_h{h}",
                                             body=dict(food_gain_net=g - 1.0), world=dict(hazard_scale=h))
    add("check", "finer grid", "81x41x91", world=dict(grid=(81, 41, 91)))
    manifest = dict(
        worlds=[dict(name=n, group=g, label=l, value=v, body=b, trip=t, world=w) for n, g, l, v, b, t, w in W],
        grid_food_gross_x_hazard=grid_map, aliases=alias,
        variants=dict(main="discount 0.95, E1 + E2 bins (primary)", g099="discount 0.99 check",
                      e2off="E1 on, E2 replaced by its per-activity mean-field"),
        notes=["bush never on a fire ring = the no-warm-bush map (warm0) of the same world (plan N4); "
               "allowed = both maps, pooled 0.59 / 0.41, and per map",
               "hazard x0.5 / x2 are diagnostics (no config knob), not settings to adopt (plan M6)",
               "N6 consistency pair: search t8_b12 vs t4_b6 (same trip / bites)",
               "the finer-grid check is solved for the main variant only (noise floor, plan M3)"],
        hazard_bins_primary=MEAS["hazard_bins"]["primary_run"], hazard_means_per_activity=BINS_MEAN,
        trip=TRIP, margins=list(MARGINS))
    return W, manifest


def make_world(body, trip, wkw, variant, warm):
    t = dict(TRIP); t.update(trip)
    kw = dict(e1=True, bites_per_item=12.0, e2="bins", hazard_bins=BINS, gamma=0.95)
    if variant == "g099":
        kw["gamma"] = 0.99
    elif variant == "e2off":
        kw.update(e2="mean", hazard_bins=None, hazard_rest=BINS_MEAN["rest"], hazard_move=BINS_MEAN["move"],
                  hazard_eat=BINS_MEAN["eat"])
    kw.update(wkw)
    return PL.World(body=BASE.with_(**body), trip=t, warm_bush=warm, **kw)


def run(job):
    name, group, label, value, body, trip, wkw, variant, out = job
    path = os.path.join(out, f"{name}__{variant}.json")
    if os.path.exists(path):
        return path, "skip", 0.0
    t0 = time.time()
    per_map, sols, arrays = {}, [], {}
    for warm, weight in ((False, 1 - PL.WARM_BUSH_SHARE), (True, PL.WARM_BUSH_SHARE)):
        sol = PL.solve(make_world(body, trip, wkw, variant, warm))
        key = f"warm{int(warm)}"
        per_map[key] = dict(
            weight=weight, iters=sol["iters"], delta=sol["delta"], nnz=sol.get("nnz"),
            summary_by_margin={str(m): PL.summarise_map(sol, margin=m) for m in MARGINS},
            warming_per_decision=PL.warming_per_decision(sol),
            rollout=PL.rollout_balance(sol))
        if variant == "main":
            cat, tie = PL.best_category(sol, "O", 0.5)
            arrays[f"cat_{key}"] = np.array([PL.CATEGORIES.index(c) for c in cat], np.uint8)
            arrays[f"tie_{key}"] = tie
        grid = list(sol["world"].grid)
        sols.append((sol, weight)); del sol
    pooled = {str(m): {k: v for k, v in PL.summarise(sols, margin=m).items() if k != "per_map"} for m in MARGINS}
    del sols
    t = dict(TRIP); t.update(trip)
    res = dict(name=name, group=group, label=label, value=value, variant=variant, body=body, trip=t,
               world={k: v for k, v in wkw.items()}, grid=grid,
               food_search_cost=t["F"] / float(wkw.get("bites_per_item", 12.0)),
               per_map=per_map, pooled_planner=pooled, seconds=time.time() - t0)
    if arrays:
        np.savez_compressed(path.replace(".json", ".npz"), grid=np.array(grid), **arrays)
    tmp = path + ".part"
    json.dump(res, open(tmp, "w"), indent=1); os.replace(tmp, path)
    return path, "ok", time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--procs", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", default=None, help="comma-separated world names (smoke runs)")
    ap.add_argument("--variants", default=",".join(VARIANTS))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    W, manifest = worlds()
    json.dump(manifest, open(os.path.join(a.out, "manifest.json"), "w"), indent=1)
    names = {w[0] for w in W}
    only = set(a.only.split(",")) if a.only else names
    if only - names:
        raise SystemExit(f"unknown worlds: {sorted(only - names)}")
    variants = a.variants.split(",")
    if set(variants) - set(VARIANTS):
        raise SystemExit(f"unknown variants: {set(variants) - set(VARIANTS)}")
    jobs = []
    for n, g, l, v, b, t, wk in W:
        if n not in only:
            continue
        for var in variants:
            if g == "check" and var != "main":
                continue
            jobs.append((n, g, l, v, b, t, wk, var, a.out))
    # longest first: the finer grid, then the 0.99 solves
    jobs.sort(key=lambda j: (j[1] != "check", j[7] != "g099"))
    print(f"[sweep_balance] {len(jobs)} jobs -> {a.out}", flush=True)
    with ProcessPoolExecutor(a.procs) as ex:
        for p, s, sec in ex.map(run, jobs):
            print(f"{s} {os.path.basename(p)} {sec:.0f}s", flush=True)


if __name__ == "__main__":
    main()
