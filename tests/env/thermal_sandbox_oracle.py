"""Independent numpy oracle for the thermal field's blur and body-temperature recurrence.

**Vendored copy.** The source is the design's calibration sandbox at
`docs/develop/active/thermal/temperature_system_plan/sim.py::gaussian_smooth`,
which is pure numpy, deliberately imports nothing from `src/`, and is the code
every calibrated number in the temperature design was computed from. It is
copied here rather than imported for two reasons:

1. `docs/` is not an import root for the test suite.
2. The sandbox hard-codes a module-level `H = W = 10`, so importing it would
   lock the test to a square 10x10 grid — and a row/column transposition in the
   kernel is invisible on a square grid.

The only change from the source is that the grid size is read from the field's
own shape instead of the module-level constants. **The two must stay in step:**
if `sim.py`'s blur changes, this copy changes with it, or the oracle silently
stops being the thing the design was calibrated against.

`body_traj` below is vendored from the same module, unmodified. It is the loop
every steps-to-death and equilibrium number in the design was printed from.

The reason this is a real oracle and not a tautology: a test that re-derived the
expected field with the same JAX helper would only verify that the function
equals itself.
"""
import numpy as np


def gaussian_smooth(f, sigma):
    """Weight-normalised Gaussian blur, EVAAA's sum/weightSum at the edges.

    Out-of-bounds contributions are dropped from BOTH the weighted sum and the
    weight sum, so an edge cell is the mean of its real neighbours rather than a
    mean that quietly counts zeros. A plain convolution differs here.

    Args:
        f: [H, W] float array of raw (pre-blur) temperatures.
        sigma: blur width in cells; <= 0 returns a copy.
    """
    if sigma <= 0:
        return f.copy()
    H, W = f.shape
    rad = int(np.ceil(3 * sigma))
    k = np.exp(-0.5 * (np.arange(-rad, rad + 1) / sigma) ** 2)
    out = np.zeros_like(f)
    wsum = np.zeros_like(f)
    for i, dr in enumerate(range(-rad, rad + 1)):
        for j, dc in enumerate(range(-rad, rad + 1)):
            wt = k[i] * k[j]
            rs = np.clip(np.arange(H) + dr, 0, H - 1)
            cs = np.clip(np.arange(W) + dc, 0, W - 1)
            inb = (((np.arange(H) + dr >= 0) & (np.arange(H) + dr < H))[:, None]
                   & ((np.arange(W) + dc >= 0) & (np.arange(W) + dc < W))[None, :])
            out += np.where(inb, f[np.ix_(rs, cs)] * wt, 0.0)
            wsum += np.where(inb, wt, 0.0)
    return out / wsum


def body_traj(T_field_seq, T0=0.0, k_ex=0.04, k_loss=0.01, k_met=0.0, T_neutral=0.0):
    """Body-temperature trajectory under the design's recurrence.

    Vendored verbatim from `sim.py::body_traj`. One entry per step PLUS the
    initial value, so `out[n]` is the body temperature after `n` steps and
    `out[0] == T0`.

    The `k_loss` term is what makes this an oracle rather than a restatement of
    the environment: drop it and the body equilibrates at exactly the cell
    temperature instead of at `k_ex*T_field/(k_ex+k_loss)`.
    """
    T = T0
    out = [T]
    for Tf in T_field_seq:
        T = T + k_ex * (Tf - T) + k_met - k_loss * (T - T_neutral)
        out.append(T)
    return np.array(out)
