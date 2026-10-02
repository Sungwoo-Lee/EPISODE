# Injury-dependent behaviour — where the modulator makes a difference (analysis plan)

## Question

The page *Where Does the Modulator Matter?* (https://claude.ai/artifact/F2BKsyf87Ho1Vx9YAR5LoW)
compares two agents trained in the same worlds: an ordinary recurrent agent (the *control*), and one
whose network is adjusted at four places by a neuromodulator — a small side network that reads all
of the agent's inputs and rescales its layers (the *modulated* agent). Its Figure 9 replays both
agents in small fixed test scenes, starting uninjured or at injury 70. Re-read without the rabbit
as the only cue, that figure carries the clearest lead on the page:

- **Levels 04 and 05:** starting injured changes the modulated agent's hiding *more* than the
  control's in 14 of 15 scene versions (one tie), by +1 to +12 points. The modulated agent hides
  little when healthy and a lot when injured; the control hides a lot regardless.
- **The modulated agent's injury effect is steadier across training** — its checkpoint-to-checkpoint
  standard deviation is 3–8 points where the control's is 11–16 in the same scenes.
- **Level 06 reverses it** in the two scenes with no fire (0 of 6), with and without level 06's
  injury-driven sensory noise, and is roughly a tie with a fire present.

The project's target is **state-dependent behaviour** — behaviour that changes with the agent's
internal state. This plan investigates *injury-dependent* behaviour in its own right (any cue, or none),
asks where, how and why the modulator strengthens or weakens it, and reorganises the page around
it. It is exploratory: the aim is clues and directions, not a verdict. Every comparison is one
training run per agent.

## Decisions (user, 2026-09-24)

| decision | choice |
|---|---|
| starting-injury levels in the scenes | 0, 10, 20, … 90 (ten levels) |
| trained agents | Wave 2 (`bq2cover`), levels 02–06, control vs full modulation; level 06 in both noise versions |
| checkpoints replayed in scenes | all 50 |
| observation manipulation (change only an input the agent receives; the world keeps the truth) | included, as a general reusable tool (below), not an injury-only script |
| page | reorganised: injury dependence is the main body; the current analyses become the appendix; same URL |

**Reading rule, fixed before the data (plan-reviewer ❓).** "The modulator strengthens injury
dependence" is written on the page only where the between-agent gap exceeds the across-checkpoint
spread (standard deviation over the newest 20 checkpoints) of *both* agents, and holds in the same
direction in most scene versions of that level. Anything weaker is reported as a lean, with its count.

## Workstreams

### A. Injury-level scene battery (the dose-response in controlled scenes)

- **Configs.** New generator `configs/environment/experiment/behavior_probes/injury_grid/generate_injury_grid.py`
  reading the maintained core probes (`behavior_probes/core/avoidance/avoid_{none,pred,rabbitwander}_inj00.yaml`)
  and writing one config per starting injury, setting **both** `start_injury_low` and `start_injury_high`
  to the level (the start is drawn uniformly between them), plus the four thermal versions (neutral,
  cool, fire beside the bush, fire away) × two noise batteries by importing `build()` from the thermal
  generator, so the scene is never restated. Scenes: no animal, predator, wandering rabbit. **The
  chasing rabbit is dropped** — the glued-rabbit environment bug (Known Bugs row 99, open) makes its
  within-reach measure a mirror of hiding.
- **Asserts** (in the generator, fatal): observation width (52 core, 58 thermal); the loaded
  `start_injury_low` and `_high` both equal the file's level; the bush blocks animals; full-arena view.
- **Sweeps** through the existing dwell-sweep driver (CPU, as before), 30 episodes × 50 checkpoints,
  fresh `output_dir`s: levels 02–04 on the core set; level 05 on four thermal clean versions; level 06
  on four thermal versions × {clean, noise-matched}. 3 scenes × 10 levels = 30 conditions per
  world-version; about 45,000 checkpoint-evaluations. At the smoke run's rate (48 per minute per node)
  that is ~16 node-hours: ~2 h on eight free nodes, chosen from live GPU/diary state at launch.
- **Level 02** trains with no random injured start, so injured starts are off its training
  distribution (caption note). **Its modulated run is still training** (43/50 at 12:00, ~1/hour); it
  runs on the checkpoints that exist and is topped up later — the driver schedules only checkpoints
  newer than those recorded.
- **Predator scene above injury ~50 is partly a survival curve** (a bite does 15–45, death at 100):
  `survival_steps` is shown beside every predator curve, points where agents die early are marked,
  and the injury-dependence reading leans on the no-animal and wandering-rabbit scenes.
- **Env-config-reviewer** audits the generated battery before any sweep launches.
- **Spot check:** the injury-0 and injury-70 conditions must reproduce Figure 9's existing values for
  the same checkpoints (same scene, same seeds, same code).

Figures (newest 20 checkpoints unless stated; spread = across checkpoints):
- **A1 dose-response curves**: time in the bush against starting injury, both agents, per level,
  scene and version. Read for size (0 → 90 change), shape (gradual vs switch-like), where it bends.
- **A2 steadiness over training**: the 0 → 90 change at each of the 50 checkpoints — when injury
  dependence appears during training, and how much it wanders.
- **A3 level contrast**: one summary number per agent, level and version (slope of hiding on injury),
  lining up levels 02–06 so the level-06 reversal is read against its neighbours.

### B. Observation manipulation — a general tool — and step-by-step scene recordings

**Tool: `scripts/analysis/obs_manipulation/run.py`** (run-agnostic; any run, any input, any world).
Built on `scripts/analysis/nmn/replay.py::load_agent`, which refuses an incomplete restore.

- **Two modes.** `--mode live`: the agent plays episodes in `--world` (a probe config, or `training`
  for its own world) with the manipulation applied, so its behaviour can change. `--mode replay`:
  recorded episodes from a trajectory store are fed back through the network with the manipulation
  applied; the agent does not act, and the change in its move preferences (and modulator output) is
  measured.
- **What to change** is a YAML file, every key mandatory:
  `sensor` (a name from the run's own observation breakdown, e.g. `Interoceptive Nociception`),
  `element` (index within that sensor), `op` (`set` | `add` | `scale`), `values` (a list — one
  condition per value, all on the same episodes), `steps` (`[start, end)` window; `null` end = to the
  end). Several entries apply together. An unknown sensor name or out-of-range element fails and
  lists the valid names.
- **Where in the step.** After the sensors build the observation — including level 06's perceptual
  noise — and immediately before the network. The world, healing, animals and death follow the true
  state. The modulator reads the whole observation (`input_sensors: all`), so it receives the
  manipulated value too: every result is the **joint effect through the main network and the
  modulator**, stated in docstring and captions (routing a different value to each needs a network
  change; listed as a later extension). At level 06 the noise magnitude still follows the *true*
  injury, so an unhurt agent made to feel injured still senses clearly — the manipulation separates
  injury's two routes (felt number vs blurred senses), and captions say so.
- **Seeds.** Live mode draws its seeds from the world config's own `behavior_measures.eval_seeds`
  (via `load_behavior_measure_cfg`), exactly as the dwell sweep does — not `replay.py`'s 90,000 block.
- **Output**: one row per checkpoint × condition × episode (time in bush, survival steps, distance
  to nearest animal, …); `--record steps` adds per-step arrays (square, in-bush, animal distance, true
  injury, felt injury, move preferences, modulator gain/offset). A manifest stores the manipulation
  file, run, checkpoint, seeds, device and git SHA.
- **Built-in checks, every call.** (1) A hidden `add 0` condition must reproduce the unmanipulated
  run move for move, or the run stops. (2) Values outside the range the input took in training are
  allowed but flagged. (3) Probe observation layout must equal the agent's, sensor by sensor.
- **Parity with the dwell sweep (once, before any figure):** CPU, the worker's environment variables,
  compared **per episode** using the sweep's own measure function (`episode_measures`, which averages
  over the step-0 snapshot as well) against the seeds recorded in the sweep's `.rec.gz`. Any differing
  episode is logged with the first differing step; a mismatch on CPU blocks the tool; GPU is used
  afterwards only if it reproduces the CPU values, otherwise the tool runs on CPU.
- **Replay-mode parity:** the store records `obs_noised`, the observation the policy actually
  received (float32 in these manifests). Rows follow the arrival convention — `action[t]` was chosen
  from `obs[t-1]` — so the unmanipulated pass must reproduce `action[t]` from `obs_noised[t-1]` exactly.
- **Default manipulations for this study:** `set` felt injury 0…0.9 from step 0 (the ladder), and
  `add` +0.1…+0.5 (keeps the natural rise and healing — the realism check beside the ladder).
- `SCRIPTS_DEPENDENCY_MAP.md` updated in the same commit as the tool.

Figures:
- **B1 time course**: time in the bush against step, one line per starting injury, with true and
  felt injury below — how long the injured behaviour lasts and whether it follows the healing.
- **B2 exit threshold**: felt injury at the moment the agent leaves the bush. Tight and low means
  "stays until healed"; comparing agents shows whose leaving is set by injury.
- **B3 manipulation in scenes**: an unhurt agent made to feel injury 0…0.9 — time in the bush against
  the manipulated value, beside A1's true-injury curve. Same shape ⇒ the agent acts on the feeling.
- **B4 modulator against felt injury (modulated agent only)**: does the modulator's output follow felt
  injury in natural (unmanipulated) scene episodes, and does that link break at level 06 in the no-fire
  versions? Read from unmanipulated runs; under manipulation the link is partly by construction.

### C. The training world (million-episode recordings)

Stores exist for Wave 2 levels 04–06 (1M at the final checkpoint, `results/trajectories_basicq2_w2`;
five late checkpoints × 100k, `results/trajectories_basicq2_late`). **Levels 02/03 are being collected**
(launched 12:03 on 109–111: lvl02 control, lvl03 control and modulated). Verify each store
(`--validate-only`, 400 parquet + manifest) before use; lvl02 modulated is launched only after it
finishes training. Nothing is relaunched into the same `out_root` while a collection is in flight.

- **C1 fine dose-response**: reuse `scripts/analysis/context_dependence.py` (its `randomised_early`
  causal panel already feeds Figure 2) with ten-point injury bins, rather than re-deriving: bush, rest
  and movement by starting injury over the first 25 steps (levels 03–06, causal) and by current felt
  injury over all steps (levels 02–06, observational, confounded with recent attack). Felt injury is
  read from the `Interoceptive Nociception` column of `obs_noised` at t−1 (Known Bugs rows 281/287).
- **C2 bush-exit rate against felt injury**: among in-bush steps with no animal within reach, the
  chance of leaving on the next step, by felt-injury bin — the training-world twin of B2.
- **C3 manipulation on recorded histories** (`--mode replay`): 2,000 episodes per run, felt injury
  shifted by `add`, change in move preferences and modulator output.
- **C4 steadiness**: C1 and C2 on the five late-checkpoint stores where they exist.

### D. The page

Same URL, reorganised. Title from *Where Does the Modulator Matter?* to one naming the new focus
(proposed: *Injury, Behaviour and the Modulator*; user can override). Main body: what injury
dependence means here → scene dose-response (A) → within an episode (B1, B2) → is it the feeling
(B3, C3) → the training world (C1, C2) → steadiness (A2, C4) → level 06 (A3, B4) → leads. Appendix:
the current sections unchanged except numbering. Built by `build_page.py` (guards unchanged); the
plan-reviewer checks the verdicts and the artifact-format-reviewer renders it before publishing.

## Verification summary

| step | check that would catch a failure |
|---|---|
| A configs | generator asserts; env-config-reviewer; load + reset of every file |
| A sweeps | every CSV has the expected checkpoint count; no `fail` markers; injury 0/70 reproduce Figure 9 |
| B tool | per-episode CPU parity with the dwell sweep; hidden `add 0` identity; layout assert |
| C collection | `run_collection.py --validate-only`; manifest seed contiguity |
| C3 | unmanipulated pass reproduces recorded `action[t]` from `obs_noised[t-1]` |
| figures | house guards (text size, overlap), data accounting emitted by each script |
| verdicts | reading rule above; plan-reviewer on the finished claims before publishing |

## Risks

1. **One run per agent.** Steadiness across checkpoints (A2, C4) is within-run.
2. **Off-distribution thermal scenes at levels 05/06**, and injured starts at level 02.
3. **Floors and ceilings** compress differences near 0 % and 100 %; log-odds shown where a claim rests on it.
4. **Felt injury lags the true injury** (alpha kernel τ = 3 steps, length 12, zero at reset) and
   **healing is fast while resting** (~5 points a step in cover), so an injured start is mostly an
   early-episode effect — B1 shows this; C1's causal window is the first 25 steps.
5. **Manipulation realism.** A constant felt injury never occurs naturally; `set` results are read as
   sensitivity, `add` as the more natural check.
6. **Predator scene survival truncation** above injury ~50.

## Feedback from plan-reviewer

*Reviewed 2026-09-24, before implementation. Verdict: **SOUND WITH CONCERNS** — no Critical finding; the
concerns below each cost a lost day or a misread figure, not a wrong conclusion, and each has a cheap fix.*

Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run · 🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

| sev | where | issue | fix |
|---|---|---|---|
| 🟡 | §B parity check | "Both are greedy and seeded, so they should agree exactly" assumes the same seeds. The dwell sweep's 30 seeds are **not** 0..29 and not `replay.py::episode_seeds` (90000+): `sweep_worker.sh` passes `--eval-n-episodes 30`, and `eval_rollout.py:989-994` takes the first 30 of the probe config's inherited `behavior_measures.eval_seeds: {rng: 42, sort: true}` (`default.yaml:580`, resolved at `config_loader.py:193-196`). Building the tool on `replay.rollout` with its default seeds guarantees the fatal parity check trips. | The tool derives seeds via `load_behavior_measure_cfg(probe_cfg).eval_seeds[:n]`, and asserts that list against the `seed` field in the sweep's `.rec.gz` recordings for the same checkpoint. |
| 🟡 | §B parity check | "Exact" equality is at the mercy of device and threading: the sweep runs on CPU with `JAX_PLATFORMS=cpu`, single-thread XLA (`sweep_worker.sh`). A GPU or multithreaded run can flip an argmax on a near-tie; over 30×100 steps that is rare but a legitimate mismatch would still be reported as "tool broken". Also the CSV value is a 30-episode mean rounded to 4 dp (`run_sweep.py:_measure_cell`), and per-episode `bush_hiding` is `mean(in_bush)` over **T+1 snapshots including t=0** (`avoidance_stats_heatmap.py:74-103`). | Run the parity pass under the worker's env vars on CPU; compare per-episode against the sweep's recordings (`load_episode` + `episode_measures`, imported, not re-derived), not only the rounded CSV mean; log the count of differing steps rather than a bare fatal. |
| 🟡 | §A sweeps, predator scene | Lethal-injury edge: death is only checked in the step (`core.py:355`, `new_injury >= 100`) and predator damage is 15–45, so any bite at start injury ≥ 55 kills. In `avoid_pred` the dose-response above ~50 is partly a survival curve — `bush_hiding` is averaged over the steps the agent lived. The plan's "injury 90 not lethal at reset" assert is vacuous (the loader already caps `high ≤ max_injury`; reset never kills). | Plot `survival_steps` beside A1 for every scene (project rule anyway); read the causal dose-response from the no-animal scene and label the predator-scene high-injury points as survival-truncated. Replace the reset assert with "no death in step 1 in the no-animal scene". |
| 🟡 | §B clamp, §B4 | The modulator reads the **whole observation** (`input_sensors: all` in all five modulated runs; `recurrent_ppo_network.py:512-516` slices `mod_in` from the same `x`). A clamp on the felt-injury slot therefore changes the modulator's input too — correct, and it must be stated: B3 measures the joint effect through both routes, and B4 "modulator follows felt injury" is partly tautological under a clamp. At level 06 noise-matched the noise sigma is gated on **true** injury (`sensor.py:434-441`), so the clamp leaves an injury-correlated signal (noise magnitude) in the observation. | State both in the tool's docstring and the B3/B4 captions. Optional extension: clamp only the trunk's copy or only the modulator's slice to separate the two routes. |
| 🟡 | §C | "Levels 02 and 03 have none — collect" is stale: the collection is already running (diary 12:03; `results/trajectories_basicq2_w2/*lvl02_t1none*`, `*lvl03_*` have manifests and parquet growing at 12:07). Re-launching into the same `out_root` is the hazard. | Change the C step to "wait for the running collection; verify 400 parquet + manifest per run (matches levels 04–06)" and launch only `lvl02_modulated` later. |
| 🟡 | §C1, C2, C3 | Prior art and the two known-bug rows in this exact class: the store now records `obs_noised` (float32 for these stores, manifest-verified), so **C3 is feasible from the store** without reconvolving; the reconstruction bug (KNOWN_BUGS row 287) was pre-`obs_noised`. But the row convention is arrival (`action[t]` was chosen from `obs[t-1]`, schema §1), and row 281 records a published figure that binned on the same row. C1's causal half already exists in `context_dependence.py` (`randomised_early`, fixed bins, first 25 steps, B0 entry measure) and feeds `a2_injury_dose.py`. | C2/C3 read felt injury from the `Interoceptive Nociception` column of `obs_noised` (index from manifest `observation_breakdown`) at row t−1; C3's parity aligns `action[t]` with the pass over `obs[0..t-1]`. C1 reuses `context_dependence.py` outputs or its binning code; do not re-derive. |
| 🟡 | maintenance contract | New `scripts/analysis/studies/injury_dependence/scene_replay.py` is a new inbound caller of `scripts/analysis/nmn/replay.py` (mapped with named callers) and a new hand-run entry point; the plan omits the `SCRIPTS_DEPENDENCY_MAP.md` update. (`generate_thermal_probes.py` is also unmapped today — not this plan's debt, but the new generator should be listed with it.) | Add the map update to the File Changes of the same commit. |
| 🟢 | §A generator | Source probes set `start_injury_low` **and** `start_injury_high` to the same value; the draw is `uniform(low, high)` (`core.py:1788`), and the loader raises if `low > high`. The assert list names only `_low`. | Set and assert both. |
| 🟢 | §A, level 02 | Level 02 trains with `random_start_injury: false` (its saved config), so any injured start is off-distribution for those two agents — injury there only ever arrived mid-episode with a contact-pain spike. A3 lines up in- and off-distribution agents. | Say so in the A3 caption. |
| 🟢 | §Risks 4 | "Builds over about 12 steps": kernel length is 12 but τ = 3 (`default.yaml:473-474`), so felt injury reaches most of its value in a handful of steps. Healing 5/step holds only while the agent **rests** in the bush (`core.py:287-316`, accelerating). | Wording. |
| ❓ | whole plan | No pre-stated reading rule: the page will be read as "the modulator strengthens injury dependence" even though the plan is exploratory. | State up front the rule already implied in Figures: a difference is reported only if it exceeds the across-checkpoint spread of both agents. |
| ❓ | §A sweeps | 45,000 checkpoint-evaluations (2.3× the thermal battery just run). Nodes and expected wall-clock are unstated; the incremental filter (`c > maxdone`) does protect partial progress. | Name nodes in the spec; expect >1 day. |

Assumptions the plan rests on (verified by me unless marked): sweep seeds reproducible from the probe config — **not in plan, see row 1**; store holds what the policy saw at float32 — verified (manifests); modulator reads the full observation — verified (five runs); injury 90 survivable at reset — verified (`max_injury: 100`, death checked in step only); raw `Injury` channel not observable, so felt injury is the only injury input — verified (`injury_observable: false`); `build_page.py` for the clue page exists — verified; level 02/03 store collection in flight — verified, plan text stale.

Not duplicated here: YAML/env mechanical soundness of the generated battery is `env-config-reviewer`'s (the plan already routes it); the bare-name import and repo-root depth hazards of the new scripts are `code-reviewer`'s once the code exists.

**Cost of being wrong:** the parity trap and the predator-scene survival confound each cost about a day (the first in debugging a tool that refuses to run, the second in a figure that has to be re-cut); the stale collection step risks a duplicated 3-run, ~24 GB GPU job. Nothing here loses data or changes training.

Owners: `developer` (tool, seeds, parity, C-alignment, map update) · `experiment-designer` (generator asserts, survival panel, captions, spec nodes) · `bug-curator` (nothing new to record; rows 281/287/99 apply as cited).

Reviewed by: plan-reviewer

### Author response (2026-09-24)
All rows folded into the plan above: seeds from `eval_seeds` and per-episode CPU parity (B); predator survival truncation and both injury bounds (A); joint-route and level-06 noise semantics stated (B); collection in flight, not relaunched (C); `obs_noised[t-1]` convention and reuse of `context_dependence.py` (C); dependency-map update (B); level-02 caption note; τ wording; reading rule and compute estimate. The clamp is renamed *observation manipulation* and generalised into a reusable tool at the user's request.
