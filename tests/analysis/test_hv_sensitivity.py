"""Study S6 accumulators and the S3 aimed-response classifier / thresholds (hand-built rows)."""
import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(HERE, "..", "..", "scripts", "analysis")
sys.path.insert(0, os.path.join(A, "core"))
sys.path.insert(0, A)
_cwd = os.getcwd()
sys.path.insert(0, os.path.join(A, "studies", "sensor_ladder"))
import collect_arm_data as CAD  # noqa: E402  (chdirs to the repo root on import)
os.chdir(_cwd)
import aimed_response as AIM  # noqa: E402
import env as E  # noqa: E402


def test_accumulate_sensitivity_known_answer():
    S = CAD.new_sensitivity()
    # rows: (bush y, rabbit distance, predator distance, start-injury quarter, current quarter, has rabbit)
    rows = [(0, 0, np.inf, 0, 0, True),    # rabbit on the agent's square: counted, not in rd_no0
            (1, 1, 2, 3, 3, True),         # predator at 2 -> not predator-free
            (1, 1, 3, 3, 2, True),         # predator at 3 -> predator-free
            (0, 7, np.inf, 1, 1, True),    # no live predator (inf) -> predator-free
            (1, 1, np.inf, 0, 0, False)]   # no rabbit in the episode -> ignored entirely
    y, dr, dp, ib, cb, hr = (np.array(c) for c in zip(*rows))
    CAD.accumulate_sensitivity(S, y.astype(float), dr.astype(float), dp.astype(float),
                               ib.astype(int), cb.astype(int), hr.astype(bool))
    assert S["rab_on_cell"].tolist() == [1, 0, 0, 0]
    assert S["rab_steps"].tolist() == [1, 1, 0, 2]
    assert S["rd_no0_tot"].sum() == 3 and S["rd_no0_tot"][0, 0] == 0        # distance-0 row absent
    assert S["rd_no0_tot"][0, 3] == 2 and S["rd_no0_bush"][0, 3] == 2
    assert S["rdpf_tot"][0, 3] == 1                                         # only the dpred=3 row
    assert S["rdpf_tot"][6, 1] == 1                                         # the inf row
    assert S["rdpf_tot"][0, 0] == 1                                         # distance 0 clipped into bin 0
    assert S["rdcpf_tot"][0, 2] == 1 and S["rdcpf_bush"][0, 2] == 1         # current quarter used
    assert S["rdpf_tot"].sum() == 3


def test_aimed_state_classifier_gives_predator_precedence():
    pn = np.array([True, True, False, False])
    rn = np.array([True, False, True, False])
    assert AIM.classify_state(pn, rn & ~pn).tolist() == [1, 1, 2, 0]


@pytest.mark.parametrize("world, want", [
    ((([0, .7, .5, 0, 0], [0, .5, .7, 0, 0], [0, .3, .3, 0, 0])), 0.3),
    ((([0, .7, 0, 0, 0], [0, .5, 0, 0, 0], [0, .3, 0, 0, 0])), 0.9),
    ((([0, .67, .67, 0, 0], [0, .53, .53, 0, 0], [0, .3, .3, 0, 0])), 1.6286)])
def test_predator_like_threshold_at_two_thirds_of_a_nat(world, want):
    p, r, sd = world
    spec = E.scent_spec({"environment": {"entities": [
        {"class": "predator", "properties": p, "properties_std": sd},
        {"class": "neutral", "properties": r, "properties_std": sd}]}})
    got = AIM.statistic_threshold(spec, AIM.PREDATOR_LIKE_AT_NATS)
    assert round(got, 4) == want
    if want == 0.3:
        assert got == 0.3                        # exactly a01's threshold, not 0.30000000000000004
    assert AIM.statistic_threshold(spec, 0.0) == round(spec.midpoint, 10)
