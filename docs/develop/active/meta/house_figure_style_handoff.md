---
title: "House figure style — state of the work, and what is left"
topic: meta
status: active
created: 2026-09-09
last_updated: 2026-09-09
---

# House figure style — state of the work, and what is left

## What this is

An attempt to put this project's figures into the visual style of Anthropic's
[transformer-circuits.pub/2026/workspace](https://transformer-circuits.pub/2026/workspace/index.html)
page. The work was **paused mid-flight** on 2026-09-09 because it was costing more effort than it
was returning. Everything below is committed and working; the list of what is *not* done is at the
end, and nothing is half-written on disk.

The shape the user asked for, and the shape it now has: **the style lives in a Python module, one
script draws each figure and writes a vector file, and the artifact loads that file.** Not prose
describing a style, and not a chart hand-drawn in the page's HTML.

## What is done and committed

| thing | where |
|---|---|
| the style, as code | `scripts/analysis/style/house.py` |
| one script, one figure (the specimen) | `scripts/analysis/style/spec01_line_chart.py` |
| the page builder, six guards | `scripts/analysis/style/build_style_page.py` |
| the page template and its built output | `docs/develop/active/meta/transformer_circuits_style{.template,}.html` |
| Pretendard, vendored + Latin subsets | `assets/fonts/pretendard/` (SIL OFL 1.1, licence included) |
| vector output for the *existing* figure pipeline | `scripts/analysis/ladder/_plot.py` — `finish()` now writes SVG + PNG |

`house.py` holds every number in one place: no axis spines (the source *deletes* them rather than
lightening them), no tick marks, faint `#ddd` rules, an 11/13/15 pt hierarchy inside the figure,
Paul Tol's `#0077bb`/`#ee7733`, legend below and unboxed. `save()` emits SVG, PDF and PNG, and runs
two checks before returning: the smallest label must clear the 9px floor at the display column, and
no ink may touch the canvas edge.

The specimen script is the test of whether the module works: it sets **no** colour, font size, spine
or grid handling of its own. If it ever has to, the module has failed at its job.

## Where the style came from, and one warning

Read out of the page's own three stylesheets (`paper.css`, `shared-styles.css`, `bundle.css`),
transcribed in `transformer_circuits_style.html`.

**Do not use a summarising fetch for this.** The first attempt did, and it returned a plausible and
largely wrong answer: body text 16px (it is 13px), a generic system font stack (three proprietary
Anthropic faces), and "viridis or similar" for figures (the two series colours are named `--tol-blue`
and `--tol-orange`). Fetch the CSS.

One finding that changes how every colour reads: each grey is written `var(--gray-N, #hex)` and no
`--gray-N` is defined in any of the three sheets, so **the fallbacks are what render**.

## Gotchas already paid for — do not rediscover these

- **matplotlib's SVG backend needs a font-weight *name*.** `axes.labelweight: "600"` raises
  `KeyError: 600` inside `backend_svg` — it maps weights through `fm.weight_dict`, which has no
  integer keys. Use `"semibold"`.
- **`woff2` subsetting needs `brotli`, which is not installed.** `pyftsubset --flavor=woff` uses
  zlib and works; a Latin subset of Pretendard is ~15 KB per weight against 766 KB, which is small
  enough that woff2 is not worth installing a dependency for.
- **Pretendard registers fine from `.otf`** via `fm.fontManager.addfont()`, giving weights 400/500/600.
- **You cannot negative-control a canvas-edge guard by drawing off-canvas.** `bbox_inches="tight"`
  *expands* the crop to include the stray artist, so nothing is ever clipped that way. The guard was
  instead verified against a real case: the sensor-grid figure `g03` before its axis label was
  shortened reports 81 ink pixels on its right edge.
- **An edge-ink threshold of 40 flags antialiasing.** A rotated axis label's halo reads as a clipped
  label. 90 needs a pixel clearly darker than paper.
- **Do not scale type up because a figure is "rendered wide and shown narrow".** A first draft did
  (`SCALE = 1.55`) and produced a specimen whose labels ran off all four edges: at 150 dpi an 11 pt
  label is already 14.7 px in a 730 px column for a 1140 px-wide figure. Shrink the canvas, and let
  `check_floor()` prove it.
- **Pretendard is proportional.** Putting it first in a `FONT_MONO` stack makes "mono" mean nothing.

## Two places the source style cannot be copied literally

Both are recorded on the page itself, and both are the reason a straight copy would be wrong here:

1. **Sizes.** Their pages display a figure at roughly its natural width; ours render 1500–2300 px and
   display in a 730 px column, so their literal 11 px label lands near 5 px. What transfers is the
   *ratio*, not the absolute values.
2. **Colour meaning.** Their blue and orange mean "series 1" and "series 2". Several pages here
   already spend purple/blue/green on what a modulator reads. `apply(series=[...])` therefore takes
   an explicit palette: the house colours are a default, not a mandate.

## What is NOT done

1. **The rebuilt page is not published.** The artifact at
   <https://claude.ai/code/artifact/a273f767-34de-47c6-899d-0162b1f3a7ee> is the **earlier** version,
   whose specimen chart was hand-authored inline SVG. The repo is ahead of the live page. Republish
   with `url=` that address — do not publish without it or a second artifact appears.
2. **A format review of the rebuilt page was in flight and was stopped**, so its verdict is unknown.
   It had got as far as "tool exits 0 on both passes; the two zero-height hits are the SVG's
   `<metadata>` and internal `<style>`, non-rendered by design". Re-run it before publishing.
3. **The house style is not applied to any real figure.** The 15 sensor-ladder figures and the 9
   neuromodulator-grid figures still use their own styling. Adopting it would change every published
   PNG, so it is a decision, not a chore.
4. **Three ladder scripts still say "dwell"** — `lad05_discrimination`, `lad10_hypervigilance_proximity`,
   `lad11_hypervigilance_odour` — missed by the 2026-09-07 rename. Separately, 11 of the 15 committed
   ladder PNGs already differ from what today's code draws, because that rename changed their labels
   and the figures were deliberately not regenerated.

## Related

- [[transformer_circuits_style]] — the transcription, and the human-readable half of `house.py`
- [[artifact_generation_guide]] §2.6 and §0 — the click-to-open rule, and how the guide gets read
- [[artifact_format_bugs]] — F37, F38, F39 were found during this work
- `.claude/skills/publish-page/SKILL.md` — every artifact publish now routes through it
