"""Export one real campfire-world episode to JSON, for the example view on the renderer-redesign page.

What it does
    Loads configs/environment/experiment/archive/thermal/campfire_world.yaml with two in-memory overrides
    (olfactory_grid_range 1, visual_sensor_range 2 -- the ranges trained with today; recorded in meta as
    `overrides`, `synthetic: true`), steps the REAL environment
    (jax_reset / jax_step) with a seeded random policy that RESTs every third step, and keeps the
    longest-surviving of seeds 0-11 (capped at 80 steps). For every recorded step it writes the
    snapshot fields the renderer reads plus the build_sensory_viz() output -- the same dicts
    scripts/eval/render_recordings.py hands to render_jax_state. Step t holds the state AFTER the
    action stored with it (step 0: initial state, action -1), matching EpisodeRecorder.

    NOTE (2026-09-16): commit f3161dcc archived 227 experiment worlds; this config now lives under
    experiment/archive/, which the project deliberately does not keep loadable. This script is a
    sketch generator for the artifact page, not a verification input: if the archived config stops
    loading, regenerate an equivalent world from default.yaml rather than migrating the archive.

    No trained policy is involved: the page shows what the dashboard draws, not what an agent does.

Output
    data/episode.json next to this file.

Run (from the repo root)
    /home/vncuser/miniconda3/envs/grid_world_pain/bin/python \
        docs/develop/active/refactors/renderer_layout_redesign/export_episode.py
"""
import copy
import json
import os
import sys

os.environ.setdefault("JAX_PLATFORMS", "cpu")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", ".."))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

import jax  # noqa: E402
import numpy as np  # noqa: E402
import yaml  # noqa: E402

from src.environment.config_loader import load_env_params  # noqa: E402
from src.environment.core import jax_reset, jax_step  # noqa: E402
from src.environment.renderer import thermal_color_limits  # noqa: E402
from src.environment.sensor import build_sensory_viz, get_observation, get_observation_breakdown  # noqa: E402
from src.utils.config import Config  # noqa: E402

CONFIG = "configs/environment/experiment/archive/thermal/campfire_world.yaml"
SEEDS = range(12)
MAX_STEPS = 80

# Derived world: the campfire config read through the senses the project trains with today
# (olfaction range 1, vision range 2), set in memory. The campfire config itself ships with both at 0.
# Sensor ranges change only what the agent observes, never the world's dynamics, and the policy below
# ignores observations, so every episode is identical to the unmodified config's.
OVERRIDES = dict(olfactory_grid_range=1, visual_sensor_range=2)
params = load_env_params(Config(copy.deepcopy(yaml.safe_load(open(CONFIG))))).replace(**OVERRIDES)
n_act = 4 + int(params.rest_action_enabled) + int(params.eat_action_enabled)


def policy(t, rng):
    return int(rng.integers(0, n_act)) if t % 3 else 4  # REST every third step


def plain(x):
    if isinstance(x, (np.ndarray, jax.Array)):
        return np.asarray(x).tolist()
    if isinstance(x, (np.floating, np.integer, np.bool_)):
        return x.item()
    return x


def survival(seed):
    state, rng, t, done = jax_reset(params, jax.random.PRNGKey(seed)), np.random.default_rng(seed), 0, False
    while t < MAX_STEPS and not done:
        state, _, done, _ = jax_step(state, policy(t, rng), params)
        t += 1
    return t


lengths = {s: survival(s) for s in SEEDS}
seed = max(SEEDS, key=lambda s: (lengths[s], -s))

state = jax_reset(params, jax.random.PRNGKey(seed))
rng = np.random.default_rng(seed)
steps, done, a, t, last_info = [], False, -1, 0, {}
while t <= MAX_STEPS and not done:
    obs = np.asarray(get_observation(state, params))
    true_obs = np.asarray(get_observation(state, params, apply_noise=False))
    viz = [{k: plain(v) for k, v in d.items()} for d in build_sensory_viz(obs, state, params, true_obs)]
    st = jax.device_get(state)
    steps.append(dict(
        t=t, action=int(a), agent=plain(st.agent_pos),
        satiation=float(st.satiation), nutrition=float(st.nutrition), injury=float(st.injury_level),
        body_temp=float(st.body_temp), res_pos=plain(st.res_pos), res_active=plain(st.res_active),
        animal_pos=plain(st.animal_pos), obs_pos=plain(st.obs_pos), sensors=viz))
    a = policy(t, rng)
    state, _, done, last_info = jax_step(state, a, params)
    t += 1

field0 = np.asarray(jax.device_get(jax_reset(params, jax.random.PRNGKey(seed))).thermal_field)
termination = {k: plain(v) for k, v in (last_info or {}).items() if np.asarray(v).size == 1}
action_names = ["UP", "RIGHT", "DOWN", "LEFT"] + (["REST"] if params.rest_action_enabled else []) \
    + (["EAT"] if params.eat_action_enabled else [])

meta = dict(
    config=CONFIG, overrides=OVERRIDES, synthetic=True,
    max_nutrition=float(params.max_nutrition), max_injury=float(params.max_injury),
    seed=int(seed), seeds_tried=len(SEEDS), survival_by_seed={str(k): v for k, v in lengths.items()},
    max_steps=MAX_STEPS, episode_done=bool(done), termination=termination, action_names=action_names,
    height=int(params.height), width=int(params.width), view=int(params.local_view_size),
    max_satiation=float(params.max_satiation), noise=bool(params.perceptual_noise_enabled),
    animal_classes=list(params.animal_classes), obstacle_names=list(params.obstacle_names),
    res_type=plain(params.res_type), obs_type=plain(params.obs_type),
    loc=plain(params.grid_location_type), thermal_field=plain(field0),
    clim=[float(v) for v in thermal_color_limits(field0, params)],
    min_temperature=float(params.min_temperature), max_temperature=float(params.max_temperature),
    temperature_setpoint=float(params.temperature_setpoint),
    breakdown={k: int(v) for k, v in get_observation_breakdown(params).items()},
    samples=[dict(what="environment steps shown in the example view", used=len(steps), total=len(steps),
                  note="every recorded step of the episode, from the initial state to the terminal step"),
             dict(what="seeds whose episode was exported", used=1, total=len(SEEDS),
                  note=f"the longest-surviving seed ({seed}); the others differ only in world layout and actions")],
)
out = os.path.join(HERE, "data", "episode.json")
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w") as fh:
    json.dump(dict(meta=meta, steps=steps), fh)
print(f"seed {seed}: {len(steps)} recorded steps, done={done}, termination={termination}")
print(f"wrote {out}")
