"""Throughput (env steps / s) of level-05 and thirst-pilot runs, by card (THIRST_TASK design, check 5)."""
import wandb

api = wandb.Api(timeout=90)
runs = api.runs("sungwoolee/grid_world_pain",
                filters={"$or": [{"group": "level05_body_interactions"}, {"group": "thirst_pilot"}]},
                per_page=100)
for r in runs:
    s = r.summary
    md = r.metadata or {}
    rt = s.get("_runtime")
    ts = s.get("timesteps")
    if not rt or not ts:
        continue
    print(f"{r.name:45s} {md.get('gpu', '?'):28s} {md.get('host', '?'):12s} {ts / rt:8.0f} steps/s "
          f"ep={s.get('Episode/Number')} h={rt / 3600:.2f} steps={ts / 1e6:.0f}M", flush=True)
