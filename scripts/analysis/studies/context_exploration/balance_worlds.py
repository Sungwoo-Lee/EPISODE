"""Part 3c of the context-exploration study: are the larger, less observable worlds still balanced?

Plain-language purpose: for every world measured by make_worlds.py + forager.py, the balance study's
ideal planner is solved with that world's search times -- a per-step chance of finding food, cover or
warmth equal to 1 / (mean search time) -- and that world's bites per food item, at the measured predator
hit odds (scaled with the world's hunting-predator density) and at twice those odds. The balance
criteria of the internal-state study are applied unchanged, then the pre-registered candidate rule.

Design (STUDY_PLAN.md Part 3 "Balance (planner)" and "Candidate rule", Revisions 1 and 1a):
  planner      sweep_balance.make_world, variant "main" (E1 food relocation 1 / bites, E2 single hits
               from the ordinary agent's bins, discount 0.95); map without a warm bush (the balance
               study's primary map); find_prob F / B / R = 1 / mean search time for food / cover /
               warmth (5 C threshold); going to open ground keeps the balance study's 2-step trip
  hazard       x1 and x2, times (hunting predators per cell) / (today's 1 per 100 cells), using the
               midpoint of each world's predator count range
  criteria     balance_rule.criteria (1 time split, 2 drive ratios incl. per-decision warming, 3 no
               cause > 60 % of late deaths when >= 5 % die after step 20, 4 survival >= 80 % of today's,
               5 injury drives hiding among fed states; 6 reported only). "Today" = the 10 x 10, range-20,
               food 1-4 world measured the same way, at hazard x1 (its real hazard); the ratio to today at
               the same hazard multiplier is reported beside it
  candidate    at BOTH hazards: criteria 1-5 pass, and mean food search (point estimate over 1,000
               resets) >= 20 steps; also required: the world's reset assertions passed and <= 1 % of
               food searches capped. Ranked by mean food search. The shortest-range 10 x 10 world passing
               criteria 1-5 at both hazards is reported next to them regardless of the search floor.
  exposure     mean food search x mean damage per moving step (with the world's hazard scale), beside
               the injury one resting step in a bush heals (recovery 0.2 x bush multiplier 25 = 5)

  python balance_worlds.py --procs 16 --worlds results/analysis/context_exploration/worlds \
      --search results/analysis/context_exploration/part3_search_times.json \
      --out results/analysis/context_exploration/part3_balance_worlds.json
"""
import argparse, json, os, sys, time
os.environ.setdefault("OMP_NUM_THREADS", "1"); os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts", "analysis", "studies", "internal_state_interactions"))
import planner as PL                                 # noqa: E402
import sweep_balance as SB                           # noqa: E402
import balance_rule as BR                            # noqa: E402

HAZARDS = (1.0, 2.0)
TODAY = ("g10f1to4b12_od", 20)
FLOOR = 20.0
MARGINS = (0.0, 0.5, 2.0)
BUSH_HEAL = SB.BASE.recovery_base * SB.BASE.bush_multiplier


def world_of(find_prob, bites, hscale):
    return SB.make_world({}, {}, dict(find_prob=find_prob, bites_per_item=float(bites), hazard_scale=hscale), "main", False)


def solve_one(job):
    key, fp, bites, hscale = job
    t0 = time.time()
    sol = PL.solve(world_of(fp, bites, hscale))
    r = dict(iters=sol["iters"], delta=sol["delta"],
             summary_by_margin={str(m): PL.summarise_map(sol, margin=m) for m in MARGINS},
             warming_per_decision=PL.warming_per_decision(sol), rollout=PL.rollout_balance(sol))
    return key, r, time.time() - t0


def extension_check():
    """The planner's find_prob option: a search found with probability 1 is a one-step trip. Values and
    Q tables of the two constructions must agree (gate); rollout survival within sampling noise (report)."""
    bins = SB.BINS
    a = PL.solve(PL.World(trip={"O": 2, "B": 2, "W": 2, "R": 2, "F": 1}, warm_bush=False, e1=True, e2="bins", hazard_bins=bins))
    b = PL.solve(PL.World(trip={"O": 2, "B": 2, "W": 2, "R": 2, "F": 4}, warm_bush=False, e1=True, e2="bins", hazard_bins=bins,
                          find_prob={"F": 1.0}))
    dv = float(np.abs(a["V"] - b["V"]).max())
    dq = max(float(np.abs(a["q"][p][1] - b["q"][p][1]).max()) for p in a["places"])
    ra, rb = PL.rollout_balance(a, n_starts=10000), PL.rollout_balance(b, n_starts=10000)
    se = np.sqrt(2 * ra["survival_share"] * (1 - ra["survival_share"]) / 10000)
    # geometric check: with find probability p, the rollouts' food searches take 1 / p steps on average
    c = PL.solve(PL.World(trip={"O": 2, "B": 2, "W": 2, "R": 2, "F": 4}, warm_bush=False, e1=True, e2="bins", hazard_bins=bins,
                          find_prob={"F": 0.1}))
    return dict(max_abs_V_diff=dv, max_abs_Q_diff=dq, pass_=bool(dv < 1e-9 and dq < 1e-9),
                rollout_survival=dict(trip1=ra["survival_share"], find_prob_1=rb["survival_share"],
                                      diff_in_se=float(abs(ra["survival_share"] - rb["survival_share"]) / se)),
                find_prob_0p1_iters=c["iters"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--procs", type=int, required=True)
    ap.add_argument("--worlds", required=True)
    ap.add_argument("--search", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    t0 = time.time()
    ext = extension_check()
    print(f"[balance_worlds] planner find_prob check pass={ext['pass_']} {ext}", flush=True)
    if not ext["pass_"]:
        raise SystemExit("planner find_prob extension check failed")
    lay = {l["layout"]: l for l in json.load(open(os.path.join(a.worlds, "layouts.json")))["layouts"]}
    srch = json.load(open(a.search))["layouts"]
    jobs, meta = [], {}
    for name, L in lay.items():
        if name not in srch:
            continue
        S = srch[name]
        plo, phi = L["changed_keys"]["entities.pred"]["count"]
        dens = ((plo + phi) / 2.0 / L["grid"] ** 2) / (1.0 / 100.0)
        for r in (20, 8, 5, 3):
            mf, mc, mw = S["food"][str(r)]["mean"], S["cover"][str(r)]["mean"], S["warmth"]["5.0"]["mean"]
            fp = {"F": min(1.0, 1.0 / max(mf, 1e-9)), "B": min(1.0, 1.0 / max(mc, 1e-9)), "R": min(1.0, 1.0 / max(mw, 1e-9))}
            slug = f"g{L['grid']}r{r}" + name[len(f"g{L['grid']}"):]
            meta[slug] = dict(layout=name, grid=L["grid"], range=r, food=L["food"], others=L["others"],
                              food_count=L["food_count"], bites=L["bites"], predator_density_factor=dens,
                              find_prob=fp, search=dict(food=S["food"][str(r)], cover=S["cover"][str(r)],
                                                        warmth_5C=S["warmth"]["5.0"]),
                              world_ok=L["world_ok"], fires_capped=L["fires_capped"], yaml=L["yaml"][str(r)])
            for h in HAZARDS:
                jobs.append(((slug, h), fp, L["bites"], h * dens))
    jobs.sort(key=lambda j: -meta[j[0][0]]["grid"])
    res = {}
    with ProcessPoolExecutor(a.procs) as ex:
        for (slug, h), r, sec in ex.map(solve_one, jobs):
            res.setdefault(slug, {})[str(h)] = r
            print(f"{slug:26s} x{h:g}: survival {r['rollout']['survival_share']:.3f} ({sec:.0f}s)", flush=True)
    br = json.load(open(os.path.join(ROOT, "results/analysis/internal_state_interactions/balance/balance_rule.json")))
    noise, spread = br["_meta_warm0"]["noise_floor"], br["_meta_warm0"]["margin_spread"]
    tslug = f"g10r{TODAY[1]}" + TODAY[0][3:]
    base = {h: res[tslug][str(h)] for h in HAZARDS}
    move_mean = SB.BINS_MEAN["move"]
    out_w = {}
    for slug, m in meta.items():
        per = {}
        for h in HAZARDS:
            r = res[slug][str(h)]
            crit, det, verdict = BR.criteria(r, base[1.0], noise, spread)
            crit_same = BR.criteria(r, base[h], noise, spread)[0]["4_survival"]
            per[str(h)] = dict(criteria=crit, verdict=verdict, pass_1to5=all(crit[k] for k in ("1_time", "2_drive", "3_death", "4_survival", "5_hide")),
                               survival_share=r["rollout"]["survival_share"], mean_survival_steps=r["rollout"]["mean_survival_steps"],
                               survival_vs_today_x1=r["rollout"]["survival_share"] / base[1.0]["rollout"]["survival_share"],
                               survival_vs_today_same_hazard=r["rollout"]["survival_share"] / base[h]["rollout"]["survival_share"],
                               criterion4_vs_today_same_hazard=crit_same,
                               starvation_share_of_late_deaths=r["rollout"]["death_cause_share"]["starvation"],
                               exposure_injury_per_food_search=m["search"]["food"]["mean"] * move_mean * h * m["predator_density_factor"],
                               detail=det, iters=r["iters"])
        mf = m["search"]["food"]["mean"]
        cand = (all(per[str(h)]["pass_1to5"] for h in HAZARDS) and mf >= FLOOR and m["world_ok"]
                and m["search"]["food"]["capped_share"] <= 0.01)
        out_w[slug] = dict(**m, per_hazard=per, passes_1to5_both=all(per[str(h)]["pass_1to5"] for h in HAZARDS),
                           search_floor_met=bool(mf >= FLOOR),
                           search_unmeasured=bool(m["search"]["food"]["capped_share"] > 0.01), candidate=bool(cand))
    cands = sorted([s for s, w in out_w.items() if w["candidate"]], key=lambda s: -out_w[s]["search"]["food"]["mean"])
    ten = sorted([s for s, w in out_w.items() if w["grid"] == 10 and w["passes_1to5_both"]], key=lambda s: out_w[s]["range"])
    manifest = []
    for s in cands + ([ten[0]] if ten and ten[0] not in cands else []):
        w = out_w[s]
        doc = yaml.safe_load(open(os.path.join(ROOT, w["yaml"])))
        manifest.append(dict(slug=s, role="candidate" if s in cands else "shortest-range 10x10 passing criteria 1-5",
                             grid=w["grid"], smell_range=w["range"], food_count=w["food_count"], bites=w["bites"],
                             others=w["others"], fires_capped=w["fires_capped"],
                             mean_food_search=w["search"]["food"]["mean"], mean_food_search_ci95=w["search"]["food"]["mean_ci95"],
                             survival_share={h: w["per_hazard"][h]["survival_share"] for h in w["per_hazard"]},
                             measurement_yaml=w["yaml"], settings=doc))
    out = dict(design="STUDY_PLAN.md Part 3 balance + candidate rule (Revisions 1, 1a)", hazards=list(HAZARDS),
               today=tslug, today_survival={str(h): base[h]["rollout"]["survival_share"] for h in HAZARDS},
               criterion6_noise_floor=noise, criterion6_margin_spread=spread, search_floor_steps=FLOOR,
               bush_heal_per_step=BUSH_HEAL, move_hazard_mean_per_step=move_mean,
               planner_extension_check=ext, worlds=out_w, candidates=cands,
               shortest_range_10x10_passing=ten[0] if ten else None, seconds=time.time() - t0)
    json.dump(out, open(a.out, "w"), indent=1)
    json.dump(dict(candidates=manifest), open(a.out.replace(".json", "_manifest.json"), "w"), indent=1)
    print("candidates:", cands, "| shortest-range 10x10 passing:", out["shortest_range_10x10_passing"])


if __name__ == "__main__":
    main()
