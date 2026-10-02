---
title: "Session board — live 'who is working on what' shared across parallel Claude sessions"
topic: meta
status: active
created: 2026-09-29
last_updated: 2026-09-30
---

# Session board

> **Status**: LIVE since 2026-09-30 (hooks in `.claude/settings.json`, user-approved). Kill switch: `touch claude_data/board/OFF`
> **Opened**: 2026-09-29
> **Related**: tmux-claude skill (`.claude/skills/tmux-claude/SKILL.md`), diary skill (`.claude/skills/diary/SKILL.md`)

---

## Context

Several Claude sessions work on this repo at the same time (six were live on 2026-09-29, each in its
own tmux session). None of them can see what the others are doing *right now*. The diary records
what already happened, and its "Sessions" table is rarely filled (on 2026-09-29 it held one
auto-created row while six sessions ran). Messages between sessions are one-to-one and only happen
when an agent thinks to send one. The result is collisions: on 2026-09-09 one session ("Dev:
Rendering") had to message another ("Dev: temperature") by hand to stop it writing configs that a
change it was about to land would break.

This doc designs a **session board**: one small card per live session saying what it is doing,
which files it is editing, and any note meant for everyone. The board is **not a record**. It
shows only the present, so cards of ended sessions disappear. Its key property is that **information
reaches every session without anyone asking for it**: Claude Code hooks automatically add *only
what changed* on other sessions' cards to each session's input, so the agent doesn't have to
remember to look.

## Analysis

### Prior art (web search, 2026-09-29)

| System | Mechanism | Lesson adopted here |
|---|---|---|
| Blackboard markdown file ([dev.to](https://dev.to/dexterlung/i-built-my-ai-team-a-blackboard-how-to-stop-parallel-claude-sessions-from-colliding-j71)) | One git-tracked table, a row per branch, "claim before acting" | The board itself collides most, so **each session edits only its own entry** (here: its own file). Hand-typed status drifts, so **auto-record the facts**. Keeping the board in git caused noise, so **keep it out of git**. |
| claude-presence ([dev.to](https://dev.to/sahil_kat/coordinate-multiple-claude-code-sessions-on-a-shared-repo-1dh4)) | Per-session broadcast of task + files; heartbeat | Advisory checks fail when agents forget, so **push via hooks**. Polling reacts one tick late, so **deliver mid-turn too**. |
| MCP Agent Mail ([GitHub](https://github.com/dicklesworthstone/mcp_agent_mail)) | Inboxes + advisory file leases with expiry + optional pre-commit guard | **Warn, don't block**. Hard locks cause pile-ups. |
| agent-claim-mcp ([GitHub](https://github.com/vk0dev/agent-claim-mcp)) | JSON ledger, claim / release / who-owns, 1 h expiry | A dead session must not hold anything, so liveness comes from the real process here. |
| Claude Code agent teams ([docs](https://code.claude.com/docs/en/agent-teams)) | Shared task list + auto-delivered mailboxes | Only works inside one lead's team, not across independently started sessions. |

### Hook facts this design relies on (Claude Code hooks reference, fetched 2026-09-29)

- Every hook receives `session_id`, `transcript_path`, `cwd`, `hook_event_name`. Inside a sub-agent it also gets `agent_id` / `agent_type`.
- `SessionStart` (start and resume), `UserPromptSubmit`, `PreToolUse` and `PostToolUse` can each add text to the model's input via `hookSpecificOutput.additionalContext`. `PreToolUse` can add context **without blocking**.
- Hooks fire for tool calls inside sub-agents too.
- Edits to hooks in settings files are picked up by **already-running** sessions (file watcher), so no restart is needed. `SessionStart` will not fire for sessions that are already running (see Rollout).
- Injected text is capped at 10,000 characters. The design caps its own output far lower.

### Decisions already taken with the user (2026-09-29, via /ask)

| Question | Decision |
|---|---|
| How updates reach sessions | Hook push, **deltas only** (full board once at session start) |
| Also during long autonomous work? | **Yes, throttled** (at most every 5 min, plus before any edit) |
| Editing a file another live session is working on | **Warn, don't block** |
| Which fields are automatic | **Edited files automatic**; agent writes a one-line task and an optional note |
| Where the board lives | **Inside the project folder on the NAS** (the container can move between nodes), gitignored |
| How long a broadcast note lives | **Until the author withdraws it or its session ends**; the author is reminded after 12 h |

## Implementation Plan

### Design

**Storage** is `claude_data/board/`, which is inside the project on the NAS and already gitignored by `.gitignore:32`.

```
claude_data/board/
  cards/<session_id>.json            # one per session; written ONLY by that session's own hooks/commands
  seen/<session_id>[.<agent_id>].json # what this (sub-)agent was last shown; written only by itself
```

Each session writes only its own files, with atomic temp-file + rename. There is no shared file and
no lock, which removes the "board collides with itself" problem.

**Card fields**

| Field | Source |
|---|---|
| `session_id`, `name`, `tmux`, `pid`, `host`, `started` | automatic: hook input + `~/.claude/sessions/<pid>.json` |
| `updated` (heartbeat) | automatic: every hook run |
| `files`: up to 10 most recent `{path, last_edit}` in the last 3 h | automatic: `PostToolUse` on Edit/Write/NotebookEdit, sub-agents included |
| `task`: one line | agent: `session_board.py task "…"` |
| `note`: optional broadcast to all | agent: `session_board.py note "…"` / `note --clear` |

**Liveness** determines which cards are shown. A card counts as live when its `host` equals this
host and its `pid` is alive and `~/.claude/sessions/<pid>.json` still names the same `session_id`.
The last check guards against a reused PID. For a card from a *different* host, which could only
happen if sessions ever ran in two containers sharing the NAS, the card counts as live if it was
`updated` within 30 min. Dead cards are hidden immediately and their files are deleted after 7 days.

**Hooks** go in the project `.claude/settings.json`, which is tracked, so every session gets them.
Each hook calls `scripts/claude/session_board.py hook <event>`.

| Hook | Does | Adds to the model's input |
|---|---|---|
| `SessionStart` | create/refresh own card; write `seen` | full board of *other* live cards + the three commands (`task`, `note`, `show`) + "set your task now" |
| `UserPromptSubmit` | heartbeat; diff live cards vs `seen`; update `seen` | only the changes (new session, task or note changed, new files, session ended). Nothing if nothing changed. Adds a one-line reminder if own `task` is unset, or if own `note` is > 12 h old. If there is no `seen` file yet (a session that was already running at rollout), adds the full board instead. |
| `PreToolUse` (Edit\|Write\|NotebookEdit) | compare target path with other live cards' `files` | **warning only**, e.g. `⚠ board: "Dev: Rendering" edited this file 12 min ago; task: "…". Check before overwriting, or message them.` Never sets a blocking decision. |
| `PostToolUse` (all tools) | record edited path (edit tools only); if own `seen` is ≥ 5 min old, diff + update `seen` | the throttled mid-turn changes, same format as above |

The mid-turn hook runs after every tool call, so it has a **fast path**. A small shell wrapper checks
the `seen` file's age and exits before starting Python when nothing is due. Only edit-tool calls and
calls at least 5 min apart start Python.

**Sub-agents.** A sub-agent's edits are recorded on the *parent's* card, because the parent owns the
work. A sub-agent keeps its **own** `seen` file (`seen/<session>.<agent_id>.json`). This matters
because a change a sub-agent sees must not be marked as seen for the parent, who would otherwise
never get it.

**Size cap.** Output above 1,500 characters is cut to "N sessions changed; run `session_board.py
show`". The expected per-change size is 50–100 tokens.

**Hooks must never block or break a session.** Every error inside the script is caught, so the
script exits 0 with no output. The hook `timeout` is 5 s. It never exits 2 and never returns a
deny/block decision.

**Human view.** `session_board.py show` prints the board. `tmux-claude list` gains a TASK column
read from the cards.

**Relation to the diary.** The two don't overlap. The diary stays the history, and the board is
present-tense only. Nothing on the board is copied to the diary.

### Token cost (estimate)

| | per prompt | ~50 prompts/day/session |
|---|---|---|
| Full board every prompt (rejected) | 400–800 | 20k–40k |
| Deltas (chosen) | 0 usually; 50–100 on a change | ~300–1,000 |
| Session start | 300–400 once | once |

### Rollout

Settings hooks are hot-reloaded, so the 6 running sessions start receiving board hooks at their
next prompt or tool call. `SessionStart` does not fire for them. The "no `seen` file, so send the
full board" rule covers that, and the prompt hook's "your task is unset" reminder gets them to fill
in their card. No restarts are needed.

## File Changes

| File | Change |
|---|---|
| `scripts/claude/session_board.py` | **new**: card read/write, liveness, diff, hook handlers, `task` / `note` / `show` commands |
| `scripts/claude/session_board_hook.sh` | **new**: fast-path wrapper (throttle check before Python) |
| `.claude/settings.json` | add the 4 hooks (currently holds only `worktree.bgIsolation`) |
| `.claude/skills/tmux-claude/tmux_claude.sh` + `SKILL.md` | TASK column in `list` |
| `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` | register the two new `scripts/claude/` files and their caller (`.claude/settings.json` hooks); maintenance contract |
| `tests/claude/test_session_board.py` | **new**: unit tests (below) |
| `CLAUDE.md` | **no change**: the SessionStart text teaches the commands (CLAUDE.md stays minimal) |

No new config keys, no `src/` or `configs/` changes.

## Verification

1. **Unit tests** with `BOARD_DIR` pointed at a temp dir and hook inputs as JSON fixtures:
   - diff shows new, changed and ended cards, and is empty when nothing changed
   - a sub-agent's `seen` is separate from the parent's
   - a dead PID, or a PID reused by a different session, is hidden
   - the edit warning fires only for *other* live sessions' files
   - a crash inside the handler still exits 0 with no output
   - output is capped at 1,500 characters
2. **Live end-to-end test on real sessions**, checked against what Claude Code actually delivered
   (the session transcript `.jsonl`), not by re-running the script. Two throwaway tmux sessions A
   and B, started with the tmux-claude skill:
   - A sets a task and a note, and edits a scratch file under `tmp/`.
   - B's next prompt receives the delta, confirmed in B's transcript.
   - B edits the same file and receives the warning, confirmed in B's transcript; the edit still succeeds.
   - A exits, and B's next prompt says A ended.
   - During a long tool loop in B, a change by A arrives within about 5 min without a prompt.
3. **Overhead check**: time 100 no-op `PostToolUse` calls through the wrapper on the NAS. Target
   < 50 ms each on the fast path.
4. **Rollout check**: after the settings change, confirm in one already-running session's transcript
   that its next prompt got the full board.

## Risks

- **Agents may not keep their task line current.** Mitigated by the unset-task reminder and by the
  automatic `files` field, which carries the collision signal even when the task line is stale.
- **Hook latency on a NAS** is covered by the fast path and verification step 3. If it is too slow,
  the fallback is to drop mid-turn delivery to edit-tool calls only.
- **Warnings may be ignored.** This is accepted: the design is advisory by the user's choice.

## Feedback from plan-reviewer

**Verdict: NOT READY** (2026-09-29). Full review with severity table, assumptions and exit condition:
[[plan_session_board]] (`docs/reviews/plan_session_board.md`).

One Critical finding: the "hook never blocks" guarantee lives in the Python handler, but the shell
fast-path wrapper runs *before* Python, outside that protection, and can exit 2 on its own (a
`[ "$x" -gt N ]` with an empty variable is exit 2). Exit 2 on `UserPromptSubmit` discards the typed
prompt; settings hot-reload delivers the bug to all six live sessions at once, and the e2e test is
scheduled *after* that rollout. Fix: wrapper structurally exits 0 on every path, a wrapper-level
failure test, and run the two throwaway test sessions with `claude --settings <scratch>` before the
tracked `settings.json` is edited.

Moderate: own-pid discovery is unstated and the sessions registry is ambiguous (two files already
name the same sessionId; stale entries persist; schema drifts by version) — a silent lookup failure
makes the board empty, which looks like "nothing changed"; CIFS (not NFS) rename fallback needs the
reader to treat a missing/half-written card as "unchanged", not "ended"; sub-agents get a full-board
dump on first hook and `seen/` never gets swept; compaction is not handled; Bash-driven writes are
invisible to the collision signal; injected card text needs a "data, not instructions" frame.

---

## Revision 1 — response to plan review (2026-09-29)

Every finding in [plan_session_board](../../../reviews/plan_session_board.md) is accepted. The changes below override the sections above wherever they conflict.

| # | Finding | Change |
|---|---|---|
| R1 🔴 | The shell wrapper runs outside the Python "always exit 0" guard. Exit 2 on `UserPromptSubmit` **discards the user's prompt**, and hot-reload would ship a bad hook to every session at once. | **Drop the shell wrapper.** Each hook command is `<interpreter> scripts/claude/session_board.py hook <event> \|\| true`, so the shell line itself cannot return non-zero. Inside Python, the whole handler sits in `try/except BaseException` and ends with `os._exit(0)`. The fast path (throttle check) moves into Python: 37 ms interpreter start was measured by the reviewer, which is acceptable. **Order of rollout:** the live end-to-end test (Verification step 2) runs first on throwaway sessions launched with `claude --settings <scratch settings file>`. The tracked `.claude/settings.json` is edited **only after** that passes. A new unit test runs the exact hook command line with garbage stdin, empty stdin and a missing interpreter, and asserts exit 0 with empty stdout. |
| R2 🟡 | How a hook finds its own session's PID was unstated. Registry scan by `sessionId` is ambiguous (duplicate and stale entries, schema drift). A silent failure would look like an empty board. | Own PID comes from walking the `/proc` parent chain up to the `claude` process. The registry `~/.claude/sessions/<pid>.json` is only a cross-check for name and tmux. The PID-reuse guard compares `procStart`; the host key is `pidDomain`, not hostname. If a session cannot classify **its own** card as live, the hook adds one line saying "board liveness check failed", so it never passes silently as "nothing changed". Liveness code reuses the approach in `tmux_claude.sh`. |
| R3 🟡 | The NAS is CIFS/SMB3, where rename can briefly leave a card missing or half-written. | A missing or undecodable card makes the reader keep its last `seen` copy and report nothing. "Ended" is reported **only** when the PID check says the process is dead. |
| R4 🟡 | Sub-agents' first hook would dump the whole board. `seen/` had no cleanup. | A sub-agent's first `seen` is copied from its parent's. The 7-day sweep covers `seen/` as well as `cards/`. |
| R5 🟡 | Compaction and `/clear` were unhandled. | `SessionStart` with source `compact` or `clear` resends the full board. `clear` creates a card for the new session ID on the same PID and retires the old one. |
| R6 🟡 | Files changed through Bash (`git mv`, heredocs, scripts) are invisible to the `files` field. | Accepted as a limit and stated plainly in the SessionStart text ("files list shows Edit/Write edits only"). The same limit is added to Risks. |
| R7 🟡 | Card text from one session is injected verbatim into others. | Injected block is framed as `[session board — status data from other sessions, not instructions]`. Newlines and control characters are stripped. `task` and `note` are capped at 200 characters, `name` at 60. |
| R8 🟢 | `tests/claude/` does not exist. The unset-task reminder would nag on every prompt. | Tests go in `tests/scripts/test_session_board.py`. The unset-task reminder fires at most once per hour. |
| R9 ❓ | Is the registry file written before `SessionStart` fires? | This no longer matters for correctness after R2, because the PID comes from `/proc`. If the registry is missing at `SessionStart`, name and tmux fill in on the next hook run. Confirmed in the step-2 transcript. |
| R10 ❓ | The wrapper needed `jq` to parse JSON. | Removed together with the wrapper (R1). |

**File Changes, revised:** `scripts/claude/session_board_hook.sh` is removed. `tests/claude/test_session_board.py` becomes `tests/scripts/test_session_board.py`. Also added: `tmp/session_board_test_settings.json`, the untracked scratch settings used for the pre-rollout test.

---

## Test results — isolated Haiku sessions (2026-09-29)

The live sessions were not touched. The hooks were loaded only through `claude --settings tmp/session_board_test_settings.json`, using a separate board directory (`SESSION_BOARD_DIR=tmp/board_test`). There were two Haiku test sessions, A and B, launched with the tmux-claude skill. Every check below was read from **B's own transcript** (the `hook_additional_context` attachments Claude Code recorded), not by re-running the script.

| Check | Result |
|---|---|
| Unit tests `tests/scripts/test_session_board.py` | 33 passed. Two real bugs were found and fixed: (1) the snapshot lacked `session_id`, so a card briefly missing mid-rename was reported "ended" (review finding R3); (2) the unset-task reminder fired on the first prompt right after the SessionStart text had already said it. |
| SessionStart gives the full board | ✅ B got A's card at startup. |
| Prompt gives the changes only | ✅ B's next prompt got A's new task, the file it edited and its note, in one line. |
| Warning before editing another session's file | ✅ `⚠ "Board test A" … edited /tmp/board_test/shared.txt 0 min ago (task: …)`, and **the edit still went through** (warn, don't block). |
| Mid-turn delivery during a long tool loop | ✅ A changed its card at about 12:45:50. B, busy with tool calls, got the change at 12:48:49, attached to a tool result. The other tool calls added nothing. The first attempt did not run because Claude Code refuses a plain foreground `sleep`, so the retry waited in Python instead. |
| Session ended | ✅ After A exited, B's next prompt got `"Board test A" ended (its note is gone)`. |
| Overhead | 49 ms mean per `PostToolUse` call on the fast path (20 calls, NAS). This is at the 50 ms target. |
| Not yet exercised live | `/compact` and `/clear` resend, sub-agent path (covered by unit tests only), a session already running at rollout getting the full board on its first prompt (Verification step 4, which is done at rollout). |

---

## Feedback from senior-developer — plan-adherence verification of commit 115f8f5e (2026-09-29)

**Verdict: implementation matches the design and Revision 1 on almost every item, but two gaps should be fixed before the rollout to `.claude/settings.json`.** Neither can break a session (the never-fail guarantee holds); both would make the rollout quietly less useful than the design promises.

**Fix before rollout**

1. **The 1,500-character cap removes the instructions.** `wrap()` replaces the *whole* message when it is too long. The instructions alone are 829 characters, the frame header is 74, and one typical card is about 300. So with three or more other live sessions (six are expected at rollout), the SessionStart message and the "no `seen` file" full board both collapse to "Many board changes — run show". The session is then never taught the `task`, `note` and `show` commands. Fix: cap only the board part, or shorten each card, and always keep the instructions.
2. **A session that is mid-turn at rollout never gets the full board.** If the first hook such a session fires is `PostToolUse`, the missing-`seen` branch of `on_post_tool` (the sub-agent-inherit path) writes a snapshot silently. When `agent_id` is None it copies from itself, so it falls back to `snapshot()`. The next `UserPromptSubmit` then finds a `seen` file and sends only deltas. The session never sees the existing cards or the instructions, only the hourly "no task" reminder. That contradicts the Rollout section and Verification step 4. Fix: in that branch, when `agent is None`, write nothing and return, so the next prompt takes the full-board path. Add a unit test for it.

**Should fix**

3. The tmux-claude `SKILL.md` was listed in File Changes but was not updated. It should document `TMUX_CLAUDE_EXTRA`, `TMUX_CLAUDE_ENV` and the TASK column. The RC column also no longer prints the `bridgeSessionId`, which was not requested and should be stated or reverted.
4. The `SCRIPTS_DEPENDENCY_MAP.md` row flags that the §2 intro sentence ("no `settings.json` invokes any of these") must be amended at rollout, but the Rollout section here does not list that step. Add it to the rollout checklist, so whoever edits `settings.json` also edits the map.
5. This doc's status line still says "PLANNED (awaiting user approval)". Change it to something like "IMPLEMENTED — rollout pending".

**Accepted deviations**: the heartbeat is written at most every 5 min rather than on every hook, to spare the NAS writes. The `files` entries use key `t` rather than `last_edit`. Overhead was timed over 20 calls rather than 100. File paths are not passed through `clean()`, which is low risk. The note-age reminder is skipped while the task is unset.

Verified by: senior-developer


---

## Revision 2: fixes from the second review round (2026-09-30)

Three reviewers ran: code-reviewer, senior-developer (plan adherence, signed section above) and plan-reviewer (rollout step). All their findings are applied. The live rollout is still not done.

| # | Finding (who) | Change |
|---|---|---|
| F1 | A session busy at rollout never gets the full board or instructions: its first hook is `PostToolUse`, which quietly wrote `seen` (senior-dev, plan-reviewer, code-reviewer) | A main agent with no `seen` file is **onboarded by that tool hook** (full board + instructions). A sub-agent whose parent is not onboarded stays silent and writes nothing. |
| F2 | The size cap replaced the whole message, instructions included, once 2–3 or more cards were live; a long collision warning was lost the same way (all three) | `wrap()` cuts **card lines only** and always keeps the instructions. The one-time full board gets `FULL_CAP` 3000 characters; per-change messages keep 1500; collision warnings have their own `WARN_CAP` 800. The "N more lines" line is budgeted at its real length. |
| F3 | No rollback lever that is independent of settings reload and git (plan-reviewer) | **Kill switch**: `touch claude_data/board/OFF` makes every hook return at its next run. |
| F4 | A lost-update race: a hook's card write could revert a concurrent `task`/`note` (code-reviewer) | The card is re-read right before saving, keeping `task`/`note`/`note_set` from the fresh copy. |
| F5 | Dead cards stayed for 7 days and slowed every read (code-reviewer) | `sweep()` removes cards and `seen` files of dead local sessions. It runs at SessionStart and at most hourly from the prompt hook. "Ended" is still reported, from the reader's own `seen` copy. |
| F6 | The PID-namespace ID alone can coincide across machines (code-reviewer) | `pid_domain` = `/etc/machine-id` + namespace. |
| F7 | Smaller items (code-reviewer) | Absolute script path in the instructions (the Bash cwd can drift), named once as `BOARD` to save space. Empty `task`/`note` are rejected. Card text is cleaned again when rendered. The onboarding prompt starts the reminder clock (no duplicate reminder). |
| F8 | tmux-claude `SKILL.md` did not document the new options (senior-dev) | Documented `TMUX_CLAUDE_EXTRA`, `TMUX_CLAUDE_ENV`, the TASK column and the ON/OFF RC column. |
| F9 | Test gaps (code-reviewer) | "Never fails" now runs the interpreter **without** `\|\| true` and asserts empty stderr. New tests: `task`/`note`/`task-of` commands, empty-argument rejection, the concurrent-write race, `/clear`, the hourly reminder, sweep, onboarding by a tool hook, sub-agent before parent, idle session at rollout, instructions surviving 12 live cards, a long warning being cut rather than replaced, the kill switch, a foreign-machine heartbeat. **45 passed.** |

**Rollout checklist**, to do in the same commit as the `.claude/settings.json` edit:
- amend the scripts dependency map's §2 intro sentence ("no `settings.json` invokes any of these") and its two `session_board.py` rows;
- set this doc's Status line;
- rollback is `touch claude_data/board/OFF` first, then revert the settings commit.

**Still open before rollout** (plan-reviewer): check that an already-running session actually reloads an edited project `settings.json` (the hot-reload canary).

### Hot-reload check (2026-09-30), the last open item before rollout

A Haiku session ran in a scratch folder outside the repo, with its own `.claude/settings.json` (`{}`, no hooks) and its own board directory. While it was in the middle of a tool loop, the hooks were written into that settings file (01:02:25). The **running** session picked them up without a restart: its card appeared at 01:02:41, and its transcript shows the full board plus instructions delivered by `PostToolUse:Bash`, which is the Revision 2 onboarding path for a busy session. This matches the hooks reference. It was tested on this build only (2.1.28x); the live sessions span 2.1.280–284.

### 7-day expiry of inactive live cards (2026-09-30, user request)

The earlier 7-day sweep deleted **any** card file untouched for 7 days, live or not. So an idle-but-running session silently vanished: other sessions were never told, and it came back with its task wiped and a confusing "task now: (cleared)". Now **no hook activity for 7 days is an explicit expiry**. `alive()` = process alive **and** not expired. Readers are told once, `"X" went quiet (no activity for 7+ days)`, and the card is swept like an ended one. If the session is used again, it rejoins as `NEW` with an empty task and note (its old task is stale), and the usual reminder asks it to set one. Tests: 47 passed.

### Worktrees share the main board (2026-09-30)

**Found by a live test:** a Claude session started inside a git worktree runs that worktree's own checked-out copy of the script, via `$CLAUDE_PROJECT_DIR`. The copy computed `REPO` as the worktree, so it wrote to the worktree's own empty `claude_data/board/`, a **separate board** invisible to everyone else. **Fix:** `main_repo()` follows the worktree's `.git` file (`gitdir: <main>/.git/worktrees/<name>`) back to the main checkout, so every worktree uses `<main>/claude_data/board/`. Verified live: a Haiku session in a throwaway detached worktree created its card on the main board (7 → 8 cards; the worktree's own board stayed empty). 48 tests pass.

**Caveat:** a worktree runs the script version **it** checked out. Worktrees created from a commit **before** this fix still write to a separate board. Create dev worktrees from a commit that includes it.

**Still not covered by the board:** a worktree session's "editing" paths are relative to its own tree. The same relative path edited in the main tree and in a worktree raises the warning, which is useful as an early merge-conflict signal, but the warning does not say which tree.

### Hook latency under NAS load (2026-09-30)

After rollout, one board hook in a live session went past its 5 s limit, so its output was dropped; nothing was blocked. Measured with the host at load average ~29:

| Cost | Before | After |
|---|---|---|
| Python start-up (the conda env's `site` imports a CUDA helper) | 819 ms | **24 ms with `python -S`**; the script uses only the standard library |
| PostToolUse, one call | ~2.1 s | **~0.35 s** (the rest is NAS I/O: reading the script and the card files) |
| PreToolUse on an edit | ~1.9 s | ~0.6 s |

The hook commands now run `python -S`. SessionStart and UserPromptSubmit get a 10 s timeout, so their board text isn't dropped on a slow NAS moment; the per-tool hooks keep 5 s. Reading the 7 cards took 0.9 s under that load against a few ms when idle. The remaining latency is the NAS, and it varies with cluster load.

### Branch awareness (2026-10-02): why the board missed the v4.0 / v5.0 split, and the fix

**Incident.** `v5.0` was cut on 09-30 inside the `thirst` worktree. The shared folder stayed on `v4.0`, which was intended, to isolate running jobs. Every other session kept committing there: by 10-02, `v4.0` held 69 commits that `v5.0` lacked, and `develop`/`main` had been advanced only locally, never pushed. The board could not see this. It tracked task, note, edited files and liveness, **nothing about branches**. The two lines of work touched different files, so no collision warning fired. The plan's "merge back later" had no owner, trigger or check. Fixed by hand on 10-02: `develop`/`main`/`v4.0` → `00769e28`, merged into `v5.0` (`db5ffb33`, `a7420940`), shared folder switched to `v5.0`.

**Fix (all tested; 61 tests):**

| Piece | Behaviour |
|---|---|
| Branch on each card | `git_head(cwd)` reads `.git/HEAD`, or the worktree's `gitdir/HEAD`, from files only, with no git process. Cards show `[on v5.0]` or `[on v5.0, worktree thirst]`; a branch change is reported in deltas. |
| Working branch | `claude_data/board/TARGET_BRANCH`, set with `BOARD target <branch>`. A session on another *named* branch is warned **at every prompt**, and its card is marked "⚠ not the working branch". Detached HEADs and Claude's own `worktree-*` isolation branches are not flagged. |
| Before `git commit` | A `PreToolUse` hook with `matcher: Bash` and `if: "Bash(*git*commit*)"` fires only for commit commands. A live test confirmed it catches plain `git commit`, `timeout 60 git commit`, `git -C <dir> commit` and `cd <dir> && git commit`, and stays silent for `git status`/`echo`. The narrower `Bash(git commit*)` missed the `timeout` and `-C` forms. The handler resolves the target directory from `git -C`/`cd` and warns if that checkout is off the working branch. |
| Gap counter | `divergence()` runs `git rev-list --count <target>..<b>` for `v*`, `develop` and `main`, with a 4 s budget. It is cached in `claude_data/board/divergence.json` for an hour and shared by all sessions. The full board, and an hourly prompt line, say "⚠ Commits not yet in v5.0: v4.0 has N". If git fails, the last known value is kept. |
| Procedure | `CLAUDE.md` "Version branches": finish a cut the same day (push `develop`/`main`, set the working branch, move the shared folder), and merge forward any commit that still lands on the old branch. |

Working branch set to `v5.0` on 2026-10-02.
