---
title: "Sensor channel names come from config, and sense panels get a fixed size"
topic: refactors
status: active
created: 2026-09-19
last_updated: 2026-09-19
---

# Sensor channel names come from config, and sense panels get a fixed size

> **Status**: PLANNED — not implemented. **One question is open and blocks nothing else:**
> §D4c — for vision, the accepted "silent overflow" turns out to mean the extra channels
> **disappear** rather than visibly spill over, which is not what was agreed to. It is with
> the user; CP5b renders both cases so the call is made against pictures.
>
> Carries four user decisions taken 2026-09-19: no recording-format version bump (§Q1); no
> channel ceiling; extra maps overflow the panel rather than being refused, now with a
> warning that names both numbers (§D4b); pre-change checkpoints cannot be re-recorded until
> the saved-config compatibility work lands, with no fallback default (§D7); and legacy
> recordings at vision range ≥ 3 are declared unrenderable with a message that points at
> re-recording (§D5b).
>
> Two `plan-reviewer` passes, both **NOT READY**. Findings and their disposition are tabled in
> "Review disposition" below. Note that the first pass reviewed a draft that still had a
> channel ceiling, and parts of the second pass reviewed a snapshot taken mid-revision — read
> both in that light rather than as descriptions of the current text.
> **Opened**: 2026-09-19
> **Related**: [[RENDERER_LAYOUT_REDESIGN]] (the renderer this changes), [[EVAL_RENDERER_SWITCHOVER]] (which made it production), [[SAVED_RUN_CONFIG_COMPAT]] (why new mandatory keys are expensive)

---

## Context

The episode video the project renders after an evaluation run draws one small map per
**sensor channel** — the agent's five smell components, its eight vision components — and
writes each channel's name under its map ("Food", "Predator", "Grass"). Those names are
currently a **hardcoded table inside the renderer's own source**, in
`src/environment/dashboard/labels.py`. This plan moves them into the environment config
file, so the user can rename a channel by editing YAML instead of editing Python, and
**deletes the hardcoded tables entirely** so there is only ever one place a channel's name
comes from.

Two further changes travel with it, because they are the same decision seen from different
sides:

1. **Sense panels get a fixed size.** How many channels each sense has is a deliberate
   experimental knob in this project — one study is currently lowering vision from eight
   channels to one, because an agent with single-channel vision showed more
   internal-state-dependent hiding. Today the panel's width is computed from however many
   channels the run actually has, so a one-channel run draws a differently-shaped panel
   than an eight-channel one. From now on each sense's panel is sized for a **conventional
   size** — the number of maps today's world draws, as a named constant in code — and a run
   using fewer channels simply leaves blank space. The blank space is intended and must not
   be "fixed" later by someone who reads it as a layout bug. There is **no ceiling on the
   channel count**: a run with more channels than the panel has slots draws its extra maps
   **past the panel edge**, silently, and the user accepted that cost in preference to any
   limit (§D4b).
2. **The vision panel's "Terrain" merge becomes config-driven.** Vision's first three
   channels (grass, sand, plain) are drawn as *one* map rather than three, because a square
   is exactly one of the three. Which channels merge, and what the merged map is called, is
   currently hardcoded. It becomes a **named group of channel indices** in the config
   (name "Terrain", channels [0, 1, 2]). A group naming a channel that does not exist must
   fail when the config loads, not quietly change the picture when the video renders.

Recordings made **before** this change carry no names, and will render with positional
names — "Channel 0", "Channel 1" — rather than falling back to a built-in table or refusing
to draw. After the change lands, the saved render-audit fixtures are re-recorded so audit
frames and the published figures show real names again.

**Why "delete the tables" is the point, not a side-effect.** The user's reason, in their
words: *"I'm worry about any potential quiet mistake."* A name that exists in two places is
a name that can disagree with itself, and the renderer lost exactly that bet the day before
this plan was written: the panel-width bug fixed in commit `4b6f7196` was two modules
holding two different answers to one question (how many maps vision draws), and every video
failed to render. That bug was about a *count*, not a name — but the shape is identical, and
a display name that silently disagrees with the channel it labels is worse, because nothing
crashes.

---

## Analysis

Everything in this section was measured on the working tree at 2026-09-19, not inferred.

### A1. The name tables, and who uses them

`src/environment/dashboard/labels.py` (207 lines) holds every table. **No module outside
the `dashboard` package imports any of them**, and every consumer of the raw tables lives in
`labels.py` itself:

| Symbol | Line | What it is |
|---|---|---|
| `OLFACTORY_LABELS` | 45 | internal short codes (`FOOD`, `AN-A`, …) |
| `OLFACTORY_LONG` | 47 | display names |
| `OLFACTORY_PARTS` | 62 | name/qualifier pairs, **derived at import** by splitting `OLFACTORY_LONG` on `" ("` |
| `VISUAL_LABELS_V8` | 71 | internal short codes |
| `VISUAL_LONG` | 82 | display names |
| `SUPERSEDED_VISUAL_LABELS` | 95 | see A2 — dead |
| `_STANDARD_VISUAL_WIDTH` | 97 | `8` |
| `TERRAIN_CHANNELS` | 173 | `("GRS","SND","PLN")`, read only at line 199 |

The package's public surface (`dashboard/__init__.py:36`, `__all__` at 98–104) exports
`channel_labels`, `olfactory_labels`, `visual_labels`. Outside the package, the only importer
of any of them is **one test**, `tests/env/test_dashboard_band_span.py:54`
(`channel_labels`).

### A2. Three corrections to the brief this plan was commissioned from

1. **`SUPERSEDED_VISUAL_LABELS` is not kept alive by a test — there is no such test.** The
   brief says it is "kept solely so a test can assert an override happened". A repo-wide
   search (`src/`, `scripts/`, `tests/`) finds the symbol at exactly one place: its own
   definition at `labels.py:95`. It is dead and is simply deleted; no test needs rewriting.
   (The `DNG` code it refers to still lives in the frozen V1 path at `sensor.py:715` and
   `renderer.py:506`, which this plan does not touch.)
2. **Commit `4b6f7196` was two sources of a *count*, not of a *name*.** It corrected three
   numbers the layout registry and the painter disagreed on (how many maps, the gap between
   maps, the card's padding). The analogy to two sources of one truth holds and is worth
   citing; the specific claim "the same bug, about names" does not.
3. **There is a third size-from-live-count site the brief does not name.**
   `painters.build_channel_rows` (`painters.py:581`) is the **range-0** path — one labelled
   row per channel instead of a diamond map — and it lays out `n = len(names)` in two
   columns. `configs/environment/default.yaml` ships `visual_sensor_range: 0` and
   `olfactory_grid_range: 0`, so **this is the path most maintained worlds actually draw**.
   Its panel *height* is already a fixed constant (`_olf_min_size` / `_visual_min_size`
   return `Size(0, OLF_ROWS_H)` / `Size(0, VISUAL_ROWS_H)` at range 0), so the panel does not
   change shape with channel count — but the rows themselves still pack to the live count.
   **Decision taken in this plan: the range-0 rows path is left alone** (§D6), because its
   panel size is already fixed, which is what the user asked for. It is recorded here so the
   omission is deliberate rather than missed.

### A3. Why the names must not go into `EnvParams` — confirmed

Two independent blockers, both verified:

- **The parity gates load configs raw.** `tests/env/test_unified_parity.py:151` and
  `tests/env/test_thermal_parity.py:247` both do `yaml.safe_load` → `Config(cfg_dict)` →
  `load_env_params(config)` with **no `extends:` resolution**, and `test_unified_parity`'s
  collector sweeps `configs/environment/experiment/**` with **no archive exclusion**. A new
  `get_mandatory` key inside `load_env_params` therefore raises on ~38 standalone fixtured
  configs (23 of them under `archive/`, which CLAUDE.md forbids migrating) plus the 3 frozen
  worlds under `tests/env/fixtures/frozen_parity_worlds/`.
- **A field added after a pickle was written is absent — or, worse, silently defaulted.**
  `EnvParams` is a Flax `struct.dataclass` pickled into every `run_meta.pkl`. A new field
  **with no class-level default** does not appear on an old unpickled object at all —
  `hasattr` returns `False` — and every recording on disk, including all 11 render-audit
  fixture cells, would break loudly. A new field **with a plain default** is worse rather
  than better: the instance dict lacks it, so attribute lookup falls through to the class
  attribute and every archived recording silently reports the default as though the run had
  declared it. That is a fallback default wearing a different hat. Either way `EnvParams` is
  the wrong carriage; the second case is the one that would have shipped quietly. `render_recordings_v2.py`
  already carries a comment recording exactly this failure (lines ~188–196): rebuilding an
  archived recording's params with `dataclasses.replace` raises, because the archived object
  predates `thermal_warming_rate_scale`.

This also settles the brief's "mandatory names list validated against a non-mandatory size
key" worry. `sensory.visual_vector_size` is read with a plain `config.get(...)` defaulting to
8 (`config_loader.py:1687`), unlike `sensory.vector_size` which is `get_mandatory`
(`:2386`). **This plan does not make `visual_vector_size` mandatory** — doing so would join
the four keys that have already broken the standalone-config population (see the Known Bugs
row on mandatory-key rollout). The names list is instead validated at **recording-write
time** against the *resolved* value `params.visual_vector_size`, which always exists. No new
mandatory key enters `load_env_params` at all.

### A4. Measured panel geometry, today

Measured by building real params through `load_env_config` → `load_env_params` and calling
`panels._span` / `labels.map_plan` directly:

| Vision channels | Maps drawn | Declared panel span at range 2 | Per-map width | Map square |
|---|---|---|---|---|
| 8 (today's default) | 6 | 362 px | 50 px | 10.0 px |
| 1 | 1 | **82 px** | 50 px | 10.0 px |

So the defect has two halves. `panels._span` (`panels.py:406`) declares a **minimum** that
collapses from 362 px to 82 px, and `painters.build_channel_maps` (`painters.py:660`)
divides whatever width it is *granted* by the live map count — `slot = (w - MAP_GAP*(n-1))/n`
— so at one channel a single map takes the whole slot. Its drawn size is then capped by
panel height (`box = min(slot, h - 58 - 40)`) and centred, so the honest description is
"one map, centred in a slot as wide as the panel", not literally a map stretched to full
width. Both sites must move to the conventional panel size (§D4) or the two disagree again —
which is the failure mode of `4b6f7196`.

### A5. A vision-dim-1 world is harder to build than the brief assumes

The brief requires a render at vision dim 1. The two fixture cells that already claim to do
this — `E6sum` and `E6bin` in `scripts/eval/make_render_fixture_recordings.py:322-338` —
**do not build**, and were never generated (no `E6*` directory exists under
`results/render_audit/recordings/`, which holds M1, M1x, M2, M3, M4, M4b, M4r, M5, M6, M6b,
W20). Both fail at load:

```
ValueError: Resource(food): 'visual_properties' has length 8 but visual_vector_size is 1.
```

Measured staged probe: a vision-dim-1 world needs **all** of the following, or
`load_env_params` raises:

- `sensory.visual_vector_size: 1`
- `sensory.visual_background_properties` as a 3×1 table (`config_loader.py:1989-1995`;
  the key already exists in `default.yaml` at 3×8, so it must be *replaced*, not added)
- every entity's `visual_properties` **and** `visual_properties_std` rewritten to length 1,
  across all three entity lists — which are `environment.resources`,
  `environment.entities`, `environment.obstacles` (**note: `entities`, not `animals`**)

With those, a dim-1 world loads and reports `Visual = 13` dims at range 2. The fixture
script's override guard (`build_params`, ~line 437) refuses any override key absent from the
config, and rejects nothing here because all these keys exist; entity lists are replaced
wholesale, which `Config.set` supports.

### A6. The baseline is already red, for reasons outside this work

`pytest tests/env/test_dashboard_band_span.py tests/env/test_dashboard_layout.py
tests/env/test_dashboard_cells.py` → **3 failed, 184 passed, 2 skipped** (42.8 s).

All three failures are the same cause: `test_dashboard_layout.py:68` names
`configs/environment/experiment/basic/03-random_init_10x10_ckpt1k.yaml`, and a **parallel
session has staged that file's move** out of `basic/` into
`configs/environment/experiment/archive/basic_superseded/`. This is not caused by this plan
and **must not be fixed by it** — the owning session must update that list. The developer
records the same three failures before and after; any *fourth* failure is theirs.

**Correction (2026-09-19, `plan-reviewer` O3).** An earlier draft of this section said the
same session had staged "two new `05-campfire_thermal_10x10_olf1_vis{2,3}.yaml` worlds". That
was wrong and inverted: the git index shows **`D` — staged deletions** for both, and neither
file is on disk. The consequence is not cosmetic. `tests/env/test_dashboard_band_span.py`
ends with `test_a_world_that_reads_both_senses_wide_packs_and_paints`, parametrised over
config paths; if those two worlds leave the tree, **its wide-sense cases skip rather than
fail** — the quiet way a gate stops gating, which is the exact failure mode `4b6f7196` was
about. **CP0 must re-measure the baseline and record whether those cases run or skip**, rather
than inheriting the numbers above.

### A7. Known-bug collisions (from `bug-curator`)

- **The height twin is open.** `panels._map_h` under-declares the painter's height need by
  36 px at every range, masked only by `layout.MIN_BAND_H = 200`, first biting at range 5.
  This plan edits `_span` (width) and `build_channel_maps` — the same two functions, other
  dimension. **Out of scope; do not absorb it.** Touching it silently would be unrequested
  scope growth on the exact functions whose disagreement broke every video last week.
- **`RECORDING_FORMAT_VERSION` is read nowhere** (`eval_recording.py:20`, written at `:85`
  and `:102`, no reader repo-wide). Do not expect the stamp to reject stale meta — see the
  open question in §Q1.
- **`tests/env/test_backward_compat_configs.py` cannot detect a missing new key** in any
  maintained world: it skips any config whose load error says "is required but missing", and
  all eight `basic/` worlds use `extends:`. It will stay green regardless; it is **not** a
  valid gate for this work.

---

## Implementation Plan

### Design

#### D1. Carriage: `run_meta.pkl`, as a new top-level key

Names and groups travel in **`run_meta.pkl`**, beside the display-facing config it already
carries (`params`, `icon_config`, `action_map`, `config_path`, `extras`, `version` —
`src/utils/eval_recording.py:99-112`). Reasons, in order of weight:

1. It is the only carriage that does not break the parity gates or existing pickles (§A3).
2. It is **already the display-config channel**: `icon_config` and `action_map` are exactly
   the same kind of thing — facts about how to *draw* a run, not about how the environment
   *behaves*.
3. Its writer never runs inside the parity gates, so `get_mandatory` there cannot turn a
   raw-loading test red.

   > **Correction (`plan-reviewer` C3/C2).** An earlier draft justified this as "the writer
   > runs only in real evaluation, where the config has been resolved through
   > `load_env_config`". **That is false.** The common evaluation path,
   > `scripts/eval/eval_rollout.py --config <run>/models/config.yaml` (`:692, :944, :959`),
   > loads a run's **frozen saved config** — a resolved snapshot with no `extends:` and no
   > keys invented after the run finished. The writer therefore *does* meet un-layered
   > configs, and `get_mandatory` raises there for every pre-change checkpoint. The carriage
   > decision is unaffected (the parity gates still never reach this code), but the
   > consequence is real and is now costed in §D7 rather than assumed away.
4. A missing key on an old pickle is a plain `.get(...) is None`, which is precisely the
   legacy signal decision #5 needs.

**A new top-level key, not a slot inside `extras`.** `extras` is per-run provenance and the
fixture generator already floods it with eleven cell-description keys; a display contract
living in that dict would be one collision away from silence. The new key is
`channel_display`, one dict covering both senses.

**Rejected alternatives**: `EnvParams` (§A3); a sidecar YAML beside the recording (a second
file to lose, and no atomicity with the meta it describes); re-reading the original config
at render time (`config_path` often points at a file that has since changed or moved —
the fixture script exists because of precisely that hazard).

#### D2. The `run_meta` payload shape

```python
'channel_display': {
    'Olfaction': {
        'names':  [{'name': 'Food', 'qualifier': ''}, ...],   # exactly N channels
        'groups': [],                                          # usually empty
    },
    'Visual': {
        'names':  [{'name': 'Grass', 'qualifier': ''}, ...],
        'groups': [{'name': 'Terrain', 'channels': [0, 1, 2]}],
    },
}
```

Sense keys are the **observation-breakdown names** `"Olfaction"` / `"Visual"`, matching what
`episode.py` already passes as `sense` — not the reader-facing titles "Olfaction"/"Vision".

#### D3. Config schema — four new flat keys under `sensory:`

All four sit **directly under `sensory:`**, beside `vector_size` and `visual_vector_size`,
at the existing two-space indent. No new sub-block.

| Key | Shape | Meaning |
|---|---|---|
| `sensory.olfactory_channel_names` | list of `{name, qualifier}`, length `vector_size` | reader-facing name per smell channel |
| `sensory.visual_channel_names` | list of `{name, qualifier}`, length `visual_vector_size` | reader-facing name per vision channel |
| `sensory.olfactory_channel_groups` | list of `{name, channels}` | channels drawn as one map; normally `[]` |
| `sensory.visual_channel_groups` | list of `{name, channels}` | ships as `[{name: Terrain, channels: [0,1,2]}]` |

**Name and qualifier are two fields, never one string.** The painter sets the qualifier in a
lighter, smaller style beside the name; a single string would force the painter to parse its
own label text, which `labels.py:59` already names as "how a display detail turns into a
parser".

**Validation, at recording-write time, all failing loudly** (`ValueError`, naming both
numbers):

- names list length ≠ the sense's resolved channel count
- any `name` empty or not a string
- a group index out of range, repeated, or appearing in two groups
- a group's channels not contiguous (the merged map is drawn at the run's first position)
- a group of fewer than 2 channels

There is deliberately **no check on how many channels a sense declares** — see §D4b.

#### D4. One constant per sense: the conventional panel size, in map slots

It lives in `labels.py` — the module `panels` and `painters` both already import, and which
has no dependencies of its own.

```python
#: How many map slots a sense's panel is sized for, whatever the run's channel
#: count. This is the number of maps TODAY'S shipped world draws: smell's five
#: channels are five maps, and vision's eight channels are six maps because the
#: three terrain channels ship merged into one. It is a conventional SIZE and NOT
#: a limit: the panel keeps this width whatever the run declares, so a run drawing
#: more maps than there are slots draws them PAST THE PANEL EDGE rather than being
#: refused or resized (user decision, 2026-09-19 -- see D4b before "fixing" an
#: overlapping frame). Raising it is a one-line edit here.
PANEL_MAP_SLOTS = {"Olfaction": 5, "Visual": 6}
```

**Why the constant is in maps, not channels.** The user named the channel counts (smell 5,
vision 8), but the panel is laid out in *maps*, and vision's eight channels draw six maps
because three of them merge. Sizing in channels would make the vision panel a third wider
than anything drawn into it — which is the precise miscount that broke every video in
`4b6f7196`.

**How the constant is anchored.** A test loads the shipped `configs/environment/default.yaml`
through the resolving loader, builds the display, and asserts the map count it actually draws
equals `PANEL_MAP_SLOTS[sense]`. The number is therefore pinned to a measurement of the real
shipped world rather than to a second hand-maintained constant that could drift.

#### D4b. No channel ceiling, and extra maps overflow silently — an ACCEPTED COST

> **This section records a user decision taken on 2026-09-19, not an engineering preference.**
> A future reader who meets an overlapping frame must find this decision here rather than
> conclude that the packer regressed.

**No validation rejects a channel count.** The ceiling check is removed. Everything else in
§D3 stays, because those are correctness checks (a names list that does not match its own
channel count, a group naming a channel that does not exist), not limits.

**The behaviour, stated plainly.** The panel keeps `PANEL_MAP_SLOTS[sense]` slots and its
fixed width **whatever the config declares**. A sense with more maps than slots draws the
extra ones **past the panel edge** — over the neighbouring sense panel, or off the card.
**Nothing raises and nothing is rejected** (a warning is logged — see the refinement below).
The user chose this on
2026-09-19 over the two alternatives they were offered: shrinking the slots to fit (rejected
because it reintroduces exactly the count-dependent sizing this change exists to remove) and
seeing a rendered frame before deciding (declined).

**Why nothing raises — the mechanism, so the claim is checkable.** The painter's only refusal
is its 10 px map-square floor (`painters.py`, `if cs < 10: raise LayoutOverflowError`). Square
size is `slot / (2r+1)` where `slot` is derived from the **slot count**, not from the number
of maps. So drawing extra maps does not shrink anything, the floor is never approached, and
the guard cannot fire. The overflow is silent by construction rather than by omission.

**What this costs, said explicitly.** It contradicts the property the whole layout was built
around. `LayoutOverflowError` exists so the renderer **refuses** rather than shipping a
misleading frame, and that refusal is the only reason the panel-width bug of 2026-09-18
surfaced at all instead of quietly shipping unreadable maps. This change carves out one case
where a misleading frame is produced deliberately. It is bounded to configs that declare more
channels than the conventional size — no shipped world does today.

**Consequence 1 — the pixel audit can now produce a TRUE finding that is not a bug.**
`scripts/eval/render_layout_audit.py` measures ink overlap between drawn elements. An
overflowing sense map lands on its neighbour, so the audit will correctly report it. The
rules that fire are, in likely order:

| Rule | What it would report | Note |
|---|---|---|
| `text_over_border` | a channel label lying across a card edge or the band divider | the audit calls this **"FORBIDDEN, not tolerated"** — it will not be a soft warning |
| `text_over_text` | the overflowing channel label sharing pixels with the neighbour's label | |
| `fill_over_text` / `text_over_fill` | a map tile painted over a neighbouring label, or the reverse | which one depends on composition order |
| `out_of_canvas` | foreground ink inside the outer canvas margin | only once overflow reaches the page edge |

**`cell_overdraw` is *not* among them**, contrary to a reasonable first guess. That rule
measures whether every occupant of a **world square in the arena grid panel** is visible; it
runs only when `--arena-axes` names the arena, and it knows nothing about the sensor band.
The band is out of its scope entirely.

**Verdict: an over-slot config is out of scope for the audit.** Its findings there are true
reports of a state the user accepted, not regressions, and the audit must not be loosened to
hide them — loosening it would blind the rule for every *correct* frame too, which is how an
instrument stops being able to detect the thing it exists for.

**How a reader tells the two cases apart — and the trap in doing so.** The comparison is the
recording's map count for that sense against `PANEL_MAP_SLOTS[sense]`. If maps ≤ slots, any
band overlap is a **real regression**. If maps > slots, band findings are expected and
explained here — **but the absence of findings proves nothing**, for the reason in §D4c: an
over-slot *vision* run produces **fewer** findings than a correct one, not more. "maps > slots
and no band finding" must never be read as "the frame is fine". CP5b records the audit output
for an over-slot cell beside the same audit on a normal cell so this exists once as worked
evidence rather than as a rule someone has to remember. Making the audit print the
slots-versus-maps comparison in its own header would make this mechanical instead of manual —
**recommended as a follow-up, deliberately not done here**, because it is scope this change
was not asked for.

#### D4c. What the overflow ACTUALLY looks like — and why the two senses fail oppositely

> **Disposition pending the user.** §D4b's cost was accepted on the understanding that
> overflow means *visible spillover*. For one of the two senses it does not: it means the
> extra channels **vanish**. The consequence has been put to the user and **their answer
> governs**; until it arrives, CP5b renders both cases so the decision is made against a
> picture rather than a description. (`plan-reviewer` C6.)

**Verified mechanism.** Map tiles are drawn with `rrect` → `ax.add_patch(FancyBboxPatch(...))`
(`dashboard/style.py:100-105`). Nothing in the dashboard package ever sets `clip_on`,
`set_clip_path` or `set_clip_box` — grepped, zero hits — so patches take Matplotlib's default
**`clip_on=True`** and are clipped to their Axes. Channel labels are created with `ax.text`,
whose default is **`clip_on=False`**, so they are **not** clipped. Both senses are drawn into
**one** band Axes (`episode.py`, `ax, box = self._card("band")`), with olfaction on the left
and vision on the right. Those three facts together produce two opposite failures from one
rule:

| Sense | Where the over-slot tiles land | What a reader sees | What the audit sees |
|---|---|---|---|
| **Olfaction** (left child) | inside the band Axes, on top of the vision panel | a genuine overlap | **reports it** — a true finding |
| **Vision** (right child) | past the band Axes' right edge → **clipped away** | six maps and some **floating labels** with no tiles under them; no sign that channels 7–8 exist | **nothing to report** — there is no ink |

**Why this is worse than what was agreed.** For vision — the sense the whole vision-dim study
varies — an over-slot config produces a frame that is not obviously broken. It silently
*under-reports the agent's observation*, which is the exact class of defect this plan exists
to remove ("I'm worry about any potential quiet mistake"). An overlapping frame is ugly and
self-evident; a frame missing two channels looks fine and is wrong.

**The carve-out's bound is `maps > slots`, not `channels > conventional`.** The two differ
whenever grouping changes: 8 channels with the Terrain group are 6 maps (fits), and the same
8 channels with the group deleted are 8 maps (overflows). Stating the bound in channels would
mis-describe which configs are affected.

**Legacy and configured recordings resolve this case differently, deliberately.** A legacy
recording **grows** its panel (§D5) and therefore never reaches this state; a configured one
**overflows** (§D4b). Applying the overflow rule to legacy instead would clip tiles 7–8 on
*every* pre-change recording at vision range ≥ 1 — every fixture on disk — which is why §D5
exists.

**Refinement, 2026-09-19: warn at load, still draw.** The decision above stands unchanged —
nothing is rejected, nothing raises, the frame draws exactly as decided. What goes is the
**silence**. A warning is emitted when the display is built, naming **both numbers**: how many
maps this sense will draw, and how many slots the panel has.

The user moved on this after the reviewer showed that the how-to block in §10 *actively
invites the triggering edit*: it teaches a reader what the merge group does, and deleting it
takes vision from 6 maps to 8 — straight into overflow. An accidental edit that produces an
overlapping video with no signal anywhere is the "quiet mistake" this whole plan exists to
remove. This is a refinement of the no-limit decision, **not a reversal of it**: no limit is
imposed, no config is refused, and no frame is withheld.

**This deliberately overrides `plan-reviewer`'s C5 exit condition**, which asked for write-time
validation plus a raise inside `panel_map_slots` on the non-legacy path. A raise is a limit,
and the user had already declined limits. The warning satisfies the finding's actual concern —
discoverability — without reimposing what was refused. Emitted at both the write site
(`channel_display_from_config`) and the display-build site (`ChannelDisplay`), so a
hand-edited pickle that never passed through the writer is still reported.

**Consequence 2 — the merge group, where "fixed width" and "slots follow the grouping" could
contradict each other.** They do not, because the slot count is a **constant** and does not
follow the grouping at all. Dropping the terrain group does not widen the panel; it adds two
maps to a panel that still has six slots, so vision at 8 channels with **no** group draws 8
maps into 6 slots and **overflows by two**. With the ceiling gone, nothing rejects that
config either. The fixed-size property therefore survives intact and can be stated without
qualification:

> Panel width depends only on the sense. It is the same for every run — every channel count,
> every grouping, configured or legacy-with-fewer-maps. What varies is how much of it is
> filled, and whether anything spills past it.

That is a stronger guarantee than the grouping-dependent version considered earlier, and it
is why the slot count is a constant rather than derived. Two vision runs at 1 and 8 channels
get identical panels, which is the comparability the user asked for.

#### D5. Legacy recordings: sized to what they draw

A recording with no `channel_display` gets positional names (`Channel 0` …) and **no
groups**. An old 8-channel recording therefore draws **8 maps, not 6** — the merge was
hardcoded and is now data the recording does not carry.

**This is the one place §D4b's overflow rule is deliberately NOT applied, and it is
load-bearing.** 8 maps into a fixed 6-slot panel would overflow — so applying the accepted
cost here would mean **every recording already on disk renders with overlapping maps**,
including all eleven render-audit fixture cells, which are all 8-channel vision with no names
payload. Decision #5 asks old recordings to render with positional names; it does not ask
them to render broken.

> **Rule: when the names payload is absent, the panel is sized to
> `max(PANEL_MAP_SLOTS[sense], maps_drawn)`.**

The fixed width and its accepted overflow apply to recordings written **after** this change,
where a config genuinely declared the channel count. The distinction is principled rather
than convenient: §D4b's cost was accepted for *a config that declares more channels than the
conventional size*, and a legacy recording declares nothing at all. It is the one deliberate
asymmetry in the design and must be commented as such in the source, because the obvious
"simplification" — using the constant everywhere — silently breaks every archived recording.

**Correction: this does NOT "keep exactly today's sizing behaviour"** (an earlier draft said
so; `plan-reviewer` C4 showed it false). Today an 8-channel recording draws **6** maps,
because the terrain merge is hardcoded. After this change the same recording draws **8**,
because the merge is data it does not carry. The panel is sized to fit those 8 — which is a
*wider* panel than today's, not the same one.

##### D5b. Legacy recordings at vision range ≥ 3 are declared unrenderable — loudly

**Measured, not predicted.** At 8 maps the vision panel needs
`8 × (2r+1) × 10 + 6 × 7 + 32` px. At range 2 that is 474 px against the 520 px the band
grants — it fits. **At range 3 it is 634 px against 520 px**, and `layout.pack` refuses the
frame with `LayoutOverflowError`. This is the very refusal `4b6f7196` was written to
eliminate, reintroduced through the back door by the legacy path.

**User decision, 2026-09-19: declare these unrenderable, explicitly.** The alternatives put
to the user were a need-proportional band split (a layout change with its own render proof,
and the open height-twin bug lives next door — §A7) and letting the frame overflow. They chose
the explicit refusal.

**The refusal must not surface as a bare `LayoutOverflowError`.** The legacy path checks
before packing and raises a message that (a) names the reason — a recording made before
channel names existed draws one map per channel, which does not fit at this sensor range —
and (b) names the remedy: re-record it, which regenerates it with names and the terrain merge
and brings it back inside the panel.

**Blast radius: three recordings, all regenerable, nothing lost.**
`results/render_audit/olf1_vis3_{adaptive,smoke_20260918,spanfix}/recordings/<pct>/`.
(The reviewer cited these as `results/render_audit/recordings/olf1_vis3_*`; **that path does
not exist** — the real layout is `results/render_audit/<run>/recordings/<pct>/`, verified on
disk, e.g. `olf1_vis3_spanfix/recordings/71/`. A checkpoint pointing at the wrong path would
test nothing.) Their range-2 siblings `olf1_vis2_{regress,smoke_20260918,spanfix}` fit and are
unaffected. All six are script-regenerable and each carries its own `models/config.yaml`.

#### D6. Out of scope, stated so the omissions are deliberate

- The **range-0 rows path** (`build_channel_rows`) — §A2 item 3.
- The **height twin** bug — §A7.
- Any change to `configs/environment/experiment/basic/*` — another session owns the vision-dim
  rollout. This plan touches `configs/environment/default.yaml` only (user-authorised).
- The three pre-existing test failures — §A6.

#### D7. Pre-change checkpoints cannot be re-recorded until the compatibility work lands

**This is an accepted cost, decided by the user on 2026-09-19, not an oversight.**

**What breaks.** `scripts/eval/eval_rollout.py --config <run>/models/config.yaml` is the
common way to re-record video from a finished run. That file is a **frozen saved config**: it
has no `extends:` to inherit through and cannot contain keys invented after the run finished.
So `channel_display_from_config`'s `get_mandatory` raises, and **every checkpoint trained
before this change fails at `write_run_meta`**. Verified on a real saved config —
`results/render_audit/olf1_vis3_spanfix/models/config.yaml` carries `visual_vector_size: 8`
and none of the four new keys.

**What does not break.** Every run trained after this change inherits the keys from
`default.yaml` and records normally. Rendering **already-recorded** episodes is unaffected —
that path reads `run_meta.pkl` and never re-reads a config (§D5 covers it).

**No fallback default.** The user explicitly rejected that option. A default here would mean a
pre-change run silently recording today's names as though it had declared them — which is the
same class of quiet mistake as the two-source name tables this plan deletes, and it would be
invisible in exactly the archived runs nobody re-checks.

**The unblocking work** is [[SAVED_RUN_CONFIG_COMPAT]] — the compatibility layer for frozen
run configs, currently PLANNED and not implemented. The four new keys should be registered in
its table so that when it lands, pre-change checkpoints become re-recordable in the same
change. Until then, re-recording a pre-change checkpoint is **not available**, and that is the
accepted position rather than a bug to be worked around.

**This is a new instance of a known class**, not a new kind of problem: it is the fifth
mandatory-key rollout to strand saved configs (§A7). `bug-curator` should record it against
that row once implemented.

**The error must teach.** `channel_display_from_config` names the missing key, says that the
config predates channel names, and points at the remedy (re-record at current code, or wait
for the compatibility layer) rather than raising a bare "key required but missing".

---

### File Changes

#### 1. `src/environment/dashboard/labels.py` — delete the tables, take names as data

**Delete**: `OLFACTORY_LABELS` (45), `OLFACTORY_LONG` (47), `OLFACTORY_PARTS` (62),
`VISUAL_LABELS_V8` (71), `VISUAL_LONG` (82), `SUPERSEDED_VISUAL_LABELS` (95),
`_STANDARD_VISUAL_WIDTH` (97), `TERRAIN_CHANNELS` (173). Rewrite the module docstring: its
current text describes overriding an adapter's labels and a name table keyed by index, both
of which stop being true.

**Add** `PANEL_MAP_SLOTS` (§D4). **No ceiling constant** — there is deliberately no validation
of how many channels a sense declares (§D4b).

**Replace** the four functions. `channel_labels` / `visual_labels` / `olfactory_labels` stop
existing as name tables; what the package needs is a single description of a sense's display,
built once from the run's `channel_display` payload (or its absence):

```python
@dataclass(frozen=True)
class ChannelDisplay:
    """Everything the renderer needs to LABEL one sense. Built from a recording's
    `run_meta['channel_display']`, or positionally when the recording predates it."""
    names: tuple[tuple[str, str], ...]          # (name, qualifier) per channel
    groups: tuple[tuple[str, tuple[int, ...]], ...]
    legacy: bool                                 # True -> positional names, no groups

    @classmethod
    def from_meta(cls, sense: str, n_channels: int, payload: dict | None) -> "ChannelDisplay":
        if payload is None:
            return cls(tuple((f"Channel {i}", "") for i in range(n_channels)), (), True)
        ...  # validate length/indices, raise ValueError naming both numbers

def map_plan(sense, display: ChannelDisplay) -> list[tuple[str, str, str, int | None]]:
    """Which maps a sense draws: [(name, qualifier, kind, channel), ...].
    A grouped run of channels becomes ONE map of kind "terrain"; every other
    channel is its own "seq" map at its own index."""

def panel_map_slots(sense, display: ChannelDisplay) -> int:
    """How many slots the panel is sized for -- the fixed conventional size,
    except that a LEGACY recording is sized to what it actually draws (D5).

    Deliberately does NOT raise when a configured run draws more maps than there
    are slots: no limit is imposed (D4b, user decision). It WARNS, naming both
    numbers, so an accidental edit -- deleting the Terrain group takes vision
    from 6 maps to 8 -- is discoverable instead of silent.
    """
    drawn = len(map_plan(sense, display))
    if display.legacy:
        return max(PANEL_MAP_SLOTS[sense], drawn)
    if drawn > PANEL_MAP_SLOTS[sense]:
        logger.warning(
            "%s draws %d maps but its panel has %d slots; the extra maps will be "
            "drawn past the panel edge. This is allowed (see D4b) -- if it was not "
            "intended, check sensory.%s_channel_groups.",
            sense, drawn, PANEL_MAP_SLOTS[sense], sense.lower())
    return PANEL_MAP_SLOTS[sense]
```

**Preserve the raising property.** `display_channel`'s guarantee — a channel code can never
silently reach a frame — is preserved structurally: names arrive as data validated at
write time, and `ChannelDisplay.from_meta` raises on a wrong-length or malformed payload.
Nothing in the drawing path can invent a name.

Keep the `PANEL_MAP_SLOTS`/`map_plan` relationship reachable from **one** call, as
`4b6f7196` made it: `panels` and `painters` must both ask `panel_map_slots`, never
recompute. `labels.py` must stay Matplotlib-free (a test pins this).

#### 2. `src/environment/dashboard/panels.py`

- `LayoutContext` (dataclass, ~202–203): add `channel_display: Mapping[str, object] | None = None`
  — the raw `run_meta` payload — and build `ChannelDisplay` per sense. Keep
  `visual_vector_size` / `olfactory_channels`; they still answer "how many channels".
- `from_params` (219): gains a `channel_display=None` parameter, passed through from
  `EpisodeRenderer`. `params` alone cannot supply it.
- `_span` (**line 406**): replace
  `n_maps = len(map_plan(sense, channel_labels(sense, n_channels)))`
  with `n_maps = panel_map_slots(sense, display)`. Signature takes the `ChannelDisplay`.
- `_olf_min_size` (367) / `_visual_min_size` (374): pass the per-sense display through.

#### 3. `src/environment/dashboard/painters.py`

- `build_channel_maps` (**line 643**, slot arithmetic at **660**): take `display` instead of
  `codes`; `maps = map_plan(sense, display)`; and crucially
  **`n = panel_map_slots(sense, display)`** for the slot divisor while iterating only over
  `maps`. Drawn maps occupy the first slots; the remainder stay blank. This is the line that
  makes blank space appear instead of one stretched map.
- `build_channel_rows` (581): takes `display` and reads `display.names` directly instead of
  calling `channel_display(sense, code)`. Layout logic unchanged (§D6).

#### 4. `src/environment/dashboard/episode.py`

- `EpisodeRenderer.__init__` (148): new keyword-only `channel_display=None`, stored and
  handed to `LayoutContext.from_params` (166). Keyword-only with a `None` default so the four
  existing direct constructor calls keep working unchanged.
- `from_recording` (540–551): pass `channel_display=meta.get("channel_display")`.
- Band drawing (466–478): replace `olfactory_labels(...)` / `visual_labels(...)` with the
  context's per-sense `ChannelDisplay`; pass it to both painters.

#### 4b. `scripts/eval/render_recordings_v2.py` — THE PRODUCTION VIDEO PATH

**Without this file the feature is invisible where it matters.** This script builds
`EpisodeRenderer` **directly** from `params` / `icon_config` / `action_map` and never calls
`from_recording`, so editing `from_recording` alone would leave every production video
rendering through the legacy branch — positional "Channel 0" names and 8 unmerged vision
maps — while every checkpoint in this plan went green through a different entry point
(`plan-reviewer` C3). That is the same shape as the 2026-09-18 incident this plan cites.

Three sites, all needed:

| Line | Function | Change |
|---|---|---|
| ~183–197 | `_init_worker` | stash `meta.get("channel_display")` into `_WORKER_STATE` alongside `params` / `icon_config` / `action_map` |
| 223 | `_render_episode` | pass `channel_display=_WORKER_STATE["channel_display"]` |
| 288 | `_benchmark` | pass `channel_display=meta.get("channel_display")` |

**`scripts/eval/render_recordings.py` needs no change** — checked, closing C3's second exit
condition. It is the **V1** path: it renders through `src.environment.renderer.render_jax_state`
(`:93, :131`) and never imports the dashboard package, so it keeps the frozen V1 labels and is
outside this plan's scope.

#### 5. `src/environment/dashboard/__init__.py`

Remove `channel_labels`, `olfactory_labels`, `visual_labels` from the import (36) and
`__all__` (98–104); export `ChannelDisplay`, `map_plan`, `panel_map_slots`,
`PANEL_MAP_SLOTS`.

#### 6. `src/utils/eval_recording.py`

- `write_run_meta` (99): new **required** parameter `channel_display: dict`, written as the
  top-level `'channel_display'` key. Required rather than defaulted, so that a new writer
  cannot forget it — **all four** existing call sites are updated in this change (§8).
  Requiring it is what surfaced the fourth site; keep it required.
- **Add the parameter AFTER the existing positional ones.**
  `tests/env/test_dashboard_v1_imports.py:80` pins
  `_sig(write_run_meta).startswith("(out_dir: pathlib.Path, params, icon_config")`, so
  inserting it earlier in the signature turns that test red for an unrelated reason.
- Module docstring (1–12): add `channel_display` to the `run_meta.pkl` contents list.
- **Do not bump `RECORDING_FORMAT_VERSION`** — decided by the user, §Q1.

#### 7. New helper — where the config is read

One function, imported by all **four** writers, so the config→payload translation exists once:

```python
# src/utils/eval_recording.py
def channel_display_from_config(config, params) -> dict:
    """Build the run_meta channel_display payload from a resolved config.

    NOT reached by the parity gates (they never write a recording), which is why
    `get_mandatory` is safe here. It IS reached with UN-LAYERED configs, though:
    `eval_rollout.py --config <run>/models/config.yaml` hands it a run's frozen
    saved config, which cannot contain keys invented after that run finished. That
    case raises, deliberately and with a message that teaches -- see D7.
    """
```

It reads the four keys with `get_mandatory`, validates per §D3 against
`int(params.olfactory_vector_size)` and `int(params.visual_vector_size)`, and raises
`ValueError` naming both numbers on any mismatch.

**Two message requirements, both load-bearing:**

- **Missing key** (the pre-change-checkpoint case, §D7): the error names the missing key,
  says the config predates channel names, and points at the remedy — re-record at current
  code, or wait for [[SAVED_RUN_CONFIG_COMPAT]]. Not a bare "key required but missing".
- **More maps than slots** (§D4b): **warn, do not raise**, naming both numbers. This is the
  same warning `panel_map_slots` emits, issued here too so that a config problem is reported
  when the recording is *written* rather than only when it is later drawn.

#### 8. Four writer call sites — not three

| File | Line | Change |
|---|---|---|
| `src/utils/evaluation_core.py` | 290 | add `channel_display=channel_display_from_config(config, params)` |
| `src/algorithms/dreamer_srl/eval.py` | 83 | same, with `env_params` |
| `src/algorithms/dreamer_srl/eval.py` | 380 | same |
| **`scripts/eval/eval_rollout.py`** | **1238** (import at 1231) | **same — missed by the first draft** |

The fourth site was found by `plan-reviewer` (C1) and verified here. Because the parameter is
required, omitting it is not a silent gap but a `TypeError` on every
`eval_rollout.py --record` — which is the argument for keeping it required. This is also the
site that meets frozen saved configs (§D7).

#### 9. `scripts/eval/make_render_fixture_recordings.py`

- `write_run_meta` call (523): pass the payload, built from the cell's resolved `_cfg`
  (already returned by `build_params`).
- **Fix cells `E6sum` / `E6bin`** (322–338) so a vision-dim-1 fixture can be generated at
  all (§A5). Their override dicts additionally need
  `sensory.visual_background_properties` as 3×1 and all three entity lists
  (`environment.resources`, `environment.entities`, `environment.obstacles`) replaced with
  length-1 `visual_properties` / `visual_properties_std`. Because these are whole-list
  replacements of config structure rather than scalar tweaks, express them as a small helper
  in the script (`_vision_dim(V)` returning the override dict) rather than by hand per cell.
- **The helper must rewrite the resolved config's OWN entity lists, never hand-copy them.**
  Reading `cfg.get("environment.<list>")` and replacing only the `visual_properties[_std]`
  fields keeps one source of truth; pasting entity definitions into the script would make it
  a second copy of `default.yaml`'s entities — two sources of one fact, inside a plan whose
  whole purpose is removing exactly that (`plan-reviewer` L2).
- No `_CONDITIONAL_KEYS` change is needed — every key involved already exists in
  `default.yaml`.
- **The dim-1 cells must also override the two display keys**, or the cell inherits
  `default.yaml`'s 8-entry `visual_channel_names` and its 3-channel Terrain group and fails
  validation at write time (`plan-reviewer` M9): add
  `sensory.visual_channel_names` (one entry) and `sensory.visual_channel_groups: []`.

#### 9b. Coordination with the parallel vision-dim rollout — time-critical

Another session is currently setting `visual_vector_size: 1` across the `basic/` ladder
configs (§Context). **Those configs will fail at recording-write time** unless each also
redeclares `visual_channel_names` (1 entry) and `visual_channel_groups: []`, for the
inheritance reason in §10's how-to block. This does not break training — the configs load and
run — so it would surface only when someone later tries to record a video, which is the worst
time to find it.

**This plan does not edit those files** (they belong to the other session). The ordering that
avoids a broken ladder:

1. This change lands `default.yaml`'s four keys **first**. Every ladder config that has not
   yet changed its channel count keeps inheriting a correct 8-entry list and is unaffected.
2. The other session adds the two display keys **in the same edit** that sets
   `visual_vector_size: 1`, so no intermediate commit has a size that disagrees with its
   names.
3. If their rollout has already landed when this change starts, the developer **reports it
   and stops** rather than editing their files: the fix is one line per config, but it is
   theirs to make, and a config edited by two sessions at once is how the staged-deletion
   confusion in §A6 happened.

**Detection, so this cannot be missed:** CP6 records, for every maintained config under
`configs/environment/`, whether `channel_display_from_config` succeeds. That sweep is the
gate — not a grep, because the failure is a length comparison after inheritance resolves.

#### 10. `configs/environment/default.yaml` — the four keys and their how-to block

Inserted in the `sensory:` block: the olfaction keys after `vector_size: 5` (line 207), the
vision keys after `visual_vector_size: 8` (line 233). **The comment block is a deliverable in
its own right**, matching the density and tone of the existing `olfactory_grid_range` note
(209–221). It must let a reader work out how to set names *without reading any code*:

```yaml
  # ── HOW TO NAME THE SMELL CHANNELS ──────────────────────────────────────────
  # These names are what a viewer reads under each map in the episode video.
  # Renaming one changes the VIDEO ONLY: it does not touch the observation vector,
  # the agent's input, or training. Nothing about a run changes except its picture.
  #
  # WHICH CHANNEL IS WHICH. Read the entity blocks above. Every entity carries a
  # `properties:` vector of length vector_size, and the POSITION it writes into is
  # the channel. Reading column by column in this file:
  #   channel 0  food           properties: [1.0, 0, 0, 0, 0]      -> "Food"
  #   channel 1  predator 0.7, rabbit 0.5                          -> shared
  #   channel 2  predator 0.5, rabbit 0.7                          -> shared
  #   channel 3  bush           properties: [0, 0, 0, 1.0, 0]      -> "Bush"
  #   channel 4  tree           properties: [0, 0, 0, 0, 1.0]      -> "Tree"
  #
  # NOTE CHANNELS 1 AND 2 -- they are the reason to read the column and not guess
  # from one entity. The predator and the rabbit BOTH write into both, with
  # opposite weightings, so neither channel belongs to one animal. Naming channel 1
  # "Predator" would claim a separation the signal does not have. Name a shared
  # channel by its leaning, and put the leaning in the qualifier.
  #
  # NAME AND QUALIFIER ARE TWO FIELDS, never one string with brackets in it: the
  # painter draws the qualifier in a smaller, lighter style beside the name, and it
  # must never have to parse its own label text to find where one ends.
  #
  # LENGTH RULE: exactly `vector_size` entries (5 here). A mismatch fails when the
  # recording is written, with a message naming both numbers.
  olfactory_channel_names:
    - {name: "Food",    qualifier: ""}
    - {name: "Odour A", qualifier: "predator-leaning"}
    - {name: "Odour B", qualifier: "neutral-leaning"}
    - {name: "Bush",    qualifier: ""}
    - {name: "Tree",    qualifier: ""}
  # Channels drawn as ONE map instead of several (see the vision block below for
  # what a group is for). Smell has none: two smells can be present at once.
  olfactory_channel_groups: []
```

```yaml
  # ── HOW TO NAME THE VISION CHANNELS ─────────────────────────────────────────
  # Same rules as the smell block above: display only, two fields per channel, and
  # exactly `visual_vector_size` entries (8 here).
  #
  # ►► IF YOU CHANGE visual_vector_size, YOU MUST REDECLARE BOTH KEYS IN THE SAME
  # FILE. A config that sets `visual_vector_size: 1` and says nothing else still
  # INHERITS this 8-entry list and the 3-channel Terrain group below, because a
  # child config replaces a list wholesale or not at all -- it cannot shorten one.
  # The mismatch is caught when a recording is written (8 names against 1 channel),
  # so the config loads and trains perfectly well and only fails later, at eval.
  # A 1-channel vision config needs BOTH of these, beside its size:
  #     visual_channel_names:  [{name: "Visible", qualifier: ""}]
  #     visual_channel_groups: []     # no terrain merge: there is no channel 1 or 2
  # The same applies to the smell keys and `vector_size`.
  #
  # WHICH CHANNEL IS WHICH. Entities carry `visual_properties:` (one-hot here), and
  # channels 0-2 come from `visual_background_properties` below, whose three rows
  # are grass / sand / plain in that order:
  #   channel 0  grass      visual_background_properties row 0   -> "Grass"
  #   channel 1  sand       row 1                                -> "Sand"
  #   channel 2  plain      row 2                                -> "Plain"
  #   channel 3  food       visual_properties: [0,0,0,1,0,0,0,0] -> "Food"
  #   channel 4  hiding_predator                                 -> "Hiding predator"
  #   channel 5  predator                                        -> "Predator"
  #   channel 6  rock AND tree AND bush all write here           -> "Obstacle"
  #   channel 7  rabbit (class neutral)                          -> "Neutral"
  #
  # CHANNEL 6 IS THE ONE TO BE CAREFUL WITH: three different obstacles share it, so
  # it is "Obstacle" and not "Rock". Check the column before renaming.
  #
  # CHANNEL COUNT IS AN EXPERIMENTAL KNOB. visual_vector_size is deliberately varied
  # between studies (a single-channel vision arm is a real experiment). The video's
  # sense panels are a FIXED SIZE -- the same width for every run, whatever this
  # number says -- so a run with fewer channels draws its maps at normal size and
  # leaves the rest of the panel BLANK. That blank area is intended: it is not a
  # layout bug, and it is what lets two runs' panels be compared side by side.
  #
  # THERE IS NO UPPER LIMIT. The vision panel holds 6 maps (8 channels, with 0-2
  # merged into one Terrain map; see below). Declare more than fits and the extra
  # maps are drawn straight past the panel edge, over the neighbouring sense --
  # nothing refuses it and the video still renders. This was chosen deliberately
  # on 2026-09-19 in preference to any limit. A WARNING is logged when it happens,
  # naming how many maps will be drawn and how many slots exist, so it is
  # discoverable; nothing fails. If a video ever looks overlapped here, THIS is
  # why; the panel size is one line in src/environment/dashboard/labels.py.
  #
  # WATCH THIS ONE IF YOU EDIT THE GROUP BELOW: deleting the Terrain group takes
  # vision from 6 maps to 8 and overflows the panel, because the three terrain
  # channels stop sharing a map. That is the likeliest accidental way to get here.
  visual_channel_names:
    - {name: "Grass",           qualifier: ""}
    - {name: "Sand",            qualifier: ""}
    - {name: "Plain",           qualifier: ""}
    - {name: "Food",            qualifier: ""}
    - {name: "Hiding predator", qualifier: ""}
    - {name: "Predator",        qualifier: ""}
    - {name: "Obstacle",        qualifier: ""}
    - {name: "Neutral",         qualifier: ""}
  # ── MERGING CHANNELS INTO ONE MAP ───────────────────────────────────────────
  # A group draws several channels as a SINGLE map instead of one map each. Terrain
  # is grouped because a square is grass OR sand OR plain and never two at once, so
  # three separate maps would each be blank wherever the other two are not.
  #   name:     what the merged map is called on screen
  #   channels: which channel indices it covers -- must be a contiguous run, each
  #             index must exist, and no channel may appear in two groups
  # A group naming a channel that does not exist FAILS when the recording is
  # written. It cannot silently change how many maps the video draws.
  visual_channel_groups:
    - {name: "Terrain", channels: [0, 1, 2]}
```

#### 11. Tests

| Path | What it must assert |
|---|---|
| `tests/env/test_dashboard_channel_display.py` (new) | length mismatch raises naming both numbers; out-of-range / duplicate / non-contiguous group raises; absent payload gives positional names and no groups; `PANEL_MAP_SLOTS[s]` equals the map count the **shipped `default.yaml`** actually draws, loaded through the resolving loader (anchors the constant to a measurement, not to a second constant); **`_span` returns the same width at 1, 8 and 12 channels**; an over-slot channel count **does not raise** (§D4b — the absence of a refusal is the decision, so it is asserted explicitly); a legacy payload with 8 maps is sized to 8, not 6 (§D5) |
| `tests/env/test_dashboard_band_span.py` | update the `channel_labels` import (54) and `_painter_map_count` (98) / `_ctx` (~78) to the new API. **The equality property must be parametrised over BOTH sizing regimes** — configured (`slots`) and legacy (`max(slots, drawn)`) — since post-change they are different functions (`plan-reviewer` M5). **`test_an_off_standard_vision_width_is_declared_one_map_per_channel` (213) must be REWRITTEN, not updated**: "4 channels ⇒ 4 maps" becomes **false** on the configured path (4 configured channels ⇒ 6 slots; 4 legacy channels ⇒ `max(6,4)` = 6). Also confirm whether its two config cases at `test_a_world_that_reads_both_senses_wide_packs_and_paints` (262) still run — §A6 |
| `tests/env/test_dashboard_channel_display.py` (missing-key cases) | **one test per new key**: delete the key from a resolved config and assert `ValueError` **naming that key**. Required by CONFIG_GUIDE Maintenance Contract item 3, which the length/index/duplicate tests do not satisfy (`plan-reviewer` M6) |
| `tests/scripts/test_render_recordings_v2.py`, `tests/env/test_dashboard_frames.py` | construct via `meta.get("channel_display")`; must still pass on pre-change fixtures (legacy path). **Name the fixture that stays un-regenerated** (CP7) — otherwise this assertion goes vacuous the moment every cell is re-recorded (`plan-reviewer` M4) |
| `tests/env/test_dashboard_v1_imports.py` | unchanged, but **must stay green**: it pins `write_run_meta`'s signature prefix (§6, L3) |

**Every one of these must be run against unmodified source first and its failure
recorded.** A test that passes before the change proves nothing. The Implementation Report
must carry the pre-change failure output for each new test.

#### 12. Documentation (maintenance contracts)

- `docs/environment/CONFIG_GUIDE.md` — the four keys, the length rule, the group rules
  (Maintenance Contract items 1–3).
- `docs/environment/02_config_schema.md` — the four keys in the `sensory` table.
- `docs/environment/CONFIG_CRITICAL_SETTINGS.md` — **a dated change-log entry is required**
  in the same commit. These keys are display-only and change no agent's behaviour, so the
  entry states that explicitly and records the blast radius as "video only". Whether they
  also belong in the *registry* table: **no** — that table is for settings that change what a
  run does. Record the reasoning in the entry.
- `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` — **not required**: no file under `scripts/`
  is added, moved, renamed or deleted; `make_render_fixture_recordings.py` is edited in
  place and its callers are unchanged. Confirm before skipping.

---

## Checkpoints

Each step names its own **failure-detectable check** and its **rollback**. The gate for
renderer work is a rendered frame someone looks at — a green unit suite is not sufficient
evidence, because a change on 2026-09-18 passed 18 new unit tests while breaking the product
end to end.

- [ ] **CP0 — Re-measure the baseline, including its red.** Run the three dashboard test
      files and `tests/env/test_unified_parity.py`; record counts. Measured 2026-09-19:
      **3 failed, 184 passed, 2 skipped** on the dashboard files (§A6) and **72 passed,
      350 skipped** on parity. **Do not inherit those numbers** — a parallel session has
      staged config deletions that change the shape of this baseline, so re-run and record
      what you actually get, including **whether `test_a_world_that_reads_both_senses_wide_packs_and_paints`
      runs or skips** (§A6; a skipped case is a gate that stopped gating).
      *Detects*: any later count that differs by anything other than the intended tests.
      *Rollback*: none (read-only).

- [ ] **CP1 — Write the new tests first, run them against unmodified source, record the
      failures.** *Detects*: a test that would have passed anyway — if any new test passes
      here, it is not testing the change and must be rewritten. *Rollback*: delete the test
      file.

- [ ] **CP2 — Config + writer only (no renderer change yet), and capture the BEFORE frame.**
      Add the four keys and the comment block; add `channel_display_from_config`; update
      **all four** writers (§8). **Before touching the renderer**, render step 0 of a
      **vision-range-2** cell to PNG with the OLD renderer and keep it — this is the only
      moment the "before" picture can be captured, and after CP7 re-records the cells it is
      gone (`plan-reviewer` M2). Pixel-comparing an old on-disk cell against a regenerated one
      would compare *different episodes anyway*: the campfire world was retuned on 2026-09-18
      (`2bfe158e`) and bush blocking changed on 09-14. So compare `layout_signature()` plus
      panel boxes, and use the PNG for human inspection rather than as a pixel oracle.
      *Detects*: `load_run_meta(...)['channel_display']` present and correct; parity suite
      **unchanged** (proves no key leaked into `load_env_params`); a deliberately wrong names
      length raises naming both numbers.
      *Rollback*: `git checkout` the affected files; regenerated cells are re-made by CP7.

- [ ] **CP2b — The two writer paths that are not the fixture script (C1, C2).**
      (a) Run `scripts/eval/eval_rollout.py --record` on a **post-change** config: it must
      write a recording carrying `channel_display`. Without the fourth call site this is a
      `TypeError`, which is the point of keeping the parameter required.
      (b) Run it on a **pre-change checkpoint** — `results/render_audit/olf1_vis3_spanfix/models/config.yaml`
      is a verified subject (it carries `visual_vector_size: 8` and none of the four new keys).
      *Detects*: it **must fail**, and the message must name the missing key and point at the
      remedy (§D7). A bare "key required but missing" fails this checkpoint. Record the exact
      output — it is the documentation of the accepted cost.
      *Rollback*: none (read-only invocations).

- [ ] **CP3 — The legacy path, on recordings that actually draw diamond maps.** Implement
      `labels.py`, `panels.py`, `painters.py`, `episode.py`, `__init__.py`. Render from
      **un-regenerated** recordings and **look at the frames**:
      (a) `results/render_audit/olf1_vis2_spanfix/recordings/77` (vision range 2) — must draw
      positional names "Channel 0…", **8 maps**, panel grown to fit, and must not raise.
      (b) `results/render_audit/olf1_vis3_spanfix/recordings/71` (vision range 3) — must
      **refuse**, with §D5b's message naming the reason and pointing at re-recording. A bare
      `LayoutOverflowError` fails this checkpoint.
      **Not `M1`/`M4`**: both read every sense at range 0 and draw the *rows* path, so they
      never exercise `_span` or `build_channel_maps` and cannot fail for the right reason
      (`plan-reviewer` M1). Render `M1` as well, to confirm the rows path still shows names.
      *Rollback*: `git checkout` the five renderer files.

- [ ] **CP4 — Vision dim 8, rendered THROUGH the production script, and looked at.**
      Regenerate a **vision-range-2** cell (`E2` or `E3`) and render it with
      **`scripts/eval/render_recordings_v2.py`** — not by constructing `EpisodeRenderer` in a
      scratch script. That script bypasses `from_recording` entirely (§4b), so a checkpoint
      that avoids it is the exact blind spot that would let this ship invisible on the only
      path that makes real videos (`plan-reviewer` C3).
      *Detects*: configured names on the frame (not "Channel 0"), **six** vision maps with
      terrain merged, unchanged widths versus CP2's before-frame and identical
      `layout_signature()`. Any difference at dim 8 is a regression, not an improvement.
      Also render `M1` through the same script for the rows path. *Rollback*: as CP3.

- [ ] **CP5 — Render at vision dim 1 and look at it.** Fix cells `E6sum`/`E6bin` (§A5),
      generate `E6bin`, render step 0 to PNG. *Detects*: **one map at normal size** (the same
      map-square pixel size as dim 8, not enlarged), **blank space beside it**, labelled with
      the configured name — not "Channel 0". *Rollback*: revert the fixture-script edit; the
      cell was never generated before, so nothing is lost.

- [ ] **CP5b — Render ABOVE the slot count, BOTH ways, and look at what actually happens.**
      This is the evidence §D4c's pending decision is made against, so it must exist as
      pictures, not description. Build throwaway cells at **vision range 2** and render step 0
      of each to PNG, **and run `render_layout_audit.py` on each beside a normal cell**:
      (a) **group kept, over-slot by count** — 12 vision channels, Terrain group present → 10
      maps into 6 slots;
      (b) **group deleted** — 8 channels, `visual_channel_groups: []` → 8 maps into 6 slots.
      This is the accidental case the how-to block invites, so it is the one most likely to
      occur in real life.
      Also render an **olfaction** over-slot cell, because the two senses fail oppositely
      (§D4c) and one frame cannot show both.
      *Detects*: (a) **where the extra maps go** — for vision, whether tiles 7–8 are clipped
      away leaving floating labels (the predicted outcome, and the one worse than what was
      agreed), and for olfaction whether they land on the vision panel; (b) that **nothing
      raises** and the **warning is emitted naming both numbers**, confirming §D4b's mechanism
      rather than assuming it; (c) which audit rules fire — recorded verbatim, including the
      expected result that the vision case produces **fewer** findings than a correct frame.
      *Report, do not fix.* If the vision case drops channels silently, that is §D4c's
      finding: put the frames in front of the user and let them decide. Do not loosen the
      audit, do not add a limit, and do not quietly change the sizing rule.
      *Rollback*: delete the throwaway cells; they touch nothing else.

- [ ] **CP6 — Full suites, deliberate breaks, and the config sweep.** Run the three dashboard
      files, the parity gates, `tests/scripts/test_render_recordings_v2.py` and
      `tests/env/test_dashboard_v1_imports.py`. Then three deliberate breaks, each reverted
      after:
      (a) a group naming **channel 9** → the write must **fail**, naming the bad index;
      (b) a names list one entry short → **fail**, naming both numbers;
      (c) `visual_channel_groups: []` at 8 channels → must **warn, not fail**, naming 8 maps
      against 6 slots (§D4b). A failure here would mean a limit crept back in.
      Then **sweep every maintained config under `configs/environment/`** through
      `channel_display_from_config` and record pass/fail per file.
      *Detects*: the validation is real rather than assumed, the warning fires where a
      refusal must not, and no maintained config — including any the parallel session has
      landed — is left unrecordable (§9b). *Rollback*: as CP3.

- [ ] **CP7 — Re-record the render-audit fixtures, keeping one legacy cell.** Regenerate the
      CP0.2 cells (`M1 M1x M2 M3 M4b M5 M6 M6b`, plus `M4r`, `W20`).
      **Deliberately leave `M4` un-regenerated** and say so here, so the legacy branch keeps a
      real on-disk subject; otherwise every legacy assertion in
      `test_render_recordings_v2` / `test_dashboard_frames` goes vacuous the moment the last
      cell is re-recorded, and the positional path is ungated from then on
      (`plan-reviewer` M4). The six `olf1_vis*` runs are also left alone and serve the same
      purpose for the diamond-map legacy path.
      *Detects*: **render one regenerated cell through `render_recordings_v2.py` and look at
      it** — real names on the frame. This, not the audit, is the check that can fail for the
      right reason: `render_layout_audit.py` renders only `v1`/`v2` and **refuses the
      dashboard renderer by design** (`:463-489`), so its frames carry the frozen V1/V2 label
      tables and say nothing whatever about this change (`plan-reviewer` M3). Keep an audit
      run only as a no-new-findings regression check against its own pre-change output.
      *Rollback*: fixtures live under gitignored `results/` and are regenerable from the
      script — but **copy the directory aside first** (`cp -a results/render_audit /tmp/...`),
      per the git-safety rule, because they are not in version control.

- [ ] **CP8 — Speed check.** Time `render_recordings_v2.py --benchmark` on one cell before
      and after, same host and cell. *Detects*: >5% slowdown warrants discussion, >15%
      blocks. Expected ≈0 — this moves table lookups to dict lookups at build time, not
      per frame.

---

## Q1 — `RECORDING_FORMAT_VERSION`: DECIDED, do not bump (user, 2026-09-19)

**Resolved.** Adding `channel_display` to `run_meta.pkl` is exactly the kind of change a
format version exists to mark, so it was put to the user rather than decided here. **The user
chose not to bump it.** `RECORDING_FORMAT_VERSION` stays at `1`; the renderer branches on
`meta.get("channel_display")` being present.

The reasoning, recorded so it is not relitigated: the thermal work set the precedent by adding
keys to this same payload without bumping; the stamp is written in two places and **read
nowhere** in the repo, so a bump changes nothing mechanically while creating a false signal
that old recordings are rejected or migrated when they are neither. A bump only earns its
keep alongside a real version check, which is separate work.

The original framing is kept below, because the argument is what makes the decision
re-checkable later.

**Recommendation as put to the user: do not bump**, following the precedent already recorded
in the source. When
the thermal work added two new keys to the recording payload it deliberately left the stamp
alone (`eval_recording.py:33-41`), reasoning that the reader must branch on
present-or-absent either way, so the bump would remove no code.

**What breaks either way:**

- **If not bumped** (recommended): nothing breaks. The renderer branches on
  `meta.get("channel_display")`, which is the mechanism decision #5 requires regardless.
  Cost: the stamp stays meaningless — but it already is, and that is an open registry item
  in its own right (`RECORDING_FORMAT_VERSION` is written in two places and **read nowhere**
  in the repo).
- **If bumped to 2**: still nothing breaks *mechanically*, because no code reads the stamp.
  The risk is the opposite one — it creates a false signal that old recordings are rejected
  or migrated when they are neither, and a future reader may trust it. A bump would only earn
  its keep alongside an actual version check, which is a separate piece of work.

---

## Review disposition

Where each `plan-reviewer` finding is answered. "Verified" means I re-checked the claim
against the code rather than accepting it.

| # | Finding | Disposition |
|---|---|---|
| C1 | Fourth `write_run_meta` caller missed | **Applied** — verified at `eval_rollout.py:1238` (import `:1231`). §8, gated by CP2b(a) |
| C2 | Writer does meet un-layered saved configs | **Applied** — the false safety claim in §D1 is corrected in place; cost accepted and costed in §D7; no fallback default; gated by CP2b(b) on a verified pre-change config |
| C3 | Production video path bypasses `from_recording` | **Applied** — new §4b covers all three sites; CP4 now renders **through** `render_recordings_v2.py`. Second exit condition checked and closed: `render_recordings.py` is the V1 path and never imports the dashboard package |
| C4 | Legacy rule reintroduces the width refusal | **Applied** — §D5b declares legacy vision range ≥ 3 unrenderable with a teaching message. Reviewer's path corrected: the recordings are at `results/render_audit/olf1_vis3_*/recordings/<pct>/`, **not** `results/render_audit/recordings/olf1_vis3_*`, which does not exist. Also corrected §D5's false "keeps exactly today's sizing" |
| C5 | No maps-vs-slots validation | **Withdrawn by the reviewer** after the user removed the ceiling. Superseded by the §D4b warning |
| C6 | Overflow is disappearance, not spillover (vision) | **Mechanism verified and documented** in §D4c — patches default to `clip_on=True`, `ax.text` to `False`, and one band Axes spans both senses. **Disposition pending the user**; CP5b renders both senses and both trigger paths |
| M1 | CP3/CP4 ran on range-0 cells | **Applied** — CP3 uses real legacy diamond-map recordings, CP4 a range-2 cell; both keep an `M1` render for the rows path |
| M2 | "Before" frame never captured | **Applied** — captured at CP2, with the reason pixel comparison is unsound recorded (worlds were retuned after those cells) |
| M3 | CP7's audit check cannot fail rightly | **Applied** — the audit refuses the dashboard renderer by design; CP7's real check is a render through the production script, audit kept only as a no-new-findings regression |
| M4 | Legacy assertion goes vacuous after CP7 | **Applied** — `M4` is deliberately left un-regenerated and named; the six `olf1_vis*` runs serve the diamond-map legacy path |
| M5 | Band-span test needs both regimes | **Applied** — §11 parametrises over configured/legacy and requires the off-standard test be **rewritten**, not updated |
| M6 | No missing-key test | **Applied** — §11, one per key, naming the key |
| M8 | Stale ceiling references | **Applied** — two survived my first revision (§A4 prose, §11 table) and are fixed. The `__init__` export and `panel_map_slots` docstring were already corrected. The how-to block's surviving "FAILS when the recording is written" refers to **group** validation, which remains true |
| M9 | Vision-dim configs inherit the 8-entry names list | **Applied** — §10's how-to gains an explicit warning block, §9b adds the coordination sequence with the parallel session, §9 fixes the dim-1 cells, CP6 sweeps every maintained config |
| L1 | Absent-field claim too strong | **Applied** — §A3 now states the worse case (a defaulted field is a silent fallback) |
| L2 | `_vision_dim` would duplicate entity data | **Applied** — §9 requires rewriting the resolved config's own lists |
| L3 | Signature prefix is pinned | **Applied** — §6 requires the new parameter come after the existing positional ones |
| O3 | Configs staged for **deletion**, not addition | **Verified and corrected** — §A6; CP0 re-measures and records whether the wide-sense cases skip |
| O5 | `E6bin` never built | **Verified** — no `E6*` directory exists and the cells fail to build; §9 fixes them, CP5 is the first real attempt |

## Implementation Report

> **Implemented by**: _(unassigned)_
> **Date**:

<!-- Filled by the `developer` agent. Must include:
     - the pre-change failure output for every new test (CP1)
     - the four PNGs from CP3/CP4/CP5 and what was seen in each
     - before/after speed numbers with host and cell (CP8)
     - any deviation from this plan, and why -->

## Verification Report

> **Verified by**: _(unassigned)_
> **Date**:

| File | Change | Status | Notes |
|------|--------|:------:|-------|
| | | | |

**Conclusion**:

---

## Feedback from plan-reviewer

**Verdict: NOT READY** (2026-09-19, reviewed at `fcd6faf2`). Full report with the probe and
per-finding exit conditions: [[plan_dashboard_channel_names]]
(`docs/reviews/plan_dashboard_channel_names.md`). The user's fixed decisions are respected;
none is re-litigated. Five Critical findings, in cost order:

1. **C3 — the production video script never receives the names.** `scripts/eval/render_recordings_v2.py:183-197, 223, 288` constructs `EpisodeRenderer` directly, not via `from_recording`, and is absent from File Changes. Every video would render positional names and 8 unmerged maps while CP4/CP5 go green through a different entry point. *Exit*: add the file (all three sites); CP4 renders **through** `render_recordings_v2.py`.
2. **C1 — four writer call sites, not three.** `scripts/eval/eval_rollout.py:1238` is missing; with the parameter required, `--record` crashes. *Exit*: add it to §8 and to a CP.
3. **C2 — the writer does meet un-layered configs.** `eval_rollout.py`'s common path (`--config <run>/models/config.yaml`, `:692, :959`) loads a frozen saved config with no `extends:` and no new keys, so `get_mandatory` raises for every pre-change checkpoint. [[SAVED_RUN_CONFIG_COMPAT]] is unimplemented. *Exit*: state the blast radius; sequence/register with the compat plan or record that pre-change checkpoints cannot be re-recorded until it lands; no fallback default.
4. **C4 — D5 reintroduces the width refusal.** Measured with the real packer: a legacy recording at vision range 3 draws 8 maps and needs 634 px against 520 px granted — `LayoutOverflowError`, on three on-disk recordings. D5's "keeps exactly today's sizing" is also false (today: 6 maps). *Exit*: user chooses the legacy rule for range ≥3; CP3 renders a legacy **diamond-map** recording (`olf1_vis3_spanfix`), not `M4` (range 0).
5. ~~**C5 — no check that maps drawn ≤ `PANEL_MAP_SLOTS`.**~~ **Withdrawn** after the user removed the ceiling and chose silent overflow (2026-09-19, mid-review). Replaced by **C6 — the sanctioned overflow has no gate, and for vision it is disappearance, not overlap.** §D4b cites `CP5b` twice but the Checkpoints list has no such entry. Map tiles go through `ax.add_patch` (clipped to the band card); labels are unclipped `Text`. So an over-slot **vision** run drops tiles 7–8 off the card with floating labels — the reader sees six maps and cannot tell there were eight; the audit sees no ink. Olfaction over-slot lands *inside* the vision panel (true overlap, audit reports it). *Exit*: write CP5b as a rendered vision-over-slot frame (with the group, and with the group removed), looked at by a human and described in the Implementation Report, with the audit output beside a normal cell. Also: state the carve-out's bound as "maps > slots" (not "channels > conventional"), note that legacy and configured recordings resolve that case differently (D5 grows; D4b overflows), and fix the audit scope note — over-slot vision yields *fewer* findings, so "no finding" is not "fine".

Post-revision additions: **M8** — four stale ceiling references survive the revision (`__init__` export of `CONVENTIONAL_MAX_CHANNELS`, the `panel_map_slots` docstring, the test table, and — the one that matters — the config how-to block, which still tells the user an oversized config "fails loudly"). **M9** — `E6bin` at `visual_vector_size: 1` inherits the 8-entry names list and the Terrain group from `default.yaml`, so §D3 validation raises and CP5 cannot generate the cell unless the override also sets a length-1 names list and `visual_channel_groups: []`; the same applies to every vision-dim config the parallel session owns under `basic/` — the how-to block must say "changing `visual_vector_size` requires redeclaring both keys". **C4 under the new decision**: legacy recordings still use D5's grow rule, so range-3 legacy still refuses; the alternative (overflow rule for legacy too) clips tiles 7–8 on *every* pre-change recording at range ≥ 1. User's call; CP3 must render `olf1_vis3_spanfix`, not `M4`.

Moderate: CP3/CP4 both run on range-0 cells (`M1`, `M4`) and never touch `_span`/`build_channel_maps`; CP4's "before" frame is never captured (and the campfire world was retuned yesterday, `2bfe158e`); CP7's audit check cannot fail for the right reason (the audit refuses the dashboard renderer by design); after CP7 no legacy fixture remains on disk; the band-span test's off-standard-width case becomes false on the configured path; the CONFIG_GUIDE contract's missing-key test is absent. Open: the git index shows `D` for both `olf1_vis{2,3}` configs — if they leave the tree, the band-span config cases skip and the CP0 baseline changes shape.

*Reviewed by: plan-reviewer*
