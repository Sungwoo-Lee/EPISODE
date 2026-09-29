"""Tests for scripts/analysis/nmn/decision_rules.py — THE FIXTURE TABLE SIGNED AT CHECKPOINT R.2.

How to read this file (for a reader who does not program)
---------------------------------------------------------
Each rule of the pre-registered rules file
(docs/experiments/active/modulator_clues/algorithmic_null_decision_rules.yaml) has a TABLE
below: a list of rows, each with
  - "case":   a short name,
  - "why":    what the row checks, in words,
  - "input":  the made-up statistics fed to the evaluator,
  - "expect": the verdict the evaluator must return (or "RAISES" when the rules assign no
              outcome to that input and the evaluator must stop rather than choose).
Every number in the inputs is a TEST FIXTURE, not a study result; no real data exists yet.
The parameter values (FIXTURE_P) are also a test fixture, not the study's rule: they are
copied from the rules' `parameters:` block so that the reading is the one the study will get.

To print every table as plain markdown:
    /home/vncuser/miniconda3/envs/grid_world_pain/bin/python tests/analysis/test_nmn_decision_rules.py

Notation used in the inputs
  band (L, U)        the ordinary-vs-ordinary "seed yardstick": L = lowest 5th percentile,
                     U = highest 95th percentile over the 3 ordinary pairs
  untrained (Lu, Uu) the same band over the 3 pairs of untrained networks
  mo_diff            the modulated-vs-ordinary, different-seed pair values (6 pairs, or 4
                     when only 2 modulated seeds pass gate G5)
  mo_diff mean 90%   5th and 95th percentile of the bootstrap distribution of their mean
  mo_same            the modulated-vs-ordinary, same-seed pair values (3, or 2)

Besides the tables: contract tests (sha pin, what each evidence status may say, dirty rules
file); for decision_rules.py and wakeup.py, the no-numeric-literal test (which also refuses a
number hidden in a string, float("0.05")) and an import allow-list; the parameter coverage test
against the real rules file (every entry is read); and the parameter PERTURBATION test (every
entry, nudged, changes some output, so it is used and not merely read; the few entries whose
consumer is a driver not written yet are listed by name as "read, not yet used").

Plan: docs/develop/active/neuromodulation/ALGORITHMIC_NULL_ANALYSIS_TOOLING.md, File Changes §6,
Checkpoints 3.1 and R.2.
"""
import ast
import hashlib
import os
import sys

import numpy as np
import pytest
import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
from scripts.analysis.nmn import decision_rules as dr  # noqa: E402
from scripts.analysis.nmn import rules_pin  # noqa: E402
from scripts.analysis.nmn import wakeup  # noqa: E402

RULES = "docs/experiments/active/modulator_clues/algorithmic_null_decision_rules.yaml"
LAYERS = ["enc.out", "rnn.state", "rnn.out", "actor.out", "critic.out"]
QUANTITIES = ["satiation", "injury_level", "nearest_predator_manhattan", "steps_remaining"]

# test fixture, not the study's rule (values copied from the rules' parameters block)
FIXTURE_P = {
    "gates": {"G1": {"action_agreement_min": 1.0, "near_tie_logit_margin": 1.0e-4,
                     "near_tie_fraction_max": 0.001},
              "G2": {"reconstruction_rel_tol": 1.0e-5},
              "G3": {"alignment_agreement_min": 1.0, "shift_control_agreement_max": 0.95},
              "G4": {"input_satiation_r2_min": 0.99, "shuffled_r2_max": 0.02},
              "G5": {"stage": 1, "stage1_survival_min_steps": 150, "stage1_food_bites_min": 1.0,
                     "min_ordinary_seeds": 3, "min_modulated_seeds": 2},
              "G6": {"bootstrap_n_min": 1000, "test_fold_groups_min": 500}},
    "common": {"bootstrap_interval": [0.05, 0.95], "split": {"n_repeats": 5, "test_frac": 0.2},
               "survival": {"window_episodes": 200000, "row_weight": "delta_episode_number",
                            "min_window_n": 1000, "se_floor_steps": 3.6, "se_multiplier": 2}},
    "A1": {"same_max_below_divisor": 3},
    "A2": {"beats_clock_margin_r2": 0.05, "arm_min_seeds": 2, "differs_min_layers": 2},
    "A3": {"survival_stage_by_status": {"evidence": 5, "interim": 1}},
    "A4": {"movement_min_seeds": 2,
           "stage_sequence": ["stage_end:0", "stage_end:1", "stage_end:2", "stage_end:3", "final"],
           "probes": ["active", "passive"],
           "drift_pairs": [{"prev": "final:prev", "checkpoint": "final", "probe": "active"},
                           {"prev": "stage_end:3:prev", "checkpoint": "stage_end:3",
                            "probe": "passive"}]},
    "study_reading": {"min_layers": 3},
    "remedy": {"undetermined_layers_trigger": 3, "extra_seeds": [45, 46]},
    "B2": {"threshold_mode_headline": "fraction_of_rise", "f": 0.5, "literal_f": 0.5,
           "plateau_f": 0.9, "final_k": 3, "noise_k": 3, "sustain": 2, "min_noise_points": 5,
           "noise_window_divisor": 3, "noise_window_max_fraction": 0.5,
           "lag_coincident_max_intervals": 1, "sign_test_alpha": 0.05, "sign_test_null_p": 0.5},
}
P = FIXTURE_P
EVID = dr.Policy("evidence", True, None, None)
INTERIM = dr.Policy("interim", True, "provisional — end of stage 1 of 5", None)
PILOT = dr.Policy("pilot", False, None, "tool validation — the two agents share seed 42; not evidence")
B2POL = dr.Policy("b2_wakeup", True, None, "wake-up timing")
ALL_PASS = {"G1": True, "G2": True, "G3": True, "G4": True, "G6": True}


# =============================================================================================
# TABLE 1 — Gates G1 to G6 ("a failed gate blocks every verdict word")
# =============================================================================================
def _g1(rows, hard, tie, margin=1.0e-4):
    return {"rows": rows, "disagree_not_near_tie": hard, "disagree_near_tie": tie,
            "near_tie_logit_margin": margin}


GATE_ROWS = [
    # G1 — each agent replays its own stored episodes and must pick the stored action
    {"case": "G1 all rows agree", "gate": "G1", "why": "1,000,000 rows, no disagreement",
     "input": _g1(1_000_000, 0, 0), "expect": True},
    {"case": "G1 one clear disagreement", "gate": "G1",
     "why": "a single disagreement that is not a near-tie fails (100 % required)",
     "input": _g1(1_000_000, 1, 0), "expect": False},
    {"case": "G1 near-ties at the allowance", "gate": "G1",
     "why": "near-tie disagreements on exactly 0.1 % of rows are allowed",
     "input": _g1(1_000_000, 0, 1000), "expect": True},
    {"case": "G1 near-ties over the allowance", "gate": "G1",
     "why": "near-tie disagreements on 0.1001 % of rows fail",
     "input": _g1(1_000_000, 0, 1001), "expect": False},
    {"case": "G1 near-ties classified at another margin", "gate": "G1",
     "why": "the replay used a different near-tie margin than the rules: stop",
     "input": _g1(1_000_000, 0, 0, margin=1e-3), "expect": "RAISES"},
    # G2 — every captured tensor rebuilt from its neighbour
    {"case": "G2 inside tolerance", "gate": "G2",
     "why": "deviation 5e-6 on a tensor of size 0.5: tolerance is 1e-5 x max(1, 0.5)",
     "input": {"rnn.state": {"max_abs_dev": 5e-6, "max_abs_ref": 0.5}}, "expect": True},
    {"case": "G2 relative to a large tensor", "gate": "G2",
     "why": "deviation 2e-5 on a tensor of size 3: tolerance 3e-5, passes",
     "input": {"logits": {"max_abs_dev": 2e-5, "max_abs_ref": 3.0}}, "expect": True},
    {"case": "G2 over tolerance", "gate": "G2",
     "why": "deviation 2e-5 on a tensor of size 0.5: tolerance 1e-5, fails",
     "input": {"rnn.state": {"max_abs_dev": 2e-5, "max_abs_ref": 0.5}}, "expect": False},
    # G3 — row alignment of the stored actions
    {"case": "G3 aligned, control discriminates", "gate": "G3",
     "why": "100 % alignment, shift-by-one control agrees on 51 % (< 95 %)",
     "input": {"alignment": _g1(24_000, 0, 0), "shift_control_agreement": 0.51}, "expect": True},
    {"case": "G3 shift control at 95 %", "gate": "G3",
     "why": "the control must agree on FEWER than 95 % of rows; exactly 95 % fails",
     "input": {"alignment": _g1(24_000, 0, 0), "shift_control_agreement": 0.95}, "expect": False},
    {"case": "G3 near-tie allowance as G1", "gate": "G3",
     "why": "G3 uses G1's near-tie allowance: 24 near-ties of 24,000 rows (0.1 %) pass",
     "input": {"alignment": _g1(24_000, 0, 24), "shift_control_agreement": 0.5}, "expect": True},
    {"case": "G3 one misaligned row", "gate": "G3", "why": "one clear misalignment fails",
     "input": {"alignment": _g1(24_000, 1, 0), "shift_control_agreement": 0.5}, "expect": False},
    # G4 — positive and negative controls
    {"case": "G4 controls pass", "gate": "G4",
     "why": "input satiation R^2 0.995 >= 0.99; shuffled R^2 all <= 0.02; folds disjoint",
     "input": {"input_satiation_r2": 0.995, "shuffled_r2": {q: 0.01 for q in QUANTITIES},
               "groups_disjoint": True}, "expect": True},
    {"case": "G4 positive control fails", "gate": "G4", "why": "input satiation R^2 0.98",
     "input": {"input_satiation_r2": 0.98, "shuffled_r2": {q: 0.01 for q in QUANTITIES},
               "groups_disjoint": True}, "expect": False},
    {"case": "G4 one shuffled control too high", "gate": "G4",
     "why": "shuffled-target R^2 of 0.03 for one quantity",
     "input": {"input_satiation_r2": 0.995,
               "shuffled_r2": {**{q: 0.01 for q in QUANTITIES}, "injury_level": 0.03},
               "groups_disjoint": True}, "expect": False},
    {"case": "G4 group in both folds", "gate": "G4", "why": "an episode group leaked",
     "input": {"input_satiation_r2": 0.995, "shuffled_r2": {q: 0.01 for q in QUANTITIES},
               "groups_disjoint": False}, "expect": False},
]


def _run_gate(row):
    g, x = row["gate"], row["input"]
    if g == "G1":
        return dr.gate_G1(x, P)
    if g == "G2":
        return dr.gate_G2(x, P)[0]
    if g == "G3":
        return dr.gate_G3(x, P)
    return dr.gate_G4(x, P)


@pytest.mark.parametrize("row", GATE_ROWS, ids=lambda r: r["case"])
def test_gates_G1_to_G4(row):
    if row["expect"] == "RAISES":
        with pytest.raises(ValueError):
            _run_gate(row)
    else:
        assert _run_gate(row) is row["expect"]


def _runs(ord_s, mod_s, ord_b=None, mod_b=None):
    out = {}
    for i, s in enumerate(ord_s):
        out[f"O{42 + i}"] = {"arm": "ordinary", "S": s, "bites": (ord_b or [5.0] * 3)[i]}
    for i, s in enumerate(mod_s):
        out[f"M{42 + i}"] = {"arm": "modulated", "S": s, "bites": (mod_b or [5.0] * 3)[i]}
    return out


G5_ROWS = [
    {"case": "G5 all six competent", "why": "every run: stage-1 survival >= 150, bites >= 1.0",
     "input": _runs([200, 210, 205], [202, 208, 204]),
     "expect": {"yardstick_complete": True, "modulated_entered": 3}},
    {"case": "G5 one modulated run fails survival",
     "why": "M42 survives 149 < 150: excluded; 3 ordinary + 2 modulated still meet the minimum "
            "(the 'two modulated seeds' rule then applies)",
     "input": _runs([200, 210, 205], [149, 208, 204]),
     "expect": {"yardstick_complete": True, "modulated_entered": 2}},
    {"case": "G5 two modulated runs fail",
     "why": "only 1 modulated seed left: every A1-A4 verdict reads 'undetermined — yardstick "
            "incomplete'", "input": _runs([200, 210, 205], [149, 140, 204]),
     "expect": {"yardstick_complete": False, "modulated_entered": 1}},
    {"case": "G5 one ordinary run fails bites",
     "why": "O43 eats 0.9 < 1.0 bites: all 3 ordinary seeds are always required -> incomplete",
     "input": _runs([200, 210, 205], [202, 208, 204], ord_b=[5.0, 0.9, 5.0]),
     "expect": {"yardstick_complete": False, "modulated_entered": 3}},
    {"case": "G5 stage not complete", "why": "a run has no stage-1 survival yet: stop",
     "input": _runs([200, None, 205], [202, 208, 204]), "expect": "RAISES"},
]


@pytest.mark.parametrize("row", G5_ROWS, ids=lambda r: r["case"])
def test_gate_G5(row):
    if row["expect"] == "RAISES":
        with pytest.raises(ValueError):
            dr.gate_G5(row["input"], P)
        return
    r = dr.gate_G5(row["input"], P)
    assert r["yardstick_complete"] is row["expect"]["yardstick_complete"]
    assert len(r["entered"]["modulated"]) == row["expect"]["modulated_entered"]
    assert r["stage_index"] == 0


G6_ROWS = [
    {"case": "G6 sizes met", "why": "bootstrap_n 1000; every repeat holds >= 500 test groups",
     "input": {"bootstrap_n": 1000, "test_groups": {"satiation": [520, 510, 505, 530, 515]}},
     "expect": {"bootstrap_ok": True, "satiation": True}},
    {"case": "G6 bootstrap too small", "why": "bootstrap_n 999 < 1000",
     "input": {"bootstrap_n": 999, "test_groups": {"satiation": [520, 510, 505, 530, 515]}},
     "expect": {"bootstrap_ok": False, "satiation": True}},
    {"case": "G6 one repeat short for one quantity",
     "why": "steps_remaining (after dropping truncated episodes) has 499 groups in one repeat: "
            "that quantity is blocked, the other is not",
     "input": {"bootstrap_n": 1000, "test_groups": {"satiation": [520] * 5,
                                                    "steps_remaining": [520, 499, 510, 505, 530]}},
     "expect": {"bootstrap_ok": True, "satiation": True, "steps_remaining": False}},
    {"case": "G6 wrong number of repeats", "why": "4 repeats reported, the rules fix 5: stop",
     "input": {"bootstrap_n": 1000, "test_groups": {"satiation": [520] * 4}}, "expect": "RAISES"},
]


@pytest.mark.parametrize("row", G6_ROWS, ids=lambda r: r["case"])
def test_gate_G6(row):
    if row["expect"] == "RAISES":
        with pytest.raises(ValueError):
            dr.gate_G6(row["input"], P)
        return
    r = dr.gate_G6(row["input"], P)
    assert r["bootstrap_ok"] is row["expect"]["bootstrap_ok"]
    for k, v in row["expect"].items():
        if k != "bootstrap_ok":
            assert r["per_key"][k] is v


# =============================================================================================
# TABLE 2 — A1, one statistic on one layer (seed band [0.80, 0.90], untrained band [0.20, 0.40])
# =============================================================================================
def _stat(mo_diff, mean_q, band=(0.80, 0.90), untrained=(0.20, 0.40)):
    return {"band": band, "untrained_band": untrained, "mo_diff": mo_diff, "mo_diff_mean_q": mean_q}


A1_STAT_ROWS = [
    {"case": "all inside the band", "why": "6 MO_diff pairs inside [L, U]; mean's 5th pct 0.84 >= L",
     "input": _stat([0.85, 0.86, 0.84, 0.88, 0.87, 0.83], (0.84, 0.87)), "expect": "same"},
    {"case": "two below L (the allowance)",
     "why": "floor(6/3) = 2 pairs may lie below L; mean's 5th pct 0.81 >= L",
     "input": _stat([0.79, 0.78, 0.85, 0.86, 0.84, 0.83], (0.81, 0.85)), "expect": "same"},
    {"case": "three below L", "why": "3 > 2 below L: neither same nor all-below",
     "input": _stat([0.79, 0.78, 0.77, 0.86, 0.84, 0.83], (0.80, 0.84)),
     "expect": "undetermined at 3 seeds"},
    {"case": "count fine, mean interval dips below L",
     "why": "1 below L, but the mean's 5th pct 0.79 < L",
     "input": _stat([0.79, 0.81, 0.82, 0.81, 0.80, 0.81], (0.79, 0.83)),
     "expect": "undetermined at 3 seeds"},
    {"case": "all below, mean interval below L", "why": "all 6 below L, mean's 95th pct 0.68 < L",
     "input": _stat([0.60, 0.65, 0.70, 0.66, 0.62, 0.64], (0.62, 0.68)), "expect": "different"},
    {"case": "all below, mean interval reaches L",
     "why": "all 6 below L but the mean's 95th pct is exactly L (0.80, not < L)",
     "input": _stat([0.70, 0.75, 0.78, 0.76, 0.72, 0.74], (0.70, 0.80)),
     "expect": "undetermined at 3 seeds"},
    {"case": "closer than two ordinary seeds",
     "why": "MO_diff above U counts as same, flagged 'closer than two ordinary seeds'",
     "input": _stat([0.92, 0.93, 0.91, 0.95, 0.92, 0.94], (0.91, 0.94)),
     "expect": "same", "flag": "closer than two ordinary seeds"},
    {"case": "yardstick overlaps untrained networks",
     "why": "untrained band [0.85, 0.95] intersects [0.80, 0.90]: training made ordinary agents "
            "no more alike than untrained ones",
     "input": _stat([0.85] * 6, (0.84, 0.87), untrained=(0.85, 0.95)),
     "expect": "uninformative — no verdict"},
    {"case": "yardstick touches untrained band at an edge",
     "why": "untrained band [0.50, 0.80] meets L = 0.80: touching counts as intersecting",
     "input": _stat([0.85] * 6, (0.84, 0.87), untrained=(0.50, 0.80)),
     "expect": "uninformative — no verdict"},
    {"case": "two modulated seeds, one below",
     "why": "G5 left 2 modulated seeds: n = 4 MO_diff pairs, floor(4/3) = 1 may lie below L",
     "input": _stat([0.79, 0.85, 0.86, 0.84], (0.81, 0.85)), "expect": "same"},
    {"case": "two modulated seeds, two below", "why": "n = 4, 2 below L > 1 allowed",
     "input": _stat([0.79, 0.78, 0.86, 0.84], (0.80, 0.85)), "expect": "undetermined at 3 seeds"},
    {"case": "no untrained pairs", "why": "the informative gate cannot be computed: stop",
     "input": _stat([0.85] * 6, (0.84, 0.87), untrained=None), "expect": "RAISES"},
]


@pytest.mark.parametrize("row", A1_STAT_ROWS, ids=lambda r: r["case"])
def test_A1_statistic(row):
    if row["expect"] == "RAISES":
        with pytest.raises(ValueError):
            dr.statistic_verdict(row["input"], P)
        return
    r = dr.statistic_verdict(row["input"], P)
    assert r["word"] == row["expect"]
    assert r["flag"] == row.get("flag")


# TABLE 3 — A1 layer verdict: predictivity decides, CKA qualifies
A1_LAYER_ROWS = [
    {"case": "both same", "input": ("same", "same"), "expect": "same"},
    {"case": "predictivity same, CKA different", "input": ("same", "different"),
     "expect": "same up to a linear re-weighting"},
    {"case": "predictivity same, CKA undetermined", "input": ("same", "undetermined at 3 seeds"),
     "expect": "same up to a linear re-weighting"},
    {"case": "predictivity same, CKA uninformative",
     "input": ("same", "uninformative — no verdict"), "expect": "same up to a linear re-weighting"},
    {"case": "predictivity different, CKA same", "input": ("different", "same"),
     "expect": "different"},
    {"case": "predictivity undetermined, CKA same", "input": ("undetermined at 3 seeds", "same"),
     "expect": "undetermined at 3 seeds"},
    {"case": "predictivity uninformative, CKA different",
     "input": ("uninformative — no verdict", "different"), "expect": "uninformative (no verdict)"},
    {"case": "unknown word", "why": "a word no rule row names: stop",
     "input": ("similar", "same"), "expect": "RAISES"},
]


@pytest.mark.parametrize("row", A1_LAYER_ROWS, ids=lambda r: r["case"])
def test_A1_layer(row):
    if row["expect"] == "RAISES":
        with pytest.raises(ValueError):
            dr.layer_verdict(*row["input"])
    else:
        assert dr.layer_verdict(*row["input"]) == row["expect"]


SAME_S = _stat([0.85] * 6, (0.84, 0.87))
DIFF_S = _stat([0.6] * 6, (0.58, 0.62))
UND_S = _stat([0.79, 0.78, 0.77, 0.86, 0.84, 0.83], (0.80, 0.84))


def _a1(preds, ckas=None, mm=None):
    ckas = ckas or preds
    out = {}
    for k, p, c in zip(LAYERS, preds, ckas):
        p = dict(p)
        if mm is not None:
            p["mm_upper_max"] = mm
        out[k] = {"predictivity": p, "cka": c}
    return out


# TABLE 4 — A1 across the five verdict layers (study verdict, gates, remedy)
A1_STUDY_ROWS = [
    {"case": "all five same (either form)",
     "why": "3 layers same, 2 same up to a linear re-weighting (CKA different there)",
     "input": _a1([SAME_S] * 5, [SAME_S] * 3 + [DIFF_S] * 2),
     "expect": {"study": "same", "remedy_triggered": False}},
    {"case": "one layer different", "why": "any different layer makes the study 'different'",
     "input": _a1([SAME_S] * 4 + [DIFF_S]),
     "expect": {"study": "different", "different_layers": ["critic.out"], "remedy_triggered": False}},
    {"case": "three undetermined -> remedy reported",
     "why": "3 undetermined layers reach remedy.undetermined_layers_trigger: reported, not acted on",
     "input": _a1([UND_S] * 3 + [SAME_S] * 2),
     "expect": {"study": "undetermined", "remedy_triggered": True, "extra_seeds": [45, 46]}},
    {"case": "two undetermined -> no remedy", "input": _a1([UND_S] * 2 + [SAME_S] * 3),
     "expect": {"study": "undetermined", "remedy_triggered": False}},
    {"case": "MM also far apart -> qualifier",
     "why": "layer different and the highest MM 95th pct 0.79 < L: the qualifier is added",
     "input": _a1([DIFF_S] * 5, mm=0.79),
     "expect": {"study": "different", "qualifier": dr.MM_QUALIFIER}},
    {"case": "MM at L -> no qualifier", "input": _a1([DIFF_S] * 5, mm=0.80),
     "expect": {"study": "different", "qualifier": None}},
    {"case": "gate failed", "why": "G3 failed: every word reads 'blocked by gate G3'",
     "input": _a1([SAME_S] * 5), "gates": {**ALL_PASS, "G3": False},
     "expect": {"study": "blocked by gate G3"}},
    {"case": "yardstick incomplete", "why": "G5 left too few seeds",
     "input": _a1([SAME_S] * 5), "yardstick": False,
     "expect": {"study": "undetermined — yardstick incomplete"}},
    {"case": "interim prefix", "why": "under 'interim' every verdict word carries the prefix",
     "input": _a1([SAME_S] * 5), "policy": INTERIM,
     "expect": {"study": "provisional — end of stage 1 of 5: same"}},
]


@pytest.mark.parametrize("row", A1_STUDY_ROWS, ids=lambda r: r["case"])
def test_A1_study(row):
    r = dr.evaluate_A1(row["input"], P, policy=row.get("policy", EVID), verdict_layers=LAYERS,
                       gates=row.get("gates", ALL_PASS),
                       yardstick_complete=row.get("yardstick", True))
    e = row["expect"]
    assert r["study"]["verdict"] == e["study"]
    if "remedy_triggered" in e:
        assert r["study"]["remedy_triggered"] is e["remedy_triggered"]
    if "extra_seeds" in e:
        assert r["study"]["remedy_extra_seeds"] == e["extra_seeds"]
    if "different_layers" in e:
        assert r["study"]["different_layers"] == e["different_layers"]
    if "qualifier" in e:
        assert all(v["qualifier"] == e["qualifier"] for v in r["layers"].values())
    if row.get("policy") is INTERIM:
        assert all(v["verdict"].startswith(INTERIM.prefix) for v in r["layers"].values())


# =============================================================================================
# TABLE 5 — A2, one quantity on one layer. Ordinary R^2 = 0.50 / 0.52 / 0.54, each with a
# bootstrap interval 0.02 wide, so the ordinary spread is max(0.04, 0.02) = 0.04.
# "beats" = excess over the clock 0.20, its 5th pct 0.10 (beats); "no" = excess 0.01 (does not).
# =============================================================================================
BEAT = {"excess": 0.20, "excess_q_lo": 0.10}
NOBEAT = {"excess": 0.01, "excess_q_lo": -0.01}


def _ag(r2, b=BEAT, w=0.02):
    return {"r2": r2, "r2_q": (r2 - w / 2, r2 + w / 2), **b}


ORD = [_ag(0.50), _ag(0.52), _ag(0.54)]
A2_LAYER_ROWS = [
    {"case": "match", "why": "modulated 0.51/0.53/0.52: gap 0.00 <= 0.04; both arms encode",
     "input": (ORD, [_ag(0.51), _ag(0.53), _ag(0.52)]), "expect": "match"},
    {"case": "match — absent in both",
     "why": "no agent beats the clock (excess 0.01 < margin 0.05); gap small",
     "input": ([_ag(v, NOBEAT) for v in (0.50, 0.52, 0.54)],
               [_ag(v, NOBEAT) for v in (0.51, 0.53, 0.52)]), "expect": "match — absent in both"},
    {"case": "different: one side and a wide gap",
     "why": "modulated 0.60/0.62/0.61 all above every ordinary; gap 0.090 > 0.04",
     "input": (ORD, [_ag(0.60), _ag(0.62), _ag(0.61)]), "expect": "different"},
    {"case": "gap wide but sides overlap",
     "why": "modulated 0.45/0.62/0.65: gap 0.053 > 0.04 but 0.45 lies below the ordinary values",
     "input": (ORD, [_ag(0.45), _ag(0.62), _ag(0.65)]), "expect": "undetermined at 3 seeds"},
    {"case": "different: one arm beats the clock, the other never",
     "why": "every ordinary seed beats the clock, no modulated seed does (R^2 close)",
     "input": (ORD, [_ag(v, NOBEAT) for v in (0.51, 0.53, 0.52)]), "expect": "different"},
    {"case": "arms disagree on encoding, not all-vs-none",
     "why": "ordinary encodes; only 1 of 3 modulated seeds beats (< 2): not a match, not "
            "'none of the other arm'",
     "input": (ORD, [_ag(0.51), _ag(0.53, NOBEAT), _ag(0.52, NOBEAT)]),
     "expect": "undetermined at 3 seeds"},
    {"case": "spread floored by interval width",
     "why": "ordinary all 0.52 (range 0) with 0.06-wide intervals: spread 0.06; modulated 0.57 "
            "gap 0.05 <= 0.06 -> match (a lucky narrow spread cannot make it differ)",
     "input": ([_ag(0.52, w=0.06)] * 3, [_ag(0.57)] * 3), "expect": "match"},
    {"case": "excess over margin but its 5th pct not > 0",
     "why": "excess 0.06 >= 0.05 yet its 5th pct is -0.01: does not beat the clock, so no "
            "modulated seed encodes -> all-vs-none",
     "input": (ORD, [_ag(v, {"excess": 0.06, "excess_q_lo": -0.01}) for v in (0.51, 0.53, 0.52)]),
     "expect": "different"},
    {"case": "two modulated seeds, one beats",
     "why": "with 2 modulated seeds '>= 2 of 3' reads 'both': 1 of 2 does not encode",
     "input": (ORD, [_ag(0.51), _ag(0.53, NOBEAT)]), "expect": "undetermined at 3 seeds"},
    {"case": "two modulated seeds, both beat", "input": (ORD, [_ag(0.51), _ag(0.53)]),
     "expect": "match"},
]


@pytest.mark.parametrize("row", A2_LAYER_ROWS, ids=lambda r: r["case"])
def test_A2_layer(row):
    assert dr.a2_layer(*row["input"], P)["word"] == row["expect"]


MATCH_L = {"ordinary": ORD, "modulated": [_ag(0.51), _ag(0.53), _ag(0.52)]}
DIFF_L = {"ordinary": ORD, "modulated": [_ag(0.60), _ag(0.62), _ag(0.61)]}


def _a2(per_q):
    return {q: {"g6_pass": g6, "layers": dict(zip(LAYERS, lays))} for q, (g6, lays) in per_q.items()}


def _allq(lays, **over):
    return {q: over.get(q, (True, lays)) for q in QUANTITIES}


# TABLE 6 — A2 profile per quantity and study verdict
A2_PROFILE_ROWS = [
    {"case": "all layers match", "input": _a2(_allq([MATCH_L] * 5)),
     "expect": {"profile": "matching", "study": "matching"}},
    {"case": "two layers different", "why": "2 >= differs_min_layers: the quantity differs",
     "input": _a2(_allq([MATCH_L] * 5, satiation=(True, [DIFF_L] * 2 + [MATCH_L] * 3))),
     "expect": {"profile": "differs", "study": "differs"}},
    {"case": "one layer different", "why": "1 differing layer is reported, not counted",
     "input": _a2(_allq([MATCH_L] * 5, satiation=(True, [DIFF_L] + [MATCH_L] * 4))),
     "expect": {"profile": "undetermined", "note": "one-layer difference (not counted)",
                "study": "undetermined"}},
    {"case": "G6 blocks one quantity",
     "why": "steps_remaining has too few test groups: that quantity reads 'blocked by gate G6'",
     "input": _a2(_allq([MATCH_L] * 5, steps_remaining=(False, [MATCH_L] * 5))),
     "q": "steps_remaining", "expect": {"profile": "blocked by gate G6", "study": "undetermined"}},
]


@pytest.mark.parametrize("row", A2_PROFILE_ROWS, ids=lambda r: r["case"])
def test_A2_profile(row):
    r = dr.evaluate_A2(row["input"], P, policy=EVID, quantities=QUANTITIES,
                       verdict_layers=LAYERS, gates=ALL_PASS, yardstick_complete=True)
    q = row.get("q", "satiation")
    assert r["quantities"][q]["profile"] == row["expect"]["profile"]
    assert r["study"]["verdict"] == row["expect"]["study"]
    if "note" in row["expect"]:
        assert r["quantities"][q]["note"] == row["expect"]["note"]


# =============================================================================================
# TABLE 7 — A3 pattern per layer. U (top of the seed band) = 0.90. "E" = same-seed excess:
# every same-seed pair above every different-seed pair and above U, and the same-seed mean's
# 5th pct above the different-seed mean's 95th pct.
# =============================================================================================
E_YES = {"mo_same": [0.97, 0.96, 0.98], "mo_diff": [0.85, 0.86, 0.84, 0.88, 0.87, 0.83],
         "U": 0.90, "mo_same_mean_q_lo": 0.95, "mo_diff_mean_q_hi": 0.88}
E_NO = {"mo_same": [0.86, 0.85, 0.87], "mo_diff": [0.85, 0.86, 0.84, 0.88, 0.87, 0.83],
        "U": 0.90, "mo_same_mean_q_lo": 0.84, "mo_diff_mean_q_hi": 0.88}
E_OVERLAP = {**E_YES, "mo_same_mean_q_lo": 0.87}          # points fine, intervals overlap
SURV_SAME = {"available": True, "same": True}
SURV_DIFF = {"available": True, "same": False}
SURV_NA = {"available": False, "same": None}

A3_ROWS = [
    {"case": "(a) alike only with a shared seed", "why": "E holds, A1 undetermined",
     "input": ("undetermined at 3 seeds", E_YES, True, SURV_SAME), "expect": dr.A3_A},
    {"case": "(a) with A1 different", "why": "E holds, A1 different (not same)",
     "input": ("different", E_YES, True, SURV_SAME), "expect": dr.A3_A},
    {"case": "(b) one solution", "why": "A1 same, no same-seed excess",
     "input": ("same", E_NO, True, SURV_SAME), "expect": dr.A3_B},
    {"case": "(b+) one solution with excess", "why": "A1 same up to linear re-weighting, E holds",
     "input": ("same up to a linear re-weighting", E_YES, True, SURV_SAME), "expect": dr.A3_BPLUS},
    {"case": "(c) same survival", "why": "A1 different, no E, survival inside 2 x SE",
     "input": ("different", E_NO, True, SURV_SAME), "expect": dr.A3_C},
    {"case": "(c') different survival", "why": "A1 different, no E, survival beyond 2 x SE",
     "input": ("different", E_NO, True, SURV_DIFF), "expect": dr.A3_CPRIME},
    {"case": "none: A1 undetermined, no E",
     "input": ("undetermined at 3 seeds", E_NO, True, SURV_SAME), "expect": dr.A3_NONE},
    {"case": "none: A1 uninformative, no E",
     "input": ("uninformative (no verdict)", E_NO, True, SURV_SAME), "expect": dr.A3_NONE},
    {"case": "none: survival not available", "why": "A1 different, no E, survival missing",
     "input": ("different", E_NO, True, SURV_NA), "expect": dr.A3_NONE},
    {"case": "E fails on overlapping intervals",
     "why": "points separate, but same-seed mean's 5th pct 0.87 <= 0.88: no E; A1 same -> (b)",
     "input": ("same", E_OVERLAP, True, SURV_SAME), "expect": dr.A3_B},
    {"case": "shared start not verified",
     "why": "Checkpoint 3.3 failed for a seed: E treated as not holding, (a) cannot occur",
     "input": ("undetermined at 3 seeds", E_YES, False, SURV_SAME), "expect": dr.A3_NONE},
    {"case": "shared start not verified, A1 same", "input": ("same", E_YES, False, SURV_SAME),
     "expect": dr.A3_B},
    {"case": "two modulated seeds", "why": "2 same-seed pairs, 4 different-seed pairs, E holds",
     "input": ("same", {**E_YES, "mo_same": [0.97, 0.96], "mo_diff": [0.85, 0.86, 0.84, 0.88]},
               True, SURV_SAME), "expect": dr.A3_BPLUS},
    {"case": "A1 word not in the rules' vocabulary",
     "why": "'similar' is no A1 layer verdict: stop rather than read it as 'none'",
     "input": ("similar", E_NO, True, SURV_SAME), "expect": "RAISES"},
]


@pytest.mark.parametrize("row", A3_ROWS, ids=lambda r: r["case"])
def test_A3_pattern(row):
    a1, v, pre, surv = row["input"]
    if row["expect"] == "RAISES":
        with pytest.raises(ValueError):
            dr.a3_pattern(a1, dr.same_seed_excess(v, pre), surv)
        return
    assert dr.a3_pattern(a1, dr.same_seed_excess(v, pre), surv) == row["expect"]


A3_STUDY_ROWS = [
    {"case": "three layers (b)", "input": [dr.A3_B] * 3 + [dr.A3_C] * 2, "expect": dr.A3_B},
    {"case": "no pattern reaches 3 layers", "input": [dr.A3_B] * 2 + [dr.A3_C] * 2 + [dr.A3_NONE],
     "expect": "mixed across layers"},
]


@pytest.mark.parametrize("row", A3_STUDY_ROWS, ids=lambda r: r["case"])
def test_A3_study(row):
    assert dr._study_pattern(dict(zip(LAYERS, row["input"])), P) == row["expect"]


# TABLE 7c — A3 when a gate blocks (Checkpoint R.2, designer item 1): the pattern words are
# replaced by the gate's word on every layer and in the study reading, as in A1, A2 and A4
A3_GATE_ROWS = [
    {"case": "A3 gate failed",
     "why": "G1 failed: every A3 layer pattern and the study reading read 'blocked by gate G1'",
     "input": {"gates": {**ALL_PASS, "G1": False}, "yardstick": True, "policy": EVID},
     "expect": "blocked by gate G1"},
    {"case": "A3 yardstick incomplete",
     "why": "G5 left too few seeds: every A3 layer pattern and the study reading read "
            "'undetermined — yardstick incomplete'",
     "input": {"gates": ALL_PASS, "yardstick": False, "policy": EVID},
     "expect": "undetermined — yardstick incomplete"},
    {"case": "A3 gate failed, interim",
     "why": "under 'interim' the gate word carries the prefix like every other word",
     "input": {"gates": {**ALL_PASS, "G1": False}, "yardstick": True, "policy": INTERIM},
     "expect": "provisional — end of stage 1 of 5: blocked by gate G1"},
]


@pytest.mark.parametrize("row", A3_GATE_ROWS, ids=lambda r: r["case"])
def test_A3_gate_word(row):
    x = row["input"]
    inp = {k: {"a1_verdict": "same", **E_NO} for k in LAYERS}
    r = dr.evaluate_A3(inp, P, policy=x["policy"], verdict_layers=LAYERS, gates=x["gates"],
                       yardstick_complete=x["yardstick"], precondition_shared_start=True,
                       survival=SURV_SAME)
    assert all(v["pattern"] == row["expect"] for v in r["layers"].values())
    assert r["study"]["reading"] == row["expect"]
    assert all(v["E"] is None for v in r["layers"].values())


# TABLE 8 — survival difference for A3 pattern (c) (modulated minus ordinary, steps)
SURVIVAL_ROWS = [
    {"case": "inside 2 x SE", "why": "diff 6.0; SE = sqrt(25/3 + 25/3) = 4.08 > floor 3.6; 6 <= 8.16",
     "input": {"ordinary": [200, 205, 210], "modulated": [206, 211, 216]},
     "expect": {"same": True, "floored": False}},
    {"case": "beyond 2 x floored SE", "why": "diff 8.0; SE 0.41 floored to 3.6; 8 > 7.2",
     "input": {"ordinary": [200, 200.5, 201], "modulated": [208, 208.5, 209]},
     "expect": {"same": False, "floored": True}},
    {"case": "survival missing", "input": {"ordinary": [200, None, 210], "modulated": [206, 211, 216]},
     "expect": {"available": False}},
]


@pytest.mark.parametrize("row", SURVIVAL_ROWS, ids=lambda r: r["case"])
def test_survival_difference(row):
    r = dr.survival_difference(row["input"], P)
    for k, v in row["expect"].items():
        assert r[k] is v


def test_survival_stage_index_by_status():
    assert dr.survival_stage_index(P, "evidence") == 4
    assert dr.survival_stage_index(P, "interim") == 0
    with pytest.raises(ValueError):
        dr.survival_stage_index(P, "pilot")


# =============================================================================================
# TABLE 9 — A4 across worlds, per layer. Movement: per seed, the 5th pct of (mean movement -
# within-stage drift); an arm moves when >= 2 of 3 seeds are above 0. Co-movement r judged by
# A1's rule against the ordinary pairs' band [0.80, 0.90].
# =============================================================================================
SEQ = FIXTURE_P["A4"]["stage_sequence"]
MOVE = [0.1, 0.2, 0.15]
TOGETHER = _stat([0.85] * 6, (0.84, 0.87), untrained=None)
INDEP = _stat([0.3] * 6, (0.25, 0.35), untrained=None)
UNDCO = _stat([0.79, 0.78, 0.77, 0.86, 0.84, 0.83], (0.80, 0.84), untrained=None)


def _a4(mv_o, mv_m, co, ends):
    return {"movement": {"ordinary": mv_o, "modulated": mv_m}, "co_movement": co,
            "stage_end_a1": dict(zip(SEQ, ends))}


A4_ROWS = [
    {"case": "move together", "why": "both arms move, r 'same', no stage end reads different",
     "input": _a4(MOVE, MOVE, TOGETHER, ["same"] * 5), "expect": "move together"},
    {"case": "together, stage ends undetermined",
     "why": "no stage end reads different (undetermined is not different)",
     "input": _a4(MOVE, MOVE, TOGETHER, ["undetermined at 3 seeds"] * 5), "expect": "move together"},
    {"case": "r together but same at one end, different at another",
     "why": "A1 same at stage_end:0, different at final -> independently",
     "input": _a4(MOVE, MOVE, TOGETHER, ["same"] * 4 + ["different"]),
     "expect": "move independently"},
    {"case": "r independent", "input": _a4(MOVE, MOVE, INDEP, ["same"] * 5),
     "expect": "move independently"},
    {"case": "modulated arm does not move", "why": "only 1 of 3 modulated seeds above drift",
     "input": _a4(MOVE, [0.1, -0.1, -0.2], TOGETHER, ["same"] * 5),
     "expect": "no measurable movement across worlds — undetermined"},
    {"case": "r undetermined", "input": _a4(MOVE, MOVE, UNDCO, ["same"] * 5),
     "expect": "undetermined at 3 seeds"},
    {"case": "different at one end only, r undetermined",
     "why": "a different end but no same end and r undetermined: none of the readings",
     "input": _a4(MOVE, MOVE, UNDCO, ["undetermined at 3 seeds"] * 4 + ["different"]),
     "expect": "undetermined at 3 seeds"},
    {"case": "two modulated seeds, both move", "input": _a4(MOVE, [0.1, 0.2], TOGETHER, ["same"] * 5),
     "expect": "move together"},
    {"case": "two modulated seeds, one moves", "why": "'>= 2 of 3' reads 'both'",
     "input": _a4(MOVE, [0.1, -0.2], TOGETHER, ["same"] * 5),
     "expect": "no measurable movement across worlds — undetermined"},
]


@pytest.mark.parametrize("row", A4_ROWS, ids=lambda r: r["case"])
def test_A4(row):
    inp = {"layout": dr.a4_layout(P), "layers": {k: row["input"] for k in LAYERS}}
    r = dr.evaluate_A4(inp, P, policy=EVID, verdict_layers=LAYERS, gates=ALL_PASS,
                       yardstick_complete=True)
    assert r["layers"]["enc.out"]["reading"] == row["expect"]
    assert r["study"]["reading"] == row["expect"]


def test_A4_layout_mismatch_raises():
    inp = {"layout": {**dr.a4_layout(P), "probes": ["active"]},
           "layers": {k: _a4(MOVE, MOVE, TOGETHER, ["same"] * 5) for k in LAYERS}}
    with pytest.raises(ValueError):
        dr.evaluate_A4(inp, P, policy=EVID, verdict_layers=LAYERS, gates=ALL_PASS,
                       yardstick_complete=True)


def test_A4_layout_counts():
    lay = dr.a4_layout(P)
    assert len(lay["profile_entries"]) == 8 and len(lay["drift_pairs"]) == 2


# =============================================================================================
# TABLE 10 — B2 reading of one measure across the 16 level-05 worlds (sign test, alpha 0.05,
# null p 1/2), and whether the 3 May seeds agree
# =============================================================================================
def _b(late=0, early=0, coin=0, undef=0):
    return ["late"] * late + ["early"] * early + ["coincident"] * coin + [None] * undef


B2_ROWS = [
    {"case": "12 of 16 late", "why": "n_def 16 -> k* = 12 (P(X>=12) = 0.038)",
     "input": (_b(late=12, early=2, coin=2), ["late"] * 3),
     "expect": {"reading": "late", "k_star": 12, "may": "agree"}},
    {"case": "11 of 16 late", "why": "11 < k* = 12", "input": (_b(late=11, early=3, coin=2), ["late"] * 3),
     "expect": {"reading": "undetermined across worlds", "k_star": 12, "may": "do not agree"}},
    {"case": "12 of 16 early", "input": (_b(early=12, late=1, coin=3), ["early"] * 3),
     "expect": {"reading": "early", "k_star": 12, "may": "agree"}},
    {"case": "coincident runs count in n_def", "why": "12 late + 4 coincident: n_def 16",
     "input": (_b(late=12, coin=4), ["late"] * 3), "expect": {"reading": "late", "k_star": 12}},
    {"case": "undefined lags leave n_def",
     "why": "12 late + 4 NaN: n_def 12 -> k* = 10 (P(X>=10) = 0.019)",
     "input": (_b(late=12, undef=4), ["late"] * 3), "expect": {"reading": "late", "k_star": 10}},
    {"case": "too few defined runs", "why": "n_def 4, all late: P(X>=4) = 0.0625 > 0.05, no k*",
     "input": (_b(late=4, undef=12), ["late"] * 3),
     "expect": {"reading": "undetermined across worlds", "k_star": None}},
    {"case": "five defined, all late", "why": "n_def 5: P(X>=5) = 0.031 -> k* = 5",
     "input": (_b(late=5, undef=11), ["late"] * 3), "expect": {"reading": "late", "k_star": 5}},
    {"case": "a May seed coincident", "why": "not on the late side -> do not agree",
     "input": (_b(late=12, coin=4), ["late", "coincident", "late"]),
     "expect": {"reading": "late", "may": "do not agree"}},
    {"case": "a May seed undefined", "why": "every May seed must be defined",
     "input": (_b(late=12, coin=4), ["late", None, "late"]),
     "expect": {"reading": "late", "may": "do not agree"}},
    {"case": "level-05 undetermined, May all late",
     "why": "READING FOR SIGN-OFF: with no level-05 side there is nothing to agree with; the "
            "code reads the rule's 'agree' condition literally (fails) -> 'do not agree'",
     "input": (_b(late=8, early=8), ["late"] * 3),
     "expect": {"reading": "undetermined across worlds", "may": "do not agree"}},
]


@pytest.mark.parametrize("row", B2_ROWS, ids=lambda r: r["case"])
def test_B2(row):
    r = dr.evaluate_B2(*row["input"], P, policy=B2POL)
    for k, v in row["expect"].items():
        assert r[k] == v


# =============================================================================================
# TABLE 11 — a missing (non-finite) summary statistic. A NaN from a failed fit or an empty
# bootstrap draw is a data defect, not a statistic: the rules give it no outcome, so every
# rule family STOPS rather than letting the NaN fall into some verdict word.
# =============================================================================================
NAN = float("nan")
NONFINITE_ROWS = [
    {"case": "A1 NaN summary -> RAISES", "family": "A1 one statistic",
     "why": "one MO_diff pair's value is NaN (its fit failed)",
     "input": _stat([0.85, NAN, 0.84, 0.88, 0.87, 0.83], (0.84, 0.87)), "expect": "RAISES"},
    {"case": "A1 NaN yardstick edge -> RAISES", "family": "A1 informative gate",
     "why": "the untrained band's upper edge is NaN",
     "input": _stat([0.85] * 6, (0.84, 0.87), untrained=(0.20, NAN)), "expect": "RAISES"},
    {"case": "A2 NaN summary -> RAISES", "family": "A2 one quantity, one layer",
     "why": "one ordinary agent's decoding R^2 is NaN",
     "input": ([_ag(0.50), _ag(NAN), _ag(0.54)], [_ag(0.51), _ag(0.53), _ag(0.52)]),
     "expect": "RAISES"},
    {"case": "A2 NaN clock excess -> RAISES", "family": "A2 beats the clock",
     "why": "the 5th percentile of one agent's excess over the clock is NaN",
     "input": (ORD, [_ag(0.51), _ag(0.53, {"excess": 0.2, "excess_q_lo": NAN}), _ag(0.52)]),
     "expect": "RAISES"},
    {"case": "A3 NaN summary -> RAISES", "family": "A3 same-seed excess",
     "why": "one same-seed pair's value is NaN",
     "input": {**E_YES, "mo_same": [0.97, NAN, 0.98]}, "expect": "RAISES"},
    {"case": "A3 NaN survival -> RAISES", "family": "A3 survival difference",
     "why": "one seed's stage survival is NaN (not None, which means 'not available')",
     "input": {"ordinary": [200, NAN, 210], "modulated": [206, 211, 216]}, "expect": "RAISES"},
    {"case": "A4 NaN summary -> RAISES", "family": "A4 movement",
     "why": "one modulated seed's movement 5th percentile is NaN",
     "input": [0.1, NAN, 0.15], "expect": "RAISES"},
    {"case": "bootstrap NaN draw -> RAISES", "family": "summaries from bootstrap draws",
     "why": "one bootstrap draw of an ordinary pair is NaN",
     "input": "draws", "expect": "RAISES"},
]


def _run_nonfinite(row):
    fam, x = row["family"], row["input"]
    if fam.startswith("A1"):
        return dr.statistic_verdict(x, P)
    if fam == "A2 one quantity, one layer" or fam == "A2 beats the clock":
        return dr.a2_layer(*x, P)
    if fam == "A3 same-seed excess":
        return dr.same_seed_excess(x, True)
    if fam == "A3 survival difference":
        return dr.survival_difference(x, P)
    if fam == "A4 movement":
        return dr.arm_moves(x, P)
    draws = np.full(50, 0.8)
    draws[7] = NAN
    pairs = {s: {f"{s}{i}": {"point": 0.8, "draws": draws if s == "OO" else np.full(50, 0.8)}
                 for i in range(n)} for s, n in (("OO", 3), ("MO_diff", 6), ("UNTRAINED", 3))}
    return dr.summarise_pairs(pairs, P)


@pytest.mark.parametrize("row", NONFINITE_ROWS, ids=lambda r: r["case"])
def test_nonfinite_summary_raises(row):
    with pytest.raises(ValueError, match="non-finite"):
        _run_nonfinite(row)


def test_nonfinite_through_the_evaluators():
    """The same NaN reaches the raise through evaluate_A1/A2/A4 (not only the leaf functions)."""
    bad = _stat([0.85, NAN, 0.84, 0.88, 0.87, 0.83], (0.84, 0.87))
    with pytest.raises(ValueError, match="non-finite"):
        dr.evaluate_A1(_a1([bad] * 5), P, policy=EVID, verdict_layers=LAYERS, gates=ALL_PASS,
                       yardstick_complete=True)
    nan_l = {"ordinary": [_ag(0.50), _ag(NAN), _ag(0.54)], "modulated": MATCH_L["modulated"]}
    with pytest.raises(ValueError, match="non-finite"):
        dr.evaluate_A2(_a2(_allq([nan_l] * 5)), P, policy=EVID, quantities=QUANTITIES,
                       verdict_layers=LAYERS, gates=ALL_PASS, yardstick_complete=True)
    inp = {"layout": dr.a4_layout(P), "layers": {k: _a4(MOVE, [0.1, NAN, 0.2], TOGETHER,
                                                         ["same"] * 5) for k in LAYERS}}
    with pytest.raises(ValueError, match="non-finite"):
        dr.evaluate_A4(inp, P, policy=EVID, verdict_layers=LAYERS, gates=ALL_PASS,
                       yardstick_complete=True)


# =============================================================================================
# Contract tests (§E): pin, evidence status, order
# =============================================================================================
def _real_pinned():
    raw = open(os.path.join(ROOT, RULES), "rb").read()
    return rules_pin.load({"decision_rules": {"file": RULES,
                                              "sha256": hashlib.sha256(raw).hexdigest()}})


def test_sha_mismatch_raises():
    with pytest.raises(ValueError, match="sha256"):
        dr.load({"decision_rules": {"file": RULES, "sha256": "0" * 64}})


def test_load_is_rules_pin_load():
    """Revision 4, R4-3: one loader. decision_rules imports neither hashlib nor yaml."""
    assert dr.load is rules_pin.load and dr.require_clean is rules_pin.require_clean
    tree = ast.parse(open(os.path.join(ROOT, "scripts", "analysis", "nmn", "decision_rules.py")).read())
    names = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    names |= {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
    assert not names & {"hashlib", "yaml"}


def test_pilot_policy_forbids_every_evaluator():
    pin = _real_pinned()
    pol = dr.verdict_policy(pin, "pilot")
    assert pol.allowed is False and "not evidence" in pol.label
    with pytest.raises(ValueError, match="no verdict word"):
        dr.evaluate_A1(_a1([SAME_S] * 5), P, policy=pol, verdict_layers=LAYERS, gates=ALL_PASS,
                       yardstick_complete=True)
    with pytest.raises(ValueError):
        dr.evaluate_A2({}, P, policy=pol, quantities=[], verdict_layers=LAYERS, gates=ALL_PASS,
                       yardstick_complete=True)
    with pytest.raises(ValueError):
        dr.evaluate_A3({}, P, policy=pol, verdict_layers=LAYERS, gates=ALL_PASS,
                       yardstick_complete=True, precondition_shared_start=True, survival=SURV_SAME)
    with pytest.raises(ValueError):
        dr.evaluate_A4({}, P, policy=pol, verdict_layers=LAYERS, gates=ALL_PASS,
                       yardstick_complete=True)
    with pytest.raises(ValueError):
        dr.evaluate_B2([], [], P, policy=pol)


def test_interim_policy_prefix_from_rules():
    pol = dr.verdict_policy(_real_pinned(), "interim")
    assert pol.allowed and pol.prefix == "provisional — end of stage 1 of 5"
    r = dr.evaluate_A2(_a2(_allq([MATCH_L] * 5)), P, policy=pol, quantities=QUANTITIES,
                       verdict_layers=LAYERS, gates=ALL_PASS, yardstick_complete=True)
    words = [r["study"]["verdict"]] + [q["profile"] for q in r["quantities"].values()] + \
        [lv["word"] for q in r["quantities"].values() for lv in q["layers"].values()]
    assert all(w.startswith(pol.prefix + ": ") for w in words)


def test_b2_status_accepted_label_returned_and_dirty_blocks():
    pin = _real_pinned()
    pol = dr.verdict_policy(pin, "b2_wakeup")
    assert pol.allowed and pol.label.startswith("wake-up timing")
    dirty = rules_pin.PinnedRules(**{**pin.__dict__, "dirty": True})
    for status in ("b2_wakeup", "interim", "evidence"):
        with pytest.raises(ValueError, match="uncommitted"):
            dr.enforce_order(dirty, dr.verdict_policy(dirty, status))
    dr.enforce_order(dirty, dr.verdict_policy(dirty, "pilot"))    # no verdict words: allowed


def test_require_clean_raises_on_dirty():
    pin = _real_pinned()
    rules_pin.require_clean(rules_pin.PinnedRules(**{**pin.__dict__, "dirty": False}))
    with pytest.raises(ValueError):
        rules_pin.require_clean(rules_pin.PinnedRules(**{**pin.__dict__, "dirty": True}))


def test_unknown_status_raises():
    with pytest.raises(ValueError):
        dr.verdict_policy(_real_pinned(), "final_answer")


def test_b2_and_a_analyses_do_not_cross():
    with pytest.raises(ValueError, match="B2 manifest"):
        dr.evaluate_A1(_a1([SAME_S] * 5), P, policy=B2POL, verdict_layers=LAYERS, gates=ALL_PASS,
                       yardstick_complete=True)
    with pytest.raises(ValueError, match="only produced"):
        dr.evaluate_B2(_b(late=12, coin=4), ["late"] * 3, P, policy=EVID)


def test_real_rules_lists_match_the_fixtures():
    pin = _real_pinned()
    assert pin.rules["common"]["verdict_layers"] == LAYERS
    assert list(pin.rules["A2"]["quantities"]) == QUANTITIES


# =============================================================================================
# No numeric constant in code (decision_rules.py, wakeup.py)
# =============================================================================================
@pytest.mark.parametrize("mod", ["decision_rules.py", "wakeup.py"])
def test_no_numeric_literals(mod):
    path = os.path.join(ROOT, "scripts", "analysis", "nmn", mod)
    bad = []
    for node in ast.walk(ast.parse(open(path).read())):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float, complex)) \
                and not isinstance(node.value, bool) and node.value not in (0, 1):
            bad.append((node.lineno, node.value))
    assert not bad, f"{mod}: numeric literals other than 0 and 1: {bad}"


@pytest.mark.parametrize("mod", ["decision_rules.py", "wakeup.py"])
def test_no_number_hidden_in_a_string(mod):
    """float("0.05") / int("3") would pass the literal test above: refuse any float(<str>) or
    int(<str>) call on a string constant (math.nan / math.inf are the spelled-out forms)."""
    path = os.path.join(ROOT, "scripts", "analysis", "nmn", mod)
    bad = [n.lineno for n in ast.walk(ast.parse(open(path).read()))
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
           and n.func.id in ("float", "int", "complex")
           and any(isinstance(a, ast.Constant) and isinstance(a.value, str) for a in n.args)]
    assert not bad, f"{mod}: number parsed from a string constant at lines {bad}"


ALLOWED_IMPORTS = {"__future__", "math", "dataclasses", "numpy", "scripts.analysis.nmn.rules_pin"}


@pytest.mark.parametrize("mod", ["decision_rules.py", "wakeup.py"])
def test_import_allow_list(mod):
    """Only these imports, so no number can come in from another module (a constants file, a
    config, the rules file read a second way). `from scripts.analysis.nmn import rules_pin`
    counts as scripts.analysis.nmn.rules_pin. No dynamic import either."""
    tree = ast.parse(open(os.path.join(ROOT, "scripts", "analysis", "nmn", mod)).read())
    got = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            got |= {a.name for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            if n.module == "scripts.analysis.nmn":
                got |= {f"{n.module}.{a.name}" for a in n.names}
            else:
                got.add(n.module)
        elif isinstance(n, ast.Call) and isinstance(n.func, (ast.Name, ast.Attribute)):
            name = n.func.id if isinstance(n.func, ast.Name) else n.func.attr
            assert name not in ("__import__", "import_module", "exec", "eval"), \
                f"{mod}: dynamic import / eval at line {n.lineno}"
    assert got <= ALLOWED_IMPORTS, f"{mod}: imports outside the allow-list: {sorted(got - ALLOWED_IMPORTS)}"


# =============================================================================================
# Parameter coverage against the REAL rules file: every parameters entry is read by some
# function, and no function reads an entry the file lacks (no exemption list).
# =============================================================================================
class Rec(dict):
    def __init__(self, d, path, seen):
        super().__init__({k: (Rec(v, f"{path}{k}.", seen) if isinstance(v, dict) else v)
                          for k, v in d.items()})
        self._path, self._seen = path, seen

    def __getitem__(self, k):
        v = super().__getitem__(k)
        if not isinstance(v, Rec):
            self._seen.add(self._path + k)
        return v


def _leaves(d, path=""):
    out = set()
    for k, v in d.items():
        out |= _leaves(v, f"{path}{k}.") if isinstance(v, dict) else {path + k}
    return out


def _exercise(Pr):
    """Call every function once with plausible inputs (outcomes do not matter here)."""
    dr.gate_G1(_g1(100, 0, 0, margin=Pr["gates"]["G1"]["near_tie_logit_margin"]), Pr)
    dr.gate_G2({"x": {"max_abs_dev": 0.0, "max_abs_ref": 1.0}}, Pr)
    dr.gate_G3({"alignment": _g1(100, 0, 0, margin=Pr["gates"]["G1"]["near_tie_logit_margin"]),
                "shift_control_agreement": 0.5}, Pr)
    dr.gate_G4({"input_satiation_r2": 1.0, "shuffled_r2": {"q": 0.0}, "groups_disjoint": True}, Pr)
    dr.gate_G5(_runs([200, 210, 205], [202, 208, 204]), Pr)
    dr.gate_G6({"bootstrap_n": 1000, "test_groups": {"q": [600] * 5}}, Pr)
    dr.split_settings(Pr)
    dr.survival_settings(Pr)
    dr.b2_settings(Pr)
    dr.survival_stage_index(Pr, "evidence")
    dr.survival_stage_index(Pr, "interim")
    rng = np.random.default_rng(0)
    pairs = {s: {f"{s}{i}": {"point": 0.8, "draws": rng.normal(0.8, 0.01, 50)} for i in range(n)}
             for s, n in (("OO", 3), ("MM", 3), ("MO_diff", 6), ("MO_same", 3), ("UNTRAINED", 3))}
    summ = dr.summarise_pairs(pairs, Pr)
    dr.evaluate_A1({k: {"predictivity": summ, "cka": summ} for k in LAYERS}, Pr, policy=EVID,
                   verdict_layers=LAYERS, gates=ALL_PASS, yardstick_complete=True)
    dr.evaluate_A2(_a2(_allq([MATCH_L] * 5)), Pr, policy=EVID, quantities=QUANTITIES,
                   verdict_layers=LAYERS, gates=ALL_PASS, yardstick_complete=True)
    dr.evaluate_A2(_a2(_allq([MATCH_L] * 5, satiation=(True, [DIFF_L] + [MATCH_L] * 4))), Pr,
                   policy=EVID, quantities=QUANTITIES, verdict_layers=LAYERS, gates=ALL_PASS,
                   yardstick_complete=True)
    dr.survival_difference({"ordinary": [200, 205, 210], "modulated": [206, 211, 216]}, Pr)
    dr.evaluate_A3({k: {"a1_verdict": "same", **E_NO} for k in LAYERS}, Pr, policy=EVID,
                   verdict_layers=LAYERS, gates=ALL_PASS, yardstick_complete=True,
                   precondition_shared_start=True, survival=SURV_SAME)
    seq = list(Pr["A4"]["stage_sequence"])
    dr.evaluate_A4({"layout": dr.a4_layout(Pr),
                    "layers": {k: {"movement": {"ordinary": MOVE, "modulated": MOVE},
                                   "co_movement": TOGETHER,
                                   "stage_end_a1": {c: "same" for c in seq}} for k in LAYERS}},
                   Pr, policy=EVID, verdict_layers=LAYERS, gates=ALL_PASS, yardstick_complete=True)
    dr.evaluate_B2(_b(late=12, coin=4), ["late"] * 3, Pr, policy=B2POL)


def test_parameter_coverage_real_rules():
    real = _real_pinned().parameters
    seen: set = set()
    _exercise(Rec(real, "", seen))
    leaves = _leaves(real)
    assert leaves - seen == set(), f"parameters never read: {sorted(leaves - seen)}"
    assert seen - leaves == set()


# =============================================================================================
# Parameter PERTURBATION against the real rules file: coverage above proves every entry is
# READ; this proves it is USED. Each entry is nudged on a copy (every other entry unchanged);
# the inputs are built from the UNPERTURBED values, sitting on the rules' edges, and at least
# one recorded decision output must change (a changed verdict, count, band, or a raise). The
# settings readers (split_settings, b2_settings, ...) are not outputs: an entry counts only
# where a decision function or an existing driver step consumes it.
# =============================================================================================
from scripts.analysis.nmn import run_wakeup as rw  # noqa: E402
from scripts.analysis.nmn import driver_io as dio  # noqa: E402
from tests.analysis import nmn_synthetic as syn  # noqa: E402

# Entries read today whose consumer is a driver not written yet. Each must NOT change any
# output (checked, so the list cannot go stale): when the driver lands, move the entry out.
# (gates.G5.stage, common.split.test_frac, common.survival.window_episodes and
# A3.survival_stage_by_status.{evidence,interim} left this list with the Stage 3 drivers: their
# steps driver_io.survival_block and driver_io.make_splits are exercised in _decisions.)
READ_NOT_YET_USED = {
    "B2.f": "run_wakeup GPU measures (headline wake point), not implemented yet",
    "B2.literal_f": "run_wakeup GPU measures (literal 50 % of final, beside), not implemented yet",
    "B2.lag_coincident_max_intervals": "run_wakeup lag reading (wakeup.lag), after the GPU measures",
}
_ALTERNATIVE = {"delta_episode_number": "window_n", "fraction_of_rise": "fraction_of_final"}


def _nudges(v):
    """Candidate perturbations of one entry (a leaf passes if ANY changes an output)."""
    if isinstance(v, bool):
        return [not v]
    if isinstance(v, int):
        return [v + 1, v - 1, v * 2]
    if isinstance(v, float):
        return [v * 1.1, v * 0.9, v * 2, v / 2]
    if isinstance(v, str):
        return [_ALTERNATIVE[v]] if v in _ALTERNATIVE else [v + "_perturbed"]
    if isinstance(v, list):
        out = [v[::-1], v[:-1]]
        if v and all(isinstance(e, (int, float)) and not isinstance(e, bool) for e in v):
            out += [[e * 1.1 if i == j else e for i, e in enumerate(v)] for j in range(len(v))]
            out += [[e * 0.9 if i == j else e for i, e in enumerate(v)] for j in range(len(v))]
        return [o for o in out if o != v]
    raise TypeError(f"no perturbation for {v!r}")


def _set(d, dotted, value):
    import copy
    d = copy.deepcopy(d)
    node = d
    parts = dotted.split(".")
    for p in parts[:-1]:
        node = node[p]
    node[parts[-1]] = value
    return d


def _norm(x):
    if isinstance(x, dict):
        return {k: _norm(v) for k, v in sorted(x.items()) if k != "stage_index"}
    if isinstance(x, (list, tuple)):
        return [_norm(v) for v in x]
    if isinstance(x, (np.floating, float)):
        return repr(float(x))
    if isinstance(x, np.ndarray):
        return [_norm(v) for v in x.tolist()]
    if isinstance(x, np.integer):
        return int(x)
    if hasattr(x, "as_dict"):
        return _norm(x.as_dict())
    return x


def _survival_rows(base):
    """Synthetic WandB episode rows for 16 checkpoints of 100,000 episodes, logged every 4,000
    episodes: survival rises then levels off, with a two-checkpoint excursion early (so
    `sustain` matters), rows at exactly the registered _window_n minimum (so min_window_n
    matters) and window sizes unlike the 4,000-episode step (so the row weighting matters)."""
    wmin = float(base["common"]["survival"]["min_window_n"])
    rows, rng = [], np.random.default_rng(11)
    for i in range(400):
        e = 4000.0 * (i + 1)
        c = e / 100000.0
        level = 100 + 80 * (1 - np.exp(-c / 3.0)) + (60 if 2.0 < c <= 4.0 else 0.0)
        wn = wmin if i % 5 == 1 else (4000.0 if i == 0 else 2500.0 + 50 * (i % 7))
        rows.append({"Episode/Number": e, "Episode/_window_n": wn,
                     "Episode/Steps": float(level + rng.normal(0, 6.0) + (25 if i % 5 == 1 else 0))})
    return rows, np.arange(1, 17, dtype=float) * 100000.0


def _decisions(Pr, base):
    """Every decision function and existing driver step, with inputs built from `base` on the
    rules' edges and the (possibly perturbed) parameters `Pr`. Returns the recorded outputs; a
    raise is recorded as its type."""
    g, c = base["gates"], base["common"]
    n = 1_000_000
    tie = int(round(g["G1"]["near_tie_fraction_max"] * n))
    calls = {
        "G1": lambda: dr.gate_G1(_g1(n, 0, tie, margin=g["G1"]["near_tie_logit_margin"]), Pr),
        "G2": lambda: dr.gate_G2({"x": {"max_abs_dev": g["G2"]["reconstruction_rel_tol"],
                                        "max_abs_ref": 0.5}}, Pr),
        "G3": lambda: dr.gate_G3({"alignment": _g1(n, 0, tie, margin=g["G1"]["near_tie_logit_margin"]),
                                  "shift_control_agreement": 0.9}, Pr),
        "G4": lambda: dr.gate_G4({"input_satiation_r2": g["G4"]["input_satiation_r2_min"],
                                  "shuffled_r2": {"q": g["G4"]["shuffled_r2_max"]},
                                  "groups_disjoint": True}, Pr),
        "G5": lambda: dr.gate_G5(_runs([g["G5"]["stage1_survival_min_steps"], 210, 205],
                                       [100, 208, 204],
                                       ord_b=[g["G5"]["stage1_food_bites_min"], 5.0, 5.0]), Pr),
        "G6": lambda: dr.gate_G6({"bootstrap_n": g["G6"]["bootstrap_n_min"],
                                  "test_groups": {"q": [g["G6"]["test_fold_groups_min"]] * c["split"]["n_repeats"]}}, Pr),
    }
    rng = np.random.default_rng(0)
    pairs = {s: {f"{s}{i}": {"point": 0.8, "draws": rng.normal(0.8, 0.01, 200)} for i in range(k)}
             for s, k in (("OO", 3), ("MM", 3), ("MO_diff", 6), ("MO_same", 3), ("UNTRAINED", 3))}
    calls["summaries"] = lambda: dr.summarise_pairs(pairs, Pr)
    two_below = _stat([0.79, 0.78, 0.85, 0.86, 0.84, 0.83], (0.81, 0.85))
    calls["A1"] = lambda: dr.evaluate_A1(_a1([two_below] * 2 + [UND_S] * 3), Pr, policy=EVID,
                                         verdict_layers=LAYERS, gates=ALL_PASS, yardstick_complete=True)
    m = base["A2"]["beats_clock_margin_r2"]
    edge = {"excess": m, "excess_q_lo": 0.01}
    mod2 = [_ag(0.51, edge), _ag(0.53, edge), _ag(0.52, NOBEAT)]
    lays = [DIFF_L] * base["A2"]["differs_min_layers"] + [{"ordinary": ORD, "modulated": mod2}] + \
        [MATCH_L] * (5 - base["A2"]["differs_min_layers"] - 1)
    calls["A2"] = lambda: dr.evaluate_A2(_a2(_allq(lays)), Pr, policy=EVID, quantities=QUANTITIES,
                                         verdict_layers=LAYERS, gates=ALL_PASS, yardstick_complete=True)
    floor, mult = c["survival"]["se_floor_steps"], c["survival"]["se_multiplier"]
    calls["survival"] = lambda: dr.survival_difference(
        {"ordinary": [200, 200.5, 201], "modulated": [200.5 + mult * floor, 201 + mult * floor,
                                                      201.5 + mult * floor]}, Pr)
    k = base["study_reading"]["min_layers"]
    a3_in = {L: {"a1_verdict": ("same" if i < k else "different"), **E_NO} for i, L in enumerate(LAYERS)}
    calls["A3"] = lambda: dr.evaluate_A3(a3_in, Pr, policy=EVID, verdict_layers=LAYERS, gates=ALL_PASS,
                                         yardstick_complete=True, precondition_shared_start=True,
                                         survival=SURV_SAME)
    seq = list(base["A4"]["stage_sequence"])
    base_layout = dr.a4_layout(base)
    calls["A4"] = lambda: dr.evaluate_A4(
        {"layout": base_layout, "layers": {L: {"movement": {"ordinary": [0.1, 0.2, -0.1],
                                                             "modulated": [0.1, 0.2, -0.1]},
                                               "co_movement": TOGETHER,
                                               "stage_end_a1": {c_: "same" for c_ in seq}}
                                           for L in LAYERS}},
        Pr, policy=EVID, verdict_layers=LAYERS, gates=ALL_PASS, yardstick_complete=True)
    calls["B2"] = lambda: dr.evaluate_B2(_b(late=12, coin=4), ["late"] * 3, Pr, policy=B2POL)
    # Stage 3 driver steps (run_similarity / run_decoding): the survival and G5 inputs of A3,
    # for both statuses that read a survival stage, and the probe split's held-out groups
    runs = syn.scanned_runs()
    calls["survival_block_evidence"] = lambda: dio.survival_block(runs, Pr, "evidence")
    calls["survival_block_interim"] = lambda: dio.survival_block(runs, Pr, "interim")
    grp = np.repeat(np.arange(400), 3)
    calls["probe_split"] = lambda: dio.split_counts(dio.make_splits(grp, Pr, 0), grp)
    rows, x = _survival_rows(base)
    calls["plateau"] = lambda: rw.plateau_crossing("synthetic", rows, x, dr.b2_settings(Pr),
                                                   dr.survival_settings(Pr))
    out = {}
    for name, f in calls.items():
        try:
            out[name] = _norm(f())
        except (ValueError, TypeError, KeyError, ZeroDivisionError, AssertionError) as e:
            out[name] = f"raises {type(e).__name__}"
    return out


def test_every_parameter_is_used_not_merely_read():
    real = _real_pinned().parameters
    base_out = _decisions(real, real)
    assert not any(isinstance(v, str) and v.startswith("raises") for v in base_out.values()), \
        f"the unperturbed exercise must not raise: {base_out}"
    unused, stale = [], []
    for leaf in sorted(_leaves(real)):
        v = rules_pin.param(real, leaf)
        changed = [nv for nv in _nudges(v) if _decisions(_set(real, leaf, nv), real) != base_out]
        if leaf in READ_NOT_YET_USED:
            if changed:
                stale.append(leaf)
        elif not changed:
            unused.append(leaf)
    assert not unused, f"parameters read but never change an output: {unused}"
    assert not stale, (f"now used, remove from READ_NOT_YET_USED: {stale}")
    assert set(READ_NOT_YET_USED) <= _leaves(real)


def test_b2_settings_are_the_wakeup_keywords():
    s = dr.b2_settings(_real_pinned().parameters)
    kw = {k: s[k] for k in ("f", "sustain", "final_k", "noise_k", "min_noise_points",
                            "noise_window_divisor", "noise_window_max_fraction")}
    x = np.arange(51, dtype=float)
    m = 1 / (1 + np.exp(-(x - 20) / 1.5))
    assert 19 <= wakeup.t_cross(x, m, mode=s["threshold_mode_headline"], anchored=True,
                                label="synthetic / logistic", **kw).t <= 21


# =============================================================================================
# Plain-markdown rendering of every table (python tests/analysis/test_nmn_decision_rules.py)
# =============================================================================================
TABLES = [
    ("1. Gates G1-G4 (pass = True)", GATE_ROWS), ("1b. Gate G5 (competence)", G5_ROWS),
    ("1c. Gate G6 (sizes)", G6_ROWS),
    ("2. A1 one statistic, one layer (band [0.80, 0.90], untrained [0.20, 0.40])", A1_STAT_ROWS),
    ("3. A1 layer verdict (predictivity, CKA)", A1_LAYER_ROWS),
    ("4. A1 across the five layers", A1_STUDY_ROWS),
    ("5. A2 one quantity, one layer (ordinary R^2 0.50/0.52/0.54)", A2_LAYER_ROWS),
    ("6. A2 profile and study", A2_PROFILE_ROWS),
    ("7. A3 pattern per layer (U = 0.90)", A3_ROWS), ("7b. A3 study reading", A3_STUDY_ROWS),
    ("7c. A3 under a blocking gate", A3_GATE_ROWS),
    ("8. Survival difference (A3 pattern c)", SURVIVAL_ROWS),
    ("9. A4 across worlds", A4_ROWS), ("10. B2 across 16 worlds", B2_ROWS),
    ("11. A missing (non-finite) summary", NONFINITE_ROWS),
]


def _fmt(x):
    s = repr(x)
    return s if len(s) <= 160 else s[:157] + "..."


if __name__ == "__main__":
    n = 0
    for title, rows in TABLES:
        print(f"\n### {title}\n\n| # | case | why | input | expected |\n|---|---|---|---|---|")
        for i, r in enumerate(rows, 1):
            inp = "(summary objects; see file)" if title.startswith(("4.", "6.")) else _fmt(r["input"])
            print(f"| {i} | {r['case']} | {r.get('why', '')} | `{inp}` | **{r['expect']}** |")
            n += 1
    print(f"\n{n} rows. Parameters: FIXTURE_P (test fixture, not the study's rule).")
