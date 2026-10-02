"""Episode recording format for offline (post-hoc) video rendering.

Each episode is serialized to ONE file per episode:

    <results_dir>/recordings/<checkpoint_pct>/episode_<NNNNNN>.rec

Plus ONE shared metadata file per eval run:

    <results_dir>/recordings/<checkpoint_pct>/run_meta.pkl
    (contains: params pytree, icon_config, action_map, config path, git sha,
     channel_display)

`channel_display` is the sensor-channel NAMES the episode video prints under each
channel's map, taken from the environment config when the recording is written.
It lives here, beside `icon_config` and `action_map`, because it is the same kind
of thing they are: a fact about how to DRAW a run, not about how the environment
behaves. A recording written before it existed simply has no such key, and the
renderer falls back to positional names ("Channel 0") -- see
`dashboard/labels.py`.

Format: pickle-gzip (level 5) chosen based on Phase 0 benchmark.
"""
import gzip
import pickle
from pathlib import Path
from typing import Any, Dict, List
import numpy as np

RECORDING_FORMAT_VERSION = 1
_DEFAULT_COMPRESSLEVEL = 5


def _snapshot_state(state) -> Dict[str, Any]:
    """Exactly the fields render_jax_state reads. Keep in lockstep with renderer.py.

    Uses unified animal_pos (CP6). Renderers slice by class via select_by_class.

    Thermal (temperature system, Stage 6a): `thermal_field` and `body_temp` are
    added here because offline video rendering reads nothing else — a recording
    without them renders a thermal episode with no field and no gauge.

    `RECORDING_FORMAT_VERSION` is deliberately NOT bumped. Every `.rec` written
    before this change lacks both keys, so the reader has to branch on their
    presence either way; a version bump would not have removed a line of that
    branch, and the stamp it would change is one that nothing in the codebase
    reads. The branch lives in `renderer.py` (a `getattr(state, ..., None)` on
    each field), which is what keeps every pre-thermal recording rendering
    exactly as it does today.

    On a thermal-OFF config `state.thermal_field` is `jnp.zeros((0, 0))`, so the
    added payload is two scalars' worth of nothing.
    """
    snap = {
        'agent_pos': np.asarray(state.agent_pos),
        'satiation': float(state.satiation),
        'nutrition': float(state.nutrition),
        'injury_level': float(state.injury_level),
        'rest_streak': int(state.rest_streak),
        'res_pos': np.asarray(state.res_pos),
        'res_active': np.asarray(state.res_active),
        'animal_pos': np.asarray(state.animal_pos),
        'obs_pos': np.asarray(state.obs_pos),
    }
    if getattr(state, 'thermal_field', None) is not None:
        snap['thermal_field'] = np.asarray(state.thermal_field)
    if getattr(state, 'body_temp', None) is not None:
        snap['body_temp'] = float(state.body_temp)
    # Water (THIRST_WATER_PLAN D8.5). `water_pos` lists EVERY pond cell,
    # shape [h*w, 2]; the dashboard draws exactly those. Both keys are absent
    # from every recording made before water existed, and the dashboard keys
    # its pond and hydration row on their presence -- so those render as before.
    if getattr(state, 'hydration', None) is not None:
        snap['hydration'] = float(state.hydration)
    if getattr(state, 'water_pos', None) is not None:
        snap['water_pos'] = np.asarray(state.water_pos)
    return snap


class EpisodeRecorder:
    """Accumulates per-step data for one episode, then writes a single file."""

    def __init__(self, episode_index: int, train_episode: int, seed: int):
        self.episode_index = int(episode_index)
        self.train_episode = int(train_episode)
        self.seed = int(seed)
        self.snapshots: List[Dict[str, Any]] = []
        self.obs: List[np.ndarray] = []
        self.true_obs: List[np.ndarray] = []
        self.actions: List[int] = []
        self.rewards: List[float] = []

    def append(self, state, obs, true_obs, action_idx: int, reward: float):
        self.snapshots.append(_snapshot_state(state))
        self.obs.append(np.asarray(obs))
        self.true_obs.append(np.asarray(true_obs) if true_obs is not None else None)
        self.actions.append(int(action_idx))
        self.rewards.append(float(reward))

    def write(self, out_path: Path):
        out_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            'version': RECORDING_FORMAT_VERSION,
            'episode_index': self.episode_index,
            'train_episode': self.train_episode,
            'seed': self.seed,
            'snapshots': self.snapshots,
            'obs': np.stack(self.obs),
            'true_obs': (np.stack([t for t in self.true_obs]) if self.true_obs[0] is not None else None),
            'actions': np.asarray(self.actions, dtype=np.int32),
            'rewards': np.asarray(self.rewards, dtype=np.float32),
        }
        with gzip.open(out_path, 'wb', compresslevel=_DEFAULT_COMPRESSLEVEL) as fh:
            pickle.dump(payload, fh, protocol=pickle.HIGHEST_PROTOCOL)


#: Which config keys carry each sense's display, and which resolved `EnvParams`
#: fields say whether that sense is on and how wide it is.
_DISPLAY_KEYS = {
    'Olfaction': ('sensory.olfactory_channel_names',
                  'sensory.olfactory_channel_groups',
                  'olfactory_enabled', 'olfactory_vector_size'),
    'Visual': ('sensory.visual_channel_names',
               'sensory.visual_channel_groups',
               'visual_sensor_enabled', 'visual_vector_size'),
}


def channel_display_from_config(config, params) -> Dict:
    """Build the `run_meta` channel_display payload from a RESOLVED config.

    NOT reached by the byte-parity gates -- they never write a recording -- which
    is why reading these keys strictly is safe here and would not be inside
    `load_env_params`. A new mandatory key there is read by those gates, which
    load ~38 standalone configs raw with no `extends:` resolution, most of them
    archived worlds the project deliberately does not keep loadable.

    IT IS, HOWEVER, REACHED WITH UN-LAYERED CONFIGS. The common evaluation
    invocation `eval_rollout.py --config <run>/models/config.yaml` hands this a
    run's FROZEN saved config -- a resolved snapshot that has no `extends:` to
    inherit through and cannot contain keys invented after that run finished. So
    every checkpoint trained before channel names existed raises here. That is
    deliberate and is an accepted cost: a fallback default would mean a
    pre-change run silently recording today's names as though it had declared
    them, which is exactly the quiet mistake this whole change removes. The
    message therefore names the remedy rather than just the missing key.

    A SENSE'S KEYS ARE READ ONLY WHEN THAT SENSE IS ON. A world with vision
    switched off has no vision channels to name, so demanding names for it would
    fail a perfectly correct config -- and giving it names would describe a sense
    the agent does not have. Display keys left behind for a disabled sense are
    ignored rather than refused: there is no resolved width to validate them
    against, and refusing would punish a harmless leftover.
    """
    from src.environment.dashboard.labels import (
        ChannelDisplay, panel_map_slots, validate_entry)

    out: Dict[str, Any] = {}
    for sense, (names_key, groups_key, on_field, width_field) in _DISPLAY_KEYS.items():
        if not bool(getattr(params, on_field)):
            continue
        width = int(getattr(params, width_field))
        values = {}
        for key in (names_key, groups_key):
            value = config.get(key)
            if value is None:
                raise ValueError(
                    f"Configuration key '{key}' is required but missing. This "
                    f"config predates sensor channel names, or declares a sense "
                    f"width without redeclaring that sense's names in the same "
                    f"file. A recording cannot be written without it, and there "
                    f"is deliberately no default -- a default here would record "
                    f"some other world's channel names as though this run had "
                    f"declared them. Remedy: re-record from a config resolved at "
                    f"current code, or add '{names_key}' and '{groups_key}' to "
                    f"this file (see configs/environment/default.yaml for the "
                    f"worked example)."
                )
            values[key] = value

        entry = {
            'names': [dict(n) if isinstance(n, dict) else {'name': n, 'qualifier': ''}
                      for n in values[names_key]],
            'groups': [dict(g) for g in values[groups_key]],
        }
        # Validate exactly as the READER will, so a payload cannot be written
        # that the renderer would later reject.
        # Both keys are named in every message: a group error reported against
        # the NAMES key alone sends the reader to the wrong line.
        validate_entry(sense, width, entry, where=f"{names_key} / {groups_key}")
        # Same over-slot warning the display build emits, issued here too so a
        # config problem is reported when the recording is WRITTEN rather than
        # only when someone later tries to draw it.
        panel_map_slots(sense, ChannelDisplay.from_meta(
            sense, width, entry, key_present=True))
        out[sense] = entry
    return out


def write_run_meta(out_dir: Path, params, icon_config, action_map, config_path: str,
                   channel_display: Dict, extras: Dict = None):
    """Write the per-run metadata every recording in this directory shares.

    `channel_display` is REQUIRED rather than defaulted: a writer that forgot it
    would produce recordings whose videos silently fall back to positional
    channel names, which is indistinguishable from a genuinely old recording.
    Build it with :func:`channel_display_from_config`.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        'version': RECORDING_FORMAT_VERSION,
        'params': params,           # EnvParams is a Flax struct.dataclass — picklable
        'icon_config': icon_config,
        'action_map': list(action_map),
        'config_path': str(config_path),
        'channel_display': dict(channel_display),
        'extras': dict(extras or {}),
    }
    with open(out_dir / 'run_meta.pkl', 'wb') as fh:
        pickle.dump(payload, fh, protocol=pickle.HIGHEST_PROTOCOL)


def load_run_meta(recording_dir: Path) -> Dict[str, Any]:
    with open(recording_dir / 'run_meta.pkl', 'rb') as fh:
        return pickle.load(fh)


def load_episode(path: Path) -> Dict[str, Any]:
    with gzip.open(path, 'rb') as fh:
        return pickle.load(fh)
