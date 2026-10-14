# Training operations: launching, resuming and keeping track of runs

**What this is.** The one place that says how training runs are started, moved, resumed and recorded on the
lab cluster, and what has gone wrong before. `training-runner` reads it before every launch; whoever
orchestrates launches (usually top-level Claude, often from a `/loop`) reads it before placing runs. It is
about *operations*: which card, which command, which records. What a run should train is the experiment
design doc's job, and the config itself is checked against
[CONFIG_CRITICAL_SETTINGS](CONFIG_CRITICAL_SETTINGS.md).

**When you hit a new launch problem, add a row to §6 in the same change that works around it.** A mistake that
is only in a chat transcript will be made again.

Related: [LAB_NODE_GPU_SPEC](LAB_NODE_GPU_SPEC.md) (cards per node) ·
[training-runner profile](../../.claude/agents/training-runner.md) (the step-by-step launch protocol) ·
[run registry](../experiments/run_registry/README.md) · [AGENT_PLAYBOOK](../AGENT_PLAYBOOK.md)
§"Queued launches, resumes and moves".

---

## 1. Who does what

| Role | Does | Never does |
|---|---|---|
| **Orchestrator** (top-level Claude; a `/loop` tick for runs that wait for cards) | Finds free cards (§2), applies the placement rules, picks the next planned run, gives `training-runner` a node + GPU, checks that running logs still advance, stops a run at a checkpoint when it must move (§5) | Start a training process itself |
| **`training-runner`** (one spawn per run; several in parallel when several cards are free) | Config pre-flight, node checks, launch or resume, verify, all records (§4) | Pick a card (it has no view of the cluster), edit `configs/` |
| **Scripts / watchers** | Detect and report: free cards, a log that stopped advancing, a finished run | Launch or resume anything. A launch that skips `training-runner` skips its checks and its records (§6, 2026-10-14) |

Queued, approved runs and stopped runs are started or resumed **without asking the user** as soon as a card is
free, then reported (user, 2026-10-13). New, unapproved experiments still need approval.

## 2. Is this card really free?

Require all of these, every time:

1. `scripts/lab/gpu_status.py --free` lists the card (live `nvidia-smi` on every node).
2. `pgrep -af 'train[.]py|dreamer_srl_main'` on the node shows no process pointed at that card. A run spends its
   first 30–60 min loading and compiling on the CPU and is invisible to `nvidia-smi` meanwhile.
3. Today's and yesterday's diary `Training runs` tables have no `running` row on that node:GPU. The first
   diary row wins a collision.
4. The node is not reserved (§7) and has the project NAS mounted (`df -h | grep nas01`).
5. For a queue that waits for cards, the card was free on **two checks about 15 min apart**. One free reading
   can be another lab member's job between two steps.

Placement rules: **one run per card, never two** (user, 2026-10-13); fill a node's free cards before the next node
(people claim whole nodes); only use card indices that exist on the node ([LAB_NODE_GPU_SPEC](LAB_NODE_GPU_SPEC.md)).

## 3. Launching

The full protocol is the runner's profile §§1–4b. The parts that have bitten us:

- Launch through `./run_command.py --no-tail <node> "bash <script>"`, never raw SSH: SSH lands in `$HOME`, so
  relative paths break and the log goes nowhere (2026-05-12). The script does its own `cd` to the repo and calls
  the conda interpreter by absolute path; never `conda run`.
- Pass `--log` as an **absolute** path. A relative one is resolved on the node, so the log ends up in that
  node's `/home/vncuser/logs/` and nobody on the NAS can read it (2026-10-13, 14 launches).
- Never wrap the launcher in a local `timeout`. It kills only the local tail; the remote run keeps going, the
  launch looks failed, and a retry starts a second copy (2026-07-21).
- Wait at least 60 s, then confirm exactly **one** process for the tag and an advancing progress count.
- dreamer_srl single-config mode reads its budget from the env config, so pass `--episodes` and
  `--log-interval` on the command line, or it runs 100 episodes and exits.

## 4. Where every run is recorded

| Record | Written by | Holds |
|---|---|---|
| `train_command-agent.sh` | `training-runner` | The exact command, with a `# WandB id:` comment. (`train_command-new.sh` is the user's file; agents never touch it) |
| Design doc launch manifest / run table | `training-runner` | Status, node, GPU, launch time, WandB run id, log path, per planned run |
| **Run registry** `docs/experiments/run_registry/runs.csv` | `scripts/lab/run_registry.py build`, run by `training-runner` after every launch and resume | One row per training session of every WandB run: id, node:GPU, checkpoint range, status, resume source, configs |
| Diary `Training runs` row | `training-runner` (`diary_append.py training-start`) | Who launched what, where, when |
| WandB | `train.py` itself | Metrics. A resume with `--wandb-resume-id` continues the same run |

**The run registry.** It is generated, never edited by hand: it reads WandB's local records
(`wandb/run-*/files/wandb-metadata.json`, which hold the full launch command) and the `results/` folders, and a
full rebuild takes about 5 s. Use it to look runs up and to resume them:

```bash
PY=/home/vncuser/miniconda3/envs/grid_world_pain/bin/python
$PY scripts/lab/run_registry.py build --live      # --live asks the nodes which runs have a process
$PY scripts/lab/run_registry.py find lookalike_hf w3
$PY scripts/lab/run_registry.py resume <run name or WandB id>   # flags + full command from the newest checkpoint
```

Known limits: it is only as fresh as its last rebuild. A launch that skips `training-runner`, a run finishing or
stopping, or another session's launch does not rebuild it, so **rebuild with `--live` before trusting a status**.
Without `--live`, "running" means "WandB wrote in the last 30 min", which misses slow-logging runs (2026-10-14:
18 vs 20). Column meanings: [README](../experiments/run_registry/README.md).

## 5. Resuming and moving a run

- Same command line plus `--load-checkpoint results/<algo>/<folder>/models --wandb-resume-id <id>`; keep
  `--episodes` at the original total. `run_registry.py resume` prints both flags. Verify the first progress
  count in the new log equals the checkpoint, not 0, and that the WandB link ends in the original id.
- A checkpoint is written every 200 k episodes for rPPO (about 25 min on a 3090, longer on a 2080 Ti). Stopping
  writes **no** final checkpoint, so everything since the last one is redone. To move a run on purpose, wait
  until its next checkpoint folder appears, give it about a minute to finish writing, then stop it
  (`terminate_command.py`) and resume on the new card.
- A resumed run writes a **new** results folder. Anything downstream (test sweeps, analyses) must be given all of
  a run's folders, oldest first; the sweep specs label them `<label>`, `<label>_resumed`, `<label>_resumed2`.
- A run whose last checkpoint is within about an hour of its end is better left to finish than moved.

## 6. Known mistakes and incidents

Newest first. Each row: what happened, why, and the rule that now prevents it.

| Date | What happened | Cause | Rule now |
|---|---|---|---|
| 2026-10-14 | 13 seed runs launched by a queue watcher had no registry entry, no design-doc row and no launch-file entry | The watcher called `run_command.py` itself and copied only the diary step of the runner's checklist | Scripts never launch; the orchestrator spawns `training-runner` per run (§1) |
| 2026-10-14 | Registry status said 18 running, live check 20 | Plain build judges "running" by recent WandB writes | Rebuild with `--live` before trusting status (§4) |
| 2026-10-13 | 14 launches wrote their logs to each node's home folder | Relative `--log` path | Absolute `--log` (§3) |
| 2026-10-13 | Node 113 went down mid-run; runs and test workers on it stopped | Node outage | Watch that logs advance; resume from the newest checkpoint on another card (§5) |
| 2026-10-13 | A helper that waited for a process "never finished" | `pgrep -f <pattern>` matched its own shell command line | Use the `[t]rain[.]py` bracket form, or a file marker, never a bare pattern that appears in your own command |
| 2026-10-12 | Six runs had been packed two to a card; they were stopped and resumed one per card | Packing to save cards | One run per card (§2); moving a run costs the episodes since its last checkpoint (§5) |
| 2026-09-09 | Two runs on node 102 died mid-training | Another lab member's job on the same node | Check node processes before and during (§2); prefer another node when 102 has a foreign tenant |
| 2026-08-04 | Two experiments launched onto the same cards on node 102 | Only `nvidia-smi` was checked; the earlier runs were still in their CPU phase | The three-way free check (§2) |
| 2026-07-21 | The same run launched twice | Local `timeout` around the launcher (§3) | Never `timeout` the launcher; check for exactly one process |
| 2026-06-27 | Launches on node 107 failed with "Permission denied" under `/media/nas01` | NAS not mounted on that node (it comes and goes) | Check `df -h | grep nas01` on the node every time; do not hard-exclude 107 |
| 2026-05-12 | A launch failed silently; log not found | Raw SSH instead of `run_command.py` | Always `run_command.py` (§3) |

## 7. Current lab constraints (live; update when they change)

| Since | Constraint | Until |
|---|---|---|
| 2026-10-14 15:35 | **Node 112 reserved for another lab member.** Launch nothing there; the half-factorial run still on 112:1 is moved off at its next checkpoint once a card frees elsewhere | The user releases it |
| 2026-09-09 | Node 102 sometimes carries another lab member's job | Check its processes at every launch |
