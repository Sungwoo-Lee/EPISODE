"""Two follow-up checks quoted in the thirst page's prose (plan-reviewer findings 2 and 5).

  python extras.py   # writes results/analysis/thirst_water/extras.json (under a minute)

  overdrink_by_refill_target: at gain 20.625, the share of episodes dying of over-drinking when the
      scripted agent drinks until 160 (the page's agent), 140 or 120 -- how much is the agent's choice.
  early_thirst_must_find: the start-hydration run (20,000 episodes, seed 15) repeated for the agent that
      must find the pond: share dead of thirst by step 10, by step 16, and overall.
"""
import json, os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import _common as C
import watersim as S

out = {"overdrink_by_refill_target": {}}
for wh in (160, 140, 120):
    r = S.run(S.World(w_hi=float(wh), water=S.Water(gain=20.625)), E=2000, seed=14)
    out["overdrink_by_refill_target"][str(wh)] = float(np.mean(r["cause"] == 2))
r = S.run(S.World(search=True), E=20000, seed=15); c, l = r["cause"], r["life"]
out["early_thirst_must_find"] = dict(by10=float(np.mean((c == 1) & (l <= 10))), by16=float(np.mean((c == 1) & (l <= 16))),
                                     overall=float(np.mean(c == 1)), E=20000)
json.dump(out, open(os.path.join(C.OUT, "extras.json"), "w"), indent=1)
print(out)
