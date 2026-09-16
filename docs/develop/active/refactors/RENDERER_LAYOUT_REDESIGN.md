---
title: "Episode-video renderer redesign: panels that cannot overlap, a faster frame, and a step-scrubbing viewer"
topic: refactors
status: active
created: 2026-09-14
last_updated: 2026-09-16
supersedes: UI_REDESIGN_PROPOSAL.md
---

# Episode-video renderer redesign: panels that cannot overlap, a faster frame, and a step-scrubbing viewer

> **Status**: PLANNED. Revised three times after `plan-reviewer` (first and second pass NOT READY; third pass SOUND WITH CONCERNS, applied in Revision 3). Revision 4 adds extended-range senses (user scope, 2026-09-14); fourth pass SOUND WITH CONCERNS, applied in Revision 5. Revision 6 records user decisions (2026-09-14); fifth pass SOUND WITH CONCERNS, applied in Revision 7. Revision 8 adopts the visual design spec (`docs/reviews/design_episode_dashboard.md`). Revision 9 records the user's answers (2026-09-14) and corrects the temperature scale to a per-episode range. Revision 10 moves every verification world onto maintained configs (new config-maintenance rule). Revision 11 (2026-09-16) re-points every config path after another session archived 227 worlds, names where the regenerated campfire world's values are copied from, and records two new environment behaviours (bushes block animals; faster healing when resting in a bush). **Revision 12 (2026-09-16) retracts Revision 11 §2** — the claim that the maintained `basic/` configs fail to load was produced by a non-resolving YAML read; all of them load, and the plan now requires every config check to go through the resolving loader. **Revision 13 (2026-09-16) corrects the verification matrix after Phase 0b was built and verified**: the three real trained-policy cells cannot be rendered at current code, cells M1 and M2 turned out to be the same world, and a new cell M1x was added. Phase 0a and Phase 0b are **implemented**; Phases 1–5 are plan only.
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

## Revision 4 2026-09-14 (user scope: extended-range senses)

**Why.** The directional smell and vision senses shipped on 2026-08-21 accept any non-negative diamond radius: `config_loader.py` only rejects values below 0. Configs the project trains with today use smell radius 1 and vision radius 2. A radius-r diamond has `2r²+2r+1` cells, `2r+1` wide. In the ~306 px right column that is about 102 / 61 / 44 / 34 px per cell at r = 1/2/3/4, which is too small to carry 8 vision channels as per-cell bars from r = 2. The plan as written would have raised `LayoutOverflowError` on configs in use.

| Item | Status | Where |
|---|---|---|
| Wide sensor band under the grid view when a sense does not fit the side column; chosen once per config; canvas unchanged; fit-or-fail still guards | **Decided** | §D7.1, §D1.2 step 4 |
| Test the in-use configs (smell r1; vision r2 with blur off / anisotropic / isotropic, occlusion, presence value modes) plus synthetic r3 and r4 stress; document the largest range that fits; fail loudly above it | **Decided** | §D7.6, matrix cells E1–E9, CP2.7 |
| Encoding for r ≥ 2 (per-channel maps / dominant channel / bars-then-table) | **Open: Q13**, chosen after the examples on the artifact page | §D7.2; one swappable painter kind |
| Grid view shows each sense's footprint; colour scales not assumed to be [0,1]; panel subtitle states blur/mask/occlusion/value mode; true-vs-observed as a noise-error map at extended range; viewer values grouped by cell | Specified | §D7.3–D7.5, §D3 |
| V1 freeze | Unchanged: V1 draws these configs exactly as today | §D5.4 |

---

## Revision 5 2026-09-14 (after plan-reviewer fourth pass: SOUND WITH CONCERNS)

| # | Finding (short) | Handling |
|---|---|---|
| 🟡33 | Layout could depend on episode data | Layout and every `min_size` read only params + font metrics; scale labels are fixed-width; test that two episodes with different maxima give identical boxes (§D7.7, CP2.7). |
| 🟡34 | Two arena cell floors; fallback order implicit | Single `ARENA_CELL_MIN_PX = 32`. Explicit order: W from ranges → side column → band → shrink W toward `local_view_size` with clip caption → compact → raise. Minimap rectangle shows the W actually drawn (§D1.2, §D7.7). |
| 🟡35 | Largest radius recorded from the packer alone | r_max is recorded only after rendering and auditing a synthetic override at that r per encoding. Machine and fonts are named. Where the band was chosen, forcing the side column must raise (§D7.7, CP2.7). |
| 🟡36 | Noise at extended range untested | New cell **E2n**: E2 with noise on, with and without true observations. The error-map box is reserved from params and captioned "true obs not recorded" when true observations are absent (§D7.7). |
| 🟡37 | Terrain channels and labels assumed an 8-wide vision vector | Terrain := non-zero columns of `params.visual_background_property`; label table only when `visual_vector_size == 8`; A/B/C defined at V = 1; CP asserts E6's label is not `GRS` (§D7.7). |
| 🟡38 | Subtitle missing radial scale | `visual_blur_radial_scale` added (§D7.5). |
| 🟡39 | Override cells not marked | `synthetic: true` + `overrides` in fixture extras; printed at CP0.2 (§D5.1). |
| 🟢40–45 | Zero-maximum guard; B hides terrain under blur; cell order from the env's offset function; E9 turns vision off; legend chips and clip caption in the non-ellipsising text class; per-episode maximum from a setup pre-pass | §D7.7, matrix E9, Q13 |
| – | Proprioception now load-bearing | Every E cell and M5 observes it, so the completeness rule blocks CP2.7 until **Q5** is answered (noted in Q5). |

---

## Revision 6 2026-09-14 (user decisions)

| # | Decision | Where applied |
|---|---|---|
| 1 | **Q13 → option A**: small diamond map per channel (smell 5; vision 1 terrain map + one map per object channel), per-sense colour scale fixed per episode. The user chose it from Figure 5, which draws smell at **range 1** as maps. The plan previously kept per-cell bars at range 1, so this revision **applies A from range 1** (range 0 smell stays a spectrum; range 0 vision stays single-cell bars). **One-line confirmation for the user:** "Option A from range 1, as in Figure 5; bars only at range 0." | §D7.2, registry rows, Decided questions |
| 2 | **Q10 → show hidden internal states.** Every internal-state row shows **both** what the agent observes (or `not observed`) **and** the true value, for satiation, nutrition, injury, interoceptive nociception and body temperature. A hidden value is never captioned as observed. | §D1.1 rule, CP2.5 |
| 3 | **Grid view prints no temperature numbers.** The thermal underlay is colour only. | §D5.2 rule 10 |
| 4 | **Temperature colour scale fixed from params only**, identical for every episode of a config; never derived from the field | §D4.3, thermal test ports |
| 5 | **Q12 → a new asset file `assets/campfire.png`.** The shared icon mapping has no `campfire` key and V1's `_load_icons` loads only mapped keys (verified by the user's session), so adding the file leaves V1 videos unchanged. The mapping file stays frozen; the new renderer maps `campfire` internally. **V1 freeze intact.** | §D1.4, §D6, File Changes, retirement gate |
| 6 | CP0.1a said "nine frozen files"; the hashed set is ten | CP0.1a |
| 7 | **Design quality:** a `visual-design-reviewer` design spec is applied and its review passed before retirement | CP-D, retirement gate |

**Known gap surfaced by decision 2.**
- **The problem:** recordings do not store the true interoceptive-nociception value. `_snapshot_state` in the frozen `eval_recording.py` carries satiation, nutrition, injury and body temperature, but no nociception field.
- **Observed worlds:** the true value comes from the recorded noise-free observation when present.
- **Unobserved worlds, or no true observations recorded:** the true column reads `true not recorded`, and the value is never recomputed from injury history.
- **The fix:** add the field to the snapshot as a retirement-gate item, because the recorder is frozen until then.
- **Blueprint:** the ASCII blueprints predate decision 2. Their vitals rows are superseded by §D1.1 (both values on every row) and are not redrawn here.

---

## Revision 7 2026-09-14 (after plan-reviewer fifth pass: SOUND WITH CONCERNS)

| # | Finding (short) | Handling |
|---|---|---|
| 🟡46 | A span from absolute stamps misses ratio-mode heat (campfire fires reach ≈ +336) | §D4.3: bounds computed from the field construction in `core.py`, covering default-temperature corners, absolute stamps, `ratio_high · max\|default_temp\|`, spots, and additive merged fires when `thermal_min_fire_separation == 0`. Tested on ten M4 seeds. |
| 🟡47 | Symmetric linear scale washes out the cold world | §D4.3: two-slope diverging scale (vmin from params, setpoint as the neutral centre, vmax from params) with asymmetric ticks. `_thermal_rgba`, `draw_thermal_diamond` and `draw_temperature_gauge` are **copied** into the package, not imported. The exact ramp follows the `visual-design-reviewer` spec (in progress: `docs/reviews/design_episode_dashboard.md`). |
| 🟡48 | V1's `_load_icons` shares a process-global cache | The new renderer never calls it; a cache-free loader is copied into the package. Compat test: V1 M4 raw-frame hashes equal the baseline after an in-process V2 render. CP2.6 asserts campfire ink comes from an `AxesImage`. |
| 🟡49 | "No text in grid" collides with the glyph's letter code | Rule narrowed to **no numeric text** in the arena. The iconless glyph code is drawn as a vector path, not a `Text` artist. |
| 🟡50 | Interoceptive nociception's true column is a percept, not a state | Three-way rule via `real_available`. Presence = `interoceptive_nociception_enabled`. Column labelled **noise-free**. CP2.5 cells updated. |
| 🟢51 | Encoding A only | CP2.7 and its test row rewritten for A; the encoding-invariance test is dropped. |
| 🟢52 | Wording / Q14 scope | "r ≥ 1" throughout. Q14 names the affected cells (E1, M5: smell at range 1). New cell E1n adds noise at smell range 1. |
| 🟢53 | Stale pin; snapshot field | `thermal_color_limits` pin dropped. Phase 5 adds the noise-free `sense_interoceptive_nociception` scalar to the snapshot, never the buffer. |

---

## Revision 8 2026-09-14 (visual design spec adopted)

**What this adopts.** The `visual-design-reviewer` report [`docs/reviews/design_episode_dashboard.md`](../../../reviews/design_episode_dashboard.md) concluded that the layout is sound but the look is dated. Its **§Spec** (Canvas theme, Type, Palette, Spacing/radii/cards, Components, Icon style guide) is adopted **by reference** as the new renderer's visual specification; hex values, sizes and component drawings live there, not here. Where that spec and this plan's earlier visual wording differ, the spec wins, except for the rules below, which change behaviour or tests and so are restated here.

| # | Rule adopted | Plan impact |
|---|---|---|
| 1 | **Light theme for the video frame**: white cards on a green-grey canvas, no monospace anywhere. A deliberate departure from the house style sheet, **for the frame only** (artifact pages keep the house style). | §D1.3 styling follows the spec; CP-D judges against it. |
| 2 | **Font "Dashboard Sans Tab"**: Pretendard with tabular digits frozen into the cmap, so numbers do not jitter between frames. It is renamed because the OFL Reserved Font Name forbids "Pretendard" in a derived name. Vendored at `assets/fonts/dashboard_sans_tab/` with `OFL.txt` and a `README` (source version, the digit-freezing step, licence). New asset; V1 unaffected. | File Changes (Phase 2); `fit_text` measures with this font; the guard records the font file sha256 with the machine/font record (§D7.7 item 4). |
| 3 | **Flat icon set drawn from primitives**: creatures and food on white tokens, flat terrain, and a **composable agent marker** that replaces the `agent_*` combination images. Exported to a **new folder `assets/dashboard_icons/`**, plus `assets/campfire.png`. Existing `assets/*.png` are untouched and V1 is unaffected. **The new renderer draws its own glyphs/icons and does not load V1 icons** (supersedes Revision 7's copied cache-free loader of V1 icons). | §D1.4; File Changes; CP2.6 now checks `dashboard_icons` ink. |
| 4 | **Temperature norm: piecewise-linear `FuncNorm` with named anchors**, replacing the Revision 7 two-slope description. Normalised positions: vmin **0.00**, lower body limit **0.25**, setpoint **0.50**, upper body limit **0.58**, warm anchor **0.75**, fire anchor **0.88**, vmax **1.00**. Anchor temperatures come from config params: `min_temperature`, `temperature_setpoint`, `max_temperature`. Default rule: warm = **4×** and fire = **10×** the upper body limit, measured from the setpoint (Q16). vmin/vmax are the Revision 7 §D4.3 params bound. **Out-of-range field value → raise at build time** naming the cell and the bound (no fallback); clamp-and-outline is the alternative, Q15. | §D4.3 bullet replaced; thermal tests updated. |
| 5 | **Component rules that change behaviour or tests.** | See below. |
| 6 | The sketch figures on the artifact page are being re-drawn to this spec (docs folder only). | No plan change. |

**Rule 5 in detail:**
- **One shared temperature legend** in the thermoception card. No second legend under the grid view; the arena card keeps no scale strip.
- **"not observed" / "not recorded"** are drawn as text over an **outlined empty track** (no hatched fill). This supersedes Revision 6's hatched muted fill, and CP2.5 checks the outlined-track style.
- **One global noise note** (header or footer, e.g. "perceptual noise: off" / "on, true observations not recorded") replaces per-card "obs only" / "no noise" captions (§D4.2). Audit rule 7 is updated to look for the global note.
- **Option A maps:** value 0 = the track colour; the agent's own cell outlined in the agent colour.
- **One meaning per colour:** iris = agent only; orange = nociception only; blue↔red = temperature only; teal = smell; slate = vision. New **CP-C** pixel census.
- **Text floors:** **14 px** for anything read during playback, **12 px** for captions. These replace the 8 pt floor (`fit_text` minimum, audit rule 5).
- **CP-D** already requires a passed visual-design review before retirement; it now judges against this spec.

---

## Revision 9 2026-09-14 (user answers; temperature scale corrected)

**Answers recorded** (moved to Decided questions):

| Q | Answer |
|---|---|
| Q1 Stack | **A**: Matplotlib painters behind our own layout, figure built once, local server viewer. Pillow painters (B) are the fallback if Phase 0 misses the speed gate. |
| Q3 Canvas | **1440 × 896 px.** |
| Q5 Proprioception | **Draw a Proprioception panel**: six chips, one per action, with the previous action's chip highlighted in the agent colour. The registry row gains a `kind: action_chips` painter (min size = six measured chips at the 14 px floor). The completeness rule now finds an owner for `Proprioception`, which **unblocks the E cells and M5** (CP2.7 no longer blocked). |
| Q7 Viewer | **Local server only**; no static HTML export (§D3's export bullet is dropped from scope). |
| Q9 Speed gate | New renderer median frame time on the campfire world **≤ half of V1's**, and **not slower than V1** on any other world. Same lab node, same frames, same worker type. |
| Q11 Hiding-predator label | **Closed (moot).** The new design writes "Hiding predator" in full; there is no abbreviation. V1 keeps `DNG` (frozen). |
| Q14 Option A range | **Maps from range 1**; bars only at range 0. |
| Q15 Out-of-range temperature | **Clamp and outline** (no raise). See below. |
| Q16 Warm/fire anchors | **Withdrawn (moot)** with the per-config bound. |

**Temperature scale: correction of Revisions 6–8.** The user clarified that "fixed" meant **shared by every step of an episode**, not a per-config bound. Therefore:

1. **Range.** `vmin`/`vmax` come from a setup pre-pass over the episode's thermal field at **every step** (min and max across all steps). They are constant for the whole video. The setpoint stays the neutral centre: the range is widened to include `temperature_setpoint` if the field lies entirely on one side of it. If the resulting range is degenerate (`vmin == vmax`), it becomes setpoint ± 1 °.
2. **Removed:**
   - the Revision 7 per-config params bound (§D4.3 "How it is computed");
   - the ten-seed bound test and the `thermal_min_fire_separation: 0` override test;
   - the Q16 anchor rules;
   - the Revision 8 default "raise on out-of-range".
3. **Safety behaviour (Q15 = clamp and outline).** Any value outside the episode range has its colour clamped to the scale end, and its element gets a thin outline in the ink colour. This cannot happen for the episode's own field, by construction. It applies e.g. to the body-temperature gauge when body temperature leaves the field's range. No raise.
4. **Consequence, stated for readers.** Colours are comparable **within an episode**, not across episodes of different worlds. The shared legend in the thermoception card prints the episode's numeric range so a viewer never compares colours across videos blindly.
5. **Concatenated videos.** `render_recordings_v2.py --concat` runs the pre-pass over **all episodes being concatenated** and uses that one shared range for every frame, so frames in one MP4 stay comparable. Per-episode MP4s written in the same run use the same shared range, so a per-episode file matches its segment of the concatenated file. `layout_signature()` is unaffected: the range is paint-time data, never layout input (§D7.7 item 1).
6. **Single-frame wrapper.** Uses that frame's field and says so.
7. **Colour spread inside the range: decided (Q17, 2026-09-14): neutral setpoint with a pale survivable band.**
   - **Anchors,** a piecewise-linear norm in order: episode minimum (cold end), lower body limit `min_temperature`, setpoint `temperature_setpoint` (near-white), upper body limit `max_temperature`, episode maximum (hot end).
   - **Ramp shape.** Between the two body limits the ramp stays pale. Colour deepens only beyond them: blue toward the episode's coldest cell, red toward its hottest. Colours are the design review's temperature ramp, with its warm/fire anchors removed.
   - **Edge case.** If the episode range does not reach a body limit on one side (e.g. the episode maximum is below `max_temperature`), that side's body-limit anchor is **dropped**, and the pale segment runs to the episode end on that side. If neither limit is reached, the whole ramp stays within the pale band. Anchors stay strictly increasing by construction; coincident anchors are merged.
   - **Legend.** Ticks the episode minimum, the episode maximum, and each body limit that lies inside the range.
   - **Tests** (added to item 8): each anchor maps to its colour; the one-sided-range case drops the anchor without error; legend ticks match.
8. **Tests (replacing the Revision 6–8 thermal test list).**
   - The cooling-world arena crop is byte-identical across steps.
   - `vmin`/`vmax` equal the min/max over all steps of the recorded field (pre-pass correctness, checked against a direct numpy min/max).
   - The setpoint maps to the neutral colour.
   - A concatenated two-episode render uses the union range, and each episode's frames are identical to its segment.
   - A doctored body temperature beyond the range renders clamped with an outline and no exception.
   - The pre-thermal recording still renders.
   - Mutation: per-step range recomputation turns the cooling-world test red.

---

## Revision 10 2026-09-14 (config-maintenance rule)

**Why.** A new project rule (CLAUDE.md, "Config maintenance scope") says only `configs/environment/default.yaml` and `configs/environment/experiment/basic/` are maintained. Everything else under `configs/environment/experiment/` is archive, deliberately **not** kept loadable, and must not gate CI or a merge. A session needing an archived world regenerates a current-schema version instead. This plan's verification matrix pointed at several archived configs, so every cell is re-sourced below. **No user question is needed.**

**Rules for every generated cell.**
- **Sources.** A cell loads only `default.yaml` or a `basic/` config, then applies an **in-memory override**, recorded as `synthetic: true` + `overrides` in the fixture `run_meta` extras (§D5.1).
- **Parameter values.** Values reproducing an archived world (blur scale, occlusion strength, …) are copied from the archived YAML **as text**, never by loading it, and cited in `overrides_source` in the extras.
- **Regeneration.** A world that cannot be expressed as scalar overrides (e.g. new entity lists with temperatures) becomes a **regenerated current-schema config under `experiment/basic/`**, created by the developer and listed in File Changes.
- **Parameter names.** Key names such as the location-sensor switch are resolved against the current `default.yaml` at CP0.2.

| Cell | Old source (archived, not loadable by rule) | New source |
|---|---|---|
| M1 default | `default.yaml` | unchanged (maintained). Note: `default.yaml` now has interoceptive nociception **on**, so CP2.5's "disabled → no row" case uses **M1x**, an override of `default.yaml` with `interoceptive_nociception_enabled: false`. |
| M2 interoceptive nociception, noise off | `archive/hypervigilance/01-interoNocicept.yaml` | `default.yaml` (nociception on, noise off; confirmed at CP0.2), otherwise override |
| M3 interoceptive nociception + noise | `…/01-interoNocicept_noise.yaml` | `basic/05-sensory_noise_10x10.yaml`, with an override turning interoceptive nociception on if it is not already |
| M4 campfire thermal | `thermal/campfire_world.yaml` | **regenerated** current-schema `experiment/basic/<NN>-campfire_thermal_<size>.yaml`: campfire obstacle entries with temperature ratios, fire separation, thermal block. The name follows the folder's `NN-description_size` pattern; the developer picks the next free number. |
| M4b body temperature not observed | override of M4 | override of the regenerated M4 (`body_temp_observable: false`) |
| M5 directional smell | `sensory_directional/B_olfaction.yaml` | override of `default.yaml`: `olfactory_grid_range: 1` |
| M6 location sensor | grep of `configs/` | override of `default.yaml` turning the location sensor on |
| M6b noise on, true obs not recorded | M3 world | M3's new source, recorded with `--no-true-obs` |
| E1 smell r1 | `sensory_ladder/B_olf_only.yaml` | same as M5, with vision off |
| E1n smell r1 + noise | override of E1 | `basic/05-sensory_noise_10x10.yaml` + `olfactory_grid_range: 1` |
| E2 vision r2 sharp | `sensory_ladder/V5_sharp.yaml` | override of `default.yaml`: vision on, `visual_sensor_range: 2`, blur/occlusion off |
| E2n vision r2 + noise | override of E2 | `basic/05-sensory_noise_10x10.yaml` + the E2 overrides |
| E3 anisotropic blur | `sensory_ladder/V1_blur40.yaml` | E2 + `visual_blur_enabled: true` and the blur scale/floor/anisotropy values copied as text from `V1_blur40.yaml` |
| E4 isotropic blur | `sensory_ladder/P1_blur05_iso.yaml` | E2 + blur values copied from `P1_blur05_iso.yaml` (anisotropy 1.0) |
| E5 occlusion | `sensory_ladder/O3_occl_all.yaml` | E2 + `visual_occlusion_enabled: true` and cos/strength copied from `O3_occl_all.yaml`. If that world also needs per-entity occluder settings that are not scalar keys, it becomes a regenerated `experiment/basic/` config instead, recorded at CP0.2. |
| E6 presence modes | `sensory_ladder/Q1_presence_sum.yaml`, `Q2_presence_binary.yaml` | E2 + `visual_value_mode` values copied from those files |
| E7 / E8 / E9 synthetic r3 / r4 / smell-only r4 | overrides of archived-sourced E1/E2 | the same overrides, applied to the new E1/E2 |
| M7 / M8 / M9 trained-policy recordings | real recordings | **unchanged: kept as recordings.** They load through their own saved `run_meta.pkl` (pickled params), never through a config file, so the rule does not touch them. |

**Also withdrawn by this rule:** the archive-config "halt and substitute" branch in §D5.1/CP0.2 (there are no archive sources left).

> **Revision 11 path note (2026-09-16).** The "Old source" column above names the **pre-move** locations. Those files now live under `configs/environment/experiment/archive/` — `archive/thermal/campfire_world.yaml`, `archive/sensory_ladder/*.yaml`, `archive/sensory_directional/*.yaml`, `archive/hypervigilance/*.yaml`. They remain values-only references (copied as text, never loaded). The regenerated campfire config's sourcing is specified in Revision 11 §3. **Revision 12:** the cells routed to `basic/05-sensory_noise_10x10.yaml` (M3, M6b, E1n, E2n) keep that file as their base — Revision 11's "it does not load" fallback is retracted.

**Not verification inputs.** The artifact page's example episodes (the campfire world and `sensory_ladder` `V2_blur20`) are **sketches** generated from those configs at HEAD for illustration. They are not fixtures, are not re-sourced by this revision, and no checkpoint depends on them.

---

## Revision 11 2026-09-16 (the archive move landed; two new environment behaviours)

**What this revision is about, in plain words.** On 2026-09-15 another session changed the ground this plan stood on. It moved 227 experiment world configs into an `archive/` folder, so several file paths written into this plan no longer point at anything. It also changed two things about how the world itself behaves: a **bush now physically blocks animals** (previously it hid the agent without stopping anyone walking through), and **resting inside a bush can heal the agent faster** — a new setting that ships switched off, at a multiplier of 1.0, so nothing moves until someone raises it. This revision repoints every config path, states exactly where the plan's regenerated campfire world gets its numbers from (read once out of the archived file and typed into a new one — the archived file is never loaded when the renderer or its tests run), records what the two behaviour changes mean for the plan's fixtures and checkpoints, and notes for the record that the example episodes on the artifact page were made before all of this and are illustrations, not evidence. **No config is changed by this plan**, and nothing here needs a user decision.

**§1. Paths.** Archived worlds now live under `configs/environment/experiment/archive/<folder>/` — `thermal/`, `sensory_ladder/`, `sensory_directional/`, `hypervigilance/` and the rest. The §D5.1 matrix and the Revision 10 mapping table are updated to those real paths, and every archived entry is now explicitly marked **values-only**: the plan copies numbers out of it as text (Revision 10's rule) and never loads it. Per CLAUDE.md the archive is deliberately **not** kept loadable, is not migrated, and must not gate anything in this plan. The ~140 tests in nine modules that still load the archived campfire world (2026-09-15 diary, open item 2) are **not this plan's to resolve**; the plan's only obligation is that nothing it creates adds to that dependency.

**§2. ~~The maintained set does not load right now.~~ RETRACTED IN FULL by Revision 12 (2026-09-16) — do not act on this section.** It claimed that all seven `configs/environment/experiment/basic/*.yaml` fail to load and that only `default.yaml` loads, and concluded that `basic/` was not a safe base. **Every part of that is wrong.** The check behind it read the YAML directly without resolving `extends:`; all seven files have a top-level `extends:`, so the keys it reported as missing are inherited ones. See Revision 12 for the measurement that replaces it and for the loader rule that prevents a repeat. The one claim in Revision 11 that *was* a real load failure — archived `sensory_ladder/V2_blur20.yaml` — survives, for a different reason (§5, and Revision 12).

**§3. Where the regenerated campfire config's values come from.** `configs/environment/experiment/basic/<NN>-campfire_thermal_<size>.yaml` is authored against the current schema, with its values **inlined from `configs/environment/experiment/archive/thermal/campfire_world.yaml`, read once by the developer at authoring time** — the campfire obstacle entries, `temperature_ratio`, fire separation, the thermal block, `body_temp_observable: true`. After that single read the archived file is **not a runtime dependency** of the new renderer, the fixture generator, the layout audit, or any test: no fixture, checkpoint or test may name that path, and the new config must not `extends:` it. The new file must be **demonstrated to load** at current code before any cell uses it (CP0.2), which means carrying `sensory.visual_value_mode` and `body.recovery_in_bush_multiplier` — declared directly if the file is standalone, or inherited via `extends: environment/default`, since mappings deep-merge while lists are replaced wholesale (`src/utils/config.py:83`). Note the archived campfire world is deliberately a full standalone config with no `extends:`, so a copy of it would inherit nothing.

**§4. The two new environment behaviours, and what must account for them.**

- **Bushes block animals** (`02be34ae`; `blocks_animals: true` in `default.yaml` and in `basic/01`–`03`). This changes recorded worlds: an episode generated after this commit has different animal trajectories from anything recorded before it, even at the same seed. Three plan consequences. (a) The frame and fixture hashes taken at **CP0.1b** must be recorded from fixtures generated **after** this commit — a fixture made earlier would read as `FIXTURE CHANGED` at the first `check`. (b) Cells **M7–M9** are trained-policy recordings made before the change; they stay valid as *layout* inputs because they load through their own pickled `run_meta` params rather than a config file, but they must not be treated as the same world as a freshly generated cell, and §D5.1's existing "M8/M9 substitute for M2/M3" fallback now substitutes a **pre-change** world — record that when it is used. (c) The regenerated campfire config declares its own `obstacles:` list, which replaces the inherited one wholesale, so **every** entry in it must state `blocks_animals` explicitly (the archived source has `blocks_animals: false` on its bush, which is the pre-change value and must not be copied blindly).
- **`body.recovery_in_bush_multiplier`** (`761f427f`; mandatory key, inert at 1.0, at `configs/environment/default.yaml:192`). Under the no-fallback rule a missing key is a load error, which is exactly how archived `V2_blur20.yaml` fails today. So **any config file this plan creates must carry it** — directly if standalone, or by inheriting from `default.yaml`. Cells built as in-memory overrides of `default.yaml` inherit it and need no action.
- **Neither behaviour affects a panel.** Bush blocking is arena-entity movement; the recovery multiplier is inert and changes no observation. The panel registry (§D1.1), the packer (§D1.2), the §D5.2 overlap audit and the CP-C colour rules are unchanged, and no new panel, row or caption is required.

**§5. The artifact page's example episodes are sketches, not verification inputs** <!-- Revision 12: this section stands; V2_blur20's load failure is real (stand-alone config, no `extends:`). -->
 — reaffirming Revision 10 with a date. They were rendered from the campfire world and `sensory_ladder/V2_blur20` **before** the bush-blocking change, before the recovery key, and before the archive move, so they depict pre-change worlds at paths that have since moved. They are not fixtures, no checkpoint depends on them, and this plan does not regenerate them. That `V2_blur20` no longer loads at current code is therefore harmless.

---

## Revision 12 2026-09-16 (retraction: the maintained configs load fine)

**What this revision is about, in plain words.** Revision 12 takes back a factual claim Revision 11 made a few hours earlier. Revision 11 said the project's seven maintained world configs — the `basic/` curriculum files — could no longer be loaded, and rebuilt part of the plan around that. **That was wrong, and it is retracted in full.** All seven load cleanly. The error came from *how* they were checked: the check read each YAML file directly, and a direct read does not follow the `extends:` line at the top of the file that pulls in the shared base config. Every one of the seven has such a line, so keys they legitimately inherit looked missing. This revision restores `basic/` as a valid base for fixture worlds, and adds a rule that any config check in this plan must go through the loader that resolves inheritance — the same one the trainer uses — so nobody repeats the mistake.

**What was measured (2026-09-16, this session, CPU).** Every config was loaded through the trainer's own path, `load_env_params(load_env_config(path))` (`src/environment/config_loader.py:78`, `:1391`; used by `train.py:581`, `:202`):

| Config | Result |
|---|---|
| `configs/environment/default.yaml` | loads |
| all seven `configs/environment/experiment/basic/*.yaml` | **load** |
| `configs/environment/experiment/archive/thermal/campfire_world.yaml` | loads (stand-alone, carries the keys) |
| `configs/environment/experiment/archive/sensory_ladder/V2_blur20.yaml` | **fails** — `body.recovery_in_bush_multiplier` missing; stand-alone, no `extends:` to inherit it from |

Inheritance shape, for the record: `00`, `01`, `02` and `03-random_init_10x10` extend `environment/default`; `03-random_init_10x10_ckpt1k` and `04-jump_attack_10x10` extend `03-random_init_10x10`; `05-sensory_noise_10x10` extends `04-jump_attack_10x10`.

**The rule this revision adds (binding on §D5 and every checkpoint).** Any config load check in this plan MUST use the resolving loader `load_env_params(load_env_config(path))` and MUST NOT use raw `yaml.safe_load` or `Config(yaml.safe_load(...))`. A non-resolving read silently drops every inherited layer and turns an inherited mandatory key into a false "required but missing" — which, given the project's no-fallback rule, looks exactly like a real strict-config failure. This is not a new hazard: it is the already-**fixed** KNOWN_BUGS row *"Config inheritance ignored"* (`22c73bac`, write-up [`EXTENDS_NOT_RESOLVED_IN_TRAINING`](../../archive/EXTENDS_NOT_RESOLVED_IN_TRAINING.md)), where the trainer itself had the same defect. Revision 11 reproduced the fixed bug in a *checking* tool, which is why the plan states the rule rather than trusting a habit. The rule is also stated inline at §D5.1 and enforced as a `Fails if:` at CP0.2.

**What changed in the plan.**
- Revision 11 **§2 is struck through and marked RETRACTED IN FULL**; it is left in place, not deleted, because it was committed (`0cba8eb0`) and a future reader who finds that claim must be able to see it was withdrawn and why.
- `configs/environment/experiment/basic/` is **restored as a valid base** for any fixture cell. The §D5.1 matrix keeps `default.yaml` + in-memory overrides wherever Revision 10 independently preferred expressing a one-key variation as an override rather than a new file — that preference stands on its own and was never about loading.
- **M3 goes back to `basic/05-sensory_noise_10x10.yaml`** as its base (with the nociception override), as Revision 10 specified; M6b, E1n and E2n follow M3. The Revision 10 mapping-table note is corrected the same way.
- CP0.2's loadability bullet now names the resolving loader and fails the checkpoint if a non-resolving read is used.

**What from Revision 11 survives unchanged.** The archived-path updates and the values-only rule (archived configs are read as text at authoring time, never loaded); `V2_blur20`'s failure, which is real but caused by it being stand-alone rather than by anything in the maintained set; the campfire config's sourcing (§3); the bush-refuge consequences (§4) — post-change fixtures at CP0.1b, M7–M9 flagged as pre-change worlds, explicit `blocks_animals` per obstacle entry, `recovery_in_bush_multiplier` required in any new standalone config; and the artifact-sketch note (§5).

**Noted, not adopted:** an untracked `configs/environment/experiment/basic/06-campfire_thermal_10x10.yaml` exists in the working tree (another session's uncommitted work). It extends `environment/default`, sets `blocks_animals: true` on its bush, and inherits the two mandatory keys — i.e. it already satisfies Revision 11 §3/§4. The plan does **not** depend on it: it is untracked, so the File Changes row still has the developer author the campfire config, who should adopt this file if it is committed by then rather than create a second one.

---

## Revision 13 2026-09-16 (after Phase 0b: three matrix cells were wrong)

**What this revision is about, in plain words.** Phase 0b built the thing that makes the rest of this plan checkable: a generator that records one saved episode per kind of world the new dashboard has to draw, and a "frame baseline" that pins exactly what the old renderer draws from three of those recordings, so any later accidental change to the old pipeline is caught immediately. Building it exposed three factual errors in the plan's own verification matrix, all found by running the code rather than by re-reading the plan.

1. **The three cells that use real trained agents cannot be drawn at all right now.** M7, M8 and M9 point at episode recordings saved by training runs from earlier in the year. Those runs predate the body-temperature system, so the saved settings object inside each recording has no temperature switch in it — and today's observation-layout function reads that switch without checking whether it exists. All three crash on load. The plan expected only real-world drift here; the reality is a hard blocker, and the plan's own fix for it (`_recording_flag`, §D4.1) is Phase 1 work. Full detail and consequences in the §D5.1 note.
2. **Cells M1 and M2 are the same world.** M2 was meant to be "the world where the internal damage signal is observed", as distinct from the plain default world. But the default world already switched that signal on, so M2 resolves to the identical config, records identical episodes, and produces identical frames. It is an alias, not a second test.
3. **The genuinely missing case was the opposite one**, and Phase 0b added it as **M1x**: the world with the internal damage signal switched *off*, which is what the dashboard's "show no row at all" behaviour needs a fixture for.

**What changes in the plan.** The §D5.1 matrix gains an M1x row, marks M7/M8/M9 blocked with a Phase 1 re-entry gate, strikes M9's "REAL differs from OBS" purpose (that recording saved no noise-free observations, so it never could have served it), and flags M2 as a duplicate. CP0.1b and CP0.2 record what was actually achieved versus what they asked for. Nothing about the architecture, the layout, or the later checkpoints changes.

**One environment fact worth stating plainly.** The regenerated campfire world (cell M4) is **not** behaviourally identical to the archived campfire world whose numbers it copies. Its observation is identical — the same 33 numbers in the same order — but its bushes block animals, where the archived world's did not. That is deliberate and correct (it is the project's current canonical setting), but it means M4's recorded animal movement, and therefore its rewards, differ from the archived world from the first step. M4 is a **post-bush-change** world. See the Phase 0b Verification Report.

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
- **Internal-state rows (decided 2026-09-14, Q10 = show).** Satiation, nutrition, injury, interoceptive nociception and body temperature each get a row **whenever the state exists** (body temperature: thermal on). Each row has two value columns:
  - **observed:** the observed value if the modality is in the breakdown, else the muted text `not observed`;
  - **true:** from the snapshot state, normalised as V1 does. **Interoceptive nociception is a percept, not a state (Revision 7).**
  - **Presence:** the row exists iff `interoceptive_nociception_enabled` (via `_recording_flag`).
  - **Second column:** labelled **noise-free** (not "true"), filled by a three-way rule using `real_available` (§D4.2):
    - noise off, or that modality's noise mode `None`: noise-free = observed;
    - noise on and `true_obs` recorded: the noise-free slice of `true_obs`;
    - noise on and `true_obs is None`: `true not recorded`.
  
  **Bar.** Solid fill = observed value with a tick at the true value when observed. When not observed, a hatched muted fill = true value and no tick. The observed column never shows a value for an unobserved modality.
  
  **Noise rule.** §D4.2's REAL-availability rule does **not** apply to internal-state rows: the true column is always present, so the vitals layout is fixed per config. `hidden_state` survives only as the painter style of an unobserved row.
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
| arena | arena | arena | – | always | square, ≥ `ARENA_CELL_MIN_PX` = 32 px/view cell (§D7.7); + scale strip when thermal on |
| action_badge | arena | action_badge | – | action recorded | pill text in arena title strip |
| olfactory | extero, or sensor band (§D7.1) | `grid_kind(olfactory_grid_range, 5)`: spectrum (r=0) / `channel_maps` (r≥1, decided) | `Olfaction` | name in breakdown | per kind (§D7.2) |
| extero_nociception | extero | intensity | `Extero Nociception` | name in breakdown | text row + bar |
| thermoception | extero | thermal_diamond | `Thermoception` | name in breakdown | `2r²+2r+1` numeric cells |
| collision | extero | cross_bars (r=1) / dir_grid | `Collision` | name in breakdown | 8 pt legend above bars |
| visual | extero, or sensor band (§D7.1) | `grid_kind(visual_sensor_range, visual_vector_size)`: single-cell bars (r=0) / `channel_maps` (r≥1, decided) | `Visual` | name in breakdown | per kind (§D7.2); 8 pt legend |
| proprioception | extero | `action_chips` (decided Q5, 2026-09-14): six chips, previous action highlighted in the agent colour | `Proprioception` | name in breakdown | six measured chips at the 14 px floor |

**Completeness rule.** At episode setup, every breakdown name must be owned by exactly one present entry, or be on an explicit "recorded, not displayed" list (only if Q5 chooses that). Otherwise setup raises `ValueError` naming the orphan. A future modality that reuses a kind is a registry entry only. A new kind adds a painter. Neither touches layout.

#### D1.2 Layout: a column packer, computed once per episode

1. **Canvas.** Fixed at **1440 × 896 px**, multiples of 16 so imageio does not resample (Q3). Header = measured line + padding.
2. **Columns.** Left 300, right 330, centre = remainder minus two 16 px gutters; module constants.
3. **Heights.** Per column, sum the present panels' min heights plus gaps. Leftover height goes to the grow panel: minimap (left), arena (centre, capped at square), and shared in proportion on the right.
4. **Fit-or-fail**, once per config, in the explicit order of §D7.7 item 3: grid-view width from the sensor ranges, then side column, then sensor band, then shrink the grid-view width with a clip caption, then `compact` min sizes, then raise. If a column still overflows, raise `LayoutOverflowError` with the panel demands **before any frame is drawn**. On the training path this fails only the render child: `async_render.py` isolates it, the recordings stay on disk, and the error is in the render log.
5. **Output.** `dict[key → Box]` in integer px; boxes disjoint by construction (CP1).

Stretchable/Taffy stays a possible later drop-in behind `Box`; it isn't needed for three stacked columns.

#### D1.3 Painting inside the box

- **Axes.** One `fig.add_axes(rect)` per panel, `clip_on=True`, layout engine `'none'`.
- **Card borders.** Drawn as a separate unfilled outline artist. Text may not touch it (§D5.2).
- **`fit_text(ax, text, box, max_px, min_px, numeric: bool)`** (Revision 8). Text uses the vendored "Dashboard Sans Tab" font and floors of **14 px** for playback text and **12 px** for captions, which replace the earlier 8 pt floor wherever "8 pt" appears below. It measures with `get_window_extent` and shrinks down to the floor.
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
    - *(Revision 7: `_load_icons`, `thermal_color_limits`, `_thermal_rgba`, `draw_temperature_gauge` and `draw_thermal_diamond` are **no longer imported**. The icon loader is copied cache-free, because V1's `_ICON_CACHE` is process-global. The three thermal helpers are copied onto the two-slope norm. None of them is pinned.)*
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
- **Icon set (Revision 8, supersedes the icon-file lookup below).**
  - **Source.** The new renderer draws every entity from its own flat icon set in `assets/dashboard_icons/`, drawn from primitives per the design spec §Icon style guide: creatures and food on white tokens, flat terrain. It does **not** load V1 icons or `icon_config` images.
  - **Agent.** A composable marker drawn over whatever occupies the cell replaces V1's `agent_*` combination images.
  - **Campfire.** `assets/campfire.png` joins the set.
  - **Fallback.** The glyph described below remains only for an entity name with no `dashboard_icons` entry.
- **Iconless entities (review finding 11).** For any obstacle, resource or animal whose icon key is missing from `icon_config` or whose file is absent, the arena draws a **deterministic glyph**: a filled rounded square in the entity's category colour, plus a centred 1–3 letter code derived from its name (e.g. `CF` for campfire), drawn as a vector path (`TextPath` → `PathPatch`) rather than a `Text` artist. The mapping lives in a small table in the painter module, with its own test that codes are unique across `params.obstacle_names`. This path is always needed because archived `icon_config` pickles lack keys added later. **Decided 2026-09-14 (Q12): a new asset `assets/campfire.png` is created.** The shared icon mapping (`configs/visualization/default.yaml`) has no `campfire` key and V1's `_load_icons` loads only mapped keys, so adding the file does not change V1 videos. The mapping stays frozen. The new renderer resolves `campfire` → `assets/campfire.png` through its own internal icon table. The glyph fallback remains for any other iconless entity and for a missing file.
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
  - `/api/values?ep=&t=` (JSON of every panel's `extract`, including `observed`/`hidden` flags, action, termination; grid senses grouped by cell per §D7.5).
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
- **When false:** no REAL slot and no tick. Revision 8 replaces per-card captions with **one global noise note** in the header or footer (e.g. `perceptual noise: off`, or `on; true observations not recorded`). Audit rule 7 checks the note's presence and its consistency with params.
- **Sub-epsilon differences:** never used to decide layout. Where REAL is shown and `|true − obs|` is below 1e-6, the tick sits on the fill end (12_renderer.md pitfall 4).
- **Concat check.** `render_recordings_v2.py --concat` asserts all episodes' `layout_signature()` are equal before concatenating, and fails otherwise.

#### D4.3 Thermal colour limits

> **Superseded by Revision 9 (2026-09-14).** The colour range is the **episode's** thermal-field min/max over all steps (for a concatenated video, over all concatenated episodes), with the setpoint kept neutral and clamp-and-outline for out-of-range values. The per-config params bound, the anchor rules and the raise-on-out-of-range text below are **withdrawn** and kept only as history. The authoritative rules and tests are in the Revision 9 note.

**Decided 2026-09-14: the scale comes from params only, never from the field, and is identical for every episode of a config.**

- **Where it lives.** A new `dashboard_thermal_limits(params)` in `src/environment/dashboard/`. V1's `thermal_color_limits` is frozen and keeps deriving from the field, so V1 and the new renderer may colour the same world differently; that is intended.
- **How it is computed (Revision 7).** The bounds follow the field construction in `src/environment/core.py`:
  - the raw field is the episode's default temperature, plus random spots (if `thermal_use_random_spots`), plus scatter-**added** entity heat;
  - each entity's heat is `absolute + ratio · |default_temp|` (`_entity_temperatures`), with ratio drawn from `[ratio_low, ratio_high]`;
  - a normalised Gaussian blur follows, a weighted average that cannot leave the raw field's range.
  
  So, over the corners `d ∈ {thermal_default_temp_low, thermal_default_temp_high}` with `D = max(|low|, |high|)`:
  - `vmax = max(d) + spot term + fire term`;
  - `vmin = min(d) + (negative spot and stamp terms, same rule)`.
  
  **Spot term:** `thermal_spot_temp` × the maximum overlap count implied by `thermal_spot_count` / `thermal_spot_size`. Conservative: count, unless CP0.2 shows spots do not add.
  
  **Fire term:** per slot, `c_i = absolute_i + max(ratio_high_i, ratio_low_i) · D`, for positive `c_i`, over obstacle and resource slots.
  - If `thermal_min_fire_separation > 0`, no two sources share a cell, so the term is `max_i c_i`.
  - If it is 0, sources can merge, so the term is `Σ_i c_i`.
  
  Finally, `vmin` and `vmax` are widened, if needed, to include `min_temperature` / `max_temperature`, so the body gauge shares the scale. The campfire world's fires (`temperature_ratio` [11, 13]) put fire cells near +336, and this bound covers them by construction.
- **Superseded by Revision 8: anchored piecewise-linear norm.**
  - **Mapping.** `matplotlib.colors.FuncNorm` with named anchors at normalised positions:
    - vmin 0.00 (params bound);
    - lower body limit 0.25 (`min_temperature`);
    - setpoint 0.50 (`temperature_setpoint`);
    - upper body limit 0.58 (`max_temperature`);
    - warm anchor 0.75;
    - fire anchor 0.88;
    - vmax 1.00 (params bound).
  - **Warm and fire default rule (Q16).** Warm = setpoint + 4 × (`max_temperature` − setpoint); fire = setpoint + 10 × (`max_temperature` − setpoint).
  - **Validity.** Anchors must be strictly increasing; a config where they are not raises at build time naming the anchors.
  - **Out of range.** A field value outside [vmin, vmax] raises at build time naming the cell and the bound (Q15 records the clamp-and-outline alternative).
  - **Colours and legend.** Anchor colours and the legend drawing come from the design spec (§Palette, §Components).
  - **Tests.** Each anchor temperature maps to its normalised position within 1e-6. A non-monotone anchor config raises. An out-of-range doctored field raises naming the cell.
  - The two-slope text below is kept for history only.
- **Two-slope diverging scale (Revision 7; superseded by Revision 8).**
  - **Mapping.** `matplotlib.colors.TwoSlopeNorm(vmin, vcenter=temperature_setpoint, vmax)`: the setpoint is the neutral colour, and each side uses its own slope. The cold side is not washed out by a large hot side, and the survivable band stays readable.
  - **Ticks.** Asymmetric, at `vmin`, `min_temperature`, setpoint, `max_temperature`, `vmax`.
  - **Copied helpers.** The copies of `_thermal_rgba`, `draw_thermal_diamond` and `draw_temperature_gauge` in `src/environment/dashboard/thermal.py` use this norm. The frozen V1 versions stay linear and are not imported.
  - **Ramp.** The exact colour ramp is whatever the `visual-design-reviewer` spec settles (in progress: `docs/reviews/design_episode_dashboard.md`); this plan fixes only the norm and the bounds.
- **Missing params.** Absent params on archived recordings are read via `_recording_flag`. A thermal recording missing any of these raises at setup, naming the field.
- **Setup check, not clipping.** If any recorded `thermal_field` value lies outside the limits, setup raises `ValueError` naming the config and the extreme value. Silent clipping would hide a config the formula does not cover. The field-construction formula is confirmed at CP0.2 against `thermal/IMPLEMENTATION_PLAN.md`.
- **Tests (ported and changed).**
  - `test_a_cooling_world_does_not_rescale_its_colours` still requires a byte-identical arena crop.
  - New `test_limits_identical_across_episodes`: **ten M4 seeds** give equal limits, and every recorded `thermal_field` value on all ten lies inside `[vmin, vmax]`. The same check runs on a `thermal_min_fire_separation: 0` in-memory override of M4, labelled synthetic.
  - New `test_two_slope_centre`: a cell at exactly `temperature_setpoint` maps to the neutral colour, and a cold cell at `vmin` maps to the cold end (not near-white).
  - New `test_limits_ignore_field_extremes`: a doctored field with a narrower range does not change the limits.
  - `test_a_recording_without_thermal_fields_still_renders` ported.
  - `test_render_honours_an_explicitly_pinned_clim` is **dropped**: there is no per-call clim argument.
  - Mutation M1 (derive limits from the field) must turn the two new tests red.
- **Grid view.** The underlay is colour only, with no numbers in cells (§D5.2 rule 10). Thermoception's own pod still prints its relative readings, because that pod is not the grid view.

### D5. Verification that detects failure

#### D5.1 Real recordings across a config matrix

> **Revision 10:** every "Source" in the tables below that points outside `configs/environment/default.yaml` or `configs/environment/experiment/basic/` is replaced per the Revision 10 mapping table: in-memory overrides of maintained configs, or a regenerated `basic/` config for the campfire world. Trained-policy recordings M7–M9 are unchanged.
>
> **Revision 11:** the archived paths in the "Old source" column below are updated to where those files actually live now (`configs/environment/experiment/archive/…`) and are marked **values-only** — the plan copies numbers out of them as text and never loads them.
>
> **Revision 12 (2026-09-16):** Revision 11's claim that `basic/` configs do not load is **retracted** — they all load. `configs/environment/experiment/basic/` is a valid base for any cell. Where the table still says `default.yaml` + in-memory overrides, that is Revision 10's own preference for expressing a one-key variation as an override rather than a new file, **not** a workaround for a loading failure.
>
> **Loader rule (Revision 12, binding on every check in §D5 and the checkpoints):** any config load check MUST use the resolving loader — `load_env_params(load_env_config(path))` (`src/environment/config_loader.py:78`, `:1391`), the trainer's own path — and **never** raw `yaml.safe_load`. A raw read does not resolve `extends:`, so a config that inherits a mandatory key reports a false "required but missing". That is exactly how Revision 11 §2's wrong claim was produced, and it is the already-FIXED KNOWN_BUGS row "Config inheritance ignored" (commit `22c73bac`; [`EXTENDS_NOT_RESOLVED_IN_TRAINING`](../../archive/EXTENDS_NOT_RESOLVED_IN_TRAINING.md)) recurring in a checking tool instead of in the trainer.

`scripts/eval/make_render_fixture_recordings.py` steps the **real environment** with a **seeded random policy**. It writes through the **production** `EpisodeRecorder` / `write_run_meta`, with `true_obs` from `get_observation(state, params, apply_noise=False)`, to `results/render_audit/recordings/<cell>/<cell>/` (gitignored; unique leaf names avoid the output-path collision in wiki `render_recordings_output_path_collision`). Each cell's `run_meta` `extras` records `config_path` plus two hashes: `config_sha256`, over the **resolved** config after `extends:` layering, serialised as sorted-key JSON; and `config_chain_sha256`, a map of every file in the `extends` chain to its content sha256. Both are taken at generation time. Override cells (M4b, M6 if overridden, E2n, E7–E9) also record `synthetic: true` and `overrides` (the exact key → value map applied in memory); real-config cells record `synthetic: false`. If the other session edits a config later, "M4" visibly means something different rather than silently changing. Real trained-policy recordings are added as further cells.

| Cell | World (plain description) | Source — **Revision 11**: what the generator loads, plus (in italics) the archived file whose values are copied as text and never loaded |
|---|---|---|
| M1 default | Default world, spectrum smell, noise off | `configs/environment/default.yaml` |
| **M1x** nociception disabled (**added Revision 13**) | Default world with interoceptive nociception switched OFF, so the dashboard's "no nociception row at all" case has a fixture | in-memory override of `default.yaml`: `sensory.interoceptive_nociception_enabled: false`, labelled synthetic. **Why it exists:** `default.yaml` now ships interoceptive nociception ON, so M1 is *not* the disabled case CP2.5's three-way rule needs. Measured breakdown 26 dims with no `Interoceptive Nociception` entry |
| M2 interoceptive nociception | Interoceptive nociception observed, noise off | `configs/environment/default.yaml` (nociception on, noise off; confirmed at CP0.2), otherwise an in-memory override of it. *Values-only reference: `configs/environment/experiment/archive/hypervigilance/01-interoNocicept.yaml`* <br>**Revision 13 — M2 is now a byte-for-byte duplicate of M1 and adds no coverage.** Since `default.yaml` already ships nociception on and noise off, M2 resolves to M1's exact config (same resolved-config sha256), the generator writes identical episode payloads from the same seed, and the two cells' eight pinned V1 frame hashes are identical. Keep it only as a named alias for the matrix's "nociception observed" requirement; **do not read a passing M2 as independent evidence**, and do not count it as a second frame-baseline cell |
| M3 interoceptive nociception + noise | Same with perceptual noise on | `configs/environment/experiment/basic/05-sensory_noise_10x10.yaml` (loads cleanly — verified Revision 12), with an override turning interoceptive nociception on if it is not already. *Values-only reference: `configs/environment/experiment/archive/hypervigilance/01-interoNocicept_noise.yaml`* |
| M4 thermal | Campfire temperature world; observation lacks Nutrition/Injury and includes Body Temperature | **regenerated** `configs/environment/experiment/basic/<NN>-campfire_thermal_<size>.yaml`, authored against the current schema and proven to load. *Values-only reference, read once at authoring time: `configs/environment/experiment/archive/thermal/campfire_world.yaml`* (Revision 11 §3) |
| M4b thermal, body temperature not observed | M4 with body temperature removed from the observation, so the temperature row takes the "not observed" path | **in-memory** override of M4 (`body_temp_observable: false`) labelled as such in the report; no config file written or read beyond M4's |
| M5 directional smell | Olfaction as a directional grid | in-memory override of `default.yaml`: `olfactory_grid_range: 1`. *Values-only reference: `configs/environment/experiment/archive/sensory_directional/B_olfaction.yaml`* |
| M6 location sensor | Location sensor on | **in-memory** override of M1 turning the location sensor on, labelled as such (no config file written); the key name is resolved against the current `default.yaml` at CP0.2 |
| M6b noise on, true obs not recorded | M3's world recorded with `true_obs=None` | M3's source plus generator flag `--no-true-obs` (exercises the "true obs not recorded" caption) |
| E1 smell r1 | Directional smell, radius 1 | M5's source with vision off. *Values-only reference: `configs/environment/experiment/archive/sensory_ladder/B_olf_only.yaml`* |
| E1n smell r1 with noise | **Synthetic override**: E1 with perceptual noise on, recorded twice (with true observations; `--no-true-obs`) | in-memory override, labelled |
| E2 vision r2 sharp | Vision radius 2, no blur | in-memory override of `default.yaml`: vision on, `visual_sensor_range: 2`, blur/occlusion off. *Values-only reference: `configs/environment/experiment/archive/sensory_ladder/V5_sharp.yaml`* |
| E3 vision r2 anisotropic blur | Blur on, anisotropic | E2's override + `visual_blur_enabled: true` and blur scale/floor/anisotropy. *Values-only reference: `configs/environment/experiment/archive/sensory_ladder/V1_blur40.yaml`* |
| E4 vision r2 isotropic blur | Blur on, isotropic | E2's override + blur values with anisotropy 1.0. *Values-only reference: `configs/environment/experiment/archive/sensory_ladder/P1_blur05_iso.yaml`* |
| E5 vision r2 occlusion | Occlusion on | E2's override + `visual_occlusion_enabled: true` and cos/strength. *Values-only reference: `configs/environment/experiment/archive/sensory_ladder/O3_occl_all.yaml`*. If per-entity occluder settings are needed (not scalar keys), this becomes a second regenerated `basic/` config, recorded at CP0.2 |
| E6 vision r2 presence modes | Summed and binary presence values | E2's override + `visual_value_mode` values. *Values-only references: `configs/environment/experiment/archive/sensory_ladder/Q1_presence_sum.yaml`, `Q2_presence_binary.yaml`* |
| E2n vision r2 with noise | **Synthetic override**: E2 with perceptual noise on, recorded twice (with true observations; `--no-true-obs`) | in-memory override, labelled |
| E7 synthetic r3 | **Synthetic override**: E2 with vision and smell radius 3 | in-memory override, labelled |
| E8 synthetic r4 | **Synthetic override**: E2 with vision and smell radius 4 | in-memory override, labelled |
| E9 synthetic smell r4 only | **Synthetic override**: E1 with smell radius 4 and `visual_sensor_enabled: false` | in-memory override, labelled |
| M7 pre-thermal, trained | Real policy, recorded before the thermal system | `results/eval/noPredator_chasingRabbit/models/9520028/recordings/9520028/` — **BLOCKED at current code (Revision 13)** |
| M8 interoceptive nociception, trained, noise off | Real policy | e.g. `results/JAX_RecurrentPPO/20260501-005013_interoNocicept_predRange5_decoy75_std4/recordings/100049/` — **BLOCKED at current code (Revision 13)** |
| ~~M9 interoceptive nociception, trained, noise on~~ | ~~Real policy; REAL differs from OBS~~ | ~~`results/JAX_RecurrentPPO/20260501-050423_interoNocicept_predRange5_decoy75_std4_noise/recordings/100023/`~~ — **BLOCKED at current code, and it could never have served its stated purpose (Revision 13): the recording has no noise-free observations saved at all (`true_obs is None`), so there is no REAL slice to differ from OBS.** The matrix's noise-gap requirement is met by **M3** alone, measured largest OBS-vs-noise-free difference **1.4876** on episode 1 |

> **Revision 13 (2026-09-16) — all three trained-policy cells are unrenderable at current code, not just M7.** Each of the three saved runs predates the body-temperature system, so the `EnvParams` pickled inside its `run_meta.pkl` has no `thermal_enabled` field; the frozen `src/environment/sensor.py::get_observation_breakdown` (line 577) reads `params.thermal_enabled` unconditionally, and every one of M7, M8 and M9 dies there with `AttributeError: 'EnvParams' object has no attribute 'thermal_enabled'`. Independently reproduced by the verifier on all three. Two further facts the matrix had wrong: **M8 as well as M9 has `true_obs is None`**, so neither can show a noise-free comparison; and **M8/M9 snapshots carry `pred_pos` and `neutral_pos` where M7 and every generated cell carry `animal_pos`**, which is a second, separate compatibility gap that will surface as soon as the first one is fixed.
>
> **Consequence for the plan.** The CP0.2 clause "M7–M9 load; V1 renders step 0 of each" is **unsatisfiable until `_recording_flag` (§D4.1) lands in Phase 1**, and the frozen file may not be edited to work around it. M7 is therefore **out of the CP0.1b frame baseline** (which pins M1, M2 and M4 only), and M7/M8/M9 move to a **Phase 1 re-entry gate**: once `_recording_flag` exists, re-run the CP0.2 report on all three, confirm the `pred_pos`/`neutral_pos` snapshot shape renders, and only then add their frame hashes. Nothing in Phases 0–1 may depend on them.

M8/M9 do not depend on archived **configs** loading — but, per Revision 13, they do not load at all at current code, so the fallback "if M2/M3 cannot be generated, M8/M9 cover those cells" is **withdrawn**: M2 and M3 generate cleanly and M8/M9 cannot substitute for anything. About 20 more trained recordings exist under `results/JAX_RecurrentPPO/*/recordings/`, and every one recorded before the thermal system has the same blocker.

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
5. **Legibility floor (Revision 8).** Every playback text element's cap height corresponds to a font size ≥ 14 px, and every caption ≥ 12 px. Measured from a reference "0" rendered in the vendored font at those sizes, not from the painter's requested size. (V1 control frames are judged at the old 8 pt floor.)
6. **Presence (ground truth = breakdown).** For every name in `get_observation_breakdown(params)` not on the explicit not-displayed list (Q5), the report must contain foreground ink attributable to a panel for that name. The name → panel association is read from rendered text (the panel title string, matched against a fixed title table in the audit module), not from the registry.
7. **Observed-caption rule (ground truth = breakdown).** Any rendered text beginning `OBS` or `REAL`, or containing "obs only", must belong to a panel whose title maps to a breakdown name that is present. Any `hidden_state` row's text must contain "not observed".
8. **Vocabulary rule (V2 frames).** No rendered text matches `\bpain\b` (case-insensitive), and no legend contains `DNG`. V1 frames are exempt, because V1 is frozen and still shows `DNG`.
9. **Canvas.** No foreground ink in the outer 4 px margin; dimensions equal the declared canvas.
10. **No numbers in the grid view (decided 2026-09-14; narrowed in Revision 7).** No `Text` element whose string contains a digit or a sign character has ink inside the arena grid's extent. The title strip, legend chips and scale strip sit outside it. The iconless-entity code is drawn as a vector path (`TextPath` → `PathPatch`), not a `Text` artist, so this rule and the glyph cannot collide. Checked on every thermal cell.

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
- No `campfire` entry is added to `configs/visualization/default.yaml` `icons:` during Phases 0–4 (file frozen and hashed). The new asset `assets/campfire.png` is added and mapped inside the new renderer only (Q12, decided); V1 does not load unmapped files.

### D7. Extended-range senses (Revision 4)

**Plain summary.** Smell and vision can be configured to sense a diamond of cells around the agent of any radius. At radius 2 and above, a vision panel squeezed into the side column becomes unreadable. The new renderer therefore moves such senses into a wide band under the grid view. It shows them with an encoding the user will choose from examples, marks on the grid view which cells each sense covers, and refuses to render above the largest radius it can show legibly.

#### D7.1 Placement: side column or wide sensor band (decided)

- The packer evaluates two layouts, **once per config**, before any frame:
  - **(a) side-column:** the current blueprint;
  - **(b) sensor-band:** grid-view card on top of the centre+right area, a full-width band below it spanning the centre and right columns (≈ 1440 − 300 − 16 ≈ 1124 px wide), and the non-grid right pods (extero nociception, thermoception, collision, location) in a narrowed right strip beside the grid view.
- Layout (a) is used iff every grid-kind sense meets its `min_size` there; otherwise (b). The canvas stays 1440 × 896.
- If (b) also fails, `LayoutOverflowError` names the sense, its range and channel count, and the encoding. No squeezing.
- `layout_signature()` includes which layout was chosen, so a concatenated video can never switch mid-video.

#### D7.2 Encoding for range ≥ 2: one swappable painter kind (open, Q13)

**Registry.** The `olfactory` and `visual` entries get their `kind` from `grid_kind(range, channels)`:
- range 0 (smell only): `spectrum`;
- range 0 vision: single-cell bars;
- range ≥ 1: the single module constant `GRID_ENCODING`, **decided = `channel_maps` (option A), 2026-09-14**, applied from range 1 as in the user's chosen Figure 5 (pending one-line confirmation, Q14). B and C remain implemented behind the same interface only if the developer needs them for the Figure 5 comparison page; otherwise they are dropped from Phase 2.

`GRID_ENCODING` is one of three painter kinds with the same `build`/`update`/`min_size` interface, so the Q13 choice changes one constant and touches no layout code. It is a module constant, not a config key (§D6). Terrain/entity channel split, labels, the V = 1 case, B's behaviour under blur and cell order are defined in §D7.7 and override the table below where they differ.

| Kind | What a frame shows | Channel handling | Min size driver |
|---|---|---|---|
| **A `channel_maps`** | One small diamond map per channel. Smell: 5 maps (FOOD, AN-A, AN-B, BUSH, TREE). Vision: 1 terrain map + 5 entity maps. | Vision terrain map is categorical (which of GRS/SND/PLN is present per cell), because GRS reads 1.0 in every in-bounds cell and a per-channel GRS map carries no information. Entity maps: FOD, HPR, PRD, RCK, NEU. One colour scale per sense, fixed per episode (§D7.4). | maps × (2r+1) × min cell px (≥ 10 px) + titles |
| **B `dominant_channel`** | One diamond. Cell colour = strongest channel, brightness = its value; legend of channel colours. | Terrain channels excluded from "strongest" unless no entity channel is non-zero in that cell (then the terrain type colour, dimmed). Ties broken by fixed channel order, stated in the legend. | (2r+1) × min cell px (≥ 16 px) + legend |
| **C `bars_then_table`** | Per-cell bars up to r = 1; above that a heat table with one column per cell (cells ordered ring by ring, outward from the centre, with ring separators) and one row per channel. | All channels shown, including terrain rows. | cells × min column px (≥ 12 px) by channels × min row px (≥ 10 px) + labels |

#### D7.3 Grid view window and sensor footprints

- **Window.** The new renderer's grid view shows `W = max(params.local_view_size, 2·max_range + 1)` cells, where `max_range` is the largest diamond radius among the present senses. This is a rendering choice only; environment params are not changed. With `local_view_size = 5` (the in-use configs), vision r2 needs 5, so nothing changes. Synthetic r3/r4 widen the view to 7/9.
- **Cell-size floor.** If `W` would push arena cells below `ARENA_CELL_MIN_PX` (32 px, the single floor in §D7.7), `W` is capped at the largest value keeping 32 px. The footprint outline is then clipped at the window edge, and the card caption says `footprint exceeds view (r=<r>)`. The audit checks that caption's presence whenever clipping occurs.
- **Footprint outline.** Each directional sense draws its diamond footprint on the grid view as a thin outline in its sense colour (smell, vision, thermoception, and collision when r > 1). The outlines are foreground artists, and a legend chip in the arena title strip names each outline. A frame test checks outline ink along the expected diamond boundary cells.

#### D7.4 Colour and bar scales are not [0,1]

- Under `visual_value_mode` / olfactory value modes that sum (smell readings of 1.40 have been observed), values can exceed 1.
- Each sense's scale is fixed **per episode** at setup: `[0, max(true, observed over the whole episode for that sense)]`, rounded up to a 2-significant-figure tick. It is printed on the panel, the same principle as `thermal_clim`. Bars use the same maximum.
- Negative observed values (noise) are clipped for colour, and a small "clipped" tick counter is shown in the subtitle.
- The single-frame wrapper uses that frame's maximum and says so.

#### D7.5 Subtitles, true-vs-observed, viewer

- **Subtitle.** Each grid panel shows one subtitle line built from params via `_recording_flag`:
  - `range r · blur <off | aniso scale k, σ-floor f, ρ a | iso scale k, σ-floor f>` (`visual_blur_enabled`, `visual_blur_radial_scale`, `visual_blur_sigma_floor`, `visual_blur_anisotropy`; isotropic iff anisotropy == 1.0);
  - `mask <on|off>` (any non-zero in `res_visual_mask`/`animal_visual_mask`/`obs_visual_mask`);
  - `occlusion <off | cos c, strength s>`;
  - `values <mode>` (`visual_value_mode`).
  
  Smell shows the analogous fields that exist on params; the list is resolved at CP0.2 from `EnvParams`. Numeric text, so it never ellipsises (§D1.3). If it cannot fit, it wraps to a second line inside the min size.
- **True vs observed at range ≥ 2.** No ghost bars. When `real_available` (§D4.2), the panel adds one **noise-error map**: a diamond of `observed − true` per cell. It takes the strongest-magnitude channel for B, one per channel group for A, and an error row block for C. It uses a diverging scale symmetric about 0, fixed per episode. At r ≤ 1 the existing REAL tick on bars stays.
- **Viewer.** `/api/values` groups grid senses by cell: `{sense: {cell_index: {offset: [dr, dc], channels: {name: {obs, true}}}}}`. The page's values table renders one row per cell with channel columns.

#### D7.6 Support scope and the largest range that fits (decided)

- **In-use configs** are tested as real recordings (matrix cells E1–E6 below).
- **Synthetic stress.** In-memory overrides of the sharp-vision config set both radii to 3 (E7) and to 4 (E8), and a smell-only r4 (E9), each labelled "synthetic override" in the report.
- **Largest fitting range.** For each encoding kind, `tests/env/test_dashboard_extended_range.py` computes the largest r at which the packer fits (vision 8 channels + smell 5 channels together, and each alone) in layout (b). It asserts that r+1 raises `LayoutOverflowError` naming sense and range. The resulting numbers are written into the Implementation Report and `docs/environment/12_renderer.md`. **No estimate is promised here**; they are measured. §D7.7 tightens the recording procedure.

#### D7.7 Refinements (Revision 5)

1. **Layout never reads episode data (33).**
   - `RenderContext` is split. `LayoutContext` holds params, icon config, canvas and font metrics; `EpisodeContext` holds snapshot 0, `thermal_clim`, sense scales and the error-map scale.
   - `layout.py` and every `min_size` accept only `LayoutContext`, and a test inspects their signatures. `real_available` is derived from params, so it may be used in layout.
   - Scale labels are fixed-width, sized from the widest template string in the numeric format (e.g. `888.8`), never from the actual maximum.
   - **Test:** two episodes of one run with different sense maxima yield identical boxes and identical `layout_signature()`.
2. **Per-episode scale maximum (45, 40).**
   - Computed in `EpisodeRenderer` setup by a pre-pass over the whole payload (`obs` and, when present, `true_obs`) before frame 0.
   - **Zero guard:** if a sense's episode maximum is 0, the scale is `[0, 1]` with the caption `no signal this episode`, which avoids a divide-by-zero.
   - The single-frame wrapper uses that frame and says so.
3. **One arena cell floor and an explicit fallback order (34).**
   - `ARENA_CELL_MIN_PX = 32` is the only arena floor; it replaces both the 48 px in §D1.1 and the 32 px in §D7.3.
   - The packer tries, in order, and records which step succeeded in `layout_signature()`:
     1. `W = max(local_view_size, 2·max_range + 1)`;
     2. layout (a) side column;
     3. layout (b) sensor band;
     4. shrink `W` by 2 per step toward `local_view_size` (never below), with the `footprint exceeds view (r=…)` caption;
     5. `compact` min sizes;
     6. raise `LayoutOverflowError`.
   - The minimap's viewport rectangle outlines the `W × W` window actually drawn.
4. **Recording the largest radius (35).**
   - A candidate r_max from the packer is **rendered**: a synthetic override at r_max, per encoding, for smell + vision together and each alone. It passes the full §D5.2 audit before being recorded, and r_max + 1 raises.
   - Recorded with it: hostname, CPU model, Matplotlib version, FreeType version, and the resolved font family and font file path.
   - For every cell where the band layout was chosen, the test forces layout (a) and asserts `LayoutOverflowError`.
5. **Noise at extended range (36).** Cell **E2n** covers it (matrix).
   - The noise-error map's box is reserved iff `real_available` (params).
   - With `true_obs is None` the box stays, captioned `true obs not recorded`, with no map ink.
   - The audit checks both variants.
6. **Terrain, labels and V = 1 (37).**
   - **Channel split.** Terrain channels are the indices `j` where any row of `params.visual_background_property[:, j]` is non-zero; every other channel is an entity channel. This replaces the hard-coded GRS/SND/PLN.
   - **Labels.** The V2 label table (`HPR` etc.) applies only when `visual_vector_size == 8`; otherwise labels are `C0…C{V−1}`.
   - **At V = 1** (e.g. presence modes), all three encodings collapse the same way. A = one map; B = one brightness map (no channel colour); C = single-row table / single bar per cell.
   - **CP2.7** asserts E6's rendered channel label is not `GRS`.
7. **B under blur (41).** With blur on, entity values spread into neighbouring cells, so the "strongest channel" is almost always an entity and terrain colour is rarely visible in B. The B legend states `terrain hidden where any entity > 0`. Q13 repeats the caveat.
8. **Cell order (42).** Heat-table columns (C), per-cell value grouping (viewer) and noise-error cells follow the environment's own offset order: the sensor module's diamond-offset function (`get_visual_offsets`; exact name confirmed at CP0.2), imported read-only. They are never re-derived.
9. **Text classes (44).** Footprint legend chips and the `footprint exceeds view` caption are `fit_text` elements in the **non-ellipsising** class, because they carry names and ranges a reader relies on. They shrink to 8 pt, then raise.

### File Changes

**Frozen (not edited by any phase; see §D5.4):** `src/environment/renderer.py`, `scripts/eval/render_recordings.py`, `src/utils/async_render.py`, `src/utils/evaluation_core.py`, `src/algorithms/dreamer_srl/eval.py`, `src/utils/eval_recording.py`, `src/environment/sensor.py`, `scripts/eval/benchmark_render.py`, `src/environment/renderer_v2.py` (not edited, deleted or shadowed). `configs/visualization/default.yaml` is also frozen and hashed by the guard.

**Phase 0: guard baseline, fixtures, audit, spike**

| File | Change |
|---|---|
| `scripts/eval/v1_path_guard.py` (new) | `record-files` / `add-session` / `record-frames` / `check` (§D5.4). `record-files` is the first action of Phase 0; `record-frames` runs right after the fixture generator lands. |
| `docs/develop/active/refactors/renderer_layout_redesign/v1_guard/baseline.json`, `frozen_files_at_baseline.diff` (new, committed) | Guard baseline and the frozen files' uncommitted delta at record time. |
| `scripts/eval/make_render_fixture_recordings.py` (new) | Matrix generator (§D5.1): `--cells`, `--episodes`, `--max-steps`, `--seed`, `--no-true-obs`, `--out`. Uses `EpisodeRecorder`, `write_run_meta`, `get_observation` read-only; writes `config_path` + `config_sha256` into `run_meta` extras. **Revision 10:** loads only `default.yaml` or `experiment/basic/` configs and applies the cell's in-memory overrides from the Revision 10 table, recording `synthetic`, `overrides` and `overrides_source` in extras. It refuses (raises) any config path outside those two locations. |
| `configs/environment/experiment/basic/<NN>-campfire_thermal_<size>.yaml` (new, Revision 10; sourcing fixed in Revision 11) | Regenerated current-schema campfire temperature world for cell M4: thermal block on, campfire obstacle entries with temperature ratios, fire separation, `body_temp_observable: true`. **Where the values come from (Revision 11):** the developer opens `configs/environment/experiment/archive/thermal/campfire_world.yaml` **once**, at authoring time, and inlines its numbers into the new file as text. The archived file is **not** a runtime dependency of the new renderer, the generator, the audit or any test — no fixture, checkpoint or test may name that path, and the new file must not `extends:` it. The file must be **demonstrated to load** at current code (`load_env_params`), which requires `sensory.visual_value_mode` and `body.recovery_in_bush_multiplier` to be present — either declared directly or inherited via `extends: environment/default` (mappings deep-merge, lists replace wholesale: `src/utils/config.py:83`). Its `obstacles:` list replaces the inherited one, so every entry must state `blocks_animals` explicitly (Revision 11 §4). Validated by `env-config-reviewer` before use. No critical-settings registry value changes. If E5 needs per-entity occluder settings, a second regenerated `basic/` config is added the same way and listed here at CP0.2. |
| `scripts/eval/render_layout_audit.py` (new) | Audit (§D5.2); imports neither layout nor registry. |
| `tests/env/test_render_audit_controls.py` (new, `integration` marker) | Positive controls (D1, D2, D3, D10 on V1 M4; D6 and presence on dormant V2 M4); import-isolation test. Mutations added in Phase 2. |
| `tests/env/test_v1_path_guard.py` (new) | In a throwaway git repo under `tmp_path`, with a fake frozen file and plan session `S1`, the three states are exercised:<br>• PASS: untouched;<br>• ATTRIBUTED: foreign commit with trailer `S2` and no extra delta;<br>• UNATTRIBUTABLE: an uncommitted edit; a commit without a trailer; a commit with trailer `S1`; a foreign commit plus an extra uncommitted delta.<br>Also: frame hash altered with files PASS gives UNATTRIBUTABLE; fixture hash altered gives FIXTURE CHANGED; exit code non-zero on any UNATTRIBUTABLE.<br>Plus: a commit with foreign trailer `S2` touching both a frozen file and `src/environment/dashboard/` gives UNATTRIBUTABLE; `accept` of the current sha gives ACCEPTED, and a further edit to that file is flagged again. |
| `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` | Same change as the Phase 0 scripts:<br>• §3 rows for `v1_path_guard.py`, `make_render_fixture_recordings.py` and `render_layout_audit.py` (all hand-run, `scripts/eval/` root-depth note);<br>• §1c test-suite rows for `tests/env/test_render_audit_controls.py` (imports the audit and generator) and `tests/env/test_v1_path_guard.py` (imports the guard). |
| `tmp/<timestamp>_renderer_spike.md` | Spike numbers (spike code stays uncommitted scratch). |

**Phase 1: registry and packer**

| File | Change |
|---|---|
| **`src/environment/dashboard/`** (new package; name is Q2) | `__init__.py` exports `EpisodeRenderer`, `render_dashboard_frame`. `src/environment/renderer_v2.py` is **not touched** (frozen; its deletion is a retirement-gate step). |
| `tests/env/test_dashboard_v1_imports.py` (new) | Pins the imported V1 signatures listed in §D1.3. Revision 7 cache-isolation check: in one process, render a new-renderer M4 frame, then V1 M4 raw frames. The V1 hashes must equal the guard baseline, proving no shared icon cache or other process-global state. Asserts no `renderer_v2` module or package was created by this plan: `src/environment/renderer_v2/` does not exist, and `import src.environment.renderer_v2` still resolves to the `.py` file. |
| `src/environment/dashboard/panels.py` (new) | `PanelSpec`, `RenderContext`, `FrameInputs`, registry, completeness rule, observed-vs-hidden rule, `_recording_flag`, `real_available` from params. |
| `src/environment/dashboard/labels.py` (new) | V2-owned channel label table (`HPR` etc.) overriding adapter labels (§D1.3). |
| `src/environment/dashboard/layout.py` (new) | Column packer, `Box`, `LayoutOverflowError`, compact fallback; no Matplotlib import. |
| `tests/env/test_dashboard_layout.py` (new) | Boxes disjoint/inside canvas for all cells. Toggling a modality frees its height. Overflow raises. Unregistered name raises. **M4 context has no observed Nutrition/Injury rows.** `real_available` identical for two episodes of one run. `_recording_flag` import confinement. |

**Phase 2: painters and episode renderer**

| File | Change |
|---|---|
| `src/environment/dashboard/text_fit.py` (new) | `fit_text` with the numeric-raise / free-text-ellipsis split, logging. |
| `src/environment/dashboard/painters.py` (new) | One painter per kind with `build`/`update`, card outlines as separate artists, `gid`s, iconless-entity glyph table. Imports from `renderer.py` read-only only what §D1.3 still pins (`draw_boresight_diamond`, `save_jax_video`, `COLORS`). The icon loader (cache-free) and the thermal helpers (two-slope) are copied into `src/environment/dashboard/icons.py` and `thermal.py` (Revision 7). Any helper needing a change is **copied** into the package; **`renderer.py` is not edited** (frozen). |
| `src/environment/dashboard/episode.py` (new) | `EpisodeRenderer` (setup / `frame` / `close` / `layout_signature`), wrapper `render_dashboard_frame`. |
| `tests/env/test_dashboard_frames.py` (new, `integration` marker) | Audit clean on all cells' checked frames + stress variant. Mutations M-A..M-D fail as expected. Value-to-pixel, obstacle-ink (CP2.6), observed-caption (CP2.5) and vocabulary (CP2.4) checks. Glyph-code uniqueness. |
| `tests/env/test_dashboard_thermal.py` (new) | Thermal tests per the **Revision 9** note item 8: episode-range pre-pass, neutral setpoint, concatenated union range, clamp-and-outline, cooling-world crop, pre-thermal recording, per-step-recompute mutation. The Revision 6–8 params-bound tests are withdrawn. |
| `tests/env/test_dashboard_proprioception.py` (new, Revision 9) | E1 and M5 render a six-chip Proprioception panel. The highlighted chip equals the recorded previous action at a sample of steps, and highlight ink is the agent colour (CP-C). No chip is highlighted at step 0 if no previous action exists. |
| `assets/fonts/dashboard_sans_tab/` (new asset folder, Revision 8) | "Dashboard Sans Tab" font files (Pretendard with tabular digits frozen into the cmap; renamed per the OFL Reserved Font Name clause), `OFL.txt`, `README` (upstream version, exact freezing step, licence note). Loaded only by `src/environment/dashboard/`. V1 unaffected (CP-G frames). |
| `assets/dashboard_icons/` (new asset folder, Revision 8) | Flat icon set per the design spec §Icon style guide, including the composable agent marker. Existing `assets/*.png` untouched. Test: every entity name the matrix cells can place has an entry, or is listed as glyph-fallback. |
| `src/environment/dashboard/palette.py` (new, Revision 8) | Named colour tokens from the design spec §Palette, with a machine-readable colour → meaning map used by CP-C. |
| `assets/campfire.png` (new asset, decided Q12) | Campfire icon, RGBA PNG at the same pixel size as existing obstacle icons. Mapped only inside `src/environment/dashboard/`. Test: a V1 frame of M4 is byte-identical before and after the file is added (CP-G frames cover this). |
| `src/environment/dashboard/painters.py` (Revision 4 addition) | `grid_kind(range, channels)`, the `GRID_ENCODING` constant, the three grid painter kinds `channel_maps` / `dominant_channel` / `bars_then_table` with one interface, noise-error map, footprint outlines, per-episode sense scales, sensor subtitle. |
| `src/environment/dashboard/layout.py` (Revision 4 addition) | Side-column vs sensor-band layout selection (§D7.1); chosen layout in `layout_signature`. |
| `tests/env/test_dashboard_extended_range.py` (new, `integration` marker) | For the decided encoding A (`channel_maps`, r ≥ 1; Revision 7):<br>• E1–E9 and E1n render audit-clean;<br>• largest fitting r measured, and r+1 raises naming sense and range;<br>• footprint outline ink on the expected boundary;<br>• scale maximum ≥ the episode maximum (a 1.40 smell value is not clipped);<br>• subtitle text matches params for E2–E6;<br>• noise-error map present iff `real_available`;<br>• grid view `W` rule and clipping caption;<br>• Revision 5 additions:<br>&nbsp;&nbsp;– layout-input signature check and two-episode box identity;<br>&nbsp;&nbsp;– fallback-order step recorded;<br>&nbsp;&nbsp;– rendered and audited r_max with machine/font record;<br>&nbsp;&nbsp;– forced-side-column raise;<br>&nbsp;&nbsp;– E2n both variants;<br>&nbsp;&nbsp;– terrain split from `visual_background_property`;<br>&nbsp;&nbsp;– V = 1 rendering for A/B/C;<br>&nbsp;&nbsp;– E6 label not `GRS`;<br>&nbsp;&nbsp;– zero-maximum caption;<br>&nbsp;&nbsp;– B-under-blur legend text;<br>&nbsp;&nbsp;– offset order matches the env function;<br>&nbsp;&nbsp;– legend chips and clip caption raise rather than ellipsise. |
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
- CP-D passed (the `visual-design-reviewer` spec is applied and the second design review passes).
- The user has looked at `render_recordings_v2.py` output for one real training run's recordings.
- The speed gate is met.

The switch itself gets its own plan section and review. Expected steps:
1. Point `render_recordings.py` (or the three `src/` callers) at V2 by the mechanism the user picks. That is the first edit to a frozen file, and the plan section must say how archived recordings and saved run configs are handled.
2. Soak for one training cycle. A `LayoutOverflowError`/`TextFitError` on the training path fails only the render child.
3. Port the demo, dream-visualiser and benchmark callers.
4. Move shared helpers into the package with re-exports.
5. Delete V1's layout body. Rename `DNG` → `HPR` in `sensor.py` and the V1 default label list, now allowed.
6. **Deletions not approved (Q8, 2026-09-14).** Neither the stale `grid_world.py` render copy nor the dormant `src/environment/renderer_v2.py` is deleted at switch-over; the switch-over plan must ask again. Add the `campfire` key to the shared icon mapping (the asset already exists from Phase 2), and add the noise-free `sense_interoceptive_nociception` **scalar** to the recording snapshot (never the history buffer) (Revision 6 known gap; Revision 7).
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
- **CF** marks where the campfire sits. Per Q12 (decided), the new renderer draws the new `assets/campfire.png` there, falling back to the glyph only if the file is missing.
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

- [ ] **CP0.1a: File baseline first.** `v1_path_guard.py record-files` is run as the very first Phase 0 action. `baseline.json` (plan-start commit, ten frozen files' working-tree sha256 and HEAD blobs, empty `plan_sessions`) and `frozen_files_at_baseline.diff` are committed under `renderer_layout_redesign/v1_guard/`. `add-session` is recorded for the developer session. *Fails if:* any other Phase 0 file predates the baseline commit, or the diff file is missing.
  - *2026-09-14 developer:* `record-files` + `add-session` run (plan start `73d466d8`, all ten files clean, diff is header-only); `check` exits 0 comparing 10 files. **Not yet committed** — the parent commits the guard, test, map rows and `v1_guard/` together after verification.
- [x] **CP0.1b: Frame baseline right after fixtures.** After the generator lands and writes M1/M2/M4, `record-frames` adds fixture hashes and 8 raw-frame hashes per cell for M1, M2, M4 and M7, from two separate processes; committed. `tests/env/test_v1_path_guard.py` green (all three states and FIXTURE CHANGED exercised). *Fails if:* the processes disagree (then switch to a pixel-diff tolerance and record it), any renderer code predates this commit, or the guard test passes a case it should flag.
  - *2026-09-16 developer, verified by senior-developer:* **MET for M1, M2, M4; M7 dropped, see Revision 13.** The two processes agreed on every frame, so no pixel-diff tolerance was needed. Verifier's independent `check`: 10/10 files PASS plus `FRAMES PASS` on all three cells, exit 0. Tests: **65 passed** (11 new frame/fixture cases plus 2 rewritten). **Caveat recorded, not waived:** M1 and M2 pin *identical* frame hashes because they are the same world (Revision 13), so the baseline covers **two** distinct worlds, not three.
  - *2026-09-16 developer, review fix pass:* **frame baseline re-recorded, and the re-record is provably innocuous.** Adding the bush-rule `provenance` field to `run_meta` moved every cell's `run_meta.pkl` hash, so the fixtures were regenerated and `record-frames --force --note` re-run. Old versus new baseline: **all 24 frame hashes identical, all episode payload hashes identical, `frozen_files` unchanged** — only the three `run_meta_sha256` values and a new `frames_note` differ. `check` afterwards: 10 PASS + `FRAMES PASS` ×3, exit 0. Separately, a missing fixture now **fails** this checkpoint's gate (exit 2) instead of passing it silently; see the Phase 0b review fix pass report.
- [ ] **CP-G: V1 pipeline untouched (after every phase, 0 through 4).** `v1_path_guard.py check` exits 0. The report pastes the diff stat, the trailer-annotated `git log`, and each frozen file's state. ATTRIBUTED re-records cite the foreign commits. *Fails if:* any file or frame is UNATTRIBUTABLE (only the user clears it, via `accept` for that exact content), a phase commit touches a frozen file, or a `renderer_v2` package/module is created.
- [ ] **CP0.2: Matrix recordings.** (Revision 10 check first.)
  - Every generated cell's `config_path` is `configs/environment/default.yaml` or under `configs/environment/experiment/basic/`, and every override value that reproduces an archived world matches the cited archived YAML text.
  - **Loadability is re-tested here, not assumed — through the resolving loader (Revision 12).** `load_env_params(load_env_config(path))` is run on every config the matrix intends to load and the result printed per file. **Raw `yaml.safe_load` is forbidden for this check**: it does not resolve `extends:` and reports inherited mandatory keys as missing (the retracted Revision 11 §2; KNOWN_BUGS "Config inheritance ignored", `22c73bac`). *Fails if:* the check is performed with a non-resolving read. Measured 2026-09-16: `default.yaml` and all seven `basic/*.yaml` load; archived `thermal/campfire_world.yaml` loads; archived `sensory_ladder/V2_blur20.yaml` does not (stand-alone, no `extends:`, missing `body.recovery_in_bush_multiplier`) — which is harmless, as no cell loads it.
  - **Revision 11 — the regenerated campfire config loads.** `load_env_params` on `basic/<NN>-campfire_thermal_<size>.yaml` succeeds, and the printed resolved config shows `sensory.visual_value_mode` and `body.recovery_in_bush_multiplier` present, and `blocks_animals` set explicitly on every obstacle entry.
  - **Revision 11 — no archived path is a runtime input.** The generator's recorded `config_path`, `config_chain_sha256` and `overrides_source` fields are printed; no `config_path` and no entry of any `extends` chain lies under `configs/environment/experiment/archive/`. `overrides_source` may cite an archived path, since that is provenance for copied text, not a load.
  - *Fails if:* a cell loads a config outside the maintained set, a cell or its `extends` chain touches `archive/`, a config the matrix intends to load raises at `load_env_params` with no recorded fallback to `default.yaml` + overrides, an override value differs from its cited source, or the regenerated campfire config has not passed `env-config-reviewer`.
  - **Revision 13 (2026-09-16), binding:** the clause "M7–M9 load; V1 renders step 0 of each" is **struck for Phases 0 and 1**. All three raise `AttributeError: 'EnvParams' object has no attribute 'thermal_enabled'` at `src/environment/sensor.py:577`, which no Phase-0 change may fix (the file is frozen). They re-enter at the **Phase 1 `_recording_flag` gate** defined in §D5.1. The generated set is **M1, M1x, M2, M3, M4, M4b, M5, M6, M6b** — nine cells, all present and reported. *Fails if:* any Phase 0 or Phase 1 checkpoint is treated as blocked on M7/M8/M9, or the generator crashes (rather than reporting BLOCKED) on one of them.
  - Then: M1–M6b are written, including M4b (M4b's breakdown must lack `Body Temperature`, and its temperature row renders "not observed"); ~~M7–M9 load; V1 renders step 0 of each~~. Per cell, print the snapshot keys, `true_obs is None`, the breakdown names, and the breakdown ↔ noise-order mapping. Also print each cell's `synthetic` flag and `overrides`, its `config_sha256`, the diamond-offset function name (§D7.7 item 8), and whether `Body Temperature` is in its breakdown, plus that viz entry's keys. *Fails if:* M4 lacks `thermal_field`; M4's breakdown contains Nutrition/Injury (the D10 premise is then wrong, so re-check); M4's `Body Temperature` entry lacks a `value` key, or the registry has no owner for a breakdown name; M3/M9 have `true_obs == obs` everywhere; M5's Olfactory is not `visual_grid`; M6b has `true_obs` present; or a mapping is unresolved. (Revision 11: the "an archive config won't load" clause is withdrawn — no cell loads an archived config. If M2/M3 still cannot be generated, the M8/M9 substitution applies and must be recorded as using a **pre-bush-change** world, per Revision 11 §4.)
- [ ] **CP0.3: Audit positive controls.** V1 M4 reports D1, D2, D3 and D10. Dormant V2 M4 reports D6, and Interoceptive Nociception absent (plus Location/Proprioception if in the breakdown). *Fails if:* any control is missed. **Stop; the audit is broken.**
- [ ] **CP0.4: Spike and decision gate.** A minimal A-style `EpisodeRenderer` (arena + vitals + one pod, figure built once) versus V1, on M4, ≥ 200 frames, pool worker, same lab node (node + CPU recorded). *Fails the gate if:* A median > 0.5 × V1 median. Report to the user with option B before Phase 1.
- [ ] **CP1: Registry and packer.** `test_dashboard_layout.py` is green. *Fails if:* boxes intersect; a disabled modality's height isn't freed; an unregistered name doesn't raise; M4 yields observed Nutrition/Injury rows; `real_available` differs between episodes of one run.
- [ ] **CP2.1: Audit clean.** All cells' checked frames: 0 collisions (text-on-border included), 0 clipped text, legibility met, presence met. The stress variant renders clean or raises; no ellipsised number. *Fails if:* any count is non-zero, or "…" appears in a numeric element.
- [ ] **CP2.2: Mutations.** M-A, M-B, M-C and M-D each make the audit fail. *Fails if:* any mutation passes.
- [ ] **CP2.3: Values match pixels.** Bar ratio and tick x within 2 px; thermal ports green; per-frame clim mutation turns the cooling test red. *Fails if:* a tolerance is exceeded or the mutation stays green.
- [ ] **CP2.4: Vocabulary.** `grep -rniw 'pain' src/environment/dashboard/` shows zero hits (comments included; keep them clean too), and the audit's vocabulary rule is clean on all frames. *Fails if:* any hit.
- [ ] **CP2.5: Observed-caption and true values (Revisions 6–7).**
  - **M4:** satiation, nutrition, injury and body temperature rows show a true value; Nutrition/Injury show `not observed` in the observed column. The interoceptive-nociception row is present iff `interoceptive_nociception_enabled`.
  - **Interoceptive nociception, three-way rule:**
    - M2 (noise off): noise-free = observed;
    - M3 and M9 (noise on, true observations recorded): noise-free slice, differing from observed at some step;
    - M6b (noise on, no true observations): `true not recorded`;
    - M1 (disabled): no row.
  - **Label:** the column is labelled `noise-free` on that row, never `true`. *Fails if:* a row lacks the true column, or an unobserved row prints a number in the observed column. On M4, no rendered text starting `OBS`/`REAL` belongs to a panel whose name is absent from the breakdown. With Q10 = show, the Nutrition/Injury rows read "not observed". *Fails if:* either condition is violated.
- [ ] **CP2.6: Entities drawn.** On M4, a step with the campfire in view shows non-empty foreground ink in its cell, and that ink belongs to an `AxesImage` (the `assets/campfire.png` icon, not the glyph fallback) (Revision 7), and glyph codes are unique across `obstacle_names`. *Fails if:* the cell is empty or grey-square-only (no glyph ink), or codes collide.
- [ ] **CP2.7: Extended-range senses.** (Unblocked 2026-09-14: Q5 answered, so Proprioception is drawn as `action_chips`.) `test_dashboard_extended_range.py` green for the decided encoding, A `channel_maps` (r ≥ 1), including:
  - E2n with and without true observations;
  - identical boxes across two episodes with different maxima;
  - forced side column raising wherever the band was chosen;
  - E6's channel label not `GRS`;
  - r_max recorded only after a rendered, audited override, with machine and fonts named. Largest fitting radius per kind recorded in the report and in `12_renderer.md`. E2–E6 take the sensor-band layout if and only if the side column fails its min size. *Fails if:* any in-use cell (E1–E6) raises; any synthetic cell renders past the recorded largest radius instead of raising; a value above 1 is clipped by the scale; or a concatenated video switches layout.
- [ ] **CP3: Separate V2 entry point.** `render_recordings_v2.py --concat` writes playable MP4s (frame count = steps) for all cells including M7–M9, only under `videos_v2/`. The concat signature assertion holds on real runs and trips on the doctored dir. `test_render_recordings_v2.py` is green (V1 MP4 bytes unchanged after a V2 render of the same dir). CP-G passes. *Fails if:* any file appears or changes under `videos/`, the assertion trips on a real single-run dir, or CP-G fails.
- [ ] **CP4: Speed.** Same node as CP0.4: V2 median ≤ V1 median on every cell and ≤ 0.5 × on M4; RSS growth < 50 MB over 10 episodes; FDs reported. *Fails if:* any gate is missed.
- [ ] **CP5: Viewer.** `test_episode_viewer.py` is green; `check_artifact_layout.py` is clean at 500/834/1440; screenshots and the contact sheet are **looked at**, with findings in the report. *Fails if:* arrays differ, the checker flags a defect, or nobody looked.
- [ ] **CP-C: One meaning per colour (Revision 8).**
  - **What is counted.** On checked frames from M1, M3, M4, E2 and E2n, a pixel census classifies each foreground pixel to the nearest palette token (ΔE threshold from the spec) and attributes it to the panel whose box contains it.
  - **Rules.**
    - Iris pixels appear only in the agent marker and the agent-cell outline.
    - Orange appears only in the nociception rows and pods.
    - The blue↔red temperature ramp appears only in the arena underlay, the thermoception card and its shared legend, and the body-temperature row.
    - Teal appears only in smell panels; slate only in vision panels.
    - There is exactly one temperature legend per frame, and a global noise note is present.
  - *Fails if:* any token is found outside its allowed panels above a small anti-aliasing tolerance (stated in the test), a second temperature legend exists, or the noise note is missing or disagrees with params.
- [ ] **CP-D: Design quality (Revision 6; before retirement; judged against the adopted spec `docs/reviews/design_episode_dashboard.md` since Revision 8).** `visual-design-reviewer` looks at rendered frames from M1, M4, E2 and E8 plus viewer screenshots, at full size. It writes its design spec and verdict to `docs/reviews/design_renderer_layout_redesign.md`. The developer applies the spec: typography, colour system, hierarchy, spacing, iconography, all against the house style sheet. The Implementation Report lists each spec item as applied or rejected-with-reason. A second `visual-design-reviewer` pass on re-rendered frames then passes the "big-tech presentation" bar. *Fails if:* no spec file exists, a spec item is unaccounted for, or the second pass does not pass. Any layout change the spec forces must still pass CP2.1–CP2.7 and CP-G.
- [ ] **CP6: Docs.** `12_renderer.md` (with the V2 disambiguation sentence), `ENVIRONMENT_SUMMARY.md` and `SCRIPTS_DEPENDENCY_MAP.md` are updated in the same commits as the code. *Fails if:* a script-adding commit lacks the map.

---

## Decided questions

Numbers are kept so earlier references stay valid.

- **Q10 (decided 2026-09-14): show.** Every internal-state row shows the observed value (or `not observed`) and the true value; a hidden value is never captioned observed (§D1.1).
- **Q12 (decided 2026-09-14): new asset `assets/campfire.png`.** The new renderer maps `campfire` internally; the shared icon mapping stays frozen, so V1 videos are unchanged (§D1.4).
- **Q13 (decided 2026-09-14): option A**, per-channel diamond maps with per-sense colour scales fixed per episode, applied **from range 1** as in Figure 5 (§D7.2). *Awaiting one-line user confirmation of "from range 1".*
- **Also decided 2026-09-14:** no temperature numbers in the grid view. The temperature colour range is shared by every step of an episode, taken from the episode's field (**corrected in Revision 9**; the earlier "fixed from params" reading is withdrawn).
- **Q1 (decided 2026-09-14): A.** Matplotlib painters behind our own layout, figure built once, local server viewer; Pillow (B) fallback if Phase 0 misses the speed gate.
- **Q3 (decided 2026-09-14): canvas 1440 × 896 px.**
- **Q5 (decided 2026-09-14): draw a Proprioception panel**, six chips with the previous action highlighted in the agent colour; unblocks the E cells and M5.
- **Q7 (decided 2026-09-14): local server viewer only**; no static export.
- **Q9 (decided 2026-09-14): speed gate.** Median frame time on the campfire world ≤ half of V1's, and not slower than V1 on any other world; same lab node, frames and worker type.
- **Q11 (closed 2026-09-14, moot):** "Hiding predator" is written in full.
- **Q13 range confirmation = Q14 (decided 2026-09-14):** option A maps from range 1; bars only at range 0.
- **Q15 (decided 2026-09-14): clamp and outline** for any temperature outside the episode range; no raise.
- **Q16 (withdrawn 2026-09-14):** moot once the per-config bound was removed.
- **Q2 (decided 2026-09-14): package `src/environment/dashboard/`.**
- **Q6 (decided 2026-09-14): minimap in the left column, under Interoception.**
- **Q8 (decided 2026-09-14): the switch-over to the new renderer gets its own reviewed plan.** Deleting the stale `grid_world.py` render copy and the dormant `renderer_v2.py` is **not approved**; both are to be asked again in that plan.
- **Q17 (decided 2026-09-14): neutral setpoint, pale survivable band.** Anchors: episode min, lower body limit, setpoint, upper body limit, episode max; an unreached body limit's anchor is dropped (Revision 9 item 7).
- **Q4 (decided 2026-09-14): as in Figure 3.** An action pill badge sits in the grid-view card's title row, plus a chevron inside the agent marker pointing in the action's direction (a dot for Rest/Eat).
- **Figure 3 is the canonical layout and visual reference (decided 2026-09-14).** The user's words: "I like your figure 3. So don't ask any decision for the layout. Make figure 3 as the direction." Figure 3 is the dashboard sketch on the artifact page, whose frames are produced by `docs/develop/active/refactors/renderer_layout_redesign/fig03_proposed_dashboard.py` with `dashboard_style.py`.
  - The new renderer's implementation follows Figure 3, together with the adopted design review (`docs/reviews/design_episode_dashboard.md`).
  - Layout choices are **not re-opened as user questions**. Implementation-level details are decided by the developer against Figure 3 and the design review.
  - Every deviation from Figure 3 is reported in the Implementation Report with its reason. CP-D compares rendered frames against Figure 3.
  - Where this plan's earlier ASCII blueprints or wording differ from Figure 3, Figure 3 wins; the plan's behavioural rules and checkpoints still apply.

## Open questions for the user

No open user questions (all decided 2026-09-14). See **Decided questions** above; Figure 3 settles any remaining layout detail.

---

## Implementation Report

> **Implemented by**: developer (Phase 0a / CP0.1a only)
> **Date**: 2026-09-14

<!-- Per phase: what was done, deviations, CP evidence (hashes, audit counts, timing table with node + CPU, screenshots looked at, empty src/ diff stat). -->

### Phase 0a (CP0.1a): V1-path guard and file baseline

**Files.** New `scripts/eval/v1_path_guard.py` (stdlib only; `record-files`, `add-session`, `check`, `accept` — user only, `record-frames` refuses until Phase 0b). New `tests/env/test_v1_path_guard.py` (no marker; 4 s). New `renderer_layout_redesign/v1_guard/baseline.json` + `frozen_files_at_baseline.diff`. `SCRIPTS_DEPENDENCY_MAP.md` §1c and §3 rows. No frozen file, `src/` or `configs/` touched.

**Frozen files at record time.** All ten clean against HEAD `73d466d8` (no unstaged, no staged changes). The thermal session's delta that §D5.4 expected had already landed as `feaa3f1b` (trailer `session_01WAgZYVh2C1xh2diJaWT9Nm`), so the diff file is header-only. Baseline sha256 prefixes: renderer.py `c52f18904f08`, render_recordings.py `bc30f58f8bf9`, async_render.py `dac83001b5b6`, evaluation_core.py `5f3efe23f5b6`, dreamer_srl/eval.py `338515971805`, eval_recording.py `13d4416e9115`, sensor.py `22c1d87f2fa2`, benchmark_render.py `30889a3f33c7`, renderer_v2.py `0904d226ab1f`, visualization/default.yaml `cb8a1b0ae2c5`. `plan_sessions` = parent session `session_01LG92Bg5jnSFoUMt4SaUUTk`.

**Tests.** `JAX_PLATFORMS=cpu pytest tests/env/test_v1_path_guard.py` → 23 passed. The cases are PASS, ATTRIBUTED, and ACCEPTED followed by a re-flag. The UNATTRIBUTABLE cases are: an uncommitted edit, a missing trailer, a plan-session trailer, a foreign commit plus our own uncommitted edit (the false-pass case), one bad commit among foreign ones, a mixed commit, content that moved with no commit, and a missing file. The guard-error cases (exit 2) are: no baseline, zero files, an entry with no hash, a frozen-set mismatch, and a frame baseline present that cannot yet be checked. The CLI exit codes are also tested. **Mutation check:** a scratch copy with change detection disabled gives 10 failed / 13 passed.

**Choices where the plan was silent.**
- If a file's content changed but no commit since plan start touches it, it is UNATTRIBUTABLE (there is nothing to attribute it to).
- Plan-owned paths include this doc and the new asset folders (the review's #29 list).
- `record-files --force` keeps `plan_sessions` and `user_accepted`.
- `check` says in plain words that frames were not compared.

**Review fixes (2026-09-14, after senior-developer VERIFIED WITH ISSUES + code-reviewer).** The baseline was **not** re-recorded; no schema change was needed.
- `record-files --force` refuses (exit 2) if any file is UNATTRIBUTABLE against the previous baseline.
- `accept` refuses (exit 2) a sha256 that is not the file's current content, or a missing or symlinked file.
- `check` uses the union of the baseline's plan-owned paths and the script's list, and prints the drift.
- Session matching compares the `session_…` id, so the URL form and the bare id match each other; `session_Xy` does not match `session_X`.
- Added `configs/environment/experiment/basic/*-campfire_thermal_*.yaml` to plan-owned paths (glob, since `<NN>` is not chosen yet).
- Commit history is read with `--full-history`.
- Baseline entry shapes are validated. Any unexpected exception exits 2, never 1.
- Baseline and diff are written atomically. A symlinked frozen path is UNATTRIBUTABLE. `--repo-root` must be the git toplevel.
- The tests isolate git config for the guard's own git calls too.

**Tests after fixes:** 47 passed. New cases cover `--force` after ATTRIBUTED (allowed) and after UNATTRIBUTABLE (refused), both `accept` refusals, plan-owned drift, and the campfire config. Trailer cases use the project's two-line block with a foreign session, a plan session, and one of each. Also covered: bare id ↔ URL in both directions, no substring match, the merge that hides an untrailed side commit, a symlink, a subdirectory `--repo-root`, seven malformed-baseline shapes plus binary garbage, and an unexpected exception exiting 2.

**Mutant checks:** with change detection disabled, 20 failed / 27 passed. With `--full-history` removed, only the merge test fails (1 failed).

**Real repo `check` after fixes:** 10/10 PASS, exit 0. It prints one note: the campfire glob is not in the recorded baseline but is applied anyway.

**Speed check:** skipped (hand-run tool; not on the training path).

### Phase 0b review fix pass (2026-09-16)

> **Implemented by**: developer
> **Date**: 2026-09-16
> **Scope**: the four findings the three reviewers raised against the uncommitted Phase 0b work. No new feature, no plan change.

**What this pass is, in plain words.** Three reviewers read the Phase 0b work (the campfire world config, the fixture generator, and the guard's new frame baseline) and passed it with four findings. One mattered: if the saved example recordings were ever deleted — which is normal, they live under `results/`, which is not in git and gets cleaned — the guard printed "FIXTURE MISSING" and then reported success anyway. In other words the half of the guard that watches the old renderer's pixels went quiet at exactly the moment it stopped working. The other three were small: a flag that promised to require a written reason and did not, a generator that left orphaned files behind, and a world config whose comments did not say plainly that it is not a byte-for-byte replay of the older world it copies.

**File by file.**

| File | Change |
|---|---|
| `scripts/eval/v1_path_guard.py` | **(1)** A pinned fixture that is missing from disk is now a structural failure — `check` raises `GuardError` and exits **2**, joining the existing exit-2 family (missing baseline, zero files compared, frozen-set mismatch). New opt-in `check --allow-missing-fixtures` restores the old tolerant behaviour (exit 0, frozen-file verdict only) for the legitimate case where the fixtures have not been generated yet; it never tolerates a fixture that is *present and disagrees*. All missing cells are collected and printed before the raise, so one run names every gap. **(2)** `record-frames --force` without a non-blank `--note` is now refused (exit 2), which is what its own refusal message already promised. Module docstring, exit-code list and the `DEFAULT_FRAME_CELLS` comment updated — the old comment argued the opposite ("an unsatisfiable checkpoint is worse than a loud gap") and would have re-justified the bug. |
| `scripts/eval/make_render_fixture_recordings.py` | **(3)** New `_clear_stale_recordings()` removes the cell's own `episode_*.rec.gz` before regenerating it, so a run with fewer episodes than the last one no longer leaves orphans that make the guard report a spurious FIXTURE CHANGED. **(4)** New `Cell.provenance` field, written into `run_meta` extras and printed in the CP0.2 report; set for M4/M4b to the campfire bush-rule fact. |
| `configs/environment/experiment/basic/06-campfire_thermal_10x10.yaml` | **(4)** New header paragraph stating the world reproduces the archived campfire world **on the current bush rule** (bushes block animals), that this is the only differing field of 190, and that recordings here are not frame-comparable with anything from before 2026-09-14. |
| `tests/env/test_v1_path_guard.py` | +7 cases, −1 rewritten. |
| `renderer_layout_redesign/v1_guard/baseline.json` | Frame baseline re-recorded (see below). |

**Deliberately narrow blast radius on finding 3.** The clearing step deletes files under gitignored `results/`, which this project has lost once before. It therefore refuses unless the directory is exactly `<out_root>/<cell>/<cell>`, unlinks only individual regular files matching `episode_*.rec.gz`, and never touches a directory, a symlink or a tree. `run_meta.pkl` is left alone on purpose: `write_run_meta` rewrites it in place in the same call, so no stale copy of it can survive anyway.

**Regression evidence (finding 1), recorded because a test that passes both before and after proves nothing.** `test_fixture_missing_is_a_guard_error` was written first and run against the unfixed guard: **failed**, `assert 0 == 2` — the old code exited 0 on a deleted fixture. After the fix: **passes**. Seven new cases in total failed pre-fix and pass post-fix. The three parametrisations cover the three ways a fixture goes missing (run_meta deleted, episode files deleted, whole directory gone). Prior art for the failure shape is in the Known Bugs registry: *"the extero-nociception byte-parity gate silently skipped for three months, and rebaselined itself if its fixture went missing"* (2026-09-09 test-gate-hygiene block) — same shape, different file.

**Tests.** `JAX_PLATFORMS=cpu pytest tests/env/test_v1_path_guard.py -q` → **71 passed in 7.8 s**, exit 0 (was 65 before this pass).

**Real-repo guard runs.**

| Run | Result |
|---|---|
| `check` (final) | `PASS=10, ACCEPTED=0, ATTRIBUTED=0, UNATTRIBUTABLE=0`; `FRAMES PASS` on M1, M2, M4; **exit 0** |
| `check` against a baseline whose three cells point at cleaned-away fixtures | **exit 2**, `GUARD ERROR: the frame baseline pins fixture(s) that are not on disk, so the frame gate compared nothing`, all three cells named |
| same, `--allow-missing-fixtures` | **exit 0**, each cell marked `(tolerated by --allow-missing-fixtures)` |
| frozen-file check | `git status` over the ten frozen paths is empty; no frozen file edited, `accept` never run |

**The baseline did need re-recording, and here is why that is safe.** Adding `provenance` to `run_meta` changes `run_meta.pkl`, whose sha256 the guard pins, so all nine CP0.2 cells were regenerated and `record-frames --force --note` was re-run. Comparing the new baseline against a copy of the old one field by field: **every frame hash is identical, every episode payload hash is identical, and the `frozen_files` block is unchanged** — the only differences are the three `run_meta_sha256` values and a new `frames_note`. So the re-record re-pinned fixture metadata and demonstrably did not paper over a change in V1's rendered output. (A re-record is the one operation that could hide such a change, which is why finding 2's `--note` requirement now bites.)

**Deviations and notes for the verifier.**
1. **Finding 1 changes behaviour the plan never specified.** §D5.4 item 4 lists FIXTURE CHANGED and the frame-drift rules but says nothing about a *missing* fixture — the tolerant exit-0 behaviour was the developer's own choice in Phase 0b, so this is not a plan deviation. If §D5.4 should now name the FIXTURE MISSING state explicitly, that is a plan edit and belongs to `senior-developer`.
2. **Candidate Known Bugs row, not filed by me.** The vacuous frame gate is a new instance of a recorded family but is not itself in the registry. Owner: **`bug-curator`** (sub-agents cannot spawn it).
3. **Not touched, still open:** the verifier's Issue 5 (`--report-cells` help text says "plus M7"; the code uses the generated cells only) — outside this pass's four findings.
4. **`SCRIPTS_DEPENDENCY_MAP.md` not updated:** this pass adds, moves, renames and deletes nothing under `scripts/` and changes no caller, so the Maintenance Contract does not fire. The map's existing rows stay accurate.
5. **Nothing staged or committed**; the working tree is left dirty for verification. `docs/develop/INDEX.md` and `SAVED_RUN_CONFIG_COMPAT.md` remain staged by another session and were not touched.

**Speed check:** skipped, and the skip is justified rather than assumed — every file in this pass is a hand-run tool off the training path (`v1_path_guard.py`, `make_render_fixture_recordings.py`, a test) plus one config used only by the fixture generator. No environment step, model, or observation-pipeline code was touched.

*Implemented by: developer*

## Verification Report

### Phase 0a (CP0.1a): V1-path guard and file baseline

> **Verified by**: senior-developer
> **Date**: 2026-09-14
> **Verdict**: VERIFIED WITH ISSUES. All three issues are minor and none blocks the Phase 0a commit.

**What was checked, in plain words.** The guard is the tool that proves the old (V1) video pipeline is left alone while the new dashboard is built. It records a fingerprint of each of the ten files it must never touch. I checked four things. The fingerprints are right, computed without using the guard. The rules match the plan. The tool catches a real change. Nothing else in the repo was edited.

| File | Change | Status | Notes |
|------|--------|:------:|-------|
| `scripts/eval/v1_path_guard.py` | new, 454 lines | ✅ | State order PASS → ACCEPTED → ATTRIBUTED → UNATTRIBUTABLE matches §D5.4 + Revisions 2/3. `accept` never touches `worktree_sha256`. `record-frames` refuses (exit 2). `check` exits 2 if a frame or fixture baseline exists that it cannot yet compare. Git is called read-only. |
| `tests/env/test_v1_path_guard.py` | new, 296 lines | ✅ | Re-run by the verifier: **23 passed** (6.9 s, pytest exit 0). The developer's mutant run (10 failing) was not re-run; the independent scratch-clone test below covers the same claim. |
| `v1_guard/baseline.json` | new | ✅ | The frozen set is exactly the ten §D5.4 files, including `renderer_v2.py` and `configs/visualization/default.yaml`. For all ten, the working-tree sha256 (Python `hashlib`, no guard import), the sha256 of `git show 73d466d8:<path>`, and `git rev-parse 73d466d8:<path>` all equal the recorded values. `plan_sessions` = `https://claude.ai/code/session_01LG92Bg5jnSFoUMt4SaUUTk`. `user_accepted` = []. |
| `v1_guard/frozen_files_at_baseline.diff` | new | ✅ | Header-only, which is correct: all ten files were clean at `73d466d8`, and the header text matches §D5.4 exactly. |
| `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` | +2 rows | ✅ | The §1c row (bare import + CLI subprocess) and the §3 row (HAND+TEST, `parents[2]`, `DEFAULT_BASELINE_REL` constant) are accurate. The diff holds only these two hunks. |
| `RENDERER_LAYOUT_REDESIGN.md` | CP0.1a note + Implementation Report | ✅ | Only the developer's two hunks, plus this report. |
| `docs/diary/2026-09-14.md` | developer row | ⚠️ | The row is correct, but the same file carries a 22:12 Notes hunk from another session. Stage only the developer's hunks, or leave the diary to its own commit. |

**Independent evidence.**
- **Real repo.** `check` gives exit 0 with PASS=10. HEAD has since moved to `401c821f`, a docs-only commit from another session that touches no frozen file. `git status` and `git diff --stat 73d466d8 HEAD` over the ten files are both empty.
- **Detection (scratch `git clone --shared`, real files untouched).** Guard run in scratch; exit codes and states:

  | Scratch scenario | Exit | State |
  |---|:---:|---|
  | Clean clone | 0 | PASS |
  | One byte flipped in `sensor.py` | 1 | UNATTRIBUTABLE |
  | `sensor.py` restored | 0 | PASS |
  | One space appended to `default.yaml` | 1 | UNATTRIBUTABLE |
  | That change committed with a foreign trailer | 0 | ATTRIBUTED |
  | A further change committed with the plan-session trailer | 1 | UNATTRIBUTABLE |

- **Scope.** `git status` over `scripts/`, `tests/`, `src/` and `configs/` shows only the two new files. The four dirty `configs/environment/*` files, the thermal `.npz` fixture and the other `docs/environment/` files belong to other sessions and must stay out of this commit.

**Choices the developer made where the plan was silent. None contradicts the plan.**
- *Changed content but no commit to attribute it to* → UNATTRIBUTABLE. Correct. The literal §D5.4 wording ("every commit carries…") would be vacuously true with zero commits, which would silently pass a reverted dirty baseline. The table's "anything else" row supports the stricter reading.
- *The plan doc and the three asset paths are plan-owned.* This is stricter than §D5.4's list and follows 🟡29. `assets/campfire.png` already exists at HEAD; that is harmless.
- *`record-files --force` keeps `plan_sessions` and `user_accepted`.* Correct. Dropping `plan_sessions` would let a plan commit look foreign after a re-record.

**Issues (minor; for Phase 0b or later).**
1. **A trailer counts as a plan session only if it matches the recorded value character for character.** A plan commit whose trailer carries the bare session ID, not the full URL, would be treated as foreign → a false ATTRIBUTED. Fix in Phase 0b: match on the `session_…` suffix.
2. **The new Revision 10 test-world configs are missing from `PLAN_OWNED_PATHS`.** These are `configs/environment/experiment/basic/<NN>-campfire_thermal_<size>.yaml`. Add them with a filename-prefix entry when Phase 0b next touches the guard.
3. **`git log <start>..HEAD -- <path>` uses default history simplification.** A frozen-file commit on the side branch of a merge could be hidden. The risk is low, since version branches advance by fast-forward. Consider `--full-history` in Phase 0b.

**Speed:** ✅ not applicable. This is a hand-run tool and is off the training path.

**Conclusion**: CP0.1a is met once the files below are committed together. The baseline is correct and independently reproduced, the rules match the plan, and detection is demonstrated. No frozen file was touched.

**Phase 0a commit (explicit pathspec):**
`scripts/eval/v1_path_guard.py`, `tests/env/test_v1_path_guard.py`, `docs/develop/active/refactors/renderer_layout_redesign/v1_guard/baseline.json`, `docs/develop/active/refactors/renderer_layout_redesign/v1_guard/frozen_files_at_baseline.diff`, `docs/environment/SCRIPTS_DEPENDENCY_MAP.md`, `docs/develop/active/refactors/RENDERER_LAYOUT_REDESIGN.md`. Exclude `docs/diary/2026-09-14.md` (it has a foreign hunk) and `docs/develop/INDEX.md` (it has foreign staged changes, and the frontmatter is unchanged so no regen is needed).

### Phase 0b (CP0.1b + CP0.2): the campfire world, the fixture generator, and the frame baseline

> **Verified by**: senior-developer
> **Date**: 2026-09-16
> **Verdict**: **VERIFIED WITH ISSUES.** Every technical claim the developer made is true and was reproduced independently. The issues are about *evidence and record-keeping*, not about the code, and none of them blocks the Phase 0b commit.

**What was checked, in plain words.** Phase 0b delivered three things: a new "campfire" world config (the only maintained world where the agent feels temperature and sees a fire it has no icon for), a script that records one saved episode per kind of world the new dashboard must draw, and an extension to the guard that pins exactly what the *old* renderer draws from three of those recordings so that later work cannot change it unnoticed. I re-derived each claim from the system's own output rather than reading the developer's report: I loaded the new config through the same loader the trainer uses and compared it field by field against the archived world it was copied from; I re-ran the guard; I read the recordings back off disk and recomputed their observation layouts; and I re-ran the matrix report myself, including the three cells the developer said were broken.

| File | Change | Status | Notes |
|------|--------|:------:|-------|
| `configs/environment/experiment/basic/06-campfire_thermal_10x10.yaml` | new, 112 lines (untracked) | ✅ | Loads through the resolving loader. **The "identical 33-dim observation" claim is confirmed**: the observation breakdown is character-for-character the archived world's — Satiation 1, Body Temperature 1, Interoceptive Nociception 1, Extero Nociception 1, Thermoception 5, Olfaction 5, Collision 5, Proprioception 6, Visual 8 = 33. Of **190** `EnvParams` fields, exactly **one** differs (below). `extends` chain is two files, neither under `archive/` — CP0.2's "no archived path is a runtime input" passes. |
| `scripts/eval/make_render_fixture_recordings.py` | new, 555 lines (untracked) | ✅ | Refuses any config outside `default.yaml` + `experiment/basic/` (Revision 10 rule) and loads through `load_env_config`, never raw `yaml.safe_load` (Revision 12 rule). A typo'd override key raises instead of being silently inert — a good addition the plan did not ask for. All nine CP0.2 cells written and reported. |
| `scripts/eval/v1_path_guard.py` | +313 / −27 (586 → 867 lines) | ✅ | `record-frames` / `frame-worker` implemented per §D5.4 item 3; `check` now compares fixtures then frames per item 4, with the FIXTURE CHANGED / FIXTURE MISSING / UNATTRIBUTABLE / ATTRIBUTED semantics the plan specifies. Re-recording an existing frame baseline requires `--force` **and** a `--note` — stricter than the plan, and correct. |
| `tests/env/test_v1_path_guard.py` | +168 / −10 (508 → 666 lines) | ✅ | Re-run by the verifier: **65 passed, 6.8 s**. 11 genuinely new cases plus 2 rewritten (the developer's "13 new tests" counts both). The frame hasher is stubbed, so the tests exercise the guard's verdict logic without rendering — the right seam. |
| `renderer_layout_redesign/v1_guard/baseline.json` | +73 | ⚠️ | Correct in form. The ⚠️ is that **M1 and M2 pin identical hashes** (same fixture payloads, same eight frame hashes), so three baseline entries cover two distinct worlds. Recorded in Revision 13; no action needed now. |
| `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` | +1 / −1 | ⚠️ | The remaining working-tree change is only the "four cells → three cells" correction. **The substantive Phase 0b rows were already committed in `2ebd6209`**, a commit titled for unrelated hypervigilance work. The map ended up describing code that had not been committed, which inverts the Maintenance Contract's "same change" requirement. Content is accurate; the sequencing was not. |
| `RENDERER_LAYOUT_REDESIGN.md` | Revision 13 + this report | ✅ | Written by the verifier, because the developer left the plan doc untouched (Issue 1). |

**The one environment difference, stated plainly.** The new campfire world's bushes **block animals**; the archived campfire world's did not. This is the only field that differs (`obs_blocks_animals`: the ten bush slots are `True` in the new world, all `False` in the archived one) and **it is a real change to recorded behaviour, not a cosmetic one**. `src/environment/core.py:609` merges that array into the animal movement mask and passes it to both the hunting and the wandering step, so an animal that could previously walk into a bush now cannot — which changes animal trajectories, and through them the random-number stream and the reward series, from the first step. The choice is nonetheless **correct**: `true` is the project's canonical value since 2026-09-14, the config redeclares its own obstacle list (and lists replace wholesale, so omitting the key would have silently reverted it), and no critical-settings registry *value* changes, so no new change-log entry is owed. The consequence to carry forward is only that **M4 is a post-bush-change world and is not frame-comparable with anything recorded before 2026-09-14**.

**Independent evidence.**

| What I re-derived | Result |
|---|---|
| New config vs archived campfire world, both through `load_env_params(load_env_config(path))` | Both load. Breakdowns **identical**, 33 dims. 1 differing field of 190 (`obs_blocks_animals`). |
| `v1_path_guard.py check`, run by the verifier | `PASS=10, ACCEPTED=0, ATTRIBUTED=0, UNATTRIBUTABLE=0`; `FRAMES PASS` on M1, M2, M4; **exit 0**. Frozen-file diff stat empty; no commits touch a frozen file since plan start. |
| Fixture extras, read back from disk (M4, M6b, plus all other cells) | Every cell carries `synthetic`, `overrides`, `overrides_source`, `config_path`, `config_sha256`, `config_chain_sha256`, `true_obs_recorded`. M4: `synthetic=False`, chain of 2. M6b: `true_obs_recorded=False`, chain of 4. |
| `true_obs` presence vs each cell's claim | Matches everywhere. **M6b is the only cell with `true_obs is None`** (CP0.2's "M6b has `true_obs` present" failure does not fire). **M3's largest OBS-vs-noise-free difference is 1.4876**, so "M3 has `true_obs == obs` everywhere" does not fire either. |
| Other CP0.2 failure conditions | M4 has `thermal_field` ✅; M4's breakdown has no Nutrition/Injury ✅; M4's `Body Temperature` has a viz entry ✅; M4b's breakdown lacks `Body Temperature` (32 vs 33) ✅; M5's Olfaction is `visual_grid` ✅; no unresolved breakdown-to-noise mapping ✅. **No CP0.2 failure condition fires** — the developer's claim is confirmed. |
| The M7/M8/M9 claim, tested on all three | **Confirmed and broader than claimed.** All three raise `AttributeError: 'EnvParams' object has no attribute 'thermal_enabled'` at `sensor.py:577`. **M8 as well as M9** has `true_obs is None`. M8/M9 snapshots carry `pred_pos`/`neutral_pos` where M7 and every generated cell carry `animal_pos`. |
| Frame-truncation soundness (the guard hashes 8 steps of a truncated copy) | **Sound.** `render_recordings.py:114` derives `thermal_clim` from `snapshots[0]` only, so truncating an episode cannot shift the colour limits and the truncated frames are the full episode's first eight. |
| Frozen files and commit state | No frozen path is modified in `git status`; both new files are **untracked**; nothing from Phase 0b is committed. Phase 0a is already committed as `7a70d666`. |

**Issues (none blocks the commit).**

1. **The developer wrote no Phase 0b Implementation Report.** The plan doc was left unmodified and all evidence lives in `tmp/20260916_cp02_report.log`, which is gitignored and will not survive. This report and Revision 13 stand in for it, but the developer should append the Implementation Report before the commit.
2. **The saved CP0.2 log is stale and ends in an uncaught crash.** It was written at 14:01, four minutes before the script it describes (14:05), predates the handler that reports a blocked cell gracefully, contains **zero** M7/M8/M9 rows, and its final lines are a traceback. The conclusion it supports is nevertheless correct — I re-ran the report with the current script and it exits 0 and prints a clean `BLOCKED` block for each of M7, M8 and M9 — but **the artifact does not support the claim it is cited for**, and a fresh log should replace it.
3. **`env-config-reviewer` has not reviewed the new campfire config.** CP0.2 lists this explicitly as a failure condition ("the regenerated campfire config has not passed `env-config-reviewer`"). No review exists under `docs/reviews/`. **This is the one open CP0.2 gate**; it is cheap and should run before or immediately after the commit.
4. **Cell M1x is undocumented scope growth** — a good addition (the plan needs a nociception-disabled fixture and no cell provided one), now written into the §D5.1 matrix by Revision 13, but it was added without a plan change.
5. **Minor, in-code doc error.** `--report-cells`' help text says the default is "the generated cells, plus M7"; the code uses the generated cells only.
6. **Minor, worth a note so nobody misreads it.** `_extends_chain` uses raw `yaml.safe_load`. That is legitimate — it hashes the files in the inheritance chain rather than checking whether a config loads — but it sits one line from the Revision 12 prohibition and deserves its existing comment.

**Speed:** ✅ not applicable, same reasoning as Phase 0a — the generator and the guard are hand-run tools off the training path. The guard's `check` now costs three subprocess renders (~seconds), which is a phase-boundary cost, not a training cost.

**Out-of-scope files in the working tree (must NOT be staged).** `docs/develop/INDEX.md` and `docs/develop/active/refactors/SAVED_RUN_CONFIG_COMPAT.md` are **staged by another session**, and the staged INDEX hunk is a regression (it rewinds the regeneration timestamp and drops 253 lines from the compat doc). `scripts/analysis/style/house.py`, `renderer_layout_redesign/page_template.html`, `docs/develop/active/meta/artifact_format_bugs.md`, `docs/diary/2026-09-14.md` and the untracked `docs/experiments/` and `scripts/analysis/studies/` trees belong to other sessions. Commit with an explicit pathspec.

**Conclusion.** CP0.1b is **met** for M1/M2/M4 (M7 correctly excluded, and its exclusion is now written into the plan). CP0.2 is **met except for the `env-config-reviewer` gate on the campfire config**. The developer's headline claim — that the plan is wrong about M7/M8/M9 — is **correct**, and in fact understated: all three cells are blocked, not one, and M8 shares M9's missing noise-free observations. No frozen file was touched and nothing was committed.

**Phase 0b commit (explicit pathspec):**
`configs/environment/experiment/basic/06-campfire_thermal_10x10.yaml`, `scripts/eval/make_render_fixture_recordings.py`, `scripts/eval/v1_path_guard.py`, `tests/env/test_v1_path_guard.py`, `docs/develop/active/refactors/renderer_layout_redesign/v1_guard/baseline.json`, `docs/environment/SCRIPTS_DEPENDENCY_MAP.md`, `docs/develop/active/refactors/RENDERER_LAYOUT_REDESIGN.md`, `docs/diary/2026-09-16.md`.

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

## Feedback from plan-reviewer (fourth pass: Revision 4, extended-range senses)

**Date**: 2026-09-14 (fourth pass, on Revision 4 only) · **Verdict**: SOUND WITH CONCERNS — no Critical finding. The three user decisions are carried faithfully: the band is chosen once per config from params and recorded in `layout_signature` (§D7.1), the canvas is unchanged, fit-or-fail still ends in `LayoutOverflowError`, the encoding is one module constant behind one painter interface (§D7.2), and the V1 freeze is untouched (Revision 4's File Changes rows are all new files plus `12_renderer.md`; the ten hashed files are not edited). Seven Moderate findings remain, all cheap to fix in the doc; two of them (#35, #36) decide whether the "largest range that fits" and the extended-range noise map are *measured* or merely *asserted*. Full table in [`docs/reviews/plan_renderer_layout_redesign.md`](../../../reviews/plan_renderer_layout_redesign.md) §Fourth pass.

Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run · 🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

**Verified today (trainer's own loader, `JAX_PLATFORMS=cpu`):** E1–E6 (seven files) and M5 all load at current code. Ranges as the plan states (smell r1; vision r2 for E2–E6; E1 vision r0 with 8 dims — not off). **All eight have `perceptual_noise.enabled: false`** and **all eight carry `Proprioception: 6`** in their breakdown. Q1/Q2 (E6) have `visual_vector_size: 1` and all-zero `visual_background_properties`; `build_sensory_viz` labels that channel `'0'`. `noise_modality_order` uses the breakdown names `Olfaction` / `Visual`, so the D4.2 mapping resolves trivially. `sensor.py:715` still emits `DNG`. `get_visual_offsets` hand-codes the r=1 order and uses loop order at r≥2 (its sort code is dead). Known Bugs, the directional-sensors report and the wiki carry nothing on rendering grid senses at r≥2 — no prior art, no collision.

**Should be resolved before Phase 2 (Moderate)**

- 🟡 **#33 Layout choice must not be able to read episode data.** `RenderContext` holds snapshot 0 and `thermal_clim`, and Revision 4 adds a per-episode scale maximum that is printed on the panel. If any `min_size`, or the (a)/(b) decision, depends on such data — even through the width of the printed scale text — `layout_signature` differs between episodes of one run and the `--concat` assertion trips on a real run. Loud, not silent, but a rerun. Fix: state in §D7.1 that layout selection and every `min_size` read only params and `FontMetrics`; give the scale label a fixed-width format; add to `test_dashboard_layout.py`: two episodes of one run with different maxima and different snapshot 0 yield the identical layout choice and boxes. — owner `senior-developer`
- 🟡 **#34 The grid-view widening rule contradicts the arena's registered floor, and its order against fit-or-fail is unspecified.** §D7.3 caps `W` "below 32 px"; §D1.1 registers the arena at "≥ 48 px/view cell". Which floor wins decides whether an r4 world (W=9, 432 px at 48) fits above the band. And "cap W + caption the clipped footprint" is a third outcome the packer sequence in §D1.2 step 4 ((a) → (b) → compact → raise) does not place. Fix: one floor; explicit order: `W` from ranges → pack (a) → pack (b) → reduce `W` toward `local_view_size` (never below) with the clip caption → compact → raise. The minimap's view rectangle should show `W`, not `local_view_size`. — owner `senior-developer`
- 🟡 **#35 "Largest range that fits" is measured by the packer, not by pixels.** §D7.6 computes `r_max` per kind from `min_size` arithmetic and asserts `r_max+1` raises; nothing is rendered or audited at `r_max`. That is the packer's constants restated, not a measurement — the exact circularity the audit exists to break. Fix: for each kind, generate a synthetic override at `r_max` (both senses; each alone), render, run the pixel audit; `r_max` goes into the report and `12_renderer.md` only if audit-clean, with the machine/font named (the number depends on `FontMetrics`). Same fix for CP2.7's "E2–E6 take the band iff the side column fails": as written it can only agree with the packer; assert instead that when (b) was chosen, forcing (a) through a test hook raises. — owner `senior-developer`
- 🟡 **#36 No fixture exercises the noise-error map.** Every E cell and M5 has noise off, so `real_available` is false for every grid sense at r≥1 in the matrix; the noise-on cells (M3/M9) have vision at r0. The test "noise-error map present iff `real_available`" can only ever see the absent branch — the same hole as #28. Fix: **E2n**, an in-memory override of E2 with `perceptual_noise_enabled: true` (its `noise_modes` already put Visual and Olfaction in mode 2), with `true_obs`; plus the same cell under `--no-true-obs`. §D7.5 should also say explicitly that the error-map **box** is reserved from params and captioned "true obs not recorded" when `true_obs is None`, the D4.2 rule applied to this slot. — owner `senior-developer`
- 🟡 **#37 E6's single-channel vision breaks §D7.2's channel semantics.** The plan identifies terrain channels by index (GRS/SND/PLN = 0–2) and overrides labels from a table "keyed by channel index". At `visual_vector_size: 1` (Q1/Q2, verified) there is no terrain channel, one entity channel, and the index-keyed table would label it `GRS` — a false caption in a video, the D10 class. Fix: terrain channels := columns where `params.visual_background_property` is non-zero in any row (0–2 at the V=8 default; none at V=1); the label table applies only when V==8, else the adapter's numeric labels stand; A shows one map, B a single-channel brightness map with no legend, C one row; CP2.7 asserts E6's label is `0`. — owner `senior-developer`
- 🟡 **#38 The subtitle omits the variable the ladder sweeps.** §D7.5 prints `σ-floor` and `ρ` but not `visual_blur_radial_scale`, which is what V1_blur40 (4.0) … V4_blur05 (0.5) vary (verified); those four arms would render identical subtitles. Fix: `blur aniso scale s, floor f, ρ a`. — owner `senior-developer`
- 🟡 **#39 Synthetic override cells record the base config's hash as their ground truth.** E7/E8/E9 (and M4b/M6 from earlier revisions) are in-memory overrides, but `run_meta` extras carry the base file's `config_sha256`, so the recording says E7 *is* E2's config. The report label does not travel with the fixture. Fix: extras carry `synthetic: true` and `overrides: {key: value}`; CP0.2 prints them. No guard interaction: the frame baseline hashes M1/M2/M4/M7 only, and no config file is written. — owner `senior-developer`

**Low**

- 🟢 #40 A scale maximum of 0 (an episode that never senses anything) divides by zero; floor only that case (e.g. 1.0), never a fixed floor, since blurred readings are ≪ 1.
- 🟢 #41 Encoding B shows terrain only when "no entity channel is non-zero"; under blur every cell carries Gaussian tails, so terrain would never show. Use a threshold relative to the scale.
- 🟢 #42 Cell order: painters and `/api/values` offsets must call `get_visual_offsets(r)` rather than re-derive ring order; add a test that the painter's cell→offset table equals it for r = 0…4.
- 🟢 #43 E9 says "vision off" but E1 has `visual_sensor_enabled: true` at range 0; the override must also disable vision, or the row should say "vision r0".
- 🟢 #44 Footprint legend chips and the "footprint exceeds view" caption are new text in the arena title strip beside the title and action badge; classify them under `fit_text`'s numeric-raise / free-text rule.
- 🟢 #45 §D7.4 says the scale is fixed at setup but not how. `EpisodeRenderer` receives the whole `episode_payload`, so a setup pre-pass over the obs/true-obs slices (by breakdown offsets, not N calls of `build_sensory_viz`) gives the maximum before the figure is built; random access in the viewer is unaffected (one renderer per episode). Say so, and count it in the setup ms that CP4 reports. Across a concatenated video the scale changes per episode, disclosed by the printed scale — the `thermal_clim` precedent.

**Assumptions (this pass)**: ❓ **Q5 (Proprioception) is now load-bearing** — every E cell and M5 carries `Proprioception: 6`, so the completeness rule raises on all of them until Q5 is answered; CP2.7 cannot run before it. ❓ `r_max` is machine-dependent through fonts (state the machine, #35). Verified: configs load; noise off in all E cells; V=1 background all-zero; frozen set untouched by Revision 4; no prior art.

**Cost of being wrong**: no data loss and no training run at stake. #35/#34 would put a packer number into `12_renderer.md` as "the largest range that fits" and let the first r3+ olfaction grid someone actually trains raise or clip on render — a day of re-rendering. #36/#37 ship the extended-range noise map and the presence cells untested into the Q13 decision, and could put a `GRS` label on a channel that is not terrain in every E6 video — a wrong caption, the D10 class, reversible by re-render.

Reviewed by: plan-reviewer

## Feedback from plan-reviewer (fifth pass: Revision 6, user decisions)

**Date**: 2026-09-14 (fifth pass, on Revision 6 only) · **Verdict**: SOUND WITH CONCERNS — no Critical finding. The six decisions are carried into the body, the ten hashed files are still unedited by this plan (the dirty four — `renderer.py`, `renderer_v2.py`, `sensor.py`, `evaluation_core.py` — are the thermal session's, as before), `assets/campfire.png` does not exist yet, and the "no nociception field in the snapshot" claim is correct (`src/utils/eval_recording.py:44-58` stores satiation, nutrition, injury_level, body_temp, thermal_field; `nociception_history_buffer` is not snapshotted). Five Moderate findings, two of which the plan's own checkpoints would let through: the thermal scale formula as written raises on the campfire world (the plan's own primary thermal cell), and the interoceptive-nociception "true" column prints a false caption on every noise-off run. Full table in [`docs/reviews/plan_renderer_layout_redesign.md`](../../../reviews/plan_renderer_layout_redesign.md) §Fifth pass.

Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run · 🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

**Should be resolved before Phase 2 (Moderate)**

- 🟡 **#46 The params-only thermal span omits ratio-mode heat sources, so §D4.3's own setup check raises on M4.** §D4.3 takes the span over `thermal_default_temp_low/high`, "every `obs_temperature` and `res_temperature` stamp (already absolute at load)", and `min/max_temperature`. The campfire world uses the *other* style — `temperature_ratio: [11, 13]` (`campfire_world.yaml:125`), so `params.obs_temperature` is 0 and the heat lives in `obs_temp_ratio_low/high` (`state.py:364-369`). A fire cell is `default_temp + ratio·|default_temp|` (`core.py:1296-1310`), i.e. up to 28 × 12 = **+336** on M4, while the formula as written gives span = 28 → limits (−28, +28) → "setup raises `ValueError` naming the extreme value" on every M4 episode. Fix: the bound must enumerate what the field builder can place — default-temp corners; absolute stamps; `ratio_high · max|default_temp|`; `count × spot_temp` when random spots are on; and, when `min_fire_separation == 0`, `count_high ×` the largest stamp (stamps are additive, `core.py:1313-1321`). The final blur is weight-normalised, so the pre-blur bound holds after it. Add a test that `dashboard_thermal_limits(params)` on M4 contains every field value of ten seeds. — owner `senior-developer`
- 🟡 **#47 The scale's midpoint is neutral only because the plan keeps the limits symmetric — and that is not the range the user described.** §D4.3 uses `(setpoint − span, setpoint + span)`, so the RdBu midpoint sits on the setpoint by construction. The user's example (an explicit "−30..+150 with setpoint 0 neutral") is *asymmetric*, and the frozen `_thermal_rgba` (`renderer.py:188-192`) is a single linear ramp: on an asymmetric range its midpoint is not the setpoint. With the symmetric formula on M4 (±336), the cold world at −28 maps to t ≈ 0.46 (near white) and the survivable band ±15 occupies 4 % of the scale — the cold/neutral distinction the underlay exists to show is nearly invisible (V1 has the same property today). Decide one: (a) symmetric, and say what resolution that costs; or (b) two-slope (`TwoSlopeNorm`-style, neutral pinned at the setpoint, asymmetric limits), in which case `_thermal_rgba`, `draw_thermal_diamond` (calls `_thermal_rgba` at `:313`) and `draw_temperature_gauge` (`:234`) must all be **copied** into the package, not imported, or the pod and gauge will disagree with the underlay; and the scale strip must show the asymmetric ticks. — owner `senior-developer` (choice is the user's)
- 🟡 **#48 V1's icon cache is process-global and ignores its argument after the first call, so "V1 unaffected" is order-dependent inside any shared process.** `_load_icons` returns `_ICON_CACHE` whenever it is set (`renderer.py:34-36`), and V1 keys obstacles by name — `icons.get(params.obstacle_names[...])` (`:723-724`, `:678`). §D1.3 lists `_load_icons` as imported read-only and §D1.4 has V2 resolve `campfire` "through its own internal icon table". If V2 populates the cache first — a pytest session where `test_dashboard_frames.py` runs before the V1 M4 positive controls in `test_render_audit_controls.py`; `test_dashboard_compat.py` (M7 with both renderers); `render_recordings_v2.py --benchmark` (both in one worker) — V1 draws the campfire PNG, its M4 frame no longer matches the CP-G baseline, and D-class controls can move. In the other order V2 inherits V1's dict, finds no `campfire`, and silently draws the `CF` glyph while CP2.6 stays green. `12_renderer.md:328` already records the hazard. Fix: V2 never calls `_load_icons`; copy a cache-free (or mapping-keyed) loader into the package under §D1.3's copy rule; `test_dashboard_compat.py` asserts V1's M4 frame hash equals the CP-G baseline **after** a V2 render in the same process; CP2.6 additionally asserts the campfire cell's ink is the PNG (an `AxesImage`), not the glyph. `assets/` need not join the file guard: a change to a *mapped* asset already surfaces in the frame hashes (§D5.4 names "an asset"), and an unmapped file can reach V1 only through this cache. — owner `senior-developer`
- 🟡 **#49 Audit rule 10 forbids the glyph fallback it is supposed to coexist with.** §D5.2 rule 10: "No `Text` element's ink lies inside the arena grid's extent." §D1.4's iconless-entity glyph is "a centred 1–3 letter code" — a `Text` inside the arena — and CP2.6 checks its ink. With `campfire.png` present M4 draws no glyph, but the fallback is the required path for archived `icon_config` pickles and missing files, and the first such frame either fails rule 10 or gets exempted by a painter tag, which is the classification-by-declaration finding #3 removed. Fix: rule 10 = no *numeric* text (`[-+]?\d`) inside the arena, or draw the glyph code as a `TextPath`/`PathPatch` — say which. — owner `senior-developer`
- 🟡 **#50 The interoceptive-nociception true column prints "true not recorded" on every noise-off run, where the observed value *is* the noise-free value.** `true_obs` is `None` unless `params.perceptual_noise_enabled` (`evaluation_core.py:305-307`), and with noise off `get_observation` returns the noise-free convolved percept unchanged (`sensor.py:409-410`, `:492-494`, `:169-186`); a modality with noise mode `none` gets `sigma_eff = 0` and is likewise exact. So on M2, M8 and every noise-off world (the majority of the project's recordings) the plan's rule "from `true_obs` when observed and recorded, else `true not recorded`" captions an exactly known value as unrecorded — a false statement about sensory access in the row the project cares most about (the D10 class), and CP2.5 as written ("a true value **or** `true not recorded`") accepts it. Fix: the true column follows §D4.2's params rule, which the plan already computes — when `real_available['Interoceptive Nociception']` is false the true value equals the observed value (say so: "= obs, no noise"); when true and `true_obs` recorded, the slice; "true not recorded" only when true and `true_obs is None` (M6b, E2n `--no-true-obs`). CP2.5 adds three assertions: M2/M8 true == observed; M3/M9 differ at the max-gap frame (M3 noises this channel at σ = 0.1, `01-interoNocicept_noise.yaml:332-334`); M6b reads "true not recorded". Also: the row's presence cannot be "whenever the state exists" — the buffer exists in every state (`state.py:81`) but is never snapshotted — so make it `interoceptive_nociception_enabled` via `_recording_flag`, else M1 carries a two-caption row. — owner `senior-developer`

**Low**

- 🟢 #51 CP2.7 and `test_dashboard_extended_range.py` still say "for each encoding kind" / "all three encoding kinds" and test layout-invariance by switching `GRID_ENCODING`, while Revision 6 drops B and C "unless the developer needs them for the Figure 5 comparison page" — which already exists (figs 05/06/07 are on disk). Decide: A only (rewrite CP2.7, drop or stub the invariance test, record r_max for A), or keep B/C and say so. Raised as Low because it costs wasted work, not a wrong result.
- 🟢 #52 §D7.5 still says "At r ≤ 1 the existing REAL tick on bars stays" and "True vs observed at range ≥ 2"; with A from range 1 there are no bars at r = 1, so the noise-error map applies from r ≥ 1. No cell exercises r = 1 with noise (E1/M5 noise off; M3/M9 are r0; E2n is r2) — add E1n or note the gap. For Q14, tell the user which cells the choice changes: **only E1/M5** (smell r1); M1, M4, M2/M3, M8/M9 are r0 for both senses (`default.yaml:206,216`, `campfire_world.yaml:236,246`, `01-interoNocicept*.yaml:267,287`) and keep spectrum + single-cell bars. The blueprint's "VISUAL (range 1)" was already inaccurate for M1.
- 🟢 #53 §D1.3's pinned-import list still names `thermal_color_limits`, which §D4.3 no longer uses; drop it or say what still imports it. The INOC "true" value is a noise-free *percept* (kernel-convolved), not a state — label the column "noise-free" or footnote it so a reader does not take it for the injury level. The Phase 5 snapshot item should name the scalar to store (`sense_interoceptive_nociception(state, params)`, noise-free) — never the buffer for later reconstruction, which is the class the Known Bugs row "Reconstructed felt-pain signal leaked the episode's random starting injury" records.

**Answers to the five asked checks.** (a) Claim correct for the snapshot; the observed/true split is well-defined for satiation, nutrition, injury and body temperature (true from the snapshot, observed from the obs slice, noisy or not) and for INOC only once #50's three-way rule is adopted. (b) Not params-only as written on M4 (#46); clipping is replaced by a setup raise, which is the right shape, but the raise fires on M4 itself until #46 is fixed; the ported "does not rescale" test survives (fixed limits are trivially frame-invariant); V1's `thermal_color_limits` is untouched and V2 no longer imports it; midpoint neutrality holds only under the symmetric form (#47). (c) V1 cannot pick the file up through configuration — `_load_icons` iterates only mapped keys, no glob/`listdir` in `renderer.py`, `grid_world.py` (own hard-coded default dict, no campfire) or `renderer_v2.py` (imports V1's loader); the other `assets/` readers are the font loaders and a demo MP4 path — but it can through the cache (#48). (d) At r = 1 kind A fits the side column (5 maps × 3 cells × 10 px ≈ 150 px + gaps < 330 px), so the band rule and r_max tests are unaffected in placement; only the stale bar-tick text (#52) and the B/C ambiguity (#51) remain. (e) Intact: Revision 6 adds a new asset, a new package function and a Phase 5 item; no frozen file is listed in any Phase 0–4 row.

**Assumptions (this pass)**: ❓ the user's intended scale is the asymmetric example, not the symmetric formula (#47); ❓ B and C are not wanted (#51). Verified: snapshot fields; `nociception_history_buffer` unsnapshotted; blur weight-normalised, stamps additive, `min_fire_separation: 3` on M4; noise-off obs is noise-free; `_ICON_CACHE` semantics; `visual-design-reviewer.md` exists and writes `docs/reviews/design_<topic>.md` (matches CP-D); frozen ten unedited; no prior-art collision (Known Bugs rows on `true_obs`/reconstruction cited above corroborate, none contradict).

**Cost of being wrong**: no data loss and no training run at stake. #46 stops CP2.3 on day one (loud, hours). #50 puts a false "true not recorded" caption on the project's central interoceptive signal in every noise-off video and CP2.5 would pass it — a wrong claim about sensory access, reversible by re-render but only once someone notices. #48 makes V1 byte-identity depend on test order and can hide a missing campfire icon behind a green CP2.6. #47 leaves the cold world near-white until the design review catches it.

Reviewed by: plan-reviewer
