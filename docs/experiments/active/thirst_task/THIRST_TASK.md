---
title: "Thirst task at three map sizes and three smell reaches: ordinary vs modulated agent"
topic: thirst_task
status: active
created: 2026-10-01
last_updated: 2026-10-01
wandb_tag: "rppo_thirst_*"
develop_link: docs/develop/active/thirst/THIRST_WATER_PLAN.md
---

# Thirst task at three map sizes and three smell reaches

> **Status**: DESIGNED 2026-10-01, **Revision 1** the same day (answers the plan review and the
> config review; §R1). Configs written and checked on real resets (§6). Nothing launched; no nodes
> chosen. Before a launch: plan-reviewer re-check of Revision 1, the pre-launch PI consultation,
> and the user's go.
> **Code**: frozen at the pinned launch commit `PIN_SHA_SHORT` and run from the detached worktree
> `.claude/worktrees/thirst-runs` (§9.3). Development continues in `.claude/worktrees/thirst`
> (branch `v5.0`). Outputs go to the shared folder, as in [[THIRST_PILOT]] §2.5.
> **Related**: [[THIRST_PILOT]] (level 06 is learnable; source of the speed and seed-spread
> numbers) · [[THIRST_WATER_PLAN]] (how water was built; Revision 2 = the pond smells only of
> food) · [[STUDY_PLAN]] in `context_exploration/` (larger worlds and smell reach, ordinary agent
> only) · [[PLACEMENT_FIXES_PLAN]] (the silent (0,0) placement fallback)

---

## Purpose (plain language)

The grid world now has a fourth body need, **thirst**, and one **pond** per episode to drink from
(level 06 of the training ladder). The pond smells exactly like one food item, so smell says
"something to eat or drink is over there" but not which; the agent must use its own body state
(thirsty or hungry) and remember where the pond is. The research reason for thirst is that the
right action now depends on **combinations** of body states, which is where an agent with a
**neuromodulator** (a small side network that rescales the main network according to what the
body feels) should beat an ordinary agent.

This experiment builds the arena for that comparison and runs a first screen. It trains the
ordinary agent and the modulated agent, **one training run each**, in **nine worlds**: three map
sizes (10×10, 15×15, 20×20 squares) crossed with three smell reaches (smell carries across the
whole map, 5 squares, or 3 squares). Bigger maps and shorter smell make the pond and the food
harder to find and to remember. Everything except the map size and smell reach is held at the
same **density**: a 20×20 map has four times the food, predators, fires and bushes of a 10×10 map,
and its pond is four times the area.

**What it asks.** (1) Does every world stay learnable: do both agents learn to eat and to drink,
and how much survival does size and short smell cost? (2) Is there any world where the modulated
agent survives clearly longer than the ordinary one? Success is measured in **survival steps per
episode**, never in reward.

**What it can and cannot show.** One run per agent per world is a **screen**. In the level-06
pilot, three runs of the same agent differed by about 2.6 % in survival, so a difference between
two single runs is only readable when it is larger than about 6 %, and that noise figure was
measured on the 10×10 map only. Any world where the modulated agent is ahead **or behind** by that
much is a **lead**: it gets two more seeds for both agents, under a decision rule and a compute cap
written down now (§5.4), before anything is claimed. The size and smell-reach patterns are
described, never tested, at one seed.

---

## R1. Revision 1 — response to review (2026-10-01)

Two reviews of the first version (commit `c631d8fa`) are kept intact at the end of this doc and
in `docs/reviews/`: the plan review ([[plan_thirst_task]], verdict NOT READY on one Critical
finding) and the config review ([[env_config_review_thirst_task]], safe to launch, one Moderate).
Every finding is answered in the body; this table says where.

| Finding | Answer | Where |
|---|---|---|
| Plan C1 🔴 / config M1 🟡: no code freeze | All 18 runs, every relaunch and every follow-up seed run from a **separate frozen worktree**, `.claude/worktrees/thirst-runs`, detached at one pinned launch commit (`PIN_SHA_SHORT`, the commit of this revision). Admin creates it with `git worktree add --detach`. Nobody edits it; it is removed only after the last run, follow-ups included, has ended and its outputs are confirmed in the shared folder. The launch script `cd`s there; the gate checks that `src` resolves under `thirst-runs`, that HEAD equals the pinned commit, and that no tracked file is modified. Gate tested: it fails on a wrong commit and on a modified tree, and passes its import checks. Pilot pre-flight and validity checks carried over, plus a check that each saved config has the Revision-2 smell and the cell's own size, pond and reach. The main worktree stays free for the placement fixes; a line in [[PLACEMENT_FIXES_PLAN]] K0 says the placement work never touches `thirst-runs` | §3.4, §9.2, §9.3, §7 |
| Plan M1: stop timing undefined | Stop boundary b\* is defined on data up to the 1 M mark; `S_final` and Δ are read on (b\*−1 M, b\*] for both runs whatever happens after. Checker = this session, polling WandB at least hourly. Stop = one `SIGINT` per run via `./terminate_command.py <NODE> "wandb-name <TAG>" --yes`, sent to both agents of the world at the first check after the rule fires. A trailing modulated run may stop short of its partner's count; both counts are recorded | §4 |
| Plan M2: "has learned" on survival only; a falling curve passes | "Has learned" also needs the thirst-death share under 0.10 in the latest block. The plateau needs each of the last two rises to be ≥ 0 and < 1 %. Two falls in a row are a flag | §4, §7 |
| Plan M3: follow-up not pre-registered | Leads of ≥ 6 % **in either direction** trigger seeds 43 and 44 for both agents. Three-seed decision rule: both new seeds have the lead's sign, and the three-seed mean is ≥ 6 %. Seed 42 is kept, with the selection caveat stated; the unselected two-seed mean is reported as the effect size. Cap: 300 GPU-hours, leads taken largest first. About one false lead is expected | §5.3, §5.4 |
| Plan M4: claims stronger than one seed allows | The size × reach refutation test is removed. §5.2 is descriptive only: at most "candidate for follow-up", never "supported". The exploratory pattern in §5.3 is "consistent / not consistent", and "not assessed" when there are no leads. The noise figure is marked 10×10-only, and the "≥ 10 % readable" line is made conditional on it | §5.2, §5.3, §5.4, Purpose |
| Plan M5: only episode-matched Δ | Equal-environment-steps read-out pre-registered beside every episode-matched number. A lead it does not support is labelled experience-sensitive | §5, §5.3, §3.5 |
| Plan M6: short reach also cuts predator, rabbit and bush odour | Stated. Injury added to the expected pattern (higher injury share at reach 5 and 3, at every size) | §3.3, §3.5, §5.2 |
| Plan M7: drinking and start hydration are not in the log | Stored-episode plan modelled on pilot §4.2: collector run from `thirst-runs`; checkpoints nearest 2 M, 4 M and b\*; drinking bouts; survival by start-hydration band; pond integrity checks; and the tools that must not be used | §5.5 |
| Plan L1: food regrowth on a fire / bush | Row added (≈ 2 % / ≈ 7 %) | §3.5 |
| Plan L2: evidence only in gitignored `tmp/` | Scripts, JSON, tables and maps committed in `checks/` next to this doc | §6 |
| Config O1 ❓: the (0,0) stop rule cannot fire | Reworded as an **accepted, unmonitored risk** (measured 0 / 2,000 resets per world), with a post-hoc check on the stored evaluation episodes | §3.5, §7, §5.5 |
| Config L1: pond near-field smell weakens with size | Row added with the reviewer's numbers | §3.5 |
| Config L2: registry wording | Entry tightened: `water.size` / `candidates` are set only in the two whole-map files | `CONFIG_CRITICAL_SETTINGS.md` |
| Config L3: frozen copies of the level-05 lists | No change. §9.3 notes that the frozen worktree also freezes `basic/` for the series | §9.3 |

---

## 1. Decisions (user, 2026-10-01; not reopened here)

| # | Decision | Where it lands |
|---|---|---|
| D1 | All worlds are level 06: the pond smells only of food, at the strength of one food item (`water.properties [1, 0, 0, 0, 0]`, THIRST_WATER_PLAN Revision 2) | inherited from `basic/06` + `default.yaml` |
| D2 | Three map sizes: 10×10, 15×15, 20×20. The 10×10 world **is** level 06; it is not copied | §3.1 |
| D3 | The pond scales with the map: 2×2 at 10, 3×3 at 15, 4×4 at 20 (4 % of the map each). Placement `list`, four corner candidates just inside a 1-cell margin. Per-cell smell `1/(h·w)` keeps the whole pond equal to one food item; verified on real resets (§6.1) | `water.size`, `water.candidates` |
| D4 | Everything else scales with area (×2.25, ×4), as the context-exploration worlds did: food 1–4 → 2–9 → 4–16 (12 bites each), campfires, rocks, bushes, hidden ambush predators, predators, rabbits. Every spawn and patrol area covers the whole map | §3.2 |
| D5 | Smell reach is a second factor: whole map, 5 squares, 3 squares (`sensory.sensor_radius`), at every size → **9 worlds** | §3.1 |
| D6 | Whole-map smell: `sensor_radius` at least the map's largest Manhattan distance | 20 / 30 / 40 (§3.3) |
| D7 | Budget 10 M episodes per run; early stopping allowed, on survival steps only | §4 |
| D8 | Agents: the ordinary / modulated pair of the level-06 pilot (`nmngaenorm_t1none` / `nmngaenorm_t16quad_ALL`) | §3.4 |
| D9 | **One seed per condition**: 9 worlds × 2 agents = **18 runs** | §2, §5.4 |

**Why a `configs/environment/experiment/thirst/` folder** when only `default.yaml` and `basic/`
are maintained (CLAUDE.md, "Config maintenance scope"): these eight worlds are one study's
worlds, not rungs of the training ladder. Putting them in `basic/` would make them maintained
ladder levels, which nobody decided. Under `thirst/` they follow the rule for every non-ladder
config: they stay correct for this study, and if a later config-system change breaks them they
are **not** migrated; a later study regenerates them. Each file's header says so.

## 2. Lessons carried over from the context-exploration study

The context-exploration study ([[STUDY_PLAN]], Parts 3–4) trained the ordinary agent, without
water, on larger and less smellable versions of level 05. Three of its findings shape this design.

1. **Food density decides whether a large world is learnable at all.** On 20×20 with only 1–4
   (or 1–2) food items the agent did not learn to eat for most of 2 M episodes (about 0.02 bites
   per episode against 35 in the 10×10 world) and starved after 70–80 steps. With food at the
   10×10 density (4–16 items, the "C4" world) it survived 0.88 as long as the 10×10 world after
   5 M episodes and passed every balance test. **Here every count is density-scaled (D4)**, so
   the sparse-food failure should not recur. The 15×15 world in that study was only run with 1–2
   food items, so its counts other than food are reused and food is scaled like everything else.
2. **Smell reach was confounded.** Its 20×20 worlds changed smell reach **and** food density
   together (C4: reach 5 with dense food; C3: reach 20 with sparse food), so the cost of short
   smell on a big map was never measured on its own. **Here reach is crossed with size** (D5),
   with density held, so the reach effect can be read at each size.
3. **Large worlds learn slowly, and an episode budget hides it.** C4 was still improving at 2 M
   and plateaued only between 2.4 and 5 M episodes; larger worlds also get fewer environment
   steps for the same number of episodes. **Here every run gets up to 10 M episodes**, the stop
   rule (§4) only fires on a measured plateau, and results report environment steps alongside
   episodes.

It also found that its world-picking simulation agreed with training in only 2 of 6 worlds, so
no simulation is used here: the worlds are trained, not predicted.

## 3. Experimental design

### 3.1 Factors and cells

| Factor | Levels |
|---|---|
| Map size | 10×10, 15×15, 20×20 |
| Smell reach (`sensory.sensor_radius`) | whole map (20 / 30 / 40), 5, 3 |
| Agent | ordinary (`t1none`, no modulator), modulated (`t16quad_ALL`, modulator on encoder, recurrent core, actor and critic, reading every sensor) |
| Seed | 42 for all 18 runs (config-owned; no `--seed` flag) |

Cell names: `g<size>s<reach>`, with `W` for whole map: `g10sW g10s5 g10s3 g15sW g15s5 g15s3 g20sW
g20s5 g20s3`.

### 3.2 What scales with the map (D3, D4)

Counts follow the context-exploration rule: `low′ = max(1, round(f·low))`, `high′ = round(f·high)`,
**round half up**, and a low of 0 stays 0; f = 2.25 at 15×15 and 4 at 20×20. At 20×20 every
count is exactly C4's. At 15×15 every count except food equals the context-exploration 15×15
worlds' counts; half-up rounding errs toward more of each thing, by at most half an item.

| Item (per episode, drawn uniformly) | 10×10 (level 06) | 15×15 | 20×20 | 15×15 rounding |
|---|---|---|---|---|
| Food items (12 bites each) | 1–4 | 2–9 | 4–16 | 2.25 → 2 |
| Hidden ambush predators | 2–12 | 5–27 | 8–48 | 4.5 → 5 |
| Predators (hunters) | 0–2 | 0–5 | 0–8 | 4.5 → 5 |
| Rabbits | 0–2 | 0–5 | 0–8 | 4.5 → 5 |
| Campfires (2-square edge inset, 4 apart) | 1–3 | 2–7 | 4–12 | 2.25 → 2; 6.75 → 7 |
| Rocks | 6–12 | 14–27 | 24–48 | 13.5 → 14 |
| Bushes | 4–10 | 9–23 | 16–40 | 22.5 → 23 |
| Pond (block, cells) | 2×2 (4 of 100) | 3×3 (9 of 225) | 4×4 (16 of 400) | exact 4 % |
| Pond candidates (1-based top-left) | [2,2] [2,8] [8,2] [8,8] | [2,2] [2,12] [12,2] [12,12] | [2,2] [2,16] [16,2] [16,16] | — |
| Smell per pond cell (food channel) | 1/4 | 1/9 | 1/16 | — |
| Spawn / patrol areas | whole map | whole map | whole map | — |

Not scaled: the water clock (drain 0.625 per step: 160 steps from the comfortable level to death
by thirst), food bites (12), body dynamics, every sensor, the episode cap (500 steps, §6.4), and
the observation (59 numbers in every world: smell, sight and touch sample a fixed diamond around
the agent, so the map size never enters the observation).

### 3.3 Smell reach values (D5, D6)

The smell kernel (`src/environment/sensor.py`, `sense_resource`) adds `1/distance` from every
source whose **Euclidean** distance to the sampled cell is at most `sensor_radius`; the agent
samples its own cell and its four neighbours.

| Map | Largest distance (Euclidean / Manhattan) | Whole-map value | Why |
|---|---|---|---|
| 10×10 | 12.7 / 18 | **20** (inherited from level 05/06) | already above both |
| 15×15 | 19.8 / 28 | **30** | 2 × side, the same rule as level 05's 20; ≥ Manhattan 28 as D6 asks |
| 20×20 | 26.9 / 38 | **40** | 2 × side; ≥ Manhattan 38 |

Because the kernel is Euclidean, the cut-off can never bind at these values; any value above the
Euclidean maximum gives an identical world, so "whole map" is exact. The short reaches 5 and 3
use the same semantics as the context-exploration worlds' "smell range 5 / 3". A source up to
reach + 1 squares away can register on the nearest neighbour sample.

**Short reach cuts every smell, not only food and pond (Revision 1, M6).** One `sensor_radius`
feeds the resource, animal, obstacle and water kernels alike (`sensor.py:37-51`). At reach 5 or 3
the agent also loses the odour of predators (`[0, 0.7, 0.5, 0, 0]`), rabbits (`[0, 0.5, 0.7, 0,
0]`) and bushes (channel 3) beyond that distance. Sight (a 13-cell diamond, radius 2) is
unchanged. So a short-reach world is harder in two ways: finding food and water, and getting early
warning of predators (and of the bushes that are refuges from them). §5.2 predicts both.

### 3.4 Agents and fixed factors

- Agents: `configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml`
  (ordinary) and `.../nmngaenorm_t16quad_ALL.yaml` (modulated). Identical except the modulator;
  both GAE-normalised returns, γ = 0.95; both checked on level 06 in the pilot (width 59).
- Training config: `configs/train/recurrent_ppo.yaml` as committed — 128 parallel worlds, seed 42,
  checkpoint every 200,000 episodes, every checkpoint kept (50 per full run).
- Launch flags: `--episodes 10000000 --log-interval 10`; no `--seed`, `--num-envs` or
  `--checkpoint-frequency` (config-owned).
- Perceptual noise: off (level 06 inherits level 05's noise-off setting; noise is level 07).
- Code: **frozen** at one pinned launch commit, run from a separate detached worktree
  `.claude/worktrees/thirst-runs` that nobody edits (Revision 1, §9.3). Every run, relaunch and
  follow-up seed uses it.

### 3.5 Confounds and limits

| Confound | Effect | Handling |
|---|---|---|
| One seed per condition | Single-run differences under ~6 % are noise | §5.4: leads get two more seeds; nothing is claimed from one run |
| Episode budget, not step budget | Worlds with shorter episodes get less experience; within a world the longer-surviving agent gets more PPO updates per episode (pilot: 25–31 % less experience at equal episodes) | Equal-environment-steps read-out pre-registered beside every episode-matched one (§5, M5); plateau rule (§4) |
| Early stop at different points per world | Final values come from different budgets | Both agents of a world stop together (§4); a common 4 M read-out is also reported |
| Short reach changes the information, not the density | It is the intended manipulation; it removes predator, rabbit and bush odour as well as food and pond odour (§3.3) | Death causes read three ways: thirst, starvation, injury (§5.2) |
| The pond's near-field smell weakens with size (the per-cell weight is 1/(h·w); config review L1) | "One food item" holds far away only. On the pond the field is 1.18 / 0.84 / 0.65 (2×2 / 3×3 / 4×4) against 2.0 on a food item; one step off its edge 0.66 / 0.53 / 0.43 against 1.0 | Decided design (D3); stated so a size effect on drinking is not read as a learning difference alone |
| Regrown food lands on a fire (≈ 2 %) or a bush (≈ 7 %) (PLACEMENT_FIXES_PLAN, measured on 10×10 levels 05/06) | Some regrown food is unreachable alive or sits in a refuge; same for both agents of a world | Known, accepted for the series (the code is frozen without the fix, §9.3) |
| Larger maps also have more predators in absolute number | Intended (density held) | Death-cause shares reported per world |
| Pond start effect: random start hydration [0, 200) kills some episodes early whatever the agent does | Same in every world, but walks to the pond are longer on big maps, so the early-thirst floor rises with size (§6.4) | Report survival by start-hydration band (as the pilot did) |
| The (0,0) placement fallback (Known Bugs ~#117) cannot be proved unreachable at 15×15 and 20×20 (fires) | A world could silently differ from its YAML | Measured 0 / 2,000 resets (§6.2). **Accepted, unmonitored risk** in training (nothing logs it); post-hoc check on the stored evaluation episodes (§5.5) |

## 4. Training budget and early-stopping rule (D7; Revision 1, M1 and M2)

Every run is launched for **10,000,000 episodes**. The trainer has no built-in early stop. A
graceful stop is one `SIGINT` to the training process: it finishes the current iteration and exits
(`train.py:136-145`, `:464-465`, break at `:1661`) **without** writing an extra checkpoint. A second
`SIGINT` force-quits, so the signal is sent **once**. Every checkpoint is kept
(`max_checkpoints_to_keep: null`), so the model at any earlier boundary stays available.

**Quantity.** `S(b)` = mean `Episode/Steps` (survival steps of the training policy, weighted by
`Episode/_window_n`, from the episode rows logged every 4,000 episodes) over the 1-million-episode
block that ends at boundary b. `D(b)` = the thirst-death share (`Episode/Term_Dehydration`, same
weighting) over that block. Rewards are never read.

**Rule, evaluated at every 1 M-episode boundary from 4 M on (4 M, 5 M, …), on data up to that
boundary only:**

1. *Plateau, per run:* the last two block-to-block changes are both **rises of at least 0 and
   under 1 %**: `0 ≤ S(b)/S(b−1) − 1 < 0.01` and `0 ≤ S(b−1)/S(b−2) − 1 < 0.01`. A falling curve
   is not a plateau. **Two consecutive falls** are a flag to the user, not a stop.
2. *Has learned, per run:* `S(b) ≥ 1.5 × S(1 M)` **and** `D(b) < 0.10`. Survival alone is not
   enough: a run that has learned to eat but not yet to drink can sit flat at a respectable level.
   A run that never satisfies rule 2 runs to 10 M and is flagged.
3. *Joint stop, per world:* the **stop boundary b\*** of a world is the first boundary at which
   **both** of its runs (ordinary and modulated) satisfy rules 1 and 2. Worlds stop independently.
4. A run with NaN, a value explosion or a crash is not "stopped"; it is a failed run (§7).

**What b\* fixes, whenever the signal actually lands.** The final model of each run is the
checkpoint nearest b\* (checkpoint keys are the actual episode count at save time, e.g.
`4000123`). `S_final` and every Δ use episodes **(b\*−1 M, b\*]** for both runs. Anything a run
trains after b\* is ignored. Both agents of a world are therefore always compared on the same
episode window, even though the ordinary agent runs about 20–25 % faster (§8) and will be past b\*
when the rule can first be evaluated (it needs the modulated run's data up to b\*).

**Who checks, how often, how the stop is sent.**
- **Checker:** this design session ("Dev: thirst"), polling WandB **at least hourly** for the
  whole series (a `/wake` loop). It applies rules 1–3 to the latest complete boundary of every
  world and writes each decision (world, b\*, both runs' `S` and `D` for the last three blocks) as a
  dated line in §10 before stopping anything.
- **Stop:** at the first check after the rule fires for a world, **both** of its runs get one
  `SIGINT`, sent from the main `thirst` worktree with the project's terminator, one call per run:

  ```bash
  ./terminate_command.py <NODE> "wandb-name <TAG>" --yes
  ```

  `<NODE>` and `<TAG>` from the manifest row (§9). The pattern is the full, unique tag after
  `wandb-name` (no leading dashes, which `pkill` would read as an option); `--yes` skips the
  prompt; no `--force` (that would send SIGTERM). The checker confirms afterwards that the log
  ends with the trainer's normal shutdown and that no `train.py` process with that tag remains.
- **Trailing run.** The modulated run may receive the stop before it has reached the ordinary
  run's episode count, or the ordinary run may be well past b\*. That is expected. The manifest
  records, per run, the episode count and environment-step count **at b\*** and **at the actual
  stop**; only the b\* values enter the analysis.

**Calibration of the 1 % line.** The ordinary agent on level 05 over 10 M episodes rose
233 → 241 → 243 → 246 → 247 → 247 → 250 steps from 2 M to 9 M (about 1 % per 1 M from 4 M to
7 M, 0–1 % after). The rule would stop such a run at about 6–8 M with roughly 2 % of survival
still to come; that is accepted. It is a plateau test, not a convergence proof.

Expected saving: about 20–40 % of the GPU-hours in §8, not counted there.

## 5. Hypotheses and pre-registered read-outs

**Primary dependent variable:** survival steps per episode, training policy, over episodes
(b\*−1 M, b\*] (`S_final`, §4), per run. **Two read-outs of every comparison are pre-registered
(Revision 1, M5):**

- **Episode-matched** (primary for the trigger rule): `S_final` as above.
- **Environment-steps-matched** (required beside every episode-matched number): the trainer logs
  cumulative environment steps (`timesteps`) on the episode rows. For a pair of runs, `E*` = the
  smaller of their two step counts at b\*; each run is read over the episodes logged while its
  `timesteps` lies in (0.9 E\*, E\*]. For the size and reach costs (§5.2), `E*` is the smallest
  step count at b\* among the ordinary runs being compared. Equal steps also means an equal number
  of PPO updates (every iteration is 128 worlds × 128 steps).

Secondary: survival at the common 4 M-episode read-out; death-cause shares (`Episode/Term_*`, all
seven); step-limit share; environment steps used; and, from stored greedy episodes (§5.5),
drinking rate and survival by start-hydration band. **Temporal evolution is mandatory**: every
read-out is also shown per 1 M block over the whole run.

### 5.1 Learnability (every world, both agents)

*Pass:* (a) the thirst-death share (`Term_Dehydration`) in the final block is at most half of its
own peak 1 M-block value (peak-referenced, as the pilot recommended, not first-block-referenced);
(b) no single cause of death above 0.60 of deaths in the final block; (c) over-drinking share
below 0.10. *Prediction:* all nine worlds pass for the ordinary agent. A failure is a finding about
that world (too hard at this budget), not about the modulator. A borderline world is reported to
the user; it gets no automatic extra seeds.

### 5.2 Cost of size and reach (ordinary agent; descriptive only)

**This single-seed series cannot test these expectations; it can only describe the pattern.**
A difference between two size or reach costs is a difference of differences, with a seed noise of
about 2 × 2.6 ≈ 5 % at 10×10 (§5.4), so no outcome here is "supported" or "refuted". Each
expectation below is read as *consistent* or *not consistent* with the pattern, and any pattern
that matters is at most a **candidate for follow-up** (more seeds under a new addendum).

*Expectations, written before training:*
- **Size:** `S_final` falls with map size; 20×20 whole-map at about 0.80–0.95 of 10×10 whole-map
  (C4, without water, reached 0.88 of its 10×10 reference at 5 M).
- **Reach at 10×10:** small cost; reach 5 and 3 within about 10 % of whole-map (context-exploration
  C2 / C6: 1.00 and 0.99 of the reference, with richer food).
- **Reach at larger sizes, by cause of death (Revision 1, M6: three-way, not two-way):**
  - *Thirst:* the reach cost grows with size and shows up mainly as thirst deaths. Measured before
    training (§6.3): some food or pond smell stays in range from about the same share of the map
    at every size (≈ 70 % at reach 3), but the pond's own coverage at reach 3 falls from 37 %
    (10×10) to 14 % (20×20).
  - *Injury:* short reach also removes predator odour beyond 5 or 3 squares (§3.3), so the injury
    share of deaths is expected **higher at reach 3 and 5 than at whole-map, at every size**, by
    a similar amount at each size (predator density is held).
  - *Starvation:* little change with reach (food-or-pond smell coverage is similar across sizes).

### 5.3 Modulated minus ordinary (the screen)

`Δ(world) = S_final(modulated) / S_final(ordinary) − 1`, episode-matched at b\*; `Δ_E(world)`, the
same ratio steps-matched (§5).

- **Lead:** `|Δ| ≥ 6 %` in a world, **in either direction** (modulator ahead or behind). Every lead
  triggers the follow-up of §5.4. If `Δ_E` has the opposite sign or is under 3 % in magnitude, the
  lead is labelled **experience-sensitive** (it may come from more updates rather than a better
  policy); it is still followed up.
- **Exploratory pattern** (Δ larger in harder worlds: bigger map, shorter reach). Read only
  descriptively: the leads are *consistent* with it if every lead is in a harder world (15×15 or
  20×20, or reach 5 or 3) and the 10×10 whole-map Δ is under 6 % in magnitude; *not consistent*
  if a lead appears at 10×10 whole-map, or the Δs show no ordering with difficulty. **If there are
  no leads, the pattern is not assessed** (absence of leads is not evidence for it). With one seed
  it is never "supported": 8 of the 9 worlds count as harder, so one noise lead would satisfy it
  about one time in three. At most it marks worlds as candidates for follow-up.
- **Null screen:** no world reaches 6 %. That says "no effect large enough to see with one seed",
  **not** "no effect".

### 5.4 What one seed can and cannot show (D9; Revision 1, M3 and M4)

**The noise figure and its limits.** The pilot's three seeds per agent gave a survival spread
(s.d.) of about 2.6 %. That figure was measured **at 10×10 only**, on the older pond smell, at 2 M
episodes, from 3 seeds (with 2 degrees of freedom its 95 % range is roughly 1.4–16 %). Whether the
15×15 and 20×20 worlds are as quiet is unknown until the follow-up seeds run there. With
σ = 2.6 %, the difference between two single runs has a spread of about √2 × 2.6 ≈ 3.7 %, so:

- **Below about 6 %** (1.6 spreads) a difference is not interpretable.
- **6–7 %** is a lead, not a finding; the conventional 95 % line for a two-run difference is
  about 7.2 %. In the pilot's own world one seed pair already differed by +7.3 %.
- **Expect false leads.** At σ = 2.6 %, a world with no true effect gives `|Δ| ≥ 6 %` about 10 %
  of the time; across 9 worlds, the chance of at least one false lead is about 60 %, and about
  one is expected. The follow-up exists to sort these out.
- **Larger effects** (≥ 10 %), learnability failures and death-cause shifts are readable from one
  run **at 10×10**; at 15×15 and 20×20 only if the follow-up seeds show a spread no larger than
  10×10's.
- One seed **cannot** support any modulator claim, any interaction claim, any size × reach claim,
  or any "no difference" claim.

**Follow-up, pre-registered now.**
- *Trigger:* every lead (§5.3, `|Δ| ≥ 6 %`, either sign) triggers **seeds 43 and 44 for both
  agents** in that world: 4 new runs, from scratch, at the same pinned code (§9.3), same configs,
  same budget and stop rule (joint stop per seed pair), `--seed 43` / `--seed 44`, tags
  `rppo_thirst_<cell>_<agent>_s43` / `_s44`, group `thirst_task`, job type `followup`.
- *Decision rule on 3 seeds:* the lead is **confirmed** when (i) `Δ` for seed 43 and for seed 44
  both have the lead's sign, **and** (ii) the mean `Δ` over seeds 42, 43 and 44 is at least 6 % in
  magnitude, in the lead's direction. Otherwise it is **not confirmed**. The same rule is applied
  to `Δ_E` and reported; a lead confirmed on `Δ` but not on `Δ_E` is reported as such.
- *Seed 42 and selection:* seed 42 stays in the three-seed analysis, but it was the run that
  **selected** the world, so it overstates the effect (winner's curse). Condition (i) depends only
  on the two unselected seeds, and the **mean of seeds 43 and 44 alone** is reported beside the
  three-seed mean as the effect-size estimate. A confirmed lead is three-seed evidence in one world;
  any wider modulator claim goes to the user and the PI first.
- *Compute cap:* follow-ups may use at most **300 GPU-hours** (RTX 3090 basis, at the full 10 M
  budget; §8 rates: about 61 GPU-h for a 10×10 world, 82 for 15×15, 127 for 20×20). Leads are
  taken in order of `|Δ|`, largest first, while the next world still fits under the cap. Any
  follow-up beyond the cap needs the user's decision.
- The pilot's 10×10 runs with seeds 42–44 used the older pond smell and stopped at 2 M episodes,
  so they are not reusable as extra seeds.

### 5.5 Stored-episode analysis (Revision 1, M7; modelled on THIRST_PILOT §4.2)

Drinking and start hydration are **not** in the training log (no `Episode/*` or `Bal_*` key
records them), so they come from stored greedy-policy episodes.

- **Collector:** `scripts/eval/traj_collect/collect_trajectories.py` **in the frozen
  `thirst-runs` worktree**, run from there, on CPU. Per run, three checkpoints: the one nearest
  2 M, the one nearest 4 M (the common read-out), and the one nearest b\* (final). Checkpoint keys
  are actual episode counts, so list `models/` and pass the nearest key. `--episodes 10000`,
  `--obs-precision float32`, `--seed-base 1000000` for every run, `--run` = the shared-folder run
  directory, out-root `<shared>/results/analysis/thirst_task/`. Measure the first store's size
  before running the other 53 (18 runs × 3).
- **Computed per store** (as the pilot): start hydration (200 × the Hydration column at t = 0);
  drinking steps (hydration rises; only the pond raises it), bouts per episode and steps per bout;
  the no-drink deadline (1.6 × start hydration); cause of death, all seven codes, shares summing to
  1; **survival by start-hydration band** (0–50, 50–100, 100–150, 150–200); and the walk from the
  start cell to the pond.
- **Pond recomputation and its integrity checks** (pilot R1): reset the environment from each
  episode's `episode_seed` with the collector's key recipe, building parameters from the run's own
  saved `models/config.yaml` through `apply_sensor_compat`, never from a worktree YAML. Check over
  every episode that the recomputed start cell matches the store, and over every step that
  "hydration rose" holds exactly when the agent stands on a recomputed pond cell. Any exception:
  the pond-dependent numbers are not reported.
- **Post-hoc (0,0) check** (config review O1): from the same recomputed resets, count episodes in
  which an active campfire sits at (0,0) (outside its inset area) or any active entity lies
  outside its spawn area. Expected 0. A non-zero count is reported with its rate; it does not
  invalidate a run (§7).
- Greedy-store numbers and training-log numbers are reported side by side and **never pooled**.
- **Must not be used** (they drop death codes 6 and 7): `scripts/analysis/ladder/lad03_how_it_ends.py`,
  `scripts/analysis/studies/context_exploration/part4_readout.py`,
  `scripts/analysis/studies/level05_body_interactions/pilot_pick.py`; and no `v4.0` tool from the
  shared folder may read these runs. Shared-folder batch tools that glob
  `results/JAX_RecurrentPPO/` should exclude `*rppo_thirst_*` until `v5.0` is merged.
- A reader placed under `scripts/` updates `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` in the same
  commit, and starts with a known-input test (a synthetic hydration trace with 2 bouts returns 2).
  It is written in the main `thirst` worktree, never in `thirst-runs`.

## 6. Checks run before commit (2026-10-01)

All checks use the trainer's own loader (`load_env_config` → `load_env_params`), the real
`jax_reset`, and the real smell kernel, on the `v5.0` worktree **after** the Revision-2 commit.
Scripts and raw output are committed next to this doc, in `checks/` (Revision 1, L2):
`validate_worlds.py`, `validate_all.json`, `validate_all_stdout.txt`, `tables.py` / `tables.md`
(every table below is generated, not typed), `pond_reach.py`, `walltime.py`, `wandb_speed.py`,
`wandb_cap.py`, `wandb_tags.py`, `make_smell_variants.py`, `layout_<cell>.png`. The scripts were run
from `tmp/20261001_thirst_task/` in the worktree and still write there.

**Precondition met.** The Revision-2 implementation commit `c33d29b1` ("the pond smells only of
food") is on `v5.0`, and the committed `default.yaml` reads `water.properties: [1.0, 0.0, 0.0,
0.0, 0.0]`. Every check below ran after it.

**Summary.**

| Check | Result |
|---|---|
| 1. Loads through the trainer's loader | **PASS**, all 9. Width 59 everywhere (breakdown sum = a real `get_observation` on a real reset); every breakdown modality has a noise entry (noise is off in all 9) |
| 2. Placement, 2,000 resets per world | **PASS**, all 9. Zero fallback cases, zero overlaps, zero entities outside their areas, nothing on the pond, agent never starts on the pond, fires always ≥ 4 apart |
| 3. Smell direction (whole map) | **No flat-smell problem.** Strongest neighbour points at the nearest source 86–98 % of the time at every distance and size (chance 42–68 %). Lowest: 20×20 at distance 5, 86 % |
| 3b. Short reach | Any food-or-pond smell in range from ≈ 90 % (reach 5) and ≈ 70 % (reach 3) of the map at every size; the **pond alone** from 64 / 35 / 23 % (reach 5) and 37 / 21 / 14 % (reach 3) at 10 / 15 / 20 |
| 4. Episode cap | **500 stays** (§6.4) |
| 5. Compute | 406 GPU-h on 3090s, 554 on 2080 Tis, full 10 M (§8) |
| 6. Sample maps | `checks/layout_<cell>.png`, one per world |

### 6.1 Load (check 1)

| Cell | Grid | sensor_radius | Pond | Smell per pond cell (ch. 0) | Whole pond (ch. 0) | Obs width (breakdown / real `get_observation`) | Breakdown modalities missing from noise | Noise on |
|---|---|---|---|---|---|---|---|---|
| g10sW | 10x10 | 20 | 2×2 | 0.2500 | 1.0000 | 59 / 59 | none | False |
| g10s5 | 10x10 | 5 | 2×2 | 0.2500 | 1.0000 | 59 / 59 | none | False |
| g10s3 | 10x10 | 3 | 2×2 | 0.2500 | 1.0000 | 59 / 59 | none | False |
| g15sW | 15x15 | 30 | 3×3 | 0.1111 | 1.0000 | 59 / 59 | none | False |
| g15s5 | 15x15 | 5 | 3×3 | 0.1111 | 1.0000 | 59 / 59 | none | False |
| g15s3 | 15x15 | 3 | 3×3 | 0.1111 | 1.0000 | 59 / 59 | none | False |
| g20sW | 20x20 | 40 | 4×4 | 0.0625 | 1.0000 | 59 / 59 | none | False |
| g20s5 | 20x20 | 5 | 4×4 | 0.0625 | 1.0000 | 59 / 59 | none | False |
| g20s3 | 20x20 | 3 | 4×4 | 0.0625 | 1.0000 | 59 / 59 | none | False |

Breakdown: Satiation 1, Body Temperature 1, Hydration 1, Interoceptive Nociception 1, Extero
Nociception 1, Thermoception 5, Olfaction 25, Collision 5, Proprioception 6, Visual 13 = 59.
**Breakdown ↔ noise sync:** every breakdown modality is named in `noise_modality_order`. That
tuple lists Hydration last (appended by design, THIRST_WATER_PLAN), not in breakdown position;
this is harmless because `apply_perceptual_noise` looks modalities up by name
(`sensor.py:440`). The per-cell smell weight is read from the loaded `EnvParams`
(`water_cell_property`) and its whole-pond sum is exactly 1.0 at every size (D3). On the 2,000
resets of §6.2, every pond's top-left cell is one of the four candidates (the four frequencies
sum to 1).

### 6.2 Placement and the silent (0,0) fallback (check 2)

| Cell | Active entity outside its own area (fallback signature) | Active entities at (0,0) per reset: observed / uniform expectation / other corners | Two active entities on one cell | Active entity on the pond | Agent starts on the pond | Fire pairs closer than 4 | Agent starts on a burning fire | Pond corner frequencies | Mean active: food / ambushers / fires / animals |
|---|---|---|---|---|---|---|---|---|---|
| g10sW | 0.00 % | 0.295 / 0.274 / 0.291 | 0.00 % | 0.00 % | 0.00 % | 0.00 % | 1.85 % | 0.249 / 0.248 / 0.256 / 0.247 | 2.4 / 6.9 / 2.0 / 2.0 |
| g10s5 | 0.00 % | 0.295 / 0.274 / 0.291 | 0.00 % | 0.00 % | 0.00 % | 0.00 % | 1.85 % | 0.249 / 0.248 / 0.256 / 0.247 | 2.4 / 6.9 / 2.0 / 2.0 |
| g10s3 | 0.00 % | 0.295 / 0.274 / 0.291 | 0.00 % | 0.00 % | 0.00 % | 0.00 % | 1.85 % | 0.249 / 0.248 / 0.256 / 0.247 | 2.4 / 6.9 / 2.0 / 2.0 |
| g15sW | 0.00 % | 0.299 / 0.279 / 0.307 | 0.00 % | 0.00 % | 0.00 % | 0.00 % | 2.15 % | 0.249 / 0.248 / 0.256 / 0.247 | 5.4 / 15.9 / 4.5 / 5.1 |
| g15s5 | 0.00 % | 0.299 / 0.279 / 0.307 | 0.00 % | 0.00 % | 0.00 % | 0.00 % | 2.15 % | 0.249 / 0.248 / 0.256 / 0.247 | 5.4 / 15.9 / 4.5 / 5.1 |
| g15s3 | 0.00 % | 0.299 / 0.279 / 0.307 | 0.00 % | 0.00 % | 0.00 % | 0.00 % | 2.15 % | 0.249 / 0.248 / 0.256 / 0.247 | 5.4 / 15.9 / 4.5 / 5.1 |
| g20sW | 0.00 % | 0.314 / 0.273 / 0.299 | 0.00 % | 0.00 % | 0.00 % | 0.00 % | 2.30 % | 0.249 / 0.248 / 0.256 / 0.247 | 10.1 / 27.6 / 8.0 / 7.9 |
| g20s5 | 0.00 % | 0.314 / 0.273 / 0.299 | 0.00 % | 0.00 % | 0.00 % | 0.00 % | 2.30 % | 0.249 / 0.248 / 0.256 / 0.247 | 10.1 / 27.6 / 8.0 / 7.9 |
| g20s3 | 0.00 % | 0.314 / 0.273 / 0.299 | 0.00 % | 0.00 % | 0.00 % | 0.00 % | 2.30 % | 0.249 / 0.248 / 0.256 / 0.247 | 10.1 / 27.6 / 8.0 / 7.9 |

How to read it. `jax_reset` places every allocated slot (the `count_high` of each entry), then
parks the unused ones **off the grid** at (row H, column W); all checks are on the active ones
(verified: every inactive slot sits at the park cell). The fallback (Known Bugs ~#117) writes an
entity that finds no free cell to cell (0,0). For the campfires, whose area is inset by 2 squares,
(0,0) is outside their area, so a fallback shows up in column 2. For every other entity the area
is the whole map and (0,0) is a legal cell, so the only trace a fallback could leave is **extra
occupancy of (0,0)**; column 3 compares it with the uniform expectation and with the mean of the
other three corners, which every placement rule treats the same way except the fallback. They
agree (largest gap 0.015 entities per reset, within sampling noise for 2,000 resets).

**Fallback rate, stated plainly:** 0 of 2,000 resets in every world. With 0 events in 2,000 the
95 % upper bound is about 0.15 % of resets. For the 10×10 worlds the placement plan's
feasibility analysis already proved the fallback unreachable (it covers every maintained world,
level 06 included, and the 10×10 reach variants place exactly as level 06). The 15×15 and 20×20
worlds **cannot be proved**: up to 7 (or 12) campfires that must sit 4 squares apart in an
11×11 (or 16×16) box can, in principle, be packed so a later fire has no legal cell — the same
reason the context-exploration 15×15/20×20 worlds were unprovable. Measured, it does not happen
here. If [[PLACEMENT_FIXES_PLAN]] lands before launch, these two sizes will load with its warning
and its counted-drop backstop rather than the silent fallback; the design does not depend on it.

**Already-known, not new:** the agent starts on a burning campfire in 1.85 % (10×10), 2.15 %
(15×15) and 2.30 % (20×20) of resets — the issue [[PLACEMENT_FIXES_PLAN]] is fixing (it reported
1.85 % for level 06). The pond corners are drawn uniformly (0.247–0.256 each).

### 6.3 Does the food-channel smell still point somewhere useful? (check 3)

The concern: with smell carrying across the whole map and up to 16 food items plus the pond, the
summed `1/distance` field could become flat, or pulled toward clusters, so the local gradient no
longer leads to anything nearby. **Method:** on the same 2,000 real reset layouts per world, the
channel-0 field (food + pond) was computed at every cell with the environment's own kernel
(`sensor._sense_olfaction_at`, noise-free). Every cell that is not itself a source was then
treated as an agent position. The agent's four neighbour samples were compared (out-of-grid
neighbours read zero, as in the sensor); the question is whether the **strongest** neighbour is
one step closer (Manhattan) to the **nearest** source, food or pond (ties split evenly). "Chance"
is what a random in-bounds neighbour would score. "In range" = any of the five samples is
non-zero. Rows are binned by the distance to the nearest source.

| Cell | Any channel-0 smell in range (random cell) | d=2: points to nearest / chance / in range (cells) | d=5 | d=10 | d=15 |
|---|---|---|---|---|---|
| g10sW | 100.00 % | 98.1 % / 46.4 % / 100.0 % (n=36,548) | 95.7 % / 53.5 % / 100.0 % (n=20,855) | 100.0 % / 67.5 % / 100.0 % (n=1,354) | — (no cell at this distance) |
| g10s5 | 92.02 % | 95.4 % / 46.4 % / 100.0 % (n=36,548) | 92.4 % / 53.5 % / 100.0 % (n=20,855) | 0.0 % / 67.5 % / 0.0 % (n=1,354) | — (no cell at this distance) |
| g10s3 | 73.31 % | 95.0 % / 46.4 % / 100.0 % (n=36,548) | 36.0 % / 53.5 % / 36.0 % (n=20,855) | 0.0 % / 67.5 % / 0.0 % (n=1,354) | — (no cell at this distance) |
| g15sW | 100.00 % | 95.9 % / 43.2 % / 100.0 % (n=73,615) | 89.3 % / 52.6 % / 100.0 % (n=48,489) | 96.1 % / 55.4 % / 100.0 % (n=7,502) | 100.0 % / 67.0 % / 100.0 % (n=360) |
| g15s5 | 88.61 % | 93.7 % / 43.2 % / 100.0 % (n=73,615) | 89.6 % / 52.6 % / 100.0 % (n=48,489) | 0.0 % / 55.4 % / 0.0 % (n=7,502) | 0.0 % / 67.0 % / 0.0 % (n=360) |
| g15s3 | 69.15 % | 92.8 % / 43.2 % / 100.0 % (n=73,615) | 40.8 % / 52.6 % / 40.8 % (n=48,489) | 0.0 % / 55.4 % / 0.0 % (n=7,502) | 0.0 % / 67.0 % / 0.0 % (n=360) |
| g20sW | 100.00 % | 94.6 % / 42.1 % / 100.0 % (n=129,497) | 86.3 % / 52.2 % / 100.0 % (n=89,538) | 92.4 % / 57.3 % / 100.0 % (n=11,112) | 96.0 % / 59.0 % / 100.0 % (n=1,154) |
| g20s5 | 89.67 % | 93.7 % / 42.1 % / 100.0 % (n=129,497) | 88.8 % / 52.2 % / 100.0 % (n=89,538) | 0.0 % / 57.3 % / 0.0 % (n=11,112) | 0.0 % / 59.0 % / 0.0 % (n=1,154) |
| g20s3 | 69.40 % | 92.1 % / 42.1 % / 100.0 % (n=129,497) | 42.3 % / 52.2 % / 42.3 % (n=89,538) | 0.0 % / 57.3 % / 0.0 % (n=11,112) | 0.0 % / 59.0 % / 0.0 % (n=1,154) |

**Verdict: the whole-map smell does not go flat; no stop.** On 20×20 the strongest neighbour
leads toward the nearest source 94.6 / 86.3 / 92.4 / 96.0 % of the time at distances 2 / 5 / 10
/ 15, against 42–59 % by chance. The mild dip at distance 5 on the bigger maps is most likely
cells whose nearest source is a lone item while a cluster further off pulls harder (not
separately measured); the gradient then leads toward *a* source, just not the nearest. Cells 10
or more squares from any source are rare (about 1 % of 20×20 cells) and sit in sparse corners.

**Short reach.** When anything is in range, direction is as good as whole-map (reach 5 at
d = 5: 89–92 %); out of range the reading is zero, so the agent gets no direction at all (d = 10
and 15 at reach 5; d ≥ 5 mostly at reach 3). Because density is held, the share of the map with
*some* food-or-pond smell is about the same at every size: ≈ 90 % at reach 5 and ≈ 70 % at
reach 3. **What shrinks with size is the pond's own coverage** (its fixed 4 % is one block, and
its distance from the agent grows with the side). Share of non-pond cells from which the pond
alone is smellable (any of the five samples within reach; `pond_reach.py`, the four corners
averaged):

| Reach | 10×10 | 15×15 | 20×20 |
|---|---|---|---|
| 5 | 63.5 % | 34.7 % | 23.2 % |
| 3 | 36.5 % | 20.8 % | 14.3 % |

So at reach 3 on 20×20 the agent can smell the pond from one cell in seven; elsewhere it must
remember where the pond is (and smell cannot say pond rather than food anyway, D1).

Also visible in the sample maps: on a whole-map 20×20 field the pond (16 cells at 1/16 each) is a
faint, broad plateau next to the peaks of food clusters. That is the decided "one food item"
weight spread over a larger block, not a defect.

### 6.4 Episode cap: 500 steps stays (check 4)

Walk from the start cell to the nearest pond cell (Manhattan steps, 2,000 resets):

| Map | Mean | Median | 95th pct | Max |
|---|---|---|---|---|
| 10×10 | 6.1 | 6 | 12 | 14 |
| 15×15 | 9.3 | 9 | 19 | 22 |
| 20×20 | 12.7 | 12 | 25 | 30 |

**Decision: keep 500, unchanged at every size.** Reasons:
1. *The thirst clock does not need a longer cap.* From the comfortable level, death by thirst
   takes 160 steps; even the longest walk to the pond on 20×20 (30 steps, 95th percentile 25)
   uses under a fifth of it, and a refill from 50 to 100 takes 10 steps. A 500-step episode
   already needs two to three pond visits, so thirst stays a live constraint at every size.
2. *The cap is not a ceiling problem.* On level 05 after 10 M episodes, 32 % of episodes reach
   the cap (0.28 at 2 M → 0.32 at 10 M, WandB, `wandb_cap.py`); the level-06 pilot was at 0.23 at
   2 M. Two-thirds of episodes end in a death that the comparison can read. §7 flags any world
   where the share passes 0.5.
3. *Comparability.* The same cap at every size keeps survival numbers comparable across sizes,
   with level 06, with the pilot and with the rest of the ladder (`eval_max_steps` is also 500).
4. *Longer walks are small next to the cap.* The 20×20 walk is about 7 steps longer on average
   than the 10×10 one, against a 500-step cap and a 160-step thirst clock.

The cost of the cap grows with size in one place: the agents that start with almost no water.
With start hydration below 50 (deadline under 80 steps) a 20×20 agent may need 25–30 of those
steps just to walk. The analysis reports survival by start-hydration band (as the pilot did) so
this floor is visible and not mistaken for a learning difference.

### 6.5 Compute (check 5)

See §8: about 406 GPU-hours on RTX 3090s or 554 on RTX 2080 Tis for all 18 runs at the full 10 M
episodes, before any early stop.

### 6.6 Sample maps (check 6)

One start layout per world, with its channel-0 smell field beside it:
`checks/layout_<cell>.png` next to this doc (`g10sW` … `g20s3`; regenerate with
`validate_worlds.py`). The three reaches of one size share the same layout (smell
reach does not enter the reset), so the nine images show three maps under three smell fields.

## 7. Failure-mode catalogue (decided in advance)

| Outcome | Reading |
|---|---|
| A run fails a validity check (§9.3: gate, width, pinned commit, saved world settings) | The run is **invalid**, not a result: stopped, never analysed, relaunched from scratch at the same pinned commit after the launch path is fixed. |
| NaN / value explosion / crash in one run | That run failed, not the world. Relaunch once from scratch with the same seed **at the same pinned commit** (§9.3) after `bug-curator` is consulted; a second failure in the same world is reported as a world-specific instability. |
| A world fails learnability (§5.1) for the ordinary agent | A finding about the world at this budget. Its Δ is not read. |
| Run still rising at 10 M (rule 1 never fired) | Report as "not plateaued"; Δ read at 10 M with that label. |
| Rule 2 blocks a stop (never learned: survival under 1.5 × its first block, or thirst deaths ≥ 0.10) | Run continues to 10 M; flagged; compare with the context-exploration sparse-food runs. |
| Survival falls two blocks in a row (§4 rule 1) | Not a stop. Flag to the user with the per-block causes of death. |
| Step-limit share in the final block above 0.5 in any world | Survival is ceiling-compressed there; Δ in that world is reported with the step-limit shares of both agents and read with caution. |
| (0,0) fallback in training (Known Bugs ~#117) | **Accepted, unmonitored risk** (config review O1). Training cannot detect it: nothing raises or logs it. Measured 0 in 2,000 resets per world (95 % upper bound ≈ 0.15 % of resets), and its likely form is one campfire parked in the corner. Checked **after the fact** on the stored evaluation episodes (§5.5). A non-zero count is reported with its rate and does not invalidate the runs. |
| Modulated agent ahead everywhere by 3–5 % | Consistent with a small effect; below the screen's resolution; seeds decide. |

## 8. Compute (check 5)

Throughput measured in WandB on the same trainer, in environment steps per second:

| Source | Card | Ordinary | Modulated |
|---|---|---|---|
| Level-06 pilot, 10×10 (3 runs each) | RTX 2080 Ti | 30.7–31.3 k | 23.3–23.7 k |
| Level-05 runs, 10×10 (2 M ordinary; 10 M modulated), ×0.953 for water | RTX 3090 | ≈ 41.0 k | ≈ 32.8 k |
| Size factor, ordinary, context-exploration (RTX 4090): 15×15 39.4 k, 20×20 25.5–26.0 k vs 10×10 53.3 k | — | 0.74 / 0.48 | (same factor used; errs long) |

Environment steps per 10 M episodes: 1.8–2.3 billion in the level-05 10 M runs; the level-06
pilot's episodes were shorter early on. Planning value **2.0 billion**, upper **2.3 billion**.

| World size | 2080 Ti ordinary | 2080 Ti modulated | 3090 ordinary | 3090 modulated |
|---|---|---|---|---|
| 10×10 | 17.9 h | 23.7 h | 13.6 h | 16.9 h |
| 15×15 | 24.2 h | 32.1 h | 18.3 h | 22.9 h |
| 20×20 | 37.3 h | 49.5 h | 28.2 h | 35.3 h |

**Total for the 18 runs at the full 10 M episodes:** about **406 GPU-hours on RTX 3090s**
(466 at the upper step count) or **554 on RTX 2080 Tis** (637 upper). The stop rule should save
20–40 %. The longest single run is the 20×20 modulated one, about 1.5 days on a 3090 and 2 days
on a 2080 Ti. The pilot's "about 660 iterations per second early on 10×10" is an episode-rate
figure from the progress bar and is not used here: episode rate changes several-fold as agents
learn to survive, environment-step rate does not.

## 9. Launch Manifest

All 18 rows share wandb-group `thirst_task` and job type `prod`. Tags follow
`rppo_thirst_<cell>_<agent>_s<seed>`; Tag and wandb-name are identical. No WandB run is named
`rppo_thirst_*` and the group `thirst_task` is unused (WandB API query, 2026-10-01). Node, GPU and
the actual columns are filled by `training-runner` at launch; **no nodes are chosen here**.

| Run | Status | Cell | Tag (= wandb-name) | wandb-group | wandb-job-type | Seed | Node | GPU | Launched at | WandB run ID | Log path |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | planned | g10sW ordinary | `rppo_thirst_g10sW_t1none_s42` | thirst_task | prod | 42 | — | — | — | — | — |
| 2 | planned | g10sW modulated | `rppo_thirst_g10sW_t16quad_s42` | thirst_task | prod | 42 | — | — | — | — | — |
| 3 | planned | g10s5 ordinary | `rppo_thirst_g10s5_t1none_s42` | thirst_task | prod | 42 | — | — | — | — | — |
| 4 | planned | g10s5 modulated | `rppo_thirst_g10s5_t16quad_s42` | thirst_task | prod | 42 | — | — | — | — | — |
| 5 | planned | g10s3 ordinary | `rppo_thirst_g10s3_t1none_s42` | thirst_task | prod | 42 | — | — | — | — | — |
| 6 | planned | g10s3 modulated | `rppo_thirst_g10s3_t16quad_s42` | thirst_task | prod | 42 | — | — | — | — | — |
| 7 | planned | g15sW ordinary | `rppo_thirst_g15sW_t1none_s42` | thirst_task | prod | 42 | — | — | — | — | — |
| 8 | planned | g15sW modulated | `rppo_thirst_g15sW_t16quad_s42` | thirst_task | prod | 42 | — | — | — | — | — |
| 9 | planned | g15s5 ordinary | `rppo_thirst_g15s5_t1none_s42` | thirst_task | prod | 42 | — | — | — | — | — |
| 10 | planned | g15s5 modulated | `rppo_thirst_g15s5_t16quad_s42` | thirst_task | prod | 42 | — | — | — | — | — |
| 11 | planned | g15s3 ordinary | `rppo_thirst_g15s3_t1none_s42` | thirst_task | prod | 42 | — | — | — | — | — |
| 12 | planned | g15s3 modulated | `rppo_thirst_g15s3_t16quad_s42` | thirst_task | prod | 42 | — | — | — | — | — |
| 13 | planned | g20sW ordinary | `rppo_thirst_g20sW_t1none_s42` | thirst_task | prod | 42 | — | — | — | — | — |
| 14 | planned | g20sW modulated | `rppo_thirst_g20sW_t16quad_s42` | thirst_task | prod | 42 | — | — | — | — | — |
| 15 | planned | g20s5 ordinary | `rppo_thirst_g20s5_t1none_s42` | thirst_task | prod | 42 | — | — | — | — | — |
| 16 | planned | g20s5 modulated | `rppo_thirst_g20s5_t16quad_s42` | thirst_task | prod | 42 | — | — | — | — | — |
| 17 | planned | g20s3 ordinary | `rppo_thirst_g20s3_t1none_s42` | thirst_task | prod | 42 | — | — | — | — | — |
| 18 | planned | g20s3 modulated | `rppo_thirst_g20s3_t16quad_s42` | thirst_task | prod | 42 | — | — | — | — | — |

**Card guidance (not an assignment).** The 20×20 runs are the long ones; if cards are mixed,
put them on the faster cards. Both agents of a world go on the same card class (§9.3). Pack
node-first (CLAUDE.md, GPU spec).

**At the stop (§4),** the checker adds to each row's Status cell: b\*, and the run's episode and
environment-step counts at b\* and at the actual stop.

### 9.1 Configs

Agent configs: ordinary = `configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml`
(odd runs); modulated = `configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml`
(even runs). Seed flag: none (config-owned 42).

| Runs | Cell | Env config | Extends |
|---|---|---|---|
| 1–2 | g10sW | `configs/environment/experiment/basic/06-pond_thirst_10x10.yaml` (existing level 06) | `basic/05` |
| 3–4 | g10s5 | `configs/environment/experiment/thirst/pond_thirst_10x10_smell5.yaml` | `basic/06` |
| 5–6 | g10s3 | `configs/environment/experiment/thirst/pond_thirst_10x10_smell3.yaml` | `basic/06` |
| 7–8 | g15sW | `configs/environment/experiment/thirst/pond_thirst_15x15.yaml` | `basic/06` |
| 9–10 | g15s5 | `configs/environment/experiment/thirst/pond_thirst_15x15_smell5.yaml` | `thirst/pond_thirst_15x15` |
| 11–12 | g15s3 | `configs/environment/experiment/thirst/pond_thirst_15x15_smell3.yaml` | `thirst/pond_thirst_15x15` |
| 13–14 | g20sW | `configs/environment/experiment/thirst/pond_thirst_20x20.yaml` | `basic/06` |
| 15–16 | g20s5 | `configs/environment/experiment/thirst/pond_thirst_20x20_smell5.yaml` | `thirst/pond_thirst_20x20` |
| 17–18 | g20s3 | `configs/environment/experiment/thirst/pond_thirst_20x20_smell3.yaml` | `thirst/pond_thirst_20x20` |

The short-reach files change one key (`sensory.sensor_radius`). The two whole-map files restate
level 05's `resources` / `entities` / `obstacles` lists (lists merge by replacement), with only
areas and counts changed; `blocks_animals: true` is kept on the bush and the tree keeps count 0.

### 9.2 For the training-runner

The launch path is the pilot's ([[THIRST_PILOT]] §2.5) with one change: the code comes from the
**frozen worktree** `.claude/worktrees/thirst-runs` (§9.3), not from the development worktree.
Every output still goes to the shared folder. The `/tmp` launch script, per row (fill `<GPU>`,
`<ENV_CFG>`, `<AGENT_CFG>`, `<TAG>`, `<TS>` from §9 / §9.1; follow-up seeds add `--seed 43` or
`--seed 44` and use job type `followup`):

```bash
#!/bin/bash
set -euo pipefail
RUNS=/media/nas01/projects/Interoceptive-AI/grid_world_pain/.claude/worktrees/thirst-runs
SHARED=/media/nas01/projects/Interoceptive-AI/grid_world_pain
PY=/home/vncuser/miniconda3/envs/grid_world_pain/bin/python
PIN=PIN_SHA_FULL
export WANDB_DIR="$SHARED"
cd "$RUNS"
# --- frozen-code gate (THIRST_TASK §9.3). CPU-only; never touches the GPU. ---
PIN="$PIN" JAX_PLATFORMS=cpu "$PY" - <<'PYEOF'
import os, sys, subprocess
RUNS = os.path.realpath(os.getcwd())
PIN = os.environ["PIN"]
def fail(msg): sys.exit(f"[thirst-gate] FAIL: {msg}")
if os.path.basename(RUNS) != "thirst-runs": fail(f"cwd is {RUNS}, not the thirst-runs worktree")
def git(*a):
    return subprocess.run(["git", *a], capture_output=True, text=True, cwd=RUNS, timeout=120).stdout.strip()
head = git("rev-parse", "HEAD")
if head != PIN: fail(f"HEAD is {head!r}, pinned commit is {PIN}")
if git("status", "--porcelain", "--untracked-files=no"): fail("thirst-runs has modified tracked files")
sys.argv = ["train.py"]
import src
paths = [os.path.realpath(p) for p in src.__path__]
if paths != [os.path.join(RUNS, "src")]: fail(f"src resolves to {paths}")
import train  # train.py's whole import graph; main() is guarded by __name__ == "__main__"
bad = sorted({os.path.realpath(m.__file__) for m in list(sys.modules.values())
              if getattr(m, "__file__", None) and "/src/" in os.path.realpath(m.__file__)
              and not os.path.realpath(m.__file__).startswith(os.path.join(RUNS, "src") + "/")})
if bad: fail(f"modules loaded from outside thirst-runs/src: {bad[:5]}")
from src.environment.state import EnvParams
if "water_enabled" not in EnvParams.__dataclass_fields__: fail("imported code has no water")
print(f"[thirst-gate] OK src={paths[0]} head={head} train={os.path.realpath(train.__file__)} "
      f"modules={len(sys.modules)}", flush=True)
PYEOF
exec "$PY" train.py \
  --config <ENV_CFG> \
  --agent_config <AGENT_CFG> \
  --episodes 10000000 --device cuda:<GPU> --log-interval 10 \
  --results-dir "$SHARED/results/JAX_RecurrentPPO/<TS>_<TAG>" \
  --tag <TAG> --wandb-name <TAG> \
  --wandb-group thirst_task --wandb-job-type prod
```

As in the pilot, the gate runs in stdin mode (`python -`) so the working directory is first on
`sys.path`; do not save it as a file elsewhere. Launch call, from the main `thirst` worktree, once
per row: `./run_command.py --no-tail --log <shared>/logs/<TS>_<TAG>.log <NODE> "bash $TMP_SCRIPT"`.
The runner appends each row's commented command block to the **main `thirst` worktree's**
`train_command-agent.sh` (never to a file in `thirst-runs`), and records the pinned commit in the
Log-path cell. Early stops are sent as in §4.

### 9.3 Code pinning and run validity (Revision 1, C1)

**The pinned launch commit is `PIN_SHA_SHORT`** on `v5.0` (subject "docs(thirst): 📝 THIRST_TASK
Revision 1 — …"; full SHA `PIN_SHA_FULL`). It contains the Revision-2 smell (`c33d29b1`), the
eight configs and this revision; its `src/`, `train.py` and `scripts/` are those of `c33d29b1`.

1. **One frozen worktree.** The launching session (Admin) creates it once, before the first launch:

   ```bash
   git worktree add --detach .claude/worktrees/thirst-runs PIN_SHA_FULL
   ```

   All 18 runs, every relaunch (§7) and every follow-up seed (§5.4) execute from it. **Nobody edits
   `thirst-runs`**: no commits, no checkouts, no file changes, no `git worktree remove` until the
   **last** run of the series, follow-ups included, has ended and its outputs (results directory,
   WandB folder, log) are confirmed in the shared folder. It is then removed by whoever closes the
   series, after a dry-run check that it holds no run output. Development, the placement fixes
   included, continues in the main `thirst` worktree and never touches `thirst-runs`
   ([[PLACEMENT_FIXES_PLAN]] K0 says the same). Because the 10×10 worlds inherit `basic/05` and
   `basic/06` through `extends:`, freezing the worktree also freezes those ladder files for the
   series (config review M1). If the code must move before a follow-up, that follow-up re-runs
   seed 42 at the new commit as well.
2. **Pre-flight, per launch** (pilot §3.2, adapted), in addition to the runner's usual checks
   (live GPU free-check, diary and `pgrep` for claimants nvidia-smi cannot see):
   - the NAS is mounted on the node, and `<thirst-runs>/train.py` is readable from it;
   - `which git` succeeds on the node (the gate and provenance need it);
   - in `thirst-runs`: `git rev-parse HEAD` prints the pinned commit and
     `git status --porcelain --untracked-files=no` prints nothing;
   - no `<shared>/results/JAX_RecurrentPPO/*_<TAG>` directory exists yet;
   - both agents of a world go on the same card class (the stop rule compares them at equal
     episodes, and a mixed pair widens the episode gap at b\*).
3. **Diary note at the first launch:** one `note` row saying the `rppo_thirst_*` runs execute code
   from `.claude/worktrees/thirst-runs` at the pinned commit, that nobody may edit or remove that
   worktree until the series (follow-ups included) has ended, and that the outputs are in the
   shared folder.
4. **Run validity, per run** (pilot P5, adapted). A run must pass (a), (b), (c) and (e); a run that
   fails any of them is invalid (§7). (d) is informational.
   - (a) The log **contains** `[thirst-gate] OK src=<thirst-runs>/src head=<pinned commit>`.
   - (b) The banner prints `Observation Dim: 59 (… Hydration=1 …)`.
   - (c) `models/provenance.json` shows `git_sha` = the pinned commit. The branch reads `HEAD`
     (detached worktree), which is expected. A `"unknown"` sha (the helper's 10 s git timeout on
     this NAS) falls back to (a).
   - (d) WandB metadata `program` / `root` / `commit`: recorded; the commit should equal (c).
   - (e) The saved `models/config.yaml` shows `water.enabled: true`, **`water.properties: [1.0,
     0.0, 0.0, 0.0, 0.0]`** (the Revision-2 smell; the pilot's runs had the old one), and the
     cell's own `environment.height` / `width`, `water.size` and `sensory.sensor_radius` (§3.1–3.3).
     `Episode/Term_Dehydration` is non-zero in at least one logged window.

   Post-launch, after the usual 3–8 minute wait, the runner checks (a) and (b) in the log, (c) and
   (e) once the run directory is written, and records the WandB run ID in the manifest.

## 10. Results

*(Empty until training. Filled by `experiment-analyzer`.)*

## 11. Conclusions

*(Empty until training.)*

## Links

- Configs: `configs/environment/experiment/thirst/` (8 files) and
  `configs/environment/experiment/basic/06-pond_thirst_10x10.yaml`
- Pilot: `docs/experiments/active/thirst_pilot/THIRST_PILOT.md`
- Water implementation: `docs/develop/active/thirst/THIRST_WATER_PLAN.md`
- Context-exploration study: `docs/experiments/active/context_exploration/STUDY_PLAN.md`
- Placement fallback: `docs/develop/active/placement/PLACEMENT_FIXES_PLAN.md`, Known Bugs ~#117
- Critical-settings change-log entry for these local overrides: `docs/environment/CONFIG_CRITICAL_SETTINGS.md`, 2026-10-01

## Feedback from plan-reviewer

*plan-reviewer, 2026-10-01, on commit `c631d8fa`. Full report: [[plan_thirst_task]]
(`docs/reviews/plan_thirst_task.md`). Appended; the design text above is unchanged.*

Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run · 🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

**Verdict: NOT READY. There is one Critical finding, and the fix is a paragraph of text.** The
configs do what they claim. I resolved all nine worlds through the trainer's loader: within each
size they differ only in `sensory.sensor_radius`, and the larger worlds differ from level 06 only
in size, areas, counts, pond and range. Every output goes outside the worktree. The stop rule can
be computed from the logged `Episode/Steps` / `Episode/Number` / `Episode/_window_n`, which are
written every 4,000 episodes.

| # | Sev | Where | Issue | Fix |
|---|---|---|---|---|
| C1 | 🔴 | §3.4 "Code", §9.2 | No code freeze. The design pins no launch SHA, forbids no edits, and does not inherit the pilot's runner pre-flight or run-validity checks (THIRST_PILOT §3.2, §2.7 P5); §9.2 inherits only §2.5. PLACEMENT_FIXES_PLAN's start gate names only the pilot runs, which finished at 17:48, so the environment code may now be edited in this worktree. Running jobs are mostly safe (their code is already loaded), but late launches, §7 relaunches and the §5.4 seeds 43/44 would train in a different world without anyone noticing. | Add §9.3: one launch SHA for all 18 runs, relaunches and follow-ups (if the code moves first, the addendum re-runs seed 42); no edits to `src/`, `train.py`, `configs/` or runtime `scripts/` here until the last run ends (placement work goes in a separate worktree); a diary freeze note; pilot §3.2 pre-flight; P5-style validity per run, plus a check that the saved config shows `water.properties [1,0,0,0,0]` and the cell's size, `water.size` and `sensor_radius`. Add "THIRST_TASK runs finished" to PLACEMENT_FIXES_PLAN K0. |
| M1 | 🟡 | §4, §9.2 | The stop is defined as "SIGINT right after the checkpoint", but checks will be late, and the ordinary run is about 20–25 % ahead of its modulated partner. Without a rule, the "last 1 M before the stop" differs between the two agents. Who checks, how often, with what tool, and what stop command are not stated. | Define the stop boundary b* retroactively. Final model = checkpoint b*; S_final and Δ read [b*−1 M, b*] for both runs; anything after b* is ignored. Name a reader script (test it on the pilot runs), a cadence and the exact stop command (full unique tag, sent once; a second SIGINT force-quits). Put both agents of a world on the same card class. |
| M2 | 🟡 | §4 rule 2 | "Learned" is judged on survival only. A run that eats but does not yet drink can be stopped. A falling curve also counts as a plateau. | Require §5.1(a) to pass at the stop. Flag two consecutive falls rather than stopping. |
| M3 | 🟡 | §5.3–5.4 | The 6 % line rests on 3 seeds at 2 M on the old smell (σ's 95 % range is about 1.4–16 %). In the pilot, one of three same-world seed pairs already gave +7.3 %. Across 9 worlds there is about a 38 % chance of at least one false lead. The follow-up's compute, its decision rule and the handling of the selected seed 42 (winner's curse) are not pre-registered, and it is one-sided. | Pre-register now: confirm on seeds 43/44 (or handle seed 42's selection); the 3-seed rule; a follow-up compute ceiling; whether ≤ −6 % worlds also get seeds. |
| M4 | 🟡 | §5.2, §5.3, §5.4 | Claims stronger than one seed allows. The reach × size refutation conflicts with §5.4, and the noise of a difference of differences is about 5 %. The exploratory hypothesis is "supported" by one noise lead about 1/3 of the time and, read literally, when there are no leads at all. "≥ 10 % readable" uses the 10×10 σ. | Reword as descriptive, close the "if any" loophole, and condition on the spread seen at the larger sizes. |
| M5 | 🟡 | §3.5, §5 | Only the episode-matched Δ is pre-registered. The agent that survives longer gets more updates per episode; the pilot measured a 25–31 % experience gap. | Pre-register an equal-environment-steps read-out for every Δ and for the size/reach costs. |
| M6 | 🟡 | §3.3, §5.2 | `sensor_radius` cuts every smell channel (`sensor.py:37-51`), including predator odour. The "thirst, not starvation" mechanism and refutation clause ignore injury. | State it, and make §5.2's outcome three-way. |
| M7 | 🟡 | §5, §6.4 | Drinking rate and survival by start hydration are not in the training log. The pilot got them from stored greedy episodes. There is no analysis-plan section. | Add §5.5 (checkpoints, collector run from the worktree, tools that must not be used), or drop those read-outs. |
| L1 | 🟢 | §3.5 | Regrown food landing on a fire (~2 %) or a bush (~7 %) is not listed. | One row. |
| L2 | 🟢 | §6 | The check evidence lives only in the worktree's gitignored `tmp/`. | Copy it to the shared `tmp/` or call it disposable. |

**Answers to the specific questions.** Stopping both agents of a world together does not bias the
comparison: neither agent is cut off while still improving. The remaining biases are the
experience gap (M5) and the undefined overshoot window (M1). Comparability with the pilot and with
context exploration is handled correctly. Project rules (survival steps only, no invented
versions, the study-folder precedent, the change-log entry) are met.

**Exit condition:** C1's paragraph, here and in PLACEMENT_FIXES_PLAN K0, flips the verdict to
SOUND WITH CONCERNS. The Moderates can be fixed in the same edit or accepted knowingly.

**Cost of being wrong:** a placement fix landing mid-series makes the later-launched, relaunched
and follow-up runs train in a different world from the seed-42 runs, and nothing shows it in
WandB. That means about 30–170 GPU-h of reruns per affected world, and a modulator lead judged on
mismatched seeds. No data-loss hazard was found.

Reviewed by: plan-reviewer
