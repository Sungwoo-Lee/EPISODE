---
title: "Single-channel smell: does a harder-to-read rabbit make the agent confuse it for a predator, and does that confusion grow with injury?"
topic: hypervigilance
status: active
created: 2026-09-30
last_updated: 2026-09-30
wandb_tag: rppo_hv1ch / rppo_hv2ch
---

# Single-channel smell: rabbit–predator confusion and hypervigilance

> **Status**: PRE-REGISTERED — designed, configs written and validated on the trainer's own loader, **nothing launched**.
> **Date**: 2026-09-30
> **Author**: experiment-designer
> **Base pages**: *What makes this agent hide?* ([[a01_hiding_drivers]], `docs/experiments/active/trajectory_factors/a01_hiding_drivers.html`) — where the scent false alarm and the aimed rabbit response were first measured; *Modulator clues* (`docs/experiments/active/modulator_clues/modulator_clues.html`) — where hypervigilance was re-analysed on the project's definition (commit `d29beb56`) and found absent under assigned injury.
> **Related**: [[LEVEL05_BODY_INTERACTIONS]] (supplies the seed-42 control pair and the collection spec this study copies); [[sameprop_existing_run_survey]] and the sameProp rounds (identical smell for both animals: the agent still told them apart by how they move); the injury-gated smell-noise design of basic level 06 (wiki `20260630_1629_injury_gated_olfactory_noise_hypervig`).

---

## 1. Research Question

**Plain-language framing.** In our standard world (the "level 05" world: a 10×10 grid with food,
bushes to hide in, campfires, a body that gets hungry, cold and injured, one or two hunting
predators and one or two harmless rabbits), the agent cannot tell the two animals apart by
sight — vision only reports *that* something is in a square, not *what*. Identity comes from
**smell**. Each animal gives off two odours: a predator smells roughly "0.7 of odour A and 0.5 of
odour B", a rabbit the reverse, "0.5 of A and 0.7 of B", and each animal's recipe is jittered at
random every episode (standard deviation 0.3 per odour). Because the *ratio* of A to B is the same
whether the animal is next to you or across the map, the two odours give the agent a
distance-proof identity cue.

We ask what happens when that cue is taken away. In the new **single-channel world**, odour B is
switched off for both animals: a predator smells of "0.7 of A", a rabbit of "0.5 of A", with the
same jitter as before. Now the only smell difference is *how strong* odour A is — and a faint
predator far away smells like a rabbit nearby. The classes overlap more (an ideal observer reading
one animal's recipe misclassifies it about 37 % of the time instead of 32 %, and the distance-proof
ratio is gone entirely). Everything else about the world is unchanged.

Two questions, asked of both of the project's standard agents (the ordinary agent and the fully
neuromodulated agent), three training seeds each:

- **Q1 — confusion.** Does the agent treat the harmless rabbit more like a predator in the
  single-channel world — hiding more when a rabbit comes close?
- **Q2 — hypervigilance.** Does that confusion grow with injury? The project defines
  hypervigilance as *injury-dependent avoidance of the harmless rabbit*: a badly injured agent
  avoids or hides from the rabbit more than a lightly injured one. The wound is assigned at random
  at the start of each episode, which makes this reading causal. In the current world neither agent
  shows it (the modulator-clues page, Figure 3).

The hypothesis (the user's): a harder-to-read smell produces more confusion, and more confusion
produces more hypervigilance. The key informative outcome is the split case — **confusion rises but
its injury dependence does not** — which would show confusion alone is not sufficient for
hypervigilance.

**Formal hypotheses** (per agent; "single-channel minus control" = mean of the three
single-channel seeds minus mean of the three two-channel control seeds; decision rules in §5.3):

> **H₁a** (*single-channel smell makes the agent hide from a nearby rabbit more*): the rabbit
> proximity effect (§5.1, P1) is at least 3 percentage points (pp) larger in the single-channel
> world, with complete seed separation.
> **H₁b** (*and that response now grows with injury*): the causal injury shift of the rabbit
> proximity effect (§5.1, P2) is at least 2 pp larger in the single-channel world, with complete
> seed separation, **and** positive in all three single-channel seeds.
> **H₀** (*smell format does not matter*): neither difference clears its rule; see §5.3 for what
> counts as a refutation versus an inconclusive result.

---

## 2. Experimental Design

### 2.1 Independent Variables

| Factor | Levels | Notes |
|---|---|---|
| **Smell format** (the manipulation) | **single-channel**: predator `[0, 0.7, 0, 0, 0]`, rabbit `[0, 0.5, 0, 0, 0]`, SD `[0, 0.3, 0, 0, 0]` both · **two-channel control** (level 05 as is): predator `[0, 0.7, 0.5, 0, 0]`, rabbit `[0, 0.5, 0.7, 0, 0]`, SD `[0, 0.3, 0.3, 0, 0]` both | Values sampled per animal per episode, `clip(mean + SD·N(0,1), 0, 1)` (`src/environment/core.py:2044`). |
| **Agent** (crossed, not compared) | ordinary (`nmngaenorm_t1none`) · neuromodulated (`nmngaenorm_t16quad_ALL`, the modulator writing to all four sites) | Each agent is analysed separately; the study makes no modulated-vs-ordinary claim. |
| **Seed** | 42, 43, 44 | Seed 42 control = the existing level-05 factorial `w0000` pair (§2.4). |

### 2.2 Verified current smell values (2026-09-30)

Read from the resolved `EnvParams` of the live loader (`load_env_config` → `load_env_params`,
the path `train.py:594` uses) **and** from the saved `models/config.yaml` of the seed-42 control
runs (what actually trained):

| | channel 1 ("Odour A", predator-leaning) | channel 2 ("Odour B", neutral-leaning) |
|---|---|---|
| predator mean / SD (level 05) | 0.7 / 0.3 | 0.5 / 0.3 |
| rabbit mean / SD (level 05) | 0.5 / 0.3 | 0.7 / 0.3 |

The inventory's "spread 0.3, clipped" is correct: SD 0.3 on both channels, sampled values clipped
to [0, 1]. The 0.4 the user saw in `default.yaml` is not what level 05 runs: the entity list is
redeclared at basic/04 (`04-jump_attack_10x10.yaml`) with SD 0.3, and basic/05 inherits it.
No other object emits on channels 1 or 2 (food = channel 0, bush = 3, tree = 4; checked: every
resource and obstacle has 0 on channels 1–2), so in the single-channel world channel 2 reads 0 in
every observation.

**What the manipulation does, quantitatively** (2 M simulated draws, clipping included):

| | two-channel | single-channel |
|---|---|---|
| separability of one animal's recipe, d′ | 0.94 | 0.66 |
| ideal observer misreads a rabbit as predator | 31.6 % | 37.0 % |
| rabbits smelling more predator-like than the median predator | 17.5 % | 25.3 % |
| distance-proof identity cue (ratio of two odours) | yes | **no** |
| mean total animal odour (rabbit / predator) | 1.18 / 1.18 | 0.50 / 0.68 |
| rabbit channel-1 value clipped at 0 / at 1 | 4.8 % / 4.8 % | same |

The per-animal separability change is modest; the larger change is the loss of the ratio cue,
which forces identity to be read from strength — which is confounded with distance. Two side
effects come with the manipulation and cannot be removed without changing the user's
specification: (i) total animal odour roughly halves, so animals are less *detectable* by smell;
(ii) predators now smell ~35 % stronger than rabbits on average, so strength carries class
information it did not carry before. Both are registered as confounds (§2.5) and have dedicated
readouts (§5.2).

**The evidence scale is shared.** For Gaussian recipes with equal SD, the log-likelihood ratio
"predator vs rabbit" of one animal's recipe is `2.22 × (x1 − x2)` in the two-channel world and
`2.22 × (x1 − 0.6)` in the single-channel world. So "predator-likeness" defined as `x1 − x2`
(two-channel, the existing definition) and as `x1` (single-channel) carry **the same evidence per
unit**; a slope "pp of hiding per unit predator-likeness" is comparable across the two worlds
(clipping aside). The thresholds in §5 are stated on this scale.

### 2.3 Controlled Variables

Everything not under test comes from `basic/05-campfire_thermal_10x10.yaml` through its ladder
(`05 → 04 → 03 → default.yaml`): random start position; random start nutrition and injury
(injury uniform on [0, 100] — the randomisation that makes the injury reading causal); random start
body temperature [−10, +5]; pouncing predators (reach 2–3, 50 % success); bushes that hide the
agent and block animals; 1–3 campfires; food 1–4; ambush predators 2–12; predators 0–2 and rabbits
0–2 per episode; 58-number observation. Training: 10,000,000 episodes, default checkpoint cadence
(every 200 k episodes, 50 checkpoints), `--log-interval 10`, γ = 0.95, the two agent configs above
unchanged.

**Validation performed (2026-09-30, live loader, project interpreter, CPU):**

- `single_channel_smell_l05.yaml` vs the control twin: resolved `EnvParams` (208 fields) differ in
  **exactly two fields**, `animal_property` and `animal_property_std`, and only in column 2.
- Control twin vs `basic/05` and vs `level05_body_interactions/worlds/w0000.yaml`: **empty diff**.
- The seed-42 control runs' own saved `models/config.yaml`, loaded through today's
  `load_env_params`: **empty diff** against the control twin (both agents). Today's trainer merge of
  the control twin shares every key of the saved config with the same value (the only differences
  are keys the train/visualisation/wandb layers add, and `agent.modulation.type` between agents).
- Both worlds build, reset and step; observation width **58** in both (Olfaction 25 = 5 channels ×
  5-cell diamond, unchanged).
- **Pairing verified:** on evaluation seed 1,000,000 the four animals' channel-1 draws are
  identical in the two worlds (0.8512, 1.0, 0.1827, 0.7134); channel 2 is 0 in the single-channel
  world. The odour jitter key does not depend on the means, so this holds for every episode.
- No critical-settings registry value changes (`sensory.vector_size` 5, `decay_power` 1.0,
  `sensor_radius` 20, `olfactory_grid_range` 1 all unchanged; entity odour vectors are not a
  registry row), so no change-log entry is written.

### 2.4 Seeds, pairing and the seed-42 control

- **Three seeds per cell.** 3 v 3 is the smallest design in which a complete-separation rule has a
  meaningful error rate (one-sided exact permutation p = 1/20 = 0.05). §5.3 pre-registers the
  top-up to five seeds if a result is inconclusive.
- **Seeds pair across worlds.** `train.py` derives the network initialisation and the environment
  key stream from `PRNGKey(seed)` alone (`src/utils/init_keys.py::trainer_init_keys`, unchanged
  by commit `18e1e5f0`, golden keys for 42–44 identical), and neither world changes the
  observation width. So the single-channel and control runs of one seed and one agent start from
  **identical weights** and see identical reset draws (animal counts, positions, injuries,
  channel-1 odours) until the policies diverge. Paired differences are reported alongside the
  unpaired rule.
- **Seed-42 control = the existing level-05 factorial cell `w0000`** (ordinary and modulated,
  launched 2026-09-27, 10 M episodes, same launch flags, stores already collected with this
  study's collection spec). Its saved world resolves identically to the control twin (above).
  Code drift since its launch: `src/` and `train.py` changes after 2026-09-27 are logging, a
  dashboard feature, opt-in activation capture and a key-recipe refactor proven bit-identical — no
  change to dynamics or initialisation. Registered anyway: seeds 43/44 have same-week controls,
  seed 42 does not; a seed-42 control that is an outlier against 43/44 is reported as such.

### 2.5 Confounds & Limitations

1. **Detection vs identification.** Halving total animal odour (§2.2) makes animals harder to
   *notice* as well as to *identify*. A drop in survival or in hiding near predators could be
   detection, not confusion. Readouts that separate them: the predator proximity effect and the
   killed-by-predator share (§5.2, S3–S4).
2. **Strength now carries class.** In the single-channel world a rabbit's predator-likeness *is*
   its odour strength; the two cannot be separated (in the two-channel world they are orthogonal,
   and a01 found both matter). The scent ladder in the single-channel world is therefore a
   likeness-plus-strength ladder; §5.2 S2 adds a matched reading on channel 1 alone in the control.
3. **Movement identifies the predator anyway.** The sameProp rounds found that with *identical*
   smells the agent still separated the classes by how they move (the predator hunts, the rabbit
   wanders). The manipulation may be largely compensated by motion cues; a null on Q1 is then a
   real finding about what the agent uses, not a failed manipulation — but it is reported as
   "identity recovered from movement is possible", not as "smell is irrelevant".
4. **One world, one level.** Results speak about level 05 only.
5. **Three seeds.** Marginal effects (below the §5.3 thresholds) are not detectable by design.

---

## 3. Launch Manifest

Tag = wandb-name, always. The runner fills Node, GPU, Launched at, WandB run ID and Log path; in
the Log-path cell it also records `git rev-parse HEAD` and
`git log -1 --format=%H -- configs/environment/default.yaml configs/environment/experiment/basic/`
(the ladder state, as in the level-05 study).

| Run | Status | Cell | Tag (= wandb-name) | wandb-group | wandb-job-type | Seed | Node | GPU | Launched at | WandB run ID | Log path |
|---|---|---|---|---|---|---|---|---|---|---|---|
| H01 | planned | 1ch · ordinary | `rppo_hv1ch_t1none_s42` | hv_single_channel_smell | prod | 42 | — | — | — | — | — |
| H02 | planned | 1ch · modulated | `rppo_hv1ch_t16quad_s42` | hv_single_channel_smell | prod | 42 | — | — | — | — | — |
| H03 | planned | 1ch · ordinary | `rppo_hv1ch_t1none_s43` | hv_single_channel_smell | prod | 43 | — | — | — | — | — |
| H04 | planned | 1ch · modulated | `rppo_hv1ch_t16quad_s43` | hv_single_channel_smell | prod | 43 | — | — | — | — | — |
| H05 | planned | 1ch · ordinary | `rppo_hv1ch_t1none_s44` | hv_single_channel_smell | prod | 44 | — | — | — | — | — |
| H06 | planned | 1ch · modulated | `rppo_hv1ch_t16quad_s44` | hv_single_channel_smell | prod | 44 | — | — | — | — | — |
| H07 | planned | 2ch · ordinary | `rppo_hv2ch_t1none_s43` | hv_single_channel_smell | prod | 43 | — | — | — | — | — |
| H08 | planned | 2ch · modulated | `rppo_hv2ch_t16quad_s43` | hv_single_channel_smell | prod | 43 | — | — | — | — | — |
| H09 | planned | 2ch · ordinary | `rppo_hv2ch_t1none_s44` | hv_single_channel_smell | prod | 44 | — | — | — | — | — |
| H10 | planned | 2ch · modulated | `rppo_hv2ch_t16quad_s44` | hv_single_channel_smell | prod | 44 | — | — | — | — | — |
| C01 | completed (not relaunched) | 2ch · ordinary | `rppo_l05body_w0000_t1none_s42` | level05_body_interactions | prod | 42 | 101 | cuda:0 | 2026-09-27T05:30:50 | `dg1ry2be` | `logs/20260927_053050.log` · run dir `results/JAX_RecurrentPPO/20260927-053057_rppo_l05body_w0000_t1none_s42` |
| C02 | completed (not relaunched) | 2ch · modulated | `rppo_l05body_w0000_t16quad_s42` | level05_body_interactions | prod | 42 | 106 | cuda:0 | 2026-09-27T05:30:54 | `nl1h2j21` | `logs/20260927_053055.log` · run dir `results/JAX_RecurrentPPO/20260927-053059_rppo_l05body_w0000_t16quad_s42` |

All ten new tags are unique and none matches an existing directory under
`results/JAX_RecurrentPPO/` (checked 2026-09-30: zero hits for `hv1ch` / `hv2ch`). C01/C02 keep
their own tags and group; the analysis finds them by run directory.

### 3.1 Configs to Produce

| Run | Config (env) | Config (agent) |
|---|---|---|
| H01, H03, H05 | `configs/environment/experiment/hypervigilance/single_channel_smell_l05.yaml` | `configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml` |
| H02, H04, H06 | `configs/environment/experiment/hypervigilance/single_channel_smell_l05.yaml` | `configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml` |
| H07, H09 | `configs/environment/experiment/hypervigilance/two_channel_smell_l05_control.yaml` | `…/nmngaenorm_t1none.yaml` |
| H08, H10 | `configs/environment/experiment/hypervigilance/two_channel_smell_l05_control.yaml` | `…/nmngaenorm_t16quad_ALL.yaml` |
| C01, C02 | (existing) `configs/environment/experiment/level05_body_interactions/worlds/w0000.yaml` — resolves identically to the control twin | as above |
| collection | `configs/trajectory_collection/hv_single_channel_smell.yaml` (paths are `FILL_AT_LAUNCH` placeholders — the collector refuses the file until they are replaced) | — |

The single-channel file restates the whole `entities:` list (lists replace wholesale on merge),
copied verbatim from basic/04 with only the four property lines edited. The control twin is a bare
`extends:` of basic/05, deliberately with no overrides.

**Launch command** (for `training-runner`, one per row H01–H10, wrapped by `run_command.py` /
`train_command-new.sh` per its own conventions; node and GPU chosen at launch from live state):

```
/home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
  --config configs/environment/experiment/hypervigilance/<single_channel_smell_l05 | two_channel_smell_l05_control>.yaml \
  --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/<nmngaenorm_t1none | nmngaenorm_t16quad_ALL>.yaml \
  --episodes 10000000 --device cuda:<gpu> --log-interval 10 \
  --tag "<tag>" --wandb-name "<tag>" \
  --wandb-group "hv_single_channel_smell" --wandb-job-type "prod" \
  [--seed 43 | --seed 44]
```

Seed-42 rows (H01, H02) pass **no** `--seed` — seed 42 is config-owned (`configs/train/default.yaml`),
exactly as C01/C02 were launched. Rows with seed 43/44 pass `--seed`.

**Pre-flight discriminators (blocking):**

1. Every banner prints observation width **58**; `t16quad` banners print
   `Neuromodulation: ENABLED (… sites=[encoder,rnn,actor,critic] …)`, `t1none` print `DISABLED`.
2. Each run's saved `models/config.yaml` (the ground truth, not a reload of the source):
   hv1ch rows show predator `properties: [0.0, 0.7, 0.0, 0.0, 0.0]` and rabbit
   `[0.0, 0.5, 0.0, 0.0, 0.0]`, both `properties_std: [0.0, 0.3, 0.0, 0.0, 0.0]`; hv2ch rows show
   `[0.0, 0.7, 0.5, 0.0, 0.0]` / `[0.0, 0.5, 0.7, 0.0, 0.0]` with SD `[0.0, 0.3, 0.3, 0.0, 0.0]`;
   `training.seed` equals the row's seed.
3. **After the last launch (ladder drift check):** load every saved `models/config.yaml` of
   H01–H10 and C01–C02 with `load_env_params` and diff field by field. Within a world the 12 files
   must give identical `EnvParams`; across worlds exactly `animal_property` and
   `animal_property_std` may differ. Any other difference (e.g. a new mandatory key landing in
   `default.yaml` from parallel work between launches) is a registered confound, reported with the
   runs it splits. Launch all ten from one checkout in one session to make this unlikely.

**Compute.** Ordinary ~14 h and modulated ~18 h per run on a 3090-class card (level-05 wall-clock):
5 × 14 + 5 × 18 ≈ **160 GPU-hours**, one wave on ten free GPUs. Collection afterwards: 10 runs ×
1 M episodes at the l05body cost per run, plus the time-course collection (§5.4).

---

## 4. Results

*(Blank until training and collection finish.)*

### 4.1 Primary Metrics (Hypothesis Test)
### 4.2 Secondary Metrics
### 4.3 Diagnostic Metrics
### 4.4 Learning Dynamics

---

## 5. Analysis plan (pre-specified)

Every measure is computed per run on its **final-checkpoint, 1,000,000-episode trajectory store**
(`seed_base` 1,000,000, so episode *i* presents the same reset draws to every run — and, within one
training seed, the same channel-1 odours to the single-channel and the control agent). The
seed-42 control reads `results/trajectories_l05body/`, all others `results/trajectories_hv1ch/`.
Steps are those the agent chose (t ≥ 1); distances are read on the row the action was chosen from.
No reward-based quantity is used anywhere.

### 5.1 Primary outcomes

| ID | What it measures (plain) | Exact definition (existing code) |
|---|---|---|
| **P1** (Q1) | **Rabbit proximity effect** — how much more the agent sits in a bush when a rabbit is 1–2 squares away than when the nearest rabbit is 6+ squares away. Higher = treats the rabbit more like a threat. | `_ladder.proximity_effect(rd_bush, rd_tot)` pooled over all four start-injury quarters (`NEAR_BINS = (0, 1)`, `FAR_BINS = (5, 6, 7)`; episodes with ≥ 1 rabbit), from the `collect_arm_data.build(..., stores=...)` sweep — the same function the modulator-clues page uses. |
| **P2** (Q2) | **Causal hypervigilance, hiding reading** — the rabbit proximity effect in the most-injured start quarter (injury 75–100) minus the least-injured (0–25). Positive = a badly wounded agent hides from a nearby rabbit more. | `a4_hypervigilance.hiding_shift(d, "rd")` = `proximity_effect(..., (3,)) − proximity_effect(..., (0,))`. |
| **P2d** (Q2, corroboration) | **Causal hypervigilance, distance reading** — share of the first 25 steps (predator-free steps only) with the nearest rabbit within 2 squares, most- minus least-injured start quarter. Negative = the wounded agent keeps the rabbit away. | `scripts/analysis/rabbit_avoidance.py`, `start.near_share_shift`. Runs unchanged on both worlds. |
| **Survival** (headline performance) | Mean survival steps per episode on the final store; termination shares (killed by predator, starved, frozen/overheated, time limit). | Episode `length` over the 1 M store; `termination_reason`. |

Survival is the project's headline metric and is reported first in every table, but it is not a
criterion for Q1/Q2: the prediction is only that survival is **lower** in the single-channel world
(harder identification costs meals through false alarms and lives through misses).

### 5.2 Secondary outcomes (pre-registered, all reported)

| ID | What | Definition |
|---|---|---|
| **S1** (the missing piece, *e*) | **Scent × injury interaction** — does the rabbit-scent false alarm grow with the assigned wound? | Episodes with **no predator and exactly one rabbit** (≈ 1/9 of episodes, ≈ 110 k per run — any hiding driven by that rabbit's scent is a pure false alarm). Outcome: bush share over the first 25 chosen steps. (i) **Quarter contrast:** the slope of that share on the rabbit's predator-likeness (pp per unit, linear fit on episodes) in the top start-injury quarter minus the bottom quarter. (ii) **Model:** quasi-binomial GLM (the `hiding_drivers.fit_glms` framework) with predator-likeness, start injury, their product, and the M1 exogenous covariates (start nutrition, bushes, rocks, food, ambush predators, spawn distance to bush); the product term reported in pp per unit likeness per 100 injury. Repeated on one-predator-one-rabbit episodes as a sensitivity check. Prediction: larger in the single-channel world. |
| **S2** | **Scent false alarm** (the a01 ladder) — hiding and survival as a function of the rabbit's randomised predator-likeness. | `hiding_drivers.py`: univariate `rab_smell_predatorness` (report **pp per unit**, the evidence-comparable scale of §2.2, and pp per SD) and model M3 (one predator + one rabbit). Plus the a01 extreme-row table (hiding, food per step, starved, killed, survival steps) for the rabbit's bottom vs top sixth of predator-likeness **within each world**. **Matched reading:** in the control, the same ladder on channel 1 alone with channel 2 as a covariate, so both worlds are also compared on the variable the single-channel agent actually receives. Predator-likeness = `x1 − x2` in the control (existing definition, unchanged), `x1` in the single-channel world. |
| **S3** | **Aimed response** — does predator-like rabbit scent raise hiding specifically when *that rabbit* is near? | The a01 three-way split on one-predator-one-rabbit episodes (nothing near / predator near / rabbit near), rabbit-like vs predator-like groups defined on the **shared evidence scale**: control `x1 − x2 < 0` vs `≥ 0.3` (a01's thresholds, unchanged); single-channel `x1 < 0.6` vs `≥ 0.9` (the same log-likelihood ratios, 0 and +0.67). Group sizes reported. |
| **S4** | **Predator response (context, confound 1)** — proximity effect for the predator (`pd` grids), killed-by-predator share, and the **confusion index** = rabbit proximity effect ÷ predator proximity effect. | Same sweep. A fall in the predator proximity effect in the single-channel world means detection/identification of *predators* also got worse, and Q1 must be read through the index. |
| **S5** | **Observational injury readings** — the same P2/P2d shifts on the injury the agent carries at that moment. | `hiding_shift(d, "rdc")`; `rabbit_avoidance.py` `current.near_share_shift`. Reported, never decisive (a currently injured agent was usually just attacked). |

### 5.3 The comparison and the noise rule

For each agent separately and each outcome `Y`:
`Δ(Y) = mean(Y over the 3 single-channel seeds) − mean(Y over the 3 control seeds)`, with the
per-seed values, the three **paired** differences (same seed = same initial weights and same reset
stream) and the between-seed SD of each arm shown beside it.

**Rule for "established":** (1) **complete separation** — all three single-channel seed values lie
beyond all three control seed values in the predicted direction (one-sided exact permutation
p = 0.05); **and** (2) `|Δ|` at least the minimum effect below. **Refuted:** complete separation in
the *opposite* direction, **or** `|Δ|` below the refutation floor with the two arms' seed ranges
overlapping. **Inconclusive:** anything else.

| Outcome | Predicted sign | Minimum effect | Refutation floor |
|---|---|---|---|
| P1 rabbit proximity effect | + | **3 pp** | 1 pp |
| P2 causal injury shift, hiding | + | **2 pp**, and the single-channel shift > 0 in all 3 seeds | 0.5 pp |
| P2d causal injury shift, distance | − | 1 pp (same sign as P2 required for H₁b; separation not required) | — |
| S1 scent × injury (quarter contrast) | + | 2 pp per unit likeness | — |
| Survival | − | reported with CI; no threshold | — |

**Why these thresholds.** The only multi-seed spreads measured on these readouts are from five
seeds of one configuration in the sensor-ladder work (critical-settings registry, 2026-09-21
entry): about 1.4 pp on the rabbit response and 1.05–2.67 pp on the injury-driven measure. A 3 v 3
difference with a 1.4 pp seed SD has a standard error of ≈ 1.1 pp, so 3 pp is ≈ 2.6 SE; 2 pp on
the noisier injury shift is 1–2 SE, which is why complete separation is also required. Current
single-seed values at level 05 (Wave 2, modulator-clues aggregates): P1 = +6.5 (ordinary) /
+4.5 pp (modulated); P2 = −1.9 / −1.7 pp; P2d = +0.8 / +0.6 pp. Before any hv run is read, the
same sweep is run on the five `cmp10m` plain-agent seeds (§5.5) and their between-seed SDs are
frozen into §4 as the study's own yardstick; the thresholds above are not changed by it.

**Verdict map (per agent):**

| P1 | P2 (+P2d) | Reading |
|---|---|---|
| established | established | **Hypothesis supported**: harder-to-read smell → more confusion → injury-dependent rabbit avoidance. |
| established | refuted / inconclusive | **Confusion without hypervigilance**: the agent confuses the animals more, but the wound does not amplify it — confusion alone is not sufficient. |
| refuted | any | **No extra confusion**: the agent recovers identity another way (movement, per sameProp) or ignores the scent; Q2 is read but not attributed to confusion. |
| inconclusive (either) | — | **Top-up**: add seeds 45 and 46 for that agent in both worlds (4 runs), re-apply with 5 v 5 using one-sided Mann–Whitney U ≤ 4 (p < 0.05) plus the same minimum effects. No further top-up; a second inconclusive is reported as inconclusive. |
| H₁b met but single-channel shift not positive in all seeds | — | **Partial**: single-channel smell weakens the wounded agent's boldness toward rabbits but does not produce hypervigilance. |

The two agents are not pooled; "supported in both agents" is the strongest statement allowed.

### 5.4 Temporal evolution (mandatory)

1. **Training curves.** Survival (`Episode/Steps`, logged every 10 episodes) for all 12 runs,
   smoothed over 1 % of training, overlaid by world per agent, with the single-channel-minus-control
   gap per seed pair over training. Last-10 % window mean (`Episode/_window_n`-weighted) reported as
   the training-time survival.
2. **Behaviour over training.** After training, a time-course collection at the checkpoints nearest
   2 M, 4 M, 6 M and 8 M episodes (the 10 M final store is the fifth point): 50,000 episodes each,
   `seed_base` 1,000,000, float32, for all 12 runs (C01/C02 included). P1, P2 and S4 are computed at
   each point. Question: does the gap between worlds emerge early (a perception limit) or late (a
   learned policy choice)? Descriptive only; P2 at 50 k episodes is expected to be noisy. The spec is
   written after training, when the checkpoint numbers exist (same convention as
   `configs/trajectory_collection/late_checkpoints/`).

### 5.5 Existing stores analysed alongside

| Store | What it is | How it is used |
|---|---|---|
| `results/trajectories_l05body/` — `w0000` pair | Seed-42 control (C01, C02) | **Part of the control arm**, not separate context. |
| `results/trajectories_basicq2_w1/`, `_w2/` (aggregates in `results/analysis/basicq2_integrated/`) — levels 03–06, both agents, one seed each | The curriculum ladder; level 06 = level 05 plus **injury-gated smell noise** (smell gets noisier the more injured the agent is) | **Descriptive context only, never pooled.** Level 06 is the reference for "confusion that grows with injury by construction": the within-wave level-06-minus-level-05 differences in P1 and P2 are shown next to this study's Δ. If level 06 produces a positive P2 and single-channel smell does not, the reading is that *injury-dependent* unreliability, not unreliability as such, is what drives hypervigilance. Caveats: single seed; Wave-2 level 05 started every episode at body temperature 0, so it is not like-for-like with this study's level 05; Wave 1 level 03 has no ladder-style aggregate. |
| `results/trajectories_nmngae/` — `cmp10m` plain agent, seeds 42–46 | Five seeds of one configuration in an older world (no smell direction, eight-channel vision that resolves identity) | **Seed-noise yardstick only**: between-seed SD of P1, P2, P2d, S2 computed with the same sweep before unblinding, frozen in §4. Not a control — its world differs in exactly the sense that matters (identity from vision). |

### 5.6 Analysis tooling required (not required for launch)

The runs and the collection need nothing new. The analysis does:

1. **`smell_channels()` refuses the single-channel config.** Both copies
   (`scripts/analysis/hiding_drivers.py:81` and `scripts/analysis/core/env.py:73`) require one
   channel where predators exceed rabbits *and* one where rabbits exceed predators; in the
   single-channel world the second does not exist, so `hiding_drivers.py` and
   `collect_arm_data.py` (P1, P2, S2, S4) stop with `SystemExit`. Needed: when exactly one channel
   separates the classes, predator-likeness = that channel and odour strength = that channel;
   the two-channel result must stay byte-identical (the `collect_arm_data` golden gate).
   `rabbit_avoidance.py` (P2d, S5) does not use it and runs as is.
2. **A study driver** that runs the sweep on the 12 runs over the two store roots, applies §5.3,
   and writes the per-seed table; plus a run-agnostic version of the a01 aimed split (S3) — the
   archived `supplementary/falsealarm.py` hard-codes the a01 store and slots.
3. **S1** (scent × injury) is new code: episode filter, early-window share, the quarter contrast
   and the GLM product term.

Route: the user invokes `feature-workflow` (`senior-developer` plans → `developer` implements)
before the analysis. **Metrics requested from `src/`: none** — every measure is computable from
the trajectory stores (`animal_property_sampled`, `injury_level`, `agent_in_bush`, positions).

### 5.7 Failure-mode catalog (decided now)

| Event | Decision |
|---|---|
| NaN / value explosion / crash in a run | The **run** is bad, not the hypothesis: relaunch the same tag suffixed `_r2`, same seed. The failed run is kept in the manifest as `failed`. |
| A single-channel agent learns a much weaker policy (training-time survival < 50 % of its paired control) | The world became a different task; behaviour measures are still computed but reported under "policy regime changed", and P1/P2 are not interpreted as confusion alone. |
| Predator proximity effect falls substantially in the single-channel world (S4) | Confound 1 is active: the manipulation degraded predator detection/identification too. Q1 is then read through the confusion index, and the headline says so. |
| P1 rises but mainly in the "nothing near" moments of S3 | Diffuse vigilance, not misidentification; Q1 is **not** counted as confusion even if P1 clears its rule. |
| Proximity-effect bins below 1,000 steps (function returns NaN) | Report as not computable for that run; no substitution of other bins. |
| Survival saturates at the 500-step limit in either world | Not expected at level 05; if it happens, survival is reported as a termination share only. |
| Effect visible at 8 M but not at 10 M (or the reverse) | The final checkpoint decides; the time course (§5.4) is reported as context. More steps are not added. |
| Seed noise swamps the effect | The §5.3 top-up (seeds 45, 46) once; then accept inconclusive. |

---

## 6. Conclusions

*(Blank until analysis.)*

### 6.1 Summary
### 6.2 Limitations & Open Questions
### 6.3 Recommended Next Experiments

---

## Appendix

### A. Raw Data Tables
*(Per-seed values of every §5 outcome, filled at analysis.)*

### B. Config Diffs

The only resolved difference between the two worlds (`EnvParams`, 208 fields compared):

```
animal_property      predators [0, 0.7, 0.5, 0, 0] -> [0, 0.7, 0, 0, 0]
                     rabbits   [0, 0.5, 0.7, 0, 0] -> [0, 0.5, 0, 0, 0]
animal_property_std  all      [0, 0.3, 0.3, 0, 0] -> [0, 0.3, 0, 0, 0]
```

### C. Changelog

- 2026-09-30 — designed (experiment-designer); configs and collection spec written; validated on
  the live loader; nothing launched.

---

## Feedback from plan-reviewer

*2026-09-30, on commit `71b7480a`. Full report with the simulation numbers:
[[plan_single_channel_smell_hypervigilance]] (`docs/reviews/plan_single_channel_smell_hypervigilance.md`).*

**Verdict: NOT READY** — one Critical, four Moderate. Nothing wrong with the two worlds or the
collection spec; the block is in §5.3 and the verdict map, which is fixable in this document alone.

Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run ·
🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

| # | Sev | Where | Issue | Suggested fix |
|---|---|---|---|---|
| C1 | 🔴 | §5.3 rule + verdict map rows 2 and 4 | **The Q2 rule cannot be met at its own minimum effect, and the verdict map turns the resulting "inconclusive" into a substantive claim.** Simulating the plan's own numbers (control P2 ≈ −1.8 pp, minimum effect +2 pp, seed SD 1.05 / 1.5 / 2.67 pp from the 2026-09-21 registry entry): P2 "established" 16 / 13 / 9 %, "inconclusive" ~80 %, "refuted" 4 / 9 / 13 %. P1 at a true +3 pp with SD 1.4: established 45 %, inconclusive 51 %. The 5 v 5 top-up (U ≤ 4 + minimum effect) has 45 % (SD 1.5) to 26 % (SD 2.67) power on P2 and 50 % on P1. Verdict-map row 2 reads "P1 established, P2 refuted **/ inconclusive**" as *confusion without hypervigilance — confusion alone is not sufficient*, so the most probable outcome of a TRUE minimum effect is the study's flagship negative claim. Separately, a 3 v 3 "refuted" (4–13 % at the true minimum effect) is exempt from the top-up. | (a) Row 2 fires only on P2 **refuted after the top-up**; P2 inconclusive → "not established", never a reading. (b) Print the power numbers in §5.3 so the reader knows 3 v 3 is a screen. (c) Either 5 v 5 up front (≈ 267 GPU-h) or make a 3 v 3 refutation also trigger the top-up. (d) Reconsider "positive in all three seeds": at −1.8 + 2 = +0.2 pp expected, the sign clause alone passes ≈ 50 %³ of the time. Owner: `experiment-designer`. |
| M1 | 🟡 | §3 pre-flight discriminator 2 (`training.seed`) | `train.py:612` writes `--seed` to the **top-level** `seed` key and `:786` reads it back from there; `training.seed` is the `configs/train/default.yaml` value (42) and is never updated. The saved C01 config carries both (`training.seed: 42` line 433, `seed: 42` line 438). For the eight seeded rows the check fails whether the launch was right or wrong, so it discriminates nothing. | Check top-level `seed` in `models/config.yaml` and the `Seed:` banner line (`train.py:1144`). Owner: `experiment-designer` → `training-runner`. |
| M2 | 🟡 | §2.4, §5.5, collection spec header | The seed-42 control stores were collected 2026-09-28 00:25 / 00:59 KST (manifest `collected_at`), **before** commit `2d54453d` (2026-09-30) forced full-float32 matmuls in the collector; their manifests carry no `matmul_precision` / `compute_device_kind`. Known Bugs row "A trajectory store replays exactly only under the matmul precision mode it was collected in": 99.8 % action agreement across modes. The ten new stores will be full-float32, so one control seed carries a 0.2 %-of-actions perturbation the other two do not. | Re-collect C01/C02 into `results/trajectories_hv1ch/` with the current collector (2 × 1 M episodes) — add two rows to the spec, drop the two-root special case. Owner: `experiment-designer`. |
| M3 | 🟡 | P1 / P2 as computed by `collect_arm_data.py:123-133` | Two base-page caveats are not carried into §2.5. (a) `np.clip(drab, 1, DIST_MAX) − 1` files a rabbit **on the agent's cell** into the NEAR bin; bushes block animals, so a distance-0 row can never be a hiding row — the near-bin bush share is diluted by each world's rabbit-contact rate (Known Bugs, OPEN: "Chasing rabbit stays glued to the agent after contact", `core.py:629`). A world in which the agent contacts rabbits less gets a higher P1 mechanically — the predicted direction. (b) The `rd` grid has **no predator-near exclusion** (only `has_r` episodes), so rows with a predator also within 2 cells count toward the rabbit proximity effect; any S4 change bleeds into P1. | In the tooling plan that is already required for `smell_channels`, add as pre-registered sensitivity readings: a distance-0 row count per world (or an extra bin), and a predator-free variant of P1/P2 (`dpred > 2`). Primary stays as is for comparability. Owner: `experiment-designer` (pre-register) → `senior-developer` (tooling plan). |
| M4 | 🟡 | Verdict map row 3 | Detection loss and confusion push P1 in **opposite** directions (rabbit total odour 1.18 → 0.50 makes a near rabbit less noticeable, P1 ↓; confusion, P1 ↑), so a P1 null can be cancellation. The failure-mode catalog handles a falling S4, but row 3 reads P1-refuted as "no extra confusion" unconditionally. | Row 3 reads "no extra confusion" only if the predator proximity effect (S4) is unchanged; otherwise "not separable from detection loss". Owner: `experiment-designer`. |
| L1 | 🟢 | Config comments, §5.3 row 5, §5.5 | `single_channel_smell_l05.yaml` cites "design doc §3.2"; the validation is §2.3. Verdict row 5 "H₁b met but shift not positive in all seeds" is self-contradictory (H₁b includes the sign clause). §5.5 calls `cmp10m` "no smell direction" — its saved config has the same 0.7/0.5 vs 0.5/0.7 two-channel layout; what differs is grid-range-0 smell and 8-channel vision. `out_root: results/trajectories_hv1ch` also holds the 2ch controls. | Wording only. |

**Assumptions the plan rests on (❓ Open unless marked verified):**

- *Verified:* the LLR identity in §2.2 (`2.22·(x1−x2)` vs `2.22·(x1−0.6)`); `smell_channels` raises `SystemExit` on the single-channel config (argmin lands on a zero column, `d[b] >= 0`); the launch wrapper `train_command-new.sh` `cd`s to the main tree, which is on `v4.0` at `71b7480a` — the thirst work sits in the isolated worktree `.claude/worktrees/thirst` on `v5.0` and does not touch it; `8187c570` (`bush_min_fire_distance`) landed 00:34 on 2026-09-27, before the 05:30 control launch; `89f3cb78` (balance metrics, 16:21) is logging only; C01/C02 keep all 50 checkpoints, so the §5.4 time course is feasible.
- ❓ O1: the main tree stays on `v4.0` for the ~18 h wave. A branch switch mid-run changes what the async checkpoint-render subprocess imports (not the dynamics). Say so in the diary launch row.
- ❓ O2: the `d′ 0.94 → 0.66` table is the designer's own 2 M-draw simulation; not re-derived here.
- ❓ O3: "paired" runs share only initial weights and the first reset — the first observation already differs (channel 2), so policies diverge at gradient step 1. The paired differences are not much stronger than the unpaired rule; fine as long as they stay secondary.
- ❓ O4: C01 trained on node 101 (2080 Ti, full-float32 matmul), C02 on 106 (3090, TF32); the new runs land wherever is free. Every study carries this; the manifest's Node/GPU columns are the record.

**Prior-art pass (done):** Known Bugs rows read — "Chasing rabbit stays glued" (OPEN, not cited → M3), "store replays exactly only in its own matmul mode" (not cited → M2), "five 2026-09-04 reference runs sit at a different level — spread only" (plan complies), "reset not bit-identical on `animal_property_sampled` (1 ulp)" (harmless to the pairing claim). No prior single-channel-smell plan in `docs/llm_wiki/` or `docs/develop/`; the sameProp and injury-gated-noise entries the plan cites are the right ones. Nothing new for `bug-curator`.

**Project rules:** no reward metric anywhere; survival is headline, not criterion; no registry value changes (entity odour vectors are not a row — checked); no `scripts/` or schema change in this plan (the later tooling plan must run the dependency-map check); interpreter path correct; frontmatter present. Mechanical YAML validation is `env-config-reviewer`'s.

**Cost of being wrong:** ~160 GPU-hours plus the top-up and two collection passes, arriving with ~80 % probability (at the plan's own minimum effect) at a P2 "inconclusive" that the verdict map as written promotes into "confusion alone is not sufficient for hypervigilance" — a claim that would enter the hypervigilance narrative. No data-loss hazard anywhere in the plan.

**What flips the verdict:** rewrite §5.3 and the verdict map per C1 (a)–(d) and fold M1–M4 into §3 / §2.5 / §5.6. No config or code change is needed to launch.

*Reviewed by: plan-reviewer*
