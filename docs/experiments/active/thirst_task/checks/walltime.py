"""Wall time per run at 10M episodes and GPU-hour total for the 18-run THIRST_TASK design (check 5).

Inputs (all measured, WandB, see wandb_speed.py output):
  10x10 level 06, RTX 2080 Ti: ordinary 30.7-31.3k env steps/s (pilot, 3 runs) -> 31.0k;
                               modulated 23.3-23.7k (pilot, 3 runs) -> 23.4k.
  10x10 RTX 3090: level 05 ordinary 2M pilots 42.3-44.5k (median ~43.0k); level 05 modulated
                  10M runs 30.0-35.5k (median ~34.4k, excluding one 23.3k outlier). Water costs
                  4.7 % (pilot, same node same time) -> ordinary 41.0k, modulated 32.8k.
  Size factor (RTX 4090, ordinary, context-exploration runs, same trainer):
      10x10 level 05 53.3k; 15x15 (C7) 39.4k -> 0.74; 20x20 (C4 25.5k, C3 26.0k) -> 0.48.
      Applied to BOTH agents. For the modulated agent the network is a larger share of each
      step, so the true slow-down from map size is smaller: this errs long.
  Env steps per 10M episodes: level 05 10M runs 1.79-2.30B (base world 2.30B); the level-06
  pilot's first 2M were 0.71x level 05's. Planning value 2.0B, upper 2.3B.
"""
RATE = {("2080Ti", "ord"): 31.0e3, ("2080Ti", "mod"): 23.4e3,
        ("3090", "ord"): 41.0e3, ("3090", "mod"): 32.8e3}
SIZE = {10: 1.00, 15: 0.74, 20: 0.48}
for steps, label in ((2.0e9, "planning 2.0B steps"), (2.3e9, "upper 2.3B steps")):
    print(f"== {label}")
    for card in ("2080Ti", "3090"):
        total = 0.0
        for g, f in SIZE.items():
            h = {a: steps / (RATE[(card, a)] * f) / 3600 for a in ("ord", "mod")}
            total += 3 * (h["ord"] + h["mod"])          # three smell reaches per size
            print(f"  {card} {g}x{g}: ordinary {h['ord']:.1f} h, modulated {h['mod']:.1f} h")
        print(f"  {card} TOTAL 18 runs: {total:.0f} GPU-h")
