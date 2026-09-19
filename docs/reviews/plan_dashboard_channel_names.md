---
title: "Plan review: sensor channel names from config + fixed-size sense panels"
topic: reviews
status: active
created: 2026-09-19
last_updated: 2026-09-19
---

# Plan review: sensor channel names from config + fixed-size sense panels

> **Reviewed**: [[DASHBOARD_CHANNEL_NAMES_FROM_CONFIG]] — three passes: `fcd6faf2` (first), an uncommitted mid-revision working copy (second), and `0dac47c1` (third, current).
> **Current verdict (third pass, at `0dac47c1`)**: **NOT READY** — two Critical findings remain, both new; every earlier Critical is applied. See "Third pass" at the end of this file.
> **Reviewed by**: plan-reviewer

Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run · 🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

---

## Verdict, in plain language

The plan moves the names written under each sensor map in the episode video out of Python and into the environment config, deletes the in-code name tables, gives the sense panels a fixed size, and makes the "Terrain" merge a config-declared group. The design choices the user fixed are respected throughout and none of them is re-litigated here.

The plan is **not ready** because it would ship in a state where the feature is invisible on the one path that actually makes videos, would crash the recorder for every checkpoint trained before the change, would make some existing recordings unrenderable again, and would let one plausible config edit draw maps off the edge of the panel without an error. In order of cost:

1. **The production video script never receives the names.** `scripts/eval/render_recordings_v2.py` builds the renderer directly (not through the `from_recording` helper the plan edits) and is not in the plan's file list. Every video would render with positional "Channel 0…" names and eight unmerged vision maps — while every checkpoint in the plan goes green, because they render through a different entry point. This is the same shape as the 2026-09-18 incident the plan itself cites.
2. **There are four recorder call sites, not three.** `scripts/eval/eval_rollout.py:1238` is missing. Because the plan makes the new argument *required* (a good choice), the omission is a crash on every `eval_rollout.py --record`.
3. **The recorder does meet un-layered configs.** The plan's safety argument for using `get_mandatory` in the writer is that it "runs only in real evaluation, where the config has been resolved". But the *common* evaluation path (`eval_rollout.py --config <run>/models/config.yaml`, per that script's own comments) loads a run's **frozen saved config**, which has no `extends:` and cannot contain keys invented after the run finished. Every pre-change checkpoint would fail at `write_run_meta` when recorded. The compatibility layer the plan cites for this is itself still unimplemented.
4. **The legacy-recording rule reintroduces the width refusal.** For recordings without names the plan draws one map per channel and sizes the panel to fit. Measured with the real packer: a pre-change recording with vision at range 3 needs 634 px and is granted 520 px — the `LayoutOverflowError` that `4b6f7196` fixed. Three such recordings exist on disk. The user's decision was "positional names, not a refusal"; this is a refusal.
5. **The newly sanctioned silent overflow has no gate, and for vision it is not overlap but disappearance.** Mid-review the user removed the channel ceiling and chose "extra maps draw past the panel edge" over refusing. The plan references a checkpoint (`CP5b`) that renders such a frame for a human to look at, but the checkpoint is not in the list. And because map tiles are clipped to the band card while their labels are not, an over-slot *vision* run does not overlap its neighbour — its extra channels simply vanish from the picture, labels floating outside the card, with nothing in the frame or the audit to say so. (An earlier item here asked for a maps ≤ slots validation; that is withdrawn — it is now the accepted cost. See "Revision after the mid-review design change" below.)

What would flip the verdict is listed per finding below. None of the fixes is large; all of them are cheaper now than after CP7 has re-recorded the fixtures.

**Cost of being wrong.** No data loss — the only irreversible step (re-recording fixtures) already snapshots first. The cost is a feature that ships invisible on the production path with a green test suite, one to two days of rework, and — if published figures are regenerated in that state — frames labelled "Channel 3" in a paper figure.

---

## Findings

| Sev | Location | Issue | Suggested fix / exit condition | Owner |
|---|---|---|---|---|
| 🔴 C1 | Plan §8 (three writer call sites); `scripts/eval/eval_rollout.py:1238` | A fourth `write_run_meta` caller exists. With `channel_display` required, `eval_rollout.py --record` raises `TypeError` at meta-write. | Add the fourth site to §8. Keep the parameter required (it is what caught this). Add a grep-based test or a CP that runs `eval_rollout.py --record` on one checkpoint. | senior-developer |
| 🔴 C2 | Plan §D1 reason 3, §7; `scripts/eval/eval_rollout.py:692, 944, 959` | "The writer runs only where configs are layered" is false. The default eval path loads `<run>/models/config.yaml` — a frozen resolved copy with no `extends:` and no new keys — so `channel_display_from_config`'s `get_mandatory` raises for **every checkpoint trained before this change**. [[SAVED_RUN_CONFIG_COMPAT]] (cited by the plan) is PLANNED, not implemented. | Do **not** add a fallback default. The plan must (a) state this blast radius explicitly, (b) name how a pre-change checkpoint gets recorded — register the four keys in the compat plan's table and sequence that plan first, or accept that pre-change checkpoints cannot be re-recorded until it lands, and say so in the diary/wiki, and (c) add a CP that records one pre-change checkpoint through `eval_rollout.py --record` and records the observed outcome. | senior-developer (plan); user (accept/sequence) |
| 🔴 C3 | Plan §File Changes (omits `scripts/eval/render_recordings_v2.py`); that file at `:183-197` (`_worker_init`), `:223`, `:288` | The production video path and the benchmark path construct `EpisodeRenderer` directly from `params / icon_config / action_map`, never via `from_recording`. After this change every video renders through the legacy branch: positional names, 8 vision maps, no Terrain merge. CP4/CP5 go green via a different entry point; CP8 runs this file without looking at names. | Add `render_recordings_v2.py` (all three sites) to File Changes. Make CP4 render **through `render_recordings_v2.py`** on a regenerated cell and look at the output frame. Also audit `scripts/eval/render_recordings.py:83` (V1 path) for whether it reaches the dashboard. | senior-developer |
| 🔴 C4 | Plan §D5; `panels._span`; `layout.pack` band split | The legacy rule `max(PANEL_MAP_SLOTS, drawn)` with no groups draws 8 maps. Probe (`load_env_config(default.yaml)` + `visual_sensor_range` 1–4, `map_plan` patched to one-map-per-channel, `pack(ctx)`): ranges 1–2 fit; **range 3 raises `LayoutOverflowError: visual needs 634px … giving it 520px`**. On-disk legacy recordings at range 3: `results/render_audit/recordings/olf1_vis3_{smoke_20260918,spanfix,adaptive}` and the trained range-3 run cited in `4b6f7196`. Also, D5's "keeps exactly today's sizing behaviour" is false — today an 8-channel recording draws 6 maps; post-change it draws 8. | User decision, not the reviewer's: (a) declare legacy recordings at vision range ≥3 unrenderable and say so — contradicts decision #5; (b) change the band split from equal halves to need-proportional (a layout change with its own render proof, and the height-twin bug lives next door); (c) another rule. Whichever: CP3 must render a **legacy diamond-map recording** (`olf1_vis3_spanfix` or `olf1_vis2_spanfix`), not `M4` (see M1). | user → senior-developer |
| 🔴 C5 | Plan §D3 validation list, §D4, `painters.build_channel_maps:660` | No check that `len(map_plan(sense, display)) ≤ PANEL_MAP_SLOTS[sense]` for a configured recording. 8 vision channels + `visual_channel_groups: []` passes every listed rule; the painter uses `n = 6` for the slot divisor but iterates 8 maps, placing map *i* at `x0 + i*(slot+MAP_GAP)` — maps 6 and 7 land past the panel edge with no raise. This is the two-constants pair's unstated invariant. | Add to write-time validation: maps drawn ≤ `PANEL_MAP_SLOTS[sense]`, error naming both numbers. Make `panel_map_slots` raise (non-legacy) rather than return the constant when `drawn > slots`, so a hand-edited pickle cannot bypass the writer. Add it to CP6's deliberate-break list (remove the Terrain group, confirm the write fails). | senior-developer |
| 🟡 M1 | CP3 (`M4`), CP4 (`M1`) | Both cells read both senses at **range 0** (`M1` = `default.yaml` unmodified; `M4` = campfire, whose chain sets no range and `_DEMO_LOOSENING` touches only thermal/body). They draw the **rows** path (`build_channel_rows`), which the plan leaves alone. CP3 therefore never exercises `_span` / `build_channel_maps` on a legacy recording, and CP4's "same six vision maps, same widths" is unobservable on `M1`. | Use a cell built on `_E2` (vision range 2, e.g. `E2`/`E3`) for CP4, and a legacy `olf1_vis2_spanfix` / `olf1_vis3_spanfix` for CP3. Keep an `M1` render too — the rows path must still show configured names. | senior-developer |
| 🟡 M2 | CP4 "compare against the same frame rendered before the change" | The "before" frame is never captured, and cannot be captured after CP2 has regenerated `M1`. Regenerated content will differ from the on-disk cell anyway: the campfire world was retuned yesterday (`2bfe158e`) and bush blocking changed 09-14, so old-vs-new pixel comparison compares different episodes. | At CP2, after regenerating the cell with the new writer but the **old renderer**, render and keep the "before" PNG then. Or compare `layout_signature()` + panel boxes, not pixels. | senior-developer |
| 🟡 M3 | CP7 "re-run `render_layout_audit.py` … audit frames show real names" | The audit renders only `v1` / `v2` and **refuses** the dashboard renderer by design (`render_layout_audit.py:463-489`). Its frames carry the frozen V1/V2 label tables, so "real names" there says nothing about this change. Cannot fail for the right reason. | Replace with: render one regenerated cell through `render_recordings_v2.py` and look (this also covers C3). Keep the audit run only as a no-new-findings regression check. | senior-developer |
| 🟡 M4 | §11 "must still pass on pre-change fixtures (legacy path)"; CP7 | After CP7 re-records every cell, no fixture on disk lacks `channel_display`, so the legacy assertion in `test_render_recordings_v2` / `test_dashboard_frames` becomes vacuous and the positional path is ungated from then on. | Keep one cell un-regenerated (name it in the plan), or commit a tiny legacy `run_meta.pkl` + one short episode under `tests/env/fixtures/` so the legacy branch stays tested. | senior-developer |
| 🟡 M5 | §11 `test_dashboard_band_span.py` | Post-change there are **two** sizing regimes (legacy `max(slots, drawn)`; configured `slots`). The equality property must be asserted for both. And `test_an_off_standard_vision_width_is_declared_one_map_per_channel` (4 channels ⇒ 4 maps) becomes **false** on the configured path (4 channels ⇒ 6 slots) — it must be rewritten, not "updated". | Parametrize the property over `{legacy, configured}`; replace the off-standard test with "4 configured channels declare 6 slots; 4 legacy channels declare max(6, 4) = 6". | senior-developer |
| 🟡 M6 | §11, §12 (CONFIG_GUIDE contract item 3) | The contract requires a test proving a **missing** mandatory key raises. §11 tests length/index/duplicate but not absence of `sensory.visual_channel_names` reaching `get_mandatory` through `channel_display_from_config`. | Add one test per key: delete it from a resolved config, assert `ValueError` naming the key. | senior-developer |
| 🟢 L1 | §A3 second bullet | "A field added after a pickle was written is genuinely absent" holds only for fields with no class-level default; a dataclass field with a plain default remains reachable via the class attribute after unpickling — which would be a *silent fallback*, i.e. worse. Conclusion (not `EnvParams`) unchanged. | Tighten the sentence. | senior-developer |
| 🟢 L2 | §9 `_vision_dim(V)` | If the helper hand-copies entity lists into the script, the script becomes a second copy of `default.yaml`'s entities — two sources of one fact, in a plan about exactly that. | Build overrides from the resolved `cfg`'s own lists, rewriting only `visual_properties[_std]`. | developer |
| 🟢 L3 | §6 `write_run_meta` signature | `tests/env/test_dashboard_v1_imports.py:80` pins `startswith("(out_dir: pathlib.Path, params, icon_config")`. A new required parameter is fine **after** the existing ones; do not insert it earlier. | Note in §6. | developer |

## Author findings, verified

| # | Claim | Status |
|---|---|---|
| 1 | Parity gates load raw; `test_unified_parity` globs `experiment/**` with no archive exclusion | ✅ `test_unified_parity.py:49, 151`; `test_thermal_parity.py:247` |
| 2 | New `EnvParams` field is absent on old pickles | ✅ with the L1 nuance |
| 3 | Carriage = new top-level `run_meta` key; writer safe to `get_mandatory` | ✅ carriage; ❌ safety claim (C2); ❌ "three call sites" (C1) |
| 4 | `SUPERSEDED_VISUAL_LABELS` dead | ✅ only `labels.py:95` |
| 5 | Third size site is the range-0 rows path, left alone | ✅ — but note that `M1` and `M4` draw **that** path, so the plan's own CPs land on it (M1) |
| 6 | Olfaction `properties` not one-hot | ✅ `default.yaml:65, 90` |
| 7 | `E6sum` / `E6bin` never generated | ✅ no `E6*` dir; cells lack the background/entity overrides |
| 8 | Baseline red ×3 from a parallel session's staged move | not re-run; see O3 |

## Assumptions the plan quietly depends on

- ❓ **O1** — `evaluation_core.py:290` is only ever reached with a layered training config. True during training; unverified whether any script calls `evaluate_jax_checkpoint` post-hoc with a saved config.
- ❓ **O2** — `dreamer_srl/eval.py:83, 380` receive a config that resolved `extends:`. Probe-eval layers `get_default_config()` + files under the probe config; the saved-run case is unverified.
- ❓ **O3** — Git index at review time shows `D` (staged **deletion**) for both `05-…olf1_vis{2,3}.yaml`, not an addition as §A6 says. If they leave the tree, `test_dashboard_band_span.py`'s two config cases **skip** — "the quiet way a gate stops gating" per `4b6f7196` — and the CP0 baseline changes shape. Re-measure before CP0.
- ❓ **O4** — `Config.set("environment.entities", [...])` replaces a whole list cleanly (asserted in §A5, not demonstrated).
- ❓ **O5** — The `E6bin` cell, once it builds, packs and paints at vision range 2 with one map (should, but CP5 is the first time it is ever tried).

## Revision after the mid-review design change (same day)

Two user decisions landed while this review was in progress and the author revised the working
copy (uncommitted at review time; snapshot md5 `93d53725…`): **the channel ceiling is removed**
(no config is rejected for its channel count) and **maps beyond the panel's slot count draw
past the panel edge silently** — chosen over shrinking slots and over refusing. The slot count
(smell 5, vision 6) stays as the fixed panel width. `RECORDING_FORMAT_VERSION` stays unbumped.

**What this changes in the findings above.** C1, C2, C3 and every Moderate/Low finding are
untouched. **C5 is withdrawn** — the missing maps ≤ slots check is now the accepted behaviour,
not a gap. **C4 stands** but its option set moves (below). Two findings are added.

### Does the plan contain the inverted safety property, or weaken it more broadly?

Contained on the code path: the painter's only refusal (`if cs < 10`) sizes squares from the
**slot count**, so it still fires whenever the panel is too narrow for six maps, and the
packer's checks are unchanged. Not contained in the *statement* of the bound, in two places:

- §D4b says the carve-out "is bounded to configs that declare more channels than the
  conventional size — no shipped world does today". That is the wrong boundary. The overflow
  engages on **maps > slots**, which (a) the plan's own Consequence 2 shows is reached at the
  *shipped* channel count by deleting the Terrain group — an edit the how-to block invites —
  and (b) is the state of **every pre-change recording** (8 positional maps into 6 slots),
  which §D5 routes to a *different* rule (grow, not overflow). One arithmetic situation, two
  behaviours, and the bound sentence names neither. State the bound as "maps > slots", and say
  that legacy and configured recordings resolve it differently.
- §D4b line ~340 says "no instrument reports it" and then, twenty lines later, tabulates the
  audit rules that will. Both cannot be right; see the audit note below for which is.

### Which checks lose their teeth

| Check | Before | After |
|---|---|---|
| D3 "channel count > conventional maximum raises" | loud | removed — no CP tested it, so no CP changes |
| CP6 deliberate break (group names channel 9) | loud | **still loud** — D3's correctness checks stay |
| `test_dashboard_band_span` equality (declared == painter's need) and "refuses one pixel less" | implied *every map is drawn* | holds trivially for maps > slots: declared and divisor are both the fixed slot count, so the test is **green on a frame that hides channels**. The property no longer means what its docstring says; the docstring must say so. |
| Packer `LayoutOverflowError` on band width | fired at 8 maps × range 3 | never fires for configured recordings (width fixed); **still fires for legacy** under §D5's grow rule — C4 |
| **CP5b** (the rendered over-maximum frame, looked at by a human) | — | **referenced twice in §D4b, not present in the Checkpoints list** (snapshot lines 706–767: CP0–CP8 only). The only gate on the newly sanctioned silent behaviour does not exist. |

### The overflow is not the overflow the plan describes — 🔴 C6

§D4b says extra maps land "over the neighbouring sense panel, or off the card" and the audit
"will correctly report it". Which one happens depends on the sense, and the vision case — the
one the vision-dim knob makes likely — is worse than overlap:

- Both senses draw on **one band-card axes** (`episode.py:459-478`), olfaction left, vision
  right. Map tiles go through `style.rrect` → `ax.add_patch` (`style.py:102`), which Matplotlib
  **clips to the axes**; channel labels are `Text` artists, which it does **not** clip.
- **Vision over slots** → tiles 7 and 8 fall past the card's right edge and are **clipped
  away**; their labels float outside the card. A reader sees six maps and has no way to know
  the run had eight channels. No ink → nothing for the audit's fill rules to see; only the
  floating text can trip `text_over_border` / `out_of_canvas`.
- **Olfaction over slots** → tiles land **inside** the vision panel: real overlap, and the
  audit does report it.

So "silently" here means, for vision, *channels vanish from the picture without trace*. That is
a stronger form of the misleading-frame cost than the plan states, and it is exactly what CP5b
must show a human. **Exit**: write CP5b into the Checkpoints as a rendered frame at
**vision** channels > 6 with the Terrain group (and, separately, 8 channels with the group
removed), looked at and described in the Implementation Report; record what the audit says on
each beside a normal cell, as §D4b promises. Whether a non-refusing marker ("+2 channels not
shown") is wanted is the user's call — the reviewer only notes that the decision was taken
without seeing this frame.

### Audit scope statement

§D4b supplies one (compare the recording's map count to `PANEL_MAP_SLOTS[sense]`; maps > slots
⇒ band findings are expected). It needs one correction: for vision the rule runs the other
way — over-slot vision produces *fewer* findings, not more, because clipped tiles lay down no
ink. "Maps > slots and **no** band finding" therefore does not mean the frame is fine. Say so.

### C4 under the new decision

Legacy recordings still follow §D5's `max(slots, drawn)` — the grow rule the user rejected for
configured recordings — so a legacy range-3 vision recording still needs 634 px against 520 px
and **refuses**. The options are now sharper: (a) keep grow for legacy → range-3 legacy
recordings refuse (contradicts "not a refusal"); (b) apply the user's overflow rule to legacy
too → they render, with tiles 7–8 clipped and labels floating, on **every** pre-change
recording at range ≥ 1, not just range 3 (8 maps > 6 slots always). Either way the plan must
say which, and CP3 must render a legacy *diamond-map* recording (`olf1_vis3_spanfix`), not `M4`.

### Stale text the revision left behind — 🟡 M8

The snapshot still carries the ceiling in four places that would be implemented as written:
`__init__` exports `CONVENTIONAL_MAX_CHANNELS` (line ~527; an `ImportError` once deleted);
`panel_map_slots`'s docstring "the conventional maximum" (~477); the **config how-to block**
(~648) tells the user "a config declaring MORE channels than the conventional maximum fails
loudly; raising the maximum is a one-line change" — the opposite of the decided behaviour, in
the deliverable the user reads instead of code; and the test table (~676) asserts
`PANEL_MAP_SLOTS[s]` against `CONVENTIONAL_MAX_CHANNELS[s]`. The how-to line is the one that
matters: fix it to say what §D4b says.

### New consequence for CP5 and for the parallel vision-dim session — 🟡 M9

`E6bin` overrides `visual_vector_size: 1` but inherits `default.yaml`'s **8-entry**
`visual_channel_names` and the `[0, 1, 2]` Terrain group. Under §D3 the write-time validation
raises (length 1 ≠ 8; group index out of range), so CP5 cannot generate the cell as written —
the override dict must also set a length-1 names list and `visual_channel_groups: []`. The same
applies to **every** config that changes `visual_vector_size`, including the other session's
vision-dim configs under `basic/` (§D6 says this plan does not touch them): the day this lands,
recording from any of them fails at `write_run_meta` until they redeclare both keys. The how-to
block must state that rule ("if you change `visual_vector_size`, you must redeclare both keys"),
and the diary should warn the owning session.

## Passes skipped

- Pass 6 (experiment-plan specifics) — not an experiment plan.
- Pass 7 (empirical-claim soundness) — not an analysis verdict.

Prior-art pass done by grepping the Known Bugs registry directly: rows on the height twin (open), `RECORDING_FORMAT_VERSION` read nowhere, mandatory-key rollout (rows ~114–120) all match the plan's §A7; **C2 is a new instance of row 119's class** and should be recorded there by `bug-curator` once the user decides how to handle it.

---

## Third pass — re-review at `0dac47c1` (2026-09-19)

Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run · 🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

### Verdict, in plain language

**NOT READY**, on two findings that are new — not on anything from the first two passes. Every
earlier Critical (the production video script, the fourth writer, the frozen saved configs, the
legacy range-3 refusal) is applied in the committed text and its checkpoint can now genuinely
fail. The overflow decision, the rollout order, the no-version-bump, and the accepted
unrecordability of pre-change checkpoints are all respected here and none is re-raised.

What still blocks implementation:

1. **The plan promises a stronger guarantee than its mechanism delivers, in three places a
   future implementer will read.** The entry-point section says a bad merge group "must fail
   when the config loads"; the design section says every run trained after this change
   "records normally"; the how-to block says a sweep test catches mismatches. The mechanism is:
   nothing fails at config load; a run whose config has no `extends:` line inherits nothing
   and fails at its first recorded evaluation; and the sweep as specified looks only in one
   directory. Eleven such standalone configs exist today outside that directory, all inside the
   trees the parity gates sweep, five of them continual stage configs that the recording script
   resolves on its own (`scripts/eval/eval_rollout.py:677-724, :956`). This is the same
   overstatement the diary already corrected once (`939899be` → the 16:30 correction), now in
   the plan itself.
2. **The Terrain merge "becomes data" in the config and the layout, but the painter still
   hardcodes it.** `painters.py:706-709` reads channels `row[:3]` and a three-entry colour
   table whatever the group says. A group declared at channels `[1, 2, 3]` — which the plan's
   own validation permits — would draw the argmax of channels 0–2 under the label "Terrain".
   That is a quietly wrong picture, which is the exact failure class this plan exists to
   remove, and it sits on the step the author names as the riskiest.

Both have a short exit condition (below). Nothing else found is Critical.

### The disputed account of the second pass — settled on evidence

| # | Author's claim | What the record shows | Who is right |
|---|---|---|---|
| 1 | C4, C1, C3 "were already applied in `b0ab1fe3` … before your second pass reported them outstanding" | The second pass was committed at **16:15:33** (`3e563115`); `b0ab1fe3` at **16:22:49**. `b0ab1fe3` could not have preceded it. The second pass reviewed an **uncommitted working copy** (md5 `93d53725…`, stated in the report) whose checkpoint list ended at line ~767; in `b0ab1fe3` CP5b sits at line 1059, so the snapshot was ~300 lines shorter — mid-revision, as the report said. The snapshot blob is not recoverable (no stash, zero dangling blobs), so neither side can prove what it contained. At `b0ab1fe3` all three are applied: §D5b (line 531), §4b (701), §8 "Four writer call sites" (772). | **Author right on substance** (all three applied at the commit), **wrong on ordering**. The reviewer's error was reviewing a moving working copy and writing "C1, C2, C3 … untouched" — meant "unaffected by the design change", readable as "unaddressed". **From now on this reviewer reviews committed SHAs only.** |
| 2 | "CP5b cited twice and does not exist" came from a mid-revision snapshot | `fcd6faf2` has no CP5b at all; `b0ab1fe3` has it in the checkpoint list (line 1059) and cites it at 14, 421, 433. The second-pass report cites the snapshot's own line range (706–767, CP0–CP8 only). | **Both right**: true of the snapshot, moot at the commit. |
| 3 | M8 was two stale references, not four; the `__init__` export and docstring were already fixed; the surviving "FAILS when the recording is written" is group validation and true | At `fcd6faf2` there were four (lines 381, 431, 552, 580). At `b0ab1fe3` none survive; the only "fails" lines are the length rule (867) and the group rule (946), both correct and neither flagged. Whether two were already gone at the snapshot cannot be shown either way. | **Moot at the commit; the author's reading of the survivor is correct.** |

### Findings

| Sev | Location | Issue | Exit condition | Owner |
|---|---|---|---|---|
| 🔴 C7 | Plan §Context line 61; §D7 "What does not break"; §9b + §11 sweep scope; how-to block line 918 | **The guarantee is overstated.** (a) Line 61: *"A group naming a channel that does not exist must fail when the config loads, not quietly change the picture when the video renders"* — nothing in the plan fails at config load; §D3/§9b place every check at record time. (b) §D7: *"Every run trained after this change inherits the keys from `default.yaml` and records normally"* — false for any config with no `extends:` line. Measured today: **12 files outside `configs/environment/` declare `sensory:`**, 11 of them set `vector_size`, **none has `extends:`** (5 × `configs/continual/nmn_double_return_stages/`, 6 × `configs/verification/`, 1 × `configs/models/q_learning/`). They inherit nothing, so `channel_display_from_config` raises the D7 missing-key error for them **after** the change too. The five continual stage configs are exactly what `eval_rollout.py --record` resolves for a continual run (`:677-724, :956`). (c) §11's sweep is "default.yaml plus experiment/basic/" — a **directory** boundary; those 12 files are outside it, and `CLAUDE.md` names them as the rollout population for a new mandatory key ("`default.yaml` plus the handful of stand-alone configs outside `configs/environment/`"). §D6 confines the plan to `default.yaml`, which contradicts that rule. (d) The same 11 files are inside the parity gates' glob (`test_unified_parity.py:49-51`) — the constraint that forbids load-time validation and the population the sweep cannot see have one cause; say so. | (1) Rewrite line 61 to "fail when the recording is written". (2) Rewrite §D7's claim as: runs whose config **extends** `default.yaml` inherit the keys; **standalone** configs do not and must declare all four. (3) **User decision**: either add the four keys to the 12 standalone files (the `CLAUDE.md` rollout rule; ~2 keys × 12 files, olfaction names of length matching each file's `vector_size`, vision the 8-entry default) **or** declare them unrecordable in §D7 and the diary. No fallback either way. (4) The standing test sweeps **by content** — every `*.yaml` under `configs/**` declaring a top-level `sensory:` block — with the `archive/` path exclusion `test_backward_compat_configs.py:27-34` already uses (14 files guarded, 143 excluded), **and asserts a floor on the number of files collected** so an empty sweep cannot pass green. (5) Every sentence about the sweep is written as a commitment ("a test will…"), since the test does not exist; §9b currently reads as if it does. | user (3); senior-developer (1, 2, 4, 5) |
| 🔴 C8 | Plan §1 `map_plan` signature (`int \| None` channel), §3 `build_channel_maps`; `painters.py:706-709` | **The merge is data on the way in and a constant on the way out.** `map_plan` returns `(name, qualifier, kind, channel)` with `channel=None` for the terrain map; the painter's per-step update reads `np.max(row[:3])` / `np.argmax(row[:3])` and indexes `P.TERRAIN_FILL` (three colours). The plan permits a group anywhere contiguous with ≥ 2 channels (§D3) — so `{name: Terrain, channels: [1, 2, 3]}` validates, draws its map at the run's first position, and colours it from channels **0–2**. A group of 2 or 4 channels indexes a 3-colour table. Nothing raises; the label is right and the picture is wrong — the "quiet mistake" the plan is named for, on the step the author calls the riskiest. The discipline the plan relies on (`panel_map_slots` from one function; equality test both regimes; constant anchored to the shipped world) covers the **count** and is sound for that; it does not cover **which channels** the merged map reads. | `map_plan` carries the group's channel tuple in the map entry (e.g. `channel: int \| tuple[int, ...]`); the painter reads `row[list(chs)]` for a group and never a literal slice; `TERRAIN_FILL` length vs. group length is either validated at write time (`len(channels) ≤ len(P.TERRAIN_FILL)`, naming both) or the palette is generalised — author's choice, stated. CP6 gains a deliberate break: a group at `[1, 2, 3]` rendered **and looked at**, confirming the merged map follows the config. §11's new test asserts the terrain update reads the configured channels (build a frame with a shifted group and check which channels change the tile). | senior-developer |
| 🟡 M10 | `tests/env/test_dashboard_band_span.py:257-282`; plan §11 row 2, CP0 | Two problems, one test. (a) `pytest.skip` at `:266` when the config is absent — both configs it names are **staged for deletion** (`git status`: `D`), so after that lands the wide-sense cases skip forever; the plan records this (CP0) but does not fix it. (b) After this change `LayoutContext.from_params(...)` with no payload is the **legacy** regime, so the `olf1_vis3` case — if its config survives — asserts that a legacy range-3 context packs, which §D5b now says must **refuse**. The case is wrong on both branches. | Rewrite the case to build its context from `default.yaml` plus range overrides (`olfactory_grid_range: 1`, `visual_sensor_range: 2` and `3`) with a **configured** display via `channel_display_from_config` — no dependency on a config file another session owns, no skip. Add the mirror: a **legacy** range-3 context refuses with §D5b's message (CP3(b) as a unit test). | senior-developer |
| 🟡 M11 | Plan §9b residual ("fails only at evaluation") | The peer's proposal — fail when the recorder is **configured** rather than at the first checkpoint video — is achievable without touching `load_env_params`: call `channel_display_from_config(config, params)` once at trainer start whenever video recording is enabled (the trainer holds both objects; the parity gates never run it). It turns "hours in on a GPU" into "first seconds". It is a **backstop, not a guard**: it fires only in a run that records, gives zero commit-time coverage, and does not reach the verification configs (which never record). It is worth having **after** the content sweep and worthless **instead of** it. | Adopt or decline explicitly in §9b; if adopted, label it "backstop" in those words and add the trainer-start call site to File Changes and a CP that runs a mismatched config and records where it stopped. | senior-developer → user |
| 🟢 L4 | §D4b/§D4c "warn at load" (lines 455, 469); §1 vs §D4c warning site | "At load" here means "when the renderer builds the display" — in a plan whose central residual is "**not** caught at config load", the word must not be reused. Also `panel_map_slots` is called from `_span` (twice, via both min-size functions) and from the painter, so one renderer build logs the warning ~3×, ×30 episodes in a batch. §1 puts the warning in `panel_map_slots`, §D4c in `ChannelDisplay` — two sites named. | Say "when the display is built"; pick one site; warn once per `(sense, drawn, slots)`. | developer |

### The author's substitution (record-time failure + standing test) — judged

**Sound in direction, incomplete in coverage.** The reason load-time failure is unavailable is
verified (`test_unified_parity.py:49-51, :151` and `test_thermal_parity.py:247` load raw with no
`extends:`; 38 standalone configs load today; a new `get_mandatory` in `load_env_params` turns
them red). Record-time failure is real and cannot be bypassed — a recording with mismatched names
cannot be written. The residual (loads, trains, fails at first checkpoint video) **is stated where
a config author reads it** (how-to block, lines 913-921) — that requirement is met.

**Can the test fail?** For the population it sweeps, yes: it goes through the resolving loader
into `channel_display_from_config`, so a `basic/` config that sets `visual_vector_size: 1` and
inherits the 8-entry list fails on length; and a config **added later to `basic/`** is caught
**only if the test globs the directory** rather than listing files — §11 says "sweep every
maintained config" without saying which; the parity gates' `_collect_configs` (glob) is the
pattern to copy, plus a collected-count floor. As specified it **cannot** fail for the 12
standalone files outside `configs/environment/`, which is C7.

### Are the earlier checkpoint fixes genuine, not reworded?

| CP | Earlier defect | Now | Verified |
|---|---|---|---|
| CP3 | ran on `M4` (range 0, rows path) | `olf1_vis2_spanfix/recordings/77` (range 2, must draw 8 positional maps) and `olf1_vis3_spanfix/recordings/71` (range 3, must refuse with §D5b's message); `M1` kept for the rows path | both directories exist on disk with `run_meta.pkl` + episodes; they are diamond-map recordings |
| CP4 | `M1` (range 0), scratch renderer | regenerated `E2`/`E3` (both built on `_E2`, vision range 2, fixture script lines 283/291) rendered **through** `scripts/eval/render_recordings_v2.py` | the three construction sites in §4b match the code: `_init_worker` state at `:195-198`, `_render_episode` at `:223`, `_benchmark` at `:288`; `render_recordings.py` is V1 (`render_jax_state`, `:93, :131`), no dashboard import — §4b's second claim holds |
| CP7 | gated on the audit, which refuses the dashboard renderer | render one regenerated cell through `render_recordings_v2.py` and look; audit demoted to no-new-findings regression; `M4` and the six `olf1_vis*` runs left as legacy subjects | genuine |
| CP2b(b) | — | pre-change subject `results/render_audit/olf1_vis3_spanfix/models/config.yaml` exists, carries `visual_vector_size: 8`, no `extends:`, none of the new keys | genuine |

### The riskiest step — does the discipline hold?

For the **count**, yes: both `panels._span` and `painters.build_channel_maps` are required to
ask `panel_map_slots(sense, display)` and never recompute; the legacy `max(slots, drawn)` and
configured `slots` regimes live in that one function; the band-span equality property is
parametrised over both; and `PANEL_MAP_SLOTS` is pinned to a measurement of the shipped world.
That is the `4b6f7196` lesson, applied. For **which channels** the merged map reads, no — C8.

### Assumptions the plan depends on

- ❓ **O6** — `Config.set("environment.entities", [...])` replaces a whole list cleanly (§A5; still asserted, not demonstrated — CP5 is the first attempt).
- ❓ **O7** — `TERRAIN_FILL`'s three colours are the only group palette wanted; a non-terrain group (e.g. two smell channels) has no colour rule in the plan.
- ❓ **O8** — no script calls `evaluate_jax_checkpoint` with a saved (frozen) config post-hoc; a repo grep finds **no** direct caller by name in `src/` or `scripts/`, so the training-time writer's config source could not be traced this pass.

### Cost of being wrong

If C7 ships as written, the first continual run someone records after this lands dies at
`write_run_meta` with a message the plan promised could not occur, and the doc that future
sessions implement against says the opposite of what the code does — the third time this
guarantee has been overstated in this plan's life. If C8 ships, a config that moves or resizes
the Terrain group produces a correctly-labelled, wrongly-coloured map with no error anywhere,
which is the precise defect the user commissioned this plan to make impossible. Neither loses
data; both cost a rerun of the fixture regeneration and, if figures are published in between, a
wrong panel in a paper figure.

### Passes skipped

Pass 6 (experiment-plan specifics) and pass 7 (empirical-claim soundness) — not applicable to an
engineering plan. Prior-art pass: Known Bugs rows 115 (mandatory-key rollout), 119 (saved run
configs), 120 (`test_backward_compat_configs` blind on `extends:` worlds) and 173 (the fixed
width bug) all re-read; C7 is a new instance of row 115's rollout rule and should be recorded
there by `bug-curator` once the user decides item (3).

*Reviewed by: plan-reviewer*
