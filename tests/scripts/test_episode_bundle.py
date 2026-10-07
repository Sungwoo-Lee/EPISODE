"""Tests for src/utils/episode_bundle.py (plan: SWEEP_EPISODE_BUNDLES_AND_ON_NODE_MEASURES.md, F1/F10).

No checkpoints, no NAS: synthetic cells are written into pytest's tmp_path with the real
EpisodeRecorder.write and np.savez_compressed, in the two layouts the sweep produces
(rPPO: episodes 0-based + .npz arrays + windows parquet stand-in; Dreamer: recordings only, 1-based).
"""
import json
import os
import shutil
import socket
import sys
import zipfile
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO))

import src.utils.episode_bundle as EB  # noqa: E402
from src.utils.eval_recording import EpisodeRecorder, load_episode  # noqa: E402

STEP = 10000021


# ------------------------------------------------------------------------------- fixtures ----
def _state(t, rng):
    return SimpleNamespace(
        agent_pos=np.array([t % 7, 3]), satiation=50.0 - t, nutrition=40.0, injury_level=0.1 * t,
        rest_streak=0, res_pos=np.zeros((2, 2), int), res_active=np.ones(2, bool),
        animal_pos=np.array([[int(rng.integers(0, 7)), 4]]), obs_pos=np.array([[2, 3]]))


def _write_cell(cell: Path, layout: str, n_ep: int = 4, seed: int = 0):
    """A synthetic sweep cell. layout 'rppo': <tag>/<step>/{episodes,recordings/<step>,windows}/...
    with 0-based episodes; 'dreamer': <tag>/<step>/recordings/<step>/ with 1-based episodes."""
    rng = np.random.default_rng(seed)
    base = cell / "run_tag" / str(STEP)
    rec_dir = base / "recordings" / str(STEP)
    first = 0 if layout == "rppo" else 1
    for e in range(first, first + n_ep):
        r = EpisodeRecorder(e, 0, seed + e)
        for t in range(5 + e):
            r.append(_state(t, rng), rng.normal(size=6), rng.normal(size=6), int(t % 4), 0.5)
        r.write(rec_dir / f"episode_{e:06d}.rec.gz")
        if layout == "rppo":
            (base / "episodes").mkdir(parents=True, exist_ok=True)
            np.savez_compressed(base / "episodes" / f"{e:04d}.npz",
                                obs=rng.normal(size=(5, 6)), act=np.arange(5))
    (rec_dir / "run_meta.pkl").write_bytes(b"meta" * 10)
    (base / "metadata.json").write_text(json.dumps({"step": STEP}))
    if layout == "rppo":
        (base / "windows").mkdir(parents=True, exist_ok=True)
        (base / "windows" / "threat_onsets.parquet").write_bytes(os.urandom(300))
        (base / "online_replay.json").write_text("{}")
    return cell


@pytest.fixture
def repo(tmp_path):
    """A fake repo root with one class-S sweep cell at results/eval/x/_scratch/lab/cond/<STEP>."""
    root = tmp_path / "repo"
    cond = root / "results" / "eval" / "avoidance" / "mh" / "_scratch" / "lab_s42" / "avoid_pred"
    cell = _write_cell(cond / str(STEP), "rppo")
    return SimpleNamespace(root=root, cond=cond, cell=cell, zip=cond / f"{STEP}.zip",
                           wal=tmp_path / "wal.jsonl")


@pytest.fixture
def host(monkeypatch):
    """Switch the hostname EB sees: host('packer') before pack, host('checker') before delete."""
    def _set(name):
        monkeypatch.setattr(EB.socket, "gethostname", lambda: name)
    return _set


def _tree_bytes(d: Path):
    return {p.relative_to(d).as_posix(): (p.read_bytes() if p.is_file() else None)
            for p in sorted(d.rglob("*"))}


# ---------------------------------------------------------------------------------- pack ----
@pytest.mark.parametrize("layout", ["rppo", "dreamer"])
def test_pack_roundtrip_bytes_equal(tmp_path, layout):
    cell = _write_cell(tmp_path / "c" / str(STEP), layout)
    z = tmp_path / "c" / f"{STEP}.zip"
    man = EB.pack(cell, z)
    with zipfile.ZipFile(z) as zf:
        assert all(i.compress_type == zipfile.ZIP_STORED for i in zf.infolist())
        for p in cell.rglob("*"):
            if p.is_file():
                assert zf.read(p.relative_to(cell).as_posix()) == p.read_bytes()
    assert set(man) == {p.relative_to(cell).as_posix() for p in cell.rglob("*") if p.is_file()}
    out = EB.extract(z, tmp_path / "x")
    assert _tree_bytes(out) == _tree_bytes(cell)
    meta = EB.read_comment(z)
    assert meta["n"] == len(man) and meta["bytes"] == sum(s for s, _ in man.values())


def test_pack_preserves_empty_dirs_and_nested_layout(tmp_path):
    cell = _write_cell(tmp_path / str(STEP), "rppo")
    (cell / "empty" / "deeper").mkdir(parents=True)
    z = tmp_path / f"{STEP}.zip"
    EB.pack(cell, z)
    with zipfile.ZipFile(z) as zf:
        names = [i.filename for i in zf.infolist()]
    assert "empty/" in names and "empty/deeper/" in names
    assert names == sorted(names)
    assert _tree_bytes(EB.extract(z, tmp_path / "x")) == _tree_bytes(cell)


def test_pack_is_atomic(tmp_path, monkeypatch):
    cell = _write_cell(tmp_path / str(STEP), "rppo")
    z = tmp_path / f"{STEP}.zip"

    def boom(*a, **k):
        raise EB.BundleMismatch("injected")
    monkeypatch.setattr(EB, "verify", boom)
    with pytest.raises(EB.BundleMismatch):
        EB.pack(cell, z)
    assert not z.exists()
    assert not list(tmp_path.glob("*.partial-*"))
    monkeypatch.undo()
    EB.pack(cell, z)
    with pytest.raises(FileExistsError):
        EB.pack(cell, z)


# ------------------------------------------------------------------------------ readers ----
@pytest.mark.parametrize("layout", ["rppo", "dreamer"])
@pytest.mark.parametrize("pattern", ["**/episode_*.rec.gz", "*/*/episodes/*.npz", "**/*",
                                     "run_tag/*/recordings/*/episode_*.rec.gz", "**/run_meta.pkl"])
def test_members_order_matches_sorted_glob(tmp_path, layout, pattern):
    cell = _write_cell(tmp_path / str(STEP), layout, n_ep=12)
    z = tmp_path / f"{STEP}.zip"
    EB.pack(cell, z)
    want = [p.relative_to(cell).as_posix() for p in sorted(cell.glob(pattern)) if p.is_file()]
    assert EB.members(cell, pattern) == want
    assert EB.members(z, pattern) == want


@pytest.mark.parametrize("layout", ["rppo", "dreamer"])
def test_measure_cell_dir_equals_zip(tmp_path, layout):
    """Phase-1 form of F10's test (cell_measures.py lands in Phase 3): every recording decodes
    identically from both forms in the same order, and run_sweep._measure_cell gives the same row
    on the original folder and on a folder extracted from the archive."""
    cell = _write_cell(tmp_path / "a" / str(STEP), layout)
    z = tmp_path / "a" / f"{STEP}.zip"
    EB.pack(cell, z)
    names = EB.members(z)
    assert names == EB.members(cell) and len(names) == 4
    assert names[0].endswith("episode_000000.rec.gz" if layout == "rppo" else "episode_000001.rec.gz")
    for n in names:
        a, b = load_episode(cell / n), EB.load_recording(z, n)
        assert a.keys() == b.keys()
        for k in ("obs", "true_obs", "actions", "rewards"):
            assert np.array_equal(a[k], b[k])
        assert len(a["snapshots"]) == len(b["snapshots"])
        for sa, sb in zip(a["snapshots"], b["snapshots"]):
            assert sa.keys() == sb.keys() and all(np.array_equal(sa[k], sb[k]) for k in sa)
        assert EB.load_recording(cell, n)["seed"] == a["seed"]
    if layout == "rppo":
        for n in EB.members(z, "**/episodes/*.npz"):
            a, b = EB.load_npz(cell, n), EB.load_npz(z, n)
            assert a.keys() == b.keys() and all(np.array_equal(a[k], b[k]) for k in a)
    sys.path.insert(0, str(_REPO / "scripts" / "eval" / "dwell_sweep"))
    import run_sweep
    ext = EB.extract(z, tmp_path / "b" / str(STEP))
    assert run_sweep._measure_cell(cell) == run_sweep._measure_cell(ext)
    assert run_sweep._measure_cell(cell) is not None


def test_cell_path_forms_and_conflict(tmp_path):
    cond = tmp_path / "cond"
    assert EB.cell_path(cond, STEP) is None
    cell = _write_cell(cond / str(STEP), "dreamer")
    assert EB.cell_path(cond, STEP) == cell
    EB.pack(cell, cond / f"{STEP}.zip")
    assert EB.cell_path(cond, STEP) == cond / f"{STEP}.zip"        # folder not newer: archive wins
    shutil.rmtree(cell)
    assert EB.cell_path(cond, str(STEP)) == cond / f"{STEP}.zip"


def test_cell_path_raises_on_dir_newer_than_zip(tmp_path):
    cond = tmp_path / "cond"
    cell = _write_cell(cond / str(STEP), "rppo")
    EB.pack(cell, cond / f"{STEP}.zip")
    newer = cell / "run_tag" / str(STEP) / "metadata.json"
    st = newer.stat()
    os.utime(newer, ns=(st.st_atime_ns, st.st_mtime_ns + 5_000_000_000))  # an old-code re-test
    with pytest.raises(EB.CellConflict):
        EB.cell_path(cond, STEP)


# ------------------------------------------------------------------------------- verify ----
def _packed(tmp_path):
    cell = _write_cell(tmp_path / str(STEP), "rppo")
    z = tmp_path / f"{STEP}.zip"
    EB.pack(cell, z)
    return cell, z


def test_verify_detects_changed_byte(tmp_path):
    cell, z = _packed(tmp_path)
    p = cell / "run_tag" / str(STEP) / "windows" / "threat_onsets.parquet"
    b = bytearray(p.read_bytes()); b[100] ^= 1; p.write_bytes(bytes(b))
    with pytest.raises(EB.BundleMismatch):
        EB.verify(cell, z)


def test_verify_detects_missing_member(tmp_path):
    cell, z = _packed(tmp_path)
    (cell / "run_tag" / str(STEP) / "online_replay.json").unlink()
    with pytest.raises(EB.BundleMismatch):
        EB.verify(cell, z)


def test_verify_detects_extra_source_file(tmp_path):
    cell, z = _packed(tmp_path)
    (cell / "run_tag" / "late.json").write_text("{}")
    with pytest.raises(EB.BundleMismatch):
        EB.verify(cell, z)


def test_verify_detects_corrupt_archive(tmp_path):
    cell, z = _packed(tmp_path)
    raw = bytearray(z.read_bytes())
    i = raw.find(b"meta" * 10)           # run_meta.pkl's stored bytes
    raw[i] ^= 1
    z.write_bytes(bytes(raw))
    with pytest.raises(EB.BundleMismatch):
        EB.verify(cell, z)


# ------------------------------------------------------------------------------- delete ----
def test_delete_happy_path(repo, host):
    host("packer"); EB.pack(repo.cell, repo.zip)
    n_files = sum(1 for p in repo.cell.rglob("*") if p.is_file())
    host("checker")
    assert EB.delete_verified(repo.cell, repo.zip, repo.wal, repo_root=repo.root) == n_files
    assert not repo.cell.exists() and repo.zip.is_file()
    assert EB.cell_path(repo.cond, STEP) == repo.zip
    assert len(repo.wal.read_text().splitlines()) == n_files


def test_delete_requires_repo_root(repo, host):
    host("packer"); EB.pack(repo.cell, repo.zip); host("checker")
    with pytest.raises(TypeError):
        EB.delete_verified(repo.cell, repo.zip, repo.wal)
    with pytest.raises(EB.DeleteRefused):
        EB.delete_verified(repo.cell, repo.zip, repo.wal, repo_root=repo.root / "results")
    assert repo.cell.is_dir()


def test_delete_refuses_on_packing_host(repo, host):
    host("packer"); EB.pack(repo.cell, repo.zip)
    with pytest.raises(EB.DeleteRefused):
        EB.delete_verified(repo.cell, repo.zip, repo.wal, repo_root=repo.root)
    assert repo.cell.is_dir() and not repo.wal.exists()


def test_delete_refuses_after_source_changed(repo, host):
    host("packer"); EB.pack(repo.cell, repo.zip); host("checker")
    (repo.cell / "run_tag" / str(STEP) / "metadata.json").write_text('{"step": 1}')
    with pytest.raises(EB.BundleMismatch):
        EB.delete_verified(repo.cell, repo.zip, repo.wal, repo_root=repo.root)
    assert sum(1 for p in repo.cell.rglob("*") if p.is_file()) > 0 and not repo.wal.exists()


def test_delete_leaves_file_created_after_verify(repo, host, monkeypatch):
    host("packer"); EB.pack(repo.cell, repo.zip); host("checker")
    late = repo.cell / "run_tag" / str(STEP) / "late.json"
    real_verify = EB.verify

    def verify_then_write(*a, **k):
        m = real_verify(*a, **k)
        late.write_text("{}")             # a writer appears between verification and unlink
        return m
    monkeypatch.setattr(EB, "verify", verify_then_write)
    with pytest.raises((EB.BundleMismatch, OSError)):
        EB.delete_verified(repo.cell, repo.zip, repo.wal, repo_root=repo.root)
    assert late.read_text() == "{}"


def test_delete_leaves_file_created_after_unlink_check(repo, host, monkeypatch):
    """A file created after the file-list re-check survives: rmdir (not rmtree) fails on it."""
    host("packer"); EB.pack(repo.cell, repo.zip); host("checker")
    late = repo.cell / "run_tag" / "late.json"
    real_unlink = os.unlink
    calls = {"n": 0}

    def unlink_and_spawn(p, *a, **k):
        calls["n"] += 1
        if calls["n"] == 1:
            late.write_text("{}")
        return real_unlink(p, *a, **k)
    monkeypatch.setattr(EB.os, "unlink", unlink_and_spawn)
    with pytest.raises(OSError):
        EB.delete_verified(repo.cell, repo.zip, repo.wal, repo_root=repo.root)
    assert late.read_text() == "{}"


@pytest.mark.parametrize("bad", ["csv", "png", "provenance", "outside", "notdigits", "underscore",
                                 "wrongzip", "notscratch"])
def test_delete_path_guard(repo, host, bad, tmp_path):
    host("packer"); EB.pack(repo.cell, repo.zip); host("checker")
    cell, z = repo.cell, repo.zip
    if bad in ("csv", "png"):
        f = cell / "run_tag" / f"table.{bad}"; f.write_text("x")
        # the archive must match for the guard to be the reason
        z.unlink(); host("packer"); EB.pack(cell, z); host("checker")
    elif bad == "provenance":
        cell = repo.root / "results" / "eval" / "a" / "_provenance" / "_scratch" / "l" / "c" / str(STEP)
        shutil.copytree(repo.cell, cell); z = cell.parent / f"{STEP}.zip"
        host("packer"); EB.pack(cell, z); host("checker")
    elif bad == "outside":
        cell = tmp_path / "elsewhere" / "_scratch" / "l" / "c" / str(STEP)
        shutil.copytree(repo.cell, cell); z = cell.parent / f"{STEP}.zip"
        host("packer"); EB.pack(cell, z); host("checker")
    elif bad in ("notdigits", "underscore", "notscratch"):
        name = {"notdigits": ("_scratch", "l", "c", "12a"), "underscore": ("_scratch", "_rows", "c", "5"),
                "notscratch": ("scratch", "l", "c", "5")}[bad]
        cell = repo.root / "results" / "eval" / "a" / Path(*name)
        shutil.copytree(repo.cell, cell); z = cell.parent / f"{name[-1]}.zip"
        host("packer"); EB.pack(cell, z); host("checker")
    elif bad == "wrongzip":
        z = repo.cond / "other.zip"; shutil.copy(repo.zip, z)
    before = _tree_bytes(cell)
    with pytest.raises(EB.DeleteRefused):
        EB.delete_verified(cell, z, repo.wal, repo_root=repo.root)
    assert _tree_bytes(cell) == before and not repo.wal.exists()


def test_delete_resumes_from_wal(repo, host, monkeypatch):
    host("packer"); EB.pack(repo.cell, repo.zip); host("checker")
    real_unlink = os.unlink
    calls = {"n": 0}

    def die_after_three(p, *a, **k):
        calls["n"] += 1
        if calls["n"] > 3:
            raise KeyboardInterrupt("killed mid-delete")
        return real_unlink(p, *a, **k)
    monkeypatch.setattr(EB.os, "unlink", die_after_three)
    with pytest.raises(KeyboardInterrupt):
        EB.delete_verified(repo.cell, repo.zip, repo.wal, repo_root=repo.root)
    monkeypatch.setattr(EB.os, "unlink", real_unlink)
    assert repo.cell.is_dir()
    # without the WAL the remnant does not verify
    with pytest.raises(EB.BundleMismatch):
        EB.verify(repo.cell, repo.zip)
    EB.delete_verified(repo.cell, repo.zip, repo.wal, repo_root=repo.root)
    assert not repo.cell.exists()
    # a remnant whose missing files are NOT in the WAL is refused
    cell2 = _write_cell(repo.cond / "777", "rppo", seed=3)
    host("packer"); EB.pack(cell2, repo.cond / "777.zip"); host("checker")
    next(p for p in cell2.rglob("*.npz")).unlink()
    with pytest.raises(EB.BundleMismatch):
        EB.delete_verified(cell2, repo.cond / "777.zip", repo.wal, repo_root=repo.root)


def test_module_has_no_repo_root_from_file_location():
    """Review N1: nothing in the library derives the repo from __file__."""
    src = (_REPO / "src" / "utils" / "episode_bundle.py").read_text()
    assert "__file__" not in src
