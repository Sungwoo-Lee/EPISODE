---
name: takeaway
description: "Answer the current job or analysis in a compact, plain-English summary that leads with the take-home message: one take-home sentence, up to six evidence bullets, a 'how sure are we' line, a 'what it means / next' line, ~300 words. Jargon is explained on first use or replaced by plain words. Numbers are re-checked against the files. Print-only — writes nothing. Trigger on /takeaway, 'what's the takeaway', 'bottom line', 'so what did we find', 'give me the short answer'."
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
**Take-home:** <one sentence: the answer, in plain English>

**Why we think so**
- <evidence, plain words; a number with its unit and what it is compared with>
- <at most six bullets; each may take two sentences: the finding, then why it matters>

**How sure are we:** <one or two sentences: what the evidence rests on (seeds, sample size,
checks done) and what could still overturn it>

**What it means / next:** <one or two sentences: the consequence, then the next step or decision>

Details: <one owning doc link>
```

## Rules

- **Take-home first**, always — the conclusion, not the background. If confidence is limited (one seed,
  a small sample, an unchecked number), the take-home or a bullet says so in plain words.
- **Jargon:** use plain English wherever the term is not needed. When a term *is* needed (it is what the
  docs and pages call it), explain it the first time, plain words first and the term in parentheses:
  "extra time hiding in a bush when hurt (injury effect)". After that the term alone is fine.
- No run IDs, SHAs, config paths, flag names or bare shorthand (`H₁a`, `Δ_SS`) — describe what they are.
  Use the project's own vocabulary (CLAUDE.md, Conventional terms only).
- **~300 words cap**, excluding the Details line. Aim for 200–300; cut bullets before cutting the explanation of a term.
- Numbers keep their units and a comparison ("11.0 vs 9.1 percentage points", not "11.0").
- One Details link to the owning doc; the user opens it for depth.
