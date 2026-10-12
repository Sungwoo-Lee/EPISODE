#!/usr/bin/env python3
"""by_predator_count.py - episode outcome by the number of predators present (visible animals, and hidden
predators = disguised food slots), from each store's episode table. Exploratory, 2026-10-11.

Promoted 2026-10-12 from tmp/20261011_foraging_deaths/by_predator_count.py (unchanged code) so the 'Hide or Forage Balance' page is reproducible
from the repo. It reads the trajectory stores (results/trajectories_*/**/_manifest.json + parquet shards);
its output for the 27 stores of 2026-10-11 is kept at docs/experiments/active/rebalance_planner/figures/data/,
which is what the page's figure scripts read -- they never re-read the stores."""
import glob, json, os, sys
from multiprocessing import Pool
import numpy as np, pyarrow.parquet as pq, pyarrow.compute as pc

def one(d):
    man = json.load(open(os.path.join(d, "_manifest.json")))
    A, R = man["dims"]["A"], man["dims"]["R"]
    pred = np.asarray(man["animal_classes"]) == "predator"
    hid = np.asarray(man["res_type"]) == 1
    out = {}
    for f in sorted(glob.glob(os.path.join(d, "episodes_*.parquet"))):
        t = pq.read_table(f, columns=["termination_reason", "animal_active", "res_allocated"])
        aa = pc.list_flatten(t.column("animal_active")).to_numpy(zero_copy_only=False).reshape(-1, A)
        ra = pc.list_flatten(t.column("res_allocated")).to_numpy(zero_copy_only=False).reshape(-1, R)
        nv, nh = aa[:, pred].sum(1), ra[:, hid].sum(1)
        tr = t.column("termination_reason").to_numpy()
        for v, h, r in zip(*np.unique(np.c_[nv, nh, tr], axis=0, return_counts=False).T, ) if False else []:
            pass
        key = nv * 10000 + nh * 100 + tr
        u, c = np.unique(key, return_counts=True)
        for k, n in zip(u, c):
            out[int(k)] = out.get(int(k), 0) + int(n)
    name = d.split("/")[1].replace("trajectories_", "") + "/" + d.split("/")[2][16:]
    return name, out

if __name__ == "__main__":
    ds = sorted(os.path.dirname(m) for r in sys.argv[2:] for m in glob.glob(os.path.join(r, "**", "_manifest.json"), recursive=True))
    with Pool(14) as p:
        res = dict(p.map(one, ds))
    json.dump(res, open(sys.argv[1], "w"))
