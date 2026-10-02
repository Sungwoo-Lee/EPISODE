"""Rough map from bush count to the typical trip to the nearest bush on the 10x10 level-05 map.

Uniform placement of the agent and k bushes on distinct cells (no edge margin, no other obstacles),
4,000 draws per count; Manhattan distance, which equals path length here (nothing blocks movement).
A quick estimate for reading the planner's "trip to cover" axis, not a measurement of real resets.
Writes results/analysis/internal_state_interactions/bush_trip_estimate.json.
"""
import json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "..", "..", "results/analysis/internal_state_interactions/bush_trip_estimate.json")
rng = np.random.default_rng(0)
cells = [(r, c) for r in range(10) for c in range(10)]
res = {}
for k in (1, 2, 3, 4, 6, 10):
    d = []
    for _ in range(4000):
        pts = [cells[i] for i in rng.choice(100, k + 1, replace=False)]
        a = pts[0]
        d.append(min(abs(a[0] - b[0]) + abs(a[1] - b[1]) for b in pts[1:]))
    res[str(k)] = dict(median=float(np.median(d)), mean=float(np.mean(d)), p90=float(np.percentile(d, 90)))
json.dump(res, open(OUT, "w"), indent=1)
print(json.dumps(res, indent=1))
