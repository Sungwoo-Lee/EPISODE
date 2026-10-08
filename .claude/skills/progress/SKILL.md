---
name: progress
description: "Summarize THIS session's current task as one flat table: task, status, when it finished, and a plain-English explanation. Done items are checked against git. Print-only — writes nothing. Trigger on /progress, 'where are we', 'what's done and what's left', 'summarize the current job', 'progress so far'."
---

# /progress — status of the current task

Print one table for the line of work this session is doing **right now**. Earlier, finished lines of
work in the same session are left out. This skill writes nothing: no board update, no diary row, no commit.

## 1. Gather (read-only)

- **Conversation:** what the user asked for in the current task, what was done and when, what was
  promised next, what is waiting on the user.
- **Board:** `BOARD show` (the command printed by the SessionStart hook): this session's card, and any
  note from another session that blocks this task.
- **Git** (each call in `timeout 20`): `git log --format='%h %ad %s' --date=format:'%m-%d %H:%M' -15`
  to match done items to commits, `git status --short -- <files this task touched>` for unsaved work, and
  `git rev-list --left-right --count origin/<branch>...<branch>` to see whether commits reached GitHub.

**If git fails** (timeout, unreadable ref, unborn branch), do not stop: build the table from the
conversation and board alone, and put this line under the job line:
`⚠️ Git isn't working right now (<plain reason>), so "done" items could not be checked.`

## 2. Print

```
**Job:** <one plain-English line: what this task is for>

| # | Task | Status | Done at | What it means |
|---|---|---|---|---|
| 1 | <short name> | ✅ Done | 10-07 17:52 | <one or two plain sentences> |
| 2 | <short name> | 🔄 In progress | — | ... |
| 3 | <short name> | ⛔ Waiting for you | — | ... |
| 4 | <short name> | ⏳ Planned | — | ... |
```

- **Rows** in order: done (oldest first), in progress, waiting, planned (in the order they will happen).
- **Status** is one of: `✅ Done`, `🔄 In progress`, `⛔ Waiting for you`, `⛔ Waiting for <who/what>`, `⏳ Planned`.
- **Done at** is local time `MM-DD HH:MM`: the commit time if the item is a commit, otherwise the time
  of the message where it was finished (transcript timestamps are UTC; convert to local). `—` for unfinished rows.
- **What it means** explains the task to someone who doesn't know the project: what it is and, where useful,
  why it matters. No jargon, no SHAs, run IDs, file paths or flag names. If a done item is not yet saved in
  git or not yet on GitHub, say so here in plain words ("not saved to git yet", "saved, not yet copied to GitHub").

## Rules

- Never mark something done that was only planned or attempted. A failed attempt is 🔄 or ⛔, with the failure explained.
- Keep it to about 3–8 rows; merge small steps. Point to the owning doc in one line below the table if details exist.
