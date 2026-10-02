"""Observation manipulation — change what a trained agent RECEIVES, never what the world IS.

Plain-language purpose: an agent's behaviour depends on its internal state (how injured, how
hungry) partly through the numbers its sensors hand the network, and partly through everything
else that goes with being in that state (a predator nearby, a particular place). This module
changes chosen input numbers just before the network sees them — after the sensors and any
perceptual noise — while the world keeps evolving from the true state. The difference in
behaviour is then caused by the input alone.

A manipulation is a YAML file, every key mandatory (no defaults):

    manipulations:
      - name: felt_injury            # label used in the output
        sensor: Interoceptive Nociception   # a name from the run's observation breakdown
        element: 0                   # index within that sensor
        op: set                      # set | add | scale
        values: [0.0, 0.3, 0.6]      # one condition per value
        steps: [0, null]             # [start, end) in episode steps; null end = to the end

Several entries apply together; their `values` lists are crossed (every combination is one
condition). A hidden identity condition (`add 0` on every entry) is always added as condition 0:
it must reproduce the unmanipulated agent exactly, which the caller asserts.

THE RECURRENT MEMORY. The agent is a GRU (and the modulator has its own GRU), so a changed input
also changes what the agent carries forward. `memory` selects how that is handled:
  sustained -- the manipulated input flows through the memory; effects accumulate and can
               outlast the step window (the after-effect is measurable, not hidden).
  one_step  -- each step the network acts from its NATURAL memory (built from the true inputs
               of the same trajectory) plus a manipulated input at that step only; this isolates
               the immediate effect of the input from its effect through memory.
Both are computed alongside a SHADOW pass: the same network fed the true inputs of the same
trajectory, which gives the natural memory and the memory-disturbance readout.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass

import numpy as np
import yaml

OPS = {"set": 1, "add": 2, "scale": 3}
MEMORY_MODES = ("sustained", "one_step")
_KEYS = ("name", "sensor", "element", "op", "values", "steps")


@dataclass
class Manipulation:
    """Compiled conditions: arrays of shape (C, K) — C conditions, K manipulated elements."""
    names: list            # K entry names
    index: np.ndarray      # (K,) int   position in the flat observation
    op: np.ndarray         # (C, K) int  0 = untouched (identity condition), else OPS
    value: np.ndarray      # (C, K) float
    t0: np.ndarray         # (K,) int
    t1: np.ndarray         # (K,) int   exclusive; max_steps+1 for "to the end"
    labels: list           # C human-readable condition labels
    spec: dict             # the YAML as read, stored in every output manifest

    @property
    def n(self):
        return self.op.shape[0]


def sensor_offsets(breakdown: dict) -> dict:
    """{sensor name: (start, width)} in the flat observation, in breakdown order."""
    out, pos = {}, 0
    for name, width in breakdown.items():
        out[name] = (pos, int(width))
        pos += int(width)
    return out


def load(path: str, breakdown: dict, max_steps: int) -> Manipulation:
    spec = yaml.safe_load(open(path))
    if not isinstance(spec, dict) or "manipulations" not in spec:
        raise ValueError(f"{path}: top-level key `manipulations` is mandatory")
    entries = spec["manipulations"]
    if not entries:
        raise ValueError(f"{path}: `manipulations` is empty")
    offs = sensor_offsets(breakdown)
    names, index, ops, vals, t0, t1 = [], [], [], [], [], []
    for i, e in enumerate(entries):
        missing = [k for k in _KEYS if k not in e]
        if missing:
            raise ValueError(f"{path}: entry {i} is missing mandatory key(s) {missing}")
        if e["sensor"] not in offs:
            raise ValueError(f"{path}: entry {e['name']!r}: sensor {e['sensor']!r} is not in this "
                             f"run's observation. Valid names: {list(offs)}")
        start, width = offs[e["sensor"]]
        el = int(e["element"])
        if not 0 <= el < width:
            raise ValueError(f"{path}: entry {e['name']!r}: element {el} out of range for "
                             f"{e['sensor']!r} (width {width})")
        if e["op"] not in OPS:
            raise ValueError(f"{path}: entry {e['name']!r}: op {e['op']!r} not one of {list(OPS)}")
        if not isinstance(e["values"], list) or not e["values"]:
            raise ValueError(f"{path}: entry {e['name']!r}: `values` must be a non-empty list")
        s = e["steps"]
        if not (isinstance(s, list) and len(s) == 2):
            raise ValueError(f"{path}: entry {e['name']!r}: `steps` must be [start, end|null]")
        lo, hi = int(s[0]), (max_steps + 1 if s[1] is None else int(s[1]))
        if not 0 <= lo < hi:
            raise ValueError(f"{path}: entry {e['name']!r}: empty step window {s}")
        names.append(e["name"]); index.append(start + el); ops.append(OPS[e["op"]])
        vals.append([float(v) for v in e["values"]]); t0.append(lo); t1.append(hi)

    K = len(names)
    combos = list(itertools.product(*vals))
    op = np.zeros((len(combos) + 1, K), np.int32)
    value = np.zeros((len(combos) + 1, K), np.float32)
    labels = ["identity"]
    for c, combo in enumerate(combos, start=1):
        op[c] = ops
        value[c] = combo
        labels.append(", ".join(f"{n} {e['op']} {v:g}" for n, e, v in zip(names, entries, combo)))
    return Manipulation(names, np.asarray(index, np.int32), op, value,
                        np.asarray(t0, np.int32), np.asarray(t1, np.int32), labels, spec)


def apply(obs, t, index, op, value, t0, t1):
    """Manipulate a batch of observations at step `t`. jit-safe.

    obs (B, D); op/value (B, K) per batch row; index/t0/t1 (K,). Entries whose op is 0, or whose
    window does not contain `t`, leave the observation untouched. Entries are applied in order.
    """
    import jax.numpy as jnp
    live = (t >= t0) & (t < t1)                                  # (K,)
    for k in range(index.shape[0]):
        cur = obs[:, index[k]]
        new = jnp.where(op[:, k] == 1, value[:, k],
              jnp.where(op[:, k] == 2, cur + value[:, k],
              jnp.where(op[:, k] == 3, cur * value[:, k], cur)))
        obs = obs.at[:, index[k]].set(jnp.where(live[k], new, cur))
    return obs


def split_memory(h, modulated: bool):
    """(task memory, modulator memory or None), each flattened to (B, n).

    The network's recurrent state is the task GRU/LSTM state, or `(task_state, modulator_state)`
    when a modulator is present (`ActorCriticRNN.initial_state`).
    """
    import jax
    import jax.numpy as jnp
    flat = lambda x: jnp.concatenate([l.reshape(l.shape[0], -1) for l in jax.tree_util.tree_leaves(x)], -1)
    if modulated:
        return flat(h[0]), flat(h[1])
    return flat(h), None
