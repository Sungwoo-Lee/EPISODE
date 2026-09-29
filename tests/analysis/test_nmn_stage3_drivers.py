"""Stage 3 drivers (run_similarity, run_decoding) and the Revision-4 reader items of
run_activations (tooling plan ALGORITHMIC_NULL_ANALYSIS_TOOLING, File Changes §8, R4-1, R4-2).

End to end on a synthetic run_activations output (tests/analysis/nmn_synthetic.py; test
fixture data, never study data), against the REAL pinned rules file:
- interim status: gate G5 from synthetic WandB rows, then decision_rules.evaluate_A1 /
  evaluate_A3 / evaluate_A2; every verdict word carries the rules' interim prefix; every
  output is stamped (rules sha256 + commit, git sha, evidence status) and has a data statement
  with each fit's penalty and grid-edge flag.
- pilot status: numbers only, no decision or gate function is called, the rules' label is
  printed, and the written outputs contain no verdict word (grepped).
- R4-2 capture plan: `:prev` checkpoints only on their drift pair's probe (read from the rules'
  parameters.A4.drift_pairs), descriptive layers only at headline_capture, untrained networks
  verdict layers only; a verdict layer / logits / value marked headline_only raises.
"""
from __future__ import annotations

import copy
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
from scripts.analysis.nmn import run_activations as ra  # noqa: E402
from tests.analysis import nmn_synthetic as syn  # noqa: E402

MC = ROOT / "docs" / "experiments" / "active" / "modulator_clues"
PILOT = MC / "algorithmic_null_pilot.yaml"
EVID = MC / "algorithmic_null_mayrep.yaml"


def _pin():
    return yaml.safe_load(PILOT.read_text())["decision_rules"]


def _pinned():
    return dr.load({"decision_rules": _pin()})


def _manifest(tmp: Path, status: str, runs: list, n_groups: int) -> Path:
    keys = syn.VERDICT + ["logits", "value"]
    man = {"name": "synth", "evidence_status": status, "out_root": str(tmp),
           "decision_rules": _pin(),
           "runs": [{"label": r["label"], "path": f"<run {r['label']}>",
                     "checkpoints": ["stage_end:0"]} for r in runs],
           "probes": [{"id": "p", "stores": [f"<store {r['label']}>" for r in runs],
                       "n_per_store": n_groups, "rows_per_episode": 1, "seed": 0,
                       "store_matmul_precision": ["recorded"] * len(runs)}],
           "layers": [{"key": k, "flatten": "none", "keep": "every_capture"} for k in keys],
           "assert_n_episodes": 1,
           "tool_checks": {"shift_change_rows_max": 0.05, "self_similarity_atol": 1e-12,
                           "buffer_index_rel_tol": 1e-3, "row_lag_min_gap": 0.1},
           "capture_matmul_precision": "highest", "headline_capture": None,
           "bootstrap_n": 1000, "inner_folds": 3, "ridge_alphas": [0.01, 1.0, 100.0],
           "probe_split": {"seed": 1, "bootstrap_seed": 2}, "min_rows_per_column": 20,
           "comparisons": "auto"}
    p = tmp / f"{status}.yaml"
    p.write_text(yaml.safe_dump(man))
    return p


SIX = [{"label": f"{a}_s{s}", "arm": a, "seed": s} for s in (42, 43, 44)
       for a in ("ordinary", "modulated")]


@pytest.fixture(scope="module")
def interim_run(tmp_path_factory):
    """Both drivers on a synthetic interim probe of six agents (2,600 groups, so gate G6's
    500 held-out groups can be met)."""
    tmp = tmp_path_factory.mktemp("interim")
    pinned = _pinned()
    syn.write_capture_dir(tmp / "synth", SIX, n_groups=2600, width=8, rules_sha=pinned.sha256)
    man = _manifest(tmp, "interim", SIX, 2600)
    mp = pytest.MonkeyPatch()
    mp.setattr(dio, "read_survival", lambda man, roles: syn.scanned_runs())
    mp.setattr(dio, "shared_start", lambda man, roles: {"per_seed": {}, "holds": True})
    from scripts.analysis.nmn import run_decoding, run_similarity
    assert run_similarity.main(["--manifest", str(man)]) == 0
    assert run_decoding.main(["--manifest", str(man)]) == 0
    mp.undo()
    return tmp / "synth", pinned


def test_interim_outputs_are_stamped_and_evaluated(interim_run):
    out, pinned = interim_run
    sim = json.loads((out / "similarity.json").read_text())
    dec = json.loads((out / "decoding.json").read_text())
    prefix = pinned.rules["evidence_status"]["interim"]["verdict_prefix"]
    for doc in (sim, dec):
        assert doc["decision_rules"]["sha256"] == pinned.sha256
        assert doc["decision_rules"]["commit"] == pinned.commit
        assert len(doc["git_sha"]) == 40 and doc["evidence_status"] == "interim"
        ds = doc["data_statement"]
        assert ds["rules"]["sha256"] == pinned.sha256 and ds["git_sha"] == doc["git_sha"]
        assert "fits_at_grid_edge" in ds["ridge"] and ds["ridge"]["fits"] > 0
    # G5 came first and every run entered
    assert sim["gate_G5"]["yardstick_complete"] is True
    assert sorted(sim["gate_G5"]["entered"]["ordinary"]) == ["ordinary_s42", "ordinary_s43",
                                                            "ordinary_s44"]
    assert sim["survival"]["available"] is True
    a1 = sim["evaluation"]["A1"]
    assert set(a1["layers"]) == set(syn.VERDICT)
    for v in a1["layers"].values():
        assert v["verdict"].startswith(prefix + ": ")
    assert sim["evaluation"]["A3"]["study"]["reading"].startswith(prefix + ": ")
    a2 = dec["evaluation"]["A2"]
    assert a2["study"]["verdict"].startswith(prefix + ": ")
    # every predictivity entry carries each fit's penalty and grid-edge flag
    pr = sim["cells"][0]["layers"]["rnn.state"]["predictivity"]
    assert set(sim["cells"][0]["pair_sets"]) == {"OO", "MM", "MO_diff", "MO_same", "UNTRAINED"}
    assert len(sim["cells"][0]["pair_sets"]["MO_diff"]) == 6
    for v in pr.values():
        for f in v["fits_ab"] + v["fits_ba"]:
            assert set(f) == {"alpha", "alpha_at_edge", "n_columns", "n_dropped"}
    q = dec["cell"]["quantities"]["satiation"]["agents"]["ordinary_s42"]["rnn.state"]
    assert set(q["fits"][0]) == {"alpha", "alpha_at_edge", "n_columns", "n_dropped"} and len(q["fits"]) == 5


def _strings(x):
    if isinstance(x, dict):
        for v in x.values():
            yield from _strings(v)
    elif isinstance(x, list):
        for v in x:
            yield from _strings(v)
    elif isinstance(x, str):
        yield x


def test_interim_every_verdict_word_carries_the_prefix(interim_run):
    """Rules evidence_status.interim: every verdict word carries the prefix — including the
    per-statistic words; the evaluator's internal unprefixed word maps are not written."""
    out, pinned = interim_run
    prefix = pinned.rules["evidence_status"]["interim"]["verdict_prefix"]
    for stem in ("similarity", "decoding"):
        ev = json.loads((out / f"{stem}.json").read_text())["evaluation"]
        assert not any(k.endswith("_words") for k in json.dumps(ev).split('"') if k)
        bad = [x for x in _strings(ev) if dio.VERDICT_WORDS.search(x)
               and not x.startswith(prefix + ": ")]
        assert not bad, bad[:5]


def test_guard_prefixed_walks_the_whole_document():
    """The guard covers every string of the written document, not only the evaluation; only the
    stamp keys verdict_prefix / label / verdict_statement are exempt."""
    pinned = _pinned()
    interim = dr.verdict_policy(pinned, "interim")
    with pytest.raises(ValueError, match="without the rules' prefix"):
        dio.guard_prefixed({"evaluation": {"A1": {"x": {"word": "different"}}}}, interim, "t")
    with pytest.raises(ValueError, match="without the rules' prefix"):
        dio.guard_prefixed({"cells": [{"note": "the two agents are the same"}]}, interim, "t")
    dio.guard_prefixed({"verdict_statement": "verdict words come only from ...",
                        "label": "undetermined label text", "verdict_prefix": interim.prefix,
                        "data_statement": {"label": "same"}}, interim, "t")
    fixed = dio.finalize_evaluation({"layer_words": {"a": "same"}, "x": {"word": "same"}}, interim)
    assert fixed == {"x": {"word": interim.prefix + ": same"}}
    dio.guard_prefixed(fixed, interim, "t")


def test_interim_statistics_behave(interim_run):
    """Controls on the synthetic probe: satiation (an observed channel) decodes from the raw
    input; shuffled targets do not; clock-free quantities have clock R^2 near 0; CKA of a
    modulated layer (per-unit gain) is below its predictivity with the same pair."""
    out, _ = interim_run
    dec = json.loads((out / "decoding.json").read_text())
    g4 = dec["cell"]["g4_controls"]
    assert g4["input_satiation_r2"] > 0.99
    assert all(v < 0.02 for v in g4["shuffled_r2"].values())
    assert abs(dec["cell"]["quantities"]["injury_level"]["clock_r2"]) < 0.02
    sim = json.loads((out / "similarity.json").read_text())
    lay = sim["cells"][0]["layers"]["actor.out"]
    k = "ordinary_s42|modulated_s43"
    assert lay["cka"][k]["point"] < lay["predictivity"][k]["point"]
    assert lay["cka"][k]["q_lo"] <= lay["cka"][k]["point"] <= lay["cka"][k]["q_hi"]


@pytest.fixture(scope="module")
def pilot_run(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("pilot")
    pinned = _pinned()
    two = SIX[:2]
    syn.write_capture_dir(tmp / "synth", two, n_groups=300, width=8, rules_sha=pinned.sha256,
                          selector="final", headline_extra={"rnn.raw": 8, "enc.uni.out": 8})
    man = yaml.safe_load(_manifest(tmp, "pilot", two, 300).read_text())
    for r in man["runs"]:
        r["checkpoints"] = ["final"]
    man["headline_capture"] = {"checkpoint": "final", "probe": "p"}
    man["layers"] += [{"key": "rnn.raw", "flatten": "none", "keep": "headline_only"},
                      {"key": "enc.uni.out", "flatten": "senses_x_units", "keep": "headline_only"}]
    (tmp / "pilot.yaml").write_text(yaml.safe_dump(man))

    def forbidden(*a, **k):
        raise AssertionError("a decision / gate function was called for the pilot")
    mp = pytest.MonkeyPatch()
    for name in ("evaluate_A1", "evaluate_A2", "evaluate_A3", "evaluate_A4", "gate_G1",
                 "gate_G2", "gate_G3", "gate_G4", "gate_G5", "gate_G6", "summarise_pairs"):
        mp.setattr(dr, name, forbidden)
    mp.setattr(dio, "survival_block", forbidden)
    mp.setattr(dio, "read_survival", forbidden)
    from scripts.analysis.nmn import run_decoding, run_similarity
    assert run_similarity.main(["--manifest", str(tmp / "pilot.yaml")]) == 0
    assert run_decoding.main(["--manifest", str(tmp / "pilot.yaml")]) == 0
    mp.undo()
    return tmp / "synth", pinned


def test_pilot_is_numbers_only_with_the_label(pilot_run):
    out, pinned = pilot_run
    label = pinned.rules["evidence_status"]["pilot"]["label"]
    for stem in ("similarity", "decoding"):
        doc = json.loads((out / f"{stem}.json").read_text())
        assert doc["evaluation"] is None
        assert doc["label"] == label and doc["data_statement"]["label"] == label
        assert doc["verdict_statement"] == dio.NO_VERDICT
        for ext in ("json", "csv"):
            text = (out / f"{stem}.{ext}").read_text()
            assert not dio.VERDICT_WORDS.search(text), dio.VERDICT_WORDS.findall(text)
    desc = json.loads((out / "similarity_descriptive.json").read_text())
    assert set(desc["descriptive"]) == {"ordinary_s42|modulated_s42 rnn.raw~rnn.raw",
                                        "ordinary_s42|modulated_s42 enc.uni.out~enc.uni.out"}
    assert desc["decision_rules"]["sha256"] == pinned.sha256 and desc["label"] == label
    for ext in ("json", "csv"):
        text = (out / f"similarity_descriptive.{ext}").read_text()
        assert not dio.VERDICT_WORDS.search(text), dio.VERDICT_WORDS.findall(text)
    sim = json.loads((out / "similarity.json").read_text())
    assert list(sim["cells"][0]["pair_sets"]["MO_same"]) == ["ordinary_s42|modulated_s42"]
    ref = sim["cells"][0]["layers"]["rnn.state"]["reference"]
    assert "untrained_ordinary_s42|ordinary_s42" in ref and "input|ordinary_s42" in ref


def test_guard_refuses_a_verdict_word_under_the_pilot_policy():
    pinned = _pinned()
    pilot = dr.verdict_policy(pinned, "pilot")
    for text in ('{"a1": "same"}', "reads different", "Undetermined at 3 seeds",
                 "match — absent in both"):
        with pytest.raises(ValueError, match="allows no verdict word"):
            dio.guard_no_verdict_words(text, pilot, "x")
    dio.guard_no_verdict_words('{"MO_same": 1, "same_max_below_divisor": 3}', pilot, "x")
    dio.guard_no_verdict_words("same", dr.verdict_policy(pinned, "interim"), "x")


def test_pair_sets():
    agents = {r["label"]: {**r, "untrained": False} for r in SIX}
    agents.update({f"untrained_{r['label']}": {**r, "untrained": True} for r in SIX
                   if r["arm"] == "ordinary"})
    s = dio.pair_sets(agents, "auto")
    assert {k: len(v) for k, v in s.items()} == {"OO": 3, "MM": 3, "MO_diff": 6, "MO_same": 3,
                                                 "UNTRAINED": 3}
    assert all(p.startswith("ordinary") for p in s["MO_diff"])
    only = dio.pair_sets(agents, [["ordinary_s42", "modulated_s42"]])
    assert {k: len(v) for k, v in only.items()}["MO_same"] == 1 and not only["OO"]


def test_primary_cell_reads_the_rules():
    pinned = _pinned()
    ev = [("stage_end:0", "active"), ("final", "active"), ("final", "passive")]
    assert dio.primary_cell(pinned, "evidence", ev) == ("final", "active")
    assert dio.primary_cell(pinned, "interim", [("stage_end:0", "a")]) == ("stage_end:0", "a")
    with pytest.raises(ValueError, match="names no primary cell"):
        dio.primary_cell(pinned, "pilot", ev)


def test_survival_block_reads_the_registered_stages():
    P = _pinned().parameters
    runs = syn.scanned_runs()
    ev = dio.survival_block(runs, P, "evidence")
    it = dio.survival_block(runs, P, "interim")
    assert ev["stage_index"] == {"G5": 0, "A3": 4} and it["stage_index"] == {"G5": 0, "A3": 0}
    assert ev["gate_G5"]["yardstick_complete"]
    r = ev["per_run"]["ordinary_s42"]
    # stage 5 levels sit ~40 steps above stage 1 in the fixture
    assert 35 < r["S_a3"] - r["S_g5"] < 45
    assert it["per_run"]["ordinary_s42"]["S_a3"] == r["S_g5"]
    assert ev["survival"]["available"] and "same" in ev["survival"]


def test_bootstrap_n_below_the_rules_floor_raises(tmp_path):
    man = yaml.safe_load(_manifest(tmp_path, "pilot", SIX[:2], 10).read_text())
    man["bootstrap_n"] = 999
    with pytest.raises(ValueError, match="below the rules' G6 minimum"):
        dio.open_rules(man)


# ------------------------------------------------------------------- R4-2 capture plan -----
def _evidence_like():
    man = yaml.safe_load(EVID.read_text())
    man["out_root"] = "x"
    for p in man["probes"]:
        p.update({"stores": ["s"], "rows_per_episode": 5, "seed": 0,
                  "store_matmul_precision": ["recorded"]})
    pilot = yaml.safe_load(PILOT.read_text())
    for k in ("layers", "assert_n_episodes", "tool_checks", "capture_matmul_precision"):
        man[k] = copy.deepcopy(pilot[k])
    man["headline_capture"] = {"checkpoint": "final", "probe": "active"}
    return man


def test_capture_plan_prev_only_on_its_drift_probe_and_headline_layers_once():
    pinned = _pinned()
    man = _evidence_like()
    ra.check_keep(man, pinned.rules["common"]["verdict_layers"])
    ordinary = [r["label"] for r in man["runs"] if "ordinary" in r["label"]]
    plan = ra.capture_plan(man, dr.param(pinned.parameters, "A4.drift_pairs"), ordinary)
    probes_of = {}
    for c in plan:
        probes_of.setdefault((c["label"], c["selector"]), []).append(c["probe"])
    for r in man["runs"]:
        assert probes_of[(r["label"], "final:prev")] == ["active"]
        assert probes_of[(r["label"], "stage_end:3:prev")] == ["passive"]
        assert probes_of[(r["label"], "final")] == ["active", "passive"]
    every = {l["key"] for l in man["layers"] if l["keep"] == "every_capture"}
    heads = [c for c in plan if c["headline"]]
    assert len(heads) == 6 and all(c["selector"] == "final" and c["probe"] == "active"
                                   for c in heads)
    for c in plan:
        assert set(c["layers"]) == (set(l["key"] for l in man["layers"]) if c["headline"]
                                    else every)
    unt = [c for c in plan if c["kind"] == "untrained"]
    assert len(unt) == 3 * 2 and all(set(c["layers"]) == every for c in unt)
    assert len(plan) == 6 * (5 * 2 + 2) + 6          # the plan's 78 captures


@pytest.mark.parametrize("key", ["rnn.state", "logits", "value"])
def test_a_verdict_layer_marked_headline_only_raises(key):
    man = _evidence_like()
    for l in man["layers"]:
        if l["key"] == key:
            l["keep"] = "headline_only"
    with pytest.raises(ValueError, match="every_capture"):
        ra.check_keep(man, _pinned().rules["common"]["verdict_layers"])


def test_prev_selector_without_a_drift_pair_raises():
    man = _evidence_like()
    man["runs"][0]["checkpoints"].append("stage_end:1:prev")
    with pytest.raises(ValueError, match="drift_pairs"):
        ra.capture_plan(man, dr.param(_pinned().parameters, "A4.drift_pairs"), [])


def test_headline_only_layers_need_a_headline_capture(tmp_path):
    man = yaml.safe_load(PILOT.read_text())
    man["headline_capture"] = None
    p = tmp_path / "m.yaml"
    p.write_text(yaml.safe_dump(man))
    with pytest.raises(ValueError, match="headline_capture is null"):
        ra.load_manifest(p)


def test_pilot_manifest_loads_for_stage3():
    man = dio.load_manifest(PILOT)
    assert man["headline_capture"] == {"checkpoint": "final", "probe": "w0000_pair_final"}
    ra.check_keep(man, _pinned().rules["common"]["verdict_layers"])


# ------------------------------------------------------------ R4-4 sampled-vs-full check -----
def test_buffer_index_deviation_is_per_row():
    """Each row is normalised by its own reference maximum: a row with large values does not
    dilute a small row's error, and a one-slot shift of a changing signal is caught."""
    from scripts.analysis.nmn import teacher_forced as tf
    ref = np.array([[0.1, 0.2], [100.0, 50.0]])
    got = ref + np.array([[0.05, 0.0], [0.0, 0.0]])
    d = tf.buffer_index_deviation(ref, got)
    assert np.allclose(d, [0.05, 0.0])            # row 0: 0.05 / max(1, 0.2)
    t = np.arange(50, dtype=float)
    sig = np.stack([np.sin(t / 3), np.cos(t / 5)], axis=1)
    assert tf.buffer_index_deviation(sig[1:], sig[:-1]).max() > 0.1


def test_quarters_of_a_length():
    from scripts.analysis.nmn import teacher_forced as tf
    assert tf.quarters([1, 2, 3, 4, 5], [0, 3, 5, 9, 10], 12) == [1.0, 3.0, None, 5.0]
    assert tf.quarters([1.0], [0], [8]) == [1.0, None, None, None]


def test_buffer_index_tolerance_is_mandatory(tmp_path):
    man = yaml.safe_load(PILOT.read_text())
    del man["tool_checks"]["buffer_index_rel_tol"]
    p = tmp_path / "m.yaml"
    p.write_text(yaml.safe_dump(man))
    with pytest.raises(ValueError, match="buffer_index_rel_tol"):
        ra.load_manifest(p)



# ------------------------------------------------------------- cross-agent row-lag control -----
def test_row_lag_control_passes_aligned_and_fails_shifted_rows():
    rng = np.random.default_rng(0)
    common = rng.normal(size=(2000, 6))
    la = common + 0.3 * rng.normal(size=common.shape)
    lb = common + 0.3 * rng.normal(size=common.shape)
    ok = dio.row_lag_control(la, lb, 0.1, "a|b")
    assert ok["lag0"] > 0.6 and ok["gap"] > 0.3
    with pytest.raises(RuntimeError, match="row-lag control failed"):
        dio.row_lag_control(la, np.roll(lb, 1, axis=0), 0.1, "a|b")


def test_row_lag_control_ran_on_every_trained_pair(interim_run):
    out, _ = interim_run
    c = json.loads((out / "similarity.json").read_text())["cells"][0]
    trained = [p for s, v in c["pair_sets"].items() if s != "UNTRAINED" for p in v]
    assert sorted(c["row_lag_control"]) == sorted(trained) and len(trained) == 15
    assert all(v["gap"] >= v["min_gap"] for v in c["row_lag_control"].values())


def test_a_refused_readout_raises_before_evaluation():
    from scripts.analysis.nmn import run_decoding as rd
    cell = {"agents": {"o": {"untrained": False, "arm": "ordinary"}},
            "quantities": {q: {"agents": {"o": {k: {"refused": "too few rows"} for k in syn.VERDICT}},
                               "held_out_groups_per_repeat": [600] * 5}
                           for q in ["satiation"]}}
    with pytest.raises(ValueError, match="refused, cannot evaluate"):
        rd.evaluate(cell, _pinned().parameters, dr.verdict_policy(_pinned(), "interim"),
                    syn.VERDICT, ["satiation"], {}, {"yardstick_complete": True}, 2000)



# ---------------------------------------- rules revision P1: admission, supporting read ------
def test_admission_is_recorded_and_the_supporting_read_is_reported(interim_run):
    out, pinned = interim_run
    sim = json.loads((out / "similarity.json").read_text())
    frac = pinned.parameters["common"]["predictor_columns"]["min_active_fraction"]
    assert sim["data_statement"]["predictor_columns"]["min_active_fraction"] == frac
    per_fit = sim["cells"][0]["ridge_fits"]["predictor_columns"]["per_fit"]
    assert per_fit and all({"fit", "n_columns", "n_dropped"} <= set(r) for r in per_fit)
    pr = sim["cells"][0]["layers"]["rnn.state"]["predictivity"]
    for name, v in pr.items():
        sup = v.get("supporting_read_modulated_to_ordinary")
        if v["pair_set"] in ("MO_same", "MO_diff"):
            assert sup["r2"] == v["r2_ba"] and name.startswith("ordinary")
            assert sup["q_lo"] <= sup["r2"] <= sup["q_hi"]
        else:
            assert sup is None
    dec = json.loads((out / "decoding.json").read_text())
    assert dec["data_statement"]["predictor_columns"]["min_active_fraction"] == frac


def test_an_output_under_other_rules_is_never_overwritten(tmp_path):
    pinned = _pinned()
    pol = dr.verdict_policy(pinned, "pilot")
    (tmp_path / "similarity.json").write_text(json.dumps({"decision_rules": {"sha256": "old"}}))
    with pytest.raises(ValueError, match="never overwritten"):
        dio.write_outputs(tmp_path, "similarity", {"decision_rules": {"sha256": "new"}}, [], pol)
    dio.write_outputs(tmp_path, "similarity", {"decision_rules": {"sha256": "old"}}, [], pol)


def test_captures_under_other_rules_reused_only_if_their_rule_numbers_agree(tmp_path):
    pinned = _pinned()
    syn.write_capture_dir(tmp_path / "synth", SIX[:2], n_groups=50, width=4, rules_sha="other")
    man = yaml.safe_load(_manifest(tmp_path, "pilot", SIX[:2], 50).read_text())
    meta = json.loads((tmp_path / "synth" / "manifest.json").read_text())
    meta["gates_read"] = dio.capture_rule_numbers(pinned.parameters)
    (tmp_path / "synth" / "manifest.json").write_text(json.dumps(meta))
    assert dio.Captures(man, pinned).rules_sha == "other"
    meta["gates_read"]["G2"] = 1.0
    (tmp_path / "synth" / "manifest.json").write_text(json.dumps(meta))
    with pytest.raises(ValueError, match="re-run run_activations"):
        dio.Captures(man, pinned)


# --------------------------------------------------------- robustness columns (descriptive) -----
def test_robustness_columns_reproduce_the_registered_value_and_are_labelled(interim_run):
    out, pinned = interim_run
    from scripts.analysis.nmn import run_similarity_robustness as rob
    man = out.parent / "interim.yaml"
    mp = pytest.MonkeyPatch()
    mp.setattr(dio, "read_survival", lambda man, roles: syn.scanned_runs())
    assert rob.main(["--manifest", str(man), "--workers", "2"]) == 0
    mp.undo()
    doc = json.loads((out / "similarity_robustness.json").read_text())
    assert doc["status_of_these_numbers"] == "descriptive — not a registered statistic"
    assert doc["decision_rules"]["sha256"] == pinned.sha256 and "evaluation" not in doc
    sim = json.loads((out / "similarity.json").read_text())
    for layer in syn.VERDICT:
        reg = sim["cells"][0]["layers"][layer]["predictivity"]
        rows = doc["layers"][layer]["pairs"]
        assert set(rows) == {p for p, v in reg.items() if v["pair_set"] != "UNTRAINED"}
        for pname, rec in rows.items():
            for v in ("admitted", "all_columns"):   # no rare column in the fixture: both equal
                assert abs(rec["variants"][v]["weighted_mutual"]["point"] - reg[pname]["point"]) < 1e-10
            if rec["pair_set"] in ("MO_diff", "MO_same"):
                sup = reg[pname]["supporting_read_modulated_to_ordinary"]["r2"]
                assert abs(rec["variants"]["admitted"]["weighted_b_to_a"]["point"] - sup) < 1e-10
        summ = doc["layers"][layer]["summary"]["admitted/weighted"]
        assert len(summ["MM_mutual_points"]) == 3 and len(summ["MO_diff_mutual_points"]) == 6
    text = (out / "similarity_robustness.csv").read_text()
    assert "descriptive — not a registered statistic" in text
