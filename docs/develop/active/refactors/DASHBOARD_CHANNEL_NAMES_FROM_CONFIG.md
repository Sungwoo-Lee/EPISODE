---
title: "Sensor channel names come from config, and sense panels get a fixed size"
topic: refactors
status: active
created: 2026-09-19
last_updated: 2026-09-21
---

# Sensor channel names come from config, and sense panels get a fixed size

> **Status**: PLANNED — not implemented. **No open questions.**
>
> **Read §A8 first.** The parallel vision-dim rollout landed in the working tree on 2026-09-20,
> mid-revision: the base config is now at **one** vision channel, not eight. Four parts of this
> plan were written against the old file and are corrected, and the agreed ordering in §9b has
> been overtaken — the developer reports and stops rather than editing those files.
>
> Carries seven user decisions: no recording-format version bump (§Q1); no channel ceiling;
> extra maps overflow the panel rather than being refused, with a warning naming both numbers
> when the display is built (§D4b); pre-change checkpoints cannot be re-recorded until the
> saved-config compatibility work lands, with no fallback default (§D7); legacy recordings at
> vision range ≥ 3 are declared unrenderable with a message pointing at re-recording (§D5b);
> the eleven standalone configs get the keys directly (§7b); and a trainer-start **backstop**
> — explicitly not a guard — fails a bad config in seconds rather than hours (§7c).
>
> **Five `plan-reviewer` passes.** The fifth was NOT READY on a single Critical that was a
> **git-safety hazard rather than a design defect** — CP2's rollback would have destroyed the
> other session's uncommitted rollout — and that hazard is **gone**: the rollout committed as
> `47b1b8c3` and `configs/` is clean, verified. The fifth pass re-derived both of the fourth
> pass's fixes independently and they hold in full.
>
> Findings and disposition are tabled in
> "Review disposition" below. The most serious is mine rather than the user's: **§D8** — the
> terrain merge became data in the config and in the layout but stayed a **constant in the
> painter**, so a group declaring channels `[1,2,3]` would have validated, drawn in the right
> place, and coloured itself from channels 0–2 with no error at all. Read the first two passes
> in the light of a design that still had a channel ceiling.
>
> The fourth pass found that **two of the third pass's own fixes rested on unverified
> premises** — §7b claimed these configs declare channel counts they do not, and four
> checkpoints needed an 8-channel world that no longer exists anywhere. Both are corrected, and
> the corrections were **measured before being written** rather than reasoned about: the
> 8-channel build route and the loader's channel assignment are demonstrated in §9.
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
   fail **when a recording is written** — loudly, and long before anything is drawn — rather
   than quietly changing the picture when the video renders. (It cannot fail at *config* load;
   §9b explains why, and an earlier draft of this sentence overstated it.)

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
   columns. ~~`default.yaml` ships both senses at range 0, so this is the path most maintained
   worlds actually draw.~~ **That justification is dead as of the rollout** (§A8): the base now
   reads smell at range 1 and vision at range 2, so **no maintained world draws the rows path
   at all** and a rows-path render needs an explicit range-0 cell (`plan-reviewer` M13d, M14).
   The decision to leave that path alone still stands — its panel size is already fixed, which
   is what the user asked for — but it now rests on scope, not on traffic.
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

**Correction, twice over.** An earlier draft said the other session had staged "two new
`05-campfire_thermal_10x10_olf1_vis{2,3}.yaml` worlds". That was inverted — they were
**deletions** — and as of `47b1b8c3` those deletions are **committed**, not staged. Neither
file exists.

**The consequence is measured, not predicted.** `tests/env/test_dashboard_band_span.py`
parametrises its wide-sense case over those two config paths and does a bare `pytest.skip`
at `:266` when a file is absent. Run today:

```
16 passed, 2 skipped
SKIPPED [1] tests/env/test_dashboard_band_span.py:266: …05-campfire_thermal_10x10_olf1_vis2.yaml not on disk
SKIPPED [1] tests/env/test_dashboard_band_span.py:266: …05-campfire_thermal_10x10_olf1_vis3.yaml not on disk
```

**The only two cases that exercised a non-zero vision channel count are silently skipping right
now.** This is the second demonstration in this plan of a gate stopping gating because a file
moved — the first was the same test's own history in `4b6f7196`. It is the argument for M10's
rebuild being **in memory with no config-file dependency and no skip path at all**: a test that
names a file on disk is one commit away from this, and absence of a subject must be a
**failure**, never a skip (§11).

### A7. Known-bug collisions (from `bug-curator`)

- **The height twin is open.** `panels._map_h` under-declares the painter's height need by
  36 px at every range, masked only by `layout.MIN_BAND_H = 200`, first biting at range 5.
  This plan edits `_span` (width) and `build_channel_maps` — the same two functions, other
  dimension. **Out of scope; do not absorb it.** Touching it silently would be unrequested
  scope growth on the exact functions whose disagreement broke every video last week.
- **`RECORDING_FORMAT_VERSION` is read nowhere** (`eval_recording.py:20`, written at `:85`
  and `:102`, no reader repo-wide). Do not expect the stamp to reject stale meta — see the
  decision recorded in §Q1.
- **`tests/env/test_backward_compat_configs.py` cannot detect a missing new key** in any
  maintained world: it skips any config whose load error says "is required but missing", and
  all eight `basic/` worlds use `extends:`. It will stay green regardless; it is **not** a
  valid gate for this work.

### A8. THE DIM-1 ROLLOUT HAS ALREADY LANDED — read this before implementing

**Committed as `47b1b8c3`** — *"default sensory becomes the ladder's Q2 arm (olf 1 / vis 2 /
vec 1 / clamp)"*. First seen 2026-09-20 as uncommitted working-tree work; **landed 2026-09-21,
and `configs/` is now clean** (no modified, staged or untracked files under it). That closes
the review's O11 — the rollout can no longer be amended out from under this plan without a
commit of its own — and it means the numbers below are a committed state rather than a
snapshot of somebody's editor. The same commit also **deleted** the two
`05-campfire_thermal_10x10_olf1_vis{2,3}.yaml` worlds and archived the 8-channel variants under
`configs/environment/experiment/archive/basic_vec8/`.

What the shipped base config now says:

| | Before (2026-09-19) | Now |
|---|---|---|
| `sensory.visual_vector_size` | 8 | **1** (`:256`) |
| `sensory.visual_background_properties` | 3×8 one-hot | **3×1, all `0.0`** — "at visual_vector_size 1 the visual sensor reports ENTITIES, not ground" (its own comment) |
| every entity's `visual_properties` | 8-wide one-hot | **`[1.0]`** — all seven entities write the same single channel |
| `sensory.olfactory_grid_range` | 0 | **1** (`:226`) |
| `sensory.visual_sensor_range` | 0 | **2** (`:237`) |
| `sensory.visual_blur_enabled` | false | **true** |
| `sensory.visual_value_mode` | `sum` | **`clamp`** |
| olfaction (`vector_size`, entity `properties`) | 5 | **5, untouched** |

**The two range changes are the ones with teeth**, and they are why §A2 item 3 and two
checkpoints had to be rewritten: with smell at range 1 and vision at range 2, **every
maintained world now draws diamond maps and none draws the range-0 rows path.**

**Four things in this plan were written against the old file and are corrected accordingly:**

1. **§10's vision how-to block** prescribed an 8-entry names list and `{Terrain, [0,1,2]}`.
   At one channel there is no terrain channel at all, so the shipped declaration is a
   **1-entry list and `visual_channel_groups: []`**. The block now shows both.
2. **The anchoring test** was specified as "`PANEL_MAP_SLOTS` equals the map count the shipped
   `default.yaml` draws". That is now **1**, not 6, so the test would fail by construction.
   Re-anchored in §11 to an explicit 8-channel reference display.
3. **CP4's "vision dim 8, unchanged from today"** no longer describes today. It must build an
   explicit 8-channel display rather than leaning on the base config.
4. **CP5's dim-1 case gets easier, not harder** — the base config *is* dim 1 now, so §A5's
   override gymnastics are only needed if the `E6` fixture cells are used.

**The slot constant does not move, and this is the moment it earns its keep.** `PANEL_MAP_SLOTS`
stays at `{Olfaction: 5, Visual: 6}`. A panel that shrank to the live channel count would now
draw vision as a single map across a one-map-wide panel, and a later return to 8 channels would
reshape it again — the exact instability the fixed size exists to remove. At one channel the
vision panel draws one map and leaves five slots blank, which is what the user asked for
("no care about black area").

**Consequence for the agreed ordering (§9b): the reconciliation is EMPTY, and the developer
proceeds.** An earlier draft of this paragraph told the developer to "report and stop". That
would halt the work on a non-event, and is withdrawn (`plan-reviewer` M13a). **No `basic/`
config redeclares `visual_vector_size`** — measured: all seven inherit `1` from the base — so
there is no per-file names list for the other session to add and nothing for them to
reconcile. The display keys go into `default.yaml` by *this* change, once, and the ladder
inherits them exactly as it inherits the width.

What replaces the halt is a check rather than a rule: **§11's sweep is the proof**, because it
resolves every maintained world and fails naming any file whose names disagree with its
resolved widths. If the other session later gives a ladder file its own width, the sweep is
what catches it. Note the ordering decision itself is now moot in practice — their rollout
landed first — and at one channel the base takes a **1-entry** list, not the 8-entry list this
plan originally drafted.

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

**How the constant is anchored.** A test builds an explicit 8-channel reference display with
`{Terrain,[0,1,2]}` and asserts the map count it draws equals `PANEL_MAP_SLOTS[sense]` (§11 —
**not** anchored to `default.yaml`, which now draws one map).

#### D4d. An oversized sensor range overflows INSIDE the panel — and range 4 is the boundary

**User instruction, 2026-09-21, in their words:** *"if the visual sensor range is too large,
let them oversized within the panel not the outside."* So an oversized **range** is contained:
the maps shrink to fit the width the panel already has, rather than the frame being refused or
spilling onto the neighbouring sense.

**This is coherent with §D4b rather than a new policy**, and it repairs the part of §D4c that
was worst. §D4b already says *draw, do not reject*. §D4c found that over-slot **vision** tiles
are clipped **off the card** with their labels left floating, so channels vanish with no ink
for the audit to report. "Inside the panel, never outside" is exactly the fix for that:
**containment instead of disappearance.** It also bounds the blast radius — nothing reaches a
neighbouring panel, so the audit's overlap findings stay meaningful and §D4b's scope statement
needs no further exception.

**Where it stops working, measured with the real packer** (`MAP_CELL_MIN_PX = 10`,
`MAP_GAP_PX = 6`, `PAD = 16`, six slots, 520 px granted):

| Vision range | Need at 6 slots | Contained cell size | Verdict |
|---|---|---|---|
| 2 | 362 px | 15.3 px | draws |
| 3 | 482 px | 10.9 px | draws |
| **4** | **602 px** | **8.5 px** | **below the painter's 10 px floor** |

At range 4 the panel is granted 520 px against a 602 px need, and containing the maps inside
it drives each map square to 8.5 px — under `painters.py`'s `if cs < 10: raise`, which exists
because a map square below 10 px is unreadable. **So at range 4 "inside the panel" and "always
draws" genuinely conflict, and the painter refuses**
(`LayoutOverflowError: visual needs 602px of width in the band; 2 children share 1056px,
giving it 520px` — measured, not predicted).

**This is a documented boundary, not a feature to build now.** The user said they will ask for
a fix if the setting is ever needed. Recorded plainly so it is not met as a surprise: **fixed
panel size caps renderable vision range at 3 under the current band split**, for configured and
legacy recordings alike, where today's live-count sizing would render a 1-channel range-4 world
in 122 px. The fixture script's `E8` cell (range 4) is exactly such a world. Lifting the cap
means the need-proportional band split the user declined earlier, and that is its own change
with its own render proof — the open height-twin bug lives next door (§A7).

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

> **Settled, 2026-09-19 — this is a recorded consequence, not an open question.** The user's
> governing reasoning, in their terms: today's channel counts **are** the conventional
> maximum, so exceeding them is off the normal path by construction, and no shipped world
> does it. The behaviour therefore stands exactly as decided in §D4b — no limit, a warning
> naming both numbers when the display is built, still draw — and what follows is written
> down so that a future
> reader who meets such a frame **finds the explanation instead of filing a bug**. Do not
> reopen it. (Measured under `plan-reviewer` C6.)

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

**What that means in practice, for whoever meets such a frame.** For vision, an over-slot
config produces a frame that is not obviously broken: it shows six maps and some labels with
no tiles under them, and it *under-reports the agent's observation* without the audit seeing
anything. That is a strange thing to encounter cold, which is the whole reason it is written
down here. **It is reachable only off the conventional path** — every shipped world is at or
below the slot count — and the warning at load (§D4b) is what points a reader from the frame
back to the config that caused it.

**The carve-out's bound is `maps > slots`, not `channels > conventional`.** The two differ
whenever grouping changes: 8 channels with the Terrain group are 6 maps (fits), and the same
8 channels with the group deleted are 8 maps (overflows). Stating the bound in channels would
mis-describe which configs are affected.

**Legacy and configured recordings resolve this case differently, deliberately.** A legacy
recording **grows** its panel (§D5) and therefore never reaches this state; a configured one
**overflows** (§D4b). Applying the overflow rule to legacy instead would clip tiles 7–8 on
*every* pre-change recording at vision range ≥ 1 — every fixture on disk — which is why §D5
exists.

**Refinement, 2026-09-19: warn when the display is built, still draw.** ("Load" is the word
this plan's whole residual turns on — §D7 and §9b both hinge on what does and does not happen
at *config* load — so it is not reused here. The warning fires when the `ChannelDisplay` is
constructed, **once per sense per run**, not per frame.) The decision above stands unchanged —
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

**The predicate is NEED versus GRANT — never the sensor range** (`plan-reviewer` M12). A legacy
panel needs `maps × (2r+1) × 10 + 6 × (maps−1) + 32` px, where `maps = max(slots, drawn)`, and
it is refused exactly when that exceeds what the band grants it.

**Why range is the wrong key, measured.** At **8** maps and range 3 the need is
`8×7×10 + 6×7 + 32 = 634` px against the 520 px granted — refused, and that is the case this
section was written for. A **1-channel** legacy recording at range 3 is sized by §D5's
`maps = max(slots, drawn) = max(6, 1) = 6`, so it needs `6×7×10 + 6×5 + 32 = **482** px` — it
fits, and it renders. (An earlier draft of this paragraph said 102 px, computing one map
instead of six and contradicting §D5 one paragraph above; the conclusion is unchanged, the
arithmetic is corrected — `plan-reviewer` M19.) Since the rollout, a 1-channel legacy recording at range 3 is an
ordinary thing to have — the `E7` cell recorded from today's tree before this lands **would be**
one (no such recording exists on disk today: `results/render_audit/` holds only the `M*` cells,
`W20` and the six `olf1_vis*` runs) — and a `range ≥ 3` rule would refuse a recording that
renders perfectly well. **State the
rule as need-versus-grant and the range drops out of it.**

**User decision, 2026-09-19: declare the ones that genuinely do not fit unrenderable,
explicitly.** The alternatives put to the user were a need-proportional band split (a layout
change with its own render proof, and the open height-twin bug lives next door — §A7) and
letting the frame overflow. They chose the explicit refusal. That decision is unchanged; only
the predicate that selects which recordings it applies to is corrected here.

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

- The **range-0 rows path** (`build_channel_rows`) — §A2 item 3. **It ignores channel groups
  deliberately**, and that is recorded here so nobody later "fixes" it to merge them: a group
  is a *map*-layout concept, and the rows path draws one labelled row per channel with no maps
  at all. It reads `zip(setters, vec)` positionally (`painters.py:625`), which stays correct
  under this change. Since the rollout no maintained world draws this path at all (§A8), so it
  is both out of scope and untrafficked.
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

**What does not break.** Runs whose config reaches the keys record normally — that means every
config that resolves them through `extends:`, **plus** the standalone configs this change edits
directly (§7b). It is **not** "every run trained after this change": a standalone config
inherits nothing, which is exactly why §7b exists, and an earlier draft of this sentence
overstated the guarantee. Rendering **already-recorded** episodes is unaffected either way —
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

#### D8. The merged map must read the channels its group NAMES — the defect this plan nearly shipped

**This is the finding that matters most, and it is mine, not the user's.** My design moved
*how many maps* into data and left *which channels the merged map reads* as a constant in the
painter. Verified at `painters.py:701-711`:

```python
if kind == "terrain":
    off = float(np.max(row[:3])) <= 0
    patch.set_facecolor(P.OFF_WORLD if off
                        else P.TERRAIN_FILL[int(np.argmax(row[:3]))])
```

`row[:3]` is a **literal slice** and `P.TERRAIN_FILL` (`palette.py:131`) is a hardcoded
three-colour tuple. So a config declaring `{name: Terrain, channels: [1, 2, 3]}` passes every
validation in §D3, is placed by `map_plan` at the run's first position — and then **colours
itself from channels 0–2**. No error. Wrong picture. A group of length 2 or 4 is equally
silent: the painter reads three channels regardless.

**That is precisely the quiet-mistake class the user commissioned this plan to make
impossible** ("I'm worry about any potential quiet mistake"), sitting on the step I had myself
named the riskiest. Count discipline — one `panel_map_slots` call shared by registry and
painter — guarantees the two agree on *how many* maps. It says nothing about *which channels*
one of them reads. The invariant was unstated, so it was unprotected.

**The fix, in three parts:**

1. **`map_plan` carries the group's channels.** Its tuple becomes
   `(name, qualifier, kind, channel_or_channels)` — for a group, the declared index tuple; for
   a plain channel, its index as today. The painter then has the answer rather than assuming
   it.
2. **The painter never writes a literal slice.** `row[:3]` becomes `row[list(channels)]`, and
   the colour index is the position *within the group*, not within the vector. A channel
   index may never again be spelled as a constant in `painters.py`.
3. **Group length versus palette arity is validated**, at write time, naming both numbers —
   `P.TERRAIN_FILL` has three colours, so a 4-channel group has no fourth colour and must be
   refused rather than silently reusing one. (Generalising the palette instead is the larger
   alternative; it is not needed while the only shipped group is terrain, and a refusal that
   names the limit is honest where a wrapped colour is not.)

**Note this is a refusal, and deliberately so** — it does not contradict §D4b's no-limit
decision. That decision was about *how many channels a sense may declare*. This is a group
naming more members than the palette can colour, which is a malformed declaration in the same
family as a group naming a channel that does not exist, not a request to draw more than fits.

**Gate: CP6 gains a shifted-group render that a human looks at.** A unit test asserting the
painter reads the right indices would be written by the same reasoning that produced the bug.
The check is a frame from a config declaring `{Terrain, [1,2,3]}` on an 8-channel display: the
merged map must show the colours of channels 1–3, and a reader must be able to see that it
differs from the `[0,1,2]` frame.

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
    def from_meta(cls, sense, n_channels, meta_entry, *, key_present: bool):
        """`key_present` is whether run_meta carried a top-level `channel_display`
        AT ALL -- NOT whether this sense has an entry in it. The two stopped being
        the same thing when names became required only for ENABLED senses (7b): a
        perfectly good configured recording legitimately has no `Visual` entry.

        Keying legacy off the per-sense entry would hand positional names to three
        unlike cases -- a pre-change recording, a disabled sense, and a forgotten
        or hand-edited entry -- and the third silently ships "Channel 0" on an
        enabled sense, which is the one name this module promises can never reach
        a frame (M20).
        """
        if not key_present:                      # genuinely pre-change: legacy
            return cls(tuple((f"Channel {i}", "") for i in range(n_channels)), (), True)
        if meta_entry is None:                   # configured, but this sense missing
            raise KeyError(
                f"run_meta carries channel_display but has no entry for {sense!r}, "
                f"which is enabled on this recording. A configured recording must "
                f"name every sense it draws.")
        ...  # validate length/indices, raise ValueError naming both numbers

def map_plan(sense, display: ChannelDisplay) -> list[tuple[str, str, str, object]]:
    """Which maps a sense draws: [(name, qualifier, kind, channels), ...].

    A grouped run of channels becomes ONE map of kind "terrain"; every other
    channel is its own "seq" map at its own index.

    The last element CARRIES THE GROUP'S OWN CHANNEL TUPLE -- an int for a plain
    channel, the declared tuple for a group. The painter must read exactly these
    and never a literal slice: a group is data now, so `row[:3]` would colour
    {Terrain, [1,2,3]} from channels 0-2 with no error at all (see D8).
    """

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
- **The terrain branch (`:701-711`) must stop reading a literal slice — §D8.** `row[:3]`
  becomes `row[list(channels)]`, where `channels` is the group's declared tuple carried on the
  map plan, and `P.TERRAIN_FILL` is indexed by position **within the group**. Today's
  `{Terrain, [0,1,2]}` must render byte-identically after this change; `{Terrain, [1,2,3]}`
  must render *differently*, which is what CP6's shifted-group frame checks. **No channel
  index may be spelled as a constant anywhere in this file** — that is the invariant D8 exists
  to establish, and it is the one a future edit is most likely to break.
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

#### 7b. The eleven standalone configs — they inherit nothing (C7)

**User decision, 2026-09-19: add the four keys to the standalone configs**, chosen over
declaring them unrecordable and over a split rule. Each declares its own `sensory:` block with
**no `extends:`**, so it inherits nothing from `default.yaml` and would otherwise raise at
`write_run_meta` the first time anyone recorded from it.

**Correction (2026-09-21, `plan-reviewer` C9): these files do NOT carry their own vision
count, and the earlier sentence here claiming they carry "their own channel counts" was false.**
Re-measured per file, values not line counts:

| What | Measured | Where it really comes from |
|---|---|---|
| `sensory.vector_size` (olfaction) | **5, declared in all eleven** | the file itself |
| `sensory.visual_vector_size` | **declared in none of them** | the loader's non-mandatory fallback, `config_loader.py:1687-1688` (`.get(..., 8)`) |
| per-entity `visual_properties` | **declared in none of them** | the loader's auto-generated one-hot at V=8 |
| `visual_sensor_enabled` | `false` in `olfaction_parity_{neutral,predator}`, `true` in the other nine | the file itself |

**A number in the relayed brief was wrong and is not implemented.** It reported
`vector_size` as **1** in all eleven. It is **5** — confirmed twice, by reading the values
(`vector_size:5` in every file) and by resolving them (`olf=5` for all eleven on 2026-09-20).
The "1" is a line **count** — an earlier probe of mine printed `vector_size_lines=1`, meaning
one matching line — read as a value. Acting on it would have put a 1-entry olfaction list into
eleven configs that each have five olfaction channels, failing validation on every one. The
review itself states this correctly ("the eleven declare olfaction's count and inherit vision's
from the loader's default"); the error entered in relay.

**So the required lengths are read from resolved `EnvParams`, never from the file.** That is
the discipline C9 exists to enforce: these files are largely silent about their own widths, so
what a file "appears to say" is not evidence. `channel_display_from_config` already validates
against `params.olfactory_vector_size` / `params.visual_vector_size`, which is the correct
source; §7b's instruction is to derive each list's length from those resolved numbers.

**Names are required only for senses that are ENABLED** (user decision, 2026-09-21).
`channel_display_from_config` reads a sense's two keys **only when that sense is on in the
resolved params** — `olfactory_enabled` and `visual_sensor_enabled` are both static `EnvParams`
fields (`state.py:282, 285`), so this is evaluable — and the payload carries no entry for a
sense that is off. Three consequences:

- `olfaction_parity_{neutral,predator}.yaml` take **olfaction names only**. Under the previous
  instruction they would have been given eight vision names for a sense that is switched off —
  which is the quiet mistake this section exists to prevent.
- **The `q_learning.yaml` exclusion is structural rather than remembered — but NOT because of
  `using_sensory`.** That key is read by no code (`plan-reviewer` M16); the exclusion rests on
  the two reasons given below, both structural: it is outside §9b's sweep roots, and it cannot
  resolve to `EnvParams` at all. The nine vision-enabled files still need both lists.
- **The sweep must check a sense only when that sense resolves enabled** (§11). Demanding
  vision names from the two parity files would fail on correct files; skipping them silently
  would hide a real omission later. Enablement is the discriminator, and it is read from
  resolved params.

**Verified present and `extends`-free (2026-09-20):**

```
configs/continual/nmn_double_return_stages/0{1,3,5}_active_predator.yaml
configs/continual/nmn_double_return_stages/0{2,4}_passive_predator.yaml
configs/verification/observability_gates_S{1,2,3,4}.yaml
configs/verification/olfaction_parity_{neutral,predator}.yaml
```

All eleven **resolve** to `olfactory_vector_size = 5` and `visual_vector_size = 8`, so the nine
vision-enabled files take a 5-entry olfaction list plus an **8-entry** vision list with
`{Terrain, [0,1,2]}`, and the two parity files take the olfaction list alone. Note this differs
from `default.yaml`, which is now at one vision channel (§A8) — **do not copy one file's block
into the other.**

**The 8-entry list is only correct because it matches a loader default nobody wrote down.**
Those files declare no entity `visual_properties`, so the channel assignment is the loader's
auto-generation. The developer **confirms each file against its resolved params' per-entity
`argmax`** rather than copying the how-to block — the reference table is a description of a
default, not a specification, and this plan has already been bitten once by treating an
apparent declaration as evidence.

**`configs/models/q_learning/q_learning.yaml` is EXCLUDED, for two structural reasons — and
`using_sensory` is NOT one of them.** It is an *agent* config rather than an environment one
(it sits with `ppo.yaml` / `dqn.yaml` under `configs/models/`, and the only references to it in
the repo are docs listing agent configs), so **§9b's sweep roots exclude it by construction**;
and it **cannot resolve to `EnvParams` at all** — it fails `load_env_params` on
`sensory.visual_sensor_range`, so it never reaches the enabled-sense rule in the first place.

**An earlier draft justified this by `using_sensory: false`. That was wrong: no code reads
`using_sensory`** — it appears only in test-fixture YAML strings, and the loader keys
enablement on `sensory.olfactory_enabled` / `sensory.visual_sensor_enabled`
(`plan-reviewer` M16). Justifying an exclusion by a key nothing consults is the same mistake
this thread keeps finding, so it is named rather than quietly replaced.

The justification before *that* — "it declares no channel count" — also did not survive
measurement: none of the eleven declares a vision count either. Three attempts, and the two
that hold are both structural.

**Why this is safe for the byte-parity gates — checked, not assumed.** The gates run an episode
and compare it against a stored fixture; neither `test_unified_parity.py` nor
`test_thermal_parity.py` contains `sha256`, `hashlib` or `md5`, so no config is hashed. The four
keys are never read by `load_env_params` — they are read at recording-write time by
`channel_display_from_config` — so the traced environment, the episode, and therefore every
fixture are untouched. **This is the whole reason the carriage is `run_meta.pkl`**; if adding an
inert key to these files moved a fixture, the carriage decision itself would be wrong and the
developer must stop and report rather than regenerate fixtures.

#### 7c. A trainer-start BACKSTOP — not a guard (M11)

**Approved by the user**, and named precisely: at trainer start, when checkpoint recording is
enabled, resolve the display once and let it raise. It turns "fails hours into a GPU run, at
the first checkpoint video" into "fails in the first seconds".

**Call site:** `train.py`, before the training loop — the recording branch is
`if eval_v_flag:` at `train.py:2552`, whose `evaluate_jax_checkpoint(..., render_video=True,
...)` call spans `:2557-2560` (its stats-only twin at `:2575`). Line numbers drift; locate the
branch, not the line. Resolve `channel_display_from_config(config, params)` during setup, after the
env config resolves, and discard the value; it exists to raise early.

**It is a backstop, not a guard, and the plan says so in those words.** It gives **zero
commit-time coverage** — nothing fails until somebody launches a run — and it **never reaches
the verification configs** in §7b, which are never trained. The peer who proposed it tested it
against exactly this case and retracted the stronger claim themselves. The real coverage for
the standalone class is §7b's edit plus the committed sweep test in §11; this only shortens the
feedback loop for the configs that *are* trained.

**Optional, and cheap if taken**: as specified the backstop resolves **stage 0 only**, so a
curriculum whose later stage changes a sense width would still fail at that stage's first
video. `train.py:869` already loads every stage's params, so resolving the display for each
stage at start costs nothing extra (`plan-reviewer` L7). Left optional because it widens a
backstop rather than closing a gap in the real coverage.

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
- **`E6sum` / `E6bin` need no fixing any more** (`plan-reviewer` M13b). They set
  `visual_vector_size: 1` on a base that is **already** 1 with matching entity vectors, so they
  build today — verified 2026-09-21: `E6sum`, `E6bin`, `M1` and `E2` all resolve
  `olf=5 vis=1 olf_range=1 vis_range=2`. §A5's override recipe stands only as the record of what
  a *width change* costs.

- **`_vision_dim(V)` must work in BOTH directions, and the grow direction is the one the plan
  needs** (`plan-reviewer` C10). Every fixture cell is now 1-channel, so **there is no
  8-channel world anywhere** — and the archived `basic_vec8/` set cannot supply one: its files
  are refused outright by `_require_maintained` (`:366-377`, which allows only `default.yaml`
  and `basic/`), and its chain is broken anyway because `basic_vec8/05-campfire_thermal_10x10`
  extends the **live** `basic/04-jump_attack_10x10`, now 1-channel. Do not migrate them; that
  is the never-resurrect-archived-configs rule.

  - **Shrinking (V < 8)**: set `sensory.visual_background_properties` to a 3×V table and
    replace all three entity lists (`environment.resources`, `environment.entities`,
    `environment.obstacles`) with length-V `visual_properties` / `visual_properties_std`.
  - **Growing to V = 8**: **strip** `visual_properties` and `visual_properties_std` from every
    entity and leave `sensory.visual_background_properties` absent, so **the loader's own V=8
    auto-generation supplies the layout**. `config_loader.py:1748-1754` permits absence only at
    width 8 — the one width where it is allowed — so this is one source of truth (the loader's
    table), not a hand-copied entity list.

  **Verified end-to-end, 2026-09-21**, because this route was an undemonstrated assumption
  (the review's O9/O10) and the last Critical existed because a fix rested on one. Stripping
  the three lists wholesale and setting width 8 loads cleanly (`vis=8 olf=5`), and the loader
  assigns exactly the reference table: **food → 3, hiding_predator → 4, predator → 5,
  rabbit → 7, all obstacles → 6**, background rows grass → 0, sand → 1, plain → 2. So the
  8-entry names list in §10 is confirmed against the loader's real output rather than asserted.

- **Set the two display keys in the same override** — an 8-entry `visual_channel_names` and
  `{Terrain, [0,1,2]}`. Both keys exist in `default.yaml` after CP2, so the script's
  override guard (which refuses any key the config lacks) allows them.
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

**This section is now history plus one live rule** (`plan-reviewer` M18 — its previous text
survived the §A8 correction and contradicted it). The rollout **has landed**, as `47b1b8c3`:
`visual_vector_size: 1` is set **once, in `default.yaml`**, and **no `basic/` file sets it at
all** — all seven inherit. So there is no per-file list for anyone to add, nothing to
reconcile, and the ordering question is moot.

**The live rule is the one that outlives the rollout**: a config that sets its own sense width
must declare that sense's names in the same file, because a child replaces a list wholesale or
not at all and cannot shorten an inherited one. That failure surfaces at recording-write time,
not at config load — so a mismatched config trains perfectly well and fails at its first video,
which is the worst time to find it. §11's sweep is what catches it at commit time instead.

**This plan does not edit those files** (they belong to the other session).

**The ordering decision is closed by events.** The user chose "this change lands first" over
letting the ladder rollout land first and over making the display keys optional per config —
the last rejected for the same reason the code tables are being deleted: an optional key with
an inherited value *is* a fallback default, and it would let a dim-1 world silently render
another world's channel names. That rejection still stands. The sequencing does not: **their
rollout landed first, in `47b1b8c3`.**

**What the developer does now: proceed.** The earlier instruction to *report and stop* is
**withdrawn** — it would halt the work on a non-event, since there is nothing left to
reconcile. Add the four keys to `default.yaml` once; the ladder inherits them exactly as it
inherits the width. §11's sweep is the proof, and it is what catches any future ladder file
that gives itself its own width.

**Where the failure surfaces, stated precisely — because "fails at load" is not available.**
The natural request is that a ladder config with a mismatched names list fail at config load,
naming the file and both keys. **It cannot fail in `load_env_params`**: a new key there is
read by the parity gates, which load ~38 standalone configs raw with no `extends:` resolution
(§A3), and that is the exact breakage the `run_meta` carriage exists to avoid. Putting the
check there would trade a display bug for a red gate on 38 configs the project does not
maintain.

So the failure is loud in the two places it can be:

- **At record time** — `channel_display_from_config` raises, naming the config, the declared
  channel count, and the names-list length. This is the real gate: it is impossible to write
  a recording whose names disagree with its channels.
- **In CI, permanently** — this change **commits a new test** (it does not exist yet) that
  sweeps the maintained env-config roots through `channel_display_from_config` and fails
  **naming the file and both keys** (§11). This is what catches a ladder config the moment it
  lands, rather than when somebody later tries to make a video, and it must be committed
  rather than left as CP6's one-off sweep because the configs it guards are still being
  written.

  **Scope, measured 2026-09-20 rather than asserted.** Copy the collector in
  `tests/env/test_backward_compat_configs.py:24-42` — it globs `configs/environment/experiment/**`
  (with the `archive/` exclusion whose docstring quotes the maintenance policy),
  `configs/continual/**`, `configs/verification/**`, plus `configs/environment/default.yaml`.
  Glob, never a hand-written list. That collects **32** files today, of which **19 resolve to
  `EnvParams`** and are validated; the other 13 are curriculum *schedules* under
  `configs/continual/` that are not env configs at all and fail on an unrelated missing key.
  **Copy the glob, NOT the collector's loader** — its loader is a raw `Config` with no
  `extends:` resolution, which would resolve only 12 of the 32 and skip all seven ladder
  worlds. Use the resolving loader.

  **A floor alone is not enough, because it catches removals and not additions**
  (`plan-reviewer` M15). With skip-on-load-error, a **new** `basic/07-*.yaml` that fails to
  load is skipped, the count stays ≥ 19, and the sweep is green on a maintained world it never
  checked. So the rule is by location, not by outcome:

  - **Skip is permitted only for files directly under `configs/continual/`** — the 13
    curriculum schedules, every one failing on `sensory.visual_value_mode is required`.
  - **Every file under `configs/environment/**`, `configs/verification/**` and
    `configs/continual/nmn_double_return_stages/` must resolve, or the test FAILS naming the
    file.**
  - **A `channel_display_from_config` raise is always a failure, never a skip** — that is the
    condition the test exists to detect.
  - Keep both floors (collected ≥ 32, validated ≥ 19) on top of the location rule.
  **`configs/models/**` is deliberately outside those roots**: `q_learning.yaml` carries a
  stray `sensory:` block and no channel counts at all, so a content-based `^sensory:` sweep
  over `configs/**` would collect an *agent* config — one that cannot resolve to `EnvParams`
  in the first place (it fails on `sensory.visual_sensor_range`) and so would fail the sweep
  for a reason having nothing to do with channel names.

The honest cost of this arrangement: a mismatched config **loads and trains perfectly well**
and fails only at evaluation or in the sweep test. That is stated in the how-to block too, so
nobody is surprised by it.

#### 10. `configs/environment/default.yaml` — the four keys and their how-to block

Inserted in the `sensory:` block: the olfaction keys after `vector_size: 5` (line 207), the
vision keys after `visual_vector_size: 1` (line **256** — the rollout moved it; re-check before
editing rather than trusting this number). **The comment block is a deliverable in
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
  # exactly `visual_vector_size` entries -- ONE here, because this world now runs
  # single-channel vision. The 8-channel table further down is kept as the
  # reference for configs that set a wider vision, since the dimension is an
  # experimental knob and moves between studies.
  #
  # ►► IF YOU CHANGE visual_vector_size, YOU MUST REDECLARE BOTH KEYS IN THE SAME
  # FILE. A config that sets `visual_vector_size: 1` and says nothing else still
  # INHERITS this 8-entry list and the 3-channel Terrain group below, because a
  # child config replaces a list wholesale or not at all -- it cannot shorten one.
  # The mismatch is caught when a recording is written (8 names against 1 channel)
  # and by a test that sweeps every maintained config, which names the offending
  # file and both keys. It is NOT caught at config load -- so a mismatched config
  # loads and trains perfectly well, and only fails later, at eval. Know that
  # before you edit: a training run can get all the way to its first video.
  #
  # A 1-channel vision config needs BOTH of these, beside its size, in the SAME
  # file that sets the size:
  #     visual_vector_size: 1
  #     visual_channel_names:  [{name: "Visible", qualifier: ""}]
  #     visual_channel_groups: []     # no terrain merge: there is no channel 1 or 2
  # The same applies to the smell keys and `vector_size`.
  #
  # WHICH CHANNEL IS WHICH -- AS THIS FILE STANDS (one channel).
  # Every entity below carries `visual_properties: [1.0]`, so they ALL write the
  # same single channel, and `visual_background_properties` is three rows of 0.0 --
  # the ground contributes nothing. So channel 0 does not mean "grass" or "food";
  # it means "something is here". Name it for what it reports:
  #   channel 0  every entity writes 1.0; ground writes nothing  -> "Visible"
  # There is no terrain channel to merge, which is why the group list is empty.
  #
  # WHICH CHANNEL IS WHICH -- AT THE 8-CHANNEL WIDTH (the reference layout).
  # Kept because the vision dimension is varied between studies and a wider config
  # needs to know the column order. Entities carry a one-hot `visual_properties:`,
  # and channels 0-2 come from `visual_background_properties`, whose three rows are
  # grass / sand / plain in that order:
  #   channel 0  grass      visual_background_properties row 0   -> "Grass"
  #   channel 1  sand       row 1                                -> "Sand"
  #   channel 2  plain      row 2                                -> "Plain"
  #   channel 3  food       visual_properties: [0,0,0,1,0,0,0,0] -> "Food"
  #   channel 4  hiding_predator                                 -> "Hiding predator"
  #   channel 5  predator                                        -> "Predator"
  #   channel 6  rock AND tree AND bush all write here           -> "Obstacle"
  #   channel 7  rabbit (class neutral)                          -> "Neutral"
  # At that width the declaration is the 8-entry list plus
  #     visual_channel_groups: [{name: "Terrain", channels: [0, 1, 2]}]
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
    - {name: "Visible", qualifier: ""}   # one channel: "something is here"
  # ── MERGING CHANNELS INTO ONE MAP ───────────────────────────────────────────
  # A group draws several channels as a SINGLE map instead of one map each. Terrain
  # is grouped because a square is grass OR sand OR plain and never two at once, so
  # three separate maps would each be blank wherever the other two are not.
  #   name:     what the merged map is called on screen
  #   channels: which channel indices it covers -- must be a contiguous run, each
  #             index must exist, and no channel may appear in two groups
  # A group naming a channel that does not exist FAILS when the recording is
  # written. It cannot silently change how many maps the video draws.
  # Empty HERE because single-channel vision has no terrain channels to merge.
  # At the 8-channel width this reads:
  #     - {name: "Terrain", channels: [0, 1, 2]}
  # The channels a group names are the channels the merged map READS -- declaring
  # [1, 2, 3] draws a map coloured from channels 1-3, not 0-2.
  visual_channel_groups: []
```

#### 11. Tests

| Path | What it must assert |
|---|---|
| `tests/env/test_dashboard_channel_display.py` (new) | length mismatch raises naming both numbers; out-of-range / duplicate / non-contiguous group raises; absent payload gives positional names and no groups; **`_span` returns the same width at 1, 8 and 12 channels**; an over-slot channel count **does not raise** (§D4b — the absence of a refusal is the decision, so it is asserted explicitly); a legacy payload with 8 maps is sized to 8, not 6 (§D5). **Anchor `PANEL_MAP_SLOTS` to an explicit 8-channel reference display with `{Terrain,[0,1,2]}`, NOT to `default.yaml`** — the base config now runs one vision channel and draws **1** map (§A8), so the original "equals what the shipped config draws" formulation would fail by construction |
| `tests/env/test_dashboard_channel_display.py` (group-channel cases, §D8) | **The invariant the plan nearly shipped without.** `map_plan` returns the group's declared channel tuple, not a position; a group of a length the palette cannot colour is **refused at write time naming both numbers**; and — the one that would have caught the bug — a display with `{Terrain,[1,2,3]}` produces a map plan whose merged entry reads channels 1–3. Assert against the returned channels, never against `row[:3]`-shaped reasoning, since that is the assumption under test |
| `tests/env/test_dashboard_band_span.py` | update the `channel_labels` import (54) and `_painter_map_count` (98) / `_ctx` (~78) to the new API. **The equality property must be parametrised over BOTH sizing regimes** — configured (`slots`) and legacy (`max(slots, drawn)`) — since post-change they are different functions (`plan-reviewer` M5). **`test_an_off_standard_vision_width_is_declared_one_map_per_channel` (213) must be REWRITTEN, not updated**: "4 channels ⇒ 4 maps" becomes **false** on the configured path (4 configured channels ⇒ 6 slots; 4 legacy channels ⇒ `max(6,4)` = 6) |
| `tests/env/test_dashboard_band_span.py` (the wide-sense case, M10 + M12) | **Rebuild `test_a_world_that_reads_both_senses_wide_packs_and_paints` (262) entirely in memory — `default.yaml` plus range *and* width overrides, with an explicitly configured display — so it has NO config-file dependency and NO skip path.** Its two named config cases were deleted by `47b1b8c3` and it is skipping **right now**, measured, not argued (§A6): that is the second time this same test has stopped gating because a file moved. **Absence of a subject must be a failure, never a `pytest.skip`** — delete the `:266` skip, do not re-point it at other files, because any file named on disk is one commit away from repeating this. Three cases, all in-memory: configured range-3 declares six slots = **482 px** against the 520 px grant and packs; **8-channel legacy** range-3 is **refused** (634 px > 520); **1-channel legacy** range-3 **renders** — it is sized by `max(6,1) = 6` maps = 482 px, not the 102 px an earlier draft of this row claimed (`plan-reviewer` M12, M19). The third case is what stops the refusal being keyed on range. Build the legacy mirror at width 8 in memory; `_ctx` (`:76-86`) already does this |
| `tests/env/test_dashboard_channel_display.py` (source invariant, L6) | One assertion making §D8's rule structural instead of prose: **`"row[:" does not appear in `painters.py`'s source**. The project already uses this pattern — `test_dashboard_band_span.py:224-238` pins `MAP_GAP` by reading the painter's source. Cheap, and it is the only thing that stops the *next* literal channel index |
| `tests/env/test_dashboard_channel_display.py` (missing-key cases) | **one test per new key**: delete the key from a resolved config and assert `ValueError` **naming that key**. Required by CONFIG_GUIDE Maintenance Contract item 3, which the length/index/duplicate tests do not satisfy (`plan-reviewer` M6) |
| `tests/scripts/test_render_recordings_v2.py`, `tests/env/test_dashboard_frames.py` | construct via `meta.get("channel_display")`; must still pass on pre-change fixtures (legacy path). **Name the fixture that stays un-regenerated** (CP7) — otherwise this assertion goes vacuous the moment every cell is re-recorded (`plan-reviewer` M4) |
| `tests/env/test_dashboard_v1_imports.py` | unchanged, but **must stay green**: it pins `write_run_meta`'s signature prefix (§6, L3) |
| `tests/env/test_channel_names_match_configs.py` (new) | **The standing guard.** Sweep **§9b's roots verbatim** — `configs/environment/**`, `configs/verification/**`, `configs/continual/nmn_double_return_stages/`, plus `configs/environment/default.yaml`; skip permitted **only** for files directly under `configs/continual/` — through the **resolving** loader and then `channel_display_from_config`. Not "`default.yaml` plus `experiment/basic/`": that was the pre-C7 directory scope and it survived into this row by mistake (`plan-reviewer` M17). A config whose resolved widths disagree with its names list, or whose merge group names a channel it does not have, must fail **naming the file and both keys**, parametrised per file so the failure names the offender. **The enabled-sense rule applies here too**: a sense's keys are checked only when that sense resolves enabled, so the two olfaction-parity configs must **pass with olfaction names alone**. Display keys present for a *disabled* sense are **ignored, not refused** — the sense is off, so there is no resolved width to validate a length against, and refusing would punish a harmless leftover |

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
      files and `tests/env/test_unified_parity.py`; record counts. **Do not inherit any number
      printed in this plan** — re-run and record what you actually get, including whether the
      band-span wide-sense cases run or **skip** (measured 2026-09-21: `16 passed, 2 skipped`,
      both skipping on configs deleted by `47b1b8c3` — §A6).
      **Also record the resolved base**, because every width and slot number in this plan keys
      off it: `(olfactory_vector_size, visual_vector_size, olfactory_grid_range,
      visual_sensor_range)` from `default.yaml` through the resolving loader. Committed state
      at `47b1b8c3` is `(5, 1, 1, 2)`. If it differs, §10's declaration and CP5's subject both
      move (M21) — stop and re-derive rather than editing to match a stale number.
      **And record `git status --short configs/`**, which must be clean: it is today, and the
      one sentence in CP2's rollback explains why that matters.
      *Detects*: any later count that differs by anything other than the intended tests.
      *Rollback*: none (read-only).

- [ ] **CP1 — Write the new tests first, run them against unmodified source, record the
      failures.** *Detects*: a test that would have passed anyway — if any new test passes
      here, it is not testing the change and must be rewritten. *Rollback*: delete the test
      file.

- [ ] **CP2 — Config + writer only (no renderer change yet), and capture the BEFORE frame.**
      Add the four keys and the comment block; add `channel_display_from_config`; update
      **all four** writers (§8). **Before touching the renderer**, render step 0 of a
      **8-channel cell built by §9's grow helper** — the *same* cell CP4 will render — to PNG
      with the OLD renderer and keep it. This is the only moment the "before" picture can be
      captured (`plan-reviewer` M2), and it must be that cell rather than a convenient
      1-channel one, or CP4 compares an 8-channel after-frame against a 1-channel before-frame
      (`plan-reviewer` C10). Pixel-comparing an old on-disk cell against a regenerated one
      would compare *different episodes anyway*: the campfire world was retuned on 2026-09-18
      (`2bfe158e`) and bush blocking changed on 09-14. So compare `layout_signature()` plus
      panel boxes, and use the PNG for human inspection rather than as a pixel oracle.
      *Detects*: `load_run_meta(...)['channel_display']` present and correct; parity suite
      **unchanged** (proves no key leaked into `load_env_params`); a deliberately wrong names
      length raises naming both numbers.
      *Rollback*: `git checkout` the affected files; regenerated cells are re-made by CP7.
      **Why that is safe now, and was not two days ago** (`plan-reviewer` C11): this step edits
      `configs/environment/default.yaml`, which until `47b1b8c3` carried another session's
      **uncommitted** rollout. A `git checkout` then would have destroyed work with no reflog
      to recover it, and a `git add` would have swept their hunks under this plan's commit.
      `configs/` is clean now — verified at CP0 — so an ordinary edit and an ordinary rollback
      are correct. **Keep this sentence**: if a rollback step ever again shares a file with
      another session's uncommitted work, `git checkout` is the wrong instrument and the
      snapshot-and-reverse-apply route is the right one.

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
      **Not `M4`**, which cannot fail for the right reason. And **not `M1` for the rows path
      either**: since the rollout `M1` is the base config with no overrides, which now reads
      smell at range 1 and vision at range 2, so it draws **diamond maps**, not rows
      (`plan-reviewer` M14). The rows-path render needs an **explicit range-0 cell** — a new
      fixture cell overriding `sensory.olfactory_grid_range: 0` and
      `sensory.visual_sensor_range: 0` (both keys exist, so the override guard allows them).
      Name it in the script and use it here and at CP4.
      *Rollback*: `git checkout` the five renderer files.

- [ ] **CP4 — Vision dim 8, rendered THROUGH the production script, and looked at.**
      Regenerate a **vision-range-2** cell (`E2` or `E3`) and render it with
      **`scripts/eval/render_recordings_v2.py`** — not by constructing `EpisodeRenderer` in a
      scratch script. That script bypasses `from_recording` entirely (§4b), so a checkpoint
      that avoids it is the exact blind spot that would let this ship invisible on the only
      path that makes real videos (`plan-reviewer` C3).
      **Build the 8-channel world with §9's grow helper** — do not lean on the base config,
      which now runs one vision channel (§A8), and **do not reach for the archived
      `basic_vec8/` variants**: they are refused by `_require_maintained` and their chain is
      broken (§9). The cell strips each entity's visual vectors so the loader auto-generates
      the canonical V=8 one-hot, and sets the 8-entry names list with `{Terrain,[0,1,2]}`.
      **This must be the same cell CP2 photographed**, or before and after are different
      worlds and the comparison means nothing.
      *Detects*: configured names on the frame (not "Channel 0"), **six** vision maps with
      terrain merged, unchanged widths versus CP2's before-frame and identical
      `layout_signature()`. Any difference at 8 channels is a regression, not an improvement.
      Also render **the explicit range-0 cell named in CP3** through the same script for the
      rows path — not `M1`, which no longer draws it (`plan-reviewer` M14).
      *Rollback*: as CP3.

- [ ] **CP5 — Render at vision dim 1 and look at it.** **Easier than when this plan was
      written**: the base config is single-channel vision at `47b1b8c3` and already reads
      vision at range 2, so a cell built on it exercises this directly, and `E6sum`/`E6bin`
      now build (verified — §9).
      **If CP0 finds the base is NOT one-channel**, this checkpoint has no subject as written:
      use §9's **shrink** helper to build a 1-channel cell rather than improvising one
      (`plan-reviewer` M21).
      *Detects*: **one map at normal size** — the same map-square pixel size as the 8-channel
      frame, **not enlarged to fill the panel** — with **blank space beside it**, labelled
      "Visible" from the config, not "Channel 0". The map size is the real assertion here; a
      stretched single map is the defect this whole change removes.
      *Rollback*: revert the fixture-script edit; nothing on disk is replaced.

- [ ] **CP5b — Render ABOVE the slot count, BOTH ways, and look at what actually happens.**
      **This documents §D4c; it does not gate the design.** The overflow behaviour is decided
      and this checkpoint cannot overturn it — its purpose is that a future reader meeting an
      off-path frame finds a picture of it here rather than filing a bug. Build throwaway
      cells at **vision range 2** and render step 0 of each to PNG, **and run
      `render_layout_audit.py` on each beside a normal cell**:
      (a) **group kept, over-slot by count** — 12 vision channels, Terrain group present → 10
      maps into 6 slots. **Say in the cell description that the 12-channel assignment is
      synthetic and arbitrary**: no loader default exists above 8, so the entity→channel map
      here is invented for the test and means nothing outside it;
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
      *Record, do not fix, do not re-ask.* The clipped-vision outcome is the expected result,
      not a defect to escalate: attach the frames to the Implementation Report as §D4c's
      worked example. Do not loosen the audit, do not add a limit, and do not change the
      sizing rule.
      *Rollback*: delete the throwaway cells; they touch nothing else.

- [ ] **CP6 — Full suites, deliberate breaks, and the config sweep.** Run the three dashboard
      files, the parity gates, `tests/scripts/test_render_recordings_v2.py` and
      `tests/env/test_dashboard_v1_imports.py`. Then three deliberate breaks, each reverted
      after:
      (a) a group naming **channel 9** → the write must **fail**, naming the bad index;
      (b) a names list one entry short → **fail**, naming both numbers;
      (c) `visual_channel_groups: []` at 8 channels → must **warn, not fail**, naming 8 maps
      against 6 slots (§D4b). A failure here would mean a limit crept back in;
      (d) a group longer than the terrain palette can colour → must **fail**, naming the group
      length and the palette arity (§D8).
      **Plus the shifted-group render, which is a frame a human looks at, not an assertion:**
      declare `{Terrain, channels: [1,2,3]}` on an 8-channel display and render it beside the
      `[0,1,2]` frame. The merged map must be coloured from channels 1–3, and **the two frames
      must visibly differ**. If they look identical, the painter is still reading a literal
      slice and §D8's defect is live — a unit test alone cannot catch this, because it would be
      written from the same wrong assumption that produced the bug.
      Then **sweep §9b's roots** (`configs/environment/**`, `configs/verification/**`,
      `configs/continual/nmn_double_return_stages/`, plus `default.yaml`; skip only files
      directly under `configs/continual/`) through `channel_display_from_config` and record
      pass/fail per file — **not** the narrower `configs/environment/` scope an earlier draft
      of this line carried (`plan-reviewer` M17).
      **Include a vision-off subject**: the fixture script's `E9` cell (vision disabled) must
      record with olfaction names alone and render with no vision panel at all. Without it the
      enabled-sense rule is never exercised end to end.
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
| C6 | Overflow is disappearance, not spillover (vision) | **Mechanism verified; topic closed by the user 2026-09-19.** §D4c documents it as a known consequence of an off-path config — today's counts *are* the conventional maximum, so exceeding them is off the normal path by construction and no shipped world does it. Behaviour unchanged (no limit, warn, still draw). CP5b is kept as documentation, not as a gate |
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
| C7 | Standalone configs inherit nothing | **Applied, with one exclusion.** §7b adds the keys to the **eleven** verified `extends`-free env configs. **`configs/models/q_learning/q_learning.yaml` is not one of them** — it is an *agent* config, outside the sweep roots, and it cannot resolve to `EnvParams` at all (it fails on `sensory.visual_sensor_range`). Reported rather than edited, per the instruction to verify first. **Its justification was corrected twice more afterwards** — "declares no channel count" did not separate it from the other eleven (C9), and `using_sensory: false` rests on a key no code reads (M16). Parity safety confirmed independently: neither gate hashes a config, and `load_env_params` never reads these keys |
| C8 | Terrain merge is data in config but a constant in the painter | **Applied — §D8.** Verified at `painters.py:701-711`: `row[:3]` is a literal slice and `P.TERRAIN_FILL` a hardcoded 3-tuple, so `{Terrain,[1,2,3]}` would validate, place correctly and colour from channels 0–2 with no error. `map_plan` now carries the group's channel tuple, the painter reads those channels, group length is validated against palette arity, and **CP6 gains a shifted-group render a human looks at**. This was mine to catch and I did not — count discipline covers *how many* maps, not *which channels* one reads |
| M10 | Band-span wide case skips, and is wrong on both branches | **Applied** — §11 rebuilds it from `default.yaml` plus range overrides with a configured display (no config-file dependency, no skip), and adds the legacy range-3 refusal as its mirror, since `from_params(...)` with no payload is the legacy regime |
| M11 | Trainer-start check | **Adopted and labelled** — §7c, called a **backstop, not a guard**, in those words: zero commit-time coverage, never reaches the verification configs. Call site `train.py` (recording branch at `:2555`) is in File Changes |
| L4 | "warn at load" reuses the load-bearing word | **Applied** — reworded to "when the display is built", one warning site, once per sense per run |
| — | **Premise change: the dim-1 rollout landed mid-revision** | **§A8.** Not a review finding — found while verifying C7. The base config moved from 8 vision channels to 1 in the working tree, invalidating §10's worked example, the `PANEL_MAP_SLOTS` anchor, and CP4's "unchanged from today". All corrected; the ordering question is moot and the "report and stop" instruction is **withdrawn** (M13a) |
| C9 | §7b rests on a false measurement; no rule for a disabled sense | **Applied, with one relayed number rejected.** §7b now states what is true: the eleven declare olfaction's width (`vector_size: 5`) and declare **nothing** about vision — the 8 is the loader's `.get(..., 8)` fallback — and required lengths are read from **resolved `EnvParams`**. The user's enabled-sense rule is adopted, which makes the `q_learning` exclusion structural. **The relayed claim that `vector_size` is 1 in all eleven is wrong and was not implemented**: it is 5, confirmed by value-grep and by resolution; the "1" was a line count. Implementing it would have put a 1-entry olfaction list into eleven 5-channel configs |
| C10 | No recordable 8-channel world for four checkpoints | **Applied, and the fix is verified rather than assumed.** §9's helper now works in both directions; the grow route strips entity visual vectors so the loader's own V=8 auto-generation supplies the layout. **Demonstrated end-to-end 2026-09-21** (the review's O9 and O10, both previously unverified): the strip-and-rebuild loads at `vis=8`, and the loader assigns food→3, hiding_predator→4, predator→5, rabbit→7, obstacles→6, background 0/1/2 — exactly §10's reference table. CP2's before-frame is taken on the same cell CP4 renders; the `basic_vec8` mention is deleted from CP4 |
| M12 | Refusal predicate stated by range | **Applied** — §D5b is now **need versus grant**. A 1-channel legacy recording at range 3 needs 102 px against 520 px and must render; only the 8-map case (634 px) is refused. The range drops out of the rule |
| M13 | Four stale premises after the rollout | **Applied** — "report and stop" withdrawn (nothing to reconcile: no `basic/` config redeclares the width); the E6 fix marked unnecessary (they build, verified); §A8's table completed with `visual_blur_enabled` and `visual_value_mode`; §A2 item 3 corrected — no maintained world draws the rows path any more |
| M14 | `M1` no longer draws the rows path | **Applied** — CP3 and CP4 now name an explicit range-0 cell (`olfactory_grid_range: 0`, `visual_sensor_range: 0`) instead of `M1` |
| M15 | Floor catches removals, not skipped additions | **Applied** — §9b's sweep is now scoped by **location**: skip only files directly under `configs/continual/`; everything under `environment/**`, `verification/**` and `continual/nmn_double_return_stages/` must resolve or fail naming the file; a `channel_display_from_config` raise is never a skip; copy the glob, not the raw loader; both floors kept |
| L5 | Line drift | **Applied** — `visual_vector_size` at `:256`, the trainer branch located by `if eval_v_flag:` rather than a line number, frontmatter re-dated |
| L6 | Prose invariant with no structural check | **Applied** — §11 adds a source-grep assertion that `"row[:"` does not appear in `painters.py`, following the project's own `MAP_GAP` precedent |
| C11 | CP2's rollback would destroy another session's uncommitted work | **Resolved by events, and verified before relying on it.** The rollout committed as `47b1b8c3` and `git status --short configs/` is now clean, so the user's "wait for them to commit first" is satisfied and an ordinary edit with an ordinary `git checkout` rollback is correct. CP0 records the clean state; CP2 keeps **one sentence** on why the ordering mattered, so nobody reintroduces a `git checkout` into a rollback step that shares a file with another session's uncommitted work |
| M16 | `using_sensory` justification | **Applied** — that key is read by **no code** (only test-fixture YAML strings); the loader keys enablement on `olfactory_enabled` / `visual_sensor_enabled`. §7b now gives the two reasons that hold: `q_learning.yaml` is outside §9b's sweep roots and cannot resolve to `EnvParams` at all (it fails on `sensory.visual_sensor_range`). Third attempt at this justification, and the first two are named rather than quietly dropped |
| M17 | Sweep spec carried the pre-C7 scope and never stated the enabled-sense rule | **Applied** — §11's row and CP6 now cite §9b's roots verbatim, state that a sense is checked only when it resolves enabled (so the parity pair passes with olfaction names alone), and settle the open question: keys for a **disabled** sense are **ignored, not refused**, since there is no resolved width to validate against. CP6 gains the vision-off `E9` cell as a subject |
| M18 | M13's fix reached §A8 but not §9b | **Applied** — §9b rewritten: the rollout landed as `47b1b8c3`, `visual_vector_size` is set once in `default.yaml` and by no `basic/` file, the reconciliation is empty, "report and stop" is withdrawn there too, and what remains is the live rule (a config setting its own width must name that sense in the same file) |
| M19 | 102 px contradicts §D5's own rule, and the range cap was unstated | **Applied, and it carries a user design instruction.** 102 → **482** corrected (`max(6,1) = 6` maps). New §D4d records the user's rule — an oversized range overflows **inside** the panel, never outside — which is coherent with §D4b (draw, do not reject) and repairs §D4c's worst case by containing rather than disappearing. **The boundary is measured and stated plainly**: contained in 520 px, range 2 → 15.3 px cells, range 3 → 10.9 px, **range 4 → 8.5 px, under the painter's 10 px floor**, so range 4 refuses (`visual needs 602px … giving it 520px`). Fixed panel size caps renderable vision range at 3; the user said they will ask for a fix if the setting is ever needed |
| M20 | The legacy signal became ambiguous | **Applied** — `from_meta` is keyed off whether `run_meta` carried the **top-level** `channel_display` at all, not off a per-sense entry. A configured recording missing an entry for an **enabled** sense now raises naming the sense, instead of silently shipping "Channel 0" — the one name §1 promises the drawing path can never produce |
| M21 | The plan never actually said "re-measure at CP0" | **Applied** — CP0 now records the resolved base `(olf, vis, olf_range, vis_range)` (committed state `(5, 1, 1, 2)`) and `git status --short configs/`, and instructs the developer to inherit **no** number printed in this plan. CP5 falls back to §9's shrink helper if the base is not one-channel |
| L7 | Stale bundle | **Applied** — CP5's "they do not currently build" corrected (they do), §D5b's `E7` recording marked as hypothetical (none exists on disk), and §7c's single-stage limitation recorded with the optional multi-stage fix |

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

### Third pass — reviewed at `0dac47c1` (2026-09-19)

**Verdict: NOT READY**, on two **new** findings only. Every Critical from the first two passes is
applied in the committed text, and CP3 / CP4 / CP7 / CP2b can now genuinely fail (subjects verified
on disk; the three `render_recordings_v2.py` sites in §4b match the code). The closed decisions —
overflow, rollout order, no version bump, C2, C4 — are respected and not re-raised. Full detail,
the settlement of the disputed second-pass account, and the judgement of the record-time
substitution: [[plan_dashboard_channel_names]] §"Third pass".

**On the dispute:** the second pass was committed at 16:15:33, `b0ab1fe3` at 16:22:49 — the
commit could not have preceded the pass, but the pass reviewed an uncommitted working copy, which
was the reviewer's error. All three of C1/C3/C4 are applied at `b0ab1fe3`; CP5b was absent from
the snapshot and present at the commit; M8's four references are all gone at the commit and the
survivor the author names is group validation and correct. This reviewer reviews committed SHAs
only from here on.

1. **C7 — the guarantee is overstated in three places** (§Context line 61 "must fail when the
   config loads"; §D7 "every run trained after this change … records normally"; §11's sweep
   scoped to one directory). Nothing fails at config load. A config with **no `extends:`** inherits
   nothing and fails at its first recorded evaluation after the change too — 12 such files
   declare `sensory:` outside `configs/environment/` today (5 continual stage configs, which
   `eval_rollout.py --record` resolves at `:677-724, :956`; 6 verification; 1 q-learning), all
   inside the parity gates' glob and all invisible to a `basic/`-only sweep. `CLAUDE.md` names
   exactly this population as a new mandatory key's rollout; §D6 confines the plan to
   `default.yaml`. *Exit*: fix the three sentences; **user decides** whether the 12 standalone
   files get the four keys or are declared unrecordable (no fallback either way); the standing
   test sweeps **by content** (`sensory:` present) over `configs/**` with the `archive/` exclusion
   `test_backward_compat_configs.py:27-34` uses, and asserts a floor on files collected; §9b's
   sweep sentences are written as commitments, not as if the test existed.
2. **C8 — the Terrain merge becomes data in config and layout but stays a constant in the
   painter.** `painters.py:706-709` reads `row[:3]` and a 3-colour table whatever the group
   says; §D3 permits a group at `[1, 2, 3]` or of 2–4 channels, which would draw a
   correctly-labelled, wrongly-coloured map with no error — on the step the plan names as the
   riskiest. *Exit*: `map_plan` carries the group's channel tuple; the painter reads those
   channels; group length vs. palette is validated or the palette generalised (author's choice);
   CP6 adds a shifted-group render that is looked at.

Moderate: **M10** — `test_dashboard_band_span.py:266` `pytest.skip`s when its two configs are
absent (both staged for deletion), and after the change its `olf1_vis3` case asserts a *legacy*
range-3 context packs, which §D5b says must refuse — rebuild the case from `default.yaml` +
range overrides with a configured display, no skip, plus the legacy-refusal mirror. **M11** —
the "fail when the recorder is configured" idea is achievable without `load_env_params` (one
`channel_display_from_config` call at trainer start when recording is on) and is a **backstop,
not a guard**: adopt or decline in §9b, and if adopted say "backstop" in those words. Low:
"warn at load" must read "when the display is built"; one warning site, once per case.

### Fourth pass — reviewed at `b2804376` (2026-09-20)

**Verdict: NOT READY**, on two **new** findings, both caused by the vision-dim rollout landing
under the plan rather than by anything the third pass asked for. C7, C8, M10, M11 and L4 are all
applied at the commit; the closed decisions are respected and none is reopened. Full detail, the
answers to the questions this pass was asked, and the assumption list:
[[plan_dashboard_channel_names]] §"Fourth pass".

1. **C9 — §7b rests on a false measurement, and there is no rule for a disabled sense.** None of
   the eleven standalone configs declares `visual_vector_size`, `visual_background_properties`,
   or any entity `visual_properties`; their eight vision channels are the loader's `.get(..., 8)`
   fallback (`config_loader.py:1687-1688`) and its auto-generated one-hot table. The two
   olfaction-parity files have `visual_sensor_enabled: false` and no entities, so §7b would give
   them eight vision names for a sense that is off — the plan's own reason for excluding
   `q_learning.yaml`. *Exit*: rewrite the "verified" sentence; **user decides** the disabled-sense
   rule (recommended: a sense's keys are read only when that sense is enabled in `params`, which
   makes the `q_learning` exclusion structural); the nine vision-enabled files are checked against
   the resolved params' per-entity `argmax`, not the how-to; the how-to says its 8-channel table
   documents the loader's default layout.
2. **C10 — no recordable 8-channel world exists for CP2's before-frame, CP4, CP5b or CP6's
   shifted-group render.** Overriding width 8 on the 1-channel base fails on every entity's
   `visual_properties: [1.0]`, and the assignment is no longer in the config; the archived
   `basic_vec8/` route is refused by `_require_maintained`
   (`make_render_fixture_recordings.py:368-377`), lacks the four keys (so the override guard at
   `:437-446` refuses to add them), and `basic_vec8/05` extends the *live* `basic/04`. *Exit*:
   §9's helper works in both directions and, for width 8, strips `visual_properties[_std]` and
   the background table so the loader's own V=8 auto-generation supplies the layout (one source);
   the two display keys ride in the same override; CP2's before-frame is the same 8-channel cell
   CP4 renders; the archived route is deleted from CP4.

Moderate: **M12** — the M10 mirror is now a 1-channel legacy context at range 3, which fits
(102 px) and refuses nothing; §D5b's predicate must be need-versus-grant, not `range ≥ 3`, and
the mirror builds its legacy context in-memory at width 8 as `_ctx` already does. **M13** — four
stale premises: no `basic/` config redeclares `visual_vector_size` (all seven inherit 1), so
§9b's reconciliation is empty and "report and stop" halts the developer on a non-event;
`E6sum`/`E6bin` now build; §A8's table omits `visual_blur_enabled` and `visual_value_mode`; §A2
item 3's "most maintained worlds draw rows" is false — every maintained world now draws diamond
maps. **M14** — `M1` is the base with no overrides and no longer draws the rows path; CP3(c) and
CP4's rows render need an explicit range-0 cell. **M15** — the sweep's floor catches removals,
not a new maintained file that fails to load and is skipped; skip only top-level
`configs/continual/` schedules, fail on everything else. Low: line drift (`default.yaml:256`,
`train.py:2552-2560`), `last_updated`; an optional source-grep test pinning "no `row[:` in
`painters.py`" would make the C8 invariant structural, as `test_dashboard_band_span.py:224-238`
does for `MAP_GAP`.

Verified this pass: the sweep's 32 collected / 19 resolving; C8's forbidden-constant rule covers
every channel-reading branch that exists (terrain `:707/:709` is the only literal; seq `:713`
and the rows path `:625` are data-driven or positional); the how-to's smell table matches the
working-tree columns exactly; the M10 configured branch is right (487 px of 520 at range 3).

*Reviewed by: plan-reviewer*

### Fifth pass — reviewed at `d3d61bf5` (2026-09-21)

**Verdict: NOT READY**, on **one** Critical that is a git-safety hazard in a checkpoint, not a
design defect. Both fourth-pass fixes were re-derived and **hold**: the eleven standalone configs
resolve `olf=5 vis=8` with the loader's own assignment (nine vision-enabled files
`res=[3…,4…] anim=[5,7,7] obs=[6]`; the parity pair `visual_sensor_enabled: false`), and the
strip-and-grow route builds an 8-channel world through the fixture script's own `build_params`
with food→3, hiding_predator→4, predator→5, rabbit→7, obstacles→6, background 0/1/2 (O9, O10
closed). The design is implementable as written. Full detail, the five questions answered, and
two reviewer disclosures: [[plan_dashboard_channel_names]] §"Fifth pass".

1. **C11 — CP2's rollback would revert the parallel session's uncommitted rollout.** "`git
   checkout` the affected files" includes `configs/environment/default.yaml`, which carries their
   unstaged 8→1 change; working-tree edits have no reflog, and the seven `basic/` files (entity
   `visual_properties: [1.0]`) would then extend an 8-channel base and the whole ladder stops
   loading. The same file cannot be committed whole without sweeping their hunks (`CLAUDE.md`;
   `git add -p` is unavailable here). *Exit*: CP0 snapshots `git diff HEAD -- configs/environment/`
   to a patch plus `cp -a`; CP2's rollback for `default.yaml` is "reverse-apply this plan's own
   hunks", never `git checkout`; the plan states how `default.yaml` is committed (after the rollout
   session commits — recommended — or via a filtered `git apply --cached`); user picks.

Moderate: **M16** — `using_sensory` is read by no code, so §7b's "structural" `q_learning`
exclusion rests on a dead key (the file fails `load_env_params` on `visual_sensor_range` and sits
outside the sweep roots — say that instead). **M17** — the §11 test row and CP6 still say "under
`configs/environment/`", the scope C7 rejected, and never state the enabled-sense rule (both
sentences predate the fourth pass — missed then); also say whether keys for a disabled sense are
ignored or refused, and add `E9` (vision off) as a CP subject. **M18** — §9b's intro and steps
1–3 are M13-stale: "report and stop" is withdrawn in §A8 and live here. **M19** — §D5b's "102 px"
contradicts §D5's own `max(slots, drawn)` (a 1-channel legacy at range 3 needs 482 px, still
fits); and the same rule **refuses at range 4** (602 > 520, measured) for configured and legacy
alike — fixed size caps renderable vision range at 3, which the plan never states and the user
has not been told (fixture cell `E8` is such a world). **M20** — after the enabled-sense rule,
`from_meta(payload=None)` cannot tell pre-change / disabled / forgotten apart and gives an
*enabled* sense on a configured recording positional names silently; key legacy on the
top-level key and raise for a missing enabled sense. **M21** — the plan does not say "re-measure
at CP0"; §10's declaration is gated by the sweep, CP5's one-channel subject is not. Low (**L7**):
CP5 "(they do not currently build)"; no `E7` recording exists on disk; §7c could resolve every
continual stage at start for free.

Disclosure: my first slot-to-entity read of the loader output was misaligned (entries expand to
`count_high` slots) and briefly showed hiding_predator→3 / rabbit→5; re-run by slot, the author's
numbers are exactly right.

### Sixth pass — reviewed at `261513e8` (2026-09-21)

**Verdict: SOUND WITH CONCERNS — nothing blocks implementation.** §D4d's containment table was
re-derived with the real packer and holds exactly (362 / 482 / 602 px; 15.3 / 10.9 / 8.5 px map
squares; range 4 refused with the quoted message); every checkpoint has a subject that exists or
builds against the committed base `(5, 1, 1, 2)`; the wide-sense rebuild is genuinely in memory
(`_ctx` builds a context from literals); `E9` resolves with no `Visual` in the breakdown and
packs; a 12-channel synthetic world loads. Full detail and the six questions answered:
[[plan_dashboard_channel_names]] §"Sixth pass".

Three Moderates, none blocking — a developer implements correctly despite each:

- **M22** — another session has **already rewritten the same wide-sense test, uncommitted**,
  pointing it at files on disk (`basic/05-campfire_thermal_10x10.yaml` and an untracked
  `tests/env/fixtures/dashboard_band_vis3.yaml`), against M10's rule and today's diary. CP0 must
  record `git status --short tests/env/` and coordinate as C11 did; §11's in-memory version
  supersedes, and the fixture YAML goes with whoever lands second.
- **M23** — `from_meta` raises for any missing entry once the key is present and has no enabled
  input; built eagerly for both senses it raises on a vision-off configured recording. Say in §2
  that a display is built only for senses in `ctx.observed`, and add the vision-off mirror case
  to §11. CP6's `E9` catches an eager build.
- **M24** — "checks before packing" (§D5b) requires re-deriving the band grant outside `pack()`,
  a second copy of the packer's arithmetic. Catch-and-reraise around `pack()` on the legacy path
  instead; CP3(b) unchanged.

Low: the range-4 refusal is issued by the layout registry, not the painter (same 10 px floor);
§9's helper branches are "V ≠ 8 / V = 8", not "shrink / grow"; the source-grep should be
`\b(row|vec)\[[^\]]*\d` rather than `"row[:"`.

*Reviewed by: plan-reviewer*
