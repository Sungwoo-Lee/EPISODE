"""Step-limit (500-step cap) share over training in long level-05 runs and the level-06 pilot (THIRST_TASK check 4)."""
import numpy as np
import wandb

api = wandb.Api(timeout=90)
names = ["rppo_l05body_w0000_t1none_s42", "rppo_l05body_w0000_t16quad_s42",
         "rppo_l06pilot_t1none_s42", "rppo_l06pilot_t16quad_s42"]
for nm in names:
    rs = api.runs("sungwoolee/grid_world_pain", filters={"display_name": nm})
    for r in rs:
        keys = [k for k in r.summary.keys() if k.startswith("Episode/Term_")]
        h = r.history(keys=["Episode/Number", "Episode/Steps"] + keys, samples=2000, pandas=True)
        h = h.dropna(subset=["Episode/Number"]).sort_values("Episode/Number")
        lim = [k for k in keys if "Limit" in k or "Trunc" in k or "Max" in k]
        print(nm, "term keys:", keys)
        ep = h["Episode/Number"].values
        for lo in np.arange(0, ep.max(), 1_000_000 if ep.max() > 3e6 else 200_000):
            m = (ep >= lo) & (ep < lo + (1_000_000 if ep.max() > 3e6 else 200_000))
            if m.sum() == 0:
                continue
            row = f"  {lo / 1e6:4.1f}M steps={h['Episode/Steps'].values[m].mean():6.1f}"
            for k in lim:
                row += f" {k.split('/')[-1]}={np.nanmean(h[k].values[m]):.3f}"
            print(row, flush=True)
