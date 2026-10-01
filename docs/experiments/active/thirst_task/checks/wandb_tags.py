"""Are the THIRST_TASK tags / group unused in WandB?"""
import wandb

api = wandb.Api(timeout=90)
hits = list(api.runs("sungwoolee/grid_world_pain",
                     filters={"$or": [{"display_name": {"$regex": "rppo_thirst_"}}, {"group": "thirst_task"}]}))
print("runs named rppo_thirst_* or in group thirst_task:", len(hits), [r.name for r in hits[:10]])
