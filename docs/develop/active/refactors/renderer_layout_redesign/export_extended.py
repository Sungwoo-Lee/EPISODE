"""Export one real world state read through extended-range senses, for the page's encoding options (Figures 5-7).

What it does
    Loads configs/environment/experiment/archive/sensory_ladder/V2_blur20.yaml (olfaction range 1, vision range 2,
    anisotropic blur on) and steps the REAL environment with a seeded random policy
    (REST every third step), keeping the longest-surviving of seeds 0-11. Within that
    episode it picks the step whose vision diamond holds the most non-terrain signal, so the drawings
    have content. At that state it reads olfaction and vision through the production observation code
    three times:
        1. as configured (olfaction 1, vision 2);
        2. both ranges overridden in memory to 3;
        3. both ranges overridden in memory to 4.
    The world state is identical in all three; only how far the agent senses changes. Rows 2-3 are
    derived stress inputs, not configs anyone trains. Readings come from build_sensory_viz, exactly as
    the video path builds them.

    NOTE (2026-09-16): commit f3161dcc archived 227 experiment worlds; this config now lives under
    experiment/archive/, which the project deliberately does not keep loadable. This script is a
    sketch generator for the artifact page, not a verification input: if the archived config stops
    loading, regenerate an equivalent world from default.yaml rather than migrating the archive.

Output
    data/extended.json next to this file.

Run (from the repo root)
    /home/vncuser/miniconda3/envs/grid_world_pain/bin/python \
        docs/develop/active/refactors/renderer_layout_redesign/export_extended.py
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
from src.environment.sensor import build_sensory_viz, get_observation, get_visual_offsets  # noqa: E402
from src.utils.config import Config  # noqa: E402

CONFIG = "configs/environment/experiment/archive/sensory_ladder/V2_blur20.yaml"
SEEDS = range(12)
MAX_STEPS = 80
VARIANTS = [("As configured: olfaction range 1, vision range 2", 1, 2, False),
            ("Stress test: both ranges set to 3 (same world state)", 3, 3, True),
            ("Stress test: both ranges set to 4 (same world state)", 4, 4, True)]

params = load_env_params(Config(copy.deepcopy(yaml.safe_load(open(CONFIG)))))
n_act = 4 + int(params.rest_action_enabled) + int(params.eat_action_enabled)


def policy(t, rng):
    return int(rng.integers(0, n_act)) if t % 3 else 4


def plain(x):
    if isinstance(x, (np.ndarray, jax.Array)):
        return np.asarray(x).tolist()
    if isinstance(x, (np.floating, np.integer, np.bool_)):
        return x.item()
    return x


def sense(viz, name):
    for d in viz:
        if d["name"] == name:
            return {k: plain(v) for k, v in d.items()}
    raise KeyError(name)


lengths = {}
for s in SEEDS:
    st, rng, t, done = jax_reset(params, jax.random.PRNGKey(s)), np.random.default_rng(s), 0, False
    while t < MAX_STEPS and not done:
        st, _, done, _ = jax_step(st, policy(t, rng), params)
        t += 1
    lengths[s] = t
seed = max(SEEDS, key=lambda s: (lengths[s], -s))

state, rng = jax_reset(params, jax.random.PRNGKey(seed)), np.random.default_rng(seed)
states, done, t = [], False, 0
while t <= MAX_STEPS and not done:
    states.append(state)
    state, _, done, _ = jax_step(state, policy(t, rng), params)
    t += 1


def entity_mass(st):
    viz = build_sensory_viz(np.asarray(get_observation(st, params, apply_noise=False)), st, params)
    v = np.asarray(sense(viz, "Visual")["vector"]).reshape(-1, params.visual_vector_size)
    return float(v[:, 3:].sum())


masses = [entity_mass(st) for st in states]
step = int(np.argmax(masses))
st = states[step]

variants = []
for label, o, v, derived in VARIANTS:
    p = params.replace(olfactory_grid_range=o, visual_sensor_range=v)
    obs = np.asarray(get_observation(st, p))
    true_obs = np.asarray(get_observation(st, p, apply_noise=False))
    viz = build_sensory_viz(obs, st, p, true_obs)
    variants.append(dict(label=label, derived=derived, olf_range=o, vis_range=v, obs_dim=int(obs.size),
                         olf=sense(viz, "Olfactory"), vis=sense(viz, "Visual"),
                         offsets_olf=plain(get_visual_offsets(o)), offsets_vis=plain(get_visual_offsets(v))))
    print(f"{label}: observation width {obs.size}")

meta = dict(config=CONFIG, seed=int(seed), step=step, episode_steps=len(states), agent=plain(st.agent_pos),
            height=int(params.height), width=int(params.width), noise=bool(params.perceptual_noise_enabled),
            blur=bool(params.visual_blur_enabled), value_mode=str(getattr(params, "visual_value_mode", "")),
            samples=[dict(what="world states drawn", used=1, total=len(states),
                          note=f"step {step} of seed {seed}: the step with the most non-terrain vision signal"),
                     dict(what="sensor ranges drawn", used=len(VARIANTS), total=len(VARIANTS),
                          note="the configured ranges plus two in-memory stress overrides of the same state")])
out = os.path.join(HERE, "data", "extended.json")
with open(out, "w") as fh:
    json.dump(dict(meta=meta, variants=variants), fh)
print(f"seed {seed}, step {step} of {len(states)}; wrote {out}")
