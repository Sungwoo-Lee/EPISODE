"""Pin the CPU backend for every test in this directory, before any of them import JAX.

WHY THIS FILE EXISTS. `tests/env/` compares live environment output against
byte-identity fixtures (`tests/env/fixtures/`), and every one of those fixtures was
captured on the CPU backend. CPU and GPU lowerings legitimately differ in the last
bits, and GPU autotuning makes repeat GPU runs differ from each other, so a
bit-exact assertion is only meaningful on a fixed backend.

WHY A conftest RATHER THAN A PER-MODULE HEADER. `os.environ.setdefault("JAX_PLATFORMS",
"cpu")` in a module header is a no-op once an earlier-collected module has already
initialised a backend — the variable is read at first backend initialisation, not at
import. Only 9 of the 35 modules here set it at all, and three fixture-consuming parity
modules (`test_unified_parity.py`, `test_visual_parity.py`, `test_extero_noc_parity.py`)
set it nowhere, so on a GPU box those failed even when run alone. pytest imports a
directory's conftest before any test module in that directory, which is early enough;
a pytest marker is not, because markers are resolved after the module is imported.

WHAT IT DELIBERATELY DOES NOT DO. It does not pin the backend repo-wide. A suite-wide
pin would make `tests/algorithms/dreamer_srl/test_gpu_buffer.py` compute `_CUDA` as
False at import and silently SKIP its 7 GPU-path tests with the reason "No CUDA device
available" — false on a GPU box, and invisible in a green run. Those tests keep their GPU.

THE CONSEQUENCE FOR A WHOLE-SUITE RUN. If something outside this directory initialises
the GPU first (collection is alphabetical, so `tests/algorithms/` precedes `tests/env/`),
the setdefault below loses and the check that follows fails ONCE, here, naming the cause —
instead of 146 opaque float mismatches spread across the directory with nothing pointing
at the backend. To run everything green in one pass, use two invocations rather than a
repo-wide pin:

    JAX_PLATFORMS=cpu pytest tests/env/
    pytest tests/ --ignore=tests/env
"""
import os

os.environ.setdefault("JAX_PLATFORMS", "cpu")

import jax

_BACKEND = jax.default_backend()
if _BACKEND != "cpu":
    raise RuntimeError(
        f"tests/env/ asserts byte-identity against fixtures captured on the CPU "
        f"backend, but JAX came up on {_BACKEND!r}. Nothing here is meaningful on "
        f"another backend: CPU and GPU lowerings differ in the last bits, so every "
        f"fixture comparison would fail for that reason alone.\n"
        f"Cause: some module imported earlier in this pytest session initialised a "
        f"JAX backend before this directory's conftest ran, so its JAX_PLATFORMS "
        f"setdefault had no effect.\n"
        f"Fix: run this directory in its own process — 'JAX_PLATFORMS=cpu pytest "
        f"tests/env/' — or set JAX_PLATFORMS=cpu for the whole invocation."
    )
