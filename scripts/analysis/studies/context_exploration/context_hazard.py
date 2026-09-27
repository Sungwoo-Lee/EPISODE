"""Part 2a of the context-exploration study: predator hit bins per episode context.

Plain-language purpose: how dangerous is a step outside cover when the episode has 0, 1 or 2 hunting
predators? This script measures, from the Wave-2 level-05 recordings of both agents, the chance of a
hit per step outside cover and the distribution of hit sizes, per activity (eating / moving / resting),
separately for each context -- with the balance study's own `measure_hazard_bins`, restricted to the
episodes of that context. Secondary: the same crossed with the ambusher band (low 2-5 / high 9-12).
The pooled bins (all episodes) are the balance study's, already in world_measurements.json.

Check (STUDY_PLAN.md Part 2): injury per exposed step (all activities outside cover) of the ordinary
agent must reproduce the plan-review figures 0.20 / 1.11 / 2.62 for 0 / 1 / 2 predators within 5 %.

  python context_hazard.py --procs 16 --out results/analysis/context_exploration/part2_context_hazard.json
"""
import argparse, glob, json, os, sys, time
from concurrent.futures import ProcessPoolExecutor
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts", "analysis", "studies", "internal_state_interactions"))
import measure_world as MW                          # noqa: E402

REVIEW_INJURY_PER_EXPOSED_STEP = {0: 0.20, 1: 1.11, 2: 2.62}
BANDS = {"low": (2, 5), "high": (9, 12)}


def _episode_context(ep_path, run):
    import pyarrow.parquet as pq
    man = json.load(open(glob.glob(os.path.join(os.path.dirname(ep_path), "_manifest.json"))[0]))
    et = pq.read_table(ep_path, columns=["episode_seed", "animal_active", "res_allocated"])
    n = et.num_rows
    aa = np.asarray(et.column("animal_active").combine_chunks().flatten()).reshape(n, -1)
    ra = np.asarray(et.column("res_allocated").combine_chunks().flatten()).reshape(n, -1)
    ps = np.array([c == "predator" and b == "hunt" for c, b in zip(man["animal_classes"], man["animal_behaviours"])])
    n_pred = aa[:, ps].sum(1)
    n_amb = (ra & (np.array(man["res_type"]) == 1)[None, :]).sum(1)
    return et.column("episode_seed").to_numpy(), n_pred, n_amb


class Select:
    """episode_select callable for measure_hazard_bins: episodes with `pred` hunting predators and,
    optionally, an ambusher count inside `band`."""
    def __init__(self, run, pred, band=None):
        self.run, self.pred, self.band = run, pred, band
        self.n_episodes = 0

    def __call__(self, steps_path):
        seeds, n_pred, n_amb = _episode_context(steps_path.replace("steps_", "episodes_"), self.run)
        m = n_pred == self.pred
        if self.band is not None:
            m &= (n_amb >= self.band[0]) & (n_amb <= self.band[1])
        self.n_episodes += int(m.sum())
        return seeds[m]


def job(args):
    run, ctx, pred, band, blocks = args
    t0 = time.time()
    sel = Select(run, pred, BANDS[band] if band else None)
    hb = MW.measure_hazard_bins([run], blocks, episode_select=sel)
    acts = hb["runs"][run]["activities"]
    rows = sum(acts[a]["rows"] for a in acts)
    dmg = sum(acts[a]["mean_damage_per_step"] * acts[a]["rows"] for a in acts)
    return run, ctx, dict(predators=pred, ambusher_band=band, episodes=sel.n_episodes, exposed_steps=rows,
                          injury_per_exposed_step=dmg / rows, hazard_bins=hb, seconds=time.time() - t0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--procs", type=int, required=True)
    ap.add_argument("--blocks", type=int, default=200)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    jobs = []
    for run in MW.RUNS:
        for p in (0, 1, 2):
            jobs.append((run, f"pred{p}", p, None, a.blocks))
            for b in BANDS:
                jobs.append((run, f"pred{p}_amb{b}", p, b, a.blocks))
    res = {run: {} for run in MW.RUNS}
    with ProcessPoolExecutor(a.procs) as ex:
        for run, ctx, r in ex.map(job, jobs):
            res[run][ctx] = r
            print(f"{run[-20:]} {ctx}: episodes {r['episodes']:,}, exposed steps {r['exposed_steps']:,}, "
                  f"injury/exposed step {r['injury_per_exposed_step']:.3f} ({r['seconds']:.0f}s)", flush=True)
    # pooled (balance study) bins for reference
    meas = json.load(open(MW.MEAS_PATH))
    pooled = {}
    for run in MW.RUNS:
        acts = meas["hazard_bins"]["runs"][run]["activities"]
        rows = sum(acts[x]["rows"] for x in acts)
        pooled[run] = dict(injury_per_exposed_step=sum(acts[x]["mean_damage_per_step"] * acts[x]["rows"] for x in acts) / rows,
                           blocks=meas["hazard_bins"]["runs"][run]["blocks"])
    chk = {}
    for p, ref in REVIEW_INJURY_PER_EXPOSED_STEP.items():
        v = res[MW.PRIMARY_RUN][f"pred{p}"]["injury_per_exposed_step"]
        chk[str(p)] = dict(new=v, review=ref, rel_error=abs(v - ref) / ref, pass_=bool(abs(v - ref) / ref <= 0.05))
    out = dict(design="STUDY_PLAN.md Part 2 (Revision 1): contexts = hunting-predator count 0/1/2 (primary), "
                      "x ambusher band low 2-5 / high 9-12 (secondary)",
               blocks=a.blocks, primary_run=MW.PRIMARY_RUN, contexts=res, pooled_reference=pooled,
               review_check=dict(checks=chk, pass_=all(c["pass_"] for c in chk.values()),
                                 note="ordinary agent, injury per exposed step (all activities outside cover, t >= 1)"))
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(out, open(a.out, "w"), indent=1)
    print(json.dumps(out["review_check"], indent=1))


if __name__ == "__main__":
    main()
