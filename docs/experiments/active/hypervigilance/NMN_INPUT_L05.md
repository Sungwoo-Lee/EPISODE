---
title: "Modulator input at level 05 — does changing what the modulator reads enlarge its effect on injury-driven hiding?"
topic: hypervigilance
status: active
created: 2026-10-07
last_updated: 2026-10-07
wandb_tag: "rppo_nmninp_l05_*_s*"
---

# Modulator input at level 05

> **Status**: DESIGNED, NOT LAUNCHED. Stage 1 = 4 runs (seed 42). Stage 2 (seeds 43, 44) by the user's
> judgement after the stage-1 readout (§5.1).
> **Date**: 2026-10-07
> **Author**: `experiment-designer`
> **Related**: [[FAST_HEAL_REPLICATION]] (the reference runs and the readout this design copies) ·
> [[NMN_CAPACITY_GRID_L05]] (the sister screen, running; this design copies its structure) ·
> [[CROSS_STUDY_NULL_DOSSIER]] (the September input-slice result) ·
> [[NMN_INPUT_SITE_GRID_GAENORM]] (the September grid that first restricted the modulator's input) ·
> [[plan_nmn_capacity_grid]] (the review whose detection-power numbers apply here too) ·
> [[EXCLUSIVE_MODULATOR_INPUT]] (the planned follow-up that removes the redundancy, §8)

---

## 1. Research question

### Plain-language entry point

The project's "modulated" agent carries a small second network, the **modulator**. At every step it
reads the agent's senses and rescales the main network: each neuron gets multiplied by a gain and shifted
by an offset (a technique called FiLM). The hope is that this makes behaviour depend more on body state,
for example hiding in a bush more when injured.

In the fast-bush-healing replication, the modulator read **everything** the agent senses: 58 numbers at
level 05, most of them about the outside world (smell, vision, heat from fires). It did **not** reliably
enlarge injury-driven hiding over an ordinary agent without a modulator. A modulator that reads the same
things as the network it rescales has little reason to carry a body-state signal. A modulator that reads
*only* the body might.

**This experiment** keeps everything from the replication's level-05 modulated agent and changes only
what the modulator reads. There are four versions:

- **N**: felt injury only (1 number);
- **I**: fullness and felt injury (2 numbers);
- **IT**: fullness, body temperature and felt injury (3 numbers, every body-state signal level 05 has);
- **X**: the outside world only: contact pain, felt heat, smell, collision and vision (49 numbers).

The main network still reads all 58 numbers in every version, so no version takes information away
from the agent.

A September test of a similar body-only modulator, in a simpler world, found it the **least**
state-dependent of all the versions tried. So the most likely outcome here is no improvement.

Stage 1 trains one seed of each version. The user decides after seeing the results whether any
version gets two more seeds. This is **exploration**: one seed per version can flag a version worth
following up. It cannot establish an effect.

### Formal statement

> **H₀** (*input does not matter*): no input setting changes the injury effect on bush dwell beyond
> the seed-to-seed variation already seen for the ordinary and all-senses modulated agents at level 05.
>
> **H₁** (*some input setting enlarges the modulator's effect*): at least one input setting produces
> an injury effect on bush dwell (starting injury 70 minus 0) that exceeds both the all-senses modulated
> agent and the ordinary agent, consistently across seeds, in the thermal-neutral test scenes, with the
> own-scene result not reversing.
>
> **H₁-body** (*the direction motivating the study*): the effect, if any, appears in the body-reading
> cells (N, I, IT) and not in X.

## 2. Experimental design

### 2.1 Independent variable

One key, `agent.modulation.input_sensors`. Sensor names are those of the level-05 observation
(`get_observation_breakdown`; widths checked live by the generator, §3.2):

| Sensor | Numbers | Kind |
|---|---|---|
| Satiation | 1 | body (fullness) |
| Body Temperature | 1 | body |
| Interoceptive Nociception | 1 | body (felt injury: the smoothed internal ache; the agent's only trace of its wound) |
| Extero Nociception | 1 | outside (contact pain) |
| Thermoception | 5 | outside (heat felt from the surroundings) |
| Olfaction | 25 | outside |
| Collision | 5 | outside |
| Proprioception | 6 | own previous action |
| Visual | 13 | outside |
| **Total** | **58** | |

| Cell | `input_sensors` | Numbers read by the modulator |
|---|---|---|
| N | `["Interoceptive Nociception"]` | 1 |
| I | `["Satiation", "Interoceptive Nociception"]` | 2 |
| IT | `["Satiation", "Body Temperature", "Interoceptive Nociception"]` | 3 |
| X | `["Extero Nociception", "Thermoception", "Olfaction", "Collision", "Visual"]` | 49 |
| *reference (not retrained)* | `"all"` | 58 |

User decision 2026-10-07 (final). N ⊂ I ⊂ IT are nested, so N→I isolates fullness and I→IT isolates body
temperature as a modulator input. I has the same sensor list as the September "body-only" slice.

**Proprioception is in no cell (designer's decision, default per the brief).** Proprioception is the
one-hot of the agent's previous action. It is neither a body-state signal nor a signal about the outside
world. The September grid excluded it from both restricted slices for that reason (user decision
2026-09-07, recorded in the site-grid generator). Keeping the same rule keeps X comparable to the September
"outside world only" slice. Two consequences:

- IT ∪ X is 52 of the 58 numbers. No cell is the complement of another.
- X differs from the all-senses reference by 9 numbers: the 3 body signals plus the 6 proprioceptive
  ones. An X-vs-reference difference therefore cannot be attributed to the body signals alone. The
  clean body-versus-world contrast is IT vs X (confound C2).

**Modulator parameter count** (constructed models, generator `--verify`): N 23,904; I 23,952; IT 24,000;
X 26,208; reference 26,640. Only the modulator's input layer changes. The task network has 640,903
parameters in every cell.

### 2.2 Controlled variables

Everything except the one key is identical to the replication's level-05 modulated runs. This was checked
mechanically against the runs' **saved** configs (§3.2):

- **World**: `configs/environment/experiment/basic/05-campfire_thermal_10x10.yaml`, unchanged. Level 05
  with **random start body temperature** (`random_start_body_temp: true`, start in [−10, +5]) and fast
  bush healing (`recovery_base_rate 0.2`, `recovery_accel_rate 0`, `recovery_in_bush_multiplier 25`).
- **Agent** (everything else): `configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml`.
  This means FiLM at encoder, task GRU, actor and critic, a 16-unit modulator, grouping 1,
  `rnn_mechanism: activation`, the temperature channel off, `return_mode: GAE_NORM`, and every PPO
  hyperparameter unchanged. That file's header says the modulator reads "all 27 sensed numbers"; that
  is the level-04 count. At level 05, "all" is 58 numbers.
- **Budget**: `--episodes 10000000` and `--log-interval 10`, as in the replication. 50 checkpoints per
  run, one every 200,000. `num_envs` 128 and `checkpoint_frequency` 200000 are config-owned.
- **Seed mechanism**: `--seed <42|43|44>` on the command line, as in the replication and the capacity
  grid. One config per cell serves all seeds.
- **Starting network**: with the trainer's seed-42 init key, every cell's task-network starting weights
  are bit-identical to the reference modulated agent's (checked by `--verify`; the modulator is built
  last). The modulator's own weights differ, because its input layer has a different width.

### 2.3 Confounds and limitations

| # | Confound | Severity | Handling |
|---|---|---|---|
| C1 | **Redundancy.** The main network reads every sensor in every cell. A body-only modulator therefore gives the policy no information it lacks; it can only change *how* the body signals are used. A null here does not show that a body-reading modulator is useless. It shows that adding one beside a network that already reads the body does not help. | High | Stated in every verdict. The direct test is an **exclusive-input** version, where the main network does not receive what the modulator reads. That needs code: [[EXCLUSIVE_MODULATOR_INPUT]] (plan by `senior-developer`, 2026-10-07, awaiting user decisions). |
| C2 | X vs the all-senses reference differs by 9 numbers (3 body + 6 proprioception). | Med | X-vs-reference is not read as "the body signals matter". The body-vs-world contrast is IT vs X. |
| C3 | **The neutral test scenes are off the training distribution on exactly the channels IT and X read.** In those scenes the air is 0 °C with no fire, body temperature sits at 0 and the heat sensors read 0. In training the air is about −30 °C and the body starts in [−10, +5]. N and I read neither channel. So a neutral-scene difference between IT/X and N/I may be an out-of-distribution input to the modulator, not a difference in learned behaviour. | High (for IT and X) | The own level-05 scenes (training world, campfire beside the bush) are the in-distribution check. An IT or X result is reported only with its own-scene value beside it. Neither scene set alone decides. |
| C4 | Stage-2 seeds would be chosen after seeing seed 42, so a selected cell's seed-42 value is biased upward. | Med | Stage-2 effect sizes use seeds 43–44 only (§5.2). |
| C5 | Seed-to-seed variation at level 05 is as large as the agent difference (the replication's take-home), and stage 1 has one seed per cell. | High | The detection-power caveat (§5.1) is carried into every stage-1 statement. Effects of a few percentage points will usually be missed. |
| C6 | Stage-1 GPUs are mixed: RTX 3090 (node 109: N, I) and RTX 4090 (node 113: IT, X). | Low | Changes speed and floating-point non-determinism, not the algorithm. The replication and the capacity grid also mixed cards. |
| C7 | The four stage-1 cells share the task network's initialisation and first world (seed 42), so they are not four independent draws. | Low | Seed-42 comparisons are descriptive (as in [[plan_nmn_capacity_grid]] F5). |
| C8 | New readouts come from a new sweep folder; the references from the 2026-10-06 healrep sweeps. | Low | Same probes, episodes, conditions and estimator. Compare the two sweeps' `_provenance/` snapshots before reading. If the evaluation code or scenes changed, re-test the six references into the new folder. |

## 3. Launch manifest

WandB group `nmn_input_l05`, job type `ablation`, for all 12 rows. Tag = WandB name, format
`rppo_nmninp_l05_<CELL>_s<seed>`. Stage-1 node:GPU slots are the user's pool (2026-10-07), packed node
first: 109 (RTX 3090, both GPUs) and then 113 (RTX 4090, both GPUs). The `training-runner` confirms that
the GPUs are free (gpu-status + diary + pgrep) and that the NAS is mounted before launch. Node 113 rebooted
once during the replication (2026-10-05). Stage-2 nodes are assigned by the user if stage 2 happens.

**Expected wall time**: ~19–20 h per run on an RTX 3090 (the replication's level-05 modulated runs on
109–111). Expect about the same or less on the 4090. Shrinking the modulator's input does not measurably
change cost; the 640k-parameter task network dominates.

| Run | Stage | Status | Cell | Tag (= wandb-name) | wandb-group | wandb-job-type | Seed | Node | GPU | Launched at | WandB run ID | Log path |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | planned | N | rppo_nmninp_l05_N_s42 | nmn_input_l05 | ablation | 42 | 109 | cuda:0 | — | — | — |
| 2 | 1 | planned | I | rppo_nmninp_l05_I_s42 | nmn_input_l05 | ablation | 42 | 109 | cuda:1 | — | — | — |
| 3 | 1 | planned | IT | rppo_nmninp_l05_IT_s42 | nmn_input_l05 | ablation | 42 | 113 | cuda:0 | — | — | — |
| 4 | 1 | planned | X | rppo_nmninp_l05_X_s42 | nmn_input_l05 | ablation | 42 | 113 | cuda:1 | — | — | — |
| 5 | 2 | conditional | N | rppo_nmninp_l05_N_s43 | nmn_input_l05 | ablation | 43 | — | — | — | — | — |
| 6 | 2 | conditional | N | rppo_nmninp_l05_N_s44 | nmn_input_l05 | ablation | 44 | — | — | — | — | — |
| 7 | 2 | conditional | I | rppo_nmninp_l05_I_s43 | nmn_input_l05 | ablation | 43 | — | — | — | — | — |
| 8 | 2 | conditional | I | rppo_nmninp_l05_I_s44 | nmn_input_l05 | ablation | 44 | — | — | — | — | — |
| 9 | 2 | conditional | IT | rppo_nmninp_l05_IT_s43 | nmn_input_l05 | ablation | 43 | — | — | — | — | — |
| 10 | 2 | conditional | IT | rppo_nmninp_l05_IT_s44 | nmn_input_l05 | ablation | 44 | — | — | — | — | — |
| 11 | 2 | conditional | X | rppo_nmninp_l05_X_s43 | nmn_input_l05 | ablation | 43 | — | — | — | — | — |
| 12 | 2 | conditional | X | rppo_nmninp_l05_X_s44 | nmn_input_l05 | ablation | 44 | — | — | — | — | — |

Tags are unique, and no `rppo_nmninp_*` folder exists under `results/JAX_RecurrentPPO/` (checked
2026-10-07). Stage-2 rows become `cancelled` for cells the user does not advance.

**Launch command** (one per row; `<CELL>` from the table, `<D>` = GPU index):

```bash
/home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
  --config configs/environment/experiment/basic/05-campfire_thermal_10x10.yaml \
  --agent_config configs/models/recurrent_ppo/nmn_input_l05/nmninp_<CELL>.yaml \
  --episodes 10000000 \
  --device cuda:<D> \
  --log-interval 10 \
  --seed <SEED> \
  --tag <TAG> --wandb-name <TAG> \
  --wandb-group nmn_input_l05 --wandb-job-type ablation
```

Give each run its own `--log` file and stagger the launches by about 12 s, as for the capacity grid (three
replication runs launched in the same second once shared a log). **Post-launch ground-truth check**
(runner): each run's `models/config.yaml` must show its cell's `input_sensors` list, the row's `seed`,
`recovery_in_bush_multiplier: 25.0` and `random_start_body_temp: true`.

### 3.1 Configs to produce (done)

| Cell (runs) | Config (env) | Config (agent) |
|---|---|---|
| N (1, 5, 6) | `configs/environment/experiment/basic/05-campfire_thermal_10x10.yaml` (unchanged) | `configs/models/recurrent_ppo/nmn_input_l05/nmninp_N.yaml` |
| I (2, 7, 8) | same | `.../nmninp_I.yaml` |
| IT (3, 9, 10) | same | `.../nmninp_IT.yaml` |
| X (4, 11, 12) | same | `.../nmninp_X.yaml` |

All four, and the eight eval specs of §5.4, are generated by
`configs/models/recurrent_ppo/nmn_input_l05/generate_input_arms.py`. Do not hand-edit them. No new schema
keys (`input_sensors` lists are already read by `_resolve_modulator_input_indices`), no environment config
change, and no registry setting change, so there is no `CONFIG_CRITICAL_SETTINGS.md` entry.

### 3.2 Verification record (2026-10-07, `generate_input_arms.py --verify`, CPU)

- **`--check`**: all 12 generated files match the generator byte for byte.
- **Text diff** of every agent file against the reference (comments and blank lines stripped): exactly
  one line, `input_sensors: "all"` → the cell's list (X wraps onto two lines).
- **[1] flattened key diff** vs the reference: exactly `{agent.modulation.input_sensors}` for all four.
- **[2] resolved config vs ground truth**: train.py's merge order plus this manifest's flags, compared with
  the saved `models/config.yaml` of the replication run `rppo_healrep_l05_t16quad_s42`. The reference
  agent resolved now reproduces that saved config exactly, apart from the WandB group/job type. This
  validates the reconstruction. Every cell × seed (12 combinations) differs from it only in
  `input_sensors`, `seed` (43/44 only), `tag` and `wandb.name/group/job_type`.
- **[3] observation layout**: the live level-05 breakdown matches §2.1 in names, order and widths (58).
- **[4] construction** with the trainer's seed-42 init key, for all four:
  - the modulator reads exactly the named sensors' columns (N: 2; I: 0, 2; IT: 0–2; X: 3–57 without
    Proprioception's 46–51), and its input layer has that width;
  - the modulator has 16 units and grouping 1; all four sites are on, the temperature channel is off;
  - the task-network starting weights are bit-identical to the reference;
  - the forward pass is finite, and a finite, non-zero gradient reaches the input layer and all 10 FiLM
    heads;
  - **isolation**: changing every column the cell does not read leaves the modulator's state and all
    ten FiLM outputs bit-identical over two steps. The main network's output does change, because it
    still reads all 58. Changing a column the cell does read changes the modulator's state.

## 4. Predicted outcomes

- **Most likely: null.** The prior comes from the dossier and the replication. In September, the
  body-only modulators were the least state-dependent of any input setting: about 7 % of their gain
  variation was over time, against about 21 % for all-senses (at the encoder, 97 % of their variation was
  fixed). No cell leaves the six-run reference range at seed 42.
- **H₁-body shape, if true:** N, I or IT shows a neutral-scene injury effect with the wandering rabbit
  clearly above the six reference runs from ~2 M steps on. The effect is stable across checkpoints and
  carries into the own scenes, and survival is unchanged. X sits inside the reference range.
- **Plausible other shapes:**
  - IT or X differs from N and I in the neutral scenes but not in the own scenes. That is confound C3
    (off-distribution heat channels), not an input effect.
  - The body-only modulators end with a near-constant gain (the September pattern). The injury effect
    then equals the ordinary agent's.

## 5. Analysis plan (pre-specified)

**Readout = the replication page's tests, unchanged** (as in [[NMN_CAPACITY_GRID_L05]] §5). These are
the experiment tests at every saved checkpoint, 30 episodes per scene and starting injury, read as
checkpoint-wise means over 2–10 M steps on the 0.2 M grid (41 checkpoints), with the lag-1-corrected
95 % interval of the Basic Behaviour estimator
(`scripts/analysis/studies/fast_heal_replication/figures.py`, `effect()`). The measures:

- **Injury effect, no animal**: bush dwell at starting injury 70 minus at 0, no animal in the scene (pp).
- **Injury effect, wandering rabbit**: the same with a harmless wandering rabbit (pp).
- **Predator effect**: bush dwell with a hunting predator minus with no animal, unhurt (pp).
- **Ten-injury dose figures**: bush dwell vs starting injury 0..90, in the injury-grid scenes (no animal /
  rabbit) and the chase scenes.
- **Training view**: ten injury lines across training (the page's B5 view), per cell.

Two scene sets, as for level 05 on the page:

- the **thermal-neutral scenes** (air 0 °C, no campfire, start body temperature 0);
- the **own level-05 scenes** (built on the training world, with a campfire beside the bush).

Because of C3, the two sets are read side by side for every cell. Neither is labelled "main" for IT or X.

Performance checks use **survival steps only**:

- in the tests, mean survival ≥ 95 steps in the four no-predator scenes (the page's floor; below it a
  value is reported, not interpreted);
- in training, WandB `Episode/Steps`, checkpoint-wise mean over 2–10 M steps, not more than 10 % below
  the lowest of the six reference runs. The reference values and the resulting threshold are in §5.0.

Reward is not used anywhere.

### 5.0 References (already trained, not retrained)

The replication's level-05 runs, seeds 42–44, both agents (run list in [[FAST_HEAL_REPLICATION]], Launch
record; test results under `results/eval/avoidance/metrics_history_rppo_healrep/l05_{neutral,own,grid,gridchase}/`).
Values computed 2026-10-06 with the page's estimator (copied from [[NMN_CAPACITY_GRID_L05]] §5, where they
were independently reproduced by the plan-reviewer):

| Measure (2–10 M mean, pp) | ordinary s42 / s43 / s44 | all-senses modulated s42 / s43 / s44 | six-run range |
|---|---|---|---|
| Injury effect, no animal — neutral | 5.3 / 10.3 / 11.7 | 11.0 / 3.7 / 11.5 | 3.7 – 11.7 (median 10.65) |
| Injury effect, wandering rabbit — neutral | 0.6 / 9.2 / 8.8 | 8.4 / 3.4 / 7.1 | 0.6 – 9.2 |
| Predator effect — neutral | 43.7 / 48.8 / 46.3 | 49.9 / 36.4 / 57.5 | 36.4 – 57.5 |
| Injury effect, no animal — own | 8.8 / 9.8 / 10.9 | 10.8 / 11.0 / 11.9 | 8.8 – 11.9 |
| Injury effect, wandering rabbit — own | 9.1 / 9.6 / 11.1 | 9.6 / 9.7 / 11.3 | 9.1 – 11.3 |
| Predator effect — own | 28.5 / 18.2 / 35.5 | 27.2 / 30.4 / 22.5 | 18.2 – 35.5 |

**Training survival** (WandB `Episode/Steps`, computed 2026-10-07). For each of the 41 checkpoints from
2 M to 10 M, the logged value nearest that checkpoint is taken from WandB's sampled history (2,500 rows per
run), and the 41 values are averaged:

| | s42 | s43 | s44 |
|---|---|---|---|
| ordinary | 242.1 | 243.3 | 242.7 |
| all-senses modulated | 246.4 | 247.1 | 247.8 |

**Survival-guard threshold: 217.9 steps** (10 % below the lowest, 242.1). This answers the capacity-grid
review's F3 for this study. The same number applies to the capacity grid, whose doc did not record one.

**Context, not references:** the nine capacity-grid seed-42 runs ([[NMN_CAPACITY_GRID_L05]], running since
2026-10-06) will be tested with the same probes. Their values are shown beside this study's for context.
They are other modulator variants, not controls, and they share seed 42 with this study's cells (C7).

### 5.1 Stage-1 readout and the stage-2 decision (seed 42 only; user's judgement)

**No numeric gate.** As for the capacity grid (user decision 2026-10-06), the user decides by judgement
after seeing the stage-1 readout which cells, if any, get seeds 43 and 44. The readout to be produced,
fixed now, is one table per scene set (neutral, own) with:

- **rows**: N, I, IT, X (seed 42), then the six reference runs, then the nine capacity-grid seed-42 runs
  (context);
- **columns**: injury effect with no animal; injury effect with the wandering rabbit; predator effect. Each
  is the 2–10 M checkpoint-wise mean with its lag-1-corrected 95 % interval;
- **per-checkpoint columns** (mandatory temporal view, for the two injury effects): the share of the 41
  checkpoints in which cell − (seed-42 all-senses modulated) is positive, and whether the 2–10 M mean is
  carried by a late jump rather than a stable offset. Descriptive only (C7);
- **survival columns**: mean test survival in the four no-predator scenes; training `Episode/Steps` mean
  over 2–10 M against the §5.0 threshold;
- **two reference-only columns**, which do not decide anything:
  - *strict rule* (the capacity grid's original §5.1): rabbit effect ≥ 12.2 pp and no-animal effect
    ≥ 14.7 pp, with both 95 % lower bounds above the range maximum (9.2 / 11.7), and own-scene effects
    ≥ the seed-42 all-senses modulated agent's (10.8 / 9.6);
  - *option A* (the plan-reviewer's): rabbit effect ≥ 9.2 pp, no-animal effect ≥ 10.65 pp, both own-scene
    effects ≥ 8.8 / 9.1 pp, and the survival guard holds.

The ten-injury dose figures and the training view (B5) for each cell sit beside the table.

**Detection-power caveat (from [[plan_nmn_capacity_grid]], F1; it applies unchanged, because the six
references and their spread are the same).** The six reference values of each neutral injury effect have
a standard deviation of about 3.5 pp, with a 95 % interval of roughly 2.2–8.6 pp. Under a normal model,
the chance that a single cell passes is:

| True shift of the cell (pp) | strict rule | option A |
|---|---|---|
| 0 (no effect) | ~1.5 % | ~17 % |
| +3 | ~10 % | ~47 % |
| +5 | ~23 % | ~67–70 % |
| +7 | ~44 % | ~77–87 % |

With four cells and no true effect, at least one passes option A about half the time (assuming
independence; C7 makes them less than independent). Reading by judgement does not escape these numbers.
A stage-1 null must be recorded as **"no cell separated at seed 42; effects smaller than about 7 pp were
more likely missed than detected"**, never as "no effect".

### 5.2 Stage-2 readout (if the user advances a cell; exploratory)

For each advanced cell, paired by seed against **both** references (the all-senses modulated agent and the
ordinary agent at the same seed), on the **fresh seeds 43 and 44 only**:

1. **Fresh seeds carry it.** At seeds 43 and 44, the neutral-scene injury effect with the wandering
   rabbit is larger than both references at that seed. The own-scene injury effect is not below the
   six-run minimum.
2. **Size.** The mean over seeds 43–44 of (cell − all-senses modulated) for that measure, with the 3-seed
   mean beside it (not instead of it).
3. **Consistency.** The no-animal injury effect points the same way at both fresh seeds.
4. **Survival guard** at every seed.

If 1–4 hold, the verdict reads "this input setting is a candidate for a confirmatory test", not "the
input setting increases the modulator effect". A claim needs a separate, pre-registered confirmatory
run with ≥ 5 fresh seeds. Under no effect, a cell beats both references at both fresh seeds about one
time in nine per seed pair (it must be the highest of three at each seed).

### 5.3 Secondary and diagnostic readouts (no decision weight)

- **How state-dependent the modulator's output is**: its gain split into the part that changes over time
  and the part that differs only between units (the dossier's measure). September predicts N/I/IT lower
  than the all-senses reference, and X close to it. Tooling: `scripts/analysis/nmn/` (reads sizes from the
  constructed model).
- **Freeze test**: hold the modulator's output at its mean and measure the survival cost. It has never been
  run on a body-only modulator (dossier, "untested for body-only and world-only"). This would show whether
  the N/I/IT modulators are used at all.
- **Training survival curves** (`Episode/Steps`) for all cells against the six references.

### 5.4 Eval sweep specs (prepared, not launched)

Same probe folders, conditions, 30 episodes, x axis and measures as the healrep level-05 specs (checked:
the non-run fields are identical):

| Scene set | Stage 1 (4 runs) | Stage 2 (8 runs; delete rows of cells not advanced) |
|---|---|---|
| neutral | `configs/eval_sweeps/nmninp/nmninp_l05_neutral_stage1_rppo.yaml` | `..._neutral_stage2_rppo.yaml` |
| own | `configs/eval_sweeps/nmninp/nmninp_l05_own_stage1_rppo.yaml` | `..._own_stage2_rppo.yaml` |
| injury grid (dose) | `configs/eval_sweeps/nmninp/nmninp_l05_grid_stage1_rppo.yaml` | `..._grid_stage2_rppo.yaml` |
| chase grid (dose) | `configs/eval_sweeps/nmninp/nmninp_l05_gridchase_stage1_rppo.yaml` | `..._gridchase_stage2_rppo.yaml` |

Output: `results/eval/avoidance/metrics_history_rppo_nmninp/l05_<set>/`. Run paths are globs on the planned
tag. `run_sweep.py` refuses a glob that matches 0 or 2+ folders, so after a relaunch, the live folder must
be pinned by hand. The nodes (109, 113) are placeholders; confirm they are free before a sweep. The
stage-1 readout table needs a small study script that applies `figures.effect()` to these folders, the
reference folders and the capacity-grid folders. The capacity-grid review (F4) asked for that script to
be built and checked against the §5.0 table before any results exist. One script should serve both
studies. That is analysis-phase work and does not block the launch.

## 6. Failure-mode catalog (decided in advance)

| Observation | Counts as |
|---|---|
| NaN / divergence / critic explosion in a cell | A failed **run**, not a refutation. Relaunch once with the same seed. A second failure is reported as "this input setting is unstable at level 05". |
| A cell below the survival floor (test or training) | Its behaviour numbers are reported, not interpreted. |
| A cell's effect is visible in the neutral scenes only (IT or X) | Confound C3 first. Not read as an input effect unless the own scenes agree in direction. |
| A body-only cell equals the ordinary agent | The expected null (redundancy C1 plus the September pattern). Reported with the C1 caveat. It motivates the exclusive-input follow-up; it does not refute body-reading modulation in general. |
| An effect carried by the last few checkpoints only | Flagged for the user; the default is not to advance. |
| The node dies mid-run (node 113 rebooted on 2026-10-05) | A failed run. Relaunch from scratch with the same tag on another node. The dead folder is excluded and the eval glob is pinned. |
| Effect visible by 10 M but still rising | Insufficient horizon is **not** assumed. A longer horizon would be a new design. |
| Every cell inside the reference range | The pre-registered null for this screen, recorded with the detection-power caveat (§5.1). |

## 7. Code hazards checked (2026-10-07, HEAD of `v5.0`)

None blocks the launch.

1. **Sensor names.** `_resolve_modulator_input_indices` raises on an unknown name, and the names are
   resolved against the run's own observation layout. All four lists resolve at level 05 (§3.2 [4]).
2. **Slicing order.** The modulator's input is gathered *after* the network's symlog compression
   (`recurrent_ppo_network.py`, forward pass), so it sees the same scaling as the task network.
3. **Isolation** is verified directly (§3.2 [4]). The excluded senses cannot reach the modulator.
4. **Checkpoint restore and analysis tools.** Both rebuild the model from the run's saved config, which
   carries the list, so the modulator's input width is restored correctly. A wrong config fails loudly on
   the shape mismatch.
5. **Test coverage.** The September grid trained list-valued `input_sensors` in 40 runs, so this is not an
   untested path. The new cells are N and IT (new lists) and X (adds Thermoception).
6. **Interaction with the exclusive-input change.** [[EXCLUSIVE_MODULATOR_INPUT]] adds a new mandatory
   agent key and regenerates the reference agent file. Its plan review (F2, F3) already lists this family.
   - **If the four stage-1 runs launch before that change lands**: nothing to do. The runs carry their
     saved configs, and that plan's compatibility shim covers re-opening them for the tests.
   - **If the change lands first**: rerun this generator, so the four files pick up the new key from the
     regenerated reference. Widen `--verify` [2] (both the reference equality check and the per-cell
     subset check) to allow the new key, which the replication's saved config lacks. Rerun `--verify`.
     Launching the current files after the change would fail loudly at start-up (missing mandatory key);
     it costs time, not data.
7. **Stale header in the reference agent file**: "all 27 sensed numbers" is the level-04 count (§2.2).
   That file is generated by another study's script and is not edited here.

## 8. Follow-up: exclusive input (pending)

A version where the main network does **not** receive what the modulator reads would remove confound C1:
a body-only modulator would then be the agent's only route to the body signals. That needs code (a list of
sensors withheld from the main network) and is planned in [[EXCLUSIVE_MODULATOR_INPUT]] (`senior-developer`,
2026-10-07; awaiting user decisions D1–D4). The same key on an ordinary agent gives the matched control: an
ordinary agent blind to the same sensors.

## 9. Results

*(empty until stage 1 is trained and tested)*

## 10. Conclusions

*(empty)*
