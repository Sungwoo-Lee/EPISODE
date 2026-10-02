---
id: 20260909_1504_env_parameter_surface_and_degenerate_traits
date: 2026-09-09
time: "15:04"
folder: env_entities
tags: [config, design, learned_lesson]
summary: "The grid world has 65 settings; only 15 have ever been tested as drivers of bush hiding. Three of the five per-episode predator traits are declared distributional but written degenerate in every live config, so the sampler runs each episode and returns a constant. Most untested factors — spatial arrangement, per-event damage — need no new training."
related: ["20260623_0143_per_episode_count_variance_masking", "20260630_1630_predator_params_per_episode_ranges", "20260819_1947_basic04_predator_combinatorics_fully_latent"]
session_origin: claude_code
session_label: "hiding-artifact inventory + Hiding Factor Atlas"
importance: high
status: settled
valid_until: null
confidence: high
supersedes: []
raw_source: claude_data/.claude/projects/-media-nas01-projects-Interoceptive-AI-grid-world-pain/745adcad-de68-49fe-bbd5-e1086dec05a8.jsonl
raw_completeness: full
---

# The environment's full parameter surface: 65 settings, 15 tested, and three switched-off predator traits

## Key conclusion

A full read of the config chain for the reference agent (the arm of the resting-bonus sweep where
resting earns no extra healing) turns up **65 distinct environment settings**. The published hiding
studies have tested **15** of them as drivers of bush hiding — the share of an episode's steps the
agent spends standing in a bush.

The useful way to sort the other 50 is by **cadence**: whether the environment rerolls the value
before every episode. A rerolled value is assigned independently of the agent, so its effect is
causally identified, and it is already recorded in the per-episode table of the trajectory store —
free to analyse from the million-episode collection on disk. A value pinned in the config file
cannot be studied without training another agent. That single distinction prices every open question.

Three findings came out of the read:

1. **Spatial arrangement is untouched.** Every tested factor is a *count* or a *trait* — how many
   bushes, how far a predator sees. Nothing tests *where things are*, although every position is
   redrawn each episode and recorded at every step.
2. **Per-event damage is untouched.** A predator's bite is drawn afresh from `[15, 120]` on every
   collision — an eightfold range — and no analysis separates a graze from a near-fatal blow.
3. **Three of the five per-episode predator traits are switched off.** The config schema declares
   five animal fields as distributional (a `[low, high]` pair sampled at reset), but only
   `detection_range` and `max_stamina` are ever given a real range in this config line.
   `stamina_recovery_rate`, `hunt_stamina_threshold` and `lose_interest_multiplier` are written
   as degenerate `[x, x]` everywhere, so the sampling machinery runs each episode and returns a
   constant.

## Evidence, measurements, facts

- Config chain read in resolution order: `04-restprem_a01.yaml` → `04-jump_attack_10x10.yaml` →
  `03-random_init_10x10.yaml` → `configs/environment/default.yaml`.
- Rerolled every episode in this world: predator count `[0,2]`, rabbit count `[0,2]`,
  `detection_range [1,7]`, `max_stamina [30,150]`, `attack_range [2,3]`, `attack_delay [1,3]`,
  bush count `[4,10]`, rock count `[6,12]`, food count `[1,4]`, ambush count `[2,12]`,
  start injury `[0,100]`, start nutrition `[0,100]`, every entity position
  (`random_start_pos: true`), and the two-channel odour draw (`properties_std` 0.3 on channels 1
  and 2 for both predator and rabbit).
- Degenerate in every live config: `stamina_recovery_rate: [1,1]`,
  `hunt_stamina_threshold: [0.7,0.7]`, `lose_interest_multiplier: [1.5,1.5]`,
  `move_interval: [1,1]`. Real ranges exist **only** in three archived configs —
  `archive/hypervigilance/03-sameProp_R3_predatorDistributional.yaml`,
  `archive/hypervigilance/04-sameProp_R4_chasingRabbit.yaml`,
  `archive/v2_smoke/02-entities-distributional.yaml` — using
  `stamina_recovery_rate [0.25,2.0]`, `hunt_stamina_threshold [0.3,0.9]`,
  `lose_interest_multiplier [1.0,3.0]`.
- `lose_interest_multiplier` is the one of the three whose mechanism points most directly at
  hiding: it is chase persistence as a multiple of the detection range, i.e. how long the agent must
  stay in cover before coming out is safe. It is the closest thing this environment has to a
  hiding-duration knob, and it is switched off.
- `attack_success_rate: 0.5` is a plain parameter, not a per-episode draw — but its realised
  outcome varies on every pounce, and a miss lands the predator on a random adjacent cell rather
  than on the agent. Recoverable from the recorded hit flags and positions; never analysed.
- Settings fixed in this world but varied by other studies: the sensory block (the fourteen-arm
  ladder), `recovery_accel_rate` (the ten-arm resting-bonus sweep), and `blocks_animals` on the
  bush, whose `true`/`false` sibling configs differ in exactly that one key.
- `perceptual_noise.enabled` is `false` here. When on, several modalities scale their noise by
  the agent's injury level — a mechanism that would couple wound and hiding directly, and that the
  next curriculum level turns on.
- Not measured: this is an inventory. No claim is made that any listed parameter does or does not
  move hiding.

## Decisions and actions

- Published the inventory as a page: https://claude.ai/code/artifact/36369fd2-66a7-4b66-8077-21f0c83282cd
  with the companion doc at `docs/experiments/active/trajectory_factors/hiding_factor_atlas.md`
  (commit `0de7115f`).
- Recommended order of attack if the hiding line continues: spatial arrangement first, then
  per-event damage — both free from the existing store — and the three switched-off chase traits
  last, since enabling them changes the training world and costs a run.
- Extends [[20260630_1630_predator_params_per_episode_ranges]], which wired these fields and noted
  that the remaining float fields were "one YAML edit from randomizing". This insight records that
  three of them still have not had that edit, and that the ranges which do exist are archived.

## Open questions and follow-ups

- Whether to enable the three degenerate traits in a future arm, and if so which — the chase-persistence
  one has the most direct mechanism.
- Whether ambush-predator resources regenerate: `max_consumption: -1` with
  `regeneration_delay: 20` reads as never-depletes, and a prior review verified "never respawn".
  Consistent, but the two statements were established separately and have not been reconciled in code.
- The odour draw carries two independent quantities — the channel *difference* (predator-likeness,
  analysed) and the channel *sum* (sheer intensity, only partly analysed). The confusability of the
  specific predator/rabbit pair drawn in a given episode has never been computed at all.

## References

- Page: https://claude.ai/code/artifact/36369fd2-66a7-4b66-8077-21f0c83282cd
- Companion doc: `docs/experiments/active/trajectory_factors/hiding_factor_atlas.md`
- Schema: `docs/environment/02_config_schema.md` (Distributional fields; per-episode count ranges),
  `docs/environment/TRAJECTORY_STORE_SCHEMA.md` §3.1–3.2 (the recorded draw columns)
- Prior art: [[20260630_1630_predator_params_per_episode_ranges]],
  [[20260623_0143_per_episode_count_variance_masking]],
  [[20260819_1947_basic04_predator_combinatorics_fully_latent]]
- Commit: `0de7115f`
- Raw conversation: synced via `./sync-agent-data.sh claude push`. To read on another node:
  `./sync-agent-data.sh claude pull`, then either `claude --resume 745adcad-de68-49fe-bbd5-e1086dec05a8` or
  `python scripts/claude/claude_jsonl_to_md.py <jsonl> /tmp/<id>.md`.

<!-- BACKLINKS — auto-generated by scripts/regen_wiki_graph.py; do not edit -->
## Backlinks
- _no inbound links yet_
<!-- END BACKLINKS -->
