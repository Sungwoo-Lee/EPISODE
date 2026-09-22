---
id: 20260922_1559_six_more_checks_that_cannot_fail
date: 2026-09-22
time: "15:59"
folder: episode_renderer
tags: [learned_lesson, testing, meta]
summary: "Six checks in one session could not report what they were built to report, each failing differently; the common cause was writing a check quickly and then trusting its output as ground truth."
related: ["20260919_1317_checks_that_cannot_fail", "20260922_1558_shadowed_guards_one_constant"]
relations: ["extends:20260919_1317_checks_that_cannot_fail", "see_also:20260922_1558_shadowed_guards_one_constant"]
session_origin: claude_code
session_label: "renderer display + retirement step 1"
importance: high
status: settled
valid_until: null
confidence: high
supersedes: []
raw_source: claude_data/.claude/projects/-media-nas01-projects-Interoceptive-AI-grid-world-pain/14318db1-bd0b-4e8c-a423-e4d1d64d2180.jsonl
raw_completeness: full
---

# Six more checks that could not fail, in one session, each broken a different way

## Key conclusion

A sibling entry recorded four checks that could not distinguish the world where
their claim was true from the world where it was false. This session produced
**six more**, and the mechanism was identical every time: the check was written
quickly, its output was then treated as ground truth, and the error surfaced only
when something external contradicted it. What resolved each one was **reading the
subject's own documentation, or resolving it structurally** — never re-running
the check.

## Evidence, measurements, facts

1. **A grep killed by its own timeout.** `timeout 120 grep -l "$tag" logs/*.log`
   ran inside a command that itself hit 120 s. The grep was killed and returned
   empty, printing "(no log matched)" — indistinguishable from a grep that ran
   and found nothing. The logs existed; they are named by timestamp, not by tag.
2. **`ls -1 | tail -3` sorts lexicographically.** `"9800010"` sorts AFTER
   `"10000058"`, so the real final checkpoint sat earlier in the listing and was
   never looked at. Two completed training runs were reported as "ambiguous,
   possibly died near the end". `sort -n`, plus the log's own
   `Training complete.` line, settled it in seconds.
3. **`ps` blind to a PID namespace.** `ps -p <pids>` over SSH returned a header
   and no rows. `nvidia-smi` reports HOST pids and the shell runs in a container
   with its own namespace, so "empty" was equally consistent with "processes
   gone" and "pids invisible from here". The discriminator was DEVICE-reported
   GPU memory — 4 MiB against 13.7 GB — which no namespace can hide.
4. **A stop condition invented rather than read.** A checkpoint says "any
   non-`cell_` finding on a correct frame is a stop and report". Coded literally
   as `not rule.startswith("cell_")`, it fired on `text_over_fill` — which the
   audit's own docstring calls *legible by design*, and which the retired
   renderer and the dormant one both score 5 on. A rule every renderer ever built
   emits on correct frames is not a defect the new one introduced.
5. **A filter that deleted its own success line.** `grep -vE "...|  |^$"`
   excludes any line containing two consecutive spaces — which is exactly how the
   renderer's success line begins (`  ep    1: 9 frames verified`). The run had
   succeeded; the proof was filtered away. Checking the output DIRECTORY, rather
   than re-running with a cleverer filter, answered it.
6. **An AST walk that both invented and missed rules.** It collected every string
   constant passed positionally to `Finding(...)`. The dataclass is
   `(rule, detail, a, b, overlap_px, bbox)`, so prose from `detail`/`a`/`b` was
   swept in as "rules" ("canvas edge", whole sentences) — and four real rules
   emitted through a VARIABLE at one call site (`text_over_text`,
   `text_over_border`, `fill_over_text`, `text_over_fill`) were missed entirely.
   Two of those four appear in no literal `Finding("...")` anywhere in the file.

- **A seventh, of a different kind**: a test run scoped by expectation. Three
  suites were run because they were the ones judged affected; a fifth file
  asserting the same constant was never searched for. This happened **twice** in
  the same session, and the second time the commit had already landed, leaving
  the branch red.

## Decisions and actions

- **Derive lists structurally, never transcribe them.** The canonical audit-rule
  list now resolves the variable emission site via the `rule, detail = "..."`
  assignments feeding it, and reports how many `Finding()` calls still use a
  non-literal rule — so a new emission shape announces itself instead of being
  silently uncovered. The derived count (16) matched an independent reviewer's
  AST count exactly, which is corroboration rather than self-agreement.
- **Search for the subject; do not reason about where it lives.** Both
  expectation-scoped test runs would have been caught by one repo-wide grep for
  the constant being changed.
- **Prefer a quantity no layer can hide.** Device-reported GPU memory beat a
  process list; a decoded frame count beat the writer's own report; a log's
  completion marker beat an idle GPU.

## Open questions and follow-ups

- None as a finding. The pattern is recorded; the specific defects it produced
  are fixed and the corrections are in the commits named below.

## References

- [[20260919_1317_checks_that_cannot_fail|extends]] — the same failure mode,
  four instances, recorded three days earlier. That entry's guard ("run the check
  against the state where it should fail, before trusting it against the state
  where it should pass") would have caught instances 1, 2, 3 and 5 here.
- [[20260922_1558_shadowed_guards_one_constant|see_also]] — instance 6's rule
  derivation, and the range probe that measured only the painter, both belong to
  that entry's work.
- Commits: `c9f7e958`, `5364ad60`, `5d8321d4`, `385dc052`, `52320023`.
- Raw conversation: synced via `./sync-agent-data.sh claude push`. To read on
  another node: `./sync-agent-data.sh claude pull`, then either
  `claude --resume 14318db1-bd0b-4e8c-a423-e4d1d64d2180` or
  `python scripts/claude/claude_jsonl_to_md.py <jsonl> /tmp/<id>.md`.

<!-- BACKLINKS — auto-generated by scripts/regen_wiki_graph.py; do not edit -->
## Backlinks
- [[20260922_1558_shadowed_guards_one_constant]] (episode_renderer, 2026-09-22) — Removing the renderer's legibility floor changed nothing, because the layout reg
<!-- END BACKLINKS -->
