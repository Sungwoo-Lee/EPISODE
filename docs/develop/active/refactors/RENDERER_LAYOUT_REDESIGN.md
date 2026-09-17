---
title: "Episode-video renderer redesign: panels that cannot overlap, a faster frame, and a step-scrubbing viewer"
topic: refactors
status: active
created: 2026-09-14
last_updated: 2026-09-17
supersedes: UI_REDESIGN_PROPOSAL.md
---

# Episode-video renderer redesign: panels that cannot overlap, a faster frame, and a step-scrubbing viewer

> **Status**: PLANNED. Revised three times after `plan-reviewer` (first and second pass NOT READY; third pass SOUND WITH CONCERNS, applied in Revision 3). Revision 4 adds extended-range senses (user scope, 2026-09-14); fourth pass SOUND WITH CONCERNS, applied in Revision 5. Revision 6 records user decisions (2026-09-14); fifth pass SOUND WITH CONCERNS, applied in Revision 7. Revision 8 adopts the visual design spec (`docs/reviews/design_episode_dashboard.md`). Revision 9 records the user's answers (2026-09-14) and corrects the temperature scale to a per-episode range. Revision 10 moves every verification world onto maintained configs (new config-maintenance rule). Revision 11 (2026-09-16) re-points every config path after another session archived 227 worlds, names where the regenerated campfire world's values are copied from, and records two new environment behaviours (bushes block animals; faster healing when resting in a bush). **Revision 12 (2026-09-16) retracts Revision 11 §2** — the claim that the maintained `basic/` configs fail to load was produced by a non-resolving YAML read; all of them load, and the plan now requires every config check to go through the resolving loader. **Revision 13 (2026-09-16) corrects the verification matrix after Phase 0b was built and verified**: the three real trained-policy cells cannot be rendered at current code, cells M1 and M2 turned out to be the same world, and a new cell M1x was added. Phase 0a and Phase 0b are **implemented**; Phases 1–5 are plan only. **Revision 17 (2026-09-16) records two user design decisions** — terrain drawn as the square's ground cover with occupants in slots on top of it (variant H), and a 48 px arena square — works out what they cost the surrounding panels, specifies the minimap's admittedly coded encoding, records three cases the design does not solve, and adds a co-occupancy rule to the pixel audit. **Revision 18 (2026-09-16) supersedes Revision 17's square size and window** — the user, given a corrected picture of which panel the numbers belonged to, decided that the grid view shows the **whole 10 × 10 world at a 50 px square** (`ARENA_CELL_PX = ARENA_CELL_MIN_PX = 50`, centre card 564 × 564 px); the 5×5 window is removed, Revision 17's "accepted cost" of a 1–2 px shortfall is retired because 50 px clears both measured floors, and the slot geometry is recomputed. **Revision 19 (2026-09-16) answers the sixth `plan-reviewer` pass (NOT READY)**: the co-occupancy audit rule is rewritten to measure the ink that **survives the painting order** rather than what each artist draws alone (so a token painted *underneath* the bed can no longer pass), §D1.2's arena is reconciled with Revision 18 and covers the two maintained 5×5 worlds, and the Phase-0 speed gate is re-specified for a 100-square arena with one pre-registered failure path and a conditional user question (Q22). **Revision 20 (2026-09-16) answers the seventh `plan-reviewer` pass (SOUND WITH CONCERNS)**: no verdict flip was needed, so it is spec tightening — the co-occupancy rule's two self-asserted preconditions were over-scoped and would have failed a **correct** painter (the agent's own translucent halo, the page's background rectangle), the agent's square outline and the sense-footprint outlines had no painting depth pinned relative to the animals, the survival floor was an unswept number, the minimap's floor had been copied onto an instrument that measures something else, the speed spike's split measured update cost rather than draw cost, and one occluder class (a near-canvas-coloured ground) was invisible to the probe. Every fix narrows **which elements the rule asserts things about**, never **which elements can cover something** — stated explicitly, because the tempting shortcut would silently re-open the draw-order hole Revision 19 closed. **Revision 21 (2026-09-17)** records three decisions taken after Phase 2 and Phase 0d were verified together: the speed gate is accepted as met in substance at 1.78× (Q22 closed by the user), the "this is scenery" floor moves 40 % → 48 % with its measured populations, and this plan's own agent-halo rule is corrected. **Revision 22 (2026-09-17) decides the three contradictions the World map's colour census reported once it could run at all** — it fires 2–4 times per frame on *correct* frames — and decides them **without moving any threshold**: the hiding predator's identity pip is a second paint of its own mark that the census did not know about (an instrument gap, §R22.1); the rim pip's "outside the dot" was geometrically unachievable at the pip size the painter chose, so spec and painter are **both** wrong and the rim pip is retired (§R22.2); and the encoding is extended from three occupants to four by dividing the dot into wedges (§R22.3). §R22.4 states the test that separates "move the constant" from "fix the drawing", §R22.5 records that dropping or repurposing the map would have dissolved all three — **the branch the user weighed and DECLINED: Q21 is answered, the World map stays as a minimap (2026-09-17), and §R22.7's repair is the accepted cost of keeping it** — and §R22.9 confirms the M5 `panel_absent` finding belongs to CP2.7. **§R22.7 was implemented on 2026-09-17**; one finding remains open and it is a constant question, not a painter defect (see the Implementation Report "§R22.7: the World map's wedges, and CP2.8's committed home"). **Revision 23 (2026-09-17) settles that finding — the last thing blocking CP2.8.** The World map gets **its own** survival floor (`MINIMAP_SURVIVAL_MIN = 0.93`) and the grid panel keeps 0.98: one number was serving two instruments whose objects differ by an order of magnitude in size, and §R20.4 had already ruled the map must never reuse the arena's floor — a ruling applied to one of the map's two measurement paths and silently not to the other. The number is placed in a gap **re-measured before it was used**, which changed it: two of the three pre-registered map mutations fire through a different check entirely, so a graded family was registered and the defect side rose from 0.833 to **0.9167** against a worst correct control of **0.9412** (§R23.1, §R23.2). The one-pixel seam is **not** repaired in the painter, on a measured verdict — drawing the wedges edgeless scores a correct picture **above 1.000**, crediting a kind with pixels it never drew (§R23.3). §R23.5 folds the `12_renderer.md` minimap paragraph into **CP6**, which is itemised so it cannot be lost. Phases 0a, 0b, 0c, 0d, 1 and 2 are implemented; Phases 3–5 are plan only.
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
| M3 interoceptive nociception + noise | `…/01-interoNocicept_noise.yaml` | `basic/06-sensory_noise_10x10.yaml` (**renamed from `05-sensory_noise_10x10.yaml` and re-parented, Revision 14**), with an override turning interoceptive nociception on if it is not already |
| M4 campfire thermal | `thermal/campfire_world.yaml` | **regenerated** current-schema `experiment/basic/<NN>-campfire_thermal_<size>.yaml`: campfire obstacle entries with temperature ratios, fire separation, thermal block. The name follows the folder's `NN-description_size` pattern; the developer picks the next free number. |
| M4b body temperature not observed | override of M4 | override of the regenerated M4 (`body_temp_observable: false`) |
| M5 directional smell | `sensory_directional/B_olfaction.yaml` | override of `default.yaml`: `olfactory_grid_range: 1` |
| M6 location sensor | grep of `configs/` | override of `default.yaml` turning the location sensor on |
| M6b noise on, true obs not recorded | M3 world | M3's new source, recorded with `--no-true-obs` |
| E1 smell r1 | `sensory_ladder/B_olf_only.yaml` | same as M5, with vision off |
| E1n smell r1 + noise | override of E1 | `basic/06-sensory_noise_10x10.yaml` (renamed, Revision 14) + `olfactory_grid_range: 1` |
| E2 vision r2 sharp | `sensory_ladder/V5_sharp.yaml` | override of `default.yaml`: vision on, `visual_sensor_range: 2`, blur/occlusion off |
| E2n vision r2 + noise | override of E2 | `basic/06-sensory_noise_10x10.yaml` (renamed, Revision 14) + the E2 overrides |
| E3 anisotropic blur | `sensory_ladder/V1_blur40.yaml` | E2 + `visual_blur_enabled: true` and the blur scale/floor/anisotropy values copied as text from `V1_blur40.yaml` |
| E4 isotropic blur | `sensory_ladder/P1_blur05_iso.yaml` | E2 + blur values copied from `P1_blur05_iso.yaml` (anisotropy 1.0) |
| E5 occlusion | `sensory_ladder/O3_occl_all.yaml` | E2 + `visual_occlusion_enabled: true` and cos/strength copied from `O3_occl_all.yaml`. If that world also needs per-entity occluder settings that are not scalar keys, it becomes a regenerated `experiment/basic/` config instead, recorded at CP0.2. |
| E6 presence modes | `sensory_ladder/Q1_presence_sum.yaml`, `Q2_presence_binary.yaml` | E2 + `visual_value_mode` values copied from those files |
| E7 / E8 / E9 synthetic r3 / r4 / smell-only r4 | overrides of archived-sourced E1/E2 | the same overrides, applied to the new E1/E2 |
| M7 / M8 / M9 trained-policy recordings | real recordings | **unchanged: kept as recordings.** They load through their own saved `run_meta.pkl` (pickled params), never through a config file, so the rule does not touch them. |

**Also withdrawn by this rule:** the archive-config "halt and substitute" branch in §D5.1/CP0.2 (there are no archive sources left).

> **Revision 11 path note (2026-09-16).** The "Old source" column above names the **pre-move** locations. Those files now live under `configs/environment/experiment/archive/` — `archive/thermal/campfire_world.yaml`, `archive/sensory_ladder/*.yaml`, `archive/sensory_directional/*.yaml`, `archive/hypervigilance/*.yaml`. They remain values-only references (copied as text, never loaded). The regenerated campfire config's sourcing is specified in Revision 11 §3. **Revision 12:** the cells routed to `basic/05-sensory_noise_10x10.yaml` (M3, M6b, E1n, E2n) keep that file as their base — Revision 11's "it does not load" fallback is retracted. **Revision 14 (2026-09-16):** that file is now `basic/06-sensory_noise_10x10.yaml` and its world gained body temperature and campfires; the campfire world is now `basic/05-campfire_thermal_10x10.yaml` and its world gained random body init and pouncing predators.

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

Inheritance shape, as measured on 2026-09-16 **before** Revision 14: `00`, `01`, `02` and `03-random_init_10x10` extend `environment/default`; `03-random_init_10x10_ckpt1k` and `04-jump_attack_10x10` extend `03-random_init_10x10`; `05-sensory_noise_10x10` extends `04-jump_attack_10x10`; and `06-campfire_thermal_10x10` extended `environment/default` directly. **Superseded at levels 5 and 6 by Revision 14 (same day):** the thermal world became `05-campfire_thermal_10x10` extending `04-jump_attack_10x10`, and the noise world became `06-sensory_noise_10x10` extending `05-campfire_thermal_10x10`, so the ladder now chains from 03 up to 06. Levels `00`–`03` are unchanged and still extend `environment/default`.

**The rule this revision adds (binding on §D5 and every checkpoint).** Any config load check in this plan MUST use the resolving loader `load_env_params(load_env_config(path))` and MUST NOT use raw `yaml.safe_load` or `Config(yaml.safe_load(...))`. A non-resolving read silently drops every inherited layer and turns an inherited mandatory key into a false "required but missing" — which, given the project's no-fallback rule, looks exactly like a real strict-config failure. This is not a new hazard: it is the already-**fixed** KNOWN_BUGS row *"Config inheritance ignored"* (`22c73bac`, write-up [`EXTENDS_NOT_RESOLVED_IN_TRAINING`](../../archive/EXTENDS_NOT_RESOLVED_IN_TRAINING.md)), where the trainer itself had the same defect. Revision 11 reproduced the fixed bug in a *checking* tool, which is why the plan states the rule rather than trusting a habit. The rule is also stated inline at §D5.1 and enforced as a `Fails if:` at CP0.2.

**What changed in the plan.**
- Revision 11 **§2 is struck through and marked RETRACTED IN FULL**; it is left in place, not deleted, because it was committed (`0cba8eb0`) and a future reader who finds that claim must be able to see it was withdrawn and why.
- `configs/environment/experiment/basic/` is **restored as a valid base** for any fixture cell. The §D5.1 matrix keeps `default.yaml` + in-memory overrides wherever Revision 10 independently preferred expressing a one-key variation as an override rather than a new file — that preference stands on its own and was never about loading.
- **M3 goes back to `basic/05-sensory_noise_10x10.yaml`** as its base (with the nociception override), as Revision 10 specified; M6b, E1n and E2n follow M3. *(That file is `basic/06-sensory_noise_10x10.yaml` since Revision 14, with a changed world — see there.)* The Revision 10 mapping-table note is corrected the same way.
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

## Revision 14 2026-09-16 (the basic ladder now chains at levels 5 and 6 — cell M4's world CHANGED CONTENT)

**What this revision is about, in plain words.** The project's "basic curriculum" is a ladder of worlds that get harder as you climb: level 00 is a toy 5x5 world with a predator that never moves, and each level above adds one difficulty. Two rungs of that ladder were not actually stacked on the rung below them. The temperature world (campfires, body heat) sat on the shared base config instead of on the jump/pounce world beneath it, and the sensory-noise world sat on the jump world rather than on the temperature world. The user asked for the two to be re-numbered and re-parented so that each rung inherits the one below. **Only levels 5 and 6 changed; levels 00–04 were deliberately left alone** (00 and 01 are 5x5 worlds and 02/03 are 10x10, so chaining those is a different and bigger change).

The two files, with their `extends:` line:

| Before | After |
|---|---|
| `basic/06-campfire_thermal_10x10.yaml`, extending `environment/default` | `basic/05-campfire_thermal_10x10.yaml`, extending `basic/04-jump_attack_10x10` |
| `basic/05-sensory_noise_10x10.yaml`, extending `basic/04-jump_attack_10x10` | `basic/06-sensory_noise_10x10.yaml`, extending `basic/05-campfire_thermal_10x10` |

**The headline for this plan: cell M4's world changed CONTENT, not just its filename.** M4 is the fixture the dashboard's temperature drawing is verified against. Because its config now inherits from level 04 instead of from the shared base, the campfire world gained three things it never had: episodes that **start hungry and/or injured** at random (level 03's `body:` block), **predators that pounce** from two or three cells away and hit half the time (level 04's `attack_range` / `attack_success_rate`), and level 03's scene counts (food 1–4 rather than 2–6; ambush predators 2–12 rather than 2–4; predator and rabbit 0–2 rather than 1–2). Measured through the resolving loader, **37 of 190 resolved `EnvParams` fields differ** from the pre-re-level campfire world. **Do not read fixtures recorded before 2026-09-16 and after it as the same world.**

Cell M3's world (and M6b, E1n, E2n, which follow it) changed too, in the other direction: the noise world now sits on top of the temperature world, so **39 of 190 fields** differ from its pre-re-level self, its observation grows from 27 numbers to **33** (it gains Body Temperature and Thermoception), and its arena gains campfires.

**What was verified, and how.** Every claim here was measured by loading the configs through the trainer's own resolving loader — `load_env_params(load_env_config(path))` — never by a raw `yaml.safe_load`, per the Revision 12 loader rule.

| Check | Result |
|---|---|
| Both worlds load at current code | ✅ both resolve to 190 `EnvParams` fields |
| Campfire world, before vs after re-parenting | **37 of 190** fields differ (pounce knobs, predator damage/detection/stamina, `random_start_injury` / `random_start_nutrition`, `start_injury_high` 50 → 100, resource counts and the resource-slot arrays, entity counts 39 → 45) |
| Noise world, before vs after re-parenting | **39 of 190** fields differ (`thermal_enabled` false → true and the whole `thermal_*` block, `min/max_temperature` 0 → ±15, the obstacle arrays gaining campfire and tree, entity counts 42 → 45) |
| The campfire world keeps level 04's pouncing predators | ✅ `animal_attack_range_low/high` `[2,3]`, `animal_attack_success_rate` 0.5, `has_attack_feature` true |
| The campfire world's own obstacle list still replaces the inherited one | ✅ campfire / rock / tree / bush present; bush keeps `blocks_animals: true` |
| The noise world's "interoception kept CLEAN" claim survives re-parenting | ✅ `noise_sigmas` identical before and after; satiation, interoceptive and extero nociception all 0.0 |
| Observation layout | campfire world 33 dims (unchanged); noise world 27 → **33** dims |
| Divergence from the **archived** campfire world | **38 of 190** fields, where before the re-level exactly **1** did (`obs_blocks_animals`). The one-field claim in the Phase 0b Verification Report was true only on the old parent; it is marked superseded there, and the config header and the fixture generator's `provenance` string are corrected |

**Frame baseline: which cells moved and which did not.** The CP0.2 fixtures were regenerated and `record-frames --force --note` was re-run (the note records the re-level as the reason). Comparing the eight pinned V1 frames per cell, before against after:

| Cell | World | Frames | Fixture (`run_meta`) |
|---|---|---|---|
| M1 | `default.yaml` — untouched by this change | **all 8 identical** (`20a67f21…` → `20a67f21…`) | unchanged |
| M2 | `default.yaml` — untouched (and a known duplicate of M1, Revision 13) | **all 8 identical** | unchanged |
| M4 | the campfire world, **re-parented** | **all 8 differ** (`994ae6a8…` → `3da423ec…`, last frame `caf849dd…` → `a8cfe9aa…`) | changed |

That is the expected and wanted result: the two cells whose config did not change did not move a pixel, which is what rules out an accidental change to the frozen V1 path; the one cell whose world genuinely changed moved from the first frame, which is what a real world change looks like. Unlike the previous re-record (a metadata-only change), these hashes were **expected** to differ.

**Repairs the rename required.** `scripts/eval/make_render_fixture_recordings.py` (its `CAMPFIRE` and `NOISE_WORLD` constants, plus the corrected `provenance` text); `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` (the row that named the campfire config as the thing to update "if that config is renamed" — it now names both constants); `tests/env/test_v1_path_guard.py` (a fake-repo path string); and two env tests that hard-coded the old noise path, one of which needed more than a path edit — see below. The frozen V1 files were not touched and `accept` was never run.

**One consequence nobody predicted, worth recording.** `tests/env/test_truncation_not_death.py` pinned the noise world and drove the agent in one direction until it died, asserting the cause of death was **starvation**. On the re-parented world it now **freezes to death first** (`termination_reason` 5, "frozen or overheated", instead of 2) — the temperature world's baseline is cold, so an agent that never warms up runs out of heat before it runs out of food. The test was repointed at `basic/04-jump_attack_10x10.yaml`, the highest rung without the temperature system, which reproduces the behaviour it was written against exactly: the old noise world *was* level 04 plus perceptual noise, and perceptual noise perturbs the observation only — it changes no transition, no body update and no termination rule. The wider point for this plan: **level 06 now has a third way to die**, and any measurement on it that assumes starvation or predation are the only outcomes needs re-checking.

---

## Revision 15 2026-09-16 (after Phase 0c verification: defect D2 was misclassified, and the audit measures ink differently from the plan)

**What this revision is about, in plain words.** Phase 0c built the measuring instrument this whole redesign depends on: a script that takes a real rendered video frame and reports, in pixels, where drawn content collides. Verifying it turned up three things the plan itself had wrong or had left unsaid, all found by measuring rather than by re-reading.

1. **Defect D2 is not the kind of defect this plan says it is.** The plan's defect table calls it "text on top of other text" — the words `REAL: --` printed over the title of the extero-nociception panel. Measured in pixels, the two strings **never touch**: they sit 1.55 pixels apart and share no pixel at all, before or after this plan's 1-pixel tolerance. The real defect is different and, if anything, worse: the `REAL: --` readout is drawn **outside the panel it belongs to**, in the narrow strip above that panel which belongs to the title alone — so a viewer reads it as part of the title line rather than as the panel's own number. D2 is reclassified from *text-on-text* to an **escaped label** (content drawn outside its allotted box).

   This is not an artefact of the campfire world having changed in Revision 14. The verifier re-derived it from the frozen renderer's own arithmetic: the readout is anchored at the bar's top edge plus its label offset, which works out to **exactly** the panel card's top edge for **any** value of the renderer's squeeze factor, and the panel title is anchored a constant 0.015 of the column height above that. The two can therefore never close the gap, in any world, at any squeeze. (`renderer.py` `draw_dual_capsule_bar` at `:328`, `draw_pod_frame` at `:378`, the pod loop at `:992`–`:1022`.)

2. **Defect D5 reproduces on the default world today, with pixel evidence.** The plan recorded D5 — a vitals row's observed value colliding with the next row's true value — from a frame that was never kept. It is real and current: on the default world's fixture, three separate `OBS:` × `REAL:` collisions of 17, 17 and 16 pixels, in the left-hand vitals column. Found by the audit unprompted, then reproduced by the verifier.

3. **The audit measures an element's ink by isolating it, not by hiding it**, which is the opposite of what §D5.2 said. The plan is what changes here, because isolation is the better measurement — see the §D5.2 item 2 note for the measured reason, which is narrower than the reason originally given for the change.

**What changes in the plan.** §A2's D2 row and its class; §A2 gains a note that D5 is confirmed current; §D5.2 item 2 is rewritten to specify isolation and to record what the two methods actually measure. Nothing about the architecture, the layout, the checkpoints or any later phase changes.

---

## Revision 16 2026-09-16 (after the Phase 0c fix pass: the audit gains negative controls, and a thirteenth defect is numbered)

**What this revision is about, in plain words.** The measuring instrument this whole redesign will be judged by — the script that takes a rendered video frame and reports, in pixels, where drawn content collides — could not previously be told apart from an instrument that flags *everything*. A code review found that if the function measuring "which pixels did this element put on the canvas" had simply answered "all of them", every one of its 18 tests would still have passed and all seven known defects would still have been "found", because a test that asks *did it find the defect* measures sensitivity and never discrimination. The fix pass added the tests a permanently-sounding alarm fails. While re-examining a class of finding the original pass had called harmless, it also found a real layout defect nobody had noticed. This revision gives that defect a number — **D13** — and records what the verification measured.

**D13, in plain words.** Under the arena, the renderer draws a small colour bar showing the temperature scale, with the lowest and highest temperature printed at its two ends. The bar is painted over the leading corner of the high-end label, so the reader sees a clipped `+` sign. The cause is arithmetic rather than chance: the bar is drawn as 52 segments, each made slightly wider than its share so no hairline gaps show between them, and that extra width applies to the last segment too — carrying the bar past the point where the label begins. Both numbers are constants in the source, so this happens on **every thermal frame ever rendered**, in every world, at every squeeze factor. Measured on the campfire fixture frame: 2 of the label's 70 pixels of ink are replaced by the bar's colour exactly.

**What changes in the plan.** §A2 gains a **D13** row, a root-cause bullet, and a note that `text_over_fill` is no longer reported as a uniformly benign class — it splits into 5 benign and 1 covered on the campfire frame. The CP0.3 checkpoint note records the number. Nothing about the architecture, the layout, the other checkpoints or any later phase changes. Hand-off: **`bug-curator`** extends the episode-video dashboard row in `KNOWN_BUGS.md`, which covers D1–D9, D11 and D12 but not this defect.

---

## Revision 17 2026-09-16 (user decisions: terrain as ground cover, and a 48 px grid cell)

**What this revision is about, in plain words.** A square of the world can hold more than one thing at a time — the agent standing on a bush, a predator and a rabbit in the same square, a piece of food lying on a rock. The dashboard draws one picture per square, so it has to say "two things are here" somehow. The old renderer solved this with hand-drawn combination pictures (an "agent in a bush" image, an "agent caught by a predator" image), and when a combination had no picture, nothing was drawn. The redesign's new flat icon set has no combination pictures at all, and the sketch painter draws every occupant on top of the same centre point — so two white discs land exactly on each other and whichever name comes later in the alphabet wins, and the agent's soft halo is wider than the entire bush drawing, which is why an agent standing in a bush currently renders as an agent alone. The small world map in the left column is worse still: the agent's dot is drawn over the other animals' dots, so a predator sharing the agent's square disappears.

Two rounds of design mock-ups explored the problem (the sheets and the generators live in `tmp/20260916_design_cell_cooccupancy/` and `tmp/20260916_design_cell_cooccupancy_r2/`). **The user has decided two things, and this revision records them as settled, not as proposals:**

1. **Terrain becomes the floor of the square, not a picture in the middle of it** (variant **H**, "terrain bed + token"). A bush, a rock, a tree or a campfire is drawn as ground cover filling the square, leaving a margin of the square's own temperature colour showing all round. Because the ground cover is the floor, it costs the animals no room: a lone agent standing on a bush is drawn at exactly the size it would be on an empty square. A second and a third occupant stand side by side in the middle of the square. The user rejected every coded alternative — corner dots, folded corners, a rim legend — on an explicit principle: **a viewer should recognise both occupants by seeing them, not by decoding a legend.**
2. **A 48-pixel square in the grid view**, up from the 28 px the design round measured as "today's cell". This was the round's central finding: at 28 px no literal (non-coded) variant works for any shared square, and 48 px is where the hard cases come within a pixel of legibility.

Two things follow that the user must know, and the rest of this section works them out: whether the surrounding panels can pay for a 48 px square (they can in the grid view, and cannot in the small world map), and that 48 px is 1–2 px under variant H's own measured floor for the hardest squares.

---

### R17.1 What can actually share a square (measured, not assumed)

The round-2 generator enumerated the reachable multi-occupant states by reading the environment rather than guessing: **64 distinct multi-occupant square states in the default world, 102 once the thermal world's campfire and tree are included** (re-derived independently while writing this revision: `count_reachable` in `tmp/20260916_design_cell_cooccupancy_r2/cooccupancy_r2.py`). Nobody hand-draws 102 pictures — which is what killed the "just draw more combination sprites" option — but the set is **not flat**. It is three independent layers, and a rule over three layers generates every state from nine drawings:

```
terrain (0 or 1 of rock / bush / tree / campfire)  ×  statics (food, trap)  ×  movers (agent, predator, rabbit)
```

The five reachability rules the generator read off `src/environment/core.py`, kept here because the painter and its audit both depend on them:

| | Rule | Consequence for the painter |
|---|---|---|
| R1 | Reset places every non-agent entity on a **distinct** square (`resolve_overlaps_global`, scan order res → pred → obs → neutral) | **At most one terrain per square, ever.** No two statics at step 0. The "bed" layer is therefore single-valued and never has to compose two terrains |
| R2 | The agent is placed **outside** that scan (`core.py:1460`) | Agent + anything is reachable at step 0, including agent + tree — a square the agent can never *walk* onto |
| R3 | Animals move against `obs_blocking | obs_blocks_animals` (`core.py:609`) | Predator and rabbit can **never** stand on a bush or a tree. `agent + bush + predator` is unreachable |
| R4 | Resources move only on respawn, and that path applies **no** overlap resolution (`core.py:703-712`) | food-on-bush, food-on-rock, food-on-trap are reachable but **rare** — respawn is their only route |
| R5 | Inactive slots are re-parked off-grid at `(height, width)` each step (`core.py:682`) | No phantom sharing; the painter must skip inactive slots, as Figure 3's sketch already does |

### R17.2 The layout consequence, with the arithmetic

**Where the numbers come from.** Figure 3 is the canonical layout (Decided questions, 2026-09-14) and its geometry is in `renderer_layout_redesign/fig03_proposed_dashboard.py` with `dashboard_style.py`: outer gutter 24 px, gap between cards 16 px, card padding 16 px, header 64 px; left column 320 px wide; grid-view card `view × 96 + 64` = **544 px** wide for a 5×5 window; right column what remains, **496 px**, against a stated minimum of 440 px. Vertically: content runs 64 → 880 = 816 px; the grid card is 48 + 480 + 16 = **544 px** tall; the sensor band starts at 624 and is **256 px** tall against a stated minimum of 200. So the layout as approved carries **56 px of width slack** (right column) and **56 px of height slack** (sensor band) and no more.

The left column holds two cards. Interoception is `76 × rows + 124`: **504 px** in the thermal world (five rows) and **428 px** in the default world (four). The World map card takes the remainder, capped at 350 px, so its map square is `min(320 − 32, h − 46 − 16)` = **234 px** in the thermal world and **288 px** in the default world — that is, **23.4 px and 28.8 px per world square**. This is the "~280 px" the decision compares against: it is the **small world map**, not the grid view.

> **Read §R17.2 as history.** Its question — which panel the 48 px belongs to — was answered by the user in **Revision 18**: the grid view shows the **whole world at a 50 px square**, and the World map keeps its ~23–29 px squares. The measured facts below (what each panel costs, why the World map cannot grow) are unchanged and still load-bearing; only the chosen square size moved, 48 → 50 px, and the final layout arithmetic is re-derived in §R18.1.

Now the three panels a 48 px square could refer to:

| Panel | Today (Figure 3) | At a 48 px square | Verdict |
|---|---|---|---|
| **Grid view, 5×5 window** | 96 px per square, 480 px of drawing in a 544 px card | 5 × 48 = 240 px of drawing, a 304 px card | **Closes with 240 px to spare.** The floor is met twice over; the neighbours *gain* space rather than give any up |
| **Grid view widened to the whole 10×10 world** | – | 10 × 48 = **480 px**, i.e. **exactly the drawing area the card already has**; card stays 544 × 544 | **Closes exactly, at zero cost to every neighbour.** The centre card's geometry is unchanged to the pixel; left, right and band boxes are untouched |
| **World map (minimap), 10×10** | 23.4 px (thermal) / 28.8 px (default) per square | needs 480 + 32 = **512 px wide** and 480 + 46 + 16 = **542 px tall** | **Does not close** — see below |

**Why the World map does not close, in numbers.** Width could just about be bought: the column would grow 320 → 512 (+192 px), the right column's entire 56 px of slack would be spent (pinning it at its 440 px minimum, with nothing left for the thermoception diamond and its shared scale), and the remaining 136 px would have to come out of the grid card, dropping it 544 → 408 px, i.e. 68.8 px per grid square — still above the 48 px floor. So width is expensive but survivable. **Height is not.** The left column has 816 px. Interoception measures 504 px in the thermal world, leaving 296 px for the World card after the 16 px gap; a 48 px map needs 542. That is **246 px short in the thermal world and 170 px short in the default world**, and there is nothing in that column to take it from — the only other card is Interoception, and shrinking a card below its measured content is precisely what §D1.2's fit-or-fail exists to forbid. **Stated plainly for the user: the small world map cannot be drawn at 48 px squares on a 1440 × 896 canvas without moving Interoception out of the left column, which would be a different layout from Figure 3.** This is consistent with — and is the measured reason for — the minimap rule in §R17.4, where show-don't-encode is given up deliberately.

**One question this raises, and it is the user's to answer, not the developer's.** The decision says "a 48 px grid cell, up from today's 28 px", but the two numbers belong to two different panels: 28.8 px is today's **World map** square, while today's **grid view** square is 96 px. The 480 px figure in the decision is exactly a 10×10 world at 48 px — which fits the grid-view card to the pixel. The reading this plan adopts unless the user says otherwise is therefore: **48 px is the floor and the drawing size for the grid view's squares, and the grid view may show the whole world where the whole world fits at 48 px** (see §R17.6 for what that changes). The World map keeps its ~23–29 px squares and its coded encoding. If the user instead meant that the World map itself should grow, the numbers above say what would have to move.

> **Answered, Revision 18 (2026-09-16).** The user was asked (Q20) and chose the whole world in the grid view, at **50 px** rather than 48 px. The World map keeps its ~23–29 px squares and the coded encoding of §R17.4. The 48 px reading in the paragraph above is superseded; §R18.1 carries the layout arithmetic at 50 px.

**Worlds that do not fit.** At 48 px the grid-view card holds at most 10 squares across (544 − 64 = 480). An 11×11 or larger world cannot be shown whole at 48 px, so the window rule (§D7.3) still applies above 10 — it does not become dead code, and the fallback order in §D7.7 item 3 still decides what happens. No maintained config has a world above 10×10 today (`configs/environment/default.yaml`: `height: 10`, `width: 10`). **At Revision 18's 50 px the ceiling is the same 10 squares** (the binding constraint becomes the sensor band's 200 px minimum, which caps a whole-world square at 53 px), so the fallback's scope is unchanged — but see §R18.2 item 9 for a defect in the fallback's shrink step that must be fixed in Phase 1.

### R17.3 The H rule, specified to implement

Terminology, fixed here so painter, test and audit use one vocabulary: **ground** = the square's own fill (temperature colour, or the neutral track when thermal is off); **bed** = the terrain ground cover; **token** = one occupant's drawing; **slot** = the box a token is drawn for; **h** = a token's ink half-extent in pixels, the single number that decides legibility.

1. **Ground.** Unchanged from Figure 3: rounded square, radius 8, 2 px seam of card white between squares, no grid lines, no numbers (§D5.2 item 10 still holds).
2. **Bed.** Terrain (rock, bush, tree, campfire; **at most one**, by R1) is drawn full-bleed, inset by `BED_MARGIN = 0.14 × cell` on every side, so a ring of the square's own temperature colour always shows. Drawn above the ground and below every token. **Revision 20:** that ordering is now a pinned constant with a test (bed zorder strictly below token zorder, §R20.1), so a bed's translucent parts — the campfire's glow at alpha 0.28 — can never be "drawn after" a token; and **each bed is exactly one artist** (a compound path, or a `PatchCollection` with per-subpath face colours where a bed needs more than one colour), so the audit's ≥ 40 % area test measures it whole (§R20.8). A bed is *not* a glyph being covered — it is the floor the occupants stand on — so a token over a bed is not the occlusion the brief rules out, and the audit must not count it as one (measured bed-under-token ink at 48 px: 0–772 px per square, by design; at Revision 18's 50 px square the same geometry scales to roughly 0–840 px, an illustrative range rather than a pinned assertion).
3. **Tokens, by non-terrain occupant count `n`** (terrain never counts, because it is the floor):
   - `n = 0` — bed only, or bare ground.
   - *(Pixel values in this item are quoted at the 48 px square of Revision 17. **Revision 18's decided square is 50 px**; the formulas are unchanged and §R18.3 carries the recomputed values — `h` = 15.00 / 10.35 / 10.12 px.)*
   - `n = 1` — one centred token at `h = 0.30 × cell` (**14.4 px at a 48 px square; 15.00 px at 50 px**): identical to an unshared square. This is the property the whole variant was chosen for.
   - `n = 2` — one row of two in a band of height `0.60 × cell` centred on the square, side margin `0.05 × cell`; column width `w = (cell − 2 × margin) / 2`; `h = min(w, band_height) / 2 × 0.92` → **9.9 px at 48 px; 10.35 px at 50 px**.
   - `n = 3, 4` — **two rows of two** in a band of height `0.88 × cell`, the last row centred when it holds one, so three reads as 2-over-1 rather than as a gap; `h` → **9.7 px at 48 px; 10.12 px at 50 px**. This is the degeneration recorded in §R17.5: from the third occupant on, the tokens take almost the whole square and the bed shows only as its margin.
   - A single row of three was tried and rejected by measurement: it collapses `h` to `0.135 × cell` and pushes the four-way minimum to 75 px — an artefact of the layout, not of the idea.
4. **Order is explicit, never alphabetical.** `CELL_PRIORITY = ("agent", "predator", "hiding_predator", "food", "neutral")`, filled left-to-right then top-to-bottom. The observed overdraw bug is exactly what an alphabetical `sorted()` over entity names buys; the constant is module-level with a test that every entity name the matrix can place appears in it.
5. **Slots are computed before anything is drawn.** The painter builds the slot list from `(bed?, occupants)` and then draws; it never draws concentrically and relies on z-order. Measured on the mock at 48 px, **glyph-on-glyph ink is 0 px in every reachable case** — that zero is what §R17.7's audit rule re-measures on the real painter.
6. **Companion forms.** Each token has a reduced form drawn *for* a small box rather than scaled down into one, keeping exactly one named identifying mark whose short dimension never falls below a stated fraction of `h`: food 0.34 (green leaf), predator 0.30 (amber eye slit), rabbit 0.30 (ear gap), trap 0.32 (amber spike tip), agent 0.55 (white chevron). These fractions are constants in the painter, because they are what makes a minimum square size computable in a test rather than argued about.
7. **The white keyline, not a white platter.** A shared token is separated from the bed by a white keyline at radius **exactly `h`** — not 1.06 h. *(Corrected Revision 19, #55: the mock strokes it **centred** on `h` at `lw = max(0.8, h/8) pt` — 1.29 px at the two-mover size — not as "1 px inside `h`". Centred, it puts half the stroke outside `h`, leaving a ~0.5 px geometric gap between adjacent slots that lies inside the anti-aliasing fringe. **The painter's constant is the stroke width `h/8` with the stroke **inset** so its outer edge lies at `h`**, and §R19.4 item 2's Phase 0d control measures at 50 px what the audit then reads there. If it reads non-zero, the fix is this geometry — never a looser tolerance.)* At 1.06 h the keylines of two adjacent slots touch, and that invisible white-on-white kiss was the whole of the bed family's residual measured "glyph overlap". Keeping the keyline inside `h` is what makes the 0 px measurement mean what it says, and it is also what keeps §R17.7's connected-component rule honest.
8. **The agent's indigo outline and last-action chevron.**
   - The **square outline** (2 px iris rounded rectangle on the *square*) is unchanged and is unaffected by sharing. **Revision 20 (#64): it is pinned BELOW token zorder.** Tokens never reach it, so this is no visual change — the outline still reads as the square's border — but drawn above, its inner fringe sits 0.1–1.1 px from a four-way token's edge and costs that token 1–2 % of its pixels, right at the survival floor. It stays in the occluder set: raise it above the tokens later and the floor fires, which is exactly what the rule is for. It, not the token's size, is what says which square the agent is in — which is why the token may shrink without the agent becoming hard to find.
   - The **halo is dropped whenever the square holds anything else at all — any occupant *or a bed*.** *(**Corrected in Revision 21, 2026-09-17.** This clause originally read "whenever the square is shared (`n ≥ 2`)", and since terrain deliberately does not count towards `n`, a lone agent standing on a bush was `n = 1` and **kept** its halo. Measured on a rendered frame in Phase 2: that halo reaches `0.396 × cell` from the square's centre while the bed beneath it spans only `0.36 × cell` from the centre — the halo is wider than the entire floor it stands on, so "agent in a bush" still rendered as an agent alone. That is the original defect in a new form, inside this plan's own rule text. The painter implements the corrected rule; the bare-ground case is unchanged, where the halo covers only empty ground and makes the agent easy to find.)* At full size the agent marker carries a 16 % iris halo at `1.32 × r`; in a shared square that halo is ink that spills past `h` onto the neighbour, and it was the entirety of H's measured overlap before it was removed. Concretely: at `h = 0.30 × cell` the halo reaches `0.396 × cell` from the centre, while the whole bush glyph reaches only `0.261 × cell` — the halo is wider than the drawing it is supposed to sit beside, which is the mechanism behind "agent-in-bush renders as agent alone".
   - The **white ring** stays at every size (`lw = max(0.9, h / 8) pt`), and the **chevron** stays inside the token at `0.62 × h` in the last action's direction, with the dot for Rest/Eat. At 48 px the chevron is 6.1 px long when two occupants share and 6.0 px with four — on the 6 px legibility line; **at Revision 18's 50 px square it is 6.42 px and 6.27 px**, clearing it with room. **The floor is on the chevron, not on `h` (clarified Revision 19, #60): `0.62 × h ≥ 6 px`**, equivalently `h ≥ 9.68 px` — which is what the 6.42 / 6.27 px figures above are being compared against, and which the four-way case clears by 0.44 px. Below it the chevron is not legible and the painter raises rather than drawing an unreadable one; the floor joins the values `test_dashboard_cells.py` recomputes.
   - The action pill in the card's title row is unchanged (Q4).

### R17.4 The minimap: where colour is a code, and the page says so

At the World map's ~20–29 px square, a token's mark would be under 3 px and would not survive video compression. Show-don't-encode **cannot** survive here, and pretending otherwise would be the one dishonest part of this design. The map's job is therefore explicitly narrowed: **it answers *where*, and the grid view answers *what*.**

- **Terrain tints the whole square** — the bed idea one scale down — over the temperature tint at the existing 75 % alpha.
- **One mover:** a dot, as today (agent iris at 64 % of the square with a 2 px white ring; others 48–52 % with a 1.2 px ring).
- **Two movers:** one dot **split into two half-discs** of the same diameter, each in its occupant's colour, divided by a 0.8 px white line.
- ~~**Three or more:** the third becomes a **rim pip** at the square's lower-right, 12 % of the square, outside the dot.~~ **SUPERSEDED by Revision 22 §R22.2–§R22.3 (2026-09-17): the rim pip is retired and the dot is divided into `n` wedges for `n = 1…4`** (one whole dot, two half-discs, three at 120°, four at 90°). Measured, "outside the dot" was **not achievable** as written: a rim pip must satisfy `r_p ≤ 0.1016 × cell` to sit outside the `0.30 × cell` dot *and* inside the square, so the painter's `0.12 × cell` was infeasible by construction, and a pip small enough to comply has a 4–7 px colour core that neither the census nor video compression can be relied on to preserve. The ceiling is **four kinds**, matching the grid panel's four slots; `CELL_PRIORITY` order is unchanged, so the agent is never the one dropped.
- Statics (food, trap) count as occupants for the split; terrain does not, because it is the tint.
- **Collision to resolve, named so it is not discovered late:** the adopted design review already spends a pip — an **amber pip at 34 % of dot diameter, centred inside the dot** — to tell the hiding predator from the predator (design review finding 3). ~~The occupancy pip must be distinguishable from it: the identity pip is **inside** the dot, the occupancy pip sits **on the square's rim**, and a test asserts the two can appear on one square without sharing a pixel.~~ **Revision 22:** with the rim pip retired there is no occupancy pip to collide with, so this clause is discharged rather than met — and the **identity pip moves from the square's centre into its owner's own wedge** for `n ≥ 2`, because at the centre it straddles every wedge and eats a *neighbouring* kind's colour (§R22.1). The identity pip is also the reason the hiding predator's map mark is **two** palette colours rather than one, which the audit's census must know (§R22.1).
- **Two painter-vs-spec drifts recorded while deciding Revision 22, neither load-bearing, so neither is fixed here:** the dot sizes above (agent 64 % of the square, others 48–52 %) are **not** what ships — `painters.py` draws every mover at a uniform `0.30 × cell` radius, i.e. 60 % of the square; and the white ring widths are 1.2 px for the dot and 0.8 px for a pip. The uniform size is defensible (the map answers *where*, and a size code would be a second legend), but the spec and the painter should be made to agree at CP-D, where `visual-design-reviewer` looks at the rendered map.
- **It is stated on the page, not hidden.** The World card carries a caption in words. ~~e.g. *"Shared squares: two occupants split the dot, a third is a corner pip. Colour identifies them here; the grid view shows what they are."*~~ **The example is updated with the encoding (Revision 22 §R22.8), because a caption describing a mark the painter no longer draws is the §R19.2 (#56) failure mode — two parts of one system disagreeing, with the reader building from the stale one.** It now reads, e.g.: *"Shared squares: the dot is divided between the occupants, up to four. Colour identifies them here; the grid view shows what they are."* Two conditions on any rewording: it must still contain the substring the audit keys on (`shared square`, `SHARED_CAPTION`), and it must still say **in words** that colour is the code here — that sentence is the honesty condition this whole section's exemption from Q18 rests on. The audit checks the caption is present on any frame whose snapshot contains a shared square (§R17.7).

### R17.5 Cases this design does not solve (recorded, not buried)

1. **Multiplicity.** Two predators in one square render as **one** predator token. No variant in either round counts occupants, and the 64/102 reachable-state enumeration is over *kinds*, not instances. Counting would need a badge or a numeral — a legend, which the principle rules out — so it is not done. **Consequence for verification:** the audit's ground truth must be the number of *distinct kinds* in a square, never the number of entity instances, or it will report failures that are not failures.
2. **H degenerates to equal tiles from three occupants up.** The "a lone occupant keeps full size" property holds for one occupant and the bed; with three or four, the tokens take the band and the bed survives only as its margin, and every occupant is the same size (no focal point). Measured minimum square sizes: **49 px** for the binding two-mover cases (agent + predator, predator + rabbit, agent + rock + predator) and **50 px** for the four-way.

> **Retired by Revision 18 (2026-09-16).** The rest of this item as originally written recorded an *accepted cost*: at the then-decided 48 px square the binding marks (the predator's amber eye slit, the rabbit's ear gap) measured 2.97 px against a 3.0 px chroma-survival heuristic, 1 px under the two-mover floor and 2 px under the four-way one, with "a 50 px square" named as the first remedy. **The user has since decided the 50 px square** (Revision 18), which clears both floors — the marks measure 3.105 px and 3.036 px — so there is no longer any accepted cost here and the paragraph is not carried forward. What remains true is the sentence above it: variant H degenerates to equal tiles from the third occupant up, and a three- or four-way square has no focal point. That is a property of the design and is **not** retired.
3. **A resource stranded on a blocking tree.** By R4, respawn applies no overlap resolution, so food can land on a tree — a square the agent can never walk onto. The frame will show a tree bed with a food token on it, which is *truthful* but does not tell the viewer the food is unreachable. No marking is proposed, because any marking is a legend. Recorded here so nobody later "fixes" the picture by hiding the food.
4. **Two statics on one square** (food + trap) is reachable only by respawn and is drawn by the same two-occupant rule; it has no special case and no special mark.
5. **Five or more kinds in one square are drawn by neither panel (added Revision 22 §R22.3 item 6).** The grid panel's composition defines `n = 1…4` (§R17.3 item 3) and the World map's encoding now matches that ceiling, so a square holding **five or more distinct kinds** has no specified drawing in either picture. `CELL_PRIORITY` decides who is dropped, and because the agent is first it is never the one dropped — the map keeps answering *where the agent is*, which is its stated job. This is recorded rather than fixed: no episode of any of the nine matrix cells produces even a **four**-kind square (measured — the four-way archetype had to be synthesised), so a fifth is not a case worth designing for today. **Consequence for verification:** the co-occupancy rules' ground truth is the kinds the encoding is *specified* to show, and a square exceeding the ceiling must be reported as out of scope rather than silently passed — if one ever appears, that is the signal to design for it, not to widen a tolerance.

### R17.6 What changes in the phases that are not built yet

Phases 0a–0c are complete. The changes below land in the phases that follow, and every one of them is a *change to this plan*, not a new plan.

- **Phase 0d (new, small): the audit learns to see squares.** `scripts/eval/render_layout_audit.py` gains the co-occupancy rule in §R17.7 with its own positive and negative controls, *before* Phase 1, so the instrument exists when the painter arrives. No other Phase-0 artefact changes; the V1 path guard and the frame baseline are untouched.
- **Phase 1 (registry and packer).**
  - *(Superseded by Revision 18 §R18.5: the square is **50 px**, not 48, and the grid view shows the whole world rather than a window. Implement from §R18.5.)*
  - `layout.py`: `ARENA_CELL_MIN_PX` **32 → 48**, and a new `ARENA_CELL_PX = 48` target. The fallback order of §D7.7 item 3 is unchanged in shape; its first question becomes whether the world fits whole at 48 px, then the local window.
  - `panels.py`: the arena row's min size becomes `W × 48 px`; the minimap row's min size gains the height of the shared-square caption line.
  - `test_dashboard_layout.py`: the arena box is exactly `W × 48` px; a 10×10 window fits the Figure-3 centre card with the neighbours' boxes unchanged; a world too large to show whole at 48 px takes the documented fallback rather than silently shrinking below the floor.
- **Phase 2 (painters).**
  - **New module `src/environment/dashboard/cells.py`** owning square composition: the bed table, the companion-form table, `CELL_PRIORITY`, the slot packer, `BED_MARGIN`, and the identifying-mark fractions. Kept out of `painters.py` so the arena painter stays a caller.
  - **Assets.** Terrain now needs a **bed** form as well as its map/legend glyph; tokens need a **companion** form. The `assets/dashboard_icons/` test becomes: every entity the matrix can place has a bed form or a companion form as appropriate, or is on the glyph-fallback list.
  - **Agent marker** per §R17.3 item 8 (halo dropped when shared; ring and chevron kept; square outline untouched).
  - **Fixtures must contain shared squares.** `make_render_fixture_recordings.py` gains a report of which co-occupancy archetypes each cell's episodes actually contain (agent + terrain, two movers, three-way, four-way, food-on-terrain), because a seeded random policy is not guaranteed to produce them. An archetype the matrix never reaches is rendered from a **synthetic snapshot labelled as derived input**, the same precedent as the existing stress variant. *Fails if:* a checked archetype is neither found nor synthesised, or a synthetic one is not labelled.
  - `test_dashboard_frames.py` gains the co-occupancy cases and the mutation below.
- **Phase 3 (entry point).** `layout_signature()` gains the arena square size and the window rule, so a concatenated video cannot switch square size or window mid-video.
- **Phase 4 (viewer).** `/api/values` gains the per-square occupant list, so the viewer can name what shares a square; the page's grid draws the same rule, and if its viewport forces squares under 48 px (**50 px since Revision 18**) it **says so** rather than shrinking silently.
- **Docs.** `docs/environment/12_renderer.md` gains the square-composition rule (bed / token / slot vocabulary), the minimap's coded encoding and its on-page statement, and the three unsolved cases. No config key changes; `CONFIG_CRITICAL_SETTINGS.md` unchanged; `SCRIPTS_DEPENDENCY_MAP.md` unchanged by this revision (no script is added, moved or renamed — Phase 0d edits an existing one).

### R17.7 The audit's co-occupancy check (Phase 0d) — what it measures, and the cases it does not see

> **Partly superseded by Revision 19 §R19.1 (2026-09-16).** This section's original title claimed the rule "cannot be fooled", and `plan-reviewer` showed it could: as specified below in items 2–5 it counts components of **isolated** ink, so a token drawn in the correct slot but *underneath* the bed, the ground or the agent's outline keeps its ink and passes. **Items 2–5 and the Controls list below are replaced by §R19.1**, which adds a composition clause, a survival floor, two self-asserted preconditions, a composite-measured minimap and mutation M-F. Item 1 (kinds, never instances) and the two checkpoints stand, with the clauses §R19.1 adds. Read §R19.1 as the specification; this section is kept for the reasoning that produced the rule.

The observed defect is that a painter can draw two occupants and a viewer sees one. The existing audit measures *text* collisions; it has no rule that fires when two graphics coincide, so it would pass the very frame this revision exists to prevent.

**Rule `cell_overdraw`.** For each square of the named arena axes (`--arena-axes`, which already exists because the arena can only be named, never guessed), with the square grid derived from that axes' extent and the recording's world/window size — **not** from the layout module, which the audit still may not import:

1. Ground truth is the **snapshot**: the set of distinct non-terrain kinds at that square (R5 — inactive slots skipped). Kinds, not instances (§R17.5 item 1).
2. Ink is measured by the existing isolation probe (`FrameProbe.ink`). Elements whose ink covers ≥ 40 % of the square's area are the **bed** and the ground and are excluded; what remains is token ink.
3. The token ink inside the square must form **exactly as many connected components as there are distinct kinds**, and no two components may touch. A painter that draws concentrically yields one component where the snapshot says two — the rule fires.
4. Tolerance: **zero** shared pixels between components, no dilation. The 1 px dilation in the text rule exists for glyph anti-aliasing and is wrong here; the mock measures exactly 0 px precisely because the keyline is kept inside `h` (§R17.3 item 7), so a non-zero number is a real defect rather than a rounding artefact.
5. **Bed-under-token ink is exempt by construction**, because the bed is excluded at step 2. This is the one place the rule needs the bed/token distinction, and it takes it from measured area, not from a painter tag — the same discipline mutation M-C already enforces.

**Controls, because an instrument nobody calibrated is worthless (the CP0.3 lesson).**
- **Positive:** a synthetic two-token figure drawn concentrically, built by the test itself, must fire; and a mutation of the real painter (**M-E**: force every occupant to the square's centre) must fail the audit at Phase 2.
- **Negative:** a single-occupant square and an empty square must produce **zero** findings; a square holding a bed plus one token must produce zero (the bed exemption must not be a blanket "ignore large things" that silences real overlaps); and the exact per-square finding count on a frozen frame is pinned, as the existing negative controls are, so an `ink()` that answers "everything" fails it.
- **Minimap:** the same ground truth applied at map scale — a square whose snapshot holds two movers must show two distinguishable colour areas, and the shared-square caption must be present on that frame.

**New checkpoints.**
- **CP0.3b: the audit sees squares.** `cell_overdraw` fires on the synthetic concentric figure and is silent on the three negative controls; the per-rule counts on the frozen M1 and M4 frames are re-pinned. *Fails if:* the rule fires on a single-occupant square, stays silent on the concentric one, or changes any existing rule's count on the frozen frames.
- **CP2.8: squares render as many occupants as they hold.** On every matrix cell, every checked frame with a shared square passes `cell_overdraw`; the four archetypes (agent + terrain, two movers, three-way, four-way) are each rendered and **looked at**; mutation M-E fails the audit; the minimap caption is present wherever a split dot is drawn. *Fails if:* any archetype is missing without a labelled synthetic substitute, any check is non-zero, M-E passes, or the caption is absent.

Existing checkpoints that gain a clause: **CP2.6** (entity ink) now also requires that a *shared* square shows ink for every kind the snapshot places there; **CP-C** (one meaning per colour) counts the shared-square token colours and the minimap split wedges against the same palette table; **CP-D** looks at shared squares at full size, since this is the change most likely to look crowded rather than measure crowded.

---

## Revision 18 2026-09-16 (user decision: the grid view shows the WHOLE world at a 50 px square — supersedes Revision 17's 48 px and its 5×5 window)

**What this revision is about, in plain words.** The dashboard's big centre panel is the one that draws the world the agent is walking through. Until now the plan had it showing only a 5×5 patch of that world around the agent, and Revision 17 recorded a decision to draw each square of the patch 48 pixels wide. The picture the user was given when they made that call contained an error of mine: I told them today's square is 28 pixels, but **28 px is the square of the small *World map* in the left column, not of the big grid panel** — today's grid panel draws its squares at 96 px. With that corrected, the user chose something simpler than a window: **the grid panel shows the whole 10 × 10 world, and each square is 50 pixels across.** Two things follow. There is no 5×5 viewport any more — nothing pans, nothing centres on the agent, and the panel's frame is the world's edge. And the square is 50 px rather than 48 px, which matters because 48 px was one to two pixels *under* the size at which two animals sharing one square stay tellable apart — a shortfall Revision 17 recorded as an accepted cost. At 50 px that shortfall is gone, so the paragraph recording it is retired below rather than left for a later reader to trip over.

**What is superseded, precisely.** Revision 17's square size (48 px) and the assumption that the grid panel draws a local window. **Everything else in Revision 17 stands unchanged**: variant H (terrain as the square's ground cover with occupants in slots on top of it), `CELL_PRIORITY`, the shared-cell agent rule, the minimap's deliberately coded encoding (§R17.4), the three unsolved cases (§R17.5 items 1, 3, 4), and the `cell_overdraw` audit rule (§R17.7).

### R18.1 The arithmetic, re-derived from Figure 3's own code

**How this was checked.** Not by trusting the numbers quoted in the brief or in Revision 17: the canvas, gutter, gap, padding, header, left-column width and right-column minimum were read straight out of `renderer_layout_redesign/dashboard_style.py` and `fig03_proposed_dashboard.py` (`W=1440, H=896, OUTER=24, GAP=16, PAD=16, HEAD=64, LEFT_W=320, MIN_RIGHT_W=440`), the packer's arithmetic was replicated from `fig03_proposed_dashboard.pack()`, and the replication was validated by reproducing Figure 3's own approved layout to the pixel before any new number was computed.

| | Figure 3 as approved (5 × 96 px) | Revision 17's reading (10 × 48 px) | **Revision 18 (10 × 50 px)** |
|---|---|---|---|
| Centre (grid) card | 544 × 544 px | 544 × 544 px | **564 × 564 px** |
| Right column width | 496 px (min 440) | 496 px | **476 px** — 36 px of slack |
| Sensor band | starts y = 624, 256 px tall (min 200) | same | **starts y = 644, 236 px tall** — 36 px of slack |
| Right column height available / needed | 544 / 516 px | 544 / 516 | **564 / 516 px** — 48 px of slack |
| Left column (Interoception 504 + World map 220 + gap) | 740 of 816 px | unchanged | **unchanged — the left column is not touched at all** |

**The 564 px card closes, and here is what it costs.** The centre card grows 20 px in both directions. Horizontally that comes out of the right column, 496 → 476 px, still 36 px above the 440 px the thermoception diamond and its shared scale need — and `fig03_proposed_dashboard.pack()` raises `LayoutOverflowError` if it ever is not, so this is a guarded number, not a hoped-for one. Vertically it comes out of the sensor band, 256 → 236 px, still 36 px above its 200 px minimum. The right column's *available height* actually **grows** (it is measured against the arena's bottom edge), so every right-hand card gains room. **The layout's spare width and spare height both drop from 56 px to 36 px** — that is the whole price, and nothing is pushed below a stated minimum.

**The ceiling, so nobody has to re-derive it.** On this canvas, with the sensor band present, the largest whole-world square is **53 px** (at 54 px the band falls to 196 px and the right column to 436 px — both under their minima). 50 px therefore sits 3 px below the ceiling, not against it.

### R18.2 The grid view is no longer a window — what that changes

1. **View size.** The drawn view is the world, `W = params.width` (and height), not `max(local_view_size, 2·max_range + 1)`. §D7.3's window rule survives only as the fallback for worlds larger than the card can hold whole (above 10 squares at 50 px), which no maintained config has today.
2. **No centring, no panning.** The old windowed view implied a viewport that follows the agent; there is none. The world's origin maps to the card's corner and stays there for the whole episode, and the agent moves *inside* a fixed frame instead of the world sliding underneath a fixed agent. This is a visible change in how the video reads and is called out here so it is not discovered in review.
3. **No off-world cells, no edge padding.** A window near a wall used to contain cells outside the world, drawn in `OFF_WORLD` white. Showing the world whole, every square is a real square; the off-world path becomes reachable only through the over-10 fallback, and any frame test asserting off-world ink must be moved onto that path rather than onto a maintained world.
4. **The minimap's viewport rectangle is dropped.** §D7.7 item 3 had the World map outline the `W × W` window actually drawn. With the whole world drawn, that outline is a rectangle around the entire map — pure noise. It is removed, and a test that asserted its presence must assert its absence for whole-world frames.
5. **The `footprint exceeds view (r=…)` caption** (§D7.3) can no longer fire on a 10×10 world: a sense's diamond can now only be clipped by the world's own edge, which is truthful rather than a rendering limitation. The caption survives for the over-10 fallback.
6. **`layout_signature()` still carries the window rule**, because the fallback still exists; it now records "whole world" for every maintained config.
7. **`/api/values` returns 100 squares, not 25.** The viewer's per-square occupant list (§R17.6 Phase 4) grows fourfold; the page's table needs to stay readable at that size.
8. **The arena painter's work grows about fourfold** — 100 squares per frame instead of 25, each with a ground, possibly a bed, and up to four tokens. **This bears directly on the Q9 speed gate** ("median frame time on the campfire world ≤ half of V1's"), which was agreed before this decision. *(Corrected in Revision 19 §R19.3: the original sentence here said "Phase 1 must measure the arena painter", which is impossible — Phase 1 is Matplotlib-free and the painters are Phase 2. The measurement is **CP0.4**, whose spike now draws the whole world, reports arena-only versus non-arena time, and has one pre-registered failure path ending in user question **Q22**. The developer does not reconsider the gate, the per-square cost or the square size unilaterally.)*
9. **A defect found while checking the fallback, recorded rather than left.** §D7.7 item 3's step 4 shrinks `W` by 2 toward `local_view_size`. In the thermal world that is unsound at either square size: a 9-square view gives a centre card 514 px tall (496 px at 48 px squares), while the right column's three cards need 516 px — so the shrink step makes the right column overflow, because the right column's height is measured against the arena's bottom edge. The Phase 1 packer test must assert the right column still fits at whatever `W` the fallback lands on, and the fallback must reject a `W` that does not clear it.

### R18.3 Slot geometry at 50 px (the numbers `tests/env/test_dashboard_cells.py` asserts)

Recomputed from §R17.3's own formulas — `h(1) = 0.30 × cell`; for `n = 2`, `w = (cell − 2 × 0.05 × cell)/2` and `h = min(w, 0.60 × cell)/2 × 0.92`; for `n = 3, 4`, two rows in a band of `0.88 × cell`, `h = min(w, band/2)/2 × 0.92`. The formulas were validated by reproducing Revision 17's recorded 48 px values (14.40 / 9.936 / 9.715) before being applied at 50 px.

| Occupants in the square | `h` (token ink half-extent) at 48 px | **at 50 px** | Chevron `0.62 × h` at 50 px | Smallest identifying mark `0.30 × h` at 50 px |
|---|---|---|---|---|
| 1 (or 1 + terrain bed) | 14.40 px | **15.00 px** | – | – |
| 2 | 9.936 px | **10.35 px** | 6.42 px | **3.105 px** |
| 3 or 4 | 9.715 px | **10.12 px** | 6.27 px | **3.036 px** |

Also at 50 px: `BED_MARGIN = 0.14 × cell` = **7.00 px** (was 6.72); the white keyline radius stays **exactly `h`** (§R17.3 item 7); the chevron clears its 6 px legibility floor in every reachable case with room to spare (it was 6.16 / 6.02 px at 48 px, i.e. on the line).

**The floors are cleared, and the derivation is reproducible.** The binding constraint is the predator's amber eye slit and the rabbit's ear gap at `0.30 × h`, against a 3.0 px chroma-survival heuristic. Solving it: two movers need `0.207 × cell ≥ 10.0` → `cell ≥ 48.31` → **49 px**; the four-way needs `0.2024 × cell ≥ 10.0` → `cell ≥ 49.41` → **50 px**. Those are exactly the 49 px and 50 px floors Revision 17 recorded, re-derived here independently. At 50 px both are met — the four-way by construction meets it exactly (10.12 px of half-extent against the 10.0 px the mark needs), so 50 px is the smallest square that clears every reachable case, not a comfortable margin above it. **`test_dashboard_cells.py` therefore asserts `h` = 15.00 / 10.35 / 10.12 px, and recomputes both floors from the mark fractions and compares them against 49 and 50.**

### R18.4 Revision 17 §R17.5 item 2's "accepted cost" is retired

Revision 17 recorded that 48 px was 1 px under the two-mover floor and 2 px under the four-way floor, and accepted it on the grounds that the 3.0 px chroma floor is a JPEG heuristic rather than a cliff, with "a 50 px square" named as the first remedy. **That remedy is now the decision, so there is no accepted cost left to carry.** §R17.5 item 2 is amended in place to say so. What remains true in it, and is kept: variant H still degenerates to equal tiles from the third occupant up, and the frame still gives no focal point in a three- or four-way square. That is a property of the design, not a pixel shortfall, and it is not retired.

### R18.5 Deltas to Revision 17 §R17.6 (the phases not yet built)

- **Phase 1.** `layout.py`: `ARENA_CELL_PX = ARENA_CELL_MIN_PX = 50`. The fallback order's first question is whether the **world** fits whole at 50 px (it does at 10×10); the local-window steps are the fallback for larger worlds only, and must additionally clear the right column's 516 px (§R18.2 item 9). `panels.py`: the arena row's min size is `W × 50 px` where `W` is the world size; the minimap loses its viewport rectangle and keeps its shared-square caption line. `test_dashboard_layout.py`: the arena box is exactly `W × 50` px **and never larger** (it is a fixed box, not a grow panel — §R19.2); a whole 10×10 world yields a 564 × 564 centre card with the right column at 476 px and the sensor band at 236 px, both above their minima — asserted on a **synthetic `LayoutContext`** with thermal on and one sense at r ≥ 1, because no maintained config has both a thermoception card and a sensor band (§R19.4 item 3); a **5×5** world yields a 314 × 314 card with the right column at 726 px, and a synthetic 5×5 context with thermal *and* a band raises `LayoutOverflowError` naming the right column (§R19.2); a world too large to draw whole at 50 px takes the documented fallback, and **one check covers all three** — the right column must fit whatever arena height is chosen.
- **Phase 2.** Cell composition is unchanged in rule; only the constants move (§R18.3). One new consequence: co-occupancy archetypes are now hunted over 100 squares per frame rather than 25, which makes it *more* likely a real episode contains them and correspondingly less likely a synthetic snapshot is needed.
- **Phase 3.** `layout_signature()` records square size 50 and window rule "whole world" for maintained configs.
- **Phase 4.** `/api/values` covers every world square; the page says so if its viewport forces squares below 50 px.
- **Docs.** `docs/environment/12_renderer.md` records the 50 px square, the whole-world rule, and the removal of the viewport rectangle. No config key changes; `CONFIG_CRITICAL_SETTINGS.md` and `SCRIPTS_DEPENDENCY_MAP.md` are unaffected by this revision.

### R18.6 One consequence the user should decide (Q21)

The World map in the left column exists to give global context while the grid panel shows a local patch. **With the grid panel showing the whole world, the two panels now show the same extent** — the World map becomes a smaller, coded copy of the picture already on screen, and §R17.4's split dots and rim pips exist to serve exactly that copy. This plan does **not** decide it either way; it is opened as Q21 with the arithmetic of what dropping it would buy, because deleting a panel the user asked for is not a developer's call. *(**Answered 2026-09-17: the map is KEPT, as a minimap.** See Decided questions; the encoding it keeps is Revision 22 §R22.3's, not the split-dot-and-rim-pip scheme described here.)*

---

## Revision 19 2026-09-16 (after plan-reviewer sixth pass: the co-occupancy check learns about painting order, the arena's box is pinned in one place, and the speed gate is re-specified)

**What this revision is about, in plain words.** The reviewer read Revisions 17 and 18 and returned **NOT READY** on one finding, with eight smaller ones behind it. The blocking one is worth stating carefully, because it is this plan checking itself and getting the wrong answer. The redesign exists to stop a square that holds two animals from being drawn as one animal. Revision 17 added a check for exactly that — and specified it to measure **each drawing on its own, in an otherwise empty frame**. A drawing that sits in the right place but is painted *underneath* the ground, the terrain cover or the agent's outline still looks complete when measured on its own: the check counts two drawings, calls the frame clean, and the picture a viewer sees still shows one animal. The instrument was blind to precisely the defect it was built for — and that defect is not hypothetical, it is the observed one, where whichever entity name sorts later in the alphabet is painted last and wins. §R19.1 fixes it by measuring the ink that **survives** the painting rather than the ink that was laid down.

The other two blocking findings: two sections of this plan describe the centre panel differently and **Phase 1 builds from the wrong one** (§R19.2, which also covers the two maintained 5×5 worlds nobody had considered), and the Phase-0 speed gate **cannot be run in the order it is written** and would measure a quarter of the work the real panel now does (§R19.3). §R19.4 folds in the small findings.

**Nothing here re-opens a user decision.** Variant H, the 50 px square, the whole-world view, `CELL_PRIORITY`, the minimap's deliberately coded encoding and the three unsolved cases all stand. One new question — **Q22** — is opened for the user, and it is **conditional**: it is asked only if the Phase-0 speed measurement misses its target, and it exists because changing the speed target the user set (Q9) is the user's call, not the developer's.

### R19.1 The co-occupancy rule measures what SURVIVES the painting, not what was drawn (#54, Critical)

**The hole, stated exactly.** §R17.7 measured token ink with the audit's isolation probe (`FrameProbe.ink`: render one element alone against the bare background, and call the difference its ink). Isolation was adopted in Revision 15 for a good reason — it does not lose the disputed pixels of a text label that something opaque was painted over — but it has a mirror-image blind spot: **it cannot tell whether an element is visible in the finished frame.** A predator token drawn in the correct slot and then covered by the terrain bed, the ground square or the agent's square outline keeps every pixel of its isolated ink. The component count then equals the kind count, the rule passes, and the composed frame shows one occupant. Mutation M-E (force every occupant to the square's centre) is caught, because concentric drawing merges two components into one; a z-order mutation is not caught at all. The same blindness applies to the minimap variant, and the minimap defect Revision 17 itself names *is* a draw-order defect ("the agent's dot is drawn over the other animals' dots").

**Phase 0c already solved this class, for text.** The `fill_over_text` rule asks whether the partner was composed *after* the label, using matplotlib's own composition order — zorder first, then insertion index within one Axes — implemented as `_is_painted_over` / `_draw_index` (`scripts/eval/render_layout_audit.py:436-465`). The machinery exists, is calibrated, and has both positive and negative controls. The cell rule simply did not use it.

**Vocabulary** (fixed here so painter, test and audit use one set of words):

- **isolated ink** of an element — `FrameProbe.ink(el)`, unchanged: the pixels it lays down when rendered alone.
- **drawn after** — the existing composition order (`_is_painted_over`): higher zorder wins; equal zorder, higher insertion index wins.
- **surviving ink** of an element (new) — the pixels of its isolated ink at which **no element drawn after it** has isolated ink.
- **token ink** of a square — the union of isolated inks of the square's token elements, i.e. everything except the excluded classes below.
- **visible token ink** of a square — the union of *surviving* inks of the same elements.

**The rule, restated in full.** It replaces §R17.7 steps 2–5 and §D5.2 item 11.

1. **Ground truth is unchanged.** The set of **distinct non-terrain kinds** the snapshot places at that square (never instance counts — §R17.5 item 1). Call it `K`.
2. **Exclusions, measured and not declared** (as before, plus one addition):
   - an element whose isolated ink covers **≥ 48 %** of the square's area is the **bed** or the **ground**, and is excluded; *(**the constant moved 0.40 → 0.48 in Revision 21, 2026-09-17, with its evidence: at 0.40 a *correct* lone agent on bare ground measures 0.4376 of its square and is thrown out as scenery — the mirror of §R20.8. Measured populations: largest correct token **0.4376**, smallest bed **0.5168**, bed floor by construction **0.5184**; 0.48 sits 53.5 % up that gap and every negative control passes. See Revision 21 §R21.2.)*
   - an element whose ink sits on the **perimeter of its own bounding box** is a square outline or a seam, and is excluded. *(Wording corrected in Revision 20 §R20.7 item 1: the helper `_ink_is_outline` (`render_layout_audit.py:414-433`) tests the element's **own** bbox, not the square's box, and Revision 20 adds the failing-direction guard that an outline-classified element whose bbox spans under 80 % of the square is reported rather than silently excluded.)* The agent's 2 px iris square outline is the case that matters, and leaving it in would let it bridge two token components around the square's rim and break the count.
   - *(Revision 20 §R20.8: a bed must be **one artist**, so the ≥ 40 % test measures it whole; a bed split into parts leaks its small parts into the token count and fires on a correct painter.)*
   - Everything else inside the square is a **token element**. No painter tag is consulted, per finding #3's discipline.
3. **The concentric check (kept).** The connected components of the **token ink** must number exactly `|K|`, pairwise touching in 0 px. This is the old rule, and it is what catches a painter that draws two occupants on one centre.
4. **The composition check (new, and the point of this revision).** The connected components of the **visible token ink** must *also* number exactly `|K|`. A token completely covered by something drawn after it contributes no surviving pixels, so the count falls short and the rule fires.
5. **The survival floor (new).** For each component `c` of the token ink, `|c ∩ visible| / |c| ≥ SURVIVAL_MIN`. This is what a component count alone cannot do: a token 95 % hidden behind a bed still leaves a sliver, the sliver is still one component, and step 4 alone would pass it. Two properties make the denominator honest without any painter grouping: a component is a **pixel set**, so a token's own parts overdrawing each other (the eye over the body, the ring over both, the chevron over the ring) never reduces it — those pixels are in the union and they survive; and a token is by construction disjoint from its neighbours, so nothing legitimate eats into it. **A correct composition must therefore measure exactly 1.000.** `SURVIVAL_MIN` is pinned at **0.98** to absorb a single-pixel anti-aliased seam, and Phase 0d **records the measured value on the correct control**. A control that measures below 1.000 is investigated, not absorbed into a looser constant. *(**Revision 20 §R20.3**: 0.98 is an undefended value — 2 % is only ~6.4 px of a ~330 px² token, while a 1 px seam round the whole circumference is ~19 %. Phase 0d now **sweeps both sides** and records a gap table: the minimum over every negative control against the maximum over an M-F2 family at three insets. The constant moves only in this plan text, with its evidence, never in a test.)*
6. **Preconditions the rule asserts about itself, and fails rather than skips.** They exist because "what was drawn last" is only a valid proxy for "what the viewer sees" under them.

   > **Re-scoped by Revision 20 §R20.1 (both), and extended by §R20.6 (a third).** As originally written below, both preconditions are **arena-global and fail on a correct painter** — the agent's own translucent halo and shadow trip the opacity clause on every frame with an agent, and the page's background rectangle trips the one-Axes clause on every frame. **Read §R20.1 and §R20.6 as the specification.** In one line: both are re-scoped to `L(p)`, the last-drawn element with ink at a token pixel — if `L(p)` is not a token element of that square it must be fully opaque (a′) and must belong to the arena Axes (b′); and a third precondition (c′) requires the ground, bed, outline and keyline colours to be visible to the probe at all. **The occluder set from which `L(p)` is computed remains every element in the figure** — narrowing what is asserted, never what can occlude.

   - **One Axes.** Every element with ink inside the arena's extent must belong to the named arena Axes. `_is_painted_over` deliberately refuses to order two elements in different Axes, so token ink drawn into a foreign Axes would be silently un-orderable. The rule reports it and **fails**; it never passes an undecidable square.
   - **Opacity above tokens.** Every element drawn after a token element must be fully opaque (artist alpha `None` or 1.0, and no RGBA face or edge alpha below 1). A translucent overlay would make "drawn after" the wrong test in both directions — it would report an occlusion a viewer can see through. The arena has no translucent overlays by design (the minimap's terrain tint is drawn *below* the dots, §R17.4); asserting it is what keeps that true as the painter changes.
7. **Bed-under-token ink stays exempt, and is now exempt for the right reason.** The bed is excluded at step 2, and a token's pixels that sit over the bed are exactly the pixels that *survive* — which is the correct reading of "the occupants stand on the floor".
8. **Tolerance is still zero shared pixels, no dilation**, on both masks — see §R19.4 item 2 for the negative control that pins what "zero" reads as at a 50 px square.
9. **Minimap: measured on the composite, not by isolation.** *(**Further corrected by Revision 22 §R22.1, 2026-09-17: a kind's ground truth is the SET of palette colours its own mark is drawn in, and the denominator is the same census over that kind's own artists rendered TOGETHER** — not the per-element maximum the rule shipped with. The hiding predator's mark is deliberately two paints, body plus amber accent, so a single-colour ground truth read its own accent as ~21 % of itself missing and fired on a correct frame. This is §R19.1 step 5's union-of-own-parts rule, which the grid panel already had and the minimap variant never inherited. No floor moves.)* *(**Ground truth and floor both re-grounded by Revision 20 §R20.4** — read that as the specification. As written below the clause fails a correct painter twice: "at least as many distinct colours as **movers**" fails a correct two-predator square, which is two movers and one kind; and `SURVIVAL_MIN` against a **geometric** wedge is unreachable on a correct ~13 px split dot, a third to a half of whose pixels are edge blends. §R20.4 makes the ground truth the distinct palette colours of the **kinds** present, and measures the denominator with the same census on the isolated wedge, or pins a separately swept `MINIMAP_AREA_MIN`.)* A square whose snapshot holds two movers must show **two distinguishable colour areas in the composed image** — classify the composite pixels inside the map square against the palette table (the same census CP-C runs), and require at least as many distinct occupant colours as the snapshot has movers, each with an area at least `SURVIVAL_MIN` of its expected wedge. Isolation would report a split dot as correct even when one half is painted over the other, which is the exact defect §R17.4 exists to prevent. The shared-square caption check is unchanged.

**Controls. The mutation is the finding**, so it is specified rather than left to the developer:

- **M-F1 (full occlusion).** Draw the terrain bed *after* the tokens. Steps 4 and 5 both fire. A pure isolated-ink rule passes it — that is the demonstration that this revision was needed.
- **M-F2 (partial occlusion).** Draw the bed after the tokens, inset a further `0.10 × cell`, so a rim of each token survives. The component count in step 4 **still equals `|K|`**; only the survival floor fires. Without M-F2, `SURVIVAL_MIN` is an unexercised number.
- **M-F3 (minimap).** Draw the agent's dot above the split wedge. The composite census finds one colour area where the snapshot says two.
- **M-F1g (the ground, not the bed, drawn after the tokens)** — added by Revision 20 §R20.6. Run with the figure facecolor set to `CANVAS`, it is also the demonstration that precondition (c′) is load-bearing: without (c′) the ground has no probe-visible ink and the mutation **passes silently**.
- **Negative partners (all must produce zero findings and are recorded with their measured survival ratio):** a single-occupant square; an empty square; a bed plus one token — **the campfire bed specifically** (§R20.8); a correct two-token square **containing the agent**; a correct four-way square **containing the agent**; and an E-cell footprint edge crossing an occupied square (§R20.2). The recorded ratios form one side of §R20.3's gap table.

**What this rule still does not see, stated so nobody over-trusts it.** (a) **Multiplicity** — two predators in one square are one kind and one token by design (§R17.5 item 1); the ground truth is kinds, and that is deliberate, not a gap in the instrument. (b) **A token in the wrong slot but unoccluded** — geometrically wrong, yet it is one disjoint component of full surviving ink, so both checks pass. That case belongs to the value-to-pixel checks and to CP2.8's human look, and CP2.8 keeps both. (c) **Identity errors** — a predator drawn with the rabbit's form is invisible here; CP-C's colour census and the look are what cover it. (d) **An occluder the probe cannot see** (Revision 20 §R20.6) — an element whose colour lies within `INK_DELTA` (8/255) of the figure facecolor lays down no isolated ink, so it can never be the last-drawn element at a token pixel and cannot occlude anything as far as this rule is concerned. Precondition (c′) converts that blindness into a **failure** for the colours the arena actually uses (ground, bed bases, outline, keyline); it cannot convert it for a colour nobody has written down yet. §R17.7's original title claimed the rule "cannot be fooled"; it is retitled, because the honest claim is narrower and is written out above.

### R19.2 One description of the arena, and the 5×5 worlds nobody had counted (#56)

**The contradiction.** §D1.2 items 2–3 — the section Phase 1 builds `layout.py` from — still described the arena as a **grow** panel in a layout with a 300 px left column and a 330 px right column. Revision 18 pins a **fixed** 50 px square inside Figure 3's 320 px left column and 440 px right-column minimum. Two competent implementers reading the same plan diverge on day one: one grows the arena into the leftover height (up to the 53 px ceiling on a 10×10 world, or to 100 px on a 5×5 one), the other pins 50 px. §D1.2 is rewritten below to Figure 3's constants, and the arena is stated to be a fixed box.

**The maintained 5×5 worlds.** Revision 18 reasoned only about worlds of 10 or more. Two maintained curriculum levels are 5×5 — `configs/environment/experiment/basic/00-static_predator_5x5.yaml` and `01-slow_predator_5x5.yaml` (`environment.height/width: 5`). Both carry **only** an `environment:` block over `extends: environment/default`, so both inherit `thermal.enabled: false`, `olfactory_grid_range: 0` and `visual_sensor_range: 0` — verified in the files, not assumed. The arithmetic was re-derived here from `fig03_proposed_dashboard.py::pack()` rather than copied from the review:

| | 10×10 at 50 px | **5×5 at 50 px** |
|---|---|---|
| Centre card (`W × 50 + 64`, square) | 564 × 564 px | **314 × 314 px** (250 px of drawing) |
| Right column width (`1040 − card width`) | 476 px (min 440 — 36 px slack) | **726 px** (min 440 — 286 px slack) |
| Sensor band, if present (`880 − (64 + card + 16)`) | 236 px (min 200 — 36 px slack) | 486 px |
| Right column height available — **band present** (`card height`) | 564 px | **314 px** |
| Right column height available — **no band** (`64 → 880`) | 816 px | 816 px |

**A real hazard falls out of the last two rows, and it is the same one §R18.2 item 9 found in the fallback.** The right column's available height is measured against the arena's bottom edge whenever a sensor band is present, so a *smaller* world gives the right column *less* height. A 5×5 world with a band present would leave the right column **314 px** against the **516 px** a thermal right column needs (Proprioception 104 + the extero/collision row 150 + Thermoception 230 + two 16 px gaps) — an overflow. **No maintained config reaches it today** (the two 5×5 worlds have neither thermal nor a sense range above 0), so this is a guard, not a defect in the shipped set. But it is the same coupling arriving from a different direction, and Phase 1 must make the check **once, in one place**: *the right column must fit whatever arena height is chosen* — whether that height comes from the world's own size, from the whole-world rule, or from the fallback's shrink step. That single check subsumes §R18.2 item 9.

**Phase 1 tests that follow** (added to `tests/env/test_dashboard_layout.py`): a 5×5 context yields an arena box of exactly `5 × 50` px inside a 314 × 314 card with the right column at 726 px; a **synthetic** 5×5 context with thermal on and a sense at r ≥ 1 raises `LayoutOverflowError` naming the right column; and the arena box is exactly `W × 50` for every context, never larger, which is what pins "fixed, not grow".

### R19.3 The speed gate: runnable order, the right arena, and one failure path (#57)

**Three defects, and none of them is the number.** (a) **Ordering.** §R18.2 item 8 said "Phase 1 must measure the arena painter", but Phase 1 is Matplotlib-free — `layout.py` has no import of it and the painters are Phase 2 — and CP0.4 is written as a gate *before* Phase 1. (b) **The spike measured the wrong thing**: as specified it drew a 5×5 arena, 25 plain squares, while the decided arena draws **100** squares each with a ground, possibly a bed, and up to four vector tokens. Figure 3's approach pre-builds every glyph for every entity name in every square — roughly 9 names × ~5 patches × 100 squares ≈ 4,500 artists — and the artist count is now the largest unmeasured cost in this plan. (c) **Two conflicting failure paths** were written: CP0.4 said "go back to the user with B (Pillow)", §R18.2 item 8 said "reconsider the gate or the painter's per-square cost".

**Why (b) and (c) together are dangerous rather than untidy.** The 0.5× ratio was agreed (Q9) as a proxy for *the architecture*: V1 rebuilds its whole figure every frame, the new renderer builds once and updates artists, and half the time was the expected payoff. With four times the arena content on one side of the ratio and not the other, a miss no longer distinguishes "the architecture does not pay" from "we are drawing four times as much". Acting on such a miss would mean pivoting to Pillow — re-authoring every painter in a second toolkit — which is the most expensive move available in this plan, for a reason that is not the toolkit's fault.

**Re-specified CP0.4:**

- **Order, stated explicitly.** Phase 1 (`layout.py`, `panels.py`, `labels.py` — no Matplotlib, nothing a frame timing can measure) **may be built before CP0.4**. CP0.4 **must be passed, or escalated to the user and answered, before Phase 2 writes a painter.** §R18.2 item 8's "Phase 1 must measure the arena painter" is withdrawn.
- **What the spike draws.** The **whole 10×10 world** with §R17.3's composition — a ground per square, a bed on every square where the M4 snapshot places terrain, and tokens for every occupant, so the archetype mix is the real one from the M4 frames rather than an empty world — plus the vitals card and one right-hand pod, figure built once, `frame(t)` updating artists.
- **How it is measured.** Against V1 on the same M4 recordings, ≥ 200 frames (first 5 excluded), in a `ProcessPoolExecutor` worker on one lab node, node and CPU model recorded, exactly as §D5.3 requires.
- **What it reports — this is the new part.** Setup ms; median and p95 frame ms; and the frame time split into **arena-only** and **non-arena**, obtained by timing `frame(t)` with the arena painter's update enabled and disabled on the same figure and the same artists. Plus three counts that explain the number: total artists, arena artists, and the per-square pool size.
- **One pre-registered failure path**, replacing both:
  - spike median **≤ 0.5 × V1 median on M4** → the gate is met, Q9 stands untouched, Phase 2 proceeds, **and no user question is asked**;
  - **0.5× < median ≤ 1.0 ×** → **do not pivot and do not adjust anything.** Report the split, the artist counts and the four options of **Q22** to the user, and stop until they answer;
  - **median > 1.0 × V1** → the hard floor (never slower than V1, which is what protects training-time rendering) is breached. Same report, same question, with option 4 (Pillow) named as live.
  - In no case does the developer change the gate, the square size, or the stack on their own initiative. Changing Q9 is the user's decision.
- **CP4's end-state gates are unchanged** (V2 median ≤ 1.0 × V1 on every cell and ≤ 0.5 × on M4), subject to whatever the user decides at Q22 if it is asked.

### R19.4 The smaller findings, folded in (#55, #58–#62)

1. **Token medium is vector, and CP2.6 is rewritten (#58).** The plan said two incompatible things: §D1.4 and CP2.6 described raster icons from `assets/dashboard_icons/` (CP2.6 asserted the campfire's ink belongs to an `AxesImage`), while §R17.3 and the `cells.py` row describe vector forms with parametric mark fractions — and `test_dashboard_cells.py` recomputes `MIN_MARK × h` as a number, which a PNG cannot supply. **Decided here: beds, tokens and companion forms are vector primitives drawn in `cells.py`.** `assets/dashboard_icons/` keeps only what is drawn at a fixed size and never recomputed — legend chips and minimap glyphs — and the developer records in the Implementation Report whether those too are drawn from the same vector forms, in which case the folder is dropped. *(**Condition met, and the drop is scheduled — Revision 21 §R21.4 item 2.** Phase 2 reports every form in the frame, including the World map's marks and the legend chips, is vector; verified that nothing under `src/`, `scripts/` or `tests/` reads the folder, and that the frozen V1 renderer loads its icons from the **`assets/` root** instead, so V1 is unaffected. **Drop the nine PNGs and the `v1_path_guard.py:145` row together at CP-D**, not before — CP-D is the last point at which `visual-design-reviewer` could ask for a raster texture.)* CP2.6's `AxesImage` clause is replaced by an area-classified bed check. Q12's `assets/campfire.png` is unaffected as a **legend/map** glyph; the arena's campfire is a drawn bed, so that asset is no longer what CP2.6 measures.
2. **The 0 px tolerance is pinned by measurement, not by inheritance (#55).** The "glyph-on-glyph ink is 0 px" figure came from the round-2 mock at a **40 px** cell, on a transparent canvas under an alpha > 24/255 mask — not at 50 px and not under the audit's per-channel > 8/255 difference over a coloured ground. At 50 px two adjacent slots are 22.5 px apart with disc radius 10.35 px and a keyline stroke **centred** on `h` at `lw = max(0.8, h/8)` = 1.29 px, leaving a ~0.5 px geometric gap that lies inside the anti-aliasing fringe. **Phase 0d adds a negative control** that draws two adjacent-slot tokens at 50 px with the real forms and measures with `FrameProbe.ink`, and pins what it reads. If it is non-zero, the fix is the **keyline geometry** — inset the stroke so its outer edge lies at `h` — and **never** a loosened tolerance. §R17.3 item 7's "1 px white keyline" is corrected to the measured stroke width and its placement is stated.
3. **Phase 1's 564 / 476 / 236 clause is asserted on a synthetic `LayoutContext` (#59).** No matrix cell produces that geometry: every maintained config has both sense ranges at 0 (`default.yaml:222,232`; no `basic/` file carries a `sensory:` block at all), so **no M-cell has a sensor band**; the thermal cells have the thermoception card and no band, the E-cells a band and no thermal card. Thermal-plus-band exists only in Figure 3's sketch, where the ranges were overridden for the drawing. The Phase 1 test therefore constructs a `LayoutContext` with thermal on and one sense at r ≥ 1 and says so; a developer asserting it on M4 would find no band.
4. **The chevron floor is on the chevron (#60).** `0.62 × h ≥ 6 px` — the drawn chevron length, which is what the 6.42 px and 6.27 px figures in §R18.3 are. Equivalently `h ≥ 9.68 px`; the four-way case clears it by 0.44 px. It joins the floors `test_dashboard_cells.py` recomputes.
5. **Q21's working assumption is recorded (#61).** Phase 1's pinned numbers rest on **keeping** the World map with `LEFT_W = 320`. Deferring Q21 is safe only while that is written down, because "drop it and narrow the column" would move 564 / 476 / 236 and would waste Phase 0d's minimap control and Phase 2's split-dot work. ~~**Q21 must be answered before Phase 2 starts the minimap**, not before Phase 1.~~ **The gate is discharged: Q21 was answered on 2026-09-17 and the answer is KEEP the map** (Decided questions). The working assumption was the right one, every pinned number stands unchanged, and there is no longer a question here for a later phase to re-open.
6. **Phase 0d's controls are synthetic, and CP0.3b's re-pin is a no-change assertion (#62).** *(Extended by Revision 20 §R20.3 and §R20.7: the control list gains an agent, a footprint edge, a campfire bed and a cross-Axes order control, and the sample is sized for the audit's cost.)* `cell_overdraw` needs `--arena-axes`, and V1's arena axes is unlabelled, so the rule **cannot run on any frozen V1 frame**. CP0.3b's "re-pin the per-rule counts on the frozen M1 and M4 frames" therefore asserts that the new rule changes **nothing** on those frames — still worth running, since it is what catches a new rule that accidentally reclassifies elements — and every Phase 0d positive and negative control is a figure the test builds, until Phase 2 supplies a real painter. `/api/values` returns **kinds with a count** per square: a number in a table is not a legend on a picture, so it does not cut against Q18's show-don't-encode principle, which is about the drawn frame. **Prior art worth using:** the open Known Bugs row "Chasing rabbit stays glued to the agent after contact" (`core.py:629`) makes agent + rabbit a *frequent* two-mover square in rabbit worlds — a cheap place for CP2.8 to find a real two-mover archetype rather than synthesising one. It is not itself a rendering defect.

---

## Revision 20 2026-09-16 (after plan-reviewer seventh pass: the co-occupancy rule is narrowed to the elements it CHECKS, never to the elements that can COVER something)

**What this revision is about, in plain words.** The reviewer read Revision 19 and came back with **SOUND WITH CONCERNS**: nothing is blocked, no decision the user made is re-opened, and the hole the previous pass found — a drawing that sits in the right place but is painted *underneath* something, so the viewer never sees it — stays closed. What the reviewer found instead is that the new check, exactly as worded, would **shout at a renderer that is doing everything right**. Three of the seven findings are that same shape:

1. The check demands that anything painted after an animal be fully solid. The agent's own soft glow and its drop shadow are deliberately see-through, and because they are painted at the same depth as everything else in the panel, they land *after* the animals of squares drawn earlier. So the demand fails on any frame containing an agent or a campfire.
2. The check demands that everything with ink inside the map panel belong to that panel. The page's own background rectangle — one big off-white rectangle covering the whole dashboard — is drawn by a different panel and lies under the map. So that demand fails on every frame.
3. Nothing in the plan says whether the thin indigo outline round the agent's square, or the thin diamond outlines that show how far a sense reaches, are painted **above** or **below** the animals. Painted above, a sense outline crossing an animal removes roughly seven per cent of that animal's pixels, and the agent's square outline grazes a four-way animal's edge by a fraction of a pixel — either is enough to trip the check on a correct picture.

A false alarm is loud, not dangerous. **The danger is the fix somebody reaches for to silence it**, and the reviewer named it precisely: the tempting move is to stop counting see-through things, or outlines, as capable of covering anything. That would re-open **#54** — the draw-order blindness Revision 19 exists to close — and re-open it *silently*, because the instrument would then report a clean frame while an animal sits invisible underneath a bed.

**So this revision obeys one rule, and every fix below is an instance of it.**

> **The narrowing rule.** A fix here may narrow **which elements and which pixels the rule makes assertions about**. It may never narrow **which elements are capable of covering a token**. The set of things that can cover something — the *occluder set* — stays "every element in the figure".

Two consequences, written out so a later reader cannot take the shortcut by accident:

- **Every precondition below is scoped in terms of `L(p)` — the last-drawn element with ink at pixel `p`** — and `L(p)` is *computed from the full occluder set*. A shortcut that dropped translucent elements or outlines from the occluder set would change `L(p)`, which would change the measured survival numbers the checkpoints record. The narrowing is therefore structurally unable to hide a draw-order defect: it consumes the occluder set rather than editing it.
- **The rule may read a painter-set property only where reading it can make the rule FAIL.** Alpha (§R20.1), face colour (§R20.6) and the outline classification (§R20.7) are all read in the failing direction only. Nothing — not `zorder`, not a `gid`, not an artist class — may ever be read to *exempt* ink from the count. That is finding #3's discipline (the audit must not let the painter under test declare which of its own ink is off-limits), carried into the co-occupancy rule.

**Two further points before the findings.** The reviewer's #65 asks for the survival floor to be *swept* rather than asserted, and this plan already has the precedent: the `out_of_card` title-strip factor was not defended by argument, it was settled by measuring it across a range and showing the chosen value sat in the middle of a gap rather than on a cliff. §R20.3 does the same for `SURVIVAL_MIN`. And #66 is a different kind of error from the rest — the same 0.98 number was carried from the big grid panel to the small World map, where it measures something else entirely and is **unreachable on a correct drawing**; §R20.4 re-grounds it rather than re-tuning it.

**Nothing here re-opens a user decision.** Variant H, the 50 px square, the whole-world grid view, `CELL_PRIORITY`, the minimap's deliberately coded encoding, Q21 and the conditional Q22 all stand exactly as recorded.

**How each finding is handled**

| # | Finding, in one line | Handling |
|---|---|---|
| 🟡63 | Both self-asserted preconditions fail on a correct painter | §R20.1 — both re-scoped to the last-drawn element at a token pixel; bed pinned below tokens; occluder set untouched |
| 🟡64 | Square outline and sense-footprint outlines have no zorder relative to tokens | §R20.2 — both pinned **below** token zorder (a painter change, not an instrument change); controls gain an agent and a footprint edge |
| 🟡65 | `SURVIVAL_MIN = 0.98` is an undefended value | §R20.3 — swept on both sides, `out_of_card` precedent; CP0.3b records a gap table |
| 🟡66 | The minimap floor was transplanted onto a different instrument | §R20.4 — ground truth becomes distinct palette colours of the **kinds** present; denominator measured by the same census on the isolated wedge; a separately swept minimap floor as the fallback |
| 🟡67 | CP0.4's split measures update cost, not draw cost | §R20.5 — three arms (full / arena update off / arena Axes hidden) |
| 🟡68 | An occluder the probe cannot see, because its colour matches the empty canvas | §R20.6 — third precondition that **fails**, mutation M-F1g, and a new entry (d) on the "does not see" list |
| 🟢69–🟢72 | bbox wording, stale `AxesImage` line, spike code disposition, audit cost | §R20.7 |
| 🟠S1 | *(found here, not by the reviewer)* a multi-part bed leaks its small parts into the token count | §R20.8 — the bed is one artist; the existing bed control is specified to use the campfire bed, so the hole is loud at Phase 0d instead of Phase 2 |

### R20.1 The two preconditions are scoped to the last-drawn element at a token pixel (#63)

**What was wrong.** §R19.1 step 6 asserted two things about the whole frame:

- *opacity* — "every element drawn after a token element must be fully opaque". Measured, this fails on ordinary frames. The agent marker's halo is a disc at alpha **0.16** and its drop shadow a disc at alpha **0.12** (`renderer_layout_redesign/dashboard_style.py:340-341`), and the campfire form carries a glow disc at alpha **0.28** (`:319`). Each is drawn immediately before its own body, but they share a zorder band with the rest of the arena, so within one Axes insertion order decides — and they are inserted *after* every token of every square painted earlier. Every frame with an agent or a campfire trips it.
- *one Axes* — "every element with ink inside the arena's extent must belong to the named arena Axes". The dashboard's background is one rectangle drawn in a separate full-figure Axes (`fig03_proposed_dashboard.py:138`, the `bg` Axes), and its ink lies under the whole arena. Every frame trips it.

**The fix, stated once for both.** Let `T` be a square's **token ink** (unchanged: every element inside the square except those excluded by measured area or measured outline shape, per §R19.1 step 2). For each pixel `p ∈ T`, let **`L(p)`** be the last-drawn element with isolated ink at `p`, computed over **every element in the figure**. Then:

- **(a′) Opacity where it decides.** If `L(p)` is **not** a token element of that same square, `L(p)` must be fully opaque (artist alpha `None` or 1.0, and no RGBA face or edge alpha below 1). Otherwise the rule **reports and fails** — it never skips.
- **(b′) One Axes where it decides.** `L(p)` must belong to the named arena Axes. Otherwise the rule **reports and fails**.

**Why this is a narrowing of the assertion and not of the occluder set.** `L(p)` is a function *of* the occluder set: to know which element is last at a pixel you must consider all of them. Nothing is removed from consideration; what changed is that the plan no longer demands opacity from elements that can never be last at a token pixel, nor Axes membership from elements that are painted underneath. Concretely:

- the agent's **halo and shadow** are token elements of their own square, so where they are last, (a′) exempts them — and where a *neighbouring* square's translucent part were ever last over this square's token, (a′) fires, which is the case that actually matters;
- the **background rectangle** is drawn first, so it is never `L(p)` anywhere, and (b′) never sees it;
- a **translucent bed drawn over a token** still fails (the bed is not a token element), and that is correct: the plan will not pass a square whose visibility is undecidable. The way out is to make the bed opaque or to draw it below the tokens, never to stop counting it.

**One painter pin that removes the remaining case.** `cells.py` pins **bed zorder strictly below token zorder** (§R17.3 item 2 already says "above the ground and below every token"; it becomes a constant with a test rather than prose). With that pin a bed's glow can never be "after" a token in the first place.

**The comparator must work across Axes, and that is measured, not assumed.** `_is_painted_over` (`render_layout_audit.py:436-465`) deliberately refuses to order two elements in different Axes, so with (b′) scoped to `L(p)` the audit needs a figure-wide rank to find `L(p)` at all. It is extended to the triple `(axes rank, artist zorder, child index)`, where *axes rank* is the position of the artist's Axes in the figure's own sorted-by-zorder, insertion-stable Axes order — matplotlib's composition rule, not a new invention. An artist with no Axes ranks last-resort and, if it is ever `L(p)`, fails (b′). **This derivation is pinned by a control, not trusted:** CP0.3b builds a two-element figure in two Axes of known zorder, renders it, and requires the composite colour at the shared pixel to agree with the comparator in **both** orders. A derived order that the pixels contradict is a broken instrument, and this is the cheapest place to find that out.

### R20.2 Every arena overlay is pinned below the tokens (#64)

**What was wrong.** Two overlays had no stated depth relative to tokens, and the survival floor punishes both if they land above:

- the agent's **2 px iris square outline** (§R17.3 item 8) — its inner fringe sits 0.1–1.1 px from a four-way token's edge (the token reaches 21.4 px from the square centre, the outline's inner edge 22–23 px), which costs a four-way token on the order of 1–2 % of its pixels: **at the floor**, i.e. exactly where a measurement decides a checkpoint by accident;
- the **sense-footprint outlines** (§D7.3, "foreground artists") — a diamond edge about 1.5 px wide crossing a 20 px token removes roughly 7 % of a 322–336 px² token, which fails the floor outright on a correct picture.

**The fix is in the painter, not in the instrument.** Both are pinned **below token zorder** as constants in `cells.py` / `painters.py`:

- the square outline is drawn on the *square*, and tokens never reach it, so drawing it under them is **no visual change at all** — the outline still reads as the square's border;
- a footprint diamond passing behind an animal is the correct picture anyway: the animal is the subject, the footprint is annotation.

**What is deliberately *not* done:** neither is removed from the occluder set. If a future painter raises either above the tokens, the pixels stop surviving, the floor fires, and the audit names the element — which is the behaviour #54 asked for. The pin prevents a *false* failure; the rule still catches a *real* regression. That asymmetry is the whole point, and it is why "drop outlines from the occluder set" is the wrong shape of fix even though it would also silence the false alarm.

**Controls gain the elements that were missing.** The negative controls in CP0.3b must now include:

- a **two-mover square containing the agent**, so the square outline is present;
- a **four-way square containing the agent**, the tightest case (0.1–1.1 px clearance);
- an **E-cell footprint edge crossing an occupied square**, so the footprint outline is present and measured rather than reasoned about.

All three are negative controls: they must produce **zero findings**, and their measured survival ratios are recorded in the gap table of §R20.3.

### R20.3 The survival floor is swept, not asserted (#65)

**What was wrong.** `SURVIVAL_MIN = 0.98` has a defended *shape* — a correct composition measures exactly 1.000, so any floor below 1 is pure tolerance — and an **undefended value**. The reviewer's arithmetic: 2 % of a 322–336 px² token is only **6.4–6.7 px**, which is a single-pixel seam along at most ~6 px of arc, while a 1 px seam round the token's whole circumference (~65 px) is about **19 %**. The plausible fringe cases — the outline clearance of §R20.2, anti-aliasing where a keyline meets a bed — land at **1–2 %**, i.e. right at the chosen number. A single M-F2 mutation at one inset exercises the floor nowhere near where a real fringe case sits.

**The precedent this plan already set.** The `out_of_card` title-strip factor was not settled by argument either: it was swept, and the chosen value was shown to sit mid-band rather than on a cliff. The same procedure applies here.

**What Phase 0d records — a gap table, pre-registered.**

| Side | What is measured | Requirement |
|---|---|---|
| Correct painter (the floor must be **below** this) | The **minimum** survival ratio over **every** negative control: single occupant; empty square; bed + one token (campfire bed, §R20.8); correct two-mover **with the agent**; correct four-way **with the agent**; footprint edge through an occupied square | Each ≥ 0.98, and any value below **1.000** is investigated and its cause written down before it is accepted |
| Defect (the floor must be **above** this) | The **maximum** survival ratio over an **M-F2 family** — the bed drawn after the tokens at three insets, `0.005 / 0.010 / 0.020 × cell` *(re-registered from `0.02 / 0.05 / 0.10` in Revision 21 §R21.2 — insetting a bed shrinks its ink share below the floor test, at which point it stops being read as a bed and is caught by the disjointness rule instead, so the member stops measuring the thing it was registered to measure. Measured survival at the three new insets: 0.091 / 0.095 / 0.101 and 0.132 / 0.136 / 0.144, all firing the survival floor at **both** 0.40 and 0.48.)* | Every member fails the floor, **via the survival floor and not via another rule** |

*Fails if:* the two columns do not straddle 0.98 with margin, **or** the developer moves the constant to make them straddle it. If the measured gap does not contain 0.98, the developer reports both numbers, the proposed value **and its evidence**, and the value is changed only in this plan text — never in a test to make a red checkpoint green. The three-member family exists so the floor is exercised near a rim-survives case rather than only at the easy end.

### R20.4 The minimap gets its own ground truth and its own floor (#66)

**What was wrong — two separate errors in §R19.1 step 9.**

1. **The floor was transplanted onto a different instrument.** In the grid-panel rule, numerator and denominator are the same kind of measurement (isolated ink, in pixels). In the minimap variant the denominator is a **geometric** expected wedge while the numerator is a **colour-classified composite** (the ΔE census CP-C runs). At the World map's ~24–29 px square the split dot is about 13 px across, so a half-disc is roughly 66 px² with about 33 px of edge: **a third to a half of its pixels are blends** with the white ring, the 0.8 px split line and the terrain tint, and the census does not classify a blend as either occupant's colour. A **correct** split dot therefore cannot reach 0.98 of its geometric wedge. The number was not too strict — it was measuring something else.
2. **"At least as many distinct occupant colours as the snapshot has movers" fails a correct two-predator square.** Two predators are two movers and **one** kind, and §R17.5 item 1 fixed the ground truth as kinds, never instances. A correct painter draws one predator colour there and the rule reports a defect. (The hiding predator is the same colour plus an amber identity pip, so a predator + hiding predator square is also one palette colour with a pip, not two colours.)

**The fix — re-ground both sides on the palette, and measure the denominator with the same instrument as the numerator.**

- **Ground truth** is the set of **distinct palette colours that the kinds present map to**, taken from the colour → meaning map in `src/environment/dashboard/palette.py` (the same table CP-C uses). Two predators → one colour. Predator + hiding predator → one colour, plus the pip check §R17.4 already specifies. Agent + rabbit → two colours. *(**Corrected by Revision 22 §R22.1:** a kind maps to a **set** of colours, not one, because the hiding predator's mark is body **plus** amber accent; distinctness is compared on the sets. The "predator + hiding predator → one colour" reading above is withdrawn — their sets differ, which is what the amber accent exists to make true for the viewer as well as for the census. The denominator is measured over the union of a kind's **own** artists rendered together, replacing the per-element maximum.)*
- **The composite census must find exactly that many distinct occupant colours** inside the map square — the `≥ movers` wording is withdrawn.
- **The area test's denominator is measured by the same census on the isolated wedge**, not computed from geometry: render the wedge artist alone, run the identical ΔE classification on it, and use that pixel count as the denominator. Edge blends are then excluded from numerator and denominator alike, so a correct dot measures ≈ 1.000 and the same reasoning that defends `SURVIVAL_MIN`'s shape applies here too.
- **Fallback, pre-registered:** if the wedge cannot be isolated as its own artist (for example if the split dot is drawn as one artist with two subpaths), the denominator falls back to the geometric wedge and the floor becomes a **separate constant `MINIMAP_AREA_MIN`, swept by the §R20.3 procedure on the minimap's own controls**. It is never `SURVIVAL_MIN` reused, and the sweep is recorded in the same gap table. Which of the two paths was taken is stated in the Implementation Report.
- **M-F3 is unchanged and still the point:** the agent's dot drawn above the split wedge must make the census find one colour where the snapshot's kinds say two.

### R20.5 The speed spike gets a third arm, so the split measures drawing and not just updating (#67)

**What was wrong.** CP0.4 reports the frame time split into "arena-only" and "non-arena" by timing `frame(t)` with the arena painter's update enabled and disabled. But `canvas.draw()` **composes every visible artist in both arms**: switching the arena's *update* off removes the cost of setting its artists' data and leaves the cost of drawing its ~230 visible artists inside the "non-arena" number. That number is exactly what **Q22 option 3** would hold the 0.5× target against — so the option meant to separate "is the architecture right?" from "are we drawing more?" would be decided on a number that still contains the drawing.

**Re-specified: three arms on the same figure, same recording, same worker, artist counts reported unchanged across arms.**

| Arm | What is disabled | What its median means |
|---|---|---|
| 1 | nothing (full frame) | the real per-frame cost |
| 2 | the arena painter's **update** (artists stay visible) | arm 1 minus arm 2 = the arena's **update** cost |
| 3 | the arena **Axes** (`ax.set_visible(False)`) | arm 1 minus arm 3 = the arena's **update + draw** cost; arm 3 itself is the true non-arena number |

**Q22 option 3, if it is ever asked, is scored against arm 3.** Arm 3 is explicitly labelled a **synthetic reference**: it composes a frame no viewer will ever see, which is why it is reported alongside arms 1 and 2 rather than instead of them. The three counts (total artists, arena artists, per-square pool size) are reported once and must be identical across the arms — a differing count means an arm changed the figure rather than what was drawn from it, and the measurement is void.

### R20.6 An occluder the probe cannot see — a third precondition, and it fails rather than skips (#68)

**The one genuinely silent case in the pass.** The audit's ink probe calls a pixel "ink" when rendering an element alone differs from the empty canvas by more than `INK_DELTA = 8/255` per channel (`scripts/eval/render_layout_audit.py:607-614`). The "empty canvas" is the figure with every artist hidden — i.e. **the figure's own facecolor**. An element whose colour is within 8/255 of that facecolor therefore has **no isolated ink at all**, and an element with no ink can neither be counted nor be `L(p)`: it cannot occlude anything, as far as the instrument is concerned.

The numbers are uncomfortably close. The square's neutral ground is `TRACK #ECEEEA` and the page's canvas is `CANVAS #F2F3F0` (`dashboard_style.py:31`) — **6 / 5 / 6** apart, below the threshold. Figure 3 happens to leave the *figure* facecolor at matplotlib's white and paints `CANVAS` as a rectangle in a background Axes, so today the ground differs from white by 19/255 and is visible to the probe. **But nothing pins that for Phase 2.** A build-once renderer that sets `fig.set_facecolor(CANVAS)` — a natural thing to do — would make the ground invisible to the probe, and "the ground square drawn over the tokens", one of the three cases §R19.1 names in its own motivation, would become **undetectable**. The same blindness covers any near-white occluder: a stale-slot eraser rectangle, a neighbour's white keyline.

**The fix — a third precondition, asserted per frame, failing rather than skipping.**

- **(c′) Probe visibility.** Every colour the rule depends on being able to see — the ground fill, **every** bed's base colour, the square-outline colour and the keyline colour — must differ from the **figure facecolor** by more than `INK_DELTA` in at least one channel. The audit reads those colours from the artists themselves (`get_facecolor` / `get_edgecolor`) and compares against `fig.get_facecolor()`. If any is within the threshold, the rule **fails the frame** and names the colour pair and the channel distances.
- This is a read of a painter-set property, and it is in the **failing** direction only — consistent with the narrowing rule at the head of this revision. It can never exempt anything.
- **New mutation M-F1g: the ground square drawn after the tokens.** Distinct from M-F1 (the *bed* after the tokens), because it is the case (c′) exists to keep visible. It must fail. Run together with a facecolor set to `CANVAS`, M-F1g is also the demonstration that (c′) is load-bearing: without (c′) the mutation passes silently.
- **Added to the "does not see" list as (d)**: *an occluder whose colour lies within `INK_DELTA` of the figure facecolor is invisible to the probe and therefore to this rule. (c′) converts that blindness into a failure for the colours the arena actually uses; it does not convert it for a colour nobody has written down yet.*

**Recorded as the plan's position, for Phase 2:** the figure facecolor should stay distinct from `CANVAS` — Figure 3's own arrangement, where the page colour is a drawn rectangle rather than the figure's background. That is a recommendation, not a decision to be taken silently: (c′) is what makes the alternative loud if someone takes it.

### R20.7 The four small findings (#69–#72)

1. **Which bbox `_ink_is_outline` tests (#69).** §R19.1 step 2 says an element "whose ink sits on the perimeter of the square's own box" is excluded. The helper actually tests the perimeter of the **element's own bounding box** (`render_layout_audit.py:414-433`: it builds the core rectangle from the mask's own `bbox` and asks whether under 2 % of the ink falls inside it). Harmless today — every token part is a filled form, and the keyline sits at `z − 0.05`, below its own token — but the wording is corrected to the element's own bbox, **and one guard is added in the failing direction**: the only outline exclusions this rule intends are things that span the square (the agent's square outline, a seam), so an element classified as outline whose bbox spans **less than 80 %** of the square in either dimension is reported as `outline_like_token` and **fails**, rather than quietly leaving the token union. A ring-shaped token part drawn as its own artist is exactly that case, and it must not be able to disappear from the count.
2. **§D1.4's stale raster line (#70).** Setup item 2 still read "a fixed pool of `AxesImage` icon slots per view cell per layer", contradicting the vector decision eight lines below it (Revision 19, #58). Rewritten to a per-square pool of **vector artists**; see §D1.4.
3. **The spike's cell code is disposable (#71).** CP0.4's spike must implement §R17.3's composition — a ground, a bed and up to four tokens per square — to measure it, which is most of what `cells.py` will do. **Decided here: the spike's cell code is scratch.** It lives under `tmp/`, is imported by nothing in `src/`, and does not become `cells.py`; `cells.py` is authored in Phase 2 against its own tests (`test_dashboard_cells.py`). The alternative — letting the spike grow into the module — was considered and rejected: it would put untested painter code into the package ahead of the checkpoint that tests it, and CP0.4's only deliverable is a number. **What carries forward instead is the measurement:** CP0.4 records which forms the spike drew, the per-square artist count and the total artist count, so Phase 2 can reproduce the cost, and CP4 re-measures the real painter regardless. *Fails if:* CP0.4's report omits the forms and counts, or any spike file is imported from `src/`.
4. **The audit's per-frame cost, and how CP2.8 is sized (#72).** Isolation is **N + 1 renders per frame**; a V1 frame at ~100 elements measured ~22 s, and a V2 frame with a 100-square arena carries several hundred more visible elements, so an unoptimised audited V2 frame runs into **minutes**. Three things are specified rather than discovered:
   - **Rank once per frame.** `_draw_index` currently scans an Axes' child list per pair (O(N) per comparison). Build the figure-wide rank of §R20.1 **once per frame** as a `dict[id(artist) → rank]`, so every comparison is a lookup. This is a pure implementation change: the values are identical, and the cross-Axes control of §R20.1 pins them.
   - **Probe only what can reach the arena, measured.** For `cell_overdraw`, an element whose bounding box, padded 2 px, does not meet a given square cannot put ink in that square, so it is not probed for that square. This is a **measured** exclusion from the *work*, not from the occluder set: the padded bbox bounds the element's ink, so `L(p)` is unchanged by construction. The padding is stated as a constant and the equivalence is asserted once in Phase 0d by running one control both ways and requiring identical findings.
   - **CP2.8's sample is sized and stated.** `cell_overdraw` runs on **at most two frames per matrix cell** — one archetype-rich frame plus step 0 — with the archetype coverage carried by the Phase 0d synthetic controls, which are small figures. The test carries the `integration` marker, and the Implementation Report states the measured wall-clock per audited frame on the machine used, so the next person sizing a sample has a number rather than a guess.

### R20.8 A multi-part bed leaks into the token count (found while scoping #63; not a reviewer finding)

**What this is.** §R19.1 step 2 classifies **per element**: an element whose isolated ink covers ≥ 40 % of the square is the bed or the ground and is excluded, everything else inside the square is a token. A bed drawn as **several artists** therefore only has its big part excluded. The campfire form in the design mock is the worked example: `g_campfire` (`dashboard_style.py:315-328`) is a glow disc, two logs and three nested flame teardrops — **six artists**, the largest of which (the glow at radius `0.95 × 0.30 s`) covers about **25 %** of the square, under the 40 % line. Ported to a bed as-is, the flames and logs would be counted as **token** ink: a square holding only a campfire has no non-terrain kinds (`|K| = 0`) but would show one token component, and `cell_overdraw` would fire **on a correct painter**.

This is the same shape as #63 and #64 — an over-scoped classification producing a false failure — and it has the same forbidden fix: widening the exclusion (for example "exclude anything a painter marks as bed", or "exclude anything drawn below the first token") re-opens #54 by giving the painter a way to have ink ignored.

**The fix, in the painter and in the control.**

- **Each bed is exactly one artist.** `cells.py` composes every bed form as a single artist — a compound path, or a `PatchCollection` carrying per-subpath face colours where a bed needs more than one colour (the campfire does: glow, logs, flame core). Its ink then covers ≥ 40 % of the square as a whole and the existing area test excludes it whole. This is a constraint on Phase 2, stated now so it is a design input rather than a surprise.
- **The bed-plus-token negative control uses the campfire bed**, not a plain rectangle — the campfire is the bed with the most parts and the only one whose largest part is under the 40 % line. With it, a multi-part bed is caught at **Phase 0d**, loudly, on a control built for the purpose, instead of at Phase 2 as a mystery failure on a real frame.
- **No change to the occluder set, and none to the area test itself.** The number stays a measurement of ink area; what changes is that the painter must present a bed as one thing to be measured. *(**Revision 21 §R21.2 moved the number itself, 0.40 → 0.48**, for the mirror-image reason: the classifier was also wrong from the *token* side, where a correct lone agent measured 0.4376 and was read as floor. The shape of the test is untouched.)*

**Verification note (senior-developer, 2026-09-16).** Revision 20 was written in a session that died mid-edit, so it was verified clause-by-clause against the seventh pass before Phase 1 builds from it. Findings #63–#72 and §R20.8 are all resolved, and the narrowing rule holds everywhere — no fix removes anything from the occluder set. **One edit was genuinely lost and has been completed during verification:** §D5.2's *mutation and negative-control list* — the paragraph an implementer actually builds Phase 0d from — had not been updated, while §D5.2 item 11's rule paragraph, CP0.3b and the Phase 0d File Changes rows all had. It still named **three** M-F variants (no `M-F1g`), still carried the pre-Revision-20 negative partners (no campfire bed, no agent in the shared squares, no footprint edge), asserted a bare `1.000` that contradicts §R20.3's investigate-below-1.000 rule, and repeated the uncorrected "perimeter of the square's own box" wording that §R20.7 item 1 fixed in §R19.1. All four are now aligned with §R20.1–§R20.8, and **CP2.8's *Fails if:* clause**, which enumerated `M-E / M-F1 / M-F2 / M-F3`, now includes `M-F1g` so the gate covers the mutation its own body requires. This was the §R19.2 (#56) failure mode — two sections of one plan disagreeing, with Phase 0d reading the stale one.

---

## Revision 21 2026-09-17 (after verifying Phase 2 and Phase 0d together: the speed target is accepted as met in substance, the floor constant moves, and this plan's own halo rule is corrected)

**What this revision is about, in plain words.** Two pieces of work were checked at once. The first (Phase 2) wrote the code that actually draws the new dashboard, and ended with a complete picture of the campfire world rendered from a real recording. The second (Phase 0d) built the *measuring instrument* for the one claim this whole redesign exists to make good: that a square of the world holding two things is drawn showing **both** of them, rather than one covering the other. The instrument agrees with the picture — on the rendered frames every occupant keeps 100 % of itself — and the frames were looked at, at full size, by the verifier: the square holding the agent and a bush shows a green bush plate with the agent standing on it, and a later frame shows the agent and a piece of food side by side in one square. That is the defect fixed, seen and measured.

Three things are decided here, and they are decisions rather than findings.

1. **The speed target is accepted as met in substance (question Q22 is closed by the user).** The new renderer draws a frame in 187 ms against the current renderer's 333 ms — **1.78× faster** — but the target written down earlier was "at most half the time", i.e. 167 ms, so it misses by about 21 ms. The measurement that matters is the breakdown: the big world-grid panel, which is the thing that grew four-fold and the reason the target was ever questioned, costs only **11 of those 187 ms (about 6 %)**. The rest is the text-heavy cards. Blocking on 21 ms, or re-writing every painter in a second drawing toolkit to attack the wrong 6 %, would both be spending real effort on a number that is not the problem. The user chose to treat the target as met and to record why.
2. **The "this is scenery, not an occupant" threshold in the audit is wrong and moves from 40 % to 48 % of a square.** The audit decides whether a drawing is the *floor* of a square (a bush, a rock) or an *occupant* (an animal) by how much of the square it covers. At 40 % a **correct** picture fails: a lone agent on bare ground keeps its soft halo, and that halo makes the agent cover 43.8 % of its square — so a real occupant is classified as scenery and the square reports "nothing is standing here". The two populations the threshold has to separate were measured, not argued: the largest correct occupant covers 0.4376 of its square, the smallest floor covers 0.5168. 48 % sits about halfway between them.
3. **This plan's own rule for the agent's halo is corrected.** It said the halo is dropped when a square is "shared", and defined sharing as two or more *occupants* — with terrain deliberately not counting. A lone agent on a bush therefore kept a halo wider than the entire bush beneath it, and rendered as an agent alone: the original defect, in a new form, written into the fix. The rule is now "dropped whenever the square holds any other occupant **or a bed**".

### R21.1 Q22 is answered: the gate counts as met, and the number is recorded so it is defensible later

**The user's decision: accept 1.78× and close Q22.** Q9's `≤ 0.5 ×` is **superseded by the measured result**, not renegotiated in the abstract, and no option from Q22's table is adopted: not option 1 (hold the number and risk pivoting to Pillow over 21 ms), not option 2 (a synthetic like-for-like arm), not option 3 (re-scoring against the non-arena part), not option 4 (re-architecting the per-square artist pool).

**The evidence, kept here so the number does not have to be re-argued:**

| Arm (same recording, same process, 40 frames, first 5 excluded, in-container) | Median |
|---|---|
| V1, the renderer training uses today | **333.0 ms** |
| V2, this renderer (arm 1, full frame) | **187.3 ms** |
| V2 with the arena Axes hidden (arm 3, the true non-arena number) | **176.1 ms** |

- **Ratio 0.563** against a `≤ 0.500` gate — missed by 0.063, i.e. **~21 ms**.
- **Arena cost = arm 1 − arm 3 = 11.2 ms of 187 ms ≈ 6 %** of the frame, drawn with **178 of the frame's 1045 visible artists**.
- The hard floor — never slower than the production renderer — holds with a **1.78×** margin, and that is the part protecting training-time rendering.

**Why accepting is the right call rather than the convenient one.** Q9's half-the-time number was explicitly a *proxy for the architecture paying off* (V1 rebuilds its whole figure every frame; V2 builds once and updates). The architecture did pay off: 1.78×. The proxy was written before the panel grew from 25 squares to 100, and the split now shows the growth is not what costs the time — so a miss of 21 ms carries none of the information the gate was set up to carry. Blocking would licence exactly the response §R19.3 warned about: "pivoting to Pillow … the most expensive move available in this plan, for a reason that is not the toolkit's fault."

**What would re-open it, stated so the acceptance is not open-ended.** CP4 still re-measures on a lab node, in a pool worker, over ≥ 200 frames. The acceptance is of **this** ratio on that measurement; it is re-opened if CP4 shows V2 **slower than V1 on any cell** (the hard floor, untouched), or if the arena's share of the frame rises above ~25 %, which would mean the arena *has* become the cost and the original Q22 premise has become true after all.

**CP0.4 itself remains formally unrun** — lab node, pool worker, ≥ 200 frames, node and CPU model recorded — and it is **not** waived by this decision. What is decided is the *response to the band it landed in*: the pre-registered "report and stop" has been reported, asked and answered, so Phase 2 is no longer gated on it.

### R21.2 The 40 % floor is wrong in the plan text, and moves to 48 %

**The defect, in one sentence.** §R19.1 step 2 excludes "an element whose isolated ink covers ≥ 40 % of the square" as the bed or the ground — and a *correct* lone agent covers **43.76 %**, so the rule throws the occupant away as scenery and reports 0 components where the snapshot says 1. It is the exact mirror of §R20.8, which found the same classifier wrong from the bed side.

**The measured populations, which make this arithmetic and not argument:**

| Quantity | Value | Where it comes from |
|---|---|---|
| Largest **correct token** ink share | **0.4376** | a lone agent with its halo, measured by the audit's own probe |
| Smallest **bed** ink share | **0.5168** | the smallest of rock / bush / tree / campfire, measured |
| Bed plate fraction **by construction** | **0.5184** | `(1 − 2 × BED_MARGIN)² = 0.72²`, pinned in `test_dashboard_cells.py` |
| **New floor** | **0.48** | `(0.48 − 0.4376) / (0.5168 − 0.4376) = 53.5 %` of the way up the gap |

**Verified independently during this verification, not taken from the report:** at a 0.48 floor the lone-agent control and the campfire-bed, bush-bed and four-way controls all produce **zero findings**; the developer's 43.76 % / 51.68 % figures reproduce; and the whole control suite is **66 passed, 1 xfailed**.

**The alternative was considered and is rejected: do not drop the halo on every square.** The halo is not decoration — it is what makes the agent findable at a glance in a 100-square grid, and a lone agent on bare ground is precisely the case where nothing else needs the room. More importantly, a token covering 43.76 % of its square **is an occupant**; a classifier that calls it floor is wrong about the world, and shrinking the picture until the classifier's mistake stops showing is fixing the evidence rather than the instrument. The constant is what is wrong, and §R20.3's procedure — move it in the plan, with its evidence, never in a test — is what is followed here.

**One consequence the move has, found while verifying and fixed here rather than left to surface in Phase 0d.** The defect side of §R20.3's gap table is an **M-F2 family** — the bed drawn over the tokens, inset so a rim survives — pre-registered at insets `0.02 / 0.05 / 0.10 × cell`. Insetting a bed shrinks its ink share (`(0.72(1 − 2i))²` → 47.8 % / 42.0 % / 33.2 %), and once it falls under the floor test it stops being classified as a bed, is read as a token, and is caught by the **disjointness** rule instead. At the shipped 0.40 floor only the 0.10 member had fallen out; **at 0.48 the 0.05 member falls out too**, leaving the survival floor with a single positive control. Measured here across both floors:

| Inset | Fires the **survival floor** at 0.40? | at 0.48? | Survival ratios |
|---|---|---|---|
| 0.020 | yes | **yes** | 0.101 / 0.144 |
| 0.050 | yes | **no** (read as a token) | — |
| 0.100 | no | no | — |
| **0.005** | yes | **yes** | 0.091 / 0.132 |
| **0.010** | yes | **yes** | 0.095 / 0.136 |

**The family is therefore re-registered at `0.005 / 0.010 / 0.020 × cell`**, which exercises the floor at both constants and keeps three members rather than one. The developer's exclusion of the 0.10 member from the gap maximum, with its reason, is judged **honest**: a member that fires through a different rule has a survival ratio of 1.0 and would have *raised* the recorded maximum toward the floor — i.e. the convenient move would have been to keep it and claim a wider margin, not to drop it. Dropping it is the conservative direction.

**What the developer must change, and where (this is the plan's instruction, not a code edit made here):**

| Site | Change |
|---|---|
| `scripts/eval/render_layout_audit.py:832` | `CELL_FLOOR_FRACTION = 0.40` → `0.48`, with the two measured populations named in the comment |
| `scripts/eval/render_layout_audit.py:193, 262` | the module docstring's two statements of the constant |
| `tests/env/test_render_audit_controls.py:810-822` | remove the `strict` xfail; the lone-agent control joins `NEGATIVE_CELLS` as a plain negative control |
| `tests/env/test_render_audit_controls.py:850` | `assert token > audit.CELL_FLOOR_FRACTION` inverts to `token < audit.CELL_FLOOR_FRACTION < bed`, which is the property that actually has to hold |
| `tests/env/test_render_audit_controls.py:864-869` | the `M-F2` insets become `0.005 / 0.010 / 0.020`, and the gap-table test asserts **three** floor-firing members rather than "whatever is left" |

*Fails if:* the constant is moved anywhere other than alongside this evidence; the lone-agent control is made to pass by shrinking the halo instead; or the gap table is left with fewer than three members that fire the **survival floor** specifically.

### R21.3 §R17.3 item 8 is corrected: the halo goes when a bed is present too

Recorded in full at §R17.3 item 8. In short: `n ≥ 2` was the wrong condition because terrain does not count towards `n`, so the literal rule kept a halo reaching `0.396 × cell` over a bed spanning `0.36 × cell` — wider than the floor beneath it — and "agent in a bush" still rendered as an agent alone. Phase 2 caught this **on a rendered frame**, deviated deliberately, and reported it; the deviation is **accepted** and the plan text now says what the painter does. Nothing is filed in the Known Bugs registry: this was a defect in a plan's rule text, caught before the behaviour ever shipped.

### R21.4 Three carried items, judged

1. **Beds are full-bleed plates, not the design mock's silhouettes — and that deviation is right.** The mock's rock and tree cover roughly 28–36 % of a square. Ported as-is they would fall under the floor test and be classified as *occupants*, so `cell_overdraw` would fire on a correct painter — the §R20.8 failure mode arriving from the other side. The plan's own words for a bed are already "drawn full-bleed, inset by `BED_MARGIN` on every side" (§R17.3 item 2), which is what shipped: `0.72² = 51.84 %` by construction, 53.4 % and 51.7 % measured on the real frame. The visual cost is real and is not hidden — a bush now reads as a green plate rather than as a bush silhouette — and **CP-D is the right place to judge that**, with `visual-design-reviewer` looking at a rendered frame. The classification is not the reason to keep it: a silhouette bed could also have been kept by giving beds their own measured rule. The reason to keep it is that variant H *is* "terrain is the floor", and a floor that covers a third of its square is not a floor.
2. **`assets/dashboard_icons/` is unused, and should be dropped — but not yet.** Confirmed: nothing under `src/`, `scripts/` or `tests/` reads it. The frozen V1 renderer loads its icons from the **`assets/` root** (`renderer.py::_load_icons`, filenames like `agent.png`), so dropping the subfolder cannot touch V1. The only reference anywhere is `v1_path_guard.py:145`, which lists it as **plan-owned**, not frozen. §R19.4 item 1 set the condition for dropping it — "every form including the map marks is vector" — and Phase 2 reports that condition met. **Decision: drop it, at CP-D, not now.** CP-D is the checkpoint at which `visual-design-reviewer` may still ask for a raster texture somewhere in the frame, and deleting nine committed PNGs a week before the only checkpoint that could want them buys nothing. The deletion carries the `v1_path_guard.py` row with it in the same commit.
3. **The CP1 band-card hoist has never been exercised by a real world, and will not be until the sensor-band painter exists.** No maintained config has a sense at range ≥ 1, so every maintained world takes the no-band path and the "more than one band card" refusal is unreachable there. Its only coverage is the **synthetic** thermal-plus-band contexts in the Phase 1 suite (§R19.4 item 3 pre-registered exactly this). That is adequate for now and is **recorded as a known coverage gap**: the band painter, when it is written, is where the hoist is first exercised for real, and Phase 2's report saying so is the behaviour wanted, not a defect.

---

## Revision 22 2026-09-17 (the World map's three contradictions are decided: one is the instrument's fault, one is this plan's, one is the encoding's — and the floor does not move)

**What this revision is about, in plain words.** The dashboard has two pictures of the world: a big grid panel that draws every square at 50 pixels, and a small "World map" in the left column that draws the same world at about **18 pixels** a square. At that size no shape survives, so the small map gives up drawing *what* things are and encodes them as **colour** instead — a deliberate, recorded exception to this project's rule that a viewer should recognise things by seeing them rather than by decoding a legend.

Until this week the check that measures the small map could not run at all, because it needs to be pointed at a drawing area that *is* the map grid, and the map was drawn into the whole card — title, caption and all. That has been fixed, the check now runs, and it **reports two to four defects per frame on frames that are correct**. Three separate causes were measured (not guessed) by hiding one kind of drawing at a time and re-running:

- **(A)** The small amber dot that marks a *hiding* predator — the thing that tells it apart from an ordinary predator, which is nearly the same colour at this size — is drawn on top of its own animal's colour patch and covers about a fifth of it. The check counts that as "this animal has been painted over".
- **(B)** When three things share a square, the third is drawn as a small pip on the square's rim. The plan's own words say that pip sits **outside** the central dot. The painter draws it **overlapping** the dot, so it eats into the neighbour's colour.
- **(C)** When four things share a square, the map has no way to show the fourth at all: it simply is not drawn.

**The three do not share an answer, and none of them is answered by relaxing the check's tolerance.** (A) is a gap in the *measuring instrument*: it assumes one colour per kind of animal, and the hiding predator's mark is deliberately drawn in **two** colours. (B) is a straightforward contradiction between the plan and the painter, and this revision works out which of the two is wrong — the answer is **both**, because the pip size the painter chose makes the plan's "outside the dot" geometrically impossible. (C) is a real limit of the encoding, and this revision extends the encoding rather than recording another excuse.

**Nothing here moves a threshold.** Revision 21 moved one constant (the 40 % "this is scenery" line) and that was right, because a *correct picture* genuinely failed it. None of (A), (B), (C) is that shape: each is a drawing overlapping a drawing, or an occupant with nowhere to be drawn. Moving the map's floor to absorb them would be fitting the instrument to the defect — the exact move §R20's narrowing rule exists to forbid. §R22.4 states the test that separates the two cases, so the distinction is reusable rather than asserted.

**~~All three are contingent on an open user question.~~ Q21 is ANSWERED (user, 2026-09-17): the World map stays, as a minimap.** The question — whether the small map still earns its place now that the big grid panel shows the whole world — was put to the user with the cost of keeping it attached, and the user chose to keep it knowing that choice buys the painter change and the instrument change below. **All three repairs are therefore live**, and §R22.5's dissolution table is kept only as the record of what was weighed. The decision is recorded in **Decided questions** and is not re-opened — not here, not at CP-D.

### R22.1 (A) The identity pip is not an occluder — the census is missing the idea of a mark drawn in two colours

**What the instrument currently does.** `minimap_overdraw` (`scripts/eval/render_layout_audit.py:1309`) classifies the pixels of the finished image against a table of **one colour per entity name** (`MINIMAP_PALETTE`), and for each kind present it requires the composed image to retain ≥ `SURVIVAL_MIN` (0.98) of the colour area that kind covers when its artist is drawn alone. The denominator is a **per-element maximum** (`:1375`: `den = max(den, census(solo(e), …))`) — the single best artist, never the union of a kind's own parts.

**Why that fires on a correct painter.** A hiding predator's map mark is deliberately **two** paints, not one: the body colour `HIDE_BODY #2B3442` plus the amber accent `HIDE_EYE #F59E0B` that tells it from an ordinary predator (`PRED #1F2733`, which differs from the body by only 15/255 per channel — a distinction the census can just barely make and a human at 18 px cannot make at all). The census counts only the body colour, so the amber accent reads as **missing body area**: measured 92 / 87 / 88 px against 116 / 113 / 115 px with the accent hidden, i.e. the mark "loses" ~21 % of itself to its own second paint.

**This plan already solved this exact problem once, on the other panel.** §R19.1 step 5 pins the grid panel's denominator as the **union of the token's own parts**, with the reason written out: *"a token's own parts overdrawing each other (the eye over the body, the ring over both, the chevron over the ring) never reduces it — those pixels are in the union and they survive."* The minimap variant was written with a single-colour ground truth and never inherited that clause. **(A) is therefore a defect in the instrument, and it is the same defect §R19.1 step 5 names, arriving on the panel that did not get the fix.**

**The decision — the ground truth becomes a kind's colour SET, and the denominator its own artists measured together.**

1. `MINIMAP_PALETTE` gains a second form: each kind maps to the **set of palette colours its own map mark is drawn in**. Every kind keeps one colour except `hiding_predator`, which is `{HIDE_BODY, HIDE_EYE}`.
2. The **numerator** for a kind is the composite pixels matching **any** colour in its set.
3. The **denominator** is the same census run over that kind's **own artists rendered together, alone** — wedge/dot *and* its identity pip — replacing the per-element `max`. Edge blends are then excluded from numerator and denominator alike, exactly as §R20.4 already argues for the split dot, and a correct mark measures ≈ 1.000 with no floor change.
4. **Distinctness is computed on the sets, not on single colours.** Two kinds collide only if their sets are equal; `hiding_predator` and `predator` remain distinct.

**Why this is not an amnesty, and the guard that keeps it from becoming one.** The risk of letting amber count towards `hiding_predator` is that some *other* amber thing could then paint over a hiding predator undetected. Today nothing else on the map is amber — `MINIMAP_COLOUR` contains no amber, and `HIDE_EYE` is drawn only for `hiding_predator`. That is a fact about today's painter, so it is asserted rather than assumed: **a test requires that no minimap artist other than a hiding predator's identity pip paints `HIDE_EYE`**, and it fails if one ever does. Consistent with §R20's discipline, this reads a painter property **only in the failing direction**.

**A latent case the developer's evidence did not contain, found while deciding this, and it makes (A) larger rather than smaller.** The identity pip is a `Circle` fixed at the **square's centre** (`painters.py:318`) and is shown whenever the hiding predator is one of the **two** occupants the dot carries (`:367`, `if "hiding_predator" in occ[:2]`). On a **shared** square the dot is two half-discs, so a centred amber pip straddles **both** — it eats the *neighbouring kind's* colour, not only its own. Every finding behind (A) came from **solo** squares, so this case is unmeasured, and the union fix above must **not** absorb it: amber over a foreign wedge is a real occlusion. The fix is in the painter (§R22.3 item 4) and the control that proves the distinction is mutation **M-F4** (§R22.6).

### R22.2 (B) The painter is wrong, and so is §R17.4 — "outside the dot" is unachievable at the pip size the painter chose

**The contradiction, stated exactly.** §R17.4 says the third occupant *"becomes a **rim pip** at the square's lower-right, 12 % of the square, **outside the dot**."* The painter (`painters.py:316`) draws `Circle((cx + 0.26·cell, cy − 0.26·cell), 0.12·cell)` — radius `0.12 × cell`, centred `0.26√2 = 0.3677 × cell` from the square's centre — so its inner edge lies at `0.3677 − 0.12 = 0.2477 × cell`, **inside** the dot's `0.30 × cell`. At the measured 18.40 px square that is 0.96 px of overlap, and the pip eats the wedge it sits on.

**Which of the two is wrong is a question with an arithmetic answer, so here it is.** Write `r_d = 0.300` (dot radius), `r_p` (pip radius), both in cell units; the dot's white ring is 1.2 px (half-stroke 0.0326 cell at 18.40 px) and the pip's 0.8 px (half-stroke 0.0217 cell); the square's ground plate is inset 1 px, so the drawable half-extent from the centre is `cell/2 − 1 = 0.4457 cell`. A pip on the lower-right diagonal at radial distance `d` must satisfy both:

- **clear the dot** — `d ≥ r_d + 0.0326 + r_p + 0.0217`
- **stay inside the square** — `d/√2 + r_p + 0.0217 ≤ 0.4457`

Eliminating `d` gives the whole answer in one line:

$$r_p \;\le\; \frac{\sqrt{2}\,(0.4457 - 0.0217) - (0.300 + 0.0326 + 0.0217)}{1 + \sqrt{2}} \;=\; 0.1016\ \text{cell}$$

**So the painter's `0.12 × cell` is infeasible by construction** — there is no placement of a pip that size that is both outside the dot and inside the square — and **§R17.4's "outside the dot" is achievable only at a pip ~15 % smaller in radius**, with the feasible band collapsing to a single value of `d` exactly at `r_p = 0.1016`. For real clearance the pip has to come down to about `0.085 cell`, which at 18.40 px is a **3.1 px disc**; subtract its own 0.8 px white ring and the colour core the census has to classify is roughly **4–7 px**. That is below the size at which either the census or video compression can be relied on to preserve it.

**The verdict, and it goes against both documents.** §R17.4's "outside the dot" was **never achievable at this square size as a rim pip**, and the painter's pip is **not a permissible reading of it** either. Neither is simply "right". The plan does not get to keep a rule whose own geometry it never checked, and the painter does not get to quietly overlap the dot while the spec says otherwise. **The rim pip is retired** (§R22.3), which is the only repair that does not trade one of legibility, measurability or truthfulness for another. Two alternatives were worked out and are recorded so the choice is visible rather than asserted:

| Repair | Does it work? | Why it is not chosen |
|---|---|---|
| Shrink the pip to `r_p ≤ 0.1016 cell` and push it to the corner | Geometrically yes | Its classifiable colour core falls to ~4–7 px — at or below what the census can see and what compression preserves, so it converts a loud failure into a fragile pass. It also leaves **(C)** untouched |
| Shrink the **dot** to `0.22 cell` whenever a rim pip is drawn (which makes `r_p = 0.12` feasible) | Yes — the bound above becomes `r_p ≤ 0.1347` | Introduces a dot whose size changes with occupancy, so the map's marks stop being comparable square to square; and it too leaves **(C)** untouched |

### R22.3 (C) The encoding stops at three, and is extended to four — the same ceiling the grid panel already has

**What was measured.** On a four-way square the fourth kind by `CELL_PRIORITY` measures **1 px** — it is not drawn at all. §R17.4's encoding genuinely stops at "the third becomes a rim pip", so this is the encoding's limit rather than a painting defect.

**Why this is not recorded as an accepted limit, though this plan has precedent for doing that.** §R17.5 item 1 records exactly such a limit — two predators render as one token — and aligns the instrument to it (ground truth is *kinds*, never instances). The difference is that multiplicity is **unrepresentable without a legend** (a numeral or a badge), whereas a fourth occupant is representable with the encoding the map already uses: the dot is already being divided. Recording a limit is honest when the alternative is a legend; here the alternative is one more wedge.

**The decision — the dot is divided among the occupants, `n = 1…4`, and the rim pip is gone.**

1. **`n = 1`** — one whole dot at `0.30 × cell`, unchanged.
2. **`n = 2`** — two half-discs, unchanged (this is what ships and what the controls already cover).
3. **`n = 3`** — three wedges of 120°. **`n = 4`** — four wedges of 90°. Same radius, same 0.8 px white split lines, same white ring: **no new constant, no new mark, and nothing drawn outside the dot.**
4. **The identity pip moves from the square's centre into its owner's own wedge** (its centroid, radius scaled to fit within that wedge), for `n ≥ 2`. At the centre it straddles every wedge — which is the latent defect §R22.1 found — and in its own wedge it annotates only the mark it belongs to.
5. **Occupants are taken in `CELL_PRIORITY` order**, unchanged, so the agent (priority 1) can never be the one dropped if a square ever holds more than four kinds.
6. **The ceiling becomes four, matching the grid panel's four slots** (§R17.3 item 3 defines `n = 1…4`). A square holding five or more kinds is out of scope for **both** panels and inherits the grid panel's existing unstated behaviour; recorded here as a known limit rather than fixed, and cross-referenced from §R17.5.

**One pre-registered risk, with its decision rule written down before the measurement — because this is the branch where a later ad-hoc fix would be tempting.** At 18.40 px a quarter wedge is roughly 24 px² of geometry before the white split lines and ring blends are removed, and the census deliberately classifies a blend as **neither** colour. If a correct four-way square's fourth wedge classifies at a **non-zero** count, the ratio test is scale-free (numerator and denominator are the same census) and it measures ≈ 1.000 — the design holds. If it classifies at **zero**, the denominator falls back to geometry with the `MINIMAP_AREA_MIN = 0.55` floor and the rule fires on a correct picture.

- **If it measures zero**, the answer is **not** to lower a floor and **not** to widen `MINIMAP_DELTA`. It is evidence that the map cannot encode four at this square size, and the pre-registered response is to **fall back to a stated ceiling of three** — encode three, and say on the card, in words, that a fourth occupant is not shown — which is §R17.5's honest-limit pattern applied only after the measurement earns it.
- Either branch is truthful; what would not be is discovering the zero and quietly retuning a tolerance to hide it.

### R22.4 Why the floor does not move here, when Revision 21 moved one

The user's challenge is the right one to answer explicitly: this plan has already moved a constant in plan text with measured evidence (Revision 21 §R21.2, the 40 % → 48 % scenery line), so what makes that legitimate and this not? **The two cases are separated by a test, not by taste:**

> **Move the constant when a picture that is correct *as drawn* is misclassified by the number. Fix the drawing, or the ground truth, when the picture contains ink overlapping ink — or an occupant with no ink at all.**

Applied:

| | What the picture actually contains | Verdict |
|---|---|---|
| **R21.2** (moved) | A lone agent on bare ground, drawn exactly as designed, nothing overlapping anything. Two populations measured and **separated** — largest correct token 0.4376, smallest bed 0.5168 — with the constant sitting in the empty gap between them | The **number** was wrong; the picture was right |
| **(A)** | The instrument's model of a mark says one colour; the mark is drawn in two | The **ground truth** was wrong; neither the number nor the picture |
| **(B)** | A pip's ink overlapping a neighbour's ink, by 0.96 px, in contradiction of the spec's own words | The **drawing** was wrong (and so was the spec) |
| **(C)** | An occupant with **no ink at all** — 1 px | The **encoding** was wrong |

Only the first is a threshold question. For (A), (B) and (C) a lower floor would make the instrument agree with a picture that is wrong — and would do it *silently*, since the same loosened floor would also stop catching the draw-order defect the whole redesign exists to prevent. `SURVIVAL_MIN` (0.98), `MINIMAP_AREA_MIN` (0.55), `MINIMAP_DELTA` (12) and `MINIMAP_ALIGN_MAX_BLANK` (0.5) are **unchanged by this revision**, and the *Fails if:* clauses below say so.

### R22.5 What Q21 would have dissolved — the branch that was NOT taken

> **CLOSED 2026-09-17 (user decision): the World map is KEPT, as a minimap.** This section is retained because the reasoning is worth preserving — it is the record of what keeping the map was weighed against — but it is **not a standing option**. The "drop" and "repurpose" rows below are decided against and must not be re-proposed; the §R22.7 repair is the agreed cost of the answer the user gave. See **Decided questions**.

**Q21 was unanswered when this revision was drafted**, with the recorded working assumption "keep the World map, `LEFT_W = 320`" (§R19.4 item 5). §R19.4 item 5 and the Q21 entry both said **Q21 must be answered before Phase 2 starts the minimap** — and Phase 2 *had* already built it, so that gate was crossed. That is recorded as a fact rather than a reproach: it is why three decisions were taken on a panel whose existence was formally undecided, and it is why the cost was put in front of the user before the work was implemented. **The user answered: keep it.**

| Answer to Q21 | (A) identity pip | (B) rim pip | (C) fourth occupant | Also dissolved |
|---|---|---|---|---|
| **Keep the map as specified** (the working assumption) | Must be fixed (§R22.1) | Must be fixed (§R22.3) | Must be fixed (§R22.3) | — |
| **Drop the map** | **Dissolves** | **Dissolves** | **Dissolves** | `minimap_overdraw`, `minimap_caption` and `minimap_grid_unaligned` become dead rules; CP2.8's minimap clauses, CP-C's split-wedge clause and the §R17.4 on-page statement are all struck; ~236 px of left-column height is freed (Q21 already records that the grid square gains **at most 3 px** from it) |
| **Repurpose it as a "where is the agent" map** — one dot per square, no per-kind colour | **Dissolves** (no identity pip) | **Dissolves** (no rim pip) | **Dissolves** (nothing to rank) | The whole coded encoding of §R17.4 goes, and with it the show-don't-encode exception this plan had to argue for |

**The consequence for how Q21 was asked, and how it was answered:** "keep it" was no longer the free option it was when Q21 was written. Q21's own text said keeping it *"costs nothing that is not already spent"* — true of **layout**, not of **work**: keeping it buys the painter change and the instrument change in this revision, plus their controls. **The user was given that cost explicitly and chose to keep the map anyway.** The cheap branch was available — dropping or repurposing the map would have dissolved (A), (B) and (C) in one edit and made this revision moot — and it was declined. That is the decision; the repair is the price of it.

**What this revision does *not* do:** it does not assume an answer. Every change specified here is scoped to the "keep it" branch and is listed in one place (§R22.7) so it can be struck in one edit if the user drops or repurposes the map.

### R22.6 The controls, because a fix nobody can see fail is not a fix

Pre-registered, in the style CP0.3b already uses — each must be a **figure the test builds**, and the correct partner must be silent:

- **M-F3 (unchanged, must still fire):** the agent's dot drawn above the split wedge. The union fix of §R22.1 must not silence it — the agent's colour set and the hiding predator's are disjoint.
- **M-F4 (new, and it is today's painter):** the identity pip drawn at the **square's centre** on a shared square, so it straddles a foreign wedge. **Must fire**, naming the foreign kind. This is the mutation that proves §R22.1's union fix did not become a blanket amnesty — and reverting `painters.py:318` to a centred circle is literally how it is produced.
- **M-F5 (new):** any minimap artist other than a hiding predator's identity pip painted `HIDE_EYE`. **Must fire.** This is the guard that keeps the amber exemption honest as the painter changes.
- **Negative controls, each zero findings, each recorded with its measured ratio:** a solo hiding predator **with** its identity pip (the exact square that fires today); a two-occupant square containing a hiding predator, pip in its own wedge; a correct three-way; a correct four-way; a correct two-predator square (one kind, one colour — §R20.4's case, which must stay silent).
- **The four-way census count is recorded as a number, not a verdict** (§R22.3 item 6's branch point): the report states the classified pixel count of the smallest wedge and which denominator path was taken (`isolated-wedge` or `geometric`).

*Fails if:* any floor or delta constant is changed to make a control pass; M-F4 or M-F5 is silent; the four-way's branch is taken without its measurement recorded; or a correct control's ratio is below 1.000 without an investigation written down (§R20.3's standing rule).

### R22.7 What the developer must change, and where (the "keep the map" branch only)

This is the plan's instruction, not a code edit made here. ~~If Q21 answers "drop" or "repurpose", every row below is struck instead.~~ **Q21 is answered — the map is kept — so every row below stands and was implemented on 2026-09-17** (see the Implementation Report "§R22.7: the World map's wedges, and CP2.8's committed home").

| Site | Change |
|---|---|
| `scripts/eval/render_layout_audit.py:872` `MINIMAP_PALETTE` | Kind → **set** of its own palette colours; `hiding_predator` → `{HIDE_BODY, HIDE_EYE}`, every other kind a singleton. Keep it a copy of the package table, and keep the anti-drift test (§R22.1) |
| `scripts/eval/render_layout_audit.py:1368-1379` | Numerator matches **any** colour in the kind's set; denominator becomes the same census over the union of **that kind's own artists rendered together**, replacing the per-element `max`. The `geometric` fallback and `MINIMAP_AREA_MIN` are untouched |
| `scripts/eval/render_layout_audit.py:1354-1357` | Distinctness compares colour **sets**, not single colours |
| `src/environment/dashboard/painters.py:305-322` | The per-square pool becomes **up to four wedges** plus the whole dot; the **rim pip is removed** |
| `src/environment/dashboard/painters.py:338-368` | `n = 3` → three 120° wedges, `n = 4` → four 90° wedges, `CELL_PRIORITY` order unchanged; the identity pip is placed at its **owner's wedge centroid** for `n ≥ 2`, centre for `n = 1` |
| `src/environment/dashboard/painters.py:324-327` | The card caption is rewritten to match the encoding that ships and to keep §R17.4's on-page statement true — it must still say, in words, that **colour is the code here** and that the grid view shows what the occupants are. The audit keys on the substring `shared square` (`SHARED_CAPTION`), which the new text must still contain |
| `tests/env/test_render_audit_controls.py:1098-1176` | The synthetic minimap figure gains the three- and four-wedge cases and the identity pip; M-F4 and M-F5 added; the negative controls of §R22.6 added |
| `docs/environment/12_renderer.md` | The minimap's encoding paragraph records the `n = 1…4` split, the retired rim pip, and the four-kind ceiling — in the same change as the painter (§R17.6 "Docs" row already owns this) |

**Unchanged and to stay unchanged:** `SURVIVAL_MIN`, `MINIMAP_AREA_MIN`, `MINIMAP_DELTA`, `MINIMAP_ALIGN_MAX_BLANK`, `CELL_FLOOR_FRACTION`, and the whole of `cell_overdraw` — the grid panel's rule reports **zero findings on all 18 matrix frames** and nothing in this revision touches it. `SCRIPTS_DEPENDENCY_MAP.md`'s Maintenance Contract does **not** trigger (no script added, moved, renamed or deleted, no caller changed); its prose for `render_layout_audit.py` remains under-complete, already flagged in the Phase 2 / Phase 0d verification as a nice-to-have.

### R22.8 The show-don't-encode statement: checked, and still required

§R17.4's closing clause — *"It is stated on the page, not hidden"* — is the honesty condition attached to this map's exemption from Q18's principle, and the user asked for it to be re-checked rather than assumed. **Checked three ways:**

1. **The claim is still true, and provably so.** The measurements in this revision are themselves the proof that colour *is* a code at this size: a mark large enough to be a *shape* cannot be fitted beside the dot (§R22.2's bound `r_p ≤ 0.1016 cell`, whose colour core is 4–7 px), and the two predator kinds differ by 15/255 — a distinction only an added colour accent can carry. The exemption is earned by measurement, not asserted.
2. **The requirement is still present** in the plan (§R17.4 final bullet), in the instrument (`minimap_caption`, `SHARED_CAPTION = "shared square"`, `render_layout_audit.py:1410-1419`) and in the painter (`painters.py:324-327`). It was **measured passing**: no `minimap_caption` finding on any of the 18 matrix frames, including every frame holding a shared square.
3. **It survives this revision only if the caption is rewritten with the encoding**, which is why that is a row in §R22.7 rather than a remark. A caption that still says *"a third is a rim pip"* after the rim pip is retired would leave the map encoding one thing and stating another — the failure mode §R19.2 (#56) named, where two parts of one system disagree and the reader builds from the stale one.

### R22.9 The M5 `panel_absent: Olfaction` finding belongs to CP2.7 — confirmed

The CP2.8 pass reported `panel_absent: Olfaction` on both audited frames of matrix cell **M5**, and the developer judged it a true positive belonging to CP2.7 rather than a co-occupancy defect. **That reading is confirmed, and the reasoning is independent of the report:** M5 is the only maintained cell with `olfactory_range: 1`, which routes it down the **sensor-band** layout (§D7.1), so its card list contains `band` and **no `olfactory` card** — where M4 at range 0 has one titled "Olfaction". The audit's presence rule (§D5.2 item 6) takes its ground truth from `get_observation_breakdown(params)`: olfaction **is** in M5's observation, so a panel is owed and none is drawn. The audit is right, and the cause is that **the sensor-band painter is deliberately unbuilt** (Phase 2 "What is deliberately NOT built yet"; §R21.4 item 3 records the band as never exercised by a real world).

It is therefore **not** a CP2.8 item, **not** a regression from the real-painter pass, and **not** a Known Bugs row — it is unbuilt scope, already owned by **CP2.7** ("Extended-range senses"). CP2.7's clause is extended below so that this is *gated* rather than merely known, and so nobody rediscovers it later as a defect: **CP2.7 does not close while any maintained cell reports `panel_absent` for a modality that is in its own breakdown.** M5 is named there explicitly as the case that must go green.

---

## Revision 23 2026-09-17 (finding D is settled: the World map gets its own survival floor, swept on map-sized wedges — one number was serving two instruments, and that was the defect)

**What this revision is about, in plain words.** The dashboard draws the world twice — a big grid panel at 50 pixels a square, and a small **World map** at about 18 pixels a square. An automatic check measures both, asking of every occupant of a shared square: *does it still show, once everything else has been painted on top of it?* It answers by comparing how much of its own colour survives in the finished picture against how much that occupant covers when drawn by itself, and complains if the surviving share falls below a floor.

That floor is **98 %**, and it was chosen by measurement — on the **big** panel, where an occupant is roughly 330 pixels and losing one pixel costs 0.3 %. Nobody ever re-measured it for the small map, where an occupant is **6 to 32 pixels** and losing one pixel costs 3–8 %. The previous pass repaired the map's drawing and got the check from "2 to 4 complaints on every one of 18 frames" down to "none on 13 of them" — and the nine complaints left over are all the same true fact: on the one square in the whole matrix where three animals really do stand together, one wedge of the dot loses **exactly one pixel**, because the thin white line dividing two wedges is painted by both of them and a pixel painted white twice ends up whiter than a pixel painted white once. The picture is correct. The number is wrong for the instrument it is being applied to.

**The decision: the map gets its own floor, `MINIMAP_SURVIVAL_MIN = 0.93`, and the big panel's 98 % is left exactly where it is.** One constant serving two instruments that measure objects an order of magnitude apart in size is the actual defect here, and this plan had already said so once — §R20.4 ruled that the map "gets its own ground truth and its own floor … never `SURVIVAL_MIN` reused". That ruling was applied to *one* of the map's two measurement paths and the other quietly inherited the arena's number. This revision finishes the job it started.

**The number is placed in a gap that was measured, not asserted** — and measuring it properly changed the answer. The previous pass reported a gap between a worst correct case of 0.941 and a best defect of 0.833, which looks roomy. But only **one** of the map's three deliberate sabotage tests actually exercises this floor at all; the other two trip a different check entirely, so "0.833" was a single point rather than a population. Sweeping a **graded** family of sabotages — the same defects made progressively shallower — brings the defect side up to **0.9167**, and the real gap is **(0.9167, 0.9412]**: two and a half points wide, not eleven. 0.93 sits **54 %** of the way up it, which is where Revision 21 put the last constant this plan moved.

**Three things are decided here.**

1. **Two constants, not one** (§R23.1). The map's census path gets `MINIMAP_SURVIVAL_MIN = 0.93`; `SURVIVAL_MIN` stays at 0.98 for the grid panel and `MINIMAP_AREA_MIN` stays at 0.55 for the map's geometric fallback.
2. **The map's sabotage family is re-registered** (§R23.2), because as pre-registered it does not test the thing the floor does.
3. **The one-pixel seam is NOT fixed in the painter** (§R23.3) — and that is a measured verdict, not a preference: the repair makes the *measurement* worse, in the direction that hides occlusion.

### R23.1 The floor is swept on map-sized wedges, and it splits into two constants

**Why this is the Revision 21 case and not the (A)/(B)/(C) case.** §R22.4's test asks what the picture actually contains. Here it contains three wedges drawn exactly as specified, in their own sectors, overlapping nothing — with a dividing line whose shared pixel is composited twice. Nothing is drawn over anything it should not be, and no occupant is missing. That is "a picture correct as drawn, misclassified by a number", which is the one row of §R22.4's table where the number is what moves.

**Why the number that moves is a NEW one rather than `SURVIVAL_MIN` itself.** Three reasons, in descending order of force:

1. **The plan already decided this principle and applied it incompletely.** §R20.4 says the minimap's floor "is never `SURVIVAL_MIN` reused: it measures a different thing and is swept on the minimap's own controls". That produced `MINIMAP_AREA_MIN` — but only for the **geometric fallback** path. When §R22.1 rebuilt the denominator as a census over a kind's own artists, the new **census path** took `SURVIVAL_MIN` (`render_layout_audit.py:1433`). So the map today measures with two floors, one of which was swept for it and one of which was swept for a different panel.
2. **The two instruments cannot share a number.** The arena's own gap table is `max(defect) < 0.5` against `min(correct) = 1.000` **exactly** — every correct arena composition measures 1.000, so its floor is pure tolerance for a single seam and belongs just under 1. Lowering it to 0.93 would let a grid-panel occlusion of up to 7 % of a 330 px² token — about 23 pixels, plainly visible — pass silently. Raising the map to 0.98 is arithmetically impossible: **a 0.98 floor is only reachable at ≥ 50 classified pixels per wedge**, and the largest wedge on a shared map square is 24.
3. **It is the reuse itself that failed, so the fix has to remove the reuse.** Moving `SURVIVAL_MIN` to 0.93 would leave one number serving both instruments and would simply relocate the same defect onto the arena.

**The two populations, both measured at the real square size** (harness: a read-only sweep driving the committed test helpers in `tests/env/test_dashboard_frames.py` against the real painter; every mutation applied to artists the painter itself drew).

*Correct — the floor must sit **below** all of these:*

| Control | map square | worst kind | num / den | ratio |
|---|---|---|---|---|
| `n = 1` agent | 18.40 px | agent | 60 / 60 | 1.0000 |
| `n = 1` hiding predator (two-paint mark) | 18.40 px | hiding_predator | 48 / 48 | 1.0000 |
| two predators — two movers, **one** kind (§R20.4's case) | 18.40 px | predator | 48 / 48 | 1.0000 |
| `n = 2` hiding predator + neutral | 18.40 px | hiding_predator | 16 / 16 | 1.0000 |
| `n = 2` predator + neutral | 18.40 px | both | 24 / 24 | 1.0000 |
| `n = 3` agent + predator + neutral | 18.40 px | **agent** | **16 / 17** | **0.9412** |
| `n = 3` agent + predator + hiding predator | 18.40 px | **agent** | **16 / 17** | **0.9412** |
| `n = 4` agent + predator + food + neutral | 18.40 px | each | 13 / 13 | 1.0000 |
| `n = 4` with a hiding predator | 18.40 px | hiding_predator | 6 / 6 | 1.0000 |
| **REAL** `M1` (8,6) three-way | 23.80 px | agent, predator | 31 / 32 | 0.9688 |
| **REAL** `M6` (8,6) three-way | 19.80 px | agent | 17 / 18 | 0.9444 |

**Minimum over the correct population: 0.9412.**

*Defect — the floor must sit **above** all of these, and each must fire **via the ratio floor**, not via another rule:*

| Mutation | measured | ratio | which rule fires |
|---|---|---|---|
| **M-F4** identity pip at the square's centre (the painter as it stood before Revision 22) | neutral 20 / 24 | 0.8333 | ratio floor |
| **M-F4** pip **80 %** of the way from its own wedge to the centre | neutral 22 / 24 | **0.9167** | ratio floor |
| **M-F3** agent disc at **0.25 ×** dot radius | 18 / 24 | 0.7500 | ratio floor |
| **M-F3** agent disc at **0.35 ×** dot radius | 14 / 24 | 0.5833 | ratio floor |
| M-F3 agent disc at 0.50 × dot radius | 6 / 24 | 0.2500 | ratio floor |
| M-F3 agent disc at 0.70 × dot radius (≈ as pre-registered) | 0 / 24 | 0.0000 | **distinctness**, not the floor |
| M-F5 amber painted over a neighbour's wedge | neutral 0 / 24 | — | **distinctness** + the artist guard, not the floor |
| *M-F4 pip 60 % / 40 % of the way* | *neutral 24 / 24* | *1.0000* | *silent — see below* |

**Maximum over the defects that exercise the floor: 0.9167.**

$$\text{gap} = (0.9167,\; 0.9412], \qquad \frac{0.9300 - 0.9167}{0.9412 - 0.9167} = 54.4\,\%$$

**`MINIMAP_SURVIVAL_MIN = 0.93`**, sitting 54 % of the way up the measured gap — the same placement discipline, and almost the same fraction (Revision 21 §R21.2 used 53.5 %), as the last constant this plan moved.

**The silent members are a result, not a failure.** Pushing the pip only 60 % or 40 % of the way back to the centre costs the neighbour **no classified pixel at all**, so the rule is silent and correctly so: the pip is still inside its own wedge as far as anything measurable is concerned. That is this instrument's **resolution limit, measured rather than assumed — one classified pixel**. It is why the graded family stops where it does, and it is the honest boundary of what this rule can promise.

**What the floor means in pixels, stated because a ratio hides it.** At 0.93 a wedge of 15–24 classified pixels may lose **exactly one** pixel and stay silent; a wedge of 14 or fewer may lose **none**. The smallest wedges on the map are the four-way's 13 px and a two-paint mark's 6 px, and both measure **1.000** today — no seam loss at all — so nothing is firing on that account. **Pre-registered branch, written before it can be needed:** if a *correct* four-way is ever measured losing one pixel (12 / 13 = 0.923, below the floor), the response is **not** to nudge the floor to 0.92 to absorb it. It is to record the new populations here and decide in plan text; and if they then overlap, the finding is that a ratio floor has reached its resolution limit at that wedge size, and the answer is a **stated detection limit** — the §R17.5 honest-limit pattern — never a number chosen to make today's frames pass.

**What this rule can and cannot catch on the map, added to the "does not see" list.** At 0.93 the census path catches an occlusion that removes **≥ 2** classified pixels from a 15–24 px wedge and **≥ 1** from a wedge of 14 or fewer. A one-pixel occlusion of a large wedge is **below** its resolution and is not caught by this rule; total occlusion of a kind is caught by the **distinctness** check regardless of size, which is the half of the rule that has no floor at all.

**What the developer must change, and where (the plan's instruction, not a code edit made here):**

| Site | Change |
|---|---|
| `scripts/eval/render_layout_audit.py:866-870` | **New constant beside `MINIMAP_AREA_MIN`:** `MINIMAP_SURVIVAL_MIN = 0.93`, with both measured populations named in the comment (min correct **0.9412**, max floor-firing defect **0.9167**, placed 54 % up the gap) and the one-pixel resolution limit stated |
| `scripts/eval/render_layout_audit.py:1433` | `den, path, floor = best, "isolated-wedge", SURVIVAL_MIN` → `MINIMAP_SURVIVAL_MIN`. The `own-artists` branch at `:1434-1436` inherits it (it reassigns `den` and `path`, never `floor`); the `geometric` branch at `:1438` keeps `MINIMAP_AREA_MIN`, untouched |
| `scripts/eval/render_layout_audit.py:826-831` | `SURVIVAL_MIN`'s own comment gains one sentence: it is the **grid panel's** floor, and the map has its own — so the next reader cannot reuse it onto a third instrument, which is the whole defect being fixed here |
| `scripts/eval/render_layout_audit.py:264-269` | the docstring's tolerance list gains `MINIMAP_SURVIVAL_MIN = 0.93`; the minimap paragraph at `:252-262` states that the census path has the map's own floor and what its one-pixel resolution limit is |
| `tests/env/test_dashboard_frames.py:404-414` | **Delete the `strict` xfail** `test_a_correct_three_way_is_silent`; it becomes a plain passing test. (A strict xfail turning red on the day the floor is settled is exactly what it was for — this is that day) |
| `tests/env/test_dashboard_frames.py:371-401` | the 16 / 17 measurement **stays**, rewritten from "an OPEN finding" to a pinned property: a correct three-way loses exactly one pixel to the shared split line, and `16/17 = 0.9412` clears `MINIMAP_SURVIVAL_MIN` with 0.0112 to spare |
| `tests/env/test_dashboard_frames.py` (new test) | the **minimap gap table**, mirroring `test_render_audit_controls.py:930-975`: min over the correct controls, max over the re-registered family, asserting `hi < MINIMAP_SURVIVAL_MIN <= lo` **and** that every family member fired through the ratio floor (`"covers" in f.detail`) rather than distinctness |
| `tests/env/test_render_audit_controls.py:1098-1150` | `_minimap_figure` gains the graded mutations (M-F4 by pip fraction, M-F3 by disc radius) so the mock-scale controls exercise the same family; re-run and report their ratios at the new floor |

*Fails if:* the constant is moved anywhere other than alongside this evidence; `SURVIVAL_MIN`, `MINIMAP_AREA_MIN` or `MINIMAP_DELTA` is changed; a control is made to pass by shrinking a wedge, widening the colour tolerance or folding a square's wedges into one artist; the minimap family is left with fewer than **four** members that fire **via the ratio floor** specifically; or the re-run matrix still reports a minimap finding and the floor is moved a second time to absorb it (report the number instead).

### R23.2 The map's sabotage family is re-registered, because two of its three members never tested this floor

**What was wrong, and it is the same shape as §R20.3's finding on the arena.** §R22.6 pre-registered three minimap mutations. Measured, **M-F3 (the agent's dot over the split wedge) and M-F5 (amber painted by something else) both fire through the DISTINCTNESS check** — the composite shows fewer distinct palette colours than the square holds kinds — and never reach the ratio floor at all. Only **M-F4** exercises it. A floor with one defect point behind it has a *measurement*, not a *population*, and the apparent 0.833-to-0.941 gap was an artefact of that.

This is exactly why §R20.3 re-registered the arena's M-F2 family at three insets with the words *"a member caught by another rule has survival 1.0 and never measured this floor"*. The minimap variant never inherited that discipline either — the same omission, on the same panel, as §R22.1 found for the union-of-own-parts rule.

**The re-registered family — four members, each of which must fire via the ratio floor:**

| Member | What it is | measured ratio |
|---|---|---|
| **M-F4a** | identity pip at the square's centre | 0.8333 |
| **M-F4b** | identity pip **80 %** of the way to the centre — a *shallow* crossing | **0.9167** |
| **M-F3a** | agent disc at **0.35 ×** dot radius over a shared dot | 0.5833 |
| **M-F3b** | agent disc at **0.25 ×** dot radius — the shallowest partial overpaint that still costs classified pixels | 0.7500 |

M-F3 at full dot radius and M-F5 are **kept unchanged** as distinctness controls — they test the other half of the rule and must keep firing. The negative partner of M-F4b is measured and recorded: at 60 % and 40 % the pip costs the neighbour nothing and the rule is silent.

*Fails if:* a family member is dropped because it is "the same defect as another"; any member fires through distinctness and is counted towards the floor's gap anyway; or the shallow members are removed when they become inconvenient.

### R23.3 The one-pixel seam is NOT fixed in the painter — and the verdict is measured, not preferred

The question is fair and had to be answered rather than waved away: a hairline that is whiter than specified is a real drawing artefact, not only a measurement one, so should the painter stop stroking each dividing line twice?

**Measured: the repair makes the measurement worse.** Drawing the wedges of a correct three-way **edgeless** — the only change that removes the double stroke — was applied to the painter's own artists and re-censused:

| Kind | num / den | ratio |
|---|---|---|
| agent | 21 / 21 | 1.0000 |
| predator | **23 / 22** | **1.0455** |
| neutral | **26 / 25** | **1.0400** |

The one-pixel loss does disappear. What replaces it is worse: **ratios above 1.000** — a kind credited in the finished picture with pixels its own artist never laid down. With no white line between them the two wedge colours meet directly and their blend lands close enough to one of the two to classify as that kind. That is credit **in the direction that conceals occlusion**: a defect removing a pixel can now be paid for by a blend adding one, and the rule would be quietly less able to see the very thing it exists to catch. It also removes the property the census is built on — §R20.4 and `_classify_census`'s own contract are that *a blend classifies as neither colour*, and the white split line is what makes that true between two wedges.

**Verdict: the seam stays.** It is one pixel, at 18 px per square, invisible to a viewer — §R22.7's "somebody looked" pass saw three clean wedges — and every repair measured so far trades a correct picture's honest one-pixel cost for a dishonest measurement.

**Recorded with the two repairs already rejected, so none of the three is re-proposed without new evidence:** round joins (implemented, measured, *changed nothing*, reverted); folding a square's wedges into one artist (would force 1.000 by construction while hiding the draw-order defect M-F3 exists to catch); and now edgeless wedges (removes the loss, introduces above-1.000 credit).

**One variant was NOT measured, and is named so nobody thinks it was ruled out:** edgeless wedges **plus** the dividing lines drawn once each as their own artist. It would keep the white separation the census relies on while stroking each boundary once. The reason it is not proposed is that the boundary pixels would then leave every wedge's own isolated ink while still being painted over the composite — which points toward a *systematic* loss rather than the present one-pixel one — but that is reasoning, not a measurement, and this plan does not accept reasoning where a number is available. *If anyone proposes it:* run the same arm, and it is adopted only if every correct control measures **≤ 1.000** and the re-registered family of §R23.2 still fires on every member.

### R23.4 What CP2.8 needs after this decision — this and nothing else on the map side

The arena side is **done and not re-opened**: `cell_overdraw` and every other grid-panel rule report **0 findings across all 18 matrix frames**, all five mutations fail on the real painter, all five archetypes are rendered and looked at, and the four-way census took §R22.3's first pre-registered branch on a measured non-zero count. §R22.7's diff touches only `build_minimap`, so that evidence stands.

Remaining, all of it on the map side and all of it downstream of this one constant:

1. **Implement §R23.1's seven rows** — the new constant, the one call site, the two docstrings, the xfail deletion, the re-pinned measurement and the two new tests.
2. **Re-register §R23.2's four-member family** and add the minimap gap table.
3. **Re-run the 18-frame matrix** and report the World map's finding count. **The prediction, stated in advance so it is a test rather than a description:** all nine remaining findings are of the form `(n−1)/n` with `n` between 17 and 32, so all lie between 0.941 and 0.969 and all clear 0.93 — **the map should report 0 findings on 18 of 18**. *If any frame still fires,* report the number and the wedge size; do not move the floor again.
4. **State the re-run's wall-clock per audited frame**, which CP2.8 asks for to size future samples (the last pass measured 49.1 s).

Nothing else. The caption, the encoding, the ceiling of four, the amber guard, the committed home under the `integration` marker and the "somebody looked" clause were all closed by §R22.7.

### R23.5 `12_renderer.md` belongs to CP6, and CP6 is made to name it

**The §R22.7 row that was not carried out, judged.** That row asks for "the minimap's encoding paragraph" in `docs/environment/12_renderer.md`. The developer checked rather than assumed and found there is **no such paragraph and no dashboard section** — the document describes only renderer **V1** and the dormant **V2**.

**Decision: fold it into CP6. Do not write a paragraph now.** The reason is not scheduling convenience, it is a concrete mis-read hazard: `12_renderer.md:209` already documents *a different minimap* — V1's, an `imshow` of the terrain with scatter dots and a cobalt viewport rectangle. A paragraph about dots dividing into four wedges, dropped into a document whose only renderers are V1 and V2, would most naturally be read as describing **that** map, and the reader would come away with a confident wrong picture of the renderer that is actually in production. An honest gap is better than a plausible mis-attribution, and the document's own rewrite — which introduces the dashboard package, the registry, the packer and the episode renderer — is what makes the paragraph readable at all.

**So that this cannot be rediscovered later as an omission, CP6 is amended from a one-line checkpoint into an itemised one** (see the Checkpoints section): the minimap's `n = 1…4` encoding, the retired rim pip, the four-kind ceiling, the on-page caption statement and the map's own survival floor with its one-pixel resolution limit are named as required content, with a *Fails if:* clause that bites if any is missing. The existing "V2 disambiguation sentence" already planned for CP6 is extended to disambiguate **"minimap"** as well as "V2", since the word now names two different pictures in two different renderers.

*Fails if:* CP6 is ticked while `12_renderer.md` describes the World map's encoding incorrectly, describes only V1's minimap without saying so, or omits any named item.

### R23.6 Two carried items, neither of which blocks CP2.8

1. **The audit has no completeness assertion on artist enumeration, and this revision adds a rule under that blindness.** The Known Bugs registry carries the fixed `Collection`-enumeration defect (filed and closed, `4a1a6dd9` / `588cf88d`) and, attached to it, a still-**open** follow-up: *after any change to artist enumeration, assert that the enumerated set accounts for the full canvas ink*. No such assertion exists. It does **not** block CP2.8 — this revision changes a constant and a call site, not enumeration — but it is the standing gap under which every census rule is built, and it is the thing to satisfy **before the census gains another rule**. Owner: `senior-developer`, as a separate plan item.
2. **Whether finding D earns a Known Bugs row is `bug-curator`'s call, and the one fact that bears on it is recorded here.** Consulted: no registry row matches the audit's constants, its colour census, the minimap encoding, a floor reused across two instruments, or an anti-aliased seam. `bug-curator`'s own disposition test is *"did a wrong number ever get acted on"* — and the one thing that touches it is that finding counts produced under the unswept floor (**9 findings across 18 frames**) were quoted in this plan. **`senior-developer`'s recommendation is no row:** those counts were published *as an open blocker*, are superseded in the same document by §R23.4's re-run, and no checkpoint was ticked and no calibration frozen under them — which is §R21.3's precedent and the same disposition Revision 21 gave the 0.40 → 0.48 move. `bug-curator` owns the final call.

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
| D2 | V1 | ~~"REAL: --" floats over the EXTERO NOCICEPTION pod title~~ → **corrected Revision 15**: the `REAL: --` readout is drawn **outside its own card**, in the strip above it that belongs to the EXTERO NOCICEPTION title, so it reads as part of the title line. The two strings are **1.55 px apart and share no pixel** (measured; 0 shared px raw and after the 1 px dilation), so this was never a text-on-text defect | ~~text-on-text~~ **escaped label** (content outside its box) |
| D3 | V1 | "MINIMAP" label overlaps the Run Context box border | text-on-border |
| D4 | V1 | ~15% dead whitespace top and bottom | space allocation |
| D5 | V1 (default) | Vitals rows: one row's "OBS: 0.95" collides with the next row's "REAL: 0.95". **Confirmed reproducing on the default world 2026-09-16** (Revision 15): three collisions of **17, 17 and 16 px** on cell M1 step 0, in the left vitals column (x 317–364; y 274, 351, 428) | text-on-text |
| D6 | dormant V2 | Collision title overprints its C U R D L labels | text-on-text |
| D7 | dormant V2 | Minimap tiny (~125 px) | space allocation |
| D8 | dormant V2 | Interoceptive-nociception and LOC panels missing | silent panel drop |
| D9 | dormant V2 | Vital cards mostly empty; visual feature labels tiny/clipped | space / clipping |
| D10 | V1 | Nutrition/Injury drawn from true state and captioned `OBS` in worlds whose observation lacks them (campfire) | false claim of sensory access |
| D11 | V1 | Campfire obstacle drawn as a grey square (no icon) | missing entity rendering |
| D12 | V1 | `Proprioception` emitted by the viz adapter, never drawn | silent panel drop |
| D13 | V1 | **Added Revision 16.** The thermal scale's max-value label (e.g. `+84`) is painted over by the colour strip's last segment, so the reader sees a clipped `+`. Structural and world-independent: the strip's 52nd segment ends at axes-fraction **0.77220** (each segment is drawn `strip_w/51 + 0.002` wide, the bleed closing hairline gaps between segments) while the label is anchored at **0.77000** with `ha='left'`, and the segment's `zorder=5` beats the label's `zorder=3`. Inside `if thermal_on:`, so **every thermal frame**. Measured on M4 step 0 (verifier, independently): the label's box overlaps the strip by **1.22 px** of the host axes' 554.26 px width, costing **2 px of the label's 70 px of ink**, at which the final frame is `[103 0 31]` — the segment's colour exactly, 157 and 243 away from what the glyph alone would paint (`renderer.py:769-772` strip, `:777` label) | fill over text (label ink covered) |

**On the `text_over_fill` class (Revision 16).** It is **not** uniformly benign, and §D5.2's audit no longer reports it as though it were. It splits by composition order into `text_over_fill` (the label is composed last, so the frame shows the glyph — legible by design) and `fill_over_text` (the partner is composed after the label and covers its raw ink — a defect whatever the intent). On the V1 campfire frame that is **5 benign + 1 covered** (the covered one is D13), replacing the original pass's blanket "6, all by design"; on the dormant V2 frame, 5 benign + 0.

**Root causes.**
- **D1–D7, D9.** No step gives each panel a box sized from its needs and keeps it inside. Constrained layout ignores in-card `ax.text`.
  - **D2 specifically** (Revision 15) is the pure form of this: the readout's anchor is computed from the *bar's* geometry (`y_frame_bottom + 0.02·squeeze + 0.07·squeeze + 0.02·squeeze`) and the card's top edge from the *pod's* (`y_frame_bottom + 0.11·squeeze`). Those two expressions are algebraically equal at every squeeze factor, so the label lands exactly **on** the card edge and escapes it, by construction, in every world. Two independent coordinate systems for the same box, with nothing checking that one stays inside the other — which is precisely what §D1.3's paint-inside-the-box step removes.
- **D8, D12.** A hard-coded panel list that skips unknown names.
- **D10.** Presence and caption come from the renderer's own assumptions ("always drawn"), not from what the agent observes.
- **D11.** No specified fallback for iconless entities.
- **D13** (Revision 16). Two constants in the same block that were never checked against each other: a decorative bleed added to every strip segment to hide hairline gaps, and a label anchor placed at the strip's *nominal* end. Neither is wrong on its own; nothing in the renderer asks whether the drawn strip still ends where the label assumes it does. The same family as D1–D7 — a coordinate computed twice, from two different premises — and removed by §D1.3's paint-inside-the-box step, which gives the strip and its end labels one box and one owner.

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
| minimap | world | minimap | – | always | ≥ 2 px/world cell, ≥ 180 px side, + one caption line for the shared-square note (Revision 17 §R17.4) |
| location | world | text_row | `Location` | name in breakdown | one text line |
| arena | arena | arena | – | always | square, `ARENA_CELL_PX` = `ARENA_CELL_MIN_PX` = **50 px per world cell** (**Revision 18**; was 48 at Revision 17, 32 before that), and the view is the **whole world** where it fits at 50 px; + scale strip when thermal on. Square composition (bed / token / slot) per §R17.3, at the 50 px values in §R18.3 |
| action_badge | arena | action_badge | – | action recorded | pill text in arena title strip |
| olfactory | extero, or sensor band (§D7.1) | `grid_kind(olfactory_grid_range, 5)`: spectrum (r=0) / `channel_maps` (r≥1, decided) | `Olfaction` | name in breakdown | per kind (§D7.2) |
| extero_nociception | extero | intensity | `Extero Nociception` | name in breakdown | text row + bar |
| thermoception | extero | thermal_diamond | `Thermoception` | name in breakdown | `2r²+2r+1` numeric cells |
| collision | extero | cross_bars (r=1) / dir_grid | `Collision` | name in breakdown | 8 pt legend above bars |
| visual | extero, or sensor band (§D7.1) | `grid_kind(visual_sensor_range, visual_vector_size)`: single-cell bars (r=0) / `channel_maps` (r≥1, decided) | `Visual` | name in breakdown | per kind (§D7.2); 8 pt legend |
| proprioception | extero | `action_chips` (decided Q5, 2026-09-14): six chips, previous action highlighted in the agent colour | `Proprioception` | name in breakdown | six measured chips at the 14 px floor |

**The three heights Figure 3 never draws (pinned 2026-09-16, after Phase 1 was verified).** Figure 3 always has a sensor band, so it never draws a spectrum smell pod, a range-0 vision pod or the location row, and the rows above give only qualitative drivers for them. Phase 1 had to choose numbers, and they are **not free** — the binding case is a real maintained world, not a hypothetical. Recorded here so nobody re-derives them and so the budget is visible:

| Panel | Height | Column it is charged to |
|---|---|---|
| `olfactory` at range 0 (spectrum) | **118 px** = title 46 + label row + 5 bars + pad 16 | right |
| `visual` at range 0 (bars) | **134 px** = title 46 + legend + channel bars + pad 16 | right |
| `location` | **46 px** = one text line + padding | **left** (§D1.1's `world` group), so it does **not** consume the right-column budget below |

**The budget, measured.** Two maintained worlds — the campfire thermal world and the sensory-noise world — have thermal on and **both** sense ranges at 0, so neither sense goes to a band and the right column must hold five pods at once. With no band the right column is 816 px, of which Figure 3's own pinned pods already claim `104 + 150 + 230 + 4 × 16 = 548`, leaving **268 px** for the smell and vision pods together. `118 + 134 = 252`, so both worlds pack with **16 px spare** — verified by packing all nine maintained configs, not by arithmetic alone; every other maintained world lacks the thermoception card and has 262 px spare.

**Status: provisional, and the failure mode is a hard one.** These are the numbers most likely to move when Phase 2 measures real text, and the `compact` fallback deliberately does **not** shrink right-column pods (a thermoception diamond cannot be compacted and stay legible). So if Phase 2's measurement pushes the pair past 268 px, `pack()` **raises on a real maintained config** rather than degrading. Two requirements follow, both on Phase 2:
- `tests/env/test_dashboard_layout.py` gains a test that pins the campfire world's right-column need against its 816 px, so a Phase-2 change that eats the margin fails **naming the budget** instead of surfacing as an unexplained `LayoutOverflowError`;
- if the measured pods exceed 268 px, the developer reports both numbers and the proposed remedy and **stops** — re-cutting the split, or letting `compact` reduce pod chrome, is a plan change recorded here, never a constant quietly raised in the source.

**One naming point for Phase 2.** The registry gives the range-0 vision pod the kind string `cross_bars`, which is also collision's kind, while this section's table calls it "single-cell bars". They are different pictures with different content (8 channels versus 5 directions) and they carry different heights (134 versus 150). Phase 2 either gives the range-0 vision pod its own kind string or records here why one painter serves both.

**Completeness rule.** At episode setup, every breakdown name must be owned by exactly one present entry, or be on an explicit "recorded, not displayed" list (only if Q5 chooses that). Otherwise setup raises `ValueError` naming the orphan. A future modality that reuses a kind is a registry entry only. A new kind adds a painter. Neither touches layout.

#### D1.2 Layout: a column packer, computed once per episode

1. **Canvas.** Fixed at **1440 × 896 px**, multiples of 16 so imageio does not resample (Q3). Header = measured line + padding.
2. **Columns — Figure 3's constants (rewritten in Revision 19; the earlier "left 300, right 330" is withdrawn).** Outer gutter 24 px, gap 16 px, card padding 16 px, header 64 px. **Left column fixed at `LEFT_W = 320` px.** The centre column is the arena card's own width, and the right column is what remains: `right_w = 1440 − 24 − (24 + 320 + 16 + card_w + 16)` = `1040 − card_w`, which must be **≥ `MIN_RIGHT_W` = 440 px** or the packer raises. All of these are module constants read from Figure 3 (`renderer_layout_redesign/fig03_proposed_dashboard.py`, `dashboard_style.py`), not re-chosen.
3. **The arena is a FIXED box, not a grow panel (Revision 19, #56).** The arena card is `W × ARENA_CELL_PX + 64` px wide and `48 + W × ARENA_CELL_PX + 16` px tall — square, as `pack()` builds it — where `W` is the number of world squares drawn (the whole world for every maintained config, §R18.2) and `ARENA_CELL_PX = 50`. It **never** absorbs leftover height and it never grows to fill a column: the arena box is exactly `W × 50` px of drawing, and a Phase 1 test asserts that for every context. Leftover height goes only to the minimap (left column, capped at `46 + LEFT_W − 2 × PAD + PAD` = 350 px) and to the thermoception card on the right. Per column, sum the present panels' min heights plus gaps as before.
   - **The sensor band and the right column's height.** When a band is present it starts at `64 + card_h + 16` and runs to `880`, and must be **≥ 200 px**; the right column is then measured against the arena's **bottom edge** (`64 → 64 + card_h`), so its available height moves with the world size. With no band the right column runs `64 → 880` = 816 px. **One check covers every way that height can be chosen** (Revision 19 §R19.2): the right column must fit whatever arena height is selected — from the world's own size, from the whole-world rule, or from the fallback's shrink step (§R18.2 item 9). Worked numbers for 10×10 and for the two maintained 5×5 worlds are in §R19.2.
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
  2. Figure plus every artist: card outlines, titles, legends, bar tracks, arena grid lines, and a fixed pool of **vector** artists per arena square — ground, bed, and one slot per token position (**corrected Revision 20, #70**; the earlier "a fixed pool of `AxesImage` icon slots per view cell per layer" was stale against the vector decision recorded two bullets below, Revision 19 #58). The pool's per-square size is one of the counts CP0.4 reports.
  3. Thermal underlay `imshow` with fixed `set_clim`, and gauge marks.
- **`frame(t)`.** `extract`, update artists (`set_width`, `fit_text` updates, `set_data`, `set_visible`, `set_offsets`), then `canvas.draw()`, then copy of `buffer_rgba()[..., :3]`.
- **`close()`.** `plt.close(fig)`.
- **`layout_signature()`.** Hash of the panel keys, kinds, boxes and REAL-slot flags, used by the concat check in §D4.2.
- **Icon set (Revision 8, supersedes the icon-file lookup below).**
  - **Source.** The new renderer draws every entity from its own flat icon set per the design spec §Icon style guide: creatures and food on white tokens, flat terrain. It does **not** load V1 icons or `icon_config` images.
  - **Medium (decided Revision 19, #58).** Everything drawn **inside an arena square** — beds, tokens, companion forms, the agent marker — is a **vector primitive built in `src/environment/dashboard/cells.py`**, never a raster image. The reason is testability: `test_dashboard_cells.py` recomputes `h` and the identifying-mark fractions as numbers and compares them against the 49 / 50 px floors, and a PNG cannot supply `MIN_MARK × h`. `assets/dashboard_icons/` holds only fixed-size artwork that is never recomputed — legend chips and minimap glyphs — and the Implementation Report records whether even those are drawn from the same vector forms, in which case the folder is dropped.
  - **Agent.** A composable marker replaces V1's `agent_*` combination images. **Revision 17:** it is *not* drawn over whatever occupies the cell — a shared cell lays its occupants out in slots (§R17.3), the agent's halo is dropped whenever the cell is shared, and the agent's identity is carried by the cell's iris outline rather than by the token's size.
  - **Terrain (Revision 17).** Terrain is drawn as a **bed** — full-bleed ground cover inset by `BED_MARGIN = 0.14 × cell` — not as a centred glyph. Each terrain entity therefore needs a bed form in addition to its map/legend glyph, and each token entity a reduced companion form (§R17.3 items 2, 6).
  - **Campfire.** `assets/campfire.png` joins the set **as a legend/minimap glyph only** (Revision 19, #58). In an arena square the campfire is a drawn **bed**, so CP2.6 measures bed ink classified by area, not an `AxesImage`. Q12's decision to create the asset is unchanged; what it is used for is narrowed.
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
| M3 interoceptive nociception + noise | Same with perceptual noise on | `configs/environment/experiment/basic/06-sensory_noise_10x10.yaml` (**renamed from `05-…` and re-parented onto the campfire world by Revision 14; loads cleanly — re-verified 2026-09-16**), with an override turning interoceptive nociception on if it is not already. *Values-only reference: `configs/environment/experiment/archive/hypervigilance/01-interoNocicept_noise.yaml`* |
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

**Frames checked per cell:** step 0; last step; max injury; max extero nociception; min and max `body_temp` (M4); max REAL−OBS gap (M3/M9); and for M4 a step where the campfire is in view. **Added Revision 17:** one step per co-occupancy archetype — agent on terrain, two movers in one square, a three-way, a four-way, and a resource on terrain — with the generator **reporting which archetypes each cell's episodes actually contain**. An archetype no episode reaches is rendered from a synthetic snapshot labelled "derived input, co-occupancy only", the same precedent as the stress variant. A **stress variant** copies those snapshots with extreme values (body temp −14.99, noisy OBS outside [0,1], all visual channels 1.0), labelled "derived input, text-fit stress only". It must either render clean or raise `TextFitError`/`LayoutOverflowError`, never produce a frame with an ellipsised number.

#### D5.2 Overlap/clip audit with a pixel ground truth

`scripts/eval/render_layout_audit.py` (also imported by tests; tests carry the registered `integration` marker). **It imports neither the layout module nor the registry.** A test checks its imports. For each checked frame:

1. **Element classification by artist type and geometry, not by painter tags** (review finding 3).
   - **Foreground:** every `Text`; every `Line2D` shorter than 90% of its axes' width and height (ticks, marks); every `AxesImage` smaller than 90% of its axes (icons); every `Patch` with area below 90% of its axes' area (bar fills, cells, glyphs, pills); every **unfilled** outline patch (card borders), whatever its size.
   - **Background (demoted):** only filled patches ≥ 90% of their axes (card fills), `AxesImage`s ≥ 90% of their axes (the thermal underlay), and `Line2D`s spanning ≥ 90% of the arena extent (grid lines).
   - The audit **asserts this geometry itself**, measured via `get_window_extent`. Painter `gid`s are used only to name elements in the report.
   - V1 frames use the same classifier, so V1 and V2 are judged by one rule.
2. **Ink masks — by ISOLATION** (*changed in Revision 15, 2026-09-16; this item previously specified hide-and-diff*). One render of the bare background, plus one render per element with **only that element visible**. The element's ink = pixels that differ from the bare background. This is N+1 renders per frame (~22 s for a V1 frame, measured).

   **Why not hide-and-diff** (render everything, then re-render with the element hidden, and call the difference its ink). Hide-and-diff measures *what an element contributes to the final picture*, not *what it draws* — so an element that is overdrawn by something opaque loses exactly the pixels that are in dispute, which are the only pixels a collision rule cares about. Isolation has no such dependence on paint order.

   **What that is worth, measured rather than argued** (Phase 0c verification). Constructing the worst case — an opaque haloed label drawn on top of a card border, the same halo pattern `renderer.py` uses for the body-temperature readout — the collision measures **298 px under isolation and 8 px under hide-and-diff**, a 37× collapse, because 12% of the border's ink disappears under the halo. On the real frames the gap is smaller: across the **10 collisions** the audit reports on V1 M4, hide-and-diff would have detected **all 10**, at 70–100% of the isolation figure. So the honest statement is that hide-and-diff is *systematically under-sensitive by a large and unbounded factor*, not that it is blind: no control would have been missed by it today. Isolation is adopted because the margin of safety matters more than the 0 controls it currently buys, and because a rule whose sensitivity depends on z-order cannot be reasoned about as the renderer changes.
3. **Collision rule.** A text element's ink, dilated 1 px, intersecting any other foreground ink **fails**, including card-border outlines (text-on-border forbidden). Text over background ink is allowed. Every pair is reported with both strings and a crop.
4. **Clip rule.** A text element re-rendered with clipping off whose ink differs has been cut off, and fails.
5. **Legibility floor (Revision 8).** Every playback text element's cap height corresponds to a font size ≥ 14 px, and every caption ≥ 12 px. Measured from a reference "0" rendered in the vendored font at those sizes, not from the painter's requested size. (V1 control frames are judged at the old 8 pt floor.)
6. **Presence (ground truth = breakdown).** For every name in `get_observation_breakdown(params)` not on the explicit not-displayed list (Q5), the report must contain foreground ink attributable to a panel for that name. The name → panel association is read from rendered text (the panel title string, matched against a fixed title table in the audit module), not from the registry.
7. **Observed-caption rule (ground truth = breakdown).** Any rendered text beginning `OBS` or `REAL`, or containing "obs only", must belong to a panel whose title maps to a breakdown name that is present. Any `hidden_state` row's text must contain "not observed".
8. **Vocabulary rule (V2 frames).** No rendered text matches `\bpain\b` (case-insensitive), and no legend contains `DNG`. V1 frames are exempt, because V1 is frozen and still shows `DNG`.
9. **Canvas.** No foreground ink in the outer 4 px margin; dimensions equal the declared canvas.
10. **No numbers in the grid view (decided 2026-09-14; narrowed in Revision 7).** No `Text` element whose string contains a digit or a sign character has ink inside the arena grid's extent. The title strip, legend chips and scale strip sit outside it. The iconless-entity code is drawn as a vector path (`TextPath` → `PathPatch`), not a `Text` artist, so this rule and the glyph cannot collide. Checked on every thermal cell.
11. **Cell co-occupancy (`cell_overdraw`, added Revision 17, **rewritten in Revision 19 §R19.1**, built in Phase 0d).** Ground truth is the snapshot's set of **distinct non-terrain kinds** per arena square (never instance counts — §R17.5 item 1). Excluded from token ink, by measurement and never by painter tag: elements whose isolated ink covers ≥ **48 %** of a square's area (bed/ground; **0.40 until Revision 21 §R21.2 moved it with its evidence** — and per Revision 20 §R20.8 **a bed must be one artist**, so that test measures it whole rather than letting a multi-part bed's small parts leak into the token count), and elements whose ink sits on the perimeter of **their own bounding box** (`_ink_is_outline` — the agent's square outline, seams; wording corrected in Revision 20 §R20.7 item 1, which also adds the failing-direction guard that an outline-classified element whose bbox spans **under 80 %** of the square is reported as `outline_like_token` and **fails** rather than quietly leaving the token union). Then **three** conditions, not one: the connected components of the square's **token ink** (isolated) number exactly `|kinds|`, pairwise touching in 0 px, no dilation; the components of its **visible token ink** — the pixels at which no element drawn *after* the token has ink, using the existing composition order `_is_painted_over` / `_draw_index` — **also** number exactly `|kinds|`; and each token-ink component's surviving fraction is ≥ `SURVIVAL_MIN` (0.98; a correct composition measures 1.000). Preconditions the rule asserts and **fails** on rather than skipping — **re-scoped in Revision 20 §R20.1 and §R20.6**, because as first written they fail on a correct painter. Let `L(p)` be the last-drawn element with ink at a token pixel `p`, computed over **every element in the figure**: (a′) if `L(p)` is not a token element of that square it must be fully opaque; (b′) `L(p)` must belong to the named arena Axes; (c′) the ground, every bed base, the square-outline and the keyline colours must differ from the figure facecolor by more than `INK_DELTA`, or the rule cannot see them at all. The composition comparator is extended to rank across Axes as `(axes rank, zorder, child index)` and that derivation is pinned by a rendered two-Axes control. The minimap variant is measured on the **composite** (a colour census against the palette table), not by isolation, together with the presence of the shared-square caption; its ground truth is the distinct palette colours of the **kinds** present and its denominator is the same census on the isolated wedge (§R20.4), never the mover count and never a geometric wedge. **Revision 22 §R22.1:** a kind's ground truth is the **set** of palette colours its own mark is drawn in (`hiding_predator` = body + amber accent), the numerator matches any colour in that set, distinctness compares sets, and the denominator is the same census over the union of that kind's **own artists rendered together** — the per-element maximum the rule shipped with read a mark's second paint as missing area and fired on a correct frame. The exemption is held honest by mutation **M-F5** (no other minimap artist may paint the amber) and **M-F4** (the identity pip over a *foreign* wedge must still fire). Every painter-set property this rule reads — alpha, face colour, outline shape — is read **only where reading it can make the rule fail**; nothing may be read to exempt ink from the count (finding #3's discipline). The square grid is derived from the named arena axes' extent and the recording's world/window size; the audit still imports neither the layout module nor the registry. Connected-component labelling may use `scipy.ndimage.label` (scipy is already a project dependency and is used under `src/` and `scripts/`) or a stdlib flood fill — no new dependency either way.

**Positive controls** (known defects; if any is missed, the audit is broken, so stop):
- V1 M4 frame: **D1**, **D2**, **D3** (text on the Run Context border), and **D10** (`OBS` under Nutrition/Injury while the breakdown lacks them).
- Dormant V2 M4 frame: **D6**, and presence reporting **Interoceptive Nociception** absent, plus **Location**/**Proprioception** if they are in M4's breakdown (**D8**/**D12**).

**Mutation controls:**
- **M-A:** shift one V2 legend 6 px into its title; the audit must fail.
- **M-B:** set a vitals row's min height below its measured text and bypass fit-or-fail; the audit must fail.
- **M-C:** retag a bar fill's `gid`/role as background in the painter and draw a label over it; the audit must still fail, since classification ignores tags.
- **M-D:** swap a `hidden_state` caption to `OBS`; the observed-caption rule must fail.
- **M-E (Revision 17):** force every occupant of a shared square to the square's centre (the sketch painter's concentric behaviour); `cell_overdraw` must fail. Its negative partners are the shared list below.
- **M-F (Revision 19, extended to four variants by Revision 20 — the mutation set that pins §R19.1):** **M-F1** draws the terrain bed *after* the tokens (full occlusion — the isolated-ink rule alone passes it); **M-F2** draws the bed after the tokens inset a further `0.10 × cell`, so a rim of each token survives and only the survival floor can fire; **M-F3** draws the minimap's agent dot above the split wedge; **M-F1g** (Revision 20 §R20.6) draws the **ground**, not the bed, after the tokens, run with the figure facecolor set to `CANVAS` — only precondition (c′) catches it, and without (c′) it passes silently. All four must fail the audit, and with M-E that is the **five** mutations CP0.3b gates on.
- **Negative partners (Revision 20 §R20.2, §R20.8) — each must produce zero findings and is recorded with its measured survival ratio:** a single-occupant square; an empty square; a bed plus one token, using **the campfire bed specifically** (the bed with the most parts, and the only one whose largest part falls under the floor); a correct two-mover square **containing the agent**, so its square outline is present; a correct four-way square **containing the agent**, the tightest clearance in the design; an E-cell footprint edge crossing an occupied square; and — **added by Revision 21 §R21.2, because it is the control the shipped constant failed** — a **lone agent on bare ground**, which keeps its halo. A correct composition measures **1.000**; per §R20.3 any control reading below 1.000 is **investigated and its cause recorded before it is accepted**, never absorbed by loosening the constant. These ratios form one side of §R20.3's pre-registered gap table, whose other side is the **M-F2 family** at insets `0.005 / 0.010 / 0.020 × cell` (re-registered in Revision 21 §R21.2).

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
- **Phase 0 decision gate (CP0.4):** A-spike median on M4 ≤ **0.5 × V1 median on M4** (Q9), with the spike drawing the **whole 10×10 world** (Revision 19 §R19.3). The benchmark reports the frame time across the **three arms** of Revision 20 §R20.5 — full, arena *update* disabled, arena *Axes* hidden — plus total / arena artist counts, because with 100 squares the ratio alone no longer separates the architecture from the amount of drawing, and because disabling only the update leaves the arena's ~230 visible artists' **draw** cost inside the "non-arena" number. If missed, the single pre-registered path is CP0.4's: report the split to the user with **Q22**'s options and stop. The developer does not pivot to B, change the gate or change the square size.
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
  - **(b) sensor-band:** grid-view card on top of the centre+right area, a full-width band below it spanning the centre and right columns (`1440 − 24 − (24 + 320 + 16)` = **1056 px** wide, on Figure 3's constants; the earlier "≈ 1440 − 300 − 16 ≈ 1124" used the withdrawn 300 px left column — corrected Revision 19, §R19.2), and the non-grid right pods (extero nociception, thermoception, collision, location) in a narrowed right strip beside the grid view.
- ~~Layout (a) is used iff every grid-kind sense meets its `min_size` there; otherwise (b).~~ **Corrected 2026-09-16, after Phase 1 verification — the two-step evaluation is withdrawn.** The band is **not** a fallback that (a) gets first refusal on: **a grid-kind sense (smell or vision at range ≥ 1) goes in the band, and everything else goes in the side column**, full stop. That is Figure 3's own rule (`fig03_proposed_dashboard.py:172`, `band = bool(self.olf_range or self.vis_range)`), and Figure 3 is the canonical layout reference. The canvas stays 1440 × 896.
  - **Why the withdrawn wording was wrong, measured rather than argued.** Under the two-step reading, the synthetic 5×5 world with thermal *and* a range-1 sense would try (a) first and **find a side column that fits** — a 726 × 816 px right column against the 624 px those pods need — so it would pack happily and **would not raise**. That directly contradicts §R19.2, which pins that case as the guard that must raise `LayoutOverflowError` naming the right column. Verified by forcing both layouts on that context: band → raises ("right column needs 516px, has 314px"), forced side column → packs. The two-step rule would also put a range-1 smell map in the narrow side column of every 10×10 world, which is the opposite of what §D7 exists to do.
- If the band layout does not fit, `LayoutOverflowError` names the sense, its range and channel count, and the encoding. No squeezing, and no silent fallback to a side column that happens to fit.
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

- **View (rewritten by Revision 18).** The grid view shows the **whole world** — `W = params.width` — wherever the world fits at the 50 px square, which every maintained config does (10×10). There is no local window, no centring on the agent and no panning; the panel's frame is the world's edge (§R18.2). The windowed rule below survives **only** as the fallback for worlds too large to draw whole.
- **Window (fallback only).** For a world above 10 squares across, the renderer falls back to `W = max(params.local_view_size, 2·max_range + 1)` cells, where `max_range` is the largest diamond radius among the present senses. This is a rendering choice only; environment params are not changed. No maintained config reaches it today.
- **Cell-size floor.** If `W` would push arena cells below `ARENA_CELL_MIN_PX` (**50 px since Revision 18**, the single floor in §D7.7), `W` is capped at the largest value keeping 50 px. At 50 px the centre card holds at most 10 squares across, which is exactly the maintained worlds' 10×10 (§R18.1). The footprint outline is then clipped at the window edge, and the card caption says `footprint exceeds view (r=<r>)` — reachable only on the fallback path, since a whole-world view clips a sense's diamond at the world's own edge, which is truthful rather than a rendering limit. The audit checks that caption's presence whenever clipping occurs.
- **Footprint outline.** Each directional sense draws its diamond footprint on the grid view as a thin outline in its sense colour (smell, vision, thermoception, and collision when r > 1). The outlines are foreground artists, and a legend chip in the arena title strip names each outline. **Revision 20 (#64): they are pinned BELOW token zorder.** A ~1.5 px diamond edge crossing a ~20 px token removes roughly 7 % of it, which fails the survival floor on a correct picture; behind the animal is also the correct picture, since the animal is the subject and the footprint is annotation. They stay in the occluder set, so raising them later fires the floor. A frame test checks outline ink along the expected diamond boundary cells.

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
   - `ARENA_CELL_MIN_PX = 50` (**Revision 18**, user decision; was 48 at Revision 17 and 32 before that) is the only arena floor, and `ARENA_CELL_PX = 50` is the drawing size. The floor exists because no literal shared-square variant is legible below it — 50 px is the smallest square meeting every measured floor (§R18.3).
   - The packer tries, in order, and records which step succeeded in `layout_signature()`:
     0. **the whole world at 50 px** (Revision 18) — the only step any maintained config reaches;
     1. `W = max(local_view_size, 2·max_range + 1)`;
     2. layout (a) side column;
     3. layout (b) sensor band;
     4. shrink `W` by 2 per step toward `local_view_size` (never below), with the `footprint exceeds view (r=…)` caption;
     5. `compact` min sizes;
     6. raise `LayoutOverflowError`.
   - ~~The minimap's viewport rectangle outlines the `W × W` window actually drawn.~~ **Removed by Revision 18:** with the whole world drawn, the rectangle would outline the entire minimap. It is drawn only when the fallback actually windows the view (§R18.2 item 4). **Revision 18 §R18.2 item 9 also records a defect in step 4 below**: shrinking `W` shortens the centre card, and at 9 squares the right column no longer fits in the thermal world — the fallback must check it.
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
| `tmp/<timestamp>_renderer_spike.md` | Spike numbers (spike code stays uncommitted scratch). **Revision 20 (#71):** the spike's cell code is **disposable** — under `tmp/`, imported by nothing in `src/`, and it does **not** become `cells.py`. The report names the forms drawn and the per-square / total artist counts, and carries all **three** timing arms of §R20.5. |

**Phase 0d: the audit learns to see squares (added Revision 17)**

| File | Change |
|---|---|
| `scripts/eval/render_layout_audit.py` | Adds rule `cell_overdraw` (§D5.2 item 11, specified in **§R19.1**): snapshot-derived kinds per square; bed/ground excluded by measured area and square outlines by `_ink_is_outline`; component count on the **isolated** token ink **and** on the **visible** token ink (surviving composition, via the existing `_is_painted_over` / `_draw_index`); a per-component **survival floor** `SURVIVAL_MIN = 0.98`, **swept on both sides** at CP0.3b (Revision 20 §R20.3); 0 px tolerance on both masks; **three** self-asserted preconditions, all scoped to `L(p)`, the last-drawn element with ink at a token pixel, and all **failing** rather than skipping (Revision 20 §R20.1, §R20.6) — (a′) a non-token `L(p)` must be fully opaque, (b′) `L(p)` must belong to the named arena Axes, (c′) ground / bed base / outline / keyline colours must differ from the figure facecolor by more than `INK_DELTA`; the composition comparator extended to rank across Axes as `(axes rank, zorder, child index)`, pinned by a rendered two-Axes control; minimap variant measured on the **composite** colour census, with the ground truth being the distinct palette colours of the **kinds** present and the denominator the same census on the isolated wedge (Revision 20 §R20.4); shared-square caption check. **The occluder set from which `L(p)` is computed is every element in the figure** — the only permitted exclusion from the *work* is an element whose 2 px-padded bbox cannot reach the square, which is proved equivalent at CP0.3b. Performance: build the figure-wide rank **once per frame** as `dict[id(artist) → rank]` rather than scanning an Axes child list per pair. Square grid derived from the named arena axes and the recording's world/window size; **no** import of the layout module or the registry (the existing import-isolation test still applies). Component labelling via `scipy.ndimage.label` (already a dependency) or a stdlib flood fill — no new dependency. **Revision 22 §R22.1 / §R22.7 (Q21 "keep" branch only):** `MINIMAP_PALETTE` maps each kind to the **set** of palette colours its own mark is drawn in (`hiding_predator` = `{HIDE_BODY, HIDE_EYE}`); the numerator matches any colour in the set, distinctness compares sets, and the denominator becomes the same census over the union of that kind's **own artists rendered together**, replacing the per-element `max` at `:1375`. No floor or delta constant changes. |
| `tests/env/test_render_audit_controls.py` | **Every control here is a figure the test builds** — `cell_overdraw` needs `--arena-axes` and V1's arena axes is unlabelled, so it cannot run on a frozen frame until Phase 2 supplies a real painter (#62). Positive controls, four mutations (§R19.1): **M-E** concentric drawing; **M-F1** bed drawn above the tokens; **M-F2** the same inset `0.10 × cell`, so a rim survives and only the survival floor can fire; **M-F3** the minimap's agent dot above the split wedge. **M-F1g** the *ground* drawn above the tokens with the figure facecolor set to `CANVAS` (Revision 20 §R20.6 — only precondition (c′) catches it). Negative controls (Revision 20 §R20.2, §R20.8): single-occupant, empty, **campfire**-bed-plus-one-token, a correct two-mover **with the agent** and a correct four-way **with the agent**, and a footprint edge crossing an occupied square — all zero findings, each recorded with its survival ratio, and the correct shared squares **measure 1.000** (a control below 1.000 is investigated and its cause recorded before acceptance, §R20.3 — never absorbed by loosening the constant). Plus the §R20.3 gap table (minimum over the negative controls against the maximum over an M-F2 family at `0.02 / 0.05 / 0.10 × cell`), the cross-Axes comparator control rendered in two Axes, and the padded-bbox equivalence run. Plus the §R19.4 item 2 adjacent-slot control at **50 px** with the real forms, whose reading is pinned (non-zero → inset the keyline, never loosen the tolerance). The exact per-rule counts on the frozen M1 and M4 frames are re-pinned and must be **unchanged**, so an `ink()` that answers "everything" still fails and a new rule that reclassifies existing elements is caught. |
| `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` | **No change** — no script is added, moved, renamed or deleted; an existing row's file gains a rule. |

**Phase 1: registry and packer**

| File | Change |
|---|---|
| **`src/environment/dashboard/`** (new package; name is Q2) | `__init__.py` exports `EpisodeRenderer`, `render_dashboard_frame`. `src/environment/renderer_v2.py` is **not touched** (frozen; its deletion is a retirement-gate step). |
| `tests/env/test_dashboard_v1_imports.py` (new) | Pins the imported V1 signatures listed in §D1.3. Revision 7 cache-isolation check: in one process, render a new-renderer M4 frame, then V1 M4 raw frames. The V1 hashes must equal the guard baseline, proving no shared icon cache or other process-global state. Asserts no `renderer_v2` module or package was created by this plan: `src/environment/renderer_v2/` does not exist, and `import src.environment.renderer_v2` still resolves to the `.py` file. |
| `src/environment/dashboard/panels.py` (new) | `PanelSpec`, `RenderContext`, `FrameInputs`, registry, completeness rule, observed-vs-hidden rule, `_recording_flag`, `real_available` from params. |
| `src/environment/dashboard/labels.py` (new) | V2-owned channel label table (`HPR` etc.) overriding adapter labels (§D1.3). |
| `src/environment/dashboard/layout.py` (new) | Column packer, `Box`, `LayoutOverflowError`, compact fallback; no Matplotlib import. **Revision 18:** `ARENA_CELL_PX = ARENA_CELL_MIN_PX = 50` (was 48 at Revision 17); the fallback order first asks whether the world fits whole at 50 px — the only step a maintained config reaches — then the local window. **Revision 19 (§R19.2):** built from **§D1.2 as rewritten** — Figure 3's constants (`LEFT_W = 320`, `MIN_RIGHT_W = 440`, outer 24 / gap 16 / pad 16 / header 64), and the arena is a **fixed** `W × 50` box, never a grow panel. **One** check covers every way the arena's height can be chosen — world size, whole-world rule, or the fallback's shrink step: the right column must fit the arena height selected (this subsumes §R18.2 item 9). |
| `tests/env/test_dashboard_layout.py` (new) | Boxes disjoint/inside canvas for all cells. Toggling a modality frees its height. Overflow raises. Unregistered name raises. **M4 context has no observed Nutrition/Injury rows.** `real_available` identical for two episodes of one run. `_recording_flag` import confinement. **Revision 19:** the arena box is exactly `W × 50` and **never larger**; a **synthetic `LayoutContext`** (thermal on + one sense at r ≥ 1) yields the 564 / 476 / 236 geometry — synthetic because no maintained config has both a thermoception card and a sensor band (#59); a **5×5** world yields a 314 × 314 card with a 726 px right column; and a synthetic 5×5 context with thermal *and* a band raises `LayoutOverflowError` naming the right column (§R19.2). |

**Phase 2: painters and episode renderer**

| File | Change |
|---|---|
| `src/environment/dashboard/text_fit.py` (new) | `fit_text` with the numeric-raise / free-text-ellipsis split, logging. |
| `src/environment/dashboard/painters.py` (new) | One painter per kind with `build`/`update`, card outlines as separate artists, `gid`s, iconless-entity glyph table. Imports from `renderer.py` read-only only what §D1.3 still pins (`draw_boresight_diamond`, `save_jax_video`, `COLORS`). The icon loader (cache-free) and the thermal helpers (two-slope) are copied into `src/environment/dashboard/icons.py` and `thermal.py` (Revision 7). Any helper needing a change is **copied** into the package; **`renderer.py` is not edited** (frozen). **Revision 22 §R22.3 / §R22.7 (Q21 "keep" branch only):** `build_minimap`'s per-square pool loses the **rim pip** and gains **up to four wedges** (`n = 1` whole dot, `n = 2` halves, `n = 3` at 120°, `n = 4` at 90°, `CELL_PRIORITY` order); the amber identity pip moves from the square's centre to **its owner's wedge centroid** for `n ≥ 2`; and the card caption is rewritten to describe the encoding that ships while still containing the substring `shared square` the audit keys on and still stating in words that **colour is the code here** (§R17.4's on-page requirement, §R22.8). |
| `src/environment/dashboard/cells.py` (new, Revision 17) | Square composition: bed table (`bed_bush` / `bed_rock` / `bed_tree` / `bed_campfire`, `BED_MARGIN = 0.14`), companion-form table with the identifying-mark fractions as constants, `CELL_PRIORITY = ("agent", "predator", "hiding_predator", "food", "neutral")`, the slot packer (1 / 2 / two-row for 3–4), and the shared-cell agent rule (halo dropped, ring and chevron kept). Forms ported from the round-2 design mock with attribution. The arena painter is a caller. **Revision 19 (#58):** every form drawn inside an arena square — bed, token, companion form, agent marker — is a **vector primitive** built here, never a raster image, because the floor tests recompute `MIN_MARK × h` as a number. The keyline's stroke width and placement are stated as constants (§R17.3 item 7 as corrected). |
| `tests/env/test_dashboard_cells.py` (new, Revision 17; numbers updated Revision 18) | Slot geometry at **50 px** (`h` = **15.00 / 10.35 / 10.12 px** for 1 / 2 / 3–4 occupants — the 48 px values 14.4 / 9.9 / 9.7 are superseded, §R18.3); every entity name the matrix can place is in `CELL_PRIORITY`; every terrain has a bed form and every token a companion form; the keyline radius is exactly `h` (the adjacent-slot touch test); the minimum-square arithmetic is recomputed from the mark fractions and compared against the recorded 49 px / 50 px floors, so a change to a form that breaks legibility fails here rather than in a video. **Revision 19 (#60):** the chevron floor is recomputed too, as `0.62 × h ≥ 6 px` (equivalently `h ≥ 9.68 px`) — the drawn chevron length, which is what 6.42 / 6.27 px are; the four-way clears it by 0.44 px. **Revision 20:** the zorder pins are asserted here too — bed < token, square outline < token, footprint outline < token — and every bed form is a single artist whose ink covers ≥ 40 % of the square (§R20.1, §R20.2, §R20.8). |
| `src/environment/dashboard/episode.py` (new) | `EpisodeRenderer` (setup / `frame` / `close` / `layout_signature`), wrapper `render_dashboard_frame`. **Revision 17:** `layout_signature()` includes the arena square size and the window rule (whole world vs local window), so a concatenated video can never switch square size or window mid-video. |
| `tests/env/test_dashboard_frames.py` (new, `integration` marker) | Audit clean on all cells' checked frames + stress variant. Mutations M-A..M-D fail as expected. Value-to-pixel, obstacle-ink (CP2.6), observed-caption (CP2.5) and vocabulary (CP2.4) checks. Glyph-code uniqueness. |
| `tests/env/test_dashboard_thermal.py` (new) | Thermal tests per the **Revision 9** note item 8: episode-range pre-pass, neutral setpoint, concatenated union range, clamp-and-outline, cooling-world crop, pre-thermal recording, per-step-recompute mutation. The Revision 6–8 params-bound tests are withdrawn. |
| `tests/env/test_dashboard_proprioception.py` (new, Revision 9) | E1 and M5 render a six-chip Proprioception panel. The highlighted chip equals the recorded previous action at a sample of steps, and highlight ink is the agent colour (CP-C). No chip is highlighted at step 0 if no previous action exists. |
| `assets/fonts/dashboard_sans_tab/` (new asset folder, Revision 8) | "Dashboard Sans Tab" font files (Pretendard with tabular digits frozen into the cmap; renamed per the OFL Reserved Font Name clause), `OFL.txt`, `README` (upstream version, exact freezing step, licence note). Loaded only by `src/environment/dashboard/`. V1 unaffected (CP-G frames). |
| `assets/dashboard_icons/` (new asset folder, Revision 8; **scope narrowed Revision 19, #58**) | Fixed-size artwork that is never recomputed — legend chips and minimap glyphs — per the design spec §Icon style guide. **Nothing drawn inside an arena square comes from here**: beds, tokens, companion forms and the agent marker are vector primitives in `cells.py`. Existing `assets/*.png` untouched. Test: every entity name the matrix cells can place has a vector form in `cells.py` **or** an entry here, or is listed as glyph-fallback. The Implementation Report records whether the legend/minimap glyphs are also drawn from the vector forms, in which case this folder is dropped. |
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
| `scripts/eval/episode_viewer.py` (new) | Server (§D3). **Revision 17:** `/api/values` also returns the per-square occupant list, so the page can name what shares a square; if the viewport forces squares below **50 px** (Revision 18) the page says so rather than shrinking silently. **Revision 18:** the list now covers every square of the world (100 for a 10×10), not the 25 of a 5×5 window. |
| `scripts/eval/episode_viewer.html` (new) | Page; light mode. |
| `tests/scripts/test_episode_viewer.py` (new) | Served PNG == in-process array; `/api/values` == `extract` including observed/hidden flags; out-of-range → 404. |
| `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` | §3 row for `episode_viewer.py` (hand-run server). A "**not a script**" row for `episode_viewer.html` (served by the viewer; precedent row `scripts/analysis/pipeline_layout.html`). §1c row for `tests/scripts/test_episode_viewer.py` (bare-imports the viewer; `parents[2]` depth). |

**Evidence already on disk (commit alongside this plan; top-level decides)**

`docs/develop/active/refactors/renderer_layout_redesign/` holds `render_current_frames.py`, `figures/v1_thermal.png`, `figures/v2_thermal.png`, `data/`, plus the artifact-page builder files.

**Docs (same change as the code they describe)**

| File | Change |
|---|---|
| `docs/environment/12_renderer.md` | Replace the dormant-V2 sections with the registry / packer / episode-renderer design, the observed-vs-hidden rule, the separate `render_recordings_v2.py` entry point and `videos_v2/` folder (V1 remains what training and eval use), viewer, audit, and "add a modality = registry entry". **One disambiguating sentence:** "'V2' in documents before 2026-09-14 means the April 2026 subfigures renderer in `src/environment/renderer_v2.py` (dormant, to be removed at the retirement gate); from 2026-09-14 'V2' means the registry-based renderer in `src/environment/dashboard/`, run via `scripts/eval/render_recordings_v2.py`." Fix stale `render_recordings.py` line citations. **Revision 17:** add the square-composition rule (bed / token / slot vocabulary, `CELL_PRIORITY`, the shared-cell agent rule), the minimap's coded encoding with its on-page statement, and the three unsolved cases (multiplicity, four-way degeneration, a resource stranded on a blocking tree). **Revision 18:** the **50 px** square, the **whole-world** grid view (no window, no panning, no viewport rectangle on the minimap), and the measured 49/50 px legibility floors it clears. |
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
- **Revision 18:** the grid view shows the **whole 10 × 10 world**, not the `LOCAL VIEW 5×5` the ASCII above draws, and its squares are **50 px** (the centre card is 564 × 564 px). Nothing pans and nothing centres on the agent.
- **Revision 17** (square size superseded by Revision 18): arena squares are **48 px**, terrain is drawn as the square's ground cover (a "bed") rather than a centred glyph, and a shared square lays its occupants out in slots — one centred, two side by side, three or four in a two-row band. A square holding the agent and a bush shows both, at the agent's full size. The ASCII above cannot draw this; §R17.3 is the specification and Figure 3 plus the design review are the visual reference.
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
- **Revision 18:** as in the thermal block above, the `ARENA · LOCAL VIEW 5×5` title the ASCII draws is superseded — the grid view shows the **whole 10 × 10 world** at 50 px squares, so the title reads `ARENA · WORLD 10×10` and the panel does not pan or centre on the agent. The "no thermal underlay, so the arena takes the full column height" note still holds; the arena is still square and still width-limited.
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
  - *2026-09-16 developer, demonstration-loosening re-record:* **frame baseline re-recorded again, and the control behaved exactly as a control should.** The recording world was loosened in memory (see the Implementation Report "Demonstration loosening"), so `record-frames --force --note` was re-run. **M1 and M2 — whose world did not change — are byte-identical on all 8 frames, all payloads and their `run_meta`; M4, whose world genuinely changed, moved on all 8** (`3da423ec…` → `fd92f8c3…`). `frozen_files`, `user_accepted` and `plan_start_commit` are untouched. `check` afterwards: 10 PASS + `FRAMES PASS` ×3, exit 0.
- [ ] **CP-G: V1 pipeline untouched (after every phase, 0 through 4).** `v1_path_guard.py check` exits 0. The report pastes the diff stat, the trailer-annotated `git log`, and each frozen file's state. ATTRIBUTED re-records cite the foreign commits. *Fails if:* any file or frame is UNATTRIBUTABLE (only the user clears it, via `accept` for that exact content), a phase commit touches a frozen file, or a `renderer_v2` package/module is created.
  - *2026-09-16 developer (Phase 2):* **PASS, before and after.** `PASS=10, ACCEPTED=0, ATTRIBUTED=0, UNATTRIBUTABLE=0`, `FRAMES PASS` on M1/M2/M4, `RESULT: OK`, **exit 0**. No frozen file was touched and no `renderer_v2` package exists — now pinned by a test (`test_dashboard_v1_imports.py`) rather than only by the guard, which hashes the *file* and would stay green beside a shadowing package. The new package also never **imports** the frozen renderer, checked in a subprocess with a blindness control, so the frozen renderer's process-global icon cache cannot be primed by a V2 render.
- [ ] **CP0.2: Matrix recordings.** (Revision 10 check first.)
  - Every generated cell's `config_path` is `configs/environment/default.yaml` or under `configs/environment/experiment/basic/`, and every override value that reproduces an archived world matches the cited archived YAML text.
  - **Loadability is re-tested here, not assumed — through the resolving loader (Revision 12).** `load_env_params(load_env_config(path))` is run on every config the matrix intends to load and the result printed per file. **Raw `yaml.safe_load` is forbidden for this check**: it does not resolve `extends:` and reports inherited mandatory keys as missing (the retracted Revision 11 §2; KNOWN_BUGS "Config inheritance ignored", `22c73bac`). *Fails if:* the check is performed with a non-resolving read. Measured 2026-09-16: `default.yaml` and all seven `basic/*.yaml` load; archived `thermal/campfire_world.yaml` loads; archived `sensory_ladder/V2_blur20.yaml` does not (stand-alone, no `extends:`, missing `body.recovery_in_bush_multiplier`) — which is harmless, as no cell loads it.
  - **Revision 11 — the regenerated campfire config loads.** `load_env_params` on `basic/<NN>-campfire_thermal_<size>.yaml` succeeds, and the printed resolved config shows `sensory.visual_value_mode` and `body.recovery_in_bush_multiplier` present, and `blocks_animals` set explicitly on every obstacle entry.
  - **Revision 11 — no archived path is a runtime input.** The generator's recorded `config_path`, `config_chain_sha256` and `overrides_source` fields are printed; no `config_path` and no entry of any `extends` chain lies under `configs/environment/experiment/archive/`. `overrides_source` may cite an archived path, since that is provenance for copied text, not a load.
  - *Fails if:* a cell loads a config outside the maintained set, a cell or its `extends` chain touches `archive/`, a config the matrix intends to load raises at `load_env_params` with no recorded fallback to `default.yaml` + overrides, an override value differs from its cited source, or the regenerated campfire config has not passed `env-config-reviewer`.
  - **Revision 13 (2026-09-16), binding:** the clause "M7–M9 load; V1 renders step 0 of each" is **struck for Phases 0 and 1**. All three raise `AttributeError: 'EnvParams' object has no attribute 'thermal_enabled'` at `src/environment/sensor.py:577`, which no Phase-0 change may fix (the file is frozen). They re-enter at the **Phase 1 `_recording_flag` gate** defined in §D5.1. The generated set is **M1, M1x, M2, M3, M4, M4b, M5, M6, M6b** — nine cells, all present and reported. *Fails if:* any Phase 0 or Phase 1 checkpoint is treated as blocked on M7/M8/M9, or the generator crashes (rather than reporting BLOCKED) on one of them.
  - Then: M1–M6b are written, including M4b (M4b's breakdown must lack `Body Temperature`, and its temperature row renders "not observed"); ~~M7–M9 load; V1 renders step 0 of each~~. Per cell, print the snapshot keys, `true_obs is None`, the breakdown names, and the breakdown ↔ noise-order mapping. Also print each cell's `synthetic` flag and `overrides`, its `config_sha256`, the diamond-offset function name (§D7.7 item 8), and whether `Body Temperature` is in its breakdown, plus that viz entry's keys. *Fails if:* M4 lacks `thermal_field`; M4's breakdown contains Nutrition/Injury (the D10 premise is then wrong, so re-check); M4's `Body Temperature` entry lacks a `value` key, or the registry has no owner for a breakdown name; M3/M9 have `true_obs == obs` everywhere; M5's Olfactory is not `visual_grid`; M6b has `true_obs` present; or a mapping is unresolved. (Revision 11: the "an archive config won't load" clause is withdrawn — no cell loads an archived config. If M2/M3 still cannot be generated, the M8/M9 substitution applies and must be recorded as using a **pre-bush-change** world, per Revision 11 §4.)
  - *2026-09-16 developer, demonstration loosening:* **all nine cells regenerated; no CP0.2 failure condition fires.** The four thermal cells (M3, M4, M4b, M6b) are now `synthetic: True` and carry the loosening in `overrides` plus a plain-language `provenance` note, so a reader can see the world was loosened and by how much; the five non-thermal cells are unchanged. Re-checked per cell: M4 has `thermal_field` ✅, its breakdown still has no Nutrition/Injury ✅ (33 dims, unchanged), `Body Temperature` still carries a `value` key ✅, M4b still lacks `Body Temperature` (32 dims) ✅, M6b is still the only cell with `true_obs is None` ✅, M3's largest OBS-vs-noise-free gap is **1.27345** (non-zero, so the "`true_obs == obs` everywhere" failure does not fire) ✅, and no breakdown↔noise mapping is unresolved ✅. **No config file was edited, so CP0.2's `env-config-reviewer` gate is not re-opened by this change.**
- [x] **CP0.3: Audit positive controls.** V1 M4 reports D1, D2, D3 and D10. Dormant V2 M4 reports D6, and Interoceptive Nociception absent (plus Location/Proprioception if in the breakdown). *Fails if:* any control is missed. **Stop; the audit is broken.**
  - *2026-09-16 developer:* **MET — 7/7 controls fired** (`render_layout_audit.py --controls`, exit 0): D1, D2, D3 on V1 M4; D6, D8 on dormant V2 M4; plus D10 and D12. Each is reported with both participants, the measured overlap in pixels and the coordinates, so a control cannot pass because something else was flagged in the same frame. **One plan correction (owner `senior-developer`): §A2 classes D2 as "text-on-text", and measured it is not** — `'REAL: --'` and the `EXTERO NOCICEPTION` title are a fixed 1.5 px apart and never share a pixel, in the current M4 fixture *and* in the archived world the evidence frame came from. D2 is real but is an **out-of-card** defect (the label is drawn in the card's title strip, outside the card whose bar it labels), and is detected as such. Details in the Phase 0c Implementation Report.
  - *2026-09-16 developer, fix pass:* **still MET — 7/7 controls fire on the same rules, the same elements and the same coordinates**, and the checkpoint is now defended from the other side as well. The controls only ever measured *sensitivity*: an `ink()` that returned all-True — an instrument flagging every pixel of the canvas — passed all 18 original tests and fired all 7 controls. Negative controls were added (the exact absent-panel set, exact per-rule finding counts on two frozen frames, the rules that must stay silent, and the control coordinates), and under that mutation **10 tests now fail**. Suite 18 → 38 tests, all green unmutated. One new, previously unnumbered **real** defect found while re-examining the "benign" class: the thermal scale's `+84` end label is painted over by the colour strip's last segment. **Owner `senior-developer`** for a defect number. See the Phase 0c fix-pass report.
  - *2026-09-16 senior-developer, fix-pass verification:* **MET, and the mutation claim reproduces independently.** The verifier re-ran the flag-everything mutation with its own construction (a pytest plugin patching `FrameProbe.ink` at class level to return `ones_like` of the real mask, rather than the in-suite `monkeypatch`): **10 failed, 28 passed**, the same ten test names the developer reported. The complementary mutation — an `ink()` that sees *nothing* — fails **17**, including the four pixel positive controls, which shows the controls are falsifiable from the other side. The new defect is numbered **D13** in §A2, re-derived from the frozen source's own constants and confirmed in the composite pixels. Full report in the Verification Report below.
- [ ] **CP0.3b: The audit sees squares (added Revision 17; rewritten Revision 19 §R19.1; controls and floor extended Revision 20).** `cell_overdraw` fires on **five** synthetic mutations — concentric drawing (**M-E**), the bed drawn above the tokens (**M-F1**), the bed drawn above the tokens but inset so a rim survives (**M-F2**, which only the survival floor can catch), the minimap's agent dot above the split wedge (**M-F3**), and the **ground** drawn above the tokens with the figure facecolor set to `CANVAS` (**M-F1g**, Revision 20 §R20.6, which only precondition (c′) can catch) — and is silent on **every** negative control. The per-rule finding counts on the frozen M1 and M4 frames are re-pinned and every rule's count is **unchanged** — `cell_overdraw` cannot run on a frozen V1 frame at all (V1's arena axes is unlabelled), so every control here is a figure the test builds, and this clause asserts the new rule disturbs nothing existing (#62).
  - **Negative controls (Revision 20 §R20.2, §R20.8):** single occupant; empty square; **campfire** bed plus one token (the bed with the most parts, and the only one whose largest part is under the 40 % line); a correct two-mover square **containing the agent**, so its square outline is present; a correct four-way square **containing the agent**, the tightest clearance in the design; and an E-cell footprint edge crossing an occupied square. Each produces **zero findings** and its measured survival ratio is recorded.
  - **The survival floor is swept, not asserted (Revision 20 §R20.3).** The report carries a **gap table**: the **minimum** survival ratio over every negative control above, and the **maximum** over an **M-F2 family** at insets `0.005 / 0.010 / 0.020 × cell` (re-registered from `0.02 / 0.05 / 0.10` in Revision 21 §R21.2, because at the larger insets the shrunken bed stops being classified as a bed and the member stops measuring the floor). `SURVIVAL_MIN = 0.98` must lie between them with margin. Any negative control below **1.000** is investigated and its cause written down before it is accepted.
  - **The cross-Axes order comparator is pinned by pixels (Revision 20 §R20.1).** A two-element figure in two Axes of known zorder is rendered, and the composite colour at the shared pixel must agree with the comparator's verdict in **both** orders.
  - **The bbox-padding optimisation is proved equivalent, not assumed (Revision 20 §R20.7 item 4).** One control is run both with and without the "padded bbox cannot reach this square" skip, and the findings must be identical.
  - *2026-09-17 developer:* **BUILT AND CALIBRATED, but NOT TICKED — one negative control fails at the constant the plan specifies, and the constant is the plan's to move, not mine.** All **five** mutations fire, each via the rule named for it: **M-E** and **M-F1** and the three-member **M-F2** family via `cell_overdraw`, **M-F1g** via precondition (c′) alone. **Eight of the nine** negative controls are silent at the shipped `CELL_FLOOR_FRACTION = 0.40`; **all nine** are silent at `0.48`. The one that fails is **a lone agent on bare ground**, and it is a defect in §R19.1 step 2 rather than in the painter: the agent keeps its halo on an unshared square (1.32 × its own radius, §R17.3 item 8), so that **correct** token's ink measures **43.76 %** of its square — above the 40 % "this element IS the floor" line — and the occupant is excluded as scenery, leaving 0 components against 1 kind. This is the exact mirror of §R20.8, which fixed the same classifier from the bed side. **Both populations are measured, so the choice is evidence and not argument:** largest correct token **0.4376**, smallest bed **0.5168**, bed floor by construction **0.5184** (already pinned by `test_dashboard_cells.py`). A floor of **0.48** sits **53.5 %** of the way up that gap. The constant is **not** moved here — §R20.3's discipline is that a constant moves in this plan text with its evidence, never in a test to turn a checkpoint green — so the control ships as a `strict` xfail naming the measurement, and **`senior-developer` owns the decision**. The two candidates are: move the floor to 0.48 in §R19.1 step 2, or drop the halo on every square (the painter already drops it whenever the square is shared, Phase 2 deviation 1).
  - *2026-09-17 developer, the rest of the clause:* **met.** Frozen per-rule counts on V1 M1, V1 M4 and dormant V2 M4 are **unchanged** — the pre-existing pinned-count tests pass untouched, which is what this clause asks (#62). Suite **38 → 66 passed + 1 xfailed**. **Gap table (§R20.3):** minimum over the negative controls **1.000000** (every correct square measures exactly 1.000, including the four-way with the agent, §R20.2's tightest case, which measures 1.000 because `cells.py` pins the outline below the tokens); maximum over the M-F2 family **0.198444**; `SURVIVAL_MIN = 0.98` lies between them. A floor sweep from 0.50 to 1.000 flips **no** verdict on **any** control, so 0.98 is not near a cliff — the nearest boundaries are 0.198 below and 1.000 above. **Two M-F2 members do not measure the floor and are excluded from that maximum with their reason:** insetting the bed shrinks it under the floor test, so it stops being a bed, is read as a token and is caught by the disjointness rule instead — still a failure, but its survival is 1.0 and would poison a table it never measured. **The pre-registered family of three insets is therefore not all reachable as specified** (bed ink share is `(0.72(1−2i))²`: 47.8 % / 42.0 % / 33.2 %), which is a finding about the plan's own numbers. Cross-Axes comparator control: **passes in both orders**, the composite pixel agreeing with the derived rank. Padded-bbox equivalence: **identical findings** both ways. Adjacent slots at 50 px with the real forms: **0 shared pixels**, so §R19.4 item 2's figure holds at the decided square and no keyline change is needed.
  - *2026-09-17 developer, a defect in the instrument itself, found by these controls:* **every `Collection` artist was silently dropped from the audit's element list, on every frame.** `Collection.get_window_extent` returns an empty bbox `(inf, inf, −inf, −inf)`, which `enumerate_elements` filtered out — and an artist that is not an Element is **never hidden by `FrameProbe._draw`**, so it was painted into every isolated render *including the bare background* and ate the ink of whatever it covered. Measured: the page rectangle's isolated ink came out **665 px short**, exactly the area of the two tokens sitting on it. It matters twice — the redesign draws every bed and token as one `PatchCollection` (§R20.8), so the rule would have measured an arena with nothing standing in it; and the **frozen V1 and dormant-V2 frames carry 17 visible `LineCollection`s each**, whose ink has been contaminating every isolation measurement taken on them since Phase 0c. Fixed with a path-extent fallback; **the frozen counts did not move**, which is the evidence that no existing verdict rested on it. **Not in the Known Bugs registry** (grepped 2026-09-17; rows 117–119 are the renderer's D1–D13 and row 179 is the import-isolation test) — **`bug-curator` owns filing it.**
  - The adjacent-slot control of §R19.4 item 2 is measured at 50 px and its reading pinned.
  - **Minimap controls (added Revision 22 §R22.6).** `minimap_overdraw` fires on **M-F3** (the agent's dot above the split wedge), **M-F4** (the identity pip drawn at the square's centre on a shared square, so it straddles a foreign wedge — this is the painter's pre-Revision-22 behaviour, so the mutation is produced by reverting it) and **M-F5** (any minimap artist other than a hiding predator's identity pip painted `HIDE_EYE`). It is silent on: a **solo hiding predator with its identity pip** (the exact square that fires today); a two-occupant square containing a hiding predator with the pip in its own wedge; a correct three-way; a correct four-way; and a correct **two-predator** square (two movers, one kind, one colour — §R20.4's case). The four-way's smallest-wedge classified pixel count and its denominator path (`isolated-wedge` or `geometric`) are **recorded as numbers**, because §R22.3's pre-registered fallback branches on them. *Fails if:* M-F4 or M-F5 is silent, any negative control fires, or any minimap constant (`SURVIVAL_MIN`, `MINIMAP_AREA_MIN`, `MINIMAP_DELTA`, `MINIMAP_ALIGN_MAX_BLANK`) is changed to make a control pass.
  - *2026-09-17 senior-developer, verification:* **everything built in Phase 0d verifies, and the one blocker is now decided — CP0.3b needs one more developer pass before it can be ticked.** Re-derived independently rather than read: **M-F1g is silent with precondition (c′) disabled** (2 kinds → 2 isolated → 2 visible components, survival 1.000/1.000, **zero findings**) and fires via `cell_probe_blind` with it enabled — so the rule's hardest clause is load-bearing and alive, exactly as §R20.6 predicted. The **Collection-enumeration fix is confirmed and so is the claim that nothing moved**: the frozen V1 M4 and M1 frames each carry **17 visible `Collection`s**, the element list goes 305 → 322 (M4) and 204 → 221 (M1), and **every per-rule count is byte-identical before and after** on both frames (checked by neutering the new path-extent fallback and re-running the audit) — so no earlier calibration in this plan rested on the bug. Control suite reproduces at **66 passed, 1 xfailed**. **What remains before the tick:** (a) the floor constant moves to **0.48** per Revision 21 §R21.2 and the `strict` xfail is replaced by a plain negative control; (b) the **M-F2 family is re-registered at insets `0.005 / 0.010 / 0.020`**, because at 0.48 the 0.05 member stops measuring the floor and the gap table would otherwise rest on a single member; (c) the gap table is re-run and re-recorded at the new constant. Nothing else in CP0.3b is outstanding. The Collection defect is **`bug-curator`'s to file** and is not yet in the registry.
  - *2026-09-17 developer, the remaining pass — **CP0.3b is now MET**.* The three items the verification left are done, at the five sites Revision 21 §R21.2 names and nowhere else: `CELL_FLOOR_FRACTION` **0.40 → 0.48** with both measured populations in the constant's comment; the `strict` xfail **removed**, the lone agent on bare ground joining `NEGATIVE_CELLS` as a plain negative control; the inverted assertion **`token < CELL_FLOOR_FRACTION < bed`**, which fails in both directions (below the token the classifier calls an occupant the floor, above the bed it calls the floor an occupant); and the **M-F2 family re-registered at `0.005 / 0.010 / 0.020`** with a new assertion that **all three fire the survival floor specifically** — a member caught by another rule has survival 1.0 and never measured the floor. Suite **67 passed, 0 xfailed** (was 66 + 1 xfailed); full `tests/env` **603 passed, 0 failed**. The gap table re-run on the real painter is in the CP2.8 note below: the correct side measures **1.000** and the re-registered family measures **0.0921 / 0.0954 / 0.102** (and `0.1323 / 0.1362 / 0.144` for the second occupant), reproducing §R21.2's pre-registered figures, so `SURVIVAL_MIN = 0.98` still lies in the gap with margin. **The constant was moved only because the plan moved it first, with its evidence.**
  - *Fails if:* the rule fires on any negative control, stays silent on any of the five mutations, the gap table does not straddle 0.98, `SURVIVAL_MIN` is changed in a test rather than in this plan with evidence, the comparator disagrees with the rendered pixels, the padded-bbox skip changes any finding, a correct control measures below 1.000 without an investigation recorded, or any existing rule's count moves. **Stop; the instrument cannot see the defect the redesign exists to prevent.**
- [ ] **CP0.4: Spike and decision gate (re-specified Revision 19 §R19.3).** A minimal A-style `EpisodeRenderer` versus V1 on M4, ≥ 200 frames (first 5 excluded), pool worker, same lab node (node + CPU model recorded).
  - **Order.** Phase 1 (`layout.py`, `panels.py`, `labels.py` — no Matplotlib) **may be built before this checkpoint**; CP0.4 **must be met or escalated-and-answered before Phase 2** writes a painter. §R18.2 item 8's "Phase 1 must measure the arena painter" is withdrawn — Phase 1 has no painter.
  - **What the spike draws.** The **whole 10×10 world** with §R17.3's composition — a ground per square, a bed wherever the M4 snapshot places terrain, tokens for every occupant — plus the vitals card and one right-hand pod, figure built once, `frame(t)` updating artists. Not a 5×5 arena of plain squares.
  - **What it reports.** Setup ms; median and p95 frame ms; the frame time split across **three arms** (re-specified Revision 20 §R20.5, because two arms measured update cost and called it draw cost); and three counts — total artists, arena artists, per-square pool size — which must be **identical across the arms**.
    - **Arm 1** nothing disabled — the real per-frame cost.
    - **Arm 2** the arena painter's *update* disabled, artists still visible — arm 1 − arm 2 is the arena's **update** cost.
    - **Arm 3** the arena **Axes** hidden (`set_visible(False)`) — arm 1 − arm 3 is the arena's **update + draw** cost, and arm 3 is the true **non-arena** number. Labelled a synthetic reference: it composes a frame no viewer sees. **If Q22 is ever asked, its option 3 is scored against arm 3**, never arm 2.
  - **The spike's cell code is scratch (Revision 20 §R20.7 item 3).** It lives under `tmp/`, is imported by nothing in `src/`, and does not become `cells.py`. What carries forward is the measurement: the report names which forms the spike drew and the per-square and total artist counts, so Phase 2 can reproduce the cost.
  - **One failure path, pre-registered.** median ≤ 0.5 × V1 → gate met, Q9 untouched, Phase 2 proceeds, **no user question asked**. 0.5× < median ≤ 1.0× → report the split, the counts and **Q22**'s four options to the user and **stop**. median > 1.0× → the hard floor is breached; same report and question, with the Pillow option named as live. *Fails if:* the developer changes the gate, the square size or the stack without the user's answer, or the split and artist counts are not reported.
  - *2026-09-16 developer:* **still unrun as specified, and Phase 2 was written anyway on the user's explicit instruction — flagged, not absorbed.** An indicative in-container measurement (40 frames, first 5 excluded, same recording, same process — **not** a lab node and **not** a pool worker) gives V1 median **333.0 ms**, V2 median **187.3 ms**, **ratio 0.563**. That is inside the pre-registered `0.5× < median ≤ 1.0×` band, so the response is **report and stop**: nothing was tuned — not the gate, not the square size, not the stack. The three-arm split is the informative part: arena Axes hidden gives 176.1 ms, so the arena is **11.2 ms of a 187 ms frame** (~6 %), with 1045 visible artists of which **178** are the arena's. **The four-fold arena growth Q22 was opened about is not what is costing the time** — the text-heavy cards are — which bears directly on Q22 option 3.
  - *2026-09-17 user decision, recorded by senior-developer:* **Q22 is answered — the gate is treated as MET IN SUBSTANCE at 0.563×, and Q9's `≤ 0.5 ×` is superseded by this measurement.** The reasoning and the numbers that make it defensible are in **Revision 21 §R21.1**: 1.78× faster than the renderer training uses, the miss is ~21 ms, and the arena — the thing that grew four-fold and the reason the gate was ever questioned — is **11.2 ms of 187 ms (~6 %)**. No option from Q22's table is adopted; nothing was tuned, re-authored or re-stacked. **CP0.4 is NOT waived**: the lab-node, pool-worker, ≥ 200-frame measurement is still owed and is folded into CP4. What this decision settles is the *response to the band*, so Phase 2 is no longer gated on it. Re-opened if CP4 shows V2 slower than V1 on any cell, or the arena's share rises above ~25 % of frame time.
- [x] **CP1: Registry and packer.** `test_dashboard_layout.py` is green. *Fails if:* boxes intersect; a disabled modality's height isn't freed; an unregistered name doesn't raise; M4 yields observed Nutrition/Injury rows; `real_available` differs between episodes of one run.
  - *2026-09-16 developer:* **MET — 98 tests pass.** Each of the three named failure conditions was shown to be detectable rather than assumed: a packer mutated to overlap its columns **and** to skip its own overlap check turns **16 tests red** (`test_no_two_cards_share_a_pixel` on all 8 contexts, `test_every_maintained_config_packs_and_is_complete` on all 8 configs), because those tests recompute the pairwise overlap themselves instead of trusting `pack()`. CP-G re-run after implementation: 10/10 PASS + FRAMES PASS ×3, exit 0. **Two things for `senior-developer`:** the heights of the spectrum-smell and range-0 vision pods are pinned nowhere in this plan, and the maintained campfire world (M4) is the binding case that decides them; and `tests/env/test_dashboard_v1_imports.py`, listed in the Phase 1 File Changes rows, is deferred to Phase 2 with a reason. See the Phase 1 Implementation Report.
  - *2026-09-16 senior-developer:* **MET on its own five failure conditions, with one blocker outside them.** All three named conditions were re-shown catchable by the verifier's own mutations (16 / 8 / 4 tests red respectively), the 98 tests reproduce, the pod budget and the band rule were re-derived independently, and CP-G re-run is 10/10 PASS + FRAMES PASS ×3, exit 0. **Blocking the Phase 1 commit, not CP1 itself:** the full `tests/env` run is **red** — Phase 1's new package makes the Phase 0 test `test_render_audit_controls.py::test_audit_imports_neither_layout_nor_registry` fail whenever `test_dashboard_layout.py` runs first in the same process. Fix belongs to the Phase 0 test. §D1.1 and §D7.1 corrected. Full report below.
  - *2026-09-16 developer (CP1 fix-up):* **Blocker cleared; the suite is green.** The Phase 0 leak check now runs in a **subprocess** — the assertion itself is unchanged and still demands an empty list, and it was shown to still bite by making the audit really import the package (test goes red, then green again on a byte-identical revert). Full `tests/env`: **546 passed, 0 failed** (`-m "not integration"`; was 1 failed / 540 passed) and **572 passed, 0 failed** unfiltered. The two minor findings landed with it: the box-equality exemption is **removed** from `_validate` and from the test helper rather than re-keyed, and `03-random_init_10x10_ckpt1k.yaml` joins `MAINTAINED` (**nine** configs now pack). CP-G re-run: 10/10 PASS + FRAMES PASS ×3, exit 0. See the CP1 Fix-Up Report below.
- [ ] **CP2.1: Audit clean.** All cells' checked frames: 0 collisions (text-on-border included), 0 clipped text, legibility met, presence met. The stress variant renders clean or raises; no ellipsised number. *Fails if:* any count is non-zero, or "…" appears in a numeric element.
  - *2026-09-16 developer:* **partially demonstrated — two frames of one cell, not the matrix.** On M4 (steps 0 and 32, real fixture recording): `text_over_text` **0**, `text_over_border` **0**, `clipped` **0**, `out_of_card` **0**, `out_of_canvas` **0**, `panel_absent` **0**, `observed_caption` **0**, `numeric_in_arena` **0**. The only non-zero rule is `text_over_fill` (16 / 15), every instance a label inside **its own** widget — the class the audit's docstring calls legible by design and the Correction Report leaves to CP0.3b. The audit found two defects the eye missed (a pod titled "Vision" that the title table cannot map, and a column head beginning `OBS`); both fixed, the second by renaming the head — see Phase 2 Implementation Report deviation 4. The audit was driven through a scratch harness because `render_capture` cannot name this renderer; **no audit file was edited**. 45.2 s per audited frame at ~710 elements.
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
- [ ] **CP2.6: Entities drawn.** On M4, a step with the campfire in view shows non-empty foreground ink in its square, and glyph codes are unique across `obstacle_names`. **Revision 19 (#58):** the campfire is a **drawn bed**, not a raster icon, so the clause "that ink belongs to an `AxesImage`" is withdrawn and replaced by: the campfire's ink is present, is classified as a **bed** by the square-area test (**≥ 48 % since Revision 21 §R21.2**; 40 % as first written), and is not the `CF` glyph fallback. *Fails if:* the square is empty, the ink classifies as a token rather than a bed, the glyph fallback was used for a terrain that has a bed form, or codes collide. **Revision 17:** a *shared* square must additionally show ink for every distinct kind its snapshot places there — the campfire's bed and any token standing on it are both checked, and per §R19.1 the token's ink must **survive** the bed.
- [ ] **CP2.7: Extended-range senses.** (Unblocked 2026-09-14: Q5 answered, so Proprioception is drawn as `action_chips`.) `test_dashboard_extended_range.py` green for the decided encoding, A `channel_maps` (r ≥ 1), including:
  - E2n with and without true observations;
  - identical boxes across two episodes with different maxima;
  - forced side column raising wherever the band was chosen;
  - E6's channel label not `GRS`;
  - r_max recorded only after a rendered, audited override, with machine and fonts named. Largest fitting radius per kind recorded in the report and in `12_renderer.md`. E2–E6 take the sensor-band layout if and only if the side column fails its min size. *Fails if:* any in-use cell (E1–E6) raises; any synthetic cell renders past the recorded largest radius instead of raising; a value above 1 is clipped by the scale; or a concatenated video switches layout.
  - **A modality in the breakdown must have something DRAWN in its box (added Revision 22 §R22.9, from a finding surfaced by the CP2.8 real-painter pass).** No maintained matrix cell may report `panel_absent` for a modality that is present in its own `get_observation_breakdown(params)`. **`M5` is named as the case that must go green:** it is the only maintained cell with `olfactory_range: 1`, so it takes the **sensor-band** layout and has no `olfactory` card, and the band painter is deliberately unbuilt — so olfaction is in its observation with a box reserved and **nothing drawn in it**. The audit is right and this is unbuilt scope, not a defect and not a Known Bugs row; it is gated here so it cannot be rediscovered later as one. This is also the checkpoint where the CP1 band-card hoist is first exercised by a real world (§R21.4 item 3). *Fails if:* CP2.7 is ticked while any maintained cell still reports `panel_absent` for a modality in its breakdown.
- [x] **CP2.8: Shared squares render every occupant (added Revision 17).** On every matrix cell, each checked frame containing a shared square passes `cell_overdraw` (0 findings). All five archetypes — agent on terrain, two movers, three-way, four-way, resource on terrain — are rendered and **looked at** at full size, each either found in a real episode or drawn from a labelled synthetic snapshot. Mutations **M-E** (all occupants forced to the square's centre) and **M-F1 / M-F1g / M-F2 / M-F3** (bed drawn above the tokens; **ground** drawn above the tokens with the figure facecolor set to `CANVAS`, Revision 20 §R20.6; the bed inset so only a rim survives; the minimap's agent dot above the split wedge) each fail the audit on the **real** painter, not only on the Phase 0d synthetic figure. **Sample size (Revision 20 §R20.7 item 4):** `cell_overdraw` runs on **at most two frames per matrix cell** — one archetype-rich frame plus step 0 — because isolation is N+1 renders and a 100-square arena carries several hundred visible elements; archetype coverage is carried by the Phase 0d synthetic controls. The test carries the `integration` marker and the report states the measured wall-clock per audited frame with the machine. The minimap's shared-square caption is present on every frame whose snapshot contains a shared square, and the occupancy rim pip shares no pixel with the hiding-predator identity pip. *Fails if:* an archetype is neither found nor synthesised-and-labelled, any finding count is non-zero, any of M-E / M-F1 / **M-F1g** / M-F2 / M-F3 — or, from Revision 22 §R22.6, **M-F4** (the identity pip over a foreign wedge) or **M-F5** (amber painted by anything but a hiding predator's identity pip) — passes, the caption is missing, the caption still describes an encoding the painter no longer draws, or nobody looked.
  - *2026-09-17 developer (Phase 0d):* **the instrument now exists, and on the two real frames it reports ZERO `cell_overdraw` findings — but CP2.8 as written is still NOT met.** What is now measured, by the instrument rather than by hand, on `M4` episode 1 steps 0 and 32: **0 cell findings at both the shipped floor (0.40) and the candidate (0.48)**; every occupant measures **1.0000**; the two-occupant square **(5,1) `agent + food`** measures **2 kinds → 2 isolated components → 2 visible components → 1.0000 / 1.0000**; `(3,5) `neutral + rock`` and `(4,3) `agent + bush`` each measure **1.0000** over a bed. **It reproduces Phase 2's hand measurement exactly and independently, and there is NO disagreement:** bed ink **53.44 %** (bush) and **51.68 %** (rock) against the hand-measured 53.4 % and 51.7 %, and token survival 100.0 % against 100.0 %. The audit derives its occupancy from the recorded snapshot itself, and that ground truth was checked against the renderer's own `occupancy_of` — **they agree on every square of both frames**, which is what makes this an independent reproduction rather than the same computation run twice. `text_over_fill` reads **16 / 15**, matching Phase 2's report. **Cost: 46.5 s and 46.3 s per audited frame at 735 / 737 elements** on this container (Phase 2 measured 45.2 s at 708–710), so adding the rule did not change the per-frame cost materially — the number CP2.8 asks to be stated for sizing its sample.
  - *2026-09-17 developer, why CP2.8 still does not close.* Four of its clauses are untouched by this phase, and none of them is the instrument's fault: (1) **the mutations were not run against the real painter** — M-E / M-F1 / M-F1g / M-F2 / M-F3 all fail on the Phase 0d synthetic figures, but CP2.8 requires them to fail "on the **real** painter, not only on the Phase 0d synthetic figure"; (2) **two archetypes of five** appear in these frames (agent on terrain, two movers) — the three-way and four-way were not reached and were not synthesised; (3) **one matrix cell**, not every cell; (4) **nobody looked** at the frames at full size in this phase. **And the minimap clause cannot be assessed at all yet:** the rule divides the *named axes* into world squares, which is exact for the arena — whose axes **is** the grid — and wrong for the World map, whose axes is the **whole card** with the grid inset below its title and above its caption. Pointed at it, the census samples card background and finds nothing in **9 of 9** colour-bearing squares; rather than emit nine confident wrong "this dot was painted over" verdicts it emits **one** `minimap_grid_unaligned` and reports nothing else. **The cheap fix is a painter change that mirrors what the arena already does** — give the map grid its own labelled Axes inside the card, exactly as `arena_card` / `arena` are split — and it is `senior-developer`'s call. The **shared-square caption check does work** and is silent on step 32, which holds a shared square.
  - *2026-09-16 developer:* **CANNOT BE MET TODAY — the instrument does not exist.** `scripts/eval/render_layout_audit.py` contains no `cell_overdraw` and no `SURVIVAL_MIN`; **CP0.3b is unticked** and Phase 0d was never built. No partial version of the rule was written, deliberately: a half-built instrument that passes is worse than none. The substance was instead **measured by hand in scratch**, by §R19.1's own method (isolated ink per artist, then the pixels no later-drawn artist covers), on the real M4 frames: square (4,3) `agent + bush` — bed ink 53.4 % of the square, bed survives 55.1 %, **agent token survives 100.0 %**; (3,5) `neutral + rock` — 51.7 %, 60.5 %, **100.0 %**; (5,1) `agent + food` — **100.0 % / 100.0 %**. Every bed clears the 40 % line that classifies it as floor, and every occupant measures the 1.000 a correct composition must. Three of the five archetypes (agent on terrain, two movers, resource-adjacent) were found in real episodes; the three- and four-way were not reached and were not synthesised. **This is evidence, not the instrument, and it does not close CP2.8.**
  - *2026-09-17 developer, the real-painter pass:* **the arena rule is clean on every matrix cell, all five mutations fail on the real painter, every archetype is rendered and looked at, and the rim-pip clause finally has a number — but CP2.8 still does NOT close, on the minimap side and on the test-home side.** Full detail in the Implementation Report "CP0.3b's remaining pass, and CP2.8 against the real painter". In brief. **Matrix: 18 frames, all nine cells, 2 frames each — ZERO findings** from `cell_overdraw`, `cell_opacity`, `cell_foreign_axes`, `cell_probe_blind` and `outline_like_token`; survival is `[1.0]` ×154, `[1.0, 1.0]` ×4, `[1.0, 1.0, 1.0]` ×5, with **no value below 1.000 anywhere**. **Mutations, on one real frame (`M4` f1 s32, chosen because it carries BOTH `(5,1) agent + food` and `(3,5) neutral + rock`):** control silent; **M-E** 3 findings (2 kinds → 1 component + 235 px shared token ink); **M-F1** 2 (survival 0.000); **M-F1g** 17 (nine squares at 0.000 — and on the *neutral* world it is caught by precondition (c′) alone, 784 `cell_probe_blind`, because there the ground is `TRACK`, within `INK_DELTA` of `CANVAS`); **M-F2** ×3 each 2; **M-F3** fires at exactly the target square, `seen ['agent']` where the snapshot has two kinds, with no finding there unmutated. **Two vacuity findings, recorded rather than corrected away:** M-F1 and all three M-F2 members were first run on `M1` f0 s34 and were silent — *bed-under-token squares = `{}`* on that frame, so they were **structurally incapable of firing**; and M-E is vacuous on `M4` s0, whose only shared square is `agent + bush` (one non-terrain kind). **M-F2's mechanism is shape-dependent, which is a result:** on a solo-token square the bed covers the token whole (`h = 15 px` inside a `± 18 px` plate) so it fires via the component count, never the floor; only a square with **two or more** occupants leaves the rim the floor measures. **Measured: zero real squares in the matrix hold terrain plus two or more kinds** (rule R3 — animals cannot stand on a bush or tree), so the family was also run on a **synthetic** `bush + agent + predator` square against the real painter, where all three members fire the **survival floor** at `[0.0921, 0.1323] / [0.0954, 0.1362] / [0.102, 0.144]` — reproducing §R21.2's pre-registered figures. **Archetypes:** agent-on-terrain, two-movers and the **three-way** (`(8,6) agent + hiding_predator + predator`, `M1/M1x/M2/M5/M6` f0 s34) are **real**; **four-way and resource-on-terrain occur in NO episode of any cell** and are **synthetic, labelled in the frame's own header** — a four-way measuring 1.000 is evidence about the **painter** and none about the **worlds**. All looked at at full size: the four-way renders as four equal tiles 2-over-2 inside the agent's outline, the degeneration §R17.5 item 2 predicted and nobody had seen. **Rim pip vs. identity pip: 0 shared pixels** (21 px / 17 px), on a synthetic square because the one real three-way puts the hiding predator on the rim; this needed a painter change, since the identity pip was drawn only for a *lone* hiding predator and the two could never coexist. **Cost: 44.2–53.3 s per frame at 687–755 elements, 31 frames, Intel i9-7900X, `docker-102`.** Guard 10/10 + FRAMES PASS ×3, exit 0, before and after.
  - *2026-09-17 developer, what blocks CP2.8:* **(1) `minimap_overdraw` fires on CORRECT frames** — 2–4 per frame on all 18, now that the grid-only Axes lets the census run at all. Three causes, decomposed by hiding each artist class and re-measuring, not guessed: **(A)** the amber identity pip covers ~**21 %** of its own occupant's dot (solo hiding-predator squares census **92/87/88 px**, and **116/113/115 px** with the pip hidden) against a 0.98 floor; **(B)** the rim pip is drawn at radius `0.12 × cell` centred `0.3677 × cell` out, so its inner edge at `0.248 × cell` lies **inside** the dot's `0.30 × cell` and eats the neighbouring wedge — while §R17.4's own words are "a rim pip … **outside the dot**"; **(C)** a four-way square encodes only three occupants, so the fourth kind has **no colour area at all** (measured 1 px). None is caused by this pass's pip change — (A)'s findings are all *solo* squares where the pip was already drawn, and (B)/(C) involve no identity pip. All three are contradictions between §R17.4's encoding and §R19.1 step 9 / §R20.4's ground truth, and **choosing between moving the minimap floor, redrawing the pips, or extending the encoding past three is `senior-developer`'s call** — nothing was loosened here, per §R20's narrowing rule. **(2) No committed test carries this evidence:** CP2.8 requires the `integration` marker and §R17.6 gives it the home `tests/env/test_dashboard_frames.py`, which **does not exist** (Phase 2 deferred it), so today's numbers are reproducible by hand through a `tmp/` harness but not by CI. **Separately, not a CP2.8 item:** `M5` reports `panel_absent: Olfaction` on both frames — it is the only maintained cell with `olfactory_range: 1`, so it takes the **sensor-band** layout and has no `olfactory` card, and the band painter is deliberately unbuilt. That is a true positive belonging to **CP2.7**.
  - *2026-09-17 senior-developer, verification:* **the developer's list of what is still missing is complete, not generous to itself — and one item is added.** Confirmed against the checkpoint's own clauses: the five mutations ran only on the Phase 0d synthetic figures and **not on the real painter**; **two archetypes of five** are covered (agent on terrain, two movers) with the three-way and four-way neither found nor synthesised-and-labelled; **one matrix cell** (M4) of nine; and the World map's clause cannot be assessed because the rule divides the *named axes* into squares and the map's axes is the whole card. **The "nobody looked" item is now discharged for these two frames** — the verifier looked at `M4_ep1_step000.png` and `M4_ep1_step032.png` at full size: square (4,3) shows a green bush plate with the agent standing on it inside its indigo square outline; (5,1) shows the agent and a piece of food **side by side** in one square; (3,5) shows the rabbit on a grey rock plate. That is the redesign's whole claim, visible rather than inferred. **Added to the list:** the **occupancy rim pip vs. hiding-predator identity pip** clause has no coverage at all, because the minimap painter has not reached rim pips. **So CP2.8 still needs:** the five mutations against the real painter; the three-way and four-way archetypes rendered and looked at (synthesised and labelled if no episode reaches them); the remaining eight matrix cells at ≤ 2 frames each; a **grid-only Axes for the World map** (a painter change mirroring the existing `arena_card` / `arena` split — approved here as the fix, and it is small); and the two-pip disjointness check once rim pips exist. At **46 s per audited frame**, the full matrix is ~14 minutes of audit — cheap enough that the sample size is not the obstacle.
  - *2026-09-17 senior-developer, the three minimap causes are DECIDED — see Revision 22.* The developer's decomposition is accepted as measurement rather than conjecture, and **none of the three is answered by moving the minimap floor** (§R22.4 states the test that separates this case from Revision 21's legitimate constant move). **(A)** is a defect in the **instrument**: a kind's mark may be drawn in more than one palette colour — the hiding predator's is body **plus** amber accent — so the census's one-colour-per-kind ground truth read a correct mark's own accent as 21 % of itself missing. The fix is §R19.1 step 5's union-of-own-parts rule, which the grid panel already had and the minimap variant never inherited (§R22.1). **(B)** is a contradiction in which **both** documents are wrong: a rim pip must satisfy `r_p ≤ 0.1016 × cell` to sit outside the `0.30 × cell` dot *and* inside the square, so the painter's `0.12 × cell` is infeasible **by construction**, and a compliant pip's 4–7 px colour core is below what the census or video compression can hold — §R17.4's "outside the dot" was never achievable here (§R22.2). **(C)** is a limit of the encoding, and it is **extended rather than excused**, because unlike §R17.5's multiplicity case the fourth occupant is representable with the mechanism already in use. **The decision for (B) and (C) is one change:** the rim pip is retired and the dot is divided into `n` wedges for `n = 1…4`, with the identity pip moved into its owner's wedge. **One case the developer's evidence could not contain, found while deciding:** the identity pip is fixed at the square's **centre** and is drawn whenever the hiding predator is one of the two occupants the dot carries, so on a **shared** square it straddles both half-discs and eats the *neighbouring* kind's colour — every (A) finding came from **solo** squares, so (A) is larger than measured. Mutation **M-F4** is exactly that behaviour and must fire, which is what stops (A)'s fix becoming a blanket amnesty.
  - *2026-09-17 senior-developer, what CP2.8 still needs after this decision.* **(1)** §R22.7's painter and instrument changes implemented, with §R22.6's controls — but **only on the "keep the map" branch of Q21**, which is why (2) comes first. **(2) Q21 answered.** Dropping or repurposing the World map dissolves (A), (B) and (C) together and strikes CP2.8's minimap clauses entirely (§R22.5); the gate §R19.4 item 5 set — *answer Q21 before Phase 2 starts the minimap* — has already been crossed, so this is now the binding order-of-work item, not a formality. **(3)** `tests/env/test_dashboard_frames.py` created, so this checkpoint's evidence is carried by the committed suite under the `integration` marker instead of a `tmp/` harness (the developer's blocker 2, unchanged by this revision). **(4)** the four-way census count recorded as a number and §R22.3's pre-registered branch taken on it. **Not outstanding:** the arena side — `cell_overdraw` reports **0 findings on all 18 matrix frames**, all five mutations fail on the real painter, all five archetypes are rendered and looked at, the caption is present, and the rim-pip/identity-pip disjointness clause is **discharged** by §R22.3 rather than met, since retiring the rim pip removes the collision it guarded against.
  - *2026-09-17 developer, §R22.7 implemented — **items (1), (3) and (4) are done; the blocker is now ONE cause on ONE square**.* Full detail in the Implementation Report "§R22.7: the World map's wedges, and CP2.8's committed home". **Q21 was answered (keep the map), so the whole "keep it" branch was built:** the rim pip is retired, the dot divides into `n = 1…4` wedges, the identity pip moved into its owner's wedge, the census's ground truth became a colour **set** per kind with the denominator measured over that kind's **own artists rendered together**, and the caption was rewritten to describe what is drawn. **No threshold moved.** **Matrix, same 18 frames, like-for-like:** grid-panel rules still **0 findings**; the World map goes from **2–4 findings on every frame** to **0 on 13 of 18**. **Controls:** (A)'s false alarm 73.3 % → **1.000**; correct `n = 1/2/4` all **1.000** (62/62, 48/48, 16/16, 24/24, 13/13 ×4, and a two-paint mark 6/6); **M-F3, M-F4 and M-F5 all FIRE** — M-F4 at **83.3 %, naming the foreign kind**, which is the control proving the union fix is not an amnesty; restoring the single-colour table makes the same correct figure fire again. **The four-way census is 13 px per wedge, ratio 1.000 — non-zero, so §R22.3's first branch is taken and the ceiling stands at four**, not lowered to three. **CP2.8's evidence is now in `tests/env/test_dashboard_frames.py`** under the `integration` marker (12 passed + 1 strict xfail), including one full-audit frame at **49.1 s**. Guard 10/10 + FRAMES PASS ×3, exit 0, before and after; `tests/env` **642 passed, 0 failed**.
  - *2026-09-17 developer, **finding D — the only thing still blocking CP2.8, and it is a constant question**.* The 9 remaining findings are all the matrix's **one real three-way square** `(8,6)`, on the 5 frames that hold it. Measured: a correct three-way loses **exactly one classified pixel** — `M1` agent **31/32** and predator **31/32** (0.9688), `M6` agent **17/18** (0.9444), synthetic **16/17** (0.9412) — while the hiding predator's two-paint mark measures **23/23 = 1.000**, so §R22.1's fix is working. **Cause, measured at the pixel:** the 0.8 px white line dividing two wedges is stroked by **both**, and compositing the same partially-covered pixel twice leaves it whiter than either pass alone — (104, 90, 221) composited against (98, 83, 220) isolated — carrying one pixel from 7/255 to 13/255 from its colour, just past `MINIMAP_DELTA`'s 12. **Under §R22.4's own test this is the Revision 21 case, not the (A)/(B)/(C) case:** a picture correct as drawn, misclassified by a number — and the number is `SURVIVAL_MIN = 0.98`, swept on ~330 px² arena tokens and reused **unswept** on a 13–32 px map wedge. **A 0.98 floor is only reachable at ≥ 50 classified pixels per wedge; no map wedge has that.** The gap is real and measured: **worst correct control 0.941, best mutation 0.833**. `MINIMAP_AREA_MIN` already exists because this map needs its own floor rather than `SURVIVAL_MIN` reused, but it is applied only on the geometric path. **Nothing was moved; the decision is `senior-developer`'s.** Two repairs were tried and rejected on measurement — round joins (changed nothing, reverted) and folding a square's wedges into one artist (would force 1.000 by construction, but would hide a draw-order defect *between* wedges, which is what M-F3 exists to catch). Pinned in CI as the measured 16/17 **plus a strict xfail**, so settling the floor turns the suite red rather than letting this note drift.
  - *2026-09-17 senior-developer, **finding D is DECIDED — the map gets its own floor, and the arena's is untouched** (Revision 23).* The reported gap was re-measured before being used, and measuring it properly changed it: **two of the three pre-registered minimap mutations (M-F3, M-F5) fire through the DISTINCTNESS check and never reach the ratio floor**, so "best mutation 0.833" was one point rather than a population. A **graded** family — the same defects made progressively shallower — brings the defect side up to **0.9167** (the identity pip pushed 80 % of the way to the square's centre, neutral 22/24), against a worst correct control of **0.9412** (16/17). **The real gap is (0.9167, 0.9412], 2.45 points wide, not 10.8.** `MINIMAP_SURVIVAL_MIN = 0.93` is placed **54.4 %** of the way up it — the same discipline and nearly the same fraction as §R21.2's 53.5 %. **It is a NEW constant, not a moved one:** §R20.4 already ruled the map must never reuse `SURVIVAL_MIN`, and that ruling had been applied to the geometric fallback (`MINIMAP_AREA_MIN`) while the census path silently inherited the arena's number — the reuse *is* the defect, so `SURVIVAL_MIN` stays at 0.98 and `MINIMAP_AREA_MIN` at 0.55. **The seam is not fixed in the painter, and that verdict is measured:** drawing the wedges edgeless removes the one-pixel loss but produces ratios **above 1.000** (23/22, 26/25) — a kind credited with pixels its own artist never drew, in the direction that conceals occlusion — because the white split line is what makes a blend classify as neither colour. **What CP2.8 still needs is §R23.1's seven code rows, §R23.2's re-registered four-member family, and the 18-frame matrix re-run**, which is predicted in advance to report **0 minimap findings on 18 of 18** (every remaining finding is `(n−1)/n` for `n` in 17–32, i.e. 0.941–0.969, all clearing 0.93); if any frame still fires, report the number rather than moving the floor again.
  - *2026-09-17 developer, **§R23.1 + §R23.2 implemented — CP2.8 CLOSES***. Full detail in the Implementation Report "§R23.1 / §R23.2: the World map's own survival floor, and CP2.8's last clause". **The pre-registered prediction held exactly: 0 findings on 18 of 18 frames** — `grep` finds no `minimap_*` and no `cell_*` finding anywhere in the re-run log, against 9 minimap findings on 5 frames before. What remains on those frames is `text_over_fill` (9–15/frame, pre-existing, a different rule) and `panel_absent: Olfaction` ×1 on M5's two frames, which §R22.9 assigns to **CP2.7**. **The floor was not moved a second time**, per §R23.1's *Fails if:*. **The reuse was removed rather than relocated:** the census path reads `MINIMAP_SURVIVAL_MIN = 0.93`, `SURVIVAL_MIN` stays **0.98** and `MINIMAP_AREA_MIN` **0.55**, and which floor a path uses is now a **lookup in `MINIMAP_FLOORS`** — so a path added later and left unregistered raises `KeyError` instead of silently inheriting the arena's number, with a test asserting the grid panel's constant is not so much as *named* inside `minimap_overdraw`. **The family is re-registered at four members, every one firing through the RATIO FLOOR** (M-F4a 20/24 = 0.8333, M-F4b 22/24 = **0.9167**, M-F3a 14/24 = 0.5833, M-F3b 18/24 = 0.7500), with the silent partners kept and measured (pip at 60 % / 40 % costs the neighbour **no** pixel). **One number in §R23.1's table did not reproduce, and it is reported rather than absorbed:** sweeping a second map square finds a worst correct control of **0.9375** (15/16) rather than 0.9412 (16/17) — the same one-pixel seam on a wedge one pixel smaller, and exactly the resolution limit §R23.1 states in advance. The gap is therefore **(0.9167, 0.9375]**, 2.08 points wide, with 0.93 sitting **64.0 %** up it rather than 54.4 %. Still a gap, every correct control silent, **constant unchanged**. **Cost, which CP2.8 asks be stated: 43.58 s mean per audited frame** (18 frames, 38.3–46.6 s, 656–755 elements, **uncontended**; the previous pass's same 18 frames averaged 45.02 s). Machine: container `docker-102`, Intel i9-7900X, 20 threads. **Tests:** `tests/env` **689 passed, 377 skipped, 0 failed**, and **no xfail remains** — the strict xfail that was registered to turn red on this day was deleted and its test now passes plainly. Guard **10/10 PASS + FRAMES PASS ×3, exit 0**, before and after.
- [ ] **CP3: Separate V2 entry point.** `render_recordings_v2.py --concat` writes playable MP4s (frame count = steps) for all cells including M7–M9, only under `videos_v2/`. The concat signature assertion holds on real runs and trips on the doctored dir. `test_render_recordings_v2.py` is green (V1 MP4 bytes unchanged after a V2 render of the same dir). CP-G passes. *Fails if:* any file appears or changes under `videos/`, the assertion trips on a real single-run dir, or CP-G fails.
  - *2026-09-17 developer:* **every clause met EXCEPT "including M7–M9", which is deliberately left unticked rather than waived.** Full detail in the Implementation Report "Phase 3 (CP3)". **Met:** M4 renders end to end and the videos play — `episode_000002.mp4` decodes to **75 frames for 75 recorded steps**, `episode_000001.mp4` to **24 for 24**, and `eval_M4.mp4` to **99 = 24 + 75**, each count read back by `ffprobe` **decoding the finished file** rather than taken from the writer. Output is **only** under `videos_v2/`; no `videos/` directory exists anywhere under `results/render_audit/`, and the test asserts V1's MP4 bytes are unchanged after a V2 render of the same directory (hash-for-hash, plus no file added or removed). **Determinism verified, not assumed:** the same recording rendered twice gives byte-identical MP4s, per episode *and* concatenated (`0468efdf…`, `4f3bd535…`, `31e676c6…` both times). `tests/scripts/test_render_recordings_v2.py` **8 passed**. CP-G **10/10 PASS + FRAMES PASS ×3, exit 0**, before and after. **Not met, and not mine to clear: M7/M8/M9 still cannot be rendered**, and the plan's own re-entry mechanism cannot clear them — the `AttributeError` is raised *inside* the frozen `sensor.py:577`, which `panels.py:184` calls, so `_recording_flag` (§D4.1) never gets the chance to apply. They now **fail loudly per recording** (full traceback, batch continues, exit 1) instead of aborting. **For `senior-developer`:** decide the mechanism (a params proxy at the package boundary, or a frozen-file edit deferred to the retirement gate) — see the report's deviation 1.
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
    - **Revision 17:** shared-square token colours and the minimap's split-dot wedges are classified against the same palette table — a split wedge may only carry its occupant's own token colour, and ~~the occupancy rim pip may not use the amber reserved for the hiding-predator identity pip~~ **(Revision 22: the rim pip is retired, so this clause becomes the stronger one it was approximating — `HIDE_EYE` amber may appear on the map ONLY as a hiding predator's identity pip, asserted by mutation M-F5, §R22.6)**. A square's dot may carry up to **four** wedges, each in its own kind's colour.
  - *Fails if:* any token is found outside its allowed panels above a small anti-aliasing tolerance (stated in the test), a second temperature legend exists, or the noise note is missing or disagrees with params.
- [ ] **CP-D: Design quality (Revision 6; before retirement; judged against the adopted spec `docs/reviews/design_episode_dashboard.md` since Revision 8).** `visual-design-reviewer` looks at rendered frames from M1, M4, E2 and E8 plus viewer screenshots, at full size. It writes its design spec and verdict to `docs/reviews/design_renderer_layout_redesign.md`. The developer applies the spec: typography, colour system, hierarchy, spacing, iconography, all against the house style sheet. The Implementation Report lists each spec item as applied or rejected-with-reason. A second `visual-design-reviewer` pass on re-rendered frames then passes the "big-tech presentation" bar. *Fails if:* no spec file exists, a spec item is unaccounted for, or the second pass does not pass. Any layout change the spec forces must still pass CP2.1–CP2.7 and CP-G.
- [ ] **CP6: Docs.** `12_renderer.md` (with the V2 disambiguation sentence), `ENVIRONMENT_SUMMARY.md` and `SCRIPTS_DEPENDENCY_MAP.md` are updated in the same commits as the code. *Fails if:* a script-adding commit lacks the map.
  - **Itemised by Revision 23 §R23.5, because one row of §R22.7 landed here rather than in the change that prompted it.** §R22.7 asked for the minimap's encoding paragraph in `12_renderer.md` in the same change as the painter; that document has **no dashboard section at all** — it describes only V1 and the dormant V2 — and `12_renderer.md:209` already documents **a different minimap** (V1's `imshow` with scatter dots and a cobalt viewport rectangle). A wedge paragraph dropped into it would most naturally be read as describing *that* map, so the work is deliberately deferred to this checkpoint rather than done as an orphan. **Required content, named so it cannot be rediscovered as an omission:** (1) the World map's `n = 1…4` wedge encoding; (2) the **retired rim pip**, and that nothing is drawn outside the dot; (3) the **four-kind ceiling** and `CELL_PRIORITY`'s guarantee that the agent is never dropped; (4) §R17.4's **on-page caption statement** and why a coded encoding needs one; (5) the map's **own survival floor** (`MINIMAP_SURVIVAL_MIN`, Revision 23) with its one-classified-pixel resolution limit. The **disambiguation sentence covers "minimap" as well as "V2"**, since the word now names two different pictures in two different renderers. *Fails if:* CP6 is ticked while `12_renderer.md` describes the World map's encoding incorrectly, describes only V1's minimap without saying so, or omits any of the five items.

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
- **Q9 (decided 2026-09-14; the `≤ 0.5 ×` half SUPERSEDED 2026-09-17 by the measured result, see Q22 and Revision 21 §R21.1): speed gate.** Median frame time on the campfire world ≤ half of V1's, and not slower than V1 on any other world; same lab node, frames and worker type. **The `≤ 0.5 ×` clause is retired**: measured at **0.563 ×** (V1 333.0 ms, V2 187.3 ms — 1.78× faster), with the arena that the gate was written to guard against costing only 11.2 ms of 187 ms (~6 %). The user accepted the gate as met in substance. **The "never slower than V1 anywhere" clause is NOT retired** — it is the absolute floor protecting training-time rendering, and CP4 still measures it on every cell.
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
- **Q18 (decided 2026-09-16): variant H — terrain bed + token.** Terrain is the square's ground cover, not a centred glyph; occupants stand on it in slots; nothing is drawn concentrically; corner pips, terrain folds and every other coded scheme are rejected on the principle that a viewer should recognise both occupants **by seeing them, not by decoding a legend**. Full rule in Revision 17 §R17.3. Not re-opened.
- **Q19 (decided 2026-09-16; ~~48 px~~ → superseded by Q20's answer, Revision 18): the arena square.** Originally recorded as **48 px**, with an accepted 1–2 px shortfall against variant H's measured legibility floors. **Superseded 2026-09-16 by Revision 18: the square is 50 px** (`ARENA_CELL_PX = ARENA_CELL_MIN_PX = 50`), which clears both floors (49 px for two movers, 50 px for the four-way), so the accepted cost no longer exists (§R18.3, §R18.4). The "up from today's 28 px" comparison in the original wording was wrong: 28 px is the *World map*'s square, not the grid view's, which is 96 px today — my error, corrected to the user before they answered Q20.
- **Q20 (decided 2026-09-16, Revision 18): the grid view shows the WHOLE world, at a 50 px square.** Asked because "a 48 px grid cell, up from today's 28 px" named two different panels' numbers. Given the corrected picture — the grid view's square is 96 px today, the World map's is ~28 px — the user chose: **the grid view draws the entire 10 × 10 world with 50 px squares** (centre card 564 × 564 px, right column 476 px against its 440 px minimum, sensor band 236 px against its 200 px minimum). There is **no 5×5 window**, so nothing pans and nothing centres on the agent. The World map keeps its ~23–29 px squares and the coded encoding of §R17.4. Arithmetic re-derived from Figure 3's own code in §R18.1; the consequences of removing the window are in §R18.2. Not re-opened.

- **Q22 (opened 2026-09-16 Revision 19; DECIDED by the user 2026-09-17): the speed gate counts as met in substance at 0.563 ×, and none of the four options is adopted.** The new renderer draws a frame in **187.3 ms** against the production renderer's **333.0 ms** — **1.78× faster** — while the pre-registered target was half the time (≈167 ms), so it misses by about **21 ms**. The three-arm split shows the big world-grid panel, whose four-fold growth was the entire reason Q22 was opened, costs **11.2 ms of 187 ms (~6 %)**; the text-heavy cards are the rest. The user chose to record that rather than block on 21 ms or re-author every painter in a second toolkit against the wrong 6 %. Q9's `≤ 0.5 ×` clause is superseded by this measurement; Q9's "never slower than V1" floor stands untouched. **CP0.4's lab-node measurement is still owed** and is folded into CP4, and the acceptance re-opens if CP4 shows V2 slower than V1 on any cell or the arena's share of the frame rises above ~25 %. Full reasoning and the arm table: Revision 21 §R21.1. Not re-opened.

- **Q21 (opened 2026-09-16 Revision 18; DECIDED by the user 2026-09-17): the World map STAYS, as a minimap.** Asked because the grid view now draws the whole world, so the small map shows the same extent as the panel beside it and its colour-coded encoding exists only to make that small copy readable at 18.40 px a square. **The user has confirmed it twice and asked that it stop being raised.** It is kept, at `LEFT_W = 320`, with the encoding of Revision 22 §R22.3 — one dot per square divided between up to four occupants. **The cost was stated before the answer and is accepted as part of it:** keeping the map bought the painter repair and the instrument repair of §R22.7 (the rim pip retired, the dot divided into `n` wedges, the identity pip moved into its owner's wedge, and the census's ground truth widened from one colour per kind to the set of colours a kind's own mark is drawn in), plus their controls. Dropping or repurposing the map would have dissolved all three defects in one edit — that branch is recorded in §R22.5 as **weighed and declined**, not as a standing option. **Not re-opened — not at CP-D, not anywhere.** Implemented 2026-09-17.

## Open questions for the user

> **Q21 is CLOSED (user decision, 2026-09-17): the World map stays, as a minimap.** It has moved to **Decided questions** above. What follows is the record of what was weighed, kept because the arithmetic is worth preserving — **it is not a live question, and the "drop"/"repurpose" branches are decided against.** Do not re-propose them.

**~~Q21 (opened 2026-09-16, Revision 18)~~: now that the grid view shows the whole world, does the small World map still earn its place in the left column?** The World map exists to give global context while the grid view shows a local patch. With the grid view drawing the entire world, the two panels show **the same extent** — the World map becomes a smaller, colour-coded copy of a picture already on screen, and §R17.4's coded encoding exists only to make that copy readable at ~18–29 px per square. *(Updated 2026-09-17: "split dots and rim pips" — the rim pip has since been retired and the dot is divided into up to four wedges, Revision 22 §R22.3. The measured square is **18.40 px**, at the low end of the range originally estimated.)*

- **Keeping it** ~~costs nothing that is not already spent~~ — **corrected 2026-09-17, Revision 22 §R22.5: that is true of LAYOUT and is no longer true of WORK.** The left column is still untouched by Revision 18 (Interoception 504 px + World map 220 px in 816 px available), but the map's coded encoding has since been built and measured, and it reports **2–4 defects per frame on frames that are correct**, from three separate causes. Keeping the map now buys a painter change (the rim pip retired, the dot divided into up to four wedges, the identity pip moved into its owner's wedge) and an instrument change (a kind's ground truth becomes a **set** of colours), plus their controls. **Dropping or repurposing the map dissolves all three defects at a stroke** and makes Revision 22 moot — the dissolution table is in §R22.5. It still differs from the grid view in one way — it is a compact, always-same-size picture, where the grid view carries the thermal field, the footprint outlines and the action badge.
- **Dropping it** frees ~236 px of left-column height, and would allow the left column to narrow, which is the only way to grow the grid square further. **The ceiling is 53 px per square regardless** (at 54 px the sensor band falls below its 200 px minimum), so the gain is at most 3 px per square — narrow the left column and the *band*, not the width, becomes binding. Stated so the option is not oversold.
- ~~**Recommendation, if one is wanted:** keep it for now and look at a rendered frame at Phase 2's CP-D, where "does this read as a duplicate?" is a question a picture answers and arithmetic does not.~~ **Superseded by the user's decision (2026-09-17): the map is kept, full stop.** This bullet is struck specifically because it deferred the question to CP-D, and the decision is not contingent on what a later reviewer thinks of the picture. CP-D may still say the map should *look* different; it may not re-ask whether it exists.
- **Phase 1's working assumption, recorded (Revision 19, #61): keep the World map, `LEFT_W = 320`.** Every pinned number in §R18.1 — the 564 px card, the 476 px right column, the 236 px band — rests on it. **The assumption turned out to be the decision:** the user answered *keep*, so all three numbers stand unchanged and nothing that was built on them has to move.
- **The gate was crossed before the answer arrived, and that is recorded rather than glossed (Revision 22 §R22.5).** Phase 2 built the minimap and the CP2.8 real-painter pass measured it while Q21 was still open. Nothing was broken by it — the working assumption held — and the answer has now closed the gap in the right direction: §R22.7's changes were implemented on 2026-09-17, on the branch the user chose. **There is no remaining conditionality here for a later phase to act on.**

> **Q22 is CLOSED (user decision, 2026-09-17): the gate is met in substance at 0.563 ×, and no option below is adopted.** It was asked, because the measurement landed in the `0.5× < median ≤ 1.0×` band. The decision and its evidence are in the **Decided questions** list above and in **Revision 21 §R21.1**; the table below is kept for the reasoning that produced the answer.

**Q22 (opened 2026-09-16, Revision 19; CONDITIONAL — asked only if CP0.4 misses; ~~open~~ **ANSWERED 2026-09-17**): how should the speed target be read now that the grid panel draws four times as much?** Q9 set the target at "median frame time on the campfire world ≤ half of V1's, and never slower than V1 anywhere". That was agreed when the panel drew a 5×5 window — 25 plain squares. The decided panel draws **100** squares, each with a ground, possibly a terrain bed, and up to four drawn tokens. The half-the-time target was a proxy for the *architecture* paying off (V1 rebuilds its whole figure every frame; the new one builds once and updates), and with four times the content on one side of the comparison and not the other, a miss no longer tells us whether the architecture failed or whether we are simply drawing more. **This question is not asked at all if CP0.4 meets 0.5×.** If it misses, the four options:

| | Option | What it costs |
|---|---|---|
| 1 | **Keep Q9 exactly as agreed.** 0.5× on the campfire world, never slower anywhere. | Nothing to renegotiate — but a miss caused by drawing four times as much would be read as the toolkit's failure, and the response on the table is re-authoring every painter in Pillow: the most expensive move in this plan, spent on the wrong cause. |
| 2 | **Keep 0.5×, but compare like with like.** Time the current renderer on the same 100 squares by giving the timing harness a params copy with `local_view_size` set to the world width (it is an ordinary env param, `default.yaml:354`; the benchmark already calls the old renderer read-only with params it builds, so no frozen file is touched). The ratio then measures architecture, as intended. Keep "never slower than the **production** renderer" as a separate absolute floor — that is the part protecting training-time rendering. | One extra benchmark arm, plus an honest caveat: no production video is ever rendered that way, so the arm is a synthetic reference and must be labelled one. **Unverified assumption:** that the old renderer draws correctly and meaningfully at a 10×10 local view. Worth a one-hour check before choosing this. |
| 3 | **Split the gate along the measurement.** Hold 0.5× against the **non-arena** part of the frame — the part the build-once architecture was supposed to fix — and give the arena its own absolute per-frame budget in ms, set from CP0.4's own measurement and pre-registered before Phase 2 starts. | The gate stops being one number the user agreed to, and an absolute budget only means something with a named machine. In exchange it is the only option that answers the question actually being asked ("is the architecture right?") and it cannot trigger a wrong pivot. |
| 4 | **Attack the cost instead of the target.** Replace Figure 3's per-name glyph pool (every entity name pre-built in every square — roughly 9 × 5 × 100 ≈ 4,500 artists) with a **per-slot pool** (4 slots × 100 squares, each slot a small reusable set re-pathed and re-coloured per step). Keep both Q9 numbers. If even that misses, Pillow (option B of §D2) becomes live. | A more complex painter, and a real risk of re-introducing the identity-by-draw-order bug this redesign exists to remove: a reused artist must be re-pathed *and* re-coloured every step and a stale slot hidden — exactly the class §R19.1's rule now checks, so at least the check would catch it. |

**My recommendation, for the user to accept or reject:** option 3 for the gate, with option 4 held in reserve, and option 2 only if the one-hour check says the old renderer is meaningful at a 10×10 view. Option 1 is the one I would avoid, because its failure mode is the costliest and the least deserved.

Everything else remains decided (see **Decided questions** above); Figure 3 settles any remaining layout detail, at the square size and view rule of Revision 18.

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
| `configs/environment/experiment/basic/06-campfire_thermal_10x10.yaml` *(renamed to `05-campfire_thermal_10x10.yaml` by Revision 14, 2026-09-16)* | **(4)** New header paragraph stating the world reproduces the archived campfire world **on the current bush rule** (bushes block animals), that this is the only differing field of 190, and that recordings here are not frame-comparable with anything from before 2026-09-14. |
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

### Phase 0c (CP0.3): the pixel-overlap audit, and its calibration

> **Implemented by**: developer
> **Date**: 2026-09-16
> **Scope**: `scripts/eval/render_layout_audit.py` + `tests/env/test_render_audit_controls.py` + one `SCRIPTS_DEPENDENCY_MAP.md` row pair. No frozen file, no `src/`, no `configs/`.

**What this phase is, in plain words.** The redesign's central promise is that panels will no longer be able to overlap — not "we nudged the labels until they stopped colliding", but "the layout makes collision impossible". Nobody can check that promise by looking at a picture and forming an opinion, so this phase builds the thing that measures it: a script that takes a real rendered video frame and reports, in pixels, where drawn content collides — text over text, text lying across a panel edge, a label drawn outside the panel it belongs to, content cut off at the edge of the image. The script is the instrument. An instrument nobody has calibrated is worthless, so it ships with **positive controls**: defects we already know are in today's videos, which it must find. If it cannot find a defect a human can point at, it is not sensitive enough to certify anything, and that is a stop-work condition rather than a reason to shorten the list of defects.

**Result: 7 of 7 controls fired**, including all five the brief pins as ground truth. One of the five turned out to be described incorrectly in this plan; that is written up below rather than quietly accommodated.

**Files.**

| File | Change |
|---|---|
| `scripts/eval/render_layout_audit.py` (new, ~620 lines) | The audit (§D5.2). Loads a fixture recording, builds each step's inputs the way `render_recordings.py::_render_episode` does, renders with the **frozen** V1 or dormant V2 renderer read-only, measures every artist's ink, and reports findings in the families `text_over_text` / `text_over_border` / `text_over_fill` / `out_of_card` / `clipped` / `out_of_canvas` / `panel_absent` / `observed_caption` / `legibility` / `numeric_in_arena`. `--controls` runs the CP0.3 controls and exits non-zero if any required one misses. Writes `audit.json` + `index.html` under `--out`. |
| `tests/env/test_render_audit_controls.py` (new, 18 tests) | Import-isolation test (the audit must not import the renderer package it audits); pure-helper unit tests; the five positive controls as `integration` cases that **skip with a reason** when the gitignored fixtures are absent; a check that V1 *does* draw the panel V2 drops (so D8 cannot pass because of a bug in the audit's own title table); and a **mutation control**. |
| `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` | §1c bare-import row for the test, §3 row for the script. **This file is MIXED** — see Blockers. |

**Collision definition and tolerances** (full statement in the script's module docstring, which is the authority):

- **Ink** is measured by **isolation**: `ink(E)` = pixels that change when *only* `E` is drawn over the bare background. A pixel counts at a per-channel difference **> 8/255**.
- A **collision** is a Text's ink, **dilated by 1 px**, sharing **≥ 2 px** with another foreground element's ink. Foreground/background is decided by artist **type and geometry** (the plan's 90% rule), never by a painter's tag.
- Sub-classes: partner is a Text → `text_over_text`; partner is an outline/hairline → `text_over_border` (forbidden outright); any other foreground → `text_over_fill` (reported separately, see false positives).
- `out_of_card`: a Text with ink in a card's **title strip** — the band between the card's top edge and its own title, which is one text line tall and belongs to the title alone.
- Canvas margin 4 px; legibility floor **off by default** (see Deviation 3).

**Control results, one by one** (frame = cell M4, episode 1, step 0, the fixture written by `make_render_fixture_recordings.py`):

| Control | Frame | Rule that fired | Elements | Measured |
|---|---|---|---|---|
| **D1** | V1 M4 | `text_over_text` | `'OBS:  0.00'` × `'THERMOCEPTION (OBS ONLY)'` | **59 px** at (1179, 357)–(1230, 359) |
| **D2** | V1 M4 | `out_of_card` | `'REAL: --'` × the card titled `'EXTERO NOCICEPTION (OBS ONLY)'` | **169 px** at (1183, 279)–(1228, 286) |
| **D3** | V1 M4 | `text_over_border` | `'MINIMAP'` × the Run Context card outline | **30 px** at (252, 644)–(295, 644) |
| **D6** | V2 M4 | `text_over_text` | `'COLLISION  (OBS ONLY)'` × `'C'`, and × `'U'` | **17 px** at (1117, 453); **25 px** at (1179, 453) |
| **D8** | V2 M4 | `panel_absent` | `Interoceptive Nociception` in the breakdown, no panel title with ink | — |
| *D10* | V1 M4 | `observed_caption` | `'OBS:  0.13'` × panel `'Nutrition'` (absent from the breakdown) | 4 captions, Nutrition + Injury |
| *D12* | V1 M4 | `panel_absent` | `Proprioception` emitted by the adapter, never drawn | — |

Coordinates are image pixels from the top-left. Both participants are checked, not just the finding count: `_control_matches` rejects the right rule on the wrong elements, and a test asserts that.

**What the plan got wrong about D2 — the one substantive correction.** §A2 classes D2 as **text-on-text** ("'REAL: --' floats over the EXTERO NOCICEPTION pod title"). Measured, it is not a text-on-text collision and never was:

- `'REAL: --'` occupies y 711.3–721.3; the title occupies y 722.8–732.8. They overlap horizontally by 47 px and are separated vertically by **1.5 px**. They share no pixel.
- This is **not** a consequence of cell M4's world changing (bush rule, Revision 14 re-level). I re-rendered the **archived campfire world** with the exact recipe that produced the original evidence frame (`figures/v1_thermal.png`: `PRNGKey(3)`, actions RIGHT DOWN RIGHT DOWN REST) and got **byte-identical bounding boxes** for both texts. The gap is structural: the label sits at `bar_y + bar_h + label_dy` and the title at `frame_bottom + pod_h + 0.015`, a constant 0.015 axes-fraction apart **independent of the squeeze factor**, so no world can close it.
- The defect is nonetheless **real**: the label is drawn *outside the card* whose bar it labels, in that card's title strip, where it reads as part of the title line. That is the "content outside its allotted box" family, and it is what `out_of_card` detects.

Consequence: §A2's D2 row and the Context bullet should be re-worded from "text-on-text" to an out-of-box/escaped-label defect. **Owner: `senior-developer`** — I did not edit the analysis section.

**False-positive behaviour.** The honest answer first: **there is no defect-free V1 or V2 frame to measure a clean false-positive rate against.** V1's defects are systemic, so "a frame with no known defect" does not exist in this renderer. The measurement is therefore per class, on three frames:

| Frame | Total | `text_over_text` | `text_over_border` | `out_of_card` | `text_over_fill` | `panel_absent` | `observed_caption` | `clipped` / `out_of_canvas` / `numeric_in_arena` |
|---|---|---|---|---|---|---|---|---|
| V1 M1 (default world) | 12 | 4 | 2 | 1 | 0 | 1 | 4 | 0 |
| V1 M4 (campfire) | 16 | 1 | 3 | 1 | 6 | 1 | 4 | 0 |
| V2 M4 (dormant) | 11 | 2 | 0 | 0 | 5 | 2 | 2 | 0 |

- **Hard classes (`text_over_text`, `text_over_border`, `out_of_card`, `panel_absent`, `observed_caption`): every single finding traces to a numbered defect.** On M1 that is D5 (three separate `OBS:`/`REAL:` row collisions — the audit rediscovered D5 unprompted on the default world, which is exactly where §A2 says it lives), D3, D2, D12, D10 ×4, plus the extero `OBS:` readout lying on the Collision card's border, which is the same escape that produces D1 on M4. Zero unexplained hits in these classes across all three frames.
- **`text_over_fill` is the one benign class**, and it is why it is reported separately and is not a control. All 11 instances are text drawn deliberately inside its own widget: the thermoception diamond prints each cell's reading inside that cell's coloured patch (8 of 11), the body-temperature gauge prints its value inside the bar with a white halo — `renderer.py` documents that choice explicitly — and a rotated `GRS` channel label sits over its own bar. Judging these "by design" is my reading of the frozen source, not a measurement.
- **Nothing flags everywhere**: 11–16 findings per frame out of 54–103 text elements and 147–305 drawn elements, and three rules stayed silent on every frame.
- One marginal hit worth naming: `'GRS'` × a card outline on V1 M4 at **4 px**, just over the 2 px floor. Real but minor, and previously unnumbered.

**Tests.** `JAX_PLATFORMS=cpu pytest tests/env/test_render_audit_controls.py -q` → **18 passed in 71 s**, exit 0.

The mutation control is the one that matters: with `MIN_OVERLAP_PX` raised to 10⁹, `text_over_text`, `text_over_border` and `out_of_card` must all disappear while `panel_absent` — which does not depend on pixel overlap — must survive. It does. That is what distinguishes a measurement from a constant that always says "yes".

**Bugs found in the instrument by running it, and fixed** (each was caught by the control set or the full-frame reports, not by reading the code):

1. **Border-vs-fill was decided from the declared face colour.** V1's cards are `Rectangle`s filled in the *background* colour, so an alpha test called them solid while the canvas shows only their edge. D3 was reported as `text_over_fill` instead of `text_over_border` — right frame, wrong collision, which counts as not firing. Now decided from measured ink: an element whose ink lies on the perimeter of its own bbox is an outline.
2. **The title-strip rule invented a 65 px strip** in the left column, because a card whose own title is not in the title table (V1's "RUN CONTEXT") adopted the nearest matching text far above it — 4 false positives. Bounded to one title line.
3. **`panel_absent: Body Temperature` on V1 M4 was wrong** — the gauge *is* drawn, labelled `BODY TEMP   DIE -15 / +15`. An exact-match title table reported a drawn panel as dropped, which is the one verdict this rule exists to give. Now longest-prefix matched.
4. **Caption attribution used horizontal proximity**, so a vitals row's right-aligned value was blamed on another panel. Now attributed by column (the axes) and vertical order.
5. **Text-text collisions were double-counted** (once from each side).

**Deviations from the plan, and why.**

1. **Ink is measured by ISOLATION, not by hiding the element** (§D5.2 item 2 says hide-and-diff). Hide-and-diff has a blind spot on exactly the case the audit exists to find: where text is drawn opaquely over a card border, hiding the border changes no pixel, so the border's "ink" excludes the overlapped region and the collision reports clean. The plan's intent (pixels, not tags) is preserved and strengthened. Cost: one render per element rather than per element, same order.
2. **Added an `out_of_card` rule**, which the plan's ten rules do not contain. Needed because V1 draws a whole column into **one** Axes, so the plan's "content outside its allotted box" is vacuous at axes level — the *card* is the box. This is what detects D2. The new renderer, with one clipped axes per panel, will satisfy the axes-level form as well.
3. **The legibility floor defaults to OFF.** The plan says V1 control frames are judged at the old 8 pt floor, but V1 draws most labels at 4–7 pt, so that floor emits ~40 findings per frame on a frozen renderer nobody will fix — noise that buries the defects. The rule is implemented and enabled with `--text-floor-px` (the redesign's floors are 14 px / 12 px).
4. **Added D10 and D12 as controls.** CP0.3 names both; they were free calibration.
5. **Not implemented in this phase** (all belong to later checkpoints, none is a CP0.3 gate): the vocabulary rule (§D5.2 item 8 — V1/V2 are exempt anyway), mutations M-A…M-D (CP2.2), the value-to-pixel checks (CP2.3), obstacle ink (CP2.6), per-finding crop images in the contact sheet (only `index.html` + `audit.json` are written), and the headless-Chrome pass (CP5).
6. **Two rules are implemented but not exercised**, stated rather than left to be discovered: `numeric_in_arena` is not wired to the CLI (it needs a named arena axes, which V1 does not label and the new renderer will), and the clip-path half of the `clipped` rule never fires because neither V1 nor V2 sets a clip path on text — only the canvas-edge half is exercised.

**Prior-art check (done, not skipped).** `grep -i` over `docs/develop/active/issues/KNOWN_BUGS.md`: the dashboard-collision family is already registered — one row covers **D1–D9, D11, D12**, a second covers **D10**, and a third covers the live renderer's shared icon cache / dead figure cache / `DNG` label. Nothing I measured contradicts those rows. Two items a curator may want: D2's class is wrong in this plan (a doc fact, not a new bug), and **D5 is confirmed reproducible on the default world today** with pixel evidence. **Owner: `bug-curator`** — sub-agents cannot spawn it.

**Runtime** (container, i9-7900X, CPU): single V1 M4 frame audit **22 s**, single V2 M4 frame **13 s**, full 7-control run **33 s**. This is a phase-boundary cost on a hand-run tool, not a training cost.

**Speed check: skipped, and the skip is justified rather than assumed.** Nothing in this phase is on the hot path or on any training path: two new files that are hand-run/test-only, plus two documentation rows. No environment step, model, loss, observation-pipeline or renderer code was touched. The strongest evidence is independent of my judgement — the guard's raw-frame hashes for M1, M2 and M4 are unchanged, so V1's rendered output is bit-identical to before this phase.

**CP-G (V1 pipeline untouched).** `v1_path_guard.py check` run **before** and **after**: both `PASS=10, ACCEPTED=0, ATTRIBUTED=0, UNATTRIBUTABLE=0` with `FRAMES PASS` on M1, M2, M4 and `RESULT: OK`, exit 0. `git status` over the ten frozen paths is empty. `accept` was never run. The audit imports the frozen renderers and executes them read-only; it patches `matplotlib.pyplot.figure`/`close` for the duration of a render only, so the Figure survives the renderer's own `plt.close`, and it **proves the captured figure redraws byte-identically to the returned frame before taking any measurement** — if it did not, every finding would describe a different picture from the one under audit.

**Blockers and follow-ups.**

1. **`docs/environment/SCRIPTS_DEPENDENCY_MAP.md` is a MIXED FILE.** Its working-tree diff already carried another session's `recovery_in_bush_tuning` `f01…f05` → `f02…f06` renumbering before I touched it. I added my two rows and **staged and committed nothing**. Whoever commits must check hunks and use an explicit pathspec.
2. **Plan correction owed** for D2's classification (owner `senior-developer`), per above.
3. **Nothing staged, nothing committed**; working tree left dirty for verification. `docs/develop/INDEX.md` and `SAVED_RUN_CONFIG_COMPAT.md` remain staged by another session and were not touched.
4. M7/M8/M9 remain blocked at current code (Revision 13); this phase neither depends on them nor changes that.

*Implemented by: developer*

### Phase 0c fix pass (2026-09-16), after the senior-developer verification and the code review

**What this pass is, in plain words.** Phase 0c built the instrument this redesign will be judged by — a script that measures, in pixels, where a rendered video frame's content collides. Verification passed it, but a code review then found a hole that matters more than anything in the original report: **the test suite could not tell the instrument apart from one that flags everything.** If the function that measures "which pixels did this element put on the canvas" had simply answered "all of them", every one of the 18 tests would still have passed and all seven known defects would still have been "found" — because a test that asks *did it find the defect* can only ever measure sensitivity, never discrimination. A smoke alarm that is always sounding detects every fire. This pass adds the tests that a permanently-sounding alarm fails, fixes three bugs in the instrument that were fixed but never tested, corrects one class of finding that was wrongly described as harmless, and pins *where* in the frame each known defect is, not merely that it was reported.

**Headline result.** The instrument is unchanged in what it reports on real frames — the same seven controls fire on the same rules, the same elements and the same coordinates as before. What changed is that it can now be *falsified*: under a deliberately broken measurement that claims every pixel for every element, **10 tests fail** where previously **none** did.

**1. Negative controls — the important one.** Four kinds of "what must NOT be reported" are now pinned:

- **The exact set of silently-dropped panels on V1 M4** is `{"Proprioception"}` — not "Proprioception is somewhere in the set". The test additionally asserts that Body Temperature, Interoceptive Nociception and Thermoception are in the world's observation breakdown *and* are not reported absent, which pins instrument bug 3 (below) at frame level rather than only at unit level.
- **Exact per-rule finding counts on two frozen frames** (V1 M4 and V1 M1), as equality against a dict, not as lower bounds. They are exact on purpose: V1 is a frozen file and the fixtures are pinned by the guard's raw-frame hashes, so any movement is either a change to a frozen renderer or a change in the instrument, and both must be seen rather than absorbed.
- **The rules that must stay SILENT** on those frames (`clipped`, `out_of_canvas`, `legibility`, `numeric_in_arena`, and `fill_over_text` on M1). An instrument that flags everything cannot keep any of them quiet.
- **Coordinates** (item 4 below), which turn out to catch the flag-everything mutation too, since a whole-canvas overlap has a whole-canvas bounding box.

**The proof, run rather than asserted.** `FrameProbe.ink()` was replaced with one returning an all-True mask (scratch pytest plugin, `tmp/20260916_173000_mutation/mutate_ink.py`) and the suite re-run. **10 failed, 28 passed** (against **0 failed** for the original suite):

| Test that fails under a flag-everything `ink()` | What it catches |
|---|---|
| `test_positive_control_hits_at_the_pinned_coordinates[D1]` | overlap bbox becomes the whole canvas |
| `test_positive_control_hits_at_the_pinned_coordinates[D2]` | 〃 |
| `test_positive_control_hits_at_the_pinned_coordinates[D3]` | 〃 |
| `test_positive_control_hits_at_the_pinned_coordinates[D6]` | 〃 |
| `test_positive_control_hits_at_the_pinned_coordinates[D10]` | 〃 |
| `test_v1_m4_finding_counts_are_pinned` | hard-class counts explode; `out_of_card` collapses to 0 (no element's ink is an outline any more, so no card is recognised) |
| `test_v1_m1_finding_counts_are_pinned` | 〃 |
| `test_v1_m1_reproduces_d5_in_the_vitals_column` | D5's three collisions stop being three, and stop being in the vitals column |
| `test_v1_m4_out_of_card_flags_only_the_escaped_readout` | the single escaped-label finding disappears |
| `test_fill_class_splits_the_thermal_scale_label_from_the_in_widget_labels` | the benign/covered split collapses |

**Stated honestly, two things this mutation does *not* break.** `test_positive_control_fires` still passes for all seven — which is the point: controls measure sensitivity, and a flag-everything instrument is maximally sensitive. And `test_v1_m4_absent_panels_are_exactly_proprioception` also still passes, because `panel_absent` asks only whether a title has *any* ink and all-True gives every title ink; that test is a negative control against a **different** failure — a broken title table, i.e. instrument bug 3 — which is what it was asked for. An in-suite mutation test (`test_an_ink_that_flags_everything_breaks_the_calibrated_counts`) now encodes this permanently so the property is not re-lost.

**2. The three untested instrument bugs now have regression tests.**

| Bug | Was | Now covered by |
|---|---|---|
| **#2** the title-strip rule invented a 65 px band (a card whose own title is not in the title table adopted a distant one — 4 false findings) | fixed, untested | `test_title_strip_is_bounded_to_one_title_line` (unit, no render: a title 65 px above a card yields **no** strip; one line above yields a strip ≤ 4 rows tall) **and** `test_v1_m4_out_of_card_flags_only_the_escaped_readout` (frame level: exactly one finding, and never `RUN CONTEXT` / `MINIMAP` / `10x10`) |
| **#4** caption attribution used horizontal proximity | fixed, exercised only by D10, which was **missing from the parametrised control list** | D10 added — the list is now parametrised over `list(audit.CONTROLS)`, so a control can never again be added and left untested — plus `test_owning_title_attributes_by_column_not_by_x_proximity` (unit: the caption's own title does not overlap it in x, a foreign column's does, and the own-column title must win) |
| **#5** text-text collisions double-counted, once from each side | fixed, untested | `test_text_collisions_are_not_double_counted` on M1 (the frame with the most text-text collisions), plus the exact count pin (4, not 8) |
| **#3** `BODY TEMP   DIE -15 / +15` reported as a dropped panel | pinned at unit level only; the integration test never asserted Body Temperature was present | now asserted in `test_v1_m4_absent_panels_are_exactly_proprioception` |

**3. `'+84'` — the verdict: a real, previously unnumbered layout defect, not an artefact of the rule.** The verification found that five of the six `text_over_fill` instances on V1 M4 are text inside its own widget, but `'+84'` is text outside one, with 3 % ink overlap and the widget z-ordered above. Investigated properly:

- `'+84'` is the **maximum-value label of the thermal scale strip** under the arena (`renderer.py:777`). Its partner is the **52nd and last segment of the colour strip** (`renderer.py:769-772`).
- The cause is arithmetic, not chance. The strip is drawn as 52 segments each `strip_w/51 + 0.002` wide — the `+0.002` being a deliberate bleed so no hairline gap shows between segments. That bleed applies to the last segment too, so the strip ends at axes-fraction **0.77220** while the label is anchored at **0.77000** with `ha='left'`. The segment is `zorder=5`, the label `zorder=3`.
- **It is therefore structural and world-independent**: both numbers are constants, so on every thermal frame ever rendered the first ~2 px column of the `+` glyph is painted over by the dark-red end of the colour bar. Confirmed in the composite: at both shared pixels the final frame is `[103 0 31]` — the segment's colour exactly, 157 and 243 away from what the glyph alone would show.
- Small (2 px of a 70 px glyph) but real: the reader sees a clipped `+`. Same family as the `'GRS'` × card-outline 4 px hit named in the original report.

**Recorded, not numbered: owner `senior-developer`.** It belongs in §A2 alongside D1–D12; the plan is yours, so I have not assigned it a number. **Prior art checked** (`grep -i` over `docs/develop/active/issues/KNOWN_BUGS.md`): nothing on the thermal scale strip, colour bar or this collision. The dashboard row covers D1–D9, D11, D12 and does not include it — **owner `bug-curator`** to extend that row once the defect has a number (sub-agents cannot spawn it).

**And `text_over_fill` has stopped being reported as uniformly benign.** It is split into two measured classes: `text_over_fill` (the label is composed last, so the frame shows the glyph — legible by design) and **`fill_over_text`** (the partner is composed after the label and covers its raw ink — a defect whatever the intent). On V1 M4 that is **5 benign + 1 defect**, replacing the old blanket "6, all by design"; on V2 M4, 5 benign + 0.

**How that split is decided, and the two candidates that were measured and rejected.** This mattered more than expected, because the obvious pixel tests are wrong:

| Discriminator | body-temp readout | 4 thermoception readings | V2 `GRS` | `'+84'` | |
|---|---|---|---|---|---|
| (A) hide the text, call unchanged pixels "lost" | **DEFECT, 29 px** ✗ | benign | benign | DEFECT | false-positives on a white halo over a `#F3F4F6` card |
| (B) solo render vs text+partner | benign | **DEFECT, 33-43 px** ✗ | **DEFECT** ✗ | DEFECT | false-positives on every anti-aliased glyph edge |
| **(C) composition order + shared raw ink** | benign ✓ | benign ✓ | benign ✓ | **DEFECT** ✓ | kept |

Anti-aliasing defeats (A) and (B): a glyph's fringe pixels are mostly background by construction, so any colour test on them measures the blend, not the occlusion. Containment fails too — V2's `GRS` label lies half outside its own bar (54 % of its ink on it) and is perfectly legible. (C) is not the classification-by-declaration that §D5.2 item 1 forbids: no painter is asked which of its own ink to ignore; this is the order matplotlib composed the image in, and it was checked against the pixels at the decisive solid-ink pixels of all eleven collisions. It is also the cheapest — it adds no extra render, where (A) and (B) each cost one per text.

**4. Coordinates are pinned.** Every control hit is now asserted at its measured position: rule, both participants, overlap in pixels **and** bounding box, tolerance ±2 px on each coordinate and ±20 % on the pixel count. The frames are byte-pinned by the guard on this machine so the honest tolerance is zero; the couple of pixels are allowed only for freetype hinting on another machine, and are far tighter than any relocation (a collision that moved to a different element moves by tens to hundreds of pixels).

**5. Small items.**

- **D2's `text_over_border` alternative removed** — it was *unreachable*, not lenient: a border finding names its partner `patch Rectangle in axes@NNNN` (the axes' name), so `b_contains: "EXTERO NOCICEPTION"` could never match one. `text_over_text` stays, because that is the class the defect would take if the renderer's 1.55 px gap ever closed. A test pins both facts, and the stale comment claiming D2 "collides with a BORDER" is corrected to match Revision 15.
- **The `clipped` docstring corrected rather than the rule implemented — decided by measurement.** Of 103 texts on V1 M4 and 54 on V2 M4, **zero** have a clip path or a clip box set (49 and 10 carry the `clip_on` flag, which here clips against nothing). The clip-path half would be an extra render per text to execute a branch no fixture can enter. The docstring now says so and says when it gets written: the phase that introduces painters which actually clip.
- **`numeric_in_arena` is now reachable**, via `--arena-axes NAME`, and is *exercised* rather than merely wired: V1 draws its arena into an unlabelled Axes so the rule cannot run on V1 at all, but the dormant V2 names its axes, so a test points the rule at a V2 axes known to contain numeric text and asserts all 5 findings — and asserts it stays silent with no `--arena-axes`, since the arena cannot be guessed.
- **`REQUIRED_CONTROLS` removed** along with the test that asserted it; a replacement test asserts the name is *gone* and that `CONTROLS` is the full set of seven. `main()` already failed on any miss, so the constant advertised D10/D12 as optional when CP0.3 names them too.

**Final control table — unchanged by this pass, which is the point.**

| Control | Frame | Rule | Elements | Measured |
|---|---|---|---|---|
| **D1** | V1 M4 | `text_over_text` | `'OBS:  0.00'` × `'THERMOCEPTION (OBS ONLY)'` | **59 px** at (1179, 357)–(1230, 359) |
| **D2** | V1 M4 | `out_of_card` | `'REAL: --'` × card titled `'EXTERO NOCICEPTION (OBS ONLY)'` | **169 px** at (1183, 279)–(1228, 286) |
| **D3** | V1 M4 | `text_over_border` | `'MINIMAP'` × the Run Context card outline | **30 px** at (252, 644)–(295, 644) |
| **D6** | V2 M4 | `text_over_text` | `'COLLISION  (OBS ONLY)'` × `'C'`, and × `'U'` | **17 px** at (1117, 453); **25 px** at (1179, 453) |
| **D8** | V2 M4 | `panel_absent` | `Interoceptive Nociception` | — |
| **D10** | V1 M4 | `observed_caption` | `'OBS:  0.13'` × panel `'Nutrition'` | at (316, 292)–(365, 298) |
| **D12** | V1 M4 | `panel_absent` | `Proprioception` | — |

**Frame totals after the fill split** (the only change to the false-positive table): V1 M4 is now `text_over_border` 3, `text_over_fill` **5**, `fill_over_text` **1**, `text_over_text` 1, `out_of_card` 1, `panel_absent` 1, `observed_caption` 4 — 16 findings, as before. V1 M1 and V2 M4 are unchanged in total (12 and 11).

**Tests.** `JAX_PLATFORMS=cpu pytest tests/env/test_render_audit_controls.py -q` → **38 passed in 110 s**, exit 0 (was 18 passed in 71 s). `render_layout_audit.py --controls` → **7/7 fired**, exit 0.

**CP-G (V1 pipeline untouched).** `v1_path_guard.py check` after the pass: `PASS=10, ACCEPTED=0, ATTRIBUTED=0, UNATTRIBUTABLE=0`, `FRAMES PASS` on M1, M2 and M4, `RESULT: OK`, exit 0. `git status` over the ten frozen paths is empty. `accept` was never run.

**Speed check: skipped, and the skip is corroborated rather than asserted.** Both files are hand-run/test-only and off every training path; no environment step, model, loss, observation-pipeline or renderer code was touched. The independent evidence is the guard's raw-frame hashes for M1, M2 and M4, which are unchanged — V1's rendered output is bit-identical to before this pass. Tool runtime is unchanged in kind (the kept fill discriminator adds no render); the suite grew 71 s → 110 s because it now renders two more frames (the M1 fixture and the V2 arena-rule case) and runs the ink mutation.

**Files.**

| File | Change |
|---|---|
| `scripts/eval/render_layout_audit.py` | `fill_over_text` class + `_is_painted_over` / `_draw_index`; D2's dead rule removed and its stale comment corrected; `REQUIRED_CONTROLS` removed; `--arena-axes` added and wired; docstring corrected on the fill classes, the `clipped` rule's scope and the arena rule, and gained the "sensitivity is only half of calibration" statement |
| `tests/env/test_render_audit_controls.py` | 18 → 38 tests: negative controls, coordinate pins, regressions for instrument bugs 2/4/5 and 3-at-frame-level, the fill-split test, the arena-rule test, the flag-everything mutation |
| `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` | the §3 row's "any of the five required ones" corrected to any of the seven, and `--arena-axes` documented. Already listed in Phase 0c's File Changes; the file is otherwise clean of other sessions' work as of this pass |
| `RENDERER_LAYOUT_REDESIGN.md` | this report + the CP0.3 checkpoint note |

**Hand-offs.**

1. **`senior-developer`** — give the `'+84'` collision a defect number in §A2 (structural, every thermal frame; evidence above), and note that §A2's D5/false-positive discussion now reads 5 benign + 1 covered rather than "all 11 by design".
2. **`bug-curator`** — extend the dashboard row in `KNOWN_BUGS.md` once that number exists; nothing there covers it today.
3. Nothing staged, nothing committed; working tree left dirty for verification.

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
| `configs/environment/experiment/basic/06-campfire_thermal_10x10.yaml` *(renamed to `05-campfire_thermal_10x10.yaml` and re-parented onto `04-jump_attack_10x10` by Revision 14, 2026-09-16 — **the measurements in this row describe the world as it was on the `extends: environment/default` parent**, and 37 of the 190 fields below have moved since)* | new, 112 lines (untracked) | ✅ | Loads through the resolving loader. **The "identical 33-dim observation" claim is confirmed**: the observation breakdown is character-for-character the archived world's — Satiation 1, Body Temperature 1, Interoceptive Nociception 1, Extero Nociception 1, Thermoception 5, Olfaction 5, Collision 5, Proprioception 6, Visual 8 = 33. Of **190** `EnvParams` fields, exactly **one** differs (below). `extends` chain is two files, neither under `archive/` — CP0.2's "no archived path is a runtime input" passes. |
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

### Phase 0c (CP0.3): the pixel-overlap audit, and its calibration

> **Verified by**: senior-developer
> **Date**: 2026-09-16
> **Verdict**: **VERIFIED WITH ISSUES.** The instrument is calibrated and its key threshold is principled, not tuned. Every measurement the developer reported was independently reproduced, to the pixel. The issues are two overstated claims in the write-up and one small unexamined finding; none blocks the Phase 0c commit.

**What was checked, in plain words.** This phase built the tool the whole redesign will be judged by: a script that takes a real rendered video frame and reports, in pixels, where drawn content collides — labels on top of each other, a label lying across a panel's edge, a label escaping the panel it belongs to, a panel silently missing. A tool like this is only worth anything if someone has checked that it can actually find defects a human can point at, and — just as important — that it is not finding them because a number was quietly chosen to make it do so. That second worry is the one this verification was built around, and it is the reason nothing below is taken from the developer's report: every figure was re-measured from the system's own output.

**The headline: the threshold is principled, and the hard-stop condition does not apply.** The rule that catches defect D2 (a readout drawn outside its own panel, in the strip that belongs to the panel's title) needs to know how tall that strip is. The audit bounds it at "one title line", expressed as a factor of **2.0** times the title's own height. The developer stated this factor was chosen, and that it is the only reason D2 is detectable — which raises the obvious worry that 2.0 was picked *because* D2 would otherwise be missed. **Swept, it was not.** The panel that produces D2 has a physically measured strip-to-title-height ratio of **0.955**, so D2 fires at any factor at or above that. The next panel in the frame that could produce a *false* finding sits at ratio **7.820**, and the sweep confirms the first spurious findings appear only between factor 6 and 10. The clean band is therefore **0.955 ≤ factor < 7.820 — a range of 8.2×**, with 2.0 sitting near its centre (the geometric midpoint is 2.73). A factor anywhere from 1.0 to 7.8 gives byte-identical results on this frame. That is a wide, physically meaningful range, not a narrow window around a tuned value. Two further points in its favour: the bound is expressed in units of the title's own ink height, so it tracks the font rather than being a pixel count picked by hand; and the lower edge of the band is not a tolerance at all but the actual geometry of the defect.

| factor | `out_of_card` findings | D2 fires | spurious findings |
|---|---|---|---|
| 0.50, 0.80 | 0 | no | — |
| **1.00 … 6.00** (incl. the shipped **2.00**) | **1** | **YES** | **none** |
| 10.00 | 3 | yes | `RUN CONTEXT`, `+0.00 real +0.00` |
| unbounded | 7 | yes | 6, incl. `MINIMAP`, `10x10` |

| File | Change | Status | Notes |
|------|--------|:------:|-------|
| `scripts/eval/render_layout_audit.py` | new, 1034 lines (untracked) | ✅ | Imports neither a layout module nor a registry. Classifies foreground/background by artist type and geometry, never by `gid` — verified by reading `enumerate_elements`. Border-vs-fill decided from measured ink, which is what makes D3 report as `text_over_border` rather than `text_over_fill`. Proves the captured figure redraws byte-identically to the returned frame **before** measuring (`FrameProbe.__init__`), and pins the layout engine to `none` so hiding an artist cannot re-solve the layout. |
| `tests/env/test_render_audit_controls.py` | new, 183 lines (untracked) | ✅ | Re-run by the verifier: **18 passed in 74.7 s**, exit 0. The mutation control is real: with `MIN_OVERLAP_PX` at 10⁹ the three pixel rules go silent while `panel_absent` survives. |
| `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` | +2 / −0 | ✅ | §1c bare-import row and §3 row, both accurate. **The developer's "MIXED FILE" blocker has cleared** — the other session's figure renumbering has since been committed, and the working-tree diff is now exactly these two added rows and nothing else. Still commit with an explicit pathspec. |
| `RENDERER_LAYOUT_REDESIGN.md` | Revision 15 + §A2 + §D5.2 + this report | ✅ | Written by the verifier, as the developer correctly flagged was owed. |

**Independent evidence — every number below was re-measured, not read from the report.**

| What was re-derived | Result |
|---|---|
| All seven controls, re-run by the verifier | **7/7 FIRED**, exit 0. Rules, element pairs, pixel counts and coordinates reproduce the developer's table **exactly**: D1 `text_over_text` 59 px at (1179, 357); D2 `out_of_card` 169 px at (1183, 279); D3 `text_over_border` 30 px at (252, 644); D6 `text_over_text` 17 px and 25 px at y 453; D8/D12 `panel_absent`; D10 `observed_caption`. |
| "Each control fires on the right elements" | **Confirmed, and it is structural rather than incidental.** `run_controls` counts a control as fired only through `_control_matches`, which requires the rule *and* both named participants; a right-rule/wrong-element hit yields `fired: False`. `test_control_matcher_rejects_the_right_rule_on_the_wrong_elements` asserts both rejection paths. |
| D2 is not text-on-text | **Confirmed.** `'REAL: --'` occupies y 711.27–721.27, the title y 722.82–732.82 — a **1.55 px** gap, **0 shared pixels** both raw and after the 1 px dilation. Independently, only one finding in the whole frame pairs `REAL:` with `EXTERO NOCICEPTION`, and it is `out_of_card`. |
| That this is not an artefact of M4's world changing | **Confirmed by a stronger route than the developer's.** Rather than re-render the archived world, the verifier re-derived the geometry from the frozen source: the readout anchors at `y_frame_bottom + (0.02+0.07+0.02)·squeeze` and the card top at `y_frame_bottom + 0.11·squeeze` — **algebraically equal at every squeeze factor** — with the title a constant 0.015 above. No world and no squeeze can close the gap or move the label inside the card. |
| D5 on the default world | **Confirmed.** Cell M1 step 0: three `OBS:` × `REAL:` collisions at **17, 17 and 16 px**, x 317–364, y 274 / 351 / 428 — the left vitals column, exactly where §A2 places D5. |
| The three-frame false-positive table | **Reproduced exactly**: V1 M1 12 findings (4/2/1/0/1/4), V1 M4 16 (1/3/1/6/1/4), V2 M4 11 (2/0/0/5/2/2). |
| `v1_path_guard.py check`, run by the verifier | `PASS=10, ACCEPTED=0, ATTRIBUTED=0, UNATTRIBUTABLE=0`; `FRAMES PASS` on M1, M2, M4; **exit 0**. `git status` over the ten frozen paths is empty; frozen-file diff stat against plan start is empty; no commit since plan start touches a frozen file. |
| Commit state | Both new files **untracked**; nothing from Phase 0c staged or committed. The only staged paths are `docs/develop/INDEX.md` and `SAVED_RUN_CONFIG_COMPAT.md`, both another session's. |

**Issues (none blocks the commit).**

1. **The §D5.2 deviation is right, but its stated reason overstates what was measured.** The report and the script's module docstring both claim hide-and-diff is *blind* to text drawn opaquely on a border — that "the collision reports clean". Tested directly: across the **10 collisions** the audit reports on V1 M4, hide-and-diff would have detected **all 10**, at 70–100% of the isolation figure; **no control would have been missed**. Constructing the worst case deliberately (an opaque haloed label over a border, the halo pattern `renderer.py` itself uses) the collision falls from **298 px to 8 px** — a 37× collapse that still clears the 2 px floor. So the true finding is that hide-and-diff is *systematically under-sensitive by a large factor whose size depends on paint order*, not that it produces a false pass. **The deviation is nonetheless justified and the plan is what should change** — a rule whose sensitivity depends on z-order cannot be reasoned about as the renderer changes. §D5.2 item 2 has been rewritten accordingly, with the measured numbers rather than the original argument.
2. **One of the `text_over_fill` findings is not benign, and the blanket characterisation is wrong for it.** The developer judged all 11 instances "text drawn deliberately inside its own widget", flagging honestly that this was a reading of the source rather than a measurement. Measured: **5 of the 6 on V1 M4 are confirmed benign** — text bounding box fully inside the widget's, 100% of the text's ink on it, same axes (the four thermoception cell readings and the body-temperature value). **The sixth is not**: `'+84'` × a `Rectangle` in the arena axes, 6 px, where the text box is **outside** the widget, only **3%** of the text's ink lies on it, and the widget's z-order (5) is **above** the text's (3) — a neighbouring patch painted over the corner of a label. Small, but the same family as the `'GRS'` 4 px hit the developer did name, and previously unnumbered. Worth a defect number when the register is next touched; not a CP0.3 gate.
3. **No test pins the coordinates.** Element identity is enforced in the firing criterion, but the pixel counts and positions are only printed. A future change that moved a defect elsewhere in the frame would still pass. Cheap to add when CP2.2's mutations land.
4. **`REQUIRED_CONTROLS` is dead in `main()`.** `main()` fails on *any* missed control, which is stricter than the constant advertises; the constant is used only by a test. Harmless, but it reads as though D10/D12 were optional when they are not.
5. **Not re-verified, and correctly declared out of scope by the developer**: the two rules that are implemented but unexercised (`numeric_in_arena` is not wired to the CLI; the clip-path half of `clipped` never fires because neither renderer sets a clip path on text). Both are stated in the Implementation Report rather than left to be discovered, which is the right handling.

**Speed:** ✅ not applicable, and the skip is independently corroborated rather than accepted on judgement — the guard's raw-frame hashes for M1, M2 and M4 are unchanged, so V1's rendered output is bit-identical to before this phase. Both new files are hand-run/test-only and off every training path. Audit runtime (a phase-boundary cost, not a training cost): V1 M4 frame 22 s, V2 M4 frame 13 s, full 7-control run 33 s, container i9-7900X CPU.

**Not run, deliberately:** `scripts/claude/regen_dev_index.py`. This doc's frontmatter is unchanged by Revision 15, so the index entry is unchanged — and the regenerator stamps `datetime.now()` into its output, so running it would write a spurious diff onto `docs/develop/INDEX.md`, which currently carries another session's staged changes.

**Conclusion.** CP0.3 is **met**. The audit finds all seven known defects on the right elements at the right coordinates, its one chosen threshold survives an 8.2× sweep without changing any verdict, its mutation control demonstrates the findings are decided by measured pixels rather than by a constant, and it found a real defect (D5 on the default world) and a real plan error (D2's class) that nobody prompted it to look for. No frozen file was touched, `accept` was never run, and nothing was committed.

**Phase 0c commit (explicit pathspec):**
`scripts/eval/render_layout_audit.py`, `tests/env/test_render_audit_controls.py`, `docs/environment/SCRIPTS_DEPENDENCY_MAP.md`, `docs/develop/active/refactors/RENDERER_LAYOUT_REDESIGN.md`.
Exclude `docs/develop/INDEX.md` and `docs/develop/active/refactors/SAVED_RUN_CONFIG_COMPAT.md` (staged by another session), and the untracked `docs/experiments/active/sensor_ladder/figures/` tree and `docs/diary/`, `docs/develop/active/meta/artifact_format_bugs.md`, `docs/experiments/active/recovery_in_bush_tuning/` (all other sessions' work).

*Verified by: senior-developer*

### Phase 0c fix pass (2026-09-16): negative controls, and the thirteenth defect

> **Verified by**: senior-developer
> **Date**: 2026-09-16
> **Verdict**: **VERIFIED.** Every claim in the fix-pass report was re-derived rather than read. The mutation result reproduces exactly under an independently written mutation; the `'+84'` finding is confirmed from the frozen source's own constants and from the composite pixels, and is numbered **D13**; the fill-split holds against a pixel check of all eleven collisions. Three small notes below, none blocking.

**What was checked, in plain words.** The previous verification passed this instrument, and then a code review found the hole that mattered most: the test suite could not tell a working instrument from one that flags every pixel of the canvas. This pass was supposed to close that. Checking it means doing the same thing to the tests that the tests do to the instrument — breaking the measurement deliberately and confirming the suite notices. Nothing below is taken from the developer's report; where a number appears, the verifier produced it.

**The mutation, re-run with a different construction.** The developer's proof used pytest's `monkeypatch` inside the suite. The verifier instead patched `FrameProbe.ink` at class level from a pytest **plugin** loaded before collection, returning `ones_like` of the real mask — same semantics, independent wiring, and it also proves the shape of the mutated mask is the shape the real measurement produces.

| Run | Result |
|---|---|
| Suite, unmutated (verifier's own run) | **38 passed in 110.39 s**, exit 0 |
| `ink()` → all-True (flag everything) | **10 failed, 28 passed** — `test_positive_control_hits_at_the_pinned_coordinates[D1/D2/D3/D6/D10]`, `test_v1_m4_finding_counts_are_pinned`, `test_v1_m1_finding_counts_are_pinned`, `test_v1_m1_reproduces_d5_in_the_vitals_column`, `test_v1_m4_out_of_card_flags_only_the_escaped_readout`, `test_fill_class_splits_the_thermal_scale_label_from_the_in_widget_labels` |
| `ink()` → all-False (see nothing), the complementary mutation, run by the verifier | **17 failed, 21 passed** |

The ten failing names are **exactly** the developer's table, in the same set. The claim stands as written.

**Are the two stated caveats honest, or is there a hole? Answered by measuring the opposite mutation.**

- **`test_positive_control_fires` surviving flag-everything is correct, not a gap.** A positive control measures sensitivity; a maximally sensitive instrument passes it by construction. The question worth asking is whether *anything* can falsify it — and the blind mutation does: D1, D2, D3 and D6 all fail under it. The controls are therefore two-sided overall (coordinates catch over-reporting, blindness catches under-reporting), which is what the pair of mutations demonstrates.
- **`test_v1_m4_absent_panels_are_exactly_proprioception` surviving flag-everything is also correct.** `panel_absent` asks whether a title has ink; Proprioception has no title element at all, so it stays absent whatever `ink()` claims. And that test is a genuine negative control against its own failure mode — under blind ink it **fails**, because every title loses its ink and every panel is then reported dropped.
- **The residual hole, stated precisely (note 1).** `panel_absent` is decided by the title table and the observation breakdown, not by pixels, so the D8 and D12 controls fire under **both** mutations. On the V1 campfire frame the exact-absent-set test covers the over-reporting direction. On the **V2** frame nothing does: there is no exact-count pin and no exact-absent-set pin for V2, so a `panel_absent` rule that started over-reporting on V2 would pass the whole suite. Narrow and non-blocking — the natural home is CP2.2's mutations.

**`'+84'` — confirmed, and numbered D13.** Re-derived from the frozen source before looking at any pixel, then confirmed against the composite.

| Claim | Verifier's measurement |
|---|---|
| Strip's 52nd segment ends at axes-fraction 0.77220 | `0.76 + (0.52/51 + 0.002)` = **0.7721961** ✅ |
| Label anchored 0.77000, `ha='left'` | `0.24 + 0.52 + 0.01` = **0.77** ✅ (`renderer.py:777`) |
| Segment `zorder=5` over label `zorder=3` | ✅ same Axes, read off the live artists |
| Every thermal frame | ✅ the block is inside `if thermal_on:`; both numbers are literals |
| The `+` loses ~2 px | **2 px of the label's 70 px of raw ink**, in a single pixel column (867, rows 802–803). Predicted overlap from the constants alone: 0.00220 × 554.26 px = **1.22 px** of axes width |
| The frame shows the segment, not the glyph | ✅ composite `[103 0 31]` at both pixels = the segment exactly (distance 0); the glyph alone would paint `[152 157 167]` and `[242 243 244]` — **157 and 243** away |

Numbered **D13** in §A2 with a root-cause bullet. Two precision notes: the developer's phrase "the first ~2 px column" is one column 1.22 px wide (their "2 px of a 70 px glyph" is exact); and the label is formatted `{vmax:+.0f}`, so the *geometric* overlap is world-independent while whether ink is lost depends on the left side bearing of the sign glyph — measured for `+`. Hand-off to `bug-curator` issued and completed.

**The `text_over_fill` / `fill_over_text` split — checked against pixels on all eleven collisions, not accepted as reasoning.** For each collision the verifier asked the frame directly: at the shared **raw** ink, does the composite match the glyph drawn alone or the partner drawn alone?

| Collisions | Pixel verdict vs. assigned class |
|---|---|
| 5 benign on V1 M4 (`+0.00 real +0.00`, `+10`, `-13`, `-14`, `-12`) | composite matches the **glyph exactly** at **100 % of solid-ink pixels** (90/90, 12/16, 11/15, 13/16, 10/15), partner at 0 % — **agrees** |
| `'+84'` on V1 M4 | composite matches the **partner exactly** at 100 %, glyph at 0 % — **agrees** |
| 4 benign on V2 M4 (thermoception readings) | glyph exact at all solid pixels, partner at none — **agrees** |
| `'GRS'` on V2 M4 | **undecidable by pixels** — see below |

`GRS` is the interesting one, and it vindicates the developer's argument rather than undermining it. A first pass with discriminator (B) (solo-vs-pair) called it "partner on top" — the exact false positive the report says (B) produces on that exact element. Refining to solid-ink pixels shows why: `GRS` is drawn **semi-transparently** (peak deviation from the bare canvas **99**/255, against 218–224 for every opaque label), so the composite is a true blend and matches **neither** solo render at **any** of its 20 shared pixels. No pure-pixel test can attribute a blended glyph; composition order (text `zorder=3` above the bar's `2`, same Axes) is the only sound answer, and it says the label is composed last. So the split is a measurement, not a convenient relabelling — **note 2**: the dominant cause of (B)'s failure on `GRS` is alpha, with anti-aliasing secondary, which is slightly narrower than the report's "anti-aliased fringes"; and **note 3**: the class docstring's "what the frame shows at the shared pixels is the glyph" is strictly a blend for an alpha-drawn label — legible, but worth a word when §D1.3's painters land.

**Everything else confirmed.**

| Check | Result |
|---|---|
| `--controls` | **7/7 fired**, exit 0 — same rules, same elements, same coordinates as the earlier verification: D1 `text_over_text` 59 px (1179, 357); D2 `out_of_card` 169 px (1183, 279); D3 `text_over_border` 30 px (252, 644); D6 17 px and 25 px at y 453; D8/D12 `panel_absent`; D10 `observed_caption` (316, 292) |
| `v1_path_guard.py check` | `PASS=10, ACCEPTED=0, ATTRIBUTED=0, UNATTRIBUTABLE=0`; `FRAMES PASS` on M1, M2, M4; `RESULT: OK`, **exit 0** |
| No frozen file touched | `git status` over `src/`, `configs/` and the frozen `scripts/eval/` files is **empty** |
| `accept` never run | `baseline.json` has `user_accepted: []` and is **git-clean**; last three commits touching it are Phase 0a, 0b and the ladder re-record |
| Nothing staged | `git diff --cached` names only `docs/develop/INDEX.md` and `SAVED_RUN_CONFIG_COMPAT.md`, both another session's |
| `SCRIPTS_DEPENDENCY_MAP.md` | **+2 / −0**, no other hunk: the §1c bare-import row and the §3 row, both Phase 0c's own. The "five required" wording the fix pass mentions never existed as a separate hunk — the §3 row is new and already says seven |
| Claimed removals/additions | `REQUIRED_CONTROLS` **gone** from the script (a test asserts its absence); `--arena-axes` wired at 4 sites; D2's control rules are `("out_of_card", "text_over_text")` with the unreachable `text_over_border` removed |
| Scope proportionality | audit 1034 → 1164 lines (+130: the fill split, `_is_painted_over`/`_draw_index`, the arena flag, docstring); tests 183 → 595 (+412 for 18 → 38 tests, mostly coordinate tables and fixtures); plan +293; map +2. Nothing outside the reported scope |

**Speed:** ✅ not applicable, corroborated rather than asserted — the guard's raw-frame hashes for M1, M2 and M4 are unchanged, so V1's output is bit-identical; both files are hand-run/test-only and off every training path. Suite runtime 71 s → 110 s is the two extra rendered frames plus the in-suite mutation, a phase-boundary cost.

**Not run, deliberately:** `scripts/claude/regen_dev_index.py`. This doc's frontmatter is unchanged (`last_updated` was already 2026-09-16), so the index entry would not move — and the regenerator stamps `datetime.now()`, which would write a spurious diff onto `docs/develop/INDEX.md`, a file another session currently has both staged and modified.

**Conclusion.** The fix pass does what it claims. The instrument is now falsifiable in both directions, the seven controls are unchanged on real frames, and the one finding the original pass mislabelled as harmless is a real defect, now **D13**. Phase 0c is ready to commit.

**Phase 0c commit (explicit pathspec, unchanged from the earlier verification):**
`scripts/eval/render_layout_audit.py`, `tests/env/test_render_audit_controls.py`, `docs/environment/SCRIPTS_DEPENDENCY_MAP.md`, `docs/develop/active/refactors/RENDERER_LAYOUT_REDESIGN.md`.
`docs/develop/active/issues/KNOWN_BUGS.md` (the D13 row, written by `bug-curator`) is a **separate** commit — different concern, different owner. Exclude everything else in the working tree: `docs/develop/INDEX.md` and `SAVED_RUN_CONFIG_COMPAT.md` (staged by another session), the untracked `docs/experiments/active/sensor_ladder/figures/` tree, `docs/diary/`, `artifact_format_bugs.md`, and `docs/experiments/active/recovery_in_bush_tuning/`.

*Verified by: senior-developer*

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

---

## Implementation Report — the demonstration loosening of the recording world (2026-09-16)

> **Implemented by**: developer · **Date**: 2026-09-16 · **Scope**: make the render-audit *recording* world survivable enough to produce usable demonstration footage, then re-record the CP0.2 fixtures and the V1 frame baseline.

### What this is, in plain words

The dashboard redesign is demonstrated and audited on a handful of saved episodes called *fixtures* — one per kind of world the new video has to draw. The most important of them is the **campfire world**: the only maintained world where the agent has a body temperature, feels heat, and shares its arena with fires. The problem was that this world killed the agent almost immediately, so every fixture was a few-second clip of something dying — a poor demonstration of panels whose entire job is to show a body changing over time.

The user's instruction was to loosen the world **for recording purposes only**, and explicitly **not** to edit the two curriculum config files (`05-campfire_thermal_10x10.yaml`, `06-sensory_noise_10x10.yaml`), whose difficulty is theirs to set and which another session is tuning right now. So the loosening lives entirely **inside the fixture generator** as an in-memory override, and is stamped into every affected recording so nobody can mistake a loosened recording for the curriculum level it names.

**The headline, and it corrects the brief.** The brief's premise was that the world kills the agent *by freezing*. Measured across twelve seeds rather than the single exported episode that prompted it, **freezing is not the main killer** — it accounts for 2 of 12 deaths. **Predation does** (6 of 12, all recorded as "injury"), with starvation third (4 of 12). Warming the world therefore fixes a real problem but a smaller one than expected, and the report below says plainly what it did and did not buy.

### Files changed

| File | Change |
|---|---|
| `scripts/eval/make_render_fixture_recordings.py` | New `_DEMO_LOOSENING` override dict and `_DEMO_LOOSENING_NOTE` provenance string, both heavily commented with the measurements that chose them. Applied to the four cells whose world carries the thermal system: **M3, M4, M4b, M6b**. No behaviour change for M1, M1x, M2, M5, M6. |
| `docs/.../v1_guard/baseline.json` | Re-recorded fixture + frame baseline (`record-frames --force --note`, the note citing the loosening and its measured consequences). |
| `tests/env/test_render_audit_controls.py` | **Three pinned literals re-pinned** — see "Deviations" item 3. Not named in the brief; flagged rather than done silently. |
| *(none)* | **No config file was edited.** `configs/environment/experiment/basic/05-campfire_thermal_10x10.yaml` and `06-sensory_noise_10x10.yaml` are untouched, as required. |

### The loosening, and how it was chosen

```
thermal.default_temp     -28..-22  ->  -20.5..-19.5     (the world baseline)
body.start_injury_high        100  ->  40               (level 03's random-start range)
body.start_nutrition_low        0  ->  60               (level 03's random-start range)
```

**The coupling was measured, not assumed.** A fire's heat is defined as a *ratio* of the baseline's magnitude (`temperature_ratio: [11, 13]` × `|default_temp|`), so warming the world **also cools every campfire** — by about 19% here. The question "is the fire still a meaningful, visibly hot feature" was answered from the field the environment actually builds, not from arithmetic on the config.

**Candidates for the ambient, all measured on twelve seeds (7–18) against an 80-step cap.** "body eq" is the temperature the body settles at in that cell, which is what the survivable band `[-15, +15]` is defined on.

| Candidate | `default_temp` | Episode lengths | Cold deaths | Fire cell → body eq | Ring 1 out → body eq | Coldest → body eq | Arena span | Verdict |
|---|---|---|---|---|---|---|---|---|
| C0 | −28..−22 *(baseline)* | 2,3,4,5,8,8,14,16,30,30,33,34 | **2/12** | +72.6 → **+58.1** | +10.6 → +8.5 | −24.5 → −19.6 | 97.1° | the world as it was |
| C1 | −24..−21 | …,33,34,38,38 | 2/12 | +66.0 → +52.8 | +9.7 → +7.7 | −22.2 → −17.8 | 88.2° | rejected: cold still kills |
| C2 | −22..−20 | …,33,34,47,47 | 2/12 | +61.8 → +49.4 | +9.0 → +7.2 | −20.8 → −16.7 | 82.6° | rejected: cold still kills |
| C3 | −21..−20 | …,33,34,50,50 | 2/12 | +60.5 → +48.4 | +8.9 → +7.1 | −20.4 → −16.3 | 80.9° | rejected: cold still kills |
| **C4** | **−20.5..−19.5** | …,33,34,50,50 | **0/12** | **+59.0 → +47.2** | **+8.6 → +6.9** | **−19.9 → −15.9** | **78.9°** | **CHOSEN** |
| C5 | −20..−19.2 | identical to C4 | 0/12 | +57.9 → +46.3 | +8.5 → +6.8 | −19.5 → −15.6 | 77.4° | rejected: no gain over C4, less margin |
| C6 | −19.6..−19.2 | identical to C4 | 0/12 | +57.4 → +45.9 | +8.4 → +6.7 | −19.4 → −15.5 | 76.8° | rejected: sits on the refusal edge |
| C7 | −19.2..−19.0 | — | — | — | — | — | — | **REFUSED AT LOAD** |
| C8 | −19..−18.5 | — | — | — | — | — | — | **REFUSED AT LOAD** |
| C9 | −18..−16 | — | — | — | — | — | — | **REFUSED AT LOAD** |

> **Read the "Cold deaths" column as warm-only (clarified 2026-09-16).** This sweep varies the **ambient temperature alone**, with the two start-condition keys left at their config values. So C4's **0/12** is the cold-death count for `default_temp` −20.5..−19.5 *by itself*, and it is **not** the figure for the override that shipped, which also sets `start_injury_high` and `start_nutrition_low` and measures **1/12**. Carrying this column across to describe the combined override is exactly the error the verification report's Issue 1 caught; the column is correct for what it measured, and is labelled here so it is not borrowed again.

**There is a hard ceiling, and it is the environment's own.** `config_loader._check_thermal_structure` refuses to load a thermal world that has lost the task. Past roughly −19.2 it raises *"the cold is not a clock: three cells out settles at −14.98, inside the survivable band, so the agent never has to return to the fire."* That is the load-time gate deciding the upper bound, not a judgement call — and it is why C4 was preferred over the marginally warmer C5/C6: it keeps ~0.3–0.5° of margin to a boundary that is measured, not estimated.

**The other lever — lowering the lethal floor — fails, and here is why.** Dropping `thermal.min_temperature` widens the survivable band from *both* ends, so the "three cells out must be lethal" condition breaks immediately:

| Lever | Result |
|---|---|
| `min_temperature` −15 → −25 | **REFUSED**: three cells out settles at −22.07, inside `[-25, 15]` |
| `min_temperature` −15 → −20 | **REFUSED**: three cells out settles at −17.34, inside `[-20, 15]` |
| `min_temperature` −20 *with* ambient −24..−21 | **REFUSED**: three cells out settles at −18.92, inside `[-20, 15]` |

So warming the ambient is the only lever of the two that the environment will certify. Recorded here so nobody re-tries the floor.

**Why the two start-condition keys were needed as well.** Warming the ambient does **nothing** for the two episodes the fixtures actually record (seeds 7 and 8), because both end in starvation, not cold: nutrition falls 1.0 per step, so an episode that begins at nutrition 13 is over in 13 steps whatever the weather. Measured, warm-only versus warm-plus-start-conditions:

| Variant | Lengths (12 seeds) | Median | ≥60 steps | Seed 8 (fixture episode 2) |
|---|---|---|---|---|
| Neither lever | 2,3,4,5,8,8,14,16,30,30,33,34 | 11.0 | 0/12 | 34 steps |
| Warm only | 2,3,4,5,8,8,14,16,33,34,50,50 | 11.0 | 0/12 | **34 steps — unchanged** |
| Warm + start conditions | 3,4,6,9,9,9,18,23,51,57,73,74 | 13.5 | 2/12 | **74 steps** |

### What this does NOT fix — stated rather than omitted

**The binding cause of short episodes in this world is predation, not cold.** Under a seeded *random* policy against level 03's 2–12 ambush predators and level 04's pounce, **6 of 12 seeds still end inside 10 steps by injury**, several from a near-healthy start (seed 10 starts at injury 1 and is dead at step 3). No thermal or start-condition value changes that. Reaching "most episodes at the 80-step cap" would need either a **predator-pressure override** — which would gut the threat/olfaction demonstration exactly as removing fires would gut the thermal one — or a **trained policy** instead of a random one. Both are decisions for the user, so neither was done. The generator's override mechanism is also dotted-scalar only, so a predator-count override would need new machinery.

**Target achieved, honestly stated:** death by cold is **halved, not gone** — **2/12 → 1/12** under the override that actually ships (all three keys together). *Corrected 2026-09-16 after the verification report's Issue 1: the earlier "0/12" here was the **warm-only** result, carried across to describe the combined override. Warming alone does remove freezing, but the fuller starting stomach buys longer episodes, and seed 11 then survives to freeze at step 57 — longer episodes buy back the cold. Re-measured independently (`tmp/20260916_2100_remeasure_shipped_override.py`), classifying each death twice — once from `termination_reason`, once from the final body state — and the two agree seed for seed: injury 9, starvation 2, freezing 1. The developer's own `tmp/20260916_191500_campfire_two_levers.log` row A6 agrees.* The recorded footage roughly doubles in length (fixture episodes **14 and 34 steps → 23 and 74 steps**), with one episode now effectively at the 80-step cap. A *majority* of episodes at the cap was **not** achieved, for the reason above.

### The fixtures and the frame baseline

All nine CP0.2 cells regenerated (`--episodes 2 --max-steps 120 --seed 7`, the defaults). Snapshot counts: thermal cells **[15, 35] → [24, 75]**; every non-thermal cell unchanged at **[36, 9]**.

| Cell | World | `run_meta` | Episode payloads | 8 pinned V1 frames |
|---|---|---|---|---|
| M1 | `default.yaml` — untouched | SAME | SAME | **all 8 identical** (`20a67f21…`) |
| M2 | `default.yaml` — untouched | SAME | SAME | **all 8 identical** (`20a67f21…`) |
| M4 | campfire world — **loosened** | CHANGED | CHANGED | **all 8 moved** (`3da423ec…` → `fd92f8c3…`, last `a8cfe9aa…` → `6d272fbc…`) |

**This is exactly the wanted result**: the only cell that moved is the one whose world genuinely changed, and the two cells on the untouched config did not move a single pixel — which is what rules out an accidental change to the frozen V1 path. `frozen_files`, `user_accepted` (still 0 entries) and `plan_start_commit` are unchanged in the baseline.

### Test results

| Check | Before | After | Notes |
|---|---|---|---|
| `v1_path_guard.py check` | 10 PASS, `FRAMES PASS` ×3, **exit 0** | 10 PASS, `FRAMES PASS` ×3, **exit 0** | all ten frozen files `PASS`; `accept` never run |
| `tests/env/test_v1_path_guard.py` | — | **71 passed** | |
| `tests/env/test_render_audit_controls.py` | **38 passed** | 3 failed / 35 passed → **38 passed** after re-pin | see Deviations item 3 |
| CP0.2 matrix report | — | 9/9 cells, **no failure condition fires**, exit 0 | evidence in the CP0.2 checkpoint note above |

### Speed check

**Skipped, and here is why it provably cannot matter:** every file changed is off the training path. `make_render_fixture_recordings.py` is a hand-run fixture generator, `test_render_audit_controls.py` is a test, and `baseline.json` is data. No `src/` module, no environment step, no model code and no config consumed by training was touched — the ten frozen V1 files are byte-identical and the two curriculum configs were not opened for writing.

### Deviations from the brief — none silent

1. **The loosening is not only thermal.** The brief said "temp"; the measurement showed temperature alone does nothing for the two episodes actually recorded (table above), so two of level 03's random-start ranges were loosened as well. Both are in the same in-memory override, both are stamped in `run_meta`, and reverting them is a two-line change. **Flagged for `senior-developer` to accept or reverse.**
2. **Applied to M3 and M6b as well as M4/M4b.** Level 06 (the noise world) inherits level 05's campfires and cold baseline, so it froze identically; leaving it out would have left half the demonstration footage short. These two cells are not in the frame baseline, so the guard is unaffected by the choice.
3. **`tests/env/test_render_audit_controls.py` was edited, and it was not named in the brief.** Three *literals* in it encode numbers the frame draws — the thermoception tick labels, the thermal scale's max-value label (`'+84'` → `'+63'`), and D10's nutrition token (`OBS: 0.13` → `OBS: 0.65`) — so all three moved when the world did. What did **not** move is the part that matters: `V1_M4_COUNTS` and `V1_M1_COUNTS` are unchanged, all seven positive controls still fire, and D13's bbox `(866, 801, 867, 804)` and 6 px overlap and D10's bbox are **identical to the old pins**. In other words the renderer and the instrument are unchanged and only the world's numbers moved, which is the reading the re-pin records in a dated comment beside each literal. The alternative — leaving three red tests — is the "undiagnosed red gate" pattern `KNOWN_BUGS.md` warns about, so it was rejected.

### Prior art

Checked `docs/develop/active/issues/KNOWN_BUGS.md` directly (sub-agents cannot spawn `bug-curator`): **no row records the recording world being too harsh for demonstration footage**, and nothing here contradicts an existing row. The adjacent rows — the episode-video dashboard row (D1–D13) and the "stale fixtures" note — are consistent with this work. **No new bug row is owed**; this was a deliberate world change, not a defect.

### Blockers / follow-ups for `senior-developer`

- **Decide on Deviation 1 and 2** (the non-thermal keys, and extending the loosening to M3/M6b).
- **Decide on the predation ceiling.** If demonstration footage really must run to the 80-step cap, someone must choose between a predator-pressure override (new machinery in the generator, and a weaker threat demonstration) and recording from a trained policy.
- **Out of scope and deliberately not done**, per the brief: the artifact page's example episode and its figures were not regenerated, since the grid is about to change to a 48 px cell with a new shared-cell rule.
- **Nothing was staged or committed.** The working tree carries this plan doc (which also holds another session's Revisions 15/16), `make_render_fixture_recordings.py`, `test_render_audit_controls.py` and `baseline.json`. `docs/develop/INDEX.md` and `SAVED_RUN_CONFIG_COMPAT.md` are **staged by another session** and must not be swept in — commit with an explicit pathspec.

Implemented by: developer

---

## Verification Report — the demonstration loosening of the recording world (2026-09-16)

> **Verdict**: ✅ **VERIFIED WITH ISSUES**. The change does what it claims and the frozen V1 path is provably untouched — but one number that is **stamped into four recordings and into the guard baseline** is wrong, and must be corrected before this is committed.

### What was checked, in plain words

The developer loosened the world used to *record* demonstration footage — warmer air, a gentler starting injury, a fuller starting stomach — so the saved episodes last long enough to demonstrate panels whose job is to show a body changing. Nothing about the loosening lives in a config file; it is applied in memory inside the fixture generator and stamped into each recording so nobody can mistake a loosened recording for the curriculum level it names. The question this report answers is whether the *world* moved and the *renderer and its measuring instrument* stayed still — because three pinned test values were changed to match new output, and re-pinning a test to match new output is the classic way a real regression gets absorbed. **Everything was re-derived from the environment and the loader rather than read out of the developer's report or re-run through the developer's own sweep script.**

### The corrected premise — independently confirmed

The brief's premise (mine) was that this world "kills the agent by freezing while otherwise healthy". **It does not.** Stepping the shipped campfire world over the same twelve seeds (7–18) against an 80-step cap, with the fixture generator's own seeded random policy re-implemented from `generate_cell`, and classifying each death **twice** — once from the environment's `termination_reason` code and once, independently, from the final body state (nutrition ≤ 0 / injury ≥ max / body temperature outside `[−15, +15]`) — the two classifiers agree seed for seed:

| Cause | Deaths in 12 seeds |
|---|---|
| Injury, i.e. predation | **6** |
| Starvation | **4** |
| Freezing | **2** (seeds 9 and 11, both at 30 steps) |

So freezing is the *smallest* of the three killers, exactly as the developer reported. **The record now says what is true, and my brief was wrong.**

### File-by-file

| File | Verdict | Finding |
|---|---|---|
| `scripts/eval/make_render_fixture_recordings.py` | ✅ | +100/−12 lines, all of it the `_DEMO_LOOSENING` dict, its provenance string, and the four cell entries that take it. The override is applied through the existing in-memory path (`build_params`, which already raises on an override key that names nothing), so no new machinery. Verified on disk: cells **M3, M4, M4b, M6b** carry `synthetic=True` and the exact three (M4b: four) override keys in `run_meta`; **M1, M2, M5, M6 are untouched**. One incidental correction rides along and is right: M3's description said "level-05 basic world", which Revision 14 had already made wrong — the noise world is level 06. |
| `docs/.../v1_guard/baseline.json` | ✅ | 13 lines changed, and **only** the ones that should be: M4's `run_meta_sha256`, its two episode hashes, its eight frame hashes, and the two note lines. `frozen_files` (10 entries), `user_accepted` (still `[]`) and `plan_start_commit` (`73d466d8…`) are byte-identical. M1's and M2's fixture and frame hashes do not appear in the diff at all. |
| `tests/env/test_render_audit_controls.py` | ⚠️ | The high-risk item. Re-pin judged **sound** — see the next section. Marked ⚠️ only because the benign-set assertion is now weaker than it was (four distinct strings where there were five), which is a real, explained consequence rather than a defect. |
| `RENDERER_LAYOUT_REDESIGN.md` (Implementation Report) | ⚠️ | Accurate and unusually candid, except for the "0/12" freezing claim — see Issue 1. |
| `configs/**` | ✅ | **Nothing modified.** `git status --porcelain -- configs/` is empty; so is `-- src/`. The two curriculum configs the user reserved are untouched. |

### The three re-pinned test literals: why this is the world moving, not the instrument

The claim is that only numbers the frame *draws* changed. Checked four ways, and all four agree:

1. **What did not move.** `V1_M4_COUNTS` and `V1_M1_COUNTS` do not appear in the diff. Neither does D13's bbox `(866, 801, 867, 804)` nor its 6 px overlap, nor D10's bbox `(316, 292, 365, 298)`. The `numeric_in_arena` hit count is still pinned at 5 and the `text_over_fill` count still at 5 via `V1_M4_COUNTS`. A renderer or audit change would have moved at least one of these; none moved.
2. **The numbers that did move, moved by exactly the world's own scale factor.** A campfire's heat is `temperature_ratio × |default_temp|`, so warming the baseline from −28 to −20.5 scales every temperature the frame prints by ≈ **0.732**. Measured against the re-pins: the thermal scale's max label `+84 → +63` is a factor of **0.750**; the arena's hottest thermoception reading `+75 → +56` is **0.747**; the tick labels `+10 → +8`, `−13 → −10`, `−12 → −9` are the same ratio within rounding. That is a world uniformly cooler by the factor the config change implies — not an arbitrary redraw.
3. **D10's nutrition token** `OBS: 0.13 → OBS: 0.65` is the direct consequence of `body.start_nutrition_low 0 → 60`, at an unchanged bbox — the same string box, a different number in it.
4. **The whole suite is green:** `tests/env/test_render_audit_controls.py` + `tests/env/test_v1_path_guard.py` = **109 passed** (38 + 71), re-run by the verifier, which includes all seven positive controls and both "the instrument is broken" negative controls.

**One consequence worth naming for a later reader:** the benign `text_over_fill` set now holds four strings for five collisions (two thermoception cells read the same temperature on this frame), where before it held five for five. The set assertion is therefore one element weaker than it was; the count is still pinned separately at 5, so nothing is unguarded — but a future world where three cells coincide would weaken it again, and the count is what should be trusted.

### The load-bearing ceiling claim: verified against the loader, not against the report

Every candidate was re-run through the real `load_env_config` → `load_env_params` path. `config_loader._check_thermal_structure` does refuse a warmer world, in the exact terms quoted, and it refuses the alternative lever too:

| Tried | Loader's answer |
|---|---|
| Ambient −20.5..−19.5 (**the chosen value**) | **LOADS** |
| Ambient −19.6..−19.2 | LOADS (the last one that does) |
| Ambient −19.2..−19.0 | **REFUSED** — "the cold is not a clock: three cells out settles at **−14.98**, inside the survivable band [−15.0, 15.0], so the agent never has to return to the fire" |
| Ambient −19.0..−18.5 / −18..−16 | **REFUSED**, same rule |
| `min_temperature` −15 → −25 | **REFUSED** — three cells out settles at **−22.07**, inside [−25, 15] |
| `min_temperature` −15 → −20 | **REFUSED** — settles at **−17.34**, inside [−20, 15] |
| `min_temperature` −20 **with** ambient −24..−21 | **REFUSED** — settles at **−18.92**, inside [−20, 15] |

The developer had not mis-read an error: the ceiling is the environment's own load-time gate, the chosen value sits just under it with margin, and the floor lever genuinely widens the band from both ends. **The lever chosen is the only one the environment will certify.**

### The frame baseline split, and the guard

`v1_path_guard.py check`: **10 frozen files PASS**, `ACCEPTED=0`, `UNATTRIBUTABLE=0`, **FRAMES PASS on M1, M2 and M4**, `RESULT: OK`, **exit 0**. `accept` was never run (`user_accepted` is still empty). M1 and M2 — both on the untouched `default.yaml` — are byte-identical across all eight pinned frames; M4, the loosened world, moved on all eight. That split is the evidence the frozen V1 path did not drift, and it holds.

### ❗ Issue 1 (must fix before commit): the "freezing is gone, 2/12 → 0/12" claim is false for the override that actually shipped

Re-measuring the **combined** override — warm air *and* the two start-condition keys, i.e. exactly what `_DEMO_LOOSENING` applies — over the same twelve seeds:

| | Freezing | Predation (injury) | Starvation |
|---|---|---|---|
| Developer's claim, everywhere it is written | **0 / 12** | – | – |
| Measured by the verifier (episode lengths 3, 4, 6, 9, 9, 9, 18, 23, 51, 57, 73, 74) | **1 / 12** (seed 11, at step 57) | 9 / 12 | 2 / 12 |

The developer's **own** log agrees with the verifier: `tmp/20260916_191500_campfire_two_levers.log`, row **A6** — the shipped combination — records `terminators {'injury': 9, 'starvation': 2, 'THERMAL': 1}`. The `0/12` figure is the **warm-only** result (row A1, and the C4 row of the candidate sweep), and it was carried across to describe the combined override. The mechanism is easy to see and worth stating: warming the world removes the two 30-step freezes, but the fuller starting stomach then lets seed 11 survive to step 57 — long enough to freeze anyway. **Longer episodes buy back the cold.**

This matters more than a typo because the sentence is **durable and duplicated**: it is stamped into the `run_meta` of four recordings (M3, M4, M4b, M6b) via `_DEMO_LOOSENING_NOTE`, written into `baseline.json`'s `frames_note`, and repeated in the source comment and the Implementation Report. A later reader comparing worlds will read "freezing 2/12 → 0/12" off the recording itself.

**Required fix, and its cost.** Correct the claim in all four places to "**freezing as a cause of death 2/12 → 1/12** (the two 30-step freezes are removed; one episode now survives long enough to freeze at step 57)", and correct the report's "death by cold is gone" to "death by cold is halved". Because the note text lives in `run_meta`, changing it changes M4's `run_meta_sha256` — so the fixtures must be regenerated and `record-frames --force` re-run. **The eight frame hashes will not change** (the note does not touch the world), only the fixture hashes, which is itself a useful confirmation when it happens.

### The two scope deviations, judged

**(a) The override is not purely thermal — it also sets start injury and start nutrition. → ACCEPTED.** The brief said "temp", and the developer measured that temperature alone does nothing for the two episodes actually recorded (seed 8 stays at 34 steps under warm-only, and goes to 74 with the start keys). Nutrition falls 1.0 per step, so the starting value is a hard cap on episode length no matter the weather — warming a world cannot save an agent that begins with 13 nutrition. The keys are level-03 random-start *ranges*, they change no observation layout and no thermal structure, they are in-memory only, they are stamped in `run_meta`, and reverting them is a two-line change. One cost to record rather than discover later: the fixtures now never start with a near-fatal injury, so the vitals panels' extreme-value rendering is no longer exercised by a recorded episode — that case is already covered by §D5.3's labelled stress variant, and Phase 2 must not quietly drop it.

**(b) Applied to M3 and M6b as well as M4/M4b. → ACCEPTED.** Since Revision 14 the noise world (level 06) inherits the campfire world (level 05), so it carries the same fires and the same cold and froze identically; loosening one and not the other would have left half the demonstration footage short and the two worlds incomparable. Verified: neither cell is in the frame baseline (`frames` holds only M1, M2, M4), so the guard is untouched by the choice, and both cells carry the provenance note in `run_meta`. Both now record 24 and 75 snapshots, matching M4.

### Speed check

**⚠️ Skipped by the developer, and the skip is accepted.** The rule of thumb (discuss above 5 %, block above 15 %) presumes the change can affect runtime. This one cannot: `git status --porcelain` is empty for both `src/` and `configs/`, the ten frozen V1 files all report `PASS` against their baseline hashes, and the three changed files are a hand-run fixture generator, a test file and a JSON data file. No training step, environment step, model or training-consumed config was touched. Verdict: **✅ no regression possible**.

### Out-of-scope changes

**None.** Every changed file is named in the brief. `docs/develop/INDEX.md` and `SAVED_RUN_CONFIG_COMPAT.md` are staged by a different session and were correctly left alone.

### Conclusion

The world change is measured, justified, reversible, stamped into every artefact it affects, and demonstrably did not move the renderer or the audit. The re-pin is sound and is the right call over leaving three red tests. **One number is wrong in four places and must be corrected, with a fixture regeneration, before this is committed.**

Verified by: senior-developer

---

## Correction Report — Issue 1 fixed: freezing is halved, not removed (2026-09-16)

### What this is, in plain words

The verification report above found that one sentence in my Implementation Report was wrong, and that the wrong sentence had been **stamped into four saved recordings and into the guard's baseline file** — so anyone later opening one of those recordings to ask "what world did this come from?" would have been told something false about it. The sentence claimed that warming the recording world removed death-by-freezing entirely. It does not. That "gone" figure describes **warming the air on its own**; the override that actually ships also fills the agent's stomach and softens its starting injury, and those longer episodes give the cold more time to work. This report records the re-measurement, the four corrections, and the check proving nothing but the text changed.

### The re-measured figure, and the evidence for it

**Freezing as a cause of death under the shipped override: 1 of 12 seeds, not 0 of 12.** The one death is seed 11, which freezes at **step 57**.

I re-measured rather than trusting either the brief or the verifier. The script is `tmp/20260916_2100_remeasure_shipped_override.py`; it reads the override dict **out of the generator itself** (asserting `CELLS["M4"].overrides` equals `_DEMO_LOOSENING`, so a retyped value cannot drift from the shipped one), steps the real environment over the same twelve seeds (7–18) against an 80-step cap, and classifies each death **twice** — once from the environment's `termination_reason`, once independently from the final body state (nutrition ≤ 0 / injury ≥ `max_injury` / body temperature outside the loaded `[−15, +15]` band). **The two classifiers agree on all twelve seeds:**

| Cause | Deaths in 12 seeds |
|---|---|
| Injury (predation) | 9 |
| Starvation | 2 |
| **Freezing** | **1** (seed 11, step 57) |

This matches the developer log's row A6 — the shipped combination — which records `{'injury': 9, 'starvation': 2, 'THERMAL': 1}`, and it matches the verifier's independent count. **The user's stated figure of 1/12 is confirmed, and the measurement is what was used.**

**Why the error happened, stated so it is not repeated:** warming the air alone (log row A1) genuinely gives 0/12 — it removes both 30-step freezes. Adding the two start-condition keys then lets seed 11 survive to step 57, long enough to freeze anyway. **Longer episodes buy back the cold.** The 0/12 was a true number about a *different* override, borrowed to describe the shipped one.

### The four places corrected

| # | Place | What it now says |
|---|---|---|
| 1 | `_DEMO_LOOSENING_NOTE` in `scripts/eval/make_render_fixture_recordings.py` — the string written into the `run_meta` of **M3, M4, M4b, M6b** | "Measured on the **COMBINED** override, i.e. exactly the three values above and not on any one of them alone: freezing as a cause of death **2/12 seeds → 1/12, HALVED rather than removed**", followed by the mechanism and the note that warming alone would give 0/12 |
| 2 | `baseline.json` `frames_note` | Rewritten through `record-frames --force --note` (**never hand-edited**), carrying the same corrected figure, an explicit note that the earlier 0/12 in that field was the warm-only result carried across by mistake, and the expected hash split for this re-record |
| 3 | The source comment above `_DEMO_LOOSENING` | Now says warming **alone** gives 0/12 and adds "BE PRECISE ABOUT WHICH OVERRIDE THAT DESCRIBES", the combined 1/12, and the buy-back mechanism |
| 4 | Implementation Report, "Target achieved, honestly stated" | "death by cold is **halved, not gone** — **2/12 → 1/12** under the override that actually ships", with a dated note on what the old number was and where it came from |

**A fifth place, clarified rather than changed.** The candidate-sweep table's "Cold deaths" column (C0–C6) measures the **ambient lever alone**, so its `0/12` for C4 is correct for what it measured; changing it would have made it wrong. A note under the table now labels the whole column warm-only and states it is not the figure for the shipped override — since borrowing that column is precisely how this error occurred.

### The regeneration used as a check: frame hashes vs fixture hashes

The note is **metadata**: it must move the fixture hashes and leave every pinned pixel alone. `baseline.json` was snapshotted before anything was touched, then compared field by field.

| Hash set | Expected | Measured |
|---|---|---|
| **8 pinned frame hashes, M1** | identical | ✅ **all 8 identical** |
| **8 pinned frame hashes, M2** | identical | ✅ **all 8 identical** |
| **8 pinned frame hashes, M4** (the loosened, regenerated cell) | identical | ✅ **all 8 identical** — first `fd92f8c38200…`, last `6d272fbcf6e6…`, unchanged |
| **M4 `run_meta_sha256`** (carries the note) | changes | ✅ **`8b11d9872f20c714…` → `a52d2e838f7e211c…`** |
| M4 episode payloads | — | **byte-identical** (both episodes) |
| M1/M2 fixture hashes | unchanged | ✅ unchanged (not regenerated; the control) |

**No frame hash moved, so no investigation was owed.** The result is sharper than predicted: the only hash that moved in the entire baseline is the one `run_meta` carrying the text, and even the episode payloads are byte-identical — the world, the trajectories and every drawn pixel are provably untouched, and the change is confined to the provenance string. `frozen_files` (10), `user_accepted` (still **0 entries** — `accept` was never run), `plan_start_commit`, `plan_owned_paths` and `plan_sessions` are all unchanged.

### Test results

| Check | Result |
|---|---|
| `scripts/eval/v1_path_guard.py check` | **10/10 frozen files PASS**; ACCEPTED=0, ATTRIBUTED=0, UNATTRIBUTABLE=0; **FRAMES PASS ×3** (M1, M2, M4 "8 raw frames identical"); `RESULT: OK`, **exit 0** |
| `tests/env/test_render_audit_controls.py` | **38 passed**, exit 0 |
| `tests/env/test_v1_path_guard.py` | **71 passed**, exit 0 |
| Fixture regeneration (`--cells M3 M4 M4b M6b`) | exit 0; corrected note confirmed present in `run_meta` |

All four expected outcomes met: 38 + 71 passing, 10/10 PASS + FRAMES PASS, exit 0.

### Speed check

**Skipped, and it provably cannot matter.** The only code change is the text of a comment and of a provenance string in a hand-run fixture generator; `git status --porcelain` is **empty for both `src/` and `configs/`**, and the guard reports all ten frozen V1 files byte-identical. No training step, environment step, model, or training-consumed config was touched.

### On the benign `text_over_fill` set (the verification's open question) — recommendation, not a silent change

**It was not changed either way.** The assertion at `tests/env/test_render_audit_controls.py:524` pins four distinct strings for five collisions, because two thermoception cells happen to read the same temperature on this frame.

**Recommendation: leave it to CP0.3b, which owns it — do not tighten it now.** (1) **CP0.3 is closed** (`[x]`) but **CP0.3b is open** (`[ ]`), and its text already commits to re-pinning "the per-rule finding counts on the frozen M1 and M4 frames" with "every other rule's count unchanged" — this assertion sits squarely inside that scope, so tightening it now would do CP0.3b's work under a note-correction change and outside its gate. (2) Nothing is currently unguarded: the **count is pinned separately at 5** via `V1_M4_COUNTS`, so a collision appearing or disappearing still fails the suite; only the weaker *identity* check has degraded. (3) The right fix is a **multiset/`Counter`** over the collision strings rather than a `set`, restoring five-for-five and immune to future coincidences — but that changes the audit's own assertion shape, exactly the kind of instrument change CP0.3b exists to gate and re-pin deliberately. Doing it here would mean re-pinning an instrument in the same change that re-recorded a baseline, the pattern this plan is careful to avoid. **Flagged for `senior-developer` to schedule into CP0.3b.**

### Deviations and scope

**None.** Every file changed is one of the four the brief names. No config file was opened for writing (`05-campfire_thermal_10x10.yaml` and `06-sensory_noise_10x10.yaml` untouched), none of the ten frozen V1-path files changed, `accept` was never run, and **nothing was staged or committed** — the parallel session's staged files were left untouched and the index was never written.

Implemented by: developer

---

## Feedback from plan-reviewer (sixth pass: Revisions 17–18, terrain as ground cover and the whole world at 50 px)

**Date**: 2026-09-16 · **Verdict**: **NOT READY** — one Critical finding, in the verification Revision 17 adds, not in the two user decisions (which were not re-opened). The arithmetic was re-derived from `fig03_proposed_dashboard.py::pack()` and holds to the pixel (564 / 476 / 236; the 53 px ceiling is right); the slot formulas reproduce 15.00 / 10.35 / 10.12 px from the round-2 mock. Full table, answers to the six asked checks, assumptions and pass log in [`docs/reviews/plan_renderer_layout_redesign.md`](../../../reviews/plan_renderer_layout_redesign.md) §Sixth pass.

Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run · 🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

**Must be resolved before Phase 0d (Critical)**

- 🔴 **#54 `cell_overdraw` is blind to draw-order occlusion.** The rule counts connected components of *isolated* ink (what each artist draws alone). A token in the right slot but drawn beneath the bed, the ground square or the agent's outline keeps its full isolated ink, so components == kinds and the rule passes while the frame shows one occupant. The minimap variant has the same hole if measured by isolation — and the minimap defect §R17 names is draw order. M-E (force to centre) is caught; a z-order mutation is not. Phase 0c solved this exact problem for text with composition order (`fill_over_text`, `_is_painted_over` / `_draw_index`); the cell rule omits it. **Fix:** for every pixel of a token component the last-drawn element with ink there must belong to that component; measure the minimap's colour areas on the composite; add mutation **M-F** (bed above tokens; minimap agent dot above the split wedge) to CP0.3b and CP2.8. — owner `senior-developer` (spec), `developer` (Phase 0d)

**Should be resolved before Phase 1 pins its numbers (Moderate)**

- 🟡 **#55 The zero-tolerance was pinned from a different instrument at a different size.** The mock measured overlap at **40 px** (`cooccupancy_r2.py:705,1012`), with an alpha > 24/255 mask on a transparent canvas — not the audit's per-channel > 8/255 diff, and not at 48 or 50. At 50 px adjacent slots leave a 0.5 px geometric gap (keyline stroke *centred* on `h` at `h/8` = 1.29 px, not the plan's "1 px inside `h`"), entirely inside the anti-aliasing fringe. **Fix:** a Phase 0d negative control drawing two adjacent-slot tokens at 50 px, measured with `FrameProbe.ink`; if non-zero, inset the keyline — never loosen the tolerance. State stroke width and placement.
- 🟡 **#56 §D1.2 still says the arena is a grow panel with 300/330 columns; Revision 18 pins a fixed 50 px square on Figure 3's 320/440.** Two implementers diverge on day one. Maintained **5×5 worlds exist** (`basic/00-…5x5`, `01-…5x5`) and Revision 18 considers only ≥ 10. **Fix:** rewrite §D1.2 items 2–3; arena box is exactly `W × 50`; add a 5×5 case (314 px card, right column 726 px) to `test_dashboard_layout.py`.
- 🟡 **#57 The speed gate is now specified for the wrong arena, at the wrong phase, with two fail paths.** CP0.4 (unchecked, "before Phase 1") spikes a 25-square arena; §R18.2 item 8 says "Phase 1 must measure the arena painter" but Phase 1 has no painter (Matplotlib-free); CP0.4 says "go back to the user with B" while R18 says "reconsider the gate or the per-square cost". With 4× arena content the 0.5× ratio no longer discriminates architecture from content, so a miss could trigger a wrong pivot to Pillow. **Fix:** the spike draws the whole 10×10 world with §R17.3's composition and reports arena-only vs non-arena time; Phase 1 may precede CP0.4, CP0.4 must precede Phase 2; one pre-registered fail path — if A misses 0.5× but beats 1.0×, report the split to the user with three options (looser M4 ratio; per-cell slot pool instead of per-name glyph pool; B). Any change to Q9 is the user's.
- 🟡 **#58 Token medium unspecified.** §D1.4 and CP2.6 say `AxesImage` icons from `assets/dashboard_icons/`; §R17.3 and the `cells.py` row say vector forms ported from the mock (the floor test needs `MIN_MARK × h` to be a constant, which a PNG cannot give). A patch-drawn campfire bed **fails CP2.6 as written**. **Fix:** vector primitives in `cells.py`; rewrite CP2.6's clause to "bed ink present and classified as bed by area".
- 🟡 **#59 No matrix cell produces the geometry Phase 1's test asserts.** Every maintained config has both sense ranges at 0 (`default.yaml:222,232`, no `basic/` override), so no M-cell has a band; E-cells have a band but no thermal card. Thermal + band (516 px right need, 236 px band) exists only in Figure 3's sketch. **Fix:** assert the clause on a synthetic `LayoutContext` and say so.

**Low**

- 🟢 #60 The chevron floor is ambiguous (`h < 6` vs `0.62 h < 6`; the four-way clears the latter by 0.44 px). Say which and add it to the recomputed floors.
- 🟢 #61 Deferring Q21 is safe for Phase 1 only if "keep, `LEFT_W = 320`" is recorded as the assumption its pins rest on; ask Q21 before Phase 2 starts the minimap work.
- 🟢 #62 `cell_overdraw` cannot run on any frozen frame (V1's arena axes is unlabelled), so every Phase 0d negative control is synthetic until Phase 2 — say so. `/api/values`: kinds with a count. Prior art: Known Bugs "Chasing rabbit stays glued to the agent" makes agent + rabbit a frequent two-mover square — useful for archetype hunting; not a collision.

**On the six asked checks, briefly.** §R18.5 is tight on slots, priority, margin, halo and outline; loose on keyline, medium, chevron floor and fixed-vs-grow. The margins are non-negative against `fig03` literals (`MIN_RIGHT_W = 440`, band 200), not against measured minima — fit-or-fail makes a miss loud, but the 50 px floor cannot give, so pre-register the levers (Q21, the band). At 53 px both slacks are 6 px. The cells test is a real check; the audit rule is real for the concentric bug and blind for z-order (#54). The window's removal is carried through except the grow rule, 5×5 worlds, the no-band matrix, and the audit's per-frame cost (isolation renders scale with visible elements; minutes per V2 frame — a phase-boundary cost to state). None of the three unsolved cases blocks Phase 1.

**Assumptions**: ❓ Figure 3's constants are the real minima (CP1 measures). ❓ The mock's 0 px transfers to 50 px under the audit's threshold (#55). ❓ An A-style painter at 100 squares lands ≤ 0.5 × V1 (never measured). ❓ Grid pixel phase is constant (`x0 = 32`, integer cells). Verified: the arithmetic and ceiling; slot formulas; every maintained world ≤ 10; no maintained sense range ≥ 1; entity names match `CELL_PRIORITY`; the audit skips invisible artists (`render_layout_audit.py:536`); Phase 0d and the package do not exist yet; no config key, script or critical setting is touched.

**Cost of being wrong**: no data loss, no training run. #54 lets a z-order bug ship under a green CP2.8 from an instrument titled "cannot be fooled". #57 risks a wrong pivot to Pillow, the most expensive outcome on the table. The rest are a day of rework each.

**To flip the verdict**: fix #54, #56 and #57 in the plan text; the others can ride with the Phase 1 commit.

Reviewed by: plan-reviewer

## Feedback from plan-reviewer (seventh pass: Revision 19, the co-occupancy rule sees draw order)

> **Folded into [Revision 20](#revision-20-2026-09-16-after-plan-reviewer-seventh-pass-the-co-occupancy-rule-is-narrowed-to-the-elements-it-checks-never-to-the-elements-that-can-cover-something)** (2026-09-16), with a handling table per finding. One further false-failure (a multi-part bed leaking into the token count) was found while scoping #63 and is recorded there as §R20.8.

**Date**: 2026-09-16 · **Verdict**: **SOUND WITH CONCERNS** — the sixth pass's Critical (#54) is closed, #56 and #57 are closed, and every cheap fix (#55, #58–#62) landed as a real clause rather than a sentence. No new Critical. Seven Moderate findings, all in the *scope* of the new rule and the spike's measurement rather than in the idea; each is a sentence of spec to fix before Phase 0d is coded. Full table, the assumption list and the pass log are in [`docs/reviews/plan_renderer_layout_redesign.md`](../../../reviews/plan_renderer_layout_redesign.md) §Seventh pass.

Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run · 🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

**On the author's critique of the sixth-pass wording.** Half right. The clause "the last-drawn element with ink there must belong to that component" was *underspecified*, not circular: the only tag-free reading consistent with step 2 is "is a token element", i.e. survived the two measured exclusions — and under that reading the bed cannot belong, because step 2 already removed it. §R19.1's "surviving ink" is pixel-for-pixel the same predicate (a pixel of token ink survives ⟺ the last-drawn element with ink there is a token element), so the revision formalised the clause rather than replacing it, then strengthened it with the count on visible ink and the survival floor. Nothing circular has moved: token membership is fixed by measured exclusions before any order is consulted, and the occluder set is *every* element, so no artist→token grouping is needed. **It closes the draw-order hole for opaque occluders whose colour the probe can see** — the two qualifiers are #63 and #68 below.

**Moderate — fold into the plan text before Phase 0d is coded**

- 🟡 **#63 Both self-asserted preconditions are over-scoped and fail on a correct painter.** (a) Opacity: the agent's halo (alpha 0.16) and its shadow disc (alpha 0.12, `renderer_layout_redesign/dashboard_style.py:340-341`) and the campfire bed's glow (alpha 0.30 / 0.42 in the mock) are translucent arena elements. Each is drawn *before* its own body, but at a shared zorder it is drawn *after* the token elements of every earlier square, so "every element drawn after a token element must be fully opaque" fails on every frame with an agent or a campfire. (b) One Axes: the canvas rectangle (`fig03_proposed_dashboard.py:138`, drawn in the `bg` Axes) has ink under the arena's extent, so "every element with ink inside the arena's extent must belong to the arena Axes" fails on every frame. **Fix:** scope (a) to elements drawn after a token element *whose isolated ink intersects that token's isolated ink*, scope (b) to elements whose ink intersects token ink, and pin bed zorder < token zorder so a bed's glow is never "after" a token.
- 🟡 **#64 The z-order of every arena overlay relative to tokens is unpinned, and the survival floor punishes it.** The agent's 2 px square outline (§R17.3 item 8) and the sense-footprint outlines (§D7.3, "foreground artists") have no stated zorder. Drawn *above* tokens: a footprint edge through a boundary square's token removes ~1.5 px × 20 px ≈ 7 % of a 322–336 px² token (false floor failure); the square outline's inner fringe sits 0.1–1.1 px from the four-way token's edge (token reaches 21.4 px from the square centre, outline inner edge at 22–23 px), costing ~1–2 % — at the cliff. The dangerous shortcut fix is to drop outlines from the *occluder* set, which re-opens #54 for the exact case it named. **Fix:** pin both below the token zorder (tokens never reach them, so no visual change), and require the negative controls to include an agent — outline present — in the two-mover and four-way squares, plus an E-cell footprint edge through an occupied square.
- 🟡 **#65 `SURVIVAL_MIN = 0.98` has a defended shape and an undefended value.** Correct = 1.000 is the right anchor. But 2 % is 6.4–6.7 px of a 322–336 px² token: "a single-pixel anti-aliased seam" only along ≤ 6 px of arc — a 1 px seam round the whole circumference is ~65 px ≈ 19 %. Apply the `out_of_card` precedent: the checkpoint records the **minimum** survival over the negative controls (single; two-mover with agent; four-way with agent; bed + token; footprint through square) and the **maximum** over an **M-F2 family** (bed inset 0.02 / 0.05 / 0.10 × cell), and shows 0.98 lies in the gap with margin. A single M-F2 at 0.10 × cell exercises the floor far from where a fringe case would land.
- 🟡 **#66 The minimap census transplants the floor to a different instrument.** Denominator = the *geometric* expected wedge; numerator = nearest-palette classification of the *composite* (CP-C's ΔE census). At a 24–29 px square the split dot is ~13 px across, a half-disc ~66 px² with ~33 px of edge, so a third to half of its pixels are blends with the white ring, the 0.8 px split line and the terrain tint — 0.98 of the geometric wedge is not reachable on a correct painter. Also "as many distinct occupant colours as the snapshot has *movers*": two predators are two movers and one colour (the hiding predator shares it plus a pip), so a correct painter fails. **Fix:** ground truth = distinct palette colours of the *kinds* present (§R17.5 item 1's discipline); measure the denominator with the same census on the isolated wedge, or pin a minimap-specific floor by the #65 sweep.
- 🟡 **#67 CP0.4's arena/non-arena split measures update cost, not draw cost.** `canvas.draw()` composes every visible artist in both arms; disabling the arena *update* leaves the arena's ~230 visible artists (100 grounds + beds + token parts) inside the "non-arena" number — and Q22 option 3 proposes holding 0.5× against that number. **Fix:** three arms — full; arena update off; arena Axes `set_visible(False)` — all reported, artist counts unchanged.
- 🟡 **#68 The rule cannot see an occluder whose colour is within `INK_DELTA` (8/255) of the probe's empty canvas** (all elements hidden → the figure facecolor). The ground square is `TRACK #ECEEEA`; the canvas is `#F2F3F0`, 6/5/6 apart. Figure 3 leaves the figure facecolor at matplotlib's white, so today the ground has ink (19/255) — but nothing pins that for Phase 2, and a build-once renderer that sets the figure facecolor to `CANVAS` silently makes "ground drawn over tokens" — one of the three cases §R19.1 names — undetectable. The same blindness covers any white occluder (a stale-slot "eraser", a neighbour's keyline at 1.06 h). **Fix:** a third precondition, failing not skipping — ground, every bed's base colour and the outline colour differ from the figure facecolor by > `INK_DELTA` per channel; add **M-F1g** (ground after tokens) so the blindness shows if present; add it as (d) to the "does not see" list.

**Low**

- 🟢 #69 `_ink_is_outline(mask, bbox, h)` tests the perimeter of the *element's* bbox (`render_layout_audit.py:427-433`), not "the square's own box" as §R19.1 step 2 says. Harmless today (every token part is filled; the keyline sits at `z − 0.05` below its token) — but say which, since a ring-shaped token part would silently leave the union.
- 🟢 #70 §D1.4 item 2 still reads "a fixed pool of `AxesImage` icon slots per view cell per layer" — stale against the vector decision eight lines below it.
- 🟢 #71 CP0.4's spike must implement §R17.3's composition to measure it, i.e. most of `cells.py`; say whether the spike's cell code is disposable or becomes `cells.py` (CP4 re-measures either way).
- 🟢 #72 Audit cost is still unstated (sixth pass, check 5): isolation is N + 1 renders per frame and `_draw_index` is an O(N) scan per pair, so ~230 visible arena elements cost minutes per V2 frame. Sort the Axes children once per frame; size CP2.8's frame sample for it.

**The three named checks.** §R19.2: the 5×5 derivation is correct — `pack()` sets `col_bottom = top + arena_h if band else bottom` (`fig03_proposed_dashboard.py:199`), so with a band the right column's height *is* the card's, and a smaller world does give it less; 314 / 726 / 486 / 314 and the 350 px minimap cap (`:176`) all reproduce, no maintained 5×5 config has a band or thermal, and a band without thermal at 5×5 fits (104 + 150 + 16 = 270 ≤ 314). §D1.2 items 2–3 now match Revision 18 and R18.5 asserts "never larger". §R19.3: the order is now runnable, the spike draws the right arena, one failure path terminates in a conditional Q22 with four costed options — #67 is the only defect and it is in what the split measures, not in the gate. Nothing in Revision 19 contradicts Revisions 17–18 or the committed Phase 0a–0c code; the one mismatch is #69's bbox wording.

**Assumptions**: ❓ Phase 2 keeps a figure facecolor that contrasts with the ground (#68). ❓ Bed, token and overlay zorders are strictly ordered bed < token, overlays below tokens (#63, #64). ❓ The correct four-way control with the outline present reads ≥ 0.98 (#65). Verified: `pack()`'s band/column coupling; the halo at `zorder = z` below the body at `z + 0.1` and the keyline at `z − 0.05`; the mock's keyline `lw = max(0.8, h/8)` centred (matches the #55 correction); the style sheet sets no figure facecolor; CP0.3b, CP0.4, CP2.6, Q21, Q22 and §D1.4's medium landed as full clauses; Known Bugs has no row on arena draw order beyond D1–D13; no user decision is re-opened; no config key, script or critical setting is touched.

**Cost of being wrong**: no data loss, no training run. #63, #64 and #66 as written fail Phase 0d's own negative controls on a correct painter — loud, hours — and the danger is the shortcut fix (drop outlines or translucent elements from the occluder set) that re-opens #54 silently. #67 could settle Q22 on a number that still contains the arena's draw. #68 is the one silent case, and it turns on a facecolor choice nobody has made yet.

Reviewed by: plan-reviewer

---

## Implementation Report — Phase 1 (CP1): the panel registry and the layout packer (2026-09-16)

> **Implemented by**: developer

### What this is, in plain words

The episode-video dashboard is being rebuilt because its panels currently print
on top of each other. This phase builds the two pieces that are supposed to make
that impossible rather than merely unlikely. Every panel now **declares** what it
needs — whether it is on screen for a given world, and the smallest box it can be
drawn in — and a **packer** turns those declarations into actual rectangles on the
1440 × 896 canvas. If the declarations cannot all fit, the packer raises
`LayoutOverflowError` before a single frame is drawn, instead of quietly
shrinking a panel or letting two boxes share pixels. Nothing is drawn yet: this
phase has no painters and does not import Matplotlib at all.

### Files changed (all new; nothing existing was edited)

| File | What it does |
|---|---|
| `src/environment/dashboard/__init__.py` | Package entry point. Exports the Phase 1 surface. |
| `src/environment/dashboard/layout.py` | `Box`, `Size`, `CardDemand`, `Layout`, `LayoutOverflowError`, `pack()`, the fallback ladder, and the structural validation pass. Figure 3's constants (`LEFT_W = 320`, `MIN_RIGHT_W = 440`, outer 24 / gap 16 / pad 16 / header 64, `ARENA_CELL_PX = ARENA_CELL_MIN_PX = 50`). No Matplotlib import. |
| `src/environment/dashboard/panels.py` | `PanelSpec`, `LayoutContext` (+ `from_params`), `FontMetrics`, the 19-entry registry, the completeness rule, the observed-vs-hidden rule, `_recording_flag`, `real_available`, and `present_cards()` which turns present panels into the packer's card demands. |
| `src/environment/dashboard/labels.py` | The V2-owned channel label table that overrides the frozen adapter's `DNG` with `HPR`, with positional `C0…C{V-1}` fallback off the standard 8-channel vector. |
| `tests/env/test_dashboard_layout.py` | 98 tests (see below). |

### How the registry declares a panel

A `PanelSpec` carries its identity (`key`, `group`, `order`, `kind`), the
observation names it is responsible for drawing (`breakdown_names`), and two
predicates: `present(ctx)` and `min_size(ctx)`. Per Revision 5 (§D7.7 item 1)
both take **only** a `LayoutContext`, which is built from environment params and
never from a recorded episode — so two episodes of one run pack identically. A
test inspects the signatures to keep it that way.

The observed-vs-hidden rule is encoded **structurally** rather than by a runtime
branch: an observed row and its hidden twin (`nutrition` / `nutrition_hidden`)
are two registry entries with mutually exclusive `present` predicates, so a
modality the agent cannot sense **cannot** produce a row captioned `OBS`. That is
the live defect D10 this replaces.

### The packer's algorithm

Three columns under a header. The left column is fixed at 320 px; the arena card
sits in the middle and is a **fixed** box of `view × 50 px` of drawing plus its
chrome, never a grow panel; the right column is whatever is left,
`right_w = 1040 − card_w`, which must clear 440 px. Each column stacks its cards
in declared order, and leftover height goes only to the two grow panels (the
minimap, capped at 350 px, and the thermoception card). When a sensor band is
present it runs from below the arena to the bottom margin, and the right column
is then measured against the **arena's bottom edge**.

Candidates are tried in the plan's fallback order — whole world at 50 px, local
window, shrink by 2 toward `local_view_size`, `compact` minimums, then raise — and
**every candidate is validated by the same code**, so the right column is checked
against whatever arena height that candidate chose. That single check subsumes
§R18.2 item 9 and covers all three routes to an arena height.

Output is split into `cards` (placed units, pairwise disjoint) and `panels`
(leaf boxes actually painted into, each inside its card and disjoint from its
siblings). The split is what lets the arena expose a drawing box of exactly
`view × 50` while the card that frames it is `view × 50 + 64`.

### Test results

`JAX_PLATFORMS=cpu pytest tests/env/test_dashboard_layout.py -q` → **98 passed** (9.9 s).

Pinned geometry, all asserted to the pixel and all reproducing the plan:

| | 10×10 (synthetic, thermal + band) | 5×5 (real maintained configs) |
|---|---|---|
| arena card | 564 × 564 | 314 × 314 |
| arena drawing box | 500 × 500 | 250 × 250 |
| right column width | 476 (min 440) | 726 |
| sensor band | 236 px, starting y = 644, 1056 wide | — (no band) |
| right column height | 564, against the 516 a thermal column needs | 816 |

The thermal-plus-band case is asserted on a **synthetic `LayoutContext`** and the
test says so, per finding #59. This was verified independently rather than taken
from the plan: all eight maintained configs were loaded through
`load_env_params(load_env_config(path))` and **every one has both sense ranges at
0**, so none has a sensor band. `test_no_maintained_config_has_a_sensor_band`
records that as an assertion, because the synthetic tests depend on it.

### Mutation result — the overlap check is shown to bite

CP1 fails if boxes intersect, so the suite must be able to detect an overlap. The
packer was mutated in two ways at once: columns advance by **less** than the gap
(so consecutive cards overlap by 32 px), **and** the packer's own overlap check
is disabled — i.e. a packer that permits an overlap and does not complain.

**Result: 16 failed, 82 passed.** The tests that catch it are
`test_no_two_cards_share_a_pixel` (all 8 contexts) and
`test_every_maintained_config_packs_and_is_complete` (all 8 maintained configs).
They catch it because they recompute the pairwise overlap themselves rather than
asking `pack()` whether it was happy. Restored afterwards: 98 passed.

**Disclosure, because a silent near-miss here would be worthless:** my *first*
mutation attempt reported "1 failed, 97 passed" and I nearly recorded it. It was
invalid — the `sed` pattern carried the wrong indentation, so the overlap was
never introduced and only the disabled-check half applied. The numbers above are
from the corrected run, with both mutations verified present in the file before
the suite ran.

### CP-G (standing gate)

`scripts/eval/v1_path_guard.py check`, run **before** and **after** implementation,
both times: `PASS=10, ACCEPTED=0, ATTRIBUTED=0, UNATTRIBUTABLE=0`, plus
`FRAMES PASS` on M1, M2 and M4, `RESULT: OK`, **exit 0**. No frozen file was
edited, and no `renderer_v2` package or module was created.

### Speed check — skipped, with reason

Skipped. Phase 1 is pure Python with no Matplotlib import, runs **once per
episode** before any frame exists, and is imported by nothing on the training or
eval path — no `src/` module, script or test outside this phase references the
package. There is no hot path it can touch. The renderer's speed gate is CP0.4,
which is a Phase 2 precondition and is unaffected by this phase.

### Deviations and underspecifications — none silent

1. **The two pod heights the plan never pins, and why they are not free (please review).**
   §D1.1 gives only qualitative min-size drivers for the spectrum-smell pod, the
   range-0 vision pod and the location row, and Figure 3 never draws any of them
   because it always has a sensor band. My first values (138 / 158 / 62) made the
   **real maintained campfire config M4 overflow its right column by 28 px** — a
   genuine finding, not a typo. With no band the right column has 816 px, of
   which Figure 3's own pinned pods already claim 548 (prop 104 + extero/collision
   row 150 + thermoception 230 + 4 gaps), leaving **268 px for the smell and
   vision pods together**. I set them to 118 and 134 (252, so 16 px spare) and
   location to 46, documenting the derivation in the source. These are the
   numbers most likely to move when Phase 2 measures real text, and the budget is
   tight enough that `senior-developer` should confirm the split.
2. **Band selection follows Figure 3, not §D7.1's two-step evaluation.** §D7.1 says
   layout (a) is used iff every grid-kind sense meets its `min_size` there,
   otherwise (b). Figure 3's own `registry()` instead makes the band
   unconditional on a grid-kind sense being present. I implemented Figure 3's
   rule, because it is the canonical reference **and** because the two-step
   reading breaks one of this plan's own pinned tests: with a fallback to the
   side column, the synthetic 5×5 thermal-plus-band case would find a side column
   that fits and therefore would **not** raise, contradicting §R19.2. The fallback
   ladder still records which step succeeded.
3. **`__init__.py` cannot yet export `EpisodeRenderer` / `render_dashboard_frame`.**
   The Phase 1 File Changes row names them, but they are defined in `episode.py`,
   which is Phase 2. Exporting them now would make the package unimportable. The
   docstring records that they join the exports in Phase 2.
4. **`tests/env/test_dashboard_v1_imports.py` is deferred to Phase 2** (listed in
   the Phase 1 rows). Its substance is Phase-2-dependent: it pins the signatures
   of V1 helpers that only the Phase 2 painters import, and its cache-isolation
   check requires *rendering a new-renderer M4 frame*, which is impossible with
   no painters. Its one Phase-1-checkable clause — that no `renderer_v2` package
   was created — is already covered by CP-G, which passes. Flagged rather than
   silently skipped; `senior-developer` to confirm the deferral. *(Verifier: deferral accepted with one correction — see the Phase 1 Verification Report. The clause is **not** covered by CP-G; it is true today and was confirmed directly.)*
5. **`min_size` takes only `LayoutContext`**, per Revision 5 §D7.7 item 1, which
   supersedes §D1.1's `(RenderContext, FontMetrics)` signature. `FontMetrics`
   exists as a type so Phase 2 can supply measurements without a signature change.
   Phase 1 measures no text — every pinned height is a Figure 3 constant.
6. **One completeness-rule exemption, which the plan implies but does not state.**
   A panel drawn as observed must have its name in the breakdown — except the
   hidden-state kinds. The body-temperature row exists whenever the world has a
   body temperature and reads "not observed" when the agent cannot sense it
   (cell M4b), so it legitimately owns a name that is absent from the breakdown.
   Without the exemption the rule rejects M4b.
7. **Cards versus leaves.** The plan says `pack()` returns `dict[key -> Box]`. I
   return both, because the arena needs a drawing box of exactly `W × 50` inside a
   card of `W × 50 + 64`; a single flat dict cannot express both without one
   containing the other and tripping the disjointness check.
8. **`PanelSpec.extract` is declared but `None` everywhere.** It is part of a
   panel's identity per §D1.1, and Phase 2 fills it; nothing calls it yet.

### Prior art

Checked `docs/develop/active/issues/KNOWN_BUGS.md` directly (sub-agents cannot
spawn `bug-curator`). Rows 116–118 already record this dashboard's defects
(D1–D13, the "observed" mis-captioning D10, and the renderer housekeeping
hazards) and all three already point at this plan. Nothing new was found and no
row needs updating for this phase.

### Blockers and follow-ups

- **Nothing blocks Phase 2's layout work.** Two gates the plan already sets still
  stand: **CP0.4** must be met or escalated-and-answered before Phase 2 writes a
  painter, and **Q21** (does the World map still earn its place?) must be answered
  before Phase 2 starts the minimap. Phase 1's pinned numbers rest on keeping it
  at `LEFT_W = 320`.
- **For `senior-developer`:** items 1 and 4 above are the two that want a decision
  rather than just a read.

---

## Verification Report — Phase 1 (CP1): the panel registry and the layout packer (2026-09-16)

> **Verified by**: senior-developer

### What was checked, in plain words

Phase 1 is the first actual code of the new episode-video renderer, and its entire purpose is one claim: that two dashboard panels printing on top of each other becomes **impossible by construction**, not merely unlikely. Panels declare the room they need, a packer turns those declarations into rectangles, and a budget that cannot close raises an error before any frame is drawn. A claim like that cannot be verified by reading the code and agreeing with it — a packer whose tests ask the packer whether it overlapped would pass every review and protect nothing. So the claim was attacked: the packer was deliberately broken in three different ways and the suite was required to notice each time. It did. Separately, the one number in this phase that a real world nearly broke — how much height the smell and vision pods may take — was re-derived from the configs rather than taken from the report, and one disagreement between two sections of this plan was settled by measurement rather than by reading.

**Verdict: VERIFIED WITH ISSUES.** CP1's own five failure conditions are met and are each demonstrably catchable. One issue blocks the **commit** rather than the checkpoint: running the whole `tests/env` suite is now red, because Phase 1's new package trips a Phase 0 test that assumed no such package existed.

### The central claim, attacked three ways

Each mutation was applied to `layout.py` by script, **proved live by a probe before the suite ran** (the developer's own first attempt was a no-op `sed`, so a mutation that is merely believed to be present is worth nothing), then reverted with a sha256 check that the file returned to its original bytes.

| Mutation | What was broken | Probe that proved it live | Suite result |
|---|---|---|---|
| **A — overlap** | columns advance by `h − 32` instead of `h + GAP` (32 px of overlap) **and** `_validate`'s card-intersect check disabled | 6 overlapping card pairs computed independently on the default world, e.g. `minimap`/`vitals` sharing 320 × 32 px | **16 failed, 82 passed** — `test_no_two_cards_share_a_pixel` (8 contexts) + `test_every_maintained_config_packs_and_is_complete` (8 configs) |
| **B — a declared panel never placed** | `stack` flow drops its last child **and** `_validate`'s missing-panel check disabled | `intero_nociception` declared present but absent from the placed panels | **8 failed, 90 passed** — `test_every_present_panel_gets_a_box` (8 contexts) |
| **C — overflow does not raise** | all three overflow raises (`rw < MIN_RIGHT_W`, `need > avail`, band height) **and the entire `_validate` pass** disabled | the synthetic 5×5 thermal-plus-band world packs **silently**, no exception | **4 failed, 94 passed** — the four tests that require a raise |

The developer's reported 16 / 82 for mutation A **reproduces exactly**, including which tests fire. They fire because they recompute the pairwise overlap themselves rather than asking `pack()` whether it was happy — the property that makes the suite worth having.

**One honest detail about mutation C.** A first, weaker version — the three overflow raises disabled but `_validate` left in — still raised, from a *different* guard (`panel … escapes its card`), and two tests still went red because the message no longer names the right column. The packer's refusal is therefore **over-determined**: several independent guards catch the same bad budget. That is a strength, but it means "overflow raises" can only be falsified by disabling the validation pass as well, which is what version C does. Both runs are recorded so the margin is visible rather than implied.

### The pod-height budget (Implementation Report deviation 1) — confirmed, re-derived, and tightened

Re-derived by packing **all nine** maintained configs, not by repeating the arithmetic:

- The binding worlds are the campfire thermal world **and** the sensory-noise world — the report names only the first. Both have thermal on and both sense ranges at 0, so the right column carries five pods: need **800 px** against **816 px** available, **16 px spare**. Every other maintained world lacks the thermoception card and has 262 px spare.
- **The `location` row is not part of this budget.** It is a `world`-group panel and is charged to the **left** column (which has 76 px spare in the binding worlds), and no maintained config observes `Location` at all. The report's "118 / 134 / 46" framing implies all three compete for the same 268 px; two of them do.
- Sensitivity, measured: holding vision at 134, the smell pod overflows the campfire world at **135 px** — a **+17 px** margin on a single panel.

**Is 16 px enough? No, not as a standing margin — but the values are accepted as provisional.** 16 px is about 2 % of the column and these are the two numbers in the phase least anchored in Figure 3 (which never draws either pod). What makes this worth acting on rather than noting is the **failure mode**: `compact` deliberately does not shrink right-column pods, so a Phase-2 measurement that pushes the pair past 268 px makes `pack()` raise on a **real maintained world** — the renderer refuses to draw the campfire video — rather than degrading. The split is **not** re-cut now, because re-cutting it before Phase 2 measures real text would be swapping one unmeasured number for another. Instead §D1.1 now pins all three heights, states the 268 px joint budget and the 16 px margin, and places two requirements on Phase 2: a test that pins the budget so it fails *naming the budget*, and a stop-and-report rule if the measurement exceeds it. One naming point is recorded there too: the range-0 vision pod is given collision's kind string `cross_bars` while §D1.1's table calls it "single-cell bars".

### The band-selection deviation (Implementation Report deviation 2) — the implementation is right; §D7.1 was wrong

Settled by forcing both layouts on the disputed context rather than by reading:

- forced **band**: raises `right column needs 516px, has 314px` — the behaviour §R19.2 pins;
- forced **side column**: **packs** (right column 726 × 816 px against the 624 px those pods need).

So §D7.1's two-step reading ("layout (a) unless a grid-kind sense misses its `min_size`") would have made this plan's own pinned 5×5 guard **fail to raise**. The implementation follows Figure 3 (`fig03_proposed_dashboard.py:172`), which is the canonical reference, and Figure 3's rule is also the only one consistent with §D7's purpose — a two-step rule would put a range-1 smell map in the narrow side column of every 10×10 world. **§D7.1 is corrected**, with the measurement recorded.

### The deferral (Implementation Report deviation 4) — accepted, with one claim corrected

Deferring `tests/env/test_dashboard_v1_imports.py` to Phase 2 is **sound**: its cache-isolation check requires rendering a V2 frame, which cannot exist without painters, and the V1 helpers it pins (`draw_boresight_diamond`, `save_jax_video`, `COLORS`, the thermal helpers) are imported by nobody until Phase 2. Two corrections:

1. **"Its one Phase-1-checkable clause is already covered by CP-G" is not accurate.** The guard hashes the **file** `src/environment/renderer_v2.py`; it has no assertion that a `renderer_v2/` **package** was not created alongside it, and such a package would leave the guard green. The clause is nonetheless **true today** — verified directly: `src/environment/` contains `renderer_v2.py` and no `renderer_v2/` directory.
2. **One pinned V1 signature is already imported at Phase 1**, not Phase 2: `panels.py` imports `get_observation_breakdown` from the frozen `sensor.py`. It is exercised de facto (the suite loads nine real configs through `LayoutContext.from_params`), but it is not *pinned*. Phase 2's `test_dashboard_v1_imports.py` must cover it.

### The confirmations requested

| Claim | Result |
|---|---|
| No Matplotlib in the package | ✅ asserted in a subprocess, and `import matplotlib` appears nowhere in the four files |
| `present` / `min_size` take only a `LayoutContext` | ✅ pinned by signature inspection; the observed-vs-hidden split is two registry entries with mutually exclusive predicates, so it is structural, not a runtime branch |
| All maintained configs pack | ⚠️ **eight of nine.** `03-random_init_10x10_ckpt1k.yaml` is absent from the test's `MAINTAINED` list. It packs identically to `03-random_init_10x10.yaml` (verified), so this is a coverage gap, not a defect |
| Synthetic thermal-plus-band context used **and labelled** (#59) | ✅ every such test says SYNTHETIC in its name or docstring and says why no config produces it; `test_no_maintained_config_has_a_sensor_band` pins the premise |
| `v1_path_guard.py check` | ✅ `PASS=10, ACCEPTED=0, ATTRIBUTED=0, UNATTRIBUTABLE=0`, `FRAMES PASS` ×3, `RESULT: OK`, **exit 0** — re-run independently |
| Nothing staged | ✅ the Phase 1 files are untracked and unstaged. *(Note: `docs/develop/INDEX.md` and `SAVED_RUN_CONFIG_COMPAT.md` are staged by a **parallel session** — do not sweep them into the Phase 1 commit; use an explicit pathspec.)* |
| No frozen file touched | ✅ all ten clean in the working tree; no `renderer_v2` package |
| Vocabulary (`pain`) | ✅ zero hits in the package, comments included |

### ❗ Issue 1 (must fix before the Phase 1 commit): the full test suite is red

`pytest tests/env -m "not integration"` → **1 failed, 540 passed, 377 skipped**.

```
FAILED tests/env/test_render_audit_controls.py::test_audit_imports_neither_layout_nor_registry
AssertionError: audit pulled in the renderer package under test:
  ['src.environment.dashboard.labels', 'src.environment.dashboard.layout',
   'src.environment.dashboard.panels', 'src.environment.dashboard']
```

**Not a false alarm and not the audit's fault.** That Phase 0 test asserts `sys.modules` contains nothing matching `environment.dashboard`, which was a valid proxy for "the audit did not import the package" only while **no such package existed**. `tests/env/test_dashboard_layout.py` sorts before `test_render_audit_controls.py`, imports the package, and leaves it in `sys.modules` for the rest of the process. Reproduced minimally with just those two files; the audit-controls file **passes alone** (12 passed). The static half of the same test — that `render_layout_audit.py` contains no `import src.environment.dashboard` — still passes, so the audit's real isolation is intact.

**Fix (for `developer`, one file, Phase 0 test):** make the leak check process-local — run the audit import in a subprocess and inspect *its* `sys.modules`, the pattern `test_dashboard_layout.py::test_the_package_imports_without_matplotlib` already uses — or snapshot and restore `sys.modules` around the check. Do **not** weaken the assertion to a substring allow-list; the check is what keeps the audit independent of the thing it audits.

### File-by-file

| File | State |
|---|---|
| `src/environment/dashboard/__init__.py` | ✅ exports the Phase 1 surface; the `EpisodeRenderer` / `render_dashboard_frame` row of the File Changes table is correctly deferred with the reason in the docstring |
| `src/environment/dashboard/layout.py` | ✅ Figure 3's constants, arena a fixed `W × 50` box, one validation pass over finished boxes. ⚠️ minor: `_validate`'s docstring says cards sharing a box "are compared by identity of their region", but the code exempts any two cards whose **boxes are equal** — a geometric exemption, not a structural one. Unreachable today (a second band card raises), but it means two cards sharing *every* pixel would pass both the packer and the test helper, which copies the same exemption. Tighten to `card.region == "band"` in Phase 2 |
| `src/environment/dashboard/panels.py` | ✅ registry, completeness rule, observed-vs-hidden as mutually exclusive entries, `_recording_flag` confined to the package (pinned by an AST test, not a grep). ⚠️ the two pod heights, handled above |
| `src/environment/dashboard/labels.py` | ✅ `DNG` → `HPR` override with the off-standard positional fallback; `sensor.py` untouched, so V1 keeps `DNG` and the byte-identity guard stays meaningful |
| `tests/env/test_dashboard_layout.py` | ✅ 98 pass, reproduced; the three CP1 conditions are each independently catchable. ⚠️ one maintained config missing from `MAINTAINED` |
| `docs/.../RENDERER_LAYOUT_REDESIGN.md` | ✅ Implementation Report appended; +192 lines, no deletions beyond the CP1 checkbox |
| `tests/env/test_render_audit_controls.py` | ❌ unmodified but now **failing in a full-suite run** — Issue 1 |

### Speed check — skip accepted (✅ no regression possible)

Not measured, and correctly so. The package imports no Matplotlib, runs once per episode before any frame exists, and is imported by **nothing** outside itself and its own test — verified by grep across `src/`, `scripts/` and `tests/` (the only other mentions are the guard's path list and two Phase 0 tests naming the path as a *string*). There is no hot path it can touch. The renderer's speed gate remains **CP0.4**, a Phase 2 precondition.

### Out-of-scope changes

None. Every changed or added file is named in the Phase 1 File Changes rows, apart from the deferred `test_dashboard_v1_imports.py`. No script was added under `scripts/`, so `SCRIPTS_DEPENDENCY_MAP.md` correctly needs no row. No config key was added or changed, so `CONFIG_CRITICAL_SETTINGS.md` correctly needs no change-log entry.

### Conclusion

**VERIFIED WITH ISSUES.** The phase does what it claims: overlap is structurally prevented, and that is shown by breaking the packer three ways and watching the suite go red each time rather than by trusting the packer's own report. CP1 stands. Before the Phase 1 commit, Issue 1 must be fixed (one Phase 0 test), and the two ⚠️ coverage items — the missing maintained config and the box-equality exemption — should be folded in at the same time. §D1.1 and §D7.1 have been corrected in this plan; Phase 2 carries the pod-budget requirements recorded in §D1.1.

**Verified by: senior-developer**

---

## Implementation Report — CP1 fix-up: the blocker and the two coverage findings (2026-09-16)

> **Implemented by**: developer

### What this is, in plain words

The CP1 verification passed the work but stopped it from being committed, for one
reason and with two smaller notes attached. The reason: running the whole
`tests/env` folder in one go turned one test red, even though every file passed
when run on its own. The test in question is part of the *measuring instrument*
built in an earlier phase — a pixel audit whose job is to check the new dashboard
from the outside — and it asserts that the audit never loads the dashboard code
it is supposed to be measuring. That assertion was checking a list Python keeps of
"every module loaded anywhere in this program". While the dashboard package did
not exist, that list was a fair stand-in for "the audit did not load it". Once
Phase 1 created the package, a *different* test file — which runs earlier in the
alphabet — loaded it perfectly legitimately and left it in that shared list, so
the audit was blamed for an import it never made.

This change makes the check ask the question in a place where only the audit can
answer it: a **fresh separate Python process** that imports nothing but the audit.
Nothing about what is demanded was relaxed — the answer must still be an empty
list. The two smaller notes were an exemption in the packer that let two panels
occupying *exactly* the same rectangle slip past the overlap check, and one of the
project's nine maintained world configs missing from the test list.

### The blocker: the leak check is subprocessed, never loosened

The constraint here was explicit and it shaped the fix: that assertion is what
stops the instrument from sharing code with the thing it measures, so a version
that goes green because it was weakened would be worse than the red. **No
allow-list, no substring exemption, no `sys.modules` snapshot-and-restore.** The
check now spawns a subprocess that puts only `scripts/eval/` on its path, imports
`render_layout_audit`, and reports the leaked module list as JSON. The parent
asserts that list is **empty, exactly** — the same demand as before, asked where
the answer is not contaminated by whatever else the pytest session imported.

The pattern is the one Phase 0c already established for the Matplotlib-free
check in `test_dashboard_layout.py::test_the_package_imports_without_matplotlib`,
which the Phase 1 developer wrote as a subprocess for exactly this reason.

**The probe is also checked for blindness, in the same subprocess.** After taking
the measurement it imports the dashboard package *on purpose* and measures again,
and the test asserts that second list is non-empty. Without this, a probe that had
gone blind — the package renamed, moved, or made unimportable — would report "no
leak" forever, and an empty result from a blind probe is evidence of nothing. This
is the same discipline the audit-controls file already applies to itself: a
control set measures sensitivity, so discrimination has to be pinned separately.

The **static half** of the test (that the audit's source contains no
`import src.environment.dashboard`) is untouched and still runs.

#### Proof that the repaired check still bites

A check that passes is worthless until it has been shown capable of failing. The
audit was mutated to genuinely import the package — via
`importlib.import_module("src.environment.dashboard")`, a form the *static* half
cannot see, so that only the repaired dynamic half could be what fires.

| Step | Result |
|---|---|
| **A. Mutation proved live before the suite ran** | the probe subprocess returned `['src.environment.dashboard', '…labels', '…layout', '…panels']` — 4 modules |
| **B. Static half stays silent** | `grep -c` for both banned substrings = **0**, so the failure is attributable to the subprocess check alone |
| **C. The test under mutation** | **FAILED**: `audit pulled in the renderer package under test: [...4 modules]` |
| **D. Revert** | sha256 `cfa84cc3faf9f0b4…` **identical** before and after; `git status` on the file is clean |
| **E. The test after revert** | **1 passed** |

`scripts/eval/render_layout_audit.py` is plan-owned, **not** one of the ten frozen
V1-path files (confirmed against the guard's own list before touching it), and it
is byte-identical now.

### Finding 2: the equal-box exemption is a hole, and it is removed

**Decision: removed outright, not re-keyed.** The verification suggested tightening
it to `card.region == "band"`; I did not, because on inspection there is **no
legitimate case for it to serve**, and a structural key would preserve an
exemption for a situation that cannot arise:

1. The exemption's stated purpose was "the band's single card". A **single** card
   cannot pair with itself — the check is a pairwise loop over distinct keys — so
   the case it was written for could never reach it.
2. Two band cards *would* have shared a box, because every band card was assigned
   the same `band_box`. But the packer already refuses a second band card. The
   refusal simply happened **after** the boxes were handed out, which is what made
   the exemption look necessary. I moved that raise **above** the assignment loop,
   so "no two cards share a box" is now true by construction rather than patched
   up afterwards.
3. As written the exemption was keyed on the boxes' **coordinates** matching, so it
   exempted *any* two cards that happened to coincide, whatever they were — and two
   cards occupying exactly the same rectangle is the most complete overlap
   possible, not a special case.

**The test helper no longer mirrors the implementation.** `_overlapping_pairs` had
copied the same `if boxes[a] == boxes[b]: continue`, which is the failure mode the
verification flagged: a helper that agrees with the packer by construction cannot
catch a mistake in the packer's rule. It now reports identical boxes as
overlapping, and three new tests pin the whole business independently:

- `test_the_overlap_helper_itself_flags_two_identical_boxes` — the check on the
  checker. If the helper still had the exemption, every geometry test in the file
  would pass against a packer that stacked two cards on one rectangle.
- `test_two_cards_with_the_same_box_are_rejected_rather_than_exempted` — asserts
  `_validate` raises, on a **hand-built** `Layout` rather than a packed one,
  precisely because no real context can reach this state; a test that only packs
  real configs could never see the hole.
- `test_a_second_band_card_is_refused_before_a_box_is_assigned` — pins the refusal
  that makes the exemption unnecessary.

### Finding 3: the ninth maintained config

`configs/environment/experiment/basic/03-random_init_10x10_ckpt1k.yaml` is added to
`MAINTAINED`, so the two parametrised suites now cover **nine of nine**. It is a
thin training-only override (checkpoint frequency and retention) that `extends:`
`03-random_init_10x10`, resolved through the trainer's loader exactly as the other
eight are. **Confirmed to pack**, identically to its parent:
`arena Box(x=360, y=64, w=564, h=564)`, 9 cards, `step=whole_world`, no sensor band.

### Test results — every count

Run with `JAX_PLATFORMS=cpu`. Full log: `tmp/20260916_223523_cp1_fixups.log`.

| Run | Before this change | After |
|---|---|---|
| **The reproducer** — `test_dashboard_layout.py` + `test_render_audit_controls.py` together | **1 failed**, 109 passed, 26 deselected | **141 passed**, 0 failed |
| `tests/env/test_dashboard_layout.py` | 98 passed | **103 passed** |
| `tests/env/test_render_audit_controls.py` | 38 passed | **38 passed** |
| `tests/env/test_v1_path_guard.py` | 71 passed | **71 passed** |
| **whole `tests/env`**, `-m "not integration"` | **1 failed**, 540 passed, 377 skipped | **546 passed**, 0 failed, 377 skipped, 26 deselected |
| **whole `tests/env`**, no marker filter | — | **572 passed**, 0 failed, 377 skipped |
| `scripts/eval/v1_path_guard.py check` | 10/10 PASS | **PASS=10**, ACCEPTED=0, ATTRIBUTED=0, UNATTRIBUTABLE=0, **FRAMES PASS ×3** (M1/M2/M4), `RESULT: OK`, **exit 0** |

The blocker was **reproduced first with just the two files** (1 failed / 109
passed), before anything was changed, so the failure was in hand rather than
inferred.

**Where the +5 tests come from**, so the number is not mysterious: 98 → 103 is the
3 new tests above, plus 2 parametrised instances from the ninth maintained config
(`test_every_maintained_config_packs_and_is_complete` and
`test_no_maintained_config_has_a_sensor_band`). The full-directory count rises by
6: those 5, plus the 1 test that was failing and now passes.

The guard was run **twice** — once before the doc edits and once after the audit
mutation was reverted — green both times.

### Speed check — skipped, with reason

Skipped, and it provably cannot matter. Two of the three files are tests. The one
`src/` change is inside `layout.py`, which imports no Matplotlib, runs **once per
episode** before any frame exists, and is imported by nothing on the training or
eval path — a property the CP1 verification confirmed independently by grep across
`src/`, `scripts/` and `tests/`. The change itself removes two lines of work from a
validation pass and hoists one existing guard earlier; no training step,
environment step, model, or training-consumed config is touched. The renderer's
speed gate remains **CP0.4**, a Phase 2 precondition.

### Deviations from the brief — one, stated

**Finding 2 was resolved by deletion rather than by the re-keying the verification
proposed.** The brief allowed either ("say precisely what the case is, and make the
exemption structural … or it is a hole and should go"); I concluded it is a hole,
for the three reasons above, and the packer change that makes deletion safe — the
band-card refusal moved ahead of box assignment — is a **source** change in
`_pack_once` beyond the literal `_validate` edit. It is three lines moved, no
behaviour added, and it is what lets the overlap check run with **no exemption at
all**. Flagged because `senior-developer` proposed the other option.

### Scope

Three files, all already owned by this plan: `src/environment/dashboard/layout.py`
and `tests/env/test_dashboard_layout.py` (Phase 1 File Changes rows) and
`tests/env/test_render_audit_controls.py` (the Phase 0 test the verification names
as the fix site). No new file, no config key, no change under `scripts/` — so
`SCRIPTS_DEPENDENCY_MAP.md` and `CONFIG_CRITICAL_SETTINGS.md` correctly need no
entry. Frontmatter is unchanged (`last_updated` was already 2026-09-16), so
`INDEX.md` needs no regeneration — deliberately, since a parallel session has it
staged. **Nothing is staged or committed**; the only staged paths in the repo are
that parallel session's `docs/develop/INDEX.md` and `SAVED_RUN_CONFIG_COMPAT.md`,
untouched. None of the ten frozen V1-path files was modified and the guard's
`accept` was never run.

### Prior art

Checked `docs/develop/active/issues/KNOWN_BUGS.md` directly (sub-agents cannot
spawn `bug-curator`), grepping for the dashboard, `sys.modules` and import-order
hazards. Row 116 records this dashboard's defects (D1–D13) and already points at
this plan; nothing there covers test-order pollution. **One judgement call for
`senior-developer`:** the hazard class — a test asserting on process-global
`sys.modules` silently becoming order-dependent when a new package appears — is
not recorded anywhere, and it will recur in Phase 2 when the package grows. I did
not add a row, since the instance is fixed in this same change, but if you think
the class is worth recording, `bug-curator` owns that call.

### Blockers and follow-ups

- **None blocking.** The Phase 1 commit is unblocked: the full `tests/env`
  directory is green and CP-G passes.
- Unchanged from the CP1 report: **CP0.4** must be met or escalated before Phase 2
  writes a painter, and **Q21** must be answered before the minimap work. The pod
  budget (16 px spare in the two binding worlds) carries into Phase 2 per §D1.1.

Implemented by: developer

---

## Implementation Report — Phase 2 (first complete frame): the painters, the square composition and the episode renderer (2026-09-16)

> **Implemented by**: developer

### What this is, in plain words

The dashboard now draws. Phase 1 built the part that decides *where* each panel
goes; this phase builds the part that puts ink in those boxes, and it ends with a
complete 1440 × 896 frame of the campfire world rendered from a real recording.

The defect it exists to remove is specific. A square of the world can hold more
than one thing at once, and the old renderer drew every occupant on the same
centre point, so one covered the other: **an agent standing in a bush rendered as
an agent alone**. The fix the user chose (variant H) stops treating terrain as a
picture in the middle of the square and makes it the square's **floor** — a bush,
rock, tree or campfire is ground cover filling the square, and the occupants
stand on it. Because the floor costs the occupants no room, a lone agent on a
bush is drawn at exactly the size it would be on empty ground, and two occupants
stand side by side in a band across the middle.

That is not asserted here, it is measured. On the rendered campfire frame, the
square holding the agent **and** a bush now shows both: the bush keeps 55 % of
its own ink and the agent keeps **100 %** of its own. On a later step, a square
holding the agent and a piece of food shows two separate drawings, each keeping
**100 %**, and a rabbit standing on a rock keeps 100 % while the rock keeps 60 %.

### Files changed

| File | What it does |
|---|---|
| `src/environment/dashboard/cells.py` (new) | The composition of one square: `CELL_PRIORITY`, `BED_MARGIN`, the slot packer, the bed forms, the companion token forms, the identifying-mark fractions, the chevron floor, and the pinned depths (bed < token, square outline < token, footprint < token). All vector primitives; no raster. |
| `src/environment/dashboard/painters.py` (new) | One painter per visual **kind** — header, the merged vitals card, the World map, the arena, the action pill, action chips, a spectrum, an intensity pod, cross bars, channel bars, the thermoception diamond with the frame's one shared temperature legend, a text row. Each builds its artists once and returns an update callable. |
| `src/environment/dashboard/episode.py` (new) | `EpisodeRenderer` (setup / `frame` / `close` / `layout_signature`), `render_dashboard_frame`, the recording→frame adapter, and `occupancy_of` (which square holds which **kinds**). |
| `src/environment/dashboard/palette.py` (new) | The named colour tokens and the colour → meaning map CP-C will read. Pins `FIGURE_FACECOLOR` white, deliberately **not** `CANVAS` (§R20.6). |
| `src/environment/dashboard/thermal.py` (new) | The episode-anchored temperature scale (Q17), **copied** from the approved sketch rather than imported from the frozen renderer, whose scale is a different design. |
| `src/environment/dashboard/style.py` (new) | Type roles, the vendored font loader, and the two drawing primitives. The px→pt conversion lives here once. |
| `src/environment/dashboard/text_fit.py` (new) | `fit_text`: numeric text raises at the legibility floor, free text (the header only) ellipsises and logs. |
| `src/environment/dashboard/__init__.py` | The two drawing-side names are exported **lazily** (see deviation 6). |
| `tests/env/test_dashboard_cells.py` (new) | 20 tests: the pinned slot geometry, both square floors re-derived, the tables, the depth pins, the one-artist bed rule. |
| `tests/env/test_dashboard_v1_imports.py` (new) | 7 tests: the frozen helpers' signatures, the diamond-offset order, and — in a subprocess, with a blindness check — that this package never imports the frozen renderer. |
| `tests/env/test_dashboard_layout.py` | +1 test pinning the campfire world's right-column budget (800 of 816 px), which §D1.1 requires of Phase 2. |

### The frame, and what is in it

`M4` (the maintained campfire thermal world), episode 2, rendered from the real
fixture recording. Layout: `step=whole_world`, 10 × 10 squares at **50 px**, so
the arena's drawing box is exactly 500 × 500 inside a 564 × 564 card — the
geometry Phase 1 pinned, reached by a real config rather than a synthetic one.

Two frames were rendered and **looked at** at full size:

* **step 0** — contains the archetype this design exists for: square (4,3) holds
  `agent + bush`.
* **step 32** — contains two shared squares: (5,1) `agent + food` (two occupants
  in slots) and (3,5) `neutral + rock` (a token standing on a bed).

Written to `tmp/20260916_dashboard_frames/`. They are scratch, not committed.

### Test results

| Command | Result |
|---|---|
| `pytest tests/env/test_dashboard_cells.py -q` | **20 passed** |
| `pytest tests/env/test_dashboard_v1_imports.py -q` | **7 passed** |
| `pytest tests/env/test_dashboard_layout.py -q` | **104 passed** (was 103; +1 budget test) |
| `pytest tests/env -m "not integration" -q` | **574 passed**, 377 skipped, 26 deselected (was 546 — exactly +28, the new tests) |
| `pytest tests/env -q` | **600 passed**, 377 skipped (was 572 — the same +28) |
| `scripts/eval/v1_path_guard.py check` | **PASS=10**, ACCEPTED=0, ATTRIBUTED=0, UNATTRIBUTABLE=0, **FRAMES PASS ×3** (M1/M2/M4), `RESULT: OK`, **exit 0** — run before and after |

One pin earned its keep immediately: `test_sensor_helpers_keep_their_signatures`
failed on first run because I had typed `get_observation_breakdown`'s signature
from memory instead of measuring it (it carries a type annotation). That is the
test doing its job on its author.

### The audit, run on the rendered frames

The audit cannot name this renderer — `render_capture` knows `v1` and the dormant
`v2` only — so a scratch harness hands it the frame already rendered and lets
**every rule run unchanged**. The audit file itself was not edited: it is a
plan-owned Phase 0 artefact whose isolation from the renderer package is under
test, and a `--renderer dashboard` arm is a change `senior-developer` should
schedule, not one to slip in here.

| Rule | step 0 | step 32 |
|---|---|---|
| `text_over_text` | **0** | **0** |
| `text_over_border` | **0** | **0** |
| `clipped` | **0** | **0** |
| `out_of_card` | **0** | **0** |
| `out_of_canvas` | **0** | **0** |
| `panel_absent` | **0** | **0** |
| `observed_caption` | **0** | **0** |
| `numeric_in_arena` | **0** | **0** |
| `text_over_fill` | 16 | 15 |

Every `text_over_fill` is a label drawn inside **its own** widget — an action
chip, a collision letter, a thermoception cell's number, the action pill — which
is the class the audit's own docstring describes as legible by design and
explicitly not one of its calibrated controls. Per the Correction Report's
recorded position, that class belongs to **CP0.3b** and is not tightened here.

**The audit found two defects I had not seen by eye**, which is the argument for
running it rather than looking:

1. `panel_absent: Visual` — I had titled the vision pod "Vision". The audit reads
   panel titles against a fixed table of breakdown names, so a synonym makes a
   panel that is plainly on screen report as missing. Fixed by titling it
   `Visual`, the breakdown's own word.
2. `observed_caption` on the word **"Observed"** — the vitals column head begins
   with `OBS`, and the rule requires any such text to belong to a panel whose
   modality is in the observation. A column head spanning five rows belongs to no
   single modality, so it can never satisfy that rule. See deviation 4.

It also caught both defects I *had* seen (the arena title printing through the
action pill, and the World map's caption crossing its own card edge), at the
pixel, with coordinates.

**Cost:** 45.2 s per audited frame at 708–710 elements, on this container. That
is the number CP2.8 asks to be stated for sizing its sample.

### Speed check — measured, and it lands in the plan's report-and-stop band

Same recording, same process, 40 frames with the first 5 excluded, on this
container (not a lab node, not a pool worker).

| | median | p95 |
|---|---|---|
| **V1** (production renderer) | **333.0 ms** | 505.8 ms |
| **V2** (this renderer) | **187.3 ms** | 202.1 ms |
| V2, arena Axes hidden (arm 3) | 176.1 ms | — |

**Ratio V2/V1 = 0.563.** Command:
`python tmp/20260916_2345_render_m4.py bench --cell M4 --episode 1 --frames 35`.

Three things follow, and none of them is mine to act on:

* The **hard floor holds comfortably** — the new renderer is 1.78× faster than
  the one training uses, so nothing regresses.
* The **0.5× gate on M4 is missed**, at 0.563×. §R19.3 pre-registers exactly this
  band (`0.5× < median ≤ 1.0×`): *report the split and the artist counts, ask
  **Q22**, and stop.* I have changed nothing — not the gate, not the square size,
  not the stack.
* The **split says the arena is not the cost.** Arm 1 − arm 3 = **11.2 ms** of a
  187 ms frame. With 1045 visible artists of which **178** are the arena's, the
  100-square arena is ~6 % of the frame; the remainder is the text-heavy cards.
  That matters for Q22, because option 3 ("hold 0.5× against the non-arena part")
  would be scored against a number that is almost the whole frame — the four-fold
  arena growth Q22 was opened about is **not** what is costing the time here.

**This is not CP0.4.** CP0.4 requires a lab node, a `ProcessPoolExecutor` worker,
≥ 200 frames, and the node and CPU model recorded. This is an indicative
in-container measurement. CP0.4 remains unrun — see Gates below.

### Deviations from the plan — none silent

1. **The agent's halo is dropped whenever the square holds anything else,
   including a bed — not only when `n ≥ 2` (§R17.3 item 8).** This is the one
   change that decides whether the phase's own goal is met. Measured: a lone
   agent's halo reaches `0.396 × cell` from the centre while the bed spans
   `0.72 × cell`, i.e. `0.36 × cell` from the centre. The halo is therefore
   **wider than the entire floor beneath it**, so under the literal rule (`n = 1`,
   because terrain does not count as an occupant) "agent in a bush" still
   rendered as an agent alone — the defect, not the fix. I verified this on a
   rendered frame before changing it. On a genuinely empty square the halo is
   kept: there it covers only bare ground and it makes the agent easy to find.
   **§R17.3 item 8 should be amended to "shared with any occupant or a bed".**
2. **Beds are a full-bleed plate with the terrain's texture on it, not the design
   mock's silhouettes.** §R20.8 requires a bed to be **one artist** whose ink the
   audit's ≥ 40 %-of-square test classifies as floor. The mock's bed forms are
   partial silhouettes: measured on the plate geometry they cover roughly 28–36 %
   for rock and tree, i.e. **under the line**, so ported as-is they would be
   counted as *occupants* and `cell_overdraw` would fire on a correct painter.
   The plan's own words for a bed are "drawn full-bleed, inset by `BED_MARGIN` on
   every side" (§R17.3 item 2), and that is what is implemented: `0.72²` = 51.8 %
   by construction. Measured on the real frame: **53.4 %** (bush) and **51.7 %**
   (rock) of the square. A test pins the plate fraction above 0.40.
3. **A bed is one artist and so is a token — and the token's keyline travels
   inside it.** Beds for §R20.8. Tokens because §R20.7 item 1 adds a failing
   guard for ink sitting on the perimeter of its own bounding box: a white
   keyline drawn as its own artist is exactly that shape, and would either be
   excluded from the count or reported as `outline_like_token`. Carried inside
   its token's compound form, it cannot be either. It also cuts the artist count:
   178 arena artists rather than the ~4,500 Figure 3's per-name glyph pool implies.
4. **The vitals column head reads "Sensed", not "Observed".** The audit rules
   that any rendered text beginning `OBS` must belong to a panel whose modality
   is in the observation — a rule that exists to catch a *value* captioned as
   observed when it is not (the live defect D10). A column head spanning five
   rows belongs to no single modality and can never satisfy it. The word is not
   load-bearing here: what carries the meaning is the per-row **"not observed"**
   text, which is unchanged and which the rule requires. **For
   `senior-developer`:** either §D5.2 item 7 should be scoped to value captions,
   or the head keeps a different word. I took the second, reversibly.
5. **The arena is two Axes** — the card's chrome (title, action pill) and the
   grid itself, labelled `arena`. The "no numbers inside the grid view" rule
   measures against the named Axes' extent, and the card's title legitimately
   reads "whole 10 × 10 world"; with one Axes that title would be a violation of
   a rule it does not break.
6. **`__init__.py` exports `EpisodeRenderer` and `render_dashboard_frame`
   lazily.** The Phase 1 File Changes row asks for them to be exported; a Phase 1
   test pins that a bare `import src.environment.dashboard` pulls in no
   Matplotlib. Both hold: a module-level `__getattr__` resolves the two names on
   first use.
7. **Painters are built in the closure style of Figure 3** (`build_*` draws once
   and returns an update callable) rather than as painter classes with
   `build`/`update` methods. Figure 3 is the canonical reference and this is its
   own shape; the interface obligation — build once, update per step — is met.
8. **The World map's square is 19.6 px, below the ~23–29 px §R17.2 quotes.** The
   shared-square caption §R17.4 requires is reserved out of the map's own size
   rather than drawn wherever it lands, because a caption falling off its card is
   a layout defect (the audit caught exactly that on my first frame). Two lines
   at 12 px cost the map ~4 px per square. Worth a look at CP-D, and it bears on
   **Q21**.
9. **The registry still calls the range-0 vision pod `cross_bars`** while a
   distinct painter (`build_channel_bars`) draws it. §D1.1 asks Phase 2 either to
   give it its own kind string or to record why one painter serves both. I did
   **neither in the registry**, deliberately: the kind strings are asserted by
   Phase 1 tests, so changing one is an act that should ride with its own test
   update rather than be folded into a first-frame pass. Recorded as a follow-up.

### What is deliberately NOT built yet

Stated so the frame is not mistaken for a finished renderer: no sensor-band
painter and no `channel_maps` (no maintained config has a sense at range ≥ 1, so
neither can be exercised on a real world); no footprint outlines for the same
reason; no `icons.py`; the ellipsis path of `fit_text` is reachable only from the
header. **`assets/dashboard_icons/` is not used at all** — every form in the
frame, including the World map's marks and the legend chips, is drawn from the
vector tables in `cells.py` and `palette.py`. Per §R19.4 item 1 that is the
recorded condition for **dropping that folder**, and I recommend dropping it.

### Gates — two standing ones are crossed, and I am flagging both rather than absorbing them

1. **CP0.4 has never been run, and it is a stated precondition for Phase 2
   writing a painter.** I wrote painters because the task instructed it
   explicitly. The indicative measurement above is what CP0.4 would have asked
   for in miniature, and it lands in the band where the plan says *stop and ask
   Q22*. **Nothing was tuned in response.**
2. **Phase 0d does not exist**, so `cell_overdraw` — the rule CP2.8 is defined in
   terms of — cannot be run. `scripts/eval/render_layout_audit.py` contains no
   `cell_overdraw`, no `SURVIVAL_MIN`, and CP0.3b is unticked. CP2.8 therefore
   **cannot be met today**, and I did not build a partial version of the rule: a
   half-built instrument that passes is worse than none.

   What I did instead is measure the substance by hand, in scratch, using §R19.1's
   own method (isolated ink per artist, then the pixels no later-drawn artist
   covers). On the campfire frames:

   | square | occupants | bed ink (share of square) | bed survives | token survives |
   |---|---|---|---|---|
   | (4,3) step 0 | agent + bush | 53.4 % | 55.1 % | **100.0 %** |
   | (3,5) step 32 | neutral + rock | 51.7 % | 60.5 % | **100.0 %** |
   | (5,1) step 32 | agent + food | — | — | **100.0 % / 100.0 %** |

   Every occupant measures the 1.000 §R19.1 says a correct composition must, and
   every bed clears the 40 % line that classifies it as floor rather than as an
   occupant. **This is evidence, not the instrument**, and it does not close
   CP2.8.

3. **Q21 is unanswered.** Built to the plan's recorded working assumption — keep
   the World map, `LEFT_W = 320` — and flagged rather than decided. Deviation 8
   is new information for that decision.

### On the CP1 band-card refusal (asked for specifically)

The fix-up hoisted the "more than one band card" refusal above box assignment in
`_pack_once`. **Nothing looks wrong with it, and I must be honest that my
painters did not exercise it.** No maintained world has a sensor band — every one
has both sense ranges at 0 — so every pack in this phase, including M4's, takes
the no-band path where `band_cards` is empty and the refusal is never reached.
What does exercise it is the synthetic thermal-plus-band contexts in the Phase 1
suite, and those pass (104 tests). Reading it against this phase's use: the hoist
is sound and is what lets `_validate` run with no exemption at all, because the
only way two cards could have shared a box was two band cards receiving the same
`band_box`. The band painter, when it is written, is where it will first be
exercised for real.

### Prior art

Checked `docs/develop/active/issues/KNOWN_BUGS.md` directly (sub-agents cannot
spawn `bug-curator`). Rows 117–119 record this dashboard's defects D1–D13, the
`OBS` mis-captioning D10 and the frozen renderer's housekeeping hazards, and all
three already point at this plan. Row 91 ("chasing rabbit stays glued to the
agent") is useful archetype context rather than a defect. **Nothing new to file:**
the halo-versus-bed finding (deviation 1) is a defect in *this plan's own rule
text*, caught before any code shipped, so it belongs in this plan and not in the
registry. If `senior-developer` disagrees, `bug-curator` owns that call.

### Blockers and follow-ups

- **For the user (via `senior-developer`): Q22.** The 0.5× gate is missed at
  0.563×, and the split shows the arena is 6 % of the frame — so the premise Q22
  was opened on (four times the arena content) is not what the measurement blames.
- **For `senior-developer`:** amend §R17.3 item 8 (deviation 1); rule on the
  `OBS` column-head question (deviation 4); schedule Phase 0d, without which
  CP2.8 cannot be met; decide whether the audit gains a `--renderer dashboard`
  arm or whether a harness stays the route; and answer **Q21** before the minimap
  work goes further.
- **Not done and not hidden:** CP2.1 is demonstrated on **two frames of one
  matrix cell**, not on every cell's checked frames; CP2.2–CP2.7 are untouched.

Implemented by: developer

---

## Implementation Report — Phase 0d / CP0.3b (2026-09-17)

### What this phase built, in plain words

The redesign exists because a square of the world holding two animals was drawn as
**one** animal. Phase 2 wrote painters that fix it, but nobody could *prove* it: the
measuring instrument for that specific claim had never been built, so checkpoint CP2.8 —
"squares render as many occupants as they hold" — could not be met. This phase built the
instrument. It is a new rule in the pixel audit called `cell_overdraw`, and for every
square of the grid it now measures three things rather than one:

1. **what was drawn** — the connected blobs of ink each occupant lays down on its own;
2. **what survives the painting** — the pixels where nothing drawn afterwards covers them;
3. **how much of each occupant survives** — because an animal that is 95 % hidden behind a
   bush still leaves one blob, and would sail through any test that only counts blobs.

The third is the one that matters most and is the cheapest to get wrong. A correct picture
scores exactly **100 %** on it, and everything below is tolerance.

**The headline result: the instrument agrees with Phase 2, exactly.** Run against the real
campfire-world frames, every occupant keeps **100.0 %** of itself, and the bushes and rocks
they stand on measure **53.44 %** and **51.68 %** of their square against the 53.4 % and
51.7 % Phase 2 measured by hand. There is **no disagreement to report**. Since one of the
two would have to be wrong if they differed, this is the outcome that matters.

**But CP0.3b is not ticked, and CP2.8 is not closed**, for reasons given in full below. The
short version: one *correct* picture — a lone agent standing on bare ground — is
misclassified by a constant the plan itself specifies, and moving that constant is the
plan's decision to make, not mine.

### File-by-file

| File | What changed |
|---|---|
| `scripts/eval/render_layout_audit.py` | The rule `cell_overdraw` (ground truth from the snapshot's distinct **kinds**; bed/ground excluded by measured area; outlines by `_ink_is_outline` with §R20.7's failing-direction guard; component counts on isolated **and** surviving ink; the per-component floor `SURVIVAL_MIN = 0.98`). All three preconditions, each **failing** rather than skipping and each scoped to `L(p)`, the last-drawn element with ink at a token pixel: **(a′)** a non-token `L(p)` must be opaque, **(b′)** it must belong to the arena Axes, **(c′)** no element of the arena may have all its declared paints within `INK_DELTA` of the figure facecolor. New `DrawOrder` class building the figure-wide rank `(axes rank, zorder, child index)` **once per frame**. `minimap_overdraw` (composite colour census, kinds-not-movers ground truth, denominator measured on the isolated wedge, shared-square caption). `occupancy_from_state`, `square_rects`, `_paints`, `_is_fully_opaque`, `_probe_blind_distance`, `_components`. New CLI flags `--cell-axes` and `--minimap-axes`. **Plus one fix to existing code** — see "a defect in the instrument itself". |
| `tests/env/test_render_audit_controls.py` | +29 tests: 8 negative controls, 6 mutation cases, the exact-1.000 assertion, the §R20.3 gap table, the cross-Axes comparator control pinned by pixels, the padded-bbox equivalence run, the 50 px adjacent-slot control, the `outline_like_token` guard, the Collection-enumeration regression, 4 minimap controls, and the palette-drift guard. One `strict` xfail (the lone agent). |

**No file outside the plan's Phase 0d File Changes list was touched.** In particular
`src/environment/dashboard/` was **not** edited — several findings below are painter
suggestions, and none of them was acted on. `SCRIPTS_DEPENDENCY_MAP.md` is unchanged, which
is what the plan's Phase 0d row specifies and what its Maintenance Contract requires (no
script added, moved, renamed or deleted; no caller changed). Its prose description of the
audit is now slightly under-complete — it does not mention the new rule or flags — which I
flag rather than fix, since the contract's trigger did not fire.

### The mutation table

A mutation is "before" and the same figure unmutated is "after": the audit must **fire** on
the mutation and be **silent** on the correct picture. Both directions were run, because a
rule that fired on everything would pass the left column alone.

| Mutation | Fires? | Via which rule | Same figure, unmutated |
|---|---|---|---|
| **M-E** all occupants forced to the square's centre | **YES** (3 findings) | `cell_overdraw` — 2 kinds, 1 component, plus overlapping token ink | silent |
| **M-F1** bed drawn after the tokens | **YES** (2) | `cell_overdraw` — 1 visible component where there is 1 kind, survival **0.000** | silent |
| **M-F1g** ground drawn after the tokens, facecolor `CANVAS` | **YES** (1) | `cell_probe_blind` **only** — precondition (c′) | silent |
| **M-F2** bed after tokens, inset 0.02 × cell | **YES** (2) | `cell_overdraw` survival floor — 0.101 / 0.144 | silent |
| **M-F2** inset 0.05 × cell | **YES** (2) | `cell_overdraw` survival floor — 0.143 / 0.198 | silent |
| **M-F2** inset 0.10 × cell | **YES** (4) | `cell_overdraw` disjointness (see note) | silent |
| **M-F3** minimap agent dot above the split wedge | **YES** | `minimap_overdraw` composite census | silent |

**M-F1g is the one that earns precondition (c′).** It is caught by nothing else: with the
figure facecolor set to `CANVAS`, the ground square's colour is 6/255 away from it, so the
ground lays down **no isolated ink at all** and can never be seen to occlude anything.
Without (c′) this mutation passes silently — which is exactly what §R20.6 predicted.

**Note on M-F2 at the 0.10 inset, which is a finding about the plan's own numbers.**
Insetting a bed shrinks it, and a bed's ink share is `(0.72(1−2i))²` → **47.8 % / 42.0 % /
33.2 %** at the three pre-registered insets. At 0.10 (and, at a 0.48 floor, also at 0.05)
the bed falls **under the floor test**, stops being classified as a bed, is read as a
token, and is caught by the disjointness rule instead of the survival floor. It still
fails — the mutation does not escape — but it no longer measures the thing it was
pre-registered to measure, so it is **excluded from the gap table's maximum with its
reason** rather than contributing a meaningless 1.0.

**One addition I made to the rule, and why it is not the forbidden shortcut.** Two token
elements of one square may not share a pixel. §R19.1 item 3 already states "pairwise
touching in 0 px" of the *components*; asserting it of the *elements* as well is what
closes a hole the component count cannot see at `|K| = 1`: an occluder that is itself
counted as a token **merges** with the token it covers, and one component over one kind
then passes a frame in which an occupant has been painted out. This only ever adds
failures, and nothing is removed from the occluder set.

### The `SURVIVAL_MIN = 0.98` gap table, and my verdict

| Side | Measured | Which control |
|---|---|---|
| Correct painter (floor must be **below**) | **1.000000** | minimum over **every** negative control — single occupant, empty, campfire bed + token, two movers **with the agent**, three-way, four-way **with the agent**, footprint edge through an occupied square, adjacent slots at 50 px |
| Defect (floor must be **above**) | **0.198444** | maximum over the M-F2 members that actually exercise the floor |

`SURVIVAL_MIN = 0.98` lies between them. **My verdict: it does not sit on a cliff, and I am
not moving it.** A sweep of the floor from **0.50 to 1.000** flips **no verdict on any
control** — every correct square stays silent and every occluded one keeps firing across
that entire range. The nearest boundary below is 0.198 and the nearest above is 1.000, so
0.98 sits inside a band 0.80 wide in which the instrument's answers are constant.

The one honest qualification: the margin on the **correct** side is only 0.02, and that is
**structural rather than worrying** — §R19.1's own argument is that a correct composition
measures exactly 1.000, so any floor below 1 is pure tolerance and *must* sit just under
it. Every negative control measured **exactly 1.000000**, including the four-way with the
agent, which §R20.2 flagged as the tightest case (0.1–1.1 px outline clearance, "right at
the floor"). It measures 1.000 because `cells.py` pins the square outline **below** the
tokens — §R20.2's painter fix, working as designed and now measured rather than reasoned
about.

### CP2.8 on the real frames

Run against the Phase 2 frames (`M4` episode 1, steps 0 and 32) through a scratch harness,
because `render_capture` still knows only `v1` and the dormant `v2`. **The audit file was
not edited to accommodate the new renderer.**

| | step 0 | step 32 |
|---|---|---|
| `cell_overdraw` findings | **0** | **0** |
| squares measured | 9 | 8 |
| occupancy ground truths agree | **yes** | **yes** |
| shared square | (4,3) `agent + bush` | (5,1) `agent + food`, (3,5) `neutral + rock` |
| every occupant's survival | **1.0000** | **1.0000** |
| `text_over_fill` | 16 | 15 |
| wall-clock per audited frame | 46.5 s (735 elements) | 46.3 s (737) |

The two-occupant square **(5,1)** measures **2 kinds → 2 isolated components → 2 visible
components → 1.0000 / 1.0000**, which is the whole claim of variant H, measured.

**Agreement with Phase 2's hand measurement: exact, with no disagreement.** Bed ink 53.44 %
(bush) and 51.68 % (rock) against 53.4 % and 51.7 %; token survival 100.0 % against
100.0 %. The audit derives occupancy from the recorded snapshot **itself**, and that ground
truth was checked square-by-square against the renderer's own `occupancy_of` — they agree
on every square of both frames, which is what makes this an independent reproduction rather
than the same computation run twice.

**CP2.8 still does not close**, for four reasons that are not the instrument's fault and
one that is a painter gap — all itemised in the CP2.8 checkpoint note above.

### A defect in the instrument itself, found by these controls

**Every `Collection` artist was silently dropped from the audit's element list, on every
frame, since Phase 0c.** `Collection.get_window_extent` returns an empty bbox
`(inf, inf, −inf, −inf)`, which `enumerate_elements` filtered out — and an artist that is
not an Element is **never hidden by `FrameProbe._draw`**, so it was painted into every
isolated render *including the bare background* and ate the ink of whatever it covered.
Measured: the page rectangle's isolated ink came out **665 px short**, exactly the area of
the two tokens sitting on top of it.

It matters twice. The redesign draws every bed and every token as **one** `PatchCollection`
(§R20.8 requires it), so `cell_overdraw` would have measured an arena with nothing standing
in it — which is precisely how I found it. And the **frozen V1 and dormant-V2 frames carry
17 visible `LineCollection`s each**, whose ink has been contaminating every isolation
measurement taken on them.

Fixed with a path-extent fallback. **The frozen per-rule counts did not move**, which is
the evidence that no existing verdict rested on the bug. **Not in the Known Bugs registry**
— I grepped it directly (sub-agents cannot spawn `bug-curator`); rows 117–119 are the
renderer's D1–D13 and row 179 is the audit's import-isolation test. **`bug-curator` owns
filing it.**

### Deviations from the plan, and decisions I did not take

1. **`CELL_FLOOR_FRACTION` stays at the plan's 0.40, and one negative control therefore
   fails.** A lone agent on bare ground keeps its halo, and that **correct** token measures
   **43.76 %** of its square — above the 40 % "this is the floor" line — so the occupant is
   excluded as scenery. Both populations are measured: largest correct token **0.4376**,
   smallest bed **0.5168**, bed floor by construction **0.5184**; a floor of **0.48** sits
   **53.5 %** of the way up that gap and makes every control pass. I did **not** move it —
   §R20.3's discipline is that a constant moves in the plan text with its evidence, never
   in a test to turn a checkpoint green. It ships as a `strict` xfail naming the numbers.
   **Two candidate fixes for `senior-developer`:** move the floor to 0.48 in §R19.1 step 2,
   or drop the halo on every square (the painter already drops it whenever the square is
   shared).
2. **An element with ink outside the square is not a token of that square.** Needed for
   §R20.2's own footprint control, which otherwise splits a correct two-mover square into
   six components: a diamond footprint spans three squares and is not an occupant of the
   middle one. It stays in the **occluder set**, so raising it above the tokens still fires
   the floor — only the assertion narrows, which is what §R20's narrowing rule permits.
3. **`cell_overdraw` has its own flag (`--cell-axes`), not `--arena-axes`.** The two rules
   want different axes: `numeric_in_arena` is legitimately pointed at any axes that should
   carry no numbers (an existing test points it at `thermoception`), while this rule divides
   the axes it is given into world squares. Sharing a flag would have made that test invent
   a grid over a card. This is also what keeps every frozen count unchanged.
4. **The audit carries its own copy of the minimap palette**, because it may not import the
   package it audits. A test that *may* import both asserts the copy has not drifted.
5. **`minimap_overdraw` requires the named axes to BE the grid**, and Phase 2's World map
   axes is the whole card. Rather than emit nine confident wrong verdicts it emits one
   `minimap_grid_unaligned`. The fix is a painter change mirroring `arena_card` / `arena`.

### Speed check

**Skipped for the training hot path, and the reason is structural:** every file changed is
an offline analysis instrument or a test. `scripts/eval/render_layout_audit.py` is imported
by nothing under `src/`, by no training entry point and by no renderer — it *imports* the
frozen renderer read-only, never the reverse. No environment step, model forward/backward,
vmap/jit boundary, observation pipeline or loss computation is touched.

The instrument's **own** cost is the number that moved, and it did not move much, despite
the Collection fix enumerating more artists per frame (V1 M4: 305 → 322 elements):

| Measurement | Before | After |
|---|---|---|
| Control suite, same 38 tests | 119.51 s | 118.57 s |
| Control suite, 67 tests | — | 123.60 s |
| Real dashboard frame, audited | 45.2 s @ 708–710 elements (Phase 2) | **46.5 s @ 735 elements** |

### Tests

| Command | Result |
|---|---|
| `pytest tests/env/test_render_audit_controls.py -q` | **66 passed, 1 xfailed** (was 38 passed) |
| `pytest tests/env -m "not integration" -q` | **602 passed, 377 skipped, 26 deselected, 1 xfailed** (was 574 / 377 / 26 — exactly +28 +1 xfail, the new tests, no regressions) |
| `scripts/eval/v1_path_guard.py check` | **PASS=10**, ACCEPTED=0, ATTRIBUTED=0, UNATTRIBUTABLE=0, **FRAMES PASS ×3**, `RESULT: OK`, **exit 0** — run before and after |

`render_layout_audit.py` was confirmed against the guard's own `PLAN_OWNED_PATHS` list
before editing: it is plan-owned, not one of the ten frozen V1-path files. No frozen file
was touched.

### Blockers and follow-ups

- **For `senior-developer`, blocking CP0.3b:** the `CELL_FLOOR_FRACTION` decision
  (deviation 1). Everything else in CP0.3b is met.
- **For `senior-developer`:** the M-F2 family's third inset is unreachable as
  pre-registered (§R20.3); the World map needs a grid-only Axes before its clause of CP2.8
  can be assessed; and `SCRIPTS_DEPENDENCY_MAP.md`'s prose for this script is now
  under-complete though its contract did not trigger.
- **For `bug-curator`:** the Collection-enumeration defect, which is not in the registry.
- **Not done and not hidden:** the five mutations were **not** run against the real
  painter, only against the Phase 0d synthetic figures; three of the five archetypes are
  still neither found nor synthesised; only matrix cell M4 was audited; and nobody looked
  at a frame at full size in this phase.

Implemented by: developer

---

## Verification Report — Phase 2 (the painters) and Phase 0d / CP0.3b (the `cell_overdraw` rule), verified together (2026-09-17)

### What was checked, in plain words

Two phases were verified in one pass, because their claims are the same claim seen twice. Phase 2 wrote the code that draws the new dashboard and reported, by hand, that a square of the world holding two things now shows **both**. Phase 0d built the instrument that measures exactly that, and reported the same numbers. Two reports agreeing is worth very little if they are the same computation run twice, so the verification did three things rather than read them: it **re-derived** the load-bearing measurements itself, it **looked at the rendered pictures**, and it checked that the instrument's own recently-found defect had not quietly moved any earlier number in this plan.

**Verdict: VERIFIED WITH ISSUES.** Nothing is wrong with what was built. Both checkpoints are held open by decisions this plan owed them — now recorded in **Revision 21** — plus work the developer named itself and did not hide.

### The headline claim, attacked rather than read

| Claim | How it was checked here | Result |
|---|---|---|
| The overdraw defect is fixed: a shared square shows every occupant | **Looked at both rendered frames at full size.** Square (4,3) at step 0 shows a green bush plate with the agent standing on it inside its indigo outline; (5,1) at step 32 shows the agent and a piece of food **side by side**; (3,5) shows the rabbit on a grey rock plate | ✅ visible, not inferred |
| The instrument reproduces Phase 2's hand measurement **independently** | Read both measurement paths. They share the *method* (§R19.1) and the 8/255 ink threshold, and **no code**: Phase 2's scratch harness toggles artist visibility itself, builds its own bare-background baseline, ranks only the arena's own children, and does its own survival arithmetic; the audit uses `FrameProbe`, a figure-wide `DrawOrder` and `occupancy_from_state`. The occupancy ground truths are two ports over **different input objects** (the audit reads the recorded `state`, the renderer reads the snapshot dict) and were compared square-by-square | ✅ two implementations, one method — which is what "independent reproduction" honestly means here, and is stated that way rather than overclaimed |
| **M-F1g** (the ground drawn over the tokens, figure facecolor `CANVAS`) is caught by precondition (c′) **alone** | **Re-derived.** With `(c′)` disabled the frame measures 2 kinds → 2 isolated → 2 visible components, survival **1.000 / 1.000**, and produces **zero findings** — it passes silently. With it enabled, one `cell_probe_blind` finding | ✅ the rule's hardest clause is alive, exactly as §R20.6 predicted |
| The instrument's own defect (every `Collection` dropped from the element list) is fixed, **and the frozen counts did not move** | **Re-derived by neutering the new path-extent fallback and re-running the audit on the frozen frames.** V1 M4: 322 elements shipped vs **305** pre-fix, 17 visible `Collection`s, 17 in the element list vs **0**; V1 M1: 221 vs 204, same 17. **Every per-rule count is identical in both states, on both frames** | ✅ no earlier calibration in this plan rested on the bug |
| The M-F2 exclusion at inset 0.10 is honest, not convenient | Re-measured the whole family at both floors. A member that stops being read as a bed has survival **1.0**, so keeping it would have *raised* the recorded defect maximum toward the floor and made the margin look wider. Dropping it is the conservative direction | ✅ honest — and see the issue below, which the exclusion led to |
| The control suite | `pytest tests/env/test_render_audit_controls.py` re-run | ✅ **66 passed, 1 xfailed** — reproduces exactly |

### Issues

1. **⚠️ Moving the floor to 0.48 would have left the survival floor with one positive control, and this was not visible in the report.** Found while verifying, measured, and fixed in the plan rather than left for Phase 0d to hit: at a 0.48 floor the M-F2 member at inset **0.05** also stops being classified as a bed, so the gap table's defect side would rest on the single 0.02 member. The family is **re-registered at `0.005 / 0.010 / 0.020`**, all three of which fire the survival floor at both 0.40 and 0.48 (survival 0.091–0.144). Recorded in Revision 21 §R21.2 with the measurements. The developer's own note flagged the 0.05 member as at risk; it did not follow through to what that does to the table.
2. **⚠️ CP0.3b and CP2.8 remain open**, with their remaining work now enumerated at the checkpoints themselves. CP0.3b needs one small developer pass (the constant, the xfail, the re-registered insets, a re-run gap table). CP2.8 needs real-painter mutations, three more archetypes, eight more matrix cells, a grid-only Axes for the World map, and the rim-pip/identity-pip check once rim pips exist — one item (**the pip disjointness clause**) the developer's list did not mention; the rest of that list is complete.
3. **ℹ️ The Collection-enumeration defect is not in the Known Bugs registry.** It is `bug-curator`'s to file, and filing it is not this verification's to do.
4. **ℹ️ `SCRIPTS_DEPENDENCY_MAP.md`'s prose for `render_layout_audit.py` is now under-complete** (no mention of the new rule or the two new flags). Its Maintenance Contract did **not** trigger — no script was added, moved, renamed or deleted, and no caller changed — so this is a nice-to-have, correctly flagged rather than silently fixed.

### File-by-file

| File | Verdict |
|---|---|
| `scripts/eval/render_layout_audit.py` (+795) | ✅ in scope. The new rule, `DrawOrder`, `occupancy_from_state`, `square_rects`, the minimap census, two new CLI flags, and the `Collection` extent fallback. The three hunks outside the new block are a widened `audit_frame` signature, the two `argparse` rows and the call that passes them through — all required by the flags |
| `tests/env/test_render_audit_controls.py` (+495, **0 deletions**) | ✅ in scope. Purely additive: no existing control was edited or weakened, which is the property that makes the unchanged frozen counts mean something |
| `src/environment/dashboard/{cells,painters,episode,palette,style,text_fit,thermal}.py` (new) | ✅ in scope, Phase 2's own File Changes rows |
| `src/environment/dashboard/__init__.py` (+44 / −6) | ✅ in scope — the lazy export of the two Phase-2 names, which is what keeps Phase 1's "a bare import pulls in no Matplotlib" test true |
| `tests/env/test_dashboard_cells.py`, `tests/env/test_dashboard_v1_imports.py` (new) | ✅ in scope |
| `tests/env/test_dashboard_layout.py` (+52) | ✅ in scope — the single right-column budget test §D1.1 asks Phase 2 for |
| Everything else in the working tree | ⛔ **not this plan's** — olfaction figures and their scripts, the imperativism manifest, `artifact_format_bugs.md`, `INDEX.md`, `SAVED_RUN_CONFIG_COMPAT.md` and the diary files belong to parallel sessions and must not be staged with this work |

### Speed check — ✅ no regression

- **Training hot path: structurally untouched.** Nothing changed here is imported by any training entry point; the audit is offline and imports the frozen renderer read-only, never the reverse. The new `dashboard` package is not yet wired into any renderer entry point, and its `__init__` was verified to keep Matplotlib out of a bare import.
- **The renderer itself is faster than what production uses** — 187.3 ms against 333.0 ms, a **1.78×** improvement, which is the direction that matters for training-time rendering. The `≤ 0.5 ×` target is missed at 0.563 ×, and that is a **user decision recorded at Q22 / Revision 21 §R21.1**, not an absorbed regression.
- **The instrument's own cost moved +2.9 %** (45.2 s → 46.5 s per audited frame) while enumerating 17 more artists per frame. Well inside the 5 % discussion threshold, and it is an offline analysis tool.

### Conclusion

**VERIFIED WITH ISSUES.** Phase 2's painters and Phase 0d's rule both do what their reports say, and the two load-bearing claims — "a shared square shows both occupants" and "precondition (c′) is what catches the invisible-occluder case" — were re-derived here rather than taken on trust, with the pictures looked at. The three decisions the phases were waiting on are recorded in **Revision 21**: Q22 accepted at 1.78×, the floor constant moved to 0.48 with its evidence and the M-F2 family re-registered, and §R17.3 item 8 corrected. **CP0.3b needs one developer pass; CP2.8 needs the work enumerated at its checkpoint.** Neither is blocked on anything undecided.

---

## Implementation Report — CP0.3b's remaining pass, and CP2.8 against the real painter (2026-09-17)

### What this is, in plain words

The redesign exists because a square of the world holding two things was drawn showing
only one. Checkpoint **CP2.8** is the one that certifies the fix: it asks that every
occupant of a shared square actually be **visible in a rendered frame**, that the
measuring instrument be shown to *catch* the defect when the defect is put back
deliberately (a "mutation"), and that somebody **look** at the pictures. This pass did
four things. It applied the constant change Revision 21 §R21.2 had already decided in the
plan text. It gave the small World map its own drawing area so its colour census can run
at all. It ran the five mutations against **the painter that actually ships**, rather than
against small figures a test builds. And it audited **every** matrix cell.

**The headline: the arena rule is clean everywhere.** Across **18 audited frames — all
nine matrix cells, two frames each — the co-occupancy rule reports ZERO findings**, and
every occupant of every square keeps **100 %** of itself (154 single-occupant squares,
4 two-occupant, 5 three-occupant, all measuring exactly 1.000). All five mutations fail
the audit on the real painter. The rim-pip clause, which had no coverage at all, now
measures **0 shared pixels**.

**CP2.8 does not close.** Two things block it, neither of them the arena painter and
neither fixable by adjusting a number — they are named in full at the end, and nothing was
tightened, re-scoped or re-framed to reach a tick.

### Part 1 — CP0.3b's remaining pass (the constant, the xfail, the re-registered family)

Revision 21 §R21.2 decided this in the plan text with its evidence; this pass carried it
into the code, at the five sites the revision names and nowhere else.

| Site | Change |
|---|---|
| `render_layout_audit.py:832` | `CELL_FLOOR_FRACTION` **0.40 → 0.48**, with both measured populations written into the constant's comment (largest correct token **0.4376**, smallest bed **0.5168**, plate fraction by construction **0.5184**) |
| `render_layout_audit.py:193, 262` | the module docstring's two statements of the constant |
| `test_render_audit_controls.py` | the `strict` xfail is **removed**; the lone agent on bare ground joins `NEGATIVE_CELLS` as a plain negative control |
| `test_render_audit_controls.py` | `assert token > CELL_FLOOR_FRACTION` inverts to **`token < CELL_FLOOR_FRACTION < bed`** — the property that actually has to hold, failing in both directions |
| `test_render_audit_controls.py` | the M-F2 family re-registered at **0.005 / 0.010 / 0.020**, with a new assertion that **all three** fire the **survival floor specifically** |

Control suite: **67 passed, 0 xfailed** (was 66 passed + 1 xfailed — exactly the xfail
becoming a pass). Full `tests/env`: **603 passed, 377 skipped, 26 deselected, 0 failed**
(was 602 + 1 xfailed).

### Part 2 — the painter changes

| File | Change | Why |
|---|---|---|
| `episode.py` | new `grid_axes()` helper; the World map card becomes `minimap_card` with a **grid-only `minimap` Axes** inside it | The census divides the *named axes* into world squares, which is exact only when that axes **is** the grid. Pointed at the whole card — title above, two-line caption below — it sampled card background and could only answer `minimap_grid_unaligned`. Approved as the fix in the Phase 2 / Phase 0d verification. Measured after: the grid Axes is **184 × 184 px on a 10 × 10 world = exactly 18.40 px per square**, so the derived grid aligns by construction |
| `painters.py` | `build_minimap` draws grounds, tints and the dot pool into the grid Axes in its own coordinates | same |
| `painters.py` | the amber **identity pip** is now drawn whenever the hiding predator is one of the occupants **the dot carries** (`occ[:2]`), not only when it is alone | §R17.4 requires the occupancy rim pip and the identity pip to be able to appear on **one square** with a test asserting they share no pixel. As written they were mutually exclusive, so that clause was structurally untestable — which is why the verification found it had no coverage |

`v1_path_guard.py` was consulted before editing: `src/environment/dashboard/` and
`scripts/eval/render_layout_audit.py` are **plan-owned**. No frozen file was touched.

### Part 3 — the mutation table, against the REAL painter

Driven through a scratch harness (`tmp/20260917_1230_cp28_real_painter.py`) that renders
the real dashboard and hands the audit a frame it has already drawn, so **every audit rule
runs unchanged and no audit file was edited to accommodate the renderer**. Each mutation
is applied to `src/environment/dashboard/` at runtime — a z-order constant, the slot
function, the bed builder — never to the instrument.

**The definitive table is on ONE real frame: `M4` episode file 1, step 32.** That frame was
chosen by measurement, not convenience: it is one of nine real frames carrying **both**
structures the family needs — `(5,1) agent + food` (two non-terrain kinds, so concentric
drawing has something to merge) and `(3,5) neutral + rock` (a bed under a token, so a bed
drawn late has something to cover).

| Mutation | Fires? | `cell_overdraw` | What the rule measured |
|---|---|---|---|
| *(none — control)* | **silent** | **0** | `(5,1)` 2 kinds → 2 isolated → 2 visible, survival `[1.0, 1.0]` |
| **M-E** every occupant forced to the square's centre | **YES** | 3 | `(5,1)` 2 kinds → **1** isolated, **1** visible; plus 235 px of shared token ink between two occupant drawings |
| **M-F1** bed drawn after the tokens | **YES** | 2 | `(3,5)` 1 kind → 1 isolated, **0 visible**, survival **0.000** over 510 px |
| **M-F1g** ground drawn after the tokens, figure facecolor `CANVAS` | **YES** | 17 | 9 squares fully covered, including `(5,1)` at survival `[0.0, 0.0]` |
| **M-F2** bed after tokens, inset `0.005 × cell` | **YES** | 2 | `(3,5)` survival **0.000** |
| **M-F2** inset `0.010 × cell` | **YES** | 2 | `(3,5)` survival **0.000** |
| **M-F2** inset `0.020 × cell` | **YES** | 2 | `(3,5)` survival **0.000** |
| **M-F3** the agent's dot above the split wedge | **YES** | — (`minimap_overdraw`) | `(5,1)` reads `seen ['agent']`: 2 kinds, **1** distinct colour. The unmutated frame has **no** finding at `(5,1)`, so this one is the mutation's own |

**M-F1g is caught by different clauses in different worlds, and both are failures.** On the
neutral world (`M1`) it fires **784 `cell_probe_blind`** findings — precondition (c′)
alone — because that world's ground is `TRACK`, 5–6/255 from `CANVAS` and therefore
invisible to the ink probe. On the thermal world (`M4`) the grounds are temperature-tinted
and remain visible, so the ordinary composition check catches it instead (17–18
`cell_overdraw`). The mutation escapes in neither.

#### The M1 vacuity — recorded, not quietly corrected

The first mutation run was on `M1` episode file 0, step 34. **M-F1 and all three M-F2
members produced zero `cell_overdraw` findings there, and that was not evidence of
anything**: that frame's only multi-occupant square is `(8,6) agent + hiding_predator +
predator`, which holds **no terrain**. Measured directly: *bed-under-token squares =* `{}`
on that frame, against `{(4,3): ('agent','bush')}` on `M4` step 0. A bed drawn after the
tokens had **no bed over any token to draw**, so those mutations were structurally
incapable of firing, and recording them as passes would have been exactly the failure this
phase exists to prevent. The rows were moved to a frame carrying the structure they
attack. The same shape in reverse: **M-E is vacuous on `M4` step 0**, whose only shared
square is `agent + bush` — one non-terrain kind, so there is nothing to merge.

#### M-F2's mechanism depends on the square's SHAPE — a result, not a quirk of one frame

On every **real** frame the M-F2 family fires through the **component count**, never
through the survival floor it is registered to sweep. The reason is geometric and
general: a solo token is centred with `h = 0.30 × cell = 15 px` inside a bed plate
spanning `± 18 px`, so a bed inset by 0.005–0.020 × cell (0.25–1.0 px) still covers it
**whole** → survival 0.000. Only a square with **two or more** occupants puts tokens in
slots reaching 21.4 px from the centre, permanently protruding past the 18 px plate, so a
rim survives and the floor is what catches it.

And **no real square in the matrix has that shape**: measured across all nine cells and
both episode files, squares holding terrain **plus two or more** non-terrain kinds number
**0**. (Environment rule R3 is why — animals can never stand on a bush or a tree.)

So the family was additionally run against a **synthetic** `bush + agent + predator` square
— the same composition Phase 0d's own control uses — on the **real painter**:

| Inset | `cell_overdraw` | Components | Survival | Fires via |
|---|---|---|---|---|
| *(control)* | **0** | 2 kinds → 2 → 2 | `[1.0, 1.0]` | — silent |
| `0.005 × cell` | 2 | 2 kinds → 2 → **2** | **`[0.0921, 0.1323]`** | **survival floor** |
| `0.010 × cell` | 2 | 2 kinds → 2 → **2** | **`[0.0954, 0.1362]`** | **survival floor** |
| `0.020 × cell` | 2 | 2 kinds → 2 → **2** | **`[0.102, 0.144]`** | **survival floor** |

Those reproduce Revision 21 §R21.2's pre-registered `0.091 / 0.132`, `0.095 / 0.136`,
`0.101 / 0.144` **on the shipping painter**, with the component count still correctly 2 —
which is the property that makes the floor the only thing that can fire.

> **For whoever next picks a frame for this family:** it needs a square holding **terrain
> plus two or more occupants**. On a solo-token square the constant goes unswept while the
> mutation still "fails", which looks like success and measures nothing. This is the M1
> vacuity one level up — a sweep family that quietly stops testing what it claims.

### Part 4 — archetype and cell coverage

| Archetype | Where | Source | Result |
|---|---|---|---|
| agent on terrain | `M3/M4/M4b/M6b` step 0 — `(4,3) agent + bush` | **real episode** | 0 findings, survival 1.000 |
| two movers / two occupants | `M4` f1 s32 `(5,1) agent + food`; `M1` f0 s34 `agent + hiding_predator` | **real episode** | 0 findings, `[1.0, 1.0]` |
| **three-way** | `M1/M1x/M2/M5/M6` file 0, step 34 — `(8,6) agent + hiding_predator + predator` | **real episode** | 0 findings, `[1.0, 1.0, 1.0]` |
| **four-way** | `(1,1) agent + food + neutral + predator` | **SYNTHETIC — derived input** | 0 findings, `[1.0, 1.0, 1.0, 1.0]` |
| **resource on terrain** | `(3,3) bush + food` | **SYNTHETIC — derived input** | 0 findings, survival 1.000 |
| *(three-way carrying both pips)* | `(6,6) food + hiding_predator + neutral` | **SYNTHETIC — derived input** | 0 findings, `[1.0, 1.0, 1.0]` |

**The synthetic frames are labelled in the frame itself** — the header reads `SYNTHETIC
derived input · M4` — and in the filename. **What they are and are not evidence for,
stated plainly: a four-way square measuring 1.000 survival is real evidence about the
PAINTER and no evidence at all about the WORLDS.** Four-way and resource-on-terrain occur
in **no episode of any of the nine cells** (measured: 0 hits each, over every step of both
episode files), so nothing here says a trained agent will ever see one. It says that if
one arrives, it draws correctly. Everything not marked synthetic came from a real episode.

**Every matrix cell, ≤ 2 frames each (CP2.8's own sample rule), 18 frames:**

| Cells | Frames audited | `cell_*` findings | Archetypes in those frames |
|---|---|---|---|
| `M1`, `M1x`, `M2`, `M5`, `M6` | f1 s0 + f0 s34 | **0** | three-way, two occupants |
| `M3`, `M4`, `M4b`, `M6b` | f1 s0 + f1 s32 | **0** | agent on terrain, two occupants |

**Total across all 18 frames: 0 findings from `cell_overdraw`, `cell_opacity`,
`cell_foreign_axes`, `cell_probe_blind` and `outline_like_token`.** Survival values seen
anywhere: `[1.0]` ×154, `[1.0, 1.0]` ×4, `[1.0, 1.0, 1.0]` ×5 — no value below 1.000
anywhere in the matrix.

### Part 5 — the rim pip, and the minimap census now that it can run

**Rim pip vs. hiding-predator identity pip: 0 shared pixels** (identity pip 21 px, rim pip
17 px), measured on the rendered synthetic square `(6,6) food + hiding_predator +
neutral`, where `by_priority` puts the hiding predator in the dot and the neutral on the
rim. This clause had **no coverage at all** before, and could not have had any: the
identity pip was drawn only for a *lone* hiding predator, so the two pips could never
coexist. A real frame cannot supply this square today — the one real three-way puts the
hiding predator third, on the rim — so the measurement is on a labelled synthetic frame.

**The census runs now, and it fires on CORRECT frames.** With the grid-only Axes the rule
no longer refuses; it returns per-square verdicts, and 2–4 of them per frame are against a
painter doing what the plan told it to do. The causes were decomposed by measurement, not
guessed — hiding each artist class and re-running:

| Cause | Evidence | Findings it accounts for |
|---|---|---|
| **(A) the identity pip covers its own occupant's dot** | solo hiding-predator squares census **92 / 87 / 88 px**; with the identity pip hidden, **116 / 113 / 115 px** — the pip removes ~**21 %** of the colour area the rule requires the occupant to keep (floor 0.98) | 3 of 4 on `M1` s34; hiding it removes exactly those 3 |
| **(B) the rim pip overlaps the dot** | drawn at radius `0.12 × cell` centred `0.3677 × cell` out, so its inner edge sits at `0.248 × cell` — **inside** the dot's `0.30 × cell`, eating the neighbouring wedge. §R17.4's own words are "a rim pip … **outside the dot**" | the 4th finding (`(8,6) predator`); hiding the rim pip removes exactly it |
| **(C) a four-way square can only encode three occupants** | on the synthetic four-way, `neutral` — the 4th by priority — measures **1 px**: it is not drawn on the map at all. §R17.4's encoding stops at "the third becomes a rim pip" | the `neutral` finding on the synthetic frame |

**None of the three is caused by this pass's identity-pip change** — (A)'s three findings
are all *solo* squares, where the identity pip was already drawn before; (B) and (C)
involve no identity pip. All three are contradictions between §R17.4's encoding (pips
deliberately drawn over the colours they annotate; three-occupant ceiling) and §R19.1 step
9 / §R20.4's ground truth (one distinct palette colour per kind, each keeping ≥ 98 % of
its isolated colour area). **Nothing was loosened**: per §R20's narrowing rule the fix for
a false alarm is never a wider threshold or a smaller occluder set, and choosing between
"move the floor", "draw the pips differently" and "extend the encoding past three" is a
plan decision, not a developer's. **Owner: `senior-developer`.**

The **shared-square caption** clause passes: no `minimap_caption` finding on any of the 18
frames, including every frame holding a shared square.

### Part 6 — one finding outside CP2.8, not hidden

`M5` reports **`panel_absent: Olfaction`** on both its audited frames. Diagnosed rather
than filed: `M5` is the only maintained cell with `olfactory_range: 1`, which routes it
down the **sensor-band** layout — its cards are `[… 'band' …]` with **no `olfactory`
card**, where `M4` (range 0) has one titled "Olfaction". The band painter is deliberately
unbuilt (Phase 2 "what is NOT built yet"; Revision 21 §R21.4 item 3 records the band as
never exercised by a real world). So a modality in the observation has a box reserved and
**nothing drawn in it** — the audit is right, and this belongs to **CP2.7**, not CP2.8. It
is not a co-occupancy defect and not a regression from this pass.

### Test results

| Command | Result |
|---|---|
| `pytest tests/env/test_render_audit_controls.py -q` | **67 passed, 0 xfailed** (was 66 + 1 xfailed) |
| `pytest tests/env/test_dashboard_{cells,layout,v1_imports}.py -q` | **131 passed** |
| `pytest tests/env -m "not integration" -q` | **603 passed, 377 skipped, 26 deselected, 0 failed** |
| `scripts/eval/v1_path_guard.py check` (before **and** after) | **PASS=10**, ACCEPTED=0, ATTRIBUTED=0, UNATTRIBUTABLE=0, **FRAMES PASS ×3**, `RESULT: OK`, **exit 0** |

### Speed check

**Training hot path: structurally untouched.** `render_layout_audit.py` is an offline
instrument imported by nothing under `src/`. The two painter files are in the dashboard
package, which is **not yet wired into any renderer entry point** and is imported by no
training path; the changes are one added child Axes and one visibility condition, both
outside any environment step, model forward/backward, vmap/jit boundary or loss.

**The instrument's own cost, which is what CP2.8 asks be stated for sizing a sample:**
**44.2 – 53.3 s per audited frame at 687 – 755 elements**, over **31 audited frames**, on
**Intel i9-7900X @ 3.30 GHz, 20 threads, container `docker-102`**. Phase 0d measured 46.5 s
at 735 elements; the wider spread here is deliberate CPU contention — up to four audit
batches ran concurrently. **Sample chosen: 18 matrix frames (2 per cell, CP2.8's own cap)
+ 8 mutation frames + 4 synthetic-M-F2 frames + 1 synthetic-archetype frame ≈ 24 minutes
of audit**, run as concurrent batches rather than sequentially.

Frames enumerate as expected — the `PatchCollection` sanity check the brief asked for:
each audited frame reports 655–755 elements, and the arena's beds and tokens appear in the
element list as `collection PatchCollection in arena` (they are named as such in the M-E
findings above). The class silently dropped until `4a1a6dd9` is being counted.

### Deviations from the plan — none silent

1. **Two painter changes beyond the constant pass**, both above: the grid-only World-map
   Axes (approved as the fix in the Phase 2 / Phase 0d verification) and the identity-pip
   visibility condition (required by §R17.4's own "the two can appear on one square"
   clause, without which CP2.8's pip check is untestable). Both are in files the plan's
   Phase 2 File Changes rows already list.
2. **The mutation table spans two frames plus a synthetic square**, with the reason
   measured in each case (above). A single real frame carries all five mutations
   (`M4` f1 s32); only the M-F2 **floor mechanism** needs a square shape the worlds never
   produce.
3. **No test file was added.** CP2.8's evidence is produced by a scratch harness under
   `tmp/`, not by the committed suite — see blocker 2.

### Prior art

Grepped `docs/develop/active/issues/KNOWN_BUGS.md` directly (sub-agents cannot spawn
`bug-curator`): no row matches `minimap`, `world map`, `rim pip`, `identity pip` or
`grid-only`. The three minimap causes are **not** in the registry. Following Revision 21
§R21.3's precedent — a defect in a plan's own rule text, caught before the behaviour ever
shipped, is not filed — they are reported here for `senior-developer` rather than filed.
If that judgement is wrong, **`bug-curator` owns it**. The `Collection`-enumeration row
(175) and the import-isolation row (211) are present and unrelated to this pass.

### Does CP2.8 close? **No — and here is exactly what blocks it**

Clause by clause: every matrix cell's checked frames pass `cell_overdraw` with **0**
findings ✅; all five archetypes rendered, two of them synthesised **and labelled** ✅;
looked at, at full size ✅ (the four-way renders as four equal tiles 2-over-2 inside the
agent's indigo outline — the degeneration §R17.5 item 2 predicted and nobody had seen; the
real three-way shows agent, predator and hiding predator side by side; `(3,3)` shows a red
apple standing on a green bush plate); all five mutations fail on the **real** painter ✅;
the caption is present ✅; the rim pip and identity pip share **0 pixels** ✅; the sample
is ≤ 2 frames per cell with its wall-clock and machine stated ✅.

**Blocker 1 — `minimap_overdraw` fires on correct frames (2–4 per frame, all 18).** Causes
(A), (B) and (C) in Part 5, each measured. CP2.8's *Fails if:* clause says "any finding
count is non-zero"; on the strictest reading of that clause the checkpoint fails, and I am
reporting it that way rather than arguing the clause covers only the arena rule. Resolving
it means choosing between moving the minimap floor, changing where the pips are drawn, or
extending the encoding past three occupants — **all plan decisions, `senior-developer`'s
to make**. Nothing was adjusted here to make the count zero.

**Blocker 2 — no committed test carries this evidence.** CP2.8 says "the test carries the
`integration` marker", and §R17.6 gives it a home: `tests/env/test_dashboard_frames.py`,
which **does not exist** — Phase 2 deferred it. Today's numbers come from a scratch
harness under `tmp/`, so they are reproducible by hand but not by CI. Until that file
exists, the checkpoint's own instrument is not in the suite.

Everything else CP2.8 asks for is measured and recorded above.

Implemented by: developer

Verified by: senior-developer

---

## Implementation Report — §R22.7: the World map's wedges, and CP2.8's committed home (2026-09-17)

### What this is, in plain words

The dashboard draws the world twice: a big grid panel at 50 px a square, and a small **World
map** at **18.40 px** a square. At that size no shape survives, so the small map gives up
drawing *what* things are and encodes them as **colour** — which the card has to admit in
words, because a viewer cannot infer a code.

The check that measures that small map had been reporting **two to four defects per frame on
frames that are correct**. Revision 22 decomposed that into three causes and decided each one
separately, and this pass implements those decisions. **The user answered Q21 first: the map
stays, as a minimap** — the cheap branch (drop it, and all three defects dissolve at once) was
on the table with its cost attached and was declined, so this is the repair, not the shortcut.

Three different kinds of fix, because they were three different kinds of defect:

1. **The instrument was wrong** about what a hiding predator's mark *is*. The map marks it with
   its body colour **plus** an amber dot — the only thing that tells it from an ordinary
   predator, whose colour differs by 15 parts in 255 and is indistinguishable at 18 px. The
   check assumed one colour per kind, so it read the mark's own amber as **21 % of the mark
   missing**. A kind's ground truth is now the **set** of colours its own mark is drawn in.
2. **The drawing was wrong**, and so was the plan's own rule. A third occupant used to become a
   pip on the square's rim, which the plan said sat *outside* the central dot. Measured, no pip
   of that size can be both outside the dot and inside the square. **The rim pip is retired**
   and the dot is simply divided between its occupants — a whole dot, halves, thirds, quarters.
3. **The encoding stopped at three.** A fourth occupant was not drawn at all. It is now the
   fourth quarter of the dot, matching the grid panel's own four-slot ceiling.

**No threshold moved.** `SURVIVAL_MIN`, `MINIMAP_AREA_MIN`, `MINIMAP_DELTA` and
`MINIMAP_ALIGN_MAX_BLANK` are untouched, and the one new thing this pass found that *would*
need a constant to move is **reported, not fixed** (finding D below).

**Headline numbers.** Across the same 18 matrix frames as the previous pass: `cell_overdraw`
and every other grid-panel rule still report **0 findings**, and the World map goes from
**2–4 findings on all 18 frames** to **0 findings on 13 of 18**. The 9 that remain are all one
square — the single real three-way in the matrix — from a single measured cause that is a
constant question, not a painter defect. CP2.8's evidence now lives in
`tests/env/test_dashboard_frames.py` under the `integration` marker instead of a `tmp/` script.

### Part 1 — the painter (`src/environment/dashboard/painters.py`)

| Change | What and why |
|---|---|
| `_wedge_angles(n, i)` (new) | Wedge `i` of `n`, from 12 o'clock. `n = 2` reproduces the shipped half-discs **exactly** (90..270, 270..450), so the encoding the controls already cover is unchanged by the generalisation |
| `_pip_place(n, i, r_dot)` (new) | The identity pip's centre and radius **inside its owner's wedge**: the sector centroid `(2/3)·R·sin α / α` at the sector's mid-angle, with the radius clipped to clear both bounding radii and the dot's rim. The clip never binds at the pip's existing 0.34 × dot radius (tightest is `n = 4`, which allows 0.36) — it is **computed rather than asserted** so the pip cannot silently become infeasible the way the rim pip did |
| `IDENT_FRAC = 0.34` | The factor the painter already drew the pip at, named rather than inlined. **Not a new constant and not a new size** |
| the per-square pool | **Four** wedges + the whole dot + the identity pip. **The rim pip artist is deleted.** Nothing is drawn outside the dot any more |
| `upd` | `n = 1` whole dot, `n = 2..4` wedges at 180/120/90°, `CELL_PRIORITY` order unchanged, ceiling of four; the pip is placed at its owner's wedge centroid for `n ≥ 2` and at the centre for `n = 1` |
| `MINIMAP_CAPTION` (new constant) | The card's two caption lines, rewritten to describe the encoding that actually ships |

**The caption, and why it is a constant with a test.** §R17.4 makes the on-page statement the
honesty condition the whole coded encoding rests on, and §R22.8 requires it to describe what the
painter draws — the old text said *"a third is a rim pip"*, and a caption naming a mark that no
longer exists is finding #56's failure mode. It now reads:

> Shared squares: the dot splits between up to four
> occupants. Colour is the code; grid view shows what.

It keeps the substring the audit keys on (`shared square`), says **in words** that colour is the
code and that the grid view is where occupants are identified, and states the ceiling. It is
**measured**, not estimated: the slot is 288 px and the two lines are **264.0 px** and
**283.6 px** in the vendored font. That matters because the caption role is already at its 12 px
legibility floor, so the text fitter **raises** rather than shrinking — an overlong caption would
take the whole renderer down. `test_dashboard_cells.py` now pins both the widths and the wording.

### Part 2 — the instrument (`scripts/eval/render_layout_audit.py`, + `palette.py`)

| Site | Change |
|---|---|
| `MINIMAP_PALETTE` | kind → **`frozenset` of its own mark's colours**; `hiding_predator` → `{HIDE_BODY, HIDE_EYE}`, every other kind a singleton |
| `palette.MINIMAP_MARK_COLOURS` (new) | the package-side table the audit's copy is checked against, so the anti-drift test survives the type change and pins **both** directions (sets equal, and every kind's set still contains its single-colour body value) |
| `_classify_census` | counts the **union** over a kind's colour set, taken on the mask so a pixel can never be counted twice |
| `minimap_overdraw` denominator | the same census over **that kind's own artists rendered together**, replacing the per-element `max`. Ownership is **measured, not declared**: an artist belongs to kind `k` only if its *isolated* ink carries one of `k`'s colours |
| `minimap_overdraw` distinctness | compares colour **sets**, so `hiding_predator` and `predator` stay two kinds |
| module docstring + rule docstring | restated for the set ground truth and the own-artists denominator |

**Cost of the denominator change: one extra render per (square, kind) that is drawn in more than
one artist** — which today is only the hiding predator. Every other kind still costs exactly the
solo render it always cost, and the render cache is now keyed by artist *set* rather than by
single artist id.

### Part 3 — the controls, and the one that matters most

Measured on the real painter at the real 18.40 px square (harness
`tmp/20260917_1700_r22_minimap.py`, which runs `minimap_overdraw` alone — a few renders rather
than the 45–53 s full audit — so the encoding could be iterated at all), and then committed as
tests.

| Control | Result |
|---|---|
| **(A) before the fix** — solo hiding predator, one-colour-per-kind ground truth restored | **fires at 73.3 %** |
| **(A) after the fix** — the same frame, same painter | **0 findings**, ratio **1.000** |
| correct `n = 1` (agent; hiding predator) | silent, **62/62** and **48/48** = 1.000 |
| correct `n = 2` (hiding predator + neutral) | silent, **16/16** and **24/24** = 1.000 |
| correct `n = 4` (agent + predator + food + neutral) | silent, **13/13** ×4 = 1.000 |
| correct `n = 4` **with** a hiding predator | silent, its two-paint mark **6/6** = 1.000 |
| two predators (one kind, two movers — §R20.4's case) | silent |
| **M-F3** agent's dot over the split wedge | **FIRES** |
| **M-F4** identity pip back at the square's centre, shared square | **FIRES, naming the foreign kind**: `neutral` at **83.3 %** (20 px against its own 24) |
| **M-F5** amber painted by something other than the identity pip | **FIRES twice** — the artist-level ownership guard names the offending artist, and the census independently reports the kind whose colour vanished |

**M-F4 is the load-bearing one and it is not hypothetical — it is this morning's painter.** The
risk in letting amber count towards the hiding predator is that amber could then paint over
anything undetected. Putting the pip back at the square's centre, where it straddles both halves
of a shared dot, is exactly that, and the rule catches it and names the kind that was eaten. The
correct partner (pip in its own wedge) is silent on the same square. **The union fix is
therefore not an amnesty**, which is what §R22.1 required be demonstrated rather than argued.

A second control proves the fix is load-bearing in the other direction: restoring the
single-colour table makes the **same correct figure** fire again
(`test_the_union_ground_truth_is_what_makes_the_two_paint_mark_pass`).

### Part 4 — the four-way census: the number, and the pre-registered branch taken

§R22.3 wrote the branch down before the measurement: if the smallest wedge of a correct four-way
classifies at a **non-zero** count the ratio test is scale-free and the design holds at four; if
it classifies at **zero** the answer is a **stated ceiling of three**, never a lowered floor or a
widened `MINIMAP_DELTA`.

**Measured: 13 classified pixels per wedge, all four wedges, ratio 1.000 each, denominator by the
`isolated-wedge` path.** With a hiding predator in the fourth position its two-paint mark measures
**6 px against its own 6**. The count is non-zero, so **the first branch is taken: the design
holds, and the ceiling is four.** Nothing was retuned to reach it. The number is pinned in
`test_the_four_way_census_is_a_number_and_the_ratio_is_scale_free`, whose failure message names
the other branch, so a future shrink that drives it to zero is read as the plan already decided
rather than re-argued.

### Part 5 — the matrix, re-audited: 18 frames

Same sample rule as before (≤ 2 frames per matrix cell: step 0 plus the archetype-richest frame),
same nine cells, so the before/after is like-for-like.

| | Before this pass | After |
|---|---|---|
| grid panel (`cell_overdraw`, `cell_opacity`, `cell_foreign_axes`, `cell_probe_blind`, `outline_like_token`) | **0** across 18 | **0** across 18 |
| World map (`minimap_overdraw`) | **2–4 on every one of the 18** | **0 on 13 of 18**; **9 findings total**, all on **one square** |
| `minimap_caption` | 0 | 0 |
| `minimap_grid_unaligned` | 0 | 0 |
| `text_over_fill` | 9–16 per frame | 9–15 per frame (unchanged; pre-existing, not a co-occupancy rule) |
| `panel_absent: Olfaction` on `M5` | 1 per frame | unchanged — **CP2.7's**, per §R22.9, not touched here |

The 9 remaining findings are the five frames that contain the matrix's **only real three-way
square**, `(8,6) agent + hiding_predator + predator` (`M1`, `M1x`, `M2`, `M5`, `M6` file 0 step
34). Finding D below is what they are.

**Frames audited, and why that number.** **18** through the full audit (all nine cells × 2 frames
— CP2.8's own cap, re-run in full because the three-way square that turned out to matter lives in
five different cells and a subset would have found it in one); **13** more through the committed
integration tests, one of which is a full-audit frame; and **~14** through the minimap-only
harness while iterating. The full audit costs **49.1 s per frame** (measured by `pytest
--durations` on the committed test, ~700 elements, Intel i9-7900X, container `docker-102`), which
is why the minimap work was done on a rule-only harness and only the final evidence paid the full
price. The 18-frame matrix took **~21 minutes** wall clock, run concurrently with two pytest
sessions, so that figure carries deliberate CPU contention.

### Part 6 — finding **D**, new, measured, and NOT fixed here

**What it is.** On a **correct** three-way dot, one wedge measures **one classified pixel short**
of what it measures when its own artist is drawn alone:

| Frame | map square | kind | numerator / denominator | ratio |
|---|---|---|---|---|
| `M1` f0 s34 (23.80 px cell) | (8,6) | agent | **31 / 32** | 0.9688 |
| `M1` f0 s34 | (8,6) | predator | **31 / 32** | 0.9688 |
| `M1` f0 s34 | (8,6) | **hiding_predator** (two-paint mark) | **23 / 23** | **1.0000** |
| `M6` f0 s34 (19.80 px cell) | (8,6) | agent | **17 / 18** | 0.9444 |
| synthetic three-way on `M4` (18.40 px cell) | (4,4) | agent | **16 / 17** | 0.9412 |

**The cause, measured rather than reasoned.** The 0.8 px white line that divides two wedges is
stroked by **both** of them. Compositing the same partially-covered pixel twice leaves it whiter
than either pass alone — measured at the offending pixel: **(104, 90, 221) composited against
(98, 83, 220) isolated**, against the agent's `#5B4BDB` = (91, 75, 219). That carries exactly one
pixel from 7/255 to 13/255 away from its colour, just past `MINIMAP_DELTA`'s 12. It is always
**one** pixel; the ratio only varies because the wedge does.

**Why it is not fixed here.** Under §R22.4's own test this is the *other* category — a picture
correct as drawn, misclassified by a number — and the number is `SURVIVAL_MIN = 0.98`, swept on
the grid panel's ~330 px² tokens where one pixel is 0.3 %, and reused **unswept** on a 13–32 px
map wedge where it is 3–8 %. Arithmetically, **a 0.98 floor is only reachable at ≥ 50 classified
pixels per wedge**, and no map wedge has that. Moving a constant is a plan decision taken in the
plan text with its evidence, never in a test (§R20.3), so this is reported. **The gap it would
have to sit in is measured and real: worst correct control 0.941, best mutation 0.833.** The plan
already has the right-shaped instrument for it — `MINIMAP_AREA_MIN` exists precisely because the
map needs its own floor rather than `SURVIVAL_MIN` reused — but it is applied only on the
geometric path today. **Owner: `senior-developer`.**

Two repairs were tried and rejected on measurement rather than taste, recorded so they are not
re-tried: **round joins** on the wedges (the miter-spike theory — implemented, measured,
*changed nothing at all*, reverted) and **folding a square's wedges into one artist** (would make
the ratio 1.000 by construction, and was rejected because it would also hide a draw-order defect
*between* the wedges of one dot, which is exactly what M-F3 exists to catch).

It is pinned in CI two ways: a test that asserts the measured 16/17, and a **strict xfail** on
"a correct three-way is silent", so the day the floor question is settled the suite goes **red**
and forces this note to be updated rather than drifting out of date.

### Part 7 — CP2.8's committed home, and Q21's closure

**`tests/env/test_dashboard_frames.py` (new, 12 passed + 1 strict xfail).** §R17.6's named home
for this evidence. It deliberately does **not** re-derive the arena side — that was clean across
18 frames before this pass and the arena painter is untouched by this diff (every hunk in
`painters.py` falls inside `build_minimap`; `build_arena` and `build_arena_chrome` are
byte-identical, so the previous pass's M-E / M-F1 / M-F1g / M-F2 table stands). It carries
instead: the encoding as arithmetic (wedges partition the dot; the pip clears both bounding radii
and stays inside the dot for every `n`; §R22.2's `r_p ≤ 0.1016` bound recomputed; the ceiling of
four with the agent never dropped; amber reserved to the identity pip), the **real-square-size**
minimap controls and mutations, the four-way census number, the caption, and **one** full-audit
frame (`M4` f1 s32, 49.1 s) as the frame-level proof that every occupant of every shared square
survives.

**Q21 is closed in the question register**, at the coordinator's instruction and per the user's
decision: moved to **Decided questions** with today's date; §R22.5's dissolution table marked
**weighed and declined** rather than left as a standing option; §R19.4 item 5's gate, §R18.6, the
Revision 22 preamble, §R22.7's conditional header and the CP-D deferral bullet all rewritten so
nothing reads as contingent. Historical Implementation and Verification Reports that mention Q21
were **left alone** — they are signed records of what was true when written, and editing them
would falsify the history rather than update the plan.

### Test results

| Command | Result |
|---|---|
| `pytest tests/env/test_render_audit_controls.py -q` | **80 passed** (was 67; +13 new minimap controls) |
| `pytest tests/env/test_dashboard_frames.py -q -m integration` | **12 passed, 1 xfailed** (the strict xfail of finding D), 131 s |
| `pytest tests/env/test_dashboard_{cells,frames}.py -q -m "not integration"` | **32 passed** |
| `pytest tests/env -m "not integration" -q` | **642 passed, 377 skipped, 39 deselected, 0 failed** (was 603 passed / 26 deselected) |
| `scripts/eval/v1_path_guard.py check` (before **and** after) | **PASS=10**, ACCEPTED=0, ATTRIBUTED=0, UNATTRIBUTABLE=0, **FRAMES PASS ×3**, `RESULT: OK`, **exit 0** |

### Somebody looked

At full size, on the rendered maps: the real three-way `(8,6)` on `M1` and `M6` shows **three
120° wedges — indigo agent, dark predator, dark hiding predator with its amber dot in its own
third**; solo hiding predators elsewhere on the same frames show the amber dot centred in a whole
dark dot; a two-occupant square shows half dark with the amber inside *its* half and half grey.
The synthetic four-way renders as four clean quarters (indigo, red, dark, grey), and the
four-way-with-hiding-predator carries the amber dot inside one quarter without touching its
neighbours. **M-F4's frame is visibly wrong in the way the numbers say**: the amber dot sits on
the dividing line and eats into the grey neighbour. Crops under `tmp/20260917_r22_frames/`.

### Speed check

**Training hot path: structurally untouched, and the skip is stated rather than assumed.**
`render_layout_audit.py` is an offline instrument imported by nothing under `src/`. The dashboard
package is **not wired into any renderer entry point** and is imported by no training path; this
diff touches one painter function, a colour table and a test. No environment step, model
forward/backward, vmap/jit boundary, observation pipeline or loss is on any changed line.

**The instrument's own cost, which is what CP2.8 asks be stated:** **49.1 s** for one full audited
frame at ~700 elements (Intel i9-7900X @ 3.30 GHz, container `docker-102`), against the previous
pass's 44.2–53.3 s — unchanged within its own spread, as expected: the denominator change adds at
most one render per multi-paint mark per square, and only the hiding predator has one.

### Deviations from the plan — none silent

1. **`docs/environment/12_renderer.md` was NOT updated**, though §R22.7 lists it. Checked rather
   than assumed: that document currently describes only renderer **V1** and **V2**; it has no
   dashboard section and no minimap-encoding paragraph to correct. Writing one would mean
   authoring the whole Phase-5 "Docs" deliverable, which §R17.6 assigns to that phase. The
   encoding is fully documented in the painter's own docstring and in this report. **Flagged for
   `senior-developer`** as the one §R22.7 row not carried out.
2. **One new constant was named, not introduced:** `IDENT_FRAC = 0.34` is the factor already in
   the painter's expression `cell * 0.30 * 0.34`. `MINIMAP_CAPTION` is likewise the caption text
   moved out of two inline calls so a test can pin it. No tolerance, floor or delta changed.
3. **`palette.MINIMAP_MARK_COLOURS` is a new package-side table**, not named in §R22.7. It exists
   so the audit's copy keeps an anti-drift partner after becoming set-valued, which §R22.7's own
   row requires ("keep the anti-drift test"). Derived from `MINIMAP_COLOUR`, so it cannot drift.
4. **The round-join experiment** (Part 6) was written, measured and reverted. Recorded because a
   reader of the diff would otherwise not know the miter-spike hypothesis had been tested.

### Prior art

Grepped `docs/develop/active/issues/KNOWN_BUGS.md` directly (sub-agents cannot spawn
`bug-curator`): no row matches `minimap`, `world map`, `rim pip`, `identity pip`, `wedge` or
`census`. Finding D is **not** in the registry. Following §R21.3's precedent — a defect in a
plan's own rule text, caught before the behaviour ever shipped, is not filed — it is reported
here for `senior-developer` rather than filed. **If that judgement is wrong, `bug-curator` owns
it.**

### Does CP2.8 close? **Not quite — one clause, one cause, and it is not the painter**

Closed by this pass: the World map's encoding is implemented for `n = 1…4` ✅; the rim pip is
retired and with it §R17.4's two-pip collision clause, which is **discharged rather than met**
✅; the identity pip annotates its own mark and **M-F4 proves it** ✅; **M-F5** guards the amber
exemption ✅; the four-way census is recorded as a **number** and the pre-registered branch taken
✅; the caption describes the encoding the painter actually draws ✅; CP2.8's evidence is in the
committed suite under the `integration` marker, in its named file ✅; the grid panel is still
**0 findings across all 18 matrix frames** ✅; somebody looked ✅.

**Still open — finding D.** `minimap_overdraw` fires on the matrix's one real three-way square
(9 findings across the 5 frames that contain it; the other 13 frames are clean), because a 0.98
survival floor swept on 330 px² arena tokens is unreachable on a 17–32 px map wedge where one
anti-aliased pixel is 3–8 %. On CP2.8's strictest reading — "any finding count is non-zero" — the
checkpoint does not close, and that is how it is reported rather than arguing the clause covers
only the arena. **Nothing was loosened to reach a tick.** The decision is a constant, the
evidence and the gap are above, and it belongs to `senior-developer`.

Implemented by: developer

---

## Implementation Report — §R23.1 / §R23.2: the World map's own survival floor, and CP2.8's last clause (2026-09-17)

### What this is, in plain words

The dashboard draws the world twice — a big grid panel at 50 pixels a square, and a small **World map** at about 18 pixels a square. An automatic check asks of every occupant of a shared square: *does it still show, once everything else has been painted on top of it?* It answers by comparing how much of an occupant's colour survives in the finished picture against how much that occupant covers when drawn alone, and complains when the surviving share falls below a floor.

That floor was **98 %**, chosen by measurement on the **big** panel, where an occupant is ~330 pixels and one lost pixel costs 0.3 %. It had never been re-measured for the small map, where an occupant is 6–32 pixels and one lost pixel costs 3–17 %. The consequence was that the **one square in the whole verification matrix where three animals really do stand together** was reported as broken on all five frames that contain it — nine complaints about a picture that is correct, because the thin white line dividing two wedges is painted by both of them and a pixel painted white twice ends up whiter than a pixel painted white once.

This pass did what Revision 23 decided: **the map got its own floor** (93 %), the big panel kept its 98 %, and the map's geometric fallback kept its 55 %. The nine complaints are gone and **no frame reports anything at all** from either co-occupancy rule. Nothing was loosened to get there: the same deliberate sabotages must still be caught, and they are — re-registered as **four** graded defects instead of one, because two of the three that existed turned out to be caught by a *different* check and never tested this floor at all.

### The regression evidence: the strict xfail, before and after

The plan pre-registered its own failing test rather than a note. `test_a_correct_three_way_is_silent` carried a **strict** xfail whose stated purpose was to turn the suite red the day the floor question was settled.

| | State |
|---|---|
| **Before the fix** (verbatim, this session, pre-edit) | `XFAIL tests/env/test_dashboard_frames.py::test_a_correct_three_way_is_silent` — *"OPEN: the minimap reuses SURVIVAL_MIN (0.98) … A correct three-way therefore fires at 94.1 %"*. 22 passed, 1 xfailed |
| **After the fix** | the xfail marker is **deleted**; the test passes plainly. The whole `tests/env` run reports **no xfail and no xpass** |

The test that proves the fix is therefore one that **failed before and passes after**, and it was written by the plan before the code was touched, not by me afterwards.

### File-by-file — exactly the three files §R23.1 names, and no others

**`scripts/eval/render_layout_audit.py`** (4 of §R23.1's rows)

1. **New constant** beside `MINIMAP_AREA_MIN`: `MINIMAP_SURVIVAL_MIN = 0.93`, with both measured populations, the gap, the 54 %-placement precedent and the **one-pixel resolution limit** in its comment, plus §R23.1's pre-registered branch for the day a correct four-way measures 12/13.
2. **The call site** (`:1433` as it stood): `den, path, floor = best, "isolated-wedge", SURVIVAL_MIN` → the floor is no longer assigned beside a branch at all. Path and denominator are decided first, then `floor = MINIMAP_FLOORS[path]`.
3. **`SURVIVAL_MIN`'s comment** gains the sentence that makes the next reader stop: it is the **grid panel's** floor and only that; the map has its own; reusing it on a third instrument is the defect that was just removed.
4. **The module docstring** — the tolerance list gains `MINIMAP_SURVIVAL_MIN = 0.93` and marks `SURVIVAL_MIN` as *GRID PANEL only*; the minimap paragraph states that every map path measures against a map floor, that the choice is a lookup, and what the rule can and cannot see at this size.

**`tests/env/test_dashboard_frames.py`** (3 rows + the new table)

5. **The strict xfail is deleted** and `test_a_correct_three_way_is_silent` becomes a plain test, with a docstring naming the three ways it must **never** be made green (shrink a wedge, widen `MINIMAP_DELTA`, fold the wedges into one artist).
6. **The 16/17 measurement stays**, rewritten from "an OPEN finding" into a pinned property, and now also asserts the **margin**: 0.9412 − 0.93 = 0.0112.
7. **`_mutate` is graded** — `M-F4` by how far the identity pip is dragged toward the square's centre, `M-F3` by the overpainting disc's radius — with the pip's *radius* held fixed across the M-F4 family so the sweep varies one thing only.
8. **The minimap gap table** (`test_the_minimap_floor_sits_in_a_gap_and_not_on_a_cliff`), mirroring the arena's at `test_render_audit_controls.py`, plus `test_the_map_never_measures_against_the_grid_panels_floor`.

**`tests/env/test_render_audit_controls.py`** (1 row)

9. `_minimap_figure` gains the same graded mutations at the ~28 px mock scale, with two new tests: every graded member fires through the ratio floor, and the two shallow partners stay silent.

### Part 1 — the reuse is removed, not relocated

The brief's sharpest instruction was that it must not be possible for a future path to inherit the arena's floor by omission. A constant renamed at one call site would not have achieved that — the next path added would simply not set `floor` and would pick up whatever was assigned above it, which is **precisely how this bug happened**: §R20.4 ruled in Revision 20 that the map must never reuse `SURVIVAL_MIN`, the geometric path honoured it, and the census path added in §R22.1 quietly took the arena's number anyway.

So the floor is now **looked up from the path that was taken**:

```python
MINIMAP_FLOORS = {"isolated-wedge": MINIMAP_SURVIVAL_MIN,
                  "own-artists":    MINIMAP_SURVIVAL_MIN,
                  "geometric":      MINIMAP_AREA_MIN}
```

An unregistered path raises `KeyError` on its first square rather than measuring against a number swept for a panel eighteen times the size. A test asserts the grid panel's constant is **not even named** inside `minimap_overdraw`, that the three paths are exactly the registered ones, that none maps to `SURVIVAL_MIN`, and that an invented path raises.

**That guard bit immediately, on me.** My first version of the explanatory comment at the call site contained the words "the arena's `SURVIVAL_MIN`", and the test failed on it. The comment was reworded rather than the test weakened — a guard that fires on prose is a guard that will fire on the real thing.

### Part 2 — the re-registered family (§R23.2), measured at the real square size

Every ratio §R23.2 pre-registered reproduced **exactly**, at 18.40 px per square, against the real painter:

| Member | What it is | num / den | ratio | fires via |
|---|---|---|---|---|
| **M-F4a** | identity pip at the square's centre (the painter before Revision 22) | neutral 20 / 24 | **0.8333** | ratio floor |
| **M-F4b** | identity pip **80 %** of the way to the centre — a shallow crossing | neutral 22 / 24 | **0.9167** | ratio floor |
| **M-F3a** | agent disc at **0.35 ×** dot radius | 14 / 24 | **0.5833** | ratio floor |
| **M-F3b** | agent disc at **0.25 ×** dot radius — shallowest that still costs pixels | 18 / 24 | **0.7500** | ratio floor |

**4 of 4 fire through the floor**, none through distinctness — which is the whole point of the re-registration, since the previously registered M-F3 (full radius) and M-F5 are caught by the distinctness check and never consult a ratio. Both are **kept unchanged** as distinctness controls and still fire.

**The negative partners, measured and kept:** the pip at **60 %** and **40 %** of the way to the centre costs the neighbour **no classified pixel** (24/24) and the rule is correctly silent. That is this instrument's resolution limit — **one classified pixel** — measured rather than assumed, and it is why the family stops at 0.80. Two further gradations were measured and recorded: M-F3 at 0.50 × fires at 6/24 = 0.2500, and at 0.70 × the neighbour's colour vanishes entirely (0/24) and **distinctness** catches it, `seen []`.

**The minimap gap table:**

| Side | Value | Source |
|---|---|---|
| min over **correct** controls | **0.9375** | predator 15/16 on a three-way at square (2,2) |
| max over **floor-firing defects** | **0.9167** | M-F4b, neutral 22/24 |
| **gap** | **(0.9167, 0.9375]**, width 0.0208 | |
| **`MINIMAP_SURVIVAL_MIN`** | **0.93**, sitting **64.0 %** up the gap | unchanged from the plan |

All nine correct controls report **zero findings**. The same four members at the ~28 px mock scale measure 0.8781 / 0.9211 / 0.8525 / 0.9221 and all fire through the floor there too, with the 60 %/40 % partners silent at 0.9580 / 0.9887 — the scale difference is the reason both harnesses exist and neither stands in for the other.

### Part 3 — the 18-frame matrix against the pre-registered prediction

Re-run in full (all nine cells × 2 frames, CP2.8's own cap, same sample rule as the previous pass so the comparison is like-for-like).

| | Before (previous pass) | **After** |
|---|---|---|
| World map (`minimap_overdraw`) | 9 findings on 5 frames, 0 on 13 | **0 on 18 of 18** |
| grid panel (`cell_*`, `outline_like_token`) | 0 across 18 | **0 across 18** |
| `minimap_caption`, `minimap_grid_unaligned` | 0 | **0** |
| `text_over_fill` | 9–15 / frame | 9–15 / frame (unchanged; pre-existing, a different rule) |
| `panel_absent: Olfaction` on M5 | 1 / frame | unchanged — **CP2.7's**, per §R22.9 |

**The prediction was stated in advance and is met exactly: 0 findings on 18 of 18.** A `grep` for `minimap` or `cell_` over the whole re-run log returns **zero** matches. No frame fired, so the instruction "if any frame still fires, report the number and stop" was not reached and **the floor was not touched a second time**.

### Part 4 — one number in the plan's table did not reproduce, and it is reported rather than absorbed

§R23.1 records the worst correct control as **0.9412** (16/17). Sweeping a **second** map square finds **0.9375** (15/16, the predator's wedge on a three-way at square (2,2)) — the same one-pixel seam on a wedge one pixel smaller. Sub-pixel rasterisation differs by square: the same three-way composition measures agent 16/17 at (4,4) and predator 15/16 at (2,2).

**Consequences, stated plainly:** the gap narrows from 2.45 points to **2.08**, and 0.93 sits **64.0 %** up it rather than 54.4 %. It remains a real gap, every correct control remains silent, and **0.9375 > 0.93**. This is also exactly what §R23.1 pre-registered: *"a wedge of 15–24 classified pixels may lose exactly one pixel and stay silent; a wedge of 14 or fewer may lose none"* — 15/16 is that case, and 13/14 = 0.9286 would not be. **The constant was not moved for it**, per the plan's own *Fails if:*. `senior-developer` may wish to correct §R23.1's table to 0.9375.

### Part 5 — a **correct** control measuring ABOVE 1.000, on the shipped painter

Not predicted by the plan, found by this sweep, **not fixed**: on the three-way at square (2,2) the neutral wedge measures **16 / 15 = 1.0667** — 16 classified pixels in the finished picture against 15 when its own artist is drawn alone.

This is the same mechanism §R23.3 measured for *edgeless* wedges (23/22, 26/25) — a blend between two colours landing close enough to one of them to be credited to it — appearing at ~1 px on the painter that ships. It causes no finding (a ratio above the floor never fires) and it is **weaker** than the edgeless case, so §R23.3's verdict stands. But it does show the "credit in the direction that conceals occlusion" effect is not *absent* today, merely small, and the white split line bounds its magnitude rather than eliminating it. Recorded so the next person to reason about the seam has the number. `senior-developer`'s call whether §R23.3 wants a sentence.

### Part 6 — the variant §R23.3 named as unmeasured: **measured, and both arms fail**

Reported separately, as asked, and it changed no shipped file — the treatment is applied to artists the real painter drew, exactly as a mutation is. §R23.3's bar, quoted: *adopted only if every correct control measures ≤ 1.000 and the re-registered family still fires on every member.*

| Arm | Correct controls | Family | Verdict |
|---|---|---|---|
| **A** edgeless + one divider per boundary, as its own artist | **2 of 4 measure ABOVE 1.000** (neutral 34/30 = 1.1333; 13/11 = 1.1818) | **only 2 of 4 fire** — M-F4a and M-F4b both go to 1.0000 / 1.0667 | **REJECTED** |
| **B** the same, with the dot's outer ring restored as its own artist | all ≤ 1.000, **but every correct control FIRES** (2/3/3/4 findings; ratios collapse to 0.64–0.85) | 4 of 4 fire | **REJECTED** |

Arm A fails both halves: it does not remove the above-1.000 credit, and it makes the instrument **blind to the identity-pip defect entirely** — the mutation the census's amber exemption depends on. Arm B trades that for a **systematic 15–35 % loss on every correct mark**, which is precisely the failure §R23.3 predicted by reasoning (*"the boundary pixels would then leave every wedge's own isolated ink while still being painted over the composite — which points toward a systematic loss"*). That reasoning now has a measurement behind it.

**One honest note about my own tooling:** the scratch harness printed `ADOPTABLE` for Arm B, because its pass criterion tested only "≤ 1.000" and never tested "the correct controls stay silent". The printed verdict is a bug in the harness, not a result; the numbers in the same output refute it. **Neither arm is proposed. The seam stays, per §R23.3.**

### Test results

| Command | Result |
|---|---|
| `pytest tests/env -q --durations=15 -rxX` | **689 passed, 377 skipped, 0 failed**, 752.95 s — **no xfail, no xpass** |
| `pytest tests/env/test_render_audit_controls.py -q` | **80 passed**, 112 s |
| `pytest tests/env/test_dashboard_frames.py -q` (pre-fix, for the record) | 22 passed, **1 xfailed** (the strict xfail, on current code) |
| `scripts/eval/v1_path_guard.py check` | **10/10 PASS, FRAMES PASS ×3, RESULT OK, exit 0** — run **before and after** |
| matrix re-run, 18 frames | **0 co-occupancy findings**, 13.1 min |

New-test cost: the gap table is **79.2 s** (13 rendered frames) and the full-audit frame is **48.0 s**; both carry the `integration` marker.

### Speed check — skipped, with the reason stated

**No file on any training or rendering hot path was touched.** `git status` over `src/` and `configs/` is **empty**: the change is one offline audit instrument (`scripts/eval/render_layout_audit.py`) and two test files. Training speed cannot be affected, so a before/after SPS measurement would compare two identical code paths.

**The instrument's own cost was measured anyway**, like-for-like on the same 18 frames: **45.02 s → 43.58 s** mean per audited frame (−3.2 %; before 39.7–50.6 s, after 38.3–46.6 s). The change is a dict lookup per square and cannot plausibly account for it — both runs are within each other's spread, and the earlier one shared the machine with two pytest sessions while this one did not. **No regression.** Machine: container `docker-102`, Intel i9-7900X, 20 threads.

### Deviations from the plan — three, none silent

1. **`MINIMAP_FLOORS` and its guard test are more than §R23.1's literal seven rows.** The plan says to change the constant at one call site; I made the floor a **lookup keyed by path** and added a test that the arena's constant is not named inside the rule. Reason: the brief required that a future path must not be able to inherit the arena's floor *by omission*, and a renamed assignment does not give that — it is the exact shape of the original defect. No behaviour changes for the three existing paths.
2. **The correct side of the gap table measures 0.9375, not the plan's 0.9412** (Part 4). Reported, constant unchanged.
3. **The optional variant was run** (Part 6), because the required work finished with capacity to spare. It shipped nothing.

**No file outside §R23.1's own table was modified.** `docs/develop/INDEX.md`, `SAVED_RUN_CONFIG_COMPAT.md` and the diary files belong to parallel sessions and were left alone — they are staged in the shared index by another session and **nothing was staged or committed by me**. The plan's frontmatter `last_updated` already reads `2026-09-17`, so no change was needed there and **`regen_dev_index.py` was deliberately not run**, which would have rewritten the index another session is holding.

### Prior art

Grepped `docs/develop/active/issues/KNOWN_BUGS.md` directly (sub-agents cannot spawn `bug-curator`): **no row matches** `render_layout_audit`, `SURVIVAL_MIN`, `minimap`, `wedge`, or the audit's constants. The only nearby row is the **fixed** `Collection`-enumeration defect and its still-open follow-up (assert the enumerated artist set accounts for the full canvas ink), which §R23.6 item 1 already carries and which this change does not touch — it alters a constant and a call site, not enumeration. §R23.6 item 2 records `senior-developer`'s recommendation of **no row** for finding D; nothing measured here changes that, and **Part 5's above-1.000 observation is new and unrecorded** — if anyone thinks it earns a row, `bug-curator` owns that call.

### Does CP2.8 close? **Yes**

Against the checkpoint's own clauses: every matrix cell, every checked frame, **0 findings** from `cell_overdraw` and from `minimap_overdraw` alike (18/18); the five archetypes rendered and looked at, and the mutations failing on the **real** painter, were discharged by the §R22.7 pass and are unaffected by a change to one constant; M-F4 and M-F5 fire; the caption is present on every frame holding a shared square (0 `minimap_caption`); the rim-pip/identity-pip clause is **discharged** by §R22.3's retirement of the rim pip; the evidence lives in `tests/env/test_dashboard_frames.py` under the `integration` marker; and the wall-clock per audited frame is stated with the machine. §R23.4's four remaining items — the seven rows, the four-member family and gap table, the re-run, the cost — are all done.

The only clause-adjacent finding left on these frames is `panel_absent: Olfaction` on M5, which §R22.9 assigns to **CP2.7** and explicitly not here.

Implemented by: developer

---

## Implementation Report — Phase 3 (CP3): the V2 entry point that writes videos (2026-09-17)

> **Implemented by**: developer

### What this is, in plain words

Everything built so far could draw **one picture** of one recorded moment. Nothing
turned those pictures into a **video you can watch**. This phase adds the one
missing piece: a script that takes a folder of recorded episodes and writes MP4s.

It is a **separate script on purpose**. The renderer training and evaluation
actually use is frozen for the duration of this work — that was the user's
condition — so the new one is a second entry point that writes to a different
folder (`videos_v2/`, never `videos/`), is called by nothing automatically, and
has no flag that could delete anything. Which renderer you get is decided by
which of the two scripts you run, and by nothing else.

**The deliverable is a real video**: a full episode of the campfire world,
75 steps, 15 seconds, 1440 × 896 — path and numbers below.

### Files changed

| File | What it does |
|---|---|
| `scripts/eval/render_recordings_v2.py` (new) | The entry point. Pool, one task per episode: build an `EpisodeRenderer`, loop `frame(t)`, `close()`, write the MP4 through `save_jax_video` imported read-only from the frozen renderer. Probes every written file's frame count. `--workers`, `--fps`, `--concat`, `--skip-existing`, `--max-episodes`, `--stride`, `--output-dir`, `--benchmark`. **No** `--cleanup-per-episode`. |
| `tests/scripts/test_render_recordings_v2.py` (new) | 8 tests: V1's MP4 bytes byte-identical after a V2 render of the same directory; V2's output only under `videos_v2/`; decoded frame count == recorded step count; `--skip-existing` ignores `videos/`; the concat refusal fires and is actionable; a real run shares one signature; an unrenderable recording fails loudly and alone; no deleting code path. |
| `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` | §1c row (test's bare import + its two subprocess script paths), §3 roll-up row (hand-run only; **no `src/` caller**, deliberately), and a §4 Cluster B sentence — the new script is a second renderer coupled to the same recording format, so a format change breaks both. |

### The design, and why the parallelism is what it is

**Measured first, copied second.** V1 uses a `ProcessPoolExecutor` with one task
per episode, and the obvious move was to copy that shape. I measured instead:
one V2 frame of M4 costs **223.6 ms median** (75-step episode, first 5 excluded)
and the per-episode setup costs **3.3 s**. So a frame is cheap — the ~44 s/frame
figure in earlier reports is the **pixel audit**, which does N+1 renders per
frame to isolate every artist, and is not what plain drawing costs.

That measurement decides the shape: the work inside one episode is a serial loop
of cheap frames sharing one built figure, so there is nothing to parallelise
*within* an episode; the parallel axis is *across* episodes, exactly as V1 has
it. **One task per episode, kept.** What I changed is the default worker count:
V1 defaults to `cpu_count - 1` (19 here) regardless of how many episodes exist,
and each V2 worker holds a whole figure with ~1000 artists (**755 MB peak RSS**
measured). The default is therefore `min(number of tasks, cpu_count - 1)`, so a
two-episode directory starts two workers rather than nineteen idle ones.
`--workers` still overrides.

**Three properties are checked rather than assumed.**

1. **Frame count, probed off the finished file.** After each MP4 is written it is
   re-opened and **decoded** — by `ffprobe` (`-count_frames`), a different
   program from the one that wrote it, with an imageio fallback that still
   decodes. A mismatch is reported and the run exits non-zero. Asking the writer
   how many frames it wrote would answer the wrong question.
2. **The concat cannot change shape mid-video.** Each worker returns its
   episode's `layout_signature()`; `--concat` refuses unless all agree, naming
   the episodes on each side.
3. **No deleting code path at all.** No `--cleanup-per-episode`, and no
   `unlink`/`rmtree` anywhere in the file — asserted by a test.

**Copied, not imported, per §D1.3/§D5.4:** V1's `_raise_fd_limit`, and
`async_render.py::_render_env`'s CPU-only env pinning (`JAX_PLATFORMS=cpu`,
`CUDA_VISIBLE_DEVICES=""`), set at module import before anything pulls in JAX.
**`_load_icons` is never called** — that cache is process-global and ignores its
argument after the first call (plan finding #48), so priming it from a V2 worker
is exactly how "V1 is unaffected" would quietly stop being true. V2 draws its own
vector forms and needs no icon cache.

### The deliverable video

`results/render_audit/recordings/videos_v2/M4/episode_000002.mp4`

| | |
|---|---|
| World | M4, the maintained campfire thermal world (10 × 10, whole world at 50 px a square) |
| Episode | 2 — **the longer of the two available**, 75 steps against episode 1's 24. This is the loosened recording world (the 2026-09-16 demonstration loosening), which is why it runs long enough to show behaviour rather than an early death. |
| **Frames / steps** | **75 / 75** — equal, decoded from the file with `ffprobe` |
| Duration | **15.000 s** at 5 fps |
| Size | **287,510 bytes** (281 KB), 1440 × 896 |
| sha256 | `4f3bd5350f4bc49565ffd386e1432798addf36f0282190602fb5b7f4b4834cfc` |

Also written, from the same run:
`.../videos_v2/M4/episode_000001.mp4` (24 frames / 24 steps, 162 KB) and the
concatenation `.../videos_v2/eval_M4.mp4` — **99 frames = 24 + 75**, 19.8 s,
402 KB, `31e676c6…`.

**Determinism, verified rather than assumed.** The whole directory was rendered
twice into separate output folders and every file hashed: per-episode **and**
concatenated MP4s are **byte-identical across runs**. That is what makes the
frame baseline meaningful — a video that differed run to run could not be
compared to anything.

### Test results

| Command | Result |
|---|---|
| `pytest tests/scripts/test_render_recordings_v2.py -q` | **8 passed** in 65 s |
| `scripts/eval/v1_path_guard.py check` (before implementation) | **PASS=10**, ACCEPTED=0, ATTRIBUTED=0, UNATTRIBUTABLE=0, **FRAMES PASS ×3**, `RESULT: OK`, **exit 0** |
| `scripts/eval/v1_path_guard.py check` (after) | identical — **10/10 PASS + FRAMES PASS ×3, exit 0** |
| `render_recordings_v2.py <M4> --concat` | exit **0**; 24/24, 75/75, concat 99/99 frames verified |
| `render_recordings_v2.py <M4> --skip-existing` | exit **0**, "All selected episodes already rendered under videos_v2/" |
| `render_recordings_v2.py <M7> --concat` | exit **1**, every episode reported with its full traceback, nothing written |

One test failed on first run and it was **the test's fault, not the script's**:
it grepped the source for `--cleanup-per-episode`, and the module docstring names
that flag in order to say it does not exist. A check that cannot tell an
explanation from an implementation is not measuring anything, so it now asserts
on the real interface (`--help`) and on `add_argument` — recorded because the
first version would have passed for the wrong reason if the docstring had been
worded differently.

### How an unrenderable recording behaves

M7, M8 and M9 are trained-policy recordings from earlier in the year. Their
pickled `EnvParams` predates the body-temperature system, and the frozen
`sensor.py:577` reads `params.thermal_enabled` unconditionally, so they raise
`AttributeError`. Run against M7's directory, the script now:

* renders each episode as its own task, so one bad recording **cannot abort the
  batch** — every other episode still renders;
* prints the **full traceback per failed recording**, naming
  `panels.py:184 → sensor.py:577` and the missing attribute, so the cause is on
  screen rather than inferred;
* closes with `N recording(s) could not be rendered` and
  "Nothing under `videos/` was touched";
* **exits 1**, so a failure cannot pass for success in a script or a CI step.

Verified on the real M7 directory (all 10 episodes fail, exit 1) and, in the test
suite, on a mixed directory where one episode is corrupt and the good one still
renders to a probed MP4.

### Speed check — skipped, with the reason stated

**No hot-path code was touched**: this change adds one new script and one new
test, and edits one document. Nothing under `src/`, `configs/`, the env step, the
model, or the observation pipeline changed — the guard's 10 frozen files are
byte-identical and V1's raw frames still hash to their baseline. A training
speed measurement here could not differ from noise.

Rendering speed, which this change *is* about, was measured anyway via the new
`--benchmark` mode (§D5.3), M4, this container (Intel i9-7900X, 20 threads),
94 warm frames per renderer:

| | median | p95 |
|---|---|---|
| **V1** (frozen production renderer) | **312.9 ms** | 476.5 ms |
| **V2** (this renderer) | **181.7 ms** | 191.3 ms |

Ratio **V2/V1 = 0.581**; V2 setup 2150 ms, V1 first frame 776 ms, peak RSS
755 MB, 15 open fds. Consistent with Phase 2's 0.563 and, like it, **not CP0.4 or
CP4** — those need a lab node, a pool worker and ≥ 200 frames. Recorded as
context, not as a gate.

### Deviations from the plan — none silent

1. **CP3's "for all cells including M7–M9" is not met, and the plan's own
   re-entry mechanism cannot meet it.** Revision 13 moved M7–M9 to a "Phase 1
   `_recording_flag` gate", expecting §D4.1's absence-shaped reader to unblock
   them. It cannot: `_recording_flag` governs what the **package** reads off
   `params`, but the `AttributeError` is raised *inside* the frozen
   `sensor.py:577`, reached from `panels.py:184`'s call to
   `get_observation_breakdown(params)`. No amount of care inside
   `src/environment/dashboard/` intercepts an attribute read that happens in a
   file this plan may not edit. Reproduced on all three cells. **Two mechanisms
   exist and both are `senior-developer`'s call, not mine:** wrap `params` in a
   proxy that supplies pre-thermal defaults at the package boundary before
   calling the frozen breakdown, or defer to the retirement gate where the frozen
   file may be edited. I implemented neither and invented no third.
2. **The concat's "doctored two-param-set dir" is tested as a function, because
   such a directory cannot be built.** A recordings directory holds exactly one
   `run_meta.pkl`; every episode in it renders from those same params; and a
   layout signature is a pure function of params. So two episodes of one
   directory **always** share a signature whatever their payloads hold. The
   refusal is therefore exercised directly (`_assert_single_layout` with two
   different signatures → `SystemExit` naming both sides), and the real-directory
   case asserts the opposite — that a genuine run shares one. The plan's clause
   "trips on the doctored dir" should be reworded to name the function.
3. **The concatenation drops V1's 5-frame padding between episodes.** V1 holds
   each episode's last frame for 5 extra frames ("legacy behavior"). Keeping that
   would make the concat's frame count `steps + 5 × episodes`, and CP3's bar is
   *frame count = steps*. No padding: `eval_M4.mp4` is exactly 24 + 75 = 99.
4. **`--concat` covers every selected episode, not only the ones rendered this
   run.** V1 concatenates its `tasks` list, so with `--skip-existing` an episode
   already on disk is silently **left out of the consolidated video**. V2
   concatenates every selected episode whose MP4 exists. Signatures are asserted
   over the episodes this run actually rendered (a skipped one reports none).
5. **A `videos/` sibling is not created, looked at, or needed.** V1 derives
   `run_root = rec_dir.parent.parent` and so does V2, but only to place
   `videos_v2/`. For the M4 fixture that is
   `results/render_audit/recordings/videos_v2/`, and no `videos/` directory
   exists anywhere under `results/render_audit/` after any run above.
6. **Worker default is `min(tasks, cpu_count - 1)`**, not V1's flat
   `cpu_count - 1` — see the parallelism section; each worker holds a 755 MB
   figure, so idle workers are not free.
7. **`--benchmark` is implemented to §D5.3's four reported quantities** (setup,
   median/p95 with the first 5 excluded *and* reported, RSS, open fds) but its
   "RSS after 10 episodes" clause is reported over the episodes actually present
   — M4 has two. CP4 remains unrun.

### Prior art

Checked `docs/develop/active/issues/KNOWN_BUGS.md` directly (sub-agents cannot
spawn `bug-curator`): `grep -in 'render\|video'`. The dashboard defect rows
(D1–D13), the `OBS` mis-captioning (D10), the frozen renderer's icon-cache
hazard and the Dreamer "no noise-free observation" row all already point at this
plan. The wiki's `render_recordings_output_path_collision` is the derived-path
collision §D5.4 cites, and the separate output folder is what avoids it.
**Nothing new to file.** Deviation 1 is a gap in *this plan's* re-entry
mechanism, caught before any code shipped, so it belongs here rather than in the
registry — if `senior-developer` disagrees, `bug-curator` owns that call.

### Blockers and follow-ups

- **For `senior-developer`:** rule on deviation 1 (how M7–M9 re-enter, if at all
  before the retirement gate) — this is the only thing standing between CP3 and a
  tick; reword CP3's "doctored dir" clause per deviation 2; and note that
  `--benchmark` now exists as the home for CP4, which is still unrun.
- **Not done and not hidden:** CP4 (the speed gate on a lab node) and Phase 4
  (the viewer) are untouched. No file was staged and nothing was committed.

Implemented by: developer
