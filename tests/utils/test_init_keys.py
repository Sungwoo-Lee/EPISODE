"""Golden keys for train.py's key recipe (src/utils/init_keys.trainer_init_keys).

Plain-language context: a run's starting network is drawn from keys derived from its seed, and
no step-0 checkpoint is saved. The analysis rebuilds untrained networks from the same recipe,
so the recipe must never change silently. These are the raw uint32 key data of (key, env_key,
init_key) for seeds 42, 43 and 44, recorded on commit a236ccf5 (train.py last changed at
89f3cb78), BEFORE the recipe moved into src/utils/init_keys.py; the recording script
(tmp/20260930_r46_golden_keys.py) asserted train.py's own chain text first. A second test
checks that untrained.py calls the helper instead of copying the chain back in.

Plan: docs/develop/active/neuromodulation/ALGORITHMIC_NULL_ANALYSIS_TOOLING.md, R4-6.
"""
import ast
import os
import sys
from pathlib import Path

os.environ.setdefault("JAX_PLATFORMS", "cpu")
_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

import jax  # noqa: E402
import numpy as np  # noqa: E402
import pytest  # noqa: E402

from src.utils.init_keys import trainer_init_keys  # noqa: E402

GOLDEN = {   # recorded on a236ccf5, before the edit
    42: {"key": [1012194634, 3152801799], "env_key": [2465931498, 255383827],
         "init_key": [1705926158, 899080142]},
    43: {"key": [449051237, 3616999620], "env_key": [1512537201, 2531556346],
         "init_key": [3471251761, 3587158380]},
    44: {"key": [2001052130, 3307961423], "env_key": [1637027069, 3739161765],
         "init_key": [1548230112, 2157066771]},
}


@pytest.mark.parametrize("seed", sorted(GOLDEN))
def test_golden_keys(seed):
    key, env_key, init_key = trainer_init_keys(seed)
    got = {n: np.asarray(jax.random.key_data(k)).astype(np.uint32).tolist()
           for n, k in (("key", key), ("env_key", env_key), ("init_key", init_key))}
    assert got == GOLDEN[seed]


def _calls(path):
    """Dotted names of every call in a file (docstrings and comments are not calls)."""
    out = []
    for node in ast.walk(ast.parse(Path(path).read_text())):
        if isinstance(node, ast.Call):
            parts, f = [], node.func
            while isinstance(f, ast.Attribute):
                parts.append(f.attr)
                f = f.value
            if isinstance(f, ast.Name):
                parts.append(f.id)
            out.append(".".join(reversed(parts)))
    return out


def test_untrained_calls_the_helper_and_copies_no_chain():
    calls = _calls(_REPO / "scripts" / "analysis" / "nmn" / "untrained.py")
    assert "trainer_init_keys" in calls
    copied = [c for c in calls if c.endswith("random.split") or c.endswith("random.PRNGKey")]
    assert not copied, copied


def test_train_py_calls_the_helper_and_splits_no_init_key():
    src = (_REPO / "train.py").read_text()
    assert "trainer_init_keys" in _calls(_REPO / "train.py")
    assert "key, init_key = jax.random.split(key)" not in src
    assert "key, model_key, env_key = jax.random.split(key, 3)" not in src
