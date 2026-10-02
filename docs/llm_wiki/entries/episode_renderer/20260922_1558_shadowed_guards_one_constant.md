---
id: 20260922_1558_shadowed_guards_one_constant
date: 2026-09-22
time: "15:58"
folder: episode_renderer
tags: [learned_lesson, design, decision, testing]
summary: "Removing the renderer's legibility floor changed nothing, because the layout registry declared panel width from the same 10px constant and refused at exactly the same sensor ranges; two guards computed from one number shadow each other."
related: ["20260919_1316_two_modules_one_geometry_drift", "20260922_1559_six_more_checks_that_cannot_fail"]
relations: ["extends:20260919_1316_two_modules_one_geometry_drift", "see_also:20260922_1559_six_more_checks_that_cannot_fail"]
session_origin: claude_code
session_label: "renderer display + retirement step 1"
importance: high
status: settled
valid_until: null
confidence: high
supersedes: []
raw_source: claude_data/.claude/projects/-media-nas01-projects-Interoceptive-AI-grid-world-pain/14318db1-bd0b-4e8c-a423-e4d1d64d2180.jsonl
raw_completeness: full
---

# Two guards computed from one constant shadow each other — removing the visible one changed nothing

## Key conclusion

The user asked for an oversized sensor range to DRAW SMALL rather than refuse to
render. Removing the painter's `if cs < 10: raise` floor looked like the whole
job and accomplished nothing measurable: the layout registry independently
declared a sense panel's width as `slots x (2r+1) x MAP_CELL_MIN_PX`, using the
SAME 10 px constant, so the packer refused at exactly the ranges the painter used
to. The refusal only disappeared once the DECLARATION stopped depending on the
sensor range. **A guard removed from one layer is not a guard removed, when a
second layer computes the same threshold from the same number.**

## Evidence, measurements, facts

- **Before and after the floor removal, the boundary did not move.** A probe
  across declared ranges 1-12 under both slot rules refused from **range 4**
  (conventional slots) and **range 5** (the lowered vision slots) in both
  states. Same numbers, different error message.
- **The two sites**: `painters.build_channel_maps` raised on `cs < 10`;
  `panels._span` returned `n_maps * cells * MAP_CELL_MIN_PX + gaps + 2*PAD` with
  `cells = 2r + 1`, and `panels._map_h` returned `(2r+1) * MAP_CELL_MIN_PX`.
  Both sides of the "disagreement" agreed, which is precisely why the first fix
  was invisible.
- **The fix that worked**: make both declarations range-independent. The panel
  asks for a fixed size; the painter divides whatever it is granted by however
  many squares the range needs. Re-probed 1-12: the packer grants at **every**
  range under both slot rules, nothing refuses anywhere.
- **Resulting sizes**, measured: vision holds a 158 px block with squares
  52.7 / 31.6 / 22.6 / 14.4 / 9.3 / 6.3 px at ranges 1 / 2 / 3 / 5 / 8 / 12;
  olfaction holds 92.8 px with 30.9 / 18.6 / 13.3 px at ranges 1 / 2 / 3.
- **A second-order consequence, measured rather than assumed.** With nothing
  refusing, the legacy eight-map case at range 3 packs cleanly — so
  `pack_or_explain`'s `except LayoutOverflowError` branch became unreachable.
  Had the replacement warning been written there (the obvious place), it would
  never have fired and the capability would have been reported as delivered.
- **Where the warning actually went**: `labels.panel_map_slots`, the one function
  that already knows both numbers and already warns for configured runs. Call
  volume checked before worrying about log noise: **4 calls per episode, 0 per
  frame** — the layout is computed once per episode. A planned de-duplication
  was abandoned as unnecessary.

## Decisions and actions

- `_span` and `_map_h` are range-independent; `MAP_CELL_MIN_PX` keeps its value
  but changes meaning from "floor anything enforces" to "nominal size the panel
  asks for", and its comment says so.
- **Warn, never refuse** (user decision). The message that taught the reader what
  to do about a pre-channel-names recording survives verbatim; only its delivery
  moved from `raise` to `logger.warning`.
- `pack_or_explain` is kept — `episode.py` calls it, and the packer can still
  refuse for reasons unrelated to sensor range (a window too wide to draw, a
  column that cannot fit its cards), which must not be swallowed. Its docstring
  was rewritten so it stops describing a refusal it no longer performs.
- **A test was re-aimed rather than deleted.** `test_the_declared_minimum_is_
  exactly_what_the_painter_needs` asserted `declared == needed`, which was the
  guard against a real outage. Once neither side depended on the range that
  equality stopped carrying information — it would go red on harmless changes and
  green on real ones. It now asserts the two properties that still matter: the
  declaration always fits inside the band's grant, and it does not vary with the
  range.
- Orphans the change created were removed: `map_plan_len` (its only caller was
  the deleted `except` branch) and an unused `LayoutOverflowError` import.

## Open questions and follow-ups

- The height twin recorded in `_map_h` (the declaration under-stating the
  painter's real demand by 36 px at every range) is now harmless for a NEW
  reason — nothing refuses on it — rather than the old one, which was that
  `MIN_BAND_H` happened to exceed it. The note in the source says to read it as
  history, not as a live hazard.
- Nothing now prevents a very wide range drawing a 3.7 px square, which is a grey
  smear rather than a map. The user accepted this explicitly: conventional
  ranges are small, and they will ask for a fix if a real config ever needs one.

## References

- Commits: `c9f7e958` (painter floor removed — the change that did nothing),
  `52320023` (declarations made range-independent — the change that worked).
- Source: `src/environment/dashboard/panels.py` (`_span`, `_map_h`,
  `pack_or_explain`), `src/environment/dashboard/labels.py`
  (`panel_map_slots`, the legacy warning).
- [[20260919_1316_two_modules_one_geometry_drift|extends]] — that entry records
  two modules DISAGREEING about one count, and the fix was to give them a single
  source of truth. This one is the mirror image: two guards AGREEING on one
  constant, where the agreement is what hid the second guard. The same pair of
  modules, the opposite failure.
- [[20260922_1559_six_more_checks_that_cannot_fail|see_also]] — the probe that
  first reported "no refusal at any range" was measuring the painter only, not
  the layout, and is one of that entry's six.
- Raw conversation: synced via `./sync-agent-data.sh claude push`. To read on
  another node: `./sync-agent-data.sh claude pull`, then either
  `claude --resume 14318db1-bd0b-4e8c-a423-e4d1d64d2180` or
  `python scripts/claude/claude_jsonl_to_md.py <jsonl> /tmp/<id>.md`.

<!-- BACKLINKS — auto-generated by scripts/regen_wiki_graph.py; do not edit -->
## Backlinks
- [[20260922_1559_six_more_checks_that_cannot_fail]] (episode_renderer, 2026-09-22) — Six checks in one session could not report what they were built to report, each 
<!-- END BACKLINKS -->
