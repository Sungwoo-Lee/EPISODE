---
title: "Code-graph benchmark — does Graft or Graphify help Claude Code on this repo? (results)"
topic: meta
status: active
created: 2026-09-24
last_updated: 2026-09-24
---

# Code-graph benchmark — does a code-graph tool (Graft, Graphify) help Claude Code on this repo?

## Verdict (plain language)

No benefit **detected** for either tool (an underpowered null, not proof of no effect). Across six real past multi-file changes of this repo, replayed as tasks
(3 attempts each per group, 54 sandboxed Claude Code runs, Sonnet), plain Claude Code, Claude Code with Graft,
and Claude Code with Graphify all solved **18/18** attempts, broke no neighbouring tests, and touched the same
share of the real commit's files. Task-by-task, no difference in time, tokens, turns or tool calls was detected, but the 95% intervals are
wide enough (Graft wall-clock 0.62-1.17) that a 25-40% gain cannot be excluded. The Graft agents **never called a
Graft tool, command, or read its graph folder** (0/18 runs); Graft reached them only through hook-injected context
(an 8.3 KB `[graft]` session-start map in every run; the per-prompt and post-edit hooks are not observable in the
event log). Graphify agents skimmed its report (`head -c 2500`) in 12/18 runs but never ran a Graphify command.

**The pre-registered rule did not name its statistic.** Under one reading (pooled median, -36%) Graft meets the
25% wall-clock bar; under the pooled mean (-21%) and the task-paired estimate (-1%; faster on 3 of 6 tasks, slower
on 3) it does not. We chose the paired estimate after seeing the data. We report the rule as **not decisively met**
and record the ambiguity as a flaw in the pre-registration.

**Correctness tested nothing:** every group — including the baseline — solved 18/18, so criterion (a) could not be
met by design.

Plan (with Revisions 2-3 applying the plan review): `[[CODE_GRAPH_BENCHMARK_PLAN]]`.
First, flawed test (2026-09-22; lookup questions, tool delivery inactive): `tmp/20260922_130852_graft_headtohead.md` (gitignored working file).

## Pre-registered decision rule and how it came out

Rule (plan Revision 2): a tool is *beneficial* only if (a) it resolves ≥3 more attempts than baseline with no
more P2P breakages, or (b) it matches baseline correctness within 1 attempt AND uses ≥25% fewer total tokens or
≥25% less wall-clock.

- (a) fails for both tools — every group scored 18/18 (ceiling).
- (b) tokens: fails for both (paired ratio 0.99 G, 1.02 F).
- (b) wall-clock: **not decisively met.** Pooled median 307 s (G) vs 478.5 s (A) = -36% (meets the bar);
  pooled mean 359 vs 454 = -21% (fails); task-paired geometric mean of per-task median ratios 0.99 (95% bootstrap
  0.62-1.17; fails). G was 0.38x on T3 and 2.47x on T2; pooling tasks of very different length lets those two
  dominate. The paired statistic was chosen after seeing the data. Wall-clock is also confounded by machine load
  (see Limitations).

## Results

| Group | Correct | Broke neighbouring tests | Ref-set recall | Median wall s | Median total input tokens | Median tool calls | Used the tool |
|---|---|---|---|---|---|---|---|
| A — plain Claude Code | 18/18 | 0 | 0.86 | 478.5 | 1,105,740 | 18.5 | — |
| G — Graft (hooks + MCP + Sonnet summaries) | 18/18 | 0 | 0.87 | 307.0 | 1,008,660 | 19.0 | 0/18 invoked (context injected in 18/18) |
| F — Graphify (CLAUDE.md section + hook + skill) | 18/18 | 0 | 0.87 | 385.5 | 1,083,844 | 16.5 | 12/18 skimmed GRAPH_REPORT; 0 commands |

Task-paired ratios vs A (geometric mean of per-task median ratios; 95% bootstrap over trials, computed by `_common.paired_ratios`, the same function the page and figure 2 use):

| Metric | G / A | F / A |
|---|---|---|
| wall-clock | 0.99 (0.62-1.17) | 0.97 (0.56-1.57) |
| total input tokens | 0.99 (0.83-1.15) | 1.02 (0.87-1.25) |
| tool calls | 1.06 (0.82-1.20) | 0.96 (0.79-1.12) |
| turns | 1.05 (0.83-1.19) | 0.96 (0.80-1.11) |

Per task (correct/3 · median wall s · median total input tokens):

| Task | A | G | F |
|---|---|---|---|
| T1 thermal warming/cooling speeds | 3/3 · 593 · 1.37M | 3/3 · 518 · 1.33M | 3/3 · 804 · 1.80M |
| T2 MC_FIXED return mode | 3/3 · 322 · 0.69M | 3/3 · 796 · 1.08M | 3/3 · 173 · 0.86M |
| T3 blur knobs conditional-mandatory | 3/3 · 502 · 0.99M | 3/3 · 191 · 0.76M | 3/3 · 463 · 0.79M |
| T6 dashboard never refuses a range | 3/3 · 498 · 1.49M | 3/3 · 461 · 1.22M | 3/3 · 458 · 1.10M |
| T7 band declares the painter's width | 3/3 · 164 · 1.11M | 3/3 · 192 · 1.08M | 3/3 · 206 · 1.24M |
| T8 GAE_NORM / MC_RAW modes | 3/3 · 107 · 0.58M | 3/3 · 112 · 0.60M | 3/3 · 118 · 0.62M |

One-off setup cost: Graft Sonnet summaries 41.7 min / 569 calls from scratch, 21-47 min per later snapshot
(cache-seeded), ~$62 API-equivalent in total on the subscription; Graphify ~9 s per snapshot, no model calls.

## Why no benefit here (interpretation)

1. **Ceiling — two competing explanations.** Plain Claude Code solved every task every time. Either (i) on this
   consistently named, heavily commented repo Sonnet localises multi-file changes by grep reliably, or (ii) the
   task prompts were specific enough to point at where the code lives ("add `validate_return_mode` to the
   recurrent PPO trainer module", "the layout registry … the painter", exact equations) — partly forced by the
   requirement that prompts carry every name the hidden tests assert. This benchmark cannot tell (i) from (ii). The published gains (RepoGraph +32.8% relative on SWE-bench-Lite)
   come from settings where the baseline fails often.
2. **The agents do not reach for the tools.** Even with Graft's MCP tools connected and its context injected,
   and with Graphify's CLAUDE.md rule "ALWAYS read GRAPH_REPORT.md before … grep", the agents went straight to
   Grep/Read (Graft agents even excluded `graft/` from their globs). Graphify agents ran grep/rg through Bash
   130 times, so its PreToolUse nudge should have matched; whether it fired and was ignored is not observable in
   the event log.
3. **Fixed context dominates tokens.** Each run carries ~60k tokens of system prompt + CLAUDE.md re-read every
   turn (cache reads), so exploration savings of a few thousand tokens are invisible.

## Limitations

- 6 tasks × 3 trials; every group at ceiling, so a correctness difference smaller than a few attempts, or one on
  harder tasks, is not ruled out.
- `docs/` was removed from every snapshot to prevent answer leakage; the real repo's plan-first workflow (plans
  that name the files) would make localisation even easier.
- **Run order / load confound:** runs were NOT fully interleaved — stage-1 A/F ran first, and all Graft runs for
  T1/T6/T7 ran last (19:14-19:42) after the A/F runs of the same tasks, with 4-7 runs sharing the machine at
  different times. Agents run CPU-heavy tests, so wall-clock is confounded by load; tokens and correctness are not.
- **Grader gaps (no observed effect here):** existing test files an agent edited are not reset before grading
  (all 9 T8 runs edited `test_mc_fixed_mode.py`, all 9 T7 runs edited `test_dashboard_layout.py`; every deleted
  line was checked — all additive or stricter). Reference-set recall is capped at 0.6 on T7/T8 because the
  reference set includes config YAMLs the tests never need; the grader self-check's "recall 1.0" was 1.0 by
  construction. T3's correctness rests on a single fail-to-pass test.
- Bootstrap uses 3 runs per cell; code saved as `scripts/analysis/studies/code_graph_benchmark/_common.py` (`paired_ratios`).
- Graphify ran without LLM doc extraction; Graft ran with Sonnet summaries.
- The user's claude.ai connectors loaded in every run (all arms; not callable).

## Artifacts

Harness scripts, prompts, grading lists, per-run scores / patches / event streams: `data/` in this folder (per-run scores, patches, tool-use counts, harness scripts, prompts, grading lists); raw event streams stay in the gitignored `tmp/20260924_graft_bench/runs/*/stream.tsv.gz`.

## Verdict review

plan-reviewer (analysis gate), 2026-09-24: **SUPPORTED WITH CAVEATS** — 'no benefit shown' holds; wording corrected above for the post-hoc statistic, the false 'never invoked' argument, the run-order confound, the Graphify-nudge claim, the ceiling's competing explanation, and the grader gaps.

## Artifact

Compact page: <https://claude.ai/artifact/ScnqjBbvp4vVjbNnAhfB8g> — `code_graph_benchmark.html` in this folder, built by `python scripts/analysis/studies/code_graph_benchmark/build_page.py`.
