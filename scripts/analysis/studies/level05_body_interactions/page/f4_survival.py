"""FIGURE 4 — How long does each agent survive in each world?

Survival steps = the pre-registered measure 2 (design doc §4.1): mean episode length over the last
10 % of training (episodes 9 M - 10 M), weighted by each logged row's episode count
(Episode/_window_n), from the local WandB binaries. Read from factorial_effects.json (written by
factorial_effects.py); nothing is recomputed. Left: which of the four body rules are on in each
world. Middle: both agents. Right: modulator minus ordinary.
No interval is drawn: each value is one training run (one seed), and the logged window means carry
no per-episode spread.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import _common as C, _perworld as P

C.house.apply()
d = C.load("factorial_effects.json")
sw = d["measures"]["survival_wandb"]["worlds"]
vals = {w: (sw[w]["ordinary"], sw[w]["modulated"]) for w in C.WORLDS}
gaps = np.array([m - o for o, m in vals.values()])
fig, ax = P.draw(vals, "modulator minus\nordinary (steps)", "survival steps (mean episode length,\nlast tenth of training)",
                 (170, 265), (-1, 8))
C.record_kind("f4_survival", "training")
meta = d["survival_wandb"]
rows = [dict(what="training runs read (16 worlds x 2 agents)", used=sum(v["status"] == "ok" for v in meta.values()),
             total=len(meta), note="every run reached 10,000,000 episodes"),
        dict(what="logged rows in the last-tenth window, all runs", used=sum(v["rows"] for v in meta.values()),
             total=sum(v["rows"] for v in meta.values()),
             note="episodes 9,000,000-10,000,000 of each run; each row averages a window of episodes"),
        dict(what="worlds where the modulator survives longer", used=int((gaps > 0).sum()), total=16,
             note=f"gap {gaps.min():+.1f} to {gaps.max():+.1f} steps, mean {gaps.mean():+.1f}")]
C.record_samples("f4_survival", rows)
print(f"  gap min {gaps.min():.2f} max {gaps.max():.2f} mean {gaps.mean():.2f}; ordinary {min(v[0] for v in vals.values()):.1f}-{max(v[0] for v in vals.values()):.1f}")
C.save(fig, "f4_survival")
