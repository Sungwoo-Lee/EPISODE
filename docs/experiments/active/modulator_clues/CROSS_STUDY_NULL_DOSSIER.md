---
title: "Cross-study evidence dossier: the neuromodulated agent versus the ordinary agent (September 2026)"
topic: modulator_clues
status: active
created: 2026-09-29
last_updated: 2026-09-29
phase: consolidation (no new training, no new analysis)
wandb_tag: "rppo_nmnsite_*, rppo_nmngaenorm_*, rppo_basicq2_*, rppo_bq2cover_*, rppo_l05body_*, rppo_cw_*"
---

# Cross-study evidence dossier: the modulated agent versus the ordinary agent

> **Status**: COMPLETE as a consolidation. Mode B (after the fact). No run was launched and no new
> analysis was computed. Every number below is copied from a source document or from a run's own saved
> configuration, and the source is cited next to it. Every code fact was re-read from the code at
> HEAD on branch `v4.0` on 2026-09-29.
> **Date**: 2026-09-29
> **Author**: `experiment-analyzer`
> **Audience**: the two professors re-reading the FiLM-in-RL literature for an algorithmic cause, plus
> the user and PI.
> **Related**: [[NMN_INPUT_SITE_GRID]] · [[NMN_INPUT_SITE_GRID_GAENORM]] · [[TRAINING_HEALTH_AUDIT]] ·
> [[nmn_input_site_grid_optimisation_dynamics]] · [[INJURY_DEPENDENCE_PLAN]] ·
> [[LEVEL05_BODY_INTERACTIONS]] · [[STUDY_PLAN]] (context exploration) · [[CONTINUAL_WORLDS]] ·
> [[MAY_DOUBLE_RETURN_REPLICATION]] · PI call [[2026-09-28_after_body_rules_null_and_world_screen]]

---

## 1. Question and headline (plain language)

**What this is about.** The project's agent can carry a **neuromodulator**. This is a small second
network (a 16-unit recurrent network) that reads the agent's senses at every step. It then rescales
parts of the main network: each neuron at a chosen place is multiplied by a learned gain and shifted
by a learned offset (the technique is called FiLM). The hope is that the modulated agent's behaviour
will depend on its body state more than an ordinary agent's does. For example, it would hide when
injured and ignore the same bush when healthy. Since 7 September the two agents have been compared in
about ten settings, using roughly 200 training runs. These settings include which part of the network
is rescaled, what the modulator reads, how the learning signal is computed, how the world's body rules
work, and continual-learning schedules.

**Why this document exists.** The answer has kept coming back "no measurable difference". Every
explanation so far has blamed the **world** ("the world never asked for state-dependent behaviour").
The user now suspects an **algorithmic** cause as well. This dossier puts the facts in one place, checks
them against the sources and the code, and marks which ones bear on an algorithmic explanation.

**Headline.**

- **Survival and behaviour.** No setting moved the modulated agent's survival or its state-dependent
  behaviour beyond seed noise. Almost every comparison is **one training run per agent**. So what we
  have is "no difference detected at about a 5–15-step resolution". It is not evidence that the two
  agents are equivalent.
- **Internals.** The modulator is not dead. It receives gradient throughout training. It could swing a
  neuron's gain by about 11. When its variation is replaced by its own average in a trained agent, that
  agent loses up to 180 of about 210 survival steps.
- **The central puzzle.** The trained modulated agent depends heavily on its modulator, yet it does no
  better than an ordinary agent trained from scratch.
- **Why this points at the algorithm.** The most direct reading is that the modulator is used as an
  alternative route to a function the ordinary network learns anyway. Nothing in the objective or the
  optimiser gives it a job only it can do.

**Three corrections to the brief** (details in §5):

- Not every run's modulator reads all sensors. The four site-by-input grids trained **20 body-only
  modulators**.
- The 47–180-step freeze cost covers only the arms whose modulator reads every sensor. At some sites it
  is 0 or even positive.
- "Dormancy" was **never measured**.

---

## 2. Method of this consolidation

- **Sources read.** Every document named in the brief, the extended-olfaction comparison page next to
  the grid documents, the May continual probe, and the `nmn_diagnosis` folder of the LLM Wiki.
  Numbers are quoted with their section. Where two sources disagree, both are given.
- **Code checked, not re-derived** (HEAD `v4.0`, 2026-09-29):
  - the rPPO optimiser construction in `train.py`;
  - the loss in `src/models/recurrent_ppo_trainer.py`;
  - the modulated forward pass in `src/models/recurrent_ppo_network.py`;
  - the modulator module in `src/models/neuromodulator.py`.
- **Saved configs checked**, from each run's own trainer-written `models/config.yaml`:
  - the Wave-2 level-05 modulated run;
  - the body-rules factorial's no-rules pair;
  - the May-replication modulated seed 42;
  - one body-only grid cell.
- **What this dossier does not do.** It does not re-analyse any run, and it does not rank hypotheses.
  Wherever a fact is inferred rather than read, it says so.
- **Working notes**: `tmp/20260929_1700_cross_study_null_dossier.md`.

---

## 3. Study table

**Notation.** "Mod − ord" means modulated minus ordinary (unmodulated). "Seed noise" is the best
available yardstick for how much the same number moves when training is simply repeated.

**Every modulated arm is the same family of agent.** It uses:

- FiLM with one gain and one offset per neuron, from a 16-unit recurrent modulator;
- recurrent PPO with a 128-unit GRU;
- policy temperature switched off;
- a plain GRU cell in the memory (the "activation" mechanism).

The exceptions are the rows marked *May*.

| # | Study (dates) | What varied | Runs | Seeds per cell | Measure | Mod − ord effect | Noise scale | Verdict (source) |
|---|---|---|---|---|---|---|---|---|
| 1 | **Site × input grid, MC returns** (trained 7 Sep) — 10 × 10 jump-attack world, 27-number observation | Where the modulator writes (encoder / memory output / actor hidden / critic hidden / all four) × what it reads (all 27 senses / 2 body channels / 19 outside-world channels). Plus 1 control | 16 | **1** (seed 42 for all) | Survival, mean over the final 1 M episodes (training rolling mean) | Mean **+1.7** steps (sd 2.2; range −1.4 to +6.1; 12 of 15 cells above control). Control 164.46 | 5 earlier seeds of the same control: range 4.5 steps (sd 1.9). Pre-registered bands: under 15 = "no evidence", 15–30 = "flagged", over 30 = "candidate" | **No cell reaches 15 steps: no evidence.** The design doc's Results section (§7) was **never filled in**. Numbers come from [[TRAINING_HEALTH_AUDIT]] §4.1 and the olfaction comparison page |
| 2 | **Same grid, GAE_NORM returns** (7–8 Sep) | As row 1. Only the estimator differs | 16 | **1** (42) | As row 1 | Mean **−0.2** (sd 1.6; range −3.0 to +2.5; 5 of 15 above). Control 170.62 | 5 earlier seeds: range 1.3 (sd 0.52) | Null. The estimator's effect has the same sign in all 16 cells (+4.3 ± 1.6), with no site- or slice-specific interaction ([[TRAINING_HEALTH_AUDIT]] §5.8) |
| 3 | **Same grid under a directional sense of smell** (MC and GAE, 47-number observation; around 14–16 Sep) | As rows 1–2, with a wider sense of smell | 32 | **1**. A single control run per grid | Three behaviour measures: injury → hiding over the first 25 steps; the same read over the whole episode and against carried injury; hypervigilance (rabbit shift minus predator shift) | In **12 of 12** grid × measure comparisons (all four grids), the control sits **inside** the spread of the 15 modulated cells | In the two 27-number grids, 5 control seeds span "most of" the modulated spread (olfaction comparison page §07). The 47-number grids have **no** seed band | Null, and **not pre-registered** (olfaction comparison page §07) |
| 4 | **Look inside the modulator** (9–16 Sep, no training) | Offline analyses of the 30 modulated agents from rows 1–2 | 0 new | Within-agent | Reachable gain swing; contextual fraction; paired freeze-at-mean test | Not a mod − ord comparison. See §5.4 | Paired within-agent: 128 episodes, sign tests | The modulator has room to act, varies little, and the variation is used ([[repr_analysis]] page) |
| 5 | **Curriculum levels, Wave 1** (21 Sep) and **Wave 2 / cover heals 25× faster** (22 Sep) | 7 curriculum levels (00–06) × {ordinary, modulator writing to all four sites and reading all senses} | 14 + 14 | **1** (42) | Survival over 1 M replayed episodes; about 9 behaviour gaps; scene tests at 10 starting injuries; changing only the injury the agent feels | Survival gap per world-level cell (blind, W1 04/05/06, W2 04/05/06): **+6.8, +3.9, −3.1, −2.5, −0.9, +0.8, +2.4**. Behaviour gaps within about ±5 percentage points, with mixed signs | Only the spread across a single run's checkpoints (newest 20). **Seed noise is not measured** | "Leads, not effects". Level 05 is the only level where the modulated agent's steeper injury → hiding slope passes the rule fixed before the data, in both windows (11 of 12 scene versions larger). At levels 04–05 its injury dependence is 2–4× steadier across checkpoints. In the training world the two agents' injury curves nearly coincide (modulator clues page §04, §05, §14, §A13) |
| 6 | **Level-05 body-rules factorial** (26–28 Sep) | 4 on/off body rules (healing slows when hungry, healing costs food, being cold or hot costs food, scarcer food) = 16 worlds × 2 agents | 32 | **1** (42). All 16 ordinary runs share one initialisation, and all 16 modulated runs share another | M1: nutrition dependence of injury-driven hiding (primary). M3: injury dependence of eating. Combination gain. Survival | Survival **+3.6** (range +1.9 to +5.8; 16 of 16 positive; appears in the third tenth of training). Behaviour: **none of 15 factorial effects on the gap exceeds even the single-effect margin** (for M1, true injury: margin 0.047, simultaneous margin 0.095; largest effect +0.039) | Single-gap seed yardstick about 2.1 steps (from pilot seeds with sd about 1.5). Lenth's pseudo-standard-error margins | **Null screen.** The survival lead is **not** licensed as a modulator effect: initialisation, capacity and seed are confounded. M1's zero point turned out to be uncalibrated (§7.10) ([[LEVEL05_BODY_INTERACTIONS]] §7) |
| 7 | **Hidden-danger reanalysis** (context exploration, Part 1; 27 Sep) | The Wave-2 level-05 pair from row 5, read on the number of hidden ambushers (2–5 vs 9–12) | 0 new | **1** | Change in cover share between high- and low-ambusher episodes, matched on injury × food × time in episode | Paired difference (mod gap − ord gap): **−0.11 pp** [−0.16, −0.05] | 95% bootstrap over episodes (within-run only) | Neither agent adapts (both gaps under 1 pp against a 5 pp threshold). The PI later noted that the ambusher count carries nothing an agent could usefully infer ([[STUDY_PLAN]] "Part 1"; PI call 09-28 §1) |
| 8 | **Continual-worlds pilots** (28 Sep, in progress) | The row-6 no-rules pair, switched Home → each new world | 2 per world (12 + 6 re-pilots + 2 scouts with the modulator) | **1** (42) | Survival over the last 200 k episodes | Famine −0.5; **Winter −37.2** (modulated worse: 160.8 vs 198.0; it peaked at 175.7, then slid 8.5%); Danger-A +8.4; Fog-B +3.7; worlds failed by both agents within ±3 | None measured | Descriptive; not an analysis. "Not evidence about the modulator" ([[CONTINUAL_WORLDS]] §3.7.1) |
| 9 | **May double-return replication** (launched 29 Sep 15:38) | Hunting ↔ harmless predator schedule, trained from scratch | 6 | **3** (42, 43, 44) | Survival on the hunter's two returns | **No data yet** | Standard-error floor 3.6 steps, so a difference smaller than about 7 steps (about 10 for stage-to-stage changes) cannot count | Pending ([[MAY_DOUBLE_RETURN_REPLICATION]] §5.2) |
| *May* | May continual probe (Round 2, 11–12 May). *Different agent*: FiLM with a policy-temperature head, MC returns, gate-bias memory | Same schedule as row 9 | 2 | **1** | Survival on the returns | **+106.9, +132.5** | ±4.4-step seed noise from a separate rerun | The only large positive result. Unreplicated (NMN_CONTINUAL_DOUBLE_RETURN_PROBE §5.5) |
| *May* | Noise-heterogeneity sweep (8 May). *Different agent* (as above) | 5 noise profiles × {FiLM, ordinary} | 10 | **1** | Survival | FiLM **5–13 steps worse** in every profile | ±4.4 | Negative (wiki `20260508_2003_nmn_heterogeneity_sweep_verdict_film_worse`) |

**Seed count, stated plainly.** Rows 1–8 hold **about 200 training runs**. Apart from the reference
seeds borrowed for rows 1–2, **every modulated-versus-ordinary contrast in them is one run against one
run**. In rows 1–3 and 6, every cell also shares seed 42. That makes the cells correlated draws, not
independent replicates: 16 worlds in row 6 are one comparison seen 16 times, and one lucky or unlucky
seed is common to every cell of a grid. Row 9 is the first modulated-versus-ordinary comparison this
month with three seeds per agent.

---

## 4. What the null is, precisely

| Level | What was measured | Result | "No difference detected" or "evidence of equivalence"? |
|---|---|---|---|
| **Performance** (survival steps) | Rows 1, 2, 5, 6 | Gaps of −3 to +7 steps against controls of about 165–250 steps. The only consistently signed gap is +3.6 (row 6), from one initialisation pair | **Not detected.** Stated resolution: 15 steps (rows 1–2, pre-registered); about 2.1 steps per gap (row 6, one seed); about 7 steps (row 9, not yet read). Rows 1–2 carry an honest equivalence statement at their stated resolution: no difference ≥ 15 steps in any of 30 cells. That is a bound at n = 1 per cell, not an equivalence test |
| **Behaviour: state dependence in the training world** | Injury → hiding dose-response; nutrition × injury contrasts; hypervigilance; hidden-danger adaptation (rows 1–3, 5–7) | Control inside the modulated spread (rows 1–3). Factorial gap effects all inside the margin (row 6). Training-world injury curves coincide (row 5). Neither agent adapts to the hidden danger (row 7) | **Not detected.** The grids registered a seed band of **0.63 pp** on the headline hiding statistic, against a within-run interval of ±0.10 pp. So a within-run "significant" +0.3 pp would still sit inside the null ([[NMN_INPUT_SITE_GRID]] §2.3). Row 6's floor is about 0.047 on M1 (the single-effect margin), and "a null here does not exclude a gap effect smaller than about [that]" (§7.8 flag 5). M1's zero point is uncalibrated (§7.10) |
| **Behaviour: in controlled scenes and when only the felt injury is changed** (row 5) | 10 starting injuries × 3 scenes × 50 checkpoints; setting the felt-injury input by hand | **Leads.** Level 05: steeper injury dependence (passes the rule). Levels 04–05: 2–4× steadier across checkpoints. The modulated agent over-reacts to a one-step jump in felt injury (+27–29 pp chance of Rest at levels 03 and 05, against −1 to +4 for the ordinary agent). Level 06 reverses | Leads only. The spreads are **within one run's checkpoints**, and the page says so ("nothing here can measure" run-to-run spread). Both agents act on the felt injury itself: injury dependence exists **without** the modulator (modulator clues page §14) |
| **Internals** | Row 4, plus the training-health audit | Gradient present; capacity present; about 15% contextual; the freeze costs up to 180 steps | Not a null. See §5.4–§5.5 |

**Two points that bear on how to read the null.**

1. **The ordinary agent already shows the target behaviour in most worlds that reward it** (rows 5 and
   6: hurt → hide, leave cover once healed, act on the felt signal). What remains untested is whether
   the modulator *adds* state dependence the plain network cannot reach. That was never tested in a
   world where the plain network provably fails, and row 7's world had nothing inferable.
2. **The row-1 control does *not* show the target behaviour in the base world.** Starting badly injured
   changes cover entry by −0.53 to +0.10 pp across 5 seeds, while resting rises 18–21 pp
   ([[NMN_INPUT_SITE_GRID]] §1.1). So in the grids the question was whether the modulator *creates* the
   behaviour, and it did not.

---

## 5. Algorithm-relevant facts (verified)

Each fact carries: **Status** (confirmed / corrected / refined relative to the brief), **Source**, and
**Bearing** (why it matters for an algorithmic explanation).

### 5.1 What the modulator reads

- **Confirmed for every modulated run outside the grids; corrected for the grids.**
  - **Reads everything (all sensors).** Every modulated run in rows 5, 6, 8 and 9 reads the whole
    observation. Checked in the saved configs:
    - Wave-2 level-05 modulated run: `input_sensors: all`;
    - body-rules no-rules modulated run: `all`;
    - May replication seed 42: `all`.

    This is what the 2026-09-23 plan-reviewer note found (diary 2026-09-23 23:35; review
    `docs/reviews/plan_modulator_clues_page.md`).
  - **Reads a slice.** The four site-by-input grids (rows 1–3; 60 modulated runs) trained **20
    body-only** modulators (satiation + felt injury, 2 numbers) and **20 outside-world-only** modulators
    (19 numbers in the 27-number grids). A saved config was checked: the MC four-site body-only cell has
    `input_sensors: [Satiation, Interoceptive Nociception]`.
  - **Not tested.** No body-only modulator was ever trained in a world with thermal state (levels
    05/06) or in the continual schedules.
- **Same scaling as the trunk.** The slice is taken *after* the network's symlog compression, so the
  modulator sees exactly what the trunk sees (`recurrent_ppo_network.py:500-516`).
- **The modulator's input is the raw observation.** Its GRU reads the symlog observation directly, not
  the trunk's encoder output. Its hidden state (16 units) is reset at episode end together with the
  trunk's.
- **Bearing.**
  - In every all-sensors run, the modulator is **self-conditioned**: it reads the same observation as the
    pathway it modulates. A 2026-09-01 literature review in this project records "active negative
    evidence" for self-conditioning. HyperMARL's "w/o GD" ablation "is our configuration and degrades
    on both environments" (wiki `20260901_1528_film_literature_verdict_grouping_and_self_conditioning`).
  - The main network also receives both body channels in every arm. So even a body-only modulator gives
    the policy no information it lacks; it can only change *how* that information is used
    ([[NMN_INPUT_SITE_GRID]] §1.4, H5-add).

### 5.2 The FiLM parameterisation

- **Confirmed, with three refinements.**
- **Gain formula.** For each unit `i` at each site, the gain is `γ_i = g_i + b_i + Σ_j K_ji h_j`, where:
  - `h` is the modulator's 16-unit GRU state, which lies in [−1, 1];
  - `b_i` is the gain head's bias, **initialised to 1.0** for FiLM whatever `percept_bias_init` says
    (that key's 3.0 is inert);
  - `g_i` is a separate learned per-unit baseline, initialised to 0;
  - `K` is the head weight matrix.

  The offset has its own head, bias (init 0) and baseline (init 0) (`neuromodulator.py:142-217`).
- **The baseline is redundant here.** With one gain per unit (`grouping_size: 1`), `b` and `g` get
  identical gradients. Their difference stays 1.0 to float32 rounding over 10 M episodes (largest
  deviation 4.1e-5); the offset pair stays bit-identical ([[repr_analysis]] §01).
- **Refinement 1: identity at step 0 holds only on average.** The head weight matrices use the default
  random initialisation, not zero. At the first logged point each unit's gain is 1.0 ± 0.29–0.39 and
  its offset 0 ± 0.27–0.35 ([[TRAINING_HEALTH_AUDIT]] §8.1).
- **Refinement 2: gain and offset are unbounded.** They are linear, with no sigmoid, tanh or clip. The
  `memory_clip: [-2, 2]` key is read only by the legacy gate-bias memory path and is **inert** in every
  run here (`neuromodulator.py:262-266`).
- **Refinement 3: where it acts.** Four sites (`recurrent_ppo_network.py:517-563`,
  `forward_with_modulation` at line 205):
  - **Encoder**, two stages: after LayerNorm, before ReLU. **At stage 1 (per-sensor), one 128-long
    gain vector is broadcast across all sensors' encodings.** The modulator can re-weight feature
    index *j* but cannot up-weight one sense against another. Stage 2 is the fusion hub.
  - **Memory**: the GRU's *emitted* output only (`x_h ← γ⊙x_h + β`, no nonlinearity). The carried state
    is untouched.
  - **Actor**: the single 128-unit hidden layer, before ReLU.
  - **Critic**: the single 128-unit hidden layer, before ReLU.

  The actor and critic hidden layers read the same (possibly modulated) memory output. Temperature
  modulation is off in every September run. The May agents had it on.
- **Bearing.**
  - The constant part (`g + b + K·E[h]`) is a **gauge quantity**: the modulated layer's own affine
    parameters can absorb it exactly. Only the part that varies over time is identifiable
    ([[nmn_input_site_grid_optimisation_dynamics]] §2.2).
  - The parameterisation has no term that favours the varying part over the constant part.

### 5.3 How the optimiser treats the modulator compared with the main network

- **Confirmed: identical treatment. There is no modulator-specific learning rate, clip, schedule or
  regulariser.**
- **One optimiser for everything.** One `nnx.Optimizer` over every `nnx.Param` of the whole model:
  trunk, both heads **and the modulator** (a sub-module of the model). The chain is
  `optax.clip_by_global_norm(max_grad_norm)` **then** `optax.adam(lr)` (`train.py:1253-1262`).
  - `lr` is `agent.lr_actor` = **5e-4**.
  - No learning-rate schedule, no warm-up, no weight decay, no parameter groups.
  - Adam's own defaults apply.
- **The critic learning rate is dead.** `lr_critic` has **no consumer** anywhere in `train.py`,
  `src/models/` or `src/utils/` (re-checked by grep 2026-09-29, and consistent with wiki
  `20260901_1528_lr_critic_dead_across_all_rppo_per_file_migration`). **Correction to
  [[MAY_DOUBLE_RETURN_REPLICATION]] §3.4:** its listed May-vs-today difference "`lr_critic` 0.0001 →
  0.0005" is almost certainly inert. It is inert under today's trainer. It was not re-verified at May's
  commit.
- **No modulator learning rate.** `lr_modulator` does not exist anywhere.
- **Clipping is global.** `max_grad_norm` = 0.5, applied to the whole-model gradient norm, so a spike in
  either the trunk or the modulator throttles both.
- **One loss trains the modulator end to end** (`recurrent_ppo_trainer.py:173-208`):
  `policy + vf_coef × ½·MSE + ent_coef × (−entropy)`.
  - `vf_coef` = 0.5, `ent_coef` = **0.01** (fixed, no annealing), `eps_clip` = 0.1.
  - 4 epochs per rollout, sequence length 128, γ = 0.95, λ = 0.95.
  - There is no stop-gradient anywhere, so the **value loss trains the modulator** as well as the policy
    loss. This holds even for actor-only or encoder-only sites, because the modulator's GRU is shared.
  - There is no auxiliary loss on the modulator: no reconstruction, no prediction of body state, no
    penalty on its constant part.
- **Advantage.** In both return modes the advantage is the critic's residual against a z-scored target
  ([[nmn_input_site_grid_optimisation_dynamics]] §1.3). The same scalar weights the policy and value
  terms.
- **Bearing.**
  - Under Adam, parameters of small magnitude get large relative steps. As the mean gain falls to about
    0.2–0.5, the gain parameters become the highest-relative-learning-rate part of the layer (critique
    §2.2c).
  - With no weight decay, the constant (gauge) part drifts indefinitely. The action-head and value-head
    offsets were still sliding at 10 M episodes in both grids (audit §11).
  - The modulator's share of the squared gradient norm rises from about 15–45% early to **40–75% late**
    in the encoder and four-site arms. By 10 M episodes it is the part of the network where the loss is
    steepest (critique §4.1).

### 5.4 Representation-analysis findings

Status: **confirmed, with two corrections and one scope limit.** All from [[repr_analysis]]; 30
modulated agents from rows 1–2.

- **Reachable gain swing is about 11.** Confirmed.
  - The mean over units is `2·Σ|K_ji|`, with all-sites mean **10.95 ± 1.39**. It is exact, because the
    GRU state is bounded.
  - Minimum 7.95. The maximum over units is about twice the mean (22.33).
  - Identical across input slices (11.05 / 10.92 / 10.87) and across estimators (MC 10.66, GAE_NORM
    11.23).
  - Grows 1.64× over training in all 60 agent-site measurements; none contracts.
  - Reading: **capacity is not the bottleneck.**
- **Contextual fraction is about 15%.** Confirmed.
  - It is the share of gain variance that is *over time* rather than *between units*: **0.148 ± 0.085**
    overall.
  - Everything-reading 0.206; **body-only 0.073**; world-only 0.166.
  - Body-only modulators are **2–4× less contextual at every site, 15 of 15**. At the encoder, 97% of
    their variation is fixed.
  - Other measurements agree: 0.08–0.15 median across all four grids (olfaction comparison page §05);
    8–31% in the Wave 1 / Wave 2 agents (modulator clues page §A7).
  - The remaining about 85% is a fixed per-unit re-tuning that is absorbable into the next layer's
    weights, as the brief says.
  - Additional structure: about a third of units at every site take both signs during an episode.
    77% of gains sit below 1. Unlike Perez et al. 2018, there is no spike of gains at exactly 0.
- **The freeze-at-mean cost. Corrected: the 47–180 range is not the full picture.**

  *How the test works.* The varying part is replaced by the unit's own time-average. The gain and the
  offset are frozen separately and together, over 128 paired greedy episodes. **This was run only on the
  everything-reading slice** (10 arms = 5 sites × 2 estimators). Live survival in these replays is
  about 190–220 steps.

  Mean paired change in survival steps, MC / GAE_NORM:

  | Site frozen | Gain frozen | Offset frozen |
  |---|---|---|
  | encoder | −122.8 / −47.2 | −107.7 / −130.0 |
  | memory | **+11.0** / −4.2 | −147.5 / −76.0 |
  | actor | −123.2 / −121.3 | −14.0 / −4.2 |
  | critic | **0.0 / 0.0** | 0.0 / 0.0 |
  | all four | −177.0 / −48.5 | −173.4 / −80.2 |

  *Notes on the table:*
  - The critic's 0.0 is a positive control. The policy is greedy and the critic does not act, so freezing
    it must change nothing.
  - Across the modulated arms, freezing the **gain** averages **−63.3 ± 67.5** (between-arm sd),
    freezing the offset **−73.3 ± 65.9**, and freezing both **−132.9 ± 71.3**.
  - "Not every effect is significant: the largest sign-test p-value among the gain-freeze arms is
    0.788."
  - The costs are lopsided. At the actor, the typical episode loses 10 steps while the worst 5% lose
    480 (see the note below).
  - The page's worked agent (MC, actor only) goes 213.5 → 90.3 with the gain frozen and → 33.6 with
    both frozen (−180).
  - The correct statement: **large (47–180 step) costs at the encoder, at the actor gain, at the memory
    offset, and in the all-four arm; near zero at the actor offset and memory gain (one +11
    improvement); zero at the critic by construction.**

  *Note on the 480 figure:* the page reports it as a loss, but survival is capped at 500 steps and live
  survival is about 210 steps on average. Read it as "the worst episodes lose nearly the whole episode".
  The exact quantile definition is not given on the page and was not re-derived here.
- **MC-trained agents lean on the modulator about 2× more.** Confirmed for the gain; about 1.5× for the
  offset.
  - Gain freeze: −82.4 ± 83.3 (MC) against −44.2 ± 48.8 (GAE_NORM). Offset: −88.5 against −58.1.
  - The modulation signal itself does not differ by estimator (contextual fraction 0.146 vs 0.151).
  - So the difference is in how much the *downstream* network has come to depend on the signal, not in
    what the modulator emits.
- **Scope limit.** The freeze test was never run on body-only or world-only modulators. It is listed as
  "highest value per unit of effort" and still open (repr page §07).
- **Scope limit.** The current code **cannot load the 32 grid agents** (a later feature made a config
  key mandatory). The analyses ran on an isolated pinned copy of the code (repr page §07). Any re-analysis
  meets the same wall.

### 5.5 Training-health findings (rows 1–2, 32 runs; [[TRAINING_HEALTH_AUDIT]], critique)

- **Healthy.**
  - Zero NaN or infinity; zero recompiles; no stalls.
  - All 32 runs are still very slightly improving at 10 M episodes (+0.4 to +1.1 steps per M in the
    second half, GAE_NORM).
  - Loss channels are indistinguishable from the control. Entropy is −0.60 to −0.70 against the
    control's −0.66, so there is no premature collapse.
- **The modulator gradient never vanishes.**
  - Minimum 0.0071 (MC) and 0.0076 (GAE_NORM), about 7× the "vanishing" threshold. Both minima are in
    the actor-site, body-only arm.
  - Under MC it *grows* over training in 14 of 15 arms; under GAE_NORM it is flat. That difference is
    **unexplained**: the critic's residual scale accounts for at most 6% of it.
  - The action head is the one site where it declines in both grids.
- **Clipping.**
  - Mean total gradient norm is about half the 0.5 ceiling in every arm, and the modulated arms stay in
    the same regime as the control.
  - The critique's re-reading of the audit's softer measure: the actor, everything-reading arm has the
    ceiling touched **within** 83–87% of logging windows, against 4.5% for body-only. "A real difference
    in optimiser regime": intermittent clipping acts like an update-dependent learning rate (critique
    §6.1).
- **Gauge drift.**
  - Mean gains end at **0.16–0.91** depending on site, input slice and estimator. Mean offsets end
    negative, down to **−1.83** (actor, everything-reading, MC).
  - Encoder gains follow a U-shape. The action-head gain keeps falling. **The action-head and value-head
    offsets have not converged at 10 M episodes, in both grids.**
  - The critique classifies this as normal for FiLM under Adam without weight decay (a flat direction),
    not as a budget problem.
- **Dormancy was NOT measured. This is an open item, not a finding.** The one "genuine open concern"
  (critique §7):
  - gain around 0.16–0.2 combined with offset around −1.0 **in front of a ReLU** could silence units
    permanently;
  - the most extreme pairing is value head, GAE_NORM, four-site body-only: gain 0.160, offset −1.050;
  - a silenced unit is an absorbing state, because it gets no gradient and can be revived only by drift
    in the shared modulator state.

  Requested twice (audit §9 item 1; critique §8 items 1 and 4); no result exists. The brief's phrase
  "Training-health findings (dormancy, …)" should read "dormancy suspected, never measured".
- **Unmatched capacity.** The modulated agents have more parameters than the control (modulator GRU plus
  heads). No capacity-matched ordinary agent exists in any study (modulator clues page §14; factorial
  §7.0).
- **Provenance.** The `git_dirty` flag recorded "unknown" in 31 of 32 grid runs. Judged harmless by a
  recorded evidence review ([[NMN_INPUT_SITE_GRID]] launch-time ruling).

---

## 6. The central puzzle

> **Freezing the modulator's moment-to-moment variation at its own average costs a trained modulated
> agent tens to about 180 of its roughly 210 survival steps. Yet a modulated agent trained end to end
> survives and behaves no differently from an ordinary agent trained from scratch (within about 5–15
> steps, one seed per cell).**

**What the combination implies.**

1. **The modulator is wired in and used, not dead.** Gradient, capacity and a large freeze cost together
   rule out "disconnected" and "decorative".
2. **Within-agent dependence is not between-agent advantage.**
   - Freezing is a lesion applied *after* training. The downstream weights co-adapted to a varying
     signal, so removing it takes the network off its training distribution.
   - The freeze counterfactual is "this network minus its varying part". The comparison that returned
     the null is "a network trained with the modulator versus one trained without it". Only the second
     asks whether modulation helps, and it came back null.
3. **The simplest account consistent with both is redundancy.**
   - The trained modulated agent computes, partly through the modulator, a function the ordinary network
     reaches through its own weights. The modulator reads the same observation, and its multiplicative
     interaction is something a GRU plus MLP of this size can already approximate.
   - Training therefore distributes the solution across whichever pathway is available. Nothing in the
     loss or optimiser (§5.3) rewards putting context-dependence specifically in the modulator.
   - **This is an inference, not a measured result.**
4. **How much the network depends on the modulator is set partly by the training recipe, not by what the
   modulator emits.** MC-trained agents lean on it about 2× more (gain), while the signal is the same
   (contextual fraction 0.146 vs 0.151).

**What the combination does not imply.**

- **That the varying 15% tracks body state.** The freeze test was run only on everything-reading
  modulators, and the variation could follow external stimuli. The regression of the gain on satiation
  and felt injury was proposed (critique §3.2) but not computed. The only related evidence: when the
  felt injury is set by hand, the mean gain changes at some sites, by about 0.4 at the level-05 encoder
  (modulator clues page §10).
- **That the modulator hurts.** "Every frozen agent ends up worse than the agents trained without a
  modulator at all" is noted on the repr page as a cross-agent comparison at one seed, "named, not
  concluded".
- **That a lesion of the ordinary agent would be harmless.** No matched lesion (for example, clamping
  the same number of the ordinary agent's hidden units to their mean) was run. **Without it, "load-bearing"
  cannot be told apart from the generic fragility of any trained pathway.** This is the missing control
  that most directly decides point 3.
- **That the null is established at small effect sizes** (see §4).

---

## 7. What has been ruled out, and on what evidence

| Candidate explanation | Status | Evidence |
|---|---|---|
| Modulator disconnected, or gradient vanishing | **Ruled out** (all 30 grid runs) | Audit §4.2 / §5.2: minimum 0.0071, never below threshold |
| Numerical instability, gain blow-up, divergence | **Ruled out** | Zero NaN or infinity in 32 runs; the one 1030-magnitude gradient spike (MC) was absorbed by the clip and not repeated in the GAE_NORM grid (audit §4.8, §11) |
| Modulated arms stuck in the clip regime | **Ruled out as a regime change**; intermittent-clipping difference noted | Audit §4.5; critique §6.1 |
| Not enough modulation capacity | **Ruled out** | Swing about 11, growing 1.6× over training, the same for every input slice (repr §01) |
| Modulator's output unused ("decorative") | **Ruled out for everything-reading arms**; **untested for body-only and world-only** | Freeze test (repr §03) |
| Wrong write site | **Screened, null at n = 1** | 5 sites × 4 grids; no cell reaches 15 steps; control inside spread in 12 of 12 (rows 1–3) |
| Wrong input (everything vs body-only vs world-only) | **Screened, null at n = 1** | Rows 1–3. Body-only is the *least* contextual (repr §02) |
| Return estimator (MC vs GAE_NORM) | **Screened, null** | Rows 1–2. The estimator's effect is uniform across cells (audit §5.8) |
| Sense of smell too coarse (27 vs 47 numbers) | **Screened, null** | Row 3. The 47-number MC grid is the least contextual |
| Gate-bias memory initialisation confound (the pre-September modulated runs) | **Removed by design** | Memory mechanism set to "activation"; the control's parameter tree and forward pass are bit-identical ([[NMN_INPUT_SITE_GRID]] §2.2, launch ruling) |
| Temperature channel confounding the sites | **Removed by design** | `temperature.enabled: false` in every September run |
| Critic learning rate misconfigured | **Not a factor** | `lr_critic` has no consumer; every parameter trains at 5e-4 (§5.3) |
| The world does not require several body states at once (body rules) | **Tested, null** | Row 6: the rules change behaviour strongly, but equally for both agents |
| Healing incentive too weak | **Tested** | Wave 1 → Wave 2 (cover heals 25×) moved both agents' hiding far more than the modulator did (modulator clues page §A13) |
| Behaviour instrument too coarse | **Partly addressed** | Controlled scenes, felt-injury manipulation and 1 M-episode stores all tried; they yield leads, not effects (row 5) |
| Entropy collapse or premature determinism | **Not observed** | Entropy matches the control (audit §4.1) |

**Not ruled out: open, and algorithm-relevant.**

- **Unit dormancy** created by gain × offset before a ReLU. Never measured.
- **Missing lesion control on the ordinary agent** (§6). Without it the freeze result cannot be read as
  "specific to modulation".
- **Self-conditioning.** Every everything-reading modulator sees the trunk's input (§5.1). The body-only
  arms are not a clean fix, because the trunk still sees the body channels.
- **No pressure toward the varying part.**
  - There is no auxiliary objective, no penalty on the constant part, and no zero-initialised head.
  - The constant part is a free gauge direction that Adam drifts along with no weight decay (§5.2–§5.3).
  - "A design that cannot collapse into a fixed rescaling — a hypernetwork, or a penalty on the constant
    part" was proposed and never tried (modulator clues page §A13).
- **Shared optimiser, learning rate and global clip for the modulator and the trunk.** There is no
  separate timescale. This has never been varied.
- **The value loss trains the shared modulator.** There is no stop-gradient (§5.3), and it has never
  been varied.
- **Stage-1 encoder gain shared across senses.** It cannot re-weight one sense against another (§5.2).
  This has never been varied.
- **Seeds.** Everything except row 9 is one seed per cell. The 3–6-step survival gaps (rows 1 and 6) and
  the steadiness lead (row 5) are unresolved, not refuted.
- **Hidden-context worlds** (short smell range). Candidate worlds are screened with the ordinary agent
  only, and there is **no modulator comparison yet** (PI call 09-28, still pending the user's decision).
- **The May positive.** A different agent (temperature head, MC, gate-bias memory), one seed. Being
  replicated with today's agent (row 9); not yet read.

---

## 8. Corrections to the brief (summary)

| Brief said | Source says | Where |
|---|---|---|
| The 09-23 note: a saved config showed the modulator reads all sensors, not internal-only | **True for the Wave 1 / Wave 2 pair and for everything since.** But 20 body-only modulators were trained in the September grids | §5.1 |
| "Freezing the modulation at its mean costs 47–180 survival steps" | That range describes the large-cost cells of **everything-reading arms only**. Costs range from **+11 (an improvement) through ≈0** (actor offset, memory gain; critic 0 by construction) to −180. Between-arm mean for the gain: −63 ± 68. The largest gain-freeze sign-test p is 0.79 | §5.4 |
| "MC-trained agents lean on it ~2× more" | **2× for the gain** (−82 vs −44); **about 1.5× for the offset** (−89 vs −58) | §5.4 |
| Training-health findings include "dormancy" | **Dormancy was never measured.** It is the critique's one open concern and the audit's top-priority requested metric | §5.5 |
| "Head bias initialised to 1; a redundant per-unit baseline" | Correct. Plus: the head *weights* are not zero-initialised (per-unit gain 1.0 ± 0.3 at step 0); gains and offsets are unbounded; the stage-1 encoder gain is shared across all senses | §5.2 |
| (Implicit) a learning-rate difference between May and today | `lr_critic` is read by no code, so the "0.0001 → 0.0005" difference listed in the May-replication design is inert | §5.3 |
| (Implicit) the grid's outcome analysis exists | The site-grid design docs' Results / Analysis / Conclusions sections are **still empty**. The grid's verdict lives in the audit, the olfaction comparison page and the repr page, none of which is the pre-registered read-out | §3 row 1 |

---

## Metrics Requested

| Metric | Why now | Where it would live | Cost |
|---|---|---|---|
| Per-unit post-FiLM activity probability `p_i` and dormancy score (Sokar τ = 0.025), per site, **for modulated and ordinary agents** (dimensionless) | The one untested pathology that could make a modulator actively harmful; its absorbing-state property matters for any algorithmic fix | Offline replay script over saved checkpoints (`scripts/analysis/nmn/`); optionally `src/models/recurrent_ppo_network.py` after each FiLM application | Cheap offline; cheap online (one comparison and one mean per site) |
| Modulator gradient norm split by loss term (policy / value / entropy) | Would show whether the value loss or the policy loss drives the modulator, which bears directly on the "shared end-to-end loss" candidate | `src/models/recurrent_ppo_trainer.py`, around the existing `modulator/grad_norm` | Cheap (three extra reductions) |
| Matched-lesion survival for the ordinary agent (clamp *k* hidden units to their time-average, *k* matched to the modulator's footprint) | The missing control in §6; decides whether "load-bearing" is specific to modulation | Offline, with the freeze-test code | Cheap offline, no training |
| Freeze-at-mean on body-only and world-only arms | Stated as "highest value per unit of effort" and still open | Offline, same script | Cheap |
| R² of the gain's varying part on satiation and felt injury | Tests whether the 15% contextual part tracks the body or the world | Offline replay | Cheap |

## Related Issues

- **The 32 grid agents do not load under the current code** (a mandatory key added later). Every
  re-analysis needs a pinned copy of the code or a documented compatibility path. Engineering decision
  for the user (repr page §07). Suggested route: `bug-curator` to check whether it is registered.
- **The site-grid design docs have empty Results sections** ([[NMN_INPUT_SITE_GRID]] §7–§9,
  [[NMN_INPUT_SITE_GRID_GAENORM]] §8–§10), and their Launch Manifests were never filled in (audit §10
  item 3).
- **[[MAY_DOUBLE_RETURN_REPLICATION]] §3.4** lists the dead `lr_critic` as a May-vs-today difference.
  This is harmless, but it should be noted as inert.
- **Suggested for `plan-reviewer`** before this dossier is used as a premise: check §6's "redundancy"
  reading, which is inference.

## Links

- Grids and internals: `docs/experiments/active/nmn_input_site_grid/` — `NMN_INPUT_SITE_GRID.md`,
  `NMN_INPUT_SITE_GRID_GAENORM.md`, `TRAINING_HEALTH_AUDIT.md`, `repr_analysis.html`,
  `olf_comparison.html`
- Critiques: `docs/project/critiques/nmn_input_site_grid_optimisation_dynamics.md`,
  `20260518_film_as_hyperparameter_modulator_theoretical_audit.md`,
  `20260518_film_as_hyperparameter_modulator_audit_story.md`. The May audit is relevant here for its
  "chain-rule gradient gating" point: a FiLM gain below 1 also scales down the gradient to everything
  upstream. The critique finds this channel "fails at the action head" as an explanation of the quiet
  body-only gradients (§5).
- Behaviour: `docs/experiments/active/modulator_clues/modulator_clues.html`, `INJURY_DEPENDENCE_PLAN.md`
- Factorial: `docs/experiments/active/level05_body_interactions/LEVEL05_BODY_INTERACTIONS.md` §7
- Worlds: `docs/experiments/active/context_exploration/STUDY_PLAN.md`;
  `docs/experiments/active/continual_worlds/CONTINUAL_WORLDS.md`, `MAY_DOUBLE_RETURN_REPLICATION.md`
- May probe: `docs/experiments/active/hypervigilance/NMN_CONTINUAL_DOUBLE_RETURN_PROBE.md`
- PI calls: `docs/pi/calls/2026-09-26_level05_body_interactions_launch.md`,
  `2026-09-27_context_exploration_part4_launch.md`,
  `2026-09-28_after_body_rules_null_and_world_screen.md`
- Code (HEAD `v4.0`): `train.py:1241-1262`; `src/models/recurrent_ppo_trainer.py:173-208`;
  `src/models/recurrent_ppo_network.py:205-263, 500-567`; `src/models/neuromodulator.py:136-300`

## Appendix: deviation from the training_analysis template

This is a consolidation, not a single experiment. So there is no Launch Manifest, no Design section and
no pre-registered hypothesis. §1 serves as the Research Question entry point. §3–§5 replace
Results / Analysis. §6–§7 replace Conclusions. The absence of pre-registration applies to this synthesis
only; each source study's own pre-registration status is given in §3.
