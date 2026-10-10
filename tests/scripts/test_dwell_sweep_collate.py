"""Tests for the on-node sweep pipeline (plan SWEEP_EPISODE_BUNDLES_AND_ON_NODE_MEASURES.md, F2-F5/F10):
cell_measures, finish_cells.py, run_sweep.py collation / liveness / status, and the COPIED worker
end to end (with a stub test program), all in pytest temp dirs. No checkpoints, no NAS, no nodes.
"""
import csv
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

import numpy as np
import pytest

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(_REPO / "scripts" / "behavior_measures"))
sys.path.insert(0, str(_REPO / "scripts" / "eval" / "dwell_sweep"))

import src.utils.episode_bundle as EB  # noqa: E402
import run_sweep as RS  # noqa: E402
import finish_cells as FC  # noqa: E402
import cell_measures as CM  # noqa: E402
from tests.scripts.test_episode_bundle import _write_cell, STEP  # noqa: E402

PY = "/home/vncuser/miniconda3/envs/grid_world_pain/bin/python"


# ------------------------------------------------------------------------------- helpers ----
def _scratch_with_cells(base, labels=("labA",), conds=("avoid_x", "avoid_y"), steps=(100, 200), n_ep=4):
    scr = base / "out" / "_scratch"
    for li, lab in enumerate(labels):
        for ci, cond in enumerate(conds):
            for si, s in enumerate(steps):
                _write_cell(scr / lab / cond / str(s), "rppo", n_ep=n_ep, seed=100 * li + 10 * ci + si)
    return scr


def _finish(tmp_path, scr, launch, node, cells_, n_ep, piece_name="p0"):
    """Simulate a node: copy each legacy cell folder to a local stage, run finish_cells on it."""
    pairs = []
    for i, (lab, cond, s) in enumerate(cells_):
        stage = tmp_path / f"stage_{launch}_{node}_{piece_name}" / str(i)
        shutil.copytree(scr / lab / cond / str(s), stage)
        pairs.append(f"{stage}={scr / lab / cond / str(s)}")
    rc = FC.main(["--repo-root", str(_REPO), "--pairs", *pairs,
                  "--rows-piece", str(scr / "_rows" / launch / node / f"{piece_name}.csv"),
                  "--episodes", str(n_ep), "--log", str(tmp_path / "finish.log")])
    return rc


def _groups(scr, labels, conds):
    out = scr.parent
    return [{"run_label": lab, "cond": c, "out_csv": out / lab / f"{c}.csv"} for lab in labels for c in conds]


# --------------------------------------------------------------------------- cell_measures ----
@pytest.mark.parametrize("layout", ["rppo", "dreamer"])
def test_measure_cell_dir_equals_zip(tmp_path, layout):
    cell = _write_cell(tmp_path / "c" / str(STEP), layout, n_ep=6)
    z = tmp_path / "c" / f"{STEP}.zip"
    EB.pack(cell, z)
    a, b = CM.measure_cell(cell), CM.measure_cell(z)
    assert a == b and a[0] == STEP
    assert RS._measure_cell(cell) == a                      # the kept run_sweep entry point
    assert CM.measure_cell_n(z)[2] == 6


def test_cell_row_is_the_only_nanmean():
    # plot_summary.py averages for its figures, not for the CSV rows
    hits = [p.name for p in (_REPO / "scripts/eval/dwell_sweep").glob("*.py")
            if "nanmean" in p.read_text() and p.name != "plot_summary.py"]
    assert hits == ["cell_measures.py"]


# --------------------------------------------------------------------------- finish_cells ----
def test_finish_cells_writes_archive_and_row(tmp_path):
    scr = _scratch_with_cells(tmp_path, steps=(100,))
    legacy = {c: CM.measure_cell(scr / "labA" / c / "100") for c in ("avoid_x", "avoid_y")}
    shutil.copytree(scr, tmp_path / "legacy_copy")
    for c in ("avoid_x", "avoid_y"):
        shutil.rmtree(scr / "labA" / c / "100")
    cells_ = [("labA", c, 100) for c in ("avoid_x", "avoid_y")]
    stage_src = tmp_path / "legacy_copy"
    pairs = []
    for i, (lab, cond, s) in enumerate(cells_):
        st = tmp_path / "stage" / str(i)
        shutil.copytree(stage_src / lab / cond / str(s), st)
        pairs.append(f"{st}={scr / lab / cond / str(s)}")
    rc = FC.main(["--repo-root", str(_REPO), "--pairs", *pairs, "--rows-piece", str(tmp_path / "rows.csv"),
                  "--episodes", "4", "--log", str(tmp_path / "f.log")])
    assert rc == 0
    rows = list(csv.DictReader(open(tmp_path / "rows.csv")))
    assert [r["cond"] for r in rows] == ["avoid_x", "avoid_y"]
    for r in rows:
        z = scr / "labA" / r["cond"] / "100.zip"
        assert z.is_file() and not (scr / "labA" / r["cond"] / "100").exists()
        EB.verify(stage_src / "labA" / r["cond"] / "100", z)          # archive == original bytes
        assert [r[h] for h in CM.HEAD] == [str(x) for x in legacy[r["cond"]][1]]
        assert r["n_episodes"] == "4" and r["numpy_version"] == np.__version__
        assert r["bundle"] == f"labA/{r['cond']}/100.zip"
    assert "OK labA/avoid_x/100 n=4" in (tmp_path / "f.log").read_text()


def test_finish_cells_short_episode_count_fails(tmp_path):
    st = _write_cell(tmp_path / "stage" / "0", "rppo", n_ep=3)
    cell = tmp_path / "out" / "_scratch" / "labA" / "avoid_x" / "100"
    rc = FC.main(["--repo-root", str(_REPO), "--pairs", f"{st}={cell}", "--rows-piece", str(tmp_path / "r.csv"),
                  "--episodes", "4", "--log", str(tmp_path / "f.log")])
    assert rc == 1
    assert list(csv.DictReader(open(tmp_path / "r.csv")))[0]["n_episodes"] == "3"


def test_finish_cells_requires_repo_root(tmp_path):
    with pytest.raises(SystemExit):
        FC.main(["--pairs", "a=b", "--rows-piece", "x", "--episodes", "1", "--log", "l"])
    with pytest.raises(SystemExit, match="does not hold"):
        FC.main(["--repo-root", str(tmp_path), "--pairs", "a=b", "--rows-piece", "x", "--episodes", "1",
                 "--log", str(tmp_path / "l")])


# -------------------------------------------------------------------------------- collate ----
def _launch(tmp_path, scr, launch, labels, conds, steps, n_ep=4, drop=(), node="101"):
    """Archive + score every listed cell via finish_cells (except `drop`), remove the folders."""
    todo = [(lab, c, s) for lab in labels for c in conds for s in steps if (lab, c, s) not in drop]
    assert _finish(tmp_path, scr, launch, node, todo, n_ep) == 0
    for lab, c, s in [(lab, c, s) for lab in labels for c in conds for s in steps]:
        shutil.rmtree(scr / lab / c / str(s), ignore_errors=True)
    return [[lab, c, s] for lab in labels for c in conds for s in steps]


def test_collate_matches_aggregate_from_bundles(tmp_path):
    labels, conds, steps = ("labA", "labB"), ("avoid_x", "avoid_y"), (100, 200, 300)
    scr = _scratch_with_cells(tmp_path, labels, conds, steps)
    cells_ = _launch(tmp_path, scr, "L1", labels, conds, steps)
    groups = _groups(scr, labels, conds)
    n, problems = RS.collate(groups, scr, "L1", ["101"], cells_, 4)
    assert n == 4 and problems == {}
    via_rows = {g["out_csv"]: g["out_csv"].read_bytes() for g in groups}
    for g in groups:
        g["out_csv"].unlink()
    assert RS.aggregate_from_bundles(groups, scr, n_workers=1, seed_from_csv=False) == 4
    for g in groups:
        assert g["out_csv"].read_bytes() == via_rows[g["out_csv"]]


def test_collate_merges_without_dropping_old_rows(tmp_path):
    scr = _scratch_with_cells(tmp_path, steps=(100, 200))
    groups = _groups(scr, ("labA",), ("avoid_x", "avoid_y"))
    for g in groups:
        g["out_csv"].parent.mkdir(parents=True, exist_ok=True)
        g["out_csv"].write_text(",".join(CM.HEAD) + "\n" + "50,0.0001" + "," * len(CM.KEYS) + "\n")
    cells_ = _launch(tmp_path, scr, "L1", ("labA",), ("avoid_x", "avoid_y"), (100, 200))
    n, problems = RS.collate(groups, scr, "L1", ["101"], cells_, 4)
    assert n == 2 and not problems
    for g in groups:
        steps = [int(r["step"]) for r in csv.DictReader(open(g["out_csv"]))]
        assert steps == [50, 100, 200]


def test_collate_raises_on_missing_cell(tmp_path):
    scr = _scratch_with_cells(tmp_path, steps=(100, 200))
    cells_ = _launch(tmp_path, scr, "L1", ("labA",), ("avoid_x", "avoid_y"), (100, 200),
                     drop={("labA", "avoid_x", 100)})
    groups = _groups(scr, ("labA",), ("avoid_x", "avoid_y"))
    n, problems = RS.collate(groups, scr, "L1", ["101"], cells_, 4)
    assert n == 1 and list(problems) == [("labA", "avoid_x")]
    assert not groups[0]["out_csv"].exists() and groups[1]["out_csv"].exists()


def test_collate_raises_on_short_episode_count(tmp_path):
    scr = _scratch_with_cells(tmp_path, conds=("avoid_x",), steps=(100,), n_ep=3)
    todo = [("labA", "avoid_x", 100)]
    assert _finish(tmp_path, scr, "L1", "101", todo, 4) == 1          # finisher flags it too
    n, problems = RS.collate(_groups(scr, ("labA",), ("avoid_x",)), scr, "L1", ["101"], [list(todo[0])], 4)
    assert n == 0 and "3 episodes, expected 4" in problems[("labA", "avoid_x")][0]


def test_collate_reads_pieces_when_rows_table_missing(tmp_path):
    scr = _scratch_with_cells(tmp_path, conds=("avoid_x",), steps=(100,))
    cells_ = _launch(tmp_path, scr, "L1", ("labA",), ("avoid_x",), (100,))
    assert not (scr / "_rows" / "L1" / "rows_101.csv").exists()     # worker died before concatenating
    n, problems = RS.collate(_groups(scr, ("labA",), ("avoid_x",)), scr, "L1", ["101"], cells_, 4)
    assert n == 1 and not problems


def _fake_spec(tmp_path, steps, conds=("avoid_x", "avoid_y")):
    run = tmp_path / "JAX_RecurrentPPO" / "run_s42"
    for s in steps:
        (run / "models" / str(s)).mkdir(parents=True)
    probe = tmp_path / "probes"
    probe.mkdir()
    for c in conds:
        (probe / f"{c}.yaml").write_text("{}\n")
    return {"name": "t", "algo": "rppo", "probe": str(probe), "conditions": list(conds), "nodes": [101],
            "runs": [{"label": "labA", "path": str(run)}]}


def test_incomplete_group_not_merged_and_retested(tmp_path):
    """Review M6: after a hole, the group's CSV is not advanced, so the next launch re-tests it."""
    steps = (100, 200, 300)
    spec = _fake_spec(tmp_path, steps)
    out = tmp_path / "out"
    scr = _scratch_with_cells(tmp_path, steps=steps)
    cells_ = _launch(tmp_path, scr, "L1", ("labA",), ("avoid_x", "avoid_y"), steps,
                     drop={("labA", "avoid_x", 200)})
    _, cond_groups = RS.build_groups(spec, out, None)
    n, problems = RS.collate(cond_groups, scr, "L1", ["101"], cells_, 4)
    assert n == 1 and list(problems) == [("labA", "avoid_x")]
    ck_groups, _ = RS.build_groups(spec, out, None)
    pending = sorted((g["step"], c["cond"]) for g in ck_groups for c in g["conds"])
    assert pending == [(100, "avoid_x"), (200, "avoid_x"), (300, "avoid_x")]


# ------------------------------------------------------------------------------- liveness ----
class Clock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t

    def sleep(self, dt):
        self.t += dt


def _mark(scr):
    m = scr / "_run_markers"
    m.mkdir(parents=True, exist_ok=True)
    return m


def test_poll_done_does_not_wait_forever_on_dead_worker(tmp_path):
    """Regression test for the silent hang (plan A3): a worker that died (exit_ written by its EXIT
    trap, no done_) must end the wait. Fails (5 s timeout) on the pre-2026-10 poll_done."""
    scr = tmp_path / "_scratch"
    m = _mark(scr)
    (m / "started_101").write_text("host=x pid=1 0\n")
    (m / "exit_101").write_text("rc=137 0\n")
    box = {}
    th = threading.Thread(target=lambda: box.setdefault("r", RS.poll_done(scr, ["101"], interval=0.01)),
                          daemon=True)
    th.start()
    th.join(5)
    assert not th.is_alive(), "poll_done still waiting 5 s after the worker died"
    assert box["r"] == {"101": "dead"}
    assert (m / "FAILED_101").exists()


def test_poll_detects_stalled_heartbeat(tmp_path):
    scr = tmp_path / "_scratch"
    m = _mark(scr)
    (m / "started_101").write_text("x\n")
    (m / "alive_101").write_text("5 3\n")                     # never changes again
    c = Clock()
    st = RS.poll_done(scr, ["101"], interval=30, clock=c, sleep=c.sleep)
    assert st == {"101": "stalled"} and c.t - 1000 <= RS.HEARTBEAT_STALE_S + 60


def test_poll_detects_no_progress(tmp_path):
    scr = tmp_path / "_scratch"
    m = _mark(scr)
    (m / "started_101").write_text("x\n")
    c = Clock()

    def sleep(dt):                                             # heartbeat alive, lines frozen at 7
        c.sleep(dt)
        (m / "alive_101").write_text(f"{c.t:.0f} 7\n")
    st = RS.poll_done(scr, ["101"], interval=30, clock=c, sleep=sleep)
    assert st == {"101": "stalled"}
    assert RS.PROGRESS_STALE_S < c.t - 1000 <= RS.PROGRESS_STALE_S + 120
    assert "no worklist line finished" in (m / "FAILED_101").read_text()


def test_poll_detects_never_started(tmp_path):
    scr = tmp_path / "_scratch"
    _mark(scr)
    c = Clock()
    assert RS.poll_done(scr, ["101"], interval=30, clock=c, sleep=c.sleep) == {"101": "never_started"}


def test_poll_waits_for_healthy_node_after_another_dies(tmp_path):
    scr = tmp_path / "_scratch"
    m = _mark(scr)
    for n in ("101", "102"):
        (m / f"started_{n}").write_text("x\n")
    (m / "exit_101").write_text("rc=1 0\n")
    c = Clock()

    def sleep(dt):
        c.sleep(dt)
        (m / "alive_102").write_text(f"{c.t} {int(c.t)}\n")
        if c.t > 1300:
            (m / "done_102").write_text("")
    assert RS.poll_done(scr, ["101", "102"], interval=30, clock=c, sleep=sleep) == {"101": "dead", "102": "done"}


# ---------------------------------------------------------------------------------- status ----
def _prov(out, cid, nodes):
    d = out / "_provenance" / cid
    d.mkdir(parents=True)
    (d / "provenance.json").write_text(json.dumps({"launch_format": RS.FORMAT, "nodes": nodes,
                                                   "cells": [], "episodes": 4}))


def test_status_reports_dead_collation_any_host(tmp_path):
    out = tmp_path / "out"
    scr = out / "_scratch"
    m = _mark(scr)
    _prov(out, "L1", ["101"])
    (m / "done_101").write_text("")
    (m / "collate_L1.started").write_text(json.dumps({"host": "some-other-host", "pid": 1}))
    (m / "collate_L1.alive").write_text("0\n")
    old = time.time() - RS.COLLATE_STALE_S - 60
    os.utime(m / "collate_L1.alive", (old, old))
    lines = RS.status(out)
    assert any("launch L1" in ln and "DEAD" in ln for ln in lines)


def test_status_workers_done_never_collated(tmp_path):
    out = tmp_path / "out"
    m = _mark(out / "_scratch")
    _prov(out, "L1", ["101", "102"])
    (m / "done_101").write_text("")
    (m / "done_102").write_text("")
    lines = RS.status(out)
    assert any("workers done, never collated" in ln for ln in lines)


def test_collate_markers_done_and_failed(tmp_path):
    scr = tmp_path / "_scratch"
    assert RS.with_collate_markers(scr, "c1", lambda: 7, beat_s=0.01) == 7
    assert RS.collation_state(scr, "c1") == "done"
    with pytest.raises(ZeroDivisionError):
        RS.with_collate_markers(scr, "c2", lambda: 1 / 0, beat_s=0.01)
    assert RS.collation_state(scr, "c2") == "failed"
    assert "ZeroDivisionError" in (scr / "_run_markers" / "collate_c2.failed").read_text()


# -------------------------------------------------------- the copied worker, end to end (N1) ----
STUB_EVAL = r'''
import argparse, sys
from pathlib import Path
sys.path.insert(0, "@REPO@")
from tests.scripts.test_episode_bundle import _write_cell
ap = argparse.ArgumentParser()
ap.add_argument("--config-list"); ap.add_argument("--checkpoint"); ap.add_argument("--eval-n-episodes", type=int)
a, _ = ap.parse_known_args()
for i, line in enumerate(Path(a.config_list).read_text().splitlines()):
    cfg, out = line.split("\t")
    _write_cell(Path(out), "rppo", n_ep=a.eval_n_episodes, seed=int(Path(a.checkpoint).name) + len(cfg))
'''


def _fake_repo(tmp_path):
    """A repo root that is NOT where the worker copy lives: real src/ + measures, stub test program."""
    r = tmp_path / "repo"
    (r / "scripts" / "eval").mkdir(parents=True)
    os.symlink(_REPO / "src", r / "src")
    os.symlink(_REPO / "tests", r / "tests")
    os.symlink(_REPO / "scripts" / "behavior_measures", r / "scripts" / "behavior_measures")
    (r / "scripts" / "eval" / "eval_rollout.py").write_text(STUB_EVAL.replace("@REPO@", str(_REPO)))
    return r


def test_copied_worker_end_to_end(tmp_path):
    """N1: the worker and finisher run from a provenance copy, given the repo root explicitly; they
    write one archive per cell, the rows tables, and the markers; collation reproduces the CSV that
    scoring the archives gives."""
    repo = _fake_repo(tmp_path)
    out = tmp_path / "results" / "out"
    scr = out / "_scratch"
    worker = out / "_provenance" / "L1" / "worker"
    worker.mkdir(parents=True)
    for f in RS.WORKER_FILES:
        shutil.copy2(_REPO / "scripts" / "eval" / "dwell_sweep" / f, worker / f)
    steps, conds = (100, 200), ("avoid_x", "avoid_y")
    lines = [f"/runs/run_s42/models/{s}|-|-|" + ";".join(f"/cfg/{c}.yaml,{scr / 'labA' / c / str(s)}" for c in conds)
             for s in steps]
    (scr / "_worklists").mkdir(parents=True)
    wl = scr / "_worklists" / "worklist_101.txt"
    wl.write_text("\n".join(lines) + "\n")
    cmd = RS.worker_command(worker / "sweep_worker.sh", wl, "101", 2, 3, "L1").replace(str(RS.REPO_ROOT), str(repo))
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=600)
    m = scr / "_run_markers"
    assert r.returncode == 0, r.stderr
    assert (m / "done_101").exists() and (m / "exit_101").read_text().startswith("rc=0")
    assert not (m / "fail_101").exists(), (m / "fail_101").read_text()
    assert len((m / "lines_101").read_text().split()) == 2
    for c in conds:
        for s in steps:
            assert (scr / "labA" / c / f"{s}.zip").is_file() and not (scr / "labA" / c / str(s)).exists()
    cells_ = [["labA", c, s] for c in conds for s in steps]
    groups = _groups(scr, ("labA",), conds)
    n, problems = RS.collate(groups, scr, "L1", ["101"], cells_, 3)
    assert n == 2 and not problems
    via_rows = {g["out_csv"]: g["out_csv"].read_bytes() for g in groups}
    for g in groups:
        g["out_csv"].unlink()
    RS.aggregate_from_bundles(groups, scr, n_workers=1, seed_from_csv=False)
    for g in groups:
        assert g["out_csv"].read_bytes() == via_rows[g["out_csv"]]
    assert not list(Path("/tmp").glob("dwellsweep_L1_101_*"))          # staging cleaned


def test_worker_refuses_without_repo_root(tmp_path):
    r = subprocess.run(["bash", str(_REPO / "scripts/eval/dwell_sweep/sweep_worker.sh"), "wl", "101", "2", "3", "L1"],
                       capture_output=True, text=True)
    assert r.returncode == 2 and "repo_root" in r.stderr


def test_dry_run_prints_copied_worker_with_six_args(tmp_path, capsys, monkeypatch):
    spec = _fake_spec(tmp_path, (100,))
    spec["output_dir"] = str(tmp_path / "o")
    import yaml
    sp = tmp_path / "spec.yaml"
    sp.write_text(yaml.safe_dump(spec))
    monkeypatch.setattr(sys, "argv", ["run_sweep.py", str(sp), "--dry-run", "--nodes", "105,110"])
    RS.main()
    o = capsys.readouterr().out
    cmd_lines = [ln for ln in o.splitlines() if "sweep_worker.sh" in ln]
    assert len(cmd_lines) == 1                                     # one checkpoint -> one node used
    assert "/_provenance/" in cmd_lines[0] and "/worker/sweep_worker.sh" in cmd_lines[0]
    tail = cmd_lines[0].split("sweep_worker.sh", 1)[1].split('"')[0].split()
    assert len(tail) == 6 and tail[-1] == str(RS.REPO_ROOT)
