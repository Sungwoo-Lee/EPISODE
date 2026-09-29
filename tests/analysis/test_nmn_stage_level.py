"""Tests for scripts/analysis/nmn/wandb_history.py (plan File Changes §7).

Synthetic rows only (hand-computed values); the real-binary cross-check against
pilot_readout (Checkpoint 4.6) is a separate slow test, not written yet.
"""
import importlib.util
import json
import os
import sys

import numpy as np
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
from scripts.analysis.nmn import wandb_history as wh  # noqa: E402

N, WN, ST = "Episode/Number", "Episode/_window_n", "stage/index"


def _row(num, steps, wn=5000, stage=None, **kw):
    r = {N: float(num), WN: float(wn), "Episode/Steps": float(steps), **kw}
    if stage is not None:
        r[ST] = float(stage)
    return r


def _scanned(rows, exit_code=None):
    return {"rows": rows, "exit_code": exit_code, "file": "synthetic"}


# ------------------------------------------------------------------------------- weighting
def test_delta_weighting_and_skip_by_hand():
    rows = [_row(4000, 10, wn=4000), _row(8000, 20, wn=500), _row(12000, 30), _row(20000, 40)]
    kept = wh.weighted(rows, 0.0, "delta_episode_number", 1000)
    # the 8000 row is skipped (window 500 < 1000) and its 4000 episodes are NOT handed on
    assert [(e, w) for e, w, _ in kept] == [(4000, 4000), (12000, 4000), (20000, 8000)]
    kept_w = wh.weighted(rows, 0.0, "window_n", 1000)
    assert [w for _, w, _ in kept_w] == [4000, 5000, 5000]


def test_unknown_weighting_raises():
    with pytest.raises(ValueError):
        wh.weighted([_row(4000, 1)], 0.0, "rows", 1000)


def test_interval_means_by_hand():
    rows = [_row(4000, 10, wn=4000), _row(8000, 20), _row(12000, 30), _row(20000, 40)]
    m, info = wh.interval_means(rows, "Episode/Steps", [0, 10000, 20000], "delta_episode_number", 1000)
    assert m[0] == pytest.approx((10 * 4000 + 20 * 4000) / 8000)
    assert m[1] == pytest.approx((30 * 4000 + 40 * 8000) / 12000)
    assert info["rows_per_interval"] == [2, 2]


def test_interval_empty_is_nan_not_filled():
    rows = [_row(4000, 10, wn=4000), _row(8000, 20)]
    m, info = wh.interval_means(rows, "Episode/Steps", [0, 8000, 16000], "delta_episode_number", 1000)
    assert np.isnan(m[1]) and info["empty_intervals"] == [1]


def test_matches_pilot_readout_series():
    spec = importlib.util.spec_from_file_location(
        "pilot_readout", os.path.join(ROOT, "scripts/analysis/studies/continual_worlds/pilot_readout.py"))
    pr = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pr)
    rng = np.random.default_rng(0)
    rows = [_row(4000 * (i + 1), rng.uniform(50, 250), wn=(4000 if i == 0 else rng.choice([800, 5000])))
            for i in range(200)]
    ser = pr.Series(rows, 0.0)
    kept = wh.weighted(rows, 0.0, "delta_episode_number", pr.MIN_WINDOW_N)
    assert np.array_equal(ser.w, np.array([w for _, w, _ in kept]))
    m, _ = wh.interval_means(rows, "Episode/Steps", [0, 400000, 800000], "delta_episode_number",
                             pr.MIN_WINDOW_N)
    assert m[1] == pytest.approx(ser.S(400000, 800000), rel=1e-12)


# ----------------------------------------------------------------------------- stage level
def _two_stage():
    s0 = [_row(4000 * (i + 1), 100 + i, stage=0, wn=(4000 if i == 0 else 5000)) for i in range(100)]
    s1 = [_row(400000 + 4000 * (i + 1), 200, stage=1) for i in range(10)]
    return s0, s1


def test_stage_level_last_window_by_hand():
    s0, s1 = _two_stage()
    v, info = wh.stage_level(_scanned(s0 + s1), 0, "Episode/Steps", 200000, 1000,
                             "delta_episode_number", stage_start=0.0)
    # last row at 400,000: window rows in (200,000, 400,000] are i = 50..99, equal weights
    assert v == pytest.approx(np.mean([100 + i for i in range(50, 100)]))
    assert info["rows_used"] == 50


def test_stage_level_incomplete_is_none():
    s0, _ = _two_stage()
    v, info = wh.stage_level(_scanned(s0), 0, "Episode/Steps", 200000, 1000,
                             "delta_episode_number", stage_start=0.0)
    assert v is None and "not complete" in info["reason"]
    v2, _ = wh.stage_level(_scanned(s0, exit_code=0), 0, "Episode/Steps", 200000, 1000,
                           "delta_episode_number", stage_start=0.0)
    assert v2 is not None


def test_stage_level_short_stage_is_none():
    s0, s1 = _two_stage()
    v, info = wh.stage_level(_scanned(s0 + s1), 1, "Episode/Steps", 200000, 1000,
                             "delta_episode_number", stage_start=400000.0)
    assert v is None


# --------------------------------------------------------------------------- tag + join
def _fake_wandb(tmp_path, tags):
    for i, t in enumerate(tags):
        d = tmp_path / f"run-2026_{i}-id{i}" / "files"
        d.mkdir(parents=True)
        (d / "wandb-metadata.json").write_text(json.dumps({"args": ["--tag", t, "--seed", "42"]}))
    return str(tmp_path)


def test_resolve_by_tag_exactly_one(tmp_path):
    root = _fake_wandb(tmp_path, ["a", "b", "b"])
    assert wh.resolve_by_tag("a", root).name == "run-2026_0-id0"
    with pytest.raises(ValueError, match="found 2"):
        wh.resolve_by_tag("b", root)
    with pytest.raises(ValueError, match="found 0"):
        wh.resolve_by_tag("c", root)


def test_read_keys_join_by_timesteps_and_own_number():
    rows = [_row(4000, 1, timesteps=100.0), _row(8000, 1, timesteps=374374400.0),
            {"loss/grad_norm": 2.0, "timesteps": 3.743744e+08},          # level-05 form
            {"loss/grad_norm": 3.0, N: 12000.0},                           # May form
            {"loss/grad_norm": 4.0, "timesteps": 5.0}]                     # unmatched
    out, info = wh.read_keys(_scanned(rows), ["loss/grad_norm"])
    e, v = out["loss/grad_norm"]
    assert e.tolist() == [8000.0, 12000.0] and v.tolist() == [2.0, 3.0]
    assert info["loss/grad_norm"]["unmatched"] == 1
