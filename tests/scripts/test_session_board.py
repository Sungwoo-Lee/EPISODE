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
    monkeypatch.setattr(sb, "OFF", tmp_path / "board" / "OFF")
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


def test_control_chars_stripped_and_text_capped(board, capsys, monkeypatch):
    assert sb.clean("a\nb\x1b[31mc", 200) == "a b [31mc"
    assert len(sb.clean("x" * 500, 200)) == 200
    text = sb.wrap([f"line {i} " + "y" * 100 for i in range(50)])
    assert len(text) <= sb.OUT_CAP and "more line(s)" in text


@pytest.mark.parametrize("stdin", ["", "not json", "[1, 2]", '{"session_id": 5}', '{"session_id": "../../etc"}',
                                   '{"session_id": "zz", "tool_name": "Edit", "tool_input": 3}'])
@pytest.mark.parametrize("event", list(sb.HANDLERS))
def test_hook_command_never_fails(stdin, event, tmp_path):
    env = {**os.environ, "SESSION_BOARD_DIR": str(tmp_path)}
    r = subprocess.run([sb.PY, SCRIPT, "hook", event], input=stdin, capture_output=True, text=True, env=env, timeout=30)
    assert r.returncode == 0      # the script's own exit code, not masked by `|| true`
    assert r.stderr == ""
    if r.stdout:   # a well-formed session id may legitimately produce output; it must be valid hook JSON
        assert json.loads(r.stdout)["hookSpecificOutput"]["hookEventName"] == event


def test_hook_command_survives_missing_interpreter():
    r = subprocess.run(["sh", "-c", f'/nonexistent/python "{SCRIPT}" hook UserPromptSubmit || true'],
                       input="{}", capture_output=True, text=True, timeout=30)
    assert r.returncode == 0 and r.stdout == ""


# ------------------------------------------------------------------ added after code review (2026-09-30)
def many_sessions(board, capsys, monkeypatch, n):
    procs = []
    for i in range(n):
        p = board(f"S{i}", f"Session number {i}")
        hook("SessionStart", {"session_id": f"S{i}", "source": "startup"}, p.pid, capsys, monkeypatch)
        set_field(f"S{i}", task="a fairly long task description " * 5)
        procs.append(p)
    return procs


def test_instructions_survive_many_sessions(board, capsys, monkeypatch):
    many_sessions(board, capsys, monkeypatch, 12)
    me = board("ME", "Me")
    out = hook("SessionStart", {"session_id": "ME", "source": "startup"}, me.pid, capsys, monkeypatch)
    assert "BOARD task" in out and "more line(s)" in out
    assert len(out) <= sb.FULL_CAP


def test_long_collision_warning_is_cut_not_replaced(board, capsys, monkeypatch):
    procs = many_sessions(board, capsys, monkeypatch, 10)
    edit = {"tool_name": "Edit", "tool_input": {"file_path": os.path.join(sb.REPO, "tmp/z.py")}, "cwd": str(sb.REPO)}
    for i, p in enumerate(procs):
        hook("PostToolUse", {"session_id": f"S{i}", **edit}, p.pid, capsys, monkeypatch)
    me = board("ME", "Me")
    hook("SessionStart", {"session_id": "ME", "source": "startup"}, me.pid, capsys, monkeypatch)
    out = hook("PreToolUse", {"session_id": "ME", **edit}, me.pid, capsys, monkeypatch)
    assert out.count("⚠") >= 1 and "more line(s)" in out and len(out) <= sb.WARN_CAP


def test_busy_session_at_rollout_is_onboarded_by_first_tool_hook(board, capsys, monkeypatch):
    a, b = board("A", "Sess A"), board("B", "Sess B")
    hook("SessionStart", {"session_id": "A", "source": "startup"}, a.pid, capsys, monkeypatch)
    # B was running before the board existed: no SessionStart, first hook is a tool call
    out = hook("PostToolUse", {"session_id": "B", "tool_name": "Read"}, b.pid, capsys, monkeypatch)
    assert '"Sess A"' in out and "BOARD task" in out
    assert hook("UserPromptSubmit", {"session_id": "B"}, b.pid, capsys, monkeypatch) == ""   # not repeated


def test_subagent_before_parent_onboarded_stays_silent(board, capsys, monkeypatch):
    b = board("B", "Sess B")
    assert hook("PostToolUse", {"session_id": "B", "agent_id": "x", "tool_name": "Read"}, b.pid, capsys, monkeypatch) == ""
    assert not sb.seen_path("B", "x").exists()
    assert "BOARD task" in hook("PostToolUse", {"session_id": "B", "tool_name": "Read"}, b.pid, capsys, monkeypatch)


def test_idle_session_at_rollout_gets_full_board_on_first_prompt(board, capsys, monkeypatch):
    a, b = board("A", "Sess A"), board("B", "Sess B")
    hook("SessionStart", {"session_id": "A", "source": "startup"}, a.pid, capsys, monkeypatch)
    out = hook("UserPromptSubmit", {"session_id": "B"}, b.pid, capsys, monkeypatch)
    assert '"Sess A"' in out and "BOARD task" in out and "has no task" not in out


def test_kill_switch_silences_hooks(board, capsys, monkeypatch, tmp_path):
    board_dir = tmp_path / "killswitch"
    board_dir.mkdir()
    (board_dir / "OFF").touch()
    env = {**os.environ, "SESSION_BOARD_DIR": str(board_dir)}
    r = subprocess.run([sb.PY, SCRIPT, "hook", "SessionStart"], input='{"session_id": "zz", "source": "startup"}',
                       capture_output=True, text=True, env=env, timeout=30)
    assert r.returncode == 0 and r.stdout == "" and not (board_dir / "cards").exists()


def test_task_note_commands_and_task_of(board, capsys, monkeypatch):
    a = board("A", "Sess A")
    hook("SessionStart", {"session_id": "A", "source": "startup"}, a.pid, capsys, monkeypatch)
    sb.main(["task", "doing", "things"])
    sb.main(["note", "careful\nnow"])
    c = sb.read_json(sb.card_path("A"))
    assert c["task"] == "doing things" and c["note"] == "careful now" and c["note_set"]
    capsys.readouterr()
    sb.main(["task-of", str(a.pid)])
    assert capsys.readouterr().out.strip() == "doing things"
    sb.main(["note", "--clear"])
    assert sb.read_json(sb.card_path("A"))["note"] == ""
    for bad in (["task"], ["task", "  "], ["note"]):
        with pytest.raises(SystemExit):
            sb.main(bad)
    assert sb.read_json(sb.card_path("A"))["task"] == "doing things"


def test_hook_write_does_not_revert_a_concurrent_task(board, capsys, monkeypatch):
    a = board("A", "Sess A")
    hook("SessionStart", {"session_id": "A", "source": "startup"}, a.pid, capsys, monkeypatch)
    real_read = sb.read_json
    stale = real_read(sb.card_path("A"))            # the hook read the card before `task` ran ...
    set_field("A", task="set meanwhile")             # ... then `task` wrote ...
    reads = []

    def first_read_stale(p):
        if p == sb.card_path("A") and not reads:
            reads.append(p)
            return dict(stale)
        return real_read(p)

    monkeypatch.setattr(sb, "read_json", first_read_stale)
    sb.upsert_own("A", a.pid, touch_file="tmp/q.py")  # ... and now the hook saves
    card = real_read(sb.card_path("A"))
    assert card["task"] == "set meanwhile" and card["files"][0]["path"] == "tmp/q.py"


def test_clear_retires_old_card_on_same_pid(board, capsys, monkeypatch, tmp_path):
    a = board("A", "Sess A")
    hook("SessionStart", {"session_id": "A", "source": "startup"}, a.pid, capsys, monkeypatch)
    (tmp_path / "registry" / f"{a.pid}.json").write_text(json.dumps({"sessionId": "A2", "name": "Sess A"}))
    hook("SessionStart", {"session_id": "A2", "source": "clear"}, a.pid, capsys, monkeypatch)
    assert not sb.card_path("A").exists() and sb.card_path("A2").exists()


def test_task_reminder_at_most_hourly(board, capsys, monkeypatch):
    b = board("B", "Sess B")
    hook("SessionStart", {"session_id": "B", "source": "startup"}, b.pid, capsys, monkeypatch)
    assert "has no task" not in hook("UserPromptSubmit", {"session_id": "B"}, b.pid, capsys, monkeypatch)
    seen = sb.read_json(sb.seen_path("B")); seen["last_nag"] = time.time() - 4000; sb.write_json(sb.seen_path("B"), seen)
    assert "has no task" in hook("UserPromptSubmit", {"session_id": "B"}, b.pid, capsys, monkeypatch)
    assert "has no task" not in hook("UserPromptSubmit", {"session_id": "B"}, b.pid, capsys, monkeypatch)


def test_sweep_removes_dead_local_cards_and_their_seen(board, capsys, monkeypatch):
    a, b = board("A", "Sess A"), board("B", "Sess B")
    hook("SessionStart", {"session_id": "A", "source": "startup"}, a.pid, capsys, monkeypatch)
    hook("SessionStart", {"session_id": "B", "source": "startup"}, b.pid, capsys, monkeypatch)
    a.kill(); a.wait()
    sb.sweep()
    assert not sb.card_path("A").exists() and not sb.seen_path("A").exists()
    assert sb.card_path("B").exists()
    # B still learns that A ended, even though A's card is already gone
    assert '"Sess A" ended' in hook("UserPromptSubmit", {"session_id": "B"}, b.pid, capsys, monkeypatch)


def test_foreign_machine_card_uses_heartbeat(board, capsys, monkeypatch):
    a = board("A", "Sess A")
    sb.upsert_own("A", a.pid, force=True)
    set_field("A", pid_domain="other-machine:pid:[1]", updated=time.time())
    assert sb.alive(sb.read_json(sb.card_path("A")))
    set_field("A", updated=time.time() - 3600)
    assert not sb.alive(sb.read_json(sb.card_path("A")))
