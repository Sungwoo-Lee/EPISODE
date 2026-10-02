"""Measure the level-05 map and hazard numbers the reduced world uses, from the real environment.

Writes results/analysis/internal_state_interactions/world_measurements.json:
  cell temperature by Manhattan distance from the nearest fire (300 real resets)
  trip lengths: from a random open cell, steps to the nearest bush, food item, fire ring
  share of episodes with at least one bush on a fire ring ("warm bush")
  predator hazard: mean damage per step outside / inside a bush, from Wave 2 level-05 training
  recordings (first 10 blocks of each agent's final-checkpoint store)
  discount factor of the level-05 training runs (their saved configs)
  share of active bushes by (Manhattan, Chebyshev) class to the nearest burning fire
  ("bushes_by_fire_class"; BUSH_FIRE_CLEARANCE §A2)

  python measure_world.py --src-root <frozen source tree> --resets 300
  python measure_world.py --src-root <tree> --resets 300 --bush-min-fire-distance 3 --out tmp/<ts>_x.json
  python measure_world.py --hazard-bins-only --blocks 200

--hazard-bins-only (study plan Revision 2a, E2) adds ONE key, "hazard_bins", to the existing
world_measurements.json and leaves every other key untouched (no environment is needed: it reads
only the recordings). Per activity outside cover -- eating (ate_food), resting (rested), moving
(neither; includes staying in place) -- the per-step hit probability and the distribution of hit
sizes (damage > 0) over fixed bins 0-5, 5-15, 15-30, 30-60, 60-100, >=100 (the last is lethal at
any injury), for each agent separately; the ordinary agent (t1none) is primary. Asserts, per
activity, that p(hit) x the binned mean hit size reproduces the recordings' mean damage per step
within 5 %. The full measurement (without the flag) writes the same key as well.

--bush-min-fire-distance N sets thermal.bush_min_fire_distance IN MEMORY after loading
level 05 (no config file is written); it requires --out, so a variant run can never
overwrite the study's world_measurements.json. Without it the script writes exactly as before.
"""
import argparse, glob, json, os, sys
import numpy as np, yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
RUNS = ["20260922-182534_rppo_bq2cover_lvl05_t1none_s42", "20260922-182538_rppo_bq2cover_lvl05_t16quad_s42"]
PRIMARY_RUN = RUNS[0]                     # the ordinary agent: the balance study concerns ordinary agents
MEAS_PATH = os.path.join(ROOT, "results/analysis/internal_state_interactions/world_measurements.json")
# hit-size bins (upper edges inclusive): (0,5], (5,15], (15,30], (30,60], (60,100), [100, inf) lethal
BIN_LABELS = ["0-5", "5-15", "15-30", "30-60", "60-100", ">=100"]
ACTIVITIES = ("eat", "move", "rest")


def _bin_of(x):
    b = np.digitize(x, [5.0, 15.0, 30.0, 60.0], right=True)          # 0..4 for x <= 60, 4 for (60, inf)
    return np.where(x >= 100.0, 5, b)


def measure_hazard_bins(runs, n_blocks, episode_select=None):
    """E2 numbers from the Wave-2 level-05 recordings, per run and activity outside cover.
    Accumulates counts/sums block by block (no whole-store load); also reports the two halves of the
    blocks separately as a stability check.
    episode_select (optional; context-exploration study Part 2): callable(steps_parquet_path) -> array of
    episode seeds whose steps are kept (e.g. the episodes with a given predator count); None = every
    episode, exactly as before."""
    import pyarrow.parquet as pq
    out = {}
    for run in runs:
        fs = sorted(glob.glob(os.path.join(ROOT, f"results/trajectories_basicq2_w2/{run}/*/*/steps_*.parquet")))[:n_blocks]
        if not fs:
            raise SystemExit(f"no step blocks for {run}")
        acc = {h: {a: dict(rows=0, hits=0, dmg=0.0, cnt=np.zeros(6), sz=np.zeros(6)) for a in ACTIVITIES} for h in (0, 1)}
        for k, f in enumerate(fs):
            tb = pq.read_table(f, columns=["t", "damage", "agent_in_bush", "rested", "ate_food"]
                               + (["episode_seed"] if episode_select is not None else []))
            t = tb.column("t").to_numpy(); d = tb.column("damage").to_numpy().astype(np.float64)
            bush = tb.column("agent_in_bush").to_numpy(zero_copy_only=False).astype(bool)
            rst = tb.column("rested").to_numpy(zero_copy_only=False).astype(bool)
            ate = tb.column("ate_food").to_numpy(zero_copy_only=False).astype(bool)
            m = (t >= 1) & ~bush
            if episode_select is not None:
                m = m & np.isin(tb.column("episode_seed").to_numpy(), np.asarray(episode_select(f)))
            sel = {"eat": m & ate, "rest": m & rst & ~ate, "move": m & ~rst & ~ate}
            h = int(k >= len(fs) / 2)
            for a, s in sel.items():
                x = d[s]; hit = x > 0; b = _bin_of(x[hit]); A = acc[h][a]
                A["rows"] += int(s.sum()); A["hits"] += int(hit.sum()); A["dmg"] += float(x.sum())
                A["cnt"] += np.bincount(b, minlength=6); A["sz"] += np.bincount(b, weights=x[hit], minlength=6)
        res = {}
        for a in ACTIVITIES:
            tot = {key: acc[0][a][key] + acc[1][a][key] for key in ("rows", "hits", "dmg", "cnt", "sz")}
            p_hit = tot["hits"] / tot["rows"]
            probs = tot["cnt"] / max(tot["hits"], 1)
            means = np.where(tot["cnt"] > 0, tot["sz"] / np.maximum(tot["cnt"], 1), 0.0)
            mean_dmg = tot["dmg"] / tot["rows"]
            reproduced = p_hit * float((probs * means).sum())
            rel = abs(reproduced - mean_dmg) / mean_dmg if mean_dmg > 0 else 0.0
            halves = [dict(rows=acc[h][a]["rows"], p_hit=acc[h][a]["hits"] / max(acc[h][a]["rows"], 1),
                           mean_damage_per_step=acc[h][a]["dmg"] / max(acc[h][a]["rows"], 1),
                           bin_probs=(acc[h][a]["cnt"] / max(acc[h][a]["hits"], 1)).tolist()) for h in (0, 1)]
            res[a] = dict(rows=tot["rows"], hits=tot["hits"], p_hit=p_hit, bin_labels=BIN_LABELS,
                          bin_counts=tot["cnt"].astype(int).tolist(), bin_probs=probs.tolist(),
                          bin_mean_size=means.tolist(), mean_damage_per_step=mean_dmg,
                          reproduced_mean_damage=reproduced, reproduction_rel_error=rel,
                          reproduction_pass=bool(rel <= 0.05), halves=halves)
            assert rel <= 0.05, f"{run} {a}: p x mean hit {reproduced:.4f} vs recorded {mean_dmg:.4f} ({rel:.1%})"
        out[run] = dict(blocks=len(fs), activities=res)
        print(f"[hazard_bins] {run}: {len(fs)} blocks, rows " +
              ", ".join(f"{a} {res[a]['rows']:,} (p {res[a]['p_hit']:.4f}, mean {res[a]['mean_damage_per_step']:.3f})"
                        for a in ACTIVITIES), flush=True)
    return dict(primary_run=PRIMARY_RUN, source="results/trajectories_basicq2_w2 (Wave-2 level-05 final checkpoints)",
                activity_definition="outside cover (agent_in_bush false), t >= 1; eat = ate_food; rest = rested; "
                                    "move = neither (includes staying in place)",
                bins="(0,5], (5,15], (15,30], (30,60], (60,100), [100,inf) lethal; bin_mean_size = mean hit within the bin",
                runs=out)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--src-root", default=None)
    ap.add_argument("--resets", type=int, default=None)
    ap.add_argument("--hazard-bins-only", action="store_true",
                    help="add only the 'hazard_bins' key to the existing world_measurements.json (no env needed)")
    ap.add_argument("--blocks", type=int, default=200, help="step blocks per run read for hazard_bins")
    ap.add_argument("--bush-min-fire-distance", type=int, default=None,
                    help="set thermal.bush_min_fire_distance in memory (requires --out)")
    ap.add_argument("--out", default=None, help="output JSON path (required with --bush-min-fire-distance)")
    a = ap.parse_args()
    if a.hazard_bins_only:
        p = a.out or MEAS_PATH
        meas = json.load(open(p))
        meas["hazard_bins"] = measure_hazard_bins(RUNS, a.blocks)
        json.dump(meas, open(p, "w"), indent=1)
        print(f"[measure_world] wrote hazard_bins into {p} (other keys unchanged)")
        return
    if a.src_root is None or a.resets is None:
        ap.error("--src-root and --resets are required unless --hazard-bins-only")
    if a.bush_min_fire_distance is not None and a.out is None:
        ap.error("--bush-min-fire-distance requires --out (never overwrite world_measurements.json)")
    os.environ.setdefault("JAX_PLATFORMS", "cpu"); sys.path.insert(0, os.path.abspath(a.src_root))
    import jax
    from src.environment.config_loader import load_env_config, load_env_params
    from src.environment import core
    cfg = load_env_config(os.path.join(a.src_root, "configs/environment/experiment/basic/05-campfire_thermal_10x10.yaml"))
    if a.bush_min_fire_distance is not None:
        cfg.set("thermal.bush_min_fire_distance", a.bush_min_fire_distance)
        print(f"[measure_world] thermal.bush_min_fire_distance set to {a.bush_min_fire_distance} in memory")
    P = load_env_params(cfg)
    reset = jax.jit(core.jax_reset)
    by_d = {}; trips = {"bush": [], "food": [], "ring": []}; warm = []; ring_bush = []
    bush_class = {}

    def fire_class(b, fires):
        m, c = min((abs(int(b[0]) - int(f[0])) + abs(int(b[1]) - int(f[1])),
                    max(abs(int(b[0]) - int(f[0])), abs(int(b[1]) - int(f[1])))) for f in fires)
        return f"({m},{c})" if (m, c) in {(0, 0), (1, 1), (2, 1), (2, 2), (3, 2)} else "far"
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
        foods = np.asarray(st.res_pos)[np.asarray(st.res_active) & (np.asarray(P.res_type) == 0)]
        rings = [(r, c) for r in range(H) for c in range(W) if min(dist((r, c), f) for f in fires) == 1]
        warm.append(any(min(dist(b, f) for f in fires) <= 1 for b in bushes))
        ring_bush.extend(min(dist(b, f) for f in fires) <= 1 for b in bushes)
        for b in bushes:
            k = fire_class(b, fires); bush_class[k] = bush_class.get(k, 0) + 1
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
               share_of_bushes_on_a_fire_ring=float(np.mean(ring_bush)),
               bushes_by_fire_class={k: v / max(1, sum(bush_class.values())) for k, v in sorted(bush_class.items())},
               hazard=hazard, gamma=gammas, hazard_bins=measure_hazard_bins(RUNS, a.blocks))
    p = a.out or MEAS_PATH
    os.makedirs(os.path.dirname(p), exist_ok=True); json.dump(out, open(p, "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
