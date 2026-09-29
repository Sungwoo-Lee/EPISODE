---
title: Artifact format bugs — the register, and why reading the CSS never finds them
topic: meta
status: active
created: 2026-08-31
last_updated: 2026-09-16
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
- [ ] No `max-content` grid track over unbreakable keys without a stacking breakpoint (F48)

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

### F31 amendment — the pinned-width pass reports page overflow only, so it cannot see inside a scroll box

**Saw:** a four-column results table dropping its **entire last column** — the percentage that was the
point of three of its four rows — on every phone between 390 and 429 px, with no scroll cue. It had
survived four separate format reviews, mine included.

**Cause, in two parts.** The table had no declared floor, so its width was whatever its content
happened to need (min-content 346 px) against a box of `W − 84` inside a card — overflowing below
434 px. And none of the page's three cue breakpoints was attached to it. Ordinary F31, except for
where it lived: entirely **below Chrome's ~500 px viewport floor**, in the band only the pinned pass
can reach.

**Why the tool did not catch it:** `--pin-width` exists precisely to reach real phone widths, but it
asserts on **page-level** horizontal overflow — `documentElement.scrollWidth > clientWidth`. A table
inside `.scroll` never overflows the page; that is what the scroll box is *for*. So the pinned pass
reports a clean page while a column sits off-screen inside it, and the wide passes cannot reproduce
it because Chrome will not render the width at which it happens. Reading the CSS does not find it
either: nothing is wrong with any single rule, only with the absence of a floor and a cue.

**Rule:** a table gets a **declared** floor on its own class — declare a round number above the
measured min-content, never hard-code the measurement — and a cue breakpoint derived from *its own*
box, not shared with a table in a different container. A table in a bare section has box `W − 42`; in
a card, `W − 84`. Two tables with different floors or different containers must not share a cue, or
the band between them carries a cue for a cut that is not happening (F32).

**Verifying a fix below 500 px:** the media query cannot be observed there — Chrome renders 500
whatever you ask for, so the cue's own breakpoint is untestable by rendering. Verify the *arithmetic*
instead: measure `clientWidth` at two or more widths ≥ 500 to confirm the box formula (`W − 84` here,
checked at 500/560/604 giving 416/476/520), then the overflow threshold follows by subtraction and
the breakpoint is a statement about it. State the measured pairs in the comment so a reader can
re-derive rather than trust.

**Tool fix worth making:** have the pinned pass print every `.scroll` whose `scrollWidth >
clientWidth` at that width, with the overflow amount. One line, and it converts this whole class from
invisible to reported.

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

### F44 amendment — a caption naming an element that a responsive breakpoint hides

The original F44 is a caption bound to a **theme**-dependent rendering. This is the same defect bound
to a **breakpoint**-dependent one.

**Saw:** under a CSS-drawn network figure, the caption "The three arrows mark the sites the modulator
is allowed to reach into." Two problems at once. At wide widths the figure contains eight arrows —
five vertical, three horizontal — so "the three arrows" was already ambiguous. Below the layout's
700px breakpoint the three horizontal arrows are `display:none` (they are meaningless once the
columns collapse and are replaced by a text label), so the sentence referred to nothing on screen at
all.

**Cause:** the caption was written against the wide rendering, which is the one the author composes
in. A responsive figure is not one picture — it is a family of them — and a caption is shared by
every member of the family.

**Why neither review method catches it:** the caption is accurate in the composing width, and the
CSS is correct — hiding a directional arrow when the direction stops existing is the right call. The
defect is only visible by reading the caption against the *narrow* screenshot, which is a step
neither a source read nor a single-width render performs.

**Rule:** a caption may only name pieces of a CSS-drawn figure that exist at **every** width. Prefer
naming the thing that carries the meaning rather than the thing that draws it — "the three γ β
markers" survives a breakpoint that removes the arrows, because the marker is present in both forms.
Where a count appears, check it against the widest rendering too; a figure often gains decorative
strokes there that make a bare count ambiguous.

**Verifying a fix:** read the caption aloud against the narrowest and the widest screenshot in turn.
Every noun it names must be findable in both.

**Related:** [F34 amendment](#f34-amendment) is the same failure in a scroll cue — text describing a
layout state that the layout no longer has.

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

### F46 — `table-layout:fixed` plus `nowrap`: a too-narrow column paints into its neighbour

**Saw:** at phone width, a data-accounting table printed `16,969,747186,754,1439.1%` — three
numbers with no boundary between them, the last one overprinting the tail of the one before. Every
value was correct and present. They simply had no gaps.

**Cause:** the table was `table-layout:fixed` with percentage column widths and `white-space:nowrap`
on the numeric cells. Under fixed layout a column's width is what the rule says, full stop; content
that does not fit neither wraps (`nowrap` forbids it) nor widens the column (fixed layout forbids
it). It overflows the cell box and is painted on top of whatever is next to it. At the table's
`min-width` floor the three numeric columns came out 60/60/44px against content needing ~64px and
~92px, so all three collided at once. The percentages had been chosen against the *headings*, which
are short, rather than against the widest value any row would hold.

**Why neither review method catches it:** nothing overflows the scroll container — the table is
sitting exactly at its declared floor, so `scrollWidth == clientWidth` on the box and the page
reports no horizontal scroll. No cell wraps, so the squeezed-prose-ribbon heuristic finds nothing.
The geometry checker walks elements, and every element is where its CSS says it should be. The
defect exists only in the *painted* result, one level below the box tree, and only at widths where
the table hits its floor — so a desktop-first look never sees it either.

**Rule:** a `nowrap` column may not be given a width that was not derived from its widest content.
Either let the numeric columns size themselves (auto layout, `width:100%`, floor only on the one
column allowed to wrap), or keep fixed layout and set each column from the widest value it will
ever hold with the floor as their sum. Prefer the first: it cannot go stale when the data grows.

**Verifying a fix:** at the narrowest width the table is reachable at, assert
`cell.scrollWidth <= cell.clientWidth` for **every** non-wrapping cell — not one sample — and
separately assert that no cell's left edge sits left of the previous cell's right edge. The second
check is the one that catches painting-into-a-neighbour, because a cell can overflow by a hair
without visibly colliding. Both must run on every such table on the page: N tables built by one
class are N different content widths, the same trap as
[F32's amendment](#f32--one-scroll-cue-serving-two-components-with-different-content-floors).

---

### F47 — a new direct child of a two-column grid silently re-deals every sibling into the wrong track

**Saw:** the whole of *The Sensor Ladder* rendered in the 190px table-of-contents rail at desktop
width. Body paragraphs were 138px wide, headings broke every second word, and the document ran
94,120px tall instead of 42,176px. Below 1300px it was perfect. The page had been published twice
in that state, on 2026-09-07 and 2026-09-11, before a reader opened it on a wide screen.

**Cause:** `.wrap` is `grid-template-columns:190px 1fr` above 1300px and held three children —
`header.mast` pinned by `.mast{grid-column:2}`, then `nav.toc` and `main`, both auto-placed. That
worked only because *two* auto items were left to fall into the remaining cells in exactly the
right order. A later commit added an unrelated `<section>` (a one-paragraph rename notice) as a
direct child of `.wrap`, between the header and the nav. Auto-placement then had three items to
deal instead of two, every one of them shifted a cell, and `main` — the article — landed in the
190px track. The commit that broke it touched no CSS, no layout, and no other page; nothing about
adding a notice paragraph suggests it can move the article into the sidebar.

**Why neither review method catches it:** nothing overflows and nothing overlaps, so the geometry
checker reports the page *clean* on its primary checks — every box is exactly where the cascade
says. Static reading fails worse: the CSS is correct as written, the HTML is correct as written,
and the defect lives only in the *interaction* between a grid container's track list and the number
of auto-placed children, which is not visible in either file alone. The one signal that fires is
the squeezed-prose heuristic, and it fires ~62 times — easy to dismiss as a heuristic having a bad
day on a long page. The unmistakable tell is the **page getting taller as the viewport gets
wider**: 40,463px at 834px but 94,120px at 1440px. Width up, height up is never correct.

**Rule:** in a multi-track grid, place **every** direct child explicitly, not just the one that
needed moving. `.wrap > *{grid-column:2}` with `.toc{grid-column:1}` states the layout as an
invariant, so a child added later inherits a correct position instead of re-dealing its siblings.
Pinning one child and leaving the rest to auto-placement encodes the current child *count* into the
layout, and nothing warns when that count changes.

**Verifying a fix:** render at one width below the breakpoint and two above it, and assert on the
grid container's children directly — for each, `getBoundingClientRect().width` and the resolved
`gridColumnStart`. `main` must be in the wide track at every width above the breakpoint. Then check
the cheap global invariant as a regression guard: **document height must not increase as viewport
width increases.** That single comparison catches this whole defect class without knowing anything
about the page's structure, and belongs in the layout checker rather than in any one page's tests.

---

### F48 — a `max-content` grid track, sized by an unbreakable key, starves the prose track on a phone

**Saw:** a definition list whose left column holds a monospace config key
(`thermal.body_temp_observable`, 218 px at 13 px mono) laid out as
`dl{display:grid; grid-template-columns:max-content 1fr}`. At a 500 px viewport the `dd` column was
204 px wide and its first entry ran nine lines of three to five words; at a real 390 px phone the
column was **131 px** — two or three words per line, 377 px tall for one sentence. A second `dl` on
the same page, with a longer mono term (281 px), had been shipping the same way at 141 px / 122 px since the page
was first published. Nothing overflowed, nothing was clipped, and the desktop render was perfect.

**Cause:** `max-content` is the right track size for a column of short keys — it makes the keys line
up and gives the prose everything else. But a monospace identifier cannot wrap, so the track's
`max-content` is also its `min-content`, and the `1fr` track absorbs the entire shortfall as the
viewport narrows. The layout is doing exactly what it was told; it was told the wrong thing for a
phone.

**Why neither review method catches it:** the stylesheet reads as a textbook two-column list, and
the geometry checker is nearly blind to it. Its narrow-column heuristic fires at 150 px, so it
reported the older 141 px instance at 500 px and said nothing about the new 204 px one; and the
`--pin-width 390` pass — the only pass that lays the page out at phone width — reports **overflow
only**, not narrowness, so the 131 px column it would have seen is never printed. A defect that
appears only below Chrome's 500 px floor and only as *narrowness* is in the tool's blind spot twice
over.

**Rule:** any grid whose first track is `max-content` over unbreakable content stacks to one column
below the width at which the flexible track drops under about 40 characters:
`@media (max-width: <key + 40ch + gap + padding>) { dl{grid-template-columns:1fr} }`, with the
derivation beside the rule. Derive the breakpoint from the **widest key on the page**, since every
`dl` shares the selector.

**Verifying a fix:** in the pinned 390 px pass, read `getBoundingClientRect().width` on every `dd`
and require it to be at least 40 × the `dd`'s `ch`; and extend the pinned probe to report narrow
text columns as the default pass does, so the next instance is printed rather than inferred.

### F49 — a short inline code chip splits after its leading hyphens at a line end

**Saw (2026-09-14, House Style Sheet):** at 1440 px a sentence ended in `--` and the next line began
`accent` — the custom-property name `--accent` torn in two, and `--series-1` exposed the same way.

**Cause:** hyphen-minus is a native line-break opportunity. The browser breaks after it even when the
whole chip would fit on the next line, so a chip that is short enough never to need wrapping still
wraps. This is not F8 (an unbreakable string overflowing): the chip has too many break points, not
too few. `overflow-wrap:anywhere` on `code`, correct for long paths, does nothing to stop it.

**Why both review methods missed it:** static review reads `<code>--accent</code>` as one token; the
geometry checker sees no overflow, because nothing overflows — the text just breaks in the wrong place.

**Rule:** keep short identifier chips whole. The house-style builder
(`scripts/analysis/style/build_style_page.py`) inserts U+2060 WORD JOINER after every `-` inside a
`<code>` of 32 characters or fewer, and leaves longer, path-like chips free to wrap. A hand-built page
can do the same, or give short chips `white-space:nowrap`.

**Verifying a fix:** at several widths, for every inline `code` whose text starts with `-`, check that
`getClientRects().length` is 1 unless the chip is longer than its line.

### F49 amendment — a short chip wraps at a plain space it never needed

The original F49 is a chip breaking after a leading hyphen. Same shape, different break character:
an inline `.mono` expression carrying ordinary spaces — `γ = W·h + b` — split across two lines with
the break falling **before the equals sign**, at every width below 1440. The chip is 84 px wide in a
255 px column: it never needed to wrap at all. It wrapped because a space is a break opportunity and
the line happened to end near it.

`overflow-wrap:anywhere` is not the cause and removing it does not help; the spaces are.

**Rule:** an expression or identifier chip short enough that it should never wrap gets `&nbsp;` for
its internal spaces, or a `white-space:nowrap` scoped **to those spans only**. Never put `nowrap` on
`.mono` or on a selector that reaches a table — that is a min-content change everywhere the selector
lands, which is the F35 amendment.

**Verifying a fix:** assert `getClientRects().length === 1` for every inline chip narrower than about
a third of its container, at the narrowest width the page supports.

### F50 — an inline citation chip separated from its word by a breakable space

**Saw (2026-09-14, Loop and Graph Engineering tutorial, first format gate):** at every width a
sentence read `34 co-authors [1] . It lists` — a visible gap between the chip and its full stop. At
834 / 500 / 390 px, 1 / 3 / 2 chips began a line on their own, e.g. `…who prompts the agent` ↵
`[2] . The person writes…`.

**Cause:** the template wrote `word {{CITE:x}}.`. `white-space:nowrap` keeps the chip itself whole,
but the ordinary space *before* it is still a break opportunity, so the chip can wrap alone; and the
punctuation after it sits outside the chip's right padding, whose `--surface` tint is nearly
invisible on `--ground`, so the padding reads as a space. Related to F49 (a chip breaking where it
should not) and F26 (a superscript and its line box), but neither rule covers it.

**Why both review methods missed it:** static review sees a correctly `nowrap`ped chip; the geometry
checker sees nothing overflow. Only reading rendered lines, or probing which chips start a line box,
shows it.

**Rule:** a citation chip is never preceded by a breakable space and never followed by the sentence's
punctuation. The builder moves any following `. , ; :` in front of the chip(s), deletes the
whitespace before each chip, **and puts U+2060 WORD JOINER immediately before each chip**; the chip's
own `margin-left` supplies the visual gap. Deleting the space alone is not enough: the second gate
found Chrome still breaks between sentence punctuation (`.` `:` `”`) and the chip's `[`, leaving
1–3 chips per width at a line start and two alone on a line; the word joiner closed all of them
(`scripts/analysis/tutorials/loop_graph_engineering/build_page.py`). A page built from the
field-review citation pattern (guide §12b) should do the same.

**Verifying a fix:** at 834, 500 and 390 px, for every `a.cite`, check that its first client rect is
not the first inline box on its line (compare its `top` with the previous text node's last rect), and
that the character after the chip is never `.`, `,`, `;` or `:`.

### Tool note — the overlap test compares bounding boxes, so two wrapped inline chips always "overlap"

**Saw (2026-09-14, Loop and Graph Engineering tutorial, second format gate):** `check_artifact_layout.py`
reported "text overlaps other text" between two consecutive long path chips in the Provenance paragraph
at every width. The crops at 390 and 500 px showed clean, non-overlapping lines.

**Cause:** the overlap test uses `getBoundingClientRect()`. A *wrapped* inline element's bounding box
spans the full column across every line it touches, so any two consecutive inline elements that both
wrap report as overlapping even though no glyphs collide. A fragment-level comparison using
`getClientRects()` found zero overlapping fragments.

**Rule:** treat an overlap report between two wrapped inline elements as unconfirmed until the line
fragments (`getClientRects()`) or a crop show a real collision. Expect it on any page with two adjacent
long `code` chips until the checker compares fragments instead of bounding boxes.

### F51 — a heading placed mid-container under a uniform flex `gap` is equidistant from the paragraph above and below

**Saw (2026-09-14, Loop and Graph Engineering tutorial, §06 gate):** five idea headings (B–F) sat 18 px
under the previous idea's closing paragraph and 18 px over their own opening one, so each read as a
caption to the wrong paragraph.

**Cause:** `.col{display:flex;flex-direction:column;gap:18px}` plus `h3{margin:0}`. That is correct while
every `h3` is the first child of its section (the section boundary supplies the `.wrap` 52 px gap), and
wrong the first time a heading is emitted mid-section.

**Why both review methods missed it:** nothing overlaps, clips or overflows, and both rules are correct
for the structure they were written against. Only measuring the space above against the space below
shows it.

**Rule:** a heading's space above must exceed its space below. Either never emit a heading mid-container,
or give non-first headings a `margin-top` larger than the gap (the tutorial page uses
`.col > h3:not(:first-child){margin-top:24px}`).

**Verifying a fix:** for every `h2`/`h3` that is not the first child of its container, assert
`gapAbove > gapBelow` from `getBoundingClientRect()` at 1440 and 390 px.

### Tool note — the interaction checker's tab walk stops at the first repeated identical stop

**Saw (2026-09-14, same gate):** `check_artifact_interactions.py` stopped its tab walk after 3 stops
(`[1]`, `[1]`, Figure 1). Its dedupe key is `(tag, id, text, w, h)`, so identical citation chips share a
key and the walk treats the repeat as a cycle. Figures 2–13's focus rings went unchecked by the walk.
**Rule:** until the key includes document-order index or a DOM path, do not read a short tab walk on a
page with repeated identical chips as coverage.

### F18 amendment — the label-fit guard checks axis labels only, so a rotated `ax.text` walks out of the panel

The original F18 is an **axis label** wider than its panel. `_plot.assert_labels_fit(fig, ax)` measures
`ax.xaxis.label` and `ax.title` against the panel width and refuses to save on overflow. It looks like
a general guard and is not: it never touches `ax.texts`.

**Saw (2026-09-16, recovery_in_bush_tuning format gate):** in the study's answer figure a rotated
annotation — "half the threshold, or twice the budget", `rotation=90`, anchored low on a log y-axis —
started inside the axes and ran out through the **bottom**, printing across the x-axis title so the
reader saw `(injur`**y**` points`. Two further escapes in the same figure set were found only once the
missing check was written: a three-line advisory note ran 220 px past the right edge of its own panel,
and a marker label ran 110 px past it.

**Cause:** an annotation is anchored in **data** coordinates with a **pixel** offset, so how far it
reaches depends on the axis scale, the rotation and the string length at draw time. None of those is
knowable when the call is written, and matplotlib clips nothing by default.

**Why nothing caught it:** three separate guards each looked past it. `_plot.assert_labels_fit` reads
only the axis label and the title. `house.check_floor` measures type size, not position.
`house.save`'s margin-ink check is defeated by `bbox_inches="tight"`, which **grows the canvas** to
include the escaped text — so the figure is not clipped, it is merely wrong, and the guard sees clean
margins. And the DOM layout checker sees a PNG.

**Rule:** measure every **hand-placed** text artist's rendered bbox against its own axes bbox and
refuse to save on escape. Ticks, axis labels and titles are excluded — they are supposed to sit
outside. `house.assert_text_inside_axes(axes)` does this and is now called by all five scripts of
`scripts/analysis/studies/recovery_in_bush_tuning/`; it caught two of the three cases above by itself.

**Verifying a fix:** re-run the figure script. The guard raises with the offending string, the pixel
overshoot and the rotation, which is enough to re-anchor without re-rendering by eye. Where an
annotation has nowhere collision-free to sit, move its text to the **legend** — a line's meaning
belongs there anyway — rather than shrinking it until it fits.

### F52 — an annotation ink chosen against the page ground, drawn over a colour-mapped ground

**Saw (2026-09-16, recovery_in_bush_tuning format gate):** three labels on a heat map — "shipped
default", and "a01" in both panels — were set in `--ink-2` and drawn over the dark end of a blue
sequential ramp. Measured contrast about **1.5 : 1**. At 1440 px they were readable by squinting; at
834 px they were effectively absent. The token was the correct one for the page, and every static
check of it passes.

**Cause:** a text colour is chosen once, against the **page ground**, where `--ink-2` is about 8 : 1.
A heat map has no single ground: the colour under a label is whatever the data puts there, and a
label anchored in data coordinates lands wherever its setting happens to be. A marker moves with the
data; the ink does not move with the marker.

**A second, related face of the same defect:** the house sequential ramp runs through `--series-1`
exactly. On a page that spends blue on a data category, a blue marker is then drawn on blue ground and
survives only on its white edge — the F11 second amendment, reached from the colour-ramp side. The fix
is a **neutral ramp for that figure**, not a change to the shared one, which is blue by design and has
other consumers.

**Why nothing caught it:** contrast checkers read tokens against a declared background, and the
declared background is right. The ground that matters is inside the PNG, and it varies per pixel.

**Rule:** any text drawn over a heat map, an image or a data line is **outlined in the page ground**
rather than recoloured — `house.halo()` returns the `path_effects` list
(`withStroke(foreground=PAPER)`). One ink then survives every ground, including grounds the data will
move under it next time the figure is regenerated. The same treatment applies to contour labels and
to contour lines themselves.

**Verifying a fix:** sample the rendered ground beneath each text bbox and compute contrast against
the text colour — do **not** check the token against the page background, which is the measurement
that passes while the label is invisible. A halo makes the check moot, which is the point of
preferring it to a per-region colour choice.

### F33 amendment — a gridline is ink, and a per-glyph halo does not mask one

The original F33 is "an annotation goes where there is no ink. Enlarge the axis margin until empty
space exists." In practice "ink" gets read as *data* — the series, the markers, the bars — and a
gridline is mentally filed as background.

**Saw (2026-09-16, recovery_in_bush_tuning re-gate):** in the validation figure's residual panel, the
horizontal rules at 10⁰, 10⁻² and 10⁻³ ran straight through two hand-placed notes, at every viewport
width. The note had already been given a `house.halo()` outline, and the strike-through survived it.

**Cause, and the part worth keeping:** `path_effects.withStroke` outlines **each glyph**. It breaks a
rule where a letter is and leaves it running in the gaps **between** letters — so a line still reads as
continuous across a word at normal viewing size. A halo solves a contrast problem (F52). It does not
solve an occlusion problem.

**Rule:** a multi-line annotation over a gridded panel brings its own ground —
`bbox=dict(boxstyle="square,pad=0.5", facecolor=PAPER, edgecolor="none")` — rather than a halo. Reserve
the halo for short labels over a colour-mapped or image ground, where there is no line to interrupt.
Either way, treat gridlines as ink when deciding where an annotation may sit.

**Verifying a fix:** crop the annotation at full resolution and look along each text line for a rule
resuming on both sides of the block. If the rule stops at the block's edge and restarts after it, the
patch is masking; if it reappears between words, it is a halo and it has not worked.

### F53 — a legend handle shorter than one dash period shows a line style the plot does not have

**Saw (2026-09-16, recovery_in_bush_tuning re-gate):** three of five figures distinguish series by
**line style** (solid = resting in the open, dashed = resting on a bush), and the legend handle for a
dashed series rendered as a dash-and-a-bit — close enough to a short solid rule that the legend did not
teach the distinction the figures rely on.

**Cause:** `house.py` sets `legend.handlelength: 1.1` (em). A dash pattern needs at least one full
period, and preferably two, inside the handle before the handle *depicts* the style rather than
sampling it. The value is fine for a legend that separates series by colour alone, which is what it was
chosen against.

**Why nothing caught it:** nothing is clipped, overlapped or off-palette, and the figure is a PNG. It is
a legibility defect in a legend, which no geometric check looks at.

**Scope, and why it is recorded rather than fixed:** `handlelength` is in the **shared** style module,
so changing it regenerates every figure in the project that uses the house style, not only the three
here. That is its own change with its own before/after check, not a line to slip into a format-gate
pass.

**Rule:** where a legend distinguishes series by dash pattern, the handle must be long enough to show at
least one full dash period — roughly `handlelength >= 2.4` for the house dash patterns. A figure that
cannot have a long handle should label the lines directly instead.

### F54 — a page-specific class reusing a house class name inherits every declaration it does not override

**Saw:** an entire page rendering as one flat `--pick` rectangle at every width, with a single stray
expression in the top-left corner. Nothing else. Clicks landed on the rectangle.

**Cause:** the page was ported onto the House Style Sheet, whose head defines the full-size figure
viewer as `.lb { position:fixed; inset:0; z-index:99; background:rgba(12,12,14,.93); display:flex }`.
The page's own block then declared `.lb` for three small equation label chips, setting font, size,
background, colour and padding. Equal specificity, so the later rule won — **but only for the five
properties it named.** `position:fixed`, `inset:0`, `z-index:99` and `display:flex` survived from the
house rule, so each chip became a full-viewport overlay and the last one in the DOM painted over the
document.

**Why every check passed it:** an orphan-class audit compares classes *used* against classes
*defined* and sees one name with one definition site — it cannot see a name defined twice. The
geometry checker compares text bounding boxes, not paint order, so no box overlapped. The keyboard
walk still reached every link, because they were all still there, underneath. And both tools happily
reported "clean" on screenshots that were 100% a single colour.

**Rule, and it is a build step rather than a review step:** before appending page-specific CSS to a
house head, **intersect the set of class selectors defined in the two blocks and require it to be
empty**, or inspect every name in the intersection and satisfy yourself it is a deliberate
descendant or token-scope override rather than a second component wearing the same name. And delete
any house component the page does not use — this collision lived entirely inside a viewer block that
the page had already dropped the script for.

**Two instances, and the second is why the guard matters more than the fix.** `.lb` was visible and
fatal. Applying the intersection guard immediately surfaced `.sw` — a house colour-swatch container
(border plus `background:var(--ground)`) reused by the page for a 13px legend swatch. That one was
invisible, because an inline `style` on every instance happened to override the inherited background.
A latent collision waiting for the inline style to be refactored away.

**Verifying:** compute `position` on every element whose class appears in both blocks; assert no
element with `position:fixed|absolute` covers more than half the viewport; and sample
`document.elementFromPoint()` at the centre of ~50 text nodes — if the hit element is neither the
node nor an ancestor of it, something is painted over the page.

**Tool note:** neither checker detects an element painting over the page, and neither notices a
capture that is one solid colour. An ink-fraction sanity check on the screenshot would have caught
this in one line, and belongs in `check_artifact_layout.py` alongside the `elementFromPoint` sample.

### Tool note — a guard "called from all N scripts" is a guard only where the call site exists

**Saw (2026-09-16, recovery_in_bush_tuning re-gate):** a new figure guard
(`house.assert_text_inside_axes`) was wired into five figure scripts by hand and reported as such. It
was in four. The fifth kept only a **comment naming the guard** next to the annotation it was meant to
protect — a later edit of that file replaced a slice between two string indices without re-reading what
was inside it, and took the call (and the figure's halo loop) with it. The figure then shipped
unguarded, and the report said it was guarded, because the comment read like evidence.

**Rule, two halves.** For the *reader* of a claim: **grep the call sites, not the claim** — a comment
mentioning a function is not a call to it, and `grep -rn "house.save\|assert_text_inside_axes"` costs
nothing. For the *author* of a guard: **a check that every script must remember to call is a check that
some script will forget.** Put it on the one path every figure already takes — here, inside
`house.save()`, which no figure can skip — and keep the standalone function only for scripts that want
to fail earlier. Provide a documented opt-out (`check_text=False`) for the legitimate exception rather
than letting scripts drift out silently; the loop-and-graph tutorial's diagrams use it, because their
axes are a bare borderless canvas with no axis title for a label to print through.

**Related:** the same shape as F15 (a number typed into markup where no test reaches it) and as the
entry above about editing one of N repeated structures with a `.*?` regex — an edit that spans more
text than its author was looking at.

### F55 — a legend's swatches copied as literals from another module's palette, orphaned when that palette changed

**Saw (2026-09-16, renderer_layout_redesign format gate):** after three icons were redrawn — food from a green
apple to a rose-red one, the hiding predator from a green bush-with-eyes to a charcoal thorn cluster, the
neutral animal from teal to grey — Figures 3, 4 and 8 and all 35 scrubber frames showed the new icons, and
Figure 6's colour key, 800 px below Figure 8, still read **Food = green, Hiding predator = dark green,
Neutral = teal**. Its three swatches were byte-identical to the *old* icon constants (`#1E9E5A`, `#33503A`,
`#0E7490`). Green now meant food in one figure and leaf/bush/tree in the next; teal meant a neutral animal in
Figure 6 and the smell ramp everywhere else.

**Cause:** the figure script chose its categorical hues to match the icons — the comment says so, "object icon
colours where free" — but wrote them down as literal hex strings instead of reading them from
`dashboard_style.py`. When the icon module changed, the copy did not. The page's footer then declared Figures
5–7 un-regenerable (the world they were drawn from was archived), which made the stale key look permanent.
That claim was wrong: the script reads a saved export (`data/extended.json`), not the world, and re-running it
in a scratch tree reproduced all three PNGs byte-for-byte.

**Why neither review method catches it:** the figure is correct against its own script, the icons are correct
against theirs, and a diff of the icon commit touches neither the figure script nor the legend. Nothing
overflows, overlaps or clips. F11's pixel census against `:root` tokens does not fire, because the stale hues
are not page tokens — they are the *previous* values of a module the census never reads. Only holding one
figure's swatches against another figure's glyphs shows it.

**Rule:** a legend that means "the colour of X" imports X's colour; it never restates it. And a note that says
"this figure cannot be regenerated" is a claim to be tested by running the script, not a reason to ship a
figure that contradicts its neighbour — say what *step* cannot be re-run (here, the export), not that the figure
is frozen.

**Verifying a fix:** for every figure whose hues are keyed to a palette elsewhere, take the swatch pixels from
the rendered PNG and assert each is within a small ΔE of the *current* value in the module that owns it. After
any icon or palette change, re-run every figure script on the page from its saved inputs and `cmp` the outputs:
a figure that changes was keyed to the palette; a figure that must change but cannot be re-run is the defect.

### F33 amendment — a label anchored at a marker on a line, where the line runs on past the marker

**Saw (2026-09-16, recovery_in_bush_tuning Figure 1 gate):** the "passes A" verdict label in panel (a),
anchored at the marker where the recommended line meets the rest-budget edge (x = 50), with the line
itself drawn on to the axis edge at x = 62. The stroke ran straight through the glyphs at every width —
legible-but-struck-through at 1440 px, a green smear at 390 px. A struck-through "passes" reads as its
opposite.

**Cause:** the annotation was placed at the *event* (the marker) rather than at the *end of the ink*.
F33 already says an annotation goes where there is no ink; the trap is that "the marker" and "the end of
the line" look like the same point when the call is written, and are not when the line's x-range exceeds
the marker's.

**Why nothing caught it:** `house.assert_text_inside_axes` (F18 amendment) reads like a general text
guard and checks only that text stays *inside* the axes — text over data is inside the axes. The guard's
existence is the hazard: a script that calls it looks protected against F33 and is not.

**Rule:** a label for a line's end goes beyond the line's last x, or above/below it with a y offset that
clears the stroke, or into the legend. Verify per F33: sample every plotted series over the label bbox's
x-range and assert no y falls inside the bbox.

### F56 — a script-emitted description that describes the intended drawing, not the drawn one

**Saw (2026-09-16, same gate):** Figure 1 panel (b)'s alt text, its "How it is computed" block and its
script-emitted Data line all said "three rectangles" / "3 boxes with 2 diagonals", including "a faint
reference one 25 by 50". The render has two rectangles drawn as top-and-right edge pairs, and for the
third only a grey dot at its corner and a dotted diagonal — a pixel scan at x = 50 between y = 12.5 and
y = 25 finds only page ground. A screen-reader user is told about a box a sighted reader cannot find.

**Cause:** the used/available Data line is emitted by the figure script, which the guide treats as
protection against hand-typed drift (F15). But the emitted *string* was still authored by hand, from the
author's plan for the figure, and was never read back against the draw calls. Emission guarantees the
numbers in the string are not stale; it says nothing about the nouns.

**Why nothing caught it:** the F15 check asks "is this number emitted?" — it is. The F44 checks ask
"does the caption name something a theme or breakpoint hides?" — nothing hides it; it was never drawn.
The geometry checker sees a PNG.

**Rule:** the nouns in an alt text, a Data line and a method block are checked against the figure's
*artists*, not its plan. Where a script emits descriptive prose, derive counts from what it drew
(`len(ax.patches)`, `len(ax.lines)`), never from a literal — and a reviewer counts the rendered shapes
against the sentence, the same way F36 counts tick labels against a binning word.

### F57 — a values table prints the code's token where every hand-written surface prints the display name

**Saw (2026-09-17, renderer_layout_redesign format gate):** the scrubber's numbers grid, in the row
"Shared squares in this frame", read **`agent + food, neutral + rock`**. Two paragraphs above it the
caption said the two shared squares hold "the agent and food" and "a rabbit and a rock", and Figure 8
labelled that same glyph **"Rabbit"**. `neutral` is the code's token for the rabbit. Nothing on the page
told a reader the two words name one animal, so the grid read as a fifth kind of thing the world
contains.

**Cause:** the exporter serialised the renderer's occupancy census — a dict keyed by entity token —
straight into the JSON the page prints. The project's rule protects numbers by *emitting* them from the
script instead of typing them (F15), and that rule was followed here: the value is emitted, it is
current, it matches the frame beside it. The defect is *in* the emission. Emission guarantees a string
is not stale; it says nothing about whether the string is in the reader's vocabulary.

**Why nothing caught it:** every automated check passes — the token is the correct token, the row
matches the frame, no box overflows, the contrast is fine. And prose review does not catch it either,
which is the trap worth naming: an identifier that happens to be a plausible English word reads as
prose. A reviewer skims "neutral + rock" and parses "neutral" as an adjective describing the square,
not as a class name. `hiding_predator` would have been caught on sight; `neutral` was not. The more
ordinary the identifier looks, the longer it survives.

**Rule:** an exporter that emits a string a reader will see routes it through the same display-name
table the figure labels use — one table, owned by the module that defines the tokens, with a
coverage guard so a new entity without a reader's name fails at import rather than reaching a page.
A label written by hand next to that table is the same defect one step later: derive the figure's
labels from the table too, so the two cannot drift.

**Verifying a fix:** strip tags and scripts from the *built* page, then grep the visible text for
identifier shapes — `snake_case`, bare lowercase class names, short ALL-CAPS codes, config stems,
file paths — and hold every hit against the page's own vocabulary. A hit is legitimate only if the
page defines it where a reader meets it (a cell name like `M4` that the page explains, a script name
in a "how to regenerate" line); an entity's internal class name never is. Run the same grep over the
emitted data file, not only the markup, because the markup may be innocent and the payload guilty.

---

### F58 — a point label that clears every other label and still lands on somebody else's mark

**Saw (2026-09-17, imperativism field-review page; recurred 2026-09-21 on the computational-functionalism
page):** on a debate map, "Klein 2016" sat immediately beside the mark for Coelho Mollo 2018, nearer to
that mark than to its own. The placement routine was working exactly as written — it had checked the
label against every *label* already placed and found no overlap — and the figure passed the text-inside-
axes guard, the legibility floor and a careful read of the code.

**Cause:** the obstacle set was labels only. A scatter figure's marks are drawn first and are not text,
so a routine that grows its obstacle list as it places labels never sees them. Every offset the routine
tries is small by design, which means the winning offset is frequently the one that tucks the label into
the gap *between* two marks — the position that looks tidiest and reads wrongest.

**Two things bite while fixing it.** `Annotation.get_window_extent` includes the leader line's bounding
box, so a label joined to its mark by a leader measures as a box stretching back to the mark and collides
with everything on the way; measure with `Text.get_window_extent` after `update_positions(renderer)`
instead. And `subplots_adjust` after placement moves every axis under labels already measured in pixels,
so the layout must be fixed *before* the first label is placed.

**Rule:** a label-placement routine treats every drawn mark as an obstacle, padded by about a marker
radius at the figure's dpi, and accepts a candidate position only if the label is nearer to its own mark
than to any other — relaxed only for a position joined to its mark by a drawn leader line, where the
pairing is explicit. A label that fits nowhere is dropped and reported, and the script exits non-zero
rather than shipping a figure whose labels are ambiguous. The reference implementation is
`label_positions()` in `docs/project/references/computational_functionalism/page/_cffig.py`.

---

### F50 amendment — the same `&nbsp;` glue, applied to a chip that is not short

**Saw (2026-09-21, computational-functionalism field-review page, format gate):** at 360 px the
whole document scrolled sideways by 19 px, and nine reference entries pushed their status chip past
the column edge. F50's rule — glue a chip to its preceding word with `&nbsp;` so a line break cannot
orphan it — had been applied to the reference list's `[short summary from the PDF]` tag. With
`white-space: nowrap` on the chip, `implementation&nbsp;[short summary from the PDF]` is a single
unbreakable token of word-length plus chip-length.

**Why the checker under-reported it:** the layout tool measures in fallback fonts, which are wider,
so it flagged +45 px where the real fonts give +11 to +17 px. The number was wrong in the safe
direction; the defect was real at three of the widths and only the narrowest scrolled the document.

**Rule:** glue a chip to its word only when word + chip fits the narrowest supported column. A
citation marker (`[12]`) always does; a status tag carrying three or four words does not. When it
does not, use a plain space and let the chip wrap onto its own line, which is what it does elsewhere
in the same list without looking wrong.

---

### F59 — a chip styled for one word, filled from a data column

**Saw (2026-09-21, same page and gate):** a monospace status badge designed to read
`status in this corpus: open` rendered a thirty-word sentence instead, because the debate table's
`status_direction` column was appended to it. At 390 px it was a six-line block of 12.5 px mono
`334 × 132 px`; at 1440 px a three-line grey slab. Nothing overflowed, so neither the layout checker
nor the interaction checker fired.

**Cause:** two separate mistakes that look like one. The renderer prefixed `"leaning toward "` to a
column whose values already begin with `"toward"`, so the chip read `leaning — leaning toward toward
Putnam's mapping construction failing…`; and the direction text had no business in a chip at any
length.

**Rule:** a chip renders a **controlled-vocabulary** value — one of a known, short set. Free text
from a data column goes in a prose element beside it. Where a builder composes chip text from data,
assert the vocabulary (the build fails on an unknown status) and assert the length, so the first
long value breaks the build rather than the page. And when a renderer prepends a word to a data
value, check the column does not already start with it: this one shipped `toward toward`.

### F60 — a builder lifts a component from another page's TEMPLATE rather than its BUILT output

**What a reader saw.** Nothing. The page rendered, in the wrong typeface, and said nothing about it.

**What happened.** A new page's builder copied the House Style Sheet's `<style>` block so the page
would inherit the house look — and copied it from `house_style_sheet.template.html` instead of the
built `house_style_sheet.html`. The template's two `@font-face` rules read
`src: url(data:font/woff;base64,{{FONT:Regular}})`; the substitution that fills those in lives in
`build_style_page.py`, which the new builder never ran. So the page shipped with both faces pointing
at the literal string `{{FONT:Regular}}`.

**Why nothing failed.** A `{{...}}` inside a CSS `url()` is an invalid URL, and CSS **discards an
invalid declaration silently**. There is no error, no fallback warning, no visual break — the
browser simply uses the next font in the stack. The only trace is two `ERR_INVALID_URL` console
lines and `document.fonts` reporting `error` rather than `loaded`, neither of which anyone reads.

**Why both review methods missed it.** A source read sees an `@font-face` with a `src` and moves on;
the token looks like something the build fills in, and it is — just not by this build. And a
screenshot scan sees clean, legible text, because the fallback is a real font. The page looked
*fine*. What it was not was the house style, and the page declared no departure.

**The cost is bigger than the typeface.** Every width measurement taken against that build was a
fallback-metric measurement: different advance widths, different wrap points, different overflow.
One full review pass — six findings, three of them measured in pixels — had to be redone once the
real fonts loaded.

**Rule:** a builder lifts a component only from a **built artefact**, never from the template that
produces it. Where that is impractical, run the same substitution. And assert it: no `{{` may
survive into the output, and a page that embeds fonts must contain `data:font`.

**How to verify a fix:** `grep -c '{{' built.html` is 0 and `grep -c 'data:font' built.html` is
non-zero; in the browser, `document.fonts` reports `loaded` for every declared face. Re-take any
layout measurement made before the fonts loaded — it is not comparable.

### F61 — a page copies the house HEAD without the house BODY scaffolding, collapsing every gap

**What a reader saw.** Paragraphs run together with no space between them; every section heading sits
flush against the block above it, reading as that block's caption rather than as the next section's
title; prose runs about 130 characters per line while the figures beneath it are capped much
narrower.

**What happened.** The house sheet resets element margins — `p{margin:0}`, `h2{margin:0}` — and
expresses **all** vertical rhythm through flex `gap`: `.wrap{gap:52px}` between sections,
`.col{gap:18px}` inside one, with `.col{max-width:70ch}` holding the measure. A page that copies the
`<style>` block but writes bare `<section>` elements therefore gets the reset and none of the
rhythm: measured section-to-section gap 0 px, paragraph-to-paragraph gap 0 px, every heading 0 px
above and 0 px below.

**The second face, which survives the obvious fix.** Adding `class="col"` to every section fixed the
inner gaps and not the outer ones, because the page also had a `<main>` between `.wrap` and the
sections. `<main>` is `display:block`, so it was `.wrap`'s only flex child and absorbed the entire
52 px section gap. Every section carried the class and every section still touched.

**Rule:** the invariant is **`.wrap > section.col`** — the sections must be *direct children* of
`.wrap`. Any wrapper between them defeats the outer gap even when the class is correct. Copying a
house head obliges the page to copy the house body scaffolding with it.

**How to verify a fix:** assert `.wrap`'s element children are exactly the sections, and in the
browser that the gap between consecutive `section.col` is 52 px and that every `h2` has more space
above it than below.

### F62 — a scroll cue that does not say anything, or measures the wrong box

**What a reader saw.** On a phone, a five-column table cut off after the fourth column, with the
whole explanatory column off-screen — and above it, either a blank line or nothing at all.

**Three faces, all of which pass a naive "cue present, and shown only when it overflows" check.**

1. **No text.** The builder emitted `<p class="cue"></p>` — the element, the class, the toggling,
   and no words. It appears and disappears correctly and tells the reader nothing.
2. **The wrong box.** A command block was emitted as `<p class="cue">` + `<div class="scroll">` +
   `<pre>`. The house gives `<pre>` its own `overflow-x:auto`, so the `<pre>` became the scroll
   container and the `.scroll` wrapper around it could never overflow. `updateCues()` measures the
   cue's `nextElementSibling` — the wrapper — so the cue stayed hidden at 390 px while the `<pre>`
   inside it was visibly cut to `…bin/py`. Correct by every structural check, bound to a box that
   cannot overflow.
3. **The general rule behind both.** A cue is a *promise about a specific element*. It is only true
   if it says something, and if the element it measures is the element that scrolls.

**Rule:** the builder emits the cue's text, not an empty shell, and emits it `hidden` so there is no
flash before the toggle runs. A cue's next sibling must be the actual scroll container — never a
wrapper around something that has its own `overflow`.

**How to verify a fix:** for every `.cue`, read `nextElementSibling`; assert its `overflow-x` is
`auto` or it is a `<pre>`; assert no descendant of it is also a scroll container; assert its text
content is non-empty after stripping tags and entities; and assert
`hidden == !(scrollWidth > clientWidth)` across a width sweep that **includes one below 480 px**,
which is where the only misbinding on the page that produced this entry actually lived.

### F24 amendment — the rule is about any scroll container, and the signal is a cue visible on a desktop

**What a reader saw.** On a 1440 px desktop, the one equation a page's new section existed to state,
cut at `… / max_te`, with a scroll cue above it.

**Why every mechanism on the page missed it, each behaving correctly.** The cue truthfully reported
that its box overflowed. The layout checker truthfully found no page-level horizontal overflow,
because it exempts scroll containers **by design** — that exemption is what stops it firing on every
legitimately-scrolling wide table. The build check asserted the cue was present, carried text, and
was bound to the element that actually scrolls: all three true. Nothing in the stack distinguishes
"this box scrolls on a phone, as intended" from "this box scrolls on every screen ever made".

**The rule, generalised from tables to anything with its own `overflow`.** Overflow at the *widest
supported viewport* means the content was never designed to fit its column. A phone scroll is an
accommodation; a desktop scroll is a defect. The detectable signal is therefore not the overflow —
it is **a cue that is visible at the widest width**.

**Two traps in guarding it at build time.** First, entities: a formula built from `&minus;`,
`&sup2;` and `&radic;` measures at roughly twice its rendered width if you count source characters,
so entities must resolve to one glyph before measuring. Second, and the reason this amendment
exists rather than a bare limit: **a character count silently encodes one font's advance width**,
which is exactly the assumption F35's measured floors were written to stop people inheriting. Derive
the limit from two stated, browser-measurable constants — the prose column at the widest width, and
the monospace advance at its rendered size — so that a change to either is a change to a named
number rather than a mystery.

**How to verify a fix:** `pre.scrollWidth == pre.clientWidth` at the widest supported width, and the
cue hidden there. It may legitimately still scroll, with its cue visible, on a phone.

**Also worth knowing:** the fix that produced this defect was itself a fix. The `<pre>` began as an
ASCII fraction with stacked numerator and denominator, whose middle line sat one column off and
which would have drifted the first time anyone edited a term. Breaking each equation at its `+`
signs, one term per line with a hanging indent, removes both problems at once: nothing is
column-aligned across lines except the leading `+`, so no edit can shift another term.


### F64 — a figure-level legend built from one panel's handles, where that panel lacks a series

**What a reader saw.** A 15-panel figure (behaviour by injury, five levels) with blue and orange
lines in 12 panels and a legend naming only "ordinary agent"; the caption said "the two agents again
look alike".

**Cause.** The shared legend was built by `legend_below(ax[-1, 0])`, i.e. from the handles of the
bottom-left panel. In that grid the first column is a level whose second run had not been collected
yet, so the panel held one series and the figure's legend inherited that panel's truth.

**Why nothing caught it.** The legend was correct for the panel it was read from; the figure guards
check text size, placement and overlap, never that the legend's label set equals the set of labels
actually plotted; and the sibling figure built by the same function was right only because its first
column happened to be complete.

**Rule.** A legend shared by several panels is built from explicit handles (one per series the figure
can show) or from the union of every panel's handles — never from one panel's.

**How to verify a fix.** Before saving, collect `get_legend_handles_labels()` over all axes and assert
the legend's labels equal that union; render the figure with one series missing from the first panel
and check both entries still appear. Found on "Injury, Behaviour and the Modulator", Figure 10
(`scripts/analysis/studies/modulator_clues/_inj.py::dose_grid`), 2026-09-24.

### F65 — a dense raster figure with no width floor shrinks to a thumbnail on a phone

**What a reader saw.** On a 390 px phone, three figures with 26–27 labelled rows or twelve small maps
rendered 334 px wide; their row labels came out at about 4–5 px, and the fit-mode viewer (354 px) did
not help. The same page gave every data table a scroll box and a cue.

**Why it was missed.** `check_floor` / `assert_min_text_px` measure text against the desktop column
(688 px), where the labels were 10.5 px; the layout checker found no overflow because the image simply
scaled down. Nothing measured a raster's label size at the narrowest width.

**Rule.** A figure whose smallest label falls under 9 px at 390 px gets a width floor (canvas px × 9 /
label px, rounded up) inside a `.scroll` box with a `hidden` cue toggled by the same measured-overflow
script as the tables.

**How to verify a fix.** Pinned 390 px pass: each dense figure's `img.clientWidth` ≥ its floor, its
scroll box overflows and its cue is visible; at 1440 px the cue is hidden and the figure fills the column.
Found on "Interactions Between Internal States", 2026-09-26.

### F66 — an unclosed `<section>` nests every section after it, and only the spacing shows it

**What a reader saw.** On a 1440 px desktop, the last two section headings of a fifteen-section page sat
18 px below the paragraph above them where every other heading sat 52 px below its predecessor. Nothing
overflowed, nothing overlapped, every word was readable — the page just looked wrong at the end.

**Cause.** The template had 18 `<section class="col">` and 17 `</section>`; section 13 was never closed.
HTML has no error for this: the parser nests sections 14 and 15 *inside* 13, so they become children of
a `.col` flex column (gap 18 px) instead of children of `.wrap` (gap 52 px). Pre-existing for at least one
publish before it was noticed.

**Why nothing caught it.** The markup reads correctly section by section — the missing tag is an absence,
not a wrong line. The layout checker measures overflow, overlap and zero-height boxes; a nested section
produces none of them. The interaction checker walks focusable elements; a section is not one. A screenshot
scan passes over it because a heading 18 px below a paragraph is still a heading below a paragraph.

**Rule.** Sections are balanced by count at build time: the builder fails when `<section` and `</section`
counts differ. A page's top-level sections all share one parent.

**How to verify a fix.** `document.querySelectorAll('section section').length === 0`, and for every `h2`
the vertical gap to the previous sibling of its section is the same number (here 52 px, or the group-heading
value where an `h3.group` precedes it). Found on "Interactions Between Internal States", 2026-09-27; the
builder now asserts the count (18/18).

### F67 — a nested `<p>` inside a flex column: the parser's phantom paragraphs each cost a gap

**What a reader saw.** One section's heading-to-prose and prose-to-figure spacing at twice the
page's rhythm — 36 px where every other section had 18 — at every viewport width.

**Cause.** The template carried `<p><p>…</p><p>…</p></p>` (a prose placeholder wrapped in `<p>` was
filled with text that brought its own `<p>` tags). HTML has no error for this: the parser closes the
outer `<p>` the moment the inner one opens, leaving an empty `<p>` before the first paragraph and
another after the stray `</p>`. Both are zero-height, but `.col` is a flex column with `gap:18px`, and
a zero-height flex item still takes its gap.

**Why nothing caught it.** The layout checker's zero-height test looks for elements *with text*;
these have none. Nothing overlaps, clips or overflows. A source read sees a paragraph inside a
paragraph and reads it as one paragraph. Only measuring the gaps, or comparing the section
against its neighbours in the render, shows it.

**Rule.** The builder fails when a `<p` opens inside an open `<p>`, and when any empty `<p>`
survives into the output.

**How to verify a fix.** `document.querySelectorAll('.col > p:empty').length === 0`, and for every
section the H2-to-next-sibling gap equals the column gap. Found on "Continual Worlds",
2026-09-28, first format gate.

**F67 note (2026-09-29) — figure anchors.** Guide §13c first prescribed the deep-link anchor as an
empty `<div class="fig-anchor" id="fig-<stem>">` before each `<figure>`. On every page whose `.col`
spaces by `gap`, that zero-height div took a gap: anchored figures sat 36 px below their predecessor,
unanchored ones 18 px (measured at 390 and 1440 on five pages; a page spacing by margins was
unaffected). Forms tested in Chrome, gap / where `#fig-…` navigation lands:
empty div before the figure — 36 px / correct; **`id` on the `<img>` — 18 px / correct (adopted)**;
div as first child inside `<figure>` with `position:absolute` — 18 px / correct;
`margin-bottom:-18px` — 18 px / correct but couples to the gap value;
div before the figure with `position:absolute` — 18 px / **wrong: lands at the section top**, because
an absolutely-positioned flex child takes its static position at the container's start;
`display:none` or `display:contents` — 18 px / **navigation does nothing**. Verify a fix by measuring
the anchored figure's gap to its previous sibling; it must equal the unanchored figures' gap.

