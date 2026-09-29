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
