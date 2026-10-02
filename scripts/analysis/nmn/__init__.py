"""Offline representational analyses of the neuromodulator, run from saved checkpoints.

Nothing in this package trains anything or touches `src/models/`, `train.py` or
`configs/`. Every module here reads checkpoints that already exist on disk under
`results/JAX_RecurrentPPO/` and emits numbers.

Modules
-------
ckpt_io          Run discovery + raw parameter loading straight out of an orbax
                 checkpoint, without rebuilding the model or the environment.
spectral_bound   Method 1 — weights-only bounds on how much the modulator can move
                 the network's output (Marquis-style spectral norms).
"""
