#!/bin/bash
set -euo pipefail

# This script is launched via `run_command.py` which no longer cds to the
# project root or activates a conda env. Both responsibilities live here.
cd /media/nas01/projects/Interoceptive-AI/grid_world_pain

#
# train_command-agent.sh
# ----------------------
# Launch script edited ONLY by the `training-runner` agent.
# The user's manual launch script is `train_command-new.sh` — the agent never touches that.
#
# ---------------------------------------------------------------------------
# Config-owns-values convention
# ---------------------------------------------------------------------------
# --num-envs, --seed, and --checkpoint-frequency are CONFIG-OWNED —
# configs/train/default.yaml is authoritative for these three values (Dreamer
# reads it directly; RecurrentPPO additionally layers configs/train/recurrent_ppo.yaml
# on top, overriding checkpoint_frequency to 200000 and log_interval to 500 —
# both already correct in-config). Standard launches must NOT pass these
# three flags on the CLI; do so only as an intentional, one-off deviation,
# and flag it to the user when you do (this is the root-cause fix for the
# --num-envs 16 bug that silently trained 6 runs at the wrong parallelism).
#
# --episodes MUST always be passed explicitly on every launch — the config's
# episodes: 100 is a smoke-test safety placeholder, not a real budget.
#
# Minimal config-owned launch form:
#   /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#     --config <env_config.yaml> \
#     --agent_config <agent_config.yaml> \
#     --episodes <int> \
#     --device cuda:N \
#     --log-interval <int> \
#     --wandb-group <str> --wandb-job-type <str> \
#     --wandb-name <str> --tag <str>
# ---------------------------------------------------------------------------
# train.py CLI arguments (full list — agent fills the relevant ones below)
# ---------------------------------------------------------------------------
# Required:
#   --agent_config <path>     Path to agent/model config YAML (e.g., configs/models/dreamer_v3/dreamer_v3.yaml)
#
# Common (env / training):
#   --config <path>           Base env config YAML (single-stage)
#   --configs-dir <dir>       Directory of stage YAMLs for continual learning (mutually exclusive with --config)
#   --continual-schedule <p>  Schedule YAML (required when --configs-dir is used)
#   --episodes <int>          Number of episodes
#   --total-timesteps <int>   Total timesteps (overrides --episodes if set)
#   --seed <int>              Random seed
#   --num-envs <int>          Parallel envs
#   --num-steps <int>         Steps per iteration (rollout length)
#   --hidden-size <int>       Hidden layer size
#   --lr <float>              Learning rate (overrides agent config)
#   --device <str>            'cuda:N' / 'gpu' / 'cpu'
#   --no-satiation            Disable satiation
#   --no-overeating-death     Disable death by overeating
#   --checkpoint-frequency N  Save checkpoint every N evals
#   --load-checkpoint <path>  Resume from checkpoint
#   --results-dir <path>      Custom results directory
#
# WandB filtering (see convention block below):
#   --wandb-project <str>     Default: 'grid_world_pain' (leave unset; default applies)
#   --wandb-entity <str>      Default: 'sungwoolee'      (leave unset; default applies)
#   --wandb-group <str>       Experiment family
#   --wandb-job-type <str>    Operational category
#   --wandb-name <str>        Run display name in WandB web
#   --wandb-resume-id <str>   Resume an existing WandB run by id
#   --no-wandb                Disable WandB logging entirely
#
# Logging / dev:
#   --tag <str>               Project-internal tag (drives results/JAX_<algo>/<ts>_<tag>/ and logs/<ts>_<tag>.log)
#   --log-interval <int>      WandB logging interval (iterations)
#   --log-accumulate / --no-log-accumulate
#                             Accumulate episode metrics across the log interval (default: accumulate)
#   --quiet                   Suppress stdout / progress bar
#   --debug                   Verbose step-by-step progress
#   --profile                 jax.profiler trace; forces --no-wandb + --quiet
#
# ---------------------------------------------------------------------------
# WandB-field convention (the agent fills all four below)
# ---------------------------------------------------------------------------
#   --wandb-group     experiment family — top dir under configs/environment/experiment/
#                       e.g. 'basic', 'hypervigilance', 'noise'
#
#   --wandb-job-type  operational category. Default 'prod'.
#                     Set to 'debug' / 'test' / 'pilot' / 'ablation' only when the user says so.
#                     (Algorithm is already filterable via Config.agent.algorithm —
#                      job-type is reserved for ops metadata.)
#
#   --wandb-name      run display name in WandB web. Format:
#                       <algo>_<config_stem>_n<node>            (single seed)
#                       <algo>_<config_stem>_s<seed>_n<node>    (seed override)
#                     e.g. 'dreamer_v3_00-5X5_NoPred_n113'
#
#   --tag             identical to --wandb-name. Drives local paths:
#                       results/JAX_<algo>/<ts>_<tag>/
#                       logs/<ts>_<tag>.log
#                     and shows up as Config.tag in the WandB run config.
#
# Defaults from configs/logger/wandb.yaml: project=grid_world_pain, entity=sungwoolee.
# The agent leaves --wandb-project and --wandb-entity unset so those defaults apply.
# ---------------------------------------------------------------------------

# hunger_gated_lindecay sweep — 2026-06-20 through 2026-06-22
# 10 recurrent_ppo runs across nodes 101/102/103/110/106/108, seed 42, ~10M episodes, fresh-init.
# wandb-group: hunger_gated_lindecay, job-type: prod
# Launched via CIFS-bypass /tmp scripts; this file is the audit record.
#
# Run 01: rppo_hg01_s0_sig0_dp1_s42      — node 108, cuda:0  (held anchor; launched 2026-06-22)
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/hunger_gated_lindecay/01-s0_sig0.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --device cuda:0 \
#   --num-envs 16 \
#   --episodes 10000000 \
#   --seed 42 \
#   --wandb-group hunger_gated_lindecay \
#   --wandb-job-type prod \
#   --wandb-name rppo_hg01_s0_sig0_dp1_s42 \
#   --tag rppo_hg01_s0_sig0_dp1_s42
#
# Run 02: rppo_hg02_s0.05_sig0_dp1_s42   — node 101, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/hunger_gated_lindecay/02-s0.05_sig0.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --device cuda:0 \
#   --num-envs 16 \
#   --episodes 10000000 \
#   --seed 42 \
#   --wandb-group hunger_gated_lindecay \
#   --wandb-job-type prod \
#   --wandb-name rppo_hg02_s0.05_sig0_dp1_s42 \
#   --tag rppo_hg02_s0.05_sig0_dp1_s42

# ---------------------------------------------------------------------------
# basic_curriculum continual-learning run — 2026-06-22
# RecurrentPPO, 5-stage schedule (00→04 basic configs), ~10M total steps
# (1M/1M/2M/2M/4M), node 106 cuda:0, wandb-group: basic_curriculum
# Re-launch after BMState stage-transition NameError fix in train.py
# ---------------------------------------------------------------------------
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --configs-dir configs/environment/experiment/basic \
#   --continual-schedule configs/continual/basic_curriculum_schedule.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --num-envs 128 \
#   --device cuda:0 \
#   --wandb-group basic_curriculum \
#   --wandb-job-type prod \
#   --wandb-name rppo_basic_curriculum_n106 \
#   --tag rppo_basic_curriculum_n106

# ---------------------------------------------------------------------------
# basic_curriculum long-L4 continual run — 2026-06-23
# RecurrentPPO (unmodulated), 5-stage schedule (longL4 variant), stage 4 runs ~1B eps
# (1M/1M/2M/2M then stage-4 runs from 6M to 1B — manually stopped by user).
# Node 114, cuda:1, wandb-group: basic_curriculum
# CIFS-bypass: launched via /tmp script — this file is the audit record.
# ---------------------------------------------------------------------------
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --configs-dir configs/environment/experiment/basic \
#   --continual-schedule configs/continual/basic_curriculum_schedule_longL4.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --num-envs 128 \
#   --device cuda:1 \
#   --wandb-group basic_curriculum \
#   --wandb-job-type prod \
#   --wandb-name rppo_basic_curriculum_longL4 \
#   --tag rppo_basic_curriculum_longL4

# ---------------------------------------------------------------------------
# basic_curriculum long-L4 continual run — FiLM/NMN modulated — 2026-06-24
# RecurrentPPO + NMN FiLM modulator (per-neuron γ/β, temp_clip [0.5, 5.0])
# 5-stage longL4 schedule: stages 0-3 = 1M/1M/2M/2M eps; stage 4 far-sight
# runs from 6M to 1B eps (manually stopped). Comparison target: unmod run oq2vvh8g.
# Node 114, cuda:2, wandb-group: basic_curriculum
# CIFS-bypass: launched via /tmp script — this file is the audit record.
# ---------------------------------------------------------------------------
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --configs-dir configs/environment/experiment/basic \
#   --continual-schedule configs/continual/basic_curriculum_schedule_longL4.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_nmn_film_g1_tempceil5.yaml \
#   --num-envs 128 \
#   --device cuda:2 \
#   --wandb-group basic_curriculum \
#   --wandb-job-type prod \
#   --wandb-name rppo_nmn_film_curric_longL4_n114 \
#   --tag rppo_nmn_film_curric_longL4_n114

# ---------------------------------------------------------------------------
# basic standalone — random-init 10x10 — 2026-06-27
# RecurrentPPO (unmodulated), single-config from scratch, 10M steps.
# 05-random_init_10x10: per-episode randomised predator/food/bush/rock counts,
# random start nutrition [0,100] + injury [0,100], full-grid spawn, clean smell.
# Standalone (NOT continual). Level 4 basic converged ~3.6M steps → 10M gives margin.
# checkpoint_frequency in episodes: ~1000 eps ≈ 200k steps at ~200 avg steps/ep.
# Node 112, cuda:0, wandb-group: basic
# CIFS-bypass: launched via /tmp script — this file is the audit record.
# ---------------------------------------------------------------------------
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/05-random_init_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --num-envs 16 \
#   --total-timesteps 10000000 \
#   --checkpoint-frequency 1000 \
#   --device cuda:0 \
#   --wandb-group basic \
#   --wandb-job-type prod \
#   --wandb-name rppo_basic05_randinit_n112 \
#   --tag rppo_basic05_randinit_n112

# ---------------------------------------------------------------------------
# NMN FiLM grouping_size screen — 2026-06-27
# RecurrentPPO + NMN FiLM modulator, 8-point group-count curve (grouping_size 1→128)
# Env: 04-far_sight_predator_10x10 (far-sight L4, from scratch, no curriculum)
# Budget: 10M episodes, num_envs=128, seed=42, checkpoint_frequency=100000
# temp_clip: [0.5, 10.0] (non-binding ceiling; de-confounds temperature rail)
# Nodes 106–109, 2 GPUs each; wandb-group: basic_curriculum, job-type: prod
# Design doc: docs/experiments/active/basic_curriculum/NMN_FILM_GROUPING_SCREEN.md
# CIFS-bypass: launched via /tmp scripts — this file is the audit record.
# ---------------------------------------------------------------------------
# Run 1: rppo_nmn_film_g1_screen_s42   — node 106, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-far_sight_predator_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_nmn_film_g1_screen.yaml \
#   --num-envs 128 --episodes 10000000 --checkpoint-frequency 100000 \
#   --log-interval 10 --device cuda:0 --seed 42 \
#   --wandb-group basic_curriculum --wandb-job-type prod \
#   --wandb-name rppo_nmn_film_g1_screen_s42 \
#   --tag rppo_nmn_film_g1_screen_s42
#
# Run 2: rppo_nmn_film_g2_screen_s42   — node 106, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-far_sight_predator_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_nmn_film_g2_screen.yaml \
#   --num-envs 128 --episodes 10000000 --checkpoint-frequency 100000 \
#   --log-interval 10 --device cuda:1 --seed 42 \
#   --wandb-group basic_curriculum --wandb-job-type prod \
#   --wandb-name rppo_nmn_film_g2_screen_s42 \
#   --tag rppo_nmn_film_g2_screen_s42
#
# Run 3: rppo_nmn_film_g4_screen_s42   — node 110, cuda:0 (reassigned from 107; 107 had no NAS mount)
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-far_sight_predator_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_nmn_film_g4_screen.yaml \
#   --num-envs 128 --episodes 10000000 --checkpoint-frequency 100000 \
#   --log-interval 10 --device cuda:0 --seed 42 \
#   --wandb-group basic_curriculum --wandb-job-type prod \
#   --wandb-name rppo_nmn_film_g4_screen_s42 \
#   --tag rppo_nmn_film_g4_screen_s42
#
# Run 4: rppo_nmn_film_g8_screen_s42   — node 110, cuda:1 (reassigned from 107; 107 had no NAS mount)
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-far_sight_predator_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_nmn_film_g8_screen.yaml \
#   --num-envs 128 --episodes 10000000 --checkpoint-frequency 100000 \
#   --log-interval 10 --device cuda:1 --seed 42 \
#   --wandb-group basic_curriculum --wandb-job-type prod \
#   --wandb-name rppo_nmn_film_g8_screen_s42 \
#   --tag rppo_nmn_film_g8_screen_s42
#
# Run 5: rppo_nmn_film_g16_screen_s42  — node 108, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-far_sight_predator_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_nmn_film_g16_screen.yaml \
#   --num-envs 128 --episodes 10000000 --checkpoint-frequency 100000 \
#   --log-interval 10 --device cuda:0 --seed 42 \
#   --wandb-group basic_curriculum --wandb-job-type prod \
#   --wandb-name rppo_nmn_film_g16_screen_s42 \
#   --tag rppo_nmn_film_g16_screen_s42
#
# Run 6: rppo_nmn_film_g32_screen_s42  — node 108, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-far_sight_predator_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_nmn_film_g32_screen.yaml \
#   --num-envs 128 --episodes 10000000 --checkpoint-frequency 100000 \
#   --log-interval 10 --device cuda:1 --seed 42 \
#   --wandb-group basic_curriculum --wandb-job-type prod \
#   --wandb-name rppo_nmn_film_g32_screen_s42 \
#   --tag rppo_nmn_film_g32_screen_s42
#
# Run 7: rppo_nmn_film_g64_screen_s42  — node 109, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-far_sight_predator_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_nmn_film_g64_screen.yaml \
#   --num-envs 128 --episodes 10000000 --checkpoint-frequency 100000 \
#   --log-interval 10 --device cuda:0 --seed 42 \
#   --wandb-group basic_curriculum --wandb-job-type prod \
#   --wandb-name rppo_nmn_film_g64_screen_s42 \
#   --tag rppo_nmn_film_g64_screen_s42
#
# Run 8: rppo_nmn_film_g128_screen_s42 — node 109, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-far_sight_predator_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_nmn_film_g128_screen.yaml \
#   --num-envs 128 --episodes 10000000 --checkpoint-frequency 100000 \
#   --log-interval 10 --device cuda:1 --seed 42 \
#   --wandb-group basic_curriculum --wandb-job-type prod \
#   --wandb-name rppo_nmn_film_g128_screen_s42 \
#   --tag rppo_nmn_film_g128_screen_s42
#
# Run 03: rppo_hg03_s0.1_sig0_dp1_s42    — node 101, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/hunger_gated_lindecay/03-s0.1_sig0.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --device cuda:1 \
#   --num-envs 16 \
#   --episodes 10000000 \
#   --seed 42 \
#   --wandb-group hunger_gated_lindecay \
#   --wandb-job-type prod \
#   --wandb-name rppo_hg03_s0.1_sig0_dp1_s42 \
#   --tag rppo_hg03_s0.1_sig0_dp1_s42
#
# Run 04: rppo_hg04_s0.25_sig0_dp1_s42   — node 102, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/hunger_gated_lindecay/04-s0.25_sig0.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --device cuda:0 \
#   --num-envs 16 \
#   --episodes 10000000 \
#   --seed 42 \
#   --wandb-group hunger_gated_lindecay \
#   --wandb-job-type prod \
#   --wandb-name rppo_hg04_s0.25_sig0_dp1_s42 \
#   --tag rppo_hg04_s0.25_sig0_dp1_s42
#
# Run 05: rppo_hg05_s0.5_sig0_dp1_s42    — node 102, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/hunger_gated_lindecay/05-s0.5_sig0.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --device cuda:1 \
#   --num-envs 16 \
#   --episodes 10000000 \
#   --seed 42 \
#   --wandb-group hunger_gated_lindecay \
#   --wandb-job-type prod \
#   --wandb-name rppo_hg05_s0.5_sig0_dp1_s42 \
#   --tag rppo_hg05_s0.5_sig0_dp1_s42
#
# Run 06: rppo_hg06_s0.1_sig0.2_dp1_s42  — node 103, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/hunger_gated_lindecay/06-s0.1_sig0.2.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --device cuda:0 \
#   --num-envs 16 \
#   --episodes 10000000 \
#   --seed 42 \
#   --wandb-group hunger_gated_lindecay \
#   --wandb-job-type prod \
#   --wandb-name rppo_hg06_s0.1_sig0.2_dp1_s42 \
#   --tag rppo_hg06_s0.1_sig0.2_dp1_s42
#
# Run 07: rppo_hg07_s0.25_sig0.2_dp1_s42 — node 103, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/hunger_gated_lindecay/07-s0.25_sig0.2.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --device cuda:1 \
#   --num-envs 16 \
#   --episodes 10000000 \
#   --seed 42 \
#   --wandb-group hunger_gated_lindecay \
#   --wandb-job-type prod \
#   --wandb-name rppo_hg07_s0.25_sig0.2_dp1_s42 \
#   --tag rppo_hg07_s0.25_sig0.2_dp1_s42
#
# Run 08: rppo_hg08_s0.5_sig0.2_dp1_s42  — node 110, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/hunger_gated_lindecay/08-s0.5_sig0.2.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --device cuda:0 \
#   --num-envs 16 \
#   --episodes 10000000 \
#   --seed 42 \
#   --wandb-group hunger_gated_lindecay \
#   --wandb-job-type prod \
#   --wandb-name rppo_hg08_s0.5_sig0.2_dp1_s42 \
#   --tag rppo_hg08_s0.5_sig0.2_dp1_s42
#
# Run 09: rppo_hg09_s0.1_sig0.4_dp1_s42  — node 110, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/hunger_gated_lindecay/09-s0.1_sig0.4.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --device cuda:1 \
#   --num-envs 16 \
#   --episodes 10000000 \
#   --seed 42 \
#   --wandb-group hunger_gated_lindecay \
#   --wandb-job-type prod \
#   --wandb-name rppo_hg09_s0.1_sig0.4_dp1_s42 \
#   --tag rppo_hg09_s0.1_sig0.4_dp1_s42
#
# Run 10: rppo_hg10_s0.5_sig0.4_dp1_s42  — node 106, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/hunger_gated_lindecay/10-s0.5_sig0.4.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --device cuda:1 \
#   --num-envs 16 \
#   --episodes 10000000 \
#   --seed 42 \
#   --wandb-group hunger_gated_lindecay \
#   --wandb-job-type prod \
#   --wandb-name rppo_hg10_s0.5_sig0.4_dp1_s42 \
#   --tag rppo_hg10_s0.5_sig0.4_dp1_s42

# ---------------------------------------------------------------------------
# basic standalone — random-init 10x10 — RE-LAUNCH 2026-06-27
# PRIOR LAUNCH (same date) used --total-timesteps 10000000 which caused exit in ~45s
# (single-config mode reads episodes default = 100 → ran 100 eps and stopped).
# FIX: replaced with --episodes 10000000 (episode-budget convention).
# RecurrentPPO (unmodulated), single-config from scratch, 10M episodes.
# 05-random_init_10x10: per-episode randomised predator/food/bush/rock counts,
# random start nutrition [0,100] + injury [0,100], full-grid spawn, clean smell.
# Standalone (NOT continual). Level 4 basic converged ~3.6M steps → 10M gives margin.
# Node 112, cuda:0, wandb-group: basic
# Supersedes defunct WandB run k9wyijj3.
# CIFS-bypass: launched via /tmp script — this file is the audit record.
# ---------------------------------------------------------------------------
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/05-random_init_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --num-envs 16 \
#   --episodes 10000000 \
#   --checkpoint-frequency 100000 \
#   --device cuda:0 \
#   --log-interval 50 \
#   --wandb-group basic \
#   --wandb-job-type prod \
#   --wandb-name rppo_basic05_randinit_n112 \
#   --tag rppo_basic05_randinit_n112

# ---------------------------------------------------------------------------
# basic standalone — random-init 10x10 + FULLY RANDOMISED PREDATOR — 2026-06-30
# RecurrentPPO (unmodulated), single-config from scratch, 10M episodes.
# 05-random_init_10x10 (commit 033c255): predator/rabbit count 0-2, random start
# nutrition/injury, AND per-episode predator behaviour — detection_range [1,7],
# move_interval [1,3], attack_delay [1,3]. Fully randomised predator behaviour
# distinguishes this run from the prior basic-05 run on node 112 (WandB ga5fkr1q).
# Standalone (NOT continual). Episode budget 10M (manual stop convention).
# Node 110, cuda:0, wandb-group: basic
# CIFS-bypass: launched via /tmp script — this file is the audit record.
# ---------------------------------------------------------------------------
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/05-random_init_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --num-envs 16 \
#   --episodes 10000000 \
#   --checkpoint-frequency 100000 \
#   --device cuda:0 \
#   --log-interval 50 \
#   --wandb-group basic \
#   --wandb-job-type prod \
#   --wandb-name rppo_basic05_randpred_n110 \
#   --tag rppo_basic05_randpred_n110

# ---------------------------------------------------------------------------
# basic05_variants — 4-run predator-pressure sweep — 2026-06-30
# RecurrentPPO (unmodulated), single-config (standalone, NOT continual), 10M episodes each.
# Four variants of 05-random_init_10x10 testing increased predator difficulty:
#   v1 (01-more_hiding_predators): more ambush predators (count_high 4→12) — node 108 cuda:0
#   v2 (02-relentless_stamina):    predator max_stamina [30,150] (sometimes chases to starvation) — node 108 cuda:1
#   v3 (03-fast_move_interval):    predator move_interval fixed 1 (always full-speed) — node 109 cuda:0
#   v4 (04-all_combined):          all three factors combined — node 109 cuda:1
# num_envs=16, checkpoint_frequency=100000, log_interval=50
# wandb-group: basic05_variants, job-type: prod
# CIFS-bypass: launched via /tmp scripts — this file is the audit record.
# NOTE: Runs 1 and 2 (node 108) were SKIPPED on initial launch (2026-06-30) — nas01
#   CIFS share not mounted on node 108 at that time. User remounted nas01 on node 108
#   (confirmed 52T free). RE-LAUNCHED 2026-06-30 via CIFS-bypass /tmp scripts.
# ---------------------------------------------------------------------------
# Run 1: rppo_basic05v1_hiding_n108 — node 108, cuda:0 — RE-LAUNCHED 2026-06-30
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic05_variants/01-more_hiding_predators.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --num-envs 16 \
#   --episodes 10000000 \
#   --checkpoint-frequency 100000 \
#   --device cuda:0 \
#   --log-interval 50 \
#   --wandb-group basic05_variants \
#   --wandb-job-type prod \
#   --wandb-name rppo_basic05v1_hiding_n108 \
#   --tag rppo_basic05v1_hiding_n108
#
# Run 2: rppo_basic05v2_stamina_n108 — node 108, cuda:1 — RE-LAUNCHED 2026-06-30
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic05_variants/02-relentless_stamina.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --num-envs 16 \
#   --episodes 10000000 \
#   --checkpoint-frequency 100000 \
#   --device cuda:1 \
#   --log-interval 50 \
#   --wandb-group basic05_variants \
#   --wandb-job-type prod \
#   --wandb-name rppo_basic05v2_stamina_n108 \
#   --tag rppo_basic05v2_stamina_n108

# Run 3: rppo_basic05v3_fastmove_n109 — node 109, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic05_variants/03-fast_move_interval.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --num-envs 16 \
#   --episodes 10000000 \
#   --checkpoint-frequency 100000 \
#   --device cuda:0 \
#   --log-interval 50 \
#   --wandb-group basic05_variants \
#   --wandb-job-type prod \
#   --wandb-name rppo_basic05v3_fastmove_n109 \
#   --tag rppo_basic05v3_fastmove_n109

# Run 4: rppo_basic05v4_all_n109 — node 109, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic05_variants/04-all_combined.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --num-envs 16 \
#   --episodes 10000000 \
#   --checkpoint-frequency 100000 \
#   --device cuda:1 \
#   --log-interval 50 \
#   --wandb-group basic05_variants \
#   --wandb-job-type prod \
#   --wandb-name rppo_basic05v4_all_n109 \
#   --tag rppo_basic05v4_all_n109

# ---------------------------------------------------------------------------
# Run 5: rppo_basic05v5_allnoise_n110 — node 110, cuda:1 — 2026-07-02
# basic05_variants/05-all_combined_noise: extends variant-04 (all predator-pressure
# factors combined: more hiding predators, relentless stamina, fast move-interval)
# AND ADDS level-06 injury-gated sensory noise on olfaction (0.15 -> 0.75 sigma at
# max injury) + mild visual noise. Interoception kept clean so pain-gate stays
# reliable. The hardest hypervigilance probe in the basic05_variants family.
# RecurrentPPO (unmodulated), single-config from scratch (standalone, NOT continual).
# num_envs=16, episodes=10000000, checkpoint_frequency=100000, log_interval=50.
# GPU 0 on node 110 busy with rppo_basic05_randpred_n110 (PID 1154); GPU 1 free.
# CIFS-bypass: launched via /tmp script — this file is the audit record.
# ---------------------------------------------------------------------------
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic05_variants/05-all_combined_noise.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --num-envs 16 \
#   --episodes 10000000 \
#   --checkpoint-frequency 100000 \
#   --device cuda:1 \
#   --log-interval 50 \
#   --wandb-group basic05_variants \
#   --wandb-job-type prod \
#   --wandb-name rppo_basic05v5_allnoise_n110 \
#   --tag rppo_basic05v5_allnoise_n110

# ---------------------------------------------------------------------------
# basic standalone — level 07 jump/attack 10x10 — 2026-07-03
# RecurrentPPO (unmodulated), single-config from scratch (standalone, NOT continual).
# 07-jump_attack_10x10: extends basic/06 (all predator-pressure factors combined +
# injury-gated olfactory noise), ADDS predator jump/pounce (teleport onto an
# un-hidden agent within attack_range when cooldown is up; stochastic hit/miss).
# The toughest basic level — bush refuge becomes the only reliable defense.
# num_envs=16, episodes=10000000 (episode-budget convention), checkpoint_frequency=100000,
# log_interval=50.
# Node 113, cuda:0 (both 113 GPUs confirmed free RTX 4090; nas01 mounted, 52T free).
# CIFS-bypass: launched via /tmp script — this file is the audit record.
# NOTE: superseded as the active block below — this run (tag rppo_basic07_jump_n113,
# WandB u1tyn8xk) remains ALIVE on node 113 cuda:0; left untouched by the 2026-07-03 launch.
# ---------------------------------------------------------------------------
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/07-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --num-envs 16 \
#   --episodes 10000000 \
#   --checkpoint-frequency 100000 \
#   --device cuda:0 \
#   --log-interval 50 \
#   --wandb-group basic \
#   --wandb-job-type prod \
#   --wandb-name rppo_basic07_jump_n113 \
#   --tag rppo_basic07_jump_n113

# ---------------------------------------------------------------------------
# basic standalone — level 07 + wider jump reach (attack_range 2-or-3) — 2026-07-03
# RecurrentPPO (unmodulated), single-config from scratch (standalone, NOT continual).
# 06-jump_range_2to3: basic level 07 (jump/pounce predator) with attack_range widened
# to [2,4] -> per-episode pounce reach randomised to 2 or 3 cells (vs. level 07's
# narrower reach). Tests whether wider ambush range further stresses bush-refuge
# reliance as the agent's primary defense.
# num_envs=16, episodes=10000000 (episode-budget convention), checkpoint_frequency=100000,
# log_interval=50.
# Node 113, cuda:1 (GPU 0 busy with basic/07 run u1tyn8xk; GPU 1 confirmed free RTX 4090;
# nas01 confirmed mounted, 52T free).
# CIFS-bypass: launched via /tmp script — this file is the audit record.
# ---------------------------------------------------------------------------
#
# --- (previous active block preserved below the new one; see history above) ---
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic05_variants/06-jump_range_2to3.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --num-envs 16 \
#   --episodes 10000000 \
#   --checkpoint-frequency 100000 \
#   --device cuda:1 \
#   --log-interval 50 \
#   --wandb-group basic05_variants \
#   --wandb-job-type prod \
#   --wandb-name rppo_basic07_jumpreach23_n113 \
#   --tag rppo_basic07_jumpreach23_n113

# ---------------------------------------------------------------------------
# basic04 size sweep — XS/S/M/L/XL (NO 128-baseline; that's already running on
# node 106) — 2026-07-15
# RecurrentPPO size-variant agent configs (hidden_size 256/512/1024/2048/4096,
# mirrors DreamerV3 XS/S/M/L/XL presets), single-config from scratch (standalone,
# NOT continual). Env: basic/04-jump_attack_10x10 (jump/pounce predator,
# attack_range [2,3], no sensory noise, random_start_injury true).
# num_envs=16, episodes=100000000, checkpoint_frequency=100000, log_interval=50.
# wandb-group: basic04_size_sweep, job-type: prod.
# Pack-node-first: 107 (XS/S), 108 (M/L), 110:0 already used elsewhere -> 110 not
# used here per the launch plan (XL goes to 110:0 per plan; verify no collision
# at launch time). All GPUs confirmed idle + NAS mounted + JAX GPU-compile check
# passed (jax 0.9.0.1) on 107/108/110 prior to launch.
# CIFS-bypass: launched via /tmp scripts — this file is the audit record.
# ---------------------------------------------------------------------------
# Run XS: rppo_b04_szXS_16env_n107 — node 107, cuda:0 — LAUNCHED (WandB uxcu4wid)
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_XS.yaml \
#   --num-envs 16 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:0 --log-interval 50 \
#   --wandb-group basic04_size_sweep --wandb-job-type prod \
#   --wandb-name rppo_b04_szXS_16env_n107 --tag rppo_b04_szXS_16env_n107
#
# Run S: rppo_b04_szS_16env_n107 — node 107, cuda:1 — LAUNCHED (WandB 4p93s8ev)
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_S.yaml \
#   --num-envs 16 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:1 --log-interval 50 \
#   --wandb-group basic04_size_sweep --wandb-job-type prod \
#   --wandb-name rppo_b04_szS_16env_n107 --tag rppo_b04_szS_16env_n107
#
# Run M: rppo_b04_szM_16env_n108 — node 108, cuda:0 — LAUNCHED (WandB jwy6opzk)
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_M.yaml \
#   --num-envs 16 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:0 --log-interval 50 \
#   --wandb-group basic04_size_sweep --wandb-job-type prod \
#   --wandb-name rppo_b04_szM_16env_n108 --tag rppo_b04_szM_16env_n108
#
# Run L: rppo_b04_szL_16env_n108 — node 108, cuda:1 — LAUNCHED (WandB r62tqyzh)
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_L.yaml \
#   --num-envs 16 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:1 --log-interval 50 \
#   --wandb-group basic04_size_sweep --wandb-job-type prod \
#   --wandb-name rppo_b04_szL_16env_n108 --tag rppo_b04_szL_16env_n108
#
# Run XL: rppo_b04_szXL_16env_n110 — node 110, cuda:0 (confirmed idle immediately
# pre-launch; 0 MiB used, no compute processes)
/home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
  --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
  --agent_config configs/models/recurrent_ppo/recurrent_ppo_XL.yaml \
  --num-envs 16 --episodes 100000000 --checkpoint-frequency 100000 \
  --device cuda:0 --log-interval 50 \
  --wandb-group basic04_size_sweep --wandb-job-type prod \
  --wandb-name rppo_b04_szXL_16env_n110 --tag rppo_b04_szXL_16env_n110

# ---------------------------------------------------------------------------
# basic standalone — level 06 sensory noise 10x10 — RE-LAUNCH after extends: fix — 2026-07-03
# RecurrentPPO (unmodulated), single-config from scratch (standalone, NOT continual).
# 06-sensory_noise_10x10: extends basic/05 (random-init nutrition/injury + all
# combined predator-pressure factors), ADDS injury-gated olfactory sensory noise.
# RE-LAUNCH RATIONALE: the config-loader `extends:` chain was previously not
# resolved by train.py, so the inherited noise layer was silently dropped. Fixed
# upstream; this run verifies the fix by checking the saved config.yaml for
# perceptual_noise.enabled=true, olfaction injury_noise_scale=4.0, and
# random_start_injury=true.
# num_envs=16, episodes=10000000 (episode-budget convention), checkpoint_frequency=100000,
# log_interval=50.
# Node 110, cuda:0 (confirmed free RTX 3090; nas01 mounted 52T free; JAX GPU-compile
# check passed jax 0.9.0.1).
# CIFS-bypass: launched via /tmp script — this file is the audit record.
# ---------------------------------------------------------------------------
# NOTE 2026-09-30 (THIRST_WATER_PLAN): --config below repointed 06-sensory_noise -> 07-sensory_noise (the file was renamed and now sits on the pond world); the 2026-07-03 run used the old 06 file.
/home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
  --config configs/environment/experiment/basic/07-sensory_noise_10x10.yaml \
  --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
  --num-envs 16 --episodes 10000000 --checkpoint-frequency 100000 \
  --device cuda:0 --log-interval 50 \
  --wandb-group basic --wandb-job-type prod \
  --wandb-name rppo_basic06_noise_n110 --tag rppo_basic06_noise_n110

# ---------------------------------------------------------------------------
# basic standalone — level 07 jump/attack 10x10 — RE-LAUNCH after extends: fix — 2026-07-03
# RecurrentPPO (unmodulated), single-config from scratch (standalone, NOT continual).
# 07-jump_attack_10x10: extends basic/06 (all predator-pressure factors combined +
# injury-gated olfactory noise) + random-init nutrition/injury + predator jump/pounce.
# RE-LAUNCH RATIONALE: the config-loader `extends:` chain was previously not
# resolved by train.py, so inherited layers (noise + random-init + all-combined +
# jump) were silently dropped. Fixed upstream; this run verifies the fix by
# checking the saved config.yaml for perceptual_noise.enabled=true and
# random_start_injury=true.
# num_envs=16, episodes=10000000 (episode-budget convention), checkpoint_frequency=100000,
# log_interval=50.
# Node 108, cuda:0 (confirmed free RTX 3090; nas01 mounted 52T free; JAX GPU-compile
# check passed jax 0.9.0.1).
# CIFS-bypass: launched via /tmp script — this file is the audit record.
# ---------------------------------------------------------------------------
/home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
  --config configs/environment/experiment/basic/07-jump_attack_10x10.yaml \
  --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
  --num-envs 16 \
  --episodes 10000000 \
  --checkpoint-frequency 100000 \
  --device cuda:0 \
  --log-interval 50 \
  --wandb-group basic \
  --wandb-job-type prod \
  --wandb-name rppo_basic07_jump_v2_n108 \
  --tag rppo_basic07_jump_v2_n108

# ---------------------------------------------------------------------------
# NMN FiLM grouping_size screen — CONTINUAL (CURRICULUM) RE-LAUNCH 2026-06-27
# RecurrentPPO + NMN FiLM modulator, 8-point group-count curve (grouping_size 1→128)
# REPLACES the from-scratch single-env screen (terminated same day).
# Env: 5-stage basic curriculum (00→04 only), via frozen dir basic_curriculum/
#   (basic_curriculum_schedule_longL4 expects 5 stages; basic/ has 6 after
#    05-random_init_10x10 was added 2026-06-27 → fix: use dedicated basic_curriculum/ dir).
# Budget: schedule-driven (no --episodes); checkpoints from schedule.
# num_envs=128, seed=42, log-interval=10. Matches rppo_nmn_film_curric_longL4_n114 exactly,
# varying only agent_config + tag + node/GPU.
# Nodes 106 (cuda:0/1), 110 (cuda:0/1), 108 (cuda:0/1), 109 (cuda:0/1)
# wandb-group: basic_curriculum, job-type: prod
# Design doc: docs/experiments/active/basic_curriculum/NMN_FILM_GROUPING_SCREEN.md
# CIFS-bypass: launched via /tmp scripts — this file is the audit record.
# ---------------------------------------------------------------------------
# Run 1: rppo_nmn_film_g1_curric_longL4_s42   — node 106, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --configs-dir configs/environment/experiment/archive/basic_curriculum \
#   --continual-schedule configs/continual/basic_curriculum_schedule_longL4.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_nmn_film_g1_screen.yaml \
#   --num-envs 128 --seed 42 --log-interval 10 \
#   --device cuda:0 \
#   --wandb-group basic_curriculum --wandb-job-type prod \
#   --wandb-name rppo_nmn_film_g1_curric_longL4_s42 \
#   --tag rppo_nmn_film_g1_curric_longL4_s42
#
# Run 2: rppo_nmn_film_g2_curric_longL4_s42   — node 106, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --configs-dir configs/environment/experiment/archive/basic_curriculum \
#   --continual-schedule configs/continual/basic_curriculum_schedule_longL4.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_nmn_film_g2_screen.yaml \
#   --num-envs 128 --seed 42 --log-interval 10 \
#   --device cuda:1 \
#   --wandb-group basic_curriculum --wandb-job-type prod \
#   --wandb-name rppo_nmn_film_g2_curric_longL4_s42 \
#   --tag rppo_nmn_film_g2_curric_longL4_s42
#
# Run 3: rppo_nmn_film_g4_curric_longL4_s42   — node 110, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --configs-dir configs/environment/experiment/archive/basic_curriculum \
#   --continual-schedule configs/continual/basic_curriculum_schedule_longL4.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_nmn_film_g4_screen.yaml \
#   --num-envs 128 --seed 42 --log-interval 10 \
#   --device cuda:0 \
#   --wandb-group basic_curriculum --wandb-job-type prod \
#   --wandb-name rppo_nmn_film_g4_curric_longL4_s42 \
#   --tag rppo_nmn_film_g4_curric_longL4_s42
#
# Run 4: rppo_nmn_film_g8_curric_longL4_s42   — node 110, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --configs-dir configs/environment/experiment/archive/basic_curriculum \
#   --continual-schedule configs/continual/basic_curriculum_schedule_longL4.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_nmn_film_g8_screen.yaml \
#   --num-envs 128 --seed 42 --log-interval 10 \
#   --device cuda:1 \
#   --wandb-group basic_curriculum --wandb-job-type prod \
#   --wandb-name rppo_nmn_film_g8_curric_longL4_s42 \
#   --tag rppo_nmn_film_g8_curric_longL4_s42
#
# Run 5: rppo_nmn_film_g16_curric_longL4_s42  — node 108, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --configs-dir configs/environment/experiment/archive/basic_curriculum \
#   --continual-schedule configs/continual/basic_curriculum_schedule_longL4.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_nmn_film_g16_screen.yaml \
#   --num-envs 128 --seed 42 --log-interval 10 \
#   --device cuda:0 \
#   --wandb-group basic_curriculum --wandb-job-type prod \
#   --wandb-name rppo_nmn_film_g16_curric_longL4_s42 \
#   --tag rppo_nmn_film_g16_curric_longL4_s42
#
# Run 6: rppo_nmn_film_g32_curric_longL4_s42  — node 108, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --configs-dir configs/environment/experiment/archive/basic_curriculum \
#   --continual-schedule configs/continual/basic_curriculum_schedule_longL4.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_nmn_film_g32_screen.yaml \
#   --num-envs 128 --seed 42 --log-interval 10 \
#   --device cuda:1 \
#   --wandb-group basic_curriculum --wandb-job-type prod \
#   --wandb-name rppo_nmn_film_g32_curric_longL4_s42 \
#   --tag rppo_nmn_film_g32_curric_longL4_s42
#
# Run 7: rppo_nmn_film_g64_curric_longL4_s42  — node 109, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --configs-dir configs/environment/experiment/archive/basic_curriculum \
#   --continual-schedule configs/continual/basic_curriculum_schedule_longL4.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_nmn_film_g64_screen.yaml \
#   --num-envs 128 --seed 42 --log-interval 10 \
#   --device cuda:0 \
#   --wandb-group basic_curriculum --wandb-job-type prod \
#   --wandb-name rppo_nmn_film_g64_curric_longL4_s42 \
#   --tag rppo_nmn_film_g64_curric_longL4_s42
#
# Run 8: rppo_nmn_film_g128_curric_longL4_s42 — node 109, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --configs-dir configs/environment/experiment/archive/basic_curriculum \
#   --continual-schedule configs/continual/basic_curriculum_schedule_longL4.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_nmn_film_g128_screen.yaml \
#   --num-envs 128 --seed 42 --log-interval 10 \
#   --device cuda:1 \
#   --wandb-group basic_curriculum --wandb-job-type prod \
#   --wandb-name rppo_nmn_film_g128_curric_longL4_s42 \
#   --tag rppo_nmn_film_g128_curric_longL4_s42

# ---------------------------------------------------------------------------
# NMN FiLM grouping_size screen — basic05_variants/04-all_combined (single-env,
# NOT continual) — 2026-07-02
# RecurrentPPO + NMN FiLM modulator, 8-point group-count curve (grouping_size 1->128).
# Env: basic05_variants/04-all_combined (all three predator-pressure factors
# combined: more hiding predators count_high 4->12, predator max_stamina
# [30,150], predator move_interval fixed 1). Harder than the basic_curriculum
# far-sight screen (this env family has never been curriculum-staged).
# Pre-flight: env config resolves/builds cleanly, obs_dim=27 action_dim=6
# (matches expectation); all 8 agent configs verified byte-identical except
# modulation.grouping_size (and header comments).
# Cards are 11GB RTX 2080 Ti (nodes 101/103/104/105), smaller than the 24GB
# cards used for the earlier far-sight screen at --num-envs 128. Smoke-tested
# --num-envs 128 on node 101 (200-episode --no-wandb dry run): peak GPU memory
# well under 11GB, no OOM -> used 128 uniformly across all 8 runs.
# Budget: 10M episodes, seed=42, checkpoint_frequency=100000, log_interval=50.
# Nodes 101, 103, 104, 105 (2 GPUs each); wandb-group: basic05_variants, job-type: prod
# CIFS-bypass: launched via /tmp scripts — this file is the audit record.
# ---------------------------------------------------------------------------
# Run 1: rppo_nmn_film_g1_basic05all_s42   — node 101, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic05_variants/04-all_combined.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_nmn_film_g1_screen.yaml \
#   --num-envs 128 --episodes 10000000 --checkpoint-frequency 100000 \
#   --log-interval 50 --device cuda:0 --seed 42 \
#   --wandb-group basic05_variants --wandb-job-type prod \
#   --wandb-name rppo_nmn_film_g1_basic05all_s42 \
#   --tag rppo_nmn_film_g1_basic05all_s42
#
# Run 2: rppo_nmn_film_g2_basic05all_s42   — node 101, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic05_variants/04-all_combined.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_nmn_film_g2_screen.yaml \
#   --num-envs 128 --episodes 10000000 --checkpoint-frequency 100000 \
#   --log-interval 50 --device cuda:1 --seed 42 \
#   --wandb-group basic05_variants --wandb-job-type prod \
#   --wandb-name rppo_nmn_film_g2_basic05all_s42 \
#   --tag rppo_nmn_film_g2_basic05all_s42
#
# Run 3: rppo_nmn_film_g4_basic05all_s42   — node 103, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic05_variants/04-all_combined.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_nmn_film_g4_screen.yaml \
#   --num-envs 128 --episodes 10000000 --checkpoint-frequency 100000 \
#   --log-interval 50 --device cuda:0 --seed 42 \
#   --wandb-group basic05_variants --wandb-job-type prod \
#   --wandb-name rppo_nmn_film_g4_basic05all_s42 \
#   --tag rppo_nmn_film_g4_basic05all_s42
#
# Run 4: rppo_nmn_film_g8_basic05all_s42   — node 103, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic05_variants/04-all_combined.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_nmn_film_g8_screen.yaml \
#   --num-envs 128 --episodes 10000000 --checkpoint-frequency 100000 \
#   --log-interval 50 --device cuda:1 --seed 42 \
#   --wandb-group basic05_variants --wandb-job-type prod \
#   --wandb-name rppo_nmn_film_g8_basic05all_s42 \
#   --tag rppo_nmn_film_g8_basic05all_s42
#
# Run 5: rppo_nmn_film_g16_basic05all_s42  — node 104, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic05_variants/04-all_combined.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_nmn_film_g16_screen.yaml \
#   --num-envs 128 --episodes 10000000 --checkpoint-frequency 100000 \
#   --log-interval 50 --device cuda:0 --seed 42 \
#   --wandb-group basic05_variants --wandb-job-type prod \
#   --wandb-name rppo_nmn_film_g16_basic05all_s42 \
#   --tag rppo_nmn_film_g16_basic05all_s42
#
# Run 6: rppo_nmn_film_g32_basic05all_s42  — node 104, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic05_variants/04-all_combined.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_nmn_film_g32_screen.yaml \
#   --num-envs 128 --episodes 10000000 --checkpoint-frequency 100000 \
#   --log-interval 50 --device cuda:1 --seed 42 \
#   --wandb-group basic05_variants --wandb-job-type prod \
#   --wandb-name rppo_nmn_film_g32_basic05all_s42 \
#   --tag rppo_nmn_film_g32_basic05all_s42
#
# Run 7: rppo_nmn_film_g64_basic05all_s42  — node 105, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic05_variants/04-all_combined.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_nmn_film_g64_screen.yaml \
#   --num-envs 128 --episodes 10000000 --checkpoint-frequency 100000 \
#   --log-interval 50 --device cuda:0 --seed 42 \
#   --wandb-group basic05_variants --wandb-job-type prod \
#   --wandb-name rppo_nmn_film_g64_basic05all_s42 \
#   --tag rppo_nmn_film_g64_basic05all_s42
#
# Run 8: rppo_nmn_film_g128_basic05all_s42 — node 105, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic05_variants/04-all_combined.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_nmn_film_g128_screen.yaml \
#   --num-envs 128 --episodes 10000000 --checkpoint-frequency 100000 \
#   --log-interval 50 --device cuda:1 --seed 42 \
#   --wandb-group basic05_variants --wandb-job-type prod \
#   --wandb-name rppo_nmn_film_g128_basic05all_s42 \
#   --tag rppo_nmn_film_g128_basic05all_s42

# ---------------------------------------------------------------------------
# basic05_variants/06 — jump-REACH comparison to basic/07 — RE-LAUNCH after
# extends: fix — 2026-07-03
# RecurrentPPO (unmodulated), single-config from scratch (standalone, NOT continual).
# 06-jump_range_2to3.yaml: extends basic/07-jump_attack_10x10 (all predator-pressure
# factors + injury-gated olfactory noise + random-init + jump/pounce), REDECLARES
# only the predator's attack_range to [2,4] so the per-episode pounce reach is
# uniformly 2 OR 3 cells (vs. basic/07's fixed reach). Same config as the earlier
# rppo_basic07_jumpreach23_n113 entry above but on GPU 0 (not 1) with the
# convention-matching tag, launched after the config-loader extends: fix so the
# inherited noise + random-init layers are no longer silently dropped.
# num_envs=16, episodes=10000000 (episode-budget convention), checkpoint_frequency=100000,
# log_interval=50.
# Node 113, cuda:0 (confirmed free RTX 4090; nas01 mounted 52T free; JAX GPU-compile
# check passed jax 0.9.0.1).
# CIFS-bypass: launched via /tmp script — this file is the audit record.
# ---------------------------------------------------------------------------
/home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
  --config configs/environment/experiment/basic05_variants/06-jump_range_2to3.yaml \
  --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
  --num-envs 16 --episodes 10000000 --checkpoint-frequency 100000 \
  --device cuda:0 --log-interval 50 \
  --wandb-group basic --wandb-job-type prod \
  --wandb-name rppo_basic07_jumpreach_n113 --tag rppo_basic07_jumpreach_n113

# ---------------------------------------------------------------------------
# basic standalone — 05-random_init_10x10 (all-combined predator pressure +
# random-init nutrition/injury) — RE-LAUNCH after extends: fix — 2026-07-03
# RecurrentPPO (unmodulated), single-config from scratch (standalone, NOT continual).
# 05-random_init_10x10: extends environment/default (sensory/noise/behavior_measures
# inherited); random-init nutrition/injury + all predator-pressure factors folded
# in directly in this file (more hiding predators, relentless stamina, fast
# move-interval) — proper random init merged with variant-04 on 2026-07-02.
# RE-LAUNCH RATIONALE: the config-loader `extends:` chain was previously not
# resolved by train.py, so the inherited `environment/default` layer was silently
# dropped. Fixed upstream; this run verifies the fix by checking the saved
# config.yaml for random_start_injury=true and predator count_high=2,
# move_interval=[1,1] (proves the all-combined + random-init layers are present).
# num_envs=16, episodes=10000000 (episode-budget convention), checkpoint_frequency=100000,
# log_interval=50.
# Node 109, cuda:0 (confirmed free RTX 3090; nas01 mounted 52T free; JAX GPU-compile
# check passed jax 0.9.0.1).
# CIFS-bypass: launched via /tmp script — this file is the audit record.
# ---------------------------------------------------------------------------
/home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
  --config configs/environment/experiment/basic/05-random_init_10x10.yaml \
  --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
  --num-envs 16 --episodes 10000000 --checkpoint-frequency 100000 \
  --device cuda:0 --log-interval 50 \
  --wandb-group basic --wandb-job-type prod \
  --wandb-name rppo_basic05_alcomb_n109 --tag rppo_basic05_alcomb_n109

# ---------------------------------------------------------------------------
# basic05_variants/02 — relentless predator stamina — RE-LAUNCH after extends:
# fix — 2026-07-03 — PACKED onto node 108 GPU 1 (GPU 0 already runs basic/07,
# left untouched)
# RecurrentPPO (unmodulated), single-config from scratch (standalone, NOT continual).
# 02-relentless_stamina.yaml: extends basic05_variants/... -> basic/05-random_init_10x10
# (random-init nutrition/injury + all-combined predator-pressure factors), REDECLARES
# only the predator's max_stamina to [30,150] (some episodes spawn a relentless
# chaser that can drive the agent to starvation) and move_interval [1,3].
# RE-LAUNCH RATIONALE: supersedes the pre-fix 2026-06-30 run tagged
# rppo_basic05v2_stamina_n108 (same config, same node/GPU) — that run predates the
# config-loader extends: fix, so inherited layers (random_start_injury, all-combined
# predator pressure) were silently dropped. Verifies via saved config.yaml:
# random_start_injury=true, predator move_interval=[1,3], max_stamina=[30,150].
# num_envs=16, episodes=10000000 (episode-budget convention), checkpoint_frequency=100000,
# log_interval=50.
# Node 108, cuda:1 (GPU 0 busy with basic/07 jump run, PID confirmed via nvidia-smi
# 91% util; GPU 1 confirmed free 0% util/5MiB; nas01 mounted 52T free; JAX GPU-compile
# check passed jax 0.9.0.1).
# CIFS-bypass: launched via /tmp script — this file is the audit record.
# ---------------------------------------------------------------------------
/home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
  --config configs/environment/experiment/basic05_variants/02-relentless_stamina.yaml \
  --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
  --num-envs 16 --episodes 10000000 --checkpoint-frequency 100000 \
  --device cuda:1 --log-interval 50 \
  --wandb-group basic --wandb-job-type prod \
  --wandb-name rppo_basic05v02_relentstam_n108 --tag rppo_basic05v02_relentstam_n108

# ---------------------------------------------------------------------------
# basic05_variants/03 — fixed fast predator move_interval — PACKED onto node 109
# GPU 1 (GPU 0 already runs basic/05 all-combined, left untouched) — 2026-07-03
# RecurrentPPO (unmodulated), single-config from scratch (standalone, NOT continual).
# 03-fast_move_interval.yaml: extends basic/05-random_init_10x10 (random-init
# nutrition/injury + all-combined predator-pressure factors), REDECLARES only the
# predator's move_interval to a fixed [1,1] (always full-speed, no slow-predator
# episodes) and max_stamina [30,30].
# Verifies via saved config.yaml: random_start_injury=true, predator
# move_interval=[1,1], max_stamina=[30,30].
# num_envs=16, episodes=10000000 (episode-budget convention), checkpoint_frequency=100000,
# log_interval=50.
# Node 109, cuda:1 (GPU 0 busy with rppo_basic05_alcomb_n109, 78% util; GPU 1
# confirmed free 0% util/63MiB; nas01 mounted 52T free; JAX GPU-compile check
# passed jax 0.9.0.1).
# CIFS-bypass: launched via /tmp script — this file is the audit record.
# ---------------------------------------------------------------------------
/home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
  --config configs/environment/experiment/basic05_variants/03-fast_move_interval.yaml \
  --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
  --num-envs 16 --episodes 10000000 --checkpoint-frequency 100000 \
  --device cuda:1 --log-interval 50 \
  --wandb-group basic --wandb-job-type prod \
  --wandb-name rppo_basic05v03_fastmove_n109 --tag rppo_basic05v03_fastmove_n109

# ---------------------------------------------------------------------------
# FRESH re-leveled 6-level basic ladder — 2026-07-04
# Ladder re-leveled per commit b093023 (jump moved before noise; [2,3] default
# attack_range; variants retired into the main basic/ ladder). All 6 runs are
# RecurrentPPO (unmodulated), single-config from scratch (standalone, NOT
# continual), num_envs=16, episodes=10000000 (episode-budget convention),
# checkpoint_frequency=100000, log_interval=50.
# 00 static / 01 slow / 02 pred+rabbit / 03 random-init all-combined /
# 04 jump/pounce (no noise) / 05 sensory noise (full stack).
# Pack-node-first: 106 (00,01), 108 (02,03), 109 (04,05); node 110 left free;
# node 107 EXCLUDED (no NAS mount).
# CIFS-bypass: launched via /tmp scripts — this file is the audit record.
#
# PATH WARNING (added 2026-09-16, commit 0425367e): the basic ladder was
# re-chained and levels 05/06 SWAPPED. `basic/05-*` is now the CAMPFIRE
# THERMAL world; the sensory-noise world moved to
# `basic/06-sensory_noise_10x10.yaml`. The commands below are the historical
# record and are deliberately left exactly as launched — do NOT copy-paste a
# `05-sensory_noise` line, because that path now resolves to a different world
# than the run it is recorded against actually used.
# ---------------------------------------------------------------------------
# Run 00: rppo_basic00_static_n106 — node 106, cuda:0
/home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
  --config configs/environment/experiment/basic/00-static_predator_5x5.yaml \
  --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
  --num-envs 16 --episodes 10000000 --checkpoint-frequency 100000 \
  --device cuda:0 --log-interval 50 \
  --wandb-group basic --wandb-job-type prod \
  --wandb-name rppo_basic00_static_n106 --tag rppo_basic00_static_n106

# Run 01: rppo_basic01_slow_n106 — node 106, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/01-slow_predator_5x5.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --num-envs 16 --episodes 10000000 --checkpoint-frequency 100000 \
#   --device cuda:1 --log-interval 50 \
#   --wandb-group basic --wandb-job-type prod \
#   --wandb-name rppo_basic01_slow_n106 --tag rppo_basic01_slow_n106
#
# Run 02: rppo_basic02_predrabbit_n108 — node 108, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/02-predator_and_rabbit_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --num-envs 16 --episodes 10000000 --checkpoint-frequency 100000 \
#   --device cuda:0 --log-interval 50 \
#   --wandb-group basic --wandb-job-type prod \
#   --wandb-name rppo_basic02_predrabbit_n108 --tag rppo_basic02_predrabbit_n108
#
# Run 03: rppo_basic03_randinit_n108 — node 108, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/03-random_init_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --num-envs 16 --episodes 10000000 --checkpoint-frequency 100000 \
#   --device cuda:1 --log-interval 50 \
#   --wandb-group basic --wandb-job-type prod \
#   --wandb-name rppo_basic03_randinit_n108 --tag rppo_basic03_randinit_n108
#
# Run 04: rppo_basic04_jump_n109 — node 109, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --num-envs 16 --episodes 10000000 --checkpoint-frequency 100000 \
#   --device cuda:0 --log-interval 50 \
#   --wandb-group basic --wandb-job-type prod \
#   --wandb-name rppo_basic04_jump_n109 --tag rppo_basic04_jump_n109
#
# Run 05: rppo_basic05_noise_n109 — node 109, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/05-sensory_noise_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --num-envs 16 --episodes 10000000 --checkpoint-frequency 100000 \
#   --device cuda:1 --log-interval 50 \
#   --wandb-group basic --wandb-job-type prod \
#   --wandb-name rppo_basic05_noise_n109 --tag rppo_basic05_noise_n109

# ---------------------------------------------------------------------------
# basic03_randinit RESUME-AND-EXTEND — 10M -> 100M episode budget — 2026-07-08
# RecurrentPPO (unmodulated), resumes the COMPLETED basic03_randinit run
# (results/JAX_RecurrentPPO/20260704-230444_rppo_basic03_randinit_n108/models,
# latest checkpoint step 10000016) and extends the SAME single-task config
# (basic/03-random_init_10x10) to a 100M-episode budget. No curriculum, no
# multi-task change — user will stop the run manually when satisfied.
# --num-envs 16 is MANDATORY: the checkpoint was trained with 16 parallel envs;
# train.py's global default (128) causes a fatal Orbax shape-mismatch on
# restore. Confirmed by a prior resume-correctness gate test with this exact
# arg shape (weights + optimizer + counters all restore correctly).
# --checkpoint-frequency 100000 (finer than default) so behavior can be probed
# across many intermediate checkpoints.
# Node 108, cuda:1 (confirmed free via nvidia-smi immediately pre-launch: 0%
# util, 5 MiB used; GPU 0 busy at 97% util with an unrelated run — untouched).
# CIFS-bypass: launched via /tmp script — this file is the audit record.
# ---------------------------------------------------------------------------
/home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
  --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
  --config configs/environment/experiment/basic/03-random_init_10x10.yaml \
  --load-checkpoint results/JAX_RecurrentPPO/20260704-230444_rppo_basic03_randinit_n108/models \
  --num-envs 16 \
  --episodes 100000000 \
  --checkpoint-frequency 100000 \
  --device cuda:1 \
  --wandb-group basic \
  --wandb-job-type prod \
  --wandb-name rppo_basic03_randinit_cont100M_n108 \
  --tag rppo_basic03_randinit_cont100M_n108

# ---------------------------------------------------------------------------
# 6-level basic ladder RE-LAUNCH FROM SCRATCH at --num-envs 128 — 2026-07-08
# The originals (Run 00-05 above, 2026-07-04 block) were wrongly launched at
# --num-envs 16; intended setting is 128. TERMINATED (SIGINT) prior to this
# relaunch: rppo_basic00_static_n106 (PID 4846, node 106 cuda:0),
# rppo_basic01_slow_n106 (PID 5144, node 106 cuda:1),
# rppo_basic02_predrabbit_n108 (PID 1522844, node 108 cuda:0),
# rppo_basic03_randinit_cont100M_n108 (PID 2360259, node 108 cuda:1 — the
# checkpoint-resume/100M-budget variant from the block directly above).
# All 6 below are FRESH from-scratch runs (no --load-checkpoint), num_envs=128,
# episodes=10000000, checkpoint_frequency=100000, log_interval=50.
# Pack-node-first: 109 (00,01), 110 (02,03) — both fully free (4 GPUs);
# 106 (04) and 108 (05) — freed up by the termination above.
# GPU-compile pre-flight (jax 0.9.0.1, matmul+block_until_ready) passed on all
# 4 nodes; nvidia-smi confirmed all 8 target GPUs free immediately pre-launch.
# CIFS-bypass: launched via /tmp scripts — this file is the audit record.
#
# PATH WARNING (added 2026-09-16, commit 0425367e): levels 05/06 were SWAPPED.
# `basic/05-*` is now the CAMPFIRE THERMAL world; the sensory-noise world moved
# to `basic/06-sensory_noise_10x10.yaml`. Below is the historical record, left
# exactly as launched — do NOT copy-paste the `05-sensory_noise` line.
# ---------------------------------------------------------------------------
# Run 00: rppo_basic00_static_128env_n109 — node 109, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/00-static_predator_5x5.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --num-envs 128 --episodes 10000000 --checkpoint-frequency 100000 \
#   --device cuda:0 --log-interval 50 \
#   --wandb-group basic --wandb-job-type prod \
#   --wandb-name rppo_basic00_static_128env_n109 --tag rppo_basic00_static_128env_n109
#
# Run 01: rppo_basic01_slow_128env_n109 — node 109, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/01-slow_predator_5x5.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --num-envs 128 --episodes 10000000 --checkpoint-frequency 100000 \
#   --device cuda:1 --log-interval 50 \
#   --wandb-group basic --wandb-job-type prod \
#   --wandb-name rppo_basic01_slow_128env_n109 --tag rppo_basic01_slow_128env_n109
#
# Run 02: rppo_basic02_predrabbit_128env_n110 — node 110, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/02-predator_and_rabbit_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --num-envs 128 --episodes 10000000 --checkpoint-frequency 100000 \
#   --device cuda:0 --log-interval 50 \
#   --wandb-group basic --wandb-job-type prod \
#   --wandb-name rppo_basic02_predrabbit_128env_n110 --tag rppo_basic02_predrabbit_128env_n110
#
# Run 03: rppo_basic03_randinit_128env_n110 — node 110, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/03-random_init_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --num-envs 128 --episodes 10000000 --checkpoint-frequency 100000 \
#   --device cuda:1 --log-interval 50 \
#   --wandb-group basic --wandb-job-type prod \
#   --wandb-name rppo_basic03_randinit_128env_n110 --tag rppo_basic03_randinit_128env_n110
#
# Run 04: rppo_basic04_jump_128env_n106 — node 106, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --num-envs 128 --episodes 10000000 --checkpoint-frequency 100000 \
#   --device cuda:0 --log-interval 50 \
#   --wandb-group basic --wandb-job-type prod \
#   --wandb-name rppo_basic04_jump_128env_n106 --tag rppo_basic04_jump_128env_n106
#
# Run 05: rppo_basic05_noise_128env_n108 — node 108, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/05-sensory_noise_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --num-envs 128 --episodes 10000000 --checkpoint-frequency 100000 \
#   --device cuda:0 --log-interval 50 \
#   --wandb-group basic --wandb-job-type prod \
#   --wandb-name rppo_basic05_noise_128env_n108 --tag rppo_basic05_noise_128env_n108

# ---------------------------------------------------------------------------
# 6-level basic ladder — RESUME-AND-EXTEND levels 03/04/05 — 10M -> 100M
# episode budget — 2026-07-09
# RecurrentPPO (unmodulated), resumes the just-finished 128-env from-scratch
# runs (Run 03/04/05 in the block directly above) from their ~10M-episode
# checkpoints and extends the SAME single-task config to a 100M-episode
# budget. No curriculum, no config change — user will stop manually.
# Levels 00/01/02 are left untouched (still running / not extended).
# --num-envs 128 is MANDATORY — matches the checkpoints' h_state batch dim
# (confirmed via each checkpoint's saved config.yaml: num_envs: 128).
# Latest checkpoint steps confirmed on disk: basic03=10000029,
# basic04=10000005, basic05=10000167.
# Nodes 106 (cuda:0/1) and 108 (cuda:0) — all confirmed free via nvidia-smi
# immediately pre-launch (0% util); JAX GPU-compile check (jax 0.9.0.1,
# matmul + block_until_ready) passed on both nodes.
# CIFS-bypass: launched via /tmp scripts — this file is the audit record.
#
# PATH WARNING (added 2026-09-16, commit 0425367e): levels 05/06 were SWAPPED.
# `basic/05-*` is now the CAMPFIRE THERMAL world; the sensory-noise world moved
# to `basic/06-sensory_noise_10x10.yaml`. Below is the historical record, left
# exactly as launched — do NOT copy-paste the `05-sensory_noise` line.
# ---------------------------------------------------------------------------
# Run 03 resume: rppo_basic03_randinit_128env_100M_n106 — node 106, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/03-random_init_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/20260708-193853_rppo_basic03_randinit_128env_n110/models \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:0 \
#   --wandb-group basic --wandb-job-type prod \
#   --wandb-name rppo_basic03_randinit_128env_100M_n106 \
#   --tag rppo_basic03_randinit_128env_100M_n106
#
# Run 04 resume: rppo_basic04_jump_128env_100M_n106 — node 106, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/20260708-193852_rppo_basic04_jump_128env_n106/models \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:1 \
#   --wandb-group basic --wandb-job-type prod \
#   --wandb-name rppo_basic04_jump_128env_100M_n106 \
#   --tag rppo_basic04_jump_128env_100M_n106
#
# Run 05 resume: rppo_basic05_noise_128env_100M_n108 — node 108, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/05-sensory_noise_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/20260708-193853_rppo_basic05_noise_128env_n108/models \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:0 \
#   --wandb-group basic --wandb-job-type prod \
#   --wandb-name rppo_basic05_noise_128env_100M_n108 \
#   --tag rppo_basic05_noise_128env_100M_n108

# ---------------------------------------------------------------------------
# basic03 MODEL-SIZE SWEEP — 6 runs — 2026-07-13
# RecurrentPPO, 6-point hidden_size curve (128/256/512/1024/2048/4096) on the
# same env config basic/03-random_init_10x10 (all predator-pressure factors +
# random start nutrition/injury, no jump/pounce, clean smell).
# num_envs=16, episodes=100000000 (100M budget), checkpoint_frequency=100000,
# log_interval=50. All sizes fit a 24GB RTX 3090 at num_envs=16 (XL peaks ~18GB,
# pre-checked before launch).
# Pack-node-first: 107 (cuda:0,1), 108 (cuda:0,1), 109 (cuda:0,1); node 110 left free.
# wandb-group: basic03_size_sweep, job-type: prod
# CIFS-bypass: launched via /tmp scripts, one at a time — this file is the audit record.
# ---------------------------------------------------------------------------
# Run 1 (128, baseline): rppo_b03_sz128_n107 — node 107, cuda:0
/home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
  --config configs/environment/experiment/basic/03-random_init_10x10.yaml \
  --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
  --num-envs 16 --episodes 100000000 --checkpoint-frequency 100000 \
  --device cuda:0 --log-interval 50 \
  --wandb-group basic03_size_sweep --wandb-job-type prod \
  --wandb-name rppo_b03_sz128_n107 --tag rppo_b03_sz128_n107
#
# Run 2 (XS/256): rppo_b03_szXS_n107 — node 107, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/03-random_init_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_XS.yaml \
#   --num-envs 16 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:1 --log-interval 50 \
#   --wandb-group basic03_size_sweep --wandb-job-type prod \
#   --wandb-name rppo_b03_szXS_n107 --tag rppo_b03_szXS_n107
#
# Run 3 (S/512): rppo_b03_szS_n108 — node 108, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/03-random_init_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_S.yaml \
#   --num-envs 16 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:0 --log-interval 50 \
#   --wandb-group basic03_size_sweep --wandb-job-type prod \
#   --wandb-name rppo_b03_szS_n108 --tag rppo_b03_szS_n108
#
# Run 4 (M/1024): rppo_b03_szM_n108 — node 108, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/03-random_init_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_M.yaml \
#   --num-envs 16 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:1 --log-interval 50 \
#   --wandb-group basic03_size_sweep --wandb-job-type prod \
#   --wandb-name rppo_b03_szM_n108 --tag rppo_b03_szM_n108
#
# Run 5 (L/2048): rppo_b03_szL_n109 — node 109, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/03-random_init_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_L.yaml \
#   --num-envs 16 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:0 --log-interval 50 \
#   --wandb-group basic03_size_sweep --wandb-job-type prod \
#   --wandb-name rppo_b03_szL_n109 --tag rppo_b03_szL_n109
#
# Run 6 (XL/4096): rppo_b03_szXL_n109 — node 109, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/03-random_init_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_XL.yaml \
#   --num-envs 16 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:1 --log-interval 50 \
#   --wandb-group basic03_size_sweep --wandb-job-type prod \
#   --wandb-name rppo_b03_szXL_n109 --tag rppo_b03_szXL_n109

# ---------------------------------------------------------------------------
# basic04 (jump) MODEL-SIZE SWEEP — same 6-point hidden_size curve, RELAUNCH on
# basic/04-jump_attack_10x10 — 2026-07-14
# PHASE 1 (done first): the 6 basic03_size_sweep runs above (rppo_b03_sz128_n107,
# szXS_n107, szS_n108, szM_n108, szL_n109) were killed via SIGINT and confirmed
# gone; rppo_b03_szXL_n109 had ALREADY died on its own at 2026-07-14 07:27 from a
# node-109 GPU1 hardware fault (CUDA_ERROR_LAUNCH_FAILED flood in
# logs/20260713_185426.log, PID 3376504).
# PHASE 2: same 6 sizes (128/256/512/1024/2048/4096), same env family swapped to
# basic/04-jump_attack_10x10 (extends basic/03 directly, adds predator jump/pounce:
# attack_range [2,3], attack_success_rate 0.5; no sensory noise; random_start_injury
# inherited true). num_envs=16, episodes=100000000, checkpoint_frequency=100000,
# log_interval=50. wandb-group: basic04_size_sweep, job-type: prod.
# BLOCKER: node 109 is NOT usable right now — nvidia-smi reports
# "Unable to determine the device handle for GPU1: Unknown Error", and a fresh JAX
# process cannot even cuInit() on GPU0 either (CUDA_ERROR_UNKNOWN, falls back to
# CPU) — the whole node's CUDA driver stack looks poisoned by the GPU1 fault.
# Requires a reboot / driver reset outside training-runner scope. Only the 4 runs
# below (107:0, 107:1, 108:0, 108:1 — sizes 128/XS/S/M) were launched; szL_n109 and
# szXL_n109 are PENDING, surfaced to the user for a node-109-recovery or
# reassignment decision.
# Nodes 107/108 confirmed idle (GPU0+GPU1 both 0% util / ~0 MiB) and JAX
# GPU-compile check passed (jax 0.9.0.1, real matmul) before launch.
# CIFS-bypass: launched via /tmp scripts, one at a time — this file is the audit record.
# ---------------------------------------------------------------------------
# Run 1 (128, baseline): rppo_b04_sz128_n107 — node 107, cuda:0
/home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
  --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
  --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
  --num-envs 16 --episodes 100000000 --checkpoint-frequency 100000 \
  --device cuda:0 --log-interval 50 \
  --wandb-group basic04_size_sweep --wandb-job-type prod \
  --wandb-name rppo_b04_sz128_n107 --tag rppo_b04_sz128_n107
#
# Run 2 (XS/256): rppo_b04_szXS_n107 — node 107, cuda:1
/home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
  --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
  --agent_config configs/models/recurrent_ppo/recurrent_ppo_XS.yaml \
  --num-envs 16 --episodes 100000000 --checkpoint-frequency 100000 \
  --device cuda:1 --log-interval 50 \
  --wandb-group basic04_size_sweep --wandb-job-type prod \
  --wandb-name rppo_b04_szXS_n107 --tag rppo_b04_szXS_n107
#
# Run 3 (S/512): rppo_b04_szS_n108 — node 108, cuda:0
/home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
  --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
  --agent_config configs/models/recurrent_ppo/recurrent_ppo_S.yaml \
  --num-envs 16 --episodes 100000000 --checkpoint-frequency 100000 \
  --device cuda:0 --log-interval 50 \
  --wandb-group basic04_size_sweep --wandb-job-type prod \
  --wandb-name rppo_b04_szS_n108 --tag rppo_b04_szS_n108
#
# Run 4 (M/1024): rppo_b04_szM_n108 — node 108, cuda:1
/home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
  --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
  --agent_config configs/models/recurrent_ppo/recurrent_ppo_M.yaml \
  --num-envs 16 --episodes 100000000 --checkpoint-frequency 100000 \
  --device cuda:1 --log-interval 50 \
  --wandb-group basic04_size_sweep --wandb-job-type prod \
  --wandb-name rppo_b04_szM_n108 --tag rppo_b04_szM_n108
#
# ---------------------------------------------------------------------------
# Run 5/6 REASSIGNMENT — node 109 unusable, moved to node 110 — 2026-07-14
# Node 109 confirmed hardware/CUDA-faulted (GPU1 "Unknown Error", GPU0 also
# fails cuInit()) — unusable, left untouched. Reassigned to node 110
# (RTX 3090 x2), confirmed free (0 MiB / 0% util both GPUs), nas01 mounted
# (74T free), JAX GPU-compile check passed (jax 0.9.0.1, real matmul).
# Same settings as the 4 already running (128/XS on 107, S/M on 108):
# num_envs=16, episodes=100000000, checkpoint_frequency=100000, log_interval=50.
# Launched ONE AT A TIME via CIFS-bypass /tmp scripts — this file is the audit record.
# ---------------------------------------------------------------------------
# Run 5 (L/2048): rppo_b04_szL_n110 — node 110, cuda:0
/home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
  --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
  --agent_config configs/models/recurrent_ppo/recurrent_ppo_L.yaml \
  --num-envs 16 --episodes 100000000 --checkpoint-frequency 100000 \
  --device cuda:0 --log-interval 50 \
  --wandb-group basic04_size_sweep --wandb-job-type prod \
  --wandb-name rppo_b04_szL_n110 --tag rppo_b04_szL_n110
#
# Run 6 (XL/4096): rppo_b04_szXL_n110 — node 110, cuda:1
/home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
  --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
  --agent_config configs/models/recurrent_ppo/recurrent_ppo_XL.yaml \
  --num-envs 16 --episodes 100000000 --checkpoint-frequency 100000 \
  --device cuda:1 --log-interval 50 \
  --wandb-group basic04_size_sweep --wandb-job-type prod \
  --wandb-name rppo_b04_szXL_n110 --tag rppo_b04_szXL_n110

# ---------------------------------------------------------------------------
# basic04_variants — 4-run predator-pressure DIFFICULTY SWEEP (default/original
# RecurrentPPO size, hidden_size 128) — 2026-07-21
# RecurrentPPO (unmodulated, default size — NOT any XS/S/M/L/XL variant),
# single-config from scratch (standalone, NOT continual), 100M-episode budget.
# Four variants of basic/04-jump_attack_10x10, each softening exactly one
# predator knob relative to the harsh baseline (attack_range [2,3], damage
# 15-120, move_interval [1,1] fixed full-speed):
#   v01 (01-slow_move_interval):  move_interval [1,1] -> [1,3] (predator sometimes slower)
#   v02 (02-short_attack_range):  attack_range [2,3] -> [1,2] (shorter pounce reach)
#   v03 (03-reduced_damage):      damage 15-120 -> 15-80 (no one-shot kill; max_injury=100)
#   v04 (04-all_combined):        all three softenings combined
# num_envs=128, episodes=100000000, checkpoint_frequency=100000, log_interval=50.
# Memory: default 128-size model at 128 envs peaks ~1.4GB on a 24GB RTX 3090 (verified fine).
# wandb-group: basic04_variants, job-type: prod.
# Pack-node-first: 111 (v01 cuda:0, v02 cuda:1), 112 (v03 cuda:0, v04 cuda:1).
# Both nodes/GPUs confirmed idle (0% util) + NAS mounted (74T free) + JAX
# GPU-compile check passed (jax 0.9.0.1, real matmul on GPU) before launch.
# Launched ONE AT A TIME via CIFS-bypass /tmp scripts — this file is the audit record.
# ---------------------------------------------------------------------------
# Run v01: rppo_b04v01_slowmove_128env_n111 — node 111, cuda:0 — LAUNCHED (WandB 78nirb3q, PID 44147)
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/archive/basic04_variants/01-slow_move_interval.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:0 --log-interval 50 \
#   --wandb-group basic04_variants --wandb-job-type prod \
#   --wandb-name rppo_b04v01_slowmove_128env_n111 --tag rppo_b04v01_slowmove_128env_n111
#
# Run v02: rppo_b04v02_shortjump_128env_n111 — node 111, cuda:1 — LAUNCHED (WandB ugxsegwy, PID 47014)
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/archive/basic04_variants/02-short_attack_range.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:1 --log-interval 50 \
#   --wandb-group basic04_variants --wandb-job-type prod \
#   --wandb-name rppo_b04v02_shortjump_128env_n111 --tag rppo_b04v02_shortjump_128env_n111
#
# Run v03: rppo_b04v03_lowdmg_128env_n112 — node 112, cuda:0 — LAUNCHED (WandB lhy6be5b, PID 685263)
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/archive/basic04_variants/03-reduced_damage.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:0 --log-interval 50 \
#   --wandb-group basic04_variants --wandb-job-type prod \
#   --wandb-name rppo_b04v03_lowdmg_128env_n112 --tag rppo_b04v03_lowdmg_128env_n112
#
# Run v04: rppo_b04v04_allcomb_128env_n112 — node 112, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/archive/basic04_variants/04-all_combined.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:1 --log-interval 50 \
#   --wandb-group basic04_variants --wandb-job-type prod \
#   --wandb-name rppo_b04v04_allcomb_128env_n112 --tag rppo_b04v04_allcomb_128env_n112

# ---------------------------------------------------------------------------
# basic04_variants — 4 NEW difficulty variants (05-08), default rPPO size — 2026-07-21
# RecurrentPPO (unmodulated, default size — hidden_size 128, recurrent_ppo.yaml),
# single-config from scratch (standalone, NOT continual), 100M-episode budget.
# Four MORE variants of basic/04-jump_attack_10x10 (companions to v01-v04 already
# running on 111/112), each probing the pounce HIT RATE (attack_success_rate) axis
# while deliberately keeping the predator's move_interval at [1,1] (fast chase) —
# per the 2026-07-21 diary finding that a fast predator preserves bush-hiding
# behaviour, whereas slowing it (as v04-all_combined does) suppresses hiding to ~8%:
#   v05 (05-attack_success_030): asr 0.5 -> 0.3 (softer hit rate only)
#   v06 (06-attack_success_070): asr 0.5 -> 0.7 (harder hit rate only)
#   v07 (07-combined_move1_asr030): attack_range [2,3]->[1,2], damage 15-120->15-80,
#                                   asr 0.5->0.3 — ALL combined but move_interval STAYS [1,1]
#   v08 (08-combined_move1_asr070): same as v07 but asr 0.5->0.7
# num_envs=128, episodes=100000000, checkpoint_frequency=100000, log_interval=50.
# wandb-group: basic04_variants, job-type: prod.
# Pack-node-first: 106 (v05 cuda:0, v06 cuda:1), 107 (v07 cuda:0, v08 cuda:1).
# 108 deliberately left free. 111/112 (v01-v04) untouched. 109 faulted (not used).
# 110/113/114 in use by others (not used).
# Both nodes' GPUs confirmed idle (0 MiB / 0% util) + NAS mounted (74T free) + JAX
# GPU-compile check passed (jax 0.9.0.1, real matmul on GPU) on 106 and 107 before launch.
# Launched ONE AT A TIME via CIFS-bypass /tmp scripts, per the LAUNCH->WAIT->VERIFY
# protocol (60s wait + pgrep-only verification) — this file is the audit record.
# ---------------------------------------------------------------------------
# Run v05: rppo_b04v05_asr030_128env_n106 — node 106, cuda:0 — LAUNCHED (WandB bpb8wja7, PID 3168139)
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/archive/basic04_variants/05-attack_success_030.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:0 --log-interval 50 \
#   --wandb-group basic04_variants --wandb-job-type prod \
#   --wandb-name rppo_b04v05_asr030_128env_n106 --tag rppo_b04v05_asr030_128env_n106
#
# Run v06: rppo_b04v06_asr070_128env_n106 — node 106, cuda:1 — LAUNCHED (WandB 7lwxbf2j, PID 3168391)
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/archive/basic04_variants/06-attack_success_070.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:1 --log-interval 50 \
#   --wandb-group basic04_variants --wandb-job-type prod \
#   --wandb-name rppo_b04v06_asr070_128env_n106 --tag rppo_b04v06_asr070_128env_n106
#
# Run v07: rppo_b04v07_comb030_128env_n107 — node 107, cuda:0 — LAUNCHED (WandB unvd1rbw, PID 3229788)
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/archive/basic04_variants/07-combined_move1_asr030.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:0 --log-interval 50 \
#   --wandb-group basic04_variants --wandb-job-type prod \
#   --wandb-name rppo_b04v07_comb030_128env_n107 --tag rppo_b04v07_comb030_128env_n107
#
# Run v08: rppo_b04v08_comb070_128env_n107 — node 107, cuda:1 — LAUNCHED (WandB n9jtaqi7, PID 3230039)
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/archive/basic04_variants/08-combined_move1_asr070.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:1 --log-interval 50 \
#   --wandb-group basic04_variants --wandb-job-type prod \
#   --wandb-name rppo_b04v08_comb070_128env_n107 --tag rppo_b04v08_comb070_128env_n107

# ---------------------------------------------------------------------------
# GAE return-mode variant — basic/03 and basic/04 — 2026-07-22
# RecurrentPPO with recurrent_ppo_gae.yaml (return_mode: GAE, everything else
# identical to the default MC-return recurrent_ppo.yaml: hidden_size 128,
# default fc/actor/critic layer sizes). Compares GAE(lambda) returns vs. the
# usual Monte-Carlo return baseline used across the rest of the project.
# basic/03-random_init_10x10: random start nutrition/injury, all-combined
#   predator pressure, NO jump/pounce (attack_range [0,0]), no sensory noise.
# basic/04-jump_attack_10x10: extends basic/03, ADDS predator jump/pounce
#   (attack_range [2,3], attack_success_rate 0.5), no sensory noise.
# num_envs=128, episodes=100000000, checkpoint_frequency=100000, log_interval=50.
# Node 106, cuda:0 (basic/03) + cuda:1 (basic/04) — both confirmed FREE via
# gpu_status.py; GPU-compile preflight passed (jax 0.9.0.1) on node 106.
# wandb-group: rppo_gae, job-type: prod. Launched ONE AT A TIME per instruction.
# CIFS-bypass: launched via /tmp scripts — this file is the audit record.
# ---------------------------------------------------------------------------
# Run 1: rppo_b03_gae_128env_n106 — node 106, cuda:0
/home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
  --config configs/environment/experiment/basic/03-random_init_10x10.yaml \
  --agent_config configs/models/recurrent_ppo/recurrent_ppo_gae.yaml \
  --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
  --device cuda:0 --log-interval 50 \
  --wandb-group rppo_gae --wandb-job-type prod \
  --wandb-name rppo_b03_gae_128env_n106 --tag rppo_b03_gae_128env_n106

# Run 2: rppo_b04_gae_128env_n106 — node 106, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_gae.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:1 --log-interval 50 \
#   --wandb-group rppo_gae --wandb-job-type prod \
#   --wandb-name rppo_b04_gae_128env_n106 --tag rppo_b04_gae_128env_n106

# ---------------------------------------------------------------------------
# NMN-g32 vs plain head-to-head — basic/03 + basic/04 x {MC, GAE} — 2026-07-23
# RecurrentPPO + NMN FiLM modulator (grouping_size=32, temp_clip [0.5,10.0]),
# single-config from scratch (standalone, NOT continual), 100M-episode budget.
# 4-run 2x2: env {basic/03 no-jump, basic/04 jump/pounce} x return_mode {MC, GAE}.
# Agent configs: recurrent_ppo_nmn_film_g32_screen.yaml (MC) and its byte-identical
# GAE sibling recurrent_ppo_nmn_film_g32_screen_gae.yaml (commit 54792eb).
# Comparison targets: the plain-rPPO baselines rppo_b03_gae_128env_n106 /
# rppo_b04_gae_128env_n106 on node 106 (same env configs, same launch params).
# num_envs=128 (config default, passed explicitly to match baselines),
# episodes=100000000, checkpoint_frequency=100000 (matches baselines; deviates
# from recurrent_ppo.yaml's 200000 by explicit instruction), log_interval=50.
# wandb-group: nmn_g32_vs_plain_b0304, job-type: prod.
# Pack-node-first: 112 (b03 MC cuda:0, b03 GAE cuda:1), 111 (b04 MC cuda:0,
# b04 GAE cuda:1). All 4 GPUs confirmed idle (0 compute procs) + NAS mounted
# (73T free) on both nodes + JAX GPU-compile check passed (jax 0.9.0.1, real
# matmul, both CudaDevices visible) on 111 and 112 pre-launch.
# SMOKE: 5-min foreground dry run of b03 x g32-MC on 112:0 (--no-wandb, tag
# smoke_nmn_g32_b03_delete_me) passed — FiLM g32 enabled, obs 27 / act 6, JIT +
# checkpoint clean, ~800 it/s; debris deleted.
# Launched ONE AT A TIME via CIFS-bypass /tmp scripts per the LAUNCH->WAIT->VERIFY
# protocol (--no-tail, 60s wait, pgrep-only verify) — this file is the audit record.
# ---------------------------------------------------------------------------
# Run 1: rppo_nmn_g32_b03_mc_n112 — node 112, cuda:0 — LAUNCHED (WandB tgilz3eu, PID 3320979, log 20260723_210707.log)
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/03-random_init_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_nmn_film_g32_screen.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:0 --log-interval 50 \
#   --wandb-group nmn_g32_vs_plain_b0304 --wandb-job-type prod \
#   --wandb-name rppo_nmn_g32_b03_mc_n112 --tag rppo_nmn_g32_b03_mc_n112
#
# Run 2: rppo_nmn_g32_b03_gae_n112 — node 112, cuda:1 — LAUNCHED (WandB 34frib5j, PID 3321084, log 20260723_210712.log)
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/03-random_init_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_nmn_film_g32_screen_gae.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:1 --log-interval 50 \
#   --wandb-group nmn_g32_vs_plain_b0304 --wandb-job-type prod \
#   --wandb-name rppo_nmn_g32_b03_gae_n112 --tag rppo_nmn_g32_b03_gae_n112
#
# Run 3: rppo_nmn_g32_b04_mc_n111 — node 111, cuda:0 — LAUNCHED (WandB 48cb7q5l, PID 2810347, log 20260723_210715.log)
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_nmn_film_g32_screen.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:0 --log-interval 50 \
#   --wandb-group nmn_g32_vs_plain_b0304 --wandb-job-type prod \
#   --wandb-name rppo_nmn_g32_b04_mc_n111 --tag rppo_nmn_g32_b04_mc_n111
#
# Run 4: rppo_nmn_g32_b04_gae_n111 — node 111, cuda:1 — LAUNCHED (WandB j9gs52dh, PID 2810517, log 20260723_210721.log)
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_nmn_film_g32_screen_gae.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:1 --log-interval 50 \
#   --wandb-group nmn_g32_vs_plain_b0304 --wandb-job-type prod \
#   --wandb-name rppo_nmn_g32_b04_gae_n111 --tag rppo_nmn_g32_b04_gae_n111

# ---------------------------------------------------------------------------
# basic04 100M relaunch — during-training experiment-eval opt-in via config
# layer (replaces the now-removed --experiment-eval CLI flag) — 2026-07-25
# RecurrentPPO (unmodulated, default size), single-config from scratch
# (standalone, NOT continual). Env: basic/04-jump_attack_10x10 (jump/pounce
# predator, no sensory noise, random_start_injury true).
# --eval-config configs/evaluation/experiment_on.yaml opts into the
# during-training behavior-probe eval (extends evaluation/default, sets
# experiment.during_training.enabled: true -> conditions=all, episodes=30,
# log_measures=[bush_dwell, survival_steps], every_n_checkpoints=1). Dispatches
# an on-node CPU subprocess at every checkpoint, logs Experiment/* to WandB.
# Feature already verified end-to-end; this run's purpose is provenance parity
# with the committed config-layer mechanism (vs. the removed CLI flag).
# num_envs=128, episodes=100000000, checkpoint_frequency=100000, log_interval
# default (config-owned) -- matches the established convention for every other
# basic/04-jump_attack_10x10 launch in this file.
# Node 110, cuda:0 (confirmed idle 0 MiB/0% util, no compute procs; NAS mounted
# 72T free; JAX GPU-compile check passed jax 0.9.0.1, real matmul on GPU).
# CIFS-bypass: launched via /tmp script — this file is the audit record.
# ---------------------------------------------------------------------------
/home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
  --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
  --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
  --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 --device cuda:0 \
  --eval-config configs/evaluation/experiment_on.yaml \
  --wandb-group basic04_experimenteval --wandb-job-type prod \
  --wandb-name rppo_b04_experimenteval_128env_100M_n110 --tag rppo_b04_experimenteval_128env_100M_n110

# ---------------------------------------------------------------------------
# decay_power-1.0 corrected baselines — 4-run relaunch — 2026-07-26
# CONTEXT: sensory.decay_power had silently drifted 1.0->2.0 (commit def81c1,
# 2026-02-27) and was reverted to the intended 1.0 in commit d6240f5 (2026-07-26
# 03:48; see docs/environment/CONFIG_CRITICAL_SETTINGS.md). Every earlier rPPO
# run — including the 2026-07-23 NMN-g32-vs-plain b03/b04 2x2 on nodes 111/112 —
# trained under the wrong decay_power=2.0. These four runs are the corrected
# re-launch of that same 2x2 design (env {basic/03, basic/04} x agent {plain,
# NMN FiLM g32}), now under decay_power=1.0. All prior six rPPO runs on nodes
# 106/111/112 were terminated by the user before this relaunch; those GPUs
# confirmed free. Nodes 101/103/104/105 belong to a colleague (untouched);
# node 114 hosts a parallel Dreamer grid (untouched).
# All 4: RecurrentPPO, return_mode=MC, single-config from scratch (standalone),
# num_envs=128, episodes=100000000, seed=0 (default — not overridden).
# wandb-group: rppo_baseline_dp1, job-type: prod.
# GPUs confirmed idle (0 MiB/0%, no compute procs) + NAS mounted (72T free) on
# both 110 and 113 + JAX GPU-compile check passed (jax 0.9.0.1, real matmul on
# GPU) on both nodes pre-launch. Launched ONE AT A TIME via CIFS-bypass /tmp
# scripts per the LAUNCH->WAIT->VERIFY protocol (--no-tail, 60s wait,
# pgrep-only verify) — this file is the audit record.
# ---------------------------------------------------------------------------
# Run 1: rppo_b03_mc_dp1_n110 — node 110, cuda:0 — plain rPPO, basic/03 (no jump)
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/03-random_init_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:0 --log-interval 50 \
#   --wandb-group rppo_baseline_dp1 --wandb-job-type prod \
#   --wandb-name rppo_b03_mc_dp1_n110 --tag rppo_b03_mc_dp1_n110
#
# Run 2: rppo_b04_mc_dp1_n110 — node 110, cuda:1 — plain rPPO, basic/04 (jump/pounce)
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:1 --log-interval 50 \
#   --wandb-group rppo_baseline_dp1 --wandb-job-type prod \
#   --wandb-name rppo_b04_mc_dp1_n110 --tag rppo_b04_mc_dp1_n110
#
# Run 3: rppo_nmn_g32_b03_mc_dp1_n113 — node 113, cuda:0 — NMN FiLM g32, basic/03
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/03-random_init_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_nmn_film_g32_screen.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:0 --log-interval 50 \
#   --wandb-group rppo_baseline_dp1 --wandb-job-type prod \
#   --wandb-name rppo_nmn_g32_b03_mc_dp1_n113 --tag rppo_nmn_g32_b03_mc_dp1_n113
#
# Run 1: rppo_b03_mc_dp1_n110 — LAUNCHED (node 110, cuda:0, PID 893609)
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/03-random_init_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:0 --log-interval 50 \
#   --wandb-group rppo_baseline_dp1 --wandb-job-type prod \
#   --wandb-name rppo_b03_mc_dp1_n110 --tag rppo_b03_mc_dp1_n110
#
# Run 2: rppo_b04_mc_dp1_n110 — LAUNCHED (node 110, cuda:1, PID 893864)
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:1 --log-interval 50 \
#   --wandb-group rppo_baseline_dp1 --wandb-job-type prod \
#   --wandb-name rppo_b04_mc_dp1_n110 --tag rppo_b04_mc_dp1_n110
#
# Run 3: rppo_nmn_g32_b03_mc_dp1_n113 — LAUNCHED (node 113, cuda:0, PID 4037725)
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/03-random_init_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_nmn_film_g32_screen.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:0 --log-interval 50 \
#   --wandb-group rppo_baseline_dp1 --wandb-job-type prod \
#   --wandb-name rppo_nmn_g32_b03_mc_dp1_n113 --tag rppo_nmn_g32_b03_mc_dp1_n113
#
# Run 4: rppo_nmn_g32_b04_mc_dp1_n113 — LAUNCHED (node 113, cuda:1, PID 4038066)
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_nmn_film_g32_screen.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:1 --log-interval 50 \
#   --wandb-group rppo_baseline_dp1 --wandb-job-type prod \
#   --wandb-name rppo_nmn_g32_b04_mc_dp1_n113 --tag rppo_nmn_g32_b04_mc_dp1_n113

# ---------------------------------------------------------------------------
# decay_power-1.0 corrected baselines — SECOND 4-run relaunch — 2026-07-26
# Same family as the rppo_baseline_dp1 4-run relaunch above; extends the plain-
# vs-NMN-g32 split to basic/01 + basic/02. Plain rPPO on node 107, NMN FiLM g32
# on node 108 (mirrors the 110/113 plain/NMN split above).
# basic/01-slow_predator_5x5: 5x5 grid, 1 slow hunt predator (move_interval 3,
#   no jump), 2 static hiding predators, no rabbit.
# basic/02-predator_and_rabbit_10x10: 10x10 grid, 1 fast hunt predator
#   (move_interval 1, no jump), 4 hiding predators, 1 wandering rabbit.
# All 4: RecurrentPPO, return_mode=MC, single-config from scratch (standalone),
# num_envs=128, episodes=100000000, seed=42 (config default — not overridden,
# per explicit instruction). wandb-group: rppo_baseline_dp1, job-type: prod.
# checkpoint_frequency=100000, log_interval=50 (mirrors the 110/113 pair).
# Nodes 107/108 pre-flighted by the user (NAS mounted, both GPUs idle, 0
# compute procs) + JAX GPU-compile check passed (jax 0.9.0.1, real matmul on
# GPU) on both nodes pre-launch by this agent. Launched ONE AT A TIME via
# CIFS-bypass /tmp scripts per the LAUNCH->WAIT->VERIFY protocol (--no-tail,
# 60s wait, pgrep-only verify) — this file is the audit record.
# ---------------------------------------------------------------------------
# Run 1: rppo_b01_mc_dp1_n107 — node 107, cuda:0 — plain rPPO, basic/01 (5x5, slow predator)
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/01-slow_predator_5x5.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:0 --log-interval 50 \
#   --wandb-group rppo_baseline_dp1 --wandb-job-type prod \
#   --wandb-name rppo_b01_mc_dp1_n107 --tag rppo_b01_mc_dp1_n107
#
# Run 2: rppo_b02_mc_dp1_n107 — node 107, cuda:1 — plain rPPO, basic/02 (10x10, predator+rabbit)
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/02-predator_and_rabbit_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:1 --log-interval 50 \
#   --wandb-group rppo_baseline_dp1 --wandb-job-type prod \
#   --wandb-name rppo_b02_mc_dp1_n107 --tag rppo_b02_mc_dp1_n107
#
# Run 3: rppo_nmn_g32_b01_mc_dp1_n108 — node 108, cuda:0 — NMN FiLM g32, basic/01
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/01-slow_predator_5x5.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_nmn_film_g32_screen.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:0 --log-interval 50 \
#   --wandb-group rppo_baseline_dp1 --wandb-job-type prod \
#   --wandb-name rppo_nmn_g32_b01_mc_dp1_n108 --tag rppo_nmn_g32_b01_mc_dp1_n108
#
# Run 1: rppo_b01_mc_dp1_n107 — LAUNCHED (node 107, cuda:0, PID 1403622)
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/01-slow_predator_5x5.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:0 --log-interval 50 \
#   --wandb-group rppo_baseline_dp1 --wandb-job-type prod \
#   --wandb-name rppo_b01_mc_dp1_n107 --tag rppo_b01_mc_dp1_n107
#
# Run 2: rppo_b02_mc_dp1_n107 — LAUNCHED (node 107, cuda:1, PID 1403874)
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/02-predator_and_rabbit_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:1 --log-interval 50 \
#   --wandb-group rppo_baseline_dp1 --wandb-job-type prod \
#   --wandb-name rppo_b02_mc_dp1_n107 --tag rppo_b02_mc_dp1_n107
#
# Run 3: rppo_nmn_g32_b01_mc_dp1_n108 — LAUNCHED (node 108, cuda:0, PID 4009642)
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/01-slow_predator_5x5.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_nmn_film_g32_screen.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:0 --log-interval 50 \
#   --wandb-group rppo_baseline_dp1 --wandb-job-type prod \
#   --wandb-name rppo_nmn_g32_b01_mc_dp1_n108 --tag rppo_nmn_g32_b01_mc_dp1_n108
#
# Run 4: rppo_nmn_g32_b02_mc_dp1_n108 — LAUNCHED (node 108, cuda:1, PID 4009895)
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/02-predator_and_rabbit_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_nmn_film_g32_screen.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:1 --log-interval 50 \
#   --wandb-group rppo_baseline_dp1 --wandb-job-type prod \
#   --wandb-name rppo_nmn_g32_b02_mc_dp1_n108 --tag rppo_nmn_g32_b02_mc_dp1_n108

# ---------------------------------------------------------------------------
# rppo_bushrefuge — 4-run bush-as-physical-refuge ladder — 2026-08-04
# ---------------------------------------------------------------------------
# WHAT THIS TESTS (plain language): the bush in this project has always concealed the
# agent from predator detection, but predators could still walk THROUGH a bush cell.
# The new configs/environment/experiment/archive/basic_bushrefuge/ ladder (commit 76711de) is a
# byte-for-byte sibling of configs/environment/experiment/basic/ with exactly ONE key
# changed — the bush obstacle now carries `blocks_animals: true`, so predators and the
# wandering rabbit cannot MOVE INTO a bush cell while the agent still enters freely and
# stays concealed. The bush becomes a true physical refuge. Question: does that change
# hiding behaviour?
#
# Plain rPPO (unmodulated, modulation.type: null), single-config from scratch
# (standalone, NOT continual). Settings deliberately identical to the 2026-07-26
# `rppo_baseline_dp1` batch so the two families are directly comparable:
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 --log-interval 50
#   seed: config default 42 (NOT overridden on the CLI)
#
# NEW vs. the 2026-07-26 batch: --eval-config configs/evaluation/experiment_on.yaml
#   turns on the during-training behaviour probe so Experiment/bush_dwell and
#   Experiment/survival_steps plot live on WandB. A bush-refuge manipulation with no
#   bush-dwell curve is not worth running, so this flag is mandatory on all four runs.
#
# Deviations flagged to the user pre-launch:
#   - --checkpoint-frequency 100000 overrides the rPPO config-owned 200000
#     (configs/train/recurrent_ppo.yaml) — intentional, for baseline comparability.
#   - --num-envs 128 is redundant (config-owned value is already 128) but passed
#     explicitly to mirror the baseline batch's command line exactly.
#
# Pre-flight: nodes 102 + 113 both NAS-mounted (71T free), JAX 0.9.0.1 GPU-compile
# check passed on both, all four RTX 4090 GPUs idle. sensory.decay_power resolves to
# 1.0 = registry canonical (docs/environment/CONFIG_CRITICAL_SETTINGS.md).
# wandb-group: rppo_bushrefuge, job-type: prod
# CIFS-bypass: launched via /tmp scripts — this file is the audit record.
# ---------------------------------------------------------------------------
# Run 1: rppo_bushrefuge_b01_n102 — node 102, cuda:0 — 5x5, slow predator (move_interval 3)
# LAUNCHED 2026-08-04, PID 3514180, launcher log logs/20260804_040530.log
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/archive/basic_bushrefuge/01-slow_predator_5x5.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --eval-config configs/evaluation/experiment_on.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:0 --log-interval 50 \
#   --wandb-group rppo_bushrefuge --wandb-job-type prod \
#   --wandb-name rppo_bushrefuge_b01_n102 --tag rppo_bushrefuge_b01_n102
#
# Run 2: rppo_bushrefuge_b02_n102 — node 102, cuda:1 — 10x10, fast predator + wandering rabbit
# LAUNCHED 2026-08-04, PID 3514932, launcher log logs/20260804_040708.log
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/archive/basic_bushrefuge/02-predator_and_rabbit_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --eval-config configs/evaluation/experiment_on.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:1 --log-interval 50 \
#   --wandb-group rppo_bushrefuge --wandb-job-type prod \
#   --wandb-name rppo_bushrefuge_b02_n102 --tag rppo_bushrefuge_b02_n102
#
# Run 3: rppo_bushrefuge_b03_n113 — node 113, cuda:0 — 10x10 random-init + all-combined pressure
# LAUNCHED 2026-08-04, PID 1315, launcher log logs/20260804_040843.log
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/archive/basic_bushrefuge/03-random_init_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --eval-config configs/evaluation/experiment_on.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:0 --log-interval 50 \
#   --wandb-group rppo_bushrefuge --wandb-job-type prod \
#   --wandb-name rppo_bushrefuge_b03_n113 --tag rppo_bushrefuge_b03_n113
#
# Run 4: rppo_bushrefuge_b04_n113 — node 113, cuda:1 — 10x10 jump/pounce (attack_range [2,3], 50% hit)
# LAUNCHED 2026-08-04, PID 1692, launcher log logs/20260804_041012.log
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/archive/basic_bushrefuge/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --eval-config configs/evaluation/experiment_on.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:1 --log-interval 50 \
#   --wandb-group rppo_bushrefuge --wandb-job-type prod \
#   --wandb-name rppo_bushrefuge_b04_n113 --tag rppo_bushrefuge_b04_n113

# ---------------------------------------------------------------------------
# rppo_restprem — 10-arm REST-PREMIUM sweep — 2026-08-10
# ---------------------------------------------------------------------------
# WHAT THIS TESTS (plain language): in this project injury heals ONLY when the agent
# takes the Rest action, so an injured agent freezes and heals wherever it happens to
# be standing — it does NOT travel to cover first. Measured on the bush-refuge runs:
# while injured the agent rests ~86% of the time but sits in a bush only 1-3% of it.
# This sweep asks whether making an UNINTERRUPTED rest streak valuable is enough to
# push an injured agent to walk to the refuge bush (which predators cannot enter) and
# complete the heal somewhere safe — i.e. whether injury can be made to INCREASE cover
# use instead of suppressing it.
#
# THE SINGLE VARIABLE is the "streak premium": how much more healing you get on the
# 10th consecutive Rest than on the 1st Rest after an interruption.
#   recovery = recovery_base_rate * (1 + recovery_accel_rate)^(rest_streak - 1)
# The 10 arms sweep that premium log-spaced from 1x (flat, no continuity incentive)
# to 129962x. recovery_base_rate is SOLVED per arm so every arm still sheds injury 70
# in ~13-15 rest steps — the injured window is matched, only the continuity gradient
# differs. a01 = the zero-premium anchor; a03 (38x) reproduces the current default.
#
#   arm  premium      base        accel
#   a01  1x           5.0         0.0
#   a02  ~2x          ...         ...
#   a03  38x          0.12        0.5     <- current/default regime
#   a04-a08  (log-spaced between)
#   a09  19683x       2.9e-05     2.0     <- WATCH: very small base rate
#   a10  129962x      2.1e-06     2.7     <- WATCH: very small base rate
#
# Base task: configs/environment/experiment/archive/basic_bushrefuge/04-jump_attack_10x10
# (bush blocks_animals, jump/pounce predator attack_range [2,3]) — each arm `extends:`
# it and overrides ONLY body.recovery_base_rate + body.recovery_accel_rate.
# Configs committed at 5e170a1; the agent did not modify them.
#
# Plain rPPO (unmodulated), single-config from scratch (standalone, NOT continual).
# Flags deliberately IDENTICAL to the 2026-08-04 rppo_bushrefuge batch so the
# restpremium arms are directly comparable to that ladder:
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 --log-interval 50
#   --eval-config configs/evaluation/experiment_on.yaml   (bush_dwell / survival probe)
#   seed: config default 42 (NOT overridden on the CLI)
#
# Deviations flagged to the user pre-launch (inherited from the bushrefuge precedent):
#   - --checkpoint-frequency 100000 overrides the rPPO config-owned 200000
#     (configs/train/recurrent_ppo.yaml) — intentional, for cross-batch comparability.
#   - --num-envs 128 is redundant (config-owned value is already 128) but passed
#     explicitly to mirror the bushrefuge batch's command line exactly.
#
# Pre-flight 2026-08-10: nodes 106/107/108/110 NAS-mounted (nas01, 68T free), all 8
# RTX 3090 GPUs idle (<=58 MiB, no compute procs), JAX 0.9.0.1 GPU-compile check passed
# on all four. sensory.decay_power resolves to 1.0 = registry canonical
# (docs/environment/CONFIG_CRITICAL_SETTINGS.md).
# NODE 109 FAILED PRE-FLIGHT: reachable, but nas01 is NOT mounted (only nas02 + nas03;
# /media/nas01 empty). Arms a07 + a08 were therefore NOT launched — see block below.
# wandb-group: rppo_restprem, job-type: prod
# CIFS-bypass: launched via /tmp scripts — this file is the audit record.
# ---------------------------------------------------------------------------
# Arm a01: rppo_restprem_a01_n106 — node 106, cuda:0 — premium 1x (base 5.0, accel 0.0)
# LAUNCHED 2026-08-10, PID 3906803, launcher log logs/20260810_185746.log, WandB szje7o9w
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/archive/basic_bushrefuge_restpremium/04-restprem_a01.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --eval-config configs/evaluation/experiment_on.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:0 --log-interval 50 \
#   --wandb-group rppo_restprem --wandb-job-type prod \
#   --wandb-name rppo_restprem_a01_n106 --tag rppo_restprem_a01_n106
#
# Arm a02: rppo_restprem_a02_n106 — node 106, cuda:1
# LAUNCHED 2026-08-10, PID 3906972, launcher log logs/20260810_185754.log (SHARED/garbled — see note), WandB 96xmquu3
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/archive/basic_bushrefuge_restpremium/04-restprem_a02.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --eval-config configs/evaluation/experiment_on.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:1 --log-interval 50 \
#   --wandb-group rppo_restprem --wandb-job-type prod \
#   --wandb-name rppo_restprem_a02_n106 --tag rppo_restprem_a02_n106
#
# Arm a03: rppo_restprem_a03_n107 — node 107, cuda:0 — 38x, reproduces current default
# LAUNCHED 2026-08-10, PID 3560982, launcher log logs/20260810_185754.log (SHARED/garbled), WandB 2na5mqbl
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/archive/basic_bushrefuge_restpremium/04-restprem_a03.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --eval-config configs/evaluation/experiment_on.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:0 --log-interval 50 \
#   --wandb-group rppo_restprem --wandb-job-type prod \
#   --wandb-name rppo_restprem_a03_n107 --tag rppo_restprem_a03_n107
#
# Arm a04: rppo_restprem_a04_n107 — node 107, cuda:1
# LAUNCHED 2026-08-10, PID 3561022, launcher log logs/20260810_185754.log (SHARED/garbled), WandB idv8vkjl
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/archive/basic_bushrefuge_restpremium/04-restprem_a04.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --eval-config configs/evaluation/experiment_on.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:1 --log-interval 50 \
#   --wandb-group rppo_restprem --wandb-job-type prod \
#   --wandb-name rppo_restprem_a04_n107 --tag rppo_restprem_a04_n107
#
# Arm a05: rppo_restprem_a05_n108 — node 108, cuda:0
# LAUNCHED 2026-08-10, PID 1521914, launcher log logs/20260810_185754.log (SHARED/garbled), WandB f6u0z3mo
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/archive/basic_bushrefuge_restpremium/04-restprem_a05.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --eval-config configs/evaluation/experiment_on.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:0 --log-interval 50 \
#   --wandb-group rppo_restprem --wandb-job-type prod \
#   --wandb-name rppo_restprem_a05_n108 --tag rppo_restprem_a05_n108
#
# Arm a06: rppo_restprem_a06_n108 — node 108, cuda:1
# LAUNCHED 2026-08-10, PID 1521919, launcher log logs/20260810_185754.log (SHARED/garbled), WandB m7pm9xqm
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/archive/basic_bushrefuge_restpremium/04-restprem_a06.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --eval-config configs/evaluation/experiment_on.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:1 --log-interval 50 \
#   --wandb-group rppo_restprem --wandb-job-type prod \
#   --wandb-name rppo_restprem_a06_n108 --tag rppo_restprem_a06_n108
#
# Arms a07 + a08 — REASSIGNED node 109 -> node 111 by the user, 2026-08-10.
# The original 109 assignment was BLOCKED: node 109 has no nas01 CIFS mount (only
# nas02 + nas03 present; /media/nas01 is an empty directory), so the project tree is
# unreachable there. Node 111 re-verified at reassignment time: nas01 mounted (67T
# free), both RTX 3090s idle (28 / 196 MiB, 0% util), no train.py running.
# Tags renamed _n109 -> _n111 to reflect the actual node.
# Launched SEQUENTIALLY with a ~60 s gap: the first 8 arms ran 8 cold JIT compiles
# concurrently over CIFS, which is why they took ~45 min to reach the first step;
# staggering avoids compounding that. Each got an EXPLICIT --log path via
# run_command.py --log, so neither collides with the other's launcher log.
#
# Arm a07: rppo_restprem_a07_n111 — node 111, cuda:0
# LAUNCHED 2026-08-10 20:24, PID 1971, launcher log logs/20260810_restprem_a07_n111.log, WandB 70erj7yy
# (commented 2026-08-16: still running on 111:1 lineage; superseded as the live block
#  by the NO-HIDING-PREDATOR batch below)
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/archive/basic_bushrefuge_restpremium/04-restprem_a07.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --eval-config configs/evaluation/experiment_on.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:0 --log-interval 50 \
#   --wandb-group rppo_restprem --wandb-job-type prod \
#   --wandb-name rppo_restprem_a07_n111 --tag rppo_restprem_a07_n111
#
# Arm a08: rppo_restprem_a08_n111 — node 111, cuda:1
# LAUNCHED 2026-08-10 20:25 (~60 s after a07, staggered), PID 2187,
# launcher log logs/20260810_restprem_a08_n111.log, WandB wezpfd69
# (commented 2026-08-16 — see note on a07 above)
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/archive/basic_bushrefuge_restpremium/04-restprem_a08.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --eval-config configs/evaluation/experiment_on.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:1 --log-interval 50 \
#   --wandb-group rppo_restprem --wandb-job-type prod \
#   --wandb-name rppo_restprem_a08_n111 --tag rppo_restprem_a08_n111
#
# Arm a09: rppo_restprem_a09_n110 — node 110, cuda:0 — 19683x (base 2.9e-05) WATCH ITEM
# LAUNCHED 2026-08-10, PID 1017751, launcher log logs/20260810_185754.log (SHARED/garbled), WandB evrn1amy
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/archive/basic_bushrefuge_restpremium/04-restprem_a09.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --eval-config configs/evaluation/experiment_on.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:0 --log-interval 50 \
#   --wandb-group rppo_restprem --wandb-job-type prod \
#   --wandb-name rppo_restprem_a09_n110 --tag rppo_restprem_a09_n110
#
# Arm a10: rppo_restprem_a10_n110 — node 110, cuda:1 — 129962x (base 2.1e-06) WATCH ITEM
# LAUNCHED 2026-08-10, PID 1017791, launcher log logs/20260810_185755.log, WandB vauz72ni
#
# LAUNCH-TIME NOTES (2026-08-10):
#  - LAUNCHER-LOG COLLISION: run_command.py names the log logs/<UTC-second>.log on the
#    SHARED NAS. Six arms (a02..a06, a09) launched inside the same second and therefore
#    all redirect into logs/20260810_185754.log, whose contents are interleaved/garbled.
#    Training is unaffected (each run has its own WandB run + results dir), but that
#    launcher log is not readable. Pass --log explicitly on future batch launches.
#  - --log-interval 50 is IGNORED by these configs (they use the two-level `logging:`
#    block: logging.episode.interval_episodes=4000, logging.step.interval_iters=50).
#    Kept on the command line only to mirror the bushrefuge batch byte-for-byte.
#  - SLOW STARTUP: with experiment.during_training enabled, startup walks the whole
#    results/eval tree over CIFS before the first GPU step. At T+23 min all 8 procs were
#    alive with CPU time climbing and the directory walk visibly advancing, but GPU util
#    was still 0%. Expected-slow, not a hang.
# (commented 2026-08-10: the live block is now the a07/a08 node-111 pair above)
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/archive/basic_bushrefuge_restpremium/04-restprem_a10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --eval-config configs/evaluation/experiment_on.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:1 --log-interval 50 \
#   --wandb-group rppo_restprem --wandb-job-type prod \
#   --wandb-name rppo_restprem_a10_n110 --tag rppo_restprem_a10_n110
#
# ===========================================================================
# NO-HIDING-PREDATOR rest-premium sweep (10 arms) — LAUNCHED 2026-08-16
# ---------------------------------------------------------------------------
# Replicate of the 2026-08-10 rest-premium sweep with the 2-12 ambush
# `hiding_predator` resources REMOVED (resources restated food-only). Tests
# whether "moving is dangerous" is what stopped injured agents from travelling
# to the refuge bush. WandB group: rppo_restpremNH (new group).
#
# Configs: configs/environment/experiment/archive/basic_bushrefuge_restpremium_nohide/
#          committed cfc0293, verified food-only; recovery curves, bush-refuge
#          blocks_animals and jump/pounce all inherited from the parent arms.
#
# LAUNCH-TIME NOTES (2026-08-16):
#  - EXPLICIT --log PER RUN this time: logs/20260816_restpremNH_<arm>_n<node>.log.
#    The 2026-08-10 batch collided six runs into logs/20260810_185754.log because
#    run_command.py defaults to logs/<UTC-second>.log on the shared NAS.
#  - STAGGERED ~60 s apart. Eight concurrent cold JIT compiles took ~54 min on
#    2026-08-10; staggering cut it to ~44 min.
#  - GPUs 108:1 and 111:1 DELIBERATELY EXCLUDED — the 2026-08-10 arms a06/a08 were
#    still finishing there (94.9M / 98.9M of 100M) at launch time.
#  - DEVIATION FROM CONFIG-OWNS-VALUES: --num-envs 128 and --checkpoint-frequency
#    100000 are passed explicitly to mirror the parent sweep byte-for-byte so the
#    two sweeps stay comparable. Flagged to the user at launch.
#  - --log-interval 50 is IGNORED by these configs (they use the two-level
#    `logging:` block). Kept only to mirror the parent batch byte-for-byte.
#  - Launched via the CIFS-bypass pattern: each block was mirrored to a unique
#    /tmp script on its target node and run through run_command.py --no-tail.
# ===========================================================================
#
# Arm a01: rppo_restpremNH_a01_n106 — node 106, cuda:0
# LAUNCHED 2026-08-16, PID 1550979, launcher log logs/20260816_restpremNH_a01_n106.log, WandB oloh6yt3
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/archive/basic_bushrefuge_restpremium_nohide/04-restprem_nohide_a01.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --eval-config configs/evaluation/experiment_on.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:0 --log-interval 50 \
#   --wandb-group rppo_restpremNH --wandb-job-type prod \
#   --wandb-name rppo_restpremNH_a01_n106 --tag rppo_restpremNH_a01_n106
#
# Arm a02: rppo_restpremNH_a02_n106 — node 106, cuda:1
# LAUNCHED 2026-08-16, PID 1551189, launcher log logs/20260816_restpremNH_a02_n106.log, WandB o2ze4gji
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/archive/basic_bushrefuge_restpremium_nohide/04-restprem_nohide_a02.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --eval-config configs/evaluation/experiment_on.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:1 --log-interval 50 \
#   --wandb-group rppo_restpremNH --wandb-job-type prod \
#   --wandb-name rppo_restpremNH_a02_n106 --tag rppo_restpremNH_a02_n106
#
# Arm a03: rppo_restpremNH_a03_n107 — node 107, cuda:0
# LAUNCHED 2026-08-16, PID 1204293, launcher log logs/20260816_restpremNH_a03_n107.log, WandB ob3rkm8u
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/archive/basic_bushrefuge_restpremium_nohide/04-restprem_nohide_a03.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --eval-config configs/evaluation/experiment_on.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:0 --log-interval 50 \
#   --wandb-group rppo_restpremNH --wandb-job-type prod \
#   --wandb-name rppo_restpremNH_a03_n107 --tag rppo_restpremNH_a03_n107
#
# Arm a04: rppo_restpremNH_a04_n107 — node 107, cuda:1
# LAUNCHED 2026-08-16, PID 1204507, launcher log logs/20260816_restpremNH_a04_n107.log, WandB vk5upgay
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/archive/basic_bushrefuge_restpremium_nohide/04-restprem_nohide_a04.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --eval-config configs/evaluation/experiment_on.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:1 --log-interval 50 \
#   --wandb-group rppo_restpremNH --wandb-job-type prod \
#   --wandb-name rppo_restpremNH_a04_n107 --tag rppo_restpremNH_a04_n107
#
# Arm a05: rppo_restpremNH_a05_n108 — node 108, cuda:0
# LAUNCHED 2026-08-16, PID 3161807, launcher log logs/20260816_restpremNH_a05_n108.log, WandB 1atfgt5p
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/archive/basic_bushrefuge_restpremium_nohide/04-restprem_nohide_a05.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --eval-config configs/evaluation/experiment_on.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:0 --log-interval 50 \
#   --wandb-group rppo_restpremNH --wandb-job-type prod \
#   --wandb-name rppo_restpremNH_a05_n108 --tag rppo_restpremNH_a05_n108
#
# Arm a06: rppo_restpremNH_a06_n110 — node 110, cuda:0
# LAUNCHED 2026-08-16, PID 2838529, launcher log logs/20260816_restpremNH_a06_n110.log, WandB 7jgvntqe
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/archive/basic_bushrefuge_restpremium_nohide/04-restprem_nohide_a06.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --eval-config configs/evaluation/experiment_on.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:0 --log-interval 50 \
#   --wandb-group rppo_restpremNH --wandb-job-type prod \
#   --wandb-name rppo_restpremNH_a06_n110 --tag rppo_restpremNH_a06_n110
#
# Arm a07: rppo_restpremNH_a07_n110 — node 110, cuda:1
# LAUNCHED 2026-08-16, PID 2838740, launcher log logs/20260816_restpremNH_a07_n110.log, WandB 45jsidrg
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/archive/basic_bushrefuge_restpremium_nohide/04-restprem_nohide_a07.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --eval-config configs/evaluation/experiment_on.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:1 --log-interval 50 \
#   --wandb-group rppo_restpremNH --wandb-job-type prod \
#   --wandb-name rppo_restpremNH_a07_n110 --tag rppo_restpremNH_a07_n110
#
# Arm a08: rppo_restpremNH_a08_n111 — node 111, cuda:0
# LAUNCHED 2026-08-16, PID 1800371, launcher log logs/20260816_restpremNH_a08_n111.log, WandB edlxgeum
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/archive/basic_bushrefuge_restpremium_nohide/04-restprem_nohide_a08.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --eval-config configs/evaluation/experiment_on.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:0 --log-interval 50 \
#   --wandb-group rppo_restpremNH --wandb-job-type prod \
#   --wandb-name rppo_restpremNH_a08_n111 --tag rppo_restpremNH_a08_n111
#
# Arm a09: rppo_restpremNH_a09_n112 — node 112, cuda:0 — recovery_base_rate 2.9e-05 WATCH ITEM
# LAUNCHED 2026-08-16, PID 532510, launcher log logs/20260816_restpremNH_a09_n112.log, WandB neta4235
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/archive/basic_bushrefuge_restpremium_nohide/04-restprem_nohide_a09.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --eval-config configs/evaluation/experiment_on.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:0 --log-interval 50 \
#   --wandb-group rppo_restpremNH --wandb-job-type prod \
#   --wandb-name rppo_restpremNH_a09_n112 --tag rppo_restpremNH_a09_n112
#
# Arm a10: rppo_restpremNH_a10_n112 — node 112, cuda:1 — recovery_base_rate 2.1e-06 WATCH ITEM
# LAUNCHED 2026-08-16, PID 532722, launcher log logs/20260816_restpremNH_a10_n112.log, WandB ff0r7qrs
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/archive/basic_bushrefuge_restpremium_nohide/04-restprem_nohide_a10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo.yaml \
#   --eval-config configs/evaluation/experiment_on.yaml \
#   --num-envs 128 --episodes 100000000 --checkpoint-frequency 100000 \
#   --device cuda:1 --log-interval 50 \
#   --wandb-group rppo_restpremNH --wandb-job-type prod \
#   --wandb-name rppo_restpremNH_a10_n112 --tag rppo_restpremNH_a10_n112
#
# ---------------------------------------------------------------------------
# POST-LAUNCH FINDING (2026-08-16, T+1h40m) — STARTUP EVAL-TREE WALK IS THE
# DOMINANT STARTUP COST AND IS GROWING RUN-OVER-RUN.
#
# All 10 arms launched cleanly (1 PID each, distinct WandB run, no errors), but
# at T+1h40m NONE had reached the first training step; GPU util 0% on all ten
# with only a ~280 MiB CUDA context allocated. The processes are NOT hung:
# CPU time climbs steadily (a01 05:29 -> 17:18) and `wchan` is `wait_for_response`
# (CIFS network wait).
#
# Root cause: with experiment.during_training enabled, startup walks
# results/eval/ before the first GPU step. That tree now contains
#   results/eval/avoidance/metrics_history_rppo_gae/_scratch/{b03_gae,b04_gae}/
# = 24 conditions x ~723 checkpoint dirs, each with nested
# <ckpt>/models/<ckpt>/episodes/ levels -> O(1e5) directory entries to stat over
# CIFS, from an UNRELATED July-22 experiment. Sampling /proc/<pid>/fd confirmed
# the walk advancing (avoid_pred_inj70 -> avoid_rabbit_inj70 -> b03_gae/...).
# Ten concurrent runs all walking the same CIFS tree compounds it.
#
# This is why 2026-08-10 took ~54 min and 2026-08-16 exceeds 1h40m: the cost
# scales with accumulated eval scratch output, not with the run itself.
#
# NOT actioned here (out of training-runner scope, and results/ is gitignored
# data that must not be casually deleted). Surfaced to the user for a decision:
# prune/archive the _scratch tree, or bound the startup walk in code.
# ---------------------------------------------------------------------------

# ===========================================================================
# return_mode comparison (MC / MC_FIXED / GAE) — basic/04, 5 seeds each — 2026-09-03
# ===========================================================================
# 15 plain-RecurrentPPO runs measuring, in SURVIVAL STEPS, whether PPO's mainstream
# return-normalisation convention beats this project's historical one on the jump level.
#
#   MC       (configs/models/recurrent_ppo/recurrent_ppo_cmp_mc.yaml)
#            Monte-Carlo returns z-scored, used as BOTH critic target and advantage.
#            The project's historical mode; byte-identical to prior behaviour.
#   MC_FIXED (configs/models/recurrent_ppo/recurrent_ppo_cmp_mcfixed.yaml)
#            SAME MC returns, used RAW as the critic target, ADVANTAGES normalised
#            instead — the convention 9/9 surveyed mainstream PPO libraries use.
#            NEW code path, added today in af4047ac + 98b94d99.
#   GAE      (configs/models/recurrent_ppo/recurrent_ppo_cmp_gae.yaml)
#            GAE(lambda), raw critic target, normalised advantages. Unchanged.
#
# The three agent configs differ from each other ONLY in `return_mode` (verified by
# comment-stripped diff), and the MC arm is identical to recurrent_ppo.yaml.
# modulation.type: null in all three — a modulator would confound an estimator comparison.
# Env for all 15: basic/04-jump_attack_10x10 as it currently resolves, no overrides.
# 10x10 grid, obs_dim 27, action_dim 6, max_steps 500 (confirmed at smoke-test startup).
#
# wandb-group: return_mode_cmp, job-type: prod
#
# ---------------------------------------------------------------------------
# CLI-flag deviations from the config-owns-values convention (flagged to the user)
# ---------------------------------------------------------------------------
#   --num-envs 128            NOT a deviation. configs/train/recurrent_ppo.yaml already
#                             sets num_envs: 128; the flag is redundant but agrees.
#   --checkpoint-frequency 50000  DEVIATION. rPPO's config layer owns 200000. Caller asked
#                             for 50000 => 4x more checkpoints + eval videos per run.
#   --seed 42..46             DEVIATION by design. Config owns seed: 42; this is the
#                             5-seed sweep that the experiment is built on.
#   --log-interval 50         NO-OP. train.py:731 prints
#                             "[WARN] --log-interval is IGNORED: this config uses the
#                             two-level `logging:` block". The effective value comes from
#                             configs/train/recurrent_ppo.yaml logging.step.interval_iters,
#                             which is ALREADY 50 — so the requested cadence is what runs.
#                             Kept on the CLI for parity with the caller's spec.
#
# ---------------------------------------------------------------------------
# Smoke test (MC_FIXED only — the one untested-in-training code path)
# ---------------------------------------------------------------------------
# Ran to completion on node 104 cuda:1 (RTX 2080 Ti, 11 GB — the tightest-memory card
# in this batch) at the full --num-envs 128, --no-wandb, --results-dir tmp/... :
#   "RNN Type: GRU, Activation: relu, Return Mode: MC_FIXED" / "Neuromodulation: DISABLED"
#   JIT compiled, 163 iterations, 100,032 episodes, ~20-39 it/s, no OOM,
#   value loss fell monotonically 1442.9 -> ~109 (raw-return units, as MC_FIXED expects),
#   no NaN, 2 checkpoints + 2 eval videos rendered, clean "Training complete".
# Debris deleted afterwards. MC and GAE need no smoke test (unchanged code).
#
# ---------------------------------------------------------------------------
# Launched via CIFS-bypass /tmp scripts, strictly ONE AT A TIME (run_command.py is not
# parallel-safe: concurrent calls share an SSH control socket and can return the wrong
# node's PIDs). This file is the audit record; the 15 blocks below are the exact
# command lines, kept commented because only one block can ever be active.
# ---------------------------------------------------------------------------

# Run 01: rppo_cmp_mc_s42 — node 101, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_cmp_mc.yaml \
#   --episodes 1000000 \
#   --num-envs 128 \
#   --checkpoint-frequency 50000 \
#   --log-interval 50 \
#   --seed 42 \
#   --device cuda:0 \
#   --wandb-group return_mode_cmp --wandb-job-type prod \
#   --wandb-name rppo_cmp_mc_s42 --tag rppo_cmp_mc_s42

# Run 02: rppo_cmp_mc_s43 — node 101, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_cmp_mc.yaml \
#   --episodes 1000000 \
#   --num-envs 128 \
#   --checkpoint-frequency 50000 \
#   --log-interval 50 \
#   --seed 43 \
#   --device cuda:1 \
#   --wandb-group return_mode_cmp --wandb-job-type prod \
#   --wandb-name rppo_cmp_mc_s43 --tag rppo_cmp_mc_s43

# Run 03: rppo_cmp_mc_s44 — node 103, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_cmp_mc.yaml \
#   --episodes 1000000 \
#   --num-envs 128 \
#   --checkpoint-frequency 50000 \
#   --log-interval 50 \
#   --seed 44 \
#   --device cuda:0 \
#   --wandb-group return_mode_cmp --wandb-job-type prod \
#   --wandb-name rppo_cmp_mc_s44 --tag rppo_cmp_mc_s44

# Run 04: rppo_cmp_mc_s45 — node 103, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_cmp_mc.yaml \
#   --episodes 1000000 \
#   --num-envs 128 \
#   --checkpoint-frequency 50000 \
#   --log-interval 50 \
#   --seed 45 \
#   --device cuda:1 \
#   --wandb-group return_mode_cmp --wandb-job-type prod \
#   --wandb-name rppo_cmp_mc_s45 --tag rppo_cmp_mc_s45

# Run 05: rppo_cmp_mc_s46 — node 104, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_cmp_mc.yaml \
#   --episodes 1000000 \
#   --num-envs 128 \
#   --checkpoint-frequency 50000 \
#   --log-interval 50 \
#   --seed 46 \
#   --device cuda:0 \
#   --wandb-group return_mode_cmp --wandb-job-type prod \
#   --wandb-name rppo_cmp_mc_s46 --tag rppo_cmp_mc_s46

# Run 06: rppo_cmp_mcfixed_s42 — node 104, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_cmp_mcfixed.yaml \
#   --episodes 1000000 \
#   --num-envs 128 \
#   --checkpoint-frequency 50000 \
#   --log-interval 50 \
#   --seed 42 \
#   --device cuda:1 \
#   --wandb-group return_mode_cmp --wandb-job-type prod \
#   --wandb-name rppo_cmp_mcfixed_s42 --tag rppo_cmp_mcfixed_s42

# Run 07: rppo_cmp_mcfixed_s43 — node 105, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_cmp_mcfixed.yaml \
#   --episodes 1000000 \
#   --num-envs 128 \
#   --checkpoint-frequency 50000 \
#   --log-interval 50 \
#   --seed 43 \
#   --device cuda:0 \
#   --wandb-group return_mode_cmp --wandb-job-type prod \
#   --wandb-name rppo_cmp_mcfixed_s43 --tag rppo_cmp_mcfixed_s43

# Run 08: rppo_cmp_mcfixed_s44 — node 105, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_cmp_mcfixed.yaml \
#   --episodes 1000000 \
#   --num-envs 128 \
#   --checkpoint-frequency 50000 \
#   --log-interval 50 \
#   --seed 44 \
#   --device cuda:1 \
#   --wandb-group return_mode_cmp --wandb-job-type prod \
#   --wandb-name rppo_cmp_mcfixed_s44 --tag rppo_cmp_mcfixed_s44

# Run 09: rppo_cmp_mcfixed_s45 — node 106, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_cmp_mcfixed.yaml \
#   --episodes 1000000 \
#   --num-envs 128 \
#   --checkpoint-frequency 50000 \
#   --log-interval 50 \
#   --seed 45 \
#   --device cuda:0 \
#   --wandb-group return_mode_cmp --wandb-job-type prod \
#   --wandb-name rppo_cmp_mcfixed_s45 --tag rppo_cmp_mcfixed_s45

# Run 10: rppo_cmp_mcfixed_s46 — node 106, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_cmp_mcfixed.yaml \
#   --episodes 1000000 \
#   --num-envs 128 \
#   --checkpoint-frequency 50000 \
#   --log-interval 50 \
#   --seed 46 \
#   --device cuda:1 \
#   --wandb-group return_mode_cmp --wandb-job-type prod \
#   --wandb-name rppo_cmp_mcfixed_s46 --tag rppo_cmp_mcfixed_s46

# Run 11: rppo_cmp_gae_s42 — node 107, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_cmp_gae.yaml \
#   --episodes 1000000 \
#   --num-envs 128 \
#   --checkpoint-frequency 50000 \
#   --log-interval 50 \
#   --seed 42 \
#   --device cuda:0 \
#   --wandb-group return_mode_cmp --wandb-job-type prod \
#   --wandb-name rppo_cmp_gae_s42 --tag rppo_cmp_gae_s42

# Run 12: rppo_cmp_gae_s43 — node 107, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_cmp_gae.yaml \
#   --episodes 1000000 \
#   --num-envs 128 \
#   --checkpoint-frequency 50000 \
#   --log-interval 50 \
#   --seed 43 \
#   --device cuda:1 \
#   --wandb-group return_mode_cmp --wandb-job-type prod \
#   --wandb-name rppo_cmp_gae_s43 --tag rppo_cmp_gae_s43

# Run 13: rppo_cmp_gae_s44 — node 108, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_cmp_gae.yaml \
#   --episodes 1000000 \
#   --num-envs 128 \
#   --checkpoint-frequency 50000 \
#   --log-interval 50 \
#   --seed 44 \
#   --device cuda:0 \
#   --wandb-group return_mode_cmp --wandb-job-type prod \
#   --wandb-name rppo_cmp_gae_s44 --tag rppo_cmp_gae_s44

# Run 14: rppo_cmp_gae_s45 — node 108, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_cmp_gae.yaml \
#   --episodes 1000000 \
#   --num-envs 128 \
#   --checkpoint-frequency 50000 \
#   --log-interval 50 \
#   --seed 45 \
#   --device cuda:1 \
#   --wandb-group return_mode_cmp --wandb-job-type prod \
#   --wandb-name rppo_cmp_gae_s45 --tag rppo_cmp_gae_s45

# Run 15: rppo_cmp_gae_s46 — node 109, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_cmp_gae.yaml \
#   --episodes 1000000 \
#   --num-envs 128 \
#   --checkpoint-frequency 50000 \
#   --log-interval 50 \
#   --seed 46 \
#   --device cuda:0 \
#   --wandb-group return_mode_cmp --wandb-job-type prod \
#   --wandb-name rppo_cmp_gae_s46 --tag rppo_cmp_gae_s46

# ---------------------------------------------------------------------------
# LAUNCH RECORD — all 15 verified live, exactly one PID per tag, 2026-09-03T16:48:20
# Run  Tag                       Arm       Seed  Node:GPU  PID      WandB     Log
# 1    rppo_cmp_mc_s42           mc        42    101:0     196840   rk3huayr  logs/20260903_163031.log
# 2    rppo_cmp_mc_s43           mc        43    101:1     197637   x2jxkpq8  logs/20260903_163215.log
# 3    rppo_cmp_mc_s44           mc        44    103:0     197326   4dnvtpqf  logs/20260903_163316.log
# 4    rppo_cmp_mc_s45           mc        45    103:1     197912   9kjjj5t8  logs/20260903_163418.log
# 5    rppo_cmp_mc_s46           mc        46    104:0     201684   mx8orfd1  logs/20260903_163519.log
# 6    rppo_cmp_mcfixed_s42      mcfixed   42    104:1     202279   k7tu4ch0  logs/20260903_163621.log
# 7    rppo_cmp_mcfixed_s43      mcfixed   43    105:0     199549   tifzlhcq  logs/20260903_163722.log
# 8    rppo_cmp_mcfixed_s44      mcfixed   44    105:1     200169   0t83gfxv  logs/20260903_163824.log
# 9    rppo_cmp_mcfixed_s45      mcfixed   45    106:0     4406     x6me4z6a  logs/20260903_163925.log
# 10   rppo_cmp_mcfixed_s46      mcfixed   46    106:1     5704     kqjxkgwu  logs/20260903_164027.log
# 11   rppo_cmp_gae_s42          gae       42    107:0     13718    g20s999t  logs/20260903_164128.log
# 12   rppo_cmp_gae_s43          gae       43    107:1     14286    x36zqm96  logs/20260903_164229.log
# 13   rppo_cmp_gae_s44          gae       44    108:0     4808     s1lpg7o8  logs/20260903_164330.log
# 14   rppo_cmp_gae_s45          gae       45    108:1     5428     pwn54tw7  logs/20260903_164431.log
# 15   rppo_cmp_gae_s46          gae       46    109:0     20183    0ghnqaly  logs/20260903_164534.log
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# return_mode_cmp_10m — MC / MC_FIXED / GAE return-estimator comparison — 2026-09-04
# 10M-EPISODE RE-RUN of the 15-run 1M comparison launched 2026-09-03 (block above).
# The 1M results are KEPT; these runs use DISTINCT tags carrying a `10m` marker
# (rppo_cmp10m_*) so nothing overwrites results/JAX_RecurrentPPO/*_rppo_cmp_*.
#
# 3 arms x 5 seeds (42-46). Env identical for all 15:
#   configs/environment/experiment/basic/04-jump_attack_10x10.yaml (as it resolves;
#   no overrides). decay_power resolves to the canonical 1.0 from environment/default.
# The three agent configs are byte-identical except for one line, `return_mode`:
#   recurrent_ppo_cmp_mc.yaml       return_mode "MC"       (z-scored MC as target AND advantage)
#   recurrent_ppo_cmp_mcfixed.yaml  return_mode "MC_FIXED" (raw MC target, normalised advantages)
#   recurrent_ppo_cmp_gae.yaml      return_mode "GAE"      (GAE(lambda), raw target, normalised adv)
# All three: algorithm RecurrentPPO, modulation.type null (a modulator would confound
# an estimator comparison).
#
# TWO DELIBERATE CHANGES FROM THE 1M LAUNCH — both to match the project's standard 10M
# baseline (the 14-arm sensor-ladder study) rather than scaling the short-run settings up:
#   --episodes 10000000        (was 1000000)  — the sensor-ladder budget, so these results
#                              sit on comparable footing with that study.
#   --checkpoint-frequency 200000 (was 50000) — at 10M this gives 50 checkpoints/run, the
#                              sensor-ladder cadence. Keeping 50000 would have produced 200
#                              checkpoints AND 200 eval-video renders per run, 3000 across
#                              the batch.
#
# CONFIG-OWNED-VALUES NOTE: --num-envs 128 and --checkpoint-frequency 200000 exactly match
# the values configs/train/recurrent_ppo.yaml already carries, so they are redundant rather
# than deviating. --seed is a genuine, intended deviation: this is a 5-seed sweep and each
# row needs its own seed. --log-interval 50 is a knowing no-op on this config (the two-level
# `logging:` block governs and already uses 50) — passed for command-line consistency; the
# resulting [WARN] is expected and not a problem.
#
# PRE-FLIGHT (2026-09-04, all 8 nodes): nas01 CIFS mounted (192T, 41T free) on every node;
# every assigned GPU idle (no compute processes); JAX GPU-compile check passed on all 8
# (jax 0.9.0.1, real 4x4 matmul JIT on platform=gpu, version-matched across the cluster);
# zero train.py processes cluster-wide; no results dir matching *cmp10m* pre-existed.
# No smoke test: all three code paths incl. MC_FIXED ran 1M episodes to completion on these
# same configs and nodes hours earlier.
#
# wandb-group: return_mode_cmp_10m, job-type: prod
# run_command.py is NOT parallel-safe (shared SSH control socket can return another node's
# PIDs) -> launched STRICTLY ONE AT A TIME, each verified by pgrep before the next starts.
# CIFS-bypass: launched via per-run /tmp scripts — this file is the audit record.
# ---------------------------------------------------------------------------

# Run 1: rppo_cmp10m_mc_s42 — node 101, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_cmp_mc.yaml \
#   --episodes 10000000 \
#   --num-envs 128 \
#   --checkpoint-frequency 200000 \
#   --log-interval 50 \
#   --seed 42 \
#   --device cuda:0 \
#   --wandb-group return_mode_cmp_10m --wandb-job-type prod \
#   --wandb-name rppo_cmp10m_mc_s42 --tag rppo_cmp10m_mc_s42

# Run 2: rppo_cmp10m_mc_s43 — node 101, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_cmp_mc.yaml \
#   --episodes 10000000 \
#   --num-envs 128 \
#   --checkpoint-frequency 200000 \
#   --log-interval 50 \
#   --seed 43 \
#   --device cuda:1 \
#   --wandb-group return_mode_cmp_10m --wandb-job-type prod \
#   --wandb-name rppo_cmp10m_mc_s43 --tag rppo_cmp10m_mc_s43

# Run 3: rppo_cmp10m_mc_s44 — node 103, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_cmp_mc.yaml \
#   --episodes 10000000 \
#   --num-envs 128 \
#   --checkpoint-frequency 200000 \
#   --log-interval 50 \
#   --seed 44 \
#   --device cuda:0 \
#   --wandb-group return_mode_cmp_10m --wandb-job-type prod \
#   --wandb-name rppo_cmp10m_mc_s44 --tag rppo_cmp10m_mc_s44

# Run 4: rppo_cmp10m_mc_s45 — node 103, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_cmp_mc.yaml \
#   --episodes 10000000 \
#   --num-envs 128 \
#   --checkpoint-frequency 200000 \
#   --log-interval 50 \
#   --seed 45 \
#   --device cuda:1 \
#   --wandb-group return_mode_cmp_10m --wandb-job-type prod \
#   --wandb-name rppo_cmp10m_mc_s45 --tag rppo_cmp10m_mc_s45

# Run 5: rppo_cmp10m_mc_s46 — node 104, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_cmp_mc.yaml \
#   --episodes 10000000 \
#   --num-envs 128 \
#   --checkpoint-frequency 200000 \
#   --log-interval 50 \
#   --seed 46 \
#   --device cuda:0 \
#   --wandb-group return_mode_cmp_10m --wandb-job-type prod \
#   --wandb-name rppo_cmp10m_mc_s46 --tag rppo_cmp10m_mc_s46

# Run 6: rppo_cmp10m_mcfixed_s42 — node 104, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_cmp_mcfixed.yaml \
#   --episodes 10000000 \
#   --num-envs 128 \
#   --checkpoint-frequency 200000 \
#   --log-interval 50 \
#   --seed 42 \
#   --device cuda:1 \
#   --wandb-group return_mode_cmp_10m --wandb-job-type prod \
#   --wandb-name rppo_cmp10m_mcfixed_s42 --tag rppo_cmp10m_mcfixed_s42

# Run 7: rppo_cmp10m_mcfixed_s43 — node 105, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_cmp_mcfixed.yaml \
#   --episodes 10000000 \
#   --num-envs 128 \
#   --checkpoint-frequency 200000 \
#   --log-interval 50 \
#   --seed 43 \
#   --device cuda:0 \
#   --wandb-group return_mode_cmp_10m --wandb-job-type prod \
#   --wandb-name rppo_cmp10m_mcfixed_s43 --tag rppo_cmp10m_mcfixed_s43

# Run 8: rppo_cmp10m_mcfixed_s44 — node 105, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_cmp_mcfixed.yaml \
#   --episodes 10000000 \
#   --num-envs 128 \
#   --checkpoint-frequency 200000 \
#   --log-interval 50 \
#   --seed 44 \
#   --device cuda:1 \
#   --wandb-group return_mode_cmp_10m --wandb-job-type prod \
#   --wandb-name rppo_cmp10m_mcfixed_s44 --tag rppo_cmp10m_mcfixed_s44

# Run 9: rppo_cmp10m_mcfixed_s45 — node 106, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_cmp_mcfixed.yaml \
#   --episodes 10000000 \
#   --num-envs 128 \
#   --checkpoint-frequency 200000 \
#   --log-interval 50 \
#   --seed 45 \
#   --device cuda:0 \
#   --wandb-group return_mode_cmp_10m --wandb-job-type prod \
#   --wandb-name rppo_cmp10m_mcfixed_s45 --tag rppo_cmp10m_mcfixed_s45

# Run 10: rppo_cmp10m_mcfixed_s46 — node 106, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_cmp_mcfixed.yaml \
#   --episodes 10000000 \
#   --num-envs 128 \
#   --checkpoint-frequency 200000 \
#   --log-interval 50 \
#   --seed 46 \
#   --device cuda:1 \
#   --wandb-group return_mode_cmp_10m --wandb-job-type prod \
#   --wandb-name rppo_cmp10m_mcfixed_s46 --tag rppo_cmp10m_mcfixed_s46

# Run 11: rppo_cmp10m_gae_s42 — node 107, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_cmp_gae.yaml \
#   --episodes 10000000 \
#   --num-envs 128 \
#   --checkpoint-frequency 200000 \
#   --log-interval 50 \
#   --seed 42 \
#   --device cuda:0 \
#   --wandb-group return_mode_cmp_10m --wandb-job-type prod \
#   --wandb-name rppo_cmp10m_gae_s42 --tag rppo_cmp10m_gae_s42

# Run 12: rppo_cmp10m_gae_s43 — node 107, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_cmp_gae.yaml \
#   --episodes 10000000 \
#   --num-envs 128 \
#   --checkpoint-frequency 200000 \
#   --log-interval 50 \
#   --seed 43 \
#   --device cuda:1 \
#   --wandb-group return_mode_cmp_10m --wandb-job-type prod \
#   --wandb-name rppo_cmp10m_gae_s43 --tag rppo_cmp10m_gae_s43

# Run 13: rppo_cmp10m_gae_s44 — node 108, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_cmp_gae.yaml \
#   --episodes 10000000 \
#   --num-envs 128 \
#   --checkpoint-frequency 200000 \
#   --log-interval 50 \
#   --seed 44 \
#   --device cuda:0 \
#   --wandb-group return_mode_cmp_10m --wandb-job-type prod \
#   --wandb-name rppo_cmp10m_gae_s44 --tag rppo_cmp10m_gae_s44

# Run 14: rppo_cmp10m_gae_s45 — node 108, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_cmp_gae.yaml \
#   --episodes 10000000 \
#   --num-envs 128 \
#   --checkpoint-frequency 200000 \
#   --log-interval 50 \
#   --seed 45 \
#   --device cuda:1 \
#   --wandb-group return_mode_cmp_10m --wandb-job-type prod \
#   --wandb-name rppo_cmp10m_gae_s45 --tag rppo_cmp10m_gae_s45

# Run 15: rppo_cmp10m_gae_s46 — node 109, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_cmp_gae.yaml \
#   --episodes 10000000 \
#   --num-envs 128 \
#   --checkpoint-frequency 200000 \
#   --log-interval 50 \
#   --seed 46 \
#   --device cuda:0 \
#   --wandb-group return_mode_cmp_10m --wandb-job-type prod \
#   --wandb-name rppo_cmp10m_gae_s46 --tag rppo_cmp10m_gae_s46

# ---------------------------------------------------------------------------
# LAUNCH RECORD — all 15 verified live, exactly one PID per tag, 2026-09-04T17:54:13
# Cluster-wide sweep confirmed exactly 15 'cmp10m' processes (2 per node except 109:1)
# and ZERO surviving 1M-set processes. All 15 1M result dirs (*_rppo_cmp_*) intact.
# Run  Tag                        Arm       Seed  Node:GPU  PID      WandB     Log
# 1    rppo_cmp10m_mc_s42         mc        42    101:0     271088   xy7nic92  logs/20260904_173800.log
# 2    rppo_cmp10m_mc_s43         mc        43    101:1     271676   cmqugy51  logs/20260904_173901.log
# 3    rppo_cmp10m_mc_s44         mc        44    103:0     269196   quydmpd7  logs/20260904_174002.log
# 4    rppo_cmp10m_mc_s45         mc        45    103:1     269769   ymbhe3qp  logs/20260904_174104.log
# 5    rppo_cmp10m_mc_s46         mc        46    104:0     275814   uqnl1scm  logs/20260904_174205.log
# 6    rppo_cmp10m_mcfixed_s42    mcfixed   42    104:1     276428   se72bm9i  logs/20260904_174306.log
# 7    rppo_cmp10m_mcfixed_s43    mcfixed   43    105:0     273660   ukte3hbu  logs/20260904_174408.log
# 8    rppo_cmp10m_mcfixed_s44    mcfixed   44    105:1     274271   ef2pg37t  logs/20260904_174509.log
# 9    rppo_cmp10m_mcfixed_s45    mcfixed   45    106:0     79245    b09iehij  logs/20260904_174610.log
# 10   rppo_cmp10m_mcfixed_s46    mcfixed   46    106:1     80124    vpabnrrz  logs/20260904_174711.log
# 11   rppo_cmp10m_gae_s42        gae       42    107:0     87229    4sqc0lsd  logs/20260904_174813.log
# 12   rppo_cmp10m_gae_s43        gae       43    107:1     88075    haw7hl3e  logs/20260904_174914.log
# 13   rppo_cmp10m_gae_s44        gae       44    108:0     79124    whdabu5w  logs/20260904_175015.log
# 14   rppo_cmp10m_gae_s45        gae       45    108:1     79970    4ug6okvu  logs/20260904_175116.log
# 15   rppo_cmp10m_gae_s46        gae       46    109:0     59573    96ej3ngm  logs/20260904_175218.log
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# return_mode_cmp_10m — FOURTH ARM: GAE_NORM — 2026-09-04
# Adds the missing cell of the 2x2 (estimator x normalisation scheme) to the
# 15-run MC / MC_FIXED / GAE batch launched at 17:54 today (block above).
#   MC        Monte-Carlo estimator, MATCHED scale   (z-scored target, raw residual adv)
#   MC_FIXED  Monte-Carlo estimator, SPLIT scale     (raw target, normalised adv)
#   GAE       GAE(lambda) estimator, SPLIT scale
#   GAE_NORM  GAE(lambda) estimator, MATCHED scale   <-- THIS ARM
# Hypothesis: MC's ~3.5x survival advantage at 1M comes from the MATCHED SCALE,
# not from the Monte-Carlo estimator. If so, GAE_NORM tracks MC; if the estimator
# is what matters, GAE_NORM tracks GAE.
#
# IDENTICAL to the 15 in-flight runs in every respect except the agent config,
# the seed, the tag and the node/GPU. Verified: the gaenorm agent config's `agent`
# block differs from recurrent_ppo_cmp_gae.yaml in exactly ONE key —
# return_mode "GAE" -> "GAE_NORM". No `extends:`; return_mode is in the trainer's
# LEGAL_RETURN_MODES and validates. modulation.type null (a modulator would confound).
# Env: basic/04-jump_attack_10x10.yaml, no overrides; decay_power resolves to the
# canonical 1.0 from environment/default.yaml (CONFIG_CRITICAL_SETTINGS registry).
#
# CONFIG-OWNED-VALUES NOTE (unchanged from the 17:54 block): --num-envs 128 and
# --checkpoint-frequency 200000 exactly match configs/train/recurrent_ppo.yaml, so they
# are redundant rather than deviating — passed for byte-parity with the other three arms.
# --seed IS a genuine intended deviation (5-seed sweep). --log-interval 50 is a knowing
# no-op on this config; the resulting [WARN] is expected.
#
# PRE-FLIGHT (2026-09-04, nodes 110/111/112): nas01 CIFS mounted (192T, 41T free) on all
# three; all five assigned GPUs FREE (RTX 3090, 0% util, <=64 MiB residual, no compute
# processes); zero train.py processes on all three nodes; JAX GPU-compile check passed on
# all three (jax 0.9.0.1, real 4x4 matmul JIT on platform=gpu — version-matched to the
# cluster and to the 15 in-flight runs); no results dir matching *gaenorm* pre-existed.
#
# wandb-group: return_mode_cmp_10m (same group as the other three arms), job-type: prod
# run_command.py is NOT parallel-safe (shared SSH control socket can return another node's
# PIDs) -> launched STRICTLY ONE AT A TIME, each verified by pgrep before the next starts.
# CIFS-bypass: launched via per-run /tmp scripts — this file is the audit record.
# ---------------------------------------------------------------------------

# Run 16: rppo_cmp10m_gaenorm_s42 — node 110, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_cmp_gaenorm.yaml \
#   --episodes 10000000 \
#   --num-envs 128 \
#   --checkpoint-frequency 200000 \
#   --log-interval 50 \
#   --seed 42 \
#   --device cuda:0 \
#   --wandb-group return_mode_cmp_10m --wandb-job-type prod \
#   --wandb-name rppo_cmp10m_gaenorm_s42 --tag rppo_cmp10m_gaenorm_s42

# Run 17: rppo_cmp10m_gaenorm_s43 — node 110, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_cmp_gaenorm.yaml \
#   --episodes 10000000 \
#   --num-envs 128 \
#   --checkpoint-frequency 200000 \
#   --log-interval 50 \
#   --seed 43 \
#   --device cuda:1 \
#   --wandb-group return_mode_cmp_10m --wandb-job-type prod \
#   --wandb-name rppo_cmp10m_gaenorm_s43 --tag rppo_cmp10m_gaenorm_s43

# Run 18: rppo_cmp10m_gaenorm_s44 — node 111, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_cmp_gaenorm.yaml \
#   --episodes 10000000 \
#   --num-envs 128 \
#   --checkpoint-frequency 200000 \
#   --log-interval 50 \
#   --seed 44 \
#   --device cuda:0 \
#   --wandb-group return_mode_cmp_10m --wandb-job-type prod \
#   --wandb-name rppo_cmp10m_gaenorm_s44 --tag rppo_cmp10m_gaenorm_s44

# Run 19: rppo_cmp10m_gaenorm_s45 — node 111, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_cmp_gaenorm.yaml \
#   --episodes 10000000 \
#   --num-envs 128 \
#   --checkpoint-frequency 200000 \
#   --log-interval 50 \
#   --seed 45 \
#   --device cuda:1 \
#   --wandb-group return_mode_cmp_10m --wandb-job-type prod \
#   --wandb-name rppo_cmp10m_gaenorm_s45 --tag rppo_cmp10m_gaenorm_s45

# Run 20: rppo_cmp10m_gaenorm_s46 — node 112, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_cmp_gaenorm.yaml \
#   --episodes 10000000 \
#   --num-envs 128 \
#   --checkpoint-frequency 200000 \
#   --log-interval 50 \
#   --seed 46 \
#   --device cuda:0 \
#   --wandb-group return_mode_cmp_10m --wandb-job-type prod \
#   --wandb-name rppo_cmp10m_gaenorm_s46 --tag rppo_cmp10m_gaenorm_s46

# ---------------------------------------------------------------------------
# LAUNCH RECORD — all 5 verified live, exactly one PID per tag, 2026-09-04T19:07
# Cluster sweep of 110/111/112 found exactly 5 train.py processes (2+2+1), no duplicates.
# Ground truth: every run's saved models/config.yaml reads `return_mode: GAE_NORM` and
# `group: return_mode_cmp_10m`. All 5 observed stepping on GPU (util 89-99%, ~5.5 GB).
# Run  Tag                        Arm       Seed  Node:GPU  PID    WandB     Log
# 16   rppo_cmp10m_gaenorm_s42    gaenorm   42    110:0     4845   26mwmoc9  logs/20260904_185745.log
# 17   rppo_cmp10m_gaenorm_s43    gaenorm   43    110:1     5834   ac522oud  logs/20260904_185917.log
# 18   rppo_cmp10m_gaenorm_s44    gaenorm   44    111:0     17873  0mtwmifc  logs/20260904_190034.log
# 19   rppo_cmp10m_gaenorm_s45    gaenorm   45    111:1     18830  87a1r9ld  logs/20260904_190152.log
# 20   rppo_cmp10m_gaenorm_s46    gaenorm   46    112:0     4943   1v91itww  logs/20260904_190311.log
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# return_mode_cmp_10m — FIFTH ARM: MC_RAW — 2026-09-04
# Completes the estimator x scale-scheme comparison begun with the 15-run
# MC / MC_FIXED / GAE batch (17:54) and the 5-run GAE_NORM batch (18:57):
#   MC        Monte-Carlo estimator, MATCHED scale at ~1   (z-scored target, raw residual adv)
#   MC_FIXED  Monte-Carlo estimator, SPLIT scale           (raw target, separately z-scored adv)
#   GAE       GAE(lambda) estimator, SPLIT scale
#   GAE_NORM  GAE(lambda) estimator, MATCHED scale at ~1
#   MC_RAW    Monte-Carlo estimator, MATCHED scale at ~24  <-- THIS ARM (nothing rescaled)
# Question this arm answers: the first four arms cannot separate "critic target and
# advantage must share UNITS" from "the advantage must land near spread 1", because
# every matched-scale arm is matched AT 1. MC_RAW is matched at the LARGE raw scale.
# If matching is what matters, MC_RAW tracks MC (138.8 mean survival steps at 1M);
# if landing near spread 1 is what matters, MC_RAW tracks MC_FIXED (40.0) / GAE (41.9).
#
# IDENTICAL to the 20 sibling runs in every respect except the agent config, the seed,
# the tag and the node/GPU. Verified pre-flight: recurrent_ppo_cmp_mcraw.yaml has NO
# `extends:`, its `agent` block differs from recurrent_ppo_cmp_mcfixed.yaml in exactly
# ONE key (return_mode "MC_FIXED" -> "MC_RAW"), and MC_RAW is in the trainer's
# LEGAL_RETURN_MODES (src/models/recurrent_ppo_trainer.py:193) with a real implemented
# branch (line 444: raw MC returns as target, raw `returns - value` residual as
# advantage, no normalisation line). modulation.type null (a modulator would confound).
# Env: basic/04-jump_attack_10x10.yaml, no overrides; decay_power resolves to the
# canonical 1.0 from environment/default.yaml (CONFIG_CRITICAL_SETTINGS registry).
#
# CONFIG-OWNED-VALUES NOTE (unchanged from the 17:54 and 18:57 blocks): --num-envs 128
# and --checkpoint-frequency 200000 exactly match configs/train/recurrent_ppo.yaml, so
# they are redundant rather than deviating — passed for byte-parity with the other four
# arms. --seed IS a genuine intended deviation (5-seed sweep). --log-interval 50 is a
# knowing no-op on this config (the `logging:` block supersedes it); the [WARN] is expected.
#
# PRE-FLIGHT (2026-09-04, nodes 102/105/106/109/112): nas01 CIFS mounted (192T, 41T free)
# on all five; all five assigned GPUs FREE (102:0 RTX 4090; 105:0 RTX 2080 Ti; 106:1,
# 109:1, 112:1 RTX 3090 — 0% util, <=133 MiB residual, no compute processes); JAX
# GPU-compile check passed on all five (jax 0.9.0.1, real 4x4 matmul JIT on platform=gpu
# — version-matched to the cluster and to the 20 sibling runs); no results dir matching
# *mcraw* pre-existed.
# NOTE ON WHY 105:0 AND 106:1 ARE FREE: rppo_cmp10m_mcfixed_s43 (105:0) and
# rppo_cmp10m_mcfixed_s46 (106:1) COMPLETED their full 10M-episode budget earlier today
# ("Training complete." in logs/20260904_174408.log and logs/20260904_174711.log) — they
# did not crash. Their diary rows still read `running`.
# Deliberately spread across single free GPUs on otherwise-occupied nodes so that nodes
# 113 and 114 stay whole for heavier jobs — NOT consolidated.
#
# wandb-group: return_mode_cmp_10m (same group as the other four arms), job-type: prod
# run_command.py is NOT parallel-safe (shared SSH control socket can return another node's
# PIDs) -> launched STRICTLY ONE AT A TIME, each verified by pgrep before the next starts.
# CIFS-bypass: launched via per-run /tmp scripts — this file is the audit record.
# ---------------------------------------------------------------------------

# Run 21: rppo_cmp10m_mcraw_s42 — node 105, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_cmp_mcraw.yaml \
#   --episodes 10000000 \
#   --num-envs 128 \
#   --checkpoint-frequency 200000 \
#   --log-interval 50 \
#   --seed 42 \
#   --device cuda:0 \
#   --wandb-group return_mode_cmp_10m --wandb-job-type prod \
#   --wandb-name rppo_cmp10m_mcraw_s42 --tag rppo_cmp10m_mcraw_s42

# Run 22: rppo_cmp10m_mcraw_s43 — node 106, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_cmp_mcraw.yaml \
#   --episodes 10000000 \
#   --num-envs 128 \
#   --checkpoint-frequency 200000 \
#   --log-interval 50 \
#   --seed 43 \
#   --device cuda:1 \
#   --wandb-group return_mode_cmp_10m --wandb-job-type prod \
#   --wandb-name rppo_cmp10m_mcraw_s43 --tag rppo_cmp10m_mcraw_s43

# Run 23: rppo_cmp10m_mcraw_s44 — node 109, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_cmp_mcraw.yaml \
#   --episodes 10000000 \
#   --num-envs 128 \
#   --checkpoint-frequency 200000 \
#   --log-interval 50 \
#   --seed 44 \
#   --device cuda:1 \
#   --wandb-group return_mode_cmp_10m --wandb-job-type prod \
#   --wandb-name rppo_cmp10m_mcraw_s44 --tag rppo_cmp10m_mcraw_s44

# Run 24: rppo_cmp10m_mcraw_s45 — node 112, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_cmp_mcraw.yaml \
#   --episodes 10000000 \
#   --num-envs 128 \
#   --checkpoint-frequency 200000 \
#   --log-interval 50 \
#   --seed 45 \
#   --device cuda:1 \
#   --wandb-group return_mode_cmp_10m --wandb-job-type prod \
#   --wandb-name rppo_cmp10m_mcraw_s45 --tag rppo_cmp10m_mcraw_s45

# Run 25: rppo_cmp10m_mcraw_s46 — node 102, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/recurrent_ppo_cmp_mcraw.yaml \
#   --episodes 10000000 \
#   --num-envs 128 \
#   --checkpoint-frequency 200000 \
#   --log-interval 50 \
#   --seed 46 \
#   --device cuda:0 \
#   --wandb-group return_mode_cmp_10m --wandb-job-type prod \
#   --wandb-name rppo_cmp10m_mcraw_s46 --tag rppo_cmp10m_mcraw_s46

# ---------------------------------------------------------------------------
# LAUNCH RECORD — all 5 verified TRAINING, exactly one PID per tag, 2026-09-04T22:06
# Verification beyond process-existence: every run's episode counter advanced between
# two samples ~25 s apart (~400k -> ~430k of 10,000,000 episodes at ~1000-1350 it/s,
# finite losses, no NaN), and every assigned GPU is resident and busy (80-99% util,
# 4.5-5.6 GB). Node 102's loose pgrep shows 2 hits only because this Claude container
# runs ON node 102 — the exact `bin/python train.py` match returns exactly 1.
# Ground truth: every run's saved models/config.yaml reads `return_mode: MC_RAW`,
# `algorithm: RecurrentPPO`, `modulation.type: null`, `num_envs: 128`, `decay_power: 1.0`.
# KNOWN SNAPSHOT ARTIFACT (pre-existing, NOT introduced here): the saved config.yaml
# records `seed: 42` and `episodes: 100` for ALL FIVE — but so do all 20 sibling runs
# (mc/mcfixed/gae/gaenorm), which demonstrably ran to 10M episodes. The saved YAML keeps
# the pre-CLI-override values for those two fields. The per-run seed IS applied: the
# trainer's own startup banner prints seed 42/43/44/45/46 respectively, and the tqdm
# total reads 10,000,000. Verify seed/episodes from the banner or WandB, not from the
# saved config.yaml.
# Run  Tag                      Arm     Seed  Node:GPU  PID      WandB     Log
# 21   rppo_cmp10m_mcraw_s42    mcraw   42    105:0     442997   j0vuwph7  logs/20260904_215843.log
# 22   rppo_cmp10m_mcraw_s43    mcraw   43    106:1     256258   ls7riwt1  logs/20260904_215901.log
# 23   rppo_cmp10m_mcraw_s44    mcraw   44    109:1     139018   yo02nvg9  logs/20260904_215911.log
# 24   rppo_cmp10m_mcraw_s45    mcraw   45    112:1     39113    37oqpt8k  logs/20260904_215922.log
# 25   rppo_cmp10m_mcraw_s46    mcraw   46    102:0     1921862  o6yac86p  logs/20260904_215932.log
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# NMN input x site grid — 16 runs — 2026-09-07
# Study: docs/experiments/active/nmn_input_site_grid/NMN_INPUT_SITE_GRID.md
# Grid: WHAT the modulator reads (ALL / interoceptive-2 / exteroceptive-4)
#       x WHERE it writes (none / encoder / rnn / actor / critic / all-four).
# Env: basic/04-jump_attack_10x10 on all sixteen. Agent: RecurrentPPO, return_mode MC.
# seed (42), num_envs (128) and checkpoint_frequency (200000) are CONFIG-OWNED —
# deliberately NOT passed on the CLI. --episodes IS passed (config's 100 is a placeholder).
# Node 114 deliberately left whole (reserved for heavier jobs) despite 4 free Ada cards.
# Code SHA pinned for the whole wave: a71f4471.
# ---------------------------------------------------------------------------

# Run 1: rppo_nmnsite_t1none_s42 — node 106, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid/nmnsite_t1none.yaml \
#   --episodes 10000000 \
#   --device cuda:0 \
#   --log-interval 10 \
#   --wandb-group nmn_input_site_grid --wandb-job-type pilot \
#   --wandb-name rppo_nmnsite_t1none_s42 --tag rppo_nmnsite_t1none_s42

# Run 2: rppo_nmnsite_t2enc_ALL_s42 — node 106, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid/nmnsite_t2enc_ALL.yaml \
#   --episodes 10000000 \
#   --device cuda:1 \
#   --log-interval 10 \
#   --wandb-group nmn_input_site_grid --wandb-job-type pilot \
#   --wandb-name rppo_nmnsite_t2enc_ALL_s42 --tag rppo_nmnsite_t2enc_ALL_s42

# Run 3: rppo_nmnsite_t2enc_I_s42 — node 107, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid/nmnsite_t2enc_I.yaml \
#   --episodes 10000000 \
#   --device cuda:0 \
#   --log-interval 10 \
#   --wandb-group nmn_input_site_grid --wandb-job-type pilot \
#   --wandb-name rppo_nmnsite_t2enc_I_s42 --tag rppo_nmnsite_t2enc_I_s42

# Run 4: rppo_nmnsite_t2enc_X_s42 — node 107, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid/nmnsite_t2enc_X.yaml \
#   --episodes 10000000 \
#   --device cuda:1 \
#   --log-interval 10 \
#   --wandb-group nmn_input_site_grid --wandb-job-type pilot \
#   --wandb-name rppo_nmnsite_t2enc_X_s42 --tag rppo_nmnsite_t2enc_X_s42

# Run 5: rppo_nmnsite_t3rnn_ALL_s42 — node 108, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid/nmnsite_t3rnn_ALL.yaml \
#   --episodes 10000000 \
#   --device cuda:0 \
#   --log-interval 10 \
#   --wandb-group nmn_input_site_grid --wandb-job-type pilot \
#   --wandb-name rppo_nmnsite_t3rnn_ALL_s42 --tag rppo_nmnsite_t3rnn_ALL_s42

# Run 6: rppo_nmnsite_t3rnn_I_s42 — node 108, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid/nmnsite_t3rnn_I.yaml \
#   --episodes 10000000 \
#   --device cuda:1 \
#   --log-interval 10 \
#   --wandb-group nmn_input_site_grid --wandb-job-type pilot \
#   --wandb-name rppo_nmnsite_t3rnn_I_s42 --tag rppo_nmnsite_t3rnn_I_s42

# Run 7: rppo_nmnsite_t3rnn_X_s42 — node 109, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid/nmnsite_t3rnn_X.yaml \
#   --episodes 10000000 \
#   --device cuda:0 \
#   --log-interval 10 \
#   --wandb-group nmn_input_site_grid --wandb-job-type pilot \
#   --wandb-name rppo_nmnsite_t3rnn_X_s42 --tag rppo_nmnsite_t3rnn_X_s42

# Run 8: rppo_nmnsite_t4act_ALL_s42 — node 109, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid/nmnsite_t4act_ALL.yaml \
#   --episodes 10000000 \
#   --device cuda:1 \
#   --log-interval 10 \
#   --wandb-group nmn_input_site_grid --wandb-job-type pilot \
#   --wandb-name rppo_nmnsite_t4act_ALL_s42 --tag rppo_nmnsite_t4act_ALL_s42

# Run 9: rppo_nmnsite_t4act_I_s42 — node 110, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid/nmnsite_t4act_I.yaml \
#   --episodes 10000000 \
#   --device cuda:0 \
#   --log-interval 10 \
#   --wandb-group nmn_input_site_grid --wandb-job-type pilot \
#   --wandb-name rppo_nmnsite_t4act_I_s42 --tag rppo_nmnsite_t4act_I_s42

# Run 10: rppo_nmnsite_t4act_X_s42 — node 110, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid/nmnsite_t4act_X.yaml \
#   --episodes 10000000 \
#   --device cuda:1 \
#   --log-interval 10 \
#   --wandb-group nmn_input_site_grid --wandb-job-type pilot \
#   --wandb-name rppo_nmnsite_t4act_X_s42 --tag rppo_nmnsite_t4act_X_s42

# Run 11: rppo_nmnsite_t5crt_ALL_s42 — node 111, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid/nmnsite_t5crt_ALL.yaml \
#   --episodes 10000000 \
#   --device cuda:0 \
#   --log-interval 10 \
#   --wandb-group nmn_input_site_grid --wandb-job-type pilot \
#   --wandb-name rppo_nmnsite_t5crt_ALL_s42 --tag rppo_nmnsite_t5crt_ALL_s42

# Run 12: rppo_nmnsite_t5crt_I_s42 — node 111, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid/nmnsite_t5crt_I.yaml \
#   --episodes 10000000 \
#   --device cuda:1 \
#   --log-interval 10 \
#   --wandb-group nmn_input_site_grid --wandb-job-type pilot \
#   --wandb-name rppo_nmnsite_t5crt_I_s42 --tag rppo_nmnsite_t5crt_I_s42

# Run 13: rppo_nmnsite_t5crt_X_s42 — node 112, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid/nmnsite_t5crt_X.yaml \
#   --episodes 10000000 \
#   --device cuda:0 \
#   --log-interval 10 \
#   --wandb-group nmn_input_site_grid --wandb-job-type pilot \
#   --wandb-name rppo_nmnsite_t5crt_X_s42 --tag rppo_nmnsite_t5crt_X_s42

# Run 14: rppo_nmnsite_t16quad_ALL_s42 — node 112, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid/nmnsite_t16quad_ALL.yaml \
#   --episodes 10000000 \
#   --device cuda:1 \
#   --log-interval 10 \
#   --wandb-group nmn_input_site_grid --wandb-job-type pilot \
#   --wandb-name rppo_nmnsite_t16quad_ALL_s42 --tag rppo_nmnsite_t16quad_ALL_s42

# Run 15: rppo_nmnsite_t16quad_I_s42 — node 113, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid/nmnsite_t16quad_I.yaml \
#   --episodes 10000000 \
#   --device cuda:0 \
#   --log-interval 10 \
#   --wandb-group nmn_input_site_grid --wandb-job-type pilot \
#   --wandb-name rppo_nmnsite_t16quad_I_s42 --tag rppo_nmnsite_t16quad_I_s42

# Run 16: rppo_nmnsite_t16quad_X_s42 — node 113, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid/nmnsite_t16quad_X.yaml \
#   --episodes 10000000 \
#   --device cuda:1 \
#   --log-interval 10 \
#   --wandb-group nmn_input_site_grid --wandb-job-type pilot \
#   --wandb-name rppo_nmnsite_t16quad_X_s42 --tag rppo_nmnsite_t16quad_X_s42

# ---------------------------------------------------------------------------
# LAUNCH RECORD — all 16 verified TRAINING, exactly one PID per tag, 2026-09-07T05:06
# Verification beyond process-existence: every run's episode counter advanced between
# two samples ~95 s apart, and every assigned GPU is resident and busy (72-100% util,
# 5.4-6.7 GB). Node 114 left whole as instructed (all 4 Ada cards idle, 1 MiB).
# Ground truth from each run's OWN saved models/config.yaml: modulation.sites and
# modulation.input_sensors match the intended arm on all 16 (t1none: type null);
# TOP-LEVEL seed: 42 and episodes: 10000000 on all 16; num_envs 128; decay_power 1.0
# (registry canonical); return_mode MC; algorithm RecurrentPPO.
# NOTE: read seed/episodes from the TOP-LEVEL keys — the nested training: pair is a
# known stale duplicate that always reads 42/100 (see KNOWN_BUGS.md).
# provenance.json git_short = a71f4471 on ALL SIXTEEN (no split-SHA wave).
#
# LAUNCH DEFECT (caught pre-training, nothing wasted): the first attempt at runs 2-16
# staged the remote /tmp scripts with `ssh -n ... "cat > $TMP" < stage.sh`. The -n flag
# forces stdin to /dev/null, overriding the redirect, so all 15 scripts were written
# 0 bytes; `bash <empty>` exits 0 instantly -> 0-byte logs, no processes, no results
# dirs, no WandB runs, no GPU touched. Relaunched without -n plus a post-stage
# assertion that the staged file contains the expected --tag before run_command.py is
# called. Run 1 was staged before the -n was introduced and was never affected.
# Run  Tag                            Arm         Slice  Node:GPU  PID      WandB     Log
# 1    rppo_nmnsite_t1none_s42        t1none      -      106:0     349961   anpfno02  logs/20260907_045528_rppo_nmnsite_t1none_s42.log
# 2    rppo_nmnsite_t2enc_ALL_s42     t2enc       ALL    106:1     354805   pom30693  logs/20260907_050217_rppo_nmnsite_t2enc_ALL_s42.log
# 3    rppo_nmnsite_t2enc_I_s42       t2enc       I      107:0     267885   9f8wx4b9  logs/20260907_050218_rppo_nmnsite_t2enc_I_s42.log
# 4    rppo_nmnsite_t2enc_X_s42       t2enc       X      107:1     268045   kir9fubn  logs/20260907_050219_rppo_nmnsite_t2enc_X_s42.log
# 5    rppo_nmnsite_t3rnn_ALL_s42     t3rnn       ALL    108:0     259660   3ed43b2i  logs/20260907_050220_rppo_nmnsite_t3rnn_ALL_s42.log
# 6    rppo_nmnsite_t3rnn_I_s42       t3rnn       I      108:1     259817   84964jnn  logs/20260907_050221_rppo_nmnsite_t3rnn_I_s42.log
# 7    rppo_nmnsite_t3rnn_X_s42       t3rnn       X      109:0     243285   ryt9z2lo  logs/20260907_050222_rppo_nmnsite_t3rnn_X_s42.log
# 8    rppo_nmnsite_t4act_ALL_s42     t4act       ALL    109:1     243445   p6yc4akb  logs/20260907_050223_rppo_nmnsite_t4act_ALL_s42.log
# 9    rppo_nmnsite_t4act_I_s42       t4act       I      110:0     183809   qeesiize  logs/20260907_050224_rppo_nmnsite_t4act_I_s42.log
# 10   rppo_nmnsite_t4act_X_s42       t4act       X      110:1     183969   skmnxb2h  logs/20260907_050225_rppo_nmnsite_t4act_X_s42.log
# 11   rppo_nmnsite_t5crt_ALL_s42     t5crt       ALL    111:0     197715   qug0fubt  logs/20260907_050226_rppo_nmnsite_t5crt_ALL_s42.log
# 12   rppo_nmnsite_t5crt_I_s42       t5crt       I      111:1     197875   hi2ly2sh  logs/20260907_050226_rppo_nmnsite_t5crt_I_s42.log
# 13   rppo_nmnsite_t5crt_X_s42       t5crt       X      112:0     185723   f5qlrnql  logs/20260907_050227_rppo_nmnsite_t5crt_X_s42.log
# 14   rppo_nmnsite_t16quad_ALL_s42   t16quad     ALL    112:1     185883   b2cen70a  logs/20260907_050228_rppo_nmnsite_t16quad_ALL_s42.log
# 15   rppo_nmnsite_t16quad_I_s42     t16quad     I      113:0     290554   ldsttwlo  logs/20260907_050229_rppo_nmnsite_t16quad_I_s42.log
# 16   rppo_nmnsite_t16quad_X_s42     t16quad     X      113:1     290742   hxey8k3h  logs/20260907_050230_rppo_nmnsite_t16quad_X_s42.log
# ---------------------------------------------------------------------------

# ===========================================================================
# WAVE: NMN input x site grid -- GAE_NORM twin  (16 runs, launched 2026-09-07)
# ---------------------------------------------------------------------------
# The estimator-swapped twin of the MC grid recorded above: same 16 arms, same
# env, same seed, differing from their MC counterparts in exactly one agent-config
# key -- return_mode: GAE_NORM instead of MC.
#
# Config-owned and therefore NOT passed on the CLI: --seed (42), --num-envs (128),
# --checkpoint-frequency (200000 via configs/train/recurrent_ppo.yaml).
# --episodes IS passed explicitly (10,000,000) as the convention requires.
#
# Nodes 107/108/109/112 were deliberately left untouched (both GPUs) so the four
# still-training stragglers from the MC wave keep a clean node.
#
# Run 1 below is the active block; runs 2-16 differ from it ONLY in
# --agent_config, --device and the tag/wandb-name pair, and are recorded in the
# table that follows. Each run was staged to a unique /tmp/train_cmd_<epoch>_<rand>.sh
# on its target node (CIFS-bypass), asserted non-empty + carrying its own --tag,
# then launched with `run_command.py --no-tail`.
# ===========================================================================

# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
#   --episodes 10000000 --device cuda:0 --log-interval 10 \
#   --tag "rppo_nmngaenorm_t1none_s42" --wandb-name "rppo_nmngaenorm_t1none_s42" \
#   --wandb-group "nmn_input_site_grid_gaenorm" --wandb-job-type "pilot"

# Runs 2-16 (same command shape; only these three fields differ):
#  2  --agent_config .../nmngaenorm_t2enc_ALL.yaml    --device cuda:1  --tag/--wandb-name rppo_nmngaenorm_t2enc_ALL_s42
#  3  --agent_config .../nmngaenorm_t2enc_I.yaml      --device cuda:0  --tag/--wandb-name rppo_nmngaenorm_t2enc_I_s42
#  4  --agent_config .../nmngaenorm_t2enc_X.yaml      --device cuda:1  --tag/--wandb-name rppo_nmngaenorm_t2enc_X_s42
#  5  --agent_config .../nmngaenorm_t3rnn_ALL.yaml    --device cuda:0  --tag/--wandb-name rppo_nmngaenorm_t3rnn_ALL_s42
#  6  --agent_config .../nmngaenorm_t3rnn_I.yaml      --device cuda:1  --tag/--wandb-name rppo_nmngaenorm_t3rnn_I_s42
#  7  --agent_config .../nmngaenorm_t3rnn_X.yaml      --device cuda:0  --tag/--wandb-name rppo_nmngaenorm_t3rnn_X_s42
#  8  --agent_config .../nmngaenorm_t4act_ALL.yaml    --device cuda:1  --tag/--wandb-name rppo_nmngaenorm_t4act_ALL_s42
#  9  --agent_config .../nmngaenorm_t4act_I.yaml      --device cuda:0  --tag/--wandb-name rppo_nmngaenorm_t4act_I_s42
# 10  --agent_config .../nmngaenorm_t4act_X.yaml      --device cuda:1  --tag/--wandb-name rppo_nmngaenorm_t4act_X_s42
# 11  --agent_config .../nmngaenorm_t5crt_ALL.yaml    --device cuda:0  --tag/--wandb-name rppo_nmngaenorm_t5crt_ALL_s42
# 12  --agent_config .../nmngaenorm_t5crt_I.yaml      --device cuda:1  --tag/--wandb-name rppo_nmngaenorm_t5crt_I_s42
# 13  --agent_config .../nmngaenorm_t5crt_X.yaml      --device cuda:0  --tag/--wandb-name rppo_nmngaenorm_t5crt_X_s42
# 14  --agent_config .../nmngaenorm_t16quad_ALL.yaml  --device cuda:1  --tag/--wandb-name rppo_nmngaenorm_t16quad_ALL_s42
# 15  --agent_config .../nmngaenorm_t16quad_I.yaml    --device cuda:2  --tag/--wandb-name rppo_nmngaenorm_t16quad_I_s42
# 16  --agent_config .../nmngaenorm_t16quad_X.yaml    --device cuda:3  --tag/--wandb-name rppo_nmngaenorm_t16quad_X_s42
#
# LAUNCH RECORD -- all 16 verified TRAINING, exactly one PID per tag, 2026-09-07T16:05
# Verification beyond process-existence: every run's log grew between two samples
# 100 s apart (39-62 KB of new output each), and every assigned GPU is resident and
# busy (86-100% util, 4.5-6.8 GB). Nodes 107/108/109/112 untouched (MC-wave stragglers).
# Ground truth from each run's OWN saved models/config.yaml:
#   return_mode = GAE_NORM on ALL SIXTEEN (the point of this wave);
#   modulation.sites and modulation.input_sensors match the intended arm on all 16;
#   run 1 (t1none) has modulation.type = null;
#   TOP-LEVEL seed: 42 and episodes: 10000000 on all 16; num_envs 128.
# NOTE: read seed/episodes from the TOP-LEVEL keys -- the nested training: pair is a
# known stale duplicate that always reads 42/100 (see KNOWN_BUGS.md).
# provenance.json git_short = 6695aa29 on ALL SIXTEEN (no split-SHA wave).
# git_dirty = "unknown" on all 16 -- expected, not a defect: provenance shells out to
# git with a 10 s timeout and sixteen simultaneous launches lose that race on the NAS.
#
# Staging note: scripts were staged with `ssh ... "cat > $TMP" < stage.sh` WITHOUT the
# -n flag (which would force stdin to /dev/null and write 0 bytes), and each staged
# file was asserted non-empty AND carrying its own --tag before run_command.py ran.
# All 16 asserted STAGE_OK at 541-556 bytes.
# Run  Tag                              Arm      Slice  Node:GPU  PID      WandB     Log
# 1    rppo_nmngaenorm_t1none_s42       t1none   -      101:0     452172   xvw6uzrs  logs/20260907_155850_rppo_nmngaenorm_t1none_s42.log
# 2    rppo_nmngaenorm_t2enc_ALL_s42    t2enc    ALL    101:1     452294   dtai9q6q  logs/20260907_155852_rppo_nmngaenorm_t2enc_ALL_s42.log
# 3    rppo_nmngaenorm_t2enc_I_s42      t2enc    I      102:0     2916318  a0qrdefg  logs/20260907_155852_rppo_nmngaenorm_t2enc_I_s42.log
# 4    rppo_nmngaenorm_t2enc_X_s42      t2enc    X      102:1     2916436  9ovumjg0  logs/20260907_155853_rppo_nmngaenorm_t2enc_X_s42.log
# 5    rppo_nmngaenorm_t3rnn_ALL_s42    t3rnn    ALL    103:0     444457   k3nkwafh  logs/20260907_155854_rppo_nmngaenorm_t3rnn_ALL_s42.log
# 6    rppo_nmngaenorm_t3rnn_I_s42      t3rnn    I      103:1     444577   3om5z4jv  logs/20260907_155855_rppo_nmngaenorm_t3rnn_I_s42.log
# 7    rppo_nmngaenorm_t3rnn_X_s42      t3rnn    X      104:0     456738   igrblp5d  logs/20260907_155856_rppo_nmngaenorm_t3rnn_X_s42.log
# 8    rppo_nmngaenorm_t4act_ALL_s42    t4act    ALL    104:1     456860   bo6t6y4m  logs/20260907_155857_rppo_nmngaenorm_t4act_ALL_s42.log
# 9    rppo_nmngaenorm_t4act_I_s42      t4act    I      105:0     543334   3whh6e86  logs/20260907_155858_rppo_nmngaenorm_t4act_I_s42.log
# 10   rppo_nmngaenorm_t4act_X_s42      t4act    X      105:1     543456   3jqmnf3a  logs/20260907_155900_rppo_nmngaenorm_t4act_X_s42.log
# 11   rppo_nmngaenorm_t5crt_ALL_s42    t5crt    ALL    106:0     530591   rinfx023  logs/20260907_155900_rppo_nmngaenorm_t5crt_ALL_s42.log
# 12   rppo_nmngaenorm_t5crt_I_s42      t5crt    I      106:1     530713   e1ty78id  logs/20260907_155902_rppo_nmngaenorm_t5crt_I_s42.log
# 13   rppo_nmngaenorm_t5crt_X_s42      t5crt    X      114:0     270517   76krj6ri  logs/20260907_155902_rppo_nmngaenorm_t5crt_X_s42.log
# 14   rppo_nmngaenorm_t16quad_ALL_s42  t16quad  ALL    114:1     270737   u69q0auc  logs/20260907_155904_rppo_nmngaenorm_t16quad_ALL_s42.log
# 15   rppo_nmngaenorm_t16quad_I_s42    t16quad  I      114:2     270998   khcs2pxc  logs/20260907_155905_rppo_nmngaenorm_t16quad_I_s42.log
# 16   rppo_nmngaenorm_t16quad_X_s42    t16quad  X      114:3     271243   d4okzt4v  logs/20260907_155907_rppo_nmngaenorm_t16quad_X_s42.log
# ---------------------------------------------------------------------------

# ===========================================================================
# WAVE: nmn_site_grid_olf_mc — neuromodulator input x site grid on the
# OLFACTION-ONLY sensor-ladder arm (2026-09-09)
# ---------------------------------------------------------------------------
# What changed vs the two previous waves: the ENVIRONMENT. Both earlier waves
# (rppo_nmnsite_* MC, rppo_nmngaenorm_* GAE_NORM) ran on
# configs/environment/experiment/basic/04-jump_attack_10x10.yaml. This wave runs
# the same UNCHANGED 16-arm MC agent grid on
# configs/environment/experiment/archive/sensory_ladder/B_olf_only.yaml — the
# olfaction-only ladder arm, chosen because it previously produced the strongest
# bush-hiding and some state-dependent behaviour.
#
# OBSERVATION-DIMENSION DISCRIMINATOR (the single most valuable pre-flight check):
#   B_olf_only              -> 47  {Satiation 1, Interoceptive Nociception 1,
#                                   Extero Nociception 1, Olfaction 25,
#                                   Collision 5, Proprioception 6, Visual 8}
#   04-jump_attack_10x10    -> 27  (same seven sensors, Olfaction 5)
# The difference is sensory.olfactory_grid_range: 1 (B_olf_only) vs 0 (basic/04),
# which widens Olfaction from 1x5 to a 5-cell diamond x 5 = 25. If a run's banner
# prints 27, the WRONG environment loaded and the wave is void.
#
# Modulator input widths against obs_dim 47: ALL = 47, I = 2
# (Satiation + Interoceptive Nociception), X = 39 (Extero Nociception 1 +
# Olfaction 25 + Collision 5 + Visual 8). Verified pre-launch.
#
# REGISTRY DEVIATION (flagged, intentional): sensory.olfactory_grid_range is 1
# here against the canonical 0 in configs/environment/default.yaml
# (docs/environment/CONFIG_CRITICAL_SETTINGS.md). That IS the sensory_ladder
# B-arm's defining property, not drift. sensory.decay_power = 1.0 and
# thermal.enabled = false both match their canonical registry values.
#
# --seed / --num-envs / --checkpoint-frequency are NOT passed (config-owned).
# --episodes IS passed explicitly (10,000,000) as the convention requires.
#
# Nodes 109-114 deliberately untouched — reserved for a parallel session's
# thermal work and for the GAE_NORM wave that follows this one.
#
# Run 1 below is the active block; runs 2-16 differ from it ONLY in
# --agent_config, --device and the tag/wandb-name pair, and are recorded in the
# table that follows. Each run is staged to a unique /tmp/train_cmd_<epoch>_<rand>.sh
# on its target node (CIFS-bypass), asserted non-empty + carrying its own --tag,
# then launched with `run_command.py --no-tail`.
# ===========================================================================

/home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
  --config configs/environment/experiment/archive/sensory_ladder/B_olf_only.yaml \
  --agent_config configs/models/recurrent_ppo/nmn_input_site_grid/nmnsite_t1none.yaml \
  --episodes 10000000 --device cuda:0 --log-interval 10 \
  --tag "rppo_olfmc_t1none_s42" --wandb-name "rppo_olfmc_t1none_s42" \
  --wandb-group "nmn_site_grid_olf_mc" --wandb-job-type "pilot"

# Runs 2-16 (same command shape; only these three fields differ):
#  2  --agent_config .../nmnsite_t2enc_ALL.yaml    101:1  --tag/--wandb-name rppo_olfmc_t2enc_ALL_s42
#  3  --agent_config .../nmnsite_t2enc_I.yaml      102:0  --tag/--wandb-name rppo_olfmc_t2enc_I_s42
#  4  --agent_config .../nmnsite_t2enc_X.yaml      102:1  --tag/--wandb-name rppo_olfmc_t2enc_X_s42
#  5  --agent_config .../nmnsite_t3rnn_ALL.yaml    103:0  --tag/--wandb-name rppo_olfmc_t3rnn_ALL_s42
#  6  --agent_config .../nmnsite_t3rnn_I.yaml      103:1  --tag/--wandb-name rppo_olfmc_t3rnn_I_s42
#  7  --agent_config .../nmnsite_t3rnn_X.yaml      104:0  --tag/--wandb-name rppo_olfmc_t3rnn_X_s42
#  8  --agent_config .../nmnsite_t4act_ALL.yaml    104:1  --tag/--wandb-name rppo_olfmc_t4act_ALL_s42
#  9  --agent_config .../nmnsite_t4act_I.yaml      105:0  --tag/--wandb-name rppo_olfmc_t4act_I_s42
# 10  --agent_config .../nmnsite_t4act_X.yaml      105:1  --tag/--wandb-name rppo_olfmc_t4act_X_s42
# 11  --agent_config .../nmnsite_t5crt_ALL.yaml    106:0  --tag/--wandb-name rppo_olfmc_t5crt_ALL_s42
# 12  --agent_config .../nmnsite_t5crt_I.yaml      106:1  --tag/--wandb-name rppo_olfmc_t5crt_I_s42
# 13  --agent_config .../nmnsite_t5crt_X.yaml      107:0  --tag/--wandb-name rppo_olfmc_t5crt_X_s42
# 14  --agent_config .../nmnsite_t16quad_ALL.yaml  107:1  --tag/--wandb-name rppo_olfmc_t16quad_ALL_s42
# 15  --agent_config .../nmnsite_t16quad_I.yaml    108:0  --tag/--wandb-name rppo_olfmc_t16quad_I_s42
# 16  --agent_config .../nmnsite_t16quad_X.yaml    108:1  --tag/--wandb-name rppo_olfmc_t16quad_X_s42
#
# LAUNCH RECORD -- all 16 verified TRAINING, exactly one PID per tag, 2026-09-09T02:41
#
# ENVIRONMENT CONFIRMED (the check that mattered): all sixteen startup banners print
#   "Observation Dim: 47 (Satiation=1, Interoceptive Nociception=1, Extero Nociception=1,
#    Olfaction=25, Collision=5, Proprioception=6, Visual=8)"
# i.e. B_olf_only, NOT the 27-dim basic/04 of the two previous waves. Pre-computed the
# same breakdown locally through train.py's own load path (get_default_config +
# load_env_config + load_env_params + get_observation_breakdown) BEFORE launching, so a
# wrong-env wave would have been caught at zero cost; the banners then confirmed it.
#
# Ground truth from each run's OWN saved models/config.yaml (all 16):
#   sensory.olfactory_grid_range = 1  (B_olf_only's defining key; basic/04 is 0)
#   thermal.enabled = false           (thermal system off, as required)
#   agent.return_mode = MC            (this is the MC grid, not GAE_NORM)
#   modulation.sites + modulation.input_sensors match the intended arm on all 16
#   run 1 (t1none) has modulation.type = null
#   TOP-LEVEL seed: 42 and episodes: 10000000; num_envs 128
#   (read seed/episodes from the TOP-LEVEL keys -- the nested training: pair is a known
#    stale duplicate that always reads 42/100; see KNOWN_BUGS.md)
# provenance.json git_short = 880f1077 on ALL SIXTEEN (no split-SHA wave).
# git_dirty is MIXED this time -- some runs wrote true, others "unknown". Both are the
# same 10 s git-timeout race against the NAS under 16 simultaneous launches; "true" is
# correct (the tree carried uncommitted sensory_directional + docs edits at launch).
#
# Health at T+5min: every log GROWING between two samples (+6.8-11.7 KB), every assigned
# GPU resident and busy (73-100% util, 4.5-6.6 GB), all 16 advancing at 489-711 it/s
# (Iter 353-562). No OOM / traceback in any log. Exactly 16 results dirs, one per tag.
#
# NODE 102 FOREIGN TENANT (reported, not acted on): pre-flight showed 102 completely idle
# (2 MiB, no compute apps), but a third-party job appeared AFTER launch holding 18570 MiB
# on GPU 0 and 386 MiB on GPU 1. Our two runs there are unaffected and are in fact the
# fastest in the wave (4090s, Iter 560/562), but GPU 0 is now at 23986/24564 MiB -- only
# ~580 MiB headroom. NOTE: nvidia-smi on these nodes reports PIDs in a DIFFERENT namespace
# than ssh `ps`, so "unknown" nvidia-smi PIDs are normally our own runs; 102 is the one
# node where a genuine THIRD pid exists.
#
# Staging note: scripts were staged with `ssh ... "cat > $TMP" < local.sh` WITHOUT the -n
# flag (which would force stdin to /dev/null and write 0 bytes), and each staged file was
# asserted >100 bytes AND carrying its own --tag AND the B_olf_only path before
# run_command.py ran. All 16 asserted STAGE_OK at 494-509 bytes. The launch loop read the
# matrix into an ARRAY (never `while read`, which would drain its own stdin and let
# run_command.py's ssh eat the rest of the matrix) and passed </dev/null to each inner
# call. No local `timeout` wrapped run_command.py.
#
# Run  Tag                          Arm      Slice  Node:GPU  PID      WandB     Log
# 1    rppo_olfmc_t1none_s42        t1none   -      101:0     631777   683qk0uj  logs/20260909_023635.log
# 2    rppo_olfmc_t2enc_ALL_s42     t2enc    ALL    101:1     631817   uj1w5uu7  logs/20260909_023636.log
# 3    rppo_olfmc_t2enc_I_s42       t2enc    I      102:0     3915681  4019the7  logs/20260909_023637.log
# 4    rppo_olfmc_t2enc_X_s42       t2enc    X      102:1     3915711  2mi860zc  logs/20260909_023639.log
# 5    rppo_olfmc_t3rnn_ALL_s42     t3rnn    ALL    103:0     618423   br8tl82k  logs/20260909_023640.log
# 6    rppo_olfmc_t3rnn_I_s42       t3rnn    I      103:1     618461   5olp3iva  logs/20260909_023641.log
# 7    rppo_olfmc_t3rnn_X_s42       t3rnn    X      104:0     636340   gbr992lc  logs/20260909_023642.log
# 8    rppo_olfmc_t4act_ALL_s42     t4act    ALL    104:1     636380   xerdg69k  logs/20260909_023644.log
# 9    rppo_olfmc_t4act_I_s42       t4act    I      105:0     722948   7ell8l1x  logs/20260909_023645.log
# 10   rppo_olfmc_t4act_X_s42       t4act    X      105:1     722988   b3l8bzz0  logs/20260909_023646.log
# 11   rppo_olfmc_t5crt_ALL_s42     t5crt    ALL    106:0     711026   89mjw56e  logs/20260909_023648.log
# 12   rppo_olfmc_t5crt_I_s42       t5crt    I      106:1     711066   fsmuo106  logs/20260909_023649.log
# 13   rppo_olfmc_t5crt_X_s42       t5crt    X      107:0     450985   i7ymftsy  logs/20260909_023650.log
# 14   rppo_olfmc_t16quad_ALL_s42   t16quad  ALL    107:1     451025   lomvrpyc  logs/20260909_023652.log
# 15   rppo_olfmc_t16quad_I_s42     t16quad  I      108:0     445218   supdbzxk  logs/20260909_023653.log
# 16   rppo_olfmc_t16quad_X_s42     t16quad  X      108:1     445258   xume2sw4  logs/20260909_023654.log
# ---------------------------------------------------------------------------

# ===========================================================================
# WAVE: nmn_site_grid_olf_gaenorm — the ESTIMATOR-SWAPPED TWIN of the
# nmn_site_grid_olf_mc wave launched earlier today at 02:41 (2026-09-09)
# ---------------------------------------------------------------------------
# Same environment, same 16-arm neuromodulator input x site grid, same budget.
# The ONLY thing that changes is how the advantage/return target is estimated:
#   MC wave        -> configs/models/recurrent_ppo/nmn_input_site_grid/nmnsite_<cell>.yaml
#                     (return_mode: MC)
#   THIS wave      -> configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_<cell>.yaml
#                     (return_mode: GAE_NORM)
# All 16 config pairs were diffed comment-stripped before launch: each pair
# differs on exactly ONE line, `return_mode: MC` -> `return_mode: GAE_NORM`,
# and on nothing else. No config was created or edited for this wave.
#
# Tags/wandb-names use `olfgae` where the MC wave used `olfmc`, and
# --wandb-group is "nmn_site_grid_olf_gaenorm" (MC wave: "nmn_site_grid_olf_mc").
# --wandb-job-type stays "pilot".
#
# OBSERVATION-DIMENSION DISCRIMINATOR (the check that decides wave validity —
# identical reasoning to the MC block above, and it applies unchanged):
#   B_olf_only              -> 47  {Satiation 1, Interoceptive Nociception 1,
#                                   Extero Nociception 1, Olfaction 25,
#                                   Collision 5, Proprioception 6, Visual 8}
#   04-jump_attack_10x10    -> 27  (same seven sensors, Olfaction 5)
# The difference is sensory.olfactory_grid_range: 1 (B_olf_only) vs 0, which
# widens Olfaction from 1x5 to a 5-cell diamond x 5 = 25. A banner printing 27
# means the WRONG environment loaded and that run is void.
# Pre-computed locally through train.py's OWN load path before launching
# (get_default_config + load_env_config + load_env_params +
# get_observation_breakdown) -> exactly 47 with Olfaction=25, so a wrong-env
# wave would have been caught at zero GPU cost.
#
# Modulator input widths against obs_dim 47, re-verified on the GAE_NORM
# configs (not inherited from the MC audit):
#   ALL = 47 (input_sensors: "all")
#   I   = 2  ["Satiation", "Interoceptive Nociception"]
#   X   = 39 ["Extero Nociception" 1, "Olfaction" 25, "Collision" 5, "Visual" 8]
# Proprioception (6) is deliberately in neither slice; 2 + 39 + 6 = 47.
# All 16 modulation.sites blocks match their intended arm; t1none has
# modulation.type = null.
#
# REGISTRY DEVIATION (flagged, intentional, same as the MC wave):
# sensory.olfactory_grid_range is 1 here against the canonical 0 in
# configs/environment/default.yaml (docs/environment/CONFIG_CRITICAL_SETTINGS.md).
# That IS the sensory_ladder B-arm's defining property, not drift.
# sensory.decay_power = 1.0 and thermal.enabled = false both match canonical.
#
# --seed / --num-envs / --checkpoint-frequency are NOT passed (config-owned).
# --episodes IS passed explicitly (10,000,000) as the convention requires.
#
# NODE SELECTION (supplied by the caller, verified not re-picked): 102, 106,
# 107:0, 109, 111, 112, 113, 114:0-2. Nodes 101/103/104/105/107:1/108 still
# carry the 11 unfinished MC runs and were excluded; 110 excluded entirely for
# foreign PIDs on 110:0. Pre-flight confirmed NAS mounted on all 8 target
# nodes, all 16 target GPUs idle (<=133 MiB, 0% util), and a REAL JAX GPU
# compile (4x4 matmul + block_until_ready) on every node at jax 0.9.0.1 /
# flax 0.12.4. The foreign tenant seen on 102 during the MC wave is GONE
# (102:0 and 102:1 both at 2 MiB at this pre-flight).
#
# Run 1 below is the active block; runs 2-16 differ from it ONLY in
# --agent_config, --device and the tag/wandb-name pair, and are recorded in the
# table that follows. Each run is staged to a unique /tmp/train_cmd_<epoch>_<rand>.sh
# on its target node (CIFS-bypass), asserted non-empty + carrying its own --tag,
# then launched with `run_command.py --no-tail`.
# ===========================================================================

/home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
  --config configs/environment/experiment/archive/sensory_ladder/B_olf_only.yaml \
  --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
  --episodes 10000000 --device cuda:0 --log-interval 10 \
  --tag "rppo_olfgae_t1none_s42" --wandb-name "rppo_olfgae_t1none_s42" \
  --wandb-group "nmn_site_grid_olf_gaenorm" --wandb-job-type "pilot"

# Runs 2-16 (same command shape; only these three fields differ):
#  2  --agent_config .../nmngaenorm_t2enc_ALL.yaml    109:1  --tag/--wandb-name rppo_olfgae_t2enc_ALL_s42
#  3  --agent_config .../nmngaenorm_t2enc_I.yaml      111:0  --tag/--wandb-name rppo_olfgae_t2enc_I_s42
#  4  --agent_config .../nmngaenorm_t2enc_X.yaml      111:1  --tag/--wandb-name rppo_olfgae_t2enc_X_s42
#  5  --agent_config .../nmngaenorm_t3rnn_ALL.yaml    112:0  --tag/--wandb-name rppo_olfgae_t3rnn_ALL_s42
#  6  --agent_config .../nmngaenorm_t3rnn_I.yaml      112:1  --tag/--wandb-name rppo_olfgae_t3rnn_I_s42
#  7  --agent_config .../nmngaenorm_t3rnn_X.yaml      106:0  --tag/--wandb-name rppo_olfgae_t3rnn_X_s42
#  8  --agent_config .../nmngaenorm_t4act_ALL.yaml    106:1  --tag/--wandb-name rppo_olfgae_t4act_ALL_s42
#  9  --agent_config .../nmngaenorm_t4act_I.yaml      107:0  --tag/--wandb-name rppo_olfgae_t4act_I_s42
# 10  --agent_config .../nmngaenorm_t4act_X.yaml      102:0  --tag/--wandb-name rppo_olfgae_t4act_X_s42
# 11  --agent_config .../nmngaenorm_t5crt_ALL.yaml    102:1  --tag/--wandb-name rppo_olfgae_t5crt_ALL_s42
# 12  --agent_config .../nmngaenorm_t5crt_I.yaml      113:0  --tag/--wandb-name rppo_olfgae_t5crt_I_s42
# 13  --agent_config .../nmngaenorm_t5crt_X.yaml      113:1  --tag/--wandb-name rppo_olfgae_t5crt_X_s42
# 14  --agent_config .../nmngaenorm_t16quad_ALL.yaml  114:0  --tag/--wandb-name rppo_olfgae_t16quad_ALL_s42
# 15  --agent_config .../nmngaenorm_t16quad_I.yaml    114:1  --tag/--wandb-name rppo_olfgae_t16quad_I_s42
# 16  --agent_config .../nmngaenorm_t16quad_X.yaml    114:2  --tag/--wandb-name rppo_olfgae_t16quad_X_s42
#
# LAUNCH RECORD -- all 16 verified TRAINING, exactly one PID per tag, 2026-09-09T16:11
#
# ENVIRONMENT CONFIRMED (the check that mattered): all sixteen startup banners print
#   "Observation Dim: 47 (Satiation=1, Interoceptive Nociception=1, Extero Nociception=1,
#    Olfaction=25, Collision=5, Proprioception=6, Visual=8)"
# i.e. B_olf_only, NOT the 27-dim basic/04. Read from each run's OWN
# wandb/run-*/files/output.log (see the LOG COLLISION note below -- the shared NAS
# run_command logs were NOT usable for this). Pre-computed the same breakdown locally
# through train.py's own load path BEFORE launching, so a wrong-env wave would have been
# caught at zero cost; the banners then confirmed it on all 16.
#
# Ground truth from each run's OWN saved models/config.yaml (all 16):
#   sensory.olfactory_grid_range = 1  (B_olf_only's defining key; basic/04 is 0)
#   thermal.enabled = false
#   agent.return_mode = GAE_NORM      (this is the GAE_NORM grid, not MC -- the one
#                                      field that separates this wave from rppo_olfmc_*)
#   modulation.sites + modulation.input_sensors match the intended arm on all 16
#   run 1 (t1none) has modulation.type = null
#   Modulator input widths recomputed from each saved config against its own obs
#   breakdown: ALL = 47 (x6... n/a for t1none), I = 2, X = 39 on every arm, as designed.
#   TOP-LEVEL seed: 42 and episodes: 10000000; num_envs 128
#   (read seed/episodes from the TOP-LEVEL keys -- the nested training: pair is a known
#    stale duplicate that always reads 42/100; see KNOWN_BUGS.md)
# provenance.json git_short = 53b2611e on ALL SIXTEEN (no split-SHA wave).
# git_dirty is MIXED (14x "unknown", 2x true) -- the same 10 s git-timeout race against
# the NAS under 16 simultaneous launches seen in the MC wave; "true" is correct (the tree
# carried uncommitted sensory_directional + docs edits at launch).
#
# LOG COLLISION (deviation from the MC wave -- READ THIS BEFORE READING THE LOGS):
# run_command.py names its NAS log logs/YYYYMMDD_HHMMSS.log at SECOND resolution. These
# 16 launches completed inside ~4 s, so the 16 runs collapsed onto only FIVE log files
# (161133-161137), 2-4 writers each, appending concurrently to the same NAS file. The
# result is byte-interleaved and corrupt at line granularity -- e.g. a literal
# "rppo_olfgae_t3wandb" where two writers' bytes landed in one line, and only ONE
# surviving "Observation Dim" line per file instead of 2-4. Those five files are NOT a
# per-run record and must not be parsed per run. The MC wave at 02:41 did not hit this
# only because its launches happened to straddle second boundaries.
# The authoritative per-run stdout is wandb/run-20260909_1611*-<id>/files/output.log
# (one file per run, unshared) -- that is what the banner + health checks above used.
#
# Health at T+3min: every assigned GPU resident and busy (5.5-6.8 GB, 54-100% util),
# all 16 advancing (Iteration 425-847), no traceback / OOM / RESOURCE_EXHAUSTED in any
# per-run log. Exactly 16 results dirs, one per tag. wandb metadata `host` field
# independently confirms every run landed on its intended node.
#
# NODE 102 FOREIGN TENANT: GONE. The third-party job that held 18570 MiB on 102:0 during
# the MC wave was absent at this pre-flight (102:0 and 102:1 both at 2 MiB) and has not
# returned. NOTE: this container runs on the 102 host, so `ps` on 102 also shows the
# launcher's own shells -- a naive pgrep on 102 over-counts. The verification below
# counted only processes whose argv[0] is the env interpreter and argv[1] is train.py.
#
# Run  Tag                            Arm      Slice  Node:GPU  PID      WandB     Per-run log
# 1    rppo_olfgae_t1none_s42         t1none   -      109:0     433931   fixefbop  wandb/run-20260909_161148-fixefbop/files/output.log
# 2    rppo_olfgae_t2enc_ALL_s42      t2enc    ALL    109:1     433936   svust7zw  wandb/run-20260909_161148-svust7zw/files/output.log
# 3    rppo_olfgae_t2enc_I_s42        t2enc    I      111:0     385343   bkqeyxs6  wandb/run-20260909_161148-bkqeyxs6/files/output.log
# 4    rppo_olfgae_t2enc_X_s42        t2enc    X      111:1     385348   15i9vlrk  wandb/run-20260909_161148-15i9vlrk/files/output.log
# 5    rppo_olfgae_t3rnn_ALL_s42      t3rnn    ALL    112:0     371906   re0xu8wg  wandb/run-20260909_161149-re0xu8wg/files/output.log
# 6    rppo_olfgae_t3rnn_I_s42        t3rnn    I      112:1     371946   1fjn7kro  wandb/run-20260909_161149-1fjn7kro/files/output.log
# 7    rppo_olfgae_t3rnn_X_s42        t3rnn    X      106:0     888815   8zl38wbn  wandb/run-20260909_161149-8zl38wbn/files/output.log
# 8    rppo_olfgae_t4act_ALL_s42      t4act    ALL    106:1     888855   ldr2gtfe  wandb/run-20260909_161149-ldr2gtfe/files/output.log
# 9    rppo_olfgae_t4act_I_s42        t4act    I      107:0     620470   74ynx017  wandb/run-20260909_161149-74ynx017/files/output.log
# 10   rppo_olfgae_t4act_X_s42        t4act    X      102:0     335161   3wyfh97p  wandb/run-20260909_161143-3wyfh97p/files/output.log
# 11   rppo_olfgae_t5crt_ALL_s42      t5crt    ALL    102:1     335169   1cw3oibv  wandb/run-20260909_161143-1cw3oibv/files/output.log
# 12   rppo_olfgae_t5crt_I_s42        t5crt    I      113:0     553737   5z28xpjw  wandb/run-20260909_161149-5z28xpjw/files/output.log
# 13   rppo_olfgae_t5crt_X_s42        t5crt    X      113:1     553805   045humwu  wandb/run-20260909_161149-045humwu/files/output.log
# 14   rppo_olfgae_t16quad_ALL_s42    t16quad  ALL    114:0     782689   339g62q7  wandb/run-20260909_161150-339g62q7/files/output.log
# 15   rppo_olfgae_t16quad_I_s42      t16quad  I      114:1     782757   udjh94rw  wandb/run-20260909_161150-udjh94rw/files/output.log
# 16   rppo_olfgae_t16quad_X_s42      t16quad  X      114:2     782825   f2wxnymu  wandb/run-20260909_161150-f2wxnymu/files/output.log
# ---------------------------------------------------------------------------

# ===========================================================================
# RELAUNCH: two nmn_site_grid_olf_gaenorm cells that DIED mid-training
# 2026-09-14 — cells 10 (t4act_X) and 11 (t5crt_ALL) of the GAE_NORM wave above
# ---------------------------------------------------------------------------
# Both originally launched 2026-09-09T16:11 onto node 102 (102:0 and 102:1,
# runs 10 and 11 in the table above) and died mid-training. Node 102 carries a
# foreign tenant and is EXCLUDED for this relaunch. Caller supplied node 113
# (two RTX 4090s) — not re-picked here.
#
# Settings are COPIED from the GAE_NORM wave block above, not reconstructed.
# Only --device changes relative to the original launch of these two cells
# (102:0/102:1 -> 113:0/113:1). Config paths, --episodes, tags, wandb-name,
# wandb-group and wandb-job-type are byte-identical to the original.
#
# Tags are reused EXACTLY (rppo_olfgae_t4act_X_s42 / rppo_olfgae_t5crt_ALL_s42)
# so the reruns stay joinable to the rest of the 16-cell grid. This creates a
# SECOND WandB run per tag; the dead 2026-09-09 runs (WandB 3wyfh97p and
# 1cw3oibv) are the ones being superseded.
#
# The two dead result dirs are LEFT UNTOUCHED by this relaunch (they hold
# partial checkpoints + a dangling orbax-checkpoint-tmp; the user moves them
# aside separately). Their actual names are timestamped 161139, NOT 161137/
# 161138:
#   results/JAX_RecurrentPPO/20260909-161139_rppo_olfgae_t4act_X_s42
#   results/JAX_RecurrentPPO/20260909-161139_rppo_olfgae_t5crt_ALL_s42
# No --load-checkpoint is passed: these are clean restarts from scratch, which
# is what keeps them comparable with the 14 sibling cells that ran uninterrupted.
#
# PRE-FLIGHT (2026-09-14, node 113):
#   - 113:0 and 113:1 both 3 MiB / 0% util, no train.py processes on the node.
#     NOTE: runs 12 and 13 of the wave above (t5crt_I / t5crt_X) were assigned
#     113:0/113:1 and are no longer present either — node 113 is fully idle.
#   - NAS mounted (//192.168.0.250/cocoanlab01 on /media/nas01).
#   - REAL JAX GPU compile (4x4 matmul + block_until_ready) OK:
#     jax 0.9.0.1 / flax 0.12.4 / optax 0.2.6, devices [CudaDevice(0), CudaDevice(1)]
#     — version-matched to the rest of the cluster and to the original wave.
#   - return_mode: GAE_NORM confirmed present in BOTH agent configs (line 54).
#   - Modulator slices confirmed: t4act_X input_sensors
#     ["Extero Nociception","Olfaction","Collision","Visual"] (39 of 47);
#     t5crt_ALL input_sensors "all" (47 of 47).
#   - No live process carried either tag on 102 or 113 before launch, so the
#     relaunch cannot duplicate a survivor.
#
# REGISTRY DEVIATION (flagged, intentional, unchanged from the original wave):
# sensory.olfactory_grid_range = 1 against the canonical 0 in
# configs/environment/default.yaml. That IS the sensory_ladder B-arm's defining
# property. sensory.decay_power = 1.0 and thermal.enabled = false both match
# the canonical values in docs/environment/CONFIG_CRITICAL_SETTINGS.md.
#
# --seed / --num-envs / --checkpoint-frequency are NOT passed (config-owned:
# seed 42, num_envs 128, checkpoint_frequency 200000 from the rPPO train config).
# --episodes IS passed explicitly (10,000,000) as the convention requires.
#
# Each run is staged to a unique /tmp/train_cmd_<epoch>_<rand>.sh on node 113
# (CIFS-bypass) and launched with `run_command.py --no-tail`.
# ===========================================================================

# Relaunch A — cell 10, t4act_X, node 113 GPU 0
/home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
  --config configs/environment/experiment/archive/sensory_ladder/B_olf_only.yaml \
  --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t4act_X.yaml \
  --episodes 10000000 --device cuda:0 --log-interval 10 \
  --tag "rppo_olfgae_t4act_X_s42" --wandb-name "rppo_olfgae_t4act_X_s42" \
  --wandb-group "nmn_site_grid_olf_gaenorm" --wandb-job-type "pilot"

# Relaunch B — cell 11, t5crt_ALL, node 113 GPU 1
/home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
  --config configs/environment/experiment/archive/sensory_ladder/B_olf_only.yaml \
  --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t5crt_ALL.yaml \
  --episodes 10000000 --device cuda:1 --log-interval 10 \
  --tag "rppo_olfgae_t5crt_ALL_s42" --wandb-name "rppo_olfgae_t5crt_ALL_s42" \
  --wandb-group "nmn_site_grid_olf_gaenorm" --wandb-job-type "pilot"

# LAUNCH RECORD -- both verified TRAINING, exactly one PID per tag, 2026-09-14T12:55
#
# Run  Tag                        Arm      Slice  Node:GPU  PID     WandB     Per-run log
# 10r  rppo_olfgae_t4act_X_s42    t4act    X      113:0     811011  xbn9b2yg  wandb/run-20260914_125045-xbn9b2yg/files/output.log
# 11r  rppo_olfgae_t5crt_ALL_s42  t5crt    ALL    113:1     811177  xqc146jl  wandb/run-20260914_125048-xqc146jl/files/output.log
#
# Launches were STAGGERED (12:50:31 / 12:50:35) so run_command.py's
# second-resolution NAS log names did not collide -- logs/20260914_125031.log and
# logs/20260914_125035.log are one-writer-each and ARE parsable per run, unlike the
# five interleaved files of the original 16-way wave.
#
# ENVIRONMENT CONFIRMED: both startup banners print
#   "Observation Dim: 47 (Satiation=1, Interoceptive Nociception=1, Extero Nociception=1,
#    Olfaction=25, Collision=5, Proprioception=6, Visual=8)"
# i.e. B_olf_only, NOT the 27-dim basic/04. wandb metadata `host` = docker-113 on both,
# independently confirming they landed on the intended node.
#
# Ground truth from each run's OWN saved models/config.yaml:
#   agent.return_mode = GAE_NORM on both (the field separating this grid from rppo_olfmc_*)
#   t4act_X   : modulation.type FiLM, sites {actor: true, others false},
#               input_sensors ["Extero Nociception","Olfaction","Collision","Visual"] (39 of 47)
#   t5crt_ALL : modulation.type FiLM, sites {critic: true, others false},
#               input_sensors "all" (47 of 47)
#   TOP-LEVEL seed: 42, episodes: 10000000, num_envs 128, checkpoint_frequency 200000
#   (read seed/episodes from the TOP-LEVEL keys -- the nested training: pair is a known
#    stale duplicate that always reads 42/100; see KNOWN_BUGS.md)
#   sensory.olfactory_grid_range = 1, decay_power = 1.0, thermal.enabled = false
#
# Health at T+5min: both GPUs resident and busy (5667 MiB, 92% and 100% util), both
# processes in R state with CPU time accruing, ~811 it/s (t4act_X) and ~973 it/s
# (t5crt_ALL), no traceback / OOM / RESOURCE_EXHAUSTED in either per-run log.
#
# CHECKPOINTING CONFIRMED (the specific thing the dead runs failed at): the first
# 200k-episode checkpoint completed cleanly on BOTH runs --
#   models/200170 (t4act_X) and models/200039 (t5crt_ALL), 5.4M each,
#   and `find -name '*orbax-checkpoint-tmp*'` returns ZERO on both, i.e. no dangling
#   partial write of the kind left behind in the dead 2026-09-09 dirs.
#
# The two dead run dirs were NOT touched by this relaunch:
#   results/JAX_RecurrentPPO/20260909-161139_rppo_olfgae_t4act_X_s42
#   results/JAX_RecurrentPPO/20260909-161139_rppo_olfgae_t5crt_ALL_s42
# (both still carry their partial checkpoints through 1000047 plus the dangling
#  1200001.orbax-checkpoint-tmp; the user moves them aside separately.)
#
# SIDE OBSERVATION, NOT ACTED ON: runs 12 and 13 of the wave above (t5crt_I on 113:0,
# t5crt_X on 113:1) were also absent at this pre-flight -- node 113 was fully idle
# before these two launches. Those two cells are therefore ALSO dead and are not
# covered by this relaunch. Surfaced to the user rather than relaunched unasked.
# ---------------------------------------------------------------------------

# ===========================================================================
# RENDER CHECK: does WandB receive the checkpoint video from the V2 dashboard
# renderer? -- 2026-09-18, node 113 GPU 0
# ---------------------------------------------------------------------------
# NOT a science run. This is an INSTRUMENT CHECK of commit 891d2057 ("the
# dashboard renderer becomes the default for evaluation videos"), which
# repointed the three src/ eval call sites from scripts/eval/render_recordings.py
# to scripts/eval/render_recordings_v2.py. The run is launched only far enough
# to produce its FIRST checkpoint video, verified, and then killed -- it is not
# meant to reach its 10M-episode budget.
#
# WHAT THE CHECK LOOKS FOR (all three, or the switchover did not take effect):
#   1. recordings/<ckpt>/episode_*.rec.gz written at the checkpoint;
#   2. videos_v2/eval_<ckpt>.mp4 exists and is non-trivial. V1 wrote to
#      videos/ and V2 is deliberately NOT taught to write there, so a videos/
#      directory appearing instead is the failure signature;
#   3. videos_v2/render_<ckpt>.log contains "frames verified" -- a phrase that
#      exists ONLY in render_recordings_v2.py (lines 444 / 489), so it is direct
#      evidence of WHICH renderer ran, not an inference from the output path.
# The WandB side is the actual deliverable: async_render.poll_render() hands the
# finished MP4 to wandb_utils, which logs it under the key "eval/video".
#
# PROVENANCE: settings are COPIED from the 2026-09-14 relaunch block directly
# above (cell 10, t4act_X), NOT reconstructed -- with exactly TWO deliberate,
# user-approved substitutions:
#
#   (a) --config swapped. The original pointed at
#       configs/environment/experiment/archive/sensory_ladder/B_olf_only.yaml,
#       which NO LONGER LOADS: it raises
#         ValueError: Strict Config: Configuration key
#         'body.recovery_in_bush_multiplier' is required but missing
#       (the sixth mandatory key, added 2026-09-15). Archived configs are
#       deliberately NOT migrated per the settings-tree policy, so the user chose
#       the maintained ladder world configs/environment/experiment/basic/
#       04-jump_attack_10x10.yaml instead. NOTE this changes the observation
#       width 47 -> 27; the agent config's own generated header already describes
#       its slice as "19 of the 27 observation numbers", i.e. 27 dims is the
#       width that file was generated against.
#   (b) --tag / --wandb-name changed to rppo_rendercheck_t4act_X_s42 and
#       --wandb-job-type to "render_check", so this instrument run can never be
#       confused with the science pilot rppo_olfgae_t4act_X_s42 in WandB or in
#       results/JAX_RecurrentPPO/. --wandb-group is kept as given.
#
# Everything else is byte-identical to the 2026-09-14 launch.
#
# PRE-FLIGHT (2026-09-18, node 113 -- node:GPU supplied by the caller, not picked here):
#   - Caller verified: gpu_status.py both 113 GPUs FREE (3 MiB, 0% util); no diary
#     claim on 113 today or yesterday; no training processes on the node.
#   - Independently re-confirmed here: 113:0 and 113:1 both 3 MiB / 0% util,
#     `pgrep -af train.py` empty, NAS mounted (//192.168.0.250/cocoanlab01, 28T free).
#   - REAL JAX GPU compile (4x4 matmul + block_until_ready) OK: jax 0.9.0.1 with
#     flax / optax / orbax / chex all importable -- version-matched to the cluster.
#
# REGISTRY CHECK vs docs/environment/CONFIG_CRITICAL_SETTINGS.md: basic/04 inherits
# default.yaml, so sensory.decay_power = 1.0, sensory.olfactory_grid_range = 0 and
# thermal.enabled = false all sit at their CANONICAL values. Unlike the archived
# B_olf_only arm this run carries NO registry deviation.
#
# WandB IS ON (no --no-wandb). That is the entire point of the run.
#
# CHECKPOINT CADENCE -- CORRECTING THE BRIEF: checkpoint_frequency for RecurrentPPO is
# 200000 episodes (configs/train/recurrent_ppo.yaml, merged above configs/train/
# default.yaml, whose 10000 is only the DQN/DRQN/PPO fallback). So the first
# checkpoint lands at ~200k episodes, NOT the ~10k / "nine or ten iterations" the
# brief assumed. No --checkpoint-frequency is passed: it stays config-owned, which
# keeps the render path under test identical to a real run's.
# --seed / --num-envs are likewise NOT passed (config-owned: seed 42, num_envs 128).
# --episodes IS passed explicitly (10,000,000) as the convention requires, even
# though the run is killed long before it.
#
# Staged to a unique /tmp/train_cmd_<epoch>_<rand>.sh on node 113 (CIFS-bypass) and
# launched with `run_command.py --no-tail`.
# ===========================================================================
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t4act_X.yaml \
#   --episodes 10000000 --device cuda:0 --log-interval 10 \
#   --tag "rppo_rendercheck_t4act_X_s42" --wandb-name "rppo_rendercheck_t4act_X_s42" \
#   --wandb-group "nmn_site_grid_olf_gaenorm" --wandb-job-type "render_check"

# LAUNCH RECORD -- VERDICT: THE V2 SWITCHOVER WORKS END-TO-END. 2026-09-18
#
# Launched 11:34:54 via run_command.py --no-tail, node 113 GPU 0, PID 1067380 (exactly
# one PID for the tag; the raw `pgrep -f | wc -l` reported 2, which was the SSH remote
# shell matching its OWN pattern string -- resolved with `ps | grep "[t]rain\.py"`, which
# cannot self-match. NOT a duplicate launch).
#   NAS log : logs/20260918_113454.log
#   Results : results/JAX_RecurrentPPO/20260918-113456_rppo_rendercheck_t4act_X_s42
#   WandB   : 1tnkacym -- https://wandb.ai/sungwoolee/grid_world_pain/runs/1tnkacym
#
# ENVIRONMENT CONFIRMED from the startup banner: "Observation Dim: 27 (Satiation=1,
# Interoceptive Nociception=1, Extero Nociception=1, Olfaction=5, Collision=5,
# Proprioception=6, Visual=8)" -- i.e. basic/04, the substituted world, NOT the
# 47-dim archived B_olf_only. Neuromodulation ENABLED (FiLM, sites=[actor],
# input_sensors=[Extero Nociception,Olfaction,Collision,Visual]), Return Mode GAE_NORM.
#
# TIME TO FIRST CHECKPOINT: ~3m38s. Checkpoint fired at episode 200176 (as predicted by
# the rPPO config-owned checkpoint_frequency of 200000, NOT the 10000 fallback) --
# recordings/ appeared 11:38:34, videos_v2/ 11:38:49, consolidated MP4 complete 11:38:54
# (~3m58s after start). Throughput ~995 it/s at the checkpoint.
#
# ALL THREE ON-DISK CHECKS PASS:
#   1. recordings/200176/episode_00000{1,2,3}.rec.gz written (1093 / 1473 / 1063 B)
#      + run_meta.pkl.
#   2. videos_v2/eval_200176.mp4 = 182,663 B, ISO Media MP4, 1440x896, 34 frames, 6.8s.
#      NO videos/ directory was ever created -- the run dir holds exactly
#      models/ recordings/ videos_v2/. This is the V1-vs-V2 discriminator.
#   3. videos_v2/render_200176.log carries the V2-only phrase, verbatim:
#        "  34 frames verified (expected 34)"
#      and per episode e.g. "  ep    2: 17 steps, 17 frames verified, 3.4s".
#
# WANDB RECEIVED THE VIDEO -- the actual deliverable, confirmed against the CLOUD via
# the public API, not just the local staging dir:
#   run summary key `eval/video` ->
#     {'path': 'media/videos/eval/video_60_49bafff9c33f176aa01d.mp4', 'size': 182663,
#      '_type': 'video-file', 'caption': 'Episode 200176'}
#   and md5 of that staged file == md5 of videos_v2/eval_200176.mp4
#   (a06eb578268eaed87295eedfe4214e0c) -- byte-identical, so the artifact WandB holds
#   is this render and not a stale or re-encoded file.
#
# NON-DEFECT, recorded so it is not re-diagnosed later: render_200176.log opens with a
# JAX traceback "cuInit(0) failed: CUDA_ERROR_NO_DEVICE". That is EXPECTED and harmless
# -- async_render deliberately runs the renderer CPU-only (it must not contend with the
# training process for the GPU). The render still exited 0 and verified every frame.
#
# STOPPED ON PURPOSE at 11:41 by user instruction, once the video was confirmed, rather
# than hold a 4090 for a 10M-episode budget: terminate_command.py 113 <tag> --yes
# (SIGINT, graceful). Verified afterwards: 0 PIDs for the tag, both 113 GPUs back to
# 3 MiB / 0% util, no compute apps. WandB closed the run cleanly -- state "finished",
# runtime 301 s, with eval/video still present in the finished run's summary.
# The run reached ~208k of 10,000,000 episodes; that is by design, NOT a crash, and this
# run must never be read as a science result.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# VISION-RANGE-3 RENDER CHECK — 2026-09-18 — node 113, cuda:1
# ---------------------------------------------------------------------------
# Second render-check of the V2 switchover, at a LARGER SENSOR FOOTPRINT than the
# 11:34 run on 113:0 (which used basic/04, a 27-dim observation, and PASSED).
# World: 05-campfire_thermal_10x10_olf1_vis3 — olfactory_grid_range 1,
# visual_sensor_range 3, thermal enabled, 10x10, max_steps 500, perceptual noise OFF.
# Observation is ~245 numbers (visual 200 + olfaction 25 + the rest), so throughput
# is expected to be MATERIALLY LOWER than the 995 it/s of the 27-dim run — the time
# to first checkpoint is to be measured, not compared against that run's 3m38s.
# The arena widens to a 7x7 view here via max(local_view_size, 2*max_sense_range+1);
# that is expected, not a fault.
#
# WHY THIS RUN EXISTS: this world FAILED TO RENDER until commit 4b6f7196, which fixed
# the band's width declaration (olfaction now declares 206 px, vision 482 px, 704 px
# total against a 1056 px band). A CPU smoke run and a direct render already produce
# video at these ranges (results/render_audit/olf1_vis3_spanfix/videos_v2/eval_71.mp4,
# 33 frames verified). This run confirms the checkpoint video reaches WandB from a
# real GPU training run.
#
# CONFIG-OWNED: --checkpoint-frequency deliberately NOT passed. RecurrentPPO takes
# 200000 from configs/train/recurrent_ppo.yaml (NOT the 10000 in train/default.yaml,
# which is only the DQN/PPO fallback), so the code path under test is a real run's.
# --num-envs and --seed likewise left config-owned. WandB deliberately ON (--no-wandb
# NOT passed) — the cloud upload is the entire point; auth via ~/.netrc on the node.
#
# PRE-FLIGHT at 12:0x: 113 GPUs 0 and 1 both 3 MiB / 0% util, no train.py process on
# the node, nas01 mounted, JAX GPU-compile check passed (jax 0.9.0.1, both CudaDevices
# visible). Today's only 113 diary row is the 11:41 run on 113:0, already done.
# CIFS-bypass: launched via a unique /tmp script — this file is the audit record.
# ---------------------------------------------------------------------------
/home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
  --config configs/environment/experiment/basic/05-campfire_thermal_10x10_olf1_vis3.yaml \
  --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t4act_X.yaml \
  --episodes 10000000 --device cuda:1 --log-interval 10 \
  --tag "rppo_vis3_rendercheck_s42" --wandb-name "rppo_vis3_rendercheck_s42" \
  --wandb-group "nmn_site_grid_olf_gaenorm" --wandb-job-type "render_check"

# LAUNCH RECORD -- VERDICT: VISION RANGE 3 RENDERS AND REACHES WANDB. 2026-09-18
#
# Launched 21:12:25 via run_command.py --no-tail, node 113 GPU 1, PID 1072403 -- exactly
# ONE pid for the tag, checked with `ps -eo pid,cmd | grep "[t]rain\.py"` (the bracket
# form cannot self-match; a bare `pgrep -f` reports a phantom second hit because the SSH
# remote shell's own cmdline contains the pattern).
#   NAS log : logs/20260918_211225.log
#   Results : results/JAX_RecurrentPPO/20260918-211228_rppo_vis3_rendercheck_s42
#   WandB   : ytjaq3wc -- https://wandb.ai/sungwoolee/grid_world_pain/runs/ytjaq3wc
#
# WORLD CONFIRMED from the startup banner -- this is the wide-sensor world, not a
# substitute: "Observation Dim: 245 (Satiation=1, Body Temperature=1, Interoceptive
# Nociception=1, Extero Nociception=1, Thermoception=5, Olfaction=25, Collision=5,
# Proprioception=6, Visual=200)". Visual=200 is vision range 3; Olfaction=25 is
# olfactory grid range 1; Body Temperature + Thermoception confirm thermal enabled.
# Neuromodulation ENABLED (FiLM, sites=[actor], input_sensors=[Extero Nociception,
# Olfaction,Collision,Visual]), Return Mode GAE_NORM.
#
# TIME TO FIRST CHECKPOINT: 3m32s (21:12:25 -> recordings/200224/ at 21:15:57); the
# consolidated MP4 completed 21:16:06, i.e. 3m41s end-to-end. Throughput ~1088 it/s at
# the checkpoint. NOTE FOR THE RECORD: the 245-number observation did NOT cost the
# expected slowdown -- this is on par with the 27-dim run's ~995 it/s. The early tqdm
# figures (24 -> 700 it/s) are a cumulative average recovering from a ~44 s JIT compile
# and must not be read as steady-state throughput.
#
# CHECKPOINT CADENCE WAS CONFIG-OWNED, as intended: --checkpoint-frequency was NOT
# passed, the log banner reads "checkpoint_frequency : 200000" (from
# configs/train/recurrent_ppo.yaml, NOT the 10000 DQN/PPO fallback in
# configs/train/default.yaml), and the checkpoint fired at episode 200224.
#
# ALL ON-DISK CHECKS PASS:
#   1. recordings/200224/episode_00000{1,2,3}.rec.gz (2188 / 4537 / 1987 B) + run_meta.pkl.
#   2. videos_v2/eval_200224.mp4 = 295,463 B, ISO Media MP4 Base Media v1.
#      NO videos/ directory was ever created -- the run dir holds exactly
#      models/ recordings/ videos_v2/. This is the V1-vs-V2 discriminator.
#   3. videos_v2/render_200224.log carries the V2-only phrase, verbatim:
#        "  48 frames verified (expected 48)"
#      with per-episode "ep 1: 9 steps, 9 frames verified", "ep 2: 32 steps, 32 frames
#      verified", "ep 3: 7 steps, 7 frames verified".
#   4. No LayoutOverflowError and no TextFitError anywhere in the render log -- i.e. the
#      band-width fix in commit 4b6f7196 holds at olfaction 206 px + vision 482 px = 704 px
#      against the 1056 px band, under a real GPU training run and not just a smoke test.
#
# WANDB RECEIVED THE VIDEO -- confirmed against the CLOUD, and more strongly than by
# reading the local staging dir: the run summary key `eval/video` ->
#   {'path': 'media/videos/eval/video_60_b079c77c740959ba8230.mp4', 'size': 295463,
#    '_type': 'video-file', 'caption': 'Episode 200224'}
# and the file DOWNLOADED BACK from the cloud via the public API md5s to
#   3b33279bfa751af2c833645053b24a6c == md5(videos_v2/eval_200224.mp4)
# so the artifact WandB holds is byte-identical to this render, not a stale or
# re-encoded file.
#
# NON-DEFECT, recorded so it is not re-diagnosed later: render_200224.log opens with a
# JAX traceback "cuInit(0) failed: CUDA_ERROR_NO_DEVICE" (8 occurrences). EXPECTED and
# harmless -- async_render deliberately runs the renderer CPU-only so it does not contend
# with training for the GPU. Every frame still verified and the render exited 0.
#
# STOPPED ON PURPOSE at 21:17 once the cloud upload was confirmed, rather than hold a
# 4090 for a 10M-episode budget: terminate_command.py 113 <tag> --yes (SIGINT, graceful).
# Verified afterwards: 0 PIDs for the tag, both 113 GPUs back to 3 MiB / 0% util with no
# compute apps, and WandB closed the run cleanly -- state "finished", runtime 274 s, with
# eval/video still present in the finished run's summary.
# The run reached ~250k of 10,000,000 episodes; that is BY DESIGN, NOT a crash, and this
# run must never be read as a science result.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# WAVE — basic_levels_q2_default — 2026-09-21
# 14 recurrent_ppo runs: seven basic levels x two arms (control / modulated),
# seed 42 (config-owned), 10,000,000 episodes, fresh init.
# wandb-group: basic_levels_q2_default, job-type: pilot
# Design doc: docs/experiments/active/basic_levels_q2_default/BASIC_LEVELS_Q2_DEFAULT.md
#
# ARMS (identical files except the `modulation` block — verified by diff):
#   control   configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml
#   modulated configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml
#             (FiLM, sites encoder+rnn+actor+critic, input_sensors "all", temperature off)
#
# CONFIG-OWNED VALUES NOT PASSED: --num-envs (128), --seed (42),
# --checkpoint-frequency (200000, from configs/train/recurrent_ppo.yaml).
# --episodes 10000000 passed explicitly per convention.
# --log-interval 10 passed explicitly (deviation from the config's 500; requested
# by the user in the launch spec for this wave, so short-horizon curves are dense).
#
# PRE-FLIGHT (all seven nodes 101/103/104/105/106/107/108):
#   NAS mounted (df | grep -c nas01 = 1), both GPUs idle, no train.py running,
#   jax 0.9.0.1 + flax/optax/orbax/chex import AND a real 4x4 GPU matmul JIT-compiled
#   (block_until_ready) on every node — uniform versions, ptxas present.
#   No level config resolves through configs/environment/experiment/archive/.
#
# OBSERVATION-WIDTH DISCRIMINATOR — the load-bearing check (default.yaml changed
# in 47b1b8c3). Every banner verified from its own log; a banner of 27 would mean an
# archived eight-channel config was loaded and the run void. ZERO runs printed 27:
#   levels 00, 01 -> 44  (Sat 1, InteroNoci 1, ExteroNoci 1, Olf 25, Coll 5, Proprio 6, Vis 5)
#   levels 02-04  -> 52  (same, Vis 13)
#   levels 05, 06 -> 58  (adds Body Temperature 1 + Thermoception 5, Vis 13)
# Modulator confirmed live on the modulated arms —
#   "Neuromodulation: ENABLED (type=FiLM, mod_hidden=16, grouping=1, input_sensors=[all],
#    sites=[encoder,rnn,actor,critic], rnn_mechanism=activation, temperature=off)"
# and "Neuromodulation: DISABLED (baseline)" on every control.
#
# NOT A DEFECT: every log's banner reads "Device: gpu (cuda:0)" regardless of the
# --device index, because train.py line 54 sets CUDA_VISIBLE_DEVICES to the requested
# index, so in-process the card is always local 0. Physical placement was verified
# against nvidia-smi instead: exactly two compute apps per node, one on GPU 0 and one
# on GPU 1, both at 84-100% util.
#
# Launched via CIFS-bypass /tmp scripts (each staged file asserted non-empty,
# 525-540 B, and asserted to contain its own --tag before invoking — the previous
# wave's failure mode was a 0-byte staged script from `ssh -n`). This file is the
# audit record; run_command.py --no-tail drove every launch.
#
# | #  | tag                            | node:GPU | PID     | WandB id | obs | log                      |
# |----|--------------------------------|----------|---------|----------|-----|--------------------------|
# | 1  | rppo_basicq2_lvl00_t1none_s42  | 101:0    | 816565  | jgtjv7qv | 44  | logs/20260921_114813.log |
# | 2  | rppo_basicq2_lvl00_t16quad_s42 | 101:1    | 816762  | 4o1srir4 | 44  | logs/20260921_114817.log |
# | 3  | rppo_basicq2_lvl01_t1none_s42  | 103:0    | 795990  | b39w8s4z | 44  | logs/20260921_114821.log |
# | 4  | rppo_basicq2_lvl01_t16quad_s42 | 103:1    | 796181  | htbrkjnw | 44  | logs/20260921_114825.log |
# | 5  | rppo_basicq2_lvl02_t1none_s42  | 104:0    | 819539  | 994j5bpc | 52  | logs/20260921_114829.log |
# | 6  | rppo_basicq2_lvl02_t16quad_s42 | 104:1    | 819733  | pj6a2jse | 52  | logs/20260921_114833.log |
# | 7  | rppo_basicq2_lvl03_t1none_s42  | 105:0    | 906180  | qc9bis74 | 52  | logs/20260921_114837.log |
# | 8  | rppo_basicq2_lvl03_t16quad_s42 | 105:1    | 906372  | 9n91mhlc | 52  | logs/20260921_114841.log |
# | 9  | rppo_basicq2_lvl04_t1none_s42  | 106:0    | 1077322 | 4pfljig3 | 52  | logs/20260921_114845.log |
# | 10 | rppo_basicq2_lvl04_t16quad_s42 | 106:1    | 1077517 | rajw94o5 | 52  | logs/20260921_114849.log |
# | 11 | rppo_basicq2_lvl05_t1none_s42  | 107:0    | 725956  | akr5536q | 58  | logs/20260921_114852.log |
# | 12 | rppo_basicq2_lvl05_t16quad_s42 | 107:1    | 726169  | 8x0c6wkw | 58  | logs/20260921_114856.log |
# | 13 | rppo_basicq2_lvl06_t1none_s42  | 108:0    | 633501  | k0kih5kt | 58  | logs/20260921_114900.log |
# | 14 | rppo_basicq2_lvl06_t16quad_s42 | 108:1    | 633715  | 2160h4nc | 58  | logs/20260921_114904.log |
#
# PIDs are as seen by `pgrep` on the node; nvidia-smi reports host-namespace PIDs
# and will not match. Exactly one PID per tag was confirmed 110 s after launch.
#
# Representative active command (run 14 — level 06, modulated arm, node 108 cuda:1).
# The other thirteen differ only in --config, --agent_config, --device and the tag pair.
# ---------------------------------------------------------------------------
# NOTE 2026-09-30 (THIRST_WATER_PLAN): --config below repointed 06-sensory_noise -> 07-sensory_noise (the file was renamed and now sits on the pond world, width 59); the run recorded above used the old 06 file (width 58).
/home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
  --config configs/environment/experiment/basic/07-sensory_noise_10x10.yaml \
  --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml \
  --episodes 10000000 --device cuda:1 --log-interval 10 \
  --tag "rppo_basicq2_lvl06_t16quad_s42" --wandb-name "rppo_basicq2_lvl06_t16quad_s42" \
  --wandb-group "basic_levels_q2_default" --wandb-job-type "pilot"

# ---------------------------------------------------------------------------
# WAVE — basic_levels_q2_cover — 2026-09-22
# 14 recurrent_ppo runs: seven basic levels x two arms (control / modulated),
# seed 42 (config-owned), 10,000,000 episodes, fresh init.
# wandb-group: basic_levels_q2_cover, job-type: pilot
# Design doc: docs/experiments/active/basic_levels_q2_default/BASIC_LEVELS_Q2_DEFAULT.md
#
# SUPERSEDES the 2026-09-21 `basic_levels_q2_default` wave recorded above.
# That wave trained in a world where the two things this experiment depends on were
# wrong, so its null would have been uninterpretable rather than informative:
#   (a) COVER HAD NO HEALING ROLE. body.recovery_in_bush_multiplier shipped at 1.0
#       (resting in a bush healed exactly as fast as resting in the open) while
#       recovery_base_rate 0.1 + recovery_accel_rate 0.5 cleared the ENTIRE 100-point
#       injury scale on open ground in ~12 rest steps. Bush hiding is this project's
#       main behavioural readout for internal-state dependence, and an injured agent
#       had no reason to travel to cover — measured at 86% of injured steps resting
#       against 1-3% spent in a bush. Fixed in 81dbbeb0 to the tuning study's values
#       (base 0.2 / accel 0.0 / multiplier 25.0).
#   (b) NUTRITION WAS ONE-SIDED. The reward target sat at the ceiling of a 0-100 axis,
#       so more food was always better and the only way to die was starving — there
#       was nothing to REGULATE. Fixed in 379ec8fc: the axis is 0-200 with the
#       setpoint at 100 (the middle) and overeating_death genuinely lethal, so
#       over-eating costs exactly what equal under-eating costs.
# Both commits are ancestors of HEAD (verified with `git merge-base --is-ancestor`).
# Wave 1's tags (rppo_basicq2_*) are NOT reused; this wave is rppo_bq2cover_*.
# Wave 1's runs are retained on disk as a pre-tuning baseline and are NOT comparable
# with this wave.
#
# ARMS (identical files except the `modulation` block — verified by diff; the only
# other difference is comment text):
#   control   configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml
#   modulated configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml
#             (FiLM, sites encoder+rnn+actor+critic, input_sensors "all", temperature off)
#
# CONFIG-OWNED VALUES NOT PASSED: --num-envs, --seed (42), --checkpoint-frequency.
# --episodes 10000000 passed explicitly per convention.
# --log-interval 10 passed explicitly (deviation from the config's 500; carried over
# from the superseded wave so the two are directly comparable in curve density).
#
# PRE-FLIGHT (all seven nodes 101/103/104/105/106/107/108):
#   NAS mounted on every node — including 107, whose mount is intermittent across days
#   and was re-verified immediately before staging its two runs. All 14 GPUs idle at
#   0-40 MiB with zero compute apps. jax 0.9.0.1 + flax 0.12.4 + optax/orbax/chex
#   import AND a real 4x4 GPU matmul JIT-compiled (block_until_ready) on every node —
#   uniform versions, ptxas present, 2 GPUs visible each.
#   No level config resolves through configs/environment/experiment/archive/; all
#   seven chain to configs/environment/default.yaml.
#
# BODY-SETTINGS DISCRIMINATOR — the check this relaunch exists for. All seven levels
# resolve through the live loader to base 0.2 / accel 0.0 / bush 25.0 and
# max_nutrition 200 / max_satiation 200 / setpoint 100 / overeating_death true, with
# no level overriding any of them. That is a re-derivation, so it was CONFIRMED AGAINST
# EACH RUN'S OWN SAVED ARTEFACT (models/config.yaml, not a fresh reload of the source)
# for one run per width group — lvl00 (44), lvl02 (52), lvl05 (58) — all seven values
# correct in all three.
#
# OBSERVATION-WIDTH DISCRIMINATOR — verified from every run's own banner. A banner of
# 27 would mean an archived eight-channel config was loaded and the run void.
# ZERO runs printed 27:
#   levels 00, 01 -> 44 | levels 02-04 -> 52 | levels 05, 06 -> 58
# Modulator confirmed live at BOTH width extremes (obs 44 and obs 58), identical line:
#   "Neuromodulation: ENABLED (type=FiLM, mod_hidden=16, grouping=1, input_sensors=[all],
#    sites=[encoder,rnn,actor,critic], rnn_mechanism=activation, temperature=off)"
# and "Neuromodulation: DISABLED (baseline)" on all seven controls — so it resolves
# against each run's own width rather than the generator's hardcoded 27.
#
# NOT A DEFECT: every banner reads "Device: gpu (cuda:0)" regardless of --device,
# because train.py sets CUDA_VISIBLE_DEVICES to the requested index and the card is
# always local 0 in-process. Physical placement verified against nvidia-smi instead:
# exactly two compute apps per node, one on GPU 0 and one on GPU 1, 60-100% util,
# 4.4-6.5 GiB each.
#
# Launched via CIFS-bypass /tmp scripts. Each staged file was asserted non-empty
# (525-540 B) AND asserted to contain its own --tag before invoking — the earlier
# failure mode was a 0-byte staged script. Verification used `ps -eo pid,args` and
# never a bare `pgrep -f` on the tag, which matches its own launcher shell and has
# produced false "already running" readings twice. run_command.py --no-tail drove
# every launch, none wrapped in a local timeout. Exactly one PID per tag at +90 s.
#
# | #  | tag                             | node:GPU | PID     | WandB id | obs | log                      |
# |----|---------------------------------|----------|---------|----------|-----|--------------------------|
# | 1  | rppo_bq2cover_lvl00_t1none_s42  | 101:0    | 977501  | s78nhqql | 44  | logs/20260922_182443.log |
# | 2  | rppo_bq2cover_lvl00_t16quad_s42 | 101:1    | 977614  | buubzgb2 | 44  | logs/20260922_182448.log |
# | 3  | rppo_bq2cover_lvl01_t1none_s42  | 103:0    | 943209  | 39zzf48r | 44  | logs/20260922_182452.log |
# | 4  | rppo_bq2cover_lvl01_t16quad_s42 | 103:1    | 943315  | wusb4iu7 | 44  | logs/20260922_182457.log |
# | 5  | rppo_bq2cover_lvl02_t1none_s42  | 104:0    | 953147  | m2xz2m12 | 52  | logs/20260922_182501.log |
# | 6  | rppo_bq2cover_lvl02_t16quad_s42 | 104:1    | 953257  | jkrd3m2f | 52  | logs/20260922_182506.log |
# | 7  | rppo_bq2cover_lvl03_t1none_s42  | 105:0    | 1083396 | usiopa5z | 52  | logs/20260922_182510.log |
# | 8  | rppo_bq2cover_lvl03_t16quad_s42 | 105:1    | 1083506 | g193gcfn | 52  | logs/20260922_182515.log |
# | 9  | rppo_bq2cover_lvl04_t1none_s42  | 106:0    | 1266406 | ks9ve5z0 | 52  | logs/20260922_182519.log |
# | 10 | rppo_bq2cover_lvl04_t16quad_s42 | 106:1    | 1266517 | b7n83tsb | 52  | logs/20260922_182524.log |
# | 11 | rppo_bq2cover_lvl05_t1none_s42  | 107:0    | 912572  | z2u1orlf | 58  | logs/20260922_182529.log |
# | 12 | rppo_bq2cover_lvl05_t16quad_s42 | 107:1    | 912710  | ihq3tt7f | 58  | logs/20260922_182534.log |
# | 13 | rppo_bq2cover_lvl06_t1none_s42  | 108:0    | 822601  | j0z4lm4b | 58  | logs/20260922_182538.log |
# | 14 | rppo_bq2cover_lvl06_t16quad_s42 | 108:1    | 822734  | 6cmhr45f | 58  | logs/20260922_182543.log |
#
# PIDs are as seen by `ps` on the node; nvidia-smi reports host-namespace PIDs and
# will not match. Every run's WandB display name was cross-checked against its tag
# from its own "Syncing run" line — 14 of 14 match.
#
# Representative active command (run 14 — level 06, modulated arm, node 108 cuda:1).
# The other thirteen differ only in --config, --agent_config, --device and the tag pair.
# ---------------------------------------------------------------------------
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/06-sensory_noise_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml \
#   --episodes 10000000 --device cuda:1 --log-interval 10 \
#   --tag "rppo_bq2cover_lvl06_t16quad_s42" --wandb-name "rppo_bq2cover_lvl06_t16quad_s42" \
#   --wandb-group "basic_levels_q2_cover" --wandb-job-type "pilot"

# ---------------------------------------------------------------------------
# LEVEL-05 BODY INTERACTIONS — STAGE-1 PILOTS (16 runs) — 2026-09-27
# ---------------------------------------------------------------------------
# Plan: docs/experiments/active/level05_body_interactions/LEVEL05_BODY_INTERACTIONS.md
# (§3.0 rows P0a-P0c, P01-P13; §3.1 launch command). Ordinary agent only
# (nmngaenorm_t1none.yaml). 2,000,000 episodes, --log-interval 10, group
# level05_body_interactions, job-type pilot, tag = wandb-name.
# Seed: config-owned 42, except P0b --seed 43 and P0c --seed 44 (per the plan).
# P14/P15 and every factorial row NOT launched: all four factors/selected_*.yaml
# still say PROVISIONAL (expected; stage 2 gated).
#
# M7 ladder state at launch (all 16 rows):
#   HEAD                                   4209024d9a46b756dc8b15541bb46d12b7ef72d4
#   last commit on default.yaml + basic/   8187c570c09b0c40dfb89658b34f231fc7d03eab
#   (thermal.bush_min_fire_distance: 0 in default.yaml — inert, per §2.6)
#   git status --short src/ configs/environment/ was clean.
#
# | Run | Env config                                              | node:GPU | extra   |
# |-----|---------------------------------------------------------|----------|---------|
# | P0a | basic/05-campfire_thermal_10x10.yaml                    | 106:0    |         |
# | P0b | basic/05-campfire_thermal_10x10.yaml                    | 106:1    | seed 43 |
# | P0c | basic/05-campfire_thermal_10x10.yaml                    | 107:0    | seed 44 |
# | P01 | level05_body_interactions/pilots/p01_b5_floor0p5.yaml   | 107:1    |         |
# | P02 | .../pilots/p02_b5_floor0p2.yaml                         | 108:0    |         |
# | P03 | .../pilots/p03_b5_floor0p0.yaml                         | 108:1    |         |
# | P04 | .../pilots/p04_b3_cost0p5.yaml                          | 109:0    |         |
# | P05 | .../pilots/p05_b3_cost1p0.yaml                          | 109:1    |         |
# | P06 | .../pilots/p06_b3_cost2p0.yaml                          | 110:0    |         |
# | P07 | .../pilots/p07_a1_rate2.yaml                            | 110:1    |         |
# | P08 | .../pilots/p08_a1_rate4.yaml                            | 111:0    |         |
# | P09 | .../pilots/p09_a1_rate8.yaml                            | 111:1    |         |
# | P10 | .../pilots/p10_a4bite_gain4.yaml                        | 112:0    |         |
# | P11 | .../pilots/p11_a4bite_gain3.yaml                        | 112:1    |         |
# | P12 | .../pilots/p12_a4trip_food1to2.yaml                     | 113:0    |         |
# | P13 | .../pilots/p13_a4trip_food1to1.yaml                     | 113:1    |         |
# Launched via CIFS-bypass /tmp scripts + run_command.py --no-tail.
# RELAUNCH 2026-09-27 01:16: P12/P13 stuck at XLA compile on 113 (node SSH-unreachable;
# abandoned WandB c3wd9snn / 35f5vjgq). Relaunched identically on 101:0 (P12, WandB
# e8pc7ajl, logs/20260927_011649.log) and 101:1 (P13, WandB nuy4mx32,
# logs/20260927_011655.log). The 113 processes were NOT killed (node unreachable).
#
# Representative active command (P13 — node 113 cuda:1). The other fifteen differ
# only in --config, --device, the tag pair, and --seed for P0b/P0c.
# ---------------------------------------------------------------------------
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/level05_body_interactions/pilots/p13_a4trip_food1to1.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
#   --episodes 2000000 --device cuda:1 --log-interval 10 \
#   --tag "rppo_l05body_p13_a4tripfood1to1_t1none_s42" --wandb-name "rppo_l05body_p13_a4tripfood1to1_t1none_s42" \
#   --wandb-group "level05_body_interactions" --wandb-job-type "pilot"

# ---------------------------------------------------------------------------
# 2026-09-27 — level-05 body interactions, STAGE-2 pilot P14 (all four factors at the
# selected strengths; identical world to factorial cell w1111). Ordinary agent t1none,
# config-owned seed 42, 2,000,000 episodes. P15 skipped per design doc §6.2.
# Node 106 cuda:0 (RTX 3090; P0a finished there). Provisional guard passed (grep printed nothing).
# M7 ladder state at launch:
#   HEAD                                   feb6e62567c5b1b9d99673446b924f8f12c496f1
#   last commit on default.yaml + basic/   8187c570c09b0c40dfb89658b34f231fc7d03eab
#   git status --short src/ configs/environment/ was clean.
# ---------------------------------------------------------------------------
/home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
  --config configs/environment/experiment/level05_body_interactions/pilots/p14_all4_selected.yaml \
  --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
  --episodes 2000000 --device cuda:0 --log-interval 10 \
  --tag "rppo_l05body_p14_all4sel_t1none_s42" --wandb-name "rppo_l05body_p14_all4sel_t1none_s42" \
  --wandb-group "level05_body_interactions" --wandb-job-type "pilot"

# ---------------------------------------------------------------------------
# LEVEL-05 BODY INTERACTIONS — STAGE-3 FACTORIAL (32 runs, F01-F32) — 2026-09-27
# ---------------------------------------------------------------------------
# Plan: docs/experiments/active/level05_body_interactions/LEVEL05_BODY_INTERACTIONS.md
# (§3.0b rows F01-F32; §3.1 launch command). 16 worlds worlds/w<B5 B3 A1 A4>.yaml x
# {ordinary nmngaenorm_t1none (odd F), full modulator nmngaenorm_t16quad_ALL (even F)}.
# 10,000,000 episodes, --log-interval 10, group level05_body_interactions, job-type prod,
# tag = wandb-name. Seed: config-owned 42 (not passed). --num-envs / --checkpoint-frequency
# config-owned (not passed).
# Gates: no selected_*.yaml says PROVISIONAL; stage-2 P14 not collapsed (§6.2, f00f6c61);
# src/ + configs/environment/ clean; HEAD f00f6c61; ladder (M7) 8187c570 = pilots' ladder.
# Placement (user-authorised): t16quad on 3090/4090 (106-112, 102); t1none w0000-w0111 on
# 101/103/104/105, w1000-w1111 two per GPU on 114 (Ada 49 GB; train.py disables JAX
# preallocation). Every command below = the representative one with --config,
# --agent_config, --device and the tag pair substituted. Launched via CIFS-bypass /tmp
# scripts + run_command.py --no-tail.
#
# | Run | world | agent   | node:GPU |    | Run | world | agent    | node:GPU |
# | F01 | w0000 | t1none  | 101:0    |    | F02 | w0000 | t16quad  | 106:0    |
# | F03 | w0001 | t1none  | 101:1    |    | F04 | w0001 | t16quad  | 106:1    |
# | F05 | w0010 | t1none  | 103:0    |    | F06 | w0010 | t16quad  | 107:0    |
# | F07 | w0011 | t1none  | 103:1    |    | F08 | w0011 | t16quad  | 107:1    |
# | F09 | w0100 | t1none  | 104:0    |    | F10 | w0100 | t16quad  | 108:0    |
# | F11 | w0101 | t1none  | 104:1    |    | F12 | w0101 | t16quad  | 108:1    |
# | F13 | w0110 | t1none  | 105:0    |    | F14 | w0110 | t16quad  | 109:0    |
# | F15 | w0111 | t1none  | 105:1    |    | F16 | w0111 | t16quad  | 109:1    |
# | F17 | w1000 | t1none  | 114:0    |    | F18 | w1000 | t16quad  | 110:0    |
# | F19 | w1001 | t1none  | 114:0    |    | F20 | w1001 | t16quad  | 110:1    |
# | F21 | w1010 | t1none  | 114:1    |    | F22 | w1010 | t16quad  | 111:0    |
# | F23 | w1011 | t1none  | 114:1    |    | F24 | w1011 | t16quad  | 111:1    |
# | F25 | w1100 | t1none  | 114:2    |    | F26 | w1100 | t16quad  | 112:0    |
# | F27 | w1101 | t1none  | 114:2    |    | F28 | w1101 | t16quad  | 112:1    |
# | F29 | w1110 | t1none  | 114:3    |    | F30 | w1110 | t16quad  | 102:0    |
# | F31 | w1111 | t1none  | 114:3    |    | F32 | w1111 | t16quad  | 102:1    |
#
# Representative active command (F32 — w1111, modulator, node 102 cuda:1).
/home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
  --config configs/environment/experiment/level05_body_interactions/worlds/w1111.yaml \
  --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml \
  --episodes 10000000 --device cuda:1 --log-interval 10 \
  --tag "rppo_l05body_w1111_t16quad_s42" --wandb-name "rppo_l05body_w1111_t16quad_s42" \
  --wandb-group "level05_body_interactions" --wandb-job-type "prod"

# ---------------------------------------------------------------------------
# CONTEXT EXPLORATION — PART 4 (rows C3, C4, C5) — 2026-09-27
# ---------------------------------------------------------------------------
# Plan: docs/experiments/active/context_exploration/STUDY_PLAN.md ("Part 4 design" 4.9 +
# "Part 4 Revision 1"). Ordinary agent t1none, 2,000,000 episodes, --log-interval 10,
# group context_exploration, job-type pilot, tag = wandb-name. Seed config-owned 42
# (not passed). --num-envs / --checkpoint-frequency config-owned (not passed).
# HEAD a90eb973a90c376442e568864c98690984a866a7. User-approved placement (all RTX 4090):
#
# | Run | world           | node:GPU |
# | C3  | g20r20f1to4b12  | 102:1    |
# | C4  | g20r5f4to16b12  | 113:0    |
# | C5  | g20r20f1to2b36  | 113:1    |
#
# Launched ≥2 s apart via CIFS-bypass /tmp scripts + run_command.py --no-tail.
# The other two rows differ only in --config, --device and the tag pair.
# C3: g20r20f1to4b12.yaml, cuda:1 (node 102), rppo_ctxexp_g20r20f1to4b12_t1none_s42
# C5: g20r20f1to2b36.yaml, cuda:1 (node 113), rppo_ctxexp_g20r20f1to2b36_t1none_s42
# Representative active command (C4 — node 113 cuda:0).
/home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
  --config configs/environment/experiment/context_exploration/g20r5f4to16b12.yaml \
  --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
  --episodes 2000000 --device cuda:0 --log-interval 10 \
  --tag "rppo_ctxexp_g20r5f4to16b12_t1none_s42" --wandb-name "rppo_ctxexp_g20r5f4to16b12_t1none_s42" \
  --wandb-group "context_exploration" --wandb-job-type "pilot"

# context_exploration Part 4 — C1a (level-05 reference, seed 42), node 102 cuda:0
/home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
  --config configs/environment/experiment/basic/05-campfire_thermal_10x10.yaml \
  --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
  --episodes 2000000 --device cuda:0 --log-interval 10 \
  --tag "rppo_ctxexp_lvl05ref_t1none_s42" --wandb-name "rppo_ctxexp_lvl05ref_t1none_s42" \
  --wandb-group "context_exploration" --wandb-job-type "pilot"

# context_exploration Part 4 — C1b (level-05 reference, seed 43), node 105 cuda:1
/home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
  --config configs/environment/experiment/basic/05-campfire_thermal_10x10.yaml \
  --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
  --episodes 2000000 --seed 43 --device cuda:1 --log-interval 10 \
  --tag "rppo_ctxexp_lvl05ref_t1none_s43" --wandb-name "rppo_ctxexp_lvl05ref_t1none_s43" \
  --wandb-group "context_exploration" --wandb-job-type "pilot"

# context_exploration Part 4 — C7 (102:1), C2 (113:1), C6 (112:1)
/home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
  --config configs/environment/experiment/context_exploration/g15r8f1to2b36.yaml \
  --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
  --episodes 2000000 --device cuda:1 --log-interval 10 \
  --tag "rppo_ctxexp_g15r8f1to2b36_t1none_s42" --wandb-name "rppo_ctxexp_g15r8f1to2b36_t1none_s42" \
  --wandb-group "context_exploration" --wandb-job-type "pilot"
/home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
  --config configs/environment/experiment/context_exploration/g10r5f1to2b36.yaml \
  --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
  --episodes 2000000 --device cuda:1 --log-interval 10 \
  --tag "rppo_ctxexp_g10r5f1to2b36_t1none_s42" --wandb-name "rppo_ctxexp_g10r5f1to2b36_t1none_s42" \
  --wandb-group "context_exploration" --wandb-job-type "pilot"
/home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
  --config configs/environment/experiment/context_exploration/g10r3f1to2b36.yaml \
  --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
  --episodes 2000000 --device cuda:1 --log-interval 10 \
  --tag "rppo_ctxexp_g10r3f1to2b36_t1none_s42" --wandb-name "rppo_ctxexp_g10r3f1to2b36_t1none_s42" \
  --wandb-group "context_exploration" --wandb-job-type "pilot"

# ---------------------------------------------------------------------------
# context_exploration Part 4 — 2M -> 5M extension (R1.4), 2026-09-27, user-approved: C4 102:0, C3 102:1, C1a 113:0, C1b 113:1
# (C5, C7 NOT extended.) CIFS-bypass /tmp launch; this block is the audit record (commented).
# ---------------------------------------------------------------------------
# C4
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/context_exploration/g20r5f4to16b12.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/20260927-184755_rppo_ctxexp_g20r5f4to16b12_t1none_s42/models/2000021 \
#   --episodes 5000000 --device cuda:0 --log-interval 10 \
#   --wandb-resume-id 7ctxxltq \
#   --tag "rppo_ctxexp_g20r5f4to16b12_t1none_s42" --wandb-name "rppo_ctxexp_g20r5f4to16b12_t1none_s42" \
#   --wandb-group "context_exploration" --wandb-job-type "pilot"
# C3
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/context_exploration/g20r20f1to4b12.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/20260927-184753_rppo_ctxexp_g20r20f1to4b12_t1none_s42/models/2000166 \
#   --episodes 5000000 --device cuda:1 --log-interval 10 \
#   --wandb-resume-id whpmbq6l \
#   --tag "rppo_ctxexp_g20r20f1to4b12_t1none_s42" --wandb-name "rppo_ctxexp_g20r20f1to4b12_t1none_s42" \
#   --wandb-group "context_exploration" --wandb-job-type "pilot"
# C1a
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/05-campfire_thermal_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/20260927-185708_rppo_ctxexp_lvl05ref_t1none_s42/models/2000052 \
#   --episodes 5000000 --device cuda:0 --log-interval 10 \
#   --wandb-resume-id v4tbwrfn \
#   --tag "rppo_ctxexp_lvl05ref_t1none_s42" --wandb-name "rppo_ctxexp_lvl05ref_t1none_s42" \
#   --wandb-group "context_exploration" --wandb-job-type "pilot"
# C1b
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/05-campfire_thermal_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/20260927-191211_rppo_ctxexp_lvl05ref_t1none_s43/models/2000065 \
#   --episodes 5000000 --seed 43 --device cuda:1 --log-interval 10 \
#   --wandb-resume-id qxz17vr0 \
#   --tag "rppo_ctxexp_lvl05ref_t1none_s43" --wandb-name "rppo_ctxexp_lvl05ref_t1none_s43" \
#   --wandb-group "context_exploration" --wandb-job-type "pilot"

# context_exploration Part 4 — 5M extension RELAUNCH (2026-09-27): first attempt crashed at restore because
# --load-checkpoint pointed at models/<step>; restorer expects the models/ root (loads latest = 2M). Same nodes/GPUs.
# C4
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/context_exploration/g20r5f4to16b12.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/20260927-184755_rppo_ctxexp_g20r5f4to16b12_t1none_s42/models \
#   --episodes 5000000 --device cuda:0 --log-interval 10 \
#   --wandb-resume-id 7ctxxltq \
#   --tag "rppo_ctxexp_g20r5f4to16b12_t1none_s42" --wandb-name "rppo_ctxexp_g20r5f4to16b12_t1none_s42" \
#   --wandb-group "context_exploration" --wandb-job-type "pilot"
# C3
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/context_exploration/g20r20f1to4b12.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/20260927-184753_rppo_ctxexp_g20r20f1to4b12_t1none_s42/models \
#   --episodes 5000000 --device cuda:1 --log-interval 10 \
#   --wandb-resume-id whpmbq6l \
#   --tag "rppo_ctxexp_g20r20f1to4b12_t1none_s42" --wandb-name "rppo_ctxexp_g20r20f1to4b12_t1none_s42" \
#   --wandb-group "context_exploration" --wandb-job-type "pilot"
# C1a
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/05-campfire_thermal_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/20260927-185708_rppo_ctxexp_lvl05ref_t1none_s42/models \
#   --episodes 5000000 --device cuda:0 --log-interval 10 \
#   --wandb-resume-id v4tbwrfn \
#   --tag "rppo_ctxexp_lvl05ref_t1none_s42" --wandb-name "rppo_ctxexp_lvl05ref_t1none_s42" \
#   --wandb-group "context_exploration" --wandb-job-type "pilot"
# C1b
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/basic/05-campfire_thermal_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/20260927-191211_rppo_ctxexp_lvl05ref_t1none_s43/models \
#   --episodes 5000000 --seed 43 --device cuda:1 --log-interval 10 \
#   --wandb-resume-id qxz17vr0 \
#   --tag "rppo_ctxexp_lvl05ref_t1none_s43" --wandb-name "rppo_ctxexp_lvl05ref_t1none_s43" \
#   --wandb-group "context_exploration" --wandb-job-type "pilot"

# ---------------------------------------------------------------------------
# continual_worlds PILOTS — runs 1-18, launched 2026-09-28 (training-runner)
# Plan: docs/experiments/active/continual_worlds/CONTINUAL_WORLDS.md §4 (manifest) / §4.1-4.2 (commands).
# group continual_worlds, job-type pilot, tag = wandb-name. --seed and --checkpoint-frequency 100000
# are PLAN-SPECIFIED (design doc §4.1/§4.2), not boilerplate. --log-interval not passed (doc §4.2).
# Rows 13-16 are continual-schedule mode (no --episodes; budget = last boundary 15M).
# Launched via CIFS-bypass /tmp scripts + run_command.py --no-tail. Audit record only (commented).
# ---------------------------------------------------------------------------
# Run 1: rppo_cw_pilot1_forage_t1none_s42 — node 106, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/continual_worlds/forage_20x20.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/20260927-053057_rppo_l05body_w0000_t1none_s42/models \
#   --episodes 14000000 --checkpoint-frequency 100000 --seed 42 --device cuda:0 \
#   --tag "rppo_cw_pilot1_forage_t1none_s42" --wandb-name "rppo_cw_pilot1_forage_t1none_s42" \
#   --wandb-group "continual_worlds" --wandb-job-type "pilot"
# Run 2: rppo_cw_pilot1_forage_t16quad_s42 — node 106, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/continual_worlds/forage_20x20.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/20260927-053059_rppo_l05body_w0000_t16quad_s42/models \
#   --episodes 14000000 --checkpoint-frequency 100000 --seed 42 --device cuda:1 \
#   --tag "rppo_cw_pilot1_forage_t16quad_s42" --wandb-name "rppo_cw_pilot1_forage_t16quad_s42" \
#   --wandb-group "continual_worlds" --wandb-job-type "pilot"
# Run 3: rppo_cw_pilot1_danger_t1none_s42 — node 107, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/continual_worlds/danger_15x15.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/20260927-053057_rppo_l05body_w0000_t1none_s42/models \
#   --episodes 13000000 --checkpoint-frequency 100000 --seed 42 --device cuda:0 \
#   --tag "rppo_cw_pilot1_danger_t1none_s42" --wandb-name "rppo_cw_pilot1_danger_t1none_s42" \
#   --wandb-group "continual_worlds" --wandb-job-type "pilot"
# Run 4: rppo_cw_pilot1_danger_t16quad_s42 — node 107, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/continual_worlds/danger_15x15.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/20260927-053059_rppo_l05body_w0000_t16quad_s42/models \
#   --episodes 13000000 --checkpoint-frequency 100000 --seed 42 --device cuda:1 \
#   --tag "rppo_cw_pilot1_danger_t16quad_s42" --wandb-name "rppo_cw_pilot1_danger_t16quad_s42" \
#   --wandb-group "continual_worlds" --wandb-job-type "pilot"
# Run 5: rppo_cw_pilot1_famine_t1none_s42 — node 108, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/continual_worlds/famine_15x15.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/20260927-053057_rppo_l05body_w0000_t1none_s42/models \
#   --episodes 13000000 --checkpoint-frequency 100000 --seed 42 --device cuda:0 \
#   --tag "rppo_cw_pilot1_famine_t1none_s42" --wandb-name "rppo_cw_pilot1_famine_t1none_s42" \
#   --wandb-group "continual_worlds" --wandb-job-type "pilot"
# Run 6: rppo_cw_pilot1_famine_t16quad_s42 — node 108, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/continual_worlds/famine_15x15.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/20260927-053059_rppo_l05body_w0000_t16quad_s42/models \
#   --episodes 13000000 --checkpoint-frequency 100000 --seed 42 --device cuda:1 \
#   --tag "rppo_cw_pilot1_famine_t16quad_s42" --wandb-name "rppo_cw_pilot1_famine_t16quad_s42" \
#   --wandb-group "continual_worlds" --wandb-job-type "pilot"
# Run 7: rppo_cw_pilot1_winter_t1none_s42 — node 109, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/continual_worlds/winter_15x15.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/20260927-053057_rppo_l05body_w0000_t1none_s42/models \
#   --episodes 13000000 --checkpoint-frequency 100000 --seed 42 --device cuda:0 \
#   --tag "rppo_cw_pilot1_winter_t1none_s42" --wandb-name "rppo_cw_pilot1_winter_t1none_s42" \
#   --wandb-group "continual_worlds" --wandb-job-type "pilot"
# Run 8: rppo_cw_pilot1_winter_t16quad_s42 — node 109, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/continual_worlds/winter_15x15.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/20260927-053059_rppo_l05body_w0000_t16quad_s42/models \
#   --episodes 13000000 --checkpoint-frequency 100000 --seed 42 --device cuda:1 \
#   --tag "rppo_cw_pilot1_winter_t16quad_s42" --wandb-name "rppo_cw_pilot1_winter_t16quad_s42" \
#   --wandb-group "continual_worlds" --wandb-job-type "pilot"
# Run 9: rppo_cw_pilot1_fog_t1none_s42 — node 110, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/continual_worlds/fog_15x15.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/20260927-053057_rppo_l05body_w0000_t1none_s42/models \
#   --episodes 13000000 --checkpoint-frequency 100000 --seed 42 --device cuda:0 \
#   --tag "rppo_cw_pilot1_fog_t1none_s42" --wandb-name "rppo_cw_pilot1_fog_t1none_s42" \
#   --wandb-group "continual_worlds" --wandb-job-type "pilot"
# Run 10: rppo_cw_pilot1_fog_t16quad_s42 — node 110, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/continual_worlds/fog_15x15.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/20260927-053059_rppo_l05body_w0000_t16quad_s42/models \
#   --episodes 13000000 --checkpoint-frequency 100000 --seed 42 --device cuda:1 \
#   --tag "rppo_cw_pilot1_fog_t16quad_s42" --wandb-name "rppo_cw_pilot1_fog_t16quad_s42" \
#   --wandb-group "continual_worlds" --wandb-job-type "pilot"
# Run 11: rppo_cw_pilot1_harsh_t1none_s42 — node 111, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/continual_worlds/harsh_15x15.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/20260927-053057_rppo_l05body_w0000_t1none_s42/models \
#   --episodes 13000000 --checkpoint-frequency 100000 --seed 42 --device cuda:0 \
#   --tag "rppo_cw_pilot1_harsh_t1none_s42" --wandb-name "rppo_cw_pilot1_harsh_t1none_s42" \
#   --wandb-group "continual_worlds" --wandb-job-type "pilot"
# Run 12: rppo_cw_pilot1_harsh_t16quad_s42 — node 111, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/continual_worlds/harsh_15x15.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/20260927-053059_rppo_l05body_w0000_t16quad_s42/models \
#   --episodes 13000000 --checkpoint-frequency 100000 --seed 42 --device cuda:1 \
#   --tag "rppo_cw_pilot1_harsh_t16quad_s42" --wandb-name "rppo_cw_pilot1_harsh_t16quad_s42" \
#   --wandb-group "continual_worlds" --wandb-job-type "pilot"
# Run 13: rppo_cw_pilot2a_t1none_s42 — node 112, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --configs-dir configs/continual/continual_worlds/pilot2a_danger_famine_stages \
#   --continual-schedule configs/continual/continual_worlds/pilot2a_danger_famine.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/20260927-053057_rppo_l05body_w0000_t1none_s42/models \
#   --seed 42 --device cuda:0 \
#   --tag "rppo_cw_pilot2a_t1none_s42" --wandb-name "rppo_cw_pilot2a_t1none_s42" \
#   --wandb-group "continual_worlds" --wandb-job-type "pilot"
# Run 14: rppo_cw_pilot2a_t16quad_s42 — node 112, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --configs-dir configs/continual/continual_worlds/pilot2a_danger_famine_stages \
#   --continual-schedule configs/continual/continual_worlds/pilot2a_danger_famine.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/20260927-053059_rppo_l05body_w0000_t16quad_s42/models \
#   --seed 42 --device cuda:1 \
#   --tag "rppo_cw_pilot2a_t16quad_s42" --wandb-name "rppo_cw_pilot2a_t16quad_s42" \
#   --wandb-group "continual_worlds" --wandb-job-type "pilot"
# Run 15: rppo_cw_pilot2b_t1none_s42 — node 113, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --configs-dir configs/continual/continual_worlds/pilot2b_fog_danger_stages \
#   --continual-schedule configs/continual/continual_worlds/pilot2b_fog_danger.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/20260927-053057_rppo_l05body_w0000_t1none_s42/models \
#   --seed 42 --device cuda:0 \
#   --tag "rppo_cw_pilot2b_t1none_s42" --wandb-name "rppo_cw_pilot2b_t1none_s42" \
#   --wandb-group "continual_worlds" --wandb-job-type "pilot"
# Run 16: rppo_cw_pilot2b_t16quad_s42 — node 113, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --configs-dir configs/continual/continual_worlds/pilot2b_fog_danger_stages \
#   --continual-schedule configs/continual/continual_worlds/pilot2b_fog_danger.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/20260927-053059_rppo_l05body_w0000_t16quad_s42/models \
#   --seed 42 --device cuda:1 \
#   --tag "rppo_cw_pilot2b_t16quad_s42" --wandb-name "rppo_cw_pilot2b_t16quad_s42" \
#   --wandb-group "continual_worlds" --wandb-job-type "pilot"
# Run 17: rppo_cw_nursery_t1none_s43 — node 102, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/continual_worlds/nursery_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
#   --episodes 2000000 --checkpoint-frequency 100000 --seed 43 --device cuda:0 \
#   --tag "rppo_cw_nursery_t1none_s43" --wandb-name "rppo_cw_nursery_t1none_s43" \
#   --wandb-group "continual_worlds" --wandb-job-type "pilot"
# Run 18: rppo_cw_nursery_t16quad_s43 — node 102, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/continual_worlds/nursery_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml \
#   --episodes 2000000 --checkpoint-frequency 100000 --seed 43 --device cuda:1 \
#   --tag "rppo_cw_nursery_t16quad_s43" --wandb-name "rppo_cw_nursery_t16quad_s43" \
#   --wandb-group "continual_worlds" --wandb-job-type "pilot"
# ---------------------------------------------------------------------------
# 2026-09-28 — continual-worlds Revision 1a re-pilots (rows 31, 32, 35, 36; Fog rows 33-34 NOT launched)
# Plan: docs/experiments/active/continual_worlds/CONTINUAL_WORLDS.md §4 (manifest) / §4.1 (rows 31-36 =
# rows 3-12 flags with world + tag swapped). --seed / --checkpoint-frequency 100000 PLAN-SPECIFIED.
# env-config-reviewer GO 2026-09-28. Launched via CIFS-bypass /tmp scripts + run_command.py --no-tail.
# ---------------------------------------------------------------------------
# Run 31: rppo_cw_pilot1s_danger_soft_t1none_s42 — node 101, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/continual_worlds/danger_soft_15x15.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/20260927-053057_rppo_l05body_w0000_t1none_s42/models \
#   --episodes 13000000 --checkpoint-frequency 100000 --seed 42 --device cuda:0 \
#   --tag "rppo_cw_pilot1s_danger_soft_t1none_s42" --wandb-name "rppo_cw_pilot1s_danger_soft_t1none_s42" \
#   --wandb-group "continual_worlds" --wandb-job-type "pilot"
# Run 32: rppo_cw_pilot1s_danger_soft_t16quad_s42 — node 101, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/continual_worlds/danger_soft_15x15.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/20260927-053059_rppo_l05body_w0000_t16quad_s42/models \
#   --episodes 13000000 --checkpoint-frequency 100000 --seed 42 --device cuda:1 \
#   --tag "rppo_cw_pilot1s_danger_soft_t16quad_s42" --wandb-name "rppo_cw_pilot1s_danger_soft_t16quad_s42" \
#   --wandb-group "continual_worlds" --wandb-job-type "pilot"
# Run 35: rppo_cw_pilot1s_harsh_soft_t1none_s42 — node 103, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/continual_worlds/harsh_soft_15x15.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/20260927-053057_rppo_l05body_w0000_t1none_s42/models \
#   --episodes 13000000 --checkpoint-frequency 100000 --seed 42 --device cuda:0 \
#   --tag "rppo_cw_pilot1s_harsh_soft_t1none_s42" --wandb-name "rppo_cw_pilot1s_harsh_soft_t1none_s42" \
#   --wandb-group "continual_worlds" --wandb-job-type "pilot"
# Run 36: rppo_cw_pilot1s_harsh_soft_t16quad_s42 — node 103, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/continual_worlds/harsh_soft_15x15.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/20260927-053059_rppo_l05body_w0000_t16quad_s42/models \
#   --episodes 13000000 --checkpoint-frequency 100000 --seed 42 --device cuda:1 \
#   --tag "rppo_cw_pilot1s_harsh_soft_t16quad_s42" --wandb-name "rppo_cw_pilot1s_harsh_soft_t16quad_s42" \
#   --wandb-group "continual_worlds" --wandb-job-type "pilot"
# ---------------------------------------------------------------------------
# 2026-09-28 — continual-worlds Revision 1a re-pilots, Fog-soft (rows 33, 34)
# Precondition met: original Fog pilots (rows 9-10) finished and FAIL the survivable rule for both
# agents (final 93.6 / 94.3 steps vs pass lines 124.9 / 126.7). Same flags as rows 31/32/35/36.
# --seed / --checkpoint-frequency 100000 PLAN-SPECIFIED (manifest §4.1). env-config-reviewer GO
# on fog_soft 2026-09-28. Launched via CIFS-bypass /tmp scripts + run_command.py --no-tail.
# ---------------------------------------------------------------------------
# Run 33: rppo_cw_pilot1s_fog_soft_t1none_s42 — node 104, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/continual_worlds/fog_soft_15x15.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/20260927-053057_rppo_l05body_w0000_t1none_s42/models \
#   --episodes 13000000 --checkpoint-frequency 100000 --seed 42 --device cuda:0 \
#   --tag "rppo_cw_pilot1s_fog_soft_t1none_s42" --wandb-name "rppo_cw_pilot1s_fog_soft_t1none_s42" \
#   --wandb-group "continual_worlds" --wandb-job-type "pilot"
# Run 34: rppo_cw_pilot1s_fog_soft_t16quad_s42 — node 104, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/continual_worlds/fog_soft_15x15.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/20260927-053059_rppo_l05body_w0000_t16quad_s42/models \
#   --episodes 13000000 --checkpoint-frequency 100000 --seed 42 --device cuda:1 \
#   --tag "rppo_cw_pilot1s_fog_soft_t16quad_s42" --wandb-name "rppo_cw_pilot1s_fog_soft_t16quad_s42" \
#   --wandb-group "continual_worlds" --wandb-job-type "pilot"
# ---------------------------------------------------------------------------
# 2026-09-28 — 5x5 video-ladder pilots (one-off, no plan_doc). Configs committed b96a3693,
# env-config-reviewer: forage READY WITH CONCERNS (design-only), slow_predator_bush READY.
# Mirrors rppo_bq2cover_lvl00_t1none_s42 flag set; --seed / --num-envs / --checkpoint-frequency
# CONFIG-OWNED (not passed). Short runs for agent-playing videos; user stops early.
# Launched via CIFS-bypass /tmp scripts + run_command.py --no-tail.
# ---------------------------------------------------------------------------
# Run 1: rppo_ladder_forage5x5_t1none_s42 — node 105, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/forage_5x5.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
#   --episodes 1000000 --device cuda:1 --log-interval 10 \
#   --tag rppo_ladder_forage5x5_t1none_s42 --wandb-name rppo_ladder_forage5x5_t1none_s42 \
#   --wandb-group video_ladder_5x5 --wandb-job-type pilot
# Run 2: rppo_ladder_slowpredbush5x5_t1none_s42 — node 105, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/slow_predator_bush_5x5.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
#   --episodes 1000000 --device cuda:0 --log-interval 10 \
#   --tag rppo_ladder_slowpredbush5x5_t1none_s42 --wandb-name rppo_ladder_slowpredbush5x5_t1none_s42 \
#   --wandb-group video_ladder_5x5 --wandb-job-type pilot
# ---------------------------------------------------------------------------
# 2026-09-28 — continual_worlds manifest row 27: seed-43 Home leg, ordinary agent (Path A,
# plan_doc docs/experiments/active/continual_worlds/CONTINUAL_WORLDS.md §4.2). Loads run 17's
# final Nursery checkpoint (2,000,002 eps; Pilot 3 passed) and continues to 10,000,000 in Home
# (= level 05). --seed 43 / --checkpoint-frequency 100000 are PLANNED deviations from
# config-owned values (manifest); restored PRNG key governs. Node 102, cuda:0.
# Launched via CIFS-bypass /tmp script + run_command.py --no-tail.
# ---------------------------------------------------------------------------
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/continual_worlds/home_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/20260928-131756_rppo_cw_nursery_t1none_s43/models \
#   --episodes 10000000 --checkpoint-frequency 100000 --seed 43 --device cuda:0 \
#   --tag rppo_cw_home_t1none_s43 --wandb-name rppo_cw_home_t1none_s43 \
#   --wandb-group continual_worlds --wandb-job-type prod
# ---------------------------------------------------------------------------
# 2026-09-28 — continual_worlds manifest row 28: seed-43 Home leg, MODULATED agent (Path A,
# plan_doc docs/experiments/active/continual_worlds/CONTINUAL_WORLDS.md §4.1/§4.2). Loads run 18's
# final Nursery checkpoint (2,000,002 eps; Pilot 3 passed: survival 417, bites 77, eat ratio 17.1,
# hide ratio 3.03, time warm 0.21, late thermal 0.03, no collapse) and continues to 10,000,000 in
# Home (= level 05). --seed 43 / --checkpoint-frequency 100000 are PLANNED deviations from
# config-owned values (manifest); restored PRNG key governs. Node 102, cuda:1.
# Launched via CIFS-bypass /tmp script + run_command.py --no-tail.
# ---------------------------------------------------------------------------
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/continual_worlds/home_10x10.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/20260928-131804_rppo_cw_nursery_t16quad_s43/models \
#   --episodes 10000000 --checkpoint-frequency 100000 --seed 43 --device cuda:1 \
#   --tag rppo_cw_home_t16quad_s43 --wandb-name rppo_cw_home_t16quad_s43 \
#   --wandb-group continual_worlds --wandb-job-type prod
# ---------------------------------------------------------------------------
# 2026-09-28 — continual-worlds Revision 1b exploratory scouts (rows 37-41), ORDINARY agent only.
# Plan: docs/experiments/active/continual_worlds/CONTINUAL_WORLDS.md §4 (manifest) / §4.1 (row 37 full
# command). Same flags as rows 31/33/35 with the scout world, --episodes 11500000 and tag swapped.
# --seed 42 / --checkpoint-frequency 100000 PLAN-SPECIFIED (manifest §4.1). env-config-reviewer
# GO WITH NOTES 2026-09-28. Launched via CIFS-bypass /tmp scripts + run_command.py --no-tail,
# spaced >= 5 s apart so each gets its own log.
# ---------------------------------------------------------------------------
# Run 37: rppo_cw_scout_danger_scout_a_t1none_s42 — node 105, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/continual_worlds/danger_scout_a_15x15.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/20260927-053057_rppo_l05body_w0000_t1none_s42/models \
#   --episodes 11500000 --checkpoint-frequency 100000 --seed 42 --device cuda:0 \
#   --tag rppo_cw_scout_danger_scout_a_t1none_s42 --wandb-name rppo_cw_scout_danger_scout_a_t1none_s42 \
#   --wandb-group continual_worlds --wandb-job-type pilot
# Run 38: rppo_cw_scout_danger_scout_b_t1none_s42 — node 105, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/continual_worlds/danger_scout_b_15x15.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/20260927-053057_rppo_l05body_w0000_t1none_s42/models \
#   --episodes 11500000 --checkpoint-frequency 100000 --seed 42 --device cuda:1 \
#   --tag rppo_cw_scout_danger_scout_b_t1none_s42 --wandb-name rppo_cw_scout_danger_scout_b_t1none_s42 \
#   --wandb-group continual_worlds --wandb-job-type pilot
# Run 39: rppo_cw_scout_danger_scout_c_t1none_s42 — node 114, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/continual_worlds/danger_scout_c_15x15.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/20260927-053057_rppo_l05body_w0000_t1none_s42/models \
#   --episodes 11500000 --checkpoint-frequency 100000 --seed 42 --device cuda:0 \
#   --tag rppo_cw_scout_danger_scout_c_t1none_s42 --wandb-name rppo_cw_scout_danger_scout_c_t1none_s42 \
#   --wandb-group continual_worlds --wandb-job-type pilot
# Run 40: rppo_cw_scout_fog_scout_a_t1none_s42 — node 114, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/continual_worlds/fog_scout_a_15x15.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/20260927-053057_rppo_l05body_w0000_t1none_s42/models \
#   --episodes 11500000 --checkpoint-frequency 100000 --seed 42 --device cuda:1 \
#   --tag rppo_cw_scout_fog_scout_a_t1none_s42 --wandb-name rppo_cw_scout_fog_scout_a_t1none_s42 \
#   --wandb-group continual_worlds --wandb-job-type pilot
# Run 41: rppo_cw_scout_fog_scout_b_t1none_s42 — node 114, cuda:2
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/continual_worlds/fog_scout_b_15x15.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/20260927-053057_rppo_l05body_w0000_t1none_s42/models \
#   --episodes 11500000 --checkpoint-frequency 100000 --seed 42 --device cuda:2 \
#   --tag rppo_cw_scout_fog_scout_b_t1none_s42 --wandb-name rppo_cw_scout_fog_scout_b_t1none_s42 \
#   --wandb-group continual_worlds --wandb-job-type pilot
# ---------------------------------------------------------------------------
# 2026-09-28 — RELAUNCH of Revision 1b scouts rows 39-41 as `_r2` (node 114 hung during XLA
# compile ~19:09; SSH banner timeouts; the 114 copies are abandoned/possibly zombie). Commands are
# IDENTICAL to rows 39-41 above except --device, and --tag/--wandb-name carry a `_r2` suffix so
# they cannot collide with any surviving 114 process. Pre-flight: 107/110 GPUs idle, no train.py,
# NAS mounted, JAX GPU-compile check OK. CIFS-bypass /tmp scripts + run_command.py --no-tail, >=5 s apart.
# ---------------------------------------------------------------------------
# Run 39 r2: rppo_cw_scout_danger_scout_c_t1none_s42_r2 — node 107, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/continual_worlds/danger_scout_c_15x15.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/20260927-053057_rppo_l05body_w0000_t1none_s42/models \
#   --episodes 11500000 --checkpoint-frequency 100000 --seed 42 --device cuda:0 \
#   --tag rppo_cw_scout_danger_scout_c_t1none_s42_r2 --wandb-name rppo_cw_scout_danger_scout_c_t1none_s42_r2 \
#   --wandb-group continual_worlds --wandb-job-type pilot
# Run 40 r2: rppo_cw_scout_fog_scout_a_t1none_s42_r2 — node 107, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/continual_worlds/fog_scout_a_15x15.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/20260927-053057_rppo_l05body_w0000_t1none_s42/models \
#   --episodes 11500000 --checkpoint-frequency 100000 --seed 42 --device cuda:1 \
#   --tag rppo_cw_scout_fog_scout_a_t1none_s42_r2 --wandb-name rppo_cw_scout_fog_scout_a_t1none_s42_r2 \
#   --wandb-group continual_worlds --wandb-job-type pilot
# Run 41 r2: rppo_cw_scout_fog_scout_b_t1none_s42_r2 — node 110, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/continual_worlds/fog_scout_b_15x15.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/20260927-053057_rppo_l05body_w0000_t1none_s42/models \
#   --episodes 11500000 --checkpoint-frequency 100000 --seed 42 --device cuda:0 \
#   --tag rppo_cw_scout_fog_scout_b_t1none_s42_r2 --wandb-name rppo_cw_scout_fog_scout_b_t1none_s42_r2 \
#   --wandb-group continual_worlds --wandb-job-type pilot
# ---------------------------------------------------------------------------
# 2026-09-28 — Revision 1b scout row 42: MODULATED agent (t16quad) in Danger-A, pairing row 37
# (ordinary agent at ~123-130 survival, on the survivable line). Identical to row 37 except agent
# config, CK_M checkpoint, device and tag. Pre-flight: 109 GPUs idle (Pilot 1 Winter finished), no
# train.py, NAS mounted, JAX GPU-compile check OK; env config GO WITH NOTES (2026-09-28).
# ---------------------------------------------------------------------------
# Run 42: rppo_cw_scout_danger_scout_a_t16quad_s42 — node 109, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/continual_worlds/danger_scout_a_15x15.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/20260927-053059_rppo_l05body_w0000_t16quad_s42/models \
#   --episodes 11500000 --checkpoint-frequency 100000 --seed 42 --device cuda:0 \
#   --tag rppo_cw_scout_danger_scout_a_t16quad_s42 --wandb-name rppo_cw_scout_danger_scout_a_t16quad_s42 \
#   --wandb-group continual_worlds --wandb-job-type pilot
# ---------------------------------------------------------------------------
# 2026-09-28 — Revision 1b scout row 43: MODULATED agent (t16quad) in Fog-B, pairing row 41-r2
# (ordinary agent at ~130 survival, passes the 124.9 line). Identical to row 42 except world
# config, device and tag. Pre-flight: 109:1 idle (row 42 alone on 109:0), NAS mounted, JAX
# GPU-compile check OK; decay_power inherited (1.0, registry canonical).
# ---------------------------------------------------------------------------
# Run 43: rppo_cw_scout_fog_scout_b_t16quad_s42 — node 109, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/continual_worlds/fog_scout_b_15x15.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/20260927-053059_rppo_l05body_w0000_t16quad_s42/models \
#   --episodes 11500000 --checkpoint-frequency 100000 --seed 42 --device cuda:1 \
#   --tag rppo_cw_scout_fog_scout_b_t16quad_s42 --wandb-name rppo_cw_scout_fog_scout_b_t16quad_s42 \
#   --wandb-group continual_worlds --wandb-job-type pilot
# ---------------------------------------------------------------------------
# 2026-09-29 — continual-worlds MAIN branches, manifest rows 19-24 (user go 2026-09-29, design doc 3.7.7).
# Continual schedule mode (--configs-dir + --continual-schedule; no --episodes, budget = last boundary).
# Each loads its agent's branch-point copy (Forage pilot step 11000025 ordinary / 11000022 modulated).
# Pre-flight: run 14 'Training complete'; branch copies byte-identical to sources, latest_step = copied
# step; 107/108/109 GPUs free, no train.py, NAS mounted, JAX GPU-compile OK (0.9.0.1); no src/train.py
# change since Pilot 2; schedules env-config-reviewed GO WITH NOTES. --seed 42 per manifest (record only).
# ---------------------------------------------------------------------------
# Run 23: rppo_cw_p3_t1none_s42 — node 107, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --configs-dir configs/continual/continual_worlds/p3_winter_famine_stages \
#   --continual-schedule configs/continual/continual_worlds/p3_winter_famine.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/cw_branchpoint_forage_t1none_s42/models \
#   --seed 42 --device cuda:0 --tag rppo_cw_p3_t1none_s42 --wandb-name rppo_cw_p3_t1none_s42 \
#   --wandb-group continual_worlds --wandb-job-type prod
# Run 24: rppo_cw_p3_t16quad_s42 — node 107, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --configs-dir configs/continual/continual_worlds/p3_winter_famine_stages \
#   --continual-schedule configs/continual/continual_worlds/p3_winter_famine.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/cw_branchpoint_forage_t16quad_s42/models \
#   --seed 42 --device cuda:1 --tag rppo_cw_p3_t16quad_s42 --wandb-name rppo_cw_p3_t16quad_s42 \
#   --wandb-group continual_worlds --wandb-job-type prod
# Run 19: rppo_cw_p1_danger_scout_a_famine_t1none_s42 — node 108, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --configs-dir configs/continual/continual_worlds/p1_danger_scout_a_famine_stages \
#   --continual-schedule configs/continual/continual_worlds/p1_danger_scout_a_famine.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/cw_branchpoint_forage_t1none_s42/models \
#   --seed 42 --device cuda:0 --tag rppo_cw_p1_danger_scout_a_famine_t1none_s42 --wandb-name rppo_cw_p1_danger_scout_a_famine_t1none_s42 \
#   --wandb-group continual_worlds --wandb-job-type prod
# Run 20: rppo_cw_p1_danger_scout_a_famine_t16quad_s42 — node 108, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --configs-dir configs/continual/continual_worlds/p1_danger_scout_a_famine_stages \
#   --continual-schedule configs/continual/continual_worlds/p1_danger_scout_a_famine.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/cw_branchpoint_forage_t16quad_s42/models \
#   --seed 42 --device cuda:1 --tag rppo_cw_p1_danger_scout_a_famine_t16quad_s42 --wandb-name rppo_cw_p1_danger_scout_a_famine_t16quad_s42 \
#   --wandb-group continual_worlds --wandb-job-type prod
# Run 21: rppo_cw_p2_fog_scout_b_danger_scout_a_t1none_s42 — node 109, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --configs-dir configs/continual/continual_worlds/p2_fog_scout_b_danger_scout_a_stages \
#   --continual-schedule configs/continual/continual_worlds/p2_fog_scout_b_danger_scout_a.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/cw_branchpoint_forage_t1none_s42/models \
#   --seed 42 --device cuda:0 --tag rppo_cw_p2_fog_scout_b_danger_scout_a_t1none_s42 --wandb-name rppo_cw_p2_fog_scout_b_danger_scout_a_t1none_s42 \
#   --wandb-group continual_worlds --wandb-job-type prod
# Run 22: rppo_cw_p2_fog_scout_b_danger_scout_a_t16quad_s42 — node 109, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --configs-dir configs/continual/continual_worlds/p2_fog_scout_b_danger_scout_a_stages \
#   --continual-schedule configs/continual/continual_worlds/p2_fog_scout_b_danger_scout_a.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml \
#   --load-checkpoint results/JAX_RecurrentPPO/cw_branchpoint_forage_t16quad_s42/models \
#   --seed 42 --device cuda:1 --tag rppo_cw_p2_fog_scout_b_danger_scout_a_t16quad_s42 --wandb-name rppo_cw_p2_fog_scout_b_danger_scout_a_t16quad_s42 \
#   --wandb-group continual_worlds --wandb-job-type prod
# ---------------------------------------------------------------------------
# 2026-09-29 — May double-return replication, manifest rows M1-M6
# (docs/experiments/active/continual_worlds/MAY_DOUBLE_RETURN_REPLICATION.md; env-config-reviewer GO WITH NOTES,
# plan-reviewer SOUND WITH CONCERNS — analysis-only findings; user decisions 8.1).
# From scratch, continual schedule mode (no --episodes; budget = last boundary 5.1M). Code commit 0ebd09b9.
# Pre-flight: 110/111/112 both GPUs idle, no train.py / continual_forgetting_matrix.py, NAS mounted,
# JAX GPU-compile OK (0.9.0.1). Node 107 (P3) and 114 excluded per caller.
# ---------------------------------------------------------------------------
# Run M1: rppo_cw_mayrep_t1none_s42 — node 110, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --configs-dir configs/continual/continual_worlds/may_replication_stages \
#   --continual-schedule configs/continual/continual_worlds/may_replication.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
#   --seed 42 --device cuda:0 --tag rppo_cw_mayrep_t1none_s42 --wandb-name rppo_cw_mayrep_t1none_s42 \
#   --wandb-group continual_worlds --wandb-job-type prod
# Run M2: rppo_cw_mayrep_t16quad_s42 — node 110, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --configs-dir configs/continual/continual_worlds/may_replication_stages \
#   --continual-schedule configs/continual/continual_worlds/may_replication.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml \
#   --seed 42 --device cuda:1 --tag rppo_cw_mayrep_t16quad_s42 --wandb-name rppo_cw_mayrep_t16quad_s42 \
#   --wandb-group continual_worlds --wandb-job-type prod
# Run M3: rppo_cw_mayrep_t1none_s43 — node 111, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --configs-dir configs/continual/continual_worlds/may_replication_stages \
#   --continual-schedule configs/continual/continual_worlds/may_replication.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
#   --seed 43 --device cuda:0 --tag rppo_cw_mayrep_t1none_s43 --wandb-name rppo_cw_mayrep_t1none_s43 \
#   --wandb-group continual_worlds --wandb-job-type prod
# Run M4: rppo_cw_mayrep_t16quad_s43 — node 111, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --configs-dir configs/continual/continual_worlds/may_replication_stages \
#   --continual-schedule configs/continual/continual_worlds/may_replication.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml \
#   --seed 43 --device cuda:1 --tag rppo_cw_mayrep_t16quad_s43 --wandb-name rppo_cw_mayrep_t16quad_s43 \
#   --wandb-group continual_worlds --wandb-job-type prod
# Run M5: rppo_cw_mayrep_t1none_s44 — node 112, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --configs-dir configs/continual/continual_worlds/may_replication_stages \
#   --continual-schedule configs/continual/continual_worlds/may_replication.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
#   --seed 44 --device cuda:0 --tag rppo_cw_mayrep_t1none_s44 --wandb-name rppo_cw_mayrep_t1none_s44 \
#   --wandb-group continual_worlds --wandb-job-type prod
# Run M6: rppo_cw_mayrep_t16quad_s44 — node 112, cuda:1
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --configs-dir configs/continual/continual_worlds/may_replication_stages \
#   --continual-schedule configs/continual/continual_worlds/may_replication.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml \
#   --seed 44 --device cuda:1 --tag rppo_cw_mayrep_t16quad_s44 --wandb-name rppo_cw_mayrep_t16quad_s44 \
#   --wandb-group continual_worlds --wandb-job-type prod

# ---------------------------------------------------------------------------
# 2026-10-01 13:21-13:22 — THIRST_PILOT (level 06 pond + thirst), 7 runs, user-approved launch
# (docs/experiments/active/thirst_pilot/THIRST_PILOT.md §2.5/§3). Code runs from THIS worktree
# (.claude/worktrees/thirst, branch v5.0, HEAD d35a3c67, clean); outputs go to the SHARED folder
# (--results-dir <shared>/results/JAX_RecurrentPPO/<TS>_<TAG>, WANDB_DIR=<shared>, --log <shared>/logs/<TS>_<TAG>.log).
# Each run = unique /tmp script on the node: cd worktree -> v5.0 code-origin gate -> exec train.py (below).
# Launched with: ./run_command.py --no-tail --log <shared>/logs/<TS>_<TAG>.log <NODE> "bash /tmp/train_cmd_<...>.sh"
# Pre-flight: 101/103/104/105 cards idle (no compute apps), no train.py, no diary running rows; NAS mounted,
# worktree train.py readable, /usr/bin/git present, JAX GPU-compile OK (0.9.0.1); no *l06pilot* results dir.
# Seeds 43/44 pass --seed (flagged deviation per design §2.4); seed 42 config-owned.
# Run 7: rppo_l06pilot_l05ctl_t1none_s42 — node 101, cuda:0, TS 20261001_132137, bash /tmp/train_cmd_1790828497_25269_rppo_l06pilot_l05ctl_t1none_s42.sh
#   exec "$PY" train.py \
#     --config configs/environment/experiment/basic/05-campfire_thermal_10x10.yaml \
#     --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
#     --episodes 2000000 --device cuda:0 --log-interval 10 \
#     --results-dir "$SHARED/results/JAX_RecurrentPPO/20261001_132137_rppo_l06pilot_l05ctl_t1none_s42" \
#     --tag rppo_l06pilot_l05ctl_t1none_s42 --wandb-name rppo_l06pilot_l05ctl_t1none_s42 \
#     --wandb-group thirst_pilot --wandb-job-type pilot
# Run 1: rppo_l06pilot_t1none_s42 — node 101, cuda:1, TS 20261001_132138, bash /tmp/train_cmd_1790828498_4260_rppo_l06pilot_t1none_s42.sh
#     --config configs/environment/experiment/basic/06-pond_thirst_10x10.yaml \
#     --episodes 2000000 --device cuda:1 --log-interval 10 \
#     --results-dir "$SHARED/results/JAX_RecurrentPPO/20261001_132138_rppo_l06pilot_t1none_s42" \
#     --tag rppo_l06pilot_t1none_s42 --wandb-name rppo_l06pilot_t1none_s42 \
# Run 2: rppo_l06pilot_t1none_s43 — node 103, cuda:0, TS 20261001_132158, bash /tmp/train_cmd_1790828518_1104_rppo_l06pilot_t1none_s43.sh
#     --episodes 2000000 --device cuda:0 --log-interval 10 --seed 43 \
#     --results-dir "$SHARED/results/JAX_RecurrentPPO/20261001_132158_rppo_l06pilot_t1none_s43" \
#     --tag rppo_l06pilot_t1none_s43 --wandb-name rppo_l06pilot_t1none_s43 \
# Run 3: rppo_l06pilot_t1none_s44 — node 103, cuda:1, TS 20261001_132159, bash /tmp/train_cmd_1790828519_20025_rppo_l06pilot_t1none_s44.sh
#     --episodes 2000000 --device cuda:1 --log-interval 10 --seed 44 \
#     --results-dir "$SHARED/results/JAX_RecurrentPPO/20261001_132159_rppo_l06pilot_t1none_s44" \
#     --tag rppo_l06pilot_t1none_s44 --wandb-name rppo_l06pilot_t1none_s44 \
# Run 4: rppo_l06pilot_t16quad_s42 — node 104, cuda:0, TS 20261001_132200, bash /tmp/train_cmd_1790828520_21344_rppo_l06pilot_t16quad_s42.sh
#     --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml \
#     --results-dir "$SHARED/results/JAX_RecurrentPPO/20261001_132200_rppo_l06pilot_t16quad_s42" \
#     --tag rppo_l06pilot_t16quad_s42 --wandb-name rppo_l06pilot_t16quad_s42 \
# Run 5: rppo_l06pilot_t16quad_s43 — node 104, cuda:1, TS 20261001_132201, bash /tmp/train_cmd_1790828521_7865_rppo_l06pilot_t16quad_s43.sh
#     --episodes 2000000 --device cuda:1 --log-interval 10 --seed 43 \
#     --results-dir "$SHARED/results/JAX_RecurrentPPO/20261001_132201_rppo_l06pilot_t16quad_s43" \
#     --tag rppo_l06pilot_t16quad_s43 --wandb-name rppo_l06pilot_t16quad_s43 \
# Run 6: rppo_l06pilot_t16quad_s44 — node 105, cuda:0, TS 20261001_132201, bash /tmp/train_cmd_1790828521_22669_rppo_l06pilot_t16quad_s44.sh
#     --episodes 2000000 --device cuda:0 --log-interval 10 --seed 44 \
#     --results-dir "$SHARED/results/JAX_RecurrentPPO/20261001_132201_rppo_l06pilot_t16quad_s44" \
#     --tag rppo_l06pilot_t16quad_s44 --wandb-name rppo_l06pilot_t16quad_s44 \

# 2026-10-02 01:27-01:28 — THIRST_TASK (3 map sizes x 3 smell reaches x 2 agents), 18 runs, user-approved launch
# (docs/experiments/active/thirst_task/THIRST_TASK.md §9/§9.2/§9.3). Code runs from the FROZEN worktree
# .claude/worktrees/thirst-runs (detached at 583b022f941647d362c5795012ad607ea422e3ab, clean); outputs go to the SHARED folder
# Each run = unique /tmp script on the node: cd thirst-runs -> §9.3 frozen-code gate -> exec train.py (below).
# Pre-flight: all 18 target cards idle (no compute apps), no python/train.py on 106/107/109-114 (stale rppo_hv* diary
# rows on 106-112 are finished runs); NAS mounted, /usr/bin/git present, JAX GPU-compile OK (0.9.0.1); no *rppo_thirst_* results dir.
# Seed 42 config-owned (no --seed flag).
# Run 1: rppo_thirst_g10sW_t1none_s42 — node 110, cuda:0, TS 20261002_012801, bash /tmp/train_cmd_1790872081_18715_rppo_thirst_g10sW_t1none_s42.sh
#     --episodes 10000000 --device cuda:0 --log-interval 10 \
#     --results-dir "$SHARED/results/JAX_RecurrentPPO/20261002_012801_rppo_thirst_g10sW_t1none_s42" \
#     --tag rppo_thirst_g10sW_t1none_s42 --wandb-name rppo_thirst_g10sW_t1none_s42 \
#     --wandb-group thirst_task --wandb-job-type prod
# Run 2: rppo_thirst_g10sW_t16quad_s42 — node 110, cuda:1, TS 20261002_012802, bash /tmp/train_cmd_1790872082_28922_rppo_thirst_g10sW_t16quad_s42.sh
#     --episodes 10000000 --device cuda:1 --log-interval 10 \
#     --results-dir "$SHARED/results/JAX_RecurrentPPO/20261002_012802_rppo_thirst_g10sW_t16quad_s42" \
#     --tag rppo_thirst_g10sW_t16quad_s42 --wandb-name rppo_thirst_g10sW_t16quad_s42 \
# Run 3: rppo_thirst_g10s5_t1none_s42 — node 111, cuda:0, TS 20261002_012804, bash /tmp/train_cmd_1790872084_22358_rppo_thirst_g10s5_t1none_s42.sh
#     --config configs/environment/experiment/thirst/pond_thirst_10x10_smell5.yaml \
#     --results-dir "$SHARED/results/JAX_RecurrentPPO/20261002_012804_rppo_thirst_g10s5_t1none_s42" \
#     --tag rppo_thirst_g10s5_t1none_s42 --wandb-name rppo_thirst_g10s5_t1none_s42 \
# Run 4: rppo_thirst_g10s5_t16quad_s42 — node 111, cuda:1, TS 20261002_012806, bash /tmp/train_cmd_1790872086_23222_rppo_thirst_g10s5_t16quad_s42.sh
#     --results-dir "$SHARED/results/JAX_RecurrentPPO/20261002_012806_rppo_thirst_g10s5_t16quad_s42" \
#     --tag rppo_thirst_g10s5_t16quad_s42 --wandb-name rppo_thirst_g10s5_t16quad_s42 \
# Run 5: rppo_thirst_g10s3_t1none_s42 — node 112, cuda:0, TS 20261002_012808, bash /tmp/train_cmd_1790872088_22077_rppo_thirst_g10s3_t1none_s42.sh
#     --config configs/environment/experiment/thirst/pond_thirst_10x10_smell3.yaml \
#     --results-dir "$SHARED/results/JAX_RecurrentPPO/20261002_012808_rppo_thirst_g10s3_t1none_s42" \
#     --tag rppo_thirst_g10s3_t1none_s42 --wandb-name rppo_thirst_g10s3_t1none_s42 \
# Run 6: rppo_thirst_g10s3_t16quad_s42 — node 112, cuda:1, TS 20261002_012809, bash /tmp/train_cmd_1790872089_17832_rppo_thirst_g10s3_t16quad_s42.sh
#     --results-dir "$SHARED/results/JAX_RecurrentPPO/20261002_012809_rppo_thirst_g10s3_t16quad_s42" \
#     --tag rppo_thirst_g10s3_t16quad_s42 --wandb-name rppo_thirst_g10s3_t16quad_s42 \
# Run 7: rppo_thirst_g15sW_t1none_s42 — node 106, cuda:0, TS 20261002_012749, bash /tmp/train_cmd_1790872069_10829_rppo_thirst_g15sW_t1none_s42.sh
#     --config configs/environment/experiment/thirst/pond_thirst_15x15.yaml \
#     --results-dir "$SHARED/results/JAX_RecurrentPPO/20261002_012749_rppo_thirst_g15sW_t1none_s42" \
#     --tag rppo_thirst_g15sW_t1none_s42 --wandb-name rppo_thirst_g15sW_t1none_s42 \
# Run 8: rppo_thirst_g15sW_t16quad_s42 — node 106, cuda:1, TS 20261002_012751, bash /tmp/train_cmd_1790872071_26300_rppo_thirst_g15sW_t16quad_s42.sh
#     --results-dir "$SHARED/results/JAX_RecurrentPPO/20261002_012751_rppo_thirst_g15sW_t16quad_s42" \
#     --tag rppo_thirst_g15sW_t16quad_s42 --wandb-name rppo_thirst_g15sW_t16quad_s42 \
# Run 9: rppo_thirst_g15s5_t1none_s42 — node 107, cuda:0, TS 20261002_012753, bash /tmp/train_cmd_1790872073_28441_rppo_thirst_g15s5_t1none_s42.sh
#     --config configs/environment/experiment/thirst/pond_thirst_15x15_smell5.yaml \
#     --results-dir "$SHARED/results/JAX_RecurrentPPO/20261002_012753_rppo_thirst_g15s5_t1none_s42" \
#     --tag rppo_thirst_g15s5_t1none_s42 --wandb-name rppo_thirst_g15s5_t1none_s42 \
# Run 10: rppo_thirst_g15s5_t16quad_s42 — node 107, cuda:1, TS 20261002_012755, bash /tmp/train_cmd_1790872075_11328_rppo_thirst_g15s5_t16quad_s42.sh
#     --results-dir "$SHARED/results/JAX_RecurrentPPO/20261002_012755_rppo_thirst_g15s5_t16quad_s42" \
#     --tag rppo_thirst_g15s5_t16quad_s42 --wandb-name rppo_thirst_g15s5_t16quad_s42 \
# Run 11: rppo_thirst_g15s3_t1none_s42 — node 109, cuda:0, TS 20261002_012757, bash /tmp/train_cmd_1790872077_17346_rppo_thirst_g15s3_t1none_s42.sh
#     --config configs/environment/experiment/thirst/pond_thirst_15x15_smell3.yaml \
#     --results-dir "$SHARED/results/JAX_RecurrentPPO/20261002_012757_rppo_thirst_g15s3_t1none_s42" \
#     --tag rppo_thirst_g15s3_t1none_s42 --wandb-name rppo_thirst_g15s3_t1none_s42 \
# Run 12: rppo_thirst_g15s3_t16quad_s42 — node 109, cuda:1, TS 20261002_012759, bash /tmp/train_cmd_1790872079_28873_rppo_thirst_g15s3_t16quad_s42.sh
#     --results-dir "$SHARED/results/JAX_RecurrentPPO/20261002_012759_rppo_thirst_g15s3_t16quad_s42" \
#     --tag rppo_thirst_g15s3_t16quad_s42 --wandb-name rppo_thirst_g15s3_t16quad_s42 \
# Run 13: rppo_thirst_g20sW_t1none_s42 — node 114, cuda:0, TS 20261002_012738, bash /tmp/train_cmd_1790872058_12875_rppo_thirst_g20sW_t1none_s42.sh
#     --config configs/environment/experiment/thirst/pond_thirst_20x20.yaml \
#     --results-dir "$SHARED/results/JAX_RecurrentPPO/20261002_012738_rppo_thirst_g20sW_t1none_s42" \
#     --tag rppo_thirst_g20sW_t1none_s42 --wandb-name rppo_thirst_g20sW_t1none_s42 \
# Run 14: rppo_thirst_g20sW_t16quad_s42 — node 114, cuda:1, TS 20261002_012740, bash /tmp/train_cmd_1790872060_32459_rppo_thirst_g20sW_t16quad_s42.sh
#     --results-dir "$SHARED/results/JAX_RecurrentPPO/20261002_012740_rppo_thirst_g20sW_t16quad_s42" \
#     --tag rppo_thirst_g20sW_t16quad_s42 --wandb-name rppo_thirst_g20sW_t16quad_s42 \
# Run 15: rppo_thirst_g20s5_t1none_s42 — node 114, cuda:2, TS 20261002_012741, bash /tmp/train_cmd_1790872062_10082_rppo_thirst_g20s5_t1none_s42.sh
#     --config configs/environment/experiment/thirst/pond_thirst_20x20_smell5.yaml \
#     --episodes 10000000 --device cuda:2 --log-interval 10 \
#     --results-dir "$SHARED/results/JAX_RecurrentPPO/20261002_012741_rppo_thirst_g20s5_t1none_s42" \
#     --tag rppo_thirst_g20s5_t1none_s42 --wandb-name rppo_thirst_g20s5_t1none_s42 \
# Run 16: rppo_thirst_g20s5_t16quad_s42 — node 114, cuda:3, TS 20261002_012743, bash /tmp/train_cmd_1790872063_21878_rppo_thirst_g20s5_t16quad_s42.sh
#     --episodes 10000000 --device cuda:3 --log-interval 10 \
#     --results-dir "$SHARED/results/JAX_RecurrentPPO/20261002_012743_rppo_thirst_g20s5_t16quad_s42" \
#     --tag rppo_thirst_g20s5_t16quad_s42 --wandb-name rppo_thirst_g20s5_t16quad_s42 \
# Run 17: rppo_thirst_g20s3_t1none_s42 — node 113, cuda:0, TS 20261002_012745, bash /tmp/train_cmd_1790872065_19758_rppo_thirst_g20s3_t1none_s42.sh
#     --config configs/environment/experiment/thirst/pond_thirst_20x20_smell3.yaml \
#     --results-dir "$SHARED/results/JAX_RecurrentPPO/20261002_012745_rppo_thirst_g20s3_t1none_s42" \
#     --tag rppo_thirst_g20s3_t1none_s42 --wandb-name rppo_thirst_g20s3_t1none_s42 \
# Run 18: rppo_thirst_g20s3_t16quad_s42 — node 113, cuda:1, TS 20261002_012747, bash /tmp/train_cmd_1790872067_15251_rppo_thirst_g20s3_t16quad_s42.sh
#     --results-dir "$SHARED/results/JAX_RecurrentPPO/20261002_012747_rppo_thirst_g20s3_t16quad_s42" \
#     --tag rppo_thirst_g20s3_t16quad_s42 --wandb-name rppo_thirst_g20s3_t16quad_s42 \
# 2026-10-01 — Single-channel smell hypervigilance, manifest rows H01-H16
# (docs/experiments/active/hypervigilance/SINGLE_CHANNEL_SMELL_HYPERVIGILANCE.md §3; env-config-reviewer GO on
# all three worlds; plan-reviewer SOUND WITH CONCERNS on Revision 1, doc-only fixes pending).
# Main checkout, branch v4.0, HEAD 29eeea02def0164df6df104006a43b5c12044763; ladder commit b96a3693ec7e04f9ed07f6b3c8ea172628024976.
# Seed-42 rows pass no --seed (config-owned, as C01/C02); seed 43/44 rows pass --seed per manifest.
# Pre-flight: 102/106-112 both GPUs idle, no train.py, NAS mounted, JAX 0.9.0.1 GPU-compile OK, diary claims released.
# Launched via /tmp mirror scripts (CIFS bypass), run_command.py --no-tail, >=4 s apart.
# Run H01: rppo_hv1ch_t1none_s42 — node 106, cuda:0
# /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py \
#   --config configs/environment/experiment/hypervigilance/single_channel_smell_l05.yaml \
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
#   --episodes 10000000 --device cuda:0 --log-interval 10 \
#   --tag "rppo_hv1ch_t1none_s42" --wandb-name "rppo_hv1ch_t1none_s42" \
#   --wandb-group "hv_single_channel_smell" --wandb-job-type "prod"
# Run H02: rppo_hv1ch_t16quad_s42 — node 106, cuda:1
#   --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml \
#   --episodes 10000000 --device cuda:1 --log-interval 10 \
#   --tag "rppo_hv1ch_t16quad_s42" --wandb-name "rppo_hv1ch_t16quad_s42" \
# Run H03: rppo_hv1ch_t1none_s43 — node 107, cuda:0
#   --tag "rppo_hv1ch_t1none_s43" --wandb-name "rppo_hv1ch_t1none_s43" \
#   --wandb-group "hv_single_channel_smell" --wandb-job-type "prod" --seed 43
# Run H04: rppo_hv1ch_t16quad_s43 — node 107, cuda:1
#   --tag "rppo_hv1ch_t16quad_s43" --wandb-name "rppo_hv1ch_t16quad_s43" \
# Run H05: rppo_hv1ch_t1none_s44 — node 108, cuda:0
#   --tag "rppo_hv1ch_t1none_s44" --wandb-name "rppo_hv1ch_t1none_s44" \
#   --wandb-group "hv_single_channel_smell" --wandb-job-type "prod" --seed 44
# Run H06: rppo_hv1ch_t16quad_s44 — node 108, cuda:1
#   --tag "rppo_hv1ch_t16quad_s44" --wandb-name "rppo_hv1ch_t16quad_s44" \
# Run H07: rppo_hv2ch_t1none_s43 — node 109, cuda:0
#   --config configs/environment/experiment/hypervigilance/two_channel_smell_l05_control.yaml \
#   --tag "rppo_hv2ch_t1none_s43" --wandb-name "rppo_hv2ch_t1none_s43" \
# Run H08: rppo_hv2ch_t16quad_s43 — node 109, cuda:1
#   --tag "rppo_hv2ch_t16quad_s43" --wandb-name "rppo_hv2ch_t16quad_s43" \
# Run H09: rppo_hv2ch_t1none_s44 — node 110, cuda:0
#   --tag "rppo_hv2ch_t1none_s44" --wandb-name "rppo_hv2ch_t1none_s44" \
# Run H10: rppo_hv2ch_t16quad_s44 — node 110, cuda:1
#   --tag "rppo_hv2ch_t16quad_s44" --wandb-name "rppo_hv2ch_t16quad_s44" \
# Run H11: rppo_hv1chm_t1none_s42 — node 111, cuda:0
#   --config configs/environment/experiment/hypervigilance/matched_strength_smell_l05.yaml \
#   --tag "rppo_hv1chm_t1none_s42" --wandb-name "rppo_hv1chm_t1none_s42" \
# Run H12: rppo_hv1chm_t16quad_s42 — node 111, cuda:1
#   --tag "rppo_hv1chm_t16quad_s42" --wandb-name "rppo_hv1chm_t16quad_s42" \
# Run H13: rppo_hv1chm_t1none_s43 — node 112, cuda:0
#   --tag "rppo_hv1chm_t1none_s43" --wandb-name "rppo_hv1chm_t1none_s43" \
# Run H14: rppo_hv1chm_t16quad_s43 — node 112, cuda:1
#   --tag "rppo_hv1chm_t16quad_s43" --wandb-name "rppo_hv1chm_t16quad_s43" \
# Run H15: rppo_hv1chm_t1none_s44 — node 102, cuda:0
#   --tag "rppo_hv1chm_t1none_s44" --wandb-name "rppo_hv1chm_t1none_s44" \
# Run H16: rppo_hv1chm_t16quad_s44 — node 102, cuda:1
#   --tag "rppo_hv1chm_t16quad_s44" --wandb-name "rppo_hv1chm_t16quad_s44" \

# ---------------------------------------------------------------------------
# fast_heal_replication — 18 runs, launched 2026-10-05
# Plan: docs/experiments/active/hypervigilance/FAST_HEAL_REPLICATION.md (launch manifest).
# 3 worlds (levels 04/05/06) x 2 agents (t1none ordinary, t16quad_ALL modulated) x seeds 42/43/44.
# DEVIATION (user-approved seed sweep): --seed passed explicitly on every row. --seed 42 equals the
# config default (configs/train/default.yaml seed: 42), so seed-42 rows reproduce the 22-Sep pair.
# --num-envs / --checkpoint-frequency config-owned (not passed). User-approved node:GPU placement.
# Launched via per-run CIFS-bypass /tmp scripts + run_command.py --no-tail, ~20 s apart per node.
# Commented out: running this file must not relaunch them.
# [106:0] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml --episodes 10000000 --seed 42 --device cuda:0 --log-interval 10 --tag "rppo_healrep_l04_t1none_s42" --wandb-name "rppo_healrep_l04_t1none_s42" --wandb-group "fast_heal_replication" --wandb-job-type "replication"
# [106:1] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml --episodes 10000000 --seed 42 --device cuda:1 --log-interval 10 --tag "rppo_healrep_l04_t16quad_s42" --wandb-name "rppo_healrep_l04_t16quad_s42" --wandb-group "fast_heal_replication" --wandb-job-type "replication"
# [107:0] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml --episodes 10000000 --seed 43 --device cuda:0 --log-interval 10 --tag "rppo_healrep_l04_t1none_s43" --wandb-name "rppo_healrep_l04_t1none_s43" --wandb-group "fast_heal_replication" --wandb-job-type "replication"
# [107:1] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml --episodes 10000000 --seed 43 --device cuda:1 --log-interval 10 --tag "rppo_healrep_l04_t16quad_s43" --wandb-name "rppo_healrep_l04_t16quad_s43" --wandb-group "fast_heal_replication" --wandb-job-type "replication"
# [108:0] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml --episodes 10000000 --seed 44 --device cuda:0 --log-interval 10 --tag "rppo_healrep_l04_t1none_s44" --wandb-name "rppo_healrep_l04_t1none_s44" --wandb-group "fast_heal_replication" --wandb-job-type "replication"
# [108:1] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/04-jump_attack_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml --episodes 10000000 --seed 44 --device cuda:1 --log-interval 10 --tag "rppo_healrep_l04_t16quad_s44" --wandb-name "rppo_healrep_l04_t16quad_s44" --wandb-group "fast_heal_replication" --wandb-job-type "replication"
# [109:0] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/05-campfire_thermal_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml --episodes 10000000 --seed 42 --device cuda:0 --log-interval 10 --tag "rppo_healrep_l05_t1none_s42" --wandb-name "rppo_healrep_l05_t1none_s42" --wandb-group "fast_heal_replication" --wandb-job-type "replication"
# [109:1] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/05-campfire_thermal_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml --episodes 10000000 --seed 42 --device cuda:1 --log-interval 10 --tag "rppo_healrep_l05_t16quad_s42" --wandb-name "rppo_healrep_l05_t16quad_s42" --wandb-group "fast_heal_replication" --wandb-job-type "replication"
# [110:0] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/05-campfire_thermal_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml --episodes 10000000 --seed 43 --device cuda:0 --log-interval 10 --tag "rppo_healrep_l05_t1none_s43" --wandb-name "rppo_healrep_l05_t1none_s43" --wandb-group "fast_heal_replication" --wandb-job-type "replication"
# [110:1] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/05-campfire_thermal_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml --episodes 10000000 --seed 43 --device cuda:1 --log-interval 10 --tag "rppo_healrep_l05_t16quad_s43" --wandb-name "rppo_healrep_l05_t16quad_s43" --wandb-group "fast_heal_replication" --wandb-job-type "replication"
# [111:0] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/05-campfire_thermal_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml --episodes 10000000 --seed 44 --device cuda:0 --log-interval 10 --tag "rppo_healrep_l05_t1none_s44" --wandb-name "rppo_healrep_l05_t1none_s44" --wandb-group "fast_heal_replication" --wandb-job-type "replication"
# [111:1] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/05-campfire_thermal_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml --episodes 10000000 --seed 44 --device cuda:1 --log-interval 10 --tag "rppo_healrep_l05_t16quad_s44" --wandb-name "rppo_healrep_l05_t16quad_s44" --wandb-group "fast_heal_replication" --wandb-job-type "replication"
# [113:0] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/06-pond_thirst_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml --episodes 10000000 --seed 42 --device cuda:0 --log-interval 10 --tag "rppo_healrep_l06_t1none_s42" --wandb-name "rppo_healrep_l06_t1none_s42" --wandb-group "fast_heal_replication" --wandb-job-type "replication"
# [113:1] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/06-pond_thirst_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml --episodes 10000000 --seed 42 --device cuda:1 --log-interval 10 --tag "rppo_healrep_l06_t16quad_s42" --wandb-name "rppo_healrep_l06_t16quad_s42" --wandb-group "fast_heal_replication" --wandb-job-type "replication"
# [101:0] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/06-pond_thirst_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml --episodes 10000000 --seed 43 --device cuda:0 --log-interval 10 --tag "rppo_healrep_l06_t1none_s43" --wandb-name "rppo_healrep_l06_t1none_s43" --wandb-group "fast_heal_replication" --wandb-job-type "replication"
# [101:1] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/06-pond_thirst_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml --episodes 10000000 --seed 43 --device cuda:1 --log-interval 10 --tag "rppo_healrep_l06_t16quad_s43" --wandb-name "rppo_healrep_l06_t16quad_s43" --wandb-group "fast_heal_replication" --wandb-job-type "replication"
# [103:0] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/06-pond_thirst_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml --episodes 10000000 --seed 44 --device cuda:0 --log-interval 10 --tag "rppo_healrep_l06_t1none_s44" --wandb-name "rppo_healrep_l06_t1none_s44" --wandb-group "fast_heal_replication" --wandb-job-type "replication"
# [103:1] /home/vncuser/miniconda3/envs/grid_world_pain/bin/python train.py --config configs/environment/experiment/basic/06-pond_thirst_10x10.yaml --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml --episodes 10000000 --seed 44 --device cuda:1 --log-interval 10 --tag "rppo_healrep_l06_t16quad_s44" --wandb-name "rppo_healrep_l06_t16quad_s44" --wandb-group "fast_heal_replication" --wandb-job-type "replication"
