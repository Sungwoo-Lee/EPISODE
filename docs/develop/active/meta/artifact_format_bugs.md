---
title: Artifact format bugs — the register, and why reading the CSS never finds them
topic: meta
status: active
created: 2026-08-31
last_updated: 2026-09-09
---

# Artifact format bugs

## Why this document exists

The sensor-ladder artifact shipped with three numbered lists rendering **one word per line**, prose
spilling out of its column, and code chips overflowing their boxes. The page had been checked twice
before it shipped: once by me, once by a dedicated reviewing agent given a long, specific brief
about cascade collisions, grid containment, theme tokens and table overflow. That agent produced a
genuinely excellent report — it found a defect that made the whole page scroll sideways on every
phone — and it **did not find the one-word-per-line bug**. Neither did I.

The user found it in about one second, by looking at the page.

That is the lesson this document exists to encode. **Every format check before this one was static
analysis: reading HTML and CSS and reasoning about what they would produce. Chrome has been
installed in this container the whole time.** A defect that lives in the box tree rather than in the
stylesheet text is invisible to reading and obvious to rendering. The fix is not a better brief. It
is to render the page, measure it, and look at it.

## The protocol, from now on

Before publishing or republishing any artifact:

```bash
python scripts/claude/check_artifact_layout.py <page.html> --out tmp/artifact_layout
```

It wraps the page in the same skeleton the Artifact host injects at publish time, renders it in
headless Chrome at several viewport widths, and reports horizontal page overflow, boxes that escape
the viewport, text squeezed into an absurd column, elements with text but zero height, text
overlapping text, and image problems — then writes a full-page screenshot per width. **Exit code is
non-zero when it finds anything.**

Then **open the screenshots**. The measurements catch geometry; they do not catch ugly. Both steps
are required, and the second one is the one that found the bug that started this document.

Then hand the page to the [`artifact-format-reviewer`](../../../../.claude/agents/artifact-format-reviewer.md)
agent, which runs the tool, reads this register, and looks at the rendering.

### Known limits of the tool

- **Chrome headless floors the viewport at 500px.** Asking for 390 silently renders 500. Genuine
  phone-width layout is therefore not covered; the tool says so when you ask for less.
- It renders a *lean* copy with the inlined images swapped for same-aspect placeholders, so the run
  is fast. Text layout is identical; anything about the image content itself is not tested.
- It knows nothing about whether the design is good, whether a colour means two different things,
  or whether an axis label is wrong. Those need a reader.
- **It does not tell you whether the web fonts actually loaded.** A page measured under the DejaVu
  fallback has different metrics from the same page under its real faces, so a `min-width` floor
  derived in a fallback render can be wrong on every reader's screen. Probe `document.fonts` for
  `status === 'loaded'` on each declared family before trusting any width measurement
  (see [F35](#f35), whose floor-vs-content check is only as good as the face it was measured in).
- **`--out` is a shared directory, not a per-page one.** Two pages checked into the same `--out`
  overwrite each other's screenshots, and the second review then reads the first page's rendering.
  Give each page its own directory — `tmp/artifact_layout_<page>` — whenever more than one page is
  in flight, which on this project is most of the time.

---

## The register

Each entry is a defect that actually shipped or nearly shipped, what a reader saw, why the static
review missed it, and the rule that would have caught it.

### F1 — `display:grid` turns bare text into anonymous grid items

**Saw:** three numbered lists rendering one word per line in a ~40px column, with `<code>` chips
overflowing to the right and an `<em>` overlapping the word before it.

**Cause:** `.caveats li{display:grid;grid-template-columns:26px 1fr}` where the `<li>` content was
`<strong>…</strong> text <em>…</em> text <code>…</code> text`. In a grid container **every
contiguous run of bare text becomes its own anonymous grid item**. The author counted two items —
the `::before` counter and "the content" — but there were seven, so the prose alternated between the
26px counter column and the content column.

**Why reading missed it:** the CSS is correct in isolation and the HTML is valid. `<strong>` inside
`<li>` is fine; `display:grid` is fine. The defect exists only in the box tree, which requires
enumerating the element's *children* — including text nodes — and applying the anonymous-item rule.
Two sibling lists on the same page used the same CSS and looked fine, because their content happened
to be wrapped in a single child element, which made the pattern look proven.

**Rule:** never put `display:grid` or `display:flex` on an element whose children include bare text.
For a counter-and-content list, place the counter with `position:absolute` inside a
`position:relative` list item; it is immune to whatever inline markup the content contains.

### F2 — a grid item's automatic minimum size is its content minimum

**Saw:** the entire page scrolled sideways — 800px of drag on a phone, 110px even at 1300px.

**Cause:** `<main>` was a grid item in a `1fr` track. A grid item's automatic minimum size is its
*content* minimum, and `figure img{width:100%}` contributes the image's **intrinsic** width during
intrinsic sizing (a percentage width resolves to `auto` there). The inlined PNGs are 2000–3600px
wide, clamped by `.wide{max-width:1120px}`, so the track could never be narrower than 1120px.
`img{max-width:100%}` does not help — a percentage max-width is also ignored for intrinsic sizing.

**Rule:** every grid or flex item that contains content wider than the layout gets `min-width:0`.

### F3 — a utility class beats a type selector, silently

**Saw:** every figure and every section divider lost its vertical margin; figures butted against the
prose above them.

**Cause:** `.col{margin:0 auto}` and `.wide{margin:0 auto}` are class selectors (0,1,0) and beat
`figure{margin:44px 0}` and `hr{margin:70px 0}` (0,0,1) regardless of source order. The shorthand
claimed all four sides.

**Rule:** a centring utility sets `margin-left`/`margin-right` only, never the `margin` shorthand.

### F4 — `overflow:auto` clips the caption too

**Saw:** scrolling a wide table sideways carried its own title off the left edge, leaving a floating
border.

**Cause:** `<caption>` is a child of `<table>`, which was inside the `overflow-x:auto` box.

**Rule:** a scroll container holds only the thing that scrolls. Titles, captions and controls are
siblings of it.

### F5 — `position:sticky` constrains the margin box, so padding pushes the element down

**Saw:** the sticky table of contents floated 130px below the top of the window, permanently.

**Cause:** `.toc{position:sticky;top:34px;padding-top:96px}`. The sticky offset applies to the
margin box, so the content began at 34+96. Moving it to `margin-top` does not help either.

**Rule:** when a sticky element has leading padding, subtract it from `top`.

### F6 — `width:100%` inside a scroll box squeezes instead of scrolling

**Saw:** on a narrow screen, 50-character table headers crushed into 100px columns, five lines tall,
while the scroll container never scrolled.

**Cause:** `table{width:100%}` fills the `.scroll` box exactly, so there is never any overflow to
scroll.

**Rule:** a data table inside a scroll container is `width:max-content;min-width:100%` — natural
width, at least filling the box.

> **Amended after F24 — this rule holds only for tables whose columns are all short or numeric.**
> F6 and F24 are the two ends of one trade-off, and the register has to say which applies when.
> Under `max-content`, a cell containing a *sentence* claims that sentence's full unwrapped width, so
> the table outgrows its scroll box and the **last column disappears at desktop width** (F24) — a far
> worse failure than F6's, because F6 is visible and F24 is not. The split:
>
> | Table | Rule |
> |---|---|
> | every column short or numeric | `width:max-content; min-width:100%` (F6 as written) |
> | any column carries prose | `width:100%` **plus** a `min-width` floor (≈560px), `nowrap` on the numeric cells only |
>
> The `min-width` floor is what keeps the prose case from falling back into F6's ribboning: below the
> floor the box scrolls (signalled, expected on a phone) instead of crushing prose into one-to-two-word
> lines. Never put `white-space:nowrap` on `th` — a long header forces the same overflow F24 describes.

### F7 — `scroll-margin-top` has to be on the element the anchor targets

**Saw:** clicking a table-of-contents link parked the heading flush against the top of the window.

**Cause:** the property was on `h2`; every anchor targeted the enclosing `<section>`.

**Rule:** put it on `[id]`, or on whatever actually carries the anchor.

### F8 — a percentage `max-width` does not stop an unbreakable string

**Saw:** a 54-character file path overflowed the text column on a narrow screen.

**Cause:** inline `<code>` with no wrapping opt-in.

**Rule:** `code{overflow-wrap:anywhere}`.

### F9 — the host declares `color-scheme: light` and nothing else

**Saw:** bright light-mode scrollbars on dark panels in dark mode.

**Rule:** declare `color-scheme:light dark` on `:root` and pin it in each explicit theme block.

### F10 — panels a reader is asked to compare, drawn on different scales

**Saw:** a three-panel figure whose entire purpose was "these three answers differ" gave each panel
its own y-range, so the panel showing the *wrong* answer looked as strong as the right one.

**Rule:** panels presented as a comparison share a scale. If one then looks flat, that is the
finding.

### F11 — one colour, five meanings

**Saw:** red meant sign-of-change, predator, cause-of-death, heavy-wound, and
cannot-resolve-identity — twice within a single image.

**Rule:** fix the colour→meaning map once, in the shared plotting module, with a comment. A reader
who learns a colour on figure 3 must not be punished for carrying it to figure 8.

### F12 — more than about six series in one colour ramp

**Saw:** 14 and 28 lines in a continuous viridis ramp, where adjacent ramp colours were exactly the
series the text asked the reader to tell apart.

**Rule:** colour by the distinction the argument turns on, draw the rest thin, and label the
discussed series directly on the line.

### F13 — per-row annotations not reordered when the rows were

**Saw:** every value label in the report's headline figure sat on the wrong bar. The 166-step bar
was labelled 250; the longest bush-dwell bar was labelled with the smallest number.

**Cause:** fixing F-something-else (the y-axis said "poorest at the bottom" while plotting the
poorest at the top) meant changing the bar order from `np.arange(n)[::-1]` to `np.arange(n)`. The
bars moved. The separate annotation loop still placed its text at `len(arms) - 1 - i`, which was
correct only for the old order.

**Why nothing caught it:** the figure is internally plausible — the bars are right, the axis labels
are right, and every number printed is a real number from the data. Only cross-referencing a label
against the bar it sits on reveals it. The geometry checker cannot see it (nothing overlaps or
overflows), and a reader who does not already know the result will not notice.

**Rule:** draw an annotation from the same row object as its bar, never from a parallel index. Where
that is impractical, **read both back off the axes and assert they agree** — `lad01_ladder_overview.py`
now does exactly this, comparing every `axis.texts` entry against the `axis.patches` bar at the same
y, and refusing to write the figure if any disagree.

### F14 — an author `display` rule defeats the `hidden` attribute

**Saw:** the full-screen figure viewer rendered open on page load, dimming the whole article, in any
host that does not mark its `[hidden]` rule `!important`.

**Cause:** `.lb{display:flex}` on an element whose only closing mechanism is the `hidden` attribute.
The UA's `[hidden]{display:none}` loses to any author `display` rule. The layout checker's own
skeleton *does* use `!important`, which is precisely why its screenshots looked fine — the bug was
invisible to the tool that should have caught it.

**Rule:** every element toggled with `hidden` carries its own `.x[hidden]{display:none!important}`.
Never rely on the host's rule being `!important`.

### F15 — prose repeats a figure's number by hand, and the number moved

**Saw:** after the evaluation sample was tripled and every figure regenerated, about a dozen
sentences still quoted the old values — mostly 0.1–0.4 off the figure sitting beside them, but one
range wrong by 1.3 (a panel described as collapsing "to between &minus;0.0 and &minus;0.7" actually
ran &minus;2.0 to +0.0). One alt-text string still asserted a claim the correction box two paragraphs
below explicitly withdrew, so a screen-reader user got the retracted version.

**Why nothing caught it:** the tables and figures are generated, so they were all correct and
mutually consistent. Only the hand-written sentences drifted, and each one is individually
plausible — you cannot spot it without cross-reading every quoted number against the figure or table
it summarises. The geometry checker sees text, not meaning. A first review that fixed four instances
and stopped left ten behind.

**Rule:** a number that appears in both a figure and a sentence should be emitted by the analysis
code into both, or the sentence should quote a table cell verbatim. Where prose genuinely must
restate a value, a republish after any data regeneration re-scans **every** number in the prose and
in **all** alt text — not only the ones flagged last time. Beware of claiming a page is fully
generated when only its tables are: this report's Method section said "every number on this page is
generated, not transcribed" while a dozen transcribed numbers were stale.

### Tool note — a truncated screenshot is not a review

`check_artifact_layout.py --shot-height` defaulted to 24,000px while these pages run 32,000–37,000px
tall, so the bottom third was never rendered to an image, and a review that only looked at the
screenshots would have silently skipped Sections 6–8, the Method and the Limitations. The
measurements always covered the whole DOM; only the pictures were short. The tool now reports the
page height, and **counts a truncated capture as a problem** with the `--shot-height` value needed to
fix it.

---

### F16 — a regex that edits one of N repeated elements, and reaches into the next

**Saw:** one figure shipped with no "How it is computed" block, and no error anywhere.

**Cause:** a `re.DOTALL` pattern of the form `FIG:lad03.*?<div><h5>How it is computed</h5>...` was
used to replace that figure's method block. Figure 3 had no such block, so `.*?` ran forward into
figure 4 and replaced *its* block instead. Figure 4's own pass then rewrote it correctly, leaving no
trace except a silently missing block.

**Rule:** to edit one of N repeated structures, first slice out that element (`re.finditer` over
`<figure ...>.*?</figure>`, pick the one you want, edit inside it, splice back), so no pattern can
span two of them. And assert the postcondition: the build now fails if any figure lacks an axes
sentence or a method block.

### F17 — content inside a closed `<details>` is laid out but never painted

**Saw:** the layout checker reported 24 text-on-text overlaps on a clean page, all of them a table
cell inside a collapsed panel against the paragraph above it.

**Cause:** a closed `<details>` does not paint its content, but the content still has a layout box —
`getComputedStyle` reports `display: table-cell` and `getBoundingClientRect` returns real
coordinates. Any geometry check that walks the DOM will see it.

**Rule:** a renderer-based checker must skip content inside a closed `<details>`, the same way it
skips `display:none`. `check_artifact_layout.py` now does.

### F18 — an axis label wider than its panel, in a multi-panel figure

**Saw:** in a two-panel figure the two x-axis labels printed through each other mid-canvas, reading
`...below zero = hides LESS when o**aneDIsFFEeRE**NCE in percentage points...`, and the right one
ran off the canvas edge mid-word. Three figures were affected.

**Cause:** the labels had just been *lengthened* — to fix a different defect, F15's cousin, where
"percentage points" alone did not tell the reader an axis was a difference. Matplotlib places an
xlabel centred under its axes and neither wraps nor warns when it is wider than the panel; in a
multi-panel figure it simply overlaps the neighbour.

**Why nothing caught it:** the defect is inside the PNG. The DOM-based layout checker sees an image,
not the text drawn in it, and matplotlib emits nothing.

**Rule:** measure every axis label's rendered extent against its own panel at draw time and refuse
to write the figure on overflow — the same read-back-and-assert pattern F13 mandates for bar
annotations. `_plot.assert_labels_fit(fig, ax)` does this and is called by all fifteen figure
scripts; it immediately caught a fourth figure the human reviewer had not flagged.

### F19 — a collapsed panel is never geometry-checked

**Saw:** nothing, for a while — which is the problem. Once the layout checker was taught to skip
content inside a closed `<details>` (F17), that content stopped being checked at all, and a real
defect sat inside one undetected: at a 500px viewport the notes column of every data panel was
142px wide, crushing a 214-character sentence into a ribbon.

**Cause:** the F17 fix was correct but one-sided. Skipping unpainted content removes the false
positives and the true ones together.

**Rule:** a checker that skips collapsed content must also offer a pass that expands it.
`check_artifact_layout.py --open-details` forces every `<details>` open and re-runs the geometry;
run both passes before publishing. Relatedly, the `<summary>` element itself *is* painted when the
details is closed and must stay in the default pass.

## Checklist

- [ ] `check_artifact_layout.py` exits 0
- [ ] The screenshots have been **opened and looked at**, not just generated
- [ ] No `display:grid` / `display:flex` on any element with bare text children (F1)
- [ ] Every grid/flex item that can hold wide content has `min-width:0` (F2)
- [ ] No centring utility uses the `margin` shorthand (F3)
- [ ] Scroll containers hold only the scrolling thing (F4)
- [ ] Sticky offsets account for the element's own padding (F5)
- [ ] Data tables are `width:max-content;min-width:100%` (F6)
- [ ] `scroll-margin-top` is on the anchored element (F7)
- [ ] Long unbreakable strings can wrap (F8)
- [ ] `color-scheme` declared in all theme paths (F9)
- [ ] Compared panels share a scale (F10)
- [ ] One meaning per colour across the whole figure set (F11)
- [ ] No more than ~6 series distinguished by colour alone (F12)
- [ ] Every per-row annotation verified against the row it sits on (F13)
- [ ] Every `hidden`-toggled element carries its own `[hidden]{display:none!important}` (F14)
- [ ] The screenshots are as tall as the page — the tool now says so
- [ ] Every number quoted in prose AND in alt text re-checked against its figure (F15)
- [ ] Edits to one of N repeated elements are scoped to that element (F16)
- [ ] Geometry checks skip closed `<details>` content (F17)
- [ ] Every axis label measured against its own panel at draw time (F18)
- [ ] The checker run twice: default, and `--open-details` (F19)
- [ ] Breakout wrappers are siblings of the column, not children (F20)
- [ ] Mono-block column alignment uses `&nbsp;` or `pre`, not plain spaces (F21)
- [ ] Numeric table columns are right-aligned, headers included (F22)
- [ ] Every figure has exactly one generating script, and the page says which

### F20 — a nested max-width silently caps a designed-wider element

**Saw:** a four-step pipeline diagram given its own `.wide` wrapper (`max-width:940px`) to break out
of the 720px prose column rendered its step columns at ~130px — three words per line — at *every*
desktop viewport. The layout checker flagged "squeezed column" four times at 834/1100/1440 but named
the symptom, not the cause.

**Cause:** the breakout wrapper was placed **inside** the column it was meant to escape. A child can
never exceed its parent's `max-width`, so the wrapper was inert and the diagram silently inherited
720px. Nothing in the stylesheet looks wrong; the defect lives entirely in the nesting.

**Rule:** a breakout wrapper must be a **sibling** of the column, never a child — close the column
element, emit the wide block, reopen the column. Verify by measuring the element's *rendered* width
against its own `max-width`; if they disagree, an ancestor is capping it. And because closing and
reopening a wrapper is exactly where a spacing artefact would appear, check the **margins at both
boundaries** after the fix, not just the width.

### F21 — column alignment built from collapsible spaces

**Saw:** a monospace block aligning two labelled values with runs of plain spaces
(`value  =  29.0` / `value   =   1.2`) rendered with its `=` signs and values off by a character at
every viewport width. A second block in the same page, built with `&nbsp;`, aligned correctly.

**Cause:** HTML collapses consecutive whitespace. Monospace makes the *glyphs* equal width, which is
easy to mistake for alignment being handled — but the spacing between them is still collapsed to one
space.

**Rule:** in a mono block, build column alignment from `&nbsp;` runs or `white-space: pre`, never
plain spaces. The symptom is subtle — it reads as sloppiness rather than as an error — so it survives
proofreading and only shows up on render.

### F22 — `tabular-nums` mistaken for column alignment

**Saw:** a worked-example table whose numeric columns held mixed signs and digit counts
(`0.58`, `13.95`, `−7.32`, `4.25`) rendered with the decimal points drifting down every column.
`font-variant-numeric: tabular-nums` was set, and the cells were monospace, so the alignment
looked handled.

**Cause:** tabular figures equalise the *width of each glyph*; they say nothing about where the
number starts. A **left-aligned** numeric column still begins every value at the same left edge, so
a minus sign or an extra integer digit shifts the decimal point. Monospace plus tabular-nums makes
the drift look deliberate rather than broken, which is why it survives proofreading.

**Rule:** numeric table columns are **right-aligned** (`td.num, th.num { text-align: right }`) — with
a fixed number of decimal places that right-alignment decimal-aligns for free. Pad with a figure
space (U+2007) only where right-alignment is not wanted. `tabular-nums` is necessary but not
sufficient; align the header cell too, or the column reads as detached from its label.

### F23 — a component's `p{margin:0}` reset, written when the component only ever held one paragraph

**Saw:** a `.correction` callout on the sensor-ladder page, holding a three-paragraph argument,
rendered as one unbroken wall of text. The two paragraph breaks got exactly the within-paragraph
line pitch — measured 0 px gap against a 23.6 px line-height — so the reader saw a block where the
author had written three steps. A pre-existing two-paragraph instance of the same component had the
defect too, unnoticed, because nobody had read it closely.

**Cause:** `.correction p{margin:0}` was written when every instance of the component held exactly
one paragraph, where the reset is correct and invisible. The first instance to hold several inherits
it silently. Nothing overlaps, nothing is clipped, nothing squeezes, and the CSS reads as deliberate
in source review — so **the geometry checker structurally cannot see this**, and neither can reading
the stylesheet. Only looking at the render finds it.

**Rule:** any component that resets `p{margin:0}` must also set `p + p{margin-top: …}`. More
generally: a reset written for a single-child case is a latent defect the first time the component
takes a second child. When adding a paragraph to an existing callout, card or note component, render
it — do not assume the component's spacing was designed for more than it had.

**Verifying a fix:** measure the gap in the box tree rather than trusting the rule was added — and
check the measurement fires by removing the rule and confirming it reports 0 px. A spacing assertion
that has never been seen to fail is not evidence.

### F23 amendment — a component that styles only `p` restyles nothing else

**Saw:** a bulleted list inside a callout rendering one point larger and airier than the paragraphs
directly above and below it, so the callout read as two components welded together. Measured: `li`
at 16.5px/26.7px against `.callout p` at 15.5px/24.3px, and 26px of space after the list against
12px between paragraphs.

**Cause:** `.callout p{font-size:15.5px;line-height:1.57}`. The component had only ever contained
paragraphs, so styling `p` was indistinguishable from styling the component. The first `<ul>` placed
inside one inherited the page's body type instead, and the mismatch is small enough to read as
sloppiness rather than as a bug.

**Why neither review method catches it:** the CSS is correct for everything it was written against,
the markup is correct, nothing overflows or overlaps, and the text is perfectly legible. The defect
is a typographic inconsistency of one point, which a screenshot scan reads as a design choice.

**Rule:** style the component, not the tag it happens to contain — `.callout{font-size:…}` with
children inheriting, or at minimum `.callout p, .callout li`. Whenever a new element type first
appears inside an existing component, check its computed type against a sibling paragraph.

**Verifying:** for each component instance, read `font-size` and `line-height` on every direct child
and assert they agree with the component's paragraphs.

### F24 — `width:max-content` on a table that has a prose column hides the last column, at every width

**Saw:** a new results section whose headline table listed three training arms and their scores. The
score column — `138.2 ± 3.5 / 40.3 ± 0.8 / 41.9 ± 0.7`, the entire point of the section — was off the
right edge of its scroll box at **1440 px**, not merely on a phone. The reader saw a header clipped to
`SURVIVAL` with nothing beneath it. A sweep of the same page then found **eight pre-existing tables**
with the identical defect, including one in an appendix whose third column had never been visible to
any reader at any viewport width since the page was first published.

**Cause:** `table{width:max-content;min-width:100%}` (the F6 rule) tells the table to take its natural
width, and a cell containing a sentence has a natural width of *that sentence on one line*. The rule is
right for the short numeric cells it was written for, and looks proven by the ten other tables on the
same page that use it correctly. Add one prose column and the table silently outgrows the 720 px text
column; the `.scroll` wrapper then does its job and hides the overflow. A long `th` under
`white-space:nowrap` causes the same thing on an all-numeric table.

**Why nothing caught it:** the geometry checker **deliberately exempts any element overflowing its own
scroll container** — that is normally correct behaviour, since a scroll box is supposed to scroll — so
it reports nothing at all. Reading the CSS finds nothing either: the rule is correct in isolation and
has many working instances above the broken one. And with `--hide-scrollbars` set for screenshots, the
render carries no visible cue; the column is simply absent.

**Rule:** `width:max-content` only for tables whose cells are **all short**. Any table with a prose
column is `width:100%`, with `white-space:nowrap` left on the numeric cells so the prose column absorbs
the wrapping. Do not put `white-space:nowrap` on `th` — let long headers wrap to two lines rather than
push a column off-screen.

**Verifying a fix:** the checker's silence is not evidence here. Measure `scrollWidth − clientWidth` on
every scroll container at the **widest** viewport and require it to be zero. Overflow at 1440 px means
the table was never designed to fit — it does not mean the scroll box is working. Some overflow at
phone width is acceptable and expected; overflow at desktop width is the defect.

### F25 — a legibility `min-width` floor carried from one diagram's viewBox to another's

**Saw:** a hand-authored SVG whose labels rendered at **6.6 px** on a phone, directly beneath a CSS
comment promising "a legible floor". The floor was doing nothing, and the comment made it look
handled.

**Cause:** `figure svg{min-width:660px}` had been tuned for an earlier diagram. Rendered label size
is not the floor — it is `floor x fontSize / viewBoxWidth`. The new diagram used a 1000-unit viewBox
with 10-unit labels, so the same 660 px floor produced 6.6 px text where the old diagram had
produced legible text. Nothing in the CSS records which viewBox the constant was derived from, so
the next diagram inherits a number that no longer means anything.

**Rule:** derive the floor per diagram from its smallest label:
`min-width >= 9px x viewBoxWidth / smallestFontSize`. Write the derivation into the comment beside
the rule, not just the result — a bare constant cannot be checked by the next reader. Measure the
rendered size (`svg.getBoundingClientRect().width x fontSize / viewBox.baseVal.width`) rather than
trusting the floor.

### F8 amendment — the 500 px floor in the checker hides F8

**Saw:** two full review passes called a page clean at 500 px; pinned to a real 390 px phone it
scrolled sideways by 35 px, with two monospace paths running off the right edge mid-path.

**Cause:** Chrome headless refuses to open a viewport below 500 px — `--window-size=390` silently
reports a `clientWidth` of 500. A 56-character monospace token at 11.5 px is about 386 px: it fits
the 448 px column a 500 px window produces and overflows the 338 px column a real phone produces. So
the tool's floor sits exactly above the width at which this defect appears, and every rendered pass
reports clean.

**Rule:** `check_artifact_layout.py` now runs a `--pin-width 390` pass by default, pinning
`html,body{width:390px}` inside the 500 px window so the document lays out at the true width, and
reporting the elements whose text cannot wrap. Media queries still see 500 px, so the pinned pass
checks the one thing it can check honestly: does the document overflow its own width. Do not treat a
clean 500 px pass as evidence about phones.

### F26 — a UA-default `<sup>` or `<sub>` widens the line box it sits in

**Saw:** one line inside a three-paragraph callout sat 4-5 px lower than every other line, wherever
the prose carried an exponent. Measured line pitch in that paragraph read `[24, 28, 25]` against a
24.3 px line-height.

**Cause:** the page declared no `sup` rule, so the browser default applied — `vertical-align: super`
with `font-size: smaller` and a non-zero line-height. A raised inline box with its own line-height
**grows the line it sits on**, so the text around it is pushed apart.

**Why neither review method finds it:** there is no rule to read. The markup is correct and the
defect is the *absence* of a declaration, so source review sees nothing wrong; and nothing overlaps,
clips or overflows, so the geometry checker stays silent. Only measuring line pitch, or looking
closely at the render, shows it.

**Rule:** any page using `<sup>` or `<sub>` declares them explicitly —
`sup,sub{font-size:.72em;line-height:0;vertical-align:baseline;position:relative}` with
`top:-.5em` / `top:.25em`. `line-height:0` is the load-bearing part: it stops the raised box
contributing to the line box at all.

**Verifying a fix:** collect the line rectangles across the paragraph with `Range.getClientRects()`
and require every gap to equal the line-height. Filter out sub-pixel rect boundaries first — a naive
version of this check reports 1-2 px "pitches" that are rect edges rather than lines, and those
false positives will hide the real 4 px one.

### F24 amendment — `width:max-content` fixes a numeric table and breaks a prose one

**Saw:** two four-column tables of prose hid **2,082 px and 1,950 px** of themselves at 1440 px, on a
page with room to spare. The rightmost column of each — the one carrying the argument — was absent at
every viewport width, silently, behind an overlay scrollbar.

**Cause:** `table{width:max-content;min-width:100%}`, copied verbatim from a page whose tables were
four columns of single digits. There it is correct: let the table size to its content and scroll
rather than squeeze numbers. On columns of prose, `max-content` means *as wide as the longest
sentence*, so the table grows to two or three thousand pixels and the scroll container dutifully
hides most of it.

**Why it is worth its own entry:** the two cases look identical in the stylesheet, and the fix for
one is the defect in the other. A rule carried between pages without re-asking what its columns
contain is how a fix becomes a bug.

**Rule:** numeric tables may use `width:max-content`; tables containing a prose column use
`width:100%` with a `min-width` around the point where the columns stop being readable (560 px works
for four columns). Verify by measuring `scrollWidth - clientWidth` on the scroll container at the
widest viewport — it must be **0**. The layout checker exempts scroll containers by design, so it
reports clean either way and cannot catch this.

### F11 amendment — page chrome must not borrow the data palette

**Saw:** a page whose legend read "colour carries one meaning only: purple is the body-only slice,
blue the world-only slice, green everything" drew the word **FINISHED** in that green — including
inside a blue *world-only* cell. The same three tokens were also styling tier badges, a callout
accent and the header eyebrow.

**Cause:** F11 as written is about plotting code, so a page that keeps its *figure* colours honest
can still contradict its own legend through chrome. The tokens were reused because they were the
nice colours already on the page.

**Rule:** a token that encodes a data category is a data colour. Nothing that is not a member of that
category may use it — not a status badge, not a tier label, not an accent border, not the eyebrow.
Give chrome its own tokens. Check by grepping every `var(--<data-token>)` outside the figure that
defines it; on a correct page the only hits are the encoded elements themselves.

### F1 amendment — the same defect wearing `display:flex`

**Saw:** eighteen `<summary>` elements, each holding a marker, a bold term, a **bare text run**
(`, and why it is not called pain`) and a muted span. At desktop every comma sat 10 px away from its
word. At 390 px the runs wrapped into *side-by-side columns* — one summary rendered as
`Neuromodulator | (the / "NMN") | — a small / network that / re-tunes the / big one`, and a two-word
run `, and` became a 25 px column with the comma on one line and "and" on the next.

**Cause:** `summary{display:flex; gap:10px}`. A bare text run inside a flex container becomes an
**anonymous flex item**, so it can no longer wrap as part of the surrounding sentence — it shrinks to
its own min-content and wraps independently. The `gap` then applies *between words*, which is what
tears the comma off.

**Why it recurs:** this is F1 — the founding entry, first seen as `display:grid` on a list item — and
it will keep coming back, because flex and grid are the natural way to place a marker beside a label.
The display value changes; the defect does not.

**Rule:** never make a text-bearing element a flex or grid container. Position the marker instead:
`position:relative` on the row, `position:absolute; left:0` on the `::before`, and padding to clear
it. Then term, bare text and span flow as one inline run.

**Verifying a fix:** collect the summary's rectangles with `Range.getClientRects()`, group them by
`top`, and require the gap between consecutive rects **on the same line** to be 0. A non-zero
same-line gap is a torn word.

### F3 amendment — a `margin` shorthand un-centres a component that also carries the layout class

**Saw:** one section sat **175 px** left of every other section at 1440 px, hanging out of the page
column.

**Cause:** `.terms{margin:26px 0}` on an element whose class list is `col terms`. `.col` centres
itself with `margin-left:auto; margin-right:auto`; the shorthand later in the sheet resets all four
sides, so the auto margins became zero. Nothing overlaps and nothing overflows, so the geometry
checker sees a correctly laid-out section that happens to be in the wrong place.

**Rule:** a component rule applied *alongside* a layout class sets `margin-top`/`margin-bottom`
individually, never the shorthand.

**Verifying a fix:** measure `getBoundingClientRect().left` for every top-level column child; they
must all be identical.

### F3, second amendment — two rules that TIE on specificity, where the later one silently wins

The original F3 is a rule that *beats* another on specificity. This is the flatter case, and it is
harder to see: two rules with **equal** specificity, where source order decides and the loser reads
as live code.

**Saw:** a table given its own wider floor, `table.repl{min-width:660px}`, rendering at 560 —
because `table.results{min-width:560px}` appears later in the sheet and both selectors score
(0,1,1). The consequence was not visual: the table simply had a smaller floor than intended, its
real overflow point moved, and the scroll cue derived from the intended 660 then announced a scroll
across a 76px band where nothing scrolled. A dead declaration produced a wrong cue two rules away.

**Why neither review method catches it:** the stylesheet reads correctly — both rules are present,
both are well-formed, and the intent is obvious. Nothing overlaps, clips or overflows, so the
geometry checker is silent, and the rendered table looks entirely normal at its unintended floor.
The defect is only visible by comparing the declared value against the computed one.

**Rule:** a per-instance floor must **out-score** the shared rule it is meant to override, not merely
follow it: write `table.results.repl`, not `table.repl`. And never trust a `min-width` you have only
read — confirm it with `getComputedStyle(el).minWidth` on the rendered page, then derive any
breakpoint from that number.

**A scoping trap the fix itself creates.** The clean repair for a tie like this is often to move the
rule onto a *wrapper* — breaking out `figure.code` rather than the `<pre>` inside it, say. That works,
and it silently excludes every element of the same tag that lacks the wrapper. On the page where this
was done, eleven code blocks broke out correctly and the twelfth — the one `<pre>` written directly
into a section — kept clipping its longest line at every desktop width. **After moving a rule to a
wrapper, grep the page for the same tag outside that wrapper**; the block that still misbehaves is
the one nobody wrapped. Better still, emit the wrapper from the builder so a new block cannot arrive
without it.

**Verifying a fix:** for every element carrying a floor, print the declared value beside
`getComputedStyle(el).minWidth`. Any disagreement is a rule that lost a tie you did not know it was
in.

### F27 — a diagram's legibility floor can push all of its data off a phone

**Saw:** a schematic with a 950 px minimum width inside a scrolling box. At 390 px the reader saw the
row labels, one control box, and none of the grid the diagram exists to show — with overlay
scrollbars, no indication anything was missing.

**Cause:** the floor keeps labels readable (correct, see F25) but says nothing about *what is in the
first screenful*. Here the data columns started a quarter of the way across the viewBox, so the
visible strip was entirely label gutter.

**Rule:** at the floor, `firstDataX × floor ÷ viewBoxWidth` must land inside the narrowest column
width supported, or the phone view opens on nothing. Fix by tightening the label gutter in the
viewBox; where the diagram genuinely cannot fit, **say so** — a one-line scroll cue shown under a
media query, because an overlay scrollbar is not a cue.

### F28 — a class that matches no rule renders as a bare block, silently

**Saw:** a `<div class="note">` intended as a bordered callout rendered with no border, no
background and no padding, beside seven correctly boxed callouts on the same page. Its mono
uppercase heading, designed to sit inside a box, read as an orphan sub-label under the preceding
paragraph.

**Cause:** the component is defined as a **compound selector**, `.callout.note`, and the markup
carried only the modifier. `class="note"` matches nothing, so the element inherits bare-`div`
styling. CSS has no error for this: an unmatched selector is indistinguishable from a deliberate
absence of styling.

**Why neither review method catches it:** the markup looks right — `class="note"` is exactly what a
reader expects for a note — and the stylesheet is right too; the defect lives in the mismatch
between them. Nothing overflows, overlaps or clips, so the geometry checker is silent, and the block
is still perfectly readable, so a screenshot scan can pass over it.

**Rule:** a modifier class never travels alone. Write `class="callout note"`, or define the modifier
as a standalone rule.

**Verifying a fix:** append a bare `<div>`, read its computed style, then walk every `[class]`
element and flag any whose border, padding and background are all identical to it. One pass, and it
catches every instance on the page rather than the one somebody noticed.

### F29 — a table whose header row has fewer cells than its body rows

**Saw:** a sixteen-row results table rendered with three column headers over seven columns of
numbers. Every cell after the third sat under no header at all, and the reader had no way to know
which quantity a column held. The page still looked orderly: the rows were aligned, the numbers were
right, and nothing overflowed.

**Cause:** the table was rebuilt by a script that located it with a regex on
`<table class="results">`, and the page had three tables with that class. The regex matched the
**first** in document order, so a newly written three-column header was written over the sixteen-row
seven-column table while the intended target kept its stale numbers. Two defects for the price of
one, and neither is visible unless you count.

**Why neither review method catches it:** the HTML reads correctly in isolation — a `<thead>` with
three `<th>` is valid markup, and a `<tbody>` row with seven `<td>` is valid markup. The browser
does not complain; it renders the extra columns headerless. Nothing overlaps, nothing clips, and a
screenshot scan reads the block as "a table", because the eye checks alignment, not arity.

**Rule:** any script that rewrites a table must address it by **position or a unique id**, never by
a class that repeats. And after any table edit, assert that every `<tbody>` row has exactly as many
cells as the `<thead>` has headers, for every table on the page.

**Verifying a fix:** parse the page and, per table, print `len(thead th)` against the set of
`len(tr td)` across body rows. A set with more than one member, or a member that differs from the
header count, is the defect. This is three lines and catches every table at once; counting by eye on
the rendered page does not scale past about five columns.

### F30 — a transparent raster figure carries one theme's ink onto both grounds

**Saw:** in dark mode, two plots with no visible title, no axis labels, no ticks, no spines and no
reference line — a nearly empty rectangle with two bright white legend boxes floating in it. The
same two files look perfect in light mode, in a file browser, and in every screenshot taken so far.

**Cause:** the figures were written with `savefig(transparent=True)` and `figure.facecolor: none`,
which was done deliberately so they would sit on the page's paper colour rather than a white card.
But transparency does not make a figure theme-aware — it makes it inherit whatever ground the
reader has, while its ink stays the single colour it was drawn in. Near-black ink on a `#141416`
ground is invisible. The legends survived only because a legend frame has its own opaque fill,
which is what makes the failure look bizarre rather than blank.

**Why neither review method catches it:** the PNG is correct in isolation and the CSS is correct in
isolation; the defect exists only in the composite. The layout checker substitutes placeholders for
images and renders light by default, so it reports nothing. A screenshot review that looks at the
light render — the natural one to take — sees a good figure.

**Rule:** a raster figure either carries an **opaque** background, or ships one variant per theme
switched by `[data-theme]` plus the guarded media query. Transparency is only safe when every mark
in the image is drawn in a colour legible on both grounds, which for a plot with axes and text it
never is. This project's convention is the opaque form: `_plot.finish()` has always passed
`facecolor="white"`, and a new figure script that departs from it is the defect.

**Verifying a fix:** read the PNG's corner pixel and assert alpha is 255; then composite the image
over both `--paper` values and look at each.

### F31 — a scroll cue keyed to the viewport, for an overflow keyed to the column

**Saw:** at 1440px — a desktop, with room to spare — a prose table's last column cut off mid-word
("not a location, so a freezi"), with an overlay scrollbar as the only indication that anything was
missing. At 500px the same table showed a correct scroll cue.

**Cause:** the cue was written as `.tbl-hint{display:none}` plus
`@media (max-width:820px){.tbl-hint{display:block}}` — the right form for a table that overflows
only on a narrow *viewport*. But the table had since been given a content floor (`min-width:860px`)
larger than the 730px reading column it sits in, so it overflows its scroll box at **every**
viewport width. The condition that hides the cue and the condition that creates the overflow are
different conditions, and they had drifted apart.

**Why neither review method catches it:** the `.scroll` container absorbs the overflow, so nothing
spills onto the page and a geometry checker sees a clean box. A reviewer checking the phone width —
the width where scroll cues are usually wrong — finds the cue present and correct.

**Rule:** compare the scroll box's content floor against the width of the **column** it lives in,
not the viewport. If the floor is larger, the cue is unconditional (`display:block`); the
media-query form is correct only when the box is as wide as the viewport.

**Verifying a fix:** for each `.scroll`, read `scrollWidth` and `clientWidth` at the widest
supported viewport. Any box where `scrollWidth > clientWidth` there must have a cue that is visible
at that width.

### F32 — one scroll cue serving two components with different content floors

**Saw:** the cue "the plot is wider than a phone screen — scroll it sideways" printed above seven
figures that fitted their column perfectly, at every tablet width from about 670px to 1010px. Below
670 it was correct; above 1010 it was correctly absent. The false band was the middle.

**Cause:** the page had one `.dia-hint` class and one breakpoint, `@media (max-width:1010px)`. That
breakpoint was derived correctly — for the SVG diagram, whose legibility floor is 950px. When raster
figures were later given the same scroll-with-a-cue treatment, they reused the class, and their
floor is 620px. One breakpoint cannot be right for two floors, so it was wrong for whichever
component did not own it.

**Why neither review method catches it:** the phone width is the one everybody checks, and there the
cue is present and true; the desktop width is the second, and there it is correctly absent. The
defect lives only in the band between the two floors, which is exactly the range a two-width review
skips. Nothing overflows, nothing clips — the page is merely lying to the reader about a scrollbar.

**Rule:** one cue per floor, and the breakpoint is `floor + the column's side padding`, written in a
comment beside the rule so the derivation can be checked rather than trusted. This is the mirror of
[F31](#f31--a-scroll-cue-keyed-to-the-viewport-for-an-overflow-keyed-to-the-column): there the cue
was absent where overflow existed, here it is present where none does. Both come from a cue whose
condition and an overflow whose condition were allowed to drift apart.

**Verifying a fix:** for each scroll box, at three widths spanning the floors, assert
`cueVisible == (scrollWidth > clientWidth)`.

**F32, amendment — N blocks styled by one class are N floors, not one.** The original entry reads as
though the defect needs two *kinds* of component (a diagram and a raster figure) to appear. It does
not. Twelve code blocks sharing one `.code-hint` class have twelve different content floors, because
each one's floor is set by its own longest line; a single breakpoint derived from the widest is
false for the other eleven across the whole band between their floors. That band was 456–779px here,
which the standard 390 / 500 / 834 / 1440 review widths straddle without landing in — 500 sits below
it and 834 above, so a four-width check reports clean while eleven of twelve blocks announce a
scrollbar they do not have.

The general fix is not a better breakpoint. A breakpoint is a *proxy* for overflow, and every proxy
eventually disagrees with the thing it stands for. Ask the box: bind the cue to the measurement
itself, per block, on load and on resize —

```
document.querySelectorAll('figure.code').forEach(f => {
  const pre = f.querySelector('pre'), hint = f.querySelector('.code-hint');
  if (pre && hint) hint.hidden = !(pre.scrollWidth > pre.clientWidth);
});
```

— keeping the media query underneath as the no-JS fallback. Two things this needs to be correct.
The page must declare its own `[hidden]{display:none!important}`, because `.code-hint{display:block}`
inside a media query otherwise beats the `hidden` attribute and the script's work is invisible
(that is [F14](#f14--the-hidden-attribute-loses-to-a-display-rule) arriving from a new direction).
And the listener must include `resize`, or the cue is correct only at the width the page loaded at.

The measurement-bound version is also right in a way no breakpoint can be: the floor of a code block
depends on the monospace face the *reader's* browser resolves, which is not the one the page was
measured in. A breakpoint derived on this machine encodes this machine's font metrics.

### F32 amendment — a derivation comment that does not sum to the breakpoint it justifies

**Saw:** three tables clipping their right-hand column across a 2px band (602–603px) with no scroll
cue, on a page whose CSS carried a comment explaining exactly why the cue sat where it did.

**Cause:** the comment read *"scroll box is W-82 (20 wrap + 20 card padding + 1 border, each side)"*
and then used `520+84 = 604` two lines later. The arithmetic in the prose and the arithmetic in the
rule disagreed by 2px, and the rule was the one that was right: the `.scroll` element has its own
1px border, and `clientWidth` excludes it, so the box is `W-84`. The author had measured correctly
and then written down a term short.

**Why neither review method catches it:** the comment *looks* like a derivation, so a reader
checking the breakpoint reads it and moves on — that is the entire purpose F32 gives it. A geometry
checker never reads comments at all. The defect is that the justification and the thing it justifies
were never actually reconciled, and nothing in either review method reconciles them.

**Rule:** [F32](#f32) requires the derivation to sit beside the breakpoint "so it can be checked
rather than trusted". Extend that: the derivation must **sum to the number in the rule**. A comment
whose terms do not add up to the constant beneath it is worse than no comment, because it converts
a checkable claim into a trusted one. Include every border in the sum — the container's *and* the
scroll box's own — and state the measured `clientWidth` at the boundary width so the claim is
falsifiable against a render rather than against the author's addition.

**Verifying a fix:** probe `clientWidth` at the boundary and assert it equals the declared floor
exactly; then sweep widths asserting `cueVisible == (scrollWidth > clientWidth)`. A 2px band is
invisible at the usual 500/560/610/834/1440 checkpoints — it needs the boundary itself, and the
width either side of it, in the sweep.

### F11, second amendment — a figure that borrows the page's *status* palette

The original F11 and its first amendment forbid the page's chrome from using the data colours. This
is the same defect running the other way: a figure script choosing a categorical colour with no
knowledge of what the surrounding page has already spent.

**Saw:** a stacked-bar figure drew "starved" in `#8a6d1f` — byte-identical to the page's
`--pending` token, the ochre that borders every "still open" callout — and "survived" in a green a
short hop from `--both`, the colour that means "the modulator reads everything" in the figure 1,300
pixels above. A reader who has just learned that green means *everything* meets green bars on the
same rows meaning *survived*.

**Why the caption is not the fix:** the caption said, in as many words, "these colours mean an
outcome and nothing else — they are not the purple/blue/green that mean what the modulator reads."
A sentence telling the reader to ignore what they can see is an admission that the figure and the
page disagree, not a repair.

**Rule:** the figure module owns one colour→meaning map for the whole page, chrome tokens included,
and a new categorical set is checked against every token in `:root` before it ships — by perceptual
distance, not equality, since a near neighbour reads the same as an exact match. Where every hue is
already spent, the honest answer is a neutral ramp: it carries the ordering without claiming a
meaning the page has given away.

**Verifying a fix:** take a pixel census of the rendered PNG, take the token list from `:root`, and
report the closest token to each figure colour. The output is not pass/fail — an exact match is
*correct* when the figure element means what the token means, and this project's data figures should
hit `--intero` / `--extero` / `--both` dead on. The check earns its keep by forcing the author to
name, colour by colour, why each near match is intended; the one that cannot be named is the defect.
Running it on the fixed figure above returns only its own data colours and its text ink, and nothing
within reach of `--pending`.

### F33 — the legibility fix for an in-panel annotation deletes the data it was illegible against

**Saw:** in a panel whose entire claim is "these sixteen lines are flat", one of the sixteen ran
into a tidy label box two thirds of the way across and never came out. The label was perfectly
readable. So was every other line. Nothing looked wrong.

**Cause:** the annotation had previously been reported as hard to read, because three thin series
ran through its glyphs. The fix applied was an opaque `bbox` behind the text. But text-on-data and
box-on-data are the same collision over the same pixels: an opaque ground does not resolve it, it
only decides which of the two the reader loses. The first version lost the text; the second lost the
data, which is strictly worse, and is invisible because a missing line looks like a line that was
never plotted.

**Why neither review method catches it:** the geometry checker sees one PNG and no overflow. A
screenshot scan sees a clean, legible label — the defect is the *absence* of something, and absence
does not attract the eye. Finding it means tracing one specific line from one end of the panel to
the other and noticing it stops.

**Rule:** an annotation goes where there is no ink. Enlarge the axis margin until empty space
exists, or move the text into it. A filled `bbox` is permitted only over axes that are genuinely
empty there. Where the text must sit over data, use a halo
(`path_effects.withStroke(linewidth=…, foreground=<paper>)`) instead: the glyphs stay legible and
the line runs through the gaps between them, so neither is deleted.

**Verifying a fix:** for each annotation take its bounding box in data coordinates and assert that
no plotted series has a y-value inside it across the box's x-range. Failing that, crop the region at
full resolution and follow each line through it.

**Related:** this is the third defect in the family where a *fix* introduced the next one — the
opaque figure background of [F30](#f30) was the fix that made [F25](#f25)'s narrowing necessary, and
the narrowing then sheared an axis label off the canvas. A figure script that is edited to satisfy a
review finding should be re-rendered and re-read as a whole, not diffed.

### F34 — a `min-width` floor sized for the widest table, applied by a type selector

**Saw:** at a 390px phone width, a sixteen-row numeric table rendering its row-label column and
**neither of its two numbers** — a list of sixteen names with no data. At 500px the same table was
worse than useless: the clip edge fell exactly on the decimal point, so 28.62, 26.67 and 24.03 read
as "28", "26" and "24" — plausible integers, wrong values, with nothing to suggest anything was
missing.

**Cause:** `table{min-width:560px}` — a bare type selector. The 560 was derived honestly, for the
page's seven-column results table. Every other table on the page then inherited it, including a
three-column one whose own content needs about 350px and which would have fitted a phone with room
to spare. The floor did not describe that table's content; it described a different table's.

**Why neither review method catches it:** the floor is inside a `.scroll` container, so nothing
overflows the page and the geometry checker is silent. The table is not squeezed — it is at its
floor, which is the state the floor exists to produce. And a review at the common 500px checkpoint
sees numbers, because the clip lands mid-value rather than before it; only reading them against the
source shows they are truncations rather than values.

**Rule:** a `min-width` floor is a statement about one table's content, so it belongs on a class,
never on `table{}`. Every table gets the floor its own columns need, or none.

**A second trap in the same family:** a `.scroll` box inside a padded component is narrower than one
in a bare section — on this page, 52px narrower inside a `.callout`. A cue breakpoint derived as
`floor + column padding` is therefore wrong by exactly that much for the boxes inside callouts, and
the table's verdict column was cut with no cue across a 50px band. Derive each breakpoint from the
box's own measured `clientWidth`, not from the column's.

**Verifying a fix:** for every table, assert its declared floor is no greater than its `max-content`
width plus whatever headroom was intended; and for every `.scroll`, assert `cueVisible ==
(scrollWidth > clientWidth)` at a sweep of widths rather than at two checkpoints.

### F34 amendment — a scroll cue that counts hidden columns, defeated by the mid-value clip

**Saw:** a cue reading *"2 columns hidden — scroll sideways"* under a table where the clip edge fell
inside a value, so the reader saw `0.207 ± 0.11` where the data said `0.207 ± 0.111`. Three columns
were visible and the third was wrong; the cue's count was right and its implication was not.

**Cause:** the cue described the *layout* (how many columns did not fit) when the reader's problem
is the *data* (a number on screen is a truncation). F34's own mid-value trap and the cue wording
were written at different times and never reconciled: the register knew the clip lands mid-value,
and the cue still promised that everything shown was intact.

**Why neither review method catches it:** the cue is present, styled, and numerically accurate, so
it passes a static read; the geometry checker only asks whether a cue exists when a box overflows,
which it does. Only reading a rendered value against the source shows the miscount.

**Rule:** a scroll cue warns that **the visible values may be cut**, never how many columns are
missing. Wording that survives every clip position: *"Wider than the screen — scroll sideways; the
right-hand column is cut off."* A count is also a maintenance liability — it is a hand-typed
constant that silently goes stale the next time a column is added.

### F35 — a shared `min-width` floor SMALLER than a table's content, where a value takes the hit

The mirror of [F34](#f34). There an inherited floor was too large and pushed columns off a phone.
Here it is 14 pixels too small, and the failure is stranger: the table does not overflow at all.

**Saw:** across a 126px band of viewport widths, one row of a numeric table rendered as

```
bush hiding (% of steps)     14.45 ±      13.84 ± 0.53
                              0.57
```

and two column headers broke at their hyphens. On a 390px phone the clip fell after `14.` and the
wrapped `0.57` was off-screen, so the row showed a number over an empty line.

**Cause:** the table inherited `table.results{min-width:560px}`, sized for a different table. Its own
max-content width is 574px. A table asked to fit inside less than its content does not necessarily
overflow — it looks for something to break, and a numeric cell like `14.45 ± 0.57` contains a
breakable space. So the table met the floor by splitting a *value* across two lines.

**Why every check passes:** nothing overflows, so the scroll cue is correct at every width — and the
`cueVisible == (scrollWidth > clientWidth)` sweep that catches F31 and F32 confirms it. No text is
narrow, nothing overlaps, nothing sticks out, and the table is fully legible at desktop and at the
floor. The defect exists only between the two, and it is one deformed row.

**Second instance (2026-09-09):** a mapping table whose cells carry `td.mono{white-space:nowrap}` measured a 684px content floor against a declared 520 inherited from a shared `table{}` rule, and its cue was derived from the declared number. Note the extra hazard there: the measured floor depends on which monospace fallback the machine loads, so the fix is to **declare** a floor for that table rather than to hard-code the number that was measured once.

**Rule:** a numeric table's floor is *its own* measured max-content width, never a number borrowed
from a wider table — and `td.num` carries `white-space:nowrap`, so no future floor can split a value
whatever else it does.

**Verifying a fix:** render each table at its declared floor and assert every body cell is one line
tall (`height − padding ≤ line-height`). F34's check — floor ≤ max-content — tests the other
direction and cannot see this one; both are needed, and together they say the floor must equal the
content, not merely bound it from one side.

### F35 amendment — `white-space:nowrap` on a shared selector is a min-content change everywhere it reaches

F35's fix was `td.num{white-space:nowrap}`, so a value could never again be split across lines. It
was applied as `td.num, th.num` — belt and braces, and one word too many.

**Saw:** a *different* table, six columns wide and previously fitting its 660px floor exactly, began
overflowing its box with no cue, cutting its verdict column mid-word at tablet widths and losing its
last column's padding at every desktop width up to 1440.

**Cause:** that table met its floor only because its four header cells — "original grid", "sites
agreeing", "twin grid", "sites agreeing" — were free to wrap to two lines. `th.num{nowrap}` took
that away, raising its min-content from 660 to 687 against a box that is at most 678 wide. The floor
was never the problem; the slack was in the headers, and the fix removed the slack.

**Why it is worth its own entry:** the review that requested the belt-and-braces, the author who
applied it, and the check that verified F35 were all looking at the table F35 was about. A rule
written on a shared selector is not a property of the table you are fixing; it is a property of
every table the selector reaches, and `nowrap` in particular changes a box's *minimum* size, which
is the quantity every floor and every cue breakpoint is derived from.

**Rule:** `nowrap` goes on `td.num` only — headers may wrap, values may not. More generally: after
editing any selector shared across components, re-run the floor-versus-content check on **all** of
them, not on the one being fixed.

**Verifying:** for every table, print declared floor, `max-content` and `min-content` side by side
both before and after the edit. A min-content that moved on a table you did not touch is the defect.

### F36 — a bin vocabulary carried from one figure script into another whose edges differ

**Saw:** an axis labelled "randomised starting injury (0-100 scale), in quarters" printed directly
above tick labels reading `0-25 | 25-50 | 50-100`. Three bins, and the last one is a half. Four
captions, two "What it shows" blocks and two table captions on the same page repeated the word,
speaking of the "highest quarter" of a scale that had no fourth quarter. A later section of the same
page used a different script whose bins really are quartiles, so one word meant two things and the
reader had no way to know which.

**Cause:** the phrase was written for the sensory study's script, where `INJ_EDGES` are the three
quartile boundaries, and reused when a second script binned the same variable on
`[0+, 25, 50]` — which after dropping an empty zero bin leaves three unequal bands. The label
travelled with the copied code; the edges did not.

**Why neither review method catches it:** the caption is right for the figure its author had in
mind, the PNG is right for its own data, and the two are read separately — the caption when checking
prose, the image when checking layout. Nothing overflows, nothing is illegible, and every number in
the figure is correct. Only holding the sentence against the tick labels shows the disagreement.

**Rule:** whenever a caption or an axis label names a binning — quarters, quartiles, deciles, halves
— count the tick labels on the rendered figure and check the span of the last one against the word.
Better, derive the label from the edge array rather than writing it: a label that says "three bands"
because the array has three entries cannot drift from the data.

**Verifying a fix:** for each figure, print the bin edges the script used beside every occurrence of
a binning word in its caption and in any prose that cites it.

### F37 — a percentage `max-height` on a grid item resolves against a track the item itself sizes

**Saw:** a figure viewer whose "Fit to window" mode fitted the width only. A 1539×2664 figure opened
at 1404×2430 inside a 756px-tall box: the reader got the top third and a scrollbar, under a button
labelled "Actual size" implying the current state was already the fitted one. Live on two pages, for
weeks.

**Cause:** `.lb-scroll{display:grid; place-items:center}` with an implicit `auto` row, and
`max-height:100%` on the image. A grid item's percentage resolves against its track; an `auto` track
is sized **from the item**. The constraint is circular, so it never binds and the declaration is
inert — while reading as though it obviously works.

**Why nothing caught it:** landscape figures fit by width alone, so the mode looked proven on every
figure anyone happened to open. The layout checker never opens the viewer at all — it is behaviour,
not layout. And the CSS is not wrong in any way a reader can see; `max-height:100%` inside a
full-height box is what you would write.

**Rule:** an image that must fit a box gets **flex** centring, where a percentage resolves against a
definite flex item — `display:flex; align-items:center; justify-content:center` on the box and
`flex:0 0 auto` on the image. (`grid-template-rows:minmax(0,1fr)` also fixes the fit but silently
drops the box's trailing padding in the other mode.)

**Verifying a fix:** open the **tallest** figure on the page and assert
`img.height <= scroll.clientHeight`. A viewer ported from another page inherits that page's
untested cases, so re-run this on the new page rather than trusting the old one.

### F38 — a focus ring offset outward, inside an overflow container, is clipped to nothing

**Saw:** nothing at all — which is the defect. Every figure was made a `tabindex=0` `role="button"`,
and a `:focus-visible` outline was written for it. Focused, `:focus-visible` matched, and a pixel
census of the 7px band around the image found **zero** ring pixels. A keyboard user tabbing the page
lands on a focusable figure with no indication, and after closing the viewer focus returns to that
figure equally invisibly.

**Cause:** `outline-offset:3px` draws the ring *outside* the element's border box, and the element
sits inside `.figscroll{overflow-x:auto}` — which makes `overflow-y` computed `auto` as well, so the
container clips it away.

**Why neither review method catches it:** the rule is present and correct-looking in the stylesheet,
the element really does receive focus, and a screenshot review does not tab through a page. Absence
of a ring looks exactly like a page you did not happen to focus.

**Rule:** anything focusable inside `overflow:auto|hidden|clip` uses a **negative** `outline-offset`
(or the container carries padding to hold the ring).

**Verifying a fix:** focus the element programmatically and count ring-coloured pixels in the band
around it. Reading the rule proves nothing — the rule was already right.

### F39 — markdown syntax printed literally in an HTML page

**Saw:** body prose reading `Blue and orange are chosen *because* they survive` — asterisks and all,
at every viewport, in both themes.

**Cause:** the prose was drafted in a markdown habit inside an HTML file. `*…*`, `**…**` and `_…_`
are inert in HTML; the browser prints the punctuation. Every other emphasis on the same page used
`<em>` correctly, which is what makes the slip survive a read-through: the author sees the intent.

**Why neither review method catches it:** the geometry is perfect — the text is the right size, in
the right box, in the right colour, and nothing overflows — so a layout checker has nothing to say.
And a screenshot review reads prose for sense rather than for punctuation; an asterisk is small,
mid-sentence, and looks like a footnote marker.

**Rule:** before publishing, grep the page body for `\*\w[^*]*\w\*`, `\*\*` and `_\w+_` outside
`<code>` and `<pre>`. It is a one-line check and it is the only thing that reliably finds this.

**Verifying a fix:** the grep returns nothing.

### F40 — an `auto-fit` grid whose container carries the gap colour as a background

**Saw:** the four-cell evidence tally on a parameter-reference page rendered, between about 561 and
720 px, as three cells and **a solid grey slab** occupying the remaining two column tracks. The slab
looked like a rendering failure; it was empty grid area.

**Cause:** `grid-template-columns:repeat(auto-fit,minmax(168px,1fr))` on a container using the
1px-gap-plus-container-background trick to draw hairlines between cells. `auto-fit` chose four
columns in that band while the content supplied three rows' worth of items, and every cell the items
did not occupy showed the container's background — which here is the *line* colour, not the surface.
With a transparent container the same orphan is invisible; with this one it is a filled block.

**Why neither review method catches it:** nothing overflows and nothing overlaps, so a geometry
checker sees a clean box. The defect only exists in the width band where the item count fails to
divide the column count, so a review at 500 and 1440 — the two widths most likely to be checked —
misses it in both directions.

**Rule:** a grid that paints its gaps via the container background gets **explicit column counts per
breakpoint**, never `auto-fit`. If the column count is not chosen by hand, the empty cells are not
either.

**Verifying a fix:** step the viewport across the component's whole range and assert
`cells × cellWidth + gaps == containerWidth` at every step, or simply that the item count is a
multiple of the resolved column count.

### F41 — a sticky offset hard-coded to another sticky element's height, which wraps

**Saw:** a sticky group-navigation rail set to `top:78px` below a sticky toolbar. Between 861 and
~950 px the toolbar's chip row wrapped to a second line, making it 99 px tall, and the rail's first
row — the *active* one — sat underneath it, showing only a sliver of its accent border. Clicking a
rail link also landed the target heading 13 px under the toolbar, because `scroll-margin-top` was
hard-coded from the same stale measurement.

**Cause:** two sticky elements whose offsets were written from one measurement of the first one's
height. That height is not a constant: a flex-wrap toolbar grows a row whenever its contents stop
fitting, so the offset is correct only at the widths where the author happened to look.

**This is not F5.** F5 is `position:sticky` constraining the margin box so an element's *own* padding
pushes it down. This is a *sibling's* height changing with viewport width, which no amount of care
about the second element's own box will catch.

**Why neither review method catches it:** the CSS reads as obviously correct — `top:78px` against a
toolbar that is 68px tall plus 10px of clearance. Both numbers are true at desktop width. A
screenshot scan at 500 (rail hidden) and 1440 (toolbar one row) shows no defect, because the failure
lives in a ~90px band between them.

**Rule:** a second sticky element's `top`, and any `scroll-margin-top` derived from it, is either
measured from the first element at runtime and written to a custom property, or the first element is
**prevented from wrapping at every width where the second is shown**. The cheap fix is usually the
second: hide the dependent element at the same breakpoint where the toolbar gains its row.

**Verifying a fix:** step the viewport across the band, scroll each element into its stuck state, and
assert `railTop >= toolbarBottom` at every step. Sample widths on either side of the band will pass a
broken page.

### Tool note — a DOM probe that runs at `DOMContentLoaded` measures fallback-font layout

**Saw:** a review harness probing the same page twice returned twelve badges wrapped onto their own
row, then seven; element offsets differed from the screenshots by 50–250 px. Neither pass was buggy.

**Cause:** the probe fired at `DOMContentLoaded`, before the Google Fonts faces arrived, so it
measured Georgia and system-ui metrics — different advance widths, different wrap points, different
heights, and a different `ch` for every `max-width` expressed in it. The screenshot, taken under
`--virtual-time-budget`, waits for the real faces. So the numbers describe a page nobody sees while
the image beside them describes the real one.

**This is a property of `scripts/claude/check_artifact_layout.py` itself** — its probe is attached at
`DOMContentLoaded` (line ~136) deliberately, because under `--virtual-time-budget` a `load`-plus-
`setTimeout` path never runs (the reason is in the comment at line 133). The trade-off is sound; its
consequence for the reported geometry is what was never written down.

**Rule:** any renderer probe awaits `document.fonts.ready` before measuring, and records
`[...document.fonts].filter(f => f.status === 'loaded').map(f => f.family)` alongside its numbers. A
pass that reports zero loaded families is a fallback-font pass and must say so in its output rather
than presenting the geometry as the page's.

**Verifying a fix:** run the probe twice on a page with a web font and a wrap-sensitive component;
the two passes agree only once the wait is in place.

### F42 — hand-placed labels in an inline SVG collide, and the checker cannot see SVG text

**Saw:** in a hand-authored diagram, `not a ste` with `excluded from every rate` stamped through
the final letter — two labels printed over each other at every viewport, in both themes.

**Cause:** both `<text>` nodes have sensible coordinates read on their own: one starts at x=20, the
other is centred at x=150, and their baselines are six units apart. The collision only exists once
glyph widths are applied — the first runs to x≈86 and the second starts at x≈74.

**Why neither review method catches it:** the layout checker's overlap test walks **HTML** text
boxes; SVG `<text>` is invisible to it, so the tool reports a clean page. And reading the source
shows two coordinates that look fine, because the width of a string is not in the source.

**Rule:** any hand-placed SVG label is checked by rendering, not by reading. The checker should walk
SVG `<text>` nodes and assert pairwise `getBBox()` disjointness; until it does, an author verifies
the same in the console before shipping a hand-authored diagram.

**Related:** [F18](#f18) is the raster cousin — a matplotlib label wider than the panel it sits in.
The difference is where the fix lives: F18 belongs in the figure script, F42 belongs in the checker,
because a hand-drawn SVG has no script to guard it.

### F40 amendment — a wrapping `auto-fit` grid whose cells carry a one-sided border

**Saw:** a three-panel timeline built with `repeat(auto-fit,minmax(220px,1fr))`. Between about
500 and 700&nbsp;px it wrapped to two columns, and the third panel arrived underneath the first
**with no rule above it** and an empty cell beside it showing the container's ground — nearly
invisible in light mode, a darker block in dark.

**Cause:** the cells separate themselves with `border-right` only, which is correct for a
single row: N cells give N&minus;1 internal verticals and `:last-child` clears the trailing one.
The moment `auto-fit` adds a row there is a horizontal join that no cell draws, and a trailing
empty track that no cell fills. `auto-fit` decides the column count from the container width, so
the author never chose the wrapped state and never saw it.

**Why neither review method catches it:** nothing overflows, overlaps or clips, so the geometry
checker is silent; and the CSS is right for the layout the author had in mind. The defect only
exists in a column count the stylesheet never names.

**Rule:** a grid whose cells draw a border on **one** side only must have an explicit column
count per breakpoint, not `auto-fit`. Where the count changes, swap the border side with it
(`border-right` in a row, `border-bottom` when stacked). If `auto-fit` is genuinely wanted, put
the separators on the container (`gap` + a background) rather than on the cells.

**Verifying a fix:** render at the breakpoints either side of every wrap and count the visible
rules; a wrapped grid with R rows and C columns needs R&minus;1 horizontal and C&minus;1 vertical.

### F43 — a token sized for a border, reused as text, fails contrast while looking on-palette

**Saw:** a two-column ledger whose right-hand heading — 11&nbsp;px, uppercase, letter-spaced —
measured **2.3:1** against the light ground. Its left-hand twin was fine. Both headings took
their colour from the same family of tokens, and the page looked coherent.

**Cause:** the token was authored as `--warn-line`, for a 3&nbsp;px `border-left` on a callout,
where a mid-chroma amber reads perfectly. Reused as `color:` on small uppercase text it fails,
because a border only has to be *seen* while text has to be *read*: the contrast a 3&nbsp;px
band needs and the contrast an 11&nbsp;px glyph needs are different requirements against the
same background.

**Why neither review method catches it:** the colour is "correct" — it is the page's own warn
hue, used on the element that means warning, so both a stylesheet read and a screenshot scan
report a consistent palette. Nothing is clipped, overlapped or mis-coloured; it is simply too
light to read, and only a measurement says so.

**Rule:** type the tokens. A `*-line` / `*-border` token is for borders and rules; a `*-text`
token is for text, and is a darker step of the same hue. Never set `color:` from a `-line`
token. Add the text variants in the same commit as the border ones, in every theme.

**Verifying a fix:** walk every element whose computed `color` came from a token, compute the
contrast ratio against its own computed background, and flag anything under 4.5:1 (3:1 for text
at or above 18.66&nbsp;px bold / 24&nbsp;px regular). Run it in **both** themes — this one
passed in dark and failed in light.

### Tool note — a review is not tied to the build it reviewed

**Saw:** a page was rebuilt while a format review was in flight. The first screenshots described
the previous build, and only a mid-review re-render caught it. The differences were text-only
that time, so no finding was wrong; that was luck.

**Rule:** `check_artifact_layout.py` should print the reviewed file's **mtime and a short content
hash** in its report, and a review should quote them. A finding that cannot be tied to a build is
a finding the author cannot reproduce — and the natural author response, "I already fixed that",
is unfalsifiable without it.

### F44 — a caption naming a rendered property of a CSS-drawn picture, where that property flips with theme

**Saw:** a schematic drawn from CSS boxes — a grid of cells tinted by `opacity` on `var(--accent)` to
show a quantity — under a caption reading *"darker is a larger gain"*. True in light theme. In dark
theme `--accent` is a light lilac on a near-black card, so the largest value renders **brightest**,
and every reader on a dark screen read the picture inverted.

**Cause:** the caption described the *rendering* rather than the *encoding*. "Darker" is a fact about
one theme's output; "larger" is a fact about the data. Bind a caption to the first and it inverts the
moment the other theme paints it.

**Why neither review method catches it:** the caption is accurate in the theme most authors compose
and screenshot in, and the CSS is plainly correct — one token, one opacity ramp, nothing conditional.
Nothing in the source says which end of the ramp is dark, because that depends on a token defined a
hundred lines away and redefined again under a media query. Only rendering the page in the *other*
theme shows it.

**Rule:** never describe a theme-dependent rendered property (darker, lighter, brighter, paler) in a
caption. Either name the encoding theme-neutrally ("the more strongly tinted, the larger the value")
or, better, **emit a swatch legend** so the reader calibrates against swatches that live in the same
theme as the picture. A legend is also the only version that survives a later palette change.

**Verifying a fix:** render the page in both themes and read the caption against the picture in each.
If the sentence is still true in both, it was not theme-dependent.

**Related:** [F11](#f11) — same root cause seen from the other side: a colour carrying a meaning the
page has not pinned down. F11 is about one token meaning two things; this is about one token meaning
two *opposite* things in the two themes.

### F45 — a case-changing `text-transform` applied over case-sensitive identifiers

**Saw:** a table header rendering `LARGEST |(B − G) − 1| ACROSS THE 128 UNITS` — capital *B* and *G* —
sitting directly beneath a callout that spends a paragraph explaining what the lowercase *b* and *g*
are and warning they must not be confused with γ and β.

**Cause:** a blanket `th{text-transform:uppercase}`, which is a perfectly reasonable typographic
choice for prose headers, reaching an `<em>` holding a mathematical symbol. In maths, source code and
gene names, case *is* the identity — `b` and `B` are different objects — so a presentational transform
silently renamed the thing the page was about.

**Why neither review method catches it:** the HTML is right (`<em>b</em>` is exactly what the author
typed), so reading the source shows the correct symbol. The CSS is right in isolation. The defect
exists only in the composed output, and a screenshot scan reads `B` as a plausible symbol rather than
as a corrupted `b` unless the reviewer knows which one the page meant.

**Rule:** any `text-transform` that changes case must exclude the elements that carry identifiers —
`th em, th code, th .sym {text-transform:none}` — or not be applied to that header at all. The same
applies to `font-variant:small-caps`, which flattens case visually while leaving it in the DOM.

**Verifying a fix:** assert `getComputedStyle(el).textTransform === 'none'` on every element inside a
transformed header that carries a symbol, and read the rendered header back against the source string.

## Related

- [`artifact_generation_guide`](artifact_generation_guide.md) — the wider guide: content, claims,
  jargon, figure legibility. This document is the *format* half and is narrower on purpose.
- `scripts/claude/check_artifact_layout.py` — the tool.
- [`artifact-format-reviewer`](../../../../.claude/agents/artifact-format-reviewer.md) — the agent
  that runs it.
