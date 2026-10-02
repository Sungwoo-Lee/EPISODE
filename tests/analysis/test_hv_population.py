"""make_population.py + readings.load_population on fake run dirs (plan R3, Revision 2 N1/N3/N4)."""
import os
import sys

import pytest
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scripts", "analysis", "studies", "hypervigilance"))
import make_population as MP  # noqa: E402
import readings as RD  # noqa: E402

HEADER = ("| Run | Status | Cell | Tag (= wandb-name) | wandb-group | wandb-job-type | Seed | Node | GPU "
          "| Launched at | WandB run ID | Log path |")
SEP = "|" + "---|" * 12


def fake_run(tmp, name, seed=42, ckpts=(10000046,), budget=10000000):
    run = tmp / "results" / "JAX_RecurrentPPO" / name
    (run / "models").mkdir(parents=True)
    yaml.safe_dump({"seed": seed, "episodes": budget}, open(run / "models" / "config.yaml", "w"))
    for c in ckpts:
        (run / "models" / str(c)).mkdir()
    return run


def fake_store(tmp, name, ckpt=10000046, root="traj"):
    d = tmp / root / name / str(ckpt) / "abc123"
    d.mkdir(parents=True)
    (d / "episodes_00000.parquet").write_text("")
    return tmp / root


def row(rid, status, cell, tag, seed, run):
    log = f"`logs/x.log` · run dir `{run}` · HEAD `abc`" if run else "—"
    return f"| {rid} | {status} | {cell} | `{tag}` | g | prod | {seed} | 1 | 0 | t | `id` | {log} |"


def doc(tmp, rows):
    p = tmp / "study.md"
    p.write_text("# Study\n\n## 3. Launch Manifest\n\nintro\n\n" + HEADER + "\n" + SEP + "\n"
                 + "\n".join(rows) + "\n\nafter\n")
    return str(p)


def test_failed_run_and_its_relaunch_resolve_to_the_relaunch(tmp_path):
    a = fake_run(tmp_path, "20261001-000000_rppo_hv1ch_t1none_s42")
    b = fake_run(tmp_path, "20261002-000000_rppo_hv1ch_t1none_s42_r2")
    root = fake_store(tmp_path, b.name)
    md = doc(tmp_path, [row("H01", "failed (NaN at 3M)", "1ch · ordinary", "rppo_hv1ch_t1none_s42", 42, a),
                        row("H01r", "completed", "1ch · ordinary", "rppo_hv1ch_t1none_s42_r2", 42, b)])
    cells = MP.from_study_doc(md, [str(root)])
    assert [c["status"] for c in cells] == ["failed", "completed"]
    P = RD.load_population(_write(tmp_path, cells))
    assert len(P["cells"]) == 1 and P["cells"][0]["run"].endswith("_s42_r2")
    assert P["cells"][0]["stores"][0].startswith(str(root / b.name))


def _write(tmp, cells):
    import json
    p = tmp / "population.json"
    json.dump({"population": "t", "cells": cells}, open(p, "w"))
    return str(p)


def test_two_completed_candidates_for_one_seed_are_refused(tmp_path):
    a = fake_run(tmp_path, "20261001-000000_rppo_hv1ch_t1none_s42")
    b = fake_run(tmp_path, "20261002-000000_rppo_hv1ch_t1none_s42_r2")
    root = fake_store(tmp_path, a.name)
    fake_store(tmp_path, b.name)
    md = doc(tmp_path, [row("H01", "completed", "1ch · ordinary", "t", 42, a),
                        row("H01r", "completed", "1ch · ordinary", "t", 42, b)])
    with pytest.raises(SystemExit, match="two completed cells"):
        RD.load_population(_write(tmp_path, MP.from_study_doc(md, [str(root)])))


def test_matched_dir_is_never_single_channel(tmp_path):
    m = RD.HV_TAG_RE.match("20261001-000000_rppo_hv1chm_t1none_s42")
    assert m["world"] == "hv1chm"
    run = fake_run(tmp_path, "20261001-000000_rppo_hv1chm_t1none_s42")
    root = fake_store(tmp_path, run.name)
    md = doc(tmp_path, [row("H11", "completed", "1ch · ordinary", "t", 42, run)])   # wrong cell
    with pytest.raises(SystemExit, match="world/agent/seed"):
        RD.load_population(_write(tmp_path, MP.from_study_doc(md, [str(root)])))


def test_status_parsing_and_planned_rows(tmp_path):
    assert MP.parse_status("completed (not relaunched; stores re-collected)") == "completed"
    with pytest.raises(SystemExit):
        MP.parse_status("finished")
    md = doc(tmp_path, [row("H17", "planned", "2ch · modulated", "rppo_hv2ch_t16quad_s45", 45, None)])
    cells = MP.from_study_doc(md, [str(tmp_path / "traj")])
    assert cells[0]["status"] == "planned" and cells[0]["run"] is None
    assert RD.load_population(_write(tmp_path, cells))["cells"] == []


def test_stale_running_status_is_refused_never_promoted(tmp_path):
    run = fake_run(tmp_path, "20261001-000000_rppo_hv2ch_t1none_s43")
    md = doc(tmp_path, [row("H07", "running", "2ch · ordinary", "t", 43, run)])
    cells = MP.from_study_doc(md, [str(tmp_path / "traj")])       # final ckpt, no store: fine
    assert cells[0]["status"] == "running"
    root = fake_store(tmp_path, run.name)
    with pytest.raises(SystemExit, match="stale status"):
        MP.from_study_doc(md, [str(root)])


def test_running_row_before_the_final_checkpoint_is_not_stale(tmp_path):
    run = fake_run(tmp_path, "20261001-000000_rppo_hv2ch_t1none_s43", ckpts=(8000012,))
    root = fake_store(tmp_path, run.name, ckpt=8000012)
    assert MP.from_study_doc(doc(tmp_path, [row("H07", "running", "2ch · ordinary", "t", 43, run)]),
                             [str(root)])[0]["status"] == "running"


def test_completed_row_without_a_store_is_refused(tmp_path):
    run = fake_run(tmp_path, "20261001-000000_rppo_hv2ch_t1none_s43")
    md = doc(tmp_path, [row("H07", "completed", "2ch · ordinary", "t", 43, run)])
    with pytest.raises(SystemExit, match="no store"):
        MP.from_study_doc(md, [str(tmp_path / "traj")])


def test_checkpoint_nearest_is_per_run(tmp_path):
    a = fake_run(tmp_path, "20261001-000000_rppo_hv2ch_t1none_s42")
    b = fake_run(tmp_path, "20261001-000001_rppo_hv2ch_t1none_s43")
    root = None
    for run, ck in ((a, 8000033), (b, 8000043)):
        for c in (2000011, ck, 10000046):
            root = fake_store(tmp_path, run.name, ckpt=c, root="late")
    cells = MP.from_runs([str(a), str(b)], "hv2ch", [str(root)], nearest=8000000)
    assert [c["checkpoint"] for c in cells] == ["8000033", "8000043"]
    assert all(f"/{c['checkpoint']}/" in c["stores"][0] for c in cells)
    assert cells[0]["run"].endswith("_s42") and cells[1]["run"].endswith("_s43")
    with pytest.raises(SystemExit, match="several store checkpoints"):
        MP.from_runs([str(a)], "hv2ch", [str(root)])
    with pytest.raises(SystemExit, match="equally near"):
        MP.from_runs([str(a)], "hv2ch", [str(root)], nearest=5000022)


def test_backtick_aware_row_split_and_column_count_guard(tmp_path):
    cells = MP.split_row("| a | `x | y` | c |")
    assert cells == ["a", "`x | y`", "c"]
    run = fake_run(tmp_path, "20261001-000000_rppo_hv2ch_t1none_s43")
    bad = row("H07", "running", "2ch · ordinary", "t", 43, run) + " extra |"
    with pytest.raises(SystemExit, match="refusing rather than mis-aligning"):
        MP.parse_launch_manifest(doc(tmp_path, [bad]))
    ok = row("H07", "running", "2ch · ordinary", "t", 43, run).replace("`logs/x.log`", "`logs/a|b.log`")
    assert MP.parse_launch_manifest(doc(tmp_path, [ok]))[0]["Log path"].startswith("`logs/a|b.log`")


def test_regex_entry_disagreement_is_refused(tmp_path):
    run = fake_run(tmp_path, "20261001-000000_rppo_hv1ch_t1none_s44")
    root = fake_store(tmp_path, run.name)
    md = doc(tmp_path, [row("H05", "completed", "1ch · ordinary", "t", 43, run)])   # seed disagrees
    with pytest.raises(SystemExit):
        RD.load_population(_write(tmp_path, MP.from_study_doc(md, [str(root)])))


def test_the_real_study_manifest_parses():
    p = os.path.join(RD.ROOT, "docs", "experiments", "active", "hypervigilance",
                     "SINGLE_CHANNEL_SMELL_HYPERVIGILANCE.md")
    rows = MP.parse_launch_manifest(p)
    assert len(rows) == 18 and {MP.parse_status(r["Status"]) for r in rows} <= set(MP.STATUSES)
