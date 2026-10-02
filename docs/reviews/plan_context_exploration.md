# Plan review — hidden context and exploration in larger level-05 worlds

## Verdict

**NOT READY.** Two Critical findings, seven Moderate, four Low, four open assumptions. Both
Criticals are cheap to fix — one is a mislabelled axis, the other a mis-specified set of
contexts — and both are fixed in the plan text plus one measurement the existing scripts already
know how to make. Nothing needs new environment code.

**What the plan is, in plain language.** The campfire world (level 05) is a 10 × 10 grid where
smells carry 20 cells, so the agent senses almost everything at once and a plain network can
simply react. The plan asks three questions before any training: (1) do today's two trained
agents already behave differently in dangerous and safe episodes at the same body state — that
is, do they infer a danger level they cannot see; (2) would a perfect agent even gain from knowing
the danger level, measured with the balance study's ideal planner; (3) which bigger worlds (15 × 15,
20 × 20) with shorter smell ranges and fewer, longer-lasting food items keep the three needs
balanced while making the search for food a real task. The verdict feeds the choice of worlds for
the next round of training, so a wrong answer here steers weeks of GPU time.

**Why NOT READY, in one paragraph each.**

*Part 1 measures a sensed signal and calls it hidden.* On a 10 × 10 grid the farthest two cells are
12.7 apart and the smell radius is 20, so every hunting predator is inside the agent's olfactory
field on every step of every episode. The recordings show exactly the "adaptation" the plan would
report: the ordinary agent spends 15 % / 35 % / 54 % of its steps in a bush in episodes with 0 / 1 / 2
predators. That is a reaction to a smell the agent has right now, not an inference about a hidden
episode-level variable, and the plan's rule ("behaves differently at matched body state ⇒ adapting")
would read it as the latter. The only genuinely hidden axis is the ambusher count (ambushers have an
all-zero smell vector), and there the effect is small: bush share 24 % vs 28 %, damage per exposed
step 0.51 vs 0.73, for low (2–5) vs high (9–12) ambusher episodes.

*Part 2's contexts are far narrower than the real ones.* The plan uses the balance study's hazard
scalings ×0.5 / ×1 / ×2 as the danger contexts. Measured from the same recordings, the real contexts
are 0.20 / 1.11 / 2.62 injury per exposed step for 0 / 1 / 2 predators — ×0.3 to ×4.1 of the pooled
0.64, a 13-fold range rather than 4-fold — and they differ in shape (predators hit eating and moving
agents; ambushers only moving ones). In 0-predator episodes 10 % of episodes end in death, in
2-predator episodes 97 %. A value-of-information computed on ×0.5–×2 is a lower bound that can turn
a real "worth knowing" into the plan's pre-registered "danger variation is unlikely to separate the
agents" — a wrong negative that would shelve the direction.

## Severity legend

🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run · 🟢 Low = cosmetic ·
❓ Open = an assumption nobody has verified yet.

## Findings

| # | Sev | Where | Issue | Suggested fix | Owner |
|---|---|---|---|---|---|
| C1 | 🔴 | STUDY_PLAN §Part 1 (lines 11–13, 26–34) | Predator count is not hidden: `sensor_radius 20` ≥ the grid's diagonal (12.7), and `sense_resource` masks on `dist <= radius` with no amplitude threshold (`src/environment/sensor.py:23`), so predators are in the smell field on every step. Measured bush share by predator count 0/1/2 = 0.148 / 0.347 / 0.543 (ordinary agent, Wave-2 block 0, 5,000 episodes) — the plan's rule would call this adaptation to hidden context. Ambushers (smell vector all zero; count in `res_allocated` × manifest `res_type == 1`, not `res_active`) are the only hidden axis; their effect is small (bush 0.238 vs 0.275). A second confound: mean episode length is 454 / 201 / 121 steps by predator count, so matched-body-state steps come from different phases of the episode, and with 10⁶ episodes any nonzero gap will be "significant" — the plan pre-registers no effect size. | Make ambusher count the primary hidden-context axis. Report the predator axis as "sensed threat", and if it is kept as a context, match additionally on the recorded true olfactory animal channels (`obs_true`, 5 cells × 5 channels) or on "no animal smell this step". Add time-in-episode (or steps since last hit) to the matching. Pre-register the smallest share difference that counts as adaptation (e.g. 5 points on cover share), not only a bootstrap interval excluding zero. | experiment-designer |
| C2 | 🔴 | STUDY_PLAN §Part 2 (lines 41–47) | Contexts = hazard ×0.5 / ×1 / ×2 (the balance study's *diagnostic* axis, M6 there: "no config knob"). Real contexts measured from the same recordings: injury per exposed step 0.201 / 1.108 / 2.622 and predator-hit probability 0 / 0.012 / 0.033 for 0 / 1 / 2 predators; ambusher-hit probability 0.0027 vs 0.0097 for low vs high ambusher count. The ×0.5–×2 band covers about a third of the real range and none of its activity structure, so the value of information is under-estimated and the pre-registered negative reading can fire wrongly. The threshold "under 2 survival points" is also undecidable as written (percentage points of survival share, or mean survival steps?) and sits at the 2,000-start sampling noise (SE ≈ 1 pp); "choices differ in under 10 % of states" names no tie margin. | Build the three contexts from per-predator-count hazard bins measured with the existing `measure_hazard_bins` machinery conditioned on `animal_active` (both agents; context prior 1/3 each — counts 1730 / 1684 / 1586 in block 0); optionally cross with the ambusher band. "Average context" = the pooled bins the balance study already uses (the optimal memoryless policy under the prior, which is the right no-inference baseline). State the units of the 2-point threshold, use ≥ 3 rollout seeds or 10,000 starts with an interval, and name the tie margin (0.5) for the choice-difference share. | experiment-designer |
| M1 | 🟡 | §Part 3 Balance (line 74) | Hit odds are scaled with predator density only. They were measured at smell radius 20, where the agent has warning of every predator; at radius 3–8 it loses the warning, and predators pounce from 2–3 cells with sight 1–7, so hit odds per exposed step rise in exactly the worlds the study wants. Criterion (c) "survival ≥ 80 % of today's" is then optimistic. | State it as a limit and bracket it: solve each world at hazard ×1 and ×2 and require a candidate to pass (a)–(c) at both; or say plainly that the trained-agent balance search, not this planner, decides survival. | experiment-designer |
| M2 | 🟡 | §Part 3 Worlds measured (lines 60–69) | Density scaling has no config plan. Every placement box is a hard-coded 1-based `[[1, 1], [10, 10]]`: food and ambusher `spawn_area`, predator and rabbit `spawn_area` + `patrol_area`, rock / bush / campfire `area`, and `location_areas` grass `area` (`configs/environment/default.yaml:29,43,72-73,98-99,103,111,132`; `05-campfire_thermal_10x10.yaml:109,128,148`). `Config.merge` replaces lists wholesale, so a 15 × 15 world must restate the full resources / entities / obstacles lists. Campfire `edge_margin: 2` insets the (widened) area at load (`config_loader.py:375`). `min_fire_separation 4` is enforced inside the placement scan (`core.py:1335-1406`), not at load, so 4–12 fires at separation 4 in a 16 × 16 inset that cannot be packed fall to the registry's known silent fallback — the entity is parked at cell (0,0) — not to an error. Rounding of ×2.25 counts (food 1–4 → ?) is unstated. `placement.mode` must stay `per_entity` (`per_type` is refused with fire separation, `config_loader.py:2330`). | List these keys in the plan; the reset measurement must assert, per world, that entity positions span the whole grid, that no active entity sits at (0,0), and that the number of placed fires equals the number drawn. State the count rounding. Where the variant configs live (outside `basic/`, per the earlier decision) and who writes them. Mechanical validation to `env-config-reviewer`. | experiment-designer; env-config-reviewer |
| M3 | 🟡 | §Part 3 Search time (lines 57–58) | The validation is circular: at range 20 everything is smelled, so the forager's search time is the Manhattan walk — the same quantity `measure_world.py:164` already computes as the 4-step median. It cannot fail on the random-walk phase, which is the only new component. | Add a check that can fail: on an empty grid with one target and radius r, the forager's mean search time must match the numerically solved hitting time of the walk (a small Markov-chain solve) within 10 %; and median search must be monotone non-increasing in radius on every grid. | experiment-designer |
| M4 | 🟡 | §Part 3 Balance (line 72) | The planner takes one deterministic trip length per place; search times are heavy-tailed (geometric-like), so the median under-weights the mean and starvation risk lives in the tail — the median can be 8 while the mean is 20. | Feed the mean, or model search as a per-step find probability (1 / mean) the way E1 models relocation — `planner.py` already branches on stochastic outcomes. Report median, mean and p90 for every world. | experiment-designer |
| M5 | 🟡 | §Part 3 Balance (line 76) | "Deaths reported only, since the planner rarely starves" contradicts the inherited Revision-2 criterion 3 (gated when ≥ 5 % of starts die after step 20), and on a 20 × 20 grid with starts at food energy 0–200 and long searches, starvation becomes a real cause. | Keep criterion 3 gated exactly as inherited; report the starvation share per world. | experiment-designer |
| M6 | 🟡 | §Deliverables / Files (absent) | New scripts (the forager, world-measurement variants, config generation) need rows in `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` in the same commit; the plan does not say, and does not name where the code and outputs go. | Add a Files section as the parent study has (scripts folder, outputs under `results/analysis/`, map rows in the same commit). | experiment-designer |
| M7 | 🟡 | §Candidate rule (b) (line 80) | "Median food search ≥ 2 × today's" = 8 steps is arbitrary: 8 steps is small against the agent's 20-step planning horizon (γ 0.95) and against the starvation clock, and the crude forager can meet it on today's 10 × 10 at radius 5 without any change in what is hidden. | Tie the floor to something: the planning horizon (search ≥ ~20 steps), or exposure cost (search × hazard per step ≥ one bush-healing unit); or keep 2 × as the floor but say why, and lean on the ranking. | experiment-designer |
| L1 | 🟢 | §Part 3 Search time (line 56) | "Warmth found by feel" has no detection rule. Thermoception is a 5-cell relative stencil (`sensor.py:65-93`); the cell two steps from a fire reads ≈ −16.5 against −30, so a fire is felt from 2–3 cells away, not only on the ring. | Define detection as "any stencil cell warmer than the baseline by more than x", and say x. | experiment-designer |
| L2 | 🟢 | §Part 1 (line 31) | "Steps before the first bite" is per episode and not matched on body state (starting food energy is uniform 0–200). | Match on starting food energy, or drop it from the matched measures. | experiment-designer |
| L3 | 🟢 | §Part 3 Search time (line 54) | Rocks and fires are non-blocking in level 05 (`blocking: false`); the forager avoiding them is a choice the agents do not make. | Say so; or let the forager cross rocks and count the exposure. | experiment-designer |
| L4 | 🟢 | (verified, nothing to change) | Observation width is grid-independent: `get_observation_breakdown` (`sensor.py:561-618`) has no height/width term; the location sensor normalises by grid size (`sensor.py:123-128`); vision, olfaction and thermoception are fixed diamonds. Smell falls as 1/d (`sensory.decay_power 1.0`) with a hard Euclidean cutoff at `sensor_radius` and no amplitude threshold, so "any smell sensed" = any of the 5 sample cells within radius of a food item. | Record this in the plan so the next reader does not re-derive it. | — |

## Open assumptions

- ❓ Part 1 uses agents that started at 0 °C, untrained under any swept setting (stated in the plan; carried, not verified).
- ❓ "Measured in minutes" — a random walk on 20 × 20 at radius 3 can run for hundreds of steps per reset; the forager needs a step cap (say 2,000) and the share of capped resets reported.
- ❓ Whether the two agents' stores share `seed_base` (paired episodes) — if so, Part 1's agent comparison can be paired per episode; the plan does not use this.
- ❓ One archived config uses a 20 × 20 grid; not checked whether a larger grid was tried and rejected before.

## Passes with nothing to report

Data-loss hazards (analysis outputs and new configs only; no git operations). Fallback defaults (the plan adds no code paths; the new configs must use mandatory keys — `env-config-reviewer`). Survival not reward (Part 2 uses survival share and survival steps). Version numbers (none invented). Doc framing (the entry point is plain language). Prior art: the registry rows on ambushers-as-resources (fixed 2026-09-26, `res_type` filter) and on the silent (0,0) placement fallback are both relevant and are cited above; nothing new for `bug-curator`.

## Cost of being wrong

Parts 1 and 2 wrong in the way suspected → a false "today's agents already adapt" or a false "adapting is not worth it" verdict steers which worlds get trained next — weeks of GPU on the wrong question, or a live direction shelved on a wrong negative. Part 3 wrong → candidate worlds whose survival is overstated and whose density scaling silently did not happen, costing one ordinary-agent balance search (days). No unrecoverable loss.

## What flips the verdict

C1: ambusher count named as the hidden axis, the predator axis relabelled as sensed threat (or matched on the recorded smell), time-in-episode in the matching, and a pre-registered effect size — in the plan. C2: contexts rebuilt from per-predator-count hazard bins measured from the recordings, and the two thresholds made decidable (units, interval, tie margin) — in the plan, before Part 2 runs.

Reviewed by: plan-reviewer
