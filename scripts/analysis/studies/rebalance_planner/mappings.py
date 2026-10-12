"""Turn each candidate world's settings into the ideal planner's numbers (rebalance-planner study).

Plain-language purpose: the ideal planner (scripts/analysis/studies/internal_state_interactions/planner.py)
does not simulate predators, traps or rocks one by one; it sees, for every step spent outside a bush,
the odds of being hit and how hard. This script derives those odds for each of the 8 half-factorial
worlds (+ level 05 as a reference) from real data, plus the trip to the next food item, and writes
them to docs/experiments/active/rebalance_planner/figures/mappings.json.

Sources and conventions
  predator    The planner works in DAMAGE per step (hit probability x hit size), as the old study's
              measured "hazard bins" do. The one-predator episode table (6.7 M level-05 episodes,
              aggregated by one_predator_aggregate.py
              into figures/data/one_predator_l05_by_sight_pounce.json) gives DEATHS, so it is used only
              for the RELATIVE effect of sight (detection range) and pounce (attack range):
                lethal-encounter hazard  lam(sight, pounce) = injury deaths / (0.74 x total steps)
              (0.74 = share of steps outside the bush at level 05, predator_deaths.json); injury deaths
              include trap deaths, so the trap part is removed with a common slope on the number of
              traps (fixed effect per sight x pounce cell). The ABSOLUTE predator hit rate at level 05
              comes from the old study's recordings: hits of 60+ damage can only be predators (traps
              deal 15-45, rocks 1-5), and a predator hit is U[15,120], so 60+ is 60/105 of them.
                p_pred(world, activity) = p_pred(level 05, activity) x
                                          [mean over the world's (sight, pounce) of lam_pred x expected count]
                                          / [mean over level 05's (sight, pounce) of lam_pred x 1]
              Assumes the share of encounters that kill is the same across sight/pounce settings and
              hazard grows linearly with predator count.
  traps       hidden predators; U[15,45] per step stood on. Visible: the trained level-05 agent's own
              measured residual 15-60 hit rate (after the predator share) scaled by expected count / 7.
              Invisible: the agent cannot route around them -- hit odds per TRAVEL step = expected
              count / 100 cells (density). Not applied to standing-still or resting steps.
  rocks       U[1,5] per step stood on. Visible: measured 0-5 hit rate x expected count / 9.
              Invisible: expected count / 100 per travel step.
  eating      eating steps keep the measured rock / trap hit rates (food sitting on a rock or trap cell
              is a property of the map, not of routing), scaled by expected count.
  food trip   Monte Carlo of the Manhattan distance from a random cell to the nearest of k food items
              on a 10 x 10 grid (k uniform in the world's range). Trip = the MEDIAN, the old study's convention
              (its trip 4 is the measured median for 1-4 items; the Monte Carlo median for 1-4 items is
              also 4, so the two agree). Sensitivity: trip 4 x ratio of the means, rounded (gives 4 for
              1-3 items as well) -- written as trip_sensitivity_mean_ratio.

  python mappings.py
"""
import json, os, sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
AGG = os.path.join(ROOT, "docs/experiments/active/rebalance_planner/figures/data/one_predator_l05_by_sight_pounce.json")
DEATHS_JSON = os.path.join(ROOT, "docs/experiments/active/rebalance_planner/figures/data/predator_deaths.json")
MEAS = os.path.join(ROOT, "results/analysis/internal_state_interactions/world_measurements.json")
OUT = os.path.join(ROOT, "docs/experiments/active/rebalance_planner/figures/mappings.json")
OUTSIDE_SHARE = 0.74
L05_STORES = ["basicq2_w2/rppo_bq2cover_lvl05_t1none_s42", "basicq2_w2/rppo_bq2cover_lvl05_t16quad_s42",
              "hvsmell/rppo_l05body_w0000_t1none_s42", "hvsmell/rppo_l05body_w0000_t16quad_s42"]

# group levels: (-) today's lookalike world, (+) new
LEVELS = {
    "A": {"-": dict(sight=[3], pounce=[3], pred_count=(0, 2)),
          "+": dict(sight=[2, 3], pounce=[2, 3], pred_count=(1, 1))},   # revised 2026-10-12: exactly 1 (was 0-1)
    "B": {"-": dict(food_count=(1, 4), bites=6, gross=6.0),
          "+": dict(food_count=(1, 3), bites=9, gross=16.0)},
    "C": {"-": dict(visible=True), "+": dict(visible=False)},
    "D": {"-": dict(rocks=(6, 12), traps=(2, 12), trap_dmg=(15.0, 45.0)),
          "+": dict(rocks=(4, 8), traps=(3, 6), trap_dmg=(25.0, 60.0))},
}
DESIGN = {1: "----", 2: "+--+", 3: "-+-+", 4: "++--", 5: "--++", 6: "+-+-", 7: "-++-", 8: "++++"}
LEVEL05 = dict(sight=list(range(1, 8)), pounce=[2, 3], pred_count=(0, 2), food_count=(1, 4), bites=12, gross=6.0,
               visible=True, rocks=(6, 12), traps=(2, 12), trap_dmg=(15.0, 45.0))
L05_TRAPS, L05_ROCKS = 7.0, 9.0          # level-05 expected counts (2-12, 6-12) behind the measured rates


def world_settings():
    W = {"level05": dict(LEVEL05, label="level 05 (reference)", signs=None)}
    for k, s in DESIGN.items():
        d = {}
        for g, sign in zip("ABCD", s):
            d.update(LEVELS[g][sign])
        W[f"w{k}"] = dict(d, label=f"world {k} ({s})", signs=s)
    return W


def predator_lambda():
    """lam per (sight, pounce) from the aggregated one-predator table (one_predator_aggregate.py)."""
    A = json.load(open(AGG))
    g = pd.DataFrame([dict(detect=r["sight"], attack_range=r["pounce"], n_hidden=r["traps"], n=r["episodes"],
                           steps=r["steps"], deaths=r["endings"].get("4", 0)) for r in A["rows"]])
    g["lam"] = g.deaths / (OUTSIDE_SHARE * g.steps)
    # common trap slope with a fixed effect per (sight, pounce) cell, weighted by steps
    cells = g.groupby(["detect", "attack_range"])
    x = g.n_hidden - cells.n_hidden.transform(lambda v: np.average(v, weights=g.loc[v.index, "steps"]))
    y = g.lam - cells.lam.transform(lambda v: np.average(v, weights=g.loc[v.index, "steps"]))
    slope = float(np.sum(g.steps * x * y) / np.sum(g.steps * x * x))
    g["hid_ep"] = g.n_hidden * g.n
    c = g.groupby(["detect", "attack_range"]).agg(episodes=("n", "sum"), deaths=("deaths", "sum"),
                                                  steps=("steps", "sum"), hid_ep=("hid_ep", "sum"))
    c["mean_hidden"] = c.hid_ep / c.episodes
    c["lam"] = c.deaths / (OUTSIDE_SHARE * c.steps)
    c["lam_pred"] = c.lam - slope * c.mean_hidden
    reasons = {}
    for r in A["rows"]:
        for k, v in r["endings"].items():
            reasons[int(k)] = reasons.get(int(k), 0) + v
    return c, slope, dict(episodes=int(A["episodes"]), steps=int(A["steps"]), injury_deaths=int(g.deaths.sum()),
                          reasons=reasons, lam_all=float(g.deaths.sum() / (OUTSIDE_SHARE * A["steps"])))


def outside_share_check():
    d = json.load(open(DEATHS_JSON))
    out = {}
    for s in L05_STORES:
        st = d[s]["steps"]; tot = sum(st.values())
        out[s] = 1.0 - st["bush"] / tot
    return out


def measured_rates():
    """Per-activity hit rates (per step outside cover) split by source, from the old study's bins."""
    m = json.load(open(MEAS)); hb = m["hazard_bins"]; acts = hb["runs"][hb["primary_run"]]["activities"]
    U = lambda lo, hi: (min(hi, 120) - max(lo, 15)) / 105.0 if hi > 15 else 0.0   # share of U[15,120] in a bin
    out = {}
    for a, x in acts.items():
        p = np.array(x["bin_probs"]) * x["p_hit"]          # per-step rate in each bin: 0-5,5-15,15-30,30-60,60-100,>=100
        p_pred = (p[4] + p[5]) / U(60, 1e9)
        trap = max(0.0, p[2] - p_pred * U(15, 30)) + max(0.0, p[3] - p_pred * U(30, 60))
        out[a] = dict(rows=x["rows"], p_hit=x["p_hit"], pred=p_pred, trap=trap, rock=float(p[0]),
                      bin_rates=p.tolist(), mean_damage_per_step=x["mean_damage_per_step"],
                      check_15_30_pred_share=U(15, 30), check_ratio_60_100_vs_100=float(p[4] / p[5]) if p[5] else None)
    return out, hb["primary_run"]


def nearest_food_trip(count_range, n=400_000, seed=0):
    rng = np.random.default_rng(seed)
    k = rng.integers(count_range[0], count_range[1] + 1, n)
    a = rng.integers(0, 10, (n, 2))
    best = np.full(n, 99)
    for j in range(count_range[1]):
        f = rng.integers(0, 10, (n, 2))
        d = np.abs(f - a).sum(1)
        best = np.where(j < k, np.minimum(best, d), best)
    return dict(mean=float(best.mean()), median=float(np.median(best)), p90=float(np.percentile(best, 90)),
                share_zero=float((best == 0).mean()))


def hit_bins_uniform(lo, hi, edges):
    """Discretise U[lo,hi] into bins [(prob, mean size)] at the given edges."""
    out = []
    for a, b in zip(edges[:-1], edges[1:]):
        a2, b2 = max(a, lo), min(b, hi)
        if b2 > a2:
            out.append(((b2 - a2) / (hi - lo), (a2 + b2) / 2.0))
    return out


def main():
    c, slope, pq_meta = predator_lambda()
    lam = {(int(d), int(r)): dict(lam=float(v.lam), lam_pred=float(v.lam_pred), episodes=int(v.episodes),
                                  deaths=int(v.deaths), steps=int(v.steps), mean_hidden=float(v.mean_hidden))
           for (d, r), v in c.iterrows()}
    rates, run = measured_rates()
    trips = {str(r): nearest_food_trip(r) for r in [(1, 4), (1, 3)]}
    MEASURED_TRIP_14 = 4                                   # old study: measured median trip to food (1-4 items)
    W = world_settings()

    def mix(s, key):
        return float(np.mean([lam[(d, r)][key] for d in s["sight"] for r in s["pounce"]]))
    ref = mix(LEVEL05, "lam_pred") * 1.0
    worlds = {}
    for name, s in W.items():
        cnt = sum(s["pred_count"]) / 2.0
        scale = mix(s, "lam_pred") * cnt / ref
        tr, rk = sum(s["traps"]) / 2.0, sum(s["rocks"]) / 2.0
        mc = trips[str(s["food_count"])]
        trip = int(mc["median"])                           # old convention: the median trip (MC median 4 = measured 4 at 1-4)
        trip_mean_ratio = int(round(MEASURED_TRIP_14 * mc["mean"] / trips["(1, 4)"]["mean"]))
        pred_bins = hit_bins_uniform(15.0, 120.0, [15, 30, 60, 100, 120])
        trap_bins = hit_bins_uniform(*s["trap_dmg"], [0, 30, 45, 60])
        rock_bins = [(1.0, 3.0)]
        if s["visible"]:
            trap_travel = rates["move"]["trap"] * tr / L05_TRAPS
            rock_travel = rates["move"]["rock"] * rk / L05_ROCKS
        else:
            trap_travel, rock_travel = tr / 100.0, rk / 100.0
        hz = {}
        for what, act in (("move", "move"), ("idle", "move"), ("eat", "eat"), ("rest", "rest")):
            src = {"predator": (rates[act]["pred"] * scale, pred_bins)}
            if what == "move":
                src["trap"] = (trap_travel, trap_bins); src["rock"] = (rock_travel, rock_bins)
            elif what == "eat":
                src["trap"] = (rates["eat"]["trap"] * tr / L05_TRAPS, trap_bins)
                src["rock"] = (rates["eat"]["rock"] * rk / L05_ROCKS, rock_bins)
            hz[what] = {k: dict(p=float(p), bins=[[float(q), float(x)] for q, x in b]) for k, (p, b) in src.items()}
        mean_dmg = {w: sum(v["p"] * sum(q * x for q, x in v["bins"]) for v in d.values()) for w, d in hz.items()}
        worlds[name] = dict(settings={k: v for k, v in s.items()}, predator_scale=scale,
                            lam_pred_mix=mix(s, "lam_pred"), lam_mix=mix(s, "lam"), expected_predators=cnt,
                            lethal_encounter_hazard_per_outside_step=mix(s, "lam") * cnt,
                            food=dict(trip=trip, trip_sensitivity_mean_ratio=trip_mean_ratio, bites=s["bites"], gross=s["gross"], net=s["gross"] - 1.0,
                                      per_item=(s["gross"] - 1.0) * s["bites"],
                                      per_item_net_of_drain=(s["gross"] - 2.0) * s["bites"]),
                            expected_traps=tr, expected_rocks=rk, hazard=hz, mean_damage_per_step=mean_dmg)
    out = dict(
        sources=dict(one_predator_aggregate=os.path.relpath(AGG, ROOT), deaths_json=os.path.relpath(DEATHS_JSON, ROOT),
                     measurements=os.path.relpath(MEAS, ROOT), recordings_run=run),
        outside_share_used=OUTSIDE_SHARE, outside_share_by_store=outside_share_check(),
        parquet=pq_meta, trap_slope_per_trap=slope,
        lam_by_sight_pounce={f"{d},{r}": v for (d, r), v in lam.items()},
        level05_reference_lam_pred=ref, measured_rates_level05=rates,
        food_trip_monte_carlo=trips, measured_trip_1_4=MEASURED_TRIP_14, worlds=worlds,
        notes=["predator scale = 1 for level 05 by construction",
               "hazard per activity: move = travel step; idle = standing still in the open (predator only); "
               "eat = eating step; rest = resting step (predator only); no hazard inside a bush",
               "lam averaged as a simple mean over the (sight, pounce) combinations a world draws (each equally "
               "likely per episode)"])
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w"), indent=1)
    print(f"trap slope {slope:.3e}/trap; level-05 ref lam_pred {ref:.5f}; parquet {pq_meta}")
    print("outside share by store", out["outside_share_by_store"])
    for a, r in rates.items():
        print(f"  measured {a}: pred {r['pred']:.5f} trap {r['trap']:.5f} rock {r['rock']:.5f}  60-100/100+ {r['check_ratio_60_100_vs_100']}")
    print("trips", trips)
    for n, w in worlds.items():
        print(f"{n:8s} scale {w['predator_scale']:.3f} lam {w['lethal_encounter_hazard_per_outside_step']:.5f} "
              f"trip {w['food']['trip']} per item {w['food']['per_item']:.0f} "
              f"move p: " + " ".join(f"{k} {v['p']:.4f}" for k, v in w['hazard']['move'].items())
              + f" | mean dmg/step " + " ".join(f"{k} {v:.3f}" for k, v in w['mean_damage_per_step'].items()))


if __name__ == "__main__":
    main()
