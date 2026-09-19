---
title: "Sensor channel names come from config, and sense panels get a fixed size"
topic: refactors
status: active
created: 2026-09-19
last_updated: 2026-09-19
---

# Sensor channel names come from config, and sense panels get a fixed size

> **Status**: PLANNED — not implemented, not reviewed by `plan-reviewer` yet
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
   maximum** (smell 5, vision 8 — today's values, as a named constant in code), and a run
   using fewer channels simply leaves blank space. The blank space is intended and must not
   be "fixed" later by someone who reads it as a layout bug.
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
- **A field added after a pickle was written is genuinely absent.** `EnvParams` is a Flax
  `struct.dataclass` pickled into every `run_meta.pkl`; a new field does not appear on an
  old unpickled object with a class default — `hasattr` returns `False`. Every recording on
  disk, including all 11 render-audit fixture cells, would break. `render_recordings_v2.py`
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
width. Both sites must move to the conventional maximum or the two disagree again — which is
the failure mode of `4b6f7196`.

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
`configs/environment/experiment/archive/basic_superseded/` (it has also staged two new
`05-campfire_thermal_10x10_olf1_vis{2,3}.yaml` worlds). This is not caused by this plan and
**must not be fixed by it** — the owning session must update that list. The developer records
the same three failures before and after; any *fourth* failure is theirs.

If that session's work lands before implementation starts, re-measure the baseline rather
than assuming these three still fail.

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
3. Its writer runs **only in real evaluation**, where the config has been resolved through
   `load_env_config` (`extends:` layered). So the writer may use `get_mandatory` without any
   raw-loading test ever reaching that code.
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
- channel count > the conventional maximum (§D4)

#### D4. Two constants per sense, each with one job

Both live in `labels.py` — the module `panels` and `painters` both already import, and which
has no dependencies of its own.

```python
#: The conventional maximum number of channels a sense is expected to carry.
#: Not a hard limit in principle -- raising one is a one-line edit here -- but a
#: config exceeding it fails loudly rather than drawing off the edge of its panel.
CONVENTIONAL_MAX_CHANNELS = {"Olfaction": 5, "Visual": 8}

#: How many map slots the panel is ALWAYS sized for, whatever the run's channel
#: count. Vision is 6 rather than 8 because the three terrain channels ship merged
#: into one map; this is the number of maps the conventional maximum DRAWS.
PANEL_MAP_SLOTS = {"Olfaction": 5, "Visual": 6}
```

**Why two numbers and not one.** The user named 5 and 8 — those are *channel* counts, and
they are what a config is validated against. But the panel is sized in *maps*, and vision's
eight channels draw six maps because three of them merge. Deriving the slot count from the
live config's own groups would make the panel *wider* at one channel (no groups → no merge →
8 slots) than at eight (6 slots), which is the opposite of a fixed size. So the slot count is
its own constant, pinned to today's picture. A test asserts `PANEL_MAP_SLOTS[s]` equals the
map count that `CONVENTIONAL_MAX_CHANNELS[s]` channels draw under the shipped groups, so the
pair cannot drift apart unnoticed.

#### D5. Legacy recordings: sized to what they draw

A recording with no `channel_display` gets positional names (`Channel 0` …) and **no
groups**. An old 8-channel recording therefore draws **8 maps, not 6** — the merge was
hardcoded and is now data the recording does not carry.

That collides with a fixed 6-slot vision panel: 8 maps into 6 slots must not silently
overflow, and must not refuse to render. **Rule: when the names payload is absent, the panel
is sized to `max(PANEL_MAP_SLOTS[sense], maps_drawn)`** — i.e. legacy recordings keep exactly
today's sizing behaviour, and the fixed-size promise applies to recordings written after this
change. This keeps every recording on disk renderable, which decision #5 requires. It is the
one deliberate asymmetry in the design and is commented as such in the source.

#### D6. Out of scope, stated so the omissions are deliberate

- The **range-0 rows path** (`build_channel_rows`) — §A2 item 3.
- The **height twin** bug — §A7.
- Any change to `configs/environment/experiment/basic/*` — another session owns the vision-dim
  rollout. This plan touches `configs/environment/default.yaml` only (user-authorised).
- The three pre-existing test failures — §A6.

---

### File Changes

#### 1. `src/environment/dashboard/labels.py` — delete the tables, take names as data

**Delete**: `OLFACTORY_LABELS` (45), `OLFACTORY_LONG` (47), `OLFACTORY_PARTS` (62),
`VISUAL_LABELS_V8` (71), `VISUAL_LONG` (82), `SUPERSEDED_VISUAL_LABELS` (95),
`_STANDARD_VISUAL_WIDTH` (97), `TERRAIN_CHANNELS` (173). Rewrite the module docstring: its
current text describes overriding an adapter's labels and a name table keyed by index, both
of which stop being true.

**Add** `CONVENTIONAL_MAX_CHANNELS` and `PANEL_MAP_SLOTS` (§D4).

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
    """How many slots the panel is sized for -- the conventional maximum, except
    that a legacy recording is sized to what it actually draws (see D5)."""
    drawn = len(map_plan(sense, display))
    return max(PANEL_MAP_SLOTS[sense], drawn) if display.legacy else PANEL_MAP_SLOTS[sense]
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

#### 5. `src/environment/dashboard/__init__.py`

Remove `channel_labels`, `olfactory_labels`, `visual_labels` from the import (36) and
`__all__` (98–104); export `ChannelDisplay`, `map_plan`, `panel_map_slots`,
`CONVENTIONAL_MAX_CHANNELS`, `PANEL_MAP_SLOTS`.

#### 6. `src/utils/eval_recording.py`

- `write_run_meta` (99): new **required** parameter `channel_display: dict`, written as the
  top-level `'channel_display'` key. Required rather than defaulted, so that a new writer
  cannot forget it — the three existing call sites are all updated in this change.
- Module docstring (1–12): add `channel_display` to the `run_meta.pkl` contents list.
- **Do not bump `RECORDING_FORMAT_VERSION`** pending the user's answer to §Q1.

#### 7. New helper — where the config is read

One function, imported by all three writers, so the config→payload translation exists once:

```python
# src/utils/eval_recording.py
def channel_display_from_config(config, params) -> dict:
    """Build the run_meta channel_display payload from a RESOLVED config.

    Runs only on the evaluation path, where `load_env_config` has already layered
    `extends:`, so `get_mandatory` is safe here and never reaches a parity test.
    """
```

It reads the four keys with `get_mandatory`, validates per §D3 against
`int(params.olfactory_vector_size)` and `int(params.visual_vector_size)`, and raises
`ValueError` naming both numbers on any mismatch.

#### 8. Three writer call sites

| File | Line | Change |
|---|---|---|
| `src/utils/evaluation_core.py` | 290 | add `channel_display=channel_display_from_config(config, params)` |
| `src/algorithms/dreamer_srl/eval.py` | 83 | same, with `env_params` |
| `src/algorithms/dreamer_srl/eval.py` | 380 | same |

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
- No `_CONDITIONAL_KEYS` change is needed — every key involved already exists in
  `default.yaml`.

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
  # sense panels are sized for a CONVENTIONAL MAXIMUM, not for this run's count, so
  # a run with fewer channels draws its maps at normal size and leaves the rest of
  # the panel BLANK. That blank area is intended -- it is not a layout bug, and it
  # is what keeps two runs' panels comparable. A config declaring MORE channels than
  # the conventional maximum fails loudly; raising the maximum is a one-line change
  # in src/environment/dashboard/labels.py.
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
| `tests/env/test_dashboard_channel_display.py` (new) | length mismatch raises naming both numbers; out-of-range / duplicate / non-contiguous group raises; absent payload gives positional names and no groups; `PANEL_MAP_SLOTS[s]` equals the maps `CONVENTIONAL_MAX_CHANNELS[s]` channels draw under the shipped groups; **`_span` returns the same width at 1 channel as at 8** |
| `tests/env/test_dashboard_band_span.py` | update the `channel_labels` import (54) and `_painter_map_count` (98) / `_ctx` (~78) to the new API. **The equality property it asserts must survive**: declared width == painter's need, now at the conventional maximum |
| `tests/scripts/test_render_recordings_v2.py`, `tests/env/test_dashboard_frames.py` | construct via `meta.get("channel_display")`; must still pass on pre-change fixtures (legacy path) |

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

- [ ] **CP0 — Record the baseline, including its red.** Run the three dashboard test files
      and `tests/env/test_unified_parity.py`; record counts. Expect **3 failed, 184 passed,
      2 skipped** on the dashboard files (§A6) and **72 passed, 350 skipped** on parity.
      *Detects*: any later count that differs by anything other than the intended tests.
      *Rollback*: none (read-only).

- [ ] **CP1 — Write the new tests first, run them against unmodified source, record the
      failures.** *Detects*: a test that would have passed anyway — if any new test passes
      here, it is not testing the change and must be rewritten. *Rollback*: delete the test
      file.

- [ ] **CP2 — Config + writer only (no renderer change yet).** Add the four keys and the
      comment block; add `channel_display_from_config`; update the three writers. Then
      regenerate **one** fixture cell (`M1`) and print the new `run_meta.pkl` key.
      *Detects*: `load_run_meta(...)['channel_display']` present and correct for M1; parity
      suite **unchanged at 72/350** (proves no key leaked into `load_env_params`); a
      deliberately wrong names length raises naming both numbers. *Rollback*: `git checkout`
      the four files; the regenerated M1 is re-made by CP7.

- [ ] **CP3 — Renderer reads the payload; legacy path proven first.** Implement `labels.py`,
      `panels.py`, `painters.py`, `episode.py`, `__init__.py`. **Render a frame from an
      un-regenerated fixture** (e.g. `M4`, which predates the feature) to PNG and **look at
      it**. *Detects*: it must draw with positional names "Channel 0…" at today's sizing and
      must not raise — this is decision #5 and §D5's asymmetry, and it is the case most
      likely to be broken silently. *Rollback*: `git checkout` the five renderer files.

- [ ] **CP4 — Render at vision dim 8 and look at it.** Regenerate `M1`, render step 0 to
      PNG, compare against the same frame rendered before the change. *Detects*: **frame
      content unchanged from today** — same six vision maps, same names, same widths. Any
      visible difference at dim 8 is a regression, not an improvement. *Rollback*: as CP3.

- [ ] **CP5 — Render at vision dim 1 and look at it.** Fix cells `E6sum`/`E6bin` (§A5),
      generate `E6bin`, render step 0 to PNG. *Detects*: **one map at normal size** (the same
      map-square pixel size as dim 8, not enlarged), **blank space beside it**, labelled with
      the configured name — not "Channel 0". *Rollback*: revert the fixture-script edit; the
      cell was never generated before, so nothing is lost.

- [ ] **CP6 — Full suites + a deliberate break.** Run the three dashboard files, the parity
      gates, and `tests/scripts/test_render_recordings_v2.py`. Then **edit a group in
      `default.yaml` to name channel 9 and confirm the recording write fails loudly**, then
      revert it. *Detects*: the group validation is real rather than assumed. *Rollback*: as
      CP3.

- [ ] **CP7 — Re-record the render-audit fixtures.** Regenerate the CP0.2 cells
      (`M1 M1x M2 M3 M4 M4b M5 M6 M6b`, plus `M4r`, `W20`) and re-run
      `scripts/eval/render_layout_audit.py` on one. *Detects*: audit frames show real names;
      audit report shows no new findings versus the pre-change run. *Rollback*: fixtures live
      under gitignored `results/` and are regenerable from the script — but **copy the
      existing directory aside first** (`cp -a results/render_audit /tmp/...`), per the git-
      safety rule, because they are not in version control.

- [ ] **CP8 — Speed check.** Time `render_recordings_v2.py --benchmark` on one cell before
      and after, same host and cell. *Detects*: >5% slowdown warrants discussion, >15%
      blocks. Expected ≈0 — this moves table lookups to dict lookups at build time, not
      per frame.

---

## Q1 — Question for the user: bump `RECORDING_FORMAT_VERSION`?

**This plan does not decide it.** Adding `channel_display` to `run_meta.pkl` is exactly the
kind of change a format version exists to mark, and project rules forbid inventing or bumping
a version without the user's permission.

**Recommendation: do not bump**, following the precedent already recorded in the source. When
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
