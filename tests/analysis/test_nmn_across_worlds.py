"""A4 driver (scripts/analysis/nmn/run_across_worlds.py), tooling plan §A1/A3/A4 statistics (A4).

- The signed A4 fixture table (tests/analysis/test_nmn_decision_rules.py, TABLE 9, Checkpoint
  R.2) goes through the driver's own `evaluate` and gives every expected reading.
- End to end on a synthetic two-world capture directory (test fixture data, never study data),
  against the real pinned rules: similarity first (the primary cell), then A4. The output is
  stamped, has the rules' A4 layout, one A1 cell per stage end on that stage's own world, an
  8-entry movement profile per agent, and an evaluate_A4 reading per layer; a movement entry
  equals a direct run_similarity.predictivity on the same captures.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("JAX_PLATFORMS", "cpu")

from scripts.analysis.nmn import decision_rules as dr  # noqa: E402
from scripts.analysis.nmn import driver_io as dio  # noqa: E402
from scripts.analysis.nmn import run_across_worlds as a4  # noqa: E402
from tests.analysis import nmn_synthetic as syn  # noqa: E402
from tests.analysis import test_nmn_decision_rules as T  # noqa: E402

PILOT = ROOT / "docs" / "experiments" / "active" / "modulator_clues" / "algorithmic_null_pilot.yaml"
SIX = [{"label": f"{a}_s{s}", "arm": a, "seed": s} for s in (42, 43, 44)
       for a in ("ordinary", "modulated")]


def _pinned():
    return dr.load({"decision_rules": yaml.safe_load(PILOT.read_text())["decision_rules"]})


# ------------------------------------------------------------- the signed fixture table -----
@pytest.mark.parametrize("row", T.A4_ROWS, ids=lambda r: r["case"])
def test_driver_evaluate_reproduces_the_signed_A4_fixtures(row):
    """The driver's evaluate() gives the reading the signed R.2 table expects, per layer and
    study-wide (fixture parameters, as in the table)."""
    r = a4.evaluate({k: row["input"] for k in T.LAYERS}, T.P, T.EVID, T.LAYERS, T.ALL_PASS, True)
    assert r["layers"]["enc.out"]["reading"] == row["expect"]
    assert r["study"]["reading"] == row["expect"]


def test_pearson_rows():
    rng = np.random.default_rng(0)
    A, B = rng.normal(size=(8, 50)), rng.normal(size=(8, 50))
    got = a4.pearson_rows(A, B)
    assert np.allclose(got, [np.corrcoef(A[:, k], B[:, k])[0, 1] for k in range(50)])


def test_movement_entries_follow_the_rules_layout():
    lay = dr.a4_layout(_pinned().parameters)
    ent = a4.movement_entries(lay)
    assert [e[0] for e in ent].count("profile") == 8 and [e[0] for e in ent].count("drift") == 2
    assert ("drift", "final:prev", "final", "active") in ent
    assert ("drift", "stage_end:3:prev", "stage_end:3", "passive") in ent


# ------------------------------------------------------------------------- end to end -------
@pytest.fixture(scope="module")
def a4_run(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("a4")
    pinned = _pinned()
    run_root = tmp / "runs"
    syn.write_a4_capture_dir(tmp / "synthA4", SIX, run_root, n_groups=2600, width=8,
                             rules_sha=pinned.sha256)
    keys = syn.VERDICT + ["logits", "value"]
    man = {"name": "synthA4", "evidence_status": "evidence", "out_root": str(tmp),
           "decision_rules": yaml.safe_load(PILOT.read_text())["decision_rules"],
           "runs": [{"label": r["label"], "path": str(run_root / r["label"]),
                     "checkpoints": list(syn.A4_SELECTORS)} for r in SIX],
           "probes": [{"id": pid, "stores": [f"<store {r['label']} {pid}>" for r in SIX],
                       "n_per_store": 2600, "rows_per_episode": 1, "seed": 0,
                       "store_matmul_precision": ["recorded"] * 6} for pid in ("active", "passive")],
           "layers": [{"key": k, "flatten": "none", "keep": "every_capture"} for k in keys],
           "assert_n_episodes": 1,
           "tool_checks": {"shift_change_rows_max": 0.05, "self_similarity_atol": 1e-12,
                           "buffer_index_rel_tol": 1e-3, "row_lag_min_gap": 0.1},
           "capture_matmul_precision": "highest", "headline_capture": None,
           "bootstrap_n": 1000, "inner_folds": 3, "ridge_alphas": [0.01, 1.0, 100.0],
           "probe_split": {"seed": 1, "bootstrap_seed": 2}, "min_rows_per_column": 20,
           "comparisons": "auto"}
    mp_path = tmp / "a4.yaml"
    mp_path.write_text(yaml.safe_dump(man))
    mp = pytest.MonkeyPatch()
    mp.setattr(dio, "read_survival", lambda man, roles: syn.scanned_runs())
    mp.setattr(dio, "shared_start", lambda man, roles: {"per_seed": {}, "holds": True})
    from scripts.analysis.nmn import run_similarity
    assert run_similarity.main(["--manifest", str(mp_path)]) == 0
    assert a4.main(["--manifest", str(mp_path), "--workers", "3"]) == 0
    mp.undo()
    return tmp / "synthA4", pinned, man


def test_a4_output_is_stamped_and_complete(a4_run):
    out, pinned, _ = a4_run
    doc = json.loads((out / "across_worlds.json").read_text())
    assert doc["decision_rules"]["sha256"] == pinned.sha256 and len(doc["git_sha"]) == 40
    assert doc["evidence_status"] == "evidence"
    assert doc["layout"] == json.loads(json.dumps(dr.a4_layout(pinned.parameters)))
    assert doc["stage_end_worlds"] == {"stage_end:0": "active", "stage_end:1": "passive",
                                       "stage_end:2": "active", "stage_end:3": "passive",
                                       "final": "active"}
    cells = doc["stage_end_cells"]
    assert cells["final"]["source"] == "similarity.json"
    assert all(cells[s]["source"] == "computed here" for s in cells if s != "final")
    assert all(cells[s]["cell"][1] == doc["stage_end_worlds"][s] for s in cells)
    assert all(v for c in cells.values() for v in c["gates"].values())
    words = {"move together", "move independently",
             "no measurable movement across worlds — undetermined", "undetermined at 3 seeds"}
    ev = doc["evaluation"]
    assert set(ev["layers"]) == set(syn.VERDICT)
    assert all(v["reading"] in words for v in ev["layers"].values())
    for key in syn.VERDICT:
        for n, a in doc["layers"][key]["agents"].items():
            assert len(a["profile"]) == 8 and len(a["entries"]) == 10
            assert a["q_lo"] is not None and a["mean_movement_minus_drift"] > 0   # fixture moves
        assert len(doc["layers"][key]["co_movement"]["OO"]) == 3
        assert len(doc["layers"][key]["co_movement"]["MO_diff"]) == 6
    assert (out / "across_worlds.csv").exists()


def test_a4_movement_entry_equals_a_direct_predictivity(a4_run):
    """One movement entry, recomputed with run_similarity.predictivity on the same captures,
    splits and bootstrap: m = 1 - P."""
    out, pinned, man = a4_run
    from scripts.analysis.nmn import representation as rep
    from scripts.analysis.nmn.run_similarity import _Fits, predictivity
    P = pinned.parameters
    caps = dio.Captures(man, pinned)
    g = caps.probes["passive"].row_seed
    splits = dio.make_splits(g, P, 1)
    boots = rep.joint_group_bootstrap(g, splits, 1000, 2)
    pr = predictivity(caps.layer("modulated_s43", "stage_end:1", "passive", "rnn.state"),
                      caps.layer("modulated_s43", "stage_end:2", "passive", "rnn.state"),
                      g, splits, boots, dio.ridge(man, P), _Fits(), "check")
    doc = json.loads((out / "across_worlds.json").read_text())
    ent = [e for e in doc["layers"]["rnn.state"]["agents"]["modulated_s43"]["entries"]
           if e["from"] == "stage_end:1" and e["to"] == "stage_end:2" and e["probe"] == "passive"]
    assert len(ent) == 1 and abs(ent[0]["movement"] - (1 - pr["point"])) < 1e-12
