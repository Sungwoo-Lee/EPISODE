"""Measure the level-05 map and hazard numbers the reduced world uses, from the real environment.

Writes results/analysis/internal_state_interactions/world_measurements.json:
  cell temperature by Manhattan distance from the nearest fire (300 real resets)
  trip lengths: from a random open cell, steps to the nearest bush, food item, fire ring
  share of episodes with at least one bush on a fire ring ("warm bush")
  predator hazard: mean damage per step outside / inside a bush, from Wave 2 level-05 training
  recordings (first 10 blocks of each agent's final-checkpoint store)
  discount factor of the level-05 training runs (their saved configs)

  python measure_world.py --src-root <frozen source tree> --resets 300
"""
import argparse, glob, json, os, sys
import numpy as np, yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
RUNS = ["20260922-182534_rppo_bq2cover_lvl05_t1none_s42", "20260922-182538_rppo_bq2cover_lvl05_t16quad_s42"]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--src-root", required=True)
    ap.add_argument("--resets", type=int, required=True); a = ap.parse_args()
    os.environ.setdefault("JAX_PLATFORMS", "cpu"); sys.path.insert(0, os.path.abspath(a.src_root))
    import jax
    from src.environment.config_loader import load_env_config, load_env_params
    from src.environment import core
    P = load_env_params(load_env_config(os.path.join(a.src_root, "configs/environment/experiment/basic/05-campfire_thermal_10x10.yaml")))
    reset = jax.jit(core.jax_reset)
    by_d = {}; trips = {"bush": [], "food": [], "ring": []}; warm = []; ring_bush = []
    rng = np.random.default_rng(0)
    for s in range(a.resets):
        st = reset(P, jax.random.PRNGKey(s)); F = np.asarray(st.thermal_field)
        fires = np.argwhere(F > 40)
        dist = lambda p, q: abs(int(p[0]) - int(q[0])) + abs(int(p[1]) - int(q[1]))
        H, W = F.shape
        for r in range(H):
            for c in range(W):
                d = min(dist((r, c), f) for f in fires)
                by_d.setdefault(min(d, 4), []).append(float(F[r, c]))
        hides = np.asarray(P.obs_hides_agent) & np.asarray(st.obs_active)
        bushes = np.asarray(st.obs_pos)[hides]
        # food items only: res_type 1 is an ambush predator (plan-reviewer / env-config-reviewer 2026-09-26)
        foods = np.asarray(st.res_pos)[np.asarray(st.res_active) & (np.asarray(st.res_type) == 0)]
        rings = [(r, c) for r in range(H) for c in range(W) if min(dist((r, c), f) for f in fires) == 1]
        warm.append(any(min(dist(b, f) for f in fires) <= 1 for b in bushes))
        ring_bush.extend(min(dist(b, f) for f in fires) <= 1 for b in bushes)
        occupied = {tuple(b) for b in bushes} | {tuple(f) for f in fires}
        for _ in range(20):                                  # random open cells
            p = (int(rng.integers(1, H - 1)), int(rng.integers(1, W - 1)))
            if p in occupied:
                continue
            if len(bushes): trips["bush"].append(min(dist(p, b) for b in bushes))
            if len(foods): trips["food"].append(min(dist(p, f) for f in foods))
            if rings: trips["ring"].append(min(dist(p, q) for q in rings))
    import pyarrow.parquet as pq
    hazard = {}
    for run in RUNS:
        fs = sorted(glob.glob(os.path.join(ROOT, f"results/trajectories_basicq2_w2/{run}/*/*/steps_*.parquet")))[:10]
        d, b, t, rs = [], [], [], []
        for f in fs:
            tb = pq.read_table(f, columns=["t", "damage", "agent_in_bush", "rested"])
            d.append(tb.column("damage").to_numpy()); b.append(tb.column("agent_in_bush").to_numpy(zero_copy_only=False))
            t.append(tb.column("t").to_numpy()); rs.append(tb.column("rested").to_numpy(zero_copy_only=False))
        d, b, t, rst = np.concatenate(d), np.concatenate(b).astype(bool), np.concatenate(t), np.concatenate(rs).astype(bool)
        m = t >= 1
        # split outside cover by whether the agent rested that step (plan-reviewer R3): the rest-vs-cover
        # choice hinges on the resting rate. Selection caveat: agents choose where they rest.
        hazard[run] = dict(open=float(d[m & ~b].mean()), bush=float(d[m & b].mean()),
                           open_resting=float(d[m & ~b & rst].mean()), open_not_resting=float(d[m & ~b & ~rst].mean()),
                           open_hit_share=float((d[m & ~b] > 0).mean()), rows=int(m.sum()))
    gammas = {run: yaml.safe_load(open(os.path.join(ROOT, "results/JAX_RecurrentPPO", run, "models/config.yaml")))["agent"]["gamma"]
              for run in RUNS}
    out = dict(resets=a.resets,
               cell_temp_by_fire_distance={str(k): dict(median=float(np.median(v)), p10=float(np.percentile(v, 10)),
                                                        p90=float(np.percentile(v, 90))) for k, v in sorted(by_d.items())},
               trip_steps={k: dict(median=float(np.median(v)), mean=float(np.mean(v)), p90=float(np.percentile(v, 90)))
                           for k, v in trips.items()},
               warm_bush_episode_share=float(np.mean(warm)),
               share_of_bushes_on_a_fire_ring=float(np.mean(ring_bush)), hazard=hazard, gamma=gammas)
    p = os.path.join(ROOT, "results/analysis/internal_state_interactions/world_measurements.json")
    os.makedirs(os.path.dirname(p), exist_ok=True); json.dump(out, open(p, "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
