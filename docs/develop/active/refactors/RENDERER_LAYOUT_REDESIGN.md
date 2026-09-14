---
title: "Episode-video renderer redesign: panels that cannot overlap, a faster frame, and a step-scrubbing viewer"
topic: refactors
status: active
created: 2026-09-14
last_updated: 2026-09-14
supersedes: UI_REDESIGN_PROPOSAL.md
---

# Episode-video renderer redesign: panels that cannot overlap, a faster frame, and a step-scrubbing viewer

> **Status**: PLANNED. Revised three times after `plan-reviewer` (first and second pass NOT READY; third pass SOUND WITH CONCERNS, applied in Revision 3). Plan only; awaiting re-review, then user approval. No code written.
> **Opened**: 2026-09-14
> **Related**: [[UI_REDESIGN_PROPOSAL]] (the April plan this one replaces) · [[12_renderer]] (renderer reference doc) · [thermal IMPLEMENTATION_PLAN](../thermal/IMPLEMENTATION_PLAN.md) (§"Rendering: what the rewrite's state turned out to be") · [[BODY_TEMPERATURE_OBSERVATION]] (thermal; **untracked work-in-progress in another session, read as unstable input only**) · [[ASYNC_CHECKPOINT_VIDEO_RENDER]] · [[SAVED_RUN_CONFIG_COMPAT]] · review: [`docs/reviews/plan_renderer_layout_redesign.md`](../../../reviews/plan_renderer_layout_redesign.md) · evidence frames + measuring script: [`renderer_layout_redesign/`](renderer_layout_redesign/) · web research note `tmp/20260914_renderer_layout_web_research.md`

---

## Context

Every evaluation episode this project records can be turned into a video. Each frame is a dashboard. The agent's internal body readings sit on the left: satiation, nutrition, injury, interoceptive nociception (the internal damage signal) and body temperature. A zoomed map of the world around the agent fills the middle. The agent's outside-world senses sit on the right: smell, extero nociception (the contact-damage signal), heat, collision and vision. These videos are how people check what an agent actually did, and they are uploaded to the training dashboard (WandB) during training.

**The problem.** Frames rendered today from the new temperature world draw text on top of text:
- the extero-nociception reading "OBS: 0.00" is printed over the title of the heat-sense panel;
- a floating "REAL: --" sits on a panel title;
- the minimap label runs into the run-information box;
- about a quarter of the frame is empty margin.

An April attempt at a cleaner layout was half-built as a second renderer. That renderer has no callers and has its own collisions, and it silently drops two panels. There is also a subtler defect in the renderer that runs today: it captions some values as what the agent **observes** even in worlds where the agent cannot observe them. The cause is structural. Matplotlib's automatic layout only makes room for axis ticks, labels, titles and legends, and cannot see the text the dashboard draws inside its cards. Every frame also builds a new figure from scratch.

**What stays untouched during development (user constraint, 2026-09-14).** The current training and evaluation video pipeline keeps running exactly as it does today while the new renderer is built. No file on that pipeline is edited: the current renderer, the recording writer, the offline render script, the in-training render dispatch, the two evaluation modules, the sensor adapter and the benchmark script. The dormant April renderer file is also left alone, because another session is editing it right now. No config key or default changes either, including the icon mapping that production videos read. The new renderer lives in new files, is run through its own new script, and writes its videos to a separate folder, so it can never overwrite a production video. **Moving any training or evaluation video over to the new renderer is a later, separate decision by the user**, taken only at the retirement gate at the end of this plan.

**What this plan proposes.** A rebuilt renderer that runs alongside the current one, which stays the production default until the new one passes checks:
- Each sense declares what it shows and the space it needs. A sense shows up as "observed" only if it is actually part of the agent's observation.
- The layout is computed once per episode and each panel draws only inside its own box. If an episode cannot fit, the renderer refuses to start it rather than draw collisions.
- The figure is built once per episode, and each step only updates the numbers.
- A local interactive viewer lets you scrub through steps of the same recordings.

The recommended toolkit keeps Matplotlib for drawing but replaces its layout (§D2). That choice is a genuinely close call against a browser-based option now that Chrome is known to exist on lab nodes, and the user must make it along with the open questions at the end.

---

## Revision 2026-09-14 (after plan-reviewer)

`plan-reviewer` returned **NOT READY**, with 2 Critical, 10 Moderate and 3 Low findings; the full text is appended at the end of this doc and in `docs/reviews/plan_renderer_layout_redesign.md`. How each finding was handled:

| # | Finding (short) | Handling |
|---|---|---|
| 🔴1 | "pain" used as the signal's name | Removed from all prose and labels: "interoceptive nociception" / "extero nociception"; blueprint row label `INOC`. New checkpoint **CP2.4** greps the painter package and every rendered frame's text for the whole word `pain` (case-insensitive, word-boundary so "painter" does not match) and expects zero hits. |
| 🔴2 | Vitals presence rule undecided; V1 captions unobserved state as OBS | §D1.1 rewritten. An observed row (`vital_row`, `temp_row`) is present **iff** its name is in `get_observation_breakdown(params)`. A true state value the agent does not observe may be shown only through a separate `hidden_state` kind, captioned "not observed", with no OBS/REAL text and no tick (open question Q10: show or omit). New frame test **CP2.5** on the campfire world. V1's mis-caption (the `sensor_map.get('Nutrition'/'Injury', {'intensity': state_value})` fallback in `render_jax_state`) goes to `bug-curator` after approval. |
| 🟡3 | Audit exemptions declared by the painter under test | §D5.2 step 1 rewritten. Foreground/background is decided by artist **type and geometry**; painter tags are used only for naming in reports. Card borders are their own foreground outline, so text on a border is **forbidden**. New mutation **M-C** (retag a bar fill as background); **D3** added as a V1 positive control. |
| 🟡4 | Presence rule has no positive control | CP0.3 extended: the audit on the dormant renderer's campfire frame must report Interoceptive Nociception absent, plus Location/Proprioception if they are in that world's observation. |
| 🟡5 | V1 baseline too narrow; unclear what is hashed; training path unguarded | §D5.4 / CP0.1 cover M1, M2, M4 and M7. **Raw frames** are hashed by monkeypatching `save_jax_video`, and in two separate processes. *Superseded by the user constraint below:* no `--renderer` flag exists, so the async-test assertion is dropped. The training path is instead guarded by **CP-G**: content hashes of all eight frozen files, including the three `src/` callers, plus V1 raw-frame hashes, checked after every phase. |
| 🟡6 | Chrome premise false | Corrected: reviewer verified `/usr/bin/google-chrome` on nodes 101, 106 and 114. D2 re-weighed; §D2.1 states plainly what option C's viewer gives that A's does not; Q1 rewritten. |
| 🟡7 | 200 ms gate has no hardware; numbers from untracked script | The gate is now a **same-machine, same-cell ratio** measured in a pool worker on a lab node. Today's container numbers are cited as context with their script (`renderer_layout_redesign/render_current_frames.py`, i9-7900X container). Q9 rewritten. |
| 🟡8 | REAL availability from per-episode data | §D4.2 rewritten. **Availability comes from params** (noise on and the modality's noise mode not `None`) through the recording-flag helper, so it is constant per run. Data only picks the caption. New check: layout signature identical across all episodes of one concatenated video. |
| 🟡9 | `fit_text` ellipsises numbers in production | Numeric kinds never ellipsise: shrink to 8 pt, then raise. Only free header text may ellipsise, and any ellipsis is logged. |
| 🟡10 | `DNG` legacy label | Blueprint uses `HPR`. **The `sensor.py` rename is withdrawn** (user constraint below: `build_sensory_viz` labels feed V1 frames, so renaming would change production videos). V2 maps its own labels inside `src/environment/dashboard/` (a label table keyed by channel index that overrides the adapter's `labels`). The `sensor.py` rename moves to the retirement gate. Abbreviation is Q11. |
| – | **User constraint 2026-09-14: V1 pipeline frozen during development** | Folded throughout.<br>• **No edits** to `src/environment/renderer.py`, `scripts/eval/render_recordings.py`, `src/utils/async_render.py`, `src/utils/evaluation_core.py`, `src/algorithms/dreamer_srl/eval.py`, `src/utils/eval_recording.py`, `src/environment/sensor.py`, `scripts/eval/benchmark_render.py` until a separately approved retirement step.<br>• **No `--renderer` flag.** A new entry point `scripts/eval/render_recordings_v2.py` writes to `videos_v2/` and also carries the benchmark mode.<br>• **V2 imports V1 helpers read-only**; any helper needing change is copied into the package.<br>• The earlier async-dispatch test edit is dropped as moot (nothing on that path changes).<br>• **Checkable guarantee:** new guard script `scripts/eval/v1_path_guard.py` records a content-hash baseline of those eight files, plus V1 raw-frame hashes (M1, M2, M4, M7), and every phase must pass it (**CP-G**).<br>• Context and the retirement gate state that moving any video to V2 is a later user decision, with no config key or default change before then. |
| 🟡11 | Campfire obstacle has no icon | §D1.4 specifies a deterministic per-obstacle-name glyph fallback, always available because archived `icon_config` pickles lack new keys. Adding a `campfire.png` asset is Q12. New frame test **CP2.6**: every in-view obstacle has non-empty foreground ink in its cell. |
| 🟡12 | `INDEX.md` commit hazard | Noted for whoever commits: pathspec commit, check hunks; the other session's staged hunk is not ours. No plan change. |
| 🟢13 | Two meanings of "V2" | Q2 keeps the package name. `12_renderer.md` gets one disambiguating sentence (File Changes). |
| 🟢14 | Evidence folder uncited | A2 now cites `renderer_layout_redesign/figures/{v1,v2}_thermal.png` and the script. The default-world frames were rendered to session scratch only and are **not** in the folder. |
| 🟢15 | Audit cost | Audit tests carry the registered `integration` marker; §D5.2 reuses one full render plus N element-hidden renders. |

Also new: another session has **uncommitted edits** to `renderer.py`, `renderer_v2.py`, `sensor.py` and `evaluation_core.py` (seen in `git status`) for the body-temperature observation work. Line numbers in those files are therefore unstable, so this revision cites functions and strings.

The V1-path guard does **not** compare against HEAD. It compares against a recorded baseline of each file's content hash, so that session's work is detected and attributed rather than blamed on this plan (§D5.4).

---

## Revision 2 2026-09-14 (after plan-reviewer second pass)

The second pass confirmed findings #1–#15 resolved in the body and returned **NOT READY** on how the revision treated the other session's live work. Its signed feedback is appended at the end of this doc and in `docs/reviews/plan_renderer_layout_redesign.md`.

| # | Finding (short) | Handling |
|---|---|---|
| 🔴16 | Phase 1 would `git rm` (or shadow) `src/environment/renderer_v2.py`, which carries another session's uncommitted edits | The package is renamed to **`src/environment/dashboard/`** (Q2 is now a choice among descriptive names only). `renderer_v2.py` joins the frozen set: **not edited, not deleted, not shadowed**. No module or package named `renderer_v2` is created, and the guard hashes the file. Its deletion moves to the retirement gate, after the thermal session is told and its work has landed. The one-frame wrapper is renamed `render_dashboard_frame`. |
| 🔴17 | Guard attribution rule can false-pass and fail unresolvably | Replaced with the reviewer's **three-state mechanical rule** (§D5.4). **PASS** iff the working-tree sha equals the baseline. **ATTRIBUTED** iff the working-tree sha equals `git rev-parse HEAD:<path>` and every commit touching the path since plan start carries a `Claude-Session:` trailer that is not one of the plan's recorded sessions. **UNATTRIBUTABLE** otherwise, including a missing trailer; it is named in the report, cleared only by the user, and never re-baselined. Fixture-recording hashes added so a regenerated fixture is reported as such. `tests/env/test_v1_path_guard.py` exercises all three states in a throwaway git repo. |
| 🟡18 | Phase 0 ordering circular | Split: `record-files` is the first action of Phase 0; `record-frames` runs right after the fixture generator lands and before any renderer code (CP0.1a / CP0.1b). |
| 🟡19 | Baseline unversioned | Baseline JSON and `frozen_files_at_baseline.diff` (`git diff <plan-start> -- <frozen files>` at record time) are written to `docs/develop/active/refactors/renderer_layout_redesign/v1_guard/` and committed, not under gitignored `results/`. |
| 🟡20 | Body Temperature has already landed in the working tree; helper signatures moving | Registry names **`Body Temperature`** now (viz key `value`). In M4 as the tree stands, the temperature row takes the **observed** path. The fixture generator writes each cell's config-file sha256 into `run_meta` extras, and CP0.2 prints it. §D1.3 lists every imported V1 signature; `tests/env/test_dashboard_v1_imports.py` pins them. |
| 🟡21 | Q12 asset contradicts the freeze | Asset **deferred to the retirement gate**; the new renderer uses the glyph until then. Q12 rewritten as defer (proposed) or an explicit user exception. |
| 🟡22 | Scripts map incomplete | File Changes now list map rows for all four new scripts plus `episode_viewer.html` (a "not a script" row, precedent `pipeline_layout.html`). §1c test-suite rows cover every test that imports a script, with the `scripts/eval/` root-depth note. The "two" vs three count is fixed. |
| 🟢23 | `slow` marker unregistered | The registered `integration` marker is used. |
| 🟢24 | Frame-capture harness details | §D5.4: call `render_recordings._worker_init(run_meta_path)` first (the actual name in the file; the review wrote `_init_worker`). Patch `src.environment.renderer.save_jax_video`. Pass a scratch output path under a temp dir. |
| 🟢25 | CP2.4 comment exclusion | CP2.4 now requires zero hits, comments included. |

---

## Revision 3 2026-09-14 (after plan-reviewer third pass: SOUND WITH CONCERNS)

| # | Finding (short) | Handling |
|---|---|---|
| 🟡26 | The thermal session's normal uncommitted delta would block every phase boundary | New user-run `v1_path_guard.py accept <path> <sha256>` writes a `user_accepted` entry into `baseline.json`. `check` reports that **exact** content as **ACCEPTED**, and any other content of the file is flagged again. This is not a re-baseline (§D5.4, CP-G). |
| 🟡27 | Icon mapping not guarded | `configs/visualization/default.yaml` joins the hashed frozen set. |
| 🟡28 | "Not observed" temperature row never exercised | New matrix cell **M4b**: an in-memory override of M4 with body temperature not observed. It does not depend on any untracked config file. |
| 🟡29 | A mixed commit could be ATTRIBUTED by trailer | A commit touching a frozen file **and** any plan-owned path is UNATTRIBUTABLE regardless of trailer; guard test case added. |
| 🟢30 | gzip embeds mtime | Fixture hashes are taken over the **decompressed** `.rec.gz` payload. |
| 🟢31 | M5 config uses `extends:` | `config_sha256` hashes the resolved config, and `config_chain_sha256` hashes every file in the `extends` chain. |
| 🟢32 | Diff file could be mistaken for a patch | `frozen_files_at_baseline.diff` starts with a header naming it as another session's work-in-progress snapshot, not to be applied. |

---

## Analysis

### A1. What runs today (verified 2026-09-14; line numbers as of HEAD `75757dfc`, working tree dirty, see revision note)

| Piece | Where | Notes |
|---|---|---|
| Live renderer | `src/environment/renderer.py` `render_jax_state(state, params, …, thermal_clim=None, debug_thermal_cells=False)` | Flat 1×3 GridSpec, then hand-placed axes-fraction coordinates with a y-cursor, with a 5-bar special case for vitals and a `_squeeze` budget for right pods on thermal configs only. `plt.close('all')` + a new `plt.figure(figsize=(14, 10))` **every call**. `_FIG_CACHE` is assigned but never read. Draws Satiation/Nutrition/Injury **always**, falling back to `{'intensity': state_value}` when the modality is not in `sensory_data`, and captions that value `OBS` (review finding 2). Iconless entities fall back to a grey square marker (`m_map.get(icon_key, ('s', 'grey'))`). Output 1400×1000, which `save_jax_video` (imageio, macro-block 16) writes as 1408×1008. |
| Dormant renderer | `src/environment/renderer_v2.py` `render_jax_state_v2` | `subfigures` + `subplot_mosaic` + `layout='constrained'`. **Zero call sites.** Round 1 of the April plan; Round 2 was never built. |
| Stale copy | `src/environment/grid_world.py` (`render_jax_state` at `:344`) | Near-verbatim old copy of `renderer.py`; nothing imports it. |
| Viz adapter | `src/environment/sensor.py` `build_sensory_viz(obs, state, params, true_obs)` | Walks `get_observation_breakdown(params)`, emits one dict per modality, and ends in `else: raise ValueError`. Olfaction is `type 'visual_grid'` when `params.olfactory_grid_range > 0`. Emits `Proprioception` (`type 'radial'`), which **V1 never draws**. Visual labels `['GRS','SND','PLN','FOD','DNG','PRD','RCK','NEU']`, where `DNG` is legacy "danger" vocabulary. |
| Recorder | `src/utils/eval_recording.py` `EpisodeRecorder`, `_snapshot_state`, `write_run_meta` | Snapshot carries `thermal_field`/`body_temp` only when the state has them; `run_meta.pkl` pickles `EnvParams` and `icon_config`. |
| True observations | `src/utils/evaluation_core.py` `record_true_obs = config.get_mandatory('testing.record_true_observations') and (record_stats or (render_video and params.perceptual_noise_enabled))` | A noise-on run can have `true_obs = None` when the key is false. |
| Offline render | `scripts/eval/render_recordings.py` | Pool, one task per episode; pins `thermal_clim` once from snapshot 0; per step `build_sensory_viz` → `render_jax_state`; `save_jax_video`. |
| In-training dispatch | `src/utils/async_render.py` `dispatch_render` | `Popen`s `render_recordings.py --concat --skip-existing --cleanup-per-episode --fps N [--workers N]`, CPU-only; the parent uploads to WandB. Blocking fallbacks in `evaluation_core.py` and `dreamer_srl/eval.py`. `tests/training/test_async_render_dispatch.py` stubs the script and does not assert the command list. |
| Other V1 callers | `scripts/media/record_env_demo.py`, `scripts/dreamer/visualize_dream.py`, `scripts/eval/benchmark_render.py` | Single-frame, live-state callers. |
| Params used for availability | `src/environment/state.py` `EnvParams`: `perceptual_noise_enabled`, `noise_modality_order` (tuple of names), `noise_modes` (0 None / 1 Constant / 2 State-dependent), `obstacle_names` | Archived pickles may lack newer fields (A3). |
| Existing tests | `tests/env/test_thermal_rendering.py` (16, V1), `tests/algorithms/dreamer_srl/test_eval_recording.py` | Thermal tests compare frames within one process only. |

### A2. Observed defects

Evidence: `docs/develop/active/refactors/renderer_layout_redesign/figures/v1_thermal.png` and `v2_thermal.png`, produced by `renderer_layout_redesign/render_current_frames.py` (campfire world, `PRNGKey(3)`, fixed actions RIGHT, DOWN, RIGHT, DOWN, REST). The default-world frames (D5) were rendered by the same script into session scratch and are **not** in the folder; CP0.3 re-renders them.

| # | Renderer | Defect | Class |
|---|---|---|---|
| D1 | V1 | Extero-nociception readout "OBS: 0.00" overprints the THERMOCEPTION pod title | text-on-text |
| D2 | V1 | "REAL: --" floats over the EXTERO NOCICEPTION pod title | text-on-text |
| D3 | V1 | "MINIMAP" label overlaps the Run Context box border | text-on-border |
| D4 | V1 | ~15% dead whitespace top and bottom | space allocation |
| D5 | V1 (default) | Vitals rows: one row's "OBS: 0.95" collides with the next row's "REAL: 0.95" | text-on-text |
| D6 | dormant V2 | Collision title overprints its C U R D L labels | text-on-text |
| D7 | dormant V2 | Minimap tiny (~125 px) | space allocation |
| D8 | dormant V2 | Interoceptive-nociception and LOC panels missing | silent panel drop |
| D9 | dormant V2 | Vital cards mostly empty; visual feature labels tiny/clipped | space / clipping |
| D10 | V1 | Nutrition/Injury drawn from true state and captioned `OBS` in worlds whose observation lacks them (campfire) | false claim of sensory access |
| D11 | V1 | Campfire obstacle drawn as a grey square (no icon) | missing entity rendering |
| D12 | V1 | `Proprioception` emitted by the viz adapter, never drawn | silent panel drop |

**Root causes.**
- **D1–D7, D9.** No step gives each panel a box sized from its needs and keeps it inside. Constrained layout ignores in-card `ax.text`.
- **D8, D12.** A hard-coded panel list that skips unknown names.
- **D10.** Presence and caption come from the renderer's own assumptions ("always drawn"), not from what the agent observes.
- **D11.** No specified fallback for iconless entities.

### A3. Backward-compatibility facts (verified 2026-09-14)

- A **pre-thermal recording from a trained policy loads at current code**: `results/eval/noPredator_chasingRabbit/models/9520028/recordings/9520028/`. Its params unpickle to `EnvParams` with `hasattr(params, 'thermal_enabled') == False`. Its 501 snapshots lack `thermal_field`/`body_temp`, and `true_obs` is present.
- More trained-policy recordings exist under `results/JAX_RecurrentPPO/*/recordings/` (April–May 2026). They include interoceptive-nociception worlds with and without perceptual noise; none of these have been loaded yet (CP0.2).
- `thermal_clim` must be fixed per episode (thermal plan).
- The untracked body-temperature-observation doc proposes an observed body-temperature value. It is not committed, so this plan does not build against it. The temperature row's presence rule (§D1.1) already handles "observed or not".

### A4. Why this is a redesign and not a tuning pass

Most defects share one failure: text placed by coordinates that nothing checks. D10 shares a second: the renderer decides what the agent perceives. A guarantee needs:
- a layout step that knows every panel's minimum content size;
- painters that cannot draw outside their box;
- presence derived from the observation breakdown;
- a test whose ground truth is the **rendered pixels** and the **breakdown**, never the layout's own boxes or the painter's own tags.

---

## Implementation Plan

### D1. Architecture (stack-neutral part)

```
 .rec.gz + run_meta.pkl
        │
        ▼
 FrameInputs (per step)      ◄── adapter: snapshot → attribute object, build_sensory_viz(obs, s, params, true_obs)
        │
        ▼
 PANEL REGISTRY  ── present(ctx) / min_size(ctx) / extract(inputs) → PanelValues
        │                    │
        │ once per episode   │ every step
        ▼                    ▼
 LAYOUT (column packer)   PAINTERS (one per visual *kind*, not per modality)
   → dict[panel_key → Box]   draw PanelValues strictly inside Box; text via fit_text
        │                    │
        └────► EpisodeRenderer: build figure + artists ONCE, update artists per step ──► RGB frame
                                                         │                         │
                                                  save_jax_video (MP4)     episode viewer (PNG over HTTP)
```

#### D1.1 Panel registry

```python
@dataclass(frozen=True)
class PanelSpec:
    key: str
    group: str                   # 'header' | 'vitals' | 'world' | 'arena' | 'extero'
    order: int
    kind: str                    # 'vital_row' | 'temp_row' | 'hidden_state' | 'intensity' | 'spectrum'
                                 #   | 'dir_grid' | 'cross_bars' | 'thermal_diamond' | 'text_row'
                                 #   | 'minimap' | 'arena' | 'action_badge' | 'header'
    breakdown_names: tuple[str, ...]      # names in get_observation_breakdown() this panel owns
    present: Callable[[RenderContext], bool]      # evaluated ONCE per episode
    min_size: Callable[[RenderContext, FontMetrics], Size]
    extract: Callable[[FrameInputs, RenderContext], PanelValues]
```

`RenderContext` is built once per episode. It holds params, icon config, snapshot 0, `thermal_clim`, `real_available` (§D4.2), and the canvas size.

**The observed-vs-hidden rule** (review finding 2):
- **Observed rows.** An observed row (`vital_row`, `temp_row` with an observed value, `intensity`, …) is present **iff** one of its `breakdown_names` is in `get_observation_breakdown(params)`. Only observed rows may print `OBS` / `REAL` text or a REAL tick.
- **Hidden rows.** A `hidden_state` row shows a true state value the agent does **not** observe. Its caption is `<LABEL>  <value>  not observed` in muted text, with a plain bar and no OBS/REAL text or tick. It is present iff the state field exists in the snapshot **and** the corresponding modality is absent from the breakdown **and** Q10 is answered "show". If Q10 is "omit", `hidden_state` rows are never present.
- **Body temperature.** The temperature gauge is an observed `temp_row` iff **`Body Temperature`** is in the breakdown. In that case its OBS value is the viz entry's `value` key, its REAL value is the snapshot's `body_temp`, and REAL follows §D4.2. Otherwise it is `hidden_state`-captioned ("not observed"), keeping its die-threshold and setpoint marks. As the working tree stands on 2026-09-14, the other session's uncommitted `build_sensory_viz` emits `Body Temperature` (keyed `value`), and the campfire config sets `body_temp_observable: true`. So M4 takes the observed path; CP0.2 confirms which path each cell takes.

| key | group | kind | owns breakdown name(s) | present when | min size driver |
|---|---|---|---|---|---|
| header | header | header | – | always | one text line |
| satiation / nutrition / injury | vitals | vital_row | `Satiation` / `Nutrition` / `Injury` | name in breakdown | label + OBS (+REAL) + bar ≥ 120 px |
| satiation_hidden / nutrition_hidden / injury_hidden | vitals | hidden_state | – | state field exists, name **not** in breakdown, Q10 = show | label + value + "not observed" + bar |
| intero_nociception | vitals | vital_row | `Interoceptive Nociception` | name in breakdown | as vital_row |
| body_temp | vitals | temp_row / hidden_state | `Body Temperature` (viz key `value`) | `body_temp` in snapshot; observed iff `Body Temperature` in breakdown, else hidden | label + value + threshold/setpoint marks |
| minimap | world | minimap | – | always | ≥ 2 px/world cell, ≥ 180 px side |
| location | world | text_row | `Location` | name in breakdown | one text line |
| arena | arena | arena | – | always | square, ≥ 48 px/view cell; + scale strip when thermal on |
| action_badge | arena | action_badge | – | action recorded | pill text in arena title strip |
| olfactory | extero | spectrum / dir_grid | `Olfaction` | name in breakdown; kind by `olfactory_grid_range > 0` | 5 labelled bars / `(2r²+2r+1)` cells × 5 |
| extero_nociception | extero | intensity | `Extero Nociception` | name in breakdown | text row + bar |
| thermoception | extero | thermal_diamond | `Thermoception` | name in breakdown | `2r²+2r+1` numeric cells |
| collision | extero | cross_bars (r=1) / dir_grid | `Collision` | name in breakdown | 8 pt legend above bars |
| visual | extero | dir_grid | `Visual` | name in breakdown | cells × `visual_vector_size`, 8 pt legend |
| proprioception | extero | Q5 | `Proprioception` | name in breakdown | Q5 |

**Completeness rule.** At episode setup, every breakdown name must be owned by exactly one present entry, or be on an explicit "recorded, not displayed" list (only if Q5 chooses that). Otherwise setup raises `ValueError` naming the orphan. A future modality that reuses a kind is a registry entry only. A new kind adds a painter. Neither touches layout.

#### D1.2 Layout: a column packer, computed once per episode

1. **Canvas.** Fixed at **1440 × 896 px**, multiples of 16 so imageio does not resample (Q3). Header = measured line + padding.
2. **Columns.** Left 300, right 330, centre = remainder minus two 16 px gutters; module constants.
3. **Heights.** Per column, sum the present panels' min heights plus gaps. Leftover height goes to the grow panel: minimap (left), arena (centre, capped at square), and shared in proportion on the right.
4. **Fit-or-fail.** Try `compact` min sizes first. If a column still overflows, raise `LayoutOverflowError` with the panel demands **before any frame is drawn**. On the training path this fails only the render child: `async_render.py` isolates it, the recordings stay on disk, and the error is in the render log.
5. **Output.** `dict[key → Box]` in integer px; boxes disjoint by construction (CP1).

Stretchable/Taffy stays a possible later drop-in behind `Box`; it isn't needed for three stacked columns.

#### D1.3 Painting inside the box

- **Axes.** One `fig.add_axes(rect)` per panel, `clip_on=True`, layout engine `'none'`.
- **Card borders.** Drawn as a separate unfilled outline artist. Text may not touch it (§D5.2).
- **`fit_text(ax, text, box, max_pt, min_pt=8, numeric: bool)`.** Measures with `get_window_extent` and shrinks down to 8 pt.
  - **Numeric kinds never ellipsise:** `vital_row`, `temp_row`, `hidden_state`, `intensity`, `thermal_diamond` cells and `text_row` raise `TextFitError` at the floor, in every mode.
  - **Free text** (header only) may ellipsise at the floor, and each ellipsis is written to the render log.
- **Round 2 decisions carried in full:**
  - Merged VITALS card.
  - `LABEL  OBS (REAL)`: REAL is the same size and muted, with **no Δ text**, and a tick marks REAL on the bar.
  - Action badge at the arena card's top-right (Q4).
  - Horizontal 8 pt legends above bars.
  - Minimum px gap between title and tallest bar.
- **Vocabulary.** Labels use the project's terms. `INOC` for interoceptive nociception and `EXTERO NOCICEPTION` in full; never "pain".
- **Channel labels.** Visual channels use `HPR` for hiding predator (Q11). The mapping lives in a V2-owned label table keyed by channel index (`src/environment/dashboard/labels.py`), which overrides the `labels` field `build_sensory_viz` emits. `sensor.py` is not edited, so V1 frames keep `DNG` until retirement.
- **Frozen V1 helpers.** V1 helpers are imported read-only. If one needs any behaviour change, it is copied into the package, never edited in place.
- **Imported V1 signatures** (working tree, 2026-09-14), pinned by `tests/env/test_dashboard_v1_imports.py` via `inspect.signature`. A change fails that test naming the helper; the fix is to copy the helper into the package or re-pin with a note, never to adapt silently.
  - `src/environment/renderer.py`:
    - `_load_icons(icon_config=None)`
    - `thermal_color_limits(thermal_field, params)`
    - `_thermal_rgba(value, clim)`
    - `draw_temperature_gauge(ax, x, y, w, h, body_temp, params, clim, transform=None, label_dy=0.02, obs_temp=None)` (`obs_temp` is the other session's uncommitted addition)
    - `draw_thermal_diamond(ax, x, y, w, h, values, sensor_range, clim, transform=None, colour_offset=0.0)`
    - `draw_boresight_diamond(ax, x, y, size, vec, r, num_features, true_vec=None, icons=None, obs_only=False, transform=None)`
    - `save_jax_video(frames, output_path, fps=5, quiet=False)`
    - the `COLORS` dict (keys used are listed in the test)
  - `src/environment/sensor.py`:
    - `build_sensory_viz(obs, state, params, true_obs=None)`
    - `get_observation_breakdown(params)`
    - `get_observation(state, params, apply_noise=True)`
  - `src/utils/eval_recording.py`:
    - `EpisodeRecorder(episode_index, train_episode, seed)`
    - `write_run_meta(out_dir, params, icon_config, action_map, config_path, extras=None)`
    - `load_run_meta(recording_dir)`
    - `load_episode(path)`

#### D1.4 Build once, update per step; arena entities

`EpisodeRenderer(params, icon_config, episode_payload)`:

- **Setup (once).**
  1. Context, completeness rule, layout.
  2. Figure plus every artist: card outlines, titles, legends, bar tracks, arena grid lines, and a fixed pool of `AxesImage` icon slots per view cell per layer.
  3. Thermal underlay `imshow` with fixed `set_clim`, and gauge marks.
- **`frame(t)`.** `extract`, update artists (`set_width`, `fit_text` updates, `set_data`, `set_visible`, `set_offsets`), then `canvas.draw()`, then copy of `buffer_rgba()[..., :3]`.
- **`close()`.** `plt.close(fig)`.
- **`layout_signature()`.** Hash of the panel keys, kinds, boxes and REAL-slot flags, used by the concat check in §D4.2.
- **Iconless entities (review finding 11).** For any obstacle, resource or animal whose icon key is missing from `icon_config` or whose file is absent, the arena draws a **deterministic glyph**: a filled rounded square in the entity's category colour, plus a centred 1–3 letter code derived from its name (e.g. `CF` for campfire). The mapping lives in a small table in the painter module, with its own test that codes are unique across `params.obstacle_names`. This path is always needed because archived `icon_config` pickles lack keys added later. A real `campfire.png` is **deferred to the retirement gate** (Q12): adding its `icons:` mapping would change V1 production videos, since evaluation reads `visualization.icons` into `icon_config`.
- **Single-frame wrapper.** `render_dashboard_frame(...)` builds a one-frame `EpisodeRenderer` for the demo, dream-visualiser and benchmark callers.

### D2. Stack comparison and recommendation

Speed figures are **estimates** unless marked measured. The Phase 0 gate (§D5.3) replaces them with lab-node measurements.

| | **A. Matplotlib painters + own packer + figure built once** (recommended, narrowly) | **B. Pillow (or skia-python) painters + same packer** | **C. HTML/CSS page in a persistent headless Chrome per worker** |
|---|---|---|---|
| Overlap guarantee | Boxes disjoint; per-panel clip; numeric text raises instead of shrinking past 8 pt; pixel audit (§D5.2) | Same as A | Strongest by default (CSS box model, `overflow`, `text-overflow`) |
| Per-frame CPU | est. 30–100 ms after setup. Context, container i9-7900X via `render_current_frames.py`: V1 default 0.36 s, V1 thermal first call 4.29 s incl. warm-up, dormant V2 ~0.5–0.6 s | est. 5–20 ms | est. 20–60 ms warm screenshot |
| Porting cost | Low–medium: V1 drawing logic re-homed into per-panel axes, artist-update form | High: every painter in 2D primitives | Highest: every panel in HTML/SVG/canvas, icons + field as data, JS update code |
| New dependencies | None | None (Pillow) / `skia-python` | A Python↔Chrome driver (`playwright` or a CDP client; neither installed). **Chrome itself is present** on nodes 101, 106, 114 (reviewer, direct SSH, 2026-09-14); the other 11 nodes are unsampled |
| Training-time / multiprocess fit | Unchanged process model under `async_render.py` | Same | Browser (≈150–300 MB) per worker inside a `Popen`ed child that is already known to orphan on SIGINT (wiki `train_py_orphan_render_workers_on_sigint`); orphaned browsers hold RAM and processes on training nodes |
| Viewer | Server renders PNG per step with the same renderer (§D3); needs a running Python process with NAS access | Same, faster scrubbing | One page is both the video source and the viewer (§D2.1) |
| Text quality | Good (current look) | Pillow lower unless supersampled; skia good | Best |
| Test determinism | Agg byte-stable per machine (to confirm across processes, CP0.1) | Stable | Screenshot pixels depend on Chrome version and fonts, which can differ between nodes, so byte-hash tests turn into tolerance tests |

#### D2.1 What C's viewer gives that A's does not (stated plainly, because the user asked for a viewer)

1. **A static, shareable viewer.** C's page can load the episode as JSON (a few MB) and run with no Python process. It could be published as an Artifact or opened by a collaborator without NAS access. A's static export is pre-rendered JPEGs (~30 MB per 500-step episode, est.).
2. **Instant scrubbing.** C updates the DOM locally, while A pays one server render per unseen step (est. 30–100 ms, mitigated by prefetch).
3. **In-page inspection.** Hover a grid cell or bar to read raw values, toggle panels, zoom the arena. A offers a values table beside the frame instead.
4. **One spec drives both outputs, with no server in between.** In A the spec is also shared (same renderer), but the viewer is a thin client around Python.

**What C costs, now that the Chrome-presence argument is gone:**
- a new Python dependency on the training-time render path;
- browser lifecycle inside an orphan-prone render child;
- re-authoring every panel, including the arena, icons and thermal underlay;
- screenshot nondeterminism across nodes, which weakens the byte-identical checks this plan relies on.

**Recommendation: A, with B as fallback.** A keeps the training path unchanged and the verification byte-exact, and it fixes every defect class listed (D1–D12). The margin is narrow. If a static, shareable, inspectable viewer matters more to the user than those costs, **C is a defensible choice**. In that case the registry semantics, observed-vs-hidden rule, audit and checkpoints still apply, and the other 11 nodes should be sampled for Chrome first. A hybrid (A for video + a separate JavaScript viewer) is **not** recommended: it would mean two implementations of every panel that can drift apart.

### D3. Interactive viewer (for A/B; for C this section is replaced by the page itself)

- **Reads.** A recordings directory (`run_meta.pkl` + `episode_*.rec.gz`), the same inputs as `render_recordings.py`.
- **Runs.** `scripts/eval/episode_viewer.py <recordings_dir> [--port 8765]` on the container or a lab node with the NAS mounted (via SSH port-forward). Bound to `127.0.0.1`, stdlib `ThreadingHTTPServer`.
- **Endpoints.**
  - `/` (static HTML under git).
  - `/api/episodes` (index, steps, final step).
  - `/api/frame?ep=&t=` (PNG of `EpisodeRenderer.frame(t)`, one renderer per open episode, LRU cache).
  - `/api/values?ep=&t=` (JSON of every panel's `extract`, including `observed`/`hidden` flags, action, termination).
- **Page.**
  - Episode picker, step slider; ←/→ steps by 1, Shift+←/→ by 10; play/pause at the video fps; jump to first or last step.
  - Prefetches ±5 frames.
  - Collapsible values table.
- **Shares the spec.** It imports `EpisodeRenderer`. A test asserts the served frame equals the in-process array; raw arrays are compared, not MP4, since the MP4 is resized to 1408×1008 today.
- **Static export (Q7).** `--export <episode> out.html`, JPEG frames + values JSON, `--stride` for long episodes.

### D4. Backward compatibility

#### D4.1 Pre-thermal and older recordings

- **State fields.** `body_temp` and the thermal underlay exist only when the snapshot has them (same contract as V1 and the thermal plan's D4).
- **Archived params.** Flags on unpickled `EnvParams` are read through `_recording_flag(params, name)`. It returns "absent" **only** when the attribute does not exist, and it is documented as absence-shaped compatibility for recordings, never used on the live config path. A test pins that only `src/environment/dashboard/` imports it.
- **Bar.** V2 renders every recording V1 renders (tested on M7).

#### D4.2 REAL availability: decided from params, captioned from data

- **`real_available[m]`**, once per run:
  - `_recording_flag(params, 'perceptual_noise_enabled')` is true, **and**
  - `m` appears in `noise_modality_order`, **and**
  - `noise_modes[index] != 0`.
  - Every episode of a run shares these params, so the REAL slot is identical across a concatenated video.
  - The breakdown-name ↔ noise-order-name mapping is built from `sensor.py`'s own modality map and printed per matrix cell at CP0.2. A modality whose mapping can't be resolved raises.
- **Captions** when `real_available[m]` is true:
  - `true_obs` recorded: show REAL values and tick.
  - `true_obs is None` (e.g. `testing.record_true_observations: false`): reserve the slot and show the muted caption "true obs not recorded".
- **When false:** no REAL slot, no tick, and a card caption "no noise".
- **Sub-epsilon differences:** never used to decide layout. Where REAL is shown and `|true − obs|` is below 1e-6, the tick sits on the fill end (12_renderer.md pitfall 4).
- **Concat check.** `render_recordings_v2.py --concat` asserts all episodes' `layout_signature()` are equal before concatenating, and fails otherwise.

#### D4.3 Thermal colour limits

- `thermal_color_limits(snapshot0.thermal_field, params)` is computed once in setup, with `set_clim` once, and the scale strip prints the limits.
- Port `test_a_cooling_world_does_not_rescale_its_colours`, `test_render_honours_an_explicitly_pinned_clim` and `test_a_recording_without_thermal_fields_still_renders`.
- Mutation M1 (per-frame recompute) must turn them red.

### D5. Verification that detects failure

#### D5.1 Real recordings across a config matrix

`scripts/eval/make_render_fixture_recordings.py` steps the **real environment** with a **seeded random policy**. It writes through the **production** `EpisodeRecorder` / `write_run_meta`, with `true_obs` from `get_observation(state, params, apply_noise=False)`, to `results/render_audit/recordings/<cell>/<cell>/` (gitignored; unique leaf names avoid the output-path collision in wiki `render_recordings_output_path_collision`). Each cell's `run_meta` `extras` records `config_path` plus two hashes: `config_sha256`, over the **resolved** config after `extends:` layering, serialised as sorted-key JSON; and `config_chain_sha256`, a map of every file in the `extends` chain to its content sha256. Both are taken at generation time. If the other session edits a config later, "M4" visibly means something different rather than silently changing. Real trained-policy recordings are added as further cells.

| Cell | World (plain description) | Source (resolve at CP0.2; archive configs may not load at current code) |
|---|---|---|
| M1 default | Default world, spectrum smell, noise off | `configs/environment/default.yaml` |
| M2 interoceptive nociception | Interoceptive nociception observed, noise off | `configs/environment/experiment/archive/hypervigilance/01-interoNocicept.yaml` |
| M3 interoceptive nociception + noise | Same with perceptual noise on | `…/01-interoNocicept_noise.yaml` |
| M4 thermal | Campfire temperature world; observation lacks Nutrition/Injury and (working tree 2026-09-14) includes Body Temperature | `configs/environment/experiment/thermal/campfire_world.yaml` |
| M4b thermal, body temperature not observed | M4 with body temperature removed from the observation, so the temperature row takes the "not observed" path | **in-memory** override of M4 (`body_temp_observable: false`) labelled as such in the report; no config file written or read beyond M4's |
| M5 directional smell | Olfaction as a directional grid | `configs/environment/experiment/sensory_directional/B_olfaction.yaml` |
| M6 location sensor | Location sensor on | grep `location_sensor_enabled: true` under `configs/`; if none, an **in-memory** override of M1 labelled as such (no config file written) |
| M6b noise on, true obs not recorded | M3's world recorded with `true_obs=None` | generator flag `--no-true-obs` (exercises the "true obs not recorded" caption) |
| M7 pre-thermal, trained | Real policy, recorded before the thermal system | `results/eval/noPredator_chasingRabbit/models/9520028/recordings/9520028/` |
| M8 interoceptive nociception, trained, noise off | Real policy | e.g. `results/JAX_RecurrentPPO/20260501-005013_interoNocicept_predRange5_decoy75_std4/recordings/100049/` |
| M9 interoceptive nociception, trained, noise on | Real policy; REAL differs from OBS | e.g. `results/JAX_RecurrentPPO/20260501-050423_interoNocicept_predRange5_decoy75_std4_noise/recordings/100023/` |

M8/M9 do not depend on archived configs loading. If M2/M3 cannot be generated, M8/M9 cover those cells and the substitution is recorded. About 20 more trained recordings exist under `results/JAX_RecurrentPPO/*/recordings/`.

**Frames checked per cell:** step 0; last step; max injury; max extero nociception; min and max `body_temp` (M4); max REAL−OBS gap (M3/M9); and for M4 a step where the campfire is in view. A **stress variant** copies those snapshots with extreme values (body temp −14.99, noisy OBS outside [0,1], all visual channels 1.0), labelled "derived input, text-fit stress only". It must either render clean or raise `TextFitError`/`LayoutOverflowError`, never produce a frame with an ellipsised number.

#### D5.2 Overlap/clip audit with a pixel ground truth

`scripts/eval/render_layout_audit.py` (also imported by tests; tests carry the registered `integration` marker). **It imports neither the layout module nor the registry.** A test checks its imports. For each checked frame:

1. **Element classification by artist type and geometry, not by painter tags** (review finding 3).
   - **Foreground:** every `Text`; every `Line2D` shorter than 90% of its axes' width and height (ticks, marks); every `AxesImage` smaller than 90% of its axes (icons); every `Patch` with area below 90% of its axes' area (bar fills, cells, glyphs, pills); every **unfilled** outline patch (card borders), whatever its size.
   - **Background (demoted):** only filled patches ≥ 90% of their axes (card fills), `AxesImage`s ≥ 90% of their axes (the thermal underlay), and `Line2D`s spanning ≥ 90% of the arena extent (grid lines).
   - The audit **asserts this geometry itself**, measured via `get_window_extent`. Painter `gid`s are used only to name elements in the report.
   - V1 frames use the same classifier, so V1 and V2 are judged by one rule.
2. **Ink masks.** One full render, plus one render per element with that element hidden. The element's ink = pixels that differ. This is N+1 renders per frame (~40 s for a V1 frame, est.).
3. **Collision rule.** A text element's ink, dilated 1 px, intersecting any other foreground ink **fails**, including card-border outlines (text-on-border forbidden). Text over background ink is allowed. Every pair is reported with both strings and a crop.
4. **Clip rule.** A text element re-rendered with clipping off whose ink differs has been cut off, and fails.
5. **Legibility floor.** Every text element's ink height is at least the rendered height of a reference 8 pt "0" measured at the canvas dpi.
6. **Presence (ground truth = breakdown).** For every name in `get_observation_breakdown(params)` not on the explicit not-displayed list (Q5), the report must contain foreground ink attributable to a panel for that name. The name → panel association is read from rendered text (the panel title string, matched against a fixed title table in the audit module), not from the registry.
7. **Observed-caption rule (ground truth = breakdown).** Any rendered text beginning `OBS` or `REAL`, or containing "obs only", must belong to a panel whose title maps to a breakdown name that is present. Any `hidden_state` row's text must contain "not observed".
8. **Vocabulary rule (V2 frames).** No rendered text matches `\bpain\b` (case-insensitive), and no legend contains `DNG`. V1 frames are exempt, because V1 is frozen and still shows `DNG`.
9. **Canvas.** No foreground ink in the outer 4 px margin; dimensions equal the declared canvas.

**Positive controls** (known defects; if any is missed, the audit is broken, so stop):
- V1 M4 frame: **D1**, **D2**, **D3** (text on the Run Context border), and **D10** (`OBS` under Nutrition/Injury while the breakdown lacks them).
- Dormant V2 M4 frame: **D6**, and presence reporting **Interoceptive Nociception** absent, plus **Location**/**Proprioception** if they are in M4's breakdown (**D8**/**D12**).

**Mutation controls:**
- **M-A:** shift one V2 legend 6 px into its title; the audit must fail.
- **M-B:** set a vitals row's min height below its measured text and bypass fit-or-fail; the audit must fail.
- **M-C:** retag a bar fill's `gid`/role as background in the painter and draw a label over it; the audit must still fail, since classification ignores tags.
- **M-D:** swap a `hidden_state` caption to `OBS`; the observed-caption rule must fail.

**Value-to-pixel checks:**
- Bar-fill ink width at 0.0 / 0.5 / 1.0 in ratio 0 : 0.5 : 1 within 2 px.
- REAL tick x at a known value.
- Temperature gauge across the survivable band (port).
- **Obstacle ink (CP2.6).** For each obstacle name in `params.obstacle_names` with an instance in view at a checked step, that cell's foreground ink (with the underlay demoted) is non-empty.

**Headless Chrome visual check.**
- The audit writes a contact sheet `results/render_audit/<timestamp>/index.html`.
- `scripts/claude/check_artifact_layout.py` runs on the viewer page at 500/834/1440.
- `artifact-format-reviewer` or the verifier **looks at** the contact sheet and screenshots. A green audit is necessary, not sufficient.

#### D5.3 Timing benchmark and speed gate

`scripts/eval/benchmark_render.py` is frozen and not edited. The benchmark is a mode of the new entry point: `render_recordings_v2.py <recordings_dir> --benchmark`. It times V2 and V1 on the **same recordings, in a `ProcessPoolExecutor` worker, on the same lab node**. V1 is timed by calling `render_jax_state` read-only, with the same per-step inputs `render_recordings.py` builds. No video is written in this mode. The node is chosen via the `gpu-status` skill and the diary like any CPU claim, launched with `run_command.py`, and recorded in the report with CPU model. The benchmark reports:
- V2 setup ms / V1 first-frame ms;
- median and p95 per-frame ms over ≥ 200 frames (first 5 excluded, reported separately);
- worker RSS after 10 episodes;
- open FDs per worker.

**Gates (ratios, same node, same cell):**
- **Phase 0 decision gate (CP0.4):** A-spike median on M4 ≤ **0.5 × V1 median on M4** (Q9). If missed, go back to the user with B.
- **CP4:** V2 median ≤ 1.0 × V1 median on every cell, and ≤ 0.5 × on M4.
- **CP4:** worker RSS growth < 50 MB over 10 episodes.
- **Context only:** absolute ms, and today's container figures with their script `renderer_layout_redesign/render_current_frames.py` (i9-7900X container, not a pool worker).

#### D5.4 V1 pipeline preserved (user constraint; checkable)

**Frozen files** (no edits by this plan until a separately approved retirement step):
- `src/environment/renderer.py`
- `scripts/eval/render_recordings.py`
- `src/utils/async_render.py`
- `src/utils/evaluation_core.py`
- `src/algorithms/dreamer_srl/eval.py`
- `src/utils/eval_recording.py`
- `src/environment/sensor.py`
- `scripts/eval/benchmark_render.py`
- `src/environment/renderer_v2.py`: the dormant April renderer. **Not edited, not deleted, not shadowed**: no module or package named `renderer_v2` is created under `src/environment/`, because a package directory would take precedence over this file on import. Another session is editing it.
- `configs/visualization/default.yaml`: its `icons:` mapping feeds every V1 video via `icon_config`.

**New script `scripts/eval/v1_path_guard.py`**, stdlib + numpy, imports V1 modules read-only. Paths and repo root are parameters, so the test can run it on a throwaway repo. Subcommands:

1. **`record-files`**, the **first action of Phase 0**, before any other Phase 0 file exists. Writes `docs/develop/active/refactors/renderer_layout_redesign/v1_guard/baseline.json` (committed) with:
   - `plan_start_commit` = `git rev-parse HEAD`;
   - per frozen file: `worktree_sha256` (working-tree content, deliberately not HEAD, because another session has uncommitted edits in `renderer.py`, `renderer_v2.py`, `sensor.py` and `evaluation_core.py`) and `head_blob` (`git rev-parse HEAD:<path>`);
   - `plan_sessions: []`.

   Also writes `frozen_files_at_baseline.diff` beside it (committed) = `git diff <plan_start_commit> -- <frozen files>`, so the dirty-tree baseline state is recoverable from git. Its first line is a header: `# SNAPSHOT of other sessions' uncommitted work-in-progress at guard baseline (<date>). Record only; DO NOT apply.`
2. **`add-session <Claude-Session trailer value>`** (e.g. `https://claude.ai/code/session_…`). Every developer session working on this plan runs it before its first commit, and the updated JSON is committed with that first commit.
3. **`record-frames`**, run **right after `make_render_fixture_recordings.py` lands and has produced M1/M2/M4**, before any renderer code. Adds:
   - `fixtures`: sha256 of each used episode's **decompressed** `.rec.gz` payload (gzip headers embed mtime) and of `run_meta.pkl`, for M1, M2, M4 and the real M7 dir.
   - `frames`: sha256 of the **raw frames** of the first 8 steps per cell. The harness calls `render_recordings._worker_init(str(run_meta_path))` first (it fills `_WORKER_STATE`), monkeypatches **`src.environment.renderer.save_jax_video`** (the name `_render_episode` imports at call time) to capture the frame list, and passes an output path inside a temp dir (`_render_episode` still `mkdir`s its parent). No MP4 is involved.
   - Computed in **two separate processes**, which must agree.
4. **`check`**, run at the end of every phase. Prints `git diff --stat <plan_start_commit> -- <frozen files>` and `git log --format='%h %(trailers:key=Claude-Session,valueonly)' <plan_start_commit>..HEAD -- <frozen files>`, then assigns each frozen file exactly one state:

   | State | Condition (all mechanical) | Consequence |
   |---|---|---|
   | **PASS** | working-tree sha256 == baseline `worktree_sha256` | none |
   | **ATTRIBUTED** | working-tree content hashes to the same blob as `git rev-parse HEAD:<path>` (no uncommitted delta on top of HEAD) **and** every commit in `<plan_start_commit>..HEAD -- <path>` carries a `Claude-Session:` trailer whose value is **not** in `plan_sessions` | reported with the commit list; the verifier may re-record files + frames, and the re-record is committed citing those commits |
   | **UNATTRIBUTABLE** | anything else, including: an uncommitted delta that differs from baseline; any commit on the path **without** a `Claude-Session:` trailer; any commit whose trailer is in `plan_sessions`; any commit that touches a frozen file **and** any plan-owned path (`src/environment/dashboard/`, the new `scripts/eval/` files, the new tests, `docs/develop/active/refactors/renderer_layout_redesign/`), whatever its trailer | named in the report with diff stat and commits; **never passes, never re-baselined**; cleared only by the user, in writing, in the Implementation Report |

   Frames:
   - If a fixture hash differs, the report says **FIXTURE CHANGED** (the fixture was regenerated) rather than a renderer change; re-record frames only after confirming the generator commit.
   - If fixtures are unchanged and a frame hash differs: when all frozen files are PASS, that is **UNATTRIBUTABLE** (something outside the frozen set changed V1 output, e.g. an asset, a config, or a library); when the moved files are ATTRIBUTED, frames follow those files' consequence.
   - Exit code 0 only if there is no UNATTRIBUTABLE state.
5. **`accept <path> <sha256>`**, **run by the user only**. It appends `{path, sha256, date, note}` to `user_accepted` in `baseline.json` (committed). `check` reports a file whose working-tree content hashes to an accepted sha256 as **ACCEPTED**; any other content of that file is judged by the three states again. `accept` never changes `worktree_sha256` or the frame baseline. It exists so the thermal session's ordinary uncommitted delta, once looked at, does not block a phase boundary.

**Output isolation.** `render_recordings_v2.py` writes only under `<run_root>/videos_v2/<rec_dir.name>/` (per-episode) and `<run_root>/videos_v2/eval_<pct>.mp4` (concat), with `--output-dir` to override. It never reads or deletes anything under `videos/`. Its `--skip-existing` looks only in its own folder. This avoids the derived-path collision recorded in wiki `render_recordings_output_path_collision`. A test renders V1 and V2 for the same recordings directory and asserts both sets of MP4s exist with V1's bytes unchanged.

### D6. Config keys

**No new config keys, and no config key or default changes of any kind before the retirement gate.**
- Which renderer runs is decided by which script is invoked: `render_recordings.py` = V1 (unchanged, used by training and eval); `render_recordings_v2.py` = V2 (manual only). Canvas and font floors are module constants.
- No `campfire` entry is added to `configs/visualization/default.yaml` `icons:` during Phases 0–4. Evaluation reads that mapping into `icon_config`, so the entry would change V1 production videos. The asset is deferred to the retirement gate unless the user grants an explicit exception (Q12).

### File Changes

**Frozen (not edited by any phase; see §D5.4):** `src/environment/renderer.py`, `scripts/eval/render_recordings.py`, `src/utils/async_render.py`, `src/utils/evaluation_core.py`, `src/algorithms/dreamer_srl/eval.py`, `src/utils/eval_recording.py`, `src/environment/sensor.py`, `scripts/eval/benchmark_render.py`, `src/environment/renderer_v2.py` (not edited, deleted or shadowed). `configs/visualization/default.yaml` is also frozen and hashed by the guard.

**Phase 0: guard baseline, fixtures, audit, spike**

| File | Change |
|---|---|
| `scripts/eval/v1_path_guard.py` (new) | `record-files` / `add-session` / `record-frames` / `check` (§D5.4). `record-files` is the first action of Phase 0; `record-frames` runs right after the fixture generator lands. |
| `docs/develop/active/refactors/renderer_layout_redesign/v1_guard/baseline.json`, `frozen_files_at_baseline.diff` (new, committed) | Guard baseline and the frozen files' uncommitted delta at record time. |
| `scripts/eval/make_render_fixture_recordings.py` (new) | Matrix generator (§D5.1): `--cells`, `--episodes`, `--max-steps`, `--seed`, `--no-true-obs`, `--out`. Uses `EpisodeRecorder`, `write_run_meta`, `get_observation` read-only; writes `config_path` + `config_sha256` into `run_meta` extras. |
| `scripts/eval/render_layout_audit.py` (new) | Audit (§D5.2); imports neither layout nor registry. |
| `tests/env/test_render_audit_controls.py` (new, `integration` marker) | Positive controls (D1, D2, D3, D10 on V1 M4; D6 and presence on dormant V2 M4); import-isolation test. Mutations added in Phase 2. |
| `tests/env/test_v1_path_guard.py` (new) | In a throwaway git repo under `tmp_path`, with a fake frozen file and plan session `S1`, the three states are exercised:<br>• PASS: untouched;<br>• ATTRIBUTED: foreign commit with trailer `S2` and no extra delta;<br>• UNATTRIBUTABLE: an uncommitted edit; a commit without a trailer; a commit with trailer `S1`; a foreign commit plus an extra uncommitted delta.<br>Also: frame hash altered with files PASS gives UNATTRIBUTABLE; fixture hash altered gives FIXTURE CHANGED; exit code non-zero on any UNATTRIBUTABLE.<br>Plus: a commit with foreign trailer `S2` touching both a frozen file and `src/environment/dashboard/` gives UNATTRIBUTABLE; `accept` of the current sha gives ACCEPTED, and a further edit to that file is flagged again. |
| `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` | Same change as the Phase 0 scripts:<br>• §3 rows for `v1_path_guard.py`, `make_render_fixture_recordings.py` and `render_layout_audit.py` (all hand-run, `scripts/eval/` root-depth note);<br>• §1c test-suite rows for `tests/env/test_render_audit_controls.py` (imports the audit and generator) and `tests/env/test_v1_path_guard.py` (imports the guard). |
| `tmp/<timestamp>_renderer_spike.md` | Spike numbers (spike code stays uncommitted scratch). |

**Phase 1: registry and packer**

| File | Change |
|---|---|
| **`src/environment/dashboard/`** (new package; name is Q2) | `__init__.py` exports `EpisodeRenderer`, `render_dashboard_frame`. `src/environment/renderer_v2.py` is **not touched** (frozen; its deletion is a retirement-gate step). |
| `tests/env/test_dashboard_v1_imports.py` (new) | Pins the imported V1 signatures listed in §D1.3. Asserts no `renderer_v2` module or package was created by this plan: `src/environment/renderer_v2/` does not exist, and `import src.environment.renderer_v2` still resolves to the `.py` file. |
| `src/environment/dashboard/panels.py` (new) | `PanelSpec`, `RenderContext`, `FrameInputs`, registry, completeness rule, observed-vs-hidden rule, `_recording_flag`, `real_available` from params. |
| `src/environment/dashboard/labels.py` (new) | V2-owned channel label table (`HPR` etc.) overriding adapter labels (§D1.3). |
| `src/environment/dashboard/layout.py` (new) | Column packer, `Box`, `LayoutOverflowError`, compact fallback; no Matplotlib import. |
| `tests/env/test_dashboard_layout.py` (new) | Boxes disjoint/inside canvas for all cells. Toggling a modality frees its height. Overflow raises. Unregistered name raises. **M4 context has no observed Nutrition/Injury rows.** `real_available` identical for two episodes of one run. `_recording_flag` import confinement. |

**Phase 2: painters and episode renderer**

| File | Change |
|---|---|
| `src/environment/dashboard/text_fit.py` (new) | `fit_text` with the numeric-raise / free-text-ellipsis split, logging. |
| `src/environment/dashboard/painters.py` (new) | One painter per kind with `build`/`update`, card outlines as separate artists, `gid`s, iconless-entity glyph table. Imports drawing helpers from `renderer.py` read-only (`thermal_color_limits`, `_load_icons`, and others that take `ax` + coordinates). Any helper needing a change is **copied** into the package; **`renderer.py` is not edited** (frozen). |
| `src/environment/dashboard/episode.py` (new) | `EpisodeRenderer` (setup / `frame` / `close` / `layout_signature`), wrapper `render_dashboard_frame`. |
| `tests/env/test_dashboard_frames.py` (new, `integration` marker) | Audit clean on all cells' checked frames + stress variant. Mutations M-A..M-D fail as expected. Value-to-pixel, obstacle-ink (CP2.6), observed-caption (CP2.5) and vocabulary (CP2.4) checks. Glyph-code uniqueness. |
| `tests/env/test_dashboard_thermal.py` (new) | Thermal ports (§D4.3). |
| `tests/env/test_dashboard_compat.py` (new) | M7 renders with V1 and V2 (explicit skip reason if `results/` path absent; the Phase 3 audit run may not skip). M1 shows "no noise" captions. M6b shows "true obs not recorded". |

**Phase 3: separate V2 entry point (V1 pipeline untouched; nothing in training or eval calls it)**

| File | Change |
|---|---|
| `scripts/eval/render_recordings_v2.py` (new) | Reads the same `recordings_dir` (`run_meta.pkl` + `episode_*.rec.gz`). Pool, one task per episode: `EpisodeRenderer` → `frame(t)` loop → `close()` → `save_jax_video` imported read-only. Output only under `<run_root>/videos_v2/` or `--output-dir` (§D5.4). Flags mirror V1's where meaningful: `--workers`, `--fps`, `--concat` (with the `layout_signature` assertion), `--skip-existing` (own folder only), `--max-episodes`, `--stride`. **No** `--cleanup-per-episode`, so it can never delete anything. Plus `--benchmark` (§D5.3). Its own fd-limit raise is copied, not imported, from V1. |
| `tests/scripts/test_render_recordings_v2.py` (new) | Output isolation: V1 and V2 on the same fixture dir; V1 MP4 bytes unchanged, V2 MP4s only under `videos_v2/`, nothing written under `videos/`. `--skip-existing` ignores V1 files. Concat signature assertion trips on a doctored two-param-set dir. |
| `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` | §3 row for `render_recordings_v2.py` (manual-only caller; no `src/` caller; `scripts/eval/` root-depth note). §1c row for `tests/scripts/test_render_recordings_v2.py` (bare-imports the script; `parents[2]` depth). |

**Phase 4: viewer**

| File | Change |
|---|---|
| `scripts/eval/episode_viewer.py` (new) | Server (§D3). |
| `scripts/eval/episode_viewer.html` (new) | Page; light mode. |
| `tests/scripts/test_episode_viewer.py` (new) | Served PNG == in-process array; `/api/values` == `extract` including observed/hidden flags; out-of-range → 404. |
| `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` | §3 row for `episode_viewer.py` (hand-run server). A "**not a script**" row for `episode_viewer.html` (served by the viewer; precedent row `scripts/analysis/pipeline_layout.html`). §1c row for `tests/scripts/test_episode_viewer.py` (bare-imports the viewer; `parents[2]` depth). |

**Evidence already on disk (commit alongside this plan; top-level decides)**

`docs/develop/active/refactors/renderer_layout_redesign/` holds `render_current_frames.py`, `figures/v1_thermal.png`, `figures/v2_thermal.png`, `data/`, plus the artifact-page builder files.

**Docs (same change as the code they describe)**

| File | Change |
|---|---|
| `docs/environment/12_renderer.md` | Replace the dormant-V2 sections with the registry / packer / episode-renderer design, the observed-vs-hidden rule, the separate `render_recordings_v2.py` entry point and `videos_v2/` folder (V1 remains what training and eval use), viewer, audit, and "add a modality = registry entry". **One disambiguating sentence:** "'V2' in documents before 2026-09-14 means the April 2026 subfigures renderer in `src/environment/renderer_v2.py` (dormant, to be removed at the retirement gate); from 2026-09-14 'V2' means the registry-based renderer in `src/environment/dashboard/`, run via `scripts/eval/render_recordings_v2.py`." Fix stale `render_recordings.py` line citations. |
| `docs/environment/ENVIRONMENT_SUMMARY.md` | Renderer row: V1 default, V2 status, viewer. |
| `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` | See the Phase 0 (three scripts, two test rows), Phase 3 (one script, one test row) and Phase 4 (viewer script, HTML "not a script" row, one test row) entries. Each lands in the same change as its files. |
| `docs/environment/CONFIG_CRITICAL_SETTINGS.md` | No change. |

**After user approval of this plan (senior-developer)**

0. Tell the thermal session (via the diary and a note in [[BODY_TEMPERATURE_OBSERVATION]]'s owner hand-off) that this plan freezes the V1 video path and `renderer_v2.py` but does not block its work there. The guard will report its commits as ATTRIBUTED **only** if they carry a `Claude-Session:` trailer.
1. Set [[UI_REDESIGN_PROPOSAL]] `status: superseded`, `superseded_by: RENDERER_LAYOUT_REDESIGN.md`; `git mv` it to `docs/develop/archive/`; `python scripts/claude/regen_dev_index.py`. Commit with an explicit pathspec after checking `INDEX.md` hunks (review finding 12).
2. `bug-curator` rows:
   - dashboard text collisions and dropped panels (D1–D9);
   - V1 captions unobserved Nutrition/Injury as `OBS` (D10);
   - campfire obstacle has no icon (D11);
   - `Proprioception` emitted but never drawn (D12).

**Phase 5: retirement gate (a later, separate user decision; not authorised by approving this plan)**

Until the user explicitly decides to move training/eval videos to V2, **no frozen file is edited and no config key or default changes**. Approving this plan approves Phases 0–4 only.

Preconditions for even proposing the switch:
- Phases 0–4 verified with CP-G passing after each.
- The user has looked at `render_recordings_v2.py` output for one real training run's recordings.
- The speed gate is met.

The switch itself gets its own plan section and review. Expected steps:
1. Point `render_recordings.py` (or the three `src/` callers) at V2 by the mechanism the user picks. That is the first edit to a frozen file, and the plan section must say how archived recordings and saved run configs are handled.
2. Soak for one training cycle. A `LayoutOverflowError`/`TextFitError` on the training path fails only the render child.
3. Port the demo, dream-visualiser and benchmark callers.
4. Move shared helpers into the package with re-exports.
5. Delete V1's layout body. Rename `DNG` → `HPR` in `sensor.py` and the V1 default label list, now allowed.
6. Delete the stale `grid_world.py` render copy **only after a grep confirms no importer and the user OKs it**. Delete the dormant `src/environment/renderer_v2.py` only after the thermal session has been told and its uncommitted edits to that file have landed or been abandoned by that session; confirm with `git status` on the file. Add the `campfire` icon asset and mapping if Q12 chose to defer it here.
7. Retarget `test_thermal_rendering.py` and `test_eval_recording.py` to V2.
8. Update docs.

---

## Layout blueprint

Thermal-on, all sensors observed, noise on (1440 × 896 px). ASCII compresses rows and abbreviates labels where too narrow; real frames use full 8 pt labels.

```
┌────────────────────────────────────────────────────────────────────────────────────────────────┐
│ GridWorld · episode 3 · checkpoint 80% · seed 7                      step 23 / 501             │
├────────────────────────┬──────────────────────────────────────────────┬────────────────────────┤
│ VITALS     obs (real)  │ ARENA · LOCAL VIEW 5×5            [ ↓ DOWN ] │ OLFACTORY   obs ┃real  │
│ ┌────────────────────┐ │ ┌──────────────────────────────────────────┐ │ FOD ANA ANB BSH TRE    │
│ │SAT  0.90 (0.95)    │ │ │        │        │        │        │      │ │  ▓    ▓▓   ▓    ▓▓   ░ │
│ │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓┃░░░ │ │ │  food  │        │        │  pred  │      │ │ ────────────────────── │
│ │NUT  0.75 (0.77)    │ │ │────────┼────────┼────────┼────────┼──────│ │ EXTERO NOCICEPTION     │
│ │▓▓▓▓▓▓▓▓▓▓▓┃░░░░░░░ │ │ │        │  warm  │  CF    │  warm  │      │ │ OBS 0.66   REAL 0.90   │
│ │INJ  0.71 (0.45)    │ │ │────────┼────────┼────────┼────────┼──────│ │ ▓▓▓▓▓▓▓▓▓▓▓▓░░░░┃░░░░  │
│ │▓▓▓▓▓▓▓▓┃▓▓▓░░░░░░░ │ │ │  rock  │  warm  │ AGENT  │  warm  │ rock │ │ ────────────────────── │
│ │INOC 0.20 (0.18)    │ │ │────────┼────────┼────────┼────────┼──────│ │ THERMOCEPTION  vs body │
│ │▓▓▓┃░░░░░░░░░░░░░░░ │ │ │        │        │  pred  │        │      │ │          [+4]          │
│ │TEMP +4.19 die ±15  │ │ │────────┼────────┼────────┼────────┼──────│ │    [+4] [+62] [+4]     │
│ │|░░░░░░╎▓▓▓░░░░░░░| │ │ │        │        │        │        │      │ │          [+4]          │
│ └────────────────────┘ │ │  (thermal field underlay, cold→hot)      │ │ ────────────────────── │
│ MINIMAP  10×10 world   │ │        │        │        │        │      │ │ COLLISION              │
│ ┌────────────────────┐ │ └──────────────────────────────────────────┘ │  C    U    R    D    L │
│ │ · ·  ┌────┐   ·  · │ │ cold -66 ░░░░░░░░░▒▒▒▒▒▓▓▓▓▓▓▓▓▓ +66 hot     │  ·    ·    ▓    ·    · │
│ │   ·  │ ●  │ ·      │ │   field colour scale, fixed for the episode  │ ────────────────────── │
│ │ ·    └────┘    ·   │ │                                              │ VISUAL  (range 1)      │
│ │    ·     ·   ·   · │ │                                              │ GRS SND PLN FOD HPR …  │
│ │ ·   ·       ·      │ │                                              │ ▓   ·   ·   ·   ·   …  │
│ └────────────────────┘ │                                              │ (one row per cell)     │
│ LOC  (0.42, 0.77)      │                                              │                        │
└────────────────────────┴──────────────────────────────────────────────┴────────────────────────┘
```

Reading guide:
- **INOC** is interoceptive nociception.
- **TEMP**'s bar has die thresholds at both ends (`|`) and the setpoint at `╎`. In a world where body temperature is not part of the observation, this row reads `TEMP +4.19  not observed`, with no OBS/REAL.
- **CF** is the campfire's generated glyph, the only campfire rendering in the new renderer until the retirement gate (Q12).
- **HPR** is hiding predator.
- The old RUN CONTEXT box is folded into the header, and the action badge sits in the arena card's title strip.
- **Campfire world as actually configured (M4):** its observation has no Nutrition or Injury. Those rows either disappear or, if Q10 = show, appear as `NUT  0.75  not observed` / `INJ  0.71  not observed` with plain bars and no `(real)` or tick. In the 2026-09-14 working tree its body temperature **is** observed (`Body Temperature` in the breakdown), so `TEMP` shows OBS (with REAL per the noise rule).

**Default world, noise off:** no interoceptive nociception, no temperature, no heat sense, spectrum smell, no location. It collapses to:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────┐
│ GridWorld · episode 1 · checkpoint 80% · seed 7                       step 5 / 212             │
├────────────────────────┬──────────────────────────────────────────────┬────────────────────────┤
│ VITALS  (no noise)     │ ARENA · LOCAL VIEW 5×5            [ ● REST ] │ OLFACTORY  (no noise)  │
│ ┌────────────────────┐ │ ┌──────────────────────────────────────────┐ │  ▓    ▓▓   ▓    ▓▓   ░ │
│ │SAT  0.95           │ │ │                                          │ │ ────────────────────── │
│ │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░ │ │ │   no thermal underlay, no scale strip:   │ │ EXTERO NOCICEPTION     │
│ │NUT  0.95           │ │ │   the arena takes the full column        │ │ OBS 0.00               │
│ │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░ │ │ │   height (square, so width-limited)      │ │ ────────────────────── │
│ │INJ  0.00           │ │ │                                          │ │ COLLISION              │
│ │░░░░░░░░░░░░░░░░░░░ │ │ └──────────────────────────────────────────┘ │  C    U    R    D    L │
│ └────────────────────┘ │                                              │ ────────────────────── │
│ MINIMAP  10×10 world   │                                              │ VISUAL  (range 1)      │
│ ┌────────────────────┐ │                                              │ GRS SND PLN FOD HPR …  │
│ │ (grows into the    │ │                                              │ (4 pods share height)  │
│ │  space the two     │ │                                              │                        │
│ │  missing vital     │ │                                              │                        │
│ │  rows released)    │ │                                              │                        │
│ │                    │ │                                              │                        │
│ └────────────────────┘ │                                              │                        │
└────────────────────────┴──────────────────────────────────────────────┴────────────────────────┘
```

Collapse rules:
- **Presence:** rows follow the observation breakdown. Absent vitals rows and absent extero pods release their min height to the grow panel.
- **Thermal off:** removes the underlay and scale strip.
- **Noise off:** removes every REAL slot and tick for the whole run, with a "no noise" caption. Noise on with no recorded true observations keeps the slot, captioned "true obs not recorded".
- **Directional smell:** replaces the spectrum with a grid. If the right column overflows, the compact fallback applies, else `LayoutOverflowError`.

---

## Checkpoints

Each checkpoint states what would show it failed.

- [ ] **CP0.1a: File baseline first.** `v1_path_guard.py record-files` is run as the very first Phase 0 action. `baseline.json` (plan-start commit, nine frozen files' working-tree sha256 and HEAD blobs, empty `plan_sessions`) and `frozen_files_at_baseline.diff` are committed under `renderer_layout_redesign/v1_guard/`. `add-session` is recorded for the developer session. *Fails if:* any other Phase 0 file predates the baseline commit, or the diff file is missing.
- [ ] **CP0.1b: Frame baseline right after fixtures.** After the generator lands and writes M1/M2/M4, `record-frames` adds fixture hashes and 8 raw-frame hashes per cell for M1, M2, M4 and M7, from two separate processes; committed. `tests/env/test_v1_path_guard.py` green (all three states and FIXTURE CHANGED exercised). *Fails if:* the processes disagree (then switch to a pixel-diff tolerance and record it), any renderer code predates this commit, or the guard test passes a case it should flag.
- [ ] **CP-G: V1 pipeline untouched (after every phase, 0 through 4).** `v1_path_guard.py check` exits 0. The report pastes the diff stat, the trailer-annotated `git log`, and each frozen file's state. ATTRIBUTED re-records cite the foreign commits. *Fails if:* any file or frame is UNATTRIBUTABLE (only the user clears it, via `accept` for that exact content), a phase commit touches a frozen file, or a `renderer_v2` package/module is created.
- [ ] **CP0.2: Matrix recordings.** M1–M6b are written, including M4b (M4b's breakdown must lack `Body Temperature`, and its temperature row renders "not observed"); M7–M9 load; V1 renders step 0 of each. Per cell, print the snapshot keys, `true_obs is None`, the breakdown names, and the breakdown ↔ noise-order mapping. Also print each cell's `config_sha256` and whether `Body Temperature` is in its breakdown, plus that viz entry's keys. *Fails if:* M4 lacks `thermal_field`; M4's breakdown contains Nutrition/Injury (the D10 premise is then wrong, so re-check); M4's `Body Temperature` entry lacks a `value` key, or the registry has no owner for a breakdown name; M3/M9 have `true_obs == obs` everywhere; M5's Olfactory is not `visual_grid`; M6b has `true_obs` present; an archive config won't load (substitute M8/M9 and note); or a mapping is unresolved.
- [ ] **CP0.3: Audit positive controls.** V1 M4 reports D1, D2, D3 and D10. Dormant V2 M4 reports D6, and Interoceptive Nociception absent (plus Location/Proprioception if in the breakdown). *Fails if:* any control is missed. **Stop; the audit is broken.**
- [ ] **CP0.4: Spike and decision gate.** A minimal A-style `EpisodeRenderer` (arena + vitals + one pod, figure built once) versus V1, on M4, ≥ 200 frames, pool worker, same lab node (node + CPU recorded). *Fails the gate if:* A median > 0.5 × V1 median. Report to the user with option B before Phase 1.
- [ ] **CP1: Registry and packer.** `test_dashboard_layout.py` is green. *Fails if:* boxes intersect; a disabled modality's height isn't freed; an unregistered name doesn't raise; M4 yields observed Nutrition/Injury rows; `real_available` differs between episodes of one run.
- [ ] **CP2.1: Audit clean.** All cells' checked frames: 0 collisions (text-on-border included), 0 clipped text, legibility met, presence met. The stress variant renders clean or raises; no ellipsised number. *Fails if:* any count is non-zero, or "…" appears in a numeric element.
- [ ] **CP2.2: Mutations.** M-A, M-B, M-C and M-D each make the audit fail. *Fails if:* any mutation passes.
- [ ] **CP2.3: Values match pixels.** Bar ratio and tick x within 2 px; thermal ports green; per-frame clim mutation turns the cooling test red. *Fails if:* a tolerance is exceeded or the mutation stays green.
- [ ] **CP2.4: Vocabulary.** `grep -rniw 'pain' src/environment/dashboard/` shows zero hits (comments included; keep them clean too), and the audit's vocabulary rule is clean on all frames. *Fails if:* any hit.
- [ ] **CP2.5: Observed-caption.** On M4, no rendered text starting `OBS`/`REAL` belongs to a panel whose name is absent from the breakdown. With Q10 = show, the Nutrition/Injury rows read "not observed". *Fails if:* either condition is violated.
- [ ] **CP2.6: Entities drawn.** On M4, a step with the campfire in view shows non-empty foreground ink in its cell, and glyph codes are unique across `obstacle_names`. *Fails if:* the cell is empty or grey-square-only (no glyph ink), or codes collide.
- [ ] **CP3: Separate V2 entry point.** `render_recordings_v2.py --concat` writes playable MP4s (frame count = steps) for all cells including M7–M9, only under `videos_v2/`. The concat signature assertion holds on real runs and trips on the doctored dir. `test_render_recordings_v2.py` is green (V1 MP4 bytes unchanged after a V2 render of the same dir). CP-G passes. *Fails if:* any file appears or changes under `videos/`, the assertion trips on a real single-run dir, or CP-G fails.
- [ ] **CP4: Speed.** Same node as CP0.4: V2 median ≤ V1 median on every cell and ≤ 0.5 × on M4; RSS growth < 50 MB over 10 episodes; FDs reported. *Fails if:* any gate is missed.
- [ ] **CP5: Viewer.** `test_episode_viewer.py` is green; `check_artifact_layout.py` is clean at 500/834/1440; screenshots and the contact sheet are **looked at**, with findings in the report. *Fails if:* arrays differ, the checker flags a defect, or nobody looked.
- [ ] **CP6: Docs.** `12_renderer.md` (with the V2 disambiguation sentence), `ENVIRONMENT_SUMMARY.md` and `SCRIPTS_DEPENDENCY_MAP.md` are updated in the same commits as the code. *Fails if:* a script-adding commit lacks the map.

---

## Open questions for the user

1. **Stack.** A close call, with the full trade-off in §D2.1.
   - **A (recommended):** Matplotlib painters behind our own layout, figure built once, a local server-based viewer. The training-time render path is unchanged and tests stay byte-exact. B (Pillow painters) is the fallback if A misses the Phase 0 speed ratio.
   - **C:** HTML page in headless Chrome. It gives a static, shareable viewer with instant scrubbing and hover inspection. It costs a new Python dependency on the training render path, browser processes inside a render child that already orphans, re-authoring every panel, and screenshot tests that can't be byte-exact across nodes. Chrome is confirmed on nodes 101, 106 and 114; the rest would be checked before building.
2. **Name.** The new package can't reuse `renderer_v2`: another session is editing the dormant `renderer_v2.py`, and a same-named package would silently shadow it on import. Proposed `src/environment/dashboard/`; alternatives `src/environment/episode_dashboard/` or `src/environment/telemetry_view/`. The entry script and output folder keep the `_v2` names from your constraint (`render_recordings_v2.py`, `videos_v2/`). No new version number is introduced.
3. **Canvas size.** 1440 × 896 px. Today's videos are 1408 × 1008 after imageio's resize. This changes WandB video dimensions from switch-over onward.
4. **Action badge.** In the arena card's title strip at top-right (proposed; covers nothing), or overlaid on the grid's top-right cell (covers that cell's icon)?
5. **Proprioception.** Never drawn today. Add a panel (kind to be designed), or mark it "recorded, not displayed" so the completeness rule allows it explicitly?
6. **Minimap placement.** Left column under VITALS (proposed), or under the arena?
7. **Viewer delivery.** Local server only, or also a static single-episode HTML export (~30 MB per 500 steps, est.) for sharing?
8. **Retirement gate (for later, not now).** Per your 2026-09-14 constraint, nothing in training or eval moves to V2 during development. When you do decide to switch, do you want that as its own plan with review? It would be the first edit to the frozen V1 files. And do you approve, at that point, deleting the stale `grid_world.py` render copy and the dormant `renderer_v2.py` (the latter after the thermal session is told and its edits have landed)?
9. **Speed gate.** Is "the new renderer's median frame time ≤ half of V1's, same lab node, campfire world" the right Phase 0 threshold, with "not slower than V1" on every other world?
10. **Unobserved body state.** When the agent cannot observe a body variable (e.g. Nutrition and Injury in the campfire world), should the dashboard still show its true value as a row captioned "not observed", or omit the row entirely?
11. **Hiding-predator label.** Is `HPR` the right 3-letter abbreviation for the new renderer's Visual legend (e.g. `HID` / `HPD` instead)? V1 videos keep the legacy `DNG` until the retirement gate, because the sensor adapter is frozen.
12. **Campfire icon.** Adding a `campfire` icon mapping would change today's production (V1) videos too, because evaluation reads the shared icon mapping, and your freeze forbids that. Proposed: the new renderer uses the generated glyph (`CF`) only, and the real asset is deferred to the retirement gate. Alternative: add the asset now as an explicit exception to the freeze, knowing V1 videos will start showing the icon.

---

## Implementation Report

> **Implemented by**: [TBD]
> **Date**: [TBD]

<!-- Per phase: what was done, deviations, CP evidence (hashes, audit counts, timing table with node + CPU, screenshots looked at, empty src/ diff stat). -->

## Verification Report

> **Verified by**: [TBD]
> **Date**: [TBD]

| File | Change | Status | Notes |
|------|--------|:------:|-------|
| | | | |

**Conclusion**: [one-line summary]

## Feedback from plan-reviewer

**Date**: 2026-09-14 · **Verdict**: NOT READY (two Critical findings, both doc-level and cheap to fix; the architecture and verification design are otherwise sound). Full table, assumption list and pass log in [`docs/reviews/plan_renderer_layout_redesign.md`](../../../reviews/plan_renderer_layout_redesign.md).

Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run · 🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

**What blocks approval**

- 🔴 **"PAIN" as a row label / "pain" as the signal's name** (blueprint L429, L447; Context L20, L22; M2/M3 rows L263–264; L453). Project vocabulary: the signal is nociception; pain is the explanandum. A renderer label ends up in every video and figure. Use `INOC`/`NOCI` in the blueprint and "nociception" in prose; add a grep CP on the painter module.
- 🔴 **Vitals presence rule left undecided** (registry rows for satiation/nutrition/injury: "in breakdown **or** always"). V1 draws Nutrition/Injury from state and captions the value `OBS` even when the agent cannot observe them (`renderer.py:829`, `:837`). The campfire config's breakdown has no Nutrition/Injury. Copying "always" would tell a viewer the agent observes its injury when it does not. Derive rows from `get_observation_breakdown`; if a hidden state value is shown, it must never be captioned as observed.

**Should be resolved before Phase 0/1 (Moderate)**

- The pixel audit lets the painter under test declare which of its own ink is `background` and therefore exempt — classify by artist type/geometry instead, and add a mutation that retags a bar fill as background. Text-on-border (D3 class) is currently allowed and uncontrolled.
- The presence rule (silent panel drop, D8 class) has no positive control; dormant V2's M4 frame is one.
- V1 hash baseline omits M4/M7, exactly the path whose helpers V2 will import from `renderer.py`; CP4 does not say whether raw frames or MP4 bytes are hashed; `tests/training/test_async_render_dispatch.py` does not assert the spawned command list.
- Chrome **is** present on lab nodes 101, 106 and 114 (`/usr/bin/google-chrome`, checked by direct SSH today). The C rejection should rest on its other grounds only.
- The 200 ms gate has no stated hardware; the 0.36 s / 4.29 s figures came from an untracked container-side script, not a lab-node pool worker. Make the gate a same-machine, same-cell ratio.
- `real_available` from per-episode data lets the layout change between episodes of one concatenated video, and `true_obs` is `None` whenever `testing.record_true_observations` is off — decide availability from params, caption from data.
- `fit_text` ellipsising numeric readouts in production is a silent data loss in videos; numeric kinds should raise instead.
- `DNG` legend label (blueprint L439, L469; source `sensor.py:651`) is the pre-rename "danger" vocabulary.
- The campfire obstacle has no icon in `assets/` (V1 draws a grey square, `renderer.py:658`); the arena painter must say what it draws.
- `docs/develop/INDEX.md` has a staged hunk from another session and an unstaged regen that indexes an untracked doc — commit with a pathspec after checking hunks.

**For `bug-curator`** (not in the registry today): `Proprioception` viz entry emitted (`sensor.py:659`) but never drawn; campfire obstacle iconless; V1 captions unobserved Nutrition/Injury state values as `OBS`.

Reviewed by: plan-reviewer

## Feedback from plan-reviewer (second pass)

**Date**: 2026-09-14 (second pass, after the same-day revision) · **Verdict**: NOT READY — two Critical findings, both in how the revision handles the *other* session's live work; everything from the first pass (#1–#15) is resolved in the plan body, not only in the revision note. Full table in [`docs/reviews/plan_renderer_layout_redesign.md`](../../../reviews/plan_renderer_layout_redesign.md) §Second pass.

Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run · 🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

**First-pass findings, checked against the body (not the table):** residual "pain" appears only in rule statements ("never pain") and in quoted findings; `DNG` appears only as the V1 legacy label, the V2 override, the audit exemption and the retirement step; the Chrome premise is corrected everywhere it was wrong and the "other 11 nodes unsampled" caveat is honest. #3 (geometry classification + M-C), #4 (dormant-V2 positive control), #7 (same-node ratio gate), #8 (availability from params, layout-signature concat check), #9 (numeric never ellipsises), #11 (glyph fallback + CP2.6) are all in the body. Dropping the async-test assertion (#5) is right: no `--renderer` flag exists, and the three `src/` callers are now content-hashed. Resolved: all fifteen.

**What blocks approval**

- 🔴 **Phase 1 deletes a file the other session is editing right now.** `git status` shows `src/environment/renderer_v2.py` with 44 uncommitted lines from the thermal session (an `obs_temp` parameter on `draw_temperature_card`, the body-temperature call site), and that session's plans direct further mirroring into it (`thermal/IMPLEMENTATION_PLAN.md` L615, L621, L1964; `BODY_TEMPERATURE_OBSERVATION.md` Change 14). The revision note at L65 lists the file among the other session's edits, yet Phase 1 still says "`git rm` the dormant module". A plain `git rm` refuses on a file with unstaged changes; the only ways forward are `git rm -f` (destroys another session's uncommitted work: a parallel-session data-loss hazard) or waiting for their commit and then deleting what they just landed. Creating the package `src/environment/renderer_v2/` while `renderer_v2.py` still exists is not a workaround either: Python's import system resolves a package directory before a same-named module, so `import src.environment.renderer_v2` would silently stop returning their file. The frozen list has eight files; this is the ninth file the other session touches, and it is the one this plan removes. **Exit:** answer Q2 with the descriptive package name (e.g. `src/environment/dashboard/`), add `renderer_v2.py` to the not-edited / not-deleted set for Phases 0–4, and move its deletion to the retirement gate as a step the thermal session is told about. — owner `senior-developer`
- 🔴 **The V1-path guard's pass rule can pass silently and fail unresolvably, because it attributes changes by commit in a working tree two sessions share.** §D5.4 "Attributed change" passes a moved hash when (a) no plan commit touches the file and (b) the phase's commits do not list it, then re-baselines. Two holes. *Silent false-pass:* the developer edits `renderer.py` uncommitted, the thermal session commits its own `renderer.py` change; (a) and (b) both hold, the verifier re-baselines with the developer's edit inside it. It is caught later only if the developer's eventual commit subject "references this doc's topic", which is a heuristic, not a check. *Unresolvable fail:* the thermal session keeps editing `renderer.py` / `sensor.py` / `evaluation_core.py` before committing (its plan is mid-flight, so this is the expected case); the hash moves with "no commit behind it", the rule says Fail, and no re-baseline is permitted, so CP-G blocks every phase until another session commits. The guard reports loudly but cannot tell the truth: with one shared checkout, an uncommitted foreign edit and an uncommitted own edit are the same bytes. **Exit (mechanical, no heuristics):** per frozen file, PASS iff working-tree sha == baseline sha; ATTRIBUTED iff working-tree sha == `git rev-parse HEAD:<path>` (no uncommitted delta on top) **and** every commit in `<plan-start>..HEAD -- <path>` carries a `Claude-Session:` trailer that is not one of this plan's sessions (record the developer session IDs in the baseline; the trailer is already in this repo's commit messages); everything else is a third explicit state, UNATTRIBUTABLE, which the report must name and the user must clear — never pass, never re-baseline. Also add the fixture recordings' own hashes to the baseline so "frames moved because the fixture was regenerated" is reported as that, not as a renderer change. — owner `senior-developer`

**Should be resolved before Phase 0 (Moderate)**

- 🟡 **Phase 0 ordering is circular.** CP0.1 says `record` runs "before any other Phase 0 file lands", but its raw-frame hashes need the M1/M2/M4 fixtures, which only `make_render_fixture_recordings.py` (a Phase 0 file) can produce. Split it: file-hash baseline first (nothing else on disk), frame baseline immediately after the fixture generator lands and before any renderer code.
- 🟡 **The guard's baseline is unversioned and unreproducible.** It lives under gitignored `results/` (lost once already) and snapshots a *dirty* tree, so no commit reproduces it. Commit the JSON (small) under `renderer_layout_redesign/`, and store `git diff <plan-start> -- <frozen files>` at record time beside it so the baseline state is recoverable.
- 🟡 **V1 helpers are moving underneath the read-only imports, and one of them changes M4 today.** `campfire_world.yaml` in the working tree already has `body_temp_observable: true`, and `sensor.py`'s uncommitted `build_sensory_viz` emits a `"Body Temperature"` modality keyed `value` (not `intensity`). So the Phase 0 M4 fixture will carry `Body Temperature` in its breakdown, the completeness rule raises on it unless the registry owns it from day one, and the temp row takes the observed path, not the "not observed" path the blueprint describes for M4. §D1.1 still says "body-temperature name if the WIP lands" — it has landed in the tree Phase 0 records from. Name it now (`Body Temperature`, viz key `value`), and have the fixture generator write each cell's config content hash into `run_meta` extras so a later config edit by the other session is detected rather than silently changing what "M4" means. `draw_temperature_gauge`'s signature has also changed (`obs_temp=`); list the helper signatures V2 imports so a change is a visible break, not a runtime surprise.
- 🟡 **Q12's asset option contradicts the plan's own constraint.** `evaluation_core.py:277` reads `visualization.icons` into `icon_config` for every training/eval video, so adding a `campfire` entry to `configs/visualization/default.yaml` changes what V1 draws in production from that moment (an icon instead of the grey square). §D6 calls it "not a critical setting"; the constraint at L30/L422 says *any* config default. Either defer the asset to the retirement gate or state in Q12 that choosing it is a knowing exception the user accepts.
- 🟡 **Scripts dependency-map obligations are incomplete.** Phase 4 adds `scripts/eval/episode_viewer.py` and `episode_viewer.html` with no map row (the map already has a "not a script" precedent row for `pipeline_layout.html`); the Docs table says "Phase 0 for the two new scripts" while Phase 0 adds three; `tests/scripts/test_render_recordings_v2.py` and `test_episode_viewer.py` import scripts and therefore need §1c bare-import rows and the `parents[2]` depth note for `scripts/eval/`. — owner `senior-developer` (same-change contract)

**Low**

- 🟢 `slow` is not a registered pytest marker (`pyproject.toml` registers only `integration`); register it in the same change or use `integration`.
- 🟢 The guard's frame capture must patch `src.environment.renderer.save_jax_video` (the name `_render_episode` imports locally at call time), call `_init_worker(run_meta_path)` first (it fills `_WORKER_STATE`), and pass a scratch output path because `_render_episode` still `mkdir`s the parent.
- 🟢 CP2.4's `grep -rniw 'pain'` cannot exclude comments as the text claims; say "zero hits" and keep comments clean too.

**Q10–Q12:** Q10 is sound (both branches specified, CP2.5 covers both). Q11 is a naming call only. Q12 is the Moderate above.

**Cost of being wrong:** the first Critical costs another session its uncommitted work and its planned mirror target; the second turns the user's freeze into a green checkbox that cannot see a violation, discovered after Phases 0–4 when a training video changes. Neither costs a training run.

Reviewed by: plan-reviewer

## Feedback from plan-reviewer (third pass)

**Date**: 2026-09-14 (third pass, on Revision 2) · **Verdict**: SOUND WITH CONCERNS — no Critical finding. Both second-pass Criticals (#16, #17) and all Moderates/Lows (#18–#25) are resolved **in the plan body**, not only in the Revision 2 table. The user's freeze holds: no step in Phases 0–4 edits, deletes, or shadows any of the nine frozen files, and the `_v2` names collide with nothing. Four Moderate findings remain, three of them holes in what the V1-path guard can actually see. Full table in [`docs/reviews/plan_renderer_layout_redesign.md`](../../../reviews/plan_renderer_layout_redesign.md) §Third pass.

Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run · 🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

**Second-pass findings, checked against the body**

- **#16** — package is `src/environment/dashboard/` (§D1.3, §D5.4, File Changes Phase 1, Q2); `renderer_v2.py` is the ninth frozen file, "not edited, not deleted, not shadowed" (§D5.4 L439, File Changes L477); `test_dashboard_v1_imports.py` asserts no `renderer_v2` package exists and the import still resolves to the `.py`; deletion is Phase 5 step 6, after the thermal session is told (step 0 of "After user approval"). No `git rm` remains anywhere in Phases 0–4. Resolved.
- **#17** — §D5.4 `check` implements the three states mechanically: PASS iff working-tree sha256 == baseline; ATTRIBUTED iff working-tree content == `git rev-parse HEAD:<path>` blob **and** every commit in `<plan_start>..HEAD -- <path>` carries a `Claude-Session:` trailer not in `plan_sessions`; UNATTRIBUTABLE otherwise, explicitly including a missing trailer, cleared only by the user, never re-baselined. Fixtures (`.rec.gz` + `run_meta.pkl`) are hashed. `tests/env/test_v1_path_guard.py` exercises the false-pass case ("a foreign commit plus an extra uncommitted delta" → UNATTRIBUTABLE) plus the trailer-missing and own-trailer cases. Verified today: git 2.34.1 renders `%(trailers:key=Claude-Session,valueonly)` correctly; the thermal session's prior commits on `renderer.py`/`sensor.py` carry the trailer. Resolved.
- **#18** CP0.1a/CP0.1b split; **#19** baseline + `frozen_files_at_baseline.diff` under `renderer_layout_redesign/v1_guard/`, committed; **#20** `Body Temperature` keyed `value` (matches working-tree `sensor.py:695`), `config_sha256` in `run_meta` extras, thirteen pinned signatures — every one checked against the working tree today and matching, including `draw_temperature_gauge(..., obs_temp=None)` and `draw_thermal_diamond(..., colour_offset=0.0)`; **#21** asset deferred, Q12 rewritten; **#22** map rows for all five new scripts + HTML "not a script" row + §1c test rows; **#23** `integration` (the only registered marker); **#24** `_worker_init` (correct name, `render_recordings.py:74`), patch `src.environment.renderer.save_jax_video` (correct: `_render_episode` imports it locally at `:93`), scratch output path; **#25** zero hits, comments included. All resolved.

**Freeze and name checks (asked)**

- Frozen nine: `git status` today shows `renderer.py`, `renderer_v2.py`, `sensor.py`, `evaluation_core.py` dirty (thermal session) and the other five clean — exactly what §D5.4 records. Phases 0–4 only *execute* or *import* frozen files (`record-frames` runs `_worker_init`/`_render_episode`; `--benchmark` calls `render_jax_state`; the isolation test runs V1's script on a fixture dir); none edits one. The V2 entry point has no `--cleanup-per-episode`, so it cannot delete.
- `render_recordings_v2.py`, `videos_v2/`, `v1_path_guard.py`, `episode_viewer.*`, `make_render_fixture_recordings.py`, `render_layout_audit.py`, `src/environment/dashboard/`, and the eight new test files: none exists on disk and none is referenced by any tracked file. Every production caller (`async_render.py:120`, `evaluation_core.py:275`, `dreamer_srl/eval.py:547`, `render_recordings.py:179,234`) uses the literal `"videos"`, never a glob, so `videos_v2/` cannot be picked up by accident.

**Should be resolved before Phase 0 (Moderate)**

- 🟡 **CP-G cannot be passed while the thermal session holds uncommitted edits, and the plan gives the user no mechanical way to clear it.** §D5.4 says UNATTRIBUTABLE is "cleared only by the user, in writing, in the Implementation Report" and "exit code 0 only if there is no UNATTRIBUTABLE state"; CP-G says "`check` exits 0". UNATTRIBUTABLE is the *expected* state whenever the other session has an uncommitted delta on top of HEAD that differs from baseline — which is the working tree's normal condition while its plan is mid-flight (four files, 163 lines dirty today). A phase boundary that lands in that window has an unsatisfiable checkpoint. Fix: an `accept <path> <sha256>` subcommand run by the user, writing `user_accepted: [{path, sha256, date}]` into `baseline.json`; `check` reports that exact content as **ACCEPTED** (PASS-equivalent) and re-flags any different content. This is not a re-baseline: it is user-authored, pinned to one sha, and pasted into the report. CP-G then reads "exits 0; any ACCEPTED entries listed". — owner `senior-developer`
- 🟡 **The icon mapping is declared frozen but is invisible to the guard.** File Changes L477 and §D6 freeze `configs/visualization/default.yaml` `icons:`, yet it is not among the nine hashed files, and the frame hashes cannot see it either: `_worker_init` takes `icon_config` from the fixture's `run_meta.pkl` (`render_recordings.py:84–85`), pickled at generation time from `evaluation_core.py:277`. So the exact change Q12 defers (a `campfire` entry) would leave CP-G green while changing every new production video. Fix: add the file to the hashed set with the same three-state treatment. — owner `senior-developer`
- 🟡 **The "not observed" temperature path has no fixture.** §D1.1 and the blueprint (L610) specify `TEMP +4.19 not observed` for a world where body temperature is not observed, and CP2.5 checks it, but no matrix cell produces it: M4 takes the observed path (`campfire_world.yaml:364` `body_temp_observable: true`) and M7 has no `body_temp`. The thermal session has an **untracked** `campfire_world_body_temp_hidden.yaml` (`body_temp_observable: false` at `:375`) — do not depend on it; add an **M4b** cell as an in-memory override of M4 (the M6 pattern), labelled as such. — owner `senior-developer`
- 🟡 **Residual false-pass: ATTRIBUTED trusts `plan_sessions` to be complete, and filling it is procedural.** A developer session (or a later top-level session that resumes this plan) that skips `add-session` gets its own frozen-file commits ATTRIBUTED. Cheap mechanical tightening: any commit in `<plan_start>..HEAD` that touches a frozen file **and** any path this plan owns (`src/environment/dashboard/`, the five new scripts, the new tests, this doc, `v1_guard/`) is UNATTRIBUTABLE regardless of trailer; add that case to `test_v1_path_guard.py`. — owner `senior-developer`

**Low**

- 🟢 Fixture hashes will report **FIXTURE CHANGED** on every regeneration, even a byte-identical one: `.rec.gz` is written with `gzip.open(..., 'wb')` (`eval_recording.py:95`), whose header carries the write time. Hash the decompressed payload bytes instead.
- 🟢 `config_sha256` is a file-content hash; M5's `B_olfaction.yaml` has `extends: environment/experiment/basic/04-jump_attack_10x10`, so a parent edit would change "M5" silently. M1–M4 have no `extends:` (verified). Hash the resolved config (post-`extends`, e.g. sorted JSON of the loaded dict) or every file in the chain.
- 🟢 `frozen_files_at_baseline.diff` will commit ~163 lines of another session's unfinished code under `docs/`. Fine for reproducibility; put a one-line header in the file saying whose work-in-progress it snapshots and that it is not to be applied.

**Assumptions (this pass)**: archive configs M2/M3 load at current code — ❓ (plan has the M8/M9 substitution); Agg output byte-stable across processes — ❓ (plan has the tolerance fallback); no `location_sensor_enabled: true` config exists — verified, so M6's in-memory override applies; the user is available to `accept`/clear at phase boundaries — ❓ (the first Moderate makes this the gating dependency).

**Cost of being wrong**: no data-loss hazard and no training run at stake. The first Moderate costs a stalled phase boundary; the second lets the one config change the freeze most specifically forbids pass the guard unseen, changing production videos until someone notices by eye (reversible by a one-line revert). The third ships an untested painter path into the retirement-gate decision.

Reviewed by: plan-reviewer
