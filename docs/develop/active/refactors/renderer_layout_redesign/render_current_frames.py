"""Render one frame with each existing renderer, for the renderer-redesign page.

What it does
    For the campfire temperature world (configs/environment/experiment/archive/thermal/campfire_world.yaml)
    and the default world (configs/environment/default.yaml): reset with PRNGKey(3), take the fixed
    actions RIGHT, DOWN, RIGHT, DOWN, REST, then render the resulting state with the production
    renderer (src/environment/renderer.py::render_jax_state, "V1") and the dormant one
    (src/environment/renderer_v2.py::render_jax_state_v2, "V2"). The sensory panels get
    build_sensory_viz() output built from the noisy and the noise-free observation, exactly as
    scripts/eval/render_recordings.py does; V1 also gets the fixed thermal colour limits.

    NOTE (2026-09-16): commit f3161dcc archived 227 experiment worlds; this config now lives under
    experiment/archive/, which the project deliberately does not keep loadable. This script is a
    sketch generator for the artifact page, not a verification input: if the archived config stops
    loading, regenerate an equivalent world from default.yaml rather than migrating the archive.

Output
    figures/{v1,v2}_{thermal,default}.png and figures/frames_meta.json (frame sizes, render seconds,
    and the sample counts shown in the page's data-used tables).

Run (from the repo root)
    /home/vncuser/miniconda3/envs/grid_world_pain/bin/python \
        docs/develop/active/refactors/renderer_layout_redesign/render_current_frames.py
"""
import copy
import json
import os
import sys
import time

os.environ.setdefault("JAX_PLATFORMS", "cpu")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", ".."))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

import jax  # noqa: E402
import numpy as np  # noqa: E402
import yaml  # noqa: E402
from PIL import Image  # noqa: E402

from src.environment.config_loader import load_env_params  # noqa: E402
from src.environment.core import jax_reset, jax_step  # noqa: E402
from src.environment.renderer import render_jax_state, thermal_color_limits  # noqa: E402
from src.environment.renderer_v2 import render_jax_state_v2  # noqa: E402
from src.environment.sensor import build_sensory_viz, get_observation  # noqa: E402
from src.utils.config import Config  # noqa: E402

WORLDS = (("configs/environment/experiment/archive/thermal/campfire_world.yaml", "thermal"),
          ("configs/environment/default.yaml", "default"))
ACTIONS = [1, 2, 1, 2, 4]
OUT = os.path.join(HERE, "figures")
os.makedirs(OUT, exist_ok=True)

meta = {}
for cfg, tag in WORLDS:
    params = load_env_params(Config(copy.deepcopy(yaml.safe_load(open(cfg)))))
    state = jax_reset(params, jax.random.PRNGKey(3))
    for a in ACTIONS:
        state, *_ = jax_step(state, a, params)
    obs = get_observation(state, params)
    true_obs = get_observation(state, params, apply_noise=False)
    sd = build_sensory_viz(np.asarray(obs), state, params, np.asarray(true_obs))
    st = jax.device_get(state)
    clim = thermal_color_limits(getattr(st, "thermal_field", None), params)
    for name, fn, kw in (("v1", render_jax_state, dict(thermal_clim=clim)), ("v2", render_jax_state_v2, {})):
        t0 = time.perf_counter()
        img = fn(st, params, episode=1, step=len(ACTIONS), action=ACTIONS[-1], sensory_data=sd, **kw)
        secs = time.perf_counter() - t0
        stem = f"{name}_{tag}"
        Image.fromarray(img).save(os.path.join(OUT, f"{stem}.png"))
        meta[stem] = dict(
            config=cfg, seed=3, actions=ACTIONS, width=int(img.shape[1]), height=int(img.shape[0]),
            render_seconds=round(secs, 3),
            samples=[dict(what="frames rendered", used=1, total=1,
                          note=f"one state: seed 3 after {len(ACTIONS)} fixed actions"),
                     dict(what="sensory panels the observation carries", used=len(sd), total=len(sd),
                          note="every entry build_sensory_viz emitted was passed to the renderer; "
                               "whether the renderer draws each one is what the figure shows")])
        print(stem, img.shape, f"{secs:.2f}s")

with open(os.path.join(OUT, "frames_meta.json"), "w") as fh:
    json.dump(meta, fh, indent=1)
