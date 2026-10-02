"""verdict.py: the study's two-stage rule, S4 bound, absolute sign, C-sign, anchors, power table."""
import os
import shutil
import sys

import numpy as np
import pytest
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scripts", "analysis", "studies", "hypervigilance"))
import verdict as V  # noqa: E402

S3, S5 = V.SEEDS_STAGE1, V.SEEDS_STAGE2
d = lambda seeds, vals: dict(zip(seeds, vals))


def test_stage1_established_topup_and_overlap():
    assert V.decide(d(S3, [5, 6, 7]), d(S3, [0, 1, 2]), +1, 3.0)["status"] == "established"
    assert V.decide(d(S3, [3, 3.5, 4]), d(S3, [1, 2, 2.5]), +1, 3.0)["status"] == "top-up"   # |Δ| < min
    assert V.decide(d(S3, [5, 6, 1.5]), d(S3, [0, 1, 2]), +1, 3.0)["status"] == "top-up"     # overlap


def test_stage2_u_matches_scipy():
    rng = np.random.default_rng(3)
    for _ in range(50):
        t, r = rng.normal(0, 1, 5).round(1), rng.normal(0, 1, 5).round(1)
        assert V.u_not_beyond(t, r, +1) == stats.mannwhitneyu(r, t).statistic
        assert V.u_not_beyond(t, r, -1) == stats.mannwhitneyu(t, r).statistic


def test_stage2_established_refuted_opposite():
    ref = d(S5, [0, 1, 2, 0.5, 1.5])
    est = V.decide(d(S5, [4, 5, 1.8, 6, 7]), ref, +1, 3.0)        # stage 1 overlap -> stage 2
    assert est["stage"] == 2 and est["status"] == "established" and est["U_predicted"] <= 4
    near0 = V.decide(d(S5, [0.2, 1.1, 1.9, 0.6, 1.4]), ref, +1, 3.0)
    assert near0["status"] == "refuted" and near0["bound_predicted_side"] < 3
    opp = V.decide(d(S5, [-5, -4, -6, -3, -7]), ref, +1, 3.0)
    assert opp["status"] == "refuted" and opp["U_opposite"] <= 4


def test_predicted_negative_outcome_uses_the_lower_side():
    ref = d(S5, [0, 0.2, -0.1, 0.1, 0])
    r = V.decide(d(S5, [-3, -2.5, -0.05, -3.5, -2]), ref, -1, 1.0)
    assert r["stage"] == 2 and r["status"] == "established"
    r2 = V.decide(d(S5, [0.3, 0.1, 0.2, 0.0, 0.25]), ref, -1, 1.0)
    assert r2["status"] == "refuted" and r2["bound_predicted_side"] > -1.0     # lower bound above -min


def test_contrast_c_is_descriptive_only():
    c = V.describe_c(d(S5, [9, 9.5, 10, 11, 12]), d(S5, [0, 1, 2, 3, 4]))
    assert c["status"] == "descriptive" and c["clearly_non_zero"] is True
    assert "established" not in str(c)


def test_other_seed_counts_are_not_evaluable():
    r = V.decide(d((42, 43, 44, 45), [1, 2, 3, 4]), d((42, 43, 44, 45), [0, 0, 0, 0]), +1, 3)
    assert r["status"] == "not evaluable under §5.3"
    assert V.decide(d(S3, [1, np.nan, 3]), d(S3, [0, 0, 0]), +1, 3)["status"].startswith("not evaluable")


def test_s4_bound_hand_computed():
    ref = d(S3, [0, 0, 0])
    lb = V.one_sided_bound([-1, -2, -3], [0, 0, 0], "lower")
    assert lb == pytest.approx(-2 - 2.919986 * (1 / np.sqrt(3)), abs=1e-4)
    assert round(lb, 3) == -3.686
    p1_stage1 = {"status": "established", "stage": 1}
    assert V.s4_condition(p1_stage1, d(S3, [-1, -2, -3]), ref)["status"] == "S4 may have fallen"
    ok = V.s4_condition(p1_stage1, d(S3, [0, -1, -2]), ref)
    assert ok["status"] == "S4 did not fall" and round(ok["lower_bound"], 3) == -2.686
    p1_stage2 = {"status": "not established", "stage": 2}
    s4t = d(S5, [0, -1, -2, -8, -9])            # seeds 45/46 drag it down: stage-2 set must be used
    assert V.s4_condition(p1_stage2, s4t, d(S5, [0] * 5))["status"] == "S4 may have fallen"
    assert V.s4_condition({"status": "top-up", "stage": 1}, s4t, d(S5, [0] * 5))["status"] == "pending"


def test_absolute_sign_bound_hand_computed():
    a = V.absolute_p2([1, 2, 3], True)
    assert round(a["lower_bound"], 3) == 0.314 and a["above_zero"] and not a["weakens_boldness"]
    b = V.absolute_p2([-1, 0, 1], True)
    assert round(b["lower_bound"], 3) == -1.686 and b["weakens_boldness"]


def test_c_sign_readings():
    assert V.c_sign("not established", "established", 1.0)["readings"][0].startswith("i:")
    assert V.c_sign("refuted", "established", -4.0)["readings"][0].startswith("ii:")
    assert V.c_sign("established", "not established", 4.0)["readings"][0].startswith("iii:")
    assert any(r.startswith("iv:") for r in V.c_sign("established", "established", 5.0)["readings"])
    assert V.c_sign("not established", "not established", 0.0)["note"] == \
        "no registered cross-contrast reading"


def test_verdict_map_rows():
    assert V.verdict_row("established", "established", "S4 did not fall")["row"] == 1
    assert V.verdict_row("established", "refuted", "S4 did not fall")["row"] == 2
    assert V.verdict_row("established", "not established", "S4 may have fallen")["row"] == 3
    assert V.verdict_row("refuted", "established", "S4 did not fall")["row"] == 4
    assert V.verdict_row("not established", "any", "S4 may have fallen")["row"] == 5
    assert V.verdict_row("not established", "any", "S4 did not fall")["row"] == 6
    assert V.verdict_row("top-up", "established", "pending")["row"] is None


def test_anchors_pass_on_the_study_and_fail_on_a_changed_threshold(tmp_path):
    V.check_anchors()
    txt = open(V.STUDY_DOC).read()
    bad = tmp_path / "bad.md"
    bad.write_text(txt.replace("| P1 rabbit proximity effect | + | **3 pp** |",
                               "| P1 rabbit proximity effect | + | **2 pp** |"))
    with pytest.raises(SystemExit, match="P1 minimum"):
        V.check_anchors(str(bad))


def test_anchor_quoted_only_in_a_feedback_section_does_not_count(tmp_path):
    txt = open(V.STUDY_DOC).read()
    sentence = "The two-stage rule below applies to contrasts A and B only."
    assert sentence in txt
    moved = txt.replace(sentence, "The rule applies to every contrast.")
    moved += "\n\n## Feedback from someone\n\n" + sentence + "\n"
    p = tmp_path / "moved.md"
    p.write_text(moved)
    with pytest.raises(SystemExit, match="two-stage rule scope"):
        V.check_anchors(str(p))


@pytest.mark.parametrize("effect, sd, mn, key, want", [
    (3, 1.4, 3, "established_overall", 0.59), (3, 1.4, 3, "refuted", 0.05),
    (0, 1.4, 3, "refuted", 0.92), (2, 1.5, 2, "established_overall", 0.51),
    (0, 2.67, 2, "established_overall", 0.07), (0, 2.67, 2, "refuted", 0.27)])
def test_power_reproduces_the_registered_table(effect, sd, mn, key, want):
    assert V.power(effect, sd, 40000, rng_seed=7, minimum=mn)[key] == pytest.approx(want, abs=0.03)


def test_power_false_positive_below_one_percent():
    assert V.power(0, 1.4, 40000, rng_seed=7, minimum=3)["established_overall"] < 0.01
