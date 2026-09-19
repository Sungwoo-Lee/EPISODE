---
id: 20260919_1316_two_modules_one_geometry_drift
date: 2026-09-19
time: "13:16"
folder: episode_renderer
tags: [learned_lesson, design, testing]
summary: "The dashboard's layout registry and its painter each computed the sensor band's geometry independently and drifted apart, so the packer refused frames the painter draws comfortably; the fix was to make the painter the single source of truth."
headline: "Two modules computing one geometry drift: the registry demanded width for 8 maps where the painter draws 6"
related: ["20260919_1315_eval_videos_moved_to_v2_renderer", "20260919_1317_checks_that_cannot_fail"]
session_origin: claude_code
session_label: "eval renderer switchover (v4.0)"
importance: high
status: settled
valid_until: null
confidence: high
supersedes: []
raw_source: none
raw_completeness: none
---

# Two modules computing one geometry will drift — the band declared a width its painter never drew at

## Key conclusion

`panels.py` (the layout registry, which declares how much room a panel needs) and
`painters.py` (which actually draws it) each computed the sensor band's geometry from
their own constants. They disagreed on three counts at once, so the packer **refused to
render any world with vision at range 3** — a layout the painter would have drawn with
room to spare. The fix was not to change the allocator, the canvas, or the legibility
floor, but to make the painter the single source of truth: import its constant, and ask
its `map_plan` for the map count instead of recomputing one.

## Evidence, measurements, facts

- **The three disagreements**, all in `_span` / `_visual_min_size`:
  1. **Map count** — the registry used `ctx.visual_vector_size` = **8**; the painter draws
     `len(map_plan(...))` = **6**, because the three terrain channels merge into one
     categorical map when the codes are the standard eight in standard order
     (`visual_labels(8) == ('GRS','SND','PLN','FOD','HPR','PRD','RCK','NEU')`).
  2. **Gap** — registry `MAP_GAP_PX = 8` against the painter's `MAP_GAP = 6`.
  3. **Padding** — the registry omitted the `2 * PAD` the packer removes before the painter
     sees the width (`episode.py:465`, `cw = child.w - 2 * PAD`).
- **Net effect, both directions at once.** Vision **over**-declared 616 px against a true
  482 px, so the packer refused. The same missing padding term **under**-declared olfaction
  182 px against 206 px, where the painter itself raised
  `its map squares would be 8.4px across (floor 10px)`. Two faults, one symptom.
- **The refusal was never about space.** At the existing equal split the vision panel gets
  520 px, the painter receives 488 after padding, and produces **10.90 px cells** — above
  its own 10 px floor. Range 3 was always drawable.
- **Three wrong diagnoses preceded the right one**, each of which sounded principled:
  (a) the equal-width split in `layout.py` was blamed, and a minimum-first allocator was
  built against that theory — it passed 18 unit tests and **regressed a working range-2
  config end to end** (reverted, never committed); (b) the declared minimums were blamed in
  the wrong direction; (c) it was attributed to a deliberate legibility ceiling, which the
  redesign plan's own §D7.6 wording supported.
- **What actually settled it was counting maps in an approved figure.** Figure 5 of the
  published renderer-redesign artifact shows vision as six maps (Terrain, Food, Hiding
  predator, Predator, Obstacle, Neutral) and had done since the design round. The registry
  was computing for eight. The evidence pre-dated every theory about it.
- **Post-fix declarations**: olfaction 206 / 306 / 406 px and vision 242 / 362 / 482 px at
  ranges 1 / 2 / 3; at range 3 the pair totals 704 px in a 1056 px band. Verified by
  rendering, not only by test: 33-frame and 22-frame videos at vision 3 and 2.

## Decisions and actions

- **Width fixed structurally, not numerically** (`4b6f7196`): `MAP_GAP_PX` became one
  constant the painter imports, and `map_plan` moved to `labels.py` so the registry can ask
  for the map count without importing Matplotlib. The width half cannot drift apart again.
- **The height twin was found and deliberately left unfixed** (`e5925528`): the painter
  needs `98 + (2r+1)·10` while the registry declares `46 + (2r+1)·10 + 16` — 36 px
  understated at every range, masked by `MIN_BAND_H = 200`, **first biting at sensor
  range 5**. Its fix reflows the band for both senses and needs its own render proof.
- Both halves recorded in `KNOWN_BUGS.md` (`2f94e64a`, `e5925528`), the fixed one carrying
  the wrong-diagnosis history so the next reader meets the method rather than the theory.

## Open questions and follow-ups

- The height twin is open. The fix shape its sibling proved — make the painter the single
  source of truth — is available to copy.
- The renderer is px-absolute throughout (`CANVAS_W`, `LEFT_W`, `PAD`, `MAP_CELL_MIN_PX`,
  and text sized via `fontsize * dpi / 72`). Raising `dpi` alone changes nothing, because
  `figsize` is `CANVAS_W / dpi`; raising the canvas yields more empty space rather than
  larger components. A ratio-based layout, or one global `SCALE` multiplying every
  constant, is the lever if larger sense maps are ever wanted.

## References

- Commits: `4b6f7196` (fix + regression test `tests/env/test_dashboard_band_span.py`),
  `2f94e64a` (fixed row), `e5925528` (latent height twin).
- Figure 5: `docs/develop/active/refactors/renderer_layout_redesign/figures/fig05_option_a_channel_maps.png`
- Related: [[20260919_1315_eval_videos_moved_to_v2_renderer]], [[20260919_1317_checks_that_cannot_fail]]
