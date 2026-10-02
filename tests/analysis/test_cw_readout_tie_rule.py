"""Recovery-tie rule of scripts/analysis/studies/continual_worlds/pilot_readout.py.

CONTINUAL_WORLDS.md 3.7.7 (a) (also used by MAY_DOUBLE_RETURN_REPLICATION.md 5.3 H-rec): "If both agents
recover in the same logged row (episodes are resolved only to the 4,000-episode logging interval), that
reading is a tie; a vote with any tied reading is 'not counted (tie)'." A tie is the SAME LOGGED ROW, not
exact equality of the episode counts (two runs' logging grids differ by a few episodes to ~130).
Synthetic rows only; no WandB binary is read.
"""
import importlib.util
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_spec = importlib.util.spec_from_file_location(
    "pilot_readout", os.path.join(ROOT, "scripts", "analysis", "studies", "continual_worlds", "pilot_readout.py"))
pr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pr)


def _series(start, offset, steps):
    """Rows every 4,000 episodes from `start + offset`, survival `steps[i]` in row i."""
    rows = [{"Episode/Number": start + offset + 4000 * (i + 1), "Episode/_window_n": 5000.0, "Episode/Steps": s}
            for i, s in enumerate(steps)]
    return pr.Series(rows, start)


def _prog(ser):
    return {"ep": ser.last - ser.start, "env_steps": float(ser.cum_steps[-1])}


def test_same_logged_row_is_a_tie_even_if_counts_differ():
    # both agents already at the reference: recovery in the first row with a full 20k window (row 4),
    # ordinary's grid 8 episodes after the switch, modulated's 62 -> counts 20,008 vs 20,062
    so, sm = _series(1e6, 8, [100.0] * 10), _series(1e6, 62, [100.0] * 10)
    ro, rm = pr.recovery(so, 100.0, None), pr.recovery(sm, 100.0, None)
    assert ro["ep"] == 20008 and rm["ep"] == 20062
    for unit in ("ep", "env_steps"):
        sign, diff = pr._rec_sign(ro, rm, unit, _prog(so), _prog(sm))
        assert sign == "tie", unit
        assert diff is not None and diff > 0      # the raw difference is still reported
    assert ro["row"] == rm["row"] == 4


def test_different_rows_are_not_a_tie():
    so = _series(1e6, 8, [100.0] * 10)
    sm = _series(1e6, 8, [10.0] * 5 + [100.0] * 10)     # modulated needs more rows
    ro, rm = pr.recovery(so, 100.0, None), pr.recovery(sm, 100.0, None)
    assert ro["row"] != rm["row"]
    assert pr._rec_sign(ro, rm, "ep", _prog(so), _prog(sm))[0] == "ordinary"


def test_vote_with_a_tied_reading_is_not_counted_as_tie():
    signs = {"own_ep": "tie", "own_steps": "tie", "common_ep": "ordinary", "common_steps": "ordinary"}
    v = pr._vote(signs, [("own_ep", "common_ep"), ("own_steps", "common_steps")],
                 [("own_ep", "own_steps"), ("common_ep", "common_steps")])
    assert v["vote"] == "not counted"
    assert v["reason"].startswith("tie:")
