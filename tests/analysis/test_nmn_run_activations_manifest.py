"""Reader side of Revision 4, R4-1 (tooling plan ALGORITHMIC_NULL_ANALYSIS_TOOLING): how
`probes[].store_matmul_precision` resolves against a store manifest's recorded mode, and
that `capture_matmul_precision` accepts only `highest`. Pure python; no JAX, no data."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))

from scripts.analysis.nmn import run_activations as ra   # noqa: E402

PILOT = _ROOT / "docs" / "experiments" / "active" / "modulator_clues" / "algorithmic_null_pilot.yaml"


def test_recorded_on_a_recording_store_uses_the_recorded_mode():
    assert ra.resolve_store_precision("recorded", "highest", "s") == "highest"


def test_recorded_on_a_legacy_store_raises():
    with pytest.raises(ValueError, match="records no matmul_precision"):
        ra.resolve_store_precision("recorded", None, "s")


def test_explicit_value_matching_the_recorded_mode_is_accepted():
    assert ra.resolve_store_precision("highest", "highest", "s") == "highest"


def test_explicit_value_conflicting_with_the_recorded_mode_raises():
    with pytest.raises(ValueError, match="conflicts"):
        ra.resolve_store_precision("default", "highest", "s")


@pytest.mark.parametrize("entry", ["highest", "default"])
def test_explicit_value_on_a_legacy_store_is_accepted(entry):
    assert ra.resolve_store_precision(entry, None, "s") == entry


def test_unknown_entry_raises():
    with pytest.raises(ValueError, match="must be one of"):
        ra.resolve_store_precision("tf32", None, "s")


def _write(tmp_path, man) -> Path:
    p = tmp_path / "m.yaml"
    p.write_text(yaml.safe_dump(man))
    return p


def test_pilot_manifest_loads_unchanged():
    man = ra.load_manifest(PILOT)
    assert man["capture_matmul_precision"] == "highest"
    assert [p["store_matmul_precision"] for p in man["probes"]][0] == ["highest", "default"]


def test_capture_precision_default_raises(tmp_path):
    man = yaml.safe_load(PILOT.read_text())
    man["capture_matmul_precision"] = "default"
    with pytest.raises(ValueError, match="capture_matmul_precision"):
        ra.load_manifest(_write(tmp_path, man))


def test_manifest_accepts_recorded_and_rejects_unknown_store_entries(tmp_path):
    man = yaml.safe_load(PILOT.read_text())
    ok = copy.deepcopy(man)
    for p in ok["probes"]:
        p["store_matmul_precision"] = ["recorded"] * len(p["stores"])
    ra.load_manifest(_write(tmp_path, ok))
    bad = copy.deepcopy(man)
    bad["probes"][0]["store_matmul_precision"] = ["tf32"] * len(bad["probes"][0]["stores"])
    with pytest.raises(ValueError, match="store_matmul_precision"):
        ra.load_manifest(_write(tmp_path, bad))
