"""Shared loading for the internal-state reward/observation figures.

Every quantity these figures draw is read from the LIVE environment — `calculate_drive`,
`get_observation`, the resolved `EnvParams` — never re-derived from the formulas in prose.
That is deliberate: a page that documents how reward is computed is worthless if it
documents what the author believes rather than what the code does.
"""
import os, sys
os.environ.setdefault("JAX_PLATFORMS", "cpu")
_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", "..", "..", ".."))
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "scripts", "analysis", "style"))

import numpy as np
import house                                                    # noqa: E402
from src.utils.config import Config, get_default_config         # noqa: E402
from src.environment.config_loader import load_env_config, load_env_params  # noqa: E402
from src.environment.core import calculate_drive, satiation_deviation_range  # noqa: E402

FIG_ROOT = os.path.join(_ROOT, "docs/experiments/active/internal_state_reward/figures")

#: The two worlds the page contrasts. `10x10` is the ordinary case; `thermal` is the only
#: maintained world with a third homeostatic axis, so it is the one that shows the scale factor.
LEVELS = {
    "10x10":   "configs/environment/experiment/basic/04-jump_attack_10x10.yaml",
    "thermal": "configs/environment/experiment/basic/05-campfire_thermal_10x10.yaml",
}


def params_for(level="10x10", **body_overrides):
    """Resolve EnvParams through train.py's own merge order, optionally overriding body keys."""
    c = get_default_config()
    c.merge(Config.load_yaml(os.path.join(_ROOT, "configs/train/default.yaml")))
    c.merge(load_env_config(os.path.join(_ROOT, LEVELS[level])))
    for k, v in body_overrides.items():
        c.set(f"body.{k}", v)
    return load_env_params(c)


def drive(satiation, injury, params, body_temp=None):
    """Vectorised call into the REAL `calculate_drive`.

    All arguments are broadcast to ONE common shape rather than to the first argument's shape:
    a caller that sweeps injury while holding satiation fixed is as ordinary as the reverse,
    and assuming satiation is always the array is how this helper broke on its second use.
    """
    arrs = [np.asarray(satiation, dtype=float), np.asarray(injury, dtype=float)]
    if params.thermal_enabled:
        if body_temp is None:
            raise ValueError("drive(): body_temp is required on a thermal world")
        arrs.append(np.asarray(body_temp, dtype=float))
    shape = np.broadcast_shapes(*[a.shape for a in arrs]) or (1,)
    b = [np.broadcast_to(a, shape).astype(float) for a in arrs]
    if params.thermal_enabled:
        return np.asarray(calculate_drive(b[0], b[1], params, body_temp=b[2]))
    return np.asarray(calculate_drive(b[0], b[1], params))


def satiation_of(nutrition, params):
    """The derived channel: S = max_satiation * (N / max_nutrition) ** k."""
    n = np.asarray(nutrition, dtype=float)
    return params.max_satiation * (n / params.max_nutrition) ** params.nutrition_to_satiation_scaling_factor


def record_samples(stem, rows):
    """Write `<stem>.data.txt` — the used/available statement, EMITTED not typed (guide 11b)."""
    os.makedirs(FIG_ROOT, exist_ok=True)
    with open(os.path.join(FIG_ROOT, f"{stem}.data.txt"), "w") as fh:
        for r in rows:
            used, total = r["used"], r["total"]
            pct = (100.0 * used / total) if total else 0.0
            fh.write(f"{r['what']}|{used}|{total}|{pct:.1f}|{r['note']}\n")
    print(f"  wrote {stem}.data.txt ({len(rows)} row(s))")
