"""Regression: the analysis checkpoint reader must not ask JAX for a CPU device.

Known Bugs row "GPU analysis jobs that expose only the CUDA device crash ..." (2026-09-30):
`ckpt_io.load_params` restored onto `jax.local_devices(backend="cpu")[0]`, which raises
"Unknown backend cpu" in a process started with JAX_PLATFORMS=cuda. It now restores to host
numpy arrays and requests no device. The test makes every device query raise (the CUDA-only
situation, reproducible on CPU) and checks the values equal a plain orbax read.

Needs a gitignored run; skipped when absent.
"""
import os
import sys
from pathlib import Path

import numpy as np
import pytest

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
os.environ.setdefault("JAX_PLATFORMS", "cpu")

RUN = _REPO / "results/JAX_RecurrentPPO/20260927-053059_rppo_l05body_w0000_t16quad_s42/models"
STEP = 200019


def _leaves(d, out):
    for k in sorted(d):
        _leaves(d[k], out) if isinstance(d[k], dict) else out.append(d[k])
    return out


def test_load_params_requests_no_device(monkeypatch):
    if not (RUN / str(STEP)).is_dir():
        pytest.skip("run not present (gitignored)")
    import jax
    from scripts.analysis.nmn import ckpt_io
    ref = _leaves(ckpt_io.load_params(RUN, STEP), [])      # unpatched read

    def no_backend(*a, **k):
        raise RuntimeError("Unknown backend cpu. Available backends are ['cuda']")
    monkeypatch.setattr(jax, "local_devices", no_backend)
    monkeypatch.setattr(jax, "devices", no_backend)
    got = _leaves(ckpt_io.load_params(RUN, STEP), [])
    assert len(got) == len(ref) == 60
    assert all(isinstance(g, np.ndarray) and g.dtype == np.float32 for g in got)
    assert all(np.array_equal(g, r) for g, r in zip(got, ref))
