"""Solve the ideal planner in every rebalance world and measure decision balance, survival, death
causes and time use (rebalance-planner study).

Plain-language purpose: for each of the 8 half-factorial candidate worlds (+ level 05 as a reference),
find the best choice in every body state and ask how often hiding in a bush and going out to eat are
each the best choice; then follow the best policy for 500 steps from 4,000 random starts.

Per world, on both maps (no warm bush, weight 0.59; warm bush, weight 0.41), pooled with those weights:
  decision balance  shares of training start states at open ground whose best choice is hide / forage /
                    other (warm up or stay in the open) -- margin 0 (primary, pre-registered) and
                    margin 0.5 with ties dropped; the same from inside a cold bush (stay vs leave)
  gap               exploratory: best hide value - best forage value per start state (quantiles,
                    share within 1 return unit)
  rollout           rp.rollout: survival at 500 steps, deaths by cause, time shares, hits per source
Sensitivity worlds (suffix _trip4): the "+" food worlds with the food trip at 4 instead of 5.
EXPLORATORY, NOT pre-registered (added 2026-10-12): single levers from world 8 (LEVERS: predator hit odds
x0.5 / x2, food trip 4 / 6 / 8, bush healing multiplier 12.5 / 5 -- the last planner-only, for understanding
only), and every world's decision balance among start states with food energy < 100.
Writes <out>/<world>.json and <world>.npz (choice codes per state at open ground, both maps), then
<out>/results.json (all worlds + group main effects).

  python run_worlds.py --procs 10 --out docs/experiments/active/rebalance_planner/figures
"""
import argparse, json, os, sys, time
from concurrent.futures import ProcessPoolExecutor

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rp

PL = rp.PL
MAPS = ((False, 1 - PL.WARM_BUSH_SHARE), (True, PL.WARM_BUSH_SHARE))
REAL_CHOICE = 0.20          # pre-registered: hide >= 20 % and forage >= 20 %


LEVER_BASES = ["w8", "w4"]          # world 4 added 2026-10-12 at the verdict review
# EXPLORATORY, NOT pre-registered (tmp/20261011_233031_rebalance_planner.md): single levers from world 8.
# The bush-healing lever is planner-only, "for understanding only" -- training bush healing stays fixed.
LEVERS = [dict(pred_scale=0.5), dict(pred_scale=2.0), dict(trip=4), dict(trip=6), dict(trip=8),
          dict(bush_multiplier=12.5), dict(bush_multiplier=5.0)]


def lever_tag(name, lv):
    if not lv:
        return name
    k, v = next(iter(lv.items()))
    return f"{name}_" + {"trip": "trip", "pred_scale": "pred", "bush_multiplier": "heal", "gamma": "g"}[k] + f"{v:g}"


def jobs():
    M = rp.load_mappings()["worlds"]
    out = [(n, {}, "main") for n in M]
    out += [(n, dict(trip=4), "sensitivity") for n, w in M.items() if w["food"]["trip"] != 4 and n not in LEVER_BASES]
    out += [(b, lv, "lever") for b in LEVER_BASES for lv in LEVERS]
    # sensitivity (verdict review 2026-10-12, as the old study's discount check): discount 0.99
    out += [(b, dict(gamma=0.99), "sensitivity_gamma") for b in ("w4", "w8")]
    return out


def hungry_mask(grid):
    GN, GI, GT = PL.grids(PL.World(grid=tuple(grid)))
    NN, II, TT = np.meshgrid(GN, GI, GT, indexing="ij")
    return (((TT >= -10 - 1e-9) & (TT <= 5 + 1e-9)) & (NN < 100)).ravel()


def run(job):
    name, lv, role, outdir = job
    trip = lv.get("trip")
    tag = lever_tag(name, lv)
    path = os.path.join(outdir, "worlds", f"{tag}.json")
    if os.path.exists(path):
        return tag, "skip", 0.0
    t0 = time.time()
    wm = rp.load_mappings()["worlds"][name]
    per_map, arrays = {}, {}
    for warm, weight in MAPS:
        sol = PL.solve(rp.make_world(wm, warm, trip_food=trip, pred_scale=lv.get("pred_scale", 1.0),
                                       bush_multiplier=lv.get("bush_multiplier"), gamma=lv.get("gamma", 0.95)))
        gap = rp.hide_forage_gap(sol)
        key = f"warm{int(warm)}"
        per_map[key] = dict(
            weight=weight, iters=sol["iters"], delta=sol["delta"],
            decision_open=rp.decision_shares(sol, "O", 0.0),
            decision_open_ties_dropped=rp.decision_shares(sol, "O", 0.5),
            decision_in_bush=rp.decision_shares(sol, "B", 0.0),
            gap=dict(q10=float(np.quantile(gap, 0.1)), q50=float(np.median(gap)), q90=float(np.quantile(gap, 0.9)),
                     within_1=float((np.abs(gap) < 1.0).mean()), hide_better=float((gap > 0).mean())),
            rollout=rp.rollout(sol))
        code, tie = rp.category_codes(sol, "O")
        arrays[f"code_{key}"] = code; arrays[f"tie_{key}"] = tie
        grid = list(sol["world"].grid)
        del sol
    pool = lambda f: sum(per_map[k]["weight"] * f(per_map[k]) for k in per_map)
    pooled = dict(
        decision_open={d: pool(lambda m: m["decision_open"][d]) for d in rp.DECISIONS},
        decision_open_ties_dropped={d: pool(lambda m: m["decision_open_ties_dropped"][d]) for d in rp.DECISIONS},
        decision_in_bush={d: pool(lambda m: m["decision_in_bush"][d]) for d in rp.DECISIONS},
        gap_within_1=pool(lambda m: m["gap"]["within_1"]),
        survival=pool(lambda m: m["rollout"]["survival"]), mean_steps=pool(lambda m: m["rollout"]["mean_steps"]),
        death_share_of_starts={c: pool(lambda m: m["rollout"]["death_share_of_starts"][c]) for c in rp.DEATHS},
        time_share={k: pool(lambda m: m["rollout"]["time_share"][k]) for k in rp.TIME_KEYS},
        warm_cell_share=pool(lambda m: m["rollout"]["warm_cell_share"]),
        hits_per_100_steps={s: pool(lambda m: m["rollout"]["hits_per_100_steps"][s]) for s in rp.SOURCES})
    d = pooled["decision_open"]
    pooled["real_choice"] = bool(d["hide"] >= REAL_CHOICE and d["forage"] >= REAL_CHOICE)
    # exploratory, not pre-registered: the same shares among start states with food energy < 100
    hun = {}
    for (warm, weight) in MAPS:
        c = arrays[f"code_warm{int(warm)}"][hungry_mask(grid)]
        for i, d in enumerate(rp.DECISIONS):
            hun[d] = hun.get(d, 0.0) + weight * float((c == i).mean())
    pooled["exploratory_decision_open_hungry"] = hun
    res = dict(world=name, tag=tag, role=role, levers=lv, trip_food=trip or wm["food"]["trip"],
               sensitivity=(role != "main"), label=wm["settings"]["label"],
               signs=wm["settings"]["signs"], grid=grid, per_map=per_map, pooled=pooled, seconds=time.time() - t0)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    np.savez_compressed(path.replace(".json", ".npz"), grid=np.array(grid), **arrays)
    json.dump(res, open(path + ".part", "w"), indent=1); os.replace(path + ".part", path)
    return tag, "ok", time.time() - t0


def main_effects(R, metric):
    """mean over '+' worlds minus mean over '-' worlds, per group, for metric(result)."""
    W = [r for r in R.values() if r["signs"] and not r["sensitivity"]]
    out = {}
    for g, k in zip("ABCD", range(4)):
        plus = [metric(r) for r in W if r["signs"][k] == "+"]
        minus = [metric(r) for r in W if r["signs"][k] == "-"]
        out[g] = float(np.mean(plus) - np.mean(minus))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--procs", type=int, required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    J = [(n, lv, role, a.out) for n, lv, role in jobs()]
    with ProcessPoolExecutor(a.procs) as ex:
        for tag, st, sec in ex.map(run, J):
            print(f"{st} {tag} {sec:.0f}s", flush=True)
    R = {}
    for n, lv, _, _ in J:
        tag = lever_tag(n, lv)
        R[tag] = json.load(open(os.path.join(a.out, "worlds", f"{tag}.json")))
    metrics = {
        "hide share (open ground)": lambda r: r["pooled"]["decision_open"]["hide"],
        "forage share (open ground)": lambda r: r["pooled"]["decision_open"]["forage"],
        "other share (open ground)": lambda r: r["pooled"]["decision_open"]["other"],
        "survival at 500 steps": lambda r: r["pooled"]["survival"],
        "injury deaths (share of starts)": lambda r: sum(r["pooled"]["death_share_of_starts"][c] for c in rp.SOURCES),
        "starvation deaths (share of starts)": lambda r: r["pooled"]["death_share_of_starts"]["starvation"],
        "time in bush": lambda r: r["pooled"]["time_share"]["bush"],
        "time eating": lambda r: r["pooled"]["time_share"]["eat"],
    }
    eff = {m: main_effects(R, f) for m, f in metrics.items()}
    summary = {tag: dict(label=r["label"], signs=r["signs"], trip_food=r["trip_food"], sensitivity=r["sensitivity"],
                         role=r["role"], levers=r["levers"],
                         **{k: v for k, v in r["pooled"].items()}) for tag, r in R.items()}
    out = dict(pre_registered=dict(real_choice="hide >= 20 % and forage >= 20 % of training start states at open "
                                               "ground, margin 0, pooled over the two maps", threshold=REAL_CHOICE),
               worlds=summary, main_effects=eff,
               exploratory_note="NOT pre-registered: exploratory_decision_open_hungry (start states with food < 100) and "
                                "the role='lever' rows (single levers from world 8; bush healing is planner-only, for "
                                "understanding only -- training bush healing stays fixed)",
               revision="2026-10-12: A+ predator count exactly 1 (expected 1, was 0-1 -> 0.5)",
               main_effects_note="mean of the four '+' worlds minus the four '-' worlds; half factorial (8 of 16), "
                                 "main effects aliased with three-way interactions; sensitivity and level-05 rows excluded")
    json.dump(out, open(os.path.join(a.out, "results.json"), "w"), indent=1)
    print(f"{'world':14s} {'hide':>6s} {'forage':>6s} {'other':>6s} choice {'surv':>5s}  deaths p/t/r/starve/over/cold  time bush/trav/eat/warm/open")
    for tag, s in summary.items():
        d = s["decision_open"]; ds = s["death_share_of_starts"]; ts = s["time_share"]
        print(f"{tag:14s} {d['hide']:6.2f} {d['forage']:6.2f} {d['other']:6.2f} {str(s['real_choice']):6s} {s['survival']:5.2f}  "
              + "/".join(f"{ds[c]:.2f}" for c in rp.DEATHS[:6]) + "  " + "/".join(f"{ts[k]:.2f}" for k in rp.TIME_KEYS))
    for m, e in eff.items():
        print(f"  {m:40s} " + " ".join(f"{g} {v:+.3f}" for g, v in e.items()))


if __name__ == "__main__":
    main()
