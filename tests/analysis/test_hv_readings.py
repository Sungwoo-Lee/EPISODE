"""readings.py: S1 estimators, joins, sextile assertion, stamp gate, output-root guard (synthetic)."""
import json
import os
import sys

import numpy as np
import pytest
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scripts", "analysis", "studies", "hypervigilance"))
import readings as RD  # noqa: E402


def _episodes(n=40000, seed=0, slopes=(1.0, 5.0), z_effect=None):
    rng = np.random.default_rng(seed)
    inj0 = rng.uniform(0, 100, n)
    x = rng.normal(0, 1, n)
    z = 0.6 * x + rng.normal(0, 0.8, n)
    q = np.digitize(inj0, RD.INJ_Q_EDGES)
    slope = np.where(q == 3, slopes[1], np.where(q == 0, slopes[0], 3.0))
    y = 20 + slope * x + (z_effect * z if z_effect else 0) + rng.normal(0, 8, n)
    w = rng.integers(10, 26, n).astype(float)
    return y, x, w, inj0, z


def test_s1_quarter_contrast_recovers_a_planted_slope_difference():
    y, x, w, inj0, _ = _episodes()
    r = RD.s1_quarter_contrast(y, x, w, inj0)
    assert r["contrast"]["value"] == pytest.approx(4.0, abs=0.3)
    assert r["q0"]["slope_pp_per_nat"]["value"] == pytest.approx(1.0, abs=0.3)


def test_s1_matched_variant_recovers_channel1_slope_with_channel2_covariate():
    y, x, w, inj0, z = _episodes(z_effect=10.0)
    with_z = RD.s1_quarter_contrast(y, x, w, inj0, z)
    assert with_z["q3"]["slope_pp_per_nat"]["value"] == pytest.approx(5.0, abs=0.3)
    assert with_z["contrast"]["value"] == pytest.approx(4.0, abs=0.3)
    without = RD.s1_quarter_contrast(y, x, w, inj0)          # z correlated with x -> biased
    assert abs(without["q3"]["slope_pp_per_nat"]["value"] - 5.0) > 2


def test_s1_glm_product_term_has_the_planted_sign():
    rng = np.random.default_rng(1)
    n = 20000
    llr = rng.normal(0, 1, n)
    inj = rng.uniform(0, 100, n)
    L = np.full(n, 25.0)
    p = 1 / (1 + np.exp(-(-1.5 + 0.1 * llr + 0.02 * llr * inj / 1)))
    Y = rng.binomial(25, p).astype(float)
    D = {"inj0": inj, "nut0": rng.uniform(0, 100, n), "n_bush": rng.integers(4, 11, n) * 1.0,
         "n_rock": rng.integers(6, 13, n) * 1.0, "n_food": rng.integers(1, 5, n) * 1.0,
         "n_ambush": rng.integers(2, 13, n) * 1.0, "d_bush0": rng.integers(0, 6, n) * 1.0}
    g = RD.s1_glm(Y, L, llr, D, np.ones(n, bool))
    assert g["product_pp_per_nat_per_100_injury"]["value"] > 0


def test_seed_join_refuses_misaligned_episode_files():
    with pytest.raises(SystemExit, match="different episode seeds"):
        RD.join_episodes({"seed": np.arange(5)}, {"seed": np.arange(1, 6)})


@pytest.mark.parametrize("p, r, sd, flag", [
    ([0, .7, .5, 0, 0], [0, .5, .7, 0, 0], [0, .3, .3, 0, 0], False),
    ([0, .7, 0, 0, 0], [0, .5, 0, 0, 0], [0, .3, 0, 0, 0], True),
    ([0, .67, .67, 0, 0], [0, .53, .53, 0, 0], [0, .3, .3, 0, 0], True)])
def test_statistic_equals_intensity_flag(p, r, sd, flag):
    spec = RD.ENV.scent_spec({"environment": {"entities": [
        {"class": "predator", "properties": p, "properties_std": sd},
        {"class": "neutral", "properties": r, "properties_std": sd}]}})
    assert spec.statistic_equals_intensity is flag
    assert spec.as_dict()["statistic_equals_intensity"] is flag


def _reading(label, cuts, world="hv1ch"):
    return {"label": label, "world": world, "level": None, "wave": None,
            "S2": {"extremes": {"rabbit": {"sextile_cuts": cuts}, "predator": {"sextile_cuts": [0] * 5}}}}


def test_sextile_cross_run_assertion():
    RD.assert_sextiles([_reading("a", [1, 2, 3, 4, 5]), _reading("b", [1, 2, 3, 4, 5]),
                        _reading("c", [9, 9, 9, 9, 9], world="hv1chm")])
    with pytest.raises(SystemExit, match="sextile cut points differ"):
        RD.assert_sextiles([_reading("a", [1, 2, 3, 4, 5]), _reading("b", [1, 2, 3, 4, 5.0001])])


def test_world_layout_mismatch_is_refused(tmp_path):
    run = tmp_path / "20261001-000000_rppo_hv1ch_t1none_s42"
    (run / "models").mkdir(parents=True)
    cfg = {"seed": 42, "environment": {"entities": [
        {"class": "predator", "count_high": 1, "properties": [0, .7, .5], "properties_std": [0, .3, .3]},
        {"class": "neutral", "count_high": 1, "properties": [0, .5, .7], "properties_std": [0, .3, .3]}],
        "obstacles": [], "resources": []}}
    yaml.safe_dump(cfg, open(run / "models" / "config.yaml", "w"))
    c = {"label": "x", "run": str(run), "stores": [str(tmp_path)], "world": "hv1ch", "seed": 42}
    with pytest.raises(SystemExit, match="expects layout single"):
        RD.check_cell(c)
    cfg["seed"] = 43
    yaml.safe_dump(cfg, open(run / "models" / "config.yaml", "w"))
    with pytest.raises(SystemExit, match="seed"):
        RD.check_cell(c)


def test_golden_stamp_gate_refuses_a_changed_source(tmp_path):
    with pytest.raises(SystemExit, match="golden stamp missing"):
        RD.require_stamps(str(tmp_path))
    sw = {"sources": RD.source_hashes(RD.SWEEP_SOURCES), "combined": "x"}
    json.dump(sw, open(tmp_path / "_golden_sweep_pass.json", "w"))
    asm = {"sources": RD.source_hashes(RD.ASSEMBLY_SOURCES), "combined": "y",
           "sweep_stamp_sha256": RD.sha256(str(tmp_path / "_golden_sweep_pass.json"))}
    json.dump(asm, open(tmp_path / "_golden_assembly_pass.json", "w"))
    RD.require_stamps(str(tmp_path))                                       # all current: passes
    sw["sources"]["scripts/analysis/core/env.py"] = "0" * 64                # a sweep source "changed"
    json.dump(sw, open(tmp_path / "_golden_sweep_pass.json", "w"))
    with pytest.raises(SystemExit, match="changed since the golden check"):
        RD.require_stamps(str(tmp_path))


def test_output_root_guard():
    with pytest.raises(SystemExit, match="absolute"):
        RD.guard_out_root("results/analysis/ladder")
    with pytest.raises(SystemExit):
        RD.guard_out_root(RD.LIVE_LADDER_ROOT)
    with pytest.raises(SystemExit, match="not under"):
        RD.guard_out_root("/tmp/elsewhere")
    ok = RD.guard_out_root(os.path.join(RD.HV_ROOT, "hvsmell"))
    assert ok.endswith("hypervigilance/hvsmell")
    env = RD.child_env(os.path.join(ok, "cell", "ladderstyle"), ok)
    assert env["LADDER_OUT_ROOT"].startswith(ok + os.sep)
    with pytest.raises(SystemExit):
        RD.child_env("relative/ladderstyle", ok)
    with pytest.raises(SystemExit):
        RD.child_env(RD.LIVE_LADDER_ROOT, ok)


def test_hv_world_needs_the_frozen_yardstick(tmp_path, monkeypatch):
    monkeypatch.setattr(RD, "YARDSTICK", str(tmp_path / "yardstick.json"))
    RD.require_yardstick_for([{"world": "cmp10m"}])
    with pytest.raises(SystemExit, match="yardstick"):
        RD.require_yardstick_for([{"world": "hv1chm"}])
