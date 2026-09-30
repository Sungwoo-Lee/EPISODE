---
title: "Single-channel smell: does a harder-to-read rabbit make the agent confuse it for a predator, and does that confusion grow with injury?"
topic: hypervigilance
status: active
created: 2026-09-30
last_updated: 2026-09-30
wandb_tag: rppo_hv1ch / rppo_hv1chm / rppo_hv2ch
---

# Single-channel smell: rabbit–predator confusion and hypervigilance

> **Status**: PRE-REGISTERED, **Revision 1 (2026-09-30, pre-launch)** — a third world added (matched smell strength) and the decision rule rewritten after plan review (see [Revision 1](#revision-1) and [Response to plan-reviewer](#response-to-plan-reviewer)). Configs written and validated on the trainer's own loader; **nothing launched**.
> **Date**: 2026-09-30
> **Author**: experiment-designer
> **Base pages**: *What makes this agent hide?* ([[a01_hiding_drivers]], `docs/experiments/active/trajectory_factors/a01_hiding_drivers.html`) — where the scent false alarm and the aimed rabbit response were first measured; *Modulator clues* (`docs/experiments/active/modulator_clues/modulator_clues.html`) — where hypervigilance was re-analysed on the project's definition (commit `d29beb56`) and found absent under assigned injury.
> **Related**: [[LEVEL05_BODY_INTERACTIONS]] (supplies the seed-42 control runs and the collection spec this study copies); [[sameprop_existing_run_survey]] and the sameProp rounds (identical smell for both animals: the agent still told them apart by how they move); the injury-gated smell-noise design of basic level 06 (wiki `20260630_1629_injury_gated_olfactory_noise_hypervig`); plan review [[plan_single_channel_smell_hypervigilance]].

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

We take that cue away in two ways, so that "hard to tell apart" and "hard to notice" can be
separated:

- **Single-channel world** (the user's original manipulation): odour B is switched off for both
  animals — predator "0.7 of A", rabbit "0.5 of A", same jitter. The animals become harder to tell
  apart (the ratio is gone; only strength differs, and a faint predator far away smells like a
  rabbit nearby) **and** harder to notice (total animal smell roughly halves).
- **Matched-strength world** (added in Revision 1): both animals smell of the *same* 50/50 mix of
  A and B — predator 0.67 + 0.67, rabbit 0.53 + 0.53, same jitter. The ratio again carries no
  identity, and the two animals are as hard to tell apart as in the single-channel world, but the
  total amount of animal smell is the same as today's. Only "hard to tell apart" changes.
- **Control**: level 05 as it is.

Two questions, asked of both of the project's standard agents (the ordinary agent and the fully
neuromodulated agent), three training seeds each:

- **Q1 — confusion.** When the animals are harder to tell apart, does the agent treat the harmless
  rabbit more like a predator — hiding more when a rabbit comes close?
- **Q2 — hypervigilance.** Does that confusion grow with injury? The project defines
  hypervigilance as *injury-dependent avoidance of the harmless rabbit*: a badly injured agent
  avoids or hides from the rabbit more than a lightly injured one. The wound is assigned at random
  at the start of each episode, which makes this reading causal. In the current world neither agent
  shows it (the modulator-clues page, Figure 3).

The hypothesis (the user's): a harder-to-read smell produces more confusion, and more confusion
produces more hypervigilance. The matched-strength world is the clean test of that hypothesis;
the single-channel world is kept because it is the manipulation the question started from, and the
difference between the two tells us how much of any single-channel effect is merely animals being
harder to *notice*.

**How strong a test this is.** Three seeds per world detect effects of about twice the minimum
sizes below reliably; at the minimum sizes themselves roughly half of true effects are confirmed
and the rest end "not established" (§5.3 prints the numbers). A result that is not confirmed at
three seeds triggers one pre-registered top-up to five seeds. "Not established" is never read as
evidence of absence.

**Formal hypotheses** (per agent; each tested on the **identifiability contrast** — matched-strength
minus control — and, separately, on the **single-channel contrast** — single-channel minus control;
decision rules in §5.3):

> **H₁a** (*harder-to-tell-apart smell makes the agent hide from a nearby rabbit more*): the rabbit
> proximity effect (§5.1, P1) is at least 3 percentage points (pp) larger than in the control.
> **H₁b** (*and that response grows more with injury*): the causal injury shift of the rabbit
> proximity effect (§5.1, P2) is at least 2 pp larger than in the control.
> **H₀** (*smell format does not matter*): each difference is shown to be smaller than its minimum
> size (§5.3 "refuted"), after the top-up.

---

## 2. Experimental Design

### 2.1 Independent Variables

| Factor | Levels | Notes |
|---|---|---|
| **Smell format** (the manipulation) | **single-channel** (`1ch`): predator `[0, 0.7, 0, 0, 0]`, rabbit `[0, 0.5, 0, 0, 0]`, SD `[0, 0.3, 0, 0, 0]` both · **matched-strength** (`1chm`): predator `[0, 0.67, 0.67, 0, 0]`, rabbit `[0, 0.53, 0.53, 0, 0]`, SD `[0, 0.3, 0.3, 0, 0]` both · **two-channel control** (`2ch`, level 05 as is): predator `[0, 0.7, 0.5, 0, 0]`, rabbit `[0, 0.5, 0.7, 0, 0]`, SD `[0, 0.3, 0.3, 0, 0]` both | Values sampled per animal per channel per episode, `clip(mean + SD·N(0,1), 0, 1)` (`src/environment/core.py:2044`). |
| **Agent** (crossed, not compared) | ordinary (`nmngaenorm_t1none`) · neuromodulated (`nmngaenorm_t16quad_ALL`, the modulator writing to all four sites) | Each agent is analysed separately; the study makes no modulated-vs-ordinary claim. |
| **Seed** | 42, 43, 44 (top-up: 45, 46, §5.3) | Seed-42 control = the existing level-05 factorial `w0000` runs (§2.4). |

**The three contrasts** (per agent):

| Contrast | Worlds | What changes | What is held |
|---|---|---|---|
| **B — identifiability** (primary for the hypothesis) | matched-strength − control | tell-apart-ability: d′ 0.94 → 0.65, ratio cue removed | average total animal smell (1.18 vs 1.18) |
| **A — single-channel** (the original manipulation) | single-channel − control | tell-apart-ability **and** strength (1.18 → 0.59) | everything else |
| **C — strength** (the detection decomposition) | single-channel − matched-strength | total animal smell (0.59 vs 1.18) | tell-apart-ability (d′ 0.66 vs 0.65, no ratio cue in either) |

A ≈ B + C (the two need not add exactly). Claims about *identifiability* rest on contrast B; claims
about *the single-channel manipulation* rest on A; C says how much of A is detection.

### 2.2 Verified current smell values (2026-09-30) and what each world does

Read from the resolved `EnvParams` of the live loader (`load_env_config` → `load_env_params`,
the path `train.py:594` uses) **and** from the saved `models/config.yaml` of the seed-42 control
runs (what actually trained):

| | channel 1 ("Odour A", predator-leaning) | channel 2 ("Odour B", neutral-leaning) |
|---|---|---|
| predator mean / SD (level 05) | 0.7 / 0.3 | 0.5 / 0.3 |
| rabbit mean / SD (level 05) | 0.5 / 0.3 | 0.7 / 0.3 |

The inventory's "spread 0.3, clipped" is correct: SD 0.3 on both channels, sampled values clipped
to [0, 1]. The 0.4 in `default.yaml` is not what level 05 runs: the entity list is redeclared at
basic/04 (`04-jump_attack_10x10.yaml`) with SD 0.3, and basic/05 inherits it. No other object
emits on channels 1 or 2 (food = channel 0, bush = 3, tree = 4; every resource and obstacle has 0
on channels 1–2), so in the single-channel world channel 2 reads 0 in every observation.

**The three worlds, quantitatively** (2 M simulated draws per class, clipping included; "misread"
= a rabbit falls on the predator side of the midpoint between the two classes' mean statistic —
`x1 − x2` in the control, `x1` in single-channel, `x1 + x2` in matched):

| | control (2ch) | single-channel (1ch) | matched-strength (1chm) |
|---|---|---|---|
| separability of one animal's recipe, d′ | 0.94 | 0.66 | **0.65** |
| ideal observer misreads a rabbit as predator | 31.5 % | 38.5 % | 38.4 % |
| distance-proof identity cue (ratio of the two odours) | yes | no | no |
| mean total animal odour, predator / rabbit | 1.18 / 1.18 | 0.68 / 0.50 | 1.30 / 1.05 |
| mean total animal odour, average of the classes | 1.18 | 0.59 | **1.18** |
| predator channel 1 clipped at 1.0 | **15.9 %** | **15.9 %** | 13.5 % (and 13.5 % on ch 2) |
| predator channel 2 clipped at 1.0 | 4.8 % | — | 13.5 % |
| rabbit channel 1 clipped at 1.0 / at 0 | 4.8 % / 4.8 % | 4.8 % / 4.8 % | 5.9 % / 3.9 % |
| rabbit channel 2 clipped at 0 | 1.0 % | — (always 0) | 3.9 % |

*(Revision 1 note: the first version quoted 37.0 % single-channel misreads, using the unclipped
boundary `x1 = 0.6`; the table now uses one boundary rule for all three worlds.)*

**How the matched values were chosen.** The request was one smell channel with each animal's total
equal to today's. Taken literally that is impossible, for two reasons: both animals today total
1.2, so matching each one gives two identical animals (no separation at all); and one channel is
capped at 1.0 by the sampler, below the 1.18 an average animal smells today. The best literal
single-channel settings tried reach only 0.75–0.84 average strength with heavy clipping (predator
1.0 / rabbit 0.8: 0.82, half of predators clipped at 1.0; 1.4 / 1.0 with SD 0.6: 0.84, 75 %
clipped, d′ 0.52). The matched world instead carries **one odour mix on two receptor channels**
with the same 1 : 1 recipe for both classes, so the ratio says nothing about identity. Two
conditions fix the two numbers: (i) separability equal to the single-channel world —
`d′ = √2 · (a − b) / 0.3 = 0.2 / 0.3` gives `a − b = 0.14`; (ii) average strength equal to today's —
`a + b = 1.2`. Hence predator `a = 0.67`, rabbit `b = 0.53`, SD 0.3 unchanged. Simulated with
clipping: d′ 0.652 (target 0.661), average total 1.178 (target 1.176).

**What the matched world does not match, stated so it is not mistaken for a match:** in the
control both classes smell equally strong in total (1.18 each); in the matched world the predator
is stronger (1.30 vs 1.05). That is inherent: once the ratio carries no identity, strength is the
only place identity can live — exactly as in the single-channel world (0.68 vs 0.50).

**The evidence scale is shared.** For Gaussian recipes with equal SD, the log-likelihood ratio
"predator vs rabbit" of one animal's recipe is `2.22 × (x1 − x2)` in the control,
`2.22 × (x1 − 0.6)` in the single-channel world and `1.56 × (x1 + x2 − 1.2)` in the matched world.
Every scent-ladder slope in §5 is therefore reported **per unit of evidence** (per nat of
log-likelihood ratio), which makes the three worlds comparable (clipping aside); the existing
per-unit-of-predator-likeness figures are reported beside it for continuity with the base pages.

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

- Resolved `EnvParams` (208 fields): matched vs control differ in **exactly one field**,
  `animal_property`; single-channel vs control and single-channel vs matched differ in exactly
  `animal_property` and `animal_property_std`.
- Control twin vs `basic/05` and vs `level05_body_interactions/worlds/w0000.yaml`: **empty diff**.
- The seed-42 control runs' own saved `models/config.yaml`, loaded through today's
  `load_env_params`: **empty diff** against the control twin (both agents). Today's trainer merge of
  the control twin shares every key of the saved config with the same value.
- All three worlds build, reset and step; observation width **58** (Olfaction 25 = 5 channels ×
  5-cell diamond, unchanged); both agent configs merge on the matched world (`t1none`: no
  modulation; `t16quad`: FiLM).
- **Same underlying draws:** on evaluation seed 1,000,000 the animals' channel-1 normals are the
  same in all three worlds (control 0.8512 = 0.7 + 0.3·0.504; matched 0.8212 = 0.67 + 0.3·0.504;
  single-channel 0.8512), and channel 2 uses the same normal in control and matched. The odour
  jitter key does not depend on the means.
- No critical-settings registry value changes (`sensory.vector_size` 5, `decay_power` 1.0,
  `sensor_radius` 20, `olfactory_grid_range` 1 all unchanged; entity odour vectors are not a
  registry row), so no change-log entry is written.

### 2.4 Seeds, pairing and the seed-42 control

- **Three seeds per world, one top-up.** The user chose three seeds knowing the power estimate
  (§5.3). Any 3 v 3 result that is not "established" triggers seeds 45 and 46 once.
- **What "paired" buys (less than it sounds).** `train.py` derives the network initialisation and
  the environment key stream from `PRNGKey(seed)` alone (`src/utils/init_keys.py::trainer_init_keys`,
  unchanged by commit `18e1e5f0`, golden keys for 42–44 identical), and no world changes the
  observation width. So runs of one seed and one agent start from **identical weights** and the
  same reset draws. But the very first observation already differs (the smell values), so the
  policies diverge from the first gradient step. Paired differences are reported as a secondary
  view; the decision rule is the unpaired one.
- **Seed-42 control = the existing level-05 factorial cell `w0000`** (ordinary and modulated,
  launched 2026-09-27, 10 M episodes, same launch flags). Its saved world resolves identically to
  the control twin. Code changes since its launch are logging, a dashboard feature, opt-in
  activation capture and a key-recipe refactor proven bit-identical — none touches dynamics or
  initialisation. Its **trajectory stores are re-collected** for this study with the current
  collector (Revision 1, plan-review M2): the existing ones predate the collector's switch to
  full-float32 matmuls (commit `2d54453d`) and would sit on a different numerics mode from every
  other store here. Seeds 43/44 have same-week controls and seed 42 does not; a seed-42 control
  that is an outlier against 43/44 is reported as such.

### 2.5 Confounds & Limitations

1. **Detection vs identification.** In the single-channel world, total animal odour halves, so
   animals are harder to *notice* as well as to *identify*. Detection loss pushes the rabbit
   proximity effect **down** (a close rabbit is less noticeable) while confusion pushes it **up**,
   so contrast A can cancel. The matched-strength world removes this by design for contrast B;
   contrast C measures it; the predator proximity effect and the killed-by-predator share (§5.2,
   S4) are the direct readouts.
2. **Strength carries class in both treated worlds.** Once the ratio says nothing, a rabbit's
   predator-likeness *is* its odour strength. In the control the two are orthogonal (a01 found
   both matter). §5.2 S2 adds a matched reading on the same variable in the control.
3. **Movement identifies the predator anyway.** With *identical* smells (sameProp) the agent still
   separated the classes by how they move (the predator hunts, the rabbit wanders). A null on Q1
   can therefore mean identity is recovered from movement; it is reported as that, not as
   "smell is irrelevant".
4. **A rabbit on the agent's own square is counted as "near"** (plan-review M3a). The proximity
   sweep files distance 0 into the 1–2 bin (`collect_arm_data.py`, `np.clip(drab, 1, 8) − 1`).
   Bushes block animals, so a distance-0 step is never a hiding step, and the near-bin hiding share
   is diluted by how often the agent is in contact with a rabbit (Known Bugs, OPEN: "Chasing rabbit
   stays glued to the agent after contact", `core.py:629`). A world in which the agent touches
   rabbits less gets a higher proximity effect mechanically — the predicted direction. Carried as a
   sensitivity reading (§5.2, S6).
5. **The rabbit proximity effect does not exclude predator-near steps** (plan-review M3b): steps
   with a predator also within 2 squares count, so any change in the predator response (S4) can
   bleed into P1/P2. Carried as a sensitivity reading (§5.2, S6).
6. **One world, one level.** Results speak about level 05 only.
7. **Three seeds.** See §5.3 for what that can and cannot detect.

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
| H11 | planned | 1chm · ordinary | `rppo_hv1chm_t1none_s42` | hv_single_channel_smell | prod | 42 | — | — | — | — | — |
| H12 | planned | 1chm · modulated | `rppo_hv1chm_t16quad_s42` | hv_single_channel_smell | prod | 42 | — | — | — | — | — |
| H13 | planned | 1chm · ordinary | `rppo_hv1chm_t1none_s43` | hv_single_channel_smell | prod | 43 | — | — | — | — | — |
| H14 | planned | 1chm · modulated | `rppo_hv1chm_t16quad_s43` | hv_single_channel_smell | prod | 43 | — | — | — | — | — |
| H15 | planned | 1chm · ordinary | `rppo_hv1chm_t1none_s44` | hv_single_channel_smell | prod | 44 | — | — | — | — | — |
| H16 | planned | 1chm · modulated | `rppo_hv1chm_t16quad_s44` | hv_single_channel_smell | prod | 44 | — | — | — | — | — |
| C01 | completed (not relaunched; stores re-collected) | 2ch · ordinary | `rppo_l05body_w0000_t1none_s42` | level05_body_interactions | prod | 42 | 101 | cuda:0 | 2026-09-27T05:30:50 | `dg1ry2be` | `logs/20260927_053050.log` · run dir `results/JAX_RecurrentPPO/20260927-053057_rppo_l05body_w0000_t1none_s42` |
| C02 | completed (not relaunched; stores re-collected) | 2ch · modulated | `rppo_l05body_w0000_t16quad_s42` | level05_body_interactions | prod | 42 | 106 | cuda:0 | 2026-09-27T05:30:54 | `nl1h2j21` | `logs/20260927_053055.log` · run dir `results/JAX_RecurrentPPO/20260927-053059_rppo_l05body_w0000_t16quad_s42` |

All sixteen new tags are unique and none matches an existing directory under
`results/JAX_RecurrentPPO/` (checked 2026-09-30: zero hits for `hv1ch` / `hv1chm` / `hv2ch`).
C01/C02 keep their own tags and group; the analysis finds them by run directory.

**Top-up rows (launched only if §5.3 triggers them; tags fixed now):**
`rppo_{hv1ch,hv1chm,hv2ch}_{t1none,t16quad}_s{45,46}` — for the agent and the worlds of the
contrast that needs them, same group and job type, `--seed 45` / `--seed 46`.

### 3.1 Configs to Produce

| Run | Config (env) | Config (agent) |
|---|---|---|
| H01, H03, H05 | `configs/environment/experiment/hypervigilance/single_channel_smell_l05.yaml` | `configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml` |
| H02, H04, H06 | `configs/environment/experiment/hypervigilance/single_channel_smell_l05.yaml` | `configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml` |
| H07, H09 | `configs/environment/experiment/hypervigilance/two_channel_smell_l05_control.yaml` | `…/nmngaenorm_t1none.yaml` |
| H08, H10 | `configs/environment/experiment/hypervigilance/two_channel_smell_l05_control.yaml` | `…/nmngaenorm_t16quad_ALL.yaml` |
| H11, H13, H15 | `configs/environment/experiment/hypervigilance/matched_strength_smell_l05.yaml` | `…/nmngaenorm_t1none.yaml` |
| H12, H14, H16 | `configs/environment/experiment/hypervigilance/matched_strength_smell_l05.yaml` | `…/nmngaenorm_t16quad_ALL.yaml` |
| C01, C02 | (existing) `configs/environment/experiment/level05_body_interactions/worlds/w0000.yaml` — resolves identically to the control twin | as above |
| collection | `configs/trajectory_collection/hv_single_channel_smell.yaml` — 18 stores (16 new runs + C01/C02 re-collected) into `results/trajectories_hvsmell/`; the 16 new paths are `FILL_AT_LAUNCH` placeholders the collector refuses until replaced | — |

Both treated files restate the whole `entities:` list (lists replace wholesale on merge), copied
verbatim from basic/04 with only the property lines edited. The control twin is a bare `extends:`
of basic/05, deliberately with no overrides.

**Launch command** (for `training-runner`, one per row H01–H16, wrapped by `run_command.py` /
`train_command-new.sh` per its own conventions; node and GPU chosen at launch from live state):

```
/home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
  --config configs/environment/experiment/hypervigilance/<single_channel_smell_l05 | matched_strength_smell_l05 | two_channel_smell_l05_control>.yaml \
  --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/<nmngaenorm_t1none | nmngaenorm_t16quad_ALL>.yaml \
  --episodes 10000000 --device cuda:<gpu> --log-interval 10 \
  --tag "<tag>" --wandb-name "<tag>" \
  --wandb-group "hv_single_channel_smell" --wandb-job-type "prod" \
  [--seed 43 | --seed 44]
```

Seed-42 rows (H01, H02, H11, H12) pass **no** `--seed` — seed 42 is config-owned
(`configs/train/default.yaml`), exactly as C01/C02 were launched. Rows with seed 43/44 pass
`--seed`. **Space launches at least 2 seconds apart** (env-config-reviewer note: run directories are
timestamped to the second). Launch all sixteen from the main checkout, on branch `v4.0`, in one
session; record in the diary launch row that the checkout must stay on `v4.0` for the ~18 h wave
(a branch switch mid-run changes what the checkpoint-render subprocess imports).

**Pre-flight discriminators (blocking):**

1. Every banner prints observation width **58** and a `Seed:` line equal to the row's seed
   (`train.py:1144`); `t16quad` banners print
   `Neuromodulation: ENABLED (… sites=[encoder,rnn,actor,critic] …)`, `t1none` print `DISABLED`.
2. Each run's saved `models/config.yaml` (the ground truth, not a reload of the source):
   - the **top-level `seed:` key** equals the row's seed (`train.py:612` writes `--seed` there;
     `training.seed` is the train-default 42 and is never updated, so it discriminates nothing);
   - hv1ch rows: predator `properties: [0.0, 0.7, 0.0, 0.0, 0.0]`, rabbit `[0.0, 0.5, 0.0, 0.0, 0.0]`,
     both `properties_std: [0.0, 0.3, 0.0, 0.0, 0.0]`;
   - hv1chm rows: predator `[0.0, 0.67, 0.67, 0.0, 0.0]`, rabbit `[0.0, 0.53, 0.53, 0.0, 0.0]`,
     both SD `[0.0, 0.3, 0.3, 0.0, 0.0]`;
   - hv2ch rows: predator `[0.0, 0.7, 0.5, 0.0, 0.0]`, rabbit `[0.0, 0.5, 0.7, 0.0, 0.0]`, SD
     `[0.0, 0.3, 0.3, 0.0, 0.0]`.
3. **After the last launch (ladder drift check):** load every saved `models/config.yaml` of
   H01–H16 and C01–C02 with `load_env_params` and diff field by field. Within a world the files
   must give identical `EnvParams`; across worlds only `animal_property` and `animal_property_std`
   may differ (matched vs control: `animal_property` only). Any other difference (e.g. a new
   mandatory key landing in `default.yaml` between launches) is a registered confound, reported
   with the runs it splits.

**Compute.** Ordinary ~14 h and modulated ~18 h per run on a 3090-class card (level-05 wall-clock):
8 × 14 + 8 × 18 ≈ **256 GPU-hours**, one wave on sixteen free GPUs. A full top-up (both agents, all
three worlds, seeds 45–46) would add 12 runs, ≈ 192 GPU-hours; the rule in §5.3 makes a partial
top-up the expected path. Collection: 18 × 1 M episodes, plus the time-course collection (§5.4).

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
in `results/trajectories_hvsmell/` (C01/C02 included, re-collected), all collected with the
current collector and `seed_base` 1,000,000, so episode *i* presents the same reset draws to every
run. Steps are those the agent chose (t ≥ 1); distances are read on the row the action was chosen
from. No reward-based quantity is used anywhere.

### 5.1 Primary outcomes

| ID | What it measures (plain) | Exact definition (existing code) |
|---|---|---|
| **P1** (Q1) | **Rabbit proximity effect** — how much more the agent sits in a bush when a rabbit is 1–2 squares away than when the nearest rabbit is 6+ squares away. Higher = treats the rabbit more like a threat. | `_ladder.proximity_effect(rd_bush, rd_tot)` pooled over all four start-injury quarters (`NEAR_BINS = (0, 1)`, `FAR_BINS = (5, 6, 7)`; episodes with ≥ 1 rabbit), from the `collect_arm_data.build(..., stores=...)` sweep — the same function the modulator-clues page uses. Kept as is for comparability with the base pages; its two known quirks have sensitivity readings (S6). |
| **P2** (Q2) | **Causal hypervigilance, hiding reading** — the rabbit proximity effect in the most-injured start quarter (injury 75–100) minus the least-injured (0–25). Positive = a badly wounded agent hides from a nearby rabbit more. | `a4_hypervigilance.hiding_shift(d, "rd")` = `proximity_effect(..., (3,)) − proximity_effect(..., (0,))`. |
| **P2d** (Q2, corroboration) | **Causal hypervigilance, distance reading** — share of the first 25 steps (predator-free steps only) with the nearest rabbit within 2 squares, most- minus least-injured start quarter. Negative = the wounded agent keeps the rabbit away. | `scripts/analysis/rabbit_avoidance.py`, `start.near_share_shift`. Runs unchanged on all three worlds. |
| **Survival** (headline performance) | Mean survival steps per episode on the final store; termination shares (killed by predator, starved, frozen/overheated, time limit). | Episode `length` over the 1 M store; `termination_reason`. |

Survival is the project's headline metric and is reported first in every table, but it is not a
criterion for Q1/Q2: the prediction is only that survival is **lower** in both treated worlds
(harder identification costs meals through false alarms and lives through misses).

### 5.2 Secondary outcomes (pre-registered, all reported)

| ID | What | Definition |
|---|---|---|
| **S1** (the missing piece, *e*) | **Scent × injury interaction** — does the rabbit-scent false alarm grow with the assigned wound? | Episodes with **no predator and exactly one rabbit** (11.1 % of episodes in the seed-42 control store, ≈ 110 k per run — any hiding driven by that rabbit's scent is a pure false alarm). Outcome: bush share over the first 25 chosen steps. (i) **Quarter contrast:** the slope of that share on the rabbit's scent evidence (pp per nat, §2.2) in the top start-injury quarter minus the bottom quarter. (ii) **Model:** quasi-binomial GLM (the `hiding_drivers.fit_glms` framework) with scent evidence, start injury, their product, and the M1 exogenous covariates (start nutrition, bushes, rocks, food, ambush predators, spawn distance to bush); the product term reported in pp per nat per 100 injury. Repeated on one-predator-one-rabbit episodes as a sensitivity check. Prediction: larger in both treated worlds. |
| **S2** | **Scent false alarm** (the a01 ladder) — hiding and survival as a function of the rabbit's randomised scent. | `hiding_drivers.py`: univariate rabbit scent (pp per nat and pp per SD) and model M3 (one predator + one rabbit). Plus the a01 extreme-row table (hiding, food per step, starved, killed, survival steps) for the rabbit's bottom vs top sixth of scent evidence **within each world**. Scent statistic: `x1 − x2` in the control (existing definition, unchanged), `x1` single-channel, `x1 + x2` matched. **Matched reading:** in the control, the same ladder on channel 1 alone with channel 2 as a covariate. |
| **S3** | **Aimed response** — does predator-like rabbit scent raise hiding specifically when *that rabbit* is near? | The a01 three-way split on one-predator-one-rabbit episodes (nothing near / predator near / rabbit near), rabbit-like vs predator-like groups defined on the **shared evidence scale** (log-likelihood ratio < 0 vs ≥ +0.67): control `x1 − x2 < 0` vs `≥ 0.3` (a01's thresholds, unchanged); single-channel `x1 < 0.6` vs `≥ 0.9`; matched `x1 + x2 < 1.2` vs `≥ 1.63`. Group sizes reported. |
| **S4** | **Predator response (detection readout)** — proximity effect for the predator (`pd` grids), killed-by-predator share, and the **confusion index** = rabbit proximity effect ÷ predator proximity effect. | Same sweep. "S4 unchanged" (used by the verdict map) = the predator proximity effect's difference from control is not established in either direction under §5.3 **and** its magnitude is below 3 pp. |
| **S5** | **Observational injury readings** — the same P2/P2d shifts on the injury the agent carries at that moment. | `hiding_shift(d, "rdc")`; `rabbit_avoidance.py` `current.near_share_shift`. Reported, never decisive (a currently injured agent was usually just attacked). |
| **S6** | **Sensitivity readings for the proximity sweep** (plan-review M3) | (a) the count and share of steps with a rabbit **on the agent's own square** per run, and P1/P2 recomputed with distance 0 removed from the near bin; (b) a **predator-free variant** of P1 and P2 using only steps with no predator within 2 squares (`dpred > 2`). The same §5.3 comparison is reported for both. If a primary verdict does not survive either reading, the verdict is reported with that caveat in its first sentence. |

### 5.3 The comparison, the power, and the decision rule

For each agent separately, each contrast (A, B, C; §2.1) and each outcome `Y`:
`Δ(Y) = mean(Y over the treated world's seeds) − mean(Y over the reference world's seeds)`, shown
with the per-seed values, the between-seed SD of each world, and the per-seed paired differences.

**Stage 1 — three seeds (3 v 3).** *Established* if all three treated seeds lie beyond all three
reference seeds in the predicted direction (one-sided exact permutation p = 0.05) **and** `|Δ|` is
at least the minimum effect. **Anything else** — including a result that looks like a refutation —
goes to stage 2 for that agent, contrast and outcome.

**Stage 2 — one top-up to five seeds (5 v 5, seeds 45 and 46 added in both worlds of the
contrast).** *Established* if one-sided Mann–Whitney U ≤ 4 (p < 0.05) in the predicted direction
**and** `|Δ|` ≥ the minimum effect. *Refuted* if the one-sided 95 % upper confidence bound of `Δ`
(Welch) is **below the minimum effect** — i.e. the data positively rule out an effect of the
registered size — or if U ≤ 4 holds in the **opposite** direction. *Not established* otherwise. No
further top-up. "Refuted" exists only at stage 2.

| Outcome | Predicted sign | Minimum effect |
|---|---|---|
| P1 rabbit proximity effect | + | **3 pp** |
| P2 causal injury shift, hiding | + | **2 pp** |
| P2d causal injury shift, distance | − | 1 pp (read with P2: H₁b needs P2 established and P2d's Δ of the predicted sign; P2d alone decides nothing) |
| S1 scent × injury (quarter contrast) | + | 2 pp per nat of scent evidence |
| Survival | − | reported with its 95 % interval; no threshold |

**Power, stated plainly** (Monte-Carlo, 40,000 draws per row, normal seeds, this rule; seed SDs
from the only multi-seed spreads measured on these readouts — five seeds of one configuration,
critical-settings registry 2026-09-21: ≈ 1.4 pp on the rabbit response, 1.05–2.67 pp on the
injury-driven measure):

| Outcome | true effect | seed SD | established at 3 v 3 | goes to top-up | **established overall** | wrongly refuted | not established |
|---|---|---|---|---|---|---|---|
| P1 | +3 pp (minimum) | 1.4 | 45 % | 55 % | **59 %** | 5 % | 36 % |
| P1 | +4 pp | 1.4 | 76 % | 24 % | **90 %** | < 1 % | 9 % |
| P1 | 0 (no effect) | 1.4 | < 1 % | 100 % | < 1 % (false positive) | 92 % (correctly) | 8 % |
| P2 | +2 pp (minimum) | 1.05 | 42 % | 58 % | **58 %** | 5 % | 37 % |
| P2 | +2 pp (minimum) | 1.5 | 32 % | 68 % | **51 %** | 5 % | 45 % |
| P2 | +2 pp (minimum) | 2.67 | 18 % | 82 % | **32 %** | 5 % | 63 % |
| P2 | +4 pp | 1.5 | 81 % | 19 % | **97 %** | < 1 % | 3 % |
| P2 | +4 pp | 2.67 | 44 % | 56 % | **70 %** | < 1 % | 30 % |
| P2 | 0 (no effect) | 1.5 | 3 % | 97 % | 3 % (false positive) | 59 % (correctly) | 38 % |
| P2 | 0 (no effect) | 2.67 | 5 % | 95 % | 7 % (false positive) | 27 % (correctly) | 65 % |

What this means: the design reliably detects effects about **twice** the minimum sizes; at the
minimum sizes it confirms roughly one true effect in two (one in three for P2 if seeds are as noisy
as the noisiest measured spread) and leaves the rest "not established"; it wrongly refutes a true
minimum effect about 1 time in 20. The two-look rule (3 v 3, then 5 v 5) puts the false-positive
rate per outcome at 1–7 % rather than exactly 5 %. The top-up is the **expected** path for P2 at
realistic effects. Across two agents, three contrasts and two primary outcomes there are twelve
tests; a single "established" among them is not a finding on its own (see the verdict map).

Before any hv run is read, the same sweep is run on the five `cmp10m` plain-agent seeds (§5.5) and
their between-seed SDs are frozen into §4 as the study's own yardstick. They are used to re-state
the power table, not to change the thresholds.

**Verdict map** (per agent; read on contrast B for the hypothesis, on A for the original
manipulation; "final" = after stage 2 where stage 2 ran):

| P1 (final) | P2 (final) | Reading |
|---|---|---|
| established | established | **Hypothesis supported** on that contrast: harder-to-tell-apart smell → more confusion → more injury-dependent rabbit avoidance. On contrast B this is a statement about identifiability; on A only about the single-channel manipulation. |
| established | **refuted** (at stage 2) | **Confusion without (more) hypervigilance**: the agent confuses the animals more, and an injury amplification of the registered size is ruled out. The only row that licenses "confusion alone is not sufficient". |
| established | not established | **Confusion established; its injury dependence undetermined.** No claim about hypervigilance either way. |
| refuted, **and S4 unchanged** | any | **No extra confusion** at the registered size: identity is recovered another way (movement, per sameProp) or the scent is not used. Q2 is reported but not attributed to confusion. |
| refuted or not established, **S4 changed** | any | **Not separable from detection loss** (expected mainly on contrast A): read contrasts B and C before any statement about confusion. |
| not established, S4 unchanged | any | **Undetermined.** Reported as such, with the power table. |

**Absolute sign of P2 (replaces the earlier "positive in all three seeds" clause).** Whether a
treated world shows hypervigilance *in absolute terms* is reported separately from the contrast:
the treated world's mean P2 with its one-sided 95 % lower bound. If P2's Δ is established but that
bound is not above 0, the reading is "the treated world weakens the wounded agent's boldness toward
rabbits, without producing injury-dependent avoidance of it" — a supported contrast, not
hypervigilance.

**Across the three contrasts (per agent):** B established and C not → the effect is
identifiability. A established, B not established and C established → the single-channel effect is
largely detection, not confusion. B established and A not → strength loss masks confusion in the
single-channel world (the cancellation of §2.5 item 1). The two agents are not pooled; "supported
in both agents" is the strongest statement allowed.

### 5.4 Temporal evolution (mandatory)

1. **Training curves.** Survival (`Episode/Steps`, logged every 10 episodes) for all 18 runs,
   smoothed over 1 % of training, overlaid by world per agent, with each contrast's gap per seed
   over training. Last-10 % window mean (`Episode/_window_n`-weighted) reported as the training-time
   survival.
2. **Behaviour over training.** After training, a time-course collection at the checkpoints nearest
   2 M, 4 M, 6 M and 8 M episodes (the 10 M final store is the fifth point): 50,000 episodes each,
   `seed_base` 1,000,000, float32, for all 18 runs (C01/C02 keep all 50 checkpoints). P1, P2 and S4
   are computed at each point. Question: does each contrast's gap emerge early (a perception limit)
   or late (a learned policy choice)? Descriptive only; P2 at 50 k episodes is expected to be noisy.
   The spec is written after training, when the checkpoint numbers exist (same convention as
   `configs/trajectory_collection/late_checkpoints/`).

### 5.5 Existing stores analysed alongside

| Store | What it is | How it is used |
|---|---|---|
| `results/trajectories_l05body/` — `w0000` pair | The seed-42 control runs' earlier stores, collected before the collector's full-float32 switch | **Not read by this study** (re-collected into `results/trajectories_hvsmell/`, §2.4). May be compared with the re-collection as a numerics check, nothing more. |
| `results/trajectories_basicq2_w1/`, `_w2/` (aggregates in `results/analysis/basicq2_integrated/`) — levels 03–06, both agents, one seed each | The curriculum ladder; level 06 = level 05 plus **injury-gated smell noise** (smell gets noisier the more injured the agent is) | **Descriptive context only, never pooled.** Level 06 is the reference for "confusion that grows with injury by construction": the within-wave level-06-minus-level-05 differences in P1 and P2 are shown next to this study's contrasts. If level 06 produces a positive P2 and the matched world does not, the reading is that *injury-dependent* unreliability, not unreliability as such, drives hypervigilance. Caveats: single seed; Wave-2 level 05 started every episode at body temperature 0, so it is not like-for-like with this study's level 05; Wave 1 level 03 has no ladder-style aggregate. |
| `results/trajectories_nmngae/` — `cmp10m` plain agent, seeds 42–46 | Five seeds of one configuration in an older world with the **same two-channel odour layout** (0.7/0.5 vs 0.5/0.7), but smell sampled at the agent's cell only (grid range 0, so no smell direction) and eight-channel vision that resolves identity | **Seed-noise yardstick only**: between-seed SD of P1, P2, P2d, S2 computed with the same sweep before unblinding, frozen in §4. Not a control — its vision identifies the animals, which is exactly what this study removes. |

### 5.6 Analysis tooling required (not required for launch)

The runs and the collection need nothing new. The analysis does; the user routes it through
`feature-workflow` (`senior-developer` plans → `developer` implements) before the analysis.

1. **`smell_channels()` refuses both treated configs.** Both copies
   (`scripts/analysis/hiding_drivers.py:81` and `scripts/analysis/core/env.py:73`) require one
   channel where predators exceed rabbits *and* one where rabbits exceed predators. In the
   single-channel world the second does not exist; in the matched world predators exceed rabbits on
   *both* channels. `hiding_drivers.py` and `collect_arm_data.py` (P1, P2, S2, S4) stop with
   `SystemExit` on both. Needed: a scent statistic derived from the config for all three layouts —
   difference (control), single channel, sum over the equally-signed channels (matched) — plus the
   log-likelihood-ratio scale factor of §2.2. The two-channel result must stay byte-identical (the
   `collect_arm_data` golden gate). `rabbit_avoidance.py` (P2d, S5) does not use it and runs as is.
2. **A study driver** that runs the sweep on the 18 runs, applies §5.3 (both stages), and writes the
   per-seed table; plus a run-agnostic version of the a01 aimed split (S3) — the archived
   `supplementary/falsealarm.py` hard-codes the a01 store and slots.
3. **S1** (scent × injury) is new code: episode filter, early-window share, the quarter contrast
   and the GLM product term.
4. **S6** sensitivity readings: a distance-0 count (or a separate distance-0 bin) in the proximity
   sweep, and a predator-free (`dpred > 2`) variant of the `rd` / `rdc` grids — added as new
   outputs, leaving the existing grids unchanged for the golden gate.

**Metrics requested from `src/`: none** — every measure is computable from the trajectory stores
(`animal_property_sampled`, `injury_level`, `agent_in_bush`, positions).

### 5.7 Failure-mode catalog (decided now)

| Event | Decision |
|---|---|
| NaN / value explosion / crash in a run | The **run** is bad, not the hypothesis: relaunch the same tag suffixed `_r2`, same seed. The failed run is kept in the manifest as `failed`. |
| A treated agent learns a much weaker policy (training-time survival < 50 % of the same-seed control) | The world became a different task; behaviour measures are still computed but reported under "policy regime changed", and P1/P2 are not interpreted as confusion alone. |
| Predator proximity effect changes in a treated world (S4) | The verdict map's S4 condition applies; on contrast A, read B and C before any statement about confusion. |
| P1 rises but mainly in the "nothing near" moments of S3 | Diffuse vigilance, not misidentification; Q1 is **not** counted as confusion even if P1 clears its rule. |
| A primary verdict flips under an S6 sensitivity reading | Reported with that caveat in its first sentence; the primary definition still decides. |
| Proximity-effect bins below 1,000 steps (function returns NaN) | Report as not computable for that run; no substitution of other bins. |
| Survival saturates at the 500-step limit in any world | Not expected at level 05; if it happens, survival is reported as a termination share only. |
| Effect visible at 8 M but not at 10 M (or the reverse) | The final checkpoint decides; the time course (§5.4) is reported as context. More steps are not added. |
| Seed noise swamps the effect | That is what stage 2 is for, once; then "not established" stands. |

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

Resolved differences (`EnvParams`, 208 fields compared), everything else identical:

```
                     control (2ch)          single-channel (1ch)    matched-strength (1chm)
animal_property      pred [0,0.7,0.5,0,0]   pred [0,0.7,0,0,0]      pred [0,0.67,0.67,0,0]
                     rab  [0,0.5,0.7,0,0]   rab  [0,0.5,0,0,0]      rab  [0,0.53,0.53,0,0]
animal_property_std  all  [0,0.3,0.3,0,0]   all  [0,0.3,0,0,0]      all  [0,0.3,0.3,0,0]  (= control)
```

### C. Changelog

- 2026-09-30 — designed (experiment-designer); two worlds and the collection spec written;
  validated on the live loader; nothing launched (commit `71b7480a`).
- <a id="revision-1"></a>**2026-09-30 — Revision 1, pre-launch** (experiment-designer), after
  `plan-reviewer` (NOT READY) and `env-config-reviewer` (GO WITH NOTES), and two user decisions:
  (A) add a third world with one odour for both animals and total smell strength matched to level
  05; (B) stay at three seeds, with the power estimate stated. Changes: matched-strength world
  added (§1, §2.1–2.3, six runs H11–H16, config and spec rows); contrasts A/B/C introduced, B primary
  for the hypothesis; §5.3 rewritten (two-stage rule, any non-established 3 v 3 goes to the top-up,
  "refuted" only at stage 2 and only by an upper bound below the minimum effect, power table,
  "all three seeds > 0" clause replaced by a separate absolute-sign reading); verdict map rewritten
  (row 2 only on a stage-2 refutation; the no-confusion row conditioned on S4); seed pre-flight
  check moved to top-level `seed` and the banner `Seed:` line; C01/C02 stores re-collected into
  the new root `results/trajectories_hvsmell/`; S6 sensitivity readings and two confounds added;
  clipping table extended (predator channel 1 at 1.0: 15.9 %); launches ≥ 2 s apart; wording fixes.
  Nothing launched before or during this revision.

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

## Response to plan-reviewer

*experiment-designer, 2026-09-30, Revision 1 (pre-launch). Each finding above, and where it now lives.*

| # | Response | Where |
|---|---|---|
| C1 | Accepted in full. (a) The "confusion without hypervigilance" row now fires only on a P2 **refutation at stage 2**, and refutation now needs positive evidence (the one-sided 95 % upper bound of Δ below the minimum effect, or significance in the opposite direction); P2 not established is its own row with no claim. (b) The power table is printed, recomputed for the revised rule (e.g. P2 at +2 pp: 32–58 % established overall, 5 % wrongly refuted). (c) The user chose to stay at three seeds; instead **every** 3 v 3 result that is not established — including an apparent refutation — goes to the one-time seeds-45/46 top-up. (d) The "positive in all three seeds" clause is removed from H₁b; the treated world's absolute P2 sign is a separate reading. Rows 2 and 4 no longer overlap. | §1 (plain-language power note, hypotheses), §5.3 |
| M1 | Accepted: the check reads the top-level `seed` key and the banner `Seed:` line (`train.py:1144`). | §3 pre-flight 1–2 |
| M2 | Accepted: C01/C02 are re-collected into this study's store root with the current collector; the l05body stores are not read. | §2.4, §5.5, collection spec |
| M3 | Accepted as pre-registered sensitivity readings (distance-0 count and P1/P2 without it; predator-free P1/P2), primary unchanged for comparability; both quirks added to the confound list. | §2.5 items 4–5, §5.2 S6, §5.6 item 4 |
| M4 | Accepted: the no-confusion row requires S4 unchanged (defined in S4); otherwise "not separable from detection loss". The new matched-strength world removes the detection confound by design for the hypothesis contrast (B), and contrast C measures it. | §2.1 contrasts, §2.5 item 1, §5.2 S4, §5.3 verdict map |
| L1 | Fixed: config cross-reference now §2.3; the self-contradictory row is gone with the sign clause; `cmp10m` described correctly (same two-channel layout; grid-range-0 smell and eight-channel vision); store root renamed `results/trajectories_hvsmell` (nothing had been collected). | config header, §5.5, spec |
| O1 | Adopted: launch from the main checkout on `v4.0`, noted for the diary launch row. | §3 launch notes |
| O3 | Adopted: "paired" re-described as shared initial weights and reset draws only; paired differences stay secondary. | §2.4 |
| env-config-reviewer notes | Launches spaced ≥ 2 s apart; predator channel-1 clipping at 1.0 (15.9 %) added to the clipping table. | §3, §2.2 |

The two new assumptions this revision introduces, stated for the next review: the matched world's
values rest on the designer's own 2 M-draw simulation (d′ 0.652, average strength 1.178), and the
power table rests on normal seed-to-seed variation at the registry's measured spreads.
