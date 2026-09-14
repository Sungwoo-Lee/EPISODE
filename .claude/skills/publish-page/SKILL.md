---
name: publish-page
description: "Publish a finished piece of work as an Artifact — a private web page on claude.ai with its own shareable URL — instead of leaving it as a file path or a wall of terminal text. THIS SKILL IS THE ONLY ROUTE TO THE `Artifact` TOOL: it carries the project's own artifact rules, which the native tool knows nothing about. Use for anything with figures to compare (matplotlib PNGs, kernel/parameter sweeps, before-after plots), a decision to be made from evidence, an experiment write-up, a mechanism study, or a doc a collaborator will read. Trigger on /publish-page, 'publish that', 'put that on a page', 'make it a page I can share', 'give me a link', 'artifact', 'share this with the lab', 'update the artifact/page', or any request to see several figures side by side — and on your own initiative whenever you are about to call `Artifact` for any reason, including a republish. Also use proactively when a reply would otherwise be six file paths the user must open one at a time. Do NOT use for scratch output, a single number, a one-paragraph answer, or anything the user asked to keep local."
---

# publish-page — the gate in front of the Artifact tool

`Artifact` is a **native Claude Code tool**. It renders a local HTML file to a private page on
claude.ai and returns a URL. It knows nothing about this project — not its terminology rules, not
its figure requirements, not the thirty-six format defects this project has already shipped and
diagnosed. Those rules live in the repo, and nothing in the tool call loads them.

**That gap is the reason this skill exists.** Left to itself, "make me an artifact" reaches the
native tool directly and the project's own accumulated rules are never consulted — which is exactly
how a page shipped with three lists rendering one word per line, and how a figure viewer that had
worked for weeks on one page failed to reach the next one built from the same pattern.

> **If you are about to call `Artifact` and have not worked through the steps below, stop and do
> them.** That includes a republish of a page you built earlier in the same session: the rules
> apply to the version being shipped, not to the first one.

> Lives at project level, not `~/.claude/skills/`, because Claude runs in a Docker container
> whose home directory does not persist — only this repo on the NAS survives a container
> rebuild. Anything that should outlive the session belongs in the repo.

## When NOT to use
- Scratch, intermediate, or debug output — that goes to `tmp/YYYYMMDD_HHMMSS_<topic>/` per CLAUDE.md.
- A short answer that fits in the reply. Publishing it adds a click, not clarity.
- Anything the user asked to keep local, or anything containing credentials / unpublished data
  they have not agreed to put on a hosted page. **When in doubt about sensitivity, ask first** —
  publishing is outward-facing and the URL exists whether or not it is shared.

---

## Step 0 — read the project's artifact rules. Every time.

Two documents. Neither is optional, and neither is loaded by anything else:

| read | what it is |
|---|---|
| [`artifact_generation_guide.md`](../../../docs/develop/active/meta/artifact_generation_guide.md) | The content rules: terminology (§1), figures (§2, including §2.6 click-to-open-full-size), structure (§4), reproducibility (§5), claims (§7), the **pre-publication checklist (§8)**, and the three standing requirements (§11). ~440 lines. |
| [`artifact_format_bugs.md`](../../../docs/develop/active/meta/artifact_format_bugs.md) | The format-defect register, F1–F36 plus amendments. Each entry is a defect that **shipped**, why both static review and a screenshot scan missed it, the rule, and how to verify a fix. Read the headings; open any entry that touches what you are about to build. |

Read the guide in full on the first artifact of a session. On a later artifact in the same session,
re-read **§8 (the checklist)** and **§11** at minimum — those are the parts that decide whether the
page ships.

If a rule in either document is wrong or has been overtaken, say so and fix the document. Do not
work around it silently; the value of both files is that they are believed.

## Step 1 — design

**Load the `artifact-design` skill.** Required before writing the file, every time. It calibrates
how much design the piece actually warrants.

## Step 2 — build the page

**Use the house style — required, not a suggestion (guide §0a).** [`house_style_sheet.template.html`](../../../docs/develop/active/meta/house_style_sheet.template.html)
is the default look for every artifact page: Pretendard body text, IBM Plex Sans Condensed headings,
the green-grey palette, `01`-style section numbers, callout boxes, tabs, glossaries, step lists and
tables. Copy its `<style>` block (fonts included) rather than inventing a new look, and depart from it
only for a reason the page states on the page. Figures are drawn only by Python scripts through
`scripts/analysis/style/house.py`, saved as files and embedded — never drawn in the HTML (guide §2.7). Published as
*House Style Sheet*: https://claude.ai/code/artifact/a273f767-34de-47c6-899d-0162b1f3a7ee

Write a self-contained `.html` file (usually into the same `tmp/<timestamp>_<topic>/` directory as
the scripts that produced the figures, so the page and its source sit together — or, for a study
that owns a docs folder, alongside its design doc). Write page content only — no `<!DOCTYPE>`,
`<html>`, `<head>` or `<body>` tags; those are added at publish time. Put a real `<title>` at the top.

**The three standing requirements (guide §11) are build-time, not review-time** — a violation is a
build failure, not a finding:

1. every figure caption states **both axes in words**, with units, repeated per figure;
2. every figure declares **how much data it used** — used / available / percentage per subset, with
   a reason, *emitted by the figure script and never typed by hand*;
3. every **"How it is computed"** block is written for a colleague who was not in the room, roughly
   150–250 words, with any statistical term glossed where it appears.

And **§2.6**: every raster figure opens at full size on click, with a keyboard route and a hint.
The house template already carries the viewer with the house tokens — copy it from there, and check
the page defines every token the copy references.

## Step 3 — the format gate. Before publishing, not after.

**Spawn [`artifact-format-reviewer`](../../agents/artifact-format-reviewer.md).** It renders the
page in headless Chrome at several viewport widths, *looks at the screenshots*, and checks it
against the register. Give it the list of what changed since its last pass so it reviews the new
work as new.

**Do not publish on a DO NOT PUBLISH verdict.** Fix, then re-gate. This gate exists because two
rounds of careful review that read the HTML and CSS without ever rendering them both missed three
lists rendering one word per line, which the user saw instantly.

When it finds a defect class that is not yet in the register, **add it** — with what a reader saw,
why both review methods missed it, the rule, and how to verify a fix. The register earns its keep
only if it grows.

## Step 4 — publish

- **Republish the same file path to update in place** — same URL, no second link.
- **From a different session or after a compaction**, pass the artifact's `url`; publishing without
  it creates a duplicate. Find old ones with `action: "list"`, and `action: "read"` before you
  publish over something this session has not touched.
- Give a one-sentence `description` (it becomes the gallery subtitle) and, on a first publish, a
  `favicon`. Never change a favicon on a republish — users find the tab by its icon.

## Step 5 — after

Log it. A published or republished artifact is a notable event: `/diary` with the URL, per the
diary protocol in CLAUDE.md.

---

## Conventions that make these pages worth re-reading

Carry the project's documentation framing (CLAUDE.md) onto the page — it is a doc like any other:

- **Lead with a plain-language entry point.** First section says what the page is about, why it
  exists, and what it claims, in English a reader without context can follow. Translate every
  symbol, run ID, and config path on first mention.
- **Every figure gets a real caption** — what it shows *and* what to conclude from it. A figure
  with no caption is an unlabelled data dump.
- **Say where it came from.** Footer with the path and the command that regenerates the figures.
  A page nobody can reproduce is a screenshot.
- **Separate settled from open.** For a decision page, a two-column ledger of what is decided
  and what is still open beats prose — it is the thing the user actually came for.
- **State corrections.** If the measurements contradicted an earlier claim of yours, say so on
  the page rather than quietly shipping the corrected version.

## Mechanics and gotchas

- **Self-contained only.** A strict CSP blocks external hosts. Embed PNGs as
  `data:image/png;base64,...` (a `base64.b64encode` in the page-builder script), inline all CSS
  and JS. Google Fonts is the single exception. Page must stay under 16 MB.
- **Images live in the file.** Once published, the page does not depend on the NAS staying
  mounted or the `tmp/` directory surviving.
- **Tag each `<img>` with the figure it holds** (`data-fig="<stem>"`) and re-embed by that key.
  Matching a base64 blob to its PNG by the caption next to it works for two figures; at nine it is
  how the wrong image ends up under the right caption.
- **Math.** Real equations go in a styled block; inline expressions with subscripts go in
  `<code>`; single symbols as Unicode (γ β τ σ ρ Δθ ∥ ⊥). Same reasoning as the chat renderer
  rule in CLAUDE.md, for the same reason.
- **Comments.** Viewers can leave comment threads; read them with `action: "comments"` and reply
  into any thread the user activates for Claude. Often the easiest way for the user to mark up a
  specific figure.

## Pattern: a figure-set page

Generate figures with a plotting script, then a small `build_page.py` that base64-embeds each PNG
and writes `index.html`. Keeps the page regenerable rather than hand-assembled — edit a caption or
a parameter, re-run two commands, republish to the same URL. One script per figure (guide §5): a
missing figure is then a missing file, and the merge step refuses to build a partial set.
