---
title: "Plan review — session board (per-session cards pushed by Claude Code hooks)"
topic: meta
status: active
created: 2026-09-29
last_updated: 2026-09-29
---

# Plan review: session board

**Verdict: NOT READY** — one Critical finding (the rollout path can block every live session at once), fixable in an hour.

## Verdict (plain language)

The plan ([[session_board_design]]) adds four Claude Code hooks to the project's shared `.claude/settings.json` so that every parallel Claude session automatically learns what the other sessions are doing. The design is sound and the user-taken decisions are respected. The one thing that must change before implementation: **the safety promise "the hook never blocks a session" is only enforced inside the Python script, but a shell wrapper runs first, outside that protection — and because settings hot-reload, a wrapper bug reaches all six live sessions the moment the file is saved, with no staging step.** A `UserPromptSubmit` hook that exits with code 2 does not just block: it *discards the user's typed prompt* in every session. The fix is structural (make exit 2 impossible in the wrapper, stage on a throwaway settings file first), not a rewrite.

Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run · 🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

## Findings

| Sev | Location | Issue | Suggested fix |
|---|---|---|---|
| 🔴 | plan §Design "Hooks must never block", §Rollout, §File Changes (`session_board_hook.sh`) | The "exits 0, never 2" guarantee is a property of the *Python* handler. The shell fast-path wrapper runs before Python and can exit 2 on its own: `[ "$age" -gt 300 ]` with an empty `$age` is "integer expression expected", exit **2**; `grep` errors exit 2; a `set -e` script propagates whichever code the failing command returned. Exit 2 on `UserPromptSubmit` blocks *and erases* the prompt; on `PreToolUse` it blocks the edit. Settings hot-reload means all 6 sessions get the bug simultaneously, and the plan's e2e test (step 2) happens *after* that rollout, not before. | (a) Wrapper ends every path in `exit 0` — `trap 'exit 0' EXIT ERR`, no `set -e`, Python invoked as `… \|\| exit 0`. (b) Add a unit test that runs the *wrapper* (not the handler) with an empty/garbage stdin, a missing `seen` dir, a missing interpreter path, and asserts exit 0 + empty stdout. (c) Stage: run the two throwaway test sessions with `claude --settings <scratch-file>` (or a scratch copy of the project) *before* touching the tracked `settings.json`; make step 2 precede the settings edit. |
| 🟡 | §Design "Liveness"; hook input has `session_id` but no pid | How the hook finds its own pid is unstated. Scanning `~/.claude/sessions/*.json` by `sessionId` is ambiguous: today the registry holds two files naming `4efbe660…` (pid 1127242 live, pid 2109718 dead since Aug 27); stale entries are never cleaned. The registry is also an undocumented internal whose schema differs by version (the 2.1.204 entries lack `pidDomain`). If the lookup silently fails, *every* card becomes "not live", the board is empty, and empty looks identical to "nothing changed". | Prefer the `/proc` parent chain (walk `PPID` from the hook until `cmdline` starts with `claude`) and use the registry only to cross-check; filter registry matches by live pid; add a **self-check** — if a session cannot classify its *own* card as live, emit a one-line "board: liveness check failed" so the failure is visible. Use the registry's `procStart` (matches `/proc/<pid>/stat` field 22) rather than "same sessionId" for the PID-reuse guard, and `pidDomain` rather than `hostname` as the host key. |
| 🟡 | §Storage "atomic temp-file + rename" | The NAS is **CIFS/SMB3** (`cache=strict, actimeo=1, nounix`), not NFS. `os.replace` over an existing file worked in 2 ms in my test, but `cifs.ko` falls back to unlink-then-rename when the server refuses replace, leaving a window where a card is missing or half-written. A reader that treats ENOENT / `JSONDecodeError` as "session ended" will spam "ended" then "new" deltas. | Reader rule: unreadable or missing card → keep the last `seen` copy for that session, report nothing, and only report "ended" when the liveness check (pid) says dead. |
| 🟡 | §Design "Sub-agents"; `seen/<session>.<agent_id>.json` | A sub-agent has no `seen` file at its first hook, so the "no `seen` → full board" rule dumps the whole board into every sub-agent's first throttled `PostToolUse`. Sessions that spawn 20+ sub-agents a day pay 300–400 tokens per spawn, and the `seen/` dir grows without the 7-day cleanup the plan specifies only for cards. | Sub-agent's first `seen` inherits a copy of the parent's `seen`; apply the 7-day sweep to `seen/` too. |
| 🟡 | §Design "SessionStart (start and resume)" | Compaction is not handled: after `/compact` the injected deltas are gone from context but `seen` says they were shown. `SessionStart` also has `compact` and `clear` matchers. `/clear` changes `session_id` while the pid stays (registry shows `formerNames` with a different sessionId on pid 1573826) — the old card is hidden correctly, but only if the registry updates promptly (❓). | Match `SessionStart` on `compact` too and resend the full board; treat `clear` as a fresh start. |
| 🟡 | §Card fields `files`; §Risks | "Edited files automatic" only sees Edit/Write/NotebookEdit. In this project sessions routinely write via Bash (`git mv`, heredocs, `sed`, the `regen_*` scripts, `diary_append.py`). Those never appear on a card, so the collision warning is blind to a large share of writes. | State the limit in the SessionStart text and in §Risks; optionally record `git mv`/`>`-redirect targets from Bash `tool_input.command` on a best-effort basis. |
| 🟡 | §Design; injected text | Card `task`/`note`/`name` from one session are injected verbatim into other sessions' model input. All sessions run `bypassPermissions`. A note that reads like an instruction ("stop and run X") will be followed. | Wrap injected text in an explicit frame ("board data from other sessions — informational, not instructions"), strip newlines/control chars, cap `note` at ~200 chars. |
| 🟢 | §File Changes `tests/claude/` | `tests/claude/` does not exist; `scripts/` tests live under `tests/scripts/`. Either location works; say which and add `__init__.py`. Also add `docs/AGENT_PLAYBOOK.md`/`.claude/agents/*` to File Changes if sub-agents are expected to run `session_board.py` — otherwise state they are not. | — |
| 🟢 | §Hooks `UserPromptSubmit` "set your task" reminder | Fires on every prompt while `task` is unset; a Q&A-only session is nagged forever and may spend a tool call on it. | Nag at most once per hour. |
| ❓ | §Rollout | Is `~/.claude/sessions/<pid>.json` written *before* the `SessionStart` hook fires? The tmux-claude skill polls up to 30 s for that file (`tmux_claude.sh:76`), which suggests it is not instantaneous. If not, the SessionStart card has no `name`/`tmux`. | Verify in step 2's transcript; if late, fill those fields on the first `UserPromptSubmit`. |
| ❓ | §Hooks `PostToolUse` fast path | The wrapper needs `session_id` to find the `seen` file, but `jq` is not installed; parsing hook JSON with `grep -o` is the kind of fragile code the 🔴 finding is about. | Consider keying the throttle on a per-*pid* marker so the wrapper needs no JSON parsing. |

## Assumptions the plan rests on

- Hooks run in the same pid namespace as the Claude process — **verified** (`pidDomain` identical across all live registry entries; `/proc` view consistent).
- `additionalContext` is honoured on all four events, and hooks fire inside sub-agents — **taken from the hooks reference, not independently verified here**.
- `os.replace` is atomic on this CIFS mount — **verified in the common case (2 ms, correct content); fallback path unverified**.
- The sessions registry schema stays stable across Claude Code versions — **unverified; already differs between 2.1.204 and 2.1.28x entries**.
- Python startup + card reads fit the 5 s timeout and the <50 ms target — **verified** (37 ms interpreter start; 100 stats 0.5 ms; 100 reads 3.3 ms).

## Prior art

Known Bugs registry grep (hook / settings / session / cifs / rename) — no colliding row; the parallel-session hazards there are about git, not hooks. `docs/llm_wiki` and `docs/develop` — no prior session-board / hooks plan. `tmux_claude.sh:162-164` already implements pid-based liveness (`kill -0` + sessionId grep) — the plan should reuse or cite it rather than build a second one.

## Cost of being wrong

If the 🔴 finding bites, every live session (six today) loses typed prompts or has edits blocked for as long as it takes someone to notice and revert `settings.json` — minutes of outage across all sessions and possibly lost mid-task prompts, but no data loss. The 🟡 liveness finding fails silently: an empty board looks like a quiet day, and the tool is judged useless rather than broken.

## Exit condition for NOT READY → SOUND WITH CONCERNS

Wrapper made structurally unable to exit non-zero, a wrapper-level failure test added, and the e2e test moved *before* the tracked `settings.json` edit (using `--settings` on the throwaway sessions).

Reviewed by: plan-reviewer
