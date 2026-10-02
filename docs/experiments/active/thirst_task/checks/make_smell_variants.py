"""Write the six short-smell-reach thirst worlds (THIRST_TASK design). One key each: sensor_radius."""
import os

W = "/media/nas01/projects/Interoceptive-AI/grid_world_pain/.claude/worktrees/thirst"
OUT = os.path.join(W, "configs/environment/experiment/thirst")
PARENTS = {
    10: ("environment/experiment/basic/06-pond_thirst_10x10",
         "level 06 itself (basic/06-pond_thirst_10x10.yaml)", "20"),
    15: ("environment/experiment/thirst/pond_thirst_15x15",
         "the 15 x 15 whole-map world (thirst/pond_thirst_15x15.yaml)", "30"),
    20: ("environment/experiment/thirst/pond_thirst_20x20",
         "the 20 x 20 whole-map world (thirst/pond_thirst_20x20.yaml)", "40"),
}
TEMPLATE = """# EXPERIMENTAL, NOT MAINTAINED (CLAUDE.md "Config maintenance scope"): part of the thirst-task
# design, docs/experiments/active/thirst_task/THIRST_TASK.md.
#
# WORLD pond_thirst_{g}x{g}_smell{r} (THIRST_TASK cell g{g}s{r}): {desc},
# with smell reaching only {r} squares instead of the whole map. ONE key differs:
# sensory.sensor_radius {full} -> {r}. Everything else, including the map, every count, the pond
# and its smell weight, is inherited unchanged.
#
# What the number means: a source contributes to a smell sample only if its EUCLIDEAN distance
# to the sampled cell is <= {r} (sensor.py, `dist <= radius`). The agent samples a five-cell
# diamond (its own cell and the four neighbours, olfactory_grid_range 1), so a source up to
# {r} + 1 squares away can register on the nearest neighbour cell. Same semantics as the
# context-exploration worlds' "smell range {r}" (sensory: {{sensor_radius: {r}}}).
# The observation width does not change (59): out-of-reach smell reads zero.
extends: {ext}

sensory:
  sensor_radius: {r}
"""
for g, (ext, desc, full) in PARENTS.items():
    for r in (5, 3):
        path = os.path.join(OUT, f"pond_thirst_{g}x{g}_smell{r}.yaml")
        with open(path, "w") as f:
            f.write(TEMPLATE.format(g=g, r=r, desc=desc, full=full, ext=ext))
        print("wrote", path)
