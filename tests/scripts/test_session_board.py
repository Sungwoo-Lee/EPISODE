"""Tests for scripts/claude/session_board.py (design: docs/develop/active/meta/session_board_design.md).

Fake sessions are real `sleep` processes, so the liveness check exercises the same /proc path as
production; the Claude registry and board directory are redirected to tmp dirs.
"""
import json
import os
import subprocess
import sys
import time

import pytest

_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(_REPO, "scripts", "claude"))

import session_board as sb  # noqa: E402

SCRIPT = os.path.join(_REPO, "scripts", "claude", "session_board.py")


@pytest.fixture
def board(tmp_path, monkeypatch):
    monkeypatch.setattr(sb, "BOARD", tmp_path / "board")
    monkeypatch.setattr(sb, "CARDS", tmp_path / "board" / "cards")
    monkeypatch.setattr(sb, "SEEN", tmp_path / "board" / "seen")
    monkeypatch.setattr(sb, "REGISTRY", tmp_path / "registry")
    (tmp_path / "registry").mkdir()
    procs = []

    def session(sid, name):
        p = subprocess.Popen(["sleep", "300"])
        procs.append(p)
        (tmp_path / "registry" / f"{p.pid}.json").write_text(json.dumps({"sessionId": sid, "name": name}))
        return p

    yield session
    for p in procs:
        p.kill()
        p.wait()


def hook(event, inp, pid, capsys, monkeypatch):
    monkeypatch.setattr(sb, "own_claude_pid", lambda: pid)
    sb.HANDLERS[event](inp, inp["session_id"], pid)
    out = capsys.readouterr().out
    return json.loads(out)["hookSpecificOutput"]["additionalContext"] if out else ""


def set_field(sid, **kw):
    c = sb.read_json(sb.card_path(sid))
    c.update(kw)
    sb.write_json(sb.card_path(sid), c)


def test_session_start_shows_other_sessions_and_delta_lifecycle(board, capsys, monkeypatch):
    a, b = board("A", "Sess A"), board("B", "Sess B")
    hook("SessionStart", {"session_id": "A", "source": "startup"}, a.pid, capsys, monkeypatch)
    out = hook("SessionStart", {"session_id": "B", "source": "startup"}, b.pid, capsys, monkeypatch)
    assert '"Sess A"' in out and sb.HEADER in out

    # nothing changed -> nothing injected
    assert hook("UserPromptSubmit", {"session_id": "B"}, b.pid, capsys, monkeypatch) == ""

    set_field("A", task="refactor loader", note="don't write ladder configs")
    sb.upsert_own("A", a.pid, touch_file="src/environment/config.py")
    out = hook("UserPromptSubmit", {"session_id": "B"}, b.pid, capsys, monkeypatch)
    assert "task now: refactor loader" in out
    assert "started editing: src/environment/config.py" in out
    assert "NOTE to all: don't write ladder configs" in out

    out = hook("UserPromptSubmit", {"session_id": "B"}, b.pid, capsys, monkeypatch)
    assert "Changed since" not in out   # already seen

    a.kill(); a.wait()
    out = hook("UserPromptSubmit", {"session_id": "B"}, b.pid, capsys, monkeypatch)
    assert '"Sess A" ended' in out


def test_new_session_reported(board, capsys, monkeypatch):
    b = board("B", "Sess B")
    hook("SessionStart", {"session_id": "B", "source": "startup"}, b.pid, capsys, monkeypatch)
    a = board("A", "Sess A")
    hook("SessionStart", {"session_id": "A", "source": "startup"}, a.pid, capsys, monkeypatch)
    assert '• NEW "Sess A"' in hook("UserPromptSubmit", {"session_id": "B"}, b.pid, capsys, monkeypatch)


def test_liveness_dead_reused_and_cleared_pid(board, capsys, monkeypatch, tmp_path):
    a = board("A", "Sess A")
    sb.upsert_own("A", a.pid, force=True)
    assert sb.alive(sb.read_json(sb.card_path("A")))
    set_field("A", proc_start="1")                                  # pid reused by another process
    assert not sb.alive(sb.read_json(sb.card_path("A")))
    set_field("A", proc_start=sb.proc_start(a.pid))
    (tmp_path / "registry" / f"{a.pid}.json").write_text(json.dumps({"sessionId": "A2"}))  # /clear
    assert not sb.alive(sb.read_json(sb.card_path("A")))
    (tmp_path / "registry" / f"{a.pid}.json").write_text(json.dumps({"sessionId": "A"}))
    a.kill(); a.wait()
    assert not sb.alive(sb.read_json(sb.card_path("A")))


def test_missing_card_of_live_session_is_not_reported_ended(board, capsys, monkeypatch):
    a, b = board("A", "Sess A"), board("B", "Sess B")
    hook("SessionStart", {"session_id": "A", "source": "startup"}, a.pid, capsys, monkeypatch)
    hook("SessionStart", {"session_id": "B", "source": "startup"}, b.pid, capsys, monkeypatch)
    sb.card_path("A").unlink()                  # simulates a half-finished rename on the NAS
    out = hook("UserPromptSubmit", {"session_id": "B"}, b.pid, capsys, monkeypatch)
    assert "ended" not in out


def test_edit_warning_only_for_other_sessions(board, capsys, monkeypatch):
    a, b = board("A", "Sess A"), board("B", "Sess B")
    for s, p in (("A", a), ("B", b)):
        hook("SessionStart", {"session_id": s, "source": "startup"}, p.pid, capsys, monkeypatch)
    edit = {"tool_name": "Edit", "tool_input": {"file_path": os.path.join(sb.REPO, "tmp/x.py")}, "cwd": str(sb.REPO)}
    hook("PostToolUse", {"session_id": "A", **edit}, a.pid, capsys, monkeypatch)
    assert hook("PreToolUse", {"session_id": "A", **edit}, a.pid, capsys, monkeypatch) == ""   # own file
    out = hook("PreToolUse", {"session_id": "B", **edit}, b.pid, capsys, monkeypatch)
    assert '⚠ "Sess A" edited tmp/x.py' in out
    other = {**edit, "tool_input": {"file_path": os.path.join(sb.REPO, "tmp/y.py")}}
    assert hook("PreToolUse", {"session_id": "B", **other}, b.pid, capsys, monkeypatch) == ""


def test_subagent_seen_is_separate_from_parent(board, capsys, monkeypatch):
    a, b = board("A", "Sess A"), board("B", "Sess B")
    hook("SessionStart", {"session_id": "A", "source": "startup"}, a.pid, capsys, monkeypatch)
    hook("SessionStart", {"session_id": "B", "source": "startup"}, b.pid, capsys, monkeypatch)
    set_field("A", task="new work")
    # sub-agent's first hook: inherits the parent's view, reports nothing
    assert hook("PostToolUse", {"session_id": "B", "agent_id": "sub1", "tool_name": "Read"}, b.pid, capsys, monkeypatch) == ""
    os.utime(sb.seen_path("B", "sub1"), (time.time() - 400, time.time() - 400))
    assert "task now: new work" in hook("PostToolUse", {"session_id": "B", "agent_id": "sub1", "tool_name": "Read"},
                                         b.pid, capsys, monkeypatch)
    # the parent still gets the change: the sub-agent seeing it did not mark it seen for the parent
    assert "task now: new work" in hook("UserPromptSubmit", {"session_id": "B"}, b.pid, capsys, monkeypatch)


def test_post_tool_is_throttled(board, capsys, monkeypatch):
    a, b = board("A", "Sess A"), board("B", "Sess B")
    hook("SessionStart", {"session_id": "A", "source": "startup"}, a.pid, capsys, monkeypatch)
    hook("SessionStart", {"session_id": "B", "source": "startup"}, b.pid, capsys, monkeypatch)
    set_field("A", task="x")
    assert hook("PostToolUse", {"session_id": "B", "tool_name": "Read"}, b.pid, capsys, monkeypatch) == ""
    os.utime(sb.seen_path("B"), (time.time() - 400, time.time() - 400))
    assert "task now: x" in hook("PostToolUse", {"session_id": "B", "tool_name": "Read"}, b.pid, capsys, monkeypatch)


def test_injected_text_is_sanitised_and_capped(board, capsys, monkeypatch):
    assert sb.clean("a\nb\x1b[31mc", 200) == "a b [31mc"
    assert len(sb.clean("x" * 500, 200)) == 200
    text = sb.wrap([f"line {i} " + "y" * 100 for i in range(50)])
    assert len(text) <= sb.OUT_CAP and "show" in text


@pytest.mark.parametrize("stdin", ["", "not json", "[1, 2]", '{"session_id": 5}', '{"session_id": "../../etc"}',
                                   '{"session_id": "zz", "tool_name": "Edit", "tool_input": 3}'])
@pytest.mark.parametrize("event", list(sb.HANDLERS))
def test_hook_command_never_fails(stdin, event, tmp_path):
    env = {**os.environ, "SESSION_BOARD_DIR": str(tmp_path)}
    cmd = f'{sb.PY} "{SCRIPT}" hook {event} || true'
    r = subprocess.run(["sh", "-c", cmd], input=stdin, capture_output=True, text=True, env=env, timeout=30)
    assert r.returncode == 0
    if r.stdout:   # a well-formed session id may legitimately produce output; it must be valid hook JSON
        assert json.loads(r.stdout)["hookSpecificOutput"]["hookEventName"] == event


def test_hook_command_survives_missing_interpreter():
    r = subprocess.run(["sh", "-c", f'/nonexistent/python "{SCRIPT}" hook UserPromptSubmit || true'],
                       input="{}", capture_output=True, text=True, timeout=30)
    assert r.returncode == 0 and r.stdout == ""
