"""Thermal-parity gate — Stage 0 of the temperature-system plan.

WHAT THIS IS. Before any thermal code exists, `scripts/fixtures/generate_thermal_parity_fixtures.py`
captured the observation, the reward and the homeostatic drive of every config that
loads and runs, for a fixed 100-step episode from seed 0. This test replays the same
episode against the current code and asserts it still matches. Stages 1 and 2 of
`docs/develop/active/thermal/IMPLEMENTATION_PLAN.md` promise to leave existing
behaviour byte-for-byte identical; this file is the instrument that decides whether
that promise held, rather than leaving it asserted.

WHAT IT COVERS, HONESTLY. `_collect_configs()` walks the whole config set (356 files
at the time of writing), but only the ones with a committed `.npz` under
`tests/env/fixtures/thermal_parity/` are adjudicated — the rest are *skipped*, not
passed. See the plan's F6 ("The honest coverage statement") before reading more into
a green run than it says.

THE ADJUDICATION RULE (plan, Stage 0). Exact equality on everything, with exactly one
narrow, upstream-anchored exemption:

  * Exact: reward, both drives, `state.key`, `termination_reason`, every entity
    position array, the observation breakdown total, and every observation slice
    other than Olfaction.
  * The three sampled-property state arrays (`animal_property_sampled`,
    `res_property_sampled`, `obs_property_sampled`) must be exact, EXCEPT that an
    element may differ by <= 1 float32 ulp when its entity's config declares a
    non-zero `properties_std`. Where the std is zero there is nothing to diverge and
    any difference is a regression.
  * The Olfaction slice tolerance is DERIVED from that bound (see
    `_olfaction_tolerance` below), not asserted as a constant.

WHY THE EXEMPTION EXISTS. `jax_reset` is not bit-identical across XLA lowerings:
`mean + std * noise` may lower as a separate multiply-and-add or as a fused FMA, and
which one XLA picks depends on the surrounding graph. Stage 1 adds leaves to the reset
pytree, which changes the graph. Measured bound: one float32 ulp, on
`animal_property_sampled` only. Full evidence chain:
`docs/llm_wiki/entries/env_entities/20260820_1606_reset_ulp_divergence_is_compiler_fusion.md`.
Existing precedent for the same exemption: `tests/test_trajectory_collection.py:670`.

WHAT NOT TO DO WHEN THIS GOES RED. Do not widen the tolerance, and in particular do
not convert the Olfaction bound into a global `np.allclose` — that silently retires
the instrument every later "bit-identical" claim rests on. Stop and diff.
"""
import os

# Backend pinning MUST precede any jax import: fixtures generated on GPU and compared
# on CPU differ in the last bits and the gate becomes noise. Same form as
# tests/test_trajectory_collection.py:66 and the fixture generator.
os.environ.setdefault("JAX_PLATFORMS", "cpu")

import glob
import re
import sys
import traceback

import numpy as np
import pytest

# Ensure project root on sys.path
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, _ROOT)

import jax
import yaml

from src.utils.config import Config
from src.environment.config_loader import load_env_params
from src.environment.core import jax_reset, jax_step, calculate_drive
from src.environment.sensor import get_observation, get_observation_breakdown

FIXTURE_DIR = os.path.join(_ROOT, "tests", "env", "fixtures", "thermal_parity")
ACTIONS = [0, 1, 2, 3, 4] * 20  # 100 steps — must match the generator
SEED = 0

# The three sampled-property state arrays, paired with the EnvParams std array that
# says which of their elements are allowed to move at all.
_PROPERTY_PAIRS = (
    ("animal_property_sampled", "animal_property_std"),
    ("res_property_sampled", "res_property_std"),
    ("obs_property_sampled", "obs_property_std"),
)


def _config_slug(config_path: str) -> str:
    """Matches generate_thermal_parity_fixtures.py:config_slug (and the CP1 generator)."""
    rel = os.path.relpath(config_path, _ROOT)
    slug = re.sub(r'[/\\]', '__', rel)
    slug = re.sub(r'\.yaml$', '', slug)
    slug = re.sub(r'[^A-Za-z0-9_.-]', '_', slug)
    return slug


def _collect_configs():
    """Matches generate_thermal_parity_fixtures.py:collect_configs."""
    configs = []
    configs += sorted(glob.glob(os.path.join(_ROOT, "configs", "environment", "experiment", "**", "*.yaml"), recursive=True))
    configs += sorted(glob.glob(os.path.join(_ROOT, "configs", "continual", "**", "*.yaml"), recursive=True))
    configs += sorted(glob.glob(os.path.join(_ROOT, "configs", "verification", "**", "*.yaml"), recursive=True))
    env_default = os.path.join(_ROOT, "configs", "environment", "default.yaml")
    if env_default not in configs:
        configs.append(env_default)
    return configs


def _ulp32(x: np.ndarray) -> np.ndarray:
    """Size of one float32 ulp at each element's magnitude (0 -> the subnormal step)."""
    mag = np.abs(np.asarray(x, dtype=np.float32))
    return (np.nextafter(mag, np.float32(np.inf)) - mag).astype(np.float64)


def _run_episode(params):
    """Reset + 100 steps, recording exactly what the generator recorded."""
    state = jax_reset(params, jax.random.PRNGKey(SEED))

    def snap(s):
        return {
            "key": np.array(s.key),
            "animal_property_sampled": np.array(s.animal_property_sampled),
            "res_property_sampled": np.array(s.res_property_sampled),
            "obs_property_sampled": np.array(s.obs_property_sampled),
            "res_pos": np.array(s.res_pos),
            "animal_pos": np.array(s.animal_pos),
            "obs_pos": np.array(s.obs_pos),
            "obs_clean": np.array(get_observation(s, params, apply_noise=False)),
            "obs_noisy": np.array(get_observation(s, params, apply_noise=True)),
            "drive": np.array(calculate_drive(s.satiation, s.injury_level, params)),
        }

    per_state = [snap(state)]
    per_step = []
    for action in ACTIONS:
        state, reward, done, info = jax_step(state, action, params)
        per_state.append(snap(state))
        per_step.append({
            "reward": np.array(reward),
            "done": np.array(done),
            "termination_reason": np.array(info["termination_reason"]),
        })

    got = {name: np.stack([s[name] for s in per_state]) for name in per_state[0]}
    got.update({name: np.stack([s[name] for s in per_step]) for name in per_step[0]})
    got["drive_before"] = got["drive"][:-1]
    got["drive_after"] = got["drive"][1:]
    return got


def _olfaction_slice(params):
    """(start, length, n_cells, n_channels) of the Olfaction block, or None if absent.

    `get_observation_breakdown` emits its keys in the same order `get_observation`
    concatenates its parts, so a running sum over the dict gives the slice offset.
    """
    offset = 0
    for name, dim in get_observation_breakdown(params).items():
        if name == "Olfaction":
            n_channels = int(params.res_property.shape[-1])
            return offset, int(dim), int(dim) // n_channels, n_channels
        offset += int(dim)
    return None


def _olfaction_tolerance(params, fixture, got, n_cells, n_channels):
    """DERIVE the Olfaction bound from the per-element property bound above.

    Derivation (this is the whole point of the stage — it is a consequence of the
    <=1 ulp state-array bound, not an independent allowance):

      Olfaction at one sampling cell is a three-pool weighted sum
      (`sensor.py:_sense_olfaction_at`, over resources + animals + obstacles):

          obs[cell, v] = SUM_e  prop_sampled[e, v] * w(dist(cell, e)) * mask_e

      so a perturbation of the property arrays propagates linearly:

          |d obs[cell, v]| <= SUM_e |d prop[e, v]| * w_max

      * `|d prop[e, v]|` is bounded above by ONE float32 ulp at that element's
        magnitude, and is exactly zero wherever `properties_std[e, v] == 0` —
        that is the exemption asserted directly on the state arrays.
      * `w_max` is the largest weight `sense_resource` can produce
        (`sensor.py:19-21`): `1 / 0.5**decay_power` when the agent stands on the
        entity, and at most `1 / (1**p + 1e-10) < 1` for any other integer-grid
        cell. So `w_max = max(2**decay_power, 1.0)`.
      * Every entity is counted at `w_max` and the radius mask is ignored, which
        can only make the bound looser, never tighter — and the bound is still
        exactly ZERO when no entity declares a non-zero std, so the check stays a
        strict equality wherever there is nothing legitimate to diverge.

    The same array bounds the NOISY observation: `apply_perceptual_noise` computes
    `clip(obs + noise, lo, hi)` with the noise drawn from `fold_in(state.key, 999)`,
    and `state.key` is asserted exactly equal, so the noise term is identical and
    the clip is monotone — the difference can only shrink.

    Returned shape is the flattened Olfaction slice (cell-major: cell 0's channels,
    then cell 1's, ...), so it lines up element-for-element with the observation.
    """
    w_max = max(2.0 ** float(params.sensor_decay), 1.0)

    per_channel = np.zeros(n_channels, dtype=np.float64)
    for state_field, std_field in _PROPERTY_PAIRS:
        std = np.array(getattr(params, std_field))          # [E, V]
        if std.size == 0:
            continue
        perturbable = (std != 0)                            # [E, V]
        # Use the larger of the two magnitudes so the ulp is not understated when
        # the two runs straddle a binade boundary.
        mag = np.maximum(np.abs(fixture[state_field]), np.abs(got[state_field]))  # [T, E, V]
        elem_ulp = _ulp32(mag).max(axis=0)                  # [E, V] — worst step
        per_channel += (elem_ulp * perturbable).sum(axis=0) * w_max

    return np.tile(per_channel, n_cells)


# ── Collect test cases ────────────────────────────────────────────────────────

_test_params = []
for _cfg_path in _collect_configs():
    _slug = _config_slug(_cfg_path)
    _test_params.append((_cfg_path, _slug,
                         os.path.exists(os.path.join(FIXTURE_DIR, _slug + ".npz"))))


@pytest.mark.parametrize("config_path,slug,has_fixture", _test_params,
                         ids=[p[1] for p in _test_params])
def test_thermal_parity(config_path, slug, has_fixture):
    """100 steps from seed 0 reproduce the committed pre-thermal reference exactly."""
    if not has_fixture:
        pytest.skip(f"No thermal-parity fixture for {slug}")

    with open(config_path) as f:
        cfg_dict = yaml.safe_load(f)
    try:
        params = load_env_params(Config(cfg_dict))
    except Exception as e:
        pytest.fail(f"Config load failed ({config_path}): {e}")

    fixture = np.load(os.path.join(FIXTURE_DIR, slug + ".npz"))

    try:
        got = _run_episode(params)
    except Exception:
        pytest.fail(f"Episode failed ({config_path}): {traceback.format_exc()}")

    # ── Exact: the observation's own shape contract ───────────────────────────
    breakdown_total = int(sum(get_observation_breakdown(params).values()))
    assert breakdown_total == int(fixture["obs_breakdown_total"]), (
        f"{slug}: sum(get_observation_breakdown(params).values()) changed "
        f"{int(fixture['obs_breakdown_total'])} -> {breakdown_total}"
    )
    assert got["obs_clean"].shape[-1] == int(fixture["obs_dim"]), (
        f"{slug}: observation dimension changed "
        f"{int(fixture['obs_dim'])} -> {got['obs_clean'].shape[-1]}"
    )

    # ── Exact: PRNG stream, reward, drive, termination, placement ─────────────
    # `key` first — it is the tripwire. If the PRNG stream moved, every other
    # difference below is a consequence rather than an independent finding.
    for field in ("key", "reward", "done", "termination_reason",
                  "drive_before", "drive_after",
                  "res_pos", "animal_pos", "obs_pos"):
        assert np.array_equal(got[field], fixture[field]), (
            f"{slug}: '{field}' is not byte-identical to the pre-thermal reference. "
            f"This is a regression — diff it, do not widen a tolerance."
        )

    # ── The ONE exemption: sampled-property arrays, <= 1 ulp, std != 0 only ───
    # Anchored on the STATE arrays because that is where the measured bound lives.
    # Elements whose entity declares properties_std == 0 have nothing to diverge,
    # so they are held to exact equality; the exemption is a commented branch and
    # never a global tolerance.
    for state_field, std_field in _PROPERTY_PAIRS:
        want, have = fixture[state_field], got[state_field]
        assert want.shape == have.shape, f"{slug}: '{state_field}' shape changed"
        if want.size == 0:
            continue
        diff = np.abs(have.astype(np.float64) - want.astype(np.float64))
        std = np.array(getattr(params, std_field))                    # [E, V]
        perturbable = np.broadcast_to((std != 0)[None, ...], diff.shape)

        # (a) properties_std == 0 -> exact, no exemption.
        assert not np.any(diff[~perturbable]), (
            f"{slug}: '{state_field}' differs on elements whose config declares "
            f"properties_std == 0. Nothing there can legitimately diverge — regression."
        )
        # (b) properties_std != 0 -> at most one float32 ulp (compiler fusion).
        allowed = _ulp32(np.maximum(np.abs(want), np.abs(have)))
        bad = perturbable & (diff > allowed)
        assert not np.any(bad), (
            f"{slug}: '{state_field}' exceeds the documented one-float32-ulp bound on "
            f"{int(bad.sum())} element(s); max excess "
            f"{float((diff - allowed)[bad].max()):.3e}. The ulp exemption covers "
            f"compiler fusion only — a larger difference is a regression."
        )

    # ── Observation: exact everywhere except a DERIVED Olfaction bound ────────
    olf = _olfaction_slice(params)
    if olf is None:
        olf_tol = None
    else:
        olf_start, olf_len, n_cells, n_channels = olf
        olf_tol = _olfaction_tolerance(params, fixture, got, n_cells, n_channels)
        assert olf_tol.shape[0] == olf_len  # derivation must cover the whole slice

    for field in ("obs_clean", "obs_noisy"):
        want, have = fixture[field], got[field]
        assert want.shape == have.shape, f"{slug}: '{field}' shape changed"
        if olf is None:
            assert np.array_equal(have, want), (
                f"{slug}: '{field}' is not byte-identical to the pre-thermal reference."
            )
            continue

        # Everything outside the Olfaction slice: byte-identical, no exception.
        head_ok = np.array_equal(have[:, :olf_start], want[:, :olf_start])
        tail_ok = np.array_equal(have[:, olf_start + olf_len:],
                                 want[:, olf_start + olf_len:])
        assert head_ok and tail_ok, (
            f"{slug}: '{field}' differs OUTSIDE the Olfaction slice "
            f"[{olf_start}:{olf_start + olf_len}]. The ulp exemption does not reach "
            f"here — this is a regression."
        )

        # Olfaction: the derived bound, which is exactly 0.0 for every config whose
        # entities all declare properties_std == 0.
        olf_diff = np.abs(have[:, olf_start:olf_start + olf_len].astype(np.float64)
                          - want[:, olf_start:olf_start + olf_len].astype(np.float64))
        bad = olf_diff > olf_tol[None, :]
        assert not np.any(bad), (
            f"{slug}: '{field}' Olfaction slice exceeds the derived bound on "
            f"{int(bad.sum())} element(s); max diff {float(olf_diff.max()):.3e} vs "
            f"derived tolerance {float(olf_tol.max()):.3e}. Do NOT widen this into a "
            f"global allclose — re-derive it or treat it as a regression."
        )
