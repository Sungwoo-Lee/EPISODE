---
id: 20260922_1600_vision_slots_legibility_over_anchor
date: 2026-09-22
time: "16:00"
folder: episode_renderer
tags: [design, decision, tradeoff]
summary: "Vision's panel slot count was lowered from six to three so its map squares double, deliberately breaking the rule that a panel's slot count equals what a reference world draws; olfaction keeps its anchor."
related: ["20260919_1316_two_modules_one_geometry_drift"]
relations: ["extends:20260919_1316_two_modules_one_geometry_drift"]
session_origin: claude_code
session_label: "renderer display + retirement step 1"
importance: medium
status: settled
valid_until: null
confidence: high
supersedes: []
raw_source: claude_data/.claude/projects/-media-nas01-projects-Interoceptive-AI-grid-world-pain/14318db1-bd0b-4e8c-a423-e4d1d64d2180.jsonl
raw_completeness: full
---

# Vision's slot count traded its anchoring rule for legible squares, deliberately

## Key conclusion

A sense panel is half the sensor strip divided into a fixed number of equal
slots, and a map can never be wider than its slot. At six slots vision drew
**15.3 px** squares inside a panel whose height allowed **31.6 px**, while four
of its six slots sat permanently blank under the current one-channel
configuration. Lowering vision to **three** slots makes it height-bound instead
of width-bound and doubles the square. The cost is real and was accepted with
eyes open: the rule that *a panel's slot count equals the map count a reference
world draws* no longer holds for vision.

## Evidence, measurements, facts

- **The mechanism**: `box = min(slot_width, panel_height_room)`. Vision's slot
  was 76.3 px against 158 px of height room, so width bound it. Olfaction, with
  five maps in five slots, is width-bound at 92.8 px and is NOT changed by this.
- **Measured, and it changed the decision**: vision renders **identically at 1, 2
  and 3 slots**, because `box` lands on the height room in all three cases. The
  slot count therefore has no visible effect at the current configuration, and
  **3 was chosen as the most conservative value that achieves the effect** rather
  than for any appearance difference. An earlier claim of mine that the constant
  "gets the size right and the position wrong" was wrong — it came from comparing
  against a mock-up that centred a single slot, not from comparing the production
  renders to each other.
- **Rejected: divide by the LIVE map count.** Produces an identical picture, but
  reintroduces exactly the count-dependent sizing `labels.py` documents as what
  "makes two runs incomparable" — two arms of one study would draw
  differently-sized maps — and needs matching care for legacy recordings sized
  `max(slots, drawn)`, which would otherwise overflow every recording on disk.
- **Rejected: re-proportion the band by demand** (olfaction 814 px, vision
  158 px, both height-bound). This is the better outcome on the merits — BOTH
  senses' squares grow, olfaction's roughly doubling — and it preserves the
  anchor. It was set aside for cost: the band divider and the sense headings do
  not move with the panels, so mock-ups showed olfaction's later channels
  crossing the divider and vision's colour ramp clipped at the card edge. Fixing
  that means changing `layout.py`'s panel carving, not just the painter.
- **An earlier suggestion of mine was wrong and would have made things worse**:
  wrapping olfaction's five channels into two rows. Two rows inside 158 px of
  vertical room gives 75 px per row, LESS than the 92.8 px olfaction already
  gets. It would have been a regression, and it would have been built if the
  user had said yes.
- **Five tests asserted the old constant in a file that was never searched.** The
  change was committed against three suites judged to be the blast radius; the
  fifth file left the branch red.

## Decisions and actions

- `PANEL_MAP_SLOTS["Visual"]`: 6 -> 3. Olfaction unchanged at 5 and still
  anchored to its reference (five channels, five maps, five slots).
- **The design document gets a dated amendment, not an edit.** It records a
  decision taken on 2026-09-19 with its reasons; a later decision does not make
  the earlier one never have happened. The amendment names the cost and the
  alternatives the user was shown.
- **The anchoring test was rewritten, not retuned.** It now asserts olfaction's
  anchor holds, vision's constant is 3, and vision's constant is **strictly
  below** its reference count — so the divergence cannot widen, or be quietly
  undone, without failing.

## Open questions and follow-ups

- **The bill falls due at eight vision channels.** A full eight-channel world
  draws six maps into three slots, so three are drawn past the panel edge. That
  is permitted by the no-ceiling decision of 2026-09-19 and the existing warning
  names both numbers, so it is visible rather than silent — but a return to
  eight-channel vision makes the strip look wrong.
- Re-proportioning the band remains the better long-term answer and is not
  blocked by this change; it would restore the anchor and enlarge olfaction too.

## References

- Commits: `5364ad60` (the constant), `385dc052` (the five retuned pins, the
  rewritten anchoring test, and the design-doc amendment).
- Source: `src/environment/dashboard/labels.py` (`PANEL_MAP_SLOTS` and its
  rationale comment).
- Plan: `docs/develop/active/refactors/DASHBOARD_CHANNEL_NAMES_FROM_CONFIG.md`
  — the 2026-09-22 amendment at the end supersedes two passages above it, for
  vision only.
- [[20260919_1316_two_modules_one_geometry_drift|extends]] — the same pair of
  modules and the same constant family; that entry fixed a COUNT mismatch
  between them, this one deliberately introduces a divergence and pins it.
- Raw conversation: synced via `./sync-agent-data.sh claude push`. To read on
  another node: `./sync-agent-data.sh claude pull`, then either
  `claude --resume 14318db1-bd0b-4e8c-a423-e4d1d64d2180` or
  `python scripts/claude/claude_jsonl_to_md.py <jsonl> /tmp/<id>.md`.

<!-- BACKLINKS — auto-generated by scripts/regen_wiki_graph.py; do not edit -->
## Backlinks
- _no inbound links yet_
<!-- END BACKLINKS -->
