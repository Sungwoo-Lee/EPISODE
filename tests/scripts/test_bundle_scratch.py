"""Tests for scripts/eval/dwell_sweep/bundle_scratch.py (plan SWEEP_EPISODE_BUNDLES_AND_ON_NODE_MEASURES.md,
F7/F10): pack --into + verify + gate (Gate G1 logic) on a synthetic root, the gate's refusal to pass
vacuously, and the exclusion rules E1 (live), E2 (unregistered reader), E3 (lock), E4 (hold).
Temp dirs only; nothing under results/ is touched.
"""
import json
import os
import shutil
import socket
import sys
import time
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(_REPO / "scripts" / "eval" / "dwell_sweep"))

import bundle_scratch as BS  # noqa: E402
import run_sweep as RS  # noqa: E402
from tests.scripts.test_episode_bundle import _write_cell  # noqa: E402

NEP = 4


def _old_root(tmp_path, labels=("labA",), conds=("avoid_x", "avoid_y"), steps=(100, 200)):
    """A legacy root: folder cells + per-scene CSVs written by the folder scoring path, + done_ marker."""
    root = tmp_path / "root"
    scr = root / "_scratch"
    for li, lab in enumerate(labels):
        for ci, c in enumerate(conds):
            for si, s in enumerate(steps):
                _write_cell(scr / lab / c / str(s), "rppo", n_ep=NEP, seed=li * 100 + ci * 10 + si)
    groups = [{"run_label": lab, "cond": c, "out_csv": root / lab / f"{c}.csv"} for lab in labels for c in conds]
    RS.aggregate_from_bundles(groups, scr, n_workers=1)
    m = scr / "_run_markers"
    m.mkdir()
    (m / "npar_105").write_text("x")
    time.sleep(0.01)
    (m / "done_105").write_text("")
    for g in groups:                                   # CSVs newer than done_ (collated)
        os.utime(g["out_csv"])
    return root


def test_pack_into_verify_gate_pass(tmp_path):
    root = _old_root(tmp_path)
    before = {p: p.stat().st_mtime_ns for p in root.rglob("*")}
    gate = tmp_path / "gate"
    res = BS.cmd_pack(root, into=gate, workers=1)
    assert [r[1] for r in res] == ["packed"] * 4
    assert {p: p.stat().st_mtime_ns for p in root.rglob("*")} == before       # held root only read
    assert all(r[2] == "ok" for r in BS.cmd_verify(root, into=gate, workers=1))
    s = BS.cmd_gate(root, into=gate, episodes=NEP, workers=1)
    assert s["all_ok"] and s["cells"] == 4 and s["rows_identical"] == 4 and s["csv_byte_identical"] == 2
    again = BS.cmd_pack(root, into=gate, workers=1)
    assert [r[1] for r in again] == ["exists-ok"] * 4


def test_subset_gate_newest(tmp_path):
    root = _old_root(tmp_path, steps=(100, 200, 1000))
    gate = tmp_path / "gate"
    res = BS.cmd_pack(root, into=gate, workers=1, newest=2)
    assert sorted(Path(r[0]).name for r in res) == ["1000", "1000", "200", "200"]   # numeric, not string order
    assert all(r[2] == "ok" for r in BS.cmd_verify(root, into=gate, workers=1, newest=2))
    s = BS.cmd_gate(root, into=gate, episodes=NEP, workers=1, newest=2)
    assert s["all_ok"] and s["rows_identical"] == 4 and s["csv_byte_identical"] == 2
    csvp = root / "labA" / "avoid_x.csv"
    lines = csvp.read_text().splitlines()
    lines[-1] = lines[-1].rsplit(",", 1)[0] + ",9.9999"           # newest row changed -> must fail
    csvp.write_text("\n".join(lines) + "\n")
    assert not BS.cmd_gate(root, into=gate, episodes=NEP, workers=1, newest=2)["all_ok"]


def test_gate_fails_on_empty_archives(tmp_path):
    """Review M2: archives holding no recordings must FAIL the gate, not pass vacuously."""
    root = _old_root(tmp_path, conds=("avoid_x",), steps=(100,))
    gate = tmp_path / "gate"
    empty = tmp_path / "empty_cell"
    (empty / "run_tag").mkdir(parents=True)
    (empty / "run_tag" / "metadata.json").write_text("{}")
    z = gate / "_scratch" / "labA" / "avoid_x" / "100.zip"
    z.parent.mkdir(parents=True)
    BS.EB.pack(empty, z)
    s = BS.cmd_gate(root, into=gate, episodes=NEP, workers=1)
    assert not s["all_ok"]


def test_gate_fails_on_changed_row_and_on_missing_archive(tmp_path):
    root = _old_root(tmp_path)
    gate = tmp_path / "gate"
    BS.cmd_pack(root, into=gate, workers=1)
    csvp = root / "labA" / "avoid_x.csv"
    txt = csvp.read_text().splitlines()
    parts = txt[1].split(",")
    parts[2] = "9.9999"
    txt[1] = ",".join(parts)
    csvp.write_text("\n".join(txt) + "\n")
    assert not BS.cmd_gate(root, into=gate, episodes=NEP, workers=1)["all_ok"]
    shutil.rmtree(gate / "_scratch" / "labA" / "avoid_y")
    s = BS.cmd_gate(root, into=gate, episodes=NEP, workers=1)
    assert not s["all_ok"]


def test_gate_wrong_episode_count_fails(tmp_path):
    root = _old_root(tmp_path, conds=("avoid_x",), steps=(100,))
    gate = tmp_path / "gate"
    BS.cmd_pack(root, into=gate, workers=1)
    assert not BS.cmd_gate(root, into=gate, episodes=30, workers=1)["all_ok"]


# ---------------------------------------------------------------------------------- E1 ----
def test_e1_live_markers(tmp_path):
    root = _old_root(tmp_path)
    assert BS.live_reasons(root, ps_lines=[]) == []
    m = root / "_scratch" / "_run_markers"
    (m / "started_110").write_text("x")
    assert any("node 110" in w for w in BS.live_reasons(root, ps_lines=[]))
    (m / "started_110").unlink()
    (m / "alive_105").write_text("1 2")
    assert any("alive_" in w for w in BS.live_reasons(root, ps_lines=[]))
    (m / "alive_105").unlink()
    (m / "collate_L1.started").write_text("{}")
    assert any("collation L1" in w for w in BS.live_reasons(root, ps_lines=[]))
    (m / "collate_L1.done").write_text("")
    assert BS.live_reasons(root, ps_lines=[]) == []
    with pytest.raises(SystemExit, match="E1 live"):
        (m / "started_111").write_text("x")
        BS.cmd_pack(root, workers=1)


def test_e1_possibly_collating(tmp_path):
    root = _old_root(tmp_path)
    m = root / "_scratch" / "_run_markers"
    old = time.time() - 100
    for p in root.glob("*/*.csv"):
        os.utime(p, (old, old))
    os.utime(m / "npar_105", (old - 10, old - 10))
    os.utime(m / "done_105")
    assert any("possibly collating" in w for w in BS.live_reasons(root, ps_lines=[]))


def test_e1_process_naming_root(tmp_path):
    root = _old_root(tmp_path)
    ps = [f"4242 bash sweep_worker.sh {root}/_scratch/_worklists/worklist_105.txt 105 18 30 L1 /repo"]
    assert any("process names the root" in w for w in BS.live_reasons(root, ps_lines=ps))
    assert BS.live_reasons(root, ps_lines=["4243 python something_else.py " + str(root)]) == []


# ---------------------------------------------------------------------------------- E2 ----
def test_e2_unregistered_reader_blocks(tmp_path):
    fake = tmp_path / "repo"
    (fake / "scripts" / "x").mkdir(parents=True)
    (fake / "src").mkdir()
    (fake / "tests").mkdir()
    (fake / "scripts" / "x" / "new_reader.py").write_text("glob('**/episode_*.rec.gz')\n")
    (fake / "scripts" / "x" / "harmless.py").write_text("print(1)\n")
    (fake / "src" / "utils").mkdir()
    (fake / "src" / "utils" / "eval_recording.py").write_text("def load_episode(p): ...\n")   # NON_READER
    assert BS.unswitched_readers(repo=fake) == ["scripts/x/new_reader.py"]


def test_e2_repo_has_no_unregistered_reader():
    """Every current file that mentions sweep episodes is classified (switched or non-reader)."""
    assert BS.unswitched_readers() == []


def test_non_readers_disjoint_from_switched():
    assert not set(BS.NON_READERS) & set(BS.SWITCHED_READERS["S"])
    assert all(reason.strip() for reason in BS.NON_READERS.values())


# ---------------------------------------------------------------------------------- E3 ----
def test_e3_lock_stale_rule(tmp_path):
    root = _old_root(tmp_path)
    lock = root / "_scratch" / "_bundle.lock"
    with BS.Lock(root):
        assert lock.exists() and not BS.lock_is_stale(lock)
        with pytest.raises(FileExistsError):
            BS.Lock(root).__enter__()
    assert not lock.exists()
    lock.write_text(json.dumps({"host": socket.gethostname(), "pid": 2 ** 22 + 12345, "start": 0}))
    assert BS.lock_is_stale(lock)                                   # same host, pid dead
    lock.write_text(json.dumps({"host": "elsewhere", "pid": 1, "start": 0}))
    assert not BS.lock_is_stale(lock)
    old = time.time() - BS.LOCK_STALE_S - 10
    os.utime(lock, (old, old))
    assert BS.lock_is_stale(lock)


def test_run_sweep_refuses_locked_root(tmp_path):
    root = _old_root(tmp_path)
    lock = root / "_scratch" / "_bundle.lock"
    lock.write_text(json.dumps({"host": "elsewhere", "pid": 1, "start": time.time()}))
    with pytest.raises(SystemExit):
        RS.check_lock(root / "_scratch")


# ---------------------------------------------------------------------------------- E4 ----
def test_e4_unresolved_label_is_held_and_not_packed(tmp_path):
    root = _old_root(tmp_path)
    held, _ = BS.held_labels(root)
    assert held == {"labA"}                                         # no provenance/worklist: fail closed
    assert BS.cmd_pack(root, workers=1) == []                       # nothing packed in place


def test_e4_resolution_from_provenance(tmp_path):
    root = _old_root(tmp_path, labels=("labA", "labB"))
    p = root / "_provenance" / "20261011_000000"
    p.mkdir(parents=True)
    p.joinpath("provenance.json").write_text(json.dumps({"runs": [
        {"label": "labA", "path": "results/JAX_RecurrentPPO/" + BS.SESSION_HOLDS["runs"][0]},
        {"label": "labB", "path": "results/JAX_RecurrentPPO/20260101-000000_some_free_run"}]}))
    held, _ = BS.held_labels(root)
    assert held == {"labA"}
    res = BS.cmd_pack(root, workers=1)
    assert sorted(Path(r[0]).parent.parent.name for r in res) == ["labB"] * 4


def test_e4_held_root_name(tmp_path):
    root = tmp_path / "metrics_history_rppo_case_l05_s42"
    _write_cell(root / "_scratch" / "labZ" / "avoid_x" / "100", "rppo", n_ep=2)
    held, why = BS.held_labels(root)
    assert held == {"labZ"} and why == "held root"
