"""FIGURE 5 — Does either agent's behaviour depend on COMBINATIONS of body states?

Measure 4 of the design doc (§4.1), the behavioural combination gain: each decision step is labelled
with the agent's activity (eating, in cover, on a fire ring, in the open); the best predictor of
that activity from ONE body variable (nutrition, injury or body temperature, 10 fixed bins each) is
compared with the best predictor from TWO; gain = pair accuracy minus single accuracy, in
percentage points. Read from combination_gain.json (behavioural_combination_gain.py); nothing is
recomputed. Left: which rules are on. Middle: both agents. Right: modulator minus ordinary.
No interval: the source keeps only the totals per run.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import _common as C, _perworld as P

C.house.apply()
d = C.load("combination_gain.json")
runs = d["runs"]
vals = {w: (runs[f"{w}_ordinary"]["final"]["gain_points"], runs[f"{w}_modulated"]["final"]["gain_points"])
        for w in C.WORLDS}
for w in C.WORLDS:                                          # the per-world table must agree with the runs
    assert abs(d["worlds"][w]["D_gain_points"] - (vals[w][1] - vals[w][0])) < 1e-9
gaps = np.array([m - o for o, m in vals.values()])
fig, ax = P.draw(vals, "modulator minus\nordinary (points)", "combination gain: two body variables\nminus one (percentage points)",
                 (1.5, 5.5), (-1.5, 1.5))
C.record_kind("f5_combination", "recordings")
N = [runs[f"{w}_{a}"]["final"]["N"] for w in C.WORLDS for a in ("ordinary", "modulated")]
drop = sum(sum(v["rows"] for v in runs[f"{w}_{a}"]["final"]["dropped"].values())
           for w in C.WORLDS for a in ("ordinary", "modulated"))
rows = [dict(what="evaluation episodes (32 runs x 1,000,000)", used=32 * 1_000_000, total=32 * 1_000_000,
             note="final checkpoint, greedy policy, one recording per run"),
        dict(what="decision steps used, all runs", used=sum(N) - drop, total=sum(N),
             note=f"{drop:,} steps in body-variable bins under 200 steps were dropped; decision steps are the states the policy acted from"),
        dict(what="worlds where the modulator's gain is higher", used=int((gaps > 0).sum()), total=16,
             note=f"gap {gaps.min():+.2f} to {gaps.max():+.2f} points")]
C.record_samples("f5_combination", rows)
print(f"  gain ord {min(v[0] for v in vals.values()):.2f}-{max(v[0] for v in vals.values()):.2f}; gap {gaps.min():.2f}..{gaps.max():.2f}, >0 in {(gaps>0).sum()}")
C.save(fig, "f5_combination")
