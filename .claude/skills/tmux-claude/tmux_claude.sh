#!/usr/bin/env bash
# tmux_claude.sh — inspect and control Claude Code sessions running inside tmux panes.
# Usage: see .claude/skills/tmux-claude/SKILL.md
set -uo pipefail

PROJECT_DIR=/media/nas01/projects/Interoceptive-AI/grid_world_pain
PY=/home/vncuser/miniconda3/envs/grid_world_pain/bin/python
SESS_DIR="$HOME/.claude/sessions"
TRANSCRIPTS="$HOME/.claude/projects/-media-nas01-projects-Interoceptive-AI-grid-world-pain"
CLAUDE_FLAGS="--permission-mode bypassPermissions"

die() { echo "ERROR: $*" >&2; exit 1; }

# Claude PID running directly under a pane's shell (empty if none).
claude_pid() {
  local shell_pid
  shell_pid=$(tmux display -p -t "$1" '#{pane_pid}' 2>/dev/null) || die "no such tmux target: $1"
  pgrep -P "$shell_pid" -f '(^|/)claude( |$)' | head -1
}

# Field from ~/.claude/sessions/<pid>.json ('' if missing/null).
sess_field() {
  local f="$SESS_DIR/$1.json"
  [ -f "$f" ] || { echo ""; return; }
  "$PY" -c "import json,sys;v=json.load(open(sys.argv[1])).get(sys.argv[2]);print('' if v is None else v)" "$f" "$2"
}

cmd_list() {
  printf '%-22s %-9s %-38s %-26s %-8s %s\n' TARGET PID SESSION_ID NAME STATUS REMOTE_CONTROL
  tmux list-panes -a -F '#{session_name}:#{window_index}.#{pane_index}' 2>/dev/null | while read -r t; do
    local pid; pid=$(claude_pid "$t")
    if [ -z "$pid" ]; then
      printf '%-22s %-9s %s\n' "$t" "-" "(no claude: $(tmux display -p -t "$t" '#{pane_current_command}'))"
      continue
    fi
    local rc; rc=$(sess_field "$pid" bridgeSessionId)
    printf '%-22s %-9s %-38s %-26s %-8s %s\n' "$t" "$pid" "$(sess_field "$pid" sessionId)" \
      "$(sess_field "$pid" name)" "$(sess_field "$pid" status)" "$([ -n "$rc" ] && echo "ON ($rc)" || echo OFF)"
  done
}

cmd_peek() {  # peek <target> [lines]
  tmux capture-pane -p -t "$1" -S -200 | grep -v '^\s*$' | tail -"${2:-30}"
}

cmd_last() {  # last <target|session-id> [n]  — last n user/assistant messages from the transcript
  local sid="$1"
  if [[ ! "$sid" =~ ^[0-9a-f-]{36}$ ]]; then
    local pid; pid=$(claude_pid "$1"); [ -n "$pid" ] || die "no claude in $1"
    sid=$(sess_field "$pid" sessionId)
  fi
  "$PY" - "$TRANSCRIPTS/$sid.jsonl" "${2:-6}" <<'EOF'
import json, sys
rows = []
for line in open(sys.argv[1]):
    try: d = json.loads(line)
    except Exception: continue
    if d.get('type') not in ('user', 'assistant') or d.get('isSidechain') or d.get('isMeta') or d.get('isCompactSummary'):
        continue
    c = d['message'].get('content')
    t = ' '.join(x.get('text', '') for x in c if x.get('type') == 'text') if isinstance(c, list) else (c or '')
    t = t.strip()
    if not t or t.startswith(('<command', '<local-command', '<system-reminder', '<task-notification', 'This session is being continued')):
        continue
    rows.append((d.get('timestamp', '')[:16], d['type'].upper(), t))
for ts, who, t in rows[-int(sys.argv[2]):]:
    print(f"--- [{ts}] {who}\n{t[:900]}\n")
EOF
}

# Wait for Claude to appear in a pane, then confirm Remote Control; toggle it on if missing.
verify() {  # verify <target>
  local t="$1" pid="" rc="" i
  for i in $(seq 1 30); do pid=$(claude_pid "$t"); [ -n "$pid" ] && [ -f "$SESS_DIR/$pid.json" ] && break; sleep 1; done
  [ -n "$pid" ] || die "claude did not start in $t — check: tmux_claude.sh peek $t"
  for i in $(seq 1 30); do rc=$(sess_field "$pid" bridgeSessionId); [ -n "$rc" ] && break; sleep 1; done
  if [ -z "$rc" ]; then
    echo "Remote Control not on yet — sending /remote-control"
    tmux send-keys -t "$t" '/remote-control'; sleep 1; tmux send-keys -t "$t" Enter
    for i in $(seq 1 30); do rc=$(sess_field "$pid" bridgeSessionId); [ -n "$rc" ] && break; sleep 1; done
  fi
  echo "target=$t pid=$pid session=$(sess_field "$pid" sessionId) name=$(sess_field "$pid" name) status=$(sess_field "$pid" status)"
  echo "permission-mode: $(tr '\0' ' ' < /proc/$pid/cmdline | grep -q bypassPermissions && echo bypassPermissions || echo NOT-bypass)"
  if [ -n "$rc" ]; then echo "remote-control: ON ($rc)"; else echo "remote-control: OFF — FAILED to enable"; exit 2; fi
}

# Exit Claude in a pane gracefully (/exit), refusing if busy unless --force.
exit_claude() {  # exit_claude <target> <force>
  local t="$1" pid status i
  pid=$(claude_pid "$t"); [ -n "$pid" ] || die "no claude running in $t"
  status=$(sess_field "$pid" status)
  if [ "$status" = "busy" ] && [ "$2" != "--force" ]; then
    die "$t is busy (working). Re-run with --force only if the user agreed to interrupt it."
  fi
  tmux send-keys -t "$t" Escape; sleep 1
  tmux send-keys -t "$t" '/exit'; sleep 1; tmux send-keys -t "$t" Enter
  for i in $(seq 1 20); do kill -0 "$pid" 2>/dev/null || break; sleep 1; done
  kill -0 "$pid" 2>/dev/null && die "claude $pid did not exit after /exit"
  echo "exited: $t (pid $pid, session $SESSION_ID)"
}

cmd_restart() {  # restart <target> [--force]  — exit and resume the same conversation
  local t="$1" pid
  pid=$(claude_pid "$t"); [ -n "$pid" ] || die "no claude running in $t"
  SESSION_ID=$(sess_field "$pid" sessionId); [ -n "$SESSION_ID" ] || die "cannot find session id for pid $pid"
  exit_claude "$t" "${2:-}"
  tmux send-keys -t "$t" "cd $PROJECT_DIR && claude $CLAUDE_FLAGS --resume $SESSION_ID --remote-control" Enter
  verify "$t"
}

cmd_new() {  # new <tmux-session-name> [display-name]
  local name="$1" disp="${2:-}"
  tmux has-session -t "=$name" 2>/dev/null && die "tmux session '$name' already exists"
  tmux new-session -d -s "$name" -c "$PROJECT_DIR"
  local t; t=$(tmux list-panes -t "=$name" -F '#{session_name}:#{window_index}.#{pane_index}' | head -1)
  local cmd="cd $PROJECT_DIR && claude $CLAUDE_FLAGS"
  [ -n "$disp" ] && cmd+=" --name $(printf %q "$disp")"
  tmux send-keys -t "$t" "$cmd --remote-control" Enter
  sleep 3
  # First launch in a directory may show a trust prompt; accept it.
  if tmux capture-pane -p -t "$t" | grep -qi 'trust this folder\|Do you trust'; then tmux send-keys -t "$t" Enter; fi
  verify "$t"
}

cmd_recent() {  # recent [n]  — recent conversations, newest first, with title, where it runs, last user message
  "$PY" - "$TRANSCRIPTS" "$SESS_DIR" "${1:-20}" <<'EOF'
import json, os, glob, time, sys
tdir, sdir, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
live = {}
for f in glob.glob(os.path.join(sdir, '*.json')):
    try: d = json.load(open(f))
    except Exception: continue
    if os.path.exists('/proc/%d' % d['pid']):
        live[d['sessionId']] = (d.get('tmux') or d.get('kind') or 'running').split(':@')[0]
shown = 0
for f in sorted(glob.glob(os.path.join(tdir, '*.jsonl')), key=os.path.getmtime, reverse=True):
    sid = os.path.basename(f)[:-6]; title = None; last = None; nuser = 0
    for line in open(f):
        try: d = json.loads(line)
        except Exception: continue
        if d.get('type') == 'custom-title': title = d.get('customTitle')
        if d.get('type') == 'user' and not (d.get('isSidechain') or d.get('isMeta') or d.get('isCompactSummary')):
            c = d['message'].get('content')
            t = c if isinstance(c, str) else ' '.join(x.get('text', '') for x in c if isinstance(x, dict) and x.get('type') == 'text')
            t = (t or '').strip()
            if t and not t.startswith(('<', 'This session is being continued', '[Request interrupted')):
                last = t; nuser += 1
    if nuser == 0: continue
    print(f"{time.strftime('%m-%d %H:%M', time.localtime(os.path.getmtime(f)))} | {sid} | {live.get(sid, 'asleep'):<16} | "
          f"{(title or '')[:28]:<28} | {nuser:>3} msgs | {(last or '').replace(chr(10), ' ')[:70]}")
    shown += 1
    if shown >= n: break
EOF
}

cmd_wake() {  # wake <session-id> <tmux-session-name>  — resume an existing conversation in a new tmux session
  local sid="$1" name="$2" f
  f=$(ls "$TRANSCRIPTS"/"$sid"*.jsonl 2>/dev/null | head -1); [ -n "$f" ] || die "no conversation matching $sid"
  sid=$(basename "$f" .jsonl)
  for j in "$SESS_DIR"/*.json; do
    if grep -q "\"$sid\"" "$j" && kill -0 "$(basename "$j" .json)" 2>/dev/null; then
      die "conversation $sid is already running (pid $(basename "$j" .json)) — use restart on its pane instead"
    fi
  done
  tmux has-session -t "=$name" 2>/dev/null && die "tmux session '$name' already exists"
  tmux new-session -d -s "$name" -c "$PROJECT_DIR"
  local t; t=$(tmux list-panes -t "=$name" -F '#{session_name}:#{window_index}.#{pane_index}' | head -1)
  tmux send-keys -t "$t" "cd $PROJECT_DIR && claude $CLAUDE_FLAGS --resume $sid --remote-control" Enter
  verify "$t"
}

cmd_kill() {  # kill <target> [--force]  — exit claude, then close the pane
  local t="$1" pid
  pid=$(claude_pid "$t")
  if [ -n "$pid" ]; then
    SESSION_ID=$(sess_field "$pid" sessionId)
    exit_claude "$t" "${2:-}"
    echo "resume later with: claude --resume $SESSION_ID"
  fi
  tmux kill-pane -t "$t" && echo "closed pane $t"
}

case "${1:-}" in
  list)    cmd_list ;;
  peek)    cmd_peek "${2:?target}" "${3:-30}" ;;
  last)    cmd_last "${2:?target or session id}" "${3:-6}" ;;
  verify)  verify "${2:?target}" ;;
  restart) cmd_restart "${2:?target}" "${3:-}" ;;
  recent)  cmd_recent "${2:-20}" ;;
  wake)    cmd_wake "${2:?session id (prefix ok)}" "${3:?tmux session name}" ;;
  new)     cmd_new "${2:?tmux session name}" "${3:-}" ;;
  kill)    cmd_kill "${2:?target}" "${3:-}" ;;
  *) echo "usage: $0 {list|recent [n]|wake ID NAME|peek T [n]|last T|ID [n]|verify T|restart T [--force]|new NAME [display]|kill T [--force]}"; exit 1 ;;
esac
