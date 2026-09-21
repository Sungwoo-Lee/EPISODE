---
title: "Plan review: sensor channel names from config + fixed-size sense panels"
topic: reviews
status: active
created: 2026-09-19
last_updated: 2026-09-21
---

# Plan review: sensor channel names from config + fixed-size sense panels

> **Reviewed**: [[DASHBOARD_CHANNEL_NAMES_FROM_CONFIG]] — five passes: `fcd6faf2` (first), an uncommitted mid-revision working copy (second), `0dac47c1` (third), `b2804376` (fourth), and `d3d61bf5` (fifth, current).
> **Current verdict (fifth pass, at `d3d61bf5`)**: **NOT READY** — on one Critical that is a git-safety hazard in a checkpoint's rollback, not a design defect: the design itself is now implementable, and both of the fourth pass's Critical fixes were re-measured and hold. See "Fifth pass" at the end of this file.
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

---

## Fourth pass — re-review at `b2804376` (2026-09-20)

Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run · 🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

Reviewed at the committed SHA only. Every measurement below was taken on the working tree of
2026-09-20, which carries the parallel session's uncommitted vision-dim rollout; nothing in that
rollout was staged, edited or reverted by this review.

### Verdict, in plain language

**NOT READY**, on two findings that come from the baseline moving under the plan — not from
anything the third pass asked for. Everything the third pass asked for is applied at the commit:
the eleven standalone configs get the keys (C7), the terrain painter reads the channels its group
names (C8), the wide-sense test is rebuilt (M10), the trainer-start check is adopted and called a
backstop in those words (M11), and "at load" is gone (L4). The user's closed decisions — no
version bump, `run_meta.pkl` carriage, no ceiling with a warning, legacy range-3 refused, the
documented limit on pre-change checkpoints, keys added to the standalone configs — are respected
and none is reopened here.

What blocks implementation now:

1. **The eleven standalone configs are not what §7b says they are, and two of them have vision
   switched off.** §7b says they were "verified … carrying their own channel counts" and resolve
   to eight vision channels. Measured: every one declares `vector_size: 5`, and **none declares
   `visual_vector_size`, `visual_background_properties`, or a single entity `visual_properties`**.
   Their vision width of 8 is the loader's `.get(..., 8)` fallback — the very fallback §A3 cites
   as the reason the key must not be made mandatory — and their entity vectors are the loader's
   own auto-generated one-hot table. Two of them (the olfaction-parity pair) have
   `visual_sensor_enabled: false` and no entities at all, so §7b as written would have them
   declare eight vision names for a sense that is off — the exact reason the plan gives for
   *excluding* `q_learning.yaml`. The plan has no rule for a disabled sense, and the developer
   cannot invent one.
2. **Every checkpoint that needs an 8-channel frame has no buildable source after the rollout.**
   CP2's before-frame, CP4, CP5b and CP6's shifted-group render all need a *recordable* world
   with at least eight vision channels. Both routes CP4 names fail: a fixture override from the
   1-channel base needs an entity-to-channel assignment the base no longer contains, and the
   archived `basic_vec8/` files are refused by the fixture script's own maintained-set gate, lack
   the four keys (so the override guard refuses to add them), and one of them extends the *live*
   1-channel ladder. The developer would be left to improvise the source — most likely by hand-
   copying the old entity lists (the two-source problem L2 already flagged) or by migrating an
   archived config (which CLAUDE.md forbids).

Both have short exits, stated per finding below.

### The questions this pass was asked, answered

**Does the plan hold against the new baseline, or only the one it was written for?** Mostly the
new one, with four stale spots. The how-to block is correct against the working tree: the smell
table matches the columns exactly (food→0, predator `[0,.7,.5]`, rabbit `[0,.5,.7]`, bush→3,
tree→4 at `default.yaml:30, 65, 90, 125, 144`), and the vision block honestly describes one
channel every entity writes `[1.0]` into. The `PANEL_MAP_SLOTS` anchor is correctly re-pointed at
an explicit in-memory 8-channel display. CP4's "dim 8 unchanged from today" is corrected in words
but has no source to build from (C10). The four stale spots: CP2's before-frame is captured on
"a vision-range-2 cell" — `E2`/`E3` are built on the base, which is now one channel, so the
before-frame would be a 1-channel frame compared against an 8-channel after-frame (folded into
C10); `M1` is the base config with no overrides and no longer draws the rows path (M14); §A5/§9's
"`E6sum`/`E6bin` do not build" is now false — both set `visual_vector_size: 1` on a base that
already is 1 (M13); and §A8's table omits two more rollout changes, `visual_blur_enabled: false→true`
and `visual_value_mode: sum→clamp` (M13).

**Is the ordering decision overtaken, and does the plan say who reconciles?** Overtaken, and
benignly — but the plan does not say so. Verified: **none of the seven `basic/` configs redeclares
`visual_vector_size`**; all inherit 1 from `default.yaml` (their `visual_properties: [1.0]` is
entity-level). So they inherit the 1-entry names list and empty group too and are consistent by
construction. There is nothing for the other session to add, yet §A8 tells the developer to treat
§9b step 3 as live and "report and stop" — a halt on a non-event (M13). The sweep test (§11) is
what proves the reconciliation: all seven must pass once `default.yaml` carries the keys.

**Does the rationale for config-driven vision names still hold at one channel, and does the
how-to teach from olfaction?** Yes to both. The rationale — one source for a name, the in-code
table deleted — is carried by olfaction's five genuinely distinct channels and by every world
wider than one channel (the nine vision-enabled standalone files today; any future arm). The
how-to teaches smell first, with the column-reading lesson on channels 1–2, and the vision block
says plainly that channel 0 means "something is here". One correction is needed to the vision
block's own words: it calls its 8-channel table "the reference for configs that set a wider
vision", but after the rollout no config on disk carries that layout — the only 8-channel worlds
left are the nine standalone files, whose layout is the **loader's** auto-generation table
(`config_loader.py:1735-1754`, background one-hot at `~1988`). The comment should say that is
what it documents (folded into C9).

**C8's fix, on the mechanism.** The forbidden-constant rule covers every branch that exists.
Channel data is read in exactly three places in `painters.py`: the terrain branch (`row[:3]` at
`:707, :709` — the only literal), the seq branch (`row[ch]` at `:713`, already driven by
`map_plan`), and the range-0 rows path (`zip(setters, vec)` at `:625`, positional, ignores groups
— consistent with today, and §D6 should say the rows path ignores groups *deliberately* so nobody
later "fixes" it to merge). The `argmax(vec)` at `:508` is proprioception, not a sense channel.
The author's residual is real — prose forbids the next literal, nothing structural does — and
the project already has the pattern for making it structural: `test_dashboard_band_span.py:224-238`
pins `MAP_GAP` by reading the painter's source. A one-line source test asserting `row[:` does not
appear in `painters.py` closes it (L6).

**Can each checkpoint still fail?** CP0, CP1, CP2b, CP3(a)(b), CP5, CP6(a–d and the sweep), CP7,
CP8 — yes, subjects verified. CP2's before-frame, CP4, CP5b, CP6's shifted-group render — **no
source to build** (C10). CP3(c) and CP4's rows-path render on `M1` — **land on the wrong path**
(M14).

**M10, both branches.** The configured branch is right: `default.yaml` plus range overrides with
a configured display at vision range 3 declares six slots = 487 px against the 520 px band grant,
packs, and paints one map. The legacy mirror is **wrong on the new baseline**: "the same world,
the other regime" is now a 1-channel legacy context, which at range 3 draws one map needing
102 px — it fits and nothing refuses. The mirror either fails (need-keyed refusal, nothing to
refuse) or passes only if the refusal is keyed on `range ≥ 3`, which would also refuse a
legitimate 1-channel legacy recording — for instance the `E7` cell recorded from today's tree
before this lands. §D5b's predicate must be need-versus-grant, not range (M12).

**The sweep floor.** 32 collected, 19 resolving through the resolving loader — both verified
(`glob` copied from `test_backward_compat_configs.py:24-42`; HEAD's tree has 34 before the
rollout's deletions). The 13 non-resolvers are all top-level `configs/continual/` schedules,
every one failing on `sensory.visual_value_mode is required`. Two cautions: the collector's own
*loader* is raw `Config` with no `extends:` — copied wholesale it resolves only 12 and skips all
seven ladder worlds (the 19-floor would catch that, which is the floor working); and a floor is a
floor — a **new** maintained file that fails to load is skipped with the count still ≥ 19, so the
sweep can silently stop covering an *added* file (M15).

**Project rules.** No fallback default introduced by the plan (C9 is about a pre-existing one the
plan leans on without saying so). No version invented or bumped. Maintenance contracts: §12
covers CONFIG_GUIDE, the schema table and a CRITICAL_SETTINGS change-log entry; no `scripts/` file
is added, moved or renamed, so the dependency map is correctly not required. Archived configs:
the plan never migrates one — the only near miss is CP4's "or the archived `basic_vec8/`
variants", which C10 removes.

### Findings

| Sev | Location | Issue | Exit condition | Owner |
|---|---|---|---|---|
| 🔴 C9 | Plan §7b lines 907–927; `configs/continual/nmn_double_return_stages/0{1..5}_*.yaml`, `configs/verification/observability_gates_S{1..4}.yaml`, `configs/verification/olfaction_parity_{neutral,predator}.yaml`; `src/environment/config_loader.py:1687-1688, 1735-1754, ~1988` | **§7b rests on a false measurement and has no rule for a disabled sense.** "Verified … carrying their own channel counts" — none of the eleven declares `visual_vector_size`, `visual_background_properties` or any entity `visual_properties` (script over all eleven, 2026-09-20). Vision width 8 is the loader's `.get(..., 8)` fallback; entity vectors are the loader's auto-generated one-hot (`_default_ch = 3 if food else 4`; background rows 0/1/2). The two parity files have `visual_sensor_enabled: false` and no entities, so §7b's instruction gives them eight vision names for a sense that is off — the reason the plan itself excludes `q_learning.yaml`. The distinction §7b draws ("declares no `vector_size` and no `visual_vector_size`") does not separate the cases: none of the eleven declares `visual_vector_size` either. | (1) Rewrite the "verified" sentence to what is true: the eleven declare olfaction's count and inherit vision's from the loader's default. (2) **Decide the disabled-sense rule** — recommended: `channel_display_from_config` reads a sense's two keys only when that sense is enabled in `params` (the renderer already never draws an unobserved sense: `panels.py:258-261`, `episode.py:457-459`), and the payload carries no entry for it. That makes the `q_learning` exclusion structural (`using_sensory: false`) rather than by fiat, and the parity pair need olfaction names only. The alternative — always required — must then say why eight names for an off sense is not the quiet mistake §7b calls it. No fallback either way. (3) For the nine vision-enabled files, state that the 8-entry list is correct only because it matches the loader's V=8 auto-generation, and have the developer confirm each file by reading the resolved params' per-entity `argmax` — not by copying the how-to. (4) The how-to's vision block says its 8-channel table is "the reference for configs that set a wider vision"; after the rollout it documents the loader's default table, and should say so. | user (2); senior-developer (1, 3, 4) |
| 🔴 C10 | CP2 before-frame; CP4 "build the 8-channel world explicitly … or the archived `basic_vec8/` variants"; CP5b (a)(b); CP6 shifted-group render; plan §9 `_vision_dim(V)`; `scripts/eval/make_render_fixture_recordings.py:368-377` (`_require_maintained`), `:437-446` (override guard); `configs/environment/experiment/archive/basic_vec8/05-campfire_thermal_10x10.yaml:87` | **No recordable 8-channel world exists for the four checkpoints that need one.** Route A (override `visual_vector_size: 8` on the base): the base's entities carry `visual_properties: [1.0]`, so at width 8 each raises "length 1 but visual_vector_size is 8"; the assignment food→3, hiding_predator→4, … is not in the 1-channel config, and §9's helper is specified for the shrink direction only. Route B (archived `basic_vec8/`): refused outright by `_require_maintained` (only `default.yaml` or `basic/`); they extend `archive/basic_vec8/default.yaml`, which lacks the four keys, so `get_mandatory` raises and the override guard refuses to supply a key the config does not have; and `basic_vec8/05` extends the **live** `basic/04` (now 1-channel), so its chain is broken regardless. Also CP2's "before" frame is taken on `E2`/`E3`, which are 1-channel now, and CP4 compares an 8-channel after-frame against it. | (1) Redefine §9's helper for both directions, and name the 8-channel source: for width 8, **strip** `visual_properties[_std]` from every entity in the resolved config and set `visual_background_properties` to `None`/absent, so the loader's own V=8 auto-generation supplies the canonical one-hot (`config_loader.py:1748-1754` permits absence only at V=8 — the one width where it is allowed). That is one source (the loader's table), not a hand-copy. (2) Add the two display keys to the same override (8-entry list, `{Terrain,[0,1,2]}`) — they exist in `default.yaml` after CP2, so the guard allows them. (3) CP2's before-frame is captured on the **same** 8-channel cell CP4 renders, with the old renderer. (4) Delete "or the archived `basic_vec8/` variants" from CP4. (5) For CP5b(a)'s 12-channel cell the assignment is arbitrary and may be synthetic; say so in the cell description. | senior-developer |
| 🟡 M12 | Plan §D5b; §11 band-span row (M10) "the same world, the other regime"; `tests/env/test_dashboard_band_span.py:76-86` | **The legacy mirror is built from a world that no longer refuses, and the refusal predicate is stated by range.** A 1-channel legacy context at range 3 draws one map needing 102 px against 520 px granted — it fits. The mirror as specified either fails (need-keyed) or passes only under a `range ≥ 3` rule that would also refuse a legitimate 1-channel legacy recording (the `E7` cell, recorded from today's tree before this lands, is exactly that). §D5b's "legacy recordings at vision range ≥ 3 are declared unrenderable" was measured at 8 maps and is now a function of the recording's channel count. | State §D5b's predicate as **need versus grant** (`max(slots, drawn) × (2r+1) × 10 + gaps + padding` against the band's grant), never the range. Build the mirror's legacy context in-memory with `visual_vector_size=8` and no payload — `_ctx` already does this — and add the third case: a 1-channel legacy context at range 3 **renders**. | senior-developer |
| 🟡 M13 | Plan §A8 (table and "Consequence for the agreed ordering"); §A5; §9 `E6sum`/`E6bin` fix; §A2 item 3; CP5 | **Four stale premises after the rollout.** (a) No `basic/` config redeclares `visual_vector_size` — all seven inherit 1 — so nothing needs redeclaring, the other session has nothing to add, and "report and stop" halts the developer on a non-event. (b) `E6sum`/`E6bin` now build: they set `visual_vector_size: 1` on a base already at 1 with matching entities; §9's fix is unnecessary. (c) §A8's table omits `visual_blur_enabled: false→true` and `visual_value_mode: sum→clamp` (`git diff HEAD -- configs/environment/default.yaml`). (d) §A2 item 3 says the base ships range 0 for both senses so the rows path is "the path most maintained worlds actually draw" — the base now reads smell at range 1 and vision at range 2, so **every** maintained world draws diamond maps and none draws rows. The §D6 decision to leave the rows path alone still stands; its justification sentence does not. | Rewrite §A8's ordering paragraph: the reconciliation is empty, the sweep proves it, the developer proceeds. Mark §A5/§9's E6 fix as no longer needed. Complete the table. Correct §A2 item 3 and CP5's "at `visual_sensor_range: 2`" (already so). | senior-developer |
| 🟡 M14 | CP3 "Render `M1` as well, to confirm the rows path still shows names"; CP4 "also render a range-0 cell … for the rows path"; `make_render_fixture_recordings.py:213` | **`M1` no longer draws the rows path.** It is `default.yaml` with no overrides, which now reads both senses at range ≥ 1. Both rows-path renders land on diamond maps and cannot fail for their stated reason — the same shape as the third pass's M1. | Give the rows-path render an explicit cell with `olfactory_grid_range: 0` and `visual_sensor_range: 0` overrides (both keys exist, so the guard allows them), and name it. | senior-developer |
| 🟡 M15 | Plan §9b sweep scope ("copy the collector … assert a floor on both numbers"); `tests/env/test_backward_compat_configs.py:20-42` | **The floor catches removals, not additions that skip; and the collector's loader is raw.** Copied wholesale, the collector's raw `Config` load resolves 12 of 32, skipping all seven ladder worlds (the 19-floor would fire — good — but the plan should say "copy the glob, not the loader"). More important: with skip-on-load-error, a **new** `basic/07-*.yaml` that fails to load is skipped, the count stays ≥ 19, and the sweep is green on a maintained world it never checked. | Skip is permitted only for files directly under `configs/continual/` (the 13 schedules, all failing on `sensory.visual_value_mode`); every file under `configs/environment/**`, `configs/verification/**` and `configs/continual/nmn_double_return_stages/` must resolve or the test fails naming the file. A `channel_display_from_config` raise is always a failure, never a skip. Keep the two floors. | senior-developer |
| 🟢 L5 | §10 "after `visual_vector_size: 8` (line 233)"; §7c "`train.py:2555`"; frontmatter | Line drift: `visual_vector_size: 1` is at `default.yaml:256` now; the video branch is `if eval_v_flag:` at `train.py:2552` with the call at `:2557-2560`. `last_updated: 2026-09-19` on a doc whose §A8 is dated 09-20. | Fix on next revision. | senior-developer |
| 🟢 L6 | §3 "no channel index may be spelled as a constant anywhere in this file" | Prose invariant with no structural check; the author names this residual. The project's own precedent is a source-grep test (`test_dashboard_band_span.py:224-238`). | One assertion in the new test file: `"row[:" not in painters.py source`. Optional. | developer |

### Assumptions the plan depends on (this pass)

- ❓ **O9** — `Config.set` on an entity list can *remove* a key from each entity dict (C10 exit (1) needs it, or an equivalent wholesale replacement without `visual_properties`). Not demonstrated; CP4 would be the first attempt.
- ❓ **O10** — the loader's V=8 auto-generation for the two animal classes (`_load_animals`, `config_loader.py:1202-1229`) assigns predator→5 and neutral→7 as the how-to's reference table says; verified for food (3) and hiding_predator (4) at `:1747`, not for animals this pass.
- ❓ **O11** — the parallel session's rollout lands as it stands in the working tree. If it is amended before this plan is implemented (for instance restoring a range or a width), §A8, C10's source and M12's numbers move again. The developer re-measures at CP0.

### Cost of being wrong

If C9 ships, two verification configs carry eight vision names for a sense that is off and nine
carry a list whose correctness depends on a loader default nobody wrote down — the quiet-mistake
class the user commissioned this plan against, in the files that resolved the previous Critical.
If C10 ships, the developer reaches CP2 with no way to capture the before-frame and improvises an
8-channel world by hand — most likely a second copy of the old entity lists, or a migrated
archived config — and CP4/CP6's human-inspected frames are then frames of a world nobody
specified. Neither loses data; both cost a day and a fifth pass. The Moderates each cost a
checkpoint that goes green without testing what it says.

### Passes skipped

Pass 6 (experiment-plan specifics) and pass 7 (empirical-claim soundness) — engineering plan.
Prior-art pass: Known Bugs rows 114 (format stamp), 115 (mandatory-key rollout), 119 (saved run
configs), 120 (`test_backward_compat_configs` blind on `extends:` worlds), 125 (height twin) and
173 (fixed width) re-read; nothing new walked into. Row 435 (noise painted on the wrong channel,
2026-01) is the ancestor of C8's class and worth a cross-reference when `bug-curator` records C8.

*Reviewed by: plan-reviewer*

---

## Fifth pass — re-review at `d3d61bf5` (2026-09-21)

Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run · 🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

Reviewed at the committed SHA only. Every measurement was taken on the working tree of
2026-09-21, which still carries the parallel session's uncommitted vision-dim rollout
(` M` on `default.yaml` and seven `basic/` files, two staged deletions, untracked
`archive/basic_vec8/`); nothing in that rollout was staged, edited or reverted by this review.

### Verdict, in plain language

**NOT READY** — but for the first time not on the design. Both fixes the fourth pass demanded
were re-derived independently and **hold in full**: the eleven standalone configs resolve to five
smell channels and eight vision channels with the loader's own channel assignment, the two
olfaction-parity files have vision switched off, and the "strip the entity vectors and let the
loader auto-generate" route to an 8-channel world builds through the fixture script's own
override guard and assigns exactly the channels the plan's reference table says. The
enabled-sense rule is evaluable from two static `EnvParams` fields and does what it claims.

What blocks implementation is one line in a checkpoint. **CP2's rollback — "`git checkout` the
affected files" — would discard the parallel session's uncommitted rollout**, because
`configs/environment/default.yaml` is one of the files this plan edits and it currently carries
their unstaged 8→1 channel change. Working-tree edits have no reflog; that revert is
unrecoverable except by redoing their work. The same file cannot be *committed* whole either
without sweeping their hunks under this plan's message, which `CLAUDE.md` forbids, and `git add
-p` is not available in this environment. The plan says nothing about either direction. This is
a git-safety hazard of the class the project lost `results/` to, and the fix is three sentences.

Everything else found is Moderate or Low, and most of it is stale text left behind by the
fourth pass's corrections: a sweep-scope sentence that contradicts the corrected one, a
"report and stop" instruction withdrawn in one section and live in another, and an explanatory
number that disagrees with the rule beside it. One Moderate is new information the user should
see: the fixed six-slot vision panel **refuses to pack at vision range 4** (602 px needed
against 520 granted, measured with the real packer) for configured and legacy recordings alike,
where today's live-count sizing renders a one-channel range-4 world in 122 px. Fixed size caps
renderable vision range at 3 under the current band split, and the plan does not say so.

**Two disclosures.** (1) The §11 test-spec row and CP6's sweep sentence that contradict §9b
were already in the text at `b2804376`; I verified C7's fix from §9b and did not check that the
correction had propagated — that was mine to catch. CP2's rollback wording likewise predates
this pass. (2) My first read of the loader's channel assignment paired the wrong labels with
the wrong slots (the loader expands each entity entry to `count_high` slots, and I zipped two
labels against ten values) and briefly showed hiding_predator→3 and rabbit→5. Re-run aligned by
slot, the author's numbers are exactly right. That is the count-versus-value class of error the
brief warned about, on the reviewer's side this time, and it is recorded here so the pattern is
visible.

### The five questions this pass was asked

**1. Verdict, and is it implementable?** NOT READY on C11 alone. The design is implementable as
written; every checkpoint except CP2's rollback has a subject that exists and a check that can
fail. What flips the verdict: CP0 snapshots the rollout, CP2's rollback for `default.yaml` is
"reverse-apply this plan's own hunks", and the plan says how `default.yaml` is committed while
another session's edits sit in it.

**2. C10's measurements, re-derived.** All hold. On the working-tree base: strip
`visual_properties` / `visual_properties_std` from every entry in `environment.resources`,
`environment.entities`, `environment.obstacles`; set `sensory.visual_vector_size: 8`; set
`sensory.visual_background_properties` to `None` → `load_env_params` returns `vis=8 olf=5`.
Per-slot `argmax` of the resolved property arrays: resources `[3,3,3,3,3,3,4,4,4,4]` (food ×6
→ 3, hiding_predator ×4 → 4), animals `[5,5,7,7]` (predator ×2 → 5, neutral/rabbit ×2 → 7),
all 22 obstacle slots → 6, background rows → `[0,1,2]`. The same overrides passed through the
fixture script's own `build_params` (with its "key must already exist" guard) build at `vis=8`
— so O9 (wholesale list replacement, `set(..., None)` read as absent) and O10 (animal classes
→ 5 / 7) are both closed. Note the route depends on `sensory.visual_background_properties`
*existing* in the base so the guard passes before it is nulled; it must exist at V=1, so this
is stable.

**3. The enabled-sense rule as written.** Sound where it is stated (§7b): `olfactory_enabled`
and `visual_sensor_enabled` are static `EnvParams` fields (`state.py:282, 285`), set from
`sensory.olfactory_enabled` / `sensory.visual_sensor_enabled` (`config_loader.py:2332, 2336`).
Measured raw (no `extends:`): nine of the eleven resolve `olf_on=True vis_on=True`; the two
parity files resolve `olf_on=True vis_on=False`. A sweep that calls
`channel_display_from_config` inherits the rule automatically and would fail the parity pair
only if vision names were demanded — which the function, as specified, does not do. Three gaps:
the §11 row and CP6 that *specify* the sweep still carry the pre-C7 directory scope and never
mention the rule (M17); the plan does not say whether display keys present for a *disabled*
sense are ignored or refused (M17); and `q_learning.yaml`'s "structural" exclusion is
attributed to `using_sensory: false`, a key **no code reads** (M16). On the render side the
rule makes the legacy signal ambiguous (M20).

**4. Can every checkpoint still fail?** CP0, CP1, CP2 (before-frame on the grown cell —
buildable, verified), CP2b(a)(b), CP3(a)(b) (both on-disk recordings exist), CP3/CP4's rows
render (explicit range-0 cell — correct, though not yet named), CP4, CP5 (base resolves
`vis=1 olf=5 olf_range=1 vis_range=2` — verified), CP5b, CP6(a)–(d) and the shifted-group
render, CP7, CP8 — yes. CP6's sweep — scope as written in CP6 is the narrow one (M17). CP2's
*rollback* is the hazard (C11).

**5. The rollout residual.** The brief's summary is stronger than the text: the plan does
**not** say "re-measure at CP0"; CP0 re-measures **test counts** and the wide-case skip only,
and §10 says "re-check before editing" of a *line number*. Two carried numbers become
deliverables: §10's one-entry vision declaration is config content written into
`default.yaml`, and CP5's subject assumes the base is one-channel. The first is genuinely
gated — §11's sweep validates `default.yaml`'s names against its resolved width, so a wrong
§10 block fails CP6. The second is not: if the base reverts to eight channels CP5 has no
one-channel subject unless §9's shrink helper is used, and CP5 does not say so. The in-memory
checkpoints (M12's mirror, the `PANEL_MAP_SLOTS` anchor, the grow helper, CP3's on-disk
recordings) are rollout-independent, which is the right shape. See M21.

### Findings

| Sev | Location | Issue | Exit condition | Owner |
|---|---|---|---|---|
| 🔴 C11 | CP2 *Rollback* ("`git checkout` the affected files"); CP0; §9b "this change lands FIRST"; `configs/environment/default.yaml` (` M`, part of a 10-file, 118+/124− uncommitted rollout) | **The rollback reverts another session's uncommitted work, and the commit would sweep it.** `default.yaml` is edited by this plan *and* carries the parallel session's unstaged 8→1 channel change. `git checkout -- configs/environment/default.yaml` discards their edit with no reflog to recover it, and leaves the seven `basic/` files — whose entity `visual_properties: [1.0]` need `V=1` — extending an 8-channel base, so the entire maintained ladder stops loading. In the other direction, `git add configs/environment/default.yaml` stages their hunks under this plan's message; `CLAUDE.md` forbids it and `git add -p` is interactive and unavailable here. The plan addresses neither. This wording predates the rollout landing; the hazard did not. | (1) CP0: `git diff HEAD -- configs/environment/ > /tmp/rollout-bk-$(date +%s).patch` and `cp -a configs/environment /tmp/configs-env-bk-$(date +%s)` before any edit. (2) CP2's rollback for `default.yaml` (and CP3–CP7's, where they say "as CP3"): keep this plan's own edit as a patch as it is made and `git apply -R` it; **never `git checkout`** a file under `configs/environment/`. (3) State how `default.yaml` is committed: after the rollout session commits (recommended — §9b's "lands first" is already moot), or as a filtered patch via `git apply --cached`. User picks. | senior-developer (1, 2); user (3) |
| 🟡 M16 | §7b "`q_learning.yaml` is EXCLUDED — and now by the rule, not by fiat. It sets `using_sensory: false`, so the enabled-sense rule above excludes it" | **`using_sensory` is read by no code.** A quoted grep over `src/`, `scripts/`, `tests/` finds it only in four test-fixture YAML strings; the loader keys enablement on `sensory.olfactory_enabled` / `visual_sensor_enabled`. `q_learning.yaml` never reaches the enabled-sense rule — it fails `load_env_params` on `sensory.visual_sensor_range` (measured). The exclusion that holds is the sweep-roots one the same paragraph already states. A fix justified by a key nothing consults is the pattern this thread keeps finding. | Delete the `using_sensory` sentence. Say: excluded because it is outside the sweep roots and cannot resolve to `EnvParams` at all. | senior-developer |
| 🟡 M17 | §11 row `test_channel_names_match_configs.py` ("Sweep every maintained config under `configs/environment/` — `default.yaml` plus `experiment/basic/`"); CP6 ("sweep every maintained config under `configs/environment/`"); §7b bullet 3 | **The test spec still carries the scope C7 rejected, and never states the enabled-sense rule.** §9b's location-scoped roots (`environment/**`, `verification/**`, `continual/nmn_double_return_stages/`; skip only top-level `continual/`) are correct; the row a developer implements from says the directory boundary. Both sentences were already at `b2804376` — missed by the fourth pass. Also unstated: whether display keys present for a *disabled* sense are ignored or refused. | Rewrite the §11 row and CP6 to cite §9b's roots verbatim; add "a sense's keys are checked only when it resolves enabled — the two parity files must pass with olfaction names alone". State ignored-vs-refused for a disabled sense's keys (recommend *ignored*, since the sense is off and the sweep cannot validate a length for it). Add fixture cell `E9` (vision off) as a CP subject: records with olfaction names only, renders with no vision panel. | senior-developer |
| 🟡 M18 | §9b intro and steps 1–3; §9 "The dim-1 cells must also override the two display keys, or the cell inherits `default.yaml`'s 8-entry list" | **M13's fix reached §A8 but not §9b.** §9b still says the other session "is currently setting `visual_vector_size: 1` across the `basic/` ladder" (it is set once, in `default.yaml`; no `basic/` file sets it), that ladder files "keep inheriting a correct 8-entry list" (1-entry now), that the other session adds keys "in the same edit that sets `visual_vector_size: 1`" (no such edit exists), and step 3 tells the developer to **report and stop** — withdrawn in §A8, live here. Two contradicting instructions in the section titled "time-critical". The dim-1 bullet is harmless if followed (same values) but false. | Rewrite §9b's ordering block to match §A8: reconciliation empty, proceed, the sweep is the proof. Mark the dim-1 override bullet as conditional on the base *not* already being one-channel. | senior-developer |
| 🟡 M19 | §D5b "at **1** map and range 3 the need is `1×7×10 + 0 + 32 = 102` px"; §D4/§D4c "Panel width depends only on the sense" | **The number contradicts the rule one paragraph up, and hides a consequence the plan never states.** Under §D5's `maps = max(slots, drawn)`, a 1-channel legacy needs `max(6,1) = 6` maps = **482 px** (measured), not 102. It still fits 520, so the M12 fix and its conclusion stand. But the same arithmetic at **range 4** gives 602 px against 520 — **the packer refuses**, for configured and legacy recordings alike (measured: `LayoutOverflowError: visual needs 602px … giving it 520px`), where today's live-count sizing renders a 1-channel range-4 world at 122 px. Fixed size caps renderable vision range at 3 under the current band split; the fixture script's `E8` cell (range 4) is exactly a world this change makes unrenderable. It is a refusal, so it is loud — but the user chose fixed size without being told this. | Correct 102 → 482 and say why. Add one sentence to §D4 stating the range cap as a consequence of the fixed-size decision; user confirms they accept it or asks for the need-proportional split they earlier declined. | senior-developer; user (accept) |
| 🟡 M20 | §1 `ChannelDisplay.from_meta(payload=None) → legacy`; §D1 reason 4; §7b per-sense omission | **The legacy signal is now ambiguous.** D1 says legacy = top-level `channel_display` absent. After the enabled-sense rule a *configured* recording legitimately lacks a sense entry, so `from_meta` receives `None` in three unlike cases — pre-change recording, disabled sense, forgotten/hand-edited entry — and hands all three positional names. Harmless for a disabled sense (never drawn: `LayoutContext.observed` gates on the breakdown). For an **enabled** sense on a configured recording it silently ships "Channel 0" — the invented name §1 says the drawing path can never produce. | Build the per-sense displays from the top-level key: absent → legacy for every sense; present → every sense in `ctx.band_senses` must have an entry, else raise naming the sense. One §11 case: configured payload missing `Visual` on a vision-enabled context raises. | senior-developer |
| 🟡 M21 | CP0; CP5; §10 | **The plan does not say "re-measure at CP0".** CP0 re-measures test counts only. Two carried numbers become deliverables: §10's one-entry declaration is config content (gated: the §11 sweep validates it against the resolved width — good), and CP5's subject assumes a one-channel base (ungated: if the rollout reverts, CP5 has no subject and does not say to use §9's shrink helper). | CP0 records `git diff HEAD --stat -- configs/environment/` and the resolved base `(olf, vis, olf_range, vis_range)`; §10's declaration is derived from the resolved base at CP2; CP5 uses the shrink helper if the base is not one-channel at CP0. | senior-developer |
| 🟢 L7 | CP5 "(they do not currently build)"; §D5b "the `E7` cell recorded from today's tree … is exactly one"; §7c | Stale bundle: §9 says `E6sum`/`E6bin` build (true); no `E7` recording exists on disk (only `M*`, `W20`, six `olf1_vis*`) — say "would be". §7c's backstop resolves stage 0 only; `train.py:869` already loads every stage's params, so resolving each stage at start costs nothing extra — optional. | Fix on next revision. | senior-developer |

### Author findings, verified this pass

| # | Claim | Status |
|---|---|---|
| C9 fix | eleven resolve `olf=5 vis=8`; parity pair `visual_sensor_enabled: false`; nine vision-enabled files match the reference table | ✅ raw `Config` → `load_env_params`, no `extends:`: `res=[3,3,3,3,4,4,4,4] anim=[5,7,7] obs=[6]` on all nine; parity pair `vis_on=False`, one animal each (7 / 5) |
| C10 fix | strip + width 8 loads; loader assigns 3/4/5/7/6 and 0/1/2 | ✅ direct and through `build_params` — see question 2 |
| M12 | 8 maps r3 = 634 > 520 refuses; configured 6 slots r3 packs | ✅ 634 refuses; 6 slots r3 = **482** packs (plan and fourth pass both said 487 — harmless); 1-ch legacy r3 = 482, not 102 (M19) |
| M13 | §A8 table complete; §A2 item 3 corrected; E6 cells build | ✅ table lists blur/value_mode; base resolves `vis=1 … vis_range=2` |
| M14 / M15 / L5 / L6 | explicit range-0 cell; location-scoped sweep; line drift; source-grep test | ✅ in §9b/CP3/CP4/§11 (range-0 cell not yet named — fine) |
| §7c | `train.py` holds both `config` and `params` at setup | ✅ `params = load_env_params(config)` at `:777`; video branch `eval_v_flag` at `:2535-2560` |

### Assumptions the plan depends on (this pass)

- ❓ **O11** (carried) — the rollout lands as it stands. C11's exit makes the plan safe either
  way; M21 makes CP5 robust to it.
- ❓ **O12** — the parity fixtures for `olfaction_parity_{neutral,predator}.yaml` are not
  regenerated by adding an inert key (§7b argues from "no hashing"; the gates were not run this
  pass). CP6 runs them, so this is gated.
- ❓ **O13** — no production path records from a config at vision range ≥ 4 today. If one does,
  M19's refusal is a regression on that path, not a hypothetical.

### Cost of being wrong

If C11 ships as written, the first checkpoint that fails after CP2 discards the parallel
session's uncommitted rollout of `default.yaml` — and, if the developer reads "affected files"
broadly, the seven ladder files with it — recoverable only by redoing that session's work from
the untracked `basic_vec8/` copies and memory; or their half-finished rollout goes out under this
plan's commit message. The Moderates each cost a checkpoint that goes green without testing what
it says (M17, M20), a developer halted on a withdrawn instruction (M18), or a "why won't my
range-4 video render" day (M19). No design-level rework remains.

### Passes skipped

Pass 6 (experiment-plan specifics) and pass 7 (empirical-claim soundness) — engineering plan.
Prior-art pass: Known Bugs rows 114, 115, 119, 120, 125, 173 re-read; nothing new walked into.
The range-4 refusal (M19) sits beside row 125 (height twin, "first biting at range 5") and row
173 (the width bug at range 3) and should be recorded by `bug-curator` once the user decides.

*Reviewed by: plan-reviewer*

---

## Sixth pass — re-review at `261513e8` (2026-09-21)

Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run · 🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

Reviewed at the committed SHA only. Measurements were taken on the working tree of 2026-09-21
after `47b1b8c3`; `configs/` is clean (verified), and the base resolves to `(5, 1, 1, 2)` through
the trainer's own loader (verified). Nothing was staged, edited or reverted by this review.

### Verdict, in plain language

**SOUND WITH CONCERNS — nothing found blocks implementation.** This pass was a gate, and the
question it was asked was whether any remaining defect would reach a rendered frame or destroy
work. None does. The newest mechanism — an oversized sensor range shrinks its maps *inside* the
fixed panel rather than spilling out — was re-derived with the real packer and the author's
table is exactly right: at six slots a 520 px grant leaves 15.3 px map squares at vision range
2, 10.9 px at range 3, and 8.5 px at range 4, which is under the 10 px floor, so range 4 refuses
with the quoted message. The in-memory rebuild of the wide-sense test is genuinely in memory
(the existing `_ctx` helper builds a layout context from literals with no file at all), the
legacy signal is keyed off the top-level key as asked, every checkpoint has a subject that
exists on disk or can be built, and the trap cases (a vision-off recording, a 12-channel
synthetic world) both resolve through the fixture script's own `build_params`.

Three Moderates remain, and for each a developer can implement correctly *despite* it: one is
a coordination hazard on a test file another session has edited but not committed, one is an
ambiguity about *when* a sense's display is built that the plan's own E9 checkpoint would
catch, and one is a wording that invites a second copy of the packer's arithmetic. Two Lows
are wording. A seventh cycle is not justified by anything here; the fixes are sentences and can
ride with the implementation.

### The six questions this pass was asked

**1. Does anything still block implementation?** No. See findings — each says "blocks: no" and
why.

**2. §D4d's containment table, re-derived.** Holds exactly. Real packer, base `(5,1,1,2)` with
`visual_vector_size=8` (six maps) and `visual_range` ∈ {2,3,4}: `_span` = **362 / 482 / 602** px;
range 2 and 3 are granted **520** px (`band_w = CANVAS_W − OUTER − cx`, two children), inner
width 488, six-slot pitch 76.3 px, map squares **15.27 / 10.90** px; range 4 is refused with
`visual needs 602px of width in the band; 2 children share 1056px, giving it 520px`. The
1-channel column also holds (live `_span` 82 / 102 / 122 px today, so today's sizing does
render a 1-channel range-4 world, and 8.48 px contained at range 4 after). The refusal is issued
by the **layout registry's** band check, not by the painter's `cs < 10` the section names — the
two floors are the same constant and the band-span equality test is what keeps them agreeing,
so the verdict is identical (L8, wording). Through the real cells: `E7` (both senses at range 3)
packs at 1 and 8 channels; `E8` (range 4) packs at 1 channel today and refuses at 8 — the
boundary is where the plan says it is.

**3. Can every checkpoint fail against `(5, 1, 1, 2)`?** Yes. CP1's source-grep case fails today
(`painters.py:707,709`). CP2b(b)'s subject carries `visual_vector_size: 8` and none of the four
keys (verified). CP3's subjects exist with `run_meta.pkl` (`olf1_vis2_spanfix/recordings/77`,
`olf1_vis3_spanfix/recordings/71`); (a) needs 8 maps × 5 cells = 474 px ≤ 520 and draws, (b)
needs 634 > 520 and refuses. CP4's before/after `layout_signature` is identical by construction
(live 8-channel = 6 maps = 362 px; slots = 6 = 362 px). CP5's one map is 15.3 px either way, so
"not enlarged" is a real assertion. CP5b(a)'s 12-channel world loads through the loader with
explicit 12-wide lists (`Visual = 156` dims). CP6's `E9` resolves with `Visual` absent from the
breakdown and packs as a single 1056 px band child.

**4. M10's rebuilt cases.** In memory, yes: `test_dashboard_band_span.py:76` `_ctx` constructs
`LayoutContext` from literals — no config read. The §11 row's "`default.yaml` plus range and
width overrides" adds one benign dependency (the maintained base; its absence is a loader error,
never a skip); all three cases can be built with `_ctx` alone and I would. No skip path: `:266`
is the only `pytest.skip` in the file at HEAD and the row deletes it. Note the working-tree
collision in M22 — the same function has already been rewritten, uncommitted, by another session.

**5. M20's legacy keying.** Enabled sense with no entry raises: yes, `key_present and
meta_entry is None → KeyError`. Disabled sense with no entry does not raise: **only if the
display is built lazily** — the sketch has no enabled input, so an eager per-sense build in
`LayoutContext.from_params` would raise on E9. The registry sizes only present panels
(`panels.py:629` `present_panels` → `:708` band `min_size`) and `episode.py:455-459` draws only
present band keys, so lazy is the natural wiring, but the plan should say it (M23).

**6. The source-grep residual.** `"row[:"` catches slice literals only (`:707`, `:709` today) and
would miss `row[0]`, `row[1:3]`, `vec[:, :3]`. A regex `\b(row|vec)\[[^\]]*\d` catches those
three and nothing legitimate (`row[ch]`, `row[list(channels)]` have no digit). It is still not
airtight against a renamed variable; the structural guarantee stays where the plan put it —
`map_plan` carries the channels and CP6's shifted-group frame is looked at (L9).

### Findings

| Sev | Location | Issue | Exit condition | Blocks? | Owner |
|---|---|---|---|---|---|
| 🟡 M22 | §11 band-span row; CP0; working tree ` M tests/env/test_dashboard_band_span.py` (+63/−), ` M tests/env/test_dashboard_layout.py` (+67/−), `?? tests/env/fixtures/dashboard_band_vis3.yaml` | **Another session has already rewritten the same wide-sense test, uncommitted, the other way.** Their version asserts instead of skipping (good) but repoints the two cases at **files on disk** (`basic/05-campfire_thermal_10x10.yaml` and a new fixture YAML) — the dependency M10 forbids — and today's diary row says the case is "NOT being patched standalone". The fixture's own comment carries pre-plan arithmetic ("declares 102 px"). CP0 checks only `configs/` for foreign hunks; this is C11's shape on a different file, at staging rather than rollback. | CP0 also records `git status --short tests/env/`; if the band-span test is dirty, coordinate before editing it exactly as C11 required for `default.yaml`. State the resolution: §11's in-memory version **supersedes** the file-based one, and `dashboard_band_vis3.yaml` is removed by whoever lands second unless something else reads it. The layout-test edit is the other session's fix for §A6's three failures — CP0's "re-measure, inherit no number" already absorbs it. | **No.** No rollback step names the file; the `CLAUDE.md` staging rule ("confirm every hunk is yours") already governs the commit. | senior-developer; the owning session |
| 🟡 M23 | §1 `ChannelDisplay.from_meta(sense, n_channels, meta_entry, *, key_present)`; §2 "build `ChannelDisplay` per sense" | **The sketch raises for any missing entry once the key is present, and has no enabled input.** Built eagerly for both senses, a configured vision-off recording (`E9`) raises `KeyError` at context construction — the false positive the docstring says it avoids. Built lazily — only for senses in the breakdown — it is correct, and that is how the registry and the band loop already work. | One sentence in §2: a sense's display is built only when `ctx.observed(sense)`; an unobserved sense never has one. Add the mirror case to §11 beside M20's: configured payload lacking `Visual` on a vision-**off** context builds and renders without raising. | **No.** CP6's `E9` render fails on an eager build, in seconds. | senior-developer |
| 🟡 M24 | §D5b "The legacy path checks **before packing** and raises a message that …" | **The grant is known only inside `pack()`.** A pre-pack check must re-derive `CANVAS_W − OUTER − cx` and the two-child split — a second copy of the packer's arithmetic in another module, which is the `4b6f7196` shape the plan cites as its reason to exist. | Implement as catch-and-reraise around `pack()` on the legacy path (or expose the band grant from `layout` as the one function both call). CP3(b)'s check is unchanged. | **No.** CP3(b) and §11's 482/634 cases hold either way; this chooses between two implementations. | senior-developer → developer |
| 🟢 L8 | §D4d "under `painters.py`'s `if cs < 10: raise`" + the quoted `visual needs 602px …` message; §9 "Shrinking (V < 8)" / "Growing to V = 8" | The message quoted is the registry's, which refuses first; both floors are 10 px. §9's branches are named by direction, but CP5b's 12-channel cell needs the explicit-list branch at V > 8 (verified it loads). | Say "the registry refuses first, on the same floor"; rename the branches "V ≠ 8 → explicit lists / V = 8 → strip". | No | senior-developer |
| 🟢 L9 | §11 source-invariant row `"row[:"` | Catches slice literals only. | Use `\b(row|vec)\[[^\]]*\d`; keep the structural guarantee in `map_plan` + CP6. | No | senior-developer |

### Author findings, verified this pass

| # | Claim | Status |
|---|---|---|
| C11 | rollout committed as `47b1b8c3`; `configs/` clean | ✅ `git status --short configs/` empty; commit stat shows `default.yaml`, seven `basic/`, two deletions, `archive/basic_vec8/` |
| M19 / §D4d | 362 / 482 / 602 px; 15.3 / 10.9 / 8.5 px; range 4 refuses | ✅ exactly, real packer (question 2) |
| §D5b 482 px | 1-channel legacy r3 sized to six slots | ✅ 482 ≤ 520 packs |
| M10 | wide cases skipping right now, `16 passed, 2 skipped` at `:266` | ✅ at HEAD; the working tree already carries a foreign rewrite (M22) |
| M16 | `q_learning.yaml` outside sweep roots, fails on `visual_sensor_range` | ✅ carried from fifth pass; unchanged |
| M20 | legacy keyed on top-level key | ✅ as sketched; lazy build needed (M23) |
| CP0 base | `(5, 1, 1, 2)` | ✅ `olfactory_channels=5 visual_vector_size=1 olfactory_range=1 visual_range=2` |
| E9 / E7 / E8 | vision-off resolves; range-3 packs; range-4 refuses at 8 ch | ✅ through `build_params` |

### Assumptions the plan depends on (this pass)

- ❓ **O12** (carried) — the parity fixtures are unaffected by an inert key. Gated by CP6.
- ❓ **O13** (carried) — no production path records at vision range ≥ 4; `E8` is a fixture cell.
- ❓ **O14** — the other session's band-span / layout test edits either land or are abandoned
  before CP1; whichever, CP0 records the working-tree state it actually finds (M22).

### Cost of being wrong

If the three Moderates ship as written: M22 costs at worst another session's ~130-line test edit
swept under this plan's commit or a merge on one function — no data, but the `CLAUDE.md` rule
exists because of exactly this; M23 costs one CP6 iteration, caught in seconds; M24 leaves a
second copy of the packer's arithmetic that can drift, confined to *when* a legacy recording's
refusal message is issued. Nothing reaches a rendered frame of a configured recording, and
nothing requires a rerun of anything expensive.

### Passes skipped

Pass 6 (experiment-plan specifics) and pass 7 (empirical-claim soundness) — engineering plan.
Prior-art: Known Bugs rows 125 (height twin) and 173 (width fix) re-read; no new collision. The
silent-skip of the band-span guard is in today's diary but not the registry — `bug-curator`
should record it once the test lands, whichever version wins.

*Reviewed by: plan-reviewer*
