---
id: 20260909_1505_one_python_figure_pipeline_not_split
date: 2026-09-09
time: "15:05"
folder: behavior_measures
tags: [design, decision, meta, learned_lesson]
summary: "User rejected splitting figure work into a Python script that computes numbers and JavaScript that draws them: it makes each figure two artifacts that must agree with nothing forcing it, and a browser-drawn figure cannot go into the paper. One Python one-script-per-figure pipeline stands. Separately, a01's refactor to that pattern stalled at 6 of 19 scripts and its merge output is read by nothing."
related: []
session_origin: claude_code
session_label: "hiding-artifact inventory + Hiding Factor Atlas"
importance: high
status: settled
valid_until: null
confidence: high
supersedes: []
raw_source: claude_data/.claude/projects/-media-nas01-projects-Interoceptive-AI-grid-world-pain/745adcad-de68-49fe-bbd5-e1086dec05a8.jsonl
raw_completeness: full
---

# One Python figure pipeline, not a Python/JavaScript split — and the a01 refactor that stalled

## Key conclusion

The project has two ways of getting a figure onto a published page. The sensor-ladder study runs a
Python script per figure that saves a PNG, which the page build embeds. The bush-hiding study's page
does the opposite: it carries a blob of pre-computed numbers and **draws all sixteen figures in the
browser** with hand-written JavaScript that emits SVG.

A proposal to keep the browser-drawing approach and add per-figure Python scripts that emit JSON —
so each figure would have a Python half computing the numbers and a JavaScript half drawing them —
**was rejected by the user**, for two reasons that are worth keeping:

1. **Split-brain drift.** It makes every figure two artifacts that must agree, with no mechanism
   forcing them to. Update one and not the other and the page is silently wrong. That is the same
   failure class the project's one-script-per-figure rule exists to prevent, merely relocated.
2. **Paper reuse.** A figure drawn by JavaScript inside a published page cannot go into a
   manuscript. A figure produced by a script can go into both. The figure-generation pipeline has to
   serve the paper, not only the page.

So: one pipeline, Python-owned, producing real figure files. The browser-drawing design's real
advantages — a 135 KB page instead of 8.4 MB, figures that follow the page's theme, and a rename
that costs a string edit instead of re-running a sweep — do not outweigh those two.

## Evidence, measurements, facts

- The bush-hiding page has **zero images**: no `<img>`, no `data:` URIs, no external requests.
  Two inline `<script>` blocks hold a JSON blob and a hand-rolled SVG helper
  (`createElementNS` wrappers) plus one draw routine per figure. 135 KB total.
- The sensor-ladder page embeds 15 base64 PNGs from matplotlib: 8.4 MB.
- The cost of the PNG route is visible on the ladder page itself: after the project renamed the
  measure "bush dwell" → "bush hiding" (commit `6695aa29`), its figures still show the old word,
  because re-running fifteen matplotlib figures over ~996M rows to change one label was judged not
  worth it. The page carries a disclaimer saying so.
- **The a01 refactor to one-script-per-figure is unfinished and partly inert.** Commit `41cced71`
  (2026-08-25) is titled "Figure 5 rendered empty; **begin** one-script-per-figure refactor":
  - `scripts/analysis/figures/README.md` declares 19 figure scripts plus a parity check;
    `build_figure_data.py` hard-codes an `EXPECT` dict of 18. **Six exist on disk** (fig07–fig12).
  - `run_all.py` globs `fig*.py`, so it runs the six it finds and reports "6 succeeded, 0 failed"
    — a clean pass over an incomplete set. The loud failure only arrives at `build_figure_data.py`.
  - `build_figure_data.py` writes `results/analysis/figures/all_figures.json` and **nothing in
    the repo reads it**. There is no `build_artifact.py` for a01, so even the six working scripts
    never reach the published page; its data blob is pasted by hand.
  - The registry has drifted from the page: `EXPECT` is numbered 2–19 while the shipped page has
    Figure 1–16, so the count of what is missing is itself uncertain.
- The ladder's `build_artifact.py` is the working model of the merge step and fails loudly on: a
  token naming a figure with no PNG; a figure with no generating script; a figure shown twice; a
  caption with no axes sentence; a missing "How it is computed" block; a figure whose script
  recorded no data accounting; any unsubstituted token; a figure on disk the page never shows; and
  scripts and shown figures disagreeing.
- Gap for paper reuse: `scripts/analysis/ladder/_plot.py::finish()` calls `fig.savefig(path)` and
  every caller passes a `.png`; rcParams set `figure.dpi`/`savefig.dpi`. **PNG only** — no vector
  output. Reusing these figures in a manuscript needs a PDF or SVG emitted from the same script.

## Decisions and actions

- **Decided**: consolidate a01 onto the ladder's Python one-script-per-figure pipeline. Do not
  introduce a JavaScript drawing layer with its own per-figure modules.
- **Open, needs the user**: whether the pipeline should emit a vector format alongside the PNG the
  page embeds, and whether that is retrofitted to the ladder's fifteen figures or applied to a01 only.
- Handover prompt for a fresh session written to
  `tmp/20260909_133208_a01_figure_pipeline_handoff.md`. It records the rejected proposal and the
  reasoning explicitly, so the next session does not re-propose it after reading the current page.
- Suggested order: re-derive the figure-number mapping against the shipped page first (the registry
  is stale and everything downstream inherits its numbering), settle the vector question, write the
  missing scripts, then write a01's `build_artifact.py` with the ladder's gates.
- **Expect published numbers to move.** The generation guide §5 records that rewriting figures this
  way already surfaced undocumented drift once — a number went 20.7% → 18.9% purely because the
  original conditioned on `t>=2` and the rewrite on `t>=1`. Neither was wrong; the difference was
  invisible until the choice had to be written down. Any such move is adjudicated with the user, not
  absorbed inside a refactor.
- Do not "fix" `hiding_drivers.py:214`'s contemporaneous injury binning inside this work — it is a
  separately registered item, deliberately reproduced bug-for-bug by the ported scanner.

## Open questions and follow-ups

- Vector output: PDF, SVG, or both, and retrofit scope.
- Whether the six existing a01 scripts still reproduce the numbers on the published page, given the
  registry/page numbering drift.
- `scripts/analysis/hiding_drivers.py` is deliberately kept (an earlier study names it as its
  producer, and the ladder's `lad06` filters arms by its CSV path); a consolidated pipeline has to
  decide whether that stays a permanent second producer.

## References

- Rule: `docs/develop/active/meta/artifact_generation_guide.md` §5 ("One figure, one script"),
  checklist lines "One script per figure, and the merge step fails loudly"
- Diary origin of the rule: `docs/diary/2026-08-30.md` (sensor-ladder session)
- Working model: `scripts/analysis/ladder/build_artifact.py`, `_plot.py`, `lad01`–`lad15`
- Stalled refactor: `scripts/analysis/figures/` (README, `build_figure_data.py`, `run_all.py`)
- Handover: `tmp/20260909_133208_a01_figure_pipeline_handoff.md`
- Pages: hiding study https://claude.ai/code/artifact/1351009f-d7f7-4114-a290-f6582bb9a004 ·
  sensor ladder https://claude.ai/code/artifact/3d191a81-2aec-4f97-a3e8-993568936b5b
- Raw conversation: synced via `./sync-agent-data.sh claude push`. To read on another node:
  `./sync-agent-data.sh claude pull`, then either `claude --resume 745adcad-de68-49fe-bbd5-e1086dec05a8` or
  `python scripts/claude/claude_jsonl_to_md.py <jsonl> /tmp/<id>.md`.

<!-- BACKLINKS — auto-generated by scripts/regen_wiki_graph.py; do not edit -->
## Backlinks
- _no inbound links yet_
<!-- END BACKLINKS -->
