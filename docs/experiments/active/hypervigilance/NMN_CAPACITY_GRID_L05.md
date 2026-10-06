---
title: "Modulator capacity grid at level 05 — does a larger or coarser-grained modulator enlarge the modulator's effect on injury-driven hiding?"
topic: hypervigilance
status: active
created: 2026-10-06
last_updated: 2026-10-06
wandb_tag: "rppo_nmncap_l05_h*g*_s*"
---

# Modulator capacity grid at level 05

> **Status**: DESIGNED — stage 1 ready to launch; stage 2 conditional on the stage-1 rule (§5.1). Nothing launched.
> **Date**: 2026-10-06
> **Author**: `experiment-designer`
> **Related**: [[FAST_HEAL_REPLICATION]] (the reference runs and the readout this design copies; results
> page "Fast Bush Healing Replication", https://claude.ai/artifact/SRzbPi3VeWxxR11hVn9aym) ·
> [[CROSS_STUDY_NULL_DOSSIER]] (why capacity is a candidate) · [[NMN_FILM_GROUPING_SCREEN]] (the June
> grouping screen, which has no written result)

---

## 1. Research question

### Plain-language entry point

The project's "modulated" agent carries a small second network, the **modulator**. It reads the agent's
senses at every step and rescales the main network: each neuron gets multiplied by a gain and shifted by an
offset (a technique called FiLM). The hope is that this lets behaviour depend more on body state, for
example hiding in a bush more when injured.

The fast-bush-healing replication trained ordinary and modulated agents with three seeds each. Both agent
types learned to hide more when injured. The modulator did **not** reliably enlarge that effect, though.
With a harmless wandering rabbit in the scene, the modulated agent's injury effect was larger in only 4
of 9 matched pairs, by about 1 percentage point on average. Differences between seeds of the same agent
were as large as the difference between the agents.

Every modulated agent so far has used the same size settings: a 16-unit modulator and one gain per
neuron. The size of the modulator has never been varied. A cross-study review found that 85–90 % of the
modulator's output is a fixed, unchanging re-tuning. That leaves room for a modulator that is too small,
or too finely split, to carry a useful state-dependent signal.

**This experiment** trains nine modulator size settings at level 05: the 10×10 world with predators,
rabbits, body temperature and campfires, where injuries heal fast in a bush. It crosses three modulator
sizes (32, 64, 128 units) with three degrees of sharing: 8, 16 or 32 neighbouring neurons share one
state-dependent gain. Everything else is identical to the replication's level-05 modulated agent.

The experiment runs in two stages. Stage 1 trains one seed (42) of every setting. Only settings that
clearly stand out at that seed get two more seeds (stage 2). If none stands out, this direction is
dropped.

This is **exploration, not a confirmatory test**. At most three seeds per setting can flag a setting
worth confirming. They cannot establish an effect.

### Formal statement

> **H₀** (*capacity does not matter*): no capacity setting changes the injury effect on bush dwell beyond
> the seed-to-seed variation already seen for the ordinary and current-setting modulated agents at level 05.
>
> **H₁** (*some capacity setting enlarges the modulator's effect*): at least one (`mod_hidden_size`,
> `grouping_size`) cell produces an injury effect on bush dwell (starting injury 70 minus 0) that exceeds
> both the current-setting modulated agent (16 units, grouping 1) and the ordinary agent at the same seed,
> consistently across seeds — in the thermal-neutral test scenes, with the own-scene result not reversing.

Numerical forms of both, and of the stage-1 screen, are in §5.

## 2. Experimental design

### 2.1 Independent variables

| Variable | Values | Reference value (not retrained) | Meaning |
|---|---|---|---|
| `agent.modulation.mod_hidden_size` | 32, 64, 128 | 16 | units in the modulator's own GRU (its memory/working width) |
| `agent.modulation.grouping_size` | 8, 16, 32 | 1 | neurons of a 128-wide task layer sharing one state-dependent gain/offset → 16 / 8 / 4 gains per modulated layer (reference: 128) |

3 × 3 = 9 cells. User decision (2026-10-06, final): hidden 16, grouping 1 and grouping 128 are deliberately
excluded; the (16, 1) cell already exists as the reference.

**What grouping does and does not change (read from `src/models/neuromodulator.py`, `_get_signal`).**
Each FiLM head outputs `128 / grouping_size` numbers that are repeated across each group; to that the
modulator adds a per-neuron learned baseline that is 128 wide at every grouping. So grouping coarsens only
the *state-dependent* part of the gain/offset. The fixed per-neuron re-tuning — which the dossier found to
be ~85 % of the gain variance — remains fully per-neuron in every cell.

**Modulator parameter count** (counted on the constructed models by the generator's `--verify`):

| | g8 | g16 | g32 |
|---|---|---|---|
| h32 | 15,296 | 12,656 | 11,336 |
| h64 | 35,296 | 30,096 | 27,496 |
| h128 | 93,728 | 83,408 | 78,248 |

Reference (h16, g1): 26,640. Task network: 640,903 in every cell. Note that the h32 cells have *fewer*
modulator parameters than the reference. "Capacity" here is two-dimensional — more recurrent width, fewer
independent output channels — not a single "bigger" axis (§2.3, C1).

### 2.2 Controlled variables

Everything except the two keys is identical to the replication's level-05 modulated runs. This was checked
mechanically, against the runs' **saved** configs, by the generator (§3.2):

- **World**: `configs/environment/experiment/basic/05-campfire_thermal_10x10.yaml` unchanged — level 05 with
  **random start body temperature** (`random_start_body_temp: true`), *not* the fixed-start-temperature
  arm; fast bush healing (`recovery_base_rate 0.2`, `recovery_accel_rate 0`, `recovery_in_bush_multiplier 25`).
- **Agent** (everything else): the reference agent
  `configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml`. This means FiLM
  at encoder + task GRU + actor + critic, the modulator reading all 27 sensed numbers,
  `rnn_mechanism: activation`, the temperature channel off, `return_mode: GAE_NORM`, and every PPO
  hyperparameter unchanged.
- **Budget**: `--episodes 10000000` (the replication's flag; the trainer saves a checkpoint every
  200,000 of these, 50 checkpoints per run; the replication page labels this axis "million training
  steps"). `--log-interval 10`. `num_envs` 128 and `checkpoint_frequency` 200000 are config-owned
  (`configs/train/default.yaml` + `configs/train/recurrent_ppo.yaml`), not passed on the command line —
  as in the replication.
- **Seed mechanism**: `--seed <42|43|44>` on the command line, as in the replication. Evidence: the
  saved config of `rppo_healrep_l05_t16quad_s43` has top-level `seed: 43` while `training.seed` stays 42.
  One config per cell therefore serves all seeds. No seed-specific config files are needed.
- **Starting network**: with the trainer's seed-42 init key, every cell's *task network* starting weights
  are bit-identical to the reference modulated agent's. This holds because the modulator is constructed
  last, so its size does not shift the random stream (checked by `--verify`). Paired-by-seed comparisons
  against the current-setting modulated agent therefore share the task network's initial weights and the
  first world. They diverge once actions differ.

### 2.3 Confounds and limitations

| # | Confound | Severity | Handling |
|---|---|---|---|
| C1 | No cell shares either setting with the reference (16, 1), so a cell-vs-reference difference cannot be attributed to one key alone. Within-grid rows and columns can be compared (one key varies), but with one seed per cell in stage 1, those comparisons are weak. | Med | User's design decision (final). Stated in every verdict: "the (h, g) setting", never "more units" or "coarser grouping" alone, unless a row/column pattern holds across seeds. |
| C2 | "Capacity" is two-dimensional: the h32 cells have fewer modulator parameters than the reference. | Low | Parameter table in §2.1; the verdict names cells, not "capacity". |
| C3 | Stage 2 is chosen on seed 42 (selection, so the selected cell's seed-42 value is biased upward). | Med | The stage-2 verdict requires the two *fresh* seeds (43, 44) to pass on their own (§5.2). |
| C4 | Stage-1 GPUs are mixed: RTX 2080 Ti on nodes 101/103 (cells h32g8, h32g16, h32g32, h64g8), RTX 3090 on 106/107/108. | Low | The GPU type changes speed and floating-point non-determinism, not the algorithm. The replication also mixed card types. |
| C5 | Readouts of the new runs come from a new sweep. The references come from the 2026-10-06 healrep sweeps. | Low | Same probe folders, episodes, conditions and estimator. Before reading, compare the two sweeps' `_provenance/` snapshots (commit + resolved scenes). If the evaluation code or scenes changed, re-test the six references in the new output folder. |
| C6 | Seed-to-seed variation at level 05 is as large as the agent difference (the replication's take-home), and stage 1 has one seed per cell. | High | The stage-1 rule asks for a value **outside** the six-run envelope by a margin (§5.1), and stage 2 exists to remove false triggers. Small real effects (a few pp) will be missed. That is accepted for a screen. |

## 3. Launch manifest

WandB group `nmn_capacity_l05`, job type `ablation`, for all 27 rows. Tag = WandB name, format
`rppo_nmncap_l05_h<H>g<G>_s<seed>`. Node:GPU for stage 1 is the user-approved pool (2026-10-06); the
`training-runner` confirms the GPUs are free (gpu-status + diary + pgrep) and the NAS is mounted (node 107
is intermittent) before launch. Avoid 114 and 102. Stage-2 nodes are assigned by the user if and when stage 2
is triggered.

**Expected wall time** (from the replication's level-05 modulated runs): ~19–20 h per run on an RTX 3090
(nodes 109–111). The level-06 modulated runs took ~22 h on the RTX 2080 Ti nodes 101/103. So expect
~20–23 h per run, about one day. The extra modulator compute is small next to the 640k-parameter task
network. The h128 cells may run a few percent slower.

| Run | Stage | Status | Cell | Tag (= wandb-name) | wandb-group | wandb-job-type | Seed | Node | GPU | Launched at | WandB run ID | Log path |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | planned | h32g8 | rppo_nmncap_l05_h32g8_s42 | nmn_capacity_l05 | ablation | 42 | 101 | 0 | — | — | — |
| 2 | 1 | planned | h32g16 | rppo_nmncap_l05_h32g16_s42 | nmn_capacity_l05 | ablation | 42 | 101 | 1 | — | — | — |
| 3 | 1 | planned | h32g32 | rppo_nmncap_l05_h32g32_s42 | nmn_capacity_l05 | ablation | 42 | 103 | 0 | — | — | — |
| 4 | 1 | planned | h64g8 | rppo_nmncap_l05_h64g8_s42 | nmn_capacity_l05 | ablation | 42 | 103 | 1 | — | — | — |
| 5 | 1 | planned | h64g16 | rppo_nmncap_l05_h64g16_s42 | nmn_capacity_l05 | ablation | 42 | 106 | 0 | — | — | — |
| 6 | 1 | planned | h64g32 | rppo_nmncap_l05_h64g32_s42 | nmn_capacity_l05 | ablation | 42 | 106 | 1 | — | — | — |
| 7 | 1 | planned | h128g8 | rppo_nmncap_l05_h128g8_s42 | nmn_capacity_l05 | ablation | 42 | 107 | 0 | — | — | — |
| 8 | 1 | planned | h128g16 | rppo_nmncap_l05_h128g16_s42 | nmn_capacity_l05 | ablation | 42 | 107 | 1 | — | — | — |
| 9 | 1 | planned | h128g32 | rppo_nmncap_l05_h128g32_s42 | nmn_capacity_l05 | ablation | 42 | 108 | 0 | — | — | — |
| 10 | 2 | conditional | h32g8 | rppo_nmncap_l05_h32g8_s43 | nmn_capacity_l05 | ablation | 43 | — | — | — | — | — |
| 11 | 2 | conditional | h32g8 | rppo_nmncap_l05_h32g8_s44 | nmn_capacity_l05 | ablation | 44 | — | — | — | — | — |
| 12 | 2 | conditional | h32g16 | rppo_nmncap_l05_h32g16_s43 | nmn_capacity_l05 | ablation | 43 | — | — | — | — | — |
| 13 | 2 | conditional | h32g16 | rppo_nmncap_l05_h32g16_s44 | nmn_capacity_l05 | ablation | 44 | — | — | — | — | — |
| 14 | 2 | conditional | h32g32 | rppo_nmncap_l05_h32g32_s43 | nmn_capacity_l05 | ablation | 43 | — | — | — | — | — |
| 15 | 2 | conditional | h32g32 | rppo_nmncap_l05_h32g32_s44 | nmn_capacity_l05 | ablation | 44 | — | — | — | — | — |
| 16 | 2 | conditional | h64g8 | rppo_nmncap_l05_h64g8_s43 | nmn_capacity_l05 | ablation | 43 | — | — | — | — | — |
| 17 | 2 | conditional | h64g8 | rppo_nmncap_l05_h64g8_s44 | nmn_capacity_l05 | ablation | 44 | — | — | — | — | — |
| 18 | 2 | conditional | h64g16 | rppo_nmncap_l05_h64g16_s43 | nmn_capacity_l05 | ablation | 43 | — | — | — | — | — |
| 19 | 2 | conditional | h64g16 | rppo_nmncap_l05_h64g16_s44 | nmn_capacity_l05 | ablation | 44 | — | — | — | — | — |
| 20 | 2 | conditional | h64g32 | rppo_nmncap_l05_h64g32_s43 | nmn_capacity_l05 | ablation | 43 | — | — | — | — | — |
| 21 | 2 | conditional | h64g32 | rppo_nmncap_l05_h64g32_s44 | nmn_capacity_l05 | ablation | 44 | — | — | — | — | — |
| 22 | 2 | conditional | h128g8 | rppo_nmncap_l05_h128g8_s43 | nmn_capacity_l05 | ablation | 43 | — | — | — | — | — |
| 23 | 2 | conditional | h128g8 | rppo_nmncap_l05_h128g8_s44 | nmn_capacity_l05 | ablation | 44 | — | — | — | — | — |
| 24 | 2 | conditional | h128g16 | rppo_nmncap_l05_h128g16_s43 | nmn_capacity_l05 | ablation | 43 | — | — | — | — | — |
| 25 | 2 | conditional | h128g16 | rppo_nmncap_l05_h128g16_s44 | nmn_capacity_l05 | ablation | 44 | — | — | — | — | — |
| 26 | 2 | conditional | h128g32 | rppo_nmncap_l05_h128g32_s43 | nmn_capacity_l05 | ablation | 43 | — | — | — | — | — |
| 27 | 2 | conditional | h128g32 | rppo_nmncap_l05_h128g32_s44 | nmn_capacity_l05 | ablation | 44 | — | — | — | — | — |

Stage-2 rows run **only** for cells that pass the stage-1 rule (§5.1). The rest become `cancelled`.

**Launch command** (one per row; `<CELL_FILE>` from §3.1, `<D>` = GPU index):

```bash
/home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
  --config configs/environment/experiment/basic/05-campfire_thermal_10x10.yaml \
  --agent_config configs/models/recurrent_ppo/nmn_capacity_grid/<CELL_FILE> \
  --episodes 10000000 \
  --device cuda:<D> \
  --log-interval 10 \
  --seed <SEED> \
  --tag <TAG> --wandb-name <TAG> \
  --wandb-group nmn_capacity_l05 --wandb-job-type ablation
```

`--seed` on every row is the replication's own mechanism, not a deviation. Give each run its own `--log`
file. Three replication runs launched in the same second without one shared a log. **Post-launch
ground-truth check** (runner): each run's `models/config.yaml` must show its cell's `mod_hidden_size` /
`grouping_size`, the row's `seed`, and `recovery_in_bush_multiplier: 25.0`,
`random_start_body_temp: true`.

### 3.1 Configs to produce (done)

| Cell (runs) | Config (env) | Config (agent) |
|---|---|---|
| h32g8 (1, 10, 11) | `configs/environment/experiment/basic/05-campfire_thermal_10x10.yaml` (unchanged) | `configs/models/recurrent_ppo/nmn_capacity_grid/nmncap_h32_g8.yaml` |
| h32g16 (2, 12, 13) | same | `.../nmncap_h32_g16.yaml` |
| h32g32 (3, 14, 15) | same | `.../nmncap_h32_g32.yaml` |
| h64g8 (4, 16, 17) | same | `.../nmncap_h64_g8.yaml` |
| h64g16 (5, 18, 19) | same | `.../nmncap_h64_g16.yaml` |
| h64g32 (6, 20, 21) | same | `.../nmncap_h64_g32.yaml` |
| h128g8 (7, 22, 23) | same | `.../nmncap_h128_g8.yaml` |
| h128g16 (8, 24, 25) | same | `.../nmncap_h128_g16.yaml` |
| h128g32 (9, 26, 27) | same | `.../nmncap_h128_g32.yaml` |

All nine are generated by `configs/models/recurrent_ppo/nmn_capacity_grid/generate_capacity_arms.py`. Do not
hand-edit them. No new schema keys, no environment config, and no registry setting changes, so there is no
`CONFIG_CRITICAL_SETTINGS.md` entry.

### 3.2 Verification record (2026-10-06, `generate_capacity_arms.py --verify`, CPU)

- **Text diff** of every file against the reference agent (comments stripped): exactly two lines,
  `mod_hidden_size: 16 → H` and `grouping_size: 1 → G`.
- **[1] flattened key diff** vs the reference: exactly
  `{agent.modulation.grouping_size, agent.modulation.mod_hidden_size}` for all nine.
- **[2] resolved config vs ground truth**: train.py's merge order plus this manifest's flags, compared
  with the saved `models/config.yaml` of the replication run `rppo_healrep_l05_t16quad_s42`. The reference
  agent run through the reconstruction reproduces that saved config exactly, apart from the WandB
  group/job type, which validates the reconstruction. Every cell × seed (27 combinations) differs from it
  only in the two keys, `seed`, `tag`, `wandb.name/group/job_type`. So the world, budget and every other
  setting are unchanged since the replication launched.
- **[3] construction** with the trainer's seed-42 init key, for all nine:
  - modulator sizes and the 10 FiLM head shapes are `(H, 128/G)`;
  - the forward pass is finite;
  - the state-dependent gain is constant within each group and differs between groups;
  - a finite, non-zero gradient reaches all 10 heads;
  - the task-network starting weights are bit-identical to the reference.

## 4. Predicted outcomes

- **Most likely (prior from the dossier and replication): null.** No cell leaves the six-run envelope at
  seed 42. The direction is dropped after ~1 day of compute on 9 GPUs.
- **H₁ shape, if true:** the injury effect with the wandering rabbit is ≥ 3 pp above the envelope from
  ~2 M steps on. The effect is stable across checkpoints rather than one late spike. The own scenes show
  the same direction. Survival is unchanged.
- **Plausible failure shapes:** h128 cells train slower early (larger recurrent state, same learning
  rate), or coarser grouping removes the state-dependent part the critic/actor used. That would show up as
  a *smaller* injury effect, which is reported but not advanced (§5.1, "report-only").

## 5. Analysis plan (pre-specified)

**Readout = the replication page's tests, unchanged.** These are the experiment tests at every saved
checkpoint, 30 episodes per scene and starting injury, read as checkpoint-wise means over 2–10 M steps on
the 0.2 M grid (41 checkpoints), with the lag-1-corrected 95 % interval of the Basic Behaviour estimator
(`scripts/analysis/studies/fast_heal_replication/figures.py`, `effect()`). The measures are:

- **Injury effect, no animal**: bush dwell at starting injury 70 minus at 0, no animal in the scene (pp).
- **Injury effect, wandering rabbit**: the same with a harmless wandering rabbit (pp).
- **Predator effect**: bush dwell with a hunting predator minus with no animal, unhurt (pp).
- **Ten-injury dose figures**: bush dwell vs starting injury 0..90, in the injury-grid scenes (no animal /
  rabbit) and the chase scenes.
- **Training view**: ten injury lines across training (the page's B5 view), per cell.

Two scene sets are used, as for level 05 on the page:

- the **thermal-neutral scenes** (air 0 °C, no campfire, start body temperature 0) — the main set;
- the **own level-05 scenes** (built on the training world with a campfire beside the bush).

Performance checks use **survival steps only**:

- in the tests, mean survival ≥ 95 steps (the page's floor; below it a value is reported, not
  interpreted);
- in training, WandB `Episode/Steps`, checkpoint-wise over 2–10 M steps.

Reward is not used anywhere.

**References (already trained, not retrained):** the replication's level-05 runs, seeds 42–44, both agents
(listed in [[FAST_HEAL_REPLICATION]] Launch record; test results under
`results/eval/avoidance/metrics_history_rppo_healrep/l05_{neutral,own,grid,gridchase}/`). The values computed
2026-10-06 from those folders with the page's estimator are:

| Measure (2–10 M mean, pp) | ordinary s42 / s43 / s44 | current modulated s42 / s43 / s44 | six-run envelope |
|---|---|---|---|
| Injury effect, no animal — neutral | 5.3 / 10.3 / 11.7 | 11.0 / 3.7 / 11.5 | 3.7 – 11.7 |
| Injury effect, wandering rabbit — neutral | 0.6 / 9.2 / 8.8 | 8.4 / 3.4 / 7.1 | 0.6 – 9.2 |
| Predator effect — neutral | 43.7 / 48.8 / 46.3 | 49.9 / 36.4 / 57.5 | 36.4 – 57.5 |
| Injury effect, no animal — own | 8.8 / 9.8 / 10.9 | 10.8 / 11.0 / 11.9 | 8.8 – 11.9 |
| Injury effect, wandering rabbit — own | 9.1 / 9.6 / 11.1 | 9.6 / 9.7 / 11.3 | 9.1 – 11.3 |
| Predator effect — own | 28.5 / 18.2 / 35.5 | 27.2 / 30.4 / 22.5 | 18.2 – 35.5 |

All six references are at the 101-step ceiling in the four no-predator scenes.

### 5.1 Stage-1 → stage-2 decision rule (seed 42 only, one value per cell)

At one seed, the only defensible yardstick for "clearly separates" is the variation already observed
between runs that differ only by seed or by agent. A cell **advances to stage 2** only if **all** of the
following hold:

1. **Outside the envelope, with a margin (neutral scenes).** Injury effect with the wandering rabbit
   **≥ 12.2 pp** (envelope maximum 9.2 + 3) **and** injury effect with no animal **≥ 14.7 pp**
   (11.7 + 3).
2. **Its own interval clears the envelope.** For both measures, the cell's lag-1-corrected 95 % lower
   bound is above the envelope maximum (9.2 and 11.7).
3. **The own scenes do not reverse it.** Both own-scene injury effects are ≥ the seed-42
   current-setting modulated agent's own-scene values (10.8 and 9.6 pp).
4. **Survival guard.** Mean test survival ≥ 95 steps in the four no-predator scenes (no animal / wandering
   rabbit × injury 0 / 70). The training `Episode/Steps` mean over 2–10 M steps is not more than 10 %
   below the lowest of the six reference runs' values.

**Why these numbers.** The six reference values of each injury effect have a standard deviation of
about 3.5 pp, and the mean is 8.9 (no animal) / 6.3 (rabbit). A single new run of an agent no different
from the references would exceed the envelope maximum by chance about one time in seven. With the 3 pp
margin, that drops to roughly 5 % per measure under a normal approximation. Requiring both measures lowers
it further, because the two are correlated (the joint rate is not computed). Across nine cells, a
chance pass by at least one cell is still plausible, very roughly one chance in five to one in three.
Stage 2 is the guard against those.

**If no cell passes, the direction is dropped** (user decision). Stage-2 rows are cancelled.

**Report-only (no automatic stage 2; the user decides):**

- a cell whose wandering-rabbit injury effect is ≤ −2.4 pp or whose no-animal effect is ≤ 0.7 pp (envelope
  minimum − 3), i.e. a capacity setting that *removes* injury-driven hiding;
- a predator effect below 31.4 pp in the neutral scenes (envelope minimum 36.4 − 5).

Per-checkpoint view (temporal evolution, mandatory): for each cell, report the share of the 41
checkpoints in which cell − (seed-42 current modulated) is positive, for both injury effects. Also
report whether a pass is carried by a late jump rather than a stable offset. A pass carried by fewer than
half the checkpoints is flagged for the user even if rules 1–4 hold.

### 5.2 Stage-2 readout — "a capacity setting increases the modulator effect" (exploratory)

For each advanced cell, paired by seed against **both** references (the current-setting modulated agent
and the ordinary agent at the same seed):

1. **Fresh seeds carry it.** At seeds 43 **and** 44, the neutral-scene injury effect with the wandering
   rabbit is larger than both references at that seed. Together with seed 42, that makes 3 of 3 seeds.
2. **Size.** The 3-seed mean of (cell − current modulated) for that measure is ≥ 3 pp, about three times
   the replication's modulated-minus-ordinary mean of ~1 pp.
3. **Consistency.** The no-animal injury effect is larger than both references in ≥ 2 of 3 seeds, and the
   own-scene injury effects are larger than the current modulated agent's in ≥ 2 of 3 seeds.
4. **Survival guard** (rule 4 of §5.1) holds at every seed.

If 1–4 hold, the verdict reads "this setting is a candidate for a confirmatory test", not "capacity
increases the modulator effect". Under no effect, winning 3 of 3 paired comparisons happens 1 time in 8
for each comparison. Three seeds cannot reach conventional significance, and seed 42 was used for
selection. A claim needs a separate, pre-registered confirmatory run on the selected cell only, with ≥ 5
fresh seeds.

### 5.3 Secondary and diagnostic readouts (no decision weight)

- The ten-injury dose figures for each cell beside its references (grid and chase scenes).
- The modulator's output split into the part that changes over time and the part that differs only
  between units (the dossier's 85 % constant measure). This asks whether a larger or coarser modulator
  carries more state-dependent signal. Tooling: `scripts/analysis/nmn/` (shape-agnostic; see §7).
- Training survival curves (`Episode/Steps`) for all cells against the six references.

### 5.4 Eval sweep specs (prepared, not launched)

Same probe folders, conditions, 30 episodes, x axis and measures as the healrep level-05 specs:

| Scene set | Stage 1 (9 runs) | Stage 2 (18 runs; delete rows of cells not advanced) |
|---|---|---|
| neutral (main) | `configs/eval_sweeps/nmncap/nmncap_l05_neutral_stage1_rppo.yaml` | `..._neutral_stage2_rppo.yaml` |
| own | `configs/eval_sweeps/nmncap/nmncap_l05_own_stage1_rppo.yaml` | `..._own_stage2_rppo.yaml` |
| injury grid (dose) | `configs/eval_sweeps/nmncap/nmncap_l05_grid_stage1_rppo.yaml` | `..._grid_stage2_rppo.yaml` |
| chase grid (dose) | `configs/eval_sweeps/nmncap/nmncap_l05_gridchase_stage1_rppo.yaml` | `..._gridchase_stage2_rppo.yaml` |

Output: `results/eval/avoidance/metrics_history_rppo_nmncap/l05_<set>/`. Run paths are globs on the planned
tag (`results/JAX_RecurrentPPO/*_<TAG>`). `run_sweep.py` refuses a glob that matches 0 or 2+ folders, so
after a relaunch the live folder must be pinned by hand. The nodes (109, 110) are placeholders; confirm
they are free before running. The figure script of the replication page is hard-coded to the healrep runs.
The stage-1 readout needs a small study script that applies `figures.effect()` to these folders. That is
analysis-phase work, not a launch blocker.

## 6. Failure-mode catalog (decided in advance)

| Observation | Counts as |
|---|---|
| NaN / divergence / critic explosion in a cell | A failed **run**, not a refutation. Relaunch once with the same seed. A second failure is reported as "this setting is unstable at level 05", and the cell does not advance. |
| A cell below the survival floor (rule 4) | Its behaviour numbers are reported, not interpreted. It does not advance. |
| A pass carried by the last few checkpoints only | Flagged (§5.1). The user decides; the default is not to advance. |
| The node dies mid-run (as 113 did) | A failed run. Relaunch from scratch with the same tag on another node; the dead folder is excluded and the eval glob is pinned. |
| Effect visible by 10 M but still rising | Insufficient horizon is **not** assumed. The design is the replication's 10 M; a longer-horizon follow-up would be a new design. |
| Every cell inside the envelope | The pre-registered null for this direction: drop it (user rule). Reporting "no cell separated at seed 42" is the result, with the explicit caveat that effects under ~3 pp were not detectable. |

## 7. Code hazards checked (2026-10-06, HEAD of `v5.0`)

None blocks the launch. Findings:

1. **Divisibility / width.** `NeuromodulatorRNN` computes `ceil(128 / G)` groups, repeats and truncates to
   128. 8, 16 and 32 divide 128 exactly. `ActorCriticRNN` asserts that every FiLM target (encoder, actor,
   critic, task GRU) is `hidden_size` = 128 wide before building the modulator.
2. **Untested path.** No test under `tests/` builds the rPPO modulator with `grouping_size > 1` or
   `mod_hidden_size` ≠ 8. The generator's `--verify` (construction, forward, gradient, grouping structure)
   is the only coverage. Recommended, not required: a unit test via `developer`.
3. **Rollout buffer / modulator state.** The trainer stores the `ModulatorOutput` pytree and the
   `(task_h, mod_h)` state from `initial_state()`. All shapes derive from the model. The FiLM outputs are
   128 wide after the repeat at every G, and `mod_h` is `(envs, H)`. No hard-coded 16. The memory impact
   is negligible.
4. **Trajectory store.** Records no modulator outputs, so its schema is unaffected.
5. **Checkpoint restore.** Rebuilds from the run's saved config and hard-fails on any key/shape mismatch
   (`assert_restored_tree_matches` in `src/utils/trajectory_store.py`). A wrong config fails loudly; it
   cannot silently build the wrong model.
6. **Analysis tools (`scripts/analysis/nmn/`).** `replay.py`, `mod_distribution.py` and `freeze.py` read
   sizes from the constructed model. `freeze.py` routes the frozen target through the per-unit baseline
   precisely so that G > 1 works. `spectral_bound.py` takes `grouping_size` from the run config. It uses
   `mod_cfg.get("grouping_size", 1)`, a fallback default (a project-rule violation, harmless here because
   every saved config carries the key). Docstrings say "16 in these runs" and are only prose.
7. **Stale comment in the reference file.** Its header says "Seed is config-owned … no --seed is passed at
   launch", but the replication did pass `--seed`. The new files state the real mechanism. The reference
   file is generated and is not edited here.

## 8. Results

*(empty until stage 1 is trained and tested)*

## 9. Conclusions

*(empty)*
