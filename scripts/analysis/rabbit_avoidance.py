#!/usr/bin/env python
"""Hypervigilance as injury-dependent AVOIDANCE of a harmless animal, measured by distance.

THE PROJECT'S DEFINITION. Hypervigilance is injury-state-dependent avoidance: a badly injured agent
avoids the harmless rabbit more than a lightly injured one. Nothing is compared with the predator.
Avoidance is read two ways across the project; this script supplies the DISTANCE reading (the hiding
reading -- extra time in a bush when the rabbit is near -- already comes from the Sensor Ladder
aggregate's `rd` / `rdc` grids):
  * near_share -- share of steps on which the nearest live rabbit is within NEAR squares (Chebyshev);
  * mean_dist  -- mean distance to the nearest live rabbit, capped at DMAX.
Avoiding the rabbit more shows up as LOWER near_share and HIGHER mean_dist.

WHICH STEPS. Only episodes that contain a rabbit, and only steps on which NO predator is within NEAR
squares -- otherwise distance from the rabbit would partly be the agent fleeing a predator. The t=0
row is excluded. Distances are read on the row the action was chosen from (row t-1), as elsewhere.

TWO INJURY READINGS, reported separately:
  * `start`  -- binned by the STARTING injury the environment assigned at random (levels 03-06):
                causal. First EARLY steps only, while the assigned wound is still largely intact.
  * `current`-- binned by the injury on the deciding row, every step: observational (an injured agent
                was usually just attacked, which confounds it).
Bins are injury quarters 0-25, 25-50, 50-75, 75-100. The SHIFT is the top quarter minus the bottom one.

USAGE
    python scripts/analysis/rabbit_avoidance.py --run results/JAX_RecurrentPPO/<run> \
        --store-root results/trajectories_basicq2_w2 --out out.json [--max-blocks N]
"""
import argparse, json, os, sys, time
import numpy as np
import pyarrow.parquet as pq
import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hiding_drivers import slot_layout, find_stores, shard_files, listcol   # noqa: E402

NEAR, DMAX, EARLY = 2, 8, 25
EDGES = [25.0, 50.0, 75.0]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", required=True); ap.add_argument("--checkpoint", default=None)
    ap.add_argument("--store-root", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-blocks", type=int, default=None, help="read only the first N blocks (testing)")
    a = ap.parse_args()
    cfg = yaml.safe_load(open(f"{a.run}/models/config.yaml"))
    lay = slot_layout(cfg); P, R = lay["pred"], lay["neutral"]; na = len(P) + len(R)
    if not R:
        raise SystemExit("this world has no rabbit slots -- rabbit avoidance is undefined")
    stores = find_stores(a.run, a.checkpoint, a.store_root)
    ef = shard_files(stores, "episodes"); sf = shard_files(stores, "steps")
    if a.max_blocks is not None:
        ef, sf = ef[:a.max_blocks], sf[:a.max_blocks]
    ep = pq.read_table(ef, columns=["episode_seed", "animal_active"])
    eseed = ep.column("episode_seed").to_numpy(); o = np.argsort(eseed)
    seed0 = int(eseed[o][0])
    act = np.array(ep.column("animal_active").to_pylist(), bool)[o]
    has_r = act[:, R].any(1)
    acc = {k: {"n": np.zeros(4), "near": np.zeros(4), "dsum": np.zeros(4)} for k in ("start", "current")}
    t0 = time.time()
    for fi, f in enumerate(sf):
        tb = pq.read_table(f, columns=["episode_seed", "t", "injury_level", "agent_row", "agent_col",
                                       "animal_row", "animal_col"])
        sd = tb.column("episode_seed").to_numpy(); t = tb.column("t").to_numpy(); N = len(t)
        inj = tb.column("injury_level").to_numpy(zero_copy_only=False).astype(float)
        ar = tb.column("agent_row").to_numpy().astype(float); ac = tb.column("agent_col").to_numpy().astype(float)
        AR = listcol(tb.column("animal_row"), na).astype(float); AC = listcol(tb.column("animal_col"), na).astype(float)
        live = act[sd - seed0]
        d = np.where(live, np.maximum(np.abs(AR - ar[:, None]), np.abs(AC - ac[:, None])), np.inf)
        dp = d[:, P].min(1) if P else np.full(N, np.inf); dr = np.minimum(d[:, R].min(1), DMAX)
        st = np.flatnonzero(t == 0); ends = np.append(st[1:], N)
        start_inj = np.repeat(inj[st], ends - st)
        prev = np.arange(N) - 1                         # the row the action was chosen on
        ok = (t >= 1) & has_r[sd - seed0]
        prev = np.where(ok, prev, 0)
        ok &= np.isfinite(dr[prev]) & (dp[prev] > NEAR)
        for key, binv, extra in (("start", start_inj, t <= EARLY), ("current", inj[prev], np.ones(N, bool))):
            m = ok & extra
            b = np.digitize(binv[m], EDGES); dd = dr[prev][m]
            np.add.at(acc[key]["n"], b, 1.0); np.add.at(acc[key]["near"], b, (dd <= NEAR).astype(float))
            np.add.at(acc[key]["dsum"], b, dd)
        if fi % 40 == 0:
            print(f"  shard {fi}/{len(sf)} ({time.time()-t0:.0f}s)", flush=True)
    out = {"run": a.run, "stores": stores, "near": NEAR, "dmax": DMAX, "early": EARLY, "edges": EDGES}
    for key, A in acc.items():
        n = A["n"]; ns = np.where(n > 5000, 100 * A["near"] / np.maximum(n, 1), np.nan)
        md = np.where(n > 5000, A["dsum"] / np.maximum(n, 1), np.nan)
        out[key] = {"n": n.tolist(), "near_share_pct": ns.tolist(), "mean_dist": md.tolist(),
                    "near_share_shift": float(ns[3] - ns[0]), "mean_dist_shift": float(md[3] - md[0])}
    json.dump(out, open(a.out, "w"), indent=1)
    print(f"written: {a.out}")
    for key in ("start", "current"):
        print(f"  {key:8} near% {np.round(out[key]['near_share_pct'],1)}  dist {np.round(out[key]['mean_dist'],2)}")


if __name__ == "__main__":
    main()
