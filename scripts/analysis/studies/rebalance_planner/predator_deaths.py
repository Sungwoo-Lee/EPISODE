#!/usr/bin/env python3
"""predator_deaths.py - how often do agents die from a predator while foraging? (exploratory, 2026-10-11)

For every 1M-episode trajectory store given, per shard:
  * deaths by cause (episode termination_reason);
  * for injury deaths, the source of the LAST damaging step (visible predator = an animal hit,
    hidden predator = a disguised food item, other = thorn/obstacle damage), and the agent's state then:
    in the bush or out; foraging or not (ate food in the last 20 steps, or the step moved it closer to
    the nearest real food); hunger (satiation before the hit) and distance to the nearest bush;
  * per-step exposure: steps spent in each state, and predator hits / fatal predator hits in each state,
    so risk per 1,000 steps can be compared across states.

    $P scripts/analysis/studies/rebalance_planner/predator_deaths.py --out <json> <store_dir> [<store_dir> ...]


Promoted 2026-10-12 from scripts/analysis/studies/rebalance_planner/predator_deaths.py (unchanged code) so the 'Hide or Forage Balance' page is reproducible
from the repo. It reads the trajectory stores (results/trajectories_*/**/_manifest.json + parquet shards);
its output for the 27 stores of 2026-10-11 is kept at docs/experiments/active/rebalance_planner/figures/data/,
which is what the page's figure scripts read -- they never re-read the stores."""
import argparse
import glob
import json
import os
from multiprocessing import Pool

import numpy as np
import pyarrow.compute as pc
import pyarrow.parquet as pq

COLS = ["episode_seed", "t", "agent_row", "agent_col", "satiation", "injury_level", "damage", "ate_food",
        "hit_predator", "hit_hiding_predator", "agent_in_bush", "termination_reason",
        "res_row", "res_col", "res_active", "obs_row", "obs_col"]
REASONS = {1: "max_steps", 2: "starvation", 3: "overeating", 4: "injury", 5: "thermal", 6: "dehydration",
           7: "overdrinking"}
STATES = ("bush", "out_ate20", "out_toward", "out_other")
SAT_BINS = np.arange(0, 205, 5)
DIST_BINS = np.arange(0, 62, 2)
WIN = 20


def mat(tb, c, w):
    return pc.list_flatten(tb.column(c)).to_numpy().reshape(tb.num_rows, w)


def shard(job):
    path, man = job
    tb = pq.read_table(path, columns=COLS)
    n = tb.num_rows
    R, B = man["dims"]["R"], man["dims"]["B"]
    food_slot = np.asarray(man["res_type"]) == 0
    bush_slot = np.asarray(man["obs_hides_agent"], bool)
    g = {c: tb.column(c).to_numpy(zero_copy_only=False) for c in COLS[:12]}
    t = g["t"].astype(np.int64)
    ar, ac = g["agent_row"].astype(np.int32), g["agent_col"].astype(np.int32)
    rr, rc, ra = mat(tb, "res_row", R).astype(np.int32), mat(tb, "res_col", R).astype(np.int32), mat(tb, "res_active", R)
    orow, ocol = mat(tb, "obs_row", B).astype(np.int32), mat(tb, "obs_col", B).astype(np.int32)
    idx = np.arange(n)
    start = idx - t                               # row of t=0 for each row (rows are sorted by seed, t)
    # bush cells: concealing slots that exist this episode (episode table obs_active; inactive slots are parked)
    ep = pq.read_table(path.replace("steps_", "episodes_"), columns=["episode_seed", "obs_active"])
    eseed = ep.column("episode_seed").to_numpy()
    oact = pc.list_flatten(ep.column("obs_active")).to_numpy(zero_copy_only=False).reshape(ep.num_rows, B)
    order = np.argsort(eseed)
    erow = order[np.searchsorted(eseed[order], g["episode_seed"])]
    assert (eseed[erow] == g["episode_seed"]).all()
    b_r, b_c = orow[start], ocol[start]
    bvalid = bush_slot[None, :] & oact[erow]
    dbush = np.where(bvalid, np.abs(b_r - ar[:, None]) + np.abs(b_c - ac[:, None]), 10 ** 6).min(1)
    # foraging: ate in the last WIN steps, or this step moved closer to the nearest real food active before it
    cs = np.cumsum(g["ate_food"].astype(np.int64))
    k = np.minimum(t, WIN)
    ate_recent = (cs - np.where(idx - k >= 0, cs[np.maximum(idx - k, 0)], 0)) > 0
    prev = np.maximum(idx - 1, 0)
    fvalid = (ra[prev] & food_slot[None, :])
    dprev = np.where(fvalid, np.abs(rr[prev] - ar[prev, None]) + np.abs(rc[prev] - ac[prev, None]), 10 ** 6).min(1)
    dnow = np.where(fvalid, np.abs(rr[prev] - ar[:, None]) + np.abs(rc[prev] - ac[:, None]), 10 ** 6).min(1)
    toward = (dnow < dprev) & (dprev < 10 ** 6)
    live = t >= 1
    inb = g["agent_in_bush"].astype(bool)
    state = np.where(inb, 0, np.where(ate_recent, 1, np.where(toward, 2, 3)))
    vis, hid = g["hit_predator"].astype(bool), g["hit_hiding_predator"].astype(bool)
    anyhit = (vis | hid) & live
    out = {"rows": int(n), "steps": {}, "hits": {}, "fatal": {}, "sat_all_out": np.zeros(len(SAT_BINS) - 1),
           "dist_all_out": np.zeros(len(DIST_BINS) - 1)}
    for si, s in enumerate(STATES):
        m = live & (state == si)
        out["steps"][s] = int(m.sum())
        out["hits"][s] = int((anyhit & m).sum())
    sat_prev = g["satiation"][prev]
    outm = live & ~inb
    out["sat_all_out"] += np.histogram(sat_prev[outm], SAT_BINS)[0]
    out["dist_all_out"] += np.histogram(dbush[outm], DIST_BINS)[0]
    # episodes: last row of each episode
    last = np.r_[np.nonzero(np.diff(g["episode_seed"]))[0], n - 1]
    reason = g["termination_reason"][last]
    out["episodes"] = int(len(last))
    out["reasons"] = {REASONS.get(int(r), str(int(r))): int((reason == r).sum()) for r in np.unique(reason)}
    out["length_sum"] = float(t[last].sum())
    # last damaging step per injury death
    dmg_rows = np.nonzero((g["damage"] > 0) & live)[0]
    seeds = g["episode_seed"]
    inj_last = last[reason == 4]
    # for each injury-death episode, the last damaging row with the same seed
    pos = np.searchsorted(dmg_rows, inj_last, side="right") - 1
    ok = (pos >= 0)
    fr = np.where(ok, dmg_rows[np.maximum(pos, 0)], -1)
    ok &= seeds[np.maximum(fr, 0)] == seeds[inj_last]
    fr = fr[ok]
    src = np.where(vis[fr] & hid[fr], "both", np.where(vis[fr], "visible", np.where(hid[fr], "hidden", "other")))
    fat = out["fatal"]
    fat["injury_deaths"] = int(len(inj_last))
    fat["no_damage_found"] = int((~ok).sum())
    fat["hit_on_last_step"] = int((fr == inj_last[ok]).sum())
    for s in ("visible", "hidden", "both", "other"):
        m = src == s
        fat[s] = {st: int((m & (state[fr] == si)).sum()) for si, st in enumerate(STATES)}
    pm = (src != "other")
    fat["pred_sat_hist"] = np.histogram(sat_prev[fr][pm & (state[fr] != 0)], SAT_BINS)[0]
    fat["pred_dist_hist"] = np.histogram(dbush[fr][pm & (state[fr] != 0)], DIST_BINS)[0]
    fat["pred_gap_hist"] = np.histogram((inj_last[ok] - fr)[pm], np.arange(0, 22, 1))[0]
    fat["pred_inj_before"] = np.histogram(g["injury_level"][prev][fr][pm], np.arange(0, 105, 5))[0]
    return out


def add(a, b):
    if isinstance(a, dict):
        for k, v in b.items():
            a[k] = add(a[k], v) if k in a else v
        return a
    return a + b


def store_dirs(roots):
    for r in roots:
        for m in sorted(glob.glob(os.path.join(r, "**", "_manifest.json"), recursive=True)):
            yield os.path.dirname(m)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--procs", type=int, default=16)
    ap.add_argument("--max-shards", type=int, default=0)
    ap.add_argument("stores", nargs="+")
    a = ap.parse_args()
    res = json.load(open(a.out)) if os.path.exists(a.out) else {}
    with Pool(a.procs) as pool:
        for sd in a.stores:
            for d in store_dirs([sd]):
                name = d.split("/")[1].replace("trajectories_", "") + "/" + d.split("/")[2][16:]
                if name in res:
                    continue
                man = json.load(open(os.path.join(d, "_manifest.json")))
                fs = sorted(glob.glob(os.path.join(d, "steps_*.parquet")))
                if a.max_shards:
                    fs = fs[:a.max_shards]
                tot = None
                for o in pool.imap_unordered(shard, [(f, man) for f in fs]):
                    tot = o if tot is None else add(tot, o)
                tot = json.loads(json.dumps(tot, default=lambda x: x.tolist()))
                tot["shards"] = len(fs)
                res[name] = tot
                json.dump(res, open(a.out, "w"))
                print(name, tot["episodes"], flush=True)


if __name__ == "__main__":
    main()
