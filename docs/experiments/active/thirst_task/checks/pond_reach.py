"""Share of the map from which the POND alone is smellable (any of the 5 sampled cells within
sensor_radius, Euclidean, of any pond cell), per world, from the loaded params' pond table."""
import os, sys, logging
os.environ["JAX_PLATFORMS"] = "cpu"
logging.disable(logging.WARNING)
W = "/media/nas01/projects/Interoceptive-AI/grid_world_pain/.claude/worktrees/thirst"
sys.path.insert(0, W); os.chdir(W)
import numpy as np
from src.environment.config_loader import load_env_config, load_env_params

WORLDS = [("g10", "configs/environment/experiment/basic/06-pond_thirst_10x10.yaml"),
          ("g15", "configs/environment/experiment/thirst/pond_thirst_15x15.yaml"),
          ("g20", "configs/environment/experiment/thirst/pond_thirst_20x20.yaml")]
for name, rel in WORLDS:
    p = load_env_params(load_env_config(rel))
    H, Wd, h, w = int(p.height), int(p.width), int(p.water_block_h), int(p.water_block_w)
    rr, cc = np.meshgrid(np.arange(H), np.arange(Wd), indexing="ij")
    out = []
    for radius in (5, 3):
        fr = []
        for r0, c0 in p.water_topleft_table:
            pond = np.array([(r0 + i, c0 + j) for i in range(h) for j in range(w)])
            seen = np.zeros((H, Wd), bool)
            for dr, dc in [(0, 0), (-1, 0), (0, 1), (1, 0), (0, -1)]:
                sr, sc = rr + dr, cc + dc
                inb = (sr >= 0) & (sr < H) & (sc >= 0) & (sc < Wd)
                d = np.sqrt((sr[..., None] - pond[:, 0]) ** 2 + (sc[..., None] - pond[:, 1]) ** 2).min(-1)
                seen |= inb & (d <= radius)
            onpond = np.zeros((H, Wd), bool)
            onpond[r0:r0 + h, c0:c0 + w] = True
            fr.append(seen[~onpond].mean())
        out.append(f"reach {radius}: pond smellable from {100 * np.mean(fr):.1f} % of non-pond cells")
    print(name, "; ".join(out))
