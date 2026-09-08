"""Independent numpy oracle for the thermal field's Gaussian blur.

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
