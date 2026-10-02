"""Part 2b of the context-exploration study: how much would knowing the episode's danger be worth?

Plain-language purpose: the ideal planner of the balance study is solved once per danger context
(episodes with 0, 1 or 2 hunting predators, hit bins from context_hazard.py) and once for the
"average" context (the pooled bins the balance study uses -- the best policy that does not know the
context). In each context, both policies are followed; the survival difference is the value of
knowing the context. Also: the share of start states where the context policy's best choice beats
the average policy's choice by more than a tie margin.

Design (STUDY_PLAN.md Part 2, Revision 1):
  world        the balance study's baseline (sweep_balance.make_world, variant "main": E1 food
               relocation, E2 single hits from bins, discount 0.95), map without a warm bush
  value        survival share (alive at the 500-step rollout end) of policy(context) minus
               policy(average), both followed in the context; percentage points; 3 seeds x 10,000
               starts each; 95 % interval = normal interval of a difference of two proportions over
               the 30,000 starts per policy (seeds pooled; per-seed values reported)
  choice diff  share of training-style start states (open ground, body temperature -10..+5) where
               Q_context(best of context) - Q_context(average policy's choice) > margin; margin 0.5
               primary, 0 and 2 sensitivity; category level (the balance study's choice categories)
               primary, action level reported
  reading      worth knowing: value >= 2 points with interval excluding 0 in >= 1 context, or choice
               difference >= 10 % in >= 1 context; not worth knowing: every context's upper bound
               < 2 points and choice difference < 10 %; undecided otherwise

  python value_of_knowing.py --procs 16 --hazard results/analysis/context_exploration/part2_context_hazard.json \
      --out results/analysis/context_exploration/part2_value_of_knowing.json
"""
import argparse, json, os, sys, time
os.environ.setdefault("OMP_NUM_THREADS", "1"); os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
from concurrent.futures import ProcessPoolExecutor
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts", "analysis", "studies", "internal_state_interactions"))
import planner as PL                                 # noqa: E402
import sweep_balance as SB                           # noqa: E402

SEEDS = (0, 1, 2)
N_STARTS = 10_000
MARGINS = (0.0, 0.5, 2.0)
PRIMARY = ("pred0", "pred1", "pred2")


def world_for(bins):
    return SB.make_world({}, {}, dict(hazard_bins=bins), "main", False)


def bins_of(hz_entry, run):
    return PL.hazard_bins_from_measurements(dict(hazard_bins=hz_entry["hazard_bins"]), run=run)


def _solve(args):
    key, bins = args
    t0 = time.time()
    return key, PL.solve(world_for(bins)), time.time() - t0


def _roll(args):
    key, sol, dyn, seed = args
    r = PL.rollout_balance(sol, n_starts=N_STARTS, seed=seed, dyn_world=dyn)
    return key, seed, dict(survival_share=r["survival_share"], mean_survival_steps=r["mean_survival_steps"],
                           death_cause_share=r["death_cause_share"], late_death_share=r["late_death_share_of_starts"])


def choice_difference(sol_c, sol_avg):
    mask = PL.start_mask(sol_c["world"])[0]
    names, qc = sol_c["q"]["O"]; names_a, qa = sol_avg["q"]["O"]
    assert list(names) == list(names_a)
    cols = np.arange(qc.shape[1])
    best_c = qc.argmax(0); choice_a = qa.argmax(0)
    act_gap = qc[best_c, cols] - qc[choice_a, cols]
    cats = np.array([PL.CATEGORY[n] for n in names])
    bc = np.stack([np.where((cats == c)[:, None], qc, -np.inf).max(0) for c in PL.CATEGORIES])
    ba = np.stack([np.where((cats == c)[:, None], qa, -np.inf).max(0) for c in PL.CATEGORIES])
    cat_c = bc.argmax(0); cat_a = ba.argmax(0)
    cat_gap = bc[cat_c, cols] - bc[cat_a, cols]
    out = {}
    for m in MARGINS:
        out[str(m)] = dict(category=float((cat_gap[mask] > m).mean()), action=float((act_gap[mask] > m).mean()))
    out["start_states"] = int(mask.sum())
    out["differs_at_all"] = dict(category=float((cat_c[mask] != cat_a[mask]).mean()),
                                 action=float((best_c[mask] != choice_a[mask]).mean()))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--procs", type=int, required=True)
    ap.add_argument("--hazard", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    t0 = time.time()
    hz = json.load(open(a.hazard))
    runs = list(hz["contexts"])
    solve_jobs = []
    for run in runs:
        solve_jobs.append(((run, "average"), PL.hazard_bins_from_measurements(SB.MEAS, run=run)))
        for ctx, e in hz["contexts"][run].items():
            solve_jobs.append(((run, ctx), bins_of(e, run)))
    sols = {}
    with ProcessPoolExecutor(a.procs) as ex:
        for key, sol, sec in ex.map(_solve, solve_jobs):
            sols[key] = sol
            print(f"solved {key[0][-22:]} {key[1]}: iters {sol['iters']} ({sec:.0f}s)", flush=True)
    roll_jobs = []
    for run in runs:
        for ctx in hz["contexts"][run]:
            dyn = sols[(run, ctx)]["world"]
            for s in SEEDS:
                roll_jobs.append(((run, ctx, "context_policy"), sols[(run, ctx)], None, s))
                roll_jobs.append(((run, ctx, "average_policy"), sols[(run, "average")], dyn, s))
        for s in SEEDS:
            roll_jobs.append(((run, "average", "average_policy"), sols[(run, "average")], None, s))
    rolls = {}
    with ProcessPoolExecutor(a.procs) as ex:
        for key, seed, r in ex.map(_roll, roll_jobs, chunksize=1):
            rolls.setdefault(key, {})[seed] = r
    print(f"rollouts done ({time.time() - t0:.0f}s)", flush=True)
    res = dict(design="STUDY_PLAN.md Part 2 (Revision 1)", seeds=list(SEEDS), starts_per_seed=N_STARTS,
               world="sweep_balance baseline, variant main (E1 + E2 bins, discount 0.95), no warm bush",
               hazard_source=os.path.relpath(a.hazard, ROOT), per_agent={})
    for run in runs:
        tag = "ordinary" if run == hz["primary_run"] else "modulator"
        per = {}
        for ctx in hz["contexts"][run]:
            c = rolls[(run, ctx, "context_policy")]; v = rolls[(run, ctx, "average_policy")]
            pc = np.mean([c[s]["survival_share"] for s in SEEDS]); pv = np.mean([v[s]["survival_share"] for s in SEEDS])
            n = N_STARTS * len(SEEDS)
            se = np.sqrt(pc * (1 - pc) / n + pv * (1 - pv) / n)
            d = (pc - pv) * 100; lo, hi = d - 196 * se, d + 196 * se
            per[ctx] = dict(
                episodes=hz["contexts"][run][ctx]["episodes"],
                injury_per_exposed_step=hz["contexts"][run][ctx]["injury_per_exposed_step"],
                survival_share=dict(context_policy=float(pc), average_policy=float(pv)),
                mean_survival_steps=dict(context_policy=float(np.mean([c[s]["mean_survival_steps"] for s in SEEDS])),
                                         average_policy=float(np.mean([v[s]["mean_survival_steps"] for s in SEEDS]))),
                value_points=float(d), value_ci95=[float(lo), float(hi)],
                value_points_per_seed=[float((c[s]["survival_share"] - v[s]["survival_share"]) * 100) for s in SEEDS],
                death_cause_share=dict(context_policy=c[0]["death_cause_share"], average_policy=v[0]["death_cause_share"]),
                choice_difference=choice_difference(sols[(run, ctx)], sols[(run, "average")]),
                iters=sols[(run, ctx)]["iters"])
        prim = [per[k] for k in PRIMARY]
        worth = any((p["value_points"] >= 2 and p["value_ci95"][0] > 0) or p["choice_difference"]["0.5"]["category"] >= 0.10
                    for p in prim)
        notw = all(p["value_ci95"][1] < 2 and p["choice_difference"]["0.5"]["category"] < 0.10 for p in prim)
        avg = rolls[(run, "average", "average_policy")]
        res["per_agent"][tag] = dict(run=run, contexts=per,
                                     average_context_self=dict(survival_share=float(np.mean([avg[s]["survival_share"] for s in SEEDS])),
                                                               mean_survival_steps=float(np.mean([avg[s]["mean_survival_steps"] for s in SEEDS]))),
                                     reading_primary=("worth knowing" if worth else "not worth knowing in today's world" if notw
                                                      else "undecided"))
    res["seconds"] = time.time() - t0
    json.dump(res, open(a.out, "w"), indent=1)
    for tag, v in res["per_agent"].items():
        print(tag, v["reading_primary"])
        for ctx, p in v["contexts"].items():
            print(f"  {ctx:14s} value {p['value_points']:6.2f} [{p['value_ci95'][0]:6.2f},{p['value_ci95'][1]:6.2f}]  "
                  f"surv ctx {p['survival_share']['context_policy']:.3f} avg {p['survival_share']['average_policy']:.3f}  "
                  f"choice diff {p['choice_difference']['0.5']['category']:.3f}")


if __name__ == "__main__":
    main()
