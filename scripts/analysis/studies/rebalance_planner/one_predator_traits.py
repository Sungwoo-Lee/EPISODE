#!/usr/bin/env python3
"""one_predator_traits.py - in episodes with exactly one visible predator, compare that predator's sampled
traits between episodes the agent survived to max steps and episodes it died of injury. Exploratory, 2026-10-11.

Promoted 2026-10-12 from tmp/20261011_foraging_deaths/one_predator_traits.py (unchanged code) so the 'Hide or Forage Balance' page is reproducible
from the repo. It reads the trajectory stores (results/trajectories_*/**/_manifest.json + parquet shards);
its output for the 27 stores of 2026-10-11 is kept at docs/experiments/active/rebalance_planner/figures/data/,
which is what the page's figure scripts read -- they never re-read the stores."""
import glob, json, os, sys
from multiprocessing import Pool
import numpy as np, pandas as pd, pyarrow.parquet as pq, pyarrow.compute as pc

TRAITS = ["animal_detect_sampled", "animal_max_stamina_sampled", "animal_recovery_sampled", "animal_hunt_thresh_sampled",
          "animal_lose_interest_sampled", "animal_move_int_sampled", "animal_attack_delay_sampled",
          "animal_attack_range_sampled"]

def one(d):
    man = json.load(open(os.path.join(d, "_manifest.json")))
    A, R = man["dims"]["A"], man["dims"]["R"]
    pred = np.asarray(man["animal_classes"]) == "predator"
    hid = np.asarray(man["res_type"]) == 1
    rows = []
    for f in sorted(glob.glob(os.path.join(d, "episodes_*.parquet"))):
        t = pq.read_table(f, columns=["termination_reason", "length", "animal_active", "res_allocated"] + TRAITS)
        aa = pc.list_flatten(t.column("animal_active")).to_numpy(zero_copy_only=False).reshape(-1, A) & pred
        sel = aa.sum(1) == 1
        slot = aa.argmax(1)
        df = pd.DataFrame({"reason": t.column("termination_reason").to_numpy(), "length": t.column("length").to_numpy(),
                           "n_hidden": (pc.list_flatten(t.column("res_allocated")).to_numpy(zero_copy_only=False).reshape(-1, R) & hid).sum(1)})
        for c in TRAITS:
            m = pc.list_flatten(t.column(c)).to_numpy().reshape(-1, A)
            df[c.replace("animal_", "").replace("_sampled", "")] = m[np.arange(len(m)), slot]
        rows.append(df[sel])
    return pd.concat(rows)

if __name__ == "__main__":
    ds = sorted(os.path.dirname(m) for r in sys.argv[2:] for m in glob.glob(os.path.join(r, "**", "_manifest.json"), recursive=True))
    with Pool(14) as p:
        D = pd.concat(p.map(one, ds))
    D.to_parquet(sys.argv[1])
    print(len(D), "episodes with one visible predator from", len(ds), "stores")
