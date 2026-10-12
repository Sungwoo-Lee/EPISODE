"""Reduce the one-predator episode table to a small JSON the page and the planner mappings read.

Input: the episode table written by one_predator_traits.py -- level-05-world episodes with exactly one
visible predator (6,674,860 episodes from 20 stores on 2026-10-11: the two Wave-2 level-05 agents and the
18 agents of the single-channel-smell study, all on the level-05 map with predator sight 1-7 and pounce
2-3). Output: counts per (sight = detection_range, pounce = attack_range, number of traps), with episodes,
total steps and endings by termination reason (1 survived 500 steps, 2 starvation, 3 over-eating,
4 injury, 5 cold). Nothing is estimated here; mappings.py and figure a5 compute from these counts.

  python one_predator_aggregate.py --parquet tmp/20261011_foraging_deaths/one_predator_l05.parquet
"""
import argparse, json, os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
OUT = os.path.join(ROOT, "docs/experiments/active/rebalance_planner/figures/data/one_predator_l05_by_sight_pounce.json")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--parquet", required=True); a = ap.parse_args()
    D = pd.read_parquet(a.parquet, columns=["reason", "length", "n_hidden", "detect", "attack_range"])
    rows = []
    for (d, r, h), g in D.groupby(["detect", "attack_range", "n_hidden"]):
        rc = g.reason.value_counts()
        rows.append(dict(sight=int(d), pounce=int(r), traps=int(h), episodes=int(len(g)), steps=int(g.length.sum()),
                         endings={str(int(k)): int(v) for k, v in rc.items()}))
    out = dict(source=os.path.relpath(os.path.abspath(a.parquet), ROOT), episodes=int(len(D)), steps=int(D.length.sum()),
               reasons={"1": "survived 500 steps", "2": "starvation", "3": "over-eating", "4": "injury", "5": "cold"},
               stores="20 level-05-world stores: basicq2_w2 lvl05 t1none/t16quad + 18 hvsmell agents (2026-10-11)",
               rows=rows)
    json.dump(out, open(OUT, "w"), indent=0)
    print(f"{len(rows)} cells, {out['episodes']:,} episodes -> {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
