---
title: "Code-graph benchmark — plan and revisions"
topic: meta
status: active
created: 2026-09-24
last_updated: 2026-09-24
---

# Plan — does a code-graph tool (Graft, Graphify) help Claude Code on this repo?

## Purpose (plain language)

A first test (2026-09-22, `tmp/20260922_130852_graft_headtohead.md`) found that the Graft code-graph
tool gave no benefit over Claude's normal grep/read search. A follow-up web review showed that test
measured the wrong thing: it asked five *lookup* questions that each contained an obvious search word,
ran Graft with its automatic context delivery switched off (sub-agents, no MCP tools), and let a fixed
~70k-token start-up cost swamp the search cost. The published benefits of these tools (RepoGraph,
ICLR 2025: +32.8% relative on SWE-bench-Lite; Graft's own SWE-bench run) come from **multi-file code
changes graded by tests**, where the graph helps the agent find the "sibling" files a change needs.

This plan re-tests that claim on our own repo: replay real past multi-file commits as tasks, give each
to three groups of Claude Code sessions (no tool / Graft / Graphify), and grade each attempt with the
commit's own tests plus a check of which files it edited.

## Arms

| Arm | Setup inside the task snapshot |
|---|---|
| **A — baseline** | Snapshot as-is. `graft`/`graphify` not on PATH, no graph outputs present. |
| **G — Graft** | `graft build --deep` (Sonnet summaries via the subscription relay, cache seeded from the nearest earlier build) + `graft init --agents claude --no-global --no-statusline` (its default hooks: SessionStart map, UserPromptSubmit pointers, PostToolUse blast-radius + refresh, Stop) + Graft MCP tools passed with `--mcp-config`. |
| **F — Graphify** | `graphify update .` (tree-sitter, whole repo code) + `graphify claude install` (its project-level always-on mode: a `## graphify` section in the snapshot's CLAUDE.md) + the graphify skill copied into the snapshot's `.claude/skills/` (NOT `~/.claude`, which `graphify install` writes to globally). Docs are not LLM-extracted (that needs an API key or a heavy in-session pass) — stated limitation. |

Every arm gets the identical task prompt, model, flags, PATH (except the tool), and snapshot.

## Tasks — six real past commits (history-free snapshots)

| ID | Commit | Change | Source files the commit touched |
|---|---|---|---|
| T1 | d4c30a2a | separate warming/cooling speeds for body temperature | config_loader.py, core.py, state.py, default.yaml |
| T2 | af4047ac | add MC_FIXED return mode to rPPO | ppo_trainer.py, recurrent_ppo_trainer.py, train.py |
| T3 | 35a26452 | blur knobs become conditional-mandatory | config_loader.py, scripts/eval/traj_collect/collect_trajectories.py |
| T4 | 18b079cf | configurable two-hot bin range for Dreamer-SRL | dreamer_srl_main.py, dreamer_srl/train.py |
| T5 | 8334d89a | three review nits (starvation label guard, LSTM+modulation guard, narrowed except) | core.py, recurrent_ppo_network.py, recurrent_ppo_trainer.py |
| T6 | 52320023 | dashboard: never refuse a sensor range — draw small squares and warn | dashboard/labels.py, dashboard/panels.py |

Snapshot = `git archive <commit>^` minus `docs/project/references/*/sources/**` (1.2 GB of paper PDFs),
extracted to local tmpfs, then `git init` + one base commit. **No project history** is present, so an
agent cannot read the answer from `git log`. Pre-existing plan docs describing the change may exist in
`docs/` (they were written before the commit) — equal across arms; noted as a limitation.

**Task prompt** = an issue-style description of the desired behaviour, written from the commit message
and the hidden tests. It names the public interface the tests exercise (config key names, mode strings,
function/argument names) but **never names the files to edit**.

**Validity gate per task (SWE-bench style):** the commit's test files, overlaid on the *before* snapshot,
must have ≥1 failing test; on the *after* snapshot, all must pass. Tasks failing the gate are dropped.

## Runner

`claude -p "<prompt>" --model sonnet --output-format stream-json --verbose` run inside the snapshot
copy, with:
- `--permission-mode acceptEdits`, `--allowedTools` = Bash, Read, Grep, Glob, Edit, Write, (G: `mcp__graft__*`);
  `--disallowedTools Agent` (no sub-agents — keeps runs comparable and cheap);
- deny rules for writes under `/media/nas01/**`, `ssh`, `run_command.py`, `git push`;
- same prompt suffix for all arms: "Benchmark run: implement the change in this directory and make the
  relevant tests pass. Do not update the diary, LLM wiki, or memory; do not commit; do not launch training."

Order: interleaved (A, G, F for task 1, then task 2 …) so time-of-day / rate-limit effects spread evenly.
Stage 1 = 1 trial per task×arm (18 runs). Stage 2 = 2 more trials per cell (36 runs) only if stage 1
completes cleanly.

## Metrics

1. **Correct** — hidden tests (the commit's test files overlaid on the agent's result) all pass.
2. **File recall** — fraction of the commit's non-test, non-doc files the agent changed.
3. **Tokens** — from the final stream-json `result` event: fresh input, cache-read, cache-write, output;
   reported separately so the fixed CLAUDE.md start-up cost is visible, not blended in.
4. **Exploration cost** — tool calls and seconds before the first Edit/Write.
5. **Wall-clock**, **turns**, **total tool calls** (by tool name).

## Verification checks (failure-detectable)

- Before stage 1: one smoke run per arm on T1 confirming (a) G: stream-json init lists `mcp__graft__*`
  tools and the SessionStart/UserPromptSubmit hook output appears; (b) F: the CLAUDE.md graphify section
  is present and `graphify-out/graph.json` exists; (c) A: no graft/graphify on PATH, no graph folders.
- After every run: real repo `git status` unchanged; no files under `~/.claude/CLAUDE.md` or
  `~/.claude/skills/graph*`.
- Grading script re-run on the pristine *after* snapshot must score 100% correct / recall 1.0 (the
  grader is checked against the known answer before it grades anyone).

## Limitations stated up front

- n = 6 tasks × 3 trials; differences smaller than roughly one task are noise.
- Tasks come from one repo whose code is well documented — the result is about *this* project.
- Graphify runs without LLM doc extraction; Graft runs with Sonnet summaries.
- Snapshots contain the plan docs written before each commit.

---

## Revision 2 — applying the plan-reviewer findings (NOT READY → fixes)

| Finding | Fix |
|---|---|
| T4 fails the validity gate | Dropped. |
| T1 / T5 answer leakage via docs | **`docs/` is removed from every snapshot** (all arms equal; CLAUDE.md kept). Plus a mechanical **prompt-identifier leak gate**: every backticked name in a task prompt is grepped in the before-snapshot; any hit outside the files the commit edits fails the task. T5 dropped (also mostly ungraded). |
| NAS reachable; tests hardcode the live repo path | Every agent runs under **bubblewrap**: `/` read-only, `/media/nas01` replaced by an empty tmpfs, private `/tmp`, only the run's snapshot copy and its own HOME writable (the real OAuth credentials file bind-mounted so token refreshes stay in one place). Verified: NAS shows 0 entries, `/home` write fails, `claude -p` authenticates. The absolute repo path inside each snapshot is rewritten to the snapshot's own path so hardcoded-root tests import the snapshot, not the NAS. |
| Only fail-to-pass graded | Add **PASS_TO_PASS**: all tests in the hidden tests' directories that pass both before and after the real commit. Report both. |
| Prompts must carry every asserted name/substring | Prompts rewritten from the hidden tests (T1 includes the archived thermal worlds requirement; T6 includes the warning's content requirements). |
| Graphify skill not invocable | `Skill` added to allowed tools in all arms; smoke run must show it invoked. |
| Graft cache seeding could leak after-state summaries | G graphs are built per snapshot in chronological order, each seeded only from an *earlier* before-snapshot's cache; after every build `graft/` is grepped for all prompt identifiers that are new in the commit; any hit fails. |
| Per-run memory/transcript bleed | Unique snapshot copy and unique HOME per run. |
| No decision rule | **Pre-registered:** stage 1 (1 trial/cell) is a pipeline check only. A tool is judged *beneficial* only if, over all trials, it (a) resolves ≥3 more task attempts than baseline with no more P2P breakages, or (b) matches baseline correctness within 1 attempt AND uses ≥25% fewer total tokens or ≥25% less wall-clock. Otherwise: no benefit shown. |
| Setup cost excluded | Graph build time and relay tokens reported as one-off setup cost. |
| "File recall" wording | Renamed *reference-set recall*. |

---

## Revision 3 — what happened while executing (2026-09-24)

- **Final task set** (validity gate + prompt-identifier leak gate, docs/ stripped): T1 d4c30a2a, T2 af4047ac,
  T3 35a26452, T6 52320023, T7 4b6f7196 (band width fix; its two repro worlds added to the before-copy as test
  fixtures), T8 78a46b61 (GAE_NORM / MC_RAW). Dropped: T4 (no failing test), T5 (leak + 1/3 graded), and eight
  other candidates (core dumps, 25-33 min suites, pre-existing failures, or tasks that create new modules the
  tests import by path). T1's `scripts/fixtures/generate_thermal_rate_scale_fixture.py` removed (describes the
  feature and names the hidden test).
- **Grader self-check:** the real after-state scores correct, 0 P2P broken, recall 1.0 on all six tasks.
- **Delivery verified (the first test's flaw):** Graft run — MCP server `connected`, all 6 `mcp__graft__*`
  tools listed, SessionStart hook injected the `[graft]` map, UserPromptSubmit hook recorded the task as
  `lastQuery`, Sonnet summaries survive the copy (2386 ready / 24 stale = the edited functions). Graphify run —
  CLAUDE.md `## graphify` section + PreToolUse hook present, graph built (~11k nodes).
- **Observed in smoke runs:** agents in both tool arms went straight to Grep/Read. Graphify's nudge hook only
  matches grep run *through Bash*; Claude used its built-in Grep tool, so the nudge never fired.
- **Prompt fixes after stage 1 (pipeline check):** T6 prompt said "remove unreachable code", and both arms deleted
  `pack_or_explain`, which the real commit kept and the tests call; T8's tests pin the order of
  `LEGAL_RETURN_MODES`. Both prompts corrected; all T6/T8 runs made with the old wording moved to
  `runs_discarded/` and re-queued. No other prompt changed.
- **Graft setup cost:** T3 from scratch 41m42s / 569 Sonnet calls (~$19.8 API-equivalent, subscription);
  T2 seeded from T3 21m11s / 105 calls. Leak grep of `graft/` for each task's new identifiers: 0 hits so far.
- **Confound noted:** claude.ai connectors from the user's account load in every run (all arms equally; not in
  allowed tools, so not callable).
