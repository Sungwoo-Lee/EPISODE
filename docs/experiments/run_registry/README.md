# Run registry

**What this is.** `runs.csv` lists every training run this project has sent to WandB, with the
WandB run ID, where its checkpoints are, and whether it finished. It exists so that any session can
find a run's ID and checkpoint folders in one place, above all to **resume a stopped run into its
own WandB run** instead of starting a new one (how: [training-runner §4d](../../../.claude/agents/training-runner.md)).

It is **generated, never edited by hand**: `scripts/lab/run_registry.py build` reads WandB's own
local records (`wandb/run-<date>_<time>-<id>/files/wandb-metadata.json`, which hold the full launch
command) and the `results/` folders, and rewrites the whole file. Notes such as *why* a run stopped
belong in the experiment's design doc and the diary, not here.

## When it is rebuilt

- After every training launch or resume, by whoever launched (the `training-runner` agent, a resume
  watcher), then committed and pushed with the launch bookkeeping.
- By any session that wants a fresh view: `scripts/lab/run_registry.py build` (add `--live` to ask
  the nodes which unfinished runs still have a process).

## Looking a run up

```bash
PY=/home/vncuser/miniconda3/envs/grid_world_pain/bin/python
$PY scripts/lab/run_registry.py find lookalike_hf w3        # sessions whose name/tag/id/group contain all terms
$PY scripts/lab/run_registry.py resume <run name or WandB id> # resume flags + full command from the newest checkpoint
grep mkeipck0 docs/experiments/run_registry/runs.csv          # or plain grep / pandas
```

## One row per session

A **session** is one process run of the trainer. A run that was stopped and resumed under the same
WandB ID has several rows with the same `wandb_id`, numbered by `session`; each has its own start
time, node, results folder and checkpoint range. Group by `wandb_id` for one line per run.

## Columns

| column | meaning |
|---|---|
| `wandb_id` | WandB's 8-character run ID; the value for `--wandb-resume-id` |
| `run_name` | WandB run name (`--wandb-name`, else `--tag`) |
| `session` | 1 for the first launch, 2 for the first resume, … |
| `status` | see below |
| `session_start` | local (KST) start time of this session, from the WandB folder name |
| `node`, `gpu` | lab node and card index (blank when the record does not say, e.g. early runs) |
| `first_ckpt`, `last_ckpt`, `n_ckpt` | checkpoint episode numbers saved in this session's results folder |
| `target_episodes` | `--episodes` (or `--total-steps` for dreamer_srl) |
| `results_dir` | this session's results folder (matched by tag and start time, within 15 min) |
| `resumed_from_dir`, `resumed_from_ckpt` | for a resume: the folder passed to `--load-checkpoint` and the newest checkpoint it held at session start |
| `algorithm` | RecurrentPPO, DreamerV3, DreamerSRL, … (from the results folder) |
| `trainer` | `train` (train.py) or `dreamer_srl` |
| `tag`, `wandb_group`, `wandb_job_type`, `wandb_project`, `seed` | launch arguments (blank = default) |
| `env_config`, `agent_config` | config files passed at launch |
| `git_commit` | code version at launch (first 8 characters) |
| `wandb_dir` | the local WandB record this row was built from |

## Status

Assigned in this order, first match wins:

| status | rule |
|---|---|
| `aborted` / `superseded` | results folder was moved to `results/_aborted/` or `results/_superseded/` |
| `finished` | last checkpoint ≥ 99.9 % of `target_episodes` |
| `resumed_later` | a later session of the same WandB run exists |
| `running` | WandB's stream file was written in the last 30 minutes (with `--live`: a process with this tag exists on the node) |
| `no_results` | no results folder found (crashed at startup, debug run, or folder deleted) |
| `stopped` | anything else: stopped before reaching its target and not resumed |
