"""launch_collection.py `--logs` (tooling plan ALGORITHMIC_NULL_ANALYSIS_TOOLING File Changes §12).

A listed log that names a finished run is read; a missing or empty listed file raises; giving
both `--logs` and `--logs-glob` (or neither) is refused.
"""
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    "launch_collection",
    ROOT / "scripts/analysis/studies/level05_body_interactions/launch_collection.py")
lc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lc)


def _log(tmp_path, name, text):
    p = tmp_path / name
    p.write_text(text)
    return p


def test_listed_log_names_finished_run(tmp_path):
    done = _log(tmp_path, "a.log", "noise\nTraining complete. Results saved to "
                "results/JAX_RecurrentPPO/20260929-153635_rppo_cw_mayrep_t1none_s42\n")
    running = _log(tmp_path, "b.log", "Episode 3700000 ...\n")
    files = lc.log_files(logs=[str(done), str(running)])
    assert lc.finished_runs(files) == {"20260929-153635_rppo_cw_mayrep_t1none_s42"}


def test_missing_listed_log_raises(tmp_path):
    with pytest.raises(ValueError, match="does not exist"):
        lc.log_files(logs=[str(tmp_path / "nope.log")])


def test_empty_listed_log_raises(tmp_path):
    empty = _log(tmp_path, "empty.log", "")
    with pytest.raises(ValueError, match="empty"):
        lc.log_files(logs=[str(empty)])


def test_both_flags_refused(tmp_path):
    f = _log(tmp_path, "a.log", "x\n")
    with pytest.raises(SystemExit):
        lc.main(["spec.yaml", "--logs-glob", "logs/*.log", "--logs", str(f),
                 "--nodes", "106", "--dry-run"])
    with pytest.raises(ValueError, match="exactly one"):
        lc.log_files(logs_glob="logs/*.log", logs=[str(f)])


def test_neither_flag_refused():
    with pytest.raises(SystemExit):
        lc.main(["spec.yaml", "--nodes", "106", "--dry-run"])
