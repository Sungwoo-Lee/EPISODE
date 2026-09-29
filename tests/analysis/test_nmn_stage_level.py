"""Tests for scripts/analysis/nmn/wandb_history.py (plan File Changes §7).

Synthetic rows (hand-computed values), plus two tests on the real local WandB binaries of
the six May-replication runs, marked `integration` (slow; skipped when the binaries are absent):
the Checkpoint 4.6 cross-check against pilot_readout, and the truncated-record handling of
`scan` on a cut copy of a real binary.
"""
import importlib.util
import json
import os
import shutil
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


def _pilot_readout():
    spec = importlib.util.spec_from_file_location(
        "pilot_readout", os.path.join(ROOT, "scripts/analysis/studies/continual_worlds/pilot_readout.py"))
    pr = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pr)
    return pr


def test_matches_pilot_readout_series():
    pr = _pilot_readout()
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
    v, info = wh.stage_level(_scanned(s0 + s1), 0, (0.0, 400000.0), "Episode/Steps", 200000, 1000,
                             "delta_episode_number")
    # last row at 400,000: window rows in (200,000, 400,000] are i = 50..99, equal weights
    assert v == pytest.approx(np.mean([100 + i for i in range(50, 100)]))
    assert info["rows_used"] == 50 and info["reached_boundary"]


def test_stage_level_incomplete_is_none():
    s0, _ = _two_stage()
    v, info = wh.stage_level(_scanned(s0), 0, (0.0, 400000.0), "Episode/Steps", 200000, 1000,
                             "delta_episode_number")
    assert v is None and "not complete" in info["reason"]
    v2, _ = wh.stage_level(_scanned(s0, exit_code=0), 0, (0.0, 400000.0), "Episode/Steps", 200000,
                           1000, "delta_episode_number")
    assert v2 is not None


def test_stage_level_short_stage_is_none():
    s0, s1 = _two_stage()
    v, info = wh.stage_level(_scanned(s0 + s1), 1, (400000.0, 800000.0), "Episode/Steps", 200000,
                             1000, "delta_episode_number")
    assert v is None


def test_stage_rows_selection_is_pilot_readouts():
    """M3: rows are stage/index == k AND lo < Episode/Number <= hi + 4000 (pilot_readout l.667),
    and the series starts at lo. Planted: a stage-0 row past hi + 4000 (dropped), one exactly at
    hi + 4000 (kept), a stage-1 row inside stage 0's bounds (dropped), a stage-0 row at or below
    lo (dropped). The level equals pilot_readout.last_level(Series(srows, lo)) exactly."""
    pr = _pilot_readout()
    lo, hi = 100000.0, 500000.0
    rows = ([_row(lo, 999, stage=0), _row(lo - 4000, 999, stage=0)]
            + [_row(lo + 4000 * (i + 1), 100 + (i % 17), stage=0, wn=(4000 if i == 0 else 5000))
               for i in range(100)]
            + [_row(hi + 4000, 150, stage=0), _row(hi + 8000, 999, stage=0),
               _row(hi - 2000, 999, stage=1)]
            + [_row(hi + 4000 * (i + 3), 300, stage=1) for i in range(5)])
    sel = wh.stage_rows(_scanned(rows), 0, (lo, hi))
    want = sorted([r for r in rows if lo < r[N] <= hi + 4000 and int(r.get(ST, -1)) == 0],
                  key=lambda r: r[N])
    assert sel == want and len(sel) == 101
    v, info = wh.stage_level(_scanned(rows), 0, (lo, hi), "Episode/Steps", pr.LEVEL_WINDOW,
                             pr.MIN_WINDOW_N, "delta_episode_number")
    assert v == pr.last_level(pr.Series(want, lo)) and info["last_episode"] == hi + 4000


def test_stage_bounds_must_be_ordered():
    with pytest.raises(ValueError):
        wh.stage_rows(_scanned([]), 0, (400000.0, 400000.0))


# ------------------------------------------------ Checkpoint 4.6: the six real May runs
MAY_DOC = "docs/experiments/active/continual_worlds/MAY_DOUBLE_RETURN_REPLICATION.md"
INTERIM_MANIFEST = "docs/experiments/active/modulator_clues/algorithmic_null_mayrep_interim.yaml"
OUT_46 = os.path.join(ROOT, "tmp", "checkpoint_4_6_stage1.json")


def _may_runs(pr):
    if not os.path.exists(os.path.join(ROOT, MAY_DOC)):
        pytest.skip("May design doc absent")
    man = pr.parse_manifest(open(os.path.join(ROOT, MAY_DOC)).read(), id_prefix=pr.MR_ID_PREFIX,
                            allow_empty=True)
    if len(man) != 6:
        pytest.skip(f"expected the six May-replication runs in the design manifest, got {len(man)}")
    try:
        for m in man:
            pr.wandb_dir(m["wandb_id"])
    except ValueError as e:
        pytest.skip(f"local WandB binaries absent: {e}")
    return man


@pytest.mark.integration
def test_checkpoint_4_6_may_stage1_equals_pilot_readout():
    """Checkpoint 4.6: for all six May-replication runs, stage_level on stage 1 (stage/index =
    gates.G5.stage - 1, from the pinned rules) with the rules' window, row weighting and
    _window_n skip gives S_1 and bites equal to pilot_readout's May readout (mayrep_run) to
    1e-9 relative. The window_n-weighted values are recorded beside them as a diagnostic.
    Numbers are written to tmp/checkpoint_4_6_stage1.json for the Implementation Report."""
    import yaml
    from scripts.analysis.nmn import decision_rules as dr
    pr = _pilot_readout()
    man = _may_runs(pr)
    P = dr.load(yaml.safe_load(open(os.path.join(ROOT, INTERIM_MANIFEST)))).parameters
    surv, k = dr.survival_settings(P), dr.g5_stage_index(P)
    assert k == 0
    table = []
    for m in man:
        d = pr.read_run(m, {})
        ref = pr.mayrep_run(d)["stages"][k + 1]
        assert ref["complete"], f"{m['tag']}: pilot_readout says stage 1 is not complete"
        wdir = wh.resolve_by_tag(m["tag"])
        assert os.path.relpath(wdir, ROOT) == d["wandb_dir"]          # resolver reproduces §C
        scanned = wh.scan(wdir, allow_truncated=True)
        args = pr.launch_args(str(wdir))
        import yaml as _y
        hi = float(_y.safe_load(open(os.path.join(ROOT, pr.arg(args, "--continual-schedule"))))
                   ["continual"]["episode_boundaries"][k])
        lo = wh.start_counter(wh.episode_rows(scanned, None))
        assert lo == d["start_counter"]
        row = {"tag": m["tag"], "bounds": [lo, hi], "wandb_truncated": scanned["truncated"],
               "pilot_S1": ref["S"], "pilot_bites": ref["bites"]}
        for key, name in (("Episode/Steps", "S1"), ("Episode/FoodEaten", "bites")):
            v, info = wh.stage_level(scanned, k, (lo, hi), key, surv["window_episodes"],
                                     surv["min_window_n"], surv["row_weight"])
            vw, _ = wh.stage_level(scanned, k, (lo, hi), key, surv["window_episodes"],
                                   surv["min_window_n"], "window_n")
            row[name], row[name + "_window_n"], row[name + "_rows_used"] = v, vw, info["rows_used"]
            p = row["pilot_" + name]
            row[name + "_rel_diff"] = abs(v - p) / abs(p)
        table.append(row)
    os.makedirs(os.path.dirname(OUT_46), exist_ok=True)
    json.dump({"rules": {"row_weight": surv["row_weight"], "window": surv["window_episodes"],
                         "min_window_n": surv["min_window_n"], "stage_index": k},
               "runs": table}, open(OUT_46, "w"), indent=1)
    for r in table:
        assert r["S1_rel_diff"] <= 1e-9 and r["bites_rel_diff"] <= 1e-9, r


@pytest.mark.integration
def test_scan_truncated_trailing_record(tmp_path):
    """O1: a copy of a real May binary cut mid-record. allow_truncated=False raises;
    allow_truncated=True stops at the cut and says so, and returns the rows before it. A
    record corrupted before the last block raises either way."""
    pr = _pilot_readout()
    man = _may_runs(pr)
    src = [f for f in os.listdir(pr.wandb_dir(man[0]["wandb_id"])) if f.endswith(".wandb")][0]
    src = os.path.join(pr.wandb_dir(man[0]["wandb_id"]), src)
    cut = tmp_path / "cut"
    cut.mkdir()
    with open(src, "rb") as f:
        data = f.read(3 * 32768 + 12345)                 # mid-record in the fourth block
    (cut / "run-cut.wandb").write_bytes(data)
    with pytest.raises(RuntimeError, match="unreadable record"):
        wh.scan(cut, allow_truncated=False)
    got = wh.scan(cut, allow_truncated=True)
    assert got["truncated"] and len(got["rows"]) > 0
    bad = tmp_path / "bad"
    bad.mkdir()
    shutil.copy(src, bad / "run-bad.wandb")
    with open(bad / "run-bad.wandb", "r+b") as f:
        f.seek(40000)
        f.write(b"\xff" * 64)                            # corrupt the second block
        f.truncate(8 * 32768)
    with pytest.raises(RuntimeError, match="before the last block"):
        wh.scan(bad, allow_truncated=True)


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
