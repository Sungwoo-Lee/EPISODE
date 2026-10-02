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
    monkeypatch.setattr(sb, "TARGET", tmp_path / "board" / "TARGET_BRANCH")
    monkeypatch.setattr(sb, "DIVERGENCE", tmp_path / "board" / "divergence.json")
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
    assert '⚠ "Sess A"' in out and "edited tmp/x.py" in out   # a branch tag may sit between them
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


# ------------------------------------------------------------------ 7-day expiry of live-but-inactive cards (2026-09-30)
def test_quiet_live_session_expires_and_rejoins_clean(board, capsys, monkeypatch):
    a, b = board("A", "Sess A"), board("B", "Sess B")
    hook("SessionStart", {"session_id": "A", "source": "startup"}, a.pid, capsys, monkeypatch)
    hook("SessionStart", {"session_id": "B", "source": "startup"}, b.pid, capsys, monkeypatch)
    set_field("A", task="old work", note="old note", updated=time.time() - sb.EXPIRE - 60)
    card = sb.read_json(sb.card_path("A"))
    assert sb.process_alive(card) and not sb.alive(card)          # process still running, card expired
    out = hook("UserPromptSubmit", {"session_id": "B"}, b.pid, capsys, monkeypatch)
    assert '"Sess A" went quiet' in out and "ended" not in out
    assert "Sess A" not in "\n".join(sb.full_board("B"))
    # A comes back: fresh card without the stale task; B sees it rejoin
    hook("UserPromptSubmit", {"session_id": "A"}, a.pid, capsys, monkeypatch)
    card = sb.read_json(sb.card_path("A"))
    assert card["task"] == "" and card["note"] == "" and sb.alive(card)
    assert '• NEW "Sess A"' in hook("UserPromptSubmit", {"session_id": "B"}, b.pid, capsys, monkeypatch)


def test_expired_card_swept_is_reported_quiet_not_ended(board, capsys, monkeypatch):
    a, b = board("A", "Sess A"), board("B", "Sess B")
    hook("SessionStart", {"session_id": "A", "source": "startup"}, a.pid, capsys, monkeypatch)
    hook("SessionStart", {"session_id": "B", "source": "startup"}, b.pid, capsys, monkeypatch)
    set_field("A", updated=time.time() - sb.EXPIRE - 60)
    seen = sb.read_json(sb.seen_path("B"))
    seen["cards"]["A"]["updated"] = time.time() - sb.EXPIRE - 60
    sb.write_json(sb.seen_path("B"), seen)
    sb.sweep()
    assert not sb.card_path("A").exists()
    assert '"Sess A" went quiet' in hook("UserPromptSubmit", {"session_id": "B"}, b.pid, capsys, monkeypatch)


# ------------------------------------------------------------------ worktrees share the main board (2026-09-30)
def test_main_repo_resolves_worktree_to_main_checkout(tmp_path):
    main = tmp_path / "main"
    (main / ".git" / "worktrees" / "wt1").mkdir(parents=True)
    wt = tmp_path / "wt1"
    wt.mkdir()
    (wt / ".git").write_text(f"gitdir: {main}/.git/worktrees/wt1\n")
    assert sb.main_repo(wt) == main
    assert sb.main_repo(main) == main                      # the main checkout itself: .git is a directory
    odd = tmp_path / "sub"; odd.mkdir(); (odd / ".git").write_text("gitdir: /somewhere/else/modules/x\n")
    assert sb.main_repo(odd) == odd                        # submodule-style pointer: left alone
    assert sb.main_repo(tmp_path / "nope") == tmp_path / "nope"


# ------------------------------------------------------------------ branch awareness (2026-10-02)
def fake_checkout(root, branch=None, sha=None):
    (root / ".git").mkdir(parents=True)
    (root / ".git" / "HEAD").write_text(f"ref: refs/heads/{branch}\n" if branch else f"{sha}\n")
    return root


def fake_worktree(main, name, branch):
    gd = main / ".git" / "worktrees" / name
    gd.mkdir(parents=True)
    (gd / "HEAD").write_text(f"ref: refs/heads/{branch}\n")
    wt = main / ".claude" / "worktrees" / name
    wt.mkdir(parents=True)
    (wt / ".git").write_text(f"gitdir: {gd}\n")
    return wt


def set_target(name):
    sb.TARGET.parent.mkdir(parents=True, exist_ok=True)
    sb.TARGET.write_text(name + "\n")


def test_git_head_shared_worktree_and_detached(tmp_path, monkeypatch):
    main = fake_checkout(tmp_path / "repo", branch="v4.0")
    monkeypatch.setattr(sb, "REPO", main)
    (main / "src" / "x").mkdir(parents=True)
    assert sb.git_head(main / "src" / "x") == ("v4.0", "shared")
    wt = fake_worktree(main, "thirst", "v5.0")
    assert sb.git_head(wt) == ("v5.0", "worktree thirst")
    det = fake_checkout(tmp_path / "det", sha="583b022f941647d362c5795012ad607ea422e3ab")
    assert sb.git_head(det)[0] == "detached@583b022f"
    assert sb.git_head(tmp_path / "nowhere") == (None, None)


def test_off_target_rules(board):
    assert not sb.off_target("v4.0")                     # no working branch set: never flagged
    set_target("v5.0")
    assert sb.off_target("v4.0") and not sb.off_target("v5.0")
    assert not sb.off_target("detached@583b022f") and not sb.off_target("worktree-agent-ab12")
    assert not sb.off_target(None)


def test_card_shows_branch_and_prompt_warns_off_target(board, capsys, monkeypatch, tmp_path):
    main = fake_checkout(tmp_path / "repo", branch="v4.0")
    monkeypatch.setattr(sb, "REPO", main)
    set_target("v5.0")
    monkeypatch.setattr(sb, "divergence", lambda force=False: [])
    a, b = board("A", "Sess A"), board("B", "Sess B")
    hook("SessionStart", {"session_id": "A", "source": "startup", "cwd": str(main)}, a.pid, capsys, monkeypatch)
    out = hook("SessionStart", {"session_id": "B", "source": "startup", "cwd": str(main)}, b.pid, capsys, monkeypatch)
    assert '"Sess A" [on v4.0] ⚠ not the working branch' in out
    assert "Working branch for this project: v5.0." in out and "You are on branch v4.0" in out
    for _ in range(2):                                    # every prompt, not just once
        assert "You are on branch v4.0" in hook("UserPromptSubmit", {"session_id": "B", "cwd": str(main)},
                                                 b.pid, capsys, monkeypatch)
    sb.TARGET.write_text("v4.0\n")                        # now on the working branch: silent
    assert "You are on branch" not in hook("UserPromptSubmit", {"session_id": "B", "cwd": str(main)},
                                           b.pid, capsys, monkeypatch)


def test_branch_change_is_reported(board, capsys, monkeypatch, tmp_path):
    main = fake_checkout(tmp_path / "repo", branch="v4.0")
    monkeypatch.setattr(sb, "REPO", main)
    wt = fake_worktree(main, "thirst", "v5.0")
    a, b = board("A", "Sess A"), board("B", "Sess B")
    hook("SessionStart", {"session_id": "A", "source": "startup", "cwd": str(main)}, a.pid, capsys, monkeypatch)
    hook("SessionStart", {"session_id": "B", "source": "startup", "cwd": str(main)}, b.pid, capsys, monkeypatch)
    hook("UserPromptSubmit", {"session_id": "A", "cwd": str(wt)}, a.pid, capsys, monkeypatch)   # A moves to the worktree
    out = hook("UserPromptSubmit", {"session_id": "B", "cwd": str(main)}, b.pid, capsys, monkeypatch)
    assert "now on branch v5.0" in out and "worktree thirst" in out


@pytest.mark.parametrize("command,warn", [
    ("git commit -m x", True),
    ("timeout 60 git commit -q -F msg -- a b", True),
    ("git add a && git commit -m x", True),
    ("git status", False),
    ("echo commit", False),
])
def test_commit_warning_on_wrong_branch(board, capsys, monkeypatch, tmp_path, command, warn):
    main = fake_checkout(tmp_path / "repo", branch="v4.0")
    monkeypatch.setattr(sb, "REPO", main)
    set_target("v5.0")
    a = board("A", "Sess A")
    out = hook("PreToolUse", {"session_id": "A", "tool_name": "Bash", "tool_input": {"command": command},
                              "cwd": str(main)}, a.pid, capsys, monkeypatch)
    assert ("would land on branch v4.0" in out) == warn


def test_commit_warning_follows_git_C_and_cd(board, capsys, monkeypatch, tmp_path):
    main = fake_checkout(tmp_path / "repo", branch="v5.0")
    monkeypatch.setattr(sb, "REPO", main)
    old = fake_worktree(main, "old", "v4.0")
    set_target("v5.0")
    a = board("A", "Sess A")
    ev = lambda cmd: hook("PreToolUse", {"session_id": "A", "tool_name": "Bash", "tool_input": {"command": cmd},
                                         "cwd": str(main)}, a.pid, capsys, monkeypatch)
    assert ev("git commit -m x") == ""                               # cwd is on the working branch
    assert "would land on branch v4.0" in ev(f'git -C "{old}" commit -m x')
    assert "would land on branch v4.0" in ev(f"cd {old} && git commit -m x")


def make_git_repo(path):
    import subprocess
    run = lambda *a: subprocess.run(["git", "-C", str(path), *a], check=True, capture_output=True)
    path.mkdir()
    run("init", "-q", "-b", "v4.0")
    run("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "base")
    run("branch", "v5.0")
    run("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "late v4.0 work")
    return path


def test_divergence_counts_commits_missing_from_working_branch(board, monkeypatch, tmp_path):
    repo = make_git_repo(tmp_path / "gitrepo")
    monkeypatch.setattr(sb, "REPO", repo)
    set_target("v5.0")
    assert sb.divergence(force=True) == [("v4.0", 1)]
    assert "v4.0 has 1" in "\n".join(sb.branch_lines())
    cached = sb.read_json(sb.DIVERGENCE)
    assert cached["target"] == "v5.0" and cached["gaps"] == [["v4.0", 1]]
    set_target("v4.0")                                    # v5.0 has nothing v4.0 lacks
    assert sb.divergence(force=True) == []


def test_divergence_is_cached_and_survives_git_failure(board, monkeypatch, tmp_path):
    repo = make_git_repo(tmp_path / "gitrepo")
    monkeypatch.setattr(sb, "REPO", repo)
    set_target("v5.0")
    assert sb.divergence(force=True) == [("v4.0", 1)]
    import subprocess
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: (_ for _ in ()).throw(subprocess.TimeoutExpired("git", 1)))
    assert sb.divergence() == [("v4.0", 1)]               # fresh cache: no git call at all
    assert sb.divergence(force=True) == [("v4.0", 1)]     # git fails: last known value, no crash


def test_target_command(board, capsys, monkeypatch, tmp_path):
    repo = make_git_repo(tmp_path / "gitrepo")
    monkeypatch.setattr(sb, "REPO", repo)
    sb.BOARD.mkdir(parents=True, exist_ok=True)
    sb.main(["target", "v5.0"])
    assert sb.target_branch() == "v5.0" and "v4.0 has 1" in capsys.readouterr().out
    sb.main(["target", "--clear"])
    assert sb.target_branch() is None
