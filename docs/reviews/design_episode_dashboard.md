---
title: "Design review — episode-video dashboard (renderer layout redesign)"
topic: reviews
status: complete
created: 2026-09-14
last_updated: 2026-09-14
---

# Design review — episode-video dashboard

> **Reviewed by**: visual-design-reviewer
> **Date**: 2026-09-14
> **Object**: the proposed dashboard frame and its figures in
> [[RENDERER_LAYOUT_REDESIGN]] (`docs/develop/active/refactors/renderer_layout_redesign/figures/`)
> **Mock-up**: `tmp/20260914_101500_design_episode_dashboard/mockup_frame_step015.png` (throwaway, not committed)

## Verdict

**Not yet at the big-tech-presentation bar.** The layout idea — a grid view in the middle with
panels for the senses around it — is sound. What looks dated is the surface: grey boxes with grey
borders, typewriter-style digits, all-caps titles, a pale blue grid stamped with a number in every cell,
the same blue used for five different things, and cartoon sticker icons that fight the flat interface.
The mock-up shows the same information in a modern style, drawn from the same recorded episode.

The three changes that matter most:

1. **One typeface and a white-card surface.** Drop the monospace face and the all-caps titles. Use
   Pretendard with fixed-width digits, sentence case, white cards on a quiet canvas.
2. **A colour system where each colour means one thing.** Indigo = the agent. Orange = nociception.
   Blue↔red = temperature only. Teal = smell. Slate = vision.
3. **Flat icons on white tokens.** Redraw the icons as flat shapes, the campfire included, in one style,
   so creatures stay readable on any cell temperature and after video compression.

## Context

The frame becomes every training video: an MP4 at 1440×896 on WandB, usually watched shrunk to about
half size, and also pasted as stills into slides. It is drawn in Matplotlib: the figure is built once and
its artists are updated each step. Decisions already made, which this spec takes as fixed:

- **Option A for extended-range senses:** one small diamond map per channel, in a band under the grid view.
- **Observed vs true** for every internal state.
- **No numbers in grid cells.**
- **A fixed temperature scale per config:** vmin and vmax from the config parameters, with setpoint 0 as
  the neutral centre. In the campfire world that is about −28 to +336, and the survivable body band is
  −15 … +15.
- **A new campfire icon.**

Images read at full size (with crops):

- `fig03_frames/step_015.png`
- `fig04_repacking.png`
- `fig05_option_a_channel_maps.png`
- `v1_thermal.png`
- all 14 `assets/*.png` icons

The two figure scripts, `house.py`, and the house style sheet tokens were read for context.

## Ranked critique

### 1. Typography reads as a terminal, not a product (fig03, fig04) — high

- **Three type voices.** The frame mixes three: Pretendard SemiBold in caps (titles), Pretendard
  regular (captions), and **DejaVu Sans Mono** for every value, subtitle and legend ("step 15 / 34",
  "−15 limit", "obs only", "cold −61"). The mono is not a deliberate choice. `house.FONT_MONO` names IBM
  Plex Mono first, which is not installed, so Matplotlib silently falls back to DejaVu Sans Mono. That
  wide, 2000s-era typewriter look is the single strongest "old" signal in the frame.
- **All-caps titles with no letter-spacing.** "INTEROCEPTIVE NOCICEPTION" and "GRID VIEW · 5 × 5 AROUND
  THE AGENT" are cramped and shouty. Caps need tracking, and Matplotlib cannot track, so the fix is
  sentence case, not better caps.
- **Flat hierarchy.** Titles are 13 pt semibold in the secondary ink, so the eye cannot find the primary
  numbers. Values such as 0.85 and −9.68 are the same visual weight as their labels.
- **Proportional digits.** Pretendard's default digits have proportional widths (898 to 1278 units in the
  Regular), so in a video the values would jitter sideways every step. The font does ship a `tnum`
  (tabular figures) feature, but Matplotlib cannot switch OpenType features on.

### 2. Colour: one hue, many meanings; the grid is washed out (fig03) — high

- **Blue carries five meanings.** In one frame it marks the agent (minimap dot), the view window, the
  action badge, the olfaction bars and the active proprioception chip. Green means both satiation and
  food dots. Red means both the lethal body-temperature limits and the hiding-predator dots. This is the
  house-style colour-meaning rule (format register F11) broken inside a single frame.
- **The grid is one flat pale blue with 25 number tags.** Every cell reads "−23". The data-ink is spent
  repeating one number, and the white tag boxes break the surface into noise. (Already decided: remove.)
- **The ramps are generic defaults.** RdBu_r (temperature) and magma_r (fig05) look like a paper appendix.
  magma's orange-red-violet hues also collide with the temperature ramp's red half.
- **The minimap uses one-off colours.** They are Tailwind-like hexes (`#4d7c0f`, `#0891B2`, `#ea580c`)
  that appear nowhere else in the frame.

### 3. Surface and layout feel like a 2012 admin panel (fig03, fig04) — high

- **Boxed grey panels.** The cards are grey fills (`#f1f2f0`) with grey borders on an off-white ground:
  low contrast between card and canvas, but visible borders everywhere. Modern analytics UIs invert this
  to white cards with a hairline border on a slightly darker canvas.
- **Uneven density.** The minimap card has about 150 px of dead space above the map. In fig04's reduced
  variants the right-hand cards stretch to empty height: the Extero nociception card is mostly blank, and
  the Visual bars grow to 400 px for one number. The packer shares out spare height without regard to
  content.
- **"obs only" stamped six times.** Global state is repeated per card. It belongs in one place: the
  observed-vs-true interoception panel.
- **Thermoception floats.** The small cells sit centred in a wide card with no link to the temperature
  legend under the grid.

### 4. Icons do not share a style (all frames) — medium-high

- **At least four rendering styles in one set.** Flat kawaii (cat agent, rabbit), glossy 3D (apple),
  semi-realistic painted (rock, tree) and dark hairy illustration with a warning-sign decal (wolf,
  hiding_predator).
- **Downscaled to 96 px they fall apart.** The wolf becomes a black blot and the warning-sign triangle is
  unreadable. At half-size video the hiding_predator loses its identity entirely.
- **They clash with the UI.** A flat interface with painterly stickers is the most common marker of a
  hobby project in a keynote.
- **Agent variants multiply the style problem.** Crying cat, cat in bush, and so on need a combinatorial
  set of illustrations instead of a composable marker.
- **There is no campfire icon.** The sketch draws an orange circle in its place.

### 5. Data-ink in the sensor pods (fig03) — medium

- Olfaction and visual bars keep full-height grey tracks, so empty channels dominate the pod.
- Collision is five empty grey rectangles whose C U R D L labels sit above rather than in a diamond,
  although collision is a diamond of cells.
- Proprioception chips are set in mono caps.
- The visual pod ("agent cell") shows 1 of 13 cells at vision range 2 (the episode's breakdown is 104 =
  13 cells × 8 channels). Option A replaces it.

### 6. Medium fitness (fig03) — medium

- **Floor text vanishes at half size.** The 11 pt floor renders at about 15 px, which is about 7.6 px at
  half-size playback, where thin mono strokes vanish.
- **Compression attacks fine detail.** Single-pixel borders on grey-on-grey cards, the 1 px limit ticks
  and the 25 cell tags are the details H.264 chroma subsampling eats first.

### fig05 (option A, chosen) — specific notes

- **Encoding right, styling not.**
  - The "smell / FOOD" two-line titles in bold are heavier than the maps.
  - The colour bars are page-wide with 0.05 steps, which is scientific-figure chrome, not dashboard chrome.
  - Terrain in dark grey is the heaviest element, though it is the least informative channel.
  - The agent-cell outline is black, a new meaning for black.
- **Frame fixes:**
  - Per-sense single-hue ramps (teal, slate).
  - Empty cells as a light track so the diamond shape survives.
  - The agent cell outlined in the agent colour.
  - A compact 96 px legend beside each sense title.
  - Labels below maps in sentence case, no channel abbreviations.

### v1_thermal.png (today's production) — for reference

Worse on every axis, so fig03 is a real step forward:

- 30 % of the canvas is empty margin.
- The icons are tiny.
- Text is 8–9 px with overlaps ("OBS: 0.00" printed over the next panel title).

## Spec

Owner of every item: whoever implements the new renderer (`developer`, from the approved
[[RENDERER_LAYOUT_REDESIGN]] plan). The icon set and the frozen font are asset work under `assets/`.

### Canvas theme — light, argued

Light, for three reasons specific to this medium:

1. **The temperature ramp needs a light neutral.** The setpoint colour must read as "nothing to see". On
   a light canvas the neutral midpoint is near-white. On a dark canvas it becomes dark grey, and
   dark-bodied creatures (predator) vanish on setpoint-temperature cells.
2. **Stills go into slides and papers.** The project's pages and paper figures are light, and a light
   frame drops into a white slide without a black rectangle.
3. **Compression.** Coloured thin text on dark ground suffers more visible chroma bleed under H.264 4:2:0
   than dark text on light ground.

The dark-theme case ("keynote stage look") is real but loses on reasons 1 and 2.

**Departure from house style:** the video frame **inverts the surface roles**. Cards are white on a
slightly darker canvas; the house sheet has grey cards on a near-white ground. The page style is unchanged.
This is a frame-specific choice, not a proposal to change the sheet.

### Type

| Role | Font file | Size (px @1440) | Weight | Colour |
|---|---|---|---|---|
| Frame title ("Campfire world") | Dashboard Sans Tab SemiBold | 22 | 600 | ink |
| Step number | Dashboard Sans Tab SemiBold | 26 | 600 | ink; "Step" and "/ 34" 14–16 ink-3 |
| Card title | Dashboard Sans Tab SemiBold | 15 | 600 | ink |
| Card subtitle (e.g. "previous action") | Dashboard Sans Tab Regular | 13 | 400 | ink-3 |
| Row label (state / channel name) | Dashboard Sans Tab Medium | 14 (13 under maps) | 500 | ink / ink-2 |
| Value | Dashboard Sans Tab SemiBold | 18 | 600 | ink |
| Hero value (extero nociception) | Dashboard Sans Tab SemiBold | 30 | 600 | ink |
| Caption, legend ticks | Dashboard Sans Tab Regular | 12 (floor) | 400 | ink-3 |

- **Sizes.** Matplotlib size in pt = px × 72 / dpi (0.72 at dpi 100).
- **Floors.** 14 px for anything a viewer must read during playback, which is 7 px at half size. 12 px
  only for redundant captions and tick labels.
- **Case.** Sentence case everywhere; no all-caps labels (Matplotlib cannot letter-space).
- **No monospace face.**

**Fixed-width digits.** "Dashboard Sans Tab" is Pretendard with its `tnum` glyphs frozen into the
character map. It was built in about 10 lines of fontTools in
`tmp/20260914_101500_design_episode_dashboard/freeze_tnum.py`; all ten digits become 1258 / 1286 / 1314
units wide in Regular / Medium / SemiBold. Values then stop jittering between frames.

- **Why it cannot be called "Pretendard Tab":** the bundled `assets/fonts/pretendard/OFL.txt` states
  "with Reserved Font Name Pretendard". The SIL OFL 1.1 forbids a modified version from using a reserved
  name, so the derived family must carry a name without "Pretendard" in it. The mock-up uses
  "Dashboard Sans Tab"; any other name without the reserved word works.
- **Proposed home:** `assets/fonts/dashboard_sans_tab/DashboardSansTab-{Regular,Medium,SemiBold}.otf`,
  generated once, with a copy of `OFL.txt` and a note saying it is derived from Pretendard.

### Palette

| Name | Hex | Role |
|---|---|---|
| canvas | `#F2F3F0` | frame background (slight green-grey bias, as in house neutrals) |
| card | `#FFFFFF` | card surface |
| line | `#E2E4DF` | card hairline (1 px), dividers |
| track | `#ECEEEA` | empty bar track, inactive chip, zero-reading map cell |
| ink | `#15171C` | titles, values |
| ink-2 | `#4A515C` | labels, inactive chip text |
| ink-3 | `#6F7682` | subtitles, captions, "not observed" (4.6:1 on white) |
| **iris** (accent) | `#5B4BDB` | **agent only**: grid token, minimap dot, view window, action badge text, active proprioception chip, step progress, agent-cell outline in maps |
| iris-soft | `#ECE9FB` | action badge fill |
| state | `#2F3744` | neutral internal-state bars (satiation, nutrition, injury) |
| nociception | `#E8590C` | intero nociception bar, extero nociception bar, collision hit cell |
| food | `#1E9E5A` | food glyph, minimap food |
| predator | `#1F2733` | predator glyph, minimap predator |
| neutral | `#0E7490` | neutral (rabbit) glyph, minimap neutral |
| hiding-predator | `#33503A` body, `#F59E0B` eyes | hiding_predator glyph |
| obstacle rock / bush / tree | `#7D8590`+`#A1A8B1` / `#4F8A34`+`#65A044` / `#2F7A45`+`#7A5634` | terrain glyphs |
| campfire | `#F97316`, `#FB9A3C`, `#FDE68A`, logs `#7C4A2D`/`#935C38`, glow `#FDBA74` @28 % | campfire glyph (fire colours live only inside the glyph) |
| mock-up flag | `#FFF4D6` / `#E9C46A` / `#7A5A00` | the "DESIGN MOCK-UP" chip only — not for production |

**Temperature, diverging** — used for grid cells, minimap tint (75 % alpha), thermoception cells and the
body-temperature gauge, and nothing else.

*The problem it has to solve.* In the campfire world, cells run from about −28 (cold default ground) to
about +336 (fire cells; fires sit at 11–13 × the ground's magnitude). A typical episode peaks near +60,
and the agent survives only −15 … +15 around setpoint 0. A symmetric linear scale over ±336 leaves the
cold world near-white and squeezes the survivable band into about 4 % of the ramp. The scale must also
be fixed per config, not per episode.

*The mapping: a piecewise-linear norm with named anchors, all read from config parameters.* Neither
`TwoSlopeNorm` alone nor a log curve fits. Two slopes still give the hot half one uniform slope, so
+15 … +60, the range that matters behaviourally, gets about 4 % of the ramp. A log or symlog curve has no
anchors a viewer can name, and its legend ticks land at arbitrary values. Anchors do both jobs: each one
is a legend tick and a meaning.

| Anchor (value) | Where it comes from | Ramp position | Colour at anchor |
|---|---|---|---|
| vmin (e.g. −28) | config: coldest possible cell | 0.00 | `#6F9AD6` mid-blue |
| lower body limit (−15) | config: survivable band low | 0.25 | `#C3D6EF` pale blue |
| setpoint (0) | config: temperature setpoint | 0.50 | `#F3F2EE` neutral |
| upper body limit (+15) | config: survivable band high | 0.58 | `#F7DCCB` pale peach |
| warm anchor (+60) | 4 × the upper body limit (rule, not a magic number; ≈ a typical episode peak) | 0.75 | `#E6806A` salmon-red |
| fire anchor (+150) | 10 × the upper body limit, or the fire-ratio × ground magnitude lower bound if the config exposes it | 0.88 | `#B8323A` crimson |
| vmax (e.g. +336) | config: hottest possible cell | 1.00 | `#5E1320` deep oxblood |

- **Implementation:** `matplotlib.colors.FuncNorm((lambda v: np.interp(v, X, Y), lambda y: np.interp(y, Y, X)), vmin, vmax)`
  with X = the anchor values and Y = the ramp positions above, and `LinearSegmentedColormap.from_list`
  over the same positions. Colour stops sit exactly on anchors, so a tick's colour is the anchor's colour.
- **Why these positions.**
  - **Cold half is linear and generous.** The whole cold range is only about 28°, and cold ground is the
    world's default. The cold end therefore stops at mid-blue `#6F9AD6`, so ambient ground is visibly
    "cold" without flooding the grid or drowning the icons. (A first mock-up pass with a deep-blue cold
    end turned the entire grid alarm-blue.)
  - **Survivable band stays pale.** −15 … +15 spans 0.25 … 0.58, about a third of the ramp, and stays
    low-contrast: **lightness means safe for the body; saturation means dangerous.** The band is also
    bracketed on the legend.
  - **Hot tail is compressed in steps that get coarser.** +15 → +60 takes 17 % of the ramp, +60 → +150
    takes 13 %, and +150 → +336 takes 12 %. Differences that matter to the agent near the fire stay
    visible, and fire cells are unmistakable without spending half the ramp on 150–336.
  - **Hue path.** Pale peach → salmon-red → crimson → oxblood. No yellow or orange stops, so the ramp
    never borrows the nociception orange or the campfire's own flame colours. Lightness falls
    monotonically from the setpoint outward on both sides, which also makes the ramp readable in greyscale.
- **Out-of-range values.** Because the bounds come from config parameters, a cell outside them means
  the config bounds are wrong. It is not a value to paint over.
  - **Default, in line with the project's no-fallback rule:** the renderer checks the episode's thermal
    field against vmin / vmax once at build time and raises a clear error naming the cell and the bound.
  - **If the plan owner prefers drawing anyway:** clamp the colour to the end stop, draw a 2 px ink inner
    outline on every clamped cell, give the legend's end-cap triangle a 1.5 px ink outline and a
    "clipped" caption, and log a warning.
  - **Legend end-caps are always present** (the mock-up draws them unoutlined), so the convention is
    visible before it is ever needed.
- **No numbers in grid cells** (decision 3). The legend's anchor ticks are the only temperature numbers
  outside the thermoception and body-temperature readings.

**Sequential, per sense** — each scale fixed per episode (decision 1); zero is the `track` colour, not
the ramp's first stop:

- **Olfaction (teal):** `#EDF7F5` → `#7CCBBD` → `#14907F` → `#0B4F47`.
- **Vision objects (slate):** `#EFF1F4` → `#A3ACBA` → `#556072` → `#1C2330`.
- **Vision terrain (categorical, light):** grass `#DCEBD2`, sand `#EFE4C9`, plain `#E6E4DD`; off-world
  cells white.

**Hue audit:**

- **Blue** means temperature only. **Indigo** means agent only. **Orange** means nociception only.
- **Green** appears as food and as bush/tree terrain. Both read as "vegetation", which is accepted as one
  meaning.
- **Teal** is smell. The neutral glyph `#0E7490` is a deeper cyan-teal, on a white token, never adjacent
  to the smell maps.
- Blue and orange stay distinguishable under the common colour-vision deficiencies.

### Spacing, radii, cards

- **Base unit 8 px.** Outer gutter 24; gap between cards 16; card padding 16.
- **Header** 64 px, no card and no rule (canvas only).
- **Card:** white, 1 px `line` border, radius 12, no drop shadow (shadows smear under compression).
  Title baseline 30 px from card top.
- **Radii:** grid cells 8 (2 px seam of card white between cells, no grid lines); chips 8; bars fully
  rounded (radius = height / 2); map cells 3.
- **Frame layout at 1440×896:**
  - Left column 320 wide: Interoception (496 tall), World minimap below.
  - Centre: grid view card 544×544.
  - Right column: Proprioception (104), then Extero nociception + Collision side by side (150), then
    Thermoception with the shared temperature scale.
  - Sensor band under grid + right column (1056 wide × 216).

### Components

- **Header.**
  - **Left:** world name (22/600), then meta in 14 px ink-2 separated by " · " (seed, policy, view/world size).
  - **Right:** "Step" 14 ink-3, number 26/600, "/ N" 16 ink-3.
  - **Progress:** a 4 px iris progress bar under the step, 132 px wide.
  - **Drop:** "GridWorld" and the bordered bottom rule.

- **Interoception, observed vs true** (decision 2):
  - **Column headers** "Observed" | "True" (12/500 ink-3) over a hairline. Columns start at x+16 and
    x+168, each 136 wide.
  - **Each state is a 76 px row:** the name on its own line (14/500 ink), so long names like
    "Interoceptive nociception" never compete with values. Below it, in each column, the value (18/600)
    and a 6 px bar underneath.
  - **Row order:** satiation, nutrition, injury, interoceptive nociception, body temperature.
  - **Not observed:** the text "not observed" (13/400 ink-3) over an **outlined empty track** (1 px
    `#CDD1CB`, no fill). The shape says "no signal" rather than "zero".
  - **True not recorded:** "not recorded" in the True column, same outlined empty track.
  - **Bar colours:** `state` for satiation / nutrition / injury; `nociception` for interoceptive nociception.
  - **Interoceptive nociception is not a state.** Its right-hand value is the noise-free percept, not a
    hidden internal variable. Keep the column header "True" for the table, but put a right-aligned
    **"noise-free"** qualifier (12/400 ink-3) on that row's True cell, on the value line, so the viewer
    does not read it as a body state. With noise off it equals the observed value, as in the mock-up.
  - **When observed ≠ true** (noise on): keep both bars. Optionally add a 12 px ink-3 "Δ +0.04" right of
    the observed value. Do not tint the difference; the side-by-side bars carry it.
  - **Global note** at the card foot, under a hairline, e.g. "Noise off in this episode, so observed =
    true". This replaces the six "obs only" stamps.

- **Body-temperature gauge.**
  - **Track:** 6 px, spans the lethal band −15…+15, filled with the temperature ramp at 90 % alpha. A 1 px
    ink-3 tick at the setpoint.
  - **Marker:** value shown as a 12 px white dot with a 2 px ink ring.
  - **Text:** value text "−9.7°" (18/600) above; limits named once in the row header ("limits −15 / +15",
    12 ink-3).

- **Bars.**
  - **Size:** 6 px tall, fully rounded; hero bars (extero nociception) 8 px.
  - **Track:** `track`.
  - **Fill floor:** a fill never narrower than its height when > 0, so small values stay visible as a dot.

- **Diamond map cell** (option A band, collision, thermoception):
  - **Shape:** square cells on the Manhattan diamond in `sensor.get_visual_offsets` order.
  - **Olfaction map:** 66 px box (3 cells) at range 1.
  - **Vision map:** 88 px box (5 cells → about 17.6 px cells) at range 2. At ranges 3–4 the same box gives
    12.6 / 9.8 px cells. Below 12 px, switch that row to two lines of maps rather than shrinking.
  - **Cell style:** inset 1.5 px, radius 3.
  - **Zero reading:** `track` fill.
  - **Agent cell:** 2 px iris outline.
  - **Labels:** centred under the map (13/500 ink-2), sentence case, full names, wrapping to two lines
    ("Hiding / predator").
  - **Group header:** "Olfaction" (15/600) + "range 1" (13 ink-3) + a 96×8 px legend strip labelled
    "0 … max" (12 ink-3). A 1 px vertical divider separates the olfaction and vision groups.

- **Legends.**
  - **Temperature:** one shared scale inside the Thermoception card, labelled "Temperature scale, fixed
    for this config".
    - **Strip:** a 12 px gradient strip in *ramp position* (so the compressed hot tail looks compressed),
      with 9 px end-cap triangles.
    - **Ticks:** at the anchors (12 ink-3). Label vmin, −15, 0, the warm anchor and vmax. Draw the upper
      body limit (+15) and the fire anchor as tick marks only, because their labels collide at 280 px strip
      width; the renderer should drop any label whose measured box overlaps its neighbour.
    - **Survivable band:** a 1.2 px ink-2 bracket under the −15 … +15 ticks, labelled "survivable body
      range".
    - **Body marker:** an ink triangle above the strip marking current true body temperature.
    - **Caption:** two lines saying grid cells, thermoception and body temperature all use this scale.
  - **No legend under the grid view.**

- **Last-action badge.** A pill in the grid-view card's title row, right-aligned: 118×28, radius 14,
  `iris-soft` fill, arrow + action name in 14/600 iris, preceded by "Action" (13 ink-3). The same arrow
  is drawn inside the agent token, so the action is readable in the grid itself.

- **Proprioception.** Six chips in one row: 32 px tall, radius 8, `track` fill, 13/500 ink-2 labels in
  sentence case (Up, Right, Down, Left, Rest, Eat). The active chip is iris fill with white 13/600 text.

- **Collision.** A 5-cell diamond of 30 px cells, radius 6, the letter C/U/R/D/L inside each (12/600
  ink-3). A hit fills `nociception` with white letters.

- **Thermoception.** A 5-cell diamond of 46 px cells, radius 8, filled with the temperature ramp at the
  **relative** value (cell − body). Signed integer inside (14/600 ink; switch to white when the fill's
  luminance < 0.45). Numbers are kept here because they are the sense's reading; decision 3 applies to
  grid cells only.

- **Minimap ("World").**
  - **Cells:** 10×10 rounded cells (radius 3, 1 px seam) tinted by the temperature ramp at 75 % alpha.
  - **Obstacles:** rounded squares (56 % of cell) in their glyph colours: rock grey, bush green, campfire
    orange.
  - **Food and creatures:** dots (48–52 %) with a 1.2 px white ring.
  - **Agent:** iris dot (64 %) with a 2 px white ring.
  - **View window:** a 2.2 px iris rounded rectangle.
  - **Placement:** the map sits directly under the title; no dead band.

- **Grid view.**
  - **Size:** 5×5 cells, about 96 px each, filling the card.
  - **Cells:** temperature fill, radius 8, 2 px seams, no numbers.
  - **Creatures and food:** a **white token** (circle, radius 0.34 × cell, 10 % black offset shadow)
    carrying the glyph.
  - **Terrain obstacles** (rock, bush, tree, campfire): drawn flat directly on the cell.
  - **Agent:** always topmost — an iris disc (0.30 × cell) with a 3 px white ring, a 16 % iris halo and a
    white chevron for the last action (dot for Rest/Eat).
  - **Overlap:** agent + bush or agent + food draws the obstacle glyph and places the agent token over it.
    No combinatorial "agent_in_bush" images.

### Icon style guide

**Restyle, do not reuse.** The current set cannot be unified by recolouring. Replace it with a flat set
with these rules:

- **Construction.** Primitives only (circles, ellipses, rounded rectangles, polygons, cubic teardrops),
  so every icon can be drawn as Matplotlib patches at any size or exported once to 1000 px PNG.
- **Colour.** 2–3 flat fills per icon, no outlines, no gradients, no texture, no cast shadows inside the
  icon.
- **Geometry.** 96 px design canvas, glyph within the central 60 % (about 58 px), optical centre slightly
  low for heavy-bottom shapes.
- **Token.** Creatures and food sit on a white token; terrain does not. That split is the one visual rule
  a viewer needs to learn.
- **Faces.** At most two eye dots, no mouths or tears. Expression states (crying agent) are dropped; the
  interoception panel carries state.
- **Current glyphs** (all in `mockup.py`, see `mockup_icon_sheet.png`):
  - **agent:** iris disc with chevron.
  - **food:** two-lobed apple, green, leaf and stem.
  - **predator:** angular wolf head with amber eye slits.
  - **hiding_predator:** dark-green bush cluster with amber eyes.
  - **neutral:** rabbit head with two ears, deep teal.
  - **rock:** two-facet polygon.
  - **bush:** four-circle cluster.
  - **tree:** round crown and trunk.

**Campfire icon spec.** Master canvas 1000×1000 transparent PNG (and a 96 px design grid); unit
k = 0.30 × canvas.

1. **Glow:** a circle of radius 0.95k at centre, `#FDBA74` at 28 % alpha. It is the only translucent
   element and reads as heat on any cell colour.
2. **Logs:** two rounded bars, 1.6k × 0.22k, corner radius 0.11k, crossed at ±18° about a point 0.55k
   below centre. Colours `#7C4A2D` (back) and `#935C38` (front).
3. **Flames:** three nested cubic teardrops sharing an axis, points up.
   - Outer: half-width 0.48k, height 0.95k, `#F97316`.
   - Middle: 0.30k × 0.62k, `#FB9A3C`, offset down 0.10k.
   - Core: 0.15k × 0.34k, `#FDE68A`, offset down 0.18k.
4. **Placement:** no token; drawn flat on its (hot) cell. At +60° the cell ramp is salmon-red, and the
   yellow core and the glow keep it distinct.

Draft master: `tmp/20260914_101500_design_episode_dashboard/campfire_icon_1000.png`.

### Before → after

| Element | Before (fig03) | After |
|---|---|---|
| Surface | grey cards, grey borders, off-white ground | white cards, hairline, green-grey canvas |
| Values | DejaVu Sans Mono (fallback) | Dashboard Sans Tab SemiBold (Pretendard with frozen fixed-width digits) |
| Titles | 13 pt SemiBold CAPS, ink-2 | 15 px SemiBold sentence case, ink |
| "obs only" | stamped on 6 cards | one note in the interoception card |
| Grid cells | flat pale blue + 25 number tags | temperature fill on a fixed per-config piecewise scale, no numbers, 2 px seams |
| Icons | four illustration styles, agent variants | one flat set, tokens for creatures, composable agent marker |
| Agent colour | blue shared with 4 other meanings | iris, exclusive |
| Olfaction / vision | agent-cell bars | option A diamond maps in a bottom band, teal / slate ramps |
| Interoception | satiation + intero nociception + body temp | 5 states × observed / true, "not observed" as outlined track |
| Temperature legend | under grid, RdBu_r ±61 per episode | one shared scale in Thermoception, fixed per config (vmin … vmax), anchors ticked, survivable band bracketed |
| Collision | 5 grey rectangles in a row | 5-cell diamond, nociception fill on hit |

## Mock-up

`tmp/20260914_101500_design_episode_dashboard/`:

- `mockup_frame_step015.png` — full 1440×896 frame, labelled "DESIGN MOCK-UP" in the header.
- `mockup_frame_step015_half.png` — the same at 720×448, to judge half-size playback.
- `mockup_icon_sheet.png` — the flat icon set incl. campfire.
- `campfire_icon_1000.png` — campfire master.
- `mockup.py`, `freeze_tnum.py`, `fonts/` — throwaway scripts and the frozen-digit fonts.

Drawn from real data: step 15 of the recorded campfire-world episode
(`renderer_layout_redesign/data/episode.json`, seed 10, olfaction range 1, vision range 2). What it does
**not** show, because the data at this step does not contain it:

- **Observed and true are equal:** noise is off in this episode, and the frame says so.
- **No campfire in the 5×5 view:** the campfire never enters the view in this episode. It appears in the
  minimap (orange square) and in the icon sheet.
- **The vision object maps are empty:** nothing but terrain is within range 2 at this step.
- **The temperature bounds are example values:** the mock-up uses −28 / +336, the campfire-world bounds
  reported by the plan review. They were not read from the config file; the renderer must read them from
  the config parameters.
- **The mock-up is one static figure:** it does not run the per-step artist-update loop or the text
  audit. Sizes were checked by eye at full and half size, and one scripted check confirmed no ink
  outside the sensor band's card.

## Open issues for the plan owner

1. **Cold ground reads as "cold" on every frame.** The cold side has only about 28° of range and cold
   ground is the default, so almost every cell sits near the cold end. The spec caps the cold end at
   mid-blue so that is calm rather than alarming. The two derived anchors (warm = 4 × upper body limit,
   fire = 10 × upper body limit) are design rules the plan owner should confirm, or replace with config
   parameters if the config exposes better ones.
2. **Out-of-range policy needs a call.** Raising at build time (recommended, matches the no-fallback
   rule) versus clamp-and-flag. The spec gives both.
3. **The frozen-digit font is an asset addition.** Vendoring `DashboardSansTab-*.otf` under
   `assets/fonts/` needs a one-line house-style note (`house.FONT_MONO` would then be unused in the
   renderer). The family name must not contain "Pretendard" (Reserved Font Name in `OFL.txt`).
3. **The icon redraw is a separate asset task.** It is not blocked by the renderer; the renderer can take
   glyph functions or PNGs exported from them.
4. **The house style sheet is unchanged.** This review departs from it only for the video frame (surface
   inversion, no mono). If the same look is wanted for artifact pages, that is a proposal to change the
   sheet.

---

## Second pass — 2026-09-14

> **Reviewed by**: visual-design-reviewer
> **Object**: the implemented sketch (`dashboard_style.py`, `fig03_proposed_dashboard.py`,
> `fig05_extended_encodings.py`) as rendered.

### Verdict (second pass)

**It passes the big-tech-presentation bar, with two changes to make before the frame goes into a
keynote.** The first-pass problems are fixed on screen: one typeface with fixed-width digits, sentence
case, white cards, one colour per meaning, a single flat icon set with a real campfire, observed vs true
side by side, and option A maps. It now reads as a product analytics view. Two things still weaken it.
First, the grid view, the most important element, is a solid periwinkle slab, and the indigo agent
sits on it with weak contrast. That comes from the cold end of this review's own ramp. Second, the
temperature caption says "one scale", but the thermoception cells show a different quantity (cell
minus body).

### What was checked

- **Frames** `fig03_frames/step_000.png`, `step_015.png` and `step_034.png` (1440×896, RGB), each at full
  size, at 720×448, and in crops of the grid view, sensor band, minimap and step counter.
- **Other figures:** `fig04_repacking.png` and `fig05_option_a_channel_maps.png`.
- **Icons:** all 9 `assets/dashboard_icons/*.png` and `assets/campfire.png`, composited at 58 px on a
  cold cell (`#92B2E0`) and a fire cell (`#B8323A`), and at 24 px. `fig08_icon_set.png` does not exist.
- **Sampled pixels:** grid cell `#92B2E0`–`#95B5E1`, minimap cold cell `#ACC5E7`, off-world cell
  `#FFFFFF`.
- **Crude mock-up** (pixel recolour of step 15, not a re-render):
  `tmp/20260914_101500_design_episode_dashboard/mock_pass2_{lighter_cold_step015,grid_crop,half}.png`.

**Spec items now met:** Dashboard Sans Tab loads and raises if missing. Digits hold their width across
steps 0/15/34. Card radius 12, 1 px hairline, no shadows. Iris is used only for the agent. Nociception
orange is used only on nociception bars. Teal and slate map ramps are in place. The agent-cell outline
is iris. The "not observed" outlined track is in place, with a single noise note. The gauge has a
marker ring. The action pill has a matching chevron in the token. The thermoception luminance text
switch works (white on −23, ink on −13). The legend has end caps, anchor ticks, a bracketed survivable
band and a body marker. There are no numbers in grid cells. The agent token is composable. At half
size every must-read label is still legible (smallest must-read text ≈ 7 px).

### Remaining issues, ranked

| # | Impact | What the viewer sees | Fix (component, value) | Owner |
|---|---|---|---|---|
| 1 | High | **The grid view is a solid mid-blue slab.** Cold ground (−23) is the default for almost every cell, and the ramp maps it to `#92B2E0`. The primary element reads "alarm cold" on every frame. The iris agent disc sits on a neighbouring hue at **2.8 : 1** contrast, and the grey rock glyph at **1.7 : 1**. The minimap view window has the same problem. This is a defect of the first-pass spec, not of the implementation. | **Temperature ramp, cold stops:** vmin `#6F9AD6` → **`#9FBCE6`**; lower body limit (−15) `#C3D6EF` → **`#D3E1F2`**. Positions unchanged. A −23 cell becomes ≈ `#B3CAEB`, and iris-on-cell rises to **3.9 : 1**. Cold stays visibly blue, but calm. Also darken the **rock base facet** `#7D8590` → **`#6B7380`** (≈ 2.6 : 1 on the new cell). The recolour mock-up shows the effect. Re-check that the thermoception text switch still picks a readable colour on the new cold fills. | developer (`dashboard_style.py` anchors); spec amended here |
| 2 | Medium-high | **The caption overstates "one scale".** The caption says "Grid cells, thermoception and body temperature all use this one scale", but thermoception cells are coloured by *cell minus body*. At step 15 the agent's own grid cell is mid-blue (−23) while the centre thermoception cell is pale (−13). An audience will ask why the same place has two colours. | **Thermoception legend caption** (2 lines, 12 px ink-3): "Grid cells and body temperature: absolute. Thermoception: cell minus body. Same colours; 0 is neutral." Keep the card subtitle "cell minus body, °". | developer |
| 3 | Medium | **Minimap: hiding predator and predator dots look identical.** `#33503A` vs `#1F2733` is 1.68 : 1; both read as "dark dot" at 12 px and at half size. | **Minimap hiding-predator dot:** keep the `#33503A` fill and add one centred **amber `#F59E0B` pip at 34 % of dot diameter**, echoing the glyph's eyes. Predator stays plain. | developer |
| 4 | Medium | **"Animal A" / "Animal B" smell labels are opaque.** They come from `sensor.py`'s `'AN-A'`, `'AN-B'` chemical-channel labels. A viewer cannot tell which animal each one is, while vision names its channels Predator / Hiding predator / Neutral. | **Olfaction map labels:** take the names from what those `res_property` axes encode (e.g. which creature types load on each). Do not invent names. If no creature-level meaning exists, label them "Scent 2" and "Scent 3" and explain in the plan's glossary. | experiment-designer confirms meaning; developer applies |
| 5 | Medium-low | **Header meta says "sensor ranges set in memory".** This is implementation jargon, shown whenever the episode is synthetic. | **Header meta:** "sensor ranges overridden for this sketch". Production frames (never synthetic) omit it. | developer |
| 6 | Low | **The step progress track is invisible.** `track` `#ECEEEA` on canvas `#F2F3F0` is ≈ 1.05 : 1, so at step 0 the bar reads as a stray iris dot under the header. | **Header progress track:** `#D9DCD5` (canvas-only use; cards keep `track`). | developer |
| 7 | Low | **Interoception is labelled twice.** The "observed vs true" card subtitle repeats the "Observed / True" column headers directly under it. | **Interoception card subtitle:** remove. Leave the right side of the title row empty. | developer |
| 8 | Low | **The sensor band is airy.** Maps (≈ 88 px) sit in a 256 px card, with ≈ 55 px of empty space above and below the map row. The band is width-bound (label width sets map pitch), so the maps cannot grow. | **Band height:** 216 (spec), or keep 256 and accept. Do not enlarge the maps. | developer, optional |
| 9 | Low | **fig05's range-4 row draws ≈ 10 px cells** that the production renderer (12 px floor) would refuse, so the figure promises a layout that cannot ship. | **fig05:** use the same 12 px floor. If range 4 falls below it, draw that row as the two-line wrap the spec describes, or caption it "below the renderer's 12 px floor". | developer |
| 10 | Low | **The tree trunk nearly vanishes at 24 px** (half-size minimap and grid). | **Tree glyph:** trunk width ≥ 0.14 k, with the crown lowered so the trunk shows ≈ 0.25 k. | asset author |

### Implementer departures

| Departure | Verdict | Note |
|---|---|---|
| Vision channel 6 labelled **"Obstacle"** (rock, bush, campfire share it) | **Accept** | More truthful than "Rock". Cross-sense reading holds: smell has a separate Bush channel, and vision does not. |
| **2 px grid seams** | **Accept** | Matches the spec for the grid. The minimap uses ≈ 2 px against a spec of 1 px, which is also fine: it survives downscaling better. |
| **Off-world terrain cells outlined** | **Accept, adjust colour** | A white cell on a white card needs an outline. The outline uses `line` `#E2E4DF` and is barely visible at half size. Use **`#CDD1CB` 1 px**, the same outline as the "not observed" track, so "no signal" has one look everywhere. |
| **Unused column space left as canvas** (fig04 variants 2 and 3) | **Accept** | A clean void at the bottom-right reads as "nothing more here". Stretched, mostly empty cards read as a broken layout, which was the first-pass complaint. The layout is fixed per config, so the viewer never sees it jump. |
| **Vision maps below 12 px raise instead of wrapping** | **Accept for the sketch; conditional for production** | Raising fits the no-fallback rule. But it means a vision-range-4 config cannot produce a video at all. The production plan must implement the two-line wrap (or a wider band) before any range-4 config is recorded. |
| **Frames kept RGB** (no palette quantisation) | **Accept** | H.264 converts to YUV 4:2:0 anyway. Quantising shifts the ramp and glyph colours for no gain. |
| **Temperature bounds −28 … +336, anchors −28 / −15 / 0 / +15 / +60 / +150 / +336** | **Accept** | Matches the spec. Only the two cold-stop *colours* change (issue 1). Positions and anchor rules stay. |

### Icons

The set now shares one flat language: 2–3 fills, no outlines, white tokens for creatures and food, and
terrain drawn directly on the cell. It holds on both cold and fire cells. The campfire's 28 % glow still
separates it from a crimson cell. The wolf, hiding predator and rabbit are identifiable at 24 px. The
only remaining note is issue 10 (tree trunk).
