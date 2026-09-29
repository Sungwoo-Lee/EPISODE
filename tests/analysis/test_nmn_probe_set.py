"""Tests for the Stage 2 probe builder and the rules pin (algorithmic-null tooling plan §4, §E).

probe_set: the row index is the single object every array is gathered through, t runs 0..T-1
per episode, the next action is the stored action one row later, the group count is printed
and gate G6's floor raises, and a saved probe is refused if its row index was altered.
rules_pin: the whole-file sha256 pin raises on a mismatch, and the evidence status is read
from the rules (the pilot allows no verdict word; `b2_wakeup` is a valid status — plan
Revision 3, T3). Uses the real level-05 w0000 stores when present (gitignored data).
"""
import json
import os
import sys
from pathlib import Path

import numpy as np
import pytest
import yaml

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
os.environ.setdefault("JAX_PLATFORMS", "cpu")

STORES = [
    _REPO / "results/trajectories_l05body/20260927-053057_rppo_l05body_w0000_t1none_s42/10000046/a1179698aa",
    _REPO / "results/trajectories_l05body/20260927-053059_rppo_l05body_w0000_t16quad_s42/10000021/2ef4474a8f",
]
PILOT = _REPO / "docs/experiments/active/modulator_clues/algorithmic_null_pilot.yaml"
FIX = dict(test_frac=0.2, min_test_groups=5)       # test fixture values, not the rules'


@pytest.fixture(scope="module")
def probe():
    if not all((s / "_manifest.json").exists() for s in STORES):
        pytest.skip("level-05 stores not present (gitignored)")
    from scripts.analysis.nmn import probe_set
    return probe_set.build("t", [str(s) for s in STORES], 30, 4, 7, **FIX)


def test_row_index_invariants(probe):
    import pyarrow.parquet as pq
    assert np.all(np.diff(probe.rows) > 0)
    # t is 0..T-1 contiguous in every episode's block of decision rows
    for e in range(probe.ep_T.size):
        o, T = probe.ep_offset[e], probe.ep_T[e]
        assert np.array_equal(probe.t_all[o:o + T], np.arange(T))
        # action_next[t] is action_cur[t+1] inside the episode (the stored row t+1)
        assert np.array_equal(probe.action_next_all[o:o + T - 1], probe.action_cur_all[o + 1:o + T])
        assert probe.action_cur_all[o] == -1
    # obs at the sampled rows equals the stored obs_noised read independently
    st = pq.read_table(STORES[0] / "steps_00000.parquet",
                       columns=["episode_seed", "t", "obs_noised", "action", "satiation"]).to_pandas()
    sid0 = probe.row_store == 0
    for r, sd, t in list(zip(probe.rows[sid0], probe.row_seed[sid0], probe.row_t[sid0]))[:40]:
        row = st[(st.episode_seed == sd) & (st.t == t)].iloc[0]
        nxt = st[(st.episode_seed == sd) & (st.t == t + 1)].iloc[0]
        assert np.array_equal(np.asarray(row.obs_noised, np.float32), probe.obs_all[r])
        assert probe.action_next_all[r] == nxt.action
    k = np.flatnonzero(sid0)[:40]
    assert np.allclose(probe.targets["satiation"][k],
                       [st[(st.episode_seed == sd) & (st.t == t)].satiation.iloc[0]
                        for sd, t in zip(probe.row_seed[k], probe.row_t[k])])
    T = probe.ep_T[probe.row_episode]
    assert np.array_equal(probe.targets["steps_remaining"], T - probe.row_t)
    v = probe.targets["predator_valid"]
    assert np.all(np.isnan(probe.targets["nearest_predator_manhattan"][~v]))
    assert np.all(probe.targets["nearest_predator_manhattan"][v] >= 0)


def test_group_count_and_g6_floor(probe):
    from scripts.analysis.nmn import probe_set
    # both stores share seed_base: 30 + 30 episodes are 30 groups, not 60
    assert probe.counts["distinct_episode_seed_groups"] == 30
    with pytest.raises(ValueError, match="gate G6"):
        probe_set.build("t", [str(s) for s in STORES], 10, 4, 7, test_frac=0.2, min_test_groups=500)


def test_saved_probe_round_trip_and_tamper(probe, tmp_path):
    from scripts.analysis.nmn import probe_set
    probe_set.save(probe, tmp_path)
    p2 = probe_set.load(tmp_path, "t")
    assert p2.row_sha256 == probe.row_sha256
    meta = json.loads((tmp_path / "probe_t.json").read_text())
    meta["row_index_sha256"] = "0" * 64
    (tmp_path / "probe_t.json").write_text(json.dumps(meta))
    with pytest.raises(ValueError, match="row index sha256"):
        probe_set.load(tmp_path, "t")


def test_rules_pin_and_policy(tmp_path):
    from scripts.analysis.nmn import rules_pin
    man = yaml.safe_load(PILOT.read_text())
    pinned = rules_pin.load(man)                 # the pilot manifest's pin matches the file
    assert pinned.sha256 == man["decision_rules"]["sha256"]
    assert rules_pin.evidence_policy(pinned, "pilot")["verdict_words_allowed"] is False
    assert rules_pin.evidence_policy(pinned, "b2_wakeup")["verdict_words_allowed"] is True
    with pytest.raises(ValueError, match="not one the rules define"):
        rules_pin.evidence_policy(pinned, "exploratory")
    assert rules_pin.param(pinned.parameters, "gates.G1.near_tie_logit_margin") > 0
    with pytest.raises(ValueError, match="not registered"):
        rules_pin.param(pinned.parameters, "gates.G1.no_such_key")
    bad = dict(man, decision_rules={"file": man["decision_rules"]["file"], "sha256": "0" * 64})
    with pytest.raises(ValueError, match="differs from the manifest's pin"):
        rules_pin.load(bad)
