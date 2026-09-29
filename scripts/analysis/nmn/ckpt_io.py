"""Read a finished training run's saved weights without rebuilding the model.

Plain-language purpose: every run under `results/JAX_RecurrentPPO/<run>/models/`
holds 50 numbered snapshots of the network's weights, written by orbax. The usual
way to look at one is to rebuild the whole agent (which needs the environment
config, the observation layout, the action count) and let orbax pour the saved
numbers into it. For an analysis that only wants to *read numbers off the weights*
that is a lot of machinery, and — worse — it re-derives the architecture from the
current source instead of reading what the run actually saved.

This module takes the other route. Every orbax snapshot ships a `_METADATA` file
that names each saved array and its shape. We read that, build a matching target of
empty array descriptions, and ask orbax to fill it in on the CPU. The result is a
plain nested dict of numpy arrays whose keys are exactly the parameter names the
training run wrote. No model object, no environment, no GPU.

Two consequences worth stating:

* It is ground truth. If a run saved a head this code did not expect, the head shows
  up in the returned dict; nothing is silently defaulted or dropped.
* It is read-only and cheap. Loading one checkpoint's parameters is a few
  megabytes and a fraction of a second, so sweeping all 50 checkpoints of all 32
  runs is a minutes-scale job on one CPU.

Known-bug note (registry row dated 2026-09-04): a run's saved `config.yaml`
contains a *stale* nested `training.seed` / `training.episodes` pair that always
reads 42 / 100. Read the TOP-LEVEL `seed:` / `episodes:` keys instead. `run_config`
below returns the parsed YAML unchanged; callers that need the seed must take the
top-level key.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


# --------------------------------------------------------------------------
# Run discovery
# --------------------------------------------------------------------------

#  20260907-050220_rppo_nmnsite_t2enc_ALL_s42
#  20260907-045531_rppo_nmnsite_t1none_s42
#  20260909-023639_rppo_olfmc_t2enc_ALL_s42      <- the extended-olfaction twins
#  20260909-161137_rppo_olfgae_t3rnn_I_s42
#  20260921-114851_rppo_basicq2_lvl04_t16quad_s42   <- basic-levels waves: a curriculum level, and
#  20260922-182527_rppo_bq2cover_lvl04_t16quad_s42     NO slice suffix (see _slice_from_config)
_RUN_RE = re.compile(
    r"^(?P<stamp>\d{8}-\d{6})_rppo_(?P<grid>nmnsite|nmngaenorm|olfmc|olfgae|basicq2|bq2cover)_"
    r"(?:lvl(?P<level>\d{2})_)?"
    r"(?P<arm>t\d+[a-z]+)(?:_(?P<slice>ALL|I|X))?_s(?P<seed>\d+)$"
)

#: `input_sensors` in a run's saved config -> the slice label the grids encode in their names.
_INPUT_SENSORS_TO_SLICE = {"all": "ALL"}


def _slice_from_config(models_dir: Path) -> str:
    """The input slice of a modulated run whose NAME does not carry one.

    The basic-levels waves name their modulated arm `t16quad` with no `_ALL`, although the
    modulator reads every input. Inferring "no slice" from the name would label a modulated run
    "n/a (no modulator)", so the slice is read from the run's own saved config instead. An
    `input_sensors` value with no known slice is an error, never a silent default.
    """
    import yaml
    cfg = yaml.safe_load(open(Path(models_dir) / "config.yaml"))
    found = []
    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == "input_sensors":
                    found.append(v)
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(cfg)
    vals = {str(v) for v in found}
    if len(vals) != 1:
        raise ValueError(f"{models_dir}: expected exactly one input_sensors value, found {sorted(vals)}")
    v = vals.pop()
    if v not in _INPUT_SENSORS_TO_SLICE:
        raise ValueError(f"{models_dir}: input_sensors={v!r} has no known slice label")
    return _INPUT_SENSORS_TO_SLICE[v]

#: Which of the four FiLM sites each arm switches on. Read from the run's own saved
#: config at load time; this table exists only to give the arms readable names.
_ARM_LABEL = {
    "t1none": "unmodulated control",
    "t2enc": "encoder",
    "t3rnn": "recurrent",
    "t4act": "actor",
    "t5crt": "critic",
    "t16quad": "all four sites",
}

_SLICE_LABEL = {
    "ALL": "modulator reads every sense",
    "I": "modulator reads the two body signals only",
    "X": "modulator reads the external senses only",
    None: "n/a (no modulator)",
}


@dataclass(frozen=True)
class RunInfo:
    """One completed training run on disk."""
    tag: str                 # directory name
    run_dir: Path            # results/JAX_RecurrentPPO/<tag>
    models_dir: Path         # <run_dir>/models  (the CheckpointManager root)
    grid: str                # nmnsite (MC) | nmngaenorm | olfmc | olfgae
                             # the olf* pair is the same site x slice grid retrained on the
                             # olfaction-only arm: olfactory range 1, observation width 47
    arm: str                 # t1none | t2enc | t3rnn | t4act | t5crt | t16quad
    input_slice: str | None  # ALL | I | X, or None for the control
    seed: int
    level: int | None = None  # curriculum level for the basic-levels waves; None for the grids

    @property
    def modulated(self) -> bool:
        return self.arm != "t1none"

    @property
    def label(self) -> str:
        return f"{_ARM_LABEL[self.arm]} / {_SLICE_LABEL[self.input_slice]}"


def discover_runs(results_root: str | os.PathLike = "results/JAX_RecurrentPPO",
                  grids: tuple[str, ...] = ("nmnsite", "nmngaenorm")) -> list[RunInfo]:
    """Find the modulation-site grid runs under `results_root`, sorted by tag."""
    root = Path(results_root)
    if not root.is_dir():
        raise FileNotFoundError(f"results root does not exist: {root}")
    out: list[RunInfo] = []
    for d in sorted(root.iterdir()):
        if not d.is_dir():
            continue
        m = _RUN_RE.match(d.name)
        if m is None or m.group("grid") not in grids:
            continue
        models = d / "models"
        if not models.is_dir():
            raise FileNotFoundError(
                f"run {d.name} matches the grid naming pattern but has no models/ "
                f"directory — refusing to skip it silently."
            )
        arm, sl = m.group("arm"), m.group("slice")
        if sl is None and arm != "t1none":
            sl = _slice_from_config(models)
        out.append(RunInfo(
            tag=d.name, run_dir=d, models_dir=models,
            grid=m.group("grid"), arm=arm, input_slice=sl, seed=int(m.group("seed")),
            level=int(m.group("level")) if m.group("level") else None,
        ))
    return out


def list_steps(models_dir: str | os.PathLike) -> list[int]:
    """The checkpoint step numbers saved under a CheckpointManager root, ascending."""
    md = Path(models_dir)
    steps = sorted(int(p.name) for p in md.iterdir() if p.is_dir() and p.name.isdigit())
    if not steps:
        raise FileNotFoundError(f"no numbered checkpoint directories under {md}")
    return steps


def run_config(models_dir: str | os.PathLike) -> dict:
    """The agent+environment config the RUN ITSELF saved next to its checkpoints.

    Read this rather than any file under `configs/`: the run's own copy is what the
    trainer actually built the network from.
    """
    import yaml
    p = Path(models_dir) / "config.yaml"
    if not p.exists():
        raise FileNotFoundError(f"no saved config.yaml under {p.parent}")
    with open(p) as fh:
        return yaml.safe_load(fh)


# --------------------------------------------------------------------------
# Parameter loading
# --------------------------------------------------------------------------

def _metadata_tree(step_dir: Path) -> dict:
    p = step_dir / "default" / "_METADATA"
    if not p.exists():
        raise FileNotFoundError(f"checkpoint at {step_dir} has no _METADATA file")
    with open(p) as fh:
        return json.load(fh)["tree_metadata"]


def load_params(models_dir: str | os.PathLike, step: int,
                subtree: str = "model") -> dict[str, Any]:
    """Load one checkpoint's saved arrays as a nested dict of numpy arrays.

    Args:
        models_dir: the CheckpointManager root (a run's ``models/`` directory).
        step: which checkpoint (one of :func:`list_steps`).
        subtree: top-level key to restore. ``"model"`` is the network's parameters;
            ``"optimizer"`` would be Adam's state. Only this subtree is read off
            disk, so asking for ``"model"`` never pays for the optimizer.

    Returns:
        Nested dict mirroring the saved parameter names, with the orbax ``value``
        wrapper flattened away — e.g.
        ``params["modulator"]["head_unimodal"]["kernel"]`` is a ``(16, 128)`` array.

    Raises:
        FileNotFoundError: the step directory or its metadata is missing.
        ValueError: the checkpoint holds no arrays under ``subtree``.
    """
    # Imported lazily: jax initialisation is slow and this module is also imported
    # by tests that only exercise the pure-numpy maths.
    import jax
    import orbax.checkpoint as ocp

    step_dir = Path(models_dir).absolute() / str(step)
    if not step_dir.is_dir():
        raise FileNotFoundError(f"no checkpoint step directory {step_dir}")

    md = _metadata_tree(step_dir)
    target: dict = {}
    n = 0
    for entry in md.values():
        keys = [km["key"] for km in entry["key_metadata"]]
        if keys[0] != subtree:
            continue
        vm = entry["value_metadata"]
        if vm["value_type"] != "jax.Array":
            continue
        node = target
        for k in keys[:-1]:
            node = node.setdefault(k, {})
        node[keys[-1]] = jax.ShapeDtypeStruct(tuple(vm["write_shape"]), np.float32)
        n += 1
    if n == 0:
        raise ValueError(
            f"checkpoint {step_dir} has no arrays under subtree {subtree!r}; "
            f"top-level keys present: "
            f"{sorted({e['key_metadata'][0]['key'] for e in md.values()})}"
        )

    # Restored straight to host numpy arrays, so no JAX device is requested at all. The
    # earlier form asked for the CPU backend (`jax.local_devices(backend="cpu")`), which does
    # not exist in a process started with JAX_PLATFORMS=cuda: every GPU analysis job reaching
    # this reader crashed with "Unknown backend cpu" (Known Bugs, "GPU analysis jobs that
    # expose only the CUDA device crash"; fixed 2026-09-30, tooling plan Stage 4). The values
    # are the saved float32 bytes either way; the result was converted to numpy regardless.
    restore_args = jax.tree_util.tree_map(
        lambda _x: ocp.RestoreArgs(restore_type=np.ndarray), target)
    restored = ocp.PyTreeCheckpointer().restore(
        step_dir / "default",
        args=ocp.args.PyTreeRestore(item=target, restore_args=restore_args,
                                    partial_restore=True),
    )
    return _to_numpy(_unwrap_value(restored[subtree]))


def _unwrap_value(node):
    """Collapse orbax's ``{"value": array}`` leaf wrapper (nnx.Param's storage)."""
    if isinstance(node, dict):
        if set(node.keys()) == {"value"} and not isinstance(node["value"], dict):
            return node["value"]
        return {k: _unwrap_value(v) for k, v in node.items()}
    return node


def _to_numpy(node):
    if isinstance(node, dict):
        return {k: _to_numpy(v) for k, v in node.items()}
    return np.asarray(node)
