---
name: takeaway
description: "Answer the current job or analysis in a compact, plain-English summary that leads with the take-home message: a take-home box, a small table of the key numbers against their comparison, a plain-words key to the table, 'how sure are we' and 'next' lines, ~300 words. Jargon is explained on first use or replaced by plain words. Numbers are re-checked against the files. Print-only — writes nothing. Trigger on /takeaway, 'what's the takeaway', 'bottom line', 'so what did we find', 'give me the short answer'."
---

# /takeaway — the short answer to the current job

Sibling of `/progress`: `/progress` says **what has been done**; `/takeaway` says **what it means**.
Scope is the line of work this session is doing **right now** (an analysis, a bug hunt, a design
question). Earlier, finished lines of work in the same session are left out. Writes nothing: no board,
diary or commit.

## 1. Gather (read-only)

- **Conversation:** the question the current job is answering, the latest answer reached, and anything
  that was later corrected (the correction wins).
- **Owning doc / results:** the design or analysis doc, results table or figure data the job produced.
- **Check every number** you are about to print against that file (re-read it, in `timeout 20` for
  git or large reads). A number you cannot find in a file is dropped, or kept with "(not yet checked)".
  If the job has no conclusion yet, the take-home says so plainly ("No answer yet: …").

## 2. Print

```
> **Take-home:** <one or two sentences: the answer, in plain English>

| <What was measured> | <Result> | <Compared with> | <Verdict> |
|---|---|---|---|
| <plain-English name of the measure> | <number + unit> | <reference value or range> | <yes / no / lower / unclear> |

**Reading the table:** <one or two sentences defining each measure in plain words, and what the
comparison column is (e.g. "the range of the six existing agents, i.e. seed-to-seed variation")>

**Also worth knowing:** <optional, at most three short bullets for findings that don't fit a row>

**How sure are we:** <one or two sentences: what the evidence rests on (seeds, sample size,
checks done) and what could still overturn it>

**Next:** <one or two sentences: the consequence, then the next step or decision>

Details: <one owning doc link>
```

- The **take-home box** carries the whole answer: someone who reads only it must get the conclusion.
- The **table** holds the 2–6 numbers the take-home rests on, one row each. The verdict column says,
  per row, whether that number supports the take-home. Cells stay short; explanations go in
  "Reading the table", not in the cells.
- A job with no numbers (a bug hunt, a design choice) replaces the table with a table of the options
  or causes considered: `| Option / cause | What we found | Verdict |`.

## Rules

- **Take-home first**, always — the conclusion, not the background. If confidence is limited (one seed,
  a small sample, an unchecked number), the take-home or a bullet says so in plain words.
- **Jargon:** use plain English wherever the term is not needed. When a term *is* needed (it is what the
  docs and pages call it), explain it the first time, plain words first and the term in parentheses:
  "extra time hiding in a bush when hurt (injury effect)". After that the term alone is fine.
- No run IDs, SHAs, config paths, flag names or bare shorthand (`H₁a`, `Δ_SS`) — describe what they are.
  Use the project's own vocabulary (CLAUDE.md, Conventional terms only).
- **~300 words cap**, excluding the Details line. Aim for 200–300; cut table rows and extra bullets before cutting the explanation of a term.
- Numbers keep their units and a comparison ("11.0 vs 9.1 percentage points", not "11.0").
- One Details link to the owning doc; the user opens it for depth.
