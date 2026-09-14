"""Tests for scripts/eval/v1_path_guard.py (RENDERER_LAYOUT_REDESIGN.md section D5.4).

Every case runs in a throwaway git repo under tmp_path, never the project repo. Git is
isolated from user/system config for both these helpers and the guard's own
subprocesses (autouse env fixture). The frozen set is two fake files; plan session is
S1, a foreign session is S2.

Frame / fixture cases (FIXTURE CHANGED, frame drift) belong to Phase 0b (CP0.1b) and
are added with record-frames.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "scripts" / "eval"))
import v1_path_guard as guard  # noqa: E402

FROZEN = ["src/frozen_a.py", "configs/frozen_b.yaml"]
S1 = "https://claude.ai/code/session_S1"
S2 = "https://claude.ai/code/session_S2"


@pytest.fixture(autouse=True)
def _isolated_git_env(monkeypatch):
    for k, v in {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
                 "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                 "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}.items():
        monkeypatch.setenv(k, v)


def _git(repo, *args, stdin=None):
    return subprocess.run(["git", "-C", str(repo), "-c", "core.hooksPath=/dev/null",
                           *args], check=True, capture_output=True, text=True,
                          input=stdin).stdout


def _commit(repo, message, *paths):
    _git(repo, "add", "--", *paths)
    _git(repo, "commit", "-q", "-F", "-", stdin=message)


def _write(repo, rel, text):
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def _run(repo, *argv):
    return guard.main(["--repo-root", str(repo), *argv])


def _check(repo, capsys):
    capsys.readouterr()
    code = _run(repo, "check", "--frozen", *FROZEN)
    out = capsys.readouterr()
    return code, out.out + out.err


def _state_of(output, rel):
    for line in output.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1] == rel:
            return parts[0]
    raise AssertionError(f"no state line for {rel} in:\n{output}")


def _init(path):
    path.mkdir()
    _git(path, "init", "-q", "-b", "main")
    _write(path, FROZEN[0], "a = 1\n")
    _write(path, FROZEN[1], "icons: {}\n")
    _write(path, "README", "x\n")
    _commit(path, "init", *FROZEN, "README")
    return path


@pytest.fixture
def repo(tmp_path, capsys):
    r = _init(tmp_path / "repo")
    assert _run(r, "record-files", "--frozen", *FROZEN) == 0
    assert _run(r, "add-session", S1) == 0
    capsys.readouterr()
    return r


def _trailer(session):
    return f"change\n\nbody\n\nClaude-Session: {session}\n"


def _project_trailer(*sessions):
    lines = "".join(f"Claude-Session: {s}\n" for s in sessions)
    return ("feat(x): 🎨 change\n\nbody\n\n"
            "Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>\n" + lines)


def _bpath(repo):
    return repo / guard.DEFAULT_BASELINE_REL


def _baseline(repo):
    return json.loads(_bpath(repo).read_text())


def _edit_baseline(repo, fn):
    data = _baseline(repo)
    fn(data)
    _bpath(repo).write_text(json.dumps(data))


# ------------------------------------------------------------------ record + sessions


def test_record_files_contents(repo):
    data = _baseline(repo)
    head = _git(repo, "rev-parse", "HEAD").strip()
    assert data["plan_start_commit"] == head
    assert sorted(data["frozen_files"]) == sorted(FROZEN)
    for rel in FROZEN:
        e = data["frozen_files"][rel]
        assert e["worktree_sha256"] == guard.sha256_file(repo / rel)
        assert e["head_blob"] == _git(repo, "rev-parse", f"HEAD:{rel}").strip()
    assert data["plan_sessions"] == [S1]
    assert data["user_accepted"] == []
    diff = _bpath(repo).parent / guard.DIFF_FILENAME
    first = diff.read_text().splitlines()[0]
    assert first.startswith("# SNAPSHOT of other sessions' uncommitted")
    assert "DO NOT apply." in first
    assert not list(_bpath(repo).parent.glob(".*.tmp.*"))  # atomic write left no tmp


def test_record_files_on_dirty_tree_captures_delta(tmp_path, capsys):
    r = _init(tmp_path / "repo")
    _write(r, FROZEN[0], "a = 1\nwip = 2\n")
    assert _run(r, "record-files", "--frozen", *FROZEN) == 0
    diff = _bpath(r).parent / guard.DIFF_FILENAME
    assert "+wip = 2" in diff.read_text()
    code, out = _check(r, capsys)
    assert code == 0 and _state_of(out, FROZEN[0]) == "PASS"


def test_record_files_refuses_overwrite_without_force(repo):
    before = _bpath(repo).read_text()
    assert _run(repo, "record-files", "--frozen", *FROZEN) == 2
    assert _bpath(repo).read_text() == before


def test_force_rerecord_after_attributed_succeeds(repo, capsys):
    _write(repo, FROZEN[0], "a = 2\n")
    _commit(repo, _trailer(S2), FROZEN[0])
    assert _run(repo, "record-files", "--frozen", *FROZEN, "--force") == 0
    data = _baseline(repo)
    assert data["plan_sessions"] == [S1]  # carried over
    assert data["plan_start_commit"] == _git(repo, "rev-parse", "HEAD").strip()
    code, out = _check(repo, capsys)
    assert code == 0 and _state_of(out, FROZEN[0]) == "PASS"


def test_force_rerecord_refused_when_unattributable(repo, capsys):
    _write(repo, FROZEN[0], "a = 1\nours = 1\n")
    before = _bpath(repo).read_text()
    capsys.readouterr()
    assert _run(repo, "record-files", "--frozen", *FROZEN, "--force") == 2
    assert "refusing to re-record" in capsys.readouterr().err
    assert _bpath(repo).read_text() == before
    code, out = _check(repo, capsys)
    assert code == 1 and _state_of(out, FROZEN[0]) == "UNATTRIBUTABLE"


def test_add_session_idempotent_across_forms(repo):
    assert _run(repo, "add-session", S1) == 0
    assert _run(repo, "add-session", "session_S1") == 0
    assert _baseline(repo)["plan_sessions"] == [S1]


@pytest.mark.parametrize("value", ["01LG92Bg5jnSFoUMt4SaUUTk", "S2", "   "])
def test_add_session_refuses_non_session_id(repo, capsys, value):
    capsys.readouterr()
    assert _run(repo, "add-session", value) == 2
    assert "not a Claude session id" in capsys.readouterr().err
    assert _baseline(repo)["plan_sessions"] == [S1]


def test_force_rerecord_with_plan_owned_unions_previous(repo):
    assert _run(repo, "record-files", "--frozen", *FROZEN, "--force",
                "--plan-owned", "extra/owned/") == 0
    owned = _baseline(repo)["plan_owned_paths"]
    assert "extra/owned/" in owned
    assert set(guard.PLAN_OWNED_PATHS) <= set(owned)


def test_force_rerecord_refused_on_orphan_head(repo, capsys):
    before = _bpath(repo).read_text()
    _git(repo, "checkout", "-q", "--orphan", "rewritten")
    _commit(repo, "rewritten history\n", *FROZEN, "README")
    capsys.readouterr()
    assert _run(repo, "record-files", "--frozen", *FROZEN, "--force") == 2
    assert "not an ancestor" in capsys.readouterr().err
    assert _bpath(repo).read_text() == before


def test_trailerless_merge_commit_is_unattributable(repo, capsys):
    _git(repo, "checkout", "-q", "-b", "side")
    _write(repo, FROZEN[0], "a = M\n")
    _commit(repo, _trailer(S2), FROZEN[0])
    _git(repo, "checkout", "-q", "main")
    _write(repo, "README", "y\n")
    _commit(repo, _trailer(S2), "README")
    _git(repo, "merge", "-q", "--no-ff", "-m", "merge side", "side")
    code, out = _check(repo, capsys)
    assert code == 1 and _state_of(out, FROZEN[0]) == "UNATTRIBUTABLE"


# ------------------------------------------------------------------ the states


def test_pass_untouched(repo, capsys):
    code, out = _check(repo, capsys)
    assert code == 0
    assert all(_state_of(out, rel) == "PASS" for rel in FROZEN)
    assert "compared 2 file(s)" in out
    assert "frames: NOT compared" in out


def test_attributed_foreign_commit(repo, capsys):
    _write(repo, FROZEN[0], "a = 2\n")
    _commit(repo, _trailer(S2), FROZEN[0])
    code, out = _check(repo, capsys)
    assert code == 0
    assert _state_of(out, FROZEN[0]) == "ATTRIBUTED"
    assert _state_of(out, FROZEN[1]) == "PASS"


def test_mutation_uncommitted_edit_turns_red(repo, capsys):
    _write(repo, FROZEN[1], "icons: {campfire: x}\n")
    code, out = _check(repo, capsys)
    assert code == 1
    assert _state_of(out, FROZEN[1]) == "UNATTRIBUTABLE"
    assert _state_of(out, FROZEN[0]) == "PASS"
    assert "RESULT: FAIL" in out


def test_commit_without_trailer(repo, capsys):
    _write(repo, FROZEN[0], "a = 3\n")
    _commit(repo, "no trailer here\n", FROZEN[0])
    code, out = _check(repo, capsys)
    assert code == 1 and _state_of(out, FROZEN[0]) == "UNATTRIBUTABLE"
    assert "no Claude-Session trailer" in out


def test_commit_with_plan_session_trailer(repo, capsys):
    _write(repo, FROZEN[0], "a = 4\n")
    _commit(repo, _trailer(S1), FROZEN[0])
    code, out = _check(repo, capsys)
    assert code == 1 and _state_of(out, FROZEN[0]) == "UNATTRIBUTABLE"
    assert "trailer is a plan session" in out


@pytest.mark.parametrize("session,expected", [
    (S2, "ATTRIBUTED"), (S1, "UNATTRIBUTABLE"),
])
def test_project_trailer_block(repo, capsys, session, expected):
    _write(repo, FROZEN[0], "a = 40\n")
    _commit(repo, _project_trailer(session), FROZEN[0])
    code, out = _check(repo, capsys)
    assert _state_of(out, FROZEN[0]) == expected
    assert code == (0 if expected == "ATTRIBUTED" else 1)


def test_plan_and_foreign_trailer_pair(repo, capsys):
    _write(repo, FROZEN[0], "a = 41\n")
    _commit(repo, _project_trailer(S2, S1), FROZEN[0])
    code, out = _check(repo, capsys)
    assert code == 1 and _state_of(out, FROZEN[0]) == "UNATTRIBUTABLE"


def test_bare_session_id_trailer_matches_recorded_url(repo, capsys):
    _write(repo, FROZEN[0], "a = 42\n")
    _commit(repo, _project_trailer("session_S1"), FROZEN[0])
    code, out = _check(repo, capsys)
    assert code == 1 and "trailer is a plan session" in out


def test_url_trailer_matches_recorded_bare_session_id(tmp_path, capsys):
    r = _init(tmp_path / "repo")
    assert _run(r, "record-files", "--frozen", *FROZEN) == 0
    assert _run(r, "add-session", "session_S1") == 0
    _write(r, FROZEN[0], "a = 43\n")
    _commit(r, _project_trailer(S1), FROZEN[0])
    code, out = _check(r, capsys)
    assert code == 1 and "trailer is a plan session" in out


def test_session_id_is_not_a_substring_match(repo, capsys):
    _write(repo, FROZEN[0], "a = 44\n")
    _commit(repo, _project_trailer(S1 + "x"), FROZEN[0])
    code, out = _check(repo, capsys)
    assert code == 0 and _state_of(out, FROZEN[0]) == "ATTRIBUTED"


def test_false_pass_foreign_commit_plus_our_uncommitted_edit(repo, capsys):
    _write(repo, FROZEN[0], "a = 5\n")
    _commit(repo, _trailer(S2), FROZEN[0])
    _write(repo, FROZEN[0], "a = 5\nours = True\n")
    code, out = _check(repo, capsys)
    assert code == 1 and _state_of(out, FROZEN[0]) == "UNATTRIBUTABLE"
    assert "uncommitted delta on top of HEAD" in out


def test_one_bad_commit_among_foreign_ones(repo, capsys):
    _write(repo, FROZEN[0], "a = 6\n")
    _commit(repo, _trailer(S2), FROZEN[0])
    _write(repo, FROZEN[0], "a = 7\n")
    _commit(repo, "untrailed follow-up\n", FROZEN[0])
    code, out = _check(repo, capsys)
    assert code == 1 and _state_of(out, FROZEN[0]) == "UNATTRIBUTABLE"


def test_merge_hidden_untrailed_side_commit(repo, capsys):
    # Same change on both lines; default log simplification hides the side commit.
    _git(repo, "checkout", "-q", "-b", "side")
    _write(repo, FROZEN[0], "a = B\n")
    _commit(repo, "side change, NO trailer\n", FROZEN[0])
    _git(repo, "checkout", "-q", "main")
    _write(repo, FROZEN[0], "a = B\n")
    _commit(repo, _trailer(S2), FROZEN[0])
    _git(repo, "merge", "-q", "--no-ff", "-m", "merge side", "side")
    code, out = _check(repo, capsys)
    assert code == 1 and _state_of(out, FROZEN[0]) == "UNATTRIBUTABLE"
    assert "no Claude-Session trailer" in out


def test_mixed_commit_frozen_and_plan_owned_path(repo, capsys):
    _write(repo, FROZEN[0], "a = 8\n")
    _write(repo, "src/environment/dashboard/panels.py", "x = 1\n")
    _commit(repo, _trailer(S2), FROZEN[0], "src/environment/dashboard/panels.py")
    code, out = _check(repo, capsys)
    assert code == 1 and _state_of(out, FROZEN[0]) == "UNATTRIBUTABLE"
    assert "plan-owned" in out


def test_mixed_commit_with_campfire_test_world_config(repo, capsys):
    cfg = "configs/environment/experiment/basic/06-campfire_thermal_10x10.yaml"
    _write(repo, FROZEN[0], "a = 9\n")
    _write(repo, cfg, "x: 1\n")
    _commit(repo, _trailer(S2), FROZEN[0], cfg)
    code, out = _check(repo, capsys)
    assert code == 1 and _state_of(out, FROZEN[0]) == "UNATTRIBUTABLE"


def test_plan_owned_drift_in_baseline_does_not_narrow_rule(repo, capsys):
    _edit_baseline(repo, lambda d: d.__setitem__("plan_owned_paths", ["nothing/"]))
    _write(repo, FROZEN[0], "a = 10\n")
    _write(repo, "src/environment/dashboard/panels.py", "x = 1\n")
    _commit(repo, _trailer(S2), FROZEN[0], "src/environment/dashboard/panels.py")
    code, out = _check(repo, capsys)
    assert code == 1 and _state_of(out, FROZEN[0]) == "UNATTRIBUTABLE"
    assert "not in baseline" in out


def test_moved_content_with_no_commit(tmp_path, capsys):
    # Baseline taken on a dirty tree; the delta is later reverted with no commit.
    r = _init(tmp_path / "repo")
    _write(r, FROZEN[0], "a = 1\nwip\n")
    assert _run(r, "record-files", "--frozen", *FROZEN) == 0
    _write(r, FROZEN[0], "a = 1\n")
    code, out = _check(r, capsys)
    assert code == 1 and _state_of(out, FROZEN[0]) == "UNATTRIBUTABLE"


def test_accept_exact_content_then_reflag(repo, capsys):
    _write(repo, FROZEN[0], "a = 1\nthermal_wip = 1\n")
    sha = guard.sha256_file(repo / FROZEN[0])
    assert _run(repo, "accept", FROZEN[0], sha, "--note", "looked at it") == 0
    assert _baseline(repo)["frozen_files"][FROZEN[0]]["worktree_sha256"] != sha
    code, out = _check(repo, capsys)
    assert code == 0 and _state_of(out, FROZEN[0]) == "ACCEPTED"
    _write(repo, FROZEN[0], "a = 1\nthermal_wip = 2\n")
    code, out = _check(repo, capsys)
    assert code == 1 and _state_of(out, FROZEN[0]) == "UNATTRIBUTABLE"


def test_accept_refuses_sha_not_matching_current_content(repo, capsys):
    _write(repo, FROZEN[0], "a = 1\nx\n")
    capsys.readouterr()
    assert _run(repo, "accept", FROZEN[0], "0" * 64) == 2
    assert "currently hashes to" in capsys.readouterr().err
    assert _baseline(repo)["user_accepted"] == []


def test_accept_refuses_missing_file(repo, capsys):
    sha = guard.sha256_file(repo / FROZEN[0])
    (repo / FROZEN[0]).unlink()
    capsys.readouterr()
    assert _run(repo, "accept", FROZEN[0], sha) == 2
    assert "missing" in capsys.readouterr().err
    assert _baseline(repo)["user_accepted"] == []


def test_accept_rejects_non_frozen_and_bad_sha(repo):
    assert _run(repo, "accept", "README", "0" * 64) == 2
    assert _run(repo, "accept", FROZEN[0], "abc") == 2


# ------------------------------------------------------------------ loud failures


def test_missing_frozen_file(repo, capsys):
    (repo / FROZEN[0]).unlink()
    code, out = _check(repo, capsys)
    assert code == 1 and _state_of(out, FROZEN[0]) == "UNATTRIBUTABLE"


def test_symlinked_frozen_path_with_identical_bytes(repo, capsys):
    _write(repo, "elsewhere.py", "a = 1\n")
    (repo / FROZEN[0]).unlink()
    (repo / FROZEN[0]).symlink_to(repo / "elsewhere.py")
    code, out = _check(repo, capsys)
    assert code == 1 and _state_of(out, FROZEN[0]) == "UNATTRIBUTABLE"
    assert "symlink" in out


def test_repo_root_must_be_git_toplevel(repo, capsys):
    capsys.readouterr()
    assert guard.main(["--repo-root", str(repo / "src"), "check",
                       "--frozen", *FROZEN]) == 2
    assert "toplevel" in capsys.readouterr().err


def test_missing_baseline_is_guard_error(tmp_path, capsys):
    r = tmp_path / "empty"
    r.mkdir()
    _git(r, "init", "-q")
    code, out = _check(r, capsys)
    assert code == 2 and "baseline not found" in out


def test_zero_files_baseline_is_guard_error(repo, capsys):
    _edit_baseline(repo, lambda d: d.__setitem__("frozen_files", {}))
    code, out = _check(repo, capsys)
    assert code == 2 and "zero frozen files" in out


@pytest.mark.parametrize("mutate", [
    lambda d: d["frozen_files"][FROZEN[0]].pop("worktree_sha256"),
    lambda d: d["frozen_files"][FROZEN[0]].__setitem__("worktree_sha256", 5),
    lambda d: d["frozen_files"].__setitem__(FROZEN[0], "abc"),
    lambda d: d.__setitem__("plan_sessions", None),
    lambda d: d["plan_sessions"].append("01LG92Bg5jnSFoUMt4SaUUTk"),
    lambda d: d.__setitem__("plan_owned_paths", [3]),
    lambda d: d["user_accepted"].append({"path": FROZEN[0]}),
    lambda d: d.__setitem__("plan_start_commit", "HEAD"),
], ids=["no_sha", "sha_wrong_type", "entry_not_object", "sessions_null",
        "session_not_id", "owned_not_str", "accepted_no_sha", "start_not_oid"])
def test_malformed_baseline_is_guard_error(repo, capsys, mutate):
    _edit_baseline(repo, mutate)
    _write(repo, FROZEN[0], "a = 1\nx\n")  # force the non-PASS path too
    code, out = _check(repo, capsys)
    assert code == 2 and "malformed" in out


def test_binary_garbage_baseline_is_guard_error(repo, capsys):
    _bpath(repo).write_bytes(b"\xff\xfe\x00garbage")
    code, out = _check(repo, capsys)
    assert code == 2 and "not valid JSON" in out


def test_unexpected_exception_exits_2_not_1(repo, capsys, monkeypatch):
    def boom(args):
        raise RuntimeError("boom")
    monkeypatch.setattr(guard, "cmd_check", boom)
    code, out = _check(repo, capsys)
    assert code == 2 and "unexpected exception" in out


def test_frozen_set_mismatch_is_guard_error(repo, capsys):
    capsys.readouterr()
    code = _run(repo, "check", "--frozen", FROZEN[0])
    assert code == 2 and "does not match" in capsys.readouterr().err


def test_frame_baseline_present_but_uncheckable_is_guard_error(repo, capsys):
    _edit_baseline(repo, lambda d: d.__setitem__("frames", {"M1": ["deadbeef"]}))
    code, out = _check(repo, capsys)
    assert code == 2 and "frame" in out


def test_record_frames_refuses(repo):
    assert _run(repo, "record-frames") == 2


def test_canonical_frozen_set_is_ten_files():
    assert len(guard.FROZEN_FILES) == 10 == len(set(guard.FROZEN_FILES))


def test_cli_entry_point_exit_codes(repo):
    script = _REPO / "scripts" / "eval" / "v1_path_guard.py"
    cmd = [sys.executable, str(script), "--repo-root", str(repo), "check",
           "--frozen", *FROZEN]
    assert subprocess.run(cmd, capture_output=True).returncode == 0
    _write(repo, FROZEN[0], "mutated\n")
    assert subprocess.run(cmd, capture_output=True).returncode == 1
    _bpath(repo).write_text("{}")
    assert subprocess.run(cmd, capture_output=True).returncode == 2
