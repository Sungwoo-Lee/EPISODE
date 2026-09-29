"""Unit tests for the refusals of scripts/analysis/nmn/run_wakeup.py (plan File Changes §11)."""
import os
import sys

import numpy as np
import pytest
import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
from scripts.analysis.nmn import run_wakeup as rw  # noqa: E402

MAN = os.path.join(ROOT, "docs/experiments/active/modulator_clues/algorithmic_null_wakeup.yaml")


def _write(tmp_path, man):
    p = tmp_path / "m.yaml"
    p.write_text(yaml.safe_dump(man))
    return p


def test_real_manifest_loads():
    man = rw.load_manifest(MAN)
    assert len(man["runs"]) == 19


def test_point_set_key_raises(tmp_path):
    man = yaml.safe_load(open(MAN))
    man["sparse_measure_points"] = {"freeze": [1, 5, 10]}
    with pytest.raises(ValueError, match="per-measure point set"):
        rw.load_manifest(_write(tmp_path, man))
    man = yaml.safe_load(open(MAN))
    man["runs"][0]["freeze_checkpoints"] = [200019]
    with pytest.raises(ValueError, match="per-measure point set"):
        rw.load_manifest(_write(tmp_path, man))


def test_wakeup_block_must_equal_rules():
    man = rw.load_manifest(MAN)
    settings = dict(man["wakeup"])
    rw.check_wakeup_block(man, settings)
    with pytest.raises(ValueError, match="differ"):
        rw.check_wakeup_block(man, {**settings, "noise_k": 2})
    with pytest.raises(ValueError, match="keys"):
        rw.check_wakeup_block(man, {k: v for k, v in settings.items() if k != "sustain"})


def test_grid_is_the_checkpoint_list_with_step0_when_anchorable():
    run = {"label": "r", "checkpoints": [10, 20, 30]}
    assert rw.grid_x(run, True).tolist() == [0, 10, 20, 30]
    assert rw.grid_x(run, False).tolist() == [10, 20, 30]
    rw.assert_curve_grid(run, "freeze", np.array([0, 10, 20, 30]))
    with pytest.raises(AssertionError):
        rw.assert_curve_grid(run, "freeze", np.array([0, 10, 30]))
    with pytest.raises(AssertionError):
        rw.assert_curve_grid(run, "plateau", np.array([0, 10, 20, 30]))


def test_out_root_is_required(tmp_path):
    """out_root is a required manifest key (set by the designer at R.2); there is no
    --out-root CLI argument to fall back on."""
    man = yaml.safe_load(open(MAN))
    del man["out_root"]
    with pytest.raises(ValueError, match="out_root"):
        rw.load_manifest(_write(tmp_path, man))
    with pytest.raises(SystemExit):
        rw.main(["--manifest", MAN, "--measures", "plateau", "--out-root", str(tmp_path)])


def _scan_result(stages, truncated):
    rows = [{"Episode/Number": 1.0, "stage/index": float(s)} for s in stages]
    return {"rows": rows, "exit_code": None, "file": "synthetic.wandb", "truncated": truncated}


def test_truncated_read_needs_a_later_stage(monkeypatch):
    """O1: a half-written trailing record is accepted only for a continual run whose stage
    read (stage 0) is followed by logged rows of a later stage; otherwise the run stops."""
    from scripts.analysis.nmn import wandb_history as wh
    monkeypatch.setattr(wh, "scan", lambda d, allow_truncated: _scan_result([0, 0, 1], "AssertionError"))
    assert rw.read_scanned("may", "d", 0)["truncated"] == "AssertionError"
    monkeypatch.setattr(wh, "scan", lambda d, allow_truncated: _scan_result([0, 0], "AssertionError"))
    with pytest.raises(RuntimeError, match="no later stage"):
        rw.read_scanned("may", "d", 0)
    monkeypatch.setattr(wh, "scan", lambda d, allow_truncated: _scan_result([], "AssertionError"))
    with pytest.raises(RuntimeError):
        rw.read_scanned("l05", "d", None)              # a non-continual run: never accepted
    monkeypatch.setattr(wh, "scan", lambda d, allow_truncated: _scan_result([0], None))
    assert rw.read_scanned("l05", "d", None)["truncated"] is None


def test_plateau_is_numbered_on_the_run_scale():
    """O2: the plateau curve is unanchored (array index 0 = checkpoint 1); the table's
    t_plateau_checkpoint is wakeup.position(t), i.e. index + 1, the scale every lag uses."""
    from scripts.analysis.nmn import wakeup
    B2 = {"threshold_mode_headline": "fraction_of_rise", "plateau_f": 0.9, "sustain": 2,
          "final_k": 3, "noise_k": 3, "min_noise_points": 5, "noise_window_divisor": 3,
          "noise_window_max_fraction": 0.5}                       # test fixture values
    surv = {"row_weight": "delta_episode_number", "min_window_n": 1000}
    rng = np.random.default_rng(0)
    rows = [{"Episode/Number": 4000.0 * (i + 1), "Episode/_window_n": 4000.0,
             "Episode/Steps": 100 + 100 * min(1.0, (i + 1) / 200) + rng.normal(0, 1)}
            for i in range(750)]
    cks = [100000 * (i + 1) for i in range(30)]
    r, m, info = rw.plateau_crossing("synthetic", rows, rw.grid_x({"checkpoints": cks}, False),
                                     B2, surv)
    assert r.anchored is False and r.index is not None
    assert wakeup.position(r.t, cks) == r.index + 1 == cks.index(int(r.t)) + 1
    assert info["start_counter"] == 0.0 and len(m) == 30
