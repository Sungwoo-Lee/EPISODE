---
name: tmux-claude
description: "Inspect and control the Claude Code sessions the user runs inside tmux (they use tmux instead of `claude bg` because bg sessions sleep after an hour idle). Use for: listing tmux sessions/panes and which Claude conversation runs in each; peeking at a pane's screen; reading the latest user/assistant messages of a pane's conversation; restarting (rebooting) a pane's Claude so it resumes the SAME conversation; creating a new tmux session with a new Claude; waking an asleep (not running) Claude conversation into a new tmux session; terminating a pane's Claude. Every start/restart runs in the project directory with `--permission-mode bypassPermissions` and Remote Control, and is VERIFIED to have Remote Control on. Trigger on /tmux-claude, 'list the tmux sessions', 'what is running in tmux', 'restart/reboot the <name> session', 'open a new tmux claude session', 'kill/terminate window N', 'what did I last say in <pane>', 'recent sessions', 'wake up the <title> session'."
---

# /tmux-claude — drive Claude sessions living in tmux

All mechanics are in `tmux_claude.sh` next to this file. Run it; don't re-implement it with raw
`tmux send-keys`.

```
S=.claude/skills/tmux-claude/tmux_claude.sh
$S list                          # every pane: claude PID, session id, name, status, Remote Control (ON/OFF), TASK from the session board
$S recent [n]                    # recent Claude conversations, newest first: title, where running ('asleep' = none), last user msg
$S wake   <session-id> <tmux-name># resume an asleep conversation in a NEW tmux session (id prefix ok), then verify
$S peek   <target> [lines]       # what the pane shows right now (menus, pending questions)
$S last   <target|session-id> [n]# last n user/assistant messages from the conversation transcript
$S restart <target> [--force]    # /exit, then relaunch resuming the SAME conversation, then verify
$S new    <tmux-name> [display]  # new detached tmux session in the project dir + new claude, then verify
$S kill   <target> [--force]     # /exit claude, close the pane, print the resume command
$S verify <target>               # re-check bypass mode + Remote Control (turns RC on if off)
```

`<target>` is a tmux pane in `session:window.pane` form, as printed by `list` (e.g. `dev-temp:2.0`).

## Rules

1. **Remote Control must be ON after every start or restart.** Every launch passes `--remote-control`.
   `verify` then waits until the session's `bridgeSessionId` in `~/.claude/sessions/<pid>.json` is
   set. If it isn't, `verify` sends `/remote-control` to the pane and checks again, and exits with
   code 2 if it still fails. Report the Remote Control line to the user, and never report success
   on exit 2.
2. **Always launch from the project dir** (`/media/nas01/projects/Interoceptive-AI/grid_world_pain`)
   with `--permission-mode bypassPermissions`. The script does both.
3. **Look before acting.** Before a restart or kill, run `peek` (and `last` if it helps), then tell
   the user what the pane is doing. A pane showing a question menu or unread messages loses that
   menu on restart. The conversation itself is kept.
4. **Never interrupt a busy session unasked.** `restart` and `kill` refuse when status is `busy`.
   Pass `--force` only when the user explicitly agreed to interrupt it. `busy` is mid-turn;
   `idle` / `waiting` are safe.
5. **Restart resumes, it doesn't start fresh**, unless the user asks for a fresh session.
6. **Check the model after a restart.** A resumed session takes the model from its own history, which
   may differ from what it showed before (seen 2026-09-26: Opus 5.5 → Opus 5). `peek` the status bar
   and tell the user if it changed.
7. **One of the panes is probably you.** `list` shows this session too. Never restart or kill your
   own pane.

## Test launches

`new`, `wake` and `restart` read two optional environment variables, meant for throwaway test sessions:

- `TMUX_CLAUDE_EXTRA`: extra `claude` flags, e.g. `"--model haiku --settings tmp/session_board_test_settings.json"`.
- `TMUX_CLAUDE_ENV`: environment assignments put before `claude`, e.g. `"SESSION_BOARD_DIR=/abs/path/tmp/board_test"`.

Both are expanded unquoted, so they can hold several flags, but a single value that itself contains spaces
cannot be passed. The script prints only whether Remote Control is on; the bridge ID is in
`~/.claude/sessions/<pid>.json` if needed.

## Typing into a pane

Before sending a message with `tmux send-keys`, check whether the text after `❯` on the prompt line is
Claude's greyed-out **suggestion** or a **draft the user typed**. Typing replaces a suggestion, but it is
appended to a draft and then sent together with it. Check with
`tmux capture-pane -e -p -t <target> | grep -a '❯' | tail -1 | cat -v`: text wrapped in `^[[2m` (dim) is a
suggestion. Anything else is the user's draft, so don't type into that pane; ask the user. Send
messages with `send-keys -l "<text>"` (literal), then `Enter` separately. Start the message with who is
sending it (e.g. `[From the Admin session, on the user's instruction]`), so the receiving session knows
it didn't come from the user directly.

## Notes

- Two panes can hold the same line of work: a conversation that was `/compact`ed and resumed
  elsewhere is a newer continuation. Use `last` on both to tell which one is live before killing
  either.
- A new session's first launch in a folder may show a trust prompt. `new` accepts it.
- Exit code: 0 ok, 1 error (message on stderr), 2 Remote Control could not be enabled.
